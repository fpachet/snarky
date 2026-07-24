"""Small reusable rule groups expressed entirely in ordinary Snarky rules."""

from __future__ import annotations

from .actions import add
from .premises import FactPremise
from .rules import Rule, RuleGroup
from .terms import Atom, Triple, Variable

SUBTYPE = Atom("subtype")
INSTANCE_OF = Atom("instance_of")


def type_hierarchy_group(
    *,
    subtype_relation: Atom = SUBTYPE,
    instance_relation: Atom = INSTANCE_OF,
    name: str = "type_hierarchy",
) -> RuleGroup:
    """Return explainable subtype closure and instance inheritance rules."""

    lower = Variable("lower")
    middle = Variable("middle")
    upper = Variable("upper")
    item = Variable("item")
    return RuleGroup(
        name,
        (
            Rule(
                "subtype_transitivity",
                (
                    FactPremise(Triple(lower, subtype_relation, middle)),
                    FactPremise(Triple(middle, subtype_relation, upper)),
                ),
                (add(Triple(lower, subtype_relation, upper)),),
            ),
            Rule(
                "instance_inheritance",
                (
                    FactPremise(Triple(item, instance_relation, lower)),
                    FactPremise(Triple(lower, subtype_relation, upper)),
                ),
                (add(Triple(item, instance_relation, upper)),),
            ),
        ),
    )
