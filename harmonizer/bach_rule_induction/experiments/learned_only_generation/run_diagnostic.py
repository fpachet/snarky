#!/usr/bin/env python3
"""Run the frozen V4.1 learned-only diagnostic generation campaign."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from harmonizer.bach_rule_induction.learned_generator import (
    LearnedGeneration,
    generate_many_with_learned_rules,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCORES = ROOT / "experiments" / "differentiable_rules_poc" / "work" / "scores"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results"
PIECE_IDS = (
    "bach/bwv10.7",
    "bach/bwv101.7",
    "bach/bwv104.6",
    "bach/bwv108.6",
    "bach/bwv11.6",
)
SEEDS = (0, 1)


def _declared_key(score: Any, source: Path) -> tuple[int, str]:
    from music21 import key

    values: set[tuple[int, str]] = set()
    for part in score.parts:
        signatures = tuple(part.flatten().getElementsByClass(key.KeySignature))
        if len(signatures) != 1:
            raise ValueError(f"{source}: expected one key declaration per part")
        signature = signatures[0]
        tonic = getattr(signature, "tonic", None)
        mode = getattr(signature, "mode", None)
        if tonic is None or mode not in {"major", "minor"}:
            raise ValueError(f"{source}: incomplete key declaration")
        values.add((int(tonic.pitchClass), mode))
    if len(values) != 1:
        raise ValueError(f"{source}: inconsistent part keys")
    return next(iter(values))


def _first_contiguous_soprano_fragment(score: Any, length: int = 4) -> tuple[int, ...]:
    events = tuple(score.parts[0].flatten().notesAndRests)
    run: list[Any] = []
    for event in events:
        if not event.isNote:
            run = []
            continue
        if run:
            previous = run[-1]
            previous_end = float(previous.offset + previous.duration.quarterLength)
            if abs(previous_end - float(event.offset)) > 1e-7:
                run = []
        run.append(event)
        if len(run) == length:
            return tuple(int(item.pitch.midi) for item in run)
    raise ValueError("no contiguous four-note soprano fragment")


def _score_path(scores: Path, piece_id: str) -> Path:
    return scores / f"{piece_id.removeprefix('bach/')}.mxl"


def _write_musicxml(
    generation: LearnedGeneration,
    path: Path,
) -> None:
    from music21 import key, metadata, note, stream

    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = f"S-LEARNED diagnostic seed {generation.seed}"
    tonic_names = (
        "C",
        "C#",
        "D",
        "E-",
        "E",
        "F",
        "F#",
        "G",
        "A-",
        "A",
        "B-",
        "B",
    )
    for voice_index, voice_name in enumerate(("Soprano", "Alto", "Tenor", "Bass")):
        part = stream.Part()
        part.partName = voice_name
        part.insert(
            0,
            key.Key(tonic_names[generation.tonic_pc], generation.mode),
        )
        for voicing in generation.voicings:
            part.append(note.Note(voicing[voice_index], quarterLength=1))
        score.append(part)
    score.write("musicxml", fp=str(path))


def _report(
    records: list[dict[str, Any]],
    generations: tuple[LearnedGeneration, ...],
) -> str:
    activation_counts = Counter(
        activation.rule_id
        for generation in generations
        for activation in generation.activations
    )
    crossings = sum(
        generation.diagnostic_counts["vertical_crossings"] for generation in generations
    )
    unisons = sum(
        generation.diagnostic_counts["adjacent_unisons"] for generation in generations
    )
    upper_spacing = sum(
        generation.diagnostic_counts["upper_spacing_over_octave"]
        for generation in generations
    )
    bass_spacing = sum(
        generation.diagnostic_counts["tenor_bass_spacing_over_19"]
        for generation in generations
    )
    low_cardinality = sum(
        generation.diagnostic_counts["pitch_class_cardinality_lt3"]
        for generation in generations
    )
    lines = [
        "# V4.1 — Génération diagnostique `S-LEARNED`",
        "",
        "## Protocole",
        "",
        "- cinq fragments de quatre attaques, pris dans le `train` ;",
        "- deux graines enregistrées par fragment ;",
        "- soprano et tonalité globale donnés ;",
        "- domaines des voix inférieures issus des fréquences du `train` ;",
        "- sept règles apprises, aucune règle historique ;",
        "- toutes les sorties conservées.",
        "",
        "Cette campagne est exploratoire. Les poids joints de niveau A sont une",
        "projection des poids V2.4, pas un réajustement confirmatoire.",
        "",
        "## Résumé",
        "",
        f"- générations : `{len(generations)}` ;",
        f"- croisements verticaux : `{crossings}` ;",
        f"- unissons de voix adjacentes : `{unisons}` ;",
        f"- espacements soprano–alto ou alto–ténor > octave : `{upper_spacing}` ;",
        f"- espacements ténor–basse > 19 demi-tons : `{bass_spacing}` ;",
        f"- sonorités avec moins de trois classes : `{low_cardinality}` ;",
        f"- activations apprises : `{sum(activation_counts.values())}`.",
        "",
        "Activations par règle :",
        "",
    ]
    if activation_counts:
        lines.extend(
            f"- `{rule_id}` : `{count}`"
            for rule_id, count in sorted(activation_counts.items())
        )
    else:
        lines.append("- aucune sur les transitions sélectionnées.")
    lines.extend(
        [
            "",
            "## Sorties",
            "",
            "| Pièce | Graine | Soprano | Alto | Ténor | Basse | Activations |",
            "|---|---:|---|---|---|---|---:|",
        ]
    )
    for record in records:
        voicings = record["generation"]["voicings"]
        voices = tuple(
            " ".join(str(voicing[index]) for voicing in voicings) for index in range(4)
        )
        lines.append(
            f"| `{record['piece_id']}` | {record['generation']['seed']} | "
            f"`{voices[0]}` | `{voices[1]}` | `{voices[2]}` | `{voices[3]}` | "
            f"{len(record['generation']['activations'])} |"
        )
    lines.extend(
        [
            "",
            "## Lecture",
            "",
            "Le succès technique attendu est l'existence de sorties traçables sous",
            "`S-LEARNED`. Les croisements, unissons et autres défauts ne sont pas",
            "corrigés après coup : ils désignent les prochaines familles à induire.",
            "",
        ]
    )
    return "\n".join(lines)


def run(scores: Path, output: Path) -> dict[str, Any]:
    from music21 import converter

    output.mkdir(parents=True, exist_ok=True)
    generated_dir = output / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    generations: list[LearnedGeneration] = []
    for piece_id in PIECE_IDS:
        source = _score_path(scores, piece_id)
        score = converter.parse(source)
        tonic_pc, mode = _declared_key(score, source)
        soprano = _first_contiguous_soprano_fragment(score)
        piece_generations = generate_many_with_learned_rules(
            soprano,
            tonic_pc=tonic_pc,
            mode=mode,
            seeds=SEEDS,
        )
        for generation in piece_generations:
            piece_stem = piece_id.removeprefix("bach/").replace(".", "_")
            stem = f"{piece_stem}_seed{generation.seed}"
            musicxml = generated_dir / f"{stem}.musicxml"
            _write_musicxml(generation, musicxml)
            records.append(
                {
                    "piece_id": piece_id,
                    "source": str(source),
                    "musicxml": str(musicxml.relative_to(output)),
                    "generation": asdict(generation),
                    "diagnostics": generation.diagnostic_counts,
                }
            )
            generations.append(generation)
        print(f"[S-LEARNED] generated {piece_id}", flush=True)

    result = {
        "schema_version": 1,
        "experiment": "V4.1-learned-only-diagnostic",
        "status": "exploratory",
        "piece_ids": list(PIECE_IDS),
        "seeds": list(SEEDS),
        "records": records,
    }
    json_path = output / "v4_1_learned_only_diagnostic.json"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path = output / "V4_1_LEARNED_ONLY_DIAGNOSTIC_REPORT.md"
    report_path.write_text(
        _report(records, tuple(generations)),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    run(arguments.scores, arguments.output)


if __name__ == "__main__":
    main()
