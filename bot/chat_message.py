from __future__ import annotations

import datetime
from dataclasses import dataclass

import discord


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    id: int
    owner_id: int
    sender_id: int
    sender_nickname: str
    session_name: str
    timestamp: datetime.datetime
    content: str

    @staticmethod
    def from_discord_message(message: discord.Message, session_name: str, owner_id: int) -> ChatMessage:
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
            content=message.content,
        )

    def __str__(self) -> str:
        return f"From @{self.sender_nickname} (UID: {self.sender_id}) sent on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}:\n{self.content}"
