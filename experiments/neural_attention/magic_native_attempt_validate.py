"""Read-only validation of a frozen native-kernel long-run experiment."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tarfile
from pathlib import Path


def validate(root):
    manifest = json.loads((root / "manifest.json").read_text())
    for name, digest in manifest.items():
        path = root / name
        assert path.resolve().is_relative_to(root.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    frozen = json.loads((root / "frozen.json").read_text())
    with tarfile.open(root / "sources.tar.gz") as archive:
        for name, digest in frozen["source_hashes"].items():
            stream = archive.extractfile(name.lstrip("/"))
            assert stream is not None
            assert hashlib.sha256(stream.read()).hexdigest() == digest
    compiled = json.loads((root / "compile.json").read_text())
    for key, filename in (
        ("residual", "residual_enum.c"),
        ("sums", "sum_support.c"),
        ("alldiff", "alldiff_support.c"),
    ):
        hashes = [
            h for p, h in frozen["source_hashes"].items() if Path(p).name == filename
        ]
        assert hashes == [compiled[key]["identity"]["source_sha256"]]
    result = json.loads((root / "result.json").read_text())
    config = frozen["config"]
    assert result["size"] == config["size"] and result["restored"]
    assert result["nodes"] > 0 and result["search_seconds"] > 0
    assert math.isclose(
        result["nodes_per_second"],
        result["nodes"] / result["search_seconds"],
        abs_tol=1e-8,
    )
    if result["termination"] == "time_limit":
        assert result["search_seconds"] >= config["limit"]
    if not result["squares"]:
        assert result["status"] == "unknown"
    for values in result["squares"]:
        n = result["size"]
        assert sorted(values) == list(range(1, n * n + 1))
        lines = [values[i * n : (i + 1) * n] for i in range(n)]
        lines += [values[i::n] for i in range(n)]
        lines += [values[:: n + 1], values[n - 1 : n * n - 1 : n - 1]]
        assert all(
            len(line) == n and sum(line) == n * (n * n + 1) // 2 for line in lines
        )
    rows = [
        json.loads(line) for line in (root / "progress.jsonl").read_text().splitlines()
    ]
    previous = dict(
        seconds=0,
        nodes=0,
        failures=0,
        revisions=0,
        max_depth=0,
        min_unfixed_before_propagation=config["size"] ** 2,
    )
    for row in rows:
        assert row["seconds"] > previous["seconds"]
        for field in ("nodes", "failures", "revisions", "max_depth"):
            assert row[field] >= previous[field]
        assert (
            row["min_unfixed_before_propagation"]
            <= previous["min_unfixed_before_propagation"]
        )
        assert math.isclose(
            row["average_nodes_per_second"], row["nodes"] / row["seconds"], abs_tol=1e-8
        )
        assert math.isclose(
            row["interval_nodes_per_second"],
            (row["nodes"] - previous["nodes"]) / (row["seconds"] - previous["seconds"]),
            abs_tol=1e-8,
        )
        previous = row
    assert rows[-1]["event"] == "finished"
    for field in (
        "nodes",
        "failures",
        "revisions",
        "max_depth",
        "min_unfixed_before_propagation",
    ):
        assert rows[-1][field] == result[field]
    stats = result["sum_stats"]
    assert stats["calls"] == sum(
        v for k, v in stats.items() if k.startswith("path_")
    ) + stats.get("outside_original_bounds", 0)
    stats = result["alldiff_stats"]
    assert stats["calls"] == sum(
        stats.get(k, 0) for k in ("native_calls", "cached_calls", "empty_calls")
    )
    report = json.loads((root / "report.json").read_text())
    for field in ("nodes", "nodes_per_second", "search_seconds", "termination"):
        assert report[field] == result[field]
    assert report["commit"] == frozen["git_head"]
    assert report["solved"] == bool(result["squares"])
    assert all(row in rows for row in report["checkpoints"])
    print(
        json.dumps(
            dict(
                nodes=result["nodes"],
                nodes_per_second=result["nodes_per_second"],
                termination=result["termination"],
                validated_squares=len(result["squares"]),
                progress_samples=len(rows),
                source_checks=len(frozen["source_hashes"]),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    validate(
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    )
