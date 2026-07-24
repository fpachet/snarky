import pickle
from dataclasses import fields

from snarky import (
    Atom,
    Fact,
    Number,
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


def test_terms_and_facts_preserve_their_structural_hashes() -> None:
    atom = Atom("alice")
    number = Number(42)
    variable = Variable("person")
    proposition = Triple(Atom("alice"), Atom("age"), Atom("adult"))
    fact = Fact(proposition, Status.VRAI)

    assert hash(atom) == hash((atom.name,))
    assert hash(number) == hash((number.value,))
    assert hash(variable) == hash((variable.name,))
    assert hash(proposition) == hash(
        (proposition.subject, proposition.relation, proposition.object)
    )
    assert hash(fact) == hash((fact.entity, fact.status))
    assert {fact: "known"}[
        Fact(Triple(Atom("alice"), Atom("age"), Atom("adult")))
    ] == "known"

    for value in (atom, number, variable, proposition, fact):
        assert "_hash" not in {field.name for field in fields(value)}
        restored = pickle.loads(pickle.dumps(value))
        assert restored == value
        assert hash(restored) == hash(value)


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
