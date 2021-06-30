from tortoise import models, fields
import discord
from typing import Optional
from .fields import * 

__all__ = (
    "TMSlot",
    "EasyTag",
    "TagCheck",
    "ScrimData",
    "AssignedSlot",
    "ReservedSlot",
)

class ScrimData(models.Model):
    class Meta:
        table = "custom_data"

    c_id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    toggle = fields.BooleanField(default=True)
    slotlist_ch = fields.BigIntField()
    reg_ch = fields.BigIntField()
    num_slots = fields.IntField(default = 25)
    reserverd_slots = fields.IntField(null=True)
    available_slots = ArrayField(fields.IntField(), default=list)
    num_correct_mentions = fields.IntField(default = 1)
    correct_reg_role = fields.BigIntField()
    ping_role = fields.BigIntField()
    open_role = fields.BigIntField()
    custom_title = fields.TextField(default="TeaBot-Scrims")

    open_time = TimeWithoutTimeZoneField()
    close_time = TimeWithoutTimeZoneField()

    is_registeration_done_today = fields.BooleanField(default=False)
    is_running = fields.BooleanField(default=False)
    auto_clean = fields.BooleanField(default=False)

    open_on_sunday = fields.BooleanField(default=True)
    open_on_monday = fields.BooleanField(default=True)
    open_on_tuesday = fields.BooleanField(default=True)
    open_on_wednesday = fields.BooleanField(default=True)
    open_on_thursday = fields.BooleanField(default=True)
    open_on_friday = fields.BooleanField(default=True)
    open_on_saturday = fields.BooleanField(default=True)

    auto_slot_list_send = fields.BooleanField(default=False)
    auto_delete_on_reject = fields.BooleanField(default=False)

    slotlist_format = fields.TextField(null=True)

    assigned_slots: fields.ManyToManyRelation["AssignedSlot"] = fields.ManyToManyField("models.AssignedSlot")
    reserved_slots: fields.ManyToManyRelation["ReservedSlot"] = fields.ManyToManyField("models.ReservedSlot")

    open_message_embed = fields.CharField(default = '''{
  "title": ":tools: **Registartion Opened** :tools:",
  "description": "Total Slots = <<available_slots>>/<<total_slots>>[<<reserved_slots>>]\\n\nMinimum Mentions = <<mentions_required>>\n",
  "color": 53380
}''',max_length=10485760)
    close_message_embed = fields.CharField(default = '''{
  "description": ":lock: | **__Registration Is Closed Now.__**",
  "color": 53380
}''',max_length=10485760)

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def regch(self):
        if self.guild is not None:
            discord.utils.get(self.guild.text_channels, id = self.reg_ch)

    @property
    def log_ch(self):
        if self.guild is not None:
            discord.utils.get(self.guild.text_channels, name = "teabot-sm-logs")

    @property
    def slotlistch(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, id = self.slotlist_ch)

    @property
    def correctregrole(self):
        if self.guild is not None:
            return self.guild.get_role(self.correct_reg_role)

    @property
    def pingrole(self):
        if self.guild is not None:
            return self.guild.get_role(self.ping_role)

    @property
    def openrole(self):
        if self.guild is not None:
            return self.guild.get_role(self.open_role)
            
    @property
    def teams_registered(self):  # This should be awaited
        return self.assigned_slots.order_by("num").all()

    @property
    async def reserved_user_ids(self):
        return (i.user_id for i in await self.reserved_slots.all())


class BaseSlot(models.Model):
    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    num = fields.IntField(null=True)  # this will never be null but there are already records in the table so
    team_name = fields.TextField(null=True)
    members = ArrayField(fields.BigIntField(), default=list,null=True)
    leader_id = fields.BigIntField(null=True)


class AssignedSlot(BaseSlot):
    class Meta:
        table = "assigned_slots"

    message_id = fields.BigIntField(null=True)
    jump_url = fields.TextField(null=True)


class ReservedSlot(BaseSlot):
    class Meta:
        table = "reserved_slots"


class TagCheck(models.Model):
    class Meta:
        table = "tag_check"
    id = fields.IntField(pk = True,index =True)
    guild_id = fields.BigIntField()
    ch_id = fields.BigIntField()
    toggle = fields.BooleanField(default=True)
    mentions_required = fields.IntField()

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def tagcheck_ch(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, id = self.ch_id)

class EasyTag(models.Model):
    class Meta:
        table = "ez_tag"
    id = fields.IntField(pk = True,index =True)
    guild_id = fields.BigIntField()
    ch_id = fields.BigIntField()
    toggle = fields.BooleanField(default=True)

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def easytag_ch(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, id = self.ch_id)


class Tournament(models.Model):
    class Meta:
        table = "tm_data"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    tm_name = fields.CharField(max_length=200, default="TeaBot-tournament")
    registration_channel_id = fields.BigIntField(index=True)
    confirm_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_mentions = fields.IntField()
    total_slots = fields.IntField()
    open_role_id = fields.BigIntField(null=True)
    closed = fields.BooleanField(default=False)

    assigned_slots: fields.ManyToManyRelation["TMSlot"] = fields.ManyToManyField("models.TMSlot")

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def logschan(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, name="teabot-tournament-logs")

    @property
    def registration_channel(self):
        if self.guild is not None:
            return self.guild.get_channel(self.registration_channel_id)

    @property
    def confirm_channel(self):
        if self.guild is not None:
            return self.guild.get_channel(self.confirm_channel_id)

    @property
    def role(self):
        if self.guild is not None:
            return self.guild.get_role(self.role_id)

    @property
    def open_role(self):
        if self.guild is not None:
            if self.open_role_id != None:
                return self.guild.get_role(self.open_role_id)
            else:
                return self.guild.default_role

    @property
    def modrole(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.roles, name="teabot-tournament-mod")
            
class TMSlot(models.Model):
    class Meta:
        table = "tm_Slots"

    id = fields.BigIntField(pk=True)
    num = fields.IntField()
    team_name = fields.TextField()
    leader_id = fields.BigIntField()
    members = ArrayField(fields.BigIntField(), default=list,null=True)
    jump_url = fields.TextField(null=True)

