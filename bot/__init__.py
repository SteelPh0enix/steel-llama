import time

from discord import Message
from discord.ext import commands

from bot.configuration import BotConfig, Config, ModelConfig


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config


def process_thinking_output(response: str, model_config: ModelConfig, replacement: str = "*") -> str:
    if model_config.thinking_prefix is not None and model_config.thinking_suffix is not None:
        thinking_prefix_position = response.find(model_config.thinking_prefix)

        # thinking tags may be followed with whitespace, which must be removed
        # otherwise, Discord won't render the text properly if replacement is used for formatting (like '*')
        if thinking_prefix_position != -1:
            # special case - if thinking prefix is the only part of the message.
            if response.strip() == model_config.thinking_prefix:
                return f"{replacement}Thinking...{replacement}"

            response = replacement + response[thinking_prefix_position + len(model_config.thinking_prefix) :].lstrip()

            thinking_suffix_position = response.find(model_config.thinking_suffix)
            if thinking_suffix_position != -1:
                response = (
                    response[:thinking_suffix_position].rstrip()
                    + replacement
                    + response[thinking_suffix_position + len(model_config.thinking_suffix) :]
                )
            else:
                response = response.rstrip() + replacement

    return response


def process_raw_response(response: str, model_config: ModelConfig | None) -> str:
    if model_config is not None:
        return process_thinking_output(response, model_config)
    return response


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
