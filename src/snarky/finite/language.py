"""Declarative MODEL documents compiled to the same validated Python objects.

Existing GROUP and factor-premise syntax is reused. No Python expression is
executed by this parser; callbacks remain explicit Python extensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..factors import FactorDefinition, FactorGroup, FactorModel
from ..facts import Fact
from ..parser import ParseError, parse_factor_groups, parse_rule_groups, parse_term
from ..parser_actions import _parse_fact_template
from ..parser_premises import _parse_premise_block
from ..rules import RuleGroup
from ..terms import Atom, FiniteSequence, Number, Term
from .constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    ConstraintOperator,
    CountConstraint,
    ElementConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    LinearSumConstraint,
    NValueConstraint,
    PersistentConstraint,
    SumConstraint,
    TableConstraint,
)
from .factors import FactorObjective, IntegerFactor, TableFactor
from .inference import infer
from .measure import Measure, WeightTable, negative_log2_measure
from .model import (
    Constraint,
    FactConstraint,
    FiniteModel,
    FiniteVariable,
    GuardedConstraint,
    LinearObjective,
    Query,
    QueryKind,
    QueryResult,
)
from .oracle import enumerate_model
from .predicates import integer
from .search import solve


@dataclass(frozen=True, slots=True)
class QueryRequest:
    name: str
    query: Query = Query()
    backend: str = "native"
    bounding: str = "auto"
    value_policy: str = "declared"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("query requires a name")
        if self.bounding not in ("auto", "local"):
            raise ValueError("BOUNDING must be auto or local")
        if self.value_policy not in ("declared", "objective"):
            raise ValueError("VALUE_POLICY must be declared or objective")
        if (self.bounding != "auto" or self.value_policy != "declared") and (
            self.backend != "native"
            or self.query.kind not in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE)
        ):
            raise ValueError("search options require native optimization")
        if self.backend not in (
            "native",
            "enumeration",
            "weighted_search",
            "regular_bp",
        ):
            raise ValueError(f"unknown backend {self.backend!r}")
        if self.backend in (
            "weighted_search",
            "regular_bp",
        ) and self.query.kind not in (
            QueryKind.PARTITION,
            QueryKind.SAMPLE_EXACT,
        ):
            raise ValueError(f"{self.backend} supports probability queries only")

    def execute(self, model: FiniteModel) -> QueryResult:
        if self.backend == "native":
            return solve(
                model,
                self.query,
                bounding=self.bounding,
                value_policy=self.value_policy,
            )
        if self.backend == "enumeration":
            return enumerate_model(model, self.query)
        return infer(model, self.query, backend=self.backend)


@dataclass(frozen=True, slots=True)
class ModelDocument:
    model: FiniteModel
    queries: tuple[QueryRequest, ...] = ()

    def __post_init__(self) -> None:
        queries = tuple(self.queries)
        if len({request.name for request in queries}) != len(queries):
            raise ValueError("duplicate query names")
        for request in queries:
            if (
                request.query.kind in (QueryKind.MINIMIZE, QueryKind.MAXIMIZE)
                and self.model.objective is None
            ):
                raise ValueError("optimization query requires an explicit objective")
        object.__setattr__(self, "queries", queries)

    def execute(self, name: str | None = None) -> QueryResult:
        if name is None:
            if len(self.queries) > 1:
                raise ValueError("select one of the named queries")
            request = self.queries[0] if self.queries else QueryRequest("solve")
        else:
            selected = next((q for q in self.queries if q.name == name), None)
            if selected is None:
                raise ValueError(f"unknown query {name!r}")
            request = selected
        return request.execute(self.model)


class _Cursor:
    def __init__(self, text: str) -> None:
        self.lines = [
            (i, line.strip())
            for i, line in enumerate(text.splitlines(), 1)
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.position = 0
        self.line_number = 1

    @property
    def done(self) -> bool:
        return self.position >= len(self.lines)

    def take(self) -> str:
        if self.done:
            raise ParseError("unexpected end of model document")
        self.line_number, line = self.lines[self.position]
        self.position += 1
        return line

    def block(self, end: str) -> list[str]:
        lines: list[str] = []
        while not self.done:
            line = self.take()
            if line == end:
                return lines
            lines.append(line)
        raise ParseError(f"missing {end}")


def _atom(text: str) -> Atom:
    value = parse_term(text)
    if not isinstance(value, Atom):
        raise ParseError("identifier must be an atom, not a rule variable or number")
    return value


def _sequence(text: str) -> tuple[Term, ...]:
    value = parse_term(text)
    if not isinstance(value, FiniteSequence):
        raise ParseError("expected an ordered SEQ[...] value")
    return value.elements


def _fact(text: str) -> Fact:
    entity, status = _parse_fact_template(text, "FACT")
    return Fact(entity, status)


def _terms(text: str) -> tuple[tuple[int, Term], ...]:
    terms = []
    for entry in _sequence(text):
        if not isinstance(entry, FiniteSequence) or len(entry.elements) != 2:
            raise ParseError("TERMS requires SEQ[SEQ[coefficient variable] ...]")
        coefficient, variable = entry.elements
        terms.append((integer(coefficient), variable))
    return tuple(terms)


class _Fields:
    def __init__(self, lines: list[str], *, repeated: tuple[str, ...] = ()) -> None:
        self.single: dict[str, str] = {}
        self.multiple: dict[str, list[str]] = {key: [] for key in repeated}
        for line in lines:
            key, separator, value = line.partition(" ")
            if not separator:
                raise ParseError(f"expected field and value, got {line!r}")
            if key in repeated:
                self.multiple[key].append(value.strip())
            elif key in self.single:
                raise ParseError(f"duplicate field {key!r}")
            else:
                self.single[key] = value.strip()

    def take(self, name: str, default: str | None = None) -> str:
        if name not in self.single:
            if default is None:
                raise ParseError(f"missing {name}")
            return default
        return self.single.pop(name)

    def finish(self) -> None:
        if self.single:
            raise ParseError(f"unknown or unused fields: {', '.join(self.single)}")


def _constraint(name: Atom, lines: list[str]) -> Constraint:
    fields = _Fields(lines, repeated=("ALLOW", "REQUIRE", "FORBID"))
    kind = fields.take("KIND")
    guard = fields.single.pop("GUARD", None)
    if kind == "FACTS":
        if guard is not None or fields.multiple["ALLOW"]:
            raise ParseError("FACTS constraints accept REQUIRE and FORBID only")
        fact_constraint = FactConstraint(
            name,
            tuple(_fact(s) for s in fields.multiple["REQUIRE"]),
            tuple(_fact(s) for s in fields.multiple["FORBID"]),
        )
        fields.finish()
        return fact_constraint
    if fields.multiple["REQUIRE"] or fields.multiple["FORBID"]:
        raise ParseError("REQUIRE and FORBID need KIND FACTS")
    if fields.multiple["ALLOW"] and kind != "TABLE":
        raise ParseError("ALLOW needs KIND TABLE")
    constraint: PersistentConstraint
    if kind == "ALL_DIFFERENT":
        constraint = AllDifferentConstraint(name, _sequence(fields.take("SCOPE")))
    elif kind == "SUM":
        constraint = SumConstraint(
            name, _sequence(fields.take("SCOPE")), int(fields.take("TARGET"))
        )
    elif kind == "LINEAR_SUM":
        constraint = LinearSumConstraint(
            name,
            _terms(fields.take("TERMS")),
            ConstraintOperator(fields.take("OPERATOR")),
            int(fields.take("TARGET")),
        )
    elif kind == "COMPARE":
        constraint = BinaryComparisonConstraint(
            name,
            _atom(fields.take("LEFT")),
            _atom(fields.take("RIGHT")),
            BinaryComparisonOperator(fields.take("OPERATOR")),
        )
    elif kind == "ELEMENT":
        constraint = ElementConstraint(
            name,
            _atom(fields.take("INDEX")),
            _sequence(fields.take("ARRAY")),
            _atom(fields.take("VALUE")),
        )
    elif kind == "NVALUE":
        target = parse_term(fields.take("TARGET"))
        constraint = NValueConstraint(
            name,
            _sequence(fields.take("SCOPE")),
            integer(target) if isinstance(target, Number) else target,
            _sequence(fields.take("CONSTANTS", "SEQ[]")),
        )
    elif kind == "COUNT":
        constraint = CountConstraint(
            name,
            _sequence(fields.take("SCOPE")),
            parse_term(fields.take("VALUE")),
            ConstraintOperator(fields.take("OPERATOR")),
            int(fields.take("TARGET")),
        )
    elif kind == "GCC":
        scope = _sequence(fields.take("SCOPE"))
        bounds = []
        for row in _sequence(fields.take("BOUNDS")):
            if not isinstance(row, FiniteSequence) or len(row.elements) != 3:
                raise ParseError("BOUNDS requires SEQ[SEQ[value lower upper] ...]")
            value, lower, upper = row.elements
            bounds.append((value, integer(lower), integer(upper)))
        constraint = GlobalCardinalityConstraint(name, scope, tuple(bounds))
    elif kind == "TABLE":
        constraint = TableConstraint(
            name,
            _sequence(fields.take("SCOPE")),
            tuple(_sequence(row) for row in fields.multiple["ALLOW"]),
        )
    elif kind == "LEX_LESS_EQUAL":
        constraint = LexLessEqualConstraint(
            name, _sequence(fields.take("LEFT")), _sequence(fields.take("RIGHT"))
        )
    else:
        raise ParseError(f"unknown finite constraint kind {kind!r}")
    fields.finish()
    return (
        constraint
        if guard is None
        else GuardedConstraint(name, _fact(guard), constraint)
    )


def _table(
    name: str, lines: list[str], *, weight: bool = False
) -> TableFactor | WeightTable:
    fields = _Fields(lines, repeated=("ROW",))
    scope = _sequence(fields.take("SCOPE"))
    default = fields.take("DEFAULT", "0")
    rows: dict[tuple[Term, ...], str] = {}
    separator = " WEIGHT " if weight else " SCORE "
    for row in fields.multiple["ROW"]:
        values, found, score = row.rpartition(separator)
        if not found:
            raise ParseError(f"ROW needs{separator}a number")
        key = _sequence(values)
        if key in rows:
            raise ParseError("duplicate table row")
        rows[key] = score
    fields.finish()
    if weight:
        return WeightTable(
            name,
            scope,
            {key: Fraction(value) for key, value in rows.items()},
            Fraction(default),
        )
    return TableFactor(
        name, scope, {key: int(value) for key, value in rows.items()}, int(default)
    )


def _integer_factor(name: str, lines: list[str]) -> IntegerFactor:
    try:
        boundary = lines.index("WHEN")
    except ValueError as error:
        raise ParseError("INTEGER_FACTOR requires WHEN") from error
    fields = _Fields(lines[:boundary])
    scope = parse_term(fields.take("SCOPE"))
    weight = int(fields.take("WEIGHT"))
    fields.finish()
    premise_lines = (*lines[boundary + 1 :], "END_FACTOR")
    premises, position = _parse_premise_block(premise_lines, 0, "END_FACTOR", None)
    if position != len(premise_lines) - 1:
        raise ParseError("unexpected content after factor premises")
    return IntegerFactor(FactorDefinition(name, scope, tuple(premises)), weight)


def _objective(cursor: _Cursor, kind: str) -> LinearObjective | FactorObjective:
    if kind == "LINEAR":
        fields = _Fields(cursor.block("END_OBJECTIVE"))
        result = LinearObjective(
            _terms(fields.take("TERMS", "SEQ[]")), int(fields.take("OFFSET", "0"))
        )
        fields.finish()
        return result
    if kind != "FACTORS":
        raise ParseError("OBJECTIVE requires LINEAR or FACTORS")
    factors: list[IntegerFactor | TableFactor] = []
    offset = 0
    saw_offset = False
    while True:
        line = cursor.take()
        if line == "END_OBJECTIVE":
            return FactorObjective(tuple(factors), offset)
        kind, _, value = line.partition(" ")
        if kind == "OFFSET":
            if saw_offset:
                raise ParseError("duplicate OFFSET")
            offset, saw_offset = int(value), True
        elif kind == "INTEGER_FACTOR":
            factors.append(
                _integer_factor(_atom(value).name, cursor.block("END_FACTOR"))
            )
        elif kind == "TABLE_FACTOR":
            table = _table(_atom(value).name, cursor.block("END_TABLE_FACTOR"))
            assert isinstance(table, TableFactor)
            factors.append(table)
        else:
            raise ParseError(f"unknown objective declaration {line!r}")


def _measure(cursor: _Cursor, model_name: str) -> Measure:
    base: list[WeightTable] = []
    tables: list[TableFactor] = []
    groups: list[FactorGroup] = []
    while True:
        line = cursor.take()
        if line == "END_MEASURE":
            return Measure(
                tuple(base),
                tuple(tables),
                FactorModel(model_name, tuple(groups)) if groups else None,
            )
        kind, _, value = line.partition(" ")
        if kind == "BASE_TABLE":
            table = _table(
                _atom(value).name, cursor.block("END_BASE_TABLE"), weight=True
            )
            assert isinstance(table, WeightTable)
            base.append(table)
        elif kind == "LOG_TABLE":
            log_table = _table(_atom(value).name, cursor.block("END_LOG_TABLE"))
            assert isinstance(log_table, TableFactor)
            tables.append(log_table)
        elif kind == "FACTOR_GROUP":
            groups.extend(
                parse_factor_groups(
                    "\n".join(
                        (line, *cursor.block("END_FACTOR_GROUP"), "END_FACTOR_GROUP")
                    )
                )
            )
        else:
            raise ParseError(f"unknown measure declaration {line!r}")


def _query(header: str, lines: list[str]) -> QueryRequest:
    parts = header.split()
    if len(parts) != 3:
        raise ParseError("expected QUERY name kind")
    fields = _Fields(lines)
    kind = QueryKind(parts[2].lower())
    backend = fields.take("BACKEND", "native").lower()
    bounding = fields.take("BOUNDING", "auto").lower()
    value_policy = fields.take("VALUE_POLICY", "declared").lower()
    nodes = fields.single.pop("MAX_NODES", None)
    solutions = fields.single.pop("MAX_SOLUTIONS", None)
    seconds = fields.single.pop("TIME_LIMIT", None)
    query = Query(
        kind,
        None if nodes is None else int(nodes),
        None if solutions is None else int(solutions),
        None if seconds is None else float(seconds),
        int(fields.take("SAMPLE_COUNT", "1")),
        int(fields.take("SEED", "0")),
    )
    fields.finish()
    return QueryRequest(_atom(parts[1]).name, query, backend, bounding, value_policy)


def parse_model_document(text: str) -> ModelDocument:
    """Parse one MODEL and named queries, with source-line errors."""
    cursor = _Cursor(text)
    try:
        header = cursor.take()
        if not header.startswith("MODEL "):
            raise ParseError("expected MODEL name")
        name = _atom(header.removeprefix("MODEL ")).name
        variables: list[FiniteVariable] = []
        constraints: list[Constraint] = []
        facts: list[Fact] = []
        groups: list[RuleGroup] = []
        queries: list[QueryRequest] = []
        objective: LinearObjective | FactorObjective | None = None
        measure: Measure | None = None
        saw_measure = dyadic = False
        while True:
            line = cursor.take()
            if line == "END_MODEL":
                break
            kind, _, value = line.partition(" ")
            if kind == "VARIABLE":
                identifier, separator, domain = value.partition(" DOMAIN ")
                if not separator:
                    raise ParseError("VARIABLE requires name DOMAIN SEQ[...]")
                variables.append(FiniteVariable(_atom(identifier), _sequence(domain)))
            elif kind == "FACT":
                facts.append(_fact(value))
            elif kind == "GROUP":
                groups.extend(
                    parse_rule_groups(
                        "\n".join((line, *cursor.block("END_GROUP"), "END_GROUP"))
                    )
                )
            elif kind == "CONSTRAINT":
                constraints.append(
                    _constraint(_atom(value), cursor.block("END_CONSTRAINT"))
                )
            elif kind == "OBJECTIVE":
                if objective is not None:
                    raise ParseError("duplicate OBJECTIVE")
                objective = _objective(cursor, value)
            elif kind == "MEASURE":
                if saw_measure:
                    raise ParseError("duplicate MEASURE")
                saw_measure = True
                if value == "NEGATIVE_LOG2_OBJECTIVE":
                    dyadic = True
                elif not value:
                    measure = _measure(cursor, name)
                else:
                    raise ParseError("unknown MEASURE declaration")
            elif kind == "QUERY":
                queries.append(_query(line, cursor.block("END_QUERY")))
            else:
                raise ParseError(f"unknown model declaration {line!r}")
        if not cursor.done:
            raise ParseError("unexpected content after END_MODEL")
        if dyadic:
            if not isinstance(objective, FactorObjective):
                raise ParseError(
                    "NEGATIVE_LOG2_OBJECTIVE requires a table-factor objective"
                )
            measure = negative_log2_measure(objective)
        model = FiniteModel(
            name,
            tuple(variables),
            tuple(constraints),
            tuple(facts),
            tuple(groups),
            objective,
            measure,
        )
        return ModelDocument(model, tuple(queries))
    except (ValueError, TypeError, ZeroDivisionError) as error:
        raise ParseError(f"line {cursor.line_number}: {error}") from error
