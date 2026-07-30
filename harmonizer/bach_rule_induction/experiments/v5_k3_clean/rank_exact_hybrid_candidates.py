#!/usr/bin/env python3
"""Rank unselected exact columns before V16 generative admission tests."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_exact_factor_reinduction as exact_reinduction
import run_generative_moment_calibration as generative
import run_v6_factor_induction as v6

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_MODEL = FACTOR_BASE / "v13_exact_directed_metric_model.json"
DEFAULT_GRAMMAR = FACTOR_BASE / "grammar_v14_directed_metric_trajectory.yaml"
DEFAULT_CACHE = HERE / "work/k3-exact-v14-catalogue-32x10.npz"
DEFAULT_CONTEXT = HERE / "work/k3-train-validation-context-full.npz"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_OUTPUT = FACTOR_BASE / "v16_exact_candidate_shortlist.json"
DEFAULT_REPORT = FACTOR_BASE / "V16_EXACT_CANDIDATE_SHORTLIST.md"


def _rule_key(rule: dict[str, Any]) -> str:
    return k3.feature_from_model_record(rule).key


def rank_candidates(
    *,
    model_payload: dict[str, Any],
    catalogue: tuple[k3.FeatureSpec, ...],
    train: dict[str, np.ndarray],
    candidate_min: int,
    candidate_max: int,
    complexity_penalty: float,
    minimum_opportunities: int,
    minimum_piece_support: int,
    kind_prefix: str | None,
) -> list[tuple[int, exact_reinduction.ExactResidual]]:
    """Return admissible unselected residuals in deterministic score order."""

    model = model_payload["model"]
    catalogue_by_key = {feature.key: index for index, feature in enumerate(catalogue)}
    selected_indices = []
    selected_weights = []
    for rule in model["rules"]:
        key = _rule_key(rule)
        if key not in catalogue_by_key:
            raise ValueError(f"Selected model feature absent from catalogue: {key}")
        selected_indices.append(catalogue_by_key[key])
        selected_weights.append(float(rule["weight"]))
    if len(set(selected_indices)) != len(selected_indices):
        raise ValueError("Selected model contains duplicate feature keys")

    candidates = np.arange(candidate_min, candidate_max + 1, dtype=np.int16)
    selected_train = exact_reinduction._select_columns(train, selected_indices)
    probabilities = exact_reinduction._probabilities(
        selected_train["voices"],
        selected_train["modes"],
        selected_train["tonics"],
        candidates,
        selected_train["factors"],
        exact_reinduction.Parameters(
            np.asarray(model["register_logits"], dtype=np.float64),
            np.asarray(model["tonal_logits"], dtype=np.float64),
            np.asarray(selected_weights, dtype=np.float64),
        ),
    )
    residuals = exact_reinduction._residuals(
        train["chosen"],
        probabilities,
        train["factors"],
        train["piece_ids"],
        np.asarray([feature.complexity for feature in catalogue], dtype=np.float64),
        complexity_penalty=complexity_penalty,
    )
    selected_set = set(selected_indices)
    ranked = [
        (index, residual)
        for index, residual in enumerate(residuals)
        if index not in selected_set
        and residual is not None
        and residual.column_score > 0
        and residual.testable_opportunities >= minimum_opportunities
        and residual.piece_support >= minimum_piece_support
        and (
            kind_prefix is None
            or catalogue[index].kind.startswith(kind_prefix)
        )
    ]
    ranked.sort(
        key=lambda item: (
            -item[1].column_score,
            catalogue[item[0]].key,
        )
    )
    return ranked


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    lines = [
        "# V16 — présélection conditionnelle des candidats hybrides",
        "",
        "Cette étape ne sélectionne encore aucune nouvelle règle. Elle calcule le",
        "gradient conditionnel exact sous le modèle V13, exclut les facteurs déjà",
        "présents et produit le top-K qui devra ensuite passer le garde-fou",
        "génératif multigraine.",
        "",
        f"- Catalogue : `{experiment['catalogue_size']}` clauses.",
        f"- Facteurs déjà présents : `{experiment['selected_factor_count']}`.",
        (
            "- Candidats conditionnellement admissibles : "
            f"`{experiment['admissible_count']}`."
        ),
        f"- Candidats conservés : `{len(result['candidates'])}`.",
        f"- Test réservé chargé : `{str(experiment['test_loaded']).lower()}`.",
        "",
        "| Rang | Famille | Candidat | Score | Gradient | z | Occasions | Pièces |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for candidate in result["candidates"]:
        statistic = candidate["conditional"]
        lines.append(
            f"| {candidate['rank']} | `{candidate['family']}` | "
            f"`{candidate['feature']['label']}` | "
            f"{statistic['column_score']:+.6f} | "
            f"{statistic['gradient']:+.6f} | "
            f"{statistic['z_score']:+.2f} | "
            f"{statistic['testable_opportunities']} | "
            f"{statistic['piece_support']} |"
        )
    lines.extend(
        [
            "",
            "Aucun candidat de cette table n'est admis par ce seul classement.",
            "V16 doit maintenant mesurer, pour chacun, la covariance entre son",
            "activation et les dix diagnostics dans les mêmes chaînes persistantes.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--context-cache", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--complexity-penalty", type=float, default=1.0)
    parser.add_argument("--minimum-opportunities", type=int, default=100)
    parser.add_argument("--minimum-piece-support", type=int, default=10)
    parser.add_argument(
        "--kind-prefix",
        help="Optional feature-kind prefix; omitted means the complete grammar.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.top_k <= 0
        or args.complexity_penalty < 0
        or args.minimum_opportunities <= 0
        or args.minimum_piece_support <= 0
    ):
        raise ValueError("Invalid shortlist thresholds")
    model_payload = json.loads(args.model.read_text(encoding="utf-8"))
    grammar = exact_reinduction._load_grammar(args.grammar)
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    context = k3.load_k3_dataset(args.context_cache)
    train_ids = sorted(splits["train"], key=generative._stable_order)
    context_train = k3.subset_for_piece_ids(context, train_ids).with_domain(
        int(model_payload["corpus"]["candidate_min"]),
        int(model_payload["corpus"]["candidate_max"]),
    )
    catalogue = v6._catalogue(context_train, grammar)
    family_by_kind = v6._feature_family_map(grammar)

    archive = np.load(args.cache)
    metadata = json.loads(str(archive["metadata"]))
    expected_keys = [feature.key for feature in catalogue]
    if metadata["feature_keys"] != expected_keys:
        raise ValueError("Cache feature order differs from the requested grammar")
    train = {
        "factors": archive["train_factors"],
        "chosen": archive["train_chosen"],
        "piece_ids": archive["train_piece_ids"],
        "voices": archive["train_voices"],
        "modes": archive["train_modes"],
        "tonics": archive["train_tonics"],
    }
    ranked = rank_candidates(
        model_payload=model_payload,
        catalogue=catalogue,
        train=train,
        candidate_min=int(model_payload["corpus"]["candidate_min"]),
        candidate_max=int(model_payload["corpus"]["candidate_max"]),
        complexity_penalty=args.complexity_penalty,
        minimum_opportunities=args.minimum_opportunities,
        minimum_piece_support=args.minimum_piece_support,
        kind_prefix=args.kind_prefix,
    )
    result = {
        "experiment": {
            "id": "F-K3-V16-EXACT-CANDIDATE-SHORTLIST",
            "status": "CONDITIONAL_SHORTLIST_PENDING_GENERATIVE_ADMISSION",
            "source_model": str(args.model.resolve()),
            "grammar": str(args.grammar.resolve()),
            "cache": str(args.cache.resolve()),
            "catalogue_size": len(catalogue),
            "selected_factor_count": len(model_payload["model"]["rules"]),
            "admissible_count": len(ranked),
            "top_k": args.top_k,
            "kind_prefix": args.kind_prefix,
            "complexity_penalty": args.complexity_penalty,
            "minimum_opportunities": args.minimum_opportunities,
            "minimum_piece_support": args.minimum_piece_support,
            "structure_train_piece_count": len(
                set(str(value) for value in train["piece_ids"])
            ),
            "test_loaded": False,
        },
        "candidates": [
            {
                "rank": rank,
                "catalogue_index": index,
                "family": family_by_kind[catalogue[index].kind],
                "feature": catalogue[index].to_dict(),
                "conditional": asdict(statistic),
                "generative_admission": "PENDING",
            }
            for rank, (index, statistic) in enumerate(
                ranked[: args.top_k],
                start=1,
            )
        ],
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v16-shortlist] wrote {args.output}", flush=True)
    print(f"[v16-shortlist] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
