include "nvalue.mzn";

int: n;
int: queens;
int: square_count = n * n;
set of int: squares = 1..square_count;

function int: row(int: square) = (square - 1) div n;
function int: column(int: square) = (square - 1) mod n;

array[squares] of set of int: dominators = [
  {
    candidate
    | candidate in squares where
      row(candidate) = row(square) \/
      column(candidate) = column(square) \/
      abs(row(candidate) - row(square)) =
        abs(column(candidate) - column(square))
  }
  | square in squares
];

% The value selected for a square is a queen that dominates it. Restricting
% the number of distinct selected values restricts the number of queens.
array[squares] of var squares: dominating_queen;
constraint forall(square in squares)(
  dominating_queen[square] in dominators[square]
);
constraint nvalue(queens, dominating_queen);

solve
  :: int_search(dominating_queen, dom_w_deg, indomain_min, complete)
  satisfy;
