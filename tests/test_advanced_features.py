from collections.abc import Mapping

import pytest

from rulebases.thesis.geometry.computed_example import rules as geometry_rules
from snarky import (
    Atom,
    BacktrackingConstraintSolver,
    ComputedPredicate,
    ConstraintProblem,
    ConstraintVariable,
    Fact,
    FactExists,
    FactPremise,
    FiniteConstraint,
    FiniteSequence,
    ForwardEngine,
    GroupCall,
    Hypothesis,
    HypothesisSearch,
    IndexedInstantiationStrategy,
    InferenceSession,
    MEAConflictStrategy,
    NaiveInstantiationStrategy,
    Number,
    ParseError,
    PredicateRegistry,
    RecursiveGroupProcedure,
    Rule,
    RuleGroup,
    RuleGroupTemplate,
    SatClause,
    SatLiteral,
    SatProblem,
    SearchStatus,
    SemiNaiveInstantiationStrategy,
    Triple,
    Variable,
    add,
    computed,
    parse_rule_groups,
    parse_rules,
    parse_term,
    type_hierarchy_group,
)
from snarky.terms import Term


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


@pytest.mark.parametrize(
    "strategy",
    (
        NaiveInstantiationStrategy(),
        IndexedInstantiationStrategy(),
        SemiNaiveInstantiationStrategy(),
    ),
)
def test_windows_combinations_and_for_each_are_strategy_independent(
    strategy: (
        NaiveInstantiationStrategy
        | IndexedInstantiationStrategy
        | SemiNaiveInstantiationStrategy
    ),
) -> None:
    (rule,) = parse_rules(
        """
        RULE choose_pairs_in_windows
        WHEN
            WINDOW $window := SEQ[$a $b $c] VIA next
            COMBINATIONS $pair SIZE 2 FROM $window
        THEN
            ADD ($pair pair selected)
            FOR EACH $item IN $pair
                ADD ($item occurs selected)
            END_FOR_EACH
        END
        """
    )
    initial = (
        _fact("(a next b)"),
        _fact("(b next c)"),
        _fact("(c next d)"),
    )

    result = ForwardEngine((rule,), strategy=strategy).run(initial)

    assert _fact("(SEQ[a b] pair selected)") in result.facts
    assert _fact("(SEQ[b c] pair selected)") in result.facts
    assert _fact("(SEQ[c d] pair selected)") in result.facts
    assert _fact("(a occurs selected)") in result.facts
    assert _fact("(d occurs selected)") in result.facts


def test_sequence_terms_preserve_order_duplicates_and_pattern_variables() -> None:
    sequence = parse_term("SEQ[a b a]")

    assert sequence == FiniteSequence((Atom("a"), Atom("b"), Atom("a")))
    assert parse_term("SEQ[$x b $x]") != sequence


def test_explicit_focus_controls_mea_metadata() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP focused
            RULE act_on_goal
            WHEN
                (context state ready)
                FOCUS (goal status active)
            THEN
                ADD acted
            END
        END_GROUP
        """
    )
    goal = _fact("(goal status active)")
    session = ForwardEngine(
        (),
        conflict_strategy=MEAConflictStrategy(),
    ).create_session((_fact("(context state ready)"), goal))

    (candidate,) = session.inspect_agenda(group)

    assert candidate.focus_fact == goal


def test_incremental_agenda_recomputes_only_relevant_rules() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP indexed
            RULE left_rule
            WHEN
                ($x left yes)
            THEN
                ADD ($x seen left)
            END
            RULE right_rule
            WHEN
                ($x right yes)
            THEN
                ADD ($x seen right)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(
        (),
        conflict_strategy=MEAConflictStrategy(),
    ).create_session((_fact("(a left yes)"), _fact("(b right yes)")))
    session.inspect_agenda(group)
    before = session.agenda_metrics.rule_recomputations

    session.assume(_fact("(c left yes)"))
    session.inspect_agenda(group)

    assert session.agenda_metrics.rule_recomputations - before == 1
    assert session.agenda_metrics.rule_reuses >= 1
    assert session.fork().inspect_agenda(group)


def test_group_execution_recomputes_only_relevant_rules() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP selective
            RULE left_rule
            WHEN
                ($x left yes)
            THEN
                ADD ($x seen left)
            END
            RULE right_rule
            WHEN
                ($x right yes)
            THEN
                ADD ($x seen right)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(())
    session.run_group(group)
    before_recomputations = session.agenda_metrics.rule_recomputations
    before_reuses = session.agenda_metrics.rule_reuses

    session.assume(_fact("(a left yes)"))
    session.run_group(group)

    assert _fact("(a seen left)") in session.facts
    assert (
        session.agenda_metrics.rule_recomputations
        - before_recomputations
        == 1
    )
    assert session.agenda_metrics.rule_reuses - before_reuses == 3


def test_group_execution_schedules_later_dependent_rule_same_cycle() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP forward_order
            RULE source_to_middle
            WHEN
                ($x source yes)
            THEN
                ADD ($x middle yes)
            END
            RULE middle_to_final
            WHEN
                ($x middle yes)
            THEN
                ADD ($x final yes)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(())
    session.run_group(group)

    session.assume(_fact("(a source yes)"))
    session.run_group(group)

    final_event = next(
        event
        for event in session.events
        if event.fact == _fact("(a final yes)")
    )
    middle_event = next(
        event
        for event in session.events
        if event.fact == _fact("(a middle yes)")
    )
    assert final_event.cycle == middle_event.cycle


def test_group_execution_defers_earlier_dependent_rule_one_cycle() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP reverse_order
            RULE middle_to_final
            WHEN
                ($x middle yes)
            THEN
                ADD ($x final yes)
            END
            RULE source_to_middle
            WHEN
                ($x source yes)
            THEN
                ADD ($x middle yes)
            END
        END_GROUP
        """
    )
    session = ForwardEngine(()).create_session(())
    session.run_group(group)

    session.assume(_fact("(a source yes)"))
    session.run_group(group)

    final_event = next(
        event
        for event in session.events
        if event.fact == _fact("(a final yes)")
    )
    middle_event = next(
        event
        for event in session.events
        if event.fact == _fact("(a middle yes)")
    )
    assert final_event.cycle == middle_event.cycle + 1


def test_parameterized_and_recursive_group_control() -> None:
    node = Variable("node")
    template = RuleGroupTemplate(
        "visit",
        (node,),
        (
            Rule(
                "visit_node",
                (FactPremise(Triple(node, Atom("exists"), Atom("yes"))),),
                (add(Triple(node, Atom("visited"), Atom("yes"))),),
            ),
        ),
    )
    successors = {
        Atom("a"): Atom("b"),
        Atom("b"): Atom("c"),
    }

    def expand(
        call: GroupCall,
        _result: object,
        _session: InferenceSession,
    ) -> tuple[GroupCall, ...]:
        current = call.arguments[0]
        assert isinstance(current, Atom)
        successor = successors.get(current)
        return (
            ()
            if successor is None
            else (GroupCall(template, (successor,)),)
        )

    session = InferenceSession(
        (
            _fact("(a exists yes)"),
            _fact("(b exists yes)"),
            _fact("(c exists yes)"),
        )
    )
    result = RecursiveGroupProcedure(
        GroupCall(template, (Atom("a"),)),
        expand,
    ).run(session)

    assert len(result.calls) == 3
    assert _fact("(c visited yes)") in session.facts


def test_registered_computed_predicates_bind_and_guard() -> None:
    increment = ComputedPredicate(
        "increment",
        lambda arguments: Number(arguments[0].value + 1)
        if isinstance(arguments[0], Number)
        else False,
    )
    even = ComputedPredicate(
        "even",
        lambda arguments: (
            isinstance(arguments[0], Number)
            and isinstance(arguments[0].value, int)
            and arguments[0].value % 2 == 0
        ),
    )
    item = Variable("item")
    value = Variable("value")
    next_value = Variable("next")
    rule = Rule(
        "computed",
        (
            FactPremise(Triple(item, Atom("value"), value)),
            computed(increment, value, target=next_value),
            computed(even, next_value),
        ),
        (add(Triple(item, Atom("next_even"), next_value)),),
    )

    result = ForwardEngine((rule,)).run((_fact("(x value 3)"),))

    assert _fact("(x next_even 4)") in result.facts


def test_computed_predicate_dsl_requires_an_explicit_registry() -> None:
    positive = ComputedPredicate(
        "positive",
        lambda arguments: (
            isinstance(arguments[0], Number) and arguments[0].value > 0
        ),
    )
    registry = PredicateRegistry((positive,))
    text = """
        RULE safe_call
        WHEN
            ($item value $value)
            CHECK positive ARGS SEQ[$value]
        THEN
            ADD ($item accepted yes)
        END
    """

    (rule,) = parse_rules(text, predicates=registry)
    result = ForwardEngine((rule,)).run((_fact("(x value 2)"),))

    assert _fact("(x accepted yes)") in result.facts
    with pytest.raises(ParseError, match="PredicateRegistry"):
        parse_rules(text)


def test_same_named_predicates_from_different_registries_do_not_share_plans() -> None:
    text = """
        RULE guarded
        WHEN
            value
            CHECK decision ARGS SEQ[]
        THEN
            ADD accepted
        END
    """
    accepting = PredicateRegistry(
        (ComputedPredicate("decision", lambda _arguments: True),)
    )
    rejecting = PredicateRegistry(
        (ComputedPredicate("decision", lambda _arguments: False),)
    )
    accepting_rule = parse_rules(text, predicates=accepting)
    rejecting_rule = parse_rules(text, predicates=rejecting)

    assert Fact(Atom("accepted")) in ForwardEngine(
        accepting_rule,
        strategy=IndexedInstantiationStrategy(),
    ).run((Fact(Atom("value")),)).facts
    assert Fact(Atom("accepted")) not in ForwardEngine(
        rejecting_rule,
        strategy=IndexedInstantiationStrategy(),
    ).run((Fact(Atom("value")),)).facts


def test_type_hierarchy_is_explainable_by_ordinary_derivations() -> None:
    initial = (
        _fact("(cat subtype mammal)"),
        _fact("(mammal subtype animal)"),
        _fact("(felix instance_of cat)"),
    )
    result = ForwardEngine(type_hierarchy_group().rules).run(initial)
    inherited = _fact("(felix instance_of animal)")

    assert inherited in result.facts
    derivation = result.provenance.minimal_derivation(inherited)
    assert derivation is not None
    assert derivation.rule_name == "instance_inheritance"


def test_hypothesis_search_uses_isolated_forks() -> None:
    group = RuleGroup(
        "decide",
        (
            Rule(
                "blue_solves",
                (FactPremise(Atom("blue")),),
                (add(Atom("solved")),),
            ),
            Rule(
                "red_contradicts",
                (FactPremise(Atom("red")),),
                (add(Atom("contradiction")),),
            ),
        ),
    )

    def expand(
        _session: InferenceSession,
        path: tuple[Hypothesis, ...],
    ) -> tuple[Hypothesis, ...]:
        if path:
            return ()
        return (
            Hypothesis("try-red", (Fact(Atom("red")),)),
            Hypothesis("try-blue", (Fact(Atom("blue")),)),
        )

    search = HypothesisSearch(
        (group,),
        expand,
        FactExists(FactPremise(Atom("solved"))),
        FactExists(FactPremise(Atom("contradiction"))),
    )
    root = InferenceSession((Fact(Atom("start")),))

    result = search.solve(root)

    assert result.status is SearchStatus.SOLVED
    assert result.solution is not None
    assert result.solution.hypotheses[0].name == "try-blue"
    assert Fact(Atom("blue")) not in root.facts


def test_reference_constraint_and_sat_solvers_bridge_to_facts() -> None:
    one = Number(1)
    two = Number(2)

    def different(assignment: Mapping[str, Term]) -> bool:
        return assignment["x"] != assignment["y"]

    problem = ConstraintProblem(
        (
            ConstraintVariable("x", (one, two)),
            ConstraintVariable("y", (one, two)),
        ),
        (FiniteConstraint("different", ("x", "y"), different),),
    )
    solver = BacktrackingConstraintSolver()

    solutions = solver.solve(problem, max_solutions=2)
    sat = SatProblem(
        ("p", "q"),
        (
            SatClause((SatLiteral("p"), SatLiteral("q"))),
            SatClause((SatLiteral("p", positive=False),)),
        ),
    )

    assert len(solutions) == 2
    assert _fact("(x assigned 1)") in solutions[0].as_facts()
    assert solver.solve(sat.as_constraint_problem())


def test_optional_truth_maintenance_cascades_positive_justifications() -> None:
    rules = parse_rules(
        """
        RULE a_to_b
        WHEN
            a
        THEN
            ADD b
        END
        RULE b_to_c
        WHEN
            b
        THEN
            ADD c
        END
        """
    )
    session = ForwardEngine(
        rules,
        truth_maintenance=True,
    ).create_session((Fact(Atom("a")),))
    session.run_group(RuleGroup("derive", rules))

    removed = session.retract(Fact(Atom("a")))

    assert removed == (Fact(Atom("a")), Fact(Atom("b")), Fact(Atom("c")))
    assert not session.facts


def test_truth_maintenance_is_opt_in() -> None:
    (rule,) = parse_rules(
        """
        RULE a_to_b
        WHEN
            a
        THEN
            ADD b
        END
        """
    )
    session = ForwardEngine((rule,)).create_session((Fact(Atom("a")),))
    session.run_group(RuleGroup("derive", (rule,)))

    session.retract(Fact(Atom("a")))

    assert Fact(Atom("b")) in session.facts


def test_external_assumptions_reconcile_negative_refraction() -> None:
    (rule,) = parse_rules(
        """
        RULE absent_blocker
        WHEN
            trigger
            NOT EXISTS
                blocker
            END_EXISTS
        THEN
            ADD conclusion
        END
        """
    )
    group = RuleGroup("negative", (rule,))
    session = InferenceSession((Fact(Atom("trigger")),))
    session.run_group(group)

    session.assume(Fact(Atom("blocker")))
    session.retract(Fact(Atom("blocker")))
    session.run_group(group)

    assert session.snapshot().fired_activation_count == 2


def test_documented_computed_geometry_companion_executes() -> None:
    assert geometry_rules()[0].name == "accept_segment"


def test_focus_inside_an_existential_is_rejected() -> None:
    with pytest.raises(ValueError, match="top-level"):
        Rule(
            "bad_focus",
            (
                # Constructed through the parser in real DSL usage; the direct
                # object form makes the invariant independent of parsing.
                __import__("snarky").exists(
                    __import__("snarky").focus(FactPremise(Atom("nested")))
                ),
            ),
            (add(Atom("never")),),
        )
