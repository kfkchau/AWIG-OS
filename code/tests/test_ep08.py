"""EP-08 — masters as records + the standing push v1 (design 28 §6, §I4).

T-MASTERS-AS-RECORDS: the five masters + two registries are SEEDED view-definition records that BIND
  to S-plane folds; the one engine (views.master) executes them; they round-trip; an unknown fold is
  refused at creation; masters keep the DICT trigger shape (never executable-law LIST triggers).
T-PUSH-DELIVERS: an on-append worker delivers matches to per-channel queues, APPENDING NOTHING
  (the flood boundary); views.queues() is the derivation the worker accelerates; kill the queues and
  replay from the record rebuilds them identically; delivery is forward-only (each NEW record).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.push import StandingPush  # noqa: E402
from kernel.errors import OpError  # noqa: E402

MASTERS = {"rule-master": "active_rules", "actor-master": "actors", "resource-master": "resources",
           "permission-master": "permissions", "relationship-master": "relationships",
           "op-registry": "op_definitions", "view-registry": "view_definitions"}


def _trivial(gate, action):
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x", "rule_cited": "ROOT-NEG-5"})


class TestMastersAsRecords(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_masters_are_seeded_view_definition_records_bound_to_folds(self):
        vdefs = self.views.view_definitions()
        for name, fold in MASTERS.items():
            self.assertIn(name, vdefs)
            self.assertEqual(vdefs[name]["bind"], fold)     # a record naming a fold
            self.assertEqual(vdefs[name]["tier"], "owner")  # the cores' precedent (genesis-only)

    def test_the_one_engine_executes_each_master_and_it_equals_the_fold(self):
        self.assertIn("CONST-SYSTEM-FUNCTION", self.views.master("rule-master")["value"])   # the fifth const law
        self.assertEqual(set(self.views.master("actor-master")["value"]), {"SYSTEM", "owner"})
        self.assertIn("MEM-GRANT", self.views.master("op-registry")["value"])               # cores in the registry
        # a master's value IS its bound fold — no separate derivation, no drift
        self.assertEqual(self.views.master("rule-master")["value"], self.views.active_rules())
        self.assertEqual(self.views.master("view-registry")["value"], self.views.view_definitions())

    def test_masters_keep_a_dict_trigger_never_a_list(self):
        for d in self.views.view_definitions().values():
            if d.get("bind"):
                self.assertNotIsInstance(d["when"], (list, tuple))   # DICT side: not executable law

    def test_master_carries_staleness_metadata(self):
        rm = self.views.master("rule-master")
        self.assertIn("derived_at", rm)      # the store version it reflects
        self.assertIn("refresh", rm)         # a refresh mandate (None unless set)

    def test_a_view_can_carry_a_refresh_mandate(self):
        self.gate.execute("CREATE-VIEW", "owner", {"name": "watched", "bind": "actors", "refresh": "hourly"})
        self.assertEqual(self.views.master("watched")["refresh"], "hourly")

    def test_unknown_fold_bind_is_refused_at_creation(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-VIEW", "owner", {"name": "bad", "bind": "no-such-fold"})
        self.assertEqual(cm.exception.rule, "AR-2")
        self.assertNotIn("bad", self.views.view_definitions())         # nothing written

    def test_masters_round_trip_from_the_record_alone(self):
        # kill everything derived: rebuild a fresh kernel and the masters come back, execute identically
        store2, gate2, views2 = build_kernel(self.path)
        bound2 = {n for n, d in views2.view_definitions().items() if d.get("bind")}
        self.assertTrue(set(MASTERS).issubset(bound2))
        self.assertEqual(views2.master("op-registry")["value"], self.views.master("op-registry")["value"])

    def test_master_views_are_conserved_the_deliberate_flip(self):
        # THE FLIP (EP-08B B2): the EP-08 review RULED that conservation protects master views (was the
        # pre-08B openness this test used to document). A non-owner superseding a master now REFUSES and
        # the master is intact; the OWNER amends in place, tier conserved. (Full both-direction coverage
        # lives in tests/test_ep08b.py; this locks that the flip happened.)
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-VIEW", "carol", {"name": "actor-master", "bind": "resources"})
        self.assertEqual(self.views.view_definitions()["actor-master"]["tier"], "owner")      # not demoted
        self.gate.execute("CREATE-VIEW", "owner", {"name": "actor-master", "bind": "resources"})  # the owner may
        self.assertEqual(self.views.view_definitions()["actor-master"]["bind"], "resources")  # amendment took effect
        self.assertEqual(self.views.view_definitions()["actor-master"]["tier"], "owner")      # tier conserved


class TestStandingPush(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        self.push = StandingPush(self.store, self.views)   # the worker, wired after genesis (no move-to views there)
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "frob-watch", "when": {"action": "FROB"}, "then": {"move_to": "frob-inbox"}})
        _trivial(self.gate, "FROB")

    def test_delivery_appends_nothing_and_runs_at_governance_rate(self):
        before = len(self.store.all())
        self.gate.execute("FROB", "alice", {})
        # exactly ONE record appended — the FROB decision. The worker's delivery appended NOTHING
        # (the flood boundary: a delivery-record would make this +2 and would recurse on_append).
        self.assertEqual(len(self.store.all()) - before, 1)
        self.gate.execute("FROB", "bob", {})
        self.assertEqual(len(self.push.channels()["frob-inbox"]), 2)     # both delivered to the channel

    def test_the_worker_queue_equals_the_derived_queue(self):
        self.gate.execute("FROB", "alice", {})
        self.gate.execute("FROB", "bob", {})
        worker = [r["seq"] for r in self.push.channels()["frob-inbox"]]
        derived = [r["seq"] for r in self.views.queues()["frob-inbox"]]
        self.assertEqual(worker, derived)              # the in-memory queue is exactly views.queues()

    def test_kill_the_queues_replay_rebuilds_identically(self):
        self.gate.execute("FROB", "alice", {})
        self.gate.execute("FROB", "bob", {})
        before = {c: [r["seq"] for r in rs] for c, rs in self.views.queues().items()}
        # kill EVERYTHING derived — a fresh kernel from the record file alone (no worker, no memo)
        store2, gate2, views2 = build_kernel(self.path)
        after = {c: [r["seq"] for r in rs] for c, rs in views2.queues().items()}
        self.assertEqual(before, after)                # identical channels + membership from the record
        self.assertEqual(before["frob-inbox"], [r["seq"] for r in self.push.channels()["frob-inbox"]])

    def test_delivery_is_forward_only_no_backfill(self):
        # a record recorded BEFORE the view existed is NOT delivered; only NEW matches are (design §6)
        _trivial(self.gate, "GLIP")
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "glip-watch", "when": {"action": "GLIP"}, "then": {"move_to": "glip-inbox"}})
        # frob-watch already exists from setUp; add an EARLY glip before... actually glip-watch is now live,
        # so record one before AND after a LATER view to prove forward-only cleanly:
        self.gate.execute("GLIP", "before", {})
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "glip-watch2", "when": {"action": "GLIP"}, "then": {"move_to": "glip-inbox2"}})
        self.gate.execute("GLIP", "after", {})
        self.assertEqual([r["actor"] for r in self.views.queues().get("glip-inbox2", [])], ["after"])
        self.assertEqual([r["actor"] for r in self.push.channels().get("glip-inbox2", [])], ["after"])


if __name__ == "__main__":
    unittest.main()
