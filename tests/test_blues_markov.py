"""Frozen corpus integrity and independent first-order learning/DP checks."""

import hashlib
import json
from fractions import Fraction
from itertools import product

import pytest

from benchmarks.blues_corpus import (
    SIMPLIFICATION,
    audit_and_extract,
    training_sequences,
)
from benchmarks.blues_markov import CORPUS, reference_dp, train


def test_frozen_variants_transposition_multiplicity_and_review_map():
    corpus = json.loads(CORPUS.read_text())
    assert len(corpus["sequences"]) == 22
    assert len(corpus["changes"]) == 31
    assert corpus["simplification"] == SIMPLIFICATION
    for variant, expected_alphabet in (
        ("source_faithful", 60),
        ("paper_style_proposed", 36),
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
