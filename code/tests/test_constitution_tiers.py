"""EP-05 Phase A — the three-tier constitution (owner ruling 2026-07-15).

Power under law all the way up, the owner included. Three tiers on a `tier` field:
constitutional (nobody changes them through the system), owner (only "owner" retires/amends
a core op), ordinary (v1 unchanged). These tests prove the tiers are stamped and exposed
(A1), the constitutional records protect themselves BOTH directions (A3 — the dangerous rule),
core retirement is owner-only (A4), and the audit floor never lowers (A5).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.protection import Protection  # noqa: E402
from founding.install import op_definition  # noqa: E402  # op shapes read from the founding source (EP-14B)

CONST_LAWS = {"CONST-RECORDING-TOTAL", "CONST-AUTHORITY-ANCHORED", "CONST-SECRETS", "CONST-SELF-PROTECT"}


class TestTierField(unittest.TestCase):  # A1 + A2
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))

    def test_root_rules_expose_tier_and_the_four_const_laws_are_constitutional(self):
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        for law in CONST_LAWS:
            self.assertEqual(rr[law]["tier"], "constitutional", law)
            self.assertTrue(rr[law]["text"])                       # recorded with full text
        self.assertEqual(rr["ROOT-NEG-1"]["tier"], "ordinary")    # existing rules -> ordinary

    def test_const_laws_mark_enforced_vs_deferred(self):
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["CONST-RECORDING-TOTAL"]["enforcement"], "live")   # A5
        self.assertEqual(rr["CONST-SELF-PROTECT"]["enforcement"], "live")      # A3
        self.assertEqual(rr["CONST-AUTHORITY-ANCHORED"]["enforcement"], "live")  # DOCUMENTED FLIP (EP-18): the anchor guard
        self.assertEqual(rr["CONST-SECRETS"]["enforcement"], "live")            # DOCUMENTED FLIP (EP-19): the secrets vault

    def test_op_definitions_expose_tier_cores_are_owner(self):
        od = self.views.op_definitions()
        for core in ("MEM-GRANT", "BIND-DEVICE", "AMEND-PACK"):
            self.assertEqual(od[core]["tier"], "owner", core)


class TestSelfProtection(unittest.TestCase):  # A3 — THE DANGEROUS RULE, both directions
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))

    def test_constitutional_record_refuses_amendment_and_records(self):
        # (a) too-weak direction: a constitutional target must NOT be amendable — even by owner
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "owner",
                              {"rule_id": "CONST-SELF-PROTECT", "policy_key": "x", "value": 1})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)  # refusal recorded

    def test_tier_laundering_refused(self):
        # cannot amend a constitutional record's tier down to ordinary (no tier-laundering)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "owner",
                              {"rule_id": "CONST-RECORDING-TOTAL", "tier": "ordinary"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["CONST-RECORDING-TOTAL"]["tier"], "constitutional")  # unchanged

    def test_ordinary_amendment_still_succeeds(self):
        # (b) too-broad direction: the constitution must NOT lock ordinary governance shut
        self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:q", "policy_key": "k", "value": 1})
        self.assertEqual(self.views.policy_value("k"), 1)
        self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:q", "policy_key": "k", "value": 2})
        self.assertEqual(self.views.policy_value("k"), 2)  # re-amend an ordinary rule: fine

    def test_cannot_mint_a_new_constitutional_rule_at_runtime(self):
        # tiers above ordinary are genesis-only: no actor can mint a new protected
        # (unremovable) law through the system.
        #
        # [DOCUMENTED FLIP — EP-28ZD, 2026-08-13, charter §A57's fence-relation bracket.
        # CAUSE: the founding moved 1.20.0 -> 1.21.0 and CREATE-RULE now DECLARES `tier`, so
        # the claim reaches the payload the constitution guard reads. ASSERTED: the call is
        # ACCEPTED and the tier merely fails to propagate ("CREATE-RULE does not propagate a
        # `tier` param" — the old comment, kept here as the sentence that stopped being true).
        # SUPERSEDED: the call REFUSES at the gate, citing BOOT-INT, with the refusal recorded.
        # REMAINS TRUE, and this row's subject is unchanged and now held HARDER: no actor mints
        # a protected law at runtime. Before, the claim was silently dropped and the act
        # accepted, so the guard never fired and the record simply lost the field; now the
        # guard sees the claim it exists to refuse. GIVEN UP: nothing — both of the original
        # row's downstream assertions (not entrenched, freely amendable) are re-driven below
        # against an ordinary rule of the same id.]
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "SYSTEM",
                              {"rule_id": "law:fake-const", "policy_key": "z", "value": 1,
                               "tier": "constitutional"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)  # recorded
        self.assertNotIn("law:fake-const", self.views.active_rules(),
                         "the refused mint left a rule behind")
        # and ordinary governance is not locked shut by that refusal: the same id is freely
        # creatable without the protected claim, is NOT entrenched, and re-amends.
        self.gate.execute("CREATE-RULE", "SYSTEM",
                          {"rule_id": "law:fake-const", "policy_key": "z", "value": 1})
        self.assertNotEqual(self.views.active_rules()["law:fake-const"].get("tier"), "constitutional")
        self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:fake-const", "policy_key": "z", "value": 2})
        self.assertEqual(self.views.policy_value("z"), 2)

    def test_system_still_functions_after_a_refused_constitutional_amendment(self):
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-RULE", "owner", {"rule_id": "CONST-SECRETS", "value": 1})
        # an ordinary governed act right after still works — the system is not wedged shut
        rec = self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme"})
        self.assertEqual(rec["action"], "REGISTER-CAPABILITY")


class TestCoreRetirement(unittest.TestCase):  # A4
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))

    def test_non_owner_cannot_retire_a_core(self):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RETIRE-OP", "alice", {"name": "MEM-GRANT"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)  # recorded
        self.assertTrue(self.gate.has("MEM-GRANT"))  # still live — the hole is closed

    def test_owner_bare_retire_of_a_core_refused_amend_conserves(self):
        # RULING FLIP (owner, 2026-07-16, "exit not surgery"): a bare RETIRE-OP of a protected
        # core is refused for EVERY actor INCLUDING the owner — bare removal IS the protection gap.
        # The lawful path is AMEND-OP (in-place supersession), which conserves the tier. (Was
        # test_owner_may_retire_a_core; flipped by EP-05C conservation branch d.)
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RETIRE-OP", "owner", {"name": "MEM-GRANT"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)   # recorded
        self.assertTrue(self.gate.has("MEM-GRANT"))                             # the shield never dropped
        # owner's AMEND-OP on the same core SUCCEEDS, tier preserved
        new_def = dict(op_definition("MEM-GRANT"), description="grant, amended")  # op shape from the pack (EP-14B)
        self.gate.execute("AMEND-OP", "owner", {"name": "MEM-GRANT", "definition": new_def})
        self.assertTrue(self.gate.has("MEM-GRANT"))
        self.assertEqual(self.views.op_definitions()["MEM-GRANT"]["tier"], "owner")  # tier conserved

    def test_ordinary_op_retirable_by_anyone_v1_unchanged(self):
        # a runtime-created op is tier "ordinary" and retires as today (any actor)
        d = {"description": "x", "params": {"target": "required"}, "law_cited": "SIGHT-IS-LAW",
             "object_param": "target", "structural_params": ["target"], "checks": []}   # object id, inline (vocab door)
        self.gate.execute("CREATE-OP", "owner", {"name": "MY-OP", "definition": d})
        self.assertEqual(self.views.op_definitions()["MY-OP"]["tier"], "ordinary")
        self.gate.execute("RETIRE-OP", "alice", {"name": "MY-OP"})  # non-owner, ordinary -> ok
        self.assertFalse(self.gate.has("MY-OP"))


class TestAuditFloor(unittest.TestCase):  # A5
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))
        self.prot = Protection(self.store, self.gate, self.views)  # wires the dual-audit mirror
        self.floor = set(self.views.category_packs()["dual-audit-actions"]["levels"])

    def test_amend_pack_can_grow_the_audit_list(self):
        self.gate.execute("AMEND-PACK", "SYSTEM",
                          {"name": "dual-audit-actions", "levels": sorted(self.floor | {"NEW-ACT"})})
        self.assertIn("NEW-ACT", self.views.category_packs()["dual-audit-actions"]["levels"])
        self.assertIn("NEW-ACT", self.prot._audit_actions())  # the mirror follows the growth

    def test_dropping_a_floor_action_is_refused_and_recorded(self):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-PACK", "SYSTEM", {"name": "dual-audit-actions", "levels": ["MOUNT"]})
        self.assertEqual(cm.exception.rule, "CONST-RECORDING-TOTAL")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        # the pack is unchanged and the mirror still mirrors every floor action
        self.assertTrue(self.floor.issubset(set(self.views.category_packs()["dual-audit-actions"]["levels"])))
        for action in self.floor:
            self.assertIn(action, self.prot._audit_actions())

    def test_floor_only_protects_the_named_pack(self):
        # a non-protected pack can be amended freely (the floor is specific to the audit list)
        self.gate.execute("AMEND-PACK", "SYSTEM", {"name": "actor-classes", "levels": ["just-one"]})
        self.assertEqual(list(self.views.category_packs()["actor-classes"]["levels"]), ["just-one"])

    def test_amend_pack_is_a_governed_definition_born_op(self):
        od = self.views.op_definitions()
        self.assertIn("AMEND-PACK", od)                 # governed, not a raw genesis append
        self.assertEqual(od["AMEND-PACK"]["tier"], "owner")


class TestForgedWritePaths(unittest.TestCase):
    # Recognition-by-shape defeated enforcement-by-handler: the derived views recognise a law
    # (by rule_id) or a pack (by kind) across EVERY action, so a runtime-minted op that emits
    # the shape could reach them unguarded. The universal constitution guard closes every such
    # path. These reproduce the three exploits an ordinary actor mounted via CREATE-OP.
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))
        self.prot = Protection(self.store, self.gate, self.views)
        # a forge op that copies arbitrary rule_id/tier into its decision payload
        self.gate.execute("CREATE-OP", "alice", {"name": "FORGE", "definition": {
            "law_cited": "P4-REFUSE", "params": {"rule_id": "required"},
            "object_param": "rule_id", "payload_from": ["rule_id", "tier"],
            "structural_params": ["rule_id"], "checks": []}})   # object_param + payload_from => inline (vocab door)

    def test_forged_op_cannot_neuter_a_constitutional_record(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("FORGE", "alice", {"rule_id": "CONST-SELF-PROTECT", "tier": "ordinary"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.views.active_rules()["CONST-SELF-PROTECT"]["tier"], "constitutional")

    def test_forged_op_cannot_mint_a_constitutional_rule(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("FORGE", "alice", {"rule_id": "law:evil", "tier": "constitutional"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertNotIn("law:evil", self.views.active_rules())  # not entrenched — never written

    def test_forged_op_cannot_lower_the_audit_floor(self):
        self.gate.execute("CREATE-OP", "alice", {"name": "FORGE-PACK", "definition": {
            "law_cited": "P4-REFUSE", "params": {"name": "required", "levels": "required"},
            "object_param": "name", "payload_from": ["name", "levels"],
            "structural_params": ["name", "levels"],   # pack name + governance-label list, inline (vocab door)
            "payload_derive": {"kind": {"tpl": "category_pack"}}, "checks": []}})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("FORGE-PACK", "alice", {"name": "dual-audit-actions", "levels": ["MOUNT"]})
        self.assertEqual(cm.exception.rule, "CONST-RECORDING-TOTAL")
        for action in ("GRANT-READ", "op-refused"):
            self.assertIn(action, self.prot._audit_actions())  # floor intact, mirror unbroken

    def test_boot_handler_injection_is_also_blocked(self):
        # WRITE-ACTIVITY copies caller `data` into its payload and is a BOOT handler (it never
        # touches the interpreter), so it once smuggled protected shapes past a per-handler guard.
        # The guard lives at the GATE — the single point every gated write converges — so this
        # route is refused too. (Same reason the resource-observer's `data` passthrough is safe.)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("WRITE-ACTIVITY", "alice",
                              {"data": {"rule_id": "law:evil", "tier": "constitutional"}})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertNotIn("law:evil", self.views.active_rules())
        with self.assertRaises(OpError) as cm:
            self.gate.execute("WRITE-ACTIVITY", "alice",
                              {"data": {"kind": "category_pack", "name": "dual-audit-actions", "levels": ["MOUNT"]}})
        self.assertEqual(cm.exception.rule, "CONST-RECORDING-TOTAL")
        # a benign WRITE-ACTIVITY (no protected shape) still records normally
        rec = self.gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": "x", "data": {"note": "telemetry"}})
        self.assertEqual(rec["action"], "WRITE-ACTIVITY")

    def test_malformed_non_dict_payload_refuses_not_crashes(self):
        # a data-passthrough handler can be handed a non-dict payload; the guard must fail loud
        # with a cited refusal (P4-REFUSE), never an uncaught crash, and write no record.
        before_refused = len(self.store.by_action("op-refused"))
        for bad in (["x"], "scalar", 7):
            with self.assertRaises(OpError) as cm:
                self.gate.execute("WRITE-ACTIVITY", "alice", {"data": bad})
            self.assertEqual(cm.exception.rule, "AR-2")
        # fails closed: each attempt is a recorded refusal, and NO WRITE-ACTIVITY decision lands
        self.assertEqual(len(self.store.by_action("op-refused")) - before_refused, 3)
        self.assertEqual(len(self.store.by_action("WRITE-ACTIVITY")), 0)


if __name__ == "__main__":
    unittest.main()
