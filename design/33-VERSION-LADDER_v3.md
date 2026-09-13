<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — The Version Ladder: what "release" means at each rung

**Status:** v1, 2026-07-18, mentor session. What each version number actually MEANS —
what it is safe to do with the system at that rung, and what it still cannot honestly
claim. Written because "is this releasable?" and "is this pilot-ready?" have different
answers at different rungs, and conflating them is how a governance system ships a
promise it can't keep. Owner rulings control; sequencing per `design/32`.

The one honest line under everything: **a release is not "does it run" — it is "can a
person other than its builder trust the guarantees it makes."** That line is crossed at
one specific rung, and it is not the one where the code first works.

---

## The ladder

| Rung | Reached at | What it IS | What it CANNOT yet honestly claim |
|---|---|---|---|
| **v0.1 — the engine** | END OF CAMPAIGN 1 (now) | A working reference kernel in user space: one record, computed state, gated+cited acts, a self-protecting constitution, promises that keep themselves, separation of powers, health gauges, compare-without-merging. 243 tests [corrected 2026-07-24 from "233" — the EP-13 reconciled count; the stale figure was flagged as doc rot in the campaign-1 findings] + a stress-test library; reconstructs from its own record. **Proof the architecture RUNS.** | **Safe for a second person.** Identity is an unchecked string — anyone can claim to be anyone. This is the builder proving the engine to themselves, not a thing to put a user in front of. |
| **v0.2 — the pilot** | END OF CAMPAIGN 2 — **REACHED, owner-ruled 2026-07-25** | The first HONESTLY RELEASABLE rung. Verified accounts, spaces, power-by-grant, the untouchables enforced by real scope. A second person can act and the guarantees hold AGAINST them. **The doorway: real governed multi-user work in a bounded setting.** | Being an operating system (still a user-space application); undetectable-on-disk alteration-proofing; describing other governance; federating. A pilot, not the platform. |
| **v0.5 — the real kernel** | END OF CAMPAIGN 3 (depth) | Custody, not shadow: the record AUTHORIZES real file/process operations behind unchanged interfaces. It stops describing an OS and becomes one. | Cryptographic closure; cross-system description/federation. (And its own biggest risk — OS-rate performance — is proven only HERE; see caps.) |
| **v0.7 — the sealed kernel** | END OF CAMPAIGN 4 (proof) | Every guarantee upgrades from cannot-do-lawfully/quietly to **cannot-do-undetectably, even on disk**: chained+signed records, engine attestation, physically separated audit, the one true destruction ceremony. | Describing/federating other governance (that is C5/C6). |
| **v0.9 — the fluent kernel** | END OF CAMPAIGN 5 (language) | Holds OTHER people's law: the full CGL grammar, claimed-vs-effective strength on foreign rules, attract-class enforcement, prose↔full-form translation. Describes governance, not just runs its own. | Federation across sovereign instances (C6). |
| **v1.0 — the platform** | END OF CAMPAIGN 7 (metabolism at scale) | The complete civilisation-grade thing the architecture set out to be: a governed OS, cryptographically closed, able to describe and federate, RUNNING A REAL ORGANISATION end to end (the 33-seat proving example re-hosted as the reference userland). Federation (C6) lands before this. | — this is the destination. |

## The two questions this ladder answers

- **"Safe functional release, as v0.1?"** — v0.1 exists NOW and is honest AS an engine
  proof. It is NOT a release you put a user in front of; the release rung is **v0.2**,
  one campaign away, because that is where a second person can trust the guarantees.
  The sharp line: campaign 1 proves the engine to yourself; campaign 2 makes it safe to
  show someone else.
- **"Is campaign 7 pilot-ready?"** — no: **pilot-ready arrives at v0.2 (end of C2)**, far
  earlier. A pilot needs verified identity and enforced scoped power, nothing more.
  Campaign 7 is not "pilot" — it is v1.0, the full platform. Pilot is the doorway;
  campaign 7 is the destination. Everything between (C3–C6) is depth and reach, not the
  precondition for a first real user.

## Honest caps (the ladder's own risks, not hidden)

- **The single biggest unproven risk on the whole ladder is v0.5's performance.** A
  governed record layer taking real custody at operating-system speed is the one thing no
  test on this estate has touched (design/22, 23 flag it; design/32 §1 K3 reserves the
  max-tier work for it). It does NOT threaten the pilot (user-space is fine); it is the
  gate between "pilot-ready application" and "real kernel."
- **Rung numbers are direction, not a schedule** — no dates; each campaign completion
  re-prices the rungs above it (design/32 §6), exactly as campaign 1 reshaped campaign 2.
- **"Verified" strengthens across the ladder:** recorded-evidence identity at v0.2 →
  cryptographic identity at v0.7. A v0.2 pilot's guarantee is cannot-do-lawfully +
  cannot-do-quietly, not yet cannot-do-on-disk. Stated to any pilot partner, never implied
  away.
