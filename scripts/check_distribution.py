"""Verify that built distributions contain only publishable package sources."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

FORBIDDEN_PREFIXES = (
    "benchmarks/results/",
    "docs/",
    "harmonizer/generated/",
    "spinoza/",
    "third_party/",
)
FORBIDDEN_SUFFIXES = (
    ".doc",
    ".docx",
    ".mid",
    ".musicxml",
    ".pdf",
    ".ppt",
    ".pptx",
)
REQUIRED_SDIST = {
    "CHANGELOG.md",
    "LICENSE_STATUS.md",
    "README.md",
    "THIRD_PARTY.md",
    "pyproject.toml",
    "src/snarky/__init__.py",
}
REQUIRED_WHEEL = {
    "snarky/__init__.py",
    "snarky/py.typed",
}


def _relative_sdist_names(names: list[str]) -> set[str]:
    relative: set[str] = set()
    for name in names:
        parts = PurePosixPath(name).parts
        if len(parts) > 1:
            relative.add(PurePosixPath(*parts[1:]).as_posix())
    return relative


def _assert_safe(names: set[str], archive: Path) -> None:
    forbidden = sorted(
        name
        for name in names
        if name.lower().endswith(FORBIDDEN_SUFFIXES)
        or name.startswith(FORBIDDEN_PREFIXES)
    )
    if forbidden:
        rendered = "\n".join(f"  {name}" for name in forbidden)
        raise ValueError(f"private or generated material in {archive}:\n{rendered}")


def check_sdist(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        names = _relative_sdist_names(archive.getnames())
    _assert_safe(names, path)
    missing = REQUIRED_SDIST - names
    if missing:
        raise ValueError(f"required sdist files missing: {sorted(missing)}")


def check_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    _assert_safe(names, path)
    missing = REQUIRED_WHEEL - names
    if missing:
        raise ValueError(f"required wheel files missing: {sorted(missing)}")


def find_one(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise ValueError(f"expected one {pattern} in {directory}, found {len(matches)}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path("dist"),
        help="directory containing one Snarky sdist and one wheel",
    )
    directory = parser.parse_args().directory
    check_sdist(find_one(directory, "snarky-*.tar.gz"))
    check_wheel(find_one(directory, "snarky-*.whl"))
    print("distribution contents: ok")


if __name__ == "__main__":
    main()
