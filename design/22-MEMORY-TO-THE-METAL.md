<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Memory Subsystem, To The Metal (the speed-tension proof-of-method)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** STANDS as the method proof, and its
> subject is now PARTLY BUILT: the memory core's GOVERNED surface is data-born (EP-04,
> the ceiling check reproduces `_resident` exactly). The to-the-metal SPEED story here —
> minor faults record nothing, record rate tracks decisions not accesses — is unproven
> in a real kernel and becomes live in Campaign 3 (DEPTH), where memory is the fourth
> subsystem to hollow out. This doc is that campaign's memory-stage brief.

**Status:** v0.1, 2026-07-12, xhigh. This works ONE hot subsystem — memory, the
hardest speed case — all the way down, to prove the speed-tension resolution
(03 §1–§2) actually holds where it is most doubted: page faults happen millions of
times a second, and "record everything" sounds fatal here. If the law/decision/
input/cache/stream split survives the memory subsystem, it survives everywhere.
This is the proof-of-method named in 03 §8. Labels per `00-READ-FIRST`.

---

## 1. Why memory is the acid test

Scheduling ticks and file writes are frequent; **page faults are the worst case**
— a busy process can take 10⁵–10⁶ minor faults per second, and a naive "append a
record per fault" would drown the log and destroy performance. If gov-os had to
record every fault, the whole architecture would be refuted at the metal. So the
question this document must answer without hand-waving: **which memory events are
recorded, which are not, and does the un-recorded majority stay reconstructible?**

The answer is the §2 classification applied ruthlessly. The punchline up front:
**the overwhelming majority of page faults record NOTHING**, because they apply a
mapping decision that was *already* recorded — they are cache fills, not new
governed acts. Only the rare fault that makes a genuinely new decision records.

---

## 2. Every memory event, classified (the whole subsystem, no gaps)

Applying 03 §2's five classes to memory, exhaustively:

| Memory event | Class | Recorded? | Why |
|---|---|---|---|
| `mmap`/`brk` — create a mapping | **DECISION** | yes, once | a new region granted against a budget; the governed act |
| `mprotect` — change region rights | **DECISION** | yes, once | a permission change on granted space |
| `munmap` — remove a mapping | **DECISION** | yes, once | a grant revoked |
| budget/policy amendment (cgroup limit, NUMA policy) | **LAW** | yes, rarely | a rule of rules |
| **minor fault** — page present in a *recorded* mapping, fill the PTE | **CACHE fill** | **NO** | applies the already-recorded `mmap` decision; derives PTE state; governs nothing new |
| **major fault** — fault-in from backing store | **INPUT (completion)** consumed by a CACHE fill | the *I/O completion* is an INPUT (already recorded for the device); the PTE fill is CACHE | the read was a device event; the fill applies the recorded mapping |
| **first-touch fault** on a lazily-granted region | **DECISION** (region materialised) | yes, once per region | the point the abstract grant becomes concrete resident space — a governed materialisation, once, not per page unless policy says so |
| hardware **accessed/dirty bit** set on access | **STREAM** | no | ephemeral hardware telemetry; surfaces only as cited eviction evidence |
| **eviction / page-out** under pressure | **DECISION** (embeds evidence) | yes, once | reclaim is a governed choice; cites the budget rule + the aggregate it acted on |
| **OOM kill** | **DECISION** (embeds evidence) | yes, once | the governed, rule-cited decision replacing the silent reaper |
| individual load/store to mapped memory | **STREAM** | no | raw operation flow; sampled in aggregate only |

**The load-bearing row is the minor fault.** It is a **CACHE fill**: the page
belongs to a region whose `mmap` DECISION is already in the record; the fault just
materialises a PTE the record already implies. Nothing governed happens, so
nothing is appended. That is why 10⁶ faults/sec cost zero records — they were
pre-authorised by one recorded mapping decision. The record count scales with
**governed decisions** (mappings, protections, evictions), not with **accesses**.

---

## 3. The hot path is pure S (no record, no model, no judgment)

Trace the minor fault, the highest-frequency path, to the metal:

1. CPU faults on virtual address `v` (no PTE).
2. The handler looks up `v` in the **derived mapping cache** (itself a fold of the
   recorded `mmap`/`munmap` decisions — §4).
3. If `v` is in a granted region with compatible rights → allocate/locate the
   physical frame, write the PTE, return. **Pure S**: a deterministic function of
   (recorded mapping decisions) + (the fault address). No append. No model call.
   No judgment. (Sorting-pass finding, `17-`: the running kernel is all-S.)
4. If `v` is *not* in any granted region → **`SIGSEGV`**, which is a governed
   refusal (recorded, cites the rule that granted no such region) — rare, and the
   only branch that touches the log.

The fault handler reads law-derived cache and applies it. It is exactly the
"hot-path state is a derived cache of recorded decisions" claim (03 §1), realised
for the busiest path in the kernel, with zero records on the common case.

---

## 4. Reconstruction holds (the invariant, checked for memory)

The invariant (03 §2): `memory-state = f(LAW, DECISIONS, INPUTS)`, with STREAM
never load-bearing. Verify it for every derived structure:

- **Mapping table / VMAs** = fold of `mmap`/`mprotect`/`munmap` **DECISIONS** under
  the current budget/policy **LAW**. Pure function of recorded data. ✔
- **Page tables (PTEs)** = derived from the mapping table + which pages are
  currently resident. Residency is itself derivable from grant decisions +
  eviction decisions + major-fault INPUT completions. So PTEs = f(DECISIONS,
  INPUTS). The *accessed/dirty bits* are STREAM — and they are **not needed for
  reconstruction**: on replay, treat all reconstructed pages as clean-and-cold and
  let the next access re-warm them. Losing the bits costs a little re-warming, not
  correctness. ✔ (This is the §2 honesty: hardware telemetry is ephemeral by
  design.)
- **Free-lists / frame allocation** = derived from grant/evict decisions. ✔

So `T-CACHE-KILL` (`19-` test): delete every page table, VMA tree, and free-list;
replay the mapping decisions, evictions, and I/O completions; reconstruct
identical memory *structure* (bit-identical mappings and residency; accessed/dirty
bits conservatively reset). The invariant holds for the memory subsystem. ✔

**The one subtlety, stated honestly:** the *contents* of anonymous pages that were
never written are zero by definition (reconstructible); the contents of
file-backed pages come from the file subsystem's content-addressed blobs
(reconstructible, 03 §4.3); the contents of anonymous pages that *were* written
and then swapped out are on the swap device, whose writes are file-subsystem
DECISIONS (content-hashed). So page *contents* are reconstructible through the
file subsystem's guarantees — memory does not separately need to journal them.

---

## 5. The eviction decision, fully worked (evidence without journalling access)

Eviction is where a DECISION legitimately depends on the un-recorded STREAM (which
page is coldest, learned from access telemetry). This is the `[AUDIT-FIX 3]` case,
worked concretely:

1. The `web` cgroup hits its `law:mem-budget:cgroup:web@3` ceiling (LAW).
2. The reclaim path must pick a victim. It reads the **access-frequency aggregate**
   — a sampled STREAM statistic (e.g. approximate-LRU over sampled accessed-bits),
   never a per-access journal.
3. It evicts the coldest page and appends **one `evict-page` DECISION** citing
   `law:evict-coldest@2` and **embedding the evidence it trusted**:
   `evidence_summary = {aggregate: "access-freq", window_ms: 200, value: "cold",
   coverage: "sampled@1/64}` (doc 11 §3.2 shape).
4. Replay reconstructs the eviction from this decision alone. The raw accesses are
   gone (they were STREAM), but **the decision is audit-complete**: "why was this
   page reclaimed?" → `evict-coldest@2`, cold per this cited aggregate — forever.

This is the general pattern for *every* decision that consumes telemetry: **sample
the stream, but freeze the evidence you acted on into the decision.** The audit is
complete at the decision; the stream stays cheap. One record per eviction, not one
per access.

---

## 6. The numbers (why this is not just clean but fast) — Estimate, Medium

Order-of-magnitude sanity, to show the record rate is bounded and small:

- Minor faults: ~10⁶/sec → **0 records** (CACHE fills). The dominant cost vanishes.
- Mappings (`mmap`/`munmap`): ~10²–10³/sec for a busy process → ~10²–10³ records/sec.
- Evictions under pressure: bounded by reclaim rate, ~10³–10⁴/sec worst case, each
  one record with an embedded aggregate.
- Budget/policy amendments: ~minutes-to-hours apart → negligible.

So the memory subsystem's record rate tracks **decisions (~10³–10⁴/sec)**, four to
six orders of magnitude below the **access/fault rate (~10⁶–10⁹/sec)**. The append
log sees governed acts, not machine activity. This is the speed-tension resolution
made quantitative: recording scales with governance, which is slow, not with
operation, which is fast. *(Estimate — Medium: rates are representative
orders-of-magnitude from trained knowledge of Linux workloads, not measured on
gov-os, which does not yet run. The claim proved is structural — faults are CACHE
fills — the numbers only illustrate its size.)*

---

## 7. What this proves for the whole architecture

Memory was the acid test (§1). It passes: the busiest path in the kernel records
nothing because it applies already-recorded decisions; reconstruction holds;
telemetry-dependent decisions freeze their evidence; the record rate is bounded by
governance, not by operation. **If the hardest subsystem survives the split, the
split is sound** — scheduling (ticks are STREAM applying recorded policy), files
(content is DECISION-class, already worked in 03 §4.3), devices, and comms are all
*easier* cases of the same three moves shown here:

1. pre-authorise with a recorded DECISION,
2. serve the hot path as a pure-S CACHE fill that records nothing,
3. when a decision needs telemetry, freeze the evidence into the decision.

**Honest caps:** this is a design-level proof-of-method, not a running benchmark
(no code exists). The structural claims (fault = CACHE fill; reconstruction from
decisions; evidence-frozen evictions) are derived from 03 §1–2 and doc 11; the
performance numbers are illustrative orders of magnitude (Estimate — Medium). The
swap-content reconstruction (§4) leans on the file subsystem's content-addressed
guarantee — a cross-subsystem dependency, correct but worth a conformance test
(`19-` T-CACHE-KILL extended to a swap cycle). A to-the-metal treatment of a
*second* subsystem is not needed for architectural completeness — the method is
proved general here.
