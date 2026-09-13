"""EP-26 — the two times of authority, the session registry, and the reconciliation sweep.

Every probe here is a regression test (the campaign method: a verification probe lands as a
test). The law: a decision binds from its DECIDING moment, not from its arrival. Arrival order
never adjudicates. The store's acceptance is a legitimacy-transfer test — law as of the
deciding time, authority live at effect time, two verdicts never merged.

THE REFERENCE THIS BATTERY EXISTS TO REFUSE is arrival-order adjudication: last-writer-wins,
commit-timestamp semantics, or a compensation framework that reconciles by editing state. The
rows below are written so that taking any of them fails something: an arrival-ordered engine
fails T-TWO-TIMES-ACCEPT half (b), a uniformly-as-of-d engine fails T-LAW-AUTHORITY-SPLIT, and
an editing reconciler fails the asOf half of T-OVERTURN-SWEEP.

Coverage (the EP's named battery, its ADDENDUM 2 additions, and ADDENDUM 3's five rows):
  T-TWO-TIMES-ACCEPT           both halves of the owner's worked example, mechanized.
  T-LAW-AUTHORITY-SPLIT        a revoked chain refuses at the door on an old-decided act while
                               the same act under an intact chain stands against newer law.
  T-SEAL-BOUND                 a claimed deciding time predating its own pack-hash world refuses.
  T-OVERTURN-SWEEP             late law -> appended overturns -> views reconcile forward; asOf
                               before the sweep still shows the overturned effect.
  T-OVERTURN-SWEEP-REPLAY      kill everything derived, replay: the identical overturn sequence.
  T-OVERTURN-REACH             the §4b matrix, seven rows.
  T-OVERTURN-NON-MONOTONE      (ADDENDUM A.2) a refusal that would now permit appends nothing and
                               surfaces on RE-ASK; the round-one overturn stands unchanged.
  T-OVERTURN-ANCHOR            an overturn that would orphan root refuses, cited, routed.
  T-OVERTURN-ANCHOR-TRANSITIVE (ADDENDUM 2) a mid-chain grant whose exclusion leaves a sub-chain
                               with nothing above it; the guard sees it.
  T-ANCHOR-GUARD-IS-COMPUTED   (ADDENDUM 3) the trigger reads no act kind.
  T-ORPHAN-BY-ACCUMULATION-REFUSES  (ADDENDUM 3) a chain ended by ordinary overturns only.
  T-NON-ORPHANING-ANCHOR-ACT-PASSES (ADDENDUM 3) the deliberate over-refusal removal.
  T-REFUSED-SWEEP-APPENDS-NOTHING   (ADDENDUM 3) a refused sweep leaves the record unchanged.
  T-EXTENDED-LEDGER-PROOF      (ADDENDUM 3) strictly-stronger-or-equal on the whole extended set.
  T-SWEEPS-SERIALIZE           (ADDENDUM A.5) a mid-sweep law arrival lands after the empty round.
  T-DECIDING-TIME-PRECISION    (ADDENDUM A.1) the precision is stated and the tie is covered.
  T-DEGENERATE-IDENTITY        the whole pre-existing suite is the old-ledger side; here, the
                               structural half — the fast path takes the live fold unchanged.
  T-SESSION-REGISTRY           open/close recorded; the registry answers live sessions.
  T-TOTAL-ROUNDTRIP-2 extended sessions, sweep products and both views all reconstruct.
  BOTH DIRECTIONS              too-weak (a d<r case adjudicated by arrival) and too-wedged (a
                               d=r case whose behaviour moves) are explicit on every flip.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel import reconcile  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.views import Views  # noqa: E402

OWNER = "owner"


def T(h, m, s=0, us=0):
    return f"2026-07-27T{h:02d}:{m:02d}:{s:02d}.{us:06d}+00:00"


class _World(unittest.TestCase):
    """A full kernel, plus the two ops this battery needs able to carry a DECIDING TIME.

    THE ROUTE IS THE ENGINE'S OWN AND IT IS A RECORDED ACT. `occurrence_time_param` is the
    envelope router EP-24B landed: an op DECLARES which parameter supplies the envelope's
    occurrence_time. The founding's CREATE-RULE and GRANT do not declare it, so this world
    AMENDS them — through AMEND-OP, in a disposable test world, tier conserved, the amendment
    itself a record. Nothing here is a back door: the amended op is an ordinary definition-born
    op and every act below crosses the ordinary gate.

    THE PRODUCTION GAP THIS EXPOSES IS RAISED, NOT PAPERED OVER. In the SHIPPED founding no op
    can submit a law with a deciding time earlier than its arrival, because the router refuses
    when a declared parameter is absent — so declaring it on CREATE-RULE would make every
    existing caller nonconforming. The sweep is therefore correct, tested and unreachable
    through the founding surface until an optional form of the declaration exists, and that
    file is not in this EP's fence. See the log's RAISED FOR REVIEW."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        self.founding_end = self.views.founding_prefix_end()

    def timed(self, name, param="at", carry=()):
        """Amend a live op so one of its parameters supplies the deciding time, and optionally
        so it can carry extra payload fields. CREATE-RULE needs `scope` carried: a law's binding
        scope is read from its payload and the founding definition does not copy it there, so a
        space-local law cannot be written through the shipped op. Filed as a raise; carried here
        so the scope row of T-OVERTURN-REACH can be written at all."""
        live = self.views.op_definitions()[name]
        d = json.loads(json.dumps(live["definition"], default=dict))
        d["params"] = dict(d.get("params") or {}, **{param: "required"})
        d["occurrence_time_param"] = param
        for field in carry:
            d["params"][field] = "optional"
            d["payload_from"] = list(d.get("payload_from") or []) + [field]
        # VOCABULARY DOOR (design/46 member 2): AMEND-OP re-runs field classification, so the new
        # router param and any carried field must be classified. timed() only ever amends
        # CREATE-RULE and GRANT, both fully-STRUCTURAL in the production census (structural_params
        # == all params, no content_params). The added `param` is an occurrence-time field and any
        # carry (`scope`) is a law-binding-scope field — both structural, mirroring the census's
        # `occurrence_time` and `scope`. So every param is affirmed structural, deduped against the
        # live structural_params this amendment inherits — a census mirror, never a blanket.
        d["structural_params"] = list(dict.fromkeys(
            list(d.get("structural_params") or []) + [param] + list(carry)))
        self.gate.execute("AMEND-OP", OWNER, {"name": name, "tier": live.get("tier"),
                                              "definition": d})

    def spender(self, name="SPEND"):
        """An ordinary act op that carries its own deciding time."""
        self.gate.execute("CREATE-OP", OWNER, {"name": name, "definition": {
            "description": "an act decided away from the store and arriving later",
            "params": {"line": "required", "amount": "optional", "at": "required"},
            # `line` is the spend-line id read inline by object_derive ("spend:{line}"); `amount` is
            # a small numeric scalar (census: `size`/`ceiling`); `at` is the deciding-time field
            # (census: `occurrence_time`). None carries reachable content — all STRUCTURAL
            # (vocabulary door, design/46 member 2). The object field cannot be content-homed.
            "structural_params": ["line", "amount", "at"],
            "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "spend:{line}"},
            "occurrence_time_param": "at", "payload_from": ["line", "amount"]}})
        return name

    def law(self, rule_id, at, when, actor=OWNER, **extra):
        return self.gate.execute("CREATE-RULE", actor, dict(
            {"rule_id": rule_id, "at": at, "polarity": "-", "text": f"{rule_id} refuses",
             "when": when, "then": [{"refuse": rule_id}]}, **extra))

    def narrow(self):
        """Retire the founding openness grant. Every authority leash in this estate is INERT
        under openness, so both directions are only observable in a narrowed world — the
        campaign-2 extinction-matrix discipline, applied here."""
        self.gate.execute("REVOKE", OWNER, {"grant_id": "founding-openness"})

    def sweep(self):
        return self.gate.sweeps[-1]

    def refusals(self, rule=None):
        return [e for e in self.store.by_action("op-refused")
                if rule is None or e["rule_cited"] == rule]

    def overturned(self):
        return sorted(reconcile.overturned_targets(self.store))


# ============================================================================================
# T-TWO-TIMES-ACCEPT — the owner's worked example, mechanized. BOTH halves.
#
# Half (a) is the sweep's: a rule decided at 9:00 arriving at 10:00 overturns acts decided at
# 9:30. Half (b) is the door's: acts decided at 9:00 arriving at 10:00 STAND against a rule
# decided at 9:15 that arrived at 9:30. Half (b) is the row an arrival-ordered engine fails,
# and it is the whole content of the owner's ruling.
# ============================================================================================

class TestTwoTimesAccept(_World):

    def test_a_rule_decided_earlier_overturns_acts_decided_after_it(self):
        self.timed("CREATE-RULE")
        self.spender()
        act = self.gate.execute("SPEND", OWNER, {"line": "ops", "at": T(9, 30)})
        rule = self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertEqual(self.overturned(), [act["seq"]])
        o = self.views.overturns()[0]
        self.assertEqual(o["reaching_seq"], rule["seq"])
        self.assertEqual(o["target_deciding_time"], T(9, 30))
        self.assertEqual(o["reaching_deciding_time"], T(9, 0))

    def test_b_acts_decided_before_the_rule_stand_however_late_they_arrive(self):
        # THE ROW AN ARRIVAL-ORDERED ENGINE FAILS. The rule arrives FIRST and is already the
        # live law; the act arrives after it and is nonetheless accepted, because it was
        # decided before the rule's own deciding moment.
        self.timed("CREATE-RULE")
        self.spender()
        self.law("NO-SPEND", T(9, 15), [{"action": "SPEND"}])
        stands = self.gate.execute("SPEND", OWNER, {"line": "early", "at": T(9, 0)})
        self.assertTrue(self.views.standing(stands["seq"]))
        self.assertEqual(self.refusals("NO-SPEND"), [])

    def test_b_the_other_direction_an_act_decided_after_the_rule_refuses_at_the_door(self):
        # TOO-WEAK direction: if the acceptance step did nothing, this would be accepted too.
        self.timed("CREATE-RULE")
        self.spender()
        self.law("NO-SPEND", T(9, 15), [{"action": "SPEND"}])
        with self.assertRaises(OpError) as cm:
            self.gate.execute("SPEND", OWNER, {"line": "late", "at": T(9, 30)})
        self.assertEqual(cm.exception.rule, "NO-SPEND")
        self.assertEqual(len(self.refusals("NO-SPEND")), 1)

    def test_a_synchronous_act_is_still_judged_by_the_live_law(self):
        # TOO-WEDGED direction at the door: the degenerate case must not gain an escape hatch.
        # An act with no distinct deciding time is judged by the law in force NOW, exactly as
        # before this EP.
        self.timed("CREATE-RULE")
        self.gate.execute("CREATE-OP", OWNER, {"name": "PLAIN", "definition": {
            "description": "an ordinary synchronous act", "params": {"line": "required"},
            # `line` is the id read inline by object_derive ("plain:{line}") — STRUCTURAL
            # (vocabulary door, design/46 member 2); an object field cannot be content-homed.
            "structural_params": ["line"],
            "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "plain:{line}"},
            "payload_from": ["line"]}})
        self.law("NO-PLAIN", T(9, 15), [{"action": "PLAIN"}])
        with self.assertRaises(OpError) as cm:
            self.gate.execute("PLAIN", OWNER, {"line": "x"})
        self.assertEqual(cm.exception.rule, "NO-PLAIN")


# ============================================================================================
# T-DECIDING-TIME-PRECISION (design/36 ADDENDUM A.1, second half)
#
# The EP is required to STATE the precision it carries the deciding time at and to cover the
# equal-value case at that precision. A.1 also set a STOP condition: if the precision makes
# ties common rather than rare, that is a raise, not a decision. It does not — the field is
# minted at microsecond resolution — so the strict comparison exempts a corner, not a
# population, and that is measured here rather than asserted.
# ============================================================================================

class TestDecidingTimePrecision(_World):

    def test_the_engine_mints_microsecond_resolution(self):
        self.assertEqual(reconcile.DECIDING_TIME_PRECISION, "ISO-8601 UTC, microsecond")
        rec = self.gate.execute("CREATE-INFO", OWNER, {"content": "x"})
        stamp = rec["occurrence_time"]
        self.assertRegex(stamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$")

    def test_ties_are_a_corner_and_not_a_population(self):
        # A hundred consecutive gated acts; if the mint's resolution made ties common, this
        # would collide. It is the measurement A.1 asked for before proceeding.
        stamps = [self.gate.execute("CREATE-INFO", OWNER, {"content": f"n{i}"})["occurrence_time"]
                  for i in range(100)]
        self.assertEqual(len(set(stamps)), 100)

    def test_the_tie_stands_the_act_at_both_doors(self):
        # ONE RULE, APPLIED TWICE. An act decided at exactly the law's deciding moment stands —
        # at the ordinary door AND in the sweep. If the two comparisons could disagree, the
        # same pair of facts would resolve two ways depending on arrival order, which is the
        # one thing the owner's ruling forbids.
        self.timed("CREATE-RULE")
        self.spender()
        at = T(9, 15, 0, 123456)
        before_law = self.gate.execute("SPEND", OWNER, {"line": "tie-swept", "at": at})
        self.law("NO-SPEND", at, [{"action": "SPEND"}])
        self.assertEqual(self.overturned(), [])                       # the sweep passed over it
        after_law = self.gate.execute("SPEND", OWNER, {"line": "tie-door", "at": at})
        self.assertTrue(self.views.standing(before_law["seq"]))       # and the door admitted it
        self.assertTrue(self.views.standing(after_law["seq"]))

    def test_one_microsecond_later_is_reached_at_both_doors(self):
        self.timed("CREATE-RULE")
        self.spender()
        at = T(9, 15, 0, 123456)
        swept = self.gate.execute("SPEND", OWNER, {"line": "us-swept", "at": T(9, 15, 0, 123457)})
        self.law("NO-SPEND", at, [{"action": "SPEND"}])
        self.assertEqual(self.overturned(), [swept["seq"]])
        with self.assertRaises(OpError):
            self.gate.execute("SPEND", OWNER, {"line": "us-door", "at": T(9, 15, 0, 123457)})

    def test_a_deciding_time_in_another_offset_compares_as_the_same_instant(self):
        # A lexicographic string compare would put 10:00+01:00 after 09:15+00:00 and admit an
        # act the law reaches. Normalisation is what makes the comparison a comparison of
        # MOMENTS rather than of spellings.
        self.timed("CREATE-RULE")
        self.spender()
        self.law("NO-SPEND", "2026-07-27T09:15:00+00:00", [{"action": "SPEND"}])
        with self.assertRaises(OpError):
            self.gate.execute("SPEND", OWNER, {"line": "offset", "at": "2026-07-27T11:30:00+02:00"})


# ============================================================================================
# T-LAW-AUTHORITY-SPLIT — the split IS the design (design/34 §2 generalized).
#
# LAW as of the deciding time; AUTHORITY live at effect time. Two cases, two distinct records.
# An engine that implemented either half uniformly fails one of these two tests, which is why
# both are here rather than one.
# ============================================================================================

class TestLawAuthoritySplit(_World):

    def setUp(self):
        super().setUp()
        self.timed("CREATE-RULE")
        self.timed("GRANT")
        self.spender()
        self.gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": "alice", "actor_class": "human"})
        self.mother = self.views.mother_space()
        self.gate.execute("GRANT", OWNER, {"grant_id": "alice-all", "grantee": "alice",
                                           "actions": "*", "info": "*",
                                           "space": self.mother, "at": T(7, 0)})
        self.narrow()

    def test_an_intact_chain_stands_against_newer_law(self):
        self.law("NO-SPEND", T(9, 15), [{"action": "SPEND"}])
        rec = self.gate.execute("SPEND", "alice", {"line": "ok", "at": T(9, 0)})
        self.assertTrue(self.views.standing(rec["seq"]))

    def test_a_revoked_chain_refuses_at_the_door_on_the_very_same_act(self):
        # AUTHORITY IS LIVE. The deciding time is impeccable and older than the law; the chain
        # is gone at effect time, so the act refuses — and it refuses on AUTHORITY, never
        # relabelled as a law verdict. Two verdicts, two records, never merged.
        self.law("NO-SPEND", T(9, 15), [{"action": "SPEND"}])
        self.gate.execute("REVOKE", OWNER, {"grant_id": "alice-all"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("SPEND", "alice", {"line": "revoked", "at": T(9, 0)})
        self.assertIn(cm.exception.rule, ("ROOT-NEG-1", "ROOT-NEG-3"))
        self.assertEqual(self.refusals("NO-SPEND"), [])

    def test_authority_is_not_rewound_to_the_deciding_time(self):
        # The uniformly-as-of-d error, caught explicitly: if authority were evaluated as of the
        # deciding time, this act would pass on a chain that existed at 9:00 and is gone now.
        self.gate.execute("REVOKE", OWNER, {"grant_id": "alice-all"})
        with self.assertRaises(OpError):
            self.gate.execute("SPEND", "alice", {"line": "stale-power", "at": T(9, 0)})


# ============================================================================================
# T-SEAL-BOUND (design/35 §6) — a claimed deciding time cannot predate the world its seal pins.
# ============================================================================================

STATION = {
    "description": "ask an external reviewer", "params": {"line": "required"},
    # `line` is the id read inline by object_derive ("review:{line}") and written to the payload —
    # STRUCTURAL (vocabulary door, design/46 member 2); an object field cannot be content-homed.
    "structural_params": ["line"],
    "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "review:{line}"},
    "payload_from": ["line"], "executor": "external",
    "crossing": {"input_view": "view:budget-context", "template": "review@1",
                 "answerer_identity": "reviewer@1", "parser": "plain@1"},
}


class TestSealBound(_World):

    def setUp(self):
        super().setUp()
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "budget-context",
                                                 "when": {"object": "budget:ops"}})
        self.gate.execute("CREATE-OP", OWNER, {"name": "SET-BUDGET", "definition": {
            "description": "set a budget line", "params": {"name": "required", "amount": "required"},
            # `name` is the budget-line id read inline by object_derive ("budget:{name}"); `amount`
            # is a small numeric scalar (census: `size`/`ceiling`). Both STRUCTURAL (vocabulary
            # door, design/46 member 2); the object field cannot be content-homed.
            "structural_params": ["name", "amount"],
            "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "budget:{name}"},
            "payload_from": ["name", "amount"]}})
        self.gate.execute("CREATE-OP", OWNER, {"name": "ASK-REVIEW", "definition": STATION})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 5})

    def test_a_seal_over_a_world_that_existed_admits_the_claim(self):
        handout = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        p = dict(handout["payload"])
        ok, reason = reconcile.seal_bound(self.store, self.views, {
            "payload": {"seal": p["seal"], "input_view": p["input_view"]},
            "occurrence_time": handout["record_time"]})
        self.assertTrue(ok, reason)

    def test_a_deciding_time_predating_the_sealed_world_refuses_cited(self):
        handout = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        p = dict(handout["payload"])
        claim = {"payload": {"seal": p["seal"], "input_view": p["input_view"]},
                 "occurrence_time": T(1, 0)}
        ok, reason = reconcile.seal_bound(self.store, self.views, claim)
        self.assertFalse(ok)
        self.assertIn("had not yet come into being", reason)

    def test_the_bound_refuses_at_the_gate_citing_its_own_rule(self):
        # The refusal cites the SEAL-BOUND rule and not the staleness rule: staleness asks
        # whether the judged world is still the world, this asks whether the claimed moment
        # could have seen that world at all.
        handout = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        p = dict(handout["payload"])
        self.gate.execute("CREATE-OP", OWNER, {"name": "CLAIM", "definition": {
            "description": "a decision claiming a sealed world and a deciding time",
            "params": {"seal": "required", "input_view": "required", "at": "required"},
            # `seal` is a sha256 fingerprint reference (a hash, not the world it pins — census:
            # `evidence_hash`/`secret_hash`); `input_view` is a versioned view ref string; `at` is
            # the deciding time read inline by object_derive ("claim:{at}"). All are structural
            # references carrying no reachable content — STRUCTURAL (vocabulary door, design/46
            # member 2); the object field cannot be content-homed.
            "structural_params": ["seal", "input_view", "at"],
            "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "claim:{at}"},
            "occurrence_time_param": "at", "payload_from": ["seal", "input_view"]}})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CLAIM", OWNER, {"seal": p["seal"], "input_view": p["input_view"],
                                               "at": T(1, 0)})
        self.assertEqual(cm.exception.rule, reconcile.SEAL_BOUND_RULE)
        self.assertEqual(len(self.refusals(reconcile.SEAL_BOUND_RULE)), 1)

    def test_a_truthful_claim_over_the_same_seal_passes(self):
        # THE OTHER DIRECTION. A too-wedged bound would refuse an honest late arrival too.
        handout = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        p = dict(handout["payload"])
        self.gate.execute("CREATE-OP", OWNER, {"name": "CLAIM", "definition": {
            "description": "a decision claiming a sealed world and a deciding time",
            "params": {"seal": "required", "input_view": "required", "at": "required"},
            # `seal` is a sha256 fingerprint reference (a hash, not the world it pins — census:
            # `evidence_hash`/`secret_hash`); `input_view` is a versioned view ref string; `at` is
            # the deciding time read inline by object_derive ("claim:{at}"). All are structural
            # references carrying no reachable content — STRUCTURAL (vocabulary door, design/46
            # member 2); the object field cannot be content-homed.
            "structural_params": ["seal", "input_view", "at"],
            "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "claim:{at}"},
            "occurrence_time_param": "at", "payload_from": ["seal", "input_view"]}})
        rec = self.gate.execute("CLAIM", OWNER, {"seal": p["seal"],
                                                 "input_view": p["input_view"],
                                                 "at": handout["record_time"]})
        self.assertEqual(self.refusals(reconcile.SEAL_BOUND_RULE), [])
        self.assertTrue(self.views.standing(rec["seq"]))

    def test_an_arrival_carrying_no_seal_is_unbounded_and_says_so(self):
        ok, reason = reconcile.seal_bound(self.store, self.views,
                                          {"payload": {}, "occurrence_time": T(1, 0)})
        self.assertTrue(ok)
        self.assertIsNone(reason)


# ============================================================================================
# T-OVERTURN-SWEEP / -REPLAY — appended overturns acting forward, never an edit.
# ============================================================================================

class TestOverturnSweep(_World):

    def setUp(self):
        super().setUp()
        self.timed("CREATE-RULE")
        self.spender()

    def test_the_record_is_not_edited_and_the_act_is_still_there(self):
        act = self.gate.execute("SPEND", OWNER, {"line": "ops", "at": T(9, 30)})
        before = json.dumps(dict(self.store.by_seq(act["seq"])), sort_keys=True, default=str)
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        after = json.dumps(dict(self.store.by_seq(act["seq"])), sort_keys=True, default=str)
        self.assertEqual(before, after)                      # not one byte of the act moved

    def test_the_overturn_is_an_appended_decision_citing_both_deciding_times(self):
        act = self.gate.execute("SPEND", OWNER, {"line": "ops", "at": T(9, 30)})
        rule = self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        o = [e for e in self.store.all() if dict(e.get("payload") or {}).get("kind") == "overturn"]
        self.assertEqual(len(o), 1)
        p = dict(o[0]["payload"])
        self.assertEqual(o[0]["actor"], "SYSTEM")
        self.assertEqual(o[0]["rule_cited"], reconcile.OVERTURN_RULE)
        self.assertEqual(p["target_seq"], act["seq"])
        self.assertEqual(p["reaching_seq"], rule["seq"])
        self.assertEqual(p["target_deciding_time"], T(9, 30))
        self.assertEqual(p["reaching_deciding_time"], T(9, 0))
        self.assertEqual(p["record_class"], "DECISION")

    def test_views_reconcile_forward_and_as_of_before_still_shows_the_effect(self):
        # THE ROW A COMPENSATION FRAMEWORK FAILS. Order is untouched; validity is what changed.
        act = self.gate.execute("SPEND", OWNER, {"line": "ops", "at": T(9, 30)})
        rule = self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertFalse(self.views.standing(act["seq"]))
        self.assertTrue(self.views.standing(act["seq"], as_of=rule["seq"]))

    def test_overturns_in_record_order(self):
        a = self.gate.execute("SPEND", OWNER, {"line": "a", "at": T(9, 30)})
        b = self.gate.execute("SPEND", OWNER, {"line": "b", "at": T(9, 40)})
        c = self.gate.execute("SPEND", OWNER, {"line": "c", "at": T(9, 50)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        got = [dict(e["payload"])["target_seq"] for e in self.store.all()
               if dict(e.get("payload") or {}).get("kind") == "overturn"]
        self.assertEqual(got, [a["seq"], b["seq"], c["seq"]])

    def test_replay_reconstructs_the_identical_overturn_sequence(self):
        # T-OVERTURN-SWEEP-REPLAY. Kill everything derived; rebuild from the record file alone.
        for line in ("a", "b"):
            self.gate.execute("SPEND", OWNER, {"line": line, "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        live = json.dumps(self.views.overturns(), sort_keys=True, default=str)
        standing = {e["seq"]: self.views.standing(e["seq"]) for e in self.store.all()}
        store2, gate2, views2, _, _ = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs2"), os.path.join(self.dir, "vault"))
        self.assertEqual(len(store2.events), len(self.store.events))
        self.assertEqual(json.dumps(views2.overturns(), sort_keys=True, default=str), live)
        self.assertEqual({e["seq"]: views2.standing(e["seq"]) for e in store2.all()}, standing)

    def test_the_sweep_does_not_chase_its_own_output(self):
        # ADDENDUM A.2's second consequence: the sweep's own overturns are d = r acts recorded
        # after r(L), so §4b.1's boundary puts them outside the candidate set. If the sweep
        # chased them, this would not terminate at two rounds.
        for line in ("a", "b", "c"):
            self.gate.execute("SPEND", OWNER, {"line": line, "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        s = self.sweep()
        self.assertEqual(len(s["committed"]), 3)
        self.assertLessEqual(s["rounds"], 1 + s["candidates"])
        self.assertEqual(self.views.overturns()[0]["basis"], "direct")


# ============================================================================================
# T-OVERTURN-REACH — the §4b matrix.
# ============================================================================================

class TestOverturnReach(_World):

    def setUp(self):
        super().setUp()
        self.timed("CREATE-RULE")
        self.spender()
        self.mother = self.views.mother_space()

    def test_an_act_outside_the_laws_scope_stands(self):
        self.timed("CREATE-RULE", carry=("scope",))
        self.gate.execute("CREATE-SPACE", OWNER, {"name": "alpha", "parent": self.mother})
        act = self.gate.execute("SPEND", OWNER, {"line": "outside", "at": T(9, 30)})
        self.law("LOCAL-BAN", T(9, 0), [{"action": "SPEND"}], scope="space:alpha")
        self.assertEqual(self.overturned(), [])              # the mother-space act is out of reach

    def test_an_inside_scope_act_the_trigger_does_not_match_stands(self):
        other = self.spender("TRANSFER")
        act = self.gate.execute(other, OWNER, {"line": "x", "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertEqual(self.overturned(), [])

    def test_a_matching_act_is_overturned(self):
        act = self.gate.execute("SPEND", OWNER, {"line": "x", "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertEqual(self.overturned(), [act["seq"]])

    def test_an_act_decided_at_the_same_moment_is_not_reached(self):
        act = self.gate.execute("SPEND", OWNER, {"line": "tie", "at": T(9, 0)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertEqual(self.overturned(), [])              # strictly after, never at

    def test_a_dependent_act_flips_in_round_two_and_cites_its_ancestor(self):
        # TRANSITIVE REACH, COMPUTED NOT STORED (§4b.5), and the citation names the ANCESTOR
        # rather than the law (ADDENDUM A.3): a round-two overturn is not reached by L directly,
        # so citing L would be a citation that does not carry its own refusal.
        self.timed("GRANT")
        self.gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": "alice", "actor_class": "human"})
        grant = self.gate.execute("GRANT", OWNER, {"grant_id": "alice-all", "grantee": "alice",
                                                   "actions": "*", "info": "*",
                                                   "space": self.mother, "at": T(9, 30)})
        self.narrow()
        dependent = self.gate.execute("SPEND", "alice", {"line": "under-grant", "at": T(9, 40)})
        law = self.law("NO-GRANT", T(9, 0), [{"action": "GRANT", "object": "grant:alice-all"}])
        self.assertEqual(self.overturned(), sorted([grant["seq"], dependent["seq"]]))
        by_target = {o["target_seq"]: o for o in self.views.overturns()}
        self.assertEqual(by_target[grant["seq"]]["reaching_seq"], law["seq"])
        self.assertEqual(by_target[grant["seq"]]["basis"], "direct")
        self.assertEqual(by_target[dependent["seq"]]["reaching_seq"], grant["seq"])
        self.assertEqual(by_target[dependent["seq"]]["basis"], "transitive")
        self.assertEqual(by_target[dependent["seq"]]["round"], 2)
        # the chain back to L is WALKABLE on the record rather than asserted
        self.assertEqual(by_target[by_target[dependent["seq"]]["reaching_seq"]]["reaching_seq"],
                         law["seq"])

    def test_nothing_is_stored_that_says_the_dependent_act_depended(self):
        # Dependence is RECOMPUTED. No record anywhere links the dependent act to its grant;
        # the only link is that re-running admission without the grant refuses.
        self.timed("GRANT")
        self.gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": "alice", "actor_class": "human"})
        grant = self.gate.execute("GRANT", OWNER, {"grant_id": "alice-all", "grantee": "alice",
                                                   "actions": "*", "info": "*",
                                                   "space": self.mother, "at": T(9, 30)})
        self.narrow()
        dependent = self.gate.execute("SPEND", "alice", {"line": "under-grant", "at": T(9, 40)})
        blob = json.dumps(dict(self.store.by_seq(dependent["seq"])), default=str)
        self.assertNotIn("alice-all", blob)


# ============================================================================================
# The refusal direction: RE-ASK, never a fabricated effect (§4b.4 RULED) — and the EXPOSURE
# view (§4b.6 RULED).
# ============================================================================================

class TestReAskAndExposure(_World):

    def setUp(self):
        super().setUp()
        self.timed("CREATE-RULE")
        self.timed("GRANT")
        self.spender()
        self.mother = self.views.mother_space()

    def _refused_then_lifted(self):
        """A refusal a LATE-ARRIVING PERMISSIVE law would now allow.

        The ban is decided at 9:00 and the act at 10:00, so the act refuses at the door — with
        its draft on the refusal record. A LIFT of the same rule is then decided at 9:30 and
        arrives afterwards. In the world as of the refused act's own deciding moment both are
        in force and the later-recorded lift wins, so the act WOULD now be admitted. Nothing is
        appended for it: an overturn cannot perform an act that never happened."""
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        with self.assertRaises(OpError):
            self.gate.execute("SPEND", OWNER, {"line": "denied", "at": T(10, 0)})
        refusal = self.refusals("NO-SPEND")[-1]
        self.gate.execute("CREATE-RULE", OWNER, {
            "rule_id": "NO-SPEND", "at": T(9, 30), "polarity": "+", "text": "the ban is lifted",
            "when": [{"action": "SPEND"}], "then": []})
        return refusal

    def test_a_refusal_records_the_draft_it_refused(self):
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        with self.assertRaises(OpError):
            self.gate.execute("SPEND", OWNER, {"line": "denied", "at": T(10, 0)})
        r = self.refusals("NO-SPEND")[-1]
        self.assertIn("draft", dict(r["payload"]))
        self.assertEqual(dict(dict(r["payload"])["draft"])["action"], "SPEND")

    def test_a_refusal_before_a_draft_exists_records_none_and_says_so(self):
        with self.assertRaises(OpError):
            self.gate.execute("NO-SUCH-OP", OWNER, {})
        self.assertNotIn("draft", dict(self.refusals("P3-CLOSURE")[-1]["payload"]))

    def test_no_overturn_is_ever_appended_for_a_refusal(self):
        # THE ONE FORBIDDEN LIE, refused: a record claiming an effect that did not occur.
        r = self._refused_then_lifted()
        for o in self.views.overturns():
            self.assertNotEqual(o["target_seq"], r["seq"])

    def test_the_case_surfaces_on_the_re_ask_view_recomputed(self):
        r = self._refused_then_lifted()
        cases = self.views.re_ask(self.gate)
        self.assertIn(r["seq"], [c["refusal_seq"] for c in cases])
        case = [c for c in cases if c["refusal_seq"] == r["seq"]][0]
        self.assertEqual(case["op"], "SPEND")
        self.assertEqual(case["actor"], OWNER)
        self.assertEqual(case["basis"], "re-evaluated")

    def test_a_refusal_the_new_law_does_not_reach_is_not_a_re_ask_case(self):
        # THE OTHER DIRECTION. A view that surfaced every refusal would be useless: the remedy
        # is a human re-submission, so a case that would refuse again must not be raised.
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        with self.assertRaises(OpError):
            self.gate.execute("SPEND", OWNER, {"line": "denied", "at": T(10, 0)})
        r = self.refusals("NO-SPEND")[-1]
        self.law("UNRELATED", T(9, 30), [{"action": "NOTHING-MATCHES-THIS"}])
        self.assertNotIn(r["seq"], [c["refusal_seq"] for c in self.views.re_ask(self.gate)])

    def test_a_nonconforming_call_never_becomes_a_re_ask_case(self):
        # A call that was malformed does not become well-formed because law changed.
        with self.assertRaises(OpError):
            self.gate.execute("NO-SUCH-OP", OWNER, {})
        self._refused_then_lifted()
        rules = [c["rule_cited"] for c in self.views.re_ask(self.gate)]
        self.assertNotIn("P3-CLOSURE", rules)
        self.assertNotIn("AR-2", rules)

    def test_the_exposure_view_names_the_consumer_of_an_overturned_acts_output(self):
        act = self.gate.execute("SPEND", OWNER, {"line": "leaky", "at": T(9, 30)})
        self.gate.execute("GRANT-READ", OWNER, {"grantee": "alice", "target": "spend:leaky"})
        self.gate.execute("CONSUME", "alice", {"target": "spend:leaky"})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        exposed = self.views.exposure()
        self.assertEqual(len(exposed), 1)
        self.assertEqual(exposed[0]["consumer"], "alice")
        self.assertEqual(exposed[0]["object"], "spend:leaky")
        self.assertEqual(exposed[0]["overturned_seq"], act["seq"])

    def test_the_exposure_view_is_empty_when_nothing_was_consumed(self):
        self.gate.execute("SPEND", OWNER, {"line": "clean", "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertEqual(self.views.exposure(), [])

    def test_the_sweep_reconciles_state_and_does_not_touch_the_consumption(self):
        # §11 item 3, RULED: the sweep reconciles STATE; consumption is exposure plus judgment.
        # No mechanical remedy is wanted and none is built.
        self.gate.execute("SPEND", OWNER, {"line": "leaky", "at": T(9, 30)})
        self.gate.execute("GRANT-READ", OWNER, {"grantee": "alice", "target": "spend:leaky"})
        c = self.gate.execute("CONSUME", "alice", {"target": "spend:leaky"})
        before = json.dumps(dict(self.store.by_seq(c["seq"])), sort_keys=True, default=str)
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertEqual(json.dumps(dict(self.store.by_seq(c["seq"])), sort_keys=True, default=str),
                         before)
        self.assertTrue(self.views.standing(c["seq"]))       # the consumption itself is not overturned


# ============================================================================================
# T-OVERTURN-NON-MONOTONE (design/36 ADDENDUM A.2)
#
# The row that distinguishes the CORRECT termination guarantee from the one §4b.5 states. A
# refused act whose refusal depended on a limit another act had already consumed: overturn the
# consuming act in round one, and the refused act must append NO overturn (nothing restores an
# effect's standing) while the round-one overturn stands unchanged.
# ============================================================================================

class TestOverturnNonMonotone(_World):

    def test_a_freed_limit_appends_nothing_and_the_round_one_overturn_stands(self):
        self.timed("CREATE-RULE")
        self.gate.execute("CREATE-OP", OWNER, {"name": "DRAW", "definition": {
            "description": "draw against a ceiling", "params": {"holder": "required",
                                                                "amount": "required",
                                                                "line": "required",
                                                                "at": "required"},
            # `holder` is the id read inline by object_derive ("draw:{holder}") and the ceiling
            # check's holder; `amount` is the small numeric the ceiling sums (census: `size`);
            # `line` is the ceiling key; `at` is the deciding time (census: `occurrence_time`).
            # All STRUCTURAL (vocabulary door, design/46 member 2); the object field cannot be
            # content-homed.
            "structural_params": ["holder", "amount", "line", "at"],
            "law_cited": "ROOT-NEG-1", "object_derive": {"tpl": "draw:{holder}"},
            "occurrence_time_param": "at", "payload_from": ["holder", "amount", "line"],
            "checks": [{"check": "ceiling", "policy_key_prefix": "draw-ceiling:",
                        "holder_param": "holder", "amount_param": "amount",
                        "key_param": "line", "aggregate_action": "DRAW",
                        "aggregate_field": "amount", "holder_field": "holder",
                        "removal_action": "RELEASE", "cite": "ROOT-NEG-1"}]}})
        self.gate.execute("CREATE-RULE", OWNER, {"rule_id": "DRAW-CEILING",
                                                 "policy_key": "draw-ceiling:ops", "value": 10,
                                                 "at": T(6, 0)})
        consuming = self.gate.execute("DRAW", OWNER, {"holder": "ops", "line": "a",
                                                      "amount": 8, "at": T(9, 30)})
        with self.assertRaises(OpError):                     # 8 + 5 > 10 — the limit is spent
            self.gate.execute("DRAW", OWNER, {"holder": "ops", "line": "b",
                                              "amount": 5, "at": T(9, 40)})
        refusal = self.refusals("ROOT-NEG-1")[-1]
        law = self.law("NO-DRAW", T(9, 0), [{"action": "DRAW", "object": "draw:ops"}])
        # round one overturns the CONSUMING act; the refused act appends nothing at all
        self.assertIn(consuming["seq"], self.overturned())
        self.assertNotIn(refusal["seq"], self.overturned())
        self.assertEqual([o["target_seq"] for o in self.views.overturns()], [consuming["seq"]])
        # and it surfaces for a human to re-ask, which is the whole remedy
        self.assertIn(refusal["seq"], [c["refusal_seq"] for c in self.views.re_ask(self.gate)])

    def test_an_act_once_overturned_is_never_un_overturned(self):
        # ADDENDUM A.2's first consequence, asserted directly: the overturned set only grows.
        self.timed("CREATE-RULE")
        self.spender()
        a = self.gate.execute("SPEND", OWNER, {"line": "a", "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertEqual(self.overturned(), [a["seq"]])
        self.law("ALSO-NO-SPEND", T(8, 0), [{"action": "NOTHING"}])
        self.assertIn(a["seq"], self.overturned())           # still overturned, never withdrawn
        self.assertEqual(len([o for o in self.views.overturns()
                              if o["target_seq"] == a["seq"]]), 1)   # and not overturned twice


# ============================================================================================
# THE ANCHOR GUARD — computed, not matched (design/36 ADDENDUM E.1, owner-ruled 2026-07-27).
#
# THE EXTENDED LEDGER (ADDENDUM E.3). The trigger swap is a retirement, so the
# strictly-stronger proof runs on a ledger EXTENDED into the dimension the old trigger could
# not express. It runs in BOTH directions: the accumulation case the old trigger misses, and
# the non-orphaning named-kind case whose over-refusal is being removed DELIBERATELY.
# ============================================================================================

class _AnchorWorld(_World):
    """A narrowed world with a real grant chain, so the leash is observable at all."""

    def setUp(self):
        super().setUp()
        self.timed("CREATE-RULE")
        self.timed("GRANT")
        self.mother = self.views.mother_space()
        for who in ("alice", "bob", "carol"):
            self.gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": who, "actor_class": "human"})

    def grant(self, gid, maker, grantee, at, space=None):
        return self.gate.execute("GRANT", maker, {
            "grant_id": gid, "grantee": grantee, "actions": "*", "info": "*",
            "space": space or self.mother, "at": at})


class TestAnchorGuardIsComputed(_AnchorWorld):
    """T-ANCHOR-GUARD-IS-COMPUTED — a structural assertion that no kind list governs it."""

    def test_the_guards_trigger_reads_no_act_kind(self):
        import inspect
        src = inspect.getsource(reconcile.anchor_verdict) + inspect.getsource(reconcile._rootless)
        for kind in ("HANDOVER", "DESIGNATE-SUCCESSOR", "ACCEPT-SUCCESSION", "REVOKE-SUCCESSION"):
            self.assertNotIn(f'"{kind}"', src,
                             "the guard's trigger matched an act kind — the correction the owner "
                             "ruled is that the invariant is effect-level and the three named "
                             "kinds were the trigger written narrower than the law it cited")
        self.assertNotIn("root grant", src.split('"""')[2] if src.count('"""') > 2 else "")

    def test_the_leash_is_declared_in_the_ops_own_definition(self):
        # WIRE-AT-BIRTH as DATA (DIGEST-C2 §8): the leash is in the definition record the
        # founding installs, so a cold reader of the pack sees it. Never a code verb list.
        self.assertEqual(reconcile.guard_declared(self.views), "post-state")
        d = self.views.op_definitions()["OVERTURN"]["definition"]
        self.assertEqual(dict(d)["anchor_guard"], "post-state")

    def test_the_guard_is_inert_under_the_founding_openness_grant(self):
        # Every authority leash in this estate is inert under openness; both directions are
        # observable only in a narrowed world. Stated as a test so the inertness is a fact.
        ok, reason, _ = reconcile.anchor_verdict(self.store, self.views, set())
        self.assertTrue(ok, reason)


class TestOrphanByAccumulation(_AnchorWorld):
    """T-ORPHAN-BY-ACCUMULATION-REFUSES — the case the correction exists for.

    A chain ended by ORDINARY overturns only, with no named-kind act anywhere in the sweep. The
    old trigger (handover / succession / root grant) misses it entirely, because the only act
    the sweep touches is a MID-CHAIN grant made by an ordinary account."""

    def _accumulation(self):
        self.grant("root-alice", OWNER, "alice", T(7, 0))           # root grant — NOT swept
        mid = self.grant("alice-bob", "alice", "bob", T(9, 30))     # mid-chain — swept
        self.narrow()
        # decided BEFORE the law, so it is not a candidate and survives the rounds
        self.grant("bob-carol", "bob", "carol", T(8, 0))
        return mid

    def test_the_sweep_refuses_at_the_fixed_point_and_names_the_chain(self):
        mid = self._accumulation()
        self.law("NO-MID", T(9, 0), [{"action": "GRANT", "object": "grant:alice-bob"}])
        s = self.sweep()
        self.assertEqual([e["target_seq"] for e in s["computed"]], [mid["seq"]])
        self.assertEqual(s["committed"], [])
        self.assertEqual(s["refused"]["rule"], "CONST-AUTHORITY-ANCHORED")
        self.assertIn("grant:bob-carol", str(s["anchor"]["orphaned"]))
        self.assertIn("routes to the owner", s["refused"]["reason"])

    def test_the_old_three_kind_trigger_would_have_seen_nothing(self):
        # THE EVIDENCE THE CORRECTION IS LOAD-BEARING. Under the retired trigger this sweep
        # committed silently: its only target is an ordinary mid-chain grant, and a per-overturn
        # guard matching on handover / succession / root grant reports nothing wrong.
        mid = self._accumulation()
        self.law("NO-MID", T(9, 0), [{"action": "GRANT", "object": "grant:alice-bob"}])
        target = self.store.by_seq(self.sweep()["computed"][0]["target_seq"])
        self.assertEqual(target["action"], "GRANT")
        self.assertNotIn(target["action"], ("HANDOVER", "DESIGNATE-SUCCESSOR",
                                            "ACCEPT-SUCCESSION", "REVOKE-SUCCESSION"))
        self.assertNotEqual(target["actor"], self.views.chain_end())   # not a ROOT grant either

    def test_a_sweep_that_orphans_nothing_still_commits(self):
        # THE OTHER DIRECTION: a too-wedged guard would refuse every sweep in a narrowed world.
        self.grant("root-alice", OWNER, "alice", T(7, 0))
        act = self.grant("alice-bob", "alice", "bob", T(9, 30))
        self.narrow()
        self.law("NO-MID", T(9, 0), [{"action": "GRANT", "object": "grant:alice-bob"}])
        self.assertEqual(self.overturned(), [act["seq"]])
        self.assertIsNone(self.sweep()["refused"])


class TestNonOrphaningAnchorActPasses(_AnchorWorld):
    """T-NON-ORPHANING-ANCHOR-ACT-PASSES — the deliberate over-refusal removal.

    An overturn whose target IS a named kind (a ROOT grant) and which orphans nothing. The old
    trigger refused it; the corrected one permits it. Proven deliberate here rather than
    discovered later as a regression, which is the half of the extended ledger that is easy to
    skip (ADDENDUM E.3)."""

    def test_a_root_grant_that_orphans_nothing_is_overturned(self):
        root_grant = self.grant("root-alice", OWNER, "alice", T(9, 30))
        self.narrow()
        self.law("NO-ROOT-GRANT", T(9, 0), [{"action": "GRANT", "object": "grant:root-alice"}])
        self.assertEqual(self.overturned(), [root_grant["seq"]])
        self.assertIsNone(self.sweep()["refused"])

    def test_the_target_really_is_one_of_the_three_named_kinds(self):
        # Without this assertion the row above would prove nothing: it is only an over-refusal
        # removal if the old trigger would have fired.
        root_grant = self.grant("root-alice", OWNER, "alice", T(9, 30))
        self.narrow()
        self.law("NO-ROOT-GRANT", T(9, 0), [{"action": "GRANT", "object": "grant:root-alice"}])
        target = self.store.by_seq(root_grant["seq"])
        self.assertEqual(target["action"], "GRANT")
        self.assertEqual(target["actor"], OWNER)             # a ROOT grant: the old trigger's row
        self.assertEqual(target["actor"], self.views.chain_end())

    def test_a_designation_that_no_handover_used_is_overturned(self):
        # The second named kind, same direction: a succession act that moves no root.
        self.gate.execute("VERIFY-ACCOUNT", OWNER, {"account": "alice", "evidence_hash": "h:alice"})
        d = self.gate.execute("DESIGNATE-SUCCESSOR", OWNER, {"successor": "alice"})
        self.gate.execute("REVOKE-SUCCESSION", OWNER, {"reason": "changed mind"})
        self.narrow()
        self.law("NO-DESIGNATION", T(1, 0), [{"action": "DESIGNATE-SUCCESSOR"}])
        self.assertIn(d["seq"], self.overturned())
        self.assertIsNone(self.sweep()["refused"])


class TestAnchorRefusals(_AnchorWorld):
    """T-OVERTURN-ANCHOR and T-OVERTURN-ANCHOR-TRANSITIVE, plus the append-nothing guarantee."""

    def _handover(self):
        self.gate.execute("VERIFY-ACCOUNT", OWNER, {"account": "alice", "evidence_hash": "h:alice"})
        self.gate.execute("DESIGNATE-SUCCESSOR", OWNER, {"successor": "alice"})
        self.gate.execute("ACCEPT-SUCCESSION", "alice", {})
        return self.gate.execute("HANDOVER", OWNER, {})

    def test_an_overturn_that_would_move_root_refuses_cited_and_routes_to_the_owner(self):
        h = self._handover()
        self.assertEqual(self.views.chain_end(), "alice")
        self.law("NO-HANDOVER", T(1, 0), [{"action": "HANDOVER"}], actor="alice")
        s = self.sweep()
        self.assertEqual([e["target_seq"] for e in s["computed"]], [h["seq"]])
        self.assertEqual(s["committed"], [])
        self.assertEqual(s["refused"]["rule"], "CONST-AUTHORITY-ANCHORED")
        self.assertIn("moves root authority", s["refused"]["reason"])
        self.assertEqual(s["anchor"]["root_before"], "alice")
        self.assertEqual(s["anchor"]["root_after"], OWNER)
        self.assertEqual(self.views.chain_end(), "alice")    # and root did not move

    def test_a_mid_chain_grant_leaving_a_sub_chain_with_nothing_above_it(self):
        # T-OVERTURN-ANCHOR-TRANSITIVE. Under the three-kind form this row failed; the
        # corrected trigger is what makes it passable (ADDENDUM 3).
        self.grant("root-alice", OWNER, "alice", T(9, 30))
        self.narrow()
        self.grant("alice-bob", "alice", "bob", T(8, 0))     # decided earlier: never a candidate
        self.law("NO-ROOT-ALICE", T(9, 0), [{"action": "GRANT", "object": "grant:root-alice"}])
        s = self.sweep()
        self.assertEqual(s["committed"], [])
        self.assertEqual(s["refused"]["rule"], "CONST-AUTHORITY-ANCHORED")
        self.assertEqual(s["anchor"]["orphaned"][0]["id"], "grant:alice-bob")
        self.assertEqual(s["anchor"]["orphaned"][0]["why"], "maker")

    def test_a_refused_sweep_appends_nothing_at_all(self):
        # T-REFUSED-SWEEP-APPENDS-NOTHING. No partial overturns, no counter-overturns, not one
        # byte. A sweep that had committed and then refused would leave authority orphaned with
        # the record saying so — accepted-but-cannot-honour, refused outright.
        self._handover()
        self.narrow()
        before_len = len(self.store.events)
        before = open(self.record, "rb").read()
        self.law("NO-HANDOVER", T(1, 0), [{"action": "HANDOVER"}], actor="alice")
        after = open(self.record, "rb").read()
        self.assertEqual(len(self.store.events), before_len + 1)     # only the law itself
        self.assertTrue(after.startswith(before))
        self.assertEqual(self.views.overturns(), [])

    def test_an_ordinary_revoke_does_not_make_the_guard_refuse(self):
        # THE DIFFERENTIAL FORM, asserted. A revoke supersedes and nothing cascades, so a live
        # grant whose maker's own grant was revoked is an everyday state of this record. A guard
        # asked absolutely would refuse every sweep over such a world and would be enforcing an
        # invariant this estate does not hold.
        self.grant("root-alice", OWNER, "alice", T(7, 0))
        self.grant("alice-bob", "alice", "bob", T(7, 30))
        self.narrow()
        self.gate.execute("REVOKE", OWNER, {"grant_id": "root-alice"})
        unrelated = self.grant("root-carol", OWNER, "carol", T(9, 30))
        self.law("NO-CAROL", T(9, 0), [{"action": "GRANT", "object": "grant:root-carol"}])
        self.assertEqual(self.overturned(), [unrelated["seq"]])
        self.assertIsNone(self.sweep()["refused"])

    def test_the_guard_also_binds_a_hand_rolled_overturn_at_the_chokepoint(self):
        # The EP-18 R-A lesson: a leash inside one op's handler is reached past by any other op
        # minting the same record shape, so the guard fires at the write chokepoint on ANY
        # overturn-kind record, sweep or not.
        h = self._handover()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("OVERTURN", "SYSTEM", {
                "target_seq": h["seq"], "reaching_seq": h["seq"], "sweep": [h["seq"]],
                "target_deciding_time": T(9, 0), "reaching_deciding_time": T(8, 0)})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")


class TestExtendedLedgerProof(_AnchorWorld):
    """T-EXTENDED-LEDGER-PROOF — strictly-stronger-or-equal on the WHOLE extended set, both
    directions, with the ledger enumerated (owner-set, ADDENDUM E.3).

    An old ledger cannot contain cases in a dimension it could not express: the old trigger's
    ledger holds only kind-matches while the new dimension is EFFECT. So the ledger is extended
    into that dimension and the comparison is run case by case, with the old trigger
    reconstructed here as the predicate it was."""

    #: The retired trigger, reconstructed so the comparison has two sides.
    OLD_KINDS = ("HANDOVER", "DESIGNATE-SUCCESSOR", "ACCEPT-SUCCESSION", "REVOKE-SUCCESSION")

    def old_trigger(self, targets):
        """§4b.7 as written: refuse iff the overturned act's target is a handover, a succession,
        or a ROOT grant (a grant made by the chain-end)."""
        root = self.views.chain_end()
        for seq in targets:
            e = self.store.by_seq(seq)
            if e["action"] in self.OLD_KINDS:
                return True
            if e["action"] == "GRANT" and e["actor"] == root:
                return True
        return False

    def _case_orphan_by_accumulation(self):
        self.grant("root-alice", OWNER, "alice", T(7, 0))
        self.grant("alice-bob", "alice", "bob", T(9, 30))
        self.narrow()
        self.grant("bob-carol", "bob", "carol", T(8, 0))
        return "NO-MID", [{"action": "GRANT", "object": "grant:alice-bob"}], True

    def _case_non_orphaning_root_grant(self):
        self.grant("root-alice", OWNER, "alice", T(9, 30))
        self.narrow()
        return "NO-ROOT", [{"action": "GRANT", "object": "grant:root-alice"}], False

    def _case_handover_moves_root(self):
        self.gate.execute("VERIFY-ACCOUNT", OWNER, {"account": "alice", "evidence_hash": "h:alice"})
        self.gate.execute("DESIGNATE-SUCCESSOR", OWNER, {"successor": "alice"})
        self.gate.execute("ACCEPT-SUCCESSION", "alice", {})
        self.gate.execute("HANDOVER", OWNER, {})
        self.narrow_as("alice")
        return "NO-HANDOVER", [{"action": "HANDOVER"}], True

    def _case_ordinary_act_no_authority_effect(self):
        self.spender()
        self.gate.execute("SPEND", OWNER, {"line": "x", "at": T(9, 30)})
        return "NO-SPEND", [{"action": "SPEND"}], False

    def _case_mid_chain_with_nothing_below(self):
        self.grant("root-alice", OWNER, "alice", T(7, 0))
        self.grant("alice-bob", "alice", "bob", T(9, 30))
        self.narrow()
        return "NO-MID2", [{"action": "GRANT", "object": "grant:alice-bob"}], False

    def narrow_as(self, actor):
        self.gate.execute("REVOKE", actor, {"grant_id": "founding-openness"})

    CASES = ("_case_orphan_by_accumulation", "_case_non_orphaning_root_grant",
             "_case_handover_moves_root", "_case_ordinary_act_no_authority_effect",
             "_case_mid_chain_with_nothing_below")

    def test_the_extended_ledger_both_directions(self):
        ledger = []
        for name in self.CASES:
            case = TestExtendedLedgerProof(self._testMethodName)
            case.setUp()
            rule_id, when, expect_refuse = getattr(case, name)()
            actor = case.views.chain_end()
            case.law(rule_id, T(1, 0) if "handover" in name else T(9, 0), when, actor=actor)
            s = case.sweep()
            targets = [e["target_seq"] for e in s["computed"]]
            new_refuses = s["refused"] is not None
            old_refuses = case.old_trigger(targets)
            ledger.append({"case": name[6:], "targets": len(targets),
                           "old": "refuse" if old_refuses else "permit",
                           "new": "refuse" if new_refuses else "permit",
                           "expected": "refuse" if expect_refuse else "permit"})
            self.assertEqual(new_refuses, expect_refuse, f"{name}: {s.get('refused')}")
        print("\n[EP-26 T-EXTENDED-LEDGER-PROOF] " + json.dumps(ledger))
        by = {r["case"]: r for r in ledger}
        # DIRECTION ONE — the accumulation case: the old trigger MISSES it, the new one catches
        # it. This is the case the correction exists for, and it is the proof it is load-bearing.
        self.assertEqual((by["orphan_by_accumulation"]["old"],
                          by["orphan_by_accumulation"]["new"]), ("permit", "refuse"))
        # DIRECTION TWO — the non-orphaning named-kind case: the old trigger refuses it and the
        # corrected one permits it. An OVER-REFUSAL removed DELIBERATELY, proven here rather
        # than discovered later as a regression.
        self.assertEqual((by["non_orphaning_root_grant"]["old"],
                          by["non_orphaning_root_grant"]["new"]), ("refuse", "permit"))
        # THE PROTECTED INVARIANT IS PRESERVED, not the raw refusal count: every case where the
        # post-state would end a chain or move root refuses under the corrected trigger.
        for row in ledger:
            self.assertEqual(row["new"], row["expected"], row)


# ============================================================================================
# T-SWEEPS-SERIALIZE (design/36 ADDENDUM A.5)
# ============================================================================================

class TestSweepsSerialize(_World):

    def test_a_law_arriving_mid_sweep_lands_after_the_running_sweeps_empty_round(self):
        self.timed("CREATE-RULE")
        self.spender()
        for line in ("a", "b"):
            self.gate.execute("SPEND", OWNER, {"line": line, "at": T(9, 30)})
        held = {}

        def on_append(e):
            # fires from inside the running sweep's first commit
            if dict(e.get("payload") or {}).get("kind") == "overturn" and not held:
                held["token"] = reconcile.submit(self.gate, "CREATE-RULE", OWNER, {
                    "rule_id": "SECOND", "at": T(8, 0), "polarity": "-", "text": "second",
                    "when": [{"action": "NOTHING"}], "then": [{"refuse": "SECOND"}]})
        self.store.on_append(on_append)
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        self.assertIn("token", held)
        second = held["token"].record
        self.assertIsNotNone(second, "the held arrival was never accepted")
        overturn_seqs = [e["seq"] for e in self.store.all()
                         if dict(e.get("payload") or {}).get("kind") == "overturn"]
        self.assertEqual(len(overturn_seqs), 2)
        self.assertGreater(second["seq"], max(overturn_seqs))   # accepted only after the empty round
        self.assertEqual(len(self.gate._law_queue), 0)

    def test_the_two_sweeps_reconstruct_identically_on_replay(self):
        self.timed("CREATE-RULE")
        self.spender()
        for line in ("a", "b"):
            self.gate.execute("SPEND", OWNER, {"line": line, "at": T(9, 30)})
        held = {}

        def on_append(e):
            if dict(e.get("payload") or {}).get("kind") == "overturn" and not held:
                held["token"] = reconcile.submit(self.gate, "CREATE-RULE", OWNER, {
                    "rule_id": "SECOND", "at": T(8, 0), "polarity": "-", "text": "second",
                    "when": [{"action": "SPEND"}], "then": [{"refuse": "SECOND"}]})
        self.store.on_append(on_append)
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        live = json.dumps(self.views.overturns(), sort_keys=True, default=str)
        _, _, views2, _, _ = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs2"), os.path.join(self.dir, "vault"))
        self.assertEqual(json.dumps(views2.overturns(), sort_keys=True, default=str), live)


# ============================================================================================
# T-SESSION-REGISTRY (K10)
# ============================================================================================

class TestSessionRegistry(_World):

    def setUp(self):
        super().setUp()
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "budget-context",
                                                 "when": {"object": "budget:ops"}})

    def test_open_and_close_are_recorded_and_the_registry_is_derived(self):
        o = self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s1",
                                                      "read_set": ["view:budget-context"]})
        reg = self.views.sessions()
        self.assertEqual(reg["s1"]["state"], "live")
        self.assertEqual(reg["s1"]["account"], OWNER)
        self.assertEqual(reg["s1"]["read_set"], ["view:budget-context"])
        self.assertEqual(reg["s1"]["opened_seq"], o["seq"])
        c = self.gate.execute("SESSION-CLOSE", OWNER, {"session_id": "s1"})
        self.assertEqual(self.views.sessions()["s1"]["state"], "closed")
        self.assertEqual(self.views.sessions()["s1"]["closed_seq"], c["seq"])
        self.assertEqual(self.views.live_sessions(), {})

    def test_the_registry_answers_as_of_and_holds_nothing(self):
        o = self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s1", "read_set": []})
        self.gate.execute("SESSION-CLOSE", OWNER, {"session_id": "s1"})
        self.assertEqual(self.views.sessions(as_of=o["seq"])["s1"]["state"], "live")

    def test_the_read_set_is_stored_as_refs_and_resolved_at_use(self):
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s1",
                                                  "read_set": ["view:budget-context"]})
        rec = [e for e in self.store.all()
               if dict(e.get("payload") or {}).get("kind") == "session"][0]
        self.assertEqual(list(dict(rec["payload"])["read_set"]), ["view:budget-context"])
        resolved = self.views.session_read_set("s1")
        self.assertEqual(resolved["view:budget-context"]["name"], "budget-context")

    def test_a_dangling_declaration_resolves_to_none_and_is_visible(self):
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s1", "read_set": ["view:nope"]})
        self.assertIsNone(self.views.session_read_set("s1")["view:nope"])

    def test_a_second_account_opens_its_own_session(self):
        self.gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": "alice", "actor_class": "human"})
        self.gate.execute("SESSION-OPEN", "alice", {"session_id": "s2", "read_set": []})
        self.assertEqual(self.views.sessions()["s2"]["account"], "alice")

    def test_this_ep_delivers_nothing_new_to_a_session(self):
        # K10's boundary, asserted: this EP records the contact points and their views. The
        # session-aware PUSH is EP-27's, and the standing push's queues do not gain a session.
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s1", "read_set": []})
        self.assertNotIn("s1", json.dumps(self.views.queues(), default=str))


# ============================================================================================
# T-DEGENERATE-IDENTITY — the strictly-stronger floor (design/36 §7 item 2).
#
# The whole pre-existing suite is the old-ledger side and re-runs green with the acceptance
# step live; that half is proven by running it. What is proven HERE is the structural half:
# the fast path is the same rule at its degenerate point, not a bypass.
# ============================================================================================

class TestDegenerateIdentity(_World):

    def test_a_synchronous_arrival_takes_the_live_fold_unchanged(self):
        draft = {"actor": OWNER, "action": "CREATE-INFO", "payload": {"content": "x"}}
        self.assertFalse(reconcile.carries_deciding_time(draft))
        self.assertIs(reconcile.acceptance_law(self.views, draft), self.views.active_rules())

    def test_a_marked_substitution_is_treated_as_d_equals_r(self):
        # RAISED-BY-DESIGN 3, v1 reading: an occurrence_time the observe seam stood in for a
        # window that reported none gets NO counterfactual standing. Conservative on purpose.
        draft = {"actor": "obs", "action": "OBSERVE-FILE", "occurrence_time": T(1, 0),
                 "payload": {"time_source": "submission-substituted"}}
        self.assertFalse(reconcile.carries_deciding_time(draft))
        self.assertIs(reconcile.acceptance_law(self.views, draft), self.views.active_rules())

    def test_a_window_reported_time_does_carry_a_deciding_time(self):
        draft = {"actor": "obs", "action": "OBSERVE-FILE", "occurrence_time": T(1, 0),
                 "payload": {"time_source": "window-reported"}}
        self.assertTrue(reconcile.carries_deciding_time(draft))

    def test_a_malformed_payload_still_refuses_cited_rather_than_crashing(self):
        # The acceptance step runs BEFORE the branch that refuses a malformed payload, so it
        # must not crash on the way there (P4-REFUSE).
        self.gate.execute("CREATE-OP", OWNER, {"name": "PASSTHRU", "definition": {
            "description": "a data-passthrough op", "params": {"payload": "required"},
            # `payload` is arbitrary passthrough data — a reachable-content body, not a small
            # scalar or id — so it is CONTENT-classified: blob-homed by hash, never inline
            # (vocabulary door, design/46 member 2). It has no object_param, so content-homing is
            # safe; the op is a definition-only fixture (never executed), so no blob is minted.
            "content_params": {"payload": "payload_hash"},
            "law_cited": "CAP-IS-LAW", "payload_from": []}})
        self.assertFalse(reconcile.carries_deciding_time({"payload": ["not", "a", "dict"]}))
        self.assertFalse(reconcile.is_law_family({"payload": ["not", "a", "dict"]}))

    def test_the_founding_is_never_a_sweep_candidate(self):
        # Re-running the gate's admission test over genesis would ask whether the founding was
        # permitted by the world the founding itself created. The first smoke run of this sweep
        # did exactly that and proposed overturning the entire founding.
        self.timed("CREATE-RULE")
        self.law("EVERYTHING", T(1, 0), [{"action": "CREATE-ACTOR"}])
        self.assertEqual(self.overturned(), [])
        for e in self.store.all():
            if e["seq"] <= self.founding_end:
                self.assertFalse(reconcile.crossed_the_gate(e, self.founding_end))

    def test_the_audit_mirror_is_never_a_sweep_candidate(self):
        self.gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": "alice", "actor_class": "human"})
        self.gate.execute("VERIFY-ACCOUNT", OWNER, {"account": "alice", "evidence_hash": "h"})
        mirrors = [e for e in self.store.all()
                   if dict(e.get("payload") or {}).get("stream") in ("dual-audit", "dual-audit-b")]
        self.assertTrue(mirrors, "no mirror records — the fixture is not exercising the guard")
        for m in mirrors:
            self.assertFalse(reconcile.crossed_the_gate(m, self.founding_end))


# ============================================================================================
# T-TOTAL-ROUNDTRIP-2 extended (the T-TOTAL-ROUNDTRIP-3 seed; EP-33 runs it whole).
# ============================================================================================

class TestTotalRoundTripExtended(_World):

    def test_sessions_sweep_products_and_both_views_all_reconstruct(self):
        self.timed("CREATE-RULE")
        self.spender()
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "budget-context",
                                                 "when": {"object": "budget:ops"}})
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s1",
                                                  "read_set": ["view:budget-context"]})
        act = self.gate.execute("SPEND", OWNER, {"line": "leaky", "at": T(9, 30)})
        self.gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": "alice", "actor_class": "human"})
        self.gate.execute("GRANT-READ", OWNER, {"grantee": "alice", "target": "spend:leaky"})
        self.gate.execute("CONSUME", "alice", {"target": "spend:leaky"})
        self.gate.execute("SESSION-OPEN", "alice", {"session_id": "s2", "read_set": []})
        self.gate.execute("SESSION-CLOSE", OWNER, {"session_id": "s1"})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])

        def snapshot(v, g):
            return json.dumps({
                "sessions": v.sessions(), "live": sorted(v.live_sessions()),
                "overturns": v.overturns(), "exposure": v.exposure(),
                "re_ask": v.re_ask(g),
                "standing": {e["seq"]: v.standing(e["seq"]) for e in v.store.all()},
                "read_set": v.session_read_set("s1"),
            }, sort_keys=True, default=str)

        live = snapshot(self.views, self.gate)
        store2, gate2, views2, _, _ = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs2"), os.path.join(self.dir, "vault"))
        self.assertEqual(len(store2.events), len(self.store.events))
        self.assertEqual(snapshot(views2, gate2), live)
        self.assertFalse(views2.standing(act["seq"]))

    def test_killing_every_derived_structure_changes_no_answer(self):
        self.timed("CREATE-RULE")
        self.spender()
        self.gate.execute("SPEND", OWNER, {"line": "x", "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        before = json.dumps(self.views.overturns(), sort_keys=True, default=str)
        self.views._memo.clear()
        for p in list(getattr(self.store, "_projections", {}).values()):
            p.kill()
        self.gate.sweeps = []                                # the observability ledger is not load-bearing
        self.assertEqual(json.dumps(self.views.overturns(), sort_keys=True, default=str), before)


# ============================================================================================
# The founding grew: the rules and the ops are RECORDS, and the version bumped MINOR.
# ============================================================================================

class TestFoundingGrew(_World):

    def test_the_four_two_times_rules_are_founding_records(self):
        rules = self.views.active_rules()
        for rid in ("TWO-TIMES-ACCEPT", "TWO-TIMES-OVERTURN", "TWO-TIMES-SEAL-BOUND",
                    "SESSION-DECLARED"):
            self.assertIn(rid, rules, f"{rid} is not a record — law lives in the record, not in code")
            self.assertTrue(rules[rid].get("text"))

    def test_the_three_ops_are_definition_born(self):
        defs = self.views.op_definitions()
        for name in ("SESSION-OPEN", "SESSION-CLOSE", "OVERTURN"):
            self.assertIn(name, defs)
            self.assertTrue(self.gate.has(name))
            self.assertEqual(defs[name].get("tier"), "owner")

    def test_the_overturn_op_cites_the_overturn_rule(self):
        self.assertEqual(dict(self.views.op_definitions()["OVERTURN"]["definition"])["law_cited"],
                         reconcile.OVERTURN_RULE)

    def test_the_founding_version_bumped_minor(self):
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and the flip chain above stops here.]
        # ASSERTED: a FROZEN LITERAL "1.17.0", last set 2026-08-05 (EP-28N AMENDMENT 1).
        # SUPERSEDED: EP-28S landed the identity law on 2026-08-08; founding 1.17.0 -> 1.18.0.
        #   Fifth rewrite of this literal. A version literal in a test is a STORED COPY OF A
        #   COMPUTABLE VALUE, so every lawful bump reds a row that was never about the bump.
        # REMAINS TRUE, separated out and STILL ASSERTED: the founding never goes BACKWARDS
        #   past the version this row recorded (a floor cannot go stale and still reds on a
        #   regression), and THE READER AND THE RECORD AGREE — the pack on disk versus the
        #   designation the installer stamped into FOUND-STORE, two different takings of one
        #   fact. (`load_pack()["founding_version"]` is NOT the second reader: it IS what
        #   `founding_version()` returns, so that pairing is one reading wearing two labels.)
        # GIVEN UP: this row no longer notices a bump — never its job; EP-28N2 holds that
        #   against a PINNED before-side. The row's NAME is kept: the founding version did
        #   bump MINOR at EP-26 and that is a fact about two commits, not about today's pack.
        from founding.install import founding_version
        v = founding_version()
        self.assertGreaterEqual(tuple(int(n) for n in v.split(".")), (1, 17, 0))
        fs = self.store.by_action("FOUND-STORE")[0]
        self.assertEqual(dict(fs["payload"])["founding_version"], v)

    def test_the_sweeps_overturns_meet_every_standing_check(self):
        # ADDENDUM A.4's second half, stated rather than left to inference: the sweep's
        # overturns cross the gate as ordinary governed acts, so the protected-core floor and
        # the conservation law bind them. A system act above the protected core would gap a
        # shield the conservation law says is never gapped.
        self.timed("CREATE-RULE")
        self.spender()
        self.gate.execute("SPEND", OWNER, {"line": "x", "at": T(9, 30)})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        o = [e for e in self.store.all()
             if dict(e.get("payload") or {}).get("kind") == "overturn"][0]
        self.assertEqual(o["actor"], "SYSTEM")
        self.assertIsNotNone(o["rule_cited"])
        self.assertNotEqual(dict(o["payload"]).get("tier"), "constitutional")

    def test_a_structural_dont_over_overturn_would_refuse_the_sweep(self):
        # The overturns are not above the law: a recorded don't matching OVERTURN stops them.
        self.timed("CREATE-RULE")
        self.spender()
        self.gate.execute("SPEND", OWNER, {"line": "x", "at": T(9, 30)})
        self.gate.execute("CREATE-RULE", OWNER, {"rule_id": "NO-OVERTURN", "polarity": "-",
                                                 "text": "no overturns", "at": T(6, 0),
                                                 "when": [{"action": "OVERTURN"}],
                                                 "then": [{"refuse": "NO-OVERTURN"}]})
        self.law("NO-SPEND", T(9, 0), [{"action": "SPEND"}])
        s = self.sweep()
        self.assertEqual(s["refused"]["rule"], "NO-OVERTURN")
        self.assertEqual(s["committed"], [])                 # refused WHOLE, never partway
        self.assertEqual(self.views.overturns(), [])


if __name__ == "__main__":
    unittest.main()
