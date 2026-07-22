import json
from html.parser import HTMLParser
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = PROJECT_ROOT / "site"


class _AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        for name in ("href", "src"):
            value = attributes.get(name)
            if value and value.startswith("./"):
                self.references.append(value.removeprefix("./"))


def test_static_site_entrypoint_has_resolvable_relative_assets() -> None:
    parser = _AssetParser()
    html = (SITE_ROOT / "index.html").read_text(encoding="utf-8")
    parser.feed(html)

    assert {"styles.css", "app.js"} <= set(parser.references)
    assert all((SITE_ROOT / reference).is_file() for reference in parser.references)
    assert (SITE_ROOT / ".nojekyll").is_file()
    assert 'data-view="rules"' in html
    assert 'href="#rules"' in html


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
        "definition_explanations": 27,
        "catalogued_rules": 608,
    }
    assert [item["id"] for item in payload["propositions"]] == [
        f"E3P{index:02d}" for index in range(1, 60)
    ]
    assert [item["id"] for item in payload["definitions"]] == [
        f"E3DA{index:02d}" for index in range(1, 49)
    ]
    assert payload["general_definition"]["id"] == "E3DA-GENERAL"
    assert len(payload["rules"]) == 608
    assert len({rule["id"] for rule in payload["rules"]}) == 608
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
        ]
    )


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
