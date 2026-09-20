<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: campaign-paper · Vocabulary is OS-architecture (installer image, boot medium, kernel, driver bundle, enclosure) as in the seL4/Qubes/distribution literature. NON-GOAL: no offensive capability — this papers how a person installs gov-os as the core of a real machine; it deletes nothing without the owner's present hand. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CAMPAIGN-PAPER status=DRAFT verified=2026-09-19 -->

# design/61 — CAMPAIGN 9: THE INSTALLER (one file, a real machine, gov-os as the core)

    CAMPAIGN: C9 — THE INSTALLER
    STATUS: DRAFT — ruled into existence by the owner first-party (board :4597, the night of 2026-09-18); this paper cut at C7's digest as that ruling ordered. Runs in the BODY LANE, PARALLEL to C8 (the Python lane); neither waits on the other.
    VERSION: v0.1
    LAST-AS-BUILT-SYNC: 2026-09-19 (birth; nothing built)

## 2. OUTCOME — in the owner's language

A person with an ordinary machine downloads ONE file, writes it to a USB stick, and boots the machine from it. What comes up is gov-os: our kernel is the core of the machine, the record is the truth, and the drivers and devices work because a stripped Linux — kept ONLY as a driver worker, locked in a box our kernel controls — serves them. The first thing this campaign ships does not install anything: it PROBES — it boots from the stick, looks at the machine, writes what it found as rows, and touches no disk. Installing onto the disk is a later row, done with the owner present. Campaign 7 proved the system cannot lie about what it runs; this campaign makes it something a person can run.

## 3. TARGET BEHAVIORS — numbered, testable

    B1. ONE FILE. The installer is a single bootable image; writing it to a USB stick with one command makes the stick bootable. Check: the image builds reproducibly; a byte-identical rebuild.
    B2. THE PROBE BOOT DELETES NOTHING. Booting the stick on a real machine brings up gov-os, probes the devices, writes discovery rows to the STICK's own record, and powers off — the machine's disks untouched. Check: disk hashes before and after the probe boot are identical; the stick's record holds the discovery rows.
    B3. GOV-OS IS THE CORE; LINUX IS A BOXED WORKER. Our kernel boots first and owns the machine; the sealed Linux bundle (its kernel and drivers kept, everything else cut) runs ONLY inside an enclosure our kernel controls, serving device work as declared services — it never installs itself, never owns the boot path, and cannot write outside its box. Check: the bundle's crossing set is declared and censused; a planted out-of-set effect is refused and recorded (the C7 enclosed-worker form at machine scale).
    B4. EVERY DEVICE IS ROWS. What the probe finds — disks, network parts, video, input — lands as discovery rows carrying the identity the worker exports, the C7 P7b form. Check: rows read back; a phantom-present plant reds.
    B5. THE INSTALL IS AN ACT WITH THE OWNER PRESENT. The copier writes gov-os onto a machine disk only as an explicit act, owner at the keyboard, target disk named by row first; it is refused otherwise. Check: the copier without the named-target row refuses; with it, the installed disk boots to B3's state.
    B6. THE DESKTOP IS LATER AND ORDINARY. Any graphical surface arrives as ordinary installed programs under gov-os rules — never as part of the installer's core promise. Check: none in this campaign's fence; a paper row in C10 or later.

## 4. INVARIANTS — what must never break

    I1. The C7 seam law carries: one declared crossing place per worker; nothing above it names the performer. Checked by the census form C7 P2 built.
    I2. L18/L19/L21 carry whole: enclosure faults are enforcement; plants must be real; no general writable surface is widened.
    I3. The record and content store remain the only two stored truths on the installed machine, as in the guest.
    I4. NOTHING is deleted or overwritten on any machine except by B5's explicit act. The probe lane is read-only toward the machine's disks — checked by B2's hash comparison.
    I5. The bundle is FROZEN cargo: carried bytes, never a run installer. Ubuntu-class tooling never executes; the bundle cannot overwrite us (the owner's own fear, answered on the record :4597).

## 5. SETTLED LAW — rulings register

    [L1] The installer direction is committed: one file; gov-os kernel + founding + system + sealed Linux driver bundle + copier; probe-first on the owner's real machine; body lane, parallel to C8 — source: owner first-party, board :4597, 2026-09-18.
    [L2] The bundle keeps the Linux kernel and drivers as a BOXED worker under our kernel (the Qubes/Xen shape at the machine, the Alpine size ambition); everything else is cut — source: the same exchange, on the record.
    [L3] The size is an ESTIMATE — half a gigabyte, marked estimate until the first bundle is cut — source: archi estimate accepted by the owner 2026-09-18; never cite it as measured.
    [L4] The first row on real hardware is the PROBE BOOT from a USB stick on the owner's machine, deleting nothing; installing to a disk is a separate later act with the owner present — source: owner exchange of :4597; C7's Q-register (hardware acts are the owner's).
    [L5] The production switch of the real record onto any body remains governed by the side-by-side ruling (:4487): decided by the owner only when the stretch agrees whole. An installed machine changes nothing about that.

## 6. MUST-NOT-TOUCH

    The guest estate (src/, the record, the founding pack) except where a plan's fence names it; every C1-C7 pin; the owner's one-way doors (key ceremony, hardware purchase, public word, the production switch, Q2/Q3); the autosync timer; the disk-hygiene law; reference/ and every archive folder; ANY disk of ANY real machine outside B5's explicit act.

## 7. PLAN LIST — the campaign's shape

    P1 | B1+B2 | the probe image: build the one-file bootable image (our kernel + a first cut of the bundle + the stick record), boot it in the guest's nested qemu first | YELLOW | 1 | PENDING
    P2 | B2 | the probe boot on the OWNER'S REAL MACHINE from a USB stick — his hands, his machine, nothing deleted; the discovery rows read back | RED (real hardware, owner's act) | 2 | PENDING (owner-present)
    P3 | B3 | the bundle as a boxed worker: the sealed Linux serves device work through a declared crossing set under our kernel's enclosure | YELLOW | 3 | PENDING
    P4 | B4 | every probed device as rows; the phantom plant | YELLOW | 4 | PENDING
    P5 | B5 | the copier: install to a named disk as an owner-present act; refuse otherwise | RED at the write, YELLOW in the guest | 5 | PENDING
    P6 | B1 | reproducible build + the size measured (retiring the estimate) | GREEN | 6 | PENDING

## 8. AS-BUILT LOG

    2026-09-19 — paper cut at C7's digest per :4597. Nothing built.

## 9. OPEN QUESTIONS / RISKS

    Q1. The bundle's cut list (what of Linux survives into the box) — measured by P1's first cut, not guessed.
    Q2. Secure-boot/firmware handshake on the owner's real machine — unknown until P2's probe; the probe records what it finds and refuses nothing it cannot.
    Q3. Whether the stick's record and the guest estate's record federate or stay separate until install — a C8 swarm-law question (design/56 B16) and ruled there, not here.
    Q4. OWNER-DECISION FLAG: P2 runs only at his hands, on his machine, at his word (RED).
