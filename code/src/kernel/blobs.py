# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — content-addressed blob store (sha256).

File and message content is DECISION-class and full-fidelity (design 03 §4.3
[AUDIT-FIX 4]): the record holds the hash, the bytes live here, keyed by their own
sha256. Identical bytes are stored once. Write-once; never mutated. This is the store
the files/comms cores reference by hash. (Clears the foundation review's P2.)

THE DURABILITY LAW OF THIS STORE, STATED AS AN ORDERING:

    CONTENT DURABLE BEFORE THE RECORD THAT NAMES IT.

That ordering is the law and the whole of it. Any implementation satisfying it is
lawful, and the one below — temp file, `fsync` of the file, atomic `os.replace` onto
the content path, then `fsync` of the PARENT DIRECTORY so the NAME is durable and not
only the bytes — is AN implementation of the law rather than the law itself. Stating it
as a mechanism is what would make the next subsystem inherit this implementation's
accidents as its requirements.

WHY THE ORDERING IS THE RECORD PLANE'S AND NOT ANY CONSUMER'S. The record's own append
fsyncs; before EP-30-C0 the blob did not. A record naming a hash whose bytes did not
survive the same crash the record survived is a record claiming an effect that did not
occur — the one forbidden lie. The invariant therefore couples the record plane to the
blob plane, and the record plane is the engine's. EP-25 solved it in a durable subclass
inside `src/bridge/mount.py` and said so in that subclass's own docstring: solving it
per-bridge was the lawful move for one EP and the wrong home for the estate. Board
`:1492` moved it here; the bridge subclass is retired at EP-30-C0, because a subclass
that adds nothing is dead code.

(The retired subclass is deliberately NOT named here. Its name is the subject of this
plan's S5 stop condition, whose grep spans `src/` — a prose mention in this file would
hand a later hand a false third hit and a stop that means nothing. The board carries the
name; this docstring carries the reason.)

HONEST CAP, STATED RATHER THAN LEFT TO BE DISCOVERED: the barrier makes the blob's own
name durable inside its fanout directory. It does NOT fsync `self.dir` when a fanout
directory is itself newly created, so a crash in that narrow window can lose the fanout
directory's own name. The ordering law above is unchanged by this; closing it is an
implementation change and it is RAISED, not silently taken, because widening the barrier
would move the call sequence the acceptance set pins.
"""

import hashlib
import os
from collections.abc import Mapping
from pathlib import Path

#: THE GUARANTEE, AS A VALUE A CALLER CAN READ. A test asks the store what it promises
#: instead of asking what class it is: the defect being cured is that a composition
#: change moves every consumer silently, and an `isinstance` check moves with the change.
CONTENT_DURABLE_BEFORE_RECORD = "content-durable-before-the-record-that-names-it"


def _receipt_covers(receipt, hashes):
    """The STRUCTURAL minimum a receipt must satisfy before `hand_off` removes a byte: it is a
    mapping, and it NAMES the content being removed (its `object` is one of the hashes being handed
    off). This is the lower layer of the capability-absence — decoupled from the handover
    vocabulary on purpose (this store knows nothing of receipts' law), so it checks presence and
    coverage only. The CRYPTOGRAPHIC verification (the receiver's signature under a bound key) is
    the ceremony's, in kernel.erasure, and runs BEFORE this tail is reached. A bare call (no
    receipt) or a receipt naming other content fails here — no byte leaves without a receipt naming
    it."""
    if not isinstance(receipt, Mapping):
        return False
    # R6 (EP-MAINT-OUTSIDE-4): the receipt must cover EVERY hash being removed, not merely one of a
    # list. A receipt names ONE object, so a call removing several distinct hashes under a single
    # receipt is refused (only the one it names is covered). The governed handover passes a singleton;
    # this lower API now enforces the same, so no byte leaves under a receipt that does not name it.
    return bool(hashes) and set(hashes).issubset({receipt.get("object")})


class BlobStore:
    #: What this store guarantees about `put`. Read by consumers and by the composition
    #: rows; never inferred from the class name.
    durability_guarantee = CONTENT_DURABLE_BEFORE_RECORD

    def __init__(self, dir_path):
        self.dir = Path(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)
        # R3 (EP-MAINT-OUTSIDE-4): the DURABILITY MARK. The paths whose directory barrier THIS process
        # has completed. A `put` on an existing path re-runs the barrier UNLESS it is marked, so a
        # retry after a directory-sync failure (the rename landed, the parent fsync did not) re-runs
        # the barrier the first attempt missed. The mark is in-memory: a fresh process holds none, so
        # a restart conservatively re-runs the barrier on the first put per path — never skips it.
        self._barriered = set()

    def _barrier(self, p):
        """Make the NAME durable: fsync the parent directory (idempotent). Marks the path so a later
        dedup put does not re-fsync a name this process already made durable (R3)."""
        dfd = os.open(str(p.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        self._barriered.add(str(p))

    def put(self, data):
        """Store bytes; return the content hash "sha256:<hex>". Identical bytes dedup.

        Returns only once the content is durable under its own name, per the ordering
        law in this module's docstring.

        R3 (EP-MAINT-OUTSIDE-4): the dedup path is not a bare `p.exists()` pass. It VERIFIES the
        stored bytes against the hash (a name whose bytes do not hash to it is missing content and is
        REFUSED, never served) and re-runs the directory barrier unless the durability mark says this
        process already ran it — so a retry after a failed parent-fsync completes the durability the
        first attempt left half-done.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        h = "sha256:" + hashlib.sha256(data).hexdigest()
        p = self._path(h)
        if p.exists():
            # DEDUP — but verify first (never serve a name whose bytes were lost or corrupted).
            stored = p.read_bytes()
            if "sha256:" + hashlib.sha256(stored).hexdigest() != h:
                raise ValueError(
                    "blob %s exists but its bytes do not hash to it — the stored content is missing "
                    "or corrupt; refusing to return the hash for content the store cannot serve" % h)
            if str(p) not in self._barriered:
                self._barrier(p)           # IDEMPOTENT durability: re-run the barrier a retry may owe
            return h
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".part")
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())           # the BYTES are durable
        os.replace(str(tmp), str(p))       # write-once, and atomically visible
        self._barrier(p)                   # the NAME is durable too, not only the bytes
        return h

    def get(self, h):
        return self._path(h).read_bytes()

    def has(self, h):
        # An existence CHECK answers False for a malformed address rather than raising (R4 keeps
        # containment — a malformed name never resolves to a path, so it is certainly not stored, and
        # answering False reads nothing outside the directory). `put`/`get`/`_remove_bytes` still
        # refuse a malformed address through `_path`; only this boolean read is lenient, so a caller
        # probing an absent-or-sentinel hash ("sha256:absent") gets "not present", not a crash.
        try:
            return self._path(h).exists()
        except ValueError:
            return False

    def hand_off(self, hashes, receipt):
        """THE REMOVAL TAIL of a completed, verified custody transfer (design/46 member 3) — the
        DEMOTED successor to the old standalone `destroy`. It removes the LOCAL content bytes named
        by `hashes`, line-by-line, VERIFYING each removal, but ONLY as the tail of a handover that
        has already produced the receiving hand's signed received-custody receipt.

        IT IS NOT A DELETE FUNCTION (design/46 §1, capability-absence). There is no `destroy` on
        this store any more: the only path that removes bytes is this one, and it REFUSES a call
        with no receipt, or a receipt that does not name the hash being removed. No local byte
        leaves this store without a receipt proving another hand now holds the content — the
        removal is the tail of a proven transfer, never an act of its own.

        THE HONEST LAYERING, STATED RATHER THAN LEFT TO BE DISCOVERED: this store holds no keys, so
        the receipt's CRYPTOGRAPHIC verification (the receiver's signature under a bound key) is the
        ceremony's, in kernel.erasure — done BEFORE this tail is reached. What this method enforces
        is the STRUCTURAL minimum a lower layer can: the receipt is present and names each hash. The
        two together are the capability-absence; neither alone is the whole of it, and the ceremony
        is the load-bearing gate.

        Each removal is VERIFIED (`has()` False after), so the tail reports honestly that the bytes
        are gone. The unlink + parent-fsync mechanism is symmetric to `put`'s ordering law, so the
        NAME is durably GONE and not merely hidden — a real byte-removal, never a crypto-shred (the
        bytes stay, key-readable) and never a soft-delete (a visibility flag over surviving bytes).
        Idempotent per hash (already-gone completes): the crash-window recovery, the ceremony's
        removal FIRST and its departure record LAST. Returns the list of hashes handed off."""
        if not _receipt_covers(receipt, hashes):
            raise ValueError(
                "hand_off is the removal TAIL of a verified custody transfer — it refuses without a "
                "receipt naming the hashes being removed: no receipt, no removal (design/46 §1, "
                "capability-absence — there is no standalone delete function)")
        for h in hashes:
            self._remove_bytes(h)               # the demoted unlink+fsync mechanism
            if self.has(h):                     # VERIFY each removal, line-by-line
                raise ValueError("hand_off did not remove the local bytes for %s" % h)
        return list(hashes)

    def _remove_bytes(self, h):
        """The unlink + parent-fsync mechanism, DEMOTED from the old standalone `destroy` to a
        private tail step: it is reachable only through `hand_off`, never as a delete of its own.

        GUARDED ON ITS OWN KEYSPACE. It refuses anything but a content hash ('sha256:<hex>'): the
        blob store's addresses are content hashes and nothing else, so the removal tail can never be
        handed a record — records are not content-addressed, and the cannot-orphan guarantee
        (authority is derived from records) begins here, at the address the bytes are named by.

        IDEMPOTENT. A hash whose bytes are already gone completes without error and returns False,
        so a re-run over already-gone bytes finishes the transfer rather than failing. Returns True
        if bytes were present and are now gone, False if they were already absent. The removal is
        made DURABLE — the parent directory is fsync'd, symmetric to `put`'s ordering law, so the
        NAME is durably GONE and not merely hidden. This method touches NO record."""
        if not (isinstance(h, str) and h.startswith("sha256:") and ":" in h):
            raise ValueError(
                "the removal tail operates on a content hash ('sha256:<hex>') only — the blob "
                "store's keyspace is content addresses, so it can never reach a record (cannot orphan)")
        p = self._path(h)
        if not p.exists():
            return False                        # already gone: idempotent, the re-run completes the transfer
        os.remove(str(p))                        # THE BYTES LEAVE THE STORE
        dfd = os.open(str(p.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)                        # the removal of the NAME is durable, not only the bytes
        finally:
            os.close(dfd)
        return True

    def _path(self, h):
        # R4 (EP-MAINT-OUTSIDE-4): CONTAINMENT AT THE PATH. A blob address is a STRICT 64-hex sha256
        # ("sha256:<64 lowercase hex>") and nothing else. Without this check a malformed name (fewer
        # bytes, a "..", a slash) resolves to a path OUTSIDE the blob directory; the strict form
        # refuses it here, at the one place a name becomes a path, so no read or write can escape the
        # store. The estate's addresses are lowercase `hexdigest()` output, so the form is exact.
        if not (isinstance(h, str) and h.startswith("sha256:")):
            raise ValueError("a blob address is 'sha256:<64 hex>'; %r is not one" % (h,))
        digest = h.split(":", 1)[1]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(
                "a blob address is a 64-character lowercase-hex sha256; %r is malformed and would "
                "resolve outside the blob directory — refused (containment at the path)" % (h,))
        return self.dir / digest[:2] / digest[2:]  # fanout by first byte
