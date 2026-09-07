# Contributing to AWIG OS

Code, architecture review, documentation, translation (Bahasa Indonesia especially),
and critique of the governance model itself are all welcome. A project about governance
keeps its own written trace; contributing here follows that same trace.

## Before you start

Read [`GOVERNANCE.md`](./GOVERNANCE.md), which is how decisions here are proposed,
discussed, and recorded, and [`LICENSING.md`](./LICENSING.md), which sets the layer
each file lives under.

## How a change happens

The flow is deliberately simple and open:

1. **Propose, in writing.** An issue or a pull request that says what and why.
2. **Discuss, in that thread.** In the open.
3. **A recorded decision.** Accepted or rejected, preserved either way. A community
   that keeps its refusals honest keeps its acceptances meaningful.

Substantial proposals (a new layer, a change to the rule format, anything that touches
the naming or licensing commitments) start as a written proposal before code.

## Developer Certificate of Origin

Every commit carries a DCO sign-off: add `Signed-off-by: Your Name <email>` with
`git commit -s`, certifying you have the right to submit the work under this project's
licenses (see <https://developercertificate.org/>). You keep your copyright; your work
stays yours, licensed to the project under its layer's license.

## Working with the code

The runnable engine is under [`code/`](./code/); it is a **rendering** of a private
source estate, never edited by hand; `code/README.md` explains how it is generated,
stamped, and checked. Fixes to the engine are proposed against the upstream source
through the flow above, not by editing the rendered tree. Documentation and this
repository's own root files can be proposed directly.

Keep it running on the standard library alone: `cd code && python3 check.py` must stay
green (exit 0), and check 6 must stay able to fail.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
