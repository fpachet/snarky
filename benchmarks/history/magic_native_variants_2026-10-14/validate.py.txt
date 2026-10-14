"""Read-only native-variant archive checks with independent square validation."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path
from statistics import median

KEYS = (
    "nodes",
    "failures",
    "revisions",
    "support_calls",
    "cache_hits",
    "reductions",
    "work_digest",
    "termination",
    "squares",
)


def rows(path):
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )


def square(values, n):
    assert len(values) == n * n and all(type(v) is int for v in values)
    assert sorted(values) == list(range(1, n * n + 1))
    target = n * (n * n + 1) // 2
    assert all(sum(values[r * n : (r + 1) * n]) == target for r in range(n))
    assert all(sum(values[r * n + c] for r in range(n)) == target for c in range(n))
    assert sum(values[i * n + i] for i in range(n)) == target
    assert sum(values[i * n + n - 1 - i] for i in range(n)) == target


def signature(row):
    return [row[k] for k in KEYS]


def stage(folder):
    frozen = json.loads((folder / "frozen.json").read_text())
    with tarfile.open(folder / "sources.tar.gz") as archive:
        for name, expected in frozen["source_hashes"].items():
            stream = archive.extractfile(name.lstrip("/"))
            assert (
                stream is not None
                and hashlib.sha256(stream.read()).hexdigest() == expected
            )
    for compiler in folder.glob("*_compile.json"):
        record = json.loads(compiler.read_text())
        c = folder / (compiler.name.removesuffix("_compile.json") + ".c")
        assert (
            hashlib.sha256(c.read_bytes()).hexdigest()
            == record["identity"]["source_sha256"]
        )
    timed = rows(folder / "runs.jsonl")
    assert json.loads((folder / "schedule.json").read_text()) == [
        [r["size"], r["repeat"], r["variant"]] for r in timed
    ]
    signatures, exact = {}, {}
    for row in timed:
        assert row["termination"] in ("solution_limit", "node_limit")
        key = row["size"], row["variant"]
        if key in signatures:
            assert signatures[key] == signature(row)
        signatures[key] = signature(row)
        if row["variant"].startswith("exact"):
            if row["size"] in exact:
                assert exact[row["size"]] == signature(row)
            exact[row["size"]] = signature(row)
    for summary in json.loads((folder / "summary.json").read_text()):
        group = [
            r
            for r in timed
            if (r["size"], r["variant"]) == (summary["size"], summary["variant"])
        ]
        assert len(group) == frozen["config"]["repeats"]
        assert sorted(r["repeat"] for r in group) == list(range(len(group)))
        for name in ("seconds", "search_seconds"):
            assert summary[name] == median(r[name] for r in group)
        assert (
            summary["nodes"] == group[0]["nodes"]
            and summary["failures"] == group[0]["failures"]
        )
        assert summary["termination"] == group[0]["termination"]
        assert summary["solved"] == bool(group[0]["squares"])
    replay = rows(folder / "replays20.jsonl")
    replay_signatures = {}
    if replay:
        assert json.loads((folder / "replay20_schedule.json").read_text()) == [
            [r["repeat"], r["variant"]] for r in replay
        ]
        for row in replay:
            assert row["termination"] == "solution_limit"
            key = (
                "exact"
                if row["variant"].startswith("exact")
                or row["variant"] == "python_batch"
                else row["variant"]
            )
            if key in replay_signatures:
                assert replay_signatures[key] == signature(row)
            replay_signatures[key] = signature(row)
    profiles = rows(folder / "profiles.jsonl")
    for row in profiles:
        assert signature(row) == signatures[row["size"], row["variant"]]
    extra = rows(folder / "profiles20.jsonl")
    for row in extra:
        if row["variant"] != "bounds_both":
            key = "exact" if row["variant"].startswith("exact") else row["variant"]
            assert signature(row) == replay_signatures[key]
    for row in profiles + extra:
        p = row["profile"]
        assert all(v >= 0 for v in p.values())
        assert p["sum"] + p["alldiff"] <= p["propagation"] + 1e-6
        assert p["propagation"] <= row["search_seconds"] + 1e-6
    attempts = rows(folder / "attempts.jsonl")
    for row in attempts:
        assert row["nodes_per_second"] == row["nodes"] / row["search_seconds"]
        if row["termination"] == "time_limit":
            assert row["search_seconds"] >= frozen["config"]["attempt_seconds"]
    all_rows = timed + replay + profiles + extra + attempts
    witnesses = 0
    for row in all_rows:
        assert row["termination"] in ("node_limit", "time_limit", "solution_limit")
        assert row["solution_count"] == len(row["squares"])
        for values in row["squares"]:
            square(values, row["size"])
            witnesses += 1
    return len(all_rows), witnesses, len(frozen["source_hashes"])


def validate(folder):
    stages = [
        p for p in folder.iterdir() if p.is_dir() and (p / "frozen.json").exists()
    ]
    if (folder / "frozen.json").exists():
        stages = [folder]
    totals = [0, 0, 0]
    for path in stages:
        for i, value in enumerate(stage(path)):
            totals[i] += value
    if (folder / "manifest.json").exists():
        manifest = json.loads((folder / "manifest.json").read_text())
        for name, expected in manifest.items():
            assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    if (folder / "magic20_solution.json").exists():
        winner = json.loads((folder / "magic20_solution.json").read_text())
        square(winner["values"], 20)
        replay = rows(folder / "confirmation" / "replays20.jsonl")
        assert any(
            r["variant"] == "budget_both"
            and r["squares"] == [winner["values"]]
            and r["nodes"] == winner["nodes"]
            for r in replay
        )
    assert stages
    print(
        f"Verified {len(stages)} stages, {totals[0]} passes, {totals[1]} independently "
        f"validated squares, {totals[2]} frozen sources and archive integrity"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, nargs="?", default=Path(__file__).parent)
    validate(parser.parse_args().folder)
