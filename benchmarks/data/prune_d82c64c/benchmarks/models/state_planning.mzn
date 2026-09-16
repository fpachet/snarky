int: states;
int: transitions;
int: horizon;
int: start_state;
int: goal_state;
set of int: state = 1..states;
set of int: transition = 1..transitions;
set of int: step = 1..horizon;

array[transition] of state: source;
array[transition] of state: destination;
array[0..horizon, state] of var 0..1: at;
array[step, transition] of var 0..1: take;

constraint at[0, start_state] = 1;
constraint at[horizon, goal_state] = 1;
constraint forall(time in 0..horizon)(
  sum(node in state)(at[time, node]) = 1
);
constraint forall(time in step)(
  sum(edge in transition)(take[time, edge]) = 1
);
constraint forall(time in step, node in state)(
  sum(edge in transition where source[edge] = node)(take[time, edge])
    = at[time - 1, node]
);
constraint forall(time in step, node in state)(
  sum(edge in transition where destination[edge] = node)(take[time, edge])
    = at[time, node]
);

solve satisfy;
