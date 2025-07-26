from __future__ import annotations

import configparser
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ModelConfig:
    thinking_prefix: str | None
    thinking_suffix: str | None

    @staticmethod
    def from_config_section(parser: configparser.ConfigParser, section: str) -> ModelConfig:
        thinking_prefix = parser.get(section, "thinking_prefix", fallback=None)
        thinking_suffix = parser.get(section, "thinking_suffix", fallback=None)

        if thinking_prefix is not None and thinking_suffix is None:
            raise ValueError(f"Missing thinking suffix in section {section}")

        if thinking_suffix is not None and thinking_prefix is None:
            raise ValueError(f"Missing thinking prefix in section {section}")

        return ModelConfig(thinking_prefix=thinking_prefix, thinking_suffix=thinking_suffix)


@dataclass
class ModelsConfig:
    excluded_models: List[str]
    default_model: str
    models_config: dict[str, ModelConfig]

    def find_config_for_model(self, model_name: str) -> ModelConfig | None:
        for key, value in self.models_config.items():
            pattern = re.escape(key).replace(r"\*", ".*")
            if re.fullmatch(pattern, model_name):
                return value
        return None

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> ModelsConfig:
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
    id: int

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> AdminConfig:
        admin_id = parser.getint("admin", "id")
        return AdminConfig(id=admin_id)


@dataclass
class BotConfig:
    discord_api_key: str
    bot_prefix: str
    edit_delay: float

    @staticmethod
    def from_config(parser: configparser.ConfigParser) -> BotConfig:
        bot_api_key = parser.get("bot", "discord_api_key")
        bot_prefix = parser.get("bot", "bot_prefix")
        bot_delay = parser.getfloat("bot", "edit_delay_seconds")
        return BotConfig(
            discord_api_key=bot_api_key,
            bot_prefix=bot_prefix,
            edit_delay=bot_delay,
        )


@dataclass
class Config:
    models: ModelsConfig
    admin: AdminConfig
    bot: BotConfig

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
            "excluded_models": "model1, model2",
            "default_model": "default_model_name",
        }

        config["admin"] = {"id": "12345"}

        config["bot"] = {
            "discord_api_key": "your_discord_api_key_here",
            "bot_prefix": "$",
            "edit_delay_seconds": "0.5",
        }

        config["models.qwen3-*"] = {
            "thinking_prefix": "<think>",
            "thinking_suffix": "</think>",
        }

        with open(file_path, "w") as f:
            config.write(f)
