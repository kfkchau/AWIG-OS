# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture (sealed segment, verify against a key, chain-verify, union,
# content address) per OS textbooks and the seL4/gVisor/Fuchsia literature. NON-GOAL: no
# offensive capability of any kind — this proves a constitution reconstructs from the children's
# held signed segments after the parent store is gone, by function, over benign local records.
# Full declaration: SCOPE-STATEMENT.md.
"""The CONSTITUTION-SURVIVES reconstruction (B6, I15; C6 P12; design/52 §7).

With the PARENT body's store gone, the UNION of the CHILDREN's held sealed segments — each
VERIFIED AGAINST THE PARENT KEY and chain-verified — reproduces every rule any child was ever
bound by. What is lost is only positions no child ever held, and that loss is REPORTED BY
NUMBER (never filled or smoothed). B6's three words, in order: gather, verify against the
parent key, union.

A DERIVED VIEW, NEVER A RECORD (archi :3619 precision 1). This routine READS the children's
held segment references and the content-addressed segment store; it verifies and folds; it
APPENDS NOTHING to any record (its own record included). Its deliverable is a REPORT — a
return value — not a row. Founding a successor body FROM that report is a founding act (B1,
P7's law), NOT this routine: reconstruction stops at the computed view.

COMPOSING EXISTING PRIMITIVES ONLY (GREEN — no new op, no new law, no new check kind, no pack
edit, no version bump, no founding move):

  VERIFY AGAINST THE PARENT KEY   `keys.verify_countersign(mark, record, parent_key, public_key)`
      The seal binds the segment's recording fact (its chain position and its content address)
      under the parent's key; a forged mark, or a mark made under ANOTHER key, is a False — the
      RW-FORGE check that can fail (the very check this unit's A3 positive control reddens).
      ERA-AGNOSTIC (KEY-MATERIAL-REAL §3): a MODELLED mark (a dict, no algorithm tag) verifies
      under the modelled path with the vetted library ABSENT — the estate's current baseline; a
      REAL (tagged) mark verifies through `crypto.verify` only where the library is PRESENT, and
      with it absent that real verification REFUSES citing the absent library (N10 real-or-
      refused; RW-DOWNGRADE). This routine composes the one verifier and NEVER a substitute — it
      does not catch `LibraryAbsent`, so a real segment on a library-absent host refuses loudly
      rather than being mistaken here for a forgery.

  CONTENT-ADDRESS                 the bytes at the segment's address must hash to it
      `blobs.BlobStore` already refuses to serve a name whose bytes were lost or corrupted; this
      routine recomputes the content address as the SECOND forge check, so bytes that do not
      hash to their stated address (missing or tampered content) are NOT admitted to the union.

  CHAIN-VERIFY / THE ONE FOLD     `merkle.merkle_root` over the verified positions
      The reconstructed positions are folded ONCE, in chain order (sorted by position), into a
      single inspectable Merkle root — the reconstructed constitution's fingerprint. Because the
      fold is over sorted positions, child order never moves the root and two children holding
      the SAME segment fold to ONE leaf (dedup). The routine implements no second serializer and
      re-reads no record — it is a CONSUMER of the estate's one hash form and the one Merkle fold.

  THE DETERMINISTIC CHAIN-ORDER MERGE (archi :3619 precision 2)
      Each held segment carries its POSITION in the parent's chain; the merge orders by that
      position; a DUPLICATE segment held by two children (same position, same content address) is
      ONE segment; a GAP between held positions is REPORTED BY POSITION, never filled and never
      smoothed. A2's "only the unheld is lost" is asserted here as a NAMED GAP LIST, not silence.

LAYERING (stop g, RW5). A BRIDGE module: it consumes the kernel read-only (`keys`, `canonical`,
`blobs`) and the bridge Merkle fold; the kernel imports nothing here. It is the CROSS-BODY
sibling of `auto_recover`, which recovers ONE store from ITS OWN segments; P12 unions the
CHILDREN's held segments to reconstruct the PARENT's constitution — a NEW routine, not a change
to one-store recovery, and it writes nothing where `auto_recover` splices.
"""

import hashlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                       # AWIG OS/src

from kernel import keys                                          # noqa: E402  — verify against the parent key (the RW-FORGE check)
from bridge import merkle                                        # noqa: E402  — the one Merkle fold (chain-verify), REUSED


#: The report keys a caller reads off the DERIVED VIEW. `rules` is the reconstructed
#: constitution (position -> content bytes); `root` is the Merkle fold over the held positions;
#: `positions` is the chain order; `gaps` is the named unheld positions; `refused` names every
#: segment a check rejected. Nothing here is a record — the whole return value is a view.
REPORT_KEYS = ("rules", "root", "positions", "gaps", "refused")


def _content_address(data):
    """The blob store's own address form for `data` — 'sha256:<hex>' over the raw bytes (the same
    address `blobs.BlobStore.put` computes). Recomputed here as the SECOND forge check, so bytes
    that do not hash to their stated address are refused rather than served."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _fetch_and_check_address(blob_store, address):
    """Fetch the sealed bytes at `address` from the content-addressed segment store and confirm
    they hash BACK to `address` (the content-address forge check). Returns `(ok, data_or_None)`;
    a missing blob or a hash mismatch is `(False, None)` — the segment is NOT admitted."""
    try:
        data = blob_store.get(address)
    except Exception:
        return False, None                                       # the content did not survive in this store
    return (_content_address(data) == address), data


def _relpath(position):
    """A position rendered as a fixed-width relpath so the Merkle fold's lexicographic sort IS the
    chain order (position 2 sorts before position 10). The fold seals the position (the relpath)
    beside the content address, so a segment moved to another position moves the root."""
    return "%012d" % int(position)


def _gaps(positions):
    """The positions BETWEEN the held ones that NO child held — the NAMED GAP LIST (archi :3619
    precision 2). Only-the-unheld-is-lost is stated as numbers, never filled or smoothed. Empty
    when the held positions are contiguous. Bounded by the held set (the parent's own store is
    gone, so a gap is 'between held segments', per the ruling's words), not by an outside manifest."""
    if not positions:
        return []
    held = set(positions)
    return [p for p in range(positions[0], positions[-1] + 1) if p not in held]


def reconstruct(parent_key, held_segments, blob_store, public_key=None):
    """Reconstruct the parent's constitution from the CHILDREN's held sealed segments, after the
    parent's own store is gone. Composes existing primitives only; appends NOTHING.

    parent_key     the parent body's `system_key_hash` (its public custody hash) — the ONE key
                   every held segment's seal must verify against.
    held_segments  an iterable of the children's held segment REFERENCES. Each is a mapping:
                       {"position": <int>,                  position in the parent's chain
                        "address":  "sha256:<hex>",         content address of the sealed bytes
                        "record":   {seq, record_time, object: <address>, ...},  the recording fact
                        "mark":     <countersign>}           the parent's seal over `record`
                   Several children MAY hold the same reference; duplicates (same position, same
                   address) collapse to one segment (dedup).
    blob_store     the content-addressed segment store the sealed bytes live in (`blobs.BlobStore`
                   or any store exposing `.get(address) -> bytes`). This is the SURVIVING replicated
                   content the children hold — NOT the parent's removed store.
    public_key     the parent's published public half, forwarded to `verify_countersign` for a REAL
                   (tagged) mark; ignored on the modelled path (the estate's baseline).

    Returns a DERIVED VIEW (a report dict over REPORT_KEYS), appends NOTHING to any record:
        {"rules":     {position: bytes, ...},   every position ANY child held AND that verified
         "root":      "sha256:<hex>",           the Merkle fold over the reconstructed positions
         "positions": [int, ...],               sorted held positions (the chain order)
         "gaps":      [int, ...],               positions BETWEEN held ones that NO child held
         "refused":   [{"position", "address", "reason"}, ...]}   segments a check rejected
    """
    admitted = {}                                                # position -> (address, bytes): the chain-order union
    refused = []
    seen = set()                                                 # (position, address): dedup a segment two children hold
    for seg in held_segments:
        position = seg.get("position")
        address = seg.get("address")
        record = seg.get("record")
        mark = seg.get("mark")
        key = (position, address)
        if key in seen:
            continue                                             # DEDUP — same segment held by another child, one segment
        seen.add(key)
        # (1) VERIFY AGAINST THE PARENT KEY — the seal binds this record under the parent's key.
        #     A forged mark, or one made under another key, is a False (RW-FORGE). Era-agnostic:
        #     a real mark on a library-absent host raises LibraryAbsent here and is NOT swallowed.
        if not keys.verify_countersign(mark, record, parent_key, public_key=public_key):
            refused.append({"position": position, "address": address,
                            "reason": "seal does not verify against the parent key (RW-FORGE)"})
            continue
        # The seal binds the RECORD; the record must NAME this content address and this position,
        # so the seal binds the CONTENT and the PLACE, not a bare recording fact a forger could
        # re-point. A record that does not bind them is not this segment's seal.
        if not (isinstance(record, dict)
                and record.get("object") == address
                and record.get("seq") == position):
            refused.append({"position": position, "address": address,
                            "reason": "the sealed record does not bind this address and position"})
            continue
        # (2) CONTENT-ADDRESS — the stored bytes must hash to their address (the second forge
        #     check). Missing or tampered content is refused, never served into the union.
        ok, data = _fetch_and_check_address(blob_store, address)
        if not ok:
            refused.append({"position": position, "address": address,
                            "reason": "bytes do not hash to their address (missing or corrupt content)"})
            continue
        admitted[position] = (address, data)
    # (3) THE ONE FOLD — merkle_root over the verified positions, in chain order. Deterministic:
    #     sorted positions, so child order does not move the root and a duplicate is one leaf.
    tree = {_relpath(pos): {"type": "file", "address": addr}
            for pos, (addr, _data) in admitted.items()}
    root = merkle.merkle_root(tree)
    positions = sorted(admitted)
    return {"rules": {pos: admitted[pos][1] for pos in positions},
            "root": root,
            "positions": positions,
            "gaps": _gaps(positions),
            "refused": refused}
