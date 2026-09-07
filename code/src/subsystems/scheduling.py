# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS scheduling subsystem — the governed core (design/03 §4.1; design/10 §4).

Attention as governed record: admit / deschedule / set-priority / halt / resume / kill
are recorded, rule-cited DECISIONs against a scheduling policy (LAW). The runnable set,
each task's state, and the halt state are derived views. DISPATCH (which runnable task
the CPU picks per tick) is NOT recorded — it is a pure function of policy + admissions +
inputs (STREAM), so the schedule replays exactly and "why did this run" is answerable
forever, the audit a conventional scheduler loses a tick later. No drivers.

M7 (design/10 §4, EP-32) — THE SCHEDULER IS THE LAST ASSUME AND THE STRICTEST, because a
real-time promise is a TEMPORAL identity, not only a semantic one. Everywhere else the port
promises the same ANSWER; here it also promises the same DEADLINE, and governance must hold
the deadline without recording per-dispatch — proven by RATE, not by luck. This module builds
the HOST-buildable core and the frames the guest / MAX-tier dispatch measures:

  - the design/10 §4 event classification (EVENT_CLASS): sched policy = LAW; admit/block/wake/
    reap/halt/kill = DECISION; ticks + wake-causing arrivals = INPUT; runnable-set / clock reads
    = CACHE; sched_yield + per-tick dispatch = STREAM. THE CLOCK IS A SENSOR — replay never
    consults the wall clock (T-TICKS-ARE-INPUT; ban 15.1);
  - THE WAKE CARVE-OUT, discovered by the scheduling T-CACHE-KILL and never by judgment
    (`reconstruct_runqueue`): a wake whose cause is a RECORDED input (interrupt, timer — the RT
    cases) is a FILL that reconstructs; a wake whose cause is UNAUDITED (a futex word, §4.5)
    keeps DECISION class because the decision is the event's only record-visible trace;
  - the T-REALTIME-BOUND FRAME (`rt_dispatch`) — the code path whose measured latency and margin
    the guest / MAX dispatch reads; the assume does NOT flip on this seat's word;
  - the records-per-dispatch FRAME (`records_per_dispatch`, `dispatch_storm`) — the falsifiable
    form the MAX dispatch measures at real rate: records-per-dispatch FALLS toward the floor.

Note: the real-time timing guarantee (T-REALTIME-BOUND, owner ruling 2026-07-13) is measured on
the validation kernel in the GUEST — a SEPARATE gov-builder-max dispatch. This core carries the
governed decisions and the derived queue it will be measured against; it MEASURES nothing.
"""

# The scheduling core op definitions (SCHED-ADMIT / DESCHEDULE / SET-PRIORITY / SCHED-HALT /
# SCHED-RESUME / SCHED-KILL) and their law-name constants were RETIRED here in EP-14B: their one
# authoritative home is the founding pack, founding/founding-pack.json. The generic interpreter
# re-registers them from the record at boot; this module keeps only its derived views and the
# reconstruction frames. Absence of a module op-dict is guarded by tests/test_ep14b.py.

# ONE VOCABULARY FOR THE FIVE CLASSES. Imported (read-only) from the observation classmap so
# scheduling and the observation seam name the classes with the same strings — design/10 §2's five
# classes, applied to scheduling by design/10 §4. Importing is not modifying; observe/ is not touched.
from observe.classmap import DECISION, LAW, INPUT, CACHE, STREAM

# THE FAMILY-KEYED PROJECTION (EP-33B Finding 2; design/36 ADDENDUM S, K12). The scheduling
# derived views fold their answer from the SCHEDULING family of records; reading the whole
# record to compute a family-scoped answer costs records the answer does not depend on, which
# K12 forbids ("a derived answer costs its own dependencies ... not the whole stream"). The fix
# is the EXISTING mechanism, not a new one: kernel.store.RecordProjection — the same seq-only
# projection the authority folds (GovernanceIndex) and the three per-act-path folds (EP-24C)
# already read through. It holds WHERE THE INPUTS ARE, never WHAT THE ANSWER WAS, is rebuilt
# from the record on load, and REFUSES (StaleIndex) if it cannot prove itself current. Kill it,
# replay, the world is identical.
from kernel.store import RecordProjection


# ---------------------------------------------------------------------------------------------
# design/10 §4 — EVERY SCHEDULING EVENT, CLASSIFIED (the whole subsystem, no gaps). Keys are the
# derivation's own event names (design/10 §4.1: LAW = scheduling policy; DECISIONS = admit/block/
# wake/halt/kill; INPUTS = timer ticks and wake-causing events; CACHE = the runnable set; STREAM =
# per-tick dispatch aggregates). RECORDED says whether THE SCHEDULER appends. The op that REALISES
# a recorded event is named in REALISED_BY. Events with no scheduler append — the tick, the clock
# read, sched_yield, the raw dispatch — are the clock-as-sensor / machine-activity that records
# NOTHING, which is this subsystem's whole point, not an omission.
# ---------------------------------------------------------------------------------------------
EVENT_CLASS = {
    # LAW — scheduling policy: a rule-of-rules amended WITH AUTHORITY (design/10 §4
    # sched_setscheduler / sched_setaffinity / nice rows). Priority is LAW-derived state, never a
    # poked mutable status (the order's second named wrong reference).
    "sched-setscheduler":     LAW,        # SCHED_FIFO/RR/DEADLINE policy — the clearest LAW case
    "sched-setaffinity":      LAW,        # CPU placement policy — a recorded amendment
    "set-priority":           LAW,        # nice / setpriority — priority policy amendment
    # DECISION — admit/block/wake/reap/halt/kill: law-derived state changes, each citing its rule.
    "admit":                  DECISION,   # a process admitted to the runnable set (fork/clone)
    "block":                  DECISION,   # a task leaves the runnable set awaiting an event
    "wake":                   DECISION,   # a task returns to runnable — SEE THE CARVE-OUT below
    "reap":                   DECISION,   # a zombie released (wait4 reap = a release decision)
    "halt":                   DECISION,   # a governed pause — the actor's grants released
    "resume":                 DECISION,   # a halt lifted
    "kill":                   DECISION,   # terminal rung of the penalty chain
    # INPUT — the clock as SENSOR: ticks and wake-causing arrivals enter the record ALREADY
    # recorded (for the device / time subsystems), never authored by the scheduler. So the
    # scheduler appends NOTHING for them (RECORDED False) — it CONSUMES them (cf. memory's
    # major-fault-completion). Reading time records nothing; the tick is the recorded arrival.
    "timer-tick":             INPUT,      # the periodic clock arrival
    "timer-expiry":           INPUT,      # a scheduled rule fires — a recorded arrival
    "wake-causing-arrival":   INPUT,      # interrupt / io-completion — the RT wake's recorded cause
    # CACHE — the runnable set and the clock READ: derived / sensor reads that record NOTHING and
    # reconstruct from LAW + DECISIONS + INPUTS.
    "runnable-set-read":      CACHE,      # sched_getscheduler / getpriority / sched_getcpu — query
    "clock-read":             CACHE,      # THE CLOCK IS A SENSOR — reading time records nothing (15.1)
    # STREAM — sched_yield and per-tick dispatch: raw operation flow applying already-recorded
    # policy; sampled in aggregate, never load-bearing.
    "sched-yield":            STREAM,     # canonical STREAM: applies recorded policy, records nothing
    "per-tick-dispatch":      STREAM,     # which runnable task the CPU picks per tick — pure function
}

# RECORDED tracks whether THE SCHEDULER appends a record for the event. DECISION and LAW record;
# CACHE, STREAM and INPUT do not (the INPUT arrival is recorded by the device / time subsystem, not
# here — the scheduler consumes an already-recorded input). Mirrors subsystems/memory.py exactly.
RECORDED = {ev: cls in (DECISION, LAW) for ev, cls in EVENT_CLASS.items()}

# Which built op REALISES each RECORDED scheduling event. A wake is a re-admit carrying a
# `wake_cause`, so it rides SCHED-ADMIT. Events classed by design/10 §4 but whose op is not minted
# this build are named "(forecast)" so the table is complete without a reader inferring an op the
# founding does not contain (mirrors memory's first-touch-fault / oom-kill forecasts).
REALISED_BY = {
    "set-priority": "SET-PRIORITY", "admit": "SCHED-ADMIT", "block": "DESCHEDULE",
    "wake": "SCHED-ADMIT", "halt": "SCHED-HALT", "resume": "SCHED-RESUME", "kill": "SCHED-KILL",
    "sched-setscheduler": "(forecast)", "sched-setaffinity": "(forecast)", "reap": "(forecast)",
}

# THE FIVE SCHED-LAW, cited by the six shipped ops via the founding pack's `law_cited` surface
# (SCHED-ADMIT->ADMIT, DESCHEDULE->ORDER, SET-PRIORITY->PRIORITY, SCHED-HALT & SCHED-RESUME->HALT,
# SCHED-KILL->KILL-CHAIN). They are LIVE DANGLES — cited, NOT created — and ALL FIVE ARE HELD
# OWNER-GATES: no scheduling law is minted on a seat's word (EP-32 R4 / stop condition 3). Named
# here for the subsystem; the created-vs-cited fact is DRIVEN from the pack in tests/test_ep32.py.
SCHED_LAW_FAMILY = ("SCHED-LAW-ADMIT", "SCHED-LAW-ORDER", "SCHED-LAW-PRIORITY",
                    "SCHED-LAW-HALT", "SCHED-LAW-KILL-CHAIN")

# design/10 §4 vs EP-27 — TWO PRIORITY MECHANISMS, NAMED APART so neither impersonates the other
# (the order's reconciliation requirement). Lane scheduling is RECORD-PROCESSING priority (EP-27);
# thread scheduling is CPU priority (this subsystem). They share the word "priority" and nothing
# else — a lane is not a thread and a thread is not a lane.
LANE_SCHEDULING = "record-processing priority (EP-27 lanes) — NOT this subsystem"
THREAD_SCHEDULING = "CPU / thread priority (design/10 §4) — THIS subsystem"


def classify(event):
    """The design/10 §4 class of a scheduling event, by the derivation's own event name. KeyError
    on an unnamed event — the table is exhaustive by §4, and a silent default would be a class
    nobody declared (cf. observe/classmap's UnmappedAct and memory's classify)."""
    return EVENT_CLASS[event]


# THE SCHEDULING FAMILY — exactly the recorded scheduling DECISIONs/LAW the two family-scoped
# folds below fold (`runnable` reads admit/priority/deschedule/kill; `halted` reads halt/resume).
# It is the answer's dependency set and nothing wider: padding it with records these folds never
# read (a budget amendment, a device input) would make the fold's cost grow with something its
# answer does not depend on, which is the very thing K12 forbids.
SCHEDULING_ACTIONS = ("SCHED-ADMIT", "SET-PRIORITY", "DESCHEDULE", "SCHED-KILL",
                      "SCHED-HALT", "SCHED-RESUME")


def is_scheduling_record(e):
    """Does this record belong to the scheduling-family subset the derived views fold?"""
    return e["action"] in SCHEDULING_ACTIONS


class SchedulingProjection(RecordProjection):
    """The scheduling-family subset the derived views read through, so `runnable()` and
    `halted()` cost their own family's records rather than the whole stream (K12; design/36
    ADDENDUM S). A subclass supplies THREE things and nothing else (EP-24C): the name it refuses
    under, the by_action keys it answers (NONE — the folds only iterate `all()`), and the
    predicate. Everything else — currency, resolution, coherent-or-refuse — is the one shared
    RecordProjection implementation."""

    _NAME = "scheduling projection"
    _selects = staticmethod(is_scheduling_record)


class SchedulingView:
    def __init__(self, store):
        self.store = store
        # The family-keyed projection is HELD (built once per view, incrementally caught up on
        # each read), so a view kept live — the production case (kernel/compose.py) — pays the
        # subset's cost per read, not the record's length. It holds only locations; every answer
        # is still folded from the record at read time.
        self._records = SchedulingProjection(store)

    def runnable(self, as_of=None):
        run = {}
        for e in self._records.all(as_of):
            a, p = e["action"], (e.get("payload") or {})
            if a == "SCHED-ADMIT":
                run[p["proc"]] = {"priority": p.get("priority", "normal")}
            elif a == "SET-PRIORITY" and p["proc"] in run:
                run[p["proc"]]["priority"] = p["priority"]
            elif a in ("DESCHEDULE", "SCHED-KILL"):
                run.pop(p["proc"], None)
        return run

    def halted(self, as_of=None):
        state = None
        for e in self._records.all(as_of):
            if e["action"] == "SCHED-HALT":
                state = (e.get("payload") or {})
            elif e["action"] == "SCHED-RESUME":
                state = None
        return state

    def why_ran(self, proc, as_of=None):
        """Answerable forever: the admit decision (rule + wake cause) that made proc
        runnable, plus its current priority."""
        admit = None
        for e in self.store.by_action("SCHED-ADMIT", as_of):
            if (e.get("payload") or {}).get("proc") == proc:
                admit = e
        if not admit:
            return None
        return {"admitted_seq": admit["seq"], "rule_cited": admit["rule_cited"],
                "wake_cause": admit["payload"].get("wake_cause"),
                "priority": self.runnable(as_of).get(proc, {}).get("priority")}


# =============================================================================================
# THE WAKE CARVE-OUT — discovered by the scheduling T-CACHE-KILL, never applied by judgment
# (design/10 §4; EP-32 order's WAKE CARVE-OUT, owner-ruled 2026-07-29).
# =============================================================================================
def _events(store, as_of=None):
    """The record as a list, whether given a store or a plain list of events."""
    return list(store.all(as_of)) if hasattr(store, "all") else list(store)


def _wait_on(deschedule_payload):
    """What a blocked task waits on, read from the DESCHEDULE decision's `cause` (design/10 §4:
    block records what it waits on). 'wait:timer:t7' / 'block:futex:0xabc' -> 'timer:t7' /
    'futex:0xabc'; a bare cause passes through."""
    c = (deschedule_payload or {}).get("cause") or ""
    for pre in ("wait:", "block:"):
        if c.startswith(pre):
            return c[len(pre):]
    return c


def runqueue(events):
    """The runnable SET folded from the FULL decision record — every wake counted as a recorded
    DECISION. This is the 'truth' the T-CACHE-KILL reconstruction is measured against. Membership
    only (the carve-out is about whether a woken task is present); priority is LAW-derived and is
    the runnable() view's concern, not this one."""
    run = set()
    for e in events:
        a, p = e["action"], (e.get("payload") or {})
        if a == "SCHED-ADMIT":
            run.add(p["proc"])                 # a first admit OR a wake (re-admit) — runnable
        elif a in ("DESCHEDULE", "SCHED-KILL"):
            run.discard(p["proc"])             # blocked or ended — leaves the runnable set
    return run


def reconstruct_runqueue(events, recorded_inputs, treat_every_wake_as_fill):
    """T-CACHE-KILL for the WAKE CARVE-OUT. Kill the derived runqueue; replay from LAW +
    DECISIONS + INPUTS. A WAKE is a re-admit (SCHED-ADMIT carrying `wake_cause`). A wake DROPPED as
    a FILL is re-derived below from the recorded-input stream instead of from a record of its own.

      treat_every_wake_as_fill=True   the NAIVE reconstruction — DROP every wake as a fill. A wake
                                      whose cause is UNAUDITED (absent from recorded_inputs) has
                                      nothing to re-derive it, so the task stays blocked and the
                                      runqueue DIVERGES: the test DISCOVERS that wake must NOT be a
                                      fill. This is the red world R1's bite.
      treat_every_wake_as_fill=False  the CLASSIFIED reconstruction the carve-out prescribes — drop
                                      ONLY wakes whose cause IS a recorded input (genuine fills),
                                      KEEP unaudited-cause wakes as recorded DECISIONS. This always
                                      reconstructs the full runqueue.

    NO authoring judgment picks timer-vs-futex; MEMBERSHIP in `recorded_inputs` picks it.
    `recorded_inputs` is a CROSS-SUBSYSTEM input: the timer expiries / interrupts / io-completions
    the device & time subsystems recorded. Scheduling does not own it — exactly as memory's
    reconstruction consumes the file subsystem's content-addressed blobs (design/22 §4). A futex
    word write is UNAUDITED by §4.5, so it is never in `recorded_inputs`."""
    recorded_inputs = set(recorded_inputs)
    run = set()
    blocked = {}                               # proc -> what it waits on (a dropped/blocked cause)
    for e in events:
        a, p = e["action"], (e.get("payload") or {})
        if a == "SCHED-ADMIT":
            proc = p["proc"]
            wc = p.get("wake_cause")
            is_wake = wc is not None
            drop_as_fill = is_wake and (treat_every_wake_as_fill or wc in recorded_inputs)
            if drop_as_fill:
                blocked[proc] = wc             # DROPPED: re-derive from the recorded input below
            else:
                run.add(proc)                  # first admit, or a wake KEPT as a decision
                blocked.pop(proc, None)
        elif a == "DESCHEDULE":
            proc = p["proc"]
            run.discard(proc)
            blocked[proc] = _wait_on(p)
        elif a == "SCHED-KILL":
            proc = p["proc"]
            run.discard(proc)
            blocked.pop(proc, None)
    # re-derive the dropped fills: a blocked task whose cause is a RECORDED input wakes, from that
    # input ALONE (the wake was reconstructible and needed no record of its own).
    for proc, cause in blocked.items():
        if cause in recorded_inputs:
            run.add(proc)
    return run


def wake_class(events, recorded_inputs):
    """The class the T-CACHE-KILL DISCOVERS for each wake, reported as data (never asserted by
    authoring). Returns {wake_cause: 'FILL' | 'DECISION'}: FILL where a recorded input reconstructs
    it, DECISION where nothing recorded explains it (its cause is unaudited). Stop condition 5: if a
    wake carries no cause at all, it cannot be decided by the test — raise, do not guess."""
    recorded_inputs = set(recorded_inputs)
    out = {}
    for e in events:
        if e["action"] == "SCHED-ADMIT":
            wc = (e.get("payload") or {}).get("wake_cause")
            if wc is None:
                continue                       # a first admit, not a wake
            out[wc] = "FILL" if wc in recorded_inputs else "DECISION"
    return out


# =============================================================================================
# T-TICKS-ARE-INPUT — the clock is a SENSOR; replay reconstructs dispatch from recorded ticks
# with NO wall-clock read (design/10 §4/§9; ban 15.1; EP-32 A2 / R3).
# =============================================================================================
_PRIORITY_ORDER = {"rt": 0, "high": 1, "normal": 2, "idle": 3}


class Sensor:
    """The clock as a SENSOR. Replay may READ recorded ticks; it must NEVER read now() — a schedule
    is a recorded rule over recorded time INPUTS, its firing a recorded activity (design/10 §9).
    now() exists so a red world (R3) can PLANT a clock-as-scheduler read and be caught by the
    determinism test; the governed dispatch never calls it."""
    def __init__(self, t=0):
        self._t = t

    def set(self, t):
        self._t = t

    def now(self):
        return self._t


def dispatch_sequence(runnable_by_priority, ticks):
    """T-TICKS-ARE-INPUT: the per-tick dispatch reconstructed from LAW (policy priority) + recorded
    INPUTS (`ticks`) with NO wall-clock read. For each recorded tick the CPU picks the
    highest-priority runnable task (STREAM — records nothing); ties break deterministically by
    task id. The sequence is a PURE FUNCTION of (policy, runnable set, recorded ticks): two replays
    at different wall-clock times produce identical sequences, which is exactly why replay may not
    consult the clock (R3). `ticks` is the recorded input stream, never `time.time()`."""
    seq = []
    for _tick in ticks:
        if not runnable_by_priority:
            seq.append(None)
            continue
        pick = min(runnable_by_priority,
                   key=lambda pr: (_PRIORITY_ORDER.get(runnable_by_priority[pr], 9), pr))
        seq.append(pick)
    return seq


# =============================================================================================
# T-REALTIME-BOUND FRAME — the code path the guest / MAX dispatch MEASURES; not measured here
# (design/10 §4; owner ruling 2026-07-13; EP-32 A4, the owner checkpoint / stop condition 2).
# =============================================================================================
def rt_dispatch(runnable_rt, policy):
    """T-REALTIME-BOUND FRAME. The real-time dispatch decision path for SCHED_FIFO / SCHED_RR /
    SCHED_DEADLINE: a PURE, DETERMINISTIC pick that appends NOTHING (STREAM). FIFO/RR pick the
    strictly-highest rt_priority (FIFO ties by task id — a stand-in for admit order); DEADLINE picks
    the earliest deadline (EDF). `runnable_rt` maps task id -> {'policy', 'rt_priority', 'deadline'}.

    THIS IS THE FRAME, NOT THE MEASUREMENT. The temporal bound — the measured latency and its
    MARGIN on the validation kernel — is the guest / gov-builder-max dispatch (EP-32 A4). The
    real-time assume does NOT flip on this seat's word: the close FILES the margin and the OWNER
    reads it first (EP-32 §8 stop condition 2). Nothing here flips an assume."""
    rt = {t: m for t, m in runnable_rt.items()
          if m.get("policy") in ("SCHED_FIFO", "SCHED_RR", "SCHED_DEADLINE")}
    if not rt:
        return None
    if policy == "SCHED_DEADLINE":
        return min(rt, key=lambda t: (rt[t].get("deadline", float("inf")), t))       # EDF
    return min(rt, key=lambda t: (-rt[t].get("rt_priority", 0), t))                    # strict prio


# =============================================================================================
# RECORDS-PER-DISPATCH FRAME — the MAX crux in the FALSIFIABLE FORM; structural shape only, the
# measurement at real rate is the guest / MAX dispatch (design/36 ADDENDUM; EP-32 A5 / R2).
# =============================================================================================
def records_per_dispatch(n_decisions, n_dispatches):
    """A5 FRAME (the MAX crux, falsifiable form). Dispatch is STREAM and records NOTHING, so the
    total records over a run are the FIXED governed DECISIONS; records-per-dispatch =
    |decisions| / |dispatches| FALLS toward the governance floor as the dispatch rate rises with
    decisions fixed. This is a SHAPE, NOT a bound the pass declares (EP-29 finding 2). The
    MEASUREMENT at real dispatch rates under a kernel dispatch storm is the guest / gov-builder-max
    dispatch; if that ratio comes back flat or rising it is the durability-vs-real-time tension
    surfacing — STOP and raise, never tune by weakening append durability (EP-32 §8 stop 4)."""
    return n_decisions / n_dispatches if n_dispatches else float("inf")


def dispatch_storm(store, runnable_by_priority, n_dispatches):
    """Run `n_dispatches` per-tick dispatches against a live store and return the records the
    dispatch phase appended — which is ZERO (dispatch is STREAM, a pure read of the derived queue).
    The A5 FRAME whose records-per-dispatch the guest / MAX dispatch measures at real rate; the
    structural shape (ratio at >=2 rate levels, falling) is DRIVEN host-side in tests/test_ep32.py."""
    before = len(store.all())
    dispatch_sequence(runnable_by_priority, range(n_dispatches))
    return len(store.all()) - before
