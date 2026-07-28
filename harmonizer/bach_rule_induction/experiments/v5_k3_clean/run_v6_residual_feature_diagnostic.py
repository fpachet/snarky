#!/usr/bin/env python3
"""Rank missing readable K3 factors from multiseed V6 residual states."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import k3
import numpy as np
import refit_v6_generative_weights as refit
import run_generative_moment_calibration as generative
import run_v5_12_explicit_calibration as explicit
import run_v6_factor_controllability as control

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v6_train64_multimetric_iteration2_model.json"
DEFAULT_CONTROLS = tuple(
    FACTOR_BASE / f"v6_iteration3_seed{seed}_control.json"
    for seed in (10103, 20207, 30313)
)
DEFAULT_CACHES = tuple(
    HERE / f"work/v6_iteration3_seed{seed}_chains.npz"
    for seed in (10103, 20207, 30313)
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v6_iteration3_residual_feature_diagnostic.json"
DEFAULT_REPORT = FACTOR_BASE / "V6_ITERATION3_RESIDUAL_FEATURE_DIAGNOSTIC.md"


def _select_robust(
    records: list[dict[str, Any]],
    features: tuple[k3.FeatureSpec, ...],
    *,
    per_family: int,
    minimum_rate: float,
    minimum_abs_z: float,
) -> list[int]:
    """Select strongest sign-stable residuals with balanced gradient signs."""

    selected = []
    for family in ("bass_motion", "vertical_context", "sonority_transition"):
        admissible = [
            index
            for index, (record, feature) in enumerate(
                zip(records, features, strict=True)
            )
            if explicit._family(feature) == family
            and record["seed_sign_agreement"]
            and abs(record["z_score"]) >= minimum_abs_z
            and max(record["bach_rate"], record["gibbs_rate"]) >= minimum_rate
        ]
        positive = sorted(
            (index for index in admissible if records[index]["gradient"] > 0),
            key=lambda index: (records[index]["selection_score"], features[index].key),
            reverse=True,
        )
        negative = sorted(
            (index for index in admissible if records[index]["gradient"] < 0),
            key=lambda index: (records[index]["selection_score"], features[index].key),
            reverse=True,
        )
        positive_budget = per_family // 2
        selected.extend(positive[:positive_budget])
        selected.extend(negative[: per_family - positive_budget])
    return sorted(
        selected,
        key=lambda index: (records[index]["selection_score"], features[index].key),
        reverse=True,
    )


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V6 — diagnostic des facteurs résiduels après l'itération 2",
        "",
        "Ce diagnostic ne réapprend pas encore le modèle. Il réutilise les états",
        "finaux des trois campagnes multigraines et compare, pièce par pièce, les",
        "activations de Bach à celles de Gibbs. Le test réservé reste fermé.",
        "",
        "## Protocole",
        "",
        f"- Pièces de train : `{result['experiment']['pieces']}`.",
        f"- Graines : `{result['experiment']['seeds']}`.",
        f"- États générés par pièce : `{result['experiment']['states_per_piece']}`.",
        f"- Candidates lisibles : `{result['experiment']['candidate_count']}`.",
        (
            "- Seuil : signe identique sur les trois graines, "
            f"`|z| ≥ {result['experiment']['minimum_abs_z']}`."
        ),
        "",
        "## Candidates prioritaires",
        "",
        "| Famille | Description | Bach | Gibbs | Gradient | z |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for record in result["selected"]:
        lines.append(
            f"| `{record['family']}` | {record['description']} | "
            f"{record['bach_rate']:.4f} | {record['gibbs_rate']:.4f} | "
            f"{record['gradient']:+.4f} | {record['z_score']:+.2f} |"
        )
    lines.extend(
        [
            "",
            "Ces candidates sont des hypothèses de structure, pas encore des",
            "règles acceptées. La prochaine expérience doit les ajouter par petits",
            "lots, réapprendre leurs poids sur train et exiger un gain simultané à",
            "6 et 30 sweeps avant toute promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--controls", type=Path, nargs="+", default=DEFAULT_CONTROLS)
    parser.add_argument("--chain-caches", type=Path, nargs="+", default=DEFAULT_CACHES)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--minimum-support", type=int, default=20)
    parser.add_argument("--minimum-piece-support", type=int, default=5)
    parser.add_argument("--minimum-rate", type=float, default=0.003)
    parser.add_argument("--minimum-abs-z", type=float, default=2.0)
    parser.add_argument("--per-family", type=int, default=6)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if len(args.controls) != len(args.chain_caches) or len(args.controls) < 2:
        raise ValueError("One chain cache is required per independent control run")
    model_payload = json.loads(args.model.read_text(encoding="utf-8"))
    control_payloads = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.controls
    ]
    reference = control_payloads[0]["experiment"]
    piece_ids = tuple(reference["piece_ids"])
    for payload in control_payloads:
        experiment = payload["experiment"]
        if (
            experiment["test_loaded"]
            or tuple(experiment["piece_ids"]) != piece_ids
            or experiment["source_model"] != str(args.model.resolve())
        ):
            raise ValueError("Residual runs do not share one train-only contract")
    corpus = model_payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    selected_features = tuple(
        k3.feature_from_model_record(rule)
        for rule in model_payload["model"]["rules"]
    )
    selected_keys = {feature.key for feature in selected_features}

    states_by_seed = []
    seeds = []
    for payload, path in zip(
        control_payloads,
        args.chain_caches,
        strict=True,
    ):
        states, metadata = control._load_chain_cache(path)
        if metadata["weights_sha256"] != control.hashlib.sha256(
            np.asarray(
                [
                    rule["weight"]
                    for rule in model_payload["model"]["rules"]
                ],
                dtype=np.float64,
            ).tobytes()
        ).hexdigest():
            raise ValueError("Residual cache was sampled from different weights")
        states_by_seed.append(states)
        seeds.append(int(payload["experiment"]["seed"]))

    representatives: dict[str, generative.Chain] = {}
    generated_by_piece_seed: dict[
        tuple[str, int],
        list[generative.Chain],
    ] = defaultdict(list)
    all_generated = []
    for piece_id in piece_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        fixed = np.zeros_like(lattice.blocks, dtype=bool)
        fixed[:, 0] = True
        fixed[0, :] = True
        fixed[-1, :] = True
        representatives[piece_id] = generative.Chain(
            piece_id,
            lattice,
            lattice.blocks.copy(),
            fixed,
        )
        for seed_index, states in enumerate(states_by_seed):
            for replica in range(reference["chains_per_piece"]):
                chain_id = f"{piece_id}#replica={replica}"
                blocks = states[chain_id]
                k3.validated_attack_segments(blocks, lattice.attacks)
                chain = generative.Chain(
                    piece_id,
                    lattice,
                    blocks,
                    fixed,
                )
                generated_by_piece_seed[(piece_id, seed_index)].append(chain)
                all_generated.append(chain)

    candidates = explicit._candidate_catalogue(
        all_generated,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        selected_keys=selected_keys,
        minimum_support=args.minimum_support,
        minimum_piece_support=args.minimum_piece_support,
        allow_adjustments=False,
    )
    source_rates = np.stack(
        [
            refit.factor_rates(
                representatives[piece_id],
                representatives[piece_id].lattice.blocks,
                candidates,
                candidate_min,
                candidate_max,
            )
            for piece_id in piece_ids
        ]
    )
    generated_seed_rates = np.empty(
        (len(seeds), len(piece_ids), len(candidates)),
        dtype=np.float64,
    )
    for seed_index in range(len(seeds)):
        for piece_index, piece_id in enumerate(piece_ids):
            chains = generated_by_piece_seed[(piece_id, seed_index)]
            generated_seed_rates[seed_index, piece_index] = np.stack(
                [
                    refit.factor_rates(
                        chain,
                        chain.blocks,
                        candidates,
                        candidate_min,
                        candidate_max,
                    )
                    for chain in chains
                ]
            ).mean(axis=0)
    generated_rates = generated_seed_rates.mean(axis=0)
    records = explicit._paired_statistics(
        source_rates,
        generated_rates,
        candidates,
    )
    gradients_by_seed = (
        source_rates[None, :, :] - generated_seed_rates
    ).mean(axis=1)
    for index, record in enumerate(records):
        seed_gradients = gradients_by_seed[:, index]
        record["seed_gradients"] = seed_gradients.tolist()
        record["seed_sign_agreement"] = bool(
            np.all(np.sign(seed_gradients) == np.sign(seed_gradients[0]))
        )
    selected_indices = _select_robust(
        records,
        candidates,
        per_family=args.per_family,
        minimum_rate=args.minimum_rate,
        minimum_abs_z=args.minimum_abs_z,
    )
    selected = [
        {
            **records[index],
            "family": explicit._family(candidates[index]),
            "description": explicit._description(candidates[index]),
        }
        for index in selected_indices
    ]
    result = {
        "experiment": {
            "id": "F-K3-V6-ITERATION3-RESIDUAL-FEATURE-DIAGNOSTIC",
            "status": "TRAIN_ONLY_STRUCTURE_DIAGNOSTIC",
            "source_model": str(args.model.resolve()),
            "control_inputs": [str(path.resolve()) for path in args.controls],
            "chain_caches": [str(path.resolve()) for path in args.chain_caches],
            "pieces": len(piece_ids),
            "piece_ids": list(piece_ids),
            "seeds": seeds,
            "states_per_piece": len(seeds) * reference["chains_per_piece"],
            "candidate_count": len(candidates),
            "selected_count": len(selected),
            "minimum_abs_z": args.minimum_abs_z,
            "minimum_rate": args.minimum_rate,
            "test_loaded": False,
            "weights_changed": False,
            "factor_structure_changed": False,
        },
        "selected": selected,
        "candidates": [
            {
                **record,
                "family": explicit._family(feature),
                "description": explicit._description(feature),
            }
            for feature, record in zip(candidates, records, strict=True)
        ],
    }
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v6-residual] wrote {args.output}", flush=True)
    print(f"[v6-residual] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
