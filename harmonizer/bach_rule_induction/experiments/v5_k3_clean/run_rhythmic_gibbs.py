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
    tonal_logits: np.ndarray | None = None,
    tonic_pc: int | None = None,
    mode: int | None = None,
) -> np.ndarray:
    result = blocks.copy()
    generator = np.random.default_rng(seed)
    candidates = np.arange(candidate_min, candidate_min + register_logits.shape[1])
    scores = register_logits.copy()
    if tonal_logits is not None:
        if tonic_pc is None or mode is None:
            raise ValueError("Tonal initialization requires tonic and mode")
        relative = (candidates - tonic_pc) % 12
        if tonal_logits.shape == (2, 12):
            scores += tonal_logits[mode, relative][None, :]
        elif tonal_logits.shape == (4, 2, 12):
            scores += tonal_logits[:, mode, relative]
        else:
            raise ValueError("Unexpected tonal-logit shape")
    scores -= scores.max(axis=1, keepdims=True)
    probabilities = np.exp(scores)
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
    *,
    title: str,
    composer: str,
) -> Any:
    from music21 import converter, metadata

    score = copy.deepcopy(converter.parse(score_path))
    if score.metadata is None:
        score.metadata = metadata.Metadata()
    score.metadata.title = title
    score.metadata.composer = composer
    parts = {part.partName: part for part in score.parts}
    if set(parts) != set(k3.VOICE_NAMES):
        raise ValueError(f"Unexpected score parts: {tuple(parts)}")
    for voice, name in enumerate(k3.VOICE_NAMES):
        for element in parts[name].recurse().notes:
            onset = float(element.getOffsetInHierarchy(parts[name]))
            time = _note_at_offset(lattice.offsets, onset)
            element.pitch.midi = int(generated_blocks[time, voice])
    return score


def _source_score_metadata(score: Any) -> dict[str, Any]:
    from music21 import key, meter, tempo

    declared_keys = list(score.parts[0].recurse().getElementsByClass(key.Key))
    signatures = list(score.parts[0].recurse().getElementsByClass(meter.TimeSignature))
    marks = list(score.recurse().getElementsByClass(tempo.MetronomeMark))
    if len(declared_keys) != 1 or len(signatures) != 1:
        raise ValueError("Expected one declared key and time signature")
    declared = declared_keys[0]
    key_signature = declared.tonic.name + ("m" if declared.mode == "minor" else "")
    bpm = float(marks[0].number) if marks and marks[0].number else 120.0
    return {
        "key_signature": key_signature,
        "time_signature": signatures[0].ratioString,
        "tempo_microseconds": int(round(60_000_000 / bpm)),
    }


def _materialize_muses_piece(
    lattice: k3.RhythmicLattice,
    generated_blocks: np.ndarray,
    *,
    title: str,
    composer: str,
    score_metadata: dict[str, Any],
) -> Any:
    try:
        from muses.base.temporals import Piece, TemporalCollection, TemporalNote
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "MuSES is required for canonical V5.5 export; "
            "install the sibling project with `pip install -e ../muses`."
        ) from exc

    collections = []
    for voice, name in enumerate(k3.VOICE_NAMES):
        notes = []
        for start, end, segment_voice in k3.attack_segments(lattice.attacks):
            if segment_voice != voice:
                continue
            start_offset = float(lattice.offsets[start])
            end_offset = (
                lattice.end_offset
                if end == lattice.size
                else float(lattice.offsets[end])
            )
            notes.append(
                TemporalNote(
                    int(generated_blocks[start, voice]),
                    start_offset,
                    end_offset - start_offset,
                    velocity=72,
                    midi_channel=voice,
                )
            )
        collections.append(
            TemporalCollection(
                name=name,
                temporals=notes,
                instrument="choir",
                program_change=52,
                melody_type=name.lower(),
                end_beat=lattice.end_offset,
            )
        )
    return Piece(
        name="k3_learned_choral",
        title=title,
        composer=composer,
        melodies=collections,
        ticks_per_beat=480,
        time_signature=score_metadata["time_signature"],
        key_signature=score_metadata["key_signature"],
        tempo=score_metadata["tempo_microseconds"],
    )


def _write_muses_exports(
    piece: Any,
    musicxml_path: Path,
    midi_path: Path,
) -> None:
    from muses.io import MusicXMLClef, write_musicxml

    piece.save_midi(midi_path)
    write_musicxml(
        piece,
        musicxml_path,
        part_clefs=(
            MusicXMLClef("G", 2),
            MusicXMLClef("G", 2),
            MusicXMLClef("F", 4),
            MusicXMLClef("F", 4),
        ),
    )


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
        f"# {result['experiment']['id']} — génération sur rythme polyphonique réel",
        "",
        "## Protocole",
        "",
        f"- Choral : `{source['piece_id']}`, appartenant au train.",
        "- Soprano, grille d'attaques et tenues fixés.",
        "- Alto, ténor et basse rééchantillonnés par segments d'attaque.",
        (f"- `{generation['sweeps']}` balayages Gibbs, graine `{generation['seed']}`."),
        (
            f"- `{result['experiment']['learned_pitch_rules']}` facteurs K3 appris, "
            "sans règle historique."
        ),
        "- Test réservé non chargé.",
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
            (
                "- La tonalité utilisée reste la tonalité globale déclarée ; les "
                "tonicisations locales et degrés orthographiés restent absents."
                if result["experiment"]["tonal_context"]
                else "- Le catalogue actuel ne possède ni tonalité locale ni degré "
                "d'échelle."
            ),
            "- Les activations K3 sont calculées par un fournisseur pur, puis",
            "  évaluées par la base `FACTOR` Snarky sans effet de bord.",
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
    parser.add_argument("--stem")
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
    tonal_logits = (
        None
        if model.get("tonal_logits") is None
        else np.asarray(model["tonal_logits"], dtype=np.float64)
    )
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
        seed=args.seed,
        temperature=args.temperature,
        tonal_logits=tonal_logits,
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        metric_levels=lattice.metric_levels,
    )
    from music21 import converter

    source_score = converter.parse(args.score)
    title = f"{args.piece_id} — génération K3 apprise"
    composer = "Snarky / MuSES"
    source_metadata = _source_score_metadata(source_score)
    score = _materialize_score(
        args.score,
        lattice,
        generated,
        title=title,
        composer=composer,
    )
    muses_piece = _materialize_muses_piece(
        lattice,
        generated,
        title=title,
        composer=composer,
        score_metadata=source_metadata,
    )
    args.generated_directory.mkdir(parents=True, exist_ok=True)
    source_version = str(payload.get("experiment", {}).get("id", "")).split("-", 1)[0]
    version = (
        source_version.lower()
        if tonal_logits is not None and source_version
        else "v5_5"
    )
    stem = args.stem or f"{version}_{Path(args.score).stem}_seed_{args.seed}"
    musicxml_path = args.generated_directory / f"{stem}.musicxml"
    midi_path = args.generated_directory / f"{stem}.mid"
    source_layout_path = args.generated_directory / f"{stem}_source_layout.musicxml"
    _write_muses_exports(muses_piece, musicxml_path, midi_path)
    score.write("musicxml", fp=source_layout_path)
    segments = k3.attack_segments(lattice.attacks)
    result = {
        "experiment": {
            "id": (
                f"{source_version}-K3-CONTEXTUAL-RHYTHMIC-GIBBS"
                if tonal_logits is not None
                else "V5.5-K3-RHYTHMIC-GIBBS"
            ),
            "status": "EXPLORATORY",
            "test_loaded": False,
            "source_split": split,
            "learned_pitch_rules": len(features),
            "rhythm_generated": False,
            "rhythm_preserved_from_source": True,
            "tonal_context": tonal_logits is not None,
        },
        "source": {
            "piece_id": args.piece_id,
            "score": str(args.score.resolve()),
            "vertical_blocks": lattice.size,
            "end_offset_quarters": lattice.end_offset,
            "tonic_pc": lattice.tonic_pc,
            "mode": "minor" if lattice.mode else "major",
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
            "source_layout_musicxml": str(source_layout_path.resolve()),
            "exporter": "MuSES",
            "source_layout_exporter": "music21",
            "composer": composer,
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
    print(f"[k3-rhythm] wrote {source_layout_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
