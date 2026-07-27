"""Shared discovery and provenance helpers for CLAIRE4 benchmarks."""

from __future__ import annotations

import os
import platform
from pathlib import Path

from benchmarks.support import PROJECT_ROOT
from benchmarks.support import git_commit as git_commit
from benchmarks.support import git_dirty as git_dirty


def resolve_claire_root(explicit: Path | None = None) -> Path:
    """Locate CLAIRE4 explicitly, through the environment, or as a sibling."""

    candidates = (
        (explicit,)
        if explicit is not None
        else (
            (
                Path(environment_root)
                if (environment_root := os.environ.get("CLAIRE4_ROOT"))
                else None
            ),
            PROJECT_ROOT.parent / "CLAIRE4",
        )
    )
    for candidate in candidates:
        if candidate is not None and (candidate / "README").is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "CLAIRE4 was not found; pass --claire-root or set CLAIRE4_ROOT"
    )


def resolve_claire_binary(root: Path, explicit: Path | None = None) -> Path:
    """Select the bundled interpreter for the current platform."""

    if explicit is not None:
        binary = explicit
    elif platform.system() == "Darwin":
        binary = root / "interpreter" / "macos" / "claire4"
    elif platform.system() == "Linux":
        binary = root / "interpreter" / "ubuntu" / "claire4"
    else:
        raise OSError(
            "no bundled CLAIRE4 interpreter is known for this platform"
        )
    if not binary.is_file():
        raise FileNotFoundError(f"CLAIRE4 interpreter not found: {binary}")
    return binary.resolve()
