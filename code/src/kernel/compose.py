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
    store, gate, views = build_kernel(record_path, blobs=blobs)  # blobs -> content ops register
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
    return store, gate, views, blobs, subsystem_views
