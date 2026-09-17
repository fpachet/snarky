#!/usr/bin/env python3
"""Run the first learned-score-floor Snarky backtracking experiment."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import k3
import numpy as np
import run_rhythmic_gibbs as muses_export
import run_v24_snarky_search as search_poc
import snarky_choice_bridge as bridge

from csp_solver import assignment_from_solution, prepare_finite_csp_search
from csp_solver.solver import (
    CANDIDATE,
    CONTRADICTION,
    STATE,
    VIOLATED_CONSTRAINT,
)
from snarky import (
    Atom,
    ChoiceEventKind,
    ChoiceTraversal,
    Fact,
    FiniteSequence,
    PriorityMRVChoicePolicy,
    Triple,
)

HERE = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[4]
FACTOR_BASE = REPOSITORY / "harmonizer/bach_rule_induction/factor_bases/k3_v6_induced"
DEFAULT_SCORE = HERE / "work/scores/bwv108.6.mxl"
DEFAULT_MODEL = FACTOR_BASE / "v23_metric_harmony_full_model.json"
DEFAULT_CATALOGUE = FACTOR_BASE / "v23_metric_harmony_full_factors.yaml"
DEFAULT_CACHE = HERE / "work/k3-exact-v24-selected-32x10.npz"
DEFAULT_OUTPUT = FACTOR_BASE / "two_loop_score_floor_experiment.json"
DEFAULT_REPORT = FACTOR_BASE / "TWO_LOOP_SCORE_FLOOR_EXPERIMENT.md"
DEFAULT_GENERATED = REPOSITORY / "harmonizer/generated"
DEFAULT_MUSICXML = DEFAULT_GENERATED / "two_loop_score_floor_bwv108_6.musicxml"
DEFAULT_MIDI = DEFAULT_GENERATED / "two_loop_score_floor_bwv108_6.mid"

SCORE_FLOOR = Atom("minimum_learned_sequence_score")


@dataclass(frozen=True, slots=True)
class Calibration:
    """Exact pseudo-likelihood score distribution and frozen floor."""

    threshold: float
    split: str
    policy: str
    piece_scores: tuple[tuple[str, float, int], ...]
    decision_mean: float


@dataclass(frozen=True, slots=True)
class SequenceScore:
    """One exact conditional sequence score."""

    total: float
    mean: float
    contributions: tuple[tuple[tuple[int, int, int], float], ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--piece-id", default="bach/bwv108.6")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--blocks", type=int, default=6)
    parser.add_argument("--top-pitches", type=int, default=3)
    parser.add_argument("--max-nodes", type=int, default=100_000)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--calibration-cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--calibration-split",
        choices=("train", "validation"),
        default="validation",
    )
    parser.add_argument(
        "--threshold-policy",
        choices=("strict_minimum", "q01", "q05", "q10"),
        default="strict_minimum",
    )
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--musicxml", type=Path, default=DEFAULT_MUSICXML)
    parser.add_argument("--midi", type=Path, default=DEFAULT_MIDI)
    parser.add_argument("--no-export", action="store_true")
    return parser.parse_args()


def _model_program(
    model_path: Path,
    catalogue_path: Path,
) -> bridge.K3ChoiceProgram:
    model = json.loads(model_path.read_text(encoding="utf-8"))
    if model["experiment"]["test_loaded"]:
        raise ValueError("The MLE model unexpectedly loaded the sealed test")
    program = bridge.load_choice_program(catalogue_path)
    rules = model["model"]["rules"]
    model_keys = [row["feature"]["key"] for row in rules]
    program_keys = [feature.key for feature in program.features]
    if model_keys != program_keys:
        raise ValueError("MLE model and factor catalogue disagree")
    model_weights = np.asarray(
        [float(row["weight"]) for row in rules],
        dtype=np.float64,
    )
    if not np.allclose(model_weights, program.weights, atol=1e-12, rtol=0):
        raise ValueError("MLE model and factor catalogue weights disagree")
    return program


def _candidate_base_scores(
    program: bridge.K3ChoiceProgram,
    voices: np.ndarray,
    modes: np.ndarray,
    tonics: np.ndarray,
) -> np.ndarray:
    pitches = np.arange(
        program.candidate_min,
        program.candidate_max + 1,
        dtype=np.int16,
    )
    relative = (pitches[None, :] - tonics[:, None]) % 12
    return (
        program.register_logits[voices]
        + program.tonal_logits[
            voices[:, None],
            modes[:, None],
            relative,
        ]
    )


def _row_log_probabilities(
    base: np.ndarray,
    factors: np.ndarray,
    chosen: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    logits = base + np.tensordot(
        factors.astype(np.float64),
        weights,
        axes=([2], [0]),
    )
    maximum = logits.max(axis=1, keepdims=True)
    shifted = logits - maximum
    normalizers = np.log(np.exp(shifted).sum(axis=1))
    return shifted[np.arange(chosen.size), chosen] - normalizers


def calibrate_threshold(
    cache_path: Path,
    program: bridge.K3ChoiceProgram,
    *,
    split: str,
    policy: str,
    override: float | None,
) -> Calibration:
    """Calibrate a sequence score floor from exact cached conditionals."""

    archive = np.load(cache_path, allow_pickle=False)
    metadata = json.loads(str(archive["metadata"]))
    feature_keys = metadata["feature_keys"]
    expected = [feature.key for feature in program.features]
    if feature_keys[: len(expected)] != expected:
        raise ValueError("Calibration cache and MLE features disagree")
    factors = archive[f"{split}_factors"][:, :, : len(expected)]
    chosen = archive[f"{split}_chosen"]
    voices = archive[f"{split}_voices"]
    modes = archive[f"{split}_modes"]
    tonics = archive[f"{split}_tonics"]
    piece_ids = archive[f"{split}_piece_ids"]
    base = _candidate_base_scores(program, voices, modes, tonics)
    log_probabilities = _row_log_probabilities(
        base,
        factors,
        chosen,
        program.weights,
    )
    piece_scores = tuple(
        sorted(
            (
                str(piece_id),
                float(log_probabilities[piece_ids == piece_id].mean()),
                int(np.sum(piece_ids == piece_id)),
            )
            for piece_id in np.unique(piece_ids)
        )
    )
    scores = np.asarray([row[1] for row in piece_scores])
    quantiles = {
        "strict_minimum": 0.0,
        "q01": 0.01,
        "q05": 0.05,
        "q10": 0.10,
    }
    threshold = (
        float(override)
        if override is not None
        else float(np.quantile(scores, quantiles[policy]))
    )
    return Calibration(
        threshold=threshold,
        split=split,
        policy=("override" if override is not None else policy),
        piece_scores=piece_scores,
        decision_mean=float(log_probabilities.mean()),
    )


def _required_calibration_coverage(policy: str, piece_count: int) -> int:
    quantiles = {
        "strict_minimum": 0.0,
        "q01": 0.01,
        "q05": 0.05,
        "q10": 0.10,
    }
    if policy == "override":
        return 0
    return piece_count - math.ceil(quantiles[policy] * piece_count)


def _eligible_segments(attacks: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    size = attacks.shape[0]
    return tuple(
        segment
        for segment in k3.attack_segments(attacks)
        if segment[2] != 0 and segment[0] > 0 and segment[1] < size
    )


def _required_times(
    segment: tuple[int, int, int],
    size: int,
) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                time
                for central in k3.segment_energy_times(segment, size)
                for time in (central - 1, central, central + 1)
            }
        )
    )


def _segment_log_probability(
    blocks: np.ndarray,
    attacks: np.ndarray,
    metric_levels: np.ndarray,
    segment: tuple[int, int, int],
    program: bridge.K3ChoiceProgram,
    *,
    tonic_pc: int,
    mode: int,
) -> float:
    candidates = np.arange(
        program.candidate_min,
        program.candidate_max + 1,
        dtype=np.int16,
    )
    start, end, voice = segment
    base, totals = k3.candidate_segment_components(
        blocks,
        attacks,
        k3.segment_energy_times(segment, blocks.shape[0]),
        start,
        end,
        voice,
        candidates,
        candidate_min=program.candidate_min,
        candidate_max=program.candidate_max,
        register_logits=program.register_logits,
        features=program.features,
        tonal_logits=program.tonal_logits,
        tonic_pc=tonic_pc,
        mode=mode,
        metric_levels=metric_levels,
    )
    logits = base + totals @ program.weights
    chosen = int(blocks[start, voice]) - program.candidate_min
    if chosen < 0 or chosen >= candidates.size:
        return -math.inf
    maximum = float(np.max(logits))
    return float(logits[chosen] - maximum - np.log(np.exp(logits - maximum).sum()))


class MinimumLearnedScorePropagator:
    """Reject branches that can no longer reach the learned score floor."""

    watched_relations = frozenset((CANDIDATE,))

    def __init__(
        self,
        *,
        problem: Atom,
        block_variables: tuple[Atom, ...],
        source_blocks: np.ndarray,
        attacks: np.ndarray,
        metric_levels: np.ndarray,
        program: bridge.K3ChoiceProgram,
        tonic_pc: int,
        mode: int,
        threshold: float,
    ) -> None:
        self.problem = problem
        self.block_variables = block_variables
        self.source_blocks = np.asarray(source_blocks, dtype=np.int16)
        self.attacks = np.asarray(attacks, dtype=bool)
        self.metric_levels = np.asarray(metric_levels, dtype=np.int8)
        self.program = program
        self.tonic_pc = tonic_pc
        self.mode = mode
        self.threshold = threshold
        self.segments = _eligible_segments(self.attacks)
        self.required = {
            segment: _required_times(segment, self.attacks.shape[0])
            for segment in self.segments
        }
        self._score_cache: dict[
            tuple[tuple[int, int, int], tuple[search_poc.PitchBlock, ...]],
            float,
        ] = {}
        self.rejections: list[dict[str, Any]] = []

    def _fixed_blocks(
        self,
        session: Any,
    ) -> dict[int, search_poc.PitchBlock]:
        domains: dict[Atom, list[FiniteSequence]] = {
            variable: [] for variable in self.block_variables
        }
        for fact in session.facts:
            entity = fact.entity
            if (
                isinstance(entity, Triple)
                and entity.relation == CANDIDATE
                and entity.subject in domains
                and isinstance(entity.object, FiniteSequence)
            ):
                domains[entity.subject].append(entity.object)
        return {
            index: search_poc._term_block(values[0])
            for index, variable in enumerate(self.block_variables)
            if len(values := domains[variable]) == 1
        }

    def _score_segment(
        self,
        segment: tuple[int, int, int],
        fixed: dict[int, search_poc.PitchBlock],
    ) -> float:
        required = self.required[segment]
        key_blocks = tuple(fixed[time] for time in required)
        key = (segment, key_blocks)
        cached = self._score_cache.get(key)
        if cached is not None:
            return cached
        blocks = self.source_blocks.copy()
        for time, block in fixed.items():
            blocks[time] = block
        value = _segment_log_probability(
            blocks,
            self.attacks,
            self.metric_levels,
            segment,
            self.program,
            tonic_pc=self.tonic_pc,
            mode=self.mode,
        )
        self._score_cache[key] = value
        return value

    def evaluate_fixed(
        self,
        fixed: dict[int, search_poc.PitchBlock],
    ) -> tuple[float, int]:
        total = 0.0
        scored = 0
        for segment in self.segments:
            if all(time in fixed for time in self.required[segment]):
                total += self._score_segment(segment, fixed)
                scored += 1
        return total, scored

    def evaluate_blocks(self, blocks: np.ndarray) -> SequenceScore:
        fixed = {
            time: tuple(int(value) for value in block)
            for time, block in enumerate(blocks)
        }
        rows = tuple(
            (segment, self._score_segment(segment, fixed)) for segment in self.segments
        )
        total = float(sum(value for _, value in rows))
        return SequenceScore(
            total=total,
            mean=total / len(rows),
            contributions=rows,
        )

    def __call__(self, session: Any) -> None:
        contradiction = Fact(Triple(self.problem, STATE, CONTRADICTION))
        if contradiction in session.facts:
            return
        fixed = self._fixed_blocks(session)
        fixed_total, scored = self.evaluate_fixed(fixed)
        required_total = self.threshold * len(self.segments)
        # Every unresolved log-probability is at most zero. The fixed total is
        # therefore a valid optimistic upper bound for every completion.
        if fixed_total + 1e-12 >= required_total:
            return
        self.rejections.append(
            {
                "fixed_blocks": len(fixed),
                "scored_segments": scored,
                "segment_count": len(self.segments),
                "optimistic_total": fixed_total,
                "required_total": required_total,
                "optimistic_mean_if_complete": (fixed_total / len(self.segments)),
            }
        )
        session.assume(
            contradiction,
            Fact(Triple(self.problem, VIOLATED_CONSTRAINT, SCORE_FLOOR)),
            label="constraint:minimum_learned_sequence_score",
        )


def _score_payload(score: SequenceScore) -> dict[str, Any]:
    return {
        "total": score.total,
        "mean": score.mean,
        "contributions": [
            {
                "start": segment[0],
                "end": segment[1],
                "voice": segment[2],
                "log_probability": value,
            }
            for segment, value in score.contributions
        ],
    }


def _fragment_lattice(
    lattice: k3.RhythmicLattice,
    blocks: np.ndarray,
    *,
    start: int,
) -> k3.RhythmicLattice:
    end = start + blocks.shape[0]
    origin = float(lattice.offsets[start])
    end_offset = (
        float(lattice.offsets[end]) if end < lattice.size else lattice.end_offset
    )
    return k3.RhythmicLattice(
        piece_id=lattice.piece_id,
        offsets=lattice.offsets[start:end] - origin,
        blocks=blocks,
        attacks=lattice.attacks[start:end],
        end_offset=end_offset - origin,
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        metric_levels=lattice.metric_levels[start:end],
    )


def _export_solution(
    *,
    source_path: Path,
    lattice: k3.RhythmicLattice,
    blocks: np.ndarray,
    start: int,
    musicxml_path: Path,
    midi_path: Path,
) -> None:
    from music21 import converter

    source_score = converter.parse(source_path)
    metadata = muses_export._source_score_metadata(source_score)
    fragment = _fragment_lattice(lattice, blocks, start=start)
    piece = muses_export._materialize_muses_piece(
        fragment,
        blocks,
        title="Première expérience Snarky à score minimal appris",
        composer="Snarky / MuSES",
        score_metadata=metadata,
    )
    musicxml_path.parent.mkdir(parents=True, exist_ok=True)
    midi_path.parent.mkdir(parents=True, exist_ok=True)
    muses_export._write_muses_exports(piece, musicxml_path, midi_path)


def _markdown(payload: dict[str, Any]) -> str:
    calibration = payload["calibration"]
    search = payload["search"]
    comparison = payload["comparison"]
    checks = payload["checks"]
    lines = [
        "# Première expérience des deux boucles — score minimal appris",
        "",
        "Les 57 facteurs V23 et leurs poids proviennent du MLE conditionnel",
        "conjoint. Le threshold est calibré sur les pseudo-vraisemblances",
        "exactes par choral. Gibbs n'est pas utilisé pour générer.",
        "",
        "## Calibration",
        "",
        f"- Split : `{calibration['split']}`.",
        f"- Politique : `{calibration['policy']}`.",
        f"- Chorals : `{calibration['piece_count']}`.",
        f"- Couverture : `{calibration['accepted_piece_count']}/"
        f"{calibration['piece_count']}`.",
        f"- Threshold moyen : `{calibration['threshold']:.6f}`.",
        f"- Moyenne par décision : `{calibration['decision_mean']:.6f}`.",
        "",
        "## Recherche Snarky",
        "",
        f"- Statut : `{search['status']}`.",
        f"- Nœuds explorés : `{search['explored_nodes']}`.",
        f"- Branches en échec : `{search['failed_branches']}`.",
        f"- Contradictions de score : `{search['score_rejections']}`.",
        f"- Dont contradictions avant assignation complète : "
        f"`{search['early_score_rejections']}`.",
        f"- Backtracks : `{search['backtracks']}`.",
        f"- Solutions : `{search['solution_count']}`.",
        f"- Verdict du protocole : `{checks['status']}`.",
        "",
        "## Comparaison contrôlée",
        "",
        f"- Première solution sans seuil : "
        f"`{comparison['without_floor']['score']['mean']:.6f}`.",
        f"- Bach authentique (diagnostic seulement) : "
        f"`{comparison['bach_reference']['score']['mean']:.6f}`.",
    ]
    if payload.get("solution"):
        solution = payload["solution"]
        lines.extend(
            [
                f"- Score de la solution : `{solution['score']['mean']:.6f}`.",
                f"- Marge au threshold : "
                f"`{solution['score']['mean'] - calibration['threshold']:+.6f}`.",
                "",
                "## Blocs retenus",
                "",
                "| Bloc | Soprano | Alto | Ténor | Basse |",
                "|---:|---:|---:|---:|---:|",
            ]
        )
        for index, block in enumerate(solution["blocks"]):
            lines.append(
                f"| {index} | {block[0]} | {block[1]} | {block[2]} | {block[3]} |"
            )
    lines.extend(
        [
            "",
            "## Limites observées",
            "",
            "- Le threshold est calibré sur dix chorals complets, tandis que la",
            "  recherche porte ici sur un fragment court de huit décisions.",
            "- Les 23 filtres V22 restent des contraintes empiriques pré-test.",
            "- Sur six blocs, les portées exactes se recouvrent toutes : les 21",
            "  contradictions apparaissent après assignation complète.",
            "- La solution acceptée est très répétitive : V23 manque donc encore",
            "  un détecteur ou un seuil de groupe pour cette pathologie.",
            "",
            "## Interprétation",
            "",
            "Une branche est rejetée lorsque la somme de ses contributions",
            "déjà fixées est inférieure au score total requis, même en donnant",
            "la contribution maximale zéro à toutes les décisions restantes.",
            "Il s'agit d'une contrainte de satisfaction, pas d'une recherche du",
            "maximum global.",
            "",
            "Le seuil élimine bien la première solution, mais la solution",
            "acceptée reste très répétitive. Cela prouve le mécanisme de",
            "backtracking tout en révélant que le score global V23 ne détecte",
            "pas encore toutes les mauvaises solutions musicales.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.blocks < 3:
        raise ValueError("The experiment needs at least three blocks")
    program = _model_program(args.model, args.catalogue)
    calibration = calibrate_threshold(
        args.calibration_cache,
        program,
        split=args.calibration_split,
        policy=args.threshold_policy,
        override=args.threshold,
    )
    lattice = k3.extract_piece_lattice(args.score, args.piece_id)
    end = args.start + args.blocks
    if args.start < 0 or end > lattice.size:
        raise ValueError("The requested fragment lies outside the lattice")
    model, block_variables, window_variables, _ = search_poc._build_model(
        lattice,
        program,
        start=args.start,
        size=args.blocks,
        top_pitches=args.top_pitches,
    )
    hard_constraint_diagnostics = search_poc._root_propagation_diagnostics(model)
    source_blocks = lattice.blocks[args.start : end]
    attacks = lattice.attacks[args.start : end]
    metric_levels = lattice.metric_levels[args.start : end]
    score_floor = MinimumLearnedScorePropagator(
        problem=search_poc.PROBLEM,
        block_variables=block_variables,
        source_blocks=source_blocks,
        attacks=attacks,
        metric_levels=metric_levels,
        program=program,
        tonic_pc=lattice.tonic_pc,
        mode=lattice.mode,
        threshold=calibration.threshold,
    )
    priorities = {
        **{variable: index for index, variable in enumerate(window_variables)},
        **{variable: 100 for variable in block_variables},
    }
    baseline_prepared = prepare_finite_csp_search(
        model,
        max_solutions=1,
        max_nodes=args.max_nodes,
        policy=PriorityMRVChoicePolicy(priorities),
        traversal=ChoiceTraversal.DEPTH_FIRST,
    )
    baseline_result = baseline_prepared.solve()
    if not baseline_result.solutions:
        raise ValueError("The control search without a score floor failed")
    baseline_assignment = assignment_from_solution(
        baseline_result.solutions[0],
        search_poc.PROBLEM,
    )
    baseline_blocks = np.asarray(
        [
            search_poc._term_block(baseline_assignment[variable])
            for variable in block_variables
        ],
        dtype=np.int16,
    )
    baseline_score = score_floor.evaluate_blocks(baseline_blocks)
    reference_score = score_floor.evaluate_blocks(source_blocks)
    prepared = prepare_finite_csp_search(
        model,
        max_solutions=1,
        max_nodes=args.max_nodes,
        policy=PriorityMRVChoicePolicy(priorities),
        traversal=ChoiceTraversal.DEPTH_FIRST,
    )
    scored_search = replace(
        prepared.search,
        propagators=(*prepared.search.propagators, score_floor),
    )
    result = scored_search.solve(prepared.session)
    backtracks = sum(event.kind is ChoiceEventKind.BACKTRACK for event in result.events)
    payload: dict[str, Any] = {
        "experiment": {
            "id": "K3-TWO-LOOP-SCORE-FLOOR-1",
            "status": "METHOD_VALIDATION",
            "model": str(args.model.resolve()),
            "catalogue": str(args.catalogue.resolve()),
            "factor_count": len(program.factors),
            "weight_estimator": "joint_conditional_mle",
            "gibbs_used_for_generation": False,
            "bach_reference_used_for_search": False,
            "test_loaded": False,
        },
        "calibration": {
            "split": calibration.split,
            "policy": calibration.policy,
            "piece_count": len(calibration.piece_scores),
            "accepted_piece_count": sum(
                score >= calibration.threshold - 1e-12
                for _, score, _ in calibration.piece_scores
            ),
            "decision_mean": calibration.decision_mean,
            "threshold": calibration.threshold,
            "piece_scores": [
                {
                    "piece_id": piece_id,
                    "mean_log_pseudolikelihood": score,
                    "decisions": decisions,
                }
                for piece_id, score, decisions in calibration.piece_scores
            ],
        },
        "fragment": {
            "piece_id": args.piece_id,
            "start": args.start,
            "blocks": args.blocks,
            "top_pitches_per_lower_voice": args.top_pitches,
            "score_opportunities": len(score_floor.segments),
        },
        "hard_constraints": {
            "learned_pretest_predicates": len(
                search_poc._learned_constraint_features()
            ),
            "normalization_role": ("generation_filter_only_not_mle_denominator"),
            "root_propagation": hard_constraint_diagnostics,
        },
        "search": {
            "status": result.status.value,
            "explored_nodes": result.explored_nodes,
            "failed_branches": result.failed_branches,
            "backtracks": backtracks,
            "score_rejections": len(score_floor.rejections),
            "early_score_rejections": sum(
                row["fixed_blocks"] < args.blocks
                for row in score_floor.rejections
            ),
            "solution_count": len(result.solutions),
            "score_rejection_examples": score_floor.rejections[:10],
        },
        "comparison": {
            "without_floor": {
                "blocks": baseline_blocks.tolist(),
                "score": _score_payload(baseline_score),
                "satisfies_threshold": (
                    baseline_score.mean >= calibration.threshold - 1e-12
                ),
            },
            "bach_reference": {
                "blocks": source_blocks.tolist(),
                "score": _score_payload(reference_score),
                "used_for_search": False,
            },
        },
    }
    if result.solutions:
        solution = result.solutions[0]
        assignment = assignment_from_solution(
            solution,
            search_poc.PROBLEM,
        )
        selected_blocks = np.asarray(
            [
                search_poc._term_block(assignment[variable])
                for variable in block_variables
            ],
            dtype=np.int16,
        )
        score = score_floor.evaluate_blocks(selected_blocks)
        payload["solution"] = {
            "blocks": selected_blocks.tolist(),
            "score": _score_payload(score),
            "log_choice_weight": solution.log_weight,
            "decisions": len(solution.decisions),
            "satisfies_threshold": score.mean >= calibration.threshold - 1e-12,
        }
        if not args.no_export:
            _export_solution(
                source_path=args.score,
                lattice=lattice,
                blocks=selected_blocks,
                start=args.start,
                musicxml_path=args.musicxml,
                midi_path=args.midi,
            )
            payload["solution"]["exports"] = {
                "musicxml": str(args.musicxml.resolve()),
                "midi": str(args.midi.resolve()),
                "exporter": "MuSES",
            }
    payload["checks"] = {
        "calibration_coverage_matches_policy": (
            payload["calibration"]["accepted_piece_count"]
            >= _required_calibration_coverage(
                calibration.policy,
                payload["calibration"]["piece_count"],
            )
        ),
        "unconstrained_first_solution_rejected": (
            not payload["comparison"]["without_floor"]["satisfies_threshold"]
        ),
        "score_contradiction_observed": (payload["search"]["score_rejections"] > 0),
        "backtrack_observed": payload["search"]["backtracks"] > 0,
        "satisfying_solution_found": bool(
            payload.get("solution", {}).get("satisfies_threshold")
        ),
    }
    payload["checks"]["status"] = (
        "PASS"
        if all(value for key, value in payload["checks"].items() if key != "status")
        else "FAIL"
    )
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(_markdown(payload), encoding="utf-8")
    print(
        f"[score-floor] threshold={calibration.threshold:.6f} "
        f"status={result.status.value} nodes={result.explored_nodes} "
        f"rejections={len(score_floor.rejections)} "
        f"backtracks={backtracks} solutions={len(result.solutions)}",
        flush=True,
    )
    if payload.get("solution"):
        print(
            f"[score-floor] solution score={payload['solution']['score']['mean']:.6f}",
            flush=True,
        )
    print(f"[score-floor] wrote {args.output}", flush=True)
    print(f"[score-floor] wrote {args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
