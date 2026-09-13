"""EP-09 — separation of powers, real (design 28 §7).

T-DUAL-BLIND: two mutually-blind audit streams digest the same governance referents independently;
  neither mirrors the other; a stream that disagrees (a tamper/collusion attempt) is caught by the
  third-party cross-check.
T-SOP-WIRED: the sop check refuses a maker reviewing its own object; a different actor passes.
T-BRAKE-WATCHER: a watched actor halts its watcher's ops (owner-resolvable); the record never goes
  dark (the brake and the refusals are recorded and mirrored).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.protection import Protection  # noqa: E402
from kernel.errors import OpError  # noqa: E402


class TestDualBlind(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        self.prot = Protection(self.store, self.gate, self.views)

    def _governance_act(self):
        with self.assertRaises(OpError):
            self.gate.execute("DO-NOTHING", "x", {})   # unknown op -> op-refused (a dual-audit action)

    def test_both_streams_mirror_independently_and_agree(self):
        self._governance_act()
        a = self.store.by_action("dual-audit-record")
        b = self.store.by_action("dual-audit-b-record")
        self.assertEqual((len(a), len(b)), (1, 1))                          # each stream mirrored once
        self.assertEqual(a[0]["payload"]["ref_seq"], b[0]["payload"]["ref_seq"])
        self.assertEqual(a[0]["payload"]["digest"], b[0]["payload"]["digest"])   # independent, but agree
        self.assertEqual(self.prot.dual_blind_divergences(), [])            # cross-check clean

    def test_streams_are_mutually_blind_neither_mirrors_the_other(self):
        self._governance_act()
        # neither stream mirrored the other's record (a mirror is not a governance action) — no cascade
        refs = [m["payload"]["ref_action"] for m in self.store.by_action("dual-audit-record")] \
            + [m["payload"]["ref_action"] for m in self.store.by_action("dual-audit-b-record")]
        self.assertNotIn("dual-audit-record", refs)
        self.assertNotIn("dual-audit-b-record", refs)
        self.assertEqual(len(self.store.by_action("dual-audit-record")), 1)
        self.assertEqual(len(self.store.by_action("dual-audit-b-record")), 1)

    def test_a_disagreeing_stream_cannot_hide_it_from_the_crosscheck(self):
        self._governance_act()
        ref_seq = self.store.by_action("dual-audit-record")[0]["payload"]["ref_seq"]
        # simulate a compromised stream-B writer forging a WRONG digest for the same referent. Because
        # B computed independently (it never read A), it cannot silently match A — the third-party
        # cross-check flags the disagreement. This is the whole point of mutual blindness.
        self.store._append({"actor": "SYSTEM", "action": "dual-audit-b-record", "rule_cited": "SOP",
                            "payload": {"ref_seq": ref_seq, "ref_action": "op-refused",
                                        "digest": "deadbeefdeadbeef", "stream": "dual-audit-b"}})
        self.assertIn(ref_seq, self.prot.dual_blind_divergences())


class TestSopWired(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_the_maker_may_not_review_its_own_object(self):
        self.gate.execute("CREATE-INFO", "alice", {"content": "doc-1"})   # alice mints the object
        with self.assertRaises(OpError) as cm:                            # alice reviewing her own -> refused
            self.gate.execute("REVIEW", "alice", {"object": "doc-1"})
        self.assertEqual(cm.exception.rule, "SOP")
        rec = self.gate.execute("REVIEW", "bob", {"object": "doc-1"})     # a different actor may review it
        self.assertEqual(rec["action"], "REVIEW")

    def test_creator_of_reads_the_minting_record(self):
        self.gate.execute("CREATE-INFO", "carol", {"content": "doc-2"})
        self.assertEqual(self.views.creator_of("doc-2"), "carol")
        self.assertIsNone(self.views.creator_of("never-minted"))

    def test_sop_is_a_known_check_but_an_unknown_check_still_refuses_at_creation(self):
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-OP", "owner", {"name": "BAD", "definition": {
                "law_cited": "SOP", "object_param": "x", "params": {"x": "required"},
                "checks": [{"check": "no-such-check"}]}})


def _trivial(gate, action):
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x", "rule_cited": "ROOT-NEG-5"})


class TestBrakeWatcher(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        self.prot = Protection(self.store, self.gate, self.views)   # so the brake's decisions get mirrored
        _trivial(self.gate, "WANDA-OP")

    def test_watched_brakes_watcher_only_owner_resolves_record_never_dark(self):
        self.gate.execute("HALT-WATCHER", "bob", {"watcher": "wanda"})     # bob brakes the watcher wanda
        self.assertIn("wanda", self.views.halted_watchers())
        # wanda's every op is now frozen -> refused WATCHER-BRAKE, RECORDED (the record never goes dark)
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("WANDA-OP", "wanda", {})
        self.assertEqual(cm.exception.rule, "WATCHER-BRAKE")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        # the HALT-WATCHER itself was audit-mirrored to BOTH blind streams — the brake records itself
        halt_seq = self.store.by_action("HALT-WATCHER")[0]["seq"]
        self.assertTrue(any(m["payload"]["ref_seq"] == halt_seq for m in self.store.by_action("dual-audit-record")))
        self.assertTrue(any(m["payload"]["ref_seq"] == halt_seq for m in self.store.by_action("dual-audit-b-record")))
        # a NON-owner cannot lift the halt — resolution is the OWNER's (R28: now REFUSED, not inert)
        with self.assertRaises(OpError) as cm2:
            self.gate.execute("RESOLVE-WATCHER", "bob", {"watcher": "wanda"})
        self.assertEqual(cm2.exception.rule, "BOOT-INT")
        self.assertIn("wanda", self.views.halted_watchers())   # still halted (the resolve was refused)
        # the owner resolves -> wanda unfrozen, acts again
        self.gate.execute("RESOLVE-WATCHER", "owner", {"watcher": "wanda"})
        self.assertNotIn("wanda", self.views.halted_watchers())
        self.assertEqual(self.gate.execute("WANDA-OP", "wanda", {})["action"], "WANDA-OP")

    def test_the_recorder_and_the_resolver_can_never_be_braked(self):
        # halting SYSTEM or owner would take the record dark / remove the resolver — R28: now REFUSED
        # BOOT-INT (was accepted-and-inert), the record honest. Full R28 coverage in test_ep10.py.
        for target in ("SYSTEM", "owner"):
            with self.assertRaises(OpError) as cm:
                self.gate.execute("HALT-WATCHER", "bob", {"watcher": target})
            self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.views.halted_watchers(), set())


if __name__ == "__main__":
    unittest.main()
