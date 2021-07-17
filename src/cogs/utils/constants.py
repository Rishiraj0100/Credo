import re
from typing import Union
__all__ = (
    'Replies',
    'Emotes',
    'ColorsList',
    'Regex',
    "premium_perks"
)
premium_perks = {
    "Premium Role": ["❌", "✅"],
    "Scrims": ["7", "Unlimited"],
    "Tourneys": ["3", "Unlimited"],
    "TagCheck": ["4", "Unlimited"],
    "EasyTags": ["2", "Unlimited"],
    "Autorole": ["1", "Unlimited"],
    # "Custom Footer": ["❌", "✅"],
    # "Custom Color": ["❌", "✅"],
    "Giveaway": ["5", "Unlimited"],
    "Ptable Setup": ["2", "Unlimited"],
    "Edit Ptable Watermark": ["❌", "✅"],
    "Level Roles": ["5","Unlimited"],
    "Invite Roles": ["5","Unlimited"],
    "Reaction Roles": ["5","Unlimited"],
    "Automated Moderation Rule": ["5","Unlimited"],
    "Auto Ban/Kick Rules": ["5","Unlimited"]
}

class Replies():
    ERROR_REPLIES = [
    "Please don't do that.",
    "You have to stop.",
    "Do you mind?",
    "In the future, don't do that.",
    "That was a mistake.",
    "You blew it.",
    "You're bad at computers.",
    "Are you trying to kill me?",
    "Noooooo!!",
    "I can't believe you've done this",
    ]

    NEGATIVE_REPLIES = [
        "Noooooo!!",
        "Nope.",
        "I don't think so.",
        "Not gonna happen.",
        "Huh? No.",
        "Nah.",
        "Naw.",
        "Not likely.",
        "No way,",
        "Not in a million years.",
        "Fat chance.",
        "Certainly not.",
        "NEGATORY.",
        "Nuh-uh.",
        "Not in my house!",
    ]

    POSITIVE_REPLIES = [
        "Yep.",
        "Absolutely!",
        "Can do!",
        "Affirmative!",
        "Yeah okay.",
        "Sure.",
        "Sure thing!",
        "You're the boss!",
        "Okay.",
        "No problem.",
        "I got you.",
        "Alright.",
        "You got it!",
        "ROGER THAT",
        "Of course!",
        "Aye aye, cap'n!",
        "I'll allow it.",
    ]
    OWNER_MENTION_REPLIES=[
        ':expressionless:',
        '<:emoji_34:806415181332742194>',
        '<:emoji_35:806415225083265026>',
        '<:emoji_30:806415048506998814>',
        '<:emoji_33:806415151585820692>',
        '<:emoji_31:806415082798972928>',
        '<:emoji_29:806414962746327081>'
    ]

class Emotes():
    xmark = '<:xmark:820320509211574284>'
    tick = '<:tick:820320509564551178>'
    error = '<:error:820162683147911169>'
    loading = '<a:loading:824225352573255680>'
    questionmark = '<:questionmark:820319249867866143>'
    info = '<:info:820332723121684530>'
    
    voice_channel = '<:Voice_channels:820162682883014667>'
    text_channel = '<:Text_Channel:820162682970832897>'
    category = '<:category:857479667169624096>'
    deafen = '<:Deafen:857494111245172756>'
    server_deafen = '<:serverdeafean:857494163293470720>'
    server_muted = '<:servermute:857494273527382047> '
    muted = '<:muted:857494250202333235>'

    verified_bot = '<:DiscordVerifiedBot:857481883029078046>' 
    verified_bot_developer = '<:BotDeveloper:857481801752248341>' 
    bot = '<:bot:857481658261176330>'
    bug_hunter_lvl_2 = '<:BUGHUNTER_LEVEL_2:857481574415859722>' 
    bug_hunter_lvl_1 = '<:bug_hunter:857481506645737502>'
    hyper_squad_events = '<:HypeSquadevents:857481397220147260>' 
    hyper_squad = '<:hypesquad:857481224427274260>' 
    partner = '<:partner:857481126384500794>' 
    staff = '<:staff:857480983523491870> '
    supporter = '<:supporter:857480656413392908>' 
    balance = '<:balance:857480532835958804> '
    bravery = '<:bravery:857480348253290516> '
    brilliance = '<:brilliance:857480448229638164>'
    rps = '<:richpresence:857480210802278432>'
    partnered_server_badge = '<:partneredServerOwner:857491831638196224>'
    discord_certified_moderator = '<:Discord_Certified_Moderator:857492383842566154>'
    
    youtube = '<:yotube:820657499895103518>'
    
    number_emojis = {
        1: "\u0031\ufe0f\u20e3",
        2: "\u0032\ufe0f\u20e3",
        3: "\u0033\ufe0f\u20e3",
        4: "\u0034\ufe0f\u20e3",
        5: "\u0035\ufe0f\u20e3",
        6: "\u0036\ufe0f\u20e3",
        7: "\u0037\ufe0f\u20e3",
        8: "\u0038\ufe0f\u20e3",
        9: "\u0039\ufe0f\u20e3"
    }

    x = "\U0001f1fd"
    o = "\U0001f1f4"

    switch_on ='<:switch_on:845865302571089930>'
    switch_off ='<:switch_off:845865362193252372>'

    booster_1_month = '<:Boosterfor1months:857483288872747008>' 
    booster_2_month = '<:Boosterfor2months:857483550362435625>' 
    booster_3_month = '<:Boosterfor3months:857483638420668457>' 
    booster_6_month = '<:Boosterfor6months:857483746291089451>' 
    booster_9_month = '<:Boosterfor9months:857483870055039018>' 
    booster_12_month = '<:Boosterfor12months:857483986946490389>'
    booster_15_month = '<:Boosterfor15months:857484712007696424>' 
    booster_18_month = '<:Boosterfor18months:857484104719400990>' 
    booster_24_month = '<:boosterfor24months:857484133298077736> '
    
    def regional_indicator(c: str) -> str:
        """Returns a regional indicator emoji given a character."""
        return chr(0x1F1E6 - ord("A") + ord(c.upper()))

    def keycap_digit(c: Union[int, str]) -> str:
        """Returns a keycap digit emoji given a character."""
        c = int(c)
        if 0 < c < 10:
            return str(c) + "\U0000FE0F\U000020E3"
        elif c == 10:
            return "\U000FE83B"
        raise ValueError("Invalid keycap digit")

class ColorsList():
    ...

class Regex():
    # This Invite Regex From https://github.com/python-discord/bot/blob/main/bot/utils/regex.py
    INVITE_RE = re.compile(
    r"(?:discord(?:[\.,]|dot)gg|"                     # Could be discord.gg/
    r"discord(?:[\.,]|dot)com(?:\/|slash)invite|"     # or discord.com/invite/
    r"discordapp(?:[\.,]|dot)com(?:\/|slash)invite|"  # or discordapp.com/invite/
    r"discord(?:[\.,]|dot)me|"                        # or discord.me
    r"discord(?:[\.,]|dot)li|"                        # or discord.li
    r"discord(?:[\.,]|dot)io"                         # or discord.io.
    r")(?:[\/]|slash)"                                # / or 'slash'
    r"([a-zA-Z0-9\-]+)",                              # the invite code itself
    flags=re.IGNORECASE
)
