"""Compile the frozen V5.16 factor catalogue into Snarky CHOICE weights.

The catalogue remains the probabilistic model.  This module is only its
execution bridge: it evaluates the K3 factors, forms the local log score, and
returns the positive weights expected by a Snarky ``CHOICE``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import k3
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
DEFAULT_CATALOGUE = (
    REPOSITORY
    / "harmonizer/bach_rule_induction/rule_bases/k3_clean/v5_16_factors.yaml"
)


@dataclass(frozen=True)
class CompiledFactor:
    """One canonical readable factor and its learned log contribution."""

    id: str
    feature: k3.FeatureSpec
    log_weight: float
    grounding: str


@dataclass(frozen=True)
class ChoiceEvaluation:
    """Candidate values ready to be exposed to a Snarky ``CHOICE``."""

    pitches: np.ndarray
    local_scores: np.ndarray
    positive_weights: np.ndarray
    probabilities: np.ndarray
    activations: np.ndarray


@dataclass(frozen=True)
class K3ChoiceProgram:
    """Frozen V5.16 baselines and canonical factors."""

    id: str
    candidate_min: int
    candidate_max: int
    register_logits: np.ndarray
    tonal_logits: np.ndarray
    factors: tuple[CompiledFactor, ...]

    @property
    def features(self) -> tuple[k3.FeatureSpec, ...]:
        return tuple(factor.feature for factor in self.factors)

    @property
    def weights(self) -> np.ndarray:
        return np.asarray(
            [factor.log_weight for factor in self.factors],
            dtype=np.float64,
        )

    def _register_slice(self, dataset: k3.K3Dataset) -> np.ndarray:
        start = dataset.candidate_min - self.candidate_min
        stop = dataset.candidate_max - self.candidate_min + 1
        if start < 0 or stop > self.register_logits.shape[1]:
            raise ValueError("K3 choice domain lies outside the learned pitch domain")
        return self.register_logits[:, start:stop]

    def evaluate(self, dataset: k3.K3Dataset) -> ChoiceEvaluation:
        """Evaluate all alternatives without changing the probabilistic model."""

        activations = k3.feature_matrix(dataset, self.features)
        base_scores = k3.contextual_base_scores(
            dataset,
            self._register_slice(dataset),
            self.tonal_logits,
        )
        local_scores = base_scores + np.tensordot(
            activations,
            self.weights,
            axes=([2], [0]),
        )
        shifted = local_scores - local_scores.max(axis=1, keepdims=True)
        positive_weights = np.exp(shifted)
        probabilities = positive_weights / positive_weights.sum(
            axis=1,
            keepdims=True,
        )
        return ChoiceEvaluation(
            pitches=dataset.candidate_pitches,
            local_scores=local_scores,
            positive_weights=positive_weights,
            probabilities=probabilities,
            activations=activations,
        )

    def explanations(
        self,
        dataset: k3.K3Dataset,
        evaluation: ChoiceEvaluation | None = None,
    ) -> list[list[dict[str, Any]]]:
        """Return the active readable factors and contributions per candidate."""

        result = self.evaluate(dataset) if evaluation is None else evaluation
        rows: list[list[dict[str, Any]]] = []
        for row in range(dataset.size):
            alternatives: list[dict[str, Any]] = []
            for candidate, pitch in enumerate(result.pitches):
                active = [
                    {
                        "factor_id": factor.id,
                        "label": factor.feature.label,
                        "log_contribution": factor.log_weight,
                    }
                    for index, factor in enumerate(self.factors)
                    if result.activations[row, candidate, index]
                ]
                alternatives.append(
                    {
                        "pitch": int(pitch),
                        "local_score": float(result.local_scores[row, candidate]),
                        "choice_weight": float(
                            result.positive_weights[row, candidate]
                        ),
                        "probability": float(result.probabilities[row, candidate]),
                        "active_factors": active,
                    }
                )
            rows.append(alternatives)
        return rows


def _source_model_path(catalogue_path: Path, source: str) -> Path:
    candidate = Path(source)
    if candidate.is_absolute():
        return candidate
    repository_candidate = REPOSITORY / candidate
    if repository_candidate.exists():
        return repository_candidate
    return catalogue_path.parent / candidate


def load_choice_program(
    catalogue_path: Path = DEFAULT_CATALOGUE,
) -> K3ChoiceProgram:
    """Load the canonical factors and their frozen empirical baselines."""

    raw = yaml.safe_load(catalogue_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("K3 factor catalogue must be a mapping")
    source_model = _source_model_path(catalogue_path, str(raw["source_model"]))
    payload = json.loads(source_model.read_text(encoding="utf-8"))
    model = payload["model"]
    corpus = payload["corpus"]
    factors = tuple(
        CompiledFactor(
            id=str(record["id"]),
            feature=k3.FeatureSpec.from_dict(record["feature"]),
            log_weight=float(record["parameter"]["log_weight"]),
            grounding=str(record["grounding"]),
        )
        for record in raw["factors"]
    )
    expected = int(raw["counts"]["canonical_factors_after_merge"])
    if len(factors) != expected:
        raise ValueError(
            f"Catalogue declares {expected} factors but contains {len(factors)}"
        )
    return K3ChoiceProgram(
        id=str(raw["id"]),
        candidate_min=int(corpus["candidate_min"]),
        candidate_max=int(corpus["candidate_max"]),
        register_logits=np.asarray(model["register_logits"], dtype=np.float64),
        tonal_logits=np.asarray(model["tonal_logits"], dtype=np.float64),
        factors=factors,
    )


def source_model_evaluation(
    dataset: k3.K3Dataset,
    catalogue_path: Path = DEFAULT_CATALOGUE,
) -> ChoiceEvaluation:
    """Evaluate the unmerged source terms for a semantic parity check."""

    raw = yaml.safe_load(catalogue_path.read_text(encoding="utf-8"))
    source_model = _source_model_path(catalogue_path, str(raw["source_model"]))
    payload = json.loads(source_model.read_text(encoding="utf-8"))
    model = payload["model"]
    corpus = payload["corpus"]
    candidate_min = int(corpus["candidate_min"])
    register = np.asarray(model["register_logits"], dtype=np.float64)
    start = dataset.candidate_min - candidate_min
    stop = dataset.candidate_max - candidate_min + 1
    base_scores = k3.contextual_base_scores(
        dataset,
        register[:, start:stop],
        np.asarray(model["tonal_logits"], dtype=np.float64),
    )
    features = tuple(k3.feature_from_model_record(rule) for rule in model["rules"])
    weights = np.asarray(
        [float(rule["weight"]) for rule in model["rules"]],
        dtype=np.float64,
    )
    activations = k3.feature_matrix(dataset, features)
    local_scores = base_scores + np.tensordot(
        activations,
        weights,
        axes=([2], [0]),
    )
    shifted = local_scores - local_scores.max(axis=1, keepdims=True)
    positive_weights = np.exp(shifted)
    return ChoiceEvaluation(
        pitches=dataset.candidate_pitches,
        local_scores=local_scores,
        positive_weights=positive_weights,
        probabilities=positive_weights
        / positive_weights.sum(axis=1, keepdims=True),
        activations=activations,
    )
