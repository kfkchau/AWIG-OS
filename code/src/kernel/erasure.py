# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel · OS-architecture
# vocabulary (blob store, custody transfer, handover ceremony, departure view); NON-GOAL: no
# offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS kernel — the HANDOVER ceremony: the ONE removal function (design/46 members 3-4).

RE-AUTHORED on the owner's fourth word (board :2856): there is NO delete function, and the
vocabulary will never contain one — CAPABILITY-ABSENCE, the strongest enforcement class. The prior
shape of this module was a standalone DESTRUCTION ceremony (kill blob bytes, keep a scar). The
owner's word STRIKES destruction as a function: information custody is CONSERVED — it moves between
hands, it is never annihilated by this system. What survives is a HANDOVER, and it is the only path
by which local bytes ever leave the store.

THE ONE REMOVAL FUNCTION, IN ORDER (design/46 member 3). On a lawful removal demand ("forget me",
"hand it over"):

    duplicate the subject chain
      -> verify it byte-to-byte (content addressing makes the check exact: the copy's hash IS
         the original's, or it is not the copy)
      -> receive the SIGNED received-custody RECEIPT from the receiving hand (actor = receiver,
         action = received-custody, object = the chain-copy's hash — the key family, EP-36, is the
         prerequisite that makes this provable: a receiver with no bound key cannot produce a
         verifiable receipt, so custody cannot 'depart' to a hand this system cannot name)
      -> remove the local blob bytes, line-by-line, EACH REMOVAL VERIFIED (the demoted removal
         tail, blobs.hand_off — reachable only here, only after the receipt verifies)
      -> the row shells stand forever as a DEPARTURE record.

RECEIPT GATES REMOVAL (design/46 member 3; §8-f of the EP). No local byte is removed until the
signed receipt is present and verifies. A ceremony without a valid receipt removes NOTHING — the
bytes stay, the transfer did not happen, custody stays here. This is the whole of the safety: the
removal is the TAIL of a proven transfer, never an act of its own.

THE DEPARTURE RECORD (design/46 member 4). The scar, re-founded: not "destroyed" but "custody
transferred" — WHAT (by hash) / TO WHOM / WHEN (the record's own minted seq + record_time) / under
WHICH rule / RECEIPT cited. The destroyed-content shape is gone with the destruction model; a
departure reveals the ACT and the receiving hand, never the handed-over bytes. Every content-
resolving view answers the DEPARTURE marker where the content lived — a positive, uniform answer,
never a crash and never None (RW4). The standing "what has departed, to whom" answer is the
DEPARTURE LEDGER, derived live from the departure records; nothing about it is stored.

RECORDS ARE UNTOUCHABLE; AUTHORITY IS NEVER ORPHANED (design/46; design/37 Q6 corollary). The
ceremony names a CONTENT HASH and moves blob BYTES; records are not content-addressed, so no
handover can reach the acts authority derives from. A target that is not a content hash is refused
at the op's own definition. Scope is full OR partial (per-blob) — content addressing gives the
granularity.

REPLAY REPRODUCES THE DEPARTED STATE (design/23 Option C). The record replays FULLY; the local
content is physically handed over; the view answers the departure. A replay `as_of` a time BEFORE
the ceremony still answers the departure, because the bytes are a fact of the physical NOW — there
are none here to reproduce. A departure applied `as_of`-bound would be the wrong reference: it
would promise to reproduce content this store no longer holds.

SHARED MACHINERY WITH EP-43 / ARC R (design/46 §3; the EP's §8-i). Recover and handover are ONE
machine in two directions: recovery brings verified chain segments IN, handover sends them OUT. The
duplicate-and-verify step is written as a free function, reusable inward, deliberately not walled
into the handover handler.

FOUNDING-MOVE HELD (OWNER GATE — MOVER 4; design/46 §3.4). The handover op, the departure-record
DECISION kind, and the removal law are NEW FOUNDING VOCABULARY whose CREATE rides the owner's
fourth serial mover, behind the key family, the signing law, and the attestation flip. This module
is built and proven NOW in TEST founding worlds where the handover law is declared and the op
registered (test keys sign the test receipt); PRODUCTION `founding-pack.json` stays BYTE-UNTOUCHED
until the mover, at which point A6/§A57 flip live as a mechanical completion. The mechanism is INERT
until then: a world that declares no handover ceremony can hold no departure record, so
`departed_hashes` folds to the empty set and every content-resolving view answers exactly as it did
before this module — the same wire-at-birth safety `key_law_live` gives the key leash.
"""

import hashlib

from kernel.canonical import canonical_hash   # the estate's one hash form; the chain head at a
#                                               seq IS canonical_hash of that record (store.py:1044).
#                                               canonical is an import-leaf (hashlib/unicodedata
#                                               only), so this top-level import opens no cycle — the
#                                               recover direction needs it to adjudicate a target head.

# ---- the handover vocabulary (all in the ONE stream, class-tagged; design/37 §4) -------------
# The DEPARTURE record DECISION kind — the custody-transferred marker record, carried as the
# payload's class tag. The departed-hash fold recognises a departure by THIS tag, never by a
# hard-coded action-name list (the active_rules recognition precedent), so a departure is read
# however its op was spelled.
DEPARTURE_RECORD = "departure-record"

# The handover ceremony op name (registered in a test world; the production create is HELD, MOVER
# 4). This is the ONE removal function — NOT a standalone delete.
HANDOVER_OP = "HANDOVER-CUSTODY"

# The receiving hand's receipt action — the signed received-custody row (actor = receiver). Its
# signature, verified under the receiver's bound key (EP-36), is what gates the removal.
RECEIVED_CUSTODY = "received-custody"

# The rule_id the founding handover LAW declares — cited by a lawful departure record. Declared in
# a test world (the founding-moved stand-in); absent from production until the owner's mover.
HANDOVER_LAW = "HANDOVER-LAW-GS13"

# The constitutional anchor the ceremony's refusals cite. Cannot-orphan is the SAME root-authority
# law the succession/key leashes cite: root authority is never orphaned and the ceremony can never
# reach a record (design/37 Q6 derives cannot-orphan FROM this anchor). Reusing it keeps the
# refusal honest — this is an authority-anchor matter.
HANDOVER_ANCHOR = "CONST-AUTHORITY-ANCHORED"

# Departure payload field names + the §4 class tag.
CLASS = "class"
TARGET_HASH = "target_hash"       # WHAT departed, by hash
RECEIVER = "receiver"             # TO WHOM custody passed
RETENTION_RULE = "retention_rule" # under WHICH rule
RECEIPT_CITED = "receipt_cited"   # the receiving hand's receipt, CITED (never the bytes)

# The estate's invoker-signature envelope field name (gate.INVOKER_SIG). Named here as a literal so
# a receipt can be recognised without importing the gate at module load; the CRYPTOGRAPHIC verify
# is done through the gate's own `verify_invoker_sig`, lazily (see `_receipt_verifies`).
INVOKER_SIG = "invoker_sig"

# THE DEPARTURE MARKER — the one uniform answer every content-resolving view gives for a departed
# hash (replaces the destruction model's scar). A well-known, self-identifying marker: NOT the
# bytes (handed over, gone locally), NOT empty (that is a legitimately empty file), NOT a crash.
# Every site substitutes THIS for the departed content, so a departed read is recognisable by one
# constant and the standing "what departed, to whom" answer is the DEPARTURE LEDGER
# (`departure_ledger`), which reads the departure records. Bytes so no site's return type changes.
DEPARTURE = b"\x00gov-os:content-departed-by-handover\x00"

# The op definition a test world registers. `receiver` and `retention_rule` are REQUIRED at the
# param level, so a handover without a named receiving hand or a cited rule is refused as a
# nonconforming call BEFORE the handler runs — the structural half of "custody moves to a named
# hand, under a rule, never to disk". The domain gates (cannot-orphan, duplicate-verify, the
# receipt) run inside the handler, at the op's own definition.
OP_META = {
    "description": "the handover ceremony — the one removal function: transfer custody to a "
                   "receiving hand under a signed receipt, then remove the local bytes",
    "rules": [HANDOVER_LAW],
    "params": {TARGET_HASH: "required", RECEIVER: "required", RETENTION_RULE: "required"},
}


def is_departed(x):
    """Is `x` the departure marker? The one recogniser a reader or a test uses; the marker is a
    value, never a type, so equality is the whole check."""
    return x == DEPARTURE


def _is_content_hash(x):
    """Does `x` name a blob — a content hash 'sha256:<hex>'? The cannot-orphan discriminator at the
    op's own definition: a record reference (a seq, a record_id, a path) is not a content hash and
    is refused, so the ceremony's target keyspace is the blob store's and nothing else."""
    return isinstance(x, str) and x.startswith("sha256:") and len(x.split(":", 1)[1]) > 0


# ---- the departure, DERIVED live from the departure records (nothing stored) ------------------

def departed_hashes(events):
    """The set of content hashes whose custody has DEPARTED by a recorded handover — a FOLD over
    the departure records, recognised by the payload's class tag. `events` is ANY iterable of
    record dicts: a store fold (`store.all()`), an action-scoped projection, or the raw records
    list the replay leg already holds — so the three content-resolving views and the replay leg
    share ONE derivation of the departure.

    NO `as_of`. A departed hash is departed for every reader, past or present, because the local
    bytes are physically gone NOW; a replay of an earlier state still cannot produce them (design/23
    Option C). Callers therefore pass the WHOLE record, never an as-of slice, for the departure."""
    out = set()
    for e in events:
        p = e.get("payload") or {}
        if p.get("kind") == DEPARTURE_RECORD:
            h = p.get(TARGET_HASH)
            if h:
                out.add(h)
    return out


def departure_ledger(events):
    """The standing answer to 'what has ever departed, and to whom' — every handover with its
    receiver, its retention rule, its cited receipt, and when (the record's own minted seq /
    record_time). Derived from the departure records in record order; the handed-over content is
    absent by construction, so the ledger reveals the ACT and the receiving hand and never the
    content. This is the departure VIEW; the content-resolving views return the DEPARTURE marker,
    this one names each departure."""
    ledger = []
    for e in events:
        p = e.get("payload") or {}
        if p.get("kind") == DEPARTURE_RECORD:
            ledger.append({
                TARGET_HASH: p.get(TARGET_HASH),
                RECEIVER: p.get(RECEIVER),
                RETENTION_RULE: p.get(RETENTION_RULE),
                RECEIPT_CITED: p.get(RECEIPT_CITED),
                "seq": e.get("seq"),
                "record_time": e.get("record_time"),
            })
    return ledger


# ---- the ceremony's steps 1-2, shared with the recover direction (EP-43) ----------------------

class HandoverHalt(Exception):
    """A step of the ceremony did not complete, so the ceremony HALTS before any byte is removed.
    Raised by `duplicate_and_verify` and caught at the op's own definition, where it is turned into
    a recorded refusal (the record never goes dark)."""


def duplicate_and_verify(blobs, target_hash):
    """Steps 1-2 of the handover: DUPLICATE the subject content and VERIFY the copy byte-to-byte.

    Content addressing makes the verification exact and cheap: re-read the local bytes, recompute
    their hash, and confirm it equals the named hash — the duplicate the receiver carries is proven
    identical to the original by hash IDENTITY, which is the strongest byte-to-byte check there is.
    Returns the CHAIN-COPY HASH (the receiver's handle, named in the receipt). Raises `HandoverHalt`
    if the bytes are absent or do not verify: a corrupt or missing original is never handed over as
    if whole, and the ceremony halts before any removal.

    SHARED MACHINERY WITH EP-43 / ARC R (design/46 §3): recover and handover are one machine, two
    directions — this same duplicate-and-verify a recovery runs INWARD, run here OUTWARD. Kept a
    free function, not walled into the handler, so the recover direction can call it."""
    try:
        data = blobs.get(target_hash)
    except FileNotFoundError as e:
        raise HandoverHalt(
            "the subject content %s is not in the local store — there is nothing to duplicate, so "
            "the handover halts before any removal" % target_hash) from e
    recomputed = "sha256:" + hashlib.sha256(data).hexdigest()
    if recomputed != target_hash:
        raise HandoverHalt(
            "the subject chain did not verify byte-to-byte: the local bytes for %s recompute to %s "
            "— the duplicate is not proven identical, so the handover halts before any removal"
            % (target_hash, recomputed))
    return target_hash                    # the chain-copy hash (content-addressed)


# ---- step 3: the receiving hand's SIGNED received-custody receipt (EP-36 keys) ----------------

def _receipt_signed_body(receipt):
    """The canonical body the receiving hand signed over — the received-custody act's caller-
    controlled content, matched EXACTLY to what `gate.make_invoker_sig` signs (action / object /
    target / payload). The gate-added and store-minted fields are excluded, so signer and verifier
    cannot drift (the round-trip property, Q10)."""
    return {"action": receipt.get("action"), "object": receipt.get("object"),
            "target": receipt.get("target"), "payload": receipt.get("payload") or {}}


def _receipt_verifies(gate, receipt, receiver, chain_copy_hash):
    """Step 3: does the receiving hand's SIGNED received-custody receipt verify? RECEIPT GATES
    REMOVAL — this is the check that stands between a ceremony and a removed byte. True iff:

      - it is a received-custody row  (action == RECEIVED_CUSTODY),
      - from the named receiver        (actor == receiver),
      - naming EXACTLY the chain-copy hash the duplicate produced (object == chain_copy_hash),
      - and its signature verifies under the receiver's key BOUND at the founding (EP-36
        `keys.bound_key` — the KeyProjection surface, NOT re-implemented here): the receiver signed
        the receipt with a key this system can verify — provable BECAUSE keys exist. A receiver
        with no bound key cannot produce a verifiable receipt, so custody cannot 'depart' to a hand
        this system cannot name.

    A check that cannot fail is not a check (RW2): any missing or mismatched field, or an unbound
    receiver, returns False and the ceremony halts before removal. The key surface is imported
    LAZILY (at ceremony time, well after module load) so this kernel module carries no import
    cycle through the gate/keys."""
    if not isinstance(receipt, dict):
        return False
    if receipt.get("action") != RECEIVED_CUSTODY:
        return False
    if receipt.get("actor") != receiver:
        return False
    if receipt.get("object") != chain_copy_hash:
        return False
    from kernel import keys                       # EP-36 surface; lazy, no cycle
    from kernel.gate import verify_invoker_sig    # EP-37 surface; lazy, no cycle
    receiver_key = keys.bound_key(gate.store, receiver)
    if receiver_key is None:
        return False
    return verify_invoker_sig(receipt.get(INVOKER_SIG), receiver_key, _receipt_signed_body(receipt))


def _receipt_citation(receipt):
    """A DEPARTURE record CITES the receipt (design/46 member 4: 'receipt cited'), never embeds the
    handed-over bytes: the receiver, the chain-copy hash they now hold, and the signature's bound
    hash — all PUBLIC proof-of-receipt, nothing the ceremony was asked to forget."""
    receipt = receipt or {}
    sig = receipt.get(INVOKER_SIG) or {}
    return {RECEIVER: receipt.get("actor"),
            "chain_copy_hash": receipt.get("object"),
            "signed_over": sig.get("over") if isinstance(sig, dict) else None}


# ---- the ceremony op: transfer custody, then remove the local bytes (design/46 member 3) ------

def handover_handler(gate, blobs, views):
    """The handover ceremony's handler — built HERE so the production op, when the mover lands, is
    this exact logic. Registered on a kernel whose founding declares the handover law; INERT in a
    world that never registers it (no op, no departure record, no departed hash).

    It performs, IN ORDER, the one removal function of a custody-conserving system, refusing at the
    op's own definition (a recorded refusal, never a silent no-op) the moment any step does not
    hold, and REMOVING NO BYTE until the signed receipt has verified:

        cannot-orphan  ->  duplicate + verify  ->  receipt verifies  ->  remove  ->  departure

    The gate performs the one append (the sole-appender law), so the departure record is minted
    with its seq/record_time — the 'when' — like any record. The removal precedes the append, so
    the departure is written only after the effect it attests is real (blobs.py's ordering law,
    read the other direction): a departure can never claim an un-happened transfer."""
    def _handover(actor, params):
        target = params.get(TARGET_HASH)
        receiver = params.get(RECEIVER)
        rule = params.get(RETENTION_RULE)
        receipt = params.get("receipt")

        # CANNOT ORPHAN / RECORDS UNTOUCHABLE (design/46; §8-g). The ceremony reaches content-
        # addressed blob BYTES only. A target that is not a content hash — a record reference of any
        # shape — is refused here, at the op's own definition: authority is derived from records, and
        # this op can never name one, so it can never orphan authority.
        if not _is_content_hash(target):
            gate.refuse(actor, HANDOVER_OP, HANDOVER_ANCHOR,
                        "a handover moves content-addressed blob BYTES only — it can never reach a "
                        "record, so it can never orphan authority (records are untouchable)")

        # STEP 1-2: duplicate the subject chain, verify byte-to-byte. A missing or unverified step
        # HALTS the ceremony before any byte is removed (nothing is handed over as if whole).
        try:
            chain_copy_hash = duplicate_and_verify(blobs, target)
        except HandoverHalt as e:
            gate.refuse(actor, HANDOVER_OP, HANDOVER_ANCHOR, str(e))

        # STEP 3: RECEIPT GATES REMOVAL. No local byte is removed until the receiving hand's signed
        # received-custody receipt is present and verifies (the key family makes it provable). A
        # ceremony without a valid receipt removes NOTHING — custody stays here.
        if not _receipt_verifies(gate, receipt, receiver, chain_copy_hash):
            gate.refuse(actor, HANDOVER_OP, HANDOVER_ANCHOR,
                        "no valid received-custody receipt from the receiving hand — the receipt is "
                        "the gate: no receipt, no removal, custody stays here (nothing departed)")

        # STEP 4-5, IN THE ORDER DECIDE -> EFFECT -> APPEND (EP-MAINT-OUTSIDE-1 B1; §2's principle).
        # The handler here PROPOSES: it builds the departure DRAFT and defers the irreversible byte
        # removal as the gate's EFFECT, run AFTER the gate's decide passes have decided this draft
        # and BEFORE the append. Performing hand_off inline (as it did) removed the bytes before the
        # gate's own rules pass could refuse the act — so a standing rule that refused HANDOVER at
        # the gate left the effect already real (a refused act with an effect). Deferring keeps
        # erasure.py:296's law WHOLE: the removal still precedes the append, so the departure never
        # attests an un-happened transfer; it only moves the removal to AFTER the decision. The gate
        # runs `blobs.hand_off([target], receipt)` at the reserved key, then appends this draft.
        from kernel.gate import IRREVERSIBLE_EFFECT             # lazy: no import cycle (as elsewhere here)

        # STEP 5: the DEPARTURE record (design/46 member 4). WHAT (by hash) / TO WHOM / WHEN (the
        # record's own minted seq + record_time) / under WHICH rule / RECEIPT cited — the handed-over
        # CONTENT absent by construction (the departure reveals the act and the receiving hand, never
        # the bytes). Its store countersignature is the envelope addition every record carries (EP-36
        # keys.countersign); this op mints no signature of its own.
        draft = {"actor": actor, "action": HANDOVER_OP, "object": target,
                 "rule_cited": HANDOVER_LAW,
                 "payload": {"kind": DEPARTURE_RECORD, CLASS: "DECISION",
                             TARGET_HASH: target, RECEIVER: receiver, RETENTION_RULE: rule,
                             RECEIPT_CITED: _receipt_citation(receipt)}}
        # STEP 4 (the demoted transfer TAIL, blobs.hand_off) DEFERRED as the gate's irreversible
        # effect: the bytes leave this store only after the gate decides, because another named hand
        # provably holds them AND no standing rule refused the act.
        draft[IRREVERSIBLE_EFFECT] = lambda: blobs.hand_off([target], receipt)
        return draft
    return _handover


def register_ceremony(gate, views):
    """Wire the handover ceremony onto a kernel that has a blob store (`gate.blobs`, set when the
    full kernel composes). The reusable registration BOTH a test founding world and — when the
    owner's mover lands — the production compose call. A gate with no blob store cannot move
    content, so the op stays unregistered there, exactly as content ops do (content_ops_pending_
    blobs). Production `build_kernel` does NOT call this: the create is HELD (MOVER 4), so
    production carries no handover op and every departure view stays inert."""
    blobs = getattr(gate, "blobs", None)
    if blobs is None:
        return False
    gate.register(HANDOVER_OP, OP_META, handover_handler(gate, blobs, views))
    return True


# ============================================================================================
# THE RECOVER CEREMONY — the INWARD direction (EP-43; ARC R, the genesis-guardian family;
# design/46 §3, design/37 §5/:824, design/47 §3). THE CRUX.
#
# Recover and handover are ONE machine, two directions (design/46 §3): a handover sends verified
# chain segments OUT; a RECOVER brings them IN — waking a damaged system to an OLDER SOUND point
# (design/47 §3: recovery is "waking damaged"). This is destruction's mirror twin (design/37 :794):
# damaged segments healed by candidates gathered from replicas / firmware / full-fidelity
# projections, ACCEPTED ONLY BY THE CHAIN (a candidate rehashes into the sealed chain or it is
# refused), and SPLICED only by an owner-gated recorded act — a signed splice proving WHAT was
# restored, FROM WHICH sources, AGAINST WHICH anchor. NEVER automatic; views are NEVER authoritative
# (an auto-repair door is a laundering door; a view-driven repair inverts the truth hierarchy).
#
# It REUSES `duplicate_and_verify` (the free function above, kept free "so the recover direction can
# call it") to verify each candidate segment AT LOAD, and it MIRRORS the handover's owner-gate +
# cannot-orphan refusal pattern, citing the SAME constitutional anchor. Four laws hold it (the EP's
# A2-A5):
#
#   NEVER TO WRONGNESS (A2). The target must be a LAWFUL PRIOR POINT of THIS chain — a point whose
#     head the record itself once held. A fabricated head, or a state the record never lawfully
#     held, matches no record and is REFUSED at the anchor. The laundering-door stays shut: recover
#     installs only a past the record HELD, never one it did not.
#   CHAIN-ADJUDICATED (A3/RW4). Soundness is decided by the chain's OWN fold (`store.verify_chain`
#     -> verified_through / break_at), never by a stored flag. A target beyond the break is refused;
#     a target within the verified prefix is admitted. Break the chain BEFORE a target and the SAME
#     target flips from admitted to refused with no flag touched — the fold adjudicates.
#   VERIFY AT LOAD (A4/RW2). The recovered state's content is RE-READ and HASHED at load
#     (`duplicate_and_verify` inward), never trusted from the checkpoint's say-so. A corrupt or
#     missing segment HALTS the recover (the HandoverHalt pattern, inward), restoring nothing.
#   OWNER-GATED (A5/RW3). Only the ROOT AUTHORITY HOLDER (the chain-end, DERIVED — never a hardcoded
#     "owner") drives a recover splice; a non-owner recover is refused at the anchor.
#
# RECOVER NEVER TRUNCATES (archi's countersign, board :3024, load-bearing). The splice APPENDS one
# recover record; rows past `break_at` STAY IN THE FILE as adjudicated-broken history; the served
# state comes from the checkpoint the record CITES (held once, never duplicated — design/47 §4)
# gated by the verified segments; NO row is removed, rewritten, or shortened. A recover that
# shortens the file would be the one delete function :2856 forbids — it cannot happen here, because
# this op's ONLY write is the gate's single append of the recover record.
#
# LAYERING (§8-g). The kernel op takes the target head as a caller-supplied PARAM: the caller reads
# the bridge checkpoint (EP-44) for its pinned `chain_head` and passes it in. The kernel never
# imports the bridge checkpoint.
#
# FOUNDING-MOVE HELD (§8-f). The recover op is NEW founding vocabulary whose CREATE is owner-gated
# and HELD (the recovery-CAPACITY law is EP-45's, not here). This module is built and proven NOW in
# TEST founding worlds where the recover law is declared and the op registered (`register_recover`);
# PRODUCTION `founding-pack.json` stays BYTE-UNTOUCHED until the mover, and production compose never
# calls `register_recover` — the recover op is absent from every production world (A6/§A57 flip live
# on the owner's word). Inert until then, exactly as the handover create was.
# ============================================================================================

# The RECOVER splice DECISION kind — the marker record for a recover, mirroring DEPARTURE_RECORD.
# The recover fold recognises a splice by THIS tag, never by a hard-coded op-name list.
RECOVER_RECORD = "recover-record"

# The recover ceremony op name (registered in a TEST world; the production create is HELD). This is
# a SPLICE to an older sound point — NOT an in-place repair and NOT a delete.
RECOVER_OP = "RECOVER-TO-CHECKPOINT"

# The rule_id the founding recover LAW declares — cited by a lawful recover record. Declared in a
# test world (the founding-moved stand-in); absent from production until the owner's mover.
RECOVER_LAW = "RECOVER-LAW-GS14"

# The recover cites the SAME constitutional anchor as the handover. NEVER-TO-WRONGNESS and the
# owner-gate are both authority-anchor matters: root authority is never orphaned, and recover can
# install only a point the record lawfully HELD. One anchor, both directions of the one machine.
RECOVER_ANCHOR = HANDOVER_ANCHOR                  # "CONST-AUTHORITY-ANCHORED"

# Recover payload field names + the §4 class tag.
TARGET_HEAD = "target_head"              # WHAT point was restored, by its chain-head hash (the seq's record)
TARGET_SEQ = "target_seq"               # the seq the chain ADJUDICATES that head at (DERIVED, never passed)
CHECKPOINT_REF = "checkpoint_ref"       # FROM WHICH source — the checkpoint cited, by its own hash
SEGMENTS_VERIFIED = "segments_verified" # the content segments RE-READ and hashed at load (verify-at-load)
ADJUDICATION = "adjudication"           # AGAINST WHICH anchor — the chain fold's verdict at recover time
RECOVER_RULE = "recover_rule"           # under WHICH rule the recovery was demanded

# THE FOUR ROW FIELDS THE SPLICE MUST CARRY (board :3049, the owner's verbatim requirement, a
# by-name precision to the frozen plan — no re-hash; the plan already bound "a signed splice proving
# WHAT was restored, FROM WHICH sources, AGAINST WHICH anchor" (design/37 :798), and :3049 names the
# four facts a recover row makes explicit so the row proves itself). A recover row WITHOUT all four
# is a STOP under §7(c). They are:
#   (1) what region BROKE       — break_at + the broken range (break_at .. head)
#   (2) what was SOUND          — verified_through
#   (3) what was DONE           — the checkpoint hash + every segment brought in, each BY HASH
#   (4) what HAPPENED           — the outcome: verified-at-load (this row), or HALTED with the
#                                 failing segment named (the refusal, which restores nothing — a
#                                 halt writes no splice, the handover-halt pattern inward, §8-h)
BREAK_AT = "break_at"                    # (1) the first post-anchor seq whose link broke (None if whole)
BROKEN_RANGE = "broken_range"           # (1) [break_at, head] — the seqs past the sound point (None if whole)
VERIFIED_THROUGH = "verified_through"   # (2) the highest seq the chain adjudicates as intact
OUTCOME = "outcome"                     # (4) verified-at-load (on the splice) — the halt is a refusal
OUTCOME_VERIFIED_AT_LOAD = "verified-at-load"
OUTCOME_HALTED = "halted"               # the halt outcome, named in the refusal (never a splice row)

# THE AUTO-TRIGGER (EP-43-AUTO; ARC R; owner ruling :3057; the fail-safe SECOND trigger). Recover
# already carries ONE trigger — the manual owner-gated act (design/37 §5, "never automatic"). This
# adds a SECOND: an AUTO recover under a TRIPLE CHECK, refined from "never automatic" to "automatic
# ONLY under a triple check that halts on any doubt" (a STRICTER gate than manual; avoid-fail beats
# maximize-success — nuclear-plant-grade, the owner's words). The three checks are COMPOSED IN THE
# BRIDGE (`bridge/auto_recover.py`): (1) the chain adjudicates the target sound — THIS op's own
# never-to-wrongness, unchanged (the laundering-door stays shut); (2) the checkpoint's pinned head
# matches the live head (`bridge/checkpoint.check_head`, EP-44); (3) the buddy mutual-receipt verifies
# (`bridge/checkpoint.pairing_verdict`, EP-45). The KERNEL never imports the bridge (layering, §8-h):
# it receives the bridge's three-check OUTCOME as opaque DATA, records it on the splice, and re-runs
# its OWN chain check regardless of trigger. The manual owner-gated path is UNCHANGED — with no
# trigger the handler runs exactly as EP-43 built it and the row carries none of these keys (additive).
TRIGGER = "trigger"                     # "auto" on an auto splice; ABSENT on the manual owner-gated path
TRIGGER_AUTO = "auto"
TRIPLE_CHECK = "triple_check"           # the bridge's three-check outcome {chain, checkpoint, buddy}, recorded on an auto splice
TRIPLE_CHECK_MEMBERS = ("chain", "checkpoint", "buddy")   # all three, or an auto call is malformed (RW1)

# The op definition a test world registers. `target_head`, `checkpoint_ref` and `recover_rule` are
# REQUIRED at the param level, so a recover without a named point, a named source, or a cited rule is
# refused as a nonconforming call (AR-2) BEFORE the handler runs — the structural half of "recover
# to a NAMED lawful point, from a NAMED source, under a rule". The domain gates (owner, adjudication,
# verify-at-load) run INSIDE the handler, at the op's own definition, each a recorded refusal.
RECOVER_OP_META = {
    "description": "the recover ceremony — the inward direction: wake a damaged record to an older "
                   "SOUND point the chain adjudicates as intact, owner-gated, verified at load, "
                   "never to a state the record never lawfully held (the laundering-door shut)",
    "rules": [RECOVER_LAW],
    # THE AUTO-TRIGGER FIELDS, DECLARED OPTIONAL (EP-FND-RECOVER-AUTO-LIVE; owner ruling :3057; the flip
    # made LIVE per archi :3150, BOTH fields). The handler ALREADY reads (:547-548) and records (:656-657)
    # them; declaring them here makes them the op's OWN classified vocabulary rather than payload it reads
    # undeclared, so the owner's auto-recover is live as DECLARED LAW. Absent on the manual owner-gated path
    # (`trigger` None), so a manual call omits both and runs exactly as EP-43 built it (additive). No handler
    # logic changes; the recover op is code-registered (compose.py:85), so NO founding bump (the :3069 split).
    "params": {TARGET_HEAD: "required", CHECKPOINT_REF: "required", RECOVER_RULE: "required",
               TRIGGER: "optional", TRIPLE_CHECK: "optional"},
    # BOTH auto-trigger fields are STRUCTURAL (the vocabulary door, design/46 member 2; opdefs
    # STRUCTURAL_PARAMS): `trigger` a marker scalar ("auto"), `triple_check` a dict of three booleans
    # {chain, checkpoint, buddy} — governance markers carrying no reachable content, safe inline. Classified
    # so the door admits them (archi :3150). No CONTENT field, no new op, no new check kind, no founding bump.
    "structural_params": [TRIGGER, TRIPLE_CHECK],
}


def is_recover(x):
    """Is `x` a recover record's payload kind? The one recogniser a reader or a test uses."""
    return isinstance(x, dict) and x.get("kind") == RECOVER_RECORD


def _seq_of_head(store, head):
    """The seq whose record hashes to `head`, or None. THE CHAIN'S OWN ADJUDICATION OF WHETHER A
    TARGET IS A LAWFUL PRIOR POINT: the chain head at seq S IS `canonical_hash` of the record at
    seq S (store.py:1044 pins the same value on the next record's prev_hash). A head that matches
    no record is a point this chain NEVER HELD — the never-to-wrongness discriminator, decided by
    recomputation over the record, never by a stored flag. Searched from the tail so the common
    case (a recent checkpoint) resolves fast; the search is exhaustive, so a fabricated head returns
    None deterministically."""
    if not (isinstance(head, str) and head.startswith("sha256:") and len(head.split(":", 1)[1]) > 0):
        return None
    events = store.events
    for i in range(len(events) - 1, -1, -1):
        if canonical_hash(events[i]) == head:
            return i + 1                              # seq is 1-indexed (events[i] is the record at seq i+1)
    return None


def recovered_point(events):
    """The point this record was last recovered TO — the last recover splice's {target_head,
    target_seq, checkpoint_ref}, or None where none stands. A FOLD over the recover records,
    recognised by the payload's class tag (the `departed_hashes` precedent). The recovered STATE is
    the checkpoint this point cites (held once in the checkpoint artifact, never duplicated into the
    record); this names WHICH point the estate woke to. NO `as_of`: a recover is a fact of the
    physical NOW like a departure — the latest recover splice is the standing waking-point."""
    point = None
    for e in events:
        p = e.get("payload") or {}
        if p.get("kind") == RECOVER_RECORD:
            point = {TARGET_HEAD: p.get(TARGET_HEAD), TARGET_SEQ: p.get(TARGET_SEQ),
                     CHECKPOINT_REF: p.get(CHECKPOINT_REF), "seq": e.get("seq")}
    return point


def recovered_points(events):
    """ALL LIVE recover splices — the set whose adjudicated-broken tails the served fold must skip the
    UNION of (A-2; EP-MAINT-OUTSIDE-2). `recovered_point` (singular, above) keeps only the LATEST
    splice, so a fold that skips one tail REPLAYS an earlier broken tail whenever a later recovery woke
    to a point AFTER the earlier splice — two disjoint breaks, only the second skipped. This returns
    every LIVE splice so the fold skips the union of their tails. `recovered_point` is UNCHANGED for
    its callers; this is the additive plural the fold now reads.

    LIVENESS. A later recovery that wakes to a point BEFORE an earlier splice re-adjudicates that
    range, so the earlier splice's OWN record sits inside the later's broken tail and is superseded —
    not live. Only a LATER splice can supersede an earlier one (an earlier tail (T,S] can never reach a
    later splice's seq, which is > S), so liveness is one backward walk from the latest: the latest
    splice is always live; an earlier one is live only when its own seq is not inside an already-
    collected live tail. Splices with no adjudicated target seq or no minted seq are not fold-actionable
    and are excluded (as `custody.fold` already required of the singleton). Returned in seq order, each
    a dict shaped like `recovered_point`'s."""
    splices = []
    for e in events:
        p = e.get("payload") or {}
        if p.get("kind") == RECOVER_RECORD and p.get(TARGET_SEQ) is not None and e.get("seq") is not None:
            splices.append({TARGET_HEAD: p.get(TARGET_HEAD), TARGET_SEQ: p.get(TARGET_SEQ),
                            CHECKPOINT_REF: p.get(CHECKPOINT_REF), "seq": e.get("seq")})
    splices.sort(key=lambda s: s["seq"])
    live = []
    for s in reversed(splices):                                     # latest first
        if not any(l[TARGET_SEQ] < s["seq"] <= l["seq"] for l in live):
            live.append(s)                                          # not inside a later live tail -> live
    live.sort(key=lambda s: s["seq"])
    return live


def recover_handler(gate, blobs, views):
    """The recover ceremony's handler — built HERE so the production op, when the mover lands, is
    this exact logic. Registered on a kernel that declares the recover law; ABSENT from a world that
    never registers it (production compose never calls `register_recover`, so no recover op exists,
    no recover record can be minted, and `recovered_point` folds to None — the wire-at-birth safety).

    It performs, IN ORDER, refusing at the op's own definition (a recorded refusal, never a silent
    no-op) the moment any law does not hold, and APPENDING EXACTLY ONE record — the splice — and
    truncating/rewriting/deleting NOTHING:

        owner-gate  ->  chain-adjudicate the target (never to wrongness)  ->  verify segments at
        load  ->  APPEND the recover splice (what / from-where / against-which-anchor)

    The gate performs the one append (the sole-appender law), so the splice is minted with its
    seq/record_time. The broken rows past `break_at` stay in the file as adjudicated history."""
    def _recover(actor, params):
        target_head = params.get(TARGET_HEAD)
        checkpoint_ref = params.get(CHECKPOINT_REF)
        rule = params.get(RECOVER_RULE)
        segments = params.get("segments") or []
        # THE AUTO-TRIGGER, optional (EP-43-AUTO). Absent -> the manual owner-gated path, unchanged.
        # Present -> the bridge orchestrator's three-check OUTCOME (opaque data; the kernel imports no
        # bridge and re-verifies nothing about checkpoint/buddy — that is the bridge's, §8-h layering).
        trigger = params.get(TRIGGER)
        triple_check = params.get(TRIPLE_CHECK)

        # OWNER-GATE (A5/RW3). Only the ROOT AUTHORITY HOLDER — the chain-end, DERIVED (EP-18), never
        # a hardcoded "owner" — drives a recover splice. Recovery is the root's owner-gated act
        # (design/37 :798: "spliced only by an owner-gated recorded act"); a non-owner recover is
        # refused at the anchor. The check is INSIDE the handler (the ceremony pattern): under
        # founding openness the gate's authority step would pass everyone, so the gate alone does not
        # gate this — the anchor does, here, at the op's own definition.
        ce = views.chain_end()
        if actor not in (ce, "SYSTEM"):
            gate.refuse(actor, RECOVER_OP, RECOVER_ANCHOR,
                        "only the root authority holder may drive a recover splice — recovery is the "
                        "root's owner-gated recorded act (never automatic, never a view; the "
                        "laundering-door direction stays closed)")

        # THE AUTO-TRIGGER GATE (EP-43-AUTO; owner ruling :3057; §8-f, additive; RW1). The manual
        # owner-gated path is UNTOUCHED: with no trigger the handler proceeds exactly as EP-43 built
        # it. When the caller drives the AUTO trigger the splice MUST carry a triple-check outcome with
        # ALL THREE checks passing — an auto splice on a two-of-three (or a malformed / absent) triple
        # check is REFUSED here (nuclear-plant-grade is not a vote; the manual owner-gated path is the
        # fallback). The three checks are COMPOSED in the bridge; the kernel reads the outcome as DATA
        # and imports no bridge module — this is a kernel-side backstop, never the bridge's job moved
        # down. The chain's own never-to-wrongness runs below regardless of trigger, unchanged.
        if trigger == TRIGGER_AUTO:
            if not (isinstance(triple_check, dict)
                    and all(triple_check.get(k) is True for k in TRIPLE_CHECK_MEMBERS)):
                gate.refuse(actor, RECOVER_OP, RECOVER_ANCHOR,
                            "an AUTO recover must carry a triple-check outcome with the chain, "
                            "checkpoint and buddy checks ALL passing — a two-of-three, malformed, or "
                            "absent triple check does not reach the auto trigger (nuclear-plant-grade "
                            "is not a vote); the manual owner-gated recover is the fallback")

        # NEVER TO WRONGNESS (A2) + CHAIN-ADJUDICATED (A3/RW4). The chain's OWN fold decides
        # soundness — never a stored flag. First: does the target name a record this chain ever
        # held? A head matching no record is a state that NEVER LAWFULLY EXISTED — refused at the
        # anchor, the laundering-door shut. Then: is that point within the verified prefix the chain
        # adjudicates as intact? A point at or below `verified_through` is sound; a point beyond the
        # break is refused. Break the chain before a target and the SAME target flips to refused —
        # the fold adjudicates, nothing about soundness is stored.
        fold = gate.store.verify_chain()
        target_seq = _seq_of_head(gate.store, target_head)
        if target_seq is None:
            gate.refuse(actor, RECOVER_OP, RECOVER_ANCHOR,
                        "the recover target %r is not a lawful prior point of this chain — its head "
                        "matches no record this record ever held. Recover restores only a point the "
                        "record HELD, never a state it never lawfully held (never to wrongness; the "
                        "laundering-door stays shut)" % (target_head,))
        if target_seq > fold["verified_through"]:
            gate.refuse(actor, RECOVER_OP, RECOVER_ANCHOR,
                        "the recover target is at seq %d, beyond the chain's verified_through %d "
                        "(break_at=%r) — a point the chain does not adjudicate as sound is refused. "
                        "The chain adjudicates itself; nothing about soundness is stored."
                        % (target_seq, fold["verified_through"], fold["break_at"]))

        # VERIFY AT LOAD (A4/RW2). Re-read and hash EACH content segment the recovered state depends
        # on (`duplicate_and_verify` inward — content addressing makes the check exact: the bytes
        # rehash to their named hash, or they are not the segment). A corrupt or missing segment
        # HALTS the recover before any record is appended — restoring NOTHING. Never trust the
        # checkpoint's say-so and check later; the load-verify IS the gate on the served state.
        verified = []
        for seg in segments:
            try:
                verified.append(duplicate_and_verify(blobs, seg))
            except HandoverHalt as e:
                # (4) the HALTED outcome, WITH THE FAILING SEGMENT NAMED (board :3049). A halt writes
                # NO splice — the recover restores nothing (the handover-halt pattern inward, §8-h);
                # the refusal is the recorded outcome, naming the segment that did not verify.
                gate.refuse(actor, RECOVER_OP, RECOVER_ANCHOR,
                            "the recover HALTED at load-verify (outcome=%s) — the failing segment %r "
                            "did not verify: %s. Restoring nothing (verify-at-load, never "
                            "trust-then-check); no splice is written" % (OUTCOME_HALTED, seg, e))

        # THE SPLICE (design/37 :798; the four-field row, board :3049). An owner-gated recorded act
        # that PROVES ITSELF: actor = the root authority holder; action = the recover op; object =
        # the sound point recovered to (by head); target = THIS RECORD (its seal identity, the
        # chain-anchor that names the whole append-only chain, or None if unsealed). Its payload
        # carries ALL FOUR fields :3049 requires — (1) what region broke, (2) what was sound, (3)
        # what was done (the checkpoint hash + every segment by hash), (4) the outcome
        # (verified-at-load). It returns ONE draft; the gate appends it as the record's only new row.
        # NO row is removed, rewritten, or shortened — the broken rows past break_at remain as
        # adjudicated history, and the recovered STATE is the checkpoint this record cites (held once
        # in the EP-44 artifact, never duplicated).
        from kernel.store import CHAIN_ANCHOR_ACTION            # lazy: no top-level store coupling
        anchor_list = gate.store.by_action(CHAIN_ANCHOR_ACTION)
        this_record = canonical_hash(anchor_list[0]) if anchor_list else None
        head_seq = len(gate.store.events)                      # the record's head at recovery time
        broken_range = [fold["break_at"], head_seq] if fold["break_at"] is not None else None
        payload = {"kind": RECOVER_RECORD, CLASS: "DECISION",
                   # WHAT was restored — the sound point recovered to
                   TARGET_HEAD: target_head, TARGET_SEQ: target_seq,
                   RECOVER_RULE: rule,
                   # (1) WHAT REGION BROKE
                   BREAK_AT: fold["break_at"], BROKEN_RANGE: broken_range,
                   # (2) WHAT WAS SOUND
                   VERIFIED_THROUGH: fold["verified_through"],
                   # (3) WHAT WAS DONE — the checkpoint hash + every segment brought in, BY HASH
                   CHECKPOINT_REF: checkpoint_ref, SEGMENTS_VERIFIED: verified,
                   # (4) WHAT HAPPENED — the outcome (a halt would be the refusal above)
                   OUTCOME: OUTCOME_VERIFIED_AT_LOAD,
                   # the full fold, AGAINST WHICH anchor — for completeness
                   ADJUDICATION: {k: fold[k] for k in
                                  ("anchored", "prefix_ok", "verified_through", "break_at")}}
        # THE AUTO-TRIGGER RECORDED (EP-43-AUTO, additive). On the manual owner-gated path (no trigger)
        # the row is byte-identical to EP-43's — none of these keys appear. On the AUTO trigger the row
        # RECORDS the trigger and the three-check outcome the bridge composed (chain / checkpoint /
        # buddy, all ✓ — gated above), so the splice PROVES it woke automatically under the triple
        # check. This record IS the notice (:3082 precision 2 — NOTIFY = the recover ROW itself).
        if trigger == TRIGGER_AUTO:
            payload[TRIGGER] = TRIGGER_AUTO
            payload[TRIPLE_CHECK] = {k: triple_check.get(k) for k in TRIPLE_CHECK_MEMBERS}
        return {"actor": actor, "action": RECOVER_OP, "object": target_head, "target": this_record,
                "rule_cited": RECOVER_LAW, "payload": payload}
    return _recover


def register_recover(gate, views):
    """Wire the recover ceremony onto a kernel that has a blob store (`gate.blobs`, set when the full
    kernel composes). The reusable registration a TEST founding world calls (the recover law
    declared, the op registered). A gate with no blob store cannot verify segments at load, so the op
    stays unregistered there, exactly as content ops do. Since flip B (EP-FND-RECOVER-REGISTER)
    PRODUCTION `build_full_kernel` DOES call this at the compose layer, so the recover op is live in
    every full kernel; `build_kernel` (the founding path) does NOT — it stays pack-exact (EP-40 law)."""
    blobs = getattr(gate, "blobs", None)
    if blobs is None:
        return False
    gate.register(RECOVER_OP, RECOVER_OP_META, recover_handler(gate, blobs, views))
    return True
