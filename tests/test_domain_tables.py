from snarky import Atom, Fact, Triple, Variable
from snarky.instantiation.domain_tables import (
    _add_row_projection,
    _CompactTableDefinition,
    _CompactTableState,
    _DomainRow,
    _remove_row_projection,
)
from snarky.substitutions import BindingFrame
from snarky.terms import Term


def _row(
    subject: str,
    object_: str,
    x: Variable,
    y: Variable,
) -> _DomainRow:
    subject_term = Atom(subject)
    object_term = Atom(object_)
    return _DomainRow(
        Fact(Triple(subject_term, Atom("relation"), object_term)),
        ((x, subject_term), (y, object_term)),
    )


def test_compact_table_preserves_slots_and_filters_with_bitsets() -> None:
    x = Variable("x")
    y = Variable("y")
    first = _row("a", "b", x, y)
    second = _row("a", "c", x, y)
    third = _row("d", "b", x, y)
    table = _CompactTableDefinition.build(
        {row.fact: row for row in (first, second, third)},
        (x, y),
    )
    state = _CompactTableState.initial(table)

    assert table.present_mask == 0b111
    assert table.facts(state.active_mask) == (
        first.fact,
        second.fact,
        third.fact,
    )

    frame = BindingFrame(((x, Atom("a")),))
    mask, intersections = table.mask_for_frame(
        state.active_mask,
        (x, y),
        frame,
    )
    assert intersections == 1
    assert tuple(table.rows_for_mask(mask)) == (first, second)

    assert table.remove(first.fact) == (first, 0b001)
    state.active_mask &= table.present_mask
    fourth = _row("d", "e", x, y)
    assert table.add(fourth) == 0b1000
    state.reset(table)
    assert table.facts(state.active_mask) == (
        second.fact,
        third.fact,
        fourth.fact,
    )


def test_row_projections_track_shared_values_incrementally() -> None:
    x = Variable("x")
    y = Variable("y")
    first = _row("a", "b", x, y)
    second = _row("a", "c", x, y)
    counts: dict[Variable, dict[Term, int]] = {x: {}, y: {}}
    domains: dict[Variable, set[Term]] = {x: set(), y: set()}

    _add_row_projection(first, counts, domains)
    _add_row_projection(second, counts, domains)

    assert counts[x] == {Atom("a"): 2}
    assert domains[x] == {Atom("a")}
    assert domains[y] == {Atom("b"), Atom("c")}

    _remove_row_projection(first, counts, domains)

    assert counts[x] == {Atom("a"): 1}
    assert domains[x] == {Atom("a")}
    assert domains[y] == {Atom("c")}
