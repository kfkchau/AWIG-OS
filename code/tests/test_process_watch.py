"""M1 observe test: the process watcher diffs /proc snapshots and records lifecycle
crossings through the gate. Deterministic via an injected scanner; one real /proc smoke.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from observe.process_watch import register_observe_ops, ProcessWatcher, scan_proc, OBS_RULE  # noqa: E402


class TestProcessWatch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "record.jsonl"))
        register_observe_ops(self.gate, self.store)

    def test_diff_records_created_and_exited(self):
        snaps = [
            {1: {"comm": "init"}, 2: {"comm": "bash"}},
            {2: {"comm": "bash"}, 3: {"comm": "python"}},
        ]
        w = ProcessWatcher(self.gate, scan=lambda: snaps.pop(0))
        r1 = w.poll()  # baseline: 1 and 2 recorded created
        self.assertEqual(len(r1), 2)
        self.assertEqual(len(self.store.by_action("process-created")), 2)
        w.poll()  # pid 1 exited, pid 3 created
        self.assertEqual(len(self.store.by_action("process-exited")), 1)
        self.assertEqual(len(self.store.by_action("process-created")), 3)
        for e in self.store.by_action("process-created"):
            self.assertEqual(e["rule_cited"], OBS_RULE)
            self.assertEqual(e["provenance"]["source"], "/proc")

    def test_one_write_path_via_the_gate(self):
        with self.assertRaises(OpError):
            self.gate.execute("OBSERVE-NOTHING", "process-watcher", {})  # unregistered -> Closure Hit

    def test_asof_process_history(self):
        snaps = [{1: {"comm": "a"}}, {1: {"comm": "a"}, 2: {"comm": "b"}}]
        w = ProcessWatcher(self.gate, scan=lambda: snaps.pop(0))
        w.poll()
        mid = len(self.store.all())
        w.poll()
        self.assertEqual(len(self.store.by_action("process-created", as_of_seq=mid)), 1)

    def test_real_proc_scan_smoke(self):
        if not os.path.isdir("/proc"):
            self.skipTest("no /proc on this platform")
        snap = scan_proc()
        self.assertIn(os.getpid(), snap)         # this test process is visible
        self.assertIn("comm", snap[os.getpid()])


if __name__ == "__main__":
    unittest.main()
