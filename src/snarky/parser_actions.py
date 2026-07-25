"""Action parsing for the Snarky rule language."""

from __future__ import annotations

import re

from .actions import (
    Action,
    AddFact,
    Choice,
    ForEach,
    Fresh,
    Let,
    RemoveFact,
)
from .computed import PredicateRegistry
from .parser_arithmetic import parse_arithmetic_expression
from .parser_lexer import ParseError, _tokenize
from .parser_premises import _parse_premise_block, _top_level_operator
from .parser_terms import _parse_all, parse_term
from .terms import Status, Term, Variable

_LET_RE = re.compile(
    r"LET\s+(?P<variable>\$[^\s()'<>!=:+*/%-]+)\s*:=\s*(?P<expression>.+)\Z"
)
_FRESH_RE = re.compile(
    r"FRESH\s+(?P<variable>\$[^\s()'<>!=:+*/%-]+)"
    r"(?:\s+PREFIX\s+(?P<prefix>[^\s()\[\]'<>!=]+))?\Z"
)
_FOR_EACH_RE = re.compile(
    r"FOR EACH\s+(?P<variable>\$[^\s()'<>!=:+*/%-]+)"
    r"\s+IN\s+(?P<collection>.+)\Z"
)


def _parse_action_block(
    lines: tuple[str, ...],
    position: int,
    terminator: str,
    predicates: PredicateRegistry | None,
) -> tuple[list[Action], int]:
    actions: list[Action] = []
    while position < len(lines) and lines[position] != terminator:
        line = lines[position]
        if line.startswith("FOR EACH "):
            match = _FOR_EACH_RE.fullmatch(line)
            if match is None:
                raise ParseError(
                    "FOR EACH must be `FOR EACH $item IN collection`"
                )
            nested, position = _parse_action_block(
                lines,
                position + 1,
                "END_FOR_EACH",
                predicates,
            )
            if position >= len(lines):
                raise ParseError("FOR EACH block is missing END_FOR_EACH")
            try:
                actions.append(
                    ForEach(
                        Variable(match.group("variable")[1:]),
                        parse_term(match.group("collection")),
                        tuple(nested),
                    )
                )
            except ValueError as error:
                raise ParseError(str(error)) from error
            position += 1
            continue
        if line.startswith("CHOICE "):
            choice, position = _parse_choice_block(
                lines,
                position,
                predicates,
            )
            actions.append(choice)
            continue
        if line in {"END_FOR_EACH", "END_CHOICE"}:
            raise ParseError(f"unexpected {line} before {terminator}")
        actions.append(_parse_action(line))
        position += 1
    return actions, position


def _parse_choice_block(
    lines: tuple[str, ...],
    position: int,
    predicates: PredicateRegistry | None,
) -> tuple[Choice, int]:
    header = lines[position].removeprefix("CHOICE ").strip()
    target_text, separator, weight_text = header.rpartition(" WEIGHT ")
    if not separator:
        target_text = header
        weight_text = "1"
    if not target_text:
        raise ParseError("CHOICE requires a target fact")
    entity, status = _parse_fact_template(target_text, "CHOICE")
    if position + 1 >= len(lines) or lines[position + 1] != "FROM":
        raise ParseError("CHOICE target must be followed by FROM")
    premises, end = _parse_premise_block(
        lines,
        position + 2,
        "END_CHOICE",
        predicates,
    )
    if end >= len(lines) or lines[end] != "END_CHOICE":
        raise ParseError("CHOICE block is missing END_CHOICE")
    try:
        return (
            Choice(
                entity,
                tuple(premises),
                status,
                parse_term(weight_text),
            ),
            end + 1,
        )
    except ValueError as error:
        raise ParseError(str(error)) from error


def _parse_action(text: str) -> Action:
    if text.startswith("LET"):
        match = _LET_RE.fullmatch(text)
        if match is None:
            raise ParseError(f"malformed LET action {text!r}")
        variable = Variable(match.group("variable")[1:])
        expression = parse_arithmetic_expression(match.group("expression"))
        return Let(variable, expression)
    if text.startswith("FRESH"):
        match = _FRESH_RE.fullmatch(text)
        if match is None:
            raise ParseError(f"malformed FRESH action {text!r}")
        return Fresh(
            Variable(match.group("variable")[1:]),
            match.group("prefix") or "fresh",
        )
    keyword, separator, body = text.partition(" ")
    if keyword not in {"ADD", "REMOVE"} or not separator or not body.strip():
        raise ParseError(f"unsupported action {text!r}")
    entity, status = _parse_fact_template(body, keyword)
    return (
        AddFact(entity, status)
        if keyword == "ADD"
        else RemoveFact(entity, status)
    )


def _parse_fact_template(
    text: str,
    keyword: str,
) -> tuple[Term, Term]:
    tokens = _tokenize(text)
    split = _top_level_operator(tokens)
    if split is None:
        return _parse_all(tokens), Status.VRAI
    index, operator = split
    if operator != "'":
        raise ParseError(
            f"{keyword} only accepts an optional status after apostrophe"
        )
    entity = _parse_all(tokens[:index])
    status = _parse_all(tokens[index + 1 :])
    return entity, status
