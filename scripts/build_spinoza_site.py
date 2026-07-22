"""Build the static data bundle for the Ethics III web atlas."""

from __future__ import annotations

import argparse
import hashlib
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
RULE_BLOCK_PATTERN = re.compile(
    r"^RULE\s+(?P<name>\S+)\s*\n.*?^END\s*$",
    re.MULTILINE | re.DOTALL,
)
ASSET_VERSION_PATTERN = re.compile(r'(?P<prefix>\./(?:styles\.css|app\.js)\?v=)[^"\']+')

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


def _rule_definitions(root: Path) -> dict[str, dict[str, str]]:
    definitions: dict[str, dict[str, str]] = {}
    for path in sorted((root / "rules").rglob("*.rules")):
        content = path.read_text(encoding="utf-8")
        for match in RULE_BLOCK_PATTERN.finditer(content):
            name = match.group("name")
            if name in definitions:
                raise ValueError(f"duplicate rule definition: {name}")
            definitions[name] = {
                "body": match.group(0).strip(),
                "file": path.relative_to(root).as_posix(),
            }
    return definitions


def _predicate_graph(
    rule_payloads: list[dict[str, Any]],
    parse_rules: Any,
    fact_premise_type: type[Any],
    add_fact_type: type[Any],
    atom_type: type[Any],
    triple_type: type[Any],
) -> dict[str, Any]:
    predicate_index: dict[str, dict[str, set[str]]] = {}

    def predicate_name(term: Any) -> str | None:
        if isinstance(term, triple_type) and isinstance(term.relation, atom_type):
            return str(term.relation.name)
        return None

    for payload in rule_payloads:
        parsed = parse_rules(payload["body"])[0]
        inputs = sorted(
            {
                predicate
                for premise in parsed.premises
                if isinstance(premise, fact_premise_type)
                if (predicate := predicate_name(premise.entity)) is not None
            }
        )
        outputs = sorted(
            {
                predicate
                for action in parsed.actions
                if isinstance(action, add_fact_type)
                if (predicate := predicate_name(action.entity)) is not None
            }
        )
        payload["input_predicates"] = inputs
        payload["output_predicates"] = outputs
        for predicate in inputs:
            predicate_index.setdefault(
                predicate, {"producers": set(), "consumers": set()}
            )["consumers"].add(payload["id"])
        for predicate in outputs:
            predicate_index.setdefault(
                predicate, {"producers": set(), "consumers": set()}
            )["producers"].add(payload["id"])

    edges: dict[tuple[str, str], set[str]] = {}
    for predicate, uses in predicate_index.items():
        for producer in uses["producers"]:
            for consumer in uses["consumers"]:
                if producer != consumer:
                    edges.setdefault((producer, consumer), set()).add(predicate)

    return {
        "predicates": [
            {
                "id": predicate,
                "producers": sorted(uses["producers"]),
                "consumers": sorted(uses["consumers"]),
            }
            for predicate, uses in sorted(predicate_index.items())
        ],
        "producer_consumer_edge_count": len(edges),
    }


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


def _stamp_site_assets(project_root: Path, model_path: Path) -> str:
    site_root = project_root / "site"
    digest = hashlib.sha256()
    for path in (site_root / "app.js", site_root / "styles.css", model_path):
        digest.update(path.read_bytes())
    version = digest.hexdigest()[:12]

    index_path = site_root / "index.html"
    index = index_path.read_text(encoding="utf-8")
    stamped, replacements = ASSET_VERSION_PATTERN.subn(
        lambda match: f"{match.group('prefix')}{version}",
        index,
    )
    if replacements != 2:
        raise ValueError("site asset version markers are missing from index.html")
    if stamped != index:
        index_path.write_text(stamped, encoding="utf-8")
    return version


def build_payload(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    systematic_root = project_root / "spinoza" / "systematic"
    source_root = project_root / "spinoza" / "sources"
    sys.path.insert(0, str(project_root / "src"))
    from snarky.actions import AddFact
    from snarky.parser import parse_rules
    from snarky.premises import FactPremise
    from snarky.spinoza import run_case
    from snarky.terms import Atom, Triple

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
            "note": entry.get("note"),
        }
        for entry in catalog["rules"]
        for rule_id in entry["ids"]
    }
    rule_definitions = _rule_definitions(systematic_root)
    if catalog_by_rule.keys() != rule_definitions.keys():
        missing = sorted(catalog_by_rule.keys() - rule_definitions.keys())
        extra = sorted(rule_definitions.keys() - catalog_by_rule.keys())
        raise ValueError(f"rule catalog mismatch: missing={missing}, extra={extra}")

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

    explanation_sources = {
        unit["id"]: next(
            section
            for section in unit.get("sections", [])
            if "explication"
            in (section.get("label") or section.get("type") or "").lower()
        )
        for unit in corpus["units"]
        if any(
            "explication" in (section.get("label") or section.get("type") or "").lower()
            for section in unit.get("sections", [])
        )
    }
    definition_titles = {
        item["id"]: item["title"] for item in [*definitions, general_definition]
    }
    explanations: list[dict[str, Any]] = []
    for source_id, source in explanation_sources.items():
        explanation_id = f"{source_id}-EXP"
        manifest = _load_yaml(
            systematic_root / "explanations" / f"{explanation_id}.yaml"
        )
        rule_names = _rule_names(systematic_root, manifest["rule_files"])
        explanations.append(
            {
                "id": explanation_id,
                "parent_id": source_id,
                "title": f"Explication — {definition_titles[source_id]}",
                "kind": "explanation",
                "source_text": source["text"],
                "status": manifest.get("formalization_status", manifest.get("result")),
                "result": manifest.get("result"),
                "current_rules": rule_names,
                "support_rules": [],
                "rule_metadata": {
                    name: catalog_by_rule.get(name, {}) for name in rule_names
                },
                "cases": [
                    _case_payload(explanation_id, case, run_case)
                    for case in manifest["cases"]
                ],
                "limitations": manifest.get("limitations", []),
            }
        )

    definition_cases = sum(len(item["cases"]) for item in definitions) + len(
        general_definition["cases"]
    )
    proposition_cases = sum(len(item["cases"]) for item in propositions)
    explanation_cases = sum(len(item["cases"]) for item in explanations)
    all_units = [*propositions, *definitions, general_definition, *explanations]
    rules = []
    for rule_id, metadata in catalog_by_rule.items():
        declared_by = [
            unit["id"] for unit in all_units if rule_id in unit["current_rules"]
        ]
        case_uses = [
            {"unit_id": unit["id"], "case_id": case["id"]}
            for unit in all_units
            for case in unit["cases"]
            if rule_id in case["rule_names"]
        ]
        sources = metadata["sources"] or (
            [metadata["source"]] if metadata["source"] else []
        )
        rules.append(
            {
                "id": rule_id,
                "kind": "rule",
                "origin": metadata["origin"],
                "status": metadata["status"],
                "sources": sources,
                "note": metadata["note"],
                "body": rule_definitions[rule_id]["body"],
                "file": rule_definitions[rule_id]["file"],
                "declared_by": declared_by,
                "case_uses": case_uses,
            }
        )
    rule_graph = _predicate_graph(
        rules,
        parse_rules,
        FactPremise,
        AddFact,
        Atom,
        Triple,
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
                "explanations": len(explanations),
                "explanation_cases": explanation_cases,
                "catalogued_rules": len(catalog_by_rule),
                "predicates": len(rule_graph["predicates"]),
                "rule_dependencies": rule_graph["producer_consumer_edge_count"],
            },
        },
        "propositions": propositions,
        "definitions": definitions,
        "general_definition": general_definition,
        "explanations": explanations,
        "rules": rules,
        "rule_graph": rule_graph,
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
    asset_version = _stamp_site_assets(PROJECT_ROOT, args.output)
    print(
        f"Built {args.output}: "
        f"{len(payload['propositions'])} propositions, "
        f"{len(payload['definitions'])} affect definitions, "
        f"assets {asset_version}"
    )


if __name__ == "__main__":
    main()
