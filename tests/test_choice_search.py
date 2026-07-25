import pytest

import snarky
import snarky.choice as choice_api
from snarky import (
    Atom,
    ChoiceAlternative,
    ChoiceEventKind,
    ChoicePoint,
    ChoiceSearchStatus,
    ChoiceTraversal,
    Fact,
    ForwardEngine,
    InferenceSession,
    MRVChoicePolicy,
    PriorityMRVChoicePolicy,
    PriorityWeightedRandomChoicePolicy,
    SessionChoiceSearch,
    Triple,
    WeightedRandomChoicePolicy,
    parse_rule_groups,
)
from snarky.choice_frontier import (
    ChoiceTraversal as FrontierChoiceTraversal,
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
