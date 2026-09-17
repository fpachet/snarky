int: treatments;
int: blocks;
int: replication;
int: block_size;
int: pair_occurrence;
set of int: treatment = 1..treatments;
set of int: block = 1..blocks;
int: treatment_pairs = treatments * (treatments - 1) div 2;
set of int: treatment_pair = 1..treatment_pairs;

array[treatment, block] of var 0..1: design;
array[treatment_pair] of int: pair_left =
  [left | left in treatment, right in treatment where left < right];
array[treatment_pair] of int: pair_right =
  [right | left in treatment, right in treatment where left < right];
array[treatment_pair, block] of var 0..1: together;

constraint forall(t in treatment)(
  sum(b in block)(design[t, b]) = replication
);
constraint forall(b in block)(
  sum(t in treatment)(design[t, b]) = block_size
);
constraint forall(pair in treatment_pair, b in block)(
  together[pair, b] <= design[pair_left[pair], b] /\
  together[pair, b] <= design[pair_right[pair], b] /\
  design[pair_left[pair], b] + design[pair_right[pair], b]
    - together[pair, b] <= 1
);
constraint forall(pair in treatment_pair)(
  sum(b in block)(together[pair, b]) = pair_occurrence
);

% Choose canonical first row and column under treatment/block permutations.
constraint forall(t in 1..block_size)(design[t, 1] = 1);
constraint forall(t in block_size + 1..treatments)(design[t, 1] = 0);
constraint forall(b in 1..replication)(design[1, b] = 1);
constraint forall(b in replication + 1..blocks)(design[1, b] = 0);

solve satisfy;
