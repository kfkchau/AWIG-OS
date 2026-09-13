# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture (content-at-rest, per-piece key, wrapped key, sealed content,
# outer/inner fingerprint) per OS textbooks and the fscrypt/eCryptfs/LUKS content-at-rest
# literature. NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""Content-at-rest — the key family's READ direction (EP-46; design/43 addendum, D08.19).

The signing door (EP-37) proves WHO WROTE a record. This proves WHO MAY OPEN its content. A
content piece — already behind its hash by the placement law — is SEALED with its own per-piece
key; that key is WRAPPED to the OPEN key of every allowed reader and stored beside the piece;
OPENING a piece is a recorded row the gate admits only for an allowed reader. LOCATION stays in
the clear (only content is sealed); adding a reader wraps once more (content never re-encrypts);
removing a reader makes a NEW piece — custody conservation (:2856), never a deletion.

THIS MODULE SITS ABOVE THE KERNEL and CONSUMES IT READ-ONLY. It reads the OPEN-key derivation
(`kernel.keys.open_public_key`, the second derived key of an id card) and the estate's ONE hash
form (`kernel.canonical.canonical_hash`, REUSED for both fingerprints, never re-implemented). It
mints NO founding kind and NO check kind: the recorded OPEN op enters the governed way through
`CREATE-OP` (the caller's act, in test worlds), and the seal itself is a code primitive, the shape
of `canonical_hash` and the vault's `seal` — needs-nothing-new (D08.19).

THE SIX POINTS design/43 states, each a property this module holds:

  1. LOCATION NEVER SECRET. Only content is sealed. `SEALED` bytes are ciphertext; `LOCATION` is a
     clear address (verify-without-revealing). A raw read of the sealed bytes yields ciphertext
     ONLY — the content is not recoverable from them without the per-piece key (`seal_bytes`).
  2. TWO DERIVED KEYS. The SIGN key (`keys.bound_key`, unchanged) and the OPEN key
     (`keys.open_public_key` / `keys.open_private_key`) — each doing one job. This module rides the
     OPEN key; it never signs and never touches the sign key's derivation.
  3. WRAPPED TO READERS; ADD = WRAP ONCE MORE; REMOVE = A NEW PIECE. `wrap` maps each reader's
     public open key to the per-piece key sealed for them. `add_reader` wraps the SAME piece key
     once more — the content bytes are byte-identical, never re-encrypted. `remove_reader` produces
     a NEW re-keyed piece wrapped to the remaining readers and RETURNS THE OLD PIECE UNCHANGED — no
     row removed or rewritten (custody conservation, :2856; the one delete this estate forbids).
  4. TWO FINGERPRINTS. `OUTER` over the sealed bytes — anyone verifies the chain over ciphertext
     from record + blob bytes ALONE, no open, no engine, no gate, no view (the air rider, :2963).
     `INNER` over the content — checked only AT opening, by an allowed reader.
  5. OPENING IS A ROW. `open_content` recovers content for an allowed reader; the caller records the
     open (actor, action, object the piece) through the OPEN op, which the signed door admits only
     with the actor's own valid signature (per-account key enforcement, gate.py:143, REUSED). A
     non-reader's open is refused by `open_content` (raising `NotAReader`) and the caller records
     that refusal through the gate.
  6. NEEDS NOTHING NEW. No founding kind, no check kind, no version bump — proven by absence.

HONEST CAP, the SAME one `kernel.vault` names for secrets at rest (design/31 §7). This closes the
SYSTEM path: `open_content` admits an open only for the holder of a reader's own secret whose card
is in the wrapped set, and a non-holder cannot produce that secret (it is one-way behind the
recorded card). It seals the content bytes so a raw read of the blob yields ciphertext. It does NOT
close the on-disk path against a reader of the whole RECORD who derives a public open key and
unseals a wrapped key — a cryptographic trapdoor for that is design/37 §9's deferred primitive,
minted by neither this module nor this EP. The property this module ADDS over the vault's deferral
is that CONTENT bytes at rest are ciphertext, not plaintext; who-may-open is enforced by the gate
and the wrapped-reader set, exactly as who-may-write is by the signed door (RW4).

THE WRONG REFERENCE THIS REFUSES: encryption-at-rest with a master decrypt key — a single key that
opens everything, held by an apex actor above the record. There is none. Each piece has its own
key, wrapped per reader; there is no key that opens all pieces and no actor who can read a piece it
is not a wrapped reader of. The refusal is the vault's refusal (CONST-SECRETS), carried into the
read direction: an apex-actor-above-the-law decrypt path is the shape the constitution forbids.
"""

import hashlib

from kernel import keys                              # the OPEN-key derivation, consumed read-only
from kernel import crypto                            # the ONE vetted-library boundary — real AEAD/wrap when present
from kernel.canonical import canonical_hash          # the estate's ONE hash form, REUSED for both fingerprints


# The piece's fields. LOCATION is the ONLY one in the clear that names WHERE; SEALED is ciphertext;
# WRAP is the per-reader wrapped key set; OUTER/INNER are the two fingerprints (§A of the docstring).
LOCATION = "location"
SEALED = "sealed"
WRAP = "wrap"
OUTER = "outer"
INNER = "inner"
# THE ERA MARKER (KEY-MATERIAL-REAL §3). A piece produced by the REAL path carries `ALG` naming the
# AEAD (`xchacha20poly1305`); a PRE-REAL (modelled) piece has no ALG field and is XOR-sealed. Every
# open/unwrap dispatches on this so a real piece and a pre-real piece each verify under their own era
# — the past stays byte-untouched (a modelled piece is byte-identical to before, ALG absent).
ALG = "alg"


def _is_real_piece(piece):
    """True iff `piece` was sealed by the REAL path (carries the AEAD era marker)."""
    return (piece.get(ALG) if isinstance(piece, dict) else None) == crypto.TAG_AEAD


class NotAReader(Exception):
    """An account opening a piece it is not a wrapped reader of, or presenting a secret that is not
    the holder of its own card. The open is REFUSED (design/43 point 5; RW4). This is the reader
    check's failing column — a check that cannot fail is not a check (§A64)."""


class ContentMismatch(Exception):
    """The INNER fingerprint over the recovered content does not match the piece's recorded inner
    fingerprint — the content does not open to what was sealed (a wrong key, a corrupted blob).
    Raised AT opening, by the allowed reader (design/43 point 4)."""


def _keystream(key, n):
    """A deterministic byte keystream of length `n` from a key string, by chaining `sha256` over
    (key-bytes || counter). A code primitive over RAW bytes — NOT a canonical serialization, so it
    is incidental hashing, not a second governed serializer (the vault/blobs family). The one thing
    it must never be is `hash()` (per-process randomized): a keystream that changed between runs
    would make one piece open to two contents. `sha256` of a fixed key + counter is stable across
    processes and runs, which is what a seal at rest needs."""
    kb = key.encode("utf-8") if isinstance(key, str) else bytes(key)
    out = bytearray()
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(kb + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(out[:n])


def seal_bytes(data, key):
    """Seal (or open) bytes under `key` — XOR against `_keystream(key, len)`. Its OWN inverse:
    `seal_bytes(seal_bytes(x, k), k) == x`. Sealing content makes the blob bytes CIPHERTEXT (the
    content is not recoverable from them without `key`); the same call opens them with the key. A
    keyed transform, a code primitive — no new founding kind, no cryptographic trapdoor minted
    (design/37 §9's deferred primitive is not this)."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    ks = _keystream(key, len(data))
    return bytes(b ^ ks[i] for i, b in enumerate(data))


def new_piece_key():
    """A fresh per-piece key — unpredictable, unique per piece, a SECRET. It is NEVER recorded: it
    lives only wrapped, so recording it would hand every reader-set the whole content (the stop this
    EP names). Randomness is right here — a per-piece key must be unguessable — because it is not a
    record value (records are deterministic; secrets are not)."""
    import os
    return os.urandom(32).hex()


def outer_fingerprint(sealed):
    """The OUTER fingerprint — `canonical_hash` over the SEALED bytes. Anyone verifies the chain
    over ciphertext from the piece alone: no open, no open key, no engine, no gate, no view (the
    air rider, :2963; design/43 point 4). Reused hash, never re-implemented."""
    return canonical_hash(sealed)


def inner_fingerprint(content):
    """The INNER fingerprint — `canonical_hash` over the CONTENT. Checked only AT opening, by an
    allowed reader who has recovered the content (design/43 point 4). Reused hash."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return canonical_hash(content)


def _open_public_of_secret(secret):
    """The PUBLIC open key a holder's secret corresponds to — their own card recomputed from their
    secret, then its open key. This is how a reader reaches the wrap address it was wrapped under
    FROM ITS OWN SECRET (never from the public record alone): only the holder of the secret derives
    it, which is what gates a non-reader out."""
    return keys.open_public_key(keys.sign_public_from_secret(secret))


def seal(content, reader_sign_keys, location, *, piece_key=None):
    """Seal `content` into a piece readable by exactly `reader_sign_keys` (each a reader's RECORDED
    public sign key — `keys.bound_key`). Returns the piece dict.

      * the per-piece key seals the content -> `SEALED` ciphertext (location stays clear);
      * the piece key is WRAPPED to each reader's PUBLIC open key (`keys.open_public_key`, derived
        from the recorded sign key — anyone may wrap TO a reader, no secret needed);
      * the two fingerprints are computed (outer over sealed bytes, inner over content).

    The per-piece key is a fresh secret unless `piece_key` is supplied (a re-key, or a caller
    holding one). It is NEVER placed in the piece in the clear — only its per-reader wrapped forms
    are. A reader with no derivable open key (a keyless account) is skipped: it cannot be wrapped
    to, exactly as it cannot be signed for.

    ERA-SPLIT (KEY-MATERIAL-REAL §3). With the vetted library PRESENT the content is sealed with a
    REAL AEAD (XChaCha20-Poly1305, the location bound as associated data) and the per-piece key is
    WRAPPED to each reader by a REAL X25519 sealed box — the piece carries the `ALG` era marker. With
    it ABSENT the content is XOR-sealed and the key XOR-wrapped exactly as before (no ALG), so a
    fresh checkout seals and opens as today. The two fingerprints are computed the same way in both
    eras (outer over the sealed bytes, inner over the content)."""
    if piece_key is None:
        piece_key = new_piece_key()
    if isinstance(content, str):
        content = content.encode("utf-8")
    real = crypto.real_available()
    if real:
        sealed = crypto.aead_seal(content, piece_key, aad=location)   # AEAD, location as AAD
    else:
        sealed = seal_bytes(content, piece_key)                       # modelled XOR keystream
    wrap = {}
    for sign_key in reader_sign_keys:
        op = keys.open_public_key(sign_key)
        if op is None:
            continue
        if real:
            wrap[op] = crypto.box_wrap(_key_bytes(piece_key), op)     # X25519 sealed box to the open key
        else:
            wrap[op] = seal_bytes(piece_key, op)                      # the piece key, XOR-wrapped
    piece = {
        LOCATION: location,                          # WHERE the sealed content lives — in the clear
        SEALED: sealed,                              # the content, sealed (ciphertext)
        WRAP: wrap,                                  # per-reader wrapped per-piece key
        OUTER: outer_fingerprint(sealed),           # verifiable without opening
        INNER: inner_fingerprint(content),          # checked at opening
    }
    if real:
        piece[ALG] = crypto.TAG_AEAD                 # the era marker — a real piece names its AEAD
    return piece


def _key_bytes(piece_key):
    """The per-piece key as raw bytes for wrapping — a str piece key is utf-8 encoded, bytes pass
    through. Its exact bytes are what a reader recovers by unwrapping and hands back to open."""
    return piece_key.encode("utf-8") if isinstance(piece_key, str) else bytes(piece_key)


def is_reader(piece, reader_sign_key):
    """Is the account holding `reader_sign_key` a WRAPPED READER of this piece? A pure read over the
    wrap set — the account's public open key (derived from its recorded sign key) is one of the wrap
    addresses. Location and existence are never secret, so this is answerable by anyone; it is WHO
    MAY OPEN, not whether the piece is there."""
    op = keys.open_public_key(reader_sign_key)
    return op is not None and op in (piece.get(WRAP) or {})


def unwrap_key(piece, reader_secret):
    """Recover the per-piece key for the holder of `reader_secret`. The holder derives their OWN
    public open key FROM THEIR SECRET (`_open_public_of_secret`), finds their wrap entry, and unseals
    the piece key. Refuses (`NotAReader`) when the derived open key is not in the wrap set — a
    non-reader's secret derives an address that was never wrapped to, and a non-holder cannot present
    a reader's secret at all (it is one-way behind the card). The secret never leaves this call and
    is never recorded.

    ERA-SPLIT (§3): a REAL piece unwraps with the reader's PRIVATE open key (X25519 sealed box, only
    the holder's own secret derives it); a PRE-REAL piece XOR-unwraps under the public open key,
    byte-identical to before."""
    op = _open_public_of_secret(reader_secret)
    wrapped = (piece.get(WRAP) or {}).get(op)
    if wrapped is None:
        raise NotAReader(
            "this account is not a wrapped reader of the piece — its open key is not in the wrapped "
            "set, so there is no key to unwrap (design/43 point 5; the gate admits only a reader)")
    if _is_real_piece(piece):
        open_private = keys.open_private_key(reader_secret)   # derived from the holder's OWN secret
        return crypto.box_unwrap(wrapped, open_private).decode("utf-8")
    return seal_bytes(wrapped, op).decode("utf-8")   # modelled: XOR back under the same open key


def open_content(piece, reader_sign_key, reader_secret):
    """Open a sealed piece as the holder of `reader_sign_key` presenting `reader_secret`. Returns the
    content bytes. This is the ceremony an OPEN op records around (opening is a row, design/43 point
    5).

    THE POSSESSION CHECK REUSES THE SIGNED DOOR'S SHAPE (gate.py:143): the presented secret must be
    the holder of the presented card (`keys.opens_for`) — possession-plus-provenance, a claim checked
    against a recorded key, never a decrypt-and-read. THEN the reader-set check: the account must be a
    wrapped reader. Both can FAIL, and either failure is `NotAReader` — the reader check the gate
    reuses to admit an open only for an allowed reader.

    On success it unwraps the piece key, opens the content, and checks the INNER fingerprint (content
    that does not open to what was sealed raises `ContentMismatch`). A raw read of `piece[SEALED]`
    without this ceremony yields ciphertext only."""
    if not keys.opens_for(reader_secret, reader_sign_key):
        raise NotAReader(
            "the presented secret is not the holder of this card — an open is admitted only for the "
            "holder of a reader's own secret (possession-plus-provenance, the signed door's shape)")
    if not is_reader(piece, reader_sign_key):
        raise NotAReader(
            "this account is not a wrapped reader of the piece — opening is refused and the caller "
            "records the refusal (design/43 point 5; RW4)")
    piece_key = unwrap_key(piece, reader_secret)
    if _is_real_piece(piece):
        # REAL AEAD: a wrong key or a tampered ciphertext fails the Poly1305 tag and raises — mapped
        # to ContentMismatch so the ceremony's failing column is the SAME across eras (design/43 point
        # 4). The AEAD refuses BEFORE the inner check even runs, which is strictly stronger than the
        # XOR era's open-to-garbage-then-inner-catches.
        try:
            content = crypto.aead_open(piece.get(SEALED), piece_key, aad=piece.get(LOCATION))
        except Exception:
            raise ContentMismatch(
                "the sealed content did not open under the recovered key — the AEAD tag rejected it "
                "(a wrong key or a corrupted blob), refused at opening (design/43 point 4)")
    else:
        content = seal_bytes(piece.get(SEALED), piece_key)   # modelled XOR
    if inner_fingerprint(content) != piece.get(INNER):
        raise ContentMismatch(
            "the recovered content does not match the piece's inner fingerprint — it did not open to "
            "what was sealed (a wrong key or a corrupted blob), refused at opening (design/43 point 4)")
    return content


def verify_outer(piece):
    """The OUTER fingerprint check — TRUE iff the recorded outer fingerprint equals `canonical_hash`
    over the piece's sealed bytes. Verifiable by ANYONE over ciphertext, with no open key, no
    engine, no gate, no view — the piece's own bytes and its recorded fingerprint alone (the air
    rider, :2963). A tampered ciphertext reds it. A check that cannot fail is not a check — this one
    fails on any change to the sealed bytes."""
    return piece.get(OUTER) == outer_fingerprint(piece.get(SEALED))


def add_reader(piece, new_reader_sign_key, piece_key):
    """Add a reader by WRAPPING THE SAME PIECE KEY ONCE MORE (design/43 point 3). Returns a NEW piece
    dict with one more wrap entry; the SEALED bytes and BOTH fingerprints are byte-identical — the
    content is NOT re-encrypted. `piece_key` is supplied by a caller who already holds it (the sealer,
    or an existing reader who unwrapped it). The old piece dict is not mutated.

    An add is a WRAP, never a re-seal: re-encrypting the content on every reader add would make the
    outer fingerprint move for a change that added nobody's content, and would re-key readers who did
    not ask to be re-keyed (RW5). ERA-SPLIT (§3): a real piece wraps the same key with an X25519
    sealed box; a pre-real piece XOR-wraps it — the SEALED bytes and both fingerprints are untouched
    in both eras, and the ALG marker is carried through unchanged."""
    op = keys.open_public_key(new_reader_sign_key)
    new_wrap = dict(piece.get(WRAP) or {})
    if op is not None:
        if _is_real_piece(piece):
            new_wrap[op] = crypto.box_wrap(_key_bytes(piece_key), op)
        else:
            new_wrap[op] = seal_bytes(piece_key, op)
    out = dict(piece)
    out[WRAP] = new_wrap
    return out


def remove_reader(piece, content, remaining_reader_sign_keys, *, piece_key=None):
    """Remove a reader by making a NEW piece — re-keyed and wrapped to the REMAINING readers only
    (custody conservation, :2856; design/43 point 3, tail). Returns the NEW piece. The OLD piece is
    NEITHER deleted NOR rewritten — the caller keeps it exactly as it was; it stays sealed to whoever
    it was wrapped for, forever.

    The new piece takes a FRESH per-piece key by default (a re-key), so its sealed bytes differ from
    the old and the removed reader — even holding the old piece key — cannot open the new piece. This
    is removal as CUSTODY CONSERVATION: no row is removed or mutated (the one delete this estate
    forbids); the reader's access ends by a new piece coming into being, not by an old one being
    destroyed (RW6). `content` is supplied by a remaining reader who opened the old piece."""
    return seal(content, remaining_reader_sign_keys, piece.get(LOCATION),
                piece_key=piece_key or new_piece_key())
