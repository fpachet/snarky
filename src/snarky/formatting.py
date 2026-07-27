"""Conservative, comment-preserving formatting for Snarky source files."""

from __future__ import annotations

from dataclasses import dataclass

INDENT = "    "


@dataclass(frozen=True, slots=True)
class _Block:
    kind: str


def format_source(text: str) -> str:
    """Return canonically indented Snarky source without changing its meaning.

    The formatter deliberately leaves the contents of significant lines
    untouched.  It normalizes indentation, trailing whitespace, the final
    newline, and the historical ``END_EXISTS`` spelling after ``NOT EXISTS``.
    Comments and blank lines remain in their original order.
    """

    output: list[str] = []
    stack: list[_Block] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            output.append("")
            continue
        if stripped.startswith("#"):
            output.append(f"{INDENT * len(stack)}{stripped}")
            continue

        stripped = _canonical_terminator(stripped, stack)
        _close_before(stripped, stack)
        output.append(f"{INDENT * len(stack)}{stripped}")
        _open_after(stripped, stack)

    while output and not output[-1]:
        output.pop()
    return "\n".join(output) + ("\n" if output else "")


def _canonical_terminator(line: str, stack: list[_Block]) -> str:
    if (
        line == "END_EXISTS"
        and stack
        and stack[-1].kind == "NOT_EXISTS"
    ):
        return "END_NOT_EXISTS"
    return line


def _close_before(line: str, stack: list[_Block]) -> None:
    expected: str | None = None
    if line == "THEN":
        expected = "WHEN"
    elif line == "END_GROUP":
        expected = "GROUP"
    elif line == "END_PROGRAM":
        expected = "PROGRAM"
    elif line == "END_STEP":
        expected = "STEP"
    elif line == "END_FOR_EACH":
        expected = "FOR_EACH"
    elif line in {"END_CHOICE", "END_SCOPE", "END_BOUNDS", "END_TUPLES"}:
        expected = "FROM"
    elif line == "END_EXISTS":
        expected = "EXISTS"
    elif line == "END_NOT_EXISTS":
        expected = "NOT_EXISTS"
    elif line == "END_COUNT":
        expected = "COUNT"
    elif line == "END_UNIQUE":
        expected = "UNIQUE"
    elif line == "END_COLLECT":
        expected = "COLLECT"
    elif line == "END" and stack and stack[-1].kind == "THEN":
        expected = "THEN"
    if expected is not None:
        _pop_through(stack, expected)


def _pop_through(stack: list[_Block], expected: str) -> None:
    for index in range(len(stack) - 1, -1, -1):
        if stack[index].kind == expected:
            del stack[index:]
            return


def _open_after(line: str, stack: list[_Block]) -> None:
    if line.startswith("PROGRAM "):
        stack.append(_Block("PROGRAM"))
    elif line.startswith("STEP "):
        stack.append(_Block("STEP"))
    elif line.startswith("GROUP ") and not (
        stack and stack[-1].kind == "STEP"
    ):
        stack.append(_Block("GROUP"))
    elif line == "WHEN":
        stack.append(_Block("WHEN"))
    elif line == "THEN":
        stack.append(_Block("THEN"))
    elif line == "EXISTS":
        stack.append(_Block("EXISTS"))
    elif line == "NOT EXISTS":
        stack.append(_Block("NOT_EXISTS"))
    elif line.startswith("COUNT "):
        stack.append(_Block("COUNT"))
    elif line == "UNIQUE":
        stack.append(_Block("UNIQUE"))
    elif line.startswith("COLLECT "):
        stack.append(_Block("COLLECT"))
    elif line.startswith("FOR EACH "):
        stack.append(_Block("FOR_EACH"))
    elif line == "FROM":
        stack.append(_Block("FROM"))


__all__ = ["format_source"]
