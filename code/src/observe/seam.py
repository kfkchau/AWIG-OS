# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""M1 W1 — the adapter seam: the one typed boundary every observation crosses.

A WINDOW is a read-only Linux facility (windows.py). It yields OBSERVATIONS — the typed
boundary object below. The SEAM submits them through the ONE gate as ordinary registered
ops. Adapters are SUBMITTERS, never writers (design/36 §3): the store keeps its single
writer, no adapter appends, and no intake queue of our own design exists — the S5 sequencer
is campaign 6, and pressure toward a second appender is the boundary announcing itself.

WHAT THIS IS NOT (EP-22, THE REFERENCE TO AVOID): an audit daemon writing event LINES to a
log for later grepping. Nothing here writes to any file that is not THE store; there is no
log, no shipper, and no event stream beside the record. An observation is an ordinary
submission through the one gate, classed by the legend, derived into views that answer asOf.

THE THREE PINS (T-PROVENANCE-PINNED). Every observed record carries, and cannot omit:
  1. `provenance.asserted_by`  — the observer that asserts it;
  2. `provenance.window` + `provenance.window_version` — the window it saw through, at its
     version (rendered `window@version`; wall primitive 5 enters here);
  3. the envelope `occurrence_time` — as the WINDOW reported it.
Enforcement is at the write chokepoint, not in this module's logic: each observe op DECLARES
all three as REQUIRED parameters, so the gate's own nonconforming-call check refuses (AR-2,
recorded) before any handler runs. A record missing any of the three cannot be drafted.

THE OBSERVED ACT IS THE RECORD'S ACTION, and the caller does not choose it. The record says
what the box did — `file-modified`, `mount-added` — because that is what happened; a record
whose action said "an observation occurred" would be a log line about a log line, the exact
wrong reference. The safety this costs is bought back at the same chokepoint: each op admits
only the acts its own window's class map carries as RECORDED (classmap.RECORDED_ACTS), and
anything else refuses AR-2, recorded, before a draft exists. So the campaign-1 smuggle shape
— an observe call whose action names a law-lifecycle act — dies at the seam, in front of the
constitution guard that also still catches it.

WHY `SYS-RECORD` IS THE CITED LAW. It is the recorded root law reading "SYSTEM may record any
activity as evidence (recording is not permission to perform)" — which is precisely M1's
honesty rule (observation is not the gate) already standing as law. The record's `actor` is
therefore SYSTEM, the recorder, and the observer's identity lives in provenance.asserted_by,
exactly as the estate's other SYSTEM-recording surface (WRITE-ACTIVITY) already works.

TWO TIMES, FROM DAY ONE (design/36 K7). An observation's occurrence precedes its recording,
always — the observe world is ALREADY a two-times world. This EP builds no adjudication
(that is EP-26); it must only carry the occurrence time HONESTLY, which includes marking the
substitution when a window reports no time of its own (`time_source`).
"""

import datetime

from . import classmap

#: The recorded root law every observation cites (see the module note).
OBSERVATION_LAW = "SYS-RECORD"

#: The default observer identity. One observer process runs many windows; the observer and
#: the window are separate facts and both land on every record.
DEFAULT_OBSERVER = "m1-observer"

#: How an observation's occurrence_time was obtained. The second value is the marked
#: substitution EP-22's RAISED-BY-DESIGN requires: when a window reports no time of its own,
#: submission time stands in and SAYS SO, so EP-26 knows which times are which.
TIME_WINDOW_REPORTED = "window-reported"
TIME_SUBMISSION_SUBSTITUTED = "submission-substituted"

#: window -> the op that submits it. One op per window, so enumerating the registry
#: enumerates the observation surface exactly ("the bank has no counter", P3): a window with
#: no op cannot write, and an op with no window is never registered.
OP_FOR_WINDOW = {
    "process": "OBSERVE-PROCESS",
    "file": "OBSERVE-FILE",
    "mount": "OBSERVE-MOUNT",
    "device": "OBSERVE-DEVICE",
    "connection": "OBSERVE-CONNECTION",
}

#: The three pins, as parameter names, declared REQUIRED on every observe op.
PIN_PARAMS = ("window", "window_version", "occurrence_time")


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def window_at_version(window, version):
    """The rendered pin. Computed from the two recorded fields, never stored beside them —
    a stored join is a stored derivative (P2)."""
    return f"{window}@{version}"


class Observation:
    """The typed boundary between a window and the record. A window constructs these and
    knows nothing about the gate; the seam submits them and knows nothing about netlink."""

    __slots__ = ("window", "window_version", "act", "object", "occurrence_time",
                 "time_source", "data", "principal")

    def __init__(self, window, window_version, act, object, occurrence_time=None,
                 time_source=TIME_WINDOW_REPORTED, data=None, principal=None):
        self.window = window
        self.window_version = window_version
        self.act = act
        self.object = object
        # A window that reports no time of its own substitutes submission time AND MARKS IT
        # (RAISED-BY-DESIGN 4). The mark rides to the record, so a later reader — EP-26's
        # adjudication above all — never mistakes a stand-in for a reported occurrence.
        if occurrence_time is None:
            self.occurrence_time = _now_iso()
            self.time_source = TIME_SUBMISSION_SUBSTITUTED
        else:
            self.occurrence_time = occurrence_time
            self.time_source = time_source
        self.data = dict(data or {})
        self.principal = principal

    @property
    def record_class(self):
        return classmap.classify(self.window, self.act)

    def __repr__(self):
        return (f"Observation({window_at_version(self.window, self.window_version)} "
                f"{self.act} {self.object} @{self.occurrence_time} [{self.time_source}])")


def register_observe_ops(gate):
    """Register the M1 observation surface: one op per live window, each pinning the three
    provenance facts as required parameters and admitting only its own window's recorded acts.

    Registration REFUSES to proceed if the campaign-1 observe pair is already on this gate.
    Those two ops (OBSERVE-PROCESS / OBSERVE-RESOURCE, `process_watch.py` /
    `resource_watch.py`) predate the pins and are superseded IN FUNCTION by this seam; they
    remain live only as the subject of two other EPs' ledger tests. Composing both surfaces
    onto one gate would put an unpinned observe path beside a pinned one, which is the exact
    property T-PROVENANCE-PINNED denies — so it stops loudly and says why."""
    if gate.has("OBSERVE-RESOURCE"):
        raise ValueError(
            "the campaign-1 observe surface (OBSERVE-RESOURCE) is registered on this gate — "
            "it predates the M1 provenance pins and the two surfaces do not compose: register "
            "one or the other, never both (EP-22 W1)")

    for window, opname in OP_FOR_WINDOW.items():
        gate.register(opname, _op_meta(window, opname), _observe_handler(gate, window, opname))
    return sorted(OP_FOR_WINDOW.values())


def _op_meta(window, opname):
    return {
        "description": (f"record an act observed through the {window} window "
                        f"(observation is not the gate: {OBSERVATION_LAW})"),
        "rules": [OBSERVATION_LAW],
        # The three pins + what the act was and what it was about. All required: an
        # observation missing any of them is not an observation, it is an assertion.
        "params": {"window": "required", "window_version": "required",
                   "occurrence_time": "required", "act": "required", "object": "required"},
        # Read by the M1 surface guard (and by anyone enumerating the registry) to see that
        # this op's action vocabulary is closed and which acts it admits.
        "observe_window": window,
        "observe_acts": classmap.RECORDED_ACTS[window],
    }


def _observe_handler(gate, window, opname):
    """The one handler shape, per window. It COPIES what the observation carries; it derives
    nothing about the world and invents nothing. Two refusals live here, both on the write
    path and both recorded: a mismatched window, and an act outside this window's closed
    recorded vocabulary."""

    def handle(actor, params):
        if params.get("window") != window:
            gate.refuse(actor, opname, "AR-2",
                        f"{opname} records the {window!r} window; this call names "
                        f"{params.get('window')!r} — a window's records are written by its own op")
        act = params["act"]
        if act not in classmap.RECORDED_ACTS[window]:
            # The closed vocabulary, enforced where the write happens. This is what stops a
            # caller-chosen action from carrying anything but an observation of this window.
            gate.refuse(actor, opname, "AR-2",
                        f"{act!r} is not a recorded act of the {window!r} window — its vocabulary is "
                        f"closed: {', '.join(classmap.RECORDED_ACTS[window])}")
        version = params["window_version"]
        payload = {
            # The info-kind dimension of an observation (the gate's authority step reads it).
            # Observing processes and observing files are DIFFERENT information, so they are
            # different kinds — which is what lets a narrowed world grant one without the other.
            "kind": f"observed-{window}",
            "act": act,
            "window": window,
            "window_version": version,
            "record_class": classmap.classify(window, act),
            "time_source": params.get("time_source") or TIME_WINDOW_REPORTED,
            "observed": dict(params.get("data") or {}),
        }
        if params.get("principal") is not None:
            # K6, at observation scale: the principal the WINDOW reported (a pid, a uid) is
            # EVIDENCE, recorded as observed. It is not resolved to an account and never will
            # be by this EP — actor resolution derives from recorded mapping acts, and at M1
            # there are none. Recording it as evidence is honest; resolving it would not be.
            payload["observed_principal"] = params["principal"]
        return {
            "actor": "SYSTEM",                       # the recorder (SYS-RECORD)
            "action": act,                           # what the box did — the act itself
            "object": params["object"],
            "rule_cited": OBSERVATION_LAW,
            "occurrence_time": params["occurrence_time"],   # as the window reported it
            "provenance": {
                "asserted_by": actor,                # the observer, not the box
                "source": params.get("source") or window,
                "window": window,
                "window_version": version,
                "could_read": [params.get("source") or window],
            },
            "payload": payload,
        }

    return handle


class ObservationSeam:
    """The ONE submitter. Every observation in M1 crosses this method and no other.

    CACHE- and STREAM-class observations append NOTHING (I9; design/22: recording scales with
    governance, never operation). They are counted into an in-memory aggregate for the
    measurement ledger and dropped. The aggregate is observability only: nothing load-bearing
    reads it, it is never appended, and killing it changes no answer (T-OBSERVABILITY-BOUNDARY).
    """

    def __init__(self, gate, observer=DEFAULT_OBSERVER):
        self.gate = gate
        self.observer = observer
        #: (window, class) -> count. Sampled aggregate. Appended nowhere.
        self.seen = {}
        #: (window, class) -> count of observations that produced a record.
        self.recorded = {}

    # ---- the sampled aggregate (observability only; never load-bearing) -----------------
    def _count(self, table, window, cls):
        key = (window, cls)
        table[key] = table.get(key, 0) + 1

    def totals(self):
        """The aggregate, for the measurement ledger. A pure read of in-memory counters."""
        return {"seen": dict(self.seen), "recorded": dict(self.recorded),
                "seen_total": sum(self.seen.values()), "recorded_total": sum(self.recorded.values())}

    def reset_totals(self):
        self.seen, self.recorded = {}, {}

    # ---- the one write path -------------------------------------------------------------
    def submit(self, obs):
        """Submit one observation. Returns the appended record, or None when the class map
        says this act is not recorded. Raises OpError on a refusal (recorded, cited)."""
        cls = obs.record_class                       # raises UnmappedAct on a window defect
        self._count(self.seen, obs.window, cls)
        if cls in classmap.NOT_RECORDED:
            return None
        opname = OP_FOR_WINDOW[obs.window]
        rec = self.gate.execute(opname, self.observer, {
            "window": obs.window,
            "window_version": obs.window_version,
            "occurrence_time": obs.occurrence_time,
            "act": obs.act,
            "object": obs.object,
            "time_source": obs.time_source,
            "data": obs.data,
            "principal": obs.principal,
            "source": obs.data.get("source"),
        })
        self._count(self.recorded, obs.window, cls)
        return rec

    def submit_all(self, observations):
        out = []
        for obs in observations:
            rec = self.submit(obs)
            if rec is not None:
                out.append(rec)
        return out


def m1_observe_ops(gate):
    """The M1 observation surface as the REGISTRY reports it — enumeration is the
    completeness guarantee. Returns {opname: meta} for every registered op that declares an
    `observe_window`, so a reader (and the structure guard) sees the whole surface and
    nothing else."""
    return {name: entry["meta"] for name, entry in gate.ops.items()
            if entry["meta"].get("observe_window")}
