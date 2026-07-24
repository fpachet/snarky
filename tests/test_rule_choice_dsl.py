from snarky import (
    Atom,
    Choice,
    ChoiceEventKind,
    ChoiceSearchStatus,
    Fact,
    ForwardEngine,
    InferenceSession,
    Number,
    RuleChoiceProvider,
    SessionChoiceSearch,
    Triple,
    parse_rule_groups,
    parse_term,
)


def _fact(text: str) -> Fact:
    return Fact(parse_term(text))


def test_choice_action_parses_target_source_and_weight() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP choices
            RULE select_value
            WHEN
                (problem variable $item)
                NOT EXISTS ($item value $known)
            THEN
                CHOICE ($item value $candidate) WEIGHT $weight
                FROM
                    ($item candidate $candidate)
                    ($item weight SEQ[$candidate $weight])
                END_CHOICE
            END
        END_GROUP
        """
    )

    action = group.rules[0].actions[0]
    assert isinstance(action, Choice)
    assert action.entity == parse_term("($item value $candidate)")
    assert action.weight == parse_term("$weight")
    assert len(action.premises) == 2


def test_rule_choice_provider_selects_one_fact_instantiation() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP choices
            RULE select_value
            WHEN
                (problem variable $item)
                NOT EXISTS ($item value $known)
            THEN
                CHOICE ($item value $candidate) WEIGHT $weight
                FROM
                    ($item candidate $candidate)
                    ($item weight SEQ[$candidate $weight])
                END_CHOICE
            END
        END_GROUP
        """
    )
    provider = RuleChoiceProvider((group,))
    parent = ForwardEngine(()).create_session(
        (
            _fact("(problem variable object)"),
            _fact("(object candidate 1)"),
            _fact("(object candidate 2)"),
            _fact("(object weight SEQ[1 0.1])"),
            _fact("(object weight SEQ[2 0.9])"),
        )
    )
    result = SessionChoiceSearch(
        provider.propagation_groups,
        provider,
        lambda session: _fact("(object value 2)") in session.facts,
        max_solutions=1,
    ).solve(parent)

    assert result.status is ChoiceSearchStatus.SOLVED
    assert _fact("(object value 2)") in result.solutions[0].session.facts
    assert _fact("(object value 1)") not in result.solutions[0].session.facts
    assert parent.facts == (
        _fact("(problem variable object)"),
        _fact("(object candidate 1)"),
        _fact("(object candidate 2)"),
        _fact("(object weight SEQ[1 0.1])"),
        _fact("(object weight SEQ[2 0.9])"),
    )


def test_multiple_choices_in_one_rule_are_sequential() -> None:
    (group,) = parse_rule_groups(
        """
        GROUP choices
            RULE build_pair
            WHEN
                (object state open)
            THEN
                CHOICE (object first $first)
                FROM
                    (source first_candidate $first)
                END_CHOICE

                CHOICE (object second $second)
                FROM
                    (source second_candidate $second)
                    $second != $first
                END_CHOICE

                ADD (object state complete)
            END
        END_GROUP
        """
    )
    provider = RuleChoiceProvider((group,))
    session = ForwardEngine(()).create_session(
        (
            _fact("(object state open)"),
            _fact("(source first_candidate 1)"),
            _fact("(source first_candidate 2)"),
            _fact("(source second_candidate 1)"),
            _fact("(source second_candidate 2)"),
            _fact("(source second_candidate 3)"),
        )
    )

    def complete(current: InferenceSession) -> bool:
        return _fact("(object state complete)") in current.facts

    result = SessionChoiceSearch(
        provider.propagation_groups,
        provider,
        complete,
        max_solutions=4,
    ).solve(session)
    pairs = {
        (
            next(
                value
                for value in (1, 2)
                if Fact(
                    Triple(
                        Atom("object"),
                        Atom("first"),
                        Number(value),
                    )
                )
                in solution.session.facts
            ),
            next(
                value
                for value in (1, 2, 3)
                if Fact(
                    Triple(
                        Atom("object"),
                        Atom("second"),
                        Number(value),
                    )
                )
                in solution.session.facts
            ),
        )
        for solution in result.solutions
    }

    assert pairs == {(1, 2), (1, 3), (2, 1), (2, 3)}
    assert all(len(solution.decisions) == 2 for solution in result.solutions)
    assert sum(
        event.kind is ChoiceEventKind.CHOICE for event in result.events
    ) >= 3
