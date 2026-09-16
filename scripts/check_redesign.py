"""Run the explicit non-Bach redesign conformance portfolio."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def selected_tests() -> list[str]:
    manifest = json.loads((ROOT / "tests/redesign_manifest.json").read_text())
    paths = {
        path.relative_to(ROOT).as_posix()
        for pattern in manifest["include"]
        for path in ROOT.glob(pattern)
    }
    missing = set(manifest["exclude"]) - paths
    if missing:
        raise ValueError(f"stale exclusion paths: {sorted(missing)}")
    return sorted(paths - set(manifest["exclude"]))


def main() -> None:
    command = [sys.executable, "-m", "pytest", *selected_tests(), *sys.argv[1:]]
    raise SystemExit(subprocess.call(command, cwd=ROOT))


if __name__ == "__main__":
    main()
