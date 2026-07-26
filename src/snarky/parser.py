"""Parser for the deliberately small initial rule DSL."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .choice_fixed_point import SessionPropagator
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
from .premises import Premise
from .programs import RuleProgram, RuleStep
from .rules import Rule, RuleGroup


def parse_rules(
    text: str,
    *,
    predicates: PredicateRegistry | None = None,
) -> tuple[Rule, ...]:
    """Parse one or more ``RULE ... END`` definitions."""

    return _parse_rule_lines(_normalized_lines(text), predicates)


def parse_premises(
    text: str,
    *,
    predicates: PredicateRegistry | None = None,
) -> tuple[Premise, ...]:
    """Parse a standalone conjunction using the rule ``WHEN`` syntax."""

    lines = _normalized_lines(text)
    premises, position = _parse_premise_block(
        lines,
        0,
        "<END_OF_INPUT>",
        predicates,
    )
    if position != len(lines):
        raise ParseError(f"unexpected premise input {lines[position]!r}")
    return tuple(premises)


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


def parse_rule_program(
    text: str,
    groups: Sequence[RuleGroup],
    *,
    constraints: Mapping[str, SessionPropagator] | None = None,
) -> RuleProgram:
    """Parse an inspectable orchestration manifest.

    The manifest references rule groups parsed from ordinary ``.rules`` files.
    Persistent propagators may be referenced by name when supplied through
    ``constraints``.
    """

    lines = _normalized_lines(text)
    if not lines:
        raise ParseError("a rule program cannot be empty")
    header = lines[0].split(maxsplit=1)
    if len(header) != 2 or header[0] != "PROGRAM":
        raise ParseError("a rule program must start with PROGRAM <name>")
    if lines[-1] != "END_PROGRAM":
        raise ParseError(f"program {header[1]!r} is missing END_PROGRAM")

    group_catalogue = tuple(groups)
    available_groups = {group.name: group for group in group_catalogue}
    if len(available_groups) != len(group_catalogue):
        raise ParseError("program group catalogue contains duplicate names")
    available_constraints = dict(constraints or {})
    preparation: list[RuleGroup] = []
    choices: list[RuleGroup] = []
    propagation: list[RuleGroup] = []
    interpretation: list[RuleGroup] = []
    steps: list[RuleStep] = []
    position = 1
    while position < len(lines) - 1:
        line = lines[position]
        if line.startswith("PREPARE "):
            preparation.append(
                _program_group(line.removeprefix("PREPARE "), available_groups)
            )
            position += 1
            continue
        if line.startswith("CHOOSE "):
            choices.append(
                _program_group(line.removeprefix("CHOOSE "), available_groups)
            )
            position += 1
            continue
        if line.startswith("PROPAGATE "):
            propagation.append(
                _program_group(line.removeprefix("PROPAGATE "), available_groups)
            )
            position += 1
            continue
        if line.startswith("INTERPRET "):
            interpretation.append(
                _program_group(line.removeprefix("INTERPRET "), available_groups)
            )
            position += 1
            continue
        if not line.startswith("STEP "):
            raise ParseError(f"unexpected program directive {line!r}")
        step_name = line.removeprefix("STEP ").strip()
        if not step_name:
            raise ParseError("STEP requires a name")
        position += 1
        step_groups: list[RuleGroup] = []
        constraint_names: list[str] = []
        propagators: list[SessionPropagator] = []
        while position < len(lines) - 1 and lines[position] != "END_STEP":
            directive = lines[position]
            if directive.startswith("GROUP "):
                step_groups.append(
                    _program_group(
                        directive.removeprefix("GROUP "),
                        available_groups,
                    )
                )
            elif directive.startswith("CONSTRAINT "):
                constraint_name = directive.removeprefix("CONSTRAINT ").strip()
                if constraint_name not in available_constraints:
                    raise ParseError(
                        f"unknown program constraint {constraint_name!r}"
                    )
                constraint_names.append(constraint_name)
                propagators.append(available_constraints[constraint_name])
            else:
                raise ParseError(
                    f"unexpected STEP directive {directive!r}"
                )
            position += 1
        if position >= len(lines) - 1:
            raise ParseError(f"step {step_name!r} is missing END_STEP")
        position += 1
        try:
            steps.append(
                RuleStep(
                    step_name,
                    tuple(step_groups),
                    tuple(constraint_names),
                    tuple(propagators),
                )
            )
        except ValueError as error:
            raise ParseError(str(error)) from error

    try:
        return RuleProgram(
            name=header[1],
            preparation_groups=tuple(preparation),
            choice_groups=tuple(choices),
            propagation_groups=tuple(propagation),
            interpretation_groups=tuple(interpretation),
            steps=tuple(steps),
        )
    except ValueError as error:
        raise ParseError(str(error)) from error


def _program_group(
    name: str,
    groups: Mapping[str, RuleGroup],
) -> RuleGroup:
    normalized = name.strip()
    try:
        return groups[normalized]
    except KeyError as error:
        raise ParseError(f"unknown program group {normalized!r}") from error


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
