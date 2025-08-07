from bot.chat_model import ChatModel, get_all_models, get_model, split_model_name
from bot.configuration import ModelConfig
from unittest.mock import MagicMock, patch


def test_split_model_name():
    # Test normal case with tag
    assert split_model_name("llama3:8b") == ("llama3", "8b")

    # Test case without tag
    assert split_model_name("llama3") == ("llama3", None)

    # Test edge cases
    assert split_model_name("") == (None, None)
    assert split_model_name("a:b:c") == (None, None)


def get_mocked_model_config(
    context_limit: int | None = None,
    thinking_prefix: str = "<think>",
    thinking_suffix: str = "</think>",
    chat_template: str = "Dummy template",
):
    mock_tokenizer = MagicMock()
    mock_tokenizer.chat_template = chat_template

    return ModelConfig(
        thinking_prefix=thinking_prefix,
        thinking_suffix=thinking_suffix,
        tokenizer=mock_tokenizer,
        context_limit=context_limit,
    )


def get_mocked_ollama_model(name: str | None, size: str | None, parameters: str | None, quant: str | None) -> MagicMock:
    mock_ollama_model = MagicMock()
    mock_ollama_model.model = name
    mock_ollama_model.size = MagicMock()
    mock_ollama_model.size.human_readable.return_value = size
    mock_ollama_model.details = MagicMock()
    mock_ollama_model.details.parameter_size = parameters
    mock_ollama_model.details.quantization_level = quant
    return mock_ollama_model


def get_mocked_ollama_model_info(context_length: int | None) -> MagicMock:
    mock_show_response = MagicMock()
    if context_length is not None:
        mock_show_response.modelinfo = {"model.context_length": context_length}
    return mock_show_response


def test_from_ollama_model():
    """Test creating valid model from mocked ollama responses"""
    mocked_mistral_config = get_mocked_model_config(context_limit=4096)
    mocked_mistral = get_mocked_ollama_model("mistral:latest", "5.2 GB", "7B", "Q4")
    mocked_llama_config = get_mocked_model_config(context_limit=20480)
    mocked_llama = get_mocked_ollama_model("llama3", "4GB", "8B", "Q3")

    with patch("bot.chat_model.ollama") as mock_ollama:
        mock_ollama.list.return_value.models = [mocked_mistral, mocked_llama]
        mock_ollama.show.return_value = get_mocked_ollama_model_info(context_length=10240)

        chat_model = ChatModel.from_ollama_model(mocked_mistral, mocked_mistral_config)

        assert chat_model.name == "mistral"
        assert chat_model.tag == "latest"
        assert chat_model.size == "5.2 GB"
        assert chat_model.parameters_size == "7B"
        assert chat_model.quant == "Q4"
        assert chat_model.context_length == 4096
        assert chat_model.config == mocked_mistral_config

        chat_model2 = ChatModel.from_ollama_model(mocked_llama, mocked_llama_config)

        assert chat_model2.name == "llama3"
        assert chat_model2.tag is None
        assert chat_model2.parameters_size == "8B"
        assert chat_model2.quant == "Q3"
        assert chat_model2.context_length == 20480


def test_from_ollama_model_with_none_details():
    """Test creating ChatModel when ollama_model.details is None"""
    mocked_config = get_mocked_model_config(context_limit=4096)
    mocked_model = get_mocked_ollama_model("test_model", "1GB", "1B", "Q4")
    mocked_model.details = None

    with patch("bot.chat_model.ollama") as mock_ollama:
        mock_ollama.show.return_value = get_mocked_ollama_model_info(context_length=2048)

        chat_model = ChatModel.from_ollama_model(mocked_model, mocked_config)

        assert chat_model.name == "test_model"
        assert chat_model.tag is None
        assert chat_model.size == "1GB"
        assert chat_model.parameters_size is None
        assert chat_model.quant is None
        assert chat_model.context_length == 4096
        assert chat_model.config == mocked_config


def test_from_ollama_model_with_none_context_length():
    """Test creating ChatModel when context length is None in model info"""
    mocked_config = get_mocked_model_config(context_limit=4096)
    mocked_model = get_mocked_ollama_model("test_model:latest", "1GB", "1B", "Q4")
    mocked_model.details = MagicMock()
    mocked_model.details.parameter_size = "1B"
    mocked_model.details.quantization_level = "Q4"

    with patch("bot.chat_model.ollama") as mock_ollama:
        mock_ollama.show.return_value = get_mocked_ollama_model_info(context_length=None)

        chat_model = ChatModel.from_ollama_model(mocked_model, mocked_config)

        assert chat_model.name == "test_model"
        assert chat_model.tag == "latest"
        assert chat_model.size == "1GB"
        assert chat_model.parameters_size == "1B"
        assert chat_model.quant == "Q4"
        assert chat_model.context_length == 4096  # Should use config value
        assert chat_model.config == mocked_config


def test_from_ollama_model_with_no_context_override():
    """Test creating ChatModel when context length is None in model info"""
    mocked_config = get_mocked_model_config(context_limit=None)
    mocked_model = get_mocked_ollama_model("test_model:latest", "1GB", "1B", "Q4")
    mocked_model.details = MagicMock()
    mocked_model.details.parameter_size = "1B"
    mocked_model.details.quantization_level = "Q4"

    with patch("bot.chat_model.ollama") as mock_ollama:
        mock_ollama.show.return_value = get_mocked_ollama_model_info(context_length=8192)

        chat_model = ChatModel.from_ollama_model(mocked_model, mocked_config)

        assert chat_model.name == "test_model"
        assert chat_model.tag == "latest"
        assert chat_model.size == "1GB"
        assert chat_model.parameters_size == "1B"
        assert chat_model.quant == "Q4"
        assert chat_model.context_length == 8192  # Should use model value
        assert chat_model.config == mocked_config


def test_get_all_models():
    """Test get_all_models function"""
    mocked_mistral_config = get_mocked_model_config(context_limit=4096)
    mocked_llama_config = get_mocked_model_config(context_limit=20480)
    mocked_mistral = get_mocked_ollama_model("mistral:latest", "5.2 GB", "7B", "Q4")
    mocked_llama = get_mocked_ollama_model("llama3", "4GB", "8B", "Q3")

    # Mock the ollama.list() response
    with patch("bot.chat_model.ollama") as mock_ollama:
        mock_ollama.list.return_value.models = [mocked_mistral, mocked_llama]

        # Mock configs
        mock_configs = MagicMock()
        mock_configs.models = {"mistral:latest": mocked_mistral_config, "llama3": mocked_llama_config}

        models = get_all_models(mock_configs)

        assert len(models) == 2
        assert models[0].name == "mistral"
        assert models[0].tag == "latest"
        assert models[0].context_length == 4096
        assert models[1].name == "llama3"
        assert models[1].context_length == 20480


def test_get_model():
    """Test get_model function"""
    mocked_mistral_config = get_mocked_model_config(context_limit=4096)
    mocked_llama_config = get_mocked_model_config(context_limit=20480)
    mocked_mistral = get_mocked_ollama_model("mistral:latest", "5.2 GB", "7B", "Q4")
    mocked_llama = get_mocked_ollama_model("llama3", "4GB", "8B", "Q3")

    # Mock the ollama.list() response
    with patch("bot.chat_model.ollama") as mock_ollama:
        mock_ollama.list.return_value.models = [mocked_mistral, mocked_llama]

        # Mock configs
        mock_configs = MagicMock()
        mock_configs.models = {"mistral:latest": mocked_mistral_config, "llama3": mocked_llama_config}

        # Test finding a model by name
        model = get_model("mistral", mock_configs)
        assert model is not None
        assert model.name == "mistral"
        assert model.context_length == 4096

        # Test finding a model by exact name
        model2 = get_model("llama3", mock_configs)
        assert model2 is not None
        assert model2.name == "llama3"
        assert model2.context_length == 20480


def test_get_model_no_match():
    """Test get_model when no matching model is found"""
    mocked_mistral = get_mocked_ollama_model("mistral:latest", "5.2 GB", "7B", "Q4")

    with patch("bot.chat_model.ollama") as mock_ollama:
        mock_ollama.list.return_value.models = [mocked_mistral]

        # Mock configs with no matching model
        mock_configs = MagicMock()
        mock_configs.models = {}

        model = get_model("mistral", mock_configs)
        assert model is None
