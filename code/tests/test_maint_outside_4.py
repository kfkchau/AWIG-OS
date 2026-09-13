# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (record, fold, grant, standing, blob, checkpoint, port, custody, mapping). NON-GOAL:
# no offensive capability of any kind — every test here asserts the CORRECT behaviour by function
# so standing is applied by the folds, one writer holds, the blob barrier is idempotent, containment
# holds at the path and the port, recovery binds to its subject, and the creator's real uid stands.
# Each test is written from the architect's round-2 read DESCRIPTION and our OWN code at the cited
# line — NEVER from the outside harness (not read, not run; owner's order). Each reds against the
# pre-fix code for the described reason (A1) and greens after its fix (A2). Full declaration:
# SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-4 — the round-2 read's R1-R14 (integration gaps), one RED test per item.

These are INTEGRATION gaps: each component is correct alone, its contract with the others missing.
NONE breaks a C5-promised invariant (Pile A empty — the C5 grade stands). R13 is DISSOLVED (archi
:3550) and carries no test.
"""

import errno
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.expanduser("~/gov-lab"))                 # the staged fusepy adapter

from kernel import reconcile, authority                             # noqa: E402
from kernel.boot import build_kernel                                # noqa: E402
from kernel.blobs import BlobStore                                  # noqa: E402
from kernel.compose import build_full_kernel                        # noqa: E402
from kernel.errors import OpError                                   # noqa: E402
from kernel.protection import Protection                            # noqa: E402
from kernel.views import Views                                      # noqa: E402
from bridge import custody, checkpoint, auto_recover                # noqa: E402
from bridge.kernel_port import KernelPort                           # noqa: E402
from subsystems.files import FilesView                              # noqa: E402
from subsystems.memory import MemoryView                            # noqa: E402

try:
    from fuse import FuseOSError                                    # noqa: E402
    from bridge.records_fs import RecordsFS                         # noqa: E402
    FUSEPY = None
except Exception as exc:                                            # pragma: no cover
    FuseOSError = None
    RecordsFS = None
    FUSEPY = str(exc)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
OWNER = "owner"


def T(h, m, s=0, us=0):
    return f"2026-07-27T{h:02d}:{m:02d}:{s:02d}.{us:06d}+00:00"


# =================================================================================================
# R1 [HIGH] — STANDING IS NOT APPLIED BY THE FOLDS. A single LIVE-ROWS predicate in the store makes
# an overturned row ABSENT from every authority/resource fold, so the act's EXISTING authority /
# prerequisite check refuses on the absence (no per-fold patch, no new rule).
# =================================================================================================
class _StandingWorld(unittest.TestCase):
    """A full kernel able to overturn a specific act (the T-OVERTURN machinery, reused): a late-
    deciding law overturns an act decided after it, via the ordinary gate."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep-mo4-r1-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))

    def timed(self, name, param="at", carry=()):
        live = self.views.op_definitions()[name]
        d = json.loads(json.dumps(live["definition"], default=dict))
        d["params"] = dict(d.get("params") or {}, **{param: "required"})
        d["occurrence_time_param"] = param
        for field in carry:
            d["params"][field] = "optional"
            d["payload_from"] = list(d.get("payload_from") or []) + [field]
        d["structural_params"] = list(dict.fromkeys(
            list(d.get("structural_params") or []) + [param] + list(carry)))
        self.gate.execute("AMEND-OP", OWNER, {"name": name, "tier": live.get("tier"),
                                              "definition": d})

    def law(self, rule_id, at, when, actor=OWNER, **extra):
        return self.gate.execute("CREATE-RULE", actor, dict(
            {"rule_id": rule_id, "at": at, "polarity": "-", "text": f"{rule_id} refuses",
             "when": when, "then": [{"refuse": rule_id}]}, **extra))

    def narrow(self):
        self.gate.execute("REVOKE", OWNER, {"grant_id": "founding-openness"})


class TestR1StandingAuthority(_StandingWorld):

    def test_r1_overturned_grant_does_not_authorise(self):
        # A grant to alice, then a LATE law overturns it. The overturned grant is ABSENT from the
        # authority fold, so alice — narrowed off the founding openness — holds nothing and a
        # grant-authorised act refuses citing ROOT-NEG-3/-1; the overturning law is on the record.
        self.timed("CREATE-RULE")
        self.timed("GRANT")
        grant = self.gate.execute("GRANT", OWNER, {
            "grant_id": "a1", "grantee": "alice", "actions": ["CREATE-INFO"],
            "info": ["note"], "space": "space:root", "at": T(9, 30)})
        self.assertTrue(self.views.covers("alice", "CREATE-INFO", "note", "space:root"))
        self.narrow()
        # the late law overturns ALICE's grant specifically (never the founding openness)
        self.law("NO-GRANT", T(9, 0), [{"action": "GRANT", "object": "grant:a1"}])
        # the overturning law is on the record
        self.assertIn(grant["seq"], reconcile.overturned_targets(self.store))
        # R1: the overturned grant is ABSENT from the authority fold
        self.assertNotIn("grant:a1", authority.grants(self.store))
        self.assertNotIn("grant:a1", self.views.grants())
        self.assertFalse(self.views.covers("alice", "CREATE-INFO", "note", "space:root"))
        # and a grant-authorised act (alice delegating a sub-grant, leashed by attenuation to her
        # grants) refuses citing ROOT-NEG-3 — she is now a holder of nothing.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "alice", {"grant_id": "sub", "grantee": "bob",
                              "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:root",
                              "at": T(10, 0)})
        self.assertIn(cm.exception.rule, ("ROOT-NEG-3", "ROOT-NEG-1"))


class TestR1StandingMapping(_StandingWorld):

    def test_r1_overturned_mapping_not_held(self):
        # A MEM-GRANT maps a region; a LATE law overturns it. The overturned mapping is not held in
        # the memory fold (R1 applied by memory.mappings through the store's live-rows predicate).
        self.timed("CREATE-RULE")
        self.timed("MEM-GRANT")
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "h", "ceiling": 100000})
        grant = self.gate.execute("MEM-GRANT", "h", {"region": "r1", "size": 100,
                                                     "holder": "h", "at": T(9, 30)})
        self.assertIn("r1", MemoryView(self.store).mappings())          # held before the overturn
        self.law("NO-MG", T(9, 0), [{"action": "MEM-GRANT"}])
        self.assertIn(grant["seq"], reconcile.overturned_targets(self.store))
        # R1: a fresh fold does not hold the overturned mapping
        self.assertNotIn("r1", MemoryView(self.store).mappings())
        self.assertNotIn("r1", MemoryView(self.store).mappings("h"))


# =================================================================================================
# R2 [HIGH] — THE DEFAULT COMPOSITION ENFORCES NO SINGLE WRITER.
# =================================================================================================
class TestR2SingleWriter(unittest.TestCase):

    def test_r2_two_processes_one_writer(self):
        d = tempfile.mkdtemp(prefix="ep-mo4-r2-")
        record = os.path.join(d, "record.jsonl")
        blobs = os.path.join(d, "blobs")
        # the first full composition takes the writer role (writes the pidfile lock)
        build_full_kernel(record, blobs, os.path.join(d, "vault"))
        lock_path = record + ".lock"
        self.assertTrue(os.path.exists(lock_path), "the full composition took the writer lock")
        # simulate ANOTHER live process holding the writer role (the parent pid is alive and not us)
        with open(lock_path, "w") as f:
            f.write(str(os.getppid()))
        # a SECOND full composition over the SAME record is refused the writer role (no seq collision)
        with self.assertRaises(RuntimeError) as cm:
            build_full_kernel(record, blobs, os.path.join(d, "vault"))
        self.assertIn("lock", str(cm.exception).lower())


# =================================================================================================
# R3 [HIGH] — THE BLOB STORE TRUSTS A PATH AND FORGETS A FAILED BARRIER.
# =================================================================================================
class TestR3Blobs(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep-mo4-r3-")
        self.bs = BlobStore(os.path.join(self.dir, "blobs"))

    def test_r3_dedup_verifies_bytes(self):
        h = self.bs.put(b"the file content")
        # corrupt the stored bytes under the existing name
        p = self.bs._path(h)
        p.write_bytes(b"tampered content of a different length")
        # the dedup path VERIFIES the stored bytes against the hash — a mismatch is a missing-content
        # refusal, never a served hash.
        with self.assertRaises(ValueError):
            self.bs.put(b"the file content")

    def test_r3_put_reruns_barrier_until_marked(self):
        h = self.bs.put(b"content")
        p = str(self.bs._path(h))
        self.assertIn(p, self.bs._barriered)                # the first put marked durability
        # simulate a fresh process (a crash before the parent fsync completed): the mark is gone.
        self.bs._barriered.discard(p)
        self.bs.put(b"content")                             # dedup path re-runs the barrier
        self.assertIn(p, self.bs._barriered)                # ... and re-marks it (idempotent barrier)


# =================================================================================================
# R4 [HIGH] — CONTAINMENT AT THE BLOB PATH AND THE PORT.
# =================================================================================================
class TestR4Path(unittest.TestCase):

    def setUp(self):
        self.bs = BlobStore(os.path.join(tempfile.mkdtemp(prefix="ep-mo4-r4-"), "blobs"))

    def test_r4_path_refuses_non_hex(self):
        # a malformed name would resolve OUTSIDE the blob directory without a strict 64-hex check
        with self.assertRaises(ValueError):
            self.bs._path("sha256:../../etc/passwd")
        with self.assertRaises(ValueError):
            self.bs._path("sha256:deadbeef")                # too short
        with self.assertRaises(ValueError):
            self.bs._path("sha256:" + "z" * 64)             # not hex
        # a well-formed address still resolves inside the directory
        good = "sha256:" + "a" * 64
        self.assertTrue(str(self.bs._path(good)).startswith(str(self.bs.dir)))


class TestR4Port(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep-mo4-r4p-")
        self.store, self.gate, self.views, self.blobs, _subs = build_full_kernel(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def test_r4_port_eproto_before_dispatch(self):
        # a FILL request carrying a MALFORMED identity is a PROTOCOL failure and maps to EPROTO at
        # the handler, for the FILL class too (not only DECISION) — never an uncaught escape to the
        # serve loop's EIO backstop.
        fields = {"id": "1", "op": "FILL-LOOKUP", "class": "FILL",
                  "parent": "not-a-number", "name": "x"}
        status, _rf, _rp = self.port.handle(fields, b"")
        self.assertEqual(status, -errno.EPROTO)


# =================================================================================================
# R5 [HIGH] — AUTOMATIC RECOVERY BINDS ITS PIECES LOOSELY.
# =================================================================================================
def _attesting_world(dirpath):
    """A full kernel whose engine has attested (a checkpoint needs an attested body), with two files
    written so the tree-state is non-trivial."""
    record = os.path.join(dirpath, "rec.jsonl")
    blob_dir = os.path.join(dirpath, "blobs")
    store, gate, views, blobs, _subs = build_full_kernel(record, blob_dir, os.path.join(dirpath, "vault"))
    return store, gate, views, blobs, record, blob_dir


class TestR5Recovery(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep-mo4-r5-")
        self.store, self.gate, self.views, self.blobs, self.record, self.blob_dir = \
            _attesting_world(self.dir)

    def test_r5_recovery_uses_full_verifier(self):
        # a checkpoint whose pinned HEAD still matches the live head (check_head would pass) but whose
        # TREE no longer matches the record: the FULL verifier catches it, check_head could not.
        cp = checkpoint.create(self.store, self.record, self.blob_dir, root="/", pack_path=PACK_PATH)
        # head still current (check_head would say CURRENT), but the tree is corrupted
        self.assertEqual(checkpoint.check_head(cp, auto_recover._live_head(self.store)),
                         checkpoint.CURRENT)
        cp["tree"] = {"corrupted": "this is not the recomputed tree"}
        buddy_pair = (cp, self.record, self.blob_dir, cp, self.record, self.blob_dir)
        tc = auto_recover.triple_check(self.store, cp, auto_recover._live_head(self.store), buddy_pair)
        # R5: the checkpoint check runs the FULL verifier — a corrupt tree fails it
        self.assertFalse(tc["checkpoint"])
        self.assertIn("checkpoint", tc["failed"])

    def test_r5_pair_names_this_store(self):
        # a buddy pair about two OTHER stores (a valid mutual receipt) does NOT authorise a recover of
        # THIS store — the pair must name this store's record path and content root.
        other = tempfile.mkdtemp(prefix="ep-mo4-r5b-")
        st2, g2, v2, b2, rec2, bd2 = _attesting_world(other)
        cp_a = checkpoint.cross_attest(st2, rec2, bd2, witness="A", root="/", pack_path=PACK_PATH)
        cp_b = checkpoint.cross_attest(self.store, self.record, self.blob_dir, witness="B", root="/",
                                       pack_path=PACK_PATH)
        cp_a["peer_root"] = cp_b["provenance"]["merkle_root"]
        cp_b["peer_root"] = cp_a["provenance"]["merkle_root"]
        # a sound mutual receipt about st2 + self.store — but the pair for THIS recover is built from
        # two OTHER stores (st2 and a THIRD), naming neither self.store's record nor its content root.
        third = tempfile.mkdtemp(prefix="ep-mo4-r5c-")
        st3, g3, v3, b3, rec3, bd3 = _attesting_world(third)
        cp_c = checkpoint.cross_attest(st3, rec3, bd3, witness="C", root="/", pack_path=PACK_PATH)
        cp_a2 = checkpoint.cross_attest(st2, rec2, bd2, witness="A", root="/", pack_path=PACK_PATH)
        cp_a2["peer_root"] = cp_c["provenance"]["merkle_root"]
        cp_c["peer_root"] = cp_a2["provenance"]["merkle_root"]
        pair_about_others = (cp_a2, rec2, bd2, cp_c, rec3, bd3)
        tc = auto_recover.triple_check(self.store, cp_b, auto_recover._live_head(self.store),
                                       pair_about_others)
        # R5: the buddy check does not pass — the pair names two OTHER stores, not this one
        self.assertFalse(tc["buddy"])


# =================================================================================================
# R6 [GREEN] — hand_off's receipt covers a LIST.
# =================================================================================================
class TestR6Receipt(unittest.TestCase):

    def test_r6_receipt_covers_every_hash(self):
        bs = BlobStore(os.path.join(tempfile.mkdtemp(prefix="ep-mo4-r6-"), "blobs"))
        h1 = bs.put(b"first")
        h2 = bs.put(b"second")
        # a receipt naming ONLY h1 must not authorise removing BOTH h1 and h2
        receipt = {"object": h1}
        with self.assertRaises(ValueError):
            bs.hand_off([h1, h2], receipt)
        # both are still present — nothing left under a receipt that did not name it
        self.assertTrue(bs.has(h1))
        self.assertTrue(bs.has(h2))
        # the covered singleton still works
        self.assertEqual(bs.hand_off([h1], {"object": h1}), [h1])


# =================================================================================================
# R7 [GREEN] — the mirror audit misses an action absent from BOTH streams.
# =================================================================================================
class TestR7MirrorAudit(unittest.TestCase):

    def test_r7_missing_from_both_is_divergence(self):
        d = tempfile.mkdtemp(prefix="ep-mo4-r7-")
        blobs = BlobStore(os.path.join(d, "blobs"))
        # build WITHOUT protection, then execute an AUDITED governance action so it is appended with
        # NO mirror running — an act absent from BOTH streams.
        store, gate, views = build_kernel(os.path.join(d, "rec.jsonl"), blobs=blobs)
        gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "h", "ceiling": 1000})   # an audited action
        protection = Protection(store, gate, views)          # attach the streams AFTER the act
        audit = protection._audit_actions()
        expected = {e["seq"] for e in store.all() if e["action"] in audit}
        self.assertTrue(expected, "there is a retained governance action the audit list names")
        divs = set(protection.dual_blind_divergences())
        # R7: every retained governance action absent from BOTH streams is a divergence — the old
        # union(stream_a, stream_b) enumeration could never see it (it named neither stream).
        self.assertTrue(expected <= divs)


# =================================================================================================
# R8 [GREEN] — FilesView.content_at folds FILE-WRITE only (disagrees after a truncate).
# =================================================================================================
class TestR8ContentAt(unittest.TestCase):

    def test_r8_content_at_agrees_with_custody_after_truncate(self):
        d = tempfile.mkdtemp(prefix="ep-mo4-r8-")
        blobs = BlobStore(os.path.join(d, "blobs"))
        store, gate, views = build_kernel(os.path.join(d, "rec.jsonl"), blobs=blobs)
        h1 = blobs.put(b"hello world")            # the write
        h2 = blobs.put(b"hello")                  # the truncated content
        store._append({"actor": "owner", "action": "FILE-CREATE", "object": "/f",
                       "rule_cited": "ROOT-NEG-5",
                       "payload": {"path": "/f", "node_type": "file", "perm": "644"}})
        store._append({"actor": "owner", "action": "FILE-WRITE", "object": "/f",
                       "rule_cited": "ROOT-NEG-5",
                       "payload": {"path": "/f", "content_hash": h1, "length": 11}})
        store._append({"actor": "owner", "action": "FILE-TRUNCATE", "object": "/f",
                       "rule_cited": "ROOT-NEG-5",
                       "payload": {"path": "/f", "content_hash": h2, "length": 5}})
        # what the custody fold says the content is (it applies FILE-WRITE AND FILE-TRUNCATE)
        st = custody.fold(store.all())
        node = st.inodes.get(st.names.get(custody._norm("/f")))
        self.assertEqual(node.content_hash, h2)
        # R8: content_at agrees with custody after the truncate (not the pre-truncate write's hash)
        fv = FilesView(store, blobs)
        self.assertEqual(fv.content_at("/f"), blobs.get(h2))


# =================================================================================================
# R9 [GREEN] — memory.mappings(holder) skips other holders' grants (a re-grant leaves a stale entry).
# =================================================================================================
class TestR9Regrant(unittest.TestCase):

    def test_r9_regrant_clears_stale_holder_entry(self):
        d = tempfile.mkdtemp(prefix="ep-mo4-r9-")
        blobs = BlobStore(os.path.join(d, "blobs"))
        store, gate, views, b, subs = build_full_kernel(
            os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs2"), os.path.join(d, "vault"))
        gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "A", "ceiling": 100000})
        gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "B", "ceiling": 100000})
        gate.execute("MEM-GRANT", "A", {"region": "r", "size": 100, "holder": "A"})
        # region r is RE-GRANTED to B (a supersession of the whole table)
        gate.execute("MEM-GRANT", "B", {"region": "r", "size": 100, "holder": "B"})
        mv = MemoryView(store)
        # R9: A's projection no longer holds r (the re-grant to B superseded it — folded whole, then
        # filtered, so A's stale entry is gone)
        self.assertNotIn("r", mv.mappings("A"))
        self.assertIn("r", mv.mappings("B"))
        self.assertEqual(mv.mappings()["r"]["holder"], "B")


# =================================================================================================
# R10 [FOUNDING data] — SHM-GRANT after MEM-EVICT accepted (the live prerequisite absent).
# =================================================================================================
class TestR10ShmLivePrereq(unittest.TestCase):

    def test_r10_shm_grant_after_evict_refused(self):
        d = tempfile.mkdtemp(prefix="ep-mo4-r10-")
        store, gate, views, blobs, subs = build_full_kernel(
            os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
        gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "h", "ceiling": 100000})
        gate.execute("MEM-GRANT", "h", {"region": "r1", "size": 100, "holder": "h"})
        gate.execute("SHM-GRANT", "h", {"region": "r1"})            # live prerequisite holds
        gate.execute("MEM-EVICT", "h", {"region": "r1"})           # the mapping is torn down
        # R10: a SHM-GRANT over a region granted THEN evicted is refused (the historical prerequisite
        # holds, the LIVE one is absent) — the new live_present check row, citing its law.
        with self.assertRaises(OpError) as cm:
            gate.execute("SHM-GRANT", "h", {"region": "r1"})
        self.assertEqual(cm.exception.rule, "COMM-LAW-SHARE-GRANT")


# =================================================================================================
# R11 [GREEN] — rename over another name of the same inode loses a name.
# =================================================================================================
@unittest.skipIf(FUSEPY is not None, "fusepy adapter not importable: %s" % FUSEPY)
class TestR11SameInodeRename(unittest.TestCase):

    def test_r11_same_inode_rename_keeps_both(self):
        d = tempfile.mkdtemp(prefix="ep-mo4-r11-")
        store, gate, views, blobs, subs = build_full_kernel(
            os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
        fs = RecordsFS(store, gate, views, blobs)
        fs.create("/a", 0o644)
        fs.link("/b", "/a")                                # /b is a second name for /a's inode
        self.assertEqual(fs.state.lookup("/a").identity, fs.state.lookup("/b").identity)
        fs.rename("/a", "/b")                              # POSIX: same-inode rename is a NO-OP
        # R11: BOTH names are kept — a FILE-RENAME here would have unbound /a and lost a name
        self.assertIsNotNone(fs.state.lookup("/a"))
        self.assertIsNotNone(fs.state.lookup("/b"))
        self.assertEqual(fs.state.lookup("/a").identity, fs.state.lookup("/b").identity)


# =================================================================================================
# R12 [GREEN] — fault() re-folds the mapping table per call.
# =================================================================================================
class TestR12FaultMemoised(unittest.TestCase):

    def test_r12_fault_fold_memoised(self):
        d = tempfile.mkdtemp(prefix="ep-mo4-r12-")
        store, gate, views, blobs, subs = build_full_kernel(
            os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
        gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "h", "ceiling": 100000})
        gate.execute("MEM-GRANT", "h", {"region": "r1", "size": 100, "holder": "h"})
        mv = MemoryView(store)
        self.assertTrue(mv.fault("r1"))
        # the fold is memoised — the cache holds the table
        self.assertIn(None, mv._map_cache)
        before = dict(mv._map_cache[None])
        # kill the cache -> the next read re-folds an IDENTICAL table (T-CACHE-KILL)
        mv.kill_cache()
        self.assertEqual(mv._map_cache, {})
        self.assertTrue(mv.fault("r1"))
        self.assertEqual(mv._map_cache[None], before)
        # a new decision INVALIDATES the memoised fold ON APPEND — fault sees it without a manual kill
        gate.execute("MEM-GRANT", "h", {"region": "r2", "size": 100, "holder": "h"})
        self.assertTrue(mv.fault("r2"))


# =================================================================================================
# R14 [HIGH] — FILE-CREATE folds to uid 0.
# =================================================================================================
class TestR14CreatorUid(unittest.TestCase):

    def _creator_of(self, record):
        """Fold a single FILE-CREATE record through the custody state and read the created node's uid."""
        st = custody.CustodyState()
        st.apply(record)
        node = st.inodes.get(st.names.get(custody._norm(record["payload"]["path"])))
        return node.uid

    def test_r14_creator_carries_provenance_uid(self):
        # a FILE-CREATE by a NON-ROOT actor, whose provenance names no uid, must fold to THAT actor's
        # uid (carried on the record's actor rendering) — never a silent 0.
        rec = {"seq": 1, "actor": "uid:1000", "action": "FILE-CREATE", "object": "/f",
               "rule_cited": "FS-LAW-NAMESPACE",
               "payload": {"path": "/f", "node_type": "file", "perm": "644"},
               "provenance": {"asserted_by": "uid:1000", "source": "kernel-port", "could_read": []}}
        self.assertEqual(self._creator_of(rec), 1000)
        # a genuine SYSTEM-originated create names no uid and correctly stays 0 (the regression the fix
        # must NOT break)
        sysrec = {"seq": 1, "actor": "SYSTEM", "action": "FILE-CREATE", "object": "/s",
                  "rule_cited": "FS-LAW-NAMESPACE",
                  "payload": {"path": "/s", "node_type": "file", "perm": "644"},
                  "provenance": {"asserted_by": "SYSTEM", "source": "system", "could_read": []}}
        self.assertEqual(self._creator_of(sysrec), 0)


if __name__ == "__main__":
    unittest.main()
