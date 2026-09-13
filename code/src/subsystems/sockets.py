# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS sockets subsystem — the box's wire as governed record (design/51 §5, EP-48).

The six wire acts (SOCKET-OPEN / BIND / LISTEN / CONNECT / ACCEPT / CLOSE) are recorded,
rule-citing DECISIONs against the actor's record, each citing NET-LAW-GRANT (who may open
what, to where). This module holds only the DERIVED VIEW — the live socket table and its
connection projection are a fold over those six decisions, exactly the division `comms.py`
runs on for channels: the fold reduces the record, it decides nothing (the S-plane).

The op DEFINITIONS live in the founding pack (`founding/founding-pack.json`, step
`08n-socket-ops`), their law `NET-LAW-GRANT` in `05o-net-laws`, and the amended `syscall-ops`
map in `07b-syscall-ops-amendment`; the generic interpreter re-registers the ops from the
record at boot (the EP-14B convention — no op-definition dict lives here). This module keeps
only its derived view.

HOST-MODELLED: no real socket is opened by the kernel port on the host — the wire is a
MODELLED table (design/51 §5). The guest-real half is EP-48G.

NOTHING IS STORED (T-CACHE-KILL, design/51 N1). Kill `_cache` and replay the record and the
same table comes back — the socket table is a local inside a fold, never a second copy of the
record. `live_channels` (comms.py) and this table are DISJOINT in the record by construction
(N2, T-WIRE-NOT-CHANNEL): this fold reads only the six SOCKET-* actions and never a COMMS-*
one, and the channel fold reads only COMMS-OPEN/COMMS-CLOSE and never a SOCKET-* one.
"""

#: The six wire acts, in one place — the closed action set this fold reads and nothing else.
SOCKET_ACTIONS = ("SOCKET-OPEN", "SOCKET-BIND", "SOCKET-LISTEN",
                  "SOCKET-CONNECT", "SOCKET-ACCEPT", "SOCKET-CLOSE")

#: The state each wire act leaves a socket in — the observed lifecycle, as data.
_STATE_FOR = {
    "SOCKET-OPEN": "OPEN",
    "SOCKET-BIND": "BOUND",
    "SOCKET-LISTEN": "LISTEN",
    "SOCKET-CONNECT": "CONNECTED",
    "SOCKET-ACCEPT": "CONNECTED",
}

#: The acts that make a socket a live CONNECTION (the governed connection view the shadow
#: retires into): a connect or an accept. A close removes it; an open/bind/listen alone is not
#: yet a connection.
_CONNECTION_ACTS = ("SOCKET-CONNECT", "SOCKET-ACCEPT")


class SocketView:
    """Reads the live socket table out of the record. Holds no table between calls except a
    killable cache proven identical on recompute (T-CACHE-KILL)."""

    def __init__(self, store):
        self.store = store
        self._cache = {}

    # ---- the fold (S-plane mechanism: it reduces rows, it decides nothing) -----------------

    def _fold(self, as_of=None):
        """{socket: {socket, entity, family, state, address?, target?, peer?, seq}} for every
        LIVE socket. SOCKET-OPEN mints; bind/listen/connect/accept advance state and record what
        they carry; SOCKET-CLOSE removes. Keyed by the socket id the record established, never a
        name the caller supplied — the same cure comms.py's (entity, channel) keying is."""
        live = {}
        for e in self.store.action_set_projection(set(SOCKET_ACTIONS)).all(as_of):
            a, p = e["action"], (e.get("payload") or {})
            sid = p.get("socket")
            if a == "SOCKET-OPEN":
                live[sid] = {"socket": sid, "entity": p.get("entity"),
                             "family": p.get("family"), "state": "OPEN", "seq": e["seq"]}
            elif a == "SOCKET-CLOSE":
                live.pop(sid, None)
            elif sid in live:
                live[sid]["state"] = _STATE_FOR[a]
                live[sid]["seq"] = e["seq"]
                for f in ("address", "target", "peer"):
                    if p.get(f) is not None:
                        live[sid][f] = p[f]
        return live

    def live_sockets(self, as_of=None):
        """THE LIVE SOCKET TABLE — a fold, memoised in a KILLABLE cache. `kill_cache()` clears
        it and the next read recomputes an identical table from the record alone (T-CACHE-KILL):
        the cache is a convenience, never the truth."""
        if as_of not in self._cache:
            self._cache[as_of] = self._fold(as_of)
        return self._cache[as_of]

    def kill_cache(self):
        """Drop every cached table. The record is untouched; the next read re-folds it."""
        self._cache = {}

    # ---- the connection projection (the governed-authoritative connection view) ------------

    def connection_view(self, as_of=None):
        """{socket: {connection, state, entity, target?, peer?, seq}} for every LIVE connection —
        a socket the record CONNECTed or ACCEPTed and did not CLOSE. This IS the governed
        connection view the observe-plane shadow (observe/shadow.py m1-connection-state) retires
        INTO (:2646): a fold over the wire decisions, so killing every derived structure and
        replaying the record returns the same connections. A PROJECTION of the same fold, never a
        second fold — whether a socket is live and whether it is a connection are decided by the
        same acts in the same order."""
        out = {}
        for sid, row in self.live_sockets(as_of).items():
            # was this socket ever connected/accepted and not since closed? the fold already
            # dropped closed sockets; a socket that reached CONNECTED is a live connection.
            if row.get("state") == "CONNECTED":
                out[sid] = {"connection": sid, "state": row["state"], "entity": row.get("entity"),
                            "seq": row["seq"]}
                for f in ("target", "peer"):
                    if row.get(f) is not None:
                        out[sid][f] = row[f]
        return out

    def connection_states(self, as_of=None):
        """{connection-key: state} — the one field whose disagreement with the live box is real
        drift, the shape shadow.py's COMPARATORS read (`_shadow_keys_connection`). Lets the
        socket connection view be diffed against the box exactly as the shadow is."""
        return {k: v.get("state") for k, v in self.connection_view(as_of).items()}
