# Snarky textual syntax

This is the publication reference for Snarky's textual rule language and the
companion persistent-constraint template language. The parsers intentionally
accept a small explicit syntax; they do not evaluate Python source.

## Terms and facts

```text
atom
$variable
42
-3
2.5
(subject relation object)
[red green blue]
SEQ[first second third]
VRAI
FAUX
INEXISTANT
```

Parentheses contain exactly three recursive terms. `[ ... ]` is a finite set;
`SEQ[ ... ]` is an ordered finite sequence that retains duplicates. A bare
fact premise has status `VRAI`. An explicit status follows an apostrophe:

```text
($object color red)
($object color red) ' $status
```

Lines beginning with `#` are comments. Whitespace and indentation aid
readability but block keywords define structure.

## Rules and groups

```text
GROUP family_rules
    RULE grandparent
    WHEN
        ($x parent_of $y)
        ($y parent_of $z)
    THEN
        ADD ($x grandparent_of $z)
    END
END_GROUP
```

`parse_rules()` reads ungrouped `RULE ... END` definitions.
`parse_rule_groups()` reads `GROUP ... END_GROUP` blocks. Premises are
evaluated in textual order, so a comparison may use only variables already
bound by preceding premises.

## Learned factors

Factors use the same pure premise language but have no `THEN` block and no
actions:

```text
FACTOR_GROUP learned_bach
    FACTOR small_motion
    SCOPE SEQ[$decision $candidate]
    LOG_WEIGHT 0.7
    WHEN
        ($decision candidate $candidate)
        ($candidate small_motion yes)
    END_FACTOR
END_FACTOR_GROUP
```

`parse_factors()` reads standalone `FACTOR ... END_FACTOR` definitions.
`parse_factor_groups()` reads grouped definitions. `SCOPE` identifies one
ground factor instance; several witnesses for the same factor and scope count
only once. `LOG_WEIGHT` is a finite learned log contribution.

A factor can read facts, comparisons and registered pure predicates. It can
never execute `ADD`, `REMOVE`, `CHOICE`, `LET`, or any other action.
Factor activations are returned as immutable evaluation data and are not
inserted into working memory, so one factor cannot trigger another.

## Programs and sequential steps

`parse_rule_program()` reads a manifest that references named rule groups:

```text
PROGRAM satb_harmonizer
    PREPARE generate_voicings
    STEP harmonic_plan
        GROUP choose_harmonic_plan
    END_STEP
    STEP satb_realization
        GROUP choose_satb_realization
        CONSTRAINT voice_ranges
    END_STEP
    PROPAGATE maintain_channels
    INTERPRET expose_solution
END_PROGRAM
```

`PREPARE`, `PROPAGATE`, and `INTERPRET` each name one group; repeat a
directive to include several groups. `GROUP` inside a `STEP` names the rules
whose `CHOICE` actions are visible in that step. `CONSTRAINT` names a
session propagator supplied to the parser's constraint catalogue.

A step reaches the joint rules/constraints fixed point before exposing its
choices. When it has no remaining choice, execution advances to the next
step. This is not a commit: checkpoints created by earlier steps remain on
the search trail, so failure in a later step can backtrack into an earlier
one. An unstaged program may continue to use `CHOOSE group_name`.

## Premises

### Facts, focus, and comparisons

```text
($x relation $y)
FOCUS ($goal state pending)
$left == $right
$left != $right
$left < $right
$left <= $right
$left > $right
$left >= $right
DIVISIBLE $value BY 3
```

`FOCUS` is allowed on one top-level factual premise and is used by conflict
resolution. Comparisons do not generate values.

Arithmetic comparisons use `CONSTRAINT` inside a `WHEN` block:

```text
CONSTRAINT $x + 2 * $y <= $limit
```

Arithmetic supports `+`, `-`, `*`, `/`, `%`, parentheses, and unary signs.
This is a premise-local arithmetic filter; it is distinct from a top-level
persistent constraint declaration.

### Correlated blocks

```text
EXISTS
    ($x child $child)
END_EXISTS

NOT EXISTS
    ($x blocked_by $reason)
END_NOT_EXISTS

COUNT >= 2
    ($x child $child)
END_COUNT

UNIQUE
    ($cell candidate $value)
END_UNIQUE

COLLECT $values := $value
    ($cell candidate $value)
END_COLLECT
```

`EXISTS` and `NOT EXISTS` also accept a one-line form with one nested premise.
Blocks see outer bindings; their local variables do not escape.
`COLLECT` is the exception only for its declared target, which receives the
set of distinct projected values.

### Structured and generated bindings

```text
BIND $pair := SEQ[$left $right]
WINDOW $window := SEQ[$first $second $third] VIA next
COMBINATIONS $pair SIZE 2 FROM $values
ALL_DIFFERENT SEQ[$a $b $c]
NVALUE $count OF SEQ[$a $b $c]
```

`ALL_DIFFERENT` and `NVALUE` here constrain the values participating in one
rule instantiation. They do not remain active over `candidate` facts during
search.

Registered pure computed predicates use:

```text
COMPUTE $result := predicate_name ARGS SEQ[$a $b]
CHECK predicate_name ARGS SEQ[$a $b]
```

They require a `PredicateRegistry` passed to the parser.

## Actions

```text
ADD ($x state ready)
REMOVE ($x state pending)
LET $total := $left + $right
FRESH $identifier PREFIX generated

FOR EACH $item IN $items
    ADD ($container member $item)
END_FOR_EACH
```

`ADD` and `REMOVE` accept an optional apostrophe status. `LET` binds a
deterministic numeric result without asserting a fact. `FRESH` creates a
session-local atom. Actions execute in textual order.

An explicit branch point is:

```text
CHOICE ($variable decision $value) WEIGHT $weight
FROM
    ($variable candidate $value)
    ($variable choice_weight SEQ[$value $weight])
END_CHOICE
```

The weight defaults to `1` when omitted. `CHOICE` declares alternatives; it
does not branch during ordinary forward chaining. A choice-search controller
selects an alternative, checkpoints the session, propagates, and backtracks
when necessary.

## Persistent constraint templates

Persistent templates are parsed separately with
`parse_constraint_templates()`. They are grounded from root facts and remain
active across choice search.

The common skeleton is:

```text
CONSTRAINT template_name
KIND ALL_DIFFERENT
FOR EACH SEQ[$context]
    ($context kind line)
END_FOR_EACH
SCOPE $variable ORDER BY $position
FROM
    ($context member SEQ[$position $variable])
END_SCOPE
END
```

`FOR EACH` is optional. Its `SEQ[...]` is the grouping key for producing
multiple constraint instances. `SCOPE` projects variables; `ORDER BY` is
required when positional order matters.

Supported kind-specific clauses are:

```text
KIND ALL_DIFFERENT
```

```text
KIND SUM
...
TARGET $target
```

```text
KIND LINEAR_SUM
SCOPE SEQ[$coefficient $variable] ORDER BY $position
FROM
    ($expression term SEQ[$position $coefficient $variable])
END_SCOPE
OPERATOR LESS_EQUAL
TARGET $target
```

`LINEAR_SUM` supports integer coefficients, integer candidate domains, and
`EQUAL`, `LESS_EQUAL`, or `GREATER_EQUAL`. Coefficients must be non-zero and
each grounded variable may occur only once.

```text
KIND LESS_EQUAL
KIND LESS_THAN
KIND NOT_EQUAL
```

Each binary comparison uses an ordered scope containing exactly two distinct
variables. `LESS_EQUAL` and `LESS_THAN` require finite numeric `Number`
domains. `NOT_EQUAL` accepts any finite terms.

```text
KIND ELEMENT
SCOPE $array_variable ORDER BY $position
FROM
    ($array member SEQ[$position $array_variable])
END_SCOPE
INDEX $index_variable
VALUE $value_variable
```

`ELEMENT` means `$value_variable = array[$index_variable]`; indices are
one-based integers. The index, array variables, and value variable must all
be distinct.

```text
KIND COUNT
...
VALUE $counted_value
OPERATOR GREATER_EQUAL
TARGET $integer
```

`COUNT` compares the number of scoped variables equal to `VALUE` with a fixed
integer `TARGET`. Its operator is `EQUAL`, `LESS_EQUAL`, or `GREATER_EQUAL`.

```text
KIND GCC
...
BOUNDS SEQ[$value $lower $upper]
FROM
    ($bound value $value)
    ($bound lower $lower)
    ($bound upper $upper)
END_BOUNDS
```

```text
KIND TABLE
...
TUPLES $tuple
FROM
    ($relation allows $tuple)
END_TUPLES
```

```text
KIND LEX_LESS_EQUAL
SCOPE SEQ[$left $right] ORDER BY $position
FROM
    ($ordering pair SEQ[$position $left $right])
END_SCOPE
```

For `LEX_LESS_EQUAL`, every ordered scope row projects the corresponding
left/right pair. The two grounded numeric variable sequences must have the
same non-zero length.

Clauses appear in the order shown above. `TARGET`, coefficients, bounds, and
`COUNT` targets must ground to integer `Number` terms. Clause terms may be
literals or variables bound by `FOR EACH`/`SCOPE` premises.

The complete operational contract and examples are in
[Persistent finite-domain constraints](persistent_constraints.md).

## Two meanings of `CONSTRAINT`

The shared keyword is contextual:

| Location | Meaning | Lifetime |
|---|---|---|
| Inside `RULE ... WHEN` | arithmetic comparison premise | one rule instantiation |
| Top level with `KIND` | persistent finite-domain template | complete CSP search |

Similarly, premise-local `ALL_DIFFERENT SEQ[...]` filters an instantiation,
whereas top-level `KIND ALL_DIFFERENT` propagates changes over scoped
candidate domains at every search node.

## Execution boundary

Rules alone saturate by forward chaining. In finite-CSP search, persistent
constraints and affected rule groups alternate to a joint fixed point before
the engine tests the goal or exposes a `CHOICE`. Candidate-domain widening by
rules is not part of the current narrowing-only persistent semantics.

## Validation and formatting

The `snarky check` command validates `.rules`, `.constraints`, and `.program`
files. `snarky format` applies canonical four-space indentation while
preserving comments and semantics. See
[Language validation and formatting](language_tooling.md) for commands,
diagnostic codes, linking modes, and the formatting contract.
