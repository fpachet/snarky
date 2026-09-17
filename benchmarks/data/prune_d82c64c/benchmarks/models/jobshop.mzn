int: jobs;
int: tasks;
int: machines;
int: makespan;
int: operations = jobs * tasks;
set of int: operation = 1..operations;

array[operation] of 1..machines: machine;
array[operation] of int: duration;
array[operation] of var 0..makespan: start;

int: resource_pair_count =
  sum(a, b in operation where a < b /\ machine[a] = machine[b])(1);
set of int: resource_pair = 1..resource_pair_count;
array[resource_pair] of int: resource_left =
  [a | a, b in operation where a < b /\ machine[a] = machine[b]];
array[resource_pair] of int: resource_right =
  [b | a, b in operation where a < b /\ machine[a] = machine[b]];
array[resource_pair] of var 0..1: left_before_right;

constraint forall(op in operation)(start[op] + duration[op] <= makespan);
constraint forall(job in 1..jobs, task in 1..tasks - 1)(
  let {
    int: current = (job - 1) * tasks + task,
    int: next = current + 1
  } in
    start[current] + duration[current] <= start[next]
);

% A zero chooses left-before-right; a one chooses right-before-left.
constraint forall(pair in resource_pair)(
  let {
    int: a = resource_left[pair],
    int: b = resource_right[pair]
  } in
    start[a] - start[b] - makespan * left_before_right[pair]
      <= -duration[a] /\
    start[b] - start[a] + makespan * left_before_right[pair]
      <= makespan - duration[b]
);

solve satisfy;
