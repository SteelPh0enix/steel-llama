from __future__ import annotations

import datetime
from dataclasses import dataclass

import discord

from enum import StrEnum

from bot.configuration import ModelConfig


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


def transform_mentions_into_usernames(message: str, mentions: list[discord.User | discord.Member]) -> str:
    for mention in mentions:
        message = message.replace(f"<@{mention.id}>", f"<@{mention.name} (UID: {mention.id})>")
    return message


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    id: int
    owner_id: int
    sender_id: int
    sender_nickname: str
    session_name: str
    timestamp: datetime.datetime
    role: MessageRole
    content: str

    @staticmethod
    def from_discord_message(
        message: discord.Message, role: MessageRole, session_name: str, owner_id: int
    ) -> ChatMessage:
        """Create ChatMessage from discord.Message.

        Args:
            message: The discord message to convert
            session_name: The name of the chat session

        Returns:
            ChatMessage: A new ChatMessage instance
        """
        return ChatMessage(
            id=message.id,
            owner_id=owner_id,
            sender_id=message.author.id,
            sender_nickname=message.author.display_name,
            session_name=session_name,
            timestamp=message.created_at,
            role=role,
            content=transform_mentions_into_usernames(message.content, message.mentions),
        )

    def token_length(self, model_config: ModelConfig) -> int:
        return len(model_config.tokenizer.encode(str(self)))  # type: ignore

    def __str__(self) -> str:
        return f"@{self.sender_nickname}:\n{self.content}"
