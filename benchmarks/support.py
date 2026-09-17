"""Shared provenance helpers for reproducible benchmark payloads."""

from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def git_commit(repository: Path) -> str | None:
    """Return a repository's current commit when it is available."""

    completed = subprocess.run(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() or None


def git_dirty(repository: Path) -> bool | None:
    """Return whether *repository* has tracked or untracked changes."""

    completed = subprocess.run(
        (
            "git",
            "-C",
            str(repository),
            "status",
            "--porcelain",
            "--untracked-files=normal",
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return bool(completed.stdout.strip())
