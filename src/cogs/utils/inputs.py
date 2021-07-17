import asyncio
import dateparser
from datetime import datetime, timedelta
from discord.ext.commands.converter import RoleConverter, TextChannelConverter, MemberConverter
from .constants import *
from .expectations import *
import discord

__all__ = (
    "role_input",
    "safe_delete",
    "channel_input",
    "integer_input"
)

async def safe_delete(message) -> bool:
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        return False
    else:
        return True

async def channel_input(ctx, check, timeout=120, delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("Time Up!")
    else:
        if len(message.channel_mentions) == 0 or len(message.channel_mentions) > 1:
            raise InputError('You Did Not Mentioned Correct Channel Please Try Agin By Running Same Command')
        try:
            channel = await TextChannelConverter().convert(ctx, message.content)
        except:
            raise InputError('You Did Not Mentioned Correct Channel Please Try Agin By Running Same Command')
        else:
            if not message.permissions_for(ctx.me).read_messages:
                raise InputError(
                        f"Unfortunately, I don't have read messages permissions in {message.mention}."
                )
            
            if not message.permissions_for(ctx.me).send_messages:
                raise InputError(
                    f"Unfortunately, I don't have send messages permissions in {message.mention}."
                )
            if delete_after:
                await safe_delete(message)
        return channel

async def role_input(ctx, check, timeout=120,delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("Time Up!")
    else:
        if len(message.role_mentions) == 0 or len(message.role_mentions) > 1:
            raise InputError('You Did Not Mentioned Correct Role Please Try Agin By Running Same Command')
        try:
            role = await RoleConverter().convert(ctx, message.content)
        except:
            raise InputError('You Did Not Mentioned Correct Role Please Try Agin By Running Same Command')
        else:
            if role.managed:
                raise InputError(f"Role is an integrated role and cannot be added manually.")

            if role > ctx.me.top_role:
                raise InputError(
                        f"The position of {role.mention} is above my top role. So I can't give it to anyone.\nKindly move {ctx.me.top_role.mention} above {role.mention} in Server Settings."
                    )

            if ctx.author.id != ctx.guild.owner_id:
                if role > ctx.author.top_role:
                    raise InputError(
                            f"The position of {role.mention} is above your top role {ctx.author.top_role.mention}."
                        )

        if delete_after:
            await safe_delete(message)

        return role


async def integer_input(ctx, check, timeout=120, limits=(None, None), delete_after=False):
    def new_check(message):
        if not check(message):
            return False

        try:
            if limits[1] is not None:
                if len(message.content) > len(str(limits[1])):  # This is for safe side, memory errors u know :)
                    return False

            digit = int(message.content)

        except ValueError:
            return False
        else:
            if not any(limits):  # No Limits
                return True

            low, high = limits

            if all(limits):
                return low <= digit <= high
            else:
                if low is not None:
                    return low <= digit
                else:
                    return high <= digit

    try:
        message = await ctx.bot.wait_for("message", check=new_check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("Time Up!")
    else:
        if delete_after:
            await safe_delete(message)

        return int(message.content)