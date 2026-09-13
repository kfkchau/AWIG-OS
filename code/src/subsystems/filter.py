# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS filter subsystem — the firewall as rules IN the record (design/51 N8, EP-52).

A FILTER-DECISION is a recorded, rule-citing DECISION: a connection ADMITTED or REFUSED, citing
a FILTER-RULE (a CREATE-RULE of law class NET-LAW-FILTER) over a socket the record OPENED (EP-48,
sockets.py). This module holds only the DERIVED VIEW — the which-rule-decided census is a FOLD
over those decisions, exactly the division sockets.py runs for the wire and comms.py for channels:
the fold reduces the record, it decides nothing (the S-plane).

The op DEFINITION lives in the founding pack (`founding/founding-pack.json`, step `08r-filter-op`),
its law `NET-LAW-FILTER` in `05p-filter-law`; the generic interpreter re-registers the op from the
record at boot (the EP-14B convention — no op-definition dict lives here). This module keeps only
its derived view.

THE FIREWALL IS RULES IN THE RECORD, NOT A TABLE BESIDE IT (design/51 §5, the wrong reference):
'which rule dropped this' is a FOLD over the FILTER-DECISION acts here, never a cache with no
record of WHY. THE ENFORCEMENT SEAM IS NAMED, GUEST-ONLY: the record DECIDES and NAMES its seam
(guest-netfilter); the guest kernel's netfilter DROPS the real packet; the host record never claims
the drop (DIGEST-C4 §6). Per-packet traffic is STREAM — never a record.

NOTHING IS STORED (T-CACHE-KILL, design/51 N1). Kill `_cache` and replay the record and the same
census comes back. This fold reads ONLY the FILTER-DECISION action and NEVER a socket act or a
channel act — the wire fold (sockets.py, SOCKET-*), the channel fold (comms.py, COMMS-*) and this
filter fold are DISJOINT in the record by construction (N2): the filter DECIDES OVER the socket
table (it references a connection SOCKET-OPEN established) but it never reads a socket act into its
own census and never rewrites one.
"""

#: The filter act, in one place — the closed action set this fold reads and nothing else.
FILTER_ACTIONS = ("FILTER-DECISION",)


class FilterView:
    """Reads the which-rule-decided census out of the record. Holds no census between calls except
    a killable cache proven identical on recompute (T-CACHE-KILL)."""

    def __init__(self, store):
        self.store = store
        self._cache = {}

    # ---- the fold (S-plane mechanism: it reduces rows, it decides nothing) -----------------

    def _fold(self, as_of=None):
        """{connection: {connection, rule, decision, seam, entity, seq}} — for every connection a
        FILTER-DECISION has decided, the CURRENT deciding rule (the LATEST decision per connection
        wins, so a re-decision supersedes). Keyed by the connection the record decided over, never
        a name the caller supplied. This IS the census N8 calls a fold: 'which rule dropped this'
        is read here, never inferred and never held in a table beside the record."""
        decided = {}
        for e in self.store.action_set_projection(set(FILTER_ACTIONS)).all(as_of):
            p = e.get("payload") or {}
            conn = p.get("connection")
            decided[conn] = {"connection": conn, "rule": p.get("rule"),
                             "decision": p.get("decision"), "seam": p.get("seam"),
                             "entity": p.get("entity"), "seq": e["seq"]}
        return decided

    def which_rule_decided(self, as_of=None):
        """THE WHICH-RULE-DECIDED CENSUS — a fold, memoised in a KILLABLE cache. `kill_cache()`
        clears it and the next read recomputes an identical census from the record alone
        (T-CACHE-KILL): the cache is a convenience, never the truth."""
        if as_of not in self._cache:
            self._cache[as_of] = self._fold(as_of)
        return self._cache[as_of]

    def kill_cache(self):
        """Drop every cached census. The record is untouched; the next read re-folds it."""
        self._cache = {}

    # ---- projections read straight off the same fold (never a second fold) ------------------

    def rule_for(self, connection, as_of=None):
        """The rule that currently decides one connection, or None if no FILTER-DECISION decided
        it. The answer to 'which rule dropped this', read from the record."""
        row = self.which_rule_decided(as_of).get(connection)
        return row["rule"] if row else None

    def rules_that_decided(self, as_of=None):
        """The SET of FILTER-RULEs that have decided any connection — the census of deciding rules.
        A firewall as a table beside the record could not answer this; the fold does."""
        return {row["rule"] for row in self.which_rule_decided(as_of).values()}

    def refusals(self, as_of=None):
        """{connection: row} for every connection whose current decision is REFUSE — the connections
        the firewall is refusing, with the deciding rule and the named guest-netfilter seam."""
        return {c: row for c, row in self.which_rule_decided(as_of).items()
                if row.get("decision") == "refuse"}
