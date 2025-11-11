"""Progress tracking and resume capability."""
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class ProgressState:
    """State for progress tracking."""
    total_batches: int
    completed_batch_indices: list[int] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)


class ProgressTracker:
    """Tracks progress of file analysis for resume capability."""

    def __init__(self, progress_file: Path, total_batches: int):
        """Initialize progress tracker.

        Args:
            progress_file: Path to progress file
            total_batches: Total number of batches to process
        """
        self.progress_file = progress_file
        self.total_batches = total_batches
        self.state = ProgressState(total_batches=total_batches)

    @property
    def completed_batches(self) -> int:
        """Get number of completed batches."""
        return len(self.state.completed_batch_indices)

    def update(self, batch_index: int, results: list[dict[str, Any]]) -> None:
        """Update progress with batch results.

        Args:
            batch_index: Index of completed batch
            results: Results from this batch
        """
        if batch_index not in self.state.completed_batch_indices:
            self.state.completed_batch_indices.append(batch_index)

        self.state.results.extend(results)

    def save(self) -> None:
        """Save progress to file."""
        data = asdict(self.state)
        with open(self.progress_file, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, progress_file: Path) -> "ProgressTracker":
        """Load progress from file.

        Args:
            progress_file: Path to progress file

        Returns:
            ProgressTracker with loaded state
        """
        with open(progress_file) as f:
            data = json.load(f)

        tracker = cls(progress_file, total_batches=data["total_batches"])
        tracker.state = ProgressState(**data)
        return tracker

    def get_remaining_batch_indices(self) -> list[int]:
        """Get list of batch indices that still need processing.

        Returns:
            List of remaining batch indices
        """
        all_indices = set(range(self.total_batches))
        completed = set(self.state.completed_batch_indices)
        return sorted(all_indices - completed)

    def is_complete(self) -> bool:
        """Check if all batches are complete.

        Returns:
            True if all batches processed
        """
        return len(self.state.completed_batch_indices) == self.total_batches

    def get_progress_percentage(self) -> float:
        """Get progress as percentage.

        Returns:
            Progress percentage (0-100)
        """
        return (self.completed_batches / self.total_batches) * 100

    def cleanup(self) -> None:
        """Remove progress file."""
        if self.progress_file.exists():
            self.progress_file.unlink()
