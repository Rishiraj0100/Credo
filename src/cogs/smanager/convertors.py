from models import *
from discord.ext import commands
import tortoise.exceptions

__all__=(
    "ScrimConverter",
    "EasyTagConverter",
    "TagCheckConverter"
)

class ScrimConverter(commands.Converter, ScrimData):
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await ScrimData.get(pk=argument, guild_id=ctx.guild.id)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise commands.BadArgument(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")
        
class TagCheckConverter(commands.Converter, TagCheck):
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await TagCheck.get(pk=argument, guild_id=ctx.guild.id)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise commands.BadArgument(f"This is not a valid TagCheck ID.\n\nGet a valid ID with `{ctx.prefix}tag_check config`")
        
class EasyTagConverter(commands.Converter, EasyTag):
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await EasyTag.get(pk=argument, guild_id=ctx.guild.id)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise commands.BadArgument(f"This is not a valid EasyTag ID.\n\nGet a valid ID with `{ctx.prefix}ez_tag config`")