"""Declarative syntax for persistent finite-domain constraint templates."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from snarky import (
    Atom,
    Fact,
    FiniteSequence,
    IndexedInstantiationStrategy,
    Number,
    ParseError,
    Rule,
    Term,
    Variable,
    add,
    parse_premises,
    parse_term,
    render_term,
    variables_in,
)
from snarky.premises import Premise, validate_premise_bindings

from .persistent_constraints import (
    AllDifferentConstraint,
    GlobalCardinalityConstraint,
    PersistentConstraint,
    SumConstraint,
    TableConstraint,
)

_SCOPE_RE = re.compile(
    r"SCOPE\s+(?P<projection>.+?)"
    r"(?:\s+ORDER\s+BY\s+(?P<order>.+))?\Z"
)
_BOUNDS_RE = re.compile(r"BOUNDS\s+(?P<projection>.+)\Z")


class PersistentConstraintKind(StrEnum):
    ALL_DIFFERENT = "ALL_DIFFERENT"
    GCC = "GCC"
    SUM = "SUM"
    TABLE = "TABLE"


@dataclass(frozen=True, slots=True)
class PersistentConstraintTemplate:
    """One fact-derived schema that grounds persistent constraints."""

    name: str
    kind: PersistentConstraintKind
    context: tuple[Premise, ...]
    context_key: tuple[Term, ...] | None
    scope_projection: Term
    scope_order: Term | None
    scope: tuple[Premise, ...]
    target: Term | None = None
    bounds_projection: Term | None = None
    bounds: tuple[Premise, ...] = ()
    tuples_projection: Term | None = None
    tuples: tuple[Premise, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a persistent constraint template needs a name")
        context = tuple(self.context)
        scope = tuple(self.scope)
        bounds = tuple(self.bounds)
        tuples = tuple(self.tuples)
        if not scope:
            raise ValueError("a persistent constraint scope cannot be empty")
        context_bound = validate_premise_bindings(context)
        if self.context_key is not None:
            missing_context = {
                variable
                for term in self.context_key
                for variable in variables_in(term)
            } - context_bound
            if missing_context:
                raise ValueError(
                    "FOR EACH key uses unbound variables: "
                    + _variable_names(missing_context)
                )
        scope_bound = validate_premise_bindings((*context, *scope))
        required = variables_in(self.scope_projection)
        if self.scope_order is not None:
            required |= variables_in(self.scope_order)
        missing = required - scope_bound
        if missing:
            raise ValueError(
                "constraint scope uses unbound variables: "
                + _variable_names(missing)
            )
        if self.kind is PersistentConstraintKind.SUM:
            if self.target is None:
                raise ValueError("SUM constraint template requires TARGET")
            missing_target = variables_in(self.target) - scope_bound
            if missing_target:
                raise ValueError(
                    "SUM target uses unbound variables: "
                    + _variable_names(missing_target)
                )
        elif self.target is not None:
            raise ValueError(f"{self.kind} does not accept TARGET")
        if self.kind is PersistentConstraintKind.GCC:
            if self.bounds_projection is None or not bounds:
                raise ValueError("GCC constraint template requires BOUNDS")
            bounds_bound = validate_premise_bindings((*context, *bounds))
            missing_bounds = (
                variables_in(self.bounds_projection) - bounds_bound
            )
            if missing_bounds:
                raise ValueError(
                    "GCC bounds use unbound variables: "
                    + _variable_names(missing_bounds)
                )
        elif self.bounds_projection is not None or bounds:
            raise ValueError(f"{self.kind} does not accept BOUNDS")
        if self.kind is PersistentConstraintKind.TABLE:
            if self.tuples_projection is None or not tuples:
                raise ValueError("TABLE constraint template requires TUPLES")
            tuples_bound = validate_premise_bindings((*context, *tuples))
            missing_tuples = (
                variables_in(self.tuples_projection) - tuples_bound
            )
            if missing_tuples:
                raise ValueError(
                    "TABLE tuples use unbound variables: "
                    + _variable_names(missing_tuples)
                )
        elif self.tuples_projection is not None or tuples:
            raise ValueError(f"{self.kind} does not accept TUPLES")
        object.__setattr__(self, "context", context)
        if self.context_key is not None:
            object.__setattr__(self, "context_key", tuple(self.context_key))
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "bounds", bounds)
        object.__setattr__(self, "tuples", tuples)


def parse_constraint_templates(
    text: str,
) -> tuple[PersistentConstraintTemplate, ...]:
    """Parse one or more ``CONSTRAINT ... END`` templates.

    Example::

        CONSTRAINT line_sum
        KIND SUM
        FOR EACH
            ($line kind magic_line)
            ($line target $target)
        END_FOR_EACH
        SCOPE $cell ORDER BY $position
        FROM
            ($line cell SEQ[$position $cell])
        END_SCOPE
        TARGET $target
        END
    """

    lines = _normalized_lines(text)
    templates: list[PersistentConstraintTemplate] = []
    position = 0
    while position < len(lines):
        header = lines[position].split(maxsplit=1)
        if len(header) != 2 or header[0] != "CONSTRAINT":
            raise ParseError(
                f"expected CONSTRAINT header, got {lines[position]!r}"
            )
        name = header[1]
        position += 1
        if position >= len(lines) or not lines[position].startswith("KIND "):
            raise ParseError(f"constraint {name!r} is missing KIND")
        kind_text = lines[position].removeprefix("KIND ").strip()
        try:
            kind = PersistentConstraintKind(kind_text)
        except ValueError as error:
            raise ParseError(
                f"unsupported persistent constraint kind {kind_text!r}"
            ) from error
        position += 1

        context: tuple[Premise, ...] = ()
        context_key: tuple[Term, ...] | None = None
        if position < len(lines) and lines[position].startswith("FOR EACH"):
            key_text = lines[position].removeprefix("FOR EACH").strip()
            if key_text:
                parsed_key = parse_term(key_text)
                if not isinstance(parsed_key, FiniteSequence):
                    raise ParseError(
                        "FOR EACH key must be an ordered SEQ[...]"
                    )
                context_key = parsed_key.elements
            body, position = _read_block(
                lines,
                position + 1,
                "END_FOR_EACH",
                f"constraint {name!r} FOR EACH",
            )
            context = parse_premises("\n".join(body))

        if position >= len(lines):
            raise ParseError(f"constraint {name!r} is missing SCOPE")
        scope_match = _SCOPE_RE.fullmatch(lines[position])
        if scope_match is None:
            raise ParseError(
                f"constraint {name!r} expected SCOPE, "
                f"got {lines[position]!r}"
            )
        scope_projection = parse_term(scope_match.group("projection"))
        scope_order_text = scope_match.group("order")
        scope_order = (
            parse_term(scope_order_text)
            if scope_order_text is not None
            else None
        )
        position += 1
        if position >= len(lines) or lines[position] != "FROM":
            raise ParseError(f"constraint {name!r} SCOPE is missing FROM")
        scope_body, position = _read_block(
            lines,
            position + 1,
            "END_SCOPE",
            f"constraint {name!r} SCOPE",
        )
        scope = parse_premises("\n".join(scope_body))

        target: Term | None = None
        bounds_projection: Term | None = None
        bounds: tuple[Premise, ...] = ()
        tuples_projection: Term | None = None
        tuples: tuple[Premise, ...] = ()
        if kind is PersistentConstraintKind.SUM:
            if position >= len(lines) or not lines[position].startswith(
                "TARGET "
            ):
                raise ParseError(f"SUM constraint {name!r} is missing TARGET")
            target = parse_term(
                lines[position].removeprefix("TARGET ").strip()
            )
            position += 1
        elif kind is PersistentConstraintKind.GCC:
            if position >= len(lines):
                raise ParseError(f"GCC constraint {name!r} is missing BOUNDS")
            bounds_match = _BOUNDS_RE.fullmatch(lines[position])
            if bounds_match is None:
                raise ParseError(f"GCC constraint {name!r} is missing BOUNDS")
            bounds_projection = parse_term(bounds_match.group("projection"))
            position += 1
            if position >= len(lines) or lines[position] != "FROM":
                raise ParseError(
                    f"constraint {name!r} BOUNDS is missing FROM"
                )
            bounds_body, position = _read_block(
                lines,
                position + 1,
                "END_BOUNDS",
                f"constraint {name!r} BOUNDS",
            )
            bounds = parse_premises("\n".join(bounds_body))
        elif kind is PersistentConstraintKind.TABLE:
            if position >= len(lines) or not lines[position].startswith(
                "TUPLES "
            ):
                raise ParseError(
                    f"TABLE constraint {name!r} is missing TUPLES"
                )
            tuples_projection = parse_term(
                lines[position].removeprefix("TUPLES ").strip()
            )
            position += 1
            if position >= len(lines) or lines[position] != "FROM":
                raise ParseError(
                    f"constraint {name!r} TUPLES is missing FROM"
                )
            tuples_body, position = _read_block(
                lines,
                position + 1,
                "END_TUPLES",
                f"constraint {name!r} TUPLES",
            )
            tuples = parse_premises("\n".join(tuples_body))

        if position >= len(lines) or lines[position] != "END":
            raise ParseError(f"constraint {name!r} is missing END")
        position += 1
        if any(template.name == name for template in templates):
            raise ParseError(f"duplicate constraint template name {name!r}")
        try:
            templates.append(
                PersistentConstraintTemplate(
                    name,
                    kind,
                    context,
                    context_key,
                    scope_projection,
                    scope_order,
                    scope,
                    target,
                    bounds_projection,
                    bounds,
                    tuples_projection,
                    tuples,
                )
            )
        except ValueError as error:
            raise ParseError(str(error)) from error
    return tuple(templates)


def instantiate_constraint_templates(
    templates: Sequence[PersistentConstraintTemplate],
    facts: Sequence[Fact],
) -> tuple[PersistentConstraint, ...]:
    """Ground fact-derived templates against the fixed root fact set."""

    grounded: list[PersistentConstraint] = []
    facts_tuple = tuple(facts)
    for template in templates:
        grounded.extend(_instantiate_template(template, facts_tuple))
    names = tuple(constraint.name for constraint in grounded)
    if len(set(names)) != len(names):
        raise ValueError("grounded persistent constraint names are not unique")
    return tuple(grounded)


def _instantiate_template(
    template: PersistentConstraintTemplate,
    facts: tuple[Fact, ...],
) -> tuple[PersistentConstraint, ...]:
    context_bound = validate_premise_bindings(template.context)
    context_terms = (
        template.context_key
        if template.context_key is not None
        else tuple(
            sorted(context_bound, key=lambda variable: variable.name)
        )
    )
    scope_activations = _query(
        template.name,
        (*template.context, *template.scope),
        facts,
    )
    grouped: dict[
        tuple[Term, ...],
        list[tuple[Term | None, Term, Term | None]],
    ] = {}
    for activation in scope_activations:
        substitution = activation.substitution
        key = tuple(
            substitution.apply(term)
            for term in context_terms
        )
        projection = substitution.apply(template.scope_projection)
        order = (
            substitution.apply(template.scope_order)
            if template.scope_order is not None
            else None
        )
        target = (
            substitution.apply(template.target)
            if template.target is not None
            else None
        )
        grouped.setdefault(key, []).append((order, projection, target))

    bounds_by_context: dict[
        tuple[Term, ...],
        list[tuple[Term, int, int]],
    ] = {}
    if template.kind is PersistentConstraintKind.GCC:
        assert template.bounds_projection is not None
        for activation in _query(
            f"{template.name}_bounds",
            (*template.context, *template.bounds),
            facts,
        ):
            substitution = activation.substitution
            key = tuple(
                substitution.apply(term)
                for term in context_terms
            )
            projection = substitution.apply(template.bounds_projection)
            if (
                not isinstance(projection, FiniteSequence)
                or len(projection.elements) != 3
            ):
                raise ValueError(
                    f"GCC template {template.name!r} BOUNDS must project "
                    "SEQ[value lower upper]"
                )
            value, lower, upper = projection.elements
            bounds_by_context.setdefault(key, []).append(
                (
                    value,
                    _integer(lower, "GCC lower bound"),
                    _integer(upper, "GCC upper bound"),
                )
            )

    tuples_by_context: dict[
        tuple[Term, ...],
        list[tuple[Term, ...]],
    ] = {}
    if template.kind is PersistentConstraintKind.TABLE:
        assert template.tuples_projection is not None
        for activation in _query(
            f"{template.name}_tuples",
            (*template.context, *template.tuples),
            facts,
        ):
            substitution = activation.substitution
            key = tuple(
                substitution.apply(term)
                for term in context_terms
            )
            projection = substitution.apply(template.tuples_projection)
            if not isinstance(projection, FiniteSequence):
                raise ValueError(
                    f"TABLE template {template.name!r} TUPLES must "
                    "project SEQ[...]"
                )
            tuples_by_context.setdefault(key, []).append(
                projection.elements
            )

    output: list[PersistentConstraint] = []
    ordered_groups = sorted(grouped.items(), key=lambda item: repr(item[0]))
    for instance, (key, rows) in enumerate(ordered_groups, start=1):
        if template.scope_order is not None:
            rows.sort(key=lambda row: _term_sort_key(row[0]))
        else:
            rows.sort(key=lambda row: repr(row[1]))
        variables = tuple(dict.fromkeys(row[1] for row in rows))
        name = Atom(
            template.name
            if len(ordered_groups) == 1 and not key
            else f"{template.name}_{instance}"
        )
        if template.kind is PersistentConstraintKind.ALL_DIFFERENT:
            output.append(AllDifferentConstraint(name, variables))
        elif template.kind is PersistentConstraintKind.SUM:
            targets = {row[2] for row in rows}
            if len(targets) != 1:
                raise ValueError(
                    f"SUM template {template.name!r} has inconsistent targets"
                )
            target = next(iter(targets))
            if target is None:
                raise AssertionError("validated SUM target is absent")
            output.append(
                SumConstraint(
                    name,
                    variables,
                    _integer(target, "SUM target"),
                )
            )
        elif template.kind is PersistentConstraintKind.GCC:
            output.append(
                GlobalCardinalityConstraint(
                    name,
                    variables,
                    tuple(
                        sorted(
                            bounds_by_context.get(key, ()),
                            key=lambda bound: repr(bound[0]),
                        )
                    ),
                )
            )
        else:
            output.append(
                TableConstraint(
                    name,
                    variables,
                    tuple(tuples_by_context.get(key, ())),
                )
            )
    return tuple(output)


def _query(
    name: str,
    premises: tuple[Premise, ...],
    facts: tuple[Fact, ...],
):
    rule = Rule(
        f"__constraint_query_{name}",
        premises,
        (add(Atom("__constraint_query_result")),),
    )
    return IndexedInstantiationStrategy().instantiate(rule, facts)


def _integer(term: Term, description: str) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise ValueError(f"{description} must resolve to an integer Number")
    return term.value


def _term_sort_key(term: Term | None) -> tuple[int, int | float | str]:
    if isinstance(term, Number):
        return (0, term.value)
    return (1, "" if term is None else render_term(term))


def _variable_names(variables: set[Variable] | frozenset[Variable]) -> str:
    return ", ".join(
        f"${variable.name}"
        for variable in sorted(variables, key=lambda item: item.name)
    )


def _read_block(
    lines: tuple[str, ...],
    position: int,
    terminator: str,
    description: str,
) -> tuple[tuple[str, ...], int]:
    body: list[str] = []
    while position < len(lines) and lines[position] != terminator:
        body.append(lines[position])
        position += 1
    if position >= len(lines):
        raise ParseError(f"{description} is missing {terminator}")
    if not body:
        raise ParseError(f"{description} cannot be empty")
    return tuple(body), position + 1


def _normalized_lines(text: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
