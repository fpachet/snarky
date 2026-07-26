from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

MODULE_PATH = Path(__file__).with_name("run_poc.py")
SPEC = importlib.util.spec_from_file_location("differentiable_rules_poc", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
poc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = poc
SPEC.loader.exec_module(poc)


def synthetic_opportunities() -> poc.Opportunities:
    return poc.Opportunities(
        piece_ids=np.asarray(["a", "a", "b", "b"]),
        offsets_previous=np.asarray([0, 1, 0, 1], dtype=np.float32),
        offsets_current=np.asarray([1, 2, 1, 2], dtype=np.float32),
        previous_soprano=np.asarray([64, 64, 67, 67], dtype=np.int16),
        chosen_soprano=np.asarray([65, 63, 69, 65], dtype=np.int16),
        previous_bass=np.asarray([48, 48, 48, 48], dtype=np.int16),
        current_bass=np.asarray([50, 46, 50, 46], dtype=np.int16),
        candidate_min=60,
        candidate_max=72,
    )


def test_split_sizes_and_determinism() -> None:
    piece_ids = [f"bach/{index:03d}" for index in range(352)]
    first = poc.deterministic_splits(piece_ids, 1729)
    second = poc.deterministic_splits(piece_ids, 1729)
    assert first == second
    assert len(first["train"]) == 246
    assert len(first["validation"]) == 53
    assert len(first["test"]) == 53
    assert not (set(first["train"]) & set(first["validation"]))


def test_atom_masks_are_numeric_not_musicological() -> None:
    opportunities = synthetic_opportunities()
    atom_list = poc.atoms()
    labels = [atom.label for atom in atom_list]
    assert not any("fifth" in label for label in labels)
    assert not any("direct" in label for label in labels)
    masks = poc.atom_masks(opportunities, atom_list)
    target_zero = masks[poc.Atom("target_interval_mod12", 0)]
    assert target_zero.shape == (4, 13)


def test_clause_statistic_detects_avoidance() -> None:
    opportunities = synthetic_opportunities()
    atom_list = poc.atoms()
    masks = poc.atom_masks(opportunities, atom_list)
    clause = poc.Clause((poc.Atom("target_interval_mod12", 0),))
    statistic = poc.statistic_for_clause(
        clause,
        masks,
        poc.uniform_residual(opportunities),
        opportunities.chosen_indices,
    )
    assert statistic is not None
    assert statistic.observed_rate < statistic.availability_rate
    assert statistic.z_score < 0


def test_search_keeps_context_only_prefixes() -> None:
    opportunities = synthetic_opportunities()
    masks = poc.atom_masks(opportunities, poc.atoms())
    found = poc.search_clauses(
        opportunities,
        masks,
        poc.uniform_residual(opportunities),
        max_depth=2,
        beam_size=512,
        min_testable=1,
    )
    families = {
        tuple(atom.family for atom in statistic.clause.atoms) for statistic in found
    }
    assert (
        "source_interval_mod12",
        "target_interval_mod12",
    ) in families


def test_gradient_fit_improves_synthetic_conditional_loss() -> None:
    opportunities = synthetic_opportunities()
    atom_list = poc.atoms()
    masks = poc.atom_masks(opportunities, atom_list)
    clauses = [
        poc.Clause((poc.Atom("target_interval_mod12", value),)) for value in range(12)
    ]
    matrix = poc.feature_matrix(clauses, masks)
    weights, _ = poc.fit_sparse_conditional_model(
        matrix,
        opportunities.chosen_indices,
        matrix,
        opportunities.chosen_indices,
        l1=0.0,
        max_steps=80,
        learning_rate=0.05,
    )
    assert poc.conditional_nll(matrix, opportunities.chosen_indices, weights) < np.log(
        13
    )
