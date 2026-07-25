"""Check local links in first-party Markdown documents."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "third_party",
}


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not EXCLUDED_PARTS.intersection(path.parts)
    )


def broken_links(root: Path) -> list[str]:
    broken: list[str] = []
    for document in markdown_files(root):
        text = document.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip().strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            path_text = unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            destination = (document.parent / path_text).resolve()
            if not destination.exists():
                line = text.count("\n", 0, match.start()) + 1
                relative = document.relative_to(root)
                broken.append(f"{relative}:{line}: {target}")
    return broken


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    failures = broken_links(root)
    if failures:
        rendered = "\n".join(f"  {failure}" for failure in failures)
        raise SystemExit(f"broken local Markdown links:\n{rendered}")
    print("first-party Markdown links: ok")


if __name__ == "__main__":
    main()
