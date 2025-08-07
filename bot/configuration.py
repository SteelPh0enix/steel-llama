from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

from transformers import AutoTokenizer


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    thinking_prefix: str | None
    """Prefix to use when the model is thinking (optional)."""

    thinking_suffix: str | None
    """Suffix to use when the model is thinking (optional)."""

    tokenizer: AutoTokenizer
    """Tokenizer used for this model."""

    context_limit: int | None
    """Maximum amount of tokens for a prompt (only input tokens)"""

    def tokenizer_has_chat_template(self) -> bool:
        return hasattr(self.tokenizer, "chat_template")

    @staticmethod
    def from_config_section(parser: configparser.ConfigParser, section: str) -> ModelConfig:
        thinking_prefix = parser.get(section, "thinking_prefix", fallback=None)
        thinking_suffix = parser.get(section, "thinking_suffix", fallback=None)
        tokenizer_name_or_path = parser.get(section, "tokenizer")
        context_limit = parser.getint(section, "context_limit", fallback=None)

        # user must specify both or neither
        if thinking_prefix is not None and thinking_suffix is None:
            raise ValueError(f"Missing thinking suffix in section {section}")

        if thinking_suffix is not None and thinking_prefix is None:
            raise ValueError(f"Missing thinking prefix in section {section}")

        # make sure that the tokenizer is valid
        print(f"Creating tokenizer '{tokenizer_name_or_path}'...")
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name_or_path)
        print(f"Tokenizer '{tokenizer_name_or_path}' created successfully!")

        return ModelConfig(
            thinking_prefix=thinking_prefix,
            thinking_suffix=thinking_suffix,
            tokenizer=tokenizer,
            context_limit=context_limit,
        )


@dataclass
class ModelsConfig:
    """Configuration for all models used by the bot."""

    default_model: str
    """The model name to use as a default when none is specified."""

    default_model_tag: str | None
    """Default tag for the model. If specified, users may provide only the name of
    the model (for example, qwen3-8b), if not - users must provide full model name
    (for example, qwen3-8b:latest)"""

    models: dict[str, ModelConfig]
    """Dictionary mapping model patterns to their specific configurations."""

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> ModelsConfig:
        default_model = parser.get("models", "default_model")
        default_model_tag = parser.get("models", "default_model_tag", fallback=None)

        models_config: dict[str, ModelConfig] = {}
        for section in parser.sections():
            if section.startswith("models."):
                model_name = section[7:]
                models_config[model_name] = ModelConfig.from_config_section(parser, section)

        if default_model not in models_config:
            raise ValueError(f"Default model '{default_model}' doesn't have a config section in configuration file!")

        return ModelsConfig(
            default_model=default_model,
            models=models_config,
            default_model_tag=default_model_tag,
        )


@dataclass
class AdminConfig:
    """Configuration for the admin user."""

    id: int
    """The Discord ID of the admin user."""

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> AdminConfig:
        admin_id = parser.getint("admin", "id")
        return AdminConfig(id=admin_id)


@dataclass
class BotConfig:
    """Main configuration for the bot."""

    discord_api_key: str
    """The Discord API key (token) for the bot."""

    bot_prefix: str
    """The command prefix used by the bot (e.g., '$')."""

    edit_delay: float
    """Delay in seconds between editing messages when responding to prompts."""

    max_messages_for_context: int
    """Maximum amount of messages fetched from the history for LLM context.
    The actual amount of used messages may be smaller if context is not large enough."""

    session_db_path: Path
    """Path of the SQLite database file used for storing chat sessions."""

    default_system_prompt: str
    """Default system prompt for the bot, always used for temporary (global) sessions."""

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> BotConfig:
        bot_api_key = parser.get("bot", "discord_api_key")

        bot_prefix = parser.get("bot", "bot_prefix")
        if bot_prefix == "":
            raise ValueError("Invalid bot prefix, must not be empty!")

        bot_delay = parser.getfloat("bot", "edit_delay_seconds")
        if bot_delay <= 0:
            raise ValueError("Invalid bot edit delay, must be longer than 0 seconds")

        max_messages_for_context = parser.getint("bot", "max_messages_for_context")
        if max_messages_for_context < 0:
            raise ValueError("Invalid context message limit, must be 0 or more")

        session_db_path = parser.get("bot", "session_db_path")
        if not session_db_path:
            raise ValueError("Session database path cannot be empty")

        default_system_prompt = parser.get("bot", "default_system_prompt")

        return BotConfig(
            discord_api_key=bot_api_key,
            bot_prefix=bot_prefix,
            edit_delay=bot_delay,
            max_messages_for_context=max_messages_for_context,
            session_db_path=Path(session_db_path),
            default_system_prompt=default_system_prompt,
        )


@dataclass
class Config:
    """Main configuration container for the entire application."""

    models: ModelsConfig
    """Configuration related to models and their settings."""

    admin: AdminConfig
    """Configuration related to the admin user."""

    bot: BotConfig
    """Main configuration for the bot itself."""

    @staticmethod
    def from_file(config_path: Path) -> Config:
        config_parser = configparser.ConfigParser()
        files_read = config_parser.read(config_path)

        if not files_read:
            raise ValueError(f"Config file not found or could not be read: {config_path}")

        models_config = ModelsConfig.from_config(config_parser)
        admin_config = AdminConfig.from_config(config_parser)
        bot_config = BotConfig.from_config(config_parser)

        return Config(
            models=models_config,
            admin=admin_config,
            bot=bot_config,
        )

    @staticmethod
    def write_default_config(file_path: Path):
        config = configparser.ConfigParser()

        config["models"] = {
            "default_model": "qwen3-8b",
            "default_model_tag": "latest",
        }

        config["admin"] = {"id": "12345"}

        config["bot"] = {
            "discord_api_key": "your_discord_api_key_here",
            "bot_prefix": "$",
            "edit_delay_seconds": "0.5",
            "max_messages_for_context": "30",
            "session_db_path": "./bot.db",
            "default_system_prompt": 'You are a Discord bot, proceed with the following conversation with the users. Every message is prefixed with a line containing the username (and user ID) of it\'s sender (prefixed with @) and the timestamp of the message. Messages directed specifically to you are prefixed with "$llm".',
        }

        config["models.qwen3-8b"] = {
            "thinking_prefix": "<think>",
            "thinking_suffix": "</think>",
            "tokenizer": "Qwen/Qwen3-8B",
        }

        with open(file_path, "w") as f:
            config.write(f)
