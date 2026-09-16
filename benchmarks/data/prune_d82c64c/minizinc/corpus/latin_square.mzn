include "all_different.mzn";

int: n = 3;
set of int: indices = 1..n;
array[indices, indices] of var indices: square;

constraint forall(row in indices)(
  all_different([square[row, column] | column in indices])
);
constraint forall(column in indices)(
  all_different([square[row, column] | row in indices])
);
constraint square[1, 1] = 1;

solve satisfy;
