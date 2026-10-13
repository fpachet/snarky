// Common Snarky/CLAIRE combinatorial triangle-closure benchmark.
//
// Each group owns one hub, eight left nodes, and eight right nodes. The
// membership sets are prepared before timing. Adding each left -> right edge
// fires this rule, which searches the hubs and records the unique triangle.

TRIANGLE_WIDTH :: 8
TRIANGLE_MAX_GROUPS :: 100

TRIANGLE_NODE <: object(index:integer)
TRIANGLE_LEFT <: TRIANGLE_NODE(outgoing:set[TRIANGLE_NODE])
TRIANGLE_RIGHT <: TRIANGLE_NODE
TRIANGLE_HUB <: TRIANGLE_NODE(
    lefts:set[TRIANGLE_LEFT],
    rights:set[TRIANGLE_RIGHT])

(instanced(TRIANGLE_HUB))

TriangleLeft[g:(1 .. TRIANGLE_MAX_GROUPS), i:(1 .. TRIANGLE_WIDTH)] :
    TRIANGLE_LEFT := unknown
TriangleRight[g:(1 .. TRIANGLE_MAX_GROUPS), i:(1 .. TRIANGLE_WIDTH)] :
    TRIANGLE_RIGHT := unknown

TriangleRuleFirings:integer := 0
TriangleOutputs:integer := 0
TriangleChecksum:integer := 0

closeTriangle() :: rule(
  outgoing(left) :add right
  => (TriangleRuleFirings :+ 1,
      for hub in TRIANGLE_HUB
        (if (left % hub.lefts & right % hub.rights)
          (TriangleOutputs :+ 1,
           TriangleChecksum :+ hub.index))))

[benchmark(n:integer) : void
  -> if (n < 1 | n > TRIANGLE_MAX_GROUPS)
       error("group count must be in 1..~A",TRIANGLE_MAX_GROUPS),
     time_set(),
     for g in (1 .. n)
       let left_set := set<TRIANGLE_LEFT>(),
           right_set := set<TRIANGLE_RIGHT>() in
         (for i in (1 .. TRIANGLE_WIDTH)
            let node := TRIANGLE_LEFT(
                index = ((g - 1) * TRIANGLE_WIDTH + i)) in
              (TriangleLeft[g,i] := node, left_set :add node),
          for i in (1 .. TRIANGLE_WIDTH)
            let node := TRIANGLE_RIGHT(
                index = ((g - 1) * TRIANGLE_WIDTH + i)) in
              (TriangleRight[g,i] := node, right_set :add node),
          TRIANGLE_HUB(index = g, lefts = left_set, rights = right_set)),
     let preparation_ns := time_get() in
       (TriangleRuleFirings := 0,
        TriangleOutputs := 0,
        TriangleChecksum := 0,
        time_set(),
        for g in (1 .. n)
          for i in (1 .. TRIANGLE_WIDTH)
            for j in (1 .. TRIANGLE_WIDTH)
              outgoing(TriangleLeft[g,i]) :add TriangleRight[g,j],
        let inference_ns := time_get() in
          (printf(
            "SNARKY_CLAIRE_TRIANGLE_RESULT groups=~S width=~S preparation_ns=~S inference_ns=~S rule_firings=~S outputs=~S checksum=~S\n",
            n,
            TRIANGLE_WIDTH,
            preparation_ns,
            inference_ns,
            TriangleRuleFirings,
            TriangleOutputs,
            TriangleChecksum),
           exit(0)))]
