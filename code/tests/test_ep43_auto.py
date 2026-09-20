# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (auto-recover, triple check, checkpoint hash rematch, diving-buddy cross-attestation,
# halt-and-notify, fail-safe). NON-GOAL: no offensive capability of any kind. Full declaration:
# SCOPE-STATEMENT.md.
"""EP-43-AUTO (BUILD) — AUTO-RECOVER under the TRIPLE CHECK: the recover ceremony's fail-safe SECOND
trigger (owner ruling board :3057; design/37 §5, design/47 §4; ARC R, the genesis-guardian family).

The recover ceremony (EP-43) carries ONE trigger — the manual owner-gated splice. This battery proves
the SECOND: an AUTO recover under a TRIPLE CHECK (bridge/auto_recover.py), refining "never automatic"
to "automatic ONLY under a triple check that halts on any doubt" (reasoning-standard R7 — the later
owner ruling controls; the earlier reason, "an auto-repair door is a laundering door", is HONOURED
because the chain's never-to-wrongness is one of the three, unchanged). Auto is a STRICTER gate than
manual and a fail-safe by construction (avoid-fail beats maximize-success — "nuclear-plant-grade").

Every probe is a regression test (the campaign method). The battery runs in DISPOSABLE
build-full-kernel worlds on TEST content; nothing real is recovered and PRODUCTION founding-pack.json
is BYTE-UNTOUCHED (the auto-trigger amend is HELD; it rides the governed AMEND-OP door in a TEST world
and flips live on the owner's mover). The three checks COMPOSE three that ALREADY exist — the chain
(erasure), the checkpoint hash rematch (EP-44 check_head), the buddy mutual receipt (EP-45
pairing_verdict) — so NO new founding kind, NO new check-kind, NO version bump.

  A1  TestAutoProceedsOnTripleMatch  chain sound + checkpoint CURRENT (hash rematch) + buddy verifies
                                     -> NOTIFY and AUTOPROCEED; the splice carries the triple-check
                                     outcome (chain ✓, checkpoint ✓, buddy ✓) and never truncates.
  A2  TestAnyFailureHalts            break exactly ONE of the three (chain / checkpoint / buddy), and
                                     also verify-at-load -> in EACH case HALT, NOTIFY, append NO splice
                                     (RW1: nuclear-plant-grade is not a two-of-three vote).
  A3  TestNeverToWrongnessAuto       an AUTO recover to a FABRICATED head is REFUSED by the chain check
                                     at BOTH layers (the bridge halts; the kernel refuses even when
                                     handed an all-pass triple check) — the laundering-door shut (RW2).
  A4  TestManualPathIntact           the manual owner-gated recover is UNCHANGED — same gate, same four
                                     laws, same row (no trigger / no triple_check keys). Additive (RW4).
  A5  TestAutoNeverTruncates         the auto splice APPENDS one row; rows past break_at stay; nothing
                                     is removed, rewritten, or shortened (the :3024 law under auto, RW3).
  A6  (auto-trigger LIVE)            the recover op DECLARES the auto-trigger (code-registered, founded
                                     at boot); production founding byte-untouched; no new kind/check/bump (RW6).
  A7  TestLayering                   the orchestrator is BRIDGE and composes the kernel op + bridge
                                     checks; the kernel imports no bridge; the target head is a param.
  A8  (whole-ledger sweep)           the verifier's per-module re-run; not asserted here.

HONEST CAP: this EP declares its OWN behaviour green only — it adds the auto trigger under the triple
check, moves no PRODUCTION founding, changes no manual path, needs nothing new, and makes no
campaign-close claim (that is EP-42's, which stays last).
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                       # noqa: E402
from kernel.canonical import canonical_hash                        # noqa: E402
from kernel.errors import OpError                                   # noqa: E402
from kernel import erasure                                         # noqa: E402
from kernel.opdefs import STRUCTURAL_PARAMS                        # noqa: E402
from bridge import checkpoint                                      # noqa: E402  (EP-44 — check_head, the hash rematch)
from bridge import merkle                                          # noqa: E402  (EP-45 — the Merkle root)
from bridge import replay_snapshot                                 # noqa: E402  (the tree-state reader, REUSED)
from bridge import auto_recover                                    # noqa: E402  (the module under test)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

RECOVER_RULE = "RECOVER-DEMAND-1"                # a lawful recovery cites a rule (a test-world value)

# THE AUTO-TRIGGER AMEND IS HELD (§8-f): production carries no auto-recover material. The old pin here
# was a whole-pack sha256 + a version literal — RETIRED (board :3121; EP-SHAPE.md:870), because BOTH
# move with any lawful founding change (the OPEN-CONTENT activation's 1.37.0 → 1.38.0 bump moved them,
# with nothing about the auto path having changed) and so cannot tell an auto-amend from another bump.
# test_a6 below proves the held state at the DEFINITION level instead — the auto-trigger's own
# `triple_check` material, absent from the live recover op and from the pack's op_definition records.


class AutoWorld(unittest.TestCase):
    """A disposable test founding world mirroring EP-43's RecoverWorld: the full kernel composed
    (attestation live at boot, so a checkpoint can be taken; the recover op registered — flips A+B
    landed), the prefix sealed so verify_chain adjudicates breaks. Adds the buddy-pair helpers the
    auto path composes over."""

    def setUp(self):
        self._dir = tempfile.mkdtemp(prefix="ep43auto-")
        self.addCleanup(shutil.rmtree, self._dir, True)
        self.path = os.path.join(self._dir, "record.jsonl")
        self.blobdir = os.path.join(self._dir, "blobs")
        self.store, self.gate, self.views, self.blobs, _subs = build_full_kernel(self.path, self.blobdir)
        self.store.seal_prefix()                                  # anchor the prefix (break adjudication)
        self.owner = self.views.chain_end()                      # the root authority holder (DERIVED)

    # --- record-plane helpers (the EP-43/EP-44/EP-45 test-world stand-in) ----------------------
    def _write_file(self, path, content):
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
        return canonical_hash(self.store.events[seq - 1])

    def _live_head(self):
        return canonical_hash(self.store.events[-1])

    def _gather_segments(self, up_to_seq):
        return [e["payload"]["content_hash"] for e in self.store.all()
                if e.get("action") == "FILE-WRITE" and e["seq"] <= up_to_seq]

    def _buddy_pair(self, witness_a="fold-chip", witness_b="fold-disk", frozen=True):
        """Two cross-attested checkpoints over the CURRENT tree, each carrying the OTHER's root — a
        MUTUAL RECEIPT (EP-45). When `frozen` the pairing binds to independent FROZEN replica record
        files (the diving-buddy's two bodies at the checkpoint point), so the receipt is stable as the
        live record advances (the real replicas). Returns (cp_a, cp_b, buddy_pair_tuple)."""
        root_val = merkle.merkle_root(replay_snapshot.snapshot(self.path, self.blobdir, root="/"))
        cp_a = checkpoint.cross_attest(self.store, self.path, self.blobdir, witness=witness_a,
                                       root="/", peer_root=root_val, pack_path=PACK_PATH)
        cp_b = checkpoint.cross_attest(self.store, self.path, self.blobdir, witness=witness_b,
                                       root="/", peer_root=root_val, pack_path=PACK_PATH)
        if frozen:
            ra = os.path.join(self._dir, "replica-a-%d.jsonl" % self._head_seq())
            rb = os.path.join(self._dir, "replica-b-%d.jsonl" % self._head_seq())
            shutil.copyfile(self.path, ra)   # C7 P3b-5c: content only, no file-mode (I7)
            shutil.copyfile(self.path, rb)   # C7 P3b-5c: content only, no file-mode (I7)
            pair = (cp_a, ra, self.blobdir, cp_b, rb, self.blobdir)
        else:
            pair = (cp_a, self.path, self.blobdir, cp_b, self.path, self.blobdir)
        return cp_a, cp_b, pair

    def _auto(self, cp_a, target_head, pair, segments, checkpoint_ref=None, rule=RECOVER_RULE,
              notify=None):
        return auto_recover.auto_recover(
            self.gate, self.store, cp_a, target_head,
            checkpoint_ref if checkpoint_ref is not None else canonical_hash(cp_a),
            segments, rule, pair, notify=notify)

    def _tamper_on_disk(self, seq):
        with open(self.path, encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f if ln.strip()]
        rec = json.loads(lines[seq - 1])
        if isinstance(rec.get("payload"), dict):
            rec["payload"] = dict(rec["payload"])
            rec["payload"]["_damage"] = "chain-break"
        else:
            rec["_damage"] = "chain-break"
        lines[seq - 1] = json.dumps(rec)
        # C7 P3b-5c: the tampered record lands in a FRESH file (a served create) and self.path is
        # repointed to it — never reopen the present governed record with 'w' (an O_TRUNC reset the
        # body refuses). _rebuild replays this fresh damaged file; the original record is untouched.
        self._tamper_n = getattr(self, "_tamper_n", 0) + 1
        newpath = os.path.join(self._dir, "record-tampered-%d.jsonl" % self._tamper_n)
        with open(newpath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self.path = newpath

    def _rebuild(self):
        self.store, self.gate, self.views, self.blobs, _subs = build_full_kernel(self.path, self.blobdir)
        self.owner = self.views.chain_end()


# ============================================================================================
# A1 — AUTO PROCEEDS ON A TRIPLE MATCH.
# ============================================================================================

class TestAutoProceedsOnTripleMatch(AutoWorld):

    def test_a1_triple_match_notifies_and_autoproceeds_the_splice_carries_the_outcome(self):
        self._write_file("/alpha", b"the first file's bytes")
        self._write_file("/beta", b"the second file's bytes")
        s = self._head_seq()
        cp_a, _cp_b, pair = self._buddy_pair()                    # a checkpoint + buddy over the current tree
        target_head = cp_a["provenance"]["chain_head"]
        self.assertEqual(target_head, self._live_head())          # checkpoint CURRENT -> the hash rematches
        segments = self._gather_segments(s)

        notes = []
        n_before = len(self.store.all())
        res = self._auto(cp_a, target_head, pair, segments, notify=notes.append)

        # the triple check passed — all three, and the auto path AUTOPROCEEDED
        self.assertEqual(res["outcome"], auto_recover.AUTOPROCEEDED)
        self.assertTrue(res["triple_check"]["ok"])
        for name in ("chain", "checkpoint", "buddy"):
            self.assertTrue(res["triple_check"][name], name)
        self.assertTrue(res["spliced"])

        # NOTIFY = the recover ROW itself (:3082 precision 2); the governed callback carries the same event
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["outcome"], auto_recover.AUTOPROCEEDED)

        # the splice records the triple-check outcome and marks the trigger AUTO
        splice = self.store.events[-1]
        p = splice["payload"]
        self.assertEqual(p["kind"], erasure.RECOVER_RECORD)
        self.assertEqual(p[erasure.TRIGGER], erasure.TRIGGER_AUTO)
        self.assertEqual(p[erasure.TRIPLE_CHECK], {"chain": True, "checkpoint": True, "buddy": True})
        self.assertEqual(splice["actor"], "SYSTEM")               # the automatic trigger, not the owner's hand
        # the four EP-43 fields still stand under auto (board :3049)
        for field in (erasure.BREAK_AT, erasure.VERIFIED_THROUGH, erasure.CHECKPOINT_REF,
                      erasure.SEGMENTS_VERIFIED, erasure.OUTCOME):
            self.assertIn(field, p)
        self.assertEqual(p[erasure.OUTCOME], erasure.OUTCOME_VERIFIED_AT_LOAD)
        self.assertEqual(list(p[erasure.SEGMENTS_VERIFIED]), segments)

        # never truncates: exactly one row added (the splice); the standing waking-point names the point
        self.assertEqual(len(self.store.all()), n_before + 1)
        pt = erasure.recovered_point(self.store.all())
        self.assertEqual(pt[erasure.CHECKPOINT_REF], canonical_hash(cp_a))


# ============================================================================================
# A2 — ANY ONE FAILURE HALTS AND NOTIFIES, RESTORES NOTHING (RW1).
# ============================================================================================

class TestAnyFailureHalts(AutoWorld):

    def _assert_halted_no_splice(self, res, expect_failed):
        self.assertEqual(res["outcome"], auto_recover.HALTED)
        self.assertFalse(res["spliced"])
        for name in expect_failed:
            self.assertFalse(res["triple_check"][name], name)
        # RESTORING NOTHING — no recover splice stands, no waking-point
        self.assertIsNone(erasure.recovered_point(self.store.all()))
        self.assertFalse(any(erasure.is_recover(e.get("payload")) for e in self.store.all()))

    def test_a2c_buddy_one_sided_halts_chain_and_checkpoint_still_pass(self):
        # the CLEANEST single-check isolation (RW1: two-of-three does NOT proceed). chain sound,
        # checkpoint CURRENT, but the buddy receipt is ONE-SIDED (B carries the wrong root) -> halt.
        self._write_file("/f", b"content")
        s = self._head_seq()
        root_val = merkle.merkle_root(replay_snapshot.snapshot(self.path, self.blobdir, root="/"))
        cp_a = checkpoint.cross_attest(self.store, self.path, self.blobdir, witness="fold-chip",
                                       root="/", peer_root=root_val, pack_path=PACK_PATH)
        cp_b_bad = checkpoint.cross_attest(self.store, self.path, self.blobdir, witness="fold-disk",
                                           root="/", peer_root="sha256:" + "0" * 64, pack_path=PACK_PATH)
        pair = (cp_a, self.path, self.blobdir, cp_b_bad, self.path, self.blobdir)
        notes = []
        res = self._auto(cp_a, cp_a["provenance"]["chain_head"], pair, self._gather_segments(s),
                         notify=notes.append)
        self._assert_halted_no_splice(res, ["buddy"])
        self.assertTrue(res["triple_check"]["chain"])             # chain still passed
        self.assertTrue(res["triple_check"]["checkpoint"])        # checkpoint still passed
        # F3 (DIGEST-C4): a single-check HALT still FIRES the notify callback (the owner is told, :3082)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["outcome"], auto_recover.HALTED)
        # two-of-three did NOT proceed — the whole safety of loosening "never automatic"

    def test_a2b_checkpoint_stale_moved_halts_chain_and_buddy_still_pass(self):
        # the live head MOVED past the checkpoint -> the hash does NOT rematch (STALE). chain sound
        # (the target is still a lawful prior point), buddy stable over frozen replicas -> only the
        # checkpoint fails, and the auto path halts.
        self._write_file("/f", b"content")
        s = self._head_seq()
        cp_a, _cp_b, pair = self._buddy_pair(frozen=True)         # frozen replicas -> buddy stable as head moves
        self.assertEqual(checkpoint.check_head(cp_a, self._live_head()), checkpoint.CURRENT)
        self._write_file("/g", b"a write that advances the head past the checkpoint")  # MOVE the head
        self.assertEqual(checkpoint.check_head(cp_a, self._live_head()), checkpoint.STALE)
        notes = []
        res = self._auto(cp_a, cp_a["provenance"]["chain_head"], pair, self._gather_segments(s),
                         notify=notes.append)
        self._assert_halted_no_splice(res, ["checkpoint"])
        self.assertTrue(res["triple_check"]["chain"])
        self.assertTrue(res["triple_check"]["buddy"])
        # F3 (DIGEST-C4): a single-check HALT still FIRES the notify callback (the owner is told, :3082)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["outcome"], auto_recover.HALTED)

    def test_a2a_chain_broken_before_the_target_halts_checkpoint_and_buddy_still_pass(self):
        # a real chain BREAK before the target -> the target is beyond verified_through (chain False).
        # The checkpoint + buddy are taken over the CURRENT (post-break) state, so they rematch (the
        # checkpoint is CURRENT, the buddy stable): only the chain fails, and the auto path halts.
        self._write_file("/a", b"a")
        s_a = self._head_seq()
        self._write_file("/target", b"the target's own content")
        s_t = self._head_seq()
        self._write_file("/tail", b"a successor so a break before the target is visible")
        self._tamper_on_disk(s_a)                                 # break at s_a + 1
        self._rebuild()
        fold = self.store.verify_chain()
        self.assertEqual(fold["break_at"], s_a + 1)
        self.assertLess(fold["verified_through"], s_t)            # the target is now beyond the break
        cp_a, _cp_b, pair = self._buddy_pair(frozen=True)         # a CURRENT checkpoint over the damaged head
        self.assertEqual(checkpoint.check_head(cp_a, self._live_head()), checkpoint.CURRENT)
        target_head = self._head_at(s_t)
        notes = []
        res = self._auto(cp_a, target_head, pair, segments=[], notify=notes.append)
        self._assert_halted_no_splice(res, ["chain"])
        self.assertTrue(res["triple_check"]["checkpoint"])
        self.assertTrue(res["triple_check"]["buddy"])
        # F3 (DIGEST-C4): a single-check HALT still FIRES the notify callback (the owner is told, :3082)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["outcome"], auto_recover.HALTED)

    def test_a2_verify_at_load_halts_the_autoproceed_restoring_nothing(self):
        # the triple check passes (it never inspects `segments`), so the auto path AUTOPROCEEDS into the
        # kernel op — but a segment is MISSING (a well-formed hash never stored), so verify-at-load HALTS
        # there (OpError). The orchestrator catches it: HALTED, no splice, restore nothing (the fourth
        # failure arm — any doubt halts). A corrupt BLOB would also fell the buddy check (it recomputes
        # the tree from the same blob), so an ABSENT extra segment isolates verify-at-load cleanly.
        h = self._write_file("/f", b"the recovered state depends on this content")
        s = self._head_seq()
        cp_a, _cp_b, pair = self._buddy_pair()
        absent = "sha256:" + hashlib.sha256(b"never stored locally").hexdigest()
        notes = []
        res = self._auto(cp_a, cp_a["provenance"]["chain_head"], pair, [h, absent], notify=notes.append)
        self.assertEqual(res["outcome"], auto_recover.HALTED)
        self.assertFalse(res["spliced"])
        self.assertTrue(res["triple_check"]["ok"])               # the THREE passed; verify-at-load did not
        self.assertIn("verify-at-load", res["reason"])
        self.assertEqual(notes[0]["outcome"], auto_recover.HALTED)  # the owner was notified
        # restoring nothing: no recover splice stands (a refusal is recorded, but no splice)
        self.assertIsNone(erasure.recovered_point(self.store.all()))


# ============================================================================================
# A3 — THE LAUNDERING-DOOR STAYS SHUT UNDER AUTO (RW2). A fabricated head is refused by the chain
#      check at BOTH layers — the bridge halts, and the kernel refuses even a well-formed auto call.
# ============================================================================================

class TestNeverToWrongnessAuto(AutoWorld):

    def test_a3_an_auto_recover_to_a_fabricated_head_halts_at_the_chain_check(self):
        self._write_file("/f", b"real content")
        s = self._head_seq()
        cp_a, _cp_b, pair = self._buddy_pair()
        fabricated = "sha256:" + "a" * 64                         # a head this chain NEVER held
        self.assertIsNone(erasure._seq_of_head(self.store, fabricated))
        n_before = len(self.store.all())
        res = self._auto(cp_a, fabricated, pair, self._gather_segments(s))
        self.assertEqual(res["outcome"], auto_recover.HALTED)
        self.assertFalse(res["triple_check"]["chain"])           # the chain check refuses the fabrication
        self.assertFalse(res["spliced"])
        self.assertEqual(len(self.store.all()), n_before)        # the record is UNCHANGED — restore nothing
        self.assertIsNone(erasure.recovered_point(self.store.all()))

    def test_a3_the_kernel_refuses_a_fabricated_head_even_under_an_all_pass_triple_check(self):
        # BELT-AND-BRACES: never-to-wrongness is UNCHANGED in the kernel and independent of the bridge.
        # Hand the recover op a fabricated target WITH an all-pass triple-check outcome (as if a buggy
        # or hostile orchestrator waved the three checks through) — the kernel's OWN chain check still
        # refuses at the anchor. The laundering-door is shut BELOW the bridge too.
        self._write_file("/f", b"real content")
        fabricated = "sha256:" + "b" * 64
        with self.assertRaises(OpError) as cm:
            self.gate.execute(erasure.RECOVER_OP, "SYSTEM",
                              {erasure.TARGET_HEAD: fabricated, erasure.CHECKPOINT_REF: "cp-ref",
                               erasure.RECOVER_RULE: RECOVER_RULE, "segments": [],
                               erasure.TRIGGER: erasure.TRIGGER_AUTO,
                               erasure.TRIPLE_CHECK: {"chain": True, "checkpoint": True, "buddy": True}})
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIn("never", str(cm.exception).lower())

    def test_a3_rw1_an_auto_splice_on_a_two_of_three_triple_check_is_refused_at_the_kernel(self):
        # RW1 kernel-side backstop: an AUTO recover carrying a triple check with the buddy FALSE (a
        # two-of-three) is refused by the kernel's auto-gate — nuclear-plant-grade is not a vote. Even a
        # lawful, sound target does not reach the splice under a partial triple check.
        self._write_file("/f", b"content")
        s = self._head_seq()
        sound_head = self._head_at(s)
        with self.assertRaises(OpError) as cm:
            self.gate.execute(erasure.RECOVER_OP, "SYSTEM",
                              {erasure.TARGET_HEAD: sound_head, erasure.CHECKPOINT_REF: "cp-ref",
                               erasure.RECOVER_RULE: RECOVER_RULE, "segments": self._gather_segments(s),
                               erasure.TRIGGER: erasure.TRIGGER_AUTO,
                               erasure.TRIPLE_CHECK: {"chain": True, "checkpoint": True, "buddy": False}})
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIn("all passing", str(cm.exception).lower())
        self.assertIsNone(erasure.recovered_point(self.store.all()))


# ============================================================================================
# A4 — THE MANUAL OWNER-GATED PATH IS UNCHANGED (RW4). The amend is ADDITIVE.
# ============================================================================================

class TestManualPathIntact(AutoWorld):

    def _manual_recover(self, target_head, segments):
        # a MANUAL recover — no trigger, driven by the owner, exactly as EP-43 built it.
        return self.gate.execute(erasure.RECOVER_OP, self.owner,
                                 {erasure.TARGET_HEAD: target_head, erasure.CHECKPOINT_REF: "cp-ref",
                                  erasure.RECOVER_RULE: RECOVER_RULE, "segments": list(segments)})

    def test_a4_the_manual_recover_still_works_and_its_row_carries_no_auto_keys(self):
        self._write_file("/f", b"content")
        s = self._head_seq()
        self._manual_recover(self._head_at(s), self._gather_segments(s))
        p = self.store.events[-1]["payload"]
        # the four EP-43 fields stand
        for field in (erasure.BREAK_AT, erasure.VERIFIED_THROUGH, erasure.CHECKPOINT_REF,
                      erasure.SEGMENTS_VERIFIED, erasure.OUTCOME):
            self.assertIn(field, p)
        self.assertEqual(p[erasure.OUTCOME], erasure.OUTCOME_VERIFIED_AT_LOAD)
        # ADDITIVE: the manual row carries NONE of the auto keys — byte-shape-identical to EP-43's
        self.assertNotIn(erasure.TRIGGER, p)
        self.assertNotIn(erasure.TRIPLE_CHECK, p)
        # the manual splice is the OWNER's act, not SYSTEM's
        self.assertEqual(self.store.events[-1]["actor"], self.owner)
        self.assertIsNotNone(erasure.recovered_point(self.store.all()))

    def test_a4_a_non_owner_manual_recover_is_still_refused_at_the_anchor(self):
        # the owner-gate is unchanged: a non-owner (and non-SYSTEM) manual recover is refused.
        self._write_file("/f", b"content")
        s = self._head_seq()
        with self.assertRaises(OpError) as cm:
            self.gate.execute(erasure.RECOVER_OP, "mallory",
                              {erasure.TARGET_HEAD: self._head_at(s), erasure.CHECKPOINT_REF: "cp-ref",
                               erasure.RECOVER_RULE: RECOVER_RULE, "segments": []})
        self.assertEqual(cm.exception.rule, erasure.RECOVER_ANCHOR)
        self.assertIn("root authority", str(cm.exception).lower())


# ============================================================================================
# A5 — AUTO NEVER TRUNCATES (RW3, the :3024 law under the auto trigger).
# ============================================================================================

class TestAutoNeverTruncates(AutoWorld):

    def test_a5_the_auto_splice_appends_one_row_and_never_shortens_the_file(self):
        self._write_file("/a", b"a")
        self._write_file("/b", b"b")
        s = self._head_seq()
        cp_a, _cp_b, pair = self._buddy_pair()
        seqs_before = [e["seq"] for e in self.store.all()]
        res = self._auto(cp_a, cp_a["provenance"]["chain_head"], pair, self._gather_segments(s))
        self.assertEqual(res["outcome"], auto_recover.AUTOPROCEEDED)
        seqs_after = [e["seq"] for e in self.store.all()]
        self.assertEqual(seqs_after[:len(seqs_before)], seqs_before)   # the whole prior file is intact
        self.assertEqual(len(seqs_after), len(seqs_before) + 1)        # exactly one row added: the splice

    def test_a5_the_kernel_carries_no_record_truncation_primitive(self):
        # capability-absence (the §8-j shape): the auto trigger adds no truncation path to erasure.
        with open(os.path.join(REPO, "src", "kernel", "erasure.py"), encoding="utf-8") as fh:
            src = fh.read()
        for forbidden in ("truncate", "self.store.events =", "events[:", "del self.store"):
            self.assertNotIn(forbidden, src)


# ============================================================================================
# A6 — THE AUTO-TRIGGER IS LIVE, FOUNDED AT BOOT, NOTHING NEW (RW6; EP-FND-RECOVER-AUTO-LIVE). The
#      recover op DECLARES the auto-trigger fields (code-registered, register_recover); production
#      founding-pack is byte-untouched; no new kind/check/bump. The held absence (EP-43-AUTO) inverted.
# ============================================================================================

def _recover_op_def(auto=False):
    """A recover-shaped op definition citing the recover LAW — a STAND-IN whose STRUCTURAL classification
    mirrors the live code-registered recover op. All fields are classified STRUCTURAL. The AUTO form adds
    the two auto-trigger fields (`trigger`, `triple_check`), OPTIONAL and STRUCTURAL, mirroring the live
    RECOVER_OP_META declaration (EP-FND-RECOVER-AUTO-LIVE). Used as the §A64 can-fail control: the base
    form carries NEITHER field, the auto form carries BOTH, so the presence test discriminates."""
    params = {"target_head": "required", "checkpoint_ref": "required", "recover_rule": "required"}
    structural = ["target_head", "checkpoint_ref", "recover_rule"]
    if auto:
        params[erasure.TRIGGER] = "optional"                      # the auto-trigger marker scalar ("auto")
        params[erasure.TRIPLE_CHECK] = "optional"                 # the three-check outcome dict
        structural = structural + [erasure.TRIGGER, erasure.TRIPLE_CHECK]
    return {"law_cited": erasure.RECOVER_LAW, "object_param": "target_head",
            "params": params, "checks": [], STRUCTURAL_PARAMS: structural}


class TestAutoTriggerLiveFoundedAtBoot(AutoWorld):

    def test_a6_the_auto_trigger_is_founded_at_boot_code_registered_no_new_kind(self):
        # RE-EXPRESSED from the AMEND-OP staging (EP-43-AUTO staged CREATE-base -> AMEND-to-auto in a test
        # world, proving the auto-trigger COULD ride the governed door while the flip was HELD) to the
        # FOUNDED-AT-BOOT reality (EP-FND-RECOVER-AUTO-LIVE made the flip live; the :3124 shape, as
        # EP-FND-OPEN-OP re-expressed its own op). The recover op is CODE-registered (register_recover,
        # compose.py:85), so "founded at boot" here is the code register path — NOT a founding-pack
        # op_definition (that would be a new founding kind + a bump, which this code-born unit does not take).
        # The two facts the staging proved — the auto-trigger is a lawful, admitted DECLARATION of the recover
        # op, and it needs nothing new — now hold against the boot-founded op directly, masking nothing.
        self.assertTrue(self.gate.has(erasure.RECOVER_OP))            # founded at boot, live in the gate
        live = self.gate.ops[erasure.RECOVER_OP]["meta"]
        for f in (erasure.TRIGGER, erasure.TRIPLE_CHECK):
            self.assertEqual(live["params"][f], "optional", f)        # DECLARED OPTIONAL (a manual call omits both)
            self.assertIn(f, live[STRUCTURAL_PARAMS], f)              # classified STRUCTURAL (safe inline)
        # NEEDS NOTHING NEW: no new founding kind rode in — the recover op is code-registered, so NO
        # CREATE-OP / AMEND-OP op_definition record names it (a governed amend would show one). Masks nothing:
        # a new founding KIND would surface here as such a record, and its absence is DRIVEN over the store.
        self.assertFalse(any(e.get("action") in ("CREATE-OP", "AMEND-OP")
                             and (e.get("payload") or {}).get("name") == erasure.RECOVER_OP
                             for e in self.store.all()))

    def test_a6_the_live_recover_op_carries_the_auto_trigger_production_pack_byte_untouched(self):
        # INVERTED (EP-FND-RECOVER-AUTO-LIVE; the held ABSENCE flipped to a present DECLARATION). EP-43-AUTO
        # proved the auto-trigger material ABSENT from the live recover op and HELD the pack byte-untouched;
        # the flip has now landed IN CODE (RECOVER_OP_META declares both fields), so the LIVE definition
        # CARRIES it while PRODUCTION FOUNDING (the pack) still declares no recover op_definition at all — the
        # recover op is code-registered, held out of the founding (NO bump). Proven at the DEFINITION level
        # (no version literal, no whole-pack sha — both move with any lawful founding bump; :3121/EP-SHAPE.md:870,
        # so neither could tell this flip apart from another bump). Two surfaces below, DRIVEN over parsed
        # records — a DIFFERENT surface than test_a6_rw6, which greps the raw pack TEXT.

        # (1) the LIVE recover-op definition, from a pack-exact FULL build (register_recover runs at full
        # compose), now CARRIES both auto-trigger fields in its params and its structural set.
        d = tempfile.mkdtemp(prefix="ep43auto-a6-")
        self.addCleanup(shutil.rmtree, d, True)
        _s, gate, _v, _b, _subs = build_full_kernel(os.path.join(d, "record.jsonl"),
                                                    os.path.join(d, "blobs"))
        live = gate.ops[erasure.RECOVER_OP]["meta"]
        for f in (erasure.TRIGGER, erasure.TRIPLE_CHECK):
            self.assertIn(f, live.get("params", {}), f)                          # the auto-trigger param, live
            self.assertIn(f, live.get(STRUCTURAL_PARAMS, []), f)                 # and classified STRUCTURAL
        # §A64 — the check CAN fail, driven both directions: a base recover-shaped def WITHOUT the auto-trigger
        # declaration carries NEITHER field, the auto form carries BOTH — so the presence test discriminates
        # (a live definition that had not gone live would flip the assertions above).
        base, auto = _recover_op_def(auto=False), _recover_op_def(auto=True)
        for f in (erasure.TRIGGER, erasure.TRIPLE_CHECK):
            self.assertNotIn(f, base["params"], f)
            self.assertNotIn(f, base[STRUCTURAL_PARAMS], f)
            self.assertIn(f, auto["params"], f)
            self.assertIn(f, auto[STRUCTURAL_PARAMS], f)

        # (2) the production pack declares NO recover op_definition at all (the recover op is
        # code-registered and HELD out of the founding — byte-untouched, no bump), so neither the op nor a
        # `triple_check` param rode into any op_definition record — DRIVEN over the parsed records, not a grep.
        with open(PACK_PATH, encoding="utf-8") as fh:
            pack = json.load(fh)
        packops = {r["payload"]["name"]: r["payload"]["definition"]
                   for s in pack["steps"] for r in s["records"]
                   if r.get("action") == "CREATE-OP" and (r.get("payload") or {}).get("kind") == "op_definition"}
        self.assertNotIn(erasure.RECOVER_OP, packops)                            # RECOVER-TO-CHECKPOINT: 0 hits in the pack
        with_auto = [n for n, dfn in packops.items()
                     if erasure.TRIPLE_CHECK in (dfn.get("params") or {})
                     or erasure.TRIPLE_CHECK in (dfn.get(STRUCTURAL_PARAMS) or [])]
        self.assertEqual(with_auto, [])                                          # triple_check: 0 hits in the pack, driven

    def test_a6_rw6_production_carries_no_auto_trigger_token_the_check_can_fail(self):
        # §A64 — a check that can fail. Production's recover LAW carries the manual wording ONLY; the
        # auto-trigger tokens are ABSENT (the flip is HELD). Plant one into a COPY and the assertion
        # would red, while production stays byte-untouched.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        for token in ("autoproceed", "auto-recover", "triple check", "triple_check"):
            self.assertNotIn(token, real, token)                  # no auto-trigger clause in production
        planted = real.replace("RECOVER-LAW-GS14",
                               "RECOVER-LAW-GS14 (auto-recover under a triple check)")
        self.assertIn("auto-recover", planted)                    # the guard is real — a plant would flip it

    def test_a6_no_new_check_kind_the_triple_composes_three_existing_checks(self):
        # RW6 / stop (e): the auto path mints NO new check kind — it COMPOSES three checks that ALREADY
        # exist. Each is a pre-existing callable in the estate, not a new founding vocabulary member.
        self.assertTrue(callable(erasure._seq_of_head))           # (1) chain (the kernel op's own)
        self.assertTrue(callable(self.store.verify_chain))        #     the chain fold
        self.assertTrue(callable(checkpoint.check_head))          # (2) checkpoint hash rematch (EP-44)
        self.assertTrue(callable(checkpoint.pairing_verdict))     # (3) buddy mutual receipt (EP-45)
        # and the orchestrator's triple_check returns exactly these three, no fourth
        self._write_file("/f", b"content")
        s = self._head_seq()
        cp_a, _cp_b, pair = self._buddy_pair()
        tc = auto_recover.triple_check(self.store, cp_a, cp_a["provenance"]["chain_head"], pair)
        self.assertEqual(set(tc) - {"ok", "failed"}, {"chain", "checkpoint", "buddy"})


# ============================================================================================
# A7 — LAYERING HOLDS (RW5). The orchestrator is BRIDGE; the kernel imports no bridge; the target
#      head is a kernel param.
# ============================================================================================

class TestLayering(unittest.TestCase):

    def test_a7_the_orchestrator_is_bridge_and_composes_kernel_plus_bridge(self):
        with open(os.path.join(REPO, "src", "bridge", "auto_recover.py"), encoding="utf-8") as fh:
            src = fh.read()
        imports = "\n".join(ln for ln in src.splitlines()
                            if ln.strip().startswith(("import ", "from ")))
        self.assertIn("from kernel import erasure", imports)      # composes the kernel recover op
        self.assertIn("from bridge import checkpoint", imports)   # composes the bridge checks (check_head + pairing)

    def test_a7_the_kernel_recover_module_imports_no_bridge(self):
        # RW5: the auto composition placed in the kernel would invert layering. The kernel op takes the
        # target head as a caller-supplied PARAM and the triple-check outcome as DATA — it imports no
        # bridge checkpoint / buddy / orchestrator.
        with open(os.path.join(REPO, "src", "kernel", "erasure.py"), encoding="utf-8") as fh:
            src = fh.read()
        imports = "\n".join(ln for ln in src.splitlines()
                            if ln.strip().startswith(("import ", "from ")))
        for forbidden in ("bridge", "checkpoint", "merkle", "auto_recover"):
            self.assertNotIn(forbidden, imports, forbidden)

    def test_a7_the_kernel_receives_the_triple_check_outcome_as_data_not_a_bridge_import(self):
        # the erasure handler names the triple-check fields as DATA constants and reads them from
        # params — it never imports a bridge module to recompute the checkpoint or buddy.
        self.assertTrue(hasattr(erasure, "TRIGGER") and hasattr(erasure, "TRIPLE_CHECK"))
        self.assertEqual(erasure.TRIGGER_AUTO, "auto")


if __name__ == "__main__":
    unittest.main()
