# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""Observe adapters for files, mounts, and connections (M1, completing the audit product).

Same pattern as the process watcher: a scanner returns a {key: attrs} snapshot, the diff
against the last snapshot is recorded through the gate as appeared/changed/removed
crossings (one write path). Real scanners read /proc and the filesystem; tests inject
snapshots deterministically. Linux stays authoritative; AWIG OS only records. /proc and
os.stat are trained-knowledge Linux facilities.
"""

import os

# SUPERSEDED IN FUNCTION BY THE M1 SEAM (EP-22) — see the note at the head of
# `process_watch.py`. The two observe surfaces do not compose, and this pair stays live only
# as the subject of two other EPs' ledger tests. RAISED at EP-22.

# [ADJACENT FIX, EP-22:] was "OBS-1", which names no recorded rule. SYS-RECORD is the standing
# root law for exactly this — "SYSTEM may record any activity as evidence (recording is not
# permission to perform)". The founding is untouched; the citation now resolves.
OBS_RULE = "SYS-RECORD"


def register_resource_observe_ops(gate, store):
    def observe(actor, params):
        return {"actor": "SYSTEM", "action": params["event"], "object": params["object"],
                             "rule_cited": OBS_RULE,
                             "provenance": {"asserted_by": actor, "source": params.get("source"),
                                            "could_read": [params.get("source")]},
                             "payload": params.get("data", {})}
    gate.register("OBSERVE-RESOURCE",
                  {"description": "record an observed resource crossing (file/mount/connection)",
                   "rules": [OBS_RULE], "params": {"event": "required", "object": "required"}}, observe)


class DiffWatcher:
    """Diffs successive {key: attrs} snapshots; records appeared/changed/removed via the gate."""

    def __init__(self, gate, kind, scan, source):
        self.gate = gate
        self.kind = kind
        self.scan = scan
        self.source = source
        self.prev = {}

    def poll(self):
        cur = self.scan()
        rec = []
        for k, v in cur.items():
            if k not in self.prev:
                rec.append(self._emit("appeared", k, v))
            elif self.prev[k] != v:
                rec.append(self._emit("changed", k, v))
        for k in self.prev:
            if k not in cur:
                rec.append(self._emit("removed", k, self.prev[k]))
        self.prev = cur
        return rec

    def _emit(self, verb, key, attrs):
        data = {"key": key}
        if isinstance(attrs, dict):
            data.update(attrs)
        return self.gate.execute("OBSERVE-RESOURCE", "resource-watcher",
                                 {"event": f"{self.kind}-{verb}", "object": f"{self.kind}:{key}",
                                  "source": self.source, "data": data})


def scan_mounts():
    out = {}
    try:
        with open("/proc/mounts", "r", encoding="utf-8") as f:
            for line in f:
                p = line.split()
                if len(p) >= 3:
                    out[p[1]] = {"source": p[0], "fstype": p[2]}
    except FileNotFoundError:
        pass
    return out


def scan_dir(path):
    out = {}
    for root, _dirs, files in os.walk(path):
        for name in files:
            fp = os.path.join(root, name)
            try:
                st = os.stat(fp)
                out[fp] = {"size": st.st_size, "mtime": int(st.st_mtime)}
            except (FileNotFoundError, PermissionError):
                continue
    return out


def scan_connections():
    out = {}
    try:
        with open("/proc/net/tcp", "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                p = line.split()
                if len(p) >= 4:
                    out[f"{p[1]}-{p[2]}"] = {"state": p[3]}
    except FileNotFoundError:
        pass
    return out
