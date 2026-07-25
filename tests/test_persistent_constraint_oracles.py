from itertools import product

from csp_solver.persistent_constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    ConstraintOperator,
    CountConstraint,
    ElementConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    LinearSumConstraint,
    SumConstraint,
    _revise_all_different,
    _revise_binary_comparison,
    _revise_count,
    _revise_element,
    _revise_gcc,
    _revise_lex_less_equal,
    _revise_linear_sum,
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


def test_linear_sum_gac_matches_exhaustive_support_oracle() -> None:
    variables = tuple(Atom(f"x_{index}") for index in range(3))
    values = tuple(Number(index) for index in (-1, 0, 1))
    subsets = _non_empty_subsets(values)
    coefficients = (2, -1, 3)

    for operator in ConstraintOperator:
        for target in (-3, 0, 4):
            constraint = LinearSumConstraint(
                Atom(f"linear_{operator}_{target}"),
                tuple(zip(coefficients, variables, strict=True)),
                operator,
                target,
            )
            for selections in product(subsets, repeat=len(variables)):
                domains = dict(
                    zip(
                        variables,
                        (set(selection) for selection in selections),
                        strict=True,
                    )
                )

                def accepts(
                    assignment,
                    operator=operator,
                    target=target,
                ) -> bool:
                    total = sum(
                        coefficient * value.value
                        for coefficient, value in zip(
                            coefficients,
                            assignment,
                            strict=True,
                        )
                    )
                    if operator is ConstraintOperator.EQUAL:
                        return total == target
                    if operator is ConstraintOperator.LESS_EQUAL:
                        return total <= target
                    return total >= target

                consistent, expected = _supported_domains(
                    variables,
                    domains,
                    accepts,
                )
                filtered = {
                    variable: set(domain)
                    for variable, domain in domains.items()
                }

                assert _revise_linear_sum(constraint, filtered) is consistent
                if consistent:
                    assert filtered == expected


def test_binary_comparison_gac_matches_exhaustive_support_oracle() -> None:
    left, right = Atom("left"), Atom("right")
    variables = (left, right)
    values = tuple(Number(index) for index in range(3))
    subsets = _non_empty_subsets(values)

    for operator in BinaryComparisonOperator:
        constraint = BinaryComparisonConstraint(
            Atom(f"comparison_{operator}"),
            left,
            right,
            operator,
        )
        for selections in product(subsets, repeat=2):
            domains = dict(
                zip(
                    variables,
                    (set(selection) for selection in selections),
                    strict=True,
                )
            )

            def accepts(assignment, operator=operator) -> bool:
                left_value, right_value = assignment
                if operator is BinaryComparisonOperator.LESS_EQUAL:
                    return left_value.value <= right_value.value
                if operator is BinaryComparisonOperator.LESS_THAN:
                    return left_value.value < right_value.value
                return left_value != right_value

            consistent, expected = _supported_domains(
                variables,
                domains,
                accepts,
            )
            filtered = {
                variable: set(domain)
                for variable, domain in domains.items()
            }

            assert (
                _revise_binary_comparison(constraint, filtered) is consistent
            )
            if consistent:
                assert filtered == expected


def test_count_gac_matches_exhaustive_support_oracle() -> None:
    variables = tuple(Atom(f"x_{index}") for index in range(3))
    red, blue = Atom("red"), Atom("blue")
    subsets = _non_empty_subsets((red, blue))

    for operator in ConstraintOperator:
        for target in (0, 1, 3):
            constraint = CountConstraint(
                Atom(f"count_{operator}_{target}"),
                variables,
                red,
                operator,
                target,
            )
            for selections in product(subsets, repeat=len(variables)):
                domains = dict(
                    zip(
                        variables,
                        (set(selection) for selection in selections),
                        strict=True,
                    )
                )

                def accepts(
                    assignment,
                    operator=operator,
                    target=target,
                ) -> bool:
                    count = assignment.count(red)
                    if operator is ConstraintOperator.EQUAL:
                        return count == target
                    if operator is ConstraintOperator.LESS_EQUAL:
                        return count <= target
                    return count >= target

                consistent, expected = _supported_domains(
                    variables,
                    domains,
                    accepts,
                )
                filtered = {
                    variable: set(domain)
                    for variable, domain in domains.items()
                }

                assert _revise_count(constraint, filtered) is consistent
                if consistent:
                    assert filtered == expected


def test_element_gac_matches_exhaustive_support_oracle() -> None:
    index = Atom("index")
    first = Atom("first")
    second = Atom("second")
    value = Atom("value")
    variables = (index, first, second, value)
    index_subsets = _non_empty_subsets(
        tuple(Number(candidate) for candidate in range(4))
    )
    data_subsets = _non_empty_subsets((Atom("red"), Atom("blue")))
    constraint = ElementConstraint(
        Atom("element_oracle"),
        index,
        (first, second),
        value,
    )

    for index_domain in index_subsets:
        for data_domains in product(data_subsets, repeat=3):
            domains = {
                index: set(index_domain),
                first: set(data_domains[0]),
                second: set(data_domains[1]),
                value: set(data_domains[2]),
            }

            def accepts(assignment) -> bool:
                selected, *array, result = assignment
                return (
                    1 <= selected.value <= len(array)
                    and array[selected.value - 1] == result
                )

            consistent, expected = _supported_domains(
                variables,
                domains,
                accepts,
            )
            filtered = {
                variable: set(domain)
                for variable, domain in domains.items()
            }

            assert _revise_element(constraint, filtered) is consistent
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
