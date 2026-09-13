"""EP-25 — M2: files take authority (FUSE). THE CAMPAIGN CRUX.

The acceptance battery, named before the code (design/36 §8; the EP's own list).

  T-CUSTODY-IS-DERIVED   kill the derived tree, inode and fd state; replay the record
                         alone; the mount serves identical content and namespace. THE
                         CRUX DETECTOR — the one leg a passthrough-with-a-log fails.
  T-RECORD-UPSTREAM      the interrupted-crossing pair: append-then-crash heals to
                         effect; crash-before-append leaves nothing; no
                         effect-without-record path exists.
  T-UNMODIFIED-PROGRAM   cat / ls / cp / git cannot tell the mount from a native one.
  T-SHADOW-DIFF          empty under the workload battery.
  T-DIVERGENCE-HALT      a seeded divergence halts the assume and records the citation;
                         no false halts across the battery. BOTH directions.
  T-UID-IS-EVIDENCE      provenance carries the uid; actor resolution is a fold; no
                         identity table exists.
  T-COALESCE-CITED       a coalesced write event cites the recorded policy; with the
                         policy absent, no coalescing occurs (fail-closed).
  T-CUSTODY-MATRIX       (seed) in a DISPOSABLE zero-trust world: no account / no grant /
                         wrong space / covered, over open-write-unlink.
  T-ASOF-NATIVE          a directory answered as of a past T matches the replayed truth.
  T-RATE-GOVERNANCE      (custody scale) CACHE-only calls gain the store nothing;
                         DECISION and LAW rows each produce their covering record.
  T-FOLD-AT-RATE         (custody scale) the fold's inputs track governance, and a cached
                         answer is coherent-or-refuse.
  T-NO-STORED-TABLE      (custody scale) no permission table, no stored complement, no
                         identity table, on any path this EP adds.
  T-OPENNESS-UNTOUCHED   the founding openness grant is byte-intact.
  T-SEEDED-CITATIONS     every rule name this EP's ops and refusal paths cite resolves to
                         a record in the founding (ADDENDUM 4, the owner's containment line).
  T-PRESCRIPTIVE-IS-LAW  a permission-bearing attribute write records as LAW; every other
                         attribute write records as DECISION (ADDENDUM 3).

ADDENDUM 9's directed amend pass adds two, and its C4 judgement adds a third:

  T-LOCK-IS-RECORDED     a granted lock appends a rule-citing decision; a denied lock appends
                         a rule-citing refusal with the POSIX errno unchanged at the port.
                         Both directions, and the column proved able to fail (C1).
  T-UNLINK-READS-AS-UNLINK  the record of unlinking an open file shows the UNLINK decision,
                         with the port's rename-aside as mechanism beneath it; replay and the
                         POSIX contract both unchanged (C2).
  T-FIFO-IS-NOT-A-DEVICE a fifo is served and recorded (a name and a type; its data path is
                         the kernel's own pipe); a device node is refused with EPERM because
                         capability is EP-29's. The judgement C4 assigned to the builder,
                         written down as a test rather than as a sentence.

THE WORLD STAYS OPEN. Where a test narrows anything it does so inside a DISPOSABLE world
built for that test and thrown away with it; the live openness grant is never touched, and
T-OPENNESS-UNTOUCHED is what proves it.
"""

import errno
import json
import os
import shutil
import stat as statmod
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
# The FUSE adapter (fusepy over libfuse2) is staged in the lab, exactly as the campaign-1
# stepping-stone runner found it and as EP-21 stood it up. It stays OUTSIDE the zero-dependency
# core by the D9 precedent: the core is stdlib, the bridge adapter may bind libfuse. Its
# residence in a home directory rather than as a declared dependency is an honest cap and is
# raised with this EP — a test that depends on `~` is a test that can pass or vanish for
# reasons nothing in the repository states.
sys.path.insert(0, os.path.expanduser("~/gov-lab"))

from bridge import custody                                           # noqa: E402
from founding.install import load_pack, op_definitions, records      # noqa: E402
from kernel.errors import OpError                                    # noqa: E402

try:
    from fuse import FuseOSError                                     # noqa: E402
    from bridge.mount import build_mount                             # noqa: E402
    FUSEPY = None
except ImportError as exc:                                           # pragma: no cover
    FuseOSError = None
    build_mount = None
    FUSEPY = str(exc)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")
MOTHER = "space:root"


@unittest.skipIf(FUSEPY, "the fusepy adapter is not on this machine: %s" % FUSEPY)
class _Mount(unittest.TestCase):
    """A composed kernel and a custody server over it, in a disposable directory. The FUSE
    Operations object is driven DIRECTLY here — the same object `bridge.mount` hands to
    libfuse, so nothing in this file exercises a differently-composed mount than the one
    that runs. The kernel-mounted case is T-UNMODIFIED-PROGRAM's, below."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "rec.jsonl")
        self.fs, self.store, self.gate, self.views, self.blobs = build_mount(
            self.record, os.path.join(self.dir, "blobs"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    # ---- driving the mount the way the kernel would -----------------------------------
    def write_file(self, path, data, perm=0o644):
        fh = self.fs.create(path, perm)
        self.fs.write(path, data if isinstance(data, bytes) else data.encode(), 0, fh)
        self.fs.flush(path, fh)
        self.fs.release(path, fh)
        return fh

    def read_file(self, path):
        fh = self.fs.open(path, os.O_RDONLY)
        out = self.fs.read(path, 1 << 20, 0, fh)
        self.fs.release(path, fh)
        return out

    _rounds = 0

    def workload(self, n=12):
        """The battery every 'holds under load' claim is measured against. RE-RUNNABLE: each
        round works in its own subtree, so calling it twice exercises more of the namespace
        rather than colliding with the last round's names."""
        self._rounds += 1
        root = "/w%d" % self._rounds
        self.fs.mkdir(root, 0o755)
        for i in range(n):
            self.write_file("%s/f%d.txt" % (root, i), "line %d\n" % i * 3)
        self.fs.mkdir(root + "/sub", 0o755)
        for i in range(0, n, 3):
            self.fs.link("%s/sub/h%d.txt" % (root, i), "%s/f%d.txt" % (root, i))
            self.fs.symlink("%s/sub/s%d.txt" % (root, i), "f%d.txt" % i)
        for i in range(0, n, 4):
            self.fs.rename("%s/f%d.txt" % (root, i), "%s/moved%d.txt" % (root, i))
        for i in range(1, n, 5):
            if self.fs.state.exists("%s/f%d.txt" % (root, i)):
                self.fs.unlink("%s/f%d.txt" % (root, i))
        for i in range(2, n, 5):
            if self.fs.state.exists("%s/f%d.txt" % (root, i)):
                self.fs.chmod("%s/f%d.txt" % (root, i), 0o600)
        if self.fs.state.exists(root + "/f3.txt"):
            self.fs.truncate(root + "/f3.txt", 4)
        return root


# =============================================================================================
# T-CUSTODY-IS-DERIVED — the crux detector
# =============================================================================================

class TestCustodyIsDerived(_Mount):
    def test_kill_the_derived_state_replay_the_record_serve_identically(self):
        """THE ONE LEG THE JOURNALING TEMPLATE FAILS. A passthrough filesystem with a log
        bolted on passes every syscall row and dies here, because its truth lives in the host
        filesystem and the record is decoration. Kill the tree, the inodes and the fd table;
        rebuild from the append-only record ALONE; the same filesystem comes back."""
        self.workload()
        served = self.fs.state.snapshot()

        # kill everything derived
        self.fs.state = custody.CustodyState()
        self.fs._open, self.fs._burst, self.fs._reads = {}, {}, {}
        self.assertEqual(self.fs.state.names, {"/": 1}, "the derived tree survived being killed")

        # replay the record alone
        self.fs._rebuild_from_record()
        self.assertEqual(self.fs.state.snapshot(), served)

    def test_a_second_mount_over_the_same_record_serves_the_same_filesystem(self):
        """The remount half: a completely fresh process-equivalent, given only the record file
        and the blobs, serves byte-identical content and an identical namespace."""
        self.workload()
        before = {p: (self.read_file(p) if self.fs.state.lookup(p).kind == custody.KIND_FILE
                      else None)
                  for p in sorted(self.fs.state.names) if p != "/"}
        snapshot = self.fs.state.snapshot()

        fs2, store2, _g, _v, _b = build_mount(self.record, os.path.join(self.dir, "blobs"))
        self.assertEqual(fs2.state.snapshot(), snapshot)
        after = {}
        for p in sorted(fs2.state.names):
            if p == "/":
                continue
            node = fs2.state.lookup(p)
            after[p] = None
            if node.kind == custody.KIND_FILE:
                fh = fs2.open(p, os.O_RDONLY)
                after[p] = fs2.read(p, 1 << 20, 0, fh)
                fs2.release(p, fh)
        self.assertEqual(after, before)

    def test_the_mount_never_asks_the_host_filesystem_what_a_file_is(self):
        """The structural half, and the reason the first two tests can be trusted. The blob
        directory is the ONLY host path the custody server reads, and it is read by the HASH
        THE RECORD CARRIES. Remove every blob and the namespace still answers — names, modes,
        link counts, sizes — because those live in the record and not on a disk."""
        self.workload()
        names = dict(self.fs.state.names)
        modes = {p: self.fs.getattr(p)["st_mode"] for p in names if p != "/"}
        shutil.rmtree(os.path.join(self.dir, "blobs"))
        fs2, *_ = build_mount(self.record, os.path.join(self.dir, "blobs"))
        self.assertEqual(dict(fs2.state.names), names)
        self.assertEqual({p: fs2.getattr(p)["st_mode"] for p in names if p != "/"}, modes)


# =============================================================================================
# T-RECORD-UPSTREAM — the interrupted-crossing pair, exercised at the seam, both sides
# =============================================================================================

class TestRecordUpstream(_Mount):
    def test_the_reply_never_precedes_the_durable_append(self):
        """Instrument the seam: for every governed act, capture the record's length at the
        moment the effect is released. The store's append fsyncs before returning, so a
        served state that moved while the record had not is effect-without-record."""
        seen = []
        real = self.fs._act

        def watched(op, **params):
            before = len(self.store.events)
            rec = real(op, **params)
            seen.append((op, before, len(self.store.events), rec["seq"]))
            return rec
        self.fs._act = watched
        self.workload(6)
        self.fs._act = real
        self.assertTrue(seen)
        for op, before, after, seq in seen:
            self.assertGreater(after, before, "%s released its effect appending nothing" % op)
            self.assertLessEqual(seq, after)

    def test_append_then_crash_heals_record_to_effect(self):
        """Interrupted AFTER the append and BEFORE the derived state moved: the record stands,
        and restart completes the effect — because the effect IS a fold of the record."""
        self.write_file("/a.txt", "one")
        # the crash: the record is appended, the derived cache never learns of it
        self.store._listeners = []
        rec = self.gate.execute("FILE-CREATE", "uid:0", {"path": "/healed.txt", "inode": 99})
        self.assertIsNotNone(rec)
        self.assertNotIn("/healed.txt", self.fs.state.names, "the cache saw an append it should not have")
        # restart
        fs2, *_ = build_mount(self.record, os.path.join(self.dir, "blobs"))
        self.assertIn("/healed.txt", fs2.state.names, "restart did not heal record -> effect")

    def test_crash_before_the_append_leaves_nothing_in_record_or_effect(self):
        """The other direction. A refusal at the gate is a crossing that did not complete: the
        act's own record never lands, the served state never moves, and what the record DOES
        gain is the rule-citing refusal — cannot-do-lawfully AND cannot-do-quietly."""
        self.write_file("/b.txt", "two")
        before_names = dict(self.fs.state.names)
        before_len = len(self.store.events)
        with self.assertRaises(OpError):
            self.gate.execute("FILE-CREATE", "uid:0", {})     # nonconforming: no path
        self.assertEqual(dict(self.fs.state.names), before_names, "served state moved on a refused act")
        gained = [e["action"] for e in self.store.events[before_len:]]
        # op-refused, plus the two mutually-blind audit-stream mirrors that witness it. What
        # must NOT be there is any custody decision: the act left no effect and no record of one.
        self.assertIn("op-refused", gained)
        self.assertEqual([a for a in gained if a in custody.CUSTODY_ACTIONS], [])
        self.assertEqual(self.store.events[before_len]["rule_cited"], "AR-2")

    def test_a_write_whose_record_refuses_does_not_release_its_bytes(self):
        """The write path's own version: if the covering decision cannot be appended, the burst
        is NOT dropped and the effect is not released. The bytes stay un-durable, which is
        exactly what POSIX promises about an un-fsynced write."""
        self.write_file("/c.txt", "start")
        fh = self.fs.open("/c.txt", os.O_RDWR)
        self.fs.write("/c.txt", b"XXXX", 0, fh)
        real = self.gate.execute

        def refusing(name, actor, params=None):
            if name == "FILE-WRITE":
                self.gate.refuse(actor, name, "FS-LAW-PERM", "seeded refusal at the write seam")
            return real(name, actor, params)
        self.gate.execute = refusing
        with self.assertRaises(FuseOSError):
            self.fs.flush("/c.txt", fh)
        self.gate.execute = real
        self.assertIn(fh, self.fs._burst, "the burst was dropped though its record never landed")
        # and the record shows the refusal, cited
        refusals = [e for e in self.store.events if e["action"] == "op-refused"]
        self.assertEqual(refusals[-1]["rule_cited"], "FS-LAW-PERM")


# =============================================================================================
# T-SHADOW-DIFF and T-DIVERGENCE-HALT — both failure directions
# =============================================================================================

class TestShadowDiffAndHalt(_Mount):
    def test_shadow_diff_is_empty_under_the_workload(self):
        self.workload(20)
        self.assertIsNone(self.fs.shadow_diff())
        self.assertIsNone(self.fs.halted)

    def test_no_false_halt_across_the_battery(self):
        """The SECOND failure direction, and the one an eager guard fails: a halt raised where
        the two derivations agree would block a lawful assume. The mount stays live through the
        whole battery and keeps serving."""
        for _ in range(3):
            self.workload(8)
            self.fs.state = custody.fold(self.store.all())   # a quiescent point
            self.fs._shadow_check()
            self.assertIsNone(self.fs.halted, "a false halt blocked a lawful assume")
        self.assertGreater(self.fs.counters["shadow_checks"], 0, "the check never ran")

    def test_a_seeded_divergence_halts_the_assume_and_records_the_citation(self):
        """The FIRST direction. Corrupt the served state so it no longer equals what the record
        derives, then let the mount check itself."""
        root = self.workload(6)
        self.fs.state.names[root + "/ghost.txt"] = 4242       # a name no record ever created
        diff = self.fs._shadow_check()
        self.assertTrue(diff, "the divergence was not seen")
        self.assertEqual(self.fs.halted, "shadow-diff")
        halts = [e for e in self.store.events if e["action"] == "CUSTODY-HALT"]
        self.assertEqual(len(halts), 1)
        self.assertEqual(halts[0]["rule_cited"], "FS-LAW-DIVERGENCE-HALT")

    def test_a_halted_mount_refuses_state_changing_calls_and_still_serves_reads(self):
        root = self.workload(4)
        self.write_file(root + "/readable.txt", "still here")
        self.fs.halt("seeded", "a test halt")
        self.assertEqual(self.fs.halted, "seeded")
        with self.assertRaises(FuseOSError) as cm:
            self.fs.mkdir(root + "/after", 0o755)
        self.assertEqual(cm.exception.errno, errno.EROFS)
        with self.assertRaises(FuseOSError) as cm:
            self.write_file(root + "/new.txt", "nope")
        self.assertEqual(cm.exception.errno, errno.EROFS)
        # READ-ONLY MEANS NO STATE CHANGE, NOT NO RECORDING: a halted mount still serves reads,
        # and the open that serves them is still the recorded custody grant it always was.
        self.assertEqual(self.read_file(root + "/readable.txt"), b"still here")


# =============================================================================================
# T-UID-IS-EVIDENCE — the second named wrong reference, refused
# =============================================================================================

class TestUidIsEvidence(_Mount):
    def test_provenance_carries_the_uid_the_port_asserted(self):
        self.fs.mkdir("/p", 0o755)
        rec = [e for e in self.store.events if e["action"] == "FILE-MKDIR"][-1]
        prov = dict(rec["provenance"])
        # THE RECORD CARRIES WHAT THE PORT ASSERTED, which is the whole claim — not what this
        # process happens to be. Driven directly, libfuse's context is unset and reads 0/0/0;
        # driven through the kernel it is the calling process's real uid, and that case is
        # T-UNMODIFIED-PROGRAM's. Comparing against the port's own answer is what tests the
        # recording; comparing against os.getuid() would test the harness.
        uid, gid, _pid = self.fs._ctx()
        self.assertEqual(prov["uid"], uid)
        self.assertEqual(prov["gid"], gid)
        self.assertEqual(prov["source"], "fuse-port")
        self.assertEqual(prov["window"], "fuse-port@1")

    def test_actor_resolution_is_a_fold_over_recorded_mapping_acts(self):
        """No table. The mapping is recorded ACTS and the answer is recomputed every act, so
        a mapping recorded now changes who the NEXT act says it was — and changes it by
        derivation rather than by anyone updating a row."""
        uid = self.fs._ctx()[0]
        self.assertEqual(self.fs._actor(uid), "uid:%d" % uid)
        self.gate.execute("CREATE-ACCOUNT", "owner",
                          {"account_id": "ann", "actor_class": "human"})
        self.gate.execute("MAP-UID", "owner", {
            "uid": uid, "account": "ann",
            "provenance": {"asserted_by": "owner", "source": "test", "could_read": []}})
        self.assertEqual(self.fs._actor(uid), "ann")
        self.fs.mkdir("/after-mapping", 0o755)
        rec = [e for e in self.store.events if e["action"] == "FILE-MKDIR"][-1]
        self.assertEqual(rec["actor"], "ann")
        self.assertEqual(dict(rec["provenance"])["asserted_by"], "ann")

    def test_a_later_mapping_supersedes_and_nothing_was_updated(self):
        uid = self.fs._ctx()[0]
        for who in ("ann", "bob"):
            self.gate.execute("CREATE-ACCOUNT", "owner",
                              {"account_id": who, "actor_class": "human"})
            self.gate.execute("MAP-UID", "owner", {
                "uid": uid, "account": who,
                "provenance": {"asserted_by": "owner", "source": "test", "could_read": []}})
        self.assertEqual(self.fs._actor(uid), "bob")
        # BOTH mapping acts survive: supersession is a later record, never an edit
        acts = self.store.by_action("MAP-UID")
        self.assertEqual([(e.get("payload") or {}).get("account") for e in acts], ["ann", "bob"])


# =============================================================================================
# T-COALESCE-CITED — the calibration is visible, proposed, and cited; never silent
# =============================================================================================

class TestCoalesceCited(_Mount):
    def test_a_coalesced_write_event_cites_the_recorded_policy(self):
        fh = self.fs.create("/many.txt", 0o644)
        for i in range(10):
            self.fs.write("/many.txt", b"%02d" % i, i * 2, fh)
        self.fs.flush("/many.txt", fh)
        self.fs.release("/many.txt", fh)
        writes = [e for e in self.store.events if e["action"] == "FILE-WRITE"]
        self.assertEqual(len(writes), 1, "ten writes produced %d events" % len(writes))
        p = dict(writes[0]["payload"])
        self.assertEqual(p["coalesced_events"], 10)
        self.assertEqual(p["coalescing_policy"], "FS-WRITE-COALESCING")
        self.assertIn("FS-WRITE-COALESCING", self.views.active_rules())
        self.assertEqual(self.read_file("/many.txt"), b"".join(b"%02d" % i for i in range(10)))

    def test_with_the_policy_absent_no_coalescing_occurs(self):
        """FAIL-CLOSED to one event per write. Recording MORE is never the defect K3 names, so
        the direction an absent policy takes is the safe one. The policy is removed inside this
        DISPOSABLE world only."""
        self.fs.views.policy_value = lambda key, as_of=None: None    # the policy is not recorded
        fh = self.fs.create("/nocoal.txt", 0o644)
        for i in range(5):
            self.fs.write("/nocoal.txt", b"%d" % i, i, fh)
        self.fs.flush("/nocoal.txt", fh)
        self.fs.release("/nocoal.txt", fh)
        writes = [e for e in self.store.events if e["action"] == "FILE-WRITE"]
        self.assertEqual(len(writes), 5)
        for w in writes:
            self.assertIsNone(dict(w["payload"])["coalescing_policy"])

    def test_every_byte_is_content_addressed_either_way(self):
        """What the policy changes is how many EVENTS carry the bytes, never whether the bytes
        are carried (design/10 §11.4 — a named calibration, never a silent loss)."""
        fh = self.fs.create("/bytes.txt", 0o644)
        payload = b"".join(b"%03d" % i for i in range(50))
        for i in range(50):
            self.fs.write("/bytes.txt", b"%03d" % i, i * 3, fh)
        self.fs.flush("/bytes.txt", fh)
        self.fs.release("/bytes.txt", fh)
        node = self.fs.state.lookup("/bytes.txt")
        self.assertEqual(self.blobs.get(node.content_hash), payload)
        self.assertEqual(self.read_file("/bytes.txt"), payload)


# =============================================================================================
# T-ASOF-NATIVE — the ship-alone value of this stance
# =============================================================================================

class TestAsOfNative(_Mount):
    def test_a_directory_answered_as_of_a_past_time_matches_the_replayed_truth(self):
        self.fs.mkdir("/hist", 0o755)
        self.write_file("/hist/a.txt", "first")
        mark = len(self.store.events)
        then = custody.fold(self.store.all(mark)).snapshot()
        self.write_file("/hist/b.txt", "second")
        self.fs.unlink("/hist/a.txt")
        self.assertNotIn("/hist/a.txt", self.fs.state.names)
        self.assertIn("/hist/b.txt", self.fs.state.names)
        past = custody.fold(self.store.all(mark))
        self.assertEqual(past.snapshot(), then)
        self.assertIn("/hist/a.txt", past.names)
        self.assertNotIn("/hist/b.txt", past.names)

    def test_content_as_of_a_past_time_is_the_bytes_that_were_there(self):
        self.write_file("/v.txt", "version one")
        mark = len(self.store.events)
        fh = self.fs.open("/v.txt", os.O_RDWR)
        self.fs.write("/v.txt", b"version two", 0, fh)
        self.fs.flush("/v.txt", fh)
        self.fs.release("/v.txt", fh)
        past = custody.fold(self.store.all(mark))
        self.assertEqual(self.blobs.get(past.lookup("/v.txt").content_hash), b"version one")
        self.assertEqual(self.read_file("/v.txt"), b"version two")

    def test_the_blobs_history_persists_when_the_last_link_drops(self):
        """Deletion is NAMESPACE REMOVAL. The POSIX contract stays exact for the living
        namespace and the ledger keeps the history — which is the whole of "show me this
        directory as of last Tuesday"."""
        self.write_file("/gone.txt", "still recoverable")
        mark = len(self.store.events)
        self.fs.unlink("/gone.txt")
        with self.assertRaises(FuseOSError) as cm:
            self.fs.getattr("/gone.txt")
        self.assertEqual(cm.exception.errno, errno.ENOENT)
        past = custody.fold(self.store.all(mark))
        self.assertEqual(self.blobs.get(past.lookup("/gone.txt").content_hash),
                         b"still recoverable")


# =============================================================================================
# T-RATE-GOVERNANCE (custody scale) — recording tracks governance, never operation
# =============================================================================================

class TestRateGovernance(_Mount):
    def test_cache_only_calls_gain_the_store_nothing(self):
        """The design/10 §6 rows decide it: getattr, readdir, access, readlink, statfs,
        getxattr and listxattr are CACHE-only, and a CACHE-only call that appended is exactly
        what this row catches. Recording LESS is never the resolution — so the DECISION half
        below is asserted in the same test class."""
        self.workload(10)
        paths = [p for p in self.fs.state.names if p != "/"]
        before = len(self.store.events)
        for _ in range(20):
            for p in paths:
                self.fs.getattr(p)
                self.fs.access(p, os.R_OK)
                node = self.fs.state.lookup(p)
                if node.kind == custody.KIND_DIR:
                    self.fs.readdir(p, None)
                elif node.kind == custody.KIND_LINK:
                    self.fs.readlink(p)
                self.fs.listxattr(p)
            self.fs.statfs("/")
        self.assertEqual(len(self.store.events), before,
                         "CACHE-only traffic appended %d record(s)"
                         % (len(self.store.events) - before))
        self.assertGreater(self.fs.counters["cache"], 500, "the traffic did not actually run")

    def test_each_decision_row_produces_exactly_its_covering_record(self):
        cases = [
            (lambda: self.fs.mkdir("/r/d", 0o755), "FILE-MKDIR"),
            (lambda: self.fs.create("/r/f", 0o644), "FILE-CREATE"),
            (lambda: self.fs.chmod("/r/f", 0o600), "FILE-PERM"),
            (lambda: self.fs.symlink("/r/s", "f"), "FILE-SYMLINK"),
            (lambda: self.fs.link("/r/h", "/r/f"), "FILE-LINK"),
            (lambda: self.fs.rename("/r/h", "/r/h2"), "FILE-RENAME"),
            (lambda: self.fs.unlink("/r/h2"), "FILE-UNLINK"),
            (lambda: self.fs.setxattr("/r/f", "user.k", b"v", 0), "FILE-XATTR-SET"),
            (lambda: self.fs.removexattr("/r/f", "user.k"), "FILE-XATTR-REMOVE"),
            (lambda: self.fs.truncate("/r/f", 0), "FILE-TRUNCATE"),
            (lambda: self.fs.rmdir("/r/x"), "FILE-RMDIR"),
        ]
        self.fs.mkdir("/r", 0o755)
        for run, action in cases:
            if action == "FILE-RMDIR":
                self.fs.mkdir("/r/x", 0o755)
            before = len(self.store.events)
            run()
            gained = [e["action"] for e in self.store.events[before:]]
            self.assertIn(action, gained, "%s produced %s" % (action, gained))
            self.assertEqual(
                [a for a in gained if custody.CUSTODY_CLASS_MAP.get(a) == "DECISION"
                 and a != action], [],
                "%s appended a second DECISION: %s" % (action, gained))
        for e in self.store.events:
            if e["action"] in custody.CUSTODY_CLASS_MAP and e["action"] != "op-refused":
                self.assertTrue(e["rule_cited"], "%s cites no rule" % e["action"])

    def test_read_traffic_appends_nothing_per_read(self):
        """STREAM is the audit AGGREGATE, never a record per read — and the caller's bytes are
        exact regardless (§11.5)."""
        self.write_file("/big.txt", "x" * 4096)
        before = len(self.store.events)
        fh = self.fs.open("/big.txt", os.O_RDONLY)
        got = b""
        for off in range(0, 4096, 64):
            got += self.fs.read("/big.txt", 64, off, fh)
        self.fs.release("/big.txt", fh)
        self.assertEqual(got, b"x" * 4096, "the caller did not receive exact bytes")
        appended = [e["action"] for e in self.store.events[before:]]
        self.assertNotIn("FILE-READ-AGGREGATE", appended,
                         "64 reads under the window appended an aggregate")
        self.assertLessEqual(sum(1 for a in appended if a.startswith("FILE-")), 2)

    def test_the_read_aggregate_when_it_lands_is_stream_and_cites_the_policy(self):
        self.write_file("/agg.txt", "y" * 64)
        self.fs.views.policy_value = _policy_override(
            self.views, "files-read-aggregation",
            {"mode": "per-inode", "max_reads": 5, "max_bytes": 1 << 30, "closers": ["max_reads"]})
        fh = self.fs.open("/agg.txt", os.O_RDONLY)
        for _ in range(6):
            self.fs.read("/agg.txt", 8, 0, fh)
        self.fs.release("/agg.txt", fh)
        aggs = [e for e in self.store.events if e["action"] == "FILE-READ-AGGREGATE"]
        self.assertTrue(aggs)
        self.assertEqual(custody.CUSTODY_CLASS_MAP["FILE-READ-AGGREGATE"], "STREAM")
        self.assertEqual(aggs[0]["rule_cited"], "FS-READ-AGGREGATION")
        self.assertEqual(dict(aggs[0]["payload"])["reads"], 5)


def _policy_override(views, key, value):
    real = views.policy_value

    def fake(k, as_of=None):
        return value if k == key else real(k, as_of)
    return fake


# =============================================================================================
# T-FOLD-AT-RATE (custody scale) — the fold's inputs track governance; caches are coherent
# =============================================================================================

class TestFoldAtRate(_Mount):
    def test_custody_traffic_does_not_grow_what_the_authority_fold_reads(self):
        """A COUNTABLE, never a duration (the standing law W0 files). Thousands of custody
        records are operation, not governance, so the fold's input subset must not move; a
        grant is governance, so it must."""
        reads = lambda: len(self.store.governance_index().all())        # noqa: E731
        base = reads()
        self.workload(30)
        self.assertGreater(len(self.store.events), 150, "the workload did not actually run")
        self.assertEqual(reads(), base,
                         "custody traffic changed what the authority fold has to read")
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "z", "actor_class": "human"})
        self.gate.execute("GRANT", "owner", {"grant_id": "g1", "grantee": "z",
                                             "actions": ["FILE-OPEN"], "info": "*",
                                             "space": MOTHER})
        self.assertEqual(reads(), base + 1, "governance growth did not move the fold")

    def test_a_cached_fold_answer_is_coherent_with_the_record_or_refuses(self):
        """The R26 law at custody scale: a hop never lies. Invalidate the record a projection
        rests on and the next consultation recomputes or REFUSES — it never serves a subset it
        cannot prove."""
        from kernel.store import StaleIndex, is_governance_record
        self.workload(5)
        index = self.store.governance_index()
        index.all()                                       # built on first use, then current
        self.assertTrue(index.is_current())
        index.kill()
        self.assertEqual([e["seq"] for e in index.all()],
                         [e["seq"] for e in self.store.events if is_governance_record(e)])
        index._seen = len(self.store.events) + 500          # a stamp the record cannot support
        with self.assertRaises(StaleIndex):
            index.all()

    def test_the_custody_fold_itself_is_killable_and_rebuilds_identically(self):
        self.workload(12)
        snap = self.fs.state.snapshot()
        self.fs.state = custody.CustodyState()
        self.fs._rebuild_from_record()
        self.assertEqual(self.fs.state.snapshot(), snap)


# =============================================================================================
# T-NO-STORED-TABLE (custody scale) — the structure guard over everything this EP adds
# =============================================================================================

class TestNoStoredTable(_Mount):
    #: Everything the custody surface is allowed to hold. Each entry is a DERIVED cache of
    #: recorded decisions; none of them can hold a verdict, a permission set, a role expansion
    #: or a computed complement, because none of them has anywhere for one to live.
    #: DOCUMENTED FLIP, EP-28E W2 — `kids` and `paths` added, and this guard is the reason
    #: the addition had to be argued rather than made. It fired on the change, which is what
    #: an exhaustive enumeration is for: nothing gets a home in the custody state without a
    #: seat widening this line on purpose.
    #:
    #: WHY THESE TWO ARE ADMISSIBLE and a permission table is not. They hold no ANSWER.
    #: `kids` is parent-path → the basenames bound under it; `paths` is inode → the paths it
    #: is bound under. Both are the SAME binding set `names` already holds, keyed by the
    #: thing a read asks about instead of by the thing a lookup asks about — so neither can
    #: carry a verdict, because neither has a value shaped like one. A stored permission
    #: table is inadmissible because its value IS a computed verdict with no record behind
    #: it; an index whose value is a name is not that structure at any scale.
    #:
    #: AND THE PROOF IS NOT IN THIS COMMENT. Both are in `snapshot()`, so
    #: `test_the_custody_fold_itself_is_killable_and_rebuilds_identically` above — which
    #: predates this EP — now kills them and requires the replay to bring them back
    #: byte-identical. That is the test EP-28E ADDENDUM 1 §1.3 sets for telling derived
    #: state from a cache, and it was already in the suite; what changed is its subject.
    ALLOWED = {"names", "inodes", "kids", "paths", "next_ino", "applied"}

    def test_the_custody_state_holds_no_permission_answer_anywhere(self):
        self.workload(8)
        self.assertEqual(set(vars(self.fs.state)), self.ALLOWED)
        blob = json.dumps(self.fs.state.snapshot())
        for forbidden in ("covers", "permitted", "denied", "allow", "deny", "grants",
                          "complement", "capabilit", "role"):
            self.assertNotIn(forbidden, blob.lower(),
                             "the custody state carries %r — a permission answer has a home" % forbidden)

    def test_there_is_no_identity_table_on_any_path_this_ep_adds(self):
        """The second named wrong reference, guarded structurally rather than promised. The
        server holds NOTHING keyed by uid: the mapping lives in records and the answer is
        recomputed every act."""
        uid = self.fs._ctx()[0]
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "ann", "actor_class": "human"})
        self.gate.execute("MAP-UID", "owner", {
            "uid": uid, "account": "ann",
            "provenance": {"asserted_by": "owner", "source": "test", "could_read": []}})
        self.workload(4)
        for name, value in vars(self.fs).items():
            if not isinstance(value, dict):
                continue
            self.assertNotIn(uid, value.keys(),
                             "self.%s is keyed by uid — that is the identity table" % name)
            self.assertNotIn("ann", [v for v in value.values() if isinstance(v, str)],
                             "self.%s holds a resolved account — that is the identity table" % name)

    def test_the_bridge_source_declares_no_permission_or_identity_map(self):
        """The source-level half: nothing in this EP's own modules builds a dict from actor or
        uid to a verdict. Read as text, because a structure that does not exist is easier to
        prove absent than one that is merely unused today."""
        import bridge.custody as c
        import bridge.records_fs as r
        import bridge.mount as m
        for mod in (c, r, m):
            with open(mod.__file__, encoding="utf-8") as fh:
                src = fh.read()
            low = src.lower()
            for forbidden in ("self._perms =", "self._acl_cache", "self._uid_map",
                              "self._permissions", "self._covers_cache"):
                self.assertNotIn(forbidden, low,
                                 "%s builds %r" % (os.path.basename(mod.__file__), forbidden))


# =============================================================================================
# T-CUSTODY-MATRIX (seed) — the four columns, proven able to fail, in a DISPOSABLE world
# =============================================================================================

class TestCustodyMatrix(_Mount):
    """The four authority columns over open-write-unlink. The full matrix at OS scale is
    EP-33's; this is the seed that proves the columns CAN fail — a matrix with no findings
    must prove that before its no-findings result is trusted (DIGEST-C2 §4).

    THE WORLD IS NARROWED ONLY INSIDE THIS DISPOSABLE STORE, which tearDown deletes. The live
    openness grant is untouched and T-OPENNESS-UNTOUCHED proves it."""

    def narrow_to_zero(self):
        """Revoke the founding openness grant in THIS throwaway world, so the columns are
        evaluated against real authority rather than against openness. The id is the estate's
        own (`tools/mentor-probes/extinction_matrix_probes.py` narrows it exactly this way):
        the grant's identity is its record OBJECT, not a payload field."""
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.assertNotIn("grant:founding-openness", self.views.grants())

    def custody_act(self, actor, op="FILE-OPEN", **kw):
        params = dict({"path": "/m.txt", "inode": 7,
                       "provenance": {"asserted_by": actor, "source": "fuse-port",
                                      "could_read": [], "uid": 4242}}, **kw)
        return self.gate.execute(op, actor, params)

    def test_the_four_columns_over_a_custody_act(self):
        self.write_file("/m.txt", "matrix")
        self.narrow_to_zero()

        # column 1 — NO ACCOUNT: nothing founds this actor, so no chain reaches it
        with self.assertRaises(OpError) as c1:
            self.custody_act("nobody")
        self.assertEqual(c1.exception.rule, "ROOT-NEG-1")

        # column 2 — ACCOUNT, NO GRANT
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "ann", "actor_class": "human"})
        with self.assertRaises(OpError) as c2:
            self.custody_act("ann")
        self.assertEqual(c2.exception.rule, "ROOT-NEG-1")

        # column 3 — GRANT IN THE WRONG SPACE
        self.gate.execute("CREATE-SPACE", "owner", {"name": "elsewhere", "parent": MOTHER})
        self.gate.execute("GRANT", "owner", {"grant_id": "g-wrong", "grantee": "ann",
                                            "actions": ["FILE-OPEN"], "info": "*",
                                            "space": "space:elsewhere"})
        with self.assertRaises(OpError) as c3:
            self.custody_act("ann")
        self.assertEqual(c3.exception.rule, "ROOT-NEG-3")

        # column 4 — A COVERING GRANT: the act passes
        self.gate.execute("GRANT", "owner", {"grant_id": "g-ok", "grantee": "ann",
                                            "actions": ["FILE-OPEN", "FILE-WRITE", "FILE-UNLINK"],
                                            "info": "*", "space": MOTHER})
        rec = self.custody_act("ann")
        self.assertEqual(rec["action"], "FILE-OPEN")
        self.assertEqual(rec["actor"], "ann")

    def test_a_grant_one_dimension_too_narrow_still_refuses(self):
        """Proving the columns CAN fail: the covering grant minus the one action under test."""
        self.write_file("/m.txt", "matrix")
        self.narrow_to_zero()
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "bob", "actor_class": "human"})
        self.gate.execute("GRANT", "owner", {"grant_id": "g-narrow", "grantee": "bob",
                                            "actions": ["FILE-OPEN"], "info": "*",
                                            "space": MOTHER})
        self.custody_act("bob")                                    # covered
        with self.assertRaises(OpError) as e:
            self.custody_act("bob", op="FILE-UNLINK", path="/m.txt")
        self.assertEqual(e.exception.rule, "ROOT-NEG-3")

    def test_every_refusal_is_recorded_and_cites_its_rule(self):
        self.write_file("/m.txt", "matrix")
        self.narrow_to_zero()
        before = len(self.store.events)
        with self.assertRaises(OpError):
            self.custody_act("nobody")
        gained = self.store.events[before:]
        # The refusal, plus the two mutually-blind audit-stream mirrors that witness it — the
        # record does not go dark on a refusal, which is the point of mirroring it.
        self.assertEqual([e["action"] for e in gained],
                         ["op-refused", "dual-audit-record", "dual-audit-b-record"])
        self.assertTrue(gained[0]["refused"])
        self.assertEqual(gained[0]["rule_cited"], "ROOT-NEG-1")
        self.assertEqual(gained[0]["target"], "nobody")
        self.assertEqual([a for a in (e["action"] for e in gained)
                          if a in custody.CUSTODY_ACTIONS], [])


# =============================================================================================
# ADDENDUM 3 — prescriptive content is LAW, whichever syscall carries it
# =============================================================================================

class TestPrescriptiveIsLaw(_Mount):
    def test_a_permission_bearing_attribute_write_records_as_law(self):
        self.write_file("/acl.txt", "guarded")
        self.fs.setxattr("/acl.txt", "system.posix_acl_access", b"u::rw-,g::r--,o::---", 0)
        rec = [e for e in self.store.events if e["action"] == "FILE-XATTR-LAW"][-1]
        self.assertEqual(custody.CUSTODY_CLASS_MAP["FILE-XATTR-LAW"], "LAW")
        p = dict(rec["payload"])
        self.assertEqual(p["rule_id"], "acl:/acl.txt#system.posix_acl_access")
        self.assertEqual(p["space"], MOTHER)
        # it is a LAW-FAMILY record: the views fold recognises it by self-declaration
        from kernel.store import is_law_record
        self.assertTrue(is_law_record(rec))
        self.assertIn("acl:/acl.txt#system.posix_acl_access", self.views.active_rules())

    def test_a_security_namespace_write_is_the_same_class(self):
        self.write_file("/s.txt", "x")
        self.fs.setxattr("/s.txt", "security.selinux", b"label", 0)
        self.assertEqual(self.store.events[-1]["action"], "FILE-XATTR-LAW")

    def test_an_ordinary_attribute_write_records_as_decision(self):
        self.write_file("/o.txt", "x")
        self.fs.setxattr("/o.txt", "user.comment", b"just data", 0)
        rec = self.store.events[-1]
        self.assertEqual(rec["action"], "FILE-XATTR-SET")
        self.assertEqual(custody.CUSTODY_CLASS_MAP["FILE-XATTR-SET"], "DECISION")
        self.assertIsNone((dict(rec["payload"])).get("rule_id"))

    def test_the_split_is_by_attribute_namespace_and_is_data(self):
        self.assertTrue(custody.is_law_xattr("system.posix_acl_default"))
        self.assertTrue(custody.is_law_xattr("security.capability"))
        self.assertFalse(custody.is_law_xattr("user.anything"))
        self.assertFalse(custody.is_law_xattr("trusted.something"))
        self.assertEqual(custody.LAW_XATTR_PREFIXES, ("security.", "system.posix_acl_"))

    def test_the_acl_is_read_back_from_the_record_not_from_a_side_table(self):
        self.write_file("/rb.txt", "x")
        self.fs.setxattr("/rb.txt", "system.posix_acl_access", b"u::rw-", 0)
        self.assertEqual(self.fs.getxattr("/rb.txt", "system.posix_acl_access"), b"u::rw-")
        # and it survives killing everything derived, because it lives in the record
        self.fs.state = custody.CustodyState()
        self.fs._rebuild_from_record()
        self.assertEqual(self.fs.getxattr("/rb.txt", "system.posix_acl_access"), b"u::rw-")


# =============================================================================================
# ADDENDUM 4 — every rule name this EP cites resolves to a record in the founding
# =============================================================================================

class TestSeededCitations(unittest.TestCase):
    """The owner's containment line. EP-22 found that a record can cite a rule that does not
    exist and nothing catches it; the general fix lands at the campaign close. What is asserted
    here is that the class does not GROW through the crux: every rule name THIS EP's op
    definitions and refusal paths cite resolves to a record in the founding after the bump.

    Scoped to this EP's own additions. A pre-existing unseeded name elsewhere in the estate is
    a raise and not this EP's to fix — and the count of them is asserted below so that the ride
    is measured rather than merely mentioned."""

    #: The ops this EP creates or amends. Their citations are in scope.
    EP25_OPS = {
        "FILE-OPEN", "FILE-CLOSE", "FILE-TRUNCATE", "FILE-MKDIR", "FILE-RMDIR",
        "FILE-SYMLINK", "FILE-RENAME", "FILE-CHOWN", "FILE-TIMES", "FILE-XATTR-SET",
        "FILE-XATTR-REMOVE", "FILE-XATTR-LAW", "FILE-READ-AGGREGATE", "MAP-UID",
        "CUSTODY-HALT", "FILE-CREATE", "FILE-WRITE", "FILE-LINK", "FILE-UNLINK", "FILE-PERM",
        # ADDENDUM 9 C1: the lock ops, and the law they cite, enter with the same containment
        "FILE-LOCK", "FILE-UNLOCK",
    }
    #: Cited by ops this EP did NOT create, absent from the founding, and carried as a raise
    #: rather than fixed here. PINNED so the ride is measured: this set may SHRINK, and a name
    #: joining it is a finding that stops and raises.
    PRE_EXISTING_UNSEEDED = {
        "COMM-LAW-CONTRACT", "COMM-LAW-QUEUE", "COMM-LAW-SHARE-GRANT", "DEV-LAW-BIND",
        "MEM-LAW-ALLOC", "MEM-LAW-BUDGET", "MEM-LAW-EVICT", "MEM-LAW-PROTECT",
        "SCHED-LAW-ADMIT", "SCHED-LAW-HALT", "SCHED-LAW-KILL-CHAIN", "SCHED-LAW-ORDER",
        "SCHED-LAW-PRIORITY",
    }

    def setUp(self):
        self.pack = load_pack()
        self.seeded = {(r.get("payload") or {}).get("rule_id")
                       for r in records(self.pack)
                       if (r.get("payload") or {}).get("rule_id")}

    def test_every_rule_this_eps_ops_cite_is_a_record_in_the_founding(self):
        defs = op_definitions(self.pack)
        missing = {}
        for name in sorted(self.EP25_OPS):
            d = defs[name]
            cites = {d["law_cited"]}
            for c in d.get("checks") or []:
                for k in ("cite", "cite_cycle", "cite_missing"):
                    if c.get(k):
                        cites.add(c[k])
            for c in sorted(cites):
                if c not in self.seeded:
                    missing.setdefault(c, []).append(name)
        self.assertEqual(missing, {},
                         "these ops cite rule names the founding does not contain: %s" % missing)

    def test_the_three_files_laws_this_ep_seeded_are_records(self):
        for rid in ("FS-LAW-PERM", "FS-LAW-NAMESPACE", "FS-LAW-MOUNT",
                    "FS-LAW-DIVERGENCE-HALT", "FS-WRITE-COALESCING", "FS-READ-AGGREGATION",
                    "FS-LAW-LOCK"):
            self.assertIn(rid, self.seeded, "%s is cited but not seeded" % rid)

    def test_every_refusal_path_this_ep_creates_cites_a_seeded_rule(self):
        from bridge.records_fs import _ERRNO_BY_RULE
        for rule in _ERRNO_BY_RULE:
            if rule == "AR-2":
                # AR-2 is the GATE's own nonconforming-call citation and is the estate's
                # documented dangling name (eight sites, a campaign-1 review finding riding
                # three campaigns with its change already named). The mount does not mint it;
                # it TRANSLATES it to an errno, which is the one honest thing to do with a
                # citation someone else emits. Named here so the exemption is visible.
                self.assertNotIn(rule, self.seeded)
                continue
            self.assertIn(rule, self.seeded, "the mount maps an errno for unseeded %s" % rule)

    def test_the_pre_existing_ride_did_not_widen(self):
        """[EP-29 W1a, 2026-08-09 — AMENDED on the mentor's ruling. A documented flip with
        its cause. THE ROW ASSERTED SET IDENTITY WHERE ITS PURPOSE IS SET DIRECTION.]

        ASSERTED (EP-25): `cited - seeded` EQUALS `PRE_EXISTING_UNSEEDED` — thirteen names.
        SUPERSEDED: EP-29 W1a DECLARED `DEV-LAW-BIND` on 2026-08-09. It had been cited by
        `BIND-DEVICE` and `UNBIND` since campaign 1 and declared by no record in four
        campaigns. The class SHRANK to twelve and an EQUALITY reddened on the repair this row
        exists to protect.
        THE DEFECT IS THE ASSERTION, NOT THE LANDING — and this class already said so in its
        own words, twelve lines above, on the constant itself: "this set may SHRINK, and a
        name JOINING it is a finding that stops and raises." The constant declared a
        DIRECTION and the assertion encoded an IDENTITY. They disagreed inside one class, and
        the constant was right. The row's own NAME says `did_not_widen`.
        REMAINS TRUE and is now what the name always claimed — NON-INCREASE: no name may JOIN
        the unseeded-citation class through this ride. `PRE_EXISTING_UNSEEDED` is kept whole
        and untouched as the historical CEILING, so what the ride was is still readable and a
        repair does not edit the record of what it repaired.
        GIVEN UP: the ability to notice the class SHRINKING. Deliberate — a shrink is a
        seeding repair — and NOT lost from the estate: the survivor set is pinned by EQUALITY,
        which reds in BOTH directions, at
        `tests/test_ep29.py::TheDeviceLawIsDeclared::test_exactly_one_of_the_thirteen_was
        _repaired_and_the_twelve_are_pinned`, held by the pass that owns the repair. Read
        before this clause was written, not assumed."""
        cited = set()
        for r in records(self.pack):
            d = ((r.get("payload") or {}).get("definition") or {})
            if d.get("law_cited"):
                cited.add(d["law_cited"])
        joined = (cited - self.seeded) - self.PRE_EXISTING_UNSEEDED
        self.assertEqual(joined, set(),
                         "a name JOINED the unseeded-citation class through this ride: %s"
                         % sorted(joined))


# =============================================================================================
# T-OPENNESS-UNTOUCHED — the grant is byte-intact (the EP-17 precedent)
# =============================================================================================

@unittest.skipIf(FUSEPY, "needs the fusepy adapter for build_mount")
class TestOpennessUntouched(unittest.TestCase):
    def test_the_founding_openness_grant_is_byte_identical(self):
        pack = load_pack()
        step = [s for s in pack["steps"] if s["step"] == "10-founding-openness-grant"]
        self.assertEqual(len(step), 1)
        self.assertEqual(len(step[0]["records"]), 1)
        grant = step[0]["records"][0]
        # PINNED BYTE FOR BYTE, the EP-17 precedent. The whole-EP line asserts the openness
        # grant is untouched; this is that assertion with something to compare against, so a
        # single character moving in the founding's most consequential record fails here rather
        # than being noticed later by whoever narrows the world for real.
        self.assertEqual(grant, {
            "actor": "PC_RUNTIME",
            "action": "GRANT",
            "object": "grant:founding-openness",
            "rule_cited": "BOOT-INT",
            "payload": {
                "kind": "grant",
                "polarity": "+",
                "grantee": "*",
                "actions": "*",
                "info": "*",
                "space": "space:root",
                "enforcement": "inert",
                "text": "the mother space's founding openness recorded as explicit law: today's "
                        "open world as a grant anyone can read and later narrow space by space "
                        "(design/31 EP-17 transition policy). It enforces nothing at the founding.",
            },
        })

    def test_the_live_world_still_grants_everyone_everything(self):
        d = tempfile.mkdtemp()
        try:
            fs, store, gate, views, _b = build_mount(
                os.path.join(d, "r.jsonl"), os.path.join(d, "b"))
            grants = [g for g in views.grants().values() if g.get("grantee") == "*"]
            self.assertEqual(len(grants), 1)
            self.assertEqual(grants[0]["space"], MOTHER)
            self.assertEqual(list(grants[0]["actions"]), ["*"])
            self.assertTrue(views.covers("anyone-at-all", "FILE-OPEN", None, MOTHER))
        finally:
            shutil.rmtree(d, ignore_errors=True)


# =============================================================================================
# T-UNMODIFIED-PROGRAM — cat / ls / cp / git against a REAL kernel mount
# =============================================================================================

def _fuse_available():
    return os.path.exists("/dev/fuse") and (shutil.which("fusermount")
                                            or shutil.which("fusermount3"))


@unittest.skipUnless(_fuse_available() and not FUSEPY, "no /dev/fuse, fusermount, or fusepy on this machine")
class TestUnmodifiedProgram(unittest.TestCase):
    """THE M2 GATE LINE. Real unmodified programs, driven by the real kernel through the real
    VFS, against a mount whose every answer is a fold over the record. Nothing in this class
    calls the server directly: the kernel does."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.mnt = os.path.join(cls.dir, "mnt")
        cls.record = os.path.join(cls.dir, "rec.jsonl")
        os.makedirs(cls.mnt)
        env = dict(os.environ, PYTHONPATH=SRC)
        cls.proc = subprocess.Popen(
            [sys.executable, "-m", "bridge.mount", cls.record,
             os.path.join(cls.dir, "blobs"), cls.mnt],
            cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for _ in range(100):
            time.sleep(0.15)
            if _is_mounted(cls.mnt):
                break
        else:
            out = cls.proc.stdout.read().decode()[-2000:] if cls.proc.stdout else ""
            cls.tearDownClass()
            raise unittest.SkipTest("the mount did not come up: %s" % out)

    @classmethod
    def tearDownClass(cls):
        for tool in ("fusermount", "fusermount3"):
            if shutil.which(tool):
                subprocess.run([tool, "-u", cls.mnt], capture_output=True)
                break
        if getattr(cls, "proc", None):
            try:
                cls.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.proc.kill()
        shutil.rmtree(cls.dir, ignore_errors=True)

    def sh(self, cmd, **kw):
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              cwd=self.mnt, **kw)

    def test_it_is_a_real_fuse_mount_and_not_a_directory(self):
        """The check this suite exists because a human once skipped: every ABI observation
        below would pass identically against an ordinary host directory, and only this asks
        where the truth actually lives."""
        with open("/proc/self/mountinfo") as f:
            lines = [ln for ln in f if self.mnt in ln]
        self.assertTrue(lines, "nothing is mounted at the mountpoint")
        self.assertIn("fuse", lines[0])

    def test_cat_ls_and_the_shell_cannot_tell(self):
        self.assertEqual(self.sh("mkdir -p a/b/c").returncode, 0)
        self.assertEqual(self.sh("printf 'hello\\nworld\\n' > a/b/c/f.txt").returncode, 0)
        self.assertEqual(self.sh("cat a/b/c/f.txt").stdout, "hello\nworld\n")
        self.assertEqual(self.sh("ls a/b/c").stdout.strip(), "f.txt")
        self.assertEqual(self.sh("wc -l < a/b/c/f.txt").stdout.strip(), "2")
        self.assertEqual(self.sh("printf 'again\\n' >> a/b/c/f.txt").returncode, 0)
        self.assertEqual(self.sh("cat a/b/c/f.txt").stdout, "hello\nworld\nagain\n")
        self.assertEqual(self.sh("grep -c . a/b/c/f.txt").stdout.strip(), "3")

    def test_cp_and_diff_round_trip_a_real_tree(self):
        self.assertEqual(self.sh("mkdir -p src && "
                                 "for i in 1 2 3 4 5; do "
                                 "  head -c 4096 /dev/urandom | base64 > src/f$i.bin; "
                                 "done").returncode, 0)
        r = self.sh("cp -r src copy && diff -r src copy")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_toolchain_of_a_build_can_compile_on_the_mount(self):
        """A compiler and a linker exercise file semantics `cat` never reaches — O_TRUNC,
        rename-over-existing, many-small-writes, and reading a file it just wrote."""
        if not shutil.which("cc"):
            self.skipTest("no cc on this machine")
        self.assertEqual(self.sh(
            "mkdir -p build && printf '%s\\n' "
            "'#include <stdio.h>' 'int main(void){puts(\"built on the record\");return 0;}' "
            "> build/hello.c").returncode, 0)
        r = self.sh("cd build && cc -O1 -o hello hello.c && ./hello")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("built on the record", r.stdout)

    def test_git_cannot_tell(self):
        if not shutil.which("git"):
            self.skipTest("no git on this machine")
        r = self.sh(
            "mkdir -p repo && cd repo && git init -q . && "
            "git config user.email t@t && git config user.name t && "
            "echo one > a.txt && git add a.txt && git commit -qm one && "
            "echo two >> a.txt && git add a.txt && git commit -qm two && "
            "git log --oneline | wc -l && git status --porcelain | wc -l")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.split(), ["2", "0"])

    def test_an_unlinked_open_file_behaves_and_records_as_POSIX_says(self):
        """ADDENDUM 9 C2, driven by the REAL kernel: the caller unlinks a file it holds open.
        The name goes at once, the descriptor keeps reading, `fstat` still answers, and the
        record says UNLINK — not the rename the port performed to make that possible."""
        self.assertEqual(self.sh("mkdir -p u && printf 'bye' > u/f.txt").returncode, 0)
        r = self.sh("cd u && python3 -c \""
                    "import os;f=open('f.txt','rb');os.unlink('f.txt');"
                    "print(sorted(os.listdir('.')));print(f.read().decode());"
                    "print(os.fstat(f.fileno()).st_nlink);f.close();print(sorted(os.listdir('.')))\"")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.split("\n")[:4], ["[]", "bye", "0", "[]"])
        with open(self.record) as f:
            recs = [json.loads(ln) for ln in f if ln.strip()]
        unlinks = [e for e in recs if e["action"] == "FILE-UNLINK" and e["payload"].get("mechanism")]
        self.assertTrue(unlinks, "the caller's unlink is not in the record as an unlink")
        self.assertEqual(unlinks[-1]["payload"]["mechanism"], "fuse-rename-aside")
        self.assertTrue(unlinks[-1]["payload"]["hidden_path"].endswith(".txt") is False)
        # and no rename of the hidden name was recorded as a governance act
        self.assertEqual([e for e in recs if e["action"] == "FILE-RENAME"
                          and ".fuse_hidden" in json.dumps(dict(e["payload"]))], [])

    def test_a_fifo_is_served_and_a_device_node_is_refused(self):
        """ADDENDUM 9 C4's judgement, through the kernel: `mkfifo` works and the fifo is a
        fifo to `stat`; a character device is refused with EPERM because a device node is a
        capability reference and devices are EP-29."""
        r = self.sh("python3 -c \"import os,stat,errno;"
                    "os.mkfifo('p.fifo',0o644);"
                    "print(stat.S_ISFIFO(os.lstat('p.fifo').st_mode));"
                    "\nimport sys\ntry:\n os.mknod('dev.node', stat.S_IFCHR|0o600, 0)\n"
                    " print('SERVED')\nexcept OSError as e:\n print(errno.errorcode[e.errno])\"")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.split(), ["True", "EPERM"])
        self.assertEqual(self.sh("test -p p.fifo").returncode, 0)

    def test_a_lock_and_its_refusal_are_recorded_through_the_kernel(self):
        """ADDENDUM 9 C1, through the kernel and across TWO PROCESSES — the only way to
        drive a real conflict. The grant, the refusal and the release are all in the record,
        and the caller's errno is the POSIX one."""
        r = self.sh("python3 -c \"" + "\n".join([
            "import os,fcntl,struct,errno,time",
            "fd=os.open('l.txt',os.O_RDWR|os.O_CREAT,0o644)",
            "L=lambda t: struct.pack('hhllhh',t,0,0,0,0,0)",
            "fcntl.fcntl(fd,fcntl.F_SETLK,L(fcntl.F_WRLCK)); print('granted')",
            "r,w=os.pipe(); pid=os.fork()",
            "if pid==0:",
            " os.close(r); c=os.open('l.txt',os.O_RDWR)",
            " try: fcntl.fcntl(c,fcntl.F_SETLK,L(fcntl.F_WRLCK)); os.write(w,b'g')",
            " except OSError as e: os.write(w,errno.errorcode[e.errno].encode())",
            " time.sleep(0.2); os._exit(0)",
            "os.close(w); print(os.read(r,16).decode()); os.close(r)",
            "os.waitpid(pid,0); os.close(fd)"]) + "\"")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.split(), ["granted", "EAGAIN"])
        with open(self.record) as f:
            recs = [json.loads(ln) for ln in f if ln.strip()]
        grants = [e for e in recs if e["action"] == "FILE-LOCK"]
        refusals = [e for e in recs if e["action"] == "op-refused"
                    and dict(e["payload"]).get("op") == "FILE-LOCK"]
        releases = [e for e in recs if e["action"] == "FILE-UNLOCK"]
        self.assertTrue(grants and refusals and releases)
        self.assertEqual(grants[-1]["rule_cited"], "FS-LAW-LOCK")
        self.assertEqual(refusals[-1]["rule_cited"], "FS-LAW-LOCK")
        self.assertTrue(refusals[-1]["refused"])
        self.assertEqual(releases[-1]["rule_cited"], "FS-LAW-LOCK")

    def test_the_record_behind_the_mount_is_the_definitive(self):
        """Everything above ran through the kernel. This is what it left behind — and it is
        the answer to the question the first test in this class asks."""
        self.sh("sync")
        with open(self.record) as f:
            recs = [json.loads(ln) for ln in f if ln.strip()]
        actions = [e["action"] for e in recs]
        for expected in ("FILE-CREATE", "FILE-WRITE", "FILE-OPEN", "FILE-CLOSE", "FILE-MKDIR"):
            self.assertIn(expected, actions)
        for e in recs:
            if e["action"] in custody.CUSTODY_CLASS_MAP and e["action"] != "op-refused":
                self.assertTrue(e["rule_cited"], "%s cites no rule" % e["action"])
        # and the whole namespace re-derives from it alone
        rebuilt = custody.fold(recs)
        self.assertIn("/a/b/c/f.txt", rebuilt.names)


# =============================================================================================
# T-LOCK-IS-RECORDED (ADDENDUM 9 C1) — a lock is a governed act, and so is its refusal
# =============================================================================================

class TestLockIsRecorded(_Mount):
    """THE CAMPAIGN'S SHARPEST CUSTODY GAP, closed and guarded. Before this, `RecordsFS`
    implemented no lock operation, so libfuse never advertised the capability and the KERNEL
    granted locks locally: a caller held exclusivity the record had no knowledge of, and a
    denied lock — a refusal, `EAGAIN`, P4's own case — was issued by the kernel uncited and
    unrecorded. `mknod` refuses honestly; a lock SUCCEEDED and nothing recorded it, which is
    the distinction that made this the finding rather than a gap in a table."""

    def _lock(self, path, fh, cmd, ltype, start=0, length=0):
        """Drive the port's own `lock` operation exactly as libfuse drives it: a pointer to a
        `struct flock`. The struct is held in a local so it outlives the call."""
        import ctypes
        from bridge.records_fs import _Flock
        fl = _Flock(ltype, os.SEEK_SET, start, length, 0)
        rc = self.fs.lock(path, fh, cmd, ctypes.addressof(fl))
        return rc, fl

    def open_locked_file(self, path="/l.txt", data=b"0123456789"):
        self.write_file(path, data)
        return self.fs.open(path, os.O_RDWR)

    def test_the_flock_structure_this_port_reads_is_the_platforms_own(self):
        """A misread `struct flock` grants the wrong bytes SILENTLY, so the layout is
        asserted rather than trusted: libfuse hands over a pointer and this port reads it."""
        import ctypes
        from bridge.records_fs import _Flock
        self.assertEqual(ctypes.sizeof(_Flock), 32)
        self.assertEqual([(f, getattr(_Flock, f).offset) for f, _t in _Flock._fields_],
                         [("l_type", 0), ("l_whence", 2), ("l_start", 8),
                          ("l_len", 16), ("l_pid", 24)])

    def test_a_granted_lock_appends_a_rule_citing_decision(self):
        import fcntl
        fh = self.open_locked_file()
        rc, _fl = self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_WRLCK)
        self.assertEqual(rc, 0)
        rec = self.store.events[-1]
        self.assertEqual(rec["action"], "FILE-LOCK")
        self.assertEqual(rec["rule_cited"], "FS-LAW-LOCK")
        self.assertEqual(custody.CUSTODY_CLASS_MAP["FILE-LOCK"], "DECISION")
        p = dict(rec["payload"])
        self.assertEqual((p["ltype"], p["start"], p["length"]), ("write", 0, 0))
        # the port's evidence rides with it: the uid/gid/pid the KERNEL asserted (K6)
        self.assertEqual(rec["provenance"]["uid"], self.fs._ctx()[0])
        self.assertEqual(rec["provenance"]["pid"], p["owner"])

    def test_a_denied_lock_appends_a_rule_citing_refusal_and_the_posix_errno_is_unchanged(self):
        """THE HALF THAT WAS MISSING. The kernel was issuing this refusal, uncited."""
        import fcntl
        fh = self.open_locked_file()
        self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_WRLCK)
        other = self.fs._ctx()[2] + 1                      # a second holder, a second owner
        self.fs.locks.apply({"action": "FILE-LOCK", "payload": {
            "inode": self.fs._open[fh]["ino"], "owner": other, "ltype": "write",
            "start": 0, "length": 0, "path": "/l.txt"}})
        before = len(self.store.events)
        with self.assertRaises(FuseOSError) as e:
            self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_WRLCK)
        self.assertEqual(e.exception.errno, errno.EAGAIN)  # the LINUX errno, not a governance code
        gained = self.store.events[before:]
        self.assertEqual(gained[0]["action"], "op-refused")
        self.assertTrue(gained[0]["refused"])
        self.assertEqual(gained[0]["rule_cited"], "FS-LAW-LOCK")
        self.assertEqual(dict(gained[0]["payload"])["op"], "FILE-LOCK")

    def test_the_refusal_column_can_fail_in_both_directions(self):
        """A matrix with no findings must prove its columns can fail (DIGEST-C2 §4). Same
        range, different owner, incompatible modes -> refused. Same range, SAME owner ->
        granted, because a holder never conflicts with itself. Disjoint ranges -> granted.
        Two READ locks -> granted, because sharing is what a read lock is for."""
        import fcntl
        fh = self.open_locked_file()
        ino = self.fs._open[fh]["ino"]
        mine, other = self.fs._ctx()[2], self.fs._ctx()[2] + 1

        def held(owner, ltype, start=0, length=0):
            self.fs.locks.apply({"action": "FILE-LOCK", "payload": {
                "inode": ino, "owner": owner, "ltype": ltype, "start": start,
                "length": length, "path": "/l.txt"}})

        held(other, "write", 0, 10)
        self.assertIsNotNone(self.fs.locks.conflict(ino, mine, "write", 0, 10))  # refuses
        self.assertIsNotNone(self.fs.locks.conflict(ino, mine, "read", 4, 2))    # refuses
        self.assertIsNotNone(self.fs.locks.conflict(ino, mine, "write", 0, 0))   # to EOF
        self.assertIsNone(self.fs.locks.conflict(ino, other, "write", 0, 10))    # my own
        self.assertIsNone(self.fs.locks.conflict(ino, mine, "write", 40, 10))    # disjoint
        self.fs.locks.apply({"action": "FILE-UNLOCK",
                             "payload": {"inode": ino, "owner": other, "start": 0, "length": 10}})
        held(other, "read")
        self.assertIsNone(self.fs.locks.conflict(ino, mine, "read", 0, 0))       # shared
        self.assertIsNotNone(self.fs.locks.conflict(ino, mine, "write", 0, 0))   # not shared

    def test_a_zero_length_lock_reaches_the_end_of_the_file(self):
        """The one arithmetic mistake that would silently make whole-file locks stop
        conflicting: POSIX length 0 means to EOF, not an empty range."""
        self.assertTrue(custody._overlaps(0, 0, 4096, 10))
        self.assertTrue(custody._overlaps(4096, 10, 0, 0))
        self.assertFalse(custody._overlaps(0, 10, 10, 10))

    def test_an_explicit_unlock_and_a_close_both_record_their_release(self):
        import fcntl
        fh = self.open_locked_file()
        self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_WRLCK)
        self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_UNLCK)
        rec = self.store.events[-1]
        self.assertEqual(rec["action"], "FILE-UNLOCK")
        self.assertEqual(rec["rule_cited"], "FS-LAW-LOCK")
        self.assertEqual(dict(rec["payload"])["mechanism"], "fcntl-unlock")
        self.assertEqual(self.fs.locks.snapshot(), {})
        # and the POSIX rule: closing a descriptor for the file releases this owner's locks
        self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_WRLCK)
        self.fs.flush("/l.txt", fh)
        self.assertEqual(dict(self.store.events[-1]["payload"])["mechanism"],
                         "close-releases-locks")
        self.assertEqual(self.fs.locks.snapshot(), {})

    def test_a_query_appends_nothing_and_a_holder_never_conflicts_with_itself(self):
        """F_GETLK is CACHE-only (design/10 §6): it consults the fold and appends NOTHING —
        K3 at the lock path, counted rather than promised."""
        import fcntl
        fh = self.open_locked_file()
        self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_WRLCK)
        before = len(self.store.events)
        rc, fl = self._lock("/l.txt", fh, fcntl.F_GETLK, fcntl.F_WRLCK)
        self.assertEqual((rc, fl.l_type), (0, fcntl.F_UNLCK))
        self.assertEqual(len(self.store.events), before)
        # a conflicting holder is described back to the caller, still without appending
        self.fs.locks.apply({"action": "FILE-LOCK", "payload": {
            "inode": self.fs._open[fh]["ino"], "owner": self.fs._ctx()[2] + 1,
            "ltype": "write", "start": 8, "length": 16, "path": "/l.txt"}})
        rc, fl = self._lock("/l.txt", fh, fcntl.F_GETLK, fcntl.F_WRLCK)
        self.assertEqual((fl.l_type, fl.l_start, fl.l_len), (fcntl.F_WRLCK, 8, 16))
        self.assertEqual(len(self.store.events), before)

    def test_closing_an_unlocked_file_appends_nothing_extra(self):
        """The K3 direction that matters at rate: the release path is silent unless something
        was held, so ordinary file traffic pays nothing for locks existing."""
        fh = self.open_locked_file("/plain.txt", b"x")
        before = [e["action"] for e in self.store.events]
        self.fs.flush("/plain.txt", fh)
        self.assertEqual([e["action"] for e in self.store.events], before)

    def test_the_lock_table_is_a_fold_of_the_record_and_nothing_else(self):
        """No stored lock table: the running table and a table rebuilt by folding the record
        are ONE derivation over two sources (the EP-24B rule), so a divergence could only
        mean a record was missed."""
        import fcntl
        fh = self.open_locked_file()
        self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_WRLCK)
        self.assertEqual(custody.fold_locks(self.store.all()).snapshot(),
                         self.fs.locks.snapshot())
        self.assertNotEqual(self.fs.locks.snapshot(), {})
        self._lock("/l.txt", fh, fcntl.F_SETLK, fcntl.F_UNLCK)
        self.assertEqual(custody.fold_locks(self.store.all()).snapshot(),
                         self.fs.locks.snapshot())

    def test_bsd_flock_cannot_reach_this_port_and_the_reason_is_the_adapter(self):
        """THE HALF C1 COULD NOT CLOSE, written down as a test so it cannot be forgotten.

        BSD `flock(2)` never arrives at this mount: the fusepy adapter's `fuse_operations`
        declaration carries no `flock` entry, so libfuse never advertises the capability and
        the kernel settles BSD locks locally — exactly as it settled POSIX locks before this
        EP implemented `lock`. That is an ADAPTER limit and not a FUSE one (libfuse 2.9
        carries the entry), and it is raised rather than worked around, because re-declaring
        a third-party ABI struct to reach one function pointer is not a quiet fix.

        If the adapter ever gains the entry, THIS TEST FAILS and the work becomes possible —
        which is the point of asserting an absence rather than describing one."""
        import fuse as fusepy
        declared = [name for name, *_ in fusepy.fuse_operations._fields_]
        self.assertIn("lock", declared)          # the POSIX record-lock entry, now implemented
        self.assertNotIn("flock", declared,
                         "the adapter now declares flock — the BSD half of C1 is reachable "
                         "and files.flock's recording leg can be closed")
        self.assertTrue(hasattr(self.fs, "lock"))


# =============================================================================================
# T-UNLINK-READS-AS-UNLINK (ADDENDUM 9 C2) — the decision, with the mechanism beneath it
# =============================================================================================

class TestUnlinkReadsAsUnlink(_Mount):
    """The record's account of an unlink was a RENAME. Unlinking an open file makes the port
    rename it aside — POSIX-required, because a path-addressed filesystem cannot leave an open
    file nameless — and the record showed that MECHANISM in place of the DECISION the actor
    took. A reader who was not there saw a rename nobody asked for and no unlink at all."""

    HIDDEN = "/.fuse_hidden0000004800000001"

    def unlink_while_open(self, path="/u.txt", data=b"bye", mark=None):
        self.write_file(path, data)
        fh = self.fs.open(path, os.O_RDONLY)
        if mark is not None:
            mark.append(len(self.store.events))   # the caller's unlink starts HERE
        self.fs.rename(path, self.HIDDEN)     # exactly what libfuse does, and all it does
        return fh

    def test_the_record_shows_the_unlink_the_actor_decided_on(self):
        mark = []
        self.unlink_while_open(mark=mark)
        gained = [e for e in self.store.events[mark[0]:] if e["action"].startswith("FILE")]
        self.assertEqual([e["action"] for e in gained], ["FILE-UNLINK"])
        p = dict(gained[0]["payload"])
        self.assertEqual(p["path"], "/u.txt")
        self.assertEqual(p["mechanism"], "fuse-rename-aside")
        self.assertEqual(p["hidden_path"], self.HIDDEN)
        self.assertEqual(gained[0]["rule_cited"], "FS-LAW-NAMESPACE")

    def test_the_posix_contract_is_unchanged(self):
        fh = self.unlink_while_open()
        self.assertNotIn("/u.txt", self.fs.state.names)          # the name is gone at once
        self.assertNotIn("u.txt", self.fs.readdir("/", None))    # and gone from listings
        self.assertEqual(self.fs.read(self.HIDDEN, 10, 0, fh), b"bye")   # the fd still reads
        self.assertEqual(self.fs.getattr(self.HIDDEN, fh)["st_nlink"], 0)  # POSIX: no names
        with self.assertRaises(FuseOSError) as e:
            self.fs.getattr("/u.txt")
        self.assertEqual(e.exception.errno, errno.ENOENT)

    def test_the_aside_name_is_not_in_the_served_namespace(self):
        """STRICTLY TIGHTER THAN STOCK FUSE, which leaves the hidden file visible in `ls`.
        The alias is in-flight port state, like the fd table it belongs to; the record says
        the name was unlinked, and the namespace it derives agrees."""
        self.unlink_while_open()
        self.assertNotIn(self.HIDDEN, self.fs.state.names)
        self.assertNotIn(self.HIDDEN, custody.fold(self.store.all()).names)
        self.assertIn(custody._norm(self.HIDDEN), self.fs._hidden)

    def test_removing_the_alias_completes_the_mechanism_and_records_nothing(self):
        fh = self.unlink_while_open()
        self.fs.release(self.HIDDEN, fh)
        before = [e["action"] for e in self.store.events]
        self.fs.unlink(self.HIDDEN)
        self.assertEqual([e["action"] for e in self.store.events], before)
        self.assertEqual(self.fs._hidden, {})

    def test_replay_and_shadow_diff_are_unmoved(self):
        fh = self.unlink_while_open()
        self.fs.release(self.HIDDEN, fh)
        self.fs.unlink(self.HIDDEN)
        self.assertIsNone(self.fs.shadow_diff())
        self.assertEqual(custody.fold(self.store.all()).snapshot(), self.fs.state.snapshot())

    def test_an_ordinary_rename_is_still_a_rename(self):
        """The discriminator has to fail in the right direction too: four conditions have to
        hold at once, and a rename that is a caller's decision records as one."""
        self.write_file("/a.txt", "x")
        before = len(self.store.events)
        self.fs.rename("/a.txt", "/b.txt")
        self.assertEqual(self.store.events[before]["action"], "FILE-RENAME")
        # a hidden-shaped name whose source is NOT open is not the port's mechanism
        self.write_file("/c.txt", "x")
        before = len(self.store.events)
        self.fs.rename("/c.txt", "/.fuse_hidden00000048000000ff")
        self.assertEqual(self.store.events[before]["action"], "FILE-RENAME")
        # nor is a rename to a name outside the port's reserved form
        self.write_file("/d.txt", "x")
        fh = self.fs.open("/d.txt", os.O_RDONLY)
        before = len(self.store.events)
        self.fs.rename("/d.txt", "/.fuse_hidden_not_the_form")
        self.assertEqual(self.store.events[before]["action"], "FILE-RENAME")
        self.fs.release("/.fuse_hidden_not_the_form", fh)


# =============================================================================================
# T-FIFO-IS-NOT-A-DEVICE (ADDENDUM 9 C4's withheld judgement, written down)
# =============================================================================================

class TestFifoIsNotADevice(_Mount):
    """The judgement C4 assigned to this seat: a fifo is not a device node. A device node
    names a driver by major/minor and is a CAPABILITY reference, which is EP-29's; a fifo
    names nothing, and its data path is the kernel's own pipe, which never reaches a
    filesystem. So a fifo's whole custody is what this mount already governs — the name, the
    type and the permission — and it is served rather than marked."""

    def test_a_fifo_is_created_and_recorded_as_the_thing_it_is(self):
        self.fs.mknod("/p.fifo", statmod.S_IFIFO | 0o644, 0)
        rec = self.store.events[-1]
        self.assertEqual(rec["action"], "FILE-CREATE")
        self.assertEqual(dict(rec["payload"])["node_type"], "fifo")
        st = self.fs.getattr("/p.fifo")
        self.assertTrue(statmod.S_ISFIFO(st["st_mode"]))
        self.assertEqual(statmod.S_IMODE(st["st_mode"]), 0o644)
        self.assertEqual(st["st_size"], 0)

    def test_a_device_node_is_refused_because_capability_is_a_later_round(self):
        for mode in (statmod.S_IFCHR | 0o600, statmod.S_IFBLK | 0o600):
            with self.assertRaises(FuseOSError) as e:
                self.fs.mknod("/dev.node", mode, 0)
            self.assertEqual(e.exception.errno, errno.EPERM)
        self.assertNotIn("/dev.node", self.fs.state.names)

    def test_the_fifo_survives_killing_everything_derived(self):
        self.fs.mknod("/p.fifo", statmod.S_IFIFO | 0o644, 0)
        self.fs.mkdir("/d", 0o755)
        rebuilt = custody.fold(self.store.all())
        self.assertEqual(rebuilt.lookup("/p.fifo").kind, custody.KIND_FIFO)
        self.assertEqual(rebuilt.snapshot(), self.fs.state.snapshot())
        self.assertIsNone(self.fs.shadow_diff())

    def test_a_create_that_declared_no_type_is_a_regular_file(self):
        """Every create before the type was recorded made a regular file, and the fold says
        so — a record without the field is read, not guessed at."""
        st = custody.CustodyState()
        st.apply({"action": "FILE-CREATE", "payload": {"path": "/old.txt", "inode": 9}})
        self.assertEqual(st.lookup("/old.txt").kind, custody.KIND_FILE)
        st.apply({"action": "FILE-CREATE",
                  "payload": {"path": "/odd", "inode": 10, "node_type": "something-else"}})
        self.assertEqual(st.lookup("/odd").kind, custody.KIND_FILE)


# =============================================================================================
# ADDENDUM 10 — the last pass, DATA only. D1 landed; D2 could not, and the reason is a test.
# =============================================================================================

class TestChrootIsCacheOnly(unittest.TestCase):
    """T-CHROOT-IS-CACHE (ADDENDUM 10 D1, ruled at design/10 §11.1f).

    `chroot(2)` changes a PROCESS attribute. A filesystem is consulted for the path lookup
    and never for the root change, and no FUSE filesystem is offered the operation at all —
    so the row was asking a filesystem to record something it is never told about, and no
    correct mount could ever pass it. The files-group involvement is the LOOKUP, which is
    CACHE-only.

    THE HALF THIS TEST GUARDS IS THE ONE THAT WAS TEMPTING AND WRONG. Declaring the row
    NOT-GOVERNED also turns it green, and it turns the synthetic control fixture red at the
    same time, because the fixture produces what the row declares. Reclassifying is the
    amendment; declaring an outcome on an unamended row would have been a way of hiding it.
    So this asserts BOTH: the class is CACHE, and no outcome_class exists to sneak the
    expectation back in.
    """

    def _row(self):
        sys.path.insert(0, REPO)
        from tools.conformance.harness import rows as rows_mod
        _groups, compiled = rows_mod.load_all()
        return rows_mod, [r for r in compiled if r.row_id == "files.chroot"][0]

    def test_the_row_is_cache_only_and_declares_no_outcome_class(self):
        _rows_mod, row = self._row()
        self.assertEqual(list(row.recording_class), ["CACHE"])
        self.assertIsNone(
            row.outcome_class,
            "design/10 §11.1f reclassifies the row; it does not give it an outcome. An "
            "outcome_class here would turn the row green by declaring what it expects "
            "instead of by correcting what it is.",
        )

    def test_the_compiled_expectation_requires_no_record_at_all(self):
        """The class change has to reach the EXPECTATION, not just the label."""
        _rows_mod, row = self._row()
        exp = row.record_expectation
        self.assertEqual(exp.required_classes, ())
        self.assertFalse(exp.rule_citation_required)
        self.assertFalse(exp.coalescing_policy_required)


class TestStepLevelMarkingIsNotExpressible(unittest.TestCase):
    """T-STEP-MARKING-UNEXPRESSIBLE — the finding ADDENDUM 10 D2 ran into, asserted so it
    DIES the day the direction becomes executable.

    `design/10` §11.1e says "a row, OR A STEP within a row" is marked with its activating
    round and reported as not-run. Only the first half has a mechanism: `active` and
    `activates_at` are compiled at ROW level (`rows._compile_one`) and the runner drops an
    inactive row from the run. A step is a `{call, args}` pair that `probe.run_row` drives
    unconditionally, and `checks.check_abi` compares the observed step list against the
    pinned baseline positionally and then compares the whole final directory state.

    So there are exactly two row-data routes and both were MEASURED against the live mount
    rather than argued:

      declare it   a `marked` key on the step is accepted by the compiler and ignored by
                   the probe. The step still runs, still returns EPERM, and the row still
                   fails on the same two lines. A declaration that changes nothing is worse
                   than none, because it reads as scoping.
      drop it      removing the step shifts every later step out of line with the pinned
                   baseline ("step count 7 vs pinned 8", then three call-name mismatches)
                   and the pinned final state still names `dev.node`. Both stock baselines
                   would need re-capturing, and a capture rewrites the whole group's forty
                   pinned answers — a deliberate dated act under the pinning law, never a
                   consequence of editing one row.

    This test asserts the ABSENCE. When the harness gains step-level marking, both halves
    fail and the marking D2 directs becomes a row-data edit.
    """

    def _harness(self):
        sys.path.insert(0, REPO)
        from tools.conformance.harness import probe, rows as rows_mod
        return probe, rows_mod

    def test_a_marking_on_a_step_is_accepted_and_has_no_effect(self):
        probe, _rows_mod = self._harness()
        with tempfile.TemporaryDirectory() as d:
            row = {
                "row_id": "t-step-marking",
                "steps": [
                    {"call": "mkdir", "args": ["kept", "0o755"]},
                    {
                        "call": "mkdir",
                        "args": ["marked", "0o755"],
                        "marked": {"reason": "overlay-only namespace entry, out of C3 scope"},
                    },
                ],
            }
            obs = probe.run_row(row, d)
        self.assertEqual(len(obs["steps"]), 2, "the marked step was still driven")
        self.assertEqual(obs["steps"][1]["errno"], None)
        self.assertIn("marked", obs["state"], "the marked step still had its effect")
        self.assertNotIn(
            "marked", obs["steps"][1],
            "the observation carries no trace of the declaration either, so nothing "
            "downstream could act on it",
        )

    def test_the_row_compiler_carries_no_step_level_activation(self):
        _probe, rows_mod = self._harness()
        self.assertTrue(
            hasattr(rows_mod.RowAssertion, "__dataclass_fields__"),
            "RowAssertion is the compiled row",
        )
        fields = rows_mod.RowAssertion.__dataclass_fields__
        self.assertIn("active", fields)
        self.assertIn("activates_at", fields)
        _groups, compiled = rows_mod.load_all()
        row = [r for r in compiled if r.row_id == "files.mknod"][0]
        self.assertTrue(row.active)
        steps = row.probe["steps"]
        self.assertEqual(
            [s for s in steps if set(s) - {"call", "args", "kwargs", "as"}],
            [],
            "a step is a call and its arguments; there is no field on it the harness reads "
            "to scope it, which is why §11.1e's step half has no row-data expression",
        )


def _is_mounted(path):
    try:
        with open("/proc/self/mountinfo") as f:
            return any(path in ln and "fuse" in ln for ln in f)
    except OSError:
        return False


if __name__ == "__main__":
    unittest.main()
