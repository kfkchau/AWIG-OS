<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Ordering Determinism (the keystone proof)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** STANDS, and mostly DORMANT: the proof
> covers MULTI-writer interleaving (seam S5), which the campaign deferred as ruled — the
> kernel is single-writer today, so the determinism the suite proves (kill-everything,
> replay, identical) is the simpler single-writer case. This proof becomes live and
> load-bearing in Campaign 6 (FEDERATION), where real concurrent writers arrive. Its
> ordering key derivation is unchanged and waiting.

**Status:** v0.1, 2026-07-12, xhigh. This is the proof the whole audit contract
leans on (03 §1.3–1.4): that the intake pipeline yields **deterministic replay
under every interleaving**, not just the pairwise case. Doc 11 §1.2 fixed the
two-way tiebreak and flagged the general (≥3-way, same-origin) case as deferred;
this document closes it. It is a rigorous hand proof; a machine-checked version
is the optional max/formal-tools hardening (noted §6). Labels per `00-READ-FIRST`.

---

## 1. What must be proved (the claim, stated precisely)

The pipeline receives records submitted concurrently by many **origins** (each
subsystem, and one buffer per CPU). Physical arrival order is a race — it differs
run to run. The audit contract requires (03 §1.3): **replaying the recorded
records reconstructs one and the same total order, every time, on any machine,
independent of the physical race.**

Formally: let `R` be the set of recorded records. We must exhibit an ordering key
`K : R → totally-ordered domain` such that

1. **(Determinism)** `K(r)` is computed only from fields *recorded in `r`* — never
   from physical arrival time or run-specific state; and
2. **(Totality)** `K` is *injective* on `R` — no two distinct records share a key —
   so sorting `R` by `K` yields exactly one order.

If such a `K` exists, replay = "sort the recorded records by `K`", which is a pure
function of the records, so it is identical on every replay. That is the claim.

---

## 2. The fields available (from doc 11 §1.1, all recorded)

Each record `r` carries, among others:

- `record_time(r)` — timestamp the sequencer stamped; the **time-hash** buckets
  records by this. Write `bucket(r)` for its hash bucket.
- `origin(r)` — the submitting origin, carrying `built_id(origin)` = the origin's
  **creation order**, assigned once at construction, unique and fixed.
- `submission_time(r)` — the origin's own timestamp, **monotonic per origin**
  (doc 11 §1.1: strictly increasing within one origin, never globally ordered).

Two facts we will use, both already established in the architecture, not assumed
here:

- **F1 (built_id is a strict total order on origins).** Creation order is unique
  and fixed (doc 11 §1.2). So `built_id` linearly orders all origins.
- **F2 (submission_time is strictly monotonic per origin).** Within one origin,
  successive submissions carry strictly increasing `submission_time` (doc 11
  §1.1). So no origin emits two records with equal `submission_time`.

---

## 3. The ordering key

Define, for every record `r`:

```
K(r) = ( bucket(r) , built_id(origin(r)) , submission_time(r) )
```

ordered lexicographically (compare bucket first; ties broken by built_id; those
ties broken by submission_time).

This is exactly doc 11 §1.2's rule *generalised*: the two-way case "same bucket →
lower built_id first" is the first two components; the third component
(`submission_time`) is the previously-deferred within-origin tiebreak, and it was
already recorded and already monotonic — nothing new is introduced (minimality
gate satisfied: no new field, no new primitive).

**Determinism of K.** Every component — `bucket(r)` (a hash of the recorded
`record_time`), `built_id` (recorded in `origin`), `submission_time` (recorded) —
is a function of fields *in the record*. None reads physical arrival order or any
run-specific state. So requirement (1) of §1 holds by construction. ∎(det)

---

## 4. K is injective (the totality proof, by exhaustion of collision cases)

Take two distinct records `r ≠ s`. We show `K(r) ≠ K(s)` in every case.

**Case A — different buckets.** `bucket(r) ≠ bucket(s)` ⟹ the first component
differs ⟹ `K(r) ≠ K(s)`. ✔

**Case B — same bucket, different origins.** `bucket(r) = bucket(s)` but
`origin(r) ≠ origin(s)`. By **F1**, `built_id(origin(r)) ≠ built_id(origin(s))`
⟹ the second component differs ⟹ `K(r) ≠ K(s)`. ✔ *(This is the pairwise rule of
doc 11 §1.2, and note it already resolves an N-way collision among distinct
origins: any number of colliding records from distinct origins are totally
ordered by their distinct built_ids.)*

**Case C — same bucket, same origin.** `bucket(r) = bucket(s)` and
`origin(r) = origin(s)`. Since `r ≠ s` are two distinct records from the *same*
origin, by **F2** their `submission_time` values are distinct ⟹ the third
component differs ⟹ `K(r) ≠ K(s)`. ✔ *(This is the case doc 11 §1.2 deferred. It
is closed by F2: an origin cannot submit two records with equal submission_time.)*

Cases A, B, C are exhaustive (either buckets differ, or they match and origins
differ, or both match). In all three, `K(r) ≠ K(s)`. Therefore `K` is injective on
`R`. ∎(inj)

**Conclusion.** `K` is a deterministic, injective key ⟹ sorting `R` by `K` is a
total order that is a pure function of the records ⟹ replay reconstructs one and
the same order on every run and every machine. The claim of §1 holds, for **every
interleaving and any number of colliding records**, not merely the two-way case. ∎

---

## 5. Two systems obligations the proof exposes (honest, and both discharge-able)

A clean mathematical key is necessary but not sufficient for a running pipeline.
The proof surfaces exactly two real obligations; both are standard and are named
here so the build owns them rather than discovering them.

**O1 — the sequencer's `seq` must equal K-order.** `seq` (doc 11 §1.1) is the
authoritative total order used at runtime. For replay to match runtime, the
sequencer must assign `seq` in `K`-order. Since `K` is a total order on whatever
set of records the sequencer has, the sequencer sorts its pending intake by `K`
and assigns `seq` in that order. Runtime order = K-order = replay order. ✔

**O2 — bucket finalisation (the watermark).** The sequencer cannot assign `seq`
for `bucket b` until it knows no further record will land in `b`. This is the
standard event-time watermark problem. Discharge: a bucket `b` closes once every
origin has submitted a record with `bucket > b` **or** declared idle-past-`b`
(a heartbeat). Because there are finitely many origins and F2 makes each origin's
stream monotonic, every bucket closes in bounded time under liveness (each origin
eventually advances or heartbeats). This is a **liveness** property (records get
ordered promptly); the **safety** property (the order, once assigned, is the
deterministic K-order) is what §4 proved and does not depend on O2's timing —
a slow origin delays finalisation, it never changes the resulting order. ✔

The safety/liveness split is the important honesty: **§4 guarantees the order is
always the right one; O2 only governs how quickly it is committed.** A late record
(an origin that submits into an already-closed bucket) is handled by the failure
book (`15-` FB9, input-event-lost / late-arrival): it is recorded as an
out-of-window arrival citing its true bucket, and the determinism ledger flags the
watermark violation — it is never silently reordered.

---

## 6. What this proves, and what would harden it further (honest caps)

**Proved (rigorous hand proof):** a deterministic injective ordering key exists
over the recorded fields, covering every interleaving and every collision
multiplicity; replay is therefore a pure function of the records. The two-way
tiebreak of doc 11 §1.2 is the Case-B special case; the deferred general case is
closed by Case C via F2. **The keystone the audit contract leaned on is now
proved, not assumed.**

**Assumptions made explicit (each already an architecture fact, not new):** F1
(built_id total order on origins), F2 (submission_time monotonic per origin). If
either is ever violated by an implementation — e.g. an origin that can emit two
records with equal submission_time, or reused built_ids — the proof breaks exactly
there, and the determinism ledger (`15-` FB9) is the detector. So the proof also
tells the build what invariants the store contract (seam S1) must enforce: **S1
must guarantee F1 and F2.** That is the proof's build output.

**Optional hardening (max / formal tools, not required for architectural
completeness):** transcribe §3–§4 into a proof assistant (the injectivity argument
is a three-case decision over a lexicographic triple — well within TLA+/Coq/Lean
reach) and model-check O2's watermark for liveness under an adversarial scheduler.
This would convert the rigorous hand proof into a machine-checked one. It changes
nothing in the result; it removes the "trust the author's case analysis" residue.

**Trained-knowledge flag:** the watermark/event-time framing in O2 is standard
stream-processing knowledge (Estimate — High); the key `K` and the three-case
proof are derived here from the architecture's own recorded fields.
