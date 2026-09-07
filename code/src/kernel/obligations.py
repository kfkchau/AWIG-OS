# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — the obligation executor + wait/wake (seam S3; design 28 §3 obligation, §5 due).

An obligation is a runtime WHEN/THEN law record — the EP-06 full-form family lowered to a temporal
DO: its `when` is a condition over RECORDED time (elapsed ticks) or an awaited action, its `then` is
an op invocation. The clock is a SENSOR, never a scheduler (15.1, RULED 2026-07-13): time enters the
system ONLY as recorded TICK arrivals (INPUT class), each carrying the sensor's `now`. `due()` reads
those RECORDED ticks — never the wall clock — to decide what is ripe. `run_due()` fires each ripe
obligation THROUGH THE GATE (sole-appender), and firing is DERIVED: a fired decision carries
`obligation_ref` back to its obligation, so "has it fired" is computed from the record, never stored.

This is the DO direction of EP-06's full-form pass, which EP-06 deliberately left for its named home:
the DON'T pass refuses at the gate; the DO executor fires obligations here.
"""

from .errors import OpError

# The obligation / clock / wait op definitions (TICK / CREATE-OBLIGATION / BLOCK-ON) and their
# law-name constants (TICK_POLICY / WAIT_POLICY / OBLIGATION_LAW) were RETIRED here in EP-14B: their
# one authoritative home is the founding pack, founding/founding-pack.json. The generic interpreter
# re-registers them from the record at boot; this module keeps only the runtime executor below (due /
# run_due / wait / wake, which key off recorded action and payload.kind, not these constants). Absence
# is guarded by tests/test_ep14b.py::test_no_module_op_definition_dicts_outside_the_founding.


def _tick_now(store, as_of=None):
    """The current RECORDED time = the latest tick's `now` (0 before the first tick). Read from the
    record only — never the wall clock — so replay is identical (the determinism claim, design 03 §1.3)."""
    return max(((e.get("payload") or {}).get("now", 0) for e in store.by_action("TICK", as_of)), default=0)


def _obligations(store, as_of=None):
    """Live obligations: the latest record per rule_id whose kind is 'obligation' (a fold, like the
    other law views). An obligation is a law record, so re-creating one is an amendment (latest wins)."""
    obs = {}
    for e in store.all(as_of):
        p = e.get("payload") or {}
        if p.get("kind") == "obligation" and p.get("rule_id"):
            obs[p["rule_id"]] = {**p, "seq": e["seq"]}
    return obs


def _params_corroborated(record, then_params):
    """W2/W3 completion of the standing theorem (firing evidence is the OUTCOME HAPPENING —
    PARAMETERS included). The outcome record must corroborate every PROMISED param: for each
    (k, v) in the obligation's then.params, the record must carry v where the outcome op recorded
    it — payload[k] == v (the general definition-born op: params flow to payload), or, when k is
    absent from the payload, v as the record's `object` or `target` (a payloadless code op like
    CREATE-INFO records its subject there). A recorded param that CONTRADICTS the promise (the
    finding's repro: right op + ref, wrong `proc`) fails corroboration, so the promise stays unmet
    and the obligation stays due. Erring toward not-fired (re-fire) beats a false 'done' — a record
    that lies about effect is the one forbidden lie."""
    payload = record.get("payload") or {}
    for k, v in (then_params or {}).items():
        if k in payload:
            if payload[k] != v:
                return False                              # a recorded param contradicts the promise
        elif record.get("object") != v and record.get("target") != v:
            return False                                  # the promised value appears nowhere the op recorded it
    return True


def _fired(store, obligation, as_of=None):
    """Has this obligation fired? DERIVED, never stored — but the evidence is the OUTCOME HAPPENING
    (EP-07B B2, completed by W3), not a bare marker: a record whose `action` equals the obligation's
    then-op, carrying obligation_ref back to it, with `seq` GREATER than the obligation's CURRENT
    version's seq, AND whose recorded parameters corroborate the obligation's then.params.
    - R21 (no forge-silencing): a forged ref on some OTHER act (action != then-op) does not count, so
      it cannot silence the obligation. HONEST NOTE: a forge that actually performs the then-op with
      the ref AND the promised params DOES count — correct, the obliged act genuinely happened.
    - W3 (no wrong-param completion): the then-op fired with the WRONG params (finding A3) does NOT
      count — the promised thing never happened, so the obligation stays due.
    - R22 (re-arm): keyed to the current version's seq, an AMENDED obligation (higher seq) is re-armed
      while a given version fires at most once."""
    then = obligation.get("then") or {}
    then_op = then.get("op")
    then_params = then.get("params") or {}
    ob_seq = obligation["seq"]
    return any(e["action"] == then_op
               and (e.get("payload") or {}).get("obligation_ref") == obligation["rule_id"]
               and e["seq"] > ob_seq
               and _params_corroborated(e, then_params)
               for e in store.all(as_of))


def due(store, as_of=None):
    """The firing list (design 28 §5; 25-view-tree.json due()): obligations whose condition is met by
    the RECORDED ticks/events and whose outcome has not yet happened for the current version. A
    read-only feed — it refuses nothing."""
    now = _tick_now(store, as_of)
    ripe = []
    for rid, o in _obligations(store, as_of).items():
        if _fired(store, o, as_of):
            continue                                   # its outcome already happened — never twice per version
        when = o.get("when") or {}
        if "elapsed_since" in when:
            # elapsed measured in the recorded clock: now minus the tick-time in effect at creation
            created_now = _tick_now(store, as_of=o["seq"])
            if now - created_now >= when["elapsed_since"]:
                ripe.append(o)
        elif "await_action" in when:
            if any(e["action"] == when["await_action"] and e["seq"] > o["seq"] for e in store.all(as_of)):
                ripe.append(o)
    return ripe


def run_due(store, gate):
    """The driver STEP (design 28 §5): fire every ripe obligation THROUGH THE GATE. What fires is
    decided ONLY by the record (due() reads recorded ticks, never the wall clock; 15.1 clock-as-sensor).
    Sole-appender discipline holds — the outcome op is invoked via the gate, never a direct append; the
    fired decision carries obligation_ref, so the next due() sees it fired without any status field.
    Not a loop and not wall-clock-driven: a step a driver/tick handler calls.

    B4 (R24): obligations are INDEPENDENT — one broken commitment gags nothing. A refused firing is
    already the recorded designed-stall for THAT obligation (the gate recorded it); run_due catches it,
    keeps sweeping, and returns {fired, refused} so both are visible."""
    fired, refused = [], []
    for o in due(store):
        then = o.get("then") or {}
        params = dict(then.get("params") or {})
        params["obligation_ref"] = o["rule_id"]        # the fired decision references its obligation
        try:
            gate.execute(then["op"], "SYSTEM", params)  # THROUGH THE GATE — sole appender
            fired.append(o["rule_id"])
        except OpError:
            refused.append(o["rule_id"])                # the gate already recorded the refusal; do not gag the rest
    return {"fired": fired, "refused": refused}
