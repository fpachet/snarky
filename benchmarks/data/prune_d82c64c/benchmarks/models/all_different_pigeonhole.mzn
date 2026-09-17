include "all_different.mzn";

int: n;
int: hole_count;
bool: use_global;
set of int: pigeons = 1..n;
set of int: holes = 1..hole_count;
array[pigeons] of var holes: assignment;

constraint if use_global then
  all_different(assignment)
else
  forall(left, right in pigeons where left < right)(
    assignment[left] != assignment[right]
  )
endif;

solve :: int_search(assignment, input_order, indomain_min, complete) satisfy;
