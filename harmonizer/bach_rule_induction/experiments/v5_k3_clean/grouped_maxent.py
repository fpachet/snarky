"""Joint exact-pseudolikelihood fitting with structured factor groups."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import run_exact_factor_reinduction as exact


@dataclass(frozen=True)
class GroupPenalty:
    """One jointly selected block of factor coefficients."""

    name: str
    indices: np.ndarray
    strength: float
    scale_by_sqrt_size: bool = True
    matrix_shape: tuple[int, ...] | None = None
    double_center_last_two_axes: bool = False
    center_last_axis: bool = False


def double_center_transition_weights(
    weights: np.ndarray,
    *,
    shape: tuple[int, int, int],
) -> np.ndarray:
    """Remove departure and arrival main effects from transition interactions."""

    matrix = np.asarray(weights, dtype=np.float64).reshape(shape).copy()
    matrix -= matrix.mean(axis=2, keepdims=True)
    matrix -= matrix.mean(axis=1, keepdims=True)
    matrix += matrix.mean(axis=(1, 2), keepdims=True)
    return matrix.reshape(-1)


def center_last_axis_weights(
    weights: np.ndarray,
    *,
    shape: tuple[int, ...],
) -> np.ndarray:
    """Remove one categorical main effect independently in each outer cell."""

    matrix = np.asarray(weights, dtype=np.float64).reshape(shape).copy()
    matrix -= matrix.mean(axis=-1, keepdims=True)
    return matrix.reshape(-1)


def sparse_group_prox(
    weights: np.ndarray,
    *,
    learning_rate: float,
    l1: np.ndarray,
    groups: tuple[GroupPenalty, ...],
) -> np.ndarray:
    """Apply the exact proximal map for L1 plus disjoint group-L2 penalties."""

    result = np.sign(weights) * np.maximum(
        np.abs(weights) - learning_rate * l1,
        0.0,
    )
    for group in groups:
        indices = np.asarray(group.indices, dtype=np.int64)
        block = result[indices]
        norm = float(np.linalg.norm(block))
        multiplier = math.sqrt(indices.size) if group.scale_by_sqrt_size else 1.0
        threshold = learning_rate * group.strength * multiplier
        if norm <= threshold:
            block = np.zeros_like(block)
        else:
            block *= 1.0 - threshold / norm
        if group.double_center_last_two_axes:
            if group.matrix_shape is None:
                raise ValueError("Double-centering requires a matrix shape")
            block = double_center_transition_weights(
                block,
                shape=group.matrix_shape,
            )
        if group.center_last_axis:
            if group.matrix_shape is None:
                raise ValueError("Centering requires a matrix shape")
            block = center_last_axis_weights(
                block,
                shape=group.matrix_shape,
            )
        result[indices] = block
    return result


def _project_groups(
    weights: np.ndarray,
    groups: tuple[GroupPenalty, ...],
) -> None:
    for group in groups:
        if (
            not group.double_center_last_two_axes
            and not group.center_last_axis
        ):
            continue
        if group.matrix_shape is None:
            raise ValueError("Centering requires a matrix shape")
        indices = np.asarray(group.indices, dtype=np.int64)
        if group.double_center_last_two_axes:
            weights[indices] = double_center_transition_weights(
                weights[indices],
                shape=group.matrix_shape,
            )
        if group.center_last_axis:
            weights[indices] = center_last_axis_weights(
                weights[indices],
                shape=group.matrix_shape,
            )


def fit_grouped(
    train: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    candidate_pitches: np.ndarray,
    initial: exact.Parameters,
    *,
    steps: int,
    learning_rate: float,
    l1: np.ndarray,
    l2: float,
    groups: tuple[GroupPenalty, ...],
    return_best_validation: bool = True,
) -> tuple[exact.Parameters, dict[str, Any]]:
    """Fit every active coefficient jointly, then apply structured proximal maps."""

    parameters = initial.copy()
    if l1.shape != parameters.factor_weights.shape:
        raise ValueError("One L1 penalty is required per factor")
    covered = np.concatenate(
        [np.asarray(group.indices, dtype=np.int64) for group in groups]
    ) if groups else np.empty(0, dtype=np.int64)
    if covered.size != np.unique(covered).size:
        raise ValueError("Group penalties must be disjoint")
    _project_groups(parameters.factor_weights, groups)
    exact._center_nuisance(parameters)
    moments = {
        "register": np.zeros_like(parameters.register),
        "tonal": np.zeros_like(parameters.tonal),
        "factor_weights": np.zeros_like(parameters.factor_weights),
    }
    velocities = {key: np.zeros_like(value) for key, value in moments.items()}
    best = parameters.copy()
    best_validation = exact._nll(
        validation["chosen"],
        validation["voices"],
        validation["modes"],
        validation["tonics"],
        candidate_pitches,
        validation["factors"],
        parameters,
    )
    history = [
        {
            "step": 0,
            "train_nll": exact._nll(
                train["chosen"],
                train["voices"],
                train["modes"],
                train["tonics"],
                candidate_pitches,
                train["factors"],
                parameters,
            ),
            "validation_nll": best_validation,
            "group_norms": {
                group.name: float(
                    np.linalg.norm(parameters.factor_weights[group.indices])
                )
                for group in groups
            },
        }
    ]
    rows = np.arange(train["chosen"].size)
    relative = (candidate_pitches[None, :] - train["tonics"][:, None]) % 12
    voice_grid = np.broadcast_to(train["voices"][:, None], relative.shape)
    mode_grid = np.broadcast_to(train["modes"][:, None], relative.shape)

    for step in range(1, steps + 1):
        residuals = exact._probabilities(
            train["voices"],
            train["modes"],
            train["tonics"],
            candidate_pitches,
            train["factors"],
            parameters,
        )
        residuals[rows, train["chosen"]] -= 1.0
        register_gradient = np.zeros_like(parameters.register)
        np.add.at(register_gradient, train["voices"], residuals)
        register_gradient /= train["chosen"].size
        register_gradient += l2 * parameters.register
        tonal_gradient = np.zeros_like(parameters.tonal)
        np.add.at(
            tonal_gradient,
            (voice_grid, mode_grid, relative),
            residuals,
        )
        tonal_gradient /= train["chosen"].size
        tonal_gradient += l2 * parameters.tonal
        factor_gradient = (
            np.einsum(
                "ncr,nc->r",
                train["factors"],
                residuals,
                optimize=True,
            )
            / train["chosen"].size
        )
        factor_gradient += l2 * parameters.factor_weights
        gradients = {
            "register": register_gradient,
            "tonal": tonal_gradient,
            "factor_weights": factor_gradient,
        }
        for name, gradient in gradients.items():
            moments[name] = 0.9 * moments[name] + 0.1 * gradient
            velocities[name] = 0.999 * velocities[name] + 0.001 * gradient**2
            corrected_moment = moments[name] / (1.0 - 0.9**step)
            corrected_velocity = velocities[name] / (1.0 - 0.999**step)
            value = getattr(parameters, name)
            value -= learning_rate * corrected_moment / (
                np.sqrt(corrected_velocity) + 1e-8
            )
        parameters.factor_weights = sparse_group_prox(
            parameters.factor_weights,
            learning_rate=learning_rate,
            l1=l1,
            groups=groups,
        )
        exact._center_nuisance(parameters)
        if step == 1 or step % 10 == 0 or step == steps:
            train_nll = exact._nll(
                train["chosen"],
                train["voices"],
                train["modes"],
                train["tonics"],
                candidate_pitches,
                train["factors"],
                parameters,
            )
            validation_nll = exact._nll(
                validation["chosen"],
                validation["voices"],
                validation["modes"],
                validation["tonics"],
                candidate_pitches,
                validation["factors"],
                parameters,
            )
            group_norms = {
                group.name: float(
                    np.linalg.norm(parameters.factor_weights[group.indices])
                )
                for group in groups
            }
            history.append(
                {
                    "step": step,
                    "train_nll": train_nll,
                    "validation_nll": validation_nll,
                    "group_norms": group_norms,
                }
            )
            if validation_nll < best_validation:
                best_validation = validation_nll
                best = parameters.copy()
    returned = best if return_best_validation else parameters
    return returned, {
        "best_validation_nll": best_validation,
        "returned_checkpoint": (
            "best_validation" if return_best_validation else "terminal"
        ),
        "history": history,
    }
