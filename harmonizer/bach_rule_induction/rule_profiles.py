"""Versioned rule-base manifests for the Bach induction experiments."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Literal, cast

import yaml

type RuleProfileName = Literal["historical", "learned", "hybrid"]

ROOT = Path(__file__).resolve().parent
RULE_BASE_ROOT = ROOT / "rule_bases"


@dataclass(frozen=True, slots=True)
class RuleWeight:
    """One learned log-score contribution and its projection provenance."""

    rule_id: str
    log_contribution: float | None
    log_contribution_per_strength: float | None
    projection: str


@dataclass(frozen=True, slots=True)
class RuleBaseManifest:
    """Resolved, immutable description of one selectable rule base."""

    profile: RuleProfileName
    id: str
    kind: str
    manifest_path: Path
    inherited_profiles: tuple[RuleProfileName, ...]
    rule_files: tuple[Path, ...]
    rule_ids: tuple[str, ...]
    weights: tuple[RuleWeight, ...]
    scaffolding_path: Path | None

    @property
    def weight_by_rule(self) -> dict[str, RuleWeight]:
        return {weight.rule_id: weight for weight in self.weights}


def _mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field} must be a string-keyed mapping")
    return cast(dict[str, Any], value)


def _string_sequence(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return tuple(value)


def _load_direct_manifest(profile: RuleProfileName) -> RuleBaseManifest:
    path = RULE_BASE_ROOT / profile / "manifest.yaml"
    raw = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), field="manifest")
    if raw.get("schema_version") != 1:
        raise ValueError(f"{path}: unsupported schema_version")
    inherited = tuple(
        cast(RuleProfileName, item)
        for item in _string_sequence(raw.get("inherits", []), field="inherits")
    )
    if any(item not in {"historical", "learned", "hybrid"} for item in inherited):
        raise ValueError(f"{path}: unknown inherited profile")
    rule_files = tuple(
        (path.parent / item).resolve()
        for item in _string_sequence(raw.get("rule_files", []), field="rule_files")
    )
    missing = tuple(item for item in rule_files if not item.is_file())
    if missing:
        raise FileNotFoundError(f"{path}: missing rule files: {missing}")
    rule_ids = _string_sequence(raw.get("rule_ids", []), field="rule_ids")

    weights: list[RuleWeight] = []
    for rule_id, payload_value in _mapping(
        raw.get("weights", {}), field="weights"
    ).items():
        payload = _mapping(payload_value, field=f"weights.{rule_id}")
        log_contribution = payload.get("log_contribution")
        per_strength = payload.get("log_contribution_per_strength")
        if log_contribution is not None and not isinstance(
            log_contribution, (int, float)
        ):
            raise ValueError(f"{path}: non-numeric weight for {rule_id}")
        if per_strength is not None and not isinstance(per_strength, (int, float)):
            raise ValueError(f"{path}: non-numeric strength weight for {rule_id}")
        if (log_contribution is None) == (per_strength is None):
            raise ValueError(f"{path}: {rule_id} needs exactly one contribution form")
        projection = payload.get("projection")
        if not isinstance(projection, str):
            raise ValueError(f"{path}: missing projection for {rule_id}")
        weights.append(
            RuleWeight(
                rule_id,
                (None if log_contribution is None else float(log_contribution)),
                None if per_strength is None else float(per_strength),
                projection,
            )
        )

    scaffolding = raw.get("scaffolding", {})
    scaffolding_path: Path | None = None
    if isinstance(scaffolding, dict) and isinstance(scaffolding.get("file"), str):
        scaffolding_path = (path.parent / scaffolding["file"]).resolve()
        if not scaffolding_path.is_file():
            raise FileNotFoundError(scaffolding_path)

    identifier = raw.get("id")
    kind = raw.get("kind")
    if not isinstance(identifier, str) or not isinstance(kind, str):
        raise ValueError(f"{path}: id and kind must be strings")
    return RuleBaseManifest(
        profile,
        identifier,
        kind,
        path,
        inherited,
        rule_files,
        rule_ids,
        tuple(weights),
        scaffolding_path,
    )


@cache
def load_rule_base(profile: RuleProfileName) -> RuleBaseManifest:
    """Load a profile and resolve hybrid inheritance without hidden imports."""

    direct = _load_direct_manifest(profile)
    if not direct.inherited_profiles:
        if profile == "learned":
            if any(not rule_id.startswith("R-LEARNED-") for rule_id in direct.rule_ids):
                raise ValueError("S-LEARNED contains a non-learned rule id")
            if set(direct.rule_ids) != {weight.rule_id for weight in direct.weights}:
                raise ValueError("S-LEARNED needs exactly one weight per rule")
        return direct

    inherited = tuple(load_rule_base(item) for item in direct.inherited_profiles)
    rule_ids = tuple(rule_id for manifest in inherited for rule_id in manifest.rule_ids)
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError(f"{direct.manifest_path}: duplicate inherited rule ids")
    rule_files = tuple(
        rule_file for manifest in inherited for rule_file in manifest.rule_files
    )
    weights = tuple(weight for manifest in inherited for weight in manifest.weights)
    scaffolding_paths = tuple(
        manifest.scaffolding_path
        for manifest in inherited
        if manifest.scaffolding_path is not None
    )
    return RuleBaseManifest(
        profile,
        direct.id,
        direct.kind,
        direct.manifest_path,
        direct.inherited_profiles,
        rule_files,
        rule_ids,
        weights,
        scaffolding_paths[-1] if scaffolding_paths else None,
    )
