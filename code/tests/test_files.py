"""Files governed-core test (design 03 §4.3): custody as record, time-travel content,
unlink = remove-from-view, content-addressed dedup, tree round-trip. No drivers, no FUSE.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.blobs import BlobStore  # noqa: E402
from subsystems.files import FilesView  # noqa: E402


class TestFiles(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.record, blobs=self.blobs)  # files ops via genesis (EP-05)
        self.fv = FilesView(self.store, self.blobs)

    def test_create_write_read(self):
        # DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05): the container of `/etc/conf` has
        # to exist before a name can be taken inside it. The ACT moved rather than the
        # assertion — this row is about writing and reading content, and it now makes the
        # directory it always implied.
        # AND `FILE-MKDIR` REQUIRES A PROVENANCE WHERE `FILE-CREATE` DEFAULTS ONE — a
        # pre-existing asymmetry in the founding's own router declarations, met here because
        # this pass makes the mkdir compulsory. Raised, not changed.
        self.gate.execute("FILE-MKDIR", "SYSTEM",
                          {"path": "/etc", "provenance": {"uid": 0, "gid": 0, "pid": 1, "window": "test"}})
        self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/etc/conf"})
        self.gate.execute("FILE-WRITE", "SYSTEM", {"path": "/etc/conf", "content": "hello"})
        self.assertEqual(self.fv.content_at("/etc/conf"), b"hello")
        self.assertIn("/etc/conf", self.fv.tree())

    def test_time_travel_content_without_snapshots(self):
        self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/f"})
        w1 = self.gate.execute("FILE-WRITE", "SYSTEM", {"path": "/f", "content": "v1"})
        self.gate.execute("FILE-WRITE", "SYSTEM", {"path": "/f", "content": "v2"})
        self.assertEqual(self.fv.content_at("/f"), b"v2")
        self.assertEqual(self.fv.content_at("/f", as_of=w1["seq"]), b"v1")  # as-of past T

    def test_unlink_is_remove_from_view(self):
        self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/f"})
        self.gate.execute("FILE-WRITE", "SYSTEM", {"path": "/f", "content": "data"})
        self.gate.execute("FILE-UNLINK", "SYSTEM", {"path": "/f"})
        self.assertNotIn("/f", self.fv.tree())               # gone from the active view
        self.assertGreaterEqual(len(self.fv.history("/f")), 3)  # the record survives
        writes = self.store.by_action("FILE-WRITE")
        self.assertEqual(self.blobs.get(writes[0]["payload"]["content_hash"]), b"data")  # blob survives

    def test_content_addressed_dedup(self):
        self.assertEqual(self.blobs.put(b"same"), self.blobs.put(b"same"))

    def test_tree_round_trip(self):
        for p in ["/a", "/b", "/c"]:
            self.gate.execute("FILE-CREATE", "SYSTEM", {"path": p})
        self.gate.execute("FILE-UNLINK", "SYSTEM", {"path": "/b"})
        before = self.fv.tree()
        store2, gate2, views2 = build_kernel(self.record)  # rebuild from the record alone
        self.assertEqual(before, FilesView(store2, self.blobs).tree())

    def test_permission_asof(self):
        c = self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/f", "perm": "644"})
        self.gate.execute("FILE-PERM", "SYSTEM", {"path": "/f", "perm": "600"})
        self.assertEqual(self.fv.perms("/f"), "600")
        self.assertEqual(self.fv.perms("/f", as_of=c["seq"]), "644")


if __name__ == "__main__":
    unittest.main()
