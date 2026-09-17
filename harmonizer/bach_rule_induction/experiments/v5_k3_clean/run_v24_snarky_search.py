#!/usr/bin/env python3
"""Search a short Bach-shaped lattice with learned V24 factors in Snarky."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import build_v22_constraint_ablation as v22_constraints
import k3
import numpy as np
import snarky_choice_bridge as bridge

from csp_solver import (
    FiniteCSP,
    PersistentConstraintPropagator,
    TableConstraint,
    assignment_from_solution,
    prepare_finite_csp_search,
)
from csp_solver.solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
)
from snarky import (
    Atom,
    ChoiceEventKind,
    ChoiceTraversal,
    Fact,
    FactorModel,
    FiniteSequence,
    ForwardEngine,
    Number,
    PriorityMRVChoicePolicy,
    Triple,
    evaluate_factor_model,
    parse_factor_groups,
)

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SCORE = HERE / "work/scores/bwv108.6.mxl"
DEFAULT_CATALOGUE = FACTOR_BASE / "v24_contrastive_full_factors.yaml"
DEFAULT_FACTOR_PROGRAM = FACTOR_BASE / "v24_contrastive_full.factors"
DEFAULT_OUTPUT = FACTOR_BASE / "v24_snarky_search_poc.json"
DEFAULT_REPORT = FACTOR_BASE / "V24_SNARKY_SEARCH_POC.md"

PROBLEM = Atom("learned_v24_snarky_harmonization")
K3_FACTOR_ACTIVE = Atom("k3_factor_active")
BLOCK_KIND = Atom("learned_satb_block")
WINDOW_KIND = Atom("learned_k3_window")

type PitchBlock = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class WindowRecord:
    """One complete K3 world and its learned energy components."""

    blocks: tuple[PitchBlock, PitchBlock, PitchBlock]
    term: FiniteSequence
    energy: float
    base_score: float
    factor_totals: tuple[int, ...]
    violated_constraints: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--blocks", type=int, default=6)
    parser.add_argument("--top-pitches", type=int, default=3)
    parser.add_argument("--max-nodes", type=int, default=100_000)
    parser.add_argument(
        "--traversal",
        choices=tuple(item.value for item in ChoiceTraversal),
        default=ChoiceTraversal.DEPTH_FIRST.value,
    )
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument(
        "--factor-program",
        type=Path,
        default=DEFAULT_FACTOR_PROGRAM,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def _block_term(block: PitchBlock) -> FiniteSequence:
    return FiniteSequence(tuple(Number(pitch) for pitch in block))


def _learned_constraint_features() -> tuple[tuple[str, k3.FeatureSpec], ...]:
    return tuple(
        (f"C-K3-V22-{index:03d}", feature)
        for index, (_, feature) in enumerate(
            v22_constraints.constraint_features(),
            start=1,
        )
    )


def _term_block(term: FiniteSequence) -> PitchBlock:
    values = tuple(
        int(item.value)
        for item in term.elements
        if isinstance(item, Number) and isinstance(item.value, int)
    )
    if len(values) != 4:
        raise TypeError("A block term must contain four integer pitches")
    return values[0], values[1], values[2], values[3]


def _top_pitch_pool(
    program: bridge.K3ChoiceProgram,
    lattice: k3.RhythmicLattice,
    voice: int,
    count: int,
) -> tuple[int, ...]:
    pitches = np.arange(
        program.candidate_min,
        program.candidate_max + 1,
        dtype=np.int16,
    )
    tonal = program.tonal_logits[
        voice,
        lattice.mode,
        (pitches - lattice.tonic_pc) % 12,
    ]
    scores = program.register_logits[voice] + tonal
    order = sorted(
        range(pitches.size),
        key=lambda index: (-float(scores[index]), int(pitches[index])),
    )
    return tuple(int(pitches[index]) for index in order[:count])


def _block_domains(
    lattice: k3.RhythmicLattice,
    program: bridge.K3ChoiceProgram,
    *,
    start: int,
    size: int,
    top_pitches: int,
) -> tuple[tuple[PitchBlock, ...], ...]:
    learned_pools = tuple(
        _top_pitch_pool(program, lattice, voice, top_pitches) for voice in range(1, 4)
    )
    boundary_requirements: list[list[set[int]]] = [
        [set() for _ in range(4)] for _ in range(size)
    ]
    for voice in range(1, 4):
        opening_pitch = int(lattice.blocks[start, voice])
        for local_time in range(1, size - 1):
            absolute_time = start + local_time
            if lattice.attacks[absolute_time, voice]:
                break
            boundary_requirements[local_time][voice].add(opening_pitch)
        final_time = start + size - 1
        if not lattice.attacks[final_time, voice]:
            closing_pitch = int(lattice.blocks[final_time, voice])
            for local_time in range(size - 2, 0, -1):
                boundary_requirements[local_time][voice].add(closing_pitch)
                absolute_next = start + local_time + 1
                if lattice.attacks[absolute_next, voice]:
                    break
    domains: list[tuple[PitchBlock, ...]] = []
    for local_time in range(size):
        absolute_time = start + local_time
        source = tuple(int(value) for value in lattice.blocks[absolute_time])
        if local_time in {0, size - 1}:
            domains.append((source,))
            continue
        soprano = source[0]
        lower_pools = tuple(
            tuple(
                dict.fromkeys(
                    (
                        *learned_pools[voice - 1],
                        *sorted(boundary_requirements[local_time][voice]),
                    )
                )
            )
            for voice in range(1, 4)
        )
        domains.append(
            tuple(
                (soprano, alto, tenor, bass)
                for alto, tenor, bass in product(*lower_pools)
            )
        )
    return tuple(domains)


def _holds_consistent(
    blocks: tuple[PitchBlock, PitchBlock, PitchBlock],
    attacks: np.ndarray,
    central: int,
) -> bool:
    previous, current, following = blocks
    return all(
        (attacks[central, voice] or current[voice] == previous[voice])
        and (attacks[central + 1, voice] or following[voice] == current[voice])
        for voice in range(4)
    )


def _world_dataset(
    worlds: tuple[tuple[PitchBlock, PitchBlock, PitchBlock], ...],
    lattice: k3.RhythmicLattice,
    *,
    central: int,
    candidate_min: int,
    candidate_max: int,
) -> tuple[k3.K3Dataset, np.ndarray]:
    voices = tuple(voice for voice in range(4) if lattice.attacks[central, voice])
    if not voices:
        raise ValueError("Every K3 centre needs at least one attack")
    row_blocks = np.asarray(
        [world for world in worlds for _ in voices],
        dtype=np.int16,
    )
    row_voices = np.asarray(voices * len(worlds), dtype=np.int8)
    dataset = k3.K3Dataset(
        piece_ids=np.full(row_voices.size, lattice.piece_id),
        offsets=np.tile(
            np.asarray(
                [
                    lattice.offsets[central - 1],
                    lattice.offsets[central],
                    lattice.offsets[central + 1],
                ],
                dtype=np.float32,
            ),
            (row_voices.size, 1),
        ),
        voice_indices=row_voices,
        blocks=row_blocks,
        attacks=np.tile(
            lattice.attacks[central - 1 : central + 2],
            (row_voices.size, 1, 1),
        ),
        candidate_min=candidate_min,
        candidate_max=candidate_max,
        tonic_pcs=np.full(row_voices.size, lattice.tonic_pc, dtype=np.int8),
        modes=np.full(row_voices.size, lattice.mode, dtype=np.int8),
        metric_levels=np.full(
            row_voices.size,
            lattice.metric_levels[central],
            dtype=np.int8,
        ),
    )
    groups = np.repeat(
        np.arange(len(worlds), dtype=np.int32),
        len(voices),
    )
    return dataset, groups


def _window_records(
    domains: tuple[tuple[PitchBlock, ...], ...],
    lattice: k3.RhythmicLattice,
    program: bridge.K3ChoiceProgram,
    constraint_rows: tuple[tuple[str, k3.FeatureSpec], ...],
    *,
    local_central: int,
    absolute_central: int,
) -> tuple[WindowRecord, ...]:
    worlds = tuple(
        blocks
        for blocks in product(
            domains[local_central - 1],
            domains[local_central],
            domains[local_central + 1],
        )
        if _holds_consistent(blocks, lattice.attacks, absolute_central)
    )
    if not worlds:
        raise ValueError(f"No hold-consistent world at block {absolute_central}")
    dataset, groups = _world_dataset(
        worlds,
        lattice,
        central=absolute_central,
        candidate_min=program.candidate_min,
        candidate_max=program.candidate_max,
    )
    world_ids = np.arange(len(worlds), dtype=np.int32)
    base_scores, factor_totals = k3._candidate_world_components(
        dataset,
        groups,
        candidates=world_ids,
        register_logits=program.register_logits,
        features=program.features,
        tonal_logits=program.tonal_logits,
    )
    energies = base_scores + factor_totals @ program.weights
    violations = [set() for _ in worlds]
    for constraint_id, feature in constraint_rows:
        active = k3.chosen_feature_values(dataset, feature)
        counts = np.bincount(
            groups,
            weights=active,
            minlength=len(worlds),
        )
        for index in np.flatnonzero(counts):
            violations[int(index)].add(constraint_id)
    return tuple(
        WindowRecord(
            blocks=world,
            term=FiniteSequence(tuple(_block_term(block) for block in world)),
            energy=float(energies[index]),
            base_score=float(base_scores[index]),
            factor_totals=tuple(int(round(value)) for value in factor_totals[index]),
            violated_constraints=tuple(sorted(violations[index])),
        )
        for index, world in enumerate(worlds)
    )


def _domain_facts(
    variable: Atom,
    kind: Atom,
    values: tuple[FiniteSequence, ...],
) -> tuple[Fact, ...]:
    return (
        Fact(Triple(PROBLEM, VARIABLE, variable)),
        Fact(Triple(variable, KIND, CSP_VARIABLE)),
        Fact(Triple(variable, KIND, kind)),
        *(Fact(Triple(variable, CANDIDATE, value)) for value in values),
    )


def _build_model(
    lattice: k3.RhythmicLattice,
    program: bridge.K3ChoiceProgram,
    *,
    start: int,
    size: int,
    top_pitches: int,
) -> tuple[
    FiniteCSP,
    tuple[Atom, ...],
    tuple[Atom, ...],
    dict[tuple[int, FiniteSequence], WindowRecord],
]:
    domains = _block_domains(
        lattice,
        program,
        start=start,
        size=size,
        top_pitches=top_pitches,
    )
    block_variables = tuple(Atom(f"v24_block_{time}") for time in range(size))
    window_variables = tuple(Atom(f"v24_window_{time}") for time in range(1, size - 1))
    constraints: list[TableConstraint] = []
    facts: list[Fact] = [Fact(Triple(PROBLEM, KIND, CSP_PROBLEM))]
    weights: dict[tuple[Atom, FiniteSequence], float] = {}
    for variable, domain in zip(block_variables, domains, strict=True):
        values = tuple(_block_term(block) for block in domain)
        facts.extend(_domain_facts(variable, BLOCK_KIND, values))
        weights.update(((variable, value), 1.0) for value in values)
    constraint_rows = _learned_constraint_features()
    record_by_term: dict[tuple[int, FiniteSequence], WindowRecord] = {}
    for local_central, window_variable in enumerate(
        window_variables,
        start=1,
    ):
        absolute_central = start + local_central
        records = _window_records(
            domains,
            lattice,
            program,
            constraint_rows,
            local_central=local_central,
            absolute_central=absolute_central,
        )
        window_values = tuple(record.term for record in records)
        facts.extend(_domain_facts(window_variable, WINDOW_KIND, window_values))
        maximum = max(record.energy for record in records)
        for record in records:
            weights[(window_variable, record.term)] = math.exp(record.energy - maximum)
            record_by_term[(local_central, record.term)] = record
        previous, current, following = block_variables[
            local_central - 1 : local_central + 2
        ]
        constraints.append(
            TableConstraint(
                Atom(f"K3-V24-FACTOR-CHANNEL-{absolute_central}"),
                (previous, current, following, window_variable),
                tuple(
                    (
                        _block_term(record.blocks[0]),
                        _block_term(record.blocks[1]),
                        _block_term(record.blocks[2]),
                        record.term,
                    )
                    for record in records
                ),
            )
        )
        block_rows = tuple(
            tuple(_block_term(block) for block in record.blocks) for record in records
        )
        constraints.append(
            TableConstraint(
                Atom(f"STRUCTURAL-HOLD-{absolute_central}"),
                (previous, current, following),
                block_rows,
            )
        )
        for constraint_id, _ in constraint_rows:
            allowed = tuple(
                row
                for row, record in zip(block_rows, records, strict=True)
                if constraint_id not in record.violated_constraints
            )
            if not allowed:
                raise ValueError(
                    f"{constraint_id} rejects every world at block {absolute_central}"
                )
            constraints.append(
                TableConstraint(
                    Atom(f"{constraint_id}-T{absolute_central}"),
                    (previous, current, following),
                    allowed,
                )
            )
    return (
        FiniteCSP(
            PROBLEM,
            tuple(facts),
            weights,
            constraints=tuple(constraints),
        ),
        block_variables,
        window_variables,
        record_by_term,
    )


def _snarky_factor_score(
    factor_model: FactorModel,
    program: bridge.K3ChoiceProgram,
    factor_totals: tuple[int, ...],
    *,
    window: int,
) -> float:
    facts = tuple(
        Fact(
            Triple(
                FiniteSequence(
                    (
                        Number(window),
                        Atom(factor.id),
                        Number(instance),
                    )
                ),
                K3_FACTOR_ACTIVE,
                Atom(factor.id),
            )
        )
        for factor, count in zip(
            program.factors,
            factor_totals,
            strict=True,
        )
        for instance in range(count)
    )
    return evaluate_factor_model(factor_model, facts).log_score


def _root_propagation_diagnostics(model: FiniteCSP) -> dict[str, Any]:
    """Measure constraint filtering before the first search decision."""

    session = ForwardEngine(()).create_session(model.facts)
    initial_candidates = sum(
        isinstance(fact.entity, Triple) and fact.entity.relation == CANDIDATE
        for fact in session.facts
    )
    propagator = PersistentConstraintPropagator(
        model.problem,
        model.constraints,
    )
    propagator(session)
    explanations = propagator.removal_explanations(session)
    removals_by_constraint: dict[str, int] = {}
    for explanation in explanations:
        name = explanation.constraint.name
        removals_by_constraint[name] = removals_by_constraint.get(name, 0) + 1
    return {
        "initial_candidates": initial_candidates,
        "remaining_candidates": initial_candidates - len(explanations),
        "candidate_removals": len(explanations),
        "by_constraint": [
            {
                "constraint": constraint,
                "removed_candidates": count,
            }
            for constraint, count in sorted(
                removals_by_constraint.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    }


def _markdown(result: dict[str, Any]) -> str:
    search = result["search"]
    propagation = result["propagation"]
    backtrack_interpretation = (
        "Des branches incompatibles ont été détectées puis annulées."
        if search["backtracks"]
        else (
            (
                "Aucun retour arrière n'a été nécessaire : les contraintes "
                "persistantes ont supprimé les valeurs incompatibles avant "
                "qu'elles deviennent des décisions."
            )
            if propagation["candidate_removals"]
            else (
                "Aucun retour arrière n'a été nécessaire et aucune valeur "
                "n'a été filtrée à la racine : la première branche pondérée "
                "est restée compatible jusqu'à la solution."
            )
        )
    )
    lines = [
        "# V24 — POC de génération par recherche Snarky",
        "",
        "Ce POC n'utilise pas Gibbs pour générer. Les facteurs appris V24",
        "pondèrent des variables de fenêtre K3. Les 23 prédicats V22 sans",
        "exception en apprentissage et validation sont des contraintes",
        "persistantes empiriques (et non des lois universelles). Snarky",
        "alterne propagation, choix et rollback lorsque celui-ci est requis.",
        "",
        "## Résultat",
        "",
        f"- Statut : `{search['status']}`.",
        f"- Nœuds explorés : `{search['explored_nodes']}`.",
        f"- Branches en échec : `{search['failed_branches']}`.",
        f"- Décisions sur la branche solution : `{search['decisions']}`.",
        f"- Événements `BACKTRACK` : `{search['backtracks']}`.",
        f"- Parcours : `{search['traversal']}`.",
        f"- Valeurs éliminées à la racine par propagation : "
        f"`{propagation['candidate_removals']}`.",
        f"- Valeurs candidates avant/après propagation : "
        f"`{propagation['initial_candidates']}` / "
        f"`{propagation['remaining_candidates']}`.",
        f"- Contraintes apprises persistantes : "
        f"`{result['model']['learned_constraints']}`.",
        f"- Instances locales de ces contraintes : "
        f"`{result['model']['learned_constraint_instances']}`.",
        f"- Facteurs appris : `{result['model']['factor_count']}`.",
        f"- Erreur maximale du score factoriel Snarky : "
        f"`{result['factor_parity']['maximum_absolute_error']:.3e}`.",
        "",
        backtrack_interpretation,
        "",
        "## Blocs",
        "",
        "| Bloc | Offset | Métrique | Soprano | Alto | Ténor | Basse |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["solution"]["blocks"]:
        pitches = row["pitches"]
        lines.append(
            f"| {row['local_time']} | {row['offset']:.2f} | "
            f"{row['metric_level']} | {pitches[0]} | {pitches[1]} | "
            f"{pitches[2]} | {pitches[3]} |"
        )
    lines.extend(
        [
            "",
            "## Éliminations par propagation",
            "",
            "| Contrainte | Valeurs supprimées |",
            "|---|---:|",
        ]
    )
    for row in propagation["by_constraint"]:
        lines.append(f"| `{row['constraint']}` | {row['removed_candidates']} |")
    if not propagation["by_constraint"]:
        lines.append("| _aucune_ | 0 |")
    lines.extend(
        [
            "",
            "## Décisions de la solution",
            "",
            "| # | Point de choix | Alternative | Poids |",
            "|---:|---|---|---:|",
        ]
    )
    for index, decision in enumerate(result["solution"]["decisions"], start=1):
        lines.append(
            f"| {index} | `{decision['point']}` | "
            f"`{decision['alternative']}` | {decision['weight']:.6g} |"
        )
    lines.extend(
        [
            "",
            "## Impasses et retours arrière",
            "",
        ]
    )
    if search["failure_trace"]:
        lines.extend(
            [
                "| # | Événement | Profondeur | Point | Alternative | Détail |",
                "|---:|---|---:|---|---|---|",
            ]
        )
        for event in search["failure_trace"]:
            lines.append(
                f"| {event['sequence']} | `{event['kind']}` | "
                f"{event['depth']} | `{event['point']}` | "
                f"`{event['alternative']}` | {event['detail']} |"
            )
    else:
        lines.append("Aucune impasse n'a été rencontrée sur cette recherche.")
    lines.extend(
        [
            "",
            "## Limites de ce POC",
            "",
            "Les blocs de bord sont conservés comme conditions aux limites ;",
            "le soprano et le rythme sont donnés. Les domaines intérieurs sont",
            "obtenus uniquement à partir des priors de registre et de tonalité",
            "appris, sans recopier les voix intérieures de Bach.",
            "",
            "Le petit domaine `top-pitches` est un échafaudage de validation,",
            "pas encore la base générative finale. Une solution répétitive",
            "indique une lacune du modèle appris ou du domaine, et non une",
            "absence de propagation/backtracking dans Snarky.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.blocks < 3:
        raise ValueError("The POC needs at least three blocks")
    program = bridge.load_choice_program(args.catalogue)
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    if args.start < 0 or args.start + args.blocks > lattice.blocks.shape[0]:
        raise ValueError("The requested fragment lies outside the lattice")
    model, block_variables, window_variables, records = _build_model(
        lattice,
        program,
        start=args.start,
        size=args.blocks,
        top_pitches=args.top_pitches,
    )
    propagation_diagnostics = _root_propagation_diagnostics(model)
    priorities = {
        **{variable: index for index, variable in enumerate(window_variables)},
        **{variable: 100 for variable in block_variables},
    }
    traversal = ChoiceTraversal(args.traversal)
    prepared = prepare_finite_csp_search(
        model,
        max_solutions=1,
        max_nodes=args.max_nodes,
        policy=PriorityMRVChoicePolicy(priorities),
        traversal=traversal,
    )
    result = prepared.solve()
    if not result.solutions:
        raise ValueError(f"Snarky search ended without solution: {result.status}")
    solution = result.solutions[0]
    assignment = assignment_from_solution(solution, PROBLEM)
    selected_blocks = tuple(
        _term_block(assignment[variable]) for variable in block_variables
    )
    (factor_group,) = parse_factor_groups(
        args.factor_program.read_text(encoding="utf-8")
    )
    factor_model = FactorModel("K3-V24-SEARCH-POC", (factor_group,))
    parity_errors = []
    window_rows = []
    for local_central, variable in enumerate(window_variables, start=1):
        record = records[(local_central, assignment[variable])]
        source_factor_score = float(np.dot(record.factor_totals, program.weights))
        snarky_score = _snarky_factor_score(
            factor_model,
            program,
            record.factor_totals,
            window=local_central,
        )
        parity_errors.append(abs(source_factor_score - snarky_score))
        window_rows.append(
            {
                "local_central": local_central,
                "absolute_central": args.start + local_central,
                "energy": record.energy,
                "base_score": record.base_score,
                "factor_score": source_factor_score,
                "snarky_factor_score": snarky_score,
                "active_factor_instances": int(sum(record.factor_totals)),
            }
        )
    interesting = {
        ChoiceEventKind.CONTRADICTION,
        ChoiceEventKind.BACKTRACK,
        ChoiceEventKind.DEAD_END,
    }
    failure_trace = [
        {
            "sequence": event.sequence,
            "kind": event.kind.value,
            "depth": event.depth,
            "point": event.point,
            "alternative": event.alternative,
            "detail": event.detail,
        }
        for event in result.events
        if event.kind in interesting
    ]
    payload = {
        "experiment": {
            "id": "K3-V24-SNARKY-SEARCH-POC-1",
            "status": "SOLVED",
            "gibbs_used_for_generation": False,
            "historical_rules_loaded": False,
            "test_loaded": False,
        },
        "fragment": {
            "piece_id": args.piece_id,
            "start": args.start,
            "blocks": args.blocks,
            "boundary_blocks_fixed": True,
            "soprano_fixed": True,
            "rhythm_fixed": True,
            "top_pitches_per_lower_voice": args.top_pitches,
        },
        "model": {
            "factor_catalogue": str(args.catalogue.resolve()),
            "factor_program": str(args.factor_program.resolve()),
            "factor_count": len(program.factors),
            "learned_constraints": len(_learned_constraint_features()),
            "learned_constraint_instances": (
                len(_learned_constraint_features()) * len(window_variables)
            ),
            "persistent_table_constraints": len(model.constraints),
            "block_variables": len(block_variables),
            "window_variables": len(window_variables),
        },
        "search": {
            "status": result.status.value,
            "traversal": traversal.value,
            "explored_nodes": result.explored_nodes,
            "failed_branches": result.failed_branches,
            "decisions": len(solution.decisions),
            "backtracks": sum(
                event.kind is ChoiceEventKind.BACKTRACK for event in result.events
            ),
            "failure_trace": failure_trace,
        },
        "propagation": propagation_diagnostics,
        "solution": {
            "log_weight": solution.log_weight,
            "decisions": [
                {
                    "point": decision.point,
                    "alternative": decision.alternative,
                    "weight": decision.weight,
                }
                for decision in solution.decisions
            ],
            "blocks": [
                {
                    "local_time": local_time,
                    "absolute_time": args.start + local_time,
                    "offset": float(lattice.offsets[args.start + local_time]),
                    "metric_level": int(lattice.metric_levels[args.start + local_time]),
                    "attacks": lattice.attacks[args.start + local_time]
                    .astype(int)
                    .tolist(),
                    "pitches": list(block),
                }
                for local_time, block in enumerate(selected_blocks)
            ],
            "windows": window_rows,
        },
        "factor_parity": {
            "maximum_absolute_error": max(parity_errors, default=0.0),
            "tolerance": 1e-12,
            "status": ("PASS" if max(parity_errors, default=0.0) <= 1e-12 else "FAIL"),
        },
    }
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    print(
        f"[v24-snarky-search] status={result.status.value} "
        f"nodes={result.explored_nodes} failed={result.failed_branches} "
        f"backtracks={payload['search']['backtracks']}",
        flush=True,
    )
    print(
        f"[v24-snarky-search] factor parity "
        f"{payload['factor_parity']['maximum_absolute_error']:.3e}",
        flush=True,
    )
    print(f"[v24-snarky-search] wrote {args.output}", flush=True)
    print(f"[v24-snarky-search] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
