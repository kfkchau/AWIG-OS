<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Capacity Economics (the grow-forever question, costed for ruling)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** STANDS, UNBUILT: the append-only store
> grows forever by design and the horizons remain an owner calibration from evidence
> (mechanisms specified here). Nothing in campaigns 1–2 needed them (test stores are
> ephemeral). Becomes live when real custody generates real volume — Campaign 3 (DEPTH)
> at the earliest, calibrated with Campaign 7's scale evidence. GS-13 erasure (referenced
> here) is built in Campaign 4 (PROOF) as its own destruction ceremony.

**Status:** v0.1, 2026-07-12, xhigh. This closes the one OPEN design question the
review kept flagging (assessment B7; failure book FB6): an append-only record
grows forever, but disks are finite. The growth *law* is derived (03 §2: the
record grows with governed decisions, not operations — proved bounded for the
hot case in `22-` §6). What is NOT yet ruled is the *physical* answer: what
happens as the log approaches media limits. This paper frames the options,
costed, for an owner ruling — it does not invent a value. Labels per `00-READ-FIRST`.

---

## 1. Why grow-forever is a real position, not an oversight

First, the honest defence of doing nothing: the record grows only with **governed
decisions** — mappings, grants, binds, policy amendments, file/comms events — not
with operations (faults, accesses, ticks, packets), which are STREAM and never
appended (`22-` proves this for memory: ~10³–10⁴ records/sec, not ~10⁶–10⁹). File
*content* is content-addressed, so identical bytes are stored once. So the growth
rate is far below naïve intuition. For many deployments (a workstation, an
appliance, a bounded-lifetime service) grow-forever on a large disk is genuinely
fine for the machine's life, and it buys the strongest property gov-os has:
**complete history, no horizon, asOf to genesis.**

But "fine for many" is not "fine for all," and a kernel must design for the
stretch (the owner's own rule). A long-lived server, a high-decision workload, or
a regulated retention limit forces the question. So this paper exists.

---

## 2. The three levers (what can even be done to an append-only log)

Only three things can bound an append-only store's physical footprint without
lying about the record:

1. **Move old records to cheaper media** (tiering) — footprint on fast media
   bounded; nothing lost; derivability preserved at a fetch cost.
2. **Summarise a prefix into a checkpoint and drop the raw prefix** (compaction) —
   footprint truly bounded; the checkpoint becomes a new genesis; deep history
   *before* the checkpoint is forfeited (a governed, recorded loss).
3. **Erase specific old records** (GS-13 scheduled erasure) — targeted, for
   retention-limit compliance; the scar survives; regenerability of the erased
   items forfeited knowingly.

These are not exclusive; the recommended posture (§4) uses all three at different
horizons. Each is examined below with its cost-if-wrong.

---

## 3. The options, costed

### Option A — Tiering (move cold segments to cheap storage)
- **Mechanism:** append-only segments are immutable once closed (`22-`, and the
  reason venn2's O(1) versioning works). A closed segment older than a horizon is
  moved to cheap/cold storage (object store, cheaper disk); its content hashes stay
  inline in an index on fast media, so a replay that needs it fetches it.
- **Preserves:** everything — full history, full asOf, full derivability. Only
  *latency* of deep-history replay changes.
- **Bounds:** fast-media footprint (the hot window). Total footprint still grows,
  but on the cheapest tier.
- **Cost if wrong:** if cold storage is unavailable at replay time, deep asOf
  queries block or fail until it returns — an availability dependency, not a
  correctness loss. Governable by a recorded tiering policy (which horizon, which
  tier).
- **Verdict:** the safe default. Preserves the moat (complete audit), bounds the
  expensive resource, forfeits nothing.

### Option B — Horizon compaction (checkpoint + drop raw prefix)
- **Mechanism:** at a chosen horizon, write a **checkpoint** — a governed snapshot
  citing the log seq it derives from, validated by round-trip diff = ∅ (the
  snapshot law, `15-` FB7, S4) — then discard the raw records *before* it. The
  checkpoint becomes the new genesis; replay starts there.
- **Preserves:** all *current* state and all history *after* the checkpoint. Bounds
  total footprint hard.
- **Forfeits:** asOf queries *before* the checkpoint horizon. "What could X see in
  2029?" becomes unanswerable if the 2029 records were compacted. This is a
  **governed, recorded loss** — the checkpoint records what horizon it collapsed.
- **Cost if wrong:** you compact away history you later need for an audit or
  dispute — irreversible. So the horizon must be ruled conservatively and the
  compaction itself is an owner-authority act (like GS-13), never automatic.
- **Verdict:** the hard-bound option, for genuinely unbounded-lifetime deployments,
  used at a *long* horizon behind Option A, and only under owner authority.

### Option C — Scheduled erasure (GS-13, for retention compliance)
- **Mechanism:** the existing master-destruction protocol (GS-13, `18-` §C),
  applied on a schedule to classes of records a retention rule requires deleting
  (e.g. "personal data older than N years"). Owner-only; the scar survives;
  pre-erasure replay reproduces the redacted state.
- **Preserves:** everything except the specifically-erased class; the fact of
  erasure is recorded.
- **Forfeits:** regenerability of the erased items (knowingly — that is GS-13's
  whole point).
- **Cost if wrong:** erasing a class still needed — but GS-13 already owns this
  risk and its authority model. This is compliance, not capacity, but it also
  relieves capacity.
- **Verdict:** orthogonal to A/B; used when law *requires* deletion, not when disk
  requires it.

---

## 4. Recommendation (PROPOSED — owner rules the horizons)

A **layered horizon** posture, using all three levers at increasing time-scales:

```
now ──────────── hot window ──────────── warm ──────────── cold ──────────── ancient
   fast media           tier to cheap (A)      compact behind checkpoint (B, owner-authorised)
                                               GS-13 erasure (C) wherever a retention rule fires
```

- **Default (ships with the kernel):** Option A only. Grow-forever with cold-tier
  offload. Preserves the full moat; bounds fast-media cost. No history lost.
- **For unbounded-lifetime deployments:** add Option B at a long, owner-ruled
  horizon (years), behind A. The only lever that forfeits history, so it is
  owner-authority-gated and conservative.
- **Everywhere a retention law applies:** Option C on its own schedule.

**What stays an owner ruling (not invented here):** the actual horizons (how long
is the hot window; at what age does a segment tier; at what age, if ever, does a
prefix compact) are **calibration values** — they get an owner and an evidence
basis, never a number pulled from the air (03 §8, the sorting-pass §2 discipline).
This paper fixes the *mechanisms and their costs*; the numbers are a calibration
gate.

---

## 5. What this closes, and the honest residue

**Closed:** the "grow-forever meets finite disk" question is no longer open-ended.
The growth law is derived (bounded by decisions, `22-`); the three levers are
specified and costed; a layered default is recommended; the irreversible lever (B)
is correctly gated to owner authority; and the calibration horizons are named as an
owner ruling rather than invented. FB6's OPEN flag can move to
RULED-PENDING-HORIZONS.

**Residue (honest):** (1) the horizon *values* are still un-ruled — deliberately,
they are calibration; (2) Option A's cold-tier replay latency is a real
availability property that a deployment must accept or mitigate (keep the index
inline, which this specifies); (3) none of this is measured — record growth rates
are the Estimate-Medium orders of magnitude from `22-`. The *mechanism* design is
complete; the *numbers* await evidence, as the method requires.

**Trained-knowledge flag:** tiering/compaction/checkpoint are standard storage-
engineering patterns (Estimate — High); their fit to the append-only record and
the governed-loss framing of Option B are derived from the estate's own snapshot
law and GS-13.
