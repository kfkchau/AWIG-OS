# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel · OS-architecture
# vocabulary (key binding, custody, ceremony, succession); NON-GOAL: no offensive capability of
# any kind. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS kernel — keys and ceremonies (EP-36; design/37 Q6/Q8, §4): every key with its leash.

A key binds to an account by a recorded act in the ONE store. Binding, rotation and revocation
are records; VALIDITY IS A FOLD over them, evaluated live at every check — latest-supersession-
wins, nothing cascades on revocation because nothing downstream was ever stored (theorem 7
applied to keys, DIGEST-C2 §2). Verification bottoms out at the FOUNDING (design/31 J1); the
record IS the distribution. This module is the ENGINE — the pure fold + the anchor derivation +
the vault-class custody consumption; it holds no state and takes the store/views it reads.

TWO WRONG REFERENCES REFUSED (design/37 EP-36 "THE REFERENCE TO AVOID"; vault.py's own note):

  THE PKI HIERARCHY — certificate authorities, trust stores, certificate files, expiry
  calendars. Taking it puts an authority ABOVE the founding (against J1), stores trust state
  OUTSIDE the record, and re-invents revocation distribution when the record already answers
  revocation LIVE at every check. A key here is a recorded fact with a fold, not a certificate
  with an issuer.

  THE PASSWORD-MANAGER / KMS — a system key you can decrypt-and-read-back to sign with. The
  system key sits in VAULT-CLASS custody (EP-19's vault, CONSUMED unchanged): the value crosses
  ONCE, is sealed, and NO read path exists. A key held in closure cannot be read to sign with —
  so the store's countersignature is possession-in-custody + minted provenance (the recording
  fact), never a decrypt-and-sign (see `countersign`). The impossibility is architectural.

FOUNDING-MOVE HELD (OWNER GATE — EP-36-BUILD §8-g, board :2754; the MEM/SCHED precedent). The
key-bind LAW and the key-rotate/key-revoke DECISION ops are NEW FOUNDING VOCABULARY whose CREATE
rides the owner's "create the key family" word on the one-sitting batch. This module is built and
proven NOW, INERT until the law is declared: a world whose founding declares no key-bind law
binds no key, folds to the base state, and leashes nothing — exactly as `declared_roots` yields
{} for a world with no key space. The founding DATA (founding-pack.json) stays byte-untouched
until the word lands, at which point A6/§A57 flip live as a mechanical completion.

THE DOOR IS NOT HERE. This EP makes key state DERIVABLE; the gate's signature acceptance flips in
EP-37 (which makes the door READ this state). No signature enforcement at the gate lands here.

THE READ DIRECTION (EP-46; design/43 addendum, D08.19) — ADDITIVE, the SIGN key above untouched.
Signing proves WHO WROTE; a SECOND derived key proves WHO MAY OPEN. `bound_key` is the SIGN key
and does not change by one line here (its EP-36 acceptances stay green). The OPEN key is derived
BELOW, at the tail of this module — two keys each doing ONE job (design/43 point 2). NO new founding
kind, NO new check, NO version bump enters through this addition: the derivations are code
primitives, the shape of `canonical_hash` and `countersign`, and NO secret ever enters the record.
"""

from .canonical import canonical_hash

# ---- the ONE stream, class-tagged (design/37 §4) --------------------------------------------
# The three key-lifecycle record kinds carried as the payload's class tag, all in the one stream.
KEY_BIND = "key-bind"          # LAW-class: a verification anchor, account <-> public key
KEY_ROTATE = "key-rotate"      # DECISION: supersede the binding with a new public key
KEY_REVOKE = "key-revoke"      # DECISION: supersede the binding to none (revoked)
KEY_KINDS = (KEY_BIND, KEY_ROTATE, KEY_REVOKE)

# The rule_id a founding key-bind LAW declares. Its PRESENCE in the live law is the wire-at-birth
# gate that makes the succession key half and the root anchor ENGAGE (key_law_live). Held until
# the owner's word; a world without it sees exactly the succession behaviour it saw before.
KEY_LAW_BIND = "KEY-LAW-BIND"

# The vault name the system key is sealed under (F2). Custody only; there is no read path.
SYSTEM_KEY_NAME = "system-key"

# Record/payload field names.
ACCOUNT = "account"
PUBLIC_KEY = "public_key"
CLASS = "class"                # the §4 class tag on a key record ("LAW" | "DECISION")

# The anchor citation — CONST-AUTHORITY-ANCHORED in cryptographic form (design/37 Q8): the same
# root-never-orphans law the succession ceremony already carries, now over the root KEY.
KEY_ANCHOR_RULE = "CONST-AUTHORITY-ANCHORED"


# ---- the live validity fold (F1) ------------------------------------------------------------

def _key_records(store, account, as_of=None, accelerated=True):
    """Every key-lifecycle record for `account` in seq order — recognised by the payload's class
    tag (`kind` in KEY_KINDS), never by a hard-coded action-name list, so the fold reads a key act
    however its op was spelled (the active_rules recognition precedent). A fold over the record;
    nothing stored.

    THE SOURCE, NOT THE FOLD, IS WHAT `accelerated` VARIES (KEY-PROJECTION, board :2906/:2910,
    Option A; the accelerated/oracle split of views.view_fold, one fold body, two record sources):

      accelerated=True   read `store.key_projection(account)` — a SUBSET read of exactly this
                         account's key records, NOT a whole-record scan. This is the production
                         path: the signed door (EP-37 / mover-2) reads at operation rate without
                         scanning the record, so T-PER-ACT-PATH-READS-SUBSETS holds once the door
                         is wired. A `WorldStore` answers this in the as-of-past frame because its
                         `events` are already deciding-time-folded (binding 1, one read path).
      accelerated=False  read `store.all` directly — the WHOLE record, the UNACCELERATED ORACLE and
                         the definitional spec, retained as the standing differential baseline the
                         projection is proven against.

    THE FOLD BELOW IS UNCHANGED by this: binding 2 — the fold is the spec, never bent to match the
    projection; `accelerated` swaps only which store surface hands it the records."""
    source = store.key_projection(account) if accelerated else store
    out = []
    for e in source.all(as_of):
        p = e.get("payload") or {}
        if p.get("kind") in KEY_KINDS and p.get(ACCOUNT) == account:
            out.append(e)
    return out


def bound_key(store, account, as_of=None, accelerated=True):
    """The public key VALID for `account` NOW — latest bind/rotate wins, a revoke supersedes to
    None (latest-supersession-wins; theorem 7 applied to keys — nothing cascades because nothing
    downstream was stored). DERIVED live every call: there is no trust store and no stored validity
    to rot. `as_of` returns the binding valid AT a past deciding time — the SAME fold pointed at
    then (A5; EP-38 needs validity-as-of-deciding-time). An old public key superseded by a rotation
    stays on the record as DATA (an old signature over it remains verifiable as evidence of who
    decided); it is simply no longer the LIVE binding.

    `accelerated` (default True — the production path) selects the record SOURCE, never the fold:
    the per-account key projection when True, the whole-record oracle when False. The RETURN VALUE
    is identical either way (KEY-PROJECTION, board :2906/:2910); the caller contract is unchanged."""
    key = None
    for e in _key_records(store, account, as_of, accelerated):
        p = e["payload"]
        if p["kind"] == KEY_REVOKE:
            key = None
        else:                                   # bind or rotate: the newest public key wins
            key = p.get(PUBLIC_KEY)
    return key


def key_valid(store, account, as_of=None):
    """Does `account` hold a live, non-revoked key binding? DERIVED per check, never a stored
    boolean (design/31 J1). A revoked or never-bound account returns False."""
    return bound_key(store, account, as_of) is not None


def key_law_live(views, as_of=None):
    """Is the key-bind LAW declared in the live law? The leash's WIRE-AT-BIRTH gate. A world whose
    founding declares no key-bind law binds no key and leashes nothing, so the succession key half
    and the root anchor stay INERT and every world founded before the key-family create sees
    exactly the succession behaviour it saw before (this is what keeps the held founding-move from
    silently breaking succession). Read from active_rules — a LAW is self-declared by its rule_id
    (views._active_rules), never a hard-coded flag."""
    return KEY_LAW_BIND in views.active_rules(as_of)


def root_key(store, views, as_of=None):
    """The ROOT KEY (F3) — the public key founding-asserted for the root authority holder (the
    chain-end, DERIVED; never a hard-coded 'owner'). Nothing sits above the root to verify its key
    against — the same self-aware limitation J1 states for root identity (design/37 Q6). DERIVED:
    the live binding for the root account, or None where the ceremony has not sealed one (held
    until F6/§8-i — test keys until the owner's word)."""
    return bound_key(store, views.chain_end(as_of), as_of)


# ---- the anchor (F4/F5) — the root key's leash, in cryptographic form -----------------------

def successor_key_bound(store, views, as_of=None):
    """Is a successor key BOUND THROUGH SUCCESSION — does the CURRENT successor (the live
    designation/acceptance fold, verified + human re-checked at read, views.current_successor)
    hold a valid key binding? The root-key anchor and the handover key half both read this: root
    authority never retires its key without a successor key bound through the recorded, HUMAN-ONLY
    ceremony (CONST-AUTHORITY-ANCHORED in cryptographic form, design/37 Q8). The human-only leash
    is inherited whole from current_successor — this adds the key requirement ON TOP, never in
    place of it."""
    succ = views.current_successor(as_of)
    return succ is not None and key_valid(store, succ, as_of)


def is_root_key_op(views, draft, as_of=None):
    """Does this key-rotate/key-revoke draft target the ROOT KEY — the key bound to the current
    root authority holder (the chain-end)? ONLY root key ops are leashed; a NON-root key
    rotates/revokes unleashed (the guard DISCRIMINATES, it does not block — RW1's near-miss)."""
    p = draft.get("payload") or {}
    if p.get("kind") not in (KEY_ROTATE, KEY_REVOKE):
        return False
    return (p.get(ACCOUNT) or draft.get("object")) == views.chain_end(as_of)


# ---- the system key in vault-class custody (F2) — CONSUMES vault.py, closure unchanged -------

def seal_system_key(vault, value):
    """Seal the system key into VAULT-CLASS custody (EP-19's vault, CONSUMED — its closure does not
    change by one line, F2 wires the signing CALL, not the vault): the value crosses ONCE, is
    sealed write-once keyed by its own hash, and only that HASH leaves. There is NO read path — the
    wrong reference (a KMS/password-manager that decrypts the key back to sign with it) is refused
    by ABSENCE, exactly as vault.py refuses it. Returns the sealed hash ('sha256:<hex>')."""
    return vault.seal(value)


def countersign(record, system_key_hash):
    """The store's countersignature over an appended record (design/37 Q2: the store's signature
    binds the RECORDING fact). It is STORE MINTING — the seq/record_time class, below the gate, at
    I9 rate (ADDENDUM-1 item 2; NOT an audit-pack action — a per-append mirror would double the
    stream the pack exists to avoid). Derived from the record's OWN minted envelope (seq,
    record_time) bound under the system key's PUBLIC custody hash; it reads NO sealed value back. A
    key held in closure cannot be read to sign with — so the countersignature is possession-in-
    custody plus minted provenance, never a decrypt-and-sign. `verify_countersign` is its derived
    check."""
    return {"custody": system_key_hash,
            "seq": record.get("seq"),
            "record_time": record.get("record_time")}


def verify_countersign(mark, record, system_key_hash):
    """Verify a countersignature — a DERIVED CHECK, never a mirrored record. The mark must bind
    THIS record's minted recording fact (seq, record_time) under the system key currently in
    custody (its public hash). Recomputed on demand from PUBLIC data only; it reads no sealed value
    and touches no vault storage. A False here is an honest NO-MATCH, never a read path."""
    return (isinstance(mark, dict)
            and mark.get("custody") == system_key_hash
            and mark.get("seq") == record.get("seq")
            and mark.get("record_time") == record.get("record_time"))


# ---- the OPEN key: the id card's SECOND derived key, the read direction (EP-46) -------------
# design/43's read direction, D08.19. `bound_key` above is the SIGN key (WHO WROTE); this adds
# its twin, the OPEN key (WHO MAY OPEN). ONE identity derives TWO keys, each doing ONE job — one
# key doing both is weaker than two doing one (design/43 point 2). Three facts hold here, and they
# are the two precisions bound at this EP's countersign:
#
#   THE PUBLIC OPEN KEY derives from the RECORDED PUBLIC SIGN KEY (`open_public_key`), so anyone
#   holding the record derives it and ANYONE MAY WRAP TO A READER — no secret needed to address a
#   reader. It is derived live every call, never a stored value (the estate's derive-never-store
#   law; the same posture `bound_key` holds).
#
#   THE PRIVATE OPEN KEY derives from the HOLDER'S OWN SECRET (`open_private_key`), LOCALLY, and it
#   NEVER touches the record or reaches a seat — only the holder derives it, only the holder opens
#   (design/43 point 5). A build that recorded private key material would be a stop; nothing here
#   records a secret.
#
#   THE SECRET IS ONE-WAY BEHIND THE RECORDED CARD (`sign_public_from_secret` is the commitment
#   `bound_key` returns after a KEY-BIND), so a non-holder cannot produce the secret behind a
#   reader's card, and the open ceremony's possession check (`opens_for`) is possession-plus-
#   provenance — the SAME shape as the signed door's `verify_invoker_sig` (a claim checked against
#   a recorded key), never a decrypt-and-read.
#
# HONEST CAP, the SAME one `vault.py` names for secrets at rest (design/31 §7) and `gate.py` names
# for signatures (design/37 §9): key material is modelled here as opaque strings, the shape of this
# estate's test key material. This closes the SYSTEM path — the seal ceremony admits an open only
# for the holder of a reader's own secret whose card is in the wrapped set. A real cryptographic
# keypair whose trapdoor would ALSO close the on-disk path (a raw-record reader deriving a public
# open key and unsealing a wrapped key) is design/37 §9's deferred primitive, minted by neither
# this module nor this EP — needs-nothing-new (D08.19).

OPEN_PUBLIC = "openpub"      # the wrap-address key: derived from the recorded PUBLIC sign key
OPEN_PRIVATE = "openpriv"    # the holder's open capability: derived from their OWN secret


def sign_public_from_secret(secret):
    """The PUBLIC SIGN key an id card records for a holder whose own secret is `secret` — a one-way
    commitment (`canonical_hash`) to that secret, the recorded half of the keypair whose private
    half is the secret. `bound_key` returns exactly this after a KEY-BIND. The secret itself is
    NEVER recorded; only this commitment is. Test worlds bind this so the read direction's two open
    keys correspond (open_public from the card, open_private from the secret); the estate's live key
    material is the owner's own act (F6/§8-i), unchanged by this addition."""
    return "signpub:" + canonical_hash({"sign-of-secret": secret})


def open_public_key(sign_public_key):
    """The PUBLIC open key — the id card's SECOND derived key, DERIVED FROM THE RECORDED PUBLIC SIGN
    KEY. Content is WRAPPED TO this key; anyone holding the record derives it, so anyone may wrap to
    a reader (design/43 points 2/3). Derived live from the record every call, never a stored value.
    None for an account holding no bound sign key — a keyless account has no open key, exactly as it
    has no live signing binding."""
    if sign_public_key is None:
        return None
    return OPEN_PUBLIC + ":" + canonical_hash({"open-of-sign": sign_public_key})


def open_private_key(secret):
    """The PRIVATE open key — derived by the actor from THEIR OWN SECRET, LOCALLY. It is the holder's
    capability to open what was wrapped to their public open key, and it NEVER enters the record or
    reaches a seat. A non-holder cannot derive it (the secret is one-way behind the recorded card),
    so only the holder opens (design/43 point 5). Distinct from `open_public_key` — two derived
    keys, each one job: this one is never a wrap address and never signs, and the sign/public-open
    keys never open (RW3, the one-key-doing-both red)."""
    return OPEN_PRIVATE + ":" + canonical_hash({"open-of-secret": secret})


def opens_for(secret, sign_public_key):
    """Does a holder possessing `secret` legitimately hold the card that recorded `sign_public_key`?
    A DERIVED check — possession-plus-provenance, the SAME shape as the signed door's
    `verify_invoker_sig` (there the mark cites the bound key; here the secret commits to the recorded
    sign key). True iff `sign_public_from_secret(secret)` equals the recorded key. The seal ceremony
    admits an open only for the holder of the reader's own secret; a False is an honest no-match, and
    it is what lets the ceremony's reader check FAIL (a check that cannot fail is not a check). No
    secret is ever read back — this recomputes a commitment from public arithmetic and compares."""
    return sign_public_key is not None and sign_public_from_secret(secret) == sign_public_key
