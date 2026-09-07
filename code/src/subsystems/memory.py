# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS memory subsystem — the governed core (design/22, the acid test).

MEMORY IS THE ACID TEST because the hot path happens millions of times a second and must
record NOTHING. Governance counts governed DECISIONS (mappings, protections, evictions),
never machine ACTIVITY (faults, accesses). If "record every governed act" survives here it
survives everywhere (design/22 §1, §7).

THE MODEL (design/22 §2, §4). Space is a governed record: mmap/mprotect/evict/OOM/budget are
recorded, rule-citing DECISIONs (budget/policy is LAW), and every current structure — the
mapping table (VMAs), the resident set, free-lists — is a DERIVED VIEW folded from those
records. The load-bearing property: a minor page FAULT is a CACHE fill of an already-recorded
mapping and records NOTHING; a major fault's I/O completion is an INPUT (already recorded for
the device) and the fill it feeds is CACHE; accessed/dirty bits are ephemeral STREAM. So the
record rate tracks DECISIONS, not ACCESSES — the whole speed-tension resolution, at the
busiest path in the kernel.

RECONSTRUCTION (design/22 §4). memory-state = f(LAW, DECISIONS, INPUTS), STREAM never
load-bearing. Kill every page-derived structure and replay the mapping / eviction / IO
decisions — through a swap cycle — and the structure and content reconstruct identically
(accessed/dirty bits conservatively reset). Anonymous pages never written are zero by
definition WHILE THE PLATFORM ZEROES FREED FRAMES (a replay-determinism dependency, stated
not blind — order intake; design/22 §4); file-backed and swapped-out page contents come from
the file subsystem's content-addressed blobs (a cross-subsystem dependency, proven in the
swap-cycle test rather than assumed).

EVICTION (design/22 §5). Eviction is the DECISION that legitimately depends on the un-recorded
STREAM (which page is coldest). It samples the stream but FREEZES the evidence it acted on into
the decision (the aggregate, cited), so replay reconstructs the eviction from that decision
ALONE — one record per eviction, never one per access. No raw-access journal exists.

No drivers. The op definitions (AMEND-BUDGET / MEM-GRANT / MEM-PROTECT / MEM-EVICT) and their
law-name constants were RETIRED here in EP-14B: their one authoritative home is the founding
pack, founding/founding-pack.json (the generic interpreter re-registers them from the record
at boot). The budget ceiling check lives in kernel/opdefs.py. This module keeps only the
derived views. Absence of a module op-dict is guarded by tests/test_ep14b.py.
"""

# ONE VOCABULARY FOR THE FIVE CLASSES. Imported (read-only) from the observation classmap so
# memory and the observation seam name the classes with the same strings — design/03 §2's five
# classes, applied to memory by design/22 §2. Importing is not modifying; observe/ is not touched.
from observe.classmap import DECISION, LAW, INPUT, CACHE, STREAM

# THE FAMILY-KEYED PROJECTION (EP-33B Finding 2; design/36 ADDENDUM S, K12). The memory derived
# views fold their answer from the MEMORY family of records; reading the whole record to compute
# a family-scoped answer costs records the answer does not depend on, which K12 forbids ("a
# derived answer costs its own dependencies ... not the whole stream"). The fix is the EXISTING
# mechanism, not a new one: kernel.store.RecordProjection — the same seq-only projection the
# authority folds and the three per-act-path folds (EP-24C) already read through. It holds WHERE
# THE INPUTS ARE, never WHAT THE ANSWER WAS, is rebuilt from the record on load, and REFUSES
# (StaleIndex) if it cannot prove itself current. Kill it, replay, the world is identical.
from kernel.store import RecordProjection

# design/22 §2 — EVERY MEMORY EVENT, CLASSIFIED (the whole subsystem, no gaps). Keys are the
# design's own event names; the value is the class; RECORDED says whether the event appends. The
# op that REALISES a recorded event is named in REALISED_BY. Events with no op — the minor fault,
# the accessed/dirty bit, the raw load/store — are machine activity that records NOTHING, which is
# the acid test's whole point, not an omission.
EVENT_CLASS = {
    "mmap":                    DECISION,   # create a mapping — a region granted against a budget
    "mprotect":                DECISION,   # change a region's rights
    "munmap":                  DECISION,   # a grant revoked
    "budget-amendment":        LAW,        # a rule of rules (cgroup limit, NUMA policy)
    "first-touch-fault":       DECISION,   # a lazily-granted region materialised, once per region
    "eviction":                DECISION,   # reclaim under pressure — embeds the evidence it acted on
    "oom-kill":                DECISION,   # the governed, cited choice replacing the silent reaper
    "minor-fault":             CACHE,      # page present in a RECORDED mapping — applies it, records NOTHING
    "major-fault-completion":  INPUT,      # the I/O completion (already a device INPUT); its fill is CACHE
    "accessed-dirty-bit":      STREAM,     # ephemeral hardware telemetry; surfaces only as cited evidence
    "load-store":              STREAM,     # raw operation flow; sampled in aggregate only
}
RECORDED = {ev: cls in (DECISION, LAW) for ev, cls in EVENT_CLASS.items()}

# Which built op realises each RECORDED memory event. `first-touch-fault` and `oom-kill` are
# design/22 §2 classes whose ops are FORECAST (not minted this build); named here as forecast so
# the table is complete without a reader inferring an op the founding does not contain.
REALISED_BY = {
    "mmap": "MEM-GRANT", "mprotect": "MEM-PROTECT", "munmap": "MEM-EVICT",
    "budget-amendment": "AMEND-BUDGET", "eviction": "MEM-EVICT",
    "first-touch-fault": "(forecast)", "oom-kill": "(forecast)",
}


def classify(event):
    """The design/22 §2 class of a memory event, by the design's own event name. KeyError on an
    unnamed event — the table is exhaustive by §2, and a silent default would be a class nobody
    declared."""
    return EVENT_CLASS[event]


# THE MEMORY FAMILY — exactly the recorded mapping DECISIONs the family-scoped folds below fold
# (`mappings` reads grant/protect/evict; `resident_size` and `fault` fold through it; `evictions`
# reads evict). It is the answer's dependency set and nothing wider: padding it with records these
# folds never read (a budget amendment, a fault input) would make the fold's cost grow with
# something its answer does not depend on, which is the very thing K12 forbids.
MEMORY_ACTIONS = ("MEM-GRANT", "MEM-PROTECT", "MEM-EVICT")


def is_memory_record(e):
    """Does this record belong to the memory-family subset the derived views fold?"""
    return e["action"] in MEMORY_ACTIONS


class MemoryProjection(RecordProjection):
    """The memory-family subset the derived views read through, so `mappings()` /
    `resident_size()` cost their own family's records rather than the whole stream (K12;
    design/36 ADDENDUM S). A subclass supplies THREE things and nothing else (EP-24C): the name
    it refuses under, the by_action keys it answers (NONE — the folds only iterate `all()`), and
    the predicate. Everything else — currency, resolution, coherent-or-refuse — is the one shared
    RecordProjection implementation."""

    _NAME = "memory projection"
    _selects = staticmethod(is_memory_record)


class MemoryView:
    """The derived views over the record. Holds NO answer of its own: every method folds the
    record on the call, so 'kill the page-derived state and rebuild' is just a fresh MemoryView
    over a store replaying the same record (design/22 §4's reconstruction, realised). The
    family-keyed projection it holds is derived too — it stores locations, never answers, and
    killing it changes nothing a replay would not."""

    def __init__(self, store):
        self.store = store
        # The family-keyed projection is HELD (built once per view, incrementally caught up on
        # each read), so a view kept live — the production case (kernel/compose.py) — pays the
        # subset's cost per read, not the record's length. It holds only locations; every answer
        # is still folded from the record at read time.
        self._records = MemoryProjection(store)

    def mappings(self, holder=None, as_of=None):
        """The mapping table / VMAs = fold of MEM-GRANT / MEM-PROTECT / MEM-EVICT DECISIONS. A
        re-grant OVERWRITES its region; an eviction removes it. Pure function of recorded data."""
        m = {}
        for e in self._records.all(as_of):
            a, p = e["action"], (e.get("payload") or {})
            if a == "MEM-GRANT" and (holder is None or p.get("holder") == holder):
                m[p["region"]] = {"holder": p.get("holder"), "size": p.get("size"), "prot": p.get("prot")}
            elif a == "MEM-PROTECT" and p.get("region") in m:
                m[p["region"]]["prot"] = p["prot"]
            elif a == "MEM-EVICT":
                m.pop(p.get("region"), None)
        return m

    def resident_size(self, holder, as_of=None):
        """The holder's resident total = sum of its mapped regions' sizes. NOT stored — re-derived
        here on every call, which is why the budget ceiling's summed comparand carries its
        population (these mappings) and basis (their sizes) by construction (§A51; MEM-LAW-BUDGET)."""
        return sum(v["size"] for v in self.mappings(holder, as_of).values())

    def fault(self, region, as_of=None):
        """THE HOT PATH (design/22 §3) — THE A3 FRAME. A minor fault resolves against the derived
        mapping cache and RECORDS NOTHING: it applies an already-recorded grant. Pure S — a
        deterministic function of (recorded mapping decisions) + (the fault address); no append, no
        model call, no judgment. This is the code whose records-per-fault the MAX/guest dispatch
        measures under a real fault storm; its structural shape is records-per-fault = |decisions| /
        |faults|, which FALLS toward the governance floor as the fault rate rises with decisions
        fixed. A fault on no granted region is a governed refusal (SIGSEGV) — the only branch that
        would touch the log — and is NOT this cache-fill path."""
        return region in self.mappings(as_of=as_of)

    def evictions(self, as_of=None):
        """The eviction DECISIONS, each carrying the evidence_summary it FROZE at the decision
        (design/22 §5). Replay reconstructs each eviction from its own record alone — there is no
        raw-access journal to consult, because the raw accesses were STREAM and were never
        recorded. Returns [(region, evidence_summary), ...] in record order."""
        out = []
        for e in self._records.all(as_of):
            if e["action"] == "MEM-EVICT":
                p = e.get("payload") or {}
                out.append((p.get("region"), e.get("evidence_summary")))
        return out
