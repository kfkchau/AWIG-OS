"""T-CORE-MIGRATED(memory) [design 28 §I3, EP-04]: the memory core leaves code.

AMEND-BUDGET / MEM-GRANT / MEM-PROTECT / MEM-EVICT are op_definition records the generic
interpreter runs — no Python handler. Proof: the handler-registration function and the
`_resident` helper are gone; the ops are records; AMEND-BUDGET stays LAW with a byte-identical
payload; eviction still embeds its evidence; and a rebuild from the record reproduces identical
behaviour, including the doc-22 property (a fault records nothing).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import subsystems.memory as memory  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from subsystems.memory import MemoryView  # noqa: E402


class TestMemoryMigrated(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")

    def test_the_python_handler_and_resident_helper_are_gone(self):
        self.assertFalse(hasattr(memory, "register_memory_ops"))
        self.assertFalse(hasattr(memory, "_resident"))  # the aggregate now lives in the check

    def test_ops_are_definition_records_in_the_registry(self):
        store, gate, views = build_kernel(self.record)
        for op in ("AMEND-BUDGET", "MEM-GRANT", "MEM-PROTECT", "MEM-EVICT"):
            self.assertIn(op, views.op_definitions())
            self.assertTrue(gate.has(op))

    def test_amend_budget_payload_stays_law_byte_identical(self):
        store, gate, views = build_kernel(self.record)
        rec = gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 100})
        p = rec["payload"]
        self.assertEqual(p["rule_id"], "law:mem-budget:web")   # derived per-holder
        self.assertEqual(p["policy_key"], "budget:web")
        self.assertEqual(p["value"], 100)                       # aliased ceiling, numeric
        self.assertEqual(p["holder"], "web")
        self.assertEqual(p["ceiling"], 100)
        self.assertEqual(views.policy_value("budget:web"), 100)  # and it reads back as law

    def test_evict_still_embeds_evidence_via_the_interpreter(self):
        store, gate, views = build_kernel(self.record)
        gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10, "holder": "web"})
        default = {"aggregate": "access-freq", "value": "cold", "coverage": "sampled"}
        ev = gate.execute("MEM-EVICT", "web", {"region": "r1"})       # no evidence supplied
        self.assertEqual(ev["evidence_summary"], default)            # absent -> default
        empty = gate.execute("MEM-EVICT", "web", {"region": "r1", "evidence": {}})
        self.assertEqual(empty["evidence_summary"], default)         # falsy -> default (reproduces old)
        supplied = gate.execute("MEM-EVICT", "web", {"region": "r1", "evidence": {"why": "oom"}})
        self.assertEqual(supplied["evidence_summary"], {"why": "oom"})  # supplied wins

    def test_rebuild_from_record_is_behaviour_identical(self):
        store, gate, views = build_kernel(self.record)
        gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10, "holder": "web", "prot": "rw"})
        gate.execute("MEM-PROTECT", "web", {"region": "r1", "prot": "r"})
        before = MemoryView(store).mappings()

        store2, gate2, views2 = build_kernel(self.record)            # rebuild from the record alone
        self.assertIn("MEM-GRANT", views2.op_definitions())
        self.assertEqual(MemoryView(store2).mappings(), before)
        # the doc-22 property survives the migration: the fault path is the view, records nothing
        n = len(store2.all())
        for _ in range(1000):
            self.assertTrue(MemoryView(store2).fault("r1"))
        self.assertEqual(len(store2.all()), n)


if __name__ == "__main__":
    unittest.main()
