"""EP-05C — tier conservation (design/29). Protection is conserved through the system: only
founding creates it; nothing running may create, elevate, demote, gap, or bypass it, and every
attempt is a recorded refusal. Amendment is in-place supersession (AMEND-OP) with tier carried;
bare removal of a protected op is refused for EVERY actor including the owner ("exit not surgery").
The both-direction battery (the A3 discipline): every guard proven to refuse the gap AND to admit
the legitimate act, and the system still functions after each refusal.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import EventStore  # noqa: E402
from kernel.gate import Gate  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from founding.install import op_definition  # noqa: E402  # op shapes read from the founding source (EP-14B)

ORDINARY_DEF = {"description": "an ordinary op", "params": {"x": "required"}, "law_cited": "SIGHT-IS-LAW",
                "object_param": "x", "structural_params": ["x"], "checks": []}   # x is the object id, inline (vocab door)
# a forge op: emits an op_definition-shaped record with caller-controlled name/tier/definition
FORGE_OPDEF = {"description": "forge", "params": {"name": "required"}, "law_cited": "P4-REFUSE",
               "object_param": "name", "payload_from": ["name", "tier", "definition"],
               "structural_params": ["name"],   # object_param + payload_from => inline (vocab door)
               "payload_derive": {"kind": {"tpl": "op_definition"}}, "checks": []}


class TestC0GateRequiresViews(unittest.TestCase):
    def test_gate_without_views_is_unconstructable(self):
        # C0: a gate whose constitution guard is unwired must not be constructable (no fail-open)
        s = EventStore(os.path.join(tempfile.mkdtemp(), "r.jsonl"))
        with self.assertRaises(TypeError):
            Gate(s)  # missing required `views`

    def test_gate_with_explicit_none_views_is_unconstructable(self):
        # R16: a MISSING arg raises, but an explicit None slipped past — Gate(store, None) built a
        # gate whose guard no-oped (the dead `if self.views is None: return`). A future composer
        # passing None would silently disable the whole constitution. None is now rejected too.
        s = EventStore(os.path.join(tempfile.mkdtemp(), "r.jsonl"))
        with self.assertRaises((TypeError, ValueError)):
            Gate(s, None)


class TestTierConservation(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)
        # a live ordinary op to amend/retire under v1 rules, and a forge op to test elevation/demotion
        self.gate.execute("CREATE-OP", "owner", {"name": "ORD", "definition": ORDINARY_DEF})
        self.gate.execute("CREATE-OP", "owner", {"name": "FORGE", "definition": FORGE_OPDEF})

    def _refused(self):
        return len(self.store.by_action("op-refused"))

    # ---- AMEND-OP mechanics ----
    def test_amend_op_requires_a_live_target(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-OP", "owner", {"name": "NO-SUCH-OP", "definition": ORDINARY_DEF})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-6")

    def test_owner_amend_of_a_core_succeeds_tier_conserved_old_superseded(self):
        # behaviour change proving supersession: amend MEM-GRANT to a def whose object is `region`
        # (unchanged) but description differs; the record replaces in place.
        new_def = dict(op_definition("MEM-GRANT"), description="grant v2")
        self.gate.execute("AMEND-OP", "owner", {"name": "MEM-GRANT", "definition": new_def})
        od = self.views.op_definitions()["MEM-GRANT"]
        self.assertEqual(od["tier"], "owner")                       # tier conserved
        self.assertEqual(od["definition"]["description"], "grant v2")  # superseded in place, latest-wins
        self.assertTrue(self.gate.has("MEM-GRANT"))                 # live throughout (no down moment)

    def test_amend_to_content_def_in_bare_kernel_is_refused(self):
        # R18 (flips the shipped "keeps-the-shield-up" half-fix). A bare kernel (setUp uses
        # build_kernel, no blobs) cannot register a content-addressed op. The half-fix kept the OLD
        # binding live and let the record run ahead — but that survives only one process lifetime:
        # on reboot the replay fold hands the NEW content def to registration, which declines, so
        # the core drops off the registry. Live != replayed: I10 broken. An amendment of a LIVE op
        # that this composition cannot honour is refused (P4), not improvised. The prior definition
        # stays live (shield up), and the refusal is recorded.
        content_def = {"description": "grant, content", "params": {"region": "required", "size": "required"},
                       "law_cited": "MEM-LAW-ALLOC", "object_param": "region", "payload_from": ["region"],
                       "structural_params": ["region"],   # region is the object id, inline; size stays CONTENT below
                       "content_params": {"size": "size_hash"}, "checks": []}
        before = self._refused()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-OP", "owner", {"name": "MEM-GRANT", "definition": content_def})
        self.assertEqual(cm.exception.rule, "BOOT-INT")        # the amendment destroys round-trip identity
        self.assertEqual(self._refused(), before + 1)          # recorded, not silent
        self.assertTrue(self.gate.has("MEM-GRANT"))            # still live on the PRIOR definition
        # and it still executes on that prior (non-content) definition
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 10 ** 9})
        rec = self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 100, "holder": "web"})
        self.assertEqual(rec["action"], "MEM-GRANT")

    def test_full_kernel_amend_to_content_def_registers_and_round_trips(self):
        # The other side of R18: in a FULL kernel (blobs present) a content-addressed AMEND-OP
        # commits and registers cleanly, and the amended registry reconstructs from the record. This
        # exercises the listener's now-unconditional supersede on the content path the bare kernel
        # refuses — proving the simplification did not break the composed case.
        d = tempfile.mkdtemp()
        record, blob_dir = os.path.join(d, "r.jsonl"), os.path.join(d, "blobs")
        store, gate, views, _blobs, _ = build_full_kernel(record, blob_dir)
        self.assertTrue(gate.has("FILE-WRITE"))                    # a content op, registered (blobs present)
        gate.execute("AMEND-OP", "owner",
                     {"name": "FILE-WRITE", "definition": dict(op_definition("FILE-WRITE"), description="fw v2")})
        self.assertTrue(gate.has("FILE-WRITE"))                    # still live after the content amend
        self.assertEqual(views.op_definitions()["FILE-WRITE"]["definition"]["description"], "fw v2")
        self.assertEqual(views.op_definitions()["FILE-WRITE"]["tier"], "owner")   # tier conserved
        store2, gate2, views2, _b2, _ = build_full_kernel(record, blob_dir)       # rebuild from the record
        self.assertTrue(gate2.has("FILE-WRITE"))                   # amended content op re-registers on replay
        self.assertEqual(views2.op_definitions()["FILE-WRITE"]["definition"]["description"], "fw v2")

    def test_bare_kernel_amend_reboot_registry_identical(self):
        # R18 / I10: after any AMEND-OP in a bare kernel, the LIVE registry surface and the surface
        # REPLAYED from the record alone must be identical — the machine reconstructs itself. The
        # half-fix failed exactly here (live kept a binding replay dropped). A legitimate non-content
        # amend supersedes in place; a content amend is refused (above); either way live == replayed.
        self.gate.execute("AMEND-OP", "owner",
                          {"name": "MEM-GRANT", "definition": dict(op_definition("MEM-GRANT"), description="v2")})
        with self.assertRaises(OpError):  # a content amend attempt is refused + recorded; must not perturb the registry
            self.gate.execute("AMEND-OP", "owner", {"name": "MEM-GRANT",
                "definition": {"description": "c", "params": {"region": "required"}, "law_cited": "MEM-LAW-ALLOC",
                               "object_param": "region", "payload_from": ["region"],
                               "content_params": {"region": "h"}, "checks": []}})
        store2, gate2, views2 = build_kernel(self.record)   # reboot, bare (no blobs)
        names = set(self.views.op_definitions()) | set(views2.op_definitions())
        live_has = {n: self.gate.has(n) for n in names}
        replayed_has = {n: gate2.has(n) for n in names}
        self.assertEqual(live_has, replayed_has)            # the invariant the half-fix broke
        self.assertEqual(views2.op_definitions()["MEM-GRANT"]["definition"]["description"], "v2")  # amend replayed
        self.assertTrue(gate2.has("MEM-GRANT"))             # core live in the rebuilt kernel

    def test_non_owner_amend_of_a_core_refused_and_recorded(self):
        before = self._refused()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-OP", "alice", {"name": "MEM-GRANT", "definition": ORDINARY_DEF})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self._refused(), before + 1)
        self.assertEqual(self.views.op_definitions()["MEM-GRANT"]["tier"], "owner")  # unchanged

    def test_amend_op_on_an_ordinary_op_works_for_any_actor(self):
        amended = dict(ORDINARY_DEF, description="ord v2")
        self.gate.execute("AMEND-OP", "alice", {"name": "ORD", "definition": amended})  # non-owner, ordinary
        self.assertEqual(self.views.op_definitions()["ORD"]["definition"]["description"], "ord v2")

    # ---- the gap and its siblings ----
    def test_bare_retire_of_a_core_refused_for_owner_and_non_owner(self):
        for actor in ("alice", "owner"):
            with self.assertRaises(OpError) as cm:
                self.gate.execute("RETIRE-OP", actor, {"name": "MEM-GRANT"})
            self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertTrue(self.gate.has("MEM-GRANT"))  # the shield never dropped

    def test_elevation_is_refused(self):
        # forge an op_definition claiming tier owner for a name that is NOT a live owner op
        for name in ("ORD", "BRAND-NEW"):   # active ordinary, and no-target
            with self.assertRaises(OpError) as cm:
                self.gate.execute("FORGE", "owner", {"name": name, "tier": "owner", "definition": ORDINARY_DEF})
            self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.views.op_definitions()["ORD"]["tier"], "ordinary")  # not elevated

    def test_demotion_is_refused(self):
        # forge a supersession of a live OWNER core carrying a lower/absent tier
        for tier in ("ordinary", None):
            with self.assertRaises(OpError) as cm:
                self.gate.execute("FORGE", "owner", {"name": "MEM-GRANT", "tier": tier, "definition": ORDINARY_DEF})
            self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.views.op_definitions()["MEM-GRANT"]["tier"], "owner")  # not demoted

    def test_wrong_actor_owner_claim_refused(self):
        # even a well-formed owner-tier supersession of a live owner op is refused for a non-owner
        with self.assertRaises(OpError) as cm:
            self.gate.execute("FORGE", "alice", {"name": "MEM-GRANT", "tier": "owner",
                                                 "definition": op_definition("MEM-GRANT")})
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    # ---- v1 preserved for ordinary; constitution absolute ----
    def test_ordinary_ops_still_retire_and_create_as_v1(self):
        self.gate.execute("RETIRE-OP", "alice", {"name": "ORD"})  # ordinary retire by anyone
        self.assertFalse(self.gate.has("ORD"))
        self.gate.execute("CREATE-OP", "bob", {"name": "ORD2", "definition": ORDINARY_DEF})
        self.assertTrue(self.gate.has("ORD2"))

    def test_constitutional_records_still_refuse_everything(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "owner", {"rule_id": "CONST-SELF-PROTECT", "value": 1})
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    # ---- system keeps working; round-trip ----
    def test_system_functions_after_every_refusal_and_round_trips(self):
        # a stream of refusals interleaved with a legitimate amendment
        for actor, params in [("alice", {"name": "MEM-GRANT"}), ("owner", {"name": "MEM-GRANT"})]:
            with self.assertRaises(OpError):
                self.gate.execute("RETIRE-OP", actor, params)
        self.gate.execute("AMEND-OP", "owner", {"name": "FILE-CREATE",
                                                "definition": dict(op_definition("FILE-CREATE"), description="fc v2")})
        # an ordinary governed act still works after all the refusals
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme"})
        before = self.views.op_definitions()
        # full round-trip: rebuild from the record alone reconstructs the amended registry identically
        store2, gate2, views2 = build_kernel(self.record)
        self.assertEqual(views2.op_definitions()["FILE-CREATE"]["definition"]["description"], "fc v2")
        self.assertEqual(set(views2.op_definitions()), set(before))
        self.assertTrue(gate2.has("MEM-GRANT"))  # never removed


class TestPackScope(unittest.TestCase):  # C4
    def test_pack_scope_law_recorded_ordinary_tier_now_live(self):
        # (EP-05C recorded PACK-SCOPE as law-with-deferred-machinery; EP-17 flips it LIVE — the gate
        #  authority step enforces a vocabulary write by reach. DOCUMENTED FLIP: enforcement deferred
        #  -> live; tier stays ordinary — never a guardian privilege.)
        store, gate, views = build_kernel(os.path.join(tempfile.mkdtemp(), "r.jsonl"))
        rr = {r["rule_id"]: r for r in views.root_rules()}
        self.assertIn("PACK-SCOPE", rr)
        self.assertEqual(rr["PACK-SCOPE"]["polarity"], "-")
        self.assertEqual(rr["PACK-SCOPE"]["tier"], "ordinary")       # not a guardian privilege
        self.assertEqual(rr["PACK-SCOPE"]["enforcement"], "live")    # EP-17: enforced at the gate (was deferred)
        self.assertIn("beyond the actor's", rr["PACK-SCOPE"]["text"])


if __name__ == "__main__":
    unittest.main()
