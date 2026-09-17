var bool: p;
var bool: q;
var 0..1: p_as_int;

constraint p \/ not q;
constraint p_as_int = bool2int(p);

solve satisfy;
