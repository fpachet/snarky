"""Compiled execution of the canonical finite-domain classification rules."""

from __future__ import annotations

from dataclasses import dataclass

from snarky import (
    Atom,
    Fact,
    InferenceSession,
    Rule,
    RuleGroup,
    Substitution,
    Term,
    Triple,
    Variable,
)

from .finite_domain_projection import FiniteDomainProjection

CSP_PROBLEM = Atom("csp_problem")
CSP_VARIABLE = Atom("csp_variable")
KIND = Atom("kind")
VARIABLE = Atom("variable")
CANDIDATE = Atom("candidate")
VALUE = Atom("value")
DECISION = Atom("decision")
STATE = Atom("state")
SOLVED = Atom("solved")
CONTRADICTION = Atom("contradiction")
EMPTY_DOMAIN = Atom("empty_domain")
SEARCH = Atom("search")
INVALID_CHOICE = Atom("invalid_choice")

_VARIABLE_VARIABLE = Variable("variable")
_VALUE_VARIABLE = Variable("value")
_CHOSEN_VARIABLE = Variable("chosen")
_OTHER_VARIABLE = Variable("other")
_PROBLEM_VARIABLE = Variable("problem")
_SOME_VARIABLE = Variable("some_variable")


@dataclass(frozen=True, slots=True)
class _ClassificationRules:
    choices: RuleGroup
    domains: RuleGroup
    problems: RuleGroup
    restrict_chosen_domain: Rule
    reject_missing_choice_value: Rule
    retract_invalid_singleton: Rule
    assign_singleton: Rule
    detect_empty_domain: Rule
    recognize_solved_problem: Rule


class FiniteDomainStatePropagator:
    """Execute standard singleton/problem rules from a direct fact projection.

    Activations are fired through the normal session mutation/provenance path;
    only their eligibility lookup is compiled.
    """

    watched_relations = frozenset(
        (KIND, VARIABLE, CANDIDATE, VALUE, DECISION, STATE)
    )

    def __init__(
        self,
        problem: Atom,
        choices: RuleGroup,
        domains: RuleGroup,
        problems: RuleGroup,
        projection: FiniteDomainProjection | None = None,
    ) -> None:
        self.problem = problem
        self.projection = projection or FiniteDomainProjection()
        choice_rules = {rule.name: rule for rule in choices.rules}
        domain_rules = {rule.name: rule for rule in domains.rules}
        problem_rules = {rule.name: rule for rule in problems.rules}
        self._rules = _ClassificationRules(
            choices,
            domains,
            problems,
            choice_rules["restrict_chosen_domain"],
            choice_rules["reject_missing_choice_value"],
            domain_rules["retract_invalid_singleton"],
            domain_rules["assign_singleton"],
            problem_rules["detect_empty_domain"],
            problem_rules["recognize_solved_problem"],
        )

    def __call__(self, session: InferenceSession) -> None:
        snapshot = self.projection.snapshot(session)
        candidates = dict(snapshot.candidates)
        decisions = tuple(snapshot.decisions)
        value_facts = {
            variable: list(known.items())
            for variable, known in snapshot.values.items()
        }
        csp_variables = snapshot.csp_variables
        problem_variables = [
            (variable, fact)
            for problem, variable, fact in snapshot.problem_variables
            if problem == self.problem
        ]
        problem_kind = snapshot.problems.get(self.problem)
        present = set(snapshot.present)
        contradiction = (
            Fact(Triple(self.problem, STATE, CONTRADICTION))
            in present
        )

        for variable, chosen, decision_fact in decisions:
            domain = candidates.get(variable, {})
            if chosen not in domain:
                contradiction_fact = Fact(
                    Triple(SEARCH, STATE, CONTRADICTION)
                )
                invalid_fact = Fact(
                    Triple(SEARCH, INVALID_CHOICE, variable)
                )
                if (
                    contradiction_fact not in present
                    or invalid_fact not in present
                ):
                    session._fire_compiled_activation(
                        self._rules.choices,
                        self._rules.reject_missing_choice_value,
                        Substitution(
                            (
                                (_VARIABLE_VARIABLE, variable),
                                (_CHOSEN_VARIABLE, chosen),
                            )
                        ),
                        (decision_fact,),
                    )
                    present.add(contradiction_fact)
                    present.add(invalid_fact)
                continue
            restricted = dict(domain)
            for other, candidate_fact in tuple(domain.items()):
                if other == chosen:
                    continue
                session._fire_compiled_activation(
                    self._rules.choices,
                    self._rules.restrict_chosen_domain,
                    Substitution(
                        (
                            (_VARIABLE_VARIABLE, variable),
                            (_CHOSEN_VARIABLE, chosen),
                            (_OTHER_VARIABLE, other),
                        )
                    ),
                    (decision_fact, candidate_fact),
                )
                restricted.pop(other)
                present.discard(candidate_fact)
            candidates[variable] = restricted

        for variable, known_values in tuple(value_facts.items()):
            domain = candidates.get(variable, {})
            retained: list[tuple[Term, Fact]] = []
            for value, value_fact in known_values:
                if value in domain:
                    retained.append((value, value_fact))
                    continue
                session._fire_compiled_activation(
                    self._rules.domains,
                    self._rules.retract_invalid_singleton,
                    Substitution(
                        (
                            (_VARIABLE_VARIABLE, variable),
                            (_VALUE_VARIABLE, value),
                        )
                    ),
                    (value_fact,),
                )
                present.discard(value_fact)
            if retained:
                value_facts[variable] = retained
            else:
                value_facts.pop(variable, None)

        for variable, kind_fact in csp_variables.items():
            domain = candidates.get(variable, {})
            if len(domain) != 1 or variable in value_facts:
                continue
            value, candidate_fact = next(iter(domain.items()))
            session._fire_compiled_activation(
                self._rules.domains,
                self._rules.assign_singleton,
                Substitution(
                    (
                        (_VARIABLE_VARIABLE, variable),
                        (_VALUE_VARIABLE, value),
                    )
                ),
                (kind_fact, candidate_fact),
            )
            derived_value = Fact(Triple(variable, VALUE, value))
            value_facts[variable] = [(value, derived_value)]
            present.add(derived_value)

        if problem_kind is None:
            return
        for variable, variable_fact in problem_variables:
            if candidates.get(variable):
                continue
            empty_fact = Fact(
                Triple(self.problem, EMPTY_DOMAIN, variable)
            )
            contradiction_fact = Fact(
                Triple(self.problem, STATE, CONTRADICTION)
            )
            if (
                empty_fact in present
                and contradiction_fact in present
            ):
                contradiction = True
                continue
            session._fire_compiled_activation(
                self._rules.problems,
                self._rules.detect_empty_domain,
                Substitution(
                    (
                        (_PROBLEM_VARIABLE, self.problem),
                        (_VARIABLE_VARIABLE, variable),
                    )
                ),
                (problem_kind, variable_fact),
            )
            contradiction = True
            present.add(empty_fact)
            present.add(contradiction_fact)

        if (
            problem_variables
            and not contradiction
            and all(
                variable in value_facts
                for variable, _ in problem_variables
            )
        ):
            solved_fact = Fact(Triple(self.problem, STATE, SOLVED))
            if solved_fact not in present:
                some_variable, variable_fact = problem_variables[0]
                session._fire_compiled_activation(
                    self._rules.problems,
                    self._rules.recognize_solved_problem,
                    Substitution(
                        (
                            (_PROBLEM_VARIABLE, self.problem),
                            (_SOME_VARIABLE, some_variable),
                        )
                    ),
                    (problem_kind, variable_fact),
                )
