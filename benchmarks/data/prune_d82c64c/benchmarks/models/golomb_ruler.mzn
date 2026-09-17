include "all_different.mzn";

int: marks_count;
int: length;
set of int: marks_index = 1..marks_count;
int: distance_count = marks_count * (marks_count - 1) div 2;
set of int: distance_index = 1..distance_count;
array[1..8] of int: best_subruler_length = [0, 1, 3, 6, 11, 17, 25, 34];

constraint assert(
  marks_count <= 8,
  "the benchmark model needs another certified sub-ruler lower bound"
);

array[marks_index] of var 0..length: marks;
array[distance_index] of var 1..length: distances;
array[distance_index] of int: left =
  [i | i in marks_index, j in marks_index where i < j];
array[distance_index] of int: right =
  [j | i in marks_index, j in marks_index where i < j];

constraint marks[1] = 0;
constraint marks[marks_count] = length;
constraint forall(i in 1..marks_count - 1)(marks[i] < marks[i + 1]);
constraint forall(i, j in marks_index where i < j)(
  marks[j] - marks[i] >= best_subruler_length[j - i + 1]
);
constraint forall(k in distance_index)(
  distances[k] = marks[right[k]] - marks[left[k]]
);
constraint all_different(distances);

% Reflection symmetry.
constraint marks[2] - marks[1] < marks[marks_count] - marks[marks_count - 1];

solve satisfy;
