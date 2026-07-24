"""Compare a cold MEA agenda build with one incremental agenda update."""

from __future__ import annotations

import argparse
import json
import statistics
import time

from snarky import (
    Atom,
    Fact,
    FactPremise,
    ForwardEngine,
    MEAConflictStrategy,
    Rule,
    RuleGroup,
    Triple,
    Variable,
    add,
)


def _group(rule_count: int) -> RuleGroup:
    item = Variable("item")
    rules = tuple(
        Rule(
            f"rule_{index}",
            (
                FactPremise(
                    Triple(
                        item,
                        Atom(f"relation_{index}"),
                        Atom("ready"),
                    )
                ),
            ),
            (
                add(
                    Triple(
                        item,
                        Atom("matched"),
                        Atom(f"rule_{index}"),
                    )
                ),
            ),
        )
        for index in range(rule_count)
    )
    return RuleGroup("agenda_benchmark", rules)


def _initial_facts(rule_count: int) -> tuple[Fact, ...]:
    return tuple(
        Fact(
            Triple(
                Atom(f"item_{index}"),
                Atom(f"relation_{index}"),
                Atom("ready"),
            )
        )
        for index in range(rule_count)
    )


def run(rule_count: int, repeat: int) -> dict[str, object]:
    group = _group(rule_count)
    initial = _initial_facts(rule_count)
    changed = Fact(
        Triple(
            Atom("new_item"),
            Atom("relation_0"),
            Atom("ready"),
        )
    )
    cold_times: list[float] = []
    incremental_times: list[float] = []
    recomputations: list[int] = []
    reuses: list[int] = []
    for _ in range(repeat):
        cold_session = ForwardEngine(
            (),
            conflict_strategy=MEAConflictStrategy(),
        ).create_session((*initial, changed))
        started = time.perf_counter()
        cold_session.inspect_agenda(group)
        cold_times.append(time.perf_counter() - started)

        warm_session = ForwardEngine(
            (),
            conflict_strategy=MEAConflictStrategy(),
        ).create_session(initial)
        warm_session.inspect_agenda(group)
        before_recomputations = (
            warm_session.agenda_metrics.rule_recomputations
        )
        before_reuses = warm_session.agenda_metrics.rule_reuses
        warm_session.assume(changed, label="benchmark-delta")
        started = time.perf_counter()
        warm_session.inspect_agenda(group)
        incremental_times.append(time.perf_counter() - started)
        recomputations.append(
            warm_session.agenda_metrics.rule_recomputations
            - before_recomputations
        )
        reuses.append(
            warm_session.agenda_metrics.rule_reuses - before_reuses
        )
    cold = statistics.median(cold_times)
    incremental = statistics.median(incremental_times)
    return {
        "rule_count": rule_count,
        "repeat": repeat,
        "cold_median_seconds": cold,
        "incremental_median_seconds": incremental,
        "speedup": cold / incremental,
        "rules_recomputed": statistics.median(recomputations),
        "rules_reused": statistics.median(reuses),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", type=int, default=200)
    parser.add_argument("--repeat", type=int, default=20)
    arguments = parser.parse_args()
    if arguments.rules < 1 or arguments.repeat < 1:
        parser.error("--rules and --repeat must be positive")
    print(
        json.dumps(
            run(arguments.rules, arguments.repeat),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
