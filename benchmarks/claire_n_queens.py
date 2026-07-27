"""Compare Snarky and CLAIRE4 on a normalized N-Queens formulation."""

from __future__ import annotations

import argparse
import json
import platform
import random
import re
import statistics
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.claire_support import (
    git_commit as _git_commit,
)
from benchmarks.claire_support import (
    resolve_claire_binary,
    resolve_claire_root,
)
from csp_solver.four_queens import n_queens_intensional_facts
from csp_solver.solver import (
    assignment_from_solution,
    prepare_finite_csp_search,
)
from snarky import (
    Atom,
    ChoiceAlternative,
    ChoicePoint,
    ChoiceSearchStatus,
    Number,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLAIRE_SOURCE = Path(__file__).with_suffix(".cl")
RESULT_PREFIX = "SNARKY_CLAIRE_RESULT "
DEFAULT_SIZES = (8, 10, 12, 14)
_CLAIRE_RESULT = re.compile(
    r"size=(?P<size>\d+) "
    r"elapsed_ns=(?P<elapsed_ns>\d+) "
    r"solved=(?P<solved>0|1) "
    r"branch_attempts=(?P<branch_attempts>\d+) "
    r"failed_branches=(?P<failed_branches>\d+) "
    r"rule_firings=(?P<rule_firings>\d+) "
    r"candidate_removals=(?P<candidate_removals>\d+) "
    r"solution=(?P<solution>\d+(?:,\d+)*)"
)


def validate_solution(size: int, solution: Sequence[int]) -> None:
    """Reject incomplete or attacking N-Queens solutions."""

    if len(solution) != size:
        raise ValueError(
            f"expected {size} rows, received {len(solution)}"
        )
    if set(solution) != set(range(1, size + 1)):
        raise ValueError("queen rows are not a permutation of 1..N")
    if len({row + column for column, row in enumerate(solution, 1)}) != size:
        raise ValueError("queens share an ascending diagonal")
    if len({row - column for column, row in enumerate(solution, 1)}) != size:
        raise ValueError("queens share a descending diagonal")


def parse_claire_result(output: str) -> dict[str, Any]:
    """Parse the stable marker emitted amid CLAIRE's runtime banner."""

    marker = next(
        (
            line[len(RESULT_PREFIX) :]
            for line in output.splitlines()
            if line.startswith(RESULT_PREFIX)
        ),
        None,
    )
    if marker is None:
        raise ValueError("CLAIRE output has no result marker")
    match = _CLAIRE_RESULT.fullmatch(marker)
    if match is None:
        raise ValueError(f"malformed CLAIRE result marker: {marker!r}")
    parsed: dict[str, Any] = {
        key: int(value)
        for key, value in match.groupdict().items()
        if key not in {"solved", "solution"}
    }
    parsed["solved"] = match.group("solved") == "1"
    parsed["solution"] = tuple(
        int(value) for value in match.group("solution").split(",")
    )
    parsed["seconds"] = parsed.pop("elapsed_ns") / 1_000_000_000.0
    return parsed


def _summarize(
    samples: list[dict[str, Any]],
    counters: Sequence[str],
) -> dict[str, Any]:
    if not samples:
        raise ValueError("at least one sample is required")
    stable = {
        key: samples[0][key]
        for key in ("solution", *counters)
    }
    for sample in samples[1:]:
        for key, expected in stable.items():
            if sample[key] != expected:
                raise RuntimeError(
                    f"non-deterministic {key}: "
                    f"{sample[key]!r} != {expected!r}"
                )
    seconds = [float(sample["seconds"]) for sample in samples]
    summary = {
        "median_seconds": statistics.median(seconds),
        "min_seconds": min(seconds),
        "max_seconds": max(seconds),
        **stable,
        "runs": samples,
    }
    if "preparation_seconds" in samples[0]:
        preparation_seconds = [
            float(sample["preparation_seconds"]) for sample in samples
        ]
        summary.update(
            {
                "median_preparation_seconds": statistics.median(
                    preparation_seconds
                ),
                "min_preparation_seconds": min(preparation_seconds),
                "max_preparation_seconds": max(preparation_seconds),
            }
        )
    return summary


class ClaireNQueensPolicy:
    """MRV with CLAIRE's numeric column and row tie-breaking."""

    def select_point(
        self,
        points: Sequence[ChoicePoint],
    ) -> ChoicePoint:
        if not points:
            raise ValueError("cannot select from an empty choice set")
        return min(
            points,
            key=lambda point: (
                len(point.alternatives),
                _column_number(point.variable),
            ),
        )

    def order_alternatives(
        self,
        point: ChoicePoint,
        random_source: random.Random,
    ) -> tuple[ChoiceAlternative, ...]:
        del random_source
        return tuple(
            sorted(
                point.alternatives,
                key=lambda alternative: _row_number(alternative.value),
            )
        )


def _column_number(value: object) -> int:
    if not isinstance(value, Atom) or not value.name.startswith("queen_"):
        raise TypeError(f"expected a queen variable, received {value!r}")
    return int(value.name.removeprefix("queen_"))


def _row_number(value: object) -> int:
    if not isinstance(value, Number) or not isinstance(value.value, int):
        raise TypeError(f"expected an integer Number, received {value!r}")
    return value.value


def measure_snarky(size: int, repeat: int) -> dict[str, Any]:
    """Measure solve time after constructing the common intensional model."""

    model = n_queens_intensional_facts(size)
    samples: list[dict[str, Any]] = []
    for _ in range(repeat):
        preparation_started = perf_counter()
        prepared = prepare_finite_csp_search(
            model,
            max_solutions=1,
            policy=ClaireNQueensPolicy(),
            reversible_depth_first=True,
        )
        preparation_elapsed = perf_counter() - preparation_started
        search_started = perf_counter()
        result = prepared.solve()
        search_elapsed = perf_counter() - search_started
        if result.status is not ChoiceSearchStatus.SOLVED:
            raise RuntimeError(f"Snarky did not solve N-Queens for N={size}")
        assignment = assignment_from_solution(
            result.solutions[0],
            model.problem,
        )
        solution = tuple(
            _row_number(assignment[Atom(f"queen_{column}")])
            for column in range(1, size + 1)
        )
        validate_solution(size, solution)
        samples.append(
            {
                "seconds": search_elapsed,
                "preparation_seconds": preparation_elapsed,
                "solution": solution,
                "explored_nodes": result.explored_nodes,
                "failed_branches": result.failed_branches,
                "solution_decisions": len(
                    result.solutions[0].decisions
                ),
            }
        )
    return _summarize(
        samples,
        ("explored_nodes", "failed_branches", "solution_decisions"),
    )


def measure_claire(
    size: int,
    repeat: int,
    binary: Path,
    *,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = (
        subprocess.run
    ),
) -> dict[str, Any]:
    """Measure the bundled CLAIRE interpreter using its internal timer."""

    samples: list[dict[str, Any]] = []
    template = CLAIRE_SOURCE.read_text(encoding="utf-8")
    dimension = "MAX_N :: 16"
    if template.count(dimension) != 1:
        raise RuntimeError("CLAIRE template has no unique MAX_N declaration")
    with tempfile.TemporaryDirectory(
        prefix=f"snarky-claire-queens-{size}-"
    ) as temporary_directory:
        generated_source = (
            Path(temporary_directory) / f"n_queens_{size}.cl"
        )
        generated_source.write_text(
            template.replace(dimension, f"MAX_N :: {size}"),
            encoding="utf-8",
        )
        command = (
            str(binary),
            "-n",
            "-f",
            str(generated_source),
            "-e",
            f"benchmark({size})",
        )
        for _ in range(repeat):
            completed = run_command(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            parsed = parse_claire_result(completed.stdout)
            if parsed["size"] != size or not parsed["solved"]:
                raise RuntimeError(
                    "CLAIRE returned an invalid status "
                    f"for N={size}: {parsed}"
                )
            validate_solution(size, parsed["solution"])
            samples.append(parsed)
    return _summarize(
        samples,
        (
            "branch_attempts",
            "failed_branches",
            "rule_firings",
            "candidate_removals",
        ),
    )


def run(
    sizes: tuple[int, ...],
    repeat: int,
    *,
    engine: str,
    claire_root: Path | None = None,
    claire_binary: Path | None = None,
) -> dict[str, Any]:
    """Run selected engines and return one machine-readable payload."""

    selected_root: Path | None = None
    selected_binary: Path | None = None
    if engine in {"both", "claire"}:
        selected_root = resolve_claire_root(claire_root)
        selected_binary = resolve_claire_binary(
            selected_root,
            claire_binary,
        )

    results: list[dict[str, Any]] = []
    for size in sizes:
        case: dict[str, Any] = {"size": size}
        if engine in {"both", "snarky"}:
            case["snarky"] = measure_snarky(size, repeat)
        if selected_binary is not None:
            case["claire_interpreted"] = measure_claire(
                size,
                repeat,
                selected_binary,
            )
        if (
            engine == "both"
            and case["snarky"]["solution"]
            != case["claire_interpreted"]["solution"]
        ):
            raise RuntimeError(
                f"N={size}: engines selected different first solutions"
            )
        results.append(case)

    payload: dict[str, Any] = {
        "benchmark": "claire_n_queens",
        "protocol": {
            "goal": "first_solution",
            "variable_order": "minimum_remaining_values",
            "value_order": "ascending",
            "singleton_propagation": True,
            "claire_table_dimension": "exact_size",
            "timing_scope": {
                "snarky": "prepared SessionChoiceSearch.solve only",
                "claire": "queens search after source and table loading",
            },
        },
        "repeat": repeat,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "snarky_commit": _git_commit(PROJECT_ROOT),
        "results": results,
    }
    if selected_root is not None and selected_binary is not None:
        payload["claire"] = {
            "root": str(selected_root),
            "binary": str(selected_binary),
            "commit": _git_commit(selected_root),
            "mode": "interpreted",
        }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=DEFAULT_SIZES,
    )
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument(
        "--engine",
        choices=("both", "snarky", "claire"),
        default="both",
    )
    parser.add_argument("--claire-root", type=Path)
    parser.add_argument("--claire-binary", type=Path)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error("--repeat must be positive")
    if any(size < 4 or size > 16 for size in arguments.sizes):
        parser.error("--sizes must be in 4..16")
    print(
        json.dumps(
            run(
                tuple(arguments.sizes),
                arguments.repeat,
                engine=arguments.engine,
                claire_root=arguments.claire_root,
                claire_binary=arguments.claire_binary,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
