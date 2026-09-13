"""Contract test for the record (L0). This IS the store contract (seam S1):
the round-trip proof and the append-only guarantees, executable.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import EventStore  # noqa: E402


class TestStore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")

    def test_append_mints_seq_and_time(self):
        s = EventStore(self.path)
        r1 = s._append({"actor": "SYSTEM", "action": "CREATE-INFO", "object": "x"})
        r2 = s._append({"actor": "SYSTEM", "action": "CREATE-INFO", "object": "y"})
        self.assertEqual(r1["seq"], 1)
        self.assertEqual(r2["seq"], 2)
        self.assertIn("record_time", r1)
        self.assertLess(r1["seq"], r2["seq"])

    def test_seq_and_time_are_not_suppliable(self):
        # C6: seq and record_time are minted at append, never taken from the caller.
        s = EventStore(self.path)
        r = s._append({"actor": "SYSTEM", "action": "X", "seq": 999, "record_time": "FAKE"})
        self.assertEqual(r["seq"], 1)
        self.assertNotEqual(r["record_time"], "FAKE")

    def test_no_mutate_path(self):
        # C1: no update/delete path exists in code.
        s = EventStore(self.path)
        self.assertFalse(hasattr(s, "update"))
        self.assertFalse(hasattr(s, "delete"))

    def test_asof_replay(self):
        s = EventStore(self.path)
        for i in range(5):
            s._append({"actor": "SYSTEM", "action": "X", "object": str(i)})
        self.assertEqual(len(s.all()), 5)
        self.assertEqual(len(s.all(as_of_seq=3)), 3)
        self.assertEqual([e["object"] for e in s.all(as_of_seq=2)], ["0", "1"])

    def test_round_trip_diff_is_empty(self):
        # THE standing proof (round-trip law, design 02 §1.3): delete every derived
        # cache, replay, reconstruct identically. A fresh instance from the same file
        # rebuilds the derived index from the log alone.
        s1 = EventStore(self.path)
        for i in range(10):
            s1._append({"actor": "SYSTEM", "action": "A" if i % 2 else "B", "object": str(i)})
        s2 = EventStore(self.path)  # reload: caches rebuilt from scratch
        self.assertEqual(s1.all(), s2.all())                    # the record replays identically
        self.assertEqual(s1.by_action("A"), s2.by_action("A"))  # the derived index reconstructs identically
        self.assertEqual(s1.by_action("B"), s2.by_action("B"))

    def test_persistence_is_the_jsonl_log(self):
        s1 = EventStore(self.path)
        s1._append({"actor": "SYSTEM", "action": "X", "object": "persisted"})
        s2 = EventStore(self.path)
        self.assertEqual(s2.all()[0]["object"], "persisted")
        with open(self.path) as f:
            lines = [ln for ln in f.read().split("\n") if ln]
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["object"], "persisted")


if __name__ == "__main__":
    unittest.main()
