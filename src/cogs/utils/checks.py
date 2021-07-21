from discord.ext import commands
from . import emote,context,expectations

__all__ = (
    "SMNotUsable",
    "TMNotUsable",
    "can_use_sm",
    "can_use_tm"
)

class SMNotUsable(expectations.Credoerror):
    def __init__(self):
        super().__init__(f"You need either the `credo-smanager` role or `manage_guild` permissions to use scrims manager.")
class TMNotUsable(expectations.Credoerror):
    def __init__(self):
        super().__init__(f"You need either the `credo-tmanager` role or `manage_guild` permissions to use scrims manager.")

# def is_bot_setuped():
#     async def predicate(ctx):
#         if ctx.guild is None:
#             return False

#         data = await ctx.db.fetchval('SELECT is_bot_setuped FROM server_configs WHERE guild_id = $1',ctx.guild.id)
#         if data == False:
#             await ctx.send(f'{emote.error} | This Server Dose Not Have Bot Setuped Here Use `*setup`')
#             False
#             return

#         return True
#     return commands.check(predicate)
# def is_smanager_setuped():
#     async def predicate(ctx):
#         if ctx.guild is None:
#             return False

#         data = await ctx.db.fetchval('SELECT scrims_manager FROM server_configs WHERE guild_id = $1',ctx.guild.id)
#         if data == False:
#             await ctx.send(f'{emote.error} | This Server Dose Not Have Smanager Setuped Here Use `*smanager setup`')
#             False
#             return

#         return True
#     return commands.check(predicate)

def can_use_sm():
    """
    Returns True if the user has manage roles or credo-smanager role in the server.
    """

    async def predicate(ctx: context.Context):
        if ctx.author.guild_permissions.manage_guild or "credo-smanager" in (role.name.lower() for role in ctx.author.roles):
            return True
        else:
            raise SMNotUsable()

    return commands.check(predicate)

def can_use_tm():
    """
    Returns True if the user has manage roles or credo-tmanager role in the server.
    """

    async def predicate(ctx: context.Context):
        if ctx.author.guild_permissions.manage_guild or "credo-tmanager" in (role.name.lower() for role in ctx.author.roles):
            return True
        else:
            raise TMNotUsable()

    return commands.check(predicate)