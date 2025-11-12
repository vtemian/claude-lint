"""Tests for orchestrator input validation."""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from claude_lint.config import Config
from claude_lint.orchestrator import run_compliance_check


def test_run_compliance_check_raises_on_none_api_key():
    """Test that None API key after validation raises explicit error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "CLAUDE.md").write_text("# Guidelines")
        # Create a Python file so there are files to check
        (tmpdir / "test.py").write_text("# Test file")

        config = Config(
            include=["**/*.py"],
            exclude=[],
            batch_size=10,
            api_key=None,
        )

        # Mock validate_api_key to pass (simulating validation bug)
        with patch("claude_lint.orchestrator.validate_api_key"):
            # Mock os.environ.get to return None
            with patch("os.environ.get", return_value=None):
                # Should raise explicit ValueError, not pass None to create_client
                with pytest.raises(ValueError, match="API key is required but was None"):
                    run_compliance_check(tmpdir, config, mode="full")
