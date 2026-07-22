#!/usr/bin/env python3
"""Generate one auditable theorem manifest for each Ethics III proposition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

HISTORICAL_CASES: dict[str, dict[str, Any]] = {
    "E3P19": {
        "formalization_status": "historical_reproduced",
        "cases": [
            {
                "id": "destruction",
                "initial_facts": [
                    "(x0 aime y0)",
                    "(x0 imagine (y0 est inexistant))",
                ],
                "goals": ["(x0 est triste)"],
                "expected": {"status": "proved", "minimum_depth": 2},
            },
            {
                "id": "conservation",
                "initial_facts": [
                    "(x0 aime y0)",
                    "(x0 imagine (y0 est existant))",
                ],
                "goals": ["(x0 est joyeux)"],
                "expected": {"status": "proved", "minimum_depth": 2},
            },
        ],
    },
    "E3P21": {
        "formalization_status": "historical_reproduced",
        "cases": [
            {
                "id": "joie",
                "initial_facts": [
                    "(x0 aime y0)",
                    "(x0 imagine (y0 est joyeux))",
                ],
                "goals": ["(x0 est joyeux)"],
                "expected": {"status": "proved", "minimum_depth": 2},
            },
            {
                "id": "tristesse",
                "initial_facts": [
                    "(x0 aime y0)",
                    "(x0 imagine (y0 est triste))",
                ],
                "goals": ["(x0 est triste)"],
                "expected": {"status": "proved", "minimum_depth": 2},
            },
        ],
    },
    "E3P22": {
        "formalization_status": "historical_reproduced",
        "cases": [
            {
                "id": "amour",
                "initial_facts": [
                    "(x0 aime y0)",
                    "(x0 imagine (z0 affecte_de_joie y0))",
                ],
                "goals": ["(x0 aime z0)"],
                "expected": {"status": "proved", "minimum_depth": 3},
            },
            {
                "id": "haine",
                "initial_facts": [
                    "(x0 aime y0)",
                    "(x0 imagine (z0 affecte_de_tristesse y0))",
                ],
                "goals": ["(x0 hait z0)"],
                "expected": {"status": "proved", "minimum_depth": 3},
            },
        ],
    },
    "E3P33": {
        "formalization_status": "historical_reproduced_with_divergence",
        "cases": [
            {
                "id": "reciprocite",
                "initial_facts": [
                    "(x0 aime y0)",
                    "(x0 est_semblable_a y0)",
                ],
                "goals": ["(x0 s_efforce_que (y0 aime x0))"],
                "expected": {"status": "proved", "minimum_depth": 5},
            }
        ],
        "known_divergences": [
            "La chaîne historique n'utilise pas le fait de similitude.",
            "P13/2/2 est étendue du contexte imagine à s_efforce_que.",
        ],
    },
}


def build_manifest(unit: dict[str, Any]) -> dict[str, Any]:
    identifier = unit["id"]
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "id": identifier,
        "type": "theorem",
        "source_unit": identifier,
        "source_text": unit["source_text"],
        "reference_candidates": unit.get("reference_candidates", []),
        "formalization_status": "source_imported",
        "result": "not_proved",
        "missing": [
            "Formalisation des hypothèses et du but à valider.",
            "Règles antérieures nécessaires à rendre exécutables.",
        ],
        "forbidden_rules": [f"{identifier}_as_direct_rule"],
    }
    override = HISTORICAL_CASES.get(identifier)
    if override is not None:
        manifest.update(override)
        manifest["result"] = "proved"
        manifest.pop("missing", None)
        manifest["allowed_rule_origins"] = [
            "historical_model",
            "historical_interpretation",
        ]
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_json", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    corpus = json.loads(args.corpus_json.read_text(encoding="utf-8"))
    propositions = [unit for unit in corpus["units"] if unit["type"] == "proposition"]
    if len(propositions) != 59:
        raise ValueError(f"expected 59 propositions, found {len(propositions)}")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    for proposition in propositions:
        path = args.output_directory / f"{proposition['id']}.yaml"
        path.write_text(
            yaml.safe_dump(
                build_manifest(proposition),
                allow_unicode=True,
                sort_keys=False,
                width=100,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
