#!/usr/bin/env python3
"""Compare explicit bass and sonority metrics across controlled generations."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
TRIADIC_SIGNATURES = {
    145,  # {0, 4, 7}
    137,  # {0, 3, 7}
    265,  # {0, 3, 8}
    529,  # {0, 4, 9}
    545,  # {0, 5, 9}
    289,  # {0, 5, 8}
}
DOMINANT_SEVENTH_FIRST_INVERSION = 329  # {0, 3, 6, 8}
PAIR_DISSONANCE_CLASSES = {1, 2, 6, 10, 11}


def _bass_signature(block: np.ndarray) -> int:
    bass = int(block[3])
    result = 0
    for pitch in block:
        result |= 1 << ((int(pitch) - bass) % 12)
    return result


def _safe_rate(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else float(numerator / denominator)


def _metrics(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
) -> dict[str, float]:
    bass_times = np.flatnonzero(lattice.attacks[:, 3])
    bass = blocks[bass_times, 3]
    bass_motion = np.diff(bass)
    scale = (
        np.asarray([0, 2, 3, 5, 7, 8, 10])
        if lattice.mode
        else np.asarray([0, 2, 4, 5, 7, 9, 11])
    )
    signatures = np.asarray(
        [_bass_signature(block) for block in blocks],
        dtype=np.int16,
    )
    strong = lattice.metric_levels >= 2
    pair_dissonances = np.zeros(lattice.size, dtype=np.float64)
    for time, block in enumerate(blocks):
        pair_dissonances[time] = sum(
            abs(int(block[left]) - int(block[right])) % 12
            in PAIR_DISSONANCE_CLASSES
            for left in range(4)
            for right in range(left + 1, 4)
        )
    return {
        "bass_semitone_rate": _safe_rate(
            np.count_nonzero(np.abs(bass_motion) == 1),
            bass_motion.size,
        ),
        "bass_repeat_rate": _safe_rate(
            np.count_nonzero(bass_motion == 0),
            bass_motion.size,
        ),
        "bass_large_leap_rate": _safe_rate(
            np.count_nonzero(np.abs(bass_motion) > 4),
            bass_motion.size,
        ),
        "bass_outside_natural_scale_rate": float(
            (~np.isin((bass - lattice.tonic_pc) % 12, scale)).mean()
        ),
        "triadic_block_rate": float(
            np.isin(signatures, list(TRIADIC_SIGNATURES)).mean()
        ),
        "strong_nontriadic_rate": float(
            (~np.isin(signatures[strong], list(TRIADIC_SIGNATURES))).mean()
        ),
        "strong_pair_dissonances_per_block": float(
            pair_dissonances[strong].mean()
        ),
        "weak_pair_dissonances_per_block": float(
            pair_dissonances[~strong].mean()
        ),
        "dominant_65_strong_rate": float(
            (signatures[strong] == DOMINANT_SEVENTH_FIRST_INVERSION).mean()
        ),
        "dominant_65_weak_rate": float(
            (signatures[~strong] == DOMINANT_SEVENTH_FIRST_INVERSION).mean()
        ),
    }


def _mean_interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    standard_error = (
        0.0 if array.size < 2 else float(array.std(ddof=1) / math.sqrt(array.size))
    )
    mean = float(array.mean())
    return {
        "mean": mean,
        "ci95_low": mean - 1.96 * standard_error,
        "ci95_high": mean + 1.96 * standard_error,
    }


def _markdown(result: dict[str, Any]) -> str:
    labels = list(result["models"])
    metrics = (
        ("Demi-tons à la basse", "bass_semitone_rate", "%"),
        ("Répétitions à la basse", "bass_repeat_rate", "%"),
        ("Sauts de basse > 4 demi-tons", "bass_large_leap_rate", "%"),
        (
            "Basse hors gamme naturelle globale",
            "bass_outside_natural_scale_rate",
            "%",
        ),
        ("Blocs triadiques (6 renversements)", "triadic_block_rate", "%"),
        ("Blocs forts non triadiques", "strong_nontriadic_rate", "%"),
        (
            "Dissonances par bloc faible",
            "weak_pair_dissonances_per_block",
            "number",
        ),
        (
            "Dissonances par bloc fort",
            "strong_pair_dissonances_per_block",
            "number",
        ),
        ("{0,3,6,8} sur bloc fort", "dominant_65_strong_rate", "%"),
        ("{0,3,6,8} sur bloc faible", "dominant_65_weak_rate", "%"),
    )
    lines = [
        "# Audit génératif explicite de la basse et des sonorités",
        "",
        f"`{result['experiment']['pieces']}` chorals de validation, "
        f"`{result['experiment']['seeds_per_piece']}` graine(s), "
        f"`{result['experiment']['sweeps']}` balayages. Même soprano, rythme et "
        "blocs de bord pour Bach et chaque modèle. Test fermé.",
        "",
        "Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas",
        "donner davantage de poids aux chorals longs.",
        "",
        "| Mesure | Bach | " + " | ".join(labels) + " |",
        "|---|" + "---:|" * (len(labels) + 1),
    ]
    for description, key, format_kind in metrics:
        source = result["summary"]["Bach"][key]["mean"]
        values = [result["summary"][label][key]["mean"] for label in labels]
        if format_kind == "%":
            rendered = [f"{100 * value:.2f} %" for value in [source, *values]]
        else:
            rendered = [f"{value:.3f}" for value in [source, *values]]
        lines.append(f"| {description} | " + " | ".join(rendered) + " |")
    lines.extend(
        [
            "",
            "## Écarts appariés à Bach",
            "",
            "Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par",
            "pièce. Un intervalle recouvrant zéro ne démontre pas une différence",
            "stable dans ce petit audit.",
            "",
        ]
    )
    for label in labels:
        lines.extend([f"### {label}", ""])
        for description, key, format_kind in metrics:
            paired = result["paired_difference"][label][key]
            factor = 100 if format_kind == "%" else 1
            suffix = " pp" if format_kind == "%" else ""
            lines.append(
                f"- {description} : `{factor * paired['mean']:+.3f}{suffix}` "
                f"(IC95 `{factor * paired['ci95_low']:+.3f}` à "
                f"`{factor * paired['ci95_high']:+.3f}`)."
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        nargs="+",
        default=[
            f"V5.9={HERE / 'results/v5_9_generative_model.json'}",
            f"V5.12={HERE / 'results/v5_12_explicit_generative_model.json'}",
        ],
    )
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--seeds", default="5517")
    parser.add_argument("--sweeps", type=int, default=6)
    parser.add_argument("--max-pieces", type=int, default=10)
    parser.add_argument("--piece-offset", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    parser.add_argument(
        "--output-stem",
        default="v5_12_explicit_generation_audit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_paths = {}
    for specification in args.models:
        label, separator, path = specification.partition("=")
        if not separator or not label:
            raise ValueError("Models must use LABEL=PATH")
        model_paths[label] = Path(path)
    payloads = {
        label: json.loads(path.read_text(encoding="utf-8"))
        for label, path in model_paths.items()
    }
    reference_corpus = next(iter(payloads.values()))["corpus"]
    candidate_min = int(reference_corpus["candidate_min"])
    candidate_max = int(reference_corpus["candidate_max"])
    prepared = {}
    for label, payload in payloads.items():
        corpus = payload["corpus"]
        if (
            int(corpus["candidate_min"]) != candidate_min
            or int(corpus["candidate_max"]) != candidate_max
        ):
            raise ValueError("Compared models must share one pitch domain")
        model = payload["model"]
        prepared[label] = {
            "register_logits": np.asarray(
                model["register_logits"],
                dtype=np.float64,
            ),
            "tonal_logits": np.asarray(model["tonal_logits"], dtype=np.float64),
            "features": tuple(
                k3.feature_from_model_record(rule) for rule in model["rules"]
            ),
            "weights": np.asarray(
                [rule["weight"] for rule in model["rules"]],
                dtype=np.float64,
            ),
        }
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    piece_ids = list(splits["validation"])[
        args.piece_offset : args.piece_offset + args.max_pieces
    ]
    seeds = [int(value) for value in args.seeds.split(",") if value]
    rows = []
    for piece_number, piece_id in enumerate(piece_ids, start=1):
        print(
            f"[explicit-audit] {piece_number}/{len(piece_ids)} {piece_id}",
            flush=True,
        )
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        source_metrics = _metrics(lattice.blocks, lattice)
        generated_metrics: dict[str, dict[str, float]] = {}
        for label, model in prepared.items():
            seed_metrics = []
            for seed in seeds:
                local_seed = generative._piece_seed(piece_id, seed)
                initial = rhythmic._randomize_mutable_segments(
                    lattice.blocks,
                    lattice.attacks,
                    fixed,
                    model["register_logits"],
                    candidate_min,
                    local_seed,
                    model["tonal_logits"],
                    lattice.tonic_pc,
                    lattice.mode,
                )
                generated = k3.rhythmic_gibbs_sample(
                    initial,
                    lattice.attacks,
                    fixed,
                    candidate_min=candidate_min,
                    candidate_max=candidate_max,
                    register_logits=model["register_logits"],
                    features=model["features"],
                    weights=model["weights"],
                    sweeps=args.sweeps,
                    seed=local_seed,
                    tonal_logits=model["tonal_logits"],
                    tonic_pc=lattice.tonic_pc,
                    mode=lattice.mode,
                    metric_levels=lattice.metric_levels,
                )
                seed_metrics.append(_metrics(generated, lattice))
            generated_metrics[label] = {
                key: float(np.mean([row[key] for row in seed_metrics]))
                for key in source_metrics
            }
        rows.append(
            {
                "piece_id": piece_id,
                "Bach": source_metrics,
                **generated_metrics,
            }
        )
    summary = {
        label: {
            key: _mean_interval([row[label][key] for row in rows])
            for key in rows[0]["Bach"]
        }
        for label in ("Bach", *prepared)
    }
    paired = {
        label: {
            key: _mean_interval(
                [row[label][key] - row["Bach"][key] for row in rows]
            )
            for key in rows[0]["Bach"]
        }
        for label in prepared
    }
    result = {
        "experiment": {
            "id": "V5.12-EXPLICIT-GENERATION-AUDIT",
            "status": "EXPLORATORY",
            "test_loaded": False,
            "pieces": len(piece_ids),
            "piece_ids": piece_ids,
            "seeds": seeds,
            "seeds_per_piece": len(seeds),
            "sweeps": args.sweeps,
        },
        "models": {label: str(path.resolve()) for label, path in model_paths.items()},
        "summary": summary,
        "paired_difference": paired,
        "pieces": rows,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{args.output_stem}.json"
    report_path = args.output_dir / f"{args.output_stem.upper()}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[explicit-audit] wrote {json_path}", flush=True)
    print(f"[explicit-audit] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
