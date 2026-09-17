from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import run_deepbach_tonal_audit as audit

ROOT = Path(__file__).resolve().parent


def toy_vocabulary() -> list[dict[int, str]]:
    return [
        {0: "F4", 1: "G4", 2: "__"},
        {0: "B3", 1: "C4", 2: "__", 3: "B3"},
        {0: "F3", 1: "E3", 2: "__"},
        {0: "D3", 1: "E3", 2: "__"},
    ]


def test_decode_and_audit_find_exact_resolution() -> None:
    sequence = np.asarray(
        [
            [0, 0, 0, 0],
            [1, 1, 1, 1],
        ]
    )
    sounding, attacks = audit.decode_sequence(sequence, toy_vocabulary())
    result = audit.audit_decoded_sequence(sounding, attacks)
    assert result["proxy_opportunities"] == 1
    assert result["proxy_resolutions"] == 1
    assert result["exact_opportunities"] == 1
    assert result["exact_resolutions"] == 1


def test_nonresolution_is_preserved_as_deepbach_violation() -> None:
    sequence = np.asarray(
        [
            [0, 0, 0, 0],
            [1, 3, 1, 1],
        ]
    )
    sounding, attacks = audit.decode_sequence(sequence, toy_vocabulary())
    result = audit.audit_decoded_sequence(sounding, attacks)
    assert result["proxy_opportunities"] == 1
    assert result["proxy_resolutions"] == 0
    assert len(result["violations"]) == 1


def test_canonical_free_generations_report_zero_support_not_zero_error() -> None:
    result = json.loads(
        (ROOT / "results/v3_9_deepbach_tonal_audit.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["aggregate"]["generation_count"] == 2
    assert result["aggregate"]["eligible_alto_attacks"] == 101
    assert result["aggregate"]["proxy_opportunities"] == 0
    assert result["aggregate"]["proxy_resolution_rate"] is None
