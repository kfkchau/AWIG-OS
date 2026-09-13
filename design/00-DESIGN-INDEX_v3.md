<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=VIEW status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Design Package Index

**Status:** v1.0, 2026-07-18 (refreshed by the mentor; original v0.1, 2026-07-12).
This `design/` folder now holds TWO layers, and knowing which you are reading is the
whole trick:

- **THE LIVE CANON (25–35)** — the campaign-era docs the running kernel is built and
  reviewed against. If a 10–24 doc disagrees with a 25–32 doc, the LIVE canon controls.
- **THE PRE-CODE PACKAGE (10–24)** — the full paper design written before the first
  line of code ("design to the teeth"). Still valid reference and still binding where
  nothing later supersedes it; historically frozen.

## THE LIVE CANON (25–34; read these for any current work; the cold-start chain is in `planning/MENTOR-HANDOVER.md`)

| # | Doc | What it is |
|---|---|---|
| 25 | `25-VIEW-TREE.md` (+ `25-view-tree.json`) | the base view tree; deontic ruling (dos/don'ts/may-is-computed); live checks |
| 26 | `26-KERNEL-DERIVABILITY-AUDIT.md` | every kernel concept derived over the base |
| 27 | `27-FUNDAMENTAL-RULES.md` | the recorded constitution: genesis pack, root rules, ops/views as data |
| 28 | `28-TARGET-STATE-HOST-KERNEL.md` | **campaign 1's definitive** — invariants I1–I11 the whole host spine was reviewed against |
| 29 | `29-TIER-CONSERVATION.md` | the conservation law: amendment without a gap; exit-not-surgery; scoped vocabularies |
| 30 | `30-POWER-MODEL.md` | positive grant, computed complement, hop-by-hop verification, THE UNTOUCHABLES |
| 31 | `31-CAMPAIGN-2-AUTHORITY.md` | **campaign 2's definitive** (twice pressure-tested) — accounts, spaces, grants, the live chain |
| 32 | `32-CAMPAIGN-HORIZON-TARGET-STATES.md` | target states for campaigns 3–7 + the dependency lattice |
| 35 | `35-TWO-TIMES-OF-AUTHORITY.md` | OWNER-RULED 2026-07-25: deciding time carries legitimacy, recording time carries order; acceptance adjudicates by deciding time + authority; priority lanes + session-aware push; recorded overturns; design/34's seal is the backstop. C3 paper carries it. |
| 34 | `34-FINGERPRINT-DERIVATION.md` | judged-state fingerprint, SOLVED pending owner ruling (re-homed 2026-07-24 from the dissolved pwc/ staging); lands as ONE check kind beside the existing six; NOT for kernel builders — the occupant-agnostic form is carried in `planning/WALL-PRIMITIVES-HANDOVER.md` |
| 36 | `36-CAMPAIGN-3-DEPTH.md` | **campaign 3's launch paper** (author seat, 2026-07-25): custody invariants K1–K11, the overturn-reach specification design/35 §6 deferred, EP-20B + EP-21..33; GATE 3 (owner ruling) OPEN — the sitting mentor reviews against the four gates before any EP dispatches |
| 37 | `37-CAMPAIGN-4-PROOF.md` | **campaign 4's paper** (author seat, 2026-07-25, owner-commissioned): cryptographic closure Q1–Q10, EP-34..42, the R20-2 closure and the two-times bracket; DIRECTION-binding now, re-priced at the C3 close per design/32 rule 4; GATE 3 (owner ruling) OPEN — the sitting mentor reviews against the four gates before anything dispatches |
| 38 | `38-WRITE-PATH-ENDORSEMENT-DERIVATION.md` | the owner's four write-path ideas derived under the two-times law (2026-07-26): the intent buffer with retire-on-exact-echo, the multi-view stamp (P7 + the seal on the write path), endorsement-before-sequencing, the overturn-cost gradient, quorum re-homed to C6. **RAISED, not ruled — binds nothing**; homes in its §6 (EP-26/27 adjacency, C6) |

Companion live surfaces outside this folder: `DESIGN-SOUL.md` (the philosophy; §5
conformance updated mid-campaign), `planning/exec/` (EP-00 protocol + all EP files,
campaigns 1 and 2), `planning/build/BUILD-PROGRESS.md` (the append-only build+review
record), `planning/MENTOR-HANDOVER.md` + `planning/MENTOR-LETTER.md` (the seat),
`tools/mentor-probes/` (the committed pressure-test probe library).


**[AMENDMENT, 2026-07-28 — two live canon documents grew past their rows during
campaign 3, and the addenda are LAW rather than commentary.]**

`36-CAMPAIGN-3-DEPTH.md` now carries **ten dated addenda, A through J**: the
four-gate review's five §4b corrections; three measurement findings that changed
the campaign's own sequencing (K3's second half measured false, then met); the
reach test's domain; K7's cap and its closure; the router-precedence ruling; and
the shed class. Read them with the paper — several are corrections to it.

`10-SYSCALL-CONFORMANCE-MAP.md` gained **nine §11 subsections** (11.1a–11.1f,
11.2a–11.2b, 11.4a), every one found by a build rather than predicted by a plan.
The load-bearing ones for any future subsystem arc: §11.2b, an instrument
establishes its subject and cannot corrupt it; §11.4a, a record is attributed to
the act it covers rather than to the step it landed in; §11.1c, a release records
but never folds for authority.

A successor's fastest route into both is `planning/MENTOR-HANDOVER-C3.md` §2,
which says which of them will actually bite and why.

## THE PRE-CODE PACKAGE (10–24) — read order as originally designed

| # | Doc | What it is | Why it matters |
|---|---|---|---|
| 16 | `16-BRIDGE-STEPPINGSTONE-TO-KERNEL.md` | the four-stance crossing from record-machine-as-program to record-kernel | **the one joint the architecture named but never designed** — read this first; it makes the kernel step small and proven, not a leap, and each stance ships value alone |
| 17 | `17-SORTING-PASS.md` | the S/U classification of the whole build | the required method step; finds the running kernel is all-S and the judgment is all in governed law — the design's core insight |
| 11 | `11-RECORD-SHAPES.md` | the exact shape of every record the kernel appends | the data spine at kernel grade: base envelope, LAW/DECISION/INPUT shapes, the built-ID tiebreak field |
| 12 | `12-OPERATIONS-CATALOGUE.md` | every governed operation through the gate | what the kernel can be asked to do; each an op that records a decision or refuses citing a rule |
| 13 | `13-VIEWS-AND-PROC-CATALOGUE.md` | every question the kernel can answer + `/proc` as views | current state as computed views; the "why did this run" audit Linux can't offer |
| 10 | `10-SYSCALL-CONFORMANCE-MAP.md` | the Linux syscall surface mapped, ~130 calls | THE compatibility contract and its permanent test spec |
| 14 | `14-SEAM-CONTRACTS.md` | the handshake at every joint | contracts before stages; each doubles as its seam's test |
| 15 | `15-FAILURE-BOOK.md` | every anticipated failure and the governed response | nine failure modes, recorded and rule-cited; carries the S/U scar tissue to kernel grade |
| 18 | `18-LAW-BOOK.md` | everything that already binds, assembled | reading index of the constitution; sources control |
| 19 | `19-TEST-BATTERY.md` | acceptance checks written before code | the code gets built to pass a known battery; mapped to the bridge stances |
| 20 | `20-CANONICAL-GLOSSARY.md` | one name per field/verb/law-id | ends the cross-doc naming drift; controls until seam S1 |
| 21 | `21-ORDERING-DETERMINISM-PROOF.md` | **the keystone proof** — deterministic replay under every interleaving | closes the audit contract's load-bearing assumption; general case proved (not just pairwise) |
| 22 | `22-MEMORY-TO-THE-METAL.md` | the hot-subsystem proof-of-method | proves the speed-tension resolution survives page faults (the acid test): minor faults record nothing |
| 23 | `23-CAPACITY-ECONOMICS.md` | grow-forever vs finite disk, costed | closes the one open design question; three levers, layered default, horizons = owner calibration |
| 24 | `24-DRIVER-SHIM-DETAIL.md` | binding unmodified Linux drivers to the governed boundary | closes the hardware edge of "same ports"; four crossings → existing record classes |

## What is complete vs deferred

**Complete (this package):** the bridge, the sorting pass, record shapes,
operations catalogue, views/proc catalogue, syscall conformance map, seam
contracts, failure book, law book, test battery, canonical glossary — AND the two
formerly-deferred proofs (ordering determinism `21-`; memory to the metal `22-`),
the capacity decision (`23-`), and the driver-shim detail (`24-`). Together with
the three architecture docs, this is the **complete paper design** to the point
right before code, with no deferred architecture items.

**No longer deferred (closed this session):**
1. ~~ordering-determinism proof~~ → PROVED (`21-`): a deterministic injective
   ordering key `K = (bucket, built_id, submission_time)` exists over recorded
   fields; injective by three-case exhaustion; covers every interleaving and
   collision multiplicity. Optional max hardening = machine-check it.
2. ~~one hot subsystem to the metal~~ → DONE (`22-`, memory): minor page faults are
   CACHE fills that record nothing; record rate tracks decisions (~10³–10⁴/s), not
   accesses (~10⁶–10⁹/s); reconstruction verified.
3. ~~capacity economics~~ → RULED-PENDING-HORIZONS (`23-`): mechanisms specified
   and costed; only the horizon *numbers* remain (owner calibration, by design).
4. ~~driver-shim detail~~ → SPECIFIED (`24-`).

**Open owner rulings (shape the build, do not block the architecture):**
- the build route (A recommended; stances 1–3 are route-agnostic, so the ruling is
  needed only at the stance 3→4 boundary);
- the first demo story; the name;
- the capacity horizons (`23-` §4 — calibration values, ruled from evidence).

**Optional hardening (not required for architectural completeness):** transcribe
the `21-` proof into a proof assistant (TLA+/Coq/Lean) — converts the rigorous
hand proof to machine-checked. Changes nothing in the result.

## The two standing guards (from `03 §8`, binding on this folder)
1. **Frame:** governance-first. Organising around threat models = drift; re-root
   at `03 §0`.
2. **Scope:** `SCOPE-STATEMENT.md` settles the false-flag question; do not
   re-deliberate it.
