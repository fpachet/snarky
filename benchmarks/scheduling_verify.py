"""Replay every saved scheduling witness against the pinned original inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.scheduling_instances import (
    Project,
    validate_jobshop,
    validate_project,
)
from benchmarks.scheduling_standard import CACHE, load_instance, reference


def verify(archive, cache):
    count = 0
    for run in archive["runs"]:
        instance = load_instance(cache, run["instance"], archive["manifest"])
        validator = (
            validate_project if isinstance(instance, Project) else validate_jobshop
        )
        for witness in run.get("witnesses", []):
            validator(instance, witness["starts"], witness["objective"])
            count += 1
        heuristic = run.get("heuristic")
        if heuristic is not None:
            validator(instance, heuristic["starts"], heuristic["objective"])
            count += 1
            previous = None
            for witness in heuristic["history"]:
                validator(instance, witness["starts"], witness["objective"])
                if previous is not None and witness["objective"] >= previous:
                    raise ValueError("constructive history does not improve")
                previous = witness["objective"]
                count += 1
            if previous != heuristic["objective"]:
                raise ValueError("missing or mismatched constructive witness")
        objective = run.get("objective")
        if objective is not None:
            if (
                not run.get("witnesses")
                or objective != run["witnesses"][-1]["objective"]
            ):
                raise ValueError("missing or mismatched final witness")
            bound = run.get("bound")
            if bound is not None and bound > objective:
                raise ValueError("bound exceeds incumbent")
        value, status = reference(cache, run["instance"], archive["manifest"])
        if value != run["reference_objective"] or status != run["reference_status"]:
            raise ValueError("reference metadata changed")
        if run["status"] == "optimal" and objective != value:
            raise ValueError("claimed optimum contradicts reference")
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--cache", type=Path, default=CACHE)
    args = parser.parse_args()
    archive = json.loads(args.archive.read_text())
    count = verify(archive, args.cache)
    print(f"Validated {count} witnesses across {len(archive['runs'])} runs")


if __name__ == "__main__":
    main()
