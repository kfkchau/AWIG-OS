<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=SUPERSEDED supersedes=- superseded-by=design/27-FUNDAMENTAL-RULES.md verified=2026-07-24 -->
# GOV-OS — The Law Book (everything that binds, assembled)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** SUPERSEDED as an index: the binding law
> is now RECORDED and readable back from the running kernel (`views.root_rules()` in full
> trigger→outcome form; `views.active_rules()`). The constitution GREW past this assembly:
> the three tiers, the five constitutional laws (RECORDING-TOTAL, AUTHORITY-ANCHORED,
> SECRETS, SELF-PROTECT, SYSTEM-FUNCTION), PACK-SCOPE, plus conservation and the
> untouchables as machinery. Live canon: design/27 (recorded constitution), 29, 30, and
> the genesis seed in `src/kernel/boot.py`. This book is the pre-campaign reading index.

**Status:** v0.1, 2026-07-12. This assembles, in one place, every rule that
already binds gov-os — nothing new is invented here (minimality gate). Each entry
points to its source of truth, which controls. This is a reading index of the
constitution, not the constitution; where this and a source differ, the source
wins, and owner raw wording wins over any paraphrase. Labels per `00-READ-FIRST`.

---

## A. The seven kernel first principles (TWC, `reference\pwc\DESIGN-CONCEPTS.md` §1)
Binding wholesale on gov-os; the kernel root (`03 §0`) is P1/P2 at the metal.
1. **Record is the world** — nothing exists except as an event; append-only; no
   update/delete path in code.
2. **Everything current is computed** — no stored status/role/permission/balance;
   caches are pure accelerations, discardable.
3. **The bank has no counter** — act only through a registered operation; an
   unregistered op does not exist (a Closure Hit).
4. **Refusal over improvisation** — a failed gate refuses, cites its rule, stops.
5. **Law is data** — every rule is a record with scope × authority.
6. **Sight is law** — visibility is computed and binds action (the provenance
   gate); sight also creates voice.
7. **Separation** — deciding ≠ executing; content never reviewed by its maker;
   dual mutually-blind audit.

## B. The fifteen S/U laws (`reference\su\SU_AUTOMATION_GUIDE.md` §3)
Binding on the build method and the running economics. Load-bearing at kernel
grade: 1 (events only), 2 (store scores not verdicts), 3 (calibration is governed
events), 4 (no ad-hoc prompts / no model on the hot path), 9 (the chain is data),
10 (gates never automated), 11 (constructors before gates), 12 (transport-
independent stations — the shadow/mock/live device abstraction), 13 (budgets flow
down), 14 (local optimization guarded by a global measure), 15 (proof lands in
the human's channel). Full text at source; do not paraphrase in rulings.

## C. The fourteen governance-store rulings (GS-1…GS-14, `reference\cgl-plan\cgl-build-handover-pack-v1.md`, frozen Layer A — VERBATIM ONLY)
Binding on the record substrate. The load-bearing one for a kernel: **GS-13** —
erasure is the ONE sanctioned exception to append-only (owner-only master-
destruction; regenerability knowingly forfeited; pre-erasure replay reproduces
the redacted state; the scar survives). At kernel grade this is how a device that
must be physically wiped, or a legally-mandated deletion, happens without lying
about the record. Quote GS-* verbatim; never restate.

## D. The gov-os audit contract (`03 §1`) — the five guarantees
Attribution · Explanation · Replay (conditioned on recorded inputs) · Ordering
truth (definitional, via the intake pipeline) · Honest observability boundary.
These are gov-os's own additions, derived from A+B+C for the kernel case.

## E. Owner rulings specific to gov-os (this workspace)
- **Scheduled execution is lawful** — the schedule is a recorded rule; execution
  is a recorded activity (2026-07-12).
- **Multi-writer ordering** — one ordered intake pipeline; time-hash order;
  two-way collision broken by subsystem built ID (2026-07-12).
- **Architecture map before technical testing** (2026-07-12).
- **Target state** — a real kernel plug-replacing the Linux kernel, same
  interfaces, rebuilt layer by layer (2026-07-12).
- **Governance-first framing** — the kernel is derived as a governance machine;
  full-grade auditability is the defining property (2026-07-12).
- **Method** — derivational vetting is primary; the tracer slice is a
  falsification probe; running code adjudicates adoption, never truth; the
  universality test is who-derives-who (carried from the CGL workstream).

## F. The false-primitive register (keep OPEN — `reference\cgl-plan\cgl-working-summary.md`)
Things that smuggle stored state back in and must be refused at kernel grade:
- ORMs → stored state; auth libraries → stored grants; snapshot tables → freezing.
- **Kernel-specific additions (INFERRED, this workspace):** a mutable process
  table used as truth; page-table entries treated as authoritative rather than
  derived; a permission bit stored instead of a computed capability; a device
  registry mutated in place. Each is the conventional kernel's version of the
  same error — cache kept, ledger burned. Refuse each; derive instead.

## G. The do-NOT-build list (`02 §11`, extended for gov-os)
- multi-writer physical parallelism beyond the ruled intake pipeline, until scale
  demands it (the ordering rule is set; the parallel *implementation* waits);
- any model call on the kernel hot path (sorting pass §4 — a designed invariant);
- a security/threat-model frame for the kernel (standing guard 1, `03 §8`);
- gate compression (SU Law 10);
- inventing calibration values instead of ruling them from evidence.

## H. The two standing guards (`03 §8`)
1. **Frame guard** — governance-first; if organising around threat models,
   re-root at `03 §0`.
2. **Scope guard** — `SCOPE-STATEMENT.md` settles the false-flag question; do not
   re-deliberate it.

---

**How to use this book:** at the start of kernel-design work, read A–E. When
tempted to add a concept, check F and the minimality gate. When tempted to build
something, check G. When a reviewer or a session drifts, invoke H. Everything
here has a source; the source controls; owner raw wording controls the source.
