import configparser
import os
import tempfile
from pathlib import Path

import pytest

from bot.configuration import AdminConfig, BotConfig, Config, ModelConfig, ModelsConfig

TEST_TOKENIZER = "Qwen/Qwen3-8B"


def test_model_config_from_config_section():
    """Test ModelConfig creation from a config section"""
    parser = configparser.ConfigParser()
    parser["models.test"] = {
        "thinking_prefix": "<thinking>",
        "thinking_suffix": "</thinking>",
        "tokenizer": TEST_TOKENIZER,
        "context_limit": "1024",
    }

    config = ModelConfig.from_config_section(parser, "models.test")

    assert config.thinking_prefix == "<thinking>"
    assert config.thinking_suffix == "</thinking>"
    assert config.tokenizer is not None
    assert config.context_limit == 1024


def test_model_config_missing_thinking_prefix():
    """Test ModelConfig raises error when thinking prefix is missing while thinking suffix is defined"""
    parser = configparser.ConfigParser()
    parser["models.test"] = {"thinking_suffix": "</thinking>", "tokenizer": TEST_TOKENIZER}

    with pytest.raises(ValueError, match="Missing thinking prefix"):
        ModelConfig.from_config_section(parser, "models.test")


def test_model_config_missing_thinking_suffix():
    """Test ModelConfig raises error when thinking suffix is missing while thinking prefix is defined"""
    parser = configparser.ConfigParser()
    parser["models.test"] = {"thinking_prefix": "<thinking>", "tokenizer": TEST_TOKENIZER}

    with pytest.raises(ValueError, match="Missing thinking suffix"):
        ModelConfig.from_config_section(parser, "models.test")


def test_models_config_from_config():
    """Test ModelsConfig creation from parser"""
    parser = configparser.ConfigParser()
    parser["models"] = {"default_model": "test-model"}
    parser["models.test-model"] = {
        "thinking_prefix": "<thinking>",
        "thinking_suffix": "</thinking>",
        "tokenizer": TEST_TOKENIZER,
    }

    config = ModelsConfig.from_config(parser)

    assert config.default_model == "test-model"
    assert "test-model" in config.models


def test_models_config_get_model_config():
    """Test getting model config by it's name"""
    parser = configparser.ConfigParser()
    parser["models"] = {"default_model": "test-model"}
    parser["models.test-model"] = {
        "thinking_prefix": "<thinking>",
        "thinking_suffix": "</thinking>",
        "tokenizer": TEST_TOKENIZER,
    }

    config = ModelsConfig.from_config(parser)

    # Should find the model
    model_config = config.models.get("test-model", None)
    assert model_config is not None

    # Should return None for non-matching model
    model_config = config.models.get("other-model", None)
    assert model_config is None


def test_admin_config_from_config():
    """Test AdminConfig creation from parser"""
    parser = configparser.ConfigParser()
    parser["admin"] = {"id": "123456789"}

    config = AdminConfig.from_config(parser)

    assert config.id == 123456789


def test_bot_config_from_config():
    """Test BotConfig creation from parser"""
    parser = configparser.ConfigParser()
    parser["bot"] = {
        "discord_api_key": "test_api_key",
        "bot_prefix": "$",
        "edit_delay_seconds": "0.5",
        "max_messages_for_context": "30",
        "session_db_path": "./test.db",
        "default_system_prompt": "Test prompt",
    }

    config = BotConfig.from_config(parser)

    assert config.discord_api_key == "test_api_key"
    assert config.bot_prefix == "$"
    assert config.edit_delay == 0.5
    assert config.max_messages_for_context == 30
    assert config.session_db_path == Path("./test.db")
    assert config.default_system_prompt == "Test prompt"


def test_bot_config_invalid_prefix():
    """Test BotConfig raises error for empty prefix"""
    parser = configparser.ConfigParser()
    parser["bot"] = {
        "discord_api_key": "test_api_key",
        "bot_prefix": "",
        "edit_delay_seconds": "0.5",
        "max_messages_for_context": "30",
        "session_db_path": "./test.db",
        "default_system_prompt": "Test prompt",
    }

    with pytest.raises(ValueError, match="Invalid bot prefix"):
        BotConfig.from_config(parser)


def test_bot_config_invalid_delay():
    """Test BotConfig raises error for invalid delay"""
    parser = configparser.ConfigParser()
    parser["bot"] = {
        "discord_api_key": "test_api_key",
        "bot_prefix": "$",
        "edit_delay_seconds": "0",
        "max_messages_for_context": "30",
        "session_db_path": "./test.db",
        "default_system_prompt": "Test prompt",
    }

    with pytest.raises(ValueError, match="Invalid bot edit delay"):
        BotConfig.from_config(parser)

    parser["bot"]["edit_delay_seconds"] = "-1"

    with pytest.raises(ValueError, match="Invalid bot edit delay"):
        BotConfig.from_config(parser)


def test_bot_config_invalid_context_limit():
    """Test BotConfig raises error for invalid context limit"""
    parser = configparser.ConfigParser()
    parser["bot"] = {
        "discord_api_key": "test_api_key",
        "bot_prefix": "$",
        "edit_delay_seconds": "0.5",
        "max_messages_for_context": "-1",
        "session_db_path": "./test.db",
        "default_system_prompt": "Test prompt",
    }

    with pytest.raises(ValueError, match="Invalid context message limit"):
        BotConfig.from_config(parser)


def test_bot_config_invalid_session_db_path():
    """Test BotConfig raises error for invalid session database path"""
    parser = configparser.ConfigParser()
    parser["bot"] = {
        "discord_api_key": "test_api_key",
        "bot_prefix": "$",
        "edit_delay_seconds": "0.5",
        "max_messages_for_context": "30",
        "session_db_path": "",
        "default_system_prompt": "Test prompt",
    }

    with pytest.raises(ValueError, match="Session database path cannot be empty"):
        BotConfig.from_config(parser)


def test_config_from_file():
    """Test Config creation from file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        config_content = f"""
[models]
default_model = test-model

[admin]
id = 12345

[bot]
discord_api_key = test_api_key
bot_prefix = $
edit_delay_seconds = 0.5
max_messages_for_context = 30
session_db_path = ./test.db
default_system_prompt = Test prompt

[models.test-model]
thinking_prefix = <thinking>
thinking_suffix = </thinking>
tokenizer = {TEST_TOKENIZER}
"""
        f.write(config_content)
        config_file = f.name

    try:
        config = Config.from_file(Path(config_file))

        assert config.models.default_model == "test-model"
        assert config.admin.id == 12345
        assert config.bot.discord_api_key == "test_api_key"
        assert config.bot.bot_prefix == "$"
        assert config.bot.edit_delay == 0.5
        assert config.bot.max_messages_for_context == 30
        assert config.bot.session_db_path == Path("./test.db")
        assert config.bot.default_system_prompt == "Test prompt"

        # Test that the model config was parsed correctly
        model_config = config.models.models.get("test-model", None)
        assert model_config is not None
    finally:
        os.unlink(config_file)


def test_config_write_default_config():
    """Test writing default configuration file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        config_file = f.name

    try:
        Config.write_default_config(Path(config_file))

        # Read the file back
        parser = configparser.ConfigParser()
        files_read = parser.read(config_file)
        assert len(files_read) == 1

        # Check that all sections exist
        assert "models" in parser
        assert "admin" in parser
        assert "bot" in parser
        assert "models.qwen3-8b" in parser

        # Check values
        assert parser["models"]["default_model"] == "qwen3-8b"
        assert parser["admin"]["id"] == "12345"
        assert parser["bot"]["discord_api_key"] == "your_discord_api_key_here"
        assert parser["bot"]["bot_prefix"] == "$"
        assert parser["bot"]["edit_delay_seconds"] == "0.5"
        assert parser["bot"]["max_messages_for_context"] == "30"
        assert parser["bot"]["session_db_path"] == "./bot.db"

    finally:
        os.unlink(config_file)


def test_models_config_default_model_not_found():
    """Test ModelsConfig raises error when default model has no config"""
    parser = configparser.ConfigParser()
    parser["models"] = {"default_model": "nonexistent-model"}
    parser["models.test-model"] = {
        "thinking_prefix": "<thinking>",
        "thinking_suffix": "</thinking>",
        "tokenizer": TEST_TOKENIZER,
    }

    with pytest.raises(ValueError, match="doesn't have a config section"):
        ModelsConfig.from_config(parser)
