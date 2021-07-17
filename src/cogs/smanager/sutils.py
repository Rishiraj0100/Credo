from discord.ext import commands
import discord,re,asyncio
from contextlib import suppress
from models import *
from prettytable import PrettyTable,ORGMODE

__all__ = (
    "get_slots",
    "find_team",
    "ScrimError",
    "safe_delete",
    "makeslotlist",
    "already_reserved",
    "available_to_reserve",
    "add_role_and_reaction",
    "delete_denied_message",
    "check_scrim_requirements"
)

def get_slots(slots):
    for slot in slots:
        yield slot.user_id
class ScrimError(commands.CommandError):
    pass

async def safe_delete(message):
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        return False
    else:
        return True


async def delete_denied_message(message: discord.Message, seconds=10):
    with suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
        await asyncio.sleep(seconds)
        await safe_delete(message)

def find_team(message):
    """Finds team name from a message"""
    content = message.content.lower()
    author = message.author
    teamname = re.search(r"team.*", content)
    if teamname is None:
        return f"{author}'s team"

    # teamname = (re.sub(r"\b[0-9]+\b\s*|team|name|[^\w\s]", "", teamname.group())).strip()
    teamname = re.sub(r"<@*#*!*&*\d+>|team|name|[^\w\s]", "", teamname.group()).strip()

    teamname = f"Team {teamname.title()}" if teamname else f"{author}'s team"
    return teamname


async def add_role_and_reaction(ctx, role):
    with suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await ctx.author.add_roles(role)

async def already_reserved(scrim: ScrimData):
    return list(i.num for i in await scrim.reserved_slots.all())


async def available_to_reserve(scrim: ScrimData):
    reserved = await already_reserved(scrim)
    return list(i for i in scrim.available_to_reserve if i not in reserved)


async def check_scrim_requirements(bot, message: discord.Message, scrim: ScrimData) -> bool:
    _bool = True

    if scrim.num_correct_mentions and not all(map(lambda m: not m.bot, message.mentions)):
        _bool = False
        if scrim.auto_delete_on_reject == True:
            bot.loop.create_task(delete_denied_message(message))
        bot.dispatch("deny_reg",message,"mentioned_bot")

    elif not len(message.mentions) >= scrim.num_correct_mentions:
        _bool = False
        bot.dispatch("scrim_registration_deny", message, "insufficient_mentions")

    elif message.author.id in get_slots(await scrim.assigned_slots.all()):
        _bool = False
        if scrim.auto_delete_on_reject == True:
            bot.loop.create_task(delete_denied_message(message))
        
        bot.dispatch("deny_reg",message,"allready_registerd")

    return _bool


async def makeslotlist(scrim: ScrimData):
    table = PrettyTable()
    table.set_style(ORGMODE)
    table.field_names = ["Slot No", "Team Name"]
    for i in await scrim.teams_registered:
        table.add_row([i.num, i.team_name])

    return table

