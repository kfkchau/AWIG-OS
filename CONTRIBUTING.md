# Contributing to AWIG OS

Code, design review, documentation, translation (Bahasa Indonesia especially), and criticism of the governance model itself are all welcome. A project about governance keeps a written record of its own decisions, and contributing here works the same way.

## Before you start

Read [`GOVERNANCE.md`](./GOVERNANCE.md), which says how decisions here are proposed, discussed and recorded, and [`LICENSING.md`](./LICENSING.md), which says which licence each part of the project is under.

## How a change happens

1. **Propose it in writing.** Open an issue or a pull request that says what you want to change and why.
2. **Discuss it in that thread,** in the open.
3. **A decision is recorded,** accepted or rejected, and kept either way. Keeping the refusals honest is what makes the acceptances mean something.

Big proposals, such as a new layer, a change to the rule format, or anything touching the project's name or licences, start as a written proposal before any code.

## Signing your work

Every commit carries a sign-off line, `Signed-off-by: Your Name <email>`, which `git commit -s` adds for you. It certifies that you have the right to contribute the work under this project's licences (the Developer Certificate of Origin, <https://developercertificate.org/>). You keep your copyright. Your work stays yours, licensed to the project under the licence of the part it belongs to.

## Working with the code

The runnable engine is in the [`code`](./code/) folder. It is generated from a private source repository and checked, never edited by hand. `code/README.md` explains how it is made and how to check it. To fix something in the engine, propose the fix through the flow above and it goes into the source. Documentation and the files at the root of this repository can be proposed directly.

Keep the governing layer running on Python's standard library alone; the one optional library is PyNaCl, for real keys. `cd code && python3 check.py` and `python3 run_public_suite.py` must keep passing, and check 6 must keep being able to fail. The kernel under `code/src/body` is freestanding C and assembly: it builds with `gcc` and `binutils`, links no library, and every self-check it prints has a planted fault in `build.sh` that makes it fail. A change that adds a check adds its plant.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
