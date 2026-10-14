"""Read-only verification of archived fresh solver profiles and wall attribution."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tarfile
from collections import defaultdict
from pathlib import Path
from statistics import median


def signature(row):
    return (
        row["nodes"],
        row["failures"],
        row["revisions"],
        row["termination"],
        row["squares"],
        {k: v for k, v in row["stats"].items() if k != "enum_seconds"},
    )


def square(n, values):
    assert sorted(values) == list(range(1, n * n + 1))
    target = n * (n * n + 1) // 2
    lines = [values[i * n : (i + 1) * n] for i in range(n)]
    lines += [values[i::n] for i in range(n)]
    lines += [values[:: n + 1], values[n - 1 : n * n - 1 : n - 1]]
    assert all(len(line) == n and sum(line) == target for line in lines)


def validate(root):
    manifest = json.loads((root / "manifest.json").read_text())
    assert set(manifest) == {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    }
    for name, digest in manifest.items():
        path = root / name
        assert path.resolve().is_relative_to(root.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    records = sources = witnesses = 0
    for stage in ("smoke", "profile"):
        folder = root / stage
        frozen = json.loads((folder / "frozen.json").read_text())
        with tarfile.open(folder / "sources.tar.gz") as archive:
            for name, digest in frozen["source_hashes"].items():
                stream = archive.extractfile(name.lstrip("/"))
                assert stream is not None
                assert hashlib.sha256(stream.read()).hexdigest() == digest
                sources += 1
        rows = [
            json.loads(line)
            for line in (folder / "runs.jsonl").read_text().splitlines()
        ]
        schedule = json.loads((folder / "schedule.json").read_text())
        assert schedule == [
            [r["size"], r["variant"], r["phase"], r["repeat"]] for r in rows
        ]
        groups = defaultdict(list)
        for row in rows:
            records += 1
            n = row["size"]
            assert row["termination"] == ("solution_limit" if n <= 16 else "node_limit")
            assert bool(row["squares"]) == (n <= 16)
            if n > 16:
                assert row["nodes"] == 30 and not row["stats"]
            for values in row["squares"]:
                square(n, values)
                witnesses += 1
            groups[n, row["variant"]].append(row)
            if row["variant"] == "hybrid" and row["stats"]:
                stats = row["stats"]
                assert stats["attempts"] == sum(
                    stats.get(k, 0) for k in ("exhausted", "fallbacks", "witnesses")
                )
                assert stats["visits"] <= stats["attempts"] * 200000
            if row["phase"] == "wall_timers":
                times, categories = row["times"], row["attribution"]
                assert all(v["seconds"] >= -1e-8 for v in categories.values())
                assert math.isclose(
                    sum(v["seconds"] for v in categories.values()),
                    row["search_seconds"],
                    abs_tol=1e-8,
                )
                assert math.isclose(
                    sum(v["percent"] for v in categories.values()), 100, abs_tol=1e-8
                )
                for value in categories.values():
                    assert math.isclose(
                        value["percent"],
                        100 * value["seconds"] / row["search_seconds"],
                        abs_tol=1e-8,
                    )
                numeric = sum(
                    v
                    for k, v in times.items()
                    if k.startswith(("SumConstraint:", "LinearSumConstraint:"))
                )
                assert numeric == categories["sum_filtering"]["seconds"]
                assert (
                    times["AllDifferentConstraint:mask"]
                    == categories["alldiff_filtering"]["seconds"]
                )
                assert row["calls"]["propagation"] > 0
        summary = json.loads((folder / "summary.json").read_text())
        assert len(summary) == len(groups)
        for item in summary:
            key = item["size"], item["variant"]
            group = groups[key]
            assert len(group) == frozen["config"]["repeats"] + 2
            assert all(signature(r) == signature(group[0]) for r in group)
            baseline = [r for r in group if r["phase"] == "baseline"]
            wall = next(r for r in group if r["phase"] == "wall_timers")
            assert item["median_search_seconds"] == median(
                r["search_seconds"] for r in baseline
            )
            assert item["median_setup_seconds"] == median(
                r["setup_seconds"] for r in baseline
            )
            assert item["attribution"] == wall["attribution"]
            assert item["wall_seconds"] == wall["search_seconds"]
            assert (folder / f"magic{key[0]}_{key[1]}.prof").is_file()
            assert (folder / f"magic{key[0]}_{key[1]}.txt").is_file()
    print(
        json.dumps(
            dict(
                runs=records,
                validated_squares=witnesses,
                source_checks=sources,
                manifest_files=len(manifest),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    validate(
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    )
