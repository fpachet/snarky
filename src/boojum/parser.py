"""Parser for the deliberately small initial rule DSL."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .actions import AddFact
from .premises import ComparisonOperator, ComparisonPremise, FactPremise, Premise
from .rules import Rule
from .terms import Atom, Number, Status, Term, Triple, Variable


class ParseError(ValueError):
    """Raised when text does not conform to the supported DSL."""


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str


_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<LPAREN>\()|(?P<RPAREN>\))|"
    r"(?P<OP>==|!=|<=|>=|<|>)|(?P<QUOTE>')|"
    r"(?P<VARIABLE>\$[^\s()'<>!=]+)|"
    r"(?P<NUMBER>-?(?:\d+(?:\.\d*)?|\.\d+))|"
    r"(?P<ATOM>[^\s()'<>!=]+)"
    r")"
)
_COMPARISONS = {operator.value: operator for operator in ComparisonOperator}
_STATUSES = {status.value: status for status in Status}


def parse_term(text: str) -> Term:
    """Parse exactly one recursive term without using ``eval``."""

    tokens = _tokenize(text)
    term, position = _parse_term_tokens(tokens, 0)
    if position != len(tokens):
        raise ParseError(f"unexpected token {tokens[position].value!r}")
    return term


def parse_rules(text: str) -> tuple[Rule, ...]:
    """Parse one or more ``RULE ... END`` definitions."""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
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

        premises: list[Premise] = []
        while position < len(lines) and lines[position] != "THEN":
            premises.append(_parse_premise(lines[position]))
            position += 1
        if position >= len(lines):
            raise ParseError(f"rule {name!r} is missing THEN")
        position += 1

        actions: list[AddFact] = []
        while position < len(lines) and lines[position] != "END":
            actions.append(_parse_action(lines[position]))
            position += 1
        if position >= len(lines):
            raise ParseError(f"rule {name!r} is missing END")
        position += 1
        if any(rule.name == name for rule in rules):
            raise ParseError(f"duplicate rule name {name!r}")
        rules.append(Rule(name, tuple(premises), tuple(actions)))
    return tuple(rules)


def _parse_premise(text: str) -> Premise:
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


def _parse_action(text: str) -> AddFact:
    keyword, separator, body = text.partition(" ")
    if keyword != "ADD" or not separator or not body.strip():
        raise ParseError(f"unsupported action {text!r}")
    tokens = _tokenize(body)
    split = _top_level_operator(tokens)
    if split is None:
        return AddFact(_parse_all(tokens))
    index, operator = split
    if operator != "'":
        raise ParseError("ADD only accepts an optional status after apostrophe")
    return AddFact(_parse_all(tokens[:index]), _parse_all(tokens[index + 1 :]))


def _tokenize(text: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    position = 0
    while position < len(text):
        if not text[position:].strip():
            break
        match = _TOKEN_RE.match(text, position)
        if match is None:
            raise ParseError(f"invalid token near {text[position:]!r}")
        kind = match.lastgroup
        if kind is None:
            raise ParseError(f"invalid token near {text[position:]!r}")
        tokens.append(_Token(kind, match.group(kind)))
        position = match.end()
    if not tokens:
        raise ParseError("expected a term")
    return tuple(tokens)


def _parse_all(tokens: tuple[_Token, ...]) -> Term:
    term, position = _parse_term_tokens(tokens, 0)
    if position != len(tokens):
        raise ParseError(f"unexpected token {tokens[position].value!r}")
    return term


def _parse_term_tokens(tokens: tuple[_Token, ...], position: int) -> tuple[Term, int]:
    if position >= len(tokens):
        raise ParseError("expected a term")
    token = tokens[position]
    if token.kind == "LPAREN":
        subject, position = _parse_term_tokens(tokens, position + 1)
        relation, position = _parse_term_tokens(tokens, position)
        object_, position = _parse_term_tokens(tokens, position)
        if position >= len(tokens) or tokens[position].kind != "RPAREN":
            raise ParseError("a triple must contain exactly three terms")
        return Triple(subject, relation, object_), position + 1
    if token.kind == "VARIABLE":
        return Variable(token.value[1:]), position + 1
    if token.kind == "NUMBER":
        value = float(token.value) if "." in token.value else int(token.value)
        return Number(value), position + 1
    if token.kind == "ATOM":
        return _STATUSES.get(token.value, Atom(token.value)), position + 1
    raise ParseError(f"expected a term, got {token.value!r}")


def _top_level_operator(tokens: tuple[_Token, ...]) -> tuple[int, str] | None:
    depth = 0
    found: tuple[int, str] | None = None
    for index, token in enumerate(tokens):
        if token.kind == "LPAREN":
            depth += 1
        elif token.kind == "RPAREN":
            depth -= 1
            if depth < 0:
                raise ParseError("unexpected closing parenthesis")
        elif depth == 0 and token.kind in {"OP", "QUOTE"}:
            if found is not None:
                raise ParseError("a premise may contain only one top-level operator")
            found = index, token.value
    if depth != 0:
        raise ParseError("unclosed parenthesis")
    return found
