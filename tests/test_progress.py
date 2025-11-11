import json
import tempfile
from pathlib import Path
import pytest
from claude_lint.progress import ProgressTracker, ProgressState


def test_progress_tracker_initialization():
    """Test initializing progress tracker."""
    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = Path(tmpdir) / ".agent-lint-progress.json"

        tracker = ProgressTracker(progress_file, total_batches=5)

        assert tracker.total_batches == 5
        assert tracker.completed_batches == 0
        assert tracker.is_complete() is False


def test_update_progress():
    """Test updating progress."""
    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = Path(tmpdir) / ".agent-lint-progress.json"

        tracker = ProgressTracker(progress_file, total_batches=3)

        tracker.update(batch_index=0, results=[{"file": "a.py", "violations": []}])
        tracker.update(batch_index=1, results=[{"file": "b.py", "violations": []}])

        assert tracker.completed_batches == 2
        assert tracker.get_progress_percentage() == pytest.approx(66.7, rel=0.1)


def test_save_and_load_progress():
    """Test saving and loading progress."""
    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = Path(tmpdir) / ".agent-lint-progress.json"

        # Create and save progress
        tracker = ProgressTracker(progress_file, total_batches=5)
        tracker.update(batch_index=0, results=[{"file": "a.py", "violations": []}])
        tracker.update(batch_index=1, results=[{"file": "b.py", "violations": []}])
        tracker.save()

        # Load progress
        loaded = ProgressTracker.load(progress_file)

        assert loaded.total_batches == 5
        assert loaded.completed_batches == 2
        assert 0 in loaded.state.completed_batch_indices
        assert 1 in loaded.state.completed_batch_indices


def test_resume_from_progress():
    """Test resuming from saved progress."""
    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = Path(tmpdir) / ".agent-lint-progress.json"

        # Create initial progress
        tracker = ProgressTracker(progress_file, total_batches=5)
        tracker.update(batch_index=0, results=[{"file": "a.py", "violations": []}])
        tracker.update(batch_index=2, results=[{"file": "c.py", "violations": []}])
        tracker.save()

        # Resume
        resumed = ProgressTracker.load(progress_file)
        remaining = resumed.get_remaining_batch_indices()

        assert remaining == [1, 3, 4]


def test_cleanup_on_complete():
    """Test that progress file is cleaned up when complete."""
    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = Path(tmpdir) / ".agent-lint-progress.json"

        tracker = ProgressTracker(progress_file, total_batches=2)
        tracker.update(batch_index=0, results=[])
        tracker.update(batch_index=1, results=[])
        tracker.save()

        assert tracker.is_complete() is True
        tracker.cleanup()

        assert not progress_file.exists()
