# Security policy

AWIG OS is pre-alpha. It is a reference model and a seed, not a system to put real
secrets behind yet. This file says how to report a problem and states, plainly, the
one limit you must design around before you trust it with anything.

## The cap you must read first

> Every key in this release is a stand-in of the right shape, not real cryptography.
> A reader of the whole record on disk can derive an open key and unseal content.
> Protect the disk by other means (full-disk encryption).

This is by design and it is stated everywhere the keys appear. Signatures, open keys,
and attestation seals are shape-true modelled material; real cryptographic key material
under the whole family is the next named unit of work. Until it lands, treat the record
file as readable by anyone who holds the disk, and protect the disk itself.

## Reporting a vulnerability

> Report privately to **kelvin@rootrebuilder.org**, and mark the message as a security report.

Please report privately, not in a public issue, anything that lets an act evade the gate,
a record be edited without breaking the chain, a refusal go unrecorded, or a reader see
content they hold no open key for. Include the version (`code/FREEZE.txt`), the platform,
and the smallest steps that show it.

We aim to acknowledge a report within a few days, agree a disclosure timeline with you,
and credit you when it is fixed, unless you ask us not to.

## Scope

In scope: the engine under `code/src`, the seed scripts, and the release rendering and its
stamp. Out of scope for now, because they are documented caps rather than defects: the
modelled key material above, and any test count that does not name the machine it ran on.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
