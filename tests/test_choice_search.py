import pytest

import snarky
import snarky.choice as choice_api
import snarky.choice_search as search_api
from snarky import (
    Atom,
    ChoiceAlternative,
    ChoiceEventKind,
    ChoicePoint,
    ChoicePolicy,
    ChoicePropagationObservation,
    ChoiceSearchStatus,
    ChoiceTraversal,
    DomWdegChoicePolicy,
    Fact,
    ForwardEngine,
    InferenceSession,
    LearnedImpactChoicePolicy,
    MRVChoicePolicy,
    PriorityMRVChoicePolicy,
    PriorityWeightedRandomChoicePolicy,
    PropagationGuidedChoicePolicy,
    SessionChoiceSearch,
    Triple,
    WeightedRandomChoicePolicy,
    parse_rule_groups,
)
from snarky.choice_frontier import (
    ChoiceTraversal as FrontierChoiceTraversal,
)
from snarky.choice_policies import (
    ChoicePolicy as PolicyChoicePolicy,
)
from snarky.choice_policies import (
    ChoicePropagationObservation as PolicyChoicePropagationObservation,
)
from snarky.choice_policies import (
    DomWdegChoicePolicy as PolicyDomWdegChoicePolicy,
)
from snarky.choice_policies import (
    LearnedImpactChoicePolicy as PolicyLearnedImpactChoicePolicy,
)
from snarky.choice_policies import (
    MRVChoicePolicy as PolicyMRVChoicePolicy,
)
from snarky.choice_policies import (
    PriorityMRVChoicePolicy as PolicyPriorityMRVChoicePolicy,
)
from snarky.choice_policies import (
    PriorityWeightedRandomChoicePolicy as PolicyPriorityWeightedRandom,
)
from snarky.choice_policies import (
    PropagationGuidedChoicePolicy as PolicyPropagationGuidedChoicePolicy,
)
from snarky.choice_policies import (
    WeightedRandomChoicePolicy as PolicyWeightedRandomChoicePolicy,
)
from snarky.choice_production import (
    ChoiceAlternative as ProductionChoiceAlternative,
)
from snarky.choice_production import (
    ChoicePoint as ProductionChoicePoint,
)


def test_choice_traversal_keeps_its_public_import_paths() -> None:
    assert ChoiceTraversal is snarky.ChoiceTraversal
    assert ChoiceTraversal is choice_api.ChoiceTraversal
    assert ChoiceTraversal is FrontierChoiceTraversal


def test_choice_models_keep_their_public_import_paths() -> None:
    assert ChoiceAlternative is snarky.ChoiceAlternative
    assert ChoiceAlternative is choice_api.ChoiceAlternative
    assert ChoiceAlternative is ProductionChoiceAlternative
    assert ChoicePoint is snarky.ChoicePoint
    assert ChoicePoint is choice_api.ChoicePoint
    assert ChoicePoint is ProductionChoicePoint


def test_choice_policies_keep_their_public_import_paths() -> None:
    assert ChoicePolicy is snarky.ChoicePolicy
    assert ChoicePolicy is choice_api.ChoicePolicy
    assert ChoicePolicy is PolicyChoicePolicy
    assert ChoicePropagationObservation is snarky.ChoicePropagationObservation
    assert (
        ChoicePropagationObservation
        is choice_api.ChoicePropagationObservation
    )
    assert (
        ChoicePropagationObservation
        is PolicyChoicePropagationObservation
    )
    assert DomWdegChoicePolicy is snarky.DomWdegChoicePolicy
    assert DomWdegChoicePolicy is choice_api.DomWdegChoicePolicy
    assert DomWdegChoicePolicy is PolicyDomWdegChoicePolicy
    assert LearnedImpactChoicePolicy is snarky.LearnedImpactChoicePolicy
    assert LearnedImpactChoicePolicy is choice_api.LearnedImpactChoicePolicy
    assert (
        LearnedImpactChoicePolicy is PolicyLearnedImpactChoicePolicy
    )
    assert MRVChoicePolicy is snarky.MRVChoicePolicy
    assert MRVChoicePolicy is choice_api.MRVChoicePolicy
    assert MRVChoicePolicy is PolicyMRVChoicePolicy
    assert (
        PropagationGuidedChoicePolicy
        is snarky.PropagationGuidedChoicePolicy
    )
    assert (
        PropagationGuidedChoicePolicy
        is choice_api.PropagationGuidedChoicePolicy
    )
    assert (
        PropagationGuidedChoicePolicy
        is PolicyPropagationGuidedChoicePolicy
    )
    assert PriorityMRVChoicePolicy is snarky.PriorityMRVChoicePolicy
    assert PriorityMRVChoicePolicy is choice_api.PriorityMRVChoicePolicy
    assert PriorityMRVChoicePolicy is PolicyPriorityMRVChoicePolicy
    assert (
        PriorityWeightedRandomChoicePolicy
        is snarky.PriorityWeightedRandomChoicePolicy
    )
    assert (
        PriorityWeightedRandomChoicePolicy
        is choice_api.PriorityWeightedRandomChoicePolicy
    )
    assert (
        PriorityWeightedRandomChoicePolicy
        is PolicyPriorityWeightedRandom
    )
    assert WeightedRandomChoicePolicy is snarky.WeightedRandomChoicePolicy
    assert (
        WeightedRandomChoicePolicy is choice_api.WeightedRandomChoicePolicy
    )
    assert (
        WeightedRandomChoicePolicy is PolicyWeightedRandomChoicePolicy
    )


def test_dom_wdeg_selects_by_domain_over_dynamic_weighted_degree() -> None:
    x = Atom("x")
    y = Atom("y")
    z = Atom("z")
    xy = Atom("xy")
    yz = Atom("yz")

    def point(variable: Atom, size: int) -> ChoicePoint:
        return ChoicePoint(
            variable.name,
            tuple(
                ChoiceAlternative(
                    str(index),
                    (Fact(Triple(variable, Atom("value"), Atom(str(index)))),),
                )
                for index in range(size)
            ),
            variable=variable,
        )

    failed: tuple[Atom, ...] = ()
    policy = DomWdegChoicePolicy(
        {xy: (x, y), yz: (y, z)},
        lambda _session: failed,
    )
    points = (point(x, 2), point(y, 4), point(z, 4))

    assert policy.select_point(points).variable == x

    failed = (yz,)
    policy.observe_failure(InferenceSession(()))
    policy.observe_failure(InferenceSession(()))

    assert policy.weights[yz] == 3
    assert policy.select_point(points).variable == y


def test_choice_search_keeps_its_public_import_paths() -> None:
    assert SessionChoiceSearch is snarky.SessionChoiceSearch
    assert SessionChoiceSearch is choice_api.SessionChoiceSearch
    assert SessionChoiceSearch is search_api.SessionChoiceSearch
    assert ChoiceEventKind is snarky.ChoiceEventKind
    assert ChoiceEventKind is choice_api.ChoiceEventKind
    assert ChoiceEventKind is search_api.ChoiceEventKind
    assert ChoiceSearchStatus is snarky.ChoiceSearchStatus
    assert ChoiceSearchStatus is choice_api.ChoiceSearchStatus
    assert ChoiceSearchStatus is search_api.ChoiceSearchStatus
    assert snarky.ChoiceDecision is choice_api.ChoiceDecision
    assert snarky.ChoiceDecision is search_api.ChoiceDecision
    assert snarky.ChoiceEvent is choice_api.ChoiceEvent
    assert snarky.ChoiceEvent is search_api.ChoiceEvent
    assert snarky.ChoiceSearchResult is choice_api.ChoiceSearchResult
    assert snarky.ChoiceSearchResult is search_api.ChoiceSearchResult
    assert snarky.ChoiceSolution is choice_api.ChoiceSolution
    assert snarky.ChoiceSolution is search_api.ChoiceSolution
    assert snarky.StrategyFactory is choice_api.StrategyFactory
    assert snarky.StrategyFactory is search_api.StrategyFactory


def test_choice_alternative_rejects_invalid_weights() -> None:
    fact = Fact(Triple(Atom("x"), Atom("value"), Atom("one")))

    with pytest.raises(ValueError, match="finite and non-negative"):
        ChoiceAlternative("one", (fact,), weight=-1)
    with pytest.raises(ValueError, match="finite and non-negative"):
        ChoiceAlternative("one", (fact,), weight=float("nan"))


def test_search_backtracks_without_mutating_parent_session() -> None:
    (classify,) = parse_rule_groups(
        """
        GROUP classify
            RULE reject_bad
            WHEN
                (selection value bad)
            THEN
                ADD contradiction
            END

            RULE accept_good
            WHEN
                (selection value good)
            THEN
                ADD solved
            END
        END_GROUP
        """
    )
    bad = Fact(Triple(Atom("selection"), Atom("value"), Atom("bad")))
    good = Fact(Triple(Atom("selection"), Atom("value"), Atom("good")))
    solved = Fact(Atom("solved"))
    contradiction = Fact(Atom("contradiction"))
    parent = ForwardEngine(()).create_session((Fact(Atom("start")),))

    search = SessionChoiceSearch(
        (classify,),
        lambda current: (
            ()
            if bad in current.facts or good in current.facts
            else (
                ChoicePoint(
                    "selection",
                    (
                        ChoiceAlternative("bad", (bad,), weight=2.0),
                        ChoiceAlternative("good", (good,), weight=1.0),
                    ),
                ),
            )
        ),
        lambda current: solved in current.facts,
        lambda current: contradiction in current.facts,
        policy=MRVChoicePolicy(),
    )

    result = search.solve(parent)

    assert result.status is ChoiceSearchStatus.SOLVED
    assert result.failed_branches == 1
    assert good in result.solutions[0].session.facts
    assert bad not in result.solutions[0].session.facts
    assert parent.facts == (Fact(Atom("start")),)
    kinds = tuple(event.kind for event in result.events)
    assert ChoiceEventKind.CONTRADICTION in kinds
    assert ChoiceEventKind.BACKTRACK in kinds
    assert ChoiceEventKind.SOLUTION in kinds


def test_propagation_guided_order_places_a_failed_probe_last() -> None:
    (classify,) = parse_rule_groups(
        """
        GROUP classify_probe
            RULE reject_bad_probe
            WHEN
                (selection value bad)
            THEN
                ADD contradiction
            END

            RULE accept_good_probe
            WHEN
                (selection value good)
            THEN
                ADD solved
            END
        END_GROUP
        """
    )
    bad = Fact(Triple(Atom("selection"), Atom("value"), Atom("bad")))
    good = Fact(Triple(Atom("selection"), Atom("value"), Atom("good")))
    solved = Fact(Atom("solved"))
    contradiction = Fact(Atom("contradiction"))
    point = ChoicePoint(
        "selection",
        (
            ChoiceAlternative("bad", (bad,), weight=2.0),
            ChoiceAlternative("good", (good,), weight=1.0),
        ),
    )
    search = SessionChoiceSearch(
        (classify,),
        lambda current: (
            ()
            if bad in current.facts or good in current.facts
            else (point,)
        ),
        lambda current: solved in current.facts,
        lambda current: contradiction in current.facts,
        policy=PropagationGuidedChoicePolicy(
            MRVChoicePolicy(),
            lambda current: float(len(current.facts)),
        ),
    )

    result = search.solve(InferenceSession((Fact(Atom("start")),)))

    assert result.status is ChoiceSearchStatus.SOLVED
    assert result.explored_nodes == 2
    assert result.failed_branches == 0
    assert result.solutions[0].decisions[0].alternative == "good"


def test_learned_impact_orders_values_from_real_branch_observations() -> None:
    variable = Atom("x")
    low = ChoiceAlternative(
        "low",
        (Fact(Triple(variable, Atom("value"), Atom("low"))),),
        value=Atom("low"),
    )
    high = ChoiceAlternative(
        "high",
        (Fact(Triple(variable, Atom("value"), Atom("high"))),),
        value=Atom("high"),
    )
    point = ChoicePoint("x", (high, low), variable=variable)
    policy = LearnedImpactChoicePolicy(MRVChoicePolicy())
    policy.observe_propagation(
        ChoicePropagationObservation(
            "x",
            "high",
            variable,
            Atom("high"),
            2.0,
            None,
            failed=True,
        )
    )
    policy.observe_propagation(
        ChoicePropagationObservation(
            "x",
            "low",
            variable,
            Atom("low"),
            2.0,
            1.9,
        )
    )

    import random

    ordered = policy.order_alternatives(point, random.Random(0))

    assert tuple(alternative.name for alternative in ordered) == (
        "low",
        "high",
    )
    assert policy.impacts[("x", variable, Atom("high"), "high")] == 1.0


def test_search_feeds_real_branch_impacts_to_the_policy() -> None:
    (classify,) = parse_rule_groups(
        """
        GROUP classify_learned_impact
            RULE reject_bad_impact
            WHEN
                (selection value bad)
            THEN
                ADD contradiction
            END

            RULE accept_good_impact
            WHEN
                (selection value good)
            THEN
                ADD solved
            END
        END_GROUP
        """
    )
    variable = Atom("selection")
    bad_value = Atom("bad")
    good_value = Atom("good")
    bad = Fact(Triple(variable, Atom("value"), bad_value))
    good = Fact(Triple(variable, Atom("value"), good_value))
    point = ChoicePoint(
        "selection",
        (
            ChoiceAlternative(
                "bad",
                (bad,),
                value=bad_value,
                weight=2.0,
            ),
            ChoiceAlternative("good", (good,), value=good_value),
        ),
        variable=variable,
    )
    policy = LearnedImpactChoicePolicy(MRVChoicePolicy())
    result = SessionChoiceSearch(
        (classify,),
        lambda current: (
            ()
            if bad in current.facts or good in current.facts
            else (point,)
        ),
        lambda current: Fact(Atom("solved")) in current.facts,
        lambda current: Fact(Atom("contradiction")) in current.facts,
        policy=policy,
    ).solve(InferenceSession((Fact(Atom("start")),)))

    assert result.status is ChoiceSearchStatus.SOLVED
    assert result.explored_nodes == 3
    assert result.failed_branches == 1
    assert policy.impacts[
        ("selection", variable, bad_value, "bad")
    ] == 1.0
    assert policy.impacts[
        ("selection", variable, good_value, "good")
    ] == 0.0


def test_weighted_random_policy_is_seed_reproducible() -> None:
    point = ChoicePoint(
        "x",
        tuple(
            ChoiceAlternative(
                name,
                (Fact(Triple(Atom("x"), Atom("value"), Atom(name))),),
                weight=weight,
            )
            for name, weight in (("a", 0.1), ("b", 0.3), ("c", 0.6))
        ),
    )
    policy = WeightedRandomChoicePolicy()

    import random

    first = policy.order_alternatives(point, random.Random(17))
    second = policy.order_alternatives(point, random.Random(17))

    assert tuple(item.name for item in first) == tuple(
        item.name for item in second
    )


def test_priority_policies_respect_phases_before_domain_size() -> None:
    early = ChoicePoint(
        "early",
        (
            ChoiceAlternative("a", (Fact(Atom("a")),)),
            ChoiceAlternative("b", (Fact(Atom("b")),)),
        ),
        variable=Atom("early"),
    )
    late = ChoicePoint(
        "late",
        (ChoiceAlternative("only", (Fact(Atom("only")),)),),
        variable=Atom("late"),
    )
    priorities = {Atom("early"): 0, Atom("late"): 1}

    assert (
        PriorityMRVChoicePolicy(priorities).select_point((late, early))
        is early
    )
    assert (
        PriorityWeightedRandomChoicePolicy(priorities).select_point(
            (late, early)
        )
        is early
    )


@pytest.mark.parametrize(
    "traversal",
    (ChoiceTraversal.BREADTH_FIRST, ChoiceTraversal.BEST_FIRST),
)
def test_lazy_and_eager_frontiers_are_equivalent(
    traversal: ChoiceTraversal,
) -> None:
    values = tuple(
        ChoiceAlternative(
            name,
            (Fact(Triple(Atom("x"), Atom("value"), Atom(name))),),
            weight=weight,
        )
        for name, weight in (("a", 1.0), ("b", 2.0), ("c", 3.0))
    )

    def choices(current: InferenceSession) -> tuple[ChoicePoint, ...]:
        facts = current.facts
        return (
            ()
            if any(alternative.facts[0] in facts for alternative in values)
            else (ChoicePoint("x", values),)
        )

    parent = ForwardEngine(()).create_session((Fact(Atom("start")),))
    results = tuple(
        SessionChoiceSearch(
            (),
            choices,
            lambda current: any(
                alternative.facts[0] in current.facts
                for alternative in values
            ),
            traversal=traversal,
            max_solutions=3,
            lazy_frontier=lazy,
        ).solve(parent)
        for lazy in (False, True)
    )

    eager, lazy = results
    assert lazy.status is eager.status
    assert lazy.explored_nodes == eager.explored_nodes
    assert lazy.failed_branches == eager.failed_branches
    assert lazy.events == eager.events
    assert tuple(
        (solution.decisions, solution.log_weight, solution.session.facts)
        for solution in lazy.solutions
    ) == tuple(
        (solution.decisions, solution.log_weight, solution.session.facts)
        for solution in eager.solutions
    )
