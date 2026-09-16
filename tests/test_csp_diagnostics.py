"""Diagnostic subprocesses preserve partial evidence and never invent proofs."""

import json
import sys

import pytest

from benchmarks.csp_followup import BASE, ROOT, read_progress
from benchmarks.prune_comparison import run


def test_partial_last_record_is_retained_as_truncation_not_a_result():
    event = '{"event":"search","nodes":2}\n'
    assert read_progress(event) == ([{"event": "search", "nodes": 2}], False)
    assert read_progress(event + '{"event":') == (
        [{"event": "search", "nodes": 2}],
        True,
    )
    with pytest.raises(json.JSONDecodeError):
        read_progress(event + "{broken}\n")


def test_worker_node_limit_has_flushed_progress_and_a_truthful_final_result():
    record = run(
        [
            sys.executable,
            ROOT / "benchmarks/csp_diagnostics.py",
            "--model",
            BASE / "artifacts/optimization--knapsack_20_opt.fzn.json",
            "--diagnostic",
            "--nodes",
            "1",
        ],
        seconds=15,
    )
    assert record["returncode"] == 0 and not record["timed_out"]
    result = json.loads(record["stdout"])
    progress = [json.loads(line) for line in record["stderr"].splitlines()]
    assert result["nodes"] == 1 and not result["complete"]
    assert result["termination"] == "node_limit" and result["status"] == "unknown"
    assert result["families"]["LinearSumConstraint"]["attempts"] > 0
    assert progress[0]["event"] == "construction_start"
    assert progress[-1]["progress"]["event"] == "finished"


def test_external_kill_retains_progress_without_a_completion_record():
    program = """
import json,time,sys
from snarky import Atom,Number
from snarky.finite import FiniteModel,FiniteVariable,solve
model=FiniteModel('kill',(FiniteVariable(Atom('x'),(Number(0),Number(1))),),())
def observe(event):
    print(json.dumps({'event':event.event,'nodes':event.explored_nodes,'result':None}),file=sys.stderr,flush=True)
    time.sleep(60)
solve(model,on_progress=observe)
"""
    record = run([sys.executable, "-c", program], seconds=2)
    assert record["timed_out"] and record["returncode"] != 0
    events = [json.loads(line) for line in record["stderr"].splitlines()]
    assert events and events[0]["event"] == "start"
    assert all(e["result"] is None for e in events)
    assert record["stdout"] == ""
