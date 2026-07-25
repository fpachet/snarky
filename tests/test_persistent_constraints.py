import pytest

from csp_solver.constraint_syntax import (
    instantiate_constraint_templates,
    parse_constraint_templates,
)
from csp_solver.persistent_constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    CandidateRemovalExplanation,
    ConstraintOperator,
    CountConstraint,
    ElementConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    LinearSumConstraint,
    PersistentConstraintPropagator,
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
    ForwardEngine,
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


def test_candidate_removal_explanations_are_rollback_aware() -> None:
    problem = Atom("explained_sum")
    left = Atom("left")
    right = Atom("right")
    facts = _domain_facts(
        problem,
        {
            left: (1, 2),
            right: (1, 2),
        },
    )
    session = ForwardEngine(()).create_session(facts)
    constraint = SumConstraint(
        Atom("sum_three"),
        (left, right),
        3,
    )
    propagator = PersistentConstraintPropagator(
        problem,
        (constraint,),
    )
    propagator(session)
    assert propagator.removal_explanations(session) == ()

    checkpoint = session.checkpoint()
    session.retract(
        Fact(Triple(left, CANDIDATE, Number(2))),
        label="test-decision",
    )
    propagator(session)

    assert propagator.removal_explanations(session) == (
        CandidateRemovalExplanation(
            right,
            Number(1),
            constraint.name,
        ),
    )

    session.rollback(checkpoint)
    session.release(checkpoint)
    propagator(session)

    assert propagator.removal_explanations(session) == ()


def test_new_constraint_filtering_is_restored_by_rollback() -> None:
    problem = Atom("rollback_comparison")
    left, right = Atom("left"), Atom("right")
    session = ForwardEngine(()).create_session(
        _domain_facts(
            problem,
            {
                left: (1, 2),
                right: (2, 3),
            },
        )
    )
    constraint = BinaryComparisonConstraint(
        Atom("left_before_right"),
        left,
        right,
        BinaryComparisonOperator.LESS_THAN,
    )
    propagator = PersistentConstraintPropagator(problem, (constraint,))
    propagator(session)
    checkpoint = session.checkpoint()
    session.retract(
        Fact(Triple(right, CANDIDATE, Number(3))),
        label="test-decision",
    )

    propagator(session)

    assert Fact(Triple(left, CANDIDATE, Number(2))) not in session.facts
    assert propagator.removal_explanations(session) == (
        CandidateRemovalExplanation(left, Number(2), constraint.name),
    )

    session.rollback(checkpoint)
    session.release(checkpoint)
    propagator(session)

    assert Fact(Triple(left, CANDIDATE, Number(2))) in session.facts
    assert Fact(Triple(right, CANDIDATE, Number(3))) in session.facts
    assert propagator.removal_explanations(session) == ()


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


def test_fact_derived_templates_cover_the_practical_constraint_family() -> None:
    model = Atom("model")
    x, y = Atom("x"), Atom("y")
    index, first, second, result = (
        Atom("index"),
        Atom("first"),
        Atom("second"),
        Atom("result"),
    )
    facts = (
        Fact(
            Triple(
                model,
                Atom("weighted"),
                FiniteSequence((Number(1), Number(2), x)),
            )
        ),
        Fact(
            Triple(
                model,
                Atom("weighted"),
                FiniteSequence((Number(2), Number(-1), y)),
            )
        ),
        Fact(
            Triple(
                model,
                Atom("pair"),
                FiniteSequence((Number(1), x)),
            )
        ),
        Fact(
            Triple(
                model,
                Atom("pair"),
                FiniteSequence((Number(2), y)),
            )
        ),
        Fact(
            Triple(
                model,
                Atom("array"),
                FiniteSequence((Number(1), first)),
            )
        ),
        Fact(
            Triple(
                model,
                Atom("array"),
                FiniteSequence((Number(2), second)),
            )
        ),
    )
    templates = parse_constraint_templates(
        """
        CONSTRAINT weighted_capacity
        KIND LINEAR_SUM
        SCOPE SEQ[$coefficient $variable] ORDER BY $position
        FROM
            (model weighted SEQ[$position $coefficient $variable])
        END_SCOPE
        OPERATOR LESS_EQUAL
        TARGET 7
        END

        CONSTRAINT ordered_pair
        KIND LESS_THAN
        SCOPE $variable ORDER BY $position
        FROM
            (model pair SEQ[$position $variable])
        END_SCOPE
        END

        CONSTRAINT two_ones
        KIND COUNT
        SCOPE $variable ORDER BY $position
        FROM
            (model pair SEQ[$position $variable])
        END_SCOPE
        VALUE 1
        OPERATOR EQUAL
        TARGET 2
        END

        CONSTRAINT selected_value
        KIND ELEMENT
        SCOPE $variable ORDER BY $position
        FROM
            (model array SEQ[$position $variable])
        END_SCOPE
        INDEX index
        VALUE result
        END
        """
    )

    assert instantiate_constraint_templates(templates, facts) == (
        LinearSumConstraint(
            Atom("weighted_capacity"),
            ((2, x), (-1, y)),
            ConstraintOperator.LESS_EQUAL,
            7,
        ),
        BinaryComparisonConstraint(
            Atom("ordered_pair"),
            x,
            y,
            BinaryComparisonOperator.LESS_THAN,
        ),
        CountConstraint(
            Atom("two_ones"),
            (x, y),
            Number(1),
            ConstraintOperator.EQUAL,
            2,
        ),
        ElementConstraint(
            Atom("selected_value"),
            index,
            (first, second),
            result,
        ),
    )


def test_new_constraints_propagate_together_before_search() -> None:
    problem = Atom("practical_constraints")
    x, y = Atom("x"), Atom("y")
    index, first, second, result = (
        Atom("index"),
        Atom("first"),
        Atom("second"),
        Atom("result"),
    )
    count_left, count_right = Atom("count_left"), Atom("count_right")
    red, blue = Atom("red"), Atom("blue")
    numeric_facts = _domain_facts(
        problem,
        {
            x: (1, 2),
            y: (1, 2, 3),
            index: (1,),
            first: (5,),
            second: (6,),
            result: (5, 6),
            count_left: (),
            count_right: (),
        },
    )
    facts = (
        *numeric_facts,
        Fact(Triple(count_left, CANDIDATE, red)),
        Fact(Triple(count_left, CANDIDATE, blue)),
        Fact(Triple(count_right, CANDIDATE, red)),
    )
    constraints = (
        LinearSumConstraint(
            Atom("sum_four"),
            ((1, x), (1, y)),
            ConstraintOperator.EQUAL,
            4,
        ),
        BinaryComparisonConstraint(
            Atom("increasing"),
            x,
            y,
            BinaryComparisonOperator.LESS_THAN,
        ),
        ElementConstraint(
            Atom("lookup"),
            index,
            (first, second),
            result,
        ),
        CountConstraint(
            Atom("both_red"),
            (count_left, count_right),
            red,
            ConstraintOperator.GREATER_EQUAL,
            2,
        ),
    )

    result_set = solve_finite_csp(
        FiniteCSP(problem, facts, {}, constraints=constraints)
    )

    assert result_set.status is ChoiceSearchStatus.SOLVED
    assert assignment_from_solution(result_set.solutions[0], problem) == {
        x: Number(1),
        y: Number(3),
        index: Number(1),
        first: Number(5),
        second: Number(6),
        result: Number(5),
        count_left: red,
        count_right: red,
    }
