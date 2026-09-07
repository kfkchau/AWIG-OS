# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — engine attestation (EP-40-BUILD; design/37 Q3 + §9).

Boot appends an attestation record citing ONE digest over the enumerated S-plane engine
artifact set — the store, the gate interpreter, the fold machinery, the check engines, the
canonical serializer, AND the digest machinery ITSELF (this module and canonical.py). So
"which engine processed these records" becomes a citable, replayable fact OF THE RECORD,
and T-NO-LAW-IN-CODE gains its integrity twin.

THE HONEST BOUND (design/37 §9, stated not implied away). Self-attestation on one machine
proves CITABILITY, not immunity. The record makes the engine version a checkable fact; what
the platform beneath it reports is the platform's word. Hardware roots of trust are
deployment mechanism, not architecture — the same division the driver shim drew for
physical enforcement. The doc-facing names read `citable`, never `trusted`.

THE ATTESTED SET IS THE S-PLANE (design/28 §10): the enumerated .py artifacts under src/
EXCEPT src/founding/, which holds the LAW (founding-pack.json data + the installer), not
engine mechanism. That surface is EXACTLY what T-NO-LAW-IN-CODE greps
(tests/test_law_out_of_code._src_py_outside_founding). Recording the set as that same walk
is what makes the F4 twin's coverage claim EXACTLY true: everything the law guard greps is
inside the attested set, by construction (architect ruling, board :2751, tooth iii). The set
is a RECORDED LIST (`ATTESTED_MEMBERS`), grow-only: adding a member is a deliberate act
logged in BUILD-PROGRESS; a removal is a RAISE, never a silent edit (F1; RW3).

THE EXCLUSION, NAMED WITH WHY (architect ruling board :2751, teeth i and ii). The guest
kernel module (planning/vm/govosfs/) is deliberately OUT of the attested set. The guest
LOADS it, so the guest's word is the platform's word (§9 citability cap; the driver-shim
division). A host-side digest of code the host does not execute would make the attestation
assert a fact outside the engine's causal reach — a claim stronger than reality, the
false-assurance class, strictly worse than a named boundary. Its FUTURE PATH is named:
govosfs joins the attested set when attestation runs WHERE THE MODULE LOADS (in-guest,
campaign 7 self-hosting), never as a host-side file digest. It is not under src/, so it is
naturally outside the walk; `EXCLUDED` records why it is deliberately out and when it joins.

THE APPEND IS A GOVERNED SYSTEM OP THROUGH THE GATE (:2769 R2, folded 2026-09-03). At
attestation time the gate already exists, so a post-genesis record that reached the file by the
genesis-class raw `store._append` would be an ungated record — refused by name (the sole-appender
leash, tests/test_ep28g_w5). The attestation therefore rides `gate.execute` like every other
post-genesis SYSTEM act (the obligations executor, the OVERTURN path); the gate is the one
sanctioned appender and no existing op is stretched to carry it past the kind-gate.

THE OP IS OWNER-GATED founding vocabulary (:2769 item 4, the EP-36 / MEM-LAW-BUDGET shape). Its
handler computes file digests — Python the closed data-born check vocabulary cannot express — so
it is a CODE-registered op (`register_attestation`), the same shape the protection ops use, not a
pack `CREATE-OP`. Registering founding-integrity vocabulary is the owner's word: production
`compose.build_full_kernel` does NOT register it, so `attest_boot` finds no op and appends nothing
— the compose-layer wiring is present but INERT, and production's `founding-pack.json` stays
byte-untouched. The flip to live is one mechanical line (call `register_attestation` in compose)
when the owner's word lands; until then the whole-ledger-attesting acceptance is HELD and the
mechanism is proven only in the TEST founding worlds that call `register_attestation` themselves.
"""

import os

from .canonical import canonical_hash

# The S-plane root and the one excluded subtree. `founding/` is the LAW's home (data +
# installer), so the law guard greps src/ MINUS founding and the attested set is that surface.
_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))   # .../src
_FOUNDING = os.path.join(_SRC, "founding")

ATTESTATION_ACTION = "attestation"
# The boot-integrity root law the order (EP-40.md F2) names by id — cited, never quoted: the
# law TEXT lives only under founding/ (T-NO-LAW-IN-CODE, the guard this module twins). The
# attestation is that condition's integrity twin.
ATTESTATION_RULE = "BOOT-INT"

# THE ENUMERATED ATTESTED SET — a RECORDED LIST, grow-only (F1). Every .py under src/ outside
# founding/, as of authoring (EP-40-BUILD, 2026-09-03). It INCLUDES the digest machinery
# ITSELF — kernel/canonical.py and kernel/attestation.py — which is what closes the EP-09
# shared-digest-function cap (design/37 Q3): the function both audit streams rely on is inside
# the attested surface, its change history visible. A member is added ONLY as a deliberate,
# logged act (BUILD-PROGRESS); a removal is a RAISE. The T-NO-LAW-IN-CODE twin (below) reds if
# this list ever falls behind the guard's grep surface, so a new S-plane .py cannot slip in
# outside attestation coverage.
ATTESTED_MEMBERS = (
    "bridge/__init__.py",
    "bridge/auto_recover.py",   # grow-only add under EP-43-AUTO-AMEND-BUILD (archi :3031/:3041,
                                # carried in-fence): a new src/bridge/*.py the law guard greps (the
                                # AUTO-RECOVER orchestrator composing the triple check), so the F4 twin
                                # requires it here — same precedent as bridge/merkle.py (:3045).
    "bridge/checkpoint.py",
    "bridge/custody.py",
    "bridge/fuse_files.py",
    "bridge/kernel_port.py",
    "bridge/merkle.py",   # grow-only add under EP-45-BUILD (archi :3031, carried in-fence): a new
                          # src/bridge/*.py the law guard greps (the Merkle over a checkpoint's
                          # tree-state), so the F4 twin requires it here — same precedent as
                          # kernel/keys.py (:2781/:2782) and kernel/erasure.py (:2842).
    "bridge/mount.py",
    "bridge/records_fs.py",
    "bridge/replay_snapshot.py",
    "bridge/run_fuse_files.py",
    "bridge/seal.py",   # grow-only add under EP-46-BUILD (archi :3031, carried in-fence): a new
                        # src/bridge/*.py the law guard greps (the content-at-rest sealer, the key
                        # family's read direction), so the F4 twin requires it here — same precedent
                        # as bridge/merkle.py (:3045) and kernel/keys.py (:2781/:2782).
    "kernel/__init__.py",
    "kernel/attestation.py",
    "kernel/authority.py",
    "kernel/blobs.py",
    "kernel/boot.py",
    "kernel/canonical.py",
    "kernel/commit.py",
    "kernel/compose.py",
    "kernel/crossing.py",
    "kernel/erasure.py",   # grow-only add — MAINT-ATTEST-ADD-ERASURE (board :2842): the EP-41B destruction-ceremony surface, a src/kernel/*.py the law guard greps, so the F4 twin requires it here (same precedent as kernel/keys.py :2781/:2782).
    "kernel/errors.py",
    "kernel/gate.py",
    "kernel/keys.py",   # grow-only add under EP-40-BUILD (mgr ruling :2781, archi-reconciled :2782):
                        # a new src/kernel/*.py the law guard greps, so the F4 twin requires it here.
    "kernel/obligations.py",
    "kernel/opdefs.py",
    "kernel/protection.py",
    "kernel/push.py",
    "kernel/reconcile.py",
    "kernel/store.py",
    "kernel/syscall_port.py",
    "kernel/vault.py",
    "kernel/views.py",
    "observe/__init__.py",
    "observe/classmap.py",
    "observe/m1_runner.py",
    "observe/process_watch.py",
    "observe/resource_watch.py",
    "observe/seam.py",
    "observe/shadow.py",
    "observe/windows.py",
    "subsystems/__init__.py",
    "subsystems/comms.py",
    "subsystems/devices.py",
    "subsystems/files.py",
    "subsystems/memory.py",
    "subsystems/scheduling.py",
)

# THE KNOWN-OUT MEMBER, DECLARED (architect ruling board :2751, tooth i) — a silent exclusion
# is an undeclared exclusion. This states WHY the boundary is drawn here and WHEN it moves.
EXCLUDED = {
    "planning/vm/govosfs/": (
        "the guest kernel module (EP-28) — guest-LOADED, so the guest's word is the "
        "platform's word (design/37 §9 citability cap; the driver-shim division). A host-side "
        "digest of code the host does not execute would claim more than it proves — the "
        "false-assurance class. FUTURE PATH: joins the attested set when attestation runs "
        "in-guest (campaign 7 self-hosting), where the module loads, never as a host-side "
        "file digest."
    ),
}


def _member_digest(rel, src_dir):
    """The canonical digest of one member's bytes, or None if the member is not on disk.

    Uses the estate's ONE canonical serializer (canonical.py) — the digest machinery that is
    itself an attested member. `None` (an unreadable/absent member) is a fact the match probe
    reports, never a crash: an attested artifact that has vanished is exactly the divergence
    this surface exists to make loud."""
    p = os.path.join(src_dir, rel)
    try:
        with open(p, "rb") as f:
            return canonical_hash(f.read())
    except OSError:
        return None


def attested_set(src_dir=None):
    """The enumerated attested set: {member: canonical byte-digest} over `ATTESTED_MEMBERS`,
    plus one `set_digest` over the whole map (canonical, so key order and platform variance
    cannot move it) and the declared `excluded` boundary. Reads `_SRC` unless `src_dir` is
    given (the test drives the detect direction over a mutated temp tree)."""
    src = src_dir or _SRC
    members = {rel: _member_digest(rel, src) for rel in ATTESTED_MEMBERS}
    return {
        "kind": "attestation",
        "members": members,
        "set_digest": canonical_hash(members),
        "excluded": dict(EXCLUDED),
    }


def law_guard_surface(src_dir=None):
    """Every .py under src/ EXCEPT founding/ — the surface T-NO-LAW-IN-CODE greps, walked here
    the same way `tests/test_law_out_of_code._src_py_outside_founding` walks it. The F4 twin
    holds this against `ATTESTED_MEMBERS`; on the real tree the two sets are EQUAL by
    construction (the manifest IS this walk, frozen), so the twin's coverage claim is exactly
    true and a planted extra .py surfaces immediately."""
    src = src_dir or _SRC
    founding = os.path.join(src, "founding")
    out = []
    for root, _dirs, files in os.walk(src):
        if os.path.abspath(root).startswith(os.path.abspath(founding)):
            continue
        for name in files:
            if name.endswith(".py"):
                p = os.path.join(root, name)
                out.append(os.path.relpath(p, src).replace(os.sep, "/"))
    return sorted(out)


def twin_uncovered(src_dir=None):
    """THE T-NO-LAW-IN-CODE TWIN (F4) — the law guard's grepped surface MINUS the attested set.

    Every governance-bearing surface the guard greps must be inside attestation coverage. This
    returns any grepped .py NOT in `ATTESTED_MEMBERS`; it is EMPTY on the real tree because the
    manifest is that same walk. A non-empty answer is a governance surface outside coverage
    (RW1) — the near-miss the test drives by planting a .py in a temp src outside founding and
    absent from the manifest. Routed to the owner queue as a VIEW; appends nothing."""
    return sorted(set(law_guard_surface(src_dir)) - set(ATTESTED_MEMBERS))


def latest_attestation(store):
    """The latest attestation record, or None. A pure read; appends nothing."""
    recs = store.by_action(ATTESTATION_ACTION)
    return recs[-1] if recs else None


def match_probe(store, src_dir=None):
    """THE MATCH PROBE (F3), BOTH DIRECTIONS — a DERIVED check that appends NOTHING (the
    owner-queue view family: protection.dual_blind_divergences, views.contradictions). Answers
    "does the running engine match its last attestation?":

      matches   the current attested-set digest equals the latest attestation's;
      changed   members whose current byte-digest differs from the attestation's — a mutated
                engine artifact with no new boot attestation, the silent engine change this
                surface exists to make LOUD (RW2);
      missing   members the attestation recorded that are no longer present — the SHRINK
                direction (grow-only, RW3: a removal routes to the owner as a deliberate-act
                violation, never a silent edit);
      added     members present now but absent from the latest attestation.

    A non-empty changed/missing routes to the owner queue exactly as record divergence does
    (protection §7): the return value IS the queue entry; nothing is appended. With no
    attestation on record it reports attested=False / matches=False — an engine that never
    attested is not a matching engine (the near-miss control §A64: a probe that cannot report a
    mismatch is not a probe)."""
    current = attested_set(src_dir)
    latest = latest_attestation(store)
    if latest is None:
        return {"attested": False, "matches": False,
                "reason": "no attestation on record — the engine has never attested",
                "set_digest": current["set_digest"],
                "changed": [], "missing": [], "added": sorted(current["members"])}
    recorded = dict((latest.get("payload") or {}).get("members") or {})
    cur = current["members"]
    changed = sorted(r for r in recorded if r in cur and cur[r] != recorded[r])
    missing = sorted(r for r in recorded if r not in cur)
    added = sorted(r for r in cur if r not in recorded)
    matches = (current["set_digest"] == (latest.get("payload") or {}).get("set_digest"))
    return {"attested": True, "matches": matches,
            "set_digest": current["set_digest"],
            "attested_digest": (latest.get("payload") or {}).get("set_digest"),
            "changed": changed, "missing": missing, "added": added}


# THE ATTESTATION OP — the owner-gated founding-integrity vocabulary (:2769 item 4). Registering
# it is the owner's word; production compose does not, so the op stays absent there and the
# compose-layer wiring is inert. The op name is a SYSTEM boot-integrity act, not a runtime power.
ATTESTATION_OP = "ATTEST-ENGINE"


def _attestation_draft(src_dir=None):
    """The attestation record the handler RETURNS to the gate (the gate is the sole appender, so a
    handler returns a draft carrying no `seq`; the gate performs the one write). Carries the
    set-digest AND the per-member listing (the RAISED-BY-DESIGN default: one set-digest plus a
    per-file listing locates a change without N chain entries — owner's word at the verdict) and
    the declared exclusion boundary."""
    current = attested_set(src_dir)
    return {
        "actor": "SYSTEM",
        "action": ATTESTATION_ACTION,
        "object": "engine",
        "rule_cited": ATTESTATION_RULE,
        "payload": {
            "kind": "attestation",
            "set_digest": current["set_digest"],
            "members": current["members"],
            "excluded": current["excluded"],
        },
    }


def _attest_handler(actor, params):
    # The gate invokes this with actor="SYSTEM"; it returns the draft over the tree named by
    # `src_dir` (None -> the running engine's real src/). The gate does the append.
    return _attestation_draft((params or {}).get("src_dir"))


def register_attestation(gate):
    """Register the attestation op — the OWNER-GATED founding-integrity CREATE, modelled as a CODE
    registration because its handler computes file digests (Python the data-born check vocabulary
    cannot express — the same reason the authority and protection ops carried handler logic).

    Production `compose.build_full_kernel` does NOT call this: until the owner's word the op is
    absent and `attest_boot` is inert. A TEST founding world calls it to prove the mechanism end to
    end; the live flip is one line here in compose when the word lands. Idempotent: re-registration
    is a no-op (the gate refuses a duplicate op, so we guard with `gate.has`)."""
    if not gate.has(ATTESTATION_OP):
        gate.register(
            ATTESTATION_OP,
            {"description": "SYSTEM appends the engine attestation (the boot-integrity twin of "
                            "T-NO-LAW-IN-CODE); the digest of the running engine becomes a fact of "
                            "the record",
             "rules": [ATTESTATION_RULE], "params": {}},
            _attest_handler,
        )


def attest_boot(store, gate, src_dir=None):
    """THE BOOT APPEND at the COMPOSE LAYER (design/37 Q3; F2; :2769 R1). Compute the running
    engine's attested-set digest and append an attestation record citing BOOT-INT THROUGH THE GATE
    (:2769 R2) — UNLESS one of two conditions holds, in which case boot appends NOTHING:

      INERT     the attestation op is not registered in this deployment — production, where the
                owner-gated op is absent and `founding-pack.json` is byte-untouched. `attest_boot`
                returns None and no record (not even a refusal) reaches the file: it never calls the
                gate for an unregistered op, so production stays truly inert (:2769 item 4).
      IDEMPOTENT the latest attestation already carries this exact set-digest (F2; RW4): a second
                boot over an unchanged tree yields the same attested digest, never a divergent
                record — the check is BEFORE the gate call, so an idempotent reload appends nothing.

    Returns the appended record, or None (inert or idempotent). The gate is the one sanctioned
    appender — `store._append` here would be an ungated post-genesis record, refused by name."""
    if gate is None or not gate.has(ATTESTATION_OP):
        return None
    current = attested_set(src_dir)
    latest = latest_attestation(store)
    if latest is not None and (latest.get("payload") or {}).get("set_digest") == current["set_digest"]:
        return None
    return gate.execute(ATTESTATION_OP, "SYSTEM", {"src_dir": src_dir})
