client_id   = '' 
token = ''
color = 
guild = 
logo = ''
omdbapi_key = ''
weather_api_key = ''
api_alexflipnote = ''
top_gg = ''
ksoft_api_key = ''
tenor_apikey = ''
prefix = 't?'
owner = 

TORTOISE = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "",
                "port": "",
                "user": "",
                "password": "",
                "database": "",
                "max_cached_statement_lifetime": 0,
                "max_cacheable_statement_size": 0,
            },
        }
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "Asia/Kolkata",
}

POSTGRESQL = {
    "username":"",
    "password":"",
    "host":"",
    "database":"",
    "port":""
}