# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (recovery, checkpoint, chain adjudication, waking, splice); NON-GOAL: no offensive
# capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-43 (BUILD) — the RECOVER ceremony: waking damaged (design/47 §3; design/37 §5/:824; design/46 §3).

THE CRUX of ARC R, the genesis-guardian family. Recover and handover are ONE machine, two
directions (design/46 §3): a handover sends verified chain segments OUT; a RECOVER brings them IN —
waking a damaged system to an OLDER SOUND point the chain adjudicates as intact. On damage (the
chain breaks, content is missing) the recover ceremony, OWNER-GATED, brings verified segments in
(`duplicate_and_verify` inward), CHAIN-ADJUDICATED (`store.verify_chain` -> verified_through /
break_at, never a stored flag), VERIFIED AT LOAD (a corrupt segment HALTS, restoring nothing), and
it REFUSES any target that is not a lawful prior point of THIS record's own chain — the laundering-
door stays shut. It APPENDS one recover record and truncates/rewrites/deletes NOTHING (archi's
countersign, board :3024, load-bearing: rows past break_at STAY as adjudicated-broken history; a
recover that shortens the file is a STOP).

Every probe here is a regression test (the campaign method). The A1-A7 battery + RW1-RW4 + RW-F run
in DISPOSABLE build-full-kernel worlds on TEST content and a TEST recover LAW; nothing real is
recovered and the production founding pack is BYTE-UNTOUCHED (the recover-op create is owner-gated
and HELD — the EP-41B/EP-36 shape). The battery proves, in disposable stores:

  A1  TestRecoverToCheckpoint  given a checkpoint (EP-44) whose pinned head the chain adjudicates as
                               intact, the recover ceremony restores the record to that point,
                               bringing the segments in via duplicate_and_verify (byte-identity, the
                               inward direction); post-recover the recovered SOUND point reproduces
                               the checkpoint's tree while the live record keeps every row (never
                               truncates — exactly one splice row is added).
  A2  TestNeverToWrongness     a target that is NOT a lawful prior point of this chain (a fabricated
                               head; a state the record never lawfully held) is REFUSED at the
                               constitutional anchor — the laundering-door shut (RW1). The check can
                               pass: a REAL prior head is admitted.
  A3  TestChainAdjudicated     soundness is decided by the chain's OWN fold — a target within the
                               verified prefix admitted, a target beyond the break refused, citing
                               the fold (verified_through / break_at), never a stored flag.
  A4  TestVerifyAtLoad         the recovered state's content is RE-READ and hashed at load
                               (duplicate_and_verify); a corrupt OR missing segment HALTS the
                               recover, restoring nothing (RW2). Intact segments verify and are
                               recorded (a check that cannot fail is not a check).
  A5  TestOwnerGated           only the root authority holder (the chain-end, DERIVED) drives a
                               recover splice; a non-owner recover is refused at the anchor (RW3).
                               The owner's recover is admitted.
  A6  TestFoundingHeld         the recover-op create is LIVE (founding flips A+B): production
                               founding-pack.json CARRIES the recover LAW (RECOVER-LAW-GS14, the
                               1.35.0->1.36.0 bump — flip A), and production full-kernel compose
                               REGISTERS the recover op (flip B). The carries-check can fail (a
                               stripped pack reds it, RW-F); tests/era_pin.py byte-untouched (§A57 HELD).
  A7  (suite discover)         whole-ledger green is the verifier's re-run of the whole suite.

  NEVER-TRUNCATE control       archi's load-bearing binding: the recover APPENDS exactly one row;
                               the whole prior file (broken rows included) stays intact; no
                               truncation primitive lives in kernel.erasure.

HONEST CAP: this EP declares its OWN behaviour green only. It builds the ceremony (the recover op)
and proves it in TEST founding worlds; the production CREATE and the recovery-CAPACITY law (EP-45's)
are owner-gated and HELD. The recover records a splice that CITES the checkpoint (held once in the
EP-44 artifact, never duplicated into the record); wiring every content-resolving view to serve the
recovered point is a later round, not this EP's fence.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                      # noqa: E402
from kernel.canonical import canonical_hash                       # noqa: E402
from kernel.errors import OpError                                  # noqa: E402
from kernel import erasure                                        # noqa: E402
from bridge import checkpoint                                     # noqa: E402  (EP-44 — the CALLER reads it)
from bridge import replay_snapshot                                # noqa: E402  (demonstrate the recovered tree)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
ERA_PIN_PATH = os.path.join(REPO, "tests", "era_pin.py")

# The §A57 pin: tests/era_pin.py stands byte-for-byte (the era-pin sweep is HELD, a separate
# deliverable). Same digest test_ep41b pins — the two guards agree.
ERA_PIN_SHA = "19ebf106bcdd82753d46b5eb34146ee31c04e909dd9458b376e0271a4236eb87"

RECOVER_RULE = "RECOVER-DEMAND-1"                # a lawful recovery cites a rule (a test-world value)


def _declare_recover_law(store):
    """Declare the recover LAW in a test world — a CREATE-RULE appended directly (as genesis appends
    the constitution directly), the test-world stand-in for the HELD founding create."""
    store._append({
        "actor": "SYSTEM", "action": "CREATE-RULE", "object": erasure.RECOVER_LAW,
        "rule_cited": "BOOT-INT",
        "payload": {"kind": "rule", "rule_id": erasure.RECOVER_LAW, "root": True, "polarity": "+",
                    "text": "recover: on damage, the root authority holder may splice the record to "
                            "an OLDER SOUND point the chain adjudicates as intact, bringing verified "
                            "segments in, verified AT LOAD; it appends a recover record, rewrites and "
                            "deletes nothing, and never installs a state the record never lawfully held"},
    })


def _pack_recover_family_present(text):
    """Does the founding text carry ANY member of the recover family? The mechanical NO-BUMP signal —
    OWN vocabulary, direct, never a founding byte/version proxy. Under a live flip a member in the
    pack would be a version bump; the create is HELD, so the pack carries none."""
    return any(tok in text for tok in
               (erasure.RECOVER_RECORD, erasure.RECOVER_OP, erasure.RECOVER_LAW))


class RecoverWorld(unittest.TestCase):
    """A disposable test founding world: the full kernel composed (attestation live, so a checkpoint
    can be taken), the prefix sealed under a chain-anchor (so verify_chain can adjudicate breaks),
    the recover LAW declared, and the recover ceremony registered. The production create is HELD —
    A6 asserts the production pack byte-untouched and production compose recover-op-free."""

    def setUp(self):
        self._dir = tempfile.mkdtemp(prefix="ep43-")
        self.addCleanup(shutil.rmtree, self._dir, True)
        self.path = os.path.join(self._dir, "record.jsonl")
        self.blobdir = os.path.join(self._dir, "blobs")
        self.store, self.gate, self.views, self.blobs, _subs = build_full_kernel(self.path, self.blobdir)
        self.store.seal_prefix()                                  # anchor the prefix (break adjudication)
        # flip B reconciliation: the pack (1.36) supplies the recover LAW and full-kernel compose
        # registers the op, so the fixture mirrors production — no hand-declared law, no hand register.
        self.owner = self.views.chain_end()                      # the root authority holder (DERIVED)

    # --- record-plane helpers ----------------------------------------------------------------
    def _write_file(self, path, content):
        """Put a blob and record FILE-CREATE + FILE-WRITE naming it — the record plane a content view
        reads (the EP-41B/EP-44 test-world stand-in). Returns the content hash."""
        h = self.blobs.put(content)
        self.store._append({"actor": "owner", "action": "FILE-CREATE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "node_type": "file", "perm": "644"}})
        self.store._append({"actor": "owner", "action": "FILE-WRITE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "content_hash": h, "length": len(content)}})
        return h

    def _head_seq(self):
        return self.store.events[-1]["seq"]

    def _head_at(self, seq):
        """The chain head at `seq` — canonical_hash of the record at that seq (store.py:1044)."""
        return canonical_hash(self.store.events[seq - 1])

    def _take_checkpoint(self):
        return checkpoint.create(self.store, self.path, self.blobdir, root="/", pack_path=PACK_PATH)

    def _gather_segments(self, up_to_seq):
        """The content segments the recovered state depends on — the FILE-WRITE content hashes at or
        below `up_to_seq`, gathered by the caller (from the checkpoint's point / replicas)."""
        return [e["payload"]["content_hash"] for e in self.store.all()
                if e.get("action") == "FILE-WRITE" and e["seq"] <= up_to_seq]

    def _recover(self, target_head, checkpoint_ref, segments=(), rule=RECOVER_RULE, actor=None):
        params = {erasure.TARGET_HEAD: target_head, erasure.CHECKPOINT_REF: checkpoint_ref,
                  erasure.RECOVER_RULE: rule, "segments": list(segments)}
        return self.gate.execute(erasure.RECOVER_OP, self.owner if actor is None else actor, params)

    def _tamper_on_disk(self, seq):
        """Corrupt the record at `seq` on disk so its canonical_hash changes — the NEXT record's
        prev_hash no longer matches its recomputed predecessor, so verify_chain reports break_at at
        seq+1. Models real damage; the tampered record must have a successor for the break to show."""
        with open(self.path, encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f if ln.strip()]
        rec = json.loads(lines[seq - 1])
        if isinstance(rec.get("payload"), dict):
            rec["payload"] = dict(rec["payload"])
            rec["payload"]["_damage"] = "chain-break"
        else:
            rec["_damage"] = "chain-break"
        lines[seq - 1] = json.dumps(rec)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def _rebuild(self):
        """Replay the (possibly damaged) record file into a fresh kernel and re-register the recover
        op (a CODE registration; the recover LAW replays from the file). build_full_kernel's boot
        attestation is idempotent over an unchanged tree, so replay appends nothing — seqs are stable."""
        self.store, self.gate, self.views, self.blobs, _subs = build_full_kernel(self.path, self.blobdir)
        self.owner = self.views.chain_end()

    def _snapshot_of_prefix(self, up_to_seq):
        """The tree-state of the record's first `up_to_seq` rows — the SOUND point re-folded from the
        record + blobs alone (replay_snapshot has no as_of, so the caller writes the sound prefix to a
        temp file and folds it). This reproduces the checkpoint's tree, which was snapshot() at that
        seq — the recovered point, verified at load, WITHOUT touching the live (damaged) file."""
        tmp = os.path.join(self._dir, "prefix-%d.jsonl" % up_to_seq)
        with open(self.path, encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f if ln.strip()]
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines[:up_to_seq]) + "\n")
        return replay_snapshot.snapshot(tmp, self.blobdir, root="/")


# ============================================================================================
# A1 — RECOVER TO A SOUND CHECKPOINT. The chain adjudicates the checkpoint's head as intact; the
#      ceremony restores the record to that point, bringing the segments in via duplicate_and_verify.
# ============================================================================================

class TestRecoverToCheckpoint(RecoverWorld):

    def test_a1_recover_to_a_sound_checkpoint_after_damage_past_it(self):
        # A sound prefix, a checkpoint at S, then advance PAST S and DAMAGE — the chain breaks past
        # the checkpoint. Recover WAKES the record to S: the segments verify inward, the splice is
        # recorded, and the recovered sound point reproduces the checkpoint's tree.
        self._write_file("/alpha", b"the first file's bytes")
        self._write_file("/beta", b"the second file's bytes")
        cp = self._take_checkpoint()
        s = self._head_seq()                                       # the checkpoint's point
        target_head = cp["provenance"]["chain_head"]
        self.assertEqual(target_head, self._head_at(s))           # the checkpoint pins the seq-S head
        cp_ref = canonical_hash(cp)                               # FROM WHICH source
        segments = self._gather_segments(s)                      # the content the recovered state needs
        cp_tree = cp["tree"]

        # advance past the checkpoint, then damage a post-S row (with a successor, so the break shows)
        self._write_file("/gamma", b"gamma bytes, written after the checkpoint")
        g_write = self._head_seq()
        self._write_file("/delta", b"delta bytes, a successor so the break is visible")
        self._tamper_on_disk(g_write)
        self._rebuild()
        fold = self.store.verify_chain()
        self.assertIsNotNone(fold["break_at"])                    # a real break exists past the checkpoint
        self.assertGreaterEqual(fold["verified_through"], s)      # but S is still sound

        n_before = len(self.store.all())
        self._recover(target_head, cp_ref, segments)              # THE RECOVER
        rec = self.store.events[-1]                               # the splice
        p = rec["payload"]
        self.assertEqual(p["kind"], erasure.RECOVER_RECORD)              # a recover record
        self.assertEqual(p[erasure.TARGET_SEQ], s)                       # WHAT — the seq the chain adjudicated
        self.assertEqual(p[erasure.TARGET_HEAD], target_head)           # WHAT — by head hash
        self.assertEqual(p[erasure.CHECKPOINT_REF], cp_ref)             # FROM WHICH source
        self.assertEqual(list(p[erasure.SEGMENTS_VERIFIED]), segments)  # the segments verified at load
        self.assertEqual(p[erasure.ADJUDICATION]["verified_through"], fold["verified_through"])
        # the row envelope (board :3049): actor = the root, object = the sound point, target = this record
        self.assertEqual(rec["actor"], self.owner)
        self.assertEqual(rec["object"], target_head)
        self.assertIsNotNone(rec["target"])                             # target = this record (the seal identity)

        # NEVER TRUNCATES: exactly one row added (the splice); the broken rows past S STAY.
        self.assertEqual(len(self.store.all()), n_before + 1)
        # Post-recover the tree-state matches the checkpoint: the recovered SOUND point reproduces the
        # checkpoint's tree, while the live record keeps every row it held (append-only).
        self.assertEqual(self._snapshot_of_prefix(s), cp_tree)
        # The standing waking-point names the checkpoint's point.
        pt = erasure.recovered_point(self.store.all())
        self.assertEqual(pt[erasure.TARGET_SEQ], s)
        self.assertEqual(pt[erasure.CHECKPOINT_REF], cp_ref)

    def test_a1_the_recovered_point_is_derived_from_the_head_not_passed(self):
        # The op ADJUDICATES the seq from the head (the chain's own arithmetic); the caller passes a
        # head, never a seq. A recover to /alpha's point resolves that seq by hash.
        self._write_file("/alpha", b"alpha")
        s_alpha = self._head_seq()
        self._write_file("/beta", b"beta")
        cp = self._take_checkpoint()
        head_alpha = self._head_at(s_alpha)
        self._recover(head_alpha, canonical_hash(cp), self._gather_segments(s_alpha))
        self.assertEqual(self.store.events[-1]["payload"][erasure.TARGET_SEQ], s_alpha)


# ============================================================================================
# THE FOUR-FIELD ROW (board :3049, the owner's verbatim requirement, a by-name precision to the
# frozen plan). A recover ROW that does not carry all four is a STOP under §7(c).
# ============================================================================================

class TestFourFieldRow(RecoverWorld):

    def test_the_recover_row_carries_all_four_fields(self):
        # a sound prefix, a checkpoint at S, damage past S so break_at/broken_range are meaningful
        self._write_file("/a", b"a")
        self._write_file("/b", b"b")
        cp = self._take_checkpoint()
        s = self._head_seq()
        segments = self._gather_segments(s)
        self._write_file("/c", b"c after checkpoint")
        g_write = self._head_seq()
        self._write_file("/d", b"d, a successor")
        self._tamper_on_disk(g_write)
        self._rebuild()
        fold = self.store.verify_chain()
        head_seq = self.store.events[-1]["seq"]

        self._recover(cp["provenance"]["chain_head"], canonical_hash(cp), segments)
        p = self.store.events[-1]["payload"]

        # (1) WHAT REGION BROKE — break_at + the broken range
        self.assertEqual(p[erasure.BREAK_AT], fold["break_at"])
        self.assertEqual(list(p[erasure.BROKEN_RANGE]), [fold["break_at"], head_seq])
        # (2) WHAT WAS SOUND — verified_through
        self.assertEqual(p[erasure.VERIFIED_THROUGH], fold["verified_through"])
        # (3) WHAT WAS DONE — the checkpoint hash + every segment brought in, each BY HASH
        self.assertEqual(p[erasure.CHECKPOINT_REF], canonical_hash(cp))
        self.assertEqual(list(p[erasure.SEGMENTS_VERIFIED]), segments)
        for seg in p[erasure.SEGMENTS_VERIFIED]:
            self.assertTrue(seg.startswith("sha256:"))            # each segment, by hash
        # (4) WHAT HAPPENED — the outcome
        self.assertEqual(p[erasure.OUTCOME], erasure.OUTCOME_VERIFIED_AT_LOAD)
        # all four present at once — a row missing any is a STOP
        for field in (erasure.BREAK_AT, erasure.VERIFIED_THROUGH, erasure.CHECKPOINT_REF,
                      erasure.SEGMENTS_VERIFIED, erasure.OUTCOME):
            self.assertIn(field, p)


# ============================================================================================
# A2 — NEVER TO WRONGNESS. A target that is not a lawful prior point of this chain is REFUSED at
#      the constitutional anchor — the laundering-door shut (RW1). The check can pass.
# ============================================================================================

class TestNeverToWrongness(RecoverWorld):

    def test_a2_rw1_a_fabricated_head_is_refused_at_the_anchor(self):
        self._write_file("/f", b"real content")
        cp = self._take_checkpoint()
        s = self._head_seq()
        fabricated = "sha256:" + "a" * 64                          # a head this chain never held
        self.assertIsNone(erasure._seq_of_head(self.store, fabricated))
        n_before = len(self.store.all())
        with self.assertRaises(OpError) as cm:
            self._recover(fabricated, canonical_hash(cp), self._gather_segments(s))
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIn("never", str(cm.exception).lower())         # never to wrongness / laundering-door
        self.assertIsNone(erasure.recovered_point(self.store.all()))   # nothing spliced
        # A refusal is itself a recorded event (the record never goes dark), but no recover record stands.
        self.assertFalse(any(erasure.is_recover(e.get("payload")) for e in self.store.all()))

    def test_a2_a_state_the_record_never_lawfully_held_is_refused(self):
        # A head computed from a MODIFIED record — a state the chain never actually held — matches no
        # record and is refused. Recover installs only a past the record HELD.
        self._write_file("/f", b"real content")
        real = dict(self.store.events[-1])
        real["payload"] = dict(real["payload"])
        real["payload"]["length"] = 999999                        # a length this write never had
        never_held = canonical_hash(real)
        self.assertIsNone(erasure._seq_of_head(self.store, never_held))
        with self.assertRaises(OpError) as cm:
            self._recover(never_held, "cp-ref", segments=())
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)

    def test_a2_the_check_can_pass_a_real_prior_head_is_admitted(self):
        # The discrimination direction (a check that cannot fail is not a check): a REAL prior head is
        # admitted — the door opens for the lawful past.
        self._write_file("/f", b"content")
        cp = self._take_checkpoint()
        s = self._head_seq()
        self._recover(cp["provenance"]["chain_head"], canonical_hash(cp), self._gather_segments(s))
        self.assertIsNotNone(erasure.recovered_point(self.store.all()))


# ============================================================================================
# A3 — CHAIN-ADJUDICATED (RW4). Soundness is decided by the chain's OWN fold, never a stored flag.
# ============================================================================================

class TestChainAdjudicated(RecoverWorld):

    def _damaged_three(self):
        """Three post-anchor files; damage the /b write so break_at falls between /b and /c."""
        self._write_file("/a", b"a")
        s_a = self._head_seq()
        self._write_file("/b", b"b")
        s_b = self._head_seq()
        self._write_file("/c", b"c")
        s_c = self._head_seq()
        self._tamper_on_disk(s_b)                                 # break at s_b + 1
        self._rebuild()
        return s_a, s_b, s_c

    def test_a3_within_the_verified_prefix_admitted_beyond_the_break_refused(self):
        s_a, s_b, s_c = self._damaged_three()
        fold = self.store.verify_chain()
        self.assertEqual(fold["break_at"], s_b + 1)               # the fold LOCATES the break
        self.assertEqual(fold["verified_through"], s_b)

        # a target WITHIN the verified prefix (s_a < break) is admitted
        self._recover(self._head_at(s_a), "cp-ref", segments=[self._gather_segments(s_a)[0]])
        self.assertEqual(self.store.events[-1]["payload"][erasure.TARGET_SEQ], s_a)

        # the SAME kind of target, but BEYOND the break (s_c > verified_through), is refused
        with self.assertRaises(OpError) as cm:
            self._recover(self._head_at(s_c), "cp-ref", segments=[])
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIn("verified_through", str(cm.exception).lower())   # cited the fold, not a flag

    def test_a3_rw4_the_same_target_flips_when_the_chain_breaks_before_it(self):
        # RW4: adjudication is the FOLD, not a stored flag. A target admitted on an intact chain
        # becomes refused once a break is introduced BEFORE it — no flag touched, only recomputation.
        self._write_file("/a", b"a")
        s_a = self._head_seq()
        self._write_file("/target", b"the target's own content")
        s_t = self._head_seq()
        self._write_file("/tail", b"a successor so a break before the target is visible")
        target_head = self._head_at(s_t)

        # intact chain: the target is within the verified prefix -> admitted
        self.assertLessEqual(s_t, self.store.verify_chain()["verified_through"])
        self._recover(target_head, "cp-ref", segments=[self._gather_segments(s_t)[-1]])
        self.assertEqual(self.store.events[-1]["payload"][erasure.TARGET_SEQ], s_t)

        # now break the chain BEFORE the target (damage /a's write) — the SAME target flips to refused
        self._tamper_on_disk(s_a)
        self._rebuild()
        fold = self.store.verify_chain()
        self.assertLess(fold["verified_through"], s_t)            # the target is now beyond the break
        self.assertEqual(self._head_at(s_t), target_head)         # the target record itself is unchanged
        with self.assertRaises(OpError) as cm:
            self._recover(target_head, "cp-ref", segments=[])
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)


# ============================================================================================
# A4 — VERIFY AT LOAD (RW2). The recovered state's content is re-read and hashed; a corrupt or
#      missing segment HALTS the recover, restoring nothing. Intact segments verify and are recorded.
# ============================================================================================

class TestVerifyAtLoad(RecoverWorld):

    def test_a4_rw2_a_corrupt_segment_halts_the_recover_restoring_nothing(self):
        h = self._write_file("/f", b"the recovered state depends on this content")
        cp = self._take_checkpoint()
        s = self._head_seq()
        # corrupt the blob on disk so its bytes no longer rehash to h (a byte-to-byte mismatch)
        digest = h.split(":", 1)[1]
        blobpath = os.path.join(self.blobdir, digest[:2], digest[2:])
        with open(blobpath, "wb") as fh:
            fh.write(b"tampered bytes that do not hash to the named segment")
        with self.assertRaises(OpError) as cm:
            self._recover(cp["provenance"]["chain_head"], canonical_hash(cp), segments=[h])
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIn("load", str(cm.exception).lower())          # verify-at-load, not trust-then-check
        # (4) HALTED with the failing segment NAMED (board :3049)
        self.assertIn(erasure.OUTCOME_HALTED, str(cm.exception))
        self.assertIn(h, str(cm.exception))                       # the failing segment, by hash
        # restoring NOTHING: no recover record, no waking-point (the refusal is recorded; nothing spliced)
        self.assertIsNone(erasure.recovered_point(self.store.all()))
        self.assertFalse(any(erasure.is_recover(e.get("payload")) for e in self.store.all()))

    def test_a4_a_missing_segment_halts_the_recover(self):
        h = self._write_file("/f", b"content")
        cp = self._take_checkpoint()
        absent = "sha256:" + hashlib.sha256(b"never stored locally").hexdigest()
        with self.assertRaises(OpError) as cm:
            self._recover(cp["provenance"]["chain_head"], canonical_hash(cp), segments=[h, absent])
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIsNone(erasure.recovered_point(self.store.all()))

    def test_a4_intact_segments_verify_and_are_recorded(self):
        # the can-PASS direction: intact segments verify byte-to-byte and the splice records them.
        h1 = self._write_file("/a", b"aaa")
        h2 = self._write_file("/b", b"bbb")
        cp = self._take_checkpoint()
        s = self._head_seq()
        self._recover(cp["provenance"]["chain_head"], canonical_hash(cp), segments=[h1, h2])
        self.assertEqual(list(self.store.events[-1]["payload"][erasure.SEGMENTS_VERIFIED]), [h1, h2])


# ============================================================================================
# A5 — OWNER-GATED (RW3). Only the root authority holder (the chain-end, DERIVED) drives a splice.
# ============================================================================================

class TestOwnerGated(RecoverWorld):

    def test_a5_rw3_a_non_owner_recover_is_refused_at_the_anchor(self):
        h = self._write_file("/f", b"content")
        cp = self._take_checkpoint()
        s = self._head_seq()
        self.assertNotEqual(self.owner, "mallory")                # mallory is not the root
        n_before = len(self.store.all())
        with self.assertRaises(OpError) as cm:
            self._recover(cp["provenance"]["chain_head"], canonical_hash(cp),
                          self._gather_segments(s), actor="mallory")
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIn("root authority", str(cm.exception).lower())
        self.assertIsNone(erasure.recovered_point(self.store.all()))   # nothing spliced by a non-owner

    def test_a5_the_owner_recover_is_admitted(self):
        h = self._write_file("/f", b"content")
        cp = self._take_checkpoint()
        s = self._head_seq()
        self._recover(cp["provenance"]["chain_head"], canonical_hash(cp),
                      self._gather_segments(s), actor=self.owner)
        self.assertIsNotNone(erasure.recovered_point(self.store.all()))


# ============================================================================================
# NEVER-TRUNCATE control (archi's countersign, board :3024, load-bearing).
# ============================================================================================

class TestNeverTruncates(RecoverWorld):

    def test_recover_appends_exactly_one_row_and_never_shortens_the_file(self):
        self._write_file("/a", b"a")
        self._write_file("/b", b"b")
        cp = self._take_checkpoint()
        s = self._head_seq()
        self._write_file("/c", b"c after checkpoint")
        g_write = self._head_seq()
        self._write_file("/d", b"d, a successor")
        self._tamper_on_disk(g_write)
        self._rebuild()
        seqs_before = [e["seq"] for e in self.store.all()]
        self._recover(cp["provenance"]["chain_head"], canonical_hash(cp), self._gather_segments(s))
        seqs_after = [e["seq"] for e in self.store.all()]
        self.assertEqual(seqs_after[:len(seqs_before)], seqs_before)   # the whole prior file is intact
        self.assertEqual(len(seqs_after), len(seqs_before) + 1)        # exactly one row added: the splice
        self.assertGreater(len(self.store.all()), s + 1)              # the broken rows past S are STILL present

    def test_recover_refuses_to_shorten_a_shorten_shaped_call_appends_and_drops_nothing(self):
        # F7 (DIGEST-C4): the never-truncate property is otherwise carried by a SOURCE GREP (the sibling
        # below). This is the POSITIVE behavioural arm — FEED the recover path a shorten-attempt and prove
        # the append-only property BY THE ATTEMPT, not only by a grep. A careless recover would "roll back
        # to the checkpoint" by DELETING the tail; this one cannot — its only write is the gate's single
        # append. Build a substantial tail past the sound point (rows a truncation would drop), then drive
        # recover to the earlier point WITH a shorten-shaped instruction the op has no vocabulary for
        # (`truncate_to` / `remove_rows`). The gate refuses to shorten: the shorten-shaped keys are inert,
        # the whole prior file survives BYTE-IDENTICAL, and exactly one row (the splice) is appended. If the
        # record had SHORTENED instead, that is a real defect (a STOP/RAISE), not test hygiene — asserted here.
        self._write_file("/a", b"a")
        cp = self._take_checkpoint()
        s = self._head_seq()                                          # the sound point the checkpoint pins
        for i in range(5):                                            # a TAIL a truncating recover would drop
            self._write_file("/tail-%d" % i, b"tail row %d" % i)
        g_write = self._head_seq()
        self._write_file("/last", b"a successor so the break is visible")
        self._tamper_on_disk(g_write)
        self._rebuild()
        before = [canonical_hash(e) for e in self.store.all()]        # every prior row, by canonical hash
        # FEED THE SHORTEN-ATTEMPT: the earlier sound target + shorten-shaped keys (truncate_to / remove_rows)
        self.gate.execute(erasure.RECOVER_OP, self.owner,
                          {erasure.TARGET_HEAD: cp["provenance"]["chain_head"],
                           erasure.CHECKPOINT_REF: canonical_hash(cp),
                           erasure.RECOVER_RULE: RECOVER_RULE,
                           "segments": self._gather_segments(s),
                           "truncate_to": s, "remove_rows": list(range(s + 1, g_write + 1))})
        after = [canonical_hash(e) for e in self.store.all()]
        # THE GATE REFUSED TO SHORTEN: the whole prior file survives byte-identical (nothing removed or
        # rewritten), the tail a truncation would have dropped is ALL still present, and the record GREW.
        self.assertEqual(after[:len(before)], before)                 # every prior row byte-identical, present
        self.assertEqual(len(after), len(before) + 1)                 # exactly one row appended: the splice
        self.assertGreater(len(after), len(before))                   # append-only: the file never shortened

    def test_kernel_erasure_carries_no_record_truncation_primitive(self):
        # capability-absence, the §8-j shape: the recover module holds no path that shortens the
        # record. "truncate" and an events-list reassignment/slice are absent (the handover's byte
        # "remove" is content, not a record — it is not checked here).
        with open(os.path.join(REPO, "src", "kernel", "erasure.py"), encoding="utf-8") as fh:
            src = fh.read()
        for forbidden in ("truncate", "self.store.events =", "events[:", "del self.store"):
            self.assertNotIn(forbidden, src,
                             "kernel.erasure must carry no record-truncation path (recover never shortens)")


# ============================================================================================
# A6 — FOUNDING-MOVE HELD (RW-F). The recover-op CREATE is owner-gated and HELD.
# ============================================================================================

class TestFoundingHeld(unittest.TestCase):

    def test_a6_production_founding_carries_the_recover_law_after_the_move(self):
        # EP-FND-RECOVER-LAW (founding flip A): the recover LAW landed as a data-born row in the
        # PRODUCTION CONVENTION SHAPE (PC_RUNTIME / CREATE-RULE / non-root / scope space:root), MINOR
        # 1.35.0 -> 1.36.0. Production founding now carries the recover family — its LAW member; the
        # decision kind and the op are code-born (unit B) and never enter the pack.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        self.assertTrue(_pack_recover_family_present(real),
                        "production founding declares NO recover-family member — the recover LAW "
                        "create did not land")

    def test_a6_rw_f_the_carries_check_can_fail_a_stripped_pack_reds_it(self):
        # §A64 — a check that cannot fail is not a check. Strip the LAW's id from a COPY of the pack:
        # the recover family goes absent and the carries-check would RED, while production stays
        # byte-untouched. The pack's ONLY recover-family member is the LAW (the decision kind and the
        # op are code-born, unit B), so removing it removes the family.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        stripped = real.replace(erasure.RECOVER_LAW, "SOME-OTHER-RULE-ID")
        self.assertFalse(_pack_recover_family_present(stripped))  # without the LAW, the carries-check reds

    def test_a6_production_compose_now_registers_the_recover_op(self):
        # flip B (EP-FND-RECOVER-REGISTER): the create LANDED — production full-kernel compose registers
        # the recover op (the register_ceremony / register_attestation compose-layer shape), live at boot.
        # Before the compose edit this assertion REDS (build_full_kernel did not register it); after, live.
        d = tempfile.mkdtemp(prefix="ep43-live-")
        self.addCleanup(shutil.rmtree, d, True)
        _store, gate, _views, _blobs, _subs = build_full_kernel(
            os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"))
        self.assertTrue(gate.has(erasure.RECOVER_OP),
                        "production compose must register the recover op — the create landed (flip B)")

    def test_a6_era_pin_is_byte_untouched(self):
        # the §A57 era-pin sweep is HELD (a separate deliverable); era_pin bytes stand.
        with open(ERA_PIN_PATH, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, ERA_PIN_SHA,
                         "tests/era_pin.py bytes changed — the §A57 sweep is HELD, not part of EP-43")


# ============================================================================================
# STRUCTURE — the nonconforming-call half (AR-2): a recover without a named point / source / rule
#             refuses BEFORE the handler, as a nonconforming call, not at the anchor.
# ============================================================================================

class TestNonconformingCall(RecoverWorld):

    def test_a_recover_without_a_target_head_is_a_nonconforming_call(self):
        cp = self._take_checkpoint()
        with self.assertRaises(OpError) as cm:
            self._recover(None, canonical_hash(cp), segments=())
        self.assertEqual(cm.exception.rule, "AR-2")               # structural, not the domain anchor

    def test_a_recover_without_a_checkpoint_ref_is_a_nonconforming_call(self):
        self._write_file("/f", b"content")
        s = self._head_seq()
        with self.assertRaises(OpError) as cm:
            self._recover(self._head_at(s), None, segments=())
        self.assertEqual(cm.exception.rule, "AR-2")


if __name__ == "__main__":
    unittest.main()
