"""Read-only pure-Python policy archive validation; requires no native compiler."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path
from statistics import median


def square(values, n):
    assert len(values) == n * n and sorted(values) == list(range(1, n * n + 1))
    assert all(type(v) is int for v in values)
    target = n * (n * n + 1) // 2
    assert all(sum(values[r * n : (r + 1) * n]) == target for r in range(n))
    assert all(sum(values[r * n + c] for r in range(n)) == target for c in range(n))
    assert sum(values[i * n + i] for i in range(n)) == target
    assert sum(values[i * n + n - 1 - i] for i in range(n)) == target


def signature(row):
    return [
        row[k] for k in ("nodes", "failures", "revisions", "termination", "squares")
    ]


def check_sources(folder):
    frozen = json.loads((folder / "frozen.json").read_text())
    with tarfile.open(folder / "sources.tar.gz") as archive:
        for name, expected in frozen["source_hashes"].items():
            stream = archive.extractfile(name.lstrip("/"))
            assert stream is not None
            assert hashlib.sha256(stream.read()).hexdigest() == expected
    return frozen


def stage(folder):
    frozen = check_sources(folder)
    if not (folder / "runs.jsonl").exists():
        # Existing profiler verifies full signatures and witnesses during its
        # run; its compact summary retains counters rather than witness arrays.
        summary = json.loads((folder / "summary.json").read_text())
        for row in summary:
            common = [
                {
                    k: row[mode][k]
                    for k in ("nodes", "failures", "revisions", "termination", "solved")
                }
                for mode in ("baseline", "wall_timers", "cprofile")
            ]
            assert common[0] == common[1] == common[2]
            assert common[0]["solved"]
        return len(summary) * 3, 0, len(frozen["source_hashes"])
    rows = [
        json.loads(line) for line in (folder / "runs.jsonl").read_text().splitlines()
    ]
    assert json.loads((folder / "schedule.json").read_text()) == [
        [r["size"], r["repeat"], r["variant"]] for r in rows
    ]
    signatures, witnesses = {}, 0
    for row in rows:
        assert row["termination"] in ("solution_limit", "node_limit", "time_limit")
        if row["termination"] != "time_limit":
            key = row["size"], row["variant"]
            value = signature(row) + [
                row.get("reductions_sha256"),
                row.get("reduction_events"),
            ]
            if key in signatures:
                assert signatures[key] == value
            signatures[key] = value
        for values in row["squares"]:
            square(values, row["size"])
            witnesses += 1
    for summary in json.loads((folder / "summary.json").read_text()):
        group = [
            r
            for r in rows
            if (r["size"], r["variant"]) == (summary["size"], summary["variant"])
        ]
        for name in ("seconds", "search_seconds"):
            assert summary[name] == median(r[name] for r in group)
        assert (
            summary["nodes"] == group[0]["nodes"]
            and summary["termination"] == group[0]["termination"]
        )
        assert summary["solved"] == all(bool(r["squares"]) for r in group)
        exact = next(
            (
                r
                for r in rows
                if r["size"] == summary["size"] and r["variant"] == "exact"
            ),
            None,
        )
        assert summary["same_exact_search"] == (
            exact is not None and all(signature(r) == signature(exact) for r in group)
        )
        repeats = (
            frozen["config"]["repeats"] if frozen["config"]["phase"] == "timing" else 1
        )
        assert len(group) == repeats and sorted(r["repeat"] for r in group) == list(
            range(repeats)
        )
    if frozen["config"]["phase"] == "audit":
        for n in frozen["config"]["sizes"]:
            pair = [r for r in rows if r["size"] == n]
            assert len(pair) == 2 and signature(pair[0]) == signature(pair[1])
            assert pair[0]["reductions_sha256"] == pair[1]["reductions_sha256"]
            assert pair[0]["reduction_events"] == pair[1]["reduction_events"]
    return len(rows), witnesses, len(frozen["source_hashes"])


def validate(folder):
    stages = (
        [folder]
        if (folder / "frozen.json").exists()
        else [
            p for p in folder.iterdir() if p.is_dir() and (p / "frozen.json").exists()
        ]
    )
    totals = [0, 0, 0]
    for path in stages:
        for i, value in enumerate(stage(path)):
            totals[i] += value
    if (folder / "manifest.json").exists():
        for name, expected in json.loads(
            (folder / "manifest.json").read_text()
        ).items():
            assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    assert stages
    print(
        f"Verified {len(stages)} stages, {totals[0]} passes, {totals[1]} independently "
        f"validated squares, {totals[2]} frozen sources and archive integrity"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, nargs="?", default=Path(__file__).parent)
    validate(parser.parse_args().folder)
