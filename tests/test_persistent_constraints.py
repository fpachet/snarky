import pytest

from csp_solver.constraint_syntax import (
    instantiate_constraint_templates,
    parse_constraint_templates,
)
from csp_solver.persistent_constraints import (
    AllDifferentConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    SumConstraint,
    TableConstraint,
)
from csp_solver.solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    FiniteCSP,
    assignment_from_solution,
    constraint_dom_wdeg_policy,
    solve_finite_csp,
)
from snarky import (
    Atom,
    ChoiceSearchStatus,
    Fact,
    FiniteSequence,
    Number,
    Triple,
    parse_rule_groups,
)


def _domain_facts(
    problem: Atom,
    domains: dict[Atom, tuple[int, ...]],
) -> tuple[Fact, ...]:
    facts = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
    for variable, values in domains.items():
        facts.extend(
            (
                Fact(Triple(problem, VARIABLE, variable)),
                Fact(Triple(variable, KIND, CSP_VARIABLE)),
                *(
                    Fact(Triple(variable, CANDIDATE, Number(value)))
                    for value in values
                ),
            )
        )
    return tuple(facts)


def test_rules_observe_the_persistent_constraint_fixed_point() -> None:
    problem = Atom("fixed_point_example")
    left = Atom("left")
    middle = Atom("middle")
    right = Atom("right")
    (observer,) = parse_rule_groups(
        """
        GROUP observe_constraints
            RULE observe_filtered_singleton
            WHEN
                (right candidate 3)
                NOT EXISTS
                    (right candidate $other)
                    $other != 3
                END_EXISTS
            THEN
                ADD (fixed_point_example observed filtered_domains)
            END
        END_GROUP
        """
    )
    model = FiniteCSP(
        problem,
        _domain_facts(
            problem,
            {
                left: (1, 2),
                middle: (1, 2),
                right: (1, 2, 3),
            },
        ),
        {},
        (observer,),
        (
            AllDifferentConstraint(
                Atom("three_distinct"),
                (left, middle, right),
            ),
            SumConstraint(
                Atom("sum_six"),
                (left, middle, right),
                6,
            ),
        ),
    )

    result = solve_finite_csp(model, max_solutions=2)

    assert result.status is ChoiceSearchStatus.SOLVED
    assert len(result.solutions) == 2
    observed = Fact(
        Triple(problem, Atom("observed"), Atom("filtered_domains"))
    )
    assert all(observed in solution.session.facts for solution in result.solutions)
    assignments = {
        tuple(
            assignment_from_solution(solution, problem)[variable].value
            for variable in (left, middle, right)
        )
        for solution in result.solutions
    }
    assert assignments == {(1, 2, 3), (2, 1, 3)}


def test_persistent_constraint_contradiction_stops_before_choice() -> None:
    problem = Atom("pigeonhole")
    variables = tuple(Atom(f"x_{index}") for index in range(3))
    model = FiniteCSP(
        problem,
        _domain_facts(
            problem,
            {variable: (1, 2) for variable in variables},
        ),
        {},
        constraints=(
            AllDifferentConstraint(
                Atom("impossible_all_different"),
                variables,
            ),
        ),
    )

    policy = constraint_dom_wdeg_policy(model)
    result = solve_finite_csp(model, policy=policy)

    assert result.status is ChoiceSearchStatus.EXHAUSTED
    assert result.explored_nodes == 1
    assert result.failed_branches == 1
    assert policy.weights[Atom("impossible_all_different")] == 2


def test_sum_constraint_rejects_non_integer_candidate_domains() -> None:
    problem = Atom("non_numeric_sum")
    variable = Atom("x")
    model = FiniteCSP(
        problem,
        (
            Fact(Triple(problem, KIND, CSP_PROBLEM)),
            Fact(Triple(problem, VARIABLE, variable)),
            Fact(Triple(variable, KIND, CSP_VARIABLE)),
            Fact(Triple(variable, CANDIDATE, Atom("not_a_number"))),
        ),
        {},
        constraints=(
            SumConstraint(Atom("integer_sum"), (variable,), 1),
        ),
    )

    try:
        solve_finite_csp(model)
    except TypeError as error:
        assert "integer Number candidates" in str(error)
    else:
        raise AssertionError("SUM accepted a non-integer domain")


def test_lex_constraint_rejects_non_numeric_candidate_domains() -> None:
    problem = Atom("non_numeric_lex")
    variable = Atom("x")
    model = FiniteCSP(
        problem,
        (
            Fact(Triple(problem, KIND, CSP_PROBLEM)),
            Fact(Triple(problem, VARIABLE, variable)),
            Fact(Triple(variable, KIND, CSP_VARIABLE)),
            Fact(Triple(variable, CANDIDATE, Atom("not_a_number"))),
        ),
        {},
        constraints=(
            LexLessEqualConstraint(
                Atom("numeric_lex"),
                (variable,),
                (variable,),
            ),
        ),
    )

    with pytest.raises(TypeError, match="numeric Number candidates"):
        solve_finite_csp(model)


def test_fact_derived_gcc_template_filters_occurrence_bounds() -> None:
    problem = Atom("gcc_example")
    first = Atom("first")
    second = Atom("second")
    third = Atom("third")
    red = Atom("red")
    blue = Atom("blue")
    slot = Atom("slot")
    bound = Atom("gcc_bound")
    facts = (
        *_domain_facts(
            problem,
            {
                first: (),
                second: (),
                third: (),
            },
        ),
        Fact(Triple(first, KIND, slot)),
        Fact(Triple(second, KIND, slot)),
        Fact(Triple(third, KIND, slot)),
        Fact(Triple(first, CANDIDATE, red)),
        Fact(Triple(second, CANDIDATE, red)),
        Fact(Triple(third, CANDIDATE, red)),
        Fact(Triple(third, CANDIDATE, blue)),
        Fact(Triple(Atom("red_bound"), KIND, bound)),
        Fact(Triple(Atom("red_bound"), Atom("value"), red)),
        Fact(Triple(Atom("red_bound"), Atom("minimum"), Number(2))),
        Fact(Triple(Atom("red_bound"), Atom("maximum"), Number(2))),
        Fact(Triple(Atom("blue_bound"), KIND, bound)),
        Fact(Triple(Atom("blue_bound"), Atom("value"), blue)),
        Fact(Triple(Atom("blue_bound"), Atom("minimum"), Number(1))),
        Fact(Triple(Atom("blue_bound"), Atom("maximum"), Number(1))),
    )
    templates = parse_constraint_templates(
        """
        CONSTRAINT color_cardinality
        KIND GCC
        SCOPE $variable
        FROM
            ($variable kind slot)
        END_SCOPE
        BOUNDS SEQ[$value $lower $upper]
        FROM
            ($bound kind gcc_bound)
            ($bound value $value)
            ($bound minimum $lower)
            ($bound maximum $upper)
        END_BOUNDS
        END
        """
    )
    constraints = instantiate_constraint_templates(templates, facts)

    assert constraints == (
        GlobalCardinalityConstraint(
            Atom("color_cardinality"),
            (first, second, third),
            (
                (blue, 1, 1),
                (red, 2, 2),
            ),
        ),
    )
    model = FiniteCSP(
        problem,
        facts,
        {},
        constraints=constraints,
    )
    result = solve_finite_csp(model)

    assert result.status is ChoiceSearchStatus.SOLVED
    assignment = assignment_from_solution(result.solutions[0], problem)
    assert assignment == {
        first: red,
        second: red,
        third: blue,
    }


def test_fact_derived_table_constraint_filters_complete_supports() -> None:
    problem = Atom("table_example")
    left = Atom("left")
    right = Atom("right")
    relation = Atom("allowed_pairs")
    red = Atom("red")
    blue = Atom("blue")
    facts = (
        *_domain_facts(
            problem,
            {
                left: (),
                right: (),
            },
        ),
        Fact(Triple(left, CANDIDATE, red)),
        Fact(Triple(left, CANDIDATE, blue)),
        Fact(Triple(right, CANDIDATE, red)),
        Fact(Triple(right, CANDIDATE, blue)),
        Fact(
            Triple(
                problem,
                Atom("scope"),
                FiniteSequence((Number(1), left)),
            )
        ),
        Fact(
            Triple(
                problem,
                Atom("scope"),
                FiniteSequence((Number(2), right)),
            )
        ),
        Fact(
            Triple(
                relation,
                Atom("allows"),
                FiniteSequence((red, blue)),
            )
        ),
    )
    templates = parse_constraint_templates(
        """
        CONSTRAINT allowed_color_pair
        KIND TABLE
        SCOPE $variable ORDER BY $position
        FROM
            (table_example scope SEQ[$position $variable])
        END_SCOPE
        TUPLES $tuple
        FROM
            (allowed_pairs allows $tuple)
        END_TUPLES
        END
        """
    )
    constraints = instantiate_constraint_templates(templates, facts)

    assert constraints == (
        TableConstraint(
            Atom("allowed_color_pair"),
            (left, right),
            ((red, blue),),
        ),
    )
    result = solve_finite_csp(
        FiniteCSP(problem, facts, {}, constraints=constraints)
    )

    assert result.status is ChoiceSearchStatus.SOLVED
    assert assignment_from_solution(result.solutions[0], problem) == {
        left: red,
        right: blue,
    }


def test_fact_derived_lex_less_equal_accepts_paired_scope_projection() -> None:
    first = Atom("first")
    second = Atom("second")
    third = Atom("third")
    ordering = Atom("ordering")
    facts = (
        Fact(
            Triple(
                ordering,
                Atom("pair"),
                FiniteSequence((Number(1), first, second)),
            )
        ),
        Fact(
            Triple(
                ordering,
                Atom("pair"),
                FiniteSequence((Number(2), second, third)),
            )
        ),
    )
    templates = parse_constraint_templates(
        """
        CONSTRAINT canonical_order
        KIND LEX_LESS_EQUAL
        SCOPE SEQ[$left $right] ORDER BY $position
        FROM
            (ordering pair SEQ[$position $left $right])
        END_SCOPE
        END
        """
    )

    assert instantiate_constraint_templates(templates, facts) == (
        LexLessEqualConstraint(
            Atom("canonical_order"),
            (first, second),
            (second, third),
        ),
    )
