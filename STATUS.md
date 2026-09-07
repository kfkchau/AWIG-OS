# Status of AWIG OS

A plain account of what runs, what is built, what is designed, and the one cap
that matters. Pre-alpha: the design is deep, the runnable surface is a seed.

## What runs, today, in this repository

The tree under [`code/`](./code/) is a stamped, checked rendering of the engine.
With stock Python 3 and no dependencies:

    cd code
    python3 seed_demo.py      # one rule, one act allowed, one act refused, one kill-and-replay
    python3 check.py          # eight readings of the machinery; check 6 is the control that must say no

On the machine this release was cut on, the estate host, Linux, Python 3.12.3,
the battery passes **8 of 8** and both scripts exit 0. On the owner's laptop,
Debian under WSL 2, Python 3.13.5: 8 of 8, demo identical, both exit 0
(8 September 2026). A count of your own is the second opinion the scripts are
built to give: `echo $?` after either one.

## What is built

The engine renders from a private source estate at founding **1.39.0**. In shape,
its guarantees have moved from *cannot-do-lawfully* and *cannot-do-quietly* toward
*cannot-do-undetectably*:

- Every act crosses one gate and is recorded citing the rule that allowed or
  refused it; every current state is computed from the record, never stored.
- The record is chained and sealed: an edited byte of meaning breaks the chain at
  a provable point, and replay verifies every link and signature as data.
- A key-bound account can no longer act unsigned; an unkeyed account is byte-for-byte
  unaffected. No dual-mode gate, no flag day.
- Custody is conserved: there is no delete in the vocabulary; the one removal is a
  verified handover that leaves a departure scar.
- Content at rest is sealed per piece to each reader's open key; recovery never
  inverts the truth hierarchy, and auto-recover proceeds only when three independent
  checks agree, halting otherwise.

## What is designed, not yet shipped as code

The full rule engine, the constitutional AI organisation, and the automation splitter
are designed and reference-modelled; they grow from the seed above. Real cryptographic
key material under the whole key family is the next named unit of work.

## The one honest cap

> Every key in this release is a stand-in of the right shape, not real cryptography.
> A reader of the whole record on disk can derive an open key and unseal content.
> Real cryptographic key material under the whole key family is the next unit.
> Protect the disk by other means (full-disk encryption) until it lands.

The other caps, said plainly:

- Pre-alpha, one machine: every performance figure is one caller on one substrate.
- The record can be wrong while every view is right: two concurrent creates once
  produced two rows for one act, and every guard checks record to view, none the other way.
- The rename-and-replay defect is open; git stops at add.
- Containment is not demonstrated adversarially; there is no red-team transcript.
- Root can edit the record file, and the chain makes that evident rather than impossible.

Two riders travel with every figure here. The commit named in `code/RENDER-STAMP.json`
and `code/FREEZE.txt` is a commit in the estate's own repository, which is private, so
treat it as a provenance stamp rather than something you can check; the anchor you can
hold is the public tag `milestone-0-seed`. And the full test ledger does not ship; the
eight-check battery under `code/check.py` does. So any test count stated anywhere names
the machine it was taken on.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
