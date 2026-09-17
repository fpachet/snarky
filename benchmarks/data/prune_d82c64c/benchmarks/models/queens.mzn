include "all_different.mzn";

int: n;
set of int: columns = 1..n;
array[columns] of var 1..n: queen_row;

constraint all_different(queen_row);
constraint all_different([queen_row[column] + column | column in columns]);
constraint all_different([queen_row[column] - column | column in columns]);
constraint queen_row[1] < queen_row[n];

solve satisfy;
