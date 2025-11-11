"""Cache management for file analysis results."""
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class CacheEntry:
    """Cache entry for a single file."""
    file_hash: str
    claude_md_hash: str
    violations: list[str]
    timestamp: int


@dataclass
class Cache:
    """Cache for analysis results."""
    claude_md_hash: str
    entries: dict[str, CacheEntry]


def load_cache(cache_path: Path) -> Cache:
    """Load cache from file or return empty cache.

    Args:
        cache_path: Path to cache file

    Returns:
        Cache object
    """
    if not cache_path.exists():
        return Cache(claude_md_hash="", entries={})

    with open(cache_path) as f:
        data = json.load(f)

    entries = {}
    for file_path, entry_data in data.get("entries", {}).items():
        entries[file_path] = CacheEntry(**entry_data)

    return Cache(
        claude_md_hash=data.get("claudeMdHash", ""),
        entries=entries
    )


def save_cache(cache: Cache, cache_path: Path) -> None:
    """Save cache to file.

    Args:
        cache: Cache object to save
        cache_path: Path to cache file
    """
    entries_dict = {}
    for file_path, entry in cache.entries.items():
        entries_dict[file_path] = asdict(entry)

    data = {
        "claudeMdHash": cache.claude_md_hash,
        "entries": entries_dict
    }

    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)
