"""Text/Python semantic parity, all constraint kinds, tooling and installed examples."""

import json
from fractions import Fraction

import pytest

from snarky import Atom, Number
from snarky.cli import main
from snarky.finite import (
    FiniteModel,
    FiniteVariable,
    Query,
    QueryKind,
    QueryRequest,
    parse_model_document,
    solve,
)
from snarky.finite.constraints import (
    AllDifferentConstraint,
    BinaryComparisonConstraint,
    BinaryComparisonOperator,
    ConstraintOperator,
    CountConstraint,
    ElementConstraint,
    GlobalCardinalityConstraint,
    LexLessEqualConstraint,
    LinearSumConstraint,
    SumConstraint,
    TableConstraint,
)
from snarky.finite.examples import model_source, scheduling_model
from snarky.formatting import format_source
from snarky.parser import ParseError
from snarky.tooling import validate_source


@pytest.mark.parametrize(
    "name,query,objective,count",
    [
        ("rules", "closure", None, 1),
        ("four_queens", "all", None, 2),
        ("linear", "optimum", -3, 1),
        ("scheduling", "optimum", 5, 1),
    ],
)
def test_packaged_model_examples_and_formatter(name, query, objective, count):
    source = model_source(name)
    document = parse_model_document(source)
    result = document.execute(query)
    assert len(result.solutions) == count
    assert result.incumbent.objective_value == objective
    assert format_source(source) == source
    assert not validate_source(source, path="example.model")
    assert parse_model_document(format_source(source)) == document


def test_mixed_text_has_identical_python_model_and_complete_results():
    parsed = parse_model_document(model_source("scheduling"))
    assert parsed.model == scheduling_model()
    expected = solve(scheduling_model(), Query(QueryKind.ENUMERATE))
    actual = parsed.execute("all")

    def observations(result):
        return {
            tuple(sorted(s.assignment.items(), key=repr)): (
                s.facts,
                s.objective_value,
                s.contributions,
            )
            for s in result.solutions
        }

    assert observations(actual) == observations(expected)
    with pytest.raises(ValueError, match="select"):
        parsed.execute()
    with pytest.raises(ValueError, match="unknown query"):
        parsed.execute("absent")


X, Y, Z, W = (Atom(v) for v in "xyzw")
C = Atom("c")


@pytest.mark.parametrize(
    "body,constraint",
    [
        ("KIND ALL_DIFFERENT\nSCOPE SEQ[x y]", AllDifferentConstraint(C, (X, Y))),
        ("KIND SUM\nSCOPE SEQ[x y]\nTARGET 3", SumConstraint(C, (X, Y), 3)),
        (
            "KIND LINEAR_SUM\nTERMS SEQ[SEQ[2 x] SEQ[-1 y]]\n"
            "OPERATOR LESS_EQUAL\nTARGET 0",
            LinearSumConstraint(C, ((2, X), (-1, Y)), ConstraintOperator.LESS_EQUAL, 0),
        ),
        (
            "KIND COMPARE\nLEFT x\nRIGHT y\nOPERATOR LESS_THAN",
            BinaryComparisonConstraint(C, X, Y, BinaryComparisonOperator.LESS_THAN),
        ),
        (
            "KIND ELEMENT\nINDEX x\nARRAY SEQ[y z]\nVALUE w",
            ElementConstraint(C, X, (Y, Z), W),
        ),
        (
            "KIND COUNT\nSCOPE SEQ[x y]\nVALUE 1\nOPERATOR EQUAL\nTARGET 1",
            CountConstraint(C, (X, Y), Number(1), ConstraintOperator.EQUAL, 1),
        ),
        (
            "KIND GCC\nSCOPE SEQ[x y]\nBOUNDS SEQ[SEQ[1 1 1] SEQ[2 1 1]]",
            GlobalCardinalityConstraint(
                C, (X, Y), ((Number(1), 1, 1), (Number(2), 1, 1))
            ),
        ),
        (
            "KIND TABLE\nSCOPE SEQ[x y]\nALLOW SEQ[1 2]\nALLOW SEQ[2 1]",
            TableConstraint(
                C, (X, Y), ((Number(1), Number(2)), (Number(2), Number(1)))
            ),
        ),
        (
            "KIND LEX_LESS_EQUAL\nLEFT SEQ[x y]\nRIGHT SEQ[z w]",
            LexLessEqualConstraint(C, (X, Y), (Z, W)),
        ),
    ],
)
def test_every_persistent_constraint_compiles_to_the_same_object(body, constraint):
    variables = tuple(FiniteVariable(v, (Number(1), Number(2))) for v in (X, Y, Z, W))
    source = "MODEL m\n" + "\n".join(
        f"VARIABLE {v.name.name} DOMAIN SEQ[1 2]" for v in variables
    )
    source += f"\nCONSTRAINT c\n{body}\nEND_CONSTRAINT\nEND_MODEL\n"
    actual = parse_model_document(source).model
    expected = FiniteModel("m", variables, (constraint,))
    assert actual == expected

    def assignments(model):
        return {
            tuple(s.assignment[v] for v in (X, Y, Z, W))
            for s in solve(model, Query(QueryKind.ENUMERATE)).solutions
        }

    assert assignments(actual) == assignments(expected)


def test_probability_measure_query_options_and_backend_projection():
    document = parse_model_document(model_source("probability"))
    result = document.execute("partition")
    assert result.inference.partition == Fraction(7, 12)
    assert len(document.execute("draw").solutions) == 5
    request = document.queries[-1]
    assert request.query.seed == 7 and request.query.kind is QueryKind.SAMPLE_EXACT
    limited = parse_model_document("""
        MODEL limit
        VARIABLE x DOMAIN SEQ[1 2]
        QUERY partial ENUMERATE
            MAX_NODES 2
            MAX_SOLUTIONS 1
            TIME_LIMIT 0.5
            BACKEND enumeration
        END_QUERY
        END_MODEL
    """)
    assert limited.queries[0] == QueryRequest(
        "partial", Query(QueryKind.ENUMERATE, 2, 1, 0.5), "enumeration"
    )


def test_integer_and_floating_factors_preserve_explicit_units_and_scope():
    source = """
        MODEL scores
        VARIABLE x DOMAIN SEQ[a b]
        OBJECTIVE FACTORS
            OFFSET -3
            TABLE_FACTOR score
                SCOPE SEQ[x]
                ROW SEQ[a] SCORE 2
                DEFAULT 1
            END_TABLE_FACTOR
        END_OBJECTIVE
        MEASURE NEGATIVE_LOG2_OBJECTIVE
        QUERY partition PARTITION
        END_QUERY
        END_MODEL
    """
    result = parse_model_document(source).execute()
    assert result.inference.partition == 6  # 2**(3-2) + 2**(3-1)
    assert (
        parse_model_document(format_source(source)).execute().inference.partition == 6
    )
    large = model_source("scheduling").replace("WEIGHT -8", f"WEIGHT {-(10**50)}")
    assert parse_model_document(large).model.objective.factors[1].weight == -(10**50)
    scores = """
        MODEL scores
        VARIABLE x DOMAIN SEQ[a b]
        MEASURE
            LOG_TABLE unit
                SCOPE SEQ[x]
                ROW SEQ[a] SCORE 2
            END_LOG_TABLE
            FACTOR_GROUP preferences
                FACTOR chosen
                SCOPE $symbol
                LOG_WEIGHT 0.5
                WHEN
                    (x value $symbol)
                END_FACTOR
            END_FACTOR_GROUP
        END_MEASURE
        QUERY partition PARTITION
        END_QUERY
        END_MODEL
    """
    result = parse_model_document(scores).execute()
    assert result.arithmetic == "float64_log"
    assert result.inference.factor_expectations["chosen"] == pytest.approx(1)
    formatted = format_source(scores)
    assert format_source(formatted) == formatted
    assert parse_model_document(formatted).model == parse_model_document(scores).model


@pytest.mark.parametrize(
    "source,match",
    [
        ("MODEL m\nBOGUS x\nEND_MODEL", "unknown model"),
        ("MODEL m\nVARIABLE x DOMAIN [1 2]\nEND_MODEL", "ordered SEQ"),
        ("MODEL m\nVARIABLE $x DOMAIN SEQ[1]\nEND_MODEL", "identifier"),
        ("MODEL m\nVARIABLE x DOMAIN SEQ[$unbound]\nEND_MODEL", "ground"),
        ("MODEL m\nOBJECTIVE LINEAR\nOFFEST 1\nEND_OBJECTIVE\nEND_MODEL", "unused"),
        (
            "MODEL m\nMEASURE\nBASE_TABLE b\nSCOPE SEQ[]\nROW SEQ[] WEIGHT 1/0\n"
            "END_BASE_TABLE\nEND_MEASURE\nEND_MODEL",
            "zero|Fraction",
        ),
        (
            "MODEL m\nCONSTRAINT c\nKIND ALL_DIFFERENT\nSCOPE SEQ[x]\n"
            "END_CONSTRAINT\nEND_MODEL",
            "undeclared",
        ),
        ("MODEL m\nQUERY q MINIMIZE\nEND_QUERY\nEND_MODEL", "explicit objective"),
        (
            "MODEL m\nQUERY q SOLVE\nBACKEND regular_bp\nEND_QUERY\nEND_MODEL",
            "probability",
        ),
        (
            "MODEL m\nQUERY q SOLVE\nBACKEND unknown\nEND_QUERY\nEND_MODEL",
            "unknown backend",
        ),
        ("MODEL m\nQUERY q SOLVE\nMAX_NODES 0\nEND_QUERY\nEND_MODEL", "positive"),
        (
            "MODEL m\nQUERY q SOLVE\nEND_QUERY\nQUERY q SOLVE\nEND_QUERY\nEND_MODEL",
            "duplicate",
        ),
        ("MODEL m\nEND_MODEL\nignored", "after END_MODEL"),
        (
            "MODEL m\nGROUP g\nRULE r\nWHEN\n(x p y)\nTHEN\nREMOVE (x p y)\n"
            "END\nEND_GROUP\nEND_MODEL",
            "ADD only",
        ),
    ],
)
def test_invalid_documents_fail_without_ignoring_fields(source, match):
    with pytest.raises(ParseError, match=match):
        parse_model_document(source)
    diagnostics = validate_source(source, path="bad.model")
    assert diagnostics and diagnostics[-1].line >= 1


def test_cli_runs_named_queries_and_reports_categories(tmp_path, capsys):
    path = tmp_path / "scheduling.model"
    path.write_text(model_source("scheduling"))
    assert main(["run", str(path), "--query", "optimum", "--explain"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "optimal" and result["objective_bound"] == 5
    assert set(result["solutions"][0]) >= {"derivations", "reductions", "contributions"}
    assert main(["run", str(path)]) == 1
    assert "select" in capsys.readouterr().err
    path.write_text(model_source("probability"))
    assert main(["run", str(path), "--query", "partition"]) == 0
    assert json.loads(capsys.readouterr().out)["inference"]["partition"] == "7/12"
    assert main(["check", "--syntax-only", "--format", str(path)]) == 0
    capsys.readouterr()
    path.write_text(
        "MODEL m\nVARIABLE x DOMAIN SEQ[1 2]\nQUERY q ENUMERATE\nMAX_NODES 1\n"
        "END_QUERY\nEND_MODEL"
    )
    assert main(["run", str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "unknown"
