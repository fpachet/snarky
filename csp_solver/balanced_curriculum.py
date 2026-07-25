"""A balanced curriculum combining order, COUNT, ELEMENT, and LINEAR_SUM."""

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
    RuleGroup,
    Triple,
    parse_rule_groups,
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

CURRICULUM_COURSE = Atom("curriculum_course")
CURRICULUM_PERIOD = Atom("curriculum_period")
CURRICULUM_PREREQUISITE = Atom("curriculum_prerequisite")
CURRICULUM_MEMBERSHIP_CHANNEL = Atom("curriculum_membership_channel")
CURRICULUM_LOOKUP_VALUE = Atom("curriculum_lookup_value")
CURRICULUM_MEMBERSHIP = Atom("curriculum_membership")
NUMBER = Atom("number")
MINIMUM_COURSES = Atom("minimum_courses")
MAXIMUM_COURSES = Atom("maximum_courses")
MINIMUM_CREDITS = Atom("minimum_credits")
MAXIMUM_CREDITS = Atom("maximum_credits")
MEMBER = Atom("member")
INDEX = Atom("index")
VALUE = Atom("value")
LOAD_TERM = Atom("load_term")
BEFORE = Atom("before")
AFTER = Atom("after")


@dataclass(frozen=True, slots=True)
class Course:
    name: str
    credits: int

    def __post_init__(self) -> None:
        if not self.name or self.credits <= 0:
            raise ValueError("courses require a name and positive credits")


@dataclass(frozen=True, slots=True)
class CurriculumInstance:
    courses: tuple[Course, ...]
    prerequisites: tuple[tuple[str, str], ...]
    period_count: int
    minimum_courses: int
    maximum_courses: int
    minimum_credits: int
    maximum_credits: int

    def __post_init__(self) -> None:
        names = {course.name for course in self.courses}
        if len(names) != len(self.courses) or not names:
            raise ValueError("curriculum course names must be unique")
        if self.period_count < 1:
            raise ValueError("a curriculum needs at least one period")
        if not 0 <= self.minimum_courses <= self.maximum_courses:
            raise ValueError("invalid per-period course bounds")
        if not 0 <= self.minimum_credits <= self.maximum_credits:
            raise ValueError("invalid per-period credit bounds")
        if any(
            left not in names or right not in names
            for left, right in self.prerequisites
        ):
            raise ValueError("prerequisites must reference declared courses")


DEFAULT_INSTANCE = CurriculumInstance(
    courses=(
        Course("algebra", 3),
        Course("programming", 3),
        Course("algorithms", 4),
        Course("logic", 2),
        Course("databases", 4),
        Course("capstone", 3),
    ),
    prerequisites=(
        ("algebra", "algorithms"),
        ("algebra", "logic"),
        ("programming", "databases"),
        ("algorithms", "capstone"),
        ("logic", "capstone"),
    ),
    period_count=4,
    minimum_courses=1,
    maximum_courses=2,
    minimum_credits=2,
    maximum_credits=8,
)


def course_variable(name: str) -> Atom:
    return Atom(f"course_{name}")


def period_entity(number: int) -> Atom:
    return Atom(f"curriculum_period_{number}")


def membership(course: str, period: int) -> Atom:
    return Atom(f"course_{course}_in_period_{period}")


def lookup_value(target_period: int, actual_period: int) -> Atom:
    return Atom(f"period_{target_period}_lookup_{actual_period}")


def curriculum_problem(instance: CurriculumInstance = DEFAULT_INSTANCE) -> Atom:
    return Atom(
        f"balanced_curriculum_{len(instance.courses)}_{instance.period_count}"
    )


def balanced_curriculum_model(
    instance: CurriculumInstance = DEFAULT_INSTANCE,
) -> FiniteCSP:
    """Build a fact-derived curriculum feasibility model."""

    problem = curriculum_problem(instance)
    facts: list[Fact] = [Fact(Triple(problem, KIND, CSP_PROBLEM))]
    for course in instance.courses:
        variable = course_variable(course.name)
        facts.extend(
            (
                Fact(Triple(problem, VARIABLE, variable)),
                Fact(Triple(variable, KIND, CSP_VARIABLE)),
                Fact(Triple(variable, KIND, CURRICULUM_COURSE)),
                *(
                    Fact(Triple(variable, CANDIDATE, Number(period)))
                    for period in range(1, instance.period_count + 1)
                ),
            )
        )
    for target_period in range(1, instance.period_count + 1):
        period = period_entity(target_period)
        facts.extend(
            (
                Fact(Triple(period, KIND, CURRICULUM_PERIOD)),
                Fact(Triple(period, NUMBER, Number(target_period))),
                Fact(
                    Triple(
                        period,
                        MINIMUM_COURSES,
                        Number(instance.minimum_courses),
                    )
                ),
                Fact(
                    Triple(
                        period,
                        MAXIMUM_COURSES,
                        Number(instance.maximum_courses),
                    )
                ),
                Fact(
                    Triple(
                        period,
                        MINIMUM_CREDITS,
                        Number(instance.minimum_credits),
                    )
                ),
                Fact(
                    Triple(
                        period,
                        MAXIMUM_CREDITS,
                        Number(instance.maximum_credits),
                    )
                ),
            )
        )
        for actual_period in range(1, instance.period_count + 1):
            variable = lookup_value(target_period, actual_period)
            fixed = int(target_period == actual_period)
            facts.extend(
                (
                    Fact(Triple(problem, VARIABLE, variable)),
                    Fact(Triple(variable, KIND, CSP_VARIABLE)),
                    Fact(Triple(variable, KIND, CURRICULUM_LOOKUP_VALUE)),
                    Fact(Triple(variable, CANDIDATE, Number(fixed))),
                )
            )
        for position, course in enumerate(instance.courses, start=1):
            boolean = membership(course.name, target_period)
            facts.extend(
                (
                    Fact(Triple(problem, VARIABLE, boolean)),
                    Fact(Triple(boolean, KIND, CSP_VARIABLE)),
                    Fact(Triple(boolean, KIND, CURRICULUM_MEMBERSHIP)),
                    Fact(Triple(boolean, CANDIDATE, Number(0))),
                    Fact(Triple(boolean, CANDIDATE, Number(1))),
                    Fact(
                        Triple(
                            period,
                            LOAD_TERM,
                            FiniteSequence(
                                (
                                    Number(position),
                                    Number(course.credits),
                                    boolean,
                                )
                            ),
                        )
                    ),
                )
            )
            channel = Atom(
                f"curriculum_channel_{course.name}_{target_period}"
            )
            facts.extend(
                (
                    Fact(
                        Triple(
                            channel,
                            KIND,
                            CURRICULUM_MEMBERSHIP_CHANNEL,
                        )
                    ),
                    Fact(
                        Triple(
                            channel,
                            INDEX,
                            course_variable(course.name),
                        )
                    ),
                    Fact(Triple(channel, VALUE, boolean)),
                    *(
                        Fact(
                            Triple(
                                channel,
                                MEMBER,
                                FiniteSequence(
                                    (
                                        Number(actual_period),
                                        lookup_value(
                                            target_period,
                                            actual_period,
                                        ),
                                    )
                                ),
                            )
                        )
                        for actual_period in range(
                            1,
                            instance.period_count + 1,
                        )
                    ),
                )
            )
    for number, (required, course) in enumerate(
        instance.prerequisites,
        start=1,
    ):
        prerequisite = Atom(f"curriculum_prerequisite_{number}")
        facts.extend(
            (
                Fact(
                    Triple(
                        prerequisite,
                        KIND,
                        CURRICULUM_PREREQUISITE,
                    )
                ),
                Fact(
                    Triple(
                        prerequisite,
                        BEFORE,
                        course_variable(required),
                    )
                ),
                Fact(
                    Triple(
                        prerequisite,
                        AFTER,
                        course_variable(course),
                    )
                ),
                Fact(
                    Triple(
                        prerequisite,
                        MEMBER,
                        FiniteSequence(
                            (Number(1), course_variable(required))
                        ),
                    )
                ),
                Fact(
                    Triple(
                        prerequisite,
                        MEMBER,
                        FiniteSequence(
                            (Number(2), course_variable(course))
                        ),
                    )
                ),
            )
        )
    fact_tuple = tuple(facts)
    return FiniteCSP(
        problem,
        fact_tuple,
        {},
        _report_groups(),
        instantiate_constraint_templates(_templates(), fact_tuple),
    )


@cache
def _templates() -> tuple[PersistentConstraintTemplate, ...]:
    return parse_constraint_templates(
        Path(__file__).with_suffix(".constraints").read_text()
    )


@cache
def _report_groups() -> tuple[RuleGroup, ...]:
    return parse_rule_groups(Path(__file__).with_suffix(".rules").read_text())


def solve_balanced_curriculum(
    instance: CurriculumInstance = DEFAULT_INSTANCE,
    *,
    max_nodes: int = 200_000,
) -> ChoiceSearchResult:
    model = balanced_curriculum_model(instance)
    return solve_finite_csp(
        model,
        max_nodes=max_nodes,
        rule_groups=(
            *finite_csp_rule_library().finite_domain_groups,
            *model.groups,
        ),
    )


def schedule_from_solution(
    solution: ChoiceSolution,
    instance: CurriculumInstance = DEFAULT_INSTANCE,
) -> dict[str, int]:
    assignment = assignment_from_solution(solution, curriculum_problem(instance))
    return {
        course.name: _integer(assignment[course_variable(course.name)])
        for course in instance.courses
    }


def validate_schedule(
    schedule: dict[str, int],
    instance: CurriculumInstance = DEFAULT_INSTANCE,
) -> bool:
    if set(schedule) != {course.name for course in instance.courses}:
        return False
    if any(
        schedule[required] >= schedule[course]
        for required, course in instance.prerequisites
    ):
        return False
    credits = {course.name: course.credits for course in instance.courses}
    for period in range(1, instance.period_count + 1):
        selected = [name for name, assigned in schedule.items() if assigned == period]
        load = sum(credits[name] for name in selected)
        if not instance.minimum_courses <= len(selected) <= instance.maximum_courses:
            return False
        if not instance.minimum_credits <= load <= instance.maximum_credits:
            return False
    return True


def _integer(term) -> int:
    if not isinstance(term, Number) or not isinstance(term.value, int):
        raise ValueError("a curriculum variable must contain an integer")
    return term.value


def main() -> None:
    result = solve_balanced_curriculum()
    print(f"status={result.status} nodes={result.explored_nodes}")
    for solution in result.solutions:
        schedule = schedule_from_solution(solution)
        for name, period in sorted(schedule.items(), key=lambda item: item[1]):
            print(f"period {period}: {name}")


if __name__ == "__main__":
    main()
