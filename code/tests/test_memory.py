"""Memory core test (design 03 §4.2, doc 22): budgets, mappings derived, eviction embeds
evidence, and the load-bearing property — a fault records NOTHING."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from subsystems.memory import MemoryView  # noqa: E402


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)  # memory ops arrive via genesis (EP-04)
        self.mv = MemoryView(self.store)

    def test_grant_within_budget_and_refuse_over(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 100})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 100, "holder": "web"})
        self.assertEqual(self.mv.resident_size("web"), 100)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("MEM-GRANT", "web", {"region": "r2", "size": 1, "holder": "web"})
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")

    def test_evict_removes_and_embeds_evidence(self):
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10, "holder": "web"})
        ev = self.gate.execute("MEM-EVICT", "web", {"region": "r1"})
        self.assertNotIn("r1", self.mv.mappings())
        self.assertIsNotNone(ev["evidence_summary"])  # audit-complete at the decision

    def test_fault_records_nothing(self):
        # THE doc-22 property: the hot path applies an already-recorded grant and records
        # nothing. 1000 faults -> 0 records.
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10, "holder": "web"})
        n = len(self.store.all())
        for _ in range(1000):
            self.assertTrue(self.mv.fault("r1"))
        self.assertEqual(len(self.store.all()), n)

    def test_protect_and_round_trip(self):
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10, "holder": "web", "prot": "rw"})
        self.gate.execute("MEM-PROTECT", "web", {"region": "r1", "prot": "r"})
        self.assertEqual(self.mv.mappings()["r1"]["prot"], "r")
        store2, gate2, views2 = build_kernel(self.record)
        self.assertEqual(self.mv.mappings(), MemoryView(store2).mappings())


if __name__ == "__main__":
    unittest.main()
