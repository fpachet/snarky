#!/usr/bin/env python3
"""Verify V18 Python activations and Snarky FACTOR scores are identical."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import k3
import numpy as np
import snarky_choice_bridge as bridge

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CATALOGUE = FACTOR_BASE / "v18_unanimous_full_factors.yaml"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v18_snarky_parity.json"
DEFAULT_REPORT = FACTOR_BASE / "V18_SNARKY_PARITY.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--rows", type=int, default=128)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--experiment-id",
        default="K3-V18-SNARKY-PARITY-1",
    )
    parser.add_argument("--title", default="V18 — parité du programme Snarky")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    program = bridge.load_choice_program(args.catalogue)
    full = k3.load_k3_dataset(args.context).with_domain(
        program.candidate_min,
        program.candidate_max,
    )
    indices = np.linspace(
        0,
        full.size - 1,
        min(args.rows, full.size),
        dtype=np.int64,
    )
    data = full.take(indices)
    compiled = program.evaluate(data)
    source = bridge.source_model_evaluation(data, args.catalogue)
    expected_factor_scores = np.tensordot(
        compiled.activations,
        program.weights,
        axes=([2], [0]),
    )
    snarky_factor_scores = program.snarky_factor_scores(data, compiled)
    factor_error = float(
        np.max(np.abs(expected_factor_scores - snarky_factor_scores))
    )
    local_score_error = float(
        np.max(np.abs(compiled.local_scores - source.local_scores))
    )
    probability_error = float(
        np.max(np.abs(compiled.probabilities - source.probabilities))
    )
    tolerance = 1e-12
    result = {
        "experiment": {
            "id": args.experiment_id,
            "status": "PASS"
            if max(factor_error, local_score_error, probability_error) <= tolerance
            else "FAIL",
            "test_loaded": False,
        },
        "rows": data.size,
        "alternatives_per_row": data.candidate_pitches.size,
        "factor_count": len(program.factors),
        "factor_group": program.factor_group,
        "maximum_absolute_factor_score_error": factor_error,
        "maximum_absolute_local_score_error": local_score_error,
        "maximum_absolute_probability_error": probability_error,
        "tolerance": tolerance,
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(
        "\n".join(
            [
                f"# {args.title}",
                "",
                f"- Statut : `{result['experiment']['status']}`.",
                f"- Décisions K3 : `{result['rows']}`.",
                f"- Alternatives par décision : "
                f"`{result['alternatives_per_row']}`.",
                f"- Facteurs : `{result['factor_count']}`.",
                f"- Groupe : `{result['factor_group']}`.",
                f"- Erreur maximale des contributions factorielles : "
                f"`{factor_error:.3e}`.",
                f"- Erreur maximale des scores locaux : "
                f"`{local_score_error:.3e}`.",
                f"- Erreur maximale des probabilités : "
                f"`{probability_error:.3e}`.",
                "",
                "Le générateur utilise le même évaluateur compilé pour éviter",
                "le coût d'une matérialisation de faits à chaque candidate. Ce",
                "test établit que ses activations et sommes sont exactement",
                "celles du programme `FACTOR` Snarky sur l'échantillon.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(
        f"[v18-snarky] {result['experiment']['status']} "
        f"factor_error={factor_error:.3e}",
        flush=True,
    )
    print(f"[v18-snarky] wrote {args.output}", flush=True)
    print(f"[v18-snarky] wrote {args.report}", flush=True)
    return 0 if result["experiment"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
