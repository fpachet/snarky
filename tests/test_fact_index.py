from snarky import Atom, Fact, Triple, Variable
from snarky.instantiation.fact_index import FactIndex
from snarky.instantiation.indexed import FactIndex as HistoricalFactIndex
from snarky.premises import FactPremise
from snarky.substitutions import EMPTY_SUBSTITUTION


def _fact(subject: str, object_: str) -> Fact:
    return Fact(
        Triple(
            Atom(subject),
            Atom("relation"),
            Atom(object_),
        )
    )


def test_fact_index_keeps_its_historical_internal_import() -> None:
    assert HistoricalFactIndex is FactIndex


def test_fact_index_preserves_ranked_order_across_mutations_and_clones() -> None:
    first = _fact("first", "one")
    second = _fact("second", "two")
    index = FactIndex((first, second))
    clone = index.clone()

    assert index.remove(frozenset((first,))) == 1
    assert index.extend((first,)) == 1

    assert tuple(index.facts) == (second, first)
    assert tuple(clone.facts) == (first, second)
    assert clone.ranks[first] < clone.ranks[second]
    assert index.ranks[second] < index.ranks[first]


def test_fact_index_partitions_candidates_at_a_stable_delta_rank() -> None:
    old = _fact("old", "one")
    new = _fact("new", "two")
    index = FactIndex((old, new))
    premise = FactPremise(
        Triple(
            Variable("subject"),
            Atom("relation"),
            Variable("object"),
        )
    )
    delta_start = index.delta_start((new,))

    assert tuple(
        index.candidates_partitioned(
            premise,
            EMPTY_SUBSTITUTION,
            delta_start,
            new=False,
        )
    ) == (old,)
    assert tuple(
        index.candidates_partitioned(
            premise,
            EMPTY_SUBSTITUTION,
            delta_start,
            new=True,
        )
    ) == (new,)


def test_large_mutated_bucket_preserves_order_clone_and_delta_partition() -> None:
    facts = tuple(
        _fact(f"node-{index}", f"value-{index}")
        for index in range(80)
    )
    removed = facts[20]
    index = FactIndex(facts)
    premise = FactPremise(
        Triple(
            Variable("subject"),
            Atom("relation"),
            Variable("object"),
        )
    )

    assert index.remove(frozenset((removed,))) == 1
    clone = index.clone()
    added = _fact("node-new", "value-new")
    assert index.extend((added,)) == 1
    delta_start = index.delta_start((added,))

    survivors = tuple(fact for fact in facts if fact != removed)
    assert tuple(
        index.candidates_partitioned(
            premise,
            EMPTY_SUBSTITUTION,
            delta_start,
            new=False,
        )
    ) == survivors
    assert tuple(
        index.candidates_partitioned(
            premise,
            EMPTY_SUBSTITUTION,
            delta_start,
            new=True,
        )
    ) == (added,)
    assert tuple(clone.candidates(premise, EMPTY_SUBSTITUTION)) == survivors
