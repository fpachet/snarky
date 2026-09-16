int: variables;
int: horizon;
set of int: index = 1..variables;
array[index] of var 0..horizon: time;

constraint time[1] = 0;
constraint forall(i in 1..variables - 1)(
  time[i + 1] = time[i] + 1
);

solve satisfy;
