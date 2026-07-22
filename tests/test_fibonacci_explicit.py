from pathlib import Path

from snarky import (
    Atom,
    Fact,
    ForwardEngine,
    IndexedInstantiationStrategy,
    Let,
    NaiveInstantiationStrategy,
    Number,
    SemiNaiveInstantiationStrategy,
    Triple,
    Variable,
    parse_rules,
    parse_term,
)
from snarky.serialization import load_facts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "tests/rulebases/fibonacci_explicit"


def test_fibonacci_explicit_builds_the_tree_and_computes_f8() -> None:
    rules = parse_rules((FIXTURE_ROOT / "fibonacci_explicit.rules").read_text())
    initial_facts = load_facts(FIXTURE_ROOT / "initial_facts.yaml")

    result = ForwardEngine(rules).run(initial_facts)

    assert len(rules) == 3
    root_result = Fact(parse_term("(racine resultat 21)"))
    assert root_result in result.facts
    assert len(result.derived_facts) == 121
    assert len(result.facts) == 122
    assert len(initial_facts) == 1
    root_derivation = result.provenance.minimal_derivation(root_result)
    assert root_derivation is not None
    assert root_derivation.substitution[Variable("somme")] == Number(21)
    assert isinstance(rules[1].actions[0], Let)
    assert isinstance(rules[2].actions[0], Let)

    calculation_facts = {
        fact for fact in result.facts if _has_relation(fact, "fibonacci")
    }
    result_facts = {
        fact for fact in result.facts if _has_relation(fact, "resultat")
    }
    assert len(calculation_facts) == 41
    assert len(result_facts) == 41
    assert sum(
        isinstance(fact.entity, Triple)
        and fact.entity.object == Number(5)
        for fact in calculation_facts
    ) == 3


def test_indexed_fibonacci_is_identical_and_examines_fewer_facts() -> None:
    rules = parse_rules((FIXTURE_ROOT / "fibonacci_explicit.rules").read_text())
    initial_facts = load_facts(FIXTURE_ROOT / "initial_facts.yaml")
    naive = NaiveInstantiationStrategy()
    indexed = IndexedInstantiationStrategy()

    naive_result = ForwardEngine(rules, strategy=naive).run(initial_facts)
    indexed_result = ForwardEngine(rules, strategy=indexed).run(initial_facts)

    assert indexed_result.facts == naive_result.facts
    assert indexed_result.derived_facts == naive_result.derived_facts
    assert indexed_result.derivations == naive_result.derivations
    assert indexed_result.cycles == naive_result.cycles
    assert indexed_result.fired_activation_count == naive_result.fired_activation_count
    assert indexed.metrics.match_attempts * 10 < naive.metrics.match_attempts


def test_semi_naive_fibonacci_preserves_full_derivations() -> None:
    rules = parse_rules((FIXTURE_ROOT / "fibonacci_explicit.rules").read_text())
    initial_facts = load_facts(FIXTURE_ROOT / "initial_facts.yaml")
    naive_result = ForwardEngine(rules).run(initial_facts)
    strategy = SemiNaiveInstantiationStrategy()

    semi_naive = ForwardEngine(rules, strategy=strategy).run(initial_facts)

    assert semi_naive.facts == naive_result.facts
    assert semi_naive.derived_facts == naive_result.derived_facts
    assert semi_naive.derivations == naive_result.derivations
    assert semi_naive.cycles == naive_result.cycles
    assert semi_naive.fired_activation_count == naive_result.fired_activation_count
    assert strategy.metrics.activations_produced == semi_naive.fired_activation_count
    assert strategy.metrics.index_builds == len(rules)


def _has_relation(fact: Fact, relation: str) -> bool:
    entity = fact.entity
    return isinstance(entity, Triple) and entity.relation == Atom(relation)
