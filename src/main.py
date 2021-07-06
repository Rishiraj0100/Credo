import discord,traceback,jishaku,asyncio,mystbin
from discord.ext import commands
from cogs.utils import context
import config
from cogs.utils.jsonreaders import Config
from colorama import Fore,init
# from .cogs.utils.util import traceback_maker
from cogs.utils.constants import *  
from tortoise import Tortoise
import aiohttp
import logging
import pytz
from datetime import datetime

IST = pytz.timezone("Asia/Kolkata")

#================ LOGGING ===============#

class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')
    def filter(self,record):
        if record.levelname == "WARNING" and 'referencing an unknown' in record.msg:
            return False
        return True


max_bytes = 32*1024*1024
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.WARNING)
logging.getLogger('discord.state').addFilter(RemoveNoise())

discord_log = logging.getLogger()
discord_log.setLevel(logging.INFO)
discord_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord_handler.setFormatter(logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}',datefmt="%Y-%m-%d %H:%M:%S",style='{'))
discord_log.addHandler(discord_handler)

fmt = logging.Formatter(
    fmt="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
sh = logging.FileHandler(filename='tortoisedb.log', encoding='utf-8', mode='w')
sh.setLevel(logging.DEBUG)
sh.setFormatter(fmt)

# will print debug sql
logger_db_client = logging.getLogger("db_client") 
logger_db_client.setLevel(logging.DEBUG)
logger_db_client.addHandler(sh)

logger_tortoise = logging.getLogger("tortoise")
logger_tortoise.setLevel(logging.DEBUG)
logger_tortoise.addHandler(sh)


init(autoreset=True)
intents = discord.Intents.default()
intents.members = True

extensions = [
    # 'cogs.mod.mod',
    # 'cogs.fun',
    # 'cogs.utility',
    'cogs.events.error',
    'cogs.events.events',
    'cogs.teamisc.teabotmisc',
    # 'cogs.top',
    # 'cogs.teamisc.help',
    'cogs.admin',
    # 'cogs.bot_settings',
    # 'cogs.tasks',
    # 'cogs.smanager.smanager',
    # 'cogs.smanager.tasks',
    # 'cogs.events.autoevents',
    # 'cogs.events.botevents',
    'jishaku'
]


class TeaBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            strip_after_prefix=True,
            case_insensitive=True,
            chunk_guilds_at_startup=False,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, replied_user=True, users=True),
            activity=discord.Activity(type=discord.ActivityType.listening, name="*setup | *help"),
            fetch_offline_members=True,
            **kwargs,
        )
        self.OWNER = config.owners
        self.color = config.color
        self.guild = config.guild
        self.logo = config.logo
        self.client_id = config.client_id
        self.omdbapi_key = config.omdbapi_key
        self.weather_api_key = config.weather_api_key
        self.api_alexflipnote = config.api_alexflipnote
        self.top_gg = config.top_gg
        self.ksoft_api_key = config.ksoft_api_key
        self.tenor_apikey = config.tenor_apikey
        self.config = config
        self.defaultprefix = config.prefix
        self.loop = asyncio.get_event_loop()
        self.prefixes = Config('prefixes.json')
        self.binclient = mystbin.Client()
        self.emote = Emotes
        self.replies = Replies
        self.colorslist = ColorsList
        self.regex = Regex
        self.start_time = datetime.now(tz=IST)
        # self. = str
        asyncio.get_event_loop().run_until_complete(self.init_db())
        for extension in extensions:
            try:
                self.load_extension(extension)
                print(Fore.GREEN + f"{extension} was loaded successfully!")
            except Exception as e:
                tb = traceback.format_exception(type(e), e, e.__traceback__)
                tbe = "".join(tb) + ""
                print(Fore.RED + f"[WARNING] Could not load extension {extension}: {tbe}")
                # self.tr = tbe

    async def process_commands(self, message):
        ctx = await self.get_context(message,cls=context.Context)

        await self.invoke(ctx)

    async def get_prefix(self, msg: discord.Message) -> str:
        user_id = self.user.id
        prefix = ['config.prefix',f'<@!{user_id}> ', f'<@{user_id}> ']
        if msg.author.id == config.owners:
            prefix = ""
        else:
            prefix.extend(self.prefixes.get(msg.guild.id,[config.prefix]))
        return prefix

    @property
    def db(self):
        return Tortoise.get_connection("default")._pool

    async def init_db(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        await Tortoise.init(config.TORTOISE)
        await Tortoise.generate_schemas(safe=True)

        for mname, model in Tortoise.apps.get("models").items():
            model.bot = self

    def get_guild_prefixes(self, guild, *, local_inject=get_prefix):
        proxy_msg = discord.Object(id=0)
        proxy_msg.guild = guild
        return local_inject(self, proxy_msg)

    def get_raw_guild_prefixes(self, guild_id):
        return self.prefixes.get(guild_id, [config.prefix])

    async def set_guild_prefixes(self, guild, prefixes):
        if len(prefixes) == 0:
            await self.prefixes.put(guild.id, [])
        elif len(prefixes) > 10:
            raise RuntimeError('Cannot have more than 10 custom prefixes.')
        else:
            await self.prefixes.put(guild.id, sorted(set(prefixes), reverse=True))

bot = TeaBot()

@bot.command(hidden=True)
@commands.is_owner()
async def licog(ctx):
    await ctx.send(extensions)

try:
    bot.run(config.token)
except:
    print(Fore.RED + "--------------> Killed!! <---------------")
finally:
    print(Fore.RED + "--------------> Killed!! <---------------")