from tortoise import models, fields
import discord
from typing import Optional

__all__ = (
    "GuildData",
    "Brodcast"
)

class GuildData(models.Model):
    class Meta:
        table = "server_configs"
    guild_id = fields.BigIntField(pk=True)
    is_bot_setuped = fields.BooleanField(default=False)
    scrims_manager = fields.BooleanField(default=False)
    autorole_toggle = fields.BooleanField(default=False)
    autorole_bot_toggle = fields.BooleanField(default=False)
    autorole_human_toggle = fields.BooleanField(default=False)
    autorole_human = fields.BigIntField(null = True)
    autorole_bot = fields.BigIntField(null = True)
    automeme_toogle = fields.BooleanField(default=False) 
    automeme_channel_id = fields.BigIntField(null = True)
    is_guild_premium = fields.BooleanField(default = False)

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def autorolehuman(self):
        if self.guild is not None:
            return self.guild.get_role(self.autorole_human)

    @property
    def autorolebot(self):
        if self.guild is not None:
            return self.guild.get_role(self.autorole_bot)

    @property
    def automeme_channel(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, id = self.automeme_channel_id)

class Brodcast(models.Model):
    class Meta:
        table = "brodcast"
    guild_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField(null = True)

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def brodcast_channel(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, id = self.channel_id)

