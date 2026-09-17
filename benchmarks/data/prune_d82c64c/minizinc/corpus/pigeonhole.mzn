include "all_different.mzn";

array[1..4] of var 1..3: pigeon_to_hole;

constraint all_different(pigeon_to_hole);

solve satisfy;
