# Releases

A short, honest log of what each published anchor contains. Every figure names where it
was taken; the full private test ledger does not ship, the eight-check battery does.

## `milestone-0-seed`: the seed

The first runnable milestone, preserved as a tag on the last commit that carried the
`seed/` folder. One rule executes in the common format; one permission runs and leaves a
verifiable trace; a stranger can independently verify both. Two files, stock Python 3.

This tag is the public anchor for milestone 0. The folder it named has since been replaced
in the working tree by the fuller rendering under `code/` (below); its history is kept
under this tag.

## The C4 rendering: `code/` at founding 1.39.0

The tree under [`code/`](./code/) is a stamped, checked rendering of the engine as it stands
after campaign 4. What campaign 4 built, in shape: guarantees moved from *cannot-do-lawfully*
and *cannot-do-quietly* toward *cannot-do-undetectably*.

- Every post-seal record chains to its predecessor's canonical hash; an edited byte of
  meaning breaks the chain at a provable point.
- A key-bound account can no longer act unsigned; an unkeyed account is byte-for-byte
  unaffected. No flag day.
- The engine attests its own artifact set at boot; the two audit streams gain separate keys.
- Custody is conserved: no delete in the vocabulary; the one removal is a verified handover
  leaving a departure scar.
- Content at rest is sealed per piece to each reader's open key.
- The recovery family: recover never to wrongness, never truncating; checkpoints with an
  O(1) head check and Merkle-localized damage; a mutual-receipt buddy; auto-recover under a
  triple check that proceeds only on all three and halts otherwise.

Verification anchor: the shipped battery `code/check.py` passed 8 of 8 on the estate host
(Linux, Python 3.12.3) at the cut of this release. Provenance: `code/RENDER-STAMP.json` and
`code/FREEZE.txt` name a commit in the private source estate. Treat it as a stamp, not a
thing you can check from here; this repository's tag is the anchor you can hold.

**Honest cap.** Every key in this release is a stand-in of the right shape, not real
cryptography. A reader of the whole record on disk can derive an open key and unseal content.
Real cryptographic key material under the whole key family is the next unit.
Protect the disk by other means (full-disk encryption) until it lands.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
