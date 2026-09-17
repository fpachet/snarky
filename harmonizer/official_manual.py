"""Independent Snarky auditor for the official Bach-rule manual.

The MusicXML adapter emits only observable score facts.  Snarky RuleGroups
derive violations and satisfactions; pure factors score the resulting fact
snapshot; profiles independently decide which violations are hard.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import yaml

from snarky import (
    Atom,
    Fact,
    FactorModel,
    FiniteSequence,
    InferenceSession,
    Number,
    Triple,
    evaluate_factor_model,
    parse_factor_groups,
    parse_rule_groups,
    render_term,
)

VOICE_NAMES = ("soprano", "alto", "tenor", "bass")
ADJACENT_VOICES = (("soprano", "alto"), ("alto", "tenor"), ("tenor", "bass"))
VOICE_PAIRS = tuple(
    (VOICE_NAMES[upper], VOICE_NAMES[lower])
    for upper in range(4)
    for lower in range(upper + 1, 4)
)
DISSONANT_ABOVE_BASS = frozenset((1, 2, 5, 6, 10, 11))
MANUAL_RULE_IDS = (
    "MANUAL-PARALLEL-FIFTH",
    "MANUAL-PARALLEL-OCTAVE",
    "MANUAL-DIRECT-FIFTH",
    "MANUAL-VOICE-CROSSING",
    "MANUAL-VOICE-OVERLAP",
    "MANUAL-COMMON-TONE",
    "MANUAL-CONTRARY-OUTER",
    "MANUAL-COMPENSATED-LEAP",
    "MANUAL-SUSPENSION-RESOLUTION",
    "MANUAL-LEADING-TONE",
    "MANUAL-SINGABLE-LINE",
    "MANUAL-ACTIVE-INNER-VOICE",
)
METRIC_SCALE = 1_000_000
EMPIRICAL_METRIC_IDS = (
    "parallel_fifth_rate",
    "parallel_octave_rate",
    "direct_fifth_rate",
    "voice_crossing_rate",
    "voice_overlap_rate",
    "unresolved_leading_tone_ratio",
    "uncompensated_leap_ratio",
    "unresolved_suspension_ratio",
    "soprano_maximum_leap",
    "alto_maximum_leap",
    "tenor_maximum_leap",
    "bass_maximum_leap",
    "alto_longest_repeat_run",
    "tenor_longest_repeat_run",
    "bass_longest_repeat_run",
    "alto_step_deficit",
    "tenor_step_deficit",
    "bass_step_deficit",
)

HERE = Path(__file__).resolve().parent
DEFAULT_RULEBASE = HERE / "bach_rule_induction/rule_bases/official_manual"


@dataclass(frozen=True, slots=True)
class NoteEvent:
    onset: Fraction
    duration: Fraction
    pitch: int | None
    attack: bool

    @property
    def end(self) -> Fraction:
        return self.onset + self.duration


@dataclass(frozen=True, slots=True)
class SATBFrame:
    offset: Fraction
    pitches: tuple[int, int, int, int]
    attacks: tuple[bool, bool, bool, bool]


@dataclass(frozen=True, slots=True)
class ParsedSATBScore:
    source: Path
    tonic_pc: int
    frames: tuple[SATBFrame, ...]
    attacked_lines: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class ManualDiagnostic:
    source: Path
    profile: str
    violations: tuple[dict[str, str], ...]
    satisfactions: tuple[dict[str, str], ...]
    factor_activations: tuple[dict[str, Any], ...]
    factor_score: float
    hard_violations: tuple[dict[str, str], ...]
    contradiction: bool
    frame_count: int
    voice_summaries: tuple[dict[str, int | float | str], ...]
    criteria: tuple[dict[str, int | str], ...]
    empirical_metrics: tuple[dict[str, float | int | str], ...]
    empirical_budget_exceedances: tuple[dict[str, float | int | str], ...]
    empirical_budget_violations: tuple[dict[str, str], ...]

    def count(self, relation: str, rule_id: str) -> int:
        rows = self.violations if relation == "violates" else self.satisfactions
        return sum(row["rule_id"] == rule_id for row in rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source),
            "profile": self.profile,
            "frame_count": self.frame_count,
            "violations": list(self.violations),
            "satisfactions": list(self.satisfactions),
            "factor_score": self.factor_score,
            "factor_activations": list(self.factor_activations),
            "hard_violations": list(self.hard_violations),
            "contradiction": self.contradiction,
            "passes_profile": not self.contradiction,
            "voice_summaries": list(self.voice_summaries),
            "criteria": list(self.criteria),
            "empirical_metrics": list(self.empirical_metrics),
            "empirical_budget_exceedances": list(self.empirical_budget_exceedances),
            "empirical_budget_violations": list(self.empirical_budget_violations),
        }


def _xml_root(path: Path) -> ElementTree.Element:
    if path.suffix.lower() != ".mxl":
        root = ElementTree.parse(path).getroot()
    else:
        with zipfile.ZipFile(path) as archive:
            container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
            rootfile = container.find(".//{*}rootfile")
            if rootfile is None:
                raise ValueError(f"No MusicXML rootfile in {path}")
            root = ElementTree.fromstring(archive.read(rootfile.attrib["full-path"]))
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]
    return root


def _integer_text(element: ElementTree.Element, path: str, default: int) -> int:
    child = element.find(path)
    return default if child is None or child.text is None else int(child.text)


def _midi_pitch(note: ElementTree.Element) -> int | None:
    pitch = note.find("pitch")
    if pitch is None:
        return None
    step = pitch.findtext("step")
    octave_text = pitch.findtext("octave")
    if step is None or octave_text is None:
        return None
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[step]
    alter = _integer_text(pitch, "alter", 0)
    return (int(octave_text) + 1) * 12 + base + alter


def _part_events(part: ElementTree.Element) -> tuple[NoteEvent, ...]:
    divisions = 1
    measure_start = Fraction(0)
    output: list[NoteEvent] = []
    for measure in part.findall("measure"):
        cursor = measure_start
        furthest = measure_start
        previous_onset = measure_start
        for child in measure:
            if child.tag == "attributes":
                divisions = _integer_text(child, "divisions", divisions)
            elif child.tag == "backup":
                cursor -= Fraction(_integer_text(child, "duration", 0), divisions)
            elif child.tag == "forward":
                cursor += Fraction(_integer_text(child, "duration", 0), divisions)
                furthest = max(furthest, cursor)
            elif child.tag == "note":
                duration = Fraction(_integer_text(child, "duration", 0), divisions)
                chord = child.find("chord") is not None
                onset = previous_onset if chord else cursor
                previous_onset = onset
                tie_types = {tie.attrib.get("type") for tie in child.findall("tie")}
                output.append(
                    NoteEvent(
                        onset=onset,
                        duration=duration,
                        pitch=_midi_pitch(child),
                        attack="stop" not in tie_types,
                    )
                )
                if not chord:
                    cursor += duration
                    furthest = max(furthest, cursor)
        measure_start = furthest
    return tuple(sorted(output, key=lambda event: (event.onset, event.pitch or -1)))


def _tonic_pc(root: ElementTree.Element) -> int:
    key = root.find(".//part/measure/attributes/key")
    if key is None:
        return 0
    fifths = _integer_text(key, "fifths", 0)
    mode = (key.findtext("mode") or "major").strip().lower()
    return (7 * fifths + (9 if mode == "minor" else 0)) % 12


def _active_event(events: tuple[NoteEvent, ...], offset: Fraction) -> NoteEvent | None:
    active = [event for event in events if event.onset <= offset < event.end]
    if not active:
        return None
    pitched = [event for event in active if event.pitch is not None]
    return max(pitched, key=lambda event: event.onset) if pitched else None


def parse_musicxml_satb(path: Path) -> ParsedSATBScore:
    """Read one four-part monophonic score without a music21 dependency."""

    path = path.resolve()
    root = _xml_root(path)
    parts = root.findall("part")
    if len(parts) != 4:
        raise ValueError(f"Expected four SATB parts in {path}, found {len(parts)}")
    event_parts = tuple(_part_events(part) for part in parts)
    offsets = sorted(
        {
            event.onset
            for events in event_parts
            for event in events
            if event.pitch is not None
        }
    )
    frames: list[SATBFrame] = []
    for offset in offsets:
        active = tuple(_active_event(events, offset) for events in event_parts)
        if any(event is None or event.pitch is None for event in active):
            continue
        events = tuple(event for event in active if event is not None)
        frames.append(
            SATBFrame(
                offset=offset,
                pitches=tuple(int(event.pitch) for event in events),  # type: ignore[arg-type]
                attacks=tuple(
                    event.onset == offset and event.attack for event in events
                ),
            )
        )
    lines = tuple(
        tuple(
            int(event.pitch)
            for event in events
            if event.pitch is not None and event.attack
        )
        for events in event_parts
    )
    return ParsedSATBScore(path, _tonic_pc(root), tuple(frames), lines)


def _seq(*values: Atom | Number | FiniteSequence) -> FiniteSequence:
    return FiniteSequence(tuple(values))


def _atom(value: str) -> Atom:
    return Atom(value)


def _number(value: int) -> Number:
    return Number(value)


def _line_summary(line: tuple[int, ...]) -> tuple[int, int, int, int, int, int]:
    if not line:
        return (0, 0, 0, 0, 0, 0)
    motions = tuple(
        right - left for left, right in zip(line[:-1], line[1:], strict=True)
    )
    maximum = max((abs(motion) for motion in motions), default=0)
    steps = sum(0 < abs(motion) <= 2 for motion in motions)
    nonzero = sum(motion != 0 for motion in motions)
    longest = 1
    current = 1
    for left, right in zip(line[:-1], line[1:], strict=True):
        current = current + 1 if left == right else 1
        longest = max(longest, current)
    return (len(line), len(set(line)), maximum, steps, nonzero, longest)


def score_facts(score: ParsedSATBScore) -> tuple[Fact, ...]:
    """Translate a parsed score into generic immutable Snarky facts."""

    facts: list[Fact] = [
        Fact(Triple(_atom("score"), _atom("kind"), _atom("satb_score")))
    ]
    for upper, lower in ADJACENT_VOICES:
        facts.append(
            Fact(Triple(_atom(upper), _atom("adjacent_lower_voice"), _atom(lower)))
        )
    positions = tuple(_atom(f"position_{index}") for index in range(len(score.frames)))
    for position, frame in zip(positions, score.frames, strict=True):
        facts.extend(
            (
                Fact(Triple(position, _atom("kind"), _atom("satb_position"))),
                Fact(Triple(position, _atom("tonic_pc"), _number(score.tonic_pc))),
                Fact(
                    Triple(
                        position,
                        _atom("voicing"),
                        _seq(*(_number(pitch) for pitch in frame.pitches)),
                    )
                ),
            )
        )
        for voice, pitch, attacked in zip(
            VOICE_NAMES, frame.pitches, frame.attacks, strict=True
        ):
            facts.append(
                Fact(
                    Triple(
                        position,
                        _atom("voice_pitch"),
                        _seq(_atom(voice), _number(pitch)),
                    )
                )
            )
            if attacked:
                facts.append(
                    Fact(Triple(position, _atom("attacked_voice"), _atom(voice)))
                )
            if (
                voice != "bass"
                and (pitch - frame.pitches[3]) % 12 in DISSONANT_ABOVE_BASS
            ):
                facts.append(
                    Fact(Triple(position, _atom("dissonant_voice"), _atom(voice)))
                )
        for upper, lower in VOICE_PAIRS:
            upper_index = VOICE_NAMES.index(upper)
            lower_index = VOICE_NAMES.index(lower)
            facts.append(
                Fact(
                    Triple(
                        position,
                        _atom("voice_pair"),
                        _seq(
                            _atom(upper),
                            _atom(lower),
                            _number(frame.pitches[upper_index]),
                            _number(frame.pitches[lower_index]),
                        ),
                    )
                )
            )
    for index, (left, right) in enumerate(
        zip(positions[:-1], positions[1:], strict=True)
    ):
        source = score.frames[index]
        target = score.frames[index + 1]
        transition = _seq(left, right)
        facts.extend(
            (
                Fact(Triple(left, _atom("successor"), right)),
                Fact(Triple(transition, _atom("kind"), _atom("satb_transition"))),
                Fact(Triple(transition, _atom("source_position"), left)),
                Fact(Triple(transition, _atom("target_position"), right)),
            )
        )
        for voice_index, voice in enumerate(VOICE_NAMES):
            facts.append(
                Fact(
                    Triple(
                        transition,
                        _atom("voice_path"),
                        _seq(
                            _atom(voice),
                            _number(source.pitches[voice_index]),
                            _number(target.pitches[voice_index]),
                        ),
                    )
                )
            )
        for upper, lower in VOICE_PAIRS:
            upper_index = VOICE_NAMES.index(upper)
            lower_index = VOICE_NAMES.index(lower)
            facts.append(
                Fact(
                    Triple(
                        transition,
                        _atom("voice_pair"),
                        _seq(
                            _atom(upper),
                            _atom(lower),
                            _number(source.pitches[upper_index]),
                            _number(source.pitches[lower_index]),
                            _number(target.pitches[upper_index]),
                            _number(target.pitches[lower_index]),
                        ),
                    )
                )
            )
    for index, (previous, current, following) in enumerate(
        zip(positions[:-2], positions[1:-1], positions[2:], strict=True)
    ):
        frames = score.frames[index : index + 3]
        window = _seq(previous, current, following)
        facts.extend(
            (
                Fact(Triple(window, _atom("kind"), _atom("satb_window3"))),
                Fact(
                    Triple(
                        window,
                        _atom("positions"),
                        _seq(previous, current, following),
                    )
                ),
                Fact(
                    Triple(
                        window,
                        _atom("bass_path3"),
                        _seq(*(_number(frame.pitches[3]) for frame in frames)),
                    )
                ),
            )
        )
        for voice_index, voice in enumerate(VOICE_NAMES):
            facts.append(
                Fact(
                    Triple(
                        window,
                        _atom("voice_path3"),
                        _seq(
                            _atom(voice),
                            *(_number(frame.pitches[voice_index]) for frame in frames),
                        ),
                    )
                )
            )
    for voice, line in zip(VOICE_NAMES, score.attacked_lines, strict=True):
        summary = _line_summary(line)
        facts.append(
            Fact(
                Triple(
                    _atom("score"),
                    _atom("voice_summary"),
                    _seq(_atom(voice), *(_number(value) for value in summary)),
                )
            )
        )
    return tuple(facts)


def _load_profiles(rulebase: Path) -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load((rulebase / "profiles.yaml").read_text(encoding="utf-8"))
    return dict(raw["profiles"])


def _relation_rows(
    facts: tuple[Fact, ...], relation: str
) -> tuple[dict[str, str], ...]:
    target = _atom(relation)
    rows = []
    for fact in facts:
        entity = fact.entity
        if (
            isinstance(entity, Triple)
            and entity.relation == target
            and isinstance(entity.object, Atom)
            and entity.object.name.startswith(("MANUAL-", "EMPIRICAL-"))
        ):
            rows.append(
                {
                    "scope": render_term(entity.subject),
                    "rule_id": entity.object.name,
                }
            )
    return tuple(rows)


def _count_rule(rows: tuple[dict[str, str], ...], rule_id: str) -> int:
    return sum(row["rule_id"] == rule_id for row in rows)


def _failure_ratio(violations: int, satisfactions: int) -> float:
    opportunities = violations + satisfactions
    return 0.0 if opportunities == 0 else violations / opportunities


def empirical_metric_values(
    *,
    violations: tuple[dict[str, str], ...],
    satisfactions: tuple[dict[str, str], ...],
    frame_count: int,
    voice_summaries: tuple[dict[str, int | float | str], ...],
) -> dict[str, float]:
    """Return one-sided, high-is-bad empirical criteria for a full score."""

    transitions = max(frame_count - 1, 1)
    frames = max(frame_count, 1)
    summaries = {str(row["voice"]): row for row in voice_summaries}

    def violations_per(rule_id: str, opportunities: int) -> float:
        return _count_rule(violations, rule_id) / opportunities

    def unresolved_ratio(rule_id: str) -> float:
        return _failure_ratio(
            _count_rule(violations, rule_id),
            _count_rule(satisfactions, rule_id),
        )

    metrics = {
        "parallel_fifth_rate": violations_per("MANUAL-PARALLEL-FIFTH", transitions),
        "parallel_octave_rate": violations_per("MANUAL-PARALLEL-OCTAVE", transitions),
        "direct_fifth_rate": violations_per("MANUAL-DIRECT-FIFTH", transitions),
        "voice_crossing_rate": violations_per("MANUAL-VOICE-CROSSING", frames),
        "voice_overlap_rate": violations_per("MANUAL-VOICE-OVERLAP", transitions),
        "unresolved_leading_tone_ratio": unresolved_ratio("MANUAL-LEADING-TONE"),
        "uncompensated_leap_ratio": unresolved_ratio("MANUAL-COMPENSATED-LEAP"),
        "unresolved_suspension_ratio": unresolved_ratio("MANUAL-SUSPENSION-RESOLUTION"),
    }
    for voice in VOICE_NAMES:
        row = summaries[voice]
        metrics[f"{voice}_maximum_leap"] = float(row["maximum_leap"])
        if voice != "soprano":
            metrics[f"{voice}_longest_repeat_run"] = float(row["longest_repeat_run"])
            metrics[f"{voice}_step_deficit"] = 1.0 - float(row["step_rate"])
    if set(metrics) != set(EMPIRICAL_METRIC_IDS):
        raise AssertionError("empirical metric registry and extraction diverged")
    return metrics


def _empirical_budget_facts(
    profile: str,
    profile_payload: dict[str, Any],
    metrics: dict[str, float],
    rulebase: Path,
) -> tuple[Fact, ...]:
    budget_name = profile_payload.get("empirical_budgets_file")
    if budget_name is None:
        return ()
    payload = yaml.safe_load((rulebase / str(budget_name)).read_text(encoding="utf-8"))
    scale = int(payload["scale"])
    if scale != METRIC_SCALE:
        raise ValueError(f"Unsupported empirical metric scale: {scale}")
    facts: list[Fact] = []
    profile_atom = _atom(profile)
    for metric_id, value in metrics.items():
        facts.append(
            Fact(
                Triple(
                    _atom("score"),
                    _atom("observed_metric"),
                    _seq(_atom(metric_id), _number(round(value * scale))),
                )
            )
        )
    for budget in payload.get("promoted_budgets", []):
        rule_id = str(budget["rule_id"])
        facts.append(
            Fact(
                Triple(
                    profile_atom,
                    _atom("upper_budget"),
                    _seq(
                        _atom(str(budget["metric_id"])),
                        _number(int(budget["threshold_scaled"])),
                        _atom(rule_id),
                    ),
                )
            )
        )
    metric_groups = {
        str(metric_id): str(group["group_id"])
        for group in payload.get("group_budgets", [])
        for metric_id in group["metric_ids"]
    }
    for metric_id, group_id in metric_groups.items():
        facts.append(
            Fact(
                Triple(
                    _atom(metric_id),
                    _atom("empirical_budget_group"),
                    _atom(group_id),
                )
            )
        )
    if payload.get("promoted_budgets"):
        facts.append(
            Fact(
                Triple(
                    profile_atom,
                    _atom("hard_rule"),
                    _atom("EMPIRICAL-JOINT-BUDGET"),
                )
            )
        )
    for group in payload.get("group_budgets", []):
        facts.append(
            Fact(
                Triple(
                    profile_atom,
                    _atom("hard_rule"),
                    _atom(str(group["rule_id"])),
                )
            )
        )
    return tuple(facts)


def audit_parsed_satb(
    parsed: ParsedSATBScore,
    *,
    profile: str = "diagnostic",
    rulebase: Path = DEFAULT_RULEBASE,
) -> ManualDiagnostic:
    """Audit an already materialized SATB lattice with the Snarky rulebase."""

    profiles = _load_profiles(rulebase)
    if profile not in profiles:
        raise ValueError(f"Unknown official-manual profile: {profile}")
    initial = list(score_facts(parsed))
    profile_atom = _atom(profile)
    for rule_id in profiles[profile].get("hard_rules", []):
        initial.append(Fact(Triple(profile_atom, _atom("hard_rule"), _atom(rule_id))))
    groups = parse_rule_groups(
        (rulebase / "official_manual.rules").read_text(encoding="utf-8")
    )
    budget_groups = parse_rule_groups(
        (rulebase / "empirical_budgets.rules").read_text(encoding="utf-8")
    )
    acceptance_path = rulebase / "empirical_acceptance.rules"
    acceptance_groups = (
        parse_rule_groups(acceptance_path.read_text(encoding="utf-8"))
        if acceptance_path.exists()
        else ()
    )
    constraint_groups = parse_rule_groups(
        (rulebase / "profile_constraints.rules").read_text(encoding="utf-8")
    )
    session = InferenceSession(tuple(initial))
    for group in groups:
        session.run_group(group)
    preliminary_violations = _relation_rows(session.facts, "violates")
    preliminary_satisfactions = _relation_rows(session.facts, "satisfies")
    summaries = []
    for voice, line in zip(VOICE_NAMES, parsed.attacked_lines, strict=True):
        notes, unique, maximum, steps, motions, longest = _line_summary(line)
        summaries.append(
            {
                "voice": voice,
                "note_count": notes,
                "unique_pitch_count": unique,
                "maximum_leap": maximum,
                "step_count": steps,
                "motion_count": motions,
                "step_rate": 0.0 if motions == 0 else steps / motions,
                "longest_repeat_run": longest,
            }
        )
    metrics = empirical_metric_values(
        violations=preliminary_violations,
        satisfactions=preliminary_satisfactions,
        frame_count=len(parsed.frames),
        voice_summaries=tuple(summaries),
    )
    empirical_facts = _empirical_budget_facts(
        profile,
        profiles[profile],
        metrics,
        rulebase,
    )
    if empirical_facts:
        session = InferenceSession((*session.facts, *empirical_facts))
        for group in budget_groups:
            session.run_group(group)
        for group in acceptance_groups:
            session.run_group(group)
    for group in constraint_groups:
        session.run_group(group)
    factor_groups = parse_factor_groups(
        (rulebase / "official_manual.factors").read_text(encoding="utf-8")
    )
    selected_names = set(profiles[profile].get("factor_groups", []))
    selected_groups = tuple(
        group for group in factor_groups if group.name in selected_names
    )
    evaluation = evaluate_factor_model(
        FactorModel(f"official_manual_{profile}", selected_groups),
        session.facts,
    )
    violations = _relation_rows(session.facts, "violates")
    satisfactions = _relation_rows(session.facts, "satisfies")
    hard_ids = set(profiles[profile].get("hard_rules", []))
    for fact in session.facts:
        entity = fact.entity
        if (
            isinstance(entity, Triple)
            and entity.subject == profile_atom
            and entity.relation == _atom("hard_rule")
            and isinstance(entity.object, Atom)
        ):
            hard_ids.add(entity.object.name)
    hard = tuple(row for row in violations if row["rule_id"] in hard_ids)
    criteria = tuple(
        {
            "rule_id": rule_id,
            "violation_count": sum(row["rule_id"] == rule_id for row in violations),
            "satisfaction_count": sum(
                row["rule_id"] == rule_id for row in satisfactions
            ),
            "status": "hard" if rule_id in hard_ids else "diagnostic_or_factor",
        }
        for rule_id in MANUAL_RULE_IDS
    )
    contradiction = Fact(
        Triple(_atom("search"), _atom("state"), _atom("contradiction"))
    )
    return ManualDiagnostic(
        source=parsed.source.resolve(),
        profile=profile,
        violations=violations,
        satisfactions=satisfactions,
        factor_activations=tuple(
            {
                "group": activation.group_name,
                "factor": activation.factor_name,
                "scope": render_term(activation.scope),
                "log_weight": activation.log_weight,
                "witness_count": activation.witness_count,
            }
            for activation in evaluation.activations
        ),
        factor_score=evaluation.log_score,
        hard_violations=hard,
        contradiction=contradiction in session.facts,
        frame_count=len(parsed.frames),
        voice_summaries=tuple(summaries),
        criteria=criteria,
        empirical_metrics=tuple(
            {
                "metric_id": metric_id,
                "value": value,
                "scaled_value": round(value * METRIC_SCALE),
            }
            for metric_id, value in metrics.items()
        ),
        empirical_budget_exceedances=tuple(
            {
                "metric_id": entity.object.elements[0].name,
                "scaled_value": int(entity.object.elements[1].value),
                "scaled_threshold": int(entity.object.elements[2].value),
                "value": float(entity.object.elements[1].value / METRIC_SCALE),
                "threshold": float(entity.object.elements[2].value / METRIC_SCALE),
            }
            for fact in session.facts
            if isinstance((entity := fact.entity), Triple)
            and entity.subject == _atom("score")
            and entity.relation == _atom("exceeded_budget")
            and isinstance(entity.object, FiniteSequence)
            and len(entity.object.elements) == 3
            and isinstance(entity.object.elements[0], Atom)
            and isinstance(entity.object.elements[1], Number)
            and isinstance(entity.object.elements[2], Number)
        ),
        empirical_budget_violations=tuple(
            row for row in violations if row["rule_id"].startswith("EMPIRICAL-")
        ),
    )


def audit_musicxml(
    path: Path,
    *,
    profile: str = "diagnostic",
    rulebase: Path = DEFAULT_RULEBASE,
) -> ManualDiagnostic:
    """Parse and audit one four-part MusicXML score."""

    return audit_parsed_satb(
        parse_musicxml_satb(path),
        profile=profile,
        rulebase=rulebase,
    )


def write_diagnostic(path: Path, diagnostic: ManualDiagnostic) -> None:
    path.write_text(
        json.dumps(diagnostic.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
