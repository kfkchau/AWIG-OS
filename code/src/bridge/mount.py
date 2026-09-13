# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""The mount's entry point (EP-25 W7) — the stale campaign-1 runner, rebuilt.

`src/bridge/run_fuse_files.py` was the D9 flat-namespace stepping stone: it mounted a
flat top-level namespace to prove the shape, and it has sat in the campaign-1 findings
file ever since waiting for the round that takes up the bridge. This is that round
(design/36 §7 item 5), and the runner is REBUILT rather than retired, because the thing
it did is exactly what this EP needs — only over full tree custody rather than a flat one.
The old file now delegates here, so there is one entry point and no second way to raise a
mount that could drift from this one.

    python3 -m bridge.mount <record.jsonl> <blobdir> <mountpoint>

Foreground and single-threaded: the store is single-writer, and this campaign keeps ONE
store writer (design/36 §3 — adapters and FUSE threads are submitters through the one
gate, never additional writers; the S5 sequencer stays deferred and is not smuggled in).
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                 # AWIG OS/src
sys.path.insert(0, os.path.expanduser("~/gov-lab"))        # the fusepy adapter (libfuse2)

from kernel.blobs import BlobStore                          # noqa: E402


# EP-25 W3 added a DURABLE subclass of `BlobStore` here, and its own docstring said the
# placement was a fence artifact: "solving it per-bridge is the lawful move for one EP and
# the wrong home for the estate." EP-30-C0 executed that expiry on board `:1492`'s ruling —
# a record-plane invariant the kernel's own composition does not satisfy is not an
# invariant, it is a property one consumer happens to add. THE BARRIER NOW LIVES IN
# `src/kernel/blobs.py`, stated there as an ORDERING (content durable before the record
# that names it) rather than as a mechanism, and the subclass is RETIRED: once the engine
# carries the barrier the subclass adds nothing, and a class that adds nothing is dead code.
# This bridge composes the engine's store directly, like every other composition site.


def build_brain(record_path, blob_dir):
    """Compose the governed kernel ALONE — the record machine, with no transport over it.

    THE BRAIN IS WHAT STAYS IN USER SPACE (K5), and after EP-28 it has two consumers
    rather than one: the FUSE mount of stance 3, and the in-kernel seam's daemon of
    stance 4. Factored out here so both compose the SAME machine — the EP-24B
    one-implementation rule pointed at composition, because a second assembly of the
    store, gate, views, vault, protection and push is a second machine that could
    diverge from the tested one in a way no test would notice.

    It imports NOTHING from `records_fs`, and that absence is load-bearing: the
    in-kernel daemon runs in a guest where fusepy is not installed, so a stray FUSE
    import here would fail the daemon at start-up. The transport being genuinely
    retired is proven by the module that no longer imports it.
    """
    from kernel.boot import build_kernel
    from kernel.opdefs import replay_op_definitions
    from kernel.protection import Protection, register_protection_ops
    from kernel.push import StandingPush
    from kernel.vault import VaultStore

    blobs = BlobStore(blob_dir)
    store, gate, views = build_kernel(record_path, blobs=blobs)
    gate.vault = VaultStore(os.path.join(os.path.dirname(blob_dir.rstrip("/")), "vault"))
    replay_op_definitions(gate, store, views)
    views.push = StandingPush(store, views)
    protection = Protection(store, gate, views)
    register_protection_ops(gate, store, protection)
    views.protection = protection
    return store, gate, views, blobs


def build_mount(record_path, blob_dir, *, shadow_every=0):
    """Compose the governed kernel and the FUSE custody server over it. Returns
    (fs, store, gate, views, blobs) — the tuple the tests and the harness's replay adapter
    both drive, so nothing exercises a differently-composed mount than the one that runs."""
    from bridge.records_fs import RecordsFS

    store, gate, views, blobs = build_brain(record_path, blob_dir)
    fs = RecordsFS(store, gate, views, blobs, shadow_every=shadow_every)
    return fs, store, gate, views, blobs


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if len(argv) < 3:
        print(__doc__)
        return 2
    record, blobdir, mnt = argv[0], argv[1], argv[2]
    os.makedirs(mnt, exist_ok=True)
    fs, *_ = build_mount(record, blobdir)
    from fuse import FUSE
    # `default_permissions` hands POSIX permission checking to the kernel, which evaluates it
    # against the mode/uid/gid this mount reports — and those come from the derived inode
    # view, which is a fold over recorded decisions. So the check is made by the kernel and
    # ANSWERED by the record. The alternative, evaluating modes inside the server, would put
    # the permission answer in the mount instead of in the fold.
    # `use_ino` makes userland see the inode identities the RECORD minted, so two names for
    # one inode are one inode because the record says so — not because the kernel happened to
    # collapse them. Zero attribute/entry timeouts keep the kernel from serving a cached
    # answer the record has since moved past, which would be a view answering out of date.
    # `direct_io` (B2) keeps the kernel from caching a written byte and serving it back to a
    # reader on its OWN authority: a write whose covering decision the gate refuses leaves the
    # burst un-committed (POSIX un-fsynced semantics), and the mount must not let the page
    # cache serve that un-durable byte to a fresh reader — the adapter's read path decides
    # what a reader sees, so it must be the one thing the kernel asks. (The mmap consequence
    # of direct_io is measured by I3's native-control row, not assumed here.)
    FUSE(fs, mnt, foreground=True, nothreads=True, default_permissions=True, use_ino=True,
         direct_io=True, attr_timeout=0, entry_timeout=0, negative_timeout=0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
