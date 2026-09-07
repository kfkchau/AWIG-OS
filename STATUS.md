# Where AWIG OS stands

Dated 8 September 2026. If this page and the code disagree, the code is right and this page is out of date.

## What you can try today

Download this repository, open the `code` folder, and run two commands:

    python3 seed_demo.py
    python3 check.py

The program starts from a written rulebook. It performs one action the rulebook allows and writes down what it did and which rule allowed it. It then attempts an action the rulebook forbids, refuses, and writes down the refusal and the reason. Then it deletes everything except that written record, rebuilds itself from the record alone, and shows that the rebuilt copy is identical to the original. The second command runs eight checks on the same machinery; check 6 deliberately breaks one value to prove the checks can fail.

Both commands pass on the Linux machine this release was cut on (Python 3.12.3) and on a Windows laptop running Debian under WSL 2 (Python 3.13.5). Windows on its own refuses with one sentence, because it cannot prove a write has reached the disk, and points you to WSL. Needs Python 3 and nothing else.

## What exists but you cannot try yet

This part lives in the private development repository, not here. It is the same program as the code above, with more of it switched on.

- The written record is tamper-evident. Change one character of the history and the system can say where.
- Accounts can hold keys. An account with a key cannot act without signing.
- The program checks its own code at startup and writes the fingerprint into the record.
- Nothing can be deleted. The only way anything leaves is a formal handover to another party, who signs a receipt.
- Stored content is locked so that only its intended readers can open it.
- If the record is damaged, the system repairs it back to the last point that three independent checks agree on, or stops and asks.
- The rulebook itself can only be changed through the same door as everything else. It has been changed thirty-nine times that way since 24 July 2026.

How we know: the private repository runs 3,677 automated tests in 133 files against this same code, all passing at the review of 7 September 2026. Those tests do not ship. Only the eight checks in `code/check.py` do. Any test count you see from us names the machine it ran on.

## Designed on paper, not built

- Connecting machines over a network.
- Several machines, each keeping its own record.
- The AI team that is meant to work inside it.
- Running on its own hardware without Linux underneath.

## What is not true yet

Read this before trusting it with anything that matters.

- **The locks are not real yet.** The keys are placeholders of the right shape. Anyone who has the disk can read everything on it. Real encryption is the next piece of work. Until then, encrypt the disk yourself. In the build team's exact words, which appear in every file that mentions keys:

> Every key in this release is a stand-in of the right shape, not real cryptography. A reader of the whole record on disk can derive an open key and unseal content. Real cryptographic key material under the whole key family is the next unit. Protect the disk by other means (full-disk encryption) until it lands.

- **One machine, one user.** Every speed figure we publish comes from one computer with one user at a time.
- **The record can be wrong while every view of it is right.** Once, two things created at the same instant produced two entries for one act. The checks run from the record outward, never the other way.
- **A known defect: rename and replay.** Some programs save a file by writing a new one and renaming it over the old. The record then holds two entries for one file and the rebuild merges them. This is why the demo stops at `git add` and never reaches `git commit`.
- **Nobody has attacked it yet.** The list of things to try is written. The attempt has not happened.
- **An administrator can edit the file.** Someone with full rights on the machine can change the record. The chain will show where. It cannot stop them.
- **The two watchdogs have only been tested on one machine.** Two components check each other's saved states. Whether they stay independent on two separate machines is later work.

## What you can and cannot check from here

The commit number in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belongs to the private repository. You cannot look it up from here. Treat it as a stamp. What you can check is the tag `milestone-0-seed` on this repository, and the eight checks.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
