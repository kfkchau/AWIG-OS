# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (checkpoint, recovery artifact, provenance triplet, waking-point); NON-GOAL: no
# offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-44 (BUILD) acceptance + red-world battery: persisted checkpoint views (the prepared waking-point).

design/47 §3 (the genesis-guardian family; a checkpoint is a PREPARED WAKING-POINT) + design/37 §5.
A CHECKPOINT is a persisted recovery ARTIFACT: `snapshot()` tree-state + a provenance triplet
(chain-head hash + founding pack sha + attestation head) — the wake checklist's steps 1-3 (body,
record, constitution) as data. Every probe here is a regression test (the campaign method). The
battery runs in DISPOSABLE test founding worlds; nothing real is checkpointed.

  A1  TestPersistRoundTrip        a checkpoint written to disk is snapshot() tree-state + the
                                  provenance triplet; read back, byte-identical to what was written.
                                  All THREE triplet members present or it is not a checkpoint (RW1).
  A2  TestHeadCheckIsO1           the pinned chain-head compared to the live head answers current-
                                  or-stale by a SINGLE hash comparison — no re-fold, no chain walk
                                  (RW2: a head check that folds/walks is refused by construction).
  A3  TestVerifiableWithoutEngine a checkpoint is checked against the record file and blob bytes
                                  ALONE — no gate, no views, no running engine; its tree folds from
                                  those records (the air rider :2963). RW3: verification cannot reach
                                  the engine — it holds no store/gate handle and imports none.
  A4  TestArtifactNotCapability   a checkpoint holds no runtime and recovers nothing on its own — it
                                  is data a runtime (EP-43) reads. Handing it to nothing recovers
                                  nothing; the capability boundary is stated, not assumed (RW4).
  TestRedWorlds                   RW1-RW4 driven THROUGH the instrument, named.

Honest bound (design/47 §3): a checkpoint recovers NOTHING itself — recovering FROM it (waking a
damaged system to it) is EP-43's runtime. This EP creates the artifact; it moves no founding, writes
no record, and makes no campaign-close claim.
"""

import inspect
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                            # noqa: E402  — the founding path (proven NON-attesting)
from kernel.compose import build_full_kernel                     # noqa: E402  — the compose layer (attests live at boot)
from kernel.blobs import BlobStore                               # noqa: E402
from kernel.canonical import canonical_hash                      # noqa: E402
from kernel.attestation import (                                 # noqa: E402
    ATTESTATION_ACTION, attest_boot, latest_attestation, register_attestation,
)
from bridge import checkpoint                                    # noqa: E402  — the module under test
from bridge import replay_snapshot                               # noqa: E402  — the reader the checkpoint REUSES

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")


def _write_file(store, blobs, path, content):
    """Put a blob and record FILE-CREATE + FILE-WRITE naming it — the record plane a content view
    reads (the test-world stand-in for the files ops, exactly as EP-41B's battery does it)."""
    h = blobs.put(content)
    store._append({"actor": "owner", "action": "FILE-CREATE", "object": path,
                   "rule_cited": "ROOT-NEG-5",
                   "payload": {"path": path, "node_type": "file", "perm": "644"}})
    store._append({"actor": "owner", "action": "FILE-WRITE", "object": path,
                   "rule_cited": "ROOT-NEG-5",
                   "payload": {"path": path, "content_hash": h, "length": len(content)}})
    return h


def _attesting_tree_world(dir_):
    """A disposable attesting world with a small tree: build the full kernel, register the owner-gated
    attestation op and run the compose-layer boot append (exactly what production compose holds inert
    until the owner's word — the test-world stand-in), and write two files so `snapshot(root='/')`
    returns a non-empty tree. Returns (store, gate, views, blobs, path, blob_dir)."""
    path = os.path.join(dir_, "record.jsonl")
    blob_dir = os.path.join(dir_, "blobs")
    store, gate, views, blobs, _subs = build_full_kernel(path, blob_dir)
    register_attestation(gate)                                   # the owner's word, landed
    attest_boot(store, gate)                                     # the compose-layer boot append, live
    _write_file(store, blobs, "/alpha", b"the first file's bytes")
    _write_file(store, blobs, "/beta", b"the second file's bytes")
    return store, gate, views, blobs, path, blob_dir


class TestPersistRoundTrip(unittest.TestCase):
    """A1 — THE CHECKPOINT PERSISTS AND ROUND-TRIPS (and RW1: all three triplet members present)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep44-a1-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_tree_world(self.dir)
        self.cp = checkpoint.create(self.store, self.path, self.blob_dir, root="/",
                                    pack_path=PACK_PATH)

    def test_a1_is_snapshot_plus_the_triplet(self):
        # The tree-state IS snapshot()'s output — reused, not re-folded.
        self.assertEqual(self.cp["tree"], replay_snapshot.snapshot(self.path, self.blob_dir, root="/"))
        # All three triplet members present and non-empty.
        prov = self.cp["provenance"]
        self.assertEqual(set(checkpoint.TRIPLET), set(prov))
        for member in checkpoint.TRIPLET:
            self.assertTrue(prov[member] and isinstance(prov[member], str))
        self.assertTrue(checkpoint.is_valid(self.cp))
        self.assertEqual(checkpoint.missing_members(self.cp), [])

    def test_a1_the_triplet_is_the_three_facts(self):
        prov = self.cp["provenance"]
        self.assertEqual(prov["chain_head"], canonical_hash(self.store.events[-1]))
        self.assertEqual(prov["founding_pack_sha"], canonical_hash(checkpoint.load_pack(PACK_PATH)))
        self.assertEqual(prov["attestation_head"], canonical_hash(latest_attestation(self.store)))

    def test_a1_write_read_is_byte_identical(self):
        f = os.path.join(self.dir, "cp.json")
        checkpoint.write(self.cp, f)
        with open(f, "rb") as fh:
            bytes1 = fh.read()
        back = checkpoint.read(f)
        self.assertEqual(back, self.cp)                          # read back equals what was written
        # Re-writing the read-back reproduces identical bytes: byte-identical round-trip.
        g = os.path.join(self.dir, "cp2.json")
        checkpoint.write(back, g)
        with open(g, "rb") as fh:
            bytes2 = fh.read()
        self.assertEqual(bytes1, bytes2)

    def test_rw1_a_two_thirds_checkpoint_is_refused(self):
        # Drop each triplet member in turn: the write refuses, is_valid rejects, verify fails.
        f = os.path.join(self.dir, "bad.json")
        for member in checkpoint.TRIPLET:
            bad = json.loads(json.dumps(self.cp))               # a deep copy
            del bad["provenance"][member]
            self.assertFalse(checkpoint.is_valid(bad), member)
            self.assertIn(member, checkpoint.missing_members(bad))
            with self.assertRaises(ValueError, msg=member):
                checkpoint.write(bad, f)
            self.assertFalse(checkpoint.verify(bad, self.path, self.blob_dir, PACK_PATH)["ok"], member)
        # A checkpoint with no tree at all is likewise not a checkpoint.
        no_tree = json.loads(json.dumps(self.cp))
        del no_tree["tree"]
        self.assertFalse(checkpoint.is_valid(no_tree))

    def test_rw1_create_refuses_without_a_body(self):
        # A world that never attested has no body (wake step 1): create refuses rather than emit a
        # two-thirds artifact.
        d = tempfile.mkdtemp(prefix="ep44-nobody-")
        self.addCleanup(shutil.rmtree, d, True)
        path = os.path.join(d, "record.jsonl")
        blob_dir = os.path.join(d, "blobs")
        blobs = BlobStore(blob_dir)
        store, gate, views = build_kernel(path, blobs=blobs)    # the founding path never attests
        _write_file(store, blobs, "/x", b"content, but the engine never attested")
        self.assertIsNone(latest_attestation(store))
        with self.assertRaises(ValueError):
            checkpoint.create(store, path, blob_dir, root="/", pack_path=PACK_PATH)


class TestHeadCheckIsO1(unittest.TestCase):
    """A2 — THE O(1) HEAD CHECK (and RW2: a head check that re-folds/walks is refused)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep44-a2-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_tree_world(self.dir)
        self.cp = checkpoint.create(self.store, self.path, self.blob_dir, root="/",
                                    pack_path=PACK_PATH)

    def test_a2_current_when_head_unmoved(self):
        live_head = canonical_hash(self.store.events[-1])
        self.assertEqual(checkpoint.check_head(self.cp, live_head), checkpoint.CURRENT)
        self.assertTrue(checkpoint.is_current(self.cp, live_head))

    def test_a2_stale_when_head_moved(self):
        # Append one record: the head moves, and the checkpoint is detected STALE.
        _write_file(self.store, self.blobs, "/gamma", b"a new file moves the head")
        new_live = canonical_hash(self.store.events[-1])
        self.assertNotEqual(new_live, self.cp["provenance"]["chain_head"])
        self.assertEqual(checkpoint.check_head(self.cp, new_live), checkpoint.STALE)
        self.assertFalse(checkpoint.is_current(self.cp, new_live))

    def test_rw2_the_check_holds_no_path_to_walk(self):
        # A head check that walked the chain or re-folded the record would need the record path or a
        # store. `check_head` takes neither: its only inputs are the checkpoint and a head STRING.
        params = list(inspect.signature(checkpoint.check_head).parameters)
        self.assertEqual(params, ["checkpoint", "live_head"])
        # It answers with the record file DELETED — proof it never reads it (cannot fold/walk).
        os.remove(self.path)
        shutil.rmtree(self.blob_dir, ignore_errors=True)
        self.assertEqual(checkpoint.check_head(self.cp, self.cp["provenance"]["chain_head"]),
                         checkpoint.CURRENT)
        self.assertEqual(checkpoint.check_head(self.cp, "sha256:deadbeef"), checkpoint.STALE)

    def test_rw2_verdict_depends_only_on_the_head_string(self):
        # The verdict is a function of the pinned head and the passed live head ONLY — not of the
        # tree, not of any record content. Same live head -> same verdict, regardless of the world.
        pinned = self.cp["provenance"]["chain_head"]
        self.assertEqual(checkpoint.check_head(self.cp, pinned), checkpoint.CURRENT)
        self.assertEqual(checkpoint.check_head(self.cp, pinned + "x"), checkpoint.STALE)


class TestVerifiableWithoutEngine(unittest.TestCase):
    """A3 — VERIFIABLE WITHOUT THE ENGINE (the air rider), and RW3."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep44-a3-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_tree_world(self.dir)
        self.cp = checkpoint.create(self.store, self.path, self.blob_dir, root="/",
                                    pack_path=PACK_PATH)

    def test_a3_verifies_from_files_alone(self):
        f = os.path.join(self.dir, "cp.json")
        checkpoint.write(self.cp, f)
        # Drop every engine handle: only the on-disk checkpoint and the record/blob/pack files remain.
        del self.store, self.gate, self.views, self.blobs
        cp = checkpoint.read(f)
        verdict = checkpoint.verify(cp, self.path, self.blob_dir, PACK_PATH)
        self.assertTrue(verdict["ok"], verdict)
        for member in ("tree", "chain_head", "founding_pack_sha", "attestation_head"):
            self.assertTrue(verdict[member], member)

    def test_a3_tree_folds_from_the_records(self):
        # The verified tree is the one that folds from the records — recomputed via the one reader,
        # not carried. Corrupt a blob and the tree no longer folds to the pinned state.
        cp = self.cp
        # tamper: append a record that changes the tree, so the recomputed tree diverges.
        _write_file(self.store, self.blobs, "/delta", b"a file the checkpoint never saw")
        verdict = checkpoint.verify(cp, self.path, self.blob_dir, PACK_PATH)
        self.assertFalse(verdict["tree"])                       # the tree moved; the checkpoint is not of this state
        self.assertFalse(verdict["ok"])

    def test_rw3_verification_cannot_reach_the_engine(self):
        # `verify` takes the checkpoint and FILE PATHS only — no store, no gate, no views. It cannot
        # call the engine because it holds no handle to one.
        params = list(inspect.signature(checkpoint.verify).parameters)
        self.assertEqual(params, ["checkpoint", "record_path", "blob_dir", "pack_path"])
        # And the module IMPORTS no gate and no views (the running engine): a static guard over the
        # import statements only (the words appear in prose describing what is excluded).
        with open(os.path.join(REPO, "src", "bridge", "checkpoint.py"), encoding="utf-8") as fh:
            src = fh.read()
        import_lines = [ln for ln in src.splitlines()
                        if ln.startswith("import ") or ln.startswith("from ")]
        for ln in import_lines:
            self.assertNotIn("gate", ln, ln)
            self.assertNotIn("views", ln, ln)
            self.assertNotIn("compose", ln, ln)                 # the composed running engine

    def test_rw3_a_stale_founding_is_caught_without_the_engine(self):
        # Verify against a DIFFERENT pack (a moved constitution): the founding sha diverges, caught
        # by the plain reader with no engine in sight.
        other = os.path.join(self.dir, "other-pack.json")
        pack = checkpoint.load_pack(PACK_PATH)
        pack["founding_version"] = "0.0.0-not-the-real-pack"
        with open(other, "w", encoding="utf-8") as fh:
            json.dump(pack, fh)
        verdict = checkpoint.verify(self.cp, self.path, self.blob_dir, other)
        self.assertFalse(verdict["founding_pack_sha"])
        self.assertFalse(verdict["ok"])


class TestArtifactNotCapability(unittest.TestCase):
    """A4 — ARTIFACT, NOT CAPABILITY (and RW4: a checkpoint claimed to recover)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep44-a4-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_tree_world(self.dir)
        self.cp = checkpoint.create(self.store, self.path, self.blob_dir, root="/",
                                    pack_path=PACK_PATH)

    def _assert_pure_data(self, value):
        if isinstance(value, dict):
            for k, v in value.items():
                self.assertIsInstance(k, str)
                self._assert_pure_data(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                self._assert_pure_data(v)
        else:
            self.assertIsInstance(value, (str, int, float, bool, type(None)))

    def test_a4_a_checkpoint_is_pure_data(self):
        # No callables, no runtime — JSON round-trips to an equal object.
        self._assert_pure_data(self.cp)
        self.assertEqual(json.loads(json.dumps(self.cp)), self.cp)

    def test_a4_the_module_has_no_recovery_verb(self):
        # The capability boundary is STATED: recovering FROM a checkpoint is EP-43. This module
        # exposes no verb that performs one.
        for name in ("recover", "restore", "apply", "wake", "rollback", "reinstate"):
            self.assertFalse(hasattr(checkpoint, name), name)

    def test_rw4_handing_it_to_nothing_recovers_nothing(self):
        # Reading and verifying a checkpoint changes NOTHING — the record and blobs are byte-identical
        # across the read/verify (it is data a runtime reads, never a runtime).
        with open(self.path, "rb") as fh:
            record_before = fh.read()
        blobs_before = sorted(os.listdir(self.blob_dir))
        f = os.path.join(self.dir, "cp.json")
        checkpoint.write(self.cp, f)
        cp = checkpoint.read(f)
        checkpoint.verify(cp, self.path, self.blob_dir, PACK_PATH)
        with open(self.path, "rb") as fh:
            self.assertEqual(fh.read(), record_before)          # the record did not move
        self.assertEqual(sorted(os.listdir(self.blob_dir)), blobs_before)
        # The checkpoint object itself carries no method that could recover.
        self.assertFalse(any(callable(v) for v in self.cp.values()))


class TestRedWorlds(unittest.TestCase):
    """RW1-RW4 driven through the instrument, named — the four ways a checkpoint stops being a
    waking-point, each recorded here so the negative is a regression test (§A42)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep44-rw-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_tree_world(self.dir)
        self.cp = checkpoint.create(self.store, self.path, self.blob_dir, root="/",
                                    pack_path=PACK_PATH)

    def test_rw1_missing_triplet_member(self):
        for member in checkpoint.TRIPLET:
            bad = json.loads(json.dumps(self.cp))
            del bad["provenance"][member]
            self.assertFalse(checkpoint.is_valid(bad), member)
            with self.assertRaises(ValueError):
                checkpoint.write(bad, os.path.join(self.dir, "x.json"))

    def test_rw2_head_check_does_not_fold(self):
        # No record path in the signature -> it cannot walk the chain or re-fold the record.
        self.assertEqual(list(inspect.signature(checkpoint.check_head).parameters),
                         ["checkpoint", "live_head"])

    def test_rw3_needs_no_engine(self):
        self.assertEqual(list(inspect.signature(checkpoint.verify).parameters),
                         ["checkpoint", "record_path", "blob_dir", "pack_path"])
        verdict = checkpoint.verify(self.cp, self.path, self.blob_dir, PACK_PATH)
        self.assertTrue(verdict["ok"], verdict)

    def test_rw4_no_recovery_verb(self):
        for name in ("recover", "restore", "apply", "wake"):
            self.assertFalse(hasattr(checkpoint, name), name)


if __name__ == "__main__":
    unittest.main()
