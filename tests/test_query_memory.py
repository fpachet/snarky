from snarky import Fact, parse_rules, parse_term
from snarky.instantiation.base import WitnessCacheKey
from snarky.instantiation.compiled import CompiledBlock, compile_rule
from snarky.instantiation.query_memory import QueryMemory


def _query() -> tuple[WitnessCacheKey, CompiledBlock, Fact]:
    rule = parse_rules(
        """
        RULE query
        WHEN
            (item value one)
        THEN
            ADD matched
        END
        """
    )[0]
    block = compile_rule(rule).block
    key: WitnessCacheKey = (block.source, ())
    fact = Fact(parse_term("(item value one)"))
    return key, block, fact


def test_query_memory_tracks_support_removals_and_cleans_watchers() -> None:
    key, block, fact = _query()
    memory = QueryMemory()

    memory.register(
        key,
        block,
        (fact,),
        use_structural_watches=False,
    )

    assert memory.affected_keys((), frozenset((fact,))) == {key}
    memory.remove(key)
    assert memory.affected_keys((), frozenset((fact,))) == set()
    assert key not in memory.witness_cache
    assert key not in memory.blocks


def test_query_memory_tracks_creation_of_a_missing_simple_witness() -> None:
    key, block, fact = _query()
    memory = QueryMemory()

    memory.register(
        key,
        block,
        None,
        use_structural_watches=False,
    )

    assert memory.affected_keys((fact,), frozenset()) == {key}


def test_query_memory_resets_revision_only_when_requested() -> None:
    memory = QueryMemory()
    memory.processed_revision = 7

    memory.clear()
    assert memory.processed_revision == 7

    memory.clear(reset_revision=True)
    assert memory.processed_revision == 0
