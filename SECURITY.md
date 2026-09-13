# Reporting a security problem

Email **security@rootrebuilder.org** with "security" in the subject line. Do not open a public issue. Include the line from `code/FREEZE.txt`, your operating system, and the smallest steps that show the problem.

You will get an acknowledgement within a few days. We agree a disclosure date with you and credit you when it is fixed, unless you ask us not to.

## Read this before you report

AWIG OS is at an early stage. Do not put real secrets behind it yet.

The locks are real when you install them. Nothing is installed by default, and by default the keys are stand-ins of the right shape, as before. Install the named library and signing and sealing are real cryptography. Either way, whoever holds the disk or administers the running machine can read what it holds. In the build team's exact words:

> Real cryptography is in this code and is off until you turn it on. Install the one vetted library it names and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did, with keys that are stand-ins of the right shape; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.

## What counts as a security problem here

- An action that gets past the rulebook without being written down.
- A refusal that is not written down.
- A change to the history that the chain does not catch.
- Content removed without a signed receipt.
- Someone reading content they were not given a key for.
- A secret readable by any route.

## What does not count, for now

- Stand-in keys on a machine where the library is not installed. Known, and stated above.
- Reading the disk or the running program's memory. Known, and stated above.
- An administrator editing the record file. Known. The chain shows where, and cannot stop it.
- Timing and hardware side channels, and denial of service. Out of scope until stated otherwise.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
