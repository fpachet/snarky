// Common Snarky/CLAIRE version of CLAIRE4 test/rules/filter.cl.
//
// Frames are prepared before the inference timer. Each of ten positive slot
// assignments fires one independent rule and increments a counter from 3 to 4.

FilterFiringCount:integer := 0
FilterChecksum:integer := 0

FILTER_FRAME <: object(
       nc1:integer = 3,
       nc2:integer = 3,
       nc3:integer = 3,
       nc4:integer = 3,
       nc5:integer = 3,
       nc6:integer = 3,
       nc7:integer = 3,
       nc8:integer = 3,
       nc9:integer = 3,
       nc0:integer = 3,
       N1:integer = 0,
       N2:integer = 0,
       N3:integer = 0,
       N4:integer = 0,
       N5:integer = 0,
       N6:integer = 0,
       N7:integer = 0,
       N8:integer = 0,
       N9:integer = 0,
       N0:integer = 0)

a1() :: rule(
  N1(x) := y & y > 0 =>
    (nc1(x) := (nc1(x) + 1), FilterFiringCount :+ 1))
a2() :: rule(
  N2(x) := y & y > 0 =>
    (nc2(x) := (nc2(x) + 1), FilterFiringCount :+ 1))
a3() :: rule(
  N3(x) := y & y > 0 =>
    (nc3(x) := (nc3(x) + 1), FilterFiringCount :+ 1))
a4() :: rule(
  N4(x) := y & y > 0 =>
    (nc4(x) := (nc4(x) + 1), FilterFiringCount :+ 1))
a5() :: rule(
  N5(x) := y & y > 0 =>
    (nc5(x) := (nc5(x) + 1), FilterFiringCount :+ 1))
a6() :: rule(
  N6(x) := y & y > 0 =>
    (nc6(x) := (nc6(x) + 1), FilterFiringCount :+ 1))
a7() :: rule(
  N7(x) := y & y > 0 =>
    (nc7(x) := (nc7(x) + 1), FilterFiringCount :+ 1))
a8() :: rule(
  N8(x) := y & y > 0 =>
    (nc8(x) := (nc8(x) + 1), FilterFiringCount :+ 1))
a9() :: rule(
  N9(x) := y & y > 0 =>
    (nc9(x) := (nc9(x) + 1), FilterFiringCount :+ 1))
a0() :: rule(
  N0(x) := y & y > 0 =>
    (nc0(x) := (nc0(x) + 1), FilterFiringCount :+ 1))

[benchmark(n:integer) : void
 -> if (n < 1) error("frame count must be positive"),
    time_set(),
    let frames := list<FILTER_FRAME>{FILTER_FRAME() | i in (1 .. n)},
        preparation_ns := time_get() in
      (FilterFiringCount := 0,
       time_set(),
       for i in (1 .. n)
         let frame := frames[i] in
           (N1(frame) := i,
            N2(frame) := i,
            N3(frame) := i,
            N4(frame) := i,
            N5(frame) := i,
            N6(frame) := i,
            N7(frame) := i,
            N8(frame) := i,
            N9(frame) := i,
            N0(frame) := i),
       let inference_ns := time_get() in
         (FilterChecksum := 0,
          for frame in frames
            FilterChecksum :+
              (frame.nc1 + frame.nc2 + frame.nc3 + frame.nc4 + frame.nc5 +
               frame.nc6 + frame.nc7 + frame.nc8 + frame.nc9 + frame.nc0),
          printf(
            "SNARKY_CLAIRE_FILTER_RESULT size=~S preparation_ns=~S inference_ns=~S rule_firings=~S outputs=~S checksum=~S\n",
            n,
            preparation_ns,
            inference_ns,
            FilterFiringCount,
            FilterFiringCount,
            FilterChecksum),
          exit(0)))]
