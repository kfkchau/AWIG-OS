"""EP-24B — the pre-crux engine pack, minimal: the acceptance battery.

Named before code in the EP file, landed here as regression tests.

  ITEM A — the authority fold made governance-proportional
  T-ACCELERATION-IS-DERIVED       kill every acceleration structure, replay from the record
                                  alone, every authority answer identical. A cache under P2
                                  or it does not ship.
  T-FOLD-DIFFERENTIAL             the accelerated fold and the RETAINED unaccelerated fold
                                  return identical answers over a generated population
                                  covering all four grant dimensions, space containment,
                                  role routing, revocation and supersession — at head and
                                  at three as-of points. Zero divergence, count reported.
                                  (The whole-suite leg is `tests/ep24b_differential.py`,
                                  run directly; its result is in the build log.)
  T-FOLD-COHERENT-OR-REFUSE       after a revocation, a superseding grant and a scope
                                  amendment the next consultation recomputes; a stale index
                                  never serves. The column CAN fail: a deliberately stalled
                                  index is shown to answer WRONG, and the live path detects.
  T-FOLD-GOVERNANCE-PROPORTIONAL  measured both directions. Non-governance growth does not
                                  move the fold's work; law-and-grant growth does.
  T-NO-STORED-TABLE (extended)    no verdict, no permission set, no computed complement, and
                                  nothing keyed by actor-and-action, anywhere on the path.

  ITEM B — the two envelope routers
  T-ROUTER-OCCURRENCE-TIME        an op declares which parameter supplies the envelope's
  T-ROUTER-PROVENANCE             occurrence_time / provenance; the record carries it.
  T-ROUTER-REFUSES-MISSING-PARAMETER  a call omitting a declared parameter refuses through
                                  the gate's nonconforming-call path, cited, nothing written.
  T-ROUTER-FAMILY-CONSISTENT      the two new routers are members of the family the
                                  interpreter already has, not a parallel mechanism.

  WHOLE-EP
  T-DEGENERATE-IDENTITY           an op declaring no router behaves exactly as today (and
                                  the entire pre-existing suite stays green and unchanged —
                                  that half is the suite itself, reported in the log).
"""

import datetime
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ep24b_differential import as_of_points, differential                    # noqa: E402
from kernel import authority, opdefs                                         # noqa: E402
from kernel.compose import build_full_kernel                                 # noqa: E402
from kernel.errors import OpError                                            # noqa: E402
from kernel.store import (                                                   # noqa: E402
    GOVERNANCE_INDEXED_ACTIONS, EventStore, GovernanceIndex, StaleIndex, is_governance_record,
)
from kernel.views import Views                                               # noqa: E402

MOTHER = "space:root"


class _World(unittest.TestCase):
    """A composed kernel in a disposable directory. The world stays OPEN unless a test
    narrows it — narrowing happens only inside these throwaway worlds."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"))

    # ---- the generated population: all four grant dimensions, containment, roles, revoke ----
    def populate(self):
        g = self.gate.execute
        g("CREATE-SPACE", "owner", {"name": "alpha", "parent": MOTHER})
        g("CREATE-SPACE", "owner", {"name": "alpha-child", "parent": "space:alpha"})
        g("CREATE-SPACE", "owner", {"name": "beta", "parent": MOTHER})
        for a in ("ann", "bob", "cat", "dan"):
            g("CREATE-ACCOUNT", "owner", {"account_id": a, "actor_class": "human"})
        g("CREATE-ROLE", "owner", {"name": "editor", "space": "space:alpha"})
        # narrow on every dimension, one at a time
        g("GRANT", "owner", {"grant_id": "g_action", "grantee": "ann",
                             "actions": ["CREATE-INFO"], "info": "*", "space": "space:alpha"})
        g("GRANT", "owner", {"grant_id": "g_info", "grantee": "bob",
                             "actions": "*", "info": ["law"], "space": "space:alpha"})
        g("GRANT", "owner", {"grant_id": "g_space", "grantee": "cat",
                             "actions": "*", "info": "*", "space": "space:beta"})
        # the ROLE route: power granted to a role, and a hold-grant putting dan in it
        g("GRANT", "owner", {"grant_id": "g_role_power", "grantee": "role:editor",
                             "actions": ["CREATE-RULE"], "info": "*", "space": "space:alpha"})
        g("GRANT", "owner", {"grant_id": "g_role_hold", "grantee": "dan",
                             "actions": ["hold"], "info": ["role:editor"], "space": "space:alpha"})
        # SUPERSESSION: the same grant id re-minted wider, then a REVOCATION of another
        g("GRANT", "owner", {"grant_id": "g_super", "grantee": "ann",
                             "actions": ["CREATE-RULE"], "info": "*", "space": "space:beta"})
        g("GRANT", "owner", {"grant_id": "g_super", "grantee": "ann",
                             "actions": ["CREATE-RULE", "GRANT"], "info": "*", "space": MOTHER})
        g("GRANT", "owner", {"grant_id": "g_doomed", "grantee": "bob",
                             "actions": "*", "info": "*", "space": MOTHER})
        g("REVOKE", "owner", {"grant_id": "g_doomed"})
        # SCOPE AMENDMENT: re-parent a space, which moves containment for every grant over it
        g("CREATE-SPACE", "owner", {"name": "beta", "parent": "space:alpha"})

    def narrow(self):
        """Revoke the founding openness grant — IN THIS DISPOSABLE WORLD ONLY. Needed because
        under openness every verdict is already yes, so nothing a stale index served could be
        seen to be wrong. The real world stays open (the owner's standing word); the chain-end
        is exempt at the gate, so this world can still be governed after the narrowing."""
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.assertNotIn("grant:founding-openness", self.views.grants())

    def noise(self, n, action="process-created"):
        """Non-governance growth: records that cannot change what covers() answers."""
        for i in range(n):
            self.store._append({"actor": "SYSTEM", "action": action,
                                "object": f"obs:{action}:{i}:{len(self.store.events)}",
                                "rule_cited": "M1-OBSERVATION", "payload": {"n": i}})

    def answers(self, views=None):
        """Every authority answer this world can be asked, as one comparable value."""
        v = views if views is not None else self.views
        spaces = sorted(v.spaces())
        actors = sorted(v.accounts()) + ["nobody-at-all"]
        out = {"spaces": {k: dict(x) for k, x in v.spaces().items()},
               "roles": {k: dict(x) for k, x in v.roles().items()},
               "grants": {k: dict(x) for k, x in v.grants().items()},
               "mother": v.mother_space()}
        for a in actors:
            out[f"pv:{a}"] = str(v.power_view(a))
            for sp in spaces:
                out[f"reach:{a}:{sp}"] = v.reaches_space(a, sp)
                for act in ("CREATE-INFO", "CREATE-RULE", "GRANT", "hold"):
                    out[f"covers:{a}:{act}:{sp}"] = v.covers(a, act, "law", sp)
        return out


# =============================================================================================
# T-ACCELERATION-IS-DERIVED — the structure is a cache under P2 or it does not ship
# =============================================================================================

class TestAccelerationIsDerived(_World):
    def test_killing_the_index_changes_no_authority_answer(self):
        self.populate()
        before = self.answers()
        index = self.store.governance_index()
        self.assertTrue(index._seqs, "the index selected nothing — it is not being used")
        index.kill()
        self.assertEqual(index._seen, 0)
        self.assertEqual(index._seqs, [])
        self.assertEqual(self.answers(), before,
                         "an authority answer moved when the acceleration was deleted")
        self.assertTrue(index._seqs, "the index did not rebuild itself from the record")

    def test_replay_from_the_record_file_alone_reconstructs_every_answer(self):
        self.populate()
        before = self.answers()
        # a brand new kernel over the same record FILE: nothing derived carries across
        store2, gate2, views2, _b2, _s2 = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs2"))
        self.assertIsNone(store2._gov_index, "the index was built before anything asked for it")
        self.assertEqual(self.answers(views2), before,
                         "replay from the record alone did not reconstruct the authority answers")

    def test_the_index_is_rebuilt_identically_from_the_record(self):
        self.populate()
        self.noise(50)
        live = self.store.governance_index()
        live.all()
        selected = list(live._seqs)
        fresh = GovernanceIndex(self.store)
        fresh.refresh()
        self.assertEqual(fresh._seqs, selected,
                         "rebuilding the index from the record produced a different selection")
        # and the selection IS the law-and-grant subset, derived by the predicate
        self.assertEqual(selected, [e["seq"] for e in self.store.events if is_governance_record(e)])

    def test_killing_the_views_memo_changes_no_authority_answer(self):
        self.populate()
        before = self.answers()
        self.views._memo.clear()
        self.views._memo_gen = 0
        self.assertEqual(self.answers(), before)


# =============================================================================================
# T-FOLD-DIFFERENTIAL — never a divergence from the unaccelerated fold (the owner's wording)
# =============================================================================================

class TestFoldDifferential(_World):
    def _assert_no_divergence(self, label):
        compared, divergences = differential(self.views, as_of_points(self.store))
        self.assertEqual(divergences, [], f"{label}: {len(divergences)} divergence(s)")
        self.assertGreater(compared, 200, f"{label}: the differential compared too little to mean anything")
        return compared

    def test_founding_world(self):
        n = self._assert_no_divergence("founding world")
        print(f"\n[EP-24B T-FOLD-DIFFERENTIAL] founding world: {n} fold answers compared, 0 divergent")

    def test_generated_population(self):
        self.populate()
        n = self._assert_no_divergence("generated population")
        print(f"[EP-24B T-FOLD-DIFFERENTIAL] generated population: {n} fold answers compared, 0 divergent")

    def test_generated_population_under_operational_noise(self):
        """The case the acceleration exists for: a governance-small world inside a big record."""
        self.populate()
        self.noise(2000)
        n = self._assert_no_divergence("population + 2000 non-governance records")
        print(f"[EP-24B T-FOLD-DIFFERENTIAL] population + 2,000 observations: {n} fold answers "
              f"compared, 0 divergent")

    def test_narrowed_world(self):
        """Openness revoked — where a missed grant record would show as a wrong verdict rather
        than as nothing at all. A disposable world; the real world stays open."""
        self.populate()
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.assertNotIn("grant:founding-openness", self.views.grants())
        n = self._assert_no_divergence("narrowed world")
        print(f"[EP-24B T-FOLD-DIFFERENTIAL] openness narrowed to zero: {n} fold answers "
              f"compared, 0 divergent")

    def test_the_differential_itself_can_fail(self):
        """A comparator that cannot report a divergence proves nothing. Feed the fold a
        deliberately wrong subset and the comparator must say so."""
        self.populate()
        index = self.store.governance_index()
        index.all()
        real = list(index._seqs)
        try:
            index._seqs = [s for s in real
                           if (self.store.by_seq(s).get("payload") or {}).get("kind") != "grant"]
            index._prove_current = lambda: None          # freeze it in the mutilated state
            _compared, divergences = differential(self.views, (None,))
            self.assertTrue(divergences,
                            "the differential reported no divergence against a subset with every "
                            "grant removed — the comparator cannot fail and proves nothing")
        finally:
            del index._prove_current
            index._seqs = real


# =============================================================================================
# T-FOLD-COHERENT-OR-REFUSE — a hop never lies (design/36 K3, the R26 law)
# =============================================================================================

class _StalledIndex:
    """A deliberately stalled index: it holds a selection taken at one moment and NEVER
    catches up. This is what a maintenance failure looks like from the fold's side, and it
    exists so the coherence column can be shown to fail rather than asserted to hold."""

    def __init__(self, store, seqs):
        self._store, self._seqs = store, list(seqs)

    def all(self, as_of_seq=None):
        return [self._store.by_seq(s) for s in self._seqs
                if as_of_seq is None or s <= as_of_seq]

    def by_action(self, action, as_of_seq=None):
        return [e for e in self.all(as_of_seq) if e["action"] == action]


class TestFoldCoherentOrRefuse(_World):
    def _stalled_now(self):
        index = self.store.governance_index()
        index.all()
        return _StalledIndex(self.store, index._seqs)

    def test_a_revocation_is_never_served_from_a_stale_index(self):
        self.populate()
        self.narrow()
        self.assertTrue(self.views.covers("cat", "CREATE-INFO", "law", "space:beta"))
        stalled = self._stalled_now()
        index = self.store.governance_index()
        before = index.catchups

        self.gate.execute("REVOKE", "owner", {"grant_id": "g_space"})

        # the column CAN fail: the stalled selection still answers the OLD verdict
        self.assertTrue(authority.covers(stalled, "cat", "CREATE-INFO", "law", "space:beta"),
                        "the stalled index does not answer differently, so this proves nothing")
        # the live path detects it is behind the record, recomputes, and answers the new truth
        self.assertFalse(self.views.covers("cat", "CREATE-INFO", "law", "space:beta"))
        self.assertGreater(index.catchups, before,
                           "the index served without proving itself current against the record")
        self.assertEqual(self.views.covers("cat", "CREATE-INFO", "law", "space:beta"),
                         self.views.authority_fold("covers", "cat", "CREATE-INFO", "law",
                                                   "space:beta", accelerated=False))

    def test_a_superseding_grant_is_never_served_from_a_stale_index(self):
        self.populate()
        self.narrow()
        # FILE-WRITE is in none of ann's grants; g_action is the one that will be superseded
        self.assertFalse(self.views.covers("ann", "FILE-WRITE", "law", "space:alpha"))
        stalled = self._stalled_now()
        self.gate.execute("GRANT", "owner", {"grant_id": "g_action", "grantee": "ann",
                                             "actions": ["CREATE-INFO", "FILE-WRITE"], "info": "*",
                                             "space": "space:alpha"})
        self.assertFalse(authority.covers(stalled, "ann", "FILE-WRITE", "law", "space:alpha"),
                         "the stalled index does not answer differently, so this proves nothing")
        self.assertTrue(self.views.covers("ann", "FILE-WRITE", "law", "space:alpha"))

    def test_a_scope_amendment_is_never_served_from_a_stale_index(self):
        self.populate()
        self.narrow()
        # gamma is founded under the MOTHER, outside the reach of ann's CREATE-INFO grant
        # (which is scoped to space:alpha)
        self.gate.execute("CREATE-SPACE", "owner", {"name": "gamma", "parent": MOTHER})
        self.assertFalse(self.views.covers("ann", "CREATE-INFO", "law", "space:gamma"))
        stalled = self._stalled_now()
        # re-parent gamma under alpha, where ann's grant reaches: containment moves, and with it
        # the verdict — without a single grant record changing
        self.gate.execute("CREATE-SPACE", "owner", {"name": "gamma", "parent": "space:alpha"})
        self.assertFalse(authority.covers(stalled, "ann", "CREATE-INFO", "law", "space:gamma"),
                         "the stalled index does not answer differently, so this proves nothing")
        self.assertTrue(self.views.covers("ann", "CREATE-INFO", "law", "space:gamma"))

    def test_the_currency_proof_is_two_sided(self):
        """It must say 'current' when nothing moved, or 'detection' means nothing."""
        self.populate()
        index = self.store.governance_index()
        index.all()
        self.assertTrue(index.is_current())
        before = index.catchups
        for _ in range(5):
            self.views.covers("ann", "CREATE-INFO", "law", "space:alpha")
        self.assertEqual(index.catchups, before, "the index recomputed with nothing appended")
        self.noise(1)
        self.assertFalse(index.is_current())

    def test_an_index_that_cannot_be_reconciled_refuses_rather_than_serving(self):
        index = self.store.governance_index()
        index.all()
        index._seen = len(self.store.events) + 500     # an index of a record this is not
        with self.assertRaises(StaleIndex):
            index.all()

    def test_an_index_naming_a_record_that_does_not_resolve_refuses(self):
        index = self.store.governance_index()
        index.all()
        index._seqs = list(index._seqs) + [len(self.store.events) + 99]
        with self.assertRaises(StaleIndex):
            index.all()

    def test_a_read_outside_the_subset_fails_loud_instead_of_answering_empty(self):
        """The one way a future fold change could silently starve: asking for records the
        index was not built to select. An empty list is a wrong answer wearing the costume of
        a right one, so the index refuses instead."""
        index = self.store.governance_index()
        for action in GOVERNANCE_INDEXED_ACTIONS:
            index.by_action(action)                      # every admitted key answers
        with self.assertRaises(StaleIndex):
            index.by_action("process-created")


# =============================================================================================
# T-FOLD-GOVERNANCE-PROPORTIONAL — K3's second half as a test that can fail
# =============================================================================================

class TestFoldGovernanceProportional(_World):
    def _fold_ms(self, reps=40):
        m = self.views.mother_space()
        self.views.covers("ann", "CREATE-INFO", "law", m)
        t0 = time.perf_counter()
        for _ in range(reps):
            self.views.covers("ann", "CREATE-INFO", "law", m)
        return (time.perf_counter() - t0) / reps * 1000.0

    def _records_the_fold_reads(self):
        return len(self.store.governance_index().all())

    def test_non_governance_growth_does_not_move_the_fold(self):
        self.populate()
        base_reads, base_ms = self._records_the_fold_reads(), self._fold_ms()
        base_total = len(self.store.events)
        self.noise(8000)
        grown_reads, grown_ms = self._records_the_fold_reads(), self._fold_ms()
        # the deterministic direction: the fold reads the same records it read before
        self.assertEqual(grown_reads, base_reads,
                         "non-governance growth changed what the fold has to read")
        self.assertGreater(len(self.store.events), base_total + 7000)
        # [EP-25 W0 — DOCUMENTED FLIP, directed by EP-25 ADDENDUM 6 at the EP-24C verdict.]
        # A duration assertion stood here (`assertLess(grown_ms, max(base_ms * 4.0, 0.5))`). It was
        # defective in BOTH directions at once: it went red on a loaded box while the property held,
        # and it stayed green on a real regression, because the tolerance a timing bound needs to
        # survive machine noise is wider than the signal it exists to catch. Three verifier runs
        # printed 1.7577 -> 0.1560, 2.0215 -> 0.2028 and 0.1187 -> 0.1804 ms behind it, the last of
        # those being the cost rising by half again with the assertion still passing. Standing law
        # now: a property test asserts a COUNTABLE, never a duration. The countable was already being
        # computed two lines above and discarded next to the timing bound that was being trusted —
        # `grown_reads == base_reads` IS the property (non-governance growth must not change how many
        # records the fold reads), and its governance-direction twin is the integer assertion in
        # test_governance_growth_does_move_the_fold. The milliseconds stay below as REPORTED
        # measurements carrying their conditions (both record counts), never as an assertion.
        print(f"\n[EP-24B T-FOLD-GOVERNANCE-PROPORTIONAL] non-governance growth "
              f"{base_total} -> {len(self.store.events)} records: fold reads {base_reads} -> "
              f"{grown_reads}; fold {base_ms:.4f} -> {grown_ms:.4f} ms")

    def test_governance_growth_does_move_the_fold(self):
        """The other direction, and it is what makes the first one meaningful: if the fold
        never grew with anything, it would not be reading the record."""
        self.populate()
        base_reads = self._records_the_fold_reads()
        for i in range(200):
            self.gate.execute("GRANT", "owner", {"grant_id": f"bulk_{i}", "grantee": f"acct_{i}",
                                                 "actions": ["CREATE-INFO"], "info": "*",
                                                 "space": "space:alpha"})
        grown_reads = self._records_the_fold_reads()
        self.assertEqual(grown_reads, base_reads + 200,
                         "law-and-grant growth did not move what the fold reads")
        print(f"[EP-24B T-FOLD-GOVERNANCE-PROPORTIONAL] governance growth: fold reads "
              f"{base_reads} -> {grown_reads} after 200 grants")

    def test_the_fold_reads_only_law_and_grant_records(self):
        self.populate()
        self.noise(200)
        read = self.store.governance_index().all()
        self.assertTrue(all(is_governance_record(e) for e in read))
        self.assertLess(len(read), len(self.store.events) / 5)


# =============================================================================================
# T-NO-STORED-TABLE (extended over this surface)
# =============================================================================================

class TestNoStoredTable(_World):
    def test_the_index_holds_integers_and_nothing_else(self):
        """Not an assertion about intent — a fact about the contents. There is nowhere in
        this structure for a verdict, a permission set or a computed complement to live."""
        self.populate()
        index = self.store.governance_index()
        index.all()
        self.assertTrue(index._seqs)
        for s in index._seqs:
            self.assertIs(type(s), int)
        for action, seqs in index._by_action.items():
            self.assertIs(type(action), str)
            for s in seqs:
                self.assertIs(type(s), int)
        scalars = {k: v for k, v in index.__dict__.items()
                   if k not in ("_store", "_seqs", "_by_action")}
        for k, v in scalars.items():
            self.assertIs(type(v), int, f"index attribute {k} is not an integer: {v!r}")

    def test_asking_the_same_question_many_times_stores_nothing(self):
        """A cache keyed by actor would grow here. Nothing grows."""
        self.populate()
        index = self.store.governance_index()
        index.all()
        before = (list(index._seqs), {k: list(v) for k, v in index._by_action.items()},
                  dict(self.views._memo))
        for a in ("ann", "bob", "cat", "dan", "nobody-at-all"):
            for act in ("CREATE-INFO", "CREATE-RULE", "GRANT", "hold", "never-granted"):
                self.views.covers(a, act, "law", "space:alpha")
                self.views.power_view(a)
        after = (list(index._seqs), {k: list(v) for k, v in index._by_action.items()},
                 dict(self.views._memo))
        self.assertEqual(after[0], before[0])
        self.assertEqual(after[1], before[1])
        self.assertEqual(set(after[2]), set(before[2]),
                         "an authority answer was memoised — the fold's answers are computed, never kept")

    def test_no_memo_key_names_an_authority_fold(self):
        self.populate()
        for a in ("ann", "bob"):
            self.views.covers(a, "CREATE-INFO", "law", MOTHER)
        for key in self.views._memo:
            for fold in Views.AUTHORITY_FOLDS:
                self.assertFalse(key.startswith(fold + ":"),
                                 f"the views memo holds an authority answer under {key!r}")

    def test_the_verdict_is_recomputed_from_the_record_every_call(self):
        self.populate()
        self.narrow()
        self.assertTrue(self.views.covers("cat", "CREATE-INFO", "law", "space:beta"))
        self.gate.execute("REVOKE", "owner", {"grant_id": "g_space"})
        self.assertFalse(self.views.covers("cat", "CREATE-INFO", "law", "space:beta"))
        self.gate.execute("GRANT", "owner", {"grant_id": "g_space", "grantee": "cat",
                                             "actions": "*", "info": "*", "space": "space:beta"})
        self.assertTrue(self.views.covers("cat", "CREATE-INFO", "law", "space:beta"))

    def test_the_index_exposes_no_verdict_bearing_method(self):
        index = self.store.governance_index()
        public = {n for n in dir(index) if not n.startswith("_")}
        self.assertEqual(public, {"all", "by_action", "catchups", "is_current", "kill", "refresh"},
                         "the index grew a surface beyond selecting records")

    def test_the_engine_source_holds_no_actor_keyed_permission_structure(self):
        """The tell the EP names, checked against the code that changed: nothing on this
        surface is keyed by an actor or an (actor, action) pair."""
        from kernel import store as store_mod
        with open(store_mod.__file__, encoding="utf-8") as f:
            src = f.read()
        block = src[src.index("class GovernanceIndex"):]
        for forbidden in ("account", "actor", "grantee", "verdict", "permission"):
            self.assertNotIn(f"[{forbidden}", block,
                             f"the index indexes by {forbidden} — that is a table, not an index")


# =============================================================================================
# ITEM B — the two envelope routers
# =============================================================================================

WHEN = "2019-03-04T05:06:07+00:00"
PROV = {"asserted_by": "window:proc@m1.1", "source": "observation", "could_read": []}


class TestRouters(_World):
    def define(self, name, **extra):
        d = {"law_cited": "M1-OBSERVATION", "description": "a test-world op",
             "params": {"subject": "required"}, "object_param": "subject",
             "payload_from": ["subject"], "structural_params": ["subject"]}
        d.update(extra)
        self.gate.execute("CREATE-OP", "owner", {"name": name, "definition": d})
        return d

    def test_router_occurrence_time(self):
        self.define("OBS-WHEN", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        rec = self.gate.execute("OBS-WHEN", "owner", {"subject": "thing:1", "at": WHEN})
        self.assertEqual(rec["occurrence_time"], WHEN)
        # and it is the CALLER's value, not the store's mint
        self.assertNotEqual(rec["occurrence_time"], rec["record_time"])

    def test_router_provenance(self):
        self.define("OBS-PROV", params={"subject": "required", "prov": "optional"},
                    provenance_param="prov", structural_params=["subject", "prov"])
        rec = self.gate.execute("OBS-PROV", "owner", {"subject": "thing:2", "prov": PROV})
        self.assertEqual(dict(rec["provenance"])["asserted_by"], PROV["asserted_by"])
        self.assertEqual(dict(rec["provenance"])["source"], "observation")

    def test_both_routers_on_one_op(self):
        self.define("OBS-BOTH", params={"subject": "required", "at": "optional", "prov": "optional"},
                    occurrence_time_param="at", provenance_param="prov",
                    structural_params=["subject", "at", "prov"])
        rec = self.gate.execute("OBS-BOTH", "owner",
                                {"subject": "thing:3", "at": WHEN, "prov": PROV})
        self.assertEqual(rec["occurrence_time"], WHEN)
        self.assertEqual(dict(rec["provenance"])["asserted_by"], PROV["asserted_by"])

    def test_router_refuses_missing_parameter(self):
        """The declared parameter is NOT marked required in `params`, so only the router's own
        check can catch its absence — which is the case that matters."""
        self.define("OBS-STRICT", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        before = len(self.store.events)
        with self.assertRaises(OpError) as raised:
            self.gate.execute("OBS-STRICT", "owner", {"subject": "thing:4"})
        self.assertEqual(raised.exception.rule, "AR-2")
        # nothing of the act was written: no decision record, and the refusal itself is recorded
        after = self.store.events[before:]
        self.assertFalse(any(e["action"] == "OBS-STRICT" for e in self.store.events))
        refusals = [e for e in after if e["action"] == "op-refused"]
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["rule_cited"], "AR-2")
        self.assertEqual((refusals[0].get("payload") or {})["op"], "OBS-STRICT")

    def test_router_refuses_missing_provenance_parameter(self):
        self.define("OBS-STRICT-P", params={"subject": "required", "prov": "optional"},
                    provenance_param="prov", structural_params=["subject", "prov"])
        with self.assertRaises(OpError) as raised:
            self.gate.execute("OBS-STRICT-P", "owner", {"subject": "thing:5"})
        self.assertEqual(raised.exception.rule, "AR-2")
        self.assertFalse(any(e["action"] == "OBS-STRICT-P" for e in self.store.events))

    def test_router_refuses_an_empty_value_the_same_way(self):
        self.define("OBS-EMPTY", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        with self.assertRaises(OpError) as raised:
            self.gate.execute("OBS-EMPTY", "owner", {"subject": "thing:6", "at": ""})
        self.assertEqual(raised.exception.rule, "AR-2")

    # ---- T-ROUTER-FAMILY-CONSISTENT ----
    def test_the_two_new_routers_are_members_of_the_declared_family(self):
        self.assertEqual(opdefs.ENVELOPE_ROUTERS,
                         ("target_param", "content_form", "evidence_param", "stamp_actor",
                          "occurrence_time_param", "provenance_param"))

    def test_every_router_is_read_by_the_one_interpreter_and_by_nothing_else(self):
        """One reader, structurally: every mention of every router name in the module lies
        either in the family declaration or inside `_interpreter`. A router read anywhere else
        would be a parallel mechanism wearing the family's name."""
        with open(opdefs.__file__, encoding="utf-8") as f:
            src = f.read()
        decl = (src.index("ENVELOPE_ROUTERS = "), src.index("OP_CHECKS = "))
        body = (src.index("def _interpreter"), src.index("def live_definitions"))
        for router in opdefs.ENVELOPE_ROUTERS:
            hits, at = [], src.find(router)
            while at != -1:
                hits.append(at)
                at = src.find(router, at + 1)
            self.assertTrue(hits, f"{router} appears nowhere in the interpreter module")
            self.assertTrue(any(body[0] <= i < body[1] for i in hits),
                            f"{router} is not read inside the one interpreter")
            for i in hits:
                self.assertTrue(decl[0] <= i < decl[1] or body[0] <= i < body[1],
                                f"{router} is read outside the family declaration and the one "
                                f"interpreter (offset {i})")
        # and no router is reached through a branch on which op is running
        self.assertNotIn("opname ==", src[body[0]:body[1]])

    def test_a_router_works_on_any_op_name_and_survives_replay(self):
        """The declaration is DATA on the op's own record, not code: define two differently
        named ops carrying the same router, then rebuild the kernel from the record file alone
        and invoke them again."""
        self.define("ALPHA-OBS", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        self.define("OMEGA-OBS", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        for name in ("ALPHA-OBS", "OMEGA-OBS"):
            self.assertEqual(self.gate.execute(name, "owner",
                                               {"subject": f"x:{name}", "at": WHEN})["occurrence_time"],
                             WHEN)
        # EP-MAINT-OUTSIDE-5 (re-spec C): close the live writer before the rebuild so the replayed
        # kernel is a WRITER able to invoke the ops again (release-on-close); a second live open
        # would be demoted to a reader and its append refused by name.
        self.store.close()
        _s2, gate2, _v2, _b2, _x2 = build_full_kernel(self.path, os.path.join(self.dir, "blobs2"))
        for name in ("ALPHA-OBS", "OMEGA-OBS"):
            self.assertTrue(gate2.has(name))
            self.assertEqual(gate2.execute(name, "owner",
                                           {"subject": f"y:{name}", "at": WHEN})["occurrence_time"],
                             WHEN)

    def test_the_existing_four_routers_are_untouched(self):
        self.define("OLD-FAMILY", params={"subject": "required", "tgt": "optional", "ev": "optional"},
                    target_param="tgt", evidence_param="ev", content_form="blob",
                    stamp_actor=["granter"], payload_from=["subject", "granter"],
                    structural_params=["subject", "tgt", "ev"])
        rec = self.gate.execute("OLD-FAMILY", "owner",
                                {"subject": "thing:7", "tgt": "t:1", "ev": "because",
                                 "granter": "someone-else"})
        self.assertEqual(rec["target"], "t:1")
        self.assertEqual(rec["evidence_summary"], "because")
        self.assertEqual(rec["content_form"], "blob")
        self.assertEqual(dict(rec["payload"])["granter"], "owner")


# =============================================================================================
# T-DEGENERATE-IDENTITY — an op declaring no router behaves exactly as today
# =============================================================================================

class TestDegenerateIdentity(_World):
    def test_an_op_declaring_no_router_is_unchanged(self):
        self.gate.execute("CREATE-OP", "owner", {"name": "PLAIN-OP", "definition": {
            "law_cited": "M1-OBSERVATION", "description": "no routers declared",
            "params": {"subject": "required"}, "object_param": "subject",
            "payload_from": ["subject"], "structural_params": ["subject"]}})
        rec = self.gate.execute("PLAIN-OP", "owner", {"subject": "thing:8"})
        second = self.gate.execute("PLAIN-OP", "owner", {"subject": "thing:9"})
        # occurrence_time is the store's mint (a well-formed ISO instant at append time)
        #
        # [MAINT-1 — DOCUMENTED FLIP, 2026-08-20, serving the §1 extension filed FIFTEEN LINES
        # OF THIS SAME FILE AWAY at :381-392 — a property test asserts a COUNTABLE, never a
        # duration. Board :941 filed this row as one of three live breaches; :1064 ruled its
        # form.] WHAT STOOD HERE: `assertLess(abs((now(utc) - minted).total_seconds()), 60)`.
        # WHY IT WAS WRONG: the subject of this row is that `occurrence_time` is THE STORE'S
        # MINT AT APPEND TIME — the comment above says exactly that — and NOT that the record
        # is recent. Sixty seconds was a proxy for "computed, not carried", and like every
        # duration proxy it was defective in both directions: a paused or loaded box reds it
        # while the property holds, and a carried constant minted less than a minute ago
        # passes it while the property is broken. It also read a clock AT ASSERT TIME, so the
        # assertion's own basis was outside the records it was about. WHAT CARRIES THE CLAIM
        # NOW: two records appended in ONE world must carry DIFFERENT occurrence_time values,
        # each parsing as a well-formed ISO INSTANT (tz-aware, not a naive datetime).
        # Population: those two records. Basis: the two values read FROM the records — no
        # clock is read here at all. The countable is load-IMMUNE in the direction that
        # matters: load can only push two mints further apart, never together, whereas the
        # bound it replaces got harder to satisfy as the box got busier.
        minted = datetime.datetime.fromisoformat(rec["occurrence_time"])
        minted_again = datetime.datetime.fromisoformat(second["occurrence_time"])
        self.assertIsNotNone(minted.tzinfo, "occurrence_time parsed to a NAIVE datetime, so "
                                            "it is not an instant and names no moment")
        self.assertIsNotNone(minted_again.tzinfo, "occurrence_time parsed to a NAIVE "
                                                  "datetime, so it is not an instant")
        self.assertNotEqual(rec["occurrence_time"], second["occurrence_time"],
                            "two records appended in one world carry the SAME "
                            "occurrence_time, so the field is a CARRIED CONSTANT rather "
                            "than the store's mint at append time")
        # provenance is the gate's resolution of who invoked, exactly as before
        self.assertEqual(dict(rec["provenance"])["asserted_by"], "owner")
        self.assertEqual(dict(rec["provenance"])["source"], "system")
        self.assertIsNone(rec["target"])
        self.assertEqual(rec["content_form"], "inline")

    #: The founding ops that declare the provenance router, PINNED. EP-25's custody ops are the
    #: router's first consumers, so the assertion below could not stay "nobody uses it" — and it
    #: is INVERTED rather than deleted, because "nobody" and "exactly these" are both checkable
    #: while only the second one still catches something. A new op quietly declaring a router now
    #: fails here and has to be argued for.
    FOUNDING_PROVENANCE_ROUTERS = {
        "CUSTODY-HALT", "FILE-CHOWN", "FILE-CLOSE", "FILE-MKDIR", "FILE-OPEN",
        "FILE-READ-AGGREGATE", "FILE-RENAME", "FILE-RMDIR", "FILE-SYMLINK", "FILE-TIMES",
        "FILE-TRUNCATE", "FILE-XATTR-LAW", "FILE-XATTR-REMOVE", "FILE-XATTR-SET", "MAP-UID",
        # [EP-25 ADDENDUM 9 C1, argued for rather than added quietly.] The two lock ops carry
        # the port's uid/gid/pid as recorded EVIDENCE for the same reason every other custody
        # op does: who asked for exclusivity is part of what a lock decision is. They are new
        # ops with no non-port caller, so the router's refuse-on-absence (raised as R-1 at the
        # crux) cannot bite them.
        "FILE-LOCK", "FILE-UNLOCK",
        # [EP-27B, argued for rather than added quietly.] The five campaign-1 files ops that
        # EP-25 raised as R-1: they have BOTH a port caller and a non-port one, so under a
        # refuse-on-absence declaration the second caller becomes nonconforming. They declare
        # the router DEFAULTED, which is the distinction EP-27B added — port evidence when a
        # port supplies it, the gate's own true resolution when nothing does.
        "FILE-CREATE", "FILE-WRITE", "FILE-LINK", "FILE-UNLINK", "FILE-PERM",
    }

    #: The founding ops that declare the occurrence-time router, PINNED. [EP-27B, DOCUMENTED
    #: FLIP.] The half below read "no founding op declares it", which was true while the
    #: declaration could only mean REQUIRED — declaring it on a law op would have made every
    #: existing caller nonconforming, which is precisely why K7 was unreachable through the
    #: shipped founding (design/36 ADDENDUM F.2). With the required-or-defaulted distinction the
    #: three law-MAKING ops declare it defaulted, so a law-family record may carry the moment it
    #: was decided away from the store. FILE-XATTR-LAW is law-family and is deliberately absent:
    #: at the mount's port the gate decides and appends in one act, so its two times coincide by
    #: construction and there is no away-from-the-store moment for it to carry.
    # [MAINT, §A57 population re-derivation, architect ruling `:2895`.] The COMPLETE-KEY-FAMILY
    # founding move (founding_version 1.33.0) added three key ops that declare
    # occurrence_time_param DEFAULTED, so the live occurrence-time declarers grew by exactly
    # `key-bind`, `key-revoke`, `key-rotate`. Coverage GROWS, never shrinks: the three are added
    # to the pinned set, driven from `opdefs.live_definitions`, and a fourth undeclared declarer
    # still reds this row. A key op carries occurrence_time because a key decision made away from
    # the store must record the moment it was decided, which is exactly what the router encodes.
    FOUNDING_OCCURRENCE_TIME_ROUTERS = {"CREATE-RULE", "CREATE-OBLIGATION", "AMEND-BUDGET",
                                        "key-bind", "key-revoke", "key-rotate"}

    def test_the_founding_declares_the_routers_only_where_it_says_it_does(self):
        """[EP-25, DOCUMENTED FLIP; EP-27B, the second one.] This test read "nothing in the
        founding uses the routers yet" when EP-24B built them — capability first, law later,
        which is why it was worth asserting. EP-25 was the first "later": its custody ops declare
        the PROVENANCE router so the kernel-asserted uid at the mount's port lands in the
        envelope as recorded evidence (design/36 K6). EP-27B is the second, and it moves BOTH
        halves: five more ops declare provenance (its R-1), and the occurrence-time half stops
        being "nobody" because the distinction that makes it safe to declare now exists.

        Both halves are now enumerations, which is the stronger form of the same guard: it still
        fails when an op declares a router, unless the op is one a human wrote down. What the
        enumeration cannot see is WHICH FORM the declaration takes, so the row below adds the
        half that matters — no op may declare a router DEFAULTED unless it is one of the two the
        store mints for, and nothing that was required has quietly become defaulted."""
        for router, pinned in (("provenance_param", self.FOUNDING_PROVENANCE_ROUTERS),
                               ("occurrence_time_param",
                                self.FOUNDING_OCCURRENCE_TIME_ROUTERS)):
            declared = {name for name, d in opdefs.live_definitions(self.store).items()
                        if d.get(router)}
            self.assertEqual(declared, pinned, router)

    #: Which founding ops declare a router DEFAULTED, PINNED (EP-27B). Silence means required,
    #: so every op NOT named here still refuses when its declared parameter is absent — and this
    #: set is what a later round would have to change to weaken one.
    # [MAINT, §A57 population re-derivation, architect ruling `:2895`.] The three key ops the
    # COMPLETE-KEY-FAMILY move added declare occurrence_time_param DEFAULTED, so the live
    # defaulted-pair set grew by exactly (key-bind|key-revoke|key-rotate, occurrence_time_param).
    # Driven from `opdefs.live_definitions` + `router_param`; coverage GROWS, never shrinks, and
    # the exact-set equality is kept — a new op silently declaring a router DEFAULTED still reds.
    FOUNDING_DEFAULTED_ROUTERS = {
        ("AMEND-BUDGET", "occurrence_time_param"), ("CREATE-OBLIGATION", "occurrence_time_param"),
        ("CREATE-RULE", "occurrence_time_param"), ("FILE-CREATE", "provenance_param"),
        ("FILE-LINK", "provenance_param"), ("FILE-PERM", "provenance_param"),
        ("FILE-UNLINK", "provenance_param"), ("FILE-WRITE", "provenance_param"),
        ("key-bind", "occurrence_time_param"), ("key-revoke", "occurrence_time_param"),
        ("key-rotate", "occurrence_time_param"),
    }

    def test_no_founding_declaration_is_defaulted_except_where_it_says_it_is(self):
        """[EP-27B.] The enumeration above cannot tell a required declaration from a defaulted
        one, and that difference is the whole of what EP-27B added — so a router silently
        changing form would pass it. EP-22's three observer pins are the reason this row exists:
        the way "defaulted" becomes "does not matter" is one declaration at a time, by habit."""
        defaulted = set()
        for name, d in opdefs.live_definitions(self.store).items():
            for router in opdefs.MINTED_ROUTERS:
                param, when_absent = opdefs.router_param(d, router)
                if param is not None and when_absent == opdefs.DEFAULTED:
                    defaulted.add((name, router))
        self.assertEqual(defaulted, self.FOUNDING_DEFAULTED_ROUTERS)

    def test_the_store_and_the_index_agree_on_the_record(self):
        """The degenerate direction of the acceleration: with nothing but the founding, the
        index selects the founding's own law-and-grant records and no others."""
        index = self.store.governance_index()
        self.assertEqual([e["seq"] for e in index.all()],
                         [e["seq"] for e in self.store.events if is_governance_record(e)])
        self.assertTrue(any(e["action"] == "GRANT" for e in index.all()))

    def test_a_bare_store_with_no_founding_has_an_empty_subset_and_still_answers(self):
        bare = EventStore(os.path.join(self.dir, "bare.jsonl"))
        self.assertEqual(bare.governance_index().all(), [])
        self.assertIsNone(authority.mother_space(bare.governance_index()))
        self.assertEqual(authority.mother_space(bare.governance_index()),
                         authority.mother_space(bare))


if __name__ == "__main__":
    unittest.main()
