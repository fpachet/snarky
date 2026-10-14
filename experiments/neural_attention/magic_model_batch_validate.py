"""Read-only checks of captured fixpoints and whole native compilation trials."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tarfile
from collections import defaultdict
from pathlib import Path
from statistics import median


def load(path):
    return json.loads(path.read_text())


def signature(row):
    return (
        row["nodes"],
        row["failures"],
        row["revisions"],
        row["termination"],
        row["squares"],
        {k: v for k, v in row["residual_stats"].items() if k != "enum_seconds"},
        row.get("reductions_sha256"),
        row.get("reduction_events"),
    )


def square(n, values):
    assert sorted(values) == list(range(1, n * n + 1))
    lines = [values[i * n : (i + 1) * n] for i in range(n)] + [
        values[i::n] for i in range(n)
    ]
    lines += [values[:: n + 1], values[n - 1 : n * n - 1 : n - 1]]
    assert all(len(line) == n and sum(line) == n * (n * n + 1) // 2 for line in lines)


def validate(root):
    manifest = load(root / "manifest.json")
    for name, digest in manifest.items():
        path = root / name
        assert path.resolve().is_relative_to(root.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    report = load(root / "report.json")
    sources = episodes = runs = squares = 0
    final = load(root / "verification/frozen.json")
    with tarfile.open(root / "verification/sources.tar.gz") as archive:
        for name, digest in final["source_hashes"].items():
            stream = archive.extractfile(name.lstrip("/"))
            assert stream is not None
            assert hashlib.sha256(stream.read()).hexdigest() == digest
            sources += 1
    for row in load(root / "code_equivalence.json"):
        for record in row["sections"].values():
            for label in ("before", "after"):
                assert (
                    hashlib.sha256(
                        (root / record[label + "_file"]).read_bytes()
                    ).hexdigest()
                    == record[label]
                )
            assert record["equal"] and record["before"] == record["after"]
    assert report["replay"] == load(root / "replay_confirmation/summary.json")
    for stage in report["stages"]:
        folder = root / stage
        frozen = load(folder / "frozen.json")
        with tarfile.open(folder / "sources.tar.gz") as archive:
            for name, digest in frozen["source_hashes"].items():
                stream = archive.extractfile(name.lstrip("/"))
                assert stream is not None
                assert hashlib.sha256(stream.read()).hexdigest() == digest
                sources += 1
        if stage.startswith("replay"):
            generic = load(folder / "compile.json")["generic"]
            assert (
                hashlib.sha256((folder / "generic.c").read_bytes()).hexdigest()
                == generic["identity"]["source_sha256"]
            )
            summary = load(folder / "summary.json")
            for item in summary:
                n = item["size"]
                case = folder / str(n)
                compiled = load(case / "compile.json")
                assert (
                    hashlib.sha256((case / "special.c").read_bytes()).hexdigest()
                    == compiled["identity"]["source_sha256"]
                )
                capture = load(case / "capture.json")
                assert capture["model_key"] == compiled["model_key"]
                for values in capture["squares"]:
                    square(n, values)
                    squares += 1
                audit = load(case / "audit.json")
                assert len(audit) == len(capture["samples"]) == item["samples"]
                episodes += len(audit)
                for sample, answer in zip(capture["samples"], audit, strict=True):
                    assert sample["node"] == answer["node"]
                    assert sample["consistent"] == answer["consistent"]
                    assert answer["reductions"] == len(answer["log"])
                    if answer["consistent"]:
                        assert sample["after"] == answer["masks"]
                rows = load(case / "runs.json")
                assert len(rows) == 2 * frozen["config"]["repeats"]
                assert load(case / "schedule.json") == [
                    [r["repeat"], r["variant"]] for r in rows
                ]
                grouped = defaultdict(list)
                for row in rows:
                    grouped[row["repeat"]].append(row)
                    assert row["episodes"] == item["cycles"] * item["samples"]
                for pair in grouped.values():
                    assert pair[0]["work_sha256"] == pair[1]["work_sha256"]
                    for key in [
                        "episodes",
                        "revisions",
                        "support_calls",
                        "cache_hits",
                        "reductions",
                    ]:
                        assert pair[0][key] == pair[1][key]
                for variant in ["generic", "special"]:
                    assert item[variant + "_seconds"] == median(
                        r["seconds"] / item["cycles"]
                        for r in rows
                        if r["variant"] == variant
                    )
                assert math.isclose(
                    item["specialization_reduction_percent"],
                    100 * (1 - item["special_seconds"] / item["generic_seconds"]),
                    abs_tol=1e-8,
                )
                assert item["python_control_seconds"] == median(
                    load(case / "control.json")["seconds"]
                )
                runs += len(rows)
        else:
            rows = [
                json.loads(line)
                for line in (folder / "runs.jsonl").read_text().splitlines()
            ]
            assert load(folder / "schedule.json") == [
                [r["size"], r["strategy"], r["variant"], r["repeat"]] for r in rows
            ]
            groups = defaultdict(list)
            for row in rows:
                groups[row["size"], row["strategy"]].append(row)
                assert row["termination"] in ["solution_limit", "node_limit"]
                for values in row["squares"]:
                    square(row["size"], values)
                    squares += 1
                if row["variant"] != "control":
                    stats = row["batch_stats"]
                    assert stats["revisions"] == row["revisions"]
                    assert (
                        stats["support_calls"] + stats["cache_hits"]
                        == stats["revisions"]
                    )
            summary = load(folder / "summary.json")
            for item in summary:
                group = groups[item["size"], item["strategy"]]
                for subset in [
                    [r for r in group if r["variant"] == "control"],
                    [r for r in group if r["variant"] != "control"],
                ]:
                    assert all(signature(r) == signature(subset[0]) for r in subset)
                expected = (
                    1
                    if frozen["config"]["phase"] == "audit"
                    else frozen["config"]["repeats"]
                )
                assert len(group) == 3 * expected
                for variant in ["control", "generic", "special"]:
                    assert item[variant] == median(
                        r["seconds"] for r in group if r["variant"] == variant
                    )
                assert math.isclose(
                    item["specialization_reduction_percent"],
                    100 * (1 - item["special"] / item["generic"]),
                    abs_tol=1e-8,
                )
            if stage == "search_timing":
                assert summary == report["whole_solve"]
            runs += len(rows)
    assert episodes == report["audited_episodes"]
    assert runs == report["runs"]
    assert squares == report["validated_squares"]
    print(
        json.dumps(
            dict(
                audited_episodes=episodes,
                runs=runs,
                validated_squares=squares,
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
