"""Syscall port test (design 03 §5, doc 10): syscalls map to governed ops, governed
refusals map to the errno userland expects AND are recorded, unknown calls are ENOSYS."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel, genesis  # noqa: E402
from kernel.syscall_port import SyscallPort  # noqa: E402


class TestSyscallPort(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, self.blobs, self.v = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"))
        genesis(self.store)
        self.sp = SyscallPort(self.gate, self.views)

    def test_open_write_map_to_ops(self):
        self.assertTrue(self.sp.syscall("open", "p", {"path": "/f"}).get("ok"))
        self.assertTrue(self.sp.syscall("write", "p", {"path": "/f", "content": "hi"}).get("ok"))
        self.assertEqual(self.v["files"].content_at("/f"), b"hi")

    def test_governed_refusal_maps_to_errno_and_records(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 10})
        r = self.sp.syscall("mmap", "web", {"addr": "r1", "length": 100, "holder": "web"})
        self.assertEqual(r["errno"], "ENOMEM")            # the errno userland expects
        self.assertEqual(len(self.store.by_action("op-refused")), 1)  # AND recorded, rule-cited

    def test_unknown_syscall_is_enosys(self):
        self.assertEqual(self.sp.syscall("ioctl", "p", {}).get("errno"), "ENOSYS")

    def test_conformance_lists_mapped_calls(self):
        self.assertIn("open", self.sp.conformance())
        self.assertIn("mmap", self.sp.conformance())


if __name__ == "__main__":
    unittest.main()
