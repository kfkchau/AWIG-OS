<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Seam Contracts (each contract doubles as the seam's test)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** One seam is now BUILT: S3 (scheduled
> execution) was fulfilled by EP-07's obligation executor — clock-as-sensor, recorded
> ticks, due() from the record, firing through the gate with derived fired-evidence;
> T-OBLIGATION-FIRES is green in the suite. S5 (multi-writer ordering) stays deferred
> AS RULED (single writer, ordering fields carried) until Campaign 6. The remaining
> contracts stand and feed Campaign 3. Live canon controls on conflict.

**Status:** v0.1, 2026-07-12. **Route-A (hollow-out) assumed throughout** (02 §9;
03-TARGET §7 — start as Linux, replace subsystems behind unchanged interfaces).
Labels per 00-READ-FIRST §6: SOURCE-DERIVED (cite) / INFERRED (from what) /
PROPOSED (cost if wrong) / trained knowledge (flag). This is systems-engineering
documentation for an event-sourced kernel — no code.

This document writes the handshake contract for every joint where two gov-os
subsystems meet, and each contract is written so it doubles as that seam's test.
For each joint it names the two sides, states EXACTLY what crosses (the data
shape or the call), what validates the crossing, what happens on rejection, and
the acceptance test — the observation that tells you the seam works. The house
build rule sets the form: **contract before stages** — the invariant is fixed
first and no stage is built until the contract holds (02 §9 "contracts before
stages, worst seam first"; S/U rebuild step 7, "contracts for every seam,
connect the worst seam first"). Six seam contracts are specified, each
cross-referenced to the S1–S10 work packages of 02 §9. Every one reduces to a
law already proven in the estate: the record decides, the cache is discardable,
diff = ∅ is the oracle.

---

## How to read a seam contract (the fixed shape)

Every seam below is written in one shape, and the shape is the point — the
contract is stated *before* the stages, so the test exists before the build:

- **Sides** — the two subsystems that meet at this joint.
- **Contract (stated first)** — the invariant that must hold across the joint,
  independent of how either side is built. This is the law; it is fixed before
  any stage.
- **What crosses** — the exact data shape or call that passes the joint, in both
  directions.
- **What validates it** — the check applied at the joint before the crossing is
  honoured.
- **On rejection** — what the joint does when validation fails. In gov-os a
  rejection is never a dropped call: it is itself a recorded act (a refusal is a
  record, citing its rule).
- **Acceptance test** — the observations that prove the seam works. These ARE the
  seam's conformance suite; passing them is what "the seam is built" means.
- **Stages (built only after the contract holds)** — the build order, listed last
  by rule, never before the contract.

Cross-reference map to 02 §9 seams: SC1 → S1+S2, SC2 → S4 (+round-trip law,
02 §1.3), SC3 → S7 (+§2 reconstruction invariant, 03-TARGET), SC4 → 03-TARGET §6,
SC5 → 03-TARGET §5 (the ports), SC6 → S3+S5 (+§2 INPUT class, 03-TARGET).

---

## SC1 — Gate ↔ Store  (S1 store contract + S2 gate everywhere)

**Label:** SOURCE-DERIVED (02 §1.1 envelope, §1.2 gate; twc `registry.js` +
`errors.js`; DESIGN-CONCEPTS P3 "the bank has no counter").

### Sides
- **Gate** (L1) — the syscall boundary; the single write path; twc
  `registry.execute()` generalised.
- **Store** (L0) — the append-only record; the definitive; envelope §1.1.

### Contract (stated first)
Every mutation of governed state crosses this joint as a *registered operation*
and produces *exactly one appended record* — either the domain record the op
requested, or a refusal record. There is no third outcome. There is no write path
to the Store that does not pass the Gate (S2: zero writes outside `execute()`).
A refusal is not the absence of a record; it is a record.

### What crosses
- **Gate → Store (request):** an `OpRequest`:
  ```jsonc
  { "op_name": "…",            // MUST be a registry member
    "params": { … },           // validated against the op's schema
    "actor": "…",              // who is acting
    "asserted_by": "…", "confidence_tier": "…",
    "provenance": { … },       // sight-gate input: what the writer could read
    "submission_time": "…",    // monotonic per origin, never globally ordered
    "origin": { "subsystem_id": "…", "built_id": 0 } }  // built ID = S5 tiebreak
  ```
- **Store → Gate (success):** the appended `Record` (envelope §1.1) with `seq`
  and `record_time` minted at append — the sole total-order anchor.
- **Store → Gate (refusal):** an appended `Record` with `action` = the attempted
  operation, `refused: true`, and `rule_cited` (the rule that refused), plus the
  caller-facing error (errno-equivalent) — the guards `refuse()` idiom, in the
  doc-12 refusal shape (glossary `20-` controls the names).

### What validates it
In order, before the handler runs: (1) **registry membership** — unknown
`op_name` is a Closure Hit (does not exist; registry enumeration IS the
completeness guarantee); (2) **param schema** — params validated before the
handler is invoked; (3) **authority** — the actor's authority ladder permits the
op; (4) **sight-gate** — provenance shows the writer could read what the op
consumes (you cannot consume what you could not read, 02 §3).

### On rejection
The Gate appends a refusal record citing the failing rule (Closure Hit for
unknown op; schema rule for bad params; authority rule; sight rule), returns the
errno-equivalent to the caller, and **does not invoke the handler**. The refusal
is durable and queryable like any record. Referral fires on a Closure Hit.

### Acceptance test
1. Registered op, valid params → **exactly one** appended domain record; `seq`
   strictly greater than the prior; `record_time` present.
2. Unknown op → **zero** domain records, **exactly one** refusal record with
   `action:REFUSE`, `rule_id` set, and a referral event; caller gets the
   errno.
3. Invalid params → refusal appended *before* the handler runs — assert the
   handler was never entered (probe/counter reads zero).
4. **S2 grep test:** no write reaches the Store except through `execute()` — the
   one grep-verifiable write path (02 §3, "keep the S-plane that small forever").
5. **S1 contract suite:** all four estate stores (twc, cgl, venn2, 3d-auto) pass
   the same suite; round-trip CI green (02 §9 S1 acceptance).

### Stages (built only after the contract holds)
Kernel store (jsonl adapter) + registry + `OpError` type → boot the twelve-
template foundational import pack → lift cgl and every family onto the one gate
(S2) → prove zero-writes-outside-ops across families.

---

## SC2 — Store ↔ Views  (S4 governed checkpoint + the round-trip law, 02 §1.3)

**Label:** SOURCE-DERIVED (02 §1.3 round-trip law; §1.5 snapshot law; 03-TARGET
§1.3 replay guarantee; venn2 export→wipe→import→byte-identical).

### Sides
- **Store** (L0) — the append log; the only thing that is truth.
- **Views** (L2) — the derivation engine; folds events → all current state;
  universal `asOf`; caches are memoised and discardable.

### Contract (stated first)
**The round-trip law:** delete every derived artifact, replay the record, and the
reconstruction is identical — `diff = ∅`. All current state is a pure function of
the record; a view is never truth and is never referenced as truth. A snapshot is
a regenerable cache citing its log `seq`, validated by `diff = ∅`, never
referenced as truth (02 §1.5). Killing every cache changes nothing.

### What crosses
- **Store → Views (invalidation):** on append, an **append-generation** bump
  (keyed on `seq`). Views memoise on the generation; a bump invalidates exactly
  the affected memos. No state is pushed — the view *reads* the log (or a
  snapshot citing `seq` + the tail past it).
- **Views → Store (nothing that is truth):** views write only *derived* artifacts
  (snapshots, memos) that cite the `seq` they were computed from. They never
  originate governed state; that path is SC1.

### What validates it
The round-trip oracle: `replay-from-genesis` reconstructs the view; a snapshot is
accepted only if `replay-from-checkpoint ≡ replay-from-genesis` (`diff = ∅`,
S4). `asOf(T)` must answer "what was visible at T" — computed, not stored.

### On rejection
If `diff ≠ ∅`, the cache/snapshot is **rejected as truth**: discarded, recomputed
from the log, and the divergence is recorded (this is also FAILURE-BOOK FB1). A
snapshot that cannot reproduce its cited `seq` is never promoted. The log always
wins — the pathology gov-os refuses is "cache kept, ledger burned" (03-TARGET §0).

### Acceptance test
1. Append → the affected view reflects it at the next read (generation
   invalidation works); unaffected views do not recompute.
2. **Round-trip:** export → wipe all derived → import → **byte-identical** (venn2
   already runs this continuously).
3. **Checkpoint equivalence (S4):** `replay-from-checkpoint ≡
   replay-from-genesis` under `diff = ∅`.
4. **`asOf`:** `asOf(T)` returns the state visible at T, for arbitrary past T.
5. **Kill-the-cache:** delete every derived artifact mid-run → outputs unchanged
   after recompute (02 §10 thin-slice acceptance, "killing every cache changes
   nothing").

### Stages (built only after the contract holds)
View machinery + kernel views (boot state, obligations, visibility, config) →
generation-keyed memo → `asOf` → snapshot citing `seq` (S4) → wire the round-trip
diff into CI as a standing gate.

---

## SC3 — Subsystem-cache ↔ Record  (the reconstruction contract; S7 purity)

**Label:** SOURCE-DERIVED (03-TARGET §2 five classes + reconstruction invariant;
02 §9 S7 purity gates; determinism ledger, S/U guide §5 "same input hash → same
output hash, alarm on divergence").

### Sides
- **Subsystem cache** (L4) — a department's hot structure: run-queue, page
  tables, fd/dentry cache, device-binding table, comms queue-state.
- **Record** (L0) — partitioned by class into LAW, DECISIONS, INPUTS, and
  (non-load-bearing) STREAM.

### Contract (stated first)
**The reconstruction invariant** (03-TARGET §2, in one line): governed state =
`f(LAW, DECISIONS, INPUTS)`; STREAM informs humans and calibration, never the
function. Every subsystem cache reads ONLY from LAW + DECISIONS + INPUTS; it
never reads STREAM back into itself. A crash loses only caches; recovery is
recompute. Where a decision depended on stream evidence, the *decision record
already embedded the evidence summary it acted on* (AUDIT-FIX 3) — so replay
needs no stream present.

### What crosses
- **Record → cache (rebuild):** the pure fold `cache = f(LAW, DECISIONS,
  INPUTS)`. On boot or after corruption, the cache is regenerated by replaying
  exactly these three classes.
- **cache → Record (emit only):** the cache emits STREAM aggregates (dispatch
  counts, access statistics, throughput) for observability. This is one-way:
  STREAM leaves the cache and never returns into it.

### What validates it
The **purity gate** (S7 — venn2's 15-line import-line test generalised): assert
statically that no read path exists from STREAM into any cache. The **determinism
ledger**: wipe the cache, replay `(LAW, DECISIONS, INPUTS)`, hash the result;
same input hash → same output hash, alarm on divergence.

### On rejection
If a cache is found to read STREAM (purity gate fails) the build is rejected — the
layering rule is executable, not advisory. If a replayed cache ≠ the prior cache
under identical `(LAW, DECISIONS, INPUTS)`, that is a determinism-ledger
divergence → alarm + recorded divergence (FAILURE-BOOK FB1/FB9), and the record
wins.

### Acceptance test
1. **Per subsystem:** wipe the cache, replay LAW+DECISIONS+INPUTS → the cache
   reconstructs **identically** (determinism ledger green).
2. **Purity (S7):** the import-line test finds zero STREAM→cache reads in every
   family; layering is executable everywhere.
3. **Evidence-embedding:** a decision that cited an aggregate (e.g. "evicted X
   under rule R citing aggregate A") replays correctly *with the raw stream
   absent* — the audit is complete at the decision (AUDIT-FIX 3).
4. **Class discipline:** every piece of kernel state is assigned exactly one of
   LAW / DECISION / INPUT / CACHE / STREAM; nothing load-bearing lives in a
   sample (the honest-observability boundary, 03-TARGET §1.5).

### Stages (built only after the contract holds)
Classify each subsystem's state into the five classes → build the fold
`f(LAW,DECISIONS,INPUTS)` per subsystem → wire the purity gate (S7) into CI →
stand up the determinism ledger keyed by module version.

---

## SC4 — Shadow ↔ Authoritative  (the replacement handoff; 03-TARGET §6)

**Label:** SOURCE-DERIVED (03-TARGET §6 shadow→assume→retire; §7 Route-A
cost-if-wrong). PROPOSED where it names order/fallback (03-TARGET marks §6 order
PROPOSED).

### Sides
- **Shadow subsystem** (governed) — runs beside Linux's, recording LAW,
  DECISIONS, INPUTS and deriving its caches; **not yet authoritative**.
- **Authoritative subsystem** (Linux's live one) — holds authority behind the
  unchanged interface until the switch.

### Contract (stated first)
Replacement is a three-phase governed handoff behind a **constant interface**
(L5 held fixed): **shadow → assume → retire**. The shadow's derived state is
diffed against Linux's live state **continuously and under real load**; the
governed subsystem takes authority **only when `diff = ∅` holds under real
load**; and at every intermediate step the machine is a working, shippable kernel
with strictly more auditability than the day before. The interface never moves;
userland never notices.

### What crosses
- **Continuous:** a live **state diff** at the interface's observable surface —
  the shadow's derived state vs Linux's live state (the round-trip law applied
  live).
- **The switch (assume):** a recorded `assume-authority` DECISION citing the diff
  evidence — authority passes to the governed subsystem; Linux's version becomes
  the shadow.
- **The switch (retire):** a recorded `retire` DECISION — Linux's version is
  removed.

### What validates it
`diff = ∅` sustained **under real load** is the sole gate on `assume`. The syscall
conformance suite (SC5) must be green across the switch — **semantic identity**,
not timing identity. `assume` cites *observed* evidence, never intention
(scar-tissue: log green only after running).

### On rejection
If the shadow **diverges during replacement** (`diff ≠ ∅`): **halt the assume,
keep Linux authoritative, record the divergence** (what diverged, at which
interface point, under what load) — this is FAILURE-BOOK FB3, and it is the
falsification probe working, not a failure of method. If a hot subsystem cannot
be inverted inside Linux's frame, fall back to **Route B for that subsystem
only** (§7 cost-if-wrong; the ports contract makes the fallback local, not
total).

### Acceptance test
1. `diff = ∅` is **sustained under real load** before `assume` can fire (a single
   green sample is insufficient — the gate is duration under load).
2. The `assume` switch is **one recorded decision** citing the diff evidence;
   the `retire` is a second recorded decision.
3. Post-`assume`, the syscall conformance suite (SC5) is still green — userland
   sees no change.
4. **Divergence halts automatically:** inject a divergence into the shadow →
   `assume` is blocked, Linux stays authoritative, a divergence record exists
   (FB3 acceptance).
5. **Order (PROPOSED):** files first (smallest inversion), then devices, comms,
   memory, scheduling last (03-TARGET §6) — each replaced only after the prior
   pattern proved.

### Stages (built only after the contract holds)
Stand the shadow beside Linux (record + derive, no authority) → wire the live
diff → run under real load → `assume` on sustained `diff = ∅` → `retire` →
repeat per subsystem in the proposed order.

---

## SC5 — The Port Boundary  (syscall → gov-os operation; 03-TARGET §5)

**Label:** SOURCE-DERIVED (03-TARGET §5 ports; §1.4 definitional ordering).
trained knowledge (flag): the Linux syscall surface's shape and the
gVisor-Sentry / Starnix reimplementation precedent (03-TARGET §5, Estimate —
High).

### Sides
- **Syscall surface** (L5, userland-facing) — numbers, signatures, semantics,
  errno behaviour; plus `/proc`,`/sys` and the driver-model boundary.
- **Gate** (L1) — the registered-operation boundary (SC1).

### Contract (stated first)
**Semantic identity:** every syscall that touches a rebuilt subsystem behaves
identically — same behaviour, same errors, same *visible ordering guarantees*.
A rebuilt subsystem passes iff the standing syscall conformance suite is green.
Timing and performance are **not** promised identical (they never could be), and
`/proc`,`/sys` reflect gov-os's true derived state. The added capability
(replayable "why") is invisible to userland.

### What crosses
- **Userland → Gate (inbound):** a syscall `(number, signature, args)` →
  translated to a gov-os `OpRequest` (SC1) at the Gate.
- **Gate → Userland (outbound):** the op result → translated back to the
  syscall's return value / errno. A gov-os refusal maps to the errno userland
  expects **and** is additionally recorded as a rule-cited refusal (SC1).
- **`/proc`,`/sys` (inbound read):** rendered as computed views over the record —
  "what they always morally were" (03-TARGET §5).
- **Driver-model boundary:** existing drivers bind through a shim (SC-adjacent;
  see SC4's device order and FAILURE-BOOK FB5).

### What validates it
The **syscall conformance suite** — the standing test of §5. Semantic identity is
the pass condition. Visible ordering guarantees hold because the intake pipeline's
order is *definitional, not descriptive* (03-TARGET §1.4): whoever lands first IS
first, by law — this is why cross-core races are settled, not merely observed.

### On rejection
A syscall that maps to **no registered op** is an unregistered operation → a
Closure Hit at the Gate (SC1): it **fails closed**, returns the correct errno to
userland, and appends a rule-cited refusal (FAILURE-BOOK FB8). A conformance-suite
red on any syscall blocks that subsystem's `assume` (SC4). Never widen the errno
contract silently.

### Acceptance test
1. The syscall conformance suite is **green per subsystem** (semantic identity).
2. A refusal returns the errno userland expects **and** appends a rule-cited
   refusal record — the audit win is invisible to the caller.
3. `/proc/*`,`/sys/*` render as computed views from the record (asOf-capable),
   reflecting gov-os's true derived state.
4. An **unmodified userland binary** runs unchanged — the browser is the stress
   case (it depends on `shm`/`MAP_SHARED`, honoured at the port; 03-TARGET §4.5).
5. **Ordering:** two racing syscalls receive a definitional order from the intake
   pipeline (03-TARGET §1.4); the visible ordering guarantee matches Linux's.

### Stages (built only after the contract holds)
Translation shim (syscall → `OpRequest`, result → errno) → the conformance suite
as the standing gate → `/proc`,`/sys` view catalogue (named-not-hidden as
not-yet-done, 03-TARGET §8) → driver shim → run an unmodified binary end-to-end.

---

## SC6 — INPUT Capture  (interrupt / io-completion → input record; S3 + S5)

**Label:** SOURCE-DERIVED (03-TARGET §2 INPUT class + AUDIT-FIX 1; 02 §1.4
clock-as-sensor + §9 S3 RULED lawful; §9 S5 ordered intake pipeline; determinism
ledger, S/U).

### Sides
- **External world** — interrupts, I/O completions, timer ticks, packet
  arrivals, faults; happenings the kernel does not author.
- **Record** (L0) — the INPUT class; external nondeterminism enters here.

### Contract (stated first)
**The determinism boundary:** replay is deterministic **relative to the recorded
input stream** — never "free" (AUDIT-FIX 1). Therefore **every state-changing
arrival MUST become an INPUT record before the decision that consumes it.** Raw
high-frequency content is sampled (STREAM); the state-changing arrival is
recorded (INPUT). The clock-as-sensor ruling holds: a tick is recorded sensor
input, and what fires is still decided only by the record (02 §1.4; S3 RULED
lawful).

### What crosses
- **World → Record (inbound):** a state-changing arrival → an INPUT `Record`
  carrying one of the input verbs (`irq-arrival`, `io-completion`, `timer-tick`,
  `packet-arrival` — glossary `20-` §2):
  ```jsonc
  { "action": "irq-arrival",   // the specific input verb, never a generic tag
    "actor": "…",              // the device / source
    "occurrence_time": "…",    // when it arrived in the world
    "record_time": "…",        // minted at intake — the total-order anchor
    "submission_time": "…",    // monotonic per origin
    "origin": { "subsystem_id": "…", "built_id": 0 },  // S5 tiebreak
    "payload_ref": "…" }       // hash; raw high-frequency content sampled
  ```
- **All arrivals converge on ONE ordered intake pipeline** (S5): time-hash order;
  a two-entry collision broken by the writing sources' built IDs (RULED
  2026-07-12).

### What validates it
Every state-changing arrival appears as **exactly one** INPUT record **before** its
consuming decision. The **determinism ledger** is the oracle: replay the recorded
INPUTs and the derived decision stream must match the live one (same input hash →
same output hash). Ordering is validated by S5's conformance test: round-trip
`diff = ∅` under interleaved multi-writer load.

### On rejection
An arrival that **cannot be recorded** (intake saturated) must **not** be silently
dropped — a silent drop is a determinism break (FAILURE-BOOK FB9). Prefer
**backpressure**: a recorded refusal / halt beats a lost input. A drop that does
occur is detected — not absorbed — by the determinism ledger (live vs replay hash
divergence).

### Acceptance test
1. Every state-changing arrival appears as **exactly one** INPUT record **before**
   its consuming decision (assert ordering: record precedes decision `seq`).
2. All arrivals enter the **one** intake pipeline; ordering is time-hash with
   built-ID tiebreak; round-trip `diff = ∅` under interleaved load (S5
   acceptance).
3. **Replay reproduces live:** replaying recorded INPUTs regenerates the live
   decision stream (determinism ledger green).
4. **Negative test:** a deliberately dropped input surfaces as a ledger
   divergence (live hash ≠ replay hash) localised to a `seq` range — the drop is
   *detected*, never silent (FB9 acceptance).
5. **Sensor-not-scheduler:** an 18-month review trigger fires from replay alone
   (S3 acceptance) — proving elapsed record-time drives obligations, no
   wall-clock scheduler.

### Stages (built only after the contract holds)
Tick/interrupt/completion → INPUT record adapters → the one ordered intake
pipeline (S5) → the determinism ledger keyed by module version → S3 elapsed-time
obligation predicates on top.

---

## Coverage statement (what this document does NOT cover)

- **Not covered here — now existing as siblings** (written after this doc): the
  syscall conformance map (`10-`), the driver-shim detail (`24-`), and the
  `/proc`/`/sys` view catalogue (`13-` §8); SC5's standing gate is those documents.
- **Not covered here — now proved:** the ordering-determinism proof exists at
  `21-` (deterministic injective key over recorded fields, every interleaving).
  SC6 *uses* the ruling; `21-` proves it.
- **Not covered:** physical capacity and replay-cost thresholds — OPEN owner
  question (02 §1.5 assessment B7); see FAILURE-BOOK FB6/FB7. The contracts here
  are correctness contracts, not cost contracts.
- **Assumption:** Route-A (hollow-out) throughout. Under Route B the SC4 handoff
  applies per-subsystem at the compat-layer seam instead of in-place; the other
  five contracts are route-independent.

**One-line invariant across all six seams:** the record decides, the cache is
discardable, `diff = ∅` is the oracle, and a rejection is always a record.
