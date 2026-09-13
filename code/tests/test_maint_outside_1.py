# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (record, gate, effect, blob, mount, fold). NON-GOAL: no offensive capability of any
# kind — every test here asserts the CORRECT behaviour by function so a refused act leaves no
# effect, the served state is the recovered one, and a partial founding re-lands. Full
# declaration: SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-1 — the outside read's B1-B11 (defensive hardening), one RED test per item.

Each test is written from the architect's read DESCRIPTION and our OWN code at the cited line —
NEVER from the outside harness (not read, not run; owner's order). Each asserts the CORRECT
behaviour by function and reds against the current code for the described reason (A1); it greens
after its fix (A2). The HIGH four (B1/B2/B4/B9) are proven both directions (A3).

B2 was RAISED and is now RESOLVED by the architect's ruling (:3495): the test_ep25:279 keep-burst
pin STANDS (a refused write's burst is KEPT, POSIX un-fsynced semantics); P2's earlier "drop the
burst" is WITHDRAWN. Instead DIRECT_IO governs the real mount (mount.py) and the read path serves
an un-committed burst ONLY to its own writing handle (read-your-own-write, records_fs._content) —
so a fresh reader never sees the refused byte while the burst is still kept. B2 is delivered.

ONE item is RAISED, not fixed — its fix reds a PINNED design test outside its own fence
(§7 b/c STOP), never a §5 fence file:

  B11 — the fix (a directory's own metadata enters its hash) reds tests/test_ep45.py
        test_a1_the_root_is_built_leaf_dir_top, which PINS a directory hash = canonical_hash over
        CHILDREN only as EP-45 design. DEFERRED to EP-MAINT-OUTSIDE-2.

Its RED test stands, skipped, so the module runs green for the TEN delivered items; remove the
skip to see it red against current code. Delivered: B1, B2, B3, B4, B5, B6, B7, B8, B9, B10.
"""

import base64
import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.expanduser("~/gov-lab"))                 # the staged fusepy adapter

from kernel.boot import build_kernel                                # noqa: E402
from kernel.blobs import BlobStore                                  # noqa: E402
from kernel.store import EventStore                                 # noqa: E402
from kernel import erasure, keys                                    # noqa: E402
from kernel.gate import make_invoker_sig                            # noqa: E402
from kernel.errors import OpError                                   # noqa: E402
from bridge import custody, replay_snapshot, merkle                 # noqa: E402
from founding.install import install, load_pack, records            # noqa: E402
from kernel.canonical import canonical_hash                         # noqa: E402

try:
    from fuse import FuseOSError                                    # noqa: E402
    from bridge.mount import build_mount                            # noqa: E402
    FUSEPY = None
except ImportError as exc:                                          # pragma: no cover
    FuseOSError = None
    build_mount = None
    FUSEPY = str(exc)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XATTR_CREATE = 0x1                                                  # Linux XATTR_CREATE
XATTR_REPLACE = 0x2                                                 # Linux XATTR_REPLACE


# ============================================================================================
# B1 [HIGH] — a handover removes the bytes before the gate decides.
# A standing rule refusing HANDOVER at the gate must leave the target bytes present: a refused
# act has no effect. Order is DECIDE -> EFFECT -> APPEND (archi P1): the gate's passes decide the
# draft BEFORE any byte moves, then hand_off runs, then the append attests.
# ============================================================================================

RECEIVER = "the-receiving-archive"
RECEIVER_KEY = "testpub:receiving-archive:v1"


class _HandoverWorld(unittest.TestCase):
    """A disposable founding world: the handover law declared, the ceremony registered, a
    receiver key bound (the receipt verifies). Modelled on tests/test_ep41b.HandoverWorld."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self._dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.path, blobs=self.blobs)
        self._declare_handover_law()
        self.assertTrue(erasure.register_ceremony(self.gate, self.views))
        self._bind_key(RECEIVER, RECEIVER_KEY)

    def _declare_handover_law(self):
        self.store._append({
            "actor": "SYSTEM", "action": "CREATE-RULE", "object": erasure.HANDOVER_LAW,
            "rule_cited": "BOOT-INT",
            "payload": {"kind": "rule", "rule_id": erasure.HANDOVER_LAW, "root": True,
                        "polarity": "+", "text": "handover law (test world)"}})

    def _bind_key(self, account, public_key):
        self.store._append({
            "actor": "SYSTEM", "action": "KEY-BIND", "object": account, "rule_cited": "BOOT-INT",
            "payload": {"kind": keys.KEY_BIND, keys.ACCOUNT: account, keys.PUBLIC_KEY: public_key,
                        keys.CLASS: "LAW"}})

    def _write_file(self, path, content):
        h = self.blobs.put(content)
        self.store._append({"actor": "owner", "action": "FILE-CREATE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "node_type": "file", "perm": "644"}})
        self.store._append({"actor": "owner", "action": "FILE-WRITE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "content_hash": h, "length": len(content)}})
        return h

    def _signed_receipt(self, chain_copy_hash, rule="RET-GDPR-1"):
        body = {"action": erasure.RECEIVED_CUSTODY, "object": chain_copy_hash,
                "target": None, "payload": {"rule": rule}}
        receipt = dict(body)
        receipt["actor"] = RECEIVER
        receipt[erasure.INVOKER_SIG] = make_invoker_sig(RECEIVER_KEY, body)
        return receipt

    def _handover(self, target, rule="RET-GDPR-1"):
        params = {"target_hash": target, "receiver": RECEIVER, "retention_rule": rule,
                  "receipt": self._signed_receipt(target, rule)}
        return self.gate.execute(erasure.HANDOVER_OP, "owner", params)

    def _refuse_handover_at_the_gate(self):
        """Plant a standing don't-rule refusing HANDOVER-CUSTODY at the gate (full-form pass)."""
        self.store._append({
            "actor": "SYSTEM", "action": "CREATE-RULE", "object": "NO-HANDOVER-STANDING",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "NO-HANDOVER-STANDING", "polarity": "-",
                        "when": [{"action": erasure.HANDOVER_OP}],
                        "then": [{"refuse": "NO-HANDOVER-STANDING"}]}})


class TestB1RefusedHandoverKeepsBytes(_HandoverWorld):

    def test_b1_refused_handover_keeps_bytes(self):
        # A standing rule refuses HANDOVER at the gate; the target bytes REMAIN present (a refused
        # act has no effect). Reds now: hand_off removes the bytes in the handler before the gate's
        # rule-refusal, so the bytes are gone at the moment of refusal.
        h = self._write_file("/f", b"content a standing rule will refuse the handover of")
        self._refuse_handover_at_the_gate()
        with self.assertRaises(OpError) as cm:
            self._handover(h)
        self.assertEqual(cm.exception.rule, "NO-HANDOVER-STANDING")     # refused BY THE STANDING RULE
        self.assertTrue(self.blobs.has(h), "a refused handover left the bytes removed — an effect")
        self.assertEqual(erasure.departed_hashes(self.store.all()), set())  # nothing departed

    def test_b1_success_still_removes_and_records_the_departure(self):
        # A3 the other direction (the guarantee not over-applied): with NO standing refusal the
        # effect runs — the bytes depart AND the departure record stands. Reds if the deferred
        # effect were dropped instead of run after the decision.
        h = self._write_file("/f", b"content handed over lawfully")
        self._handover(h)
        self.assertFalse(self.blobs.has(h), "a completed handover did not remove the bytes")
        self.assertIn(h, erasure.departed_hashes(self.store.all()))
        self.assertEqual(self.store.events[-1]["payload"]["kind"], erasure.DEPARTURE_RECORD)


# ============================================================================================
# The mount-backed items (B2/B3/B7/B8/B10). The fusepy adapter is staged at ~/gov-lab.
# ============================================================================================

@unittest.skipIf(FUSEPY, "the fusepy adapter is not on this machine: %s" % FUSEPY)
class _Mount(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "rec.jsonl")
        self.blobdir = os.path.join(self.dir, "blobs")
        self.fs, self.store, self.gate, self.views, self.blobs = build_mount(self.record, self.blobdir)

    def _write(self, path, data, perm=0o644):
        import os as _os
        fh = self.fs.create(path, perm)
        self.fs.write(path, data if isinstance(data, bytes) else data.encode(), 0, fh)
        self.fs.flush(path, fh)
        self.fs.release(path, fh)

    def _read(self, path):
        import os as _os
        fh = self.fs.open(path, _os.O_RDONLY)
        out = self.fs.read(path, 1 << 20, 0, fh)
        self.fs.release(path, fh)
        return out


class TestB2RefusedWriteNotServed(_Mount):

    def _refuse_file_write_at_the_gate(self):
        self.store._append({
            "actor": "SYSTEM", "action": "CREATE-RULE", "object": "NO-WRITE-STANDING",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "NO-WRITE-STANDING", "polarity": "-",
                        "when": [{"action": "FILE-WRITE"}],
                        "then": [{"refuse": "NO-WRITE-STANDING"}]}})

    def test_b2_refused_write_not_served_to_a_reader(self):
        import os as _os
        self._write("/f", b"OLD-COMMITTED-CONTENT")
        self._refuse_file_write_at_the_gate()
        # write buffers (returns len), then flush closes the burst -> FILE-WRITE is refused at the
        # gate. A fresh reader must see NO refused byte (a served byte with no record behind it can
        # never happen). Reds now: the refused burst is KEPT and _content serves it.
        fh = self.fs.open("/f", _os.O_RDWR)
        self.fs.write("/f", b"REFUSED-BYTES-XX", 0, fh)
        with self.assertRaises(FuseOSError):
            self.fs.flush("/f", fh)
        self.assertEqual(self._read("/f"), b"OLD-COMMITTED-CONTENT",
                         "a refused write was served to a fresh reader")

    def test_b2_an_accepted_write_is_still_served(self):
        # A3 the other direction: dropping a REFUSED burst must not drop an ACCEPTED one — an
        # ordinary write's flush commits and is served. Reds if the drop over-applies.
        import os as _os
        self._write("/g", b"first-committed")
        fh = self.fs.open("/g", _os.O_RDWR)
        self.fs.write("/g", b"SECOND", 0, fh)
        self.fs.flush("/g", fh)                                        # an ACCEPTED write, committed
        self.fs.release("/g", fh)
        self.assertEqual(self._read("/g"), b"SECONDcommitted")


class TestB3TwoHandlesMerge(_Mount):

    def test_b3_two_handles_merge_not_clobber(self):
        import os as _os
        self._write("/f", b"XXXXYYYY")                                  # 8-byte committed base
        fh1 = self.fs.open("/f", _os.O_RDWR)
        fh2 = self.fs.open("/f", _os.O_RDWR)
        self.fs.write("/f", b"AAAA", 0, fh1)                            # handle 1 -> bytes [0,4)
        self.fs.write("/f", b"BBBB", 4, fh2)                            # handle 2 -> bytes [4,8)
        self.fs.flush("/f", fh2)                                        # the later flush ...
        self.fs.flush("/f", fh1)                                        # ... then the earlier
        self.fs.release("/f", fh1)
        self.fs.release("/f", fh2)
        # both writes must survive; the committed content carries BOTH. Reds now: the later flush
        # overwrites the earlier's whole buffer, clobbering one write.
        self.assertEqual(self._read("/f"), b"AAAABBBB")


class TestB7PartialUnlockSplits(_Mount):

    def _flock(self, fh, cmd, ltype, start, length, path):
        import ctypes
        from bridge.records_fs import _Flock
        fl = _Flock(ltype, os.SEEK_SET, start, length, 0)
        rc = self.fs.lock(path, fh, cmd, ctypes.addressof(fl))
        return rc, fl

    def test_b7_partial_unlock_splits(self):
        import os as _os, fcntl
        self._write("/l", b"0123456789" * 12)                          # 120 bytes
        fh = self.fs.open("/l", _os.O_RDWR)
        ino = self.fs._open[fh]["ino"]
        owner = self.fs._ctx()[2]
        self._flock(fh, fcntl.F_SETLK, fcntl.F_WRLCK, 0, 100, "/l")     # hold [0,100)
        self._flock(fh, fcntl.F_SETLK, fcntl.F_UNLCK, 40, 20, "/l")     # unlock the sub-range [40,60)
        held = {(lk.start, lk.length) for lk in self.fs.locks.held_by(ino, owner)}
        # the non-overlapping remainder stays held; a partial unlock SPLITS, never releases whole.
        # Reds now: the whole [0,100) lock is dropped (held == set()).
        self.assertIn((0, 40), held, "the [0,40) remainder was released by a partial unlock")
        self.assertIn((60, 40), held, "the [60,100) remainder was released by a partial unlock")
        self.assertNotIn((40, 20), held)                               # the unlocked sub-range is gone

    def test_b7_a_whole_unlock_still_releases_whole(self):
        # A control: unlocking the whole held range leaves nothing (the split is only for a strict
        # sub-range). Guards the fix against re-locking a remainder that does not exist.
        import os as _os, fcntl
        self._write("/l2", b"z" * 50)
        fh = self.fs.open("/l2", _os.O_RDWR)
        ino = self.fs._open[fh]["ino"]
        owner = self.fs._ctx()[2]
        self._flock(fh, fcntl.F_SETLK, fcntl.F_WRLCK, 0, 0, "/l2")      # whole file
        self._flock(fh, fcntl.F_SETLK, fcntl.F_UNLCK, 0, 0, "/l2")      # unlock whole file
        self.assertEqual(self.fs.locks.held_by(ino, owner), [])


class TestB8BinaryXattr(_Mount):

    def test_b8_binary_xattr_roundtrips_and_flags(self):
        self._write("/x", b"data")
        raw = b"\xff\xfe\x00\x80\x01\xc3\x28"                           # NOT valid UTF-8
        # a binary value must round-trip byte-identical. Reds now: the surrogateescape decode feeds
        # a lone-surrogate string into the canonical encoder, which raises.
        self.fs.setxattr("/x", "user.bin", raw, 0)
        self.assertEqual(self.fs.getxattr("/x", "user.bin"), raw)
        # XATTR_CREATE on an existing name refuses (EEXIST). Reds now: the flag is ignored.
        with self.assertRaises(FuseOSError) as cm:
            self.fs.setxattr("/x", "user.bin", b"other", XATTR_CREATE)
        self.assertEqual(cm.exception.errno, __import__("errno").EEXIST)

    def test_b8_text_xattr_is_unchanged(self):
        # A control: a valid-UTF-8 (ASCII) value is stored and read back exactly as before.
        self._write("/x2", b"data")
        self.fs.setxattr("/x2", "user.k", b"plain-value", 0)
        self.assertEqual(self.fs.getxattr("/x2", "user.k"), b"plain-value")


# ============================================================================================
# B4 [HIGH] — recovery records a decision no file fold consumes.
# After a RECOVER-TO-CHECKPOINT the file fold's served state is the RECOVERED base, not the
# damaged tail (archi P4: the fold of record the mount serves — custody.fold).
# ============================================================================================

class TestB4ServedStateIsRecovered(unittest.TestCase):

    HA = "sha256:" + hashlib.sha256(b"the SOUND content").hexdigest()
    HB = "sha256:" + hashlib.sha256(b"the DAMAGED tail").hexdigest()
    HC = "sha256:" + hashlib.sha256(b"a lawful act AFTER recovery").hexdigest()

    def _records(self, with_recover=True, with_post=False):
        recs = [
            {"seq": 1, "actor": "owner", "action": "FILE-CREATE", "object": "/f",
             "payload": {"path": "/f", "node_type": "file", "perm": "644", "inode": "seq:1"}},
            {"seq": 2, "actor": "owner", "action": "FILE-WRITE", "object": "/f",
             "payload": {"path": "/f", "content_hash": self.HA, "length": 17}},        # the SOUND point
            {"seq": 3, "actor": "owner", "action": "FILE-WRITE", "object": "/f",
             "payload": {"path": "/f", "content_hash": self.HB, "length": 16}},        # the DAMAGED tail
        ]
        if with_recover:
            recs.append(
                {"seq": 4, "actor": "owner", "action": erasure.RECOVER_OP, "object": self.HA,
                 "payload": {"kind": erasure.RECOVER_RECORD, "class": "DECISION",
                             erasure.TARGET_HEAD: self.HA, erasure.TARGET_SEQ: 2,
                             erasure.CHECKPOINT_REF: "cp:sound"}})
        if with_post:
            recs.append(
                {"seq": 5, "actor": "owner", "action": "FILE-WRITE", "object": "/f",
                 "payload": {"path": "/f", "content_hash": self.HC, "length": 27}})
        return recs

    def _served_hash(self, recs):
        st = custody.fold(recs)
        return st.inodes[st.names["/f"]].content_hash

    def test_b4_served_state_is_the_recovered_one(self):
        # the served file content is the recovered base HA, NOT the damaged tail HB. Reds now: the
        # fold applies every record forward and serves HB.
        self.assertEqual(self._served_hash(self._records()), self.HA)

    def test_b4_post_recovery_acts_apply_and_no_recover_is_inert(self):
        # A3 both directions. (1) a lawful act AFTER the splice DOES apply (served = HC), so the
        # fix is not "freeze at the recovered point". (2) with NO recover record the fold is
        # unchanged (serves the damaged HB) — the fix is inert without recovery, so it can never
        # silently skip a tail. Reds if either the post-recover suffix is dropped or the plain
        # fold is altered.
        self.assertEqual(self._served_hash(self._records(with_post=True)), self.HC)
        self.assertEqual(self._served_hash(self._records(with_recover=False)), self.HB)


# ============================================================================================
# B5 [GREEN] — the ceiling arm accepts a negative amount and double-counts a same-key re-grant.
# ============================================================================================

class TestB5CeilingSignAndRegrant(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "rec.jsonl"))

    def _budget(self, holder, ceiling):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": holder, "ceiling": ceiling})

    def _grant(self, region, size, holder="web"):
        return self.gate.execute("MEM-GRANT", holder, {"region": region, "size": size, "holder": holder})

    def test_b5_ceiling_sign_and_regrant(self):
        self._budget("web", 100)
        # (a) a negative amount is malformed and refuses at the door. Reds now: no sign check, so a
        # negative amount slips past (used + (-n) never exceeds the ceiling).
        with self.assertRaises(OpError):
            self._grant("r0", -5)
        # (b) a re-grant of an existing key at a higher value compares against the DELTA, not the
        # sum. Reds now: used already holds r1's prior value, and the check adds the full request
        # on top, double-counting and wrongly refusing.
        self._grant("r1", 60)                                          # used 60
        self._grant("r1", 80)                                          # re-grant r1 -> net 80 <= 100, allowed
        self.assertEqual(self.views.policy_value("budget:web"), 100)


# ============================================================================================
# B6 [GREEN] — renaming a populated directory does not rebind descendants.
# ============================================================================================

class TestB6RenameRebindsDescendants(unittest.TestCase):

    def _records(self):
        return [
            {"seq": 1, "actor": "o", "action": "FILE-MKDIR", "object": "/a",
             "payload": {"path": "/a", "node_type": "dir", "perm": "755", "inode": "seq:1"}},
            {"seq": 2, "actor": "o", "action": "FILE-CREATE", "object": "/a/b",
             "payload": {"path": "/a/b", "node_type": "file", "perm": "644", "inode": "seq:2"}},
            {"seq": 3, "actor": "o", "action": "FILE-MKDIR", "object": "/a/sub",
             "payload": {"path": "/a/sub", "node_type": "dir", "perm": "755", "inode": "seq:3"}},
            {"seq": 4, "actor": "o", "action": "FILE-CREATE", "object": "/a/sub/c",
             "payload": {"path": "/a/sub/c", "node_type": "file", "perm": "644", "inode": "seq:4"}},
            {"seq": 5, "actor": "o", "action": "FILE-RENAME", "object": "/a",
             "payload": {"path": "/a", "new_path": "/x"}},
        ]

    def test_b6_rename_rebinds_descendants(self):
        st = custody.fold(self._records())
        # every descendant resolves under the NEW path. Reds now: only /a -> /x moves; /a/b and
        # /a/sub/c keep their old keys and /x/b, /x/sub/c resolve to nothing.
        self.assertIn("/x", st.names)
        self.assertIn("/x/b", st.names)
        self.assertIn("/x/sub", st.names)
        self.assertIn("/x/sub/c", st.names)
        self.assertNotIn("/a/b", st.names)
        self.assertNotIn("/a/sub/c", st.names)


# ============================================================================================
# B9 [HIGH] — the founding idempotency guard reads the FIRST founding record.
# A founding truncated after CREATE-ACTOR SYSTEM (but before the pack's LAST record) must NOT be
# taken as complete; it re-lands (archi P3: read the pack's own LAST record, not the designation).
# ============================================================================================

class TestB9PartialFoundingRelands(unittest.TestCase):

    LAST_ACTION = "GRANT"
    LAST_OBJECT = "grant:founding-openness"

    def _openness_grants(self, store):
        return [e for e in store.by_action(self.LAST_ACTION) if e.get("object") == self.LAST_OBJECT]

    def test_b9_partial_founding_relands(self):
        recs = records(load_pack())
        # a partial prefix: FOUND-STORE + CREATE-ACTOR SYSTEM (index 1), before the final GRANT.
        prefix = recs[:2]
        self.assertEqual(prefix[1].get("action"), "CREATE-ACTOR")
        self.assertEqual((prefix[1].get("payload") or {}).get("actor_id"), "SYSTEM")
        store = EventStore(os.path.join(tempfile.mkdtemp(), "rec.jsonl"), require_rule_cited=True)
        for r in prefix:
            store._append(dict(r))
        self.assertEqual(self._openness_grants(store), [])             # the last record is absent
        install(store)                                                 # must RE-LAND, not report founded
        # reds now: the guard sees the SYSTEM CREATE-ACTOR and returns, so the re-land never runs.
        self.assertEqual(len(self._openness_grants(store)), 1,
                         "a partial founding did not re-land — the guard reported founded")

    def test_b9_a_complete_founding_is_idempotent(self):
        # A3 the other direction (the regression that reds if the guard weakens to always-proceed):
        # a COMPLETE founding re-lands NOTHING on a second install — the openness grant stays 1.
        store, _g, _v = build_kernel(os.path.join(tempfile.mkdtemp(), "rec.jsonl"))
        self.assertEqual(len(self._openness_grants(store)), 1)
        install(store)                                                 # second call
        self.assertEqual(len(self._openness_grants(store)), 1, "a complete founding re-landed")


# ============================================================================================
# B10 [GREEN] — a missing blob is served as an empty file.
# ============================================================================================

@unittest.skipIf(FUSEPY, "the fusepy adapter is not on this machine: %s" % FUSEPY)
class TestB10MissingBlobRefuses(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "rec.jsonl")
        self.blobdir = os.path.join(self.dir, "blobs")
        self.fs, self.store, self.gate, self.views, self.blobs = build_mount(self.record, self.blobdir)

    def _blob_path(self, content_hash):
        digest = content_hash.split(":", 1)[1]
        return os.path.join(self.blobdir, digest[:2], digest[2:])

    def test_b10_missing_blob_refuses(self):
        fh = self.fs.create("/f", 0o644)
        self.fs.write("/f", b"content whose blob will vanish", 0, fh)
        self.fs.flush("/f", fh)
        self.fs.release("/f", fh)
        node = self.fs.state.inodes[self.fs.state.names["/f"]]
        os.remove(self._blob_path(node.content_hash))                  # the named bytes are gone, not departed
        # a missing blob is a missing-content refusal, never empty content. Reds now: snapshot
        # serves it as data=b"" (size 0), indistinguishable from a legitimately empty file.
        with self.assertRaises(SystemExit):
            replay_snapshot.snapshot(self.record, self.blobdir, root="/")

    def test_b10_a_present_blob_still_serves(self):
        # A control: a file whose blob IS present serves its bytes (the refusal is only for absent).
        fh = self.fs.create("/g", 0o644)
        self.fs.write("/g", b"hello", 0, fh)
        self.fs.flush("/g", fh)
        self.fs.release("/g", fh)
        out = replay_snapshot.snapshot(self.record, self.blobdir, root="/")
        self.assertEqual(out["g"]["size"], 5)


# ============================================================================================
# B11 [GREEN] — RAISED, NOT FIXED. The merkle fold hashes a directory over its children only.
#
# The fix (the directory's own metadata enters its hash) reds tests/test_ep45.py
# test_a1_the_root_is_built_leaf_dir_top, which PINS `dir["hash"] == canonical_hash(dir1_pairs)`
# (children only) as the settled EP-45 merkle spec. That test is outside B11's fence
# (merkle.py + this module) and its pin is a DESIGN, not a conformance bug — §7(c) STOP. Raised
# to the architect. The RED test stands (skipped) and reds against current code if un-skipped.
# ============================================================================================

class TestB11DirModeEntersHash(unittest.TestCase):

    @unittest.skip("B11 RAISED (§7c): the fix reds test_ep45's pinned merkle spec, outside fence")
    def test_b11_dir_mode_enters_hash(self):
        tree_a = {"d": {"type": "dir", "perm": "0o755", "nlink": 2},
                  "d/f": {"type": "file", "perm": "0o644", "nlink": 1, "size": 3, "sha256": "abc"}}
        tree_b = {"d": {"type": "dir", "perm": "0o700", "nlink": 2},                # only the dir's mode
                  "d/f": {"type": "file", "perm": "0o644", "nlink": 1, "size": 3, "sha256": "abc"}}
        ha = merkle.merkle_tree(tree_a)["children"]["d"]["hash"]
        hb = merkle.merkle_tree(tree_b)["children"]["d"]["hash"]
        # a directory whose mode changed must move its merkle hash. Reds now: the dir hash is over
        # children only, so the two are equal.
        self.assertNotEqual(ha, hb, "a directory's own mode is outside its merkle hash")


if __name__ == "__main__":
    unittest.main()
