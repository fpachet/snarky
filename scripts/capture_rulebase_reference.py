"""Capture complete operational observations from a preserved reference checkout.

Run with PYTHONPATH=<reference>/src:<reference> from that reference directory.
Never regenerate the committed fixture just to make a changed engine pass.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from rulebases.runner import RULEBASE_ROOT, run_scenario
from snarky import Fact, NaiveInstantiationStrategy, RunResult, render_term


def observation(result: RunResult) -> dict[str, Any]:
    def fact(value: Fact) -> list[str]:
        return [render_term(value.entity), render_term(value.status)]

    return {
        "facts": [fact(value) for value in result.facts],
        "derived_facts": [fact(value) for value in result.derived_facts],
        "fired_activation_count": result.fired_activation_count,
        "events": [
            {
                "kind": event.kind.value,
                "fact": fact(event.fact),
                "rule": event.rule_name,
                "group": event.rule_group,
                "premises": [fact(value) for value in event.premises],
            }
            for event in result.events
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refusing to overwrite a frozen reference")
    catalogue = yaml.safe_load((RULEBASE_ROOT / "catalog.yaml").read_text())
    observations = {}
    for entry in catalogue["rulebases"]:
        name = entry["path"]
        run = run_scenario(name, strategy=NaiveInstantiationStrategy())
        if run.missing_expected_facts:
            raise AssertionError(f"reference failed oracle for {name}")
        observations[name] = observation(run.result)
    payload = {"reference_commit": args.commit, "observations": observations}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
