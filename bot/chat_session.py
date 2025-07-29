from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from bot.chat_message import ChatMessage


class ChatSession:
    def __init__(self, owner_id: int, name: str, model: str = "", system_prompt: str = "") -> None:
        self._owner_id = owner_id
        self._name = name
        self._model = model
        self._system_prompt = system_prompt
        self._messages: list[ChatMessage] = []

    @property
    def owner_id(self) -> int:
        return self._owner_id

    @owner_id.setter
    def owner_id(self, new_owner_id: int) -> None:
        self._owner_id = new_owner_id
        self._save_session_info()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name
        self._save_session_info()

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, new_model: str) -> None:
        self._model = new_model
        self._save_session_info()

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, new_system_prompt: str) -> None:
        self._system_prompt = new_system_prompt
        self._save_session_info()

    def add_message(self, message: ChatMessage) -> None:
        self._messages.append(message)
        self._messages.sort(key=lambda msg: msg.timestamp)
        self._save_session_messages()

    def messages(self, limit: int | None = None) -> list[ChatMessage]:
        return self._messages[:limit] if limit is not None else self._messages

    def save(self) -> None:
        self._save_session_info()
        self._save_session_messages()

    def _save_session_info(self) -> None:
        # Implement if needed
        pass

    def _save_session_messages(self) -> None:
        # Implement if needed
        pass


class SqliteChatSession(ChatSession):
    """Represents a persistent chat session stored in SQLite database."""

    def __init__(
        self,
        owner_id: int,
        name: str,
        db_path: Path,
    ):
        super().__init__(owner_id, name)
        self._db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create necessary tables if they don't exist."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    owner_id INTEGER,
                    name TEXT,
                    model TEXT,
                    system_prompt TEXT DEFAULT '',
                    PRIMARY KEY (owner_id, name)
                )
                """)

            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    owner_id INTEGER,
                    sender_id INTEGER,
                    sender_nickname TEXT,
                    session_name TEXT,
                    timestamp TEXT,
                    content TEXT,
                    FOREIGN KEY (owner_id, session_name) REFERENCES sessions (owner_id, name)
                )
                """)

            # Create active sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_sessions (
                    owner_id INTEGER,
                    session_name TEXT,
                    UNIQUE (owner_id, session_name)
                    FOREIGN KEY (owner_id, session_name) REFERENCES sessions (owner_id, name)
                )
                """)

            conn.commit()

    def _save_session_info(self) -> None:
        """Save or update the session in the database."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO sessions (owner_id, name, model, system_prompt)
                VALUES (?, ?, ?, ?)
                """,
                (self.owner_id, self.name, self.model, self.system_prompt),
            )
            conn.commit()

    def _save_session_messages(self) -> None:
        """Save the list of messages to the database. Removes the messages not on the list."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id 
                from MESSAGES
                WHERE owner_id = ? AND session_name = ?
                """,
                (self.owner_id, self.name),
            )
            saved_messages_ids = cursor.fetchall()
            current_messages_ids = [msg.id for msg in self._messages]

            # remove messages that aren't on the list from the database
            for id in saved_messages_ids:
                if id not in current_messages_ids:
                    cursor.execute("DELETE FROM messages WHERE id = ?", (id,))

            # add missing messages from the list to the database
            for msg in self._messages:
                if msg.id not in saved_messages_ids:
                    cursor.execute(
                        """
                        INSERT INTO messages
                        (id, owner_id, sender_id, sender_nickname, session_name, timestamp, content)
                        VALUES (?, ?, ?, ?, ?, ?, ?)                   
                        """,
                        (
                            msg.id,
                            msg.owner_id,
                            msg.sender_id,
                            msg.sender_nickname,
                            msg.session_name,
                            msg.timestamp.isoformat(),
                            msg.content,
                        ),
                    )

            conn.commit()

    def load(self) -> bool:
        """Loads the session details from database, if they are stored there.
        Overwrites current model/prompt/messages if they exist in the database."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT model, system_prompt
                FROM sessions
                WHERE owner_id = ? AND name = ?
                """,
                (self.owner_id, self.name),
            )

            if (session_details := cursor.fetchone()) is not None:
                model, system_prompt = session_details
                self._model = model
                self._system_prompt = system_prompt
            else:
                return False

            cursor.execute(
                """
                SELECT id, owner_id, sender_id, sender_nickname, session_name, timestamp, content
                FROM messages
                WHERE owner_id = ? AND session_name = ?
                ORDER BY timestamp ASC
                """,
                (self.owner_id, self.name),
            )

            messages = cursor.fetchall()
            if len(messages) > 0:
                self._messages = [
                    ChatMessage(
                        id=id,
                        owner_id=owner_id,
                        sender_id=sender_id,
                        sender_nickname=sender_nickname,
                        session_name=session_name,
                        timestamp=datetime.fromisoformat(timestamp),
                        content=content,
                    )
                    for (id, owner_id, sender_id, sender_nickname, session_name, timestamp, content) in messages
                ]

        return True

    def delete(self) -> None:
        """Deletes the session and all it's messages from database"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM messages WHERE owner_id = ? AND session_name = ?", (self.owner_id, self.name))
            cursor.execute("DELETE FROM sessions WHERE owner_id = ? AND name = ?", (self.owner_id, self.name))
            cursor.execute(
                "DELETE FROM active_sessions WHERE owner_id = ? AND session_name = ?", (self.owner_id, self.name)
            )

            conn.commit()

    def mark_as_active(self) -> None:
        """Marks current session as active"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM active_sessions WHERE owner_id = ?", (self.owner_id,))
            conn.commit()

            cursor.execute(
                "INSERT INTO active_sessions(owner_id, session_name) VALUES (?, ?)", (self.owner_id, self.name)
            )
            conn.commit()

    @staticmethod
    def list_user_sessions(user_id: int, db_path: Path) -> list[str]:
        """Returns a list of session names for specified user."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sessions WHERE owner_id = ?", (user_id,))
            sessions = cursor.fetchall()
            return [session[0] for session in sessions]

        return []

    @staticmethod
    def disable_active_session(user_id: int, db_path: Path):
        """Removes all active session markings for specified user"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_sessions WHERE owner_id = ?", (user_id,))
            conn.commit()

    @staticmethod
    def get_active_session(user_id: int, db_path: Path) -> SqliteChatSession | None:
        """Returns currently active chat session, or None if there isn't any"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT session_name FROM active_sessions WHERE owner_id = ?", (user_id,))
            if (session_name := cursor.fetchone()) is not None:
                return SqliteChatSession(user_id, session_name[0], db_path)

            return None
