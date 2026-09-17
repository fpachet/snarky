include "nvalue.mzn";

array[1..3] of var 1..3: values;
var 1..3: distinct;

constraint values[1] <= values[2];
constraint values[2] <= values[3];
constraint nvalue(distinct, values);

solve satisfy;
