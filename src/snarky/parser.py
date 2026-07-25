"""Parser for the deliberately small initial rule DSL."""

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
from .parser_arithmetic import (
    _parse_arithmetic_primary as _parse_arithmetic_primary,
)
from .parser_arithmetic import (
    _parse_arithmetic_product as _parse_arithmetic_product,
)
from .parser_arithmetic import (
    _parse_arithmetic_sum as _parse_arithmetic_sum,
)
from .parser_arithmetic import (
    _parse_arithmetic_unary as _parse_arithmetic_unary,
)
from .parser_arithmetic import (
    parse_arithmetic_expression as parse_arithmetic_expression,
)
from .parser_lexer import ParseError as ParseError
from .parser_lexer import (
    _normalized_lines,
    _tokenize,
)
from .parser_premises import (
    _parse_compact_existential as _parse_compact_existential,
)
from .parser_premises import (
    _parse_computed_call as _parse_computed_call,
)
from .parser_premises import (
    _parse_premise as _parse_premise,
)
from .parser_premises import (
    _parse_premise_block as _parse_premise_block,
)
from .parser_premises import (
    _parse_window as _parse_window,
)
from .parser_premises import (
    _top_level_operator,
)
from .parser_terms import (
    _parse_all,
)
from .parser_terms import (
    _parse_term_tokens as _parse_term_tokens,
)
from .parser_terms import (
    parse_term as parse_term,
)
from .rules import Rule, RuleGroup
from .terms import (
    Status,
    Term,
    Variable,
)

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


def parse_rules(
    text: str,
    *,
    predicates: PredicateRegistry | None = None,
) -> tuple[Rule, ...]:
    """Parse one or more ``RULE ... END`` definitions."""

    return _parse_rule_lines(_normalized_lines(text), predicates)


def parse_rule_groups(
    text: str,
    *,
    predicates: PredicateRegistry | None = None,
) -> tuple[RuleGroup, ...]:
    """Parse named ``GROUP ... END_GROUP`` blocks containing rules."""

    lines = _normalized_lines(text)
    groups: list[RuleGroup] = []
    position = 0
    while position < len(lines):
        header = lines[position].split(maxsplit=1)
        if len(header) != 2 or header[0] != "GROUP":
            raise ParseError(f"expected GROUP header, got {lines[position]!r}")
        name = header[1]
        position += 1
        body: list[str] = []
        while position < len(lines) and lines[position] != "END_GROUP":
            if lines[position].startswith("GROUP "):
                raise ParseError(f"group {name!r} contains a nested GROUP")
            body.append(lines[position])
            position += 1
        if position >= len(lines):
            raise ParseError(f"group {name!r} is missing END_GROUP")
        position += 1
        if any(group.name == name for group in groups):
            raise ParseError(f"duplicate group name {name!r}")
        try:
            groups.append(
                RuleGroup(
                    name,
                    _parse_rule_lines(tuple(body), predicates),
                )
            )
        except ValueError as error:
            raise ParseError(str(error)) from error
    return tuple(groups)


def _parse_rule_lines(
    lines: tuple[str, ...],
    predicates: PredicateRegistry | None,
) -> tuple[Rule, ...]:
    rules: list[Rule] = []
    position = 0
    while position < len(lines):
        header = lines[position].split(maxsplit=1)
        if len(header) != 2 or header[0] != "RULE":
            raise ParseError(f"expected RULE header, got {lines[position]!r}")
        name = header[1]
        position += 1
        if position >= len(lines) or lines[position] != "WHEN":
            raise ParseError(f"rule {name!r} is missing WHEN")
        position += 1

        premises, position = _parse_premise_block(
            lines,
            position,
            "THEN",
            predicates,
        )
        if position >= len(lines) or lines[position] != "THEN":
            raise ParseError(f"rule {name!r} is missing THEN")
        position += 1

        actions, position = _parse_action_block(
            lines,
            position,
            "END",
            predicates,
        )
        if position >= len(lines):
            raise ParseError(f"rule {name!r} is missing END")
        position += 1
        if any(rule.name == name for rule in rules):
            raise ParseError(f"duplicate rule name {name!r}")
        try:
            rules.append(Rule(name, tuple(premises), tuple(actions)))
        except ValueError as error:
            raise ParseError(str(error)) from error
    return tuple(rules)


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
