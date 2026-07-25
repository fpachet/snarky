"""Parser for the deliberately small initial rule DSL."""

from __future__ import annotations

from .computed import PredicateRegistry
from .parser_actions import (
    _parse_action as _parse_action,
)
from .parser_actions import (
    _parse_action_block as _parse_action_block,
)
from .parser_actions import (
    _parse_choice_block as _parse_choice_block,
)
from .parser_actions import (
    _parse_fact_template as _parse_fact_template,
)
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
from .parser_lexer import _normalized_lines
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
    _top_level_operator as _top_level_operator,
)
from .parser_terms import (
    _parse_all as _parse_all,
)
from .parser_terms import (
    _parse_term_tokens as _parse_term_tokens,
)
from .parser_terms import (
    parse_term as parse_term,
)
from .rules import Rule, RuleGroup


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
