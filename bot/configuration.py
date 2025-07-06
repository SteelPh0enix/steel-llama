from dataclasses import dataclass
from typing import List
import configparser


@dataclass
class ModelsConfig:
    excluded_models: List[str]


@dataclass
class AdminConfig:
    id: int


@dataclass
class BotConfig:
    discord_api_key: str
    bot_prefix: str


@dataclass
class Config:
    models: ModelsConfig
    admin: AdminConfig
    bot: BotConfig


def load_config(config_path: str) -> Config:
    """Load configuration from an INI file into strongly typed dataclasses."""
    config_parser = configparser.ConfigParser()

    # Attempt to read the config file
    files_read = config_parser.read(config_path)

    if not files_read:
        raise RuntimeError(f"Config file not found or could not be read: {config_path}")

    # Parse [models] section
    excluded_models_str = config_parser.get("models", "excluded_models")
    excluded_models = [model.strip() for model in excluded_models_str.split(",")]

    models_config = ModelsConfig(excluded_models=excluded_models)

    # Parse [admin] section
    admin_id = int(config_parser.get("admin", "id"))
    admin_config = AdminConfig(id=admin_id)

    # Parse [bot] section
    bot_api_key = config_parser.get("bot", "discord_api_key")
    bot_prefix = config_parser.get("bot", "bot_prefix")
    bot_config = BotConfig(discord_api_key=bot_api_key, bot_prefix=bot_prefix)

    return Config(models=models_config, admin=admin_config, bot=bot_config)


def create_example_config(file_path: str):
    """Create an example configuration file for the bot."""
    config = configparser.ConfigParser()

    # Set default config values
    config["models"] = {"excluded_models": "model1, model2"}
    config["admin"] = {"id": "12345"}
    config["bot"] = {
        "discord_api_key": "your_discord_api_key_here",
        "bot_prefix": "$",
    }

    with open(file_path, "w") as f:
        config.write(f)
