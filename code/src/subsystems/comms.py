# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS comms subsystem — the governed core (design 03 §4.5).

Channels and messages as governed record: open/close and send/receive are recorded
DECISIONs; the queue state and the message ledger are derived views. Payload is
content-addressed (as files). Shared-memory GRANT is recorded (who shares which region
with whom, under what rule); the interior writes to userland shared memory are NOT
audited — the honest boundary (03 §4.5 [AUDIT-FIX 5]). Kernel-internal state is
shared-nothing: the record is the only shared medium inside the kernel.
"""

# The comms core op definitions (COMMS-OPEN / SEND / RECV / CLOSE / SHM-GRANT) and their law-name
# constants were RETIRED here in EP-14B: their one authoritative home is the founding pack,
# founding/founding-pack.json. The generic interpreter re-registers them from the record at boot;
# this module keeps only its derived view. Absence is guarded by
# tests/test_ep14b.py::test_no_module_op_definition_dicts_outside_the_founding.


from collections.abc import Mapping


class CommsView:
    def __init__(self, store):
        self.store = store

    def live_channels(self, as_of=None):
        """THE FOLD (EP-30-C1): {(entity, channel): role} for every LIVE opening.

        ONE FOLD, TWO PROJECTIONS — `open_channels` and `channels_of` are both READERS of this,
        for the reason `_live_namespace` gives for its own pair: whether a channel is live and
        whose it is are decided by the same acts in the same order, and two folds over one record
        are two readers that can disagree.

        KEYED BY (entity, channel) AND NOT BY NAME, which is the cure. The retired fold folded
        every opening into a `set()` of strings, so the derived state of every channel in the
        estate had no owner in it and two entities opening one name were one entry.

        THE CLOSE IS NOW WHOSE-KEYED, AND THAT CAP IS CURED (EP-49C; the raise this fold carried
        since EP-30-C1). A `COMMS-CLOSE` carries only `channel`, so whose channel it closes cannot
        come from the payload — it comes from the closer, the record's own ACTOR, which is
        unforgeable by construction. A close drops exactly `(actor, channel)` — the closer's own
        opening — and leaves a second entity's same-named opening live. COMMS-CLOSE's own
        `live_present` check (opdefs.py, EP-49C) refuses a close by an entity that holds no such
        opening, so the entry this pop names is present whenever a close is recorded; a close by a
        non-holder is refused, not silently dropping nothing. Two folds over one record cannot
        disagree here because this is the SAME whose-keyed close `live_present` folds (comms.py and
        opdefs read one record, one polarity of the close, one keying)."""
        live = {}
        # K12 FAMILY SOURCE (MAINT-K12-SUBSYSTEM-VIEWS; design/36 ADDENDUM S). Live channel
        # openings depend only on COMMS-OPEN / COMMS-CLOSE records, so read that family through
        # the existing config-keyed projection (store.action_set_projection) rather than the whole
        # record. Only the iteration SOURCE moves; the fold body is byte-identical.
        for e in self.store.action_set_projection(
                {"COMMS-OPEN", "COMMS-CLOSE"}).all(as_of):
            a, p = e["action"], (e.get("payload") or {})
            if a == "COMMS-OPEN":
                live[(p.get("entity"), p["channel"])] = p.get("role")
            elif a == "COMMS-CLOSE":
                live.pop((e.get("actor"), p["channel"]), None)
        return live

    def declared_roles(self, as_of=None):
        """THE TWO ROLES, READ OUT OF THE LAW'S OWN RECORD (EP-30-C1) — never a literal here.

        The role vocabulary is declared once, in `COMMS-OPEN`'s `value_domain` check in the
        founding pack. A tuple spelled in this module beside that one would be two vocabularies,
        and the whole subject of this unit is a name that meant two things. LATEST WINS: a
        definition amended later is the one in force, so the last matching record is read."""
        roles = ()
        # K12 FAMILY SOURCE (MAINT-K12-SUBSYSTEM-VIEWS). This read consumes the OP-DEFINITION
        # records — the ones carrying a `name` and a Mapping `definition` — which is the CREATE-OP
        # / AMEND-OP family and NOT the COMMS DECISION family the other two folds read: the role
        # vocabulary is declared in COMMS-OPEN's founding op definition and amended by AMEND-OP,
        # so the answer depends on the op-definition family and costs only it. A RETIRE-OP carries
        # no definition and the fold body below skips it (isinstance is False), so widening to it
        # would change no answer; the set is exactly what the read consumes. Fold body unchanged.
        for e in self.store.action_set_projection(
                {"CREATE-OP", "AMEND-OP"}).all(as_of):
            p = e.get("payload") or {}
            definition = p.get("definition")
            # A RECORDED RECORD IS FROZEN ALL THE WAY DOWN (`store._freeze`), so a stored
            # definition arrives as a Mapping and NOT as a `dict` — `isinstance(x, dict)` is
            # False for a mappingproxy, and this read silently returned NOTHING under that
            # spelling. Duck-typed against the abstract Mapping, which both forms satisfy.
            if p.get("name") == "COMMS-OPEN" and isinstance(definition, Mapping):
                for c in (definition.get("checks") or []):
                    if c.get("check") == "value_domain" and c.get("param") == "role":
                        roles = tuple(c.get("domain") or ())
        return roles

    def channels_of(self, entity, as_of=None):
        """WHOSE CHANNEL IS THIS AND WHICH OF THE TWO IS IT (EP-30-C1; design/39 §6 bullet 1).

        {role: channel-name-or-None} over the roles the LAW declares — so a role with no live
        channel is reported as ABSENT rather than omitted. An omitted key and a key holding None
        read the same to a careless caller and differently to a careful one; the law's own
        declared set is what makes the absence sayable at all."""
        answer = {role: None for role in self.declared_roles(as_of)}
        for (ent, channel), role in self.live_channels(as_of).items():
            if ent == entity:
                answer[role] = channel
        return answer

    def open_channels(self, as_of=None):
        """THE LIVE CHANNEL NAMES — a PROJECTION of `live_channels`, not a second fold.

        Its meaning is unchanged from the retired implementation (the set of live names), so every
        reader that asks this question keeps its answer. What moved is that the set is now DERIVED
        from a fold that knows the owner, rather than being the primary state that never did."""
        return {channel for (_entity, channel) in self.live_channels(as_of)}

    def queue_depth(self, channel, as_of=None):
        sent = len([e for e in self.store.by_action("COMMS-SEND", as_of)
                    if (e.get("payload") or {}).get("channel") == channel])
        recv = len([e for e in self.store.by_action("COMMS-RECV", as_of)
                    if (e.get("payload") or {}).get("channel") == channel])
        return sent - recv

    def message_ledger(self, channel, as_of=None):
        # K12 FAMILY SOURCE (MAINT-K12-SUBSYSTEM-VIEWS): a channel's ledger is folded from the
        # COMMS-SEND / COMMS-RECV records; read that family, not the whole record. Filter body
        # byte-identical.
        return [e for e in self.store.action_set_projection(
                    {"COMMS-SEND", "COMMS-RECV"}).all(as_of)
                if e["action"] in ("COMMS-SEND", "COMMS-RECV")
                and (e.get("payload") or {}).get("channel") == channel]

    def shm_grants(self, as_of=None):
        return {(e["payload"])["region"]: e["payload"]
                for e in self.store.by_action("SHM-GRANT", as_of)}
