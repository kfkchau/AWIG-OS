# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""M1 W2 — the observation class map: the design/10 legend applied to observation.

The legend is `design/10-SYSCALL-CONFORMANCE-MAP.md` §2 (the five recording classes and
what each means); the APPLICATION to observation is `planning/11-STAGE-1-WATCH-AND-RECORD.md`
§2, which is M1's stage spec and controls here:

  1. changes a rule of rules (a mount rule, a driver capability appearing) -> LAW
  2. a state-changing act the box authored (a write, a bind, a process admit)  -> DECISION
  3. an external arrival the box did not author (an interrupt, a completion)   -> INPUT
  4. derived state or raw high-frequency flow                                  -> NOT RECORDED

The map is DATA, per window, and it is TESTED, not assumed: a misclassification is an audit
failure even when nothing crashes (EP-22 W2). Every act a window can yield appears here
exactly once; a window yielding an act this map does not carry is a defect in the window, and
an act reaching the WRITE PATH that this map does not carry as recorded is refused there
(seam.py, the closed per-window vocabulary) — the caller never chooses a record's action.

WHY AN OBSERVED OPEN IS NOT A DECISION HERE, while design/10's `open` row says DECISION.
design/10's rows classify calls AWIG OS AUTHORIZES: an open is the explicit custody grant, so
when files take authority (EP-25) it is a gated, rule-cited DECISION. At M1 AWIG OS authorizes
nothing — Linux already decided — and the file window cannot tell an open-for-read (which
changes no state) from an open-for-write (whose state change surfaces separately, and IS
recorded, as the modify/close-write act). Recording the observed open would therefore both
mint records for pure reads and double-count the one state change. planning/11 §1's own file
row lists exactly `created / written / linked / unlinked / chmod` and does not list open, so
the stage spec and this derivation agree. The shape is identical at EP-25; the authority
differs — which is the EP's own honesty rule, not an exception to it.
"""

# The five classes (design/10 §2 legend, verbatim names).
LAW = "LAW"
DECISION = "DECISION"
INPUT = "INPUT"
CACHE = "CACHE"
STREAM = "STREAM"

#: Classes that produce a record. I9 / design/22: recording scales with GOVERNANCE, so a
#: CACHE read or a STREAM flow appends NOTHING — it is counted into a sampled aggregate for
#: the measurement ledger and nothing else (T-RATE-GOVERNANCE, observe scale).
RECORDED = (LAW, DECISION, INPUT)
NOT_RECORDED = (CACHE, STREAM)

#: window -> {observed act -> recording class}. The whole map, in one place, as data.
CLASS_MAP = {
    # planning/11 §1: "process created / exited, exec, credentials change -> DECISION (lifecycle)"
    "process": {
        "process-created": DECISION,
        "process-exited": DECISION,
        "process-exec": DECISION,
        "process-credentials-changed": DECISION,
        # the box's live process state read back is derived state -> not recorded
        "process-state-read": CACHE,
    },
    # planning/11 §1: "file created / written / linked / unlinked / chmod -> DECISION (files)"
    "file": {
        "file-created": DECISION,
        "file-modified": DECISION,
        "file-closed-write": DECISION,
        "file-removed": DECISION,
        "file-attr-changed": DECISION,      # chmod/chown — design/10: "amends file permission LAW"
        "file-moved-from": DECISION,        # design/10 rename row: namespace change, recorded
        "file-moved-to": DECISION,
        # seen by the window, deliberately NOT recorded (see the module note above)
        "file-opened": CACHE,
        "file-closed-noswrite": CACHE,
        "file-read": STREAM,                # design/10 read row: STREAM (audit) + CACHE (offset)
    },
    # planning/11 §1: "mount / unmount -> LAW / DECISION (mount rule)"; design/10 `mount` row: LAW.
    # A mount amends what a path MEANS — a rule of rules over the namespace — so both directions
    # are LAW: mounting installs the rule, unmounting retires it.
    "mount": {
        "mount-added": LAW,
        "mount-removed": LAW,
        "mount-attr-changed": LAW,          # design/10 `mount_setattr` row: mount-rule amendment
        "mount-usage-read": CACHE,          # statfs and friends: derived aggregate
    },
    # planning/11 §1: "driver bound / device added-removed -> LAW (capability) / DECISION (bind)"
    "device": {
        "device-capability-registered": LAW,
        "device-capability-removed": LAW,
        "device-bound": DECISION,
        "device-unbound": DECISION,
        "device-io": STREAM,                # design/10: I/O throughput on a device fd
        "device-state-read": CACHE,
    },
    # planning/11 §1: "connection opened / closed, socket state -> DECISION (comms)"
    "connection": {
        "connection-opened": DECISION,
        "connection-closed": DECISION,
        "connection-state-changed": DECISION,
        "connection-traffic": STREAM,
        "connection-state-read": CACHE,
    },
    # The INPUT class's window — interrupts, I/O completions, timer ticks (planning/11 §1's
    # last two rows) — needs eBPF/tracepoints or seccomp-notify. It is DECLARED here so the
    # class vocabulary is whole and the deferral is visible, and it is registered as a
    # DEFERRED window (windows.py) with the observed reason, never silently absent.
    "arrival": {
        "interrupt-arrived": INPUT,
        "io-completed": INPUT,
        "timer-tick": INPUT,
        "arrival-traffic": STREAM,
    },
    # EP-49B (design/51 §3 N4, §4): a fact an ungoverned PEER asserts across the tunnel is an
    # external arrival the box did not author -> INPUT (the world's CLAIM), never a DECISION the
    # record authors. This window has NO "peer-decision" act BY CONSTRUCTION: a peer cannot author
    # a decision in this box (T-PEER-RECORD-NOT-TRUSTED). What the record truthfully says about an
    # ungoverned peer is exactly what crossed and no more (design/51 §9 — the C6 cap). The peer's
    # per-packet flow is STREAM (design/51 §4 NET-INPUT's non-recorded companion; appends nothing).
    "peer": {
        "peer-asserted-fact": INPUT,        # a claim the peer makes about itself or the world
        "peer-state-changed": INPUT,        # connected / reset / closed-by-peer (design/51 §4 NET-INPUT)
        "peer-traffic": STREAM,             # bytes on the wire from the peer — never a record
    },
    # EP-49D (design/51 §3 N9): the RECEIPT — one row, one receipt, two bodies. A row sent from body
    # A is received at body B; B's RECEIPT is a state-changing act B AUTHORED (the receiver's OWN row
    # of a crossing) -> DECISION. The row it receives from A is an external arrival B did not author
    # -> INPUT (never a DECISION the record authors; N4's cap — identity is what crossed). B writes
    # only its OWN record (one pen per record, D08.30); the per-row wire flow between bodies is STREAM
    # (appends nothing). This window has NO act mapping A's claim to a DECISION — B never authors A's
    # decision (T-PEER-RECORD-NOT-TRUSTED, the border's neighbour discipline).
    "receipt": {
        "receipt-recorded": DECISION,       # B's own record of a crossing (the receiver's row, N9)
        "row-received": INPUT,              # a row sent from body A, received at B as INPUT
        "receipt-traffic": STREAM,          # per-row flow between two bodies — never a record
    },
}

#: The acts that reach the record, per window — the closed vocabulary the write path enforces.
RECORDED_ACTS = {w: tuple(sorted(a for a, c in acts.items() if c in RECORDED))
                 for w, acts in CLASS_MAP.items()}

#: The acts a window sees and deliberately drops, per window — the audit's own statement of
#: what it classified OUT. Named, so "not recorded" is a decision on the record, not a silence.
DROPPED_ACTS = {w: tuple(sorted(a for a, c in acts.items() if c in NOT_RECORDED))
                for w, acts in CLASS_MAP.items()}

WINDOWS = tuple(sorted(CLASS_MAP))


class UnmappedAct(ValueError):
    """A window yielded an act this map does not carry — a defect in the window, not in the
    world. Raised (not refused) because no record was proposed: nothing reached the gate."""


def classify(window, act):
    """The class of one observed act. Raises UnmappedAct if the window does not carry it —
    a window may never guess a class, and an unmapped act must never fall through as CACHE
    (a silent drop is precisely the audit failure W2 names)."""
    acts = CLASS_MAP.get(window)
    if acts is None:
        raise UnmappedAct(f"no class map for window {window!r} — the map is: {', '.join(WINDOWS)}")
    cls = acts.get(act)
    if cls is None:
        raise UnmappedAct(
            f"window {window!r} yielded act {act!r}, which its class map does not carry — "
            f"the map holds: {', '.join(sorted(acts))}")
    return cls


def is_recorded(window, act):
    return classify(window, act) in RECORDED
