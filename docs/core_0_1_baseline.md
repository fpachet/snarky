# Snarky Core 0.1 Baseline

Status: frozen compatibility contract; not a public release.

This document freezes the existing symbolic Snarky language and runtime as the
reference **Snarky Core 0.1** baseline. The freeze protects working behavior
while probabilistic constraint learning, maximum-likelihood estimation, and
regular belief propagation are designed and tested as a separate experimental
layer.

The baseline is the first repository commit containing this document. Its
commit identifier is the durable reference until the legal and provenance
gates in [the release procedure](../RELEASE.md) permit a public version tag.
No release or redistribution authorization is implied by this baseline.

## 1. Purpose of the freeze

The probabilistic research must be able to reuse Snarky without silently
changing what an existing rule program means. In particular, a new
interpretation of a weight, a choice, a rule activation, or a constraint would
make old examples impossible to compare with new ones.

The freeze therefore establishes three requirements:

1. existing Core programs retain their observable meaning;
2. probabilistic features enter through additive, explicitly experimental
   interfaces;
3. optimized or specialized inference engines are checked against the Core
   reference semantics whenever their supported fragments overlap.

The freeze does not claim that every package in this repository is stable.
The Bach harmonizer, learned-factor experiments, specialized search policies,
and the public surface of `csp_solver` remain research code.

## 2. Frozen surface

### 2.1 Python API

The machine-readable set `snarky.api_stability.STABLE_CORE_API` defines the
frozen Python import surface. It is the set exported by:

```python
from snarky import *
```

The categories and historical top-level aliases remain governed by
[the API stability policy](api_stability.md). Advanced, integration, and
experimental names are deliberately outside the frozen surface.

### 2.2 Rule-language semantics

The baseline freezes the documented meaning of:

- terms, variables, facts, propositions, sequences, and sets;
- rule premises, substitutions, comparisons, collections, and computed
  predicates;
- `ADD` and `REMOVE` actions;
- forward chaining, deterministic conflict resolution, and refraction;
- named rule groups, programs, steps, sessions, and checkpoints;
- reversible `CHOICE` alternatives and their current local weights;
- persistent finite-domain constraints and their contradiction behavior;
- propagation followed by reversible search and backtracking;
- provenance and the documented result/status types.

The normative descriptions remain [the textual syntax](syntax.md) and
[the reference semantics](semantics.md). A future implementation may be
faster, but a documented Core program must not acquire a different result
solely because an optimization or backend changed.

### 2.3 `CHOICE` is not a probabilistic model

The existing `CHOICE ... WEIGHT ...` construction is frozen with its current
meaning: it exposes alternatives to reversible search, and the weight is used
by the selected choice policy for local ordering or local randomized
selection. It is not a globally normalized probability, an MLE parameter, a
factor contribution, or a completion mass.

The probabilistic extension must not reinterpret that field. Exact
probabilistic sampling will use a separate inference query whose branch
probabilities are computed from complete feasible continuation masses. If an
explicit priority-oriented syntax is later useful, it must be additive and
experimental.

### 2.4 Persistent constraints

The semantics of the existing persistent finite-domain constraint forms are
part of the tested baseline. Their low-level Python implementation and the
standalone `csp_solver` API are not frozen. This distinction permits internal
optimization without weakening the observable filtering, contradiction, and
rollback behavior promised to Core programs.

## 3. Observable compatibility

For the frozen surface, compatibility includes:

- accepted documented syntax;
- public import names and documented call signatures;
- substitutions and produced facts;
- deterministic ordering where it is documented;
- mutation, refraction, checkpoint, rollback, and backtracking behavior;
- contradiction and terminal statuses;
- persistent-domain reductions and final solutions;
- provenance sufficient to explain rule-derived facts.

The following are not frozen:

- wall-clock performance;
- internal indexes, caches, queues, and object layouts;
- private modules and names;
- experimental or advanced strategy behavior not promised by its own
  documentation;
- serialized Python objects, internal checkpoints, or benchmark files;
- the Bach harmonizer's musical model and generated output;
- any syntax introduced by the probabilistic-learning proposal.

## 4. Permitted changes after the freeze

Patch-level work may:

- fix a defect relative to the documented semantics;
- improve performance without changing observable behavior;
- improve diagnostics while preserving their documented error family;
- add tests and explanations;
- add an optional backend that passes differential conformance tests.

Minor-version work may add unambiguous syntax or new stable names. Removing or
reinterpreting frozen behavior requires the deprecation process in
[the versioning policy](versioning.md).

Experimental work must be isolated by at least one visible boundary:

- a dedicated module;
- an experimental top-level declaration;
- an explicit feature flag or query mode;
- or a separate package that consumes the Core API.

It must not inject learned state into rule matching, make factor activation
mutate working memory, or replace `CHOICE` weights with corpus probabilities.

## 5. Boundary with probabilistic constraint learning

The architecture in
[Probabilistic Constraint Learning and Exact Generation](probabilistic_constraint_learning_spec.md)
is an extension of this baseline, not a revision of it.

The boundary is:

| Concern | Snarky Core 0.1 | Experimental probabilistic layer |
|---|---|---|
| Derived symbolic knowledge | rules and working memory | may read derived observables |
| Impossibility | persistent constraints and contradiction | may add explicitly scoped hard constraints |
| Search | reversible choices and backtracking | may call Core as a feasibility oracle |
| Preference | local `CHOICE` policy weight | pure factor score with learned parameter |
| Learning | outside the Core contract | structure induction and conditional MLE |
| Exact probability | not claimed by `CHOICE` | partition, marginals, expectations, exact sampling |
| Chain specialization | none required | regular/variable-order BP backend |

Data may flow from stable derivations into pure factor evaluation, but factor
evaluation may not cause rule firings or mutate Core state. User constraints
may restrict the feasible set, but do not change learned parameters unless an
explicit learning program is run.

## 6. Conformance gates

A commit may be described as conforming to the Core 0.1 baseline only if the
following repository checks pass in the project environment:

```sh
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/pytest
.venv/bin/python scripts/check_markdown_links.py
PYTHONPATH=. .venv/bin/snarky check --syntax-only --format .
```

Distribution validation must use freshly built artifacts rather than a
possibly stale `dist/` directory:

```sh
artifact_dir="$(mktemp -d)"
.venv/bin/python -m build --outdir "$artifact_dir"
.venv/bin/python scripts/check_distribution.py "$artifact_dir"
.venv/bin/python scripts/check_wheel_install.py "$artifact_dir"
```

`PYTHONPATH=.` makes the checkout-local companion `csp_solver` package visible
to the installed console entry point. This is unnecessary once validation is
run from a distribution that packages the corresponding integration.

Where a command depends on already-built distribution artifacts, failure due
only to an absent artifact is a release-build issue rather than a semantic
failure. A public release additionally requires every gate in `RELEASE.md`, a
fresh build, isolated wheel installation, and successful CI.

The conformance evidence should record:

- the exact commit identifier;
- Python and dependency versions;
- the commands run and their exit status;
- any skipped test and its reason;
- representative differential checks between reference and optimized
  strategies.

## 7. Baseline-change review

Every proposed Core change should answer these questions:

1. Does an existing valid program parse differently?
2. Can it derive a different fact, solution, ordering, or status?
3. Does it change rollback, refraction, contradiction, or provenance?
4. Does it move a name into or out of `STABLE_CORE_API`?
5. Is the change a bug fix, an additive feature, or an incompatible change?
6. Which differential or regression test demonstrates compatibility?

An optimization that cannot answer these questions is not ready to modify the
frozen Core.

## 8. Tag and publication policy

This baseline is intentionally identified by a commit rather than a Git
version tag. The repository currently has unresolved license and third-party
provenance gates. `RELEASE.md` prohibits a public version tag until those gates
are closed.

Once they are closed, the already-tested baseline commit can receive an
annotated Semantic Versioning tag without changing its code. Until then:

- do not publish a package or GitHub release;
- do not describe the baseline as redistributable;
- use the commit identifier in experiments and reports;
- keep probabilistic work visibly marked experimental.

This preserves both scientific reproducibility and the repository's release
safety policy.
