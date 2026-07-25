"""Compiled choice projection for the canonical finite-CSP vocabulary."""

from __future__ import annotations

from collections.abc import Sequence

from snarky import (
    Atom,
    ChoiceAlternative,
    ChoicePoint,
    Fact,
    InferenceSession,
    RuleGroup,
    Substitution,
    Triple,
    Variable,
    render_term,
)

from .finite_domain_projection import FiniteDomainProjection

CSP_PROBLEM = Atom("csp_problem")
KIND = Atom("kind")
VARIABLE = Atom("variable")
CANDIDATE = Atom("candidate")
VALUE = Atom("value")
DECISION = Atom("decision")
CHOICE_WEIGHT = Atom("choice_weight")

_PROBLEM_VARIABLE = Variable("problem")
_VARIABLE_VARIABLE = Variable("variable")
_CHOSEN_VARIABLE = Variable("chosen")
_WEIGHT_VARIABLE = Variable("weight")


class FiniteDomainChoiceProvider:
    """Project the standard CSP ``CHOICE`` rule without re-running joins.

    The generated point names, alternatives, substitutions, supports, and
    ordering match ``RuleChoiceProvider`` for ``choose_csp_value``. Ordinary
    deterministic groups remain available through ``propagation_groups``.
    """

    def __init__(
        self,
        propagation_groups: Sequence[RuleGroup],
        projection: FiniteDomainProjection | None = None,
    ) -> None:
        self.propagation_groups = tuple(propagation_groups)
        self.projection = projection or FiniteDomainProjection()

    def __call__(
        self,
        session: InferenceSession,
    ) -> tuple[ChoicePoint, ...]:
        snapshot = self.projection.snapshot(session)
        decided = {
            variable for variable, _, _ in snapshot.decisions
        }

        points: list[ChoicePoint] = []
        for problem, variable, _ in snapshot.problem_variables:
            if (
                problem not in snapshot.problems
                or variable in snapshot.values
                or variable in decided
            ):
                continue
            outer = Substitution(
                (
                    (_PROBLEM_VARIABLE, problem),
                    (_VARIABLE_VARIABLE, variable),
                )
            )
            alternatives: list[ChoiceAlternative] = []
            ordered_candidates = sorted(
                snapshot.candidates.get(variable, {}).items(),
                key=lambda item: snapshot.candidate_order[item[1]],
            )
            for chosen, candidate_fact in ordered_candidates:
                weight = snapshot.weights.get((variable, chosen))
                if weight is None:
                    continue
                weight_term, numeric_weight, weight_fact = weight
                substitution = outer.extend(
                    (
                        (_CHOSEN_VARIABLE, chosen),
                        (_WEIGHT_VARIABLE, weight_term),
                    )
                )
                decision = Fact(Triple(variable, DECISION, chosen))
                alternatives.append(
                    ChoiceAlternative(
                        render_term(chosen),
                        (decision,),
                        chosen,
                        numeric_weight,
                        {
                            "rule": "choose_csp_value",
                            "rule_group": "apply_csp_choices",
                            "substitution": substitution,
                            "supports": (candidate_fact, weight_fact),
                        },
                    )
                )
            if not alternatives:
                continue
            context_label = ",".join(
                f"{name}={render_term(value)}"
                for name, value in outer.key
            )
            points.append(
                ChoicePoint(
                    "apply_csp_choices:choose_csp_value:0"
                    f"[{context_label}]",
                    tuple(alternatives),
                    variable,
                    {
                        "rule": "choose_csp_value",
                        "rule_group": "apply_csp_choices",
                        "action_index": 0,
                        "substitution": outer,
                    },
                )
            )
        return tuple(points)
