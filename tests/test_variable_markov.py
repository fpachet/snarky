"""Variable-order modes against raw-window DP, brute force, and the 2011 figures."""

import json
from dataclasses import replace
from fractions import Fraction
from itertools import product
from math import log
from random import Random

import pytest

from benchmarks import melody_reference as oracle
from snarky import Atom, Fact, Number, Triple, parse_rule_groups
from snarky.finite import (
    FactConstraint,
    MarkovGeneration,
    NGramModel,
    Query,
    QueryKind,
    ResultStatus,
    solve,
)
from snarky.finite.constraints import AllDifferentConstraint


def model(sequences, order=3):
    return NGramModel.train([tuple(map(Number, s)) for s in sequences], order)


def notes(sequence):
    return tuple(v.value for v in sequence)


@pytest.mark.parametrize("mode", oracle.MODES)
@pytest.mark.parametrize("seed", range(5))
def test_suffix_dp_and_compiled_csp_match_exhaustive_paths(mode, seed):
    rng = Random(seed)
    corpus = [tuple(rng.randrange(3) for _ in range(12)) for _ in range(2)]
    source = model(corpus)
    domains = ((0,), (0, 1, 2), (1, 2), (0, 1, 2))
    prefix = (2, 0) if seed % 2 else ()
    contour = (0, 1, 2, 1) if seed % 3 else None
    alpha = Fraction(seed, 5) if contour else Fraction(1)
    request = MarkovGeneration(
        source,
        tuple(tuple(map(Number, d)) for d in domains),
        mode,
        2,
        3,
        tuple(map(Number, prefix)),
        "marginal",
        contour,
        alpha,
    )
    expected = {}
    for seq in product(*domains):
        result = oracle.optimum(
            corpus,
            [(n,) for n in seq],
            mode,
            2,
            forbidden=3,
            prefix=prefix,
            initial="marginal",
            contour=contour,
            alpha=alpha,
        )
        if result is not None:
            expected[seq] = result[0]
        assert request.score(tuple(map(Number, seq))) == (
            None if result is None else result[0]
        )
    graph = request.graph()
    optimum = graph.optimum()
    if expected:
        assert optimum.score == max(expected.values())
    else:
        assert optimum is None
    compiled = graph.compile()
    solutions = solve(compiled, Query(QueryKind.ENUMERATE))
    actual = {
        tuple(s.assignment[Atom(f"x{i}")].value for i in range(4)): s.objective_value
        for s in solutions.solutions
    }
    assert solutions.complete and actual == expected
    for reverse in (False, True):
        result = solve(compiled, Query(QueryKind.MAXIMIZE), reverse_values=reverse)
        assert result.complete
        assert (result.incumbent.objective_value if result.incumbent else None) == max(
            expected.values(), default=None
        )
    for sequence, score in expected.items():
        assert (
            compiled.objective.evaluate(graph.assignment(tuple(map(Number, sequence))))
            == score
        )


def test_boundaries_startup_and_prefix_are_explicit():
    source = model([(0, 1, 2), (2, 0)])
    assert (Number(2), Number(2)) not in source.probabilities[1]
    request = MarkovGeneration(source, ((Number(0),), (Number(1),)), "fixed", 2)
    assert request.score((Number(0), Number(1))) == 1
    assert replace(request, initial="marginal").score(
        (Number(0), Number(1))
    ) == Fraction(2, 5)
    # Prefix contributes context but never its own likelihood.
    tail = replace(request, domains=((Number(2),),), prefix=(Number(0), Number(1)))
    assert tail.score((Number(2),)) == 1
    assert replace(tail, forbidden_order=2).graph().optimum() is None
    # The forbidden word entirely before this chunk does not reject the chunk.
    tail = replace(
        request,
        order=1,
        forbidden_order=2,
        domains=((Number(0),),),
        prefix=(Number(0), Number(1), Number(2)),
    )
    assert tail.graph().optimum().score == 1


def test_extra_global_constraint_and_rule_closure_change_optimum():
    source = model([(0, 0, 0, 1, 2, 0, 2, 1, 0)], 2)
    request = MarkovGeneration(source, (source.alphabet,) * 3, "max_order", 2)
    graph = request.graph()
    distinct = AllDifferentConstraint(
        Atom("distinct"), tuple(Atom(f"x{i}") for i in range(3))
    )
    bad = Fact(Triple(Atom("melody"), Atom("is"), Atom("bad")))
    rules = parse_rule_groups("""GROUP classify
      RULE reject_zero
      WHEN
        (x0 value 0)
      THEN
        ADD (melody is bad)
      END
      END_GROUP""")
    compiled = graph.compile(
        constraints=(distinct, FactConstraint(Atom("acceptable"), forbidden=(bad,)))
    )
    compiled = replace(compiled, rules=rules)
    expected = {
        seq: request.score(tuple(map(Number, seq)))
        for seq in product(range(3), repeat=3)
        if len(set(seq)) == 3 and seq[0] != 0
    }
    expected = {seq: score for seq, score in expected.items() if score is not None}
    result = solve(compiled, Query(QueryKind.ENUMERATE))
    assert result.complete
    assert {
        tuple(s.assignment[Atom(f"x{i}")].value for i in range(3)): s.objective_value
        for s in result.solutions
    } == expected
    optimum = solve(compiled, Query(QueryKind.MAXIMIZE))
    assert optimum.status is ResultStatus.OPTIMAL
    assert optimum.incumbent.objective_value == max(expected.values())


@pytest.fixture(scope="module")
def paper():
    fixture = json.loads(oracle.CORPUS.read_text())
    corpus = [r["pitches"] for r in fixture["training"]]
    return fixture, corpus, model(corpus, 5)


@pytest.mark.parametrize("mode", oracle.MODES)
def test_published_melodies_are_optimal_under_explicit_formulas(paper, mode):
    fixture, corpus, source = paper
    domains = ((4,),) + (tuple(v.value for v in source.alphabet),) * 15 + ((4,),)
    order, forbidden = (1, None) if mode == "fixed" else (4, 5)
    request = MarkovGeneration(
        source, tuple(tuple(map(Number, d)) for d in domains), mode, order, forbidden
    )
    graph = request.graph()
    result = graph.optimum()
    reference = oracle.optimum(corpus, domains, mode, order, forbidden=forbidden)
    assert result.score == reference[0]
    assert result.score == request.score(
        tuple(map(Number, fixture["published_solutions"][mode]))
    )
    assert (
        oracle.score(corpus, notes(result.sequence), mode, order, forbidden=forbidden)
        == result.score
    )
    csp = solve(
        graph.compile(),
        Query(QueryKind.MAXIMIZE),
        initial_assignment=graph.assignment(result.sequence),
    )
    assert csp.status is ResultStatus.OPTIMAL
    assert csp.objective_bound == csp.incumbent.objective_value == result.score
    assert csp.explored_nodes == 1


def test_paper_transcription_cross_scores_and_anticopy(paper):
    fixture, corpus, source = paper
    assert list(map(len, corpus)) == [48, 48, 9]
    assert len(source.alphabet) == 15
    domains = ((Number(4),),) + (source.alphabet,) * 15 + ((Number(4),),)
    fixed = MarkovGeneration(source, domains, "fixed", 1)
    assert [
        round(
            log(fixed.score(tuple(map(Number, fixture["published_solutions"][mode])))),
            1,
        )
        for mode in oracle.MODES
    ] == fixture["published_cross_scores"]["fixed"]
    # Preserve a documented discrepancy, not an invented matching convention.
    smooth = tuple(map(Number, fixture["published_solutions"]["smoothing"]))
    assert replace(fixed, mode="algebraic", order=4).score(smooth) == 132
    assert fixture["published_cross_scores"]["algebraic"][1] == 90
    variable = replace(fixed, mode="max_order", order=4)
    fig2, fig3 = (tuple(map(Number, fixture[f"figure{i}"])) for i in (2, 3))
    assert variable.score(fig2) is not None
    assert replace(variable, forbidden_order=5).score(fig2) is None
    assert replace(variable, forbidden_order=5).score(fig3) is not None
    for order in (2, 3, 4):
        request = replace(fixed, order=order)
        assert request.graph().optimum() is None
        assert (
            solve(request.graph().compile(), Query()).status is ResultStatus.INFEASIBLE
        )


def test_validation_and_training_immutability():
    source = model([(0, 1, 0)])
    request = MarkovGeneration(source, (source.alphabet,), order=1)
    with pytest.raises(TypeError):
        source.probabilities[0][(Number(0),)] = Fraction(1)
    for changes in (
        {"order": 0},
        {"forbidden_order": 0},
        {"order": 4},
        {"mode": "unknown"},
        {"alpha": 0.5},
        {"initial": "implicit"},
        {"contour": (1, 2)},
        {"domains": ()},
        {"prefix": (Number(7),)},
        {"alpha": Fraction(1, 2)},
    ):
        with pytest.raises(ValueError):
            replace(request, **changes)
    with pytest.raises(ValueError):
        request.graph().assignment((Number(8),))
    with pytest.raises(ValueError):
        request.score(())
    with pytest.raises(ValueError):
        NGramModel.train([], 2)


def test_constructed_ngram_models_require_normalization_and_subword_support():
    a, b = Number(0), Number(1)
    with pytest.raises(ValueError, match="sum to one"):
        NGramModel(({(a,): Fraction(1, 3)},))
    with pytest.raises(ValueError, match="subword"):
        NGramModel(
            (
                {(a,): Fraction(1, 2), (b,): Fraction(1, 2)},
                {(a, b): Fraction(1), (b, a): Fraction(1)},
                {(a, a, b): Fraction(1)},
            )
        )
