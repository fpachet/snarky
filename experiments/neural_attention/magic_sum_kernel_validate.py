"""Read-only validation of SUM native-kernel audit and timing evidence."""

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
            stats = row["sum_stats"]
            if row["variant"] == "native":
                assert stats["calls"] == stats.get("outside_original_bounds", 0) + sum(
                    v for k, v in stats.items() if k.startswith("path_")
                )
                if audit:
                    assert stats["audited_calls"] == stats["calls"]
                    audited += stats["audited_calls"]
                else:
                    assert not stats.get("audited_calls")
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
            for variant in ("python", "native"):
                actual = [r["seconds"] for r in group if r["variant"] == variant]
                assert len(actual) == expected
                assert item[variant] == median(actual)
            assert math.isclose(
                item["time_reduction_percent"],
                100 * (1 - item["native"] / item["python"]),
                abs_tol=1e-8,
            )
        if stage == "confirmation":
            assert summary == report["confirmation"]
        if stage == "large":
            assert summary == report["large_prefix"]
    attempt = root / "attempt20"
    frozen = json.loads((attempt / "frozen.json").read_text())
    with tarfile.open(attempt / "sources.tar.gz") as archive:
        for name, digest in frozen["source_hashes"].items():
            stream = archive.extractfile(name.lstrip("/"))
            assert stream is not None
            assert hashlib.sha256(stream.read()).hexdigest() == digest
            sources += 1
    result = json.loads((attempt / "result.json").read_text())
    assert result["termination"] == "time_limit" and not result["squares"]
    assert result["restored"] and not result["residual_stats"]
    assert result["search_seconds"] >= frozen["config"]["limit"]
    assert result["min_unfixed"] == min(r["min_unfixed"] for r in result["milestones"])
    assert result["nodes"] == result["milestones"][-1]["nodes"]
    assert result["sum_stats"]["calls"] == sum(
        v for k, v in result["sum_stats"].items() if k.startswith("path_")
    )
    assert result["nodes"] == report["attempt20"]["nodes"]
    assert runs == report["runs"]
    assert squares == report["validated_squares"]
    print(
        json.dumps(
            dict(
                runs=runs,
                validated_squares=squares,
                audited_sum_calls=audited,
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
