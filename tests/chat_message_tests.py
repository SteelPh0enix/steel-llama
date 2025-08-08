import datetime
from unittest.mock import MagicMock

from bot.chat_message import ChatMessage, MessageRole, transform_mentions_into_usernames


def test_transform_mentions_into_usernames():
    """Test transforming mentions into usernames"""
    # Create mock user objects
    user1 = MagicMock()
    user1.id = 123456789
    user1.name = "TestUser"

    user2 = MagicMock()
    user2.id = 987654321
    user2.name = "AnotherUser"

    # Test with mentions
    message = "Hello <@123456789> and <@987654321>"
    result = transform_mentions_into_usernames(message, [user1, user2])

    assert result == "Hello <@TestUser (UID: 123456789)> and <@AnotherUser (UID: 987654321)>"

    # Test with no mentions
    message = "Hello World"
    result = transform_mentions_into_usernames(message, [])
    assert result == "Hello World"

    # Test with single mention
    message = "Hi <@123456789>"
    result = transform_mentions_into_usernames(message, [user1])
    assert result == "Hi <@TestUser (UID: 123456789)>"


def test_chat_message_from_discord_message():
    """Test creating ChatMessage from discord.Message"""
    # Create mock discord message
    mock_message = MagicMock()
    mock_message.id = 12345
    mock_message.author.id = 98765
    mock_message.author.display_name = "TestUser"
    mock_message.content = "Hello World"
    mock_message.created_at = datetime.datetime(2023, 1, 1, 12, 0, 0)
    mock_message.mentions = []

    # Create ChatMessage
    chat_message = ChatMessage.from_discord_message(mock_message, MessageRole.USER, "test_session", 123456789)

    assert chat_message.id == 12345
    assert chat_message.owner_id == 123456789
    assert chat_message.sender_id == 98765
    assert chat_message.sender_nickname == "TestUser"
    assert chat_message.session_name == "test_session"
    assert chat_message.timestamp == datetime.datetime(2023, 1, 1, 12, 0, 0)
    assert chat_message.role == MessageRole.USER
    assert chat_message.content == "Hello World"


def test_chat_message_from_discord_message_with_mentions():
    """Test creating ChatMessage from discord.Message with mentions"""
    # Create mock discord message with mentions
    mock_message = MagicMock()
    mock_message.id = 12345
    mock_message.author.id = 98765
    mock_message.author.display_name = "TestUser"
    mock_message.content = "Hello <@123456789> and <@987654321>"
    mock_message.created_at = datetime.datetime(2023, 1, 1, 12, 0, 0)

    # Create mock user objects for mentions
    user1 = MagicMock()
    user1.id = 123456789
    user1.name = "MentionedUser"

    user2 = MagicMock()
    user2.id = 987654321
    user2.name = "AnotherUser"

    mock_message.mentions = [user1, user2]

    # Create ChatMessage
    chat_message = ChatMessage.from_discord_message(mock_message, MessageRole.USER, "test_session", 123456789)

    expected_content = "Hello <@MentionedUser (UID: 123456789)> and <@AnotherUser (UID: 987654321)>"
    assert chat_message.content == expected_content


def test_chat_message_str():
    """Test string representation of ChatMessage"""
    chat_message = ChatMessage(
        id=12345,
        owner_id=123456789,
        sender_id=98765,
        sender_nickname="TestUser",
        session_name="test_session",
        timestamp=datetime.datetime(2023, 1, 1, 12, 0, 0),
        role=MessageRole.USER,
        content="Hello World",
    )

    expected_str = "@TestUser:\nHello World"
    assert str(chat_message) == expected_str


def test_chat_message_token_length():
    """Test token length calculation"""
    # Create a mock ModelConfig with a tokenizer
    mock_model_config = MagicMock()
    mock_tokenizer = MagicMock()
    mock_model_config.tokenizer = mock_tokenizer

    # Mock the encode method to return a specific token count
    mock_tokenizer.encode.return_value = ["token1", "token2", "token3"]

    chat_message = ChatMessage(
        id=12345,
        owner_id=123456789,
        sender_id=98765,
        sender_nickname="TestUser",
        session_name="test_session",
        timestamp=datetime.datetime(2023, 1, 1, 12, 0, 0),
        role=MessageRole.USER,
        content="Hello World",
    )

    # Test token length calculation
    token_length = chat_message.token_length(mock_model_config)
    assert token_length == 3  # Should match the mocked encode result

    # Verify that tokenizer.encode was called with string representation of message
    mock_tokenizer.encode.assert_called_once_with(str(chat_message))
