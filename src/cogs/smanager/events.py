import discord,re
from discord.ext import commands,tasks
from ..utils import emote
from prettytable import PrettyTable,ORGMODE
import json
from .sutils import delete_denied_message
import asyncio
from models import *
from .sutils import (
    check_scrim_requirements,
    find_team,
    makeslotlist,
    add_role_and_reaction,
    available_to_reserve
    )
from typing import NamedTuple


QueueMessage = NamedTuple("QueueMessage", [("scrim", ScrimData), ("message", discord.Message)])

class EsportsListners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scrim_queue = asyncio.Queue()
        self.scrim_registration.start()
    
####################################################################################################################
#============================================= scrims registration worker =========================================#
####################################################################################################################
    @tasks.loop(seconds=2, reconnect=True)
    async def scrim_registration(self):
        while not self.scrim_queue.empty():
            queue_message: QueueMessage = await self.scrim_queue.get()
            scrim, message = queue_message.scrim, queue_message.message
            ctx = await self.bot.get_context(message)
            teamname = find_team(message)
            scrim = await ScrimData.get_or_none(pk=scrim.id)
            if not scrim or not scrim.is_running:  # Scrim is deleted or not opened yet.
                continue

            try:
                slot_num = scrim.available_slots[0]
            except IndexError:
                continue

            slot = await AssignedSlot.create(
                user_id=ctx.author.id, team_name=teamname, num=slot_num, message_id=message.id
            )
            await scrim.assigned_slots.add(slot)
            await ScrimData.filter(pk=scrim.id).update(available_slots=ArrayRemove("available_slots", slot_num))
            self.bot.loop.create_task(add_role_and_reaction(ctx, scrim.correctregrole))
            self.bot.dispatch("correct_reg_logs",message,teamname)
            if len(scrim.available_slots) == 1:
                self.bot.dispatch("auto_close_reg",scrim.reg_ch)

####################################################################################################################
#============================================= scrims manager registrations processes =============================#
####################################################################################################################
    @commands.Cog.listener(name = "on_message")
    async def on_scrims_reg(self,message):
        if not message.guild or message.author.bot:
            return
        # print('entered')
        scrims = await ScrimData.get_or_none(
            reg_ch=message.channel.id,
        )
        if not scrims:
            # print('not scrims')
            return 

        elif "teabot-smanger" in [role.name for role in message.author.roles]:
            # print('bot,role')
            return

        elif "teabot-sm-banned" in [role.name for role in message.author.roles]:
            if scrims['auto_delete_on_reject'] == True:
                self.bot.loop.create_task(delete_denied_message(message))
                return
            return

        elif scrims.is_running == False:
            if scrims['auto_delete_on_reject'] == True:
                self.bot.loop.create_task(delete_denied_message(message))
            return await message.reply(f'{emote.error} | Registration Has Not Opend Yet',delete_after=10)

        else:
            if not await check_scrim_requirements(self.bot, message, scrims):
                return

            self.scrim_queue.put_nowait(QueueMessage(scrims, message))



####################################################################################################################
#============================================= scrims manager Auto close registration =============================#
####################################################################################################################

    @commands.Cog.listener()
    async def on_auto_close_reg(self,channel_id):
        scrims = await ScrimData.get(reg_ch=channel_id)
        if not scrims:return #self.bot.db.fetchrow('SELECT * FROM smanager.custom_data WHERE reg_ch = $1',channel_id)
        if scrims.open_role == None:
            overwrite = scrims.reg_ch.overwrites_for(scrims.guild.default_role)
            overwrite.send_messages = False
            overwrite.view_channel = True
            try:
                await  scrims.reg_ch.set_permissions( scrims.guild.default_role, overwrite=overwrite)
            except:
                pass
            message = scrims['close_message_embed']
            embed = json.loads(message)
            em = discord.Embed.from_dict(embed)
            await  scrims.reg_ch.send(embed = em)
            self.bot.dispatch("reg_closed_logs",scrims.c_id,scrims.custom_title,scrims.guild_id)
            await scrims.update(is_running = False, is_registeration_done_today = True)
            self.bot.dispatch("slotlist_sender",scrims)
        else:
            role =  scrims.guild.get_role(scrims["open_role"])
            overwrite =  scrims.reg_ch.overwrites_for(role)
            overwrite.send_messages = False
            overwrite.view_channel = True
            try:
                await  scrims.reg_ch.set_permissions(role, overwrite=overwrite)
            except:
                pass
            message = scrims['close_message_embed']
            embed = json.loads(message)
            em = discord.Embed.from_dict(embed)
            await  scrims.reg_ch.send(embed = em)
            self.bot.dispatch("reg_closed_logs",scrims.c_id,scrims.custom_title,scrims.guild_id)
            await scrims.update(is_running = False, is_registeration_done_today = True)
            self.bot.dispatch("slotlist_sender",scrims)


####################################################################################################################
#============================================= scrims manager slotlist sender =====================================#
####################################################################################################################

    @commands.Cog.listener()
    async def on_slotlist_sender(self,datas):
        data = await ScrimData.get(c_id=datas.c_id)
        if data.auto_slot_list_send == True:
            embed = discord.Embed(title = f"Slotlist For {data.custom_title}",description = f'''```py\n{makeslotlist(data)}\n```''',color = self.bot.color)
            channel = data.slotlistch
            if not channel:return
            ch = self.bot.get_channel(channel)
            await ch.send(embed = embed)
        else:
            return

    ###################################################################################################################
    #========================================scrims manager Auto Open Listner ========================================#
    ###################################################################################################################
    @commands.Cog.listener()
    async def on_reg_open(self,channel_id):
        # print('extered on_reg_open')
        data = await ScrimData.get(reg_ch = channel_id)
        channel = data.regch
        if not channel:return
        else:
            oldslots = await data.assigned_slots
            guild = data.guild
            if not guild:
                return await data.delete()
            else:
                await AssignedSlot.filter(id__in=(slot.id for slot in oldslots)).delete()
                await data.assigned_slots.clear()
                reserved_count = await data.reserved_slots.all().count()
                await self.bot.db.execute(
            """
            UPDATE public."smanager.scrims_data" SET available_slots = $1 WHERE id = $2
            """,
                    await available_to_reserve(data),
                    data.c_id,
                )
                async for slot in data.reserved_slots.all():
                    assinged_slot = await AssignedSlot.create(
                        num=slot.num,
                        team_name=slot.team_name,
                        jump_url=None,
                    )
                    await data.assigned_slots.add(assinged_slot)
                if data.open_role == None:
                    overwrite = channel.overwrites_for(guild.default_role)
                    overwrite.send_messages = True
                    overwrite.view_channel = True
                    try:
                        await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    except:
                        self.bot.dispatch("cannot_open_reg",guild.id,f"I Was Unable To Open Registration For `{data.c_id}` Because I Don't Have Premission To Manager Channe")
                        return
                    else:
                        self.bot.dispatch("reg_ch_open_msg",channel.id,reserved_count)
                        self.bot.dispatch("reg_open_msg_logs",channel.id,guild.id)
                else:
                    role = data.openrole
                    overwrite = channel.overwrites_for(role)
                    overwrite.send_messages = True
                    overwrite.view_channel = True
                    try:
                        await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    except:
                        self.bot.dispatch("cannot_open_reg",guild.id,f"I Was Unable To Open Registration For `{data['c_id']}` Because I Don't Have Premission To Manager Channe")
                        return
                    else:
                        self.bot.dispatch("reg_ch_open_msg",channel.id)
                        self.bot.dispatch("reg_open_msg_logs",channel.id,guild.id)

                # await data.update(is_running = True,)#self.bot.db.execute(f'UPDATE smanager.custom_data SET is_running = $1,team_names = NULL WHERE reg_ch = $2',True,channel.id)
                # data = await self.bot.db.fetchrow(f"SELECT * FROM smanager.custom_data WHERE reg_ch = $1",channel.id)

        


####################################################################################################################
#====================================================== scrims manager Logs Listeners =============================#
####################################################################################################################
    @commands.Cog.listener()
    async def on_reg_ch_open_msg(self,channel_id,reserved_slots):
        data = await ScrimData.get(reg_ch = channel_id)
        message = data.open_message_embed
        message = message.replace('<<available_slots>>',f"{len(data.allowed_slots)}")
        message = message.replace('<<reserved_slots>>',f"{reserved_slots}")
        message = message.replace('<<total_slots>>',f"{data.num_slots}")
        message = message.replace('<<custom_title>>',f"{data.custom_title}")
        message = message.replace('<<mentions_required>>',f"{data.num_correct_mentions}")
        embed = json.loads(message)
        em = discord.Embed.from_dict(embed)
        role = data.openrole
        await data.regch.send(content = role.mention if role else None ,embed=em,allowed_mentions=discord.AllowedMentions(roles=True))

####################################################################################################################
#==================================================================================================================#
####################################################################################################################
    @commands.Cog.listener()
    async def on_deny_reg(self,message,type,addreact=True):
        if type == "insufficient_mentions":
            await message.reply('You Did Not Mentioned Correct Number Of Peoples',delete_after=10)
            self.bot.dispatch("deny_reg_logs",f"Reagistration For {message.author}'s Team Has Been Dnied Due To Insufficient Mentions",message.guild.id)
            if addreact == True:
                try:
                    await message.add_reaction(f'{emote.xmark}')
                except:
                    pass
        elif type == "mentioned_bot":
            await message.reply('You Mentioned A Bot',delete_after=10)
            self.bot.dispatch("deny_reg_logs",f"Reagistration For {message.author}'s Team Has Been Dnied Because They Have Mentioned A Bot",message.guild.id)
            if addreact == True:
                try:
                    await message.add_reaction(f'{emote.xmark}')
                except:
                    pass
        elif type == "baned_from_scrims":
            await message.reply('You Are banned From Scrims',delete_after=10)
            self.bot.dispatch("deny_reg_logs",f"Reagistration For {message.author}'s Team Has Been Dnied Because They Are Banned Form Scrims",message.guild.id)
            if addreact == True:
                try:
                    await message.add_reaction(f'{emote.xmark}')
                except:
                    pass
        # elif type == "incorrect_teamname":
        #     await message.reply('Team Name Is Not Correct',delete_after=10)
        #     self.bot.dispatch("deny_reg_logs",f"Reagistration For {message.author}'s Team Has Been Dnied Because No Team Name Was Given",message.guild.id)
        #     if addreact == True:
        #         try:
        #             await message.add_reaction(f'{emote.xmark}')
        #         except:
        #             pass
        elif type == "allready_registerd":
            await message.reply('You Are Already Registred',delete_after=10)
            self.bot.dispatch("deny_reg_logs",f"Reagistration For {message.author}'s Team Has Been Dnied Because They Are Already Registerd",message.guild.id)
            if addreact == True:
                try:
                    await message.add_reaction(f'{emote.xmark}')
                except:
                    pass
        else:
            pass

    @commands.Cog.listener()
    async def on_correct_reg_logs(self,message,team_name):
        log_ch = discord.utils.get(message.guild.channels, name='teabot-sm-logs')
        em = discord.Embed(title = f'🛠️ SuccessFull Registration 🛠️',description = f'{emote.tick} | Registration For Team Name = `{team_name}` Is Successfully Accepeted',color=self.bot.color)
        await log_ch.send(embed = em)

    @commands.Cog.listener()
    async def on_reg_closed_logs(self,customid,customname,customnum,guild_id):
        guild = self.bot.get_guild(guild_id)
        log_channel = discord.utils.get(guild.channels, name='teabot-sm-logs')
        msg = discord.Embed(title = f'🛠️ Registration Closed 🛠️', description = f'{emote.tick} | Succesfully Closed Registration For Custom ID = `{customid}`, Custom Number = `{customnum}`, Custom Name = `{customname}`',color=self.bot.color)
        await log_channel.send(embed=msg)

    @commands.Cog.listener()
    async def on_reg_open_msg_logs(self,ch_id,guild_id):
        guild = self.bot.get_guild(guild_id)
        # print(guild)
        # print('entered on_reg_open_msg_logs')
        ch = await self.bot.fetch_channel(ch_id)
        data = await self.bot.db.fetchrow(f"SELECT * FROM smanager.custom_data WHERE reg_ch = $1",ch.id)
        log_ch = discord.utils.get(guild.channels, name='teabot-sm-logs')
        # print(log_ch)
        custom_id = data['c_id']
        custom_num = data['custom_num']
        custom_name = data['custom_title']
        msg = discord.Embed(title = f'🛠️ Registration Opened 🛠️', description = f'{emote.tick} | Succesfully Opened Registration For Custom ID = `{custom_id}`, Custom Number = `{custom_num}`, Custom Name = `{custom_name}`',color=self.bot.color)
        await log_ch.send(embed=msg)
        # print('Done on_reg_open_msg_logs')

    @commands.Cog.listener()
    async def on_deny_reg_logs(self,message,guild_id):
        guild = self.bot.get_guild(guild_id)
        log_channel = discord.utils.get(guild.channels, name='teabot-sm-logs')
        em = discord.Embed(title = '🛠️ Registration Denied 🛠️' ,description = f'{message}',color=self.bot.color)
        await log_channel.send(embed=em)

    @commands.Cog.listener()
    async def on_cannot_open_reg(self,guild_id,message:str):
        guild = self.bot.get_guild(guild_id)
        log_channel = discord.utils.get(guild.channels, name='teabot-sm-logs')
        em = discord.Embed(title = '🛠️ Cannot Open Registartion 🛠️' ,description = f'{message}',color=self.bot.color)
        await log_channel.send(embed=em)

####################################################################################################################
#============================================= channel delete listners ============================================#
####################################################################################################################

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        data = await self.bot.db.fetchrow(f"SELECT * FROM smanager.custom_data WHERE reg_ch = $1",channel.id)
        if not data: pass
        else:
            if channel.id == int(data['reg_ch']):
                await self.bot.db.execute("UPDATE smanager.custom_data SET toggle = $1 WHERE c_id = $2",False,data['c_id'])
                if data['is_running'] == True:
                    await self.bot.db.execute("UPDATE smanager.custom_data SET is_running = $1,is_registeration_done_today = $2 WHERE c_id = $3 AND is_running = $4",False,True,data['c_id'],True)
                else:
                    pass
                log_channel = discord.utils.get(channel.guild.channels, name='teabot-sm-logs')
                em = discord.Embed(description = f"The Regitration Channel For Scrims With Id `{data['c_id']}` Has Been Deleted And Scrims Is Toggled Off Kinldy Set New Channel And Toggle It On",color = self.bot.color)
                await log_channel.send(embed=em)
            else:pass

        slot_ch = await self.bot.db.fetchrow(f"SELECT * FROM smanager.tag_check WHERE ch_id = $1",channel.id)

        if not slot_ch:pass
        else:
            if channel.id == int(slot_ch['ch_id']):
                await self.bot.dd.execute('DELETE FROM smanager.custom_data WHERE ch_id = $1',channel.id)
                log_channel = discord.utils.get(channel.guild.channels, name='teabot-sm-logs')
                em = discord.Embed(description = f"The Tag Check Channel Has Been Deleted Kindly Setup Tag Check Again With New Channel",color = self.bot.color)
                await log_channel.send(embed=em)
            else:pass

        easy_tagging = await self.bot.db.fetchrow(f"SELECT * FROM smanager.ez_tag WHERE ch_id = $1",channel.id)

        if not easy_tagging:pass
        else:
            if channel.id == int(slot_ch['ch_id']):
                await self.bot.dd.execute('DELETE FROM smanager.ez_tag WHERE ch_id = $1',channel.id)
                log_channel = discord.utils.get(channel.guild.channels, name='teabot-sm-logs')
                em = discord.Embed(description = f"The Easy Tag Channel Has Been Deleted Kindly Setup Easy Tag Again With New Channel",color = self.bot.color)
                await log_channel.send(embed=em)
            else:pass


####################################################################################################################
#================================================ Role delete listners ============================================#
####################################################################################################################

####################################################################################################################
#============================================= tag check listners =================================================#
####################################################################################################################

    @commands.Cog.listener(name = 'on_message')
    async def on_tag_check_message(self,message):
        data = await self.bot.db.fetchrow('SELECT * FROM smanager.tag_check WHERE ch_id = $1 AND toggle != $2',message.channel.id,False)
        if not data:
            return

        if message.author.bot or "teabot-smanger" in [role.name for role in message.author.roles]:
            return

        mentions = len([mem for mem in message.mentions])
        if mentions == 0 or mentions < data['mentions_required']:
            await message.reply('You Did Not Mentioned Correct Number Of Peoples',delete_after=10)
            try:
                await message.add_reaction(f'{emote.xmark}')
            except:
                pass
            return

        for mem in message.mentions:
            if mem.bot:
                await message.reply('You Mentioned A Bot',delete_after=10)
                try:
                    await message.add_reaction(f'{emote.xmark}')
                except:
                    pass
                return
        team_name = re.search(r"team.*", message.content.lower())
        if team_name is None:
            return f"{message.author}'s team"
        team_name = re.sub(r"<@*#*!*&*\d+>|team|name|[^\w\s]", "", team_name.group()).strip()
        team_name = f"Team {team_name.title()}" if team_name else f"{message.author}'s team"
        try:
            await message.add_reaction(f'{emote.tick}')
        except:
            pass
        em = discord.Embed(color=self.bot.color)
        em.description = f"Team Name: {team_name}\nPlayers: {(', '.join(m.mention for m in message.mentions)) if message.mentions else message.author.mention}"
        await message.reply(embed = em)


####################################################################################################################
#============================================= easy tagging listners ==============================================#
####################################################################################################################

        
    @commands.Cog.listener(name = 'on_message')
    async def on_ez_tag_message(self,message):
        if not message.guild or message.author.bot:
            return
        channel_id = message.channel.id
        data = await self.bot.db.fetchrow("SELECT * FROM smanager.ez_tag WHERE ch_id = $1 AND toggle = $2",channel_id,True)

        if not data:return
        elif len([mem for mem in message.mentions]) == 0:
            self.bot.loop.create_task(delete_denied_message(message,5))
            await message.reply(content = f'{emote.error} | There Are No Mentions In This Message',delete_after = 5) 
            return
        else:
            members_mentions = list()
            for mem in message.mentions:
                if mem.bot in message.mentions:
                    self.bot.loop.create_task(delete_denied_message(message,5))
                    await message.reply(content = f'{emote.error} | You Have Mentioned A Bot',delete_after = 5) 
                    return
                members_mentions.append(f'<@!{mem.id}>')
            mentions = ", ".join(members_mentions)
            msg = await message.reply(f"```{message.clean_content}\nTags: {mentions}```")
            self.bot.loop.create_task(delete_denied_message(msg,10))
            self.bot.loop.create_task(delete_denied_message(message,5))
