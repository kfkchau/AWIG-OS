# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture (checkpoint, recovery artifact, provenance triplet, waking-point)
# per OS textbooks and the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability of
# any kind. Full declaration: SCOPE-STATEMENT.md.
"""The prepared waking-point (EP-44; ARC R, the genesis-guardian family; design/47 §3, design/37 §5).

A CHECKPOINT is a persisted recovery ARTIFACT: the record's tree-state view (`snapshot()`) written
WITH a provenance triplet — the chain-head hash it captures, the founding pack sha it was taken
under, and the attestation head naming the engine that took it. The triplet is the wake checklist's
steps 1-3 (design/47 §3) as data:

    chain_head          RECORD       — the hash-chain end (integrity, step 2)
    founding_pack_sha   CONSTITUTION — the constitution it was taken under (step 3)
    attestation_head    BODY         — the attestation naming the engine that took it (step 1)

Two properties are load-bearing and each has its own acceptance:

  O(1) HEAD CHECK (A2).  A waking system compares the pinned `chain_head` to the LIVE head — a single
  hash comparison, current-or-stale — with NO re-fold of the record and NO walk of the chain. That is
  the whole reason a prepared waking-point exists: the wake is O(1), not a full fold. `check_head`
  reads no record and no blob; it compares two strings.

  VERIFIABLE WITHOUT THE ENGINE (A3, the air rider :2963).  A checkpoint is checked against the record
  file and the blob bytes ALONE — no gate, no views, no running kernel. `verify` imports the record
  READER (`replay_snapshot.snapshot`) and the pure primitives (`canonical_hash`, `load_pack`), never
  the engine. The tree-state is REUSED from the one reader, never re-folded by hand — a second fold
  inside the verifier would be the forbidden second-implementation class (:3017/:3018).

A checkpoint is a recovery ARTIFACT, NEVER a capability (A4): it is data a runtime reads. Handing a
checkpoint to nothing recovers nothing. RECOVERING FROM a checkpoint — waking a damaged system to it
— is EP-43's runtime; this module writes no record, moves no founding, and recovers nothing itself.
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                       # AWIG OS/src

from bridge import replay_snapshot                               # noqa: E402  — the tree-state reader (REUSED, never re-folded)
from bridge import merkle                                        # noqa: E402  — the ONE Merkle fold of that reader's output (EP-45; never a second fold)
from kernel.canonical import canonical_hash                      # noqa: E402  — the estate's one hash form ("sha256:<hex>")
from kernel.attestation import latest_attestation, ATTESTATION_ACTION  # noqa: E402
from founding.install import load_pack, PACK_PATH                # noqa: E402  — the pack's one reader (the pack is DATA)


#: The artifact kind marker. A checkpoint is data; this names what the data is.
KIND = "checkpoint"

#: The provenance triplet's three members, in wake-checklist order (body/record/constitution folded
#: to the fields' own names). ALL THREE present or it is not a checkpoint (RW1): a two-thirds
#: checkpoint cannot answer the wake's steps 1-3, so it is not a waking-point.
TRIPLET = ("chain_head", "founding_pack_sha", "attestation_head")


# --- the pure primitives (record + constitution readers; no engine) ---------------------------

def _read_records(record_path):
    """The append-only record as a list of records — a plain reader (the same shape `snapshot`
    reads), engine-free by construction. Used by the verify side, which has no store."""
    record_path = os.path.expanduser(record_path)
    if not os.path.exists(record_path):
        return []
    with open(record_path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def chain_head_of(records):
    """The chain head: `canonical_hash` of the LATEST record (store.py:1044 pins the same value on
    the next record's `prev_hash`). This is the record-integrity end (wake step 2). A record with no
    events has no head — a checkpoint cannot be taken of a recordless world (there is nothing to
    wake to)."""
    if not records:
        raise ValueError("no records — a checkpoint has no chain head to pin (nothing to wake to)")
    return canonical_hash(records[-1])


def founding_pack_sha_of(pack_path=PACK_PATH):
    """The founding pack sha: `canonical_hash` of the LOADED constitution (wake step 3, 'read back
    exact'). Kept in the estate's one hash form so all three triplet members are the same shape
    (design/34 §1). Reads the pack through its one reader; the pack is byte-untouched."""
    return canonical_hash(load_pack(pack_path))


def _latest_attestation_of(records):
    """The latest attestation RECORD from a record list, or None — the engine-free twin of
    `kernel.attestation.latest_attestation(store)` (which is `store.by_action(ATTESTATION_ACTION)
    [-1]`). Not a fold and not a view: a single record filter, forced by the air rider (the verify
    side holds no store). The create side uses the kernel's `latest_attestation` directly; both
    select the same record."""
    hits = [r for r in records if r.get("action") == ATTESTATION_ACTION]
    return hits[-1] if hits else None


def attestation_head_of(records):
    """The attestation head: `canonical_hash` of the latest attestation record — the head naming the
    engine that took the checkpoint (the record itself carries the engine's set-digest and members,
    wake step 1). None when the engine has never attested; a checkpoint then has no body to pin."""
    att = _latest_attestation_of(records)
    return canonical_hash(att) if att is not None else None


# --- validity (RW1: all three triplet members present, or not a checkpoint) -------------------

def is_valid(checkpoint):
    """A checkpoint is valid only if it carries a tree-state view AND all THREE triplet members,
    each present and non-empty. A missing member is RW1: a waking system cannot verify body, record
    and constitution from a two-thirds checkpoint, so it is not a waking-point."""
    if not isinstance(checkpoint, dict):
        return False
    if "tree" not in checkpoint or not isinstance(checkpoint.get("tree"), dict):
        return False
    prov = checkpoint.get("provenance")
    if not isinstance(prov, dict):
        return False
    for member in TRIPLET:
        val = prov.get(member)
        if not isinstance(val, str) or not val:
            return False
    return True


def missing_members(checkpoint):
    """The triplet members absent or empty — the RW1 diagnosis, named rather than a bare False."""
    prov = checkpoint.get("provenance") if isinstance(checkpoint, dict) else None
    prov = prov if isinstance(prov, dict) else {}
    return [m for m in TRIPLET if not (isinstance(prov.get(m), str) and prov.get(m))]


# --- create (the one place a store is consumed: read-only) ------------------------------------

def create(store, record_path, blob_dir, row_id=None, root=None, pack_path=PACK_PATH):
    """Take a checkpoint of a live system: the tree-state view plus the provenance triplet. Consumes
    the store READ-ONLY (its `events` for the chain head, `latest_attestation` for the body) and the
    record + blobs (for `snapshot`) and the pack (for the constitution). Appends nothing, moves no
    founding, recovers nothing.

    The attestation head is required: a checkpoint of an engine that has never attested has no body
    to pin (wake step 1), so create raises rather than emit a two-thirds artifact (RW1 at the source)."""
    records = list(store.events)
    tree = replay_snapshot.snapshot(record_path, blob_dir, row_id=row_id, root=root)
    att = latest_attestation(store)                              # the named consumed source (kernel)
    if att is None:
        raise ValueError("no attestation on record — the engine has no attested body to pin; a "
                         "checkpoint without a body is not a waking-point (wake step 1)")
    checkpoint = {
        "kind": KIND,
        "scope": {"row_id": row_id, "root": root},              # what subtree this tree-state is (verify recomputes it)
        "tree": tree,
        "provenance": {
            "chain_head": chain_head_of(records),
            "founding_pack_sha": founding_pack_sha_of(pack_path),
            "attestation_head": canonical_hash(att),
        },
    }
    if not is_valid(checkpoint):                                 # belt-and-braces: never emit an invalid artifact
        raise ValueError("checkpoint failed its own validity check: missing %s"
                         % (missing_members(checkpoint),))
    return checkpoint


# --- persistence (A1: write / read round-trips byte-identical) --------------------------------

def canonical_json(checkpoint):
    """The checkpoint's deterministic byte encoding: sorted keys, compact separators, UTF-8. Written
    and read through this, a checkpoint round-trips byte-identical (A1)."""
    return json.dumps(checkpoint, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def write(checkpoint, path):
    """Persist a checkpoint to disk. REFUSES an invalid checkpoint (missing a triplet member, RW1) —
    a two-thirds artifact never reaches the disk to be mistaken for a waking-point."""
    if not is_valid(checkpoint):
        raise ValueError("refusing to write an invalid checkpoint: missing %s"
                         % (missing_members(checkpoint),))
    path = os.path.expanduser(path)
    with open(path, "wb") as f:
        f.write(canonical_json(checkpoint))
    return path


def read(path):
    """Read a checkpoint back from disk. A pure read; recovers nothing (A4)."""
    path = os.path.expanduser(path)
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


# --- the O(1) head check (A2) -----------------------------------------------------------------

CURRENT = "current"
STALE = "stale"


def check_head(checkpoint, live_head):
    """Answer current-or-stale by a SINGLE hash comparison. `live_head` is the live chain head
    (`canonical_hash(events[-1])`, obtainable in O(1) from the store's last record). This reads NO
    record and NO blob and folds NOTHING: it compares the checkpoint's pinned `chain_head` to
    `live_head` and returns CURRENT or STALE. A head check that walked the chain or re-folded the
    record would be RW2 — this cannot, it holds no path to walk."""
    pinned = (checkpoint.get("provenance") or {}).get("chain_head")
    if not pinned:
        raise ValueError("checkpoint has no pinned chain head to compare (not a checkpoint)")
    return CURRENT if pinned == live_head else STALE


def is_current(checkpoint, live_head):
    """The head check as a boolean — True when the checkpoint's pinned head equals the live head."""
    return check_head(checkpoint, live_head) == CURRENT


# --- verify without the engine (A3) -----------------------------------------------------------

def verify(checkpoint, record_path, blob_dir, pack_path=PACK_PATH):
    """Check a checkpoint against the record file and the blob bytes ALONE — no gate, no views, no
    running engine (A3, the air rider). Recomputes each part from the records and blobs and compares
    to what the checkpoint pinned:

      tree               folds from the SAME records/blobs, via the one reader `snapshot` (REUSED,
                         never re-folded by hand — a second fold would be the forbidden class);
      chain_head         `canonical_hash` of the record file's latest record;
      founding_pack_sha  `canonical_hash` of the loaded pack;
      attestation_head   `canonical_hash` of the record file's latest attestation record.

    Returns a per-member verdict with an overall `ok`. Reads the world; changes nothing (A4). The
    scope (row_id/root) travels in the checkpoint, so the verifier reproduces the exact subtree
    without being told out of band."""
    verdict = {"ok": False, "valid": is_valid(checkpoint),
               "tree": False, "chain_head": False,
               "founding_pack_sha": False, "attestation_head": False}
    if not verdict["valid"]:
        return verdict
    records = _read_records(record_path)
    scope = checkpoint.get("scope") or {}
    recomputed_tree = replay_snapshot.snapshot(record_path, blob_dir,
                                               row_id=scope.get("row_id"), root=scope.get("root"))
    prov = checkpoint["provenance"]
    verdict["tree"] = (recomputed_tree == checkpoint["tree"])
    verdict["chain_head"] = (records != [] and chain_head_of(records) == prov["chain_head"])
    verdict["founding_pack_sha"] = (founding_pack_sha_of(pack_path) == prov["founding_pack_sha"])
    ah = attestation_head_of(records)
    verdict["attestation_head"] = (ah is not None and ah == prov["attestation_head"])
    verdict["ok"] = all(verdict[k] for k in ("tree", "chain_head", "founding_pack_sha",
                                             "attestation_head"))
    # --- EP-45 ADDITIVE: when the checkpoint is CROSS-ATTESTED (its provenance carries a merkle_root),
    #     ALSO verify that root and LOCALIZE any divergence — the diverging subtree path(s), not a bare
    #     "tree mismatch" (A2). The tree was recomputed ABOVE via the ONE reader (`snapshot`); the
    #     Merkle is one fold of THAT output through `merkle` (never a second fold of the record — the
    #     air rider). EP-44's four members and `ok` are UNCHANGED: a plain EP-44 checkpoint carries no
    #     merkle_root, so this block is inert and its A1-A5 stand (stop (i)). For a cross-attested
    #     checkpoint `ok` already implies `merkle_root` (the root derives from `tree`, whose equality is
    #     the `tree` member); `merkle_root`/`diverging` are reported ALONGSIDE, never folded into `ok`.
    mr = prov.get("merkle_root")
    if mr is not None:
        sch = merkle_scheme_of(checkpoint)                          # B11: fold under the checkpoint's OWN scheme
        verdict["merkle_root"] = (merkle.merkle_root(recomputed_tree, sch) == mr)
        if not verdict["merkle_root"]:
            verdict["diverging"] = merkle.localize(checkpoint["tree"], recomputed_tree, sch)
    return verdict


def merkle_scheme_of(checkpoint):
    """The MERKLE-SCHEME VERSION a checkpoint's root was folded under (B11; EP-MAINT-OUTSIDE-2). Read
    from provenance; ABSENT reads as scheme 1 (children-only) so every root minted before B11 verifies
    UNCHANGED. A verifier folds the recomputed tree under THIS, never under the current default — that
    is what makes a directory's-metadata upgrade backward-safe across already-attested checkpoints."""
    scheme = (checkpoint.get("provenance") or {}).get("merkle_scheme")
    return scheme if scheme is not None else merkle.SCHEME_CHILDREN_ONLY


# --- cross-attestation (EP-45): the checkpoint made MERKLE-SHAPED, the diving-buddy pairing --------
#
# A CROSS-ATTESTED CHECKPOINT is EP-44's checkpoint with a Merkle root ADDED to its provenance and a
# WITNESS naming the fold that computed it. EP-44's `create` is UNTOUCHED — its three-member triplet
# stands (its A1 pins `set(TRIPLET) == set(provenance)`), so this is a SEPARATE additive constructor,
# never a mutation of `create` (a broken EP-44 acceptance is stop (i), a regression, not this EP).


def cross_attest(store, record_path, blob_dir, witness, row_id=None, root=None,
                 peer_root=None, pack_path=PACK_PATH):
    """Take a CROSS-ATTESTED checkpoint: `create`'s artifact plus a `merkle_root` over its tree-state,
    a `witness` (the fold identity — no single writer produces both of a pair), and, when pairing, the
    peer witness's `peer_root` (each checkpoint carries the OTHER's root — design/47 §4). The
    merkle_root rides EP-44 A1 (it lives in provenance, so it persists and reads back byte-identical
    through `write`/`read`). `is_valid`/`write` still hold: they check the triplet is present, and
    ADDED keys are lawful."""
    cp = create(store, record_path, blob_dir, row_id=row_id, root=root, pack_path=pack_path)
    cp["provenance"]["merkle_root"] = merkle.merkle_root(cp["tree"])
    # B11 (EP-MAINT-OUTSIDE-2): RECORD the scheme this root was folded under, so a verifier folds the
    # recomputed tree under the SAME scheme. A checkpoint that omits it (every one minted before B11)
    # reads as scheme 1 (children-only) in `merkle_scheme_of`, so old roots verify unchanged.
    cp["provenance"]["merkle_scheme"] = merkle.CURRENT_SCHEME
    cp["witness"] = witness
    if peer_root is not None:
        cp["peer_root"] = peer_root
    return cp


def _recompute_root(cp, record_path, blob_dir):
    """Recompute a cross-attested checkpoint's Merkle root from the record file and blob bytes ALONE —
    the air rider: the ONE reader (`replay_snapshot.snapshot`, REUSED) folds the record into the
    tree-state, and `merkle.merkle_root` folds that output ONCE. No gate, no views, no engine, no
    second fold of the record. The checkpoint's own scope (row_id/root) travels with it, so the
    verifier reproduces the exact subtree without being told out of band."""
    scope = cp.get("scope") or {}
    tree = replay_snapshot.snapshot(record_path, blob_dir,
                                    row_id=scope.get("row_id"), root=scope.get("root"))
    return merkle.merkle_root(tree, merkle_scheme_of(cp))            # B11: the checkpoint's OWN scheme


def pairing_verdict(cp_a, record_path_a, blob_dir_a, cp_b, record_path_b, blob_dir_b):
    """THE DIVING-BUDDY PAIRING (design/47 §4) at checkpoint scale — a MUTUAL RECEIPT, never one
    signer's claim. Two cross-attested checkpoints taken by INDEPENDENT folds, each carrying the
    OTHER's `merkle_root`; the verdict holds ONLY when BOTH witnesses confirm the other's root against
    an INDEPENDENT recompute (from the record + blobs alone — the air rider), AND the two folds are
    independent (no shared write-path — one hand cannot produce both). Neither checkpoint alone is
    authority: a one-sided confirmation, an absent peer root, a non-recomputing root, or a single
    shared writer all FAIL.

    COMPUTATION-BLINDNESS, ONE MACHINE (the design/28 §7 EP-09 shape). "Independent" here is blindness
    of COMPUTATION: the two roots arise from two folds, neither reading the other's, checked by their
    distinct witnesses. The TWO-PHYSICAL-BODIES half of the diving buddy (one witness in the chip's own
    memory, one on disk, no shared write-path across devices) is design/47 §4's cap and is C7's — it is
    NOT claimed here. This proves the pairing STRUCTURE refuses a common-mode (one-fold) receipt, not
    physical separation."""
    a_root = (cp_a.get("provenance") or {}).get("merkle_root")
    b_root = (cp_b.get("provenance") or {}).get("merkle_root")
    a_peer = cp_a.get("peer_root")                               # A carries B's root
    b_peer = cp_b.get("peer_root")                               # B carries A's root
    a_witness, b_witness = cp_a.get("witness"), cp_b.get("witness")

    recompute_a = _recompute_root(cp_a, record_path_a, blob_dir_a)   # independent recompute of A's root
    recompute_b = _recompute_root(cp_b, record_path_b, blob_dir_b)   # independent recompute of B's root

    a_self = (a_root is not None and a_root == recompute_a)      # A's own pinned root recomputes
    b_self = (b_root is not None and b_root == recompute_b)      # B's own pinned root recomputes
    a_confirms_b = (a_peer is not None and a_peer == recompute_b)  # the root A carries for B is B's real root
    b_confirms_a = (b_peer is not None and b_peer == recompute_a)  # the root B carries for A is A's real root
    independent = (a_witness is not None and b_witness is not None and a_witness != b_witness)

    return {
        "a_self": a_self, "b_self": b_self,
        "a_confirms_b": a_confirms_b, "b_confirms_a": b_confirms_a,
        "independent": independent,
        "ok": a_self and b_self and a_confirms_b and b_confirms_a and independent,
    }


# --- the recovery-capacity law's shape (EP-45; owner-gated founding create, HELD §8-f) -------------
#
# Over the pair stands the RECOVERY-CAPACITY LAW (design/37 §5, the owner's fanqie insight): recovery
# capacity = CONTENT redundancy × RELATIONAL redundancy; relations ADJUDICATE (localize damage,
# constrain the missing piece, verify candidates), anchors SUPPLY (replicas, firmware copy,
# full-fidelity projections — the living dialects); neither alone recovers. The law's ADMISSION into a
# founding world rides the EXISTING founding door (its per-subsystem coverage names a founded space,
# refused by the installer's referential-integrity check when it does not — no new founding check kind
# is minted, stop (e); the EP-31 precedent — the §A51 condition resolves inside the wording). These
# predicates are the law's WELL-FORMEDNESS over its own record (population + basis stated; never a
# truncating recover) — pure data readers, no engine.


def capacity_law_wellformed(law):
    """Is a recovery-capacity law well-formed per §A51 (population + basis) and :3024 (never-truncate)?

    §A51 — A SUM CANNOT RECOVER ITS ADDENDS. Coverage is a DECLARED design property, never assumed: the
    law must STATE, per subsystem, both what SUPPLIES it (the content anchor — the population, which
    full-fidelity projection exists) and what ADJUDICATES it (the relational redundancy — the basis).
    A bare "recoverable" with no per-subsystem population + basis is not well-formed (RW5). And the
    recover-discipline must be append-only (`capacity_never_truncates`) — a wording that permits a
    shortening recover is the forbidden delete (RW6, :2856/:3024)."""
    if not isinstance(law, dict):
        return False
    pl = law.get("payload") or {}
    coverage = pl.get("coverage")
    if not isinstance(coverage, (list, tuple)) or not coverage:
        return False                                            # bare "recoverable" — no population stated
    for c in coverage:
        if not isinstance(c, dict):
            return False
        if not c.get("subsystem"):                              # population: WHICH subsystem
            return False
        if not c.get("content"):                                # basis: what SUPPLIES (the anchor / living dialect)
            return False
        if not c.get("relational"):                             # basis: what ADJUDICATES (the relation)
            return False
    return capacity_never_truncates(law)


def capacity_never_truncates(law):
    """The :3024 precision AS LAW (RW6, stop (h)): a recover APPENDS a recover row and NEVER removes,
    rewrites, or shortens the record — rows past the break stay as adjudicated-broken history, the
    served state is the checkpoint plus verified segments. A capacity law is truncation-safe only when
    it declares append-only recover-discipline and does not permit truncation. A wording that permits a
    shortening recover is the one delete the estate forbids."""
    if not isinstance(law, dict):
        return False
    pl = law.get("payload") or {}
    if pl.get("recover_discipline") != "append-only":
        return False
    if pl.get("permits_truncation"):
        return False
    return True
