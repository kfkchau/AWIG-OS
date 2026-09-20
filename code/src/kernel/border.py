# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel · OS-border vocabulary
# (border, entity, channel, draft, crossing, seal, window) per the seL4/gVisor literature; NON-GOAL:
# no offensive capability of any kind — this module GOVERNS an outside process's requests as drafts a
# gate decides; it builds a border, not an intrusion path. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS kernel — THE BORDER: THE DOOR (EP-49A; design/51 §3 N3/N9/N10, §4, §5; design/39 §1/§3).

An outside process speaks to the box AS AN ENTITY. Its request is a DRAFT the gate decides against
the record exactly as it decides any act; an allowed draft yields a REPLY carrying the CROSSING ID
(the submit row's content hash) and a SEAL over exactly what was shown; a refused draft yields a
REFUSAL surfaced through the system's own WINDOW — the refused party's own channel carries no reason.
THE SYSTEM IS THE BORDER, NOT THE COURIER (design/39 §3): a crossing is attributed to the entity that
willed it, never to the infrastructure that carried it.

THE REFERENCE THIS MODULE REFUSES (design/51 §9): the API gateway with auth middleware — a token
minted ABOVE the system as the identity, the request treated as the act, a trust store BESIDE the
record. Taking it stores trust outside the record, makes the request the act instead of a draft the
gate decides, and re-invents revocation distribution when the record already IS where validity is
read. The right derivation, held here: an entity is its recorded establishment (design/39 §1, so
BORDER-SUBMIT carries `require_prior` over CREATE-ACCOUNT and admits NO peer-minted token as
identity); a crossing is a draft the gate decides; the reply is sealed; the refusal reaches the
human through the window; the receipt is the receiver's own row (49D, not here).

DISTINCT FROM crossing.py, SHARED DISCIPLINE (the N2 lesson, design/51 §12). `crossing.py` (EP-23) is
the system-ASKS-OUT direction: a sealed hand-out (a question) plus an external ANSWER that returns as
INPUT, the crossing identified by the hand-out's store-minted SEQ (unforgeable because the store
mints it). THE BORDER is the entity-SUBMITS-IN direction: BORDER-SUBMIT a draft, BORDER-REPLY /
BORDER-REFUSAL the answer, the crossing identified by the submit's CONTENT HASH (unforgeable because
it is a measurement of the submit's own bytes). The two SHARE the discipline — a content-hash id, a
fold not a registry (kill it, replay, it comes back identical), the in-band claim ignored and the
binding read from the STORE — and this module REUSES crossing.py's serializer discipline
(`canonical`) and gate.py's `_signed_content`. They are NOT collapsed into one name: two directions
under one name is exactly the conflation the N2 lesson forbids. `crossing.py` is READ, never modified.

WHY THE CROSSING ID IS A CONTENT HASH AND NOT A SEQ (archi :3266). The reply must bind to the submit
by something the submit's bytes DETERMINE, so a reply's `crossing_id` claim is checked against the
store's recomputation of every submit's content hash and never trusted as a token — the correlation
discipline of crossing.py, in the border's own direction. A reply whose `crossing_id` matches no
submit binds nothing and is refused at the gate chokepoint (`reply_binding_guard`), for the EP-18 R-A
reason the whole estate uses: a leash in one op's handler is reached past by any other op minting the
same record shape, so the leash lives where every write converges.

THE SEAL IS REAL OR REFUSED, NEVER FAKED (N10; RW-FAKE-SEAL, stop g). The reply's seal is a REAL
Ed25519 signature over exactly what was shown, produced by the signer (the SigningKeyStore holding
the system signing key BESIDE the byte-frozen vault) with the vetted library present; with the
library ABSENT, sealing REFUSES citing the absent library (`crypto.LibraryAbsent`) and never
substitutes modelled material. This is the era-split carried into the border: the box tells the
truth about what its seal is worth.

NO FOUNDING LAW IS MINTED HERE (archi :3285). The three border ops are founding DATA that cite the
EXISTING COMM-LAW-CONTRACT (a crossing IS an opening of the entity's system-facing channel,
design/39; the entity prior-established under CAP-IS-LAW as every crossing op already carries). The
DECISION on a draft's content cites the draft's own op's rule, as any act does. If the door were to
need a law of its own (who may submit what, to whom), that is a STOP and a raise, not a mint.
"""

from collections.abc import Mapping

from . import canonical

# ---- the three border-family payload kinds — one uniform kind per role, so the gate's chokepoint
# recognises a border record by WHAT IT IS (the crossing.py chokepoint idiom, distinct family). -----
SUBMIT_KIND = "border-submit"
REPLY_KIND = "border-reply"
REFUSAL_KIND = "border-refusal"

#: The border family: every record any of the three ops mints. The chokepoint guard fires on these.
BORDER_KINDS = (SUBMIT_KIND, REPLY_KIND, REFUSAL_KIND)

#: The kinds a REPLY / REFUSAL binds back to a submit by its crossing id (the citing direction).
CITING_KINDS = (REPLY_KIND, REFUSAL_KIND)

#: The op names (data-born; registered from the founding record, never in code — the interpreter
#: re-registers them at boot). Named here only so the guard and the folds cite one spelling.
SUBMIT_OP = "BORDER-SUBMIT"
REPLY_OP = "BORDER-REPLY"
REFUSAL_OP = "BORDER-REFUSAL"

#: The law the three ops cite (existing; no BORDER law is minted in 49A — archi :3285).
BORDER_LAW = "COMM-LAW-CONTRACT"

#: The recorder / infrastructure identities a CROSSING may NEVER be attributed to (design/39 §3): the
#: system is the border, not the courier. A crossing willed by one of these is the courier fallacy.
SYSTEM_ACTORS = ("SYSTEM", "PC_RUNTIME")


# ---- the crossing id: the submit row's content hash (archi :3266) --------------------------------

def content_id(record):
    """THE CROSSING ID — `canonical_hash` of the submit row's own content (action, object, target,
    payload), derivation stripped. A measurement of the submit's bytes, so it is unforgeable by
    construction and recomputable by anyone holding the record — the border's answer to the same
    question crossing.py answers with a store-minted seq. The gate-added envelope (provenance, seq,
    occurrence_time) is EXCLUDED on purpose: those are the store's, not the crossing's, so the id a
    reply computes from the submit it was shown equals the id the gate recomputes from the stored
    submit (the round-trip property). One hash via `canonical` — the estate's single serializer."""
    core = {"action": record.get("action"), "object": record.get("object"),
            "target": record.get("target"), "payload": record.get("payload") or {}}
    return canonical.canonical_hash(canonical.strip_derivation(core))


def submits(store, as_of=None):
    """Every crossing, DERIVED: {crossing_id: submit_record}. A FOLD, not a registry — kill it,
    replay the record, it comes back identical (crossing.py's discipline, the border's direction).
    Keyed by the content hash, so a reply's `crossing_id` claim is looked up here and never
    trusted as an in-band token."""
    out = {}
    for e in store.by_action(SUBMIT_OP, as_of):
        out[content_id(e)] = e
    return out


def crossings(store, as_of=None):
    """Every crossing's border state, DERIVED: {crossing_id: {...}} with its state computed, never
    stored. Three states, all differences between records (the crossing.py shape, distinct family):

      open      — a BORDER-SUBMIT with no reply and no refusal citing its crossing id
      replied   — a BORDER-REPLY cites its crossing id
      refused   — a BORDER-REFUSAL cites its crossing id

    Kill this and replay: identical."""
    out = {}
    for cid, sub in submits(store, as_of).items():
        out[cid] = {"crossing_id": cid, "submit_seq": sub.get("seq"),
                    "entity": (sub.get("payload") or {}).get("entity"),
                    "willed_by": sub.get("actor"), "replied_by": None,
                    "refused_by": None, "state": "open"}
    for e in store.all(as_of):
        p = e.get("payload") or {}
        kind, cid = p.get("kind"), p.get("crossing_id")
        if kind == REPLY_KIND and cid in out and out[cid]["replied_by"] is None:
            out[cid]["replied_by"] = e.get("seq")
            out[cid]["state"] = "replied"
        elif kind == REFUSAL_KIND and cid in out and out[cid]["refused_by"] is None:
            out[cid]["refused_by"] = e.get("seq")
            if out[cid]["state"] == "open":
                out[cid]["state"] = "refused"
    return out


def binds_a_submit(store, crossing_id, as_of=None):
    """Does `crossing_id` name a real crossing — a BORDER-SUBMIT whose OWN content hash is this id?
    The binding is read from the STORE (each submit's recomputed content hash), never from the
    reply's claim. This is where 'the reply is about a crossing that actually happened' is
    enforced."""
    return crossing_id in submits(store, as_of)


# ---- the seal over exactly what was shown: real via the signer, refused when absent (N10) ---------

def shown_digest(crossing_id, shown):
    """THE CANONICAL BYTES THE SEAL BINDS — exactly what was shown, hashed by gate.py's own
    `_signed_content` (reused, design/51 §5): the reply's {action, object, payload} where the shown
    content lives in the payload. A changed byte of `shown` changes this digest, so a seal made over
    the old digest cannot verify over the new one (RW-SEAL-BLIND: the seal is over exactly what was
    shown). Imported lazily so the border never sits above the gate in the import graph."""
    from .gate import _signed_content
    reply_draft = {"action": REPLY_OP, "object": crossing_id, "target": None,
                   "payload": {"crossing_id": crossing_id, "shown": shown}}
    return _signed_content(reply_draft, None, None)


def seal_reply(signer, custody, crossing_id, shown):
    """A REAL Ed25519 signature over exactly what was shown (`shown_digest`), produced by the SIGNER
    with the key sealed under `custody` — a use of the system signing key, never a read. Returns the
    tagged signature. With the vetted library ABSENT `signer.sign` raises `crypto.LibraryAbsent`,
    which propagates: the border REFUSES to seal and NEVER fakes it (N10; RW-FAKE-SEAL, stop g)."""
    return signer.sign(custody, shown_digest(crossing_id, shown))


def verify_seal(public_key, seal, crossing_id, shown):
    """True iff `seal` is a real Ed25519 signature over exactly what was shown, under `public_key`.
    A seal over ALTERED shown bytes returns False — the check that can fail (RW-SEAL-BLIND). Real
    only: a tagged seal verifies only through the vetted library, which raises `LibraryAbsent` when
    absent (never a modelled pass)."""
    from . import crypto
    return crypto.verify(public_key, seal, shown_digest(crossing_id, shown))


# ---- the gate chokepoint: a reply/refusal binds an OPEN submit, by the store not the claim --------

def reply_binding_guard(gate, store, actor, opname, draft):
    """THE BORDER FAMILY'S CHOKEPOINT — beside `crossing.correlation_guard`, a DISTINCT family with
    the SAME discipline (the N2 lesson). Enforcement lives where every write converges, not in one
    op's handler: a leash in a handler is reached past by any other op minting the same record shape
    (EP-18 R-A). It fires on ANY op minting a border-family record.

    TWO BINDINGS, ONE CHOKEPOINT:
      REPLY / REFUSAL — a reply/refusal whose `crossing_id` binds NO BORDER-SUBMIT is about a
        crossing that never happened — the store binds reply to submit by the submit's own content
        hash, and an unbound citation carries nothing. The in-band `crossing_id` claim is checked
        against the store's recomputation and never trusted (RW-CROSSING-ID-DRIFT).
      SUBMIT (EP-49B, design/51 N4) — a BORDER-SUBMIT that DECLARES a tunnel must be BOUND by it (the
        entity IS the tunnel's sender — the four-tuple's first field). An unbound crossing is refused
        (RW-UNBOUND). A submit that declares no tunnel is not an external-tunnel crossing and passes
        (EP-49A's owner/glassbox direction, unchanged).
    Both cite COMM-LAW-CONTRACT (the crossing is an opening of the entity's channel; EXTERNAL-TUNNEL
    states the four-tuple binding as founding law, its general multi-entity consumer deferred — archi
    :3285, :3308, design/51 §9)."""
    p = draft.get("payload") if isinstance(draft.get("payload"), dict) else None
    if p is None:
        return
    if p.get("kind") == RECEIPT_KIND:
        _received_rule_input_guard(gate, store, actor, opname, p)  # C6 P10 (I3): a parent rule lands INPUT, never DECISION
        _received_rule_citation_guard(gate, store, actor, opname, p)  # C6 P9 (I22): a citation with no local received copy refuses by name
        _receipt_idempotency_guard(gate, store, actor, opname, p)
        _receipt_handshake_guard(gate, store, actor, opname, p)   # C6 P11 (:3698): the two refusals + I12, on the act path
        return
    if p.get("kind") == SUBMIT_KIND:
        _submit_tunnel_binding_guard(gate, store, actor, opname, p)
        return
    if p.get("kind") not in CITING_KINDS:
        return
    cid = p.get("crossing_id")
    if not binds_a_submit(store, cid):
        gate.refuse(actor, opname, BORDER_LAW,
                    f"a {p['kind']} record cites crossing id {cid!r}, which is the content hash of NO "
                    "BORDER-SUBMIT — the border binds a reply to a submit by the submit's own content "
                    "hash (the store's measurement), and a crossing id that names no submit binds "
                    "nothing (RW-CROSSING-ID-DRIFT; a reply is never about a crossing that did not happen)")


# ---- the window: a refusal reaches the human here; the refused party's channel carries no reason --

def through_the_window(store, as_of=None):
    """THE SYSTEM'S OWN WINDOW (design/51 N3; §12 item 4) — the human-facing surface of border
    refusals: {crossing_id: {reason, entity, seq}} folded from the BORDER-REFUSAL records. A refusal
    reaches the human THROUGH THIS (the record read as the system's own view, which a human actor
    reads), carrying its reason — never through the refused party. This is a fold over the record; it
    appends nothing, and the human-view surface it names already exists (no new 'window' module)."""
    out = {}
    for e in store.by_action(REFUSAL_OP, as_of):
        p = e.get("payload") or {}
        out[p.get("crossing_id")] = {"reason": p.get("reason"), "entity": p.get("entity"),
                                     "seq": e.get("seq")}
    return out


def channel_records(comms_view, entity, as_of=None):
    """The records on the refused entity's OWN live system-facing channel(s) — what the entity can
    see through its channel (comms.py, the border's neighbour). A border refusal writes NOTHING here:
    it is a WINDOW record, so the reason lives only in `through_the_window` and never crosses to the
    refused party. Returns the message ledger across the entity's every live channel."""
    out = []
    for _role, channel in comms_view.channels_of(entity, as_of).items():
        if channel is not None:
            out.extend(comms_view.message_ledger(channel, as_of))
    return out


def reason_in_records(records, reason):
    """Does any record carry the refusal's REASON inline? A pure census, ABLE TO FAIL: hand it a
    record carrying the reason and it says so (RW-REASON-TO-REFUSED). Run against the refused party's
    own channel records, which carry NONE — the refusal reaches the human through the window, and the
    refused party's channel is no courier of the reason (design/51 N3)."""
    return any(reason is not None and reason in str(r.get("payload") or {}) for r in records)


# ---- the courier-never census: no crossing attributed to the system (A4) -------------------------

def is_system_willed(crossing):
    """Is this crossing attributed to the SYSTEM as its willing entity? The courier fallacy the border
    forbids (design/39 §3): the system is the border, never the courier that wills a crossing."""
    return crossing.get("willed_by") in SYSTEM_ACTORS or crossing.get("entity") in SYSTEM_ACTORS


def system_attributed_over(crossings_iterable):
    """The census predicate over ANY iterable of crossing states — so a red world can hand it a
    planted crossing and watch it fire (the test_ep48 RW-PACKET-ROW discipline, the census read from
    the set rather than from the store, ABLE TO FAIL)."""
    return [c for c in crossings_iterable if is_system_willed(c)]


def system_attributed(store, as_of=None):
    """THE COURIER-NEVER CENSUS (design/39 §3; A4) — every crossing (BORDER-SUBMIT) whose willing
    entity is the SYSTEM. EMPTY on any real world by construction: a submit's willing entity is an
    established account (BORDER-SUBMIT's `require_prior` over CREATE-ACCOUNT), and the recorder is
    never an established submitter. A non-empty answer is the courier fallacy — the system moving a
    message AS ITS OWN act (RW-COURIER)."""
    return system_attributed_over(crossings(store, as_of).values())


# ---- the border stance: submit / reply / refusal (the orchestrators the door speaks through) -----

def submit(gate, entity, draft, actor=None, tunnel=None):
    """An outside entity submits a DRAFT — the crossing. Attributed to the ENTITY that willed it
    (design/39 §3), decided by the gate against the record BEFORE any effect (an unlawful submit is
    refused and recorded, never executed). Returns the appended submit record; its content hash is
    the crossing id.

    EP-49B: an EXTERNAL entity may DECLARE the `tunnel` it crosses IN ITS DRAFT (design/51 N4) — the
    tunnel it CLAIMS to cross is part of what it submits, and the gate CHECKS that claim against the
    founded tunnels rather than trusting it (the peer's claim is never trusted). The chokepoint holds
    the crossing to that tunnel's four-tuple binding (the entity IS the tunnel's sender), and an
    unbound crossing is refused. A submit that declares no tunnel is not an external-tunnel crossing
    and is unaffected (EP-49A's owner/glassbox direction). The declaration rides in `draft` — an
    EXISTING structural param — so EP-49A's border-submit op is extended in behaviour, not re-minted
    (§7); its META is untouched."""
    if tunnel is not None:
        draft = {**(draft or {}), "tunnel": tunnel}
    return gate.execute(SUBMIT_OP, actor or entity, {"entity": entity, "draft": draft})


def reply(gate, store, signer, custody, submit_record, shown, actor="SYSTEM"):
    """The border's REPLY to an allowed crossing: it carries the crossing id (the submit's content
    hash) and a REAL seal over exactly what was shown (refused, never faked, when the library is
    absent — the `seal_reply` call raises then). The reply is the system's own decision about the
    crossing, so it is attributed to the border (SYSTEM), never counted as a crossing itself."""
    cid = content_id(submit_record)
    seal = seal_reply(signer, custody, cid, shown)
    return gate.execute(REPLY_OP, actor, {"crossing_id": cid, "shown": shown, "seal": seal})


def refusal(gate, entity, crossing_id, reason, actor="SYSTEM"):
    """The border's REFUSAL of a crossing, surfaced through the system's own WINDOW: the record
    carries the reason (readable by the human through the window) and names the refused ENTITY —
    whose own channel this refusal never writes to. The refusal is the border's decision, attributed
    to the border (SYSTEM), never counted as a crossing."""
    return gate.execute(REFUSAL_OP, actor,
                        {"entity": entity, "crossing_id": crossing_id, "reason": reason})


# ================================================================================================
# EP-49B — IDENTITY AT THE TUNNEL (design/51 §3 N4, §5, §9; design/39 §1; design/43 §5).
#
# An external entity is verified AT THE TUNNEL. A tunnel binds the FOUR-TUPLE — sender, target,
# permitted class, proof method (design/43 §5, CGL foundational 03) — and a crossing is attributed
# to the entity that WILLED it, by its recorded establishment (authority.establishment_of), never
# to the system (the courier rule) and never to an incarnation's transient handle. The PROOF METHOD
# uses EXISTING check kinds: a real signature under the entity's bound key (its name IS its key —
# D08.42), or `secret_verify` (a candidate compared by hash, never recorded — EP-19, design/31 J8).
# A RICHER proof method (quorum / blind position / focus-lock) is the OWNER'S one word, RAISED and
# never minted here (§11 item 3; stop-e; RW-NEW-KIND-SILENT). The founding law EXTERNAL-TUNNEL
# states the binding; its general multi-entity consumer is DEFERRED — who a peer IS beyond its
# tunnel proof is the C6 cap (design/51 §9; stop-f). No trust table, session token or peer
# certificate enters: the record is where validity is read (design/51 §4 minimality gate; the
# API-gateway reference refused, §5).
# ================================================================================================

#: The founding law EP-49B mints (design/51 N4; archi :3308) — the four-tuple binding rides it.
EXTERNAL_TUNNEL_LAW = "EXTERNAL-TUNNEL"

#: The tunnel FOUR-TUPLE (design/43 §5, CGL foundational 03). The owner tunnel binds the first three
#: (the owner needs no proof method — it is the owner); an external entity's tunnel binds the fourth.
TUNNEL_FIELDS = ("sender", "target", "permitted", "proof_method")

#: The proof methods EP-49B's BASIC case reaches, each an EXISTING check kind (design/51 §3, §11-2).
PROOF_SIGNATURE = "signature"            #: a real Ed25519 signature under the entity's bound key
PROOF_SECRET_VERIFY = "secret_verify"    #: a candidate compared by hash, never recorded (EP-19)
BASIC_PROOF_METHODS = (PROOF_SIGNATURE, PROOF_SECRET_VERIFY)


def tunnels(store, as_of=None):
    """Every founded tunnel's FOUR-TUPLE, DERIVED: {name: {sender, target, permitted, proof_method,
    seq}}. A FOLD over CREATE-TUNNEL records — kill it, replay, identical. The binding is read from
    the RECORD, never a stored table (design/51 §4 minimality gate: no trust table beside the
    record). The owner tunnel's `proof_method` is None (the owner is the owner); an external entity's
    tunnel carries one."""
    out = {}
    for e in store.by_action("CREATE-TUNNEL", as_of):
        p = e.get("payload") or {}
        name = p.get("name") or e.get("object")
        out[name] = {"name": name, "sender": p.get("sender"), "target": p.get("target"),
                     "permitted": p.get("permitted"), "proof_method": p.get("proof_method"),
                     "seq": e.get("seq")}
    return out


def tunnel_binds(tunnel, sender, target=None, permitted=None):
    """Does `tunnel` bind this crossing's (sender[, target, permitted class])? The four-tuple's
    first three — the fourth (proof_method) is verified separately (`proof_verifies`, A4). `sender`
    is the crux: a tunnel binds a crossing only when the crossing's entity IS the tunnel's sender
    (the tunnel says WHO may send). `target`/`permitted`, when given, narrow further (None = the
    sender question alone). Exact match, never a string prefix."""
    if tunnel.get("sender") != sender:
        return False
    if target is not None and tunnel.get("target") != target:
        return False
    if permitted is not None and tunnel.get("permitted") != permitted:
        return False
    return True


def bound_tunnel(store, sender, target=None, permitted=None, as_of=None):
    """The founded tunnel that binds a (sender[, target, permitted]) crossing, or None — read from
    the fold, so re-founding a tunnel changes the binding at the next read. None means the crossing
    is UNBOUND (no founded tunnel admits this sender): an unbound crossing is refused (N4)."""
    for t in tunnels(store, as_of).values():
        if tunnel_binds(t, sender, target, permitted):
            return t
    return None


def _willing_sender(crossing):
    """The entity a crossing is attributed to (its willing entity) — the sender the tunnel must
    bind. Reads `willed_by` then `entity` (border.crossings' shape)."""
    return crossing.get("willed_by") or crossing.get("entity")


def bound_over(crossings_iterable, tunnels_map):
    """Which crossings BIND a tunnel in `tunnels_map` — the crossing's willing entity IS some
    founded tunnel's sender (the four-tuple's first field). A PURE predicate over any iterable, so a
    red world reads both sides: a bound crossing appears here, an unbound one does not."""
    senders = {t.get("sender") for t in tunnels_map.values()}
    return [c for c in crossings_iterable if _willing_sender(c) in senders]


def unbound_over(crossings_iterable, tunnels_map):
    """Crossings that bind NO founded tunnel — UNBOUND (RW-UNBOUND; N4: an unbound crossing is
    refused). EMPTY when every crossing's entity is some tunnel's sender; ABLE TO FAIL: a planted
    crossing whose entity is no tunnel's sender fires this census (the EP-49A courier-census
    discipline, read from the SET rather than the store)."""
    senders = {t.get("sender") for t in tunnels_map.values()}
    return [c for c in crossings_iterable if _willing_sender(c) not in senders]


def _submit_tunnel_binding_guard(gate, store, actor, opname, payload):
    """An UNBOUND crossing is refused (design/51 N4). A BORDER-SUBMIT declaring `tunnel` T must be
    BOUND by T: T is a founded tunnel whose SENDER is the crossing's entity (the four-tuple's first
    field — the tunnel says who may send). A submit declaring a tunnel that is not founded, or whose
    sender is not this entity, crosses nothing lawful and is refused (RW-UNBOUND, the check that can
    fail). The tunnel a crossing CLAIMS rides in its `draft` (the entity's own submission); the gate
    reads it there and checks it against the founded tunnels — the peer's claim is CHECKED, never
    trusted. Cites COMM-LAW-CONTRACT — the crossing is an opening of the entity's channel (EP-49A,
    archi :3285); EXTERNAL-TUNNEL states the four-tuple binding, its general consumer deferred."""
    draft = payload.get("draft")
    claimed = draft.get("tunnel") if isinstance(draft, dict) else None
    if claimed is None:
        return
    entity = payload.get("entity")
    t = tunnels(store).get(claimed)
    if t is None or t.get("sender") != entity:
        bound = None if t is None else t.get("sender")
        gate.refuse(actor, opname, BORDER_LAW,
                    f"a border-submit declares tunnel {claimed!r} as the crossing of entity "
                    f"{entity!r}, but that tunnel binds sender {bound!r} — an established external "
                    "entity crosses only the tunnel that binds it as sender (design/51 N4; the "
                    "four-tuple's sender field, EXTERNAL-TUNNEL). An unbound crossing is refused.")


def proof_verifies(tunnel, proof, *, public_key=None, crossing_id=None, shown=None):
    """Does `proof` satisfy the tunnel's PROOF METHOD (A4)? The BASIC case, under EXISTING kinds:

      signature      — `proof` is a real Ed25519 signature over exactly what was shown, verified
                       under the entity's BOUND public key (its name IS its key — D08.42). Correct
                       -> True; a wrong signature or a wrong key -> False (`verify_seal` / crypto).
                       Real-or-refused: with the vetted library ABSENT verification raises
                       `crypto.LibraryAbsent` and NEVER models a pass (the N10 discipline, EP-49A).
      secret_verify  — `proof` is a candidate secret; it verifies iff its hash equals the tunnel's
                       stored `secret_hash`. The candidate crosses ONCE and is compared BY HASH,
                       NEVER recorded (EP-19; design/31 J8). Correct -> True; wrong -> False.

    A method NOT in BASIC_PROOF_METHODS is a NEW CHECK KIND — the OWNER'S one word (quorum / blind
    position / focus-lock, §11 item 3): this RAISES ValueError naming stop-e, NEVER a silent
    modelled pass and never a kind minted here (RW-NEW-KIND-SILENT)."""
    method = tunnel.get("proof_method")
    if method == PROOF_SIGNATURE:
        return verify_seal(public_key, proof, crossing_id, shown)
    if method == PROOF_SECRET_VERIFY:
        from .vault import secret_hash            # a pure hash of the candidate — not a vault-state read
        want = tunnel.get("secret_hash")
        return want is not None and secret_hash(proof) == want
    raise ValueError(
        f"tunnel proof method {method!r} is not one of the basic existing kinds {BASIC_PROOF_METHODS!r} "
        "— a richer proof method (quorum / blind position / focus-lock) is a NEW CHECK KIND, the "
        "owner's one word, RAISED never minted here (design/51 §11 item 3; EP-49B stop-e)")


# ================================================================================================
# EP-49D — THE RECEIPT: ONE ROW, ONE RECEIPT, TWO BODIES (design/51 §3 N9, §4, §5; D08.42, D08.48).
#
# A row sent from body A is received at body B as INPUT through B's border; B appends ITS RECEIPT to
# ITS OWN record. A never writes B's record and B never A's — one pen per record (D08.30, the
# single-writer lock, store.py: one writer per data dir). A receipt is the RECEIVER's own row of a
# crossing: it cites the received row's CONTENT HASH (border.content_id — the crossing id that
# EXCLUDES record_time, so two bodies recording one crossing at different times derive the SAME hash,
# D08.40), the FROM-BODY (the sender's bound SYSTEM PUBLIC KEY together with its genesis hash — a
# body's NAME, D08.42), the sender's SIGNATURE (verified under that key, real-or-refused N10), the
# UNDER-RULE, and the REVEALED-SET (the selective-disclosure leaf set when a tree was presented,
# D08.48; empty otherwise). Identity is what CROSSED, never trust in the peer's own record (N4's cap,
# design/51 §9). A copied seed is a FORK the chain exposes, never a silent clash. ONE ROW, ONE
# RECEIPT: a second receipt for the same content hash is refused at the gate chokepoint (idempotent).
#
# THIS EXTENDS border.py (archi :3285/§11): the RECEIPT op is founding DATA citing the EXISTING
# COMM-LAW-CONTRACT (the crossing is an opening of the entity's channel). No new module, no new law,
# no new check kind. The idempotency is a leash at the WRITE CHOKEPOINT (EP-18 R-A) beside the
# reply-binding leash — a leash in a handler is reached past by any other op minting the same record
# shape, so it lives where every write converges (gate.py already calls `reply_binding_guard`).
# ================================================================================================

#: The receipt family payload kind (one uniform kind, so the chokepoint recognises a receipt record
#: by WHAT IT IS — the crossing.py / border chokepoint idiom).
RECEIPT_KIND = "receipt"

#: The op name (data-born; registered from the founding record at boot — the interpreter re-registers
#: it). Named here only so the guard and the folds cite one spelling.
RECEIPT_OP = "RECEIPT"

#: The law the receipt op cites (existing; no RECEIPT law is minted in 49D — the crossing is an
#: opening of the entity's channel, design/39; archi :3285).
RECEIPT_LAW = "COMM-LAW-CONTRACT"


def receipts(store, as_of=None):
    """Every receipt THIS BODY has recorded, DERIVED: {content_hash: receipt_record}, FIRST-WINS.
    A FOLD, not a registry — kill it, replay the record, it comes back identical. Keyed by the
    received row's content hash, so one row maps to exactly one receipt (the first); a later receipt
    for the same content hash is refused at the chokepoint (RW-DOUBLE-RECEIPT)."""
    out = {}
    for e in store.by_action(RECEIPT_OP, as_of):
        ch = (e.get("payload") or {}).get("content_hash")
        if ch is not None and ch not in out:
            out[ch] = e
    return out


def has_receipt(store, content_hash, as_of=None):
    """Does THIS BODY's record already carry a receipt for `content_hash`? Read from the fold (the
    store's own answer), never from an in-band claim — the one-row-one-receipt authority."""
    return content_hash in receipts(store, as_of)


def receipt_binds_row(receipt_record, received_row):
    """Is `receipt_record` the receipt OF `received_row`? The receipt's content hash must be the
    content hash of the row it claims to receive (border.content_id — a measurement of the row's own
    bytes, unforgeable by construction). A receipt whose content hash does not match the row it names
    binds nothing (RW-RECEIPT-NOT-BOUND) — the receipt is OF a specific crossing, never a bare token."""
    return (receipt_record.get("payload") or {}).get("content_hash") == content_id(received_row)


def from_body_name(public_key, genesis_hash):
    """A BODY'S NAME (D08.42): the pair (bound SYSTEM PUBLIC KEY, genesis hash). The key is random at
    the boot ceremony (EP-47B); the genesis hash pins the body's founding. A COPIED SEED shares the
    key but the two bodies' chains DIVERGE (different records), so the fork is exposed by the chain —
    a copied seed is a fork, never a silent clash (design/51 N9)."""
    return {"key": public_key, "genesis": genesis_hash}


def genesis_hash(store):
    """A body's GENESIS HASH — the content hash of its genesis (first) record, the founding-
    designation the installer appends first (FOUND-STORE). Two independently-booted bodies pin their
    founding here; combined with the random bound key it is the body's NAME (D08.42)."""
    first = next(iter(store.all()), None)
    return None if first is None else content_id(first)


def chain_head(store, as_of=None):
    """A body's CHAIN HEAD — the canonical hash of its last record (the `prev_hash` chain's tip,
    store.py). Two bodies with a COPIED SEED (identical key) still diverge here the moment their
    records differ, so the chain EXPOSES the fork (design/51 N9): the receipt's from-body names the
    key, and the divergent chain tells the two apart — never a silent clash."""
    from . import canonical
    recs = store.all(as_of)
    return None if not recs else canonical.canonical_hash(recs[-1])


def verify_from_sig(from_body, from_sig, content_hash):
    """Does `from_sig` verify as the sender's REAL signature over the crossing's content hash, under
    the sender's bound key (`from_body['key']`, its NAME — D08.42)? A wrong signature or a wrong key
    returns False (the check that can fail). Real-or-refused (N10): with the vetted library ABSENT,
    `crypto.verify` raises `crypto.LibraryAbsent` and NEVER models a pass — the receipt tells the
    truth about what its from-signature is worth. Identity is what CROSSED, never trust in the peer's
    record (N4's cap): the receipt records only the key that signed what crossed."""
    from . import crypto
    message = content_hash.encode() if isinstance(content_hash, str) else content_hash
    return crypto.verify(from_body.get("key"), from_sig, message)


def _receipt_idempotency_guard(gate, store, actor, opname, payload):
    """ONE ROW, ONE RECEIPT (design/51 N9) — the receipt family's chokepoint leash, beside the
    reply-binding leash and the crossing correlation guard, a DISTINCT family with the SAME
    discipline. A RECEIPT whose content hash THIS BODY's record ALREADY receipts is refused: the
    receiver records exactly one receipt per received row (RW-DOUBLE-RECEIPT). The store's `receipts`
    fold is the authority (kill it, replay, identical), never an in-band claim. Placed at the
    chokepoint, not in a handler, for the EP-18 R-A reason a leash lives where every write converges.
    Cites COMM-LAW-CONTRACT — the receipt is the receiver's row of an opening of its channel."""
    ch = payload.get("content_hash")
    if ch is not None and has_receipt(store, ch):
        gate.refuse(actor, opname, RECEIPT_LAW,
                    f"a RECEIPT cites content hash {ch!r}, which this body's record already receipts "
                    "— one row, ONE receipt (design/51 N9): the receiver records exactly one receipt "
                    "per received row, and a second is refused (RW-DOUBLE-RECEIPT; the receipt is the "
                    "receiver's own row, and a row is received once)")


def record_receipt(gate, content_hash, from_body, from_sig, under_rule=RECEIPT_LAW,
                   revealed_set=None, checks=None, disclosure_level=None, address_form=None,
                   actor="SYSTEM"):
    """THIS BODY records its RECEIPT of a crossing in ITS OWN record — a DECISION citing the received
    row's content hash, the from-body (the sender's bound key + genesis hash, D08.42), the sender's
    signature, the under-rule, and the revealed-set (the selective-disclosure leaf set when a tree was
    presented, D08.48; empty otherwise). Idempotent: a second receipt for the same content hash is
    refused at the gate chokepoint (one row, one receipt). Returns the appended receipt record. The
    receipt is B's OWN row — it is appended to B's store through B's gate, and never to A's record.

    C6 P11 — the graded-verdict fields ride the receipt (P8's THREE OPTIONAL STRUCTURAL params, already
    declared in the RECEIPT op META; no founding move): the CHECKS map ({who, body, memory_sane} each
    pass|fail — SPIKE-3 N2), the DISCLOSURE_LEVEL, and the ADDRESS_FORM. Passed only when present, so a
    bare row receipt OMITS all three and is byte-unchanged from before P8 (the honest record carries
    them only when a graded cross-body verdict was recorded). `admitted_level` is DERIVED AT READ from
    the recorded checks + disclosure_level, NEVER stored (I10)."""
    payload = {"content_hash": content_hash, "from_body": from_body, "from_sig": from_sig,
               "under_rule": under_rule, "revealed_set": revealed_set if revealed_set is not None else {}}
    if checks is not None:
        payload["checks"] = checks
    if disclosure_level is not None:
        payload["disclosure_level"] = disclosure_level
    if address_form is not None:
        payload["address_form"] = address_form
    return gate.execute(RECEIPT_OP, actor, payload)


# ---- C6 P8: THE RECEIPT AMENDMENT — admitted_level DERIVED AT READ, the segment-address form -----
# SPIKE-3 N2 (the checks map {who, body, memory_sane} + the disclosure level) and SPIKE-5 (the
# segment-address form). admitted_level is a PURE FUNCTION of a receipt's own recorded checks map and
# disclosure_level, computed AT READ and NEVER stored (I10; stop condition (d)): moving the grading
# re-judges every receipt without re-recording one. receipt_binds_segment is the SPIKE-5 code
# primitive a segment receipt needs (a blob-address rehash, not a content_id).

DISCLOSURE_LEVELS = ("HASHES-ONLY", "SHELLS", "FULL")   # I10 / B3: least -> most disclosure
CHECK_NAMES = ("who", "body", "memory_sane")            # SPIKE-3 N2: the three-check graded verdict
ADDRESS_FORMS = ("row", "segment")                      # SPIKE-5: a row content-id vs a segment blob-address
_PASS = (True, "pass", "PASS")                          # a check's pass tokens (the record's own field)

# ---- C6 P11 (I12): LEAST DISCLOSURE BY LAW — the leaves each level names, EXACTLY ----------------
# SPIKE-3 §3c: I12's carrier is the receipt's `revealed_set` (the leaves that crossed). The LAW is the
# disclosure LEVEL: each level names EXACTLY the leaves a crossing at that level carries — no more (an
# over-disclosure is a privacy breach — least disclosure, I12), no less (a withheld required leaf is
# an incomplete crossing). The leaf sets are CUMULATIVE (SPIKE-3 §3c): HASHES-ONLY crosses the three
# hashes; SHELLS adds member names/digests and tree paths/leaf hashes; FULL adds rows, blobs and pack.
# This is a MODULE CONSTANT (code, the law's content), NOT founding data — no pack edit, no new check
# kind (the check below is a plain census, the P4/P15 idiom, never an OP_CHECKS member).
DISCLOSURE_LEAVES = {
    "HASHES-ONLY": ("set_digest", "chain_head", "merkle_root"),
    "SHELLS": ("set_digest", "chain_head", "merkle_root", "members", "tree_paths"),
    "FULL": ("set_digest", "chain_head", "merkle_root", "members", "tree_paths", "rows", "blobs", "pack"),
}


def _revealed_leaf_names(revealed_set):
    """The set of leaf NAMES a crossing disclosed, read from `revealed_set['leaves']` (a dict's keys
    or a list's entries). None when no tree/leaves were presented (the I12 check is then inert — a bare
    receipt discloses no leaves). The reserved sub-keys `leaves`/`held_stages` structure the
    revealed_set; the leaf names live under `leaves`, so the held-stage presentation never reads as an
    over-disclosed leaf."""
    if not isinstance(revealed_set, dict) or "leaves" not in revealed_set:
        return None
    leaves = revealed_set.get("leaves")
    if isinstance(leaves, dict):
        return set(leaves.keys())
    if isinstance(leaves, (list, tuple, set)):
        return set(leaves)
    return None


def least_disclosure_conflicts(revealed_leaves, disclosure_level):
    """I12 — DOES A CROSSING CARRY EXACTLY THE LEAVES ITS LEVEL NAMES? A pure census, ABLE TO FAIL,
    returning `{over, withheld}`: `over` = leaves disclosed that the level does NOT name (an
    over-disclosure — the privacy breach I12 forbids); `withheld` = leaves the level REQUIRES that were
    NOT disclosed (an incomplete crossing). Both empty => the crossing discloses exactly the level's
    leaves (pass). An unknown level names nothing, so every disclosed leaf reads as `over` (fail-closed).
    Read from the presented SET, so a red world plants either failure and watches this fire."""
    required = set(DISCLOSURE_LEAVES.get(disclosure_level, ()))
    revealed = set(revealed_leaves or ())
    return {"over": sorted(revealed - required), "withheld": sorted(required - revealed)}


def admitted_level(checks, disclosure_level):
    """DERIVE the admitted level AT READ (SPIKE-3 §3d, I10) — NEVER stored. A pure function of a
    receipt's CHECKS MAP ({who, body, memory_sane} each pass|fail) and the presented DISCLOSURE_LEVEL
    (HASHES-ONLY | SHELLS | FULL). The rule (SPIKE-3 §3d): a crossing is NEVER refused outright when
    ANY check passes — admission is GRADED, not binary. The admitted level is the presented disclosure
    level bounded by the CONFIDENCE the passed checks support: n passed checks support level index
    min(n-1, 2) (one check -> HASHES-ONLY, two -> SHELLS, three -> FULL), and the crossing is admitted
    at min(that confidence, the presented disclosure ceiling). NO check passed -> None (nothing
    admitted). Unknown inputs -> None, fail-closed. The exact grading is P8's fixing of SPIKE-3's
    'pure function of the checks map' (SPIKE-3 §5 left the wire shape to the mover), open to refinement;
    the load-bearing properties are: derived-not-stored, never-refused-when-any-passes, and monotone
    in both the passed set and the disclosure ceiling."""
    if disclosure_level not in DISCLOSURE_LEVELS or not isinstance(checks, dict):
        return None
    passed = [k for k in CHECK_NAMES if checks.get(k) in _PASS]
    if not passed:
        return None
    confidence_ix = min(len(passed) - 1, len(DISCLOSURE_LEVELS) - 1)
    ceiling_ix = DISCLOSURE_LEVELS.index(disclosure_level)
    return DISCLOSURE_LEVELS[min(confidence_ix, ceiling_ix)]


def receipt_binds_segment(receipt_record, segment_bytes):
    """SPIKE-5 §2 THE SEGMENT BINDS-CHECK — the analogue of receipt_binds_row for a segment receipt.
    A segment receipt cites the SEGMENT hash (the blobs sha256: address over the segment's bytes) in
    the content_hash slot and is verified by a BLOB-ADDRESS REHASH, not by content_id. Holds iff
    content_hash == 'sha256:'+sha256(segment_bytes). The receipt DECLARES its address_form as
    'segment' in the RECEIPT op META (so a reader tells a segment receipt from a row receipt at read
    time — the op-amend-needs-meta lesson); this is the SPIKE-5 code primitive named so a consumer
    does not discover it mid-build. A segment receipt binds nothing whose bytes do not rehash to its
    cited address (RW-RECEIPT-NOT-BOUND, the segment analogue)."""
    import hashlib
    p = receipt_record.get("payload") or {}
    if isinstance(segment_bytes, str):
        segment_bytes = segment_bytes.encode("utf-8")
    return p.get("content_hash") == "sha256:" + hashlib.sha256(segment_bytes).hexdigest()


# ---- C6 P11 (the :3698 amendment): THE RECEIPT REFUSES ON THE ACT PATH (I8, I16, I12) ------------
# P6's two handshake refusals (views.refuse_double_claim I8, views.refuse_separation_of_powers I16)
# are callable and able to fail, but NO act path invokes them (SPIKE-3 named the gap; the two refusals
# were READ and INVOKED only from tests). The :3698 amendment wires them ONTO THE RECEIPT ACT PATH —
# the occasion two machines meet (P7's handshake relation over the crossing/receipt) — so a
# double-claimed (stage, scope) or an all-three-powers concentration AT THE HANDSHAKE is refused BY
# NAME and RECORDED AS A REFUSAL ROW (gate.refuse), never merely raised out of band. The I12
# least-disclosure check runs here too. All three are INERT for a bare row receipt (no handshake
# material) — P8's "a bare row receipt is byte-unchanged" holds.
#
# ONE PEN PER RECORD (I1; stop (b)): the RECEIVER folds its OWN held-stages (gate.views over its own
# record); the COUNTERPART's held-stages are PRESENTED (carried in the receipt's revealed_set, what
# crossed), NEVER read from the counterpart's record. The module-level refusals compare two
# presentations (I2 — two records are never folded as one truth); views.py's two refusals are READ and
# INVOKED here, never re-authored.

def _presented_held_stages(revealed_set):
    """The counterpart's PRESENTED held-stages, from `revealed_set['held_stages']` (a list of
    {actor, stage, scope}). None when none were presented (the double-claim / separation checks are
    then inert). This is the COUNTERPART's presentation carried in the receipt — never a read into the
    counterpart's record (I1)."""
    if not isinstance(revealed_set, dict):
        return None
    held = revealed_set.get("held_stages")
    return held if isinstance(held, (list, tuple)) else None


def _receipt_handshake_guard(gate, store, actor, opname, payload):
    """THE :3698 AMENDMENT — at the receipt that records the relation half, invoke P6's two refusals
    over BOTH records' live rules and the I12 least-disclosure check, refusing BY NAME and RECORDING
    the refusal as a row. INERT for a bare row receipt (no disclosure_level, no presented held-stages,
    no disclosed leaves) — reached only when the receipt carries handshake material.

      I12 (least disclosure) — when the crossing PRESENTED leaves at a disclosure level, the disclosed
        leaf names must be EXACTLY the level's law-named set: an over-disclosure or a withheld required
        leaf is a RECORDED refusal (A3).
      I8 (double-claim) — the RECEIVER's own held (stage, scope) presentation vs the COUNTERPART's
        PRESENTED one: a second machine claiming a stage the other holds for the SAME scope is refused
        (refuse_double_claim, INVOKED).
      I16 (separation of powers) — over BOTH presentations combined: one actor holding decision +
        enforcement + monitoring for one scope is refused (refuse_separation_of_powers, INVOKED).

    Each refusal is translated into gate.refuse (records an op-refused row citing the rule BY NAME,
    then raises) — so the receipt is NOT appended and the record carries the named refusal."""
    revealed = payload.get("revealed_set")
    level = payload.get("disclosure_level")

    # --- I12: least disclosure by law, over the crossing's revealed leaves (A3) ---
    leaf_names = _revealed_leaf_names(revealed)
    if leaf_names is not None and level is not None:
        conflicts = least_disclosure_conflicts(leaf_names, level)
        if conflicts["over"] or conflicts["withheld"]:
            gate.refuse(
                actor, opname, RECEIPT_LAW,
                f"a crossing at disclosure level {level!r} discloses leaves that are not EXACTLY the "
                f"leaves the level names (least disclosure by law, I12): over-disclosed "
                f"{conflicts['over']}, withheld-required {conflicts['withheld']} "
                "(a crossing carries exactly the leaves the receiver's rule names — no more, no less)")

    # --- I8 / I16: the two handshake refusals, over BOTH records' live rules (the :3698 amendment) ---
    presented = _presented_held_stages(revealed)
    if presented is None:
        return                                                   # no handshake presentation — inert
    from .views import refuse_double_claim, refuse_separation_of_powers   # lazy: views imports border
    from .errors import OpError

    here = gate.views.held_stage_scopes()                        # the RECEIVER's own record (one pen, I1)
    there = {(h.get("stage"), h.get("scope")) for h in presented}  # the COUNTERPART's PRESENTATION
    try:
        refuse_double_claim(here, there)                         # I8 — INVOKED, not re-authored
    except OpError as e:
        gate.refuse(actor, opname, e.rule, e.message)            # RECORD the refusal row (A4), then raise

    combined = list(gate.views.held_stages()) + [               # BOTH records' live rules (I16, A4)
        {"actor": h.get("actor"), "stage": h.get("stage"), "scope": h.get("scope")} for h in presented]
    try:
        refuse_separation_of_powers(combined)                    # I16 — INVOKED, not re-authored
    except OpError as e:
        gate.refuse(actor, opname, e.rule, e.message)            # RECORD the refusal row (A4), then raise


# ================================================================================================
# C6 P10 — AUTO-RECEIVE, NEVER AUTO-CHANGE, AND HOLD EXACTLY WHAT BINDS (B2, B5, I3, I5; design/52).
#
# A child AUTO-RECEIVES a parent's signed rules as INPUT and changes ONLY by its own act. Three moves,
# every one composed from EXISTING primitives — NO new op, law or check kind, no pack edit:
#
#   RECEIVE (I3, I7) — a row signed by the parent's key (the key held in the child's LIVE HANDSHAKE
#     RELATION, P7 — read from views.handshake_relations, NEVER the parent's record) is verified
#     against that key (keys.verify_countersign, the reconstruct.py:117 verify reused) and RECORDED as
#     the child's own RECEIPT (P8's receiving vocabulary, border.record_receipt — a DECISION, the
#     child's own pen, I1). What CROSSED — the parent's rule — rides the receipt's revealed_set tagged
#     record_class INPUT / source parent: the parent's CLAIM, never a fact the child decided (I3, the
#     authority.py PEER_FACT_CLASS shape at the parent-tree edge). The PARENT NEVER WRITES THE CHILD'S
#     RECORD: the received row is the child's OWN INPUT act, verified against the parent's key (I1).
#     A planted attempt to land the crossed rule as a DECISION is refused at the receipt chokepoint
#     and recorded (RW-PARENT-RULE-AS-DECISION; _received_rule_input_guard, the check that can fail).
#
#   ADOPT (I5, B2) — the child changes ONLY by its OWN act: a CREATE-RULE (a DECISION, the child's pen)
#     that CITES the received rule BY HASH (the received rule's content id, in the value slot; the P6
#     self-declaration idiom on the EXISTING accepted CREATE-RULE params — recognition by policy_key,
#     no new field, no founding move). Two lawful paths, the ROW recording which (B2): by HAND, or
#     AUTOMATICALLY by the child's OWN STANDING RULE (L27 — the owner's "auto make child update") for
#     named scopes, which the child may WITHDRAW. Either way the change is the child's own act.
#
#   THE ACTIVE CONSTITUTION (B5, I5, I6) — a computed VIEW over received + adopted rows: a received
#     rule is IN the active constitution IFF a child adoption act cites it by hash. A received rule
#     with no adoption is NOT in the view (receive is NOT change, A2). Every parent rule the child was
#     ever bound by lives in the child's own record as a received row, so "what bound me at T" replays
#     locally forever (B5, A4), and the constitution recomputed from received rows alone equals the
#     served one (the cache-kill form, I6). A row, no reboot.
# ================================================================================================

#: The revealed_set key under which a receipt carries the crossed parent RULE (what crossed). Distinct
#: from the reserved `leaves` / `held_stages` sub-keys, so the P6/P11 handshake guards stay inert for a
#: received-rule receipt (it presents no disclosure leaves and no held stages).
RECEIVED_RULE_KEY = "received_rule"

#: The origin marker a crossed parent rule carries (the authority.py `peer` window, at the parent-tree
#: edge) and the class it is admitted under — the parent's CLAIM, never a fact the child decided (I3).
PARENT_SOURCE = "parent"
INPUT_RECORD_CLASS = "INPUT"

#: The child's self-declared adoption markers (recognition by policy_key on the EXISTING CREATE-RULE
#: params — the P6 held-stage idiom; NO new row field, NO founding param). An ADOPT rule cites the
#: received rule by hash in its `value`; an AUTO-ADOPT standing rule names a `scope` it auto-adopts.
ADOPT_MARKER = "adopts_received_rule"
AUTO_ADOPT_MARKER = "auto_adopt_parent_rules"

#: How an adoption was issued (B2 — the row records which). Both lawful.
ADOPT_BY_HAND = "hand"
ADOPT_AUTOMATIC = "auto"


def _live_relation_parent_key(views, relation_id, as_of=None):
    """THE PARENT'S KEY, read from the child's LIVE HANDSHAKE RELATION (P7 — B2's 'the pinned parent's
    key' is the child's half of the relation, NOT a genesis pin; Q3 discharged). Returns the parent's
    bound key from views.handshake_relations()[relation_id]['parent'] when that relation is LIVE, else
    None — a relation never declared, or withdrawn, holds no key to verify against (I4: a child whose
    relation half fails reads it as ended and adopts nothing under it). Read from the child's OWN view,
    never the parent's record (I1)."""
    rel = views.handshake_relations(as_of).get(relation_id)
    if rel is None or rel.get("state") != "live":
        return None
    parent = rel.get("parent") or {}
    return parent, parent.get("key")


def receive_parent_rule(gate, views, relation_id, parent_rule_record, parent_mark,
                        actor="SYSTEM", adopt_actor="owner", as_of=None):
    """RECEIVE a parent-signed rule as INPUT (I3, B2). The rule is verified against the parent's key
    held in the child's LIVE handshake relation (P7), then recorded as the child's OWN RECEIPT (P8's
    receiving vocabulary — a DECISION by the child's pen, I1); what CROSSED (the parent's rule) rides
    the receipt's revealed_set tagged record_class INPUT / source parent (the parent's claim, I3).

    VERIFY-OR-REFUSE (keys.verify_countersign, the reconstruct.py:117 verify reused; N10 real-or-
    refused): the parent's mark must verify against the parent's key from the live relation. A relation
    that is not live, or a mark that does not verify, is REFUSED and RECORDED (RW-PARENT-SIG-FORGED /
    RW-RELATION-NOT-LIVE — the check that can fail); nothing is admitted under a relation the child
    cannot verify (I4). The PARENT NEVER WRITES THE CHILD'S RECORD (I1): this is the child's gate, the
    child's pen, and the received row is the child's own INPUT act.

    AUTO-ADOPT (B2, L27): if the child holds a LIVE standing auto-adopt rule (L27) covering the crossed
    rule's scope, the child's OWN adoption act is issued AUTOMATICALLY here (mode auto — the row records
    it); otherwise the child adopts by hand later, or not (both lawful). Returns
    {'receipt', 'received_rule', 'adoption'} (adoption None when not auto-adopted)."""
    from . import keys                                            # lazy: the reconstruct.py:117 verify reused
    parent = _live_relation_parent_key(views, relation_id, as_of)
    if parent is None:
        gate.refuse(actor, RECEIPT_OP, RECEIPT_LAW,
                    f"a parent rule was received under relation {relation_id!r}, which is not a LIVE "
                    "handshake relation in this child's own record (P7) — a child holds no parent key "
                    "to verify against outside a live relation, and adopts nothing under one it cannot "
                    "verify (RW-RELATION-NOT-LIVE; design/52 I4). The parent never writes the child's row.")
    parent_body, parent_key = parent
    if not keys.verify_countersign(parent_mark, parent_rule_record, parent_key, parent_key):
        gate.refuse(actor, RECEIPT_OP, RECEIPT_LAW,
                    "a parent-signed rule does not verify against the parent's key held in the child's "
                    "live handshake relation (keys.verify_countersign, reconstruct's verify reused) — a "
                    "row the child cannot prove the parent signed is not admitted (RW-PARENT-SIG-FORGED; "
                    "design/52 I3/I4). The received row is the child's own INPUT act, verified, or none.")

    rule_hash = content_id(parent_rule_record)
    rp = parent_rule_record.get("payload") or {}
    received_rule = {"source": PARENT_SOURCE, "record_class": INPUT_RECORD_CLASS,
                     "rule_id": rp.get("rule_id"), "rule_hash": rule_hash,
                     "scope": rp.get("scope"), "body": rp, "relation_id": relation_id}
    receipt = record_receipt(gate, rule_hash, parent_body, parent_mark,
                             revealed_set={RECEIVED_RULE_KEY: received_rule}, actor=actor)

    adoption = None
    if rp.get("scope") in auto_adopt_scopes(gate.store, views, as_of):
        adoption = adopt_received_rule(gate, rule_hash, rp.get("rule_id"), scope=rp.get("scope"),
                                       mode=ADOPT_AUTOMATIC, actor=adopt_actor)
    return {"receipt": receipt, "received_rule": received_rule, "adoption": adoption}


def _received_rule_input_guard(gate, store, actor, opname, payload):
    """I3 — A PARENT RULE LANDS ONLY AS INPUT, NEVER A DECISION (the receipt family's chokepoint leash,
    beside the idempotency and handshake leashes — the P11 :3698 pattern, a DISTINCT concern with the
    SAME discipline). A RECEIPT whose crossed rule (revealed_set[RECEIVED_RULE_KEY]) is tagged with any
    record_class OTHER than INPUT is a parent rule landed as a DECISION on the child's record — refused
    BY NAME and recorded (RW-PARENT-RULE-AS-DECISION; the check that CAN fail). INERT for a bare receipt
    or a handshake receipt (no received-rule key). Cites COMM-LAW-CONTRACT — the receipt is the
    receiver's own row of an opening of its channel."""
    rr = (payload.get("revealed_set") or {}).get(RECEIVED_RULE_KEY)
    if isinstance(rr, Mapping) and rr.get("record_class") != INPUT_RECORD_CLASS:
        gate.refuse(actor, opname, RECEIPT_LAW,
                    f"a receipt lands a parent-signed rule with record_class {rr.get('record_class')!r} "
                    "— a parent's rule crosses to the child ONLY as INPUT (the parent's claim), never as "
                    "a DECISION the child's record authors (design/52 I3; RW-PARENT-RULE-AS-DECISION). "
                    "A parent cannot write a child's row; the child receives, then adopts by its own act.")


#: The prefix of a content-hash citation (border.content_id → "sha256:…"). A rule_cited in THIS form
#: is a CITATION BY HASH — B4's local-copy form, a cross-record reference to a parent rule held as a
#: received row. A bare rule id (no prefix) is a same-record citation (a founding/native/adopted
#: rule), covered by the I6 census's every-rule_cited-resolves-locally reading, not by this guard.
_HASH_CITATION_PREFIX = "sha256:"


def _received_rule_citation_guard(gate, store, actor, opname, payload):
    """I22 — A RECEIVED ROW CITING A RULE WITH NO LOCAL MAPPING REFUSES LOUDLY BY NAME (the receipt
    family's chokepoint leash, beside the I3 input leash and the idempotency leash — a DISTINCT concern
    with the SAME discipline, at the WRITE CHOKEPOINT where every receipt converges, EP-18 R-A). NO NEW
    OP, NO NEW FIELD: the citation rides the crossed rule's EXISTING `rule_cited` slot and the received
    row's EXISTING `relation_id`; the (relation, rule hash) is DERIVED from the received row P10 lands
    (Q4 discharged, the owner's word :3755 — 'its own local copy, the parent derived').

    A received parent rule may CITE another parent rule it obeys BY HASH (B4's local-copy form: a
    content hash, `sha256:…`, of a rule the child holds as a received row). The mapping is (the citing
    row's relation, the cited hash). The child holds a LOCAL received row for that mapping iff
    `received_parent_rules` carries the cited hash under the SAME relation. When it does NOT, admitting
    the row would force a FALLBACK — resolving the cited rule in the PARENT's record, or answering with
    a generic code — and 'a fallback that answers is a check that cannot fail' (design/52 I22:94). So it
    is REFUSED and RECORDED, the MISSING MAPPING NAMED (the exact (relation, rule hash) with no local
    received row — RW-CITED-RULE-NO-LOCAL-MAPPING), never a generic code.

    INERT unless the receipt carries a crossed rule whose `body.rule_cited` is a hash citation — a bare
    receipt, a handshake receipt, and a received rule that cites only same-record rules by id all pass
    here (the I6 census reads those). Cites COMM-LAW-CONTRACT — the receipt is the receiver's own row of
    an opening of its channel."""
    rr = (payload.get("revealed_set") or {}).get(RECEIVED_RULE_KEY)
    if not isinstance(rr, Mapping):
        return                                                   # a bare / handshake receipt cites no parent rule
    body = rr.get("body")
    cited = body.get("rule_cited") if isinstance(body, Mapping) else None
    if not (isinstance(cited, str) and cited.startswith(_HASH_CITATION_PREFIX)):
        return                                                   # not a cross-record citation-by-hash -> inert (I6 covers same-record ids)
    relation = rr.get("relation_id")
    entry = received_parent_rules(store).get(cited)              # the child's OWN local mapping, keyed by rule hash
    if entry is not None and entry.get("relation_id") == relation:
        return                                                   # MAPPED: the cited rule is the child's own local received copy (I6 local)
    gate.refuse(actor, opname, RECEIPT_LAW,
                f"a received row cites parent rule {cited!r} under relation {relation!r}, but this child "
                f"holds NO received row for that mapping (relation {relation!r}, rule hash {cited!r}) — a "
                "cited rule must resolve to the child's OWN local received copy, the parent derived from "
                "it (design/52 I22/B4; the owner's word :3755). A fallback that answered this from the "
                "parent's record is a check that cannot fail; the missing mapping is named, never a "
                "generic code (RW-CITED-RULE-NO-LOCAL-MAPPING).")


def received_parent_rules(store, as_of=None):
    """B5 / I7 — every parent rule THIS child has RECEIVED, folded from its own receipts (their
    revealed_set), keyed by the received rule's content hash: {rule_hash: {source, record_class,
    rule_id, scope, body, relation_id, receipt_seq}}. A FOLD, never a stored status — kill it, replay,
    identical (P2). Every entry is tagged record_class INPUT by construction (the shape of the entries,
    I7): a census over this fold finds every peer-origin row INPUT. This is 'hold exactly what binds'
    (B5): every parent rule the child was ever bound by lives here, in the child's own record."""
    out = {}
    for e in store.by_action(RECEIPT_OP, as_of):
        rr = ((e.get("payload") or {}).get("revealed_set") or {}).get(RECEIVED_RULE_KEY)
        if isinstance(rr, Mapping) and rr.get("rule_hash") is not None and rr["rule_hash"] not in out:
            out[rr["rule_hash"]] = {**rr, "receipt_seq": e.get("seq")}
    return out


def adopt_received_rule(gate, received_rule_hash, rule_id, scope=None, mode=ADOPT_BY_HAND,
                        actor="owner"):
    """B2 / I5 — THE CHILD'S OWN ADOPTION ACT, citing the received rule BY HASH. A CREATE-RULE (a
    DECISION, the child's pen) self-declaring the adoption on the EXISTING CREATE-RULE params (the P6
    idiom, NO new field, NO founding): `policy_key` the ADOPT marker, `value` the received rule's
    content hash (the citation by hash — I5, I6: the cited rule is LOCAL, held in the child's own
    record as a received row), `text` the MODE (hand | auto — the row records which, B2), `scope` the
    scope. `rule_id` names the child's constitution entry this adoption creates. Returns the appended
    adoption record."""
    return gate.execute("CREATE-RULE", actor,
                        {"rule_id": rule_id, "policy_key": ADOPT_MARKER,
                         "value": received_rule_hash, "text": mode, "scope": scope})


def adoptions(store, as_of=None):
    """Every child ADOPTION act, folded from the child's own CREATE-RULE rows self-declaring the ADOPT
    marker: {received_rule_hash: {rule_id, mode, scope, seq}}, FIRST-WINS per cited hash. A FOLD — kill
    it, replay, identical (P2). Keyed by the received rule's hash (the citation), so the active
    constitution matches an adoption to its received rule by hash (I5)."""
    out = {}
    for e in store.by_action("CREATE-RULE", as_of):
        p = e.get("payload") or {}
        if p.get("policy_key") == ADOPT_MARKER and p.get("value") is not None \
                and p["value"] not in out:
            out[p["value"]] = {"received_rule_hash": p["value"], "rule_id": p.get("rule_id"),
                               "mode": p.get("text"), "scope": p.get("scope"), "seq": e.get("seq")}
    return out


def auto_adopt_scopes(store, views, as_of=None):
    """B2 / L27 — the scopes the child AUTO-ADOPTS: the scopes named by its LIVE standing auto-adopt
    rules (the child's own founding rule, L27). A standing auto-adopt rule is a LIVE rule (an
    active_rules entry — latest-wins liveness, so a WITHDRAWN one drops out) self-declaring the
    AUTO_ADOPT_MARKER in its `policy_key` (the P6 held-stage liveness idiom). The child may WITHDRAW
    the standing rule (supersede it), and its scope drops from this set — auto-adoption is the child's
    own standing rule, which it controls (L27). Folded over the child's OWN rows (I1)."""
    live = views.active_rules(as_of)
    scopes = set()
    for e in store.by_action("CREATE-RULE", as_of):
        p = e.get("payload") or {}
        rid = p.get("rule_id")
        if p.get("policy_key") != AUTO_ADOPT_MARKER:
            continue
        if rid is None or rid not in live or live[rid].get("seq") != e.get("seq"):
            continue                                         # absent / superseded / withdrawn -> not live
        scopes.add(p.get("scope"))
    return scopes


def active_constitution(store, as_of=None):
    """B5 / I5 / I6 — THE ACTIVE CONSTITUTION as a computed VIEW over received + adopted rows. A
    received parent rule is IN the active constitution IFF a child adoption act cites it BY HASH; a
    received rule with NO adoption is NOT here (receive is NOT change, A2). Returns {rule_hash:
    {rule_id, scope, body, relation_id, source, record_class, receipt_seq, adopted_by, mode}}.

    A FOLD over the child's OWN received-rule receipts and adoption CREATE-RULEs — recomputed from
    those rows ALONE equals the served state (the cache-kill form, I6): kill it, replay the record, it
    comes back identical. Every included rule's citation is LOCAL (the received row is in the child's
    own record, I6). This is the constitution as a VIEW, held locally forever (B5)."""
    received = received_parent_rules(store, as_of)
    adopted = adoptions(store, as_of)
    out = {}
    for rule_hash, rr in received.items():
        a = adopted.get(rule_hash)
        if a is None:
            continue                                         # received but NOT adopted -> not in force (A2)
        out[rule_hash] = {**rr, "adopted_by": a.get("rule_id"), "mode": a.get("mode")}
    return out


def bound_at(store, as_of):
    """B5 / A4 — 'WHAT BOUND ME AT T', replayed LOCALLY. Every parent rule the child had ever received
    as of position `as_of` — a fold over the child's own record up to T (received_parent_rules read
    as_of). Since every parent rule the child was ever bound by lives in its own record as a received
    row, this recomputes at any T from the child's record alone, forever (B5)."""
    return received_parent_rules(store, as_of)


def received_rules_authored_as_decision(entries):
    """I3 / I7 — THE POSITIVE CONTROL, able-to-fail (the authority.peer_facts_authored_as_decision
    shape at the parent-tree edge): every received-rule ENTRY that is a parent-origin fact
    (source == parent) yet tagged record_class DECISION — a parent's rule admitted as a fact the child
    decided rather than the parent's claim. EMPTY over any real fold by construction (received rules
    are INPUT — the shape of the entries, I7). ABLE TO FAIL: hand it a planted parent-origin entry
    tagged DECISION and it fires (the census read from the SET, the EP-49A RW-COURIER discipline). A
    pure predicate over any iterable of received-rule entries."""
    return [e for e in entries
            if e.get("source") == PARENT_SOURCE and e.get("record_class") != INPUT_RECORD_CLASS]
