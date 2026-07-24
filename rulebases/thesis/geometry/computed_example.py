"""Example of a safely registered geometric predicate."""

from __future__ import annotations

from snarky import (
    ComputedPredicate,
    PredicateRegistry,
    parse_rules,
)

DISTINCT = ComputedPredicate(
    "distinct",
    lambda arguments: arguments[0] != arguments[1],
)
REGISTRY = PredicateRegistry((DISTINCT,))


def rules():
    return parse_rules(
        """
        RULE accept_segment
        WHEN
            ($segment start $first)
            ($segment end $second)
            CHECK distinct ARGS SEQ[$first $second]
        THEN
            ADD ($segment valid true)
        END
        """,
        predicates=REGISTRY,
    )
