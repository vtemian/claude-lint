"""Batch processing and XML prompt generation."""
import json
import re
from typing import Any


def build_xml_prompt(claude_md_content: str, files: dict[str, str]) -> str:
    """Build XML prompt for Claude API.

    Args:
        claude_md_content: Content of CLAUDE.md
        files: Dict mapping file paths to their content

    Returns:
        XML formatted prompt
    """
    # Build files XML
    files_xml = ""
    for file_path, content in files.items():
        files_xml += f'  <file path="{file_path}">\n{content}\n  </file>\n'

    prompt = f"""<guidelines>
{claude_md_content}
</guidelines>

Check the following files for compliance with the guidelines above.
For each file, evaluate:
1. Pattern compliance - Does the code follow specific patterns mentioned?
2. Principle adherence - Does the code embody the philosophy described?
3. Anti-pattern detection - Does the code contain things warned against?

<files>
{files_xml}</files>

Return results in this JSON format:
{{
  "results": [
    {{
      "file": "path/to/file",
      "violations": [
        {{
          "type": "missing-pattern|principle-violation|anti-pattern",
          "message": "Description of the issue",
          "line": null or line number
        }}
      ]
    }}
  ]
}}

If a file has no violations, include it with an empty violations array.
"""

    return prompt


class BatchProcessor:
    """Processes files in batches."""

    def __init__(self, batch_size: int):
        """Initialize batch processor.

        Args:
            batch_size: Number of files per batch
        """
        self.batch_size = batch_size

    def create_batches(self, items: list[Any]) -> list[list[Any]]:
        """Split items into batches.

        Args:
            items: List of items to batch

        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(items), self.batch_size):
            batches.append(items[i:i + self.batch_size])
        return batches

    def parse_response(self, response: str) -> list[dict[str, Any]]:
        """Parse Claude API response to extract results.

        Args:
            response: Raw response text from Claude

        Returns:
            List of file results with violations
        """
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return []

        try:
            data = json.loads(json_str)
            return data.get("results", [])
        except json.JSONDecodeError:
            return []
