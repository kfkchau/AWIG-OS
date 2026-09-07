# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""M1 W3 — the shadow views: the box's state, derived from the record and nothing else.

Five views — process table, file history, mount table, device bindings, connection state.
Each one is:

  * a recorded VIEW DEFINITION (CREATE-VIEW, a governed act, replayable) that says WHICH
    records it looks at, in the engine's own closed trigger vocabulary. The definition is
    data; only the fold that reduces the selected rows is code (the S-plane, mechanism with
    zero governance value — the same division the estate's master views already run on);
  * a COVERAGE STATEMENT with two halves: what the definition itself excludes (derived
    mechanically by the engine from the definition alone) and what the WINDOW cannot see
    (declared by the window). Neither half is optional and neither is prose written here;
  * an asOf answer, because a fold over `store.all(as_of)` is what these are.

NOTHING IS STORED. Kill every table below, replay the record, and the same answers come back
— the tables are local variables inside a fold, not state (T-REPLAY / T-CACHE-KILL).

THE ANSWER NEVER CLAIMS CURRENCY IT CANNOT SHOW (R26 at observation scale). `answer()` is
always available and always labelled with the record position it reflects. `current()` is the
one that claims "this is the box right now", and it consults the windows before answering:
if the shadow and the live box disagree — because an adapter stopped, or a window went
unavailable — it REFUSES with the drift instead of serving a stale table. A hop never lies;
staleness is DETECTED, not silently served. This is the precursor of EP-25's shadow-diff gate.
"""

from . import classmap
from .seam import window_at_version

#: view name -> (window it shadows, one-line purpose)
SHADOW_VIEWS = {
    "m1-process-table": ("process", "which processes the record says are running"),
    "m1-file-history": ("file", "every recorded act on a file, in order"),
    "m1-mount-table": ("mount", "which filesystems the record says are mounted"),
    "m1-device-bindings": ("device", "which driver the record says holds which device"),
    "m1-connection-state": ("connection", "which connections the record says are open"),
}

VIEW_FOR_WINDOW = {window: name for name, (window, _) in SHADOW_VIEWS.items()}


class StaleShadow(Exception):
    """A currency claim that could not be met. Carries the drift, so the caller learns WHAT
    diverged rather than only that something did."""

    def __init__(self, view, drift):
        self.view = view
        self.drift = drift
        super().__init__(f"{view} cannot be served as current: {drift}")


def define_shadow_views(gate, actor="SYSTEM"):
    """Record the five view definitions as governed acts. Idempotent: re-defining a view by
    the same name is an amendment (latest-wins), so a second call changes no answer."""
    made = []
    for name, (window, purpose) in SHADOW_VIEWS.items():
        made.append(gate.execute("CREATE-VIEW", actor, {
            "name": name,
            # The engine's closed trigger vocabulary. `payload_kind` is what makes each
            # window's records selectable as a class: observing processes and observing
            # files are DIFFERENT information, so they carry different info kinds, and a
            # narrowed world can grant one without the other.
            "when": {"payload_kind": f"observed-{window}"},
            "then": {},          # a query view: it surfaces to its requester and pushes nowhere
        }))
    return made


# =============================================================================================
# The folds (S-plane mechanism: they reduce rows, they decide nothing)
# =============================================================================================

def _fold_process(rows):
    table = {}
    for e in rows:
        p = e.get("payload") or {}
        obs = p.get("observed") or {}
        key = obs.get("key")
        if e["action"] == "process-created":
            table[key] = {"pid": key, "comm": obs.get("comm"), "uid": obs.get("uid"),
                          "started": e.get("occurrence_time"), "seq": e["seq"]}
        elif e["action"] == "process-exited":
            table.pop(key, None)
        elif e["action"] == "process-credentials-changed" and key in table:
            table[key].update({"comm": obs.get("comm"), "uid": obs.get("uid"), "seq": e["seq"]})
    return table


def _fold_file(rows):
    """File HISTORY, not a file table: every recorded act on a path, in record order. The
    'does this path exist' question is derived from the last act, never stored."""
    hist = {}
    for e in rows:
        p = e.get("payload") or {}
        path = (p.get("observed") or {}).get("path")
        hist.setdefault(path, []).append({
            "act": e["action"], "seq": e["seq"], "occurrence_time": e.get("occurrence_time"),
            "record_time": e["record_time"], "time_source": p.get("time_source")})
    return hist


def _fold_mount(rows):
    table = {}
    for e in rows:
        obs = (e.get("payload") or {}).get("observed") or {}
        key = obs.get("key")
        if e["action"] in ("mount-added", "mount-attr-changed"):
            table[key] = {"mount_point": key, "fstype": obs.get("fstype"),
                          "source": obs.get("source"), "options": obs.get("options"),
                          "seq": e["seq"]}
        elif e["action"] == "mount-removed":
            table.pop(key, None)
    return table


def _fold_device(rows):
    table = {}
    for e in rows:
        obs = (e.get("payload") or {}).get("observed") or {}
        key = obs.get("key") or obs.get("devpath")
        act = e["action"]
        if act == "device-capability-registered":
            table[key] = {"device": key, "subsystem": obs.get("subsystem"),
                          "driver": obs.get("driver"), "seq": e["seq"]}
        elif act == "device-capability-removed":
            table.pop(key, None)
        elif act == "device-bound":
            table.setdefault(key, {"device": key, "subsystem": obs.get("subsystem")})
            table[key].update({"driver": obs.get("driver"), "seq": e["seq"]})
        elif act == "device-unbound" and key in table:
            table[key].update({"driver": None, "seq": e["seq"]})
    return table


def _fold_connection(rows):
    table = {}
    for e in rows:
        obs = (e.get("payload") or {}).get("observed") or {}
        key = obs.get("key")
        if e["action"] in ("connection-opened", "connection-state-changed"):
            table[key] = {"connection": key, "state": obs.get("state"), "uid": obs.get("uid"),
                          "seq": e["seq"]}
        elif e["action"] == "connection-closed":
            table.pop(key, None)
    return table


FOLDS = {"m1-process-table": _fold_process, "m1-file-history": _fold_file,
         "m1-mount-table": _fold_mount, "m1-device-bindings": _fold_device,
         "m1-connection-state": _fold_connection}


# ---- how a shadow row compares with what the window reports live ---------------------------
# The shadow is derived from records; the window reports the box. They are different shapes,
# so each view names the ONE field whose disagreement is real drift rather than churn.

def _live_keys_process(live):
    return {k: v.get("comm") for k, v in live.items()}


def _live_keys_mount(live):
    return {k: v.get("fstype") for k, v in live.items()}


def _live_keys_device(live):
    return {k: v.get("driver") for k, v in live.items()}


def _live_keys_connection(live):
    return {k: v.get("state") for k, v in live.items()}


def _live_keys_file(live):
    return {k: None for k in live}


def _shadow_keys_process(table):
    return {k: v.get("comm") for k, v in table.items()}


def _shadow_keys_mount(table):
    return {k: v.get("fstype") for k, v in table.items()}


def _shadow_keys_device(table):
    return {k: v.get("driver") for k, v in table.items()}


def _shadow_keys_connection(table):
    return {k: v.get("state") for k, v in table.items()}


def _shadow_keys_file(history):
    """A path exists iff its LAST recorded act was not a removal — derived, never stored."""
    gone = ("file-removed", "file-moved-from")
    return {p: None for p, acts in history.items() if acts and acts[-1]["act"] not in gone}


COMPARATORS = {
    "m1-process-table": (_shadow_keys_process, _live_keys_process),
    "m1-file-history": (_shadow_keys_file, _live_keys_file),
    "m1-mount-table": (_shadow_keys_mount, _live_keys_mount),
    "m1-device-bindings": (_shadow_keys_device, _live_keys_device),
    "m1-connection-state": (_shadow_keys_connection, _live_keys_connection),
}


# =============================================================================================
# The shadow surface
# =============================================================================================

class ShadowViews:
    """Reads the five shadow views out of the record. Holds no table between calls."""

    def __init__(self, store, views, windows=None):
        self.store = store
        self.views = views
        #: window name -> the Window object, for the currency check only. A view NEVER
        #: answers a query from a window; it answers from the record.
        self.windows = {w.name: w for w in (windows or [])}

    # ---- the rows a definition selects -------------------------------------------------
    def rows(self, name, as_of=None):
        """The records this view's DEFINITION selects — run through the engine, so the
        definition really is what governs the selection and not a filter written here."""
        out = self.views.execute_view(name, as_of)
        if out is None:
            raise KeyError(f"{name} is not a defined view — define_shadow_views has not run")
        return out["rows"]

    # ---- the answer ---------------------------------------------------------------------
    def answer(self, name, as_of=None):
        """The view's table, folded from the record, labelled with what it reflects and what
        it cannot see. Makes NO currency claim — see `current`."""
        rows = self.rows(name, as_of)
        window = SHADOW_VIEWS[name][0]
        return {
            "view": name,
            "window": window,
            "table": FOLDS[name](rows),
            "rows": len(rows),
            # Exactly what this answer reflects: the record position it was folded through.
            "derived_through_seq": as_of if as_of is not None else len(self.store.all()),
            "as_of": as_of,
            "coverage": self.coverage(name),
            "claims_currency": False,
        }

    def current(self, name):
        """The table AS THE BOX IS NOW — or a refusal. Consults the window, compares, and
        refuses with the drift rather than serving a shadow that has stopped tracking.
        Coherent-or-refuse: a stale answer is never served as a current one."""
        tracking = self.tracks(name)
        if not tracking["tracks"]:
            raise StaleShadow(name, tracking)
        out = self.answer(name)
        out["claims_currency"] = True
        out["checked_against"] = tracking["window_at_version"]
        return out

    # ---- shadow-diff (T-SHADOW-TRACKS; the precursor of EP-25's gate) -------------------
    def tracks(self, name):
        """Compare the shadow against a fresh read of its window. Returns the drift in full:
        which keys the record has and the box does not, which the box has and the record does
        not, and which disagree on the field that matters for this view."""
        window_name = SHADOW_VIEWS[name][0]
        window = self.windows.get(window_name)
        if window is None:
            return {"tracks": False, "reason": f"no {window_name} window attached to check against",
                    "window_at_version": None, "missing": [], "extra": [], "differing": []}
        ok, why = window.available()
        if not ok:
            return {"tracks": False, "reason": f"the {window_name} window is unavailable: {why}",
                    "window_at_version": window_at_version(window.name, window.version),
                    "missing": [], "extra": [], "differing": []}
        shadow_of, live_of = COMPARATORS[name]
        shadow = shadow_of(self.answer(name)["table"])
        live = live_of(window.live_state())
        missing = sorted(str(k) for k in set(live) - set(shadow))     # box has it, record does not
        extra = sorted(str(k) for k in set(shadow) - set(live))       # record has it, box does not
        differing = sorted(str(k) for k in set(shadow) & set(live) if shadow[k] != live[k])
        return {"tracks": not (missing or extra or differing),
                "reason": "shadow-diff empty" if not (missing or extra or differing) else "shadow-diff non-empty",
                "window_at_version": window_at_version(window.name, window.version),
                "missing": missing, "extra": extra, "differing": differing}

    # ---- coverage ------------------------------------------------------------------------
    def coverage(self, name):
        """Two halves, neither written by hand here: the DEFINITION's own boundary, derived
        by the engine from the definition alone, and the WINDOW's declared blind spots."""
        window_name = SHADOW_VIEWS[name][0]
        window = self.windows.get(window_name)
        structural = self.views.coverage_statement(name)
        window_coverage = window.coverage() if window is not None else {
            "facility": "(no window attached)", "sees": [],
            "does_not_see": ["this reader attached no window, so the window's blind spots "
                             "are unknown to it — which is itself stated, never assumed"]}
        return {
            "definition_boundary": structural,
            "window": window_coverage,
            "recorded_acts": list(classmap.RECORDED_ACTS[window_name]),
            "acts_seen_and_dropped": list(classmap.DROPPED_ACTS[window_name]),
            # The standing honest boundary, restated on every answer rather than filed once.
            "permanent_limit": ("interior userland activity — writes inside a program's own "
                                "shared memory, logic below the hook granularity — is "
                                "permanently out of audit reach, not an M1 gap"),
            "completeness": ("NOT CLAIMED. Whether these windows together see enough is the "
                             "owner's calibration with an evidence step (the coverage audit); "
                             "this view makes coverage measurable and never declares it "
                             "sufficient"),
        }

    def all_coverage(self):
        return {name: self.coverage(name) for name in SHADOW_VIEWS}


# =============================================================================================
# The retirement gate (design/36 §7 item 3 — the retirement ledger law, made MECHANICAL)
# =============================================================================================
# The ledger law, verbatim: "Per-subsystem shadow views retire only on proof. The shadow
# phase's Linux-authoritative view for a subsystem retires only after sustained shadow-diff ∅
# AND divergence-halt proven in both failure directions ... Never a naked swap."
#
# This gate is that law as a GUARD, not a note. It MINTS NOTHING: a retirement recorded as a
# governed act would be a `retire` op this unit does not have and does not create (design/28 §5,
# the founding-bump gate; EP-30-C5 §8). So the gate does not append to the record — it DECIDES
# whether a retirement is even lawful to attempt, and refuses the two ways a retirement is
# unlawful:
#   NAKED SWAP        — the maturation is not proven (either proof absent): the law's first bite.
#   SWAP INTO A VOID  — proven, yet no governed-authoritative view exists to retire INTO. A swap
#                       into a void is a naked swap by ANOTHER DOOR (EP-30-C5 §2), so it refuses
#                       by the same law.
# The PERMIT branch is the same law SATISFIED; it returns the retirement decision (naming the
# act and its citation) for a caller that holds a governed-authoritative target. It stops short
# of appending, because appending is the governed `retire` op that does not exist today.

#: What the retirement decision and its refusals cite — by NAME and board coordinate, the way
#: this estate cites law (never a bare line number). It is a DESIGN citation, not a recorded
#: founding rule: the only recorded divergence-halt rule, FS-LAW-DIVERGENCE-HALT, is the FILES
#: mount's ("the mount goes read-only"), and the connection subsystem serves nothing and so has
#: no mount to make read-only — minting a connection analogue would be the §8.4 founding bump
#: this unit refuses.
RETIREMENT_LAW = "design/36 §7 item 3 — retire only on proof, never a naked swap"


class NakedSwapRefused(Exception):
    """A retirement refused because the ledger law's precondition is unmet: either the
    maturation is not proven (a naked swap), or there is nowhere governed to retire into (a
    swap into a void — a naked swap by another door). Carries WHICH failure, so the caller
    learns why the law bit rather than only that it did."""

    def __init__(self, subsystem, reason, citation=RETIREMENT_LAW):
        self.subsystem = subsystem
        self.reason = reason
        self.citation = citation
        super().__init__(f"{subsystem}: retirement refused — {reason} (cites {citation})")


def retire_linux_authority(subsystem, maturation, target):
    """Gate the retirement of a subsystem's Linux-authoritative shadow view on its proof.

    `maturation` — the A2/A3 verdicts, each proven by command elsewhere, never asserted here:
        {"sustained_empty": bool,            # A2: shadow-diff ∅ sustained under a workload
         "halt_seeded_divergence": bool,     # A3(i): a seeded divergence halts current()
         "halt_no_false": bool}              # A3(ii): no false halt across the battery
    `target` — the governed-authoritative view to retire INTO, or None if none exists.

    Returns the retirement decision when the law is satisfied; raises NakedSwapRefused when it
    is not. It appends NOTHING: consummating a retirement as a recorded governed act is a
    governed `retire` op this unit does not mint (§8.4)."""
    proven = bool(maturation.get("sustained_empty")
                  and maturation.get("halt_seeded_divergence")
                  and maturation.get("halt_no_false"))
    if not proven:
        raise NakedSwapRefused(
            subsystem, "maturation not proven — sustained shadow-diff ∅ AND divergence-halt in "
            "both directions are the precondition, and at least one is not green")
    if target is None:
        raise NakedSwapRefused(
            subsystem, "no governed-authoritative view exists to retire into — a swap into a "
            "void is a naked swap by another door")
    return {"retired": subsystem, "into": target, "cites": RETIREMENT_LAW,
            "on_proof": dict(maturation)}
