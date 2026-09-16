"""Command-line interface for Snarky validation and formatting."""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Sequence
from pathlib import Path

from .formatting import format_source
from .tooling import (
    DiagnosticSeverity,
    discover_source_files,
    validate_paths,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Snarky developer CLI and return its process status."""

    parser = _argument_parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "check":
        return _check(arguments)
    if arguments.command == "format":
        return _format(arguments)
    if arguments.command == "run":
        from .finite.cli import run_document

        return run_document(arguments.path, arguments.query, explain=arguments.explain)
    parser.error("a command is required")
    return 2


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snarky",
        description="Validate and format Snarky textual source files.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser(
        "check",
        help="validate .rules, .constraints, .program, and .model files",
    )
    check.add_argument("paths", nargs="*", default=["."])
    check.add_argument(
        "--syntax-only",
        action="store_true",
        help="do not link program references across the selected files",
    )
    check.add_argument(
        "--strict-links",
        action="store_true",
        help="reject program references not declared in selected text files",
    )
    check.add_argument(
        "--format",
        action="store_true",
        dest="check_format",
        help="also require canonical formatting",
    )

    formatter = commands.add_parser(
        "format",
        help="apply canonical indentation while preserving comments",
    )
    formatter.add_argument("paths", nargs="*", default=["."])
    output = formatter.add_mutually_exclusive_group()
    output.add_argument(
        "--check",
        action="store_true",
        help="report files that would change without writing them",
    )
    output.add_argument(
        "--diff",
        action="store_true",
        help="print unified diffs without writing files",
    )
    run = commands.add_parser("run", help="execute a finite .model query")
    run.add_argument("path", help="MODEL source file")
    run.add_argument("--query", help="query name (required for multiple queries)")
    run.add_argument(
        "--explain", action="store_true", help="include proof and score details"
    )
    return parser


def _check(arguments: argparse.Namespace) -> int:
    result = validate_paths(
        arguments.paths,
        syntax_only=arguments.syntax_only,
        strict_links=arguments.strict_links,
        check_format=arguments.check_format,
    )
    for diagnostic in result.diagnostics:
        print(diagnostic.render(), file=sys.stderr)
    if result.ok:
        suffix = f", {len(result.warnings)} warning(s)" if result.warnings else ""
        print(f"checked {len(result.files)} file(s){suffix}")
        return 0
    print(
        f"found {len(result.errors)} error(s) in {len(result.files)} file(s)",
        file=sys.stderr,
    )
    return 1


def _format(arguments: argparse.Namespace) -> int:
    result = validate_paths(arguments.paths, syntax_only=True)
    errors = [
        diagnostic
        for diagnostic in result.diagnostics
        if diagnostic.severity is DiagnosticSeverity.ERROR
    ]
    if errors:
        for diagnostic in errors:
            print(diagnostic.render(), file=sys.stderr)
        print("formatting aborted because validation failed", file=sys.stderr)
        return 1

    changed = 0
    for path in discover_source_files(arguments.paths):
        original = path.read_text(encoding="utf-8")
        formatted = format_source(original)
        if formatted == original:
            continue
        changed += 1
        if arguments.diff:
            _print_diff(path, original, formatted)
        elif arguments.check:
            print(f"would reformat {path}")
        else:
            path.write_text(formatted, encoding="utf-8")
            print(f"reformatted {path}")
    if arguments.check or arguments.diff:
        return 1 if changed else 0
    print(f"reformatted {changed} file(s)")
    return 0


def _print_diff(path: Path, original: str, formatted: str) -> None:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        formatted.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    sys.stdout.writelines(diff)


__all__ = ["main"]
