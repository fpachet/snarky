"""Emit standalone native-variant sanitizer programs with an assignment oracle."""

import argparse
from pathlib import Path

from .native_variants import variant_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["exact", "bounds", "staged", "budget"], required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--delta", action="store_true")
    parser.add_argument("--shared", action="store_true")
    args = parser.parse_args()
    driver = Path(__file__).with_name("native_search_sanitize.c").read_text()
    driver = "\n".join(
        line for line in driver.splitlines() if not line.startswith('#include "')
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        variant_source(args.mode, delta=args.delta, shared=args.shared)
        + "\n"
        + driver
        + "\n"
    )


if __name__ == "__main__":
    main()
