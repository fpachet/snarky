from __future__ import annotations

import k3
import numpy as np
from run_v24_contrastive_moments import _status_counts


def test_status_counts_partition_strong_blocks_into_residual_or_v23() -> None:
    blocks = np.asarray(
        [
            [76, 67, 60, 48],
            [76, 67, 62, 48],
            [76, 67, 64, 48],
        ],
        dtype=np.int16,
    )
    lattice = k3.RhythmicLattice(
        piece_id="p",
        offsets=np.asarray([0, 1, 2], dtype=np.float32),
        blocks=blocks,
        attacks=np.ones((3, 4), dtype=bool),
        end_offset=3.0,
        tonic_pc=0,
        mode=0,
        metric_levels=np.asarray([1, 3, 1], dtype=np.int8),
    )

    counts, total = _status_counts(
        blocks,
        lattice,
        candidate_min=48,
        candidate_max=76,
    )

    assert total == 1
    assert counts.sum() == 1
    assert counts[3] == 1
