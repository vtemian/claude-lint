"""Claude API client with prompt caching support."""
from typing import Optional, Any
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError


def analyze_files(api_key: str, guidelines: str, prompt: str) -> tuple[str, Any]:
    """Analyze files using Claude API with cached guidelines.

    Args:
        api_key: Anthropic API key
        guidelines: CLAUDE.md content (will be cached)
        prompt: Prompt with files to analyze

    Returns:
        Tuple of (response text, response object)

    Raises:
        ValueError: If guidelines or prompt are empty or invalid
        APIError: If API call fails (includes connection, rate limit, etc.)
    """
    # Input validation
    if not guidelines or not isinstance(guidelines, str) or not guidelines.strip():
        raise ValueError("guidelines must be a non-empty string")
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")

    client = Anthropic(api_key=api_key)

    # Use prompt caching for guidelines
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": guidelines,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    except (APIError, APIConnectionError, RateLimitError) as e:
        # Re-raise specific API errors as-is
        raise
    except (KeyboardInterrupt, SystemExit):
        # Never catch these
        raise

    # Validate response
    if not response.content:
        raise ValueError("API returned empty response content")

    return response.content[0].text, response


def get_usage_stats(response: Any) -> dict:
    """Get usage statistics from API response.

    Args:
        response: Response object from Claude API

    Returns:
        Dict with token usage stats
    """
    usage = response.usage
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
        "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0)
    }
