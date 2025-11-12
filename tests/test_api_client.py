from unittest.mock import MagicMock, Mock, patch

import pytest
from claude_lint.api_client import analyze_files, get_usage_stats


@patch("claude_lint.api_client.Anthropic")
def test_analyze_with_caching(mock_anthropic):
    """Test making API call with prompt caching."""
    # Setup mock
    mock_response = Mock()
    mock_response.content = [Mock(text='{"results": []}')]
    mock_anthropic.return_value.messages.create.return_value = mock_response

    # Make request
    response_text, response_obj = analyze_files(
        api_key="test-key", guidelines="# Guidelines", prompt="Check these files"
    )

    # Verify API client was initialized with timeout
    mock_anthropic.assert_called_once_with(api_key="test-key", timeout=60.0)

    # Verify caching was used
    call_args = mock_anthropic.return_value.messages.create.call_args
    assert call_args[1]["model"] == "claude-sonnet-4-5-20250929"
    assert call_args[1]["max_tokens"] == 4096

    # Check system message uses cache_control
    system_messages = call_args[1]["system"]
    assert len(system_messages) == 1
    assert system_messages[0]["type"] == "text"
    assert system_messages[0]["text"] == "# Guidelines"
    assert system_messages[0]["cache_control"] == {"type": "ephemeral"}

    # Check user message
    messages = call_args[1]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Check these files"

    # Check response
    assert response_text == '{"results": []}'
    assert response_obj == mock_response


@patch("claude_lint.api_client.Anthropic")
def test_get_usage_stats(mock_anthropic):
    """Test extracting usage statistics from response."""
    mock_response = Mock()
    mock_response.content = [Mock(text='{"results": []}')]
    mock_response.usage = Mock(
        input_tokens=100,
        output_tokens=50,
        cache_creation_input_tokens=200,
        cache_read_input_tokens=0,
    )
    mock_anthropic.return_value.messages.create.return_value = mock_response

    response_text, response_obj = analyze_files(
        api_key="test-key", guidelines="# Guidelines", prompt="Check files"
    )

    stats = get_usage_stats(response_obj)

    assert stats["input_tokens"] == 100
    assert stats["output_tokens"] == 50
    assert stats["cache_creation_tokens"] == 200
    assert stats["cache_read_tokens"] == 0


@patch("claude_lint.api_client.Anthropic")
def test_analyze_files_does_not_catch_keyboard_interrupt(mock_anthropic):
    """Test that KeyboardInterrupt is not caught."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = KeyboardInterrupt()
    mock_anthropic.return_value = mock_client

    with pytest.raises(KeyboardInterrupt):
        analyze_files("key", "guidelines", "prompt")


@patch("claude_lint.api_client.Anthropic")
def test_analyze_files_with_custom_model(mock_anthropic):
    """Test using a custom Claude model."""
    # Setup mock
    mock_response = Mock()
    mock_response.content = [Mock(text='{"results": []}')]
    mock_anthropic.return_value.messages.create.return_value = mock_response

    # Make request with custom model
    response_text, response_obj = analyze_files(
        api_key="test-key",
        guidelines="# Guidelines",
        prompt="Check these files",
        model="claude-opus-4-5-20250929",
    )

    # Verify custom model was used
    call_args = mock_anthropic.return_value.messages.create.call_args
    assert call_args[1]["model"] == "claude-opus-4-5-20250929"


def test_analyze_files_handles_timeout_error():
    """Test that APITimeoutError is logged and re-raised."""
    from anthropic import APITimeoutError

    # Create a mock request for the exception
    mock_request = Mock()
    mock_request.url = "https://api.anthropic.com/v1/messages"

    mock_client = Mock()
    mock_client.messages.create.side_effect = APITimeoutError(mock_request)

    with patch("claude_lint.api_client.logger") as mock_logger:
        with pytest.raises(APITimeoutError):
            from claude_lint.api_client import analyze_files_with_client

            analyze_files_with_client(
                mock_client,
                "# Guidelines",
                "Check this code",
            )

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "timed out" in mock_logger.error.call_args[0][0]


def test_analyze_files_handles_rate_limit_error():
    """Test that RateLimitError is logged and re-raised."""
    from anthropic import RateLimitError

    # Create mock response for the exception
    mock_response = Mock()
    mock_response.status_code = 429

    mock_client = Mock()
    mock_client.messages.create.side_effect = RateLimitError(
        "Rate limit exceeded", response=mock_response, body=None
    )

    with patch("claude_lint.api_client.logger") as mock_logger:
        with pytest.raises(RateLimitError):
            from claude_lint.api_client import analyze_files_with_client

            analyze_files_with_client(
                mock_client,
                "# Guidelines",
                "Check this code",
            )

        # Verify warning was logged (not error - rate limits are expected)
        mock_logger.warning.assert_called_once()
        assert "Rate limit" in mock_logger.warning.call_args[0][0]


def test_analyze_files_handles_connection_error():
    """Test that APIConnectionError is logged and re-raised."""
    from anthropic import APIConnectionError

    # Create a mock request for the exception
    mock_request = Mock()
    mock_request.url = "https://api.anthropic.com/v1/messages"

    mock_client = Mock()
    mock_client.messages.create.side_effect = APIConnectionError(
        message="Connection failed", request=mock_request
    )

    with patch("claude_lint.api_client.logger") as mock_logger:
        with pytest.raises(APIConnectionError):
            from claude_lint.api_client import analyze_files_with_client

            analyze_files_with_client(
                mock_client,
                "# Guidelines",
                "Check this code",
            )

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "connection failed" in mock_logger.error.call_args[0][0].lower()


def test_analyze_files_handles_generic_api_error():
    """Test that generic APIError is logged and re-raised."""
    from anthropic import APIError

    # Create a mock request for the exception
    mock_request = Mock()
    mock_request.url = "https://api.anthropic.com/v1/messages"

    mock_client = Mock()
    mock_client.messages.create.side_effect = APIError("API error", mock_request, body=None)

    with patch("claude_lint.api_client.logger") as mock_logger:
        with pytest.raises(APIError):
            from claude_lint.api_client import analyze_files_with_client

            analyze_files_with_client(
                mock_client,
                "# Guidelines",
                "Check this code",
            )

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "API error" in mock_logger.error.call_args[0][0]
