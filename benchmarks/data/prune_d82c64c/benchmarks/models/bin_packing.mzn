int: items;
int: bins;
int: capacity;
set of int: item = 1..items;
set of int: bin = 1..bins;
array[item] of 1..capacity: weight;

array[item, bin] of var 0..1: packed;
array[bin] of var 0..capacity: load;

constraint forall(i in item)(sum(b in bin)(packed[i, b]) = 1);
constraint forall(b in bin)(
  load[b] = sum(i in item)(weight[i] * packed[i, b])
);

% Identical bins are interchangeable.
constraint packed[1, 1] = 1;

solve satisfy;
