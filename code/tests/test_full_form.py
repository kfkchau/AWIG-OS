"""EP-06 — root laws in full trigger->outcome form (design 28 §4/§I6).

T-RULES-FULL-FORM: a recorded law EXECUTES its outcome, read from the record — no rule hardcoded.
  * a synthetic DON'T (a real six-dimension `when`) refuses a matching act, before it commits;
  * per-link negation (the trigger-level minus) holds in both directions;
  * a synthetic DO's outcome RESOLVES to its op invocation (auto-execution is EP-07's obligation
    executor — deliberately not fired here);
  * every one of the 18 root laws carries class-appropriate full form; the toothless-must view is
    EMPTY over them, with DEFERRED distinguished from empty; the full form survives round-trip.

The 18's own behavior is unchanged (their `when` is empty, so the pass is inert) — proven by the
rest of the suite staying green. Here we exercise the new executable surface with synthetic laws.
"""

import os
import sys
import tempfile
import unittest
from collections.abc import Mapping

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402


def _plain(x):
    """Records are deep-frozen on append (list->tuple, dict->mappingproxy); normalize back to
    plain list/dict so a stored outcome can be compared to a literal."""
    if isinstance(x, Mapping):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _seed_law(store, rule_id, polarity, when, then, root=False, **extra):
    """Put a full-form law into the record the way genesis does (direct append; CREATE-RULE does
    not yet carry when/then — raised). Runtime structural laws are non-root; the constitution's 18
    are root."""
    payload = {"rule_id": rule_id, "polarity": polarity, "when": when, "then": then}
    if root:
        payload["root"] = True
    payload.update(extra)
    return store._append({"actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": rule_id,
                          "rule_cited": "BOOT-INT", "payload": payload})


def _echo_op(gate, action):
    """Register a trivial op whose draft carries `action` — something for a law trigger to match."""
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x",
                                         "rule_cited": "ROOT-NEG-5"})


class TestSyntheticLawExecutes(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_synthetic_dont_refuses_a_matching_act(self):
        # a structural don't with a REAL when fires with no new engine code — the point of full form
        _seed_law(self.store, "SYNTH-NO", "-", [{"action": "SYNTH-ACT"}], [{"refuse": "SYNTH-NO"}])
        _echo_op(self.gate, "SYNTH-ACT")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("SYNTH-ACT", "alice", {})
        self.assertEqual(cm.exception.rule, "SYNTH-NO")                       # the law's own citation
        self.assertEqual(self.store.by_action("SYNTH-ACT"), [])              # the act never committed
        refusals = self.store.by_action("op-refused")
        self.assertTrue(any(r["rule_cited"] == "SYNTH-NO" for r in refusals))  # recorded

    def test_trigger_level_negation_both_directions(self):
        # when: action == SYNTH-ACT2 AND actor != mallory  (per-link minus on the second pattern)
        _seed_law(self.store, "SYNTH-NEG", "-",
                  [{"action": "SYNTH-ACT2"}, {"actor": "mallory", "not": True}], [{"refuse": "SYNTH-NEG"}])
        _echo_op(self.gate, "SYNTH-ACT2")
        with self.assertRaises(OpError) as cm:      # alice: action hits, not-mallory holds -> refused
            self.gate.execute("SYNTH-ACT2", "alice", {})
        self.assertEqual(cm.exception.rule, "SYNTH-NEG")
        rec = self.gate.execute("SYNTH-ACT2", "mallory", {})  # mallory: not-pattern fails -> no match -> commits
        self.assertEqual(rec["action"], "SYNTH-ACT2")

    def test_synthetic_do_outcome_resolves_but_is_not_auto_fired(self):
        # a DO's outcome is executable-shaped and RESOLVES; auto-firing a must-happen is EP-07.
        _seed_law(self.store, "SYNTH-DO", "+", [{"action": "SYNTH-TRIGGER"}], [{"append_op": "SOME-OUTCOME"}])
        _echo_op(self.gate, "SYNTH-TRIGGER")
        draft = {"actor": "alice", "action": "SYNTH-TRIGGER", "object": "x", "rule_cited": "ROOT-NEG-5"}
        resolved = self.gate.full_form_outcomes(draft)
        self.assertIn("SYNTH-DO", [r["rule_id"] for r in resolved])
        self.assertEqual(_plain([r for r in resolved if r["rule_id"] == "SYNTH-DO"][0]["then"]),
                         [{"append_op": "SOME-OUTCOME"}])
        # and the pass does NOT auto-fire the do (EP-07 is its home): executing the trigger commits
        # only the trigger record, no SOME-OUTCOME appears
        self.gate.execute("SYNTH-TRIGGER", "alice", {})
        self.assertEqual(self.store.by_action("SOME-OUTCOME"), [])

    def test_pass_is_inert_without_a_matching_law(self):
        # a benign op in a kernel whose only structural law does not match runs untouched
        _seed_law(self.store, "SYNTH-OTHER", "-", [{"action": "NOT-THIS"}], [{"refuse": "SYNTH-OTHER"}])
        r = self.gate.execute("CREATE-INFO", "SYSTEM", {"content": "hello"})
        self.assertEqual(r["action"], "CREATE-INFO")


class TestConstitutionFullForm(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        self.rr = {r["rule_id"]: r for r in self.views.root_rules()}

    def test_all_root_laws_carry_full_form(self):
        # EP-06's done bar was 18/18; the count moved to 19 when the owner ruled the FIFTH
        # constitutional law in (CONST-SYSTEM-FUNCTION, 2026-07-17 — the corpus's boot step 11,
        # restored). A ruling-driven flip, logged in the mentor's fifth-law entry. It moved to 20
        # when EP-49B-BUILD (IDENTITY AT THE TUNNEL, founding mover 1.41.0 -> 1.42.0) minted the root
        # law EXTERNAL-TUNNEL beside OWNER-TUNNEL — a §A57 name-and-count RANGE sweep member (the count
        # rose, the meaning did not: still "every root law recorded, and here they all are"), driven
        # at dispatch and disclosed to mgr. EXTERNAL-TUNNEL is deferred/ordinary (design/51 §9), so the
        # constitutional-count and the deferred/live sets below are unmoved.
        self.assertEqual(len(self.rr), 20)
        for rid, r in self.rr.items():
            self.assertIsInstance(r["when"], list, f"{rid} when must be a list")
            self.assertTrue(r["then"], f"{rid} has an empty outcome (toothless) — every law needs teeth or a deferred marker")
            self.assertIsNotNone(r["enforced_by"], f"{rid} names no machinery")

    def test_class_assignments_are_recorded(self):
        # act-pattern -> a check; gate-machinery -> "gate-machinery"; deferred -> enforcement deferred
        self.assertIn("sight", self.rr["SIGHT-IS-LAW"]["enforced_by"])
        self.assertIn("consistency", self.rr["ROOT-NEG-6"]["enforced_by"])
        self.assertEqual(self.rr["ROOT-NEG-4"]["enforced_by"], "gate-machinery")
        self.assertEqual(self.rr["P3-CLOSURE"]["enforced_by"], "gate-machinery")
        # the still-deferred laws: SOP (EP-09-partial via the sop check), OWNER-TUNNEL (awaits its
        # consumer). DOCUMENTED FLIP (EP-17): ROOT-NEG-3 and PACK-SCOPE went deferred->live at the gate
        # authority step. DOCUMENTED FLIP (EP-18): CONST-AUTHORITY-ANCHORED went deferred->live at the
        # gate anchor guard. DOCUMENTED FLIP (EP-19): CONST-SECRETS went deferred->live at the secrets
        # vault — its deferred-exemption ENDS (the toothless-view exemption pattern, EP-07B B5).
        for rid in ("SOP", "OWNER-TUNNEL"):
            self.assertEqual(self.rr[rid]["enforcement"], "deferred", f"{rid} should be deferred")
        for rid in ("ROOT-NEG-3", "PACK-SCOPE", "CONST-AUTHORITY-ANCHORED", "CONST-SECRETS"):
            self.assertEqual(self.rr[rid]["enforcement"], "live", f"{rid} went live at the gate/vault")
        # SYS-RECORD's do-outcome is an op invocation; P4-REFUSE demonstrates the outcome-level minus
        self.assertEqual(_plain(self.rr["SYS-RECORD"]["then"]), [{"append_op": "WRITE-ACTIVITY"}])
        self.assertTrue(any("refrain" in step for step in self.rr["P4-REFUSE"]["then"]))

    def test_toothless_view_is_empty_over_the_constitution(self):
        self.assertEqual(self.views.toothless_musts(), [])   # EP-06 done-state

    def test_toothless_view_catches_a_real_toothless_must_but_spares_deferred(self):
        # a genuine defect: a claiming law (+/-) with an empty outcome and no deferred marker
        _seed_law(self.store, "BROKE", "-", [], [], root=True, text="claims force, does nothing")
        # honest: a deferred law with an empty outcome is law-precedes-machinery, not toothless
        _seed_law(self.store, "HONEST-DEFERRED", "-", [], [], root=True, enforcement="deferred", text="later")
        toothless = self.views.toothless_musts()
        self.assertIn("BROKE", toothless)
        self.assertNotIn("HONEST-DEFERRED", toothless)

    def test_full_form_survives_round_trip(self):
        before = {r["rule_id"]: (r["when"], r["then"], r["enforced_by"]) for r in self.views.root_rules()}
        _, _, views2 = build_kernel(self.path)   # rebuild from the record alone
        after = {r["rule_id"]: (r["when"], r["then"], r["enforced_by"]) for r in views2.root_rules()}
        self.assertEqual(before, after)


class TestRefusalPrecedence(unittest.TestCase):
    """R13 (owner-ruled 2026-07-17): refusal precedence is EXECUTION ORDER, written down as the rule.
    On a multiply-invalid act the cited rule is whichever refusal source fires FIRST in the gate
    pipeline (see Gate.execute). The owner chose to keep this order rather than reorder by tier,
    accepting that the citation is wiring-determined — and asked it locked so the drift is caught,
    not silent. These pin the observable citations; re-sequencing the pipeline breaks them."""

    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        # an active EXCLUSIVE rule, so a later contradicting CREATE-RULE trips the consistency check
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "TEST-EXCL", "policy_key": "k", "value": 1, "exclusive": True})

    def test_doubly_invalid_create_rule_cites_the_check_that_runs_first(self):
        # constitutional TARGET (would trip the constitution guard, step 5 -> BOOT-INT) AND an
        # exclusive CONTRADICTION (trips the consistency check, step 3 -> ROOT-NEG-6). Step 3 runs
        # inside the handler, BEFORE the guard, so the citation is ROOT-NEG-6 — the accident the
        # owner chose to bless and lock. Both refuse+record; only the cited rule differs.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "owner",
                              {"rule_id": "CONST-SELF-PROTECT", "policy_key": "k", "value": 2, "exclusive": True})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-6")
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["CONST-SELF-PROTECT"]["tier"], "constitutional")   # untouched either way

    def test_constitutional_target_without_contradiction_cites_the_guard(self):
        # the contrast that reveals the order: a UNIQUE key -> the consistency check passes, so the
        # constitution guard (step 5) is the first source to fire -> BOOT-INT. Together with the case
        # above, the pair documents that the check precedes the guard.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "owner",
                              {"rule_id": "CONST-SELF-PROTECT", "policy_key": "unique-key", "value": 9})
        self.assertEqual(cm.exception.rule, "BOOT-INT")


if __name__ == "__main__":
    unittest.main()
