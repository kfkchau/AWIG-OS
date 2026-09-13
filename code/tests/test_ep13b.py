"""EP-13B — the pre-campaign-2 fix pack (six ruled fixes W1-W6).

Each work item's failing test lands FIRST (each finding's repro becomes a test before the fix),
both directions per item, then the fix in the named module makes it green. One law across the
five guards: move each check to the DEFINITIVE it was approximating (the allowed-field scope,
the record being written, the promised outcome itself), not a per-form blocklist. W6 wires the
built-and-proven protection layer into the shipped composition (build_full_kernel), ON by default.
Findings: planning/build/CAMPAIGN-1-REVIEW-FINDINGS.md. Derivations carried in EP-13B.md.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.obligations import due, run_due  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from observe.resource_watch import register_resource_observe_ops  # noqa: E402


def _dont(rule_id, when):
    return {"rule_id": rule_id, "polarity": "-", "when": when, "then": [{"refuse": rule_id}]}


# ---------------------------------------------------------------------------
# W1 — the rule-trigger check reads the allowed-field scope, not the shape.
# The interim untouchables-floor classifier treated ANY extra dimension as "narrowing", so a
# trigger pinning an always-true field (rule_cited=ROOT-NEG-6, which every CREATE-RULE carries)
# or an always-absent field (zzz=None) disguised a match-everything block as targeted and bricked
# rule-making. The definitive: space-local narrowing is a concrete WHO/WHERE (actor/object) — the
# scope the guard's own refusal message already names; a non-scope/unknown field narrows nothing.
# ---------------------------------------------------------------------------
class TestW1RuleTriggerScope(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = build_kernel(os.path.join(tempfile.mkdtemp(), "r.jsonl"))

    def test_create_rule_trigger_checked_against_allowed_fields(self):
        # an unknown / always-absent trigger field over CREATE-RULE narrows nothing -> blanket ->
        # refused at creation, citing the guard's rule (the untouchables floor, BOOT-INT).
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice", _dont("brick:zzz", [{"action": "CREATE-RULE", "zzz": None}]))
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertNotIn("brick:zzz", self.views.active_rules())          # the disguise never took effect

    def test_disguised_blanket_rule_block_refused_both_forms(self):
        # BOTH findings-file disguises refuse: the constant always-true field, and the absent field.
        for rid, when in (("brick:const", [{"action": "CREATE-RULE", "rule_cited": "ROOT-NEG-6"}]),
                          ("brick:absent", [{"action": "CREATE-RULE", "zzz": None}])):
            with self.assertRaises(OpError) as cm:
                self.gate.execute("CREATE-RULE", "alice", _dont(rid, when))
            self.assertEqual(cm.exception.rule, "BOOT-INT", rid)
        # rule-making is NOT bricked — every mint was refused, the surface still works
        self.gate.execute("CREATE-RULE", "alice", {"rule_id": "ok", "policy_key": "k", "value": 1})
        self.assertEqual(self.views.policy_value("k"), 1)

    def test_targeted_rule_with_allowed_fields_still_mints(self):
        # a genuinely narrow don't (scopes WHO: actor=alice) is space-local governance and PASSES —
        # the too-wedged direction: the interim heuristic must not over-refuse the legitimate case.
        self.gate.execute("CREATE-RULE", "owner", _dont("no-alice-rules", [{"action": "CREATE-RULE", "actor": "alice"}]))
        self.gate.execute("CREATE-RULE", "bob", {"rule_id": "bobrule", "policy_key": "k", "value": 1})  # bob unaffected
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice", {"rule_id": "alicerule", "policy_key": "k2", "value": 2})
        self.assertEqual(cm.exception.rule, "no-alice-rules")             # the targeted don't fired
        # and narrowing on WHERE (object) is space-local too — a rule about one rule_id mints
        self.gate.execute("CREATE-RULE", "owner", _dont("guard-x", [{"action": "CREATE-RULE", "object": "some-rule"}]))
        self.assertIn("guard-x", self.views.active_rules())


# ---------------------------------------------------------------------------
# W2 — the removal guard reads the record being written, not the invoked op name.
# The gap-refusal keyed on opname=='RETIRE-OP', but removal takes effect from the record's ACTION;
# an observe-adapter record whose action names the retire act removed a protected op with no refusal.
# ---------------------------------------------------------------------------
class TestW2RemovalReadsRecordAction(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        register_resource_observe_ops(self.gate, self.store)             # the M1 audit composition

    def test_protected_removal_via_record_action_refused(self):
        self.assertEqual(self.views.op_definitions()["MEM-GRANT"]["tier"], "owner")   # a protected core
        with self.assertRaises(OpError) as cm:
            self.gate.execute("OBSERVE-RESOURCE", "attacker",
                              {"event": "RETIRE-OP", "object": "op:MEM-GRANT", "data": {"name": "MEM-GRANT"}})
        self.assertEqual(cm.exception.rule, "BOOT-INT")                  # the widened guard refused
        self.assertTrue(self.gate.has("MEM-GRANT"))                      # still live — never removed
        self.assertIn("MEM-GRANT", self.views.op_definitions())

    def test_protected_removal_refusal_survives_replay(self):
        with self.assertRaises(OpError):
            self.gate.execute("OBSERVE-RESOURCE", "attacker",
                              {"event": "RETIRE-OP", "object": "op:MEM-GRANT", "data": {"name": "MEM-GRANT"}})
        # the reboot lens: rebuild from the record file alone — the protected core is still there
        store2, gate2, views2 = build_kernel(self.path)
        self.assertTrue(gate2.has("MEM-GRANT"))
        self.assertIn("MEM-GRANT", views2.op_definitions())

    def test_ordinary_op_lifecycle_unaffected_by_widened_guard(self):
        # the too-wedged direction: an ORDINARY op still retires normally (only owner/constitutional refuse)
        self.gate.execute("CREATE-OP", "alice",
                          {"name": "FOO", "definition": {"law_cited": "CAP-IS-LAW", "params": {}, "payload_from": []}})
        self.assertTrue(self.gate.has("FOO"))
        self.gate.execute("RETIRE-OP", "alice", {"name": "FOO"})
        self.assertFalse(self.gate.has("FOO"))                          # reverts to not-existing


# ---------------------------------------------------------------------------
# W3 — firing evidence includes the promised parameters.
# "has it fired" compared the outcome action + reference but never the params, so the right op with
# the WRONG params marked the promise kept while the promised act never happened.
# ---------------------------------------------------------------------------
class TestW3FiringEvidenceParameters(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = build_kernel(os.path.join(tempfile.mkdtemp(), "r.jsonl"))

    def test_obligation_not_marked_done_on_wrong_parameters(self):
        # the findings-file repro: an obligation to admit `reviewer`, marked done by admitting `attacker`.
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "OB", "when": {"elapsed_since": 1}, "then": {"op": "SCHED-ADMIT", "params": {"proc": "reviewer"}}})
        self.gate.execute("TICK", "clock", {"now": 5})
        self.gate.execute("SCHED-ADMIT", "attacker", {"proc": "attacker", "obligation_ref": "OB"})  # wrong params
        self.assertEqual([o["rule_id"] for o in due(self.store)], ["OB"])   # STILL due — the promise is unmet
        # the honest outcome then fulfils it
        run_due(self.store, self.gate)
        self.assertEqual(due(self.store), [])
        admits = [e for e in self.store.by_action("SCHED-ADMIT") if (e.get("payload") or {}).get("proc") == "reviewer"]
        self.assertEqual(len(admits), 1)                                    # reviewer really was admitted

    def test_obligation_fires_once_on_matching_parameters(self):
        # the too-wedged direction: the honest outcome still marks done, exactly once
        self.gate.execute("CREATE-OBLIGATION", "owner",
                          {"rule_id": "OB", "when": {"elapsed_since": 1}, "then": {"op": "SCHED-ADMIT", "params": {"proc": "reviewer"}}})
        self.gate.execute("TICK", "clock", {"now": 5})
        self.assertEqual(run_due(self.store, self.gate)["fired"], ["OB"])
        self.assertEqual(due(self.store), [])                              # fired this version
        self.gate.execute("TICK", "clock", {"now": 50})
        self.assertEqual(run_due(self.store, self.gate), {"fired": [], "refused": []})   # never twice
        self.assertEqual(len(self.store.by_action("SCHED-ADMIT")), 1)


# ---------------------------------------------------------------------------
# W4 — a refusal always appends a cited record.
# A check citing nothing (cite:null) drove the refusal path to record rule_cited=None; with rule-
# citation enforced, store._append raised before appending — no record, no cite, a plain error.
# ---------------------------------------------------------------------------
class TestW4RefusalAlwaysCites(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = build_kernel(os.path.join(tempfile.mkdtemp(), "r.jsonl"))

    def test_citeless_check_refused_at_definition_time(self):
        citeless = {"law_cited": "CAP-IS-LAW", "params": {"driver": "required"}, "payload_from": ["driver"],
                    "checks": [{"check": "require_prior", "action": "NOPE", "field": "driver", "param": "driver", "cite": None}]}
        for op in ("CREATE-OP", "AMEND-OP"):
            with self.assertRaises(OpError) as cm:
                if op == "CREATE-OP":
                    self.gate.execute("CREATE-OP", "owner", {"name": "CITELESS", "definition": citeless})
                else:
                    # AMEND-OP requires a live target: define a clean op, then try to amend it citeless
                    self.gate.execute("CREATE-OP", "owner",
                                      {"name": "AMENDME", "definition": {"law_cited": "CAP-IS-LAW", "params": {}, "payload_from": []}})
                    self.gate.execute("AMEND-OP", "owner", {"name": "AMENDME", "definition": citeless})
            self.assertEqual(cm.exception.rule, "ROOT-NEG-5", op)          # a check that cites no law is unrecordable
        self.assertFalse(self.gate.has("CITELESS"))

    def test_refusal_path_always_appends_a_cited_record(self):
        # a citeless check that reached the record by a path that skips CREATE-OP validation (genesis /
        # direct seed) must STILL, at use, refuse with a cited record — never crash recordless. Seed one
        # by direct append (the genesis path) so its citeless check is exercised at use.
        citeless = {"description": "x", "law_cited": "CAP-IS-LAW", "params": {"driver": "required"},
                    "payload_from": ["driver"],
                    "checks": [{"check": "require_prior", "action": "NOPE", "field": "driver", "param": "driver", "cite": None}]}
        self.store._append({"actor": "PC_RUNTIME", "action": "CREATE-OP", "object": "op:CITELESS",
                            "rule_cited": "CAP-IS-LAW",
                            "payload": {"kind": "op_definition", "rule_id": "op:CITELESS", "polarity": "+",
                                        "name": "CITELESS", "definition": citeless, "tier": "ordinary"}})
        self.assertTrue(self.gate.has("CITELESS"))                        # the on-append listener registered it
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError):                                  # an OpError, never a raw ValueError
            self.gate.execute("CITELESS", "alice", {"driver": "d"})       # require_prior fails -> refusal path
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)   # a cited refusal WAS appended
        self.assertTrue(self.store.by_action("op-refused")[-1]["rule_cited"])   # non-empty cite


# ---------------------------------------------------------------------------
# W5 — dispute integrity at use.
# A dispute naming a nonexistent (or future) entry was accepted as an inert marker; a future-seq
# dispute suppressed the entry that later landed there. The definitive: refuse a dispute whose
# reference names no existing dictionary entry, mirroring the integrity its sibling reference has.
# ---------------------------------------------------------------------------
class TestW5DisputeIntegrity(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = build_kernel(os.path.join(tempfile.mkdtemp(), "r.jsonl"))

    def _entry(self, term, actor="alice"):
        return self.gate.execute("DICT-ENTRY", actor, {"term": term, "entity_kind": "action"})

    def test_dispute_naming_no_entry_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("DISPUTE", "carol", {"ref_seq": 99999})     # names no dictionary entry
        self.assertEqual(cm.exception.rule, "DICT-LAW")
        self.assertEqual(self.views._disputed_entry_seqs(), set())        # no inert marker recorded

    def test_dispute_cannot_suppress_a_future_entry(self):
        # a dispute on a seq that would only later hold an entry is refused (it does not exist yet),
        # so it can never suppress the entry that later lands there.
        future = len(self.store.all()) + 5                                # a seq no record occupies yet
        with self.assertRaises(OpError) as cm:
            self.gate.execute("DISPUTE", "carol", {"ref_seq": future})
        self.assertEqual(cm.exception.rule, "DICT-LAW")
        r = self._entry("later-term")                                     # the entry eventually lands
        self.assertIn(("action", "later-term"), self.views.dictionary("action"))   # resolves, unsuppressed

    def test_dispute_on_existing_entry_still_routes(self):
        # the too-wedged direction: a dispute on a REAL entry still routes (owner-queue behaviour unchanged)
        r = self._entry("live-term")
        self.gate.execute("DISPUTE", "carol", {"ref_seq": r["seq"]})
        self.assertIn(r["seq"], self.views._disputed_entry_seqs())
        self.assertNotIn(("action", "live-term"), self.views.dictionary("action"))   # disputed -> not the winner
        self.gate.execute("RESOLVE-DISPUTE", "owner", {"ref_seq": r["seq"]})
        self.assertIn(("action", "live-term"), self.views.dictionary("action"))      # resolved -> back


# ---------------------------------------------------------------------------
# W6 — the protection layer is wired into the shipped composition, ON by default.
# The two mutually-blind audit streams and the sight-binds-action ops were built and proven, but
# build_full_kernel never instantiated them — only tests did. Not a flag: the default machine runs
# its own audit layer.
# ---------------------------------------------------------------------------
class TestW6ProtectionWiredByDefault(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "r.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(self.path, os.path.join(self.dir, "blobs"))

    def test_shipped_composition_runs_the_audit_streams(self):
        self.assertTrue(self.gate.has("GRANT-READ"))                      # sight-binds-action ops registered
        self.assertTrue(self.gate.has("CONSUME"))
        prot = self.views.protection                                       # protection is part of the composition
        self.gate.execute("GRANT-READ", "owner", {"grantee": "alice", "target": "/x"})   # a governed, audit-grade act
        grant = [e for e in self.store.by_action("GRANT-READ")][-1]
        a = [m for m in self.store.by_action("dual-audit-record") if m["payload"]["ref_seq"] == grant["seq"]]
        b = [m for m in self.store.by_action("dual-audit-b-record") if m["payload"]["ref_seq"] == grant["seq"]]
        self.assertEqual(len(a), 1)                                        # stream A saw it
        self.assertEqual(len(b), 1)                                        # stream B saw it (mutually blind)
        self.assertEqual(prot.dual_blind_divergences(), [])               # the cross-check answers clean

    def test_shipped_composition_round_trip_with_protection(self):
        self.gate.execute("GRANT-READ", "owner", {"grantee": "alice", "target": "/x"})
        self.gate.execute("CONSUME", "alice", {"target": "/x"})
        self.assertTrue(self.store.by_action("dual-audit-record"))        # streams did fire in the shipped machine
        with open(self.path, encoding="utf-8") as f:
            before = [json.loads(line) for line in f if line.strip()]
        # kill everything derived: rebuild the whole composition from the record file alone
        store2, gate2, views2, blobs2, subs2 = build_full_kernel(self.path, os.path.join(self.dir, "blobs"))
        with open(self.path, encoding="utf-8") as f:
            after = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(before, after)                                   # identical — protection records included
        self.assertEqual(views2.protection.dual_blind_divergences(), [])  # and still clean on the rebuilt machine


if __name__ == "__main__":
    unittest.main()
