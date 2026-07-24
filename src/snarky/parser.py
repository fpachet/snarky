"""Parser for the deliberately small initial rule DSL."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .actions import Action, AddFact, Fresh, Let, RemoveFact
from .expressions import (
    BinaryArithmeticExpression,
    BinaryArithmeticOperator,
    NumericExpression,
    UnaryArithmeticExpression,
    UnaryArithmeticOperator,
)
from .premises import (
    CollectPremise,
    ComparisonOperator,
    ComparisonPremise,
    CountPremise,
    ExistsPremise,
    FactPremise,
    NotExistsPremise,
    Premise,
    UniquePremise,
)
from .rules import Rule, RuleGroup
from .terms import Atom, FiniteSet, Number, Status, Term, Triple, Variable


class ParseError(ValueError):
    """Raised when text does not conform to the supported DSL."""


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str


_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<LPAREN>\()|(?P<RPAREN>\))|"
    r"(?P<LBRACKET>\[)|(?P<RBRACKET>\])|"
    r"(?P<OP>==|!=|<=|>=|<|>)|(?P<QUOTE>')|"
    r"(?P<VARIABLE>\$[^\s()\[\]'<>!=]+)|"
    r"(?P<NUMBER>-?(?:\d+(?:\.\d*)?|\.\d+))|"
    r"(?P<ATOM>[^\s()\[\]'<>!=]+)"
    r")"
)
_COMPARISONS = {operator.value: operator for operator in ComparisonOperator}
_STATUSES = {status.value: status for status in Status}
_LET_RE = re.compile(
    r"LET\s+(?P<variable>\$[^\s()'<>!=:+*/%-]+)\s*:=\s*(?P<expression>.+)\Z"
)
_FRESH_RE = re.compile(
    r"FRESH\s+(?P<variable>\$[^\s()'<>!=:+*/%-]+)"
    r"(?:\s+PREFIX\s+(?P<prefix>[^\s()\[\]'<>!=]+))?\Z"
)
_DIVISIBLE_RE = re.compile(
    r"DIVISIBLE\s+(?P<left>.+?)\s+BY\s+(?P<right>.+)\Z"
)
_COLLECT_RE = re.compile(
    r"COLLECT\s+(?P<target>\$[^\s()'<>!=:+*/%-]+)"
    r"\s*:=\s*(?P<projection>.+)\Z"
)
_ARITH_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<LPAREN>\()|(?P<RPAREN>\))|(?P<OP>[+*/%-])|"
    r"(?P<VARIABLE>\$[^\s()+*/%-]+)|"
    r"(?P<NUMBER>(?:\d+(?:\.\d*)?|\.\d+))"
    r")"
)


def parse_term(text: str) -> Term:
    """Parse exactly one recursive term without using ``eval``."""

    tokens = _tokenize(text)
    term, position = _parse_term_tokens(tokens, 0)
    if position != len(tokens):
        raise ParseError(f"unexpected token {tokens[position].value!r}")
    return term


def parse_rules(text: str) -> tuple[Rule, ...]:
    """Parse one or more ``RULE ... END`` definitions."""

    return _parse_rule_lines(_normalized_lines(text))


def parse_rule_groups(text: str) -> tuple[RuleGroup, ...]:
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
            groups.append(RuleGroup(name, _parse_rule_lines(tuple(body))))
        except ValueError as error:
            raise ParseError(str(error)) from error
    return tuple(groups)


def _normalized_lines(text: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def _parse_rule_lines(lines: tuple[str, ...]) -> tuple[Rule, ...]:
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

        premises, position = _parse_premise_block(lines, position, "THEN")
        if position >= len(lines) or lines[position] != "THEN":
            raise ParseError(f"rule {name!r} is missing THEN")
        position += 1

        actions: list[Action] = []
        while position < len(lines) and lines[position] != "END":
            actions.append(_parse_action(lines[position]))
            position += 1
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


def _parse_premise_block(
    lines: tuple[str, ...],
    position: int,
    terminator: str,
) -> tuple[list[Premise], int]:
    premises: list[Premise] = []
    while position < len(lines) and lines[position] != terminator:
        keyword = lines[position]
        if keyword in {"EXISTS", "NOT EXISTS"}:
            nested, position = _parse_premise_block(
                lines,
                position + 1,
                "END_EXISTS",
            )
            if position >= len(lines) or lines[position] != "END_EXISTS":
                raise ParseError(f"{keyword} block is missing END_EXISTS")
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
            "END_COUNT",
            "END_UNIQUE",
            "END_COLLECT",
        }:
            raise ParseError(f"unexpected {keyword} before {terminator}")
        if (
            terminator
            in {"END_EXISTS", "END_COUNT", "END_UNIQUE", "END_COLLECT"}
            and keyword in {"THEN", "END"}
        ):
            raise ParseError(f"block is missing {terminator}")
        premises.append(_parse_premise(keyword))
        position += 1
    return premises, position


def _parse_premise(text: str) -> Premise:
    divisible = _DIVISIBLE_RE.fullmatch(text)
    if divisible is not None:
        return ComparisonPremise(
            parse_term(divisible.group("left")),
            ComparisonOperator.DIVISIBLE,
            parse_term(divisible.group("right")),
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


def parse_arithmetic_expression(text: str) -> NumericExpression:
    """Parse one safe arithmetic expression with standard precedence."""

    tokens = _tokenize_arithmetic(text)
    expression, position = _parse_arithmetic_sum(tokens, 0)
    if position != len(tokens):
        raise ParseError(f"unexpected token {tokens[position].value!r}")
    return expression


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
    tokens = _tokenize(body)
    split = _top_level_operator(tokens)
    if split is None:
        entity = _parse_all(tokens)
        return AddFact(entity) if keyword == "ADD" else RemoveFact(entity)
    index, operator = split
    if operator != "'":
        raise ParseError(
            f"{keyword} only accepts an optional status after apostrophe"
        )
    entity = _parse_all(tokens[:index])
    status = _parse_all(tokens[index + 1 :])
    return (
        AddFact(entity, status)
        if keyword == "ADD"
        else RemoveFact(entity, status)
    )


def _tokenize_arithmetic(text: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    position = 0
    while position < len(text):
        if not text[position:].strip():
            break
        match = _ARITH_TOKEN_RE.match(text, position)
        if match is None:
            raise ParseError(f"invalid arithmetic token near {text[position:]!r}")
        kind = match.lastgroup
        if kind is None:
            raise ParseError(f"invalid arithmetic token near {text[position:]!r}")
        tokens.append(_Token(kind, match.group(kind)))
        position = match.end()
    if not tokens:
        raise ParseError("expected an arithmetic expression")
    return tuple(tokens)


def _parse_arithmetic_sum(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    left, position = _parse_arithmetic_product(tokens, position)
    while position < len(tokens) and tokens[position].value in {"+", "-"}:
        operator = BinaryArithmeticOperator(tokens[position].value)
        right, position = _parse_arithmetic_product(tokens, position + 1)
        left = BinaryArithmeticExpression(left, operator, right)
    return left, position


def _parse_arithmetic_product(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    left, position = _parse_arithmetic_unary(tokens, position)
    while position < len(tokens) and tokens[position].value in {"*", "/", "%"}:
        operator = BinaryArithmeticOperator(tokens[position].value)
        right, position = _parse_arithmetic_unary(tokens, position + 1)
        left = BinaryArithmeticExpression(left, operator, right)
    return left, position


def _parse_arithmetic_unary(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    if position < len(tokens) and tokens[position].value in {"+", "-"}:
        operator = UnaryArithmeticOperator(tokens[position].value)
        operand, position = _parse_arithmetic_unary(tokens, position + 1)
        return UnaryArithmeticExpression(operator, operand), position
    return _parse_arithmetic_primary(tokens, position)


def _parse_arithmetic_primary(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[NumericExpression, int]:
    if position >= len(tokens):
        raise ParseError("expected an arithmetic operand")
    token = tokens[position]
    if token.kind == "NUMBER":
        value = float(token.value) if "." in token.value else int(token.value)
        return Number(value), position + 1
    if token.kind == "VARIABLE":
        return Variable(token.value[1:]), position + 1
    if token.kind == "LPAREN":
        expression, position = _parse_arithmetic_sum(tokens, position + 1)
        if position >= len(tokens) or tokens[position].kind != "RPAREN":
            raise ParseError("unclosed arithmetic parenthesis")
        return expression, position + 1
    raise ParseError(f"expected an arithmetic operand, got {token.value!r}")


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
    if token.kind == "LBRACKET":
        elements: list[Term] = []
        position += 1
        while position < len(tokens) and tokens[position].kind != "RBRACKET":
            element, position = _parse_term_tokens(tokens, position)
            elements.append(element)
        if position >= len(tokens):
            raise ParseError("unclosed finite set")
        return FiniteSet(tuple(elements)), position + 1
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
