# Declarative finite model language

Status: supported experimental surface in `snarky.finite`. The operational Core
language and its existing `.rules`, `.constraints`, and `.program` semantics are
unchanged. See the [model contract](finite_model_contract.md) for exact semantics
and the [redesign evidence](redesign_progress.md) for validation and remaining gates.

A `.model` document declares one immutable finite model and zero or more named
queries. Parsing constructs the same Python `FiniteModel`, constraint, objective,
measure and `Query` objects used by the native and reference backends. Parsing
never starts search. There is no embedded Python evaluation.

## A complete example

```text
MODEL placement
    VARIABLE x DOMAIN SEQ[1 2]
    VARIABLE y DOMAIN SEQ[1 2]
    CONSTRAINT distinct
        KIND ALL_DIFFERENT
        SCOPE SEQ[x y]
    END_CONSTRAINT
    OBJECTIVE LINEAR
        TERMS SEQ[SEQ[1 x] SEQ[-2 y]]
        OFFSET 0
    END_OBJECTIVE
    QUERY best MINIMIZE
        BACKEND native
    END_QUERY
    QUERY all ENUMERATE
        BACKEND enumeration
    END_QUERY
END_MODEL
```

Run and inspect it with:

```sh
snarky check --syntax-only --format placement.model
snarky format placement.model
snarky run placement.model --query best --explain
```

`run` emits JSON. Status, termination, arithmetic, backend, incumbent, bound and
work counters are separate fields. With `--explain`, each solution includes
separate rule derivations, domain reductions and factor contributions. Rational
masses are strings such as `"7/12"`, preserving exact fractions. Nonfinite floating
mass projections use strings such as `"inf"`; log partition values remain available.
Exit status is 0 for an answered query (including infeasibility or zero mass),
1 for input errors, 2 for a resource limit, and 3 for an unsupported backend request.
A requested feasibility/solution limit is a successful answer, not a resource error.

The equivalent Python entry point is:

```python
from snarky.finite import parse_model_document

document = parse_model_document(source)
result = document.execute("best")
model = document.model
```

With one query, its name may be omitted. With no queries, execution defaults to
`SOLVE`. With multiple queries, choosing a name is mandatory. Queries cannot
silently replace each other's objective, measure or constraints.

## Terms, facts and rules

Reuse Snarky's term syntax: atoms, finite numbers, triples, sets `[a b]`, ordered
sequences `SEQ[a b]`, and `$variable` pattern variables. A decision variable's name
is an **atom** (`x`), distinct from a rule pattern variable (`$x`). Domains and
constraint scopes must use ordered `SEQ[...]`, preserving deterministic order.
Whole-line `#` comments are supported and preserved by formatting. Keywords and
declarations are case sensitive; query kinds and backend names are normalized.

```text
VARIABLE slot DOMAIN SEQ[1 2 3]
FACT (job kind delivery)
FACT (job approved yes) ' FAUX
```

Facts must be ground. Omitted status is `VRAI`; an explicit status after an
apostrophe uses the existing fact syntax. Empty domains denote infeasibility;
zero decision variables denote one empty assignment.

An existing `GROUP ... END_GROUP` block may appear inside the model. The validated
scoreable fragment admits positive, function-free derivations and already-bound
comparisons. Rules observe singleton assignment facts such as `(slot value 3)`
and may derive properties, but may not destructively change the model's domains
or construct new decision variables. Unsupported operational constructs are
rejected in `.model`; they remain usable in ordinary Core programs.

## Hard constraints

Every declaration has the form `CONSTRAINT name ... END_CONSTRAINT`. The complete
existing persistent vocabulary is available directly in the core package:

| `KIND` | Required fields | Example field values |
|---|---|---|
| `ALL_DIFFERENT` | `SCOPE` | `SEQ[x y z]` |
| `SUM` | `SCOPE`, `TARGET` | `SEQ[x y]`, `3` |
| `LINEAR_SUM` | `TERMS`, `OPERATOR`, `TARGET` | `SEQ[SEQ[2 x] SEQ[-1 y]]`, `LESS_EQUAL`, `4` |
| `COMPARE` | `LEFT`, `RIGHT`, `OPERATOR` | `x`, `y`, `LESS_THAN` |
| `ELEMENT` | `INDEX`, `ARRAY`, `VALUE` | `i`, `SEQ[x y z]`, `v`; index is one-based |
| `COUNT` | `SCOPE`, `VALUE`, `OPERATOR`, `TARGET` | `SEQ[x y]`, `a`, `EQUAL`, `1` |
| `GCC` | `SCOPE`, `BOUNDS` | `SEQ[x y]`, `SEQ[SEQ[a 1 2] SEQ[b 0 1]]` |
| `TABLE` | `SCOPE`, one or more `ALLOW` rows | `SEQ[x y]`, `ALLOW SEQ[1 2]` |
| `LEX_LESS_EQUAL` | `LEFT`, `RIGHT` | `SEQ[x y]`, `SEQ[z w]` |
| `FACTS` | zero or more `REQUIRE` and `FORBID` facts | `REQUIRE (job approved yes)` |

Aggregate operators are `EQUAL`, `LESS_EQUAL`, `GREATER_EQUAL`. Binary comparison
operators are `LESS_THAN`, `LESS_EQUAL`, `NOT_EQUAL`. Coefficients, targets and
cardinality bounds are integers. Names and scopes are validated by the ordinary
Python model constructors; undeclared variables and duplicate names fail.

A persistent constraint may also have `GUARD fact`, activating it when that
positive fact belongs to the deterministic closure. `FACTS` constraints cannot be
guarded in this syntax. `REQUIRE` and `FORBID` are reserved for `KIND FACTS`.

```text
CONSTRAINT late_delivery
    KIND TABLE
    SCOPE SEQ[delivery]
    GUARD (shift needs overtime)
    ALLOW SEQ[2]
END_CONSTRAINT
```

Python `PredicateConstraint` callbacks remain the documented extension interface.
They have no executable-text equivalent: implement new syntax and a compiler for
an extension deliberately rather than evaluating arbitrary source strings.

## Objectives and factor scopes

There is at most one `OBJECTIVE ... END_OBJECTIVE` block. `LINEAR` takes `TERMS`
(default `SEQ[]`) and `OFFSET` (default zero). `FACTORS` takes an optional integer
`OFFSET` and named `TABLE_FACTOR` and `INTEGER_FACTOR` blocks:

```text
OBJECTIVE FACTORS
    OFFSET -2
    TABLE_FACTOR preferred_slot
        SCOPE SEQ[slot]
        DEFAULT 0
        ROW SEQ[2] SCORE 5
    END_TABLE_FACTOR
    INTEGER_FACTOR overtime_cost
        SCOPE shift
        WEIGHT -8
        WHEN
            (shift needs overtime)
    END_FACTOR
END_OBJECTIVE
```

Table scores and defaults are integers; a missing row takes `DEFAULT`, which is
zero unless specified. It does not forbid a configuration. Use a hard table for
support. Rows cannot repeat. `SCOPE SEQ[]` permits constant tables.

`INTEGER_FACTOR` reuses the pure factor premise grammar. It contributes `WEIGHT`
once per distinct ground `SCOPE`. Multiple witnesses do not multiply a Boolean
activation. Its weight is parsed as an integer without conversion through float.
General premise factors currently provide no partial objective bound; exhaustive
optimization still proves optimality when it finishes.

## Probability measures

An omitted measure is uniform over hard-feasible configurations. A `MEASURE ...
END_MEASURE` block can contain `BASE_TABLE`, `LOG_TABLE` and existing
`FACTOR_GROUP ... END_FACTOR_GROUP` declarations.

```text
MEASURE
    BASE_TABLE initial
        SCOPE SEQ[x]
        ROW SEQ[a] WEIGHT 1/3
        ROW SEQ[b] WEIGHT 2/3
    END_BASE_TABLE
    LOG_TABLE preference
        SCOPE SEQ[x]
        ROW SEQ[a] SCORE 2
    END_LOG_TABLE
    FACTOR_GROUP observations
        FACTOR selected
        SCOPE $symbol
        LOG_WEIGHT 0.5
        WHEN
            (x value $symbol)
        END_FACTOR
    END_FACTOR_GROUP
END_MEASURE
```

`BASE_TABLE` entries/defaults are nonnegative rational masses. Integer, fraction
and decimal strings are parsed directly by `Fraction`; unlike a Python float,
a text decimal denotes its exact decimal value. Missing rows have the explicit
default, zero unless provided. Base weights multiply. `LOG_TABLE` has the same
integer table syntax as objective table factors, but contributes to a natural-log
score inside `exp(score)`. Existing factor groups declare finite floating-point
`LOG_WEIGHT` values and preserve scope/witness semantics.

An alternative single-line declaration is `MEASURE NEGATIVE_LOG2_OBJECTIVE`.
This explicitly interprets an integer **table-factor** objective as negative log2
mass. It supports the synthetic dyadic Markov examples without silently treating
arbitrary search weights or integer objectives as probabilities. Conversion from
rounded log-costs does not restore the original unrounded distribution.

## Queries and capabilities

```text
QUERY draws SAMPLE_EXACT
    BACKEND weighted_search
    SAMPLE_COUNT 10
    SEED 7
    MAX_NODES 100000
    TIME_LIMIT 5.0
END_QUERY
```

Kinds are `SOLVE`, `ENUMERATE`, `MINIMIZE`, `MAXIMIZE`, `PARTITION`, `SAMPLE_EXACT`.
Native optimization also accepts `BOUNDING auto` (default) or `BOUNDING local`,
and `VALUE_POLICY declared` (default) or `VALUE_POLICY objective`. The latter
orders values using admissible completion bounds. Nondefault search options on
other backends or non-optimization queries are rejected, rather than ignored.
These options correspond to the Python `solve` keyword arguments and
`QueryRequest` fields; they do not change the model's objective or measure.
`MAX_NODES`, `MAX_SOLUTIONS`, and `TIME_LIMIT` are optional and positive;
`MAX_SOLUTIONS` applies only to feasibility/enumeration. `SAMPLE_COUNT` defaults
to one and applies to sampling; `SEED` defaults to zero. Optimization requires an
explicit objective. The parser rejects unknown and unused fields.

Backends are `native` (default), `enumeration`, `weighted_search`, and `regular_bp`.
The last two are probability-only. `native` routes probability queries to weighted
search. Exact capability and arithmetic boundaries are described in the
[model contract](finite_model_contract.md); declaring a backend never permits it
to ignore unsupported constraints. Optional regular-BP availability is checked
at execution, so source validation does not require that dependency.

## Migration and packaged examples

Existing Core and companion applications remain available. For compatible legacy
CSPs, `csp_solver.native.native_model` translates initial candidate facts and
persistent constraints. It rejects implicit binary relation facts and application
rules that need explicit compilation. For new pure CSPs, declare native domains
directly to avoid candidate-fact construction and inference sessions.

For mixed applications, prepare immutable context with the operational API if
needed, then construct a finite model with explicit variables and scoreable rules.
Move destructive preparation outside search. Preserve constraints as hard
predicates; declare preference factors and probability measures separately from
legacy choice weights. Validate complete feasible sets and objectives before
replacing an application path. No automatic semantics-changing rewrite is provided.

The wheel includes five executable text examples:

- [Positive rule closure](../src/snarky/finite/models/rules.model).
- [Four queens](../src/snarky/finite/models/four_queens.model).
- [Signed linear optimization](../src/snarky/finite/models/linear.model).
- [Mixed scheduling with scoped factors](../src/snarky/finite/models/scheduling.model).
- [Conditioned Markov probabilities](../src/snarky/finite/models/probability.model).

They are available without the companion package:

```python
from snarky.finite import parse_model_document
from snarky.finite.examples import model_source

result = parse_model_document(model_source("scheduling")).execute("optimum")
```

The probability example's `regular` query additionally requires `vo_regular_bp`.
Bach corpus data and research dependencies are not part of these examples.
