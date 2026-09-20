"""EP-24C — the class, not the instance: the acceptance battery.

Named before code in the EP file, landed here as regression tests.

  W1 — the projection extended to the three record kinds the per-act-path folds read
  T-SUBSET-DIFFERENTIAL        one implementation, two record sources, zero divergence over
                               every world the existing suite builds plus a generated
                               population, at head and at three as-of points. Plus the
                               structural row: NO SECOND IMPLEMENTATION of any of the three
                               folds exists — both sources reach the same function body.
  T-SUBSET-IS-DERIVED          kill the projection, replay from the record alone, identical
                               answers. A cache under P2 or it does not ship.
  T-SUBSET-COHERENT-OR-REFUSE  the mutation that matters for each fold's own record kind
                               recomputes or refuses; a deliberately stalled projection is
                               DETECTED, never silently served — and the column is shown able
                               to fail before the pass is trusted.
  T-NO-STORED-TABLE            no verdict, no answer, no fold output held anywhere on the
                               three new surfaces. Answered by CONTENTS, not by intent.

  W2 — the memoisation
  T-OP-DEFINITIONS-COMPUTED-ONCE  one computation per act where more than one consultation
                               happens, asserted by COUNTING computations, never by timing.
  T-MEMO-DIES-WITH-ITS-HEAD    a memo served across a change it depends on is the failure, and
                               that column is shown able to fail. [ALTITUDE CORRECTION, EP-28B
                               W3, 2026-07-30: this read "after ANY append the memo recomputes"
                               and drove it with records this file's own `noise` docstring says
                               cannot change what the folds answer. The law is about changes a
                               fold depends on; the trigger was written one notch wider, which
                               is charter §A26's class in its wide direction. Both halves are
                               pinned now — an append inside the subset recomputes, one outside
                               it does not.]

  W3 — the guard that closes the class (design/36 ADDENDUM C)
  T-PER-ACT-PATH-READS-SUBSETS  every fold the gate's per-act path calls reads through a
                               projection; nothing on that path reads the whole record except
                               the rows DECLARED below with their reasons.
  T-THE-GUARD-CAN-FAIL         a synthetic whole-record fold placed on the per-act path is
                               reported unaccounted for.
  T-NO-STALE-GUARD-ROWS        a declared row nothing calls any more fails, in both tables.

  W4 — the instrument
  T-SWEEP-EXCLUSIONS-DECLARED  the whole-suite differential's exclusions are declared with
                               reasons and guarded in both directions.

THE GUARD IS STRUCTURAL, NEVER A TIMING ASSERTION. That was the owner's phrasing at the
ruling and it is the whole design: a timing test looks like a guard, passes on a fast box,
fails on a loaded one, gets marked flaky and skipped — and the class is open again under a
green suite. Everything below observes CALL STRUCTURE.
"""

import collections
import os
import sys
import tempfile
import traceback
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ep24b_differential import (                                             # noqa: E402
    SWEEP_EXCLUDED, as_of_points, sweep_modules, view_differential,
)
from kernel.compose import build_full_kernel                                 # noqa: E402
from kernel.errors import OpError                                            # noqa: E402
from kernel.store import (                                                   # noqa: E402
    PROJECTIONS, EventStore, RecordProjection, StaleIndex,
)
from kernel.views import Views                                               # noqa: E402

MOTHER = "space:root"

# A definition-born op that is lawful to create, amend and retire — the op-lifecycle acts are
# what exercise the op-definition fold's own mutations.
DEF = {"law_cited": "M1-OBSERVATION", "description": "a probe op",
       "params": {"subject": "required"}, "object_param": "subject",
       "payload_from": ["subject"], "structural_params": ["subject"]}


class _World(unittest.TestCase):
    """A composed kernel in a disposable directory. The world stays OPEN — nothing here
    narrows anything outside these throwaway worlds."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"))

    def actor(self, name="ann"):
        """An ORDINARY actor with a real grant chain. The gate exempts the chain-end from the
        authority step, so an act taken as the owner never consults the fold at all — the
        measurement-method rule at the end of design/36 ADDENDUM C, applied to the tests that
        observe the path as well as to the numbers."""
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": name, "actor_class": "human"})
        self.gate.execute("GRANT", "owner", {"grant_id": f"g_{name}", "grantee": name,
                                             "actions": "*", "info": "*", "space": MOTHER})
        return name

    def populate(self):
        """Governance in every one of the three kinds, plus operational noise that cannot
        change what any of the three folds answers."""
        g = self.gate.execute
        g("CREATE-RULE", "owner", {"rule_id": "law:budget", "policy_key": "k", "value": 1})
        g("CREATE-RULE", "owner", {"rule_id": "law:second", "policy_key": "j", "value": 2})
        g("CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})
        g("CREATE-OP", "owner", {"name": "DOOMED-OP", "definition": DEF})
        g("RETIRE-OP", "owner", {"name": "DOOMED-OP"})
        floor = sorted(set(self.views.category_packs()["dual-audit-actions"]["levels"]) | {"PROBE-OP"})
        g("AMEND-PACK", "owner", {"name": "dual-audit-actions", "levels": floor})
        self.noise(40)

    def noise(self, n):
        """Non-governance growth: records that cannot change what the three folds answer."""
        for i in range(n):
            self.store._append({"actor": "SYSTEM", "action": "process-created",
                                "object": f"obs:{i}:{len(self.store.events)}",
                                "rule_cited": "M1-OBSERVATION", "payload": {"n": i}})

    def answers(self, views=None, as_of=None):
        """Every answer the three per-act-path folds can give, as one comparable value."""
        v = views if views is not None else self.views
        return {name: v.view_fold(name, as_of=as_of) for name in sorted(v.PER_ACT_FOLDS)}

    def reload(self):
        """A second kernel over the same record FILE: every derived structure starts empty and
        is rebuilt from the record alone."""
        d = tempfile.mkdtemp()
        store, gate, views, _, _ = build_full_kernel(self.path, os.path.join(d, "blobs"))
        return store, gate, views


# =============================================================================================
# T-SUBSET-DIFFERENTIAL — one implementation, two sources
# =============================================================================================

class TestSubsetDifferential(_World):
    def test_zero_divergence_over_a_generated_population_at_head_and_as_of(self):
        self.populate()
        compared, divergences = view_differential(self.views, as_of_points(self.store))
        self.assertEqual(divergences, [], f"the projection and the record disagree: {divergences}")
        self.assertGreaterEqual(compared, 12, "the comparator compared almost nothing")
        print(f"[EP-24C T-SUBSET-DIFFERENTIAL] generated world: {compared} view-fold answers "
              f"compared, {len(divergences)} divergent")

    def test_zero_divergence_after_every_mutation_kind(self):
        """Each fold's own record kind mutated in turn, comparing after every step — a subset
        that misses one mutation shows up here rather than at the next campaign."""
        actor = self.actor()
        steps = [
            ("a rule minted", lambda: self.gate.execute(
                "CREATE-RULE", "owner", {"rule_id": "law:x", "policy_key": "k", "value": 1})),
            ("the rule amended", lambda: self.gate.execute(
                "CREATE-RULE", "owner", {"rule_id": "law:x", "policy_key": "k", "value": 9})),
            ("an op created", lambda: self.gate.execute(
                "CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})),
            ("the op amended", lambda: self.gate.execute(
                "AMEND-OP", "owner", {"name": "PROBE-OP", "definition": dict(DEF, description="v2")})),
            ("the op retired", lambda: self.gate.execute("RETIRE-OP", "owner", {"name": "PROBE-OP"})),
            ("a pack amended", lambda: self.gate.execute(
                "AMEND-PACK", "owner", {"name": "actor-classes",
                                        "levels": ["human", "agentic", "system", "probe"]})),
            ("an ordinary act", lambda: self.gate.execute(
                "CREATE-INFO", actor, {"object": "info:1", "content": "x"})),
        ]
        total = 0
        for label, step in steps:
            step()
            compared, divergences = view_differential(self.views, as_of_points(self.store))
            total += compared
            self.assertEqual(divergences, [], f"after {label}: {divergences}")
        print(f"[EP-24C T-SUBSET-DIFFERENTIAL] mutation walk: {total} answers compared, 0 divergent")

    def test_no_second_implementation_of_any_of_the_three_folds_exists(self):
        """THE STRUCTURAL ROW. Both record sources must reach ONE function body, so the
        differential varies exactly one thing. Proven by replacing that body and observing
        that BOTH paths change: a second implementation would leave one of them standing."""
        for name in sorted(Views.PER_ACT_FOLDS):
            impl = f"_{name}"
            original = getattr(Views, impl)
            sentinel = {"the one implementation": name}
            try:
                setattr(Views, impl, lambda self, as_of=None, source=None, _s=sentinel: _s)
                for accelerated in (True, False):
                    self.assertIs(self.views.view_fold(name, accelerated=accelerated), sentinel,
                                  f"{name} has a second implementation on the "
                                  f"{'accelerated' if accelerated else 'unaccelerated'} path")
            finally:
                setattr(Views, impl, original)

    def test_one_projection_mechanism_not_four(self):
        """Derive, don't add: the four subsets share ONE implementation of currency,
        resolution and refusal, and vary exactly the predicate that selects. A subset with its
        own machinery would be four places to check the coherent-or-refuse property instead of
        one, and the reviewer would have to read all four to trust any."""
        for name, cls in sorted(PROJECTIONS.items()):
            self.assertTrue(issubclass(cls, RecordProjection), f"{name} has its own machinery")
            for method in ("all", "by_action", "refresh", "_resolve", "_prove_current"):
                self.assertIs(getattr(cls, method), getattr(RecordProjection, method),
                              f"{name} overrides {method} — that is a second implementation")

    def test_a_fold_outside_the_family_refuses_rather_than_defaulting(self):
        with self.assertRaises(ValueError):
            self.views.view_fold("no-such-fold")
        with self.assertRaises(StaleIndex):
            self.store.record_projection("no-such-projection")


# =============================================================================================
# T-SUBSET-IS-DERIVED — kill it, replay, identical
# =============================================================================================

class TestSubsetIsDerived(_World):
    def test_killing_every_projection_changes_no_answer(self):
        self.populate()
        before = self.answers()
        for name in PROJECTIONS:
            p = self.store.record_projection(name)
            self.assertTrue(p._seqs, f"the {name} projection selected nothing — it is not in use")
            p.kill()
            self.assertFalse(p._seqs)
        self.views._memo.clear()
        self.assertEqual(self.answers(), before)

    def test_replay_from_the_record_file_alone_reconstructs_every_answer(self):
        self.populate()
        before = self.answers()
        _, _, replayed = self.reload()
        self.assertEqual(self.answers(replayed), before)

    def test_the_projections_are_derived_at_every_as_of_point_too(self):
        self.populate()
        for as_of in as_of_points(self.store):
            before = self.answers(as_of=as_of)
            for name in PROJECTIONS:
                self.store.record_projection(name).kill()
            self.views._memo.clear()
            self.assertEqual(self.answers(as_of=as_of), before, f"asOf={as_of} moved")


# =============================================================================================
# T-SUBSET-COHERENT-OR-REFUSE — per fold, with the column proven able to fail
# =============================================================================================

class TestSubsetCoherentOrRefuse(_World):
    """Per fold: the mutation that matters for THAT fold's own record kind must recompute; a
    projection stalled behind the record must be DETECTED and must never be silently served."""

    # Per fold, the mutation that matters for THAT fold's own record kind, each row
    # (label, what must already exist, the one act that must move the answer). The
    # prerequisite is separate so a mutation can be run alone, in a world of its own, with
    # the projection frozen at the instant before it.
    _NOTHING = staticmethod(lambda t: None)
    _A_LIVE_OP = staticmethod(lambda t: t.gate.execute(
        "CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF}))

    MUTATIONS = {
        "op_definitions": (
            ("a CREATE-OP", _NOTHING, lambda t: t.gate.execute(
                "CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})),
            ("an AMEND-OP", _A_LIVE_OP, lambda t: t.gate.execute(
                "AMEND-OP", "owner", {"name": "PROBE-OP", "definition": dict(DEF, description="v2")})),
            ("a RETIRE-OP", _A_LIVE_OP, lambda t: t.gate.execute(
                "RETIRE-OP", "owner", {"name": "PROBE-OP"})),
        ),
        "active_rules": (
            ("a new rule", _NOTHING, lambda t: t.gate.execute(
                "CREATE-RULE", "owner", {"rule_id": "law:x", "policy_key": "k", "value": 1})),
            ("an amendment", lambda t: t.gate.execute(
                "CREATE-RULE", "owner", {"rule_id": "law:x", "policy_key": "k", "value": 1}),
             lambda t: t.gate.execute(
                "CREATE-RULE", "owner", {"rule_id": "law:x", "policy_key": "k", "value": 9})),
            # A RETIREMENT, IN THE ONE FORM THIS ESTATE HAS FOR A LAW. There is no retire verb
            # for a rule: rules and views retire by latest-wins SUPERSESSION (the campaign-1
            # mechanism, recorded in `views.metabolism`'s own note, which counts RETIRE-OP for
            # ops and nothing for rules). So the retirement of a law is a superseding record
            # that takes its content away — and RETIRE-OP is deliberately NOT used here,
            # because its record carries no `rule_id` and therefore is not a law record at all,
            # which is a fact about the record and not a gap in the subset. The EP names "a
            # retirement" for this fold; this is what one is.
            ("a retirement by supersession",
             lambda t: t.gate.execute(
                 "CREATE-RULE", "owner", {"rule_id": "law:doomed", "policy_key": "d", "value": 7}),
             lambda t: t.gate.execute(
                 "CREATE-RULE", "owner", {"rule_id": "law:doomed", "policy_key": "d",
                                          "value": None, "text": "retired by supersession"})),
        ),
        "category_packs": (
            ("a pack amendment", _NOTHING, lambda t: t.gate.execute(
                "AMEND-PACK", "owner", {"name": "actor-classes",
                                        "levels": ["human", "agentic", "system", "probe"]})),
        ),
    }

    def test_every_mutation_recomputes_the_fold_that_reads_it(self):
        for fold, mutations in sorted(self.MUTATIONS.items()):
            for label, prepare, mutate in mutations:
                with self.subTest(fold=fold, mutation=label):
                    self.setUp()
                    prepare(self)
                    before = self.views.view_fold(fold)
                    mutate(self)
                    self.assertNotEqual(self.views.view_fold(fold), before,
                                        f"{fold} did not move after {label}")

    def test_a_stalled_projection_answers_wrong_and_the_differential_detects_it(self):
        """THE COLUMN PROVEN ABLE TO FAIL, per fold. A projection frozen behind the record
        while CLAIMING to be current is exactly the failure the coherence check exists for; if
        it cannot be made to answer wrong, the passing case above proves nothing.

        The freeze is applied PER MUTATION, by putting back the selection the projection held
        before that one act and then stamping it current. Two reasons it is done one act at a
        time rather than once for the set: the live path catches up on its own during any act,
        so simply moving the stamp changes nothing; and a set of mutations can NET OUT — an op
        created and then retired leaves the live set exactly where it started, so a projection
        frozen across both would look right while having seen neither."""
        for fold, projection in sorted(Views.PER_ACT_FOLDS.items()):
            for label, prepare, mutate in self.MUTATIONS[fold]:
                with self.subTest(fold=fold, mutation=label):
                    self.setUp()
                    prepare(self)
                    p = self.store.record_projection(projection)
                    p.refresh()
                    stale_seqs, stale_by_action = list(p._seqs), dict(p._by_action)
                    mutate(self)
                    p._seqs, p._by_action = stale_seqs, stale_by_action
                    p._seen = len(self.store.events)      # the lie: current without ingesting
                    self.assertTrue(p.is_current(), "the stall is not claiming currency")
                    self.views._memo.clear()
                    self.assertNotEqual(self.views.view_fold(fold, accelerated=True),
                                        self.views.view_fold(fold, accelerated=False),
                                        f"the {fold} projection could not be made to answer "
                                        f"wrong after {label} — this control proves nothing")
                    _, divergences = view_differential(self.views)
                    self.assertTrue(divergences, "the differential did not detect the stall")

    def test_behind_the_record_it_recomputes_rather_than_serving(self):
        """Catching up is reading the definitive, not improvising: a projection that finds
        itself behind the record RECOMPUTES from the record before it answers, and the
        catch-up is counted so that the coherence check is observable rather than asserted."""
        for fold, projection in sorted(Views.PER_ACT_FOLDS.items()):
            for label, prepare, mutate in self.MUTATIONS[fold]:
                with self.subTest(fold=fold, mutation=label):
                    self.setUp()
                    prepare(self)
                    p = self.store.record_projection(projection)
                    p.refresh()
                    before_catchups = p.catchups
                    mutate(self)
                    self.views._memo.clear()
                    self.assertEqual(self.views.view_fold(fold, accelerated=True),
                                     self.views.view_fold(fold, accelerated=False))
                    self.assertGreater(p.catchups, before_catchups,
                                       "the projection served without proving it was current")

    def test_a_projection_that_cannot_reconcile_refuses_and_serves_nothing(self):
        self.populate()
        for name in sorted(PROJECTIONS):
            with self.subTest(projection=name):
                p = self.store.record_projection(name)
                p.refresh()
                p._seen = len(self.store.events) + 5      # ingested more than the record holds
                with self.assertRaises(StaleIndex):
                    p.all()
                p._seen = len(self.store.events)
                p._seqs = list(p._seqs) + [len(self.store.events) + 99]
                with self.assertRaises(StaleIndex):
                    p.all()

    def test_a_by_action_key_the_projection_was_not_built_for_refuses(self):
        """An empty list is a wrong answer wearing the costume of a right one. The three new
        projections declare NO indexed keys, because none of the three folds reads by action —
        so a fold that grows such a read announces itself instead of quietly reading nothing."""
        for name in sorted(Views.PER_ACT_FOLDS.values()):
            with self.subTest(projection=name):
                p = self.store.record_projection(name)
                self.assertEqual(PROJECTIONS[name]._INDEXED_ACTIONS, ())
                with self.assertRaises(StaleIndex):
                    p.by_action("CREATE-OP")


# =============================================================================================
# T-NO-STORED-TABLE — extended over the three new surfaces, answered by CONTENTS
# =============================================================================================

class TestNoStoredTableExtended(_World):
    def test_every_projection_holds_record_locations_and_nothing_else(self):
        self.populate()
        for name in sorted(PROJECTIONS):
            p = self.store.record_projection(name)
            p.refresh()
            for seq in p._seqs:
                self.assertIsInstance(seq, int)
            for action, seqs in p._by_action.items():
                self.assertIsInstance(action, str)
                for seq in seqs:
                    self.assertIsInstance(seq, int)

    def test_no_projection_exposes_a_verdict_bearing_method(self):
        """EP-24B pinned this surface for one projection; generalising the class is exactly
        the change that could widen it for all four, so the pin is re-asserted per projection.
        A structure whose only public methods select records has nowhere to hang an answer."""
        for name in sorted(PROJECTIONS):
            p = self.store.record_projection(name)
            public = {n for n in dir(p) if not n.startswith("_")}
            self.assertEqual(public, {"all", "by_action", "catchups", "is_current", "kill",
                                      "refresh"},
                             f"the {name} projection grew a surface beyond selecting records")

    def test_the_projection_source_holds_nothing_keyed_by_a_subject_of_power(self):
        """The tell the EP names, checked against the code that changed rather than against a
        promise: nothing on this surface is keyed by who is asking or by what they may do."""
        from kernel import store as store_mod
        with open(store_mod.__file__, encoding="utf-8") as f:
            src = f.read()
        block = src[src.index("class RecordProjection"):]
        for forbidden in ("account", "actor", "grantee", "verdict", "permission", "answer"):
            self.assertNotIn(f"[{forbidden}", block,
                             f"a projection keys by {forbidden} — that is a table, not a projection")

    #: One record per per-act-path fold that its OWN subset receives — written as the minimal
    #: thing each predicate selects on, so the row tests the invalidation and leaves the
    #: judgement of whether the record is well-formed where it belongs, inside the fold.
    SUBSET_RECORD = {
        "op_definitions": {"actor": "SYSTEM", "action": "CREATE-OP", "rule_cited": "CAP-IS-LAW",
                           "payload": {"kind": "op_definition", "name": "PROBE-INVALIDATION",
                                       "definition": {"law_cited": "CAP-IS-LAW"}}},
        "active_rules": {"actor": "SYSTEM", "action": "CREATE-RULE", "rule_cited": "ROOT-NEG-6",
                         "payload": {"rule_id": "probe:invalidation"}},
        "category_packs": {"actor": "SYSTEM", "action": "CREATE-INFO", "rule_cited": "BOOT-INT",
                           "payload": {"kind": "category_pack", "name": "probe-pack",
                                       "levels": ["a"]}},
    }

    def test_the_views_memo_holds_no_answer_across_a_head_change_it_depends_on(self):
        """DOCUMENTED FLIP (EP-28B W3, 2026-07-30) — the same altitude correction as
        T-MEMO-DIES-WITH-ITS-HEAD, and it is worth stating what is NOT weakened. The refused
        thing is a memo serving an answer the record contradicts. That is still refused, per
        fold, below. What is no longer asserted is that an append a fold CANNOT depend on
        invalidates it, which was never the law — it was the mechanism the law happened to be
        implemented with, and W3 replaces the mechanism.

        The stale-answer property is now checked where it can actually fail: for each fold, a
        record its own subset receives lands, and the fold must serve a different answer."""
        self.populate()
        served = {fold: getattr(self.views, fold)() for fold in sorted(Views.PER_ACT_FOLDS)}
        written = {k for k in self.views._memo}
        self.assertEqual({k.rsplit(":", 1)[0] for k in written} & set(Views.PER_ACT_FOLDS),
                         set(Views.PER_ACT_FOLDS),
                         "a per-act-path fold did not memoise under the current head")
        # an append NO fold depends on: every one of them keeps its answer (W3's own row)
        self.noise(1)
        for fold, before in served.items():
            self.assertIs(getattr(self.views, fold)(), before,
                          f"{fold} recomputed for an append outside its subset")
        # and an append each fold DOES depend on: that fold's answer is never served again
        for fold, before in served.items():
            self.store._append(dict(self.SUBSET_RECORD[fold]))
            self.assertIsNot(getattr(self.views, fold)(), before,
                             f"{fold} served the same object across a change to its own subset "
                             "— that is a stored answer with a timestamp, not a cache")


# =============================================================================================
# W2 — THE MEMOISATION
# =============================================================================================

class TestOpDefinitionsMemo(_World):
    def _counted(self):
        """Count COMPUTATIONS of the fold body and CONSULTATIONS of the public read."""
        counts = collections.Counter()
        o_impl, o_public = Views._op_definitions, Views.op_definitions

        def impl(self_, as_of=None, source=None):
            counts["computed"] += 1
            return o_impl(self_, as_of, source)

        def public(self_, as_of=None):
            counts["consulted"] += 1
            return o_public(self_, as_of)

        Views._op_definitions, Views.op_definitions = impl, public
        self.addCleanup(lambda: setattr(Views, "_op_definitions", o_impl))
        self.addCleanup(lambda: setattr(Views, "op_definitions", o_public))
        return counts

    def test_one_computation_per_act_where_several_consultations_happen(self):
        """T-OP-DEFINITIONS-COMPUTED-ONCE — asserted by COUNTING computations, never by
        timing. The test also asserts that more than one consultation happened, so it cannot
        pass by measuring an act that never consulted the fold twice."""
        # ARRANGE — this test owns its precondition. Production now attests at boot
        # (the COMPLETE-ATTEST-OP flip), a lawful governed act that runs through the gate,
        # consults op_definitions, and leaves the view memo WARM. Kill it here with the
        # estate's T-CACHE-KILL primitive (as test_ep22's T-REPLAY/T-CACHE-KILL does) so the
        # computation count below starts from the COLD memo this test has always assumed.
        self.views._memo.clear()
        counts = self._counted()
        self.gate.execute("CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})
        self.assertGreater(counts["consulted"], 1,
                           "this act consults the fold once — it cannot show a memo working")
        self.assertEqual(counts["computed"], 1,
                         f"the fold recomputed {counts['computed']} times inside one act")

    def test_an_amend_act_also_computes_once(self):
        self.gate.execute("CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})
        counts = self._counted()
        self.gate.execute("AMEND-OP", "owner",
                          {"name": "PROBE-OP", "definition": dict(DEF, description="v2")})
        self.assertGreater(counts["consulted"], 1)
        self.assertEqual(counts["computed"], 1)

    def test_the_memo_dies_with_a_head_change_it_depends_on(self):
        """T-MEMO-DIES-WITH-ITS-HEAD — DOCUMENTED FLIP (EP-28B W3, 2026-07-30), and the flip is
        an ALTITUDE correction rather than a weakening.

        As written, this row said "after ANY append the next read recomputes" and drove it with
        `noise`, whose own docstring in this file says those records "cannot change what the
        three folds answer". So the assertion and the fixture disagreed: the law is that a memo
        is never served across a change that COULD alter its answer, and the trigger filed for
        it was one notch WIDER — charter §A26's class, in the wide direction this time.

        Both halves are now pinned, and the second is W3's own acceptance row as a countable:
        an append this fold's subset receives recomputes it, and an append it cannot depend on
        does not."""
        # ARRANGE — this test owns its precondition. Production now attests at boot
        # (the COMPLETE-ATTEST-OP flip), a lawful governed act that runs through the gate,
        # consults op_definitions, and leaves the view memo WARM. Kill it here with the
        # estate's T-CACHE-KILL primitive (as test_ep22's T-REPLAY/T-CACHE-KILL does) so the
        # computation count below starts from the COLD memo this test has always assumed.
        self.views._memo.clear()
        counts = self._counted()
        self.views.op_definitions()
        self.views.op_definitions()
        self.assertEqual(counts["computed"], 1)
        self.noise(1)
        self.views.op_definitions()
        self.assertEqual(counts["computed"], 1,
                         "an append outside this fold's subset recomputed it — the invalidation "
                         "is wider than the law it enforces")
        self.gate.execute("CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})
        self.views.op_definitions()
        self.assertGreater(counts["computed"], 1, "the memo survived a change to its own subset")
        self.assertIn("PROBE-OP", self.views.op_definitions())

    def test_the_memo_serves_the_record_and_not_a_frozen_answer(self):
        before = self.views.op_definitions()
        self.gate.execute("CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})
        after = self.views.op_definitions()
        self.assertNotIn("PROBE-OP", before)
        self.assertIn("PROBE-OP", after)

    def test_that_column_can_fail_a_memo_pinned_to_a_dead_head_serves_a_stale_answer(self):
        """The control. Pin the generation so the memo CANNOT die with its head, and the fold
        serves an answer the record contradicts — which is the thing this design forbids and
        the reason the passing tests above mean something."""
        self.views.op_definitions()
        gen = self.views._memo_gen
        # `_bump` takes the committed record since EP-28B W3 (it consults the fold's own
        # predicate to decide which generations move), so the neutering signature follows it.
        self.views._bump = lambda e=None: None                # the memo now outlives its head
        self.gate.execute("CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})
        self.assertEqual(self.views._memo_gen, gen)
        self.assertNotIn("PROBE-OP", self.views.op_definitions())
        self.assertIn("PROBE-OP", self.views.view_fold("op_definitions"))

    def test_as_of_reads_are_never_memoised(self):
        counts = self._counted()
        head = len(self.store.events)
        self.views.op_definitions(as_of=head)
        self.views.op_definitions(as_of=head)
        self.assertEqual(counts["computed"], 2, "a historical view was served from the memo")


# =============================================================================================
# W3 — THE GUARD (design/36 ADDENDUM C). A DECLARED enumeration plus a two-directional check.
# =============================================================================================

# THE ACTS THAT DEFINE "THE PER-ACT PATH". Declared, because the enumeration below means
# nothing without the acts it was observed under: "the per-act path" is not one code path but
# the union of what the gate consults across the act shapes it serves. These were chosen by
# MEASURING which gate branches consult a fold and then covering every one of them — an
# ordinary act, a law act, the three op-lifecycle acts, a protected-vocabulary amendment, the
# four attenuation-family acts that write the power structure, an act refused for want of a
# chain, a grant naming an unfounded space, and an act in a world where root authority has
# moved. Each runs in its OWN disposable world, so no act's effect narrows the next one's.
REPRESENTATIVE_ACTS = (
    "an ordinary act", "a law act", "an op created", "an op amended", "an op retired",
    "a protected vocabulary amended", "a grant made", "a grant revoked", "a space founded",
    "a role founded", "a grant naming an unfounded space", "an act refused for want of a chain",
    "an ordinary act after a handover",
)

# THE FOLDS THE PER-ACT PATH CALLS, and the projection each reads through. The guard fails on
# a fold observed on the path that is not here (a new whole-record fold landing on the path)
# AND on a row here that nothing calls any more (a table outliving what it describes).
#
# Three members of the eleven-strong authority family are DELIBERATELY ABSENT — `reaches_space`,
# `roles` and `role_meaning`. They are read surfaces the gate never consults: the gate uses
# `reaches_space_structural`, and the role route is resolved INSIDE `authority.covers` off the
# record source it was handed, so it never reaches the dispatcher this guard observes. Listing
# them would be a stale row on day one, which is the failure the second direction exists to
# catch. They are accelerated all the same — EP-24B put the whole family through one projection.
PER_ACT_PATH_FOLDS = {
    # the three this EP moved (design/36 ADDENDUM C names them)
    "op_definitions": "op_definitions",
    "active_rules": "law",
    "category_packs": "category_packs",
    # the authority folds the gate consults, moved by EP-24B, all through one projection
    "mother_space": "authority",
    "spaces": "authority",
    "space_of": "authority",
    "space_reaches": "authority",
    "within_makers_reach": "authority",
    "grants": "authority",
    "power_view": "authority",
    "covers": "authority",
}

# Arguments for the authority folds, used only where a guard row has to be exercised directly.
AUTHORITY_FOLD_ARGS = {
    "space_of": ({"payload": {}},),
    "space_reaches": (MOTHER, MOTHER),
    "within_makers_reach": ("owner", {"grantee": "owner", "actions": "*", "info": "*",
                                      "space": MOTHER}),
    "power_view": ("owner",),
    "covers": ("owner", "CREATE-INFO", "law", MOTHER),
}

# WHOLE-RECORD READS STILL ON THE PER-ACT PATH, DECLARED WITH THEIR REASONS. Every row here is
# RAISED in this EP's log entry, not fixed: the owner scoped EP-24C to three folds and a memo,
# and a fourth is his word (the EP's own RAISED-BY-DESIGN item 1). The guard fails on any
# whole-record read NOT named here, and on any row here that is no longer reachable — so the
# class stays closed while these stay visible.
WHOLE_RECORD_ON_PATH_BY_DESIGN = {
    "views.current_successor":
        "Reached from `chain_end` on EVERY gated act, but only in a world where a HANDOVER has "
        "been recorded: `_chain_end` re-evaluates the successor fold as of each handover, and "
        "that fold walks the record. A fourth instance of ADDENDUM C's class, found by this "
        "guard at authoring time, measured in MEASUREMENTS entry 3 and RAISED rather than "
        "fixed. Under the founding (no handover) it is never reached at all.",
    "opdefs.live_definitions":
        "Reached on the op-lifecycle acts (CREATE-OP / AMEND-OP / RETIRE-OP) when the "
        "interpreter re-registers the definition-born surface. Governance-rate rather than "
        "operation-rate — it fires only on acts that CHANGE the operation surface — but it is "
        "a whole-record fold on a gated act's path and is named rather than omitted. "
        "`src/kernel/opdefs.py` is outside this EP's fence. RAISED.",
    "gate._constitution_guard":
        "The protected-vocabulary floor: on an amendment to a pack the constitution protects, "
        "the guard walks the record for the EARLIEST instance of that pack, which IS the "
        "floor, and stops at the first hit. Early-terminating and confined to that one act "
        "shape, but a whole-record read in the worst case. `src/kernel/gate.py` is outside "
        "this EP's fence — the EP says a guard needing that file is a finding about where the "
        "per-act path lives, and this is that finding, stated rather than acted on. RAISED.",
    # views.class_capabilities RETIRED (P8B-HARDENING delta 1, archi Resolution A :3735): THE FIX this
    # row named ("a memoised capabilities projection served like op_definitions") LANDED. The (class,
    # cell) pairing's capability read is now head-memoised on the category_packs subset generation and
    # reads THROUGH the category_packs projection (a subset), so it no longer walks the whole record. The
    # operation-rate walk this row disclosed no longer exists, so the row is retired (its reader is gone
    # from the observed raw reads). The read is served from the memo at the pre-write gate chokepoint, so
    # it is not an OBSERVED per-act fold either — but a regression to a raw store.all() walk would still
    # surface here as an undeclared whole-record read, so this guard still protects it.
}


class _Observer:
    """Runs one gated act with both fold families and every raw whole-record read
    instrumented, and reports what the path actually called. Call structure, never timing."""

    def __init__(self):
        self.folds = set()
        self.raw = collections.Counter()

    def __enter__(self):
        self._all, self._af, self._vf = (EventStore.all, Views.authority_fold, Views.view_fold)
        obs = self

        def traced_all(self_, as_of_seq=None):
            f = traceback.extract_stack()[-2]
            obs.raw[f"{os.path.basename(f.filename)[:-3]}.{f.name}"] += 1
            return obs._all(self_, as_of_seq)

        def traced_af(self_, name, *a, accelerated=True, as_of=None):
            obs.folds.add(name)
            return obs._af(self_, name, *a, accelerated=accelerated, as_of=as_of)

        def traced_vf(self_, name, accelerated=True, as_of=None):
            obs.folds.add(name)
            return obs._vf(self_, name, accelerated=accelerated, as_of=as_of)

        EventStore.all, Views.authority_fold, Views.view_fold = traced_all, traced_af, traced_vf
        return self

    def __exit__(self, *exc):
        EventStore.all, Views.authority_fold, Views.view_fold = self._all, self._af, self._vf
        return False


class TestThePerActPathGuard(_World):
    """The row that closes the class. Not three folds fixed — a rule that fails when the next
    whole-record fold lands on the gate's per-act path."""

    def _fresh(self, actor=True, live_op=False, handover=False, narrow=False):
        """A world of its own for one representative act."""
        self.setUp()
        name = self.actor() if actor else None
        if live_op:
            self.gate.execute("CREATE-OP", "owner", {"name": "LIVE-OP", "definition": DEF})
        if handover:
            import hashlib
            g = self.gate.execute
            g("CREATE-ACCOUNT", "owner", {"account_id": "sue", "actor_class": "human"})
            g("VERIFY-ACCOUNT", "owner", {"account": "sue", "method": "in-person",
                                          "evidence_hash": hashlib.sha256(b"seen").hexdigest()})
            g("DESIGNATE-SUCCESSOR", "owner", {"successor": "sue"})
            g("ACCEPT-SUCCESSION", "sue", {})
            g("HANDOVER", "owner", {})
        if narrow:
            # THE NARROWING HAPPENS ONLY INSIDE THIS DISPOSABLE WORLD (the owner's standing
            # word). It is needed because under the founding openness grant every act is
            # already covered, so the gate's refusal branch — the only place `power_view` is
            # consulted — is unreachable.
            self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "zoe", "actor_class": "human"})
            self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        return name

    def _acts(self):
        """label -> (build this act's world, take the one act). The world is built OUTSIDE the
        observation, so what the guard sees is one gated act and nothing else."""
        e = lambda *a, **k: self.gate.execute(*a, **k)                       # noqa: E731
        floor = lambda: sorted(                                              # noqa: E731
            set(self.views.category_packs()["dual-audit-actions"]["levels"]) | {"NEW-ACT"})
        return {
            "an ordinary act": (
                lambda: self._fresh(),
                lambda: e("CREATE-INFO", "ann", {"object": "i:1", "content": "x"})),
            "a law act": (
                lambda: self._fresh(),
                lambda: e("CREATE-RULE", "ann", {"rule_id": "law:probe", "policy_key": "k", "value": 3})),
            "an op created": (
                lambda: self._fresh(),
                lambda: e("CREATE-OP", "owner", {"name": "PROBE-OP", "definition": DEF})),
            "an op amended": (
                lambda: self._fresh(live_op=True),
                lambda: e("AMEND-OP", "owner",
                          {"name": "LIVE-OP", "definition": dict(DEF, description="v2")})),
            "an op retired": (
                lambda: self._fresh(live_op=True),
                lambda: e("RETIRE-OP", "owner", {"name": "LIVE-OP"})),
            "a protected vocabulary amended": (
                lambda: self._fresh(),
                lambda: e("AMEND-PACK", "owner", {"name": "dual-audit-actions", "levels": floor()})),
            "a grant made": (
                lambda: self._fresh(),
                lambda: e("GRANT", "ann", {"grant_id": "g2", "grantee": "ann",
                                           "actions": ["CREATE-INFO"], "info": "*", "space": MOTHER})),
            "a grant revoked": (
                lambda: self._fresh(),
                lambda: e("REVOKE", "ann", {"grant_id": "g_ann"})),
            "a space founded": (
                lambda: self._fresh(),
                lambda: e("CREATE-SPACE", "ann", {"name": "alpha", "parent": MOTHER})),
            "a role founded": (
                lambda: self._fresh(),
                lambda: e("CREATE-ROLE", "ann", {"name": "editor", "space": MOTHER})),
            "a grant naming an unfounded space": (
                lambda: self._fresh(),
                lambda: e("GRANT", "owner", {"grant_id": "g_orphan", "grantee": "owner",
                                             "actions": "*", "info": "*",
                                             "space": "space:never-founded"})),
            "an act refused for want of a chain": (
                lambda: self._fresh(narrow=True),
                lambda: e("CREATE-INFO", "zoe", {"object": "i:9", "content": "x"})),
            "an ordinary act after a handover": (
                lambda: self._fresh(handover=True),
                lambda: e("CREATE-INFO", "ann", {"object": "i:2", "content": "y"})),
        }

    def _observe_all(self):
        acts = self._acts()
        self.assertEqual(sorted(acts), sorted(REPRESENTATIVE_ACTS),
                         "the declared representative acts and the acts run have drifted apart")
        folds, raw = set(), collections.Counter()
        for label in REPRESENTATIVE_ACTS:
            build, act = acts[label]
            build()
            with _Observer() as obs:
                try:
                    act()
                except OpError:
                    pass                     # a refusal is a gated act's other lawful outcome
            folds |= obs.folds
            raw.update(obs.raw)
        return folds, raw

    def test_every_fold_on_the_per_act_path_reads_through_a_projection(self):
        """T-PER-ACT-PATH-READS-SUBSETS."""
        folds, raw = self._observe_all()
        undeclared = sorted(f for f in folds if f not in PER_ACT_PATH_FOLDS)
        self.assertEqual(undeclared, [],
                         "a fold on the gate's per-act path is not in the declared enumeration — "
                         "give it a projection and a row, or the class is open again: "
                         f"{undeclared}")
        for fold in sorted(folds):
            projection = PER_ACT_PATH_FOLDS[fold]
            self.assertIn(projection, PROJECTIONS,
                          f"{fold} is declared against a projection that does not exist")

    def test_nothing_on_the_per_act_path_reads_the_whole_record_undeclared(self):
        _, raw = self._observe_all()
        unaccounted = {who: n for who, n in raw.items()
                       if who not in WHOLE_RECORD_ON_PATH_BY_DESIGN}
        self.assertEqual(unaccounted, {},
                         "a whole-record read happened on the gate's per-act path that is "
                         "neither served by a projection nor declared with its reason: "
                         f"{unaccounted}")

    def test_the_guard_can_fail(self):
        """T-THE-GUARD-CAN-FAIL. A synthetic whole-record fold placed on the per-act path is
        reported unaccounted for. Without this the passing rows above prove only that the
        observation found nothing, which is not the same as there being nothing to find."""
        original = Views.halted_watchers

        def whole_record_fold(self_, as_of=None):
            len(self_.store.all(as_of))                    # a new fold reading the whole record
            return original(self_, as_of)

        Views.halted_watchers = whole_record_fold
        try:
            _, raw = self._observe_all()
        finally:
            Views.halted_watchers = original
        unaccounted = {who for who in raw if who not in WHOLE_RECORD_ON_PATH_BY_DESIGN}
        self.assertIn("test_ep24c.whole_record_fold", unaccounted,
                      "the guard did not report a whole-record fold planted on the per-act path")

    def test_no_stale_guard_rows(self):
        """T-NO-STALE-GUARD-ROWS. A declared row nothing calls any more fails, in BOTH tables:
        a guard table that outlives what it describes is bookkeeping pretending to be
        coverage."""
        folds, raw = self._observe_all()
        self.assertEqual(sorted(f for f in PER_ACT_PATH_FOLDS if f not in folds), [],
                         "a declared per-act-path fold was not called by any representative act")
        self.assertEqual(sorted(w for w in WHOLE_RECORD_ON_PATH_BY_DESIGN if w not in raw), [],
                         "a declared whole-record reader is no longer reachable — retire the row")

    def test_the_declared_projections_are_the_ones_actually_read(self):
        """The enumeration must not merely NAME a projection: each fold must actually read
        through the one it is declared against. Proven per fold by killing that projection and
        observing that the fold forces it to catch up — a fold reading somewhere else would
        leave the catch-up counter still."""
        self.populate()
        for fold, projection in sorted(PER_ACT_PATH_FOLDS.items()):
            with self.subTest(fold=fold):
                p = self.store.record_projection(projection)
                p.refresh()
                p.kill()
                before = p.catchups
                self.views._memo.clear()
                if fold in Views.PER_ACT_FOLDS:
                    self.views.view_fold(fold)
                else:
                    self.views.authority_fold(fold, *AUTHORITY_FOLD_ARGS.get(fold, ()))
                self.assertGreater(p.catchups, before,
                                   f"{fold} is declared against the {projection} projection but "
                                   "does not read through it")


# =============================================================================================
# W4 — THE INSTRUMENT: the sweep's exclusions declared and guarded, both directions
# =============================================================================================

class TestSweepExclusionsDeclared(unittest.TestCase):
    """The directed item from the EP-24B verdict, landed where the harness lives. An
    undeclared exclusion list silently changes what the divergence count means the next time a
    can-fail control is added somewhere else."""

    def _test_files(self):
        here = os.path.dirname(os.path.abspath(__file__))
        return {f for f in os.listdir(here) if f.startswith("test_") and f.endswith(".py")}

    def test_every_excluded_file_exists_and_carries_a_reason(self):
        for name, reason in SWEEP_EXCLUDED.items():
            self.assertIn(name, self._test_files(), f"{name} is excluded but does not exist")
            self.assertGreater(len(reason), 80, f"{name} is excluded without a real reason")

    def test_the_sweep_skips_exactly_the_declared_set_and_nothing_else(self):
        swept = {f"{m}.py" for m in sweep_modules()}
        self.assertEqual(self._test_files() - swept, set(SWEEP_EXCLUDED),
                         "the sweep skips a file the declaration does not name, or names one "
                         "it does not skip")

    def test_this_file_is_excluded_because_it_sabotages_the_instrument(self):
        # named explicitly, so a future edit cannot drop the row quietly
        self.assertIn("test_ep24c.py", SWEEP_EXCLUDED)
        self.assertIn("test_ep24b.py", SWEEP_EXCLUDED)


if __name__ == "__main__":
    unittest.main()
