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
"""The conformance harness's REPLAY leg, for the M2 mount (EP-25 W8).

design/10 §3 check 3: re-deriving the subsystem's caches from (LAW, DECISIONS, INPUTS)
reproduces the post-call state identically. EP-24 built the check and said plainly what it
did not yet have: "the fixture's replay folds the tree each record carried rather than
re-deriving a filesystem. The first real replay adapter lands at EP-25." This is it.

It is REAL in the sense that matters: it opens the append-only record file, folds it with
`bridge.custody.fold` — the same one fold the mount serves from — and emits the state in
the probe's own shape, computed from records and content-addressed blobs and NOTHING ELSE.
It never reads the mounted tree. That is the whole point: a passthrough-with-a-log would
pass checks 1 and 2 and die here, because its truth was never in the record.

The harness declares this as a target's `replay` command (data in the target descriptor);
it is not harness code, and the harness imports nothing from here.

    python3 -m bridge.replay_snapshot <record.jsonl> <blobdir> [row_id]
"""

import hashlib
import json
import os
import stat as statmod
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from bridge import custody  # noqa: E402
from kernel import erasure  # noqa: E402  — the departure view: a handed-over hash replays as DEPARTURE


#: The probe's own type vocabulary (`probe._ftype`), matched exactly. The replay leg has to
#: speak the shape the ABI leg speaks or check 3 compares two spellings of agreement and
#: calls them a divergence.
_TYPE = {custody.KIND_DIR: "dir", custody.KIND_LINK: "lnk", custody.KIND_FILE: "reg",
         custody.KIND_FIFO: "fifo"}


def _ftype(kind):
    return _TYPE.get(kind, "reg")


def row_root(state, row_id):
    """WHICH SUBTREE THIS ROW RAN IN, derived from the record rather than told.

    The harness's local transport gives each row a fresh `run-<hex>` directory under the
    target's scratch and the probe works in `<run>/tree/<row_id>`; neither path is passed to
    the replay leg. It does not have to be: the mount RECORDED those directories being
    created, so the newest path ending in `/tree/<row_id>` is the row that just ran. Derived
    from the record, like everything else here.

    It returns None rather than falling back to the whole namespace when it finds nothing.
    A replay leg that quietly snapshots the wrong subtree reports agreement it never tested,
    and the empty answer that produces is shaped exactly like a target whose record is empty
    — which is a confusion this EP has already paid for once."""
    want = "/tree/" + (row_id or "").replace("/", "_")
    matches = [p for p in state.names if p.endswith(want)]
    # the namespace dict preserves insertion order, which is record order: the last one wins
    return matches[-1] if matches else None


def snapshot(record_path, blob_dir, row_id=None, root=None):
    """The probe's `state` shape — {relpath: {type, perm, nlink, size, sha256|target}} —
    computed from the record and the blobs alone."""
    # The harness runs a target's `replay` command through `subprocess`, which does NOT expand
    # `~`. The descriptor's own record/class-map paths are expanded by the harness; a command's
    # arguments are handed over verbatim, correctly — it is not the harness's business what a
    # target's command line means. So the expansion belongs here, and its absence was worth a
    # run: every replay answered "nothing", which reads exactly like a target whose record is
    # empty rather than like an adapter that could not find it.
    record_path = os.path.expanduser(record_path)
    blob_dir = os.path.expanduser(blob_dir)
    records = []
    if os.path.exists(record_path):
        with open(record_path, encoding="utf-8") as f:
            records = [json.loads(ln) for ln in f if ln.strip()]
    state = custody.fold(records)
    # THE DEPARTED SET (design/46), derived from the same records the tree folds from: any hash a
    # recorded handover ceremony transferred. A departed file replays as the DEPARTURE marker below,
    # so pre-handover replay reproduces the DEPARTED state (design/23 Option C). Empty until a
    # ceremony has run — inert.
    departed = erasure.departed_hashes(records)
    root = root or row_root(state, row_id)
    if root is None:
        # NOTHING IN THE RECORD MATCHES THIS ROW. Said out loud rather than answered with an
        # empty tree, because "the row created nothing" and "the replay leg looked in the
        # wrong place" produce the same empty dict and mean opposite things.
        raise SystemExit("replay: the record holds no /tree/%s for this row — either the probe "
                         "never reached the mount, or the mount is not the target's record"
                         % (row_id or "?"))
    root = custody._norm(root)
    prefix = "/" if root == "/" else root + "/"

    from kernel.blobs import BlobStore
    blobs = BlobStore(blob_dir)

    out = {}
    for path in sorted(state.names):
        if path == root or not path.startswith(prefix):
            continue
        node = state.inodes.get(state.names[path])
        if node is None:
            continue
        rel = path[len(prefix):]
        entry = {
            "type": _ftype(node.kind),
            "perm": oct(statmod.S_IMODE(state.mode(node))),
            "nlink": state.nlink(node.ino),
        }
        if node.kind == custody.KIND_LINK:
            entry["target"] = node.target
        elif node.kind == custody.KIND_FIFO:
            # A FIFO's bytes are the KERNEL's pipe, which never reaches a filesystem, so the
            # record holds no content for one and the replayed size is 0 — which is exactly
            # what an lstat of a fifo reports, on this mount and on a stock one alike.
            entry["size"] = 0
        elif node.kind == custody.KIND_FILE:  # dirs carry no size (§11.3: fs bookkeeping)
            data = b""
            if node.content_hash and node.content_hash in departed:
                # THE DEPARTURE (design/46): these bytes had their custody handed over by a recorded
                # ceremony. The file is still here — its content is the departure marker, not the
                # (gone) local bytes and not a silent empty. A departed file reports the marker's own
                # size and digest, a stable fingerprint.
                data = erasure.DEPARTURE
            elif node.content_hash and blobs.has(node.content_hash):
                data = blobs.get(node.content_hash)
            entry["size"] = len(data)
            entry["sha256"] = hashlib.sha256(data).hexdigest()[:16]
        out[rel] = entry
    return out


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if len(argv) < 2:
        print(__doc__)
        return 2
    record, blobdir = argv[0], argv[1]
    row_id = argv[2] if len(argv) > 2 else None
    print(json.dumps(snapshot(record, blobdir, row_id), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
