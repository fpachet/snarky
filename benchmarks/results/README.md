# Archived benchmark results

These JSON and CSV files are immutable raw records produced by benchmark
programs. They are tracked as scientific evidence because they document A/B
decisions, but they are not runtime source and are excluded from Python
distributions.

New records should include the benchmark name and ISO date in the filename,
plus commit, Python, platform, parameters, logical-equivalence checks, medians,
and individual samples where the format supports them.

Do not overwrite a historical record with results from another environment.
Create a new dated file and interpret it through
[`../README.md`](../README.md).
