#!/usr/bin/env python3
"""Add the V16 Pareto-admitted factor and refit exact joint pseudolikelihood."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_exact_factor_reinduction as exact_reinduction
import run_generative_moment_calibration as generative

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SOURCE = FACTOR_BASE / "v13_exact_directed_metric_model.json"
DEFAULT_ADMISSION = FACTOR_BASE / "v16_candidate_admission.json"
DEFAULT_SPLITS = (
    HERE.parent / "differentiable_rules_poc/results/splits.variant-safe.json"
)
DEFAULT_SCORES = HERE / "work/scores"
DEFAULT_CACHE = HERE / "work/k3-exact-v16-selected-full.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "v16_exact_hybrid_iteration1_model.json"
DEFAULT_REPORT = FACTOR_BASE / "V16_EXACT_HYBRID_ITERATION1_MODEL.md"


def _markdown(result: dict[str, Any]) -> str:
    experiment = result["experiment"]
    model = result["model"]
    admitted = experiment["admitted_candidate"]
    frozen = experiment["existing_parameters_frozen"]
    lines = [
        (
            "# V16-local — petit pas admis sans réajustement"
            if frozen
            else "# V16.1 — réajustement exact après admission hybride"
        ),
        "",
        "Une seule clause a franchi successivement le classement conditionnel et",
        "le garde-fou génératif multigraine.",
        (
            "Elle est ajoutée au modèle V13 au petit pas proposé ; les 30 poids, "
            "le registre et le profil tonal de V13 restent strictement gelés."
            if frozen
            else (
                "Elle est ajoutée au modèle V13, puis les 31 poids, le registre "
                "et le profil tonal sont réajustés conjointement sur les mondes "
                "Gibbs exacts."
            )
        ),
        "",
        f"- Clause admise : `{admitted['feature']['label']}`.",
        f"- Pas local proposé : `{admitted['proposed_weight_step']:+.6f}`.",
        (
            "- Échelle du pas local : "
            f"`{experiment['local_step_scale']:.6f}`."
        ),
        (
            "- Poids appliqué/réajusté : "
            f"`{model['rules'][-1]['weight']:+.6f}`."
        ),
        f"- NLL source : `{experiment['source_validation_nll']:.6f}`.",
        f"- NLL candidate : `{model['validation_nll']:.6f}`.",
        f"- Facteurs : `{len(model['rules'])}`.",
        f"- Test réservé chargé : `{str(experiment['test_loaded']).lower()}`.",
        "",
        "Ce fichier est un candidat conditionnel. Sa promotion exige encore les",
        "audits génératifs appariés à horizon court et long.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--admission", type=Path, default=DEFAULT_ADMISSION)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument("--l1", type=float, default=0.0005)
    parser.add_argument("--l2", type=float, default=0.001)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--freeze-existing-parameters",
        action="store_true",
        help=(
            "Keep every V13 parameter fixed and apply only the admitted local "
            "candidate step."
        ),
    )
    parser.add_argument(
        "--local-step-scale",
        type=float,
        default=1.0,
        help="Dyadic scale applied to the admitted step in frozen mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.steps <= 0
        or args.learning_rate <= 0
        or args.l1 < 0
        or args.l2 < 0
        or args.workers <= 0
        or not 0 < args.local_step_scale <= 1
    ):
        raise ValueError("Invalid exact-refit parameters")
    source = json.loads(args.source.read_text(encoding="utf-8"))
    admission = json.loads(args.admission.read_text(encoding="utf-8"))
    proposed = admission["proposed_candidate"]
    if (
        admission["experiment"]["test_loaded"]
        or proposed is None
        or not proposed["admitted"]
    ):
        raise ValueError("Admission payload contains no admissible proposal")

    source_features = tuple(
        k3.feature_from_model_record(rule) for rule in source["model"]["rules"]
    )
    admitted_feature = k3.feature_from_model_record(proposed["feature"])
    if admitted_feature.key in {feature.key for feature in source_features}:
        raise ValueError("Admitted feature is already present in the source model")
    features = (*source_features, admitted_feature)

    split_payload = json.loads(args.splits.read_text(encoding="utf-8"))
    splits = split_payload.get("grouped_split", split_payload)
    train_ids = sorted(splits["train"], key=generative._stable_order)
    validation_ids = list(splits["validation"])
    corpus = source["corpus"]
    candidate_min = int(corpus["candidate_min"])
    candidate_max = int(corpus["candidate_max"])
    register = np.asarray(source["model"]["register_logits"], dtype=np.float64)
    tonal = np.asarray(source["model"]["tonal_logits"], dtype=np.float64)
    metadata = {
        "schema_version": 1,
        "scope": "exact_gibbs_attack_hold_worlds",
        "train_ids": train_ids,
        "validation_ids": validation_ids,
        "feature_keys": [feature.key for feature in features],
        "candidate_min": candidate_min,
        "candidate_max": candidate_max,
    }
    train, validation = exact_reinduction._load_or_build(
        args.cache,
        metadata=metadata,
        train_ids=train_ids,
        validation_ids=validation_ids,
        scores=args.scores,
        features=features,
        register=register,
        tonal=tonal,
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        workers=args.workers,
    )
    admitted_initial_weight = float(proposed["proposed_weight_step"])
    if args.freeze_existing_parameters:
        admitted_initial_weight *= args.local_step_scale
    initial_weights = np.asarray(
        [float(rule["weight"]) for rule in source["model"]["rules"]]
        + [admitted_initial_weight],
        dtype=np.float64,
    )
    candidates = np.arange(candidate_min, candidate_max + 1, dtype=np.int16)
    initial = exact_reinduction.Parameters(register, tonal, initial_weights)
    if args.freeze_existing_parameters:
        fitted = initial.copy()
        fit = {
            "mode": "local_step_without_refit",
            "best_validation_nll": exact_reinduction._nll(
                validation["chosen"],
                validation["voices"],
                validation["modes"],
                validation["tonics"],
                candidates,
                validation["factors"],
                fitted,
            ),
            "history": [],
        }
    else:
        fitted, fit = exact_reinduction._fit(
            train,
            validation,
            candidates,
            initial,
            steps=args.steps,
            learning_rate=args.learning_rate,
            l1=args.l1,
            l2=args.l2,
        )
    rules = [
        {
            **rule,
            "weight": float(weight),
        }
        for rule, weight in zip(
            source["model"]["rules"],
            fitted.factor_weights[:-1],
            strict=True,
        )
    ]
    rules.append(
        {
            "family": proposed["family"],
            "feature": proposed["feature"],
            "selection": {
                **next(
                    candidate["conditional"]
                    for candidate in json.loads(
                        Path(admission["experiment"]["shortlist"]).read_text(
                            encoding="utf-8"
                        )
                    )["candidates"]
                    if candidate["rank"] == proposed["rank"]
                ),
                "hybrid_admission": {
                    key: value
                    for key, value in proposed.items()
                    if key not in {"feature", "family"}
                },
            },
            "weight": float(fitted.factor_weights[-1]),
        }
    )
    result = {
        "experiment": {
            "id": (
                "F-K3-V16-EXACT-LOCAL-STEP"
                if args.freeze_existing_parameters
                else "F-K3-V16-EXACT-HYBRID-ITERATION1"
            ),
            "title": (
                "V16-local — facteur admis au petit pas sans réajustement"
                if args.freeze_existing_parameters
                else "V16.1 — facteur admis par Pareto puis réajustement exact"
            ),
            "status": (
                "EXACT_LOCAL_STEP_CANDIDATE_PENDING_GENERATION_AUDIT"
                if args.freeze_existing_parameters
                else (
                    "EXACT_HYBRID_STRUCTURE_CANDIDATE_"
                    "PENDING_GENERATION_AUDIT"
                )
            ),
            "source_model": str(args.source.resolve()),
            "source_validation_nll": float(source["model"]["validation_nll"]),
            "admission": str(args.admission.resolve()),
            "admitted_candidate": proposed,
            "factor_structure_changed": True,
            "new_factor_count": 1,
            "existing_parameters_frozen": args.freeze_existing_parameters,
            "local_step_scale": (
                args.local_step_scale
                if args.freeze_existing_parameters
                else 1.0
            ),
            "full_train_pieces": len(train_ids),
            "full_validation_pieces": len(validation_ids),
            "scope_matches_gibbs": True,
            "historical_rules_loaded": False,
            "expert_constraints_loaded": False,
            "test_loaded": False,
        },
        "corpus": source["corpus"],
        "model": {
            **source["model"],
            "register_logits": fitted.register.tolist(),
            "tonal_logits": fitted.tonal.tolist(),
            "rules": rules,
            "train_nll": exact_reinduction._nll(
                train["chosen"],
                train["voices"],
                train["modes"],
                train["tonics"],
                candidates,
                train["factors"],
                fitted,
            ),
            "validation_nll": exact_reinduction._nll(
                validation["chosen"],
                validation["voices"],
                validation["modes"],
                validation["tonics"],
                candidates,
                validation["factors"],
                fitted,
            ),
            "full_fit": fit,
        },
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(result), encoding="utf-8")
    print(f"[v16-exact-refit] wrote {args.output}", flush=True)
    print(f"[v16-exact-refit] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
