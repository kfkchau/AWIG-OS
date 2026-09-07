# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""Process-lifecycle observer (M1, first adapter).

Watches process create/exit via /proc and records each as a lifecycle DECISION
through the gate (design/11-STAGE-1 §1–§2; one write path, `02 §1.2`). The scanner is
injectable so the diff logic is tested deterministically, without depending on live
system processes. `/proc` is trained-knowledge Linux (Estimate — High).

At M1 the box's activity already happened under Linux's authority; AWIG OS records it.
So an observed lifecycle crossing is recorded with provenance = the window it was seen
through (`/proc`) and asserted_by = the watcher — not a AWIG OS-authored decision. When
files take authority (M2) the same crossings become AWIG OS's own gated decisions; the
record shape is identical, the authority differs.
"""

import os

# SUPERSEDED IN FUNCTION BY THE M1 SEAM (EP-22). `observe/seam.py` + `observe/windows.py` are
# the observation surface: they pin asserted_by + window@version + the window-reported
# occurrence time on every record, and their ops refuse a call missing any of the three. This
# module and `resource_watch.py` predate those pins and are kept live only as the subject of
# two other EPs' ledger tests (the conservation guard reading the record's action, and the
# preserved-provenance boundary). The two surfaces DO NOT COMPOSE — registering the seam on a
# gate that already holds OBSERVE-RESOURCE refuses and says why — and retiring this pair needs
# those two ledgers re-homed onto the new surface, which is another EP's fence. RAISED at EP-22.

# The observation law this adapter cites. [ADJACENT FIX, EP-22:] this was "OBS-1", which names
# NO recorded rule — the founding pack has never carried one, so every record this adapter
# wrote cited a law that does not exist and T-EXPLANATION held only textually. The correct
# citation was already standing in the founding: SYS-RECORD, the root law reading "SYSTEM may
# record any activity as evidence (recording is not permission to perform)", which is exactly
# M1's honesty rule. No new rule was minted and the founding is untouched.
OBS_RULE = "SYS-RECORD"


def scan_proc():
    """Snapshot live processes: {pid: {"comm": str}} from /proc."""
    out = {}
    try:
        names = os.listdir("/proc")
    except FileNotFoundError:
        return out
    for name in names:
        if not name.isdigit():
            continue
        pid = int(name)
        try:
            with open(f"/proc/{pid}/comm", "r", encoding="utf-8", errors="replace") as f:
                comm = f.read().strip()
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue  # the process exited between listdir and read — a normal race
        out[pid] = {"comm": comm}
    return out


def register_observe_ops(gate, store):
    """Register the observe op on the gate so observations use the one write path."""

    def observe_process(actor, params):
        return {
            "actor": "SYSTEM",
            "action": params["event"],  # process-created | process-exited
            "object": f"proc:{params['pid']}",
            "rule_cited": OBS_RULE,
            "provenance": {"asserted_by": "process-watcher", "source": "/proc", "could_read": ["/proc"]},
            "payload": {"pid": params["pid"], "comm": params.get("comm")},
        }

    gate.register(
        "OBSERVE-PROCESS",
        {"description": "record an observed process lifecycle crossing",
         "rules": [OBS_RULE], "params": {"event": "required", "pid": "required"}},
        observe_process,
    )


class ProcessWatcher:
    """Diffs successive /proc snapshots and records the lifecycle crossings.

    The first poll establishes the baseline: everything currently running is recorded
    as observed-created as of observation start (honest — they exist as of now).
    """

    def __init__(self, gate, scan=scan_proc):
        self.gate = gate
        self.scan = scan
        self.prev = {}

    def poll(self):
        cur = self.scan()
        recorded = []
        for pid in cur:
            if pid not in self.prev:
                recorded.append(self.gate.execute(
                    "OBSERVE-PROCESS", "process-watcher",
                    {"event": "process-created", "pid": pid, "comm": cur[pid]["comm"]}))
        for pid in self.prev:
            if pid not in cur:
                recorded.append(self.gate.execute(
                    "OBSERVE-PROCESS", "process-watcher",
                    {"event": "process-exited", "pid": pid, "comm": self.prev[pid]["comm"]}))
        self.prev = cur
        return recorded
