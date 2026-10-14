"""Read-only integrity, matched-work and independent square archive checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path
from statistics import median


def check_square(square, n):
    assert len(square) == n * n and all(type(v) is int for v in square)
    assert sorted(square) == list(range(1, n * n + 1))
    square = [square[r * n : (r + 1) * n] for r in range(n)]
    target = n * (n * n + 1) // 2
    assert all(sum(row) == target for row in square)
    assert all(sum(square[r][c] for r in range(n)) == target for c in range(n))
    assert sum(square[r][r] for r in range(n)) == target
    assert sum(square[r][n - r - 1] for r in range(n)) == target


def validate(folder):
    frozen = json.loads((folder / "frozen.json").read_text())
    with tarfile.open(folder / "sources.tar.gz") as archive:
        for name, expected in frozen["source_hashes"].items():
            stream = archive.extractfile(name.lstrip("/"))
            assert stream is not None
            assert hashlib.sha256(stream.read()).hexdigest() == expected
    compiler = json.loads((folder / "compile.json").read_text())
    assert (
        hashlib.sha256((folder / "search.c").read_bytes()).hexdigest()
        == (compiler["identity"]["source_sha256"])
    )
    rows = [
        json.loads(line) for line in (folder / "runs.jsonl").read_text().splitlines()
    ]
    summaries = json.loads((folder / "summary.json").read_text())
    schedule = json.loads((folder / "schedule.json").read_text())
    assert schedule == [[r["size"], r["repeat"], r["variant"]] for r in rows]
    signatures, squares = {}, 0
    keys = (
        "nodes",
        "failures",
        "revisions",
        "support_calls",
        "cache_hits",
        "reductions",
        "work_digest",
        "termination",
        "squares",
        "settings",
    )
    for row in rows:
        signature = [row[k] for k in keys]
        assert row["termination"] in ("solution_limit", "node_limit", "exhausted")
        assert row["solution_count"] == len(row["squares"])
        if row["size"] in signatures:
            assert signatures[row["size"]] == signature
        signatures[row["size"]] = signature
        for square in row["squares"]:
            check_square(square, row["size"])
            squares += 1
    for summary in summaries:
        group = [r for r in rows if r["size"] == summary["size"]]
        for variant in ("python", "native"):
            selected = [r for r in group if r["variant"] == variant]
            assert len(selected) == frozen["config"]["repeats"]
            assert sorted(r["repeat"] for r in selected) == list(range(len(selected)))
            assert summary[variant] == median(r["seconds"] for r in selected)
        assert summary["speedup"] == summary["python"] / summary["native"]
        assert summary["reduction_percent"] == 100 * (
            1 - summary["native"] / summary["python"]
        )
        assert summary["nodes"] == group[0]["nodes"]
        assert summary["solved"] == bool(group[0]["squares"])
    attempt = folder / "attempt20.json"
    if attempt.exists():
        row = json.loads(attempt.read_text())
        assert row["size"] == 20 and row["variant"] == "native"
        assert row["nodes_per_second"] == row["nodes"] / row["search_seconds"]
        assert row["termination"] in ("time_limit", "solution_limit", "exhausted")
        if row["termination"] == "time_limit":
            assert row["search_seconds"] >= frozen["config"]["attempt_seconds"]
        assert row["solution_count"] == len(row["squares"])
        for square in row["squares"]:
            check_square(square, 20)
            squares += 1
    manifest = folder / "manifest.json"
    if manifest.exists():
        for name, expected in json.loads(manifest.read_text()).items():
            assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    print(
        f"Verified {len(rows)} matched runs, {squares} squares, "
        f"{len(frozen['source_hashes'])} frozen sources and archive integrity"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, nargs="?", default=Path(__file__).parent)
    validate(parser.parse_args().folder)
