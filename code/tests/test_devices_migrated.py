"""T-CORE-MIGRATED(devices) [design 28 §I3, EP-03]: the first real subsystem leaves code.

The devices capability ops are no longer Python handlers — they are op_definition records
seeded at genesis and run by the one generic interpreter. Proof: the handler-registration
function is gone; the ops appear in the derived registry; and a rebuild from the record file
alone brings the ops back AND reproduces identical behaviour (registry = derived state).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import subsystems.devices as devices  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from subsystems.devices import DevicesView  # noqa: E402


class TestDevicesMigrated(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")

    def test_the_python_handler_is_gone(self):
        # the migration deletes the code path: no handler-registration function survives
        self.assertFalse(hasattr(devices, "register_devices_ops"))

    def test_ops_are_definition_records_in_the_registry(self):
        store, gate, views = build_kernel(self.record)
        for op in ("REGISTER-CAPABILITY", "BIND-DEVICE", "UNBIND"):
            self.assertIn(op, views.op_definitions())   # the registry is data
            self.assertTrue(gate.has(op))               # and live on the gate

    def test_rebuild_from_record_brings_ops_back_and_behaviour_is_identical(self):
        store, gate, views = build_kernel(self.record)
        gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0", "device_class": "block"})
        gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d0", "driver": "nvme0"})
        bindings_before = DevicesView(store).bindings()
        self.assertEqual(bindings_before, {"d0": "nvme0"})

        # kill everything derived; rebuild from the record file alone
        store2, gate2, views2 = build_kernel(self.record)
        self.assertIn("BIND-DEVICE", views2.op_definitions())              # op came back as a record
        self.assertEqual(DevicesView(store2).bindings(), bindings_before)  # behaviour identical
        # and the rebuilt (record-derived) op still executes through the interpreter
        gate2.execute("UNBIND", "SYSTEM", {"device": "d0"})
        self.assertNotIn("d0", DevicesView(store2).bindings())

    def test_migrated_bind_still_refuses_an_unregistered_driver(self):
        # the guard survived the migration as a require_prior check citing CAP-IS-LAW
        from kernel.errors import OpError
        store, gate, views = build_kernel(self.record)
        with self.assertRaises(OpError) as cm:
            gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d0", "driver": "ghost"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        self.assertEqual(DevicesView(store).bindings(), {})


if __name__ == "__main__":
    unittest.main()
