#!/usr/bin/env python3
"""Measure rare tonal attacks across controlled validation-set generations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "results/v5_7_k3_contextual_model.json"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


def _score_path(directory: Path, piece_id: str) -> Path:
    stem = piece_id.split("/", 1)[-1]
    matches = [
        path
        for suffix in (".mxl", ".xml")
        if (path := directory / f"{stem}{suffix}").exists()
    ]
    if len(matches) != 1:
        raise FileNotFoundError(f"{piece_id}: expected one materialized score")
    return matches[0]


def _piece_seed(piece_id: str, seed: int) -> int:
    digest = hashlib.sha256(f"{piece_id}:{seed}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _rare_lookup(tonal_logits: np.ndarray, threshold: float) -> np.ndarray:
    if tonal_logits.shape != (4, 2, 12):
        raise ValueError("The audit requires voice-specific tonal logits")
    return np.exp(tonal_logits) < threshold


def _rare_counts(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
    rare_lookup: np.ndarray,
    voices: tuple[int, ...],
) -> tuple[int, int, dict[str, int]]:
    rare = 0
    attacks = 0
    by_voice = {k3.VOICE_NAMES[voice]: 0 for voice in voices}
    for voice in voices:
        voice_attacks = lattice.attacks[:, voice]
        relative = (blocks[:, voice] - lattice.tonic_pc) % 12
        voice_rare = voice_attacks & rare_lookup[voice, lattice.mode, relative]
        count = int(voice_rare.sum())
        rare += count
        attacks += int(voice_attacks.sum())
        by_voice[k3.VOICE_NAMES[voice]] = count
    return rare, attacks, by_voice


def _mean_interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    mean = float(array.mean())
    standard_error = (
        0.0 if array.size < 2 else float(array.std(ddof=1) / math.sqrt(array.size))
    )
    return {
        "mean": mean,
        "ci95_low": mean - 1.96 * standard_error,
        "ci95_high": mean + 1.96 * standard_error,
    }


def _markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    model_version = result["experiment"].get("model_version", "V5.7").replace("_", ".")
    lines = [
        f"# {model_version} — audit Gibbs multi-chorals",
        "",
        f"`{result['experiment']['pieces']}` chorals de validation,",
        f"`{result['experiment']['seeds_per_piece']}` graines par choral et",
        f"`{result['experiment']['sweeps']}` balayages. Le soprano, le rythme et",
        "les blocs de bord restent authentiques. Le test scellé reste fermé.",
        "",
        "Les taux principaux ne portent que sur alto, ténor et basse, c'est-à-dire",
        "les voix effectivement régénérées.",
        "",
        "| Mesure | Bach | Généré V5.7 |",
        "|---|---:|---:|",
        (
            f"| Taux pondéré de classes rares | "
            f"{100 * summary['source_weighted_rate']:.3f} % | "
            f"{100 * summary['generated_weighted_rate']:.3f} % |"
        ),
        (
            f"| Moyenne par pièce | "
            f"{100 * summary['source_piece_rate']['mean']:.3f} % | "
            f"{100 * summary['generated_piece_rate']['mean']:.3f} % |"
        ),
        "",
        "Différence généré − Bach, calculée après agrégation des graines par pièce :",
        f"`{100 * summary['paired_piece_difference']['mean']:+.3f}` points",
        "(IC95 "
        f"`{100 * summary['paired_piece_difference']['ci95_low']:+.3f}` à "
        f"`{100 * summary['paired_piece_difference']['ci95_high']:+.3f}`).",
        "",
        "## Détail par pièce",
        "",
        "| Choral | Mode | Bach | Généré | Écart |",
        "|---|---|---:|---:|---:|",
    ]
    for row in result["pieces"]:
        lines.append(
            f"| `{row['piece_id']}` | {row['mode']} | "
            f"{100 * row['source_rate']:.2f} % | "
            f"{100 * row['generated_rate']:.2f} % | "
            f"{100 * row['difference']:+.2f} pp |"
        )
    lines.extend(
        [
            "",
            "## Interprétation",
            "",
            result["interpretation"],
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--seeds", default="5517,5518,5519")
    parser.add_argument("--sweeps", type=int, default=12)
    parser.add_argument("--max-pieces", type=int)
    parser.add_argument("--rarity-threshold", type=float, default=0.02)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    parser.add_argument(
        "--output-stem",
        default="v5_8_multichoral_generation_audit",
    )
    parser.add_argument(
        "--render-json",
        type=Path,
        help="Regenerate only the Markdown report from an existing result.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.render_json is not None:
        result = json.loads(args.render_json.read_text(encoding="utf-8"))
        report_path = args.output_dir / f"{args.output_stem.upper()}.md"
        report_path.write_text(_markdown(result), encoding="utf-8")
        print(f"[k3-multichoral] wrote {report_path}", flush=True)
        return 0
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    model_version = str(payload["experiment"]["id"]).split("-", 1)[0]
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    piece_ids = list(splits["validation"])
    if args.max_pieces is not None:
        piece_ids = piece_ids[: args.max_pieces]
    seeds = [int(value) for value in args.seeds.split(",") if value]
    model = payload["model"]
    corpus = payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    rare_lookup = _rare_lookup(tonal_logits, args.rarity_threshold)
    features = [k3.feature_from_model_record(rule) for rule in model["rules"]]
    weights = np.asarray([rule["weight"] for rule in model["rules"]])
    piece_rows = []
    for piece_number, piece_id in enumerate(piece_ids, start=1):
        path = _score_path(args.scores, piece_id)
        lattice = k3.extract_piece_lattice(path, piece_id)
        if lattice.blocks.min() < candidate_min or lattice.blocks.max() > candidate_max:
            raise ValueError(f"{piece_id}: source pitches outside train domain")
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        source_rare, source_attacks, _ = _rare_counts(
            lattice.blocks,
            lattice,
            rare_lookup,
            (1, 2, 3),
        )
        generated_rare = 0
        generated_attacks = 0
        seed_rates = []
        for seed in seeds:
            local_seed = _piece_seed(piece_id, seed)
            initial = rhythmic._randomize_mutable_segments(
                lattice.blocks,
                lattice.attacks,
                fixed,
                register_logits,
                candidate_min,
                local_seed,
                tonal_logits,
                lattice.tonic_pc,
                lattice.mode,
            )
            generated = k3.rhythmic_gibbs_sample(
                initial,
                lattice.attacks,
                fixed,
                candidate_min=candidate_min,
                candidate_max=candidate_max,
                register_logits=register_logits,
                features=features,
                weights=weights,
                sweeps=args.sweeps,
                seed=local_seed,
                tonal_logits=tonal_logits,
                tonic_pc=lattice.tonic_pc,
                mode=lattice.mode,
                metric_levels=lattice.metric_levels,
            )
            rare, attacks, _ = _rare_counts(
                generated,
                lattice,
                rare_lookup,
                (1, 2, 3),
            )
            generated_rare += rare
            generated_attacks += attacks
            seed_rates.append(rare / attacks)
        source_rate = source_rare / source_attacks
        generated_rate = generated_rare / generated_attacks
        piece_rows.append(
            {
                "piece_id": piece_id,
                "mode": "minor" if lattice.mode else "major",
                "source_rare": source_rare,
                "source_attacks": source_attacks,
                "source_rate": source_rate,
                "generated_rare": generated_rare,
                "generated_attacks": generated_attacks,
                "generated_rate": generated_rate,
                "seed_rates": seed_rates,
                "difference": generated_rate - source_rate,
            }
        )
        print(
            f"[k3-multichoral] {piece_number}/{len(piece_ids)} {piece_id}: "
            f"Bach={100 * source_rate:.2f}% generated={100 * generated_rate:.2f}%",
            flush=True,
        )
    source_rare = sum(row["source_rare"] for row in piece_rows)
    source_attacks = sum(row["source_attacks"] for row in piece_rows)
    generated_rare = sum(row["generated_rare"] for row in piece_rows)
    generated_attacks = sum(row["generated_attacks"] for row in piece_rows)
    source_rates = [row["source_rate"] for row in piece_rows]
    generated_rates = [row["generated_rate"] for row in piece_rows]
    differences = [row["difference"] for row in piece_rows]
    difference_interval = _mean_interval(differences)
    if difference_interval["ci95_low"] > 0:
        interpretation = (
            "La génération amplifie les classes rares de manière générale. Le "
            "prochain catalogue devra représenter leurs conditions locales de "
            "licence — notamment approche conjointe, métrique et résolution — "
            "plutôt que leur appliquer une interdiction globale."
        )
    elif difference_interval["ci95_high"] < 0:
        interpretation = (
            "La génération produit moins de classes rares que Bach. L'anomalie "
            "de BWV 108.6 est locale ; une pénalisation chromatique globale serait "
            "injustifiée."
        )
    else:
        interpretation = (
            "L'écart moyen n'est pas distinguable de zéro entre chorals. "
            "L'anomalie de BWV 108.6 doit être traitée comme un résidu local et "
            "non comme une loi chromatique générale."
        )
    result = {
        "experiment": {
            "id": "V5.8-MULTICHORAL-GENERATION-AUDIT",
            "status": "EXPLORATORY",
            "test_loaded": False,
            "source_split": "validation",
            "pieces": len(piece_rows),
            "seeds": seeds,
            "seeds_per_piece": len(seeds),
            "sweeps": args.sweeps,
            "fixed_voice": "Soprano",
            "rarity_threshold": args.rarity_threshold,
            "model_version": model_version,
            "source_model": str(args.model.resolve()),
        },
        "summary": {
            "source_weighted_rate": source_rare / source_attacks,
            "generated_weighted_rate": generated_rare / generated_attacks,
            "source_piece_rate": _mean_interval(source_rates),
            "generated_piece_rate": _mean_interval(generated_rates),
            "paired_piece_difference": difference_interval,
        },
        "pieces": piece_rows,
        "interpretation": interpretation,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{args.output_stem}.json"
    report_path = args.output_dir / f"{args.output_stem.upper()}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-multichoral] wrote {json_path}", flush=True)
    print(f"[k3-multichoral] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
