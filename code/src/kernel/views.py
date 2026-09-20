# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — views (L2): all current state computed by replay.

Ported from pwc-app/src/domain/views.js. Every "current X" is a fold over the record
(design 02 §1.3; P2 "everything current is computed"). Nothing here persists state.

Head-only memo keyed on an append generation: caching the head is safe because the
log is append-only, so a view computed at log-length N is stable. Delete the memo and
replay yields identical results (round-trip law). asOf queries are never cached.
"""

import hashlib
import json
from collections.abc import Mapping

from . import authority
from . import keys as keys_mod
from .canonical import canonical_hash, strip_derivation
from .errors import OpError
from .store import PROJECTIONS, frozen_default

# Closed trigger vocabulary for view definitions (design/27 §4; adopted-definitives, B09):
# the dimensions a view's "when" may test. A dimension outside this set is refused at
# creation — an unknown filter does not exist (the closure discipline on view triggers).
VIEW_FILTER_DIMENSIONS = ("action", "actor", "object", "rule_cited", "refused", "payload_kind")

# C6a VT-3 (design/25 v2 ruling "the third view form"; design/53 L16; board :3817/:3825): the closed
# grow-only vocabulary a DERIVED view row may narrow its parent by. A derived view row is
# `derive = {from: <parent view>, where: {<dimension>: <value>}}` — design/28's system view given a
# row form; it names its parent view and exactly ONE closed dimension. A dimension outside this set is
# refused at CREATE-VIEW (boot.create_view's inline door, mirroring the bind/trigger closure
# discipline) — an unknown derived dimension does not exist. GROW-ONLY, like FOLD_NAMES: adding a
# dimension is a deliberate edit here; a removal is a RAISE (a shrink reds the pinned five-name
# baseline). The values a dimension may take live with the design's derived_dimensions, not here; the
# door closes the DIMENSION, the serving (VT-3b) closes the narrowing.
DERIVE_DIMENSIONS = ("actor_class", "scope_class", "item_kind", "liveness", "tree_kind")

# The S-plane FOLD LIBRARY (design 28 §6, §I4; EP-08): the named engine folds a MASTER view
# definition may BIND to. A master is a RECORD that names a fold; the fold FUNCTIONS stay code
# (mechanism, zero governance value — the S-plane). This closes the loop of §I4: masters are
# derived AND defined-as-records. A definition naming a fold outside this set is refused at
# creation (CREATE-VIEW) — the closure discipline on binds, mirroring the trigger vocabulary.
FOLD_NAMES = ("active_rules", "actors", "resources", "permissions", "relationships",
              "op_definitions", "view_definitions",
              # C6a VT-1 (design/25 v2.1 ruling 19; design/53 B3/B4/I4): the level-2 OLD bands — the
              # latest-wins COMPLEMENTS of the three derived masters (rules 2.2, items 3.2,
              # relationships 4.2), each a SEPARATE bindable master beside the seven above. ONLY
              # these three join the library: events do not split active/old and the events master
              # is not bindable (I1, ruling 11), and the level-4 filters compute in memory (ruling
              # 10) — neither is an S-plane bindable master. The fold_set() pin moves ONCE, grow-only.
              "old_rules", "old_items", "old_relationships",
              # C6a VT-3 (design/25 v2 seed_form oracle; design/53 L14 "the promotion happens in the
              # unit that binds", ruling :3781): the six folds the base-view-tree seed's 12 bind rows
              # name that were not yet library members. Promotion = fold-set MEMBERSHIP so the seed's
              # binds are admitted at create_view (a bind outside FOLD_NAMES stays refused AR-2); the
              # SERVING of a bound master — its master read — is VT-3b (design/53 L16). Each is a
              # SEPARATE memoised projection, never a key on an existing one (I7): rule_changing_acts /
              # acts_under_rules are VT-1's events-split KEYS today and get their own projection when
              # served (VT-3b), never reshaping events_by_effect; static_composite is already its own.
              # The fold_set pin moves ONCE, grow-only: baseline 10 -> 16 (test_ep50:207-209).
              "rule_changing_acts", "acts_under_rules", "rules", "items", "active_items",
              "static_composite")


def fold_set():
    """THE ATTESTED FOLD LIBRARY (design/51 N6, EP-50) — the EP-40 attested-set TWIN
    (attestation.attested_set) over FOLD_NAMES. The set a MASTER may bind is a DECLARED, grow-only
    member set with a citable `set_digest`: a bind to a fold OUTSIDE it is refused at CREATE-VIEW as
    today (boot.create_view), and the set itself is now a fact any reader can recompute from the
    declared names — a record may cite it. A SEPARATE attested set from the file-attestation members
    (ATTESTED_MEMBERS): folds are CODE FUNCTIONS, not file artifacts, so this set carries no
    per-member byte digest — only the digest over the sorted names, through the estate's ONE
    canonical hash (so name order and platform variance cannot move it). Grow-only: adding a fold is
    a deliberate edit to FOLD_NAMES; a removal is a RAISE (a shrink reds the pinned baseline)."""
    members = tuple(sorted(FOLD_NAMES))
    return {"kind": "fold_set", "members": members, "set_digest": canonical_hash(members)}


def _matches(e, when):
    """Does one record match a view's trigger? Each entry tests one dimension; a value of
    {"not": X} is the minus-inside-a-trigger: the record matches only if the dimension is
    NOT X (absence as a condition — owner ruling 2026-07-15)."""
    for dim, want in (when or {}).items():
        got = (e.get("payload") or {}).get("kind") if dim == "payload_kind" else e.get(dim)
        # `want` may be a frozen mapping (deep-freeze, EP-02) — Mapping catches both a plain
        # dict and a MappingProxyType, where isinstance(_, dict) would miss the frozen one.
        if isinstance(want, Mapping) and "not" in want:
            if got == want["not"]:
                return False
        elif got != want:
            return False
    return True


def _scope_class(scope):
    """The actor CLASS a rule's scope names, or `all` when it names none (C6a VT-3b; design/25 v2
    nodes 2.1.x / 2.2.x: "scope names class S / S+U / U" vs "scope names no class — the root and the
    constitution"). A scope follows the estate's existing `kind:value` grammar (space:root); a
    `class:<c>` scope names class c; every other scope — a space scope, the root, or none — narrows
    to `all`. Reads the EXISTING `scope` field only; no new field (STOP a/b hold)."""
    if isinstance(scope, str) and scope.startswith("class:"):
        return scope.split(":", 1)[1]
    return "all"


def digest_of(e, algo="json"):
    """Content digest of a record (dual-audit cross-check; design guards.digestOf), ERA-SPLIT at
    EP-35's boundary (re-home rows 1 & 2; D4) — the family's second copy, kept in lockstep with
    protection._digest. `algo="canonical"` serializes through the ONE canonical floor and unifies
    the None/absent-payload boundary (payload -> {}), so the two copies agree everywhere for new
    records (the drift pin's shared corpus AND the None case, row 2). `algo="json"` (default) is
    kept BYTE-IDENTICAL to the pre-EP-35 function — its historical None-payload behaviour included —
    so digests written before the seal verify under exactly what wrote them (the past byte-untouched)."""
    if algo == "canonical":
        body = {"seq": e["seq"], "actor": e["actor"], "action": e["action"],
                "payload": dict(e.get("payload") or {})}
        return canonical_hash(body).split(":", 1)[1][:16]
    body = {"seq": e["seq"], "actor": e["actor"], "action": e["action"], "payload": e.get("payload")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=frozen_default).encode("utf-8")).hexdigest()[:16]


class Views:
    """THE MEMO, AND WHAT EP-28B W3 CHANGED ABOUT IT.

    Every "current X" here is a fold over the record, head-memoised on an append generation.
    Until 2026-07-30 there was ONE generation and every append moved it, so a `FILE-OPEN` —
    a custody record that cannot change one word of law — invalidated `active_rules` and the
    gate's per-act path re-derived law it had just derived. The guest measured the per-act folds
    at 13–23% of a gated act with that recompute inside it.

    THE DISTINCTION IS THE FINDING AND IT IS CARRIED VERBATIM: the subset being right and the
    invalidation being wrong are DIFFERENT THINGS. `design/36` ADDENDUM C's law was that a fold
    on the per-act path must not grow with record count, and the trigger written for it tested
    subset-READING only. Invalidation on unrelated traffic reintroduced the growth by a route
    the trigger never looked at — charter §A26's own class, a trigger written one notch narrower
    than the law it cites. So this is that law raised to its own altitude, not a new rule.

    WHAT MAKES IT LAWFUL RATHER THAN A GUESS. A fold with a DECLARED record subset already owns
    a recognition rule — the predicate its projection selects on — and that predicate is the
    only thing the answer can depend on. So the memo for such a fold is invalidated by exactly
    the records that enter its subset, consulted through the SAME predicate the projection uses.
    NO SECOND RECOGNITION RULE IS WRITTEN: that is EP-24B's one-implementation law applied one
    layer up, and it is why a divergence here could only ever be attributed to the subset and
    never to a second opinion about what a law record is.

    AND THE UNDECLARED MEMOS KEEP TODAY'S BEHAVIOUR, on purpose. `founding_prefix`, `accounts`
    and `chain_end` declare no subset, so they stay on the global append generation and are
    invalidated by every append exactly as before. Silence means "everything invalidates me",
    which is the closed direction: a fold nobody has analysed is never quietly exempted."""

    def __init__(self, store):
        self.store = store
        self._memo = {}
        self._memo_gen = 0          # the append generation: EVERY append moves it (undeclared memos)
        self._subset_gens = {}      # per-fold generation for the folds with a declared subset
        # C6a VT-6a: THE CLIMB'S IN-MEMORY PENDING-STAMP BUFFER (design/25 v2.4 ruling 13 — the
        # finalised time is a change in the view's own pipeline, NEVER a record row). The stamp
        # step (gate._stage_stamps) records an act's staged stamps here, keyed by the act's
        # content-hash echo; the sixth on-append listener (_retire_pending_stamp) retires the
        # matching copy when the act's row appends. Pipeline state ONLY: NEVER read as a truth by
        # any view/check/reply (archi :3885), and a restart empties it (the durable stamps remain
        # in the appended rows — no silent loss).
        self._pending_stamps = {}
        # The listener resolves `self._bump` AT CALL TIME, deliberately. Registering the bound
        # method directly would be equivalent in behaviour and would silently disable
        # `tests/test_ep24c.py`'s control, which neuters `_bump` to prove that a memo outliving
        # its head really does serve a stale answer. A guard that can no longer fail is worse
        # than the tidier line is better.
        store.on_append(lambda e: self._bump(e))
        # C6a VT-6a: THE SIXTH on-append listener (beside `_bump`) — the record's echo retiring the
        # view's pending stamp copy (ruling 13). It never mutates the record and never appends (the
        # gate is the sole pen, ruling 14/17); a retire failure must not take the append down.
        store.on_append(self._retire_pending_stamp)

    def _bump(self, e=None):
        """The store's on-append listener. `e` is the committed record, which is what makes the
        distinction possible: the question "could this record change this fold's answer" is
        answerable from the record, and it is answered by the fold's own predicate.

        NO RECORD, EVERYTHING MOVES. `e` is optional so a caller with nothing to judge (a test
        forcing an invalidation, a future path that bumps without a record in hand) gets the old
        behaviour — every memo invalidated. The default errs toward recomputing, never toward
        serving."""
        self._memo_gen += 1
        for fold, projection in self.PER_ACT_FOLDS.items():
            if e is None or PROJECTIONS[projection]._selects(e):
                self._subset_gens[fold] = self._subset_gens.get(fold, 0) + 1

    def _generation_of(self, name):
        """Which generation this memo is keyed on. A fold with a declared subset is keyed on its
        OWN generation; everything else is keyed on the append generation."""
        if name in self.PER_ACT_FOLDS:
            return self._subset_gens.get(name, 0)
        return self._memo_gen

    # ---- C6a VT-6a: THE CLIMB'S RELEVANCE, THE STAMP SHAPE, THE PENDING BUFFER + ITS ECHO ----
    # design/25 v2.4 rulings 12/13/15 (the stamp each master view puts on the act as it climbs — its
    # identity, the hash of what it saw, the version it saw it at; the echo retiring the pending copy;
    # detection never legitimacy); design/53 B10; the pipeline core VT-6a (board :3888). The gate's
    # stamp step (gate._stage_stamps) reads `relevant_folds`/`build_stamps` and records the pending
    # copy via `record_pending_stamps`; the sixth on-append listener `_retire_pending_stamp` retires
    # it by the content-hash echo. VT-6c reuses `relevant_folds` to know which master is relevant to
    # a row. The buffer is NEVER read as a truth by anything — a stamp exists only in a row (:3885).

    def relevant_folds(self, draft):
        """The per-act-path master views a record TOUCHES (ruling 15, "the master views its reach
        touches") — computed PER FOLD from the record itself, the SAME per-fold selection `_bump`
        uses to invalidate memos (`PROJECTIONS[projection]._selects`). A fold appears AT MOST ONCE
        (the iteration is keyed on PER_ACT_FOLDS), so a fold carrying two master definitions counts
        once, never twice; NO declared op-def field is read (VT-6b collapsed, archi :3800/:3846)."""
        return [fold for fold, projection in self.PER_ACT_FOLDS.items()
                if PROJECTIONS[projection]._selects(draft)]

    def _stamp_of_fold(self, fold):
        """One master's stamp (ruling 13): the VIEW identity (the fold it stamps for), the HASH of
        what it saw (the fold's own content at the head, through the estate's one canonical hash),
        and the VERSION = the seq the master was folded at (the current head — a record seq, so a
        positive int, the shape VT-6d's `_well_formed_stamp` requires)."""
        return {"view": fold,
                "hash": canonical_hash(self.view_fold(fold)),
                "version": len(self.store.events)}

    def build_stamps(self, draft):
        """The relevant masters' stamps for an act as it climbs — ONE per RELEVANT fold (per fold,
        never per master name). Empty when the act touches no master's reach (ruling 15 then has
        nothing to stamp, and a stamped class still lacking a required stamp is refused by VT-6d)."""
        return [self._stamp_of_fold(fold) for fold in self.relevant_folds(draft)]

    def _act_content_hash(self, rec):
        """The act's content-hash ECHO — over the CALLER-CONTROLLED content ONLY (action / object /
        target / payload, payload normalised `or {}` to match the store's own normalisation), so the
        hash the stamp step computes over the DRAFT equals the one this listener recomputes over the
        COMMITTED record: the round-trip identity (design/38 §1). The gate-added fields (provenance
        and its stamps, seq, prev_hash, recording_time) are EXCLUDED — exactly as they are from what
        the invoker signs — so a mutated or partial append never silently satisfies a pending copy."""
        return canonical_hash({"action": rec.get("action"), "object": rec.get("object"),
                               "target": rec.get("target"), "payload": rec.get("payload") or {}})

    def record_pending_stamps(self, draft, stamps):
        """Hold an act's staged stamps as the in-flight PENDING copy, keyed by the content-hash echo.
        Pipeline state ONLY (ruling 13), retired by `_retire_pending_stamp` when the act's row
        appends; a restart empties it and the durable stamps remain in the appended rows (no silent
        loss). Keyed to a LIST so two identical in-flight acts each retire on their own echo. NEVER
        read as a truth by any view/check/reply (archi :3885)."""
        self._pending_stamps.setdefault(self._act_content_hash(draft), []).append(stamps)

    def _retire_pending_stamp(self, record):
        """THE SIXTH on-append listener (beside `_bump`): when an act's row appends, retire the
        matching pending copy by the content-hash echo (ruling 13's finalised time — a change in the
        view's own pipeline, never a record row). The listener NEVER mutates the record and NEVER
        appends (the gate is the sole pen, ruling 14/17); a retire failure must not take the primary
        append path down (store.py:809 — the mirror discipline)."""
        try:
            h = self._act_content_hash(record)
            entries = self._pending_stamps.get(h)
            if entries:
                entries.pop()
                if not entries:
                    del self._pending_stamps[h]
        except Exception:
            pass

    def cached(self, name, as_of, fn):
        """Head-only memo. asOf bypasses the cache (a historical view is never head).

        ONE LIVE ENTRY PER FOLD. A superseded key is dropped when its replacement is stored, so
        the memo is bounded by the number of memoised folds rather than by traffic. The old
        bound was a 64-entry clear-everything cap, which worked when every key moved together;
        with per-subset generations it would have thrown away the very memos this change exists
        to keep, roughly every sixty appends, and the fix would have looked like it was working
        while delivering a fraction of what it claims. The KEY SHAPE `<fold>:<generation>` is
        kept deliberately: `tests/test_ep24b.py` guards that no authority fold's answer is ever
        memoised by reading these keys, and a bare-name key would have made that guard silently
        stop matching."""
        if as_of is not None:
            return fn()
        key = f"{name}:{self._generation_of(name)}"
        if key in self._memo:
            return self._memo[key]
        v = fn()
        for stale in [k for k in self._memo if k.startswith(name + ":")]:
            del self._memo[stale]
        self._memo[key] = v
        return v

    # ---- the generic fold: reduce the record (up to asOf) into a state dict ----
    def fold(self, reducer, initial=None, as_of=None):
        state = dict(initial) if initial else {}
        for e in self.store.all(as_of):
            reducer(state, e)
        return state

    # ---- the per-act-path folds (EP-24C; design/36 ADDENDUM C) --------------------------
    # THE RULE ADDENDUM C ADDS TO K3: a fold serving the gate's per-act path reads a
    # governance SUBSET, never the whole record, and a structural guard fails when a new
    # whole-record fold lands on that path. The guard is `tests/test_ep24c.py`; this is the
    # surface it declares against.
    #
    # ONE IMPLEMENTATION, TWO RECORD SOURCES — exactly the shape EP-24B proved for the
    # authority family and the mentor filed as standing law. Each fold below has ONE body;
    # `view_fold` hands it either its projection or the whole store, and NOTHING ELSE
    # differs. A fast implementation written beside a slow one would make every divergence
    # ambiguous between the subset and the logic, and no test could attribute its own finding.
    PER_ACT_FOLDS = {"op_definitions": "op_definitions",
                     "active_rules": "law",
                     "category_packs": "category_packs"}

    def view_fold(self, name, accelerated=True, as_of=None):
        """Run one named per-act-path fold against either its projection (accelerated) or the
        whole record (the retained unaccelerated oracle, the standing differential baseline)."""
        if name not in self.PER_ACT_FOLDS:
            raise ValueError(f"{name!r} is not a per-act-path fold — the family is: "
                             + ", ".join(sorted(self.PER_ACT_FOLDS)))
        source = self.store.record_projection(self.PER_ACT_FOLDS[name]) if accelerated else self.store
        return getattr(self, "_" + name)(as_of, source)

    # ---- law as data (every subsystem reads its LAW through this) ----
    def active_rules(self, as_of=None):
        return self.cached("active_rules", as_of,
                           lambda: self.view_fold("active_rules", as_of=as_of))

    def _active_rules(self, as_of=None, source=None):
        # A record IS a LAW record iff its payload declares a `rule_id` — recognition by
        # self-declaration, not by a hard-coded action-name list. So any subsystem's LAW
        # op (e.g. a memory budget amendment) is seen without coupling views to its verb.
        rules = {}
        for e in (source or self.store).all(as_of):
            p = e.get("payload") or {}
            rid = p.get("rule_id")
            if rid is not None:
                # Tier-aware latest-wins (defense in depth): a constitutional entry is
                # superseded ONLY by another constitutional-tier write. A lower-tier record
                # carrying the same rule_id — a forged one that reached the store — cannot
                # silently overwrite the constitution in the derivation. The write itself is
                # already refused at the gate's constitution guard; this makes the
                # operative constitution unshakeable even if a future write path slips past.
                if rules.get(rid, {}).get("tier") == "constitutional" and p.get("tier") != "constitutional":
                    continue
                rules[rid] = {**p, "seq": e["seq"]}
        return rules

    def policy_value(self, key, as_of=None):
        """Latest-effective-wins policy read (law is data; design views.policyValue)."""
        rules = self.active_rules(as_of)
        for rid in sorted(rules, key=lambda r: rules[r]["seq"], reverse=True):
            if rules[rid].get("policy_key") == key:
                return rules[rid].get("value")
        return None

    def category_packs(self, as_of=None):
        """Every changeable vocabulary, latest definition per name (re-seeding a pack is an
        amendment; latest wins). A category_pack is a named CREATE-INFO carrying `levels` —
        actor-classes, geometry, the dual-audit action list, the syscall map (design 28 §3).
        The one read path consumers use, so no subsystem scans the raw store for policy."""
        return self.cached("category_packs", as_of,
                           lambda: self.view_fold("category_packs", as_of=as_of))

    def _category_packs(self, as_of=None, source=None):
        # Fold over ALL records by payload KIND, not just CREATE-INFO: a pack is recognised by
        # what it IS (payload.kind == category_pack), so the genesis seeds (CREATE-INFO) AND
        # governed amendments (AMEND-PACK, A5) both count, latest-wins by sequence.
        # A pack with no `levels` LIST is malformed and does not enter the vocabulary (the
        # closure discipline, applied to data). This keeps a bad record — an operator footgun,
        # or a future bad amendment — from reaching consumers who would iterate or hash it; a
        # consumer inside the on-append audit path must never be handed junk.
        packs = {}
        for e in (source or self.store).all(as_of):
            p = e.get("payload") or {}
            if p.get("kind") == "category_pack" and p.get("name") \
                    and isinstance(p.get("levels"), (list, tuple)):
                packs[p["name"]] = {"name": p["name"], "levels": p["levels"], "seq": e["seq"]}
        return packs

    def visible_category_packs(self, viewer, as_of=None):
        """PACK-SCOPE READ half (design/31 J6; EP-17) — the FIRST sight-filtered read surface, P6
        (sight is law) extended from action to KNOWLEDGE. A per-account view of the vocabularies:
        the packs `viewer` may READ, default-deny. owner/SYSTEM see all (can_read exempts the root);
        any other account sees a pack only with a covering GRANT-READ of its object (`pack:<name>`,
        or a `*` target). The kernel's OWN machinery keeps reading the UNFILTERED category_packs()
        (it acts as the kernel, not as an account) — this is an ADDITIONAL surface for an account
        asking 'what vocabularies can I see', never a replacement. The AUDIT FLOOR stays constitutional
        and SCOPE-INDEPENDENT: what an actor can READ never changes what the floor ENFORCES (the gate's
        audit-floor branch fires on any AMEND-PACK that would lower it, whether or not the actor could
        read the pack). Under the founding, no ordinary account holds a GRANT-READ, so it sees no packs
        until sight is granted — default-deny made visible."""
        from .protection import can_read
        root = self.chain_end(as_of)
        return {name: p for name, p in self.category_packs(as_of).items()
                if can_read(self.store, viewer, f"pack:{name}", root)}

    def root_rules(self, as_of=None):
        """The recorded constitution (design/27): root rules in full trigger->outcome form
        (EP-06, design 28 §4), derived from the record — the boot law readable back as a view.
        `text` is the human sentence; `when`/`then` the executable form; `enforced_by` the
        law->machinery map; `enforcement` live|deferred."""
        out = []
        for e in self.store.by_action("CREATE-RULE", as_of):
            p = e.get("payload") or {}
            if p.get("root"):
                out.append({"rule_id": p.get("rule_id"), "polarity": p.get("polarity"),
                            "text": p.get("text"), "tier": p.get("tier", "ordinary"),
                            "enforcement": p.get("enforcement"),
                            "when": p.get("when") or [], "then": p.get("then") or [],
                            "enforced_by": p.get("enforced_by"), "seq": e["seq"]})
        return out

    def toothless_musts(self, as_of=None):
        """Laws claiming force (polarity + or -) whose OUTCOME is empty — teeth-less musts
        (design 28 §8). A law with a non-empty `then` has teeth; an empty `then` is a claim with no
        consequence. A DEFERRED law (enforcement == 'deferred') is EXEMPT — honest, not toothless:
        its machinery is named-not-built (law precedes machinery). Predicate: polarity in {+,-} AND
        then empty AND not deferred.

        WIDENED (EP-07) from root laws to ALL active law records, now that runtime full-form laws
        exist (obligations; CREATE-RULE-minted structural laws). Two kinds are excluded to avoid
        false positives: op_definition and view_definition carry polarity '+' but are DEFINITIONS,
        not outcome-laws (they have no `then`); policy/registration rules carry no polarity and are
        skipped by the polarity test. (The plan's note that view definitions 'carry no polarity' is
        imprecise — they carry '+', so they are excluded by kind here — logged as a plan/code nuance.)"""
        out = []
        for r in self.active_rules(as_of).values():
            if r.get("kind") in ("op_definition", "view_definition"):
                continue
            if r.get("polarity") in ("+", "-") and not r.get("then") and r.get("enforcement") != "deferred":
                out.append(r.get("rule_id"))
        return out

    def wait_wake(self, as_of=None):
        """Who is blocked on which condition (tree 1.2.2): BLOCK-ON events folded MINUS the arrivals
        that wake them. An actor blocked by BLOCK-ON(on=C) is woken once a later record with action C
        is recorded. Returns {actor: [conditions still blocking]} — a fold, nothing stored."""
        blocked = {}
        all_records = self.store.all(as_of)
        for e in self.store.by_action("BLOCK-ON", as_of):
            cond = (e.get("payload") or {}).get("on")
            woken = any(a["action"] == cond and a["seq"] > e["seq"] for a in all_records)
            if not woken:
                blocked.setdefault(e["actor"], []).append(cond)
        return blocked

    def wake(self, arrival, as_of=None):
        """The live check wake(arrival) (25-view-tree.json): match ONE arrival against the blocked
        set and return the actors it wakes — those still blocked on the arrival's action. `arrival`
        is a record (or a bare action string)."""
        action = arrival["action"] if isinstance(arrival, Mapping) else arrival
        return [actor for actor, conds in self.wait_wake(as_of).items() if action in conds]

    # ---- Views as data records (design/27 §4; owner rulings 2026-07-15) ----------------
    # A view IS a standing rule in full trigger->outcome form: "when a record matches
    # <when>, move it to <then.move_to>". It enters as a named info item carrying a
    # rule_id, so the law view sees it (view definitions are REQ-form records) and it is
    # reusable by name like any dictionary item. One engine executes all definitions;
    # no arrangement is hardcoded. Query, standing view, and broadcast are ONE primitive
    # (match -> move); v1 executes on request, records nothing per run (doc 17 — the
    # standing push/worker tree is the later depth stage).

    def view_definitions(self, as_of=None):
        """Every named view, latest definition per name (re-defining = a new event). A view is one of
        THREE forms: a FILTER view (`when`->`then.move_to`, DICT trigger); a MASTER (`bind` names an
        S-plane fold, EP-08); or a DERIVED view row (`derive = {from, where}` — a parent view narrowed
        by one closed dimension, C6a VT-3, design/25 v2). `tier` and `refresh` (a refresh mandate,
        design 28 §6) ride along where present.

        THIS PROJECTION'S SHAPE IS PINNED (campaign-1, test_ep16's differential oracle) and stays
        BYTE-IDENTICAL through VT-3: it does NOT carry the derive form. By I7 (design/53) a new form
        is read through a SEPARATE memoised projection, NEVER a shape change to a pinned one — so the
        derive form (the VT-3 round-trip, A3) reads back through `view_derivations` below, not here.
        The SERVING of a derived row — narrowing the parent's output — is VT-3b."""
        defs = {}
        for e in self.store.by_action("CREATE-VIEW", as_of):
            p = e.get("payload") or {}
            if p.get("kind") == "view_definition" and p.get("name"):
                name = p["name"]
                tier = p.get("tier", "ordinary")
                # TIER CONSERVATION for master views (EP-08B B2; mirrors active_rules, defense in depth):
                # a protected master's tier is CARRIED ACROSS its amendment even though create_view mints
                # no tier — an authorized re-definition INHERITS the protected tier. A lower/absent-tier
                # write cannot silently demote the master in the DERIVATION (the gate already refused any
                # unauthorized supersession; this keeps the operative registry honest even if one slipped).
                prev = defs.get(name)
                if prev and prev["tier"] in ("owner", "constitutional") and tier == "ordinary":
                    tier = prev["tier"]
                defs[name] = {"name": name, "when": p.get("when") or {}, "then": p.get("then") or {},
                              "text": p.get("text"), "bind": p.get("bind"), "tier": tier,
                              "refresh": p.get("refresh"), "seq": e["seq"]}
        return defs

    def view_derivations(self, as_of=None):
        """THE THIRD FORM read back, as its OWN projection (C6a VT-3, A3 round-trip; design/25 v2).
        {view name -> {from, where}} for every view definition carrying a `derive`, latest per name.

        A SEPARATE projection by I7 (design/53): the derive form does NOT ride on view_definitions,
        whose shape is a pinned campaign-1 answer (test_ep16's differential oracle) — a new form is a
        new separate projection, never a shape change to a pinned one. Reading the seed's 23 derived
        rows back HERE proves the round-trip without touching that pinned shape. This only READS the
        recorded form; the SERVING — narrowing the parent view's output by the one dimension — is
        VT-3b (execute_view is untouched). A view: kill it, replay the record, identical (P2)."""
        out = {}
        for e in self.store.by_action("CREATE-VIEW", as_of):
            p = e.get("payload") or {}
            if p.get("kind") == "view_definition" and p.get("name") and p.get("derive") is not None:
                out[p["name"]] = p["derive"]
        return out

    def execute_view(self, name, as_of=None):
        """Run one view. A FILTER view filters the record per its trigger and returns the matched
        rows plus the outcome template (where matches are to move). A DERIVED view row (C6a VT-3b,
        design/53 L16, board :3831) returns its PARENT view's output NARROWED by the one closed
        dimension — the parent resolved BY ITS FORM (a bind is the master read; a filter is the
        matched rows; a derive is resolved recursively), never the raw record scan; the narrowing
        keeps exactly the parent rows whose derived value equals the derive's value, IN THE PARENT'S
        OWN SHAPE (a dict-shaped fold narrows to a sub-dict; a list-shaped fold to a sub-list). An
        UNSEEDED parent, or a dimension the parent's output shape carries no source for, is REFUSED
        at read (do not flatten — STOP b), as create_view refuses at write. None if no such view."""
        derivs = self.view_derivations(as_of)
        if name in derivs:                                              # a DERIVED view row (VT-3b)
            parent = derivs[name].get("from")
            narrowed = self._serve_derive(name, as_of)                  # raises: unseeded / un-derivable
            return {"name": name, "derive": dict(derivs[name]), "parent": parent,
                    "rows": narrowed, "count": len(narrowed)}
        d = self.view_definitions(as_of).get(name)
        if d is None:
            return None
        rows = [e for e in self.store.all(as_of) if _matches(e, d["when"])]
        return {"name": name, "rows": rows, "count": len(rows), "then": d["then"]}

    # ---- C6a VT-3b: THE DERIVED VIEW SERVED (design/53 L16; board :3831) --------------------
    # execute_view above narrows a derive row's PARENT output by the one closed dimension. The
    # parent's output is resolved by its FORM (archi's binding precision, board :3831): a BIND
    # parent is the master READ (master(name).value — the fold's own output in its own shape, a
    # dict for the accounts fold, a list for the others); a FILTER parent is execute_view's matched
    # rows; a DERIVE parent is resolved RECURSIVELY up to a bind or a filter; it is NEVER the raw
    # record scan (a bind master carries an empty `when`, so execute_view over it would return every
    # row — that is not the master's output). The five derivations compute, per parent row, that
    # row's value along the dimension; the serving keeps the rows whose value equals the derive's.

    def _serve_derive(self, name, as_of=None):
        """Serve one derive row: its parent's output narrowed by the one closed dimension, kept IN
        THE PARENT'S OWN SHAPE (a dict fold -> a sub-dict, a list fold -> a sub-list)."""
        dv = self.view_derivations(as_of)[name]
        parent = dv.get("from")
        where = dict(dv.get("where") or {})
        (dim, value), = where.items()                                   # exactly one move (the door closed this)
        out = self._parent_output(parent, as_of)
        if isinstance(out, Mapping):
            return {k: v for k, v in out.items() if self._derive_value(dim, v, as_of) == value}
        return [r for r in out if self._derive_value(dim, r, as_of) == value]

    def _parent_output(self, parent, as_of=None):
        """A derive parent's OUTPUT, resolved BY ITS FORM (archi :3831). A DERIVE parent recurses; a
        BIND parent is the master read (its own shape); a FILTER parent is execute_view's matched
        rows. An UNSEEDED parent — or a bind whose fold does not resolve to a served master — is
        REFUSED at read, mirroring create_view's write-time refusal (A3). Never the raw record."""
        derivs = self.view_derivations(as_of)
        if parent in derivs:                                            # DERIVE parent -> recurse
            return self._serve_derive(parent, as_of)
        d = self.view_definitions(as_of).get(parent)
        if d is None:                                                   # UNSEEDED parent -> refuse at read
            raise OpError("AR-2", f'derived-view parent "{parent}" names no view definition at head '
                                  "— refused at read, as create_view refuses at write")
        if d.get("bind"):                                               # BIND parent -> the master READ
            m = self.master(parent, as_of)
            if m is None:                                               # a bind the master read cannot serve
                raise OpError("AR-2", f'derived-view parent "{parent}" binds "{d.get("bind")}", '
                                      "whose master read does not serve — refused at read")
            return m["value"]
        return self.execute_view(parent, as_of)["rows"]                 # FILTER parent -> its matched rows

    def _old_relationship_seqs(self, as_of=None):
        """The seqs in the OLD relationship band (superseded or withdrawn) — the liveness complement,
        read off the old_relationships fold (VT-1), never re-derived here."""
        return {r["seq"] for r in self.old_relationships(as_of)}

    def _derive_value(self, dim, row, as_of=None):
        """The value of ONE parent row along the closed dimension `dim`, DERIVED IN CODE from an
        existing source (design/25 v2 the third view form; the five derivations). Raises OpError
        when the row's shape carries no source for `dim` — the serving REFUSES rather than flattening
        a wrong bucket over it (STOP b). Every source is READ, none re-authored."""
        if not isinstance(row, Mapping):
            raise OpError("AR-2", f"derive {dim}: parent row is not a record shape")
        if dim == "actor_class":
            # the ACTING actor's DECLARED class, read AT READ TIME off the account surface (never
            # stored on the row). An event row carries `actor`; a row without one cannot carry it.
            if "actor" not in row:
                raise OpError("AR-2", "derive actor_class: parent output carries no actor — "
                                      "the dimension cannot be derived over it (STOP b)")
            return (self.accounts(as_of).get(row.get("actor")) or {}).get("actor_class")
        if dim == "scope_class":
            # from the rule's SCOPE, or `all` when it names no class (design/25 v2 2.1.4/2.2.4: "scope
            # names no class — the root and the constitution"). A rule that carries no scope, or a
            # space scope, binds ALL — that is the KNOWABLE default, not an un-derivable shape (a rule
            # row is recognised by self-declaration, `rule_id`, never by op name — the active_rules
            # recognition rule). Refuse only a row that is not a rule row at all.
            if "rule_id" not in row:
                raise OpError("AR-2", "derive scope_class: parent output is not a rule row — "
                                      "the dimension cannot be derived over it (STOP b)")
            return _scope_class(row.get("scope"))
        if dim == "item_kind":
            # actor | static. An item row carries `kind` (actor, or a static resource kind).
            if "kind" not in row:
                raise OpError("AR-2", "derive item_kind: parent output carries no kind — "
                                      "the dimension cannot be derived over it (STOP b)")
            return "actor" if row.get("kind") == "actor" else "static"
        if dim == "liveness":
            # active | old, latest-wins. A relationship row is OLD iff its seq is in the old band
            # (superseded / withdrawn), else ACTIVE — read off the old_relationships complement.
            if "seq" not in row:
                raise OpError("AR-2", "derive liveness: parent output carries no seq — "
                                      "the dimension cannot be derived over it (STOP b)")
            return "old" if row.get("seq") in self._old_relationship_seqs(as_of) else "active"
        if dim == "tree_kind":
            # actor_tree | item_tree | non_tree, from the venn2 GEOMETRY and both ENDS (VT-2's
            # relation row). NS/EM (directional containment) between two established actors is the
            # ACTOR tree; NS/EM otherwise is the ITEM tree; the symmetric AD/IN is NON-tree. A row
            # whose shape carries no geometry (e.g. the retired {from,to,rel_kind} old-band shape)
            # is refused — the dimension cannot be derived over it (STOP b, do not flatten).
            if "geometry" not in row:
                raise OpError("AR-2", "derive tree_kind: parent output carries no geometry — "
                                      "the dimension cannot be derived over it (STOP b)")
            if row.get("geometry") not in authority.CONTAINMENT_GEOMETRIES:
                return "non_tree"
            both_actors = authority.is_established(self.store, row.get("subject"), as_of) and \
                authority.is_established(self.store, row.get("object"), as_of)
            return "actor_tree" if both_actors else "item_tree"
        raise OpError("AR-2", f"unknown derived dimension {dim}")       # the door closes the set upstream

    def coverage_statement(self, name, as_of=None):
        """Derived from the definition ALONE: what this view looks at, what it excludes,
        and which dimensions it never discriminates on — every view confesses its blind
        spots mechanically (design/27 §4)."""
        d = self.view_definitions(as_of).get(name)
        if d is None:
            return None
        used = list((d["when"] or {}).keys())
        boundary = " AND ".join(f"{k} = {v}" for k, v in d["when"].items()) if used \
            else "no filters (the whole record)"
        return {"boundary": boundary,
                "complement": f"everything where NOT ({boundary})" if used else "nothing",
                "undiscriminated": [dim for dim in VIEW_FILTER_DIMENSIONS if dim not in used]}

    def op_definitions(self, as_of=None):
        """The definition-born half of the registry, derived from the record (design/27
        §3): operations admitted by CREATE-OP and not retired — the action view's proof
        that the kernel's own surface is data.

        HEAD-MEMOISED SINCE EP-24C, and the memo DIES WITH ITS HEAD. This fold was the only
        one of the three on the gate's per-act path that recomputed on every consultation —
        one to three times inside a single act, measured — while `active_rules` and
        `category_packs` had been head-memoised since campaign 1. The memo is the SAME one
        they use: keyed on the append generation, bumped by the store's own on-append
        listener, so any movement of the head invalidates it and the next read recomputes
        from the record. That boundary is the whole lawfulness of it. A memo keyed to the
        head is a cache under P2 — kill it, replay, identical answers. A memo that could be
        served ACROSS a head change would be a stored answer with a timestamp, which is the
        refused reference wearing an invalidation story. asOf reads are never memoised at
        all (`cached` bypasses for them), because a historical view is never the head."""
        return self.cached("op_definitions", as_of,
                           lambda: self.view_fold("op_definitions", as_of=as_of))

    def _op_definitions(self, as_of=None, source=None):
        live = {}
        for e in (source or self.store).all(as_of):
            p = e.get("payload") or {}
            if e["action"] in ("CREATE-OP", "AMEND-OP") and p.get("kind") == "op_definition":
                live[p["name"]] = {"name": p["name"], "definition": p.get("definition"),
                                   "tier": p.get("tier", "ordinary"), "seq": e["seq"]}  # AMEND-OP supersedes in place
            elif e["action"] == "RETIRE-OP" and p.get("name") in live:
                del live[p["name"]]
        return live

    # ---- MASTERS as records + the standing push (design 28 §6, §I4; EP-08) -------------
    # The five masters + two registries are SEEDED view-definition records that BIND to an
    # S-plane fold (FOLD_NAMES). The engine functions below are those folds; nothing hardcodes
    # which masters exist — that is data in the record. `master(name)` runs the bound fold.

    def _actors(self, as_of=None):
        """Actor master (tree 2.2.1): every minted actor, latest per id (a CREATE-ACTOR fold)."""
        out = {}
        for e in self.store.by_action("CREATE-ACTOR", as_of):
            p = e.get("payload") or {}
            if p.get("actor_id"):
                out[p["actor_id"]] = {"actor_id": p["actor_id"], "role": p.get("role"),
                                      "actor_class": p.get("actor_class"), "seq": e["seq"]}
        return out

    # ---- the account surface over the actor master (A3; design/31 J1) ------------------
    # Identity is an ACCOUNT: a recorded founding + verification evidence, verified DERIVED
    # per check (never a stored boolean — a boolean rots). Verification bottoms out at the
    # founding: owner/SYSTEM/PC_RUNTIME are FOUNDING-ASSERTED, a third resolution state
    # (ANCHORED), derived from the genesis CREATE-ACTOR records — the founding IS the anchor,
    # so no account record is minted for them (addendum-3 ruling 1b). These are folds over the
    # record; nothing here stores a status (P2).

    def _anchor_ids(self, as_of=None):
        """The founding anchors, DERIVED (design/31 J1; ruling 1b) — TIGHTENED to the CONTIGUOUS
        FOUNDING PREFIX (EP-16 directed fix, EP-15 raise #2). An anchor is an actor minted by the
        founding runtime WITHIN the unbroken initial run of records it asserted; the prefix closes
        PERMANENTLY at the first record asserted by anyone else. So a later caller spoofing the
        founding-runtime name mints NO anchor once any post-founding act has landed — the loose
        EP-15 form (any CREATE-ACTOR by the runtime's name, anywhere) is retired. The founding
        runtime is the asserter of the FIRST CREATE-ACTOR; the leading FOUND-STORE designation
        (asserted by the root owner, before any runtime actor exists) precedes the runtime and does
        not break the prefix. RESIDUAL CAP (stated, not chased here): a spoof as the LITERAL first
        post-install act still lands inside the prefix — closed for real by EP-17's verified
        identity. Walks by seq and stops at the break, so the scan is bounded by the founding
        block, and is head-memoised (the prefix is immutable after genesis).

        ONE WALK, TWO ANSWERS (EP-26). The prefix's ids and the prefix's END are the same
        computation read two ways, so `founding_prefix_end` below is not a second walk that
        could drift from this one. The sweep needs the end because genesis is appended DIRECTLY
        — the gate's own guard states that the founding and the audit mirror bypass it — and a
        record that never crossed the gate has no admission for a counterfactual to
        re-evaluate."""
        return self._founding_prefix(as_of)["ids"]

    def _founding_prefix(self, as_of=None):
        def compute():
            founding_runtime = None
            ids = set()
            seq = 1
            end = 0
            while True:
                e = self.store.by_seq(seq)
                if e is None or (as_of is not None and e["seq"] > as_of):
                    break
                actor = e["actor"]
                if founding_runtime is None:
                    if e["action"] == "CREATE-ACTOR":
                        founding_runtime = actor                       # asserter of the first actor mint
                        ids.add(founding_runtime)
                        ids.add((e.get("payload") or {}).get("actor_id") or e.get("object"))
                    elif e["action"] != "FOUND-STORE":
                        break                                          # something other than the designation first
                elif actor != founding_runtime:
                    break                                              # first record by anyone else -> prefix closed
                elif e["action"] == "CREATE-ACTOR":
                    ids.add((e.get("payload") or {}).get("actor_id") or e.get("object"))
                end = seq
                seq += 1
            return {"ids": ids, "end_seq": end}
        return self.cached("founding_prefix", as_of, compute)

    def founding_prefix_end(self, as_of=None):
        """The last seq of the contiguous founding block — where genesis stops and gated acts
        begin. Read by the reconciliation sweep, which never treats a founding record as a
        candidate: re-running the gate's admission test over genesis would ask whether the
        founding was permitted by the world the founding itself created."""
        return self._founding_prefix(as_of)["end_seq"]

    def _verified_accounts(self, as_of=None):
        """The set of accounts with GROUNDED verification evidence (raise #2). Least fixpoint:
        the founding anchors are the recursion floor (J1 — verification bottoms out at the
        founding); an account is verified iff some VERIFY-ACCOUNT names it with a verifier that
        is itself already grounded (an anchor, or an already-verified account). A verification
        loop that never reaches an anchor never grounds, so it never enters — cycles cannot
        manufacture verification. An anchor id is never a 'verified account' (it is ANCHORED, a
        distinct state), so it is excluded from the result even if a verification names it."""
        ground = self._anchor_ids(as_of)
        verifications = [((e.get("payload") or {}).get("account"), e["actor"])
                         for e in self.store.by_action("VERIFY-ACCOUNT", as_of)]
        verified = set()
        changed = True
        while changed:
            changed = False
            for acct, verifier in verifications:
                if acct and acct not in ground and acct not in verified \
                        and (verifier in ground or verifier in verified):
                    verified.add(acct)
                    changed = True
        return verified

    def verified(self, account_id, as_of=None):
        """Is this account VERIFIED — does it hold live verification evidence whose verifier
        chain grounds at the founding anchors? DERIVED per check, never a stored boolean
        (design/31 J1). A founding anchor returns False here — it is ANCHORED, a third state
        (founding-asserted, not system-verified); read its state through accounts()."""
        return account_id in self._verified_accounts(as_of)

    def _grounded_actors(self, as_of=None):
        """The actors GROUNDED in the constitution's root group (design/25 v2.1 ruling 23; C6a
        VT-2) — the ACTOR mirror of `_verified_accounts`, riding the SAME anchor least-fixpoint.
        The founding anchors are the recursion floor: the constitution's root IS the founding, so
        an anchor grounds by being the founding (the mother space's counterpart for actors). Every
        other actor grounds iff a containment (NS/EM) edge names it as SUBJECT with an OBJECT (its
        group) that is ITSELF already grounded — an anchor, or an already-grounded actor. A group
        chain that never reaches an anchor never grounds, so an orphan never enters and a loop never
        manufactures grounding (the exact shape of `_verified_accounts`, and of the space tree's
        'every chain terminates at the mother space'). Many parents lawful: ANY grounded parent
        grounds the child, so a node with three chains grounds if even one reaches the root."""
        ground = self._anchor_ids(as_of)
        edges = authority.actor_containment_edges(self.store, as_of)
        grounded = set()
        changed = True
        while changed:
            changed = False
            for subj, obj in edges:
                if subj and subj not in ground and subj not in grounded \
                        and (obj in ground or obj in grounded):
                    grounded.add(subj)
                    changed = True
        return grounded

    def actor_grounded(self, actor, as_of=None):
        """Does `actor` reach the constitution's root group through at least one containment chain
        (ruling 23)? A founding anchor grounds by being the founding; every other actor grounds via
        a chain to one. DERIVED per check, never a stored boolean — the space-tree grounding's shape
        (`space_reaches(mother, sp)`), for actors. The gate reads this to refuse an orphan edge."""
        return actor in self._anchor_ids(as_of) or actor in self._grounded_actors(as_of)

    def accounts(self, as_of=None):
        return self.cached("accounts", as_of, lambda: self._accounts(as_of))

    def _accounts(self, as_of=None):
        """The account surface (A3): every FOUNDED identity keyed by id, each carrying its
        resolution state — anchored | verified | unverified. Anchors are derived from the
        genesis CREATE-ACTOR records and are authoritative (never overwritten by an account);
        accounts are CREATE-ACCOUNT records, verified DERIVED. A bare legacy name (no account)
        is NOT here — the gate resolves it to `unverified:<name>` and it STILL ACTS (the
        transition state until EP-17 narrows the founding openness grant)."""
        anchors = self._anchor_ids(as_of)
        verified = self._verified_accounts(as_of)
        actor_class = {}
        for e in self.store.by_action("CREATE-ACTOR", as_of):
            p = e.get("payload") or {}
            actor_class[p.get("actor_id") or e.get("object")] = p.get("actor_class")
        out = {}
        for aid in anchors:
            out[aid] = {"account_id": aid, "actor_class": actor_class.get(aid),
                        "founded_by": None, "resolution": "anchored"}
        for e in self.store.by_action("CREATE-ACCOUNT", as_of):
            p = e.get("payload") or {}
            aid = p.get("account_id") or e.get("object")
            if aid is None or aid in anchors:     # an anchor is never overwritten by an account
                continue
            out[aid] = {"account_id": aid, "actor_class": p.get("actor_class"),
                        "founded_by": p.get("founded_by") or e["actor"],
                        "resolution": "verified" if aid in verified else "unverified"}
        return out

    def resolve_asserted_by(self, caller, as_of=None):
        """A2 (design/31 J1 + §9 pass-two #4): resolve the CALLER to who-the-record-verified —
        the identity written into a record's provenance.asserted_by. A FOUNDED identity (a
        founding anchor or an account) resolves to itself; a bare legacy name resolves to
        `unverified:<name>`. Enforcement of no-account->no-act is EP-17's flip under the
        openness grant; this EP RESOLVES, and a bare name STILL ACTS. Computed FRESH every act
        from the record (the chain evaluated live, J3): there is no session and no cached login
        — the record IS the session, so every act resolves anew (the web-auth wrong reference,
        refused)."""
        if caller in self._anchor_ids(as_of):
            return caller
        if caller in self.accounts(as_of):
            return caller
        return f"unverified:{caller}"

    # ---- the secrets vault surface (EP-19; design/31 J8) --------------------------------
    # Verify, never reveal: a secret's VALUE lives in the vault (write-once, no read path);
    # the record holds only the sealed HASH and the usage decisions. This fold reads the
    # sealed hash for a name — the only thing about a secret the record can answer, and even
    # that is a hash, not the value. A fold over the record; nothing stores a status (P2).

    def sealed_secret_hash(self, name, space=None, as_of=None):
        """The latest secret sealed under `name` IN `space` — its HASH (design/31 J8). ROTATION is
        supersession by hash: re-sealing a name records a new SEAL-SECRET carrying a new hash,
        and this fold reads LATEST-PER-(SPACE, NAME) (the newest seal wins; an older sealed value
        is superseded, never revealed and never comparable-against again). Keying on (space, name)
        rather than bare name is what keeps a seal in one space from clobbering a same-named sealed
        baseline in another (everything lives in a space, J2; the record already carries one via the
        general space passthrough, read back through authority.space_of). `space=None` resolves to
        the mother space — so in the one-space world this is IDENTICAL to the old latest-per-name
        (every seal and every query resolve to the mother space). Returns the "sha256:<hex>" string,
        or None if `name` was never sealed in `space` (VERIFY-SECRET then records NO-MATCH — you
        cannot match a secret that was never sealed here). A fold, never a status."""
        q_space = space if space is not None else authority.mother_space(self.store, as_of)
        latest = None
        for e in self.store.by_action("SEAL-SECRET", as_of):
            p = e.get("payload") or {}
            if p.get("name") == name and authority.space_of(self.store, e, as_of) == q_space:
                latest = p.get("secret_hash")
        return latest

    # ---- the authority surface (EP-16; design/31 J2 + J3-data, design/30 §1) ------------
    # Spaces (where), grants (how far), roles (a name), and the two questions power asks —
    # power_view (the hardened profile) and covers (the one question). All are folds over the
    # record delegated to kernel.authority; nothing here stores a status (P2 applied to
    # authority). PURE READS this EP — they answer, they do not refuse; EP-17 wires refusal.
    #
    # EP-24B: THE FOLD'S READING PATTERN, AND NOTHING ELSE. Every fold below runs the SAME
    # `kernel.authority` code it always ran, unchanged to the byte. What changed is the record
    # source it is handed: the governance index (store.GovernanceIndex), which holds the seq
    # numbers of the law-and-grant records and resolves each one out of the record at read
    # time. `covers` still computes the positive grant and its complement live on every call,
    # exactly as design/30 §1 specifies; it simply no longer walks the observations it cannot
    # be affected by. Nothing anywhere holds a verdict.
    #
    # THE UNACCELERATED FOLD IS RETAINED, PERMANENTLY, as the standing differential baseline
    # for this surface — `authority_fold(name, ..., accelerated=False)` reads the whole record.
    # Not an era-pinned migration oracle: both sides are current code, so both are live and
    # design/10 §11.2a's two-baseline logic does not apply here. A divergence between them is
    # a defect, never a discovery.

    AUTHORITY_FOLDS = ("mother_space", "spaces", "space_reaches", "reaches_space",
                       "within_makers_reach", "space_of", "grants", "roles", "role_meaning",
                       "power_view", "covers")

    def authority_fold(self, name, *args, accelerated=True, as_of=None):
        """Run one named authority fold against either the governance index (accelerated) or
        the whole record (the retained unaccelerated oracle). ONE implementation, TWO record
        sources — so the standing differential tests exactly one variable, the subset. Two
        separate implementations could also diverge in logic, which is a strictly larger
        failure surface for nothing gained."""
        if name not in self.AUTHORITY_FOLDS:
            raise ValueError(f"{name!r} is not an authority fold — the family is: "
                             + ", ".join(self.AUTHORITY_FOLDS))
        source = self.store.governance_index() if accelerated else self.store
        return getattr(authority, name)(source, *args, as_of=as_of)

    def mother_space(self, as_of=None):
        return self.authority_fold("mother_space", as_of=as_of)

    def spaces(self, as_of=None):
        """The space tree (J2), DERIVED: {space_id: {name, parent, seq}}, the mother at the root."""
        return self.authority_fold("spaces", as_of=as_of)

    def space_reaches(self, outer, inner, as_of=None):
        """Containment (J2): does reach over `outer` cover `inner` (inner IS outer or a descendant)?"""
        return self.authority_fold("space_reaches", outer, inner, as_of=as_of)

    def reaches_space(self, account, target, as_of=None):
        """Does `account` reach `target` — a covering grant whose space contains it (J2 containment)?
        The attenuation-family SPATIAL leash for CREATE-SPACE (reach over the parent) and CREATE-ROLE
        (reach over its space); inert under the openness grant (EP-17 Y3). A PURE READ."""
        return self.authority_fold("reaches_space", account, target, as_of=as_of)

    def within_makers_reach(self, creator, proposed, as_of=None):
        """Is `proposed` {grantee, actions, info, space} within `creator`'s own reach (attenuation,
        E1/X4)? Returns (ok, reason). The bar GRANT enforces at creation, reused by the REVOKE leash
        (EP-17 Y3): you may take away only what you could give. A PURE READ."""
        return self.authority_fold("within_makers_reach", creator, proposed, as_of=as_of)

    def space_of(self, record, as_of=None):
        """The DEFAULT-SPACE fold (J2, the migration): a record's space is its explicit payload
        `space` or, absent one, the mother space — membership DERIVED, never stamped."""
        return self.authority_fold("space_of", record, as_of=as_of)

    def grants(self, as_of=None):
        """The grant fold (J3), the permission master's bound fold (rebound from GRANT-READ this
        EP): the live four-dimensional grants, revoke-superseded. See the class note above the
        old GRANT-READ sight surface — sight stays its own check (can_read, protection.py), one
        info-kind of the general model; the join is EP-17's (RAISED)."""
        return self.authority_fold("grants", as_of=as_of)

    def roles(self, as_of=None):
        return self.authority_fold("roles", as_of=as_of)

    def role_meaning(self, role, as_of=None):
        """A role's DERIVED meaning (J3): the live grants that cite it — changes when they change."""
        return self.authority_fold("role_meaning", role, as_of=as_of)

    def power_view(self, account, as_of=None):
        """The account's hardened profile (design/30 §2): the grants covering it, aggregated per
        dimension. A PURE READ — computed fresh every call, no stored capability set."""
        return self.authority_fold("power_view", account, as_of=as_of)

    def covers(self, account, action, info_kind, space, as_of=None):
        """THE ONE QUESTION (J3): does an active grant let `account` take `action` on `info_kind`
        in `space` (all four dimensions in one grant, space by containment)? A PURE READ."""
        return self.authority_fold("covers", account, action, info_kind, space, as_of=as_of)

    # ---- root authority: the chain-end, the succession fold, structural reach (EP-18; design/31 J7) --
    # Root authority is the CHAIN-END, DERIVED from the founding plus the succession fold — never a
    # stored owner field (the refused wrong reference: ownership-transfer-as-a-field-update). The
    # founding owner is the chain-end until a completed HANDOVER supersedes them with the accepted
    # successor (exit-with-continuity). Every read recomputes; nothing here stores a status (P2).

    HUMAN_ACTOR_CLASS = "human"   # the actor-class token a successor must carry (the pack's actor-classes)

    def founding_root(self, as_of=None):
        """The founding chain-end, DERIVED from the record: the actor the founding minted with the
        root-instruction-authority role (the anchor). Not a hardcoded 'owner' string — the founding
        IS the anchor (design/31 J1: verification bottoms out at the founding). Falls back to the
        historical 'owner' only for a bare store with no founding."""
        for e in self.store.by_action("CREATE-ACTOR", as_of):
            if (e.get("payload") or {}).get("role") == "root-instruction-authority":
                return (e.get("payload") or {}).get("actor_id") or e.get("object")
        return "owner"

    def current_successor(self, as_of=None):
        """The CURRENT successor, a FOLD (latest valid designation-acceptance pair), never a stored
        pointer (design/31 J7). A DESIGNATE-SUCCESSOR names a successor and resets any prior
        acceptance; the named successor's own ACCEPT-SUCCESSION completes the pair; a REVOKE-SUCCESSION
        (or a superseding designation) clears it. Validity is RE-CHECKED LIVE at the moment the fold is
        read (the live-chain rule, design/31 J3 — the mentor's RAISED-BY-DESIGN read: a designation may
        age, so verify at the moment of the fold's validity): the successor must be VERIFIED (EP-15)
        AND actor_class human AT READ TIME, not merely at designation. An aged-out or downgraded
        successor simply stops being valid — no stored boolean to rot."""
        designated, accepted = None, False
        for e in self.store.all(as_of):
            a = e["action"]
            if a == "DESIGNATE-SUCCESSOR":
                designated, accepted = (e.get("payload") or {}).get("successor"), False
            elif a == "REVOKE-SUCCESSION":
                designated, accepted = None, False
            elif a == "ACCEPT-SUCCESSION" and designated is not None and e["actor"] == designated:
                accepted = True
        if not accepted or designated is None:
            return None
        if not self.verified(designated, as_of):
            return None
        if self.accounts(as_of).get(designated, {}).get("actor_class") != self.HUMAN_ACTOR_CLASS:
            return None
        return designated

    def chain_end(self, as_of=None):
        """The current ROOT AUTHORITY holder — DERIVED, never stored (no owner FIELD to update). The
        founding root until a completed HANDOVER supersedes it with the successor who was valid as of
        that handover. A HANDOVER only lands through the gate's anchor guard, which refuses it without
        a valid successor, so every recorded handover is lawful by construction (the record polices
        its builder). Under the founding (no handover) this is the founding root, so every campaign-1
        owner-root check is unchanged; only after a handover does the chain-end move. Kill the
        derivation, replay, the chain-end reconstructs identically."""
        return self.cached("chain_end", as_of, lambda: self._chain_end(as_of))

    def _chain_end(self, as_of=None):
        end = self.founding_root(as_of)
        for e in self.store.by_action("HANDOVER", as_of):
            succ = self.current_successor(e["seq"])
            if succ is not None:                       # gate-guaranteed; defensive
                end = succ
        return end

    # ---- keys and ceremonies: the key state a signed door will read (EP-36; design/37 Q6/Q8) --
    # Key validity is a FOLD over bind/rotate/revoke, evaluated live — latest-supersession-wins,
    # nothing cascades, verification bottoms out at the founding. All PURE READS delegating to
    # kernel.keys (the authority_fold precedent): they answer, they do not refuse; the gate reads
    # them to leash the root key, and EP-37 makes the per-account door read them. Every fold here is
    # INERT in a world whose founding declares no key-bind law (key_law_live) — the wire-at-birth
    # gate that keeps the held founding-move from moving a byte of succession behaviour.

    def bound_key(self, account, as_of=None):
        """The public key VALID for `account` now (latest bind/rotate wins, revoke -> None), or the
        binding valid AT a past deciding time when `as_of` is given (A5)."""
        return keys_mod.bound_key(self.store, account, as_of)

    def key_valid(self, account, as_of=None):
        """Does `account` hold a live, non-revoked key binding? DERIVED, never a stored boolean."""
        return keys_mod.key_valid(self.store, account, as_of)

    def key_law_live(self, as_of=None):
        """Is the key-bind LAW declared in the live law — should the key leash engage at all? A
        world whose founding declares no key-bind law leashes nothing (the succession key half and
        the root anchor stay inert)."""
        return keys_mod.key_law_live(self, as_of)

    def root_key(self, as_of=None):
        """The founding-asserted key of the root authority holder (the chain-end), or None where
        the ceremony has not sealed one (held until F6 — test keys until the owner's word)."""
        return keys_mod.root_key(self.store, self, as_of)

    def successor_key_bound(self, as_of=None):
        """Is a successor key bound through succession — the current successor (verified + human at
        read) holds a valid key binding? The root anchor and the handover key half read this."""
        return keys_mod.successor_key_bound(self.store, self, as_of)

    def is_root_key_op(self, draft, as_of=None):
        """Does this key-rotate/key-revoke draft target the ROOT key (the key bound to the
        chain-end)? Only root key ops are leashed; a non-root key op is unleashed."""
        return keys_mod.is_root_key_op(self, draft, as_of)

    def reaches_space_structural(self, account, target, action, as_of=None):
        """R-B (EP-18), TIGHTENED to EXACT-ACTION (EP-19 R-C3): does `account` hold a covering grant
        whose action dimension includes THE SPECIFIC structural act `action` (CREATE-SPACE to found a
        space, CREATE-ROLE to found a role) and whose space contains `target`? This is the
        attenuation-family spatial leash for founding spaces/roles — NOT mere space reach: sight is
        not authority, so a read-only grant over a space must not found subspaces/roles there. R-C3
        replaces class-level membership (any structure-class action reached any structural act) with
        the exact act: a CREATE-ROLE grant no longer authorises founding a space, and vice versa —
        class membership alone no longer reaches (the zero-trust ruling: match = the right, and the
        grant must match THIS act). The `structure-actions` vocabulary pack stays as vocabulary (it
        names which acts are structure-class), but the REACH check is now on the exact action. Under
        the founding openness grant (actions = *) every act is covered, so the leash stays INERT until
        the owner narrows; the root (the chain-end) is exempted at the gate before this is consulted.
        A PURE READ, folded live."""
        for g in self.grants(as_of).values():
            if g["grantee"] not in (account, authority.WILDCARD):
                continue
            if not self.space_reaches(g["space"], target, as_of):
                continue
            if authority.dim_covers(g["actions"], action):
                return True
        return False

    def _relationships(self, as_of=None):
        """Relationship master (tree 4, venn2 rows): the derived graph from CREATE-RELATIONSHIP
        records — ONE venn2 row per record, the C6a VT-2 shape {subject, object, geometry, zone}
        (design/25 v2.1; 25-view-tree-v2.json). GEOMETRY is the closed venn2 value {AD, IN, NS, EM}
        — `unrelated` is never stored, so a row always carries one of the four. ZONE is {edge, core,
        unknown} or None (optional, asserted). NO rel_kind is stored (ruling 7): the FRAME is the
        act's cited rule (surfaced here as `frame`), the READING is that rule's text, the ROLES are
        the record's actor/object/target — all DERIVED at read, never a stored kind. The old
        first-mint shape {from, to, rel_kind} is retired; the erased-band fold `old_relationships`
        (VT-1) keeps reading the record's own carried fields and is untouched."""
        return [{"subject": (e.get("payload") or {}).get("subject"),
                 "object": (e.get("payload") or {}).get("object"),
                 "geometry": (e.get("payload") or {}).get("geometry"),
                 "zone": (e.get("payload") or {}).get("zone"),
                 "frame": e.get("rule_cited"), "seq": e["seq"]}
                for e in self.store.by_action("CREATE-RELATIONSHIP", as_of)]

    def _resources(self, as_of=None):
        """Resource master (tree 2.2, actable-on): the info/content resources minted (a CREATE-INFO
        fold), latest per object. Minimal v1: the info surface; the fuller actor-inclusive resource
        view composes actors + devices + tunnels as those masters mature (RAISED, honest cap)."""
        out = {}
        for e in self.store.by_action("CREATE-INFO", as_of):
            out[e.get("object")] = {"object": e.get("object"),
                                    "kind": (e.get("payload") or {}).get("kind"), "seq": e["seq"]}
        return out

    def creator_of(self, obj, as_of=None):
        """The actor who MINTED an object — the actor of its EARLIEST record (its creation). The sop
        check's maker lookup (design 28 §5; EP-09), read through the view surface here rather than a
        private store scan in opdefs/protection (the read stack, §I8: operations consult views)."""
        for e in self.store.all(as_of):
            if e.get("object") == obj:
                return e["actor"]
        return None

    def halted_watchers(self, as_of=None):
        """The braked watchers (EP-09; design 28 §7): actors whose ops are frozen by a HALT-WATCHER not
        yet resolved. Ordered fold — a later RESOLVE-WATCHER lifts a halt, a later HALT-WATCHER re-brakes.
        Only the ROOT AUTHORITY holder's RESOLVE-WATCHER counts (a watcher cannot self-resolve — the
        resolution is the root's), and SYSTEM / the root can NEVER be braked (the recorder and the
        resolver stay live, so the record never goes dark). The resolver/unbrakable identity is the
        CHAIN-END, DERIVED (R-C1) — never the hardcoded "owner"; under the founding it IS "owner", and
        after a lawful handover it is the successor. SYSTEM stays a literal (the recorder, a founding
        constant). The gate reads this to freeze a halted watcher's ops."""
        # Fold ONLY the (rare) brake records in seq order — not store.all(): this runs at the gate on
        # EVERY op, so it must be cheap. HALT-WATCHER / RESOLVE-WATCHER are governance-rare.
        root = self.chain_end(as_of)
        events = sorted(self.store.by_action("HALT-WATCHER", as_of) + self.store.by_action("RESOLVE-WATCHER", as_of),
                        key=lambda e: e["seq"])
        halted = set()
        for e in events:
            if e["action"] == "HALT-WATCHER":
                w = (e.get("payload") or {}).get("watcher")
                if w and w not in ("SYSTEM", root):
                    halted.add(w)
            elif e["actor"] == root:   # only the ROOT authority holder's RESOLVE-WATCHER lifts a halt
                halted.discard((e.get("payload") or {}).get("watcher"))
        return halted

    # ---- governance health gauges (design 28 §8; EP-10) — pure derivations, append NOTHING ----

    def metabolism(self, since_seq=None, as_of=None):
        """The governance-debt gauge (design 28 §8): per LAW KIND, the INTAKE (law records created)
        vs the RETIREMENT (law records retired) over a RECORD-TIME window — a `since_seq` floor, NEVER
        the wall clock (15.1: the clock is a sensor). `record_time_now` is the recorded-tick clock
        (EP-07), the honest time source if a rate-per-time is wanted. A view routed to the owner queue;
        it appends nothing. High intake with low retirement is accruing governance debt."""
        g = {k: {"intake": 0, "retire": 0} for k in ("rule", "op", "view")}
        intake_of = {"CREATE-RULE": "rule", "CREATE-OP": "op", "CREATE-VIEW": "view"}
        for e in self.store.all(as_of):
            if since_seq is not None and e["seq"] <= since_seq:
                continue
            a = e["action"]
            if a in intake_of:
                g[intake_of[a]]["intake"] += 1
            elif a == "RETIRE-OP":
                g["op"]["retire"] += 1           # rules/views retire by latest-wins supersession, not a RETIRE verb
        for k in g:
            g[k]["net"] = g[k]["intake"] - g[k]["retire"]
        record_time_now = max(((t.get("payload") or {}).get("now", 0)
                               for t in self.store.by_action("TICK", as_of)), default=0)
        return {"per_kind": g, "since_seq": since_seq, "record_time_now": record_time_now}

    def paper_tigers(self, as_of=None):
        """Mandated views with no recorded servicing (design 28 §8; design/51 N6, EP-50): a
        view_definition carrying a `refresh` mandate that the record shows was never serviced is a
        paper tiger — it claims a refresh cadence the record cannot account for. A pure derivation
        routed to the owner queue; appends nothing.

        SERVICING IS A RECORD (N6). A VIEW-SERVICE DECISION (view_name, head_seq, servicer) is
        appended each time a mandated view is serviced, so a mandated MASTER/query view (no move_to)
        — which in v1 had NO per-run signal at all — now CLEARS when its servicing is on the record,
        and a MASTER never serviced is a FOLD, not an inference (the v1 gap closed): its own former
        honest cap ("delivery is the only one") is discharged.

        DELIVERY IS RETAINED AS A SECOND WITNESS (design/51 §6 item 4). A mandated FILTER view that
        has DELIVERED but carries no VIEW-SERVICE record is NOT a paper tiger — the delivery signal
        stays beside the servicing record until one campaign of servicing records exists. Same fold
        family as boot-integrity: a rule (the mandate) × what the record shows the system did."""
        q = self.queues(as_of)
        serviced = {(e.get("payload") or {}).get("view_name")
                    for e in self.store.by_action("VIEW-SERVICE", as_of)}
        out = []
        for d in self.view_definitions(as_of).values():
            if not d.get("refresh"):
                continue
            name = d["name"]
            if name in serviced:
                continue                          # serviced: a VIEW-SERVICE record names it (N6)
            move_to = (d.get("then") or {}).get("move_to")
            if move_to and q.get(move_to):
                continue                          # SECOND WITNESS: delivered — retained (§6 item 4)
            reason = ("mandated move-to view has no VIEW-SERVICE record and has delivered nothing"
                      if move_to else
                      "mandated master/query view has no VIEW-SERVICE record over the current head")
            out.append({"name": name, "refresh": d["refresh"], "reason": reason})
        return out

    def contradictions(self, as_of=None):
        """The comparison contradiction view (design 28 §9; EP-11) — the ONE comparison law made a
        derivation. Verdicts from DIFFERENT frames on the same (a, b) are DIFFERENT INFORMATION: never a
        conflict, both kept, no merger, no averaging — keeping both IS the feature. Only SAME-frame
        incompatibility is a contradiction: verdicts on the same (a, b, frame) holding more than one
        DISTINCT verdict value. Routed to the owner queue as a VIEW — a pure derivation that appends
        nothing (the EP-10 gauge precedent). Frames are DATA, read off each verdict (never an enum), and
        this does NOT reuse ROOT-NEG-6's rule-activation machinery — it guards comparison OUTPUTS, a
        different record family. (v1: (a, b) is ordered — a is compared to b; normalising a/b order is a
        later refinement, RAISED.)"""
        by_key = {}
        for e in self.store.by_action("COMPARE", as_of):
            p = e.get("payload") or {}
            if p.get("kind") != "verdict":
                continue
            by_key.setdefault((p.get("a"), p.get("b"), p.get("frame")), set()).add(p.get("verdict"))
        return [{"a": a, "b": b, "frame": frame, "verdicts": sorted(v)}
                for (a, b, frame), v in by_key.items() if len(v) > 1]

    # ---- C6a VT-6c: THE TWO CHECKS — the sideways bounce, the unseen flag (record folds) ----
    # design/25 v2.4 rulings 12 (neighbour against neighbour — the sideways check), 15 (the rogue-chief
    # / unseen test), 14 (detection never legitimacy); design/53 B10. Both fold the DURABLE stamps in the
    # committed act rows (provenance["stamps"], VT-6d) — the SAME family as `contradictions` (group by a
    # shared key, flag a key holding more than one distinct value) and `paper_tigers` (for each mandated
    # thing, flag the one the record shows was never serviced). Each is a pure derivation on the owner
    # queue that APPENDS NOTHING. NEITHER reads the in-memory pending buffer — a stamp exists only in a
    # row (archi :3885): the checks read `store.all()` and the rows' durable stamps, never
    # `_pending_stamps`. Detection never legitimacy (ruling 14): the checks FLAG, they never bless — a
    # refused act stays refused carrying its stamps, and no number of agreeing stamps outvotes the record.
    _REQUIRED_STAMPS_POLICY = "required-stamps"   # gate.REQUIRED_STAMPS_POLICY; the literal avoids the
    #                                               gate->views import direction (gate imports views).

    def _rows_with_stamps(self, as_of=None):
        """Committed act rows carrying a durable stamps list (provenance["stamps"], VT-6d), each paired
        with its stamps as a plain list. A RECORD fold — reads store rows only, never the in-memory
        pending buffer (a stamp exists only in a row, :3885)."""
        rows = []
        for e in self.store.all(as_of):
            prov = e.get("provenance")
            stamps = prov.get("stamps") if isinstance(prov, Mapping) else None
            if isinstance(stamps, (list, tuple)):
                rows.append((e, list(stamps)))
        return rows

    def stamp_divergences(self, as_of=None):
        """THE SIDEWAYS BOUNCE (design/25 ruling 12/13, design/53 B10 clause a). Every master that
        co-stamped one act witnessed the record at ONE head, so an honest row's stamps AGREE on the
        record version they saw; a master stamped at an OLDER record version saw a stale world and
        DIVERGES from its neighbours (its hash is the hash of that older world). The fold groups the
        stamps touching one FACT (the act's own row) and flags any fact whose relevant masters' stamps
        hold more than one distinct version — NAMING the stale master(s), the view(s) below the row's
        head version. Same shape as `contradictions`: group by a shared key (the fact), flag a key
        holding more than one distinct value (the version the neighbours saw). A pure RECORD fold over
        the durable stamps; it appends nothing and reads no buffer (:3885). Detection never legitimacy
        (ruling 14): it flags, never blesses — a divergence found here overturns no record."""
        out = []
        for e, stamps in self._rows_with_stamps(as_of):
            witnesses = [s for s in stamps if isinstance(s, Mapping)]
            versions = {s.get("version") for s in witnesses}
            if len(versions) <= 1:
                continue                                    # neighbours agree on what they saw — no flag
            ints = [v for v in versions if isinstance(v, int) and not isinstance(v, bool)]
            head = max(ints) if ints else None
            stale = sorted(v for v in {s.get("view") for s in witnesses
                                       if s.get("version") != head} if v is not None)
            out.append({"seq": e.get("seq"),
                        "versions": sorted(v for v in versions if v is not None),
                        "stale_masters": stale,
                        "saw": [{"view": s.get("view"), "version": s.get("version"),
                                 "hash": s.get("hash")} for s in witnesses],
                        "reason": "a master co-stamping this act saw an older record version than its "
                                  "neighbours — a stale master (ruling 12, neighbour against neighbour); "
                                  "the stamp adds no legitimacy (14)"})
        return out

    def unseen_rows(self, as_of=None):
        """THE UNSEEN FLAG — the rogue-chief test (design/25 ruling 15, design/53 B10). A committed row
        of a STAMPED class (a class the required-stamps policy names) that a RELEVANT master — the
        master views its reach touches, computed by `relevant_folds` — never stamped is flagged as
        UNSEEN: the organisation never saw it, a row written past the views. The fold reads the committed
        rows and their durable stamps only (never the pending buffer, :3885); it appends nothing. A
        fully-stamped row (every relevant master present in provenance["stamps"]) is not flagged. Same
        shape as `paper_tigers`: for each mandated thing, flag the one the record shows was never
        serviced. Detection never legitimacy (ruling 14): the flag blesses nothing and refuses nothing —
        it is a finding on the owner queue."""
        required_by_class = self.policy_value(self._REQUIRED_STAMPS_POLICY, as_of) or {}
        if not isinstance(required_by_class, Mapping):
            return []                                       # a malformed policy names no stamped class
        out = []
        for e in self.store.all(as_of):
            action = e.get("action")
            if action not in required_by_class:
                continue                                    # not a stamped class — nothing owed (ruling 15)
            prov = e.get("provenance")
            raw = prov.get("stamps") if isinstance(prov, Mapping) else None
            stamped = ({s.get("view") for s in raw if isinstance(s, Mapping)}
                       if isinstance(raw, (list, tuple)) else set())
            relevant = self.relevant_folds(e)               # the masters this row's reach touches
            unseen = sorted(v for v in relevant if v not in stamped)
            if unseen:
                out.append({"seq": e.get("seq"), "action": action, "unseen_masters": unseen,
                            "reason": "a master whose reach this act touched never stamped it — a row "
                                      "written past the views (ruling 15, the rogue-chief test); the "
                                      "missing stamp adds no legitimacy either way (14)"})
        return out

    # ---- the kernel dictionary (EP-12; cgl-app pattern lowered) — pure folds, append NOTHING ----

    def _disputed_entry_seqs(self, as_of=None):
        """The dictionary-entry seqs under an UNRESOLVED dispute — a fold, never a stored 'disputed'
        flag: DISPUTE(ref_seq) marks, RESOLVE-DISPUTE(ref_seq) lifts (cgl-app dispute/resolution)."""
        disputes = {(e.get("payload") or {}).get("ref_seq") for e in self.store.by_action("DISPUTE", as_of)}
        resolved = {(e.get("payload") or {}).get("ref_seq") for e in self.store.by_action("RESOLVE-DISPUTE", as_of)}
        return {s for s in disputes if s is not None} - {s for s in resolved if s is not None}

    def dictionary(self, entity_kind=None, as_of=None):
        """The kernel dictionary (EP-12): reusable TERMS as records, resolved LATEST-UNDISPUTED-WINS —
        a FOLD, never a stored status. Per (entity_kind, term_key) the current entry is the LATEST
        dictionary_entry whose seq is NOT under an unresolved dispute; a dispute changes what the fold
        answers, and a later undisputed entry wins again. `entity_kind` filters (action/resource/actor);
        None = all. Keyed on the EXACT term (v1 — no normalisation primitive in the interpreter)."""
        disputed = self._disputed_entry_seqs(as_of)
        current = {}
        for e in self.store.by_action("DICT-ENTRY", as_of):     # by_action is seq order -> latest wins in place
            p = e.get("payload") or {}
            if p.get("kind") != "dictionary_entry":
                continue
            if entity_kind is not None and p.get("entity_kind") != entity_kind:
                continue
            if e["seq"] in disputed:
                continue                                        # disputed -> not the undisputed winner
            current[(p.get("entity_kind"), p.get("term_key"))] = {**p, "seq": e["seq"]}
        return current

    def disputed_terms(self, as_of=None):
        """Conflict routing (EP-12): terms whose CURRENT (latest) dictionary entry is under an
        unresolved dispute — routed to the owner queue as a VIEW that appends nothing (the EP-10 gauge
        precedent). The owner resolves by a later undisputed entry (latest-undisputed-wins) or a
        RESOLVE-DISPUTE. Same family as EP-11's comparison contradictions — described, not re-derived."""
        disputed = self._disputed_entry_seqs(as_of)
        latest = {}
        for e in self.store.by_action("DICT-ENTRY", as_of):
            p = e.get("payload") or {}
            if p.get("kind") == "dictionary_entry":
                latest[(p.get("entity_kind"), p.get("term_key"))] = e["seq"]
        return [{"entity_kind": ek, "term_key": tk} for (ek, tk), seq in latest.items() if seq in disputed]

    def _fold(self, name):
        """Resolve a bind name to its S-plane fold (mechanism; the master record chose the name).
        The `permissions` bind REBINDS to the four-dimensional grant fold this EP builds (design/31
        S4): the permission master now reflects the general grant world. The bind NAME is unchanged
        (the permission-master record keeps binding `permissions`), only the fold it resolves to —
        the GRANT-READ sight surface stays live as its own check (can_read), not as this master."""
        # The two per-act-path folds bound here read through their projections (EP-24C) and
        # stay UNMEMOISED, exactly as before: a master read returns a freshly folded value,
        # so `master()` cannot hand two callers the same object. Only the record source moved.
        return {"active_rules": lambda as_of=None: self.view_fold("active_rules", as_of=as_of),
                "actors": self._actors, "resources": self._resources,
                "permissions": self.grants, "relationships": self._relationships,
                "op_definitions": lambda as_of=None: self.view_fold("op_definitions", as_of=as_of),
                "view_definitions": self.view_definitions,
                # C6a VT-1: the three new S-plane OLD-band masters (design/25 v2.1 ruling 19). A
                # master may now bind the old band beside the active one; the closure at CREATE-VIEW
                # (boot.py) admits them since they are FOLD_NAMES members.
                "old_rules": self.old_rules, "old_items": self.old_items,
                "old_relationships": self.old_relationships,
                # C6a VT-3b (design/53 L14/L16): the two events-split bands as bound folds, so the
                # derive parents 1.1 / 1.2 SERVE their master read and their actor_class derives can
                # be narrowed (the SERVING of a bound master is VT-3b). Their own projections above.
                "rule_changing_acts": self.rule_changing_acts,
                "acts_under_rules": self.acts_under_rules}.get(name)

    def master(self, name, as_of=None):
        """Execute a MASTER view (design 28 §I4): resolve its `bind` against the fold library and run
        that fold — the one engine executing a record, no arrangement hardcoded. Returns the derived
        value with STALENESS metadata (`derived_at` = the store version it reflects). None if `name`
        is not a bound master."""
        d = self.view_definitions(as_of).get(name)
        if not d or not d.get("bind"):
            return None
        fold = self._fold(d["bind"])
        if fold is None:                                    # a bind outside the library (should be caught at
            return None                                     # creation) — no silent wrong answer
        return {"name": name, "bind": d["bind"], "value": fold(as_of),
                "derived_at": self._memo_gen if as_of is None else as_of,
                "refresh": d.get("refresh")}                # a mandated-refresh field (design 28 §6)

    # ---- the crossing surface (EP-23; design/36 K8/K9, design/34) ----------------------
    # THE IN-FLIGHT VIEW IS A DIFFERENCE BETWEEN RECORDS. Hand-outs minus answers minus
    # re-judges — no dict of open crossings, no future, no callback registry, because a
    # registry of what is in flight is exactly the stored status P2 forbids and it dies
    # with its process. Kill every one of these answers, replay from the record file, and
    # the same crossings come back suspended at the same point. Every method here is a PURE
    # READ that appends nothing (the EP-10 gauge precedent); the folds live in
    # kernel.crossing and are imported lazily, the way visible_category_packs imports
    # protection, so the fold module can read this one's view engine without a cycle.

    def crossings(self, as_of=None):
        """Every crossing with its state DERIVED: open | answered | superseded."""
        from . import crossing
        return crossing.crossings(self.store, as_of)

    def open_crossings(self, as_of=None):
        """What is suspended right now — the whole of "in flight"."""
        from . import crossing
        return crossing.open_crossings(self.store, as_of)

    def crossing_fingerprint(self, handout_seq, as_of=None):
        """Does the judged world still hold for one crossing? Answerable independently of
        any return attempt — which is what keeps staleness and authority two separately
        observable verdicts rather than one merged outcome (design/34 §2)."""
        from . import crossing
        return crossing.fingerprint(self.store, self, handout_seq, as_of)

    def stale_crossings(self, as_of=None):
        """Open crossings whose read-set has moved — computed from the world, never read
        off refusal records (a refusal proves someone tried; staleness is a fact about the
        world whether or not anyone tried)."""
        from . import crossing
        return crossing.stale_crossings(self.store, self, as_of)

    def crossings_needing_reask(self, as_of=None):
        """Stale crossings the machine may not retry: policy says abort, or the recorded
        retry budget is spent. The stale refusal stands and a human re-asks — never a silent
        execute, never a silent drop (design/34 §4)."""
        from . import crossing
        return crossing.needing_reask(self.store, self, as_of)

    def crossing_flutter(self, as_of=None):
        """Hot-read-set flutter per station (design/34 §4): repeated re-judges mean the pack
        is over-broad or the station belongs on a coarser view. SURFACED as a view — the
        response to flutter is to see it, never to weaken the check."""
        from . import crossing
        return crossing.flutter(self.store, as_of)

    # ---- the two-times surfaces (EP-26; design/35, design/36 K7/K10 §4b) --------------------
    # Every method here is a PURE READ that appends nothing, and every one is a fold over the
    # record: the session registry, the sweep's products, and both reconciliation views hold
    # nothing at all. Kill them, replay from the record file, and the same answers come back —
    # which is exactly what T-TOTAL-ROUNDTRIP-2 extended asserts. The folds live in
    # kernel.reconcile and are imported lazily, the way the crossing surfaces above do it, so
    # the fold module can read this view engine without a cycle.

    def sessions(self, as_of=None):
        """The session registry: every decider session with its DECLARED read-set, live or
        closed. A derived view, never a table — there is no session store and no cached login,
        because the record IS the session (the web-auth reference, refused at EP-15 and refused
        again here)."""
        from . import reconcile
        return reconcile.sessions(self.store, as_of)

    def live_sessions(self, as_of=None):
        """The contact points a law change would be delivered to. EP-27 makes the delivery; this
        EP records the contact points and their views and delivers nothing new."""
        from . import reconcile
        return reconcile.live_sessions(self.store, as_of)

    def session_read_set(self, session_id, as_of=None):
        """A session's declared read-set, RESOLVED AT USE. Stored as refs and resolved on
        reading, because a resolved copy would be a frozen derivative of a definition that can
        be amended underneath it."""
        from . import reconcile
        return reconcile.session_read_set(self.store, self, session_id, as_of)

    def overturns(self, as_of=None):
        """Every overturn on the record. The acts and their overturns are BOTH permanently
        here — an overturn is an appended decision, never an edit and never a disappearance."""
        from . import reconcile
        return reconcile.overturns(self.store, as_of)

    def standing(self, seq, as_of=None):
        """Does the recorded act at `seq` still stand? asOf BEFORE its overturn still answers
        True: order is untouched, validity is what changed, and two frames give two answers
        without contradicting each other."""
        from . import reconcile
        return reconcile.standing(self.store, seq, as_of)

    def re_ask(self, gate=None, as_of=None):
        """THE RE-ASK VIEW (§4b.4, RULED): refusals a late-arriving permissive law would now
        allow. NOTHING is appended for them — an overturn cannot perform an act that never
        happened, and a record claiming an effect that did not occur is the one forbidden lie.
        The remedy is re-submission at the current head, by the actor, through the ordinary
        door. Pass the gate to have each case RE-EVALUATED rather than merely surfaced."""
        from . import reconcile
        return reconcile.re_ask(self.store, self, gate, as_of)

    def pending_sweeps(self, gate, as_of=None):
        """Every sweep the record implies, RECOMPUTED — the refused ones included. A refused
        sweep appends nothing, so it is derived rather than read: the estate's own answer
        applied to itself, compute what you did not store. A reader holding the record can see
        which sweeps refused and which chain each would have ended."""
        from . import reconcile
        return reconcile.pending(gate, self.store, self, as_of)

    def exposure(self, as_of=None):
        """THE EXPOSURE VIEW (§4b.6, RULED): who consumed what, under which overturned act. The
        sweep reconciles STATE; what was already consumed is out of mechanical reach and the
        owner ruled that no stronger mechanical remedy is wanted. What the machine owes is this
        honest list, and the remedy is judgment on the deontic side."""
        from . import reconcile
        return reconcile.exposure(self.store, as_of)

    # ---- the lane surfaces (EP-27; design/35 §3, design/36 K10, wall primitive 8) ----------
    # The delivery schedule is a DERIVATION like every other view here: the channels, the
    # pending set, what the recorded budget shed, and what reached each live session are all
    # recomputed from the record alone. The on-append worker (kernel/push.py) accelerates
    # exactly this and holds no truth of its own, which is why killing it changes no answer.

    def lane_report(self, as_of=None):
        """THE WHOLE DELIVERY SCHEDULE, DERIVED. Channels, pending (delayed) items, shed items
        with the rule that shed them, per-session law deliveries, and dangling declarations.
        Deliveries APPEND NOTHING (the flood boundary), so every one of these is computed and
        none is stored — including the sheds, which is the EP-26 answer to a refused sweep
        applied to a dropped delivery: do not store what the policy did, compute it."""
        from . import push
        return push.derive(self.store, self, as_of)

    def queues(self, as_of=None):
        """The standing-push delivery queues, DERIVED from the record (design 28 §6): for every active
        move-to view definition, the records its trigger matched, grouped by channel (the move_to
        target). THIS IS THE SOURCE OF TRUTH — the on-append worker (kernel/push.py) keeps an in-memory
        acceleration of exactly this; kill that memory and this rebuilds the same queues from the record
        alone (the round-trip law applied to delivery). Deliveries APPEND NOTHING (doc-17 flood
        boundary): a queue is a view, never a stored list.

        [EP-27] The channels are now the channel half of `lane_report` rather than a second walk
        of the record: with a recorded budget in force, a queue derived WITHOUT the lane schedule
        would disagree with the worker the moment the budget bound, which is the EP-08B defect
        (an acceleration drifting from its derivation) arriving from the other side. One
        derivation, read two ways."""
        return self.lane_report(as_of)["channels"]

    # ---- C6 P16: paths and ceilings over flows (B19, B20; design/52) -----------------------
    # COMPUTED VIEWS over the record as it stands — no new row kind, no new field, no founding
    # (stop conditions (b)/(d) of the plan). What the record does NOT yet carry — the actor
    # classes' declared domain (K12), the boundary/reach axis values, the classify act that
    # computes a content class — lands with C6 P8; these views NAME those attributes and read
    # the one signal the record holds today (the `actor_class` free string), stating the rest as
    # the cap. That is exactly the shape the architect countersigned (board :3650, precisions 1-3):
    # the fold is real, its population arrives with P8, and A3 is re-driven then.

    #: The five path families — design/52 B19:68, L19:117 ("channels; sockets and tunnels; shared
    #: memory; custody handover; sight"). Held here as design/52's own closed vocabulary. It is NOT
    #: a second copy of P4's CLASSIFIER: P4 (tools/conformance/five_families_census.py) READS an op
    #: into a family and stays the instrument of record; `path_view` NAMES the family P4 read and
    #: only validates it against this list. A sixth entry is a paper change in design/52 (L19), which
    #: this view and P4 both then read — the single source of truth is the paper, not either tool.
    FIVE_FAMILIES = ("channels", "sockets-and-tunnels", "shared-memory", "custody-handover", "sight")
    #: not-a-path is P4's positive reading for an op that moves no bytes across a boundary; a path
    #: view may name it (the op opens no conduit), but sixth-way / unknown (P4's two reds) are NOT
    #: lawful paths and `path_view` refuses them.
    _PATH_FAMILY_SET = FIVE_FAMILIES + ("not-a-path",)
    #: The three axes an endpoint sits on — D08.56 F2 (design/52): PROCESSING (the human/AI/program
    #: cut, D08.49), BOUNDARY (glassboxed / border entity / external, design/43 §5), REACH (which
    #: path families and counterpart positions the endpoint may open). Today only PROCESSING has a
    #: record signal (the `actor_class` free string, K12); BOUNDARY and REACH are named-not-populated
    #: until P8's attest amendment and the vocabulary rule land. Nothing composes across frames — a
    #: ceiling reads any one axis, never a fold of two (design/52's anti-bleed rule, design/43).
    THREE_AXES = ("processing", "boundary", "reach")
    #: The two class tokens B20 folds occupancy into names for. `HUMAN_ACTOR_CLASS` already exists
    #: above (the succession law reads it); `AI_ACTOR_CLASS` is the AI token the record uses today.
    #: Both are read from the free-string `actor_class` field as it stands (K12: no declared domain
    #: until P8) — the cap A3's test states in words.
    AI_ACTOR_CLASS = "ai"
    PROGRAM_ACTOR_CLASS = "program"   # C6 P8 (B16): the third declared class, the arm of a structured rule only
    ORG_CLASSES = ("human-only", "AI-only", "mixed")

    def path_axis_positions(self, endpoint, as_of=None):
        """B19: an ENDPOINT's positions on the THREE AXES (design/52 D08.56 F2). Names all three;
        populates PROCESSING from the endpoint's `actor_class` as it stands today (the account
        surface), leaving BOUNDARY and REACH None — the record carries no signal for them until P8
        (K12). A view that named only the populated axis would hide that the other two are owed; a
        view that omitted them would read as if the endpoint had no boundary or reach, which is a
        stronger and false claim. So all three are named, two as the honest cap."""
        cls = (self.accounts(as_of).get(endpoint) or {}).get("actor_class") if endpoint is not None else None
        return {"processing": cls, "boundary": None, "reach": None}

    def path_view(self, op, family, permits=(), actor=None, target=None,
                  cited_rule=None, frame="content-class", as_of=None):
        """B19: an opened PATH read as a VIEW over the FIVE FAMILIES (design/52 B19; D08.51).

        A path is not the datum; it is the opened conduit, and governing it means naming — for the
        op that opens it — its FAMILY (P4's reading, passed in and validated here against design/52's
        closed vocabulary, never re-classified), its two ENDPOINTS, each endpoint's POSITIONS ON THE
        THREE AXES, the CONTENT BANDS it permits, and the RULE it cites. A CEILING (the permitted
        band set, B18's content-class ceiling — distinct from the numeric budget `ceiling` check)
        ATTACHES to the path, and along the path the content's class only TIGHTENS (`content_tightens_
        along`), a comparison read in ONE frame (`frame`; design/43's same-frame rule, the
        architect's precision 3) so two frames never read as one contradiction.

        `family` MUST be one of the five families or `not-a-path`; P4's two red readings (sixth-way,
        unknown) are not lawful paths and are refused here. `cited_rule` and the target endpoint are
        read from the op's own definition when not supplied, so the view is grounded in the record."""
        if family not in self._PATH_FAMILY_SET:
            raise ValueError(
                "%r is not a lawful path family — a path is a view over %s (or not-a-path); "
                "P4's sixth-way/unknown are census reds, not paths" % (family, ", ".join(self.FIVE_FAMILIES)))
        entry = self.op_definitions(as_of).get(op) or {}
        d = entry.get("definition", entry)
        if cited_rule is None:
            cited_rule = d.get("law_cited")
        if target is None:
            target = d.get("target_param")   # the target endpoint the op declares (a param today)
        source = actor if actor is not None else "$actor"   # the source endpoint is the engine's fact
        bands = frozenset(permits)
        return {
            "op": op,
            "family": family,
            "endpoints": {"source": source, "target": target},
            "axis_positions": {
                "source": self.path_axis_positions(actor, as_of),
                "target": self.path_axis_positions(target, as_of),
            },
            "content_bands": bands,     # the classes the path permits
            "cited_rule": cited_rule,
            "ceiling": bands,           # the content ceiling attached to the path (B18: only shrinks)
            "frame": frame,             # the one frame the tightening is read under (precision 3)
        }

    @staticmethod
    def content_tightens_along(bands_sequence, frame="content-class"):
        """B19/L19: along a path the content's class only TIGHTENS, never widens. `bands_sequence`
        is the ordered content-band SETS at successive positions on ONE path, read in ONE `frame`.
        Returns True iff each successive set is a subset (equal or narrower) of the one before it;
        a later position permitting a band an earlier one did not is a WIDENING and returns False —
        the planted-widening control A1 drives. Comparison is subset in a single frame; a caller
        mixing two frames is comparing incomparable verdicts (design/43's anti-bleed rule) and must
        not, which is why the frame is named on the path, not inferred here."""
        prev = None
        for step in bands_sequence:
            cur = frozenset(step)
            if prev is not None and not cur <= prev:
                return False
            prev = cur
        return True

    @staticmethod
    def compose_ceilings(*ceilings):
        """B18/L18: ceilings compose by INTERSECTION — a class adds a ceiling, never a power, so
        nesting can only TIGHTEN. Returns the intersection of the permitted-band sets; the empty
        composition permits everything (no ceiling), matching `_ceiling_check`'s 'no policy = None =
        unlimited'. This is the one operation on ceilings that is always safe under B18: it can only
        shrink the permitted set, never grow it."""
        sets = [frozenset(c) for c in ceilings]
        if not sets:
            return None   # no ceiling composed -> unbounded (the pre-ceiling reading, stated)
        out = sets[0]
        for s in sets[1:]:
            out = out & s
        return out

    @staticmethod
    def ceiling_widens(existing, proposed):
        """B18/L18: does `proposed` WIDEN what `existing` permits — permit a band `existing` did
        not? Returns True iff `proposed - existing` is non-empty. A ceiling only shrinks, so a
        widening proposal is refused (the refuse-to-loosen guard, A2's planted-widening control);
        a proposal that is equal or narrower widens nothing and returns False."""
        return bool(frozenset(proposed) - frozenset(existing))

    @staticmethod
    def held_within_envelopes(held, class_max, structural_max):
        """I21 (design/52 :93): HELD sits inside CLASS MAX and STRUCTURAL MAX at every moment.
        The three envelopes of B18 are views: CLASS MAX (the intersection of the class ceilings),
        STRUCTURAL MAX (what the structure/grants confer), HELD (what is actually held). Returns
        True iff HELD is a subset of BOTH; held outside either is the invariant refusing (I21's own
        red world). None for an envelope means unbounded (that side imposes no ceiling)."""
        h = frozenset(held)
        if class_max is not None and not h <= frozenset(class_max):
            return False
        if structural_max is not None and not h <= frozenset(structural_max):
            return False
        return True

    def org_occupants(self, org, as_of=None):
        """B20: the LIVE occupancy of an organisation — a fold over live membership rows, never a
        stored label. An org is a founded node (a space); its occupants are the accounts holding a
        LIVE grant at that node, read from `grants()` (revoke-superseded, so a revoked member drops
        out and the fold changes — the live-fold precedent compose.py's `system_key_bound` sets:
        a supersession fold over the record, never a flag). The wildcard grantee `*` (the founding-
        openness grant) is not an account and is skipped. Returns the frozenset of occupant account
        ids."""
        accounts = self.accounts(as_of)
        return frozenset(
            g["grantee"] for g in self.grants(as_of).values()
            if g.get("space") == org and g.get("grantee") in accounts)

    def org_class(self, org, as_of=None):
        """B20: an organisation's CLASS (human-only / AI-only / mixed) is a FOLD over live
        occupancy, never a declared or stored label (D08.49 'orgs are not declared a class').
        Each occupant's class is read from the `actor_class` field AS IT STANDS today (K12: no
        declared domain until P8's attest amendment and the vocabulary rule land — the cap A3
        states in words; the computed class by classify act arrives with P8 and A3 is re-driven
        then). Human-only iff every occupant is the human class, AI-only iff every occupant is the
        AI class, mixed otherwise (occupants span more than one class, or carry a class outside
        {human, AI}). None for an empty org (no live occupant to fold)."""
        classes = {(self.accounts(as_of).get(a) or {}).get("actor_class") for a in self.org_occupants(org, as_of)}
        if not classes:
            return None
        if classes == {self.HUMAN_ACTOR_CLASS}:
            return "human-only"
        if classes == {self.AI_ACTOR_CLASS}:
            return "AI-only"
        return "mixed"

    def mixed_org_countersign_ok(self, org, countersigners=(), as_of=None):
        """B20: a rule at rule level for a MIXED organisation may require a HUMAN OCCUPANT's
        countersign, and its absence REFUSES. Returns True iff the requirement is met: for a non-
        mixed org the rule does not bind (True); for a mixed org, True iff at least one of
        `countersigners` is a HUMAN occupant of the org (its class read from `actor_class` today).
        A mixed org with no human-occupant countersign returns False — the refusal A3 drives. The
        countersign identity is checked against LIVE occupancy, so a countersigner who is not (or no
        longer) a human occupant of this org does not satisfy it."""
        if self.org_class(org, as_of) != "mixed":
            return True
        occupants = self.org_occupants(org, as_of)
        accounts = self.accounts(as_of)
        return any(
            c in occupants and (accounts.get(c) or {}).get("actor_class") == self.HUMAN_ACTOR_CLASS
            for c in countersigners)

    # ---- C6 P8: ACTOR CLASSES AS BANDS, THE (CLASS, CELL) PAIRING, THE DRY-RUN CENSUS ----------
    # B16 (classes as bands over two declared capabilities), B17 (classify is attest generalised — a
    # class is the LATEST LIVE classify act, computed AT READ), B18/I21 (a class is a ceiling that
    # only shrinks), L28 (the cell per operation; the required capability read OFF the cell; the
    # pairing through the existing ceiling machinery). ENFORCEMENT OF THE PAIRING IS LIVE (P8b, board
    # :3731; supersedes the HELD state of archi precision 2 / :3688): gate._pairing_step refuses a
    # governed act by a DECLARED-class actor whose class lacks the arm the op's cell requires. Everything
    # in THIS class is the READ-SIDE derivation that live door reads (pair / class_band /
    # class_capabilities / required_capability) plus the DRY-RUN CENSUS (pairing_census, which still only
    # REPORTS and refuses no act). admitted_level and the band are DERIVED AT READ, NEVER stored (I10; stop (d)).

    CELL_SET = ("S", "U", "U{s}", "S{u}")
    STRUCTURED_ARM = "structured-arm"
    UNSTRUCTURED_ARM = "unstructured-arm"
    #: The recorder's own SYSTEM (the founding runtime / SYSTEM) — OUTSIDE the pairing (L28; archi
    #: precision 3: the recorder's own mechanics, form-fill/validate/route, are not a judge's step).
    #: The census excludes their acts and counts them separately; the door checks the ACTING actor.
    RECORDER_SYSTEM_ACTORS = ("PC_RUNTIME", "SYSTEM")

    def class_capabilities(self, as_of=None):
        """B16: the {class: (arms...)} map, FOUNDING DATA read from the latest `actor-classes`
        category_pack record's `capabilities` (never hardcoded — re-cutting the classes is an
        AMEND-PACK, not a code change). Latest-wins by record order. Empty for a world before P8 (no
        such pack) or one whose latest actor-classes record carries no capabilities map.

        HEAD-MEMOISED ON THE category_packs SUBSET GENERATION (archi Resolution A, board :3735):
        `_class_capabilities` folds the map through the category_packs record projection (a SUBSET of the
        record, not the whole of it), and the memo is keyed on the SAME generation category_packs() rides
        — so the map re-folds ONLY when a category_pack record is appended (a governance-rate amendment),
        never on an ordinary governed act, and the LIVE (class, cell) pairing's per-act read no longer
        walks store.all(). category_packs() itself is UNTOUCHED (its projection gains no capabilities key
        — Resolution A's load-bearing point, the campaign-1 oracle test_ep16). It is DELIBERATELY NOT a
        PER_ACT_FOLDS member: that family is OBSERVED being called during an act, but this read fires at
        the PRE-WRITE gate chokepoint (before the act's own append) and so is always cache-served and
        invisible to test_ep24c's per-act observer — riding the subset generation gives the identical
        invalidation without a false 'declared-but-unobserved fold'. A regression to a raw store.all()
        walk would still surface in that observer as an undeclared whole-record read. The record-walk
        oracle below is the standing equivalence baseline (EP-24B one-implementation-two-sources idiom)."""
        proj = self.store.record_projection("category_packs")
        if as_of is not None:
            return self._class_capabilities(as_of, proj)          # a historical view is never head
        key = "class_capabilities:%d" % self._subset_gens.get("category_packs", 0)
        if key in self._memo:
            return self._memo[key]
        v = self._class_capabilities(None, proj)
        for stale in [k for k in self._memo if k.startswith("class_capabilities:")]:
            del self._memo[stale]
        self._memo[key] = v
        return v

    def _class_capabilities(self, as_of=None, source=None):
        # THE FOLD: the {class: (arms...)} map, latest actor-classes record with a VALID capabilities
        # Mapping wins. A levels-only AMEND-PACK carries no capabilities map (its op strips to
        # name/levels), so it is SKIPPED and the last valid map carries forward — the founding map
        # persists across a levels re-cut. Reads through `source` (the category_packs projection when
        # accelerated); identical to the whole-record walk because the projection holds every pack record.
        caps = {}
        for e in (source or self.store).all(as_of):
            p = e.get("payload") or {}
            cap = p.get("capabilities")
            if p.get("kind") == "category_pack" and p.get("name") == "actor-classes" \
                    and isinstance(cap, Mapping):   # the store freezes payload dicts to mappingproxy
                caps = {k: tuple(v) for k, v in cap.items()}   # latest-valid-caps wins == carry-forward
        return caps

    def _class_capabilities_record_walk(self, as_of=None):
        """RETAINED ORACLE (archi Resolution A; EP-24B differential idiom): the pre-memoisation
        whole-record walk over store.all(), kept so the memoised projection read has a standing
        equal-answers baseline. `class_capabilities` reads the memoised fold; this reads the raw record."""
        caps = {}
        for e in self.store.all(as_of):
            p = e.get("payload") or {}
            cap = p.get("capabilities")
            if p.get("kind") == "category_pack" and p.get("name") == "actor-classes" \
                    and isinstance(cap, Mapping):   # the store freezes payload dicts to mappingproxy
                caps = {k: tuple(v) for k, v in cap.items()}   # latest-valid-caps wins
        return caps

    def class_domain(self, as_of=None):
        """K12: the CLOSED actor-class domain — the declared class list, read from the actor-classes
        pack `levels` (the one home; latest-wins via category_packs). A class NOT in it is not a
        valid band, which is the domain closing at read."""
        pack = self.category_packs(as_of).get("actor-classes")
        return tuple(pack["levels"]) if pack else ()

    def latest_classify(self, subject, as_of=None):
        """B17 CLASSIFY IS ATTEST GENERALISED — the LATEST LIVE classify act on `subject`, computed
        AT READ (never a stored band). A classify act is the amended VERIFY-ACCOUNT (account =
        the subject) carrying a `target` (the band it assigns) and an `evidence_kind`; latest-by-seq
        wins, so re-classifying changes the answer AT READ with nothing stored. Returns the payload
        of the latest classify act on `subject`, or None (no classify act names it)."""
        latest, latest_seq = None, -1
        for e in self.store.by_action("VERIFY-ACCOUNT", as_of):
            p = e.get("payload") or {}
            if p.get("account") == subject and p.get("target") is not None \
                    and e.get("seq", -1) > latest_seq:
                latest, latest_seq = p, e.get("seq", -1)
        return latest

    def class_band(self, actor, as_of=None):
        """The actor's BAND for the pairing (B16/B17), computed AT READ and never stored: the band
        assigned by the LATEST LIVE classify act on the actor (the amended VERIFY-ACCOUNT's `target`),
        falling back to the actor's `actor_class` field when no classify act names it. VALIDATED
        against the closed domain (K12): a band outside the declared class list is not valid and
        returns None (a class not in the list cannot be validly classified — the domain closes)."""
        domain = self.class_domain(as_of)
        classify = self.latest_classify(actor, as_of)
        band = classify.get("target") if classify else \
            (self.accounts(as_of).get(actor) or {}).get("actor_class")
        return band if band in domain else None

    @classmethod
    def required_capability(cls, cell):
        """L28: the capability a task's CELL requires, READ OFF THE CELL with no table — the arm of
        an UNSTRUCTURED rule if ANY side has judgment (a cell other than S), else the arm of a
        STRUCTURED rule. Returns None for a cell outside the closed set, so no capability is silently
        met by an unrecognised cell (the op-META door keeps a declared cell well-formed)."""
        if cell == "S":
            return cls.STRUCTURED_ARM
        if cell in cls.CELL_SET:
            return cls.UNSTRUCTURED_ARM
        return None

    def pair(self, actor_class, cell, as_of=None):
        """L28: the (actor class, task cell) PAIRING through the capability declarations. Returns
        (admit: bool, reason). ADMIT iff the actor's class holds the capability the cell requires: a
        PROGRAM at any judgment cell is refused (it holds no unstructured arm), an AI at a pure-S cell
        is refused (it holds no structured arm — an AI is not its arm), a HUMAN holds any. An
        actor_class outside the declared domain, or an unrecognised cell, REFUSES fail-closed —
        nothing is admitted by an unknown class or an unrecognised cell, and no cell is defaulted."""
        need = self.required_capability(cell)
        if need is None:
            return False, "cell %r is not one of %s" % (cell, ", ".join(self.CELL_SET))
        held = self.class_capabilities(as_of).get(actor_class)
        if held is None:
            return False, "actor class %r is not a declared class (the domain is closed: %s)" \
                          % (actor_class, ", ".join(self.class_domain(as_of)) or "none")
        if need not in held:
            return False, "class %r may not be the arm of cell %r: it holds {%s} but the cell needs %s" \
                          % (actor_class, cell, ", ".join(held) or "no capability", need)
        return True, "class %r holds %s, admitted at cell %r" % (actor_class, need, cell)

    def op_replays_to_identity(self, op_name, as_of=None):
        """L28 THE DECLARED-S GUARD: a declared-STRUCTURED operation must REPLAY TO IDENTITY (the
        estate's founding property — kill the registry, replay, identical) or satisfy a predicate,
        or its declaration is a FINDING. A AWIG OS op replays to identity iff its record is a pure
        function of its inputs; the estate's own guard for that is the FOUNDING ROUNDTRIP (a rebuild
        adds nothing, test_ep14). Here the read-side finding is DECLARATIONAL: an op declared S whose
        definition marks it non-replayable (`replays_to_identity: false`, an author's own honest flag)
        is a finding. Absent the flag, a declared-S op is taken to replay (the estate's default and
        its founding property); a declared-JUDGMENT op is exempt (never scored by the machine)."""
        defn = (self.op_definitions(as_of).get(op_name) or {}).get("definition") or {}
        if defn.get("cell") != "S":
            return True   # a judgment op is validated to its schema and NEVER scored (L28)
        return defn.get("replays_to_identity", True) is not False

    def declared_s_findings(self, as_of=None):
        """L28: the declared-S operations whose declaration is a FINDING — a declared-S op that does
        NOT replay to identity (nor satisfy a predicate). Returns the op names by name. Empty on the
        real founding (every AWIG OS op is a structured record-mechanic that replays); a planted
        declared-S op flagged `replays_to_identity: false` reds it (the finding A3c drives)."""
        return [n for n, entry in self.op_definitions(as_of).items()
                if (entry.get("definition") or {}).get("cell") == "S"
                and not self.op_replays_to_identity(n, as_of)]

    def pairing_census(self, pack_version=None, as_of=None):
        """L28 / P8 THE DRY-RUN CENSUS (archi precision 2): over the WHOLE RECORD, every act the
        (actor class, task cell) pairing WOULD refuse, published WITH ITS WORLD (the founding version
        and the as-of head). ENFORCEMENT IS HELD — this REPORTS, it refuses NO act; turning the door
        on is the owner's call after reading it. EXCLUDED, counted separately: the recorder's own
        SYSTEM acts (RECORDER_SYSTEM_ACTORS — the founding runtime; archi precision 3), and acts whose
        action is not a declared op (a founding primitive / bootstrap append — not a pairing subject).
        For every remaining act the op's declared CELL and the actor's BAND are read and paired; a
        refusal is recorded BY NAME with its world (seq, actor, op, cell, class, reason)."""
        defs = self.op_definitions(as_of)
        head = len(self.store.all(as_of))
        would_refuse = []
        recorder_system = non_op = considered = ops_no_cell = none_band = 0
        for e in self.store.all(as_of):
            actor, action = e.get("actor"), e.get("action")
            if actor in self.RECORDER_SYSTEM_ACTORS:
                recorder_system += 1
                continue
            entry = defs.get(action)
            if entry is None:
                non_op += 1
                continue
            cell = (entry.get("definition") or {}).get("cell")
            if cell not in self.CELL_SET:
                ops_no_cell += 1     # an op with no well-formed cell — never defaulted to S (L28)
            band = self.class_band(actor, as_of)
            if band is None:                 # C6 P8b (archi :3726): the None-band population, REPORTED
                none_band += 1               # beside the other counts (visible, not hidden). The live door
                                             # ADMITS a None band; this count is what that admission covers.
            considered += 1
            admit, reason = self.pair(band, cell, as_of)
            if not admit:
                would_refuse.append({"seq": e.get("seq"), "actor": actor, "action": action,
                                     "cell": cell, "class": band, "reason": reason})
        return {
            "world": {"founding_version": pack_version, "as_of_head": head},
            "counts": {"total_acts": head, "recorder_system_excluded": recorder_system,
                       "non_op_acts_excluded": non_op, "considered": considered,
                       "would_refuse": len(would_refuse), "ops_without_wellformed_cell": ops_no_cell,
                       "none_band_considered": none_band},
            "would_refuse": would_refuse,
            "enforcement": "HELD — dry-run census only; NO act was refused (archi precision 2, L25 C6 measures only)",
        }

    # ---- C6 P7: THE HANDSHAKE RELATION over crossings (B1, I4; design/52 v2.0) --------------
    # A COMPUTED VIEW over the record as it stands — NO new row kind, NO new field, NO founding
    # (Reading A, the owner's confirmation :3658; stop conditions (b)/(d) discharged at build). A
    # child and its parent are two bodies IN A LIVE, WITHDRAWABLE HANDSHAKE RELATION, recorded over
    # the EXISTING crossing/receipt vocabulary (kernel.border, READ and reused, never re-authored):
    #   • the child's DECLARE = a BORDER-SUBMIT whose draft names the parent's body-name (key,
    #     genesis, D08.42); the crossing's CONTENT HASH (border.content_id) is the relation's id;
    #   • the mutual half = the counterpart's RECEIPT of that crossing (border.record_receipt), the
    #     counterpart's half landing in each record as INPUT, each by its own pen (one pen per
    #     record, I1) — the received-back receipt gets ONE receipt and NO loop (RECEIPT idempotence);
    #   • a WITHDRAW = a later BORDER-SUBMIT whose draft cites the relation's content hash.
    # This view folds a body's OWN declare/withdraw crossings to the current relation state, NEVER
    # the peer's record (the architect's precision 1). The relation's KIND is the crossing's
    # under_rule (its rule_cited — precision 2); the owner's Q5 relation tag (HR / NT / SY) is
    # ABSENT — not defaulted — until he gives it (read as None here; Q5:182, no tag invented). The
    # DECLARE and WITHDRAW rows both STAND — no delete; the live view reads the current state from
    # them (precision 3). Recognition is by self-declaration in the draft (the active_rules rule_id
    # precedent), so no schema field is added: the marker rides the entity's own free-form draft.

    #: The draft marker a handshake-relation crossing carries (recognition by self-declaration; the
    #: active_rules `rule_id` precedent, applied to the crossing draft — no new record field).
    HANDSHAKE_RELATION_MARKER = "handshake_relation"

    def _handshake_marker(self, submit_record):
        """The `handshake_relation` block in a BORDER-SUBMIT's own draft, or None. Read from THIS
        body's stored crossing row; a submit carrying no such marker is an ordinary crossing and is
        not a relation act (the recognition rule, one predicate)."""
        draft = (submit_record.get("payload") or {}).get("draft")
        if not isinstance(draft, Mapping):
            return None
        hs = draft.get(self.HANDSHAKE_RELATION_MARKER)
        return hs if isinstance(hs, Mapping) else None

    def handshake_relations(self, as_of=None):
        """B1 / I4 — THE LIVE-RELATION VIEW (design/52 v2.0): every handshake relation THIS body
        DECLARED, keyed by the declare crossing's content hash (the relation id), with its state
        DERIVED `live` | `withdrawn`. Folded from this body's OWN declare/withdraw crossings alone
        (precision 1: never the peer's record) — kill it, replay, identical (a fold, never a stored
        status, P2). Each entry carries the parent's body-name (key, genesis), the declarer, the
        relation's KIND = the declare crossing's `under_rule` (its rule_cited — precision 2), the
        owner's Q5 `tag` read from the row (None/ABSENT until he gives it — no tag invented), and
        the declare/withdraw seqs (both rows STAND — no delete, precision 3). A relation never
        declared is ABSENT from the result; a withdrawn one reads `withdrawn`."""
        from . import border
        out = {}
        for e in self.store.by_action(border.SUBMIT_OP, as_of):
            hs = self._handshake_marker(e)
            if hs is not None and hs.get("parent") is not None:      # a DECLARE (names a parent)
                cid = border.content_id(e)
                out[cid] = {"relation_id": cid, "parent": hs.get("parent"),
                            "declared_by": e.get("actor"), "under_rule": e.get("rule_cited"),
                            "tag": hs.get("tag"),                    # Q5 tag: ABSENT (None) until the owner gives it
                            "state": "live", "declare_seq": e.get("seq"), "withdraw_seq": None}
        for e in self.store.by_action(border.SUBMIT_OP, as_of):
            hs = self._handshake_marker(e)
            if hs is not None:                                       # a WITHDRAW cites the relation's content hash
                cited = hs.get("withdraws")
                if cited in out and out[cited]["state"] == "live":
                    out[cited]["state"] = "withdrawn"
                    out[cited]["withdraw_seq"] = e.get("seq")
        return out

    def handshake_relation_live(self, relation_id, as_of=None):
        """Is the handshake relation `relation_id` currently LIVE in THIS body's record? DERIVED
        from the body's own declare/withdraw crossings (precision 1) — a relation never declared, or
        one withdrawn, returns False; never a stored boolean. The one-line live read the tree's
        "in a live handshake relation" wording (P10's re-mint) reads."""
        r = self.handshake_relations(as_of).get(relation_id)
        return r is not None and r["state"] == "live"

    # ---- C6 P6: THE LIVE-STAGES VIEW AND THE HANDSHAKE CHECK (B8, I8, I16; design/52 v2.0) ------
    # A COMPUTED VIEW over the record as it stands, plus module-level handshake checks below — NO
    # founding, NO new op/law/check kind, NO pack edit, NO new row field (L26; Q2 discharged, :3658;
    # I9). What a machine HOLDS (its stages, per scope) is DERIVED from its LIVE rules, never a
    # founding declaration (B8, L26 — the owner's "only need to know if rule exist or not, active or
    # not"). A stage-holding is a LIVE rule (an `active_rules` entry, READ and reused — latest-wins
    # liveness, so a superseded/withdrawn rule drops out) that SELF-DECLARES it on the EXISTING
    # accepted CREATE-RULE params — recognition by self-declaration, the `active_rules` `rule_id`
    # precedent and P7's handshake marker, applied without adding a row field (I9) or a founding
    # param (Q2): `policy_key` is the marker, `value` the stage, `scope` the scope, and the HOLDER
    # (the actor the constitution assigns the stage to — I16's "an actor holds a stage") rides the
    # existing `text` string param. The machine holds a stage only where it has acted (minted such a
    # rule); a machine that has not acted holds nothing (B8). Each machine folds its OWN record
    # alone (one pen per record, I1); the handshake check compares two machines' PRESENTATIONS,
    # never folding two records as one truth (I2 — the checks are module-level functions over
    # already-computed presentations, the P4/P15 census idiom, not a rule the record checks about
    # itself).

    #: The self-declared marker a stage-holding rule carries in its own `policy_key` (recognition by
    #: self-declaration; an EXISTING accepted CREATE-RULE param, no new row field — I9, no founding
    #: param — Q2). A live rule whose `policy_key` equals this holds `value` (the stage) for `scope`,
    #: with the HOLDER actor on `text`.
    HELD_STAGE_KEY = "held_stage"

    def held_stages(self, as_of=None):
        """B8 / I8 / L26 — THE LIVE-STAGES VIEW: what stages THIS machine holds, per scope, COMPUTED
        from its LIVE rules (`active_rules`, READ and reused), never a founding declaration. A
        stage-holding is a live rule self-declaring `HELD_STAGE_KEY` in its own `policy_key`: `value`
        is the stage, `scope` the scope, and the HOLDER (I16's actor) rides the existing `text`
        param. The machine holds a stage only where it acted (a claim is an act — a machine that has
        not acted holds nothing, B8). A stage held under a live rule appears; one whose rule is
        ABSENT (never created) or WITHDRAWN (superseded so the latest version of its rule_id no
        longer declares the marker) does NOT (A1). Folded over THIS record's rows alone (one pen per
        record, I1); kill it, replay, identical (a fold, never a stored status, P2). Returns a list
        of {actor, stage, scope, rule_id, seq} — `actor` the HOLDER the rule assigns the stage to."""
        live = self.active_rules(as_of)                          # reuse the view fold: latest-wins liveness
        out = []
        for e in self.store.by_action("CREATE-RULE", as_of):
            p = e.get("payload") or {}
            rid = p.get("rule_id")
            if p.get("policy_key") != self.HELD_STAGE_KEY:       # a self-declared stage-holding only
                continue
            if rid is None or rid not in live or live[rid].get("seq") != e.get("seq"):
                continue                                         # absent / superseded / withdrawn -> not live
            out.append({"actor": p.get("text"), "stage": p.get("value"),
                        "scope": p.get("scope"), "rule_id": rid, "seq": e.get("seq")})
        return out

    def held_stage_scopes(self, as_of=None):
        """The set of (stage, scope) pairs THIS machine holds — the PRESENTATION a machine brings TO
        a handshake. The one-machine-per-stage-per-scope check (I8) runs over BOTH machines'
        presentations; each is folded by its own machine over its OWN record (I1), and the module-
        level check compares the two (I2: two records are never folded as one truth)."""
        return {(h["stage"], h["scope"]) for h in self.held_stages(as_of)}

    # ---- C6a VT-1: THE NEW FOLDS (design/25 v2.1; design/53 B3/B4; the view tree beside the active) --
    # COMPUTED VIEWS over the append-only record, added BESIDE the existing folds — NO founding, NO
    # new op/law/check kind, NO new field, NO pack edit (VT-1 is GREEN). Every OLD band is a
    # latest-wins VIEW: nothing is erased (the record is append-only; ruling 19). Each new fold is
    # its OWN memoised projection through the existing head-memo (I7 / the delta-1 Resolution A
    # principle, board :3735) — its own memo key, NEVER a key added onto an existing projection (the
    # P8b lesson: the campaign-1 oracle test_ep16 and category_packs stay byte-identical). Three of
    # these are new S-plane MASTERS (old_rules/old_items/old_relationships, in FOLD_NAMES + _fold);
    # events_by_effect is a level-2 split that is not bindable (I1, ruling 11) and the level-4 views
    # compute in memory (ruling 10), so they are methods, not library members.

    def old_rules(self, as_of=None):
        """design/25 v2.1 node 2.2 / rulings 3 & 19 / B3 — OLD RULES: the rule versions the active
        fold DROPPED by latest-wins, never erased. A rule record is OLD iff its rule_id's ACTIVE
        (latest-wins, tier-aware) version is a DIFFERENT record — so active_rules and old_rules
        PARTITION the rule population (B3). Recognition is by SELF-DECLARATION (payload.rule_id — the
        act wrote to the law), NEVER by op name (the active_rules recognition rule, read for its
        complement). A separate memoised projection (I7). Kill it, replay, identical (P2)."""
        return self.cached("old_rules", as_of, lambda: self._old_rules(as_of))

    def _old_rules(self, as_of=None):
        active = self.active_rules(as_of)              # latest-wins, READ and reused — the active band
        old = []
        for e in self.store.all(as_of):
            p = e.get("payload") or {}
            rid = p.get("rule_id")
            if rid is None:
                continue                               # not a rule record (recognition by self-declaration)
            cur = active.get(rid)
            if cur is not None and e["seq"] != cur["seq"]:
                old.append({**p, "seq": e["seq"]})     # a superseded version — dropped by latest-wins, not erased
        return old

    def old_items(self, as_of=None):
        """design/25 v2.1 node 3.2 / ruling 19 / B4 — OLD ITEMS: previous versions and removed items,
        the latest-wins COMPLEMENT of the active item view, nothing erased. Items are the actor and
        resource masters (ruling 1): an item is OLD iff a LATER record of its kind superseded its
        identity (actor_id for actors, object for resources). Each master READ and reused. CAP
        (design/25 §caps; the _resources honest-cap precedent): static kinds without a live latest-
        wins fold today (spaces/keys/tunnels/devices as items) fold in as those masters become rows
        (VT-3); the fold is ready. A separate memoised projection (I7)."""
        return self.cached("old_items", as_of, lambda: self._old_items(as_of))

    def _old_items(self, as_of=None):
        out = []
        # old actors: the non-latest CREATE-ACTOR versions per actor_id
        latest, hist = {}, {}
        for e in self.store.by_action("CREATE-ACTOR", as_of):
            aid = (e.get("payload") or {}).get("actor_id") or e.get("object")
            hist.setdefault(aid, []).append(e)
            latest[aid] = e["seq"]
        for aid, evs in hist.items():
            for e in evs:
                if e["seq"] != latest[aid]:
                    out.append({"kind": "actor", "id": aid, "seq": e["seq"]})
        # old resources: the non-latest CREATE-INFO versions per object
        latest, hist = {}, {}
        for e in self.store.by_action("CREATE-INFO", as_of):
            obj = e.get("object")
            hist.setdefault(obj, []).append(e)
            latest[obj] = e["seq"]
        for obj, evs in hist.items():
            for e in evs:
                if e["seq"] != latest[obj]:
                    out.append({"kind": "resource", "id": obj, "seq": e["seq"]})
        return out

    def old_relationships(self, as_of=None):
        """design/25 v2.1 node 4.2 / ruling 19 / B4 — OLD RELATIONSHIPS: ended, withdrawn, or
        superseded by a LATER version of the same relation — the latest-wins COMPLEMENT, nothing
        erased. Identity is SELF-DECLARED (payload `rel_id`, else (from, to, rel_kind)); an
        end/withdraw is a self-declared marker on the EXISTING free-form payload (`ended` / `state` —
        the P7 handshake & active_rules `rule_id` precedent: NO new row field, I9). The relation op
        is named-pending today (_relationships); the fold is READY and reads what the record carries
        — VT-2 makes the op live. A separate memoised projection (I7)."""
        return self.cached("old_relationships", as_of, lambda: self._old_relationships(as_of))

    def _old_relationships(self, as_of=None):
        rows = list(self.store.by_action("CREATE-RELATIONSHIP", as_of))

        def identity(e):
            p = e.get("payload") or {}
            return p.get("rel_id") if p.get("rel_id") is not None \
                else (p.get("from"), p.get("to"), p.get("rel_kind"))

        latest = {}
        for e in rows:
            latest[identity(e)] = e["seq"]              # by seq order — last wins
        old = []
        for e in rows:
            p = e.get("payload") or {}
            is_latest = e["seq"] == latest[identity(e)]
            ended = p.get("ended") is True or p.get("state") in ("ended", "withdrawn")
            if not is_latest:
                old.append({"from": p.get("from"), "to": p.get("to"), "rel_kind": p.get("rel_kind"),
                            "rel_id": p.get("rel_id"), "state": "superseded", "seq": e["seq"]})
            elif ended:
                old.append({"from": p.get("from"), "to": p.get("to"), "rel_kind": p.get("rel_kind"),
                            "rel_id": p.get("rel_id"), "state": "withdrawn", "seq": e["seq"]})
        return old

    def events_by_effect(self, as_of=None):
        """design/25 v2.1 node 1 (§1.1 / §1.2) / ruling 2 / L2 — the LEVEL-2 split of EVENTS by the
        row's EFFECT FIELD: an act that created / amended / superseded / withdrew a RULE is a
        RULE-CHANGING ACT; every other happening is an ACT UNDER RULES. The effect is read from the
        row's SELF-DECLARATION (payload.rule_id — the act wrote to the law), NEVER inferred from the
        operation name (the active_rules recognition rule: "not a hard-coded action-name list"). The
        split is PERMANENT. EVENTS DO NOT SPLIT ACTIVE/OLD — a happening is never old (ruling 19):
        this fold names NO old band and every event lands in EXACTLY ONE of the two. A separate
        memoised projection (I7)."""
        return self.cached("events_by_effect", as_of, lambda: self._events_by_effect(as_of))

    def _events_by_effect(self, as_of=None):
        rule_changing, under_rules = [], []
        for e in self.store.all(as_of):
            p = e.get("payload") or {}
            row = {"seq": e["seq"], "actor": e.get("actor"), "action": e.get("action")}
            (rule_changing if p.get("rule_id") is not None else under_rules).append(row)
        return {"rule_changing_acts": rule_changing, "acts_under_rules": under_rules}

    def rule_changing_acts(self, as_of=None):
        """C6a VT-3b (design/53 L14/L16, I7): the events-split RULE-CHANGING band as ITS OWN
        projection — the bound fold behind seed node 1.1, so master("1.1") serves and a derive over
        it (1.1.x, actor_class) can be narrowed. Reads the memoised events_by_effect band; it does
        NOT reshape it (VT-3 A6 holds: events_by_effect still returns its two keys)."""
        return self.events_by_effect(as_of)["rule_changing_acts"]

    def acts_under_rules(self, as_of=None):
        """C6a VT-3b (design/53 L14/L16, I7): the events-split ACTS-UNDER-RULES band as its own
        projection — the bound fold behind seed node 1.2, so master("1.2") serves and a derive over
        it (1.2.x, actor_class) can be narrowed. Reads the memoised events_by_effect band without
        reshaping it (VT-3 A6 holds)."""
        return self.events_by_effect(as_of)["acts_under_rules"]

    def chains_of_effect(self, as_of=None):
        """design/25 v2.1 ruling 8 — CHAINS OF EFFECT: paths computed over the record's OWN causation
        (level 4, computed — ruling 10). The record's native causal refs are the crossing lineage
        (kernel.crossing): a crossing-answer CITES its handout (handout_seq); a re-judge / sub-crossing
        NAMES its parent (parent_handout_seq). This walks those cause->effect edges into maximal
        chains. A fold: kill it, replay, identical (P2). CAP (path_axis_positions precedent): the
        causation read is the crossing lineage the record carries today; a rule change causing the
        acts under it is named by events_by_effect + the seeded tree (VT-3), not here. A separate
        memoised projection (I7); the head-memo is in-memory (ruling-10 compatible)."""
        return self.cached("chains_of_effect", as_of, lambda: self._chains_of_effect(as_of))

    def _chains_of_effect(self, as_of=None):
        from . import crossing
        succ, has_pred = {}, set()
        for e in self.store.all(as_of):
            p = e.get("payload") or {}
            k = p.get("kind")
            cause = p.get("handout_seq") if k == crossing.ANSWER_KIND else \
                (p.get("parent_handout_seq") if k == crossing.HANDOUT_KIND else None)
            if cause is not None:
                succ.setdefault(cause, []).append(e["seq"])
                has_pred.add(e["seq"])
        chains = []

        def walk(node, path):
            nxt = succ.get(node)
            if not nxt:
                chains.append(path)
                return
            for n in sorted(nxt):
                walk(n, path + [n])

        for root in sorted(c for c in succ if c not in has_pred):
            walk(root, [root])
        return chains

    #: design/25 v2.1 node 3.1.2 — the static item kinds (content, spaces, keys, tunnels, devices).
    STATIC_KINDS = ("content", "spaces", "keys", "tunnels", "devices")
    #: design/25 §caps — a static kind's CELL, DERIVED from its creating operation (blobs U-involved;
    #: keys/spaces/tunnels/devices S), never a new field.
    STATIC_KIND_CELL = {"content": "U-involved", "spaces": "S", "keys": "S",
                        "tunnels": "S", "devices": "S"}

    def static_composite(self, as_of=None):
        """design/25 v2.1 node 3.1.2 / ruling 21 — the STATIC composite over the record: content,
        spaces, keys, tunnels, devices. Populated from the LIVE reads (content via _resources, spaces
        via the space fold); kinds whose master is not a live fold today are NAMED but empty (the
        path_axis_positions honest-cap: name all, populate what the record carries) — VT-3 seeds
        them. A separate memoised projection (I7)."""
        return self.cached("static_composite", as_of, lambda: self._static_composite(as_of))

    def _static_composite(self, as_of=None):
        return {"content": self._resources(as_of), "spaces": self.spaces(as_of),
                "keys": {}, "tunnels": {}, "devices": {}}   # CAP: keys/tunnels/devices masters mature in VT-3

    def actors_by_class(self, as_of=None):
        """design/25 v2.1 node 3.1.1 level 4 / ruling 21 — the ACTORS-BY-CLASS filter (a level-4
        filter, read per act, not a permanent node). Groups the actor master by actor_class (read off
        the actor row). An actor with NO class is counted under the None key (B4: "an actor with no
        class counted and named"), never dropped. A separate memoised projection (I7)."""
        return self.cached("actors_by_class", as_of, lambda: self._actors_by_class(as_of))

    def _actors_by_class(self, as_of=None):
        by = {}
        for aid, a in self._actors(as_of).items():
            by.setdefault(a.get("actor_class"), []).append(aid)
        return by

    def static_by_kind(self, as_of=None):
        """design/25 v2.1 node 3.1.2 level 4 / ruling 21 — STATIC-BY-KIND (a level-4 filter): the
        static composite indexed by kind (the ids per static kind). A FILTER over static_composite,
        never a new node. A separate memoised projection (I7)."""
        return self.cached("static_by_kind", as_of, lambda: self._static_by_kind(as_of))

    def _static_by_kind(self, as_of=None):
        return {kind: sorted(v.keys()) for kind, v in self.static_composite(as_of).items()}

    def static_by_cell(self, cell=None, as_of=None):
        """design/25 v2.1 node 3.1.2.5 / ruling 21 / design/25 §caps — the BY-CELL filter over static
        items (a level-4 FILTER, not a node). A static item's cell is DERIVED from its kind's creating
        operation as design/25 states — content (blobs) U-involved; spaces, keys, tunnels, devices S
        — NEVER a new field. `cell` filters to one band (its kinds); None returns {cell: [kinds]}.
        Not memoised: it takes a `cell` arg (the head-memo keys on name only) and is a constant-time
        derivation over the closed kind set."""
        bands = {}
        for kind in self.STATIC_KINDS:
            bands.setdefault(self.STATIC_KIND_CELL[kind], []).append(kind)
        return bands if cell is None else bands.get(cell, [])

    # =============================================================================================
    # C6a VT-7 · THE LOCAL SLICE (design/25 v2.1 ruling 17 / ruling 16 / ruling 10; design/53 B11)
    # =============================================================================================
    # A LOCAL SLICE (ruling 17) is a session's cut of the top three levels — the rules binding this
    # session's actor and its space — carrying the record VERSION (border.chain_head, the chain
    # tip) and a content HASH (canonical_hash over the cut, seq-stripped: the design/34 §3 content
    # seal, so an identical law re-minted at a new seq is the SAME content — the version witnesses
    # position, the hash witnesses content) it was cut from. On RECONNECT the slice reads STALE BY
    # DERIVATION (the P17 pattern, the class note above: a cut outliving its head serves a stale
    # answer) — re-cut for the same session over the current head and compare the carried
    # (version, hash); NEVER a stored stale flag (stop b). While the session is CUT OFF the brake is
    # a FROZEN view of ONLY the must-nots (the polarity '-' don'ts the online gate already enforces,
    # gate.py's pass-triggered don't) and it FAILS CLOSED: the offline slice has NO allow path — a
    # must-not fires REFUSED, everything else DEFERs (a may-do is not decided locally; it waits for
    # a fresh record read — ruling 16, "only the must-nots act offline"). NO new field, NO founding:
    # polarity, when, scope, chain_head, canonical_hash and strip_derivation are read and reused.

    def _slice_binding_scope(self, rule, as_of=None):
        """A rule's BINDING SPACE, resolved exactly as the gate's don't-firing resolves it
        (gate.py: scope, else space, else the mother) — the one resolution, reused, never a second
        opinion about where a law reaches."""
        scope = rule.get("scope")
        if scope is None:
            scope = rule.get("space")
        if scope is None:
            scope = self.mother_space(as_of)
        return scope

    def local_slice(self, session, as_of=None):
        """CUT a session's LOCAL SLICE of the top three levels (ruling 17). The binding rules are the
        active rules whose scope REACHES this session's space (the gate's own `space_reaches`: a rule
        binds the session iff its scope's subtree covers the session's space — never wider than the
        actor's own reach, I1), split into the MUST-NOTS (polarity '-', the don'ts) and the MAY-DOS
        (polarity '+', the dos; op/view definitions excluded, the toothless_musts precedent — they
        are declarations, not permissions). The cut CARRIES the record VERSION (`chain_head`) and a
        content HASH (`canonical_hash` over the seq-stripped binding — design/34 §3) it was cut from.
        `session` is {actor, space}; space defaults to the mother. A DIFFERENT session (a different
        binding space) is a DIFFERENT cut — a subspace-scoped don't binds a session in that subspace
        and not a sibling's. Pure derivation; appends nothing (a permanent tier would be one
        view-definition row, never a change to the masters or the founding — ruling 16)."""
        from . import border
        space = session.get("space") or self.mother_space(as_of)
        binding = {rid: r for rid, r in self.active_rules(as_of).items()
                   if self.space_reaches(self._slice_binding_scope(r, as_of), space, as_of=as_of)}
        must_nots = {rid: r for rid, r in binding.items() if r.get("polarity") == "-"}
        may_dos = {rid: r for rid, r in binding.items()
                   if r.get("polarity") == "+"
                   and r.get("kind") not in ("op_definition", "view_definition")}
        return {"session": session.get("actor"), "space": space, "as_of": as_of,
                "must_nots": must_nots, "may_dos": may_dos,
                "cut_version": border.chain_head(self.store, as_of),
                "cut_hash": canonical_hash(strip_derivation(binding))}

    def slice_stale(self, cut, as_of=None):
        """RECONNECT (ruling 17): the slice reads STALE BY DERIVATION when the CURRENT record has
        moved past the (version, hash) it was cut from — the P17 pattern (the class note: a cut
        outliving its head serves a stale answer), NEVER a stored flag (stop b). Re-cut for the SAME
        session over the current head and compare the carried (version, hash): STALE iff EITHER
        witness differs (chain_head advances on any append — the safe direction; the seq-stripped
        content hash is the second witness, ruling 17 'witnesses, not walls', catching a content
        tamper). A cut re-checked against the head it was cut from reads LIVE — the check can fail,
        which is A2's live control."""
        fresh = self.local_slice({"actor": cut["session"], "space": cut["space"]}, as_of)
        return (cut["cut_version"], cut["cut_hash"]) != (fresh["cut_version"], fresh["cut_hash"])

    def slice_offline_decision(self, cut, draft):
        """THE OFFLINE BRAKE (ruling 16): while the session is CUT OFF, only the MUST-NOTS act. The
        FROZEN view of only the must-nots carried in the cut stays live and FAILS CLOSED — the
        offline slice has NO allow path. Returns 'REFUSED' (with the rule and its cited law) when a
        frozen must-not FIRES on the draft — the gate's own matcher (`_draft_matches` + `space_reaches`,
        reused, the same trigger the online gate refuses on). Otherwise 'DEFER': a may-do is NOT
        decided locally (a laptop acts on its local answer only for the must-nots; a permission waits
        for a fresh record read). NEVER 'ALLOWED' — the local NO is safe and final, the local YES is
        not given offline. A must-not with an empty `when` (machinery-enforced) is not locally
        evaluable, so the act DEFERs rather than proceeding — still no allow path (fail-closed)."""
        from .gate import _draft_matches
        pdict = draft.get("payload") if isinstance(draft.get("payload"), dict) else None
        act_space = (pdict.get("scope") if pdict and pdict.get("scope") is not None else None) \
            or (pdict.get("space") if pdict else None) or cut["space"]
        for rid in sorted(cut["must_nots"]):
            r = cut["must_nots"][rid]
            when = r.get("when")
            if not isinstance(when, (list, tuple)) or not when:
                continue                                  # machinery-enforced don't — not locally evaluable
            if not _draft_matches(draft, when):
                continue
            if not self.space_reaches(self._slice_binding_scope(r), act_space):
                continue                                  # the act is outside this don't's reach
            cite = next((step["refuse"] for step in (r.get("then") or []) if step.get("refuse")), None)
            return {"decision": "REFUSED", "rule": rid, "under": cite or rid}
        return {"decision": "DEFER"}


# =================================================================================================
# C6 P6 · THE HANDSHAKE CHECKS (I8 the double-claim; I16 separation of powers) — module-level.
# =================================================================================================
# These run AT a handshake (P7's relation over the crossing/receipt, consumed — the occasion two
# machines meet) OVER BOTH records' live rules. They take ALREADY-COMPUTED presentations (each
# machine folds its OWN record via Views.held_stages / held_stage_scopes — one pen per record, I1),
# so no view here folds two records as one truth (I2). They are plain instruments — the P4/P15
# census idiom — NOT gate ops and NOT registered check kinds (no OP_CHECKS member added, A4): the
# "refused and recorded" of B8/I8 rides P7's own handshake record; these name the refusal.

#: The three powers I16 forbids one actor to hold together for one scope: decision + enforcement +
#: monitoring (B7 — decision rows, refusal/enforcement rows, the monitoring view). Separation of
#: powers RIDES protection.SOP (the existing mechanism, reused, never re-authored).
THREE_POWERS = ("decision", "enforcement", "monitoring")


def handshake_double_claim(held_here, held_there):
    """I8 / B8 — the one-machine-per-stage-per-scope conflict set: the (stage, scope) pairs BOTH
    machines hold. `held_here` / `held_there` are (stage, scope) presentations (Views.
    held_stage_scopes), each computed by its machine over its OWN record. Empty => no double-claim
    (disjoint scopes, or only one holder, pass). This is the pure comparison; refuse_double_claim
    turns it into the named refusal."""
    return set(held_here) & set(held_there)


def refuse_double_claim(held_here, held_there):
    """I8 — REFUSE a second machine claiming a stage another already holds for the SAME scope, BY
    NAME, at the handshake. Raises OpError('I8') naming every conflicting (stage, scope); no
    conflict => returns (the handshake proceeds). Able-to-fail: a planted double-claim raises, and
    disjoint scopes / a single holder do not."""
    conflicts = handshake_double_claim(held_here, held_there)
    if conflicts:
        from .errors import OpError
        named = ", ".join(f"{s} @ {sc}" for (s, sc)
                          in sorted(conflicts, key=lambda x: (str(x[0]), str(x[1]))))
        raise OpError("I8", "a second machine claims a stage another machine already holds for the "
                            f"same scope (one machine per stage per scope): {named}")


def separation_of_powers_conflicts(held):
    """I16 — the (actor, scope) pairs where ONE actor holds ALL THREE powers (decision + enforcement
    + monitoring) for ONE scope. `held` is a Views.held_stages list (a machine's own presentation).
    Empty => no actor concentrates all three (holding any two of the three is not a conflict)."""
    by_actor_scope = {}
    for h in held:
        by_actor_scope.setdefault((h["actor"], h["scope"]), set()).add(h["stage"])
    return {k for k, stages in by_actor_scope.items() if set(THREE_POWERS) <= stages}


def refuse_separation_of_powers(held):
    """I16 — REFUSE a declared stage set that puts decision, enforcement AND monitoring on one actor
    for one scope. RIDES protection.SOP (reused). Raises OpError(SOP) naming the actor and scope; no
    such actor => returns. Able-to-fail: all three on one actor raises, any two of the three do
    not."""
    conflicts = separation_of_powers_conflicts(held)
    if conflicts:
        from .errors import OpError
        from .protection import SOP
        named = ", ".join(f"{a} @ {sc}" for (a, sc)
                          in sorted(conflicts, key=lambda x: (str(x[0]), str(x[1]))))
        raise OpError(SOP, "one actor may not hold decision, enforcement and monitoring together "
                           f"for one scope (separation of powers): {named}")
