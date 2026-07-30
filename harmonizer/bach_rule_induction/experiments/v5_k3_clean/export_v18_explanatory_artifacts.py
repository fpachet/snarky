#!/usr/bin/env python3
"""Export V18 RuleCards and a pure Snarky FACTOR program."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import run_exact_factor_reinduction as exact
import yaml
from export_v5_16_factor_program import render_factor_program

from snarky import parse_factor_groups

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
RULES_DIRECTORY = REPOSITORY / "harmonizer/bach_rule_induction/rules/v18_unanimous"
DEFAULT_MODEL = FACTOR_BASE / "v18_unanimous_full_model.json"
DEFAULT_CACHE = HERE / "work/k3-exact-v18-unanimous-full.npz"
DEFAULT_CATALOGUE = FACTOR_BASE / "v18_unanimous_full_factors.yaml"
DEFAULT_PROGRAM = FACTOR_BASE / "v18_unanimous_full.factors"
DEFAULT_MANIFEST = RULES_DIRECTORY / "manifest.yaml"
VOICE_NAMES = ("soprano", "alto", "tenor", "bass")


def _dataset(archive: Any, name: str) -> dict[str, np.ndarray]:
    return {
        "factors": archive[f"{name}_factors"],
        "chosen": archive[f"{name}_chosen"],
        "piece_ids": archive[f"{name}_piece_ids"],
        "voices": archive[f"{name}_voices"],
        "modes": archive[f"{name}_modes"],
        "tonics": archive[f"{name}_tonics"],
    }


def _decision_ordinals(piece_ids: np.ndarray) -> np.ndarray:
    counts: dict[str, int] = {}
    ordinals = np.zeros(piece_ids.size, dtype=np.int32)
    for index, piece in enumerate(piece_ids):
        key = str(piece)
        ordinals[index] = counts.get(key, 0)
        counts[key] = int(ordinals[index]) + 1
    return ordinals


def _examples(
    data: dict[str, np.ndarray],
    feature_index: int,
    *,
    candidate_min: int,
    activated: bool,
    limit: int = 3,
) -> list[dict[str, Any]]:
    rows = np.arange(data["chosen"].size)
    column = data["factors"][:, :, feature_index]
    chosen = column[rows, data["chosen"]]
    testable = np.ptp(column, axis=1) > 0
    mask = testable & ((chosen > 0) if activated else (chosen == 0))
    ordinals = _decision_ordinals(data["piece_ids"])
    candidates = np.flatnonzero(mask)
    if activated:
        candidates = candidates[np.argsort(-chosen[candidates], kind="stable")]
    records = []
    seen_pieces: set[str] = set()
    for row in candidates:
        piece = str(data["piece_ids"][row])
        if piece in seen_pieces:
            continue
        seen_pieces.add(piece)
        records.append(
            {
                "piece": piece,
                "decision_ordinal": int(ordinals[row]),
                "voice": VOICE_NAMES[int(data["voices"][row])],
                "chosen_midi": candidate_min + int(data["chosen"][row]),
                "chosen_activation_count": int(chosen[row]),
                "maximum_alternative_activation_count": int(column[row].max()),
            }
        )
        if len(records) >= limit:
            break
    return records


def _statistics(
    data: dict[str, np.ndarray],
    probabilities: np.ndarray,
    feature_index: int,
    statistic: exact.ExactResidual,
) -> dict[str, Any]:
    rows = np.arange(data["chosen"].size)
    column = data["factors"][:, :, feature_index].astype(np.float64)
    chosen = column[rows, data["chosen"]]
    expected = np.einsum("nc,nc->n", probabilities, column, optimize=True)
    testable = np.ptp(column, axis=1) > 0
    return {
        "pieces": int(np.unique(data["piece_ids"]).size),
        "decisions": int(data["chosen"].size),
        "testable_opportunities": int(testable.sum()),
        "piece_support": statistic.piece_support,
        "observed_mean_on_testable": float(chosen[testable].mean()),
        "model_expected_mean_on_testable": float(expected[testable].mean()),
        "postfit_residual_gradient": statistic.gradient,
        "postfit_residual_z": statistic.z_score,
    }


def _rule_card(
    rule: dict[str, Any],
    index: int,
    train_statistics: dict[str, Any],
    validation_statistics: dict[str, Any],
    bach_examples: list[dict[str, Any]],
    exceptions: list[dict[str, Any]],
    *,
    card_prefix: str,
    model_name: str,
    factor_program: str,
    factor_group: str,
) -> dict[str, Any]:
    prefer = float(rule["weight"]) > 0
    rule_id = f"{card_prefix}-{index:03d}"
    return {
        "schema_version": 1,
        "id": rule_id,
        "title": rule["clause"],
        "lifecycle": "SUPPORTED_PRETEST",
        "status": "PREFER" if prefer else "AVOID",
        "statement": rule["clause"],
        "scope": {
            "voices": "SATB",
            "window": ["previous", "current", "following"],
            "attack_hold_semantics": True,
            "corpus": "music21-3.1.0-deepbach-352",
            "split": "variant-safe-251-50-51",
        },
        "normalized_feature": rule["feature"],
        "conclusion": {
            "kind": "prefer" if prefer else "avoid",
            "log_weight": float(rule["weight"]),
            "absolute_prohibition": False,
        },
        "selection": {
            "complete_reinductions": 5,
            "selected_in": int(rule["structure_selection_count"]),
            "unanimous": True,
            "calls_other_rules": False,
        },
        "statistics": {
            "train": train_statistics,
            "validation": validation_statistics,
            "test": {"opened": False},
        },
        "provenance": {
            "model": model_name,
            "origin": "learned_from_bach_corpus",
            "human_authored": False,
            "preference_human_authored": False,
            "feature_definition_human_authored": bool(
                rule.get("feature_definition_human_authored", False)
            ),
            "historical_rules_loaded": False,
        },
        "snarky_factor": {
            "file": factor_program,
            "factor_group": factor_group,
            "factor_id": rule["id"],
        },
        "bach_examples": bach_examples,
        "validation_exceptions": exceptions,
        "deepbach_counterexamples": [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--program", type=Path, default=DEFAULT_PROGRAM)
    parser.add_argument("--rules-directory", type=Path, default=RULES_DIRECTORY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--card-prefix", default="R-LEARNED-V18")
    parser.add_argument("--catalogue-id", default="K3-V18-UNANIMOUS")
    parser.add_argument("--factor-group", default="k3_v18_unanimous")
    parser.add_argument("--manifest-id", default="S-LEARNED-V18-UNANIMOUS")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model = json.loads(args.model.read_text(encoding="utf-8"))
    rules = model["model"]["rules"]
    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    expected_keys = [rule["feature"]["key"] for rule in rules]
    if metadata["feature_keys"] != expected_keys:
        raise ValueError("Model and exact full cache disagree")
    train = _dataset(archive, "train")
    validation = _dataset(archive, "validation")
    candidates = np.arange(
        int(metadata["candidate_min"]),
        int(metadata["candidate_max"]) + 1,
        dtype=np.int16,
    )
    parameters = exact.Parameters(
        np.asarray(model["model"]["register_logits"], dtype=np.float64),
        np.asarray(model["model"]["tonal_logits"], dtype=np.float64),
        np.asarray([rule["weight"] for rule in rules], dtype=np.float64),
    )
    train_probabilities = exact._probabilities(
        train["voices"],
        train["modes"],
        train["tonics"],
        candidates,
        train["factors"],
        parameters,
    )
    validation_probabilities = exact._probabilities(
        validation["voices"],
        validation["modes"],
        validation["tonics"],
        candidates,
        validation["factors"],
        parameters,
    )
    complexities = np.asarray(
        [rule["feature"]["complexity"] for rule in rules],
        dtype=np.float64,
    )
    train_residuals = exact._residuals(
        train["chosen"],
        train_probabilities,
        train["factors"],
        train["piece_ids"],
        complexities,
        complexity_penalty=0.0,
    )
    validation_residuals = exact._residuals(
        validation["chosen"],
        validation_probabilities,
        validation["factors"],
        validation["piece_ids"],
        complexities,
        complexity_penalty=0.0,
    )
    args.rules_directory.mkdir(parents=True, exist_ok=True)
    card_paths = []
    for index, rule in enumerate(rules, start=1):
        train_statistic = train_residuals[index - 1]
        validation_statistic = validation_residuals[index - 1]
        if train_statistic is None or validation_statistic is None:
            raise ValueError(f"Untestable V18 core factor: {rule['id']}")
        prefer = float(rule["weight"]) > 0
        card = _rule_card(
            rule,
            index,
            _statistics(
                train,
                train_probabilities,
                index - 1,
                train_statistic,
            ),
            _statistics(
                validation,
                validation_probabilities,
                index - 1,
                validation_statistic,
            ),
            _examples(
                train,
                index - 1,
                candidate_min=int(metadata["candidate_min"]),
                activated=prefer,
            ),
            _examples(
                validation,
                index - 1,
                candidate_min=int(metadata["candidate_min"]),
                activated=not prefer,
            ),
            card_prefix=args.card_prefix,
            model_name=args.model.name,
            factor_program=(
                f"../../factor_bases/k3_v6_induced/{args.program.name}"
            ),
            factor_group=args.factor_group,
        )
        card_path = args.rules_directory / f"{card['id']}.yaml"
        card_path.write_text(
            yaml.safe_dump(card, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        card_paths.append(card_path)

    factors = [
        {
            "id": rule["id"],
            "family": rule["family"],
            "feature": rule["feature"],
            "parameter": {
                "scale": "log_energy_contribution",
                "log_weight": float(rule["weight"]),
                "sign": rule["polarity"],
            },
            "selection": {
                "complete_reinductions": 5,
                "selected_in": int(rule["structure_selection_count"]),
                "unanimous": True,
            },
            "origin": "learned_from_bach_corpus",
            "human_authored": False,
            "preference_human_authored": False,
            "feature_definition_human_authored": bool(
                rule.get("feature_definition_human_authored", False)
            ),
            "grounding": "k3_feature_evaluator",
        }
        for rule in rules
    ]
    catalogue = {
        "schema_version": 1,
        "id": args.catalogue_id,
        "model_id": model["experiment"]["id"],
        "source_model": str(args.model.resolve()),
        "factor_group": args.factor_group,
        "status": "FROZEN_EXPLANATORY_PRETEST",
        "counts": {"canonical_factors_after_merge": len(factors)},
        "factors": factors,
    }
    args.catalogue.write_text(
        yaml.safe_dump(catalogue, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    program = render_factor_program(
        catalogue,
        group_name=args.factor_group,
        source_label=args.catalogue.name,
    )
    (group,) = parse_factor_groups(program)
    if len(group.factors) != len(factors):
        raise ValueError("Factor program lost factors during parsing")
    args.program.write_text(program, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "id": args.manifest_id,
        "status": "SUPPORTED_PRETEST",
        "model": str(args.model.resolve()),
        "factor_program": str(args.program.resolve()),
        "rule_cards": [path.name for path in card_paths],
        "test_opened": False,
    }
    args.manifest.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"[v18-export] wrote {len(card_paths)} RuleCards", flush=True)
    print(f"[v18-export] wrote {args.catalogue}", flush=True)
    print(f"[v18-export] wrote {args.program}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
