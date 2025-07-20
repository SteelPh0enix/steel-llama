import sys

import discord

from pathlib import Path
from bot import Bot
from bot.configuration import Config

DEFAULT_CONFIG_PATH = Path("./bot-config.ini")

try:
    config = Config.from_file(DEFAULT_CONFIG_PATH)
except RuntimeError as e:
    print(f"Error: {e}. Creating example config file...")
    Config.write_default_config(DEFAULT_CONFIG_PATH)
    print(
        f"Example config created. Please edit '{DEFAULT_CONFIG_PATH}' with your settings."
    )
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

bot = Bot(config, command_prefix=config.bot.bot_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

    try:
        await bot.load_extension("bot.bot_commands")
        print("Loaded bot commands!")
    except Exception as e:
        print(f"Failed to load extension: {e}")


bot.run(config.bot.discord_api_key)
