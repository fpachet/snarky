"""Safe YAML loaders for parser-independent fact fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..facts import Fact
from ..parser import ParseError, parse_term


def load_facts(path: str | Path) -> tuple[Fact, ...]:
    """Load the version-one ``facts`` fixture format."""

    source = Path(path)
    payload: Any = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ParseError(f"{source}: expected schema_version: 1")
    entries = payload.get("facts")
    if not isinstance(entries, list):
        raise ParseError(f"{source}: expected a facts list")
    facts: list[Fact] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ParseError(f"{source}: fact {index} must be a mapping")
        entity = entry.get("entity")
        status = entry.get("status")
        if not isinstance(entity, str) or not isinstance(status, str):
            raise ParseError(f"{source}: fact {index} needs string entity and status")
        facts.append(Fact(parse_term(entity), parse_term(status)))
    return tuple(facts)
