import time

from discord import Message
from discord.ext import commands

from bot.configuration import BotConfig, Config, ModelConfig


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config


def process_raw_response(response: str, model_config: ModelConfig) -> str:
    return ""


async def process_llm_response(
    response_stream,
    message: Message,
    bot_config: BotConfig,
    model_config: ModelConfig | None,
):
    raw_response = ""
    response = ""
    last_edit_time = time.time()

    for chunk in response_stream:
        raw_response += chunk["response"]

        response = (
            process_raw_response(raw_response, model_config)
            if model_config is not None
            else raw_response
        )

        now = time.time()
        if now - last_edit_time >= bot_config.edit_delay:
            await message.edit(content=response)
            last_edit_time = now

    # process last chunk
    if response != "":
        await message.edit(content=response)
