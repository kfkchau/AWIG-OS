# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture (Merkle tree, tree-state, subtree localization, content hash)
# per OS textbooks and the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability of
# any kind. Full declaration: SCOPE-STATEMENT.md.
"""The Merkle tree over a checkpoint's tree-state (EP-45; ARC R, the genesis-guardian family;
design/37 §5, the fanqie insight — relations adjudicate, so damage LOCALIZES).

A checkpoint (EP-44) pins a tree-state as `snapshot()`'s FLAT `{relpath: node}` dict, and its
`verify` answers by WHOLE-TREE equality: one damaged node reddens the whole and names nothing.
This module folds that flat tree-state into a hierarchy of hashes so a mismatch LOCALIZES to the
diverging subtree instead:

    leaf (a file node)   = canonical_hash(node)                      -- the file's own bytes+meta
    directory node       = canonical_hash over its children's        -- the relation OVER the children,
                           sorted (childname, childhash) pairs          AND (scheme 2) the dir's own metadata
    root                 = the top directory node's hash

A DIRECTORY'S OWN METADATA IS SEALED (B11; EP-MAINT-OUTSIDE-2). A directory node's hash folds its
own snapshot entry (its mode/nlink) BESIDE the children pairs, so a directory whose mode changes and
whose children do not still moves its own hash — the merkle tree seals the directory, not only what
it contains. This is carried behind a MERKLE-SCHEME VERSION so it is BACKWARD-SAFE: a root minted
under the old spec (children-only) still verifies under ITS OWN scheme, keyed by the scheme version a
checkpoint records in its provenance (an absent version reads as scheme 1). Scheme 1 is children-only
(the pre-B11 spec, kept whole for every root already on disk); scheme 2 seals the dir's own metadata.
New checkpoints fold under `CURRENT_SCHEME`; a verifier folds under the checkpoint's own recorded
scheme. LOCALIZATION IS UNCHANGED: a dir's own metadata rides its own hash and its ancestors' (a
child of the parent's pairs), never a sibling's.

THE ONE FOLD, REUSED — never a second fold of the record (the air rider, :2963; the forbidden
second-implementation class, :3017/:3018). The record is folded ONCE, by `replay_snapshot.snapshot`,
into the flat tree-state. This module folds THAT OUTPUT (a plain dict) into a Merkle hierarchy; it
opens no record, reads no blob, and re-implements no reader. `merkle_root` and `merkle_tree` and
`localize` all annotate the SAME structure once — the checkpoint pins the root at create time and the
verifier recomputes it at verify time through this same function, so the two never diverge by
carrying two folds.

THE ONE HASH FORM. Leaves and nodes reuse the estate's single governed serializer
(`kernel.canonical.canonical_hash` → "sha256:<hex>"); this module implements no second serializer
(it never calls hashlib and never json-dumps — it is a CONSUMER of the floor, the
T-CANONICAL-ONE-SERIALIZER discipline).

LAYERING. This is a BRIDGE module. It consumes the kernel read-only (`canonical_hash`) and never the
reverse: the kernel must not import it (a kernel→bridge dependency would invert the estate's layering,
stop (g)).
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                       # AWIG OS/src

from kernel.canonical import canonical_hash                      # noqa: E402  — the estate's ONE hash form (REUSED, never re-implemented)


#: A tree-state node's `type` values that are NOT directories (the leaves the Merkle hashes whole).
#: A "dir"-typed node is a directory whose Merkle hash is the relation over its children, per A1.
_DIR = "dir"

#: THE MERKLE-SCHEME VERSIONS (B11; EP-MAINT-OUTSIDE-2). A checkpoint records which one its root was
#: folded under, so an OLD root verifies under ITS scheme (backward-safe). An ABSENT scheme reads as
#: scheme 1 — the children-only pre-B11 spec, so every root already on disk verifies UNCHANGED.
#: scheme 1: a directory's hash is `canonical_hash(children-pairs)` — the dir's own metadata is OUT.
#: scheme 2: a directory's hash folds the dir's OWN snapshot entry BESIDE the children-pairs.
SCHEME_CHILDREN_ONLY = 1
SCHEME_DIR_METADATA = 2
#: The scheme a NEW fold writes. A verifier reads a checkpoint's recorded scheme instead of this.
CURRENT_SCHEME = SCHEME_DIR_METADATA


def _structure(tree):
    """Build the hierarchy from `snapshot()`'s FLAT `{relpath: node}` dict — the SAME output the one
    reader produced, never a re-read of the record. Returns a synthetic root directory:

        {"kind": "dir", "children": {name: subnode}, "node": None}

    where a subnode is `{"kind": "file", "node": <entry>}` for a leaf, or a directory shaped like the
    root (`"node"` is the directory's own snapshot entry when the record carried one, else None). The
    relpaths encode the hierarchy; intermediate segments are directories whether or not the record
    emitted an explicit entry for them (a robustness the flat shape requires)."""
    root = {"kind": _DIR, "children": {}, "node": None}
    for relpath in sorted(tree):
        entry = tree[relpath]
        parts = [p for p in relpath.split("/") if p != ""]
        if not parts:
            continue
        cur = root
        for part in parts[:-1]:
            nxt = cur["children"].get(part)
            if nxt is None or nxt["kind"] != _DIR:
                nxt = {"kind": _DIR, "children": {}, "node": None}
                cur["children"][part] = nxt
            cur = nxt
        leaf = parts[-1]
        if entry.get("type") == _DIR:
            existing = cur["children"].get(leaf)
            if existing is not None and existing["kind"] == _DIR:
                existing["node"] = entry                         # a directory that also had children
            else:
                cur["children"][leaf] = {"kind": _DIR, "children": {}, "node": entry}
        else:
            cur["children"][leaf] = {"kind": "file", "node": entry}
    return root


def _annotate(subnode, scheme):
    """Fold ONE structure node into `{kind, hash[, children]}`, under a merkle SCHEME. A file leaf's
    hash is `canonical_hash` of its node; a directory's hash is `canonical_hash` over its children's
    SORTED (name, child-hash) pairs — the relation over the children, so a child that moves moves its
    parent's hash and no other's (localization). This is the single fold every entry point shares.

    B11 (EP-MAINT-OUTSIDE-2): under SCHEME_DIR_METADATA the directory's OWN snapshot entry
    (`subnode["node"]`, its mode/nlink — None for an intermediate dir the record named no entry for)
    is folded BESIDE the children pairs, so a dir whose own mode changes moves its own hash even when
    no child moved. Under SCHEME_CHILDREN_ONLY the dir's own metadata is OUT (the pre-B11 spec), so a
    root minted then verifies UNCHANGED. Localization is preserved either way — the dir's metadata
    rides only its own hash (and its ancestors', through the pairs), never a sibling's."""
    if subnode["kind"] == "file":
        return {"kind": "file", "hash": canonical_hash(subnode["node"])}
    children = {name: _annotate(child, scheme) for name, child in subnode["children"].items()}
    pairs = [[name, children[name]["hash"]] for name in sorted(children)]
    if scheme == SCHEME_CHILDREN_ONLY:
        h = canonical_hash(pairs)                                    # the pre-B11 spec: children only
    else:
        h = canonical_hash([subnode.get("node"), pairs])            # B11: seal the dir's own metadata
    return {"kind": _DIR, "hash": h, "children": children}


def merkle_tree(tree, scheme=CURRENT_SCHEME):
    """The full Merkle node tree over a flat tree-state: `{kind, hash, children}` at every level. The
    subtree hashes are inspectable, so an unchanged sibling subtree's hash is verifiably equal across
    two states (A2 — reported clean). One fold of the snapshot output; no record read. `scheme`
    selects the directory-hash spec (B11): default `CURRENT_SCHEME`; a verifier passes the checkpoint's
    recorded scheme so an old root folds under its own."""
    return _annotate(_structure(tree), scheme)


def merkle_root(tree, scheme=CURRENT_SCHEME):
    """The Merkle root over a flat tree-state — the estate's one hash form ("sha256:<hex>"). Pinned in
    a cross-attested checkpoint's provenance at create time and recomputed at verify time through THIS
    same function (A1). The empty tree folds to a fixed, stable root. `scheme` (B11) selects the
    directory-hash spec; a verifier passes the checkpoint's recorded scheme so an old root verifies
    under its own (backward-safe)."""
    return merkle_tree(tree, scheme)["hash"]


def localize(pinned_tree, recomputed_tree, scheme=CURRENT_SCHEME):
    """Name the DIVERGING subtree path(s) between two tree-states — not a bare "tree mismatch" (A2,
    the whole reason the Merkle exists). Relations adjudicate: a subtree whose Merkle hash MATCHES is
    clean and is not descended (an unchanged sibling costs nothing and is reported clean); divergence
    descends to the leaf that changed, appeared, or vanished. Returns the sorted diverging leaf paths
    (and any node where a directory and a file trade places). Both trees are folded under the SAME
    `scheme` (B11), so a comparison is scheme-consistent.

    Pure over two dicts — it folds each once through `merkle_tree` and walks the two annotations. No
    record, no blob, no engine (the air rider)."""
    out = []
    _walk(merkle_tree(pinned_tree, scheme), merkle_tree(recomputed_tree, scheme), "", out)
    return sorted(out)


def _walk(a, b, prefix, out):
    """Descend two annotated nodes, collecting diverging leaf paths. A matching hash prunes the
    subtree (clean); a difference descends. `a`/`b` may be None where a path exists on one side only
    (added / removed)."""
    if a is not None and b is not None and a["hash"] == b["hash"]:
        return                                                   # clean subtree — the relation adjudicates it whole
    a_dir = a is not None and a["kind"] == _DIR
    b_dir = b is not None and b["kind"] == _DIR
    if a_dir or b_dir:
        a_children = a["children"] if a_dir else {}
        b_children = b["children"] if b_dir else {}
        before = len(out)
        for name in sorted(set(a_children) | set(b_children)):
            child_prefix = (prefix + "/" + name) if prefix else name
            ca, cb = a_children.get(name), b_children.get(name)
            if ca is not None and cb is not None and ca["hash"] == cb["hash"]:
                continue                                         # an unchanged sibling subtree — clean
            _walk(ca, cb, child_prefix, out)
        if a_dir != b_dir:                                       # a directory and a file trade places here
            out.append(prefix or "/")
        elif len(out) == before:
            # Both are directories, their hashes differ, yet NO child diverged — the DIRECTORY'S OWN
            # metadata changed (B11 scheme 2, EP-MAINT-OUTSIDE-2). Localize to this directory, not a
            # bare "something moved" that names nothing (RW1 — the reason localize exists). Under
            # scheme 1 the dir's metadata is out of its hash, so this branch is never reached there.
            out.append(prefix or "/")
    else:
        out.append(prefix or "/")                                # two differing leaves (or one absent): this path diverges


# ---- C6 P11 (N1): THE INCLUSION / AUDIT-PATH PRIMITIVE — ONE leaf under a root ------------------
# SPIKE-3 §1c:50 and §3b:127 named this exact gap: `localize` needs TWO FULL trees, and no function
# proves ONE leaf under a root with a sibling path. Without it MEMORY-SANE at HASHES-ONLY is a
# signature-of-a-hash only, and I10's level-blindness fails for MEMORY-SANE (SPIKE-3 §3c). This is a
# NEW FUNCTION on the EXISTING module, BESIDE merkle_tree/merkle_root/localize — the existing three
# are UNCHANGED and this adds no module (the ATTESTED_MEMBERS rider does not fire for a function). It
# folds the snapshot output through the SAME one fold (_structure/_annotate); it opens no record,
# reads no blob, and calls no second serializer (the T-CANONICAL-ONE-SERIALIZER discipline). The
# audit path folds to the SAME value merkle_root returns for the same tree and scheme, so a leaf is
# spot-verifiable against a presented root WITHOUT the whole tree crossing (least disclosure — a
# sibling crosses as its HASH, never its value; the directory's own metadata rides the path under
# scheme 2, as the B11 hashing requires, and that is a property of the existing scheme, not this
# primitive's leak).

def inclusion_proof(tree, relpath, scheme=CURRENT_SCHEME):
    """AN AUDIT PATH proving ONE leaf's inclusion under `merkle_root(tree, scheme)` (N1; SPIKE-3 §3b).

    Returns `{leaf, leaf_hash, path, scheme}` where `path` is the sibling information at each directory
    level from the leaf's PARENT up to the ROOT (leaf-first, so it folds leaf -> root); or None when
    `relpath` names no FILE leaf in the tree (THE CHECK CAN FAIL — a leaf not in the tree yields no
    proof; a directory path yields None because a directory is not one leaf — divergence of a whole
    subtree is `localize`'s job, not an inclusion proof's). Each level records the target child's
    `name`, the directory's OWN snapshot entry `node` (its mode/nlink — None for an intermediate dir;
    folded beside the pairs under scheme 2, B11), and the `siblings` as sorted `[name, child_hash]`
    pairs. One fold of the snapshot output via `_structure`/`_annotate`; no record read, no second
    serializer. The path length equals the leaf's DEPTH in the tree."""
    parts = [p for p in str(relpath).split("/") if p != ""]
    if not parts:
        return None
    struct = _structure(tree)
    annotated = _annotate(struct, scheme)
    path = []
    s_cur, a_cur = struct, annotated
    for part in parts:
        if a_cur.get("kind") != _DIR:
            return None                                          # descended into a file before the path ended
        a_child = a_cur["children"].get(part)
        if a_child is None:
            return None                                          # the path names no child here — not in the tree
        siblings = [[name, a_cur["children"][name]["hash"]]      # every OTHER child's (name, hash), the audit path
                    for name in a_cur["children"] if name != part]
        path.append({"name": part, "node": s_cur.get("node"), "siblings": siblings})
        s_cur = s_cur["children"].get(part)
        a_cur = a_child
    if a_cur.get("kind") != "file":
        return None                                              # relpath resolves to a directory — not one leaf
    path.reverse()                                               # leaf's parent first .. root last: folds leaf -> root
    return {"leaf": "/".join(parts), "leaf_hash": a_cur["hash"], "path": path, "scheme": scheme}


def verify_inclusion(proof, root, scheme=None):
    """VERIFY an audit path against a root (N1). True iff folding the proof's leaf hash up its recorded
    sibling path — reconstructing each directory's pairs and re-hashing through the estate's ONE hash
    form under the SAME scheme `_annotate` used — reproduces `root` (which equals `merkle_root(tree,
    scheme)` for the tree the proof came from). A tampered leaf hash, an altered sibling, a wrong root,
    a wrong `node`, or a scheme mismatch ALL return False — THE CHECK THAT CAN FAIL, the whole reason an
    inclusion proof exists. A None / malformed proof returns False (a leaf not in the tree has no proof
    to verify). `scheme` defaults to the proof's own recorded scheme; passing a DIFFERENT scheme folds
    under it (so a scheme mismatch fails, by construction)."""
    if not isinstance(proof, dict) or proof.get("path") is None or proof.get("leaf_hash") is None:
        return False
    sch = scheme if scheme is not None else proof.get("scheme", CURRENT_SCHEME)
    running = proof.get("leaf_hash")
    for level in proof["path"]:
        pairs = [list(s) for s in (level.get("siblings") or [])]
        pairs.append([level.get("name"), running])              # substitute the running hash for this level's child
        pairs.sort(key=lambda p: p[0])                          # the pairs are sorted by name, as _annotate builds them
        if sch == SCHEME_CHILDREN_ONLY:
            running = canonical_hash(pairs)                     # the pre-B11 spec: children only
        else:
            running = canonical_hash([level.get("node"), pairs])  # B11: the dir's own metadata beside the pairs
    return running == root
