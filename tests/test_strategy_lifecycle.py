from snarky import (
    AdaptiveInstantiationStrategy,
    Atom,
    ChoiceAlternative,
    ChoicePoint,
    ConstraintInstantiationStrategy,
    Fact,
    ForwardEngine,
    InstantiationMetrics,
    RuleChoiceProvider,
    SessionChoiceSearch,
    Triple,
    parse_rule_groups,
    parse_rules,
)
from snarky.instantiation import (
    Activation,
    FactDelta,
    InstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
from snarky.rules import Rule


class _LifecycleAwareStrategy:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.delegate = SemiNaiveInstantiationStrategy()
        self.metrics = InstantiationMetrics()

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        assert isinstance(facts, tuple)
        return self.delegate.instantiate(rule, facts, delta)

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        self.delegate.invalidate(removed)

    def fork_for_branch(self) -> InstantiationStrategy:
        self.events.append("branch")
        return _LifecycleAwareStrategy(self.events)

    def query_view(self) -> InstantiationStrategy:
        self.events.append("query")
        return self.delegate.query_view()


class _LegacyStrategy:
    def __init__(self) -> None:
        self.delegate = SemiNaiveInstantiationStrategy()
        self.metrics = InstantiationMetrics()

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: FactDelta | tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]:
        assert isinstance(facts, tuple)
        return self.delegate.instantiate(rule, facts, delta)

    def invalidate(self, removed: frozenset[Fact] = frozenset()) -> None:
        self.delegate.invalidate(removed)


def test_search_uses_structural_branch_lifecycle_contract() -> None:
    events: list[str] = []
    strategy = _LifecycleAwareStrategy(events)
    selected = Fact(Triple(Atom("selection"), Atom("value"), Atom("yes")))
    parent = ForwardEngine((), strategy=strategy).create_session(
        (Fact(Atom("start")),)
    )
    search = SessionChoiceSearch(
        (),
        lambda session: (
            ()
            if selected in session.facts
            else (
                ChoicePoint(
                    "selection",
                    (ChoiceAlternative("yes", (selected,)),),
                ),
            )
        ),
        lambda session: selected in session.facts,
    )

    result = search.solve(parent)

    assert result.solutions
    assert events
    assert set(events) == {"branch"}


def test_search_keeps_legacy_strategy_fallback() -> None:
    selected = Fact(Triple(Atom("selection"), Atom("value"), Atom("yes")))
    parent = ForwardEngine((), strategy=_LegacyStrategy()).create_session(())
    search = SessionChoiceSearch(
        (),
        lambda session: (
            ()
            if selected in session.facts
            else (
                ChoicePoint(
                    "selection",
                    (ChoiceAlternative("yes", (selected,)),),
                ),
            )
        ),
        lambda session: selected in session.facts,
    )

    result = search.solve(parent)

    assert result.solutions
    assert selected in result.solutions[0].session.facts
    assert parent.facts == ()


def test_rule_choice_provider_uses_structural_query_lifecycle_contract() -> None:
    events: list[str] = []
    strategy = _LifecycleAwareStrategy(events)
    (choices,) = parse_rule_groups(
        """
        GROUP choices
            RULE choose_value
            WHEN
                (problem candidate $value)
            THEN
                CHOICE (problem selected $value)
                FROM
                    (problem candidate $value)
                END_CHOICE
            END
        END_GROUP
        """
    )
    session = ForwardEngine((), strategy=strategy).create_session(
        (
            Fact(
                Triple(
                    Atom("problem"),
                    Atom("candidate"),
                    Atom("yes"),
                )
            ),
        )
    )

    points = RuleChoiceProvider((choices,))(session)

    assert points
    assert events == ["query"]


def test_constraint_strategies_preserve_their_type_when_branching() -> None:
    constrained = ConstraintInstantiationStrategy().fork_for_branch()
    adaptive = AdaptiveInstantiationStrategy().fork_for_branch()

    assert type(constrained) is ConstraintInstantiationStrategy
    assert type(adaptive) is AdaptiveInstantiationStrategy


def test_populated_adaptive_strategy_forks_isolated_filter_state() -> None:
    (rule,) = parse_rules(
        """
        RULE constrained_triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )
    size = 8
    facts = (
        *(
            Fact(
                Triple(
                    Atom(f"x{x_index}"),
                    Atom("p"),
                    Atom(f"y{y_index}"),
                )
            )
            for x_index in range(size)
            for y_index in range(size)
        ),
        *(
            Fact(
                Triple(
                    Atom(f"x{x_index}"),
                    Atom("q"),
                    Atom(f"z{z_index}"),
                )
            )
            for x_index in range(size)
            for z_index in range(size)
        ),
        Fact(Triple(Atom("y0"), Atom("r"), Atom("z0"))),
    )
    strategy = AdaptiveInstantiationStrategy(minimum_domain_rows=1)
    expected = strategy.instantiate(rule, facts)

    branch = strategy.fork_for_branch()

    assert type(branch) is AdaptiveInstantiationStrategy
    assert branch._adaptive_selector is not strategy._adaptive_selector
    assert branch._filter_decisions == strategy._filter_decisions
    assert branch._filter_decisions is not strategy._filter_decisions
    assert branch._domain_memories[rule] is not strategy._domain_memories[rule]
    assert all(
        branch._domain_memories[rule].tables[position]
        is not strategy._domain_memories[rule].tables[position]
        for position in strategy._domain_memories[rule].tables
    )
    assert branch.instantiate(rule, facts) == expected

    branch.invalidate()

    assert strategy._domain_memories
    assert strategy._filter_decisions
