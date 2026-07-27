from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_variants.py")
MODULE_DIRECTORY = str(MODULE_PATH.parent)
if MODULE_DIRECTORY not in sys.path:
    sys.path.insert(0, MODULE_DIRECTORY)
SPEC = importlib.util.spec_from_file_location("variant_audit_poc", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


def test_conservative_split_moves_groups_toward_exposed_data() -> None:
    old = {
        "train": ["a"],
        "validation": ["b", "c"],
        "test": ["d", "e"],
    }
    groups = [["a", "b"], ["c", "d"], ["e"]]
    grouped, moved = audit.conservative_grouped_split(old, groups)
    assert grouped == {
        "train": ["a", "b"],
        "validation": ["c", "d"],
        "test": ["e"],
    }
    assert moved == [
        {"piece_id": "b", "from": "validation", "to": "train"},
        {"piece_id": "d", "from": "test", "to": "validation"},
    ]


def test_grouped_split_has_no_crossing_group() -> None:
    old = {
        "train": ["a"],
        "validation": ["b"],
        "test": ["c"],
    }
    groups = [["a", "b"], ["c"]]
    grouped, _ = audit.conservative_grouped_split(old, groups)
    mapping = audit.split_mapping(grouped)
    assert audit.crossing_groups(groups, mapping) == []
