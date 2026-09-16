"""First-order Blues: exact reference DP and native rational-product optimization."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from benchmarks.blues_corpus import training_sequences
from snarky import Atom
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    Query,
    QueryKind,
    RationalProductObjective,
    WeightTable,
    solve,
)
from snarky.finite.cli import result_payload
from snarky.finite.constraints import (
    AllDifferentConstraint,
    ConstraintOperator,
    CountConstraint,
    TableConstraint,
)

CORPUS = Path(__file__).parent / "data/omnibook_blues_v1/corpus.json"


@dataclass(frozen=True)
class FirstOrderModel:
    alphabet: tuple[str, ...]
    initial: dict[str, Fraction]
    transitions: dict[tuple[str, str], Fraction]

    def score(self, sequence: tuple[str, ...]) -> Fraction:
        if not sequence:
            return Fraction(1)
        result = self.initial.get(sequence[0], Fraction(0))
        for pair in zip(sequence, sequence[1:], strict=False):
            result *= self.transitions.get(pair, Fraction(0))
        return result


def train(sequences: tuple[tuple[str, ...], ...]) -> FirstOrderModel:
    """MLE within sequences; initial distribution is the corpus symbol marginal.

    Counts retain repeated half-bar chords and tune/take multiplicity. No final
    symbol is joined to another sequence's first symbol. No smoothing is applied.
    """
    symbols = Counter(symbol for sequence in sequences for symbol in sequence)
    if not symbols:
        raise ValueError("training corpus is empty")
    pairs = Counter(
        pair
        for sequence in sequences
        for pair in zip(sequence, sequence[1:], strict=False)
    )
    outgoing: Counter[str] = Counter()
    for (left, _), count in pairs.items():
        outgoing[left] += count
    return FirstOrderModel(
        tuple(sorted(symbols)),
        {symbol: Fraction(count, symbols.total()) for symbol, count in symbols.items()},
        {pair: Fraction(count, outgoing[pair[0]]) for pair, count in pairs.items()},
    )


def reference_dp(
    source: FirstOrderModel,
    domains: tuple[tuple[str, ...], ...],
    counted: str | None = None,
    target: int = 1,
) -> tuple[Fraction, tuple[str, ...]] | None:
    """Independent exact Viterbi with an optional occurrence counter; no Snarky."""
    current = {}
    for symbol in domains[0]:
        count = int(symbol == counted) if counted is not None else 0
        if source.initial.get(symbol, 0) and (counted is None or count <= target):
            current[symbol, count] = (source.initial[symbol], (symbol,))
    for domain in domains[1:]:
        following = {}
        for (previous, count), (score, path) in current.items():
            for symbol in domain:
                next_count = count + int(symbol == counted) if counted else 0
                if counted and next_count > target:
                    continue
                weight = source.transitions.get((previous, symbol), 0)
                if not weight:
                    continue
                candidate = (score * weight, (*path, symbol))
                key = symbol, next_count
                if key not in following or candidate[0] > following[key][0]:
                    following[key] = candidate
        current = following
    candidates = [
        value
        for (_, count), value in current.items()
        if counted is None or count == target
    ]
    return max(candidates, key=lambda value: value[0]) if candidates else None


def blues_domains(source: FirstOrderModel) -> tuple[tuple[str, ...], ...]:
    alphabet = tuple(sorted(source.alphabet, key=lambda s: (-source.initial[s], s)))
    anchors = {0: "C7", 8: "F7", 23: "G7"}
    if not set(anchors.values()) <= set(alphabet):
        raise ValueError("training alphabet lacks a Blues anchor")
    return tuple((anchors[i],) if i in anchors else alphabet for i in range(24))


def native_model(source: FirstOrderModel, case: str) -> FiniteModel:
    if case not in ("ordinary", "exotic", "boulez"):
        raise ValueError("unknown Blues case")
    names = tuple(Atom(f"x{i}") for i in range(24))
    domains = blues_domains(source)
    initial = {(Atom(s),): p for s, p in source.initial.items()}
    transitions = {tuple(map(Atom, pair)): p for pair, p in source.transitions.items()}
    constraints: list = [TableConstraint(Atom("initial"), names[:1], tuple(initial))]
    factors = [WeightTable("initial", names[:1], initial)]
    for i in range(1, 24):
        scope = names[i - 1 : i + 1]
        constraints.append(
            TableConstraint(Atom(f"transition{i}"), scope, tuple(transitions))
        )
        factors.append(WeightTable(f"transition{i}", scope, transitions))
    if case == "boulez":
        constraints.append(AllDifferentConstraint(Atom("distinct"), names))
    if case == "exotic":
        constraints.append(
            CountConstraint(
                Atom("one_flat_five"),
                names,
                Atom("Gb7"),
                ConstraintOperator.EQUAL,
                1,
            )
        )
    return FiniteModel(
        f"blues_{case}",
        tuple(
            FiniteVariable(v, tuple(map(Atom, domain)))
            for v, domain in zip(names, domains, strict=True)
        ),
        tuple(constraints),
        objective=RationalProductObjective(tuple(factors)),
    )


def validate_solution(source: FirstOrderModel, case: str, result, names: tuple) -> None:
    if result.incumbent is None:
        return
    sequence = tuple(result.incumbent.assignment[name].name for name in names)
    assert len(sequence) == 24
    assert (sequence[0], sequence[8], sequence[-1]) == ("C7", "F7", "G7")
    assert source.score(sequence) == result.incumbent.objective_value > 0
    if case == "exotic":
        assert sequence.count("Gb7") == 1
    if case == "boulez":
        assert len(set(sequence)) == 24


def run(corpus: Path, repeat: int, seconds: float) -> dict:
    data = json.loads(corpus.read_text())
    root = Path(__file__).resolve().parents[1]
    version = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    source_paths = sorted((root / "src/snarky/finite").glob("*.py")) + [
        Path(__file__),
        Path(__file__).with_name("blues_corpus.py"),
    ]
    payload = {
        "portfolio": "omnibook_blues_v1",
        "started_at": datetime.now(UTC).isoformat(),
        "measurement_class": "initial application baseline; not a paired speedup study",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "commit": version,
        "dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=root)
        ),
        "corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
        "source_hashes": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in source_paths
        },
        "repeat": repeat,
        "search_time_limit_seconds": seconds,
        "initial": "corpus symbol marginal",
        "augmentation": "all 12 keys, once",
        "policy": "mrv; objective value order; auto bound",
        "cases": [],
    }
    for variant in ("source_faithful", "paper_style_proposed"):
        start = perf_counter()
        source = train(training_sequences(data, variant, all_keys=True))
        training = perf_counter() - start
        for case in ("ordinary", "exotic", "boulez"):
            start = perf_counter()
            model = native_model(source, case)
            construction = perf_counter() - start
            start = perf_counter()
            reference = reference_dp(
                source, blues_domains(source), "Gb7" if case == "exotic" else None
            )
            reference_time = perf_counter() - start
            record = {
                "variant": variant,
                "case": case,
                "alphabet": len(source.alphabet),
                "transitions": len(source.transitions),
                "training_seconds": training,
                "construction_seconds": construction,
                "reference_seconds": reference_time,
                "reference_role": "relaxed_upper_bound"
                if case == "boulez"
                else "exact_optimum",
                "reference_product": str(reference[0]) if reference else None,
                "runs": [],
            }
            for _ in range(repeat):
                start = perf_counter()
                result = solve(
                    model,
                    Query(QueryKind.MAXIMIZE, time_limit_seconds=seconds),
                    policy="mrv",
                    value_policy="objective",
                )
                total = perf_counter() - start
                names = tuple(v.name for v in model.variables)
                validate_solution(source, case, result, names)
                if result.status.value == "optimal" and case != "boulez":
                    assert (
                        reference and result.incumbent.objective_value == reference[0]
                    )
                if reference and result.incumbent:
                    assert result.incumbent.objective_value <= reference[0]
                item = result_payload(result)
                item["prepare_and_search_seconds"] = total
                item["preparation_seconds"] = total - result.elapsed_seconds
                if result.incumbent:
                    p = result.incumbent.objective_value
                    item["log_probability"] = math.log(p.numerator) - math.log(
                        p.denominator
                    )
                    item["local_probabilities"] = [
                        str(source.initial[result.incumbent.assignment[names[0]].name])
                    ] + [
                        str(
                            source.transitions[
                                (
                                    result.incumbent.assignment[a].name,
                                    result.incumbent.assignment[b].name,
                                )
                            ]
                        )
                        for a, b in zip(names, names[1:], strict=False)
                    ]
                    item["sequence"] = [
                        result.incumbent.assignment[v].name for v in names
                    ]
                record["runs"].append(item)
            payload["cases"].append(record)
            print(
                json.dumps(
                    {
                        "variant": variant,
                        "case": case,
                        "runs": [
                            (
                                r["status"],
                                r["prepare_and_search_seconds"],
                                r["explored_nodes"],
                            )
                            for r in record["runs"]
                        ],
                    }
                ),
                flush=True,
            )
    for path, digest in payload["source_hashes"].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"source changed during collection: {path}")
    payload["finished_at"] = datetime.now(UTC).isoformat()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeat < 1 or not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("positive repeat and finite positive seconds required")
    if args.output.exists():
        raise FileExistsError(args.output)
    result = run(args.corpus, args.repeat, args.seconds)
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
