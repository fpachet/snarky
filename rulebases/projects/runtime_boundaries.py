"""Executable examples of propagation, saved proofs, and pure preferences.

Run from the checkout with ``python -m rulebases.projects.runtime_boundaries``.
"""

from snarky import (
    Atom,
    ChoiceAlternative,
    ChoicePoint,
    Fact,
    InferenceSession,
    SessionChoiceSearch,
    parse_rule_groups,
)
from snarky.factors import FactorModel, evaluate_factor_model
from snarky.parser_factors import parse_factor_groups


def propagation_example() -> tuple[Fact, ...]:
    """Search observes closure even if a custom filter needs several calls."""

    session = InferenceSession(tuple(Fact(Atom(x)) for x in ("a", "b", "c")))

    def narrow(current: InferenceSession) -> None:
        if len(current.facts) > 1:
            current.retract(current.facts[-1])

    result = SessionChoiceSearch(
        groups=(), choices=lambda current: (),
        goal=lambda current: len(current.facts) == 1, propagators=(narrow,),
    ).solve(session)
    assert len(session.facts) == 3  # Search preserves the caller's session.
    return result.solutions[0].session.facts


def snapshot_example() -> tuple[int, int]:
    """A saved proof survives rollback; assumptions shorten current proofs."""

    (group,) = parse_rule_groups(
        """
        GROUP explanation
            RULE infer
            WHEN
                seed
            THEN
                ADD conclusion
            END
        END_GROUP
        """
    )
    session = InferenceSession((Fact(Atom("seed")),))
    checkpoint = session.checkpoint()
    session.run_group(group)
    saved = session.snapshot()
    conclusion = Fact(Atom("conclusion"))
    session.assume(conclusion)
    current_depth = session.provenance.depth(conclusion)
    session.rollback(checkpoint)
    session.release(checkpoint)
    assert conclusion not in session.facts
    return saved.provenance.depth(conclusion), current_depth


def preferences_example() -> tuple[str, float]:
    """A local choice priority and a factor cannot override a hard restriction."""

    rejected, accepted = Fact(Atom("rejected")), Fact(Atom("accepted"))
    point = ChoicePoint("select", (
        ChoiceAlternative("rejected", (rejected,), weight=100.0),
        ChoiceAlternative("accepted", (accepted,), weight=1.0),
    ))
    result = SessionChoiceSearch(
        groups=(), choices=lambda current: (point,),
        contradiction=lambda current: rejected in current.facts,
        goal=lambda current: accepted in current.facts,
    ).solve(InferenceSession(()))
    solution = result.solutions[0]
    (group,) = parse_factor_groups(
        """
        FACTOR_GROUP preferences
            FACTOR accepted_bonus
            SCOPE accepted
            LOG_WEIGHT 2.0
            WHEN
                accepted
            END_FACTOR
        END_FACTOR_GROUP
        """
    )
    before = solution.session.snapshot()
    evaluation = evaluate_factor_model(FactorModel("example", (group,)), before.facts)
    assert solution.session.facts == before.facts
    assert solution.session.events == before.events
    assert solution.log_weight == 0.0  # The factor did not rewrite CHOICE weights.
    return solution.decisions[0].alternative, evaluation.log_score


def main() -> None:
    print("fixed point:", propagation_example())
    print("saved and assumed proof depths:", snapshot_example())
    print("feasible choice and independent factor score:", preferences_example())


if __name__ == "__main__":
    main()
