#!/usr/bin/env python3
"""Generate SATB pitches on a real per-voice ATTACK/HOLD lattice."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

import k3
import numpy as np

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
DEFAULT_MODEL = HERE / "results/v5_1_k3_compact_model.json"
DEFAULT_SCORE = HERE / "work/scores/bwv108.6.mxl"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_OUTPUT = HERE / "results/v5_5_k3_rhythmic_gibbs.json"
DEFAULT_REPORT = HERE / "results/V5_5_K3_RHYTHMIC_GIBBS.md"
DEFAULT_GENERATED = REPOSITORY / "harmonizer/generated"


def _split_membership(splits_path: Path, piece_id: str) -> str:
    payload = json.loads(splits_path.read_text(encoding="utf-8"))
    source = payload.get("grouped_split", payload)
    matches = [
        name for name in ("train", "validation", "test") if piece_id in source[name]
    ]
    if len(matches) != 1:
        raise ValueError(f"{piece_id}: expected exactly one corpus split")
    return matches[0]


def _mutable_segments(
    attacks: np.ndarray,
    fixed: np.ndarray,
) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (start, end, voice)
        for start, end, voice in k3.attack_segments(attacks)
        if not fixed[start:end, voice].any()
    )


def _randomize_mutable_segments(
    blocks: np.ndarray,
    attacks: np.ndarray,
    fixed: np.ndarray,
    register_logits: np.ndarray,
    candidate_min: int,
    seed: int,
) -> np.ndarray:
    result = blocks.copy()
    generator = np.random.default_rng(seed)
    candidates = np.arange(candidate_min, candidate_min + register_logits.shape[1])
    probabilities = np.exp(register_logits)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    for start, end, voice in _mutable_segments(attacks, fixed):
        result[start:end, voice] = generator.choice(
            candidates,
            p=probabilities[voice],
        )
    return result


def _note_at_offset(
    offsets: np.ndarray,
    offset: float,
) -> int:
    matches = np.flatnonzero(np.isclose(offsets, offset, atol=1e-7))
    if matches.size != 1:
        raise ValueError(f"Cannot map note onset {offset} to the rhythmic lattice")
    return int(matches[0])


def _materialize_score(
    score_path: Path,
    lattice: k3.RhythmicLattice,
    generated_blocks: np.ndarray,
) -> Any:
    from music21 import converter

    score = copy.deepcopy(converter.parse(score_path))
    parts = {part.partName: part for part in score.parts}
    if set(parts) != set(k3.VOICE_NAMES):
        raise ValueError(f"Unexpected score parts: {tuple(parts)}")
    for voice, name in enumerate(k3.VOICE_NAMES):
        for element in parts[name].recurse().notes:
            onset = float(element.getOffsetInHierarchy(parts[name]))
            time = _note_at_offset(lattice.offsets, onset)
            element.pitch.midi = int(generated_blocks[time, voice])
    return score


def _duration_histograms(score: Any) -> dict[str, dict[str, int]]:
    return {
        part.partName: dict(
            sorted(
                Counter(
                    f"{float(element.duration.quarterLength):g}"
                    for element in part.flatten().notes
                ).items(),
                key=lambda item: float(item[0]),
            )
        )
        for part in score.parts
    }


def _short_stepwise_counts(score: Any) -> dict[str, int]:
    """Count short central notes approached and left by same-direction steps."""

    result = {}
    for part in score.parts:
        notes = list(part.flatten().notes)
        count = 0
        for previous, central, following in zip(
            notes,
            notes[1:],
            notes[2:],
            strict=False,
        ):
            incoming = int(central.pitch.midi) - int(previous.pitch.midi)
            outgoing = int(following.pitch.midi) - int(central.pitch.midi)
            if (
                float(central.duration.quarterLength) <= 0.5
                and incoming * outgoing > 0
                and abs(incoming) <= 2
                and abs(outgoing) <= 2
            ):
                count += 1
        result[part.partName] = count
    return result


def _pitch_classes(score: Any) -> dict[str, list[int]]:
    return {
        part.partName: sorted(
            {int(element.pitch.pitchClass) for element in part.flatten().notes}
        )
        for part in score.parts
    }


def _crossing_count(blocks: np.ndarray) -> int:
    return int(np.any(blocks[:, :-1] < blocks[:, 1:], axis=1).sum())


def _markdown(result: dict[str, Any]) -> str:
    source = result["source"]
    generation = result["generation"]
    comparison = result["comparison"]
    lines = [
        "# V5.5 — génération K3 sur rythme polyphonique réel",
        "",
        "## Protocole",
        "",
        f"- Choral : `{source['piece_id']}`, appartenant au train.",
        "- Soprano, grille d'attaques et tenues fixés.",
        "- Alto, ténor et basse rééchantillonnés par segments d'attaque.",
        (f"- `{generation['sweeps']}` balayages Gibbs, graine `{generation['seed']}`."),
        (
            f"- `{result['experiment']['learned_pitch_rules']}` règles K3 apprises, "
            "sans règle historique."
        ),
        "- Test fermé non chargé.",
        "",
        "## Résultat structurel",
        "",
        f"- blocs verticaux : `{source['vertical_blocks']}` ;",
        f"- segments d'attaque totaux : `{generation['all_attack_segments']}` ;",
        f"- segments rééchantillonnés : `{generation['sampled_attack_segments']}` ;",
        f"- cellules de tenue : `{generation['hold_cells']}` ;",
        (f"- cohérence des tenues : `{str(generation['hold_consistency']).lower()}` ;"),
        f"- blocs avec croisement de voix : `{generation['voice_crossing_blocks']}`.",
        "",
        "## Durées conservées",
        "",
        "| Voix | Histogramme en noires |",
        "|---|---|",
    ]
    for voice, histogram in generation["duration_histograms_quarters"].items():
        rendered = ", ".join(
            f"`{duration}`×{count}" for duration, count in histogram.items()
        )
        lines.append(f"| {voice} | {rendered} |")
    lines.extend(
        [
            "",
            "Le choral produit contient donc des doubles-croches (`0,25`), des",
            "croches (`0,5`), des noires (`1`) et des blanches (`2`).",
            "",
            "## Mouvements courts de type passage",
            "",
            "Diagnostic purement géométrique : note centrale d'au plus une croche,",
            "approchée et quittée dans la même direction par demi-ton ou ton.",
            "",
            "| Voix | Bach | Généré |",
            "|---|---:|---:|",
        ]
    )
    for voice in k3.VOICE_NAMES:
        lines.append(
            f"| {voice} | {comparison['source_short_stepwise'][voice]} | "
            f"{comparison['generated_short_stepwise'][voice]} |"
        )
    lines.extend(
        [
            "",
            "## Limites",
            "",
            "- Le rythme est ici conservé, pas encore généré.",
            "- Le diagnostic de passage n'est pas une analyse harmonique.",
            "- Le catalogue actuel ne possède ni tonalité locale ni degré d'échelle.",
            "- Les règles pondérées sont évaluées par le moteur K3 Python ; leur",
            "  compilation dans une base Snarky apprise reste le jalon suivant.",
            "",
            "Cette expérience valide la sémantique `ATTACK/HOLD` et l'export",
            "MusicXML/MIDI. Elle ne constitue pas encore une comparaison qualitative",
            "avec DeepBach.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--sweeps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=5517)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--generated-directory", type=Path, default=DEFAULT_GENERATED)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    split = _split_membership(args.splits, args.piece_id)
    if split == "test":
        raise ValueError("The sealed test split cannot be used for this diagnostic")
    payload = json.loads(args.model.read_text(encoding="utf-8"))
    model = payload["model"]
    corpus = payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register_logits = np.asarray(model["register_logits"], dtype=np.float64)
    features = [k3.feature_from_model_record(rule) for rule in model["rules"]]
    weights = np.asarray([rule["weight"] for rule in model["rules"]])
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    if lattice.blocks.min() < candidate_min or lattice.blocks.max() > candidate_max:
        raise ValueError("Source boundary pitches fall outside the train domain")

    fixed = np.zeros_like(lattice.blocks, dtype=bool)
    fixed[:, 0] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    initial = _randomize_mutable_segments(
        lattice.blocks,
        lattice.attacks,
        fixed,
        register_logits,
        candidate_min,
        args.seed,
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
        seed=args.seed,
        temperature=args.temperature,
    )
    from music21 import converter

    source_score = converter.parse(args.score)
    score = _materialize_score(args.score, lattice, generated)
    args.generated_directory.mkdir(parents=True, exist_ok=True)
    stem = f"v5_5_{Path(args.score).stem}_seed_{args.seed}"
    musicxml_path = args.generated_directory / f"{stem}.musicxml"
    midi_path = args.generated_directory / f"{stem}.mid"
    score.write("musicxml", fp=musicxml_path)
    score.write("midi", fp=midi_path)
    segments = k3.attack_segments(lattice.attacks)
    result = {
        "experiment": {
            "id": "V5.5-K3-RHYTHMIC-GIBBS",
            "status": "EXPLORATORY",
            "test_loaded": False,
            "source_split": split,
            "learned_pitch_rules": len(features),
            "rhythm_generated": False,
            "rhythm_preserved_from_source": True,
        },
        "source": {
            "piece_id": args.piece_id,
            "score": str(args.score.resolve()),
            "vertical_blocks": lattice.size,
            "end_offset_quarters": lattice.end_offset,
            "attack_counts": {
                name: int(lattice.attacks[:, voice].sum())
                for voice, name in enumerate(k3.VOICE_NAMES)
            },
        },
        "generation": {
            "seed": args.seed,
            "sweeps": args.sweeps,
            "temperature": args.temperature,
            "fixed_voice": "Soprano",
            "sampled_attack_segments": len(_mutable_segments(lattice.attacks, fixed)),
            "all_attack_segments": len(segments),
            "hold_cells": int((~lattice.attacks).sum()),
            "hold_consistency": bool(
                np.all(
                    generated[1:][~lattice.attacks[1:]]
                    == generated[:-1][~lattice.attacks[1:]]
                )
            ),
            "voice_crossing_blocks": _crossing_count(generated),
            "duration_histograms_quarters": _duration_histograms(score),
            "musicxml": str(musicxml_path.resolve()),
            "midi": str(midi_path.resolve()),
        },
        "comparison": {
            "source_short_stepwise": _short_stepwise_counts(source_score),
            "generated_short_stepwise": _short_stepwise_counts(score),
            "source_pitch_classes": _pitch_classes(source_score),
            "generated_pitch_classes": _pitch_classes(score),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-rhythm] wrote {args.output}", flush=True)
    print(f"[k3-rhythm] wrote {args.report}", flush=True)
    print(f"[k3-rhythm] wrote {musicxml_path}", flush=True)
    print(f"[k3-rhythm] wrote {midi_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
