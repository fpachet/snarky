#!/usr/bin/env python3
"""Summarize V5.11 local-tonality persistence sensitivity runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# V5.11 — sensibilité de la persistance tonale locale",
        "",
        "Même train, même validation, quinze itérations EM. Seule varie la",
        "probabilité de conserver le statut entre deux noyaux adjacents.",
        "Le test scellé reste fermé.",
        "",
        "| Persistance | Gain d'évidence validation | États déplacés | "
        "Changements | Entropie | Rares reclassifiés |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['stay_probability']:.2f} | "
            f"{row['log_evidence_gain_per_state']:+.6f} | "
            f"{100 * row['shifted_state_rate']:.2f} % | "
            f"{100 * row['local_change_rate']:.2f} % | "
            f"{row['posterior_entropy_normalized']:.3f} | "
            f"{100 * row['globally_rare_reclassified_share']:.2f} % |"
        )
    lines.extend(
        [
            "",
            "Le résultat qualitatif est stable : même avec une transition beaucoup",
            "plus ou moins persistante, le statut améliore fortement l'évidence et",
            "reclasse environ quatre choix globalement rares sur cinq.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    paths = (
        RESULTS / "v5_11_local_tonality_hmm_stay085.json",
        RESULTS / "v5_11_local_tonality_hmm.json",
        RESULTS / "v5_11_local_tonality_hmm_stay097.json",
    )
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    rows = []
    for payload in payloads:
        status = payload["validation"]["status"]
        rarity = payload["validation"]["rarity"]
        rows.append(
            {
                "stay_probability": payload["experiment"]["stay_probability"],
                "log_evidence_gain_per_state": status["log_evidence_gain_per_state"],
                "shifted_state_rate": status["shifted_state_rate"],
                "local_change_rate": status["local_change_rate"],
                "posterior_entropy_normalized": status["posterior_entropy_normalized"],
                "globally_rare_reclassified_share": rarity[
                    "globally_rare_reclassified_share"
                ],
                "local_rare_rate": rarity["local_rare_rate"],
            }
        )
    result = {
        "experiment": {
            "id": "V5.11-LOCAL-TONALITY-SENSITIVITY",
            "test_loaded": False,
            "validation_used_for_fit": False,
        },
        "rows": rows,
    }
    json_path = RESULTS / "v5_11_local_tonality_sensitivity.json"
    report_path = RESULTS / "V5_11_LOCAL_TONALITY_SENSITIVITY.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_markdown(result), encoding="utf-8")
    print(f"[k3-v5.11] wrote {json_path}")
    print(f"[k3-v5.11] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
