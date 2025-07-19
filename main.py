import sys
import discord
from bot.configuration import load_config, create_example_config
from bot import Bot

DEFAULT_CONFIG_PATH = "bot-config.ini"

try:
    config = load_config(DEFAULT_CONFIG_PATH)
except RuntimeError as e:
    print(f"Error: {e}. Creating example config file...")
    create_example_config(DEFAULT_CONFIG_PATH)
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
