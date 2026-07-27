# Language validation and formatting

Snarky ships one command-line tool for its textual source formats:

- `.rules` for rules and rule groups;
- `.constraints` for persistent finite-domain templates;
- `.program` for orchestration manifests.

The command is installed with the `snarky` package. The equivalent
source-tree invocation is `python -m snarky`.

## Validate sources

Validate one file or recursively discover supported files below directories:

```sh
snarky check example.rules
snarky check rulebases sudoku harmonizer
snarky check .
```

Validation covers block structure, terms and arithmetic, sequential variable
binding, action and `CHOICE` bindings, duplicate declarations, persistent
constraint contracts, and program structure. `CHECK` and `COMPUTE` names are
registered as inert placeholders: validation checks their syntax and
bindings, but never executes application code.

Diagnostics include a stable code and a source position:

```text
example.rules:5:5: error [SNK100] unsupported action 'REPLACE (...)'
        REPLACE (...)
        ^
```

The process exits with status 0 when there are no errors and 1 otherwise.
Warnings do not make the command fail.

## Program references

When several paths are checked together, program group and constraint names
are compared with declarations in the selected textual sources:

```sh
snarky check harmonizer csp_solver
```

An unresolved name is normally a warning because applications may construct
groups or propagators in Python. Use strict linking for a completely textual
project:

```sh
snarky check --strict-links my_project
```

Use syntax-only validation when the external catalogue is deliberately
unavailable:

```sh
snarky check --syntax-only example.program
```

## Format sources

Apply canonical formatting in place:

```sh
snarky format example.rules
snarky format rulebases sudoku
```

Inspect changes without writing:

```sh
snarky format --check .
snarky format --diff example.rules
```

The formatter:

- uses four-space structural indentation;
- removes trailing whitespace and trailing blank lines;
- preserves comments and the order of blank lines;
- preserves the contents and order of significant source lines;
- writes exactly one final newline;
- canonicalizes `NOT EXISTS ... END_EXISTS` to
  `NOT EXISTS ... END_NOT_EXISTS`.

It does not reorder premises or actions, rewrite expressions, or execute
rules. The implementation is idempotent, and tests verify that parsing before
and after formatting produces the same rule model.

Formatting stops without writing any file if one of the selected sources does
not validate.

## Continuous integration

Require both valid and canonically formatted source without changing files:

```sh
snarky check --syntax-only --format .
```

File discovery ignores build, cache, virtual-environment, dependency, and
`third_party` directories. An explicitly named supported file is still
checked even when it is located below an otherwise ignored directory.

## Diagnostic codes

| Code | Meaning |
|---|---|
| `SNK001` | source is not canonically formatted |
| `SNK002` | requested source path does not exist |
| `SNK003` | unsupported source suffix in the library API |
| `SNK100` | syntax or local semantic error |
| `SNK101` | historical `END_EXISTS` spelling after `NOT EXISTS` |
| `SNK201` | program group absent from selected textual sources |
| `SNK202` | program constraint absent from selected textual sources |

The formatter and validator live outside the stable inference API. Their CLI
behavior and diagnostic codes are user-facing, while their internal Python
implementation may evolve during the 0.1 series.
