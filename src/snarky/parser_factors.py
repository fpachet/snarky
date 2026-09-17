"""Parser for the side-effect-free weighted factor DSL."""

from __future__ import annotations

from .computed import PredicateRegistry
from .factors import (
    FactorDefinition,
    FactorGroup,
    FactorParameter,
    WeightedFactor,
)
from .parser_lexer import ParseError, _normalized_lines
from .parser_premises import _parse_premise_block
from .parser_terms import parse_term


def parse_factors(
    text: str,
    *,
    predicates: PredicateRegistry | None = None,
) -> tuple[WeightedFactor, ...]:
    """Parse standalone ``FACTOR ... END_FACTOR`` definitions."""

    return _parse_factor_lines(_normalized_lines(text), predicates)


def parse_factor_groups(
    text: str,
    *,
    predicates: PredicateRegistry | None = None,
) -> tuple[FactorGroup, ...]:
    """Parse ``FACTOR_GROUP ... END_FACTOR_GROUP`` blocks."""

    lines = _normalized_lines(text)
    groups: list[FactorGroup] = []
    position = 0
    while position < len(lines):
        header = lines[position].split(maxsplit=1)
        if len(header) != 2 or header[0] != "FACTOR_GROUP":
            raise ParseError(f"expected FACTOR_GROUP header, got {lines[position]!r}")
        name = header[1]
        position += 1
        body: list[str] = []
        while position < len(lines) and lines[position] != "END_FACTOR_GROUP":
            if lines[position].startswith("FACTOR_GROUP "):
                raise ParseError(
                    f"factor group {name!r} contains a nested FACTOR_GROUP"
                )
            body.append(lines[position])
            position += 1
        if position >= len(lines):
            raise ParseError(f"factor group {name!r} is missing END_FACTOR_GROUP")
        position += 1
        if any(group.name == name for group in groups):
            raise ParseError(f"duplicate factor group name {name!r}")
        try:
            groups.append(
                FactorGroup(
                    name,
                    _parse_factor_lines(tuple(body), predicates),
                )
            )
        except ValueError as error:
            raise ParseError(str(error)) from error
    return tuple(groups)


def _parse_factor_lines(
    lines: tuple[str, ...],
    predicates: PredicateRegistry | None,
) -> tuple[WeightedFactor, ...]:
    factors: list[WeightedFactor] = []
    position = 0
    while position < len(lines):
        header = lines[position].split(maxsplit=1)
        if len(header) != 2 or header[0] != "FACTOR":
            raise ParseError(f"expected FACTOR header, got {lines[position]!r}")
        name = header[1]
        position += 1

        if position >= len(lines) or not lines[position].startswith("SCOPE "):
            raise ParseError(f"factor {name!r} is missing SCOPE")
        scope_text = lines[position].removeprefix("SCOPE ").strip()
        try:
            scope = parse_term(scope_text)
        except ParseError as error:
            raise ParseError(f"factor {name!r} has invalid SCOPE: {error}") from error
        position += 1

        if position >= len(lines) or not lines[position].startswith("LOG_WEIGHT "):
            raise ParseError(f"factor {name!r} is missing LOG_WEIGHT")
        weight_text = lines[position].removeprefix("LOG_WEIGHT ").strip()
        try:
            log_weight = float(weight_text)
        except ValueError as error:
            raise ParseError(
                f"factor {name!r} has invalid LOG_WEIGHT {weight_text!r}"
            ) from error
        position += 1

        if position >= len(lines) or lines[position] != "WHEN":
            raise ParseError(f"factor {name!r} is missing WHEN")
        position += 1
        premises, position = _parse_premise_block(
            lines,
            position,
            "END_FACTOR",
            predicates,
        )
        if position >= len(lines):
            raise ParseError(f"factor {name!r} is missing END_FACTOR")
        position += 1
        if any(item.name == name for item in factors):
            raise ParseError(f"duplicate factor name {name!r}")
        try:
            factors.append(
                WeightedFactor(
                    FactorDefinition(name, scope, tuple(premises)),
                    FactorParameter(name, log_weight),
                )
            )
        except ValueError as error:
            raise ParseError(str(error)) from error
    return tuple(factors)
