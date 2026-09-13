"""Whole-kernel integration: a mixed workload across all five governed cores, the
whole machine reconstructing from the record, and a cross-subsystem audit. This is the
composition proof (design 02 §10) at full-subsystem scale.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel, genesis  # noqa: E402


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blobdir = os.path.join(self.dir, "blobs")
        self.store, self.gate, self.views, self.blobs, self.v = build_full_kernel(self.record, self.blobdir)
        genesis(self.store)

    def test_mixed_workload_and_whole_kernel_reconstructs(self):
        g = self.gate
        # law
        g.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 4096})
        g.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0", "device_class": "block"})
        # a mixed workload touching every subsystem
        g.execute("SCHED-ADMIT", "SYSTEM", {"proc": "web", "wake_cause": "boot"})
        g.execute("MEM-GRANT", "web", {"region": "heap", "size": 2048, "holder": "web"})
        g.execute("BIND-DEVICE", "SYSTEM", {"device": "disk0", "driver": "nvme0"})
        # DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05): the containers of
        # `/var/log/app.log` have to exist before a name can be taken inside them. The ACT
        # moved rather than the assertion — this row is a mixed workload across subsystems,
        # and it now makes the directories it always implied.
        # AND `FILE-MKDIR` REQUIRES A PROVENANCE WHERE `FILE-CREATE` DEFAULTS ONE — a
        # pre-existing asymmetry in the founding's own router declarations, met here because
        # this pass makes the mkdir compulsory. Raised, not changed.
        g.execute("FILE-MKDIR", "web", {"path": "/var", "provenance": {"uid": 0, "gid": 0, "pid": 1, "window": "test"}})
        g.execute("FILE-MKDIR", "web", {"path": "/var/log", "provenance": {"uid": 0, "gid": 0, "pid": 1, "window": "test"}})
        g.execute("FILE-CREATE", "web", {"path": "/var/log/app.log"})
        g.execute("FILE-WRITE", "web", {"path": "/var/log/app.log", "content": "started"})
        # DOCUMENTED FLIP (EP-30-C1R, 2026-08-21, §A57 cause-mapped repair). CAUSE: VERDICT.
        # EP-30-C1 moved the founding 1.26.0 -> 1.27.0 through its own door and COMMS-OPEN
        # gained three real checks where it carried the empty list: the entity must be
        # established on the record, the role is one of two declared values, and the
        # (entity, role) slot must not already be live. SUBJECT-ERA: LIVE — this row is a
        # mixed workload across subsystems NOW, so it RE-DERIVES against live law and is
        # never era-pinned. THE ACT MOVED, NOT THE ASSERTION: exactly as EP-28N AMENDMENT 1
        # made the directories this row always implied, this row now founds the identity
        # whose channel it always opened. Every assertion below is unchanged.
        g.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": "web", "actor_class": "process"})
        g.execute("COMMS-OPEN", "web", {"channel": "sock:1", "entity": "web",
                                        "role": "user-facing"})
        g.execute("COMMS-SEND", "web", {"channel": "sock:1", "message": "hello", "to": "peer"})
        # every current answer holds across subsystems
        self.assertIn("web", self.v["scheduling"].runnable())
        self.assertEqual(self.v["memory"].resident_size("web"), 2048)
        self.assertEqual(self.v["devices"].bindings()["disk0"], "nvme0")
        self.assertEqual(self.v["files"].content_at("/var/log/app.log"), b"started")
        self.assertEqual(self.v["comms"].queue_depth("sock:1"), 1)
        # THE whole-machine property: kill every cache, rebuild from the record, identical
        _, _, _, _, v2 = build_full_kernel(self.record, self.blobdir)
        self.assertEqual(self.v["scheduling"].runnable(), v2["scheduling"].runnable())
        self.assertEqual(self.v["memory"].mappings(), v2["memory"].mappings())
        self.assertEqual(self.v["devices"].bindings(), v2["devices"].bindings())
        self.assertEqual(self.v["files"].tree(), v2["files"].tree())
        self.assertEqual(self.v["comms"].open_channels(), v2["comms"].open_channels())

    def test_cross_subsystem_audit_every_act_cites_a_rule(self):
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p", "wake_cause": "io:88"})
        self.assertEqual(self.v["scheduling"].why_ran("p")["wake_cause"], "io:88")
        # every governed act in the record cites a rule — the audit Linux cannot give
        for e in self.store.all():
            self.assertIsNotNone(e.get("rule_cited"), f"{e['action']} (seq {e['seq']}) has no rule_cited")


if __name__ == "__main__":
    unittest.main()
