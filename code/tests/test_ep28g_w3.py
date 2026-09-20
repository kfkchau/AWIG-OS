# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28G W3 — VISIBILITY: a decide entering after an append reads a fold containing it.

  T-DECIDE-SEES-ITS-PREDECESSOR   act N+1's decide, entering the region after act N's append,
                                  reads a fold that CONTAINS act N — BEFORE act N's covering
                                  sync. Asserted on a COUNTABLE (the fold's content), never
                                  on timing. RED: a double deferring fold visibility to
                                  post-sync — and that red world is the ORIGINAL BLINDNESS
                                  EP-28 ADDENDUM 10.7 item 1 warned about, exhibited.

WHY IT IS THE ROW THE WHOLE EP TURNS ON. If fold visibility waited for the sync, the region
would protect NOTHING: the next decide would read a stale world and the race would return
wearing the region's name. And it is LAWFUL to see an un-synced record, which is the half a
reader stumbles on — durability arrives in file order, so anything depending on this record
sits later in the same file; if the dependent act ever becomes durable, so did this one. No
durable record can ever cite a lost one (EP-28C AMENDMENT 3 §3.3, the prefix-durability law).

WHAT IT DOES NOT LICENSE. The reply to act N's own SUBMITTER still releases only after the
covering sync. Invariant 1 is about what leaves the machine; this row is about what the decide
path may see; the prefix-durability law is why the two lawfully differ.
"""

import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import gate as gate_mod                              # noqa: E402
from kernel import store as store_mod                            # noqa: E402
from bridge import host_seam as seam_mod                          # C7 P2 — the barrier now issues from the seam (:3927)
from kernel.compose import build_full_kernel                     # noqa: E402
from kernel.errors import OpError                                # noqa: E402

ORDINARY_DEF = {"description": "an ordinary op", "params": {"x": "required"},
                "law_cited": "SIGHT-IS-LAW", "object_param": "x", "checks": [],
                # x is the op's object_param — a scalar identity handle, safe inline. Classified
                # STRUCTURAL so this well-formed setup op passes the vocabulary door (design/46
                # member 2; archi :2956 RULING 1 — object_param => structural, not blanket).
                "structural_params": ["x"]}

#: A wedge detector, not a measurement. The true positive never reaches it.
WEDGE_S = 10.0


def defer_visibility(case, store):
    """THE RED WORLD, INSTALLED ON A LIVE STORE: a record is written and flushed at its
    publish and becomes visible to the folds only when the barrier covering it returns.

    This is EP-28 ADDENDUM 10.7 item 1's hazard, built: *"if any fold reads from disk rather
    than from the appended state, then during a batch window the gate is blind to its own most
    recent decisions — act N decides without seeing act N-1."* ONE VARIABLE MOVES — WHEN the
    record enters `self.events` — and the durability contract is untouched: the same bytes, the
    same order, the same barrier, the same reply-after-sync.

    Installed on the instance rather than as a subclass so the world is the REAL composition
    with one behaviour varied, instead of a world built differently."""
    withheld = []
    real_append_one = store._append_one
    real_commit = store._commit_batch

    def deferring_append_one(ev, f):
        record = real_append_one(ev, f)
        # HIDDEN FROM EVERY FOLD SOURCE, not only from the list: `by_action` reads the derived
        # index, so withholding one and not the other would build a world where the record is
        # half-visible, which is neither the hazard nor anything anyone has to fear.
        store.events.remove(record)
        store._by_action.get(record["action"], []).remove(record)
        withheld.append(record)
        return record

    def releasing_commit(batch):
        out = real_commit(batch)
        while withheld:                           # visible only after the covering sync
            record = withheld.pop(0)
            store.events.append(record)
            store._by_action.setdefault(record["action"], []).append(record)
        return out
    store._append_one = deferring_append_one
    store._commit_batch = releasing_commit
    store.group_commit._commit_batch = releasing_commit
    case.addCleanup(setattr, store.group_commit, "_commit_batch", real_commit)
    case.addCleanup(setattr, store, "_commit_batch", real_commit)
    case.addCleanup(setattr, store, "_append_one", real_append_one)


class VisibilityCase(unittest.TestCase):

    def build(self, defer=False):
        d = tempfile.mkdtemp(prefix="ep28g-w3-")
        self.addCleanup(shutil.rmtree, d, True)
        rec = os.path.join(d, "rec.jsonl")
        store, gate, views, blobs, _ = build_full_kernel(rec, os.path.join(d, "blobs"))
        self.addCleanup(store.close)
        if defer:
            defer_visibility(self, store)
        return store, gate, views

    def _second_decide_at_the_first_barrier(self, store, gate):
        """Act N appends; at the exact moment its covering barrier is about to run, act N+1
        enters the region and reads the fold. Returns what N+1's decide saw.

        THE HANDSHAKE IS THE POINT. The barrier is the one instant at which "appended but not
        yet durable" is guaranteed to be the record's state, and the region has already been
        released by then — which is why a second decider can be there at all. Under the big
        lock this handshake could not happen and the wait would expire."""
        seen = {}
        entered = threading.Event()
        read = threading.Event()
        real_sync = seam_mod.os.fdatasync

        def at_the_barrier(fd):
            if not entered.is_set():
                entered.set()
                read.wait(WEDGE_S)                # the second decide reads, here
            return real_sync(fd)

        def second():
            entered.wait(WEDGE_S)
            try:
                # THE FOLD READ, through the gate's own region — this IS act N+1's decide
                # arriving. `gate.has` is the same registry fold `create_op` consults.
                gate.region.enter()
                try:
                    seen["names"] = sorted(
                        (e.get("payload") or {}).get("name")
                        for e in store.by_action("CREATE-OP"))
                    seen["count"] = len(store.all())
                finally:
                    gate.region.exit()
            except BaseException as exc:          # noqa: BLE001 — reported, never hidden
                seen["error"] = exc
            read.set()
        t = threading.Thread(target=second, daemon=True)
        t.start()
        seam_mod.os.fdatasync = at_the_barrier
        try:
            gate.execute("CREATE-OP", "owner", {"name": "FIRST", "definition": ORDINARY_DEF})
        finally:
            seam_mod.os.fdatasync = real_sync
            read.set()
        t.join(timeout=WEDGE_S)
        self.assertFalse(t.is_alive(), "the second decide never returned")
        self.assertNotIn("error", seen, "the second decide raised: %r" % seen.get("error"))
        return seen

    def test_a_decide_entering_after_an_append_reads_a_fold_containing_it(self):
        """THE COUNTABLE: the fold's content. The second decide, arriving while the first
        record is appended and NOT yet durable, sees it."""
        store, gate, _ = self.build()
        seen = self._second_decide_at_the_first_barrier(store, gate)
        self.assertIn("FIRST", seen["names"],
                      "a decide entering after the append could not see it: %r" % (seen,))
        self.assertGreaterEqual(seen["count"], 1)

    def test_the_record_it_saw_was_not_yet_durable(self):
        """The other half, and without it the row would pass on a record that had already
        synced — which would assert nothing. The read happens INSIDE the barrier's own call,
        so the record it saw is by construction appended-and-not-yet-covered."""
        store, gate, _ = self.build()
        at_barrier = {}
        real_sync = seam_mod.os.fdatasync
        entered = threading.Event()
        read = threading.Event()

        def at_the_barrier(fd):
            if not entered.is_set():
                entered.set()
                at_barrier["on_disk"] = self._lines(store)
                at_barrier["in_fold"] = [(e.get("payload") or {}).get("name")
                                         for e in store.by_action("CREATE-OP")]
                read.set()
            return real_sync(fd)
        seam_mod.os.fdatasync = at_the_barrier
        try:
            gate.execute("CREATE-OP", "owner", {"name": "FIRST", "definition": ORDINARY_DEF})
        finally:
            seam_mod.os.fdatasync = real_sync
        self.assertTrue(read.is_set(), "the act issued no barrier")
        self.assertIn("FIRST", at_barrier["in_fold"],
                      "the record was not in the fold at the instant its barrier ran")

    @staticmethod
    def _lines(store):
        try:
            with open(store.file_path, encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        except FileNotFoundError:
            return 0

    def test_the_reply_still_waits_for_the_covering_sync(self):
        """VISIBILITY IS NOT A REPLY. The decide path may read an un-synced record; the
        caller may not be told about one. Asserted at the act's boundary, which is what a
        caller actually waits on."""
        store, gate, _ = self.build()
        order = []
        real_sync = seam_mod.os.fdatasync

        def spy(fd):
            order.append("sync")
            return real_sync(fd)
        seam_mod.os.fdatasync = spy
        try:
            gate.execute("CREATE-OP", "owner", {"name": "FIRST", "definition": ORDINARY_DEF})
            order.append("reply")
        finally:
            seam_mod.os.fdatasync = real_sync
        self.assertEqual(order[-2:], ["sync", "reply"],
                         "the act replied before its covering sync: %r" % (order,))

    def test_red_world_a_store_deferring_fold_visibility_to_post_sync(self):
        """RED WORLD, GENERATED, AND IT IS THE HISTORICAL HAZARD EXHIBITED. A store that
        publishes into the record only once the covering barrier has returned. The second
        decide arrives at exactly the same instant, through exactly the same path, and sees a
        world WITHOUT its predecessor — act N+1 deciding blind to act N, which is the failure
        EP-28 ADDENDUM 10.7 item 1 named and which nothing had ever exhibited.

        UNREACHABLE BY EVERY DURABILITY CLAUSE: the same bytes reach the file in the same
        order, the barrier runs, and the reply still follows it. Only the visibility clause
        moves."""
        store, gate, _ = self.build(defer=True)
        seen = self._second_decide_at_the_first_barrier(store, gate)
        self.assertNotIn("FIRST", seen["names"],
                         "the deferring double did NOT blind the second decide (%r), so this "
                         "red world proves nothing" % (seen,))
        # AND THE DURABILITY CLAUSES ARE STILL GREEN IN THIS WORLD, which is what makes the
        # red world specific to visibility.
        self.assertEqual(self._lines(store), len(store.all()),
                         "the deferring double changed what reached the file, so it moved "
                         "more than the one variable")

    def test_red_world_the_deferring_store_lets_a_shadow_check_pass_twice(self):
        """THE CONSEQUENCE OF THE BLINDNESS, driven rather than described: under the
        deferring store, two SEQUENTIAL creates of one name — no concurrency at all — can
        both pass `gate.has`, because the first is invisible until its barrier returns. The
        region is intact in this world and protects nothing, which is the sentence the plan
        makes and this is it as a measurement."""
        store, gate, _ = self.build(defer=True)
        blind = {}
        real_sync = seam_mod.os.fdatasync
        done = threading.Event()

        def at_the_barrier(fd):
            if not done.is_set():
                done.set()
                blind["has_first_while_unsynced"] = gate.has("FIRST")
                blind["fold"] = [(e.get("payload") or {}).get("name")
                                 for e in store.by_action("CREATE-OP")]
            return real_sync(fd)
        seam_mod.os.fdatasync = at_the_barrier
        try:
            gate.execute("CREATE-OP", "owner", {"name": "FIRST", "definition": ORDINARY_DEF})
        finally:
            seam_mod.os.fdatasync = real_sync
        self.assertNotIn("FIRST", blind["fold"],
                         "the deferring store did not hide the record from the fold")
        # AND THE CONTROL, on the real store: the same probe sees it.
        store2, gate2, _ = self.build()
        control = {}
        done2 = threading.Event()

        def control_barrier(fd):
            if not done2.is_set():
                done2.set()
                control["fold"] = [(e.get("payload") or {}).get("name")
                                   for e in store2.by_action("CREATE-OP")]
            return real_sync(fd)
        seam_mod.os.fdatasync = control_barrier
        try:
            gate2.execute("CREATE-OP", "owner", {"name": "FIRST", "definition": ORDINARY_DEF})
        finally:
            seam_mod.os.fdatasync = real_sync
        self.assertIn("FIRST", control["fold"],
                      "the real store hid the record too — then the double is not the "
                      "variable this row varies")

    def test_the_region_is_released_before_the_barrier_so_the_second_decide_can_arrive(self):
        """The structural reason the handshake above is possible at all, stated as its own
        clause: at the instant the barrier runs, no thread holds the region."""
        store, gate, _ = self.build()
        held = []
        real_sync = seam_mod.os.fdatasync

        def spy(fd):
            held.append(gate_mod.decide_region_held())
            return real_sync(fd)
        seam_mod.os.fdatasync = spy
        try:
            gate.execute("CREATE-OP", "owner", {"name": "FIRST", "definition": ORDINARY_DEF})
            with self.assertRaises(OpError):
                gate.execute("CREATE-OP", "owner", {"name": "FIRST",
                                                    "definition": ORDINARY_DEF})
        finally:
            seam_mod.os.fdatasync = real_sync
        self.assertGreaterEqual(len(held), 2)
        self.assertEqual(set(held), {False})


if __name__ == "__main__":
    unittest.main()
