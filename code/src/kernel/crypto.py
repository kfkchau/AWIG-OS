# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel · applied-cryptography
# vocabulary (signature, authenticated encryption, key derivation, key wrapping) per the libsodium
# literature; NON-GOAL: no offensive capability of any kind — this module BUILDS confidentiality and
# integrity primitives, it attacks nothing. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS kernel — the ONE vetted-library boundary and the presence detector (KEY-MATERIAL-REAL).

Real cryptography for the whole key family lives behind THIS module and nowhere else. Every real
primitive — Ed25519 signatures, X25519 key wrapping, XChaCha20-Poly1305 authenticated encryption —
is called through here; the vetted library (libsodium via PyNaCl) is imported in ONE place, and
PRESENCE is detected here alone (the plan's "one boundary"). A change of library is a change of this
file only; every caller reads `real_available()` and the tagged primitives, never `import nacl`.

THE LIBRARY IS AN OPTIONAL EXTRA, NOT A REQUIREMENT (owner's word 2026-09-08, board :3218). With it
ABSENT the estate runs EXACTLY as today — stand-in (modelled) keys, the whole ledger green unchanged,
and this is the current baseline: nothing is installed. A REAL (tagged) operation with the library
absent REFUSES, citing the absent library (`LibraryAbsent`), and NEVER falls back to the modelled
path — no silent downgrade (RW-DOWNGRADE). With it PRESENT the tagged path is real. A fresh checkout
runs and tests with nothing installed; one package turns real keys on.

THE ERA TAG IS THE SWITCH (design/37 §9's deferred primitive, made real; the EP-35 era-split shape).
Every value THIS module produces carries an ALGORITHM TAG (`ed25519`, `x25519`, `x25519-box`,
`xchacha20poly1305`). A value with no real tag is a PRE-REAL (modelled) value and verifies under the
modelled path; a tagged value verifies ONLY through the real path, which EXISTS only when the library
is present. So the past stays byte-untouched and the boundary is honest.

TWO WRONG REFERENCES REFUSED, the same two the key family already refuses (keys.py / seal.py / vault.py),
now carried into real material:
  HAND-ROLLED CRYPTO — a primitive coded by hand rather than through this one vetted surface. Refused
  by construction: the algorithms here are libsodium's, wrapped, never re-implemented (stop h).
  THE MASTER KEY / KMS — a single key that opens or signs for everything, or a decrypt-and-read path
  that hands a private key back to a caller. Refused: signing reads a private key only INSIDE its
  own call and returns a signature (never the key); each piece is wrapped per reader, no master
  decrypt key exists. The impossibility the vault draws for secrets at rest is carried into real
  signing — a use, never a read.

NO FOUNDING MOVE. This is a code primitive: no new op, no new check kind, no version bump. The
founding vocabulary is byte-untouched; only the code behind the unchanged key-family interfaces
changes from modelled to real.
"""

import hashlib
import hmac
import os

# ---- THE ONE IMPORT SITE ---------------------------------------------------------------------
# libsodium via PyNaCl. Imported in THIS place only; presence detected here and nowhere else. A
# failure to import (absent, or a broken install) leaves the estate on the modelled path — never a
# crash at import, because absence is a first-class supported state (the OPTIONAL-EXTRA law).
try:  # pragma: no cover - the branch taken depends on whether the optional extra is installed
    import nacl.bindings as _sodium
    import nacl.signing as _signing
    import nacl.public as _public
    import nacl.exceptions as _naclexc
    _IMPORTED = True
except Exception:  # ImportError, or any load failure of the native library
    _IMPORTED = False

# The FORCE-ABSENCE HOOK (A9): absence is SIMULATED at THIS boundary, never by uninstalling. When
# GOVOS_CRYPTO_FORCE_ABSENT is set in the environment, `real_available()` reports False even where
# the library imports — so the refusal path (and its ability to fail) is provable WITH the library
# installed, in one interpreter, exactly as the plan requires.
_FORCE_ABSENT_ENV = "GOVOS_CRYPTO_FORCE_ABSENT"

LIBRARY_NAME = "libsodium via PyNaCl"

# ---- ALGORITHM TAGS (§3) — every real value names its algorithm ------------------------------
TAG_SIG_PK = "ed25519"           # a real signing PUBLIC key:      "ed25519:<hex>"
TAG_SIG = "ed25519-sig"          # a real signature:                "ed25519-sig:<hex>"
TAG_OPEN_PK = "x25519"           # a real PUBLIC open key:          "x25519:<hex>"
TAG_OPEN_SK = "x25519-priv"      # a real PRIVATE open key (a secret; never recorded): "x25519-priv:<hex>"
TAG_WRAP = "x25519-box"          # a real wrapped per-piece key:    "x25519-box:<hex>"
TAG_AEAD = "xchacha20poly1305"   # the AEAD algorithm tag (a piece's ALG marker)
# The set that routes a value to the REAL verification path. A value tagged with none of these is
# a PRE-REAL (modelled) value and verifies under the modelled path (the era-split).
REAL_TAGS = (TAG_SIG_PK, TAG_SIG, TAG_OPEN_PK, TAG_OPEN_SK, TAG_WRAP, TAG_AEAD)

_NONCE_BYTES = 24                 # XChaCha20-Poly1305 nonce width — safe under random generation (§3)


class LibraryAbsent(RuntimeError):
    """A REAL (tagged) operation was requested with the vetted library ABSENT. The refusal CITES the
    absent library and NEVER falls back to the modelled path — no silent downgrade (RW-DOWNGRADE,
    stop j). Absence is simulated at THIS boundary; the message names the one optional package that
    turns real keys on. This is the failing column A9 proves able to fire."""


# ---- PRESENCE ---------------------------------------------------------------------------------

def real_available():
    """Is the vetted library present AND not force-absent? The ONE presence read in the estate.
    False when GOVOS_CRYPTO_FORCE_ABSENT is set (the A9 simulate-absence hook) or when the import
    failed (the current baseline — nothing installed)."""
    if os.environ.get(_FORCE_ABSENT_ENV):
        return False
    return _IMPORTED


def require_real(op):
    """Guard entered by every real primitive: refuse (never fake) when the library is absent. The
    refusal cites the absent library and names the one package; it does NOT return a modelled value."""
    if not real_available():
        raise LibraryAbsent(
            "real cryptography for '%s' needs the vetted library (%s), which is ABSENT — refused "
            "rather than faked with modelled material (no silent downgrade); install the one "
            "optional package to turn real keys on" % (op, LIBRARY_NAME))


def is_real_value(value):
    """True iff `value` was produced by the real path — a string carrying a real algorithm tag. A
    modelled value ('signpub:...', 'openpub:...', 'openpriv:...') returns False and routes to the
    modelled path; this is the era-split's dispatch (§3)."""
    return isinstance(value, str) and ":" in value and value.split(":", 1)[0] in REAL_TAGS


# ---- TAG HELPERS ------------------------------------------------------------------------------

def _tag(tag, raw):
    """Encode raw bytes as the tagged value 'tag:hex'."""
    return tag + ":" + raw.hex()


def _untag(expected_tag, value):
    """Decode a tagged value back to raw bytes, refusing a tag mismatch (a value presented under the
    wrong algorithm is a no-match, not a silent reinterpretation)."""
    if not (isinstance(value, str) and value.startswith(expected_tag + ":")):
        raise ValueError("expected a %s value, got %r" % (expected_tag, value))
    return bytes.fromhex(value.split(":", 1)[1])


# ---- KEY DERIVATION (the id card secret -> its keys) -----------------------------------------
# HKDF-SHA256 with a distinct info label per derived key (§3): the id card secret derives an Ed25519
# SIGN seed; the X25519 OPEN keypair is the standard birational image of that Ed25519 keypair
# (libsodium's ed25519->curve25519), so the PUBLIC open key derives from the RECORDED public sign
# key (anyone may wrap to a reader) and the PRIVATE open key derives from the holder's own secret —
# each doing one job, neither substituting for the other (RW3), exactly the structure the modelled
# code already held (open-of-sign / open-of-secret).

_ED_SEED_INFO = b"gov-os:key-material-real:ed25519-sign-seed:v1"


def _hkdf_sha256(secret_bytes, info, length):
    """HKDF (RFC 5869) over SHA-256 — extract then expand — deriving `length` bytes bound to `info`.
    Stdlib only; a KDF is a code primitive (no library, no new founding kind)."""
    prk = hmac.new(b"\x00" * hashlib.sha256().digest_size, secret_bytes, hashlib.sha256).digest()
    out, t, counter = b"", b"", 1
    while len(out) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        out += t
        counter += 1
    return out[:length]


def _sign_seed_from_secret(secret):
    """The Ed25519 SIGN seed for a holder whose own secret is `secret` — HKDF of the secret under the
    sign-seed info label. Deterministic, so the recorded public key and the local private key
    correspond every call. The seed is a SECRET; it is never recorded."""
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    return _hkdf_sha256(secret, _ED_SEED_INFO, 32)


# ---- Ed25519 SIGNATURES -----------------------------------------------------------------------

def sign_public_from_secret(secret):
    """The real Ed25519 PUBLIC signing key for a holder's secret — the recorded half of the keypair
    (tagged 'ed25519:<hex>'). The secret and the private key are never recorded."""
    require_real("ed25519 public key")
    seed = _sign_seed_from_secret(secret)
    pk, _sk = _sodium.crypto_sign_seed_keypair(seed)
    return _tag(TAG_SIG_PK, pk)


def public_from_seed(seed_bytes):
    """The real Ed25519 PUBLIC key for a raw 32-byte signing seed — used by the vault to publish the
    system key's public half (a public value, safe to expose) without any read of the sealed seed by
    a caller."""
    require_real("ed25519 public key")
    pk, _sk = _sodium.crypto_sign_seed_keypair(seed_bytes)
    return _tag(TAG_SIG_PK, pk)


def sign_with_seed(seed_bytes, message):
    """A real Ed25519 signature over `message` by the private key of `seed_bytes` (tagged
    'ed25519-sig:<hex>'). The seed is used INSIDE this call and never returned — the vault's SIGN op
    calls this on its sealed seed: a use, never a read."""
    require_real("ed25519 sign")
    if isinstance(message, str):
        message = message.encode("utf-8")
    sk = _signing.SigningKey(seed_bytes)
    return _tag(TAG_SIG, sk.sign(message).signature)


def verify(public_tagged, sig_tagged, message):
    """True iff `sig_tagged` is a valid Ed25519 signature over `message` under `public_tagged`. A
    signature under a DIFFERENT key, or over ALTERED bytes, returns False (an honest no-match — the
    check that can fail, RW-FORGE). Both operands must be real-tagged; a modelled value here is a
    caller error, not a real verification."""
    require_real("ed25519 verify")
    pk = _untag(TAG_SIG_PK, public_tagged)
    sig = _untag(TAG_SIG, sig_tagged)
    if isinstance(message, str):
        message = message.encode("utf-8")
    try:
        _signing.VerifyKey(pk).verify(message, sig)
        return True
    except _naclexc.BadSignatureError:
        return False


# ---- X25519 KEY WRAPPING (per-piece key -> reader's open key) ---------------------------------

def open_public_from_sign_public(sign_public_tagged):
    """The real PUBLIC open key — the birational image of the recorded Ed25519 public sign key
    (libsodium ed25519->curve25519), tagged 'x25519:<hex>'. Derivable by anyone holding the record,
    so anyone may wrap TO a reader with no secret (design/43 points 2/3)."""
    require_real("x25519 public open key")
    ed_pk = _untag(TAG_SIG_PK, sign_public_tagged)
    x_pk = _sodium.crypto_sign_ed25519_pk_to_curve25519(ed_pk)
    return _tag(TAG_OPEN_PK, x_pk)


def open_private_from_secret(secret):
    """The real PRIVATE open key for a holder's own secret — the birational image of the holder's
    Ed25519 private key (tagged 'x25519-priv:<hex>'). Derived LOCALLY from the secret; never recorded
    and never at a seat. It corresponds to `open_public_from_sign_public(sign_public_from_secret(
    secret))` because both are the curve25519 image of the SAME Ed25519 keypair."""
    require_real("x25519 private open key")
    _pk, sk = _sodium.crypto_sign_seed_keypair(_sign_seed_from_secret(secret))
    x_sk = _sodium.crypto_sign_ed25519_sk_to_curve25519(sk)
    return _tag(TAG_OPEN_SK, x_sk)


def box_wrap(plaintext, open_public_tagged):
    """Wrap `plaintext` (the per-piece key) to a reader's PUBLIC open key with an X25519 sealed box
    (ephemeral-static ECDH -> AEAD), tagged 'x25519-box:<hex>'. Adding a reader wraps once more; the
    content is never re-encrypted."""
    require_real("x25519 wrap")
    x_pk = _untag(TAG_OPEN_PK, open_public_tagged)
    box = _public.SealedBox(_public.PublicKey(x_pk))
    return _tag(TAG_WRAP, box.encrypt(plaintext))


def box_unwrap(wrapped_tagged, open_private_tagged):
    """Recover the wrapped bytes with the reader's PRIVATE open key. A non-reader's key fails the
    sealed box (a wrong key is a refusal, not a silent wrong-plaintext)."""
    require_real("x25519 unwrap")
    ct = _untag(TAG_WRAP, wrapped_tagged)
    x_sk = _untag(TAG_OPEN_SK, open_private_tagged)
    box = _public.SealedBox(_public.PrivateKey(x_sk))
    return box.decrypt(ct)


# ---- AEAD (content sealing) -------------------------------------------------------------------

def _aead_key(material):
    """A stable 32-byte AEAD key from any per-piece key material — HKDF-Expand of the material. The
    per-piece key is a secret; deriving a fixed-width key from it is a KDF use, not a serializer."""
    if isinstance(material, str):
        material = material.encode("utf-8")
    return _hkdf_sha256(material, b"gov-os:key-material-real:aead-key:v1", 32)


def aead_seal(plaintext, piece_key, aad=b""):
    """Seal `plaintext` under `piece_key` with XChaCha20-Poly1305 and a fresh 24-byte random nonce,
    authenticating `aad` (the piece's clear location, so the ciphertext is bound to WHERE it lives).
    Returns nonce||ciphertext||tag as raw bytes — the plaintext is NOT recoverable from them without
    the key (RW-SEAL). Random nonce, so the sealed bytes differ every call."""
    require_real("aead seal")
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")
    if isinstance(aad, str):
        aad = aad.encode("utf-8")
    key = _aead_key(piece_key)
    nonce = os.urandom(_NONCE_BYTES)
    ct = _sodium.crypto_aead_xchacha20poly1305_ietf_encrypt(plaintext, aad, nonce, key)
    return nonce + ct


def aead_open(sealed, piece_key, aad=b""):
    """Open sealed bytes (nonce||ciphertext||tag) under `piece_key`. A wrong key or a tampered
    ciphertext fails the Poly1305 tag and raises `nacl.exceptions.CryptoError` — never a silent
    wrong-plaintext. `aad` must match what was sealed."""
    require_real("aead open")
    if isinstance(aad, str):
        aad = aad.encode("utf-8")
    key = _aead_key(piece_key)
    nonce, ct = sealed[:_NONCE_BYTES], sealed[_NONCE_BYTES:]
    return _sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(ct, aad, nonce, key)


def aead_tag_ok(sealed, piece_key, aad=b""):
    """True iff `sealed` opens cleanly under `piece_key` — a wrong key or a tamper returns False
    (the AEAD's failing column, RW-SEAL). A convenience for the reader-side check."""
    require_real("aead verify")
    try:
        aead_open(sealed, piece_key, aad)
        return True
    except Exception:
        return False


# ---- FRESH SECRETS (never recorded) -----------------------------------------------------------

def new_signing_seed():
    """A fresh 32-byte Ed25519 signing seed — a SECRET, sealed in the vault, never recorded."""
    return os.urandom(32)
