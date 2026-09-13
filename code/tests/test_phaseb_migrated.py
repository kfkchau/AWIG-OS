"""T-CORE-MIGRATED for the last three cores (design 28 §I3, EP-05 Phase B): files, comms,
scheduling leave code. The Python handlers are gone; the ops are genesis-seeded definition
records run by the one interpreter; they are tier "owner" so A4 protects them; and the
content-addressed ops (FILE-WRITE, COMMS-SEND) register only when the blob store is composed
in — a bare build_kernel leaves them unregistered but DISCOVERABLE, never silently broken.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import subsystems.files as files_mod  # noqa: E402
import subsystems.comms as comms_mod  # noqa: E402
import subsystems.scheduling as sched_mod  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from kernel.blobs import BlobStore  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.opdefs import content_ops_pending_blobs  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from founding.install import op_definition  # noqa: E402  # op shapes read from the founding source (EP-14B)

# [EP-25, DOCUMENTED FLIP.] FILE-TRUNCATE joins the content-addressed set: setting a file's
# length CHANGES ITS CONTENT (grow = zero-fill, shrink = drop — design/10 §6, truncate row), so
# the resulting bytes go full-fidelity to a blob and the event records the hash, exactly as a
# write does. It therefore needs the blob store to register, and a bare kernel defers it and
# SAYS SO — which is the property this set exists to keep honest.
CONTENT_OPS = {"FILE-WRITE", "COMMS-SEND", "FILE-TRUNCATE"}
PLAIN_CORE_OPS = ["FILE-CREATE", "FILE-LINK", "FILE-UNLINK", "FILE-PERM", "MOUNT", "UNMOUNT",
                  "COMMS-OPEN", "COMMS-RECV", "COMMS-CLOSE", "SHM-GRANT",
                  "SCHED-ADMIT", "DESCHEDULE", "SET-PRIORITY", "SCHED-HALT", "SCHED-RESUME", "SCHED-KILL"]


class TestCoresMigrated(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")

    def test_the_python_handlers_are_gone(self):
        self.assertFalse(hasattr(files_mod, "register_files_ops"))
        self.assertFalse(hasattr(comms_mod, "register_comms_ops"))
        self.assertFalse(hasattr(sched_mod, "register_scheduling_ops"))

    def test_all_ops_are_owner_tier_definition_records(self):
        store, gate, views, blobs, _sv = build_full_kernel(self.record, os.path.join(self.dir, "b"))
        od = views.op_definitions()
        for op in PLAIN_CORE_OPS + list(CONTENT_OPS):
            self.assertIn(op, od, op)
            self.assertEqual(od[op]["tier"], "owner", op)
            self.assertTrue(gate.has(op), op)

    def test_new_cores_cannot_be_bare_removed_but_can_be_amended(self):
        # Conservation (EP-05C, ruling flip): the new owner-tier cores refuse BARE removal for
        # EVERY actor including the owner (bare removal is the protection gap); they are amended
        # in place, never bare-removed. (Was test_a4_protects_the_new_cores.)
        store, gate, views, blobs, _sv = build_full_kernel(self.record, os.path.join(self.dir, "b"))
        for actor in ("alice", "owner"):
            for op in ("FILE-WRITE", "COMMS-SEND", "SCHED-ADMIT"):
                with self.assertRaises(OpError) as cm:
                    gate.execute("RETIRE-OP", actor, {"name": op})
                self.assertEqual(cm.exception.rule, "BOOT-INT")
                self.assertTrue(gate.has(op))                     # the shield never dropped
        # owner AMEND-OP on a core succeeds, tier conserved
        new_def = dict(op_definition("SCHED-ADMIT"), description="admit, amended")  # op shape from the pack (EP-14B)
        gate.execute("AMEND-OP", "owner", {"name": "SCHED-ADMIT", "definition": new_def})
        self.assertEqual(views.op_definitions()["SCHED-ADMIT"]["tier"], "owner")

    def test_shm_grant_granter_is_stamped_not_forgeable(self):
        """[DOCUMENTED FLIP — EP-30-C4R, 2026-08-26, §A57 cause-mapped repair. CAUSE: EP-30-C4
        landed `require_prior` over MEM-GRANT's `region` on the shipped `SHM-GRANT`. This row's
        subject is FORGERY, not regions — it asks whether `granter` can be forged past the
        stamp — and the region was incidental scaffolding to it, which is exactly why its author
        never founded one. The check fires BEFORE the stamp is ever observable, so the row
        ERRORED without reaching its own question. SUBJECT-ERA: LIVE. The claim is that the live
        gate stamps the acting actor NOW; an era pin would stop asking it.
        THE LAWFUL REPAIR IS RE-DERIVATION AGAINST LIVE LAW: found "r1" through MEM-GRANT so the
        row reaches the question it was written to ask.
        ASSERTED: that the ledger reads the acting actor, "alice", and not the supplied "mallory".
        SUPERSEDED: nothing. REMAINS TRUE: the assertion, unchanged in subject, literal and
        mechanism. GIVEN UP: nothing — in particular the forgery attempt is UNCHANGED, `granter`
        is still supplied as "mallory" and the row still fails if the gate ever honours it.]"""
        # granter is an attribution field STAMPED to the acting actor — a caller cannot forge
        # it into the shm-grant audit ledger (the retired handler hard-set granter = actor).
        store, gate, views, blobs, sv = build_full_kernel(self.record, os.path.join(self.dir, "b"))
        # THE ESTABLISHMENT THE SHARE INHERITS. Held by "alice", the acting actor, so that the
        # region's holder and the row's forgery question stay independent of each other.
        gate.execute("MEM-GRANT", "alice", {"region": "r1", "size": 4096})
        gate.execute("SHM-GRANT", "alice", {"region": "r1", "granter": "mallory", "grantees": ["x"]})
        self.assertEqual(sv["comms"].shm_grants()["r1"]["granter"], "alice")  # not "mallory"

    def test_rebuild_is_behaviour_identical(self):
        store, gate, views, blobs, sv = build_full_kernel(self.record, os.path.join(self.dir, "b"))
        gate.execute("FILE-CREATE", "SYSTEM", {"path": "/f"})
        gate.execute("FILE-WRITE", "SYSTEM", {"path": "/f", "content": "data"})
        gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p1"})
        tree_before = sv["files"].tree()
        # rebuild from the record + same blobs
        store2, gate2, views2, blobs2, sv2 = build_full_kernel(self.record, os.path.join(self.dir, "b"))
        self.assertEqual(sv2["files"].tree(), tree_before)
        self.assertEqual(sv2["files"].content_at("/f"), b"data")   # content-addressed content survives
        self.assertIn("p1", sv2["scheduling"].runnable())


class TestContentOpsPendingBlobs(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")

    def test_bare_kernel_defers_content_ops_but_surfaces_them(self):
        store, gate, views = build_kernel(self.record)  # NO blobs
        for op in CONTENT_OPS:
            self.assertFalse(gate.has(op), op)             # unregistered — cannot run without blobs
            self.assertIn(op, views.op_definitions())      # but the definition record is present
        self.assertEqual(content_ops_pending_blobs(gate, store), sorted(CONTENT_OPS))  # not silent
        self.assertTrue(gate.has("FILE-CREATE"))           # plain ops still register without blobs

    def test_full_kernel_registers_content_ops(self):
        store, gate, views, blobs, _sv = build_full_kernel(self.record, os.path.join(self.dir, "b"))
        for op in CONTENT_OPS:
            self.assertTrue(gate.has(op), op)
        self.assertEqual(content_ops_pending_blobs(gate, store), [])  # nothing left pending


class TestCreateRuleDataBorn(unittest.TestCase):
    # CREATE-RULE's definition-form: its contradiction logic is the `consistency` vocabulary
    # check; its A3 self-protection is the gate guard; it is data-born and owner-tier.
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))

    def test_create_rule_is_a_definition_born_op(self):
        self.assertIn("CREATE-RULE", self.views.op_definitions())
        self.assertEqual(self.views.op_definitions()["CREATE-RULE"]["tier"], "owner")

    def test_consistency_check_refuses_a_contradicting_exclusive_rule(self):
        self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:x", "policy_key": "k", "value": 1, "exclusive": True})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:x2", "policy_key": "k", "value": 2, "exclusive": True})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-6")

    def test_non_exclusive_same_key_is_allowed(self):
        self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:y", "policy_key": "soft", "value": 1})
        self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:y2", "policy_key": "soft", "value": 9})
        self.assertEqual(self.views.policy_value("soft"), 9)  # latest wins, no conflict

    def test_no_policy_key_never_conflicts(self):
        self.gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:note"})  # no policy_key -> consistency no-op
        self.assertIn("law:note", self.views.active_rules())


if __name__ == "__main__":
    unittest.main()
