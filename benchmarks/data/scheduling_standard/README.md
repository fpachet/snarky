# Established scheduling assessment: fixed protocol

Selection fixed on 2026-09-29, before any solver runs: PSPLIB `j30G_1.sm`
for G = **1, 5, 9, 14, 18, 22, 27, 31, 35, 40, 44, 48**; OR-Library
**ft06, la01, la02, la03, la04, la05**.

The J30 groups are twelve approximately equally spaced indices across 1–48
with gaps of four or five groups, always replicate 1. This
outcome-independent spread avoids a prefix-only or easy-case selection. It is
not a random sample or a complete factorial design; no population-level success
rate is claimed. The job-shop subset is prescribed by the assessment request.

Three fresh processes per case, ten seconds per search, hash seed 0, native
solver, dom/wdeg variable selection, objective value ordering, automatic bounds,
objective propagation and numeric masks enabled. Alternate forward/reverse case
order across repetitions. No symmetry, warm start, published objective cutoff or
published lower bound. Model construction and process overhead are measured
separately. Timeouts and failures remain in the evidence. No timing assertions.

External files remain in `generated/scheduling_standard/cache` (Git ignored).
The manifest pins source URLs and SHA-256 hashes. Download on explicit request;
normal benchmark runs use and verify the cache without network access. Synthetic
unit fixtures are first-party. See the assessment report for encoding and results.
