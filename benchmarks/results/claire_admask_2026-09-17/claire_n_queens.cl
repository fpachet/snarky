// Common N-Queens benchmark for CLAIRE4 and Snarky.
//
// Derived from Yves Caseau's CLAIRE4 test/toys/queens.cl at commit
// 25b14968e1eef80269d56af418eda7d2ccd88cbf (Apache-2.0). This modified
// version makes the board size runtime-configurable and adds singleton
// propagation, validation of assigned conflicts, counters, and stable output.

MAX_N :: 16

BoardSize:integer := 8

column[n:(1 .. MAX_N)] : (0 .. MAX_N) := 0
possible[x:(1 .. MAX_N), y:(1 .. MAX_N)] : boolean := true
countPos[n:(1 .. MAX_N)] : (0 .. MAX_N) := MAX_N

// These tables participate in CLAIRE's hypothetical worlds.
store(column, possible, countPos)

BranchAttempts:integer := 0
FailedBranches:integer := 0
RuleFirings:integer := 0
CandidateRemovals:integer := 0

[forbid(x:(1 .. MAX_N), y:(1 .. MAX_N)) : void
  -> if (column[x] = y) contradiction!()
     else if (column[x] = 0 & possible[x,y])
       (possible[x,y] := false,
        countPos[x] :- 1,
        CandidateRemovals :+ 1,
        if (countPos[x] = 0) contradiction!())]

// Propagate row and diagonal conflicts after assigning a queen.
r1() :: rule(
  column[x] := z
  => (RuleFirings :+ 1,
      for y in ((1 .. BoardSize) but x) forbid(y,z)))

r2() :: rule(
  column[x] := z
  => (RuleFirings :+ 1,
      let d := x + z in
        for y in (max(1,d - BoardSize) .. min(d - 1,BoardSize))
          (if (y != x) forbid(y,d - y))))

r3() :: rule(
  column[x] := z
  => (RuleFirings :+ 1,
      let d := z - x in
        for y in (max(1,1 - d) .. min(BoardSize,BoardSize - d))
          (if (y != x) forbid(y,y + d))))

// Snarky's finite-domain engine materializes singleton assignments. Keep the
// common formulation aligned by doing the same in CLAIRE.
r4() :: rule(
  countPos[x] := n & n = 1 & column[x] = 0
  => (RuleFirings :+ 1,
      column[x] := some(y in (1 .. BoardSize) | possible[x,y])))

[tightest() : integer
  -> let smallest := BoardSize + 1, best := 0 in
       (for x in (1 .. BoardSize)
          (if (column[x] = 0 & countPos[x] < smallest)
             (best := x, smallest := countPos[x])),
        best)]

[try_position(q:(1 .. MAX_N), p:(1 .. MAX_N)) : boolean
  -> BranchAttempts :+ 1,
     let accepted := branch((column[q] := p, queens())) in
       (if not(accepted) FailedBranches :+ 1,
        accepted)]

[queens() : boolean
  -> let q := tightest() in
       (if (q = 0) true
        else exists(p in (1 .. BoardSize) |
               (possible[q,p] & try_position(q,p))))]

[benchmark(n:integer) : void
  -> if (n < 4 | n > MAX_N)
       error("board size must be in 4..~A",MAX_N),
     BoardSize := n,
     for x in (1 .. n) countPos[x] := n,
     BranchAttempts := 0,
     FailedBranches := 0,
     RuleFirings := 0,
     CandidateRemovals := 0,
     time_set(),
     let solved := queens(), elapsed := time_get(),
         solvedInt := (if solved 1 else 0) in
       (printf("SNARKY_CLAIRE_RESULT size=~A elapsed_ns=~A solved=~A",n,elapsed,solvedInt),
        printf(" branch_attempts=~A failed_branches=~A",BranchAttempts,FailedBranches),
        printf(" rule_firings=~A candidate_removals=~A solution=",RuleFirings,CandidateRemovals),
        for x in (1 .. n)
          (if (x > 1) princ(","),
           princ(column[x])),
        princ("\n"),
        exit(0))]
