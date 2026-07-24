import pytest

from snarky import (
    Atom,
    ChoiceAlternative,
    ChoiceEventKind,
    ChoicePoint,
    ChoiceSearchStatus,
    Fact,
    ForwardEngine,
    MRVChoicePolicy,
    SessionChoiceSearch,
    Triple,
    WeightedRandomChoicePolicy,
    parse_rule_groups,
)


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
