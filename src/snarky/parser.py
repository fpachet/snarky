"""Parser for the deliberately small initial rule DSL."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .actions import (
    Action,
    AddFact,
    Choice,
    ForEach,
    Fresh,
    Let,
    RemoveFact,
)
from .computed import ComputedPredicate, ComputedPremise, PredicateRegistry
from .expressions import (
    BinaryArithmeticExpression,
    BinaryArithmeticOperator,
    DistinctCountExpression,
    NumericExpression,
    UnaryArithmeticExpression,
    UnaryArithmeticOperator,
)
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
from .rules import Rule, RuleGroup
from .terms import (
    Atom,
    FiniteSequence,
    FiniteSet,
    Number,
    Status,
    Term,
    Triple,
    Variable,
)


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
_FOR_EACH_RE = re.compile(
    r"FOR EACH\s+(?P<variable>\$[^\s()'<>!=:+*/%-]+)"
    r"\s+IN\s+(?P<collection>.+)\Z"
)
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


def _normalized_lines(text: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


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
    if (
        token.kind == "ATOM"
        and token.value == "SEQ"
        and position + 1 < len(tokens)
        and tokens[position + 1].kind == "LBRACKET"
    ):
        elements = []
        position += 2
        while position < len(tokens) and tokens[position].kind != "RBRACKET":
            element, position = _parse_term_tokens(tokens, position)
            elements.append(element)
        if position >= len(tokens):
            raise ParseError("unclosed finite sequence")
        return FiniteSequence(tuple(elements)), position + 1
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
