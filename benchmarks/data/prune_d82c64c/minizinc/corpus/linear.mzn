var 0..3: x;
var 0..3: y;
var 0..3: z;

constraint 2 * x + y = 5;
constraint x < y;
constraint x != z;
constraint x + y + z <= 6;

solve satisfy;
