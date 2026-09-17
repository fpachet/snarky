from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

MODULE_PATH = Path(__file__).with_name("run_column_generation.py")
MODULE_DIRECTORY = str(MODULE_PATH.parent)
if MODULE_DIRECTORY not in sys.path:
    sys.path.insert(0, MODULE_DIRECTORY)
SPEC = importlib.util.spec_from_file_location("column_generation_poc", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
column = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = column
SPEC.loader.exec_module(column)
base = column.base


def synthetic_opportunities() -> base.Opportunities:
    return base.Opportunities(
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


def test_baseline_uses_only_generic_main_effects() -> None:
    clauses = column.baseline_clauses()
    assert len(clauses) == 21
    assert all(clause.complexity == 1 for clause in clauses)
    labels = [clause.key for clause in clauses]
    assert not any("direct" in label or "fifth" in label for label in labels)


def test_explicit_grouped_split_is_loaded_and_validated() -> None:
    piece_ids = ["a", "b", "c"]
    payload = {
        "strategy": "grouped",
        "grouped_split": {
            "train": ["a"],
            "validation": ["b"],
            "test": ["c"],
        },
    }
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "splits.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        splits, metadata = column.load_experiment_splits(piece_ids, 1729, path)
    assert splits == payload["grouped_split"]
    assert metadata["strategy"] == "grouped"


def test_uniform_residual_statistic_matches_marginal_direction() -> None:
    opportunities = synthetic_opportunities()
    atoms = base.atoms(include_derived=True)
    masks = base.atom_masks(opportunities, atoms)
    probabilities = column.probability_matrix(
        opportunities, [], masks, np.asarray([], dtype=np.float64)
    )
    clause = base.Clause((base.Atom("target_interval_mod12", 0),))
    statistic = column.residual_statistic_for_clause(
        clause,
        masks,
        probabilities,
        opportunities,
        [],
        complexity_penalty=0.0,
        redundancy_penalty=0.0,
    )
    assert statistic is not None
    assert statistic.gradient < 0
    assert statistic.z_score < 0
    assert statistic.approximate_nll_gain > 0


def test_piece_bootstrap_is_deterministic() -> None:
    opportunities = synthetic_opportunities()
    atoms = base.atoms(include_derived=True)
    masks = base.atom_masks(opportunities, atoms)
    probabilities = column.probability_matrix(
        opportunities, [], masks, np.asarray([], dtype=np.float64)
    )
    clause = base.Clause((base.Atom("target_interval_mod12", 0),))
    first = column.bootstrap_residual_clause_by_piece(
        clause,
        opportunities,
        masks,
        probabilities,
        replicates=100,
        seed=123,
    )
    second = column.bootstrap_residual_clause_by_piece(
        clause,
        opportunities,
        masks,
        probabilities,
        replicates=100,
        seed=123,
    )
    assert first == second
    assert first["piece_count"] == 2
    assert 0 <= first["negative_fraction"] <= 1


def test_residual_vanishes_when_model_matches_empirical_choice() -> None:
    opportunities = synthetic_opportunities()
    atoms = base.atoms(include_derived=True)
    masks = base.atom_masks(opportunities, atoms)
    clause = base.Clause((base.Atom("target_interval_mod12", 0),))
    mask = base.clause_mask(clause, masks)
    probabilities = np.zeros(mask.shape, dtype=np.float64)
    probabilities[np.arange(opportunities.size), opportunities.chosen_indices] = 1.0
    statistic = column.residual_statistic_for_clause(
        clause,
        masks,
        probabilities,
        opportunities,
        [],
        complexity_penalty=0.0,
        redundancy_penalty=0.0,
    )
    assert statistic is None


def test_search_can_extend_context_only_prefixes() -> None:
    opportunities = synthetic_opportunities()
    atoms = base.atoms(include_derived=True)
    masks = base.atom_masks(opportunities, atoms)
    probabilities = column.probability_matrix(
        opportunities, [], masks, np.asarray([], dtype=np.float64)
    )
    found = column.search_residual_clauses(
        opportunities,
        masks,
        probabilities,
        [],
        max_depth=2,
        beam_size=512,
        min_testable=1,
        min_piece_support=1,
        complexity_penalty=0.0,
        redundancy_penalty=0.0,
        column_direction="both",
    )
    families = {
        tuple(atom.family for atom in statistic.clause.atoms) for statistic in found
    }
    assert (
        "source_interval_mod12",
        "target_interval_mod12",
    ) in families


def test_direct_scan_is_symmetric_over_all_numeric_classes() -> None:
    clauses = column.direct_arrival_clauses()
    assert len(clauses) == 12
    assert [clause.atoms[0].value for clause in clauses] == list(range(12))
    assert all(clause.complexity == 3 for clause in clauses)


def test_family_selection_applies_same_thresholds_to_all_classes() -> None:
    scan = [
        {
            "numeric_class": 0,
            "residual_train": {"z_score": -4.0},
            "residual_validation": {"z_score": -2.5},
        },
        {
            "numeric_class": 1,
            "residual_train": {"z_score": -4.0},
            "residual_validation": {"z_score": -1.0},
        },
        {
            "numeric_class": 7,
            "residual_train": {"z_score": -3.1},
            "residual_validation": {"z_score": -2.1},
        },
    ]
    assert column.select_direct_family_classes(scan, -3.0, -2.0) == [0, 7]


def test_induced_direct_formula_matches_reference_on_valid_domain() -> None:
    comparison = column.compare_direct_clause_to_reference(
        7,
        upper_range=range(60, 68),
        lower_range=range(45, 55),
    )
    assert comparison["tested_valid_outer_voice_states"] > 0
    assert comparison["learned_positive_states"] > 0
    assert comparison["mismatches"] == 0
    assert comparison["classification"] == "RECOVERED_EQUIVALENT"
