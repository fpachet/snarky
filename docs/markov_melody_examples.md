# Variable-order melody examples from Pachet and Roy (2011)

The melody experiment, forbidden longer patterns, contour control, and chunk
continuation now run on Snarky. These complement the completed first-order
[Boulez Blues result](performance_boulez_2026-09-16.md). Bach remains outside this
project slice.

The [versioned numeric corpus](../benchmarks/data/di_meola_v1/README.md) contains
all 105 training notes from Figure 1 and the paper's printed solutions. A separate
[reference scorer and raw-window DP](../benchmarks/melody_reference.py) imports no
Snarky code. Small brute-force tests and that reference independently check the
[production implementation](../src/snarky/finite/variable_markov.py).

## What is reproduced

- **Four modes:** fixed order 1, smoothing through order 4, highest supported
  order through 4, and the algebraic sum of supported orders squared. All four
  printed 17-note melodies are globally optimal under the explicit conventions
  below. The production DP chooses a different tied algebraic optimum.
- **Forbidden order 5:** no observed six-note word may occur, including across
  chunk boundaries. Figures 2–3 demonstrate the intended difference: Figure 2
  is valid with copying allowed but rejected by the restriction; Figure 3 passes.
- **Contour control:** a new, explicitly chosen contour demonstrates the paper's
  likelihood/distance tradeoff. It is not a claimed recovery of an unpublished
  gesture trace.
- **Chunk continuation:** three six-note chunks use the previous notes as fixed
  context, with a different contour for each chunk. Each chunk is optimal given
  its prefix. Optimizing chunks separately does not optimize the whole stream.
  The demo records both scores and checks cross-boundary factors.

Fixed orders 2–4 have no feasible solution for the anchored 17-note request,
matching the paper's account. Both DP and native CSP establish infeasibility.

## Scoring contract

Training counts stay within each source sequence. A conditional probability's
denominator counts occurrences of the context **having a following symbol**.
The first note has unit weight for these anchored examples. `initial="marginal"`
explicitly includes its unigram probability instead. Existing Blues scoring is
unchanged.

At startup, only orders supported by the available history are eligible.
Every subsequent note requires an observed first-order transition:

| Mode | Local contribution |
|---|---|
| `fixed` | Conditional probability at the eligible requested order; missing support forbids the transition |
| `smoothing` | Arithmetic mean of probabilities at orders 1 through the eligible order, including missing orders as zero |
| `max_order` | Probability at the highest order supporting this continuation |
| `algebraic` | Square of the highest order supporting this continuation; contributions are added |

Probability contributions are multiplied as exact `Fraction` values. They are
objective weights; smoothing and max-order weights are not automatically
normalized next-note distributions. Search decisions never determine which
factors get counted. Prefix notes supply context but contribute no new score.
An order-k prohibition checks observed words of length k+1 ending in the new
segment; it does not retroactively reject words entirely inside the fixed prefix.

For rational `alpha = a/b`, the contour objective is explicitly
`alpha * log2(P) - (1-alpha) * D`, where D is summed squared integer pitch distance.
It is optimized by the equivalent **exact** product `P**a * 2**(-(b-a)*D)`.
Algebraic mode instead maximizes `a*S - (b-a)*D`. At alpha zero Markov support
remains a hard requirement; alpha one ignores distance. The chosen log base and
unscaled distance define the tradeoff; this is not an assertion that the paper's
interactive demonstration used the same numerical scaling.

## Published scores versus recomputed scores

Columns are the paper's fixed, smoothing, max-order and algebraic solutions.
Probability scores here are natural logarithms for comparison with Table 6;
optimization itself never uses floating-point logs.

| Scoring mode | Recomputed scores | Table 6 |
|---|---|---|
| Fixed order 1 | −13.9151, −18.4433, −24.6590, −21.9622 | −13.9, −18.4, −24.7, −22 |
| Smoothing through 4 | −28.3125, −15.5702, −15.5946, −17.9173 | −12.3, −11.3, −11.8, −12.7 |
| Max-order through 4 | −11.1425, −8.3178, −3.4657, −7.9655 | −11.1, −6.9, −3.5, −8 |
| Algebraic through 4 | 38, 132, 120, 133 | 38, 90, 120, 133 |

All four fixed-order entries match the published rounding. All printed solutions
are feasible under the no-six-note-copy restriction and achieve their respective
optimum. The remaining discrepancies are preserved rather than “corrected” by
fitting an undocumented smoothing or transcription convention. Table 6 is not
claimed to have been reproduced in full.

## API and execution

```python
from fractions import Fraction
from snarky import Atom, Number
from snarky.finite import MarkovGeneration, NGramModel, Query, QueryKind, solve
from snarky.finite.constraints import AllDifferentConstraint

# A small synthetic corpus; the research runner loads the 105-note fixture.
source = NGramModel.train([
    tuple(map(Number, [0, 1, 2, 3, 2, 1, 0])),
    tuple(map(Number, [0, 2, 1, 3, 0])),
], max_order=3)
request = MarkovGeneration(
    source, (source.alphabet,) * 4, mode="max_order", order=2,
    forbidden_order=3, prefix=(Number(0),),
    contour=(1, 2, 3, 2), alpha=Fraction(9, 10),
)
graph = request.graph()
optimum = graph.optimum()  # Exact for this request's regular controls.

# Arbitrary constraints and rules use the ordinary CSP engine.
model = graph.compile(constraints=(AllDifferentConstraint(
    Atom("distinct"), tuple(Atom(f"x{i}") for i in range(4)),
),))
result = solve(model, Query(QueryKind.MAXIMIZE), value_policy="objective")
```

`compile()` exposes note variables `x0...` and deterministic auxiliary variables
`state0...`. Attach rules/context using `dataclasses.replace` on the resulting
`FiniteModel`. `graph.assignment(sequence)` provides a complete assignment for
validated warm starts. A DP witness is only a valid warm start for a constrained
model if it satisfies the added constraints too; the solver checks this.

The DP API accepts only the controls represented by its graph. It does not
silently solve or relax an additional all-different, GCC or rule requirement.
Use native `solve()` for those models. The ordinary sparse chain bounds remain
admissible relaxations when nonlocal constraints are present.

Reproduce every example, independent oracle comparison and repeat timing:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.melody_examples \
  --output /tmp/melody-run.json --repeats 3
```

The output path must be new. The runner saves exact rational scores, numeric
melodies, printed/recomputed matrices, per-stage timing samples, native search
statistics, separate Python-allocation probes, and a source archive. Full results
and timings are in the [performance record](performance_melody_2026-09-16.md).

The new API is Python-only. Parsed variable-order syntax, sampling under these
weights, general reification, top-k diversity and a live graphical controller are
not part of this slice. This is an exact optimization implementation with an
executable contour/continuation demonstration.
