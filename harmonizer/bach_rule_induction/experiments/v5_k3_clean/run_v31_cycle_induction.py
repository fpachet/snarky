#!/usr/bin/env python3
"""Learn voice-specific ABA/ABAB factors above the confirmed V29 model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import grouped_maxent
import k3
import numpy as np
import run_exact_factor_reinduction as exact
import run_generative_moment_calibration as generative
import run_v18_explanatory_sparse_induction as sparse
import yaml
from run_v21_grouped_transition import paired_improvement, select_from_protocol
from run_v23_metric_bass_harmony import _point

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_CONFIG = FACTOR_BASE / "v31_attack_cycle_config.yaml"
DEFAULT_CACHE = HERE / "work/k3-exact-v29-selected-32x50.npz"
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v31_attack_cycle_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V31_ATTACK_CYCLE_MODEL.md"

CYCLE_STATUS_NAMES = tuple(
    f"{voice.lower()}__{status}"
    for voice in k3.VOICE_NAMES
    for status in ("first_aba_return", "continued_abab_cycle")
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _cycle_rows(
    piece_ids: list[str],
    scores: Path,
    candidates: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    matrices = []
    voices = []
    for piece_id in piece_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(scores, piece_id),
            piece_id,
        )
        history: list[list[int]] = [[] for _ in range(4)]
        piece_rows = []
        piece_voices = []
        for start, end, voice in k3.attack_segments(lattice.attacks):
            eligible = voice != 0 and start > 0 and end < lattice.size
            if eligible:
                row = np.zeros(
                    (candidates.size, len(CYCLE_STATUS_NAMES)),
                    dtype=np.uint8,
                )
                previous = history[voice]
                if len(previous) >= 2:
                    returns = (candidates == previous[-2]) & (
                        candidates != previous[-1]
                    )
                    continued = (
                        len(previous) >= 3
                        and previous[-1] == previous[-3]
                        and previous[-1] != previous[-2]
                    )
                    row[:, voice * 2 + int(continued)] = returns
                piece_rows.append(row)
                piece_voices.append(voice)
            history[voice].append(int(lattice.blocks[start, voice]))
        matrices.append(np.asarray(piece_rows, dtype=np.uint8))
        voices.extend(piece_voices)
    return np.concatenate(matrices), np.asarray(voices, dtype=np.int8)


def _base_split(archive: Any, name: str) -> dict[str, np.ndarray]:
    return {
        "factors": archive[f"{name}_factors"],
        "chosen": archive[f"{name}_chosen"],
        "piece_ids": archive[f"{name}_piece_ids"],
        "voices": archive[f"{name}_voices"],
        "modes": archive[f"{name}_modes"],
        "tonics": archive[f"{name}_tonics"],
    }


def _with_cycles(
    split: dict[str, np.ndarray],
    cycles: np.ndarray,
) -> dict[str, np.ndarray]:
    if cycles.shape[:2] != split["factors"].shape[:2]:
        raise ValueError("Cycle rows and exact K3 cache disagree")
    return {**split, "factors": np.concatenate((split["factors"], cycles), axis=2)}


def _take_pieces(
    split: dict[str, np.ndarray],
    piece_ids: list[str],
) -> dict[str, np.ndarray]:
    mask = np.isin(split["piece_ids"], np.asarray(piece_ids))
    return {key: value[mask] for key, value in split.items()}


def _initial(model: dict[str, Any]) -> exact.Parameters:
    payload = model["model"]
    return exact.Parameters(
        register=np.asarray(payload["register_logits"], dtype=np.float64),
        tonal=np.asarray(payload["tonal_logits"], dtype=np.float64),
        factor_weights=np.asarray(
            [float(rule["weight"]) for rule in payload["rules"]],
            dtype=np.float64,
        ),
    )


def _clean(point: dict[str, Any]) -> None:
    point.pop("_parameters", None)


def _markdown(result: dict[str, Any]) -> str:
    selected = result["selection"]
    confirmation = result["confirmation"]
    lines = [
        "# V31 — induction des cycles de deux notes",
        "",
        "Huit facteurs sont appris conjointement : premier retour `ABA` et",
        "continuation `ABAB`, séparément pour chaque voix. L'historique ne",
        "compte que les attaques ; les tenues sont exclues.",
        "",
        "| Candidat | Gain découverte | IC 95 % | Pièces + |",
        "|---|---:|---:|---:|",
    ]
    for index, point in enumerate(result["path"]):
        if index == 0:
            lines.append(f"| {point['label']} | — | — | — |")
            continue
        paired = point["paired_vs_baseline"]
        low, high = paired["bootstrap_95_interval"]
        lines.append(
            f"| {point['label']} | {paired['mean_improvement']:+.6f} | "
            f"[{low:+.6f}, {high:+.6f}] | "
            f"{paired['positive_piece_count']}/"
            f"{len(paired['piece_ids'])} |"
        )
    lines.extend(
        [
            "",
            f"- Sélection découverte : `{selected['selected_label']}`.",
            f"- Groupe retenu : `{str(selected['group_retained']).lower()}`.",
            f"- Confirmation 40 pièces : "
            f"`{confirmation['mean_improvement']:+.6f}` ; IC 95 % "
            f"`[{confirmation['bootstrap_95_interval'][0]:+.6f}, "
            f"{confirmation['bootstrap_95_interval'][1]:+.6f}]` ; "
            f"`{confirmation['positive_piece_count']}/"
            f"{len(confirmation['piece_ids'])}` pièces.",
            "",
            "| Statut | Poids |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{name}` | {weight:+.6f} |"
        for name, weight in zip(
            CYCLE_STATUS_NAMES,
            result["selected_cycle_weights"],
            strict=True,
        )
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    baseline = json.loads(
        (FACTOR_BASE / config["baseline_model"]).read_text(encoding="utf-8")
    )
    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    train_ids = list(metadata["train_ids"])
    validation_ids = list(metadata["validation_ids"])
    discovery_count = int(config["selection"]["discovery_validation_pieces"])
    confirmation_count = int(config["selection"]["confirmation_validation_pieces"])
    discovery_ids = validation_ids[:discovery_count]
    confirmation_ids = validation_ids[
        discovery_count : discovery_count + confirmation_count
    ]

    train_base = _base_split(archive, "train")
    validation_base = _base_split(archive, "validation")
    train_cycles, train_voices = _cycle_rows(train_ids, args.scores, candidates)
    validation_cycles, validation_voices = _cycle_rows(
        validation_ids,
        args.scores,
        candidates,
    )
    if not np.array_equal(train_voices, train_base["voices"]):
        raise ValueError("Train cycle row order differs from exact cache")
    if not np.array_equal(validation_voices, validation_base["voices"]):
        raise ValueError("Validation cycle row order differs from exact cache")
    train = _with_cycles(train_base, train_cycles)
    validation = _with_cycles(validation_base, validation_cycles)
    discovery_base = _take_pieces(validation_base, discovery_ids)
    discovery = _take_pieces(validation, discovery_ids)
    confirmation_base = _take_pieces(validation_base, confirmation_ids)
    confirmation = _take_pieces(validation, confirmation_ids)

    estimation = config["estimation"]
    initial = _initial(baseline)
    baseline_count = initial.factor_weights.size
    cycle_count = len(CYCLE_STATUS_NAMES)
    complexities = np.asarray(
        [
            k3.feature_from_model_record(rule).complexity
            for rule in baseline["model"]["rules"]
        ],
        dtype=np.float64,
    )
    baseline_l1 = (
        float(estimation["l1_baseline_by_clause_complexity"]) * complexities
    )
    prefit, _ = grouped_maxent.fit_grouped(
        train_base,
        discovery_base,
        candidates,
        initial,
        steps=int(estimation["steps_baseline_prefit"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
    )
    baseline_parameters, baseline_fit = grouped_maxent.fit_grouped(
        train_base,
        discovery_base,
        candidates,
        prefit,
        steps=int(estimation["steps_comparison"]),
        learning_rate=float(estimation["learning_rate"]),
        l1=baseline_l1,
        l2=float(estimation["l2"]),
        groups=(),
    )
    baseline_point = _point(
        label="socle V29 réajusté",
        penalty=None,
        train=train_base,
        validation=discovery_base,
        candidates=candidates,
        parameters=baseline_parameters,
        group_indices={},
        fit=baseline_fit,
    )
    group_indices = np.arange(baseline_count, baseline_count + cycle_count)
    initial_full = exact.Parameters(
        prefit.register.copy(),
        prefit.tonal.copy(),
        np.concatenate((prefit.factor_weights, np.zeros(cycle_count))),
    )
    l1 = np.concatenate(
        (
            baseline_l1,
            np.full(cycle_count, float(config["group"]["l1_inside_group"])),
        )
    )
    path = [{**baseline_point, "_parameters": baseline_parameters.copy()}]
    for index, penalty in enumerate(
        map(float, estimation["group_penalty_path"]),
        start=1,
    ):
        group = grouped_maxent.GroupPenalty(
            name=config["group"]["id"],
            indices=group_indices,
            strength=penalty,
            scale_by_sqrt_size=bool(
                config["group"]["l2_group_scaled_by_sqrt_size"]
            ),
        )
        parameters, fit = grouped_maxent.fit_grouped(
            train,
            discovery,
            candidates,
            initial_full,
            steps=int(estimation["steps_comparison"]),
            learning_rate=float(estimation["learning_rate"]),
            l1=l1,
            l2=float(estimation["l2"]),
            groups=(group,),
        )
        point = _point(
            label=f"groupe V31 cycles λ={penalty:g}",
            penalty=penalty,
            train=train,
            validation=discovery,
            candidates=candidates,
            parameters=parameters,
            group_indices={config["group"]["id"]: group_indices},
            fit=fit,
        )
        point["paired_vs_baseline"] = paired_improvement(
            baseline_point["validation_piece_nll"],
            point["validation_piece_nll"],
            seed=int(config["selection"]["paired_bootstrap_seed"]) + index,
            resamples=int(config["selection"]["paired_bootstrap_resamples"]),
        )
        path.append(point)
        print(
            f"[v31-cycle] lambda={penalty:g} "
            f"gain={point['paired_vs_baseline']['mean_improvement']:+.6f}",
            flush=True,
        )
    selected_index, _, best_index = select_from_protocol(path, config["selection"])
    candidate_index = selected_index if selected_index else best_index
    selected_parameters = path[candidate_index]["_parameters"]
    _, _, baseline_confirmation = sparse._piece_nll(
        confirmation_base,
        candidates,
        baseline_parameters,
    )
    _, _, candidate_confirmation = sparse._piece_nll(
        confirmation,
        candidates,
        selected_parameters,
    )
    confirmation_paired = paired_improvement(
        baseline_confirmation,
        candidate_confirmation,
        seed=int(config["selection"]["paired_bootstrap_seed"]) + 100,
        resamples=int(config["selection"]["paired_bootstrap_resamples"]),
    )
    confirmed = (
        selected_index != 0
        and confirmation_paired["bootstrap_95_interval"][0] > 0
        and confirmation_paired["positive_piece_count"]
        / len(confirmation_paired["piece_ids"])
        >= float(config["selection"]["minimum_positive_piece_fraction"])
    )
    cycle_weights = (
        selected_parameters.factor_weights[group_indices]
        if selected_parameters.factor_weights.size > baseline_count
        else np.zeros(cycle_count)
    )
    result = {
        "experiment": {
            "id": config["id"],
            "status": "CONFIRMED" if confirmed else "REJECTED",
            "train_pieces": len(train_ids),
            "discovery_validation_pieces": len(discovery_ids),
            "confirmation_validation_pieces": len(confirmation_ids),
            "generated_bwv108_6_used_for_weight_learning": False,
            "test_loaded": False,
        },
        "selection": {
            "selected_index": selected_index,
            "best_index": best_index,
            "candidate_index": candidate_index,
            "selected_label": path[selected_index]["label"],
            "candidate_label": path[candidate_index]["label"],
            "group_retained": selected_index != 0,
            "confirmed": confirmed,
        },
        "path": path,
        "confirmation": confirmation_paired,
        "cycle_status_names": list(CYCLE_STATUS_NAMES),
        "selected_cycle_weights": cycle_weights.tolist(),
        "selected_parameters": {
            "register_logits": selected_parameters.register.tolist(),
            "tonal_logits": selected_parameters.tonal.tolist(),
            "factor_weights": selected_parameters.factor_weights.tolist(),
        },
    }
    for point in path:
        _clean(point)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(
        f"[v31-cycle] selected={path[selected_index]['label']} "
        f"confirmed={confirmed} confirmation="
        f"{confirmation_paired['mean_improvement']:+.6f}",
        flush=True,
    )
    print(f"[v31-cycle] wrote {args.output}", flush=True)
    print(f"[v31-cycle] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
