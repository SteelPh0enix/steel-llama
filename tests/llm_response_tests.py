from bot.llm_response import LLMResponse


def test_llm_response_initialization():
    """Test LLMResponse initialization with default values"""
    response = LLMResponse()

    assert response.thoughts == ""
    assert response.content == ""
    assert response.thinking_in_progress is False


def test_llm_response_append_content():
    """Test appending content to LLMResponse"""
    response = LLMResponse()

    response.append("Hello world")
    assert response.content == "Hello world"
    assert response.thoughts == ""


def test_llm_response_append_content_with_thinking():
    """Test appending content with thinking tags"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag="</thinking>")

    # Start thinking
    response.append("<thinking>Thinking about the answer</thinking>Content after thinking")

    assert response.thoughts == "Thinking about the answer"
    assert response.content == "Content after thinking"
    assert response.thinking_in_progress is False


def test_llm_response_append_thinking():
    """Test appending only thinking content"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag="</thinking>")

    # Start thinking
    response.append("<thinking>Thinking about the answer</thinking>")

    assert response.thoughts == "Thinking about the answer"
    assert response.content == ""
    assert response.thinking_in_progress is False


def test_llm_response_append_partial_thinking():
    """Test appending partial thinking content"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag="</thinking>")

    # Start thinking
    response.append("<thinking> Thinking about the answer")

    assert response.thoughts == "Thinking about the answer"
    assert response.content == ""
    assert response.thinking_in_progress is True


def test_llm_response_append_thinking_started_then_finished():
    """Test appending content when thinking has started and then finished"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag="</thinking>")

    # Start thinking
    response.append("<thinking>Thinking about ")

    # Finish thinking
    response.append(" answer</thinking>")

    assert response.thoughts == "Thinking about  answer"
    assert response.content == ""
    assert response.thinking_in_progress is False


def test_llm_response_append_thinking_started_then_finished_with_content():
    """Test appending content when thinking has started and then finished"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag="</thinking>")

    # Start thinking
    response.append("<thinking>Thinking about the ")

    # Finish thinking
    response.append(" answer</thinking> Content after thinking")

    assert response.thoughts == "Thinking about the  answer"
    assert response.content == "Content after thinking"
    assert response.thinking_in_progress is False


def test_llm_response_append_with_no_thinking_tags():
    """Test appending content when thinking tags are not set"""
    response = LLMResponse()

    response.append("<thinking>Some content</thinking>")

    # Should treat it as regular content since no thinking tags were provided
    assert response.content == "<thinking>Some content</thinking>"
    assert response.thoughts == ""


def test_llm_response_append_content_with_only_start_tag():
    """Test appending when only start tag is provided"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag=None)

    response.append("<thinking>Content")

    # Should not process anything since end tag is missing
    assert response.content == "<thinking>Content"
    assert response.thoughts == ""


def test_llm_response_append_with_only_end_tag():
    """Test appending when only end tag is provided"""
    response = LLMResponse(thinking_start_tag=None, thinking_end_tag="</thinking>")

    response.append("<thinking>Content</thinking>")

    # Should not process anything since start tag is missing
    assert response.content == "<thinking>Content</thinking>"
    assert response.thoughts == ""


def test_llm_response_thinking_in_progress():
    """Test thinking_in_progress property"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag="</thinking>")

    # Initially should be False
    assert response.thinking_in_progress is False

    # After starting thinking, should be True
    response.append("<thinking>Thinking")
    assert response.thinking_in_progress is True

    # After finishing thinking, should be False
    response.append("</thinking>Content")
    assert response.thinking_in_progress is False


def test_llm_response_multiple_appends():
    """Test multiple append calls"""
    response = LLMResponse(thinking_start_tag="<thinking>", thinking_end_tag="</thinking>")

    response.append("<thinking>This is a thought, ")
    response.append("more thoughts ")
    response.append("and that's all </thinking>And this is content")
    response.append(" and then some")

    assert response.thoughts == "This is a thought, more thoughts and that's all"
    assert response.content == "And this is content and then some"
