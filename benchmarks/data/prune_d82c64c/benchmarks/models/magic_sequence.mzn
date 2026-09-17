int: n;
set of int: value = 0..n - 1;

% This one-hot formulation avoids reified integer equalities, which Prune's
% FlatZinc adapter does not yet support.
array[value, value] of var 0..1: selected;
array[value] of var value: sequence;

constraint forall(position in value)(
  sum(candidate in value)(selected[position, candidate]) = 1
);
constraint forall(position in value)(
  sequence[position] =
    sum(candidate in value)(candidate * selected[position, candidate])
);
constraint forall(candidate in value)(
  sequence[candidate] =
    sum(position in value)(selected[position, candidate])
);

constraint sum(position in value)(sequence[position]) = n;
constraint sum(position in value)(position * sequence[position]) = n;

solve satisfy;
