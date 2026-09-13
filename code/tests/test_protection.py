"""Protection layer test (design 02 §3, 03 §3): default-deny sight, sight binds action
(VIS-4), separation of powers (SOP), dual-audit mirror with digest cross-check."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.protection import Protection, register_protection_ops  # noqa: E402


class TestProtection(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "record.jsonl"))
        self.prot = Protection(self.store, self.gate, self.views)
        register_protection_ops(self.gate, self.store, self.prot)

    def test_default_deny_then_grant(self):
        self.assertFalse(self.prot.can_read("alice", "/secret"))
        self.gate.execute("GRANT-READ", "owner", {"grantee": "alice", "target": "/secret"})
        self.assertTrue(self.prot.can_read("alice", "/secret"))

    def test_sight_binds_action(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CONSUME", "alice", {"target": "/secret"})
        self.assertEqual(cm.exception.rule, "SIGHT-IS-LAW")
        self.gate.execute("GRANT-READ", "owner", {"grantee": "alice", "target": "/secret"})
        r = self.gate.execute("CONSUME", "alice", {"target": "/secret"})
        self.assertEqual(r["action"], "CONSUME")

    def test_separation_of_powers(self):
        with self.assertRaises(OpError) as cm:
            self.prot.assert_separation("alice", "alice", "REVIEW")
        self.assertEqual(cm.exception.rule, "SOP")
        self.prot.assert_separation("bob", "alice", "REVIEW")  # different actor: no raise

    def test_dual_audit_mirror_and_crosscheck(self):
        with self.assertRaises(OpError):
            self.gate.execute("DO-NOTHING", "x", {})  # unknown -> op-refused (a dual-audit action)
        mirrors = self.store.by_action("dual-audit-record")
        self.assertEqual(len(mirrors), 1)
        self.assertTrue(self.prot.audit_consistent())


if __name__ == "__main__":
    unittest.main()
