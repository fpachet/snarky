#!/usr/bin/env python3
"""Render the structured Appuhn corpus as one review-friendly text file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROMAN_ONES = (
    "",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
)
ROMAN_TENS = ("", "X", "XX", "XXX", "XL", "L")


def roman(number: int) -> str:
    if not 1 <= number <= 59:
        raise ValueError(f"unsupported Ethics III number: {number}")
    return ROMAN_TENS[number // 10] + ROMAN_ONES[number % 10]


def numbered_identifier(identifier: str, prefix: str) -> int:
    return int(identifier.removeprefix(prefix))


def unit_heading(unit: dict[str, Any]) -> str:
    identifier = unit["id"]
    unit_type = unit["type"]
    if unit_type == "preface":
        return "PRÉFACE — E3PREFACE"
    if unit_type == "definition":
        number = numbered_identifier(identifier, "E3D")
        return f"DÉFINITION {roman(number)} — {identifier}"
    if unit_type == "postulate":
        number = numbered_identifier(identifier, "E3POST")
        return f"POSTULAT {roman(number)} — {identifier}"
    if unit_type == "proposition":
        number = numbered_identifier(identifier, "E3P")
        return f"PROPOSITION {roman(number)} — {identifier}"
    if unit_type == "definition_of_affect":
        number = numbered_identifier(identifier, "E3DA")
        return f"DÉFINITION D’AFFECT {roman(number)} — {identifier}"
    if unit_type == "general_definition_of_affect":
        return "DÉFINITION GÉNÉRALE DES AFFECTS — E3DA-GENERAL"
    raise ValueError(f"unsupported unit type: {unit_type!r}")


def render_corpus(corpus: dict[str, Any]) -> str:
    source = corpus["source"]
    lines = [
        "BARUCH SPINOZA — ÉTHIQUE, PARTIE III",
        "DE L’ORIGINE ET DE LA NATURE DES AFFECTIONS",
        "",
        f"Traduction : {source['translation']}",
        f"Édition : {source['edition']}",
        f"Source numérique : {source['url']}",
        f"Instantané HTML SHA-256 : {source['html_sha256']}",
        "",
        (
            "Repères E3… ajoutés par le projet pour relier le texte aux règles "
            "et aux manifestes de théorèmes."
        ),
    ]
    for unit in corpus["units"]:
        lines.extend(["", "=" * 79, unit_heading(unit), "=" * 79, ""])
        lines.append(unit["source_text"])
        for section in unit.get("sections", []):
            lines.extend(["", section["label"].upper(), "", section["text"]])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_json", type=Path)
    parser.add_argument("output_text", type=Path)
    args = parser.parse_args()
    corpus: dict[str, Any] = json.loads(args.corpus_json.read_text(encoding="utf-8"))
    args.output_text.parent.mkdir(parents=True, exist_ok=True)
    args.output_text.write_text(render_corpus(corpus), encoding="utf-8")


if __name__ == "__main__":
    main()
