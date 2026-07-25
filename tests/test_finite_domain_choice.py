from csp_solver.finite_domain_choice import FiniteDomainChoiceProvider
from csp_solver.finite_domain_projection import FiniteDomainProjection
from csp_solver.finite_domain_state import FiniteDomainStatePropagator
from csp_solver.solver import (
    CANDIDATE,
    CHOICE_WEIGHT,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    STATE,
    VALUE,
    VARIABLE,
    finite_csp_rule_library,
)
from snarky import (
    Atom,
    Fact,
    FiniteSequence,
    ForwardEngine,
    Number,
    RuleChoiceProvider,
    Triple,
)


def _choice_session():
    problem = Atom("problem")
    variable = Atom("variable")
    facts = (
        Fact(Triple(problem, KIND, CSP_PROBLEM)),
        Fact(Triple(problem, VARIABLE, variable)),
        Fact(Triple(variable, KIND, CSP_VARIABLE)),
        *(
            Fact(Triple(variable, CANDIDATE, Number(value)))
            for value in (1, 2, 3)
        ),
        *(
            Fact(
                Triple(
                    variable,
                    CHOICE_WEIGHT,
                    FiniteSequence((Number(value), Number(value / 10))),
                )
            )
            for value in (1, 2, 3)
        ),
    )
    return ForwardEngine(()).create_session(facts), variable


def test_compiled_finite_domain_choices_match_rule_choices() -> None:
    session, variable = _choice_session()
    rule_provider = RuleChoiceProvider(
        finite_csp_rule_library().finite_domain_groups
    )
    compiled = FiniteDomainChoiceProvider(
        rule_provider.propagation_groups
    )

    assert compiled(session) == rule_provider(session)

    session.retract(
        Fact(Triple(variable, CANDIDATE, Number(2))),
        label="test",
    )

    assert compiled(session) == rule_provider(session)
    compiled_point = compiled(session)[0]
    rule_point = rule_provider(session)[0]
    assert dict(compiled_point.metadata) == dict(rule_point.metadata)
    for compiled_alternative, rule_alternative in zip(
        compiled_point.alternatives,
        rule_point.alternatives,
        strict=True,
    ):
        assert dict(compiled_alternative.metadata) == dict(
            rule_alternative.metadata
        )


def test_compiled_finite_domain_state_matches_canonical_rules() -> None:
    problem = Atom("problem")
    first = Atom("first")
    second = Atom("second")
    decision = Atom("decision")
    solved = Atom("solved")
    facts = (
        Fact(Triple(problem, KIND, CSP_PROBLEM)),
        Fact(Triple(problem, VARIABLE, first)),
        Fact(Triple(problem, VARIABLE, second)),
        Fact(Triple(first, KIND, CSP_VARIABLE)),
        Fact(Triple(second, KIND, CSP_VARIABLE)),
        Fact(Triple(first, CANDIDATE, Number(1))),
        Fact(Triple(first, CANDIDATE, Number(2))),
        Fact(Triple(second, CANDIDATE, Number(1))),
        Fact(Triple(first, decision, Number(2))),
    )
    library = finite_csp_rule_library()
    rule_provider = RuleChoiceProvider(library.finite_domain_groups)
    reference = ForwardEngine(()).create_session(facts)
    for group in rule_provider.propagation_groups:
        reference.run_group(group)

    compiled = ForwardEngine(()).create_session(facts)
    FiniteDomainStatePropagator(
        problem,
        library.choices,
        library.domains,
        library.problems,
    )(compiled)

    assert compiled.facts == reference.facts
    assert Fact(Triple(first, VALUE, Number(2))) in compiled.facts
    assert Fact(Triple(second, VALUE, Number(1))) in compiled.facts
    assert Fact(Triple(problem, STATE, solved)) in compiled.facts
    assert [
        (
            event.kind,
            event.fact,
            event.rule_name,
            event.rule_group,
            event.premises,
        )
        for event in compiled.events
    ] == [
        (
            event.kind,
            event.fact,
            event.rule_name,
            event.rule_group,
            event.premises,
        )
        for event in reference.events
    ]


def test_finite_domain_projection_restores_sibling_state_after_rollback() -> None:
    session, variable = _choice_session()
    projection = FiniteDomainProjection()
    root = projection.snapshot(session)
    root_candidates = frozenset(root.candidates[variable])
    checkpoint = session.checkpoint()

    session.retract(
        Fact(Triple(variable, CANDIDATE, Number(2))),
        label="first-branch",
    )
    session.assume(
        Fact(Triple(variable, VALUE, Number(1))),
        label="first-branch",
    )
    first = projection.snapshot(session)
    assert tuple(first.candidates[variable]) == (Number(1), Number(3))
    assert variable in first.values

    session.rollback(checkpoint)
    session.assume(
        Fact(Triple(variable, Atom("decision"), Number(3))),
        label="second-branch",
    )
    sibling = projection.snapshot(session)
    fresh = FiniteDomainProjection().snapshot(session)

    assert frozenset(sibling.candidates[variable]) == root_candidates
    assert variable not in sibling.values
    assert sibling.candidates == fresh.candidates
    assert sibling.values == fresh.values
    assert sibling.decisions == fresh.decisions
    assert sibling.present == fresh.present
    rule_provider = RuleChoiceProvider(
        finite_csp_rule_library().finite_domain_groups
    )
    assert FiniteDomainChoiceProvider(
        rule_provider.propagation_groups,
        projection,
    )(session) == rule_provider(session)
    session.release(checkpoint)
