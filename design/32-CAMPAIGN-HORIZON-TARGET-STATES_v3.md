<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — The Campaign Horizon: Target States for All Campaigns

**Status:** v1 DRAFT, 2026-07-17, mentor session, tier xhigh. The owner asked for the target
state of EVERY campaign written out. This paper supersedes design/31 §8's one-paragraph
roadmap with a target-state section per campaign, and states its own honesty rule:

> **Resolution decays with distance, on purpose.** Campaign 3's route is already owner-ruled
> and is written concretely. Campaign 7 is written at invariant level. EP-grade precision
> about work five campaigns out would be FAKE precision — the estate's documented assessment
> sin. Each campaign's sitting mentor re-derives a full design/31-shape paper at that
> campaign's launch; the owner rules it then. THESE sections are the definitive-until-refined:
> binding on direction, honest about depth.

Sources: the owner's rulings ledger (BUILD-PROGRESS), design/28/29/30/31, DESIGN-SOUL,
00-READ-FIRST §4 (hollow-out route, pinned kernel, subsystem order, S5 ordering, real-time
carve-out — all RULED), the corpus (OGS kernel scope; CGL grammars; venn2 foundational;
TWC runtime). Owner rulings control. Labels per 00-READ-FIRST §6.

---

## 0. The campaign lattice (what depends on what, and why this order)

```
C1 HOST-SPINE (EP-01..13)  — the downward half + the single wall      [10/13 done]
C2 AUTHORITY  (EP-14..20)  — the upward half: who / where / how far   [design/31, drafted]
C3 DEPTH                   — real custody: the hollow-out              [route RULED]
C4 PROOF                   — cryptographic closure
C5 LANGUAGE                — describe governance, not just run it
C6 FEDERATION              — many records, no merger
C7 METABOLISM AT SCALE     — the living organisation
```

- **C2 before C3:** real custody of real files without verified identity repeats the
  one-room problem at OS scale — the building needs floors before it takes the furniture.
- **C3 before C4 (default, swappable):** signing wants to know the final custody surfaces
  it seals; sealing the user-space vehicle then re-sealing the kernel is double work.
- **C5 before C6 (firm):** you cannot federate what you cannot describe — comparison across
  sovereign systems IS the language layer applied across a wire.
- **C7 rides C2 + C5** and can START its early EPs after C2 (an organisation needs
  authority and, for its real rule content, description) — it does not need C3/C4/C6 to
  begin; its full depth wants them. The one deliberate overlap the lattice permits.

## 1. CAMPAIGN 3 — DEPTH: the hollow-out (resolution: HIGH — the route is ruled)

**Essence.** The record machine stops describing an operating system and takes CUSTODY of
one: same interfaces, governed core beneath. The owner-ruled route (2026-07-13) stands:
hollow-out through the bridge — user space first (observe, then FUSE authority), enter the
kernel LAST and SMALLEST, subsystem by subsystem behind unchanged interfaces, never from
scratch. Build kernel: pinned vanilla `linux-6.18.38` LTS; validate on the exact Ubuntu
kernel. Subsystem order RULED: files → devices → comms → memory → scheduling (last).

**End-state invariants:**
- **K1 Authority, not shadow.** The governed core AUTHORIZES real operations (a FUSE open/
  write/unlink happens because the gate said yes and the record shows why) — the record is
  upstream of the effect, never a log of it.
- **K2 Semantic identity at the ports.** The syscall surface keeps its meaning exactly
  (the ports promise); the RULED carve-out stands: for real-time scheduling classes the
  timing bound IS the semantics and is promised there.
- **K3 I9 at operating-system rate.** Recording scales with governance, never operation —
  each subsystem's speed tension is resolved at MAX tier as its own narrow problem (the
  one class of work reserved for max), never by quietly recording less.
- **K4 The differential oracle at OS scale.** Every swapped subsystem proves
  behavior-identical against the un-swapped original over real workloads — campaign 1's
  proven method promoted to the system-call boundary.
- **K5 Smallest possible kernel residence.** What enters the kernel is the minimum that
  custody requires; the record machine's brain stays where it is testable.

**EP sketch (sized at launch):** FUSE files authority (full, beyond the flat-namespace
proof) → devices → comms → memory → scheduling; the byte-level syscall port; /proc.
Per-subsystem speed-tension resolutions interleave at max tier. Detail controls:
`planning/10-BUILD-ROADMAP.md` (already owner-ruled).

**Honest caps.** Performance is the campaign's whole risk and is unmeasured until K3 work
begins; the roadmap's staged validation (pinned kernel → Ubuntu kernel) is the containment.

## 2. CAMPAIGN 4 — PROOF: cryptographic closure (resolution: MEDIUM)

**Essence.** Every guarantee so far is cannot-do-lawfully + cannot-do-quietly; the record
detects alteration by cross-check, not mathematics. C4 upgrades the promise to
**cannot-do-undetectably, even on disk** — the "signing later" annotations throughout the
estate (28 §I11, EP-09's physical-separation deferral) all land here.

> **Amendment (documentation-currency, EP-MAINT-C4-FINDINGS F2 — records code state, no design change).** 2026-09-08: real cryptographic signing is the KEY-MATERIAL-REAL unit (in progress); the live shape is modelled — see gate.py:171.

**End-state invariants:**
- **Q1 The chained record.** Each record carries a hash chained to its predecessor; any
  on-disk edit breaks the chain at a provable point. Hand-editing the file — out of scope
  since the three-tier ruling — becomes DETECTABLE BY DERIVATION.
- **Q2 Signed acts.** Records are signed with keys bound to C2 accounts; "verified"
  upgrades from recorded-evidence to cryptographic. Succession (C2's anchor) gains key
  ceremony teeth.
- **Q3 The engine attests itself.** Code signing for the S-plane: T-NO-LAW-IN-CODE gains
  an integrity twin — the interpreter that runs the law is itself attestable (closes the
  shared-digest-function cap from the EP-09 review).
- **Q4 Blind streams physically separated.** The EP-09 deferral lands: separate custody
  with separate keys — real now, theatre before.
- **Q5 GS-13, the one true destruction.** Erasure exists nowhere in the estate except as
  its own recorded ceremony; C4 builds it: destruction that leaves a signed shell proving
  WHAT was destroyed, under WHOSE authority, WITHOUT revealing content (the CONST-SECRETS
  shape applied to deletion).

**Honest caps.** Algorithm choices are calibrations (owner-gated, replaceable — the
traffic-light rule: the measurement is truth, the band is display); key custody is a human
ceremony no kernel can conjure; a compromised root key is C2's succession problem in
cryptographic form — stated, not solved here.

## 3. CAMPAIGN 5 — LANGUAGE: describe, don't just run (resolution: MEDIUM)

**Essence.** The kernel currently runs ITS OWN law. C5 teaches it to DESCRIBE governance in
general — the full CGL layer: any rule system, statutory or customary, Western or not,
expressed in the shared frame-carrying grammar and compared without merger. The kernel
learns to hold other people's law respectfully: as information with a frame.

**End-state invariants:**
- **G1 Component grammars as content packs.** The CGL dimension sets (activity, action,
  resource, enforcement, measurement, architecture, geometry, connection) enter as
  vocabulary packs — composable, amendable, never enums in code.
- **G2 Enforcement dimensions first-class.** The owner's correction made kernel-real:
  targeted/blanket × block/ATTRACT — attract-class enforcement (drawing acts somewhere)
  gets its kernel expression at last, beside block.
- **G3 Claimed vs effective strength, computed.** The toothless-must view generalizes: any
  described law's claimed force is compared against its operational teeth — paper tigers
  detectable in OTHER systems' law, not just our own.
- **G4 Translation surfaces.** Prose law ↔ full-form law across the structurality gradient:
  mechanical where structure permits, JUDGMENT-PRICED where it does not (the S/U four-cell
  rule — the gradient position decides human vs machine, honestly).
- **G5 The universality test as running code.** Who-derives-who: a good framework derives
  the broken ones and diagnoses their brokenness. C5's acceptance is describing a foreign
  rule system well enough that its gaps surface as computed findings.

**Honest caps.** The grammar packs come from the cgl-app corpus (proving example exists);
translation quality at the unstructured end is bounded by judgment supply, priced not
hidden; informal/oral systems are first-class DESCRIPTION targets (the framework bends,
not the material — standing owner doctrine).

## 4. CAMPAIGN 6 — FEDERATION: many records, no merger (resolution: MEDIUM-LOW)

**Essence.** Sovereign gov-os instances compare without merging — the S6 seam. Verdicts
travel with their frames; nothing reconciles; comparability is mandatory, executability
optional (CGL's founding function, across a wire).

**End-state invariants:**
- **F1 Sovereignty is absolute.** No instance writes another's record, ever. What crosses
  is DESCRIPTION: verdicts, frames, provenance, signed proofs (C4's transport
  authentication).
- **F2 The one comparison law, federated.** Cross-instance verdicts on the same pair
  differ by frame → both kept, different information (EP-11's law, unchanged at any
  scale). Same-frame incompatibility across instances → a detected dispute, routed to
  BOTH owners' queues — the first federated governance object.
- **F3 Multi-writer arrives with real writers.** The RULED S5 ordering (one intake
  pipeline; time-hash order; two-way collisions broken by the writing subsystems' built
  IDs) is finally built, because federation is what makes concurrent writers real.
- **F4 Cross-instance obligations.** A commitment whose condition reads one record and
  whose outcome fires in another — governed on both sides, refusable on both sides.

**Honest caps.** Transport/discovery/naming are composition-layer; trust bootstrapping
between strangers is C4-dependent and partially a human ceremony; this campaign's paper
must be re-derived after C5 exists, because its objects ARE C5's descriptions in motion.

## 5. CAMPAIGN 7 — METABOLISM AT SCALE: the living organisation (resolution: LOW, deliberately)

**Essence.** The machine runs a real organisation end to end. The TWC 33-seat reference
userland — the estate's original proving example — is re-hosted ON gov-os: separation of
powers as daily practice, metabolism driving actual rule retirement, review cycles firing
from obligations, sterility debt measured instead of preached.

**End-state invariants (named, not yet lowered):**
- **M1 Separation as workflow.** Content never reviewed by its maker at organisational
  scale; the watched braking the watchers as routine, not demonstrator.
- **M2 The gauge gets its consumer.** Metabolism and paper-tiger views drive real
  retirement decisions; the cadence-windowed upgrade (EP-10's noted cap) lands because
  someone now reads the dial.
- **M3 Sterility debt instrumented.** Diversity of perspective with a guaranteed say,
  measured as an engineering property of the running organisation.
- **M4 The 33-seat parity oracle.** The organisation the corpus describes, reproduced on
  gov-os, differential-oracle style: the proving example proves the platform.

**Honest caps.** Everything here is invariant-level on purpose; the campaign's real paper
is written when C2 (authority) and C5 (language) exist, because an organisation is made of
exactly those two things: who may act, and rules described well enough to live by.

## 5b. The version ladder

What each campaign completion MEANS as a release is its own paper: `design/33-VERSION-LADDER.md`
— v0.1 engine (end of C1, now: proves the architecture to its builder), **v0.2 pilot (end of
C2: the first rung where a second person can trust the guarantees — THE release line)**,
v0.5 real kernel (C3), v0.7 sealed (C4), v0.9 fluent (C5), v1.0 the platform (C7). Pilot-ready
is the C2 doorway, NOT the C7 destination; C7 is the full thing. The ladder's honest cap:
v0.5's OS-rate performance is the single biggest unproven risk on the horizon.

## 6. Standing rules for the horizon

1. Each campaign launches only off a full design/31-shape paper by the sitting mentor
   (xhigh), pressure-tested (two passes minimum — the design/31 precedent), ruled by the
   owner. This document binds DIRECTION; the launch paper binds BUILD.
2. Campaign order changes are one owner word; the lattice above states which swaps are
   cheap (C3↔C4) and which are not (C5 before C6 is firm).
3. Every campaign inherits the standing method unchanged: the review bar, the probe
   discipline, evidence-outlives-the-session, append-only logs, owner gates raised never
   accepted, plain functional language to the owner — and the standing frame.
4. This paper is re-dated and re-ruled whenever a campaign completes: each completion
   re-prices the horizon (what C1 taught reshaped C2's draft twice; expect the same).
5. **What each rung MEANS as a release** — what may honestly be claimed, to whom, at
   which campaign boundary — is `design/33-VERSION-LADDER.md` (v0.1 engine now; v0.2
   the pilot rung at C2; v1.0 the platform at C7). The ladder re-prices with this paper.

---

## ADDENDUM — 2026-07-25 — CAMPAIGN-2 CLOSE RE-PRICING (standing rule 4; RAISED to the owner)

Campaign 2 completed (EP-14..20; suite 474 green; all ten J-invariants delivered,
all four deferred constitutional laws live; EP-20 review RAISING). Per standing
rule 4, its completion re-prices the horizon. What C2 taught, folded here as the
definitive-until-refined (each C3 launch paper re-derives at full resolution):

- **The lattice held; the reason sharpened.** "C2 before C3 — floors before
  furniture" was right, and C2 taught WHAT the floors are: grant-based authority
  (positive grant + computed complement), not authenticated identity. So DEPTH takes
  real custody while the acting actor is still CALLER-ASSERTED (identity is resolved
  into provenance and gated by grants, but the caller is not yet authenticated as the
  account it claims — EP-20 finding R20-2). DEPTH inherits cannot-do-quietly, not
  cannot-do-at-all; K1 (authority, not shadow) must be read with that cap. This does
  NOT reorder C3↔C4, but it names cryptographic identity (C4 Q2) as the closure DEPTH
  is building toward, not standing on.

- **A SECOND unproven performance risk joins v0.5's OS-rate (§5b).** The authority
  fold — `covers` / `power_view` — is consulted at EVERY gated act and every hop,
  full-scan and un-accelerated (design/31 §7, correct-but-unmeasured). At OS rate
  (C3 K3) this compounds with the recording cost. It is priced as a MEASURED
  calibration, never a stored table (that is RBAC through the back door); DEPTH's
  per-subsystem speed-tension resolutions (max tier) must include the authority fold,
  not only the record write.

- **The zero-trust regime is now a horizon CONSTANT.** The owner's 2026-07-25 ruling
  (structured work = blocked-by-default zero trust; unstructured = deontic governance)
  makes the openness grant SCAFFOLDING that narrows to zero. Consequence for every
  campaign after C2: the world CAN retire openness completely (EP-20's
  T-OPENNESS-CAN-RETIRE proved it — no wedge, no leak), and a pilot space is BORN
  zero-trust, never carved from an open world. C5 LANGUAGE's charter gains the U-side:
  grow the deontic vocabulary (dos/don'ts/should/may, claimed-vs-effective strength)
  into full CGL enforcement terms — the governance of the unstructured half the binary
  gate cannot express. G2 (attract-class enforcement) and G3 (toothless-must
  generalized) are where that lands.

- **v0.2 "pilot" is reached** (§5b, design/33) — the first rung where a second person
  can trust the guarantees — pending the owner's campaign-close word. No horizon rung
  moves; the pilot rung is confirmed as the C2 boundary, not advanced or delayed.

RULED — owner, 2026-07-25 ("yes confirm"): the re-pricing binds on DIRECTION until
the C3 launch paper re-derives it at full resolution. [Was: raised for ruling.]

---

## ADDENDUM — C3→C5 intake: four feeds campaign 3 produced for the LANGUAGE campaign (2026-07-31, the paper-author seat; binds nothing — the C3-close re-pricing consumes it)

Recorded so the C5 launch paper starts from what already ran rather than a
blank page. Each names its source; §3's resolution stays MEDIUM on purpose.

1. **A CGL classifier is already running in live law.** `design/10` §11.1b
   (the setxattr ruling, filed as a class): a write whose CONTENT is
   prescriptive is LAW-class, whichever syscall carries it — the
   structurality gradient adjudicating class by content, not carrier. G4's
   translation surfaces inherit a working precedent.
2. **The deontic side has standing customers waiting.** The owner's §4b.6
   ruling routes consumption remedies to human judgment under the deontic
   vocabulary; the exposure and re-ask views (built, EP-26) are live
   consumers of a vocabulary that does not exist yet. G2/G3 land onto them.
3. **G5 has a method seed that will have run once.** EP-33 item 31's
   assumption-outside review leg — do the claims survive without their
   vocabulary — is who-derives-who exercised at review scale before C5
   builds it as machinery.
4. **K12's discipline reaches grammar packs** (`design/36` ADDENDUM S):
   packs are authored variable-free where possible, and an enumerating
   vocabulary states what a new member's arrival does to it.
