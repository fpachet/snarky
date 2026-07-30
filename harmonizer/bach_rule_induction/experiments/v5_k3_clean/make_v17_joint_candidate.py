#!/usr/bin/env python3
"""Build one bounded V17 new-factor plus existing-factor correction."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from run_v17_paired_finite_difference import _conditional_step

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=FACTOR_BASE / "v13_exact_directed_metric_model.json",
    )
    parser.add_argument(
        "--shortlist",
        type=Path,
        default=FACTOR_BASE / "v16_exact_candidate_shortlist.json",
    )
    parser.add_argument("--candidate-rank", type=int, default=9)
    parser.add_argument("--candidate-max-abs-step", type=float, default=0.15)
    parser.add_argument("--existing-index", type=int, required=True)
    parser.add_argument("--existing-delta", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    shortlist = json.loads(args.shortlist.read_text(encoding="utf-8"))
    candidate = next(
        (
            record
            for record in shortlist["candidates"]
            if record["rank"] == args.candidate_rank
        ),
        None,
    )
    if candidate is None:
        raise ValueError("Candidate rank is absent from the shortlist")
    result = copy.deepcopy(source)
    rules = result["model"]["rules"]
    if not 0 <= args.existing_index < len(rules):
        raise ValueError("Existing factor index is out of range")
    original_weight = float(rules[args.existing_index]["weight"])
    rules[args.existing_index]["weight"] = original_weight + args.existing_delta
    candidate_step = _conditional_step(
        candidate,
        args.candidate_max_abs_step,
    )
    rules.append(
        {
            "family": candidate["family"],
            "feature": candidate["feature"],
            "selection": {
                **candidate["conditional"],
                "v17_joint_correction": {
                    "candidate_rank": args.candidate_rank,
                    "candidate_step": candidate_step,
                    "existing_factor_index": args.existing_index,
                    "existing_factor_key": rules[args.existing_index][
                        "feature"
                    ]["key"],
                    "existing_original_weight": original_weight,
                    "existing_delta": args.existing_delta,
                },
            },
            "weight": candidate_step,
        }
    )
    result["experiment"] = {
        "id": "F-K3-V17-JOINT-CANDIDATE",
        "status": "EXPLORATORY_JOINT_CANDIDATE_PENDING_PAIRED_AUDIT",
        "source_model": str(args.source.resolve()),
        "candidate_rank": args.candidate_rank,
        "candidate_step": candidate_step,
        "existing_factor_index": args.existing_index,
        "existing_factor_delta": args.existing_delta,
        "conditional_nll_not_recomputed": True,
        "test_loaded": False,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[v17-joint] wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
