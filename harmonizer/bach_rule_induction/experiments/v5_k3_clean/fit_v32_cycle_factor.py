#!/usr/bin/env python3
"""Confirm and refit the finite-state attacked-note cycle factor."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import fit_v31_cycle_conditional as v31
import k3
import run_generative_moment_calibration as generative
import run_induction as original

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_MANIFEST = (
    REPOSITORY / "harmonizer/bach_rule_induction/corpus/manifest.music21-3.1.0.json"
)
DEFAULT_ARCHIVE = (
    REPOSITORY.parent / "deepbach-reference/resources/cache/music21-3.1.0.tar.gz"
)
DEFAULT_OUTPUT = FACTOR_BASE / "v32_attack_cycle_factor_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V32_ATTACK_CYCLE_FACTOR_MODEL.md"
DEFAULT_FACTORS = FACTOR_BASE / "v32_attack_cycle_factor.factors"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--initial-pieces", type=int, default=32)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--factors", type=Path, default=DEFAULT_FACTORS)
    return parser.parse_args()


def _sum_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "lag2_returns": sum(int(row["lag2_returns"]) for row in rows),
        "continued_cycles": sum(int(row["continued_cycles"]) for row in rows),
    }


def _rate(row: dict[str, int]) -> float:
    return row["continued_cycles"] / row["lag2_returns"]


def _ll(row: dict[str, int], rate: float) -> float:
    return v31._bernoulli_log_likelihood(
        row["continued_cycles"],
        row["lag2_returns"],
        rate,
    )


def _candidate_granularities(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    by_voice = corpus["by_voice"]
    voice_rows = {name: by_voice[name] for name in k3.VOICE_NAMES[1:]}
    shared = _sum_rows(list(voice_rows.values()))
    inner = _sum_rows([voice_rows["Alto"], voice_rows["Tenor"]])
    candidates = [
        {
            "id": "shared_lower",
            "groups": (("lower", tuple(k3.VOICE_NAMES[1:]), shared),),
        },
        {
            "id": "inner_plus_bass",
            "groups": (
                ("inner", ("Alto", "Tenor"), inner),
                ("bass", ("Bass",), voice_rows["Bass"]),
            ),
        },
        {
            "id": "per_voice",
            "groups": tuple(
                (name.lower(), (name,), voice_rows[name])
                for name in k3.VOICE_NAMES[1:]
            ),
        },
    ]
    observations = shared["lag2_returns"]
    output = []
    for candidate in candidates:
        log_likelihood = sum(_ll(row, _rate(row)) for _, _, row in candidate["groups"])
        parameter_count = len(candidate["groups"])
        output.append(
            {
                "id": candidate["id"],
                "parameter_count": parameter_count,
                "log_likelihood": log_likelihood,
                "bic": parameter_count * math.log(observations)
                - 2.0 * log_likelihood,
                "groups": [
                    {
                        "id": group_id,
                        "voices": list(voices),
                        "lag2_returns": row["lag2_returns"],
                        "continued_cycles": row["continued_cycles"],
                        "probability": _rate(row),
                        "log_weight": math.log(_rate(row) / (1.0 - _rate(row))),
                    }
                    for group_id, voices, row in candidate["groups"]
                ],
            }
        )
    return output


def _factor_text(factors: list[dict[str, Any]]) -> str:
    lines = [
        "# Generated from v32_attack_cycle_factor_model.json.",
        "# Activation facts are pure finite-state observations over four attacks.",
        "FACTOR_GROUP attacked_two_note_cycle",
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
    lines.append("END_FACTOR_GROUP")
    lines.append("")
    return "\n".join(lines)


def _markdown(payload: dict[str, Any]) -> str:
    initial = payload["corpus"]["initial32"]["lower_voices_shared"]
    holdout = payload["corpus"]["holdout219"]["lower_voices_shared"]
    full = payload["corpus"]["full_train251"]["lower_voices_shared"]
    lines = [
        "# V32 — facteur séquentiel de cycle de deux notes",
        "",
        "V31 a rejeté la réplication exacte d'un taux ponctuel. V32 teste une",
        "hypothèse différente et préenregistrée avant de charger les 219",
        "chorals restants : parmi les retours `ABA`, prolonger `ABAB` doit",
        "rester rare (borne Wilson supérieure < 25 %) et le taux appris sur",
        "32 chorals doit mieux prédire le holdout qu'un Bernoulli neutre.",
        "",
        "## Confirmation",
        "",
        f"- Initial 32 : `{initial['continued_cycles']} / "
        f"{initial['lag2_returns']}` = "
        f"`{100 * initial['continuation_given_return']:.3f} %`.",
        f"- Holdout 219 : `{holdout['continued_cycles']} / "
        f"{holdout['lag2_returns']}` = "
        f"`{100 * holdout['continuation_given_return']:.3f} %`.",
        f"- Train complet 251 : `{full['continued_cycles']} / "
        f"{full['lag2_returns']}` = "
        f"`{100 * full['continuation_given_return']:.3f} %`.",
        f"- Verdict : `{payload['experiment']['status']}`.",
        "",
        "## Modèle parcimonieux",
        "",
        "La granularité choisie par BIC sur les 251 chorals est",
        f" `{payload['selection']['selected_granularity']}`.",
        "",
    ]
    for factor in payload["factors"]:
        lines.append(
            f"- `{factor['id']}` ({', '.join(factor['voices'])}) : "
            f"`p={factor['probability']:.6f}`, "
            f"`log_weight={factor['log_weight']:.6f}`."
        )
    lines.extend(
        [
            "",
            "Chaque facteur ne fait qu'ajouter son poids à l'alternative qui",
            "transformerait `... A B A` en `... A B A B`. Il n'interdit ni",
            "`ABA` ni `ABAB`, n'active aucune autre règle et ne lit que quatre",
            "attaques d'une seule voix.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    ordered_train = sorted(splits["train"], key=generative._stable_order)
    initial_ids = ordered_train[: args.initial_pieces]
    holdout_ids = ordered_train[args.initial_pieces :]

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    selected = set(ordered_train)
    pieces = [piece for piece in manifest["pieces"] if piece["id"] in selected]
    paths = original._materialize_scores(args.archive, pieces, args.scores)

    initial = v31._counts(initial_ids, paths)
    holdout = v31._counts(holdout_ids, paths)
    full = v31._counts(ordered_train, paths)
    initial_rate = initial["lower_voices_shared"]["continuation_given_return"]
    holdout_row = holdout["lower_voices_shared"]
    holdout_rate = holdout_row["continuation_given_return"]
    holdout_interval = holdout_row["wilson_95_interval"]
    learned_ll = _ll(holdout_row, initial_rate)
    neutral_ll = _ll(holdout_row, 0.5)
    confirmed = (
        holdout_interval[1] < 0.25
        and learned_ll > neutral_ll
        and initial_rate < 0.5
        and holdout_rate < 0.5
    )

    granularities = _candidate_granularities(full)
    selected_granularity = min(granularities, key=lambda row: row["bic"])
    factors = [
        {
            "id": f"F-K3-V32-CYCLE-{group['id'].upper()}",
            "group": "attacked_two_note_cycle",
            "voices": group["voices"],
            "probability": group["probability"],
            "log_weight": group["log_weight"],
            "estimator": "conditional_binomial_mle",
            "human_authored": False,
            "feature_definition_human_authored": True,
            "activation_has_side_effects": False,
        }
        for group in selected_granularity["groups"]
    ]
    payload = {
        "experiment": {
            "id": "K3-V32-ATTACK-CYCLE-FACTOR-1",
            "status": "CONFIRMED" if confirmed else "REJECTED",
            "hypothesis_source": "V29_GENERATIVE_FAILURE",
            "initial_training_pieces": len(initial_ids),
            "independent_holdout_pieces": len(holdout_ids),
            "test_split_used_for_fit": False,
        },
        "definition": {
            "activation_domain": "current attacked note is a lag-2 return",
            "positive_event": "return continues a pre-existing ABAB cycle",
            "history_attacks": 3,
            "scope": "one lower voice",
        },
        "corpus": {
            "initial32": initial,
            "holdout219": holdout,
            "full_train251": full,
        },
        "confirmation": {
            "frozen_rules": {
                "holdout_wilson_upper_below": 0.25,
                "heldout_log_likelihood_better_than_neutral": True,
                "same_negative_logit_direction": True,
            },
            "holdout_wilson_95_interval": holdout_interval,
            "heldout_log_likelihood_initial_rate": learned_ll,
            "heldout_log_likelihood_neutral_rate": neutral_ll,
            "confirmed": confirmed,
        },
        "selection": {
            "criterion": "minimum_bic_on_full_training_split",
            "candidates": granularities,
            "selected_granularity": selected_granularity["id"],
        },
        "factors": factors,
    }
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    args.factors.write_text(_factor_text(factors), encoding="utf-8")
    print(
        f"[v32-cycle] initial={initial_rate:.6f} holdout={holdout_rate:.6f} "
        f"confirmed={confirmed} selected={selected_granularity['id']}",
        flush=True,
    )
    print(f"[v32-cycle] wrote {args.output}", flush=True)
    print(f"[v32-cycle] wrote {args.report}", flush=True)
    print(f"[v32-cycle] wrote {args.factors}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
