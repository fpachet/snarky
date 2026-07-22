import pytest

from snarky import (
    ArithmeticEvaluationError,
    Fact,
    ForwardEngine,
    Let,
    Number,
    Substitution,
    Variable,
    evaluate_arithmetic,
    parse_arithmetic_expression,
    parse_rules,
    parse_term,
)


def test_arithmetic_parser_honors_precedence_parentheses_and_unary() -> None:
    substitution = Substitution(((Variable("x"), Number(4)),))

    assert evaluate_arithmetic(
        parse_arithmetic_expression("2 + $x * 3"), substitution
    ) == Number(14)
    assert evaluate_arithmetic(
        parse_arithmetic_expression("-(2 + $x) * 3"), substitution
    ) == Number(-18)


def test_let_actions_bind_sequential_results_for_add() -> None:
    rules = parse_rules(
        """
        RULE calculate
        WHEN
            ($item valeur $n)
        THEN
            LET $double := $n * 2
            LET $resultat := $double + 1
            ADD ($item resultat $resultat)
        END
        """
    )

    result = ForwardEngine(rules).run((Fact(parse_term("(test valeur 5)")),))
    expected = Fact(parse_term("(test resultat 11)"))

    assert expected in result.facts
    derivation = result.provenance.minimal_derivation(expected)
    assert derivation is not None
    assert derivation.substitution[Variable("double")] == Number(10)
    assert derivation.substitution[Variable("resultat")] == Number(11)
    assert isinstance(rules[0].actions[0], Let)


def test_let_rejects_non_numeric_operands_and_division_by_zero() -> None:
    non_numeric = parse_rules(
        """
        RULE invalid_type
        WHEN
            ($item valeur $value)
        THEN
            LET $result := $value + 1
            ADD ($item resultat $result)
        END
        """
    )
    division_by_zero = parse_rules(
        """
        RULE invalid_division
        WHEN
            ($item valeur $value)
        THEN
            LET $result := $value / 0
            ADD ($item resultat $result)
        END
        """
    )

    with pytest.raises(ArithmeticEvaluationError, match="not bound to a number"):
        ForwardEngine(non_numeric).run((Fact(parse_term("(test valeur texte)")),))
    with pytest.raises(ArithmeticEvaluationError, match="division by zero"):
        ForwardEngine(division_by_zero).run((Fact(parse_term("(test valeur 5)")),))
