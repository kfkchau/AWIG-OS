# Releases

What each public marker contains, in plain words. Every figure names the machine it came from.

## `milestone-0-seed`: the seed, 30 August 2026

The first runnable piece, kept as a tag on the last commit that carried the `seed` folder. Two files and Python 3. One rule runs in the common format, one permission runs and leaves a record you can verify, and a stranger can check both. The folder has since been replaced by the fuller `code` folder below. Its history stays under this tag.

## `c7-close`: our own kernel, rulebook version 1.55.0, 20 September 2026

The `code` folder is replaced whole. The previous contents stay under the tag `c5-close`. Campaigns 6, 6a and 7 arrive together. What they added, in plain words:

- **The kernel (campaign 7).** The system boots on its own kernel in a virtual machine with no Linux beneath it; checks its own body, record, constitution and keys before its first act, witnessed by two bodies; pins the kernel and the interpreter in the record and refuses to start on a changed byte; runs the standard Python interpreter unmodified as sealed content; opens a network connection only after its own record grants it. The kernel's source is in `code/src/body`, and a stranger can build and boot the plain kernel with `gcc` and `qemu`. The numbers under Linux and under our kernel, side by side, are on [`STATUS.md`](./STATUS.md).
- **Several machines, each its own record (campaigns 6 and 6a).** Each machine keeps its own record and its own gate; what one sends another arrives as input and is adopted under the receiver's own rules; the stage of governance each machine holds is derived from its rules; the tree of views and the loop a rule change climbs through it.
- **The first tools of the side-by-side comparison** (`code/tools/sidebyside`), begun the day after the campaign closed: they run the same acts on Linux and on our kernel and compare the two records. The comparison itself is later work and `STATUS.md` says so.
- **The four repairs from the third outside review**, listed on `STATUS.md`, with the tests that prove them. The shipped runner now recomputes the fingerprints of what it runs against and refuses an empty run.

**Checked how.** On a Windows laptop under Debian in WSL 2 (Python 3.13.5), clean copy, nothing of ours installed, 20 September 2026: sixteen checks of sixteen; the shipped suite 170 test files run, 170 passed, 0 failed, 67 skipped; the same with the real locks installed (PyNaCl 1.6.2). The build team's leak scan and sixteen checks agree on its own render of the same commit. The plain kernel was built there with gcc 14.2.0 and booted in QEMU 10.0.13: 120 lines on the serial line, every check PASS, the last line `BODY-HALT`. Tests that need the build team's virtual machine skip here in three named classes, each skip saying what it needs.

**What it does not claim.** The kernel runs in a virtual machine only and is narrow by design. It is slower than Linux and the page prints by how much. The record that matters still runs on Linux until a side-by-side stretch agrees whole. Every program born on the record with its rules sealed is campaign 8 and is not built. No bytes of anyone else's code are in this folder; the full kernel build takes two inputs from your own machine, named in [`THIRD-PARTY.md`](./THIRD-PARTY.md).

## `c5-close`: the engine after campaign 5, rulebook version 1.50.0, 13 September 2026 (3.1 the same day: one chance-prone test skipped, named in its skip row)

The `code` folder is replaced whole. The previous contents stay under the tag `c4-close`. What campaign 5 added, in plain words:

- Real cryptography, off until you install one library. With it installed, signatures, key wrapping and sealed content are real, and the program seals its own signing key at startup. Without it, the keys are stand-ins of the right shape and any act that needs a real signature is refused rather than faked.
- Network actions are governed. Opening, binding, listening, connecting, accepting and closing a socket are each a recorded decision citing a rule; the live socket table is computed from those records.
- The border is governed. Something arriving from outside is a draft the rulebook decides before it has any effect; the reply seals exactly what was shown; the sender's identity is established at the door.
- One row, one receipt, two bodies. A record sent from one machine is received by another as input, and the receiver writes its own receipt in its own record.
- The firewall is rules in the record; every filtering decision is a recorded act.
- The repairs from two rounds of outside review, listed on [`STATUS.md`](./STATUS.md), with the tests that prove them.
- The test suite and the release tools ship beside the code for the first time. `run_public_suite.py` runs 94 test files on a stock machine and skips 65, each naming what it would need.

**Checked how.** Sixteen checks in `code/check.py` and the shipped suite (94 run, 94 passed, 0 failed, 65 skipped) on the Linux machine this release was cut on (Python 3.12.3). A more serious run on Windows under Debian in WSL 2 (Python 3.13.5) found a disk-batching measurement that platform cannot make, which now skips there, and one timing test that fails under load and passes alone; neither breaks a promise of the code, and the timing test is addressed in the next release. The commits in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belong to the private development repository and cannot be looked up from here. Treat them as stamps. The tag above is the anchor you can check.

**What it does not claim.** The locks are real only when installed, an administrator can still read the machine's memory and the disk, and the box for the AI team is empty. The full list is in [`STATUS.md`](./STATUS.md). In the build team's exact words on the keys:

> Real cryptography is in this code and is off until you turn it on. Install the one vetted library it names and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did, with keys that are stand-ins of the right shape; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.

## `c4-close`: the engine after campaign 4, rulebook version 1.39.0, 8 September 2026

Kept under the tag `c4-close`. What campaign 4 added, in plain words:

- The written record is tamper-evident. Change one character of the history and the system can say where.
- Accounts can hold keys. An account with a key cannot act without signing. Accounts without keys work exactly as before.
- The program checks its own code at startup and writes the fingerprint into the record.
- Nothing can be deleted. The only way anything leaves is a formal handover to another party, who signs a receipt.
- Stored content is locked so that only its intended readers can open it.
- If the record is damaged, the system repairs it back to the last point that three independent checks agree on, or stops and asks. Damage is located precisely, not by throwing history away.

**Checked how.** The eight checks in `code/check.py` pass on the Linux machine this release was cut on (Python 3.12.3) and on a Windows laptop running Debian under WSL 2 (Python 3.13.5). The commit number in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belongs to the private development repository and cannot be looked up from here. Treat it as a stamp. The tag above is the anchor you can check.

**What it does not claim.** The locks are not real yet, nobody has attacked it, and an administrator can still edit the file. The full list is in [`STATUS.md`](./STATUS.md). In the build team's exact words on the keys:

> Every key in this release is a stand-in of the right shape, not real cryptography. A reader of the whole record on disk can derive an open key and unseal content. Real cryptographic key material under the whole key family is the next unit. Protect the disk by other means (full-disk encryption) until it lands.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
