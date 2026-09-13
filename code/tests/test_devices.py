"""Devices capability-core test (design 03 §4.4): capability is law, bind cites it or
refuses, binding table is derived. No drivers (D8)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from subsystems.devices import DevicesView  # noqa: E402


class TestDevices(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)  # devices ops arrive via genesis (EP-03)
        self.dv = DevicesView(self.store)

    def test_register_then_bind(self):
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0", "device_class": "block"})
        self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "pci:03:00.0", "driver": "nvme0"})
        self.assertEqual(self.dv.bindings()["pci:03:00.0"], "nvme0")

    def test_bind_without_capability_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "pci:03:00.0", "driver": "ghost"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        self.assertEqual(self.dv.bindings(), {})  # nothing bound

    def test_unbind_removes_from_view_history_survives(self):
        """The unbind leaves the VIEW and the BIND RECORD SURVIVES.

        [DOCUMENTED FLIP — EP-30-W1b, 2026-08-16, the declared stream key's first use.
        ASSERTED: `len(by_action("BIND-DEVICE")) == 1` — a COUNT over the stream, standing in
        for "the bind record survives" while that stream could hold nothing else.
        SUPERSEDED: the bind record asserted BY NAME, filtered on its own recorded `action`,
        with the unbind's arrival asserted SEPARATELY. op:UNBIND now declares
        `record_stream: BIND-DEVICE`, so the granting act's stream holds the revoking record
        too and the count reads 2.
        REMAINS TRUE, and it is the whole subject: THE BIND RECORD SURVIVES THE UNBIND. The
        row's claim never moved; only its proxy did.
        GIVEN UP: nothing. A bare `1 -> 2` would have been cheaper and would have left the row
        asserting only THAT TWO RECORDS EXIST, which is not what this row is for.]"""
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0"})
        self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d0", "driver": "nvme0"})
        self.gate.execute("UNBIND", "SYSTEM", {"device": "d0"})
        self.assertNotIn("d0", self.dv.bindings())
        stream = self.store.by_action("BIND-DEVICE")
        binds = [e for e in stream if e["action"] == "BIND-DEVICE"]
        self.assertEqual(len(binds), 1, "the BIND record did not survive the unbind")
        self.assertEqual(binds[0]["payload"]["device"], "d0")
        self.assertEqual(binds[0]["payload"]["driver"], "nvme0")   # it is the one we wrote
        unbinds = [e for e in stream if e["action"] == "UNBIND"]
        self.assertEqual(len(unbinds), 1,
                         "the unbind record does not land in the granting act's stream")

    def test_asof_and_round_trip(self):
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0"})
        b = self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d0", "driver": "nvme0"})
        self.gate.execute("UNBIND", "SYSTEM", {"device": "d0"})
        self.assertEqual(DevicesView(self.store).bindings(as_of=b["seq"]), {"d0": "nvme0"})  # asOf
        store2, gate2, views2 = build_kernel(self.record)
        self.assertEqual(self.dv.bindings(), DevicesView(store2).bindings())  # round-trip


if __name__ == "__main__":
    unittest.main()
