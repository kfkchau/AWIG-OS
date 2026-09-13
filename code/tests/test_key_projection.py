# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (key binding, projection, deciding-time fold); NON-GOAL: no offensive capability of
# any kind. Full declaration: SCOPE-STATEMENT.md.
"""KEY-PROJECTION (board :2906/:2910, Option A) — the per-act key read, made a SUBSET read.

Every probe here is a regression test (the campaign method: a verification probe lands as a test).

WHY THIS UNIT EXISTS. Once mover-2 declares SIGN-LAW, the signed door reads keys.bound_key on
EVERY act at operation rate. Before this unit keys._key_records did `for e in store.all(as_of)` —
a WHOLE-RECORD scan, which T-PER-ACT-PATH-READS-SUBSETS (test_ep24c) exists to forbid on that path.
This unit makes the key read projection-shaped so that scan becomes a subset read, so mover-2 can
land clean afterward. It mints NO founding vocabulary (founding stays 1.33.0) — engine machinery
only, mirroring ActionSetProjection (store.py) and the record_projection precedent.

THE TWO BINDINGS THIS BATTERY PROVES (architect :2906, non-negotiable):

  BINDING 1 — AS-OF IN BOTH FRAMES. keys.bound_key is deciding-time-sensitive. The projection must
  answer `as_of` IDENTICALLY to the fold in BOTH frames: NOW / as-of-SEQ over an EventStore, AND
  the as-of-PAST deciding-time frame served by a reconcile.WorldStore (the signed door's arrival
  re-adjudication). Driven explicitly below, both frames.

  BINDING 2 — DIFFERENTIAL EQUIVALENCE (T-CACHE-KILL class). The keys.py FOLD is the DEFINITIONAL
  SPEC and is never bent to match the projection. `projection == fold` is proven over a CHURN
  matrix (bind -> rotate -> revoke -> re-bind, multiple accounts, absent/None account, superseded
  keys) BEFORE anything relies on the projection; and the projection is derived-and-discardable —
  kill every cache and it recomputes byte-identical.

THE ORACLE is keys.bound_key(..., accelerated=False): the SAME fold body reading store.all (the
whole record). THE PROJECTION is keys.bound_key(..., accelerated=True): the same body reading
store.key_projection(account). One implementation, two record sources (store.py:276's standing
law), so a divergence can only be the subset — nothing else varies.

The world stays OPEN — nothing here narrows anything outside these throwaway stores.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel.store import EventStore, KeyProjection, RecordProjection, StaleIndex   # noqa: E402
from kernel import keys                                                            # noqa: E402
from kernel import reconcile                                                       # noqa: E402


# ---- the record population: interleaved key-lifecycle churn -----------------------------------

# occurrence times, so the deciding-time fold (WorldStore) has a real ordering to cut across.
def _t(sec):
    return f"2026-01-01T00:00:{sec:02d}Z"


class _Churn(unittest.TestCase):
    """A disposable EventStore laid with interleaved key churn across several accounts, plus a
    None/absent-account edge and non-key noise that cannot change any key answer."""

    # (occurrence-second, account, kind, public_key) — INTERLEAVED so the per-account subset must
    # pick only its own records across other accounts' records in between.
    CHURN = [
        (1,  "alice", "key-bind",   "a1"),
        (2,  "bob",   "key-bind",   "b1"),
        (3,  "alice", "key-rotate", "a2"),   # supersede: a1 -> a2, a1 stays on record as data
        (4,  "carol", "key-bind",   "c1"),
        (5,  "dave",  "key-bind",   "d1"),
        (6,  "alice", "key-revoke", None),   # revoke -> None
        (7,  "carol", "key-revoke", None),   # carol stays revoked (no re-bind)
        (8,  "dave",  "key-rotate", "d2"),
        (9,  "alice", "key-bind",   "a3"),   # re-bind after revoke -> a3
        (10, "dave",  "key-rotate", "d3"),   # superseded: d1 -> d2 -> d3
        (11, None,    "key-bind",   "n1"),   # ABSENT account field -> folds under account=None
    ]
    # The live (NOW) binding each account must resolve to — the oracle's answer, stated up front.
    EXPECTED_NOW = {"alice": "a3", "bob": "b1", "carol": None, "dave": "d3",
                    "ghost": None, None: "n1"}
    ACCOUNTS = ["alice", "bob", "carol", "dave", "ghost", None]

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "rec.jsonl")
        self.store = EventStore(self.path)
        for sec, acct, kind, pk in self.CHURN:
            payload = {"kind": kind, "public_key": pk}
            if acct is not None:
                payload["account"] = acct        # absent when acct is None (the edge)
            self.store._append({"actor": "SYSTEM", "action": kind.upper(),
                                "object": acct or "-", "occurrence_time": _t(sec),
                                "payload": payload})
        self._noise(15)

    def _noise(self, n):
        for i in range(n):
            self.store._append({"actor": "SYSTEM", "action": "process-created",
                                "object": f"obs:{i}", "payload": {"n": i}})

    # the two paths, one fold body:
    @staticmethod
    def _accel(store, account, as_of=None):
        return keys.bound_key(store, account, as_of)                    # projection

    @staticmethod
    def _oracle(store, account, as_of=None):
        return keys.bound_key(store, account, as_of, accelerated=False)  # whole-record fold

    def _as_of_points(self, store=None):
        s = store if store is not None else self.store
        return [None] + [e["seq"] for e in s.events]


# =============================================================================================
# BINDING 1 + 2 — differential equivalence over the churn matrix × both as_of frames
# =============================================================================================

class TestDifferentialEquivalence(_Churn):

    def test_the_oracle_is_the_stated_live_binding(self):
        """Anchor the oracle to the EXPECTED_NOW map, so 'projection == oracle' below is equality
        to a KNOWN answer, not two paths agreeing on a shared mistake."""
        for acct in self.ACCOUNTS:
            self.assertEqual(self._oracle(self.store, acct), self.EXPECTED_NOW[acct],
                             f"oracle wrong for {acct!r}")

    def test_now_and_every_as_of_seq_point_zero_divergent(self):
        """BINDING 1 (NOW + as-of-SEQ frame) × BINDING 2 (projection == fold). Every account at
        every seq boundary; the record lists AND the folded key compared."""
        compared = 0
        divergences = []
        for as_of in self._as_of_points():
            for acct in self.ACCOUNTS:
                a_key = self._accel(self.store, acct, as_of)
                o_key = self._oracle(self.store, acct, as_of)
                a_recs = [e["seq"] for e in keys._key_records(self.store, acct, as_of)]
                o_recs = [e["seq"] for e in
                          keys._key_records(self.store, acct, as_of, accelerated=False)]
                compared += 2
                if a_key != o_key:
                    divergences.append((as_of, acct, "key", a_key, o_key))
                if a_recs != o_recs:
                    divergences.append((as_of, acct, "records", a_recs, o_recs))
        self.assertEqual(divergences, [], f"projection and fold disagree: {divergences}")
        print(f"[KEY-PROJECTION differential] NOW+as_of-seq: {compared} answers compared, "
              f"{len(divergences)} divergent "
              f"({len(self.ACCOUNTS)} accounts x {len(self._as_of_points())} as_of points x 2)")

    def test_as_of_past_deciding_time_frame_zero_divergent(self):
        """BINDING 1, the AS-OF-PAST FRAME. A reconcile.WorldStore folds key records by DECIDING
        time; the projection built over it must answer identically to the fold reading that world —
        and must land on the SUBSTANTIVELY correct as-of-d binding (a key superseded before d reads
        the earlier binding; a key revoked before d reads None; a key bound only after d is unseen).
        Cuts placed between the churn's deciding moments."""
        # (cut-second, expected alice binding as of that cut) — alice: bind a1@1, rotate a2@3,
        # revoke@6, re-bind a3@9. `in_force_at` is STRICT ( d_law < deciding ).
        cases = [
            (2,  "a1"),    # only the bind has decided
            (4,  "a2"),    # bind + rotate decided, revoke not yet
            (7,  None),    # revoke has decided -> None
            (10, "a3"),    # re-bind decided -> a3
        ]
        compared = 0
        divergences = []
        for cut_sec, expected_alice in cases:
            cut = reconcile.deciding_time({"occurrence_time": _t(cut_sec)})
            world = reconcile.WorldStore(self.store, cut, arrival_seq=10_000)
            # substantive as-of-d correctness for alice:
            self.assertEqual(self._oracle(world, "alice"), expected_alice,
                             f"world oracle wrong for alice as of t={cut_sec}")
            for acct in self.ACCOUNTS:
                a_key = self._accel(world, acct)     # projection over the (folded) world
                o_key = self._oracle(world, acct)    # fold over the (folded) world
                compared += 1
                if a_key != o_key:
                    divergences.append((cut_sec, acct, a_key, o_key))
        self.assertEqual(divergences, [], f"world projection and fold disagree: {divergences}")
        print(f"[KEY-PROJECTION differential] as-of-past world frame: {compared} answers compared, "
              f"{len(divergences)} divergent ({len(cases)} cuts x {len(self.ACCOUNTS)} accounts)")

    def test_the_differential_can_fail(self):
        """THE COLUMN PROVEN ABLE TO FAIL (binding 2's teeth). A subset that drops records answers
        WRONG, and the accel-vs-oracle comparison must SEE it. Temporarily blind the projection's
        selector to nothing and confirm the two paths DIVERGE — then a green differential above is
        a check that could have failed, not one that cannot."""
        original = KeyProjection._selects
        try:
            KeyProjection._selects = lambda self, e: False   # a subset that selects nothing
            self.store._key_projections.clear()              # drop any cached (correct) projections
            saw_divergence = any(
                self._accel(self.store, acct) != self._oracle(self.store, acct)
                for acct in ("alice", "bob", "dave"))
            self.assertTrue(saw_divergence,
                            "a select-nothing projection did not diverge from the fold — the "
                            "differential cannot fail and proves nothing")
        finally:
            KeyProjection._selects = original
            self.store._key_projections.clear()


# =============================================================================================
# T-CACHE-KILL — the projection is DERIVED and DISCARDABLE
# =============================================================================================

class TestDerivedAndDiscardable(_Churn):

    def test_killing_the_projection_recomputes_identical(self):
        """Kill the held projection (the T-ACCELERATION-IS-DERIVED primitive); the next read proves
        itself uncurrent and rebuilds from the record alone, byte-identical. Driven at NOW and at an
        as_of-seq point."""
        for as_of in (None, self.store.events[len(self.store.events) // 2]["seq"]):
            before = {a: self._accel(self.store, a, as_of) for a in self.ACCOUNTS}
            for a in self.ACCOUNTS:
                self.store.key_projection(a).kill()
            after = {a: self._accel(self.store, a, as_of) for a in self.ACCOUNTS}
            self.assertEqual(before, after, f"kill changed an answer at as_of={as_of}")

    def test_clearing_the_whole_cache_recomputes_identical(self):
        """Drop every cached projection (the store forgets it ever built one); every answer
        reconstructs from the record with no memory of the prior projection."""
        before = {a: self._accel(self.store, a) for a in self.ACCOUNTS}
        self.store._key_projections.clear()
        after = {a: self._accel(self.store, a) for a in self.ACCOUNTS}
        self.assertEqual(before, after)

    def test_replay_from_the_record_file_alone_reconstructs_every_answer(self):
        """A SECOND store over the same record FILE starts with an empty projection cache and
        rebuilds every answer from the record alone — the projection holds no state the file does
        not (the round-trip law, applied to the key read)."""
        before = {a: self._accel(self.store, a) for a in self.ACCOUNTS}
        replay = EventStore(self.path)
        after = {a: self._accel(replay, a) for a in self.ACCOUNTS}
        self.assertEqual(before, after)


# =============================================================================================
# COHERENT-OR-REFUSE + surface — the projection never serves a subset it cannot prove
# =============================================================================================

class TestCoherentOrRefuseAndSurface(_Churn):

    def test_a_projection_behind_the_record_refuses(self):
        """A projection that has ingested MORE than the record holds cannot be a projection of it
        and REFUSES rather than serving a stale subset (RecordProjection's coherent-or-refuse
        contract, inherited unchanged)."""
        p = self.store.key_projection("alice")
        p.all()                     # build/catch up
        p._seen = len(self.store.events) + 5     # claim to have ingested records that do not exist
        with self.assertRaises(StaleIndex):
            p.all()

    def test_a_projection_naming_an_unresolvable_seq_refuses(self):
        """A seq the record does not resolve is a location that no longer exists; a projection that
        cannot resolve its own location refuses (it never serves a copy it kept)."""
        p = self.store.key_projection("alice")
        p.all()
        p._seqs = list(p._seqs) + [999_999]      # a location the record cannot resolve
        with self.assertRaises(StaleIndex):
            p.all()

    def test_public_surface_is_unchanged_six_names(self):
        """EP-24B pinned the projection's PUBLIC surface to six names (five reads plus the
        observable `catchups` counter); KeyProjection is a subclass, not a growth of it. Everything
        it adds (`_account`, the instance `_selects`) is underscored. Enumerated on an INSTANCE so
        the `catchups` data attribute (set in __init__) is counted, not just the methods."""
        p = self.store.key_projection("alice")
        public = {n for n in dir(p) if not n.startswith("_")}
        self.assertEqual(public, {"all", "by_action", "catchups", "is_current", "kill", "refresh"},
                         f"KeyProjection grew its public surface: {public}")

    def test_by_action_refuses_it_indexes_no_action(self):
        """The key fold never calls by_action; the projection declares no indexed action, so a
        by_action read refuses loud rather than returning an empty list (no silent fallback)."""
        p = self.store.key_projection("alice")
        with self.assertRaises(StaleIndex):
            p.by_action("KEY-BIND")


# =============================================================================================
# A1 STRUCTURAL — the accelerated path is a SUBSET read; no whole-record scan; one fold body
# =============================================================================================

class TestSubsetRead(_Churn):

    def test_accelerated_path_never_scans_the_whole_record(self):
        """A1: the operation-rate (accelerated) key read must NOT call store.all — it reads the
        per-account projection, which resolves through store.events / store.by_seq. Make store.all a
        tripwire and confirm an accelerated bound_key never trips it, while the oracle (which reads
        the whole record) DOES — the check proven able to fail."""
        original_all = self.store.all

        def tripwire(*a, **k):
            raise AssertionError("the accelerated key path scanned the whole record via store.all")

        self.store.all = tripwire
        try:
            self.assertEqual(keys.bound_key(self.store, "alice"), "a3")   # accelerated, no scan
        finally:
            self.store.all = original_all
        # and the oracle DOES scan -> the tripwire can fire (the row is failable):
        self.store.all = tripwire
        try:
            with self.assertRaises(AssertionError):
                keys.bound_key(self.store, "alice", accelerated=False)
        finally:
            self.store.all = original_all

    def test_the_projection_selected_only_this_accounts_records(self):
        """The subset really is a subset: alice's projection holds exactly her four key records
        (bind, rotate, revoke, re-bind), not the eleven key records on the store, and none of the
        noise."""
        p = self.store.key_projection("alice")
        p.all()
        self.assertEqual(len(p._seqs), 4, "alice's key projection is not exactly her key records")

    def test_one_fold_body_two_sources(self):
        """THE STRUCTURAL ROW. Both accelerated and oracle reach ONE function body (_key_records),
        so the differential varies exactly one thing. Replace that body and observe BOTH paths
        change — a second implementation would leave one of them standing."""
        original = keys._key_records
        sentinel = [{"payload": {"kind": "key-bind", "public_key": "SENTINEL"}}]
        try:
            keys._key_records = lambda *a, **k: sentinel
            for accelerated in (True, False):
                self.assertEqual(keys.bound_key(self.store, "alice", accelerated=accelerated),
                                 "SENTINEL", "a path did not route through the one fold body")
        finally:
            keys._key_records = original


# =============================================================================================
# Recognition is single-source (no second rule that can drift from the fold)
# =============================================================================================

class TestSingleRecognitionRule(_Churn):

    def test_projection_selects_every_kind_the_fold_recognises(self):
        """KeyProjection._selects reads keys.KEY_KINDS / keys.ACCOUNT — the fold's OWN constants —
        so a record of each recognised kind is selected. If the projection's recognition ever
        drifted from the fold's, one of these kinds would go unselected and the differential would
        red; this pins the source directly."""
        for kind in keys.KEY_KINDS:
            e = {"payload": {"kind": kind, "account": "zed"}}
            self.assertTrue(KeyProjection(self.store, "zed")._selects(e),
                            f"the projection does not recognise {kind!r} — a second rule has drifted")
        # a non-key kind, and another account's key record, are BOTH excluded:
        self.assertFalse(KeyProjection(self.store, "zed")._selects(
            {"payload": {"kind": "process-created", "account": "zed"}}))
        self.assertFalse(KeyProjection(self.store, "zed")._selects(
            {"payload": {"kind": "key-bind", "account": "other"}}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
