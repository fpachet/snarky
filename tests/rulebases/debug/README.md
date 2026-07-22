# Mini Boojum debug rule base

This is the default small rule base for day-to-day engine debugging. It is a
modern project fixture, not a historical Boojum artifact.

It is deliberately small enough to inspect by hand while exercising four
important mechanisms:

1. a two-premise join (`grand_parent`);
2. a variable in relation position and recursive forward chaining
   (`transitive_relation`);
3. proposition-valued variables inside a nested triple
   (`knows_modus_ponens`);
4. an explicit non-default status (`expose_alarm_status`).

The input contains nine facts. The expected fixed point adds six facts, with
one result at proof depth two. An implementation should first reproduce the
set in `expected.yaml` with its naive strategy. Optimized strategies must then
produce the same set and proof depths.

`mini_boojum.rules` follows the provisional textual DSL from the engine
specification. `initial_facts.yaml` and `expected.yaml` are intentionally
parser-independent test fixtures.
