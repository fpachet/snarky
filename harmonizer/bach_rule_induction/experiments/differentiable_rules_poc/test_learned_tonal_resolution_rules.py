from __future__ import annotations

import itertools
from pathlib import Path

from snarky import (
    Atom,
    Fact,
    InferenceSession,
    Number,
    Triple,
    parse_rule_groups,
)

ROOT = Path(__file__).resolve().parent
RULES_PATH = ROOT.parents[1] / "rules/learned_tonal_resolution.rules"
CANDIDATE = Atom("candidate")
STRENGTH = Atom("learned_tonal_resolution_strength")


def fact(relation: str, value: str | int) -> Fact:
    term = Number(value) if isinstance(value, int) else Atom(value)
    return Fact(Triple(CANDIDATE, Atom(relation), term))


def snarky_strength(values: tuple[bool, ...]) -> int:
    (
        major,
        alto,
        source_eleven,
        source_bass_two,
        target_bass_four,
        rises_one,
        exact_source,
        exact_target,
    ) = values
    facts = (
        fact("global_key_mode", "major" if major else "minor"),
        fact("subject_voice", "alto" if alto else "soprano"),
        fact("source_relative_class", 11 if source_eleven else 10),
        fact("source_bass_relative_class", 2 if source_bass_two else 3),
        fact("target_bass_relative_class", 4 if target_bass_four else 5),
        fact("motion_interval", 1 if rises_one else 0),
        fact(
            "source_harmonic_status",
            "exact_vii6" if exact_source else "other_source",
        ),
        fact(
            "target_harmonic_status",
            "exact_I6" if exact_target else "other_target",
        ),
    )
    session = InferenceSession(facts)
    for group in parse_rule_groups(RULES_PATH.read_text(encoding="utf-8")):
        session.run_group(group)
    strengths = {
        entity.object.value
        for derived in session.facts
        if isinstance((entity := derived.entity), Triple)
        and entity.subject == CANDIDATE
        and entity.relation == STRENGTH
        and isinstance(entity.object, Number)
    }
    return int(next(iter(strengths))) if strengths else 0


def numeric_oracle(values: tuple[bool, ...]) -> int:
    base = all(values[:6])
    exact = base and values[6] and values[7]
    return 2 if exact else 1 if base else 0


def test_compiled_rule_matches_all_256_abstract_local_states() -> None:
    for values in itertools.product((False, True), repeat=8):
        assert snarky_strength(values) == numeric_oracle(values)


def test_compiled_exact_status_has_one_strength_fact() -> None:
    assert snarky_strength((True,) * 8) == 2
