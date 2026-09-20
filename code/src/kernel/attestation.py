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

from bridge.host_seam import host   # C7 P2 — the member body-read + the S-plane walk routed through the seam
from .canonical import canonical_hash
from . import crypto  # the ONE vetted-library boundary — the attestation seal is real when present

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
    # grow-only add under C7 P3b-1 — THE BODY: MEMORY, the FIRST MERGED body code (design/54 §7
    # P3b-1; §9 mechanism 1, archi :4009): ONE ATTESTED LIST, no second plane. Every file the body
    # is built from — the hand-written C (read whole, no opaque code in the signed base, I3), the
    # asm entry, the linker script, the generated rows-digest header, the derive-from-the-rows
    # generator .py, and the guest build script — joins the attested set BY NAME, under the SAME
    # digest and the SAME grow-only discipline. The C source is not a .py, so the law guard's walk
    # (law_guard_surface / test_law_out_of_code._src_py_outside_founding) is extended to catch an
    # UNRECORDED file under src/body/ too — the property "nothing under src/ outside the attested
    # list" now holds for the body's files. The count-pins (test_ep40:259/:260, test_ep46:481,
    # test_keymat:330, test_c7_p4_wake:384, test_c7_p6_genesis_pair:351) move 57 -> 68 by name (the
    # 11 body files). The built .elf is NEVER a member (§9 mechanism 3 — the signed base is source).
    #
    # grow-only add under C7 P3b-2 — THE BODY: THE DISK AND THE RECORD ACTS (design/54 §7 P3b-2;
    # archi :4019). The body's own disk C — a polled ATA/PIO block driver (ata.c), the bespoke
    # append-only filesystem the record maps onto (bodyfs.c), the five-act self-check (diskcheck.c),
    # their shared header (disk.h) — plus the seam-routed disk-image build tool (mkdisk.py) join the
    # SAME one attested list. The walk-guard (law_guard_surface) already covers src/body's C/.h/.S/
    # build kinds, so an unrecorded body file reds either way; these are recorded here BY NAME. The
    # count-pins move 68 -> 73 (the 5 new files). Neither the built .elf nor the formatted disk image
    # is ever a member (§9 mechanism 3 — the signed base is source, not a built kernel or a disk).
    #
    # grow-only add under C7 P3b-3 — THE BODY: CLOCK, INTERRUPTS AND ENTROPY (design/54 §7 P3b-3;
    # archi :4049). The body's own interrupt + clock + entropy C — a flat GDT + a 256-gate IDT (idt.c),
    # the exception/IRQ stubs (isr.S), the two clock acts (clock.c: the CMOS wall clock + the rdtsc
    # monotonic window), the seeded ChaCha20 CSPRNG for the entropy act (entropy.c), their shared header
    # (clock.h), and the interrupt/clock/entropy self-check (clkcheck.c) join the SAME one attested
    # list. The walk-guard (law_guard_surface) already covers src/body's C/.h/.S/build kinds, so an
    # unrecorded body file reds either way; these are recorded here BY NAME. The count-pins move 73 -> 79
    # (the 6 new files: clkcheck.c/clock.c/clock.h/entropy.c/idt.c/isr.S). The built .elf is never a
    # member (§9 mechanism 3). No new act (recording-clock, commit-window and entropy all pre-exist),
    # NO founding — the pack is byte-unchanged.
    #
    # grow-only add under C7 P3b-4a — THE WORKER'S ENCLOSURE (design/54 §7 P3b-4a; §5 L18; archi :4085).
    # The body's own enclosure C — user privilege (a TSS + user segments + the return into ring 3) and the
    # SYSCALL/SYSRET crossing (the driver enclosure.c + the entry stub / recovery / incbin enclosure.S), the
    # ELF64 loader of a sealed image (enclosure.c), the request→row crossing trail and the out-of-set native
    # refusal (enclosure.c), the sealed-image digest folded on the metal (sha256.c), and OUR small
    # hand-written test worker (worker.S + its linker script worker.ld) join the SAME one attested list BY
    # NAME. The walk-guard (law_guard_surface) already covers src/body's C/.h/.S/.ld/build kinds, so an
    # unrecorded body file reds either way; these are recorded here by name. The count-pins move 79 -> 85
    # (the 6 new files: enclosure.S/enclosure.c/enclosure.h/sha256.c/worker.S/worker.ld). The built worker
    # IMAGE (worker.elf, incbin'd) is NEVER a member (§9 mechanism 3, like the body .elf); no borrowed
    # worker enters this slice, so the enclosure/act-witnessed list gains no member (I7). No new act (the
    # crossing is HOW acts are requested, not a new act — ACT_KINDS stays twelve), NO founding — the pack
    # is byte-unchanged.
    #
    # grow-only add under C7 P3b-4b — THE FORTY-NINE SERVED (design/54 §7 P3b-4b; §5 L18; precision (a)/(b)
    # of archi :4085). The body's own forty-nine-serve C — the request classifier that routes each measured
    # crossing by PURPOSE to the act machinery / floor / designed-refusal / stub and witnesses it as one
    # UNSIGNED row of the body's serve trail (serve.c), and its shared header (serve.h) — join the SAME one
    # attested list BY NAME. OUR test worker (worker.S) is EXTENDED with the forty-nine run (an edit to an
    # existing member — moves no count); the enclosure driver + phase branch are edits to enclosure.c/.h/
    # kmain.c/build.sh (edits, no count move). The walk-guard (law_guard_surface) already covers src/body's
    # C/.h kinds, so an unrecorded body file reds either way; these are recorded here by name. The count-pins
    # move 85 -> 87 (the 2 new files: serve.c/serve.h); the src/body on-disk count 28 -> 30. The body holds
    # NO key: every serve row is unsigned (sig==0/chain==0), never a row in the estate's signed chain — the
    # per-act signed gate row is the gate's, ABOVE the seam, DEFERRED to P3b-4c (precision a). No new act
    # (ACT_KINDS stays twelve — serving the measured requests realizes existing acts + their floor), NO
    # founding — the pack is byte-unchanged. The built worker IMAGE is never a member (§9 mechanism 3).
    "body/ata.c",
    "body/body.h",
    "body/bodyfs.c",
    "body/boot.S",
    "body/build.sh",
    "body/clkcheck.c",
    "body/clock.c",
    "body/clock.h",
    "body/disk.h",
    "body/diskcheck.c",
    "body/enclosure.S",
    "body/enclosure.c",
    "body/enclosure.h",
    "body/entropy.c",
    "body/gen_rows_digest.py",
    "body/heap.c",
    "body/idt.c",
    "body/isr.S",
    "body/kmain.c",
    "body/linker.ld",
    "body/mkdisk.py",
    # grow-only add under C7 P3b-6a — OUR NIC ON THE WIRE (design/54 §7 P3b-6a; archi :4250). The body's
    # own virtio-net driver — the network device driven by OUR code as its transport (I3, no borrowed
    # code; the borrowed TCP stack is 6b's enclosed worker), plus the ring-0 wire self-check that proves
    # it by an address round trip answered by the guest gateway — joins the SAME one attested list BY
    # NAME. The walk-guard (law_guard_surface) already covers src/body's C kind, so an unrecorded body
    # file reds either way; recorded here by name. The count-pins move 87 -> 88 (the 1 new file net.c);
    # the src/body on-disk count 30 -> 31. NO served shape added (serve.c untouched — the frame-crossing
    # is 6b's, archi :4247); no new act (ACT_KINDS stays twelve, :4248), NO founding — the pack is
    # byte-unchanged. The built .elf/.img is never a member (§9 mechanism 3).
    "body/net.c",
    "body/pmm.c",
    "body/rows_digest.h",
    "body/serial.c",
    "body/serve.c",
    "body/serve.h",
    "body/sha256.c",
    "body/vmm.c",
    "body/worker.S",
    "body/worker.ld",
    "bridge/__init__.py",
    "bridge/auto_recover.py",   # grow-only add under EP-43-AUTO-AMEND-BUILD (archi :3031/:3041,
                                # carried in-fence): a new src/bridge/*.py the law guard greps (the
                                # AUTO-RECOVER orchestrator composing the triple check), so the F4 twin
                                # requires it here — same precedent as bridge/merkle.py (:3045).
    "bridge/checkpoint.py",
    "bridge/custody.py",
    "bridge/fuse_files.py",
    "bridge/host_seam.py",   # grow-only add under C7 P2-SEAM-AS-A-CONTRACT (design/54 §7 P2; §5 fence
                             # "the interface + its ATTESTED_MEMBERS line and count-pin companion"): the
                             # NEW effect-seam performer interface — the closed act set the core asks its
                             # host to perform, declared as one contract with the real + stub performers, a
                             # src/bridge/*.py the law guard greps, so the F4 twin requires it here — same
                             # precedent as bridge/seal.py (EP-46) and bridge/reconstruct.py (P12). The
                             # count-pins (test_ep40/46/keymat) move 54 -> 55 by name.
    "bridge/kernel_port.py",
    "bridge/merkle.py",   # grow-only add under EP-45-BUILD (archi :3031, carried in-fence): a new
                          # src/bridge/*.py the law guard greps (the Merkle over a checkpoint's
                          # tree-state), so the F4 twin requires it here — same precedent as
                          # kernel/keys.py (:2781/:2782) and kernel/erasure.py (:2842).
    "bridge/mount.py",
    "bridge/reconstruct.py",   # grow-only add under P12-CONSTITUTION-SURVIVES-BUILD (C6 P12,
                               # B6/I15; §5 count-pin companion driven at the fence amendment,
                               # mgr :3631): the NEW cross-body reconstruction routine (union the
                               # children's held sealed segments, verify each against the parent
                               # key + chain-verify), a src/bridge/*.py the law guard greps, so the
                               # F4 twin requires it here — same precedent as bridge/auto_recover.py
                               # (:3031/:3041) and bridge/merkle.py (:3045). The count-pins
                               # (test_ep40/46/keymat) move 53 -> 54 by name.
    "bridge/records_fs.py",
    "bridge/replay_snapshot.py",
    "bridge/run_fuse_files.py",
    "bridge/seal.py",   # grow-only add under EP-46-BUILD (archi :3031, carried in-fence): a new
                        # src/bridge/*.py the law guard greps (the content-at-rest sealer, the key
                        # family's read direction), so the F4 twin requires it here — same precedent
                        # as bridge/merkle.py (:3045) and kernel/keys.py (:2781/:2782).
    "hosting/__init__.py",         # grow-only add under C7 P7a — THE INTERPRETER-HOSTING LAYER (design/54
    "hosting/interpreter_host.py",  # §7 P7; §5 fence "the layer module(s) + ... the ATTESTED_MEMBERS rider
                                    # if a NEW attested src module"): the NEW src/hosting/ package — our own
                                    # code, read whole and signed, that supplies CPython's host surface wired
                                    # to the seam (the BORROWED libc/CPython stay OUTSIDE the signed base as
                                    # sealed enclosed workers, design/47 §2 I3). Two src/*.py the law guard
                                    # greps, so the F4 twin requires them here — same precedent as
                                    # bridge/host_seam.py (C7 P2) and bridge/seal.py (EP-46). The count-pins
                                    # (test_ep40:259/:260, test_ep46:481, test_keymat:330, test_c7_p4_wake:380,
                                    # test_c7_p6_genesis_pair:347) move 55 -> 57 by name.
    "kernel/__init__.py",
    "kernel/attestation.py",
    "kernel/authority.py",
    "kernel/blobs.py",
    "kernel/boot.py",
    "kernel/border.py",   # grow-only add under EP-49A-BUILD (THE BORDER: THE DOOR, the campaign-5
                          # crux; §5 fence "+ its ATTESTED_MEMBERS line and count-pin companion",
                          # carried in-fence per the EP-48 precedent): the NEW border stance beside
                          # crossing.py (BORDER-SUBMIT/REPLY/REFUSAL, the crossing-id, the real seal),
                          # a src/kernel/*.py the law guard greps, so the F4 twin requires it here —
                          # same precedent as kernel/crypto.py and kernel/signer.py (KEY-MATERIAL-REAL)
                          # and subsystems/sockets.py (EP-48-BUILD).
    "kernel/canonical.py",
    "kernel/commit.py",
    "kernel/compose.py",
    "kernel/crossing.py",
    "kernel/crypto.py",   # grow-only add under KEY-MATERIAL-REAL (archi :3031/:3041 double-stop lesson, carried in-fence): the NEW one vetted-library boundary, a src/kernel/*.py the law guard greps, so the F4 twin requires it here (same precedent as kernel/keys.py :2781/:2782 and kernel/erasure.py :2842).
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
    "kernel/signer.py",   # grow-only add under KEY-MATERIAL-REAL (archi :3249; the :3031/:3041 double-stop
                          # lesson, the crypto.py companion doubled): the NEW SigningKeyStore that holds the
                          # system signing key BESIDE the byte-frozen vault, a src/kernel/*.py the law guard
                          # greps, so the F4 twin requires it here (same precedent as kernel/crypto.py and
                          # kernel/keys.py :2781/:2782).
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
    "subsystems/filter.py",   # grow-only add under EP-52-BUILD (FIREWALL-IN-THE-RECORD, C5 P7, the
                              # founding mover NET-LAW-FILTER + FILTER-DECISION; §5 fence "+ its
                              # ATTESTED_MEMBERS line and count-pin companion", carried in-fence per the
                              # EP-48 precedent): the NEW which-rule-decided fold beside sockets.py, a
                              # src/subsystems/*.py the law guard greps, so the F4 twin requires it here —
                              # same precedent as subsystems/sockets.py (EP-48-BUILD) and kernel/border.py
                              # (EP-49A-BUILD). The count-pins (test_ep40/46/keymat) move 52 -> 53 by name.
    "subsystems/memory.py",
    "subsystems/scheduling.py",
    "subsystems/sockets.py",   # grow-only add under EP-48-BUILD (SOCKET-GRANTS, the founding mover;
                               # §5 name-and-count sweep + :3255(b) by-name widen, carried in-fence): a
                               # new src/subsystems/*.py the law guard greps (the socket-table fold, the
                               # governed connection view the shadow retires into), so the F4 twin
                               # requires it here — same precedent as subsystems/comms.py and
                               # kernel/crypto.py (KEY-MATERIAL-REAL, :3031/:3041).
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
        with host().open_read_binary(p) as f:
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


def _attestation_message(attested):
    """The message an attestation seal signs over — the attested SET-DIGEST, which already binds
    every member's byte-digest (a change to any member moves it), through the estate's ONE hash form.
    Signer and verifier recompute exactly this, so a tampered member reddens the seal (RW-FORGE)."""
    return canonical_hash({"attestation-set-digest": attested.get("set_digest")})


def attestation_seal(attested, signer, sealed_hash):
    """THE ATTESTATION SEAL, MADE REAL (KEY-MATERIAL-REAL A5; design/37 Q3 + §9's deferred primitive;
    archi :3249). A REAL Ed25519 signature over the attested record's set-digest, produced BY THE
    SIGNER (the SigningKeyStore that holds the system signing key BESIDE the byte-frozen vault) with the
    key sealed under `sealed_hash` (a use, never a read). Returns the tagged signature. The pre-real
    era's integrity mark — the set-digest itself — is untouched and still stands for UNSEALED
    attestations; this ADDS a real signature over it, never replacing the record shape. With the vetted
    library absent `signer.sign` REFUSES citing the absent library — a real seal is never faked
    (RW-DOWNGRADE)."""
    return signer.sign(sealed_hash, _attestation_message(attested))


def verify_attestation_seal(attested, seal, public_key):
    """True iff `seal` is a valid Ed25519 signature over `attested`'s set-digest under `public_key`
    (the system key's published public half). A tampered attested surface — any member changed, so a
    changed set-digest — fails verification (RW-FORGE, the check that can fail). Refuses citing the
    absent library when it is not present (a tagged seal cannot be verified without it, never a
    modelled substitute)."""
    return crypto.verify(public_key, seal, _attestation_message(attested))


def law_guard_surface(src_dir=None):
    """The governed-source surface under src/ — walked here the same way
    `tests/test_law_out_of_code._src_py_outside_founding` walks it. EVERY .py under src/ EXCEPT
    founding/ (the surface T-NO-LAW-IN-CODE greps), PLUS EVERY file under src/body/ regardless of
    extension (C7 P3b-1, §9 mechanism 1): the first merged body's C/.h/.S/build files are not .py,
    but they ARE governed source in the signed base (read whole, no opaque code, I3), so they join
    the same one attested list and the same walk. The F4 twin holds this against `ATTESTED_MEMBERS`;
    on the real tree the two sets are EQUAL by construction (the manifest IS this walk, frozen), so
    the twin's coverage claim is exactly true and a planted extra .py — OR an unrecorded file under
    src/body/ — surfaces immediately."""
    src = src_dir or _SRC
    founding = os.path.join(src, "founding")
    body = os.path.join(src, "body")
    out = []
    for root, _dirs, files in host().walk(src):
        ar = os.path.abspath(root)
        if ar.startswith(os.path.abspath(founding)):
            continue
        if "__pycache__" in ar.split(os.sep):
            continue                      # bytecode cache is not governed source
        under_body = ar.startswith(os.path.abspath(body))
        for name in files:
            if name.endswith(".pyc") or name.endswith(".pyo"):
                continue
            if name.endswith(".py") or under_body:
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
