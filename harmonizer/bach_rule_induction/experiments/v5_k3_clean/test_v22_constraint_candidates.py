from __future__ import annotations

import audit_v22_constraint_candidates as audit
import numpy as np


def test_factor_statistics_condition_only_on_testable_rows() -> None:
    matrix = np.asarray(
        [
            [False, False, False],
            [False, True, True],
            [True, False, True],
        ]
    )
    chosen = np.asarray([0, 0, 2])
    pieces = np.asarray(["a", "a", "b"])

    result = audit.factor_extreme_statistics(matrix, chosen, pieces)

    assert result["testable_opportunities"] == 2
    assert result["authentic_activations"] == 1
    assert result["authentic_activation_rate"] == 0.5
    assert result["opportunity_piece_support"] == 2


def test_exact_prohibition_requires_both_splits_to_have_no_violation() -> None:
    train = {
        "testable_opportunities": 200,
        "opportunity_piece_support": 20,
        "authentic_activations": 0,
        "authentic_inactivations": 200,
        "authentic_activation_rate": 0.0,
    }
    validation = {
        "testable_opportunities": 50,
        "opportunity_piece_support": 8,
        "authentic_activations": 0,
        "authentic_inactivations": 50,
        "authentic_activation_rate": 0.0,
    }

    classification = audit.classify_candidate(
        train,
        validation,
        minimum_train_opportunities=100,
        minimum_train_pieces=10,
        minimum_validation_opportunities=30,
        near_exception_rate=0.01,
    )

    assert classification == "exact_empirical_prohibition"


def test_one_validation_violation_prevents_exact_constraint() -> None:
    train = {
        "testable_opportunities": 200,
        "opportunity_piece_support": 20,
        "authentic_activations": 0,
        "authentic_inactivations": 200,
        "authentic_activation_rate": 0.0,
    }
    validation = {
        "testable_opportunities": 50,
        "opportunity_piece_support": 8,
        "authentic_activations": 1,
        "authentic_inactivations": 49,
        "authentic_activation_rate": 0.02,
    }

    classification = audit.classify_candidate(
        train,
        validation,
        minimum_train_opportunities=100,
        minimum_train_pieces=10,
        minimum_validation_opportunities=30,
        near_exception_rate=0.01,
    )

    assert classification is None
