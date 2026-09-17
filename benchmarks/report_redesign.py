"""Render a paired comparison archive without discarding samples or limits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median


def ms(value):
    return f"{1000 * value:.2f}"


def report(path):
    payload = json.loads(path.read_text())
    out = [
        "# Redesign performance comparison",
        "",
        "This report uses `redesign_promotion_v1`. All raw samples, source archives,",
        "and per-run outcomes are retained beside the JSON record. It supplements",
        "the immutable initial baseline; timing scopes and search policies differ.",
        "",
        f"Raw record: `{path.name}`. Python: `{payload['python'].split()[0]}`;",
        f"platform: `{payload['platform']}`; hash seed: `{payload['hash_seed']}`.",
        f"Reference commit: `{payload['reference_commit']}`.",
        f"Candidate runtime/workload hash: `{payload['candidate_sources']['sha256']}`.",
        f"Collector hash: `{payload['collector_sha256']}`.",
        "",
        "Each of three paired sessions alternates implementation order and retains",
        "seven fresh-state samples after a discarded warmup. Tables pool the 21",
        "samples per side for readability; the final table retains per-session",
        "medians, preparation/search separation, and full observed timing ranges.",
        "No confidence interval or controlled thermal environment is claimed.",
        "",
        "Rule fixtures require matching full output fingerprints and work counters.",
        "Native/legacy CSP cases hold MRV, lexical value order and search tree fixed.",
        "The mixed case intentionally adds rule-derived reports to the native CSP.",
        "Markov cases compare solver policies/formulations, with independent sequence",
        "validation. They are not fixed-work kernel comparisons.",
        "",
        "## Rules, CSP and mixed execution",
        "",
        "Times are total preparation plus execution in milliseconds. A slowdown flag",
        "requires both >15% and >2 ms in at least two of the three paired sessions.",
        "The deliberate additional mixed inference is reported as overhead.",
        "",
        "| Case | Reference ms | Candidate ms | Speedup | Changes % | Review |",
        "|---|---:|---:|---:|---|---|",
    ]
    optimization, memory, sessions = [], [], []
    for name, data in payload["comparisons"].items():
        pairs = data["paired_sessions"]
        left = [r for p in pairs for r in p["reference"]["runs"]]
        right = [r for p in pairs for r in p["candidate"]["runs"]]
        a = median(r["total_seconds"] for r in left)
        b = median(r["total_seconds"] for r in right)
        changes, triggers = [], 0
        for i, pair in enumerate(pairs, 1):
            l_runs, r_runs = pair["reference"]["runs"], pair["candidate"]["runs"]
            la, rb = (
                median(x["total_seconds"] for x in l_runs),
                median(x["total_seconds"] for x in r_runs),
            )
            changes.append(f"{100 * (rb / la - 1):+.1f}")
            triggers += rb > la * 1.15 and rb - la > 0.002

            def cells(runs):
                return (
                    f"{ms(median(x['preparation_seconds'] for x in runs))} / "
                    f"{ms(median(x['search_seconds'] for x in runs))} / "
                    f"{ms(min(x['total_seconds'] for x in runs))}–"
                    f"{ms(max(x['total_seconds'] for x in runs))}"
                )

            sessions.append(f"| `{name}` / {i} | {cells(l_runs)} | {cells(r_runs)} |")
        if name.startswith(("markov", "scaling/")):

            def outcomes(runs):
                observations = [r["observation"] for r in runs]

                def extent(key):
                    values = [o[key] for o in observations if o.get(key) is not None]
                    return (
                        "none"
                        if not values
                        else str(min(values))
                        if min(values) == max(values)
                        else f"{min(values)}–{max(values)}"
                    )

                first = [
                    o["first_incumbent_seconds"]
                    for o in observations
                    if o.get("first_incumbent_seconds") is not None
                ]
                proof = sum(o["proved"] for o in observations)
                return (
                    f"{extent('objective')} / {extent('bound')}; {proof}/{len(runs)}; "
                    f"{extent('nodes')}; {ms(median(first)) if first else 'none'}"
                )

            same_proof = all(r["observation"]["proved"] for r in (*left, *right))
            ratio = f"{a / b:.2f}×" if same_proof else "not a proof comparison"
            optimization.append(
                f"| `{name}` | {data['reference_mode']} → {data['candidate_mode']} | "
                f"{ms(a)} → {ms(b)} | {outcomes(left)} | {outcomes(right)} | {ratio} |"
            )
        else:
            trigger = (
                "additional mixed work"
                if name == "mixed_magic3"
                else ("INVESTIGATE" if triggers >= 2 else "no")
            )
            out.append(
                f"| `{name}` | {ms(a)} | {ms(b)} | {a / b:.2f}× | "
                f"{', '.join(changes)} | {trigger} |"
            )
        lm = data["reference_memory"]["runs"][0]
        rm = data["candidate_memory"]["runs"][0]

        def peaks(run):
            return (
                f"{run['preparation_peak_traced_bytes'] / 1024:.1f} / "
                f"{run['search_peak_traced_bytes'] / 1024:.1f}"
            )

        flags = [
            rm[k] > lm[k] * 1.15 and rm[k] - lm[k] > 1024**2
            for k in ("preparation_peak_traced_bytes", "search_peak_traced_bytes")
        ]
        memory.append(
            f"| `{name}` | {peaks(lm)} | {peaks(rm)} | "
            f"{'check repeat' if any(flags) else 'no'} |"
        )
    out += [
        "",
        "## Optimization outcomes",
        "",
        "Each outcome cell is **incumbent / bound; completed proofs / 21; nodes;",
        "median first-incumbent ms**. Ranges retain variation under the 3-second",
        "budget. Ring cases have a 5,000-node limit; scaling cases have 1,000.",
        "Only paired completed proofs receive a proof-time ratio. Infeasible cases",
        "have no incumbent. A root relaxation bound can remain loose.",
        "",
        "Legacy feasibility has no cooperative deadline, so the POSIX benchmark",
        "controller interrupts it and preserves the last completed incumbent.",
        "For interrupted legacy calls, nodes/failures count completed feasibility",
        "runs only, explicitly marked `counters_complete=false` in the raw data.",
        "Its bound is the separately known analytic edge-cost bound, not a solver API.",
        "Native limits are cooperative and may overshoot at a safe boundary.",
        "",
        "| Case | Modes | Total ms | Reference | Candidate | Proof ratio |",
        "|---|---|---:|---|---|---|",
        *optimization,
        "",
        "## Isolated allocation measurements",
        "",
        "Values are **preparation / search peak KiB**, from separate subprocess",
        "`tracemalloc` runs, not RSS. Search peaks include live preparation objects.",
        "Immutable fixtures constructed before preparation are excluded. Classical",
        "compatibility cases expose a single public solve: preparation reads as",
        "approximately zero and execution includes their internal preparation.",
        "Instrumentation can hit a time limit earlier and do less search; these are",
        "peaks for the recorded instrumented outcome, not proof-memory comparisons.",
        "A single increase >15% and >1 MiB requests repetition; it cannot establish",
        "a reproduced regression by itself.",
        "",
        "| Case | Reference KiB | Candidate KiB | Memory trigger |",
        "|---|---:|---:|---|",
        *memory,
        "",
        "## Per-session timing detail",
        "",
        "Each cell is **prepare median / execute median / total min–max ms**.",
        "Complete raw samples and counters remain the authoritative evidence.",
        "",
        "| Case / session | Reference | Candidate |",
        "|---|---|---|",
        *sessions,
        "",
    ]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.output.open("x") as handle:
        handle.write(report(args.record))


if __name__ == "__main__":
    main()
