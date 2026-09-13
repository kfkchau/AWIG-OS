"""EP-07B — the five EP-07-review fixes (R20-R24), reshaped by the power ruling (design/30).

B1  the UNTOUCHABLES FLOOR (design/30 §3): a minted full-form DON'T whose trigger is BLANKET over the
    rule-processing surface (a law-lifecycle act with no narrowing dimension, or a matches-everything
    trigger) refuses at the mint, BOOT-INT, for every actor including the owner — the brick class. A
    TARGETED don't (narrowing actor/object/another dimension) passes: the space-local class the
    interim heuristic approximates pre-spaces.
B2  firing evidence is the OUTCOME HAPPENING: an obligation counts fired only on a record whose action
    equals its then-op, carrying its ref, after its current version's seq (closes forge-silencing;
    re-arms on amendment; never twice per version).
B3  the obligation_ref stamp only touches a dict payload; a non-dict falls through to the AR-2 refusal.
B4  run_due records-and-continues past a refused firing; returns {fired, refused}.
B5  regression tests documenting the pre-spaces openness (targeted don't binding another actor mints
    and fires; anyone amends it away) — no fix, the power ruling withdrew the review's owner gate.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.obligations import due, run_due  # noqa: E402
from kernel.errors import OpError  # noqa: E402


def _dont(rule_id, when):
    return {"rule_id": rule_id, "polarity": "-", "when": when, "then": [{"refuse": rule_id}]}


def _trivial(gate, action):
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x", "rule_cited": "ROOT-NEG-5"})


class TestB1UntouchablesFloor(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_blanket_brick_on_create_rule_refuses_at_mint(self):
        # R20 brick probe verbatim: a blanket don't matching CREATE-RULE would refuse all rule-making
        # including its own amendment (the owner could not undo it). Refused at the mint, BOOT-INT.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice", _dont("law:brick", [{"action": "CREATE-RULE"}]))
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        # rule-making is NOT bricked — the mint never took effect
        self.gate.execute("CREATE-RULE", "alice", {"rule_id": "ok", "policy_key": "k", "value": 1})
        self.assertEqual(self.views.policy_value("k"), 1)

    def test_blanket_brick_refuses_even_for_the_owner(self):
        # an owner minting the brick is self-bricking; exit, not surgery. Refused for the owner too.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "owner", _dont("law:brick2", [{"action": "AMEND-OP"}]))
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_action_blind_matches_everything_refuses_at_mint(self):
        # a matches-everything trigger (a pattern with no dimensions) is blanket over the surface too
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice", _dont("law:all", [{}]))
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_targeted_dont_on_create_rule_mints_and_fires(self):
        # BOTH directions: a targeted don't (narrows actor) on CREATE-RULE ITSELF passes the floor,
        # mints, and fires — the space-local class ("alice may not write rules") the heuristic allows.
        self.gate.execute("CREATE-RULE", "owner",
                          _dont("no-alice-rules", [{"action": "CREATE-RULE", "actor": "alice"}]))
        self.gate.execute("CREATE-RULE", "bob", {"rule_id": "bobrule", "policy_key": "k", "value": 1})  # bob unaffected
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice", {"rule_id": "alicerule", "policy_key": "k2", "value": 2})
        self.assertEqual(cm.exception.rule, "no-alice-rules")   # the targeted don't fired

    def test_blanket_dont_on_a_non_lifecycle_act_is_allowed(self):
        # blocking a non-law act blanket does not reach rule-processing -> not an untouchables violation
        _trivial(self.gate, "FROB")
        self.gate.execute("CREATE-RULE", "owner", _dont("no-frob", [{"action": "FROB"}]))
        self.assertIn("no-frob", self.views.active_rules())
        with self.assertRaises(OpError) as cm:
            self.gate.execute("FROB", "alice", {})
        self.assertEqual(cm.exception.rule, "no-frob")


class TestB2FiringEvidence(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_a_forged_ref_on_the_wrong_act_no_longer_silences(self):
        # R21: fired-ness is now the OUTCOME HAPPENING (a record whose action == the then-op, carrying
        # the ref). The forger records a DIFFERENT act (WRITE-ACTIVITY, not the then-op SCHED-ADMIT)
        # with a forged ref — it no longer counts as firing, so the obligation still fires.
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "ob", "when": {"elapsed_since": 1}, "then": {"op": "SCHED-ADMIT", "params": {"proc": "p"}}})
        self.gate.execute("TICK", "clock", {"now": 5})
        self.gate.execute("WRITE-ACTIVITY", "alice", {"data": {"x": 1}, "obligation_ref": "ob"})  # the forge
        self.assertEqual([o["rule_id"] for o in due(self.store)], ["ob"])   # NOT silenced
        self.assertEqual(run_due(self.store, self.gate)["fired"], ["ob"])   # it fires

    def test_amended_obligation_re_arms_but_never_fires_twice_per_version(self):
        # R22: keyed to the CURRENT version's seq — an amendment re-arms; a version fires at most once.
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "ob", "when": {"elapsed_since": 1}, "then": {"op": "SCHED-ADMIT", "params": {"proc": "p"}}})
        self.gate.execute("TICK", "clock", {"now": 5})
        self.assertEqual(run_due(self.store, self.gate)["fired"], ["ob"])
        self.assertEqual(due(self.store), [])                              # fired (this version) — never twice
        # amend the obligation (same rule_id, latest-wins) -> a new version with a higher seq
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "ob", "when": {"elapsed_since": 1}, "then": {"op": "SCHED-ADMIT", "params": {"proc": "p2"}}})
        self.gate.execute("TICK", "clock", {"now": 10})
        self.assertEqual([o["rule_id"] for o in due(self.store)], ["ob"])  # RE-ARMED (the old firing predates this version)
        self.assertEqual(run_due(self.store, self.gate)["fired"], ["ob"])
        self.assertEqual(due(self.store), [])                              # fired again, once per version
        self.assertEqual(len(self.store.by_action("SCHED-ADMIT")), 2)      # two real firings, not one, not three


class TestB3StampDoesNotCrash(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_non_dict_payload_with_obligation_ref_refuses_cleanly(self):
        # R23: WRITE-ACTIVITY passes caller `data` straight to payload; a LIST payload + obligation_ref
        # used to crash the stamp (dict(list) -> ValueError). Now it falls through to the AR-2 refusal.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("WRITE-ACTIVITY", "alice", {"data": ["not", "a", "dict"], "obligation_ref": "ob"})
        self.assertEqual(cm.exception.rule, "AR-2")                      # clean cited refusal, not a crash
        self.assertEqual(self.store.by_action("WRITE-ACTIVITY"), [])     # the malformed act did not commit
        self.assertEqual(len(self.store.by_action("op-refused")), 1)     # the refusal was recorded


class TestB4OneRefusalDoesNotGagTheRest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_a_refused_firing_is_isolated_and_the_sweep_continues(self):
        # R24: two ripe obligations; obA's firing is refused (a targeted don't blocks SYSTEM's FROB),
        # obB fires. run_due records-and-continues and returns both lists.
        _trivial(self.gate, "FROB")
        self.gate.execute("CREATE-RULE", "owner", _dont("no-sys-frob", [{"action": "FROB", "actor": "SYSTEM"}]))
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "obA", "when": {"elapsed_since": 1}, "then": {"op": "FROB", "params": {}}})
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "obB", "when": {"elapsed_since": 1}, "then": {"op": "SCHED-ADMIT", "params": {"proc": "p"}}})
        self.gate.execute("TICK", "clock", {"now": 5})
        result = run_due(self.store, self.gate)
        self.assertIn("obB", result["fired"])                           # the healthy commitment fired
        self.assertIn("obA", result["refused"])                        # the blocked one is isolated, recorded
        self.assertEqual(len(self.store.by_action("SCHED-ADMIT")), 1)   # obB's outcome really happened


class TestB5PreSpacesEnvelope(unittest.TestCase):
    """B5 (no fix): lock TODAY's pre-spaces openness so the future power-model enforcement (grants +
    spaces, design/30 §2) is a deliberate test FLIP, not a silent regression. The review's owner gate
    (who may make self-executing law) was WITHDRAWN by the power ruling: the answer is 'everyone within
    their granted space; no one outside it', and pre-spaces only the mother space exists — so a TARGETED
    cross-actor bind is open, and reversible (design/30 §4)."""

    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        _trivial(self.gate, "FROB")

    def test_any_actor_may_mint_a_targeted_dont_binding_another_actor(self):
        # alice binds bob (a targeted don't) — passes the untouchables floor and fires. FLIPS when spaces
        # gate scope (design/30 §2): alice writing law over bob's acts will then need power over bob's space.
        self.gate.execute("CREATE-RULE", "alice", _dont("bind-bob", [{"action": "FROB", "actor": "bob"}]))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("FROB", "bob", {})
        self.assertEqual(cm.exception.rule, "bind-bob")

    def test_any_actor_may_amend_the_bind_away_latest_wins(self):
        # reversible mischief, not a brick (design/30 §4): carol neutralises it (latest-wins, empty when)
        self.gate.execute("CREATE-RULE", "alice", _dont("bind-bob", [{"action": "FROB", "actor": "bob"}]))
        self.gate.execute("CREATE-RULE", "carol", {"rule_id": "bind-bob", "polarity": "-", "when": [], "then": []})
        self.gate.execute("FROB", "bob", {})                            # bob is free again
        self.assertEqual(len(self.store.by_action("FROB")), 1)


if __name__ == "__main__":
    unittest.main()


class TestFiredEvidenceForPayloadlessOps(unittest.TestCase):
    # R25 (mentor review): the B3 stamp-only-dict fix silently DROPPED the fired-evidence when the
    # obligation's outcome op produces a record with NO payload at all (e.g. CREATE-INFO) — the
    # commitment fired, the record carried no evidence, and it came due again forever. The stamp
    # must CREATE the payload for an absent one; only a malformed non-dict payload falls through
    # to the AR-2 refusal.
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))

    def test_payloadless_outcome_op_still_records_fired_evidence(self):
        self.gate.execute("CREATE-OBLIGATION", "SYSTEM",
                          {"rule_id": "ob:info", "when": {"elapsed_since": 2},
                           "then": {"op": "CREATE-INFO", "params": {"content": "the review"}}})
        self.gate.execute("TICK", "SYSTEM", {"now": 5})
        r = run_due(self.store, self.gate)
        self.assertEqual(r["fired"], ["ob:info"])
        # the fired decision carries the evidence in the record itself
        self.assertTrue(any((e.get("payload") or {}).get("obligation_ref") == "ob:info"
                            and e["action"] == "CREATE-INFO" for e in self.store.all()))
        # and therefore it is NOT due again — never twice per version
        self.gate.execute("TICK", "SYSTEM", {"now": 50})
        self.assertEqual(due(self.store), [])
        self.assertEqual(run_due(self.store, self.gate), {"fired": [], "refused": []})


class TestFifthConstitutionalLaw(unittest.TestCase):
    # Owner ruling 2026-07-17: CONST-SYSTEM-FUNCTION enters the founding — the corpus's own boot
    # step 11 ("SYSTEM rejects active rule set that destroys boot conditions"), restored. Supreme
    # law is IN THE STORE, declared where the governed can read it, protected like its four peers.
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))

    def test_fifth_law_recorded_constitutional_and_live(self):
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        law = rr["CONST-SYSTEM-FUNCTION"]
        self.assertEqual(law["tier"], "constitutional")
        self.assertEqual(law["enforcement"], "live")
        self.assertTrue(law["text"])
        # five constitutional laws now, exactly
        consts = [r for r in self.views.root_rules() if r["tier"] == "constitutional"]
        self.assertEqual(len(consts), 5)

    def test_fifth_law_protects_itself_like_its_peers(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "owner", {"rule_id": "CONST-SYSTEM-FUNCTION", "value": 1})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["CONST-SYSTEM-FUNCTION"]["tier"], "constitutional")
