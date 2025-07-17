import json

DB_FILE = 'prefixes.json'

def _load_prefixes():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def _save_prefixes(prefixes):
    with open(DB_FILE, 'w') as f:
        json.dump(prefixes, f, indent=4)

async def get_prefix(bot, message):
    # This function is typically used by discord.ext.commands.Bot for dynamic prefixes.
    # Since all commands are now slash commands, this function's primary use is for
    # compatibility or if prefix commands are re-introduced.
    prefixes = _load_prefixes()
    return prefixes.get(str(message.guild.id), 'py ')

async def set_prefix(guild_id: int, new_prefix: str):
    prefixes = _load_prefixes()
    prefixes[str(guild_id)] = new_prefix
    _save_prefixes(prefixes)
