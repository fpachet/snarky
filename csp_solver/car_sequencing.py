"""Car sequencing with GCC demand, ELEMENT lookup, and COUNT windows."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from snarky import (
    Atom,
    ChoiceSearchResult,
    ChoiceSolution,
    Fact,
    FiniteSequence,
    Number,
    Triple,
)

from .constraint_syntax import (
    PersistentConstraintTemplate,
    instantiate_constraint_templates,
    parse_constraint_templates,
)
from .solver import (
    CANDIDATE,
    CSP_PROBLEM,
    CSP_VARIABLE,
    KIND,
    VARIABLE,
    FiniteCSP,
    assignment_from_solution,
    finite_csp_rule_library,
    solve_finite_csp,
)

CAR_SLOT = Atom("car_slot")
CAR_OPTION_FLAG = Atom("car_option_flag")
CAR_LOOKUP_VALUE = Atom("car_lookup_value")
CAR_CLASS_DEMAND = Atom("car_class_demand")
CAR_OPTION_LOOKUP = Atom("car_option_lookup")
CAR_OPTION_WINDOW = Atom("car_option_window")
CLASS = Atom("class")
LOWER = Atom("lower")
UPPER = Atom("upper")
INDEX = Atom("index")
VALUE = Atom("value")
MEMBER = Atom("member")
CAPACITY = Atom("capacity")


@dataclass(frozen=True, slots=True)
class CarSequencingInstance:
    """Class demands, option/class matrix, and ``p/q`` capacities."""

    demands: tuple[int, ...]
    option_requirements: tuple[tuple[int, ...], ...]
    capacities: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        class_count = len(self.demands)
        if (
            class_count == 0
            or any(demand < 0 for demand in self.demands)
            or sum(self.demands) == 0
        ):
            raise ValueError("car demands must define at least one car")
        if len(self.option_requirements) != len(self.capacities):
            raise ValueError("every option requires one capacity")
        if any(
            len(row) != class_count or any(value not in {0, 1} for value in row)
            for row in self.option_requirements
        ):
            raise ValueError("option rows must contain one Boolean per class")
        if any(
            maximum < 0 or window < 1 or maximum > window
            for maximum, window in self.capacities
        ):
            raise ValueError("option capacities require 0 <= p <= q")

    @property
    def slot_count(self) -> int:
        return sum(self.demands)


CLASSIC_INSTANCE = CarSequencingInstance(
    demands=(1, 1, 2, 2, 2, 2),
    option_requirements=(
        (1, 0, 0, 0, 1, 1),
        (0, 0, 1, 1, 0, 1),
        (1, 0, 0, 0, 1, 0),
        (1, 1, 0, 1, 0, 0),
        (0, 0, 1, 0, 0, 0),
    ),
    capacities=((1, 2), (2, 3), (1, 3), (2, 5), (1, 5)),
)


def car_problem(instance: CarSequencingInstance) -> Atom:
    return Atom(
        f"car_sequencing_{instance.slot_count}_{len(instance.demands)}"
    )


def slot(position: int) -> Atom:
    return Atom(f"car_slot_{position}")


def option_flag(option: int, position: int) -> Atom:
    return Atom(f"car_option_{option}_slot_{position}")


def lookup_value(option: int, class_number: int) -> Atom:
    return Atom(f"car_option_{option}_class_{class_number}")


def car_sequencing_model(
    instance: CarSequencingInstance = CLASSIC_INSTANCE,
) -> FiniteCSP:
    """Build a fact-derived car-sequencing model."""

    problem = car_problem(instance)
    class_count = len(instance.demands)
    facts: list[Fact] = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
    for position in range(1, instance.slot_count + 1):
        variable = slot(position)
        facts.extend(
            (
                Fact(Triple(problem, VARIABLE, variable)),
                Fact(Triple(variable, KIND, CSP_VARIABLE)),
                Fact(Triple(variable, KIND, CAR_SLOT)),
                *(
                    Fact(Triple(variable, CANDIDATE, Number(class_number)))
                    for class_number in range(1, class_count + 1)
                ),
            )
        )
    for class_number, demand in enumerate(instance.demands, start=1):
        bound = Atom(f"car_demand_{class_number}")
        facts.extend(
            (
                Fact(Triple(bound, KIND, CAR_CLASS_DEMAND)),
                Fact(Triple(bound, CLASS, Number(class_number))),
                Fact(Triple(bound, LOWER, Number(demand))),
                Fact(Triple(bound, UPPER, Number(demand))),
            )
        )
    for option, requirements in enumerate(
        instance.option_requirements,
        start=1,
    ):
        for class_number, required in enumerate(requirements, start=1):
            variable = lookup_value(option, class_number)
            facts.extend(
                (
                    Fact(Triple(problem, VARIABLE, variable)),
                    Fact(Triple(variable, KIND, CSP_VARIABLE)),
                    Fact(Triple(variable, KIND, CAR_LOOKUP_VALUE)),
                    Fact(Triple(variable, CANDIDATE, Number(required))),
                )
            )
        for position in range(1, instance.slot_count + 1):
            flag = option_flag(option, position)
            facts.extend(
                (
                    Fact(Triple(problem, VARIABLE, flag)),
                    Fact(Triple(flag, KIND, CSP_VARIABLE)),
                    Fact(Triple(flag, KIND, CAR_OPTION_FLAG)),
                    Fact(Triple(flag, CANDIDATE, Number(0))),
                    Fact(Triple(flag, CANDIDATE, Number(1))),
                )
            )
            lookup = Atom(f"car_lookup_{option}_{position}")
            facts.extend(
                (
                    Fact(Triple(lookup, KIND, CAR_OPTION_LOOKUP)),
                    Fact(Triple(lookup, INDEX, slot(position))),
                    Fact(Triple(lookup, VALUE, flag)),
                    *(
                        Fact(
                            Triple(
                                lookup,
                                MEMBER,
                                FiniteSequence(
                                    (
                                        Number(class_number),
                                        lookup_value(option, class_number),
                                    )
                                ),
                            )
                        )
                        for class_number in range(1, class_count + 1)
                    ),
                )
            )
        maximum, window_size = instance.capacities[option - 1]
        for start in range(1, instance.slot_count - window_size + 2):
            window = Atom(f"car_window_{option}_{start}")
            facts.extend(
                (
                    Fact(Triple(window, KIND, CAR_OPTION_WINDOW)),
                    Fact(Triple(window, CAPACITY, Number(maximum))),
                    *(
                        Fact(
                            Triple(
                                window,
                                MEMBER,
                                FiniteSequence(
                                    (
                                        Number(offset),
                                        option_flag(option, start + offset - 1),
                                    )
                                ),
                            )
                        )
                        for offset in range(1, window_size + 1)
                    ),
                )
            )
    fact_tuple = tuple(facts)
    return FiniteCSP(
        problem,
        fact_tuple,
        {},
        constraints=instantiate_constraint_templates(
            _templates(),
            fact_tuple,
        ),
    )


@cache
def _templates() -> tuple[PersistentConstraintTemplate, ...]:
    return parse_constraint_templates(
        Path(__file__).with_suffix(".constraints").read_text()
    )


def solve_car_sequencing(
    instance: CarSequencingInstance = CLASSIC_INSTANCE,
    *,
    max_nodes: int = 200_000,
) -> ChoiceSearchResult:
    model = car_sequencing_model(instance)
    return solve_finite_csp(
        model,
        max_nodes=max_nodes,
        rule_groups=finite_csp_rule_library().finite_domain_groups,
    )


def sequence_from_solution(
    solution: ChoiceSolution,
    instance: CarSequencingInstance = CLASSIC_INSTANCE,
) -> tuple[int, ...]:
    assignment = assignment_from_solution(solution, car_problem(instance))
    return tuple(
        _integer(assignment[slot(position)])
        for position in range(1, instance.slot_count + 1)
    )


def validate_sequence(
    sequence: tuple[int, ...],
    instance: CarSequencingInstance = CLASSIC_INSTANCE,
) -> bool:
    if len(sequence) != instance.slot_count:
        return False
    if any(
        sequence.count(class_number) != demand
        for class_number, demand in enumerate(instance.demands, start=1)
    ):
        return False
    for requirements, (maximum, window_size) in zip(
        instance.option_requirements,
        instance.capacities,
        strict=True,
    ):
        flags = tuple(requirements[class_number - 1] for class_number in sequence)
        if any(
            sum(flags[start : start + window_size]) > maximum
            for start in range(len(flags) - window_size + 1)
        ):
            return False
    return True


def _integer(term) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise ValueError("a car-sequencing variable must contain an integer")
    return term.value


def main() -> None:
    result = solve_car_sequencing()
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        print(sequence_from_solution(solution))


if __name__ == "__main__":
    main()
