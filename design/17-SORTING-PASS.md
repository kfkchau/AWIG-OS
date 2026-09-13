<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — The Sorting Pass (S/U classification of the whole kernel build)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** STANDS, and the campaign CONFIRMED it
> in practice: the S-plane grew only by logged design amendment (the check vocabulary,
> the general interpreter fields, the tier ladder — each an explicit engine-surface
> ruling, per design/28 §5/§10), and the judgment stayed in governed law exactly as
> this pass predicted. No content superseded.

**Status:** v0.1, 2026-07-12, xhigh, Route-A assumption. The S/U guide's required
step before building: walk the whole imagined build and put every operation in a
cell (S / U{s} / S{u} / U) and an alignment class. The guide says this pass IS
the design. For a kernel the result is almost entirely S — which is itself the
finding. Read `reference\su\SU_AUTOMATION_GUIDE.md` §2–3 first.

---

## 0. Why a kernel is almost all S — and why the pass still matters

A kernel is deterministic machinery: given recorded law, decisions, and inputs,
every derivation is pure code (S). There is no per-operation model judgment in a
running kernel and there must not be — a scheduler that called a language model
per tick would be absurd. So the naive expectation is "it's all S, skip the
pass." That is wrong, and the reason is the whole point:

**The U in this system is not in the running kernel — it is in the GOVERNANCE of
the kernel.** Setting a scheduling policy, choosing a memory budget, ruling
whether a driver may be trusted, calibrating a sampling rate, deciding an OOM
tie: these are judgment, and in a conventional kernel they are made invisibly by
whoever wrote the C and then frozen. Gov-os's contribution is to pull that
judgment OUT of the code and into recorded, governed law — which means the
sorting pass's real job is to locate every point where judgment currently hides
inside kernel code and make it an explicit governed decision (an S{u} or a human
gate), leaving the hot path pure S.

The pass therefore produces three things: the S-plane module list (what to
build as pure code), the governed-decision list (judgment lifted into law), and
exactly three human gates.

---

## 1. The S-plane — pure deterministic code (the running kernel)

Everything on the hot path. Each becomes a pure function/module with a contract;
none ever calls a model. Alignment class in brackets (identity / predicate /
band per SU §2.2).

| Operation | Cell | Class | Note |
|---|---|---|---|
| Append a record, assign seq/time | S | identity | the one write primitive |
| Reconstruct a cache from law+decisions+inputs | S | identity | the reconstruction invariant; must be pure |
| Round-trip check (delete cache, replay, diff) | S | identity | the standing audit test |
| Evaluate a scheduling policy against the runnable set | S | predicate | policy is recorded LAW; evaluation is code |
| Derive the run-queue / next task | S | identity | pure function of policy + admissions + inputs |
| Check a memory-budget predicate | S | predicate | budget is LAW; the check is code |
| Derive page tables from mapping decisions | S | identity | cache rebuild |
| Resolve a path through the derived directory tree | S | identity | view over file events |
| Content-address a write payload (hash) | S | identity | full-fidelity, never sampled |
| Validate an op at the gate (registered? params?) | S | predicate | unregistered = refuse |
| Record a refusal citing its rule | S | identity | refusal is itself an event |
| Translate a syscall into a gov-os operation | S | identity | the port boundary |
| Capture an interrupt/completion as an INPUT record | S | identity | external nondeterminism → record |
| Aggregate a sampled operation stream | S | band | observability, not audit |
| Settle a two-way ordering collision by built-ID | S | identity | the ruled tiebreak |
| Diff a shadow cache against Linux live state | S | predicate | the shadow/assume gate condition |

**Finding:** the entire running kernel is S. This is correct and is the source of
the speed answer — no judgment on the hot path means kernel-grade performance is
achievable; the governance lives in the LAW the S-plane reads, not in the S-plane
itself.

## 2. The governed-decision plane — judgment lifted into recorded law (S{u} / U{s})

These are the points where a conventional kernel hides a human's judgment inside
frozen code. Gov-os makes each an explicit governed decision: a recorded LAW
amendment or a rule-cited decision, set by an authority, changeable without a
recompile. Most are U{s}→S{u} (a human or a governance process decides; the
decision is captured as a structured, validated law record).

| Hidden judgment (conventional) | Gov-os governed form | Who decides |
|---|---|---|
| The scheduling algorithm baked into C | a scheduling-policy LAW record | governance (owner/committee) |
| Memory budget / overcommit ratios | budget LAW records | governance |
| Which driver is trusted in-kernel | a device-capability amendment (recorded) | governance — capability is law |
| OOM victim selection heuristic | an OOM policy rule; the kill is a cited decision | governance sets rule, kernel cites it |
| Permission model (uid/gid/caps) | permission LAW records | governance |
| Sampling rates for the STREAM class | calibration LAW (band thresholds) | governance, from evidence |
| Write-coalescing granularity | a coalescing-policy calibration | governance, from evidence |
| Snapshot/checkpoint cadence | checkpoint-policy calibration | governance, from evidence |
| Mount and namespace rules | mount LAW records | governance |

**Finding:** every one of these is a place a normal kernel took a judgment and
welded it shut. The sorting pass's real yield is this list — it is the inventory
of "law that was hiding in code," and lifting it out is precisely what makes the
kernel audit-grade and amendable. None of these is a per-operation model call;
all are slow-metabolism governance decisions captured as data.

## 3. The three human gates (never automated, never compressed)

Per SU Law 10 and §3, exactly three kinds of gate — and the pass confirms a
kernel needs exactly these three, no more:

1. **Definition gate** — what is this kernel/instance FOR; which policies, which
   compatibility target, which subsystems governed. Ruled before build. (The
   owner decisions in `03 §7`.)
2. **Calibration gate** — every band/budget/rate/threshold in §2: set from
   evidence, with a named owner, never an invented number. Fires whenever a
   calibration law is set or amended.
3. **Acceptance gate** — does a replaced subsystem faithfully pass? The
   shadow→assume switch (§03 §6) is an acceptance decision: a human rules that
   shadow-diff = ∅ under real load is sufficient to take authority. Runs raise
   the item; they never self-accept.

**Finding:** "more than three kinds of gate = misclassified governance as
judgment" (SU §3). The pass finds exactly three, which is the confirmation that
the governance/judgment split is clean.

## 4. What the pass changes about the build

- The hot path is pure S → build it as ordinary systems code; performance is a
  code problem, not an architecture risk.
- The governed-decision list (§2) is the actual novel build surface: the LAW
  record types, the amendment authority machinery, the calibration-with-evidence
  flow. This is where gov-os differs from every kernel — build it carefully.
- Three gates → three human-facing surfaces (definition brief, calibration
  queue, acceptance queue), each self-contained per SU Law 8.
- **Leftward compression applies to the governance, not the kernel:** over time,
  calibrations that were set by judgment and proven stable can demote to defaults
  (U{s}→S) — e.g. a sampling rate that never needs changing becomes a recorded
  constant. The hot path was always S; the governance layer compresses leftward
  as evidence accumulates. Governance debt (rule intake vs retirement) is the
  metric.

## 5. Honest caps

- This pass is SOURCE-DERIVED from the SU guide's method applied to the kernel
  design; the specific hidden-judgment inventory (§2) is INFERRED from how
  conventional kernels are built (trained knowledge, Estimate — High).
- The alignment classes in §1 are asserted from the nature of each operation; the
  formal proof that the ordering-settlement operation is identity-class under all
  interleavings is the deferred max-session proof (named in `03 §8`).
- No operation in the running kernel is U (model judgment) — and that is a
  designed invariant, not an omission: **if a future session finds itself putting
  a model call on the kernel hot path, it has misclassified governance as
  runtime.** Re-root at §0.
