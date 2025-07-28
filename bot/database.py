from __future__ import annotations

import datetime
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import discord

DefaultModelName = "<DEFAULT_MODEL>"
DefaultBotDatabasePath = Path("./bot.db")


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    date: datetime.datetime
    sender_id: int
    sender_nickname: str
    content: str
    session_name: str
    user_id: int

    def to_db_tuple(self) -> Tuple:
        """Convert to tuple for database insertion."""
        return (
            self.date.isoformat(),
            self.sender_id,
            self.sender_nickname,
            self.content,
            self.session_name,
            self.user_id,
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
            user_id=data[5],
        )

    @staticmethod
    def from_discord_message(message: discord.Message, session_name: str) -> ChatMessage:
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
            user_id=message.author.id,
        )


@dataclass
class SessionInfo:
    """Represents session information."""

    model: str
    system_prompt: str


class ChatSession:
    """Represents a persistent chat session stored in SQLite database."""

    def __init__(self, name: str, user_id: int, db_path: Path = DefaultBotDatabasePath):
        self.name = name
        self.user_id = user_id
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create necessary tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create sessions table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS sessions (
                    name TEXT,
                    user_id INTEGER,
                    model TEXT DEFAULT '{DefaultModelName}',
                    system_prompt TEXT DEFAULT '',
                    PRIMARY KEY (name, user_id)
                )
            """)

            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    sender_id INTEGER,
                    sender_nickname TEXT,
                    content TEXT,
                    session_name TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (session_name, user_id) REFERENCES sessions (name, user_id)
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_name, user_id, date)
            """)

            conn.commit()

    def save_session(self, model: str = DefaultModelName, system_prompt: str = ""):
        """Save or update the session in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO sessions (name, user_id, model, system_prompt)
                VALUES (?, ?, ?, ?)
            """,
                (self.name, self.user_id, model, system_prompt),
            )
            conn.commit()

    def get_session_info(self) -> Optional[SessionInfo]:
        """Get model and system prompt for this session.

        Returns:
            SessionInfo object or None if session doesn't exist
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT model, system_prompt FROM sessions 
                WHERE name = ? AND user_id = ?
            """,
                (self.name, self.user_id),
            )
            result = cursor.fetchone()
            return SessionInfo(model=result[0], system_prompt=result[1]) if result else None

    def add_message(self, message: ChatMessage):
        """Add a message to this session."""

        with sqlite3.connect(self.db_path) as conn:
            if not self._session_exists_conn(self.name, self.user_id, conn):
                raise ValueError(
                    f"Session '{self.name}' does not exist for user {self.user_id}. Please save the session first."
                )

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages 
                (date, sender_id, sender_nickname, content, session_name, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                message.to_db_tuple(),
            )
            conn.commit()

    def get_messages(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """Retrieve messages for this session, optionally limited.

        Args:
            limit: Maximum number of messages to retrieve, ordered by date descending

        Returns:
            List of ChatMessage objects, ordered by date ascending
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute(
                    """
                    SELECT date, sender_id, sender_nickname, content, session_name, user_id
                    FROM messages 
                    WHERE session_name = ? AND user_id = ?
                    ORDER BY date DESC 
                    LIMIT ?
                """,
                    (self.name, self.user_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT date, sender_id, sender_nickname, content, session_name, user_id
                    FROM messages 
                    WHERE session_name = ? AND user_id = ?
                    ORDER BY date ASC
                """,
                    (self.name, self.user_id),
                )

            rows = cursor.fetchall()
            # If we used limit, we need to reverse the order to get chronological order
            if limit:
                rows = reversed(rows)  # type: ignore

            return [ChatMessage.from_db_tuple(row) for row in rows]

    def delete_session(self):
        """Delete this session and all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Delete messages first due to foreign key constraint
            cursor.execute(
                """
                DELETE FROM messages 
                WHERE session_name = ? AND user_id = ?
            """,
                (self.name, self.user_id),
            )

            # Delete the session
            cursor.execute(
                """
                DELETE FROM sessions 
                WHERE name = ? AND user_id = ?
            """,
                (self.name, self.user_id),
            )

            conn.commit()

    @staticmethod
    def list_sessions(user_id: int, db_path: Path = DefaultBotDatabasePath) -> List[str]:
        """List all session names for a user."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name FROM sessions WHERE user_id = ?
            """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    @staticmethod
    def session_exists(name: str, user_id: int, db_path: Path = DefaultBotDatabasePath) -> bool:
        """Check if a session exists for a user."""
        with sqlite3.connect(db_path) as conn:
            return ChatSession._session_exists_conn(name, user_id, conn)

    @staticmethod
    def _session_exists_conn(name: str, user_id: int, conn: sqlite3.Connection) -> bool:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM sessions WHERE name = ? AND user_id = ?
        """,
            (name, user_id),
        )
        return cursor.fetchone() is not None
