"""Claude API client with prompt caching support."""
from typing import Optional
from anthropic import Anthropic


class ClaudeClient:
    """Client for Claude API with prompt caching."""

    def __init__(self, api_key: str):
        """Initialize Claude API client.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.last_response = None

    def analyze_files(self, guidelines: str, prompt: str) -> str:
        """Analyze files using Claude API with cached guidelines.

        Args:
            guidelines: CLAUDE.md content (will be cached)
            prompt: Prompt with files to analyze

        Returns:
            Response text from Claude
        """
        # Use prompt caching for guidelines
        response = self.client.messages.create(
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

        self.last_response = response
        return response.content[0].text

    def get_last_usage_stats(self) -> Optional[dict]:
        """Get usage statistics from last API call.

        Returns:
            Dict with token usage stats or None if no request made
        """
        if self.last_response is None:
            return None

        usage = self.last_response.usage
        return {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
            "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0)
        }
