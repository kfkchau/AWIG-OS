"""EP-10 — metabolism gauge + paper-tiger view (design 28 §8), plus the carried R28 brake-authority fix.

R28: three brake acts the system will not honour must REFUSE (cited + recorded), never be accepted
  as clean no-op decisions — HALT-WATCHER on SYSTEM, HALT-WATCHER on owner, RESOLVE-WATCHER by a
  non-owner all refuse BOOT-INT (the R18 doctrine).
T-METABOLISM: law intake vs retirement per kind, windowed over RECORD-TIME (seq/ticks, never wall
  clock) — a pure derivation routed to the owner queue, appending nothing.
T-PAPER-TIGER: mandated views (a refresh mandate) with no recorded servicing — a pure derivation.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402


class TestR28BrakeAuthorityRefuses(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_braking_system_refuses_and_is_not_accepted(self):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("HALT-WATCHER", "bob", {"watcher": "SYSTEM"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)   # recorded refusal
        self.assertEqual(self.store.by_action("HALT-WATCHER"), [])              # NOT an accepted no-op

    def test_braking_owner_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("HALT-WATCHER", "bob", {"watcher": "owner"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.store.by_action("HALT-WATCHER"), [])

    def test_non_owner_resolve_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RESOLVE-WATCHER", "bob", {"watcher": "wanda"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.store.by_action("RESOLVE-WATCHER"), [])

    def test_effect_unchanged_the_owner_still_brakes_and_resolves(self):
        # the legitimate path still works: bob brakes a real watcher, the owner resolves
        self.gate.execute("HALT-WATCHER", "bob", {"watcher": "wanda"})
        self.assertIn("wanda", self.views.halted_watchers())
        self.gate.execute("RESOLVE-WATCHER", "owner", {"watcher": "wanda"})
        self.assertNotIn("wanda", self.views.halted_watchers())


def _trivial(gate, action):
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x", "rule_cited": "ROOT-NEG-5"})

_ORD_OP = {"law_cited": "SOP", "object_param": "x", "params": {"x": "required"},
           "structural_params": ["x"], "checks": []}   # x is the object id, inline (vocab door)


class TestMetabolism(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_intake_vs_retirement_per_kind_windowed_over_record_time(self):
        since = len(self.store.all())     # window floor: only records AFTER genesis
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "R1", "policy_key": "k", "value": 1})
        self.gate.execute("CREATE-OP", "owner", {"name": "OP1", "definition": _ORD_OP})
        self.gate.execute("CREATE-VIEW", "owner", {"name": "v1", "when": {"action": "FROB"}, "then": {"move_to": "inbox"}})
        self.gate.execute("RETIRE-OP", "owner", {"name": "OP1"})            # an op retires
        m = self.views.metabolism(since_seq=since)["per_kind"]
        self.assertEqual((m["rule"]["intake"], m["rule"]["retire"]), (1, 0))
        self.assertEqual((m["op"]["intake"], m["op"]["retire"], m["op"]["net"]), (1, 1, 0))
        self.assertEqual((m["view"]["intake"], m["view"]["retire"]), (1, 0))

    def test_the_gauge_is_record_time_only_never_the_wall_clock(self):
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "R1", "policy_key": "k", "value": 1})
        self.assertEqual(self.views.metabolism(), self.views.metabolism())   # deterministic on the record
        self.assertEqual(self.views.metabolism()["record_time_now"], 0)      # no ticks -> record-time 0
        self.gate.execute("TICK", "clock", {"now": 42})
        self.assertEqual(self.views.metabolism()["record_time_now"], 42)     # the recorded tick clock, not wall time


class TestPaperTiger(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_a_mandated_view_that_delivered_nothing_is_a_paper_tiger(self):
        self.gate.execute("CREATE-VIEW", "owner", {"name": "idle", "when": {"action": "FROB"},
                                                   "then": {"move_to": "idle-inbox"}, "refresh": "hourly"})
        self.assertIn("idle", {t["name"] for t in self.views.paper_tigers()})

    def test_a_serviced_mandated_view_is_not_a_paper_tiger(self):
        self.gate.execute("CREATE-VIEW", "owner", {"name": "busy", "when": {"action": "FROB"},
                                                   "then": {"move_to": "busy-inbox"}, "refresh": "hourly"})
        _trivial(self.gate, "FROB")
        self.gate.execute("FROB", "x", {})                                   # a delivery -> serviced
        self.assertNotIn("busy", {t["name"] for t in self.views.paper_tigers()})

    def test_an_unmandated_view_is_never_a_paper_tiger(self):
        self.gate.execute("CREATE-VIEW", "owner", {"name": "no-mandate", "when": {"action": "FROB"},
                                                   "then": {"move_to": "inbox"}})   # no refresh mandate
        self.assertNotIn("no-mandate", {t["name"] for t in self.views.paper_tigers()})
        self.assertEqual(self.views.paper_tigers(), [])                      # a fresh kernel has no mandated views


if __name__ == "__main__":
    unittest.main()
