#!/usr/bin/env python3
"""Fit the compact V34 named-dissonance outcome model and budgets."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import fit_v31_cycle_conditional as intervals
import k3
import run_generative_moment_calibration as generative
import v34_harmony

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_OUTPUT = FACTOR_BASE / "v34_harmonic_budget_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V34_HARMONIC_BUDGET_MODEL.md"
DEFAULT_FACTORS = FACTOR_BASE / "v34_harmonic_resolution.factors"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--quantile", type=float, default=0.95)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--factors", type=Path, default=DEFAULT_FACTORS)
    return parser.parse_args()


def _binomial_quantile(trials: int, probability: float, quantile: float) -> int:
    if trials <= 0:
        return 0
    cumulative = 0.0
    for successes in range(trials + 1):
        cumulative += (
            math.comb(trials, successes)
            * probability**successes
            * (1.0 - probability) ** (trials - successes)
        )
        if cumulative >= quantile:
            return successes
    return trials


def _split_counts(piece_ids: list[str], scores: Path) -> dict[str, Any]:
    strong_opportunities = 0
    dissonant_named = 0
    dissonant_chains = 0
    outcomes = {"next_triad": 0, "next_named_dissonant": 0, "next_residual": 0}
    family_outcomes: dict[str, dict[str, int]] = {}
    for piece_id in piece_ids:
        lattice = k3.extract_piece_lattice(
            generative._score_path(scores, piece_id),
            piece_id,
        )
        strong_opportunities += max(
            int((lattice.metric_levels >= 2).sum()) - 1,
            0,
        )
        rows = v34_harmony.strong_transition_rows(lattice, lattice.blocks)
        dissonant_named += len(rows)
        for row in rows:
            raw = row["resolution_outcome"]
            outcome = (
                "next_triad"
                if raw.startswith("triad_")
                else raw
            )
            outcomes[outcome] += 1
            family_outcomes.setdefault(
                row["family"],
                {key: 0 for key in outcomes},
            )[outcome] += 1
            dissonant_chains += outcome == "next_named_dissonant"
    dissonant_rate = dissonant_named / strong_opportunities
    chain_rate = dissonant_chains / dissonant_named
    return {
        "pieces": len(piece_ids),
        "strong_transition_opportunities": strong_opportunities,
        "dissonant_named_transitions": dissonant_named,
        "dissonant_named_rate": dissonant_rate,
        "dissonant_named_wilson_95_interval": intervals._wilson(
            dissonant_named,
            strong_opportunities,
        ),
        "dissonant_to_dissonant_chains": dissonant_chains,
        "chain_given_dissonant_rate": chain_rate,
        "chain_wilson_95_interval": intervals._wilson(
            dissonant_chains,
            dissonant_named,
        ),
        "outcomes": outcomes,
        "family_outcomes": family_outcomes,
    }


def _multinomial_log_likelihood(counts: list[int]) -> float:
    total = sum(counts)
    return sum(count * math.log(count / total) for count in counts if count)


def _granularity(train: dict[str, Any]) -> dict[str, Any]:
    outcome_names = tuple(train["outcomes"])
    pooled_counts = [train["outcomes"][name] for name in outcome_names]
    pooled_ll = _multinomial_log_likelihood(pooled_counts)
    family_ll = sum(
        _multinomial_log_likelihood([counts[name] for name in outcome_names])
        for counts in train["family_outcomes"].values()
        if sum(counts.values())
    )
    observations = sum(pooled_counts)
    pooled_parameters = len(outcome_names) - 1
    populated_families = len(train["family_outcomes"])
    family_parameters = populated_families * (len(outcome_names) - 1)
    pooled_bic = pooled_parameters * math.log(observations) - 2.0 * pooled_ll
    family_bic = family_parameters * math.log(observations) - 2.0 * family_ll
    return {
        "outcome_names": list(outcome_names),
        "pooled_log_likelihood": pooled_ll,
        "family_log_likelihood": family_ll,
        "pooled_parameter_count": pooled_parameters,
        "family_parameter_count": family_parameters,
        "pooled_bic": pooled_bic,
        "family_bic": family_bic,
        "selected": (
            "pooled_outcome_model" if pooled_bic <= family_bic else "family_model"
        ),
    }


def _factor_text(factors: list[dict[str, Any]]) -> str:
    lines = [
        "# Generated from v34_harmonic_budget_model.json.",
        "FACTOR_GROUP named_dissonance_next_strong_outcome",
    ]
    for factor in factors:
        lines.extend(
            [
                f"    FACTOR {factor['id']}",
                "    SCOPE $scope",
                f"    LOG_WEIGHT {factor['log_weight']:.17g}",
                "    WHEN",
                f"        ($scope k3_factor_active {factor['id']})",
                "    END_FACTOR",
                "",
            ]
        )
    lines.extend(("END_FACTOR_GROUP", ""))
    return "\n".join(lines)


def _markdown(payload: dict[str, Any]) -> str:
    train = payload["corpus"]["train251"]
    validation = payload["corpus"]["validation50"]
    lines = [
        "# V34 — modèle compact de résolution et budgets harmoniques",
        "",
        "Le modèle observe chaque accord nommé dissonant sur un temps fort",
        "et classe le prochain temps fort en triade, autre accord nommé",
        "dissonant ou sonorité résiduelle. Le BIC choisit une distribution",
        "partagée plutôt qu'une table distincte par famille.",
        "",
        "## Estimation",
        "",
        f"- Train : `{train['dissonant_named_rate']:.6f}` d'accords nommés "
        "dissonants par transition forte.",
        f"- Validation : `{validation['dissonant_named_rate']:.6f}`.",
        f"- Train : `{train['chain_given_dissonant_rate']:.6f}` de chaînes "
        "dissonant→dissonant.",
        f"- Validation : `{validation['chain_given_dissonant_rate']:.6f}`.",
        f"- Confirmation : `{payload['confirmation']['confirmed']}`.",
        "",
        "## Budgets pour 25 transitions fortes",
        "",
        f"- Accords nommés dissonants : au plus "
        f"`{payload['example_budget_25']['maximum_dissonant_named']}`.",
        f"- Chaînes, conditionnellement à ce budget : au plus "
        f"`{payload['example_budget_25']['maximum_dissonant_chains']}`.",
        "",
        "Ces maxima sont des quantiles binomiaux appris, pas des",
        "interdictions musicologiques ajoutées à la main.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    split_ids = {
        "train251": sorted(splits["train"], key=generative._stable_order),
        "validation50": list(splits["validation"]),
        "test51": list(splits["test"]),
    }
    corpus = {
        split: _split_counts(piece_ids, args.scores)
        for split, piece_ids in split_ids.items()
    }
    train = corpus["train251"]
    validation = corpus["validation50"]
    granularity = _granularity(train)
    if granularity["selected"] != "pooled_outcome_model":
        raise RuntimeError("Frozen BIC rule did not select the compact model")
    dissonant_confirmed = (
        train["dissonant_named_wilson_95_interval"][0]
        <= validation["dissonant_named_rate"]
        <= train["dissonant_named_wilson_95_interval"][1]
    )
    chain_confirmed = (
        train["chain_wilson_95_interval"][0]
        <= validation["chain_given_dissonant_rate"]
        <= train["chain_wilson_95_interval"][1]
    )
    confirmed = dissonant_confirmed and chain_confirmed
    total_outcomes = sum(train["outcomes"].values())
    probabilities = {
        name: count / total_outcomes for name, count in train["outcomes"].items()
    }
    factors = [
        {
            "id": f"F-K3-V34-{name.upper().replace('_', '-')}",
            "outcome": name,
            "probability": probability,
            "log_weight": math.log(probability),
            "estimator": "categorical_mle",
            "human_authored": False,
            "feature_definition_human_authored": True,
        }
        for name, probability in probabilities.items()
    ]
    factors.append(
        {
            "id": "F-K3-V34-STRONG-NAMED-DISSONANT",
            "outcome": "strong_named_dissonant",
            "probability": train["dissonant_named_rate"],
            "log_weight": math.log(
                train["dissonant_named_rate"]
                / (1.0 - train["dissonant_named_rate"])
            ),
            "estimator": "binomial_mle_log_odds",
            "human_authored": False,
            "feature_definition_human_authored": True,
        }
    )
    maximum_dissonant = _binomial_quantile(
        25,
        train["dissonant_named_rate"],
        args.quantile,
    )
    maximum_chains = _binomial_quantile(
        maximum_dissonant,
        train["chain_given_dissonant_rate"],
        args.quantile,
    )
    payload = {
        "experiment": {
            "id": "K3-V34-HARMONIC-BUDGET-1",
            "status": "CONFIRMED" if confirmed else "REJECTED",
            "test_split_used_for_fit": False,
            "generated_piece_used_for_fit": False,
        },
        "definition": {
            "scope": "current strong beat and next strong beat",
            "current_domain": "deterministic named dissonant chord",
            "outcomes": list(probabilities),
        },
        "corpus": corpus,
        "granularity": granularity,
        "confirmation": {
            "rule": "validation rates lie inside train Wilson 95% intervals",
            "dissonant_rate_confirmed": dissonant_confirmed,
            "chain_rate_confirmed": chain_confirmed,
            "confirmed": confirmed,
            "ablation_interpretation": (
                "rates_lower_on_validation_than_train; train budgets are conservative"
            ),
        },
        "factors": factors,
        "budgets": {
            "quantile": args.quantile,
            "dissonant_named_probability": train["dissonant_named_rate"],
            "chain_given_dissonant_probability": train[
                "chain_given_dissonant_rate"
            ],
            "semantics": "binomial_upper_quantile",
        },
        "example_budget_25": {
            "strong_transition_opportunities": 25,
            "maximum_dissonant_named": maximum_dissonant,
            "maximum_dissonant_chains": maximum_chains,
        },
    }
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    args.factors.write_text(_factor_text(factors), encoding="utf-8")
    print(
        "[v34-harmonic-budget] "
        f"dissonant={train['dissonant_named_rate']:.6f}/"
        f"{validation['dissonant_named_rate']:.6f} "
        f"chain={train['chain_given_dissonant_rate']:.6f}/"
        f"{validation['chain_given_dissonant_rate']:.6f} "
        f"confirmed={confirmed} budget25={maximum_dissonant}/{maximum_chains}",
        flush=True,
    )
    print(f"[v34-harmonic-budget] wrote {args.output}", flush=True)
    print(f"[v34-harmonic-budget] wrote {args.report}", flush=True)
    print(f"[v34-harmonic-budget] wrote {args.factors}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
