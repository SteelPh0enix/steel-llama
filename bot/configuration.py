from __future__ import annotations

import configparser
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    thinking_prefix: str | None
    """Prefix to use when the model is thinking (optional)."""

    thinking_suffix: str | None
    """Suffix to use when the model is thinking (optional)."""

    @staticmethod
    def from_config_section(parser: configparser.ConfigParser, section: str) -> ModelConfig:
        """
        Create a ModelConfig instance from a config section.

        Parameters
        ----------
        parser : configparser.ConfigParser
            The configuration parser containing the section.
        section : str
            The name of the config section to read from.

        Returns
        -------
        ModelConfig
            A new ModelConfig instance based on the config section.

        Raises
        ------
        ValueError
            If thinking_prefix is specified without thinking_suffix or vice versa.
        """
        thinking_prefix = parser.get(section, "thinking_prefix", fallback=None)
        thinking_suffix = parser.get(section, "thinking_suffix", fallback=None)

        # user must specify both or neither
        if thinking_prefix is not None and thinking_suffix is None:
            raise ValueError(f"Missing thinking suffix in section {section}")

        if thinking_suffix is not None and thinking_prefix is None:
            raise ValueError(f"Missing thinking prefix in section {section}")

        return ModelConfig(thinking_prefix=thinking_prefix, thinking_suffix=thinking_suffix)


@dataclass
class ModelsConfig:
    """Configuration for all models used by the bot."""

    excluded_models: List[str]
    """List of model names to exclude from being used."""

    default_model: str
    """The model name to use as a default when none is specified."""

    models_config: dict[str, ModelConfig]
    """Dictionary mapping model patterns to their specific configurations."""

    def find_config_for_model(self, model_name: str) -> ModelConfig | None:
        """
        Find the configuration for a given model.

        Parameters
        ----------
        model_name : str
            The name of the model to look up.

        Returns
        -------
        ModelConfig | None
            The matching model configuration if found, otherwise None.
        """
        for key, value in self.models_config.items():
            pattern = re.escape(key).replace(r"\*", ".*")
            if re.fullmatch(pattern, model_name):
                return value
        return None

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> ModelsConfig:
        """
        Create a ModelsConfig instance from the configuration parser.

        Parameters
        ----------
        parser : configparser.ConfigParser
            The configuration parser to read from.

        Returns
        -------
        ModelsConfig
            A new ModelsConfig instance based on the config file.

        Raises
        ------
        ValueError
            If the default model is in the list of excluded models.
        """
        excluded_models_str = parser.get("models", "excluded_models")
        excluded_models = [model.strip() for model in excluded_models_str.split(",")]
        default_model = parser.get("models", "default_model")

        if default_model in excluded_models:
            raise ValueError("Default model cannot be one of the excluded models.")

        models_config: dict[str, ModelConfig] = {}
        for section in parser.sections():
            if section.startswith("models."):
                model_wildcard_name = section[7:]
                models_config[model_wildcard_name] = ModelConfig.from_config_section(parser, section)

        return ModelsConfig(
            excluded_models=excluded_models,
            default_model=default_model,
            models_config=models_config,
        )


@dataclass
class AdminConfig:
    """Configuration for the admin user."""

    id: int
    """The Discord ID of the admin user."""

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> AdminConfig:
        """
        Create an AdminConfig instance from the configuration parser.

        Parameters
        ----------
        parser : configparser.ConfigParser
            The configuration parser to read from.

        Returns
        -------
        AdminConfig
            A new AdminConfig instance based on the config file.
        """
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

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> BotConfig:
        """
        Create a BotConfig instance from the configuration parser.

        Parameters
        ----------
        parser : configparser.ConfigParser
            The configuration parser to read from.

        Returns
        -------
        BotConfig
            A new BotConfig instance based on the config file.
        """
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

        return BotConfig(
            discord_api_key=bot_api_key,
            bot_prefix=bot_prefix,
            edit_delay=bot_delay,
            max_messages_for_context=max_messages_for_context,
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
        """
        Load configuration from a file.

        Parameters
        ----------
        config_path : Path
            The path to the configuration file.

        Returns
        -------
        Config
            A new Config instance based on the config file.

        Raises
        ------
        ValueError
            If the config file cannot be read or is not found.
        """
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
        """
        Write a default configuration file to the specified path.

        Parameters
        ----------
        file_path : Path
            The path where the default config file should be written.
        """
        config = configparser.ConfigParser()

        config["models"] = {
            "excluded_models": "model1, model2",
            "default_model": "default_model_name",
        }

        config["admin"] = {"id": "12345"}

        config["bot"] = {
            "discord_api_key": "your_discord_api_key_here",
            "bot_prefix": "$",
            "edit_delay_seconds": "0.5",
            "max_messages_for_context": "30",
        }

        config["models.qwen3-*"] = {
            "thinking_prefix": "<think>",
            "thinking_suffix": "</think>",
        }

        with open(file_path, "w") as f:
            config.write(f)
