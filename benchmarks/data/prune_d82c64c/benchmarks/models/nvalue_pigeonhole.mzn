include "nvalue.mzn";

int: variables;
int: values;
int: required_distinct;
set of int: variable_index = 1..variables;
set of int: value_set = 1..values;
array[variable_index] of var value_set: assignment;

constraint nvalue(required_distinct, assignment);

solve
  :: int_search(assignment, input_order, indomain_min, complete)
  satisfy;
