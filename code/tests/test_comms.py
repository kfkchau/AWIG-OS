"""Comms core test (design 03 §4.5): channels/messages as record, queue derived,
payload content-addressed, shm grant recorded (interior writes out of scope)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.blobs import BlobStore  # noqa: E402
from subsystems.comms import CommsView  # noqa: E402


class TestComms(unittest.TestCase):
    """[DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, §A57 cause-mapped repair. CAUSE: VERDICT.
    EP-30-C1 moved the founding 1.26.0 -> 1.27.0 THROUGH ITS OWN DOOR and COMMS-OPEN gained
    three real checks where it carried the empty list — `require_prior` over the entity,
    `value_domain` over the role, `live_slot` over (entity, role). Every call below passed
    `{"channel": ...}` alone, so the gate refused and these rows ERRORED.
    SUBJECT-ERA: LIVE. These rows claim that a channel opens, queues, receives and closes NOW,
    so an era-pin is UNLAWFUL here — it would compare live records to historical law and go
    green while asserting nothing. THE LAWFUL REPAIR IS RE-DERIVATION AGAINST LIVE LAW:
    establish the entity through CREATE-ACCOUNT and name a role.
    ASSERTED: the queue/round-trip/close behaviour of a channel opened with a name alone.
    SUPERSEDED: nothing. The same behaviour, of a channel opened under the contract the
    founding now requires. REMAINS TRUE: every assertion below, unchanged in subject, in
    literal and in mechanism. GIVEN UP: nothing.]"""

    #: THE ENTITY THESE ROWS OPEN CHANNELS FOR. Established through the ordinary door in
    #: setUp rather than named as a literal at each call site, because `require_prior` reads
    #: the RECORD: a channel is an opening of somebody's and the somebody must exist on it.
    ENTITY = "p1"

    #: ONE OF THE TWO DECLARED ROLES (design/39 §6). Named here so a reader meets the
    #: two-channel invariant once instead of at four call sites.
    ROLE = "user-facing"

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.record, blobs=self.blobs)  # comms ops via genesis (EP-05)
        self.cv = CommsView(self.store)
        self.gate.execute("CREATE-ACCOUNT", "SYSTEM",
                          {"account_id": self.ENTITY, "actor_class": "process"})

    def open_channel(self, channel, **over):
        """One opening, under the contract the live founding declares. Named once so the
        three rows below state the SAME call — a fourth spelling of it is a fourth thing
        that can drift from the founding without any row noticing."""
        payload = {"channel": channel, "entity": self.ENTITY, "role": self.ROLE}
        payload.update(over)
        return self.gate.execute("COMMS-OPEN", self.ENTITY, payload)

    def test_open_send_recv_queue(self):
        self.open_channel("sock:7")
        self.assertIn("sock:7", self.cv.open_channels())
        self.assertEqual(self.cv.queue_depth("sock:7"), 0)
        s = self.gate.execute("COMMS-SEND", "p1", {"channel": "sock:7", "message": "ping", "to": "p2"})
        self.assertEqual(self.cv.queue_depth("sock:7"), 1)
        self.assertEqual(self.blobs.get(s["payload"]["message_hash"]), b"ping")  # payload by hash
        self.gate.execute("COMMS-RECV", "p2", {"channel": "sock:7", "message_hash": s["payload"]["message_hash"]})
        self.assertEqual(self.cv.queue_depth("sock:7"), 0)

    def test_close_removes_channel(self):
        self.open_channel("c")
        self.gate.execute("COMMS-CLOSE", "p1", {"channel": "c"})
        self.assertNotIn("c", self.cv.open_channels())

    def test_shm_grant_recorded(self):
        """[DOCUMENTED FLIP — EP-30-C4R, 2026-08-26, §A57 cause-mapped repair. CAUSE: EP-30-C4
        landed `COMM-LAW-SHARE-GRANT`'s one check on the shipped `SHM-GRANT` — `require_prior`
        over MEM-GRANT's `region` — where the op had carried the empty list. This row granted a
        share over "shm:44", a region nothing in this file ever established, so the gate refused
        and the row ERRORED. SUBJECT-ERA: LIVE. The claim is that a shared grant is recorded in
        the who-shares-what ledger NOW, so an era pin would be unlawful here — it would compare a
        live view to historical law and go green while asserting nothing.
        THE LAWFUL REPAIR IS RE-DERIVATION AGAINST LIVE LAW: found the region through the
        ordinary door, MEM-GRANT, exactly as the check's own message says a share must inherit.
        ASSERTED: that the granter is attributed and the grantee listed in the ledger.
        SUPERSEDED: nothing. The same two assertions, over a region a prior record established.
        REMAINS TRUE: both assertions, unchanged in subject, in literal and in mechanism.
        GIVEN UP: nothing.]"""
        # THE ESTABLISHMENT THE SHARE INHERITS. `browser` holds it because `browser` is the
        # granter below — a share granted over a region held by somebody else is a world this
        # row does not mean to claim, and EP-30-K2 carries that check.
        self.gate.execute("MEM-GRANT", "browser", {"region": "shm:44", "size": 4096})
        self.gate.execute("SHM-GRANT", "browser", {"region": "shm:44", "grantees": ["renderer"], "mode": "rw"})
        g = self.cv.shm_grants()["shm:44"]
        self.assertEqual(g["granter"], "browser")
        self.assertIn("renderer", g["grantees"])  # who-shares-what ledger; interior writes uncovered by design

    def test_asof_and_round_trip(self):
        self.open_channel("c")
        mid = len(self.store.all())
        self.gate.execute("COMMS-SEND", "p1", {"channel": "c", "message": "x"})
        self.assertEqual(self.cv.queue_depth("c", as_of=mid), 0)  # asOf before the send
        store2, gate2, views2 = build_kernel(self.record)
        self.assertEqual(self.cv.open_channels(), CommsView(store2).open_channels())  # round-trip


if __name__ == "__main__":
    unittest.main()
