#!/usr/bin/env python3
# ruff: noqa: E501
"""Validate the public CHORAL extraction and its private provenance ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "choral_items.schema.json"
SOURCE_META = ROOT / "appendix_b_source_units.metadata.jsonl"
CARDS = ROOT / "appendix_b_cards.jsonl"
TABLES = ROOT / "tables.jsonl"
PRIVATE = ROOT / "work" / "source_units.full.jsonl"
PRIVATE_TABLES = ROOT / "work" / "tables.full.jsonl"
PROGRESS = ROOT / "PROGRESS.json"
DEFAULT_REPORT = ROOT / "VALIDATION_REPORT.json"

EXPECTED_PDF_PAGES = set(range(243, 321))
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^CHORAL-B-P\d{4}-U\d{3}$")
CARD_ID_RE = re.compile(r"^CHORAL-CARD-\d{4}$")
TABLE_ID_RE = re.compile(r"^CHORAL-TABLE-P\d{4}-T\d{2}$")

REQUIRED = {
    "source_metadata": {
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
        "short_source_cue",
        "notes",
    },
    "card": {
        "card_id",
        "source_unit_ids",
        "source_location",
        "source_classification",
        "title",
        "faithful_paraphrase",
        "atomic_statement",
        "semantics",
        "formalization",
        "choral_system_role",
        "snarky_assessment",
        "quality",
        "short_source_cue",
    },
    "table": {
        "table_id",
        "pdf_pages",
        "printed_pages",
        "title",
        "columns",
        "role",
        "expected_entry_count",
        "source_unit_ids",
        "private_transcription_sha256",
        "raw_ocr_locations",
        "corrected_transcription_location",
        "referencing_card_ids",
        "derived_card_ids",
        "transcription_status",
        "notes",
    },
}


def read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{line_no}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.name}:{line_no}: record is not an object")
            continue
        rows.append(value)
    return rows


def record_kind(row: dict[str, Any]) -> str | None:
    if "source_unit_id" in row:
        return "source_metadata"
    if "card_id" in row:
        return "card"
    if "table_id" in row:
        return "table"
    return None


def _schema_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }[expected]


def _validate_schema_node(
    value: Any,
    node: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    issues: list[str],
) -> None:
    """Validate the Draft 2020-12 keywords used by this repository's schema."""
    if "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            issues.append(f"{path}: unsupported external $ref {ref}")
            return
        target: Any = root_schema
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        _validate_schema_node(value, target, root_schema, path, issues)
        return
    if "oneOf" in node:
        attempts: list[list[str]] = []
        for branch in node["oneOf"]:
            branch_issues: list[str] = []
            _validate_schema_node(value, branch, root_schema, path, branch_issues)
            attempts.append(branch_issues)
        if sum(not branch for branch in attempts) != 1:
            issues.append(f"{path}: must match exactly one oneOf branch")
        return
    expected = node.get("type")
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_schema_type_matches(value, choice) for choice in choices):
            issues.append(
                f"{path}: expected type {choices}, got {type(value).__name__}"
            )
            return
    if "enum" in node and value not in node["enum"]:
        issues.append(f"{path}: value {value!r} is outside enum")
    if isinstance(value, str):
        if "minLength" in node and len(value) < node["minLength"]:
            issues.append(f"{path}: shorter than minLength")
        if "maxLength" in node and len(value) > node["maxLength"]:
            issues.append(f"{path}: longer than maxLength")
        if "pattern" in node and not re.search(node["pattern"], value):
            issues.append(f"{path}: does not match pattern {node['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            issues.append(f"{path}: below minimum")
        if "maximum" in node and value > node["maximum"]:
            issues.append(f"{path}: above maximum")
    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            issues.append(f"{path}: fewer than minItems")
        if "maxItems" in node and len(value) > node["maxItems"]:
            issues.append(f"{path}: more than maxItems")
        if node.get("uniqueItems"):
            frozen = [
                json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value
            ]
            if len(frozen) != len(set(frozen)):
                issues.append(f"{path}: array items are not unique")
        if "items" in node:
            for index, item in enumerate(value):
                _validate_schema_node(
                    item, node["items"], root_schema, f"{path}[{index}]", issues
                )
    if isinstance(value, dict):
        for key in node.get("required", []):
            if key not in value:
                issues.append(f"{path}: missing required property {key}")
        properties = node.get("properties", {})
        for key, item in value.items():
            if key in properties:
                _validate_schema_node(
                    item, properties[key], root_schema, f"{path}.{key}", issues
                )
            elif node.get("additionalProperties") is False:
                issues.append(f"{path}: additional property {key}")


def validate_schema(
    rows: list[dict[str, Any]], errors: list[str], warnings: list[str]
) -> str:
    """Validate against the checked-in schema without requiring dependencies."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    engine = "built-in validator for the Draft 2020-12 keyword subset used here"
    for row in rows:
        identity = next(
            (
                row.get(key)
                for key in ("source_unit_id", "card_id", "table_id")
                if row.get(key)
            ),
            "<unknown>",
        )
        issues: list[str] = []
        _validate_schema_node(row, schema, schema, "$", issues)
        errors.extend(f"{identity}: schema: {issue}" for issue in issues)

    # If available, the reference implementation provides an additional check.
    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(schema)
        engine += f"; cross-checked with jsonschema {getattr(jsonschema, '__version__', 'installed')}"
        for row in rows:
            for issue in validator.iter_errors(row):
                identity = next(
                    (
                        row.get(key)
                        for key in ("source_unit_id", "card_id", "table_id")
                        if row.get(key)
                    ),
                    "<unknown>",
                )
                path = ".".join(str(item) for item in issue.absolute_path)
                errors.append(f"{identity}: schema {path or '<root>'}: {issue.message}")
    except ImportError:
        pass

    for row in rows:
        kind = record_kind(row)
        if not kind:
            errors.append("record has no recognized identity field")
            continue
        missing = sorted(REQUIRED[kind] - set(row))
        if missing:
            errors.append(
                f"{row.get(next(iter(REQUIRED[kind])), '<unknown>')}: missing {missing}"
            )
    return engine


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    errors: list[str] = []
    warnings: list[str] = []
    findings: dict[str, list[str]] = defaultdict(list)

    sources = read_jsonl(SOURCE_META, errors)
    cards = read_jsonl(CARDS, errors)
    tables = read_jsonl(TABLES, errors)
    private = read_jsonl(PRIVATE, errors) if PRIVATE.exists() else []
    private_tables = (
        read_jsonl(PRIVATE_TABLES, errors) if PRIVATE_TABLES.exists() else []
    )
    all_public = [*sources, *cards, *tables]
    schema_engine = validate_schema(all_public, errors, warnings)

    source_by_id = {row.get("source_unit_id"): row for row in sources}
    card_by_id = {row.get("card_id"): row for row in cards}
    private_by_id = {row.get("source_unit_id"): row for row in private}
    private_table_by_id = {row.get("table_id"): row for row in private_tables}

    for label, rows, key, regex in (
        ("source", sources, "source_unit_id", SOURCE_ID_RE),
        ("card", cards, "card_id", CARD_ID_RE),
        ("table", tables, "table_id", TABLE_ID_RE),
    ):
        ids = [row.get(key) for row in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate {label} IDs")
        for value in ids:
            if not isinstance(value, str) or not regex.fullmatch(value):
                errors.append(f"malformed {label} ID: {value!r}")

    orders = [row.get("document_order") for row in sources]
    if orders != list(range(1, len(sources) + 1)):
        errors.append("source document_order is not contiguous and ordered")

    covered_pages = {row.get("pdf_page") for row in sources}
    missing_pages = sorted(EXPECTED_PDF_PAGES - covered_pages)
    extra_pages = sorted(covered_pages - EXPECTED_PDF_PAGES)
    if missing_pages:
        errors.append(f"pages without source units: {missing_pages}")
    if extra_pages:
        errors.append(f"source units outside Appendix B: {extra_pages}")

    for row in sources:
        sid = row["source_unit_id"]
        if row["printed_page"] != row["pdf_page"] - 9:
            errors.append(f"{sid}: printed/PDF page offset is inconsistent")
        if not SHA_RE.fullmatch(str(row["corrected_text_sha256"])):
            errors.append(f"{sid}: malformed corrected-text SHA-256")
        private_row = private_by_id.get(sid)
        if private_row:
            corrected = private_row.get("original_text_corrected", "")
            if sha256_text(corrected) != row["corrected_text_sha256"]:
                errors.append(f"{sid}: corrected text hash mismatch")
            if private_row.get("derived_card_ids") != row.get("derived_card_ids"):
                errors.append(f"{sid}: public/private derived-card links differ")
        elif private:
            errors.append(f"{sid}: absent from private ledger")

    for card in cards:
        cid = card["card_id"]
        refs = card.get("source_unit_ids", [])
        if not refs:
            errors.append(f"{cid}: has no source unit")
        for sid in refs:
            if sid not in source_by_id:
                errors.append(f"{cid}: unknown source unit {sid}")
            elif cid not in source_by_id[sid].get("derived_card_ids", []):
                errors.append(f"{cid}: missing reciprocal link from {sid}")
        for dependency in card["formalization"].get("dependencies_on_other_cards", []):
            if dependency not in card_by_id:
                errors.append(f"{cid}: unknown card dependency {dependency}")
        if not card["quality"].get("atomicity_verified"):
            findings["non_atomic_cards"].append(cid)
        if card["quality"].get("interpretation_confidence") == "low":
            findings["low_confidence_cards"].append(cid)
        if card["quality"].get("needs_domain_review"):
            findings["domain_review_cards"].append(cid)
        if card["quality"].get("ambiguities"):
            findings["ambiguous_cards"].append(cid)
        if (
            card.get("faithful_paraphrase") == card.get("atomic_statement")
            and len(card.get("source_unit_ids", [])) > 1
        ):
            findings["multi_source_atomicity_review"].append(cid)

    for source in sources:
        sid = source["source_unit_id"]
        for cid in source.get("derived_card_ids", []):
            if cid not in card_by_id:
                errors.append(f"{sid}: unknown derived card {cid}")
            elif sid not in card_by_id[cid].get("source_unit_ids", []):
                errors.append(f"{sid}: missing reciprocal source link from {cid}")
        if source.get("correction_status") == "needs_review":
            findings["source_units_needing_review"].append(sid)
        if any(
            "illegible" in json.dumps(item, ensure_ascii=False).lower()
            for item in source.get("transcription_uncertainties", [])
        ):
            findings["illegible_source_units"].append(sid)

    for table in tables:
        tid = table["table_id"]
        for sid in table.get("source_unit_ids", []):
            if sid not in source_by_id:
                errors.append(f"{tid}: unknown source unit {sid}")
        for key in ("referencing_card_ids", "derived_card_ids"):
            for cid in table.get(key, []):
                if cid not in card_by_id:
                    errors.append(f"{tid}: unknown card {cid}")
        if table.get("transcription_status") == "needs_review":
            findings["tables_needing_review"].append(tid)
        if private:
            aggregate = "\n".join(
                private_by_id[sid]["original_text_corrected"]
                for sid in table.get("source_unit_ids", [])
                if sid in private_by_id
            )
            if sha256_text(aggregate) != table["private_transcription_sha256"]:
                errors.append(f"{tid}: private table transcription hash mismatch")
        private_table = private_table_by_id.get(tid)
        if private_tables and private_table is None:
            errors.append(f"{tid}: absent from private table ledger")
        elif private_table is not None:
            private_row_sources = [
                row.get("source_unit_id") for row in private_table.get("rows", [])
            ]
            if private_row_sources != table.get("source_unit_ids", []):
                errors.append(
                    f"{tid}: private row blocks do not match public source links"
                )
        for location in table.get("raw_ocr_locations", []):
            if not (ROOT / location).exists():
                errors.append(f"{tid}: missing private OCR file {location}")
        corrected_location = table.get("corrected_transcription_location")
        if corrected_location and not (ROOT / corrected_location).exists():
            errors.append(
                f"{tid}: missing corrected private table file {corrected_location}"
            )

    forbidden_public_keys = {
        "original_text_ocr",
        "original_text_corrected",
        "raw_ocr",
        "corrected_transcription",
        "full_source_text",
    }
    for row in all_public:
        identity = (
            row.get("source_unit_id") or row.get("card_id") or row.get("table_id")
        )
        leaked_keys = sorted(forbidden_public_keys & set(row))
        if leaked_keys:
            errors.append(
                f"{identity}: forbidden full-text keys in public record: {leaked_keys}"
            )

    # Public paraphrases may retain indispensable terms, but not a long,
    # verbatim run from the private transcription.
    if private:
        for card in cards:
            public_strings = [
                card.get("faithful_paraphrase", ""),
                card.get("atomic_statement", ""),
                *card.get("semantics", {}).get("conditions", []),
                *card.get("semantics", {}).get("conclusion_or_action", []),
                *card.get("semantics", {}).get("exceptions", []),
            ]
            for sid in card.get("source_unit_ids", []):
                source_text = normalized(
                    private_by_id.get(sid, {}).get("original_text_corrected", "")
                )
                if len(source_text) < args.verbatim_threshold:
                    continue
                source_windows = {
                    source_text[index : index + args.verbatim_threshold]
                    for index in range(
                        0, len(source_text) - args.verbatim_threshold + 1, 20
                    )
                }
                if any(
                    window in normalized(public)
                    for window in source_windows
                    for public in public_strings
                ):
                    errors.append(
                        f"{card['card_id']}: contains a verbatim source run of at least "
                        f"{args.verbatim_threshold} characters from {sid}"
                    )
                    break

    progress = {}
    if PROGRESS.exists():
        progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
        if set(progress.get("pages_rendered", [])) != EXPECTED_PDF_PAGES:
            errors.append("PROGRESS.json does not report all pages rendered")
        if set(progress.get("pages_ocr_complete", [])) != EXPECTED_PDF_PAGES:
            errors.append("PROGRESS.json does not report all pages OCR-complete")
        if set(progress.get("pages_visually_reviewed", [])) != EXPECTED_PDF_PAGES:
            errors.append("PROGRESS.json does not report all pages visually reviewed")

    statistics = {
        "source_units": len(sources),
        "cards": len(cards),
        "tables": len(tables),
        "pages": len(covered_pages & EXPECTED_PDF_PAGES),
        "source_unit_kinds": dict(Counter(row.get("unit_kind") for row in sources)),
        "correction_statuses": dict(
            Counter(row.get("correction_status") for row in sources)
        ),
        "card_kinds": dict(
            Counter(
                row.get("source_classification", {}).get("normalized_kind")
                for row in cards
            )
        ),
        "representability": dict(
            Counter(
                row.get("snarky_assessment", {}).get("representability")
                for row in cards
            )
        ),
    }
    report = {
        "status": "pass" if not errors else "fail",
        "schema_engine": schema_engine,
        "errors": errors,
        "warnings": warnings,
        "review_findings": dict(findings),
        "review_finding_counts": {key: len(value) for key, value in findings.items()},
        "statistics": statistics,
    }
    return report, 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="write a machine-readable validation report",
    )
    parser.add_argument(
        "--verbatim-threshold",
        type=int,
        default=120,
        help="minimum exact normalized character run treated as public-text leakage",
    )
    args = parser.parse_args()
    report, status = validate(args)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if PROGRESS.exists():
        progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
        progress["structural_validation"] = report["status"]
        progress["validation_errors"] = len(report["errors"])
        progress["validation_warnings"] = len(report["warnings"])
        progress["next_action"] = (
            "Review units marked needs_review against work/page_images; rerun extraction, validation, and index generation."
            if report["review_finding_counts"].get("source_units_needing_review")
            else "No structural or transcription review action remains."
        )
        PROGRESS.write_text(
            json.dumps(progress, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "status": report["status"],
                "errors": len(report["errors"]),
                "warnings": len(report["warnings"]),
                "review_finding_counts": report["review_finding_counts"],
                "statistics": report["statistics"],
                "report": str(args.report.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if report["errors"]:
        for error in report["errors"][:40]:
            print(f"ERROR: {error}", file=sys.stderr)
        if len(report["errors"]) > 40:
            print(f"ERROR: … {len(report['errors']) - 40} more", file=sys.stderr)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
