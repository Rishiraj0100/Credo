import discord,re,json,asyncio
from discord.ext import commands
from models import *
from .menus import CustomEditMenu,DaysEditorMenu
from .sutils import *
from ..utils.paginitators import Pages
from datetime import datetime
from ..utils.confirmater import ConfirmationPrompt
from .events import EsportsListners
from ..utils import expectations
from pytz import timezone



class Esports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Handles the bot's esports configuration system.
    """

    @commands.group(invoke_without_command = True,aliases = ['s','sm','scirms-manager'])
    async def smanager(self,ctx):
        """
        Handles The SManager Settings For This Guild
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @smanager.command(name='setup')
    # @is_bot_setuped()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True,manage_roles=True)
    async def smanager_setup(self,ctx):
        '''
        Setups The Tea Bot Scrims Manager In Your Server
        '''
        data = await GuildData.get(guild_id=ctx.guild.id)
        if data.is_bot_setuped == False:
            raise expectations.NotSetup
        if data.scrims_manager == False:
            confirmation = ConfirmationPrompt(ctx,self.bot.color)
            await confirmation.confirm(title = 'Are You Sure?',description = f'This Action will Create 2 Roles And 1 Channel')
            if confirmation.confirmed:
                await confirmation.update(description = f'{ctx.emote.loading} | Setting Up Scrims Manager')
                guild=ctx.guild
                permissions = discord.Permissions(send_messages=True, read_messages=True,administrator=True)
                sm_role = await guild.create_role(name='teabot-smanger',permissions=permissions,colour=self.bot.color)
                sm_banned_role = await guild.create_role(name='teabot-sm-banned')
                guild = ctx.guild
                member = ctx.author
                overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True,send_messages=True),
                member: discord.PermissionOverwrite(read_messages=True,send_messages=True),
                sm_role:discord.PermissionOverwrite(read_messages=True,send_messages=True)
            }
                smlogchannel = await guild.create_text_channel('teabot-sm-logs', overwrites=overwrites)
                try:
                    await ctx.author.add_roles(sm_role)
                except:
                    pass
                else:
                    data.update(scrims_manager = True)

                slot_embed = discord.Embed(title = "🛠️Scrims Manager Logs🛠️",description = f"If events related to scrims i.e opening registrations or adding roles , etc are triggered, then they will be logged in this channel. Also I have created {sm_role.mention}, you can give that role to your scrims-moderators. User with {sm_role.mention} can also send messages in registration channels and they won't be considered as scrims-registration.\n Note: Do not rename this channel.",color = self.bot.color)
                smlogchannel_msg = await smlogchannel.send(embed=slot_embed)
                await smlogchannel_msg.pin(reason = 'bcs its important')
                await confirmation.update(
                    description = f'''
                                {ctx.emote.tick} | Created {sm_role.mention} Give This Role To Your Scrims Manager Who Manages The Scrims Note Don't Change Role Name Other Wise the Won't Able To Manage Scrims 
                                \n{ctx.emote.tick} | Created {smlogchannel.mention} Channel To Log Scrimms Manager
                                \n{ctx.emote.tick} | Created {sm_banned_role.mention} Give This Role To Banned Members From Scrims
                                \n{ctx.emote.tick} | Successfully Setuped Scrims Manager Use `*smanager setup-custom` To See Avaible Custom Help
                                ''')
            else:
                return await confirmation.update(description = 'not confirmed')
        else:
            await ctx.error(f'This Server Already Have Scrims Manager Setuped')


    @smanager.command(name='setup-custom')
    @commands.has_role('teabot-smanger')
    # @is_smanager_setuped()
    async def smanager_setup_custom(self,ctx):
        """
        Setups The Custom In Your Server
        """

        count = await ScrimData.filter(guild_id=ctx.guild.id).count()
        guild = await GuildData.get(guild_id=ctx.guild.id)

        if count >= 7 and not guild.is_guild_premium:
            await ctx.error("You Can't Create More The 7 Customs")
            return

        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel
        scrim = ScrimData(
            guild_id=ctx.guild.id
        )
# queston 1
        q1 = discord.Embed(description = f'🛠️ Ok,Lets Start You Will Get 80 Seconds To Answer Each Question \nQ1. What Should Be The Channel Where I Will Send Slot List?',color = self.bot.color)
        q1.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed = q1)
        try:
            slot_channel = await self.bot.wait_for('message', timeout=80.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You took long. Goodbye.')
        else:
            if slot_channel.content == f'{ctx.prefix}cancel':
                return await ctx.send('Aborting.')
            if len(slot_channel.channel_mentions) == 0 or len(slot_channel.channel_mentions) > 1:
                return await ctx.error('You Did Not Mentioned Correct Channel Please Try Agin By Running Same Command')
            try:
                fetched_slot_channel = await commands.TextChannelConverter().convert(ctx,slot_channel.content)
            except:
                return await ctx.error('You Did Not Mentioned Correct Channel Please Try Agin By Running Same Command')
            else:
                if not fetched_slot_channel.permissions_for(ctx.me).read_messages:
                    await ctx.error(
                    f"Unfortunately, I don't have read messages permissions in {fetched_slot_channel.mention}."
                    )
                    return
            
                if not fetched_slot_channel.permissions_for(ctx.me).send_messages:
                    await ctx.error(
                    f"Unfortunately, I don't have send messages permissions in {fetched_slot_channel.mention}."
                    )

                    return

                scrim.slotlist_ch = fetched_slot_channel.id

# question 2
        q2 = discord.Embed(description = f'🛠️ Sweet! Slotlist Will Be Uploaded In {fetched_slot_channel.mention} \nQ2. What Should Be The Registration Channel Where I WIll Accept Registration?',color=self.bot.color)
        q2.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed = q2)
        try:
            reg_channel = await self.bot.wait_for('message', timeout=80.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You took long. Goodbye.')
        else:

            if reg_channel.content == f'{ctx.prefix}cancel':
                return await ctx.send('Aborting.')
            if len(reg_channel.channel_mentions) == 0 or len(reg_channel.channel_mentions) > 1:
                return await ctx.error('You Did Not Mentioned Correct Channel Please Try Agin By Running Same Command')
            try:
                fetched_reg_channel = await commands.TextChannelConverter().convert(ctx,reg_channel.content)
            except:
                return await ctx.error('You Did Not Mentioned Correct Channel Please Try Agin By Running Same Command')
            else:
                if await ScrimData.filter(reg_ch=fetched_reg_channel.id).count():
                    await ctx.error("This channel is already a registration channel.")
                if not fetched_reg_channel.permissions_for(ctx.me).read_messages:
                    await ctx.error(
                    f"Unfortunately, I don't have read messages permissions in {fetched_reg_channel.mention}."
                    )
                    return
            
                if not fetched_reg_channel.permissions_for(ctx.me).send_messages:
                    await ctx.error(
                    f"Unfortunately, I don't have send messages permissions in {fetched_reg_channel.mention}."
                    )
                    return
                
                scrim.reg_ch = fetched_reg_channel.id
# question 3
        q3 = discord.Embed(description = f'🛠️ Ok! I Will Accept Registration In {fetched_reg_channel.mention} \nQ3. which role should I give for correct registration?',color=self.bot.color)
        q3.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed = q3)
        try:
            succes_reg_role = await self.bot.wait_for('message', timeout=80.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You took long. Goodbye.')

        if succes_reg_role.content == f'{ctx.prefix}cancel':
            return await ctx.send('Aborting.')

        if len(succes_reg_role.role_mentions) == 0 or len(succes_reg_role.role_mentions) > 1:
            return await ctx.error('You Did Not Mentioned Correct Role Please Try Agin By Running Same Command')
        try:
            fetched_succes_reg_role = await commands.RoleConverter().convert(ctx,succes_reg_role.content)
        except:
            return await ctx.error('You Did Not Mentioned Correct Role Please Try Agin By Running Same Command')
        else:
            if fetched_succes_reg_role.managed:
                return await ctx.error(f"Role is an integrated role and cannot be added manually.")
            if fetched_succes_reg_role > ctx.me.top_role:
                await ctx.error(
                    f"The position of {fetched_succes_reg_role.mention} is above my top role. So I can't give it to anyone.\nKindly move {ctx.me.top_role.mention} above {fetched_succes_reg_role.mention} in Server Settings."
                )
                self.stop()
                return

            if ctx.author.id != ctx.guild.owner_id:
                if fetched_succes_reg_role > ctx.author.top_role:
                    await ctx.error(
                        f"The position of {fetched_succes_reg_role.mention} is above your top role {ctx.author.top_role.mention}."
                    )
                    self.stop()
                    return
            
            scrim.correct_reg_role = fetched_succes_reg_role.id
# question 4
        q4 = discord.Embed(description = f'🛠️ Sweet! So I Will give This Role {fetched_succes_reg_role.mention} For Correct Registration \nQ4. How many total slots do you have? **Note: Maximum Nuber Of Slots Is `25`** ',color=self.bot.color)
        q4.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed = q4)
        try:
            total_num_slots = await self.bot.wait_for('message', timeout=80.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You took long. Goodbye.')

        if total_num_slots.content == f'{ctx.prefix}cancel':
            return await ctx.send('Aborting.')
        if not total_num_slots.content.isdigit():
            return await ctx.error(f'You Did Not Entered A Integer Please Try Agin By Running Same Command')
        
        int_converted_total_num_slots = int(total_num_slots.content)
        if int_converted_total_num_slots > 30:
            return await ctx.error(f'You Entered Slots Number More Than `30` \n**Note: Maximum Nuber Of Slots Is `30`**')

        scrim.num_slots = int_converted_total_num_slots

# question 5
        q5 = discord.Embed(description = f'🛠️ Ok! total num of slots is {int_converted_total_num_slots}  No Of Slots \nQ5. What are the minimum number of mentions for correct registration?',color=self.bot.color)
        q5.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed = q5)
        try:
            minimum_mentions_for_reg = await self.bot.wait_for('message', timeout=80.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You took long. Goodbye.')

        if minimum_mentions_for_reg.content == f'{ctx.prefix}cancel':
            return await ctx.send('Aborting.')
        if not minimum_mentions_for_reg.content.isdigit():
            return await ctx.error(f'You Did Not Entered A Integer Please Try Agin By Running Same Command')
        int_minimum_mentions_for_reg = int(minimum_mentions_for_reg.content)
        scrim.allowed_slots = int_minimum_mentions_for_reg
# question 6
        q6 = discord.Embed(description = f'🛠️ Sweet! So I Will Only Accept Registration If There Will {int_minimum_mentions_for_reg}  No Of Mentions \nQ6. At What Time I Should Open Registration Please Write Time In 24 Hours Format EX:`15:00` And Bot Only Support IST Time Zone',color=self.bot.color)
        q6.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed = q6)
        try:
            reg_open_time = await self.bot.wait_for('message', timeout=80.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You took long. Goodbye.')

        if reg_open_time.content == f'{ctx.prefix}cancel':
            return await ctx.send('Aborting.')
        match = re.match(r"\d+:\d+", reg_open_time.content)
        if not match:
            return await ctx.error(f'Thats Not A Valid Time')
        match = match.group(0) 
        hour, minute = match.split(":")
        str_time = f'{hour}:{minute}'
        converting = datetime.strptime(str_time,'%H:%M')
        reg_open_final_time = converting.time()

        scrim.open_time = reg_open_final_time

# question 7
        q9 = discord.Embed(description = f'🛠️ Ok I Will Open Registration At `{reg_open_final_time}` IST \nQ9. what is the name you gave to these scrims?',color=self.bot.color)
        q9.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed = q9)
        try:
            custom_name = await self.bot.wait_for('message', timeout=80.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You took long. Goodbye.')

        if custom_name.content == f'{ctx.prefix}cancel':
            return await ctx.send('Aborting.')

        scrim.custom_title = custom_name.content
# finals
        confirmation = ConfirmationPrompt(ctx, self.bot.color)
        fields = (
            f"> Custom Name: {custom_name.content}",
            f"> Slot List Channel: {fetched_slot_channel.mention}",
            f"> Registration Channel: {fetched_reg_channel.mention}",
            f"> Success Registration Role: {fetched_succes_reg_role.mention}",
            f"> Total Num Of Slots: `{int_converted_total_num_slots}`",
            f"> Minumu Mentions Required: `{int_minimum_mentions_for_reg}`",
            f"> Registration Open Time: `{reg_open_final_time}`"
        )
        await confirmation.confirm(
            title = "Is This Ok?",
            description = "\n".join(f"`{idx}.` {field}" for idx, field in enumerate(fields, start=1))
            )
        if confirmation.confirmed:
            await confirmation.update(description = f'{ctx.emote.loading} | Setting Up Custom')
            scrim.is_registration_done_today = False
            if reg_open_final_time <= datetime.now(timezone("Asia/Kolkata")).time():
                scrim.is_registration_done_today = True
            await scrim.save()
            guild_data = GuildData.get(guild_id = ctx.guild.id)
            if guild_data.scrims_manager == False:
                await guild_data.update(scrims_manager = True)
            await confirmation.update(description=f"{ctx.emote.tick} | The Custom Has Been Setuped Successfully, The Scrims Id = `{scrim.c_id}`")
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)

    @smanager.command(name='open')
    @commands.has_role('teabot-smanger')
    async def smanager_open(self,ctx,custom_id:ScrimConverter):
        """
        Manually Opens The Registration
        """
        guild = GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        data = custom_id
        if not data:
            return await ctx.error(f'Thats Not Correct Custom ID, To Get Valid Custom ID Use `{ctx.prefix}smanager config`')
            
        if data.toggle == False:
            return await ctx.error(f'The Scrims Is Toggled Of So You Can Not Execute This Command')

        channel = data.reg_ch

        if data.is_registeration_done_today == True:
            return await ctx.error(f'Registration For Today Is Already Completed')

        if data.is_running == True:
            return await ctx.error(f'Registration Is Already Going On')
        
        self.bot.dispatch("reg_open",channel)

        await ctx.send(f'{ctx.emote.tick}')

    @smanager.command(name='close')
    @commands.has_role('teabot-smanger')
    # @is_smanager_setuped()
    async def smanager_close(self,ctx,custom_id:ScrimConverter):
        """
        Manually Closes The Rewgistration
        """
        guild = GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        data = custom_id
        if not data:
            return await ctx.error(f'Thats Not Correct Custom ID, To Get Valid Custom ID Use `{ctx.prefix}smanager config`')
            
        if data.toggle == False:
            return await ctx.error(f'The Scrims Is Toggled Of So You Can Not Execute This Command')

        if data.is_registeration_done_today == True:
            return await ctx.error(f'Registration For Today Is Already Completed')
        else:pass

        if data.is_running == False:
            return await ctx.error(f'Registration Has Not Opened Yet')

        self.bot.dispatch("auto_close_reg",data['reg_ch'])
        await ctx.send(f'{self.bot.emote.tick}')

    @smanager.command(name='delete')
    @commands.has_role('teabot-smanger')
    # @is_smanager_setuped()
    async def smanager_delete(self,ctx,custom_id:ScrimConverter):
        """Deletes The Setuped Custom"""
        guild = GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup
            
        data = custom_id

        confirmation = ConfirmationPrompt(ctx, self.bot.color)
        await confirmation.confirm(title = 'Are You Sure?',description = f"Would you like to Delete Custom Info With Custom Id = `{custom_id}`")
        if confirmation.confirmed:
            await data.delete()
        else:
            return await confirmation.update(description = f"Not Confirmed", hide_author=True, color=self.bot.color)


    @smanager.command(name = 'toogle-custom')
    @commands.has_role('teabot-smanger')
    async def smanager_toggle_custom(self,ctx,custom_id:ScrimConverter):
        '''
        Toggle Scrims Manger Custom
        '''
        guild = GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        data = custom_id

        if data.toggle == False:
            await data.update(toggle = True)
            await ctx.success(f'Successfully enabled custom with id `{custom_id}`')
            return
        else:
            await data.update(toggle = False)
            await ctx.success(f'Successfully disabled custom with id `{custom_id}`')
            return


    # @smanager.command(name='edit-custom')
    # # @is_smanager_setuped()
    # @commands.has_role('teabot-smanger')
    # async def smanager_edit_custom(self,ctx,custom_id:ScrimConverter):
    #     """Edit The Custom Data"""
    #     guild = GuildData.get(guild_id = ctx.guild.id)
    #     if guild.scrims_manager == False:
    #         raise expectations.ScrimsManagerNotSetup
        
    #     custom_data = custom_id
    #     if custom_data['is_running'] == True:
    #         return await ctx.error(f'Registration Is Going On')

    #     menu = CustomEditMenu(scrim=custom_data)
    #     await menu.start(ctx)

    # #======= days editor ===========#
    # @smanager.command(name='edit-day')
    # # @is_smanager_setuped()
    # @commands.has_role('teabot-smanger')
    # async def smanager_edit_day(self,ctx,custom_id:ScrimConverter):
    #     """Edit The Custom Open Days"""
    #     guild = GuildData.get(guild_id = ctx.guild.id)
    #     if guild.scrims_manager == False:
    #         raise expectations.ScrimsManagerNotSetup
        
    #     custom_data = custom_id
    #     menu = DaysEditorMenu(scrim=custom_data)
    #     await menu.start(ctx)

    #======= open-message editor ===========#
    @smanager.command(name='edit-open-message')
    @commands.has_role('teabot-smanger')
    async def smanager_edit_open_message(self,ctx,custom_id:ScrimConverter):
        """Edits The Custom Open Message"""
        guild = GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup
        
        custom_data = custom_id

        embed = discord.Embed(title = f'Edit Open Message For Custom: `{custom_data.c_id}`',description = f'''You Will Get 5 Minutes To Make Your Embed Kindly [Click Here](https://embedbuilder.nadekobot.me/) To Create Your Embed\n\n**You Can Use These Variables In You Message:**\n
> 1. `<<available_slots>>` = to get available slots to registration
> 2. `<<reserved_slots>>` = to get count of reserved slots
> 3. `<<total_slots>>` = to get total slots
> 4. `<<custom_title>>` = to get scrims name
> 5. `<<mentions_required>>` = Mentions Required\n\n**Your Message Should Not Break These Rules:**\n
> 1.Embed titles are limited to 190 characters
> 2.Embed descriptions are limited to 1900 characters
> 3.There can be up to 5 fields
> 4.A field's name is limited to 100 characters and its value to 900 characters
> 5.The footer text is limited to 1900 characters
> 6.The author name is limited to 190 characters
> 7.The sum of all characters in an embed structure must not exceed 6000 characters\n\n**Note:**\n
> 1. You Should Follow Those Rulles Otherwies Your Message Won't Be Accpeted
> 2. You Will Have To Answer In 5 Minutes Otherwise You Will Have To Send The Command Again Or Keep Your Embed Ready Firstly Then Use The Command
> 3. You Can Use `[name](link)` for links to make it look cool like this: [click here](https://embedbuilder.nadekobot.me/)
> 4. Mention Meber Or role Like This `<@id>` Replace id with Mebmer,role id's **This Can Only Be Used In Description or field value**
> 5. Mention Channel Like This `<#id>` Replace Id With Channel id **This Can Only Be Used In Description or field value**
> 6. You Should Not Use Simple Text In Embed Builder.
        ''',color = self.bot.color)
        embed.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed=embed)
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel

        try:
            message = await self.bot.wait_for('message', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You Took Too Long Kindly Try Again')
        else:
            if message.content == f'{ctx.prefix}cancel':
                return await ctx.send('Aborting.')
            if message.content.startswith('{') and message.content.endswith('}'):
                msg = await ctx.send(f'{ctx.emote.loading} | Checking Your Inputed Data')
                embed = json.loads(message.content)
                if "title" in message.content:
                    if len(embed['title']) > 190:
                        await msg.delete()
                        return await ctx.error('Title Is So Long')
                if "description" in message.content:
                    if len(embed['description']) > 1900:
                        await msg.delete()
                        return await ctx.error('Description Is So Long')
                if "footer" in message.content:
                    if len(embed['footer']['text']) > 1900:
                        await msg.delete()
                        return await ctx.error('Footer Is So Long')
                if "author" in message.content:
                    if len(embed['author']['name'])>190:
                        await msg.delete()
                        return await ctx.send('Author Is So Long')
                if "fields" in message.content:
                    fields_count = 0
                    for items in embed['fields']:
                        if len(items['name']) > 100 or len(items['name']) == 0:
                            await msg.delete()
                            return await ctx.error('You One Of The Field Title Is Wrong')
                        if len(items['value']) > 900 or len(items['value']) == 0:
                            await msg.delete()
                            return await ctx.error('You One Of The Field Value Is Wrong')
                        fields_count += 1
                    if fields_count > 5:
                        await msg.delete()
                        return await ctx.error(f'You Have Given Fields More Than 5')
                if "plainText" in message.content:
                    return await ctx.send('You Have Breaked One Of The Rules')

                messageto_embeded = message.content
                messageto_embeded = messageto_embeded.replace('<<available_slots>>',f"{custom_data.allowed_slots}")
                messageto_embeded = messageto_embeded.replace('<<reserved_slots>>',f"{custom_data.reserverd_slots}")
                messageto_embeded = messageto_embeded.replace('<<total_slots>>',f"{custom_data.num_slots}")
                messageto_embeded = messageto_embeded.replace('<<custom_title>>',f"{custom_data.custom_title}")
                messageto_embeded = messageto_embeded.replace('<<mentions_required>>',f"{custom_data.num_correct_mentions}")
                finalmessageto_embeded = json.loads(messageto_embeded)
                final_embed = discord.Embed.from_dict(finalmessageto_embeded)
                await msg.delete()
                reaction_message = await ctx.send(embed = final_embed)
                reactions = ['<:tick:820320509564551178>','<:xmark:820320509211574284>']
                def reactioncheck(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in reactions
                for emoji in reactions:
                    await reaction_message.add_reaction(emoji)
                    
                try:
                    reaction,user = await self.bot.wait_for('reaction_add', timeout=80.0, check=reactioncheck)
                except asyncio.TimeoutError:
                    await ctx.error('Time Up')
                    await reaction_message.delete()
                    return
                else:
                    if str(reaction.emoji) == '<:tick:820320509564551178>':
                        await custom_data.update(open_message_embed =message.content)
                        await ctx.success(f'Done')
                    else:
                        await ctx.error('aborting')
                        await reaction_message.delete()
                        return
            else:
                return await ctx.error('Thats Not A Valid Embed')
            

    #======= close-message editor ===========#
    @smanager.command(name='edit-close-message')
    @commands.has_role('teabot-smanger')
    async def smanager_edit_close_message(self,ctx,*,custom_id:ScrimConverter):
        """Edits The Custom Close Message"""
        guild = GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        custom_data = custom_id
        embed = discord.Embed(title = f'Edit Open Message For Custom: `{custom_data.c_id}`',description = f'''You Will Get 5 Minutes To Make Your Embed Kindly [Click Here](https://embedbuilder.nadekobot.me/) To Create Your Embed\n\n**Your Message Should Not Break These Rules:**\n
> 1.Embed titles are limited to 190 characters
> 2.Embed descriptions are limited to 1900 characters
> 3.There can be up to 5 fields
> 4.A field's name is limited to 100 characters and its value to 900 characters
> 5.The footer text is limited to 1900 characters
> 6.The author name is limited to 190 characters
> 7.The sum of all characters in an embed structure must not exceed 6000 characters\n\n**Note:**\n
> 1. You Should Follow Those Rulles Otherwies Your Message Won't Be Accpeted
> 2. You Will Have To Answer In 5 Minutes Otherwise You Will Have To Send The Command Again Or Keep Your Embed Ready Firstly Then Use The Command
> 3. You Can Use `[name](link)` for links to make it look cool like this: [click here](https://embedbuilder.nadekobot.me/)
> 4. Mention Meber Or role Like This `<@id>` Replace id with Mebmer,role id's **This Can Only Be Used In Description or field value**
> 5. Mention Channel Like This `<#id>` Replace Id With Channel id **This Can Only Be Used In Description or field value**
> 6. You Should Not Use Simple Text In Embed Builder.
        ''',color = self.bot.color)
        embed.set_footer(text = f'**Type `{ctx.prefix}cancel` To Cancel Setup Any Time**')
        await ctx.send(embed=embed)
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel

        try:
            message = await self.bot.wait_for('message', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.error('You Took Too Long Kindly Try Again')
        else:
            if message.content == f'{ctx.prefix}cancel':
                return await ctx.send('Aborting.')
            if message.content.startswith('{') and message.content.endswith('}'):
                msg = await ctx.send(f'{ctx.emote.loading} | Checking Your Inputed Data')
                embed = json.loads(message.content)
                if "title" in message.content:
                    if len(embed['title']) > 190:
                        await msg.delete()
                        return await ctx.error('Title Is So Long')
                if "description" in message.content:
                    if len(embed['description']) > 1900:
                        await msg.delete()
                        return await ctx.error('Description Is So Long')
                if "footer" in message.content:
                    if len(embed['footer']['text']) > 1900:
                        await msg.delete()
                        return await ctx.error('Footer Is So Long')
                if "author" in message.content:
                    await msg.delete()
                    if len(embed['author']['name'])>190:
                        await msg.delete()
                        return await ctx.send('Author Is So Long')
                if "fields" in message.content:
                    fields_count = 0
                    for items in embed['fields']:
                        if len(items['name']) > 100 or len(items['name']) == 0:
                            await msg.delete()
                            return await ctx.error('You One Of The Field Title Is Wrong')
                        if len(items['value']) > 900 or len(items['value']) == 0:
                            await msg.delete()
                            return await ctx.error('You One Of The Field Value Is Wrong')
                        fields_count += 1
                    if fields_count > 5:
                        await msg.delete()
                        return await ctx.error(f'You Have Given Fields More Than 5')
                if "plainText" in message.content:
                    await msg.delete()
                    return await ctx.send('You Have Breaked One Of The Rules')
                final_embed = discord.Embed.from_dict(embed)
                await msg.delete()
                reaction_message = await ctx.send(embed = final_embed)
                reactions = ['<:tick:820320509564551178>','<:xmark:820320509211574284>']
                def reactioncheck(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in reactions
                for emoji in reactions:
                    await reaction_message.add_reaction(emoji)
                    
                try:
                    reaction,user = await self.bot.wait_for('reaction_add', timeout=80.0, check=reactioncheck)
                except asyncio.TimeoutError:
                    await ctx.error('Time Up')
                    await reaction_message.delete()
                    return
                else:
                    if str(reaction.emoji) == '<:tick:820320509564551178>':
                        await custom_data.update(close_message_embed = message.content)
                        await ctx.success(f'Done')
                    else:
                        await ctx.error('aborting')
                        await reaction_message.delete()
                        return

    #======= slotlist-embed-format ===========#
    # @smanager.command(name='edit-slotlist-embed-format')
    # @commands.has_role('teabot-smanger')
    # async def smanager_edit_slotlist_embed_format(self,ctx,*,custom_id:int):
    #     """Edits The Custom Slotlist Format"""
    #     #TODO Complete This
    #     scrims_manager = await self.bot.db.fetchrow('SELECT * FROM server_configs WHERE guild_id = $1',ctx.guild.id)
    #     if scrims_manager['scrims_manager'] == False:
    #         raise expectations.ScrimsManagerNotSetup

    #     embed = discord.Embed(title = f'',description = f'''  ''',color = self.bot.color)
    #     await ctx.send(embed=embed)


    @smanager.command(name='send-slotslist')
    @commands.has_role('teabot-smanger')
    async def smanager_send_slotslist(self,ctx,*,custom_id:ScrimConverter):
        """
        Send's The Slotlist To Setuped Channel
        """
        guild = GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        custom_data = custom_id

        if custom_data.is_running == True:
            return await ctx.error(f'Registration Is Going On')

        if custom_data.is_registeration_done_today == False:
            return await ctx.error(f'Registration For Today Is Not Done')

        confirmation = ConfirmationPrompt(ctx,self.bot.color)
        confirmation.confirm(title = f"Slotlist For {custom_data.custom_title}",description = f'''```py\n{makeslotlist(custom_data)}\n```''')
        if confirmation.confirmed:
            embed = discord.Embed(title = f"Slotlist For {custom_data.custom_title}",description = f'''```py\n{makeslotlist(custom_data)}\n```''',color = self.bot.color)
            await custom_data.slotlistch.send(embed =embed)
            await confirmation.update(description = f'{ctx.emote.tick} | Successfully sended the slotlist')
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)

    @smanager.command(name='config')
    @commands.has_role('teabot-smanger')
    async def smanager_config(self,ctx):
        """See The Scrims Manager Configuration For This Server"""
        guild = await GuildData.get(guild_id = ctx.guild.id)
        allscrims = await ScrimData.filter(guild_id=ctx.guild.id).all()
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        if not len(allscrims):
            return await ctx.error(f'This server does not have any customs')

        to_paginate = []
        for idx, scrim in enumerate(allscrims, start=1):
            reg_channel = getattr(scrim.regch, "mention", "`Channel Deleted!`")
            slot_channel = getattr(scrim.slotlistch, "mention", "`Channel Deleted!`")
            _role = getattr(scrim.correctregrole, "mention", "`Role Deleted!`")
            open_time = (scrim.open_time).strftime("%I:%M %p")
            close_time = 'None'
            if scrim.close_time != None:
                close_time = (scrim.close_time).strftime("%I:%M %p")
            _ping_role = getattr(scrim.pingrole, "mention", "`None`")
            _open_role = getattr(scrim.openrole, "mention", "`None`")



            mystring = f""" Scrim ID: `{scrim.c_id}`\n 
            Name: `{scrim.custom_title}`\n 
            Registration Channel: {reg_channel}\n 
            Slotlist Channel: {slot_channel}\n 
            Role: {_role}\n 
            Ping Role: {_ping_role}\n 
            Open Role: {_open_role}\n 
            Mentions: `{scrim.num_correct_mentions}`\n 
            Total Slots: `{scrim.num_slots}`\n 
            Reserved Slots : `{len(scrim.reserverd_slots)}`\n 
            Open Time: `{open_time}`\n 
            Close Time: `{close_time}`\n 
            Toggle: `{scrim.toggle}`"""

            to_paginate.append(f"**`<------ {idx:02d} ------>`**\n\n{mystring}\n")

        paginator = Pages(
            ctx, title="Total Custom Setuped: {}".format(len(to_paginate)), entries=to_paginate, per_page=1, show_entry_count=True
        )

        await paginator.paginate()
        


##############################################################################################################################
#================================================== Tag Check ===============================================================#
##############################################################################################################################
    
    @commands.group(aliases = ['tag-check','tgcheck','tg-check'])
    async def tag_check(self,ctx):
        '''
        Sytem For Tag Check
        '''
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @tag_check.command(name = 'set')
    @commands.has_role('teabot-smanger')
    async def tag_check_set(self,ctx,check_channel:discord.TextChannel,*,mentions_required:int):
        '''
        Setups The Tag Check In You Server
        '''
        scrims_manager = await self.bot.db.fetchrow('SELECT * FROM server_configs WHERE guild_id = $1',ctx.guild.id)
        if scrims_manager['scrims_manager'] == False:
            raise expectations.ScrimsManagerNotSetup

        count = await TagCheck.filter(guild_id=ctx.guild.id).count()
        guild = await GuildData.get(guild_id=ctx.guild.id)

        if count >= 2 and not guild.is_guild_premium:
            await ctx.error("You Can't Set More The 2 Tag Checks")
            return

        tag_check = TagCheck(
            guild_id=ctx.guild.id
        )

        if await TagCheck.filter(ch_id = check_channel.id).count():
            return await ctx.error(f"You Already Have Tag Check Setuped In {check_channel.mention}")

        tag_check.ch_id = check_channel.id
        tag_check.mentions_required = mentions_required
        await tag_check.save()
        await ctx.success(f"succesfully setuped tag check in {check_channel.mention} and you tag check id is: `{tag_check.id}`")

    @tag_check.command(name='config')
    @commands.has_role('teabot-smanger')
    async def tag_check_config(self,ctx):
        """See The Tag CHeck Configuration For This Server"""
        guild = await GuildData.get(guild_id = ctx.guild.id)
        alltagchek = await TagCheck.filter(guild_id=ctx.guild.id).all()
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        if not len(alltagchek):
            return await ctx.error(f'This server does not have any tag check setuped')

        to_paginate = []
        for idx, tagcheck in enumerate(alltagchek, start=1):
            channel = getattr(tagcheck.tagcheck_ch, "mention", "`Channel Deleted!`")

            mystring = f"""Tag Check ID: `{tagcheck.c_id}`\n 
            Channel: `{channel}`\n 
            Mentions Required: {tagcheck.mentions_required}\n 
            """

            to_paginate.append(f"**`<------ {idx:02d} ------>`**\n\n{mystring}\n")

        paginator = Pages(
            ctx, title="Total Tag Check Setuped: {}".format(len(to_paginate)), entries=to_paginate, per_page=1, show_entry_count=True
        )

        await paginator.paginate()

    @tag_check.command(name = 'toggle')
    @commands.has_role('teabot-smanger')
    async def tag_check_toggle(self,ctx,tag_check_id:TagCheckConverter):
        '''
        Toggles This Tag Check
        '''
        guild = await GuildData.get(guild_id = ctx.guild.id)
        if guild.scrims_manager == False:
            raise expectations.ScrimsManagerNotSetup

        data = tag_check_id

        if data.toggle == False:
            await data.update(toggle = True)
            await ctx.success(f'Successfully enabled tag check for `{data.id}`')
            return
        else:
            await data.update(toggle = False)
            await ctx.success(f'Successfully disabled tag check for `{data.id}`')
            return

#todo make delete command for tag check

####################################################################################################################
#===================================================== Other Commnads =============================================#
####################################################################################################################

    @commands.command(aliases=("idp",)) 
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def shareidp(self, ctx, room_id, room_password, map,ping_role: discord.Role = None):
        """
        Share Id/pass with embed.
        Message is automatically deleted after 30 minutes.
        """
        await ctx.message.delete()
        embed = discord.Embed(title=f"Custom Room. JOIN NOW!",color=self.bot.color)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Room ID:", value=room_id,inline=False)
        embed.add_field(name="Room Password:", value=room_password,inline=False)
        embed.add_field(name="Map:", value=map,inline=False)
        embed.set_footer(text=f"IDP Shared by: {ctx.author} | Auto delete in 30 minutes.", icon_url=ctx.author.avatar_url)
        msg = await ctx.send(
            content=ping_role.mention if ping_role else None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        self.bot.loop.create_task(delete_denied_message(msg, 30 * 60))
#  Todo: Update These to tortoise
####################################################################################################################
#======================================================== Easy Tagging ============================================#
####################################################################################################################

    @commands.group(invoke_without_command = True,aliases = ['ez_tag','eztag','ez-tag','etag'])
    async def easytag(self,ctx):
        """
        Handles Easy Tagging In Your Server
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @easytag.command(name = 'set')
    @commands.has_permissions(manage_guild = True)
    async def easytag_set(self,ctx,channel:discord.TextChannel):
        """
        Setups Easy tagging In Your Server
        """
        count = await EasyTag.filter(guild_id=ctx.guild.id).count()
        guild = await GuildData.get(guild_id=ctx.guild.id)

        if count >= 2 and not guild.is_guild_premium:
            await ctx.error("You Can't Set More The 2 Tag Checks")
            return

        easytag = EasyTag(
            guild_id=ctx.guild.id
        )

        if await EasyTag.filter(ch_id = channel.id).count():
            return await ctx.error(f"You Already Have Tag Check Setuped In {channel.mention}")

        easytag.ch_id = channel.id
        await easytag.save()
        await ctx.success(f"succesfully setuped easy tagg in {channel.mention} and you easy tag id is: `{easytag.id}`")

    @easytag.command(name = 'toggle')
    @commands.has_permissions(manage_guild = True)
    async def easytag_toggle(self,ctx):
        """Toggles Easy Tagging In Server"""
        data = await self.bot.db.fetchrow('SELECT * FROM smanager.ez_tag WHERE guild_id = $1',ctx.guild.id)
        if not data:
            return await ctx.error('You Do Not Easy Tag Setuped') 
        if data['toggle'] == False:
            await ctx.db.execute('UPDATE ez_tag SET toggle = $1 WHERE guild_id = $2',True,ctx.guild.id)
            return await ctx.success('Successfully Turned On Easy Tagging')
        else:
            await ctx.db.execute('UPDATE ez_tag SET toggle = $1 WHERE guild_id = $2',False,ctx.guild.id)
            return await ctx.success('Successfully Turned Off Easy Tagging')



####################################################################################################################
#===================================================== Tournament Manager =========================================#
####################################################################################################################



def setup(bot):
    bot.add_cog(Esports(bot))
    bot.add_cog(EsportsListners(bot))
