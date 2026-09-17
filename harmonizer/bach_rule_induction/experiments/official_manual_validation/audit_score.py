#!/usr/bin/env python3
"""Audit any generated or external SATB MusicXML with the manual rulebase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from harmonizer.official_manual import audit_musicxml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path)
    parser.add_argument(
        "--profile",
        choices=("diagnostic", "bach_empirical", "pedagogical_strict"),
        default="diagnostic",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    diagnostic = audit_musicxml(args.score, profile=args.profile)
    payload = diagnostic.to_dict()
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"[official-manual] wrote {args.output}")
    return 2 if diagnostic.contradiction else 0


if __name__ == "__main__":
    raise SystemExit(main())
