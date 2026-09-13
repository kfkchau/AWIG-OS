"""EP-07 — the obligation executor + wait/wake (seam S3; design 28 §3/§5).

T-OBLIGATION-FIRES: an elapsed-time obligation + recorded TICKs fire FROM REPLAY ALONE — the record
  drives it, never the wall clock (15.1 clock-as-sensor). Fired THROUGH THE GATE (sole-appender), the
  fired decision carrying obligation_ref so "fired" is derived; never fires twice.
T-WAIT-WAKE: BLOCK-ON folds into the wait/wake view; a matching arrival wakes the actor.
Plus the two EP-06-review extensions: CREATE-RULE may now mint a full-form law; the toothless sweep
  widened over active_rules.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.obligations import due, run_due  # noqa: E402
from kernel.errors import OpError  # noqa: E402

REVIEW = {"op": "SCHED-ADMIT", "params": {"proc": "reviewer"}}  # a benign definition-born then-op


def _trivial(gate, action):
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x", "rule_cited": "ROOT-NEG-5"})


class TestObligationFires(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def _obligation_ref_of(self, action, store=None):
        store = store or self.store
        recs = [e for e in store.by_action(action) if (e.get("payload") or {}).get("obligation_ref")]
        return recs[-1]["payload"]["obligation_ref"] if recs else None

    def test_elapsed_obligation_fires_only_after_ticks_and_from_replay_alone(self):
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "REVIEW-18MO", "when": {"elapsed_since": 18}, "then": REVIEW})
        self.assertEqual([o["rule_id"] for o in due(self.store)], [])   # nothing elapsed yet (no ticks)
        self.gate.execute("TICK", "clock", {"now": 6})
        self.assertEqual([o["rule_id"] for o in due(self.store)], [])   # 6 < 18: not ripe, though wall time passed
        self.gate.execute("TICK", "clock", {"now": 18})
        self.assertEqual([o["rule_id"] for o in due(self.store)], ["REVIEW-18MO"])   # recorded time reached it

        # FIRES FROM REPLAY ALONE: rebuild a fresh kernel from the record (obligation + ticks) and
        # the driver fires — proving elapsed RECORD-time drives it, no wall-clock scheduler.
        store2, gate2, views2 = build_kernel(self.path)
        fired = run_due(store2, gate2)
        self.assertEqual(fired, {"fired": ["REVIEW-18MO"], "refused": []})  # run_due returns {fired, refused} (EP-07B B4)
        admits = [e for e in store2.by_action("SCHED-ADMIT") if (e.get("payload") or {}).get("proc") == "reviewer"]
        self.assertEqual(len(admits), 1)                                # the outcome op ran
        self.assertEqual(self._obligation_ref_of("SCHED-ADMIT", store2), "REVIEW-18MO")  # references its obligation
        self.assertEqual(due(store2), [])                               # fired (DERIVED) — no longer ripe
        self.assertEqual(run_due(store2, gate2), {"fired": [], "refused": []})  # never fires twice

    def test_firing_goes_through_the_gate_not_a_direct_append(self):
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "OB", "when": {"elapsed_since": 1}, "then": REVIEW})
        self.gate.execute("TICK", "clock", {"now": 5})
        before = len(self.store.all())
        run_due(self.store, self.gate)
        after = self.store.all()
        self.assertEqual(len(after) - before, 1)                        # exactly one appended record
        fired = after[-1]
        self.assertEqual(fired["action"], "SCHED-ADMIT")               # a proper gate decision, full envelope
        self.assertEqual(fired["actor"], "SYSTEM")
        self.assertIsNotNone(fired["record_time"])                      # minted at the gate's append

    def test_await_action_obligation_fires_on_a_matching_arrival(self):
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "ON-X", "when": {"await_action": "TRIGGER-X"}, "then": REVIEW})
        self.assertEqual(due(self.store), [])                           # no arrival yet
        _trivial(self.gate, "TRIGGER-X")
        self.gate.execute("TRIGGER-X", "alice", {})                    # the awaited arrival
        self.assertEqual([o["rule_id"] for o in due(self.store)], ["ON-X"])
        self.assertEqual(run_due(self.store, self.gate), {"fired": ["ON-X"], "refused": []})


class TestWaitWake(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_block_folds_into_the_view_and_a_matching_arrival_wakes(self):
        self.gate.execute("BLOCK-ON", "alice", {"on": "IO-DONE"})
        self.assertEqual(self.views.wait_wake(), {"alice": ["IO-DONE"]})     # blocked
        self.assertEqual(self.views.wake({"action": "IO-DONE"}), ["alice"])  # this arrival would wake alice
        self.assertEqual(self.views.wake({"action": "OTHER"}), [])           # an unrelated arrival wakes nobody
        # the arrival is recorded -> alice is woken (the block is folded out)
        _trivial(self.gate, "IO-DONE")
        self.gate.execute("IO-DONE", "SYSTEM", {})
        self.assertEqual(self.views.wait_wake(), {})
        self.assertEqual(self.views.wake({"action": "IO-DONE"}), [])


class TestCreateRuleLearnsFullForm(unittest.TestCase):
    """Extension A (EP-06 review): a runtime CREATE-RULE may now carry when/then/polarity and mint an
    EXECUTABLE structural law — previously only genesis / direct append could (EP-06's synthetic tests
    had to seed genesis-style). Pre-extension this failed: when/then were not in CREATE-RULE's payload."""

    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_runtime_create_rule_mints_an_executable_dont(self):
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "RT-NO", "polarity": "-", "when": [{"action": "RT-ACT"}],
                           "then": [{"refuse": "RT-NO"}]})
        _trivial(self.gate, "RT-ACT")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RT-ACT", "alice", {})      # the full-form pass fires the RUNTIME law
        self.assertEqual(cm.exception.rule, "RT-NO")

    def test_ordinary_policy_create_rule_still_works(self):
        # the added fields default to absent -> inert; a plain policy rule is unchanged
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "P", "policy_key": "k", "value": 3})
        self.assertEqual(self.views.policy_value("k"), 3)


class TestToothlessSweepWidened(unittest.TestCase):
    """Extension B (EP-06 review): toothless_musts widened from root laws to active_rules, so a runtime
    full-form law with an empty outcome is caught. No false positives on definitions or obligations."""

    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_runtime_toothless_law_is_caught_but_healthy_laws_and_obligations_are_spared(self):
        self.assertEqual(self.views.toothless_musts(), [])                 # the 18 + definitions: clean
        # a runtime claiming law (-) with no outcome -> toothless (the root-only version missed this)
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "RT-TOOTHLESS", "polarity": "-", "then": []})
        self.assertIn("RT-TOOTHLESS", self.views.toothless_musts())
        # an obligation (polarity + with a then) and a deferred law are NOT toothless
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "OB", "when": {"elapsed_since": 1}, "then": REVIEW})
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "RT-DEFERRED", "polarity": "-", "then": [], "enforcement": "deferred"})
        toothless = self.views.toothless_musts()
        self.assertNotIn("OB", toothless)
        self.assertNotIn("RT-DEFERRED", toothless)


if __name__ == "__main__":
    unittest.main()
