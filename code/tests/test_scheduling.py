"""Scheduling core test (design 03 §4.1): runnable set derived, halt state, kill removes,
and why-did-this-run answerable — the audit a conventional scheduler cannot give."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from subsystems.scheduling import SchedulingView  # noqa: E402


class TestScheduling(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)  # sched ops arrive via genesis (EP-05)
        self.sv = SchedulingView(self.store)

    def test_admit_deschedule_kill(self):
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p1"})
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p2"})
        self.assertEqual(set(self.sv.runnable()), {"p1", "p2"})
        self.gate.execute("DESCHEDULE", "SYSTEM", {"proc": "p1", "cause": "wait-io"})
        self.assertEqual(set(self.sv.runnable()), {"p2"})
        self.gate.execute("SCHED-KILL", "SYSTEM", {"proc": "p2", "reason": "policy"})
        self.assertEqual(set(self.sv.runnable()), set())

    def test_priority_and_halt(self):
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p1", "priority": "normal"})
        self.gate.execute("SET-PRIORITY", "SYSTEM", {"proc": "p1", "priority": "high"})
        self.assertEqual(self.sv.runnable()["p1"]["priority"], "high")
        self.gate.execute("SCHED-HALT", "owner", {"reason": "brake"})
        self.assertIsNotNone(self.sv.halted())
        self.gate.execute("SCHED-RESUME", "owner", {})
        self.assertIsNone(self.sv.halted())

    def test_why_ran_is_answerable(self):
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p1", "wake_cause": "io-completion:88f0"})
        w = self.sv.why_ran("p1")
        self.assertEqual(w["rule_cited"], "SCHED-LAW-ADMIT")
        self.assertEqual(w["wake_cause"], "io-completion:88f0")  # the audit Linux loses a tick later

    def test_dispatch_records_nothing_and_round_trip(self):
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p1"})
        n = len(self.store.all())
        for _ in range(1000):
            _ = self.sv.runnable()  # dispatch reads the derived queue; records nothing
        self.assertEqual(len(self.store.all()), n)
        store2, gate2, views2 = build_kernel(self.record)
        self.assertEqual(self.sv.runnable(), SchedulingView(store2).runnable())


if __name__ == "__main__":
    unittest.main()
