from itertools import product

from csp_solver.persistent_constraints import (
    AllDifferentConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    SumConstraint,
    _revise_all_different,
    _revise_gcc,
    _revise_lex_less_equal,
    _revise_sum,
)
from snarky import Atom, Number, Term


def _non_empty_subsets(values: tuple[Term, ...]) -> tuple[set[Term], ...]:
    return tuple(
        {
            value
            for index, value in enumerate(values)
            if mask & (1 << index)
        }
        for mask in range(1, 1 << len(values))
    )


def _supported_domains(
    variables: tuple[Atom, ...],
    domains: dict[Term, set[Term]],
    accepts,
) -> tuple[bool, dict[Term, set[Term]]]:
    solutions = tuple(
        assignment
        for assignment in product(
            *(domains[variable] for variable in variables)
        )
        if accepts(assignment)
    )
    return (
        bool(solutions),
        {
            variable: {
                assignment[position] for assignment in solutions
            }
            for position, variable in enumerate(variables)
        },
    )


def test_all_different_gac_matches_exhaustive_support_oracle() -> None:
    variables = tuple(Atom(f"x_{index}") for index in range(3))
    values = tuple(Number(index) for index in range(3))
    subsets = _non_empty_subsets(values)
    constraint = AllDifferentConstraint(
        Atom("all_different_oracle"),
        variables,
    )

    for selections in product(subsets, repeat=len(variables)):
        domains = {
            variable: set(selection)
            for variable, selection in zip(
                variables,
                selections,
                strict=True,
            )
        }
        consistent, expected = _supported_domains(
            variables,
            domains,
            lambda assignment: len(set(assignment)) == len(assignment),
        )
        filtered = {
            variable: set(domain)
            for variable, domain in domains.items()
        }

        assert _revise_all_different(constraint, filtered) is consistent
        if consistent:
            assert filtered == expected


def test_gcc_gac_matches_exhaustive_support_oracle() -> None:
    variables = tuple(Atom(f"x_{index}") for index in range(3))
    red = Atom("red")
    blue = Atom("blue")
    values = (red, blue)
    subsets = _non_empty_subsets(values)
    bound_cases = (
        ((red, 0, 3), (blue, 0, 3)),
        ((red, 1, 2), (blue, 1, 2)),
        ((red, 2, 2), (blue, 1, 1)),
        ((red, 0, 1), (blue, 2, 3)),
    )

    for bounds in bound_cases:
        constraint = GlobalCardinalityConstraint(
            Atom("gcc_oracle"),
            variables,
            bounds,
        )
        for selections in product(subsets, repeat=len(variables)):
            domains = {
                variable: set(selection)
                for variable, selection in zip(
                    variables,
                    selections,
                    strict=True,
                )
            }
            consistent, expected = _supported_domains(
                variables,
                domains,
                lambda assignment, bounds=bounds: all(
                    lower <= assignment.count(value) <= upper
                    for value, lower, upper in bounds
                ),
            )
            filtered = {
                variable: set(domain)
                for variable, domain in domains.items()
            }

            assert _revise_gcc(constraint, filtered) is consistent
            if consistent:
                assert filtered == expected


def test_sum_gac_matches_exhaustive_support_oracle() -> None:
    variables = tuple(Atom(f"x_{index}") for index in range(3))
    values = tuple(Number(index) for index in range(4))
    subsets = _non_empty_subsets(values)

    for target in (0, 2, 4, 6, 9):
        constraint = SumConstraint(
            Atom(f"sum_{target}"),
            variables,
            target,
        )
        for selections in product(subsets, repeat=len(variables)):
            domains = {
                variable: set(selection)
                for variable, selection in zip(
                    variables,
                    selections,
                    strict=True,
                )
            }
            consistent, expected = _supported_domains(
                variables,
                domains,
                lambda assignment, target=target: sum(
                    value.value for value in assignment
                )
                == target,
            )
            filtered = {
                variable: set(domain)
                for variable, domain in domains.items()
            }

            assert _revise_sum(constraint, filtered) is consistent
            if consistent:
                assert filtered == expected


def test_lex_less_equal_bounds_filter_is_sound_with_aliases() -> None:
    x, y, z = (Atom(name) for name in ("x", "y", "z"))
    variables = (x, y, z)
    values = tuple(Number(index) for index in range(3))
    subsets = _non_empty_subsets(values)
    constraint = LexLessEqualConstraint(
        Atom("lex_oracle"),
        (x, y),
        (y, z),
    )

    for selections in product(subsets, repeat=len(variables)):
        domains = {
            variable: set(selection)
            for variable, selection in zip(
                variables,
                selections,
                strict=True,
            )
        }
        consistent, expected = _supported_domains(
            variables,
            domains,
            lambda assignment: tuple(
                value.value for value in assignment[:2]
            )
            <= tuple(value.value for value in assignment[1:]),
        )
        filtered = {
            variable: set(domain)
            for variable, domain in domains.items()
        }

        propagated = _revise_lex_less_equal(constraint, filtered)
        if not propagated:
            assert not consistent
        if consistent:
            assert all(
                expected[variable] <= filtered[variable]
                for variable in variables
            )


def test_disjoint_lex_less_equal_gac_matches_exhaustive_oracle() -> None:
    variables = tuple(Atom(name) for name in ("x_1", "x_2", "y_1", "y_2"))
    values = (Number(0), Number(1))
    subsets = _non_empty_subsets(values)
    constraint = LexLessEqualConstraint(
        Atom("disjoint_lex_oracle"),
        variables[:2],
        variables[2:],
    )

    for selections in product(subsets, repeat=len(variables)):
        domains = {
            variable: set(selection)
            for variable, selection in zip(
                variables,
                selections,
                strict=True,
            )
        }
        consistent, expected = _supported_domains(
            variables,
            domains,
            lambda assignment: tuple(
                value.value for value in assignment[:2]
            )
            <= tuple(value.value for value in assignment[2:]),
        )
        filtered = {
            variable: set(domain)
            for variable, domain in domains.items()
        }

        assert _revise_lex_less_equal(constraint, filtered) is consistent
        if consistent:
            assert filtered == expected
