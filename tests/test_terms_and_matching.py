from boojum import (
    Atom,
    PatternMatcher,
    Status,
    Substitution,
    Triple,
    Unifier,
    Variable,
    is_ground,
)


def test_recursive_terms_are_hashable_and_ground() -> None:
    proposition = Triple(
        Atom("alice"),
        Atom("sait"),
        Triple(Atom("bob"), Atom("humain"), Status.VRAI),
    )

    assert is_ground(proposition)
    assert {proposition: "known"}[proposition] == "known"
    assert not is_ground(Triple(Variable("x"), Atom("sait"), proposition))


def test_substitution_applies_recursively() -> None:
    x = Variable("x")
    proposition = Triple(x, Atom("parent_de"), Atom("bob"))

    result = Substitution({x: Atom("alice")}).apply(proposition)

    assert result == Triple(Atom("alice"), Atom("parent_de"), Atom("bob"))


def test_matcher_binds_relation_and_nested_proposition_variables() -> None:
    relation = Variable("relation")
    consequent = Variable("consequent")
    pattern = Triple(
        Atom("alice"),
        relation,
        Triple(Atom("bob"), Atom("implique"), consequent),
    )
    candidate = Triple(
        Atom("alice"),
        Atom("sait"),
        Triple(
            Atom("bob"),
            Atom("implique"),
            Triple(Atom("bob"), Atom("mortel"), Status.VRAI),
        ),
    )

    substitution = PatternMatcher().match(pattern, candidate)

    assert substitution is not None
    assert substitution[relation] == Atom("sait")
    assert substitution[consequent] == Triple(Atom("bob"), Atom("mortel"), Status.VRAI)


def test_matcher_enforces_repeated_variable_equality() -> None:
    x = Variable("x")
    pattern = Triple(x, Atom("same_as"), x)

    assert (
        PatternMatcher().match(
            pattern, Triple(Atom("alice"), Atom("same_as"), Atom("alice"))
        )
        is not None
    )
    assert (
        PatternMatcher().match(
            pattern, Triple(Atom("alice"), Atom("same_as"), Atom("bob"))
        )
        is None
    )


def test_unifier_is_bidirectional_and_performs_occurs_check() -> None:
    x = Variable("x")
    y = Variable("y")
    unifier = Unifier()

    substitution = unifier.unify(
        Triple(x, Atom("parent_de"), Atom("bob")),
        Triple(Atom("alice"), Atom("parent_de"), y),
    )

    assert substitution is not None
    assert substitution.apply(x) == Atom("alice")
    assert substitution.apply(y) == Atom("bob")
    assert unifier.unify(x, Triple(x, Atom("relation"), Atom("value"))) is None
