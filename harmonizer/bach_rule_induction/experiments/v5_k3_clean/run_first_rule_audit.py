#!/usr/bin/env python3
"""Audit whether V5.1 rule 1 is a threshold or a graded leap preference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = HERE / "work/k3-train-validation-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)


def _load_splits(path: Path) -> dict[str, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    source = payload.get("grouped_split", payload)
    return {name: list(source[name]) for name in ("train", "validation", "test")}


def _datasets(
    cache_path: Path,
    splits_path: Path,
) -> tuple[k3.K3Dataset, k3.K3Dataset, dict[str, list[str]]]:
    data = k3.load_k3_dataset(cache_path)
    splits = _load_splits(splits_path)
    train = k3.subset_for_piece_ids(data, splits["train"])
    validation = k3.subset_for_piece_ids(data, splits["validation"])
    minimum, maximum = k3.training_domain(train)
    train, train_removed = k3.filter_to_domain(train, minimum, maximum)
    validation, validation_removed = k3.filter_to_domain(validation, minimum, maximum)
    if train_removed or validation_removed:
        raise ValueError("K3 audit unexpectedly removed observed choices")
    return train, validation, splits


def _bin_distribution(
    dataset: k3.K3Dataset,
    probabilities: np.ndarray,
    sizes: np.ndarray,
) -> list[dict[str, Any]]:
    rows = np.arange(dataset.size)
    chosen_sizes = sizes[rows, dataset.chosen_indices]
    records = []
    for lower in range(13):
        if lower < 12:
            mask = sizes == lower
            label = str(lower)
        else:
            mask = sizes >= lower
            label = "12+"
        observed = (
            float(np.mean(chosen_sizes == lower))
            if lower < 12
            else float(np.mean(chosen_sizes >= lower))
        )
        expected = float(np.mean(np.sum(probabilities * mask, axis=1)))
        records.append(
            {
                "bin": label,
                "observed_rate": observed,
                "expected_rate": expected,
                "observed_expected_ratio": observed / max(expected, 1e-12),
            }
        )
    return records


def _representations(sizes: np.ndarray) -> dict[str, np.ndarray]:
    scale = 12.0
    return {
        "single_threshold_gt_2": (sizes > 2)[:, :, None].astype(np.float32),
        "two_thresholds_gt_2_gt_7": np.stack((sizes > 2, sizes > 7), axis=2).astype(
            np.float32
        ),
        "linear_step_size": (sizes / scale)[:, :, None].astype(np.float32),
        "clipped_linear_at_12": (np.minimum(sizes, 12) / scale)[:, :, None].astype(
            np.float32
        ),
        "hinge_after_2": (np.maximum(sizes - 2, 0) / scale)[:, :, None].astype(
            np.float32
        ),
        "categorical_0_to_11_and_12_plus": np.stack(
            [sizes == value for value in range(12)] + [sizes >= 12],
            axis=2,
        ).astype(np.float32),
    }


def _fit_representations(
    train: k3.K3Dataset,
    validation: k3.K3Dataset,
    register_logits: np.ndarray,
    train_sizes: np.ndarray,
    validation_sizes: np.ndarray,
    *,
    max_steps: int,
    learning_rate: float,
    l1: float,
) -> list[dict[str, Any]]:
    train_representations = _representations(train_sizes)
    validation_representations = _representations(validation_sizes)
    records = []
    for name, train_matrix in train_representations.items():
        validation_matrix = validation_representations[name]
        weights, diagnostics = k3.fit_weights(
            train,
            validation,
            register_logits,
            train_matrix,
            validation_matrix,
            l1=l1,
            max_steps=max_steps,
            learning_rate=learning_rate,
        )
        records.append(
            {
                "representation": name,
                "parameter_count": int(weights.size),
                "weights": weights.tolist(),
                "train_nll": k3.conditional_nll(
                    train, register_logits, train_matrix, weights
                ),
                "validation_nll": k3.conditional_nll(
                    validation, register_logits, validation_matrix, weights
                ),
                "fit": diagnostics,
            }
        )
    return sorted(records, key=lambda record: record["validation_nll"])


def _threshold_scan(
    dataset: k3.K3Dataset,
    probabilities: np.ndarray,
) -> list[dict[str, Any]]:
    records = []
    for threshold in range(13):
        feature = k3.FeatureSpec(
            "any_voice_adjacent_step_gt",
            -1,
            value=threshold,
        )
        statistic = k3.residual_statistic(
            dataset,
            probabilities,
            k3.feature_mask(dataset, feature),
            complexity=1,
            complexity_penalty=0.0,
        )
        if statistic is None:
            continue
        records.append(
            {
                "threshold": threshold,
                "gradient": statistic.gradient,
                "z_score": statistic.z_score,
                "approximate_nll_gain": statistic.approximate_nll_gain,
                "observed_rate": statistic.observed_rate,
                "expected_rate": statistic.expected_rate,
            }
        )
    return records


def _voice_breakdown(
    dataset: k3.K3Dataset,
    probabilities: np.ndarray,
    sizes: np.ndarray,
) -> list[dict[str, Any]]:
    rows = np.arange(dataset.size)
    voices = dataset.voice_indices
    chosen = dataset.chosen_pitches
    previous = dataset.blocks[rows, 0, voices]
    following = dataset.blocks[rows, 2, voices]
    next_attack = dataset.attacks[rows, 2, voices]
    chosen_sizes = sizes[rows, dataset.chosen_indices]
    records = []
    for voice, name in enumerate(k3.VOICE_NAMES):
        selected = voices == voice
        selected_next = selected & next_attack
        records.append(
            {
                "voice": name,
                "decisions": int(selected.sum()),
                "maximum_gt_2_rate": float(np.mean(chosen_sizes[selected] > 2)),
                "maximum_gt_2_expected_rate": float(
                    np.mean(
                        np.sum(
                            probabilities[selected] * (sizes[selected] > 2),
                            axis=1,
                        )
                    )
                ),
                "exactly_2_rate": float(np.mean(chosen_sizes[selected] == 2)),
                "incoming_gt_2_rate": float(
                    np.mean(np.abs(chosen[selected] - previous[selected]) > 2)
                ),
                "next_attack_fraction": float(np.mean(next_attack[selected])),
                "outgoing_gt_2_given_next_attack": float(
                    np.mean(
                        np.abs(following[selected_next] - chosen[selected_next]) > 2
                    )
                ),
            }
        )
    return records


def _markdown(result: dict[str, Any]) -> str:
    baseline = result["baseline"]
    lines = [
        "# V5.2 — audit de la première règle K3",
        "",
        "## Question",
        "",
        "Le seuil `> 2` représente-t-il une frontière musicale, ou seulement une",
        "approximation compacte d'une préférence graduée pour les petits pas ?",
        "",
        "Cette règle est souple : elle modifie les odds, mais n'interdit aucun",
        "candidat. Les choix authentiques qui l'activent restent conservés.",
        "",
        "## Scan des seuils sur le train",
        "",
        "| Seuil | Taux Bach | Taux attendu | z | gain NLL approximatif |",
        "|---:|---:|---:|---:|---:|",
    ]
    for record in result["threshold_scan_train"]:
        lines.append(
            f"| > {record['threshold']} | {record['observed_rate']:.4f} | "
            f"{record['expected_rate']:.4f} | {record['z_score']:+.2f} | "
            f"{record['approximate_nll_gain']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Comparaison des paramétrisations",
            "",
            f"NLL validation du registre seul : `{baseline['validation_nll']:.6f}`.",
            "",
            "| Représentation | Paramètres | NLL train | NLL validation | "
            "Gain validation |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for record in result["representations"]:
        lines.append(
            f"| `{record['representation']}` | {record['parameter_count']} | "
            f"{record['train_nll']:.6f} | {record['validation_nll']:.6f} | "
            f"{baseline['validation_nll'] - record['validation_nll']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Distribution exacte sur validation",
            "",
            "| Taille maximale | Taux Bach | Taux attendu par le registre | Ratio |",
            "|---:|---:|---:|---:|",
        ]
    )
    for record in result["exact_distribution_validation"]:
        lines.append(
            f"| {record['bin']} | {record['observed_rate']:.4f} | "
            f"{record['expected_rate']:.4f} | "
            f"{record['observed_expected_ratio']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Décomposition par voix sur validation",
            "",
            "| Voix | max > 2 Bach | max > 2 attendu | exactement 2 | "
            "entrée > 2 | sortie > 2 si attaque |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for record in result["voice_breakdown_validation"]:
        lines.append(
            f"| {record['voice']} | {record['maximum_gt_2_rate']:.4f} | "
            f"{record['maximum_gt_2_expected_rate']:.4f} | "
            f"{record['exactly_2_rate']:.4f} | "
            f"{record['incoming_gt_2_rate']:.4f} | "
            f"{record['outgoing_gt_2_given_next_attack']:.4f} |"
        )
    best = result["representations"][0]
    threshold = next(
        record
        for record in result["representations"]
        if record["representation"] == "single_threshold_gt_2"
    )
    linear = next(
        record
        for record in result["representations"]
        if record["representation"] == "linear_step_size"
    )
    exact_two = result["exact_distribution_validation"][2]
    exact_three = result["exact_distribution_validation"][3]
    lines.extend(
        [
            "",
            "## Lecture",
            "",
            (
                f"La meilleure représentation de cet audit est "
                f"`{best['representation']}` avec "
                f"{best['parameter_count']} paramètre(s)."
            ),
            (
                "Son avantage de validation sur le seuil simple est "
                f"`{threshold['validation_nll'] - best['validation_nll']:.6f}` NLL."
            ),
            "",
            (
                "À complexité égale, le seuil simple bat la pente linéaire de "
                f"`{linear['validation_nll'] - threshold['validation_nll']:.6f}` "
                "NLL."
            ),
            (
                f"Le ratio observé/attendu passe de "
                f"`{exact_two['observed_expected_ratio']:.3f}` pour deux "
                f"demi-tons à `{exact_three['observed_expected_ratio']:.3f}` "
                "pour trois."
            ),
            "",
            "Les quatre voix montrent la même direction, avec davantage de sauts",
            "à la basse. Les données soutiennent donc une frontière **souple**",
            "après le ton : `PREFER mouvement ≤ 2`, et non `FORBID mouvement > 2`.",
            "La seconde colonne `> 7` représente une pénalité graduée additionnelle.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--l1", type=float, default=0.001)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    train, validation, splits = _datasets(args.cache, args.splits)
    register_logits = k3.learn_register_logits(train)
    train_probabilities = k3.probabilities(train, register_logits)
    validation_probabilities = k3.probabilities(validation, register_logits)
    train_sizes = k3.adjacent_step_sizes(train)
    validation_sizes = k3.adjacent_step_sizes(validation)
    result = {
        "experiment": {
            "id": "V5.2-FIRST-RULE-AUDIT",
            "test_loaded": False,
            "max_steps": args.max_steps,
            "learning_rate": args.learning_rate,
            "l1": args.l1,
        },
        "corpus": {
            "train_pieces": len(splits["train"]),
            "validation_pieces": len(splits["validation"]),
            "test_pieces_reserved": len(splits["test"]),
            "train_decisions": train.size,
            "validation_decisions": validation.size,
        },
        "baseline": {
            "train_nll": k3.conditional_nll(train, register_logits),
            "validation_nll": k3.conditional_nll(validation, register_logits),
        },
        "threshold_scan_train": _threshold_scan(train, train_probabilities),
        "threshold_scan_validation": _threshold_scan(
            validation, validation_probabilities
        ),
        "exact_distribution_train": _bin_distribution(
            train, train_probabilities, train_sizes
        ),
        "exact_distribution_validation": _bin_distribution(
            validation, validation_probabilities, validation_sizes
        ),
        "voice_breakdown_validation": _voice_breakdown(
            validation, validation_probabilities, validation_sizes
        ),
        "representations": _fit_representations(
            train,
            validation,
            register_logits,
            train_sizes,
            validation_sizes,
            max_steps=args.max_steps,
            learning_rate=args.learning_rate,
            l1=args.l1,
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_2_first_rule_audit.json"
    report_path = args.output_dir / "V5_2_FIRST_RULE_AUDIT.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-audit] wrote {json_path}", flush=True)
    print(f"[k3-audit] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
