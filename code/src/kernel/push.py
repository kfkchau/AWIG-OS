# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — the standing push worker and the priority lanes (design/28 §6; design/35 §3;
design/36 K10; wall primitive 8).

An on-append worker delivers each NEW governed record to the per-channel queues of the active
move-to view definitions, and — since EP-27 — to the live decider sessions whose DECLARED view
a law change reaches. Law travels faster than traffic.

FOUR LINES THIS MUST NEVER CROSS.

  1. THE FLOOD BOUNDARY (I9, unchanged and re-proven over the new machinery). The worker fires
     at APPEND — governance rate, once per governed record, NEVER per read — and delivers by
     mutating IN-MEMORY state ONLY. It APPENDS NOTHING. That now covers three more things than
     it used to: a session delivery appends nothing, a DELAYED item appends nothing, and a SHED
     item appends nothing. The last is the one worth stating outright, because a shed looks like
     an event: under a flood the sheds are exactly proportional to the flood, so appending one
     record per shed would make recording scale with OPERATION — the precise failure I9 names,
     and the flood-control mechanism amplifying the flood into the record. A shed is not a new
     decision; it is the APPLICATION of a decision already recorded once, as the budget rule. So
     a shed is DERIVED and CITED, never appended — the EP-26 answer to a refused sweep, applied
     to a dropped delivery: do not store it, COMPUTE it.

  2. QUEUES ARE VIEWS, not stored lists. This worker's state is only an ACCELERATION of
     `Views.lane_report()` (the derivation from the record). Kill the worker and the derivation
     rebuilds the identical channels, pending set, shed list and session deliveries from the
     record alone. There is ONE implementation of the cycle logic (`_LaneEngine`) and two
     drivers — the worker steps it per append, the derivation steps it over the whole record —
     which is EP-24B's standing law (one implementation, two record sources) applied to
     delivery, and it is what makes the EP-08B defect (an acceleration drifting from its
     derivation) structurally impossible rather than merely tested for.

  3. NO GOVERNANCE VALUE LIVES IN THIS FILE (I5). There is no priority action list, no lane
     table keyed by op name, no budget constant. LANE MEMBERSHIP IS READ FROM THE RECORD'S OWN
     CLASS — a record rides the law lane because its payload declares a `rule_id`, which is the
     store's own law predicate and not a second opinion — so a law-family kind invented tomorrow
     rides the lane with zero code change here. WHICH lane holds the reserved slots, and how big
     the budget, the reserve and the depth cap are, are RECORDED RULES with a named calibration
     owner: re-prioritising is an ordinary recorded act, never an edit to this file. The named
     wrong reference for EP-27 is exactly what this paragraph refuses: QoS as engine
     configuration, where every re-prioritisation is a code change and the flood policy is
     invisible to the audit that must answer "why was this delivery late".

  4. NO CLOCK (15.1). A cycle is one APPEND, not one tick and not one second. The budget is
     spent per cycle, so the whole schedule is a function of the record's own order and the
     policy in force at each point — which is why the derivation can recompute exactly what the
     worker did, sheds included, from the record file alone.

WHAT THE RESERVE IS FOR, since a priority scheme where the urgent lane simply always goes first
would make the reserve decoration. Pending work is served in ARRIVAL ORDER, because the
record's order is the only order this estate has and inventing a second ordering principle
inside a worker is the engine-configuration trap wearing a different face. The ONE thing that
makes law outrun traffic is the RESERVE: a slice of every cycle's budget that ONLY the reserved
lane may spend. A law record can take a reserved slot from behind a backlog of any depth; an
ordinary record never can. Set the reserve to zero and the law lane competes in arrival order
and visibly starves under a standing backlog — which is what the acceptance battery proves,
because a reserve that cannot be shown failing is not known to be doing anything.

Evented / materialized delivery (writing a delivery record) would need a recorded
materialization policy with a NAMED OWNER — a calibration, never a default (design/28 §6) —
and is NOT built here.
"""

from . import reconcile
from .views import _matches

# ---- the two structural lanes -----------------------------------------------------------
# These two NAMES are engine surface in the same sense the check vocabulary and the tier
# ladder are (design/28 §10): they name a structural distinction the record itself draws —
# a record either declares law or it does not — and they carry no governance content. Which
# of them is privileged, and by how much, is data (below).
LAW_LANE = "law"
ORDINARY_LANE = "ordinary"

#: The recorded rule and policy key the whole lane schedule reads. Naming the rule here is a
#: CITATION, not a policy: the values live in the record, and a shed cites this name so an
#: auditor asking "why was this delivery dropped" is handed the rule to read.
LANE_BUDGET_RULE = "LANE-BUDGETS"
LANE_BUDGET_KEY = "lane-budgets"


def lane_of(record):
    """WHICH LANE THIS RECORD RIDES, read from what the record IS.

    A law-family record rides the law lane; everything else rides ordinary. The predicate is
    `reconcile.is_law_family` — the store's own law rule (`payload` declares a `rule_id`),
    reused rather than restated, so there is one recognition rule in the estate and not two
    that could disagree. Nothing here knows a verb, so a subsystem's future law op rides the
    lane the day it exists, and the overturn rides ORDINARY without being exempted by name:
    an overturn is a DECISION and declares no rule_id, and the sweep — not the lane — is its
    urgency (design/35 §3)."""
    return LAW_LANE if reconcile.is_law_family(record) else ORDINARY_LANE


def _budget_from(value):
    """The lane schedule as the record states it, normalised for reading. An ABSENT policy
    leaves every limit absent, and an absent limit does not bind: no cycle cap, no reserve, no
    depth cap. That is the safe direction and it is also the pre-EP behaviour exactly — there
    is no code-resident default standing in for a missing law, and a store with no founding
    delivers everything, as it always did."""
    v = dict(value or {})
    order = tuple(v.get("order") or (LAW_LANE, ORDINARY_LANE))
    cycle, reserve = v.get("cycle"), dict(v.get("reserve") or {})
    reserved_lane = order[0] if order else LAW_LANE
    # THE ALLOWANCE IS COMPUTED, and it is computed because a measurement found the hazard.
    # A reserve at or above the cycle budget leaves the general allowance at ZERO, and every
    # lane but the reserved one then waits forever — a standing starvation that a flood test
    # reveals only after the fact. It is NOT refused here: which values are sane is governance
    # content and belongs to the owner's calibration, not to a comparison written into the
    # engine. What the engine owes is that the consequence is READABLE BEFORE IT BITES, so the
    # allowance is derived and reported beside the values it comes from.
    if cycle is None:
        allowance = {reserved_lane: None, "general": None}
    else:
        held = min(reserve.get(reserved_lane, 0), cycle)
        allowance = {reserved_lane: held, "general": cycle - held}
    return {"cycle": cycle, "reserve": reserve, "depth": dict(v.get("depth") or {}),
            "order": order, "allowance": allowance}


# ---- the reach test: does this record move what the session declared it reads? -------------

def _reaches(views, record, view_def, cache):
    """DOES THIS RECORD REACH THIS VIEW — the view's own answer moving, never a second matcher.

    Two shapes, one question. A FILTER view's rows can only grow by the arriving record, so its
    answer moves iff the record matches its trigger — the standing push's own `_matches`, the
    same rule the channel delivery uses, so a session and a channel can never disagree about
    what a view saw. A MASTER view binds an S-plane fold, so its answer is asked twice: as of
    the record, and as of the moment before it. Nothing here enumerates which records affect
    which master; the fold answers for itself.

    The pair is computed once per master per arriving record and shared across every session
    declaring it (`cache`), because ten sessions watching the rule master are one question."""
    if view_def is None:
        return False
    if view_def.get("bind"):
        name, seq = view_def["name"], record["seq"]
        key = (name, seq)
        if key not in cache:
            before = views.master(name, as_of=seq - 1)
            after = views.master(name, as_of=seq)
            cache[key] = (before or {}).get("value") != (after or {}).get("value")
        return cache[key]
    return _matches(record, view_def.get("when") or {})


# ---- the one implementation of the cycle ---------------------------------------------------

class _LaneEngine:
    """ONE cycle implementation, two drivers (EP-24B's standing law applied to delivery).

    Holds the lane state: what is queued, what has been delivered, what the policy shed, and
    what reached each live session. Every field is DERIVED — kill the whole object, step it
    over the record again, and it reconstructs identically.
    """

    def __init__(self, views, budget=None, sessions=None):
        self.views = views
        self.budget = _budget_from(budget)
        self.channels = {}
        self.sessions = dict(sessions or {})      # session_id -> {account, read_set}
        self.session_deliveries = {}
        self.dangling = {}
        self.pending = []                          # arrival-ordered, both lanes
        self.shed = []
        self.starved = []

    # ---- reading the record's own declarations forward -------------------------------------
    def _absorb_policy(self, record):
        """The budget in force is read FORWARD off the record, not folded per step: a record
        carrying this policy key IS the amendment (latest-wins), so watching for it gives the
        same answer `policy_value` would and costs one dict lookup instead of a fold."""
        p = record.get("payload") or {}
        if p.get("policy_key") == LANE_BUDGET_KEY:
            self.budget = _budget_from(p.get("value"))

    def _absorb_session(self, record):
        """The live contact points, tracked forward off the session records themselves — the
        same two facts `reconcile.sessions` folds, read once as they arrive."""
        p = record.get("payload") or {}
        if p.get("kind") != "session":
            return
        sid = p.get("session_id")
        if sid is None:
            return
        if p.get("event") == "open":
            self.sessions[sid] = {"account": p.get("account") or record["actor"],
                                  "read_set": list(p.get("read_set") or [])}
        elif p.get("event") == "close":
            self.sessions.pop(sid, None)

    # ---- one cycle: enqueue what this record produced, then drain under the budget ---------
    def step(self, record, move_defs, reach_cache):
        self._absorb_policy(record)
        self._absorb_session(record)
        lane = lane_of(record)
        for d in move_defs:
            # FORWARD-ONLY (design/28 §6 "each NEW record"): a standing view delivers matches
            # recorded AFTER it was defined, never backfill.
            if record["seq"] > d["seq"] and _matches(record, d["when"]):
                self._enqueue({"lane": lane, "record": record, "target": ("channel", d["then"]["move_to"])})
        if lane == LAW_LANE:
            self._target_sessions(record, reach_cache)
        self._drain()

    def _target_sessions(self, record, reach_cache):
        """SESSION-AWARE PUSH (design/35 §3). On a law-family append, the change's reach is
        intersected with every live session's DECLARED read-set; the ones it reaches get the
        delivery on the law lane. A declaration naming no live view resolves to nothing and is
        REPORTED rather than silently empty — an under-declared session is a convenience
        problem, but an invisible one would be a correctness problem."""
        defs = self.views.view_definitions()
        for sid, s in self.sessions.items():
            reached, dangling = [], []
            for ref in s["read_set"]:
                name = ref.split(":", 1)[1] if ref.startswith("view:") else ref
                d = defs.get(name)
                if d is None:
                    dangling.append(ref)
                elif _reaches(self.views, record, dict(d, name=name), reach_cache):
                    reached.append(ref)
            if dangling:
                self.dangling.setdefault(sid, [])
                for ref in dangling:
                    if ref not in self.dangling[sid]:
                        self.dangling[sid].append(ref)
            if reached:
                self._enqueue({"lane": LAW_LANE, "record": record,
                               "target": ("session", sid), "reached": reached})

    def _enqueue(self, item):
        """Queue one delivery, applying the recorded DEPTH cap for its lane. Over the cap the
        OLDEST pending item on that lane is shed — the freshest state keeps moving, and the shed
        one is still on the record, permanently: what the policy dropped is a derived flow, never
        a fact."""
        item.setdefault("reached", [])
        self.pending.append(item)
        cap = self.budget["depth"].get(item["lane"])
        if cap is None:
            return
        on_lane = [i for i in self.pending if i["lane"] == item["lane"]]
        while len(on_lane) > cap:
            victim = on_lane.pop(0)
            self.pending.remove(victim)
            self.shed.append({**victim, "reason": "depth", "limit": cap,
                              "rule_cited": LANE_BUDGET_RULE, "policy_key": LANE_BUDGET_KEY})

    def _drain(self):
        """ONE CYCLE. Serve pending work in ARRIVAL ORDER within the cycle budget, except that
        the cycle's first `reserve` slots belong to the reserved lane and no other lane may
        spend them. That single asymmetry is what makes law outrun traffic; remove it (set the
        reserve to zero) and the law lane queues behind the backlog like everything else."""
        order = self.budget["order"]
        reserved_lane = order[0] if order else LAW_LANE
        reserved = self.budget["allowance"][reserved_lane]
        general = self.budget["allowance"]["general"]
        served, kept = [], []
        for item in self.pending:
            if general is None:
                served.append(item)
                continue
            if item["lane"] == reserved_lane and reserved > 0:
                reserved -= 1
                served.append(item)
            elif general > 0:
                general -= 1
                served.append(item)
            else:
                kept.append({**item, "reason": "cycle-budget", "rule_cited": LANE_BUDGET_RULE,
                             "policy_key": LANE_BUDGET_KEY, "limit": self.budget["cycle"]})
                if item["lane"] == reserved_lane:
                    self.starved.append({**item, "reason": "reserve-exhausted",
                                         "rule_cited": LANE_BUDGET_RULE,
                                         "policy_key": LANE_BUDGET_KEY})
        self.pending = kept
        for item in served:
            kind, where = item["target"]
            if kind == "channel":
                self.channels.setdefault(where, []).append(item["record"])
            else:
                self.session_deliveries.setdefault(where, []).append(item)

    def report(self):
        return {"channels": self.channels, "pending": self.pending, "shed": self.shed,
                "sessions": self.session_deliveries, "dangling": self.dangling,
                "starved": self.starved, "budget": self.budget}


def derive(store, views, as_of=None):
    """THE DERIVATION — the whole lane state recomputed from the record alone, which is what
    the worker accelerates and what the round-trip law binds on. Same `_LaneEngine`, driven
    over every record instead of one at a time."""
    move_defs = [dict(d, name=n) for n, d in views.view_definitions(as_of).items()
                 if (d.get("then") or {}).get("move_to")]
    engine = _LaneEngine(views)
    cache = {}
    for e in store.all(as_of):
        engine.step(e, move_defs, cache)
    return engine.report()


class StandingPush:
    """THE ACCELERATION. One engine stepped once per append, holding what the derivation would
    recompute. Nothing here is a source of truth."""

    def __init__(self, store, views):
        self.store = store
        self.views = views
        self._engine = _LaneEngine(views,
                                   budget=views.policy_value(LANE_BUDGET_KEY),
                                   sessions={s: {"account": c["account"], "read_set": c["read_set"]}
                                             for s, c in views.live_sessions().items()})
        self._move_defs = self._live_move_defs()
        self._reach_cache = {}
        self._gen = 0
        store.on_append(self._on_append)

    def _live_move_defs(self):
        return [dict(d, name=n) for n, d in self.views.view_definitions().items()
                if (d.get("then") or {}).get("move_to")]

    def _on_append(self, record):
        """Governance rate: ONE pass per governed append, zero appends.

        B1 (R26): a view-definition amendment invalidates deliveries made under the OLD version
        — which the derivation (latest-def, forward-only) correctly drops but an accumulated
        in-memory copy would keep, making the acceleration a WRONG one from that point. So on a
        committed CREATE-VIEW the worker RESYNCS from the derivation. Since EP-27 that resync
        covers the pending set, the shed list and the session deliveries too: an amendment
        invalidates the whole schedule those were computed under, not only the channels."""
        if record["action"] == "CREATE-VIEW" and (record.get("payload") or {}).get("kind") == "view_definition":
            self._resync()
        else:
            self._engine.step(record, self._move_defs, self._reach_cache)
        self._gen += 1

    def _resync(self):
        derived = derive(self.store, self.views)
        engine = _LaneEngine(self.views, budget=self.views.policy_value(LANE_BUDGET_KEY),
                             sessions={s: {"account": c["account"], "read_set": c["read_set"]}
                                       for s, c in self.views.live_sessions().items()})
        engine.channels = derived["channels"]
        engine.pending = derived["pending"]
        engine.shed = derived["shed"]
        engine.session_deliveries = derived["sessions"]
        engine.dangling = derived["dangling"]
        engine.starved = derived["starved"]
        self._engine = engine
        self._move_defs = self._live_move_defs()
        self._reach_cache = {}

    # ---- the read surface (every one of these is an acceleration, never a source) ----
    def channels(self):
        return self._engine.channels

    def pending(self):
        return self._engine.pending

    def shed(self):
        return self._engine.shed

    def starved(self):
        return self._engine.starved

    def session_deliveries(self):
        return self._engine.session_deliveries

    def dangling_declarations(self):
        return self._engine.dangling

    def budget(self):
        return self._engine.budget

    def lane_order(self):
        return self._engine.budget["order"]

    def report(self):
        return self._engine.report()


class LaneIntake:
    """THE UPWARD DIRECTION — lane-ordered processing of PENDING submissions toward the store.

    Law travels faster than traffic on the way IN as well as on the way out: given a set of
    submissions waiting to be processed, the law-family ones are processed first, so a law
    reaches the store ahead of ordinary work that was submitted before it. What this changes is
    the ORDER OF PROCESSING and nothing else. `record_time` and `seq` are still minted at
    append, still monotone, still the sole total order (design/21, design/35 §5) — the lane
    decides who goes through the door next, never what the record says once they are through.

    A LANE IS STILL READ FROM THE RECORD, one step earlier. At intake the record does not exist
    yet, so the lane is read from the record that WILL mint it: the op's own definition record,
    whose `payload_from` / `payload_derive` declare whether the payload carries a `rule_id`.
    This is the EP-16 authority-regime precedent — an op declares its regime as DATA on its own
    record, read from there and never from a verb list in code.

    THE HONEST GAP, reported rather than papered over: the bootstrap constructors (I3 — the
    only code-registered ops) have no definition record, so their lane cannot be read from the
    record at all. `lane_of_op` answers None for them and `undeclared()` names the whole set.
    They are scheduled as ordinary, which is the safe direction (nothing is privileged on an
    unread declaration), and the gap is RAISED rather than closed with a list of names here —
    a list of names is the wrong reference this EP exists to refuse.

    A SWEEP IS NEVER INTERLEAVED (design/36 ADDENDUM A.5). A law-family submission still travels
    `reconcile.submit`, the serialized door, so a sweep in flight HOLDS it until its fixed point.
    Lane priority orders arrivals; it does not reach into a running sweep."""

    def __init__(self, gate, views):
        self.gate = gate
        self.views = views
        self._pending = []

    def lane_of_op(self, name):
        """The lane this op's records will ride, read from the op's own definition record.
        None when the op has no definition record to read."""
        meta = self.views.op_definitions().get(name)
        if meta is None:
            return None
        d = meta.get("definition") or {}
        declares = ("rule_id" in (d.get("payload_from") or [])
                    or "rule_id" in (d.get("payload_derive") or {}))
        return LAW_LANE if declares else ORDINARY_LANE

    def undeclared(self):
        """Every registered op whose lane cannot be read from the record — the bootstrap
        constructors. Computed from the registry, so the list cannot go stale."""
        defined = self.views.op_definitions()
        return sorted(n for n in getattr(self.gate, "ops", {}) if n not in defined)

    def submit(self, op, actor, params=None):
        """Queue a submission. Nothing is processed until `drain`."""
        item = {"op": op, "actor": actor, "params": params or {},
                "lane": self.lane_of_op(op) or ORDINARY_LANE,
                "declared": self.lane_of_op(op) is not None,
                "index": len(self._pending)}
        self._pending.append(item)
        return item

    def pending(self):
        return list(self._pending)

    def drain(self):
        """Process every pending submission, the reserved lane first and each lane in its own
        submission order. Returns what each submission produced, in processing order — an
        appended record, or the `Deferred` a running sweep is holding."""
        budget = _budget_from(self.views.policy_value(LANE_BUDGET_KEY))
        rank = {lane: i for i, lane in enumerate(budget["order"])}
        queue = sorted(self._pending, key=lambda i: (rank.get(i["lane"], len(rank)), i["index"]))
        self._pending = []
        out = []
        for item in queue:
            if item["lane"] == LAW_LANE:
                out.append(reconcile.submit(self.gate, item["op"], item["actor"], item["params"]))
            else:
                out.append(self.gate.execute(item["op"], item["actor"], item["params"]))
        return out
