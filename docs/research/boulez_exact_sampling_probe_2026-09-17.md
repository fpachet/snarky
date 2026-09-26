# Bounded Boulez Blues exact-sampling and compression probe

## Finding

Exact weighted sampling of the current 24-chord Boulez instance is practical
with an ordinary subset dynamic program and compiled integer arithmetic.
The experiment does **not** reveal a new tractable subclass or a large exact
MDD compression. It establishes a useful baseline that future proposals must beat.

On this machine, three fresh-process measurements give a median **0.629 s**
for preprocessing and 10,000 samples, with approximately **691 MiB** peak RSS.
Forward/backward feasibility and weighted completion preprocessing together take
about **0.497 s**; the 10,000 samples take **0.076 s** (about 7.6 microseconds each).
Including the separate MDD-size diagnostic raises the process median to 2.083 s.
Compilation, corpus loading/training, and Python result validation are excluded
from these worker process timings. Serialization of the sampled sequences is
included in process time, but excluded from the sampling phase timer.

This is a standalone research kernel, not a Snarky API or a general CSP solver.
It uses the original probabilities, including zero-probability transitions;
there is no transition threshold, smoothing, beam, or probability truncation.

## Exact problem and numerical results

The source is the tracked `omnibook_blues_v2` corpus, using
`boulez_two_family_proposed`, augmented through all 12 transpositions before
first-order training. The instance has 24 positions, 24 chord symbols, global
AllDifferent, and C7/F7/G7 fixed at positions 1/9/24. Every chord appears once.
It has 252 positive transitions between different symbols.

| Quantity | Exact result or measured value |
|---|---:|
| Valid complete sequences | **202,171,981,018** |
| Reachable subset/last-chord states, forward | 19,040,573 |
| States on some complete solution | 15,629,024 |
| Largest live layer | 3,486,402 |
| Edges on complete solutions | 61,410,846 |
| Reduced Boolean MDD nodes, forward | 14,299,241 |
| Reduced weighted MDD nodes, forward | 14,873,580 |
| Reduced Boolean MDD nodes, reversed | 13,708,111 |
| Reduced weighted MDD nodes, reversed | 14,214,036 |
| Probability of the event under the original Markov model | approximately 1.629784e-19 |
| Probability of AllDifferent given the three anchors | approximately 3.539670e-16 |
| Conditional probability of the published optimal sequence | approximately 2.570879% |

Node counts include the initial state and exclude the final accepting terminal.
The forward and reverse live-state and live-edge totals agree. Reachable states
include dead ends; the backward pass removes them. Weighted MDD equivalence allows
positive scalar normalization of residual weights, making it more permissive than
literal equality of weighted suffix functions.

The exact integer partition is:

```text
552020186075600183584406597891092649
```

Each dominant-seventh row can be written with denominator 388 and each minor row
with denominator 118. Since G7 is the fixed final chord, every valid path has the
same denominator `388**11 * 118**12`, multiplied by the fixed initial probability.
The exact event probability is therefore:

```text
225776256104920475086022298537456893441 /
1385314046453477204527133663696949965467317576457972088832
```

The worker computes checked 256-bit integer sums and products. A conservative
bound based on `21! * max_edge_weight**23` fits this representation; every addition
also checks overflow. The resulting partition occupies 119 bits, and the largest
stored suffix mass occupies 114 bits. Using 256-bit cells is deliberately
conservative and leaves scope for ordinary memory engineering.

## What the MDD experiment means

A state is a used-chord subset and its last chord. After accounting for the fixed
start, middle, and end chords, only 21 free membership bits are necessary. The
middle anchor is inserted after seven free chords. The dense completion table
contains `21 * 2**20` cells; the principal arrays occupy 688 MiB.

Two different used sets at the same layer cannot have the same nonempty suffix
language: a completing suffix must contain exactly the complementary symbols.
Thus, ordinary exact MDD reduction with fixed chord labels cannot merge such sets.
Within one used set, the suffix after choosing a particular next chord is
independent of the previous last chord. This permits exact classification by:

- the set of next chords having a positive completion, for Boolean equivalence;
- the vector of weights to those chords, normalized by its GCD, for weighted
  equivalence up to a positive scalar.

The diagnostic computes these exact reduced node counts without materializing
all 61 million arcs. Small exhaustive suffix-language oracles check the reduction.
It is a comparison of representations, **not a runtime comparison against an
external MDD implementation**, relaxed MDD search, or a solver using another
variable ordering or a different representation.

Forward weighted reduction saves **4.83%** of live nodes; reverse weighted
reduction saves **9.05%**. Boolean reduction saves **8.51%** forward and **12.29%**
backward. These are useful but modest reductions. In particular, this instance
does not display an unexpectedly tiny exact weighted decision diagram.

## Other proposed structural shortcuts

| Hypothesis | Check and result |
|---|---|
| Few interchangeable chord identities | No weighted twin pairs under the full transition relation |
| Small linear rank | Transition matrix rank 24, also rank 24 after deleting self-transitions; computed with rational elimination |
| Transposition quotient with the anchors retained | All 12 shifts preserve the transition model; only the identity preserves C7/F7/G7 |
| Small overlap between past and future domains | Maximum overlap 21 after singleton-anchor elimination and adjacent-table arc consistency |
| Small transition-graph treewidth | Underlying undirected support graph has degeneracy 14, hence treewidth at least 14 |

These checks reject these particular simple explanations. They do not rule out
every possible symmetry, decomposition, parameterization, or specialized algorithm.

The weighted distribution is concentrated despite its enormous support. With seed
1729, 10,000 samples contained 5,220 distinct sequences; the most frequent appeared
267 times. The published optimal sequence alone has exactly about 2.57% of the
conditional mass. This is an interesting distributional observation, not a proof
that low-probability paths may be discarded in an exact sampler.

Rejection from an anchor-conditioned Markov sampler would accept approximately
one candidate in **2.83e15**. The completion DP avoids this rejection problem.
This calculation concerns that specific proposal distribution, not every possible
rejection sampler or envelope construction.

## Bounded protocol and validation

- Apple clang 17, `-O3 -std=c++17`, macOS 15.7.7 ARM64. Platform, compiler,
  commit, dirty status, timestamp, and SHA-256 source/corpus hashes are in the record.
- Worker timeout: 90 seconds. Main-array allocation is checked against a 1 GiB
  budget; observed process peak RSS is also checked after each run. This is not
  an operating-system-enforced hard RSS limit. Every run completed below budget.
- Three fresh-process full weighted runs with the MDD diagnostic, then three
  without it. These are consecutive observations, not confidence intervals or a
  controlled paired comparison with a different solver. Background load and
  thermal state were not controlled. Prior exploratory runs warmed the machine.
- Every repeat uses seed 1729 and therefore the same sample stream. The repeats
  measure timing variability, not independent statistical sampling experiments.
- Full-size unweighted and reversed weighted/unweighted computations agree on
  the exact totals. Reversal transposes the edge weights, swaps the endpoints,
  and moves the middle anchor from position 9 to position 16.
- 34 small instances with 4–9 symbols, dense/sparse random weighted graphs, and
  early/interior/late anchors were checked against exhaustive permutations.
  Checks cover counts, masses, live layer widths, Boolean residual languages,
  proportional weighted residual languages, and sample validity.
- The same 34 cases passed an AddressSanitizer/UndefinedBehaviorSanitizer build.
- Independent Python recursion checks the restricted 8- and 12-symbol probes.
- Every generated sample is validated as a permutation with the correct anchors
  and positive transitions. Ten retained full-size sample scores also match the
  independent Python `Fraction` scorer and the common-denominator formula.
- First-step exact branch masses sum to the partition. The 10,000-draw empirical
  first-step distribution has total-variation distance 0.01166 from the exact
  distribution. This is a diagnostic; exactness follows from the completion
  recurrence and integer rejection draws, not from an empirical histogram.
- Existing `tests/test_blues_markov.py`: 7 passed. Ruff and Markdown link checks
  passed. No runtime or CI workflow changes are part of this experiment.

The smaller corpus-derived probes restrict the alphabet to an alphabetical subset
of free chords and retain the three anchors, placing the middle anchor after
`floor((n-3)/3)` free chords. They are correctness/size controls, not musically
equivalent versions of the full instance. The 8-symbol case is infeasible;
12/16/20-symbol cases have 44/11,422/595,128 live states. Their single timings
must not be interpreted as a controlled scaling law.

## Research assessment

The experiment changes the practical assessment: there is no need for a new
theorem to obtain fast exact weighted samples of the current Boulez instance.
The fixed-universe subset algorithm already works well in a compiled kernel.

It does not yet justify a novelty claim. There is no large residual-state
compression, no newly demonstrated tractable subclass, and no comparison showing
an advantage over a strong external exact MDD/counting implementation. Nor should
these C++ counting timings be compared as a speedup over the Python optimization
benchmark: both the implementation language and the computational task differ.

A useful next engineering step would expose exact continuation sampling through
a carefully bounded API. A research step would require a clear additional target:
larger alphabets, higher Markov order, changing constraints, or a genuinely smaller
representation, with matched baselines. Those extensions were not measured here.

## Reproduce

```sh
.venv/bin/python -m benchmarks.boulez_subset_probe --repeat 3 \
  --output /tmp/boulez_subset_probe.json
```

The runner requires clang++ with C++17 and the existing Python project environment.
It compiles a temporary executable, runs the exhaustive oracles, and records the
bounded probes. Samples use exact integer selection with a seeded pseudorandom
generator. The usual ideal-random-bit interpretation of exact sampling applies.

- [Python runner](../../benchmarks/boulez_subset_probe.py)
- [C++ kernel](../../benchmarks/boulez_subset_probe.cpp)
- [Raw measurements and exact results](../../benchmarks/results/boulez_subset_probe_2026-09-17.json)

The raw record is retained for scientific reproducibility; executable files remain
temporary and no generated music or new external corpus material is added.
