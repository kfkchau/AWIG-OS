# Reporting a security problem

Email **kelvin@rootrebuilder.org** with "security" in the subject line. Do not open a public issue. Include the line from `code/FREEZE.txt`, your operating system, and the smallest steps that show the problem.

You will get an acknowledgement within a few days. We agree a disclosure date with you and credit you when it is fixed, unless you ask us not to.

## Read this before you report

AWIG OS is at an early stage. Do not put real secrets behind it yet.

The locks are not real yet. The keys are placeholders of the right shape. Anyone who has the disk can read everything on it. Real encryption is the next piece of work. Until then, encrypt the disk yourself. In the build team's exact words:

> Every key in this release is a stand-in of the right shape, not real cryptography. A reader of the whole record on disk can derive an open key and unseal content. Real cryptographic key material under the whole key family is the next unit. Protect the disk by other means (full-disk encryption) until it lands.

## What counts as a security problem here

- An action that gets past the rulebook without being written down.
- A refusal that is not written down.
- A change to the history that the chain does not catch.
- Content removed without a signed receipt.
- Someone reading content they were not given a key for.
- A secret readable by any route.

## What does not count, for now

- The placeholder keys. Known, and stated above.
- An administrator editing the record file. Known. The chain shows where, and cannot stop it.
- Timing and hardware side channels, and denial of service. Out of scope until stated otherwise.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
