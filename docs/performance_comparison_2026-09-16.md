# Redesign performance comparison


The measured decision is to accept the additive native runtime for the declared
redesign scope, with the memory tradeoff below recorded explicitly. The legacy
operational and CSP paths remain available. This is a local performance assessment,
not a public release or a claim of uniformly faster arbitrary CSP optimization.

- Rule and incremental-join cases stay within the predeclared time review thresholds;
  their isolated allocation peaks are effectively unchanged.
- Native pure CSP is **2.01–3.08× faster** on the four matched-search cases, with
  identical assignments, nodes and failures, and lower traced allocation peaks.
- Adding the reporting rule to magic3 costs about **0.55 ms** in the pooled medians.
  This measures one small bridge workload, not all possible mixed rule bases.
- Both methods prove the 25/4 Markov optimum; native total proof time improves
  **96.98×**. Native proves the 33/8 and 129/8 optima in all 21 samples, while
  repeated feasibility stops at the deadline. Those are not proof-speed ratios.
- Completion bounds improve all six original random Markov cases in this run.
  Three additional cases prove optima within the budget. Long sparse and large
  second-order cases still do not prove optimality. First-incumbent latency can
  increase even when the eventual result improves.

The [raw comparison](../benchmarks/results/redesign_comparison_2026-09-16_corrected.json)
contains **1,260 timing samples and 60 isolated memory samples**. Its
[reference source archive](../benchmarks/results/redesign_comparison_2026-09-16_corrected.reference.tar.gz)
and [candidate source archive](../benchmarks/results/redesign_comparison_2026-09-16_corrected.candidate.tar.gz)
preserve the exact measured sources. The [baseline protocol](performance_baseline.md)
defines the fixtures, timing scopes, limits and the earlier interrupted harness run.

## Memory review and decision

The large second-order case triggers the memory investigation threshold.
[Two additional isolated pairs](../benchmarks/results/redesign_memory_investigation_2026-09-16.json)
reproduce **1,173.5 KiB with local bounds versus 6,096.8 KiB with completion bounds**.
A separate inspection finds **31,816 cached local edges**. The compiler retains
immutable edge costs for reuse across branches; this explains the additional
storage. The plan's default compilation/cache guard is 100,000 estimated edges.
This is an edge-count bound, not a fixed byte limit.

Decision: accept this measured time/quality versus memory tradeoff for the optional
completion-bound policy. On the uninstrumented workload it improves the incumbent
from 185 to 161 and reaches 1,000 nodes in about 1.91 seconds; local bounds reach
339–424 nodes before the three-second limit. Neither proves an optimum. Users
needing lower allocation peaks can select `bounding="local"` / `BOUNDING local`.
The default `auto` policy is therefore not a promise of minimum memory usage.
Future cache compression or selection changes must be compared against this case.
No rule-only or fixed-search CSP memory regression is being waived.

Allocation instrumentation stops both variants at the same time limit after
less work (63 local nodes versus 47–48 auto nodes in the repeat); those memory
runs are not performance or proof comparisons. Their complete outcomes remain
in the raw records. The infeasible root case has a sub-millisecond absolute
increase below the 2 ms time-review threshold; no speed claim is made for it.

This report uses `redesign_promotion_v1`. All raw samples, source archives,
and per-run outcomes are retained beside the JSON record. It supplements
the immutable initial baseline; timing scopes and search policies differ.

Raw record: `redesign_comparison_2026-09-16_corrected.json`. Python: `3.13.11`;
platform: `macOS-15.7.7-arm64-arm-64bit-Mach-O`; hash seed: `0`.
Reference commit: `2fbdd9d0e70ad5dc45fbf4dc5472510f84365f5c`.
Candidate runtime/workload hash: `b091563a32c5ca2fd9793b452015509f80c41586c1178366910239af4d78e66d`.
Collector hash: `12671214e459ce878da7fea30c65478dfb255cc0a3ae4cabfab827ba34c05377`.

Each of three paired sessions alternates implementation order and retains
seven fresh-state samples after a discarded warmup. Tables pool the 21
samples per side for readability; the final table retains per-session
medians, preparation/search separation, and full observed timing ranges.
No confidence interval or controlled thermal environment is claimed.

Rule fixtures require matching full output fingerprints and work counters.
Native/legacy CSP cases hold MRV, lexical value order and search tree fixed.
The mixed case intentionally adds rule-derived reports to the native CSP.
Markov cases compare solver policies/formulations, with independent sequence
validation. They are not fixed-work kernel comparisons.

## Rules, CSP and mixed execution

Times are total preparation plus execution in milliseconds. A slowdown flag
requires both >15% and >2 ms in at least two of the three paired sessions.
The deliberate additional mixed inference is reported as overhead.

| Case | Reference ms | Candidate ms | Speedup | Changes % | Review |
|---|---:|---:|---:|---|---|
| `rules/small/triangle_closure:indexed` | 1.05 | 1.04 | 1.01× | -10.4, -15.7, +19.8 | no |
| `rules/small/triangle_closure:semi-naive` | 1.02 | 0.97 | 1.05× | -5.6, -5.9, +0.1 | no |
| `rules/thesis/hanoi:indexed` | 39.57 | 39.81 | 0.99× | -0.5, +1.0, +1.5 | no |
| `rules/thesis/hanoi:semi-naive` | 40.75 | 40.83 | 1.00× | -0.0, +2.6, +0.7 | no |
| `rules/thesis/monkey_bananas/neopus_mea:indexed` | 21.90 | 21.57 | 1.02× | -1.7, -1.8, +2.8 | no |
| `rules/thesis/monkey_bananas/neopus_mea:semi-naive` | 19.77 | 20.36 | 0.97× | -0.8, +4.1, +3.1 | no |
| `joins/25x8/cold` | 39.02 | 38.68 | 1.01× | -0.3, -1.3, -2.6 | no |
| `joins/25x8/streamed` | 113.61 | 115.21 | 0.99× | +1.7, +0.8, +1.4 | no |
| `joins/100x8/cold` | 194.98 | 186.81 | 1.04× | +8.7, -6.4, -2.4 | no |
| `joins/100x8/streamed` | 510.51 | 491.04 | 1.04× | +3.4, +2.8, -10.2 | no |
| `classical/magic5` | 74.92 | 75.00 | 1.00× | +8.6, +0.2, -0.8 | no |
| `classical/sudoku_pure` | 83.93 | 83.38 | 1.01× | +1.2, +0.4, -1.9 | no |
| `classical/sudoku_mixed` | 441.12 | 439.82 | 1.00× | -0.6, -0.4, +0.6 | no |
| `magic3` | 5.31 | 1.88 | 2.82× | -64.5, -64.9, -65.6 | no |
| `magic4` | 424.55 | 211.61 | 2.01× | -50.5, -50.0, -53.8 | no |
| `latin5` | 7.24 | 2.66 | 2.72× | -59.1, -63.9, -62.2 | no |
| `latin7` | 40.44 | 13.12 | 3.08× | -67.0, -69.5, -67.4 | no |
| `mixed_magic3` | 1.82 | 2.37 | 0.77× | +30.7, +15.3, +42.1 | additional mixed work |

## Optimization outcomes

Each outcome cell is **incumbent / bound; completed proofs / 21; nodes;
median first-incumbent ms**. Ranges retain variation under the 3-second
budget. Ring cases have a 5,000-node limit; scaling cases have 1,000.
Only paired completed proofs receive a proof-time ratio. Infeasible cases
have no incumbent. A root relaxation bound can remain loose.

Legacy feasibility has no cooperative deadline, so the POSIX benchmark
controller interrupts it and preserves the last completed incumbent.
For interrupted legacy calls, nodes/failures count completed feasibility
runs only, explicitly marked `counters_complete=false` in the raw data.
Its bound is the separately known analytic edge-cost bound, not a solver API.
Native limits are cooperative and may overshoot at a safe boundary.

| Case | Modes | Total ms | Reference | Candidate | Proof ratio |
|---|---|---:|---|---|---|
| `markov25x4` | legacy → native | 1471.46 → 15.17 | 26 / 26; 21/21; 1009; 31.10 | 26 / 26; 21/21; 24; 14.82 | 96.98× |
| `markov33x8` | legacy → native | 3010.94 → 144.78 | 131 / 35; 0/21; 463; 90.78 | 35 / 35; 21/21; 32; 143.34 | not a proof comparison |
| `markov129x8` | legacy → native | 3019.07 → 2638.70 | 851 / 131; 0/21; 128; 1415.26 | 131 / 131; 21/21; 128; 2632.23 | not a proof comparison |
| `scaling/short_dense` | local → auto | 12.72 → 6.56 | 8 / 8; 21/21; 133; 0.87 | 8 / 8; 21/21; 97; 1.05 | 1.94× |
| `scaling/medium_sparse` | local → auto | 123.92 → 61.54 | 46 / 2; 0/21; 1000; 2.38 | 27 / 27; 21/21; 835; 2.61 | not a proof comparison |
| `scaling/long_sparse` | local → auto | 222.40 → 102.92 | 126 / 2; 0/21; 1000; 7.96 | 105 / 48; 0/21; 1000; 8.03 | not a proof comparison |
| `scaling/wide_sparse` | local → auto | 363.95 → 101.56 | 20 / 2; 0/21; 1000; 6.37 | 12 / 12; 21/21; 525; 8.59 | not a proof comparison |
| `scaling/second_order` | local → auto | 391.35 → 70.40 | 27 / 1; 0/21; 1000; 6.18 | 20 / 20; 21/21; 375; 8.49 | not a proof comparison |
| `scaling/large_costs` | local → auto | 39.30 → 12.79 | 359835 / 359835; 21/21; 308; 2.51 | 359835 / 359835; 21/21; 146; 2.83 | 3.07× |
| `scaling/long_second_order` | local → auto | 3032.80 → 1911.95 | 185 / 0; 0/21; 339–424; 560.48 | 161 / 2; 0/21; 1000; 1027.59 | not a proof comparison |
| `scaling/tied` | local → auto | 129.84 → 103.05 | 0 / 0; 21/21; 63; 123.88 | 0 / 0; 21/21; 63; 96.76 | 1.26× |
| `scaling/infeasible` | local → auto | 0.86 → 1.05 | none / none; 21/21; 1; none | none / none; 21/21; 1; none | 0.82× |

## Isolated allocation measurements

Values are **preparation / search peak KiB**, from separate subprocess
`tracemalloc` runs, not RSS. Search peaks include live preparation objects.
Immutable fixtures constructed before preparation are excluded. Classical
compatibility cases expose a single public solve: preparation reads as
approximately zero and execution includes their internal preparation.
Instrumentation can hit a time limit earlier and do less search; these are
peaks for the recorded instrumented outcome, not proof-memory comparisons.
A single increase >15% and >1 MiB requests repetition; it cannot establish
a reproduced regression by itself.

| Case | Reference KiB | Candidate KiB | Memory trigger |
|---|---:|---:|---|
| `rules/small/triangle_closure:indexed` | 25.5 / 28.8 | 25.5 / 28.7 | no |
| `rules/small/triangle_closure:semi-naive` | 25.5 / 27.1 | 25.5 / 27.1 | no |
| `rules/thesis/hanoi:indexed` | 48.7 / 570.8 | 48.7 / 570.8 | no |
| `rules/thesis/hanoi:semi-naive` | 49.1 / 571.1 | 49.1 / 571.1 | no |
| `rules/thesis/monkey_bananas/neopus_mea:indexed` | 203.4 / 362.2 | 203.4 / 362.2 | no |
| `rules/thesis/monkey_bananas/neopus_mea:semi-naive` | 204.1 / 351.1 | 204.1 / 351.1 | no |
| `joins/25x8/cold` | 577.7 / 4281.0 | 577.7 / 4281.0 | no |
| `joins/25x8/streamed` | 411.7 / 4657.0 | 411.7 / 4657.0 | no |
| `joins/100x8/cold` | 2315.7 / 17843.5 | 2315.7 / 17843.5 | no |
| `joins/100x8/streamed` | 1801.8 / 19300.9 | 1801.8 / 19300.9 | no |
| `classical/magic5` | 0.0 / 3689.9 | 0.0 / 3689.9 | no |
| `classical/sudoku_pure` | 0.0 / 5112.8 | 0.0 / 5112.7 | no |
| `classical/sudoku_mixed` | 0.0 / 5618.8 | 0.0 / 5618.8 | no |
| `magic3` | 96.8 / 435.5 | 5.8 / 129.9 | no |
| `magic4` | 248.0 / 9756.8 | 17.6 / 803.8 | no |
| `latin5` | 165.0 / 693.6 | 11.0 / 194.5 | no |
| `latin7` | 335.4 / 1776.7 | 25.3 / 499.3 | no |
| `mixed_magic3` | 5.8 / 129.9 | 13.2 / 155.5 | no |
| `markov25x4` | 202.5 / 4918.7 | 33.7 / 171.5 | no |
| `markov33x8` | 431.9 / 6012.0 | 66.7 / 574.6 | no |
| `markov129x8` | 1719.5 / 14026.3 | 274.3 / 1810.0 | no |
| `scaling/short_dense` | 28.0 / 205.0 | 28.0 / 194.6 | no |
| `scaling/medium_sparse` | 45.6 / 126.1 | 45.6 / 227.6 | no |
| `scaling/long_sparse` | 87.5 / 191.7 | 87.5 / 257.3 | no |
| `scaling/wide_sparse` | 89.0 / 364.8 | 89.0 / 780.3 | no |
| `scaling/second_order` | 81.1 / 145.1 | 81.1 / 380.7 | no |
| `scaling/large_costs` | 45.4 / 225.4 | 45.4 / 199.8 | no |
| `scaling/long_second_order` | 976.4 / 1173.5 | 976.4 / 6096.8 | reproduced; reviewed above |
| `scaling/tied` | 348.0 / 579.9 | 348.0 / 1137.0 | no |
| `scaling/infeasible` | 67.0 / 62.2 | 67.0 / 65.5 | no |

## Per-session timing detail

Each cell is **prepare median / execute median / total min–max ms**.
Complete raw samples and counters remain the authoritative evidence.

| Case / session | Reference | Candidate |
|---|---|---|
| `rules/small/triangle_closure:indexed` / 1 | 0.86 / 0.17 / 0.96–1.21 | 0.84 / 0.16 / 0.94–1.58 |
| `rules/small/triangle_closure:indexed` / 2 | 0.88 / 0.20 / 0.93–1.40 | 0.81 / 0.15 / 0.92–1.42 |
| `rules/small/triangle_closure:indexed` / 3 | 0.79 / 0.15 / 0.93–1.16 | 0.90 / 0.17 / 1.03–1.33 |
| `rules/small/triangle_closure:semi-naive` / 1 | 0.93 / 0.12 / 0.89–1.27 | 0.81 / 0.14 / 0.91–1.41 |
| `rules/small/triangle_closure:semi-naive` / 2 | 0.89 / 0.14 / 0.91–1.38 | 0.85 / 0.14 / 0.90–1.27 |
| `rules/small/triangle_closure:semi-naive` / 3 | 0.84 / 0.13 / 0.95–1.29 | 0.83 / 0.12 / 0.90–1.33 |
| `rules/thesis/hanoi:indexed` / 1 | 1.38 / 38.32 / 39.13–40.21 | 1.30 / 38.11 / 39.29–40.25 |
| `rules/thesis/hanoi:indexed` / 2 | 1.26 / 38.38 / 39.22–40.67 | 1.43 / 38.50 / 39.65–44.18 |
| `rules/thesis/hanoi:indexed` / 3 | 1.27 / 37.98 / 38.27–41.57 | 1.46 / 38.28 / 39.08–40.22 |
| `rules/thesis/hanoi:semi-naive` / 1 | 1.42 / 39.51 / 40.51–41.99 | 1.38 / 39.38 / 39.54–41.70 |
| `rules/thesis/hanoi:semi-naive` / 2 | 1.42 / 39.35 / 40.02–41.63 | 1.36 / 40.38 / 40.67–43.63 |
| `rules/thesis/hanoi:semi-naive` / 3 | 1.33 / 39.05 / 40.10–41.71 | 1.28 / 39.10 / 40.13–41.29 |
| `rules/thesis/monkey_bananas/neopus_mea:indexed` / 1 | 4.63 / 17.90 / 20.14–23.35 | 4.32 / 17.80 / 21.47–23.80 |
| `rules/thesis/monkey_bananas/neopus_mea:indexed` / 2 | 4.42 / 17.77 / 20.63–25.24 | 4.41 / 17.20 / 20.91–23.80 |
| `rules/thesis/monkey_bananas/neopus_mea:indexed` / 3 | 4.34 / 16.63 / 20.66–23.56 | 4.35 / 16.90 / 20.00–22.05 |
| `rules/thesis/monkey_bananas/neopus_mea:semi-naive` / 1 | 4.28 / 15.75 / 19.15–21.11 | 4.34 / 15.75 / 19.10–21.39 |
| `rules/thesis/monkey_bananas/neopus_mea:semi-naive` / 2 | 4.38 / 15.39 / 18.59–20.71 | 4.72 / 16.24 / 20.36–24.33 |
| `rules/thesis/monkey_bananas/neopus_mea:semi-naive` / 3 | 4.44 / 15.43 / 19.14–21.58 | 4.65 / 15.64 / 18.96–21.89 |
| `joins/25x8/cold` / 1 | 2.08 / 36.90 / 37.91–50.54 | 1.95 / 36.88 / 36.56–50.65 |
| `joins/25x8/cold` / 2 | 2.04 / 37.71 / 38.39–55.13 | 2.02 / 36.95 / 36.48–50.33 |
| `joins/25x8/cold` / 3 | 1.96 / 36.42 / 37.08–52.60 | 1.96 / 35.63 / 36.77–48.53 |
| `joins/25x8/streamed` / 1 | 6.71 / 107.28 / 112.13–127.58 | 6.63 / 109.02 / 113.54–129.38 |
| `joins/25x8/streamed` / 2 | 6.82 / 106.47 / 111.47–127.69 | 6.67 / 107.54 / 113.43–127.18 |
| `joins/25x8/streamed` / 3 | 6.82 / 107.20 / 112.53–130.30 | 6.75 / 108.62 / 113.98–131.66 |
| `joins/100x8/cold` / 1 | 8.18 / 187.29 / 152.97–210.54 | 9.18 / 202.38 / 161.92–229.50 |
| `joins/100x8/cold` / 2 | 8.37 / 183.44 / 150.29–207.50 | 8.22 / 172.24 / 141.99–216.27 |
| `joins/100x8/cold` / 3 | 8.24 / 188.46 / 154.48–206.45 | 8.25 / 184.06 / 153.27–207.54 |
| `joins/100x8/streamed` / 1 | 26.81 / 484.11 / 469.51–638.09 | 27.24 / 500.81 / 476.07–579.26 |
| `joins/100x8/streamed` / 2 | 27.70 / 482.34 / 479.44–561.92 | 27.29 / 497.29 / 472.32–578.93 |
| `joins/100x8/streamed` / 3 | 27.61 / 504.63 / 473.06–585.19 | 26.34 / 448.94 / 437.28–526.07 |
| `classical/magic5` / 1 | 0.00 / 74.92 / 73.37–86.22 | 0.00 / 81.39 / 71.87–96.73 |
| `classical/magic5` / 2 | 0.00 / 74.58 / 73.38–88.70 | 0.00 / 74.71 / 73.62–86.21 |
| `classical/magic5` / 3 | 0.00 / 75.38 / 72.02–132.82 | 0.00 / 74.74 / 73.56–85.31 |
| `classical/sudoku_pure` / 1 | 0.00 / 84.86 / 83.51–94.48 | 0.00 / 85.88 / 84.33–96.95 |
| `classical/sudoku_pure` / 2 | 0.00 / 82.72 / 82.11–91.71 | 0.00 / 83.02 / 81.90–96.40 |
| `classical/sudoku_pure` / 3 | 0.00 / 84.07 / 81.82–93.29 | 0.00 / 82.45 / 80.97–93.09 |
| `classical/sudoku_mixed` / 1 | 0.00 / 440.34 / 437.33–458.96 | 0.00 / 437.48 / 432.20–449.47 |
| `classical/sudoku_mixed` / 2 | 0.00 / 443.69 / 434.75–452.45 | 0.00 / 441.79 / 433.77–451.01 |
| `classical/sudoku_mixed` / 3 | 0.00 / 441.01 / 433.59–455.59 | 0.00 / 443.56 / 435.02–452.92 |
| `magic3` / 1 | 0.57 / 4.69 / 4.77–6.09 | 0.02 / 1.86 / 1.69–2.15 |
| `magic3` / 2 | 0.57 / 4.63 / 4.74–6.29 | 0.02 / 1.82 / 1.72–2.30 |
| `magic3` / 3 | 0.61 / 4.82 / 4.74–6.76 | 0.02 / 1.87 / 1.69–2.10 |
| `magic4` / 1 | 1.55 / 423.03 / 422.37–436.39 | 0.04 / 210.18 / 207.41–217.69 |
| `magic4` / 2 | 1.56 / 421.09 / 400.28–432.29 | 0.04 / 211.23 / 208.34–211.86 |
| `magic4` / 3 | 1.62 / 461.93 / 415.33–574.21 | 0.04 / 213.95 / 212.66–225.37 |
| `latin5` / 1 | 0.78 / 5.97 / 6.35–7.51 | 0.03 / 2.72 / 2.37–3.88 |
| `latin5` / 2 | 0.83 / 6.46 / 7.08–9.83 | 0.03 / 2.68 / 2.36–3.80 |
| `latin5` / 3 | 0.80 / 6.05 / 6.43–7.99 | 0.03 / 2.54 / 2.42–3.59 |
| `latin7` / 1 | 2.30 / 37.27 / 38.52–41.25 | 0.05 / 13.02 / 12.81–13.57 |
| `latin7` / 2 | 2.69 / 40.48 / 41.75–133.65 | 0.05 / 13.02 / 12.77–13.39 |
| `latin7` / 3 | 2.74 / 37.56 / 39.35–43.55 | 0.05 / 13.10 / 12.82–13.64 |
| `mixed_magic3` / 1 | 0.02 / 1.80 / 1.68–2.03 | 0.03 / 2.34 / 2.17–4.39 |
| `mixed_magic3` / 2 | 0.02 / 1.88 / 1.69–1.97 | 0.03 / 2.16 / 2.15–3.50 |
| `mixed_magic3` / 3 | 0.01 / 1.70 / 1.69–1.97 | 0.03 / 2.40 / 2.24–4.33 |
| `markov25x4` / 1 | 1.11 / 1472.50 / 1357.60–1567.15 | 0.23 / 14.89 / 14.88–16.53 |
| `markov25x4` / 2 | 1.10 / 1470.28 / 1378.05–1946.53 | 0.24 / 15.11 / 14.79–22.24 |
| `markov25x4` / 3 | 1.11 / 1446.26 / 1409.54–1543.72 | 0.24 / 14.85 / 15.01–16.54 |
| `markov33x8` / 1 | 3.07 / 3007.09 / 3008.25–3011.61 | 1.16 / 144.41 / 142.73–148.83 |
| `markov33x8` / 2 | 3.10 / 3008.08 / 3009.73–3012.48 | 1.16 / 143.55 / 141.51–147.02 |
| `markov33x8` / 3 | 3.18 / 3007.75 / 3009.71–3019.40 | 1.15 / 139.99 / 138.80–147.36 |
| `markov129x8` / 1 | 12.00 / 3007.15 / 3016.27–3020.66 | 4.67 / 2629.72 / 2620.40–2685.61 |
| `markov129x8` / 2 | 12.66 / 3007.17 / 3018.15–3020.62 | 4.53 / 2638.18 / 2628.12–2870.41 |
| `markov129x8` / 3 | 12.05 / 3005.26 / 3016.04–3019.96 | 4.68 / 2634.01 / 2605.12–2674.80 |
| `scaling/short_dense` / 1 | 0.28 / 12.77 / 12.43–14.51 | 0.28 / 6.32 / 6.51–7.65 |
| `scaling/short_dense` / 2 | 0.28 / 12.44 / 12.12–13.57 | 0.27 / 6.29 / 6.15–7.49 |
| `scaling/short_dense` / 3 | 0.28 / 12.29 / 12.36–13.30 | 0.25 / 6.31 / 6.30–7.59 |
| `scaling/medium_sparse` / 1 | 0.44 / 123.57 / 121.75–125.19 | 0.42 / 61.74 / 60.26–64.02 |
| `scaling/medium_sparse` / 2 | 0.43 / 122.79 / 121.76–128.82 | 0.41 / 61.54 / 60.68–63.31 |
| `scaling/medium_sparse` / 3 | 0.44 / 123.50 / 123.01–126.47 | 0.42 / 60.52 / 60.73–61.54 |
| `scaling/long_sparse` / 1 | 0.79 / 225.16 / 224.40–234.24 | 0.77 / 103.00 / 102.35–108.50 |
| `scaling/long_sparse` / 2 | 0.82 / 221.13 / 220.28–225.86 | 0.76 / 102.09 / 101.49–182.49 |
| `scaling/long_sparse` / 3 | 0.76 / 221.22 / 220.41–223.33 | 0.75 / 100.64 / 101.07–104.90 |
| `scaling/wide_sparse` / 1 | 1.21 / 363.28 / 361.46–442.33 | 1.24 / 100.14 / 100.01–102.62 |
| `scaling/wide_sparse` / 2 | 1.25 / 361.87 / 358.93–366.07 | 1.23 / 100.21 / 100.44–103.99 |
| `scaling/wide_sparse` / 3 | 1.33 / 365.37 / 362.57–371.63 | 1.24 / 100.74 / 100.92–104.51 |
| `scaling/second_order` / 1 | 1.48 / 389.40 / 385.88–392.85 | 1.41 / 68.32 / 68.91–71.89 |
| `scaling/second_order` / 2 | 1.44 / 391.92 / 387.97–396.13 | 1.43 / 67.77 / 68.60–72.18 |
| `scaling/second_order` / 3 | 1.42 / 390.81 / 390.10–443.22 | 1.48 / 70.93 / 70.40–75.58 |
| `scaling/large_costs` / 1 | 0.38 / 38.42 / 38.58–40.12 | 0.38 / 12.38 / 12.52–14.45 |
| `scaling/large_costs` / 2 | 0.42 / 39.58 / 39.30–41.35 | 0.38 / 12.46 / 12.51–14.41 |
| `scaling/large_costs` / 3 | 0.39 / 38.75 / 38.94–40.87 | 0.37 / 12.42 / 12.68–14.28 |
| `scaling/long_second_order` / 1 | 29.63 / 3002.74 / 3030.16–3035.31 | 29.28 / 1906.55 / 1895.33–2161.26 |
| `scaling/long_second_order` / 2 | 29.57 / 3001.85 / 3030.83–3036.19 | 30.01 / 1856.53 / 1877.44–1941.43 |
| `scaling/long_second_order` / 3 | 30.39 / 3003.38 / 3031.99–3057.81 | 30.05 / 1887.07 / 1898.55–2053.15 |
| `scaling/tied` / 1 | 5.80 / 123.72 / 128.69–133.82 | 5.71 / 99.83 / 104.70–111.91 |
| `scaling/tied` / 2 | 5.75 / 124.75 / 128.90–131.96 | 5.73 / 96.93 / 101.68–105.09 |
| `scaling/tied` / 3 | 5.64 / 124.29 / 129.13–132.01 | 5.70 / 96.34 / 101.18–103.99 |
| `scaling/infeasible` / 1 | 0.62 / 0.23 / 0.83–1.01 | 0.61 / 0.43 / 1.02–1.18 |
| `scaling/infeasible` / 2 | 0.63 / 0.22 / 0.82–0.98 | 0.63 / 0.43 / 1.04–1.23 |
| `scaling/infeasible` / 3 | 0.65 / 0.23 / 0.83–1.04 | 0.61 / 0.44 / 1.01–1.29 |
