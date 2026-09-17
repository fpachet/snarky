int: items;
int: bins;
int: capacity;
set of int: item = 1..items;
set of int: bin = 1..bins;
array[item] of 1..capacity: weight;

array[item, bin] of var 0..1: packed;
array[bin] of var 0..capacity: load;
array[bin] of var 0..1: used;
var 0..bins: objective;

constraint forall(i in item)(sum(b in bin)(packed[i, b]) = 1);
constraint forall(b in bin)(
  load[b] = sum(i in item)(weight[i] * packed[i, b])
);
constraint forall(i in item, b in bin)(packed[i, b] <= used[b]);
constraint objective = sum(b in bin)(used[b]);

% Remove interchangeable-bin symmetries.
constraint used[1] = 1;
constraint forall(b in 1..bins - 1)(used[b] >= used[b + 1]);
constraint packed[1, 1] = 1;

solve
  :: seq_search([
    int_search(array1d(packed), first_fail, indomain_max, complete),
    int_search(used, input_order, indomain_min, complete)
  ])
  minimize objective;
