include "all_different.mzn";

int: n;
set of int: index = 1..n;
array[index, index] of var index: square;

constraint forall(row in index)(
  all_different([square[row, column] | column in index])
);
constraint forall(column in index)(
  all_different([square[row, column] | row in index])
);

% Remove the row/column permutation symmetry while leaving the remaining
% domains to narrow incrementally during search.
constraint forall(column in index)(square[1, column] = column);
constraint forall(row in index)(square[row, 1] = row);

solve :: int_search(
  [square[row, column] | row, column in index],
  input_order,
  indomain_min,
  complete
) satisfy;
