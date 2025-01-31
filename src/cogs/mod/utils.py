import argparse,discord
from collections import Counter
from discord.ext import commands

async def role_checker(ctx, role):
    if role.managed:
        await ctx.error(f"Role is an integrated role and cannot be added manually.")
        return False
    elif ctx.me.top_role.position <= role.position:
        await ctx.error(f"The position of {role.mention} is above my toprole ({ctx.me.top_role.mention})")
        return False
    elif not ctx.author == ctx.guild.owner and ctx.author.top_role.position <= role.position:
        await ctx.error(f"The position of {role.mention} is above your top role ({ctx.author.top_role.mention})")
        return False

    else:
        return True

class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)

def safe_reason_append(base, to_append):
    appended = base + f'({to_append})'
    if len(appended) > 512:
        return base
    return appended



class plural:
    def __init__(self, value):
        self.value = value
    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition('|')
        plural = plural or f'{singular}s'
        if abs(v) != 1:
            return f'{v} {plural}'
        return f'{v} {singular}'

async def do_removal(self, ctx, limit, predicate, *, before=None, after=None):
        if limit > 2000:
            return await ctx.send(f'Too many messages to search given ({limit}/2000)')

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        try:
            deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
        except discord.Forbidden as e:
            return await ctx.send('I do not have permissions to delete messages.')
        except discord.HTTPException as e:
            return await ctx.send(f'Error: {e} (try a smaller search?)')

        spammers = Counter(m.author.display_name for m in deleted)
        deleted = len(deleted)
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'**{name}**: {count}' for name, count in spammers)

        to_send = '\n'.join(messages)

        if len(to_send) > 2000:
            await ctx.send(f'Successfully removed {deleted} messages.', delete_after=10)
        else:
            await ctx.send(to_send, delete_after=10)


async def _basic_cleanup_strategy(self, ctx, search):
    count = 0
    async for msg in ctx.history(limit=search, before=ctx.message):
        if msg.author == ctx.me:
            await msg.delete()
            count += 1
    return { 'Bot': count }

async def _complex_cleanup_strategy(self, ctx, search):
    prefixes = tuple(self.bot.get_guild_prefixes(ctx.guild))
    def check(m):
        return m.author == ctx.me or m.content.startswith(prefixes)
    deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
    return Counter(m.author.display_name for m in deleted)

class Category(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.CategoryChannelConverter().convert(ctx, argument)
        except commands.ChannelNotFound:

            def check(category):
                return category.name.lower() == argument.lower()

            if found := discord.utils.find(check, ctx.guild.categories):
                return found

            raise commands.ChannelNotFound(argument)