"""Premise parsing for the Snarky rule language."""

from __future__ import annotations

import re

from .computed import ComputedPredicate, ComputedPremise, PredicateRegistry
from .expressions import DistinctCountExpression
from .parser_arithmetic import parse_arithmetic_expression
from .parser_lexer import ParseError, _Token, _tokenize
from .parser_terms import _parse_all, parse_term
from .premises import (
    BindPremise,
    CollectPremise,
    CombinationsPremise,
    ComparisonOperator,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
    focus,
)
from .terms import (
    FiniteSequence,
    Number,
    Term,
    Triple,
    Variable,
)

_COMPARISONS = {operator.value: operator for operator in ComparisonOperator}
_DIVISIBLE_RE = re.compile(
    r"DIVISIBLE\s+(?P<left>.+?)\s+BY\s+(?P<right>.+)\Z"
)
_CONSTRAINT_RE = re.compile(
    r"CONSTRAINT\s+(?P<left>.+?)\s*"
    r"(?P<operator>==|!=|<=|>=|<|>)\s*"
    r"(?P<right>.+)\Z"
)
_ALL_DIFFERENT_RE = re.compile(
    r"ALL_DIFFERENT\s+(?P<values>SEQ\[.*\])\Z"
)
_NVALUE_RE = re.compile(
    r"NVALUE\s+(?P<count>\$[^\s()\[\]'<>!=]+|-?\d+)"
    r"\s+OF\s+(?P<values>SEQ\[.*\])\Z"
)
_COLLECT_RE = re.compile(
    r"COLLECT\s+(?P<target>\$[^\s()'<>!=:+*/%-]+)"
    r"\s*:=\s*(?P<projection>.+)\Z"
)
_BIND_RE = re.compile(
    r"BIND\s+(?P<target>\$[^\s()'<>!=:+*/%-]+)"
    r"\s*:=\s*(?P<value>.+)\Z"
)
_WINDOW_RE = re.compile(
    r"WINDOW\s+(?P<target>\$[^\s()'<>!=:+*/%-]+)"
    r"\s*:=\s*(?P<sequence>SEQ\[.*\])"
    r"\s+VIA\s+(?P<relation>.+)\Z"
)
_COMBINATIONS_RE = re.compile(
    r"COMBINATIONS\s+(?P<target>\$[^\s()'<>!=:+*/%-]+)"
    r"\s+SIZE\s+(?P<size>\d+)\s+FROM\s+(?P<source>.+)\Z"
)
_COMPUTE_RE = re.compile(
    r"COMPUTE\s+(?P<target>\$[^\s()'<>!=:+*/%-]+)"
    r"\s*:=\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"\s+ARGS\s+(?P<arguments>SEQ\[.*\])\Z"
)
_CHECK_RE = re.compile(
    r"CHECK\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"\s+ARGS\s+(?P<arguments>SEQ\[.*\])\Z"
)


def _parse_premise_block(
    lines: tuple[str, ...],
    position: int,
    terminator: str | tuple[str, ...],
    predicates: PredicateRegistry | None,
) -> tuple[list[Premise], int]:
    terminators = (
        (terminator,) if isinstance(terminator, str) else terminator
    )
    premises: list[Premise] = []
    while position < len(lines) and lines[position] not in terminators:
        keyword = lines[position]
        if keyword.startswith("WINDOW "):
            premises.extend(_parse_window(keyword))
            position += 1
            continue
        compact_existential = _parse_compact_existential(
            keyword,
            predicates,
        )
        if compact_existential is not None:
            premises.append(compact_existential)
            position += 1
            continue
        if keyword in {"EXISTS", "NOT EXISTS"}:
            nested_terminators = (
                ("END_EXISTS", "END_NOT_EXISTS")
                if keyword == "NOT EXISTS"
                else ("END_EXISTS",)
            )
            nested, position = _parse_premise_block(
                lines,
                position + 1,
                nested_terminators,
                predicates,
            )
            if (
                position >= len(lines)
                or lines[position] not in nested_terminators
            ):
                expected = (
                    "END_NOT_EXISTS"
                    if keyword == "NOT EXISTS"
                    else "END_EXISTS"
                )
                raise ParseError(f"{keyword} block is missing {expected}")
            position += 1
            try:
                premise = (
                    ExistsPremise(tuple(nested))
                    if keyword == "EXISTS"
                    else NotExistsPremise(tuple(nested))
                )
            except ValueError as error:
                raise ParseError(str(error)) from error
            premises.append(premise)
            continue
        if keyword.startswith("COUNT "):
            parts = keyword.split()
            if (
                len(parts) != 3
                or parts[1] not in _COMPARISONS
                or not parts[2].isdigit()
            ):
                raise ParseError(
                    "COUNT header must be `COUNT <operator> <integer>`"
                )
            nested, position = _parse_premise_block(
                lines,
                position + 1,
                "END_COUNT",
                predicates,
            )
            if position >= len(lines) or lines[position] != "END_COUNT":
                raise ParseError("COUNT block is missing END_COUNT")
            position += 1
            try:
                premises.append(
                    CountPremise(
                        tuple(nested),
                        _COMPARISONS[parts[1]],
                        int(parts[2]),
                    )
                )
            except ValueError as error:
                raise ParseError(str(error)) from error
            continue
        if keyword == "UNIQUE":
            nested, position = _parse_premise_block(
                lines,
                position + 1,
                "END_UNIQUE",
                predicates,
            )
            if position >= len(lines) or lines[position] != "END_UNIQUE":
                raise ParseError("UNIQUE block is missing END_UNIQUE")
            position += 1
            try:
                premises.append(UniquePremise(tuple(nested)))
            except ValueError as error:
                raise ParseError(str(error)) from error
            continue
        if keyword.startswith("COLLECT "):
            match = _COLLECT_RE.fullmatch(keyword)
            if match is None:
                raise ParseError(
                    "COLLECT header must be `COLLECT $target := projection`"
                )
            nested, position = _parse_premise_block(
                lines,
                position + 1,
                "END_COLLECT",
                predicates,
            )
            if position >= len(lines) or lines[position] != "END_COLLECT":
                raise ParseError("COLLECT block is missing END_COLLECT")
            position += 1
            try:
                premises.append(
                    CollectPremise(
                        Variable(match.group("target")[1:]),
                        parse_term(match.group("projection")),
                        tuple(nested),
                    )
                )
            except ValueError as error:
                raise ParseError(str(error)) from error
            continue
        if keyword in {
            "END_EXISTS",
            "END_NOT_EXISTS",
            "END_COUNT",
            "END_UNIQUE",
            "END_COLLECT",
            "END_CHOICE",
        }:
            raise ParseError(
                f"unexpected {keyword} before {' or '.join(terminators)}"
            )
        if (
            any(
                item
                in {
                    "END_EXISTS",
                    "END_NOT_EXISTS",
                    "END_COUNT",
                    "END_UNIQUE",
                    "END_COLLECT",
                    "END_CHOICE",
                }
                for item in terminators
            )
            and keyword in {"THEN", "END"}
        ):
            raise ParseError(
                f"block is missing {' or '.join(terminators)}"
            )
        premises.append(_parse_premise(keyword, predicates))
        position += 1
    return premises, position


def _parse_compact_existential(
    text: str,
    predicates: PredicateRegistry | None,
) -> Premise | None:
    for keyword, premise_type in (
        ("NOT EXISTS ", NotExistsPremise),
        ("EXISTS ", ExistsPremise),
    ):
        if not text.startswith(keyword):
            continue
        nested_text = text.removeprefix(keyword).strip()
        if not nested_text:
            return None
        try:
            return premise_type(
                (_parse_premise(nested_text, predicates),)
            )
        except ValueError as error:
            raise ParseError(str(error)) from error
    return None


def _parse_premise(
    text: str,
    predicates: PredicateRegistry | None = None,
) -> Premise:
    if text.startswith("FOCUS "):
        premise = _parse_premise(
            text.removeprefix("FOCUS ").strip(),
            predicates,
        )
        if not isinstance(premise, FactPremise):
            raise ParseError("FOCUS requires a factual premise")
        return focus(premise)
    bind_match = _BIND_RE.fullmatch(text)
    if bind_match is not None:
        return BindPremise(
            Variable(bind_match.group("target")[1:]),
            parse_term(bind_match.group("value")),
        )
    combinations_match = _COMBINATIONS_RE.fullmatch(text)
    if combinations_match is not None:
        return CombinationsPremise(
            Variable(combinations_match.group("target")[1:]),
            parse_term(combinations_match.group("source")),
            int(combinations_match.group("size")),
        )
    compute_match = _COMPUTE_RE.fullmatch(text)
    if compute_match is not None:
        predicate, arguments = _parse_computed_call(
            compute_match.group("name"),
            compute_match.group("arguments"),
            predicates,
        )
        return ComputedPremise(
            predicate,
            arguments,
            Variable(compute_match.group("target")[1:]),
        )
    check_match = _CHECK_RE.fullmatch(text)
    if check_match is not None:
        predicate, arguments = _parse_computed_call(
            check_match.group("name"),
            check_match.group("arguments"),
            predicates,
        )
        return ComputedPremise(predicate, arguments)
    divisible = _DIVISIBLE_RE.fullmatch(text)
    if divisible is not None:
        return ComparisonPremise(
            parse_term(divisible.group("left")),
            ComparisonOperator.DIVISIBLE,
            parse_term(divisible.group("right")),
        )
    all_different = _ALL_DIFFERENT_RE.fullmatch(text)
    if all_different is not None:
        values = parse_term(all_different.group("values"))
        if not isinstance(values, FiniteSequence) or not values.elements:
            raise ParseError("ALL_DIFFERENT requires a non-empty SEQ")
        return ComparisonPremise(
            DistinctCountExpression(values.elements),
            ComparisonOperator.EQ,
            Number(len(values.elements)),
        )
    nvalue = _NVALUE_RE.fullmatch(text)
    if nvalue is not None:
        values = parse_term(nvalue.group("values"))
        count = parse_term(nvalue.group("count"))
        if not isinstance(values, FiniteSequence) or not values.elements:
            raise ParseError("NVALUE requires a non-empty SEQ")
        if not isinstance(count, (Number, Variable)) or (
            isinstance(count, Number)
            and not isinstance(count.value, int)
        ):
            raise ParseError("NVALUE count must be an integer or variable")
        return ComparisonPremise(
            DistinctCountExpression(values.elements),
            ComparisonOperator.EQ,
            count,
        )
    if text.startswith("CONSTRAINT"):
        constraint = _CONSTRAINT_RE.fullmatch(text)
        if constraint is None:
            raise ParseError(f"malformed arithmetic constraint {text!r}")
        return ComparisonPremise(
            parse_arithmetic_expression(constraint.group("left")),
            _COMPARISONS[constraint.group("operator")],
            parse_arithmetic_expression(constraint.group("right")),
        )
    tokens = _tokenize(text)
    split = _top_level_operator(tokens)
    if split is None:
        return FactPremise(_parse_all(tokens))
    index, operator = split
    left = _parse_all(tokens[:index])
    right = _parse_all(tokens[index + 1 :])
    if operator == "'":
        return FactPremise(left, right)
    return ComparisonPremise(left, _COMPARISONS[operator], right)


def _parse_computed_call(
    name: str,
    arguments_text: str,
    predicates: PredicateRegistry | None,
) -> tuple[ComputedPredicate, tuple[Term, ...]]:
    if predicates is None:
        raise ParseError(
            f"computed predicate {name!r} requires a PredicateRegistry"
        )
    try:
        predicate = predicates.resolve(name)
    except KeyError as error:
        raise ParseError(str(error)) from error
    arguments = parse_term(arguments_text)
    if not isinstance(arguments, FiniteSequence):
        raise ParseError("computed predicate ARGS must be a SEQ[...]")
    return predicate, arguments.elements


def _parse_window(text: str) -> tuple[Premise, ...]:
    match = _WINDOW_RE.fullmatch(text)
    if match is None:
        raise ParseError(
            "WINDOW must be `WINDOW $target := SEQ[...] VIA relation`"
        )
    sequence = parse_term(match.group("sequence"))
    if not isinstance(sequence, FiniteSequence):
        raise ParseError("WINDOW requires an ordered SEQ[...] template")
    if len(sequence.elements) < 2:
        raise ParseError("WINDOW requires at least two sequence elements")
    relation = parse_term(match.group("relation"))
    links = tuple(
        FactPremise(Triple(left, relation, right))
        for left, right in zip(
            sequence.elements,
            sequence.elements[1:],
            strict=False,
        )
    )
    return (
        *links,
        BindPremise(
            Variable(match.group("target")[1:]),
            sequence,
        ),
    )


def _top_level_operator(tokens: tuple[_Token, ...]) -> tuple[int, str] | None:
    depth = 0
    bracket_depth = 0
    found: tuple[int, str] | None = None
    for index, token in enumerate(tokens):
        if token.kind == "LPAREN":
            depth += 1
        elif token.kind == "RPAREN":
            depth -= 1
            if depth < 0:
                raise ParseError("unexpected closing parenthesis")
        elif token.kind == "LBRACKET":
            bracket_depth += 1
        elif token.kind == "RBRACKET":
            bracket_depth -= 1
            if bracket_depth < 0:
                raise ParseError("unexpected closing bracket")
        elif (
            depth == 0
            and bracket_depth == 0
            and token.kind in {"OP", "QUOTE"}
        ):
            if found is not None:
                raise ParseError("a premise may contain only one top-level operator")
            found = index, token.value
    if depth != 0:
        raise ParseError("unclosed parenthesis")
    if bracket_depth != 0:
        raise ParseError("unclosed finite set")
    return found
