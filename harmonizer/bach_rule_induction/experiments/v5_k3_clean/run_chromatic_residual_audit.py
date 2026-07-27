#!/usr/bin/env python3
"""Audit empirically rare tonal choices without opening the sealed test set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_MODEL = HERE / "results/v5_7_k3_contextual_model.json"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)


def _rare_lookup(tonal_logits: np.ndarray, threshold: float) -> np.ndarray:
    if tonal_logits.shape != (4, 2, 12):
        raise ValueError("The audit requires voice-specific tonal logits")
    return np.exp(tonal_logits) < threshold


def _rare_candidate_mask(
    dataset: k3.K3Dataset,
    rare_lookup: np.ndarray,
) -> np.ndarray:
    if dataset.tonic_pcs is None or dataset.modes is None:
        raise ValueError("The audit requires tonic and mode metadata")
    relative = (dataset.candidate_pitches[None, :] - dataset.tonic_pcs[:, None]) % 12
    row_lookup = rare_lookup[dataset.voice_indices, dataset.modes]
    return np.take_along_axis(row_lookup, relative, axis=1)


def _motion_masks(dataset: k3.K3Dataset) -> dict[str, np.ndarray]:
    candidates = dataset.candidate_pitches[None, :]
    rows = np.arange(dataset.size)
    voices = dataset.voice_indices
    previous = dataset.blocks[rows, 0, voices, None]
    following = dataset.blocks[rows, 2, voices, None]
    next_attack = dataset.attacks[rows, 2, voices, None]
    incoming = candidates - previous
    outgoing = following - candidates
    incoming_step = (np.abs(incoming) >= 1) & (np.abs(incoming) <= 2)
    outgoing_step = next_attack & (np.abs(outgoing) >= 1) & (np.abs(outgoing) <= 2)
    return {
        "incoming_step": incoming_step,
        "immediate_step_resolution": outgoing_step,
        "immediate_neighbor": (incoming_step & outgoing_step & (following == previous)),
        "immediate_passing": (
            incoming_step & outgoing_step & (np.sign(incoming) == np.sign(outgoing))
        ),
        "no_incoming_step": ~incoming_step,
        "short_note_no_step_resolution": next_attack & ~outgoing_step,
    }


def _summary(
    dataset: k3.K3Dataset,
    probabilities: np.ndarray,
    mask: np.ndarray,
) -> dict[str, Any] | None:
    statistic = k3.residual_statistic(
        dataset,
        probabilities,
        mask,
        complexity=1,
        complexity_penalty=0.0,
    )
    if statistic is None:
        return None
    rows = np.arange(dataset.size)
    chosen = mask[rows, dataset.chosen_indices]
    applicable = mask.any(axis=1) | chosen
    return {
        "decisions": int(applicable.sum()),
        "pieces": int(np.unique(dataset.piece_ids[applicable]).size),
        "observed_count": int(chosen.sum()),
        "observed_rate": statistic.observed_rate,
        "expected_rate": statistic.expected_rate,
        "difference": statistic.observed_rate - statistic.expected_rate,
        "z_score": statistic.z_score,
    }


def _chosen_role_summary(
    dataset: k3.K3Dataset,
    rare_mask: np.ndarray,
    motion_masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    rows = np.arange(dataset.size)
    chosen_rare = rare_mask[rows, dataset.chosen_indices]
    rare_count = int(chosen_rare.sum())
    result: dict[str, Any] = {"rare_choices": rare_count}
    for name, mask in motion_masks.items():
        chosen_role = mask[rows, dataset.chosen_indices]
        count = int((chosen_rare & chosen_role).sum())
        result[name] = {
            "count": count,
            "share_of_rare": 0.0 if rare_count == 0 else count / rare_count,
        }
    return result


def _pitch_class_rows(
    dataset: k3.K3Dataset,
    rare_lookup: np.ndarray,
) -> list[dict[str, Any]]:
    if dataset.tonic_pcs is None or dataset.modes is None:
        raise ValueError("The audit requires tonic and mode metadata")
    relative = (dataset.chosen_pitches - dataset.tonic_pcs) % 12
    rows = []
    for voice in range(4):
        for mode in range(2):
            scope = (dataset.voice_indices == voice) & (dataset.modes == mode)
            for pitch_class in np.flatnonzero(rare_lookup[voice, mode]):
                chosen = scope & (relative == pitch_class)
                rows.append(
                    {
                        "voice": k3.VOICE_NAMES[voice],
                        "mode": "minor" if mode else "major",
                        "relative_pitch_class": int(pitch_class),
                        "count": int(chosen.sum()),
                        "pieces": int(np.unique(dataset.piece_ids[chosen]).size),
                    }
                )
    return rows


def _markdown(result: dict[str, Any]) -> str:
    overall = result["validation"]["strata"]["overall"]
    lines = [
        "# V5.8 — audit des chromaticismes résiduels",
        "",
        "Les classes dites rares sont définies mécaniquement par une fréquence",
        "d'apprentissage inférieure à "
        f"`{100 * result['experiment']['rarity_threshold']:.2f} %`,",
        "séparément pour chaque voix et chaque mode. Il ne s'agit donc pas d'une",
        "liste de notes chromatiques écrite à la main.",
        "",
        "Le taux observé est le nombre d'attaques authentiques classées rares",
        "divisé par toutes les décisions d'attaque internes des quatre voix. Comme",
        "plusieurs classes ont chacune une fréquence train inférieure au seuil,",
        "leur taux cumulé sur validation peut dépasser 2 %.",
        "",
        "Le jeu de test scellé n'est ni chargé ni consulté.",
        "",
        "## Calibration conditionnelle sur validation",
        "",
        "| Périmètre | Décisions | Observé | Attendu par V5.7 | Écart | z |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| Ensemble | {overall['decisions']} | "
            f"{100 * overall['observed_rate']:.3f} % | "
            f"{100 * overall['expected_rate']:.3f} % | "
            f"{100 * overall['difference']:+.3f} pp | "
            f"{overall['z_score']:+.2f} |"
        ),
    ]
    for group in ("voice", "metric", "mode"):
        for name, row in result["validation"]["strata"][group].items():
            lines.append(
                f"| {group}={name} | {row['decisions']} | "
                f"{100 * row['observed_rate']:.3f} % | "
                f"{100 * row['expected_rate']:.3f} % | "
                f"{100 * row['difference']:+.3f} pp | "
                f"{row['z_score']:+.2f} |"
            )
    lines.extend(
        [
            "",
            "## Formes locales des choix rares authentiques",
            "",
            "| Statut dans le noyau K3 | Nombre | Part des choix rares |",
            "|---|---:|---:|",
        ]
    )
    roles = result["validation"]["chosen_rare_roles"]
    for name, row in roles.items():
        if name == "rare_choices":
            continue
        lines.append(
            f"| `{name}` | {row['count']} | {100 * row['share_of_rare']:.2f} % |"
        )
    lines.extend(
        [
            "",
            "## Résidus des interactions candidates",
            "",
            "| Interaction | Observé | Attendu | Écart | z |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for name, row in result["validation"]["candidate_interactions"].items():
        lines.append(
            f"| `{name}` | {100 * row['observed_rate']:.3f} % | "
            f"{100 * row['expected_rate']:.3f} % | "
            f"{100 * row['difference']:+.3f} pp | {row['z_score']:+.2f} |"
        )
    lines.extend(
        [
            "",
            "## Décision méthodologique",
            "",
            result["interpretation"],
            "",
            "L'audit porte sur les choix authentiques et leurs alternatives locales.",
            "La prochaine étape séparée est une campagne Gibbs multi-chorals, qui",
            "mesurera une éventuelle amplification propre à la génération.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--rarity-threshold", type=float, default=0.02)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    model = payload["model"]
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    full = k3.load_k3_dataset(args.cache)
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    validation, removed = k3.filter_to_domain(
        validation,
        int(payload["corpus"]["candidate_min"]),
        int(payload["corpus"]["candidate_max"]),
    )
    if removed:
        raise ValueError("Validation contains choices outside the frozen train domain")
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    tonal_logits = np.asarray(model["tonal_logits"], dtype=np.float64)
    features = [k3.feature_from_model_record(rule) for rule in model["rules"]]
    weights = np.asarray([rule["weight"] for rule in model["rules"]])
    matrix = k3.feature_matrix(validation, features)
    base_scores = k3.contextual_base_scores(
        validation,
        register_logits,
        tonal_logits,
    )
    probabilities = k3.probabilities(
        validation,
        register_logits,
        matrix,
        weights,
        base_scores=base_scores,
    )
    rare_lookup = _rare_lookup(tonal_logits, args.rarity_threshold)
    rare_mask = _rare_candidate_mask(validation, rare_lookup)
    motion_masks = _motion_masks(validation)
    strata: dict[str, Any] = {
        "overall": _summary(validation, probabilities, rare_mask),
        "voice": {},
        "metric": {},
        "mode": {},
    }
    for voice, name in enumerate(k3.VOICE_NAMES):
        applies = validation.voice_indices == voice
        strata["voice"][name] = _summary(
            validation,
            probabilities,
            rare_mask & applies[:, None],
        )
    if validation.metric_levels is None or validation.modes is None:
        raise ValueError("The audit requires metric and mode metadata")
    for level in range(4):
        applies = validation.metric_levels == level
        strata["metric"][str(level)] = _summary(
            validation,
            probabilities,
            rare_mask & applies[:, None],
        )
    for mode, name in enumerate(("major", "minor")):
        applies = validation.modes == mode
        strata["mode"][name] = _summary(
            validation,
            probabilities,
            rare_mask & applies[:, None],
        )
    interactions = {
        name: _summary(validation, probabilities, rare_mask & mask)
        for name, mask in motion_masks.items()
    }
    interactions["strong_metric"] = _summary(
        validation,
        probabilities,
        rare_mask & (validation.metric_levels >= 2)[:, None],
    )
    interactions["weak_metric"] = _summary(
        validation,
        probabilities,
        rare_mask & (validation.metric_levels <= 1)[:, None],
    )
    interactions = {name: row for name, row in interactions.items() if row is not None}
    overall = strata["overall"]
    assert overall is not None
    difference = overall["difference"]
    z_score = overall["z_score"]
    if difference < -0.002 and z_score < -3.0:
        interpretation = (
            "V5.7 surestime significativement les classes rares dans ses "
            "conditionnelles : une famille de prédicats de rareté et de traitement "
            "local peut être proposée à la réinduction."
        )
    elif difference > 0.002 and z_score > 3.0:
        interpretation = (
            "V5.7 sous-estime significativement les choix rares authentiques dans "
            "ses conditionnelles. Une pénalisation chromatique globale serait donc "
            "contraire au corpus. Il faut tester si la chaîne de Gibbs amplifie ces "
            "choix ou si l'écart aperçu sur BWV 108.6 est propre à cette pièce."
        )
    else:
        interpretation = (
            "V5.7 est correctement calibré globalement sur les classes rares. Il "
            "faut tester l'hypothèse d'une amplification par la chaîne de Gibbs "
            "avant d'ajouter une règle."
        )
    result = {
        "experiment": {
            "id": "V5.8-CHROMATIC-RESIDUAL-AUDIT",
            "status": "EXPLORATORY",
            "test_loaded": False,
            "source_model": str(args.model.resolve()),
            "rarity_threshold": args.rarity_threshold,
            "rarity_definition": "train probability by voice and declared mode",
        },
        "corpus": {
            "validation_pieces": len(splits["validation"]),
            "validation_decisions": validation.size,
            "test_pieces_reserved": len(splits["test"]),
        },
        "rare_relative_pitch_classes": {
            k3.VOICE_NAMES[voice]: {
                mode_name: np.flatnonzero(rare_lookup[voice, mode]).tolist()
                for mode, mode_name in enumerate(("major", "minor"))
            }
            for voice in range(4)
        },
        "validation": {
            "strata": strata,
            "chosen_rare_roles": _chosen_role_summary(
                validation,
                rare_mask,
                motion_masks,
            ),
            "candidate_interactions": interactions,
            "rare_pitch_class_support": _pitch_class_rows(
                validation,
                rare_lookup,
            ),
        },
        "interpretation": interpretation,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "v5_8_chromatic_residual_audit.json"
    report_path = args.output_dir / "V5_8_CHROMATIC_RESIDUAL_AUDIT.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-chromatic] wrote {json_path}", flush=True)
    print(f"[k3-chromatic] wrote {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
