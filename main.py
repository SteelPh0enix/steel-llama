import sys
import discord
from discord.ext import commands
from bot.configuration import load_config, create_example_config

try:
    config = load_config("bot-config.ini")
except RuntimeError as e:
    print(f"Error: {e}. Creating example config file...")
    create_example_config("bot-config.ini")
    print("Example config created. Please edit 'bot-config.ini' with your settings.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

bot = commands.Bot(command_prefix=config.bot.bot_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

    try:
        await bot.load_extension("bot.bot_commands")
    except Exception as e:
        print(f"Failed to load extension: {e}")


bot.run(config.bot.discord_api_key)
