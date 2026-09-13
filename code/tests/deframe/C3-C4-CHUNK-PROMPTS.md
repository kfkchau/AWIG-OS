<!-- gov-os provenance · systems-architecture documentation · paste-ready launch prompts, one per chunk, for the C3/C4 chunked authoring plan. -->
<!-- doc: class=ORDER status=LIVE supersedes=- superseded-by=- verified=2026-07-25 -->
# GOV-OS — C3 / C4 chunk prompts, paste-ready

The operational companion to `tests/deframe/C3-C4-CHUNK-PLAN.md`. That plan names the
slices; this file is the actual message you paste to open each one. Same relationship
`planning/method/SESSION-PROMPT-TEMPLATES_v3.md` has to the charter.

Three templates cover every chunk. Bracketed slots are filled from the fill tables in §4
and §5; everything outside the brackets pastes verbatim. Frozen on handover: improvements
arrive as marked addenda, never as silent rewrites of a prompt already in use.

**Paths are written as they exist on disk today**, including the `_v3` suffixes. Until
`OPEN-TASKS.md` item 1 is settled, a prompt naming a canonical `X.md` path sends the
session to `tests/archive/`, which is the wrong file. If item 1 is settled by promotion
(rename `_v3` to canonical), the `_v3` suffixes in §4 and §5 are dropped in one sweep and
this file gets a dated addendum saying so.

---

## 1. The seat split (the answer to "one EP at a time, or what")

Two different jobs get confused because both say "EP":

- **Authoring an EP file** is design work. It is a chunk. One EP file per fresh session,
  written to disk, then stop. Template T8 below.
- **Building an EP** is execution. That is the existing manager loop:
  `SESSION-PROMPT-TEMPLATES_v3.md` T6 spawns a builder per T1 and a verifier per T2. That
  machinery is unchanged and is not chunked, because a builder session reads one EP file
  and nothing else, which is already the narrowest context in the estate.

So: one slice per session for authoring, and the existing T1/T6 loop for building. The
chunk plan's line "EPs strictly one per session" binds both halves.

The paper comes before its EPs. `PAPER-STANDARD_v3.md` GATE 3 is the owner's ruling on the
paper, and the mentor reviews the paper against all four gates before any EP dispatches.
No EP-authoring chunk opens until that has happened.

## 2. Gate bookkeeping under chunking (read before running C3-P6)

Splitting the paper across sessions splits its gates, so the gates land like this:

- **GATE 1 (shape)** is checked at assembly, chunk C3-A / C4-A. Mechanical: every section
  of `PAPER-STANDARD_v3.md` §1 present.
- **GATE 2 (two pressure-test passes)** is chunk C3-P6 / C4-P5, run over the assembled
  draft. The standard is explicit that a pass finding nothing is a failed pass and gets
  re-run against what the first pass left unexamined.
- **GATE 3 (owner ruling)** is yours, after assembly.
- **GATE 4 (lowerability)** needs the invariant-to-test-to-EP mapping table.
  **The chunk plan assigns no chunk to that table.** C3-P5 produces the acceptance battery
  and C3-P0 produces the EP index, but the table that maps each K-invariant to its named
  tests and its EP is not assigned to anyone. It is a small tabular job and belongs with
  C3-P5, but the plan is yours and I have not moved it. Either extend C3-P5's output line
  to include it, or add a C3-P5b chunk. Same gap in C4 at C4-P4.

## 3. The three templates

### T7 — PAPER SECTION CHUNK

> You are an authoring session for gov-os, repo `apps/gov-os` (Linux). You write ONE
> section of a campaign target-state paper and nothing else.
>
> Your slice: **[SLICE]**
>
> Read only these files, in this order, and nothing beyond them:
> [READ-SET]
> Then read `tests/deframe/REPO-WRITING-GUIDE.md` for the writing register.
>
> Do NOT read the full author brief's read order, do NOT read the rest of the design
> canon, and do NOT re-derive the campaign's context. The slice above is the whole job.
>
> Tier: **[TIER]**. State your tier verdict before any work. If you cannot genuinely run
> at that tier, say so and STOP. A wait beats a wrong derivation.
>
> Write your output to **[OUTPUT PATH]**, in the shape required by
> `planning/method/PAPER-STANDARD_v3.md` §1 for that section, with labels on every claim
> (SOURCE-DERIVED with a citation / INFERRED from what / PROPOSED with the cost if wrong /
> trained knowledge, flagged). Estimates open "Estimate" with a confidence tier. Mark any
> contradiction with an existing doc as CONFLICT and show both sides; never harmonize.
>
> When the section is written to disk, STOP. Do not roll into the next slice, do not
> assemble, do not index, do not touch any other file.
>
> End by listing, in plain sentences: what you wrote, what you left open, and anything the
> owner owes a word on. Raise items; never accept them.

### T8 — EP AUTHORING CHUNK

> You are an authoring session for gov-os, repo `apps/gov-os` (Linux). You write ONE
> execution plan file and nothing else.
>
> Your EP: **[EP NUMBER]** — **[SUBJECT, ONE SLICE]**
>
> Read only these files, in this order, and nothing beyond them:
> - `planning/method/BUILD-PROMPT-STANDARD_v3.md` — the EP anatomy your file is born to,
>   including its two 2025-07 laws: migration oracles are era-pinned, both sides, whole
>   class; strictly-stronger proofs extend the ledger into every new dimension the
>   replacement introduces.
> - `planning/exec/EXECUTION-PLANS.md` — EP-00, the protocol every EP inherits.
> - [CAMPAIGN PAPER PATH] — the ruled paper this EP realizes. Cite it; never paraphrase it.
> - [ANY SLICE-SPECIFIC DOC]
> Then read `tests/deframe/REPO-WRITING-GUIDE.md` for the writing register.
>
> Do NOT read other EP files, do NOT read source, and do NOT hold a second EP's subject in
> this context.
>
> Tier: **[TIER]**. State your tier verdict before any work; if you cannot run at it, say
> so and STOP.
>
> Write the EP to **`planning/exec/EP-[NN].md`**. It must carry its own SESSION PROMPT
> block, read order, tier gate, preconditions, scope fence, and acceptance commands, so a
> cold builder session needs nothing but that file.
>
> When the file is on disk, STOP. One EP per session, always.
>
> End by listing, in plain sentences: what the EP asks for, what it fences out, and what
> the owner owes a word on before it dispatches.

### T9 — ASSEMBLY CHUNK

> You are an assembly session for gov-os, repo `apps/gov-os` (Linux). Your job is
> mechanical: stitch and index already-written text. You derive nothing and you decide
> nothing.
>
> Read only: the section files listed below, and
> `tests/deframe/REPO-WRITING-GUIDE.md`.
> [SECTION FILE LIST]
>
> Tier: LOW to MEDIUM. This is bookkeeping.
>
> Do:
> 1. Stitch the sections into **[TARGET PAPER PATH]** in the order given by
>    `planning/method/PAPER-STANDARD_v3.md` §1.
> 2. Add the top-of-file provenance line and the `<!-- doc: … -->` metadata line, class
>    CANON, status LIVE, and mark the paper DRAFT awaiting its gates in the status head.
> 3. Add the row to `DOC-MAP_v3.md` and the entry to `design/00-DESIGN-INDEX_v3.md`.
> 4. Append a dated entry to `planning/build/BUILD-PROGRESS_v3.md` saying what was
>    assembled, from which chunks, and that the gates are not yet passed. Write the body
>    first and the status line last.
>
> Do not: rewrite any section's content, resolve any CONFLICT marker, fill any gap you
> notice, or claim any gate has passed. If a section is missing or two sections disagree,
> stop and report it as a plain sentence. That is a finding for the owner, not a gap for
> you to fill.
>
> End by listing what you assembled and anything you found missing.

---

## 4. Fill table — Campaign 3, the paper (`design/36-CAMPAIGN-3-DEPTH.md`)

Section outputs land as separate files under `planning/exec/c3-sections/` so a chunk that
trips costs one file. C3-A stitches them into `design/36`.

| Chunk | Template | Slice | Read-set (exact paths) | Tier / model | Output |
|---|---|---|---|---|---|
| C3-P0 | T7 | the paper's structure: status head, sources, essence paragraph, the K-invariant NAMES only (they are in design/32 §1), record-kind table headers, EP index, empty section stubs. No custody mechanics. | `design/32-CAMPAIGN-HORIZON-TARGET-STATES_v3.md` §1 · `design/31-CAMPAIGN-2-AUTHORITY_v3.md` (for shape only) | medium / Opus | `planning/exec/c3-sections/P0-skeleton.md` |
| C3-P1 | T7 | invariants K1, K2, K4, K5 at sketch level: authority not shadow; semantic identity at the ports including the real-time carve-out; the differential oracle at OS scale; smallest kernel residence | `design/32-…_v3.md` §1 · `design/28-TARGET-STATE-HOST-KERNEL.md` §5 · `design/16-BRIDGE-STEPPINGSTONE-TO-KERNEL.md` | high, your call on model | `planning/exec/c3-sections/P1-invariants.md` |
| C3-P2 | T7 | the K3 section alone: the record-write and authority-fold hot-path resolution, stated as measured calibration and never as a stored table | `design/22-MEMORY-TO-THE-METAL.md` · `design/28-TARGET-STATE-HOST-KERNEL.md` §13 · `design/23-CAPACITY-ECONOMICS.md` | xhigh / Fable, isolated | `planning/exec/c3-sections/P2-k3-speed.md` |
| C3-P3 | T7 | the external-answer and two-times section alone: the external-answer record kind, session-aware push, the fingerprint-checked seal | `design/35-TWO-TIMES-OF-AUTHORITY_v3.md` · `design/34-FINGERPRINT-DERIVATION.md` | xhigh / Fable, isolated | `planning/exec/c3-sections/P3-two-times.md` |
| C3-P4 | T7 | the crossing: observe, then custody, then in-kernel; the subsystem order; the ports contract sketch | `design/16-BRIDGE-STEPPINGSTONE-TO-KERNEL.md` · `design/10-SYSCALL-CONFORMANCE-MAP.md` · `03-TARGET-STATE-ARCHITECTURE.md` §5–6 (repo root, NOT `design/03`) | high, your call on model | `planning/exec/c3-sections/P4-crossing.md` |
| C3-P5 | T7 | the record-kind table, the deferred-to-live ledger, and the acceptance battery. Mostly tabular. See §2 above on the GATE 4 mapping table. | `design/28-TARGET-STATE-HOST-KERNEL.md` §3 · `design/19-TEST-BATTERY.md` | medium / Opus | `planning/exec/c3-sections/P5-tables.md` |
| C3-P6 | T7 | the honest caps section, plus the two pressure-test passes over the assembled draft. Pass two examines the semantics pass one assumed without stating. A pass that finds nothing is re-run. | the assembled draft only (C3-P0..P5 outputs) · `planning/method/PAPER-STANDARD_v3.md` §2 | high, your call on model | `planning/exec/c3-sections/P6-caps-and-passes.md` |
| C3-A | T9 | assembly and bookkeeping | the seven section files | low / Opus | `design/36-CAMPAIGN-3-DEPTH.md` |

Run order: P0, then P1, P4, P5 in any order, then P2 and P3 each in its own empty session,
then A to assemble, then P6 over the assembled draft, then A again to fold P6 in. The two
hot slices are never in one session with each other or with anything else.

## 5. Fill table — Campaign 4, the paper (`design/37-CAMPAIGN-4-PROOF.md`)

Opens only after C3's paper is ruled. Same section-file pattern under
`planning/exec/c4-sections/`.

| Chunk | Template | Slice | Read-set (exact paths) | Tier / model | Output |
|---|---|---|---|---|---|
| C4-P0 | T7 | the paper's structure: status head, sources, essence, the Q-invariant NAMES only (design/32 §2), record-kind headers, EP index, stubs | `design/32-…_v3.md` §2 · `design/31-…_v3.md` (shape only) | medium / Opus | `planning/exec/c4-sections/P0-skeleton.md` |
| C4-P1 | T7 | Q1 the chained record and Q2 signed acts | `design/32-…_v3.md` §2 · `design/28-…md` §I11 · `design/31-…_v3.md` J7 | xhigh / Fable, isolated | `planning/exec/c4-sections/P1-chain-and-sign.md` |
| C4-P2 | T7 | Q3 engine attestation and Q4 the physically separated blind streams | `design/28-…md` §7 · `planning/exec/EP-09.md` | xhigh / Fable, isolated | `planning/exec/c4-sections/P2-attest-and-separate.md` |
| C4-P3 | T7 | Q5 the one destruction ceremony (GS-13), alone | `design/18-LAW-BOOK.md` §C · `design/23-CAPACITY-ECONOMICS.md` | xhigh / Fable, isolated | `planning/exec/c4-sections/P3-gs13.md` |
| C4-P4 | T7 | record kinds, deferred-to-live, acceptance battery. See §2 on the GATE 4 mapping table. | `design/28-…md` §3 · `design/19-TEST-BATTERY.md` | medium / Opus | `planning/exec/c4-sections/P4-tables.md` |
| C4-P5 | T7 | honest caps plus the two pressure-test passes over the assembled draft | the assembled draft only · `planning/method/PAPER-STANDARD_v3.md` §2 | high, your call on model | `planning/exec/c4-sections/P5-caps-and-passes.md` |
| C4-A | T9 | assembly and bookkeeping | the six section files | low / Opus | `design/37-CAMPAIGN-4-PROOF.md` |

## 6. Fill table — the EP-authoring chunks

Each row is one T8 session. None opens until its campaign paper has passed GATE 3 and the
mentor's review. Subjects are the chunk plan's own words.

**Campaign 3.** Paper path slot = `design/36-CAMPAIGN-3-DEPTH.md`.

| Chunk | EP | Subject (one slice) | Tier / model |
|---|---|---|---|
| C3-E1 | EP-21 | pre-C3 cleanup: retire the carried items, dead imports | medium / Opus |
| C3-E2 | EP-22 | complete the observe stance on the Ubuntu guest, the audit product | high |
| C3-E3 | EP-23 | the external-answer seam, design/35 machinery to code | xhigh / Fable |
| C3-E4 | EP-24 | FUSE files authority: the first real custody flip, nested namespace, crash-recompute | xhigh / Fable |
| C3-E5 | EP-25 | the speed tension: measure and calibrate the hot path | xhigh / Fable |
| C3-E6 | EP-26 | devices custody, against real netlink and uevents | xhigh / Fable |
| C3-E7 | EP-27 | comms custody | xhigh / Fable |
| C3-E8 | EP-28 | memory custody | xhigh / Fable |
| C3-E9 | EP-29 | scheduling custody, last, with the real-time bound | xhigh / Fable |
| C3-E10 | EP-30 | the syscall port at byte level, and /proc | xhigh / Fable |

**Campaign 4.** Paper path slot = `design/37-CAMPAIGN-4-PROOF.md`. EP numbers follow on
from C3's last and are fixed when C3 closes.

| Chunk | Subject (one slice) | Tier / model |
|---|---|---|
| C4-E1 | chained records | xhigh / Fable |
| C4-E2 | record signing, keys bound to accounts | xhigh / Fable |
| C4-E3 | module signing and engine attestation | xhigh / Fable |
| C4-E4 | blind-stream key separation, the physical split | xhigh / Fable |
| C4-E5 | the GS-13 destruction ceremony | xhigh / Fable |
| C4-E6 | succession keys | xhigh / Fable |

## 7. What this file does not settle

- The GATE 4 mapping table has no assigned chunk (§2). Owner's call.
- The `_v3` naming question (`OPEN-TASKS.md` item 1) is unsettled, so every path here
  carries the suffix. If promotion happens, one sweep drops them and this file gets a
  dated addendum.
- The chunk plan's `design/03` read-set entry does not resolve; the C3-P4 row above points
  at `03-TARGET-STATE-ARCHITECTURE.md` at the repo root instead. The chunk plan itself is
  unamended: that is the owner's file.
- Whether the section files live under `planning/exec/c3-sections/` is a placement choice
  made here so a tripped chunk costs one file. Nothing binds it; say the word and it moves.
