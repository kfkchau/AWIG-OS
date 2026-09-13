"""Observe adapters test (files/mounts/connections): deterministic diff via injected
scanners, plus a real-scanner smoke against this host."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from observe.resource_watch import (  # noqa: E402
    register_resource_observe_ops, DiffWatcher, scan_mounts, scan_dir, scan_connections,
)


class TestResourceWatch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "record.jsonl"))
        register_resource_observe_ops(self.gate, self.store)

    def test_mount_diff(self):
        snaps = [
            {"/": {"source": "root", "fstype": "ext4"}},
            {"/": {"source": "root", "fstype": "ext4"}, "/mnt": {"source": "d", "fstype": "ext4"}},
        ]
        w = DiffWatcher(self.gate, "mount", scan=lambda: snaps.pop(0), source="/proc/mounts")
        w.poll()
        w.poll()
        self.assertEqual(len(self.store.by_action("mount-appeared")), 2)

    def test_file_change_and_remove(self):
        snaps = [
            {"/f": {"size": 1, "mtime": 10}},
            {"/f": {"size": 2, "mtime": 11}},  # changed
            {},                                # removed
        ]
        w = DiffWatcher(self.gate, "file", scan=lambda: snaps.pop(0), source="scandir")
        w.poll(); w.poll(); w.poll()
        self.assertEqual(len(self.store.by_action("file-appeared")), 1)
        self.assertEqual(len(self.store.by_action("file-changed")), 1)
        self.assertEqual(len(self.store.by_action("file-removed")), 1)

    def test_real_scanners_smoke(self):
        self.assertIn("/", scan_mounts())                       # real /proc/mounts
        p = os.path.join(self.dir, "x.txt")
        with open(p, "w") as f:
            f.write("hi")
        self.assertIn(p, scan_dir(self.dir))                    # real os.walk/stat
        self.assertIsInstance(scan_connections(), dict)          # /proc/net/tcp parses, no error


if __name__ == "__main__":
    unittest.main()
