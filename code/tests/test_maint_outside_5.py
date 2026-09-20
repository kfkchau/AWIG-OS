# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (the record, the writer role, an OS advisory lock, a data dir) as in the seL4/gVisor
# literature. NON-GOAL: no offensive capability of any kind — every test here asserts the CORRECT
# behaviour by function: the one-writer rule ACROSS PROCESSES is a HELD operating-system advisory
# lock, so exactly one of many copies opened at the same instant is admitted and the record's entry
# numbers stay strictly increasing. Written from the architect's round-3 read DESCRIPTION (F1) and
# our OWN code at the cited lines — NEVER from the outside harness (not read, not run; owner's
# order). Each real arm PASSES on the fixed code and its PLANT (the old mechanism) FAILS the
# property — the check can fail. Full declaration: SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-5 — the one-writer rule made real ACROSS PROCESSES (a held OS advisory lock).

The C5 repair covered the writer role with a probe that wrote a foreign live pid ITSELF
(tests/test_maint_outside_4.py:147-162) and asserted the refusal — a check that could not race two
writers and so could not fail against the property it named. This file RACES real processes:

    A1  N>=8 real processes open one fresh record at once -> exactly one admitted, the losers refused
        by name, the record's seq strictly increasing with no duplicate. PLANT: the old plain pidfile
        write (no held OS lock) -> the race admits >=2 and a duplicate seq appears (the check can fail).
    A4  a writer that CLOSES frees the advisory lock -> a subsequent writer (a fresh process) over the
        same record is admitted. PLANT: release only at exit -> that writer is refused while the first,
        still alive, has closed but not released (the lock outlives the close). Proven ACROSS processes
        because POSIX record locks are process-associated: a same-process reopen never conflicts, so
        release-on-close can only be observed to fail between processes.

    READER DEMOTION (re-spec C; archi :4199, replacing the struck in-process registry) — IN PROCESS.
        A second same-process open over a record a LIVE writer holds is DEMOTED to a READER: no OS
        lock, every view computed, any APPEND refused BY NAME ("a reader kernel cannot append"); a
        reader for its life; a writer that CLOSES frees the path so the next open is a writer again.
        This is what the earlier registry got wrong — refusing the second open reddened the estate's
        reconstruction idiom (build_full_kernel over the same record to prove replay, which READS and
        compares, never appends). Demotion is transparent to it; only a site that genuinely WRITES
        through a second live instance trips the refusal (the true two-writer case). PLANT: neuter the
        live-writer map -> the second open is NOT demoted, it takes the writer role, two live writers
        are admitted and the append is NOT refused — the check can fail.

A3 (the foreign-pid probe kept as a smoke check, no longer the proof) STAYS in test_maint_outside_4,
UNCHANGED — the pid check that greens it is retained, and it is not restated here.
"""

import collections
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, _SRC)
sys.path.insert(0, os.path.expanduser("~/gov-lab"))

from kernel import store                                            # noqa: E402  (the live-writer map + ReaderCannotAppend)
from kernel.store import EventStore                                 # noqa: E402  (a direct writer/reader open)
from kernel.compose import build_full_kernel                        # noqa: E402  (the whole-kernel writer / reader open)


# The racing / release worker. One fresh record, a shared start instant, one of several MODES:
#   real   run the shipped code and report ADMITTED / REFUSED (A1 real, and B in A4).
#   plant  revert the seam's lock act to the OLD plain write (no held OS lock) -> the race admits
#          more than one (A1 falsifiability).
#   a4hold      build, CLOSE (real release), drop an "A_CLOSED" marker, then stay alive briefly.
#   a4hold_plant  build, CLOSE with _release_lock neutered (release-only-at-exit), marker, stay alive.
_WORKER = r'''
import os, sys, time
SRC, RECORD, START, MODE = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
sys.path.insert(0, SRC)
sys.path.insert(0, os.path.expanduser("~/gov-lab"))
from kernel.compose import build_full_kernel
from kernel.store import EventStore
d = os.path.dirname(RECORD)
if MODE == "plant":
    # OLD mechanism: a plain pidfile write with NO held lock. The 0.1s before the write WIDENS the
    # check-then-write window deterministically (independent of scheduler load), so several racers
    # pass store._acquire_lock's path_exists() check before any pidfile appears — exactly the race
    # the finding names. Without it the window is timing-dependent and the plant flakes under load.
    from bridge import host_seam
    def _plain_write(path, text):
        time.sleep(0.1)
        path.write_text(text)
    h = host_seam.host()
    h.lock_write = _plain_write
    h.lock_read = lambda path: path.read_text()
    h.lock_unlink = lambda path: (path.unlink() if path.exists() else None)
if MODE == "a4hold_plant":
    EventStore._release_lock = lambda self: None                     # PLANT: close releases nothing
while time.time() < START:                                          # barrier
    time.sleep(0.0005)
if MODE in ("real", "plant"):
    try:
        build_full_kernel(RECORD, os.path.join(d, "blobs"), os.path.join(d, "vault"))
        sys.stdout.write("ADMITTED\n")
    except Exception as e:
        sys.stdout.write("REFUSED::" + str(e) + "\n")
elif MODE in ("a4hold", "a4hold_plant"):
    r = build_full_kernel(RECORD, os.path.join(d, "blobs"), os.path.join(d, "vault"))
    r[0].close()                                                    # release on close (or plant no-op)
    with open(os.path.join(d, "A_CLOSED"), "w") as _m:              # tell the parent A has closed
        _m.write("1")
    # stay ALIVE (so a plant that did NOT release still holds the lock) until B has tried, capped.
    deadline = time.time() + 30
    while not os.path.exists(os.path.join(d, "B_DONE")) and time.time() < deadline:
        time.sleep(0.02)
sys.stdout.flush()
'''


def _write_worker(dirpath):
    p = os.path.join(dirpath, "race_worker.py")
    with open(p, "w") as f:
        f.write(_WORKER)
    return p


def _seqs_in(record):
    out = []
    if os.path.exists(record):
        with open(record) as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line).get("seq"))
    return out


class TestA1RaceAcrossProcesses(unittest.TestCase):
    """A1 — the real race: exactly one writer, seq strictly increasing, losers refused by name."""

    def test_a1_real_exactly_one_admitted_seq_strictly_increasing(self):
        d = tempfile.mkdtemp(prefix="ep-mo5-a1-real-")
        worker = _write_worker(d)
        record = os.path.join(d, "record.jsonl")
        start = time.time() + 1.0
        procs = [subprocess.Popen([sys.executable, worker, _SRC, record, str(start), "real"],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                 for _ in range(10)]
        outs = [p.communicate()[0].strip() for p in procs]
        admitted = [o for o in outs if o.startswith("ADMITTED")]
        refused = [o for o in outs if o.startswith("REFUSED")]
        self.assertEqual(len(admitted), 1,
                         "exactly ONE process may be admitted the writer role; got %d\n%s"
                         % (len(admitted), "\n".join(outs)))
        self.assertEqual(len(refused), 9)
        for o in refused:                                   # refused BY NAME
            self.assertIn("one writer per data dir", o)
        seqs = _seqs_in(record)
        self.assertGreater(len(seqs), 0, "the one admitted writer minted a genesis history")
        self.assertEqual(seqs, sorted(seqs), "seq must be strictly increasing")
        self.assertEqual(len(seqs), len(set(seqs)), "no duplicate seq: %r"
                         % [s for s, c in collections.Counter(seqs).items() if c > 1])

    def test_a1_plant_old_pidfile_write_admits_more_than_one(self):
        # THE PLANT the C5 test lacked: revert to the plain pidfile write (no held OS lock) and the
        # same race admits more than one writer, and the record holds a duplicate seq — the check can
        # fail. This is precisely the pre-fix behaviour the reviewer's headline names.
        d = tempfile.mkdtemp(prefix="ep-mo5-a1-plant-")
        worker = _write_worker(d)
        record = os.path.join(d, "record.jsonl")
        start = time.time() + 1.0
        procs = [subprocess.Popen([sys.executable, worker, _SRC, record, str(start), "plant"],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                 for _ in range(10)]
        outs = [p.communicate()[0].strip() for p in procs]
        admitted = [o for o in outs if o.startswith("ADMITTED")]
        self.assertGreaterEqual(len(admitted), 2,
                                "the OLD plain-write mechanism admits >=2 (the check can fail); got %d\n%s"
                                % (len(admitted), "\n".join(outs)))
        dups = [s for s, c in collections.Counter(_seqs_in(record)).items() if c > 1]
        self.assertTrue(dups, "the old race mints one seq twice — the record holds a duplicate")


class TestA4ReleaseOnClose(unittest.TestCase):
    """A4 — a writer that closes frees the advisory lock; a subsequent process is then admitted.
    Cross-process, because POSIX record locks are process-associated (a same-process reopen never
    conflicts, so release-on-close can only be watched to FAIL between processes)."""

    def _run(self, mode):
        d = tempfile.mkdtemp(prefix="ep-mo5-a4-")
        worker = _write_worker(d)
        record = os.path.join(d, "record.jsonl")
        marker = os.path.join(d, "A_CLOSED")
        start = time.time() + 0.5
        a = subprocess.Popen([sys.executable, worker, _SRC, record, str(start), mode],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # wait until A has built AND closed (its marker), then race B against the closed writer
        deadline = time.time() + 15
        while not os.path.exists(marker) and time.time() < deadline:
            time.sleep(0.02)
        self.assertTrue(os.path.exists(marker), "worker A never reported it had closed")
        b = subprocess.Popen([sys.executable, worker, _SRC, record, str(time.time()), "real"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        b_out = b.communicate()[0].strip()
        with open(os.path.join(d, "B_DONE"), "w") as _m:   # release A (it held the lock while B tried)
            _m.write("1")
        a.communicate()
        return b_out

    def test_a4_real_close_frees_the_lock_a_later_process_is_admitted(self):
        b_out = self._run("a4hold")
        self.assertTrue(b_out.startswith("ADMITTED"),
                        "after the first writer CLOSED, a later process must be admitted; got %r" % b_out)

    def test_a4_plant_release_only_at_exit_refuses_the_later_process(self):
        b_out = self._run("a4hold_plant")
        self.assertTrue(b_out.startswith("REFUSED"),
                        "with release-only-at-exit the closed-but-alive writer still holds the lock, "
                        "so a later process is refused (the check can fail); got %r" % b_out)
        self.assertIn("one writer per data dir", b_out)


class _DemotionSink(dict):
    """PLANT — a live-writer map that RECORDS NOTHING. `__setitem__` is a no-op, so no record path is
    ever seen as holding a live writer and the second open is NEVER demoted (it takes the writer role,
    as before the fix). Swapped in for `store._live_writers` to watch two live writers get admitted and
    the append NOT refused — the reader outcome's check can fail."""

    def __setitem__(self, k, v):
        pass


class TestReaderDemotionInProcess(unittest.TestCase):
    """Re-spec C (archi :4199) — a second same-process open over a record a LIVE writer holds opens as
    a READER: no OS lock, every view computed, any APPEND refused BY NAME; a reader for its life; a
    writer that CLOSES frees the path so the next open is a writer again. This replaces the struck
    in-process registry (which refused the second open and reddened the reconstruction idiom)."""

    def _paths(self):
        d = tempfile.mkdtemp(prefix="ep-mo5-reader-")
        return (os.path.join(d, "record.jsonl"),
                os.path.join(d, "blobs"), os.path.join(d, "vault"),
                os.path.join(d, "blobs2"), os.path.join(d, "vault2"),
                os.path.join(d, "blobs3"), os.path.join(d, "vault3"))

    def test_reader_computes_views_but_refuses_append(self):
        # THE REAL OUTCOME: a second open over a live-writer record is a reader — it computes every
        # view over the same record, and any append through it is refused BY NAME.
        record, b1, v1, b2, v2, _b3, _v3 = self._paths()
        k1 = build_full_kernel(record, b1, v1)                       # the LIVE writer
        try:
            store1 = k1[0]
            self.assertFalse(getattr(store1, "_reader", False), "the first open is the writer")
            k2 = build_full_kernel(record, b2, v2)                   # a second open -> a READER
            try:
                store2 = k2[0]
                self.assertTrue(getattr(store2, "_reader", False),
                                "a second open over a live-writer record is demoted to a reader")
                # EVERY VIEW COMPUTED: the reader read the same record the writer holds, and folds it
                self.assertEqual(len(store2.events), len(store1.events),
                                 "the reader computes over the record the live writer holds")
                self.assertEqual([e.get("seq") for e in store2.all()],
                                 [e.get("seq") for e in store1.all()],
                                 "the reader's view of the record equals the writer's")
                # ANY APPEND THROUGH THE READER IS REFUSED BY NAME
                with self.assertRaises(store.ReaderCannotAppend) as cm:
                    store2._append({"actor": "SYSTEM", "action": "WRITE-ACTIVITY",
                                    "object": "reader-probe", "rule_cited": "ROOT-NEG-5"})
                self.assertIn("a reader kernel cannot append", str(cm.exception))
                # A READER FOR ITS LIFE: it still READS after the refusal, and a repeat append refuses
                self.assertEqual(len(store2.all()), len(store1.events))
                with self.assertRaises(store.ReaderCannotAppend):
                    store2._append({"actor": "SYSTEM", "action": "WRITE-ACTIVITY",
                                    "object": "reader-probe-2", "rule_cited": "ROOT-NEG-5"})
            finally:
                store2.close()
        finally:
            k1[0].close()

    def test_the_live_writer_still_appends_alongside_a_reader(self):
        # The demotion does NOT hobble the writer: the LIVE writer appends normally while a reader is
        # open over the same record.
        record, b1, v1, b2, v2, _b3, _v3 = self._paths()
        k1 = build_full_kernel(record, b1, v1)
        try:
            k2 = build_full_kernel(record, b2, v2)                   # a reader, alive alongside
            try:
                self.assertTrue(getattr(k2[0], "_reader", False))
                before = len(k1[0].events)
                k1[1].execute("WRITE-ACTIVITY", "SYSTEM", {"about": "writer-probe", "data": {"x": 1}})
                self.assertGreater(len(k1[0].events), before, "the live writer appends")
            finally:
                k2[0].close()
        finally:
            k1[0].close()

    def test_writer_close_frees_the_path_next_open_is_a_writer(self):
        # A writer that CLOSES frees the path (release-on-close, in-process): the NEXT open over the
        # same record is a WRITER again, not a reader, and it appends.
        record, b1, v1, _b2, _v2, b3, v3 = self._paths()
        k1 = build_full_kernel(record, b1, v1)
        k1[0].close()                                                # the writer frees the path
        k3 = build_full_kernel(record, b3, v3)                       # the next open is a WRITER again
        try:
            self.assertFalse(getattr(k3[0], "_reader", False),
                             "after the writer closed, the next open is a writer (not demoted)")
            before = len(k3[0].events)
            k3[1].execute("WRITE-ACTIVITY", "SYSTEM", {"about": "post-close", "data": {"y": 2}})
            self.assertGreater(len(k3[0].events), before, "the fresh writer appends")
        finally:
            k3[0].close()

    def test_plant_no_demotion_admits_the_second_live_writer(self):
        # THE PLANT (falsifiability): neuter the live-writer map so the second open is NOT demoted ->
        # it takes the writer role and its append is NOT refused. Two live writers admitted; the
        # reader outcome's check CAN fail.
        record, b1, v1, b2, v2, _b3, _v3 = self._paths()
        saved = store._live_writers
        store._live_writers = _DemotionSink()
        k1 = k2 = None
        try:
            k1 = build_full_kernel(record, b1, v1)
            k2 = build_full_kernel(record, b2, v2)                   # NOT demoted (the map records nothing)
            self.assertFalse(getattr(k2[0], "_reader", False),
                             "with demotion neutered the second open is a full writer, not a reader")
            before = len(k2[0].events)
            k2[1].execute("WRITE-ACTIVITY", "SYSTEM",
                          {"about": "plant-second-writer", "data": {"z": 3}})
            self.assertGreater(len(k2[0].events), before,
                               "with demotion neutered the second LIVE writer APPENDS (the check can fail)")
        finally:
            if k2 is not None:
                k2[0].close()
            if k1 is not None:
                k1[0].close()
            store._live_writers = saved


if __name__ == "__main__":
    unittest.main()
