#!/usr/bin/env python3
"""Prepare piece-disjoint caches for complete V18 structure reinduction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE / "work/k3-exact-catalogue-32x10.npz"
DEFAULT_DIRECTORY = HERE / "work/v18-structure-stability"


def _folds(pieces: list[str], fold_count: int) -> list[set[str]]:
    return [set(pieces[offset::fold_count]) for offset in range(fold_count)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--fold-count", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive = np.load(args.source)
    metadata = json.loads(str(archive["metadata"]))
    piece_ids = archive["train_piece_ids"]
    pieces = sorted(map(str, np.unique(piece_ids)))
    folds = _folds(pieces, args.fold_count)
    args.directory.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": str(args.source.resolve()),
        "fold_count": len(folds),
        "piece_count": len(pieces),
        "folds": [],
    }
    for index, validation_pieces in enumerate(folds, start=1):
        validation_mask = np.asarray(
            [str(piece) in validation_pieces for piece in piece_ids],
            dtype=bool,
        )
        train_mask = ~validation_mask
        fold_metadata = {
            **metadata,
            "structure_stability_fold": index,
            "train_ids": sorted(set(pieces) - validation_pieces),
            "validation_ids": sorted(validation_pieces),
        }
        output = args.directory / f"fold{index}.npz"
        payload = {"metadata": json.dumps(fold_metadata, sort_keys=True)}
        for suffix in (
            "factors",
            "chosen",
            "piece_ids",
            "voices",
            "modes",
            "tonics",
        ):
            source = archive[f"train_{suffix}"]
            payload[f"train_{suffix}"] = source[train_mask]
            payload[f"validation_{suffix}"] = source[validation_mask]
        np.savez_compressed(output, **payload)
        manifest["folds"].append(
            {
                "fold": index,
                "cache": str(output.resolve()),
                "train_pieces": sorted(set(pieces) - validation_pieces),
                "validation_pieces": sorted(validation_pieces),
                "train_decisions": int(train_mask.sum()),
                "validation_decisions": int(validation_mask.sum()),
            }
        )
        print(
            f"[v18-structure] fold={index} "
            f"train={train_mask.sum()} validation={validation_mask.sum()} "
            f"wrote {output}",
            flush=True,
        )
    manifest_path = args.directory / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[v18-structure] wrote {manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
