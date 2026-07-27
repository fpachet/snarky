"""Validation and file discovery for Snarky's textual languages."""

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from .computed import ComputedPredicate, PredicateRegistry
from .formatting import format_source
from .parser import (
    ParseError,
    parse_rule_groups,
    parse_rule_program,
    parse_rules,
)
from .rules import RuleGroup

SUPPORTED_SUFFIXES = frozenset({".rules", ".constraints", ".program"})
DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "third_party",
    }
)

_COMPUTED_NAME_RE = re.compile(
    r"^\s*(?:CHECK\s+(?P<check>[A-Za-z_][A-Za-z0-9_]*)"
    r"|COMPUTE\s+\$[^\s]+\s*:=\s*(?P<compute>[A-Za-z_][A-Za-z0-9_]*))"
)
_VARIABLE_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_-]*")
_QUOTED_RE = re.compile(r"(?:got|input|action)\s+(?P<value>'(?:\\.|[^'])*')")


class DiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One source-oriented validation or formatting diagnostic."""

    path: Path
    line: int
    column: int
    severity: DiagnosticSeverity
    code: str
    message: str
    source_line: str = ""
    help: str | None = None

    def render(self) -> str:
        """Render a stable, terminal-friendly diagnostic."""

        header = (
            f"{self.path}:{self.line}:{self.column}: "
            f"{self.severity} [{self.code}] {self.message}"
        )
        if not self.source_line:
            return header + (
                f"\nhelp: {self.help}" if self.help is not None else ""
            )
        pointer = " " * max(self.column - 1, 0) + "^"
        rendered = f"{header}\n    {self.source_line}\n    {pointer}"
        if self.help is not None:
            rendered += f"\nhelp: {self.help}"
        return rendered


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Diagnostics and file count produced by one validation run."""

    files: tuple[Path, ...]
    diagnostics: tuple[Diagnostic, ...]

    @property
    def errors(self) -> tuple[Diagnostic, ...]:
        return tuple(
            item
            for item in self.diagnostics
            if item.severity is DiagnosticSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[Diagnostic, ...]:
        return tuple(
            item
            for item in self.diagnostics
            if item.severity is DiagnosticSeverity.WARNING
        )

    @property
    def ok(self) -> bool:
        return not self.errors


def discover_source_files(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    """Resolve files and directories into a stable supported-source list."""

    discovered: set[Path] = set()
    for candidate in paths:
        path = Path(candidate)
        if path.is_file():
            if path.suffix in SUPPORTED_SUFFIXES:
                discovered.add(path)
            continue
        if not path.is_dir():
            continue
        for child in path.rglob("*"):
            if not child.is_file() or child.suffix not in SUPPORTED_SUFFIXES:
                continue
            if any(
                part in DEFAULT_EXCLUDED_DIRECTORIES
                for part in child.relative_to(path).parts[:-1]
            ):
                continue
            discovered.add(child)
    return tuple(sorted(discovered, key=lambda item: str(item)))


def validate_paths(
    paths: Iterable[str | Path],
    *,
    syntax_only: bool = False,
    strict_links: bool = False,
    check_format: bool = False,
) -> ValidationResult:
    """Validate rule, constraint, and program sources.

    Directory validation compares program references with all groups and
    persistent constraints found in the selected source set. References not
    found in text are warnings because applications may provide them from
    Python. ``strict_links`` promotes those warnings to errors. ``syntax_only``
    disables cross-file reference checks.
    """

    requested = tuple(Path(path) for path in paths)
    files = discover_source_files(requested)
    diagnostics: list[Diagnostic] = []
    for path in requested:
        if not path.exists():
            diagnostics.append(
                Diagnostic(
                    path,
                    1,
                    1,
                    DiagnosticSeverity.ERROR,
                    "SNK002",
                    "source path does not exist",
                )
            )
        elif path.is_file() and path.suffix not in SUPPORTED_SUFFIXES:
            diagnostics.append(
                Diagnostic(
                    path,
                    1,
                    1,
                    DiagnosticSeverity.ERROR,
                    "SNK003",
                    f"unsupported Snarky source suffix {path.suffix!r}",
                    help="use .rules, .constraints, or .program",
                )
            )
    group_names: set[str] = set()
    constraint_names: set[str] = set()
    programs: list[tuple[Path, str]] = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        diagnostics.extend(_style_diagnostics(path, text))
        if check_format and format_source(text) != text:
            diagnostics.append(
                Diagnostic(
                    path,
                    1,
                    1,
                    DiagnosticSeverity.ERROR,
                    "SNK001",
                    "source is not canonically formatted",
                    help=f"run `snarky format {path}`",
                )
            )
        if path.suffix == ".program":
            programs.append((path, text))
            continue
        try:
            if path.suffix == ".rules":
                parsed = _parse_rules_source(text)
                if parsed and isinstance(parsed[0], RuleGroup):
                    group_names.update(group.name for group in parsed)
            else:
                templates = _parse_constraint_source(text)
                constraint_names.update(
                    str(template.name) for template in templates
                )
        except (ParseError, ValueError) as error:
            diagnostics.append(_diagnostic_from_error(path, text, error))

    for path, text in programs:
        try:
            referenced_groups, referenced_constraints = _program_references(
                text
            )
            _parse_program_source(
                text,
                referenced_groups,
                referenced_constraints,
            )
            if not syntax_only:
                severity = (
                    DiagnosticSeverity.ERROR
                    if strict_links
                    else DiagnosticSeverity.WARNING
                )
                for name in sorted(referenced_groups - group_names):
                    diagnostics.append(
                        _reference_diagnostic(
                            path,
                            text,
                            "group",
                            name,
                            severity,
                        )
                    )
                for name in sorted(
                    referenced_constraints - constraint_names
                ):
                    diagnostics.append(
                        _reference_diagnostic(
                            path,
                            text,
                            "constraint",
                            name,
                            severity,
                        )
                    )
        except (ParseError, ValueError) as error:
            diagnostics.append(_diagnostic_from_error(path, text, error))

    return ValidationResult(
        files,
        tuple(
            sorted(
                diagnostics,
                key=lambda item: (
                    str(item.path),
                    item.line,
                    item.column,
                    item.code,
                ),
            )
        ),
    )


def validate_source(
    text: str,
    *,
    path: str | Path = "<memory>.rules",
) -> tuple[Diagnostic, ...]:
    """Validate one source independently and return structured diagnostics."""

    source_path = Path(path)
    diagnostics = list(_style_diagnostics(source_path, text))
    try:
        if source_path.suffix == ".rules":
            _parse_rules_source(text)
        elif source_path.suffix == ".constraints":
            _parse_constraint_source(text)
        elif source_path.suffix == ".program":
            groups, constraints = _program_references(text)
            _parse_program_source(text, groups, constraints)
        else:
            diagnostics.append(
                Diagnostic(
                    source_path,
                    1,
                    1,
                    DiagnosticSeverity.ERROR,
                    "SNK003",
                    f"unsupported Snarky source suffix {source_path.suffix!r}",
                    help="use .rules, .constraints, or .program",
                )
            )
    except (ParseError, ValueError) as error:
        diagnostics.append(_diagnostic_from_error(source_path, text, error))
    return tuple(diagnostics)


def _parse_rules_source(text: str) -> tuple[Any, ...]:
    registry = _placeholder_predicates(text)
    first = _first_significant_line(text)
    if first.startswith("GROUP "):
        return cast(
            tuple[Any, ...],
            parse_rule_groups(text, predicates=registry),
        )
    return cast(tuple[Any, ...], parse_rules(text, predicates=registry))


def _parse_constraint_source(text: str) -> tuple[Any, ...]:
    try:
        module = import_module("csp_solver.constraint_syntax")
    except ImportError as error:
        raise ParseError(
            "persistent-constraint validation requires the companion "
            "`csp_solver` package"
        ) from error
    parse_constraint_templates = cast(
        Callable[[str], tuple[Any, ...]],
        module.parse_constraint_templates,
    )
    return parse_constraint_templates(text)


def _parse_program_source(
    text: str,
    group_names: Iterable[str],
    constraint_names: Iterable[str],
) -> None:
    groups = tuple(
        RuleGroup(name, ())
        for name in sorted(set(group_names))
    )

    def placeholder_propagator(session: Any) -> None:
        del session

    constraints = {
        name: placeholder_propagator
        for name in set(constraint_names)
    }
    parse_rule_program(text, groups, constraints=constraints)


def _placeholder_predicates(text: str) -> PredicateRegistry:
    names: set[str] = set()
    for line in text.splitlines():
        match = _COMPUTED_NAME_RE.match(line)
        if match is None:
            continue
        name = match.group("check") or match.group("compute")
        if name is not None:
            names.add(name)

    def placeholder(arguments: tuple[Any, ...]) -> bool:
        del arguments
        return True

    return PredicateRegistry(
        ComputedPredicate(name, placeholder)
        for name in sorted(names)
    )


def _program_references(text: str) -> tuple[set[str], set[str]]:
    groups: set[str] = set()
    constraints: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        for prefix in ("PREPARE ", "CHOOSE ", "PROPAGATE ", "INTERPRET ", "GROUP "):
            if stripped.startswith(prefix):
                groups.add(stripped.removeprefix(prefix).strip())
                break
        if stripped.startswith("CONSTRAINT "):
            constraints.add(stripped.removeprefix("CONSTRAINT ").strip())
    return groups, constraints


def _style_diagnostics(path: Path, text: str) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    nested: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped == "NOT EXISTS":
            nested.append("NOT_EXISTS")
        elif stripped == "EXISTS":
            nested.append("EXISTS")
        elif stripped == "END_NOT_EXISTS":
            if nested:
                nested.pop()
        elif stripped == "END_EXISTS":
            if nested and nested[-1] == "NOT_EXISTS":
                diagnostics.append(
                    Diagnostic(
                        path,
                        line_number,
                        len(raw_line) - len(raw_line.lstrip()) + 1,
                        DiagnosticSeverity.WARNING,
                        "SNK101",
                        "NOT EXISTS should use END_NOT_EXISTS",
                        raw_line,
                        help="`snarky format` applies the canonical terminator",
                    )
                )
            if nested:
                nested.pop()
    return tuple(diagnostics)


def _diagnostic_from_error(
    path: Path,
    text: str,
    error: Exception,
) -> Diagnostic:
    message = str(error)
    line_number, column, source_line = _locate_error(text, message)
    return Diagnostic(
        path,
        line_number,
        column,
        DiagnosticSeverity.ERROR,
        "SNK100",
        message,
        source_line,
    )


def _reference_diagnostic(
    path: Path,
    text: str,
    kind: str,
    name: str,
    severity: DiagnosticSeverity,
) -> Diagnostic:
    line_number, column, source_line = _locate_reference(text, name)
    code = "SNK201" if kind == "group" else "SNK202"
    return Diagnostic(
        path,
        line_number,
        column,
        severity,
        code,
        f"program {kind} {name!r} was not found in the selected sources",
        source_line,
        help=(
            "include its declaration in the checked paths or omit "
            "--strict-links when it is supplied by Python"
        ),
    )


def _locate_error(text: str, message: str) -> tuple[int, int, str]:
    lines = text.splitlines()
    significant = [
        (number, line, line.strip())
        for number, line in enumerate(lines, start=1)
        if line.strip() and not line.lstrip().startswith("#")
    ]
    quoted = _QUOTED_RE.search(message)
    if quoted is not None:
        try:
            value = ast.literal_eval(quoted.group("value"))
        except (SyntaxError, ValueError):
            value = ""
        for number, raw, stripped in significant:
            if stripped == value:
                return number, _first_column(raw), raw

    variables = tuple(dict.fromkeys(_VARIABLE_RE.findall(message)))
    if variables:
        ranked = [
            item
            for item in significant
            if all(variable in item[2] for variable in variables)
        ]
        if ranked:
            number, raw, _ = ranked[0]
            position = raw.find(variables[0])
            return number, position + 1 if position >= 0 else _first_column(raw), raw

    named = re.search(
        r"\b(rule|group|constraint|program|step)\s+(['\"])(?P<name>.+?)\2",
        message,
    )
    if named is not None:
        keyword = named.group(1).upper()
        if keyword == "CONSTRAINT":
            keyword = "CONSTRAINT"
        expected = f"{keyword} {named.group('name')}"
        for number, raw, stripped in significant:
            if stripped == expected:
                return number, _first_column(raw), raw

    if significant:
        number, raw, _ = significant[-1] if "missing" in message else significant[0]
        return number, _first_column(raw), raw
    return 1, 1, ""


def _locate_reference(text: str, name: str) -> tuple[int, int, str]:
    for line_number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.endswith(f" {name}"):
            position = raw.rfind(name)
            return line_number, position + 1, raw
    return 1, 1, ""


def _first_significant_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _first_column(line: str) -> int:
    return len(line) - len(line.lstrip()) + 1


__all__ = [
    "DEFAULT_EXCLUDED_DIRECTORIES",
    "SUPPORTED_SUFFIXES",
    "Diagnostic",
    "DiagnosticSeverity",
    "ValidationResult",
    "discover_source_files",
    "format_source",
    "validate_paths",
    "validate_source",
]
