"""Validate archived magic-square evidence after directory or runtime changes.

Frozen paths and code retain their recorded bytes. Sources are checked against
archived payloads, not against an evolving live solver or the old directory name.
No archived program is executed and no evidence file is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "benchmarks/history"
DEFAULT_EXPERIMENTS = (
    "magic_domain_ops_2026-10-13",
    "magic_scheduler_graph_2026-10-13",
)


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def recorded_path(value: str, root: Path) -> Path:
    """Relocate a recorded absolute workspace path or the former archive path."""
    path = Path(value)
    if path.is_absolute():
        for marker in ("/benchmarks/", "/experiments/", "/src/"):
            if marker in value:
                value = marker.lstrip("/") + value.split(marker, 1)[1]
                break
        else:
            return path
    value = value.replace("benchmarks/results/", "benchmarks/history/")
    return root / value


def validate_square(size: int, square: list[int]) -> None:
    assert sorted(square) == list(range(1, size * size + 1)), "invalid square values"
    target = size * (size * size + 1) // 2
    lines = [square[i * size : (i + 1) * size] for i in range(size)]
    lines += [square[i::size] for i in range(size)]
    lines += [square[:: size + 1], square[size - 1 : size * size - 1 : size - 1]]
    assert all(len(line) == size and sum(line) == target for line in lines), (
        "invalid magic-square line"
    )


def validate_experiment(folder: Path, *, root: Path = ROOT) -> dict[str, int | str]:
    manifest = json.loads((folder / "source_manifest.json").read_text())
    for relative, expected in manifest.items():
        path = (folder / relative).resolve()
        assert path.is_relative_to(folder.resolve()), "manifest escapes experiment"
        assert digest(path.read_bytes()) == expected, f"source manifest: {relative}"

    # Original scripts and runtime files can be in text fixtures or source tars.
    # Matching content hashes verifies their identity without rewriting the paths
    # in scientific records or executing historical code against today's API.
    available: set[str] = set()
    files = [
        p
        for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    ]
    for path in files:
        available.add(digest(path.read_bytes()))
        if path.name.endswith(".tar.gz"):
            with tarfile.open(path) as archive:
                for member in archive:
                    if member.isfile():
                        payload = archive.extractfile(member)
                        assert payload is not None
                        available.add(digest(payload.read()))
    source_count = 0
    for path in files:
        if path.suffix != ".json":
            continue
        record = json.loads(path.read_text())
        if not isinstance(record, dict):
            continue
        for original, expected in record.get("source_hashes", {}).items():
            if expected not in available:
                live = recorded_path(original, root)
                assert live.is_file() and digest(live.read_bytes()) == expected, (
                    f"missing recorded source: {path.relative_to(folder)}: {original}"
                )
            source_count += 1

    counts: Counter[str] = Counter()
    for path in folder.rglob("runs.jsonl"):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        frozen = json.loads(path.with_name("frozen.json").read_text())
        actual = [(r["size"], r["variant"], r["repeat"]) for r in rows]
        schedule = [tuple(item) for item in frozen["schedule"]]
        assert len(rows) == len(schedule) and sorted(actual) == sorted(schedule), (
            f"incomplete run schedule: {path}"
        )
        signatures = {}
        for row in rows:
            assert row["termination"] in {"solution_limit", "node_limit", "time_limit"}
            if row["termination"] != "time_limit" and row["variant"] not in {
                "batch",
                "combined",
            }:
                signature = (
                    row["settings"],
                    row["nodes"],
                    row["failures"],
                    row["revisions"],
                    row["termination"],
                    row["squares"],
                    row["reductions_sha256"],
                    row["reduction_events"],
                    {k: v for k, v in row["stats"].items() if k != "seconds"},
                )
                size = row["size"]
                if size in signatures:
                    assert signatures[size] == signature, (
                        f"different search: {path}: {size}"
                    )
                signatures[size] = signature
            for square in row["squares"]:
                validate_square(row["size"], square)
                counts["validated_squares"] += 1
            counts["runs"] += 1
            counts[row["termination"]] += 1
        summary = json.loads(path.with_name("summary.json").read_text())
        for item in summary:
            for variant, stats in item["variants"].items():
                samples = [
                    r["total_seconds"]
                    for r in rows
                    if r["size"] == item["size"] and r["variant"] == variant
                ]
                assert stats["median_seconds"] == median(samples), "incorrect median"
    return dict(
        experiment=folder.name,
        source_manifest_files=len(manifest),
        recorded_source_checks=source_count,
        **counts,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiments",
        nargs="+",
        choices=DEFAULT_EXPERIMENTS,
        default=DEFAULT_EXPERIMENTS,
    )
    args = parser.parse_args()
    reports = [validate_experiment(HISTORY / name) for name in args.experiments]
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
