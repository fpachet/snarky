from __future__ import annotations

import json
from pathlib import Path

import k3
import numpy as np
import pytest


@pytest.fixture
def synthetic_context_path(tmp_path: Path) -> Path:
    """Exercise catalogue loading without an untracked corpus cache."""
    split_path = (
        Path(__file__).resolve().parent.parent
        / "differentiable_rules_poc/results/splits.variant-safe.json"
    )
    splits = json.loads(split_path.read_text(encoding="utf-8"))["grouped_split"]
    # Reuse a training ID solely to pass the loader's split filter. The pitches
    # are synthetic; these tests check catalogue structure, not corpus statistics.
    dataset = k3.K3Dataset(
        piece_ids=np.asarray([splits["train"][0]]),
        offsets=np.asarray([[0, 1, 2]], dtype=np.float32),
        voice_indices=np.asarray([0], dtype=np.int8),
        blocks=np.asarray(
            [[[67, 64, 55, 48], [69, 66, 57, 50], [71, 67, 59, 52]]],
            dtype=np.int16,
        ),
        attacks=np.ones((1, 3, 4), dtype=bool),
        candidate_min=36,
        candidate_max=81,
        tonic_pcs=np.asarray([0], dtype=np.int8),
        modes=np.asarray([0], dtype=np.int8),
        metric_levels=np.asarray([3], dtype=np.int8),
    )
    path = tmp_path / "synthetic-context.npz"
    k3.save_k3_dataset(path, dataset)
    return path
