# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel · applied-cryptography
# vocabulary (signature, custody, key derivation) per the libsodium literature; NON-GOAL: no
# offensive capability of any kind — this module HOLDS a signing key in custody and produces
# signatures, it attacks nothing. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS kernel — the SIGNING KEY STORE (KEY-MATERIAL-REAL A4; archi :3249): sign, never reveal.

The signer holds SYSTEM-class Ed25519 signing keys — the store's countersignature key and the
attestation-seal key — BESIDE the vault, under the vault's own discipline: a seed crosses ONCE at
the ceremony (`seal`), is held in custody, and is USED to produce a real signature (`sign`) — a use,
never a read. The surface is EXACTLY three operations: `seal`, `sign`, `compare_public`. There is
deliberately NO `get`, `read`, `reveal`, `open`, `export` — no method returns the private seed. The
possession-in-custody producing a signature is the `keys.countersign` pattern MADE REAL; the key
never leaves the signer.

WHY BESIDE THE VAULT, NOT INSIDE IT (archi's design ruling :3249). The vault (`vault.py`) is the
estate's oldest closure and is BYTE-FROZEN (sha256 2038a8cd…): its five guards pin its bytes, its
public surface to exactly {seal, compare}, and its source to no read path. A SIGN operation ON the
vault would change its bytes and red those guards — and, worse, an in-vault signature would have to
read the sealed seed back to sign with it, which the vault's no-read-path law forbids. So the
signing key lives HERE, in its own store, and `vault.py` is not touched. The vault seals SECRET
VALUES that are only ever compared; the signer seals a SIGNING SEED that is only ever USED to sign.

THE SEED IS NEVER AT REST. Unlike the vault (which persists sealed bytes to disk under its honest
"the disk path is not closed" cap), the signer holds the seed IN MEMORY only — a private custody map,
never written to disk. A key that is USED within a boot session needs no disk home, and keeping the
seed off disk is a STRONGER posture than the vault's on-disk sealing (the on-disk custody cap the
vault names does not even arise here). The seed is used to sign and is discarded when the store is.

TWO WRONG REFERENCES REFUSED (the vault's own two, carried into real signing):

  THE KMS / DECRYPT-AND-READ — a `get_key` / `reveal` that hands the private key back to a caller to
  sign with elsewhere. Refused by ABSENCE, exactly as the vault refuses it: `sign` consumes the seed
  INSIDE this module and returns a signature; `compare_public` returns a bool; no method returns the
  seed. The impossibility is architectural — there is no read op to call.

  THE IN-VAULT SIGN — adding a SIGN op to `vault.py`. Refused by BUILDING BESIDE the vault (:3249):
  the vault stays byte-frozen, and the signing key's custody is a separate store with its own no-read
  discipline.

NO FOUNDING MOVE. This is a code primitive: no new op, no new check kind, no version bump. The
signer is custody mechanics behind the unchanged `keys.countersign` / attestation-seal interfaces.
"""

import hashlib

from . import crypto  # the ONE vetted-library boundary — real signatures when present, refused when absent


class SigningKeyStore:
    """A custody for SYSTEM-class Ed25519 signing seeds — like the vault, MINUS every read path, PLUS
    one internal USE (`sign`). `seal` takes a seed in and hands a custody handle out; `sign` produces a
    real signature with the sealed seed without ever returning it; `compare_public` answers whether a
    candidate public key is the sealed key's real public half — a bool, never the key. The seed is held
    in memory and never leaves: the ABSENCE of a read path is the guarantee, as it is for the vault."""

    def __init__(self):
        # custody handle -> seed bytes. In memory only; never written to disk (the seed is never at
        # rest). Private: no public method exposes it; `sign` / `compare_public` consume it internally.
        self._seeds = {}

    def seal(self, seed):
        """Seal a signing seed into custody at the ceremony — the seed crosses ONCE and is held keyed
        by its own hash (write-once; identical seeds coincide, like the vault and the blob store).
        Returns the custody handle ('sha256:<hex>') — a public commitment to the seed, the ONLY thing
        that leaves this call. The seed itself is never returned and never written to disk; there is no
        read path to get it back."""
        if isinstance(seed, str):
            seed = seed.encode("utf-8")
        custody = "sha256:" + hashlib.sha256(seed).hexdigest()
        self._seeds.setdefault(custody, seed)  # write-once; a re-seal of the same seed is a no-op
        return custody

    def sign(self, custody, message):
        """A real Ed25519 signature over `message` by the seed sealed under `custody` — a USE, never a
        read. The seed is consumed INSIDE this call (via the one vetted-library boundary) and never
        returned; only the tagged signature ('ed25519-sig:<hex>') leaves. With the vetted library ABSENT
        the boundary REFUSES (crypto.LibraryAbsent), citing the absent library — never a modelled
        fall-back (no silent downgrade, RW-DOWNGRADE)."""
        return crypto.sign_with_seed(self._seed(custody), message)

    def compare_public(self, custody, candidate_public):
        """Does `candidate_public` match the real PUBLIC half of the seed sealed under `custody`? A bool
        ONLY — the public half is derived from the sealed seed INSIDE this call and compared; nothing
        leaves but the verdict (the vault's `compare` shape, over the signing key's public half). A
        False is an honest no-match — the check that can fail. With the library ABSENT the derivation
        REFUSES (crypto.LibraryAbsent): a real public half cannot be produced without it, and no
        modelled value is substituted."""
        return candidate_public == crypto.public_from_seed(self._seed(custody))

    def _seed(self, custody):
        """The ONE internal consumption of a sealed seed — a PRIVATE custody lookup, NOT a public read
        path. `sign` and `compare_public` are its only callers and each returns a signature / a bool,
        never the seed. A custody handle with nothing sealed under it is an error, never a silent
        empty signature."""
        if custody not in self._seeds:
            raise KeyError("no signing key sealed under custody %r" % (custody,))
        return self._seeds[custody]
