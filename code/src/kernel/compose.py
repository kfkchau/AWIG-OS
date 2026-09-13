# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""Compose the full governed kernel: the foundation (record + gate + views) + the
content-addressed blob store + all five governed subsystem cores. This is the whole
machine (design 02 §10 thin slice, at full-subsystem scale) — one record, one gate,
every subsystem's current state a derived view, the entire thing reconstructible from
the record alone. Core kernel only; drivers out (DECISIONS D8).
"""

from pathlib import Path

from kernel.boot import build_kernel, genesis  # noqa: F401  (genesis re-exported)
from kernel.blobs import BlobStore
from kernel.vault import VaultStore
# All five cores now boot from genesis as op definitions (EP-03/04/05); the subsystems hold
# only their views. The blob store is wired INTO build_kernel so the content-addressed ops
# (FILE-WRITE, COMMS-SEND) register.
from subsystems.files import FilesView
from subsystems.devices import DevicesView
from subsystems.comms import CommsView
from subsystems.memory import MemoryView
from subsystems.scheduling import SchedulingView


def build_full_kernel(record_path, blob_dir, vault_dir=None):
    """Build and wire the whole governed kernel. Returns (store, gate, views, blobs,
    subsystem_views) where subsystem_views maps name -> its View. The secrets vault
    (EP-19; design/31 J8) is a SEPARATE write-once store from the blob store — secret
    values never share a home with ordinary content, and the vault has no read path.
    `vault_dir` defaults to a `vault/` sibling of the blob dir."""
    blobs = BlobStore(blob_dir)
    # R2 (EP-MAINT-OUTSIDE-4): THE FULL COMPOSITION ENFORCES A SINGLE WRITER. `EventStore(lock=False)`
    # is the bare default (a disposable read-only test world needs no pidfile); the WHOLE governed
    # kernel, which opens the real record to write it, takes the writer lock so two processes cannot
    # both mint over one record (the observed seq-166 collision). A second process on the same record
    # is refused the writer role at build (store._acquire_lock), no seq collision.
    store, gate, views = build_kernel(record_path, blobs=blobs, lock=True)  # blobs -> content ops register; single writer
    # The secrets vault (EP-19; design/31 J8). Wired HERE, at full compose (like the blob store is
    # threaded into build_kernel): set gate.vault, then re-run the replay so the secret ops
    # (SEAL-SECRET / VERIFY-SECRET), skipped during the bare replay for lack of a vault, register now.
    # replay is idempotent (already-registered ops are skipped), so nothing else re-registers.
    from kernel.opdefs import replay_op_definitions
    gate.vault = VaultStore(vault_dir if vault_dir is not None else str(Path(blob_dir).parent / "vault"))
    replay_op_definitions(gate, store, views)
    # EP-08: the standing push worker (design 28 §6). Attached to `views` rather than returned, so the
    # 5-tuple signature (used across the suite) is unchanged. It delivers to in-memory queues on append
    # (governance rate) and APPENDS NOTHING — views.queues() is the derivation it accelerates.
    from kernel.push import StandingPush
    views.push = StandingPush(store, views)
    # W6 (finding "protection not wired"; design 28 §7): the protection layer ships ON by DEFAULT — not
    # a flag, not a test fixture. Instantiating Protection attaches the two mutually-blind audit streams
    # (on-append mirrors), and register_protection_ops binds the sight-binds-action ops (GRANT-READ /
    # CONSUME). Attached to `views` (like push) so the 5-tuple signature the suite unpacks is unchanged.
    # Genesis has already run inside build_kernel above, so no founding record is retroactively mirrored;
    # the streams cover governance acts from here on, and the record file replays them identically.
    from kernel.protection import Protection, register_protection_ops
    protection = Protection(store, gate, views)
    register_protection_ops(gate, store, protection)
    views.protection = protection
    subsystem_views = {
        "files": FilesView(store, blobs),
        "devices": DevicesView(store),
        "comms": CommsView(store),
        "memory": MemoryView(store),
        "scheduling": SchedulingView(store),
    }
    # EP-40 (:2769 R1/R2/item 4; COMPLETE-ATTEST-OP flip — owner's create-word board :2847, scope
    # confirmed COMPOSE-FLIP-ONLY at :2866): engine attestation rides HERE, at the compose layer,
    # ABOVE the founding boot — never in build_kernel, whose founding roundtrip must stay pack-exact.
    # The append is a governed SYSTEM op THROUGH THE GATE (attestation.attest_boot -> gate.execute),
    # never a raw store._append. The op is OWNER-GATED founding-integrity vocabulary and the owner's
    # word has LANDED, so production now registers it and attests live at boot. This moves NO
    # founding: register_attestation is a CODE registration (its handler computes file digests, which
    # the data-born check vocabulary cannot express — the protection-op shape), so founding-pack.json
    # stays byte-untouched and build_kernel above is still pack-exact and never attests
    # (test_ep14; test_ep40.TestProductionAttests.test_build_kernel_the_founding_path_never_attests).
    from kernel.attestation import attest_boot, register_attestation
    register_attestation(gate)
    attest_boot(store, gate)
    # EP-41B (design/46 members 3-4; board :2972 archi): the HANDOVER ceremony rides HERE, at the
    # compose layer, ABOVE the founding boot — never in build_kernel, whose founding roundtrip must
    # stay pack-exact. register_ceremony self-gates on gate.blobs (wired above), so it registers the
    # HANDOVER-CUSTODY op only at full compose; build_kernel (no blobs) stays inert and never carries
    # it. This moves NO founding: register_ceremony is a CODE registration EXACTLY like
    # register_attestation above (the op blob-homes its content by hash and the departure record cites
    # only the hash — the protection-op shape the data-born vocabulary cannot express), so
    # founding-pack.json stays byte-untouched, carries no handover-family member, and the founding path
    # is still pack-exact (test_ep41b.TestEP41BCeremonyLiveInProduction). Registration only — nothing
    # hands over at boot, so no handover law is cited here.
    from kernel.erasure import register_ceremony
    register_ceremony(gate, views)
    from kernel.erasure import register_recover; register_recover(gate, views)  # flip B: recover op live at full compose (register_ceremony shape; moves no founding)
    # EP-47C (design/51 N10): WIRE THE REAL COUNTERSIGN INTO THE STORE'S APPEND PATH. The store calls this
    # hook while composing every record (store._append_one); it is `append_countersign` above — a REAL mark
    # once a system key is bound, and NOTHING (byte-identical) while unbound. Attached HERE, at full
    # compose, AFTER the pack-exact founding boot (build_kernel) and the compose-layer boot records
    # (attest_boot / register_ceremony / register_recover), so those never route through it — and would be
    # unbound anyway. This moves NO founding: it CALLS the EP-47B functions, no pack edit / op / version
    # bump. Production build_full_kernel binds NO system key (the owner's real ceremony is his own act), so
    # production records stay byte-identical; a TEST/DEMO world that runs the ceremony (seal_system_signer)
    # grows real-countersigned records from its first governed append onward, or is refused once bound
    # where the library is absent — never a silent modelled mark (theorem 3).
    store._append_countersign = lambda record: append_countersign(store, views, record)
    # Boot attestation is SEALED through `boot_attestation_seal` / `system_attestation_seal` (A4), DERIVED
    # on demand (like `bound_key`), NEVER forced here: invoking it at build would make compose itself
    # REFUSE when rebuilding a bound-but-un-ceremonied world (a restart drops the in-memory signer) — the
    # boot path seizing, which the store must never do (stop-f). So the seal is a compose-layer function
    # callers derive after the ceremony; build stays reconstructible for every world. (Persisting the seal
    # into the attestation record would touch attestation.py, out of this EP's fence — named at the close.)
    return store, gate, views, blobs, subsystem_views


# ---- EP-47B: THE SYSTEM SIGNER CEREMONY, AT THE COMPOSE LAYER (design/51 N10; archi :3302) --------
# The compose-layer half of the system-signer ceremony (Option A — the recorded ceremony at boot).
# It rides HERE, ABOVE the pack-exact founding boot (build_kernel), exactly as attest_boot and
# register_ceremony do: the BIND is an APPEND and build_kernel must never grow a boot record. This
# is NOT a founding move — the KEY-BIND LAW (founding step 05i-key-laws) and op:key-bind (08e2-key-
# ops) ALREADY exist, so the system public half binds via the EXISTING op as a boot-time record:
# NO pack edit, NO version bump, NO bump-attestation. Production build_full_kernel above does NOT
# call this — it stays byte-identical and binds no system key (the owner's real ceremony is his own
# act); a TEST/DEMO world invokes it explicitly with a MARKED-TEST seed (never the owner's seed).


class CeremonyNotRun(RuntimeError):
    """A system countersignature / attestation seal was requested AFTER a system KEY-LAW-BIND row
    exists, but the boot ceremony that seals the system signing seed has NOT run this boot — the
    seed is in memory only (signer.py) and a restart drops it. REFUSED citing the missing ceremony,
    NEVER a silent fall-back to the modelled path (PRECISION 2 / RW-SILENT-MODELLED-AFTER-BIND): once
    the system key is bound, countersign and attestation REQUIRE the signer, so after the system key
    is bound, a restart needs the ceremony before the record can grow."""


CEREMONY_ROW = "system-signer-ceremony"   # the WRITE-ACTIVITY object naming the ceremony row


def seal_system_signer(store, gate, views, contributed=None, *, at=None):
    """THE BOOT CEREMONY (Option A; archi :3302, with two architect precisions of 2026-09-08). Collect
    the seed — the OS cryptographic source ALWAYS mixed by hash with any HUMAN contribution (mouse/key
    timing), measured and REFUSED below the minimum-entropy floor; a HEADLESS boot runs the OS-only
    path. Seal the mixed seed into the signer (in memory only), RECORD THE CEREMONY ROW (a WRITE-
    ACTIVITY: THAT it happened, WHEN via record_time, HOW MANY events, the HASH COMMITMENT — never the
    raw samples — and whether it took the headless/OS-only path), bind the PUBLIC half via the EXISTING
    op:key-bind under the EXISTING KEY-LAW-BIND (a boot-time record — NOT a founding move), and attach
    the IN-MEMORY signer so keys.countersign / attestation_seal produce REAL signatures where the vetted
    library is present (refused, never faked, when absent — N10). TEST and DEMO worlds run this SAME
    scripted ceremony with a MARKED-TEST value; the seed lives in memory only, so a restart drops it and
    this ceremony must re-run. Returns the signer (attached at views.signer with system_key_hash /
    system_public_key). A refused seed (below the floor) raises BEFORE any record is appended."""
    from kernel.boot import seed_system_signer
    from kernel import keys
    signer, custody, public, descriptor = seed_system_signer(contributed)   # raises below the floor — no record yet
    # THE CEREMONY ROW — an existing WRITE-ACTIVITY record (SYSTEM): that it happened (this row), when
    # (its record_time), how many events, the hash COMMITMENT, and the source path. NEVER the raw
    # samples (only the count + the commitment reach the record).
    gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": CEREMONY_ROW, "data": {
        "ceremony": "system-signer-seed",
        "source": descriptor["source"],           # "headless-os-only" | "human-mixed"
        "event_count": descriptor["event_count"],
        "entropy_bits": descriptor["entropy_bits"],
        "commitment": custody,                     # sha256:<hex> — a one-way commitment to the sealed seed
    }})
    params = {keys.ACCOUNT: keys.SYSTEM_KEY_NAME, keys.PUBLIC_KEY: public}
    if at is not None:
        params["at"] = at
    gate.execute(keys.KEY_BIND, "SYSTEM", params)     # the system public half bound as law (boot-time record)
    views.signer = signer
    views.system_key_hash = custody
    views.system_public_key = public
    return signer


def system_key_bound(store):
    """Does a system KEY-LAW-BIND row exist — is the system signing key's public half bound? A live
    supersession fold over the record (kernel.keys), never a stored flag; None before the ceremony,
    the bound public half after it. This is the gate PRECISION 2 reads: after it is true, the signer
    is REQUIRED."""
    from kernel import keys
    return keys.bound_key(store, keys.SYSTEM_KEY_NAME) is not None


def system_countersign(store, views, record):
    """The store's countersignature over a record, ROUTED to the boot-seeded signer (real where the
    library is present; refused, never faked, when absent — N10). AFTER a system KEY-LAW-BIND exists
    the signer is REQUIRED: a boot without the ceremony (no in-memory signer) REFUSES citing the
    missing ceremony rather than silently producing modelled material (PRECISION 2, RW-SILENT-
    MODELLED-AFTER-BIND). BEFORE any system bind it is the modelled path exactly as today."""
    from kernel import keys
    signer = getattr(views, "signer", None)
    if signer is None and system_key_bound(store):
        raise CeremonyNotRun(
            "the system key is bound (a KEY-LAW-BIND row exists) but the boot ceremony has not run "
            "this boot — the in-memory system signing seed is absent; countersign REQUIRES the signer "
            "and REFUSES rather than fall back to a modelled mark (after the system key is bound, a "
            "restart needs the ceremony before the record can grow)")
    return keys.countersign(record, getattr(views, "system_key_hash", None), signer)


def system_attestation_seal(store, views, attested):
    """The engine attestation seal, ROUTED to the boot-seeded signer (real where the library is
    present; refused, never faked, when absent — N10). AFTER a system KEY-LAW-BIND exists the signer
    is REQUIRED and its absence REFUSES citing the missing ceremony (PRECISION 2). BEFORE any system
    bind, with no signer, there is no real seal to add — the unsealed attestation (its set-digest
    integrity mark) stands as today, so None is returned rather than a fake seal."""
    from kernel import attestation
    signer = getattr(views, "signer", None)
    if signer is None:
        if system_key_bound(store):
            raise CeremonyNotRun(
                "the system key is bound (a KEY-LAW-BIND row exists) but the boot ceremony has not "
                "run this boot — the in-memory system signing seed is absent; the attestation seal "
                "REQUIRES the signer and REFUSES rather than fake a seal (after the system key is "
                "bound, a restart needs the ceremony before the record can grow)")
        return None
    return attestation.attestation_seal(attested, signer, getattr(views, "system_key_hash", None))


# ---- EP-47C: THE REAL COUNTERSIGN REACHES THE RECORD, AT THE APPEND PATH (design/51 N10) -----------
# The store's append path calls the hook below while composing every record; build_full_kernel attaches
# it (store._append_countersign). It is NOT a founding move — it CALLS the EP-47B functions above from
# the append path; no pack edit, no op/law/kind, no version bump.


def _is_ceremony_bootstrap(record):
    """The two records the boot ceremony (`seal_system_signer`) appends to ESTABLISH the system signer:
    its ceremony row (a WRITE-ACTIVITY over CEREMONY_ROW) and the system KEY-LAW-BIND itself. They are
    EXEMPT from the append-path countersign — a key-bind cannot be countersigned by the very key it
    establishes (a bootstrap chicken-and-egg), and on a RE-CEREMONY (an already-bound world whose
    in-memory signer was dropped by a restart) they are appended BEFORE the signer is re-attached, so
    requiring the signer on them would make the ceremony unable to re-run (it did — EP-47B's re-ceremony
    reddened until this exemption). Every OTHER governed record, once bound, is countersigned or refused;
    this exemption is exactly the two bootstrap rows and nothing wider."""
    from kernel import keys
    payload = record.get("payload") or {}
    if record.get("action") == keys.KEY_BIND and payload.get(keys.ACCOUNT) == keys.SYSTEM_KEY_NAME:
        return True
    return record.get("action") == "WRITE-ACTIVITY" and record.get("object") == CEREMONY_ROW


def append_countersign(store, views, record):
    """THE APPEND-PATH HOOK (EP-47C): the store's real countersignature over a record it is appending,
    or NOTHING while the world carries no bound system key. It is `system_countersign` GATED on the bound
    state so the record NEVER carries a modelled mark. UNBOUND (no system KEY-LAW-BIND) -> None, and the
    store adds no field, so the record is byte-identical to the pre-EP-47C ledger (A3). The ceremony's own
    bootstrap rows (`_is_ceremony_bootstrap`) are also None — they establish the signer and cannot require
    it. Otherwise BOUND -> `system_countersign`: REAL where the vetted library is present (A1), and
    REFUSED (CeremonyNotRun / crypto.LibraryAbsent) where the key is bound but the ceremony has not run
    this boot or the library is absent (A2 — the after-bind no-fallback, theorem 3 / N10) — never a
    modelled mark once bound. Gating on `system_key_bound` (which flips at the bind row's COMMIT, so it is
    False during the FIRST bind row's own append) plus the bootstrap exemption is what begins the REAL
    mark at the first governed content append AFTER the ceremony."""
    if not system_key_bound(store):
        return None
    if _is_ceremony_bootstrap(record):
        return None
    return system_countersign(store, views, record)


def boot_attestation_seal(store, views, src_dir=None):
    """BOOT ATTESTATION, ROUTED THROUGH THE SEAL (EP-47C; design/37 Q3; A4): the real Ed25519 seal over
    the running engine's attested SET-DIGEST, DERIVED live (never stored in a record — the estate's
    derive-never-store posture, as `bound_key` is) and verifiable under the bound public half. UNBOUND ->
    None (a world with no system key keeps today's unsealed attestation; its set-digest integrity mark
    stands, byte-identical). BOUND -> `system_attestation_seal`: REAL where the library is present and
    REFUSED where the key is bound but the ceremony has not run this boot or the library is absent (N10).
    The attested set is walked ONLY when bound, so an unbound boot pays nothing."""
    if not system_key_bound(store):
        return None
    from kernel.attestation import attested_set
    return system_attestation_seal(store, views, attested_set(src_dir))
