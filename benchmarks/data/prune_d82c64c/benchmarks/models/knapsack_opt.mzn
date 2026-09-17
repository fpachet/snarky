int: items;
int: capacity;
set of int: item = 1..items;
array[item] of int: weight;
array[item] of int: value;

array[item] of var 0..1: selected;
var 0..sum(value): objective;

constraint sum(i in item)(weight[i] * selected[i]) <= capacity;
constraint objective = sum(i in item)(value[i] * selected[i]);

solve
  :: int_search(selected, first_fail, indomain_max, complete)
  maximize objective;
