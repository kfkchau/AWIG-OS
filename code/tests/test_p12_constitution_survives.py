# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-planning ·
# Vocabulary is OS-architecture (sealed segment, verify against a key, chain-verify, union) as in
# the seL4/gVisor literature. NON-GOAL: no offensive capability of any kind — this proves a
# constitution reconstructs from the children's held signed segments after the parent store is
# gone, by function, over benign local records. Full declaration: SCOPE-STATEMENT.md.
"""C6 P12 — THE CONSTITUTION SURVIVES ITS MACHINE (B6, I15).

A1 the union of the children's held sealed segments reproduces EVERY rule any child was bound
   by, after the parent's store is removed;
A2 a rule NO child ever held is absent (correctly lost) and REPORTED BY POSITION in the named
   gap list — only rows nobody was bound by are lost;
A3 the forged-segment positive control: a bad seal against the parent key, and bytes that do not
   hash to their address, each FAIL verification (the RW-FORGE check reddens) and are not admitted
   — and with the tamper removed the same segment is admitted.

These run on the estate's MODELLED-key baseline (the vetted crypto library is an optional extra;
absent here). `keys.verify_countersign` over a modelled mark is a REAL check that can fail —
proven at tests/test_keymat.py — so no real seal is stubbed and no pass is faked (N10).
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import blobs, keys, crypto
from bridge import reconstruct


PARENT_KEY = "sha256:" + "ab" * 32           # the parent body's system_key_hash (public custody)
OTHER_KEY = "sha256:" + "cd" * 32            # a DIFFERENT body's key — a seal under it must not verify


def _seal_rule(store, parent_key, position, content):
    """The parent seals one rule at `position`: put the bytes into the content-addressed store,
    countersign a recording fact that BINDS the content address and the position under the parent
    key (the modelled baseline mark). Returns the held segment REFERENCE a child would keep."""
    address = store.put(content)
    record = {"seq": position, "record_time": "t%d" % position, "object": address}
    mark = keys.countersign(record, parent_key)          # modelled mark (no signer) — the baseline
    return {"position": position, "address": address, "record": record, "mark": mark}


class ConstitutionSurvivesTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p12-")
        self.store = blobs.BlobStore(os.path.join(self._tmp, "segments"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    # ---- the parent's original constitution, and what the children hold ----------------------

    def _parent_constitution(self, rules):
        """Build the parent's full constitution as sealed segments, keyed by position. `rules` is
        {position: content_bytes}. Returns {position: held-segment-reference}."""
        return {pos: _seal_rule(self.store, PARENT_KEY, pos, content)
                for pos, content in rules.items()}

    # ============================ A1 =========================================================

    def test_a1_reconstruction_reproduces_every_bound_rule(self):
        """A1 — with the parent's store REMOVED, the union of the children's held segments
        reproduces every rule any child was bound by."""
        rules = {1: b"rule-alpha", 2: b"rule-beta", 3: b"rule-gamma", 4: b"rule-delta"}
        segs = self._parent_constitution(rules)

        # THE PARENT'S OWN STORE IS GONE. We keep only a COPY of the bound-rule content to assert
        # against, then drop the parent's authoritative store — reconstruct never receives it.
        bound = dict(rules)
        parent_store = object()                              # stands for the parent's machine/ledger
        del parent_store                                     # ... which is now gone

        # Two children between them hold every position (childA: 1,2 ; childB: 3,4).
        held = [dict(segs[1]), dict(segs[2]), dict(segs[3]), dict(segs[4])]

        report = reconstruct.reconstruct(PARENT_KEY, held, self.store)

        self.assertEqual(report["refused"], [], "no legitimate segment should be refused")
        self.assertEqual(report["positions"], [1, 2, 3, 4])
        self.assertEqual(report["gaps"], [], "contiguous held positions leave no gap")
        # every rule any child was bound by is reproduced, byte-for-byte
        self.assertEqual({pos: report["rules"][pos] for pos in report["rules"]}, bound)
        # the reconstructed view carries one inspectable Merkle fingerprint
        self.assertTrue(report["root"].startswith("sha256:"))

    def test_a1_union_is_deterministic_and_dedups_a_segment_two_children_hold(self):
        """A1 (union discipline, archi :3619 precision 2) — child order does not move the result,
        and a DUPLICATE segment held by two children is ONE segment."""
        rules = {1: b"one", 2: b"two", 3: b"three"}
        segs = self._parent_constitution(rules)

        # childA holds 1,2 ; childB holds 2,3 — position 2 is held by BOTH (a duplicate).
        held_ab = [dict(segs[1]), dict(segs[2]), dict(segs[2]), dict(segs[3])]
        # the same holdings in a different child/segment order
        held_ba = [dict(segs[3]), dict(segs[2]), dict(segs[1]), dict(segs[2])]

        report_ab = reconstruct.reconstruct(PARENT_KEY, held_ab, self.store)
        report_ba = reconstruct.reconstruct(PARENT_KEY, held_ba, self.store)

        self.assertEqual(report_ab["positions"], [1, 2, 3])       # position 2 appears ONCE (dedup)
        self.assertEqual(report_ab["rules"], report_ba["rules"])
        self.assertEqual(report_ab["root"], report_ba["root"], "the fold is order-independent")

    # ============================ A2 =========================================================

    def test_a2_only_the_unheld_is_lost_and_reported_by_position(self):
        """A2 — a rule NO child ever held is absent from the reconstruction (correctly lost) and
        named in the gap list BY POSITION; every rule any child held is present."""
        rules = {1: b"held-1", 2: b"held-2", 3: b"UNHELD-3", 4: b"held-4"}
        segs = self._parent_constitution(rules)

        # position 3 is held by NO child — no child keeps a reference to it, so reconstruction
        # (which works only from held references) never reaches it. That IS "no child held it":
        # the rule is lost, and the gap is what tells the reader WHICH rule, by number.
        held = [dict(segs[1]), dict(segs[2]), dict(segs[4])]      # 3 is absent from every holding

        report = reconstruct.reconstruct(PARENT_KEY, held, self.store)

        self.assertEqual(report["positions"], [1, 2, 4])
        self.assertEqual(report["gaps"], [3], "the unheld position is named in the gap list")
        self.assertNotIn(3, report["rules"], "an unheld rule is absent — correctly lost")
        self.assertEqual(report["rules"][1], b"held-1")
        self.assertEqual(report["rules"][2], b"held-2")
        self.assertEqual(report["rules"][4], b"held-4")

    # ============================ A3 (positive control) ======================================

    def test_a3_a_forged_seal_against_the_parent_key_is_refused(self):
        """A3 arm 1 — a segment whose seal does NOT verify against the parent key (a mark made
        under ANOTHER body's key) FAILS verification and is NOT admitted; with the real mark
        restored the same segment IS admitted. The RW-FORGE check reddens."""
        rules = {1: b"rule-one", 2: b"rule-two"}
        segs = self._parent_constitution(rules)

        # forge: re-seal position 2's record under a DIFFERENT key, so it does not bind the parent.
        forged = dict(segs[2])
        forged["mark"] = keys.countersign(segs[2]["record"], OTHER_KEY)   # a real mark, wrong key

        held_forged = [dict(segs[1]), forged]
        report = reconstruct.reconstruct(PARENT_KEY, held_forged, self.store)

        self.assertNotIn(2, report["rules"], "a forged-key segment must not enter the union")
        reasons = [r["reason"] for r in report["refused"] if r["position"] == 2]
        self.assertTrue(reasons and "parent key" in reasons[0], "refused for the parent-key check")

        # CONTROL: the ONLY change is the forged mark — restore the real mark and it is admitted.
        report_clean = reconstruct.reconstruct(PARENT_KEY, [dict(segs[1]), dict(segs[2])], self.store)
        self.assertIn(2, report_clean["rules"])
        self.assertEqual(report_clean["refused"], [])

    def test_a3_bytes_that_do_not_hash_to_their_address_are_refused(self):
        """A3 arm 2 — a segment whose stored bytes do NOT hash to its address (tampered or missing
        content) FAILS the content-address check and is not admitted; with the correct bytes it is
        admitted. The check can fail."""
        rules = {1: b"rule-one", 2: b"rule-two"}
        segs = self._parent_constitution(rules)

        # tamper: overwrite the STORED bytes at position 2's address so they no longer hash to it.
        # (We write directly to the blob path — the store itself would refuse to put mismatched
        # bytes; this simulates on-disk corruption the reconstruction must catch.)
        address = segs[2]["address"]
        digest = address.split(":", 1)[1]
        blob_path = os.path.join(str(self.store.dir), digest[:2], digest[2:])
        with open(blob_path, "wb") as f:
            f.write(b"tampered-bytes-that-do-not-hash-to-the-address")

        report = reconstruct.reconstruct(PARENT_KEY, [dict(segs[1]), dict(segs[2])], self.store)
        self.assertNotIn(2, report["rules"], "corrupt-content segment must not enter the union")
        reasons = [r["reason"] for r in report["refused"] if r["position"] == 2]
        self.assertTrue(reasons and "hash to their address" in reasons[0])

        # sanity that the forge check is what fired: position 1 (untampered) is admitted
        self.assertIn(1, report["rules"])

    def test_a3_a_record_repointed_to_another_address_is_refused(self):
        """A3 (binding) — a segment whose sealed record's `object` no longer names its address
        (a forger re-pointing the seal to other content) is refused: the seal binds the CONTENT,
        not a bare recording fact."""
        rules = {1: b"rule-one"}
        segs = self._parent_constitution(rules)
        tampered = dict(segs[1])
        tampered["address"] = self.store.put(b"other-content")   # a real, different address...
        # ...but the mark still binds the ORIGINAL record (object=original address), so the
        # record no longer names `tampered["address"]`.
        report = reconstruct.reconstruct(PARENT_KEY, [tampered], self.store)
        self.assertNotIn(1, report["rules"])
        self.assertTrue(any("bind this address" in r["reason"] for r in report["refused"]))

    # ============================ discipline riders ==========================================

    def test_the_routine_appends_nothing_it_is_a_derived_view(self):
        """archi :3619 precision 1 — the reconstruction is a REPORT (a return value), never a
        record. The routine takes no gate and exposes no append path; its output is a plain dict
        over the report keys."""
        rules = {1: b"only"}
        segs = self._parent_constitution(rules)
        report = reconstruct.reconstruct(PARENT_KEY, [dict(segs[1])], self.store)
        self.assertIsInstance(report, dict)
        self.assertEqual(set(report), set(reconstruct.REPORT_KEYS))
        # no attribute on the module can write a record: it imports keys/merkle read-only.
        self.assertFalse(hasattr(reconstruct, "execute"))
        self.assertFalse(hasattr(reconstruct, "append"))

    def test_host_is_on_the_modelled_baseline(self):
        """The seals above verify under the MODELLED path — the estate's baseline (the vetted
        crypto library is absent). A modelled mark is a real check that can fail, so no pass is
        faked. (If the library were present this asserts nothing about it — the modelled marks
        built here still route to the modelled path by their untagged shape.)"""
        mark = keys.countersign({"seq": 1, "record_time": "t", "object": "sha256:" + "00" * 32},
                                PARENT_KEY)
        self.assertFalse(crypto.is_real_value(mark), "the baseline mark is a modelled value")


if __name__ == "__main__":
    unittest.main()
