from pathlib import Path

import yaml

from snarky import (
    Fact,
    ForwardEngine,
    IndexedInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    Status,
    parse_rules,
    parse_term,
    render_term,
)
from snarky.serialization import load_facts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "tests/rulebases/debug"


def test_mini_snarky_reaches_expected_fixed_point_with_provenance() -> None:
    rules = parse_rules((FIXTURE_ROOT / "mini_snarky.rules").read_text())
    initial_facts = load_facts(FIXTURE_ROOT / "initial_facts.yaml")
    expected = yaml.safe_load((FIXTURE_ROOT / "expected.yaml").read_text())

    result = ForwardEngine(rules).run(initial_facts)

    expected_derived = {
        Fact(parse_term(entry["entity"]), parse_term(entry["status"]))
        for entry in expected["derived_facts"]
    }
    assert len(initial_facts) == expected["initial_fact_count"]
    assert set(result.derived_facts) == expected_derived
    assert len(result.derived_facts) == expected["derived_fact_count"]
    assert len(result.facts) == expected["fixed_point_fact_count"]

    for entry in expected["derived_facts"]:
        fact = Fact(parse_term(entry["entity"]), parse_term(entry["status"]))
        derivation = result.provenance.minimal_derivation(fact)
        assert derivation is not None
        assert derivation.rule_name == entry["rule"]
        assert result.provenance.depth(fact) == entry["proof_depth"]

    for forbidden in expected["must_not_derive"]:
        assert Fact(parse_term(forbidden), Status.VRAI) not in result.facts

    assert max(result.provenance.depth(fact) for fact in result.derived_facts) == 2


def test_status_variable_matches_explicit_false_not_absence() -> None:
    rules = parse_rules(
        """
        RULE expose
        WHEN
            alarme ' $status
        THEN
            ADD (alarme possede_statut $status)
        END
        """
    )

    result = ForwardEngine(rules).run((Fact(parse_term("alarme"), Status.FAUX),))

    rendered = {render_term(fact.entity) for fact in result.derived_facts}
    assert rendered == {"(alarme possede_statut FAUX)"}
    assert "(alarme possede_statut INEXISTANT)" not in rendered


def test_refraction_terminates_a_sterile_self_cycle() -> None:
    rules = parse_rules(
        """
        RULE identity
        WHEN
            ($x linked_to $y)
        THEN
            ADD ($x linked_to $y)
        END
        """
    )
    initial = (Fact(parse_term("(alice linked_to bob)")),)

    result = ForwardEngine(rules).run(initial)

    assert result.facts == initial
    assert result.cycles == 1
    assert result.fired_activation_count == 1


def test_indexed_strategy_preserves_relation_variables_and_statuses() -> None:
    rules = parse_rules((FIXTURE_ROOT / "mini_snarky.rules").read_text())
    initial_facts = load_facts(FIXTURE_ROOT / "initial_facts.yaml")

    naive = ForwardEngine(rules).run(initial_facts)
    indexed = ForwardEngine(
        rules,
        strategy=IndexedInstantiationStrategy(),
    ).run(initial_facts)

    assert indexed.facts == naive.facts
    assert indexed.derivations == naive.derivations

    semi_naive = ForwardEngine(
        rules,
        strategy=SemiNaiveInstantiationStrategy(),
    ).run(initial_facts)
    assert semi_naive.facts == naive.facts
    assert semi_naive.derivations == naive.derivations
