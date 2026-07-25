from snarky import Variable, parse_rules
from snarky.instantiation.domain_planning import _compile_domain_plan


def test_domain_plan_compiles_incidence_components_and_cycle_once() -> None:
    (rule,) = parse_rules(
        """
        RULE triangle
        WHEN
            ($x p $y)
            ($x q $z)
            ($y r $z)
        THEN
            ADD ($x solution $y)
        END
        """
    )

    plan = _compile_domain_plan(rule)

    assert plan.applicable
    assert plan.cyclic
    assert plan.variables == (
        Variable("x"),
        Variable("y"),
        Variable("z"),
    )
    assert plan.incidence == (
        (Variable("x"), (("table", 0), ("table", 1))),
        (Variable("y"), (("table", 0), ("table", 2))),
        (Variable("z"), (("table", 1), ("table", 2))),
    )
    assert all(
        component
        == frozenset((Variable("x"), Variable("y"), Variable("z")))
        for _, component in plan.components
    )
    assert _compile_domain_plan(rule) is plan


def test_domain_plan_distinguishes_acyclic_and_unsupported_rules() -> None:
    chain, unsupported = parse_rules(
        """
        RULE chain
        WHEN
            ($x p $y)
            ($y q $z)
        THEN
            ADD ($x solution $z)
        END

        RULE comparison_variable_without_table
        WHEN
            ($x p anchor)
            $x != $missing
        THEN
            ADD ($x invalid anchor)
        END
        """
    )

    chain_plan = _compile_domain_plan(chain)
    unsupported_plan = _compile_domain_plan(unsupported)

    assert chain_plan.applicable
    assert not chain_plan.cyclic
    assert not unsupported_plan.applicable


def test_wide_scope_forms_one_component_without_pairwise_edges() -> None:
    variables = " ".join(f"$value_{index}" for index in range(40))
    (rule,) = parse_rules(
        f"""
        RULE wide_scope
        WHEN
            (SEQ[{variables}] values anchor)
            $value_0 != $value_1
        THEN
            ADD (domain plan ready)
        END
        """
    )

    plan = _compile_domain_plan(rule)
    expected = frozenset(
        Variable(f"value_{index}") for index in range(40)
    )

    assert plan.applicable
    assert all(component == expected for _, component in plan.components)
