"""Public API of the Snarky inference engine."""

from .actions import AddFact, add
from .engine import EngineLimits, ForwardEngine, InferenceLimitError, RunResult
from .facts import Fact
from .instantiation import (
    IndexedInstantiationStrategy,
    InstantiationMetrics,
    InstantiationStrategy,
    NaiveInstantiationStrategy,
)
from .matching import PatternMatcher
from .parser import ParseError, parse_rules, parse_term
from .premises import ComparisonOperator, ComparisonPremise, FactPremise
from .rules import Rule, when
from .substitutions import EMPTY_SUBSTITUTION, Substitution
from .terms import (
    Atom,
    Number,
    Proposition,
    Status,
    Term,
    Triple,
    Variable,
    is_ground,
    render_term,
    variables_in,
)
from .unification import Unifier

__all__ = [
    "EMPTY_SUBSTITUTION",
    "Action",
    "AddFact",
    "Atom",
    "ComparisonOperator",
    "ComparisonPremise",
    "EngineLimits",
    "Fact",
    "FactPremise",
    "ForwardEngine",
    "InferenceLimitError",
    "IndexedInstantiationStrategy",
    "InstantiationMetrics",
    "InstantiationStrategy",
    "Number",
    "NaiveInstantiationStrategy",
    "ParseError",
    "PatternMatcher",
    "Proposition",
    "Rule",
    "RunResult",
    "Status",
    "Substitution",
    "Term",
    "Triple",
    "Unifier",
    "Variable",
    "add",
    "is_ground",
    "parse_rules",
    "parse_term",
    "render_term",
    "variables_in",
    "when",
]

# Kept as a public spelling for type-oriented API documentation.
Action = AddFact
