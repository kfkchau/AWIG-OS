# Releases

What each public marker contains, in plain words. Every figure names the machine it came from.

## `milestone-0-seed`: the seed, 30 August 2026

The first runnable piece, kept as a tag on the last commit that carried the `seed` folder. Two files and Python 3. One rule runs in the common format, one permission runs and leaves a record you can verify, and a stranger can check both. The folder has since been replaced by the fuller `code` folder below. Its history stays under this tag.

## The `code` folder: the engine after campaign 4, rulebook version 1.39.0

What campaign 4 added, in plain words:

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
