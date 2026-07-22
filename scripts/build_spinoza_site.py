"""Build the static data bundle for the Ethics III web atlas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEMATIC_ROOT = PROJECT_ROOT / "spinoza" / "systematic"
SOURCE_ROOT = PROJECT_ROOT / "spinoza" / "sources"
RULE_PATTERN = re.compile(r"^RULE\s+(\S+)", re.MULTILINE)

AFFECT_NAMES = (
    "Désir",
    "Joie",
    "Tristesse",
    "Étonnement",
    "Mépris",
    "Amour",
    "Haine",
    "Inclination",
    "Aversion",
    "Ferveur",
    "Dérision",
    "Espoir",
    "Crainte",
    "Sécurité",
    "Désespoir",
    "Épanouissement",
    "Resserrement de conscience",
    "Commisération",
    "Faveur",
    "Indignation",
    "Surestime",
    "Mésestime",
    "Envie",
    "Miséricorde",
    "Contentement de soi",
    "Humilité",
    "Repentir",
    "Orgueil",
    "Mésestime de soi",
    "Gloire",
    "Honte",
    "Souhait frustré",
    "Émulation",
    "Reconnaissance ou Gratitude",
    "Bienveillance",
    "Colère",
    "Vengeance",
    "Cruauté ou Férocité",
    "Peur",
    "Audace",
    "Pusillanimité",
    "Consternation",
    "Humanité ou Modestie",
    "Ambition",
    "Gourmandise",
    "Ivrognerie",
    "Avarice",
    "Lubricité",
)

AFFECT_FAMILIES = (
    (1, 5, "Fondations"),
    (6, 11, "Causes et objets"),
    (12, 17, "Temps et incertitude"),
    (18, 24, "Vie sociale"),
    (25, 31, "Rapport à soi"),
    (32, 43, "Désirs composés"),
    (44, 48, "Désirs par objet"),
)


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path}: expected a mapping")
    return loaded


def _family(index: int) -> str:
    return next(label for start, end, label in AFFECT_FAMILIES if start <= index <= end)


def _rule_names(root: Path, relative_paths: list[str]) -> list[str]:
    return [
        name
        for relative_path in relative_paths
        for name in RULE_PATTERN.findall(
            (root / relative_path).read_text(encoding="utf-8")
        )
    ]


def _case_payload(
    unit_id: str,
    case: dict[str, Any],
    run_case: Any,
) -> dict[str, Any]:
    result = run_case(SYSTEMATIC_ROOT, unit_id, case["id"])
    if not result.proved:
        raise ValueError(f"unproved case: {unit_id}/{case['id']}")
    return {
        "id": case["id"],
        "goals": case.get("goals", []),
        "must_not_derive": case.get("must_not_derive", []),
        "proof_depths": list(result.proof_depths),
        "rule_names": list(result.rule_names),
        "rule_origins": list(result.rule_origins),
        "initial_fact_count": result.initial_fact_count,
        "derived_fact_count": result.derived_fact_count,
        "derivation_count": result.derivation_count,
    }


def build_payload(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    systematic_root = project_root / "spinoza" / "systematic"
    source_root = project_root / "spinoza" / "sources"
    sys.path.insert(0, str(project_root / "src"))
    from snarky.spinoza import run_case

    corpus = json.loads((source_root / "passages.json").read_text(encoding="utf-8"))
    source_units = {unit["id"]: unit for unit in corpus["units"]}
    dependencies = _load_yaml(systematic_root / "definitions" / "dependencies.yaml")[
        "definitions"
    ]
    graph = json.loads(
        (project_root / "spinoza" / "reports" / "dependency_graph.json").read_text(
            encoding="utf-8"
        )
    )
    catalog = _load_yaml(systematic_root / "rules" / "catalog.yaml")
    catalog_by_rule = {
        rule_id: {
            "origin": entry["origin"],
            "source": entry.get("source"),
            "sources": entry.get("sources", []),
            "status": entry.get("status"),
        }
        for entry in catalog["rules"]
        for rule_id in entry["ids"]
    }

    propositions: list[dict[str, Any]] = []
    for index in range(1, 60):
        unit_id = f"E3P{index:02d}"
        manifest = _load_yaml(systematic_root / "theorems" / f"{unit_id}.yaml")
        source = source_units[unit_id]
        rule_files = manifest.get("rule_files", [])
        rule_names = _rule_names(systematic_root, rule_files)
        current_rules = [name for name in rule_names if name.startswith(unit_id)]
        propositions.append(
            {
                "id": unit_id,
                "number": index,
                "title": f"Proposition {index}",
                "kind": "proposition",
                "source_text": source["source_text"],
                "sections": source.get("sections", []),
                "status": manifest.get("formalization_status", manifest.get("result")),
                "result": manifest.get("result"),
                "current_rules": current_rules,
                "support_rules": [
                    name for name in rule_names if name not in current_rules
                ],
                "rule_metadata": {
                    name: catalog_by_rule.get(name, {}) for name in current_rules
                },
                "cases": [
                    _case_payload(unit_id, case, run_case) for case in manifest["cases"]
                ],
                "limitations": manifest.get("limitations", []),
                "known_divergences": manifest.get("known_divergences", []),
            }
        )

    definitions: list[dict[str, Any]] = []
    for index, affect_name in enumerate(AFFECT_NAMES, start=1):
        unit_id = f"E3DA{index:02d}"
        manifest = _load_yaml(systematic_root / "definitions" / f"{unit_id}.yaml")
        source = source_units[unit_id]
        rule_names = _rule_names(systematic_root, manifest["rule_files"])
        definitions.append(
            {
                "id": unit_id,
                "number": index,
                "title": affect_name,
                "family": _family(index),
                "kind": "definition",
                "source_text": source["source_text"],
                "sections": source.get("sections", []),
                "status": manifest.get("formalization_status", manifest.get("result")),
                "result": manifest.get("result"),
                "current_rules": rule_names,
                "support_rules": [],
                "rule_metadata": {
                    name: catalog_by_rule.get(name, {}) for name in rule_names
                },
                "dependencies": dependencies[unit_id],
                "cases": [
                    _case_payload(unit_id, case, run_case) for case in manifest["cases"]
                ],
                "limitations": manifest.get("limitations", []),
            }
        )

    general_id = "E3DA-GENERAL"
    general_manifest = _load_yaml(
        systematic_root / "definitions" / f"{general_id}.yaml"
    )
    general_rules = _rule_names(systematic_root, general_manifest["rule_files"])
    general_definition = {
        "id": general_id,
        "number": 49,
        "title": "Définition générale des affects",
        "family": "Synthèse",
        "kind": "general_definition",
        "source_text": source_units[general_id]["source_text"],
        "sections": source_units[general_id].get("sections", []),
        "status": general_manifest.get(
            "formalization_status", general_manifest.get("result")
        ),
        "result": general_manifest.get("result"),
        "current_rules": general_rules,
        "support_rules": [],
        "rule_metadata": {
            name: catalog_by_rule.get(name, {}) for name in general_rules
        },
        "dependencies": dependencies[general_id],
        "cases": [
            _case_payload(general_id, case, run_case)
            for case in general_manifest["cases"]
        ],
        "limitations": general_manifest.get("limitations", []),
    }

    definition_cases = sum(len(item["cases"]) for item in definitions) + len(
        general_definition["cases"]
    )
    proposition_cases = sum(len(item["cases"]) for item in propositions)
    explanation_count = sum(
        len(item["sections"]) for item in [*definitions, general_definition]
    )

    return {
        "meta": {
            "title": "L’Éthique III — atlas exécutable",
            "translation": "Charles Appuhn, 1913",
            "repository": "https://github.com/fpachet/snarky",
            "counts": {
                "propositions": len(propositions),
                "definitions": len(definitions),
                "general_definitions": 1,
                "proposition_cases": proposition_cases,
                "definition_cases": definition_cases,
                "definition_explanations": explanation_count,
                "catalogued_rules": len(catalog_by_rule),
            },
        },
        "propositions": propositions,
        "definitions": definitions,
        "general_definition": general_definition,
        "families": [
            {"start": start, "end": end, "label": label}
            for start, end, label in AFFECT_FAMILIES
        ],
        "proposition_graph": graph,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "site" / "data" / "model.json",
    )
    args = parser.parse_args()
    payload = build_payload()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Built {args.output}: "
        f"{len(payload['propositions'])} propositions, "
        f"{len(payload['definitions'])} affect definitions"
    )


if __name__ == "__main__":
    main()
