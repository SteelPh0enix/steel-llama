from discord.ext import commands
from bot.configuration import Config, BotConfig, ModelConfig
from discord import Message
import time


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config


async def process_llm_response(
    response_stream,
    message: Message,
    bot_config: BotConfig,
    model_config: ModelConfig | None,
):
    content = ""
    last_edit_time = time.time()

    for chunk in response_stream:
        content += chunk["response"]
        now = time.time()
        if now - last_edit_time >= bot_config.edit_delay:
            await message.edit(content=content)
            last_edit_time = now

    # process last chunk
    if content != "":
        await message.edit(content=content)
