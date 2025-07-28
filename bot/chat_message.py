from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Tuple

import discord


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    date: datetime.datetime
    sender_id: int
    sender_nickname: str
    content: str
    session_name: str
    owner_id: int

    def to_db_tuple(self) -> Tuple:
        """Convert to tuple for database insertion."""
        return (
            self.date.isoformat(),
            self.sender_id,
            self.sender_nickname,
            self.content,
            self.session_name,
            self.owner_id,
        )

    @staticmethod
    def from_db_tuple(data: Tuple) -> ChatMessage:
        """Create ChatMessage from database tuple."""
        return ChatMessage(
            date=datetime.datetime.fromisoformat(data[0]),
            sender_id=data[1],
            sender_nickname=data[2],
            content=data[3],
            session_name=data[4],
            owner_id=data[5],
        )

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
            date=message.created_at,
            sender_id=message.author.id,
            sender_nickname=message.author.display_name,
            content=message.content,
            session_name=session_name,
            owner_id=owner_id,
        )

    def __str__(self) -> str:
        return f"@{self.sender_nickname} (UID: {self.sender_id}) sent on {self.date.strftime('%Y-%m-%d %H:%M:%S')}:\n{self.content}"
