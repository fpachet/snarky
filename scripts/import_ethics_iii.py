#!/usr/bin/env python3
"""Import the public-domain Appuhn text of Ethics III from Wikisource HTML.

The importer deliberately uses only the Python standard library.  Network
retrieval is kept outside the script: pass it a saved HTML page so the exact
source snapshot can be archived and hashed independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SOURCE_URL = (
    "https://fr.wikisource.org/wiki/"
    "%C3%89thique_%28Appuhn%2C_1913%29/"
    "Troisi%C3%A8me_partie_%3A_De_l%E2%80%99origine_et_de_la_nature_"
    "des_affections"
)
ROMAN_DIGITS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
SPACE_RE = re.compile(r"\s+")
NUMBERED_PARAGRAPH_RE = re.compile(r"^(?P<number>[IVXL]+)\.\s*(?P<text>.*)$")
PROPOSITION_HEADING_RE = re.compile(r"^PROPOSITION\s+(?P<number>[IVXL]+)$")
REFERENCE_RE = re.compile(
    r"\bProp(?:osition|\.)\s*(?P<number>\d+)",
    flags=re.IGNORECASE,
)
PART_RE = re.compile(r"\bp(?:artie|\.)\s*(?P<part>I{1,3}|IV|V)\b", re.IGNORECASE)
SECTION_LABELS = {"DÉMONSTRATION", "COROLLAIRE", "SCOLIE", "EXPLICATION"}


@dataclass(frozen=True)
class Block:
    tag: str
    text: str


def roman_to_int(value: str) -> int:
    total = 0
    previous = 0
    for character in reversed(value):
        digit = ROMAN_DIGITS[character]
        total += -digit if digit < previous else digit
        previous = max(previous, digit)
    return total


def normalize_text(value: str) -> str:
    return SPACE_RE.sub(" ", value.replace("\xa0", " ")).strip()


class EthicsHTMLParser(HTMLParser):
    """Collect only semantic heading, paragraph, and section-label blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self._capture_tag: str | None = None
        self._capture_depth = 0
        self._buffer: list[str] = []
        self._skip_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if self._skip_depth:
            self._skip_depth += 1
            return
        if "pagenum" in classes or (tag == "sup" and "reference" in classes):
            self._skip_depth = 1
            return
        if self._capture_tag is not None:
            self._capture_depth += 1
            return
        is_section_div = tag == "div" and "text-align:center" in (
            attributes.get("style") or ""
        )
        if tag in {"h4", "h5", "p"} or is_section_div:
            self._capture_tag = tag
            self._capture_depth = 1
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if self._capture_tag is None:
            return
        self._capture_depth -= 1
        if self._capture_depth:
            return
        text = normalize_text("".join(self._buffer))
        if text:
            self.blocks.append(Block(self._capture_tag, text))
        self._capture_tag = None
        self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture_tag is not None and not self._skip_depth:
            self._buffer.append(data)


def numbered_units(
    blocks: list[Block],
    *,
    prefix: str,
    unit_type: str,
) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for block in blocks:
        if block.tag != "p":
            continue
        match = NUMBERED_PARAGRAPH_RE.match(block.text)
        if match:
            if current is not None:
                units.append(current)
            number = roman_to_int(match.group("number"))
            current = {
                "id": f"{prefix}{number}",
                "type": unit_type,
                "source_text": match.group("text"),
            }
        elif current is not None:
            current["source_text"] += "\n\n" + block.text
    if current is not None:
        units.append(current)
    return units


def extract_references(text: str, current_part: int = 3) -> list[str]:
    """Return conservative reference candidates, never inferred references."""

    references: set[str] = set()
    for match in REFERENCE_RE.finditer(text):
        following = text[match.end() : match.end() + 45]
        part_match = PART_RE.search(following)
        part = (
            roman_to_int(part_match.group("part").upper())
            if part_match
            else current_part
        )
        references.add(f"E{part}P{int(match.group('number')):02d}")
    return sorted(references)


def parse_sections(blocks: list[Block]) -> tuple[str, list[dict[str, str]]]:
    statement_parts: list[str] = []
    sections: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for block in blocks:
        label = block.text.upper()
        base_label = label.split()[0] if label else ""
        if block.tag == "div" and base_label in SECTION_LABELS:
            current = {"type": base_label.lower(), "label": block.text, "text": ""}
            sections.append(current)
        elif block.tag == "p":
            if current is None:
                statement_parts.append(block.text)
            else:
                separator = "\n\n" if current["text"] else ""
                current["text"] += separator + block.text
    return "\n\n".join(statement_parts), sections


def slice_between(blocks: list[Block], start: int, end: int) -> list[Block]:
    return blocks[start + 1 : end]


def build_corpus(html_bytes: bytes) -> dict[str, Any]:
    parser = EthicsHTMLParser()
    parser.feed(html_bytes.decode("utf-8"))
    blocks = parser.blocks
    h4_positions = [index for index, block in enumerate(blocks) if block.tag == "h4"]
    if not h4_positions:
        raise ValueError("no Ethics III headings found in HTML")

    first_heading = h4_positions[0]
    preface_parts = [block.text for block in blocks[:first_heading] if block.tag == "p"]
    if not preface_parts:
        raise ValueError("Ethics III preface not found before definitions")
    units: list[dict[str, Any]] = [
        {
            "id": "E3PREFACE",
            "type": "preface",
            "source_text": "\n\n".join(preface_parts),
        }
    ]
    for position_index, position in enumerate(h4_positions):
        heading = blocks[position].text.upper()
        end = (
            h4_positions[position_index + 1]
            if position_index + 1 < len(h4_positions)
            else len(blocks)
        )
        body = slice_between(blocks, position, end)
        if heading == "DÉFINITIONS":
            units.extend(numbered_units(body, prefix="E3D", unit_type="definition"))
            continue
        if heading == "POSTULATS":
            units.extend(numbered_units(body, prefix="E3POST", unit_type="postulate"))
            continue
        proposition_match = PROPOSITION_HEADING_RE.match(heading)
        if proposition_match:
            number = roman_to_int(proposition_match.group("number"))
            source_text, sections = parse_sections(body)
            all_text = "\n\n".join([source_text, *(item["text"] for item in sections)])
            units.append(
                {
                    "id": f"E3P{number:02d}",
                    "type": "proposition",
                    "source_text": source_text,
                    "sections": sections,
                    "reference_candidates": extract_references(all_text),
                }
            )
            continue
        if heading == "DÉFINITIONS DES AFFECTIONS":
            h5_positions = [
                index for index, block in enumerate(body) if block.tag == "h5"
            ]
            for h5_index, local_position in enumerate(h5_positions):
                next_position = (
                    h5_positions[h5_index + 1]
                    if h5_index + 1 < len(h5_positions)
                    else len(body)
                )
                affect_heading = body[local_position].text.upper()
                affect_body = body[local_position + 1 : next_position]
                source_text, sections = parse_sections(affect_body)
                if affect_heading == "DÉFINITION GÉNÉRALE DES AFFECTIONS":
                    identifier = "E3DA-GENERAL"
                    unit_type = "general_definition_of_affect"
                else:
                    identifier = f"E3DA{roman_to_int(affect_heading):02d}"
                    unit_type = "definition_of_affect"
                units.append(
                    {
                        "id": identifier,
                        "type": unit_type,
                        "source_text": source_text,
                        "sections": sections,
                        "reference_candidates": extract_references(
                            "\n\n".join(
                                [source_text, *(item["text"] for item in sections)]
                            )
                        ),
                    }
                )

    counts: dict[str, int] = {}
    for unit in units:
        counts[unit["type"]] = counts.get(unit["type"], 0) + 1
    expected = {
        "preface": 1,
        "definition": 3,
        "postulate": 2,
        "proposition": 59,
        "definition_of_affect": 48,
        "general_definition_of_affect": 1,
    }
    if counts != expected:
        raise ValueError(f"unexpected corpus counts: {counts!r}, expected {expected!r}")
    return {
        "schema_version": 1,
        "source": {
            "work": "Éthique, partie III",
            "author": "Baruch Spinoza",
            "translation": "Charles Appuhn",
            "edition": "Garnier Frères, 1913",
            "license_status": "public_domain",
            "url": SOURCE_URL,
            "retrieved": "2026-07-22",
            "html_sha256": hashlib.sha256(html_bytes).hexdigest(),
        },
        "counts": counts,
        "units": units,
    }


def main() -> None:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("source_html", type=Path)
    argument_parser.add_argument("output_json", type=Path)
    args = argument_parser.parse_args()
    corpus = build_corpus(args.source_html.read_bytes())
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
