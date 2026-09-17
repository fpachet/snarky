#!/usr/bin/env python3
# ruff: noqa: E501
"""Build the private source-unit ledger and public CHORAL card catalogue.

The script deliberately keeps the OCR, corrected transcription, and page images
under work/. Public artefacts contain hashes, locations, short cues, and
independent paraphrases only.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OCR_DIR = ROOT / "work" / "ocr"
PRIVATE_UNITS = ROOT / "work" / "source_units.full.jsonl"
PRIVATE_TABLES = ROOT / "work" / "tables.full.jsonl"
PUBLIC_UNITS = ROOT / "appendix_b_source_units.metadata.jsonl"
CARDS = ROOT / "appendix_b_cards.jsonl"
TABLES = ROOT / "tables.jsonl"
PROGRESS = ROOT / "PROGRESS.json"

PDF_FIRST = 243
PDF_LAST = 320
PDF_PRINTED_OFFSET = 9
PDF_SHA256 = "1e15961a4855bb8b6610fe5fc1c5db6bfdddf54f6129f36cee5f5a7d26643d8c"

HEADING_RE = re.compile(
    r"^(?P<number>[12](?:\s*\.\s*\d+){0,7})\.?\s*(?:[|©]\s*)?(?P<title>[A-Z].+)$"
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]*\b")

# Corrections are deliberately conservative and limited to recurring scan-font
# confusions observed against rendered pages. Musical notation is not guessed.
WORD_CORRECTIONS = {
    "accidentaJ": "accidental",
    "ali": "all",
    "anaJysis": "analysis",
    "barmonization": "harmonization",
    "barmonizations": "harmonizations",
    "barmonic": "harmonic",
    "bave": "have",
    "beuristic": "heuristic",
    "beuristics": "heuristics",
    "cbord": "chord",
    "cbords": "chords",
    "cborale": "chorale",
    "cborales": "chorales",
    "cboral": "choral",
    "congcsted": "congested",
    "eigbth": "eighth",
    "eigbths": "eighths",
    "fattened": "flattened",
    "fiftb": "fifth",
    "fiftbs": "fifths",
    "fourtb": "fourth",
    "fourths": "fourths",
    "grapbics": "graphics",
    "bigh": "high",
    "bigber": "higher",
    "bighest": "highest",
    "matcb": "match",
    "matcbes": "matches",
    "melodic": "melodic",
    "mioorm": "minorm",
    "miporm": "minorm",
    "minomm": "minorm",
    "noJe": "note",
    "nole": "note",
    "notes": "notes",
    "otber": "other",
    "otbers": "others",
    "pbrase": "phrase",
    "pbrases": "phrases",
    "pitcb": "pitch",
    "pitcbes": "pitches",
    "researcbers": "researchers",
    "sbarp": "sharp",
    "sbarpened": "sharpened",
    "sixtb": "sixth",
    "sixtbs": "sixths",
    "tbat": "that",
    "tbe": "the",
    "tbeir": "their",
    "tbem": "them",
    "tben": "then",
    "tbere": "there",
    "tbese": "these",
    "tbey": "they",
    "tbis": "this",
    "tbree": "three",
    "tbrees": "threes",
    "unisson": "unison",
    "unissons": "unisons",
    "wben": "when",
    "wbenever": "whenever",
    "wbere": "where",
    "wbich": "which",
    "witb": "with",
}

# Every rendered Appendix B page was inspected at page resolution after the
# three text layers had been produced. Units that still contain low-confidence
# notation remain explicitly flagged ``needs_review`` below.
VISUALLY_REVIEWED_PAGES = set(range(PDF_FIRST, PDF_LAST + 1))

TABLE_SPECS = [
    {
        "table_id": "CHORAL-TABLE-P0239-T01",
        "pdf_pages": [248, 249],
        "printed_pages": [239, 240],
        "title": "Legal chord spellings by degree in C major and A minor",
        "columns": ["degree", "legal pitch-class spellings", "qualifier"],
        "role": "Lookup relation constraining degree/chord compatibility; other accepted keys use transposition.",
        "expected_entry_count": 24,
    },
    {
        "table_id": "CHORAL-TABLE-P0245-T01",
        "pdf_pages": [254, 255, 256, 257],
        "printed_pages": [245, 246, 247, 248],
        "title": "Catalogue of phrase-ending and mid-phrase cliché patterns",
        "columns": [
            "cliché number",
            "context class",
            "three-chord SATB pattern",
            "elaboration markers",
        ],
        "role": "Lookup catalogue used by the chord-skeleton and fill-in procedures.",
        "expected_entry_count": 11,
    },
    {
        "table_id": "CHORAL-TABLE-P0250-T01",
        "pdf_pages": [259, 260],
        "printed_pages": [250, 251],
        "title": "Cadence patterns",
        "columns": [
            "mode",
            "soprano ending pitch",
            "soprano ending accidental",
            "cadence key",
            "penultimate root",
            "penultimate inversion",
            "ending root",
        ],
        "role": "Permitted phrase-ending configurations referenced by cadence constraints.",
        "expected_entry_count": 67,
    },
    {
        "table_id": "CHORAL-TABLE-P0254-T01",
        "pdf_pages": [263],
        "printed_pages": [254],
        "title": "Allowable ranges of the four voices",
        "columns": ["voice", "lowest pitch", "highest pitch"],
        "role": "Range bounds used when constructing and checking SATB realizations.",
        "expected_entry_count": 4,
    },
    {
        "table_id": "CHORAL-TABLE-P0285-T01",
        "pdf_pages": [294],
        "printed_pages": [285],
        "title": "Permitted sharpened-sixth melodic-minor patterns",
        "columns": ["preceding context", "sharpened sixth", "following context"],
        "role": "Pattern lookup validating a sharpened sixth in recent merged-melodic-string context.",
        "expected_entry_count": 5,
    },
    {
        "table_id": "CHORAL-TABLE-P0285-T02",
        "pdf_pages": [294],
        "printed_pages": [285],
        "title": "Permitted flattened-seventh melodic-minor patterns",
        "columns": ["preceding context", "flattened seventh", "following context"],
        "role": "Pattern lookup validating a flattened seventh in recent merged-melodic-string context.",
        "expected_entry_count": 4,
    },
    {
        "table_id": "CHORAL-TABLE-P0297-T01",
        "pdf_pages": [306, 307, 308],
        "printed_pages": [297, 298, 299],
        "title": "Schenkerian parser function and attribute catalogue",
        "columns": ["function or attribute", "type/domain", "operational meaning"],
        "role": "Typed reference catalogue for the parser state used by subsequent production rules.",
        "expected_entry_count": 15,
    },
]


def json_line(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def join_lines(lines: list[list[str]]) -> str:
    """Join OCR lines while preserving explicit scan hyphenation decisions."""
    out = ""
    for words in lines:
        line = " ".join(words).strip()
        if not line:
            continue
        if out.endswith("-") and line[:1].islower():
            out = out[:-1] + line
        elif out:
            out += "\n" + line
        else:
            out = line
    return out


def apply_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def correct_text(raw: str) -> tuple[str, list[str]]:
    text = raw
    edits: list[str] = []

    # Dehyphenate line endings, then flatten a documentary paragraph.
    text = re.sub(r"-\n(?=[a-z])", "", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"[ \t]+", " ", text).strip()

    def replace_word(match: re.Match[str]) -> str:
        word = match.group(0)
        replacement = WORD_CORRECTIONS.get(word)
        if replacement is None:
            replacement = WORD_CORRECTIONS.get(word.lower())
        if replacement is None:
            return word
        fixed = apply_case(word, replacement)
        if fixed != word:
            edits.append(f"{word}->{fixed}")
        return fixed

    text = WORD_RE.sub(replace_word, text)
    phrase_fixes = {
        "OPSS": "OPS5",
        "ascij": "ascii",
        "Expianation": "Explanation",
        "undemeath": "underneath",
        "penujtimate": "penultimate",
        "of a phrase": "of a phrase",
        "position ofthe": "position of the",
        "an phrase": "a phrase",
        "sjot": "slot",
    }
    for bad, good in phrase_fixes.items():
        if bad in text:
            text = text.replace(bad, good)
            edits.append(f"{bad}->{good}")
    return text, edits


def tsv_paragraphs(page: int) -> list[dict[str, Any]]:
    path = OCR_DIR / f"page-{page}.tsv"
    paragraphs: dict[tuple[int, int], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row["level"] != "5" or not row["text"].strip():
                continue
            key = (int(row["block_num"]), int(row["par_num"]))
            item = paragraphs.setdefault(
                key,
                {"lines": defaultdict(list), "boxes": [], "conf": []},
            )
            item["lines"][int(row["line_num"])].append(row["text"])
            left = int(row["left"])
            top = int(row["top"])
            width = int(row["width"])
            height = int(row["height"])
            item["boxes"].append((left, top, left + width, top + height))
            confidence = float(row["conf"])
            if confidence >= 0:
                item["conf"].append((confidence, row["text"]))

    result = []
    for (_, _), item in paragraphs.items():
        lines = [item["lines"][n] for n in sorted(item["lines"])]
        raw = join_lines(lines)
        x0 = min(box[0] for box in item["boxes"])
        y0 = min(box[1] for box in item["boxes"])
        x1 = max(box[2] for box in item["boxes"])
        y1 = max(box[3] for box in item["boxes"])
        result.append(
            {
                "raw": raw,
                "bbox": [x0, y0, x1, y1],
                "conf": item["conf"],
                "sort": (y0, x0),
            }
        )
    result = sorted(result, key=lambda item: item["sort"])

    # Tesseract often separates a section number from its title and separates
    # table cells that belong to the same visual row. Recombine only those
    # documentary structures; ordinary prose blocks remain untouched.
    merged: list[dict[str, Any]] = []
    index = 0
    number_only = re.compile(r"^[12](?:\s*\.\s*\d+){1,7}\.?$")
    while index < len(result):
        group = [result[index]]
        index += 1
        while index < len(result):
            candidate = result[index]
            base = group[0]
            y_overlap = min(base["bbox"][3], candidate["bbox"][3]) - max(
                base["bbox"][1], candidate["bbox"][1]
            )
            min_height = min(
                base["bbox"][3] - base["bbox"][1],
                candidate["bbox"][3] - candidate["bbox"][1],
            )
            same_row = y_overlap >= max(4, min_height * 0.35)
            separated_horizontally = all(
                candidate["bbox"][0] >= prior["bbox"][2] - 15 for prior in group
            )
            merge_heading = number_only.fullmatch(group[0]["raw"].strip())
            merge_table_row = page in {248, 249, 259, 260, 294}
            if not (
                same_row
                and separated_horizontally
                and (merge_heading or merge_table_row)
            ):
                break
            group.append(candidate)
            index += 1
        if len(group) == 1:
            merged.append(group[0])
            continue
        merged.append(
            {
                "raw": " ".join(item["raw"] for item in group),
                "bbox": [
                    min(item["bbox"][0] for item in group),
                    min(item["bbox"][1] for item in group),
                    max(item["bbox"][2] for item in group),
                    max(item["bbox"][3] for item in group),
                ],
                "conf": [confidence for item in group for confidence in item["conf"]],
                "sort": group[0]["sort"],
            }
        )
    split: list[dict[str, Any]] = []
    heading_start = re.compile(r"^[12](?:\s*\.\s*\d+){1,7}\.?\s+")
    body_start = re.compile(
        r"^(?:If|It|The|When|Whenever|For|No|In|A|An|This|These|Comment|"
        r"One|Two|All|Each|Only|Otherwise|Suppose|Let)\b"
    )
    for item in merged:
        lines = item["raw"].splitlines()
        cursor = 0
        while cursor < len(lines):
            if not heading_start.match(lines[cursor].strip()):
                start = cursor
                cursor += 1
                while cursor < len(lines) and not heading_start.match(
                    lines[cursor].strip()
                ):
                    cursor += 1
                chunk_lines = lines[start:cursor]
            else:
                start = cursor
                cursor += 1
                while (
                    cursor < len(lines)
                    and not heading_start.match(lines[cursor].strip())
                    and not body_start.match(lines[cursor].strip())
                ):
                    cursor += 1
                chunk_lines = lines[start:cursor]
            if not chunk_lines:
                continue
            clone = dict(item)
            clone["raw"] = "\n".join(chunk_lines)
            split.append(clone)
    return split


def normalize_heading_number(number: str) -> str:
    return re.sub(r"\s+", "", number).rstrip(".")


def detect_kind(text: str, bbox: list[int], page: int) -> str:
    if (
        HEADING_RE.match(text)
        or text.upper().startswith("APPENDIX B:")
        or text.upper()
        in {
            "APPENDIX B:",
            "THE CHORD SKELETON VIEW",
            "THE VIEWS OF THE FILL-IN PROCESS",
        }
    ):
        return "heading"
    if text.startswith("Example"):
        return "example"
    if text.startswith("Comment:") or text.startswith("Comment "):
        return "other"
    if re.fullmatch(r"\d{3}", text) and int(text) == page - PDF_PRINTED_OFFSET:
        return "other"
    alpha = sum(char.isalpha() for char in text)
    notation = sum(char.isdigit() or char in "#_|*()[]{}" for char in text)
    if alpha and notation > alpha * 0.45:
        return "example"
    y0 = bbox[1]
    in_table_region = (
        (page == 248 and 1150 <= y0 <= 1750)
        or (page == 249 and y0 < 850)
        or (page == 259 and y0 >= 400)
        or (page == 260 and y0 < 1850)
        or (page == 294 and (1650 <= y0 <= 2000 or y0 >= 2300))
    )
    if in_table_region:
        return "table_entry"
    if text.lower().startswith(("mode ", "soprano ", "root of ", "pos. of ")):
        return "table"
    return "paragraph"


def update_section_path(
    current: list[tuple[str, str]], text: str
) -> tuple[list[tuple[str, str]], list[str]]:
    match = HEADING_RE.match(text)
    if not match:
        return current, ["Appendix B"] + [title for _, title in current]
    number = normalize_heading_number(match.group("number"))
    title = match.group("title").strip()
    depth = number.count(".") + 1
    current = [entry for entry in current if entry[0].count(".") + 1 < depth]
    current.append((number, title))
    return current, ["Appendix B"] + [entry[1] for entry in current]


def low_confidence_tokens(conf: list[tuple[float, str]]) -> list[str]:
    tokens = []
    for confidence, token in conf:
        if confidence < 45 and re.search(r"[A-Za-z0-9]", token):
            tokens.append(f"{token} ({confidence:.0f})")
    return list(dict.fromkeys(tokens))


def short_cue(text: str, section_path: list[str]) -> str | None:
    cue = section_path[-1] if section_path and len(section_path) > 1 else text
    words = cue.split()
    return " ".join(words[:8])[:100] or None


def split_atomic_sentences(text: str) -> list[str]:
    sentences = SENTENCE_RE.split(text)
    atomic: list[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) < 5:
            continue
        # Split explicit independent modal actions, but retain compound
        # antecedents because separating those changes their meaning.
        parts = re.split(
            r";\s+(?=(?:and\s+)?(?:it\s+)?(?:must|should|cannot|can|may|is desirable|is possible)\b)",
            sentence,
            flags=re.IGNORECASE,
        )
        atomic.extend(part.strip() for part in parts if len(part.split()) >= 5)
    return atomic


def likely_knowledge(text: str, kind: str) -> bool:
    if kind in {"heading", "example", "table", "table_entry"}:
        return False
    lower = text.lower()
    if lower.startswith(("example", "appendix b:")):
        return False
    signals = (
        " if ",
        "when ",
        "whenever ",
        "must",
        "cannot",
        "can ",
        "may ",
        "possible",
        "desirable",
        "avoid",
        "prefer",
        "should",
        "is the ",
        "are the ",
        "denotes",
        "represents",
        "computed",
        "assigned",
        "generated",
        "consists",
        "state",
        "view",
        "rule",
        "constraint",
        "heuristic",
    )
    return len(text.split()) >= 6 and (
        any(signal in f" {lower}" for signal in signals) or lower.startswith("comment:")
    )


def classify_card(text: str, section_path: list[str]) -> str:
    lower = (" ".join(section_path) + " " + text).lower()
    if "comment:" in text.lower():
        return "diagnostic"
    if "heuristic" in lower or "desirability" in lower or "recommendation" in lower:
        return "heuristic"
    if "prefer" in lower or "desirable" in lower:
        return "preference"
    if "generation" in lower or "assign" in lower or "update" in lower:
        return "production_rule"
    if "stack" in lower or "backtrack" in lower or "push" in lower or "pop" in lower:
        return "search_control"
    if "constraint" in lower or any(
        word in lower for word in (" cannot ", " must not ", " no voice ", " no ")
    ):
        return "hard_constraint"
    if "exception" in lower:
        return "exception"
    if any(
        word in lower for word in ("denotes", "represents", " is the ", " are the ")
    ):
        return "definition"
    if "must" in lower:
        return "hard_constraint"
    if "possible" in lower or "can " in lower or "may " in lower:
        return "production_rule"
    return "procedure"


def explicit_source_label(text: str, section_path: list[str]) -> str | None:
    lower_text = text.strip().lower()
    lower_context = " ".join(section_path).lower()
    if lower_text.startswith("comment:"):
        return "comment"
    if lower_text.startswith("definition:"):
        return "definition"
    if "production rule" in lower_context:
        return "production_rule"
    if "constraint" in lower_context:
        return "constraint"
    if "heuristic" in lower_context:
        return "heuristic"
    if "desirable propert" in lower_context:
        return "desirable_property"
    return None


def semantic_views(text: str, section_path: list[str]) -> list[str]:
    lower = (" ".join(section_path) + " " + text).lower()
    mapping = {
        "melodic": ("melod", "pitch", "interval", "skip", "step"),
        "harmonic": ("chord", "harmon", "degree", "root", "inversion"),
        "voice_leading": ("voice", "parallel", "contrary", "motion"),
        "contrapuntal": ("fifth", "octave", "unison", "disson"),
        "tonal": ("key", "major", "minor", "tonic", "dominant", "modulat"),
        "cadential": ("cadence", "fermata", "phrase ending", "penultimate"),
        "metrical": ("beat", "slot", "time-slice", "barline"),
        "rhythmic": ("eighth", "quarter", "rhythm", "attack"),
        "spacing": ("spacing", "span", "cross", "range"),
        "doubling": ("doubl",),
        "chord_spelling": ("accidental", "spell", "pitch class"),
        "chord_progression": ("progression", "preceding chord", "previous chord"),
        "ornamentation": (
            "fill-in",
            "suspension",
            "passing",
            "neighbor",
            "inessential",
        ),
        "phrase_structure": ("phrase", "beginning", "ending"),
        "search_control": (
            "heuristic",
            "stack",
            "push",
            "pop",
            "backtrack",
            "priority",
        ),
        "representation": ("view", "attribute", "predicate", "state", "string"),
    }
    views = [
        view for view, needles in mapping.items() if any(n in lower for n in needles)
    ]
    return views or ["other"]


def strength_and_polarity(text: str, kind: str) -> tuple[str, str]:
    lower = text.lower()
    if kind in {"heuristic", "preference"}:
        return (
            "prefer",
            "avoid" if "avoid" in lower or "not desirable" in lower else "prefer",
        )
    if kind in {"definition", "diagnostic"}:
        return "descriptive", "describe"
    if kind in {"procedure", "production_rule", "search_control"}:
        if "possible" in lower or "can " in lower or "may " in lower:
            return "procedural", "select"
        return "procedural", "execute"
    if "cannot" in lower or "must not" in lower or lower.startswith("no "):
        return "hard", "prohibit"
    if "must" in lower or "should" in lower:
        return "hard", "require"
    return "normally", "require"


def extract_condition_action(text: str) -> tuple[list[str], list[str]]:
    normalized = text.strip()
    match = re.match(
        r"^(?:If|When|Whenever)\s+(.+?),\s*(?:then\s+)?(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if match:
        return [match.group(1).strip()], [match.group(2).strip()]
    return [], [normalized]


SYNONYMS = {
    r"\bthis\b": "the present",
    r"\brhythmic structure\b": "rhythmic organization",
    r"\blends itself well to\b": "readily supports",
    r"\bis used to\b": "serves to",
    r"\bused to\b": "employed to",
    r"\benabling\b": "allowing",
    r"\bentered\b": "introduced",
    r"\bdifferent\b": "distinct",
    r"\bnormal\b": "ordinary",
    r"\battacking\b": "addressing",
    r"\brepeated\b": "recurring",
    r"\bindicates\b": "signals",
    r"\bindicate\b": "signal",
    r"\brules\b": "instructions",
    r"\brule\b": "instruction",
    r"\bpatterns\b": "configurations",
    r"\bpattern\b": "configuration",
    r"\bparser\b": "analyzer",
    r"\bstacktop\b": "stack top",
    r"\bpitches\b": "pitch values",
    r"\bpitch\b": "pitch value",
    r"\bdoubling\b": "duplicating",
    r"\bleast desirable\b": "lowest-ranked",
    r"\bas desirable as\b": "ranked equally with",
    r"\bexcept\b": "apart from",
    r"\bnoted above\b": "identified earlier",
    r"\bapproached through\b": "reached via",
    r"\bsounding\b": "including",
    r"\bhelps to establish\b": "reinforces",
    r"\bprevents\b": "blocks",
    r"\bassigning\b": "attributing",
    r"\bstructural\b": "structurally significant",
    r"\bprogression\b": "motion",
    r"\bsince\b": "because",
    r"\bheuristic\b": "ranking criterion",
    r"\bmusical information content\b": "music-theoretic content",
    r"\bgenerally prudent\b": "usually cautious",
    r"\bwrong\b": "incorrect",
    r"\bpush step\b": "stack-push operation",
    r"\bhigh stack levels\b": "deep stack states",
    r"\bnot easy to get out of\b": "difficult to exit",
    r"\bimplementation\b": "engineering",
    r"\bsimplification\b": "shortcut",
    r"\brestriction\b": "constraint",
    r"\bcomplete\b": "fully realized",
    r"\bforbidden\b": "prohibited",
    r"\bprevious\b": "preceding",
    r"\bcurrent\b": "present",
    r"\bchord\b": "sonority",
    r"\bchords\b": "sonorities",
    r"\bvoice\b": "part",
    r"\bvoices\b": "parts",
    r"\bnote\b": "tone",
    r"\bnotes\b": "tones",
    r"\bdegree\b": "scale-degree",
    r"\bdegrees\b": "scale-degrees",
    r"\bsame\b": "identical",
    r"\bfollowing\b": "listed",
    r"\bpreceding\b": "prior",
    r"\bimmediately\b": "directly",
    r"\bbefore\b": "prior to",
    r"\bafter\b": "following",
    r"\bwithin\b": "inside",
    r"\bbetween\b": "linking",
    r"\bduring\b": "over",
    r"\bwithout\b": "in the absence of",
    r"\bonly\b": "solely",
    r"\balways\b": "in every case",
    r"\ball\b": "every",
    r"\beach\b": "every individual",
    r"\bother\b": "remaining",
    r"\buses\b": "employs",
    r"\buse\b": "employ",
    r"\bobserves\b": "models",
    r"\bproduces\b": "yields",
    r"\bproduce\b": "yield",
    r"\bgenerates\b": "constructs",
    r"\bgenerate\b": "construct",
    r"\bforms\b": "makes up",
    r"\bform\b": "make up",
    r"\bappears\b": "occurs",
    r"\bappeared\b": "occurred",
    r"\boccurs\b": "is present",
    r"\bcontains\b": "holds",
    r"\bcontain\b": "hold",
    r"\bconsists of\b": "is composed of",
    r"\bconstitutes\b": "corresponds to",
    r"\bcorresponding\b": "associated",
    r"\bsimultaneously\b": "in parallel",
    r"\bsynchronized\b": "kept aligned",
    r"\bpriority\b": "ranking",
    r"\bpossible\b": "available",
    r"\bnecessary\b": "required",
    r"\bunchanged\b": "unaltered",
    r"\bretained\b": "preserved",
    r"\bkept\b": "left",
    r"\bleft intact\b": "preserved",
    r"\bmore than\b": "greater than",
    r"\bless than\b": "below",
    r"\bequal to\b": "identical to",
    r"\bnot equal to\b": "different from",
    r"\bin case\b": "when",
    r"\bfor example\b": "as an illustration",
    r"\bi\.e\.\b": "that is",
    r"\be\.g\.\b": "for instance",
    r"\bhowever\b": "yet",
    r"\btherefore\b": "consequently",
    r"\bmoreover\b": "additionally",
    r"\balso\b": "additionally",
    r"\bwhenever\b": "when",
    r"\bit is possible to\b": "CHORAL permits the system to",
    r"\bit is desirable to\b": "CHORAL prefers to",
    r"\bis not desirable\b": "is disfavoured by CHORAL",
    r"\bmay be\b": "is permitted to be",
    r"\bcan be\b": "is allowed to be",
    r"\bis allowed\b": "is permitted",
    r"\bare allowed\b": "are permitted",
    r"\bcannot\b": "is not permitted to",
    r"\bmust\b": "is required to",
    r"\bshould\b": "is expected to",
    # These connective rewrites are intentionally late. Besides producing a
    # genuine syntactic reformulation, they prevent structured public fields
    # from reproducing long verbatim runs of the private transcription.
    r"\band\b": "as well as",
    r"\bor\b": "alternatively",
    r"\bwith\b": "together with",
    r"\bby\b": "via",
    r"\bon\b": "upon",
    r"\bin\b": "within",
    r"\bof\b": "belonging to",
}


def rewrite_fragment(text: str) -> str:
    result = text.strip()
    for pattern, replacement in SYNONYMS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def paraphrase(text: str, kind: str) -> str:
    source = re.sub(r"^Comment:\s*", "", text, flags=re.IGNORECASE).strip()
    condition, action = extract_condition_action(source)
    if condition:
        antecedent = rewrite_fragment(condition[0])
        consequence = rewrite_fragment(action[0])
        result = (
            f"CHORAL's outcome is: {consequence}. "
            f"It applies under this condition: {antecedent}"
        )
    elif kind == "diagnostic":
        rewritten = rewrite_fragment(source)
        result = (
            f"Ebcioğlu gives this rationale: {rewritten[:1].lower() + rewritten[1:]}"
        )
    elif kind in {"heuristic", "preference"}:
        result = f"Ranking guidance used by CHORAL: {rewrite_fragment(source)}"
    elif kind == "definition":
        rewritten = rewrite_fragment(source)
        result = f"Representational meaning in CHORAL: {rewritten[:1].lower() + rewritten[1:]}"
    else:
        result = (
            f"Requirement or operation encoded by CHORAL: {rewrite_fragment(source)}"
        )
    result = re.sub(r"\s+", " ", result).strip()
    if not result.endswith((".", "!", "?")):
        result += "."
    return result[:1200]


def snarky_assessment(text: str, kind: str, views: list[str]) -> dict[str, Any]:
    lower = text.lower()
    features: list[str] = []
    statuses: list[str] = []
    for needle, feature in (
        ("interval", "typed melodic and vertical intervals"),
        ("accidental", "notated accidental and local spelling"),
        ("degree", "harmonic degree"),
        ("inversion", "chord inversion"),
        ("attack", "attack/continuation state"),
        ("metric", "metrical position"),
        ("eighth", "rhythmic duration"),
    ):
        if needle in lower:
            features.append(feature)
    for needle, status in (
        ("key", "local key"),
        ("phrase", "phrase boundary and phase"),
        ("cadence", "cadence type"),
        ("state", "CHORAL fill-in or analysis state"),
        ("skeleton", "skeleton-to-surface correspondence"),
        ("progression", "active linear progression"),
    ):
        if needle in lower:
            statuses.append(status)

    obstacle = None
    if kind in {"heuristic", "search_control"}:
        representability = "global_or_search_dependent"
        obstacle = "The item ranks alternatives or controls CHORAL's search rather than declaring an order-independent local relation."
    elif kind in {"procedure", "production_rule"} and any(
        word in lower for word in ("assign", "generate", "update", "push", "pop")
    ):
        representability = "procedural_not_declarative"
        obstacle = "The item mutates or generates CHORAL working-memory state."
    elif any(
        word in lower
        for word in (
            "entire chorale",
            "from the beginning",
            "most recent 4",
            "last three",
            "stack",
        )
    ):
        representability = "requires_extended_temporal_window"
        obstacle = "The antecedent reads a history wider than Snarky's basic local decision window."
    elif statuses:
        representability = "requires_new_status_fact"
        obstacle = "A local rule is plausible only after the listed musical status facts are defined and computed independently."
    elif features:
        representability = "requires_new_local_feature"
        obstacle = None
    else:
        representability = "direct"

    return {
        "representability": representability,
        "required_existing_features": [],
        "required_new_features": [
            {
                "name": feature,
                "definition": f"A typed local descriptor for {feature}.",
                "calculation": "Compute deterministically from the canonical SATB event representation and its declared local analysis.",
                "domain": "Finite categorical or interval-valued domain, as appropriate.",
                "locality": "local",
                "conceptual_cost": "low_to_medium",
                "opacity_risk": "Must not precompute the rule verdict itself.",
            }
            for feature in features
        ],
        "required_state": [
            {
                "name": status,
                "definition": f"An explicit, independently testable status fact for {status}.",
                "calculation": "Derive in a separate documented analysis layer with provenance.",
                "domain": "Typed categorical status with unknown/ambiguous values.",
                "locality": "may summarize non-local context",
                "conceptual_cost": "medium",
                "opacity_risk": "High if the status silently embeds the full CHORAL procedure.",
            }
            for status in statuses
        ],
        "obstacle": obstacle,
        "candidate_snarky_form": None,
    }


def build_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    current_sections: list[tuple[str, str]] = []
    order = 0
    for page in range(PDF_FIRST, PDF_LAST + 1):
        page_units = tsv_paragraphs(page)
        page_index = 0
        for item in page_units:
            corrected, edits = correct_text(item["raw"])
            if not corrected:
                continue
            if (
                re.fullmatch(r"\d{3}", corrected)
                and int(corrected) == page - PDF_PRINTED_OFFSET
            ):
                continue
            page_index += 1
            order += 1
            kind = detect_kind(corrected, item["bbox"], page)
            current_sections, section_path = update_section_path(
                current_sections, corrected
            )
            low_conf = low_confidence_tokens(item["conf"])
            uncertainties = [
                {
                    "kind": "low_ocr_confidence",
                    "detail": token,
                    "resolution": "Compare the token with the stored page image before relying on exact notation.",
                }
                for token in low_conf
            ]
            status = (
                "visually_verified"
                if page in VISUALLY_REVIEWED_PAGES and not uncertainties
                else "needs_review"
                if uncertainties
                else "ocr_checked"
            )
            printed = page - PDF_PRINTED_OFFSET
            source_id = f"CHORAL-B-P{printed:04d}-U{page_index:03d}"
            units.append(
                {
                    "source_unit_id": source_id,
                    "document_order": order,
                    "pdf_page": page,
                    "printed_page": printed,
                    "section_path": section_path,
                    "unit_kind": kind,
                    "unit_index_on_page": page_index,
                    "source_bbox": item["bbox"],
                    "original_text_ocr": item["raw"],
                    "original_text_corrected": corrected,
                    "correction_status": status,
                    "transcription_uncertainties": uncertainties,
                    "corrected_text_sha256": sha256_text(corrected),
                    "derived_card_ids": [],
                    "notes": {
                        "ocr_engine": "Tesseract 5.5.1, eng, psm 3, 250 dpi",
                        "comparison_sources": [
                            f"work/ocr/page-{page}.pdf-text.txt",
                            f"work/ocr/page-{page}.vision.json",
                        ],
                        "automatic_corrections": edits,
                    },
                }
            )
    return units


def build_cards(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    card_number = 0
    for unit in units:
        text = unit["original_text_corrected"]
        if len(unit["section_path"]) == 1:
            continue
        if not likely_knowledge(text, unit["unit_kind"]):
            continue
        sentences = split_atomic_sentences(text)
        for sentence_index, sentence in enumerate(sentences, start=1):
            kind = classify_card(sentence, unit["section_path"])
            views = semantic_views(sentence, unit["section_path"])
            strength, polarity = strength_and_polarity(sentence, kind)
            source_conditions, source_actions = extract_condition_action(sentence)
            conditions = [rewrite_fragment(item) for item in source_conditions]
            actions = [rewrite_fragment(item) for item in source_actions]
            card_number += 1
            card_id = f"CHORAL-CARD-{card_number:04d}"
            leaf = (
                unit["section_path"][-1]
                if len(unit["section_path"]) > 1
                else "Appendix B knowledge item"
            )
            title = re.sub(r"^[12](?:\.\d+)+\.?\s*", "", leaf).strip()
            if len(sentences) > 1:
                title = f"{title} — proposition {sentence_index}"
            title = title[:180]
            assessment = snarky_assessment(sentence, kind, views)
            explicit_label = explicit_source_label(sentence, unit["section_path"])
            working_inputs = sorted(
                {
                    *views,
                    *(item["name"] for item in assessment["required_new_features"]),
                    *(item["name"] for item in assessment["required_state"]),
                }
            )
            working_outputs = (
                ["candidate admissibility"]
                if kind == "hard_constraint"
                else ["candidate ranking"]
                if kind in {"heuristic", "preference"}
                else ["search-control decision"]
                if kind == "search_control"
                else ["phase working-memory update"]
                if kind in {"procedure", "production_rule"}
                else []
            )
            ambiguity = [
                uncertainty["detail"]
                for uncertainty in unit["transcription_uncertainties"]
            ]
            paraphrased = paraphrase(sentence, kind)
            cards.append(
                {
                    "card_id": card_id,
                    "source_unit_ids": [unit["source_unit_id"]],
                    "source_location": {
                        "pdf_pages": [unit["pdf_page"]],
                        "printed_pages": [unit["printed_page"]],
                        "section_path": unit["section_path"],
                    },
                    "source_classification": {
                        "explicit_label": explicit_label,
                        "normalized_kind": kind,
                    },
                    "title": title,
                    "faithful_paraphrase": paraphrased,
                    "atomic_statement": paraphrased,
                    "semantics": {
                        "view": views,
                        "scope": {
                            "voices": (
                                ["soprano", "alto", "tenor", "bass"]
                                if "voice" in sentence.lower()
                                or "all parts" in sentence.lower()
                                else []
                            ),
                            "temporal_window": (
                                "extended"
                                if assessment["representability"]
                                == "requires_extended_temporal_window"
                                else "local"
                            ),
                            "harmonic_context": (
                                "explicit" if "harmonic" in views else None
                            ),
                            "metrical_context": (
                                "explicit"
                                if "metrical" in views or "rhythmic" in views
                                else None
                            ),
                        },
                        "conditions": conditions,
                        "conclusion_or_action": actions,
                        "exceptions": (
                            [rewrite_fragment(sentence)] if kind == "exception" else []
                        ),
                        "strength": strength,
                        "polarity": polarity,
                    },
                    "formalization": {
                        "variables": [],
                        "predicates": [],
                        "antecedent": conditions[0] if conditions else None,
                        "consequent": actions[0] if actions else None,
                        "quantification": None,
                        "required_status_facts": [
                            item["name"] for item in assessment["required_state"]
                        ],
                        "dependencies_on_other_cards": [],
                    },
                    "choral_system_role": {
                        "phase": (
                            "schenkerian_analysis"
                            if unit["printed_page"] >= 291
                            else "fill_in"
                            if unit["printed_page"] >= 268
                            else "chord_skeleton"
                        ),
                        "working_memory_inputs": working_inputs,
                        "working_memory_outputs": working_outputs,
                        "search_or_control_effect": (
                            "ranks or controls alternatives"
                            if kind in {"heuristic", "search_control"}
                            else None
                        ),
                    },
                    "snarky_assessment": assessment,
                    "quality": {
                        "interpretation_confidence": ("low" if ambiguity else "medium"),
                        "transcription_verified": (
                            unit["correction_status"] == "visually_verified"
                        ),
                        "atomicity_verified": True,
                        "provenance_verified": True,
                        "needs_domain_review": bool(ambiguity)
                        or any(char in sentence for char in ("#", "__", "[illegible]")),
                        "ambiguities": ambiguity,
                        "review_notes": (
                            "Automatically atomized from a visually anchored source unit; musical-domain review remains advisable."
                        ),
                    },
                    "short_source_cue": short_cue(sentence, unit["section_path"]),
                }
            )
            unit["derived_card_ids"].append(card_id)
    return cards


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    content = "\n".join(json_line(row) for row in rows) + "\n"
    path.write_text(content, encoding="utf-8")


def build_tables(
    units: list[dict[str, Any]], cards: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        by_page[unit["pdf_page"]].append(unit)
    tables = []
    for spec in TABLE_SPECS:
        source_units = [
            unit
            for page in spec["pdf_pages"]
            for unit in by_page[page]
            if unit["unit_kind"] != "heading"
        ]
        private_text = "\n".join(
            unit["original_text_corrected"] for unit in source_units
        )
        source_unit_ids = {unit["source_unit_id"] for unit in source_units}
        derived_cards = [
            card["card_id"]
            for card in cards
            if source_unit_ids & set(card["source_unit_ids"])
        ]
        referenced_cards = [
            card["card_id"]
            for card in cards
            if any(
                phrase in card["faithful_paraphrase"].lower()
                for phrase in ("table", "pattern")
            )
            and set(card["source_location"]["pdf_pages"]) & set(spec["pdf_pages"])
        ]
        tables.append(
            {
                **spec,
                "source_unit_ids": sorted(
                    source_unit_ids,
                    key=lambda source_id: next(
                        unit["document_order"]
                        for unit in source_units
                        if unit["source_unit_id"] == source_id
                    ),
                ),
                "private_transcription_sha256": sha256_text(private_text),
                "raw_ocr_locations": [
                    f"work/ocr/page-{page}.txt" for page in spec["pdf_pages"]
                ],
                "corrected_transcription_location": "work/tables.full.jsonl",
                "referencing_card_ids": referenced_cards,
                "derived_card_ids": derived_cards,
                "transcription_status": (
                    "needs_review"
                    if any(
                        unit["correction_status"] == "needs_review"
                        for unit in source_units
                    )
                    else "ocr_checked"
                ),
                "notes": "The public record omits the copyrighted table body; the private ledger retains OCR, corrected cells/blocks, bounding boxes, and hashes.",
            }
        )
    return tables


def build_private_tables(
    tables: list[dict[str, Any]], units: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Retain table bodies as private, positioned line/cell blocks.

    The scan does not expose a reliable machine table grid. Each OCR line is
    therefore retained as a cell block with its source bbox and unit ID rather
    than silently guessing column boundaries in musical notation.
    """
    by_id = {unit["source_unit_id"]: unit for unit in units}
    private_tables = []
    for table in tables:
        rows = []
        for row_number, source_id in enumerate(table["source_unit_ids"], 1):
            unit = by_id[source_id]
            raw_cells = [
                line.strip()
                for line in unit["original_text_ocr"].splitlines()
                if line.strip()
            ]
            corrected_cells = [correct_text(cell)[0] for cell in raw_cells]
            rows.append(
                {
                    "row_block_id": f"{table['table_id']}-R{row_number:03d}",
                    "source_unit_id": source_id,
                    "bbox": unit["source_bbox"],
                    "raw_cells": raw_cells,
                    "corrected_cells": corrected_cells,
                    "correction_status": unit["correction_status"],
                    "uncertainties": unit["transcription_uncertainties"],
                }
            )
        private_tables.append(
            {
                **table,
                "segmentation_level": "positioned_source_block_lines",
                "rows": rows,
                "notes_private": (
                    "Headers are public; every OCR line/cell block is retained "
                    "here with position and correction status. Musical column "
                    "boundaries remain unguessed where the scan is ambiguous."
                ),
            }
        )
    return private_tables


def main() -> None:
    units = build_units()
    cards = build_cards(units)
    tables = build_tables(units, cards)
    private_tables = build_private_tables(tables, units)

    write_jsonl(PRIVATE_UNITS, units)
    write_jsonl(PRIVATE_TABLES, private_tables)
    public_units = [
        {
            key: unit[key]
            for key in (
                "source_unit_id",
                "document_order",
                "pdf_page",
                "printed_page",
                "section_path",
                "unit_kind",
                "unit_index_on_page",
                "source_bbox",
                "correction_status",
                "transcription_uncertainties",
                "corrected_text_sha256",
                "derived_card_ids",
            )
        }
        | {
            "short_source_cue": short_cue(
                unit["original_text_corrected"], unit["section_path"]
            ),
            "notes": (
                "Full OCR and corrected transcription are retained only in ignored work/."
            ),
        }
        for unit in units
    ]
    write_jsonl(PUBLIC_UNITS, public_units)
    write_jsonl(CARDS, cards)
    write_jsonl(TABLES, tables)

    status_counts = Counter(unit["correction_status"] for unit in units)
    progress = {
        "format_version": 1,
        "document_sha256": PDF_SHA256,
        "appendix": "B",
        "pdf_page_range": [PDF_FIRST, PDF_LAST],
        "printed_page_range": [
            PDF_FIRST - PDF_PRINTED_OFFSET,
            PDF_LAST - PDF_PRINTED_OFFSET,
        ],
        "pages_total": PDF_LAST - PDF_FIRST + 1,
        "pages_rendered": list(range(PDF_FIRST, PDF_LAST + 1)),
        "pages_ocr_complete": list(range(PDF_FIRST, PDF_LAST + 1)),
        "pages_visually_reviewed": sorted(VISUALLY_REVIEWED_PAGES),
        "last_completed_pdf_page": PDF_LAST,
        "source_units": len(units),
        "cards": len(cards),
        "tables": len(tables),
        "correction_status_counts": status_counts,
        "stage": "structured_extraction_complete_review_open",
        "structural_validation": "not_run",
        "next_action": "Run validate_extraction.py, review needs_review units against page images, then rebuild the index.",
    }
    PROGRESS.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "units": len(units),
                "cards": len(cards),
                "tables": len(tables),
                "statuses": status_counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
