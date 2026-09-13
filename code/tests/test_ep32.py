"""EP-32 (BUILD) — M7: GOVERN THE SCHEDULER AT THE METAL. The battery + the red worlds.

design/10 §4 is the scheduling row catalogue, entire: policy = LAW; admit/block/wake/reap/halt/kill
= DECISION; ticks + wake-causing arrivals = INPUT; runnable-set / clock reads = CACHE; sched_yield +
per-tick dispatch = STREAM. THE CLOCK IS A SENSOR — replay never consults the wall clock.

THE ONE SENTENCE: the scheduler is the LAST assume and the STRICTEST, because a real-time promise is
a TEMPORAL identity, not only a semantic one — governance must hold the deadline without recording
per-dispatch, proven by RATE, not by luck.

SPLIT (host vs guest/MAX). Everything here runs on the HOST at the record/model level. Three items
are the guest / gov-builder-max dispatch and are NOT done here: A4's T-REALTIME-BOUND MEASUREMENT
(value + margin on the validation kernel), A5's records-per-dispatch MEASUREMENT at real rate under a
kernel dispatch storm, and A7's full kernel-replaced conformance run on BOTH kernels. This file
builds the FRAMES (rt_dispatch, records_per_dispatch, the classification, the carve-out) and drives
their STRUCTURAL shape and their teeth (R1-R5); it does NOT boot the guest and produces no on-metal
figure. The real-time ASSUME does not flip on this seat's word — the owner reads the measured margin.

NO LAW IS CREATED. All five SCHED-LAW (ADMIT/ORDER/PRIORITY/HALT/KILL-CHAIN) are LIVE DANGLES and
HELD OWNER-GATES — a create needs the owner's word (stop condition 3). THE WRONG-REFERENCE TRAP: the
five are cited on the founding pack's `law_cited` surface, NOT on cite/rule_cited — read the wrong
surface and they look like forecast (the two-surface slip C6's builder caught for comms).

MODE: every verdict here is DRIVEN (a command over the tree), never READ.
"""

import copy
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, _HERE)                                    # so `import era_pin` resolves (EP-28Z)

from kernel.boot import build_kernel  # noqa: E402
from observe.classmap import DECISION, LAW, INPUT, CACHE, STREAM  # noqa: E402
import subsystems.scheduling as S  # noqa: E402
from subsystems.scheduling import (  # noqa: E402
    SchedulingView, classify, RECORDED, SCHED_LAW_FAMILY, LANE_SCHEDULING, THREAD_SCHEDULING,
    is_scheduling_record,
)
from founding.install import (  # noqa: E402
    load_pack, records as pack_records, founding_version,
)
from era_pin import pack_at  # noqa: E402


def created_rules(recs):
    """The rule_ids the pack CREATES (a CREATE-RULE record declares one)."""
    return {r["payload"]["rule_id"] for r in recs if r.get("action") == "CREATE-RULE"}


def law_cited_surface(recs):
    """The set of law names cited on the `law_cited` surface of op DEFINITIONS — the surface the
    authoring drive MISSED (it read only cite/rule_cited). THE NAMED WRONG-REFERENCE TRAP: the five
    SCHED-LAW live here, not on cite/rule_cited, so reading the wrong surface reports them forecast."""
    cited = set()
    for r in recs:
        d = (r.get("payload") or {}).get("definition") or {}
        if d.get("law_cited"):
            cited.add(d["law_cited"])
    return cited


def sched_ops_and_the_law_each_cites(recs):
    """{op name -> law_cited} for every shipped op citing a SCHED-LAW — the countersign's driven
    fact that SIX ops cite the five laws (live dangles), read off the law_cited surface."""
    out = {}
    for r in recs:
        pl = r.get("payload") or {}
        d = (pl.get("definition") or {})
        if r.get("action") == "CREATE-OP" and str(d.get("law_cited", "")).startswith("SCHED-LAW"):
            out[pl["name"]] = d["law_cited"]
    return out


class _Sched(unittest.TestCase):
    """A booted kernel + scheduling view over a fresh record."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)
        self.sv = SchedulingView(self.store)

    def admit(self, proc, **kw):
        return self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": proc, **kw})

    def block(self, proc, cause):
        return self.gate.execute("DESCHEDULE", "SYSTEM", {"proc": proc, "cause": cause})

    def wake(self, proc, cause):
        return self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": proc, "wake_cause": cause})


# ---------------------------------------------------------------------------------------
# A1 — DRIVEN. The classification (design/10 §4). Clock a SENSOR; lanes and threads apart.
# ---------------------------------------------------------------------------------------
class A1_SchedulingEventsClassified(_Sched):
    def test_a1_every_event_lands_to_its_class_per_design10_sec4(self):
        self.assertEqual(classify("sched-setscheduler"), LAW)      # policy — the clearest LAW
        self.assertEqual(classify("sched-setaffinity"), LAW)
        self.assertEqual(classify("set-priority"), LAW)            # nice/setpriority — LAW-derived
        self.assertEqual(classify("admit"), DECISION)
        self.assertEqual(classify("block"), DECISION)
        self.assertEqual(classify("wake"), DECISION)               # DECISION — see the carve-out (A3)
        self.assertEqual(classify("reap"), DECISION)
        self.assertEqual(classify("halt"), DECISION)
        self.assertEqual(classify("kill"), DECISION)
        self.assertEqual(classify("timer-tick"), INPUT)
        self.assertEqual(classify("timer-expiry"), INPUT)
        self.assertEqual(classify("wake-causing-arrival"), INPUT)
        self.assertEqual(classify("runnable-set-read"), CACHE)
        self.assertEqual(classify("clock-read"), CACHE)            # THE CLOCK IS A SENSOR
        self.assertEqual(classify("sched-yield"), STREAM)
        self.assertEqual(classify("per-tick-dispatch"), STREAM)

    def test_a1_only_decision_and_law_events_record(self):
        # the scheduler appends for DECISION/LAW; the tick, the clock read, the dispatch record
        # NOTHING (the INPUT arrival is recorded by the device/time subsystem, not the scheduler).
        self.assertTrue(RECORDED["admit"] and RECORDED["set-priority"] and RECORDED["kill"])
        self.assertFalse(RECORDED["timer-tick"] or RECORDED["clock-read"]
                         or RECORDED["sched-yield"] or RECORDED["per-tick-dispatch"])

    def test_a1_the_behaviour_matches_the_table(self):
        # DECISION/LAW ops append exactly one record each; reading the runnable set and dispatching
        # append NONE (the clock-as-sensor / STREAM point).
        n = len(self.store.all())
        self.admit("p1")                                                        # DECISION (admit)
        self.gate.execute("SET-PRIORITY", "SYSTEM", {"proc": "p1", "priority": "high"})  # LAW
        self.block("p1", "wait:io")                                             # DECISION (block)
        self.gate.execute("SCHED-KILL", "SYSTEM", {"proc": "p1", "reason": "policy"})     # DECISION
        self.assertEqual(len(self.store.all()) - n, 4)                          # four acts, four records
        n = len(self.store.all())
        self.admit("p2")
        for _ in range(500):
            self.sv.runnable()                                                  # CACHE read — records nothing
        S.dispatch_storm(self.store, {"p2": "normal"}, 500)                     # STREAM — records nothing
        self.assertEqual(len(self.store.all()) - n, 1)                          # only the admit recorded

    def test_a1_lanes_and_threads_named_apart(self):
        # EP-27 lane priority (record-processing) and thread priority (CPU) are DISTINCT — neither
        # impersonates the other. They share only the word "priority".
        self.assertNotEqual(LANE_SCHEDULING, THREAD_SCHEDULING)
        self.assertIn("EP-27", LANE_SCHEDULING)
        self.assertIn("THIS subsystem", THREAD_SCHEDULING)


# ---------------------------------------------------------------------------------------
# A2 — DRIVEN. T-TICKS-ARE-INPUT — the clock is a sensor.
# ---------------------------------------------------------------------------------------
class A2_TicksAreInput(_Sched):
    def test_a2_replay_reconstructs_dispatch_from_recorded_ticks_no_clock_read(self):
        runnable = {"rt": "rt", "web": "normal", "idle": "idle"}
        ticks = [10, 20, 30, 40]
        clk = S.Sensor(1000)
        seq1 = S.dispatch_sequence(runnable, ticks)     # dispatch never reads clk
        clk.set(999999999)
        seq2 = S.dispatch_sequence(runnable, ticks)
        self.assertEqual(seq1, seq2)                    # clock-independent -> reconstructs identically
        self.assertEqual(seq1, ["rt", "rt", "rt", "rt"])  # highest priority runnable, from LAW + ticks

    def test_a2_dispatch_records_nothing(self):
        self.admit("p1")
        before = len(self.store.all())
        S.dispatch_sequence({"p1": "normal"}, range(2000))
        self.assertEqual(len(self.store.all()), before)

    def test_a2_priority_is_law_derived_never_a_poked_status(self):
        # priority comes from admit / SET-PRIORITY DECISIONS (LAW-derived) and reconstructs on replay
        # — never a poked mutable field.
        self.admit("p1", priority="normal")
        self.gate.execute("SET-PRIORITY", "SYSTEM", {"proc": "p1", "priority": "high"})
        self.assertEqual(self.sv.runnable()["p1"]["priority"], "high")
        store2, _, _ = build_kernel(self.record)
        self.assertEqual(SchedulingView(store2).runnable()["p1"]["priority"], "high")


# ---------------------------------------------------------------------------------------
# A3 — DRIVEN. THE WAKE CARVE-OUT, discovered by the scheduling T-CACHE-KILL.
# ---------------------------------------------------------------------------------------
class A3_WakeCarveoutByCacheKill(_Sched):
    """A wake whose cause is a RECORDED input RECONSTRUCTS (fill); a wake whose cause is UNAUDITED
    (futex) does NOT reconstruct and the row REDS — so it correctly keeps DECISION class. Discovered
    by the test, never applied by authoring judgment (stop condition 5)."""

    def _two_wakes(self):
        self.admit("rt", priority="rt")
        self.block("rt", "wait:timer:t7")
        self.wake("rt", "timer:t7")                     # recorded-cause wake (the RT case)
        self.admit("fx", priority="normal")
        self.block("fx", "wait:futex:0xabc")
        self.wake("fx", "futex:0xabc")                  # unaudited-cause wake (§4.5)
        return S._events(self.store), {"timer:t7"}      # the device recorded the timer, NOT the futex

    def test_a3_recorded_cause_reconstructs_unaudited_does_not(self):
        ev, RI = self._two_wakes()
        full = S.runqueue(ev)
        self.assertEqual(full, {"rt", "fx"})
        # NAIVE all-fills reconstruction: the timer wake reconstructs, the futex wake does NOT.
        naive = S.reconstruct_runqueue(ev, RI, treat_every_wake_as_fill=True)
        self.assertIn("rt", naive)                      # recorded-cause wake: a genuine FILL
        self.assertNotIn("fx", naive)                   # unaudited-cause wake: does NOT reconstruct
        self.assertNotEqual(naive, full)                # the row REDS if the futex is called a fill

    def test_a3_the_classified_reconstruction_matches_the_full_fold(self):
        ev, RI = self._two_wakes()
        classified = S.reconstruct_runqueue(ev, RI, treat_every_wake_as_fill=False)
        self.assertEqual(classified, S.runqueue(ev))    # keep unaudited wakes as decisions -> exact

    def test_a3_the_class_is_discovered_by_the_test_not_authored(self):
        ev, RI = self._two_wakes()
        self.assertEqual(S.wake_class(ev, RI), {"timer:t7": "FILL", "futex:0xabc": "DECISION"})


# ---------------------------------------------------------------------------------------
# A4 — DRIVEN (the FRAME). T-REALTIME-BOUND — the MEASUREMENT is the guest / MAX dispatch.
# ---------------------------------------------------------------------------------------
class A4_RealtimeBoundFrame(_Sched):
    """BUILT HERE: the RT dispatch FRAME (rt_dispatch) — deterministic, records nothing. NOT built
    here: the timing bound's MEASURED value + margin on the validation kernel — owner-ruled MAX
    tier, guest dispatch, deferred. THE ASSUME DOES NOT FLIP ON THIS SEAT (EP-32 §8 stop 2): the
    close files the margin and the OWNER reads it first."""

    def test_a4_frame_is_deterministic_and_records_nothing(self):
        rt = {"a": {"policy": "SCHED_FIFO", "rt_priority": 10},
              "b": {"policy": "SCHED_FIFO", "rt_priority": 20},
              "c": {"policy": "SCHED_OTHER"}}
        before = len(self.store.all())
        pick1 = S.rt_dispatch(rt, "SCHED_FIFO")
        pick2 = S.rt_dispatch(rt, "SCHED_FIFO")
        self.assertEqual(pick1, pick2)                  # deterministic — the bound cannot be met by luck
        self.assertEqual(pick1, "b")                    # strict highest rt_priority
        self.assertEqual(len(self.store.all()), before)  # records NOTHING (STREAM)

    def test_a4_deadline_frame_picks_earliest_deadline_edf(self):
        rt = {"x": {"policy": "SCHED_DEADLINE", "deadline": 50},
              "y": {"policy": "SCHED_DEADLINE", "deadline": 30}}
        self.assertEqual(S.rt_dispatch(rt, "SCHED_DEADLINE"), "y")   # EDF

    def test_a4_non_rt_tasks_are_not_rt_dispatched(self):
        self.assertIsNone(S.rt_dispatch({"z": {"policy": "SCHED_OTHER"}}, "SCHED_FIFO"))


# ---------------------------------------------------------------------------------------
# A5 — DRIVEN (the FRAME). THE MAX CRUX — records-per-dispatch FALLS at rate.
# ---------------------------------------------------------------------------------------
class A5_RecordsPerDispatchFrame(_Sched):
    """BUILT HERE: the records-per-dispatch FRAME and its STRUCTURAL shape (the falsifiable form).
    NOT built here: the MEASUREMENT at real dispatch rates under a kernel dispatch storm — owner-ruled
    MAX tier, guest dispatch, deferred. Stop condition 4: a flat/rising ratio at the metal is the
    durability-vs-real-time tension — STOP, not tune."""

    def _dispatch_phase_records(self, n):
        self.admit("p1")
        return S.dispatch_storm(self.store, {"p1": "normal"}, n)

    def test_a5_frame_dispatch_phase_records_nothing(self):
        self.assertEqual(self._dispatch_phase_records(2000), 0)

    def test_a5_frame_ratio_falls_toward_the_floor_as_rate_rises(self):
        for n in (100, 1000, 10000):
            self.setUp()
            self.assertEqual(self._dispatch_phase_records(n), 0)  # 0 at every rate -> at the floor

    def test_a5_decision_bound_ratio_strictly_falls(self):
        ratios = []
        for n in (100, 1000):
            self.setUp()
            self.admit("p1")                            # D counted: the admit decision (dispatch adds none)
            d = len(self.store.all())
            S.dispatch_storm(self.store, {"p1": "normal"}, n)
            self.assertEqual(len(self.store.all()), d)  # nothing added by the dispatches
            ratios.append(S.records_per_dispatch(d, n))
        self.assertLess(ratios[1], ratios[0])           # records/dispatch = D/N falls toward the floor


# ---------------------------------------------------------------------------------------
# A6 — DRIVEN. The five SCHED-LAW, all held owner-gates (the wrong-reference trap driven).
# ---------------------------------------------------------------------------------------
class A6_FiveSchedLawsHeldGates(_Sched):
    def test_a6_five_laws_cited_on_the_law_cited_surface_not_cite_or_rule_cited(self):
        cited = law_cited_surface(pack_records(load_pack()))
        self.assertTrue(set(SCHED_LAW_FAMILY) <= cited,
                        "a SCHED-LAW is missing from the law_cited surface: %s"
                        % (set(SCHED_LAW_FAMILY) - cited))

    def test_a6_six_shipped_ops_cite_the_five_they_are_live_dangles_not_forecast(self):
        self.assertEqual(sched_ops_and_the_law_each_cites(pack_records(load_pack())), {
            "SCHED-ADMIT": "SCHED-LAW-ADMIT", "DESCHEDULE": "SCHED-LAW-ORDER",
            "SET-PRIORITY": "SCHED-LAW-PRIORITY", "SCHED-HALT": "SCHED-LAW-HALT",
            "SCHED-RESUME": "SCHED-LAW-HALT", "SCHED-KILL": "SCHED-LAW-KILL-CHAIN"})

    def test_a6_none_of_the_five_is_created_all_held(self):
        created = created_rules(pack_records(load_pack()))
        for law in SCHED_LAW_FAMILY:
            self.assertNotIn(law, created, "%s was created — it is a HELD owner-gate (R4)" % law)

    def test_a6_the_five_are_not_active_rules_a_citation_to_an_uncreated_law(self):
        # cited-but-uncreated -> not an active rule (a LIVE DANGLE). A decision citing it names a law
        # the founding does not yet CONTAIN — which is exactly why the gate is HELD for the owner.
        active = self.views.active_rules()
        for law in SCHED_LAW_FAMILY:
            self.assertNotIn(law, active)


# ---------------------------------------------------------------------------------------
# A8 — DRIVEN. The §A57 era-pin sweep — no law created, so no sweep; the mechanism is R5.
# ---------------------------------------------------------------------------------------
#: EP-32's era — the commit at which this suite first landed. EP-32 minted NO SCHED-LAW (all five held
#: owner-gates), so the founding did not move and stayed at EP-31's landing 1.31.0. A8's two version
#: assertions are stored copies of that computable value (the estate's named class, test_ep26:1234) and
#: read THIS era rather than the live tree, so a later lawful bump (EP-35's 1.31.0 -> 1.32.0 era boundary)
#: no longer reds a claim that was only ever about EP-32's own window.
EP32_ERA_COMMIT = "cb1bde1f50d3010b00e931d550d3722048b1b1e5"


class A8_A57EraPinSweep(unittest.TestCase):
    """§A57: any SCHED-LAW this build creates would red downstream version/dangle pins, swept to
    pack_at(era). THIS build creates NO SCHED-LAW (all five held), so NO sweep is performed and the
    founding_version does NOT move. A8 asserts the no-op is HONEST; R5 exhibits the sweep MECHANISM
    on a copy."""

    def test_a8_no_sched_law_created_so_no_sweep_and_version_unmoved(self):
        created = created_rules(pack_records(load_pack()))
        self.assertEqual([l for l in created if l.startswith("SCHED-LAW")], [])   # nothing created
        # [DOCUMENTED FLIP — MAINT-EP31-32-VERSION-REPIN, 2026-09-03, §A57 (board :2772, AUTHORISED-BY
        # :2761). Was `founding_version()` LIVE == "1.31.0"; EP-35's lawful 1.31.0 -> 1.32.0 era boundary
        # reddened a claim about EP-32's OWN window. Now reads EP-32's era (EP32_ERA_COMMIT), where the
        # founding was 1.31.0 — EP-32 minted no law and moved it not. The subject is unchanged.]
        self.assertEqual(pack_at(EP32_ERA_COMMIT)["founding_version"], "1.31.0")   # EP-32's era; minted no law

    def test_a8_the_era_pin_tool_is_the_sweep_instrument(self):
        # the sweep reads a NAMED COMMIT's pack, never the live tree — pack_at is that instrument.
        # [DOCUMENTED FLIP — MAINT-EP31-32-VERSION-REPIN, 2026-09-03, §A57. Was `pack_at("HEAD")` — the
        # LIVE tree, which this row's own comment says the instrument must NOT read; EP-35's 1.31.0 ->
        # 1.32.0 bump reddened it. Now reads a genuinely NAMED commit (EP32_ERA_COMMIT, EP-32's era at
        # 1.31.0), which is what "reads a NAMED COMMIT's pack, never the live tree" always meant.]
        self.assertEqual(pack_at(EP32_ERA_COMMIT)["founding_version"], "1.31.0")


# =======================================================================================
# RED WORLDS — mandatory, never empty. Each drives BOTH verdicts through the instrument.
# =======================================================================================
class R1_TheWakeCarveoutBites(_Sched):
    """Classify a futex (unaudited-cause) wake as a FILL and A3's T-CACHE-KILL REDS: the event
    vanishes and the runqueue does not reconstruct. Restore DECISION class: green. The event must
    not be classifiable away."""

    def _futex_wake(self):
        self.admit("fx", priority="normal")
        self.block("fx", "wait:futex:0xabc")
        self.wake("fx", "futex:0xabc")
        return S._events(self.store), {"timer:t7"}      # futex NOT recorded (unaudited §4.5)

    def test_r1_calling_the_futex_wake_a_fill_reds_keeping_it_a_decision_greens(self):
        ev, RI = self._futex_wake()
        full = S.runqueue(ev)
        as_fill = S.reconstruct_runqueue(ev, RI, treat_every_wake_as_fill=True)   # PLANT
        self.assertNotEqual(as_fill, full)              # fx vanishes -> REDS
        self.assertNotIn("fx", as_fill)
        kept = S.reconstruct_runqueue(ev, RI, treat_every_wake_as_fill=False)     # RESTORE
        self.assertEqual(kept, full)                    # keep it a decision -> reconstructs -> green
        self.assertIn("fx", kept)


class R2_TheScalingTestCanFail(_Sched):
    """Force records-per-dispatch to NOT fall — record per dispatch — and the ratio floors at >=1
    instead of tending to 0. Restore pure-STREAM dispatch and it falls. The falsifiable form: the
    architecture's central claim where it can lose (stop condition 4)."""

    def _ratio(self, dispatch_fn, n):
        self.setUp()
        self.admit("p1")
        before = len(self.store.all())
        for _ in range(n):
            dispatch_fn("p1")
        return (len(self.store.all()) - before) / n

    def _recording_dispatch(self, proc):
        # the WRONG frame: a "dispatch" that appends a record per tick (per-dispatch journalling —
        # the named wrong reference). A planted bad path, never scheduling.py's real dispatch.
        self.gate.execute("SET-PRIORITY", "SYSTEM", {"proc": proc, "priority": "normal"})

    def _pure_dispatch(self, proc):
        S.dispatch_sequence({proc: "normal"}, [1])      # STREAM: records nothing

    def test_r2_recording_per_dispatch_floors_the_ratio_pure_stream_falls(self):
        for n in (100, 1000):
            self.assertGreaterEqual(self._ratio(self._recording_dispatch, n), 1.0)  # floors at >=1 -> REDS
        self.assertEqual(self._ratio(self._pure_dispatch, 100), 0.0)                # at the floor -> green
        self.assertEqual(self._ratio(self._pure_dispatch, 1000), 0.0)


class R3_ClockAsSchedulerIsRefused(_Sched):
    """Make replay consult the wall clock for a dispatch and A2 REDS — the sequence stops being a
    function of recorded inputs alone, so two replays at different clock values DIVERGE. Restore the
    sensor discipline (dispatch reads recorded ticks, never the clock): green. Ban 15.1."""

    def _clock_dispatch(self, runnable, ticks, clk):
        # PLANT: a dispatch that reads the wall clock to pick — the clock-as-scheduler ban.
        order = sorted(runnable)
        return [order[clk.now() % len(order)] for _ in ticks] if order else []

    def test_r3_clock_read_diverges_sensor_discipline_reconstructs(self):
        runnable = {"a": "normal", "b": "normal", "c": "normal"}
        ticks = [1, 2, 3]
        clk = S.Sensor(0)
        s1 = self._clock_dispatch(runnable, ticks, clk)
        clk.set(1)
        s2 = self._clock_dispatch(runnable, ticks, clk)
        self.assertNotEqual(s1, s2)                     # clock-reading dispatch -> diverges -> REDS
        clk.set(0)
        g1 = S.dispatch_sequence(runnable, ticks)
        clk.set(1)
        g2 = S.dispatch_sequence(runnable, ticks)
        self.assertEqual(g1, g2)                        # recorded-tick dispatch -> identical -> green


class R4_AnUngatedSchedLawCreateIsRefused(unittest.TestCase):
    """The held gate is MECHANICAL, not a note. NO SCHED-LAW is granted this build, so a guard that
    reds if ANY SCHED-LAW is created IS the gate: the real pack greens (all five held); plant a
    SCHED-LAW create and it reds. No scheduling law is minted on a seat's word (stop condition 3)."""

    def _no_sched_law_created(self, recs):
        return [l for l in created_rules(recs) if l.startswith("SCHED-LAW")] == []

    def test_r4_planted_sched_law_create_reds_real_pack_greens(self):
        self.assertTrue(self._no_sched_law_created(pack_records(load_pack())))   # real pack -> all held
        planted = copy.deepcopy(load_pack())
        planted["steps"][-1]["records"].append({
            "actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": "SCHED-LAW-ADMIT",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "SCHED-LAW-ADMIT", "text": "ungated create",
                        "scope": "space:root"}})
        self.assertFalse(self._no_sched_law_created(pack_records(planted)))       # planted -> REDS


class R5_ALawCreatedWithoutItsA57SweepRedsDownstream(unittest.TestCase):
    """A created law reds downstream version/dangle pins until they are era-pinned (charter §A57;
    EP-31's lesson, board :2662). This build creates NO SCHED-LAW, so the mechanism is exhibited on
    a COPY: plant a SCHED-LAW-ADMIT create; a downstream DANGLE PIN (asserting SCHED-LAW-ADMIT is
    still a dangle) REDS against the mutated pack; era-pinning to pack_at(pre-create commit) greens
    it. The backward-obligation is MECHANICAL, not a note (R5, A8)."""

    def _dangle_pin_holds(self, recs):
        # a downstream pin: SCHED-LAW-ADMIT is cited but NOT created (a live dangle).
        return "SCHED-LAW-ADMIT" not in created_rules(recs)

    def test_r5_planted_create_reds_the_pin_era_sweep_greens(self):
        self.assertTrue(self._dangle_pin_holds(pack_records(load_pack())))       # live: still a dangle
        planted = copy.deepcopy(load_pack())
        planted["steps"][-1]["records"].append({
            "actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": "SCHED-LAW-ADMIT",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "SCHED-LAW-ADMIT", "text": "ungated create (copy only)",
                        "scope": "space:root"}})
        self.assertFalse(self._dangle_pin_holds(pack_records(planted)))          # create -> pin REDS
        # SWEEP: read the pack AS IT STOOD AT THE PRE-CREATE ERA (HEAD), where it is still a dangle.
        self.assertTrue(self._dangle_pin_holds(pack_records(pack_at("HEAD"))))   # era-pinned -> green


# ---------------------------------------------------------------------------------------
# K12 (design/36 ADDENDUM S) — the scheduling read paths cost their family, not the stream.
# MAINT-K12-FAMILY-INDEX: runnable()/halted() read the scheduling family through a held
# RecordProjection. The projection holds locations, never answers, so killing it changes nothing.
# ---------------------------------------------------------------------------------------
class K12_FamilyProjection(_Sched):

    def test_runnable_reads_its_family_not_unrelated_records(self):
        self.admit("p1")
        self.admit("p2")
        for i in range(200):                                   # records the answer does not read
            self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:%d" % i, "content": "x"})
        self.assertEqual(sorted(self.sv.runnable()), ["p1", "p2"])   # answer unchanged by the noise
        # the fold iterates the two SCHED-ADMIT records, not the 202-record stream
        self.assertEqual(len(self.sv._records.all()), 2)
        self.assertTrue(all(is_scheduling_record(e) for e in self.sv._records.all()))

    def test_kill_the_projection_replay_from_the_record_alone_is_identical(self):
        self.admit("p1", priority="high")
        self.admit("p2")
        self.block("p2", "wait:timer:t7")
        before = self.sv.runnable()
        self.sv._records.kill()                                # T-ACCELERATION-IS-DERIVED
        self.assertEqual(self.sv.runnable(), before)           # rebuilt from the record, identical
        self.assertEqual(SchedulingView(self.store).runnable(), before)  # a fresh view agrees


if __name__ == "__main__":
    unittest.main()
