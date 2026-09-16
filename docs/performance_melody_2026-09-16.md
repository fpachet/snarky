# Melody reproduction and performance, 16 September 2026

All four 17-note melodies printed in Pachet and Roy (2011) are optimal under the
[explicit scoring conventions](markov_melody_examples.md). Both the independent
raw-window reference and Snarky's suffix-state DP establish this; unseeded native
CSP also proves every optimum. Several Table 6 numbers differ, as documented in
the guide. This is a reproduction of the models and melodies, not an assertion
that all original implementation details or scores have been recovered.

## Preserved measurements

- [Raw samples and exact scores](../benchmarks/results/melody_examples_2026-09-16.json)
- [Source archive](../benchmarks/results/melody_examples_2026-09-16.sources.tar.gz)
- [Collector](../benchmarks/melody_examples.py) and [independent oracle](../benchmarks/melody_reference.py)
- [Versioned corpus and attribution](../benchmarks/data/di_meola_v1/README.md)
- [Boulez regression control](../benchmarks/results/melody_boulez_control_2026-09-16.json)

Measurements use Python 3.13.11 on the same Apple Silicon host as the previous
Boulez report, `PYTHONHASHSEED=0`, three sequential repetitions, without concurrent
heavy tests. They are development measurements; thermal/background activity is
not controlled, and there is no discarded warmup. Raw records include environment,
source hashes, training/graph/model-construction samples, work counters, exact
objectives, incumbent history for the final repetition, and separate Python
allocation probes. Allocation peaks are not process RSS. Timeouts, if any, retain
their actual status; these four unseeded cases all finish within the five-second cap.

## Four-mode timings

Medians of three repetitions, generated from the preserved raw record:

| Mode | Reference DP | Suffix DP | Native CSP, unseeded | Native CSP, seeded | DP Python peak |
|---|---:|---:|---:|---:|---:|
| fixed | 3.9 ms | 1.9 ms | 73.7 ms | 10.1 ms | 66 KiB |
| smoothing | 2158.9 ms | 62.3 ms | 403.5 ms | 85.5 ms | 1415 KiB |
| max_order | 1780.6 ms | 57.2 ms | 390.6 ms | 84.3 ms | 1352 KiB |
| algebraic | 1721.5 ms | 53.3 ms | 180.6 ms | 73.1 ms | 1352 KiB |

DP time includes graph construction and optimization, excluding training. Native
CSP time includes finite-model construction, propagation/bound preparation and
search, excluding the already constructed graph. Seeded CSP additionally assumes
a DP witness is available; its column is not an end-to-end witness-discovery time.
The raw record separates construction timings for future comparisons. The
independent reference includes counting and raw-window DP.

The first-order graph has 15 distinct states and 621 layered edges. The three
variable-order graphs each have 325 states and 10,281 edges. Their suffix-state
DP is roughly 30–35 times faster than the simple reference. This compares two
algorithms on identical requests, not two versions of the same search loop.
The reference prioritizes independence and clarity, not competitive performance.

## What changed in the engine

1. Retain only the longest suffix that can participate in an observed context.
   The support tables contain every subword, so shorter relevant suffixes remain
   recoverable. Startup eligibility uses actual history length, not compressed
   state length. Reachability and backward pruning remove dead ends.
2. Score every edge exactly with rationals or integers. The DP maximizes a product
   or sum. Hard copy prevention is checked during transition construction.
3. Compile the same graph into native tables, deterministic note projections and
   ordinary objective factors. Additional rules/global constraints remain under
   reversible CSP search; the direct DP API cannot accept them.
4. Use a zero-default pair factor's sparse support to prepare product-chain bounds.
   For integer pair-factor models too large for the dense bound budget, use local
   hard-table support to prepare a sparse sum-chain relaxation. Missing/default
   objective rows retain their declared semantics; nonlocal constraints are
   relaxed by the bound, still enforced by the solver.

The ordinary CSP proofs take 16, 15, 12 and 16 nodes respectively. With validated
DP witnesses, all four root bounds equal the incumbent and prove optimality in
one node. This validates useful bound integration; it is not a claim that arbitrary
nonregular constraints have become polynomial-time solvable.

The sparse integer fallback ignores local non-table constraints as well as
nonlocal constraints. That can weaken its bound, but cannot invalidate it. The
existing dense path remains preferred when it fits the preparation budget.

## Copy prevention, contour and continuation

Allowing observed six-note words raises the algebraic optimum from **133 to 192**.
The selected unrestricted optimum contains ten copied six-note windows. Forbidding
order 5 eliminates all such windows; overlapping windows are counted separately.

The contour demonstration's minimum squared distance is **33** at alpha 0.
At alpha 1/2 it is **34**; at 9/10, **81**; at alpha 1, **1257** with the best
Markov score. These are exact optima for the explicitly chosen base-2 tradeoff,
checked against the independent raw-window DP. The source/target arrays and
likelihoods are preserved in the raw record.

Three six-note continuations, with changing contours, take about **9–18 ms** per
chunk in the initial measurements. Prefix context crosses each boundary, and an
independent score of the concatenation equals the product of the chunk scores.
Each chunk's optimum is independently verified. The collector also records the
whole-stream optimum, making clear that sequential chunk optima need not achieve
it. This measures a programmatic demonstration, not audio, MIDI or GUI latency.

A separate unseeded Boulez control still proves the published sequence in
**209 nodes, 1.714 seconds**, log probability **−46.921591738232166**. That is
consistent with the prior 1.73-second median. It is a single correctness/work-count
control, not a statistically significant speed comparison.

## Validation

[Recorded validation](../tests/fixtures/melody_validation_2026-09-16.json):
**920 passed, 3 skipped** in the broad non-Bach gate (217.29 seconds), plus the
subsequently added input-validation test passing separately. The focused
Python 3.12 run passed **95 tests**. Strict mypy passed all **93 modules**;
Ruff, Markdown links, source/wheel distribution checks and isolated installations
on Python 3.12/3.13 passed. The installed-wheel smoke checks execute all four
variable-order modes with contour and fixed-prefix controls.
Tests cover all four modes against exhaustive short sequences, prefix/startup
semantics, contour endpoints, impossible requests, immutable training tables,
normalization/subword-support validation, forbidden cross-boundary words, all four
paper optima, and mixed rules plus all-different. Sparse-bound tests cover reversed
scopes, changing domains, negative integer scores, constants, zero product weights,
nonzero defaults, preparation budgets and deadlines.

The existing non-Bach suite is run as the broad regression gate. Python 3.12
checks exercise the changed runtime and bound tests too. Performance and test
runs are kept separate. The corpus and research artifacts remain excluded from
built source/wheel distributions.
