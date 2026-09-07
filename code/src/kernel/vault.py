# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — the secrets vault (design/31 J8; EP-19): verify, never reveal.

The impossibility here is CLOSURE, not encryption. A secret VALUE crosses the boundary
exactly once, is hashed, and its bytes are stored write-once in this store keyed by
their own hash — OUTSIDE the record. The record ever holds only the hash and the usage
decision (MATCH / NO-MATCH). There is NO read operation for a stored secret value: not a
refused one, an ABSENT one (the bank has no counter, P3). Reading a secret back through
the system is a Closure Hit — the op does not exist.

That is why the guarantee reads "unreadable by every actor including the chain-end":
there is no lawful path to a secret value because the path was never built. The
impossibility is ARCHITECTURAL, not cryptographic.

THE WRONG REFERENCE THIS MODULE REFUSES: the password-manager / encryption-at-rest
template. There is no decrypt-with-a-master-key path — that would be exactly the
apex-actor-above-the-law shape the constitution forbids (CONST-SECRETS). The value is
not encrypted-so-only-the-owner-can-read; it is unreadable because NO read op exists.

HONEST CAP (design/31 §7; the EP names it): this store closes the SYSTEM path, not the
disk path. An actor with raw disk access could read the sealed bytes off the vault
files; sealing those bytes cryptographically (signing/crypto so on-disk custody is also
closed) is CAMPAIGN 4's work, not improvised here.

The surface is exactly two operations: `seal` (value in -> hash out; value stored
write-once, keyed by hash) and `compare` (candidate + a sealed hash -> is it a match?;
the comparison is by hash, and NEVER returns or exposes a value). There is deliberately
no `get`, no `read`, no `reveal`, no `open`, no `has` — the absence is the guarantee.
`secret_hash` is the one hash home the verify-never-reveal family shares (design/31 J8
re-home: account verification was the vault SEED — one mechanism, no parallel hashing).
"""

import hashlib
from pathlib import Path


def secret_hash(value):
    """The one hash home (sha256) the verify-never-reveal family shares — the SAME scheme
    an account's verification evidence is pre-hashed under (EP-15; the vault seed). A value
    -> "sha256:<hex>". Deterministic, so `compare` is a pure hash-equality question and
    secret ROTATION is a supersession-by-hash (re-seal a name under a new value -> a new
    hash; the record's latest-per-name fold reads the newest)."""
    if isinstance(value, str):
        value = value.encode("utf-8")
    return "sha256:" + hashlib.sha256(value).hexdigest()


class VaultStore:
    """A write-once, hash-keyed store for secret VALUES — like the content-addressed blob
    store, MINUS every read path. `seal` writes; there is NO `get`/`read`/`reveal`.
    `compare` answers a hash-equality question and never reads a stored value back out. The
    sealed bytes exist only so the value crossed once into a write-once home
    (campaign-4-protectable); no code path reads them back — that ABSENCE is the closure."""

    def __init__(self, dir_path):
        self.dir = Path(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)

    def seal(self, value):
        """Value in -> its hash out. The value is hashed and its bytes stored write-once
        keyed by that hash (identical values coincide, like blobs). Returns the
        "sha256:<hex>" hash — the ONLY thing that leaves this call and the only thing the
        record ever records (content_params-style: the value never lands in a payload). The
        value never leaves the vault; there is no read path to get it back."""
        h = secret_hash(value)
        p = self._path(h)
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            data = value.encode("utf-8") if isinstance(value, str) else value
            p.write_bytes(data)  # write-once; never mutated, never read back
        return h

    def compare(self, candidate, sealed_hash):
        """Does `candidate` match the secret sealed under `sealed_hash`? Answered BY HASH:
        hash the candidate and test equality against the sealed hash. Returns a bool ONLY —
        never the value, never the candidate. This is the whole of "verify": a MATCH /
        NO-MATCH question that reveals nothing. It does not read the vault's stored bytes;
        the sealed hash is supplied by the caller (resolved from the record's latest SEAL
        for the name)."""
        return sealed_hash is not None and secret_hash(candidate) == sealed_hash

    def _path(self, h):
        digest = h.split(":", 1)[1]
        return self.dir / digest[:2] / digest[2:]  # fanout by first byte
