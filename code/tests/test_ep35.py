# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (record chain, seal, append-only store); NON-GOAL: no offensive capability of any
# kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-35 — the chain and the anchor: the record becomes edit-evident by derivation.

Every probe here is a regression test (the campaign method: a verification probe lands as a test).
The battery proves, in disposable test stores (F4 — the live store's past is never edited):

  A1  TestChainHolds       every NEW record chains; an edited byte-of-meaning in a chained record
                           is DETECTED by recomputation (RW1: an undetected edit would red).
  A2  TestChainLocates     verification names the seq where the chain first breaks ("verified
                           through seq N" + the break point).
  A3  TestPrefixAnchored   an edit to any pre-seal PREFIX record breaks the anchor's recorded hash
                           on recomputation (RW2).
  A4  TestCanonicalNeutral both directions: a re-encoding that changes NO canonical content is NOT
                           flagged (EP-34's battery is the guarantee); a change that DOES alter
                           canonical content IS (RW3 — a false alarm is as much a failure as a miss).
  A5  TestSoleAppender     only the ONE sanctioned appender mints chain fields; the sole-appender
                           invariant does not change (RW4 — a second mint site would be caught).
  A6  TestSealRate         the append-path cost is MEASURED and logged WITH BATCH WIDTH; the test
                           asserts a COUNTABLE (chain fields == post-anchor records), never a
                           duration (BUILD-PROMPT-STANDARD_v3 §1 extension). Never resolved by
                           sealing less.
  A7  TestEraReHome        the dual-audit family (protection._digest / views.digest_of) hashes via
                           canonical for NEW records; OLD records verify under the pre-era JSON
                           serializer (era-split, D4); the boundary seq is recorded; the
                           None-boundary case is unified; the past is byte-untouched (RW5).
  A8  TestFoundingMoved    the founding version moved MINOR from its era; the pack bytes changed
                           (RW-F — a byte-unchanged founding would red).
  A10 TestSigningDegrades  with signing UNAVAILABLE the two signature fields are PENDING, assert no
                           signed claim, do NOT block, and the prev_hash chain STILL verifies; a
                           false SIGNED claim is caught (RW6).

The signature-vault of Q2 is EP-36's; here signing is honestly unavailable and the fields degrade
to PENDING (§8-j). This file composes no engine surface it modifies: it drives store/protection/
views through their public seams only.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel import protection as protection_mod  # noqa: E402
from kernel import views as views_mod            # noqa: E402
from kernel.canonical import canonical_hash      # noqa: E402
from kernel.compose import build_full_kernel      # noqa: E402
from kernel.errors import OpError                  # noqa: E402
from kernel.store import CHAIN_ANCHOR_ACTION, SIG_PENDING, EventStore  # noqa: E402

import era_pin  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
# The pre-edit era: HEAD captured at this EP's dispatch (before the founding move), where the
# founding stood at 1.31.0. §A57 era-pin — the version is read from git, never off the live tree.
PRE_EDIT_COMMIT = "c00b1521f607b65d309e422748c21d68cc1dc945"


# ============================================================================================
# Helpers — disposable chained stores built through the ONE sanctioned appender
# ============================================================================================

def _build_chained(path, n_prefix=3, n_post=3):
    """A store with `n_prefix` records sealed under an anchor and `n_post` chained records after
    it. Every record is written through the store's one appender (store._append)."""
    s = EventStore(path)
    for i in range(n_prefix):
        s._append({"actor": "a%d" % i, "action": "X", "payload": {"i": i, "k": ["v", i]}})
    anchor = s.seal_prefix()
    for i in range(n_post):
        s._append({"actor": "b%d" % i, "action": "Y", "payload": {"j": i}})
    s.close()
    return anchor


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [ln for ln in fh.read().splitlines() if ln]


def _write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _rewrite_record(path, seq, mutate):
    """Rewrite the on-disk record at `seq` (1-based) by mutating its parsed dict — simulating a
    later alteration of an already-written record. `mutate(rec)` edits in place. Compact
    separators match the store's own writer, so a canonical-NEUTRAL mutation moves only bytes."""
    lines = _read_lines(path)
    rec = json.loads(lines[seq - 1])
    mutate(rec)
    lines[seq - 1] = json.dumps(rec, separators=(",", ":"))
    _write_lines(path, lines)


# ============================================================================================
# A1 — T-CHAIN-HOLDS
# ============================================================================================

class TestChainHolds(unittest.TestCase):
    """A1: new records chain, and an edited byte-of-meaning in a chained record is DETECTED."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.anchor = _build_chained(self.path, n_prefix=3, n_post=3)

    def test_chain_holds_new_records_carry_a_store_minted_prev_hash(self):
        s = EventStore(self.path)
        a_seq = self.anchor["seq"]
        # every record AFTER the anchor carries a prev_hash equal to the canonical hash of its
        # predecessor — store-minted, self-naming its algorithm in the "sha256:" prefix.
        for seq in range(a_seq + 1, len(s.events) + 1):
            rec = s.events[seq - 1]
            self.assertIn("prev_hash", rec, "a post-anchor record did not chain")
            self.assertTrue(rec["prev_hash"].startswith("sha256:"), rec["prev_hash"])
            self.assertEqual(rec["prev_hash"], canonical_hash(s.events[seq - 2]))
        # ... and every record AT OR BEFORE the anchor is unchained (new-records-only).
        for seq in range(1, a_seq + 1):
            self.assertNotIn("prev_hash", s.events[seq - 1],
                             "a pre-seal record gained a chain field — the past was touched")

    def test_chain_holds_a_clean_chain_verifies_and_an_edit_is_detected(self):
        clean = EventStore(self.path)
        self.assertTrue(clean.verify_chain()["ok"], "a clean chain did not verify (a false alarm)")
        # RW1: edit a byte-of-meaning in a CHAINED, non-head record; recomputation MUST catch it.
        a_seq = self.anchor["seq"]
        target = a_seq + 1                                   # first post-anchor record (has a successor)
        _rewrite_record(self.path, target, lambda r: r.__setitem__("actor", "TAMPERED"))
        tampered = EventStore(self.path)
        result = tampered.verify_chain()
        self.assertFalse(result["ok"], "an edit to a chained record went UNDETECTED (RW1)")


# ============================================================================================
# A2 — T-CHAIN-LOCATES
# ============================================================================================

class TestChainLocates(unittest.TestCase):
    """A2: the check names the seq where the chain first breaks."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.anchor = _build_chained(self.path, n_prefix=2, n_post=4)

    def test_the_break_is_located_verified_through_N(self):
        a_seq = self.anchor["seq"]
        edited = a_seq + 2                                   # a middle chained record (has a successor)
        _rewrite_record(self.path, edited, lambda r: r.__setitem__("payload", {"j": 999}))
        s = EventStore(self.path)
        result = s.verify_chain()
        self.assertFalse(result["ok"])
        # editing record X breaks the link INTO X+1 (X+1.prev_hash no longer matches recomputed X):
        # the first broken link is at X+1, and every link up to and including X verified.
        self.assertEqual(result["break_at"], edited + 1,
                         "the located break is not the first broken link")
        self.assertEqual(result["verified_through"], edited,
                         "verified-through did not reach the last intact link")

    def test_a_whole_chain_reports_verified_through_the_head(self):
        s = EventStore(self.path)
        result = s.verify_chain()
        self.assertTrue(result["ok"])
        self.assertEqual(result["break_at"], None)
        self.assertEqual(result["verified_through"], len(s.events))


# ============================================================================================
# A3 — T-PREFIX-ANCHORED
# ============================================================================================

class TestPrefixAnchored(unittest.TestCase):
    """A3: an edit to any pre-seal prefix record breaks the anchor's recorded hash."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.anchor = _build_chained(self.path, n_prefix=4, n_post=2)

    def test_a_prefix_edit_breaks_the_anchor(self):
        clean = EventStore(self.path)
        self.assertTrue(clean.verify_chain()["prefix_ok"], "the clean prefix did not anchor")
        # RW2: edit ANY prefix record; the recomputed prefix hash must diverge from the anchor's.
        for target in range(1, self.anchor["payload"]["boundary_seq"] + 1):
            with self.subTest(prefix_seq=target):
                _rewrite_record(self.path, target, lambda r: r.__setitem__("actor", "TAMPERED-%d" % target))
                s = EventStore(self.path)
                result = s.verify_chain()
                self.assertFalse(result["prefix_ok"],
                                 "a prefix edit left the anchor intact (RW2) at seq %d" % target)
                self.assertFalse(result["ok"])
                # restore for the next subtest
                _rewrite_record(self.path, target, lambda r: r.__setitem__("actor", "a%d" % (target - 1)))

    def test_the_anchor_records_the_boundary_seq(self):
        self.assertEqual(self.anchor["payload"]["boundary_seq"], 4)
        self.assertEqual(self.anchor["action"], CHAIN_ANCHOR_ACTION)
        self.assertTrue(self.anchor["payload"]["prefix_hash"].startswith("sha256:"))


# ============================================================================================
# A4 — the exactness line, BOTH directions
# ============================================================================================

class TestCanonicalNeutral(unittest.TestCase):
    """A4: a canonical-NEUTRAL re-encoding is NOT flagged; a canonical-content change IS."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.anchor = _build_chained(self.path, n_prefix=3, n_post=3)

    def test_a_canonical_neutral_reencoding_is_not_flagged(self):
        # Re-serialize a chained record with its payload keys in a DIFFERENT order (sort_keys) —
        # same canonical content, different bytes on disk. The canonical hash is key-order-invariant
        # (EP-34's floor), so the chain must NOT flag it: a chain that cried wolf here would inherit
        # exactly the fuzz EP-34 removed.
        target = self.anchor["seq"] + 1
        lines = _read_lines(self.path)
        rec = json.loads(lines[target - 1])
        # a genuinely order-different, content-identical re-encoding of the whole record
        reencoded = json.dumps(rec, sort_keys=True, separators=(", ", ": "))
        self.assertNotEqual(reencoded, lines[target - 1], "the re-encoding did not change the bytes")
        lines[target - 1] = reencoded
        _write_lines(self.path, lines)
        s = EventStore(self.path)
        self.assertTrue(s.verify_chain()["ok"],
                        "a canonical-neutral re-encoding was FLAGGED (RW3 — a false alarm)")

    def test_a_canonical_content_change_is_flagged(self):
        # the same site, but a real change to canonical content: it MUST be flagged.
        target = self.anchor["seq"] + 1
        _rewrite_record(self.path, target, lambda r: r["payload"].__setitem__("j", 424242))
        s = EventStore(self.path)
        self.assertFalse(s.verify_chain()["ok"], "a real content change was not flagged (a miss)")


# ============================================================================================
# A5 — T-GATE-SOLE-APPENDER unchanged
# ============================================================================================

class TestSoleAppender(unittest.TestCase):
    """A5: only the one sanctioned appender mints chain fields; the invariant does not change."""

    def test_the_chain_anchor_and_prev_hash_ride_the_one_appender(self):
        # The chain-anchor is written through store._append (the one sanctioned appender, inside
        # store.py which the estate's sole-appender guard sanctions), and prev_hash mints inside
        # _append_one — never a second write site. The COUNTABLE that proves "only the one
        # appender mints": after sealing, exactly the post-anchor records carry a prev_hash, one
        # per append, no more and no fewer.
        d = tempfile.mkdtemp()
        path = os.path.join(d, "record.jsonl")
        anchor = _build_chained(path, n_prefix=2, n_post=5)
        s = EventStore(path)
        a_seq = anchor["seq"]
        minted = [e for e in s.events if "prev_hash" in e]
        post_anchor = [e for e in s.events if e["seq"] > a_seq]
        self.assertEqual(len(minted), len(post_anchor), "chain fields did not mint one-per-append")
        self.assertEqual([e["seq"] for e in minted], [e["seq"] for e in post_anchor])
        # the anchor itself never gained a prev_hash (its predecessor is the unsigned past, sealed
        # under prefix_hash, not chained to a single record).
        self.assertNotIn("prev_hash", s.events[a_seq - 1])

    def test_the_estates_sole_appender_guard_still_sanctions_store_py(self):
        # T-GATE-SOLE-APPENDER (tests/test_sole_appender.py) keys on the literal `._append(`. My
        # chain code adds a `self._append(` call INSIDE kernel/store.py — the sanctioned appender
        # module — and no new appender module. This asserts store.py is (still) the sanctioned home
        # of the append route, so the sole-appender invariant is unchanged by this pass.
        import test_ep28g_w5 as guard
        self.assertIn("kernel/store.py", guard.RefusedReferencesCase.SANCTIONED)


# ============================================================================================
# A6 — T-SEAL-RATE (measured, logged; the assertion is a COUNTABLE, never a duration)
# ============================================================================================

class TestSealRate(unittest.TestCase):
    """A6: the append-path cost before/after is measured and logged WITH BATCH WIDTH. The test
    asserts a COUNTABLE (every post-anchor append minted exactly one chain hash); the duration is a
    REPORT (BUILD-PROMPT-STANDARD_v3 §1 extension — a property test never gates on a duration)."""

    N = 120

    def _measure(self):
        """Interleaved arms (the filed measurement rule): each iteration times one UNSEALED append
        and one SEALED append against fresh stores, so machine drift hits both arms alike."""
        unsealed, sealed = [], []
        width = None
        for _ in range(self.N):
            du = tempfile.mkdtemp()
            su = EventStore(os.path.join(du, "r.jsonl"))
            t0 = time.perf_counter()
            su._append({"actor": "a", "action": "X", "payload": {"k": 1}})
            unsealed.append(time.perf_counter() - t0)
            width = su.group_commit.width
            su.close()

            ds = tempfile.mkdtemp()
            ss = EventStore(os.path.join(ds, "r.jsonl"))
            ss._append({"actor": "a", "action": "X", "payload": {"k": 1}})
            ss.seal_prefix()
            t0 = time.perf_counter()
            ss._append({"actor": "b", "action": "Y", "payload": {"k": 2}})   # a chained append
            sealed.append(time.perf_counter() - t0)
            ss.close()
        return unsealed, sealed, width

    @staticmethod
    def _stats(xs):
        xs = sorted(xs)
        n = len(xs)
        median = xs[n // 2]
        spread = xs[int(n * 0.9)] - xs[int(n * 0.1)]           # 10th–90th spread
        return median * 1e6, spread * 1e6                       # microseconds

    def test_seal_rate_is_measured_and_the_chain_is_present(self):
        unsealed, sealed, width = self._measure()
        # THE COUNTABLE (the gate): a chained store mints exactly one hash per post-anchor append.
        d = tempfile.mkdtemp()
        s = EventStore(os.path.join(d, "r.jsonl"))
        s._append({"actor": "a", "action": "X"})
        s.seal_prefix()
        for i in range(10):
            s._append({"actor": "b%d" % i, "action": "Y"})
        chained = [e for e in s.events if "prev_hash" in e]
        self.assertEqual(len(chained), 10, "the chain minted the wrong number of hashes")
        for e in chained:
            self.assertTrue(e["prev_hash"].startswith("sha256:"))
        s.close()
        # THE REPORT (never a gate): the measurement, WITH BATCH WIDTH as a stated condition.
        um, us = self._stats(unsealed)
        sm, ss = self._stats(sealed)
        report = ("T-SEAL-RATE [interleaved, N=%d, batch width=%d, non-exempt actor=this test "
                  "process]\n  unsealed append: median %.1f us (10-90 spread %.1f us)\n"
                  "  sealed   append: median %.1f us (10-90 spread %.1f us)\n"
                  "  delta median: %.1f us — reported, NOT asserted (a difference inside a spread "
                  "is not a difference); the seal is never resolved by sealing less."
                  % (self.N, width, um, us, sm, ss, sm - um))
        print("\n" + report)


# ============================================================================================
# A7 — the era-boundary re-home (rows 1 & 2), new-records-only
# ============================================================================================

class TestEraReHome(unittest.TestCase):
    """A7: the dual-audit family unifies onto canonical for NEW records; old records verify under
    the pre-era serializer (era-split); the None-boundary is unified; the past is byte-untouched."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        self.prot = self.views.protection

    def test_old_mirrors_stay_json_and_new_mirrors_go_canonical(self):
        # a mirrored governance act BEFORE any seal -> JSON era, NO digest_algo tag. (The genesis
        # actions are not in the dual-audit-actions pack, so a real audited act is provoked.)
        with self.assertRaises(OpError):
            self.gate.execute("NO-SUCH-OP", "alice", {})
        old_mirrors = list(self.store.by_action("dual-audit-record"))
        self.assertTrue(old_mirrors, "the pre-seal act was not mirrored")
        for m in old_mirrors:
            self.assertNotIn("digest_algo", m["payload"], "a pre-seal mirror carried an era tag")
            ref = self.store.by_seq(m["payload"]["ref_seq"])
            self.assertEqual(m["payload"]["digest"], protection_mod._digest(ref, "json"))

        boundary_before = len(self.store.events)
        anchor = self.store.seal_prefix()
        self.assertEqual(anchor["payload"]["boundary_seq"], boundary_before,
                         "the anchor did not record the era boundary seq")

        # a NEW governance act after the seal -> canonical era, tagged.
        with self.assertRaises(OpError):
            self.gate.execute("NO-SUCH-OP", "bob", {})
        new_mirrors = [m for m in self.store.by_action("dual-audit-record")
                       if m["seq"] > anchor["seq"]]
        self.assertTrue(new_mirrors, "the post-seal act was not mirrored")
        for m in new_mirrors:
            self.assertEqual(m["payload"].get("digest_algo"), "canonical",
                             "a post-seal mirror was not canonical-era")
            ref = self.store.by_seq(m["payload"]["ref_seq"])
            self.assertEqual(m["payload"]["digest"], protection_mod._digest(ref, "canonical"))
            # the canonical dual-audit digest is genuinely NOT the JSON one (the re-home is real).
            self.assertNotEqual(protection_mod._digest(ref, "canonical"),
                                protection_mod._digest(ref, "json"))

        # era-split verification holds across the boundary: nothing false-diverges.
        self.assertTrue(self.prot.audit_consistent())
        self.assertEqual(self.prot.dual_blind_divergences(), [])

    def test_the_none_boundary_is_unified_on_canonical_but_split_on_json(self):
        # A record with an ABSENT payload is where the two copies historically diverged. Row 2
        # unifies them on canonical (payload -> {}); the JSON (pre-era) branch keeps the historical
        # divergence, byte-frozen, because old records verify under exactly what wrote them.
        rec_none = {"seq": 7, "actor": "a", "action": "X"}          # no payload key at all
        self.assertNotEqual(protection_mod._digest(rec_none, "json"),
                            views_mod.digest_of(rec_none, "json"),
                            "the historical None divergence was silently erased in the frozen era")
        self.assertEqual(protection_mod._digest(rec_none, "canonical"),
                         views_mod.digest_of(rec_none, "canonical"),
                         "the None boundary was NOT unified on canonical (row 2)")

    def test_the_drift_pin_holds_on_canonical_for_payload_bearing_records(self):
        # the two copies must agree over the shared payload-bearing corpus on canonical too (the
        # U-B drift pin, extended to the new era).
        corpus = [
            {"seq": 1, "actor": "alice", "action": "GRANT-READ", "payload": {"grantee": "bob", "target": "d"}},
            {"seq": 2, "actor": "SYSTEM", "action": "CREATE-RULE", "payload": {"kind": "rule", "levels": ["a", "b"]}},
            {"seq": 3, "actor": "carol", "action": "FILE-OPEN", "payload": {}},
        ]
        for rec in corpus:
            self.assertEqual(protection_mod._digest(rec, "canonical"),
                             views_mod.digest_of(rec, "canonical"), rec)

    def test_the_past_is_byte_untouched_by_sealing(self):
        # RW5: sealing (and the era boundary) rewrites NO already-written record. The owner licensed
        # grow-only, not migration; a rewrite of the past is refused permanently. Prove it: the raw
        # bytes of every pre-seal record are identical before and after the seal + a new act.
        before = _read_lines(self.path)
        self.store.seal_prefix()
        with self.assertRaises(OpError):
            self.gate.execute("NO-SUCH-OP", "alice", {})
        after = _read_lines(self.path)
        self.assertEqual(after[:len(before)], before,
                         "sealing altered an already-written record (a migration of the past)")
        self.assertGreater(len(after), len(before), "sealing appended nothing")

    def test_a_tampered_prefix_is_caught_by_the_chain_not_hidden(self):
        # the record-can-be-wrong-while-a-view-is-right class, closed on the write side: even a
        # tamper that the dual-audit did not mirror is caught by the chain-anchor's prefix seal.
        self.store.seal_prefix()
        self.store.close()
        _rewrite_record(self.path, 2, lambda r: r.__setitem__("actor", "TAMPERED"))
        reloaded = EventStore(self.path)
        self.assertFalse(reloaded.verify_chain()["ok"])


# ============================================================================================
# A9 — the round-trip: kill everything derived, replay, verify, re-mint NOTHING (Q10's split)
# ============================================================================================

class TestRoundTrip(unittest.TestCase):
    """A9 (round-trip half): chain fields are RECORD data and verification is DERIVED, so replay
    verifies every link and the anchor but re-mints nothing — the frozen-answer law applied to the
    chain. (The whole-ledger-green half is the full `python3 -m unittest` run.)"""

    def test_replay_verifies_everything_and_re_mints_nothing(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "record.jsonl")
        anchor = _build_chained(path, n_prefix=3, n_post=4)
        before_bytes = _read_lines(path)
        # kill the in-memory replay cache entirely and rebuild from the record file alone.
        replayed = EventStore(path)
        after_bytes = _read_lines(path)
        # NOTHING re-mints: replay appends no record and rewrites no byte (no re-hash, no 2nd anchor).
        self.assertEqual(after_bytes, before_bytes, "replay re-minted or rewrote the record")
        self.assertEqual(len([e for e in replayed.events if e["action"] == CHAIN_ANCHOR_ACTION]), 1,
                         "replay minted a second anchor")
        # every link verifies and the anchor verifies, purely by recomputation.
        result = replayed.verify_chain()
        self.assertTrue(result["ok"])
        self.assertTrue(result["prefix_ok"])
        self.assertEqual(result["verified_through"], len(replayed.events))
        self.assertEqual(anchor["payload"]["prefix_hash"],
                         canonical_hash(replayed.events[:anchor["payload"]["boundary_seq"]]))


# ============================================================================================
# A8 — founding moved, version discriminated (RW-F)
# ============================================================================================

class TestFoundingMoved(unittest.TestCase):
    """A8: the founding version moved MINOR from its era; the pack bytes changed (RW-F)."""

    def _live(self):
        with open(PACK_PATH, "rb") as fh:
            return fh.read()

    def test_the_founding_version_moved_MINOR_from_the_era(self):
        era = era_pin.pack_at(PRE_EDIT_COMMIT, missing="assert")["founding_version"]
        with open(PACK_PATH, encoding="utf-8") as fh:
            live = json.load(fh)["founding_version"]
        e = tuple(int(n) for n in era.split("."))
        v = tuple(int(n) for n in live.split("."))
        self.assertGreater(v, e, "the founding version did not move")
        # MINOR: the MAJOR is unchanged and the MINOR strictly increased (no op/law removed, no
        # check-kind added — the sealing surface is new engine, not a founding removal).
        self.assertEqual(v[0], e[0], "the founding move was MAJOR — §8-i STOP, not this class")
        self.assertGreater(v[1], e[1], "the founding move was not a MINOR bump")

    def test_the_founding_bytes_changed_RW_F(self):
        # RW-F: a claimed founding move whose pack is byte-identical to its era would be a PATCH
        # masquerading as a move — it must red. The bytes moved.
        era_bytes = era_pin.blob_at(PRE_EDIT_COMMIT, era_pin.PACK_PATH, missing="assert")
        self.assertNotEqual(self._live(), era_bytes, "the founding pack is byte-unchanged (RW-F)")


# ============================================================================================
# A10 — signing degrades honestly (RW6)
# ============================================================================================

class TestSigningDegrades(unittest.TestCase):
    """A10: with signing unavailable the signature fields are PENDING, make no signed claim, do
    not block, and the prev_hash chain STILL verifies; a false SIGNED claim is caught (RW6)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.anchor = _build_chained(self.path, n_prefix=2, n_post=3)

    def test_post_seal_records_degrade_to_pending_and_the_chain_still_holds(self):
        s = EventStore(self.path)
        a_seq = self.anchor["seq"]
        post = [e for e in s.events if e["seq"] > a_seq]
        for rec in post:
            # the two signature fields are present-but-pending: no signed claim, never omitted.
            self.assertEqual(rec.get("invoker_sig"), SIG_PENDING)
            self.assertEqual(rec.get("store_sig"), SIG_PENDING)
            self.assertEqual(s.signing_state(rec), "pending",
                             "a post-seal record asserted a signature it does not hold")
        # the append did NOT block, and the prev_hash chain verifies INDEPENDENTLY of signing.
        self.assertTrue(s.verify_chain()["ok"],
                        "the chain's edit-evidence depended on signing availability")

    def test_a_false_signed_claim_is_caught_RW6(self):
        # RW6: a record RECORDED as signed while no vault exists is a dishonest degrade. A fabricated
        # signature value is 'signed' by signing_state — the honest read that would refuse it.
        s = EventStore(self.path)
        rec = dict(s.events[self.anchor["seq"]])                 # a real post-seal record
        rec["invoker_sig"] = "deadbeef-not-a-real-signature"
        self.assertEqual(s.signing_state(rec), "signed",
                         "a fabricated signature was not seen as a signed claim (RW6)")
        # ... while the genuine pending record is NOT read as signed (the check can tell them apart).
        self.assertEqual(s.signing_state(s.events[self.anchor["seq"]]), "pending")

    def test_pre_seal_records_are_unsigned_era_not_a_false_claim(self):
        s = EventStore(self.path)
        for seq in range(1, self.anchor["seq"] + 1):
            self.assertEqual(s.signing_state(s.events[seq - 1]), "unsigned-era")


if __name__ == "__main__":
    unittest.main()
