"""Read-only validation of an archived residual-kernel reuse experiment."""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from collections import defaultdict
from pathlib import Path
from statistics import median


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def square(n, rows):
    if len(rows) == n * n and all(isinstance(v, int) for v in rows):
        rows = [rows[i * n : (i + 1) * n] for i in range(n)]
    assert len(rows) == n and all(len(row) == n for row in rows)
    assert sorted(v for row in rows for v in row) == list(range(1, n * n + 1))
    target = n * (n * n + 1) // 2
    assert all(sum(row) == target for row in rows)
    assert all(sum(rows[i][j] for i in range(n)) == target for j in range(n))
    assert sum(rows[i][i] for i in range(n)) == target
    assert sum(rows[i][n - 1 - i] for i in range(n)) == target


def validate(root):
    manifest = json.loads((root / "manifest.json").read_text())
    for name, digest in manifest.items():
        assert sha(root / name) == digest, name
    report = json.loads((root / "report.json").read_text())
    source_checks = runs = witnesses = replay_states = 0
    for stage in report["stages"]:
        directory = root / stage
        frozen = json.loads((directory / "frozen.json").read_text())
        with tarfile.open(directory / "sources.tar.gz") as archive:
            for name, digest in frozen["source_hashes"].items():
                stream = archive.extractfile(name.lstrip("/"))
                assert stream is not None
                assert hashlib.sha256(stream.read()).hexdigest() == digest
                source_checks += 1
        phase = frozen["config"]["phase"]
        if phase == "cache":
            cache = json.loads((directory / "cache.json").read_text())
            assert not cache["cold"]["cache_hit"]
            assert cache["cold"]["compile_seconds"] > 0
            for kind in ("same_process", "new_process"):
                assert cache[kind]["cache_hit"] and cache[kind]["compile_seconds"] == 0
                assert cache[kind]["cache_key"] == cache["cold"]["cache_key"]
            assert cache["same_process"]["loaded_reused"]
            assert not cache["new_process"]["loaded_reused"]
            continue
        records = [
            json.loads(line)
            for line in (directory / "runs.jsonl").read_text().splitlines()
        ]
        if phase == "replay":
            assert len(records) == 75
            for row in records:
                replay_states += 1
                variants = row["variants"]
                keys = ("status", "visits", "leaves", "solutions", "witness")
                assert all(variants["old2"][k] == variants["new2"][k] for k in keys)
                completed = {
                    bool(v["status"]) for v in variants.values() if v["status"] != 2
                }
                assert len(completed) <= 1
                for result in variants.values():
                    assert 0 <= result["visits"] <= frozen["config"]["work_limit"]
                    assert result["kernel_seconds"] == median(result["kernel_samples"])
                    if "residual" in row and result["witness"] is not None:
                        witness, residual = result["witness"], row["residual"]
                        assert len(witness) == len(residual["domains"])
                        assert len(set(witness)) == len(witness)
                        assert all(
                            v in d
                            for v, d in zip(witness, residual["domains"], strict=True)
                        )
                        for op, terms, target in residual["rows"]:
                            value = sum(c * witness[i] for i, c in terms)
                            assert (
                                value == target
                                if op == 0
                                else value <= target
                                if op == 1
                                else value >= target
                            )
                if stage == report["final_replay"]:
                    assert all(
                        variants["sorted_array3"][k] == variants["bitsets4"][k]
                        for k in keys
                    )
            continue
        assert phase == "whole"
        schedule = json.loads((directory / "schedule.json").read_text())
        assert schedule == [[r["size"], r["variant"], r["repeat"]] for r in records]
        groups = defaultdict(list)
        for row in records:
            runs += 1
            assert row["termination"] == "solution_limit" and len(row["squares"]) == 1
            square(row["size"], row["squares"][0])
            witnesses += 1
            if row["variant"] != "cp":
                stats = row["stats"]
                assert stats["attempts"] == sum(
                    stats.get(k, 0) for k in ("exhausted", "fallbacks", "witnesses")
                )
                assert (
                    stats["visits"]
                    <= stats["attempts"] * frozen["config"]["work_limit"]
                )
            groups[row["size"], row["variant"]].append(row)
        summary = json.loads((directory / "summary.json").read_text())
        for row in summary:
            for variant, values in row["variants"].items():
                group = groups[row["size"], variant]
                assert len(group) == frozen["config"]["repeats"]
                assert values["median_seconds"] == median(r["seconds"] for r in group)
                assert values["solved"] == len(group)
                signatures = {
                    (
                        r["nodes"],
                        r["failures"],
                        r["revisions"],
                        json.dumps(r["squares"]),
                        json.dumps(
                            {
                                k: v
                                for k, v in r["stats"].items()
                                if k != "enum_seconds"
                            },
                            sort_keys=True,
                        ),
                    )
                    for r in group
                }
                assert len(signatures) == 1
        if stage == report["final_whole"]:
            for row, headline in zip(summary, report["whole_medians"], strict=True):
                assert row["size"] == headline["size"]
                for variant, values in row["variants"].items():
                    assert values["median_seconds"] == headline[variant]
    assert runs == report["whole_runs"]
    assert replay_states == report["replay_states"]
    print(
        json.dumps(
            dict(
                whole_runs=runs,
                replay_states=replay_states,
                validated_squares=witnesses,
                source_checks=source_checks,
                manifest_files=len(manifest),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    validate(
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    )
