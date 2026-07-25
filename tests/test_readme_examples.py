from snarky import (
    Atom,
    Fact,
    ForwardEngine,
    Rule,
    Triple,
    Variable,
    add,
    parse_rules,
    parse_term,
    when,
)


def test_programmatic_readme_example() -> None:
    x = Variable("x")
    y = Variable("y")
    z = Variable("z")
    grandparent = Rule(
        name="grandparent",
        premises=(
            when(Triple(x, Atom("parent_of"), y)),
            when(Triple(y, Atom("parent_of"), z)),
        ),
        actions=(add(Triple(x, Atom("grandparent_of"), z)),),
    )
    facts = (
        Fact(Triple(Atom("alice"), Atom("parent_of"), Atom("bob"))),
        Fact(Triple(Atom("bob"), Atom("parent_of"), Atom("clara"))),
    )

    result = ForwardEngine((grandparent,)).run(facts)

    assert Fact(
        Triple(Atom("alice"), Atom("grandparent_of"), Atom("clara"))
    ) in result.facts


def test_textual_readme_example() -> None:
    rules = parse_rules(
        """
        RULE grandparent
        WHEN
            ($x parent_of $y)
            ($y parent_of $z)
        THEN
            ADD ($x grandparent_of $z)
        END
        """
    )
    facts = (
        Fact(parse_term("(alice parent_of bob)")),
        Fact(parse_term("(bob parent_of clara)")),
    )

    result = ForwardEngine(rules).run(facts)

    assert Fact(parse_term("(alice grandparent_of clara)")) in result.facts
