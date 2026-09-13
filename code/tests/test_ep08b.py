"""EP-08B — the two directed EP-08-review fixes (R26, R27).

B1 (R26): a LIVE StandingPush must equal views.queues() at every step across a definition amendment,
  WITHOUT being killed — the worker resets affected channels from the derivation on a CREATE-VIEW.
B2 (R27): conservation reaches master views. Superseding an owner-tier master is the OWNER's in-place
  amendment only (tier conserved, master live throughout); a non-owner supersession/demotion refuses
  and records; ordinary non-master views stay free (v1 unchanged).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.push import StandingPush  # noqa: E402
from kernel.errors import OpError  # noqa: E402


def _snap(channels):
    """Normalize channels/queues to {channel: [seqs]} (empty channels dropped) for comparison."""
    return {c: [r["seq"] for r in rs] for c, rs in channels.items() if rs}


def _trivial(gate, action):
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x", "rule_cited": "ROOT-NEG-5"})


class TestB1WorkerCoherenceAcrossAmendment(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        self.push = StandingPush(self.store, self.views)
        _trivial(self.gate, "FROB")

    def test_live_worker_equals_derivation_at_every_step(self):
        # the review's probe verbatim: define, deliver, AMEND, deliver — the live acceleration must
        # equal the derivation at every step, without killing the worker.
        self.gate.execute("CREATE-VIEW", "owner", {"name": "w", "when": {"action": "FROB"}, "then": {"move_to": "A"}})
        self.assertEqual(_snap(self.push.channels()), _snap(self.views.queues()))
        self.gate.execute("FROB", "x", {})
        self.gate.execute("FROB", "y", {})
        self.assertEqual(_snap(self.push.channels()), _snap(self.views.queues()))     # both {A: [.., ..]}
        # amend the move_to A -> B. The derivation (latest-def, forward-only) drops the old-channel
        # deliveries; the un-reset worker used to keep them (the acceleration lying).
        self.gate.execute("CREATE-VIEW", "owner", {"name": "w", "when": {"action": "FROB"}, "then": {"move_to": "B"}})
        self.assertEqual(_snap(self.push.channels()), _snap(self.views.queues()))     # THE CRUX: equal, un-killed
        self.gate.execute("FROB", "z", {})
        self.assertEqual(_snap(self.push.channels()), _snap(self.views.queues()))     # both {B: [z]}
        # deliveries still appended NOTHING — only the 3 FROBs and the 2 view defs are in the record
        self.assertEqual(len(self.store.by_action("FROB")), 3)


class TestB2ConservationReachesMasters(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_a_non_owner_superseding_a_master_refuses_and_records(self):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-VIEW", "alice", {"name": "rule-master", "bind": "actors"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)          # recorded
        # the master is intact — not demoted, still bound and executing
        d = self.views.view_definitions()["rule-master"]
        self.assertEqual((d["bind"], d["tier"]), ("active_rules", "owner"))
        self.assertIn("CONST-SYSTEM-FUNCTION", self.views.master("rule-master")["value"])

    def test_the_owner_redefines_a_master_tier_conserved_and_live_throughout(self):
        # the owner amends rule-master IN PLACE (add a refresh mandate). Succeeds; tier conserved; the
        # master is live at every point (view amendment is latest-wins — no down moment).
        self.assertIn("CONST-SYSTEM-FUNCTION", self.views.master("rule-master")["value"])   # live before
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "rule-master", "bind": "active_rules", "refresh": "hourly"})
        d = self.views.view_definitions()["rule-master"]
        self.assertEqual(d["tier"], "owner")            # tier CONSERVED across the owner's amendment
        self.assertEqual(d["refresh"], "hourly")        # the amendment took effect
        self.assertIn("CONST-SYSTEM-FUNCTION", self.views.master("rule-master")["value"])   # live after

    def test_an_explicit_lower_tier_supersession_of_a_master_is_refused(self):
        # create_view mints NO tier, so a demotion CLAIM can only arrive via a forge op emitting a
        # view_definition payload carrying a tier. Even the owner's explicit LOWER-tier supersession
        # refuses (tier is conserved, never restated downward); and the fold keeps the master owner
        # regardless (defense in depth, mirroring active_rules).
        self.gate.execute("CREATE-OP", "owner", {"name": "FORGE-VIEW", "definition": {
            "description": "forge a view_definition", "law_cited": "P4-REFUSE", "object_param": "name",
            "params": {"name": "required"}, "payload_from": ["name", "tier", "bind"],
            "structural_params": ["name"],   # object_param + payload_from => inline (vocab door)
            "payload_derive": {"kind": {"tpl": "view_definition"}}, "checks": []}})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("FORGE-VIEW", "owner", {"name": "rule-master", "tier": "ordinary", "bind": "active_rules"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.views.view_definitions()["rule-master"]["tier"], "owner")   # not demoted

    def test_ordinary_non_master_views_stay_free(self):
        # v1 unchanged: any actor creates and supersedes an ordinary (non-master) view
        self.gate.execute("CREATE-VIEW", "alice",
                          {"name": "my-view", "when": {"action": "FROB"}, "then": {"move_to": "inbox"}})
        self.assertEqual(self.views.view_definitions()["my-view"]["tier"], "ordinary")
        self.gate.execute("CREATE-VIEW", "bob",
                          {"name": "my-view", "when": {"action": "GLIP"}, "then": {"move_to": "inbox2"}})  # bob supersedes
        self.assertEqual(self.views.view_definitions()["my-view"]["then"]["move_to"], "inbox2")


if __name__ == "__main__":
    unittest.main()
