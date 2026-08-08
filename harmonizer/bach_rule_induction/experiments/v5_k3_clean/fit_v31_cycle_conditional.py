#!/usr/bin/env python3
"""Fit and independently confirm the V31 attacked-note cycle factor."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

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
DEFAULT_OUTPUT = FACTOR_BASE / "v31_attack_cycle_conditional_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V31_ATTACK_CYCLE_CONDITIONAL_MODEL.md"
DEFAULT_FACTORS = FACTOR_BASE / "v31_attack_cycle_conditional.factors"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--train-pieces", type=int, default=32)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--factors", type=Path, default=DEFAULT_FACTORS)
    return parser.parse_args()


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
    if trials == 0:
        return [0.0, 1.0]
    rate = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (rate + z * z / (2.0 * trials)) / denominator
    radius = (
        z
        * math.sqrt(
            rate * (1.0 - rate) / trials + z * z / (4.0 * trials * trials)
        )
        / denominator
    )
    return [centre - radius, centre + radius]


def _counts(
    piece_ids: list[str],
    score_paths: dict[str, Path],
) -> dict[str, Any]:
    by_voice = {
        name: {"lag2_returns": 0, "continued_cycles": 0}
        for name in k3.VOICE_NAMES
    }
    for piece_id in piece_ids:
        lattice = k3.extract_piece_lattice(
            score_paths[piece_id],
            piece_id,
        )
        for voice, name in enumerate(k3.VOICE_NAMES):
            counts = k3.two_note_cycle_counts(
                k3.attacked_pitch_sequence(
                    lattice.blocks,
                    lattice.attacks,
                    voice,
                )
            )
            by_voice[name]["lag2_returns"] += counts["lag2_returns"]
            by_voice[name]["continued_cycles"] += counts["continued_cycles"]
    for row in by_voice.values():
        returns = row["lag2_returns"]
        continued = row["continued_cycles"]
        row["continuation_given_return"] = continued / returns
        row["wilson_95_interval"] = _wilson(continued, returns)
    lower_returns = sum(
        by_voice[name]["lag2_returns"] for name in k3.VOICE_NAMES[1:]
    )
    lower_continued = sum(
        by_voice[name]["continued_cycles"] for name in k3.VOICE_NAMES[1:]
    )
    lower_rate = lower_continued / lower_returns
    return {
        "pieces": len(piece_ids),
        "by_voice": by_voice,
        "lower_voices_shared": {
            "lag2_returns": lower_returns,
            "continued_cycles": lower_continued,
            "continuation_given_return": lower_rate,
            "wilson_95_interval": _wilson(lower_continued, lower_returns),
        },
    }


def _bernoulli_log_likelihood(successes: int, trials: int, rate: float) -> float:
    return successes * math.log(rate) + (trials - successes) * math.log1p(-rate)


def _training_granularity(train: dict[str, Any]) -> dict[str, Any]:
    shared = train["lower_voices_shared"]
    shared_rate = shared["continuation_given_return"]
    shared_ll = _bernoulli_log_likelihood(
        shared["continued_cycles"],
        shared["lag2_returns"],
        shared_rate,
    )
    voice_ll = 0.0
    for name in k3.VOICE_NAMES[1:]:
        row = train["by_voice"][name]
        voice_ll += _bernoulli_log_likelihood(
            row["continued_cycles"],
            row["lag2_returns"],
            row["continuation_given_return"],
        )
    observations = shared["lag2_returns"]
    shared_bic = math.log(observations) - 2.0 * shared_ll
    voice_bic = 3.0 * math.log(observations) - 2.0 * voice_ll
    return {
        "shared_log_likelihood": shared_ll,
        "voice_specific_log_likelihood": voice_ll,
        "shared_bic": shared_bic,
        "voice_specific_bic": voice_bic,
        "selected": "shared_lower_voice_factor"
        if shared_bic <= voice_bic
        else "voice_specific_factors",
    }


def _markdown(payload: dict[str, Any]) -> str:
    train = payload["corpus"]["train32"]["lower_voices_shared"]
    test = payload["corpus"]["test51"]["lower_voices_shared"]
    factor = payload["factor"]
    confirmation = payload["confirmation"]
    lines = [
        "# V31 — facteur conditionnel de continuation ABAB",
        "",
        "Le domaine d'activation est limité aux retours à retard 2. Le facteur",
        "demande alors si le retour courant prolonge un cycle déjà commencé :",
        "`... A B A -> B`. Les autres choix ne font pas partie de ce petit",
        "modèle conditionnel.",
        "",
        "## Estimation",
        "",
        f"- Train (32 chorals) : `{train['continued_cycles']} / "
        f"{train['lag2_returns']}` = "
        f"`{100 * train['continuation_given_return']:.3f} %`.",
        f"- Test intact (51 chorals) : `{test['continued_cycles']} / "
        f"{test['lag2_returns']}` = "
        f"`{100 * test['continuation_given_return']:.3f} %`.",
        f"- Poids log-odds MLE : `{factor['log_weight']:.6f}`.",
        f"- Granularité retenue par BIC sur train : "
        f"`{payload['training_granularity']['selected']}`.",
        f"- Confirmation indépendante : `{confirmation['confirmed']}`.",
        "",
        "## Interprétation déclarative",
        "",
        "Ce n'est pas une interdiction de `ABA` ni de `ABAB`. Quand une",
        "alternative prolongerait `ABAB`, Snarky active exactement un facteur",
        "négatif. Sa portée est une voix et quatre attaques successives ; il",
        "n'active aucune autre règle.",
        "",
        "Le test K3 général tenté auparavant reste rejeté selon son protocole",
        "de sélection. Ce facteur-ci est un modèle conditionnel distinct,",
        "normalisé seulement sur le domaine rare qu'il décrit.",
        "",
    ]
    return "\n".join(lines)


def _factor_text(weight: float) -> str:
    return f"""# Generated from v31_attack_cycle_conditional_model.json.
# The activation fact is a pure finite-state observation over four attacks.
FACTOR_GROUP attacked_two_note_cycle
    FACTOR F-K3-V31-ATTACK-CYCLE-CONTINUATION
    SCOPE $scope
    LOG_WEIGHT {weight:.17g}
    WHEN
        ($scope k3_factor_active F-K3-V31-ATTACK-CYCLE-CONTINUATION)
    END_FACTOR
END_FACTOR_GROUP
"""


def main() -> int:
    args = parse_args()
    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)[
        : args.train_pieces
    ]
    test_ids = list(splits["test"])
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    selected_ids = set((*train_ids, *test_ids))
    selected_pieces = [
        piece
        for piece in manifest["pieces"]
        if piece["id"] in selected_ids
    ]
    score_paths = original._materialize_scores(
        args.archive,
        selected_pieces,
        args.scores,
    )
    train = _counts(train_ids, score_paths)
    test = _counts(test_ids, score_paths)
    granularity = _training_granularity(train)
    if granularity["selected"] != "shared_lower_voice_factor":
        raise RuntimeError("The frozen BIC rule did not select the shared factor")
    train_row = train["lower_voices_shared"]
    test_row = test["lower_voices_shared"]
    rate = train_row["continuation_given_return"]
    log_weight = math.log(rate / (1.0 - rate))
    interval = train_row["wilson_95_interval"]
    test_rate = test_row["continuation_given_return"]
    confirmed = interval[0] <= test_rate <= interval[1]
    payload = {
        "experiment": {
            "id": "K3-V31-ATTACK-CYCLE-CONDITIONAL-1",
            "status": "CONFIRMED" if confirmed else "REJECTED",
            "hypothesis_source": "V29_GENERATIVE_FAILURE",
            "training_pieces": len(train_ids),
            "test_pieces": len(test_ids),
            "validation_reused_for_fit": False,
            "test_loaded": True,
        },
        "definition": {
            "activation_domain": "current attacked note is a lag-2 return",
            "positive_event": "return continues a pre-existing ABAB cycle",
            "history_attacks": 3,
            "scope": "one lower voice",
        },
        "corpus": {"train32": train, "test51": test},
        "training_granularity": granularity,
        "confirmation": {
            "rule": "test shared rate lies inside train Wilson 95% interval",
            "train_interval": interval,
            "test_rate": test_rate,
            "confirmed": confirmed,
        },
        "factor": {
            "id": "F-K3-V31-ATTACK-CYCLE-CONTINUATION",
            "group": "attacked_two_note_cycle",
            "estimator": "conditional_binomial_mle",
            "probability": rate,
            "log_weight": log_weight,
            "human_authored": False,
            "feature_definition_human_authored": True,
            "activation_has_side_effects": False,
        },
    }
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    args.factors.write_text(_factor_text(log_weight), encoding="utf-8")
    print(
        f"[v31-cycle-conditional] train={rate:.6f} test={test_rate:.6f} "
        f"weight={log_weight:.6f} confirmed={confirmed}",
        flush=True,
    )
    print(f"[v31-cycle-conditional] wrote {args.output}", flush=True)
    print(f"[v31-cycle-conditional] wrote {args.report}", flush=True)
    print(f"[v31-cycle-conditional] wrote {args.factors}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
