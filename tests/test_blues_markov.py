"""Frozen corpus integrity and independent first-order learning/DP checks."""

import hashlib
import json
from fractions import Fraction
from itertools import product
from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmarks.blues_corpus import (
    BOULEZ_SIMPLIFICATION,
    SIMPLIFICATION,
    audit_and_extract,
    training_sequences,
)
from benchmarks.blues_markov import (
    BOULEZ_ALPHABET,
    CORPUS,
    blues_domains,
    native_model,
    reference_dp,
    train,
    validate_solution,
)
from snarky import Atom


def test_frozen_variants_transposition_multiplicity_and_review_map():
    corpus = json.loads(CORPUS.read_text())
    assert len(corpus["sequences"]) == 22
    assert len(corpus["changes"]) == 31
    assert corpus["simplification"] == SIMPLIFICATION
    assert corpus["boulez_simplification"] == BOULEZ_SIMPLIFICATION
    assert len(corpus["boulez_changes"]) == 34
    for variant, expected_alphabet in (
        ("source_faithful", 60),
        ("paper_style_proposed", 36),
        ("boulez_two_family_proposed", 24),
    ):
        normalized = training_sequences(corpus, variant, all_keys=False)
        augmented = training_sequences(corpus, variant, all_keys=True)
        assert len(normalized) == 22 and len(augmented) == 264
        assert all(len(sequence) == 24 for sequence in augmented)
        assert (
            len({symbol for sequence in augmented for symbol in sequence})
            == expected_alphabet
        )
        assert tuple(augmented[i * 12] for i in range(22)) == normalized
        assert tuple(tuple(s[variant]) for s in corpus["sequences"]) == normalized
    alice = next(
        s for s in corpus["sequences"] if s["transcription_id"] == "Blues_For_Alice"
    )
    assert alice["source_faithful"][:2] == ["C", "C"]
    assert alice["paper_style_proposed"][:2] == ["C7", "C7"]
    # Adding the two-family fixture must preserve both earlier corpus variants.
    old = json.loads(
        (CORPUS.parent.parent / "omnibook_blues_v1/corpus.json").read_text()
    )
    for previous, current in zip(old["sequences"], corpus["sequences"], strict=True):
        assert all(current[key] == value for key, value in previous.items())
    for change in corpus["boulez_changes"]:
        sequence = next(s for s in corpus["sequences"] if s["id"] == change["sequence"])
        position = change["position"] - 1
        assert sequence["source_faithful"][position] == change["from"]
        assert sequence["boulez_two_family_proposed"][position] == change["to"]


def test_two_family_reduction_precedes_training_and_merges_counts():
    corpus = {
        "sequences": [
            {
                "root_kind": [
                    [0, "major"],
                    [0, "dominant"],
                    [0, "half-diminished"],
                    [0, "diminished"],
                    [0, "minor"],
                ]
            }
        ]
    }
    sequences = training_sequences(corpus, "boulez_two_family_proposed", all_keys=False)
    assert sequences == (("C7", "C7", "Cm", "Cm", "Cm"),)
    source = train(sequences)
    assert source.initial == {"C7": Fraction(2, 5), "Cm": Fraction(3, 5)}
    assert source.transitions == {
        ("C7", "C7"): Fraction(1, 2),
        ("C7", "Cm"): Fraction(1, 2),
        ("Cm", "Cm"): 1,
    }
    actual = train(
        training_sequences(
            json.loads(CORPUS.read_text()), "boulez_two_family_proposed", all_keys=True
        )
    )
    assert set(actual.alphabet) == BOULEZ_ALPHABET
    assert sum(actual.initial.values()) == 1
    for symbol in actual.alphabet:
        assert sum(p for (a, _), p in actual.transitions.items() if a == symbol) == 1


@pytest.mark.parametrize("variant", ["source_faithful", "paper_style_proposed"])
def test_boulez_has_exactly_two_families_and_rejects_previous_wider_solution(variant):
    corpus = json.loads(CORPUS.read_text())
    source = train(training_sequences(corpus, variant, all_keys=True))
    assert len(BOULEZ_ALPHABET) == 24
    assert "C" not in BOULEZ_ALPHABET and "C-7b5" not in BOULEZ_ALPHABET
    assert "C7" in BOULEZ_ALPHABET and "Cm" in BOULEZ_ALPHABET
    domains = blues_domains(source, "boulez")
    assert set().union(*domains) == BOULEZ_ALPHABET
    assert (domains[0], domains[8], domains[-1]) == (("C7",), ("F7",), ("G7",))
    model = native_model(source, "boulez")
    for position, variable in enumerate(model.variables):
        assert tuple(v.name for v in variable.domain) == domains[position]
    assert len(set().union(*blues_domains(source, "ordinary"))) == len(source.alphabet)

    # Preserve original corpus probabilities; applying a hard domain restriction
    # must not renormalize transitions and thereby change sequence ranking.
    factor = model.objective.factors[1]
    assert factor.values == {
        tuple(map(Atom, pair)): p for pair, p in source.transitions.items()
    }
    previous = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "benchmarks/results"
            / "blues_first_order_2026-09-16_counter.json"
        ).read_text()
    )
    run = next(
        case["runs"][0]
        for case in previous["cases"]
        if case["variant"] == variant and case["case"] == "boulez"
    )
    names = tuple(variable.name for variable in model.variables)
    wrong_sequence = tuple(run["sequence"])
    result = SimpleNamespace(
        incumbent=SimpleNamespace(
            assignment=dict(zip(names, map(Atom, wrong_sequence), strict=True)),
            objective_value=source.score(wrong_sequence),
        )
    )
    with pytest.raises(AssertionError):
        validate_solution(source, "boulez", result, names)


def test_counts_do_not_cross_sequence_boundaries_and_initial_is_symbol_marginal():
    source = train((("a", "b", "b"), ("c", "a")))
    assert source.initial == {
        "a": Fraction(2, 5),
        "b": Fraction(2, 5),
        "c": Fraction(1, 5),
    }
    assert source.transitions == {("a", "b"): 1, ("b", "b"): 1, ("c", "a"): 1}
    assert ("b", "c") not in source.transitions


def test_exact_counter_dp_matches_brute_force():
    source = train((("a", "b", "a", "a"), ("b", "b", "a", "b")))
    domains = (("a",), source.alphabet, source.alphabet, source.alphabet, ("b",))
    for counted in (None, "b"):
        target = 2
        expected = [
            (source.score(row), row)
            for row in product(*domains)
            if counted is None or row.count(counted) == target
        ]
        optimum = reference_dp(source, domains, counted, target)
        assert optimum[0] == max(value for value, _ in expected)
        assert optimum in expected


def test_importer_rejects_bad_transposition_grid_and_source_hash(tmp_path):
    source = tmp_path / "source.xml"
    source.write_text("synthetic source for checksum validation")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    data = {
        "sequences": [
            {
                "id": str(i),
                "source_path": "source.xml",
                "source_sha256": digest,
                "time_signature": "4/4",
                "bar_count": 12,
                "duration_quarter_notes": 48,
                "tonic_pc": 5,
                "tonic": "F",
                "title": "synthetic",
                "transcription_id": str(i),
                "source_bar_range": ["1", "12"],
                "notes": "",
                "bars": [
                    {
                        "bar": b,
                        "chords": [
                            {
                                "beat": 1,
                                "duration": 4,
                                "source_notation": {"kind": "dominant", "degrees": []},
                                "root_pc": 5,
                                "root_pc_in_C": 0,
                                "bass_pc": None,
                                "bass_pc_in_C": None,
                                "pitch_classes": [5, 9, 0, 3],
                                "pitch_classes_in_C": [0, 4, 7, 10],
                                "symbol_in_C": "C7",
                            }
                        ],
                    }
                    for b in range(1, 13)
                ],
            }
            for i in range(22)
        ]
    }
    path = tmp_path / "references.json"
    path.write_text(json.dumps(data))
    assert len(audit_and_extract(path, tmp_path)["sequences"]) == 22
    chord = data["sequences"][0]["bars"][0]["chords"][0]
    chord["root_pc_in_C"] = 5
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="transposition"):
        audit_and_extract(path, tmp_path)
    chord["root_pc_in_C"] = 0
    chord["duration"] = 3
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="half-bar"):
        audit_and_extract(path, tmp_path)
    chord["duration"] = 4
    path.write_text(json.dumps(data))
    source.write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        audit_and_extract(path, tmp_path)
