# Snarky benchmarks

Benchmarks are reproducible programs kept separate from correctness tests.
They compare implementations only after verifying equivalent logical outputs
and write machine-readable JSON or CSV under [`results/`](results/).

They are not universal performance claims. Wall-clock values depend on Python,
hardware, operating system, background load, and benchmark parameters.
Algorithmic counters and output equivalence are usually more portable.

For the upcoming redesign, use the [performance baseline and comparison
ledger](../docs/performance_baseline.md). It defines a fixed non-Bach portfolio
collected by `python -m benchmarks.redesign_baseline`, with raw samples and
explicit timing boundaries.

## Reproduction protocol

Run benchmarks from the repository root in a clean environment:

```sh
uv sync --extra dev
uv run pytest
uv run python -m benchmarks.rulebase_suite --repeat 7
```

For an optimization comparison:

1. record the exact commit, Python version, platform, and command;
2. warm up both implementations;
3. alternate baseline and candidate measurements when the script supports it;
4. report the median and retain individual samples;
5. verify facts, solutions, ordering, events, and relevant search counters;
6. store the raw result file rather than copying only a headline number.

Machine-readable results must also record whether each measured Git checkout
was dirty. A commit hash alone is not sufficient provenance when uncommitted
engine changes may affect the timing.

Do not combine results produced for different problem definitions. For
example, a two-position fixed-chord harmonizer and a four-position
chord-generating harmonizer measure different workloads.

## Benchmark catalogue

The factor-support microbenchmark compares one committed evaluator with the
working tree using the same current matcher, alternating measurement order
and checking every score, witness count, and ordered support list:

```sh
python -m benchmarks.factor_supports --baseline-ref 1a453ad \
  --output benchmarks/results/factor_supports_review_2026-09-08.json
```

The [recorded review comparison](results/factor_supports_review_2026-09-08.json)
reduces the 4,000-witness median from 1.467 s to 0.00937 s for this synthetic
shared-scope case. This is an evaluator microbenchmark, not an end-to-end
harmonization speedup. The record includes raw samples, source hash, commit,
environment, and dirty-checkout status.

### Applications and search

| Module | Comparison |
|---|---|
| `claire_n_queens` | normalized N-Queens comparison with CLAIRE4 |
| `claire_talarian_filter` | normalized Talarian rule-filter comparison with CLAIRE4 |
| `claire_triangle_closure` | streamed multi-premise triangle closure with CLAIRE4 |
| `incremental_conjunctions` | cold and streamed three-premise joins |
| `choice_search` | CSP and harmonizer integration across search traversals |
| `choice_trail` | lazy forked DFS versus reversible-trail DFS on N-queens |
| `choice_formulations` | extensional versus intensional N-queens and harmony transitions |
| `finite_markov` | native fixed-order Markov optimization scaling, limits, separate preparation/search and allocation tracing |
| `classical_csp` | magic squares, Latin squares, and constraints-only versus hybrid Sudoku |
| `csp_harmonizer_next` | generic Sudoku search and note-variable harmonizer |
| `muses_harmonizer` | symbolic harmony core versus complete MuSES object bridge |
| `sudoku_rules` | p1, p6, and p7 human-technique workloads |
| `fibonacci_explicit` | explicit recursive Fibonacci rulebase |
| `rulebase_suite` | documented rulebases across instantiation strategies |

Representative commands:

```sh
uv run python -m benchmarks.claire_n_queens \
  --sizes 8 10 12 14 --repeat 3
uv run python -m benchmarks.claire_talarian_filter \
  --sizes 100 1000 5000 --repeat 3
uv run python -m benchmarks.claire_talarian_filter \
  --engine snarky --sizes 100 1000 5000 --repeat 5 \
  --disable-event-rules
uv run python -m benchmarks.claire_triangle_closure \
  --groups 2 5 10 25 33 50 100 --repeat 5
uv run python -m benchmarks.claire_triangle_closure \
  --engine snarky --groups 2 5 10 25 --repeat 3 \
  --disable-factorized-event-rules
uv run python -m benchmarks.claire_triangle_closure \
  --engine snarky --groups 2 5 10 25 --repeat 3 \
  --disable-factorized-event-rules \
  --disable-partial-join-memory
uv run python -m benchmarks.incremental_conjunctions \
  --groups 25 100 250 --width 8 --repeat 5
uv run python -m benchmarks.incremental_conjunctions \
  --groups 25 100 250 --barrier-groups 2 5 10 25 \
  --width 8 --repeat 3
uv run python -m benchmarks.choice_search --repeat 5
uv run python -m benchmarks.choice_trail --repeat 3
uv run python -m benchmarks.choice_formulations --repeat 3
uv run python -m benchmarks.classical_csp --repeat 3
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 --only-magic --repeat 3
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 --only-magic --repeat 3 \
  --magic-symmetry-breaking
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 7 --only-magic --repeat 3 \
  --magic-propagation-guided
uv run python -m benchmarks.classical_csp \
  --magic-sizes 6 7 --only-magic --repeat 3 \
  --magic-dom-wdeg-only
uv run python -m benchmarks.csp_harmonizer_next --repeat 5
uv run python -m benchmarks.sudoku_rules \
  --levels 1 2 3 4 5 6 7 --repeat 5
uv run python -m benchmarks.fibonacci_explicit --repeat 7
```

`claire_n_queens` expects a CLAIRE4 checkout in the sibling directory
`../CLAIRE4`, or at the path named by `CLAIRE4_ROOT`. It uses CLAIRE's bundled
platform interpreter and does not include process startup or model
construction in CLAIRE's measured search time. Snarky prepares its inference
session separately, reports that preparation time, and uses only
`SessionChoiceSearch.solve()` as its primary search timing. The JSON records
these timing scopes explicitly and deliberately publishes no automatic speedup
ratio. The shared protocol finds the first solution with
minimum-remaining-values selection, numeric column and row tie-breaking,
singleton propagation, and no symmetry breaking. The runner specializes
CLAIRE's reversible tables to each requested board size before loading the
source. It requires both engines to select the same first solution.
Engine-specific search and propagation counters are retained because their
definitions are not interchangeable.

`claire_talarian_filter` adapts CLAIRE4's historical Talarian filter test to
a common ten-rule workload. Each of `N` prepared frames receives ten positive
inputs, causing exactly `10N` independent rule firings and `10N` observable
outputs; both runners validate those counts and a `40N` checksum. Primary
timings exclude source/rule parsing and process startup. For each input,
Snarky times `InferenceSession.assume()` followed by `run_group()` to a fixed
point with `materialize_result=False`, matching CLAIRE's immediately
rule-triggering slot update without copying the complete fact memory after
each input. Per-update outputs are read from the event journal. Preparation is
reported separately (input-fact construction plus an empty session for
Snarky, object construction for CLAIRE). The semantic workload and incremental
scheduling are normalized, but the engines' storage models differ, so the
runner reports inference throughput without calculating a cross-engine
speedup ratio. In particular, CLAIRE compiles these rules as event demons:
the slot update binds the object and value, then the remaining comparison is a
direct Boolean test. This benchmark therefore does not measure a general
multi-relation join or a RETE-style partial-match network.
Snarky's event-rule specialization is enabled by default;
`--disable-event-rules` runs the same workload through the generic
semi-naïve path for a direct A/B comparison.

`claire_triangle_closure` exercises a genuinely combinatorial rule. Each
group contains one hub, eight left nodes, and eight right nodes. Membership
relations are prepared first; the timed phase streams all 64 left-to-right
edges per group, with one saturation after every edge. A result exists only
when the hub-to-left, hub-to-right, and left-to-right premises agree. Both
implementations validate the exact firing count, output count, and checksum
of the owning hubs.

The natural CLAIRE formulation attaches a demon to additions in each left
node's `outgoing` set, then scans the instantiated hubs to test the other two
premises. Snarky keeps the rule declarative and compiles the arriving edge as
a factorized join anchor: fixed relation fields select the edge premise, then
two exact index lookups retrieve the hub memberships. It materializes no
left/right prefix product and is independent of `partial_join_limit`.

Consequently this comparison is useful precisely because the storage
strategies differ: CLAIRE has lower per-event overhead but scans all hubs,
while Snarky performs a constant number of indexed matches per edge. The
runner reports no automatic cross-engine speedup ratio.
`--disable-factorized-event-rules` restores the bounded partial-memory path;
adding `--disable-partial-join-memory` selects the generic semi-naïve witness.
Counters distinguish `factorized_event_evaluations`, added candidates, exact
lookups, partial-memory builds, and bypasses.

The archived common run extends to 100 groups. At 33 groups the old retained
prefix exceeds its default budget and falls back to the generic join, so a
separate one-run cliff record is retained rather than hiding that behavior in
an extrapolation.

`incremental_conjunctions --barrier-groups ...` reports all three Snarky
paths for the same comparison-barrier rule: `factorized`, `memory`, and
`generic`. Cold and ordinary streamed conjunctions remain guards for rule
shapes outside the new specialization.

### Constraint filtering and propagation

| Module | Comparison |
|---|---|
| `constraint_instantiation` | indexed joins versus safe domain filtering |
| `constraint_propagation` | strategies on the binary-constraint rulebase |
| `constraint_scaling` | declarative propagation as domains and chains grow |
| `constraint_support_churn` | residual existential witnesses during removal |
| `arithmetic_constraints` | specialized arithmetic filtering before joins |
| `global_constraints` | `NVALUE`, `ALL_DIFFERENT`, and persistent domains |
| `compact_tables` | scanned tables, bitset filters, and direct compact joins |
| `propagation_trail` | reversible trails versus full-state snapshots |
| `constraint_branching` | cloning a populated adaptive strategy |
| `domain_planning` | compilation of wide finite-domain plans |

Representative commands:

```sh
uv run python -m benchmarks.constraint_instantiation \
  --sizes 32 64 96 --repeat 7
uv run python -m benchmarks.constraint_propagation \
  --sizes 16 32 64 --repeat 7
uv run python -m benchmarks.global_constraints --size 200 --repeat 7
uv run python -m benchmarks.compact_tables \
  --levels 1 6 7 --repeat 7
uv run python -m benchmarks.propagation_trail \
  --variables 200 --branches 100 --repeat 7
```

Constraint benchmarks report metrics such as candidate facts, domain
reductions, propagator revisions, active table rows, exact matcher attempts,
and activations. A faster result is accepted only if these counters are
consistent with the intended algorithm and the final inference result is
unchanged.

### Engine and parser internals

| Module | Comparison |
|---|---|
| `agenda_incremental` | cold MEA agenda construction versus incremental update |
| `parser_lexing` | term and arithmetic tokenization |
| `parser_terms` | recursive parsing of representative term shapes |
| `parser_premises` | ordinary, aggregate, and nested premise blocks |
| `parser_actions` | ordinary and nested action blocks plus a real rulebase |

```sh
uv run python -m benchmarks.agenda_incremental --rules 200 --repeat 20
uv run python -m benchmarks.parser_lexing --repeat 11
uv run python -m benchmarks.parser_terms --repeat 11
uv run python -m benchmarks.parser_premises --repeat 11
uv run python -m benchmarks.parser_actions --repeat 11
```

Parser refactors compare both public parsing and the extracted internal
component. The real-rulebase case verifies group/rule counts so a speedup
cannot hide missing input.

## Result archive

The archive is chronological evidence, not a single current leaderboard.
File names include the feature and date:

```text
results/
├── classical_csp_2026-07-25.json
├── classical_csp_dom_wdeg_2026-07-25.json
├── classical_csp_learned_impact_2026-07-25.json
├── classical_csp_incremental_2026-07-25.json
├── classical_csp_optimized_2026-07-25.json
├── choice_search_2026-07-25.json
├── compact_tables_2026-07-24.csv
├── parser_actions_2026-07-25.json
├── rulebase_suite_2026-07-24.csv
└── ...
```

Important consolidation comparisons include:

- `fact_index_extraction_2026-07-25.json`;
- `query_memory_extraction_2026-07-25.json`;
- `semi_naive_compiled_delta_2026-07-25.json`;
- `domain_tables_extraction_2026-07-25.json`;
- `comparison_propagators_extraction_2026-07-25.json`;
- `domain_planning_2026-07-25.json`;
- `parser_lexer_2026-07-25.json`;
- `parser_terms_2026-07-25.json`;
- `parser_premises_2026-07-25.json`;
- `parser_actions_2026-07-25.json`.

These A/B runs were used as non-regression evidence while decomposing the
engine. The current implementation and environment may produce different
absolute timings.

## Interpretation

Snarky retains a naive deterministic strategy as an executable semantic
oracle. Indexed and semi-naive strategies remove repeated work. Constraint
strategies can additionally filter finite domains and compact premise tables
before exact matching. The adaptive strategy selects filtering only when its
estimated setup cost is likely to be amortized.

Consequently, no one strategy must win every microbenchmark:

- tiny rulebases can favor lower setup cost;
- append-only recursion favors semi-naive deltas;
- selective finite constraints can favor domain filtering;
- highly mutable workloads stress index and witness maintenance;
- application runs include orchestration and trace costs absent from isolated
  joins.

Optimization work should target a measured bottleneck, retain a differential
oracle, and avoid application-specific shortcuts in the generic engine. The
[finite-CSP solver optimization plan](../docs/solver_optimization_plan.md)
records the current profile, completed dependency scheduling and `SUM` bitset
work, and the acceptance boundary for future incremental state.

The [paired redesign collector](redesign_comparison.py) compares preserved
reference and candidate sources, matched-search CSPs, mixed overhead and bounded
Markov optimization. See the [comparison report](../docs/performance_comparison_2026-09-16.md)
for the measured decision, full timing scopes and memory tradeoff. Generate the
base tables for a new record with `python -m benchmarks.report_redesign RECORD.json
--output REPORT.md`, then append the correctness evidence and acceptance decision.

## LSDB Blues: exact first-order optimization

The [corpus audit](data/omnibook_blues_v2/README.md) describes the source-faithful
and proposed three-family/two-family variants and the exact training conventions. Run:

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.blues_markov \
  --repeat 3 --seconds 5 --output /tmp/blues_new_record.json
```

This compares native rational-product optimization to an independent DP for
ordinary and exactly-one-F-sharp-seventh Blues. For Boulez Blues the DP omits
all-different and is only an upper bound. Its training and generation both use the
24-symbol two-family corpus. See the
[initial performance report](../docs/performance_blues_2026-09-16.md) for results,
source snapshots and remaining work. The research corpus is not packaged with
Snarky; no LSDB installation is needed to run the committed compact fixture.

### Boulez assignment-bound comparison

The [paired collector](boulez_optimization.py) compares the frozen pre-optimization
source, the new controller with its chain bound, and automatic assignment bounds
with and without the published Table 5 warm start. It records independent sequence
validation, exact scores, first-solution/target/proof times, and separate traced
allocation runs. Existing rule/CSP/mixed control workloads are run on both sources.

```sh
mkdir -p /tmp/snarky-boulez-reference-e5e25cf
git archive e5e25cf src csp_solver sudoku rulebases benchmarks pyproject.toml \
  third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku/puzzles/grid3x3-p7.clp | \
  tar -x -C /tmp/snarky-boulez-reference-e5e25cf
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m benchmarks.boulez_optimization \
  --repeat 3 --seconds 5 --output /tmp/boulez_new_comparison.json
```

Use a fresh output path. The collector archives both source states, including dirty
candidate files, and checks their hashes remain unchanged. The output embeds the
published-witness record needed by the worker; when reproducing an archive alone,
restore it as `benchmarks/results/blues_published_witness_2026-09-16.json`.
Restore the embedded Sudoku input to its recorded path as well.
