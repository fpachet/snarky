#!/usr/bin/env python3
"""Localize V12 residuals by voice pair, metric, motion, and tonal context."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_generative_moment_calibration as generative
import run_rhythmic_gibbs as rhythmic

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = (
    HERE
    / "../../factor_bases/k3_v6_induced/v12_exact_hybrid_iteration2_model.json"
)
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
PAIR_DISSONANCE_CLASSES = {1, 2, 6, 10, 11}
VOICE_PAIRS = tuple(
    (left, right)
    for left in range(4)
    for right in range(left + 1, 4)
)


def _pair_name(left: int, right: int) -> str:
    return f"{k3.VOICE_NAMES[left]}–{k3.VOICE_NAMES[right]}"


def _add(counter: Counter[str], key: str, condition: bool) -> None:
    counter[key] += int(condition)


def _context_counts(
    blocks: np.ndarray,
    lattice: k3.RhythmicLattice,
) -> dict[str, dict[str, int]]:
    vertical_numerators: Counter[str] = Counter()
    vertical_denominators: Counter[str] = Counter()
    status_numerators: Counter[str] = Counter()
    status_denominators: Counter[str] = Counter()
    bass_numerators: Counter[str] = Counter()
    bass_denominators: Counter[str] = Counter()
    bass_transitions: Counter[str] = Counter()

    for time, block in enumerate(blocks):
        strength = "strong" if lattice.metric_levels[time] >= 2 else "weak"
        for left, right in VOICE_PAIRS:
            pair = _pair_name(left, right)
            context = f"{pair}|{strength}"
            vertical_denominators[context] += 1
            interval_class = abs(int(block[left]) - int(block[right])) % 12
            if interval_class not in PAIR_DISSONANCE_CLASSES:
                continue
            vertical_numerators[context] += 1
            status_denominators[context] += 1
            statuses = {
                "one_voice_held": not (
                    lattice.attacks[time, left]
                    and lattice.attacks[time, right]
                ),
                "step_resolved": False,
                "passing": False,
                "neighbor": False,
            }
            for voice in (left, right):
                if time + 1 >= lattice.size:
                    continue
                outgoing = int(blocks[time + 1, voice]) - int(block[voice])
                outgoing_step = (
                    lattice.attacks[time + 1, voice]
                    and 1 <= abs(outgoing) <= 2
                )
                statuses["step_resolved"] |= bool(outgoing_step)
                if time == 0 or not lattice.attacks[time, voice]:
                    continue
                incoming = int(block[voice]) - int(blocks[time - 1, voice])
                incoming_step = 1 <= abs(incoming) <= 2
                statuses["passing"] |= bool(
                    incoming_step
                    and outgoing_step
                    and np.sign(incoming) == np.sign(outgoing)
                )
                statuses["neighbor"] |= bool(
                    incoming_step
                    and outgoing_step
                    and blocks[time + 1, voice] == blocks[time - 1, voice]
                )
            statuses["unresolved_nonornamental"] = not (
                statuses["step_resolved"]
                or statuses["passing"]
                or statuses["neighbor"]
            )
            for status, active in statuses.items():
                _add(status_numerators, f"{context}|{status}", active)

    scale = (
        np.asarray([0, 2, 3, 5, 7, 8, 10])
        if lattice.mode
        else np.asarray([0, 2, 4, 5, 7, 9, 11])
    )
    bass_times = np.flatnonzero(lattice.attacks[:, 3])
    for previous_time, time in zip(bass_times[:-1], bass_times[1:], strict=True):
        previous = int(blocks[previous_time, 3])
        current = int(blocks[time, 3])
        motion = current - previous
        strength = "strong" if lattice.metric_levels[time] >= 2 else "weak"
        outside = (current - lattice.tonic_pc) % 12 not in scale
        for key, active in {
            f"semitone|{strength}": abs(motion) == 1,
            f"large_leap|{strength}": abs(motion) > 4,
            f"outside_arrival|{strength}": outside,
            f"outside_after_large_leap|{strength}": outside and abs(motion) > 4,
            f"ascending_large_leap|{strength}": motion > 4,
            f"descending_large_leap|{strength}": motion < -4,
        }.items():
            bass_denominators[key] += 1
            _add(bass_numerators, key, active)
        transition = (
            f"{(previous - lattice.tonic_pc) % 12}"
            f"→{(current - lattice.tonic_pc) % 12}|{strength}"
        )
        bass_transitions[transition] += 1

    return {
        "vertical_numerators": dict(vertical_numerators),
        "vertical_denominators": dict(vertical_denominators),
        "status_numerators": dict(status_numerators),
        "status_denominators": dict(status_denominators),
        "bass_numerators": dict(bass_numerators),
        "bass_denominators": dict(bass_denominators),
        "bass_transitions": dict(bass_transitions),
        "bass_transition_total": {"all": max(0, len(bass_times) - 1)},
    }


def _generated_counts(
    task: tuple[
        k3.RhythmicLattice,
        dict[str, Any],
        int,
        int,
        int,
        int,
    ],
) -> tuple[str, dict[str, dict[str, int]]]:
    lattice, model, candidate_min, candidate_max, seed, sweeps = task
    fixed = np.zeros_like(lattice.blocks, dtype=bool)
    fixed[:, 0] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    local_seed = generative._piece_seed(lattice.piece_id, seed)
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
        sweeps=sweeps,
        seed=local_seed,
        tonal_logits=model["tonal_logits"],
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        metric_levels=lattice.metric_levels,
    )
    return lattice.piece_id, _context_counts(generated, lattice)


def _merge(
    records: list[dict[str, dict[str, int]]],
) -> dict[str, Counter[str]]:
    keys = records[0]
    return {
        key: sum((Counter(record[key]) for record in records), Counter())
        for key in keys
    }


def _rate_rows(
    source: dict[str, Counter[str]],
    generated: dict[str, Counter[str]],
    numerator_key: str,
    denominator_key: str,
) -> list[dict[str, Any]]:
    keys = sorted(
        set(source[numerator_key])
        | set(generated[numerator_key])
        | set(source[denominator_key])
        | set(generated[denominator_key])
    )
    rows = []
    for key in keys:
        source_denominator_key = key
        generated_denominator_key = key
        if numerator_key == "status_numerators":
            source_denominator_key = "|".join(key.split("|")[:2])
            generated_denominator_key = source_denominator_key
        source_denominator = source[denominator_key][source_denominator_key]
        generated_denominator = generated[denominator_key][
            generated_denominator_key
        ]
        source_rate = (
            0.0
            if source_denominator == 0
            else source[numerator_key][key] / source_denominator
        )
        generated_rate = (
            0.0
            if generated_denominator == 0
            else generated[numerator_key][key] / generated_denominator
        )
        rows.append(
            {
                "key": key,
                "bach_rate": source_rate,
                "generated_rate": generated_rate,
                "delta": generated_rate - source_rate,
                "bach_count": source[numerator_key][key],
                "generated_count": generated[numerator_key][key],
            }
        )
    return rows


def _transition_rows(
    source: dict[str, Counter[str]],
    generated: dict[str, Counter[str]],
) -> list[dict[str, Any]]:
    source_total = source["bass_transition_total"]["all"]
    generated_total = generated["bass_transition_total"]["all"]
    rows = []
    for key in sorted(
        set(source["bass_transitions"]) | set(generated["bass_transitions"])
    ):
        bach_rate = source["bass_transitions"][key] / source_total
        generated_rate = generated["bass_transitions"][key] / generated_total
        rows.append(
            {
                "key": key,
                "bach_rate": bach_rate,
                "generated_rate": generated_rate,
                "delta": generated_rate - bach_rate,
                "bach_count": source["bass_transitions"][key],
                "generated_count": generated["bass_transitions"][key],
            }
        )
    return rows


def _table(lines: list[str], rows: list[dict[str, Any]], limit: int) -> None:
    lines.extend(
        [
            "| Contexte | Bach | V12.2 | Écart |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in sorted(rows, key=lambda item: item["delta"], reverse=True)[:limit]:
        lines.append(
            f"| `{row['key']}` | {100 * row['bach_rate']:.2f} % | "
            f"{100 * row['generated_rate']:.2f} % | "
            f"{100 * row['delta']:+.2f} pp |"
        )


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V12.3 — localisation des résidus contextuels",
        "",
        f"`{result['experiment']['train_pieces']}` chorals de train, "
        f"`{result['experiment']['seeds_per_piece']}` graines et "
        f"`{result['experiment']['sweeps']}` sweeps. Le test et la validation "
        "restent fermés.",
        "",
        "Les tableaux classent les contextes par excès `V12.2 − Bach`. Ils ne",
        "définissent pas encore des règles : ils localisent les interactions que",
        "le prochain catalogue devra rendre disponibles à l'induction.",
        "",
        "## Intervalles dissonants par paire et niveau métrique",
        "",
    ]
    _table(lines, result["vertical_pair_metric"], 12)
    lines.extend(
        [
            "",
            "## Statuts des occurrences dissonantes",
            "",
        ]
    )
    _table(lines, result["vertical_status"], 15)
    lines.extend(
        [
            "",
            "## Mouvements de basse",
            "",
        ]
    )
    _table(lines, result["bass_context"], 12)
    lines.extend(
        [
            "",
            "## Transitions tonales de basse les plus surproduites",
            "",
        ]
    )
    _table(lines, result["bass_transition"], 12)
    lines.extend(
        [
            "",
            "## Lecture",
            "",
            "Les excès stables doivent être traduits en familles de facteurs",
            "dirigés et locaux : paire de voix × classe d'intervalle × métrique ×",
            "préparation/résolution, et degré de basse × mouvement × métrique.",
            "Le signe et le poids de chaque candidat resteront appris du corpus.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--train-pieces", type=int, default=16)
    parser.add_argument("--seeds", default="10103,20207,30313")
    parser.add_argument("--sweeps", type=int, default=30)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=HERE / "results")
    parser.add_argument("--output-stem", default="v12_context_residual_audit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    model_payload = payload["model"]
    model = {
        "register_logits": np.asarray(
            model_payload["register_logits"],
            dtype=np.float64,
        ),
        "tonal_logits": np.asarray(
            model_payload["tonal_logits"],
            dtype=np.float64,
        ),
        "features": tuple(
            k3.feature_from_model_record(rule) for rule in model_payload["rules"]
        ),
        "weights": np.asarray(
            [rule["weight"] for rule in model_payload["rules"]],
            dtype=np.float64,
        ),
    }
    candidate_min = int(payload["corpus"]["candidate_min"])
    candidate_max = int(payload["corpus"]["candidate_max"])
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    piece_ids = sorted(splits["train"], key=generative._stable_order)[
        : args.train_pieces
    ]
    lattices = [
        k3.extract_piece_lattice(
            generative._score_path(args.scores, piece_id),
            piece_id,
        )
        for piece_id in piece_ids
    ]
    source = _merge(
        [_context_counts(lattice.blocks, lattice) for lattice in lattices]
    )
    seeds = [int(value) for value in args.seeds.split(",") if value]
    tasks = [
        (
            lattice,
            model,
            candidate_min,
            candidate_max,
            seed,
            args.sweeps,
        )
        for lattice in lattices
        for seed in seeds
    ]
    if args.workers == 1:
        generated_records = [record for _, record in map(_generated_counts, tasks)]
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            generated_records = [
                record for _, record in executor.map(_generated_counts, tasks)
            ]
    generated = _merge(generated_records)
    result = {
        "experiment": {
            "id": "V12.3-CONTEXT-RESIDUAL-AUDIT",
            "status": "EXPLORATORY_TRAIN_ONLY",
            "source_model": str(args.model.resolve()),
            "train_pieces": len(piece_ids),
            "piece_ids": piece_ids,
            "seeds": seeds,
            "seeds_per_piece": len(seeds),
            "sweeps": args.sweeps,
            "test_loaded": False,
            "validation_loaded": False,
        },
        "vertical_pair_metric": _rate_rows(
            source,
            generated,
            "vertical_numerators",
            "vertical_denominators",
        ),
        "vertical_status": _rate_rows(
            source,
            generated,
            "status_numerators",
            "status_denominators",
        ),
        "bass_context": _rate_rows(
            source,
            generated,
            "bass_numerators",
            "bass_denominators",
        ),
        "bass_transition": _transition_rows(source, generated),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{args.output_stem}.json"
    report_path = args.output_dir / f"{args.output_stem.upper()}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[v12-context] wrote {json_path}")
    print(f"[v12-context] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
