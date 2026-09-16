include "all_different.mzn";

int: n;
set of int: index = 1..n;
int: magic_sum = n * (n * n + 1) div 2;
array[index, index] of var 1..n * n: square;

constraint all_different([square[row, column] | row, column in index]);
constraint forall(row in index)(
  sum(column in index)(square[row, column]) = magic_sum
);
constraint forall(column in index)(
  sum(row in index)(square[row, column]) = magic_sum
);
constraint sum(i in index)(square[i, i]) = magic_sum;
constraint sum(i in index)(square[i, n + 1 - i]) = magic_sum;

% Select one representative from the rotational/reflectional symmetries.
constraint square[1, 1] < square[1, n];
constraint square[1, 1] < square[n, 1];
constraint square[1, n] < square[n, 1];

solve satisfy;
