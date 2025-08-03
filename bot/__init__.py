import time

from discord import Message
from discord.abc import Messageable
from discord.ext import commands

from bot.chat_message import ChatMessage, MessageRole
from bot.chat_session import ChatSession, SqliteChatSession
from bot.configuration import BotConfig, Config, ModelConfig
from bot.llm_response import LLMResponse

DiscordMessageLengthLimit: int = 2000


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.sessions: list[ChatSession] = []
        SqliteChatSession.create_database(self.config.bot.session_db_path)

    def find_session(self, session_name: str, owner_id: int) -> ChatSession | None:
        for session in self.sessions:
            if session.name == session_name and session.owner_id == owner_id:
                return session
        return None

    def load_session_from_db(self, session_name: str, owner_id: int) -> ChatSession | None:
        if (stored_session := self.find_session(session_name, owner_id)) is not None:
            return stored_session

        session = SqliteChatSession(owner_id, session_name, db_path=self.config.bot.session_db_path)
        if not session.load():
            return None

        self.sessions.append(session)

        return session

    async def create_temporary_session(
        self,
        session_name: str,
        llm_user_id: int,
        channel: Messageable,
        history_depth: int = 100,
        preserve_last_message: bool = False,
    ) -> ChatSession:
        session = ChatSession(
            owner_id=self.config.admin.id,
            name=session_name,
            model=self.config.models.default_model,
            system_prompt=self.config.bot.default_system_prompt,
        )
        messages_history = []

        async for message in channel.history(limit=history_depth + (0 if preserve_last_message else 1)):
            messages_history.append(message)

        for message in reversed(messages_history[1:]):
            role = MessageRole.ASSISTANT if message.author.id == llm_user_id else MessageRole.USER
            session.add_message(ChatMessage.from_discord_message(message, role, session.name, session.owner_id))

        if preserve_last_message:
            message = messages_history[0]
            role = MessageRole.ASSISTANT if message.author.id == llm_user_id else MessageRole.USER
            session.add_message(ChatMessage.from_discord_message(message, role, session.name, session.owner_id))

        return session

    def get_active_user_session(self, user_id: int) -> ChatSession | None:
        return SqliteChatSession.get_active_session(user_id, self.config.bot.session_db_path)


def _process_raw_llm_response(raw_response: str, model_config: ModelConfig | None) -> str:
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

    return "*Waiting for response...*"


async def process_llm_response(
    response_stream,
    message: Message,
    bot_config: BotConfig,
    model_config: ModelConfig | None,
    is_chat_response: bool = True,
):
    response = ""
    last_edit_time = time.time()

    for chunk in response_stream:
        if is_chat_response:
            response += chunk["message"]["content"]
        else:
            response += chunk["response"]

        if time.time() - last_edit_time >= bot_config.edit_delay:
            new_content = _process_raw_llm_response(response, model_config)
            await message.edit(content=_process_raw_llm_response(response, model_config))
            last_edit_time = time.time()

    # process last chunk
    if response != "":
        await message.edit(content=_process_raw_llm_response(response, model_config))
