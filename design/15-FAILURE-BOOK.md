<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Failure Book (every anticipated failure, and what the governed kernel does) — plain-register edition

Plain-register edition, in place (the framed original is retained at `tests/archive/15-FAILURE-BOOK.md` and in git history) [banner amended 2026-07-24]: the same nine failure modes and the same
governed responses, with the failure-index numbering replaced by named sections and a few
loaded verbs written plainly. This is a standard failure-mode-and-response catalogue (the
reliability-engineering shape), stating for each mode how the kernel detects it and what it
does — recorded and rule-cited, never silent.

> **SUPERSESSION NOTE (2026-07-18 line-audit).** STANDS — and the campaign built beyond
> it: refusal machinery this book never anticipated now exists (the constitution guard's
> branches, the protected-core floor, tier conservation, the watcher brake, the
> accepted-but-cannot-honour refusal rule). The lived record of real fixes is the running
> list in `planning/build/BUILD-PROGRESS.md` — every real defect found, how it was caught,
> and its fix. Read both: this book for the designed envelope, the log for what actually
> broke and how the method caught it.

**Status:** v0.1, 2026-07-12. **Route-A (hollow-out) assumed throughout** (03-TARGET §7).
Labels per 00-READ-FIRST §6. Companion to `14-SEAM-CONTRACTS.md` — where that book says how a
seam works, this one says what happens when it doesn't. No code.

This book lists every anticipated failure mode of the governed kernel and states exactly
what it does about each — because in gov-os a failure is not an exception to the design, it
is a case the design already governs. For each mode: the failure, the detection (how the
kernel knows), the governed response (what it does — recorded, rule-cited, never silent), and
the recovery (how it returns to a consistent state). The through-line is the governance root:
a fault that vanishes as it acts is exactly what gov-os exists to prevent. So every response
here is a recorded, rule-citing act, and every recovery reduces to one move — recompute from
the record. The estate's own hard-won lessons are carried in at kernel grade at the end.

---

## How to read a failure entry (the fixed shape)

- **Failure** — what goes wrong, stated concretely.
- **Detection** — the mechanical signal the kernel sees. A failure with no detector is not
  yet governed — that is itself a finding.
- **Governed response** — what the kernel does: recorded, rule-cited, never a silent repair.
  A refusal, halt, or reclaim is an appended record citing the rule it applied.
- **Recovery** — how governed state returns to consistency. Almost always: recompute the
  caches from the record.
- **Rule cited** — the standing law the response invokes.
- **Acceptance** — how you would know the handling works (the negative test).

The classes referenced throughout are 03-TARGET §2: LAW / DECISION / INPUT / CACHE / STREAM,
with the invariant `governed state = f(LAW, DECISIONS, INPUTS)`.

---

## Cache corruption

**Label:** SOURCE-DERIVED (03-TARGET §2 "a crash loses only caches; recovery is recompute";
02 §1.5 snapshot never referenced as truth; SC2/SC3).

- **Failure:** a hot cache (page table, run-queue, fd/dentry cache, view memo, binding
  table) holds a value inconsistent with the record — a bit-flip, a partial write, or a
  logic error in the fold.
- **Detection:** the reconstruction check (SC3) — recompute `f(LAW, DECISIONS, INPUTS)` and
  compare against the live cache; the determinism ledger signals a mismatch (same input hash
  → same output hash). At read time, a generation-key mismatch (SC2) also flags a stale
  cache.
- **Governed response:** the cache is not truth and is never referenced as truth (snapshot
  law, 02 §1.5). Discard it; recompute from the record; append a divergence record citing the
  reconstruction invariant (03-TARGET §2). No silent repair — a "fixed" cache with no record
  is the very pathology gov-os refuses.
- **Recovery:** recompute the cache from `f(LAW, DECISIONS, INPUTS)`; the record wins over any
  cached value. Service continues on the recomputed cache.
- **Rule cited:** 03-TARGET §2 reconstruction invariant; 02 §1.5 "a snapshot is never
  referenced as truth."
- **Acceptance:** set a corrupt cache value → the next read/round-trip check finds `diff ≠ ∅`
  → the cache is discarded and recomputed → a divergence record exists → outputs are
  unchanged after recompute (the kill-the-cache property, 02 §10).

---

## Crash mid-operation

**Label:** SOURCE-DERIVED (03-TARGET §2 crash-loses-only-caches; 02 §1.1 append-only, `seq`
minted at append; S1 store contract).

- **Failure:** power loss or panic between "op validated" and "op fully applied to caches," or
  during the append itself.
- **Detection:** on restart, replay the log. The last record carrying a minted `seq` is the
  last consistent decision. A half-applied cache is just a cache (discarded on boot). A
  half-written append has no `seq` and therefore is not a record.
- **Governed response:** replay to the last consistent decision. Because append is the atomic
  commit point (`seq` and `record_time` minted at append, 02 §1.1), there is no half-record;
  caches are rebuilt from the log. Append-only means no update/delete path exists to leave a
  torn record behind (S1).
- **Recovery:** recompute all caches from the record; resume. A crash loses only caches
  (03-TARGET §2). A mid-append partial write is not a record and is ignored — the store
  contract's append atomicity guarantees this (S1 acceptance).
- **Rule cited:** 03-TARGET §2; 02 §1.1 append-only + atomic-commit-at-append; S1.
- **Acceptance:** stop the process at N points across an operation → on every restart, replay
  reaches the last `seq`'d decision, caches rebuild identically, and no partial state survives
  (no torn record, no half-cache promoted).

---

## A subsystem's shadow drifting from Linux during replacement

**Label:** SOURCE-DERIVED (03-TARGET §6 shadow→assume→retire; §7 Route-A cost-if-wrong; SC4).
This is the SC4 rejection path made a first-class failure.

- **Failure:** during shadow/assume/retire, the governed shadow's derived state drifts from
  Linux's live authoritative state under real load.
- **Detection:** the continuous live round-trip diff (03-TARGET §6, SC4) reports `diff ≠ ∅`.
- **Governed response:** halt the assume — do not switch authority. Keep Linux authoritative.
  Record the drift (what drifted, at which interface point, under what load), citing the
  assume gate (§6: assume only when `diff = ∅` under real load). This is the falsification
  probe working, not a failure of method (the shadow phase IS the probe the owner's method
  requires, §7).
- **Recovery:** diagnose the drift; the interface never moved, so userland never noticed. If a
  hot subsystem cannot be inverted inside Linux's frame, fall back to Route B for that
  subsystem only — the ports contract makes the fallback local, not total (§7 cost-if-wrong).
- **Rule cited:** 03-TARGET §6 assume gate; §7 Route-A cost-if-wrong.
- **Acceptance:** introduce a drift in the shadow → the `assume` switch is blocked
  automatically → Linux stays authoritative → a drift record exists → userland sees no change
  (the conformance suite on the Linux path stays green). Ties to the lesson "log green only
  after running" — authority is never assumed on intention.

---

## Out-of-memory (OOM)

**Label:** SOURCE-DERIVED (03-TARGET §4.2 "OOM becomes a governed, recorded decision citing
its rule and its evidence, not a silent reaper"; §2 AUDIT-FIX 3 evidence-citing decisions).
Lesson tie: no silent defaults.

- **Failure:** memory demand exceeds supply; something must be reclaimed.
- **Detection:** an allocation predicate fails against the actor's budget (budgets-flow-down,
  §4.2), or a page-fault arrival (INPUT) cannot be satisfied.
- **Governed response:** OOM is a governed, recorded decision, not a silent reaper. The
  decision record names what was reclaimed, cites the rule, cites the budget, and embeds the
  evidence summary it acted on — which aggregate said the page/region was cold (AUDIT-FIX 3).
  Reclaim never happens without a record.
- **Recovery:** the reclaim is a recorded eviction/release decision; the memory map can answer
  "who was granted what, when, under which budget rule" forever (§4.2 port win). If the rule
  itself was wrong, amend the budget — a LAW amendment with named authority, not a code patch.
- **Rule cited:** 03-TARGET §4.2 (OOM as governed decision); §2 evidence-citing decisions.
- **Acceptance:** drive the system to OOM → a recorded decision names what was reclaimed + the
  rule + the budget + the evidence → no reclaim occurs without a record → "why was X
  reclaimed?" is answerable from the record alone, forever.

---

## Driver fault

**Label:** SOURCE-DERIVED (03-TARGET §4.4 validated typed boundary +
capability-is-law/pwc R14; §4.5 kernel state shared-nothing; 02 §3 the Wall).

- **Failure:** a driver malfunctions — a bad DMA, a hang, an invalid completion, a fault at
  the boundary.
- **Detection:** the validated, typed boundary (the estate's envelope rule generalised, §4.4)
  rejects the malformed crossing at the boundary; the fault does not propagate into kernel
  state.
- **Governed response:** the boundary contains it — the one place isolation appears, as a
  derived property of governed capability, not as a frame (§4.4). The invalid crossing is a
  recorded refusal citing the device's capability grant (registering a driver is a recorded,
  authorized amendment — capability is law, twc R14 — not a config edit). Unbind is a recorded
  decision.
- **Recovery:** rebind or retire the driver via recorded decisions; the binding table (a
  cache) reconstructs from the record. Because kernel-internal state is shared-nothing (§4.5),
  the fault cannot race shared kernel structures — the unrecorded-shared-mutation race class is
  removed from the kernel itself.
- **Rule cited:** 03-TARGET §4.4 (validated boundary + capability-is-law); §4.5 shared-nothing
  kernel state; 02 §3 tool containment / the Wall.
- **Acceptance:** feed a driver an invalid completion → the boundary rejects it, records the
  refusal citing the capability grant, and kernel state is unaffected → unbind/rebind are
  recorded → the binding cache reconstructs from the record.

---

## Record-store full / unbounded growth (RULED-PENDING-HORIZONS)

**Label:** SOURCE-DERIVED (02 §1.5 growth law + tiering; §9 S10; §11 do-NOT-build; GS-13
master-destruction). **Status: mechanisms RULED in `23-CAPACITY-ECONOMICS.md`; the horizon
VALUES remain an owner calibration.**

- **Failure:** the append-only record grows without bound; physical storage fills.
- **Detection:** capacity monitoring (STREAM/observability). The growth law says the record
  grows linearly with world-activity and nothing else (minimal primitives, 02 §1.5) — so
  growth is predictable, but the physical ceiling is real.
- **Governed response:** per `23-CAPACITY-ECONOMICS.md`: tiering (S10) offloads cold,
  immutable segments to a content-addressed archive with hashes retained inline —
  derivability kept at a fetch cost; horizon compaction exists only as an owner-authorised act
  at a long horizon; GS-13 remains the one destruction path. The kernel never silently prunes
  to make room; capacity pressure surfaces as a governed alert.
- **Recovery:** tiering/archive (S10 — after S4); fetch-on-replay restores cold segments at a
  cost. The horizon values are an owner calibration (23 §4) — never invented; until ruled, the
  alert stands and nothing is dropped.
- **Rule cited:** 02 §1.5 growth law + tiering; §9 S10; §11 do-NOT-build; GS-13.
- **Acceptance (partial — the full test is OPEN pending owner ruling):** growth is linear in
  world-activity (instrument and confirm); cold segments are immutable and content-addressed;
  a tiered segment is still derivable at a fetch cost (S10 acceptance). The capacity threshold
  and its cost model remain an OPEN owner decision — do not fabricate one.

---

## Replay cost growth

**Label:** SOURCE-DERIVED (02 §1.5 snapshot law; §9 S4 governed checkpoint; §11
false-primitive register "snapshot tables → freezing").

- **Failure:** replay-from-genesis time grows with the log; recovery and `asOf` become slow as
  the record lengthens.
- **Detection:** replay-time instrumentation (STREAM) — cost grows with log length; recovery
  latency crosses an operational threshold.
- **Governed response:** apply the snapshot/checkpoint law (S4): a snapshot is a regenerable
  cache citing its log `seq`, validated by round-trip `diff = ∅`, and never referenced as
  truth. `replay-from-checkpoint ≡ replay-from-genesis`. Checkpoints bound replay cost without
  becoming truth.
- **Recovery:** replay from the nearest valid checkpoint plus the tail past its `seq`; the
  checkpoint is discardable and re-derivable at any time.
- **Rule cited:** 02 §1.5 snapshot law; §9 S4; §11 false-primitive register ("snapshot tables →
  freezing — keep it open"). The checkpoint cites its `seq` and is `diff = ∅`-validated
  precisely so it never freezes into truth.
- **Acceptance:** `replay-from-checkpoint ≡ replay-from-genesis` under `diff = ∅` (S4
  acceptance); replay time bounded by (checkpoint → tail), not (genesis → tail); killing every
  checkpoint changes nothing — the state recomputes from genesis, only slower.

---

## An unregistered operation is invoked

**Label:** SOURCE-DERIVED (02 §1.2 gate, "unknown op = refusal + referral, a Closure Hit";
DESIGN-CONCEPTS P3 "the bank has no counter"; SC1/SC5). Lesson tie: fail loudly on every
lookup miss.

- **Failure:** an operation is invoked that is not in the registry — a syscall mapping to no
  registered op (SC5), a mistyped op, or an unregistered name.
- **Detection:** the registry membership check at the gate. An unknown op does not exist —
  registry enumeration IS the completeness guarantee ("the bank has no counter,"
  DESIGN-CONCEPTS P3).
- **Governed response:** a Closure Hit — refusal plus referral. The refusal is itself
  appended, citing the rule (unknown-op refused); it fails closed. At the port boundary, it
  returns the correct errno to userland and records the refusal (SC5). There is no
  default/fallthrough handler.
- **Recovery:** if the op should exist, it enters by governed amendment (capability is law —
  registering an op/handler is an authorized amendment with named authority, twc R14), never
  by silent addition. The referral routes the Closure Hit to the responsible seat.
- **Rule cited:** 02 §1.2 gate (Closure Hit); registry enumeration = completeness; the lesson
  on lookup misses (fail loudly, assert membership).
- **Acceptance:** invoke an unregistered op → zero domain records, exactly one refusal record
  with referral, correct errno at the port → confirm no default/fallthrough handler exists in
  the gate (grep the write path — the S-plane is one grep-verifiable path, 02 §3).

---

## Input event lost

**Label:** SOURCE-DERIVED (03-TARGET §1.3/§2 AUDIT-FIX 1 conditional replay determinism; §2
INPUT class; determinism ledger, S/U §5; SC6). This is the SC6 rejection path made a
first-class failure.

- **Failure:** a state-changing external arrival (interrupt, I/O completion, tick, packet,
  fault) is dropped before it becomes an INPUT record.
- **Detection:** the determinism ledger — replay output hash ≠ live output hash (same input
  hash → same output hash, signal on divergence). A lost input means the recorded input stream
  is missing an arrival the live run consumed, so the derived decision stream diverges at
  replay.
- **Governed response:** this is a determinism-boundary break. Replay is deterministic only
  relative to the recorded input stream (AUDIT-FIX 1); a lost input violates that
  precondition. Record the divergence. State the claim honestly: determinism is conditioned on
  inputs being recorded, never "free."
- **What breaks:** the affected caches can no longer be reconstructed identically past the
  lost arrival; `asOf` answers after that point become unreliable — the audit guarantee is
  voided for that `seq` range, and the void is visible.
- **Recovery:** the intake pipeline (S5) must record every state-changing arrival before the
  consuming decision (SC6 contract). Prefer backpressure to a silent drop — a recorded
  refusal/halt beats a lost input. If intake saturation is the cause, it intersects the
  capacity question above. The determinism ledger localises the void to a `seq` range for
  diagnosis.
- **Rule cited:** 03-TARGET §1.3/§2 AUDIT-FIX 1; §2 INPUT class; determinism ledger (S/U §5);
  SC6 determinism boundary.
- **Acceptance:** deliberately drop an input → the determinism ledger flags divergence (live
  vs replay hash) localised to a `seq` range → the drop is detected, never silently absorbed
  (the SC6 negative test). Backpressure path: under intake saturation, the kernel records a
  refusal/halt rather than dropping — verify no arrival is consumed by a decision without
  first being recorded.

---

## Hard-won lessons carried to kernel grade

The S/U estate paid for these once each (SU_AUTOMATION_GUIDE §8); they bind gov-os wholesale
(02 §11 inherited law). Restated at kernel grade, each maps onto a failure mode above.

### No silent lookup defaults (→ OOM, unregistered-op)
**The lesson:** a `.get` with a silent default is a latent catastrophe — a `rstrip("_lr")`
stripped the 'r' from "ear," the lookup missed, and a silent default built the wrong
primitive, invisible through several review rounds because nothing failed (S/U 8.2). **At
kernel grade:** a syscall dispatch table with a default handler, an OOM silent reaper, or an
unregistered op falling through to a fallback are the same catastrophe at the metal. **The
law:** every lookup miss fails loudly — asserts membership, appends a rule-cited refusal,
never falls through. This is why the unregistered-op case requires proving no default handler
exists, and why OOM must be a recorded decision, not a reaper.

### Log green only after running (→ subsystem-drift, and every acceptance test)
**The lesson:** a "suite PASS" was written to the log before the suite ran; the suite then
failed — it had caught a real geometry break (S/U 8.10). Evidence precedes claims; the log
line comes from the test output, not the intention. **At kernel grade:** a subsystem is not
"replaced" because the shadow was built — it assumes authority only after `diff = ∅` holds
under real load and the conformance suite is observed green. The `assume` decision cites
observed evidence, never intention. **The law:** no state transition ("assumed," "retired,"
"green," "consistent") is recorded until the evidence that licenses it has been observed.
Every acceptance test in this book is written as an observation for exactly this reason.

### Global-measure guards (→ all subsystem tuning)
**The lesson:** blocks tuned to their own targets wrecked the gestalt — per-part optimization
degraded the whole, and moving one part shifted the shared frame under all others (S/U scar 6
→ Law 14: global measure + monotonic guard). **At kernel grade:** tuning one subsystem's cache
or policy during replacement must be guarded by a global measure — the whole-record round-trip
`diff = ∅` and the syscall conformance suite green across all subsystems — kept under a
monotonic guard: keep a change only if the global measure does not regress. **The law:** no
local optimization (scheduler tweak, allocator tuning, cache-layout change) is retained unless
the global audit measure holds or improves. Optimizer objectives must equal the judge's own
code (S/U Law 11) — the "judge" here is the conformance suite and the round-trip law, not a
proxy.

---

## Coverage statement (what this book does NOT cover)

- **Capacity:** now RULED-PENDING-HORIZONS — the mechanisms and costs are specified in
  `23-CAPACITY-ECONOMICS.md`; only the horizon values remain an owner calibration. Do not
  fabricate the numbers.
- **Formerly deferred, now done:** the ordering-determinism proof exists at `21-` (the
  input-lost case detects breaks; `21-` proves the order is deterministic when inputs are
  recorded); the hot-subsystem proof-of-method exists at `22-` (memory), which is where the
  subsystem-drift inversion-resistance concern is analysed.
- **Not enumerated here:** userland-internal failures (a bug inside a program's own
  `MAP_SHARED` region) — gov-os governs the granting of shared access, not the interior
  writes (03-TARGET §4.5 AUDIT-FIX 5). Races inside userland's shared regions remain
  userland's business; this book covers only kernel-state failures.
- **Assumption:** Route-A (hollow-out) throughout; under Route B, the subsystem-drift handling
  applies at the compat-layer seam rather than in-place.

**One-line invariant across all failure modes:** the fault is recorded, the rule is cited, and
recovery is recompute from the record — a failure that vanishes as it acts is the one thing
the governed kernel does not permit.
