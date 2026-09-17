"""Paired reference/native comparison with fixed work and preserved source archives.

The same standalone worker is executed against both source roots. No engine
modules are imported until that root has been selected. Timing and allocation
runs are separate; every paired session alternates the implementation order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import tarfile
import tracemalloc
from contextlib import nullcontext
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

REFERENCE = "2fbdd9d0e70ad5dc45fbf4dc5472510f84365f5c"
ROOT = Path(__file__).resolve().parents[1]
RULE_CASES = [
    f"{case}:{strategy}"
    for case in (
        "small/triangle_closure",
        "thesis/hanoi",
        "thesis/monkey_bananas/neopus_mea",
    )
    for strategy in ("indexed", "semi-naive")
]
CSP_CASES = ["magic3", "magic4", "latin5", "latin7"]
MARKOV_CASES = ["markov25x4", "markov33x8", "markov129x8"]
JOIN_CASES = [
    f"joins/{groups}x8/{mode}" for groups in (25, 100) for mode in ("cold", "streamed")
]
CLASSICAL_CASES = [
    "classical/magic5",
    "classical/sudoku_pure",
    "classical/sudoku_mixed",
]
MARKOV_SECONDS = 3.0
SCALING_CASES = [
    "short_dense",
    "medium_sparse",
    "long_sparse",
    "wide_sparse",
    "second_order",
    "large_costs",
    "long_second_order",
    "tied",
    "infeasible",
]


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def scaling_operation(case: str, mode: str):
    from benchmarks import finite_markov
    from snarky import Atom
    from snarky.finite import Query, QueryKind
    from snarky.finite.constraints import AllDifferentConstraint
    from snarky.finite.propagation import NativeState
    from snarky.finite.search import search

    name = case.removeprefix("scaling/")
    finite_markov.CASES.update(
        {
            "long_second_order": (64, 8, 2, 0.6, 8, 31),
            "tied": (64, 8, 1, 1.0, 1, 32),
            "infeasible": (16, 4, 1, 1.0, 8, 33),
        }
    )

    def prepare():
        source, state = finite_markov.prepare(name)
        if name == "infeasible":
            state = NativeState(
                replace(
                    state.model,
                    constraints=(
                        *state.model.constraints,
                        AllDifferentConstraint(
                            Atom("impossible"),
                            tuple(v.name for v in state.model.variables[:5]),
                        ),
                    ),
                )
            )
        return source, state

    def execute(prepared):
        return search(
            prepared[1],
            Query(
                QueryKind.MINIMIZE, max_nodes=1000, time_limit_seconds=MARKOV_SECONDS
            ),
            bounding="local" if mode == "local" else "auto",
        )

    def validate(prepared, result):
        source, state = prepared
        incumbent = result.incumbent
        relaxation = finite_markov.relaxed_optimum(source, len(state.model.variables))
        if incumbent:
            sequence = tuple(
                incumbent.assignment[v.name] for v in state.model.variables
            )
            assert sequence[0] == sequence[-1]
            assert len(set(sequence[: len(source.alphabet)])) == len(source.alphabet)
            assert source.sequence_cost(sequence) == incumbent.objective_value
            assert relaxation <= incumbent.objective_value
        if name == "infeasible":
            assert result.status.value == "infeasible"
        return {
            "status": result.status.value,
            "termination": result.termination.value,
            "objective": incumbent.objective_value if incumbent else None,
            "bound": result.objective_bound,
            "proved": result.complete,
            "relaxed_chain_optimum": relaxation,
            "nodes": result.explored_nodes,
            "failures": result.failed_branches,
            "pruned": result.pruned_branches,
            "revisions": result.constraint_revisions,
            "first_incumbent_seconds": result.incumbent_history[0].elapsed_seconds
            if result.incumbent_history
            else None,
            "incumbent_values": result.incumbent_values,
        }

    return prepare, execute, validate


def legacy_portfolio_operation(case: str):
    """Preserve existing workloads; split scopes only where their API permits it."""
    if case.startswith("joins/"):
        from benchmarks import incremental_conjunctions as joins
        from snarky import (
            EngineLimits,
            ForwardEngine,
            SemiNaiveInstantiationStrategy,
            render_term,
        )

        _, size, mode = case.split("/")
        groups = int(size.split("x")[0])
        membership = joins.build_membership_facts(groups, 8)
        compatibility = joins.build_compatibility_facts(groups, 8)
        expected = joins.expected_output_facts(groups, 8)

        def prepare():
            strategy = SemiNaiveInstantiationStrategy()
            engine = ForwardEngine(
                joins.JOIN_RULES,
                strategy=strategy,
                limits=EngineLimits(
                    max_facts=len(membership) + 2 * len(compatibility) + 1
                ),
            )
            session = engine.create_session(
                (*membership, *compatibility) if mode == "cold" else membership
            )
            if mode == "streamed":
                session.run_group(engine.default_group, materialize_result=False)
                strategy.metrics.reset()
            return engine, session, strategy

        def execute(state):
            engine, session, _ = state
            if mode == "cold":
                session.run_group(engine.default_group, materialize_result=False)
            else:
                for fact in compatibility:
                    session.assume(fact)
                    session.run_group(engine.default_group, materialize_result=False)
            return session

        def validate(state, session):
            joins._validate_session(
                session.facts,
                expected,
                input_fact_count=len(membership) + len(compatibility),
            )
            return {
                "output": fingerprint([render_term(f.entity) for f in session.facts]),
                "facts": len(session.facts),
                "outputs": len(expected),
                "match_attempts": state[-1].metrics.match_attempts,
            }
    else:
        from benchmarks.classical_csp import _magic, _sudoku
        from sudoku.rulebase import TECHNIQUE_ORDER

        def prepare():
            return None

        def execute(state):
            if case == "classical/magic5":
                return _magic(
                    5,
                    symmetry_breaking=False,
                    propagation_guided=False,
                    dom_wdeg_only=False,
                )
            return _sudoku(TECHNIQUE_ORDER if case.endswith("mixed") else ())

        def validate(state, result):
            return {
                "status": result.status.value,
                "nodes": result.explored_nodes,
                "failures": result.failed_branches,
            }

    return prepare, execute, validate


def rule_operation(case: str):
    from rulebases.runner import RULEBASE_ROOT, _load_scenario
    from snarky import (
        ForwardEngine,
        IndexedInstantiationStrategy,
        MEAConflictStrategy,
        SemiNaiveInstantiationStrategy,
        parse_rule_groups,
        parse_rules,
        render_term,
    )
    from snarky.serialization.yaml_format import load_facts

    scenario, strategy_name = case.split(":")
    path = RULEBASE_ROOT / scenario
    expected = load_facts(
        path / _load_scenario(path / "scenario.yaml")["expected_facts"]
    )

    def prepare():
        payload = _load_scenario(path / "scenario.yaml")
        initial = load_facts(path / payload["facts"])
        text = (path / payload["rules"]).read_text()
        strategy = (
            IndexedInstantiationStrategy()
            if strategy_name == "indexed"
            else SemiNaiveInstantiationStrategy()
        )
        conflict = (
            MEAConflictStrategy() if payload.get("conflict_strategy") == "mea" else None
        )
        engine = ForwardEngine(
            parse_rules(text) if payload["kind"] == "rules" else (),
            strategy=strategy,
            conflict_strategy=conflict,
        )
        session = engine.create_session(initial)
        if payload["kind"] == "rules":
            groups, rounds = (engine.default_group,), 1
        else:
            indexed = {g.name: g for g in parse_rule_groups(text)}
            groups = tuple(indexed[name] for name in payload["group_order"])
            rounds = payload["max_rounds"]
        return session, groups, rounds, strategy

    def execute(prepared):
        session, groups, rounds, _ = prepared
        for _ in range(rounds):
            before = session.event_count
            for group in groups:
                session.run_group(group)
            if rounds == 1 or before == session.event_count:
                break
        else:
            raise AssertionError("no fixed point")
        return session.snapshot()

    def validate(prepared, result):
        assert set(expected) <= set(result.facts)

        def fact(value):
            return render_term(value.entity), render_term(value.status)

        observation = {
            "facts": [fact(f) for f in result.facts],
            "derived": [fact(f) for f in result.derived_facts],
            "events": [
                (
                    e.kind.value,
                    fact(e.fact),
                    e.rule_name,
                    e.rule_group,
                    tuple(fact(f) for f in e.premises),
                )
                for e in result.events
            ],
        }
        return {
            "output": fingerprint(observation),
            "facts": len(result.facts),
            "activations": result.fired_activation_count,
            "match_attempts": prepared[-1].metrics.match_attempts,
        }

    return prepare, execute, validate


def csp_operation(case: str, mode: str):
    from csp_solver.latin_square import latin_square_facts
    from csp_solver.magic_square import magic_square_facts
    from csp_solver.solver import (
        assignment_from_solution,
        finite_csp_rule_library,
        prepare_finite_csp_search,
    )
    from snarky import MRVChoicePolicy, render_term

    size = int(case[-1])
    model = (
        magic_square_facts(size)
        if case.startswith("magic") or case == "mixed_magic3"
        else latin_square_facts(size)
    )
    if mode == "legacy":

        def prepare():
            return prepare_finite_csp_search(
                model,
                policy=MRVChoicePolicy(prefer_high_weight=False),
                rule_groups=finite_csp_rule_library().finite_domain_groups,
                max_nodes=5000,
            )

        def execute(state):
            return state.solve()

        def assignment(result):
            assert result.solutions
            return assignment_from_solution(result.solutions[0], model.problem)
    else:
        from csp_solver.native import native_model
        from snarky import Atom, Fact, Triple, parse_rule_groups
        from snarky.finite import FiniteVariable, Query
        from snarky.finite.mixed import MixedState
        from snarky.finite.propagation import NativeState
        from snarky.finite.search import search

        adapted = native_model(model)
        normalized = replace(
            adapted,
            context=() if case == "mixed_magic3" else adapted.context,
            variables=tuple(
                FiniteVariable(v.name, tuple(sorted(v.domain, key=render_term)))
                for v in sorted(adapted.variables, key=lambda v: render_term(v.name))
            ),
        )
        if mode == "mixed":
            normalized = replace(
                normalized,
                rules=parse_rule_groups("""GROUP reports
RULE selected
WHEN
($v value $n)
THEN
ADD ($v selected $n)
END
END_GROUP"""),
            )

        def prepare():
            return (
                MixedState(normalized) if mode == "mixed" else NativeState(normalized)
            )

        def execute(state):
            return search(state, Query(max_nodes=5000), policy="mrv")

        def assignment(result):
            assert result.incumbent is not None
            if mode == "mixed":
                assert all(
                    Fact(Triple(v, Atom("selected"), value)) in result.incumbent.facts
                    for v, value in result.incumbent.assignment.items()
                )
            return result.incumbent.assignment

    def validate(state, result):
        values = assignment(result)
        # All persistent constraints are checked independently on a complete result.
        # Diagonals, as well as rows/columns, are therefore covered for magic squares.
        if mode != "legacy":
            from snarky.finite.predicates import accepts

            assert all(accepts(c, values) for c in model.constraints)
        rows = sorted(
            (render_term(var), render_term(value)) for var, value in values.items()
        )
        return {
            "output": fingerprint(rows),
            "assignment": rows,
            "nodes": result.explored_nodes,
            "failures": result.failed_branches,
        }

    return prepare, execute, validate


def markov_operation(case: str, mode: str):
    from snarky import Atom, Number, render_term

    length, size = (int(v) for v in case.removeprefix("markov").split("x"))
    names = tuple(Atom(f"x{i:03}") for i in range(length))
    alphabet = tuple(Number(i) for i in range(size))
    initial_cost = size.bit_length() - 1
    row_costs = [*range(1, size), size - 1]
    costs = {
        (a, b): row_costs[(b.value - a.value - 1) % size]
        for a in alphabet
        for b in alphabet
    }
    optimum = initial_cost + length - 1
    max_nodes = 5000
    if mode == "native":
        from snarky.finite import MarkovCosts, Query, QueryKind, markov_model
        from snarky.finite.constraints import AllDifferentConstraint, TableConstraint
        from snarky.finite.propagation import NativeState
        from snarky.finite.search import search

        model = markov_model(
            MarkovCosts(alphabet, 1, {(v,): initial_cost for v in alphabet}, costs),
            length,
            names=names,
            constraints=(
                AllDifferentConstraint(Atom("prefix"), names[:size]),
                TableConstraint(
                    Atom("return"),
                    (names[0], names[-1]),
                    tuple((v, v) for v in alphabet),
                ),
            ),
        )

        def prepare():
            return NativeState(model)

        def execute(state):
            result = search(
                state,
                Query(
                    QueryKind.MINIMIZE,
                    max_nodes=max_nodes,
                    time_limit_seconds=MARKOV_SECONDS,
                ),
                variable_order=names,
                value_policy="objective",
            )
            return {
                "assignment": result.incumbent.assignment if result.incumbent else None,
                "objective": result.incumbent.objective_value
                if result.incumbent
                else None,
                "proved": result.complete,
                "termination": result.termination.value,
                "bound": result.objective_bound,
                "nodes": result.explored_nodes,
                "failures": result.failed_branches,
                "runs": 1,
                "first_incumbent_seconds": result.incumbent_history[0].elapsed_seconds
                if result.incumbent_history
                else None,
            }
    else:
        from csp_solver.persistent_constraints import (
            AllDifferentConstraint,
            ConstraintOperator,
            LinearSumConstraint,
            TableConstraint,
        )
        from csp_solver.solver import (
            CANDIDATE,
            CSP_PROBLEM,
            CSP_VARIABLE,
            KIND,
            VARIABLE,
            FiniteCSP,
            assignment_from_solution,
            finite_csp_rule_library,
            prepare_finite_csp_search,
        )
        from snarky import Fact, PriorityMRVChoicePolicy, Triple

        problem = Atom("markov")
        cost_names = tuple(Atom(f"c{i:03}") for i in range(length - 1))
        facts = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
        for var, domain in [
            *((v, alphabet) for v in names),
            *(
                (v, tuple(Number(i) for i in sorted(set(row_costs))))
                for v in cost_names
            ),
        ]:
            facts.extend(
                (
                    Fact(Triple(problem, VARIABLE, var)),
                    Fact(Triple(var, KIND, CSP_VARIABLE)),
                )
            )
            facts.extend(Fact(Triple(var, CANDIDATE, value)) for value in domain)
        rows = tuple((a, b, Number(cost)) for (a, b), cost in costs.items())
        constraints = [
            TableConstraint(Atom(f"edge{i}"), (names[i], names[i + 1], c), rows)
            for i, c in enumerate(cost_names)
        ]
        constraints += [
            AllDifferentConstraint(Atom("prefix"), names[:size]),
            TableConstraint(
                Atom("return"), (names[0], names[-1]), tuple((v, v) for v in alphabet)
            ),
        ]
        model = FiniteCSP(problem, tuple(facts), {}, constraints=tuple(constraints))
        policy = PriorityMRVChoicePolicy(
            {var: i for i, var in enumerate((*names, *cost_names))},
            prefer_high_weight=False,
        )

        def prepare_model(current, budget):
            return prepare_finite_csp_search(
                current,
                policy=policy,
                max_nodes=budget,
                rule_groups=finite_csp_rule_library().finite_domain_groups,
            )

        def prepare():
            return prepare_model(model, max_nodes)

        def execute(state):
            incumbent = first = None
            nodes = failures = runs = 0
            started = perf_counter()
            proved = False
            termination = "node_limit"

            def stop(signum, frame):
                raise TimeoutError("legacy feasibility deadline")

            previous_handler = signal.signal(signal.SIGALRM, stop)
            signal.setitimer(signal.ITIMER_REAL, MARKOV_SECONDS)
            try:
                while nodes < max_nodes:
                    result = state.solve()
                    nodes += result.explored_nodes
                    failures += result.failed_branches
                    runs += 1
                    if not result.solutions:
                        proved = result.status.value == "exhausted"
                        termination = "exhausted" if proved else "node_limit"
                        break
                    assignment = assignment_from_solution(result.solutions[0], problem)
                    best = initial_cost + sum(assignment[c].value for c in cost_names)
                    incumbent = assignment, best
                    if first is None:
                        first = perf_counter() - started
                    if nodes >= max_nodes:
                        break
                    cut = LinearSumConstraint(
                        Atom("improve"),
                        tuple((1, c) for c in cost_names),
                        ConstraintOperator.LESS_EQUAL,
                        best - initial_cost - 1,
                    )
                    state = prepare_model(
                        replace(model, constraints=(*model.constraints, cut)),
                        max_nodes - nodes,
                    )
            except TimeoutError:
                termination = "time_limit"
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous_handler)
            return {
                "assignment": incumbent[0] if incumbent else None,
                "objective": incumbent[1] if incumbent else None,
                "proved": proved,
                "termination": termination,
                "bound": incumbent[1] if proved and incumbent else optimum,
                "bound_source": "analytic minimum edge costs",
                "nodes": nodes,
                "failures": failures,
                "counters_complete": termination != "time_limit",
                "runs": runs,
                "first_incumbent_seconds": first,
            }

    def validate(state, result):
        assignment = result.pop("assignment")
        if assignment is None:
            assert not result["proved"] and result["objective"] is None
            result["output"] = None
            result["known_optimum"] = optimum
            return result
        sequence = tuple(assignment[v] for v in names)
        assert len(set(sequence[:size])) == size and sequence[0] == sequence[-1]
        assert (
            initial_cost + sum(costs[sequence[i : i + 2]] for i in range(length - 1))
            == result["objective"]
        )
        assert result["objective"] >= optimum
        if result["proved"]:
            assert result["objective"] == optimum
        result["output"] = fingerprint([render_term(v) for v in sequence])
        result["known_optimum"] = optimum
        return result

    return prepare, execute, validate


def sample(operation, memory: bool = False):
    prepare, execute, validate = operation
    if memory:
        tracemalloc.start()
    started = perf_counter()
    state = prepare()
    prepared = perf_counter()
    preparation_peak = None
    if memory:
        preparation_peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.reset_peak()
    result = execute(state)
    finished = perf_counter()
    search_peak = None
    if memory:
        search_peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    observation = validate(state, result)
    return {
        "preparation_seconds": prepared - started,
        "search_seconds": finished - prepared,
        "total_seconds": finished - started,
        "preparation_peak_traced_bytes": preparation_peak,
        "search_peak_traced_bytes": search_peak,
        "observation": observation,
    }


def worker(args):
    root = args.checkout.resolve()
    sys.path[:0] = [str(root / "src"), str(root)]
    if args.case.startswith("rules/"):
        operation = rule_operation(args.case.removeprefix("rules/"))
    elif args.case.startswith("scaling/"):
        operation = scaling_operation(args.case, args.mode)
    elif args.case.startswith(("joins/", "classical/")):
        operation = legacy_portfolio_operation(args.case)
    elif args.case.startswith("markov"):
        operation = markov_operation(args.case, args.mode)
    else:
        operation = csp_operation(args.case, args.mode)
    sample(operation)  # discarded warmup, with its own fresh state
    runs = [
        sample(operation, args.memory) for _ in range(1 if args.memory else args.repeat)
    ]
    stable = [
        {k: v for k, v in r["observation"].items() if not k.endswith("_seconds")}
        for r in runs
    ]
    if not any(o.get("termination") == "time_limit" for o in stable):
        assert all(o == stable[0] for o in stable)
    print(json.dumps({"runs": runs, "memory": args.memory}))


def snapshot(root: Path, destination: Path | None = None):
    extensions = {
        ".py",
        ".toml",
        ".lock",
        ".rules",
        ".constraints",
        ".program",
        ".model",
        ".yaml",
        ".json",
    }
    paths = []
    for directory in ("src", "csp_solver", "sudoku", "rulebases", "benchmarks"):
        paths.extend(
            p
            for p in (root / directory).rglob("*")
            if p.is_file()
            and p.suffix in extensions
            and not any(
                part in {"__pycache__", "results", ".venv", "build", "dist"}
                for part in p.relative_to(root).parts
            )
        )
    paths.extend(p for p in (root / "pyproject.toml", root / "uv.lock") if p.exists())
    digest = hashlib.sha256()
    with (
        tarfile.open(destination, "x:gz") if destination is not None else nullcontext()
    ) as archive:
        for path in sorted(set(paths)):
            relative = path.relative_to(root).as_posix()
            digest.update(relative.encode() + b"\0" + path.read_bytes() + b"\0")
            if archive is not None:
                archive.add(path, arcname=relative)
    return digest.hexdigest()


def collect(args):
    if args.output is None or args.output.exists():
        raise ValueError("supply a new output filename")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not hasattr(signal, "setitimer"):
        raise RuntimeError("legacy deadline measurements require POSIX setitimer")
    reference_archive = args.output.with_suffix(".reference.tar.gz")
    candidate_archive = args.output.with_suffix(".candidate.tar.gz")
    payload = {
        "suite": "redesign_promotion_v1",
        "reference_commit": REFERENCE,
        "started_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "logical_cpu_count": os.cpu_count(),
        "hardware_note": (
            "CPU model/RAM unavailable to collector; "
            "power/thermal/background state not controlled"
        ),
        "hash_seed": os.environ.get("PYTHONHASHSEED", "unspecified"),
        "repeat": args.repeat,
        "paired_sessions": args.pairs,
        "markov_limits": {
            "seconds": MARKOV_SECONDS,
            "ring_nodes": 5000,
            "scaling_nodes": 1000,
        },
        "policies": {
            "csp": "matched MRV and lexical values",
            "ring": "sequence variables; native objective-guided values",
            "scaling": "dom_wdeg and declared values, local versus auto bounds",
        },
        "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_sources": {
            "archive": reference_archive.name,
            "sha256": snapshot(args.reference, reference_archive),
        },
        "candidate_sources": {
            "archive": candidate_archive.name,
            "sha256": snapshot(ROOT, candidate_archive),
        },
        "comparisons": {},
    }

    def run(root, mode, case, memory=False):
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--checkout",
            str(root),
            "--case",
            case,
            "--mode",
            mode,
            "--repeat",
            str(args.repeat),
        ]
        if memory:
            command.append("--memory")
        return json.loads(subprocess.check_output(command, cwd=root, text=True))

    comparisons = [
        *(
            ("rules/" + case, args.reference, "rules", ROOT, "rules")
            for case in RULE_CASES
        ),
        *(
            (case, args.reference, "legacy", ROOT, "legacy")
            for case in (*JOIN_CASES, *CLASSICAL_CASES)
        ),
        *((case, args.reference, "legacy", ROOT, "native") for case in CSP_CASES),
        ("mixed_magic3", ROOT, "native", ROOT, "mixed"),
        *((case, args.reference, "legacy", ROOT, "native") for case in MARKOV_CASES),
        *(("scaling/" + case, ROOT, "local", ROOT, "auto") for case in SCALING_CASES),
    ]
    for label, left_root, left_mode, right_root, right_mode in comparisons:
        print(f"Comparing {label}", file=sys.stderr, flush=True)
        case = label
        paired = []
        for index in range(args.pairs):
            if index % 2 == 0:
                left = run(left_root, left_mode, case)
                right = run(right_root, right_mode, case)
            else:
                right = run(right_root, right_mode, case)
                left = run(left_root, left_mode, case)
            a, b = left["runs"][0]["observation"], right["runs"][0]["observation"]
            if case in CSP_CASES or case == "mixed_magic3":
                assert (a["output"], a["nodes"], a["failures"]) == (
                    b["output"],
                    b["nodes"],
                    b["failures"],
                )
            elif case.startswith(("rules/", "joins/", "classical/")):
                assert a == b
            else:
                if a["proved"] and b["proved"]:
                    assert a["objective"] == b["objective"]
            paired.append(
                {
                    "order": ["reference", "candidate"]
                    if index % 2 == 0
                    else ["candidate", "reference"],
                    "reference": left,
                    "candidate": right,
                }
            )
        payload["comparisons"][label] = {
            "reference_mode": left_mode,
            "candidate_mode": right_mode,
            "paired_sessions": paired,
            "reference_memory": run(left_root, left_mode, case, True),
            "candidate_memory": run(right_root, right_mode, case, True),
        }
        args.output.with_suffix(".partial.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
    assert snapshot(ROOT) == payload["candidate_sources"]["sha256"], (
        "candidate sources changed"
    )
    assert snapshot(args.reference) == payload["reference_sources"]["sha256"], (
        "reference sources changed"
    )
    payload["finished_at"] = datetime.now(UTC).isoformat()
    with args.output.open("x") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(args.output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--checkout", type=Path, default=ROOT)
    parser.add_argument("--case")
    parser.add_argument(
        "--mode", choices=("rules", "legacy", "native", "mixed", "local", "auto")
    )
    parser.add_argument("--memory", action="store_true")
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument("--pairs", type=int, default=3)
    parser.add_argument(
        "--reference", type=Path, default=Path("/tmp/snarky-redesign-reference-2fbdd9d")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeat < 1 or args.pairs < 1:
        parser.error("repeat and pairs must be positive")
    if args.worker:
        worker(args)
    else:
        collect(args)


if __name__ == "__main__":
    main()
