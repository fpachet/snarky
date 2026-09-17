include "all_different.mzn";

int: order = 3;
int: size = order * order;
set of int: cell = 1..size;
array[cell, cell] of 0..size: clues;
array[cell, cell] of var 1..size: grid;

constraint forall(row in cell)(
  all_different([grid[row, column] | column in cell])
);
constraint forall(column in cell)(
  all_different([grid[row, column] | row in cell])
);
constraint forall(block_row, block_column in 0..order - 1)(
  all_different([
    grid[block_row * order + row, block_column * order + column]
    | row, column in 1..order
  ])
);
constraint forall(row, column in cell where clues[row, column] > 0)(
  grid[row, column] = clues[row, column]
);

solve satisfy;
