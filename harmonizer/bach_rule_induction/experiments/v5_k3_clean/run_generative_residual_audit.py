#!/usr/bin/env python3
"""Audit unselected rare-tone licences after V5.9 generative calibration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "results/v5_9_generative_model.json"
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"


def _description(feature: k3.FeatureSpec) -> str:
    if feature.kind == "rare_tonal_bass_pcset":
        mode_index, signature = divmod(int(feature.second_value), 4096)
        pitch_classes = [
            pitch_class for pitch_class in range(12) if signature & (1 << pitch_class)
        ]
        mode = "mineur" if mode_index else "majeur"
        return (
            f"empreinte verticale {pitch_classes}, "
            f"{k3.VOICE_NAMES[feature.target_voice]}, {mode}"
        )
    status = {
        "rare_tonal_class": "classe rare",
        "rare_tonal_incoming_step": "approche par pas",
        "rare_tonal_leap_arrival": "arrivée sans pas",
        "rare_tonal_immediate_step_resolution": "résolution immédiate par pas",
        "rare_tonal_short_no_step_resolution": "note courte sans résolution",
        "rare_tonal_immediate_neighbor": "broderie immédiate",
        "rare_tonal_immediate_passing": "passage immédiat",
        "rare_tonal_weak_metric": "niveau métrique faible",
        "rare_tonal_strong_metric": "niveau métrique fort",
    }[feature.kind]
    mode = "mineur" if feature.second_value else "majeur"
    return f"{status}, {k3.VOICE_NAMES[feature.target_voice]}, {mode}"


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V5.10 — audit résiduel des licences chromatiques",
        "",
        "Après gel des huit pénalités V5.9, les statuts non sélectionnés sont",
        "réévalués sur 16 chorals du train avec de nouvelles chaînes Gibbs.",
        "Le test et la validation ne sont pas consultés.",
        "",
        "Un gradient positif signifie que Bach emploie le statut davantage que le",
        "Gibbs : il s'agit d'une licence positive candidate.",
        "",
        "## Plus forts gradients positifs",
        "",
        "| Statut | Bach | Gibbs | Gradient | z |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["positive"][:12]:
        feature = k3.feature_from_model_record(row)
        lines.append(
            f"| {_description(feature)} | {100 * row['bach_rate']:.3f} % | "
            f"{100 * row['gibbs_rate']:.3f} % | "
            f"{100 * row['gradient']:+.3f} pp | {row['z_score']:+.2f} |"
        )
    lines.extend(
        [
            "",
            "## Plus forts gradients négatifs",
            "",
            "| Statut | Bach | Gibbs | Gradient | z |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["negative"][:12]:
        feature = k3.feature_from_model_record(row)
        lines.append(
            f"| {_description(feature)} | {100 * row['bach_rate']:.3f} % | "
            f"{100 * row['gibbs_rate']:.3f} % | "
            f"{100 * row['gradient']:+.3f} pp | {row['z_score']:+.2f} |"
        )
    lines.extend(["", "## Décision", "", result["interpretation"], ""])
    return "\n".join(lines)


def _interpretation(result: dict[str, Any]) -> str:
    count = result["credible_positive_count"]
    if count:
        return (
            f"`{count}` licences positives dépassent simultanément `+0,5` "
            "point et `z=2`. Un second tour de contraste peut les ajouter."
        )
    if result.get("vertical_candidate_count", 0):
        return (
            "Aucune licence positive n'est assez stable, même parmi les "
            f"`{result['vertical_candidate_count']}` interactions avec une "
            "empreinte verticale relative à la basse. La prochaine feature "
            "doit être un statut tonal local latent sur les trois blocs, et non "
            "une nouvelle pénalisation chromatique."
        )
    return (
        "Aucune licence positive n'est assez stable avec le vocabulaire actuel. "
        "Il faut croiser la rareté avec une empreinte verticale locale avant un "
        "nouveau calibrage."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--train-pieces", type=int, default=16)
    parser.add_argument("--rarity-threshold", type=float, default=0.02)
    parser.add_argument("--vertical-min-support", type=int, default=20)
    parser.add_argument("--vertical-min-piece-support", type=int, default=5)
    parser.add_argument("--burn-in-sweeps", type=int, default=6)
    parser.add_argument("--seed", type=int, default=5910)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    parser.add_argument("--render-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.render_json is not None:
        result = json.loads(args.render_json.read_text(encoding="utf-8"))
        result["interpretation"] = _interpretation(result)
        json_path = args.output_dir / "v5_10_generative_residual_audit.json"
        report_path = args.output_dir / "V5_10_GENERATIVE_RESIDUAL_AUDIT.md"
        json_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        report_path.write_text(_markdown(result), encoding="utf-8")
        print(f"[k3-v5.10] wrote {json_path}")
        print(f"[k3-v5.10] wrote {report_path}")
        return 0
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(
        splits["train"],
        key=generative._stable_order,
    )[: args.train_pieces]
    model = payload["model"]
    corpus = payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    base_features = tuple(k3.feature_from_model_record(rule) for rule in model["rules"])
    base_weights = np.asarray([rule["weight"] for rule in model["rules"]])
    selected_keys = {feature.key for feature in base_features}
    full = k3.load_k3_dataset(args.cache)
    train = k3.subset_for_piece_ids(full, splits["train"])
    train, removed = k3.filter_to_domain(
        train,
        candidate_min,
        candidate_max,
    )
    if removed:
        raise ValueError("Train choices unexpectedly fall outside its domain")
    motion_candidates = tuple(
        feature
        for feature in k3.rare_tonal_feature_catalogue(
            train,
            args.rarity_threshold,
            voices=(1, 2, 3),
        )
        if feature.key not in selected_keys
    )
    vertical_candidates = k3.rare_tonal_vertical_feature_catalogue(
        train,
        args.rarity_threshold,
        voices=(1, 2, 3),
        minimum_support=args.vertical_min_support,
        minimum_piece_support=args.vertical_min_piece_support,
    )
    candidates = (*motion_candidates, *vertical_candidates)
    chains = []
    for piece_id in train_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        initial = rhythmic._randomize_mutable_segments(
            lattice.blocks,
            lattice.attacks,
            fixed,
            register_logits,
            candidate_min,
            generative._piece_seed(piece_id, args.seed),
            tonal_logits,
            lattice.tonic_pc,
            lattice.mode,
        )
        chains.append(generative.Chain(piece_id, lattice, initial, fixed))
    source_rates = np.stack(
        [
            generative._feature_rates(
                chain,
                chain.lattice.blocks,
                candidates,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    )
    generative._sample_chains(
        chains,
        base_features,
        base_weights,
        (),
        np.asarray([], dtype=np.float64),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        register_logits=register_logits,
        tonal_logits=tonal_logits,
        sweeps=args.burn_in_sweeps,
        seed=args.seed + 1,
    )
    generated_rates = np.stack(
        [
            generative._feature_rates(
                chain,
                chain.blocks,
                candidates,
                candidate_min,
                candidate_max,
            )
            for chain in chains
        ]
    )
    statistics = generative._paired_statistics(
        source_rates,
        generated_rates,
        candidates,
    )
    positive = sorted(
        (row for row in statistics if row["gradient"] > 0),
        key=lambda row: (row["selection_score"], row["feature"]["key"]),
        reverse=True,
    )
    negative = sorted(
        (row for row in statistics if row["gradient"] < 0),
        key=lambda row: (row["selection_score"], row["feature"]["key"]),
        reverse=True,
    )
    credible_positive = [
        row for row in positive if row["gradient"] >= 0.005 and row["z_score"] >= 2.0
    ]
    result = {
        "experiment": {
            "id": "V5.10-GENERATIVE-RESIDUAL-AUDIT",
            "status": "EXPLORATORY",
            "test_loaded": False,
            "validation_loaded": False,
            "source_model": str(args.model.resolve()),
            "train_pieces": len(train_ids),
            "burn_in_sweeps": args.burn_in_sweeps,
            "seed": args.seed,
        },
        "candidate_count": len(candidates),
        "motion_candidate_count": len(motion_candidates),
        "vertical_candidate_count": len(vertical_candidates),
        "credible_positive_count": len(credible_positive),
        "positive": positive,
        "negative": negative,
        "interpretation": "",
    }
    result["interpretation"] = _interpretation(result)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_10_generative_residual_audit.json"
    report_path = args.output_dir / "V5_10_GENERATIVE_RESIDUAL_AUDIT.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-v5.10] wrote {json_path}")
    print(f"[k3-v5.10] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
