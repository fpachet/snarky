from __future__ import annotations

import numpy as np
from export_v18_explanatory_artifacts import _decision_ordinals, _examples


def test_decision_ordinals_restart_for_each_piece() -> None:
    pieces = np.asarray(["a", "a", "b", "a", "b"])

    assert _decision_ordinals(pieces).tolist() == [0, 1, 0, 2, 1]


def test_examples_distinguish_activation_from_avoidance() -> None:
    data = {
        "factors": np.asarray(
            [
                [[0], [1]],
                [[1], [0]],
            ],
            dtype=np.uint8,
        ),
        "chosen": np.asarray([1, 1]),
        "piece_ids": np.asarray(["a", "b"]),
        "voices": np.asarray([0, 3]),
    }

    active = _examples(data, 0, candidate_min=60, activated=True)
    avoided = _examples(data, 0, candidate_min=60, activated=False)

    assert active[0]["piece"] == "a"
    assert active[0]["chosen_midi"] == 61
    assert avoided[0]["piece"] == "b"
    assert avoided[0]["maximum_alternative_activation_count"] == 1
