"""EP-27 — lanes, session-aware push, and budgeted backpressure (design/35 §3; design/36 K10).

Law travels faster than traffic. A law change that reaches a live session's declared view is
delivered to it ahead of ordinary traffic, floods cannot starve the urgent, and deliveries
still append nothing.

THE REFERENCE THIS BATTERY EXISTS TO REFUSE is QoS as engine configuration: priority classes
as constants, a lane table in code, budget thresholds as module-level numbers. Every row below
is written so that taking it fails something. An engine with `PRIORITY_ACTIONS = [...]` fails
T-LANE-IS-DERIVED's structure guard AND its new-kind row (a law-family kind invented in a test
world must ride the lane with zero code change). An engine with its budgets in code fails
T-LANE-POLICY-IS-RECORDED (amending the recorded policy must change the machine's behaviour).
An engine that appends a delivery or a shed fails T-PUSH-APPENDS-NOTHING.

Coverage (the EP's five named rows, plus what proving them honestly required):
  T-LANE-PRIORITY          under a queued ordinary backlog a law-family record is processed and
                           delivered first, BOTH directions; the store's own order is untouched.
  T-SESSION-PUSH           the worked ordering: a session opens declaring V; a law change
                           reaching V lands and reaches the session ahead of an ordinary item
                           enqueued earlier; a session V does not reach receives nothing.
  T-PUSH-APPENDS-NOTHING   kill every queue, pending set and delivery structure, replay,
                           identical — re-proven over the lane machinery, sheds included.
  T-BACKPRESSURE-RESERVE   under a synthetic flood ordinary delivery degrades by recorded
                           policy (each shed citing its rule) while the reserve delivers; and
                           the column is PROVEN ABLE TO FAIL — a reserve of zero starves.
  T-LANE-IS-DERIVED        the structure guard: no priority action list in code; membership
                           computed from the record; a new law-family kind rides with no code
                           change; the overturn rides ORDINARY (the sweep is its urgency).
  T-LANE-POLICY-IS-RECORDED   budgets are recorded rules; amending one changes behaviour.
  T-SHED-CITES-ITS-POLICY     every shed and every delay names the rule that caused it.
  T-DERIVATION-IS-THE-TRUTH   the worker is an ACCELERATION of the derivation under pressure
                              too (the EP-08B lesson: a cache that drifts from its derivation).
  T-NO-SWEEP-INTERLEAVE       (design/36 ADDENDUM A.5) lane priority orders arrivals; it does
                              not interleave a running sweep.
  T-DEGENERATE-UNCHANGED      the old-ledger side: with the shipped defaults nothing that
                              existed before this EP moves.
"""

import json
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel import push as push_mod  # noqa: E402
from kernel import reconcile  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.push import StandingPush  # noqa: E402
from kernel.views import Views  # noqa: E402

OWNER = "owner"


def _trivial(gate, action, payload=None):
    """An ORDINARY op: its payload declares no rule_id, so its records ride the ordinary lane
    by what they ARE, with nothing anywhere naming this verb."""
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x",
                                         "rule_cited": "ROOT-NEG-5", "payload": dict(payload or {})})


class _LaneWorld(unittest.TestCase):
    """A full kernel with a fan-out of move-to views, so a backlog can be built the way a real
    one forms: delivery fan-out outrunning the cycle budget."""

    FANOUT = 3

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "r.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"))
        self.push = self.views.push
        _trivial(self.gate, "FROB")
        for i in range(self.FANOUT):
            self.gate.execute("CREATE-VIEW", OWNER, {"name": f"frob-watch-{i}",
                                                     "when": {"action": "FROB"},
                                                     "then": {"move_to": f"frob-inbox-{i}"}})
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "law-watch",
                                                 "when": {"action": "CREATE-RULE"},
                                                 "then": {"move_to": "law-inbox"}})

    # ---- helpers ----
    def set_budget(self, **changes):
        """Amend the lane budget BY AN ORDINARY RECORDED ACT — a CREATE-RULE carrying the same
        rule_id, latest-wins. This is the whole point of budgets being law-data: no code path
        anywhere sets these, and a test that wants a different machine writes a record."""
        value = dict(self.views.policy_value(push_mod.LANE_BUDGET_KEY) or {})
        value.update(changes)
        self.gate.execute("CREATE-RULE", OWNER, {"rule_id": push_mod.LANE_BUDGET_RULE,
                                                 "policy_key": push_mod.LANE_BUDGET_KEY,
                                                 "value": value,
                                                 "text": "test-world calibration of the lane budget"})
        return value

    def frob(self, n=1, actor="alice"):
        return [self.gate.execute("FROB", actor, {}) for _ in range(n)]

    def timed_create_rule(self, param="at", carry=()):
        """Make CREATE-RULE able to carry a DECIDING TIME, the EP-26 way: AMEND-OP in a
        disposable world, tier conserved, the amendment itself a record. The shipped founding
        cannot express a d<r law (design/36 ADDENDUM F.2 — K7's stated cap), so a sweep is only
        reachable through the engine's own amendment capability. No back door: the amended op
        is an ordinary definition-born op crossing the ordinary gate."""
        live = self.views.op_definitions()["CREATE-RULE"]
        d = json.loads(json.dumps(live["definition"], default=dict))
        d["params"] = dict(d.get("params") or {}, **{param: "required"})
        d["occurrence_time_param"] = param
        # The added params are governance fields read INLINE — the timing param (an occurrence
        # timestamp, routed) and each carry field (written straight into the payload) — so each
        # is STRUCTURAL, the vocabulary door's inline class (design/46 member 2).
        d["structural_params"] = list(d.get("structural_params") or []) + [param] + list(carry)
        for field in carry:
            d["params"][field] = "optional"
            d["payload_from"] = list(d.get("payload_from") or []) + [field]
        self.gate.execute("AMEND-OP", OWNER, {"name": "CREATE-RULE", "tier": live.get("tier"),
                                              "definition": d})

    def law(self, rule_id, **extra):
        return self.gate.execute("CREATE-RULE", OWNER,
                                 dict({"rule_id": rule_id, "text": f"law {rule_id}"}, **extra))

    def delivered_seqs(self):
        return {c: [r["seq"] for r in rs] for c, rs in self.push.channels().items()}

    def pending_seqs(self):
        return [(i["lane"], i["record"]["seq"]) for i in self.push.pending()]


# ======================================================================================
# T-LANE-IS-DERIVED — the structure guard and the membership rule
# ======================================================================================

class TestLaneIsDerived(_LaneWorld):

    def test_membership_is_the_records_own_class_and_nothing_else(self):
        law = self.law("TEST-LAW-A")
        ordinary = self.frob(1)[0]
        self.assertEqual(push_mod.lane_of(law), push_mod.LAW_LANE)
        self.assertEqual(push_mod.lane_of(ordinary), push_mod.ORDINARY_LANE)
        # it is the SAME predicate the store and the two-times fold use, not a second opinion
        self.assertTrue(reconcile.is_law_family(law))
        self.assertFalse(reconcile.is_law_family(ordinary))

    def test_a_new_law_family_kind_rides_the_lane_with_zero_code_change(self):
        """The row that kills a verb list. An op invented in this world, whose verb appears
        nowhere in the engine, mints a payload declaring a rule_id — and it rides the law lane
        because of WHAT IT IS."""
        _trivial(self.gate, "ZORBLE-LAW", payload={"rule_id": "ZORBLE-1", "text": "an invented law kind"})
        rec = self.gate.execute("ZORBLE-LAW", OWNER, {})
        self.assertEqual(push_mod.lane_of(rec), push_mod.LAW_LANE)
        # and the identical op WITHOUT a rule_id in its payload does not ride it
        _trivial(self.gate, "ZORBLE-PLAIN", payload={"text": "not a law"})
        self.assertEqual(push_mod.lane_of(self.gate.execute("ZORBLE-PLAIN", OWNER, {})),
                         push_mod.ORDINARY_LANE)

    def test_the_overturn_rides_ordinary_because_the_sweep_is_its_urgency(self):
        """design/35 §3, carried by the EP: the LAW class rides the lane; an overturn is a
        DECISION and rides ordinary. Nothing exempts it by name — it rides ordinary because its
        payload declares no rule_id."""
        fake_overturn = {"seq": 1, "actor": "SYSTEM", "action": "OVERTURN",
                         "payload": {"kind": "overturn", "record_class": "DECISION",
                                     "target_seq": 3, "reaching_seq": 4}}
        self.assertEqual(push_mod.lane_of(fake_overturn), push_mod.ORDINARY_LANE)

    def test_no_priority_action_list_lives_in_the_lane_code(self):
        """THE STRUCTURE GUARD. The named wrong reference is `PRIORITY_ACTIONS = [...]`. The
        lane surface may not carry a list of action names, an op-name table, or a payload-kind
        menu — governance content in engine code is I5's refusal."""
        surface = os.path.join(os.path.dirname(__file__), "..", "src", "kernel", "push.py")
        with open(surface, encoding="utf-8") as f:
            src = f.read()
        code = "\n".join(l for l in src.splitlines()
                         if not l.lstrip().startswith("#"))
        code = re.sub(r'""".*?"""', "", code, flags=re.S)
        # no collection literal of SCREAMING-KEBAB action names anywhere in the executable code
        offenders = re.findall(r'[\[\(]\s*"[A-Z][A-Z0-9-]{2,}"\s*[,\]\)]', code)
        self.assertEqual(offenders, [], f"a priority action list reached the lane code: {offenders}")
        # and the two structural lane names are the ONLY closed vocabulary here
        for verb in ("CREATE-RULE", "AMEND-OP", "OVERTURN", "GRANT", "SESSION-OPEN"):
            self.assertNotIn(f'"{verb}"', code, f"the lane code names the verb {verb}")

    def test_the_lane_precedence_is_recorded_not_coded(self):
        """Which lane holds the reserved slots is governance content, so it is read from the
        record. Re-prioritising is a recorded act, never an edit to this file."""
        policy = self.views.policy_value(push_mod.LANE_BUDGET_KEY)
        self.assertEqual(list(policy["order"]), [push_mod.LAW_LANE, push_mod.ORDINARY_LANE])
        self.set_budget(order=[push_mod.ORDINARY_LANE, push_mod.LAW_LANE])
        self.assertEqual(self.push.lane_order(), (push_mod.ORDINARY_LANE, push_mod.LAW_LANE))


# ======================================================================================
# T-LANE-POLICY-IS-RECORDED — budgets are law-data with a named calibration owner
# ======================================================================================

class TestLanePolicyIsRecorded(_LaneWorld):

    def test_the_founding_ships_the_budget_as_a_record_with_its_proposed_status_visible(self):
        rules = self.views.active_rules()
        self.assertIn(push_mod.LANE_BUDGET_RULE, rules)
        rule = rules[push_mod.LANE_BUDGET_RULE]
        self.assertEqual(rule["policy_key"], push_mod.LANE_BUDGET_KEY)
        self.assertIn("PROPOSED DEFAULT", rule["text"])
        for field in ("cycle", "reserve", "depth", "order"):
            self.assertIn(field, rule["value"])

    def test_amending_the_budget_changes_the_machine_with_no_code_change(self):
        self.set_budget(cycle=1, reserve={push_mod.LAW_LANE: 0})
        self.assertEqual(self.push.budget()["cycle"], 1)
        # and it is read AS OF the record, so history answers with the law of its own moment
        early = self.views.policy_value(push_mod.LANE_BUDGET_KEY, as_of=1)
        self.assertIsNone(early)          # before the founding seeded it, there is no budget

    def test_with_no_recorded_budget_the_lane_machinery_is_inert_not_defaulted(self):
        """FAIL-OPEN ON DELIVERY, which is the safe direction: no recorded policy means no
        shedding and no cap, which is exactly the pre-EP behaviour. There is no code-resident
        default standing in for a missing law."""
        bare_path = os.path.join(tempfile.mkdtemp(), "bare.jsonl")
        store, gate, views = build_kernel(bare_path)
        worker = StandingPush(store, views)
        # strip the budget by amending it away to nothing recorded: use a world with no policy
        self.assertIsNotNone(views.policy_value(push_mod.LANE_BUDGET_KEY))
        raw = Views(_EmptyStore())
        self.assertIsNone(raw.policy_value(push_mod.LANE_BUDGET_KEY))
        w2 = StandingPush(raw.store, raw)
        self.assertIsNone(w2.budget()["cycle"])
        self.assertEqual(w2.budget()["depth"], {})
        del worker, gate, store


class _EmptyStore:
    """A store with no founding at all — the honest way to ask what the worker does when the
    record contains no lane policy."""

    def __init__(self):
        self.events = []

    def all(self, as_of=None):
        return []

    def by_action(self, action, as_of=None):
        return []

    def on_append(self, fn):
        pass

    def record_projection(self, name):
        return self


# ======================================================================================
# T-LANE-PRIORITY — both directions, and the store's order untouched
# ======================================================================================

class TestLanePriority(_LaneWorld):

    def _build_backlog(self, appends=8):
        """A backlog forms the way a real one does: delivery fan-out outrunning the cycle
        budget. Three move-to views match every FROB; the budget serves two per cycle."""
        self.set_budget(cycle=2, reserve={push_mod.LAW_LANE: 1}, depth={})
        self.frob(appends)
        return self.push.pending()

    def test_a_law_record_is_delivered_ahead_of_an_older_ordinary_backlog(self):
        backlog = self._build_backlog()
        self.assertGreater(len(backlog), 0, "no backlog formed — the budget did not bind")
        self.assertTrue(all(i["lane"] == push_mod.ORDINARY_LANE for i in backlog))
        oldest_pending = backlog[0]["record"]["seq"]

        law = self.law("LANE-TEST-LAW")
        # the law record was appended AFTER every backlog item and is delivered in its own
        # cycle, while ordinary work recorded BEFORE it is still waiting. That is the whole
        # claim: the lane moved a later arrival ahead of earlier traffic.
        self.assertIn(law["seq"], self.delivered_seqs().get("law-inbox", []))
        overtaken = [i["record"]["seq"] for i in self.push.pending()
                     if i["record"]["seq"] < law["seq"]]
        self.assertTrue(overtaken,
                        "nothing was overtaken — the law did not travel faster than traffic")
        self.assertLessEqual(oldest_pending, max(overtaken))

    def test_the_stores_own_order_is_untouched_by_lane_scheduling(self):
        """design/35 §5 and design/21: the lane changes the SCHEDULING of processing, never
        record_time's authority. Nothing is backdated, nothing is reordered, seq and
        record_time stay monotone and minted at append."""
        self._build_backlog()
        self.law("ORDER-TEST-LAW")
        self.frob(3)
        seqs = [e["seq"] for e in self.store.all()]
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(seqs, list(range(1, len(seqs) + 1)))
        times = [e["record_time"] for e in self.store.all()]
        self.assertEqual(times, sorted(times))
        # and the law's own record_time is later than every backlog item's, exactly as its
        # arrival was: the lane moved its DELIVERY, not its place in the record
        law_rec = [e for e in self.store.all()
                   if (e.get("payload") or {}).get("rule_id") == "ORDER-TEST-LAW"][0]
        frobs = [e for e in self.store.all() if e["action"] == "FROB" and e["seq"] < law_rec["seq"]]
        self.assertTrue(all(f["record_time"] <= law_rec["record_time"] for f in frobs))

    def test_intake_processes_the_law_submission_ahead_of_a_queued_ordinary_backlog(self):
        """THE UPWARD DIRECTION. A pending set of submissions drains law-first, so the law
        reaches the store with a LOWER seq than ordinary work submitted before it."""
        intake = push_mod.LaneIntake(self.gate, self.views)
        for i in range(5):
            intake.submit("FROB", "alice", {})
        intake.submit("CREATE-RULE", OWNER, {"rule_id": "INTAKE-LAW", "text": "arrived late, processed first"})
        for i in range(2):
            intake.submit("FROB", "bob", {})
        self.assertEqual(len(intake.pending()), 8)

        drained = intake.drain()
        law_rec = [r for r in drained if (r.get("payload") or {}).get("rule_id") == "INTAKE-LAW"][0]
        frob_seqs = [r["seq"] for r in drained if r["action"] == "FROB"]
        self.assertTrue(all(law_rec["seq"] < s for s in frob_seqs),
                        "the law submission must be processed before ordinary work submitted earlier")
        # and among themselves the ordinary submissions keep their submission order
        self.assertEqual(frob_seqs, sorted(frob_seqs))
        self.assertEqual([r["actor"] for r in drained if r["action"] == "FROB"],
                         ["alice"] * 5 + ["bob"] * 2)

    def test_intake_reads_the_lane_from_the_ops_own_definition_record(self):
        intake = push_mod.LaneIntake(self.gate, self.views)
        self.assertEqual(intake.lane_of_op("CREATE-RULE"), push_mod.LAW_LANE)
        self.assertEqual(intake.lane_of_op("GRANT"), push_mod.ORDINARY_LANE)
        # an op with no definition record cannot have its lane read from the record, and the
        # intake says so rather than guessing from its name (the raise, made visible)
        self.assertIsNone(intake.lane_of_op("CREATE-OP"))
        self.assertIn("CREATE-OP", intake.undeclared())


# ======================================================================================
# T-SESSION-PUSH — the worked ordering of design/35 §3
# ======================================================================================

class TestSessionPush(_LaneWorld):

    def open_session(self, sid, read_set):
        return self.gate.execute("SESSION-OPEN", OWNER, {"session_id": sid, "read_set": read_set})

    def test_a_law_change_reaching_a_declared_view_is_delivered_to_that_session(self):
        self.open_session("s-9am", ["view:rule-master"])
        law = self.law("SESSION-REACH-LAW")
        delivered = self.push.session_deliveries()
        self.assertIn("s-9am", delivered)
        self.assertIn(law["seq"], [r["record"]["seq"] for r in delivered["s-9am"]])
        self.assertEqual(delivered["s-9am"][-1]["lane"], push_mod.LAW_LANE)
        self.assertIn("view:rule-master", delivered["s-9am"][-1]["reached"])

    def test_a_session_the_change_does_not_reach_receives_nothing(self):
        self.open_session("s-actors", ["view:actor-master"])
        self.law("UNREACHING-LAW")
        self.assertEqual(self.push.session_deliveries().get("s-actors", []), [])

    def test_the_902_update_reaches_the_900_session_before_its_905_submit(self):
        """THE WORKED ORDERING, in test time. A session opens declaring V. An ordinary item is
        already queued behind a bound budget. A law change reaching V lands after it — and
        arrives at the session first."""
        # the reserve is sized for the law-lane work ONE law arrival produces here: the
        # law-inbox channel delivery and the session delivery. A reserve too small to carry a
        # cycle's law work delays part of it, which is honest behaviour and is why the value is
        # an owner calibration rather than a constant.
        self.set_budget(cycle=3, reserve={push_mod.LAW_LANE: 2}, depth={})
        self.open_session("s-900", ["view:rule-master"])
        self.frob(8)                                    # the 9:0x ordinary traffic, backlogged
        pending_before = [i["record"]["seq"] for i in self.push.pending()]
        self.assertTrue(pending_before, "no ordinary backlog formed")

        law = self.law("NINE-OH-TWO")                   # the 9:02 update
        session_items = self.push.session_deliveries()["s-900"]
        self.assertEqual([r["record"]["seq"] for r in session_items], [law["seq"]])
        # the 9:05 submit: the ordinary work queued BEFORE the law is still waiting
        self.assertTrue(set(pending_before) & {i["record"]["seq"] for i in self.push.pending()})

    def test_a_closed_session_stops_being_a_contact_point(self):
        self.open_session("s-transient", ["view:rule-master"])
        self.law("BEFORE-CLOSE")
        self.assertEqual(len(self.push.session_deliveries()["s-transient"]), 1)
        self.gate.execute("SESSION-CLOSE", OWNER, {"session_id": "s-transient"})
        self.law("AFTER-CLOSE")
        self.assertEqual(len(self.push.session_deliveries()["s-transient"]), 1)

    def test_a_dangling_declaration_reaches_nothing_and_is_visible(self):
        self.open_session("s-dangling", ["view:no-such-view"])
        self.law("DANGLE-LAW")
        self.assertEqual(self.push.session_deliveries().get("s-dangling", []), [])
        self.assertIn("view:no-such-view", self.push.dangling_declarations()["s-dangling"])

    def test_reach_is_the_views_own_answer_moving_never_a_matcher(self):
        """The reach test is not a second matcher living beside the view engine: it asks the
        view its own question before and after, exactly as §4b.2 runs the gate's own test."""
        self.open_session("s-filter", ["view:law-watch"])
        law = self.law("FILTER-REACH")
        self.assertIn(law["seq"],
                      [r["record"]["seq"] for r in self.push.session_deliveries()["s-filter"]])
        # a filter view that does not watch law records is not reached by one
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "frob-only", "when": {"action": "FROB"},
                                                 "then": {"move_to": "frob-only-inbox"}})
        self.open_session("s-frobonly", ["view:frob-only"])
        self.law("NOT-FOR-FROB")
        self.assertEqual(self.push.session_deliveries().get("s-frobonly", []), [])


# ======================================================================================
# T-BACKPRESSURE-RESERVE — and the column proven able to fail
# ======================================================================================

class TestBackpressureReserve(_LaneWorld):

    FANOUT = 4

    def flood(self, appends=40):
        self.frob(appends)

    def test_under_flood_ordinary_degrades_by_recorded_policy_and_the_reserve_delivers(self):
        self.set_budget(cycle=2, reserve={push_mod.LAW_LANE: 1}, depth={push_mod.ORDINARY_LANE: 10})
        self.flood()
        self.assertLessEqual(len([i for i in self.push.pending()
                                  if i["lane"] == push_mod.ORDINARY_LANE]), 10)
        self.assertTrue(self.push.shed(), "the depth cap never fired — the flood did not bind")
        # the reserve still delivers the urgent item, immediately, under the same flood
        law = self.law("FLOOD-LAW")
        self.assertIn(law["seq"], self.delivered_seqs().get("law-inbox", []))
        self.assertNotIn(law["seq"], [i["record"]["seq"] for i in self.push.pending()])

    def test_a_reserve_of_zero_visibly_starves_the_law_lane(self):
        """THE COLUMN PROVEN ABLE TO FAIL. With no reserved slots the law lane competes in
        arrival order, and under a standing ordinary backlog the law record waits. If this row
        passes with a reserve of eight as well, the reserve is doing nothing and the whole
        mechanism is decoration."""
        self.set_budget(cycle=2, reserve={push_mod.LAW_LANE: 0}, depth={})
        self.flood(20)
        law = self.law("STARVED-LAW")
        self.assertNotIn(law["seq"], self.delivered_seqs().get("law-inbox", []))
        self.assertIn(law["seq"], [i["record"]["seq"] for i in self.push.pending()])
        self.assertIn(law["seq"], [i["record"]["seq"] for i in self.push.starved()])

        # the SAME world with the reserve restored delivers it — one recorded act apart, and
        # nothing about the flood changed
        self.set_budget(reserve={push_mod.LAW_LANE: 4})
        self.assertIn(law["seq"], self.delivered_seqs().get("law-inbox", []))

    def test_under_the_shipped_shape_the_law_lane_is_delayed_and_never_shed(self):
        """The shipped policy caps the depth of the ordinary lane and not the law lane, so a
        law-lane delivery under pressure WAITS — it is never dropped. Delay is recoverable;
        a shed delivery is gone."""
        self.set_budget(cycle=1, reserve={push_mod.LAW_LANE: 0},
                        depth={push_mod.ORDINARY_LANE: 5})
        self.flood(15)
        for i in range(6):
            self.law(f"UNSHEDDABLE-{i}")
        self.assertNotIn(push_mod.LAW_LANE, {s["lane"] for s in self.push.shed()},
                         "a law-lane delivery was shed under the shipped depth shape")
        self.assertIn(push_mod.LAW_LANE, {i["lane"] for i in self.push.pending()})

    def test_a_reserve_at_or_above_the_cycle_starves_every_other_lane_and_says_so_first(self):
        """FOUND BY MEASUREMENT, not by reading the code (MEASUREMENTS entry 7, run 1). A reserve
        at or above the cycle budget leaves the general allowance at ZERO, so the ordinary lane
        waits forever — a standing starvation that a flood reveals only after the fact.

        It is NOT refused. Which pairs of values are sane is governance content, and a
        comparison written into the engine would be exactly the constant this EP refuses to
        hold. What the machine owes is that the consequence is READABLE BEFORE IT BITES: the
        allowance is derived and reported beside the values it comes from, so an auditor sees
        `general: 0` without having to run a flood to discover it."""
        self.set_budget(cycle=2, reserve={push_mod.LAW_LANE: 8}, depth={})
        self.assertEqual(self.push.budget()["allowance"],
                         {push_mod.LAW_LANE: 2, "general": 0})
        self.frob(12)
        self.assertEqual(self.push.channels().get("frob-inbox-0", []), [])
        self.assertTrue(self.push.pending())
        # the shipped defaults are not in that state, and that is asserted rather than assumed
        fresh_dir = tempfile.mkdtemp()
        _, _, views, _, _ = build_full_kernel(os.path.join(fresh_dir, "r.jsonl"),
                                              os.path.join(fresh_dir, "blobs"))
        self.assertGreater(views.push.budget()["allowance"]["general"], 0)

    def test_the_engine_reads_the_depth_cap_it_is_given_and_privileges_no_lane_by_name(self):
        """THE COLUMN PROVEN ABLE TO FAIL, and the same row proves something else worth having:
        the law lane is protected by what the RECORD says, not by the engine knowing its name.
        Record a depth cap for the law lane and law deliveries shed — the machine does exactly
        what the policy says, which is what makes the policy load-bearing. A machine that
        refused to shed law would be holding a governance value in code."""
        self.set_budget(cycle=1, reserve={push_mod.LAW_LANE: 0},
                        depth={push_mod.ORDINARY_LANE: 5, push_mod.LAW_LANE: 1})
        self.flood(15)
        for i in range(6):
            self.law(f"SHEDDABLE-{i}")
        self.assertIn(push_mod.LAW_LANE, {s["lane"] for s in self.push.shed()})


# ======================================================================================
# T-SHED-CITES-ITS-POLICY
# ======================================================================================

class TestShedCitesItsPolicy(_LaneWorld):

    def test_every_shed_names_the_rule_that_shed_it(self):
        self.set_budget(cycle=1, reserve={push_mod.LAW_LANE: 0}, depth={push_mod.ORDINARY_LANE: 3})
        self.frob(20)
        shed = self.push.shed()
        self.assertTrue(shed)
        for s in shed:
            self.assertEqual(s["rule_cited"], push_mod.LANE_BUDGET_RULE)
            self.assertEqual(s["policy_key"], push_mod.LANE_BUDGET_KEY)
            self.assertEqual(s["reason"], "depth")
            self.assertEqual(s["limit"], 3)

    def test_every_delay_names_the_rule_that_delayed_it(self):
        self.set_budget(cycle=1, reserve={push_mod.LAW_LANE: 0}, depth={})
        self.frob(6)
        for item in self.push.pending():
            self.assertEqual(item["rule_cited"], push_mod.LANE_BUDGET_RULE)
            self.assertEqual(item["reason"], "cycle-budget")

    def test_a_shed_is_not_a_disappearance_the_record_still_holds_it(self):
        """Shedding a DELIVERY never touches the record. The act is on the record forever; what
        the policy dropped is a derived flow, and the derivation says so."""
        self.set_budget(cycle=1, reserve={push_mod.LAW_LANE: 0}, depth={push_mod.ORDINARY_LANE: 2})
        recs = self.frob(12)
        shed_seqs = {s["record"]["seq"] for s in self.push.shed()}
        self.assertTrue(shed_seqs)
        on_record = {e["seq"] for e in self.store.all()}
        self.assertTrue(shed_seqs <= on_record)
        self.assertTrue(all(r["seq"] in on_record for r in recs))


# ======================================================================================
# T-PUSH-APPENDS-NOTHING — the standing law, re-proven over the new machinery
# ======================================================================================

class TestPushAppendsNothing(_LaneWorld):

    def test_no_delivery_no_shed_and_no_session_push_appends_a_record(self):
        self.set_budget(cycle=2, reserve={push_mod.LAW_LANE: 2}, depth={push_mod.ORDINARY_LANE: 2})
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s", "read_set": ["view:rule-master"]})
        before = len(self.store.all())
        self.frob(10)
        self.law("APPENDS-NOTHING-LAW")
        after = len(self.store.all())
        # exactly eleven records: ten FROBs and one CREATE-RULE. Every delivery, every shed,
        # every session push and every delay added nothing.
        self.assertEqual(after - before, 11)
        self.assertTrue(self.push.shed())
        self.assertTrue(self.push.session_deliveries()["s"])

    def test_kill_every_queue_and_delivery_structure_replay_identical(self):
        self.set_budget(cycle=2, reserve={push_mod.LAW_LANE: 1}, depth={push_mod.ORDINARY_LANE: 6})
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s-rt", "read_set": ["view:rule-master"]})
        self.frob(25)
        self.law("ROUNDTRIP-LAW")
        self.frob(5)

        live = self.push.report()
        # kill EVERYTHING derived — a fresh kernel over the record file alone
        store2, gate2, views2 = build_kernel(self.path)
        replayed = views2.lane_report()
        self.assertEqual(_normalise(live), _normalise(replayed))

    def test_the_worker_is_an_acceleration_of_the_derivation_under_pressure_too(self):
        """The EP-08B lesson: an in-memory acceleration that drifts from its derivation is a
        WRONG acceleration. Under budgets and shedding the two must still agree exactly."""
        self.set_budget(cycle=1, reserve={push_mod.LAW_LANE: 1}, depth={push_mod.ORDINARY_LANE: 4})
        self.frob(15)
        self.law("PRESSURE-LAW")
        self.frob(4)
        self.assertEqual(_normalise(self.push.report()), _normalise(self.views.lane_report()))
        self.assertEqual({c: [r["seq"] for r in rs] for c, rs in self.push.channels().items()},
                         {c: [r["seq"] for r in rs] for c, rs in self.views.queues().items()})

    def test_a_view_amendment_resyncs_the_whole_lane_state_not_just_the_channels(self):
        """R26/B1 extended: a view-definition amendment invalidates deliveries made under the
        old version, and now also the pending set and the shed list."""
        self.set_budget(cycle=2, reserve={push_mod.LAW_LANE: 1}, depth={push_mod.ORDINARY_LANE: 5})
        self.frob(12)
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "frob-watch-0", "when": {"action": "FROB"},
                                                 "then": {"move_to": "frob-inbox-renamed"}})
        self.assertEqual(_normalise(self.push.report()), _normalise(self.views.lane_report()))


def _normalise(report):
    """Compare two lane reports by their record identities, not their object identities."""
    def seqs(items):
        return [(i["lane"], i["record"]["seq"]) for i in items]
    return json.dumps({
        "channels": {c: [r["seq"] for r in rs] for c, rs in sorted(report["channels"].items())},
        "pending": seqs(report["pending"]),
        "shed": [(s["lane"], s["record"]["seq"], s["reason"], s["rule_cited"]) for s in report["shed"]],
        "sessions": {s: [(i["lane"], i["record"]["seq"], sorted(i["reached"]))
                         for i in items] for s, items in sorted(report["sessions"].items())},
    }, sort_keys=True)


# ======================================================================================
# T-SESSION-PUSH-READS-SUBSETS — the EP-24C guard extended into this EP's new dimension
# ======================================================================================

class TestSessionPushReadsSubsets(unittest.TestCase):
    """design/36 ADDENDUM C's rule, applied to what THIS EP put on the gate's per-act path.

    The session reach test runs inside `store._append`'s listener, so it is on the per-act
    path, and it asks a master view its own question twice. EP-24C's guard would catch that if
    it ever saw it — and it cannot: no world under that guard has a live session, so its
    representative acts drive the session branch zero times. A guard that passes because the
    condition never arises has proven nothing about the condition, which is the shape design/36
    ADDENDUM F.1 records as the campaign's own lesson: a derivation can be right about every
    case it considers and silent about the set it ranges over.

    So the guard's own instrument is pointed at the missing case here, reading EP-24C's
    DECLARED tables rather than a copy of them, so this row can never drift from that one.
    """

    def test_a_live_session_on_the_per_act_path_reads_no_whole_record_and_no_undeclared_fold(self):
        sys.path.insert(0, os.path.dirname(__file__))
        from test_ep24c import (_Observer, PER_ACT_PATH_FOLDS,
                                WHOLE_RECORD_ON_PATH_BY_DESIGN)
        d = tempfile.mkdtemp()
        store, gate, views, _, _ = build_full_kernel(os.path.join(d, "r.jsonl"),
                                                     os.path.join(d, "blobs"))
        gate.execute("CREATE-ACCOUNT", OWNER, {"account_id": "ann", "actor_class": "human"})
        gate.execute("GRANT", OWNER, {"grant_id": "g_ann", "grantee": "ann", "actions": "*",
                                      "info": "*", "space": "space:root"})
        # the condition EP-24C's worlds never create: a live session declaring MASTER views,
        # one the law reaches and one it does not, so both branches of the reach test run.
        gate.execute("SESSION-OPEN", OWNER, {"session_id": "s1",
                                             "read_set": ["view:rule-master", "view:actor-master"]})
        with _Observer() as obs:
            gate.execute("CREATE-RULE", "ann", {"rule_id": "law:probe", "policy_key": "k", "value": 3})

        self.assertEqual(sorted(f for f in obs.folds if f not in PER_ACT_PATH_FOLDS), [],
                         "the session reach test put an undeclared fold on the gate's per-act path")
        self.assertEqual({who: n for who, n in obs.raw.items()
                          if who not in WHOLE_RECORD_ON_PATH_BY_DESIGN}, {},
                         "the session reach test read the whole record on the gate's per-act path")
        # and the delivery actually happened, so the clean observation is not clean by absence
        self.assertTrue(views.push.session_deliveries().get("s1"))


# ======================================================================================
# T-NO-SWEEP-INTERLEAVE — design/36 ADDENDUM A.5
# ======================================================================================

class TestNoSweepInterleave(_LaneWorld):

    def test_a_real_sweep_runs_under_the_lanes_and_its_overturns_ride_ordinary(self):
        """The two EPs in the same world for the first time. EP-26's sweep appends one overturn
        per reached act, which is the single largest burst of appends this estate produces —
        and every one of them rides ORDINARY, because an overturn is a DECISION and the sweep
        rather than the lane is its urgency. The worker still equals its derivation afterwards,
        and the live session is told about the LAW and not about six overturns."""
        self.timed_create_rule(carry=("scope",))
        self.gate.execute("CREATE-OP", OWNER, {"name": "SPEND", "definition": {
            "description": "an act decided away from the store and arriving later",
            "params": {"line": "required", "at": "required"}, "law_cited": "CAP-IS-LAW",
            "object_derive": {"tpl": "spend:{line}"}, "occurrence_time_param": "at",
            "payload_from": ["line"], "structural_params": ["line", "at"]}})
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s-sweep",
                                                  "read_set": ["view:rule-master"]})
        at = lambda h, m: f"2026-07-27T{h:02d}:{m:02d}:00.000000+00:00"       # noqa: E731
        for i in range(6):
            self.gate.execute("SPEND", OWNER, {"line": f"l{i}", "at": at(9, 30)})

        law = self.gate.execute("CREATE-RULE", OWNER, {
            "rule_id": "LATE-LAW", "at": at(9, 0), "polarity": "-", "text": "late law",
            "when": [{"action": "SPEND"}], "then": [{"refuse": "LATE-LAW"}]})
        self.assertEqual(len(self.gate.sweeps[-1]["committed"]), 6)

        overturns = [e for e in self.store.all()
                     if (e.get("payload") or {}).get("kind") == "overturn"]
        self.assertEqual({push_mod.lane_of(e) for e in overturns}, {push_mod.ORDINARY_LANE})
        self.assertEqual(_normalise(self.push.report()), _normalise(self.views.lane_report()))
        store2, gate2, views2 = build_kernel(self.path)
        self.assertEqual(_normalise(self.push.report()), _normalise(views2.lane_report()))
        self.assertEqual([i["record"]["seq"] for i in self.push.session_deliveries()["s-sweep"]],
                         [law["seq"]])

    def test_lane_priority_orders_arrivals_it_does_not_interleave_a_sweep(self):
        """The lane reorders which PENDING submission is processed next. It never reaches into
        a running sweep: a law-family submission still travels the serialized door, so a sweep
        in flight holds it until its fixed point."""
        intake = push_mod.LaneIntake(self.gate, self.views)
        self.gate._sweep_active = 1                     # a sweep is running
        try:
            held = intake.submit("CREATE-RULE", OWNER, {"rule_id": "HELD-LAW", "text": "held"})
            intake.submit("FROB", "alice", {})
            drained = intake.drain()
        finally:
            self.gate._sweep_active = 0
        # the law submission was HELD by the sweep's own door, not appended by the lane
        self.assertIsInstance(drained[0], reconcile.Deferred)
        self.assertIsNone(drained[0].record)
        self.assertEqual([e for e in self.store.all()
                          if (e.get("payload") or {}).get("rule_id") == "HELD-LAW"], [])
        self.gate._drain_law_queue()
        self.assertEqual(len([e for e in self.store.all()
                              if (e.get("payload") or {}).get("rule_id") == "HELD-LAW"]), 1)


# ======================================================================================
# T-DEGENERATE-UNCHANGED — the old-ledger side
# ======================================================================================

class TestDegenerateUnchanged(_LaneWorld):

    def test_with_the_shipped_defaults_nothing_that_existed_before_this_EP_moves(self):
        """The shipped budget must not bind on any world the estate already runs. If it did,
        this EP would be a behaviour change wearing a calibration's clothes."""
        self.frob(50)
        self.law("DEGENERATE-LAW")
        self.assertEqual(self.push.pending(), [])
        self.assertEqual(self.push.shed(), [])
        for i in range(self.FANOUT):
            self.assertEqual(len(self.push.channels()[f"frob-inbox-{i}"]), 50)

    def test_the_shipped_defaults_are_read_from_the_record_and_are_generous(self):
        b = self.push.budget()
        self.assertGreaterEqual(b["cycle"], 64)
        self.assertGreaterEqual(b["reserve"][push_mod.LAW_LANE], 1)
        self.assertGreaterEqual(b["depth"][push_mod.ORDINARY_LANE], 1024)


# ======================================================================================
# ADDENDUM 1 — the stale crossing STAYS CALLER-DRIVEN, and the cap is written down here
#
# EP-23 left re-judge as a DRIVER: a stale crossing records its refusal and the remedy runs
# when something calls it. Its builder declined to decide inside a seam EP and named THIS EP
# as the home, because lanes and budgets are where "what runs on its own over the record" gets
# its treatment. EP-27 ADDENDUM 1 requires a stated answer either way with its reason. The
# answer is CALLER-DRIVEN, it is not a preference, and this battery is the answer made
# checkable so a later round cannot wire a beat in without stepping on a red test.
#
# THE DERIVATION, in three steps.
#
#   1. SPLIT THE SEAM. "Is this crossing stale?" and "re-ask it" are two questions, and the
#      addendum's worry — that an unattended crossing stays stale until someone looks — reads
#      as one. Detection is ALREADY record-fired and needs no beat: `stale_crossings` is a pure
#      fold, so a crossing is stale the instant the append that moved its pack lands, whether
#      or not anything runs, and it answers identically to a kernel rebuilt from the record
#      file. What is missing is not computation. It is notification.
#
#   2. TWO SHAPES A BEAT COULD TAKE, AND THEY ARE REFUSED FOR DIFFERENT REASONS. Taking only
#      the first would under-answer the addendum, which points at the obligation executor.
#
#      SHAPE A — the on-append worker, the beat THIS EP owns. Refused structurally, and this
#      one is not a judgment call. `crossing.re_judge` APPENDS: it mints a fresh hand-out
#      through the gate. The worker's founding law is that it appends nothing (I9, the flood
#      boundary this EP re-proves). Firing an appending remedy from inside the append callback
#      makes the worker an appender and makes its cost proportional to what it triggers, in
#      the one place the campaign exists to hold that line.
#
#      SHAPE B — a driver STEP shaped like `obligations.run_due`: not a loop, no clock, reads
#      the record, fires through the gate, invoked from outside any append. That shape does
#      NOT break the flood boundary, so it has to be refused on what it DOES, and it can be.
#      (i)   AN OBLIGATION IS A RECORDED COMMITMENT AND A STALE CROSSING IS NOT. An obligation
#            is a law record saying this WILL happen; `run_due` firing it is the system
#            honouring what the record obliges. `CROSSING-STALE-POLICY` says what MAY happen
#            when an answer RETURNS stale — it is a rule for handling a return, not an
#            instruction to re-ask unprompted. A beat would convert a conditional permission
#            into an obligation, which is law-making by scheduler.
#      (ii)  THE REMEDY'S COST FALLS OUTSIDE THE S-PLANE. `run_due` fires an internal op. A
#            re-judge mints a hand-out that a channel adapter carries to a PERSON. A beat that
#            re-asks whenever the world moves generates human work at machine rate, and under
#            flutter (design/34 §4: a pack whose inputs move faster than answer latency) it
#            does so until the owner's recorded retry budget is gone — turning a design smell
#            the `flutter` view exists to SHOW into expenditure.
#      (iii) THERE IS NO HONEST ACTOR. `run_due` fires as SYSTEM because the commitment is the
#            system's own. A crossing's question belongs to whoever asked it, so a beat records
#            SYSTEM as having asked a question SYSTEM did not ask — the attribution lie the
#            estate refused at EP-05B.
#
#   3. SO THE CAP, NAMED RATHER THAN LEFT AS AN OMISSION: an open crossing whose pack has moved
#      is stale from that append and answerable by anyone, but nothing re-asks it and nothing
#      tells its asker. Both wait for a caller. EP-27 narrows the notification half only for
#      what it covers — a LAW-family record reaching a live session's declared view — and an
#      ordinary record moving a crossing's pack reaches no one. That residue is the last row
#      below, asserted rather than described, because a cap nobody can see is an omission
#      wearing a cap's clothes.
#
# WHAT IS NOT DONE HERE. No beat is built and no scheduler is added; `crossing.py` is outside
# this EP's fence and a step there would be the owner's call, raised and not taken.
# ======================================================================================

_STATION = {
    "description": "ask an executor outside the S-plane to review a budget line",
    "params": {"line": "required"},
    "law_cited": "CAP-IS-LAW",
    "object_derive": {"tpl": "review:{line}"},
    "payload_from": ["line"],
    "structural_params": ["line"],
    "executor": "external",
    "crossing": {"input_view": "view:budget-context",
                 "template": "tpl:budget-review@1.0.0",
                 "answerer_identity": "answerer:approver@1",
                 "parser": "parser:verdict-json@1"},
}


class TestStaleCrossingStaysCallerDriven(unittest.TestCase):

    def setUp(self):
        from kernel import crossing
        self.crossing = crossing
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "r.jsonl")
        self.store, self.gate, self.views, _, _ = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        self.push = self.views.push
        self.gate.execute("CREATE-OP", OWNER, {"name": "SET-BUDGET", "definition": {
            "description": "set a budget line", "params": {"name": "required", "amount": "required"},
            "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "budget:{name}"},
            "payload_from": ["name", "amount"], "structural_params": ["name", "amount"]}})
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "budget-context",
                                                 "when": {"object": "budget:ops"}})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 5})
        self.gate.execute("CREATE-OP", OWNER, {"name": "ASK-REVIEW", "definition": _STATION})
        self.handout = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})

    def handouts(self):
        return [e for e in self.store.all()
                if (e.get("payload") or {}).get("kind") == self.crossing.HANDOUT_KIND]

    def move_the_pack(self, amount=6):
        return self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": amount})

    def test_the_append_that_makes_a_crossing_stale_re_judges_nothing(self):
        """The decision, made structural. The append moves the pack, the worker runs on that
        append, and what it produces is: one record, no hand-out, no remedy."""
        self.assertTrue(self.crossing.fingerprint(self.store, self.views,
                                                  self.handout["seq"])["holds"])
        before = len(list(self.store.all()))
        self.move_the_pack()
        self.assertEqual(len(list(self.store.all())), before + 1,
                         "the append that made a crossing stale produced exactly itself — a "
                         "worker that re-judged would show a second record here")
        self.assertEqual(len(self.handouts()), 1, "no fresh hand-out was minted by any beat")
        self.assertIn(self.handout["seq"],
                      self.crossing.stale_crossings(self.store, self.views))

    def test_detection_needs_no_beat_because_it_is_a_fold_over_the_record(self):
        """Kill the whole composed kernel, rebuild from the record file alone, and the crossing
        is stale there too. Staleness is not something that has to be noticed."""
        self.move_the_pack()
        live = set(self.crossing.stale_crossings(self.store, self.views))
        store2, _, views2 = build_kernel(self.path)
        self.assertEqual(set(self.crossing.stale_crossings(store2, views2)), live)
        self.assertIn(self.handout["seq"], live)

    def test_the_remedy_is_available_and_a_caller_is_what_takes_it(self):
        """The row above must not pass because re-judging is impossible. It is possible, the
        recorded policy permits it, the budget is unspent — and it did not happen."""
        self.move_the_pack()
        rs = self.crossing.retry_state(self.store, self.views, self.handout["seq"])
        self.assertEqual(rs["policy"], "re-judge")
        self.assertEqual(rs["spent"], 0)
        self.assertTrue(rs["may_re_judge"], "the remedy was available and nothing took it")
        fresh = self.crossing.re_judge(self.gate, self.store, self.views, OWNER,
                                       self.handout["seq"])
        self.assertIsNotNone(fresh)
        self.assertEqual(len(self.handouts()), 2)
        self.assertEqual(dict(fresh["payload"])["parent_handout_seq"], self.handout["seq"])

    def test_an_ordinary_record_moving_the_pack_tells_no_live_session_and_that_is_the_cap(self):
        """THE RESIDUE, asserted. The session push fires on the LAW lane, so a session that
        declared the crossing's own pack hears nothing when an ordinary act moves it. The
        contrast row proves the machinery is working and the silence is the boundary rather
        than a defect: a law-family record reaching a declared view is delivered."""
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "law-watch",
                                                 "when": {"action": "CREATE-RULE"}})
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s-asker",
                                                  "read_set": ["view:budget-context"]})
        self.gate.execute("SESSION-OPEN", OWNER, {"session_id": "s-law",
                                                  "read_set": ["view:law-watch"]})
        self.move_the_pack()
        self.assertIn(self.handout["seq"],
                      self.crossing.stale_crossings(self.store, self.views))
        self.assertEqual(self.push.session_deliveries().get("s-asker", []), [],
                         "an ordinary act moved the pack a session declared, and the session "
                         "was told nothing — the named cap, not a defect")
        law = self.gate.execute("CREATE-RULE", OWNER, {"rule_id": "SOME-LAW", "text": "law"})
        self.assertEqual([i["record"]["seq"] for i in self.push.session_deliveries()["s-law"]],
                         [law["seq"]])
        self.assertEqual(self.push.session_deliveries().get("s-asker", []), [])

    def test_the_column_can_fail_a_beat_in_the_append_path_shows_every_cost_at_once(self):
        """PROVE THE ROWS ABOVE ARE WATCHING FOR SOMETHING. A beat is built here — shape A,
        the on-append listener, because it is the one this EP could actually have written —
        and the guards above go red against it.

        Shape A's own defect shows first: THE WORKER BECOMES AN APPENDER, so four ordinary
        acts produce more than four records. The rest of what this run shows is not specific
        to shape A and is the evidence against shape B as well, because a `run_due`-shaped
        step firing the same remedy on the same record would produce it identically:
          - THE OWNER'S BUDGET IS SPENT UNASKED. The recorded retry budget of 2 is exhausted
            by ordinary traffic, the crossing lands on `needing_reask` — the HUMAN queue — and
            `flutter`, the view whose whole job is to make an over-broad pack visible, reports
            the churn the beat manufactured while consuming it. Every one of those re-asks is
            work handed to a person outside the S-plane.
          - THE ATTRIBUTION IS A LIE. Every machine-minted hand-out records SYSTEM as having
            asked a question SYSTEM did not ask.

        Nothing is installed outside this method: the beat lives and dies inside the test."""
        def beat(_record):
            for seq in list(self.crossing.stale_crossings(self.store, self.views)):
                self.crossing.re_judge(self.gate, self.store, self.views, "SYSTEM", seq)
        self.store.on_append(beat)

        before = len(list(self.store.all()))
        self.move_the_pack(6)
        # (a) — the guard row above asserts exactly +1 here, and with a beat it is more
        self.assertGreater(len(list(self.store.all())), before + 1)
        for amount in (7, 8, 9):
            self.move_the_pack(amount)

        minted = self.handouts()[1:]
        self.assertTrue(minted, "the beat should have minted hand-outs — otherwise this row "
                                "proves nothing about the rows above")
        self.assertEqual({e["actor"] for e in minted}, {"SYSTEM"})            # (c)
        newest = self.handouts()[-1]["seq"]
        rs = self.crossing.retry_state(self.store, self.views, newest)
        self.assertEqual(rs["remaining"], 0)                                   # (b)
        self.assertIn(newest, self.crossing.needing_reask(self.store, self.views))
        self.assertEqual(self.crossing.flutter(self.store).get("ASK-REVIEW"), len(minted))


if __name__ == "__main__":
    unittest.main()
