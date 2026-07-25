"""Balanced graph coloring with persistent NOT_EQUAL, GCC, and report rules."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from snarky import (
    Atom,
    ChoiceSearchResult,
    ChoiceSolution,
    Fact,
    FiniteSequence,
    Number,
    RuleGroup,
    Triple,
    parse_rule_groups,
)

from .constraint_syntax import (
    PersistentConstraintTemplate,
    instantiate_constraint_templates,
    parse_constraint_templates,
)
from .solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    FiniteCSP,
    assignment_from_solution,
    finite_csp_rule_library,
    solve_finite_csp,
)

COLORING_VERTEX = Atom("coloring_vertex")
COLORING_COLOR = Atom("coloring_color")
COLORING_EDGE = Atom("coloring_edge")
COLORING_BOUND = Atom("coloring_bound")
MEMBER = Atom("member")
LEFT = Atom("left")
RIGHT = Atom("right")
COLOR = Atom("color")
LOWER = Atom("lower")
UPPER = Atom("upper")


@dataclass(frozen=True, slots=True)
class BalancedColoringInstance:
    vertices: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    colors: tuple[str, ...]
    bounds: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        vertices = set(self.vertices)
        if not vertices or len(vertices) != len(self.vertices):
            raise ValueError("graph vertices must be non-empty and unique")
        if not self.colors or len(set(self.colors)) != len(self.colors):
            raise ValueError("graph colors must be non-empty and unique")
        if len(self.colors) != len(self.bounds):
            raise ValueError("every color requires one cardinality bound")
        if any(
            left not in vertices or right not in vertices or left == right
            for left, right in self.edges
        ):
            raise ValueError("edges must connect distinct declared vertices")
        if any(lower < 0 or upper < lower for lower, upper in self.bounds):
            raise ValueError("color bounds require 0 <= lower <= upper")


TRIANGULAR_PRISM = BalancedColoringInstance(
    vertices=("a", "b", "c", "d", "e", "f"),
    edges=(
        ("a", "b"),
        ("b", "c"),
        ("c", "a"),
        ("d", "e"),
        ("e", "f"),
        ("f", "d"),
        ("a", "d"),
        ("b", "e"),
        ("c", "f"),
    ),
    colors=("red", "green", "blue"),
    bounds=((2, 2), (2, 2), (2, 2)),
)


def coloring_problem(
    instance: BalancedColoringInstance = TRIANGULAR_PRISM,
) -> Atom:
    return Atom(
        f"balanced_coloring_{len(instance.vertices)}_{len(instance.colors)}"
    )


def vertex(name: str) -> Atom:
    return Atom(f"coloring_vertex_{name}")


def color(name: str) -> Atom:
    return Atom(name)


def balanced_graph_coloring_model(
    instance: BalancedColoringInstance = TRIANGULAR_PRISM,
) -> FiniteCSP:
    """Build a graph coloring with explicit color-cardinality bounds."""

    problem = coloring_problem(instance)
    facts: list[Fact] = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
    for color_name, (lower, upper) in zip(
        instance.colors,
        instance.bounds,
        strict=True,
    ):
        color_term = color(color_name)
        bound = Atom(f"coloring_bound_{color_name}")
        facts.extend(
            (
                Fact(Triple(color_term, KIND, COLORING_COLOR)),
                Fact(Triple(bound, KIND, COLORING_BOUND)),
                Fact(Triple(bound, COLOR, color_term)),
                Fact(Triple(bound, LOWER, Number(lower))),
                Fact(Triple(bound, UPPER, Number(upper))),
            )
        )
    for vertex_name in instance.vertices:
        variable = vertex(vertex_name)
        facts.extend(
            (
                Fact(Triple(problem, VARIABLE, variable)),
                Fact(Triple(variable, KIND, CSP_VARIABLE)),
                Fact(Triple(variable, KIND, COLORING_VERTEX)),
                *(
                    Fact(Triple(variable, CANDIDATE, color(color_name)))
                    for color_name in instance.colors
                ),
            )
        )
    for number, (left_name, right_name) in enumerate(instance.edges, start=1):
        edge = Atom(f"coloring_edge_{number}")
        left_vertex = vertex(left_name)
        right_vertex = vertex(right_name)
        facts.extend(
            (
                Fact(Triple(edge, KIND, COLORING_EDGE)),
                Fact(Triple(edge, LEFT, left_vertex)),
                Fact(Triple(edge, RIGHT, right_vertex)),
                Fact(
                    Triple(
                        edge,
                        MEMBER,
                        FiniteSequence((Number(1), left_vertex)),
                    )
                ),
                Fact(
                    Triple(
                        edge,
                        MEMBER,
                        FiniteSequence((Number(2), right_vertex)),
                    )
                ),
            )
        )
    fact_tuple = tuple(facts)
    return FiniteCSP(
        problem,
        fact_tuple,
        {},
        _report_groups(),
        instantiate_constraint_templates(_templates(), fact_tuple),
    )


@cache
def _templates() -> tuple[PersistentConstraintTemplate, ...]:
    return parse_constraint_templates(
        Path(__file__).with_suffix(".constraints").read_text()
    )


@cache
def _report_groups() -> tuple[RuleGroup, ...]:
    return parse_rule_groups(Path(__file__).with_suffix(".rules").read_text())


def solve_balanced_graph_coloring(
    instance: BalancedColoringInstance = TRIANGULAR_PRISM,
    *,
    max_nodes: int = 100_000,
) -> ChoiceSearchResult:
    model = balanced_graph_coloring_model(instance)
    return solve_finite_csp(
        model,
        max_nodes=max_nodes,
        rule_groups=(
            *finite_csp_rule_library().finite_domain_groups,
            *model.groups,
        ),
    )


def coloring_from_solution(
    solution: ChoiceSolution,
    instance: BalancedColoringInstance = TRIANGULAR_PRISM,
) -> dict[str, str]:
    assignment = assignment_from_solution(solution, coloring_problem(instance))
    return {
        vertex_name: _atom_name(assignment[vertex(vertex_name)])
        for vertex_name in instance.vertices
    }


def validate_coloring(
    coloring: dict[str, str],
    instance: BalancedColoringInstance = TRIANGULAR_PRISM,
) -> bool:
    if set(coloring) != set(instance.vertices):
        return False
    if any(coloring[left] == coloring[right] for left, right in instance.edges):
        return False
    return all(
        lower <= tuple(coloring.values()).count(color_name) <= upper
        for color_name, (lower, upper) in zip(
            instance.colors,
            instance.bounds,
            strict=True,
        )
    )


def _atom_name(term) -> str:
    if not isinstance(term, Atom):
        raise ValueError("a graph color must be an atom")
    return term.name


def main() -> None:
    result = solve_balanced_graph_coloring()
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        print(coloring_from_solution(solution))


if __name__ == "__main__":
    main()
