import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from claude_lint.cache import Cache, CacheEntry
from claude_lint.config import Config
from claude_lint.orchestrator import (
    collect_files_for_mode,
    filter_cached_files,
    get_cached_results,
    init_or_load_progress,
    run_compliance_check,
)


@patch("claude_lint.batch_processor.analyze_files_with_client")
@patch("claude_lint.orchestrator.create_client")
@patch("claude_lint.orchestrator.is_git_repo")
def test_orchestrator_full_scan(mock_is_git, mock_create_client, mock_analyze):
    """Test full project scan mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files
        (tmpdir / "file1.py").write_text("print('hello')")
        (tmpdir / "file2.py").write_text("print('world')")
        (tmpdir / "CLAUDE.md").write_text("# Guidelines\n\nUse TDD.")

        # Mock git check
        mock_is_git.return_value = False

        # Mock client creation
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        # Mock Claude API
        mock_analyze.return_value = (
            """
        ```json
        {
          "results": [
            {"file": "file1.py", "violations": []},
            {"file": "file2.py", "violations": []}
          ]
        }
        ```
        """,
            Mock(),
        )

        # Run orchestrator
        config = Config(
            include=["**/*.py"],
            exclude=["tests/**"],
            batch_size=10,
            api_key="sk-ant-" + "x" * 50,  # Valid test key format
        )

        results, metrics = run_compliance_check(tmpdir, config, mode="full")

        # Verify
        assert len(results) == 2
        assert mock_analyze.called
        assert mock_create_client.called
        assert metrics.total_files_collected == 2


@patch("claude_lint.batch_processor.analyze_files_with_client")
@patch("claude_lint.orchestrator.create_client")
@patch("claude_lint.orchestrator.get_changed_files_from_branch")
@patch("claude_lint.orchestrator.is_git_repo")
def test_orchestrator_diff_mode(mock_is_git, mock_git_diff, mock_create_client, mock_analyze):
    """Test diff mode with git."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files
        (tmpdir / "file1.py").write_text("code")
        (tmpdir / "file2.py").write_text("code")
        (tmpdir / "CLAUDE.md").write_text("# Guidelines")

        # Mock git
        mock_is_git.return_value = True
        mock_git_diff.return_value = ["file1.py"]  # Only file1 changed

        # Mock client creation
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        # Mock Claude API
        mock_analyze.return_value = (
            """
        ```json
        {"results": [{"file": "file1.py", "violations": []}]}
        ```
        """,
            Mock(),
        )

        # Run orchestrator
        config = Config(
            include=["**/*.py"],
            exclude=[],
            batch_size=10,
            api_key="sk-ant-" + "x" * 50,  # Valid test key format
        )

        results, metrics = run_compliance_check(tmpdir, config, mode="diff", base_branch="main")

        # Verify only file1 was checked
        assert len(results) == 1
        assert results[0]["file"] == "file1.py"
        assert mock_create_client.called
        assert metrics.total_files_collected == 1


@patch("claude_lint.orchestrator.collect_all_files")
@patch("claude_lint.orchestrator.is_git_repo")
def test_orchestrator_no_files_collected(mock_is_git, mock_collect):
    """Test early return when no files are collected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "CLAUDE.md").write_text("# Guidelines")

        mock_is_git.return_value = False
        mock_collect.return_value = []  # No files collected

        config = Config(
            include=["**/*.py"],
            exclude=[],
            batch_size=10,
            api_key="sk-ant-" + "x" * 50,
        )

        results, metrics = run_compliance_check(tmpdir, config, mode="full")

        # Should return empty results without calling API
        assert results == []
        assert metrics.total_files_collected == 0
        assert metrics.files_analyzed == 0


@patch("claude_lint.orchestrator.collect_all_files")
@patch("claude_lint.orchestrator.is_git_repo")
def test_orchestrator_all_files_cached(mock_is_git, mock_collect):
    """Test return path when all files are cached."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "file1.py").write_text("print('hello')")
        (tmpdir / "CLAUDE.md").write_text("# Guidelines")

        # Setup cache with entry for file1.py
        cache_path = tmpdir / ".agent-lint-cache.json"
        file_path = tmpdir / "file1.py"

        # Compute actual hash for the file
        import hashlib

        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        guidelines_hash = hashlib.sha256(b"# Guidelines").hexdigest()

        cache_data = {
            "entries": {
                "file1.py": {
                    "file_hash": file_hash,
                    "claude_md_hash": guidelines_hash,
                    "violations": [],
                    "timestamp": 1234567890.0,
                }
            },
            "claude_md_hash": guidelines_hash,
        }
        cache_path.write_text(json.dumps(cache_data))

        mock_is_git.return_value = False
        mock_collect.return_value = [file_path]

        config = Config(
            include=["**/*.py"],
            exclude=[],
            batch_size=10,
            api_key="sk-ant-" + "x" * 50,
        )

        results, metrics = run_compliance_check(tmpdir, config, mode="full")

        # Should return cached results without calling API
        assert len(results) == 1
        assert results[0]["file"] == "file1.py"
        assert results[0]["violations"] == []
        assert metrics.files_from_cache == 1
        assert metrics.cache_hits == 1


@patch("claude_lint.orchestrator.is_git_repo")
def test_collect_files_for_mode_diff_not_git_repo(mock_is_git):
    """Test error when using diff mode in non-git repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        mock_is_git.return_value = False

        config = Config(include=["**/*.py"], exclude=[], batch_size=10)

        with pytest.raises(ValueError, match="requires git repository"):
            collect_files_for_mode(tmpdir, config, "diff", "main")


@patch("claude_lint.orchestrator.is_git_repo")
def test_collect_files_for_mode_diff_no_base_branch(mock_is_git):
    """Test error when diff mode missing base_branch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        mock_is_git.return_value = True

        config = Config(include=["**/*.py"], exclude=[], batch_size=10)

        with pytest.raises(ValueError, match="requires base_branch"):
            collect_files_for_mode(tmpdir, config, "diff", None)


@patch("claude_lint.orchestrator.get_working_directory_files")
@patch("claude_lint.orchestrator.filter_files_by_list")
@patch("claude_lint.orchestrator.is_git_repo")
def test_collect_files_for_mode_working(mock_is_git, mock_filter, mock_get_working):
    """Test working mode file collection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        mock_is_git.return_value = True
        mock_get_working.return_value = ["file1.py", "file2.py"]
        mock_filter.return_value = [Path(tmpdir / "file1.py")]

        config = Config(include=["**/*.py"], exclude=[], batch_size=10)

        result = collect_files_for_mode(tmpdir, config, "working", None)

        assert mock_get_working.called
        assert mock_filter.called
        assert result == [Path(tmpdir / "file1.py")]


@patch("claude_lint.orchestrator.get_staged_files")
@patch("claude_lint.orchestrator.filter_files_by_list")
@patch("claude_lint.orchestrator.is_git_repo")
def test_collect_files_for_mode_staged(mock_is_git, mock_filter, mock_get_staged):
    """Test staged mode file collection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        mock_is_git.return_value = True
        mock_get_staged.return_value = ["file1.py"]
        mock_filter.return_value = [Path(tmpdir / "file1.py")]

        config = Config(include=["**/*.py"], exclude=[], batch_size=10)

        result = collect_files_for_mode(tmpdir, config, "staged", None)

        assert mock_get_staged.called
        assert mock_filter.called
        assert result == [Path(tmpdir / "file1.py")]


@patch("claude_lint.orchestrator.is_git_repo")
def test_collect_files_for_mode_unknown(mock_is_git):
    """Test error for unknown mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        mock_is_git.return_value = True

        config = Config(include=["**/*.py"], exclude=[], batch_size=10)

        with pytest.raises(ValueError, match="Unknown mode"):
            collect_files_for_mode(tmpdir, config, "invalid_mode", None)


def test_filter_cached_files_no_cache_entry():
    """Test filtering when file not in cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file_path = tmpdir / "file1.py"
        file_path.write_text("print('hello')")

        cache = Cache(entries={}, claude_md_hash="hash123")

        result = filter_cached_files([file_path], cache, tmpdir, "hash123")

        # File not in cache, should need checking
        assert result == [file_path]


def test_filter_cached_files_claude_md_changed():
    """Test filtering when CLAUDE.md hash changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file_path = tmpdir / "file1.py"
        file_path.write_text("print('hello')")

        import hashlib

        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

        entry = CacheEntry(
            file_hash=file_hash,
            claude_md_hash="old_hash",
            violations=[],
            timestamp=1234567890.0,
        )
        cache = Cache(entries={"file1.py": entry}, claude_md_hash="old_hash")

        result = filter_cached_files([file_path], cache, tmpdir, "new_hash")

        # CLAUDE.md changed, should need checking
        assert result == [file_path]


def test_filter_cached_files_file_content_changed():
    """Test filtering when file content changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file_path = tmpdir / "file1.py"
        file_path.write_text("print('hello')")

        entry = CacheEntry(
            file_hash="old_file_hash",
            claude_md_hash="hash123",
            violations=[],
            timestamp=1234567890.0,
        )
        cache = Cache(entries={"file1.py": entry}, claude_md_hash="hash123")

        result = filter_cached_files([file_path], cache, tmpdir, "hash123")

        # File content changed, should need checking
        assert result == [file_path]


def test_filter_cached_files_valid_cache():
    """Test filtering when cache is valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file_path = tmpdir / "file1.py"
        file_path.write_text("print('hello')")

        import hashlib

        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

        entry = CacheEntry(
            file_hash=file_hash,
            claude_md_hash="hash123",
            violations=[],
            timestamp=1234567890.0,
        )
        cache = Cache(entries={"file1.py": entry}, claude_md_hash="hash123")

        result = filter_cached_files([file_path], cache, tmpdir, "hash123")

        # Cache valid, should not need checking
        assert result == []


def test_get_cached_results():
    """Test getting cached results for files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file1 = tmpdir / "file1.py"
        file2 = tmpdir / "file2.py"

        entry1 = CacheEntry(
            file_hash="hash1",
            claude_md_hash="md_hash",
            violations=[{"line": 1, "message": "Issue"}],
            timestamp=1234567890.0,
        )
        entry2 = CacheEntry(
            file_hash="hash2",
            claude_md_hash="md_hash",
            violations=[],
            timestamp=1234567890.0,
        )

        cache = Cache(
            entries={"file1.py": entry1, "file2.py": entry2},
            claude_md_hash="md_hash",
        )

        results = get_cached_results([file1, file2], cache, tmpdir)

        assert len(results) == 2
        assert results[0]["file"] == "file1.py"
        assert results[0]["violations"] == [{"line": 1, "message": "Issue"}]
        assert results[1]["file"] == "file2.py"
        assert results[1]["violations"] == []


def test_get_cached_results_partial():
    """Test getting cached results when only some files are cached."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file1 = tmpdir / "file1.py"
        file2 = tmpdir / "file2.py"

        entry1 = CacheEntry(
            file_hash="hash1",
            claude_md_hash="md_hash",
            violations=[],
            timestamp=1234567890.0,
        )

        cache = Cache(entries={"file1.py": entry1}, claude_md_hash="md_hash")

        results = get_cached_results([file1, file2], cache, tmpdir)

        # Only file1 is cached, so only get one result
        assert len(results) == 1
        assert results[0]["file"] == "file1.py"


def test_init_or_load_progress_create_new():
    """Test creating new progress state when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        progress_path = tmpdir / ".agent-lint-progress.json"

        progress = init_or_load_progress(progress_path, 5)

        assert progress.total_batches == 5
        assert progress.completed_batch_indices == []
        assert progress.results == []


def test_init_or_load_progress_load_existing():
    """Test loading existing progress state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        progress_path = tmpdir / ".agent-lint-progress.json"

        # Create existing progress file
        progress_data = {
            "total_batches": 5,
            "completed_batch_indices": [0, 1],
            "results": [{"file": "test.py", "violations": []}],
        }
        progress_path.write_text(json.dumps(progress_data))

        progress = init_or_load_progress(progress_path, 5)

        assert progress.total_batches == 5
        assert progress.completed_batch_indices == [0, 1]
        assert len(progress.results) == 1
