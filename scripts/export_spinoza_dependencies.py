#!/usr/bin/env python3
"""Export conservative proposition dependencies from the imported corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_json", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()
    corpus: dict[str, Any] = json.loads(args.corpus_json.read_text(encoding="utf-8"))
    propositions = [unit for unit in corpus["units"] if unit["type"] == "proposition"]
    nodes = [
        {
            "id": unit["id"],
            "label": unit["source_text"],
            "formalization_status": (
                "historical_reproduced"
                if unit["id"] in {"E3P19", "E3P21", "E3P22", "E3P33"}
                else "source_imported"
            ),
        }
        for unit in propositions
    ]
    node_ids = {node["id"] for node in nodes}
    edges = sorted(
        {
            (reference, unit["id"])
            for unit in propositions
            for reference in unit.get("reference_candidates", [])
            if reference in node_ids and reference != unit["id"]
        }
    )
    payload = {
        "schema_version": 1,
        "semantics": (
            "source is a cited prerequisite; target is the citing proposition; "
            "references are conservative regex candidates"
        ),
        "nodes": nodes,
        "edges": [
            {"source": source, "target": target, "kind": "reference_candidate"}
            for source, target in edges
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
