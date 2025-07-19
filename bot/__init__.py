from discord.ext import commands
from bot.configuration import Config
from discord import Message
import time


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config


async def process_llm_response(response_stream, message: Message, config: Config):
    content = ""
    last_edit_time = time.time()

    for chunk in response_stream:
        content += chunk["response"]
        now = time.time()
        if now - last_edit_time >= config.bot.edit_delay:
            await message.edit(content=content)
            last_edit_time = now

    # process last chunk
    if content != "":
        await message.edit(content=content)
