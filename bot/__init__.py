import time

from discord import Message
from discord.ext import commands

from bot.configuration import BotConfig, Config, ModelConfig
from bot.response import LLMResponse


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config


def process_raw_response(raw_response: str, model_config: ModelConfig | None) -> str:
    thinking_tags: tuple[str, str] | None = None
    if (
        (model_config is not None)
        and (model_config.thinking_prefix is not None)
        and (model_config.thinking_suffix is not None)
    ):
        thinking_tags = (model_config.thinking_prefix, model_config.thinking_suffix)

    response = LLMResponse(raw_response, thinking_tags)

    # there's actual message in there
    if (response.content is not None) and (len(response.content) > 0):
        # and even with some thoughts
        if (response.thoughts is not None) and (len(response.thoughts) > 0):
            return f"*{response.thoughts}*\n\n{response.content}"
        # or not
        return response.content

    # thinking in progress
    if (response.thoughts is not None) and (len(response.thoughts) > 0):
        return f"*{response.thoughts}*"

    return "Waiting for response..."


async def process_llm_response(
    response_stream,
    message: Message,
    bot_config: BotConfig,
    model_config: ModelConfig | None,
):
    response = ""
    last_edit_time = time.time()

    for chunk in response_stream:
        response += chunk["response"]

        if time.time() - last_edit_time >= bot_config.edit_delay:
            await message.edit(content=process_raw_response(response, model_config))
            last_edit_time = time.time()

    # process last chunk
    if response != "":
        await message.edit(content=process_raw_response(response, model_config))
