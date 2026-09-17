from __future__ import annotations

from prepare_v18_structure_stability import _folds


def test_piece_folds_are_disjoint_and_exhaustive() -> None:
    pieces = [f"piece-{index}" for index in range(11)]

    folds = _folds(pieces, 4)

    assert set().union(*folds) == set(pieces)
    assert sum(map(len, folds)) == len(pieces)
    for index, fold in enumerate(folds):
        assert fold.isdisjoint(set().union(*folds[:index], *folds[index + 1 :]))
