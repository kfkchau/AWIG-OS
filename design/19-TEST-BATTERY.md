<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=SUPERSEDED supersedes=- superseded-by=design/28-TARGET-STATE-HOST-KERNEL.md verified=2026-07-24 -->
# GOV-OS — The Test Battery (acceptance checks, written before code)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** SUPERSEDED by the real suite: the
> acceptance checks named here were realized and vastly extended — the live battery is
> `tests/` (200+ green) plus the committed adversarial `tools/mentor-probes/`, and each
> EP names its own T-* checks (design/28 §11). The T-names here that survived map onto
> real tests; many campaign guarantees (conservation, untouchables, obligations,
> blind streams) postdate this doc entirely. Read `tests/` for what is actually proven.

**Status:** v0.1, 2026-07-12, Route-A assumption. Every acceptance check the
kernel must pass, written now, before code exists — so the code is built to pass
known tests rather than tested after the fact (house rule: contracts double as
tests). Grouped by what they prove. Each is executable-in-principle; the ones
that need a running artifact name which bridge stance (`16-`) first makes them
runnable. Labels per `00-READ-FIRST`.

---

## 1. The audit-contract tests (prove the five guarantees, `03 §1`)

- **T-ATTRIBUTION.** For every change to governed state, a query returns the
  recorded decision that caused it, with actor, operation, and time. Fail = a
  state change with no attributable decision. *(Runnable at bridge stance 2.)*
- **T-EXPLANATION.** Every decision returns the rule it cited; every refusal is
  itself a record citing its rule. Fail = a decision or refusal with no cited
  rule. *(Stance 1.)*
- **T-REPLAY-DETERMINISM.** Given the recorded (law, decisions, inputs), replay
  reconstructs identical governed state. Run twice; states must be bit-identical.
  Fail = divergence ⇒ either a non-pure derivation or an unrecorded input.
  *(Stance 1 for app scale; stance 3 for a real resource.)*
- **T-ASOF.** For any past time T, "what could actor X see / what was the state at
  T" returns the correct historical view. Fail = a view that can't be computed
  as-of. *(Stance 2.)*
- **T-ORDERING.** Two writers colliding produce a single deterministic order:
  time-hash, then subsystem built-ID. Replay the collision; order is stable.
  Fail = nondeterministic order ⇒ the intake pipeline is not definitional.
  *(The formal-proof version is the deferred max-session item, `03 §8`.)*
- **T-OBSERVABILITY-BOUNDARY.** No governed decision depends on a sampled stream
  value except through an embedded cited-evidence summary; sampling a stream
  differently must not change any reconstructed state. Fail = a load-bearing
  sample. *(Stance 1.)*

## 2. The reconstruction-invariant tests (prove derived-not-stored, `03 §2`)

- **T-CACHE-KILL.** Delete every derived cache (run-queue, page tables, fd table,
  directory tree), replay, reconstruct. Result must equal pre-deletion state.
  This is the venn2 round-trip law at kernel grade. Fail = something was stored
  that should have been derived. *(Stance 1→3 per subsystem.)*
- **T-NO-STORED-STATUS.** Static audit of the design: grep the false-primitive
  register (`18 §F`) — no mutable process table as truth, no authoritative
  page-table entry, no stored permission bit, no in-place device registry. Fail =
  any stored status that should be computed. *(Design-time; runnable now.)*
- **T-CRASH-RECOMPUTE.** Kill the machine mid-operation; on restart, caches
  rebuild from the record to the last consistent decision. Fail = data loss
  beyond a cache. *(Stance 3.)*

## 3. The compatibility tests (prove "same ports", `03 §5`, map in `10-`)

- **T-SYSCALL-SEMANTIC.** For every syscall in the conformance map (`10-`), the
  gov-os path returns identical results, identical errno on identical error
  conditions, and identical visible ordering guarantees as stock Linux. This is
  THE big suite; the conformance map is its spec. Fail = any behavioural
  difference. *(Stance 3 for file syscalls; stance 4 per subsystem.)*
- **T-UNMODIFIED-PROGRAM.** A real, unmodified program (start with `cat`, `ls`,
  `git`; escalate to a browser) runs correctly against the records-backed
  resource. Fail = a program that behaves differently. *(Stance 3.)*
- **T-PROC-VIEW.** `/proc` and `/sys` entries the design covers (`13-`) return
  shapes programs accept, computed as views. Fail = a program that parses `/proc`
  breaking. *(Stance 2 for read-only shadows; stance 4 authoritative.)*
- **T-TIMING-NOT-PROMISED.** Explicitly NOT a pass/fail on identical latency —
  the port promises semantic identity, not timing (`03 §5`), with ONE exception
  (next test). This test only asserts the promise is documented so no one mistakes
  a perf gap for a conformance failure.
- **T-REALTIME-BOUND.** (owner-ruled 2026-07-13) The one place timing IS a
  pass/fail: a task under a real-time policy (`SCHED_FIFO`/`SCHED_RR`/`SCHED_DEADLINE`)
  must meet the latency/deadline guarantee that policy sells — because for the
  real-time classes the timing bound IS the semantics (`03 §5` carve-out). Fail =
  a missed deadline a stock-Linux real-time task would have met. *(Scheduler
  subsystem; replaced last, so runnable at its assume gate — stance 4.)*

## 4. The replacement-safety tests (prove shadow/assume/retire is reversible, `03 §6`, `16-`)

- **T-SHADOW-DIFF.** While shadowing, the gov-os subsystem's derived state is
  diffed continuously against Linux's live state; the diff trends to and holds ∅
  under real load before any assume. Fail = persistent divergence ⇒ do not assume.
  *(Stance 2→3.)*
- **T-DIVERGENCE-HALT.** Inject a deliberate divergence during shadow; the system
  must halt the assume, keep Linux authoritative, and record the divergence. Fail
  = a silent or unrecorded divergence. *(The safety catch; stance 3.)*
- **T-ASSUME-INVISIBLE.** At the assume switch, running programs see no
  interruption — the interface never moved. Fail = any program noticing the
  handoff. *(Stance 3→4.)*
- **T-LOCAL-FALLBACK.** If a subsystem's inversion fails, falling back to
  Linux/Route-B for that subsystem only leaves all other subsystems untouched.
  Fail = a local failure forcing a global rollback. *(Stance 4.)*

## 5. The governance tests (prove the law layer, `17-`, `18-`)

- **T-LAW-AMENDABLE.** Change a scheduling policy / memory budget / permission by
  amending its LAW record (no recompile); the running kernel's behaviour changes
  accordingly and the amendment is recorded with its authority. Fail = a policy
  that can only change by rebuilding. *(Stance 3+.)*
- **T-CALIBRATION-EVIDENCED.** Every calibration value (sampling rate, coalescing
  granularity, checkpoint cadence) has a recorded owner and an evidence basis —
  no invented numbers. Fail = a magic constant with no provenance. *(Design-time
  + runtime.)*
- **T-GATE-COUNT.** Exactly three human-gate kinds exist (definition, calibration,
  acceptance). Fail = a fourth ⇒ governance misclassified as judgment (`17 §3`).
  *(Design-time.)*
- **T-NO-HOTPATH-MODEL.** Static: no model call anywhere on the kernel hot path
  (`17 §5`). Fail = judgment on the running path. *(Design-time; runnable now.)*

## 6. The scar-tissue guards (paid-for lessons, `reference\su\SU_AUTOMATION_GUIDE.md` §8)

Carried to kernel grade as standing checks:
- **No silent lookup defaults** — every table miss fails loud (the `rstrip`
  disaster). Applies to every derived-cache lookup.
- **Green only after running** — no test marked pass before its check executes;
  the log line comes from output, not intention.
- **Global-measure guard on local optimization** — any per-subsystem tuning
  carries a whole-machine measure and a monotonic guard (SU Law 14).
- **Reference is registered, not found** — conformance is tested against the real
  Linux ABI (the registered reference), not against remembered behaviour.

---

## How the battery maps to the bridge (what's runnable when)

| Stance (`16-`) | Tests that become runnable |
|---|---|
| 1 (app) | T-EXPLANATION, T-REPLAY (app), T-OBSERVABILITY, T-CACHE-KILL (app), T-NO-STORED-STATUS, T-GATE-COUNT, T-NO-HOTPATH-MODEL |
| 2 (shadow real resources) | T-ATTRIBUTION, T-ASOF, T-PROC-VIEW (read), T-SHADOW-DIFF |
| 3 (FUSE authority) | T-SYSCALL-SEMANTIC (files), T-UNMODIFIED-PROGRAM, T-CRASH-RECOMPUTE, T-DIVERGENCE-HALT, T-ASSUME-INVISIBLE, T-LAW-AMENDABLE |
| 4 (in-kernel) | T-SYSCALL-SEMANTIC (per subsystem), T-PROC-VIEW (authoritative), T-LOCAL-FALLBACK |

**Honest cap:** these are acceptance *specifications*; none has run (no code
exists yet). Writing them now is the point — the code will be built to pass a
known battery. T-ORDERING's proof version now exists as a rigorous hand proof
(`21-ORDERING-DETERMINISM-PROOF.md`); the optional machine-checked hardening
remains a max-session choice. Everything else is runnable-in-principle at the
bridge stance named.
