"""Read-only validation of ALLDIFF native-kernel audit and timing evidence."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tarfile
from collections import defaultdict
from pathlib import Path
from statistics import median


def signature(row, audit):
    result = (
        row["nodes"],
        row["failures"],
        row["revisions"],
        row["termination"],
        row["squares"],
        {k: v for k, v in row["residual_stats"].items() if k != "enum_seconds"},
    )
    return (
        result + (row["reductions_sha256"], row["reduction_events"])
        if audit
        else result
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
    for name, digest in manifest.items():
        path = root / name
        assert path.resolve().is_relative_to(root.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    report = json.loads((root / "report.json").read_text())
    runs = squares = sources = audited = 0
    for stage in report["stages"]:
        folder = root / stage
        frozen = json.loads((folder / "frozen.json").read_text())
        with tarfile.open(folder / "sources.tar.gz") as archive:
            for name, digest in frozen["source_hashes"].items():
                stream = archive.extractfile(name.lstrip("/"))
                assert stream is not None
                assert hashlib.sha256(stream.read()).hexdigest() == digest
                sources += 1
        compiled = json.loads((folder / "compile.json").read_text())
        c_hashes = [
            digest
            for path, digest in frozen["source_hashes"].items()
            if Path(path).name == "alldiff_support.c"
        ]
        assert c_hashes == [compiled["alldiff"]["identity"]["source_sha256"]]
        rows = [
            json.loads(line)
            for line in (folder / "runs.jsonl").read_text().splitlines()
        ]
        schedule = json.loads((folder / "schedule.json").read_text())
        assert schedule == [
            [r["size"], r["strategy"], r["variant"], r["repeat"]] for r in rows
        ]
        audit = frozen["config"]["phase"] == "audit"
        expected = 1 if audit else frozen["config"]["repeats"]
        groups = defaultdict(list)
        for row in rows:
            runs += 1
            groups[row["size"], row["strategy"]].append(row)
            assert row["termination"] in ("solution_limit", "node_limit")
            if row["size"] <= 16:
                assert (
                    row["termination"] == "solution_limit" and len(row["squares"]) == 1
                )
            if row["termination"] == "node_limit":
                assert row["nodes"] == frozen["config"]["large_nodes"]
            for values in row["squares"]:
                square(row["size"], values)
                squares += 1
            stats = row["alldiff_stats"]
            if row["variant"] == "native":
                assert stats["calls"] == sum(
                    stats.get(k, 0)
                    for k in ("native_calls", "cached_calls", "empty_calls")
                )
                if audit:
                    assert stats["audited_calls"] == stats["calls"]
                    audited += stats["audited_calls"]
                else:
                    assert not stats.get("audited_calls")
            else:
                assert not stats
            if row["residual_stats"]:
                stats = row["residual_stats"]
                assert stats["attempts"] == sum(
                    stats.get(k, 0) for k in ("exhausted", "fallbacks", "witnesses")
                )
                assert stats["visits"] <= stats["attempts"] * 200000
        summary = json.loads((folder / "summary.json").read_text())
        assert len(summary) == len(groups)
        for item in summary:
            group = groups[item["size"], item["strategy"]]
            assert len(group) == 2 * expected
            assert all(
                signature(row, audit) == signature(group[0], audit) for row in group
            )
            assert all(r["sum_stats"] == group[0]["sum_stats"] for r in group)
            for variant in ("python", "native"):
                actual = [r["seconds"] for r in group if r["variant"] == variant]
                assert len(actual) == expected
                assert item[variant] == median(actual)
            assert math.isclose(
                item["time_reduction_percent"],
                100 * (1 - item["native"] / item["python"]),
                abs_tol=1e-8,
            )
        if stage == "pilot":
            assert summary == report["broad"]
        if stage == "confirmation":
            assert summary == report["confirmation"]
        if stage == "large":
            assert summary == report["large_prefix"]
    assert runs == report["runs"]
    assert squares == report["validated_squares"]
    print(
        json.dumps(
            dict(
                runs=runs,
                validated_squares=squares,
                audited_alldiff_calls=audited,
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
