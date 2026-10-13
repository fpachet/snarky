"""Archive relocation keeps source identities, witnesses and comparisons valid."""

import io
import json
import tarfile

import pytest

from scripts.check_benchmark_history import digest, recorded_path, validate_experiment


@pytest.fixture
def archive(tmp_path):
    root = tmp_path
    folder = root / "benchmarks/history/example"
    folder.mkdir(parents=True)
    original = b"ORIGINAL = 'benchmarks/results/example'\n"
    source = folder / "source.py.txt"
    source.write_bytes(original)
    payloads = folder / "sources.tar.gz"
    with tarfile.open(payloads, "w:gz") as tar:
        member = tarfile.TarInfo("src/example.py")
        member.size = len(original)
        tar.addfile(member, io.BytesIO(original))
    live = root / "src/example.py"
    live.parent.mkdir()
    live.write_text("CURRENT = 'benchmarks/history/example'\n")
    (folder / "source_manifest.json").write_text(
        json.dumps(
            {
                "source.py.txt": digest(original),
                "sources.tar.gz": digest(payloads.read_bytes()),
            }
        )
    )
    (folder / "frozen.json").write_text(
        json.dumps(
            {
                "schedule": [[3, "before", 0], [3, "after", 0]],
                "source_hashes": {
                    "/old/workspace/src/example.py": digest(original),
                    "/old/workspace/benchmarks/results/example/source.py.txt": digest(
                        original
                    ),
                },
            }
        )
    )
    rows = [
        dict(
            size=3,
            variant=v,
            repeat=0,
            total_seconds=s,
            nodes=2,
            failures=0,
            revisions=3,
            settings={},
            termination="solution_limit",
            squares=[[8, 1, 6, 3, 5, 7, 4, 9, 2]],
            reductions_sha256="same",
            reduction_events=[1],
            stats={"seconds": s},
        )
        for v, s in [("before", 1.0), ("after", 0.5)]
    ]
    (folder / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (folder / "summary.json").write_text(
        json.dumps(
            [
                dict(
                    size=3,
                    variants={
                        v: dict(median_seconds=s)
                        for v, s in [("before", 1.0), ("after", 0.5)]
                    },
                )
            ]
        )
    )
    return root, folder


def test_checks_frozen_sources_after_move_and_live_runtime_change(archive):
    root, folder = archive
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    result = validate_experiment(folder, root=root)
    assert result["runs"] == result["validated_squares"] == 2
    assert result["recorded_source_checks"] == 2
    assert before == {p.name: p.read_bytes() for p in folder.iterdir()}
    assert not (root / "benchmarks/results").exists()
    assert recorded_path("/old/workspace/benchmarks/results/example", root) == folder


@pytest.mark.parametrize(
    "damage", ["source", "square", "search", "schedule", "hash", "median"]
)
def test_detects_corrupted_evidence(archive, damage):
    root, folder = archive
    rows = [
        json.loads(line) for line in (folder / "runs.jsonl").read_text().splitlines()
    ]
    if damage == "source":
        (folder / "source.py.txt").write_text("corrupted")
    elif damage == "square":
        rows[0]["squares"][0][0] = 1
    elif damage == "search":
        rows[1]["nodes"] += 1
    elif damage == "schedule":
        rows.pop()
    elif damage == "hash":
        path = folder / "frozen.json"
        record = json.loads(path.read_text())
        record["source_hashes"]["missing.py"] = "0" * 64
        path.write_text(json.dumps(record))
    elif damage == "median":
        path = folder / "summary.json"
        record = json.loads(path.read_text())
        record[0]["variants"]["before"]["median_seconds"] = 5
        path.write_text(json.dumps(record))
    (folder / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(AssertionError):
        validate_experiment(folder, root=root)
