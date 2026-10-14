include "all_different.mzn";
int: n = 8;
int: m = n*(n*n+1) div 2;
array[1..n,1..n] of var 1..n*n: square;
constraint all_different(array1d(square)) :: domain;
constraint forall(r in 1..n)(sum(c in 1..n)(square[r,c]) = m);
constraint forall(c in 1..n)(sum(r in 1..n)(square[r,c]) = m);
constraint sum(i in 1..n)(square[i,i]) = m;
constraint sum(i in 1..n)(square[i,n+1-i]) = m;

constraint square[1,1] < square[1,n];
constraint square[1,1] < square[n,1];
constraint square[1,1] < square[n,n];
constraint square[1,n] < square[n,1];
constraint square[1,1] <= (n*n+1) div 2;

solve :: int_search(array1d(square), dom_w_deg, indomain_random, complete) satisfy;
output [show(array1d(square)), "\n"];
