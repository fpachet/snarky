from pathlib import Path

import pytest

from snarky import (
    Fact,
    ForwardEngine,
    IndexedInstantiationStrategy,
    NaiveInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
    parse_rule_groups,
    parse_term,
)
from snarky.serialization.yaml_format import load_facts

RULEBASE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "rulebases"
    / "constraints"
    / "binary"
)


@pytest.mark.parametrize(
    "strategy",
    (
        NaiveInstantiationStrategy(),
        IndexedInstantiationStrategy(),
        SemiNaiveInstantiationStrategy(),
    ),
)
def test_binary_arc_consistency_is_strategy_independent(
    strategy: (
        NaiveInstantiationStrategy
        | IndexedInstantiationStrategy
        | SemiNaiveInstantiationStrategy
    ),
) -> None:
    groups = parse_rule_groups(
        (RULEBASE_ROOT / "rules.rules").read_text(encoding="utf-8")
    )
    session = ForwardEngine((), strategy=strategy).create_session(
        load_facts(RULEBASE_ROOT / "initial_facts.yaml")
    )

    for group in groups:
        session.run_group(group)

    for variable, value in (
        ("chain-a", "red"),
        ("chain-b", "blue"),
        ("chain-c", "red"),
        ("chain-d", "blue"),
    ):
        assert Fact(
            parse_term(f"({variable} value {value})")
        ) in session.facts
    assert Fact(
        parse_term("(two-color-chain state solved)")
    ) in session.facts

    assert Fact(
        parse_term("(triangle-b candidate red)")
    ) not in session.facts
    assert Fact(
        parse_term("(triangle-c candidate red)")
    ) not in session.facts
    for variable in ("triangle-b", "triangle-c"):
        for value in ("green", "blue"):
            assert Fact(
                parse_term(f"({variable} candidate {value})")
            ) in session.facts
    assert Fact(
        parse_term("(three-color-triangle state solved)")
    ) not in session.facts

    assert Fact(
        parse_term("(impossible-pair state contradiction)")
    ) in session.facts
    assert Fact(
        parse_term("(impossible-pair state solved)")
    ) not in session.facts
    for variable in ("impossible-left", "impossible-right"):
        assert Fact(
            parse_term(f"(impossible-pair empty_domain {variable})")
        ) in session.facts
        assert Fact(
            parse_term(f"({variable} candidate red)")
        ) not in session.facts
