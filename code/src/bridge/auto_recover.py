# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture (recover ceremony, checkpoint, chain adjudication, diving-buddy
# cross-attestation, hash rematch, halt-and-notify, fail-safe) per OS textbooks and the
# seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability of any kind. Full declaration:
# SCOPE-STATEMENT.md.
"""The AUTO-RECOVER orchestrator — the recover ceremony's SECOND trigger (EP-43-AUTO; ARC R, the
genesis-guardian family; owner ruling board :3057; design/37 §5, design/47 §4).

The recover ceremony (EP-43) already carries ONE trigger: the manual owner-gated act — the root
authority holder drives a splice by hand (design/37 §5, "never automatic"). This module adds a SECOND
trigger: an AUTO recover under a TRIPLE CHECK, refining "never automatic" (reasoning-standard R7 —
the later owner ruling controls; the earlier stance's reason, "an auto-repair door is a laundering
door", is HONOURED because the chain's never-to-wrongness is one of the three checks, unchanged). Auto
is a STRICTER gate than manual, and a fail-safe by construction (avoid-fail beats maximize-success —
"nuclear-plant-grade", the owner's words):

    attempt auto-recover
      TRIPLE CHECK, all three ->  NOTIFY and AUTOPROCEED with the splice
      ANY one (or verify-at-load) fails ->  HALT and NOTIFY the owner, restore NOTHING,
                                            fall back to the manual owner-gated recover

THE THREE CHECKS — composed HERE, across the layer, because THE BRIDGE IS THE ONLY PLACE THEY MEET
(a checkpoint and a buddy pairing are BRIDGE artifacts; the recover op is a KERNEL op):

  (1) CHAIN — the chain adjudicates the target as a SOUND lawful prior point. This is the KERNEL recover
      op's OWN never-to-wrongness + chain adjudication, REUSED (`erasure._seq_of_head` +
      `store.verify_chain`), never re-implemented: a fabricated head folds to `None` (the laundering-
      door stays shut); a head beyond the break is not within `verified_through`.
  (2) CHECKPOINT — the FULL VERIFIER (`checkpoint.verify`, EP-44; R5 EP-MAINT-OUTSIDE-4): the checkpoint
      recomputes against THIS store's record + blobs — tree, chain head, founding-pack sha AND
      attestation head — not merely a `check_head` string-compare of the pinned head (which a moved
      tree, a swapped pack or a stale attestation would slip past). Still engine-free (the air rider
      :2963 — no gate, no views); the walk is the recompute the verifier already does. `check_head`
      keeps its role (live staleness — a moved head still HALTS). It is BOUND to the recovering subject
      by the checkpoint's pinned IDENTITY (chain head + Merkle root), never by file path — the diving
      buddy's two bodies are independent replicas at DIFFERENT paths; a pair naming no member that pins
      this store's content has no subject to verify and HALTS.
  (3) BUDDY — the diving-buddy mutual receipt (`checkpoint.pairing_verdict`, EP-45): two checkpoints by
      INDEPENDENT folds, each confirming the other's Merkle root; neither alone is authority. Engine-
      free (the air rider). A one-sided receipt HALTS — and (R5) a pair that does not NAME this store
      (a valid receipt about two OTHER stores) does not authorise a recover of THIS one and HALTS.

LAYERING (§8-h, RW5). This is a BRIDGE module: bridge sits ABOVE the kernel. It consumes the kernel
recover op read-only (via the gate) and the two bridge checks; the KERNEL never imports the bridge —
the target head travels INTO the kernel op as a param, and the three-check OUTCOME travels in as opaque
DATA that the kernel records but never re-derives (it holds no checkpoint and no buddy). The kernel's
own chain check runs regardless of trigger, so never-to-wrongness is enforced BELOW the bridge too.

NOTIFY (board :3082 precision 2). The NOTICE is RECORD-FIRST: on autoproceed the recover ROW ITSELF is
the notice (the splice records the triple-check outcome). A `notify` callback, where a deployment has
declared a comms channel, is a GOVERNED comms act — never a bare side-channel; it carries the same
event the record does. On a HALT before any kernel act the record is UNCHANGED (restore nothing), so
the notice is the callback and the returned result — the owner is told, nothing is written.

THE AMEND IS GOVERNED AND HELD (§8-f). The recover law's auto-trigger rides the governed AMEND-OP door
(`kernel.opdefs`) in a TEST founding world; PRODUCTION `founding-pack.json` stays BYTE-UNTOUCHED. NO
new founding kind, NO new check-kind, NO version bump — the triple check COMPOSES three checks that
ALREADY exist (chain, checkpoint, buddy). The auto path flips live on the owner's mover (with the
recover op's own two-unit shape); until then it is proven in disposable test worlds only.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                       # AWIG OS/src

from kernel import erasure                                       # noqa: E402  — the KERNEL recover op (chain check + verify-at-load + the single splice)
from kernel.canonical import canonical_hash                      # noqa: E402  — the estate's one hash form (the live head, O(1))
from kernel.errors import OpError                                 # noqa: E402  — a kernel refusal (verify-at-load halt / the anchor) surfaces here
from bridge import checkpoint                                    # noqa: E402  — check_head (EP-44) + pairing_verdict (EP-45); the two engine-free checks


#: The two orchestrator outcomes. AUTOPROCEEDED — the triple check (and verify-at-load) passed and the
#: splice was appended. HALTED — a check (or verify-at-load) failed; nothing was restored.
AUTOPROCEEDED = "autoproceeded"
HALTED = "halted"

#: The three check names, in ruling order (chain / checkpoint / buddy). All three, or the auto path halts.
CHECKS = ("chain", "checkpoint", "buddy")


def _live_head(store):
    """The live chain head — `canonical_hash` of the latest record (store.py:1044 pins the same value
    on the next record's prev_hash), obtainable in O(1). None for a recordless world."""
    return canonical_hash(store.events[-1]) if store.events else None


def triple_check(store, cp, target_head, buddy_pair):
    """Compose the three checks over a target head and a checkpoint (+ its buddy). READ-ONLY — it folds
    and compares, and writes NOTHING (the record is untouched whatever the verdict). Returns a dict
    with the three booleans, an overall `ok` (all three), and `failed` (the names that did not pass):

        {"chain": bool, "checkpoint": bool, "buddy": bool, "ok": bool, "failed": [str, ...]}

    `buddy_pair` is the 6-tuple `checkpoint.pairing_verdict` takes:
    `(cp_a, record_path_a, blob_dir_a, cp_b, record_path_b, blob_dir_b)` — the two INDEPENDENT folds."""
    # THE PAIR MUST NAME THIS STORE (R5, EP-MAINT-OUTSIDE-4). The recovering subject is the store whose
    # checkpoint `cp` pins THIS content — its chain head and Merkle root. The buddy pair carries two
    # cross-attested checkpoints (each over an INDEPENDENT replica record file — the diving-buddy's two
    # bodies, at DIFFERENT paths by design). Binding by file PATH would reject that legitimate model, so
    # the subject is bound by pinned IDENTITY: the pair member whose checkpoint pins the same content as
    # `cp`. A valid pair about two OTHER stores names no such member and does not authorise a recover of
    # THIS store — both the checkpoint and the buddy check then fail.
    def _ident(c):
        p = c.get("provenance") or {}
        return (p.get("chain_head"), p.get("merkle_root"))
    cp_a, rp_a, bd_a, cp_b, rp_b, bd_b = buddy_pair
    cp_ident = _ident(cp)
    mine = next(((c, rp, bd) for (c, rp, bd) in ((cp_a, rp_a, bd_a), (cp_b, rp_b, bd_b))
                 if _ident(c) == cp_ident), None)
    names_this_store = mine is not None
    # (1) CHAIN — the kernel op's OWN adjudication, reused. A fabricated head -> None (never to
    #     wrongness, the laundering-door shut); a head beyond the break -> not within verified_through.
    fold = store.verify_chain()
    target_seq = erasure._seq_of_head(store, target_head)
    chain = (target_seq is not None and target_seq <= fold["verified_through"])
    # (2) CHECKPOINT — LIVE STALENESS *and* the FULL VERIFIER (R5). `check_head` keeps its role: the
    #     pinned head must equal the LIVE head (a moved head halts — a check the verifier over a frozen
    #     replica cannot make). ADDED is the previously-UNUSED full verifier `checkpoint.verify`, which
    #     recomputes the tree, the chain head, the founding-pack sha AND the attestation head from the
    #     record + blobs the checkpoint pins (still engine-free — the air rider) — so a matching head
    #     over a corrupt tree, a swapped pack or a stale attestation now HALTS where the O(1) string
    #     compare passed. Bound to this store's own identity; a pair not naming this store fails.
    cp_ok = (names_this_store
             and checkpoint.check_head(cp, _live_head(store)) == checkpoint.CURRENT
             and bool(checkpoint.verify(cp, mine[1], mine[2])["ok"]))
    # (3) BUDDY — the diving-buddy mutual receipt (engine-free): both witnesses confirm the other's root
    #     against an independent recompute, and the two folds are independent. A one-sided receipt fails.
    #     R5: the pairing must ALSO name this store — a valid pair about two OTHER stores does not pass.
    buddy = bool(checkpoint.pairing_verdict(*buddy_pair)["ok"]) and names_this_store
    verdict = {"chain": chain, "checkpoint": cp_ok, "buddy": buddy}
    verdict["ok"] = chain and cp_ok and buddy
    verdict["failed"] = [name for name in CHECKS if not verdict[name]]
    return verdict


def _notify(notify, result):
    """The GOVERNED comms act, where a deployment declared a channel (board :3082 precision 2). The
    record is the primary notice; this callback carries the SAME event and is never a bare side-channel.
    Absent a channel it is a no-op — the returned result and the record stand."""
    if notify is not None:
        notify(result)


def auto_recover(gate, store, cp, target_head, checkpoint_ref, segments, rule, buddy_pair,
                 notify=None, actor="SYSTEM"):
    """Attempt an AUTO recover under the TRIPLE CHECK. On a triple match NOTIFY and AUTOPROCEED with the
    splice (the KERNEL recover op does the chain re-check + verify-at-load + the single append); on ANY
    of the three failing, OR on verify-at-load failing inside the splice, HALT and NOTIFY the owner,
    append NO splice, and fall back to the manual owner-gated recover (which this never touches).

    Returns a result dict: `{"outcome", "triple_check", "spliced", "record", "reason"?}`. `outcome` is
    AUTOPROCEEDED or HALTED; `spliced` is True only on an appended splice; `record` is the splice row on
    autoproceed, else None. The auto splice is driven as `actor` (SYSTEM by default — the automatic
    trigger, admitted by the recover op's owner-gate) and carries `trigger=auto` + the triple-check
    outcome, so the row PROVES it woke automatically under the triple check."""
    tc = triple_check(store, cp, target_head, buddy_pair)
    if not tc["ok"]:
        # HALT before any kernel act — restore NOTHING (the append-only record is UNCHANGED; the auto
        # trigger never reached the op). NOTIFY the owner: the fail-safe — nuclear-plant-grade is not a
        # two-of-three vote (RW1). The manual owner-gated recover is the fallback.
        result = {"outcome": HALTED, "triple_check": tc, "spliced": False, "record": None,
                  "reason": "the triple check did not pass (failed: %s) — halting and notifying the "
                            "owner, restoring nothing; the manual owner-gated recover is the fallback"
                            % ", ".join(tc["failed"])}
        _notify(notify, result)
        return result
    # ALL THREE PASS -> AUTOPROCEED. The kernel recover op re-runs its OWN never-to-wrongness + chain
    # adjudication (unchanged) and the verify-at-load; a corrupt or missing segment HALTS there
    # (OpError, no splice — the handover-halt pattern inward). The kernel takes the three-check OUTCOME
    # as DATA and imports no bridge module (layering).
    params = {erasure.TARGET_HEAD: target_head, erasure.CHECKPOINT_REF: checkpoint_ref,
              erasure.RECOVER_RULE: rule, "segments": list(segments),
              erasure.TRIGGER: erasure.TRIGGER_AUTO,
              erasure.TRIPLE_CHECK: {name: tc[name] for name in CHECKS}}
    try:
        gate.execute(erasure.RECOVER_OP, actor, params)
    except OpError as e:
        # verify-at-load (or the kernel's own re-check) HALTED — no splice was written. NOTIFY the
        # owner; fall back to manual. The auto trigger reaches only a point verify-at-load confirms.
        result = {"outcome": HALTED, "triple_check": tc, "spliced": False, "record": None,
                  "reason": "verify-at-load halted the auto splice (%s) — restoring nothing; the manual "
                            "owner-gated recover is the fallback" % e}
        _notify(notify, result)
        return result
    # the splice IS the notice (record-first, board :3082 precision 2). Report the autoproceed.
    result = {"outcome": AUTOPROCEEDED, "triple_check": tc, "spliced": True,
              "record": store.events[-1]}
    _notify(notify, result)
    return result
