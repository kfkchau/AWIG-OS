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


# =============================================================================================
# C7 P9 — THE OBSERVE WINDOWS UNDER OUR CORE (the B10 window census)
# =============================================================================================
#
# The five observe windows each open ONE Linux host facility our core does not present (L1 —
# the governance core names no Linux facility: the effect seam's twelve act kinds carry no
# /proc, inotify, netlink or sysfs). After the C7 swap a window that simply opened its facility
# would read something that is not there. B10 requires each window be SETTLED under our core,
# and NEVER left silently empty. This census names EACH of the five, DERIVED from OP_FOR_WINDOW
# (never hand-listed), and settles it one of two ways:
#
#   RE-SOURCED FROM THE CORE — the core presents the equivalent observation from ITS OWN state
#     (the record / the effect seam), NOT by adding a Linux facility (L1/L21). The settlement
#     names the CORE ROUTE; a re-sourced window whose route names a Linux facility is a body
#     widening and is REFUSED (the A3 guard).
#   DECLARED ABSENT AS A RECORD — the core presents no equivalent that is SERVED to a window
#     today. The settlement names the host facility (not presented under our core) and the
#     MEASURED reason: the named re-source route that would serve it is a body-lane slice not
#     wired into observe here. Never quietly skipped, never silently empty.
#
# A window that is NEITHER re-sourced NOR declared-absent-with-reason is a SILENT-EMPTY window,
# and the census REFUSES it (SilentEmptyWindow). That refusal is B10's own failing check: a new
# observe op added to OP_FOR_WINDOW without settling its window under our core reds the census.

#: Grow-only registry: window -> the CORE ROUTE that serves it from the core's OWN state (the
#: record / the effect seam), never a Linux facility. A body-lane slice that wires a window's
#: observation to the core's own state registers its route here and the census flips that
#: window to RE-SOURCED. EMPTY TODAY, and that is the MEASURED truth of the observe (Python)
#: lane: no window is served from the core's own state here — each re-source is a named
#: body-lane slice not taken in this unit (WINDOW_ABSENT_ROUTE). Grow-only like ACT_KINDS.
#:
#: THE FILE WINDOW IS RE-SOURCED FROM THE RECORD (C7-MAINT-FILE-WINDOW-FROM-RECORD, the B10
#: demonstration ruled at P9's close): a file change under our core IS a recorded write act,
#: so the file window's route under our core is the record's OWN write acts — read from the
#: record, never from a host facility (L21). windows.RecordFileWindow realizes this route;
#: this entry flips the census for the file window to RE-SOURCED. The route text names the
#: core's own state only and NO Linux facility token (or the census's own A3 guard,
#: _route_names_linux_facility, would refuse it as a body widening).
#: THE DEVICE WINDOW IS RE-SOURCED FROM THE RECORD'S DISCOVERY ROWS (C7 P7b): at bring-up the
#: freestanding body records one discovery row per device it performs over the settled three-device
#: list (block, network, clock; Q4 :3919), each riding the record-pen act. windows.RecordDeviceWindow
#: realizes this route; this entry flips the census for the device window to RE-SOURCED. The route
#: text names the core's own state (the discovery rows) and the identity the body EXPORTS at bring-up
#: — and NO Linux facility token (or the census's own A3 guard, _route_names_linux_facility, would
#: refuse it as a body widening).
CORE_ROUTES = {
    "file": ("the core's own record of write acts (append a record, write-once a file by "
             "temp-and-swap, declare a directory, remove, the writer's lock — L21): the file "
             "window reads the record's own write-act entries, not a host facility"),
    "device": ("the body's own device-discovery rows (C7 P7b): at bring-up the freestanding body "
               "records one discovery row per device it performs over the settled three-device "
               "list — its own block (the ata verdict), network (the wire self-check's class plus "
               "the offered MAC) and clock (the RTC's presence + epoch) drivers — each row riding "
               "the record-pen act; the device window reads those discovery rows from the record, "
               "not a host scan"),
}

#: Per-window MEASURED reason its re-source is not served under our core today: the specific
#: core route (the core's own state) that WOULD re-source it, named so the absent record is
#: measured, never a blanket "unavailable". Keyed by the OP_FOR_WINDOW window name.
WINDOW_ABSENT_ROUTE = {
    "process": ("a core execution-state surface (the core keeps a RECORD of acts by actors, "
                "not a live process table), a body-lane surface not built and not wired to a "
                "window here"),
    "file": ("the core's OWN record of write acts (append / write-once / remove) — under our "
             "core a file change IS a recorded write act, so the re-source would read the "
             "record, not inotify — a body-lane wiring not taken in this unit"),
    "mount": ("worlds-as-namespaces on the record disk (L21; C7 P3b-5a — a mount under our "
              "core is a world/namespace), state not wired to a window here"),
    "device": ("the body's own device-discovery rows (C7 P7b): the body records one discovery row "
               "per device it performs at bring-up (block/network/clock), so the re-source reads "
               "those rows from the record, not a host scan — realized by RecordDeviceWindow (this "
               "is the live re-source; consulted only when a test overrides the core routes)"),
    "connection": ("the socket act, the one connection (C7 P3b-6) — the core's own network "
                   "state not wired to a window here yet"),
}

#: Tokens that name a Linux host facility. A settlement claiming RE-SOURCED whose core route
#: contains one of these is re-sourcing a window BY ADDING A HOST FACILITY to the body — the
#: exact L1/L21 widening B10 forbids — so the census refuses it (the A3 guard, able to fire).
_LINUX_FACILITY_TOKENS = ("/proc", "inotify", "mountinfo", "/sys", "netlink", "sock_diag",
                          "uevent", "procnet", "/proc/net", "sysfs")

WINDOW_STATE_RESOURCED = "re-sourced"
WINDOW_STATE_ABSENT = "absent"


class SilentEmptyWindow(Exception):
    """A window enumerated by the census that is NEITHER re-sourced NOR declared-absent-with-
    reason — it would yield nothing and say nothing. B10's forbidden state; the census's own
    failing check (a new observe op with no under-our-core settlement reds here)."""


class BodyWideningWindow(Exception):
    """A window settled RE-SOURCED whose core route names a Linux host facility — re-sourcing a
    window by ADDING a host facility to the body, refused by L1/L21 (the A3 guard)."""


def _route_names_linux_facility(route):
    text = str(route)
    return any(tok in text for tok in _LINUX_FACILITY_TOKENS)


def _derived_window_names():
    """The five window names, DERIVED from OP_FOR_WINDOW and CROSS-CHECKED against the window
    classes in windows.py — never hand-listed. Raises if the two disagree (the set could not
    be derived: STOP condition (b) of the plan). Import is deferred to avoid the windows<->seam
    import cycle."""
    from . import windows as _windows                                     # deferred: cycle
    op_names = set(OP_FOR_WINDOW)
    #: the window classes whose `name` is one of the observation-surface windows.
    class_names = {type(w).name for w in _windows.default_windows()
                   if type(w).name in op_names}
    if class_names != op_names:
        raise ValueError(
            "the observe windows cannot be DERIVED: OP_FOR_WINDOW names %s but windows.py "
            "presents %s for those names — the census set is derived from the registry, never "
            "guessed (C7 P9 STOP (b))" % (sorted(op_names), sorted(class_names)))
    #: preserve OP_FOR_WINDOW's declared order.
    return [w for w in OP_FOR_WINDOW]


def _host_facility_for(window):
    """The Linux host facility the window reads, from its OWN static descriptor in windows.py
    (windows.<Window>.host_facility) — read, never probed, so the census names the facility
    without opening it. Deferred import (cycle)."""
    from . import windows as _windows                                     # deferred: cycle
    for w in _windows.default_windows():
        if type(w).name == window:
            fac = getattr(type(w), "host_facility", None)
            if fac:
                return fac
    raise ValueError("window %r declares no host_facility descriptor in windows.py — the "
                     "census cannot name what it reads (C7 P9 STOP (b))" % (window,))


def settle_window(window, core_routes=None):
    """Settle ONE window under our core. Returns a settlement record:

        {'window', 'state': 're-sourced', 'core_route'}                      (re-sourced)
        {'window', 'state': 'absent', 'host_facility', 'reason'}             (declared absent)

    Raises SilentEmptyWindow when the window is neither re-sourced nor declared-absent-with-
    reason (B10's forbidden silent-empty state); raises BodyWideningWindow when a re-sourced
    route names a Linux host facility (the L1/L21 widening — the A3 guard)."""
    routes = CORE_ROUTES if core_routes is None else core_routes
    if window in routes:
        route = routes[window]
        if _route_names_linux_facility(route):
            raise BodyWideningWindow(
                "the %r window is settled RE-SOURCED but its core route %r names a Linux host "
                "facility — re-sourcing a window by adding a host facility to the body is "
                "refused (L1/L21; C7 P9 A3)" % (window, route))
        return {"window": window, "state": WINDOW_STATE_RESOURCED, "core_route": route}
    reason = WINDOW_ABSENT_ROUTE.get(window)
    if not reason:
        raise SilentEmptyWindow(
            "the %r window is neither re-sourced (no core route registered) nor declared "
            "absent (no measured re-source route) under our core — a SILENT-EMPTY window, "
            "which B10 refuses: settle it (a core route, or a measured absent reason)" % (window,))
    facility = _host_facility_for(window)
    return {
        "window": window,
        "state": WINDOW_STATE_ABSENT,
        "host_facility": facility,
        "reason": ("the host facility %r is not presented under our core (the governance core "
                   "names no Linux facility, L1); the core route that would re-source it is %s"
                   % (facility, reason)),
    }


def window_census(extra_windows=(), core_routes=None):
    """The B10 window census under our core. Enumerates the five windows DERIVED from
    OP_FOR_WINDOW (cross-checked against windows.py) and settles EACH — re-sourced with its
    core route, or absent with its measured reason — so no window is silently empty.

    Returns a list of settlement records in OP_FOR_WINDOW order. Raises SilentEmptyWindow /
    BodyWideningWindow on the forbidden states (the census's own failing checks).

    `extra_windows` appends window NAMES the caller wants settled beside the five — used to
    PLANT a silent-empty window (a name with no settlement) and drive the census's failing
    check. `core_routes` overrides the live CORE_ROUTES so a test can drive the re-sourced
    arm (a valid core route settles re-sourced; a Linux-facility route reds) without the live
    registry claiming a route the body does not serve."""
    names = _derived_window_names()
    for extra in extra_windows:
        if extra not in names:
            names.append(extra)
    return [settle_window(w, core_routes=core_routes) for w in names]
