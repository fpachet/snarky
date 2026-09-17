"""Separate instrumented cut counters; run from the repository with PYTHONPATH=src:."""

import json
from pathlib import Path

from benchmarks.prune_bridge import Bridge, validate_assignment
from snarky.finite import Query, QueryKind
from snarky.finite.propagation import NativeState
from snarky.finite.search import search

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent


class AuditState(NativeState):
    def __init__(self, model):
        super().__init__(model)
        self.cut = dict(revisions=0, failures=0, removed=0)
        self.ordinary_failures = 0

    def _revise(self, index, constraint, scoped):
        volume = sum(map(len, scoped.values()))
        valid = super()._revise(index, constraint, scoped)
        if index == len(self.model.constraints):
            self.cut["revisions"] += 1
            self.cut["failures"] += not valid
            self.cut["removed"] += volume - sum(map(len, scoped.values()))
        else:
            self.ordinary_failures += not valid
        return valid


def main():
    rows = []
    for case in (
        "golomb_opt_6",
        "golomb_opt_7",
        "jobshop_ft06_opt",
        "knapsack_20_opt",
        "bin_packing_20_opt",
    ):
        artifact = (
            ROOT
            / "benchmarks/results/prune_alldiff_2026-09-16/artifacts"
            / f"optimization--{case}.fzn.json"
        )
        document = json.loads(artifact.read_text())
        bridge = Bridge(document)
        for enabled in (False, True):
            state = AuditState(bridge.model)
            kind = (
                QueryKind.MAXIMIZE
                if document["solve"]["method"] == "maximize"
                else QueryKind.MINIMIZE
            )
            result = search(
                state, Query(kind, time_limit_seconds=5), objective_propagation=enabled
            )
            for solution in result.solutions:
                validate_assignment(document, bridge.raw_assignment(solution))
            if case in ("golomb_opt_6", "golomb_opt_7", "jobshop_ft06_opt"):
                assert result.status.value == "optimal"
                assert (
                    result.incumbent.objective_value
                    == dict(golomb_opt_6=17, golomb_opt_7=25, jobshop_ft06_opt=55)[case]
                )
            assert not state.domains.removals
            rows.append(
                dict(
                    case=case,
                    objective_propagation=enabled,
                    cut=state.cut,
                    ordinary_failures=state.ordinary_failures,
                    nodes=result.explored_nodes,
                    failures=result.failed_branches,
                    pruned=result.pruned_branches,
                    revisions=result.constraint_revisions,
                    status=result.status.value,
                    complete=result.complete,
                    termination=result.termination.value,
                    objective=result.incumbent.objective_value
                    if result.incumbent
                    else None,
                    bound=result.objective_bound,
                    incumbents=result.incumbent_values,
                    incumbent_history=[
                        dict(
                            value=x.value,
                            nodes=x.explored_nodes,
                            seconds=x.elapsed_seconds,
                        )
                        for x in result.incumbent_history
                    ],
                )
            )
    (OUT / "cut_effects.json").write_text(
        json.dumps(
            dict(
                protocol=(
                    "separate instrumented counters, "
                    "five-second cooperative search cap; "
                    "no latency or matched-work claims"
                ),
                cases=rows,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
