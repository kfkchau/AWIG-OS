# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — the record (L0): the append-only master record.

Ported from the estate's proving store (apps/pwc-app/src/core/store.js) into the
AWIG OS canonical envelope (design/11-RECORD-SHAPES.md; names per
design/20-CANONICAL-GLOSSARY.md).

Laws honoured here:
  - Append is the atomic commit point. `seq` and `record_time` are minted at append,
    never supplied (design 02 §1.1; failure book FB2). record_time is the sole
    total-order anchor (02 §1.4).
  - No update path, no delete path exists in code (P1/P2). The one sanctioned
    exception is owner master-destruction with a surviving scar (GS-13); NOT in v0.
  - The round-trip law (02 §1.3): delete every derived cache, replay, and the
    reconstruction is identical. The derived index below is rebuilt on load and
    maintained on append; deleting it changes no answer. `tests/test_store.py`
    proves diff = 0.

v0 is single-writer (the stale-checked pidfile lock — the single-writer ruling). The
multi-writer intake pipeline (seam S5; ordering key K = bucket, built_id,
submission_time — design 21) is deferred; the envelope already carries
`submission_time` and `origin.built_id` so the sequencer can be added later without a
schema change (design for the stretch, 02 §2).
"""

import atexit
import datetime
import json
import os
import threading
import weakref
from pathlib import Path
from types import MappingProxyType

from .canonical import canonical_hash
from .commit import BatchFailed, GroupCommit
from . import keys                          # KeyProjection reads keys.KEY_KINDS/ACCOUNT (one
                                            # recognition rule, not a second) — keys imports
                                            # nothing, so store -> keys is acyclic.

# THE CHAIN AND THE ANCHOR (EP-35; design/37 Q1; envelope word board :2755). One SYSTEM
# decision record — the chain-anchor — seals the entire pre-existing prefix; from that record
# forward every NEW record store-mints the grow-only proof fields the owner licensed (predecessor
# hash + the two signatures) and NOTHING WIDER. `chain-anchor` is a sanctioned SYSTEM direct
# append using existing mechanisms exactly as the dual-audit mirror is — no new op, law or kind.
CHAIN_ANCHOR_ACTION = "chain-anchor"
# THE HONEST-DEGRADE SENTINEL (§8-j; A10/RW6). The two signature fields depend on write-time
# signing whose custody is EP-36's vault. Until that vault is composed, a post-seal record records
# its signature fields PRESENT-BUT-PENDING: never omitted, never a false signed claim, never
# blocking the `prev_hash` chain — the chain's edit-evidence is independent of signing.
SIG_PENDING = "pending"


def _now_iso():
    """UTC ISO-8601. record_time uses this at append (the total-order anchor)."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


#: DESCRIPTOR NUMBERS THIS PROCESS HAS LET GO OF WITHOUT CLOSING (EP-28C W4c). A store whose
#: descriptor number was taken from underneath it must not close that number later: it names a
#: different file now, and closing it would close a stranger's. The only safe act is to let go
#: without touching it, and letting go means keeping the wrapper alive — CPython closes a file
#: object's descriptor when the object is collected, so dropping it is the very act being
#: refused. Bounded by construction: an entry appears only where a descriptor was already
#: stolen, which is a defect somewhere else in the process, and it holds no memory beyond the
#: wrapper itself.
_STRANDED = []


def _close_handle(fh, fd, ident):
    """Close a store's held record descriptor — IF IT IS STILL THIS STORE'S. Module-level and
    taking the FILE rather than the store, so the finalizer that calls it holds no reference
    back to the store.

    THE DEFECT THIS CLOSES (EP-28F raise 3, intaken at EP-28C AMENDMENT 4 §4.2). This runs
    from a `weakref.finalize`, so for an ABANDONED store it runs at an arbitrary later
    garbage-collection point, in whatever code happens to be executing then. It used to call
    `fh.close()` unconditionally. A file object holds a raw descriptor NUMBER, and **a raw
    descriptor number is not a stable identity**: if anything else in the process closed that
    number first, the kernel is free to hand it to the next `open`, and a late unconditional
    close then closes a stranger's file. That is not hypothetical in this estate — the
    conformance instrument's `files.close` row exists precisely to close a descriptor number
    and see what happens, and `[Errno 9]` from this family has already reached product code at
    `src/founding/install.py:72` in full-suite runs.

    THE CHECK IS AN IDENTITY, NOT AN ABSENCE (§A38). `fstat` on the number reports which FILE
    the number currently names; compared against the identity taken when this store opened it,
    a match is a positive statement that the descriptor is still ours. An absence check — "no
    error was raised" — cannot tell "still mine" from "someone else's, and healthy".

    Returns the branch it took, so the decision is OBSERVABLE rather than inferred: a caller
    or a test can read which of the three worlds it was in.
    """
    try:
        st = os.fstat(fd)
    except OSError:
        # ALREADY CLOSED AND NOT REUSED. There is nothing of ours here and nothing to do;
        # closing again would be a second release of a number we no longer hold.
        _STRANDED.append(fh)
        return "already-closed"
    if (st.st_dev, st.st_ino) != ident:
        # TAKEN AND REUSED. The number names a different file. We neither close it nor write
        # to it, and we keep the wrapper so that collecting it cannot do either for us.
        _STRANDED.append(fh)
        return "not-ours"
    try:
        fh.close()
    except Exception:
        pass
    return "closed"


def _pid_alive(pid):
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by another user
    return True


def _freeze(obj):
    """Deep-freeze a record for the in-memory copy (H1, extended — EP-02): a stored record
    is immutable ALL THE WAY DOWN, not just at the envelope. dict -> read-only view,
    list -> tuple, recursively; scalars unchanged. The on-disk jsonl stays the truth; this
    only hardens the replay cache so no consumer can mutate a payload interior in place."""
    if isinstance(obj, dict):
        return MappingProxyType({k: _freeze(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return tuple(_freeze(v) for v in obj)
    return obj


def frozen_default(o):
    """json.dumps helper: a frozen dict (MappingProxyType) is not natively serialisable;
    expose it as a plain dict so digests over frozen records still compute. Tuples (frozen
    lists) serialise natively as arrays."""
    if isinstance(o, MappingProxyType):
        return dict(o)
    raise TypeError(f"not JSON serialisable: {type(o).__name__}")


# ---- the record projections (EP-24B item A; generalised to a class by EP-24C) -------------
# WHAT THIS IS, stated before the code because the distinction is the whole point.
#
# A PROJECTION holds WHERE THE INPUTS ARE. A CACHE holds WHAT THE ANSWER WAS. The first is a
# pure acceleration under P2 — kill it, replay, it reconstructs identically. The second is
# a stored permission table however it is spelled, and no invalidation logic converts one
# into the other, because the defect is not staleness: it is that the answer stopped being
# computed from the record. These structures are the first kind, and they are the first kind
# STRUCTURALLY rather than by assertion: their entire contents are record SEQUENCE NUMBERS.
# There is nowhere in one for a verdict, a permission set, a role expansion or a computed
# complement to live, because it stores integers. Every record a fold evaluates is
# resolved out of the record at read time, and `authority.covers` computes the positive
# grant and its complement exactly as design/30 specifies, live, on every call. What
# changed is only how many records a fold has to look past to find its inputs.
#
# EP-24C EXTENDS THE PATTERN AND DOES NOT ADD A SECOND ONE. `design/36` ADDENDUM C rules the
# defect a CLASS: any fold that reads the whole record to answer a governance question has
# it. So the machinery below is ONE implementation — currency, resolution, refusal — and each
# subset varies exactly one thing, the predicate that selects. Four subsets, one mechanism.
#
# THE ONE STEP TOO FAR, NAMED SO IT IS REFUSED BY SHAPE. The temptation this round is not to
# invent a cache; it is to extend a proven structure from holding WHERE THE INPUTS ARE to
# holding WHAT THE FOLD CONCLUDED. `_seqs` and `_by_action` hold integers and nothing else,
# and every read hands back the record itself through `_resolve`. A structure that could
# answer a governance question without any record being read would be the refused reference
# wearing last round's approval.

# The law-and-grant subset: the records the authority fold can react to. Each entry names
# the fold read that justifies it, because an entry with no reader is an entry nobody can
# check.
#   GRANT / REVOKE          authority.grants()      — the live grant set, revoke-superseded
#   CREATE-SPACE            authority.spaces()      — the space tree's nodes
#   CREATE-ROLE             authority.roles()       — the founded role names
#   payload.kind info_space authority.mother_space()— the tree's root
#   payload.kind category_pack  authority._hold_token() — the `hold` action vocabulary
#   payload.kind grant      NOT read by any fold today; admitted so that a grant-kind record
#                           minted by some other op (the R-A passthrough shape the gate
#                           already leashes) is inside the subset if a fold ever reads it.
# ADMITTING TOO MUCH IS SAFE AND ADMITTING TOO LITTLE IS NOT: a superset costs time and
# cannot change an answer, while a subset that misses a REVOKE would let the fold answer
# yes where the record says no. Every judgement call here is therefore made WIDE.
GOVERNANCE_ACTIONS = ("GRANT", "REVOKE", "CREATE-SPACE", "CREATE-ROLE")
GOVERNANCE_PAYLOAD_KINDS = ("grant", "info_space", "category_pack")
# The by_action keys the fold asks this index for. A key outside this set is a fold that has
# grown a read the index was not built to serve: it FAILS LOUD rather than returning an empty
# list, because an empty list is a wrong answer wearing the costume of a right one (ST-A, no
# silent fallbacks; P4, refusal over improvisation).
GOVERNANCE_INDEXED_ACTIONS = GOVERNANCE_ACTIONS + ("CREATE-INFO",)


def is_governance_record(e):
    """Does this record belong to the law-and-grant subset the authority fold reads?"""
    if e["action"] in GOVERNANCE_ACTIONS:
        return True
    p = e.get("payload") or {}
    return p.get("kind") in GOVERNANCE_PAYLOAD_KINDS


# ---- the echo-retire discipline (EP-28C W2; design/38 §1 as its ADDENDUM 1 rules) --------
# THE PROPERTY, in design/38's own words: confirmation is CONTENT-HASH IDENTITY, so a mutated
# or partial append can never silently satisfy an intent. A submitter hands the appender a
# draft and blocks; the reply carries the appended record's identity AND a hash over exactly
# the fields the draft STATED; the submitter compares against its own draft and refuses loud
# on any difference.
#
# THE SUBJECT IS THE STATED FIELDS AND NOT THE WHOLE RECORD, and that is a derivation rather
# than a convenience. `seq` and `record_time` are MINTED at the append and the submitter does
# not know them, so hashing them would be the appender being compared against itself — a
# check that cannot fail. What a mutated or partial append breaks is agreement with the draft
# on what the draft said, and that is precisely what this covers.
#
# AND IT ARRIVES HERE AS PIPELINE, NEVER AN EFFECT-LICENSE (design/38 ADDENDUM 1, invariant
# 4). The echo confirms a record that is already durable. It licenses nothing, it retires
# nothing early, and there is no path by which a pending entry answers a question.
ECHOED_FIELDS = (
    "actor", "action", "object", "target", "rule_cited", "evidence_summary",
    "provenance", "content_form", "refs", "payload", "record_id", "origin",
    "submission_time", "occurrence_time", "refused",
    # record_stream (EP-30-W1a): the field decides WHERE the record is indexed, which is the
    # locator every check's reach rests on, so a mutated stream is exactly the mutation this
    # echo exists to catch. Additive and inert for every draft that does not state it — the
    # digest covers only the fields a draft named, so no existing submitter's hash moves.
    "record_stream",
)


class EchoMismatch(RuntimeError):
    """The appended record disagrees with the draft on a field the draft stated. LOUD, and
    never a silent retire: an intent whose confirmation does not match is an intent nobody
    may treat as satisfied (design/38 §1)."""


def echo_digest(mapping, draft):
    """The canonical hash over exactly the fields `draft` stated, read out of `mapping`.

    Called twice with the same `draft`: once by the appender against the APPENDED RECORD, and
    once by the submitter against its own draft. Equal iff the record agrees with the draft
    everywhere the draft spoke. The canonical encoding treats a frozen mapping as a mapping
    and a tuple as a list, so the deep freeze the store applies moves nothing."""
    stated = sorted(k for k in ECHOED_FIELDS if k in draft)
    return canonical_hash({k: mapping.get(k) for k in stated})


class RegionHeldAtBarrier(RuntimeError):
    """THE DECIDE REGION'S EXCLUSION LAW, VIOLATED (EP-28G, wrong reference 1). A thread
    reached the durability barrier while still holding `gate.DecideRegion`. It is raised
    rather than asserted so that `python -O` cannot delete the one check standing between
    this estate and the big lock, and it is loud rather than degrading because a region held
    across `fdatasync` does not fail — it silently erases the lever."""


class StaleIndex(RuntimeError):
    """A projection could not prove it is current against the record. It refuses; it never
    serves (design/36 K3's coherent-or-refuse — a hop never lies)."""


def stream_of(e):
    """WHICH STREAM A RECORD IS INDEXED UNDER — the declared one, else the door it came in by.

    ONE DEFINITION, ON PURPOSE, and it is the whole reason this is a function rather than two
    `e.get(...) or e["action"]` expressions. A record is placed into a `_by_action` map at
    exactly two sites — the store's own index and a record projection's refresh — and they
    answer the same question for the same record. Two copies of this line could drift, and the
    drift would be invisible in the worst possible way: the store and a projection would
    disagree about where a record lives, so a fold reading through the projection and a check
    reading the store would locate different sets and BOTH would look right. That is the class
    this campaign keeps meeting, where the record is correct and the views disagree.

    The default is `action` — the door — so every record written before a stream could be
    declared, and every record written by an op that declares none, is indexed exactly where it
    always was."""
    return e.get("record_stream") or e["action"]


class RecordProjection:
    """A derived projection over one subset of the record: seq numbers and nothing else.

    It presents the two read methods a fold calls on a store — `all` and `by_action` — so
    the fold reads through it WITHOUT ONE LINE OF THE FOLD CHANGING. That is deliberate,
    and after EP-24B it is standing law in the build-prompt standard. One fold
    implementation reading two record sources means the differential against the
    unaccelerated path tests exactly ONE variable, the subset; two implementations could
    diverge in logic as well, so every divergence would be ambiguous between "the subset
    was wrong" and "the second implementation was wrong", and no test could tell you which.

    COHERENT OR REFUSE. Before serving anything it proves it is current against the
    record: the number of records it has ingested must equal the record's length, and
    every seq it holds must still resolve to the record it selected. Behind the record, it
    RECOMPUTES from the record (catching up is reading the definitive, not improvising).
    Unable to reconcile — a record shorter than what it ingested, or a seq that no longer
    resolves — it REFUSES. It never serves a subset it cannot prove.

    A SUBCLASS SUPPLIES THREE THINGS AND NOTHING ELSE: the name it refuses under, the
    `by_action` keys it was built to answer, and the predicate `_selects`. Everything a
    reviewer has to check about a new subset is therefore in one place, next to the fold
    read that justifies it.

    ALL THREE ARE UNDERSCORED, AND THAT IS NOT STYLE. EP-24B pinned the PUBLIC surface of
    this structure to exactly six names — `all`, `by_action`, `catchups`, `is_current`,
    `kill`, `refresh` — and guards it, because a surface that can grow is a surface a verdict
    can eventually be hung on. Generalising the class into a base tried to add three public
    names and that guard caught it. The knobs a subclass sets are internal to the projection;
    what a fold sees is still the two reads a store offers.
    """

    _NAME = "record projection"
    # The by_action keys the folds ask this projection for. A key outside this set is a fold
    # that has grown a read the projection was not built to serve: it FAILS LOUD rather than
    # returning an empty list, because an empty list is a wrong answer wearing the costume of
    # a right one (ST-A, no silent fallbacks; P4, refusal over improvisation).
    _INDEXED_ACTIONS = ()

    @staticmethod
    def _selects(e):
        """Does this record belong to the subset? The ONE thing a subset varies."""
        raise NotImplementedError

    def __init__(self, store):
        self._store = store
        self._seqs = []          # ascending seq numbers: the subset
        self._by_action = {}     # action -> ascending seq numbers
        self._seen = 0           # records ingested — the currency stamp, checked against the record
        self.catchups = 0        # observable: how often a currency check forced a recompute

    def kill(self):
        """Delete every acceleration structure (T-ACCELERATION-IS-DERIVED). The next read
        proves itself uncurrent and rebuilds from the record alone."""
        self._seqs = []
        self._by_action = {}
        self._seen = 0

    def refresh(self):
        """Catch up from the record. Killing this projection and rebuilding it is this method
        starting from zero, so 'kill it, replay, identical' is one code path, not two.

        `_seen` counts POSITIONS WALKED, never a record's own `seq` field: the stamp then
        means "I have looked at this many records" and is checked against a length the store
        owns, so nothing the projection holds about itself can make it look current when it is
        not. (A record whose seq disagrees with its position is caught separately, at
        `_resolve`, where it refuses.)"""
        n = len(self._store.events)
        if self._seen > n:
            raise StaleIndex(
                f"the {self._NAME} has ingested {self._seen} records but the record holds {n} — "
                "it is not a projection of this record and cannot be reconciled by recomputation; "
                "it refuses")
        while self._seen < n:
            e = self._store.events[self._seen]
            if self._selects(e):
                self._seqs.append(e["seq"])
                self._by_action.setdefault(stream_of(e), []).append(e["seq"])
            self._seen += 1

    def is_current(self):
        return self._seen == len(self._store.events)

    def _prove_current(self):
        if not self.is_current():
            self.refresh()
            self.catchups += 1

    def _resolve(self, seq):
        """A seq is a LOCATION; the record is the content. Resolving through the store is
        what keeps this a projection — the fold is handed the record, never a copy this
        structure kept."""
        e = self._store.by_seq(seq)
        if e is None or e["seq"] != seq:
            raise StaleIndex(
                f"the {self._NAME} names record {seq}, which the record does not resolve — "
                "a projection that cannot resolve its own locations refuses; it never serves")
        return e

    # ---- the two reads the folds make (the store's own signatures) ----
    def all(self, as_of_seq=None):
        self._prove_current()
        return [self._resolve(s) for s in self._seqs
                if as_of_seq is None or s <= as_of_seq]

    def by_action(self, action, as_of_seq=None):
        self._prove_current()
        if action not in self._INDEXED_ACTIONS:
            raise StaleIndex(
                f"the {self._NAME} was not built to answer by_action({action!r}) — the fold reading "
                "through it has grown a read outside this subset. Extend the subset (and its "
                "differential) rather than letting this read return an empty list")
        return [self._resolve(s) for s in self._by_action.get(action, [])
                if as_of_seq is None or s <= as_of_seq]


class GovernanceIndex(RecordProjection):
    """The law-and-grant subset — the records `kernel.authority`'s eleven folds can react to
    (EP-24B item A). The subset and its justifications are `is_governance_record` above."""

    _NAME = "governance index"
    _INDEXED_ACTIONS = GOVERNANCE_INDEXED_ACTIONS
    _selects = staticmethod(is_governance_record)


# ---- the three remaining per-act-path subsets (EP-24C; design/36 ADDENDUM C) --------------
# Each predicate is written next to the fold read that justifies it, and each is the fold's
# OWN recognition rule or a deliberate widening of it. The EP-24B asymmetry drove every
# judgement call and is repeated here because it is the reason these are safe: ADMITTING TOO
# MUCH COSTS TIME AND CANNOT CHANGE AN ANSWER, while admitting too little would let a fold
# miss a record the record says is there. Every choice below is therefore made WIDE.
#
# None of the three folds calls `by_action` on its source, so all three declare NO indexed
# keys: a `by_action` read against one of them refuses loud rather than returning an empty
# list, which is exactly how a fold that grows a new read announces itself.

# `views._op_definitions` folds CREATE-OP / AMEND-OP into the live set and deletes on
# RETIRE-OP. It also tests `payload.kind == "op_definition"` on the first two; this predicate
# deliberately does NOT, so a malformed or future definition-shaped record still reaches the
# fold and is judged there, by the one implementation, rather than being filtered out here.
OP_DEFINITION_ACTIONS = ("CREATE-OP", "AMEND-OP", "RETIRE-OP")


def is_op_definition_record(e):
    """Does this record belong to the operation-definition subset?"""
    return e["action"] in OP_DEFINITION_ACTIONS


def is_law_record(e):
    """Does this record belong to the law subset? THE FOLD'S OWN RULE, unchanged: a record IS
    a law record iff its payload declares a `rule_id` — recognition by self-declaration, not
    by an action-name list, so a future subsystem's law op is selected without this predicate
    learning its verb (`views._active_rules`)."""
    return (e.get("payload") or {}).get("rule_id") is not None


def is_pack_record(e):
    """Does this record belong to the vocabulary subset? The fold (`views._category_packs`)
    additionally requires a name and a well-formed `levels` list before a pack enters the
    vocabulary; that judgement stays IN THE FOLD, so a malformed pack is still seen and still
    rejected there rather than being made invisible by the subset."""
    return (e.get("payload") or {}).get("kind") == "category_pack"


class OpDefinitionProjection(RecordProjection):
    _NAME = "op-definition projection"
    _selects = staticmethod(is_op_definition_record)


class LawProjection(RecordProjection):
    _NAME = "law projection"
    _selects = staticmethod(is_law_record)


class PackProjection(RecordProjection):
    _NAME = "vocabulary projection"
    _selects = staticmethod(is_pack_record)


# The projections a store can be asked for, by the name the fold reading through it uses.
# Enumeration is the completeness guarantee (P3 applied to this surface): a name outside this
# table does not exist and refuses, rather than resolving to some default.
PROJECTIONS = {
    "authority": GovernanceIndex,
    "op_definitions": OpDefinitionProjection,
    "law": LawProjection,
    "category_packs": PackProjection,
}


class ActionSetProjection(RecordProjection):
    """A record subset keyed by a SET OF ACTIONS a check declares, not by a fixed predicate
    class (MAINT-K12-CEILING-FOLD, archi board :2727 A2).

    The four subsets above each fix their predicate in a `_selects` STATICMETHOD, because each
    answers one fold whose recognition rule is known at class-write time. A `ceiling` check's
    family is not: it is whatever `aggregate_action` and `removal_action` the check's founding
    row declares, so the subset must be a PARAMETER, not a literal. This subclass takes that
    action-set and selects on it — the SAME coherent-or-refuse, resolve-through-the-store
    machinery every subset above uses, with the ONE varying thing (the predicate) supplied per
    instance rather than per class. It reads through store.py:268's standing law unchanged: it
    presents `all`/`by_action`, so the ceiling fold reads through it with not one line of the
    fold body changing, and the differential then tests exactly one variable — the subset.

    COMPLETENESS, stated beside the fixed-name PROJECTIONS enum above because it is the same
    surface's other half: the fixed enum answers "which NAMED projections exist" (a name outside
    it refuses); this variant answers "which ACTION-SET projections exist", and the answer is
    'exactly the ones a check's founding-declared config names'. The key IS the check's own
    `{aggregate_action, removal_action}`, so the registration and the fold's recognition rule are
    ONE object and cannot disagree — no second recognition rule is written (the flaw the kernel
    would have grown by importing a subsystem's memory predicate). An action-set from nowhere —
    an empty set — REFUSES at `action_set_projection` rather than serving the empty list a
    select-nothing subset would return (a wrong answer in a right one's costume).

    EP-24B SURFACE UNMOVED: `_actions` and the instance `_selects` are underscored, so the
    T-NO-STORED-TABLE guard still sees exactly {all, by_action, catchups, is_current, kill,
    refresh}. The parameterization is a subclass, not a growth of the six-name public surface."""

    _NAME = "action-set projection"

    def __init__(self, store, actions):
        self._actions = frozenset(actions)
        super().__init__(store)

    def _selects(self, e):
        return e["action"] in self._actions


class KeyProjection(RecordProjection):
    """A record subset keyed by an ACCOUNT: exactly that account's key-lifecycle records — bind,
    rotate and revoke (keys.KEY_KINDS) — the subset keys.bound_key folds over (EP-36 F1; board
    :2906/:2910, Option A). The signed door reads the bound key on EVERY act at operation rate
    (EP-37 / mover-2's SIGN-LAW), so the per-act key read must be a SUBSET read, not a whole-record
    scan — the T-PER-ACT-PATH-READS-SUBSETS bound `tests/test_ep24c.py` declares. This makes it one.

    PARAMETERIZED BY ACCOUNT, exactly as `ActionSetProjection` above is parameterized by an
    action-set: the ONE varying thing (here the account) is supplied per instance rather than per
    class, and every other line — the coherent-or-refuse currency check, resolve-through-the-store,
    the two reads `all`/`by_action` — is `RecordProjection`'s unchanged (store.py:276's standing
    law). `keys._key_records` reads through it with NOT ONE LINE of its fold body changing, so the
    differential against the unaccelerated oracle tests exactly one variable, the subset.

    ONE RECOGNITION RULE, NOT A SECOND (the discipline stated for `ActionSetProjection` above): the
    predicate below reads `keys.KEY_KINDS` and `keys.ACCOUNT` — the FOLD'S OWN constants — so this
    projection's recognition and `keys._key_records`'s recognition are the same source and cannot
    disagree. A record of a key kind the fold recognises is a record this subset selects.

    AS-OF-PAST HOLDS BY CONSTRUCTION over a counterfactual world (board :2910): a KeyProjection
    built over a `reconcile.WorldStore` reads that world's `events`, which the world's `_selects`
    has ALREADY folded by deciding time — so `keys.bound_key` routed through it answers the binding
    valid AS OF the act's own deciding moment, the identical answer the fold gives reading that
    world directly. ONE read path, both frames (binding 1).

    EP-24B SURFACE UNMOVED: `_account` and the instance `_selects` are underscored, so the six-name
    public surface {all, by_action, catchups, is_current, kill, refresh} is unchanged."""

    _NAME = "key projection"

    def __init__(self, store, account):
        self._account = account
        super().__init__(store)

    def _selects(self, e):
        p = e.get("payload") or {}
        return p.get("kind") in keys.KEY_KINDS and p.get(keys.ACCOUNT) == self._account


class EventStore:
    """The append-only master record. One jsonl file, one record per line.

    In-memory `events` is a replay cache of the file; the file on disk is the truth.
    (Python dicts are not frozen; immutability is guaranteed by exposing no mutate
    path, matching the estate's C1. The blob store for large payloads is a later
    step; v0 keeps payloads inline.)
    """

    def __init__(self, file_path, lock=False, require_rule_cited=False):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.events = []
        self._lock_path = None
        # H3: when True, every appended record must cite a rule (fail loud, ST-A).
        self.require_rule_cited = require_rule_cited
        if lock:
            self._acquire_lock()
        if self.file_path.exists():
            with self.file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.events.append(_freeze(json.loads(line)))  # H1: deep read-only
        # Derived caches: rebuilt on load, maintained on append. Delete them and
        # replay yields identical answers (round-trip law; no state lives here).
        self._by_action = {}
        # The record projections (EP-24B, extended EP-24C) are built on FIRST USE and catch up
        # from the record on every read, so a store nobody asks pays nothing and a store that
        # is asked can never be handed a subset older than the record.
        self._projections = {}
        # Config-keyed record projections (MAINT-K12-CEILING-FOLD, board :2727 A2): held here
        # exactly like `_projections` above — build-on-first-use, caught up on every read,
        # deletion changes no answer — but keyed by the frozenset of actions a check declares
        # rather than by one of the four fixed PROJECTIONS names. See `action_set_projection`.
        self._action_set_projections = {}
        # Per-account KEY projections (KEY-PROJECTION, board :2906/:2910, Option A): held here
        # exactly like the two above — build-on-first-use, caught up on every read, deletion
        # changes no answer — but keyed by the ACCOUNT whose key binding keys.bound_key folds,
        # so the signed door's operation-rate key read is a SUBSET read. See `key_projection`.
        self._key_projections = {}
        for e in self.events:
            self._index(e)
        self._listeners = []
        # THE HELD DESCRIPTOR (EP-28C W3, carried in from the EP-28D verdict). Opened on the
        # FIRST APPEND rather than here: a store nobody writes to holds nothing, which keeps
        # the suite's thousands of disposable read-only worlds free of descriptors.
        self._fh = None
        self._broken = None
        # THE WRITE LOCK (EP-28G W1) — the single-writer discipline, relocated to the write.
        #
        # It is here because the SPLIT put it here, and the derivation is short. Before this
        # EP the publication of a record happened inside `_commit_batch`, which ran under the
        # appender role, so "one writer" was a consequence of "one appender". EP-28G moves
        # publication into the DECIDING thread — a record must be visible to the next decide
        # before its barrier, and a thread that waited for another thread to publish it could
        # not release the decide region without either holding it across the barrier or
        # closing every batch at width one. So the write is no longer inside the appender and
        # needs its own exclusion: `seq` is minted as `len(self.events) + 1` and the line is
        # written in the same breath, and two threads doing that at once would mint one number
        # twice and interleave two lines. Held for the mint, the write, the flush, the publish
        # into `self.events` and the listeners; NEVER across the barrier.
        #
        # IT IS NOT THE DECIDE REGION AND DOES NOT SUBSTITUTE FOR ONE. This lock makes two
        # appends land one after the other. It says nothing about two deciders that both read
        # the same pre-state and then both append — that is `gate.DecideRegion`, and the two
        # have different subjects (the file's integrity; the decision's consistency).
        #
        # RE-ENTRANT because the dual-audit mirror appends from inside an on-append listener,
        # which runs inside a publish on this same thread.
        self._write_lock = threading.RLock()
        #: Per-thread: is this thread currently inside a publish? A listener that appends is,
        #: and its record rides the enclosing act's barrier rather than waiting for one of its
        #: own — which is what happened before the split, when a nested submission was
        #: committed inline into the outer batch.
        self._publishing = threading.local()
        # MANY SUBMITTERS, ONE APPENDER (EP-28C W1). The queue is process-local mechanism and
        # is never persisted; `commit.GroupCommit` carries the derivation.
        self.group_commit = GroupCommit(self._commit_batch, self._verify_echo,
                                        publish_one=self._publish_one,
                                        publishing_here=self.publishing_here)
        self._finalizer = None

    # ---- single-writer lock (the single-writer ruling; one writer per data dir) ----
    def _acquire_lock(self):
        self._lock_path = self.file_path.with_name(self.file_path.name + ".lock")
        if self._lock_path.exists():
            try:
                pid = int(self._lock_path.read_text())
            except ValueError:
                pid = -1
            if _pid_alive(pid) and pid != os.getpid():
                raise RuntimeError(
                    f"event log locked by pid {pid} ({self._lock_path}) — "
                    f"one writer per data dir"
                )
        self._lock_path.write_text(str(os.getpid()))
        atexit.register(self._release_lock)

    def _release_lock(self):
        try:
            if (
                self._lock_path
                and self._lock_path.exists()
                and int(self._lock_path.read_text()) == os.getpid()
            ):
                self._lock_path.unlink()
        except Exception:
            pass

    # THE RECORD FILE IS NOW OPENED ONCE AND HELD (EP-28C W3, 2026-08-01). The raise below is
    # CLOSED and the text of it is kept because the mechanism it named turned out to be wrong,
    # and a withdrawn prediction is worth more on the record than an absent one.
    #
    # [DATED CORRECTION, 2026-08-01, EP-28C W3, on the EP-28D verdict of 2026-07-30. The
    # paragraph below is the raise AS FILED and it is NOT rewritten; this note is what driving
    # it established. Corrected in place rather than deleted, the handling `design/10` §11.2b
    # and EP-28B's own raise both got: a source comment stating a mechanism that driving it
    # refuted is a specification the next reader will build against.]
    #
    #   WHAT THE RAISE PREDICTED: that the fixture's interleaving makes the `files.close` row's
    #   EBADF answer vanish and hands the EBADF to the store's next append instead.
    #
    #   WHAT DRIVING IT SHOWED (EP-28D, held-descriptor double, both directions): the row's
    #   second `close` SUCCEEDS. The EBADF that gets reported is raised a moment later by the
    #   instrument's own barrier on the descriptor the row just closed, so the ABI leg still
    #   sees the pinned answer and the row PASSES. **Not a row red for the wrong reason — a row
    #   GREEN for the wrong reason**, which is the harder shape because nothing looks broken.
    #   The discriminator is the record itself: a `close` that raises appends nothing, so a
    #   step whose bracket grew is a step whose close returned.
    #
    #   WHAT THE RAISE WAS STILL RIGHT ABOUT, and it is why this is a correction and not a
    #   withdrawal: an instrument WAS interfering with its subject, at exactly the site named,
    #   and the repair was warranted. Only the predicted symptom was wrong.
    #
    #   AND WHY THE CHANGE WAS NOT OPTIONAL, in EP-28D's own words: the store still opened per
    #   append, so the instrument still momentarily occupied the number a row had just released
    #   — invisible only because the descriptor's lifetime was shorter than the gap between two
    #   subject calls, **which is a property of the store rather than a guarantee the instrument
    #   makes.** A conformance surface passing on an accident of timing that nobody promises is
    #   a surface that will move without anyone changing it.
    #
    # ---- THE RAISE AS FILED (EP-28B W2, HELD 2026-07-30) — retained, not rewritten ----
    #
    # The guest measured holding the descriptor instead at 0.10–1.80 ms cheaper per act, with
    # the same record and the same durability claim, and the change was written and then
    # withdrawn in the same session for a reason that has nothing to do with the store:
    #
    # The conformance instrument runs in the same process as a store, and the `files.close` row's
    # SUBJECT is that closing an already-released descriptor number returns EBADF. Its steps are
    # open, close, close-again. The row's own `close` is a subject call, so the fixture appends a
    # record between the two closes — a lazily-opened write descriptor then claims the LOWEST
    # FREE number, which is exactly the one the first close released. The second close lands on
    # the store's descriptor. [Refuted above: what follows was the predicted symptom.] The row's
    # EBADF answer vanishes and the store's next append gets EBADF instead.
    #
    # That is `design/10` §11.2b's rule about an instrument owning its subject, arriving from the
    # other side: this row's subject is the process's descriptor table and the row does not own
    # it. The repair is one line in the fixture — establish the store's descriptor BEFORE any row
    # runs — and `tools/` was not in that EP's fence, so it was raised rather than reached into.
    # Repairing the instrument that constrains you is the one shape charter §A25 says a fix may
    # never take. EP-28D was minted for exactly that reason and made the repair.
    #
    # The deployed brain is NOT affected either way: it closes every inherited descriptor at
    # startup, before the store exists (`bridge/kernel_port._close_inherited_descriptors`).

    def _index(self, e):
        self._by_action.setdefault(stream_of(e), []).append(e)

    def record_projection(self, name):
        """The derived projection a named per-act-path fold reads through (EP-24B item A,
        extended to the class by EP-24C) — the structure that makes a fold's cost track
        governance rather than the record's total length. A derived cache exactly like
        `_by_action` above: it holds locations, it is built from the record and nothing else,
        and deleting it changes no answer."""
        cls = PROJECTIONS.get(name)
        if cls is None:
            raise StaleIndex(
                f"there is no record projection named {name!r} — a fold asking for one that does "
                "not exist gets a refusal, never a default source. The projections are: "
                + ", ".join(sorted(PROJECTIONS)))
        p = self._projections.get(name)
        if p is None:
            p = self._projections[name] = cls(self)
        return p

    def action_set_projection(self, actions):
        """A HELD record projection over EXACTLY the given set of actions, keyed and cached by
        that set (MAINT-K12-CEILING-FOLD, board :2727 A2). A derived cache exactly like
        `record_projection` above — it holds locations, is built from the record on first use and
        caught up on every read, and deleting it changes no answer — the only difference is that
        its subset is named by a check's founding-declared action-set rather than by one of the
        four fixed PROJECTIONS names.

        HELD, so the K12 amortized-refresh accounting is TRUE and not arranged: the ceiling check
        reads through the ONE cached projection per action-set across every act, paying its
        family's records per read and the whole-record walk only as one-time / append-incremental
        maintenance — never a fresh walk per act (which would read the family bound off the
        instrument while doing the whole stream's work — the rejected Option C).

        An EMPTY action-set REFUSES rather than defaulting: a subset that selects nothing serves
        an empty list, which is a wrong answer wearing a right one's costume (the same discipline
        `by_action` holds for an unindexed key). The only caller is the ceiling check dispatch,
        whose `{aggregate_action, removal_action}` are guaranteed non-empty strings by
        `_require_wellformed_ceiling` (§A51); an empty set here means a caller reached this off
        that guarded path, and it is refused, not served."""
        key = frozenset(actions)
        if not key:
            raise StaleIndex(
                "an action-set projection was asked for with no actions — a subset that selects "
                "nothing would serve an empty list, a wrong answer in a right one's costume, so it "
                "refuses. The action-set derives from a check's founding-declared "
                "{aggregate_action, removal_action}; an empty one means the caller is off that path")
        p = self._action_set_projections.get(key)
        if p is None:
            p = self._action_set_projections[key] = ActionSetProjection(self, key)
        return p

    def key_projection(self, acct):
        """A HELD record projection over EXACTLY one account's key-lifecycle records — the subset
        keys.bound_key folds (EP-36 F1) — keyed and cached by account (KEY-PROJECTION, board
        :2906/:2910, Option A). A derived cache exactly like `record_projection` /
        `action_set_projection` above: it holds locations, is built from the record on first use
        and caught up on every read, and deleting it changes no answer — the only difference is
        that its subset is named by the account whose key binding is being read rather than by one
        of the four fixed PROJECTIONS names or an action-set.

        HELD, so the signed door (EP-37) reads the bound key through ONE cached per-account
        projection across every act — paying that account's key records per read and the
        whole-record walk only as one-time / append-incremental maintenance, never a fresh scan per
        act. That is the whole purpose of the unit: the operation-rate key read becomes a subset
        read (T-PER-ACT-PATH-READS-SUBSETS), which is what lets mover-2's SIGN-LAW land clean.

        NO EMPTY-REFUSE (deliberately unlike `action_set_projection`, whose empty set signals a
        caller off the guarded ceiling path): the account is whatever keys.bound_key was called with
        — a chain-end, a resolved invoker, or None in a world with no such account — and the fold
        reads exactly those records. A None or absent account folds to no key, IDENTICALLY in the
        projection and in the oracle; refusing it here would DIVERGE from the fold this projection
        exists to match (binding 2: the fold is the spec).

        The cache-key parameter is spelled `acct`, not `account`, ON PURPOSE: the projection-cache
        subscript below must not read as a subject-of-power table, the T-NO-STORED-TABLE tell that
        `action_set_projection` avoids by caching under `key` and `record_projection` under `name`
        (test_ep24c scans this module for a bracket-subscript on account/actor/grantee/... ). Keep
        the subscript on `acct`; do not rename it to the account word — that re-trips the guard."""
        p = self._key_projections.get(acct)
        if p is None:
            p = self._key_projections[acct] = KeyProjection(self, acct)
        return p

    def governance_index(self):
        """The law-and-grant projection, under the name EP-24B gave it."""
        return self.record_projection("authority")

    @property
    def _gov_index(self):
        """The law-and-grant projection if anything has asked for one yet, else None. ONE
        home for every projection (`_projections`) and this is a read of it, not a second
        place a projection can live — build-on-first-use is a property EP-24B tests by name,
        and a test asserting a store pays nothing until it is asked is worth keeping working."""
        return self._projections.get("authority")

    def on_append(self, fn):
        """Register a live listener (dual-audit mirrors, view invalidation).
        Listeners never mutate the record; a listener failure must not take the
        primary path down (the estate's mirror discipline)."""
        self._listeners.append(fn)

    # ---- the held descriptor and the one appender (EP-28C W1 + W3) ------------------
    def _require_fh(self):
        """The record file, opened ONCE and held. Opened on first append, never per append.

        THE RAISE THIS CLOSES (EP-28B W2, held; EP-28D verdict, carried into EP-28C W3): the
        store used to re-open the file on every append, measured in the guest at 0.10-1.80 ms
        of a 2.6-3.5 ms act. It was written and withdrawn at EP-28B because the conformance
        fixture took the descriptor number a row had just freed; EP-28D repaired the fixture
        and DROVE BOTH DIRECTIONS, so the change is safe and it lands here.

        AND THE REASON IT WAS NOT OPTIONAL, in EP-28D's own words: the instrument was
        momentarily occupying a number a row had just released, and that was invisible only
        because the descriptor's lifetime was shorter than the gap between two subject calls
        — which is a property of the store rather than a guarantee the instrument makes. A
        conformance surface passing on an accident of timing that nobody promises is a
        surface that will move without anyone changing it.
        """
        if self._fh is None:
            self._fh = self.file_path.open("a", encoding="utf-8")
            # Closed when this store is collected — IF THE NUMBER IS STILL OURS. The finalizer
            # holds the FILE, never the store, so registering it creates no reference that
            # would keep the store alive; and it carries the descriptor's IDENTITY, taken here
            # at the one moment the number is certainly ours, because a raw descriptor number
            # is not a stable identity and this call may run at an arbitrary later collection
            # point (EP-28C W4c; `_close_handle` carries the derivation).
            fd = self._fh.fileno()
            st = os.fstat(fd)
            self._finalizer = weakref.finalize(self, _close_handle, self._fh, fd,
                                               (st.st_dev, st.st_ino))
        return self._fh

    def close(self):
        """Release the held descriptor. Idempotent; a store may be closed and then read."""
        if self._finalizer is not None:
            self._finalizer()
            self._finalizer = None
        self._fh = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def _publish_one(self, sub):
        """THE DECIDING THREAD'S HALF OF THE APPEND (EP-28G W1): mint, write, flush, publish.

        WHY THE HALVES SEPARATE, in one paragraph, because the seam is the deliverable and not
        a convenience. A decide must be atomic against other decides — read the fold, decide,
        append — and the durability wait must sit OUTSIDE that atomicity or the region is the
        big lock and every batch closes at one. But the region cannot end BEFORE publication
        either: every fold reads `self.events`, so a region released at enqueue would let the
        next decide read a world without its predecessor and the race returns wearing the
        region's name. Both ends are forced, so publication and the durability wait must be
        separable calls. They are `_publish` and `_await_durable`; `_append` is still both, in
        that order, for every caller that wants today's contract.

        RUNS UNDER `_write_lock`, NEVER UNDER THE BARRIER. The mint and the write are one
        indivisible step (a `seq` handed out twice would be two records claiming one position)
        and the flush belongs with them: `os.fdatasync` is a syscall on a descriptor and is
        safe beside a concurrent write, but a Python buffer flushed from one thread while
        another writes into it is not. Moving the flush here costs one `write(2)` per record
        instead of one per batch, against a barrier that ADDENDUM L measured at 71-85% of the
        act — and it buys the barrier the right to run with no lock at all.
        """
        if self._broken is not None:
            raise self._broken
        with self._write_lock:
            depth = getattr(self._publishing, "n", 0)
            self._publishing.n = depth + 1
            try:
                f = self._require_fh()
                sub.record = self._append_one(sub.draft, f)
                # THE ECHO, computed by the APPENDER over what it actually wrote. The
                # submitter compares it against its own draft on the other side of the
                # covering sync (design/38 §1's retire-on-exact-match, as ADDENDUM 1
                # subordinates it to invariant 1).
                sub.echo = echo_digest(sub.record, sub.draft)
            except BaseException as exc:                  # noqa: BLE001 — carried to its own
                sub.error = exc                           # submitter, never to its neighbours
            finally:
                self._publishing.n = depth
        return sub

    def publishing_here(self):
        """Is this thread inside a publish? A listener that appends is, and its record rides
        the enclosing act's barrier — the pre-split behaviour, where a nested submission was
        committed inline into the outer batch and covered by its sync."""
        return getattr(self._publishing, "n", 0) > 0

    @property
    def _in_batch(self):
        """DERIVED, not stored (EP-28G W1, and P2 applied to this seam's own state). It used
        to be a per-STORE flag set around the append; the split made the publishing thread the
        one that sets it, and a per-store flag written by several threads at once is a fact
        about whichever of them ran last. It is the same question `publishing_here` answers
        and it now has ONE home — two copies of one fact drift, which this estate has now
        found four times in a week. The name is kept because it is what `tests/test_ep28h.py`'s
        per-append-reopen double reads to tell an outer batch from a nested one."""
        return self.publishing_here()

    def _commit_batch(self, batch):
        """THE ONE BARRIER, called from `commit.GroupCommit._drain` and from nowhere else.

        Every member of `batch` is ALREADY PUBLISHED — written, flushed and visible — because
        publication happens in the deciding thread (`_publish_one`). What is left is the one
        thing a batch genuinely shares: the `fdatasync` that makes all of it durable at once.
        Only after this returns may any reply be released (invariant 1, enforced in `_commit`).

        BATCHING SYNCS IS STILL NEVER COALESCING RECORDS (invariant 3). Nothing here touches a
        draft or a record; one barrier covering N individually-appended records is a barrier
        over N records, never one record standing for N acts.

        AND IT COVERS MORE THAN ITS MEMBERS, LAWFULLY. `fdatasync` makes the file's written
        data durable rather than a byte range, so this barrier covers every line written
        before it — including the nested records the mirror and the sweep appended inside
        their acts, which is exactly how they were covered before the split.

        THE REGION EXCLUSION IS ASSERTED HERE AND ON EVERY EXECUTION (EP-28G, wrong reference
        1). It is asserted at the barrier rather than checked over the region's span because
        the failure mode is invisible to a scan: not a barrier written between `gate.py`'s
        fold read and its append, but the region's lock still HELD while the barrier executes
        further down the call chain, in `commit.py`.
        """
        if self._broken is not None:
            raise self._broken
        from .gate import decide_region_held               # the region's home is `gate.py`
        if decide_region_held():
            raise RegionHeldAtBarrier(
                "the durability barrier was reached by a thread holding the decide region — "
                "the region is held across `fdatasync`, which is the big lock: one record "
                "ever in flight, every batch closed at one, single-threading rebuilt with a "
                "lock's name on it. Deciding needs a consistent fold and ordering needs a "
                "monotone seq; durability needs neither.")
        f = self._require_fh()
        try:
            os.fdatasync(f.fileno())
        except BaseException as exc:                      # noqa: BLE001 — the store is done
            raise self._poison(exc, "the record's barrier failed")
        return batch

    def _poison(self, exc, what):
        """A DURABILITY STEP THAT DID NOT COMPLETE POISONS THE STORE, and it refuses from here
        on rather than carrying on with two durability contracts (ST-A, P4). The records
        already in memory may or may not be on the disk, which is exactly the divergence a
        later append would bury.

        ONE POISON, TWO SITES, and the two are the two halves EP-28G separated: the write and
        its flush, in the deciding thread, and the barrier, in the appender. Either failing
        means the same thing — this store can no longer make the durability claim its callers
        were promised — so it is stated once and cited twice rather than written twice and
        allowed to drift."""
        self._broken = BatchFailed(
            "%s (%s: %s) — this store refuses every further append rather than continue "
            "with a durability claim it cannot make" % (what, type(exc).__name__, exc))
        self._broken.__cause__ = exc
        return self._broken

    def _verify_echo(self, sub):
        """THE SUBMITTING SIDE OF THE ECHO (design/38 §1). Recompute the hash from the draft
        this thread still holds and compare it against the one the appender sent back.

        A MISMATCH IS A LOUD STORE ERROR, NEVER A SILENT RETIRE. It runs after the covering
        sync because it confirms a record that already exists — the echo is not a gate the
        record passes through, which is exactly the ADDENDUM 1 reading that keeps the buffer
        pipeline rather than an effect-license."""
        expected = echo_digest(sub.draft, sub.draft)
        if sub.echo != expected:
            raise EchoMismatch(
                "the appended record's echo %s does not equal the submitted content's %s — "
                "record %s disagrees with the draft on a field the draft stated, and an "
                "intent whose confirmation does not match is never retired"
                % (sub.echo, expected,
                   (sub.record or {}).get("seq") if sub.record is not None else "?"))

    def _append_one(self, ev, f):
        """Mint, write, publish, and notify — for ONE record, inside the appender.

        The write is buffered into the held descriptor here and the barrier is issued once
        per batch by `_commit_batch`. THE FLUSH IS STILL BEFORE THE BARRIER AND STILL
        MANDATORY: Python buffers the write, so a barrier issued before the buffer reaches
        the kernel would sync nothing and report success — the flattering wrong answer.
        """
        record = {
            "record_id": ev.get("record_id") or f"rec_{len(self.events) + 1}",
            "seq": len(self.events) + 1,                 # total order, minted here
            "record_time": _now_iso(),                    # sole total-order anchor
            "submission_time": ev.get("submission_time") or _now_iso(),
            "occurrence_time": ev.get("occurrence_time") or _now_iso(),
            "origin": ev.get("origin") or {"subsystem_id": "kernel", "built_id": 0},
            "actor": ev["actor"],                         # AAOT actor
            "action": ev["action"],                       # a registered op (the gate)
            "object": ev.get("object"),
            "target": ev.get("target"),
            "rule_cited": ev.get("rule_cited"),           # mandatory on DECISIONs/refusals (enforced at the gate)
            "evidence_summary": ev.get("evidence_summary"),
            "provenance": ev.get("provenance")
            or {"asserted_by": ev["actor"], "source": "system", "could_read": []},
            "content_form": ev.get("content_form", "inline"),
            "refs": ev.get("refs") or [],
            "payload": ev.get("payload") or {},
        }
        if ev.get("refused"):
            record["refused"] = True
        # THE DECLARED STREAM (EP-30-W1a), carried the same way `refused` is: set only when the
        # act states one, so a record that declares nothing serialises byte-for-byte as it did
        # before this field existed. That is constraint 1, and the conditional IS the mechanism
        # rather than a tidiness — a field written unconditionally, even one holding the door's
        # own name, would move all 76 shipped records.
        #
        # IT MUST BE PASSED THROUGH HERE OR IT DOES NOT EXIST. This dict is built key by key
        # from `ev`, so an envelope key nobody names is dropped in silence (the property
        # `gate._decide` relies on when it stamps obligation_ref into the PAYLOAD instead). The
        # interpreter setting `record_stream` on its draft is therefore not enough on its own,
        # and a reader of that half alone would believe a capability that never reached a record.
        if ev.get("record_stream"):
            record["record_stream"] = ev["record_stream"]
        # THE CHAIN AND THE HONEST-DEGRADE SIGNATURES (EP-35; design/37 Q1; envelope word :2755).
        # Once the pre-existing prefix has been sealed under one chain-anchor, every NEW record
        # store-mints the grow-only proof fields the owner licensed — the EXACT set and nothing
        # wider: `prev_hash`, the canonical hash of the immediately-preceding record (self-naming
        # its algorithm in the "sha256:" prefix — the calibration id rides as DATA, no pack minted,
        # §8-h item-F bind); and the two signature fields, PRESENT-BUT-PENDING because EP-36's
        # signing vault is not yet composed (never a false signed claim, never blocking the chain).
        # CONDITIONAL exactly like record_stream/refused above: a record written before the seal
        # gains none of these and serialises byte-for-byte as it did before the fields existed, so
        # the past is byte-untouched — new-records-only, the one shape :2755 licensed (a migration
        # of the past is REFUSED permanently, §8-f/RW5). Minted here in the sanctioned appender, in
        # drain order, so `T-GATE-SOLE-APPENDER` does not change (ADDENDUM-1 item 1; §8-e).
        if self._chain_anchored():
            record["prev_hash"] = canonical_hash(self.events[-1])
            record["invoker_sig"] = SIG_PENDING
            record["store_sig"] = SIG_PENDING
        # THE SYSTEM COUNTERSIGNATURE, REACHING THE RECORD (EP-47C; design/51 N10; design/37 Q2). Once a
        # system signing key is BOUND (the boot ceremony's KEY-LAW-BIND, compose.seal_system_signer),
        # every record this store appends carries a REAL countersignature over its recording fact — or
        # the append is REFUSED. The hook is compose's `append_countersign`, attached at full compose and
        # reading the boot-seeded signer live. CONDITIONAL exactly like record_stream / prev_hash above: a
        # bare kernel (no compose) and every UNBOUND world return None and set NO key, so a record that is
        # not in the real era serialises BYTE-FOR-BYTE as it did before this field existed and the whole
        # prior ledger is untouched (A3). WHEN BOUND the mark is REAL where the vetted library is present
        # (A1) and the append is REFUSED — CeremonyNotRun (bound, ceremony not run this boot) or
        # crypto.LibraryAbsent (bound, library absent) — raised HERE, BEFORE the write, so no partial
        # record lands and NEVER a modelled mark once bound (the after-bind no-fallback, theorem 3 / N10;
        # A2). The refusal is carried to THIS submitter alone (_publish_one's per-sub error catch), never
        # poisoning the store or wedging a neighbour, so an unbound / bound-present append still lands
        # (A5 too-wedged). Gating on system_key_bound — which flips at the bind row's COMMIT, so it is
        # False during the bind row's own append — keeps the ceremony's ceremony/bind rows on the
        # byte-identical path and begins the REAL mark at the first governed append after the ceremony.
        _countersign = getattr(self, "_append_countersign", None)
        if _countersign is not None:
            _mark = _countersign(record)          # None (unbound) · real mark (bound+present) · RAISES (bound+absent/un-ceremonied)
            if _mark is not None:
                record["countersign"] = _mark
        # The append IS the commit: write the line and force it to the disk (H2) so a crash
        # cannot lose the tail; record_time/seq are already fixed, so a crash mid-write leaves
        # either a full line or none (a partial line has no closing newline and is dropped on
        # reload) — FB2's atomic-commit-at-append. Then freeze the in-memory copy (H1) so
        # stored records are read-only, and notify listeners.
        #
        # THE BARRIER IS NOW ONE PER BATCH AND STILL ONE PER RECORD'S REPLY (EP-28C W1). What
        # changed is how many records share a barrier; what did NOT change is that no reply
        # is released before the barrier covering ITS record. A batch shares a DURABILITY
        # MOMENT and never a RECORDING POSITION: `record_time` and `seq` carry order and are
        # minted per record, here, exactly as they were when every act synced alone.
        #
        # THE BARRIER IS `fdatasync` (EP-28B W2), and the reason is what the barrier is FOR.
        # `fsync` additionally forces the inode's metadata — timestamps above all — and no
        # reader of an append-only record needs the mtime to have reached the disk to read the
        # record. `fdatasync` forces the DATA and the file SIZE, which is exactly what a reader
        # needs to find the line and read it whole. The guest proved the weaker barrier
        # sufficient by cutting the power: a synced record survived 300 of 300, and the unsynced
        # case did not come back SHORT — the file did not exist at all.
        #
        # AND THE SENTENCE THAT RULES THIS, carried verbatim from W8 because it is the whole
        # frame: the sync is not a cost to trade, it is what makes the record exist. An append
        # that is not durable is not an append. So this line is not an optimisation of the
        # durability — it is the same durability, asking the disk for what it actually needs.
        # There is no `try fdatasync / except fsync` path and there must not be: a store whose
        # barrier depends on which branch it took has two durability contracts.
        #
        # THE FLUSH IS STILL FIRST AND STILL MANDATORY, and EP-28G moved it HERE, beside the
        # write it belongs to. It was issued once per batch in `_commit_batch`; the split that
        # put publication in the deciding thread and the barrier in the appender put a write
        # and a flush on two different threads' locks, and a Python buffer flushed from one
        # thread while another writes into it is not safe. Beside the write it is safe by
        # construction, it costs one `write(2)` per record against a barrier ADDENDUM L
        # measured at 71-85% of the act, and it leaves the barrier holding no lock at all.
        #
        # AND THE FAILURE OF EITHER POISONS THE STORE, exactly as a failed barrier does. The
        # flush is what puts the line in the kernel, so a flush that did not complete leaves a
        # record this store cannot claim to have written — and carrying on would be carrying
        # two durability contracts, which is the shape the barrier's own poison exists to
        # refuse. It fires BEFORE the record is frozen and published, so a record whose bytes
        # never reached the kernel is never visible to a decide. (Before EP-28G's split the
        # flush lived in `_commit_batch` and this poison covered it there; the flush moved and
        # its poison moved with it. That equivalence is not cosmetic: it is why a store whose
        # descriptor is closed underneath it still raises `BatchFailed` rather than a raw
        # `OSError`, which `tests/test_ep28d.py`'s honest-cap row reads as its answer.)
        try:
            self._fh.write(json.dumps(record, separators=(",", ":"), default=frozen_default) + "\n")
            f.flush()
        except BaseException as exc:                      # noqa: BLE001 — the store is done
            raise self._poison(exc, "the record's write did not reach the kernel")
        record = _freeze(record)  # deep read-only (H1, EP-02): frozen all the way down
        self.events.append(record)
        self._index(record)
        # PUBLISHED BEFORE THE BARRIER, ON PURPOSE (EP-28 ADDENDUM 10.7 item 1). The gate
        # decides from folds over `self.events`, so a record that was appended but not yet
        # visible here would leave the next act blind to it for the whole batch window. It is
        # visible the instant it is appended and durable the instant the barrier returns, and
        # nothing is released to any caller in between.
        for fn in self._listeners:
            fn(record)
        return record

    def _append(self, ev):
        """Append one record. `seq` and `record_time` are minted at the append (never
        supplied). `ev` needs at least `actor` and `action`; the rest of the envelope is
        optional. Returns the appended (read-only) record, and returns it only once that
        record is DURABLE — invariant 1, which is the whole safety property of group commit.

        MANY SUBMITTERS MAY BE HERE AT ONCE AND THERE IS STILL ONE APPENDER. This call
        enqueues and blocks; whichever submitter holds the appender role drains the queue,
        appends every member individually, issues one covering barrier, and then releases
        every reply. A lone caller is its own batch of one and closes it immediately, so the
        single-caller path is what it always was plus one uncontended lock.
        """
        record = self._publish(ev)
        self._await_durable()
        return record

    def _publish(self, ev):
        """THE FIRST HALF (EP-28G W1): mint, write, flush and publish, returning BEFORE the
        record is durable. Called inside the decide region; never a public contract.

        A record is visible to every fold the instant this returns, which is the property the
        region exists to preserve: act N+1's decide, entering after act N's append, reads a
        fold that CONTAINS act N even before N's covering sync. If visibility waited for the
        sync the region would protect nothing — the next decide would read a stale world and
        the race returns wearing the region's name. It is lawful because durability arrives in
        file order: anything depending on this record sits later in the same file, so if the
        dependent act ever becomes durable, so did this one (EP-28C AMENDMENT 3 §3.3).

        What that does NOT license is a reply. `_await_durable` is what a caller waits on, and
        invariant 1 is about what leaves the machine rather than about what the decide path
        may see."""
        if self.require_rule_cited and not ev.get("rule_cited"):
            raise ValueError(f"governed record '{ev.get('action')}' appended without a cited rule (H3)")
        return self.group_commit.publish(ev).record

    def _await_durable(self):
        """THE SECOND HALF (EP-28G W1): block until everything this thread published is
        durable, then verify each echo. Called OUTSIDE the decide region — the whole point.

        It waits on the LAST record this thread published, which covers the rest by prefix
        durability: the region held for the act's whole span, so this thread's records are
        contiguous in the file and a barrier covering the last covers every earlier one. It is
        a no-op when this thread is inside a publish (a listener's append rides the enclosing
        act's barrier) or inside the decide region (the region's outermost exit owns the
        wait) — which is the exclusion law expressed once, in the one place every append
        passes through, rather than restated at each call site."""
        return self.group_commit.await_pending()

    # ---- THE CHAIN AND THE ANCHOR (EP-35; design/37 Q1) ---------------------------------------
    def _chain_anchored(self):
        """Has the pre-existing prefix been sealed under a chain-anchor yet? O(1): the anchor is
        indexed like every other record. Before the seal a store mints NO chain fields — the
        new-records-only boundary read from the record itself, never a stored flag."""
        return bool(self._by_action.get(CHAIN_ANCHOR_ACTION))

    def seal_prefix(self):
        """Seal the ENTIRE pre-existing prefix under ONE chain-anchor and open the chained era.

        IDEMPOTENT (F2): a store already carrying an anchor returns it and mints no second — a
        re-run ceremony never double-seals. The anchor is a SYSTEM decision record carrying the
        canonical hash of everything before it (the whole pre-seal prefix), computed once by
        replay. From this record the past is edit-evident RETROACTIVELY — any later alteration of
        a prefix record breaks the anchor's recorded hash on recomputation — WITHOUT one old
        record being touched: append-only is absolute, and sealing writes exactly one new record.

        THE PREFIX READ IS A ONE-TIME WHOLE-RECORD PASS, OFF THE PER-ACT PATH BY CONSTRUCTION
        (ADDENDUM-1 item 2; §8-g). This is a ceremony, never a gated act, so the ADDENDUM-C guard
        (which observes whole-record reads DURING a gated act) never sees it — K12 is not offended
        and no WHOLE_RECORD_ON_PATH_BY_DESIGN row is owed (adding one would red T-NO-STALE-GUARD-ROWS,
        the read being unreachable from any representative gated act).
        """
        existing = self._by_action.get(CHAIN_ANCHOR_ACTION)
        if existing:
            return existing[0]
        prefix = list(self.events)
        boundary_seq = len(prefix)                        # the last sealed seq (0 for an empty store)
        prefix_hash = canonical_hash(prefix)              # names its algorithm in the "sha256:" prefix
        return self._append({
            "actor": "SYSTEM", "action": CHAIN_ANCHOR_ACTION, "object": "chain-anchor",
            "rule_cited": "SYS-RECORD",                   # SYSTEM records a derived fact; an existing root law
            "payload": {"kind": "chain-anchor", "prefix_hash": prefix_hash,
                        "boundary_seq": boundary_seq}})

    def verify_chain(self):
        """The derived edit-evidence check (F3; Q10's split). Recompute every link on demand,
        report how far the record verifies, and LOCATE the first break — this MINTS NOTHING, so
        replay verifies every link and re-mints none (chain fields are record data; recomputation
        is the check). A whole-record read run ON DEMAND, never on the gated per-act path.

        Returns {anchored, prefix_ok, verified_through, break_at, ok}:
          anchored         whether a seal exists (no anchor -> nothing to verify, vacuously ok);
          prefix_ok        whether the sealed prefix still hashes to the anchor's recorded value;
          verified_through the highest seq whose incoming link is intact ("verified through seq N");
          break_at         the first post-anchor seq whose `prev_hash` no longer matches its
                           recomputed predecessor (None when the chain is whole; a prefix break
                           reports prefix_ok False rather than a single seq, the anchor covering
                           the whole prefix as one hash);
          ok               the conjunction.
        """
        anchor_list = self._by_action.get(CHAIN_ANCHOR_ACTION)
        head = len(self.events)
        if not anchor_list:
            return {"anchored": False, "prefix_ok": None, "verified_through": head,
                    "break_at": None, "ok": True}
        anchor = anchor_list[0]
        a_seq = anchor["seq"]
        boundary = anchor["payload"]["boundary_seq"]
        prefix_ok = canonical_hash(self.events[:boundary]) == anchor["payload"]["prefix_hash"]
        if not prefix_ok:
            return {"anchored": True, "prefix_ok": False, "verified_through": 0,
                    "break_at": None, "ok": False}
        verified_through = a_seq
        for seq in range(a_seq + 1, head + 1):
            rec = self.events[seq - 1]
            if rec.get("prev_hash") != canonical_hash(self.events[seq - 2]):
                return {"anchored": True, "prefix_ok": True,
                        "verified_through": verified_through, "break_at": seq, "ok": False}
            verified_through = seq
        return {"anchored": True, "prefix_ok": True, "verified_through": head,
                "break_at": None, "ok": True}

    def signing_state(self, record):
        """The honest read of a record's two signature envelope fields (A10/RW6; §8-j). Until
        EP-36 composes the signing vault, a post-seal record's ONLY honest state is 'pending':
        the fields are present and assert NO signature. A record that ASSERTS a signature while
        no vault exists is a false claim ('signed' — RW6 reds on it); a pre-seal record never
        gained the fields ('unsigned-era'). The chain's edit-evidence is independent of all of
        this — `prev_hash` verification never consults a signature."""
        if "invoker_sig" not in record and "store_sig" not in record:
            return "unsigned-era"
        if record.get("invoker_sig") == SIG_PENDING and record.get("store_sig") == SIG_PENDING:
            return "pending"
        return "signed"

    # ---- replay access (asOf = up to a record-time seq) ----
    def all(self, as_of_seq=None):
        if as_of_seq is None:
            return list(self.events)
        return [e for e in self.events if e["seq"] <= as_of_seq]

    def by_action(self, action, as_of_seq=None):
        arr = self._by_action.get(action, [])
        if as_of_seq is None:
            return list(arr)
        return [e for e in arr if e["seq"] <= as_of_seq]

    def by_seq(self, seq):
        return self.events[seq - 1] if 1 <= seq <= len(self.events) else None

    # ---- THE LIVE-ROWS PREDICATE (EP-MAINT-OUTSIDE-4 R1) --------------------------------------
    # A row a LATE law overturned is NOT live. ONE mechanism, HERE in the store, read through by
    # EVERY fold that derives authority or resources (authority.grants, memory.mappings) — never a
    # per-fold standing patch and never a new rule. With an overturned grant made ABSENT by `live`,
    # the act's EXISTING authority/prerequisite check refuses on the absence (ROOT-NEG-3/-1). The
    # overturn fold itself is `reconcile.overturned_targets`, REUSED (a row overturned is a fact on
    # the record, folded once); it is imported LAZILY because the store is a LOWER layer than
    # reconcile (the module graph store<-reconcile<-gate<-store forbids a load-time import — the
    # same deferred-import discipline gate.py already uses).
    def overturned_seqs(self, as_of_seq=None):
        """The set of record seqs a late law has overturned — the standing predicate's source. Read
        through the INDEXED `by_action("OVERTURN")` SUBSET, never `all()`: the folds that apply this
        run on the per-act path, which must not read the whole record (EP-24C T-PER-ACT-PATH-READS-
        SUBSETS). Overturn rows are appended `action=="OVERTURN", kind==overturn` (reconcile.py), so
        the subset is exactly them; `overturned_targets` remains the whole-record fold for the sweep,
        which is not on the per-act path. The kind constant is read lazily to stay drift-free."""
        from . import reconcile as _reconcile   # lazy: a constant read; store is below reconcile
        out = set()
        for e in self.by_action("OVERTURN", as_of_seq):
            p = e.get("payload") or {}
            if p.get("kind") == _reconcile.OVERTURN_KIND and isinstance(p.get("target_seq"), int):
                out.add(p["target_seq"])
        return out

    def live(self, as_of_seq=None):
        """Every record NOT overturned by a late law — the rows a resource/authority fold may stand on.
        A fold reading through this can carry NO overturned act into its answer, so standing is applied
        by the store and not re-derived per fold (R1's one mechanism)."""
        overturned = self.overturned_seqs(as_of_seq)
        return [e for e in self.all(as_of_seq) if e["seq"] not in overturned]

    def find(self, pred, as_of_seq=None):
        return [e for e in self.all(as_of_seq) if pred(e)]

    def last(self, pred, as_of_seq=None):
        m = self.find(pred, as_of_seq)
        return m[-1] if m else None
