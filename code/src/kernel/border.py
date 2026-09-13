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
        _receipt_idempotency_guard(gate, store, actor, opname, p)
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
                   revealed_set=None, actor="SYSTEM"):
    """THIS BODY records its RECEIPT of a crossing in ITS OWN record — a DECISION citing the received
    row's content hash, the from-body (the sender's bound key + genesis hash, D08.42), the sender's
    signature, the under-rule, and the revealed-set (the selective-disclosure leaf set when a tree was
    presented, D08.48; empty otherwise). Idempotent: a second receipt for the same content hash is
    refused at the gate chokepoint (one row, one receipt). Returns the appended receipt record. The
    receipt is B's OWN row — it is appended to B's store through B's gate, and never to A's record."""
    return gate.execute(RECEIPT_OP, actor, {
        "content_hash": content_hash, "from_body": from_body, "from_sig": from_sig,
        "under_rule": under_rule, "revealed_set": revealed_set if revealed_set is not None else {}})
