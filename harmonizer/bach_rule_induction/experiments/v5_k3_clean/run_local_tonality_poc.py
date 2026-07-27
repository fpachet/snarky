#!/usr/bin/env python3
"""Fit and audit an unsupervised local-tonic HMM over K3 observations."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import k3
import local_tonality
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)


def _corpus_metrics(
    sequences: tuple[local_tonality.LocalTonalSequence, ...],
    inferences: dict[str, local_tonality.LocalTonalInference],
    profiles: np.ndarray,
    global_profiles: np.ndarray,
) -> dict[str, float]:
    state_count = sum(sequence.offsets.size for sequence in sequences)
    shifted = 0
    changes = 0
    transitions = 0
    entropy = 0.0
    local_evidence = 0.0
    fixed_global_evidence = 0.0
    for sequence in sequences:
        inference = inferences[sequence.piece_id]
        shifted += int((inference.map_tonics != sequence.global_tonic).sum())
        changes += int((inference.map_tonics[1:] != inference.map_tonics[:-1]).sum())
        transitions += max(sequence.offsets.size - 1, 0)
        entropy += float(
            -np.sum(
                inference.posterior * np.log(np.maximum(inference.posterior, 1e-12))
            )
        )
        local_evidence += inference.log_evidence
        emissions = local_tonality.emission_scores(
            sequence,
            global_profiles,
        )
        fixed_global_evidence += float(emissions[:, sequence.global_tonic].sum())
    return {
        "states": state_count,
        "shifted_state_rate": shifted / state_count,
        "local_change_rate": 0.0 if not transitions else changes / transitions,
        "posterior_entropy_normalized": entropy / (state_count * math.log(12)),
        "local_log_evidence_per_state": local_evidence / state_count,
        "fixed_global_log_evidence_per_state": (fixed_global_evidence / state_count),
        "log_evidence_gain_per_state": (local_evidence - fixed_global_evidence)
        / state_count,
    }


def _rarity_metrics(
    dataset: k3.K3Dataset,
    lookup: dict[tuple[str, float], tuple[np.ndarray, int]],
    global_logits: np.ndarray,
    local_logits: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    if dataset.tonic_pcs is None or dataset.modes is None:
        raise ValueError("Rarity comparison requires declared tonality")
    global_rare_lookup = np.exp(global_logits) < threshold
    local_rare_lookup = np.exp(local_logits) < threshold
    global_rare = 0
    local_rare = 0
    reclassified = 0
    by_voice = {
        name: {"decisions": 0, "global_rare": 0, "local_rare": 0}
        for name in k3.VOICE_NAMES
    }
    for row in range(dataset.size):
        piece_id = str(dataset.piece_ids[row])
        offset = round(float(dataset.offsets[row, 1]), 6)
        _, local_tonic = lookup[(piece_id, offset)]
        voice = int(dataset.voice_indices[row])
        mode = int(dataset.modes[row])
        pitch_class = int(dataset.chosen_pitches[row]) % 12
        global_relative = (pitch_class - int(dataset.tonic_pcs[row])) % 12
        local_relative = (pitch_class - local_tonic) % 12
        is_global_rare = bool(global_rare_lookup[voice, mode, global_relative])
        is_local_rare = bool(local_rare_lookup[voice, mode, local_relative])
        global_rare += is_global_rare
        local_rare += is_local_rare
        reclassified += is_global_rare and not is_local_rare
        voice_row = by_voice[k3.VOICE_NAMES[voice]]
        voice_row["decisions"] += 1
        voice_row["global_rare"] += int(is_global_rare)
        voice_row["local_rare"] += int(is_local_rare)
    return {
        "decisions": dataset.size,
        "global_rare_rate": global_rare / dataset.size,
        "local_rare_rate": local_rare / dataset.size,
        "globally_rare_reclassified_count": reclassified,
        "globally_rare_reclassified_share": (
            0.0 if not global_rare else reclassified / global_rare
        ),
        "by_voice": by_voice,
    }


def _markdown(result: dict[str, Any]) -> str:
    validation = result["validation"]
    rarity = validation["rarity"]
    lines = [
        "# V5.11 — statut tonal local latent",
        "",
        "Un HMM non supervisé possède douze états transposables de référence tonale.",
        "Chaque émission observe seulement les hauteurs des trois blocs K3 ; une",
        "transition locale favorise la persistance entre noyaux adjacents.",
        "Aucun accord, degré, modulation ou exemple de validation n'est fourni",
        "pendant l'apprentissage.",
        "",
        "Le mot « tonique locale » reste ici opérationnel : sans annotation",
        "musicologique, l'état peut aussi se comporter comme un centre ou une",
        "racine harmonique locale.",
        "",
        "## Ajustement",
        "",
        f"- Chorals train : `{result['corpus']['train_pieces']}`.",
        f"- Chorals validation : `{result['corpus']['validation_pieces']}`.",
        f"- Itérations EM : `{result['experiment']['iterations']}`.",
        (
            "- Probabilité de conserver le statut : "
            f"`{result['experiment']['stay_probability']:.3f}`."
        ),
        "- Test scellé non chargé.",
        "",
        "## Validation tenue à part",
        "",
        "| Mesure | Valeur |",
        "|---|---:|",
        (
            "| Gain de log-évidence par état sur tonique globale fixe | "
            f"{validation['status']['log_evidence_gain_per_state']:+.6f} |"
        ),
        (
            "| États différents de la tonique globale | "
            f"{100 * validation['status']['shifted_state_rate']:.2f} % |"
        ),
        (
            "| Changements entre états adjacents | "
            f"{100 * validation['status']['local_change_rate']:.2f} % |"
        ),
        (
            "| Entropie postérieure normalisée | "
            f"{validation['status']['posterior_entropy_normalized']:.3f} |"
        ),
        (
            "| Classes rares avec référence globale | "
            f"{100 * rarity['global_rare_rate']:.3f} % |"
        ),
        (
            "| Classes rares avec statut local | "
            f"{100 * rarity['local_rare_rate']:.3f} % |"
        ),
        (
            "| Choix globalement rares devenant localement communs | "
            f"{100 * rarity['globally_rare_reclassified_share']:.2f} % |"
        ),
        "",
        "## Lecture",
        "",
        result["interpretation"],
        "",
        "Ce POC évalue l'utilité statistique du statut. Il ne prétend pas encore",
        "que chaque état MAP correspond à une modulation analysée par un humain.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--iterations", type=int, default=15)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--stay-probability", type=float, default=0.92)
    parser.add_argument("--global-start-probability", type=float, default=0.8)
    parser.add_argument("--rarity-threshold", type=float, default=0.02)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    parser.add_argument("--output-stem", default="v5_11_local_tonality_hmm")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    full = k3.load_k3_dataset(args.cache)
    train = k3.subset_for_piece_ids(full, splits["train"])
    validation = k3.subset_for_piece_ids(full, splits["validation"])
    minimum, maximum = k3.training_domain(train)
    train, train_removed = k3.filter_to_domain(train, minimum, maximum)
    validation, validation_removed = k3.filter_to_domain(
        validation,
        minimum,
        maximum,
    )
    if train_removed or validation_removed:
        raise ValueError("Observed choices unexpectedly fall outside train domain")
    train_sequences = local_tonality.state_sequences(train)
    validation_sequences = local_tonality.state_sequences(validation)
    global_profiles = local_tonality.initialize_profiles(
        train_sequences,
        args.alpha,
    )
    profiles, train_inferences, history = local_tonality.fit_profiles(
        train_sequences,
        iterations=args.iterations,
        alpha=args.alpha,
        stay_probability=args.stay_probability,
        global_start_probability=args.global_start_probability,
    )
    validation_inferences = local_tonality.infer_corpus(
        validation_sequences,
        profiles,
        stay_probability=args.stay_probability,
        global_start_probability=args.global_start_probability,
    )
    train_lookup = local_tonality.inference_lookup(
        train_sequences,
        train_inferences,
    )
    validation_lookup = local_tonality.inference_lookup(
        validation_sequences,
        validation_inferences,
    )
    local_voice_logits = local_tonality.learn_local_voice_logits(
        train,
        train_lookup,
    )
    global_voice_logits = k3.learn_voice_tonal_logits(train)
    train_status = _corpus_metrics(
        train_sequences,
        train_inferences,
        profiles,
        global_profiles,
    )
    validation_status = _corpus_metrics(
        validation_sequences,
        validation_inferences,
        profiles,
        global_profiles,
    )
    validation_rarity = _rarity_metrics(
        validation,
        validation_lookup,
        global_voice_logits,
        local_voice_logits,
        args.rarity_threshold,
    )
    useful = (
        validation_status["log_evidence_gain_per_state"] > 0
        and validation_rarity["globally_rare_reclassified_share"] > 0.1
        and validation_status["posterior_entropy_normalized"] < 0.8
    )
    interpretation = (
        "Le statut latent améliore l'évidence tenue à part et requalifie une "
        "part substantielle des choix globalement rares sans devenir indéterminé. "
        "Il peut être ajouté comme fait local candidat à la prochaine induction."
        if useful
        else "Le statut latent ne satisfait pas encore simultanément évidence, "
        "reclassification et certitude. Il doit être recalibré avant d'entrer "
        "dans le langage de règles."
    )
    result = {
        "experiment": {
            "id": "V5.11-LOCAL-TONALITY-HMM",
            "status": "EXPLORATORY",
            "test_loaded": False,
            "validation_used_for_fit": False,
            "iterations": args.iterations,
            "alpha": args.alpha,
            "stay_probability": args.stay_probability,
            "global_start_probability": args.global_start_probability,
            "rarity_threshold": args.rarity_threshold,
        },
        "corpus": {
            "train_pieces": len(train_sequences),
            "validation_pieces": len(validation_sequences),
            "test_pieces_reserved": len(splits["test"]),
            "train_states": train_status["states"],
            "validation_states": validation_status["states"],
        },
        "model": {
            "profiles": profiles.tolist(),
            "global_profiles": global_profiles.tolist(),
            "local_voice_logits": local_voice_logits.tolist(),
            "history": history,
        },
        "train": {"status": train_status},
        "validation": {
            "status": validation_status,
            "rarity": validation_rarity,
        },
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
    print(f"[k3-v5.11] wrote {json_path}")
    print(f"[k3-v5.11] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
