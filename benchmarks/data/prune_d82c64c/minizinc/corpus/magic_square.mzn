include "all_different.mzn";

set of int: indices = 1..3;
array[indices, indices] of var 1..9: square;

constraint all_different([square[row, column] | row, column in indices]);
constraint forall(row in indices)(
  sum(column in indices)(square[row, column]) = 15
);
constraint forall(column in indices)(
  sum(row in indices)(square[row, column]) = 15
);
constraint sum(index in indices)(square[index, index]) = 15;
constraint sum(index in indices)(square[index, 4 - index]) = 15;
constraint square[1, 1] < square[1, 3];

solve satisfy;
