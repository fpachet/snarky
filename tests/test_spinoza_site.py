import json
import re
from html.parser import HTMLParser
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = PROJECT_ROOT / "site"


class _AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.raw_references: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        for name in ("href", "src"):
            value = attributes.get(name)
            if value and value.startswith("./"):
                self.raw_references.append(value)
                self.references.append(value.removeprefix("./").split("?", 1)[0])


def test_static_site_entrypoint_has_resolvable_relative_assets() -> None:
    parser = _AssetParser()
    html = (SITE_ROOT / "index.html").read_text(encoding="utf-8")
    parser.feed(html)

    assert {"styles.css", "app.js"} <= set(parser.references)
    assert all((SITE_ROOT / reference).is_file() for reference in parser.references)
    assert (SITE_ROOT / ".nojekyll").is_file()
    assert 'data-view="rules"' in html
    assert 'data-view="explanations"' in html
    assert 'data-view="graph"' in html
    assert 'href="#rules"' in html
    assert 'href="#graph"' in html
    versions = {
        reference.split("?v=", 1)[1]
        for reference in parser.raw_references
        if "?v=" in reference
    }
    assert len(versions) == 1
    assert re.fullmatch(r"[0-9a-f]{12}", versions.pop())
    app = (SITE_ROOT / "app.js").read_text(encoding="utf-8")
    assert 'cache: "no-store"' in app
    assert "modelRequest.abort()" in app


def test_static_model_contains_the_complete_executable_ethics_iii() -> None:
    payload = json.loads(
        (SITE_ROOT / "data" / "model.json").read_text(encoding="utf-8")
    )

    assert payload["meta"]["counts"] == {
        "propositions": 59,
        "definitions": 48,
        "general_definitions": 1,
        "proposition_cases": 199,
        "definition_cases": 101,
        "explanations": 27,
        "explanation_cases": 54,
        "catalogued_rules": 652,
        "predicates": 745,
        "rule_dependencies": 13107,
    }
    assert [item["id"] for item in payload["propositions"]] == [
        f"E3P{index:02d}" for index in range(1, 60)
    ]
    assert [item["id"] for item in payload["definitions"]] == [
        f"E3DA{index:02d}" for index in range(1, 49)
    ]
    assert payload["general_definition"]["id"] == "E3DA-GENERAL"
    assert len(payload["explanations"]) == 27
    assert all(item["result"] == "proved" for item in payload["explanations"])
    assert len(payload["rules"]) == 652
    assert len({rule["id"] for rule in payload["rules"]}) == 652
    assert all(
        rule["body"].startswith(f"RULE {rule['id']}\n") for rule in payload["rules"]
    )
    assert all(rule["file"].startswith("rules/") for rule in payload["rules"])
    assert all(rule["origin"] and rule["status"] for rule in payload["rules"])
    assert all(
        item["result"].startswith("proved")
        for item in [
            *payload["propositions"],
            *payload["definitions"],
            payload["general_definition"],
            *payload["explanations"],
        ]
    )


def test_rule_graph_predicate_index_matches_rule_inputs_and_outputs() -> None:
    payload = json.loads(
        (SITE_ROOT / "data" / "model.json").read_text(encoding="utf-8")
    )
    rules = {rule["id"]: rule for rule in payload["rules"]}
    predicates = {
        predicate["id"]: predicate for predicate in payload["rule_graph"]["predicates"]
    }

    for predicate_id, uses in predicates.items():
        assert all(
            predicate_id in rules[producer]["output_predicates"]
            for producer in uses["producers"]
        )
        assert all(
            predicate_id in rules[consumer]["input_predicates"]
            for consumer in uses["consumers"]
        )

    edges = {
        (producer, consumer)
        for uses in predicates.values()
        for producer in uses["producers"]
        for consumer in uses["consumers"]
        if producer != consumer
    }
    assert len(edges) == payload["rule_graph"]["producer_consumer_edge_count"]
    assert len(edges) == payload["meta"]["counts"]["rule_dependencies"]


def test_pages_workflow_builds_and_deploys_the_site_directory() -> None:
    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
    )

    assert workflow["jobs"]["build"]["steps"][2]["run"] == (
        'python -m pip install "PyYAML>=6.0"'
    )
    assert workflow["jobs"]["build"]["steps"][3]["run"] == (
        "python scripts/build_spinoza_site.py"
    )
    assert workflow["jobs"]["build"]["steps"][5]["with"]["path"] == "site"
    assert workflow["jobs"]["deploy"]["environment"]["name"] == "github-pages"
