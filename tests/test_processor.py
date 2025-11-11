from pathlib import Path
import pytest
from claude_lint.processor import BatchProcessor, build_xml_prompt


def test_build_xml_prompt():
    """Test building XML prompt for Claude API."""
    claude_md_content = "# Guidelines\n\nFollow TDD."
    files = {
        "src/main.py": "def main():\n    pass",
        "src/utils.py": "def helper():\n    return 42"
    }

    prompt = build_xml_prompt(claude_md_content, files)

    # Check structure
    assert "<guidelines>" in prompt
    assert "Follow TDD" in prompt
    assert "</guidelines>" in prompt
    assert "<files>" in prompt
    assert '<file path="src/main.py">' in prompt
    assert '<file path="src/utils.py">' in prompt
    assert "def main()" in prompt
    assert "def helper()" in prompt
    assert "</files>" in prompt


def test_batch_files():
    """Test batching files into groups."""
    files = [f"file{i}.py" for i in range(25)]
    batch_size = 10

    processor = BatchProcessor(batch_size)
    batches = processor.create_batches(files)

    assert len(batches) == 3  # 10, 10, 5
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5


def test_parse_response():
    """Test parsing Claude API response."""
    response = """
    Here are the compliance issues:

    ```json
    {
      "results": [
        {
          "file": "src/main.py",
          "violations": [
            {
              "type": "missing-pattern",
              "message": "No tests found for this module",
              "line": null
            }
          ]
        },
        {
          "file": "src/utils.py",
          "violations": []
        }
      ]
    }
    ```
    """

    processor = BatchProcessor(batch_size=10)
    results = processor.parse_response(response)

    assert len(results) == 2
    assert results[0]["file"] == "src/main.py"
    assert len(results[0]["violations"]) == 1
    assert results[1]["file"] == "src/utils.py"
    assert len(results[1]["violations"]) == 0
