"""Public API of the Snarky inference engine."""

from .actions import Action, AddFact, Let, add, let
from .engine import EngineLimits, ForwardEngine, InferenceLimitError, RunResult
from .expressions import (
    ArithmeticEvaluationError,
    BinaryArithmeticExpression,
    BinaryArithmeticOperator,
    NumericExpression,
    UnaryArithmeticExpression,
    UnaryArithmeticOperator,
    evaluate_arithmetic,
)
from .facts import Fact
from .instantiation import (
    IndexedInstantiationStrategy,
    InstantiationMetrics,
    InstantiationStrategy,
    NaiveInstantiationStrategy,
    SemiNaiveInstantiationStrategy,
)
from .matching import PatternMatcher
from .parser import ParseError, parse_arithmetic_expression, parse_rules, parse_term
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
    "ArithmeticEvaluationError",
    "Atom",
    "BinaryArithmeticExpression",
    "BinaryArithmeticOperator",
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
    "Let",
    "Number",
    "NaiveInstantiationStrategy",
    "NumericExpression",
    "ParseError",
    "PatternMatcher",
    "Proposition",
    "Rule",
    "RunResult",
    "SemiNaiveInstantiationStrategy",
    "Status",
    "Substitution",
    "Term",
    "Triple",
    "UnaryArithmeticExpression",
    "UnaryArithmeticOperator",
    "Unifier",
    "Variable",
    "add",
    "evaluate_arithmetic",
    "is_ground",
    "let",
    "parse_arithmetic_expression",
    "parse_rules",
    "parse_term",
    "render_term",
    "variables_in",
    "when",
]
