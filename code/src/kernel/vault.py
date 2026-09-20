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
exactly once, is hashed, and NOTHING of it is kept but that hash — its bytes are stored
nowhere, on disk or off. The record ever holds only the hash and the usage decision
(MATCH / NO-MATCH). There is NO read operation for a secret value: not a refused one, an
ABSENT one (the bank has no counter, P3), and now nothing to read even if one existed.
Reading a secret back through the system is a Closure Hit — the op does not exist.

That is why the guarantee reads "unreadable by every actor including the chain-end":
there is no lawful path to a secret value because the path was never built and no value
is stored. The impossibility is ARCHITECTURAL, not cryptographic.

THE WRONG REFERENCE THIS MODULE REFUSES: the password-manager / encryption-at-rest
template. There is no decrypt-with-a-master-key path — that would be exactly the
apex-actor-above-the-law shape the constitution forbids (CONST-SECRETS). The value is
not encrypted-so-only-the-owner-can-read; it is unreadable because it is not stored and
NO read op exists.

HONEST CAP (design/31 §7): the on-disk-bytes fact is DISCHARGED — the value's bytes are
no longer written to disk, so raw disk access reads no sealed value off the vault (there
is none; only the hash ever survives). ONE separate question remains, named not closed
(design/31 J8): the stored hash is an unsalted sha256, so a low-entropy secret's hash is
guessable offline; salting/strengthening the hash home is that home's later decision, not
improvised here.

The surface is exactly two operations: `seal` (value in -> hash out; nothing stored) and
`compare` (candidate + a sealed hash -> is it a match?; the comparison is by hash, and
NEVER returns or exposes a value). There is deliberately no `get`, no `read`, no
`reveal`, no `open`, no `has` — the absence is the guarantee.
`secret_hash` is the one hash home the verify-never-reveal family shares (design/31 J8
re-home: account verification was the vault SEED — one mechanism, no parallel hashing).
"""

import hashlib
from pathlib import Path

from bridge.host_seam import host   # C7 P2 (:3930/:3952) — the vault's one disk act, creating its home
                                    # dir, routed through the host seam like every other core file


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
    """A hash-only store for secret VALUES — the surface is exactly `seal` and `compare`, with
    NO `get`/`read`/`reveal`. `seal` computes a value's hash and stores NOTHING; `compare`
    answers a hash-equality question and reads no stored value (there is none). A secret value
    crosses the boundary once, is hashed, and only the hash survives — nothing of it is on disk
    but its hash. There is no stored value to read back, and that ABSENCE is the closure."""

    def __init__(self, dir_path):
        self.dir = Path(dir_path)
        host().mkdir_p(self.dir)   # the vault's home dir — routed (portable host primitive)

    def seal(self, value):
        """Value in -> its hash out, and NOTHING is stored: no file, no directory, no byte
        write. The value is hashed and the "sha256:<hex>" hash is returned — the ONLY thing
        that leaves this call and the only thing the record ever records (content_params-style:
        the value never lands in a payload). The value's bytes have no home on disk because no
        path ever reads them back and the surface has no read op; keeping them would be storing
        what cannot be derived and cannot be used. Nothing of a secret is on disk but its hash."""
        return secret_hash(value)

    def compare(self, candidate, sealed_hash):
        """Does `candidate` match the secret sealed under `sealed_hash`? Answered BY HASH:
        hash the candidate and test equality against the sealed hash. Returns a bool ONLY —
        never the value, never the candidate. This is the whole of "verify": a MATCH /
        NO-MATCH question that reveals nothing. It reads no stored bytes (there are none); the
        sealed hash is supplied by the caller (resolved from the record's latest SEAL for the
        name)."""
        return sealed_hash is not None and secret_hash(candidate) == sealed_hash
