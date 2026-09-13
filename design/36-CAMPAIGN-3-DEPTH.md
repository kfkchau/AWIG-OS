<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-09-02 -->
# GOV-OS — Campaign 3: DEPTH — the record machine takes custody

**Status:** v1 DRAFT, 2026-07-25, written at the owner's commission by the
C3/C4 paper-author session (a seat separate from the sitting mentor, per the
owner's 2026-07-25 direction), tier xhigh. This document replaces the
interrupted draft fragment of the same date at this path (39 lines, cut
mid-sentence; git history retains it — its §1 sources are carried forward
here). Gates: GATE 1 (shape) and GATE 4 (the invariant→test→EP table, §8b)
are carried in this paper; GATE 2 (two pressure-test passes) is recorded in
§10; GATE 3 (the owner's ruling) is OPEN — the ruling list is §11. The
sitting mentor reviews this paper against the four gates before any EP
dispatches. Owner rulings control over everything here.

**[AMENDMENT, 2026-07-26 — GATE 3 CLOSED on items 1–4.]** The owner ruled
§11 items 1, 2, 3 and 4 all YES on 2026-07-26, folded by the sitting mentor
the same turn (the rulings are marked at each item below, and the record
entry is at BUILD-PROGRESS file end). This paper is campaign 3's definitive.
Items 5 and 6 are unchanged: item 5 is a value the owner sets when EP-25
reaches it, item 6 is his word at the EP-28 kernel-entry gate. GATE 3 is
therefore satisfied for everything the campaign needs today. **GATES 1, 2
and 4 remain UNGRADED:** the paper carries them, but the sitting mentor's
four-gate review has not run — the seat holding this campaign was set below
the tier that review requires and stopped rather than grade at depth
(00-READ-FIRST §4a; the tier-honesty stop rule). No EP dispatches on this
paper until that review passes. Citations are by
doc-number + section. Labels per 00-READ-FIRST §6: SOURCE-DERIVED (cite) /
INFERRED (from what) / PROPOSED (cost if wrong) / trained knowledge (flagged).

**[AMENDMENT, 2026-07-26 second entry — GATES 1, 2 and 4 GRADED; §4b
corrected at five places.]** The sitting mentor's four-gate review ran at
xhigh on 2026-07-26. Gates 1, 2 and 4 PASS, and with gate 3 already closed
this paper binds as campaign 3's definitive. The independent re-derivation of
§4b found five places where the specification is incomplete rather than
wrong; they are carried in ADDENDUM A at this file's end, which is law and is
read as part of §4b. One of the five widens a refusal and is marked there as
awaiting the owner's word.

---

## 1. Sources

The ruled horizon at the campaign-2 close — design/32 §1 (K1–K5) and its
2026-07-25 re-pricing addendum (RULED "yes confirm": binds direction until
this paper re-derives at full resolution). The bridge — design/16 (stances
2–4 are this campaign's ground; the design index orders it read first). The
ports contract — design/10 (the syscall conformance map and its standing
three-check test spec; the real-time carve-out per the 2026-07-13 ruling).
The speed method — design/22 (minor faults record nothing; record rate tracks
decisions). Capacity — design/23 (three levers; horizons are the owner's
calibration). The driver boundary — design/24. The two times of authority —
design/35 (owner-ruled 2026-07-25), with design/34 (the seal, RULED adopted
as its backstop; lands as one check kind per its §6). The wall-primitives
handover (items 1, 2, 4, 6 flagged to this paper by that document itself;
item 8 priced with capacity; items 3 and 7 already standing as E1/E2). The
owner-ruled build route (2026-07-13: hollow-out through the bridge, user
space first, kernel last and smallest, files → devices → comms → memory →
scheduling; pinned vanilla 6.18.38 to build in, the exact Ubuntu kernel to
validate on — planning/10-BUILD-ROADMAP and the vm lab docs carry it). The D8
scope ruling (owner, 2026-07-14, planning/build/DECISIONS.md: core subsystems
IN, driver-support breadth OUT). The campaign-2 close: DIGEST-C1/C2 (the
standing theorems 1–12 and the method), the zero-trust regime ruling
(design/30 and /31 dated addenda), the caller-asserted boundary R20-2 (rides
to campaign 4), wire-at-birth (carried verbatim, DIGEST-C2 §8), and the open
items the author's brief names with their homes. Machine evidence: suite 474
green at close; founding v1.6.1; v0.2 "the pilot" official (owner's word,
2026-07-25). M1's stage spec — planning/11 (its residence assumption is
superseded here, §7 item 4). The existing stepping-stones: the host FUSE
flat-namespace proof (D9) and the layer1 in-kernel gate+record primitive
proof (D11).

## 2. The essence (one paragraph, functional)

Campaign 3 gives the record machine custody of real operating-system
resources. Today it governs its own record; at this campaign's end a real
directory tree is served from the record through interfaces ordinary
programs already use — a program saves a file and that save IS a gated,
rule-cited, replayable decision; kill every derived structure and replay the
record, and the same filesystem comes back. The same crossing then repeats,
subsystem by subsystem behind unchanged interfaces — devices, communication,
memory, scheduling last — with a conformance harness proving at each step
that programs cannot tell the difference. Custody also forces the seam the
estate has so far only ruled on paper: the world outside the store — real
programs, real hardware, human deciders — answers on its own clock, so this
campaign builds the crossing (external answers frozen as inputs, correlated
by the store, sealed at hand-out) and the two-times acceptance (a decision
binds from its deciding moment; late-arriving law reconciles by recorded
overturns, never edits). Everything runs under the campaign-2 authority
machinery unchanged, and under its stated cap: the caller is not yet
cryptographically authenticated, so every custody guarantee in this campaign
is cannot-do-lawfully and cannot-do-quietly — cryptographic closure is
campaign 4's work, and this campaign builds toward it, not on it.

## 3. What this campaign is NOT (scope, stated positively where possible)

Core subsystems in, driver-support breadth out (D8: the governed cores and
the device capability core, never the per-class driver menagerie — that is
what balloons to millions of lines and is not the core). The world stays
OPEN by the owner's word: DEPTH narrows nothing outside disposable test
worlds; the first real narrowing arrives with the first pilot space, as a
recorded act, born zero-trust. Cryptographic identity, record signing, and
GS-13 erasure are campaign 4. Describing other governance is campaign 5.
Federation and the S5 multi-writer sequencer are campaign 6 — this campaign
keeps one store writer; observation adapters and FUSE threads are submitters
through the one gate, never additional store writers (ordering fields stay
carried, exactly as built).

## 4. End-state invariants (the campaign is done when ALL hold)

K1–K5 carry from design/32 §1, re-derived at full resolution with what
campaign 2 and design/35 ruled; K6–K11 are this paper's extensions.
SOURCE-DERIVED throughout (design/32 §1 + re-pricing; design/35; DIGEST-C2);
the testability pointer after each names its battery rows (§8).

- **K1 — Authority, not shadow (under the stated cap).** The governed core
  AUTHORIZES real operations: a file write, a device bind, a mapping happens
  because the gate said yes, and the record shows why — the record is
  upstream of the effect, never a log of it. Mechanically testable, two
  directions: (a) no effect is released to the caller before its covering
  decision is durably appended; (b) an interrupted crossing heals
  record→effect on restart, never effect→record; and custody state is
  derived — kill it, replay, identical service. The cap, named in the
  guarantee itself: the acting caller is caller-asserted until campaign 4
  (R20-2), so K1 delivers cannot-do-lawfully + cannot-do-quietly, not
  cannot-do-at-all. → T-RECORD-UPSTREAM, T-CUSTODY-IS-DERIVED.
- **K2 — Semantic identity at the ports.** The syscall surface keeps its
  meaning exactly (design/10 rows: same returns, same errno, same visible
  ordering; /proc values reflect gov-os's true derived state — shape
  promised, dynamic bytes not). The RULED carve-out stands: for the
  real-time scheduling classes the timing bound IS the semantics and is
  promised there. One reconciliation note (from K7): state changed by an
  overturn sweep surfaces to programs as ordinary later events — a file
  changing because the system executed a recorded overturn is ABI-ordinary
  (files change when others write them); no past return value is ever
  falsified, and fsync's durability claim binds on the record, which never
  un-happens. → T-SYSCALL-SEMANTIC, T-UNMODIFIED-PROGRAM, T-REALTIME-BOUND.
- **K3 — I9 at operating-system rate, both costs.** Recording scales with
  governance, never operation (design/22: the hot path is a cache fill that
  appends nothing) — AND the authority fold consulted at every gated act is
  priced the same way (the re-pricing's second risk). The gating contract IS
  the design/10 class map: DECISION/LAW-class calls cross the gate;
  CACHE-only calls consult views and append nothing; STREAM is sampled
  aggregate. Acceleration of either cost is a measured calibration with a
  named owner — never a stored table (a stored permission table is the
  refused reference arriving through an unchecked path), and any cached fold
  answer obeys coherent-or-refuse (the R26 law: a hop never lies).
  → T-RATE-GOVERNANCE, T-FOLD-AT-RATE, T-NO-STORED-TABLE.
- **K4 — The differential oracle at OS scale.** Every swap proves
  behaviour-identical against the un-swapped original over real workloads:
  the design/10 harness runs dual-target (pinned stock baseline, then the
  governed target) with all three checks per row — ABI identity, recording-
  class fidelity, replay invariance. Shadow-diff holds empty before any
  assume; a divergence halts the assume and is recorded (design/16 §4). The
  whole-class pinning law applies to the harness's baselines: captures from
  the stock target are pinned artifacts, never re-read live.
  → T-CONFORMANCE-BASELINE-PINNED, T-SHADOW-DIFF, T-DIVERGENCE-HALT.
- **K5 — Smallest possible kernel residence.** What enters the kernel is the
  minimum custody requires; the record machine's brain stays where it is
  testable (user space). The in-kernel surface is enumerable and enumerated —
  a standing residence audit lists every file/function that crossed the
  syscall line and the custody function that justifies it.
  → T-KERNEL-RESIDENCE-ENUMERATED.
- **K6 — Custody never outruns authority.** Every custody DECISION is an
  ordinary granted act through the ONE gate under the four-dimension grant
  law — no subsystem acquires its own authority path, and the four
  power-structure theorems (DIGEST-C2 §2, 7–12) hold unchanged over custody
  ops. External caller identity at the ports resolves by the EP-15
  invoker/actor split: the kernel-asserted uid is EVIDENCE recorded in
  provenance; the acting actor derives from recorded mapping acts, never
  from a synchronized user table. The openness grant is the only openness
  (scaffolding, untouched this campaign); any pilot/test world is born
  zero-trust. → T-CUSTODY-MATRIX, T-UID-IS-EVIDENCE, T-OPENNESS-UNTOUCHED.
- **K7 — Two times govern every crossing.** A decision binds from its
  deciding moment (design/35): the store's acceptance evaluates each
  arriving decision against the LAW in force as of its deciding time, with
  the seal as proof of the world it was decided in — while AUTHORITY (the
  chain) is always evaluated live at effect time (a revoked chain refuses at
  the door regardless of deciding time; the two verdicts carry different
  information — design/34 §2 generalized). For synchronous S-plane acts the
  two times coincide by construction (the gate decides and appends in one
  act), so nothing changes for the machine-speed path; the regime is
  load-bearing exactly where deciding happens away from the store — observed
  happenings (every M1 observation arrives after its occurrence: the observe
  world is ALREADY a two-times world), external answers, human decisions.
  Late-arriving law reconciles by the sweep (§4b): appended overturn
  decisions acting forward, never edits; record_time remains the sole total
  order. → T-TWO-TIMES-ACCEPT, T-OVERTURN-SWEEP, T-OVERTURN-REACH.
- **K8 — External answers are frozen inputs.** Any answer produced outside
  the S-plane enters as an INPUT-class record correlated BY THE STORE (the
  answer record cites the hand-out's identity; an in-band token proves
  nothing) and version-pinned whole-context (template@version +
  answerer-identity@version + parser@version + context snapshot hash).
  Replay consumes the frozen answer and never re-runs the answerer — the
  clock-as-sensor law generalized to every oracle. The vault's stored value
  finds its intended consumer here: a credential the SYSTEM presents on an
  external call that no actor ever reads. → T-CROSSING-REPLAY,
  T-CORRELATION-DERIVED, T-CONTEXT-PINNED, T-VAULT-CONSUMER.
- **K9 — The judged world is checkable.** The `fingerprint` check kind
  (design/34 §6, RULED adopted): hand-out records the canonical hash of the
  declared input-view; return recomputes with the same pack definition;
  mismatch refuses citing the staleness rule; staleness and authority remain
  two separate verdicts. Returns run in the governance lane — the check
  never rides a per-operation hot path (K3 untouched, design/34 §6).
  → T-FP-HOLDS/-STALE/-ORTHOGONAL-REFUSAL/-ABA/-REPLAY/-CANONICAL.
- **K10 — Sessions are known contact points.** A decider's live working
  context is recorded (session-open/close) with a DECLARED read-set — and
  declared is derived necessity, not laziness: reads append nothing by
  design (I9), so the store cannot compute a session's exposure; the seal is
  what makes under-declaration harmless to legitimacy (only to convenience).
  Law-family records ride priority lanes in both directions, the lane a
  property of the record kind, read from the record; a law change whose
  reach intersects a live session's declared view is delivered on the lane
  immediately. Deliveries stay derived and append nothing (kill the queues,
  replay, identical). This `session` is the design/35 decider session — NOT
  the POSIX setsid session; the glossary carries the distinction (§5 note).
  → T-SESSION-PUSH, T-LANE-PRIORITY, T-PUSH-APPENDS-NOTHING,
  T-BACKPRESSURE-RESERVE.
- **K11 — Campaigns 1 and 2 survive custody.** Every I-invariant
  (design/28 §1) and J-invariant (design/31 §1) holds with the custody
  machinery loaded, and the total round-trip extends into every dimension
  this campaign introduces: kill everything derived — custody caches, shadow
  tables, the session registry, lanes, in-flight crossing state — replay
  from the record alone, reconstruct identically, custody answers included.
  → T-TOTAL-ROUNDTRIP-3, plus the full C1/C2 probe ledger re-run (EP-33).

### 4b. The overturn-reach specification (the derivation design/35 §6 defers to this paper)

SOURCE-DERIVED from design/35 §§0–2 and the standing laws cited inline; the
two policy defaults marked PROPOSED are raised in §11.

Given a law-family record L arriving with deciding time d(L) and recording
time r(L), d(L) < r(L):

1. **The candidate interval.** Candidates are recorded acts X with
   r(X) < r(L) and d(X) > d(L). Acts with d(X) ≤ d(L) stand — legitimacy
   created at a moment binds acts decided strictly after it (an act decided
   at exactly the law's own deciding moment was not decided under it; the
   tie test is a checkable field comparison, so determinism holds). Acts
   arriving after r(L) are never the sweep's business: the ordinary door
   adjudicates them at their own acceptance, against the law as of THEIR
   deciding time, which now includes L.
2. **The reach test is the gate's own test, run counterfactually.** X is
   reached iff re-evaluating X's admission as of d(X) with L present flips
   the recorded outcome. The rule's trigger chain, its scope, and space
   containment (J2/J5) do all the narrowing — no separate reach matcher
   exists; the one interpreter is the matcher (minimality: derived, not
   added).
3. **Direction one — a permit flips to refusal.** The sweep appends an
   overturn DECISION citing L, X, and both deciding times. Derived state
   recomputes forward from the overturn's record_time; asOf answers before
   the overturn still show X's effect. Order is untouched; validity is what
   changed — two frames, two answers, no contradiction.
4. **Direction two — a refusal flips to permit.** No overturn is appended:
   an overturn cannot perform an act that never happened, and a record
   claiming an effect that did not occur is the one forbidden lie. The case
   surfaces on a derived RE-ASK view; the remedy is re-submission at the
   current head. [RULED (owner, 2026-07-26, §11 item 4): re-ask stands; no
   fabricated effects. Was PROPOSED at authoring; the ruling makes it law
   and EP-26 lowers it as written.]
5. **Transitive reach, computed not stored.** Excluding X may flip acts that
   depended on X (an act admitted under a grant X minted). Dependence is
   never stored; it is recomputed: re-evaluate candidates with the overturned
   set excluded, in record order, round by round, until a round appends
   nothing. Exclusions only shrink the permitted set (grants are positive;
   the complement is computed), so the iteration is monotone decreasing over
   a finite record: it terminates, and replay reconstructs the same overturn
   sequence (the sweep is itself an ordinary governed act of the SYSTEM,
   citing the design/35 law).
6. **The sweep reconciles state, never the past's consumptions.** What was
   already consumed under a since-overturned act (bytes read, an answer
   delivered) is out of mechanical reach. The record derives an EXPOSURE
   view — who consumed what under which overturned act — and the remedy is
   judgment on the deontic side (design/30 addendum: guidance-and-obligation
   for what binary gating cannot express). [RULED (owner, 2026-07-26, §11
   item 3): the split stands — the sweep reconciles state, the exposure view
   surfaces consumption, the remedy is human judgment. Was PROPOSED at
   authoring; the ruling makes it law.]
7. **The sweep's own power arrives leashed (wire-at-birth, carried
   verbatim).** An overturn whose target is an authority-anchor act — a
   handover, a succession, a root grant — consults the anchor guard before
   appending: an overturn that would orphan authority or move root refuses
   and routes to the owner. This is the campaign's one new op family whose
   effect could reach root authority, and its anchor refusal is part of its
   own definition, never a later patch.
8. **The cost bound and the division of labour.** Sweep work is bounded by
   the record between d(L) and r(L) — the priority lanes exist to keep that
   window small (law travels faster than traffic), and the seal (K9) closes
   the race no push can. Lanes make overturns rare; the sweep makes them
   lawful; the seal makes the residue checkable.

## 5. New record kinds and vocabulary (all in the ONE stream, class-tagged; envelope unchanged — I1 holds)

| payload.kind | Class | What it founds |
|---|---|---|
| session (open / close) | DECISION | a decider's live working context: the opening account, the DECLARED read-set (view refs); close ends push targeting. Naming note for the glossary (design/20): this is the design/35 decider session, unrelated to the POSIX setsid session — the /proc and scheduling surfaces keep the POSIX word for the POSIX thing. |
| answer-returned | INPUT | the frozen answer of an external answerer: cites the hand-out decision's identity (store-held correlation), carries the whole-context version pins; replay consumes it, never re-runs the answerer |
| overturn | DECISION | the reconciliation verdict: cites the reaching law (or overturned ancestor), the overturned act, both deciding times; anchor-guard-wired at birth (§4b.7) |

What deliberately does NOT enter as a new kind (minimality gate, each
derived from what exists):

- **Observed happenings (M1)** are the EXISTING classes with observer
  provenance (asserted_by = the observer, provenance = the window@version it
  saw through) — an observed act is a DECISION the box authored under
  Linux's authority, not a new kind (planning/11 §2's honesty rule stands).
- **Custody operations** (open/write/bind/map/…) are per-op decision records
  born of CREATE-OP definition records, per the design/10 class map — the
  catalogue grows by data, not by record class.
- **The external-judgment station** (wall primitive 1) is op_definition
  DATA: an op whose definition names an external executor; the interpreter
  suspends at hand-out and resumes on answer-returned. In-flight crossings
  are a derived view, reconstructible from hand-out + answer records — no
  stored futures, no callback registry.
- **Lanes** are a property of the record kind family, read from the record;
  **budgets and backpressure** (primitive 8) enter as recorded rules
  (policy keys with named owners); **tiering decisions** (design/23 lever A)
  are decisions citing the recorded tier policy, entering only when measured
  volume warrants (§6, EP-27 note).
- **The `fingerprint` check kind** is an ENGINE amendment (design/28 §5's
  law: design-doc row + owner gate — the gate is satisfied by the design/35
  adoption ruling; the row is swept at the landing EP's verdict).

## 6. The EP sketch (numbering continues the estate sequence; sizes/tiers PROPOSED — Estimate — Medium for Arc C, which re-prices at each gate)

Resolution honesty (the roadmap's own discipline, planning/10 §0): Arcs A
and B are specced here to launch grade; Arc C EPs are direction-binding —
sized and tiered now, their EP files authored only when their predecessor's
gate is observed green. This is the standing rule, not a gap.

**Pre-flight (before the campaign opens — the EP-13B pattern):**

- **EP-20B — the pre-C3 fix pack.** S, high. Depends: the owner's campaign
  word. Contents: R20-1, the directed retirement of the dead protection
  boot-fallback (fence names protection.py; the owner's disposition "ride to
  the pre-C3 window" already given). Nothing else enters — the pack stays
  minimal so the campaign launches from a reviewed, closed base.

**Arc A — the workbench, the shadow, and the crossing (user space, no authority taken):**

- **EP-21 — M0: the lab, stood up and proven.** S, medium. Depends: —.
  The KVM guest, the clean-snapshot-and-rollback loop proven BEFORE any
  module loads, the layer0 load/unload loop, the pinned 6.18.38 staged.
  planning/vm/01 is the runnable checklist; its four gate lines are the
  acceptance. Commands are dated trained knowledge — re-verify versions.
- **EP-22 — M1: watch and record (bridge stance 1→2).** L, high. Depends:
  EP-21, EP-20B. The observation adapters (/proc scan, proc-events
  connector, fanotify/inotify, netlink uevents, sock_diag; eBPF optional)
  submitting through the BUILT kernel's gate as ordinary ops — planning/11
  is the stage spec, with its residence assumption superseded (§7 item 4):
  the spine is the campaign-1/2 engine, not a fresh lift. Every observed
  record carries observer provenance and window@version (primitive 5 enters
  here). Adapters are submitters through the one gate — S5 stays deferred;
  no sequencer is built. This EP also opens the campaign's measurement
  ledger: the first real numbers for BOTH K3 costs (append rate, fold cost)
  are taken here in observe mode, where nothing can break — the calibration
  evidence the custody EPs consume. Coverage is a named calibration with an
  evidence step (the coverage audit), never an assumption.
  Wrong reference (named for the EP file): the audit daemon / log shipper —
  events as diagnostic lines downstream of state. Taking it erases the one
  write path, the record classes, replay identity, and coverage statements.
- **EP-23 — The crossing: external answers as frozen inputs.** L, xhigh.
  Depends: EP-20B (engine base; suite-testable without the VM). Wall
  primitives 1, 2, 5, 6 and the seal, landed as one seam: the external-
  executor station (op_definition data; suspend at hand-out, resume on
  answer), the answer-returned INPUT verb, store-held correlation,
  whole-context version pinning, and the `fingerprint` check kind
  (design/34 §6 verbatim — its six named tests ship with it, including the
  canonicalization battery, which is TCB-grade). The vault-consumer
  derivation lands here: an external call presents a vault-held credential
  the SYSTEM uses and no actor reads (the brief's carried derivation).
  Wrong reference (named for the EP file): async-RPC futures and callback
  registries with in-band correlation tokens. Taking it erases replay of
  in-flight crossings (a future dies with its process; the record machine
  reconstructs crossings from records alone), correlation-as-derivation
  (the store binds request to response; a token proves nothing), and the
  never-re-run-the-answerer law.
- **EP-24 — The conformance harness (the campaign's standing instrument).**
  M, high. Depends: EP-21 (a guest to calibrate against). design/10 §3 made
  executable: each row an assertion with the three independent checks (ABI
  identity, recording-class fidelity, replay invariance), dual-target —
  calibrate against the stock kernel, capture PINNED baselines (the
  whole-class pinning law applied to baselines), then run against any
  governed target. Built as its own EP so the instrument is never authored
  by the EP it judges (the separation principle applied to tests).
  Wrong reference: adopting an existing conformance suite wholesale as the
  oracle — it checks only the ABI leg, and the recording-class and replay
  legs are exactly what makes a swap a governed swap.

**Arc B — custody in user space, and the two-times machinery:**

- **EP-25 — M2: files take authority (FUSE). THE CAMPAIGN CRUX.** L, xhigh.
  Depends: EP-22, EP-24. A real mount served from the record: file events
  become gated, rule-cited decisions; content goes to content-addressed
  blobs; the tree is a derived cache; asOf and history are native; real
  unmodified programs (cat, ls, git) cannot tell the mount from a native
  one. Extends the D9 flat-namespace proof to full tree custody; the stale
  stepping-stone runner (src/bridge/run_fuse_files.py, campaign-1 findings)
  is rebuilt or retired inside this fence — its named home. Identity at the
  port per K6: uid is recorded evidence, actor resolution derived. The
  write-coalescing policy (design/10 §6, write row) enters as a recorded
  policy with a PROPOSED default — an owner calibration (§11 item 5).
  Shadow-diff runs continuously; a deliberate divergence halts the assume
  (both failure directions tested: a divergence that fails to halt, and a
  false halt that blocks a lawful assume).
  **THE WRONG REFERENCE THIS CAMPAIGN EXISTS TO REFUSE — the journaling
  filesystem.** The template that WILL fire: a passthrough filesystem with a
  log bolted on — the record as a journal OF the filesystem instead of the
  filesystem as a VIEW of the record. It is the estate's oldest diagnosis
  ("a journalling filesystem already keeps the ledger and calls the wrong
  half truth" — planning/10 §2) and it is invisible to the ABI leg of the
  harness: a passthrough-plus-log passes every syscall row while K1 dies
  silently, because truth lives in the host filesystem and the record is
  decoration. Only the replay leg catches it: kill the derived tree, replay
  the record alone, the mount must serve identical content
  (T-CUSTODY-IS-DERIVED). A second named template, same family: a uid↔account
  sync table — a stored identity status; the mapping is recorded acts, the
  resolution a fold (K6).
- **EP-26 — The two-times acceptance, the session registry, and the sweep.**
  L, xhigh. Depends: EP-23. Acceptance adjudicates arriving decision- and
  law-family records by deciding time + authority with the seal as proof
  (K7's split stated in code-facing law: law as of deciding time, authority
  live at effect time); occurrence_time becomes load-bearing for these
  records (no envelope change — design/35 §5); the session record kind with
  declared read-sets; the reconciliation sweep implementing §4b exactly,
  overturn op anchor-wired at birth (§4b.7); the re-ask and exposure views
  (§4b.4/.6). The observe world's records (EP-22) become the first live
  consumers: every observation is a d<r record adjudicated honestly.
  Wrong reference (named for the EP file): arrival-order adjudication —
  last-writer-wins, commit-time semantics, or compensation frameworks that
  reconcile by editing state. Taking it erases the two frames (legitimacy
  vs order), append-only overturns, and the law/authority split — the
  exact content of the owner's ruling.
- **EP-27 — Lanes, session-aware push, and budgeted backpressure.** M, high.
  Depends: EP-26. The law-family priority lane in both directions (lane =
  record-kind property, read from the record, never a code verb-list); the
  standing push (design/28 §6) extended per-view over known active sessions
  (deliver a law change to every live session whose declared view it
  reaches, on the lane, ahead of ordinary traffic); budgeted lanes with
  priority-aware backpressure and a reserved emergency budget (wall
  primitive 8, priced with design/23's levers — budgets are recorded rules
  with named owners, values owner-calibrated from EP-22's measurement
  ledger). The flood boundary holds: deliveries are derived and append
  nothing. Capacity lever A (tiering) does NOT get a scheduled EP: its
  mechanics enter as their own S/M EP when the measured volume crosses the
  owner's threshold — raised then, not built on spec now.
  Wrong reference: lanes and budgets as engine configuration — constants in
  code, a QoS table. Priority is law-data; a lane no record can cite is a
  vocabulary with governance content in code (I5 refuses it).

**Arc C — below the syscall line, breadth over the proven depth path
(direction-binding; EP files authored at predecessor-green; sizes/tiers
Estimate — Medium):**

- **EP-28 — M3: files below the syscall line (bridge stance 4).** L, xhigh;
  its speed-tension work item (the write-decision path and the authority
  fold on open/write, worked to the floor) runs at MAX, per design/32 K3.
  Depends: EP-25, EP-24; OWNER CHECKPOINT at dispatch — entering the kernel
  is the owner's word even with the route long ruled. The proven records-
  backed filesystem moves from the FUSE server into the kernel's VFS layer
  behind the unchanged interface; validated on the pinned 6.18.38 AND
  accepted only when green on the exact Ubuntu kernel; fallback to stock
  files stays local. The layer1 primitive proof (D11) is the seed. /proc's
  files slices land as computed views (design/13 §8).
  Wrong reference: porting the record machine into the module — the kernel
  residence is the minimum custody requires (K5); the brain stays in user
  space where it is testable.
- **EP-29 — M4: devices — capability-as-law and the shim.** L, xhigh.
  Depends: EP-28. design/24's four crossings (register=LAW, bind=DECISION,
  IRQ=INPUT, I/O=STREAM), shadow first (observe via the kernel's own
  notification surfaces), interpose second; the LAW→bind→I/O chain enforced
  at the typed boundary; fault containment recorded (a driver fault revokes
  the binding, recorded, cited). D8 bounds it: the capability core and the
  general shim contract — never the per-class driver annex.
- **EP-30 — M5: comms.** L, xhigh. Depends: EP-29. Channels, messages, and
  the custody-transfer cases (fd passing as recorded custody transfer);
  record-as-only-shared-medium inside the kernel; userland shared memory
  honoured at the port (grant recorded, interiors unaudited — the standing
  honest boundary).
  **[AS-BUILT + SCOPE RULING, 2026-08-19, the architect seat, discharging
  the mentor's raise at board :1151. EP-30 as executed delivered REVOCATION
  END TO END — capability at W1a, first law use at W1b, enforcement at W2,
  founding 1.24.0→1.26.0 through its own front door — after E1's
  establishment redirected the family at :918, and ZERO comms units were
  ever authored. EP-30 CLOSES AS-REDEFINED when W3, R2's close and MAINT-1
  land: its closed units each met their acceptance sets, and un-begun scope
  is a plan-list entry, not a debt inside an EP. THE COMMS REMIT ABOVE IS
  NOT DISCHARGED: it re-scopes VERBATIM as **EP-30-C — M5: comms**, fresh
  units, fresh authoring, the entry above read as its text. THE DEPENDENCY
  EDGE FOLLOWS THE SUBSTANCE, NOT THE NUMBER: EP-31 depends on EP-30-C —
  §2's crossing order (devices, communication, memory, scheduling) is the
  owner's language and stands — so EP-30's close unlocks nothing. ADDENDUM
  S's "EP-30's comms" resolves to EP-30-C; K12's owner-ruled substance is
  untouched, one pointer re-resolved.
  AS-BUILT 2026-08-19, second entry: W3 lands SEVEN of TEN and closes
  with A7 unmet-and-disclosed — the three held reds are controls whose
  subject W2's law consumed, ruled a NEW UNIT (board :1338); every exit
  inside W3 was closed by W3's own stops. THE CLOSE SET GROWS BY THE
  DISCOVERED MEMBER: EP-30 closes as-redefined when W3 (closed), R2's
  close, MAINT-1, AND the named successor carrying the three rows have
  all landed — the suite-green witness is part of what CLOSED means at
  the campaign's front. Board :1340 records the absorption.
  AS-BUILT 2026-08-20, third and closing entry: THE CONDITION MET AND THE
  CLOSE FILED — W3 :1361 (A7 unmet-and-disclosed) · W4 :1421 (the named
  successor; all three subject rows repaired, none retired) · R2 :1451 ·
  MAINT-1 :1467. EP-30 CLOSED AS-REDEFINED at board :1478, the mentor's
  hand, four closes every one carrying disclosed open items. The close
  unlocked nothing, exactly as ruled above. EP-30-C's authoring is
  unblocked on BOTH halves the same day: this close (the ladder's half)
  and the owner's YES on the coalescing gate (board :1475 — his word
  dissolved the threshold framing into a tier answer; the derivation is
  in planning/build/OWNER-GATE-COALESCING.md, and the first EP-30-C unit
  built carries E.4's three measurements as acceptance rows or the
  confirmation was taken on nothing). The comms units author under
  design/39, whose §3→§5 pointer landed before any unit cites it.
  THE EP-30-C PLAN LIST, enumerated 2026-08-20 at the architect's hand,
  discharging the mentor's :1480 raise. DIVISION RULED FIRST: the LIST is
  the architect's and the UNITS are the mentor's — archi-doc-standard's
  authorship table (the plan list lives in the arch doc, WHAT is the
  architect's) read through this campaign's :767 division (the mentor
  authors build-grade, the architect countersigns); proposed by the mentor,
  concurred here, the self-dealing gate met by counterpart proposal plus
  standard citation. One line per unit; the mentor's authoring lowers each;
  re-tiering or resequencing is the mentor's raise as a mechanical delta.
  PRECONDITIONS BEFORE THE GROUP ACTIVATES (not units): the three ipc-comms
  DISPUTED rows and any no-activation-home rows ruled (EP-30.md ADDENDUM 1
  item 7, the mentor's owed pre-work); EP-28C's built channel state read
  before anything is specified about record flow under concurrency (item 6).
  C0 | ESTABLISHMENT — the substrate facts landed as CLAIMS, red on silent
  accommodation: the blob-store durability home RULED with its reason
  (engine or bridge; the law stated as ordering — CONTENT DURABLE BEFORE
  THE RECORD THAT NAMES IT); the store composition made ASSERTABLE (a test
  can tell which store it got); design/39 §2's entity/process/custody row
  vocabulary established for the group | XHIGH · REVIEW TIER RED (the
  :1492 home ruling puts the barrier in src/kernel/blobs.py, an engine
  pass by construction; countersign is WHOLE-PLAN per EP-SHAPE §1) |
  order 1 | PENDING
  THE REVIEW AXIS, stated for the class and not the instance (the
  mentor's raise of 2026-08-20; XHIGH above is the SEAT axis and was
  never the review tier): each unit's review tier is stated at its
  authoring, and ANY unit whose fence enters src/kernel/ is an engine
  pass reviewed RED by the MUST-NOT-TOUCH baseline's own condition —
  whole-plan countersign follows automatically. C1–C6's tiers are set
  when their fences exist, not guessed here.
  C1 | CHANNEL LIFECYCLE AS ENTITY CROSSINGS — opens/closes are DECISION
  events on the ENTITY's channels, never traffic between processes; the
  two-channel invariant with the user-facing channel first-class and
  distinct (consent and presentation live there; external-world seam);
  any additional opening is a raise; permission rows land on the entity,
  incarnation rows on the process | XHIGH | order 2 | PENDING
  C2 | SEND/RECEIVE UNDER THE CONFIRMED COALESCING POLICY — carries the
  owner's-YES measurement obligation BY NAME: E.4's three rows as
  acceptance (folding changes no verdict, no cited rule, no replayed
  state; conformance spread measured at zero on the third round), payload
  full-fidelity under honest STREAM aggregation, the policy landed as a
  recorded policy under latest-wins. THE REFERENT LOWERED AND DISCLOSED:
  the gate file says "the first unit built" — C0 and C1 hold no sends, so
  no folding is exhibitable before this unit; C2 IS the first unit in
  whose world the obligation can bind, and NO unit that records sends may
  close before C2's three rows are green. THE DEADLOCK IS THE INTENDED
  FAILURE MODE, NAMED AS ONE (the mentor's :1482 addition, absorbed same
  day): if sends are ever moved out of C2, C2 cannot produce the three
  rows and every send-recording unit blocks behind rows that can never
  go green — a hand meeting an unsatisfiable C2 is looking at the GUARD
  WORKING, not a defect, and the repair is to put the obligation back
  where folding exists, never to drop the rows (dropping them is a
  behavioural delta, a raise to the architect by construction) | XHIGH |
  order 3 | PENDING
  AMENDED 2026-08-21 at the architect's hand, absorbing the :1747
  distribution and the :1748 debt, E.4 OPENED AT ITS OWN LINES at the
  ruling and again at this absorption: E.4's text makes the three ONE
  DIFFERENTIAL WITH THREE PROPERTIES, not three unrelated rows. AS
  BUILT, C2 delivers: REPLAYED-STATE green (established, entry-by-entry,
  byte-exact, count-only implementations shown redding) · CITED-RULE
  measured INSIDE the generic entry-wise comparison (rule_cited compared
  in every entry, four of four in the landed artifacts) and NAMED in the
  close · VERDICT owed BY NAME with its trigger at :1748 — the
  verdict-boundary differential in the first send-recording unit whose
  workload holds adjacent allowed and refused sends, tracked as an OWED,
  countersign-checked when the trigger holds. NO ROW WAS DROPPED AND NO
  SENDS LEFT C2 — the deadlock clause's subject (sends moved out) never
  occurred; a property whose SUBJECT cannot exist in a uniform-verdict
  workload was scheduled where its subject exists, by the gate's own
  obligation-follows-the-fold rule. The close-ordering sentence above is
  RESTATED by this amendment per :1747's own correction of :1481: no
  send-recording unit closes before C2's ESTABLISHED measurement is
  green, and the verdict row binds its owing unit through the tracked
  debt — an OWED with a named trigger and a signature check is a
  STRICTER form than the unwritten row it replaces, which is why this
  is absorption and not weakening. The two prior sentences stand as
  written per the standing law; this entry is the one in force.
  CLOSED 2026-08-21, board :1868, close gate driven (thirteen declared
  paths, thirteen resolving, coined control False). Twelve countersign
  cycles, §5 unmoved through every one; the work landed once (the
  eleventh build's R5 artifact the last piece) and the text converged
  to it. The close carries the :1867 limit as a stated limit, not a
  footnote: the post-edit-arm trigger was never implemented at the
  countersign and its five passes were silence saved by a
  recorded-once exemption — stack item seventeen and the cited-waiver
  discipline are the repair, minted before this close and binding
  after it. The measurement stands: fold-world and non-fold-world
  derive identical ledgers entry by entry, payloads byte-exact through
  the content-addressed store, count-only implementations shown
  redding, the empty-population falsifier warranted — the owner's
  confirmation now has the evidence its transfer condition named, for
  every property whose subject C2's world could hold.
  C3 | FD PASSING AS RECORDED CUSTODY TRANSFER — SCM_RIGHTS as custody
  transfer by FORMAL NAME, device identity inherited from EP-29's landing
  never re-derived channel-side, attributable and replayable
  (T-CUSTODY-TRANSFER) | XHIGH | order 4 | CLOSED :1949
  AS-BUILT 2026-08-21, the architect's hand, same-turn with the close:
  THE CUSTODY PLANE HAS ITS VERB. Founding 1.27.0 → 1.28.0 through its
  own door, FILE-CUSTODY-TRANSFER minted; a handover is a DECISION
  EVENT BETWEEN ENTITIES, identity inherited, the view a fold. RULED AS
  A THIRD KIND (:1875 as narrowed :1880): a law pass in C1's shape with
  C0's absence-opening — C3 ADDED A VERB TO AN EXISTING VOCABULARY
  (custody.py, 1,095 lines, predated it). ONE BUILD CYCLE; the arc's
  first first-cycle countersign (:1892), twelve C2 cycles spent as
  authoring input. TWO WALLS DID NOT LAND AND THE CLOSE SAYS SO (:1920
  ruled the naming mandatory): the transfer DOES NOT VERIFY THE GIVER
  HOLDS THE HANDLE (a current parameter against a prior record field
  has no kind in the engine's fifteen), and R1's literal reading — BOTH
  RIDE TO A SIXTEENTH CHECK KIND UNDER src/kernel, an ENGINE PASS,
  fence held. THE SCHEDULED TRAP, named by hand: FILE-OPEN took its
  first check-reader ever; a future record_stream declaration on it
  would refuse every lawful transfer and no row would red. THE
  CONSEQUENCE DISCHARGED, NOT LEFT: the law move falsified twelve era
  rows — the guards WORKING — and EP-30-C3R (resolution unit, C1R's
  precedent, YELLOW at :1925/:1939, three countersign cycles, three
  build cycles) repaired all twelve AT THEIR CAUSES and closed :1947:
  rows 5/7 a coupled pair (one the other's control) repaired as ONE
  cause-entry after the builder obeyed the stop at cost to itself;
  failures back to the standing three, byte-identical at both widths;
  the count reported as consequence, never proof. A unit that breaks
  guards by moving law and leaves them broken has shipped half a pass;
  this pair did not.
  C4 | THE SHARED-MEMORY GRANT AT THE PORT — grant recorded at the
  border, interior honestly unaudited AND STATED
  (T-SHARED-GRANT-NOT-INTERIOR); the wake carve-out carried (ADDENDUM 1
  item 1: recorded-cause wakes are FILLS, unaudited-interior wakes keep
  DECISION; T-CACHE-KILL decides, no seat argues) | XHIGH | order 5 |
  PENDING
  GROUND-SHIFT NOTE, dated 2026-08-21, before any authoring (:1959, the
  mentor's own withdrawal of its pre-ground): SHM-GRANT IS A SHIPPED
  OPERATION — pack rule citing COMM-LAW-SHARE-GRANT, a view folding it
  at comms.py, a granter stamped unconditionally. The zero that read as
  absence was a grep for T-SHARED-GRANT — THIS ROW'S OWN PLANNED
  MARKER, nobody's runtime name — the name-for-thing class at the
  paper's own row. C4's red fact is therefore NOT an absence and must
  be re-derived at authoring. UNDRIVEN DIRECTION, held at the architect
  seat: nothing may verify the granter HOLDS the region it shares —
  C3's undischarged wall in the same words — and if that survives
  driving, the SIXTEENTH CHECK KIND becomes a C4 PRECONDITION rather
  than a C3 leftover, resequencing the kernel unit ahead of order 5.
  Marked as a direction, not a finding; the drive is the mentor's.
  RULED SAME DAY (the :1961 what-question): the tier's missing law
  layer is DELIBERATE IN STRUCTURE — the depth campaign's EP list IS
  the deferral schedule (FS's laws exist because FS's depth ran;
  memory/scheduler/comms lag because theirs is EP-30-C/31/32) — and
  UNRECORDED IN FORM, which is the defect: before the comms close, a
  checkable claim lands that every law cited by a shipped op is created
  OR scheduled at a named unit. No reordering; C4 authors within a
  scheduled-law tier and says so; the kernel-unit sequencing holds at
  the architect seat until the granter-holds drive returns.
  K1 | THE SIXTEENTH CHECK KIND — minted 2026-08-21 at the drive's
  result (:1964, ruled :1965): the engine's check vocabulary gains
  current-parameter-against-prior-record-field; giver-holds (C3's named
  wall) and granter-holds (C4's, SHM-GRANT declaring zero checks —
  attribution sound, AUTHORITY UNASKED) are its acceptance subjects;
  R1-literal carried from C3's close; sight's disposition ruled at its
  authoring (a declared kind with no user carries a scheduled user or
  retires with reason). RED BY CONSTRUCTION — vocabulary mint in the
  engine band. SEQUENCING: C4 authors and builds in parallel; C4's
  close waits on K1's landing if C4 carries an authority row — the
  wall's debtors capped at two | XHIGH | rides beside order 5 | PENDING
  C4W | THE GRANTER-HOLDS WIRING — minted 2026-08-21 on the mentor's
  unowned-debt raise: SHM-GRANT declares `bound_field` granter-holds
  (the check K1 makes expressible and no other unit wires), and C4's R5
  row is repaired AT ITS CAUSE in the same act — the era-row
  consequence discharged at its owner, never left to red unattended.
  [AS-BUILT 2026-09-02, the architect's hand — THE SHAPE THIS ROW
  DESCRIBES IS NOT THE SHAPE THAT EXECUTED, recorded as the divergence
  it is: the row's `bound_field` wiring predates the :2610 stamped-field
  ruling (direction B) and the K2W falsification that showed
  `bound_field`'s separation to be the value-domain coincidence class.
  As executed, C4W makes `_dispatch_check` resolve a check over a
  `stamp_actor` field from the ACTING ACTOR, never a parameter — the
  engine's fact over the caller's claim — minting no kind, the granter
  forgeability closed at the seam instead of wired as a per-op check.
  Authored :2614, countersigned YELLOW :2616 (the seam every check
  passes), dispatched; the A4 close-read is OWED at the architect seat
  (:2626) and the unit is building as at this writing.]
  The per-operation gap this closes is the sight condition at the op
  grain: A CAPABILITY WITH NO SCHEDULED USER, now scheduled HERE.
  REMIT EXTENDED 2026-08-22 at the cardinality ruling: SHM-GRANT's
  grantee-establishment question (every grantee names an established
  entity — the question C4's builder stopped on, unaskable without a
  quantifier) is ALSO wired here, with `every_member` — named by its
  permanent name, not as "the kind K2 mints", per the :2282-raised
  moving-reference repair: a schedule row a predicate reads carries the
  NAME, because a description resolves only while someone remembers
  what K2 minted. ONE OP, ONE WIRING UNIT, ONE ACT. Depends: C4 CLOSED, K1 CLOSED, AND K2 CLOSED,
  strictly | tier at countersign | after order 5 | PENDING
  K2 | THE QUANTIFIED KIND — minted 2026-08-22 on the C4 stop (:1989,
  ruled :1991): the check vocabulary cannot ask ANYTHING of a
  many-valued parameter — no arm iterates one, require_prior's any()
  quantifies over records not values, and the pack holds exactly two
  many-valued params (COMMS-OPEN endpoints, SHM-GRANT grantees). K2
  mints the quantifier: iterate a parameter's values, ask a
  member-question of each, in K1's discipline whole — minimality gate
  against the arms, scratch-proof of expressibility, NO wiring of ops
  owned elsewhere (grantees are C4W's; endpoints have NO WANTING LAW
  YET and that wiring rides the C6 law-schedule settlement, recorded so
  it cannot dangle silently). RED BY CONSTRUCTION — engine-band
  vocabulary mint. OWNER GATE per design/28 §5, stated at the row so no
  reading can miss it again: A CHECK KIND IS AN ENGINE AMENDMENT —
  design-doc change PLUS the owner's recorded word, never a quiet
  addition; every existing kind carries its gated bracket and K2's
  founding move proceeds ONLY on the owner's answer, raised before
  authoring. GATE ANSWERED :2039, the fifth answering, CONDITIONAL —
  "go for now" WITH THE REBUILDABILITY RIDER (design/28 §5's bracket):
  the whole vocabulary stays re-derivable from the four, nothing
  hardens against the owner's flagged re-cut, and K2's authoring binds
  to that rider. THE OWNER'S RETHINK IS A SCHEDULED INTENT, NOT A WISH:
  its natural window is at or after this campaign's close, and the
  close docket carries it. Depends: K1 CLOSED (the band serialises) |
  XHIGH | after K1 | PENDING
  AS-BUILT 2026-08-26, the architect's hand: CLOSED :2251 at the mentor,
  against the plan's own TWELVE named rows, all present at their literal
  paths. The deciding check carried a control that could fail: K2's rows
  were driven 08-22 and the tree moved since, so the close proved its
  subjects unmoved by git diff — with the same command shown returning
  content on a moved file before its empty answer was believed. R4's
  strongest form: the two empty answers are THE LAW'S and not the
  engine's. One disclosed defect at the evidence layer, not reopening:
  A3 and A4 are one file at two names (content lawful, both rows
  genuinely satisfied) — and a presence sweep over named paths CANNOT
  TELL TWELVE ARTIFACTS FROM ELEVEN AND A COPY; :2103 at the evidence
  layer, a path is a position, close-ledger item 49's sixth data point.
  K2R's dependency is MET at this close.
  C4R | THE ERA ROWS C4 FALSIFIES — minted 2026-08-22 at the paper, NOT
  inside C4, because a repair unit invented inside the plan that causes
  the reds is the plan grading its own collateral (the mentor's refusal,
  adopted as the reason). C3R's shape verbatim: the population is an
  ARTIFACT from C4's close (the delta set, both widths, anchored
  extraction), each row repaired AT ITS CAUSE never by sweep, standing
  reds untouched, the count a consequence and never the proof. The four
  rows the region half alone is expected to falsify (test_comms,
  test_ep27b twice, test_phaseb_migrated — all outside C4's fence) are
  the EXPECTED population; the artifact decides the actual one.
  Depends: C4 CLOSED | tier at countersign | after C4 | PENDING
  AS-BUILT 2026-08-26, the architect's hand, from the record: the
  expected population HELD through a proven-complete run — the four
  errors are exactly the four predicted rows (:2110 claim 5) and the
  repair took them four to zero with the thirteen standing failures
  IDENTICAL BY ID, no sweep cap (:2125). Countersigned :2099 (YELLOW at
  signature over authored GREEN), released live at :2111 (:2102 voided
  by a verb-reach, re-filed at the author's hand), DISPATCHED :2113.
  A4's two cross-unit rows, briefly excluded by a manager brief, RULED
  C4R's own at :2128 — the brief was wrong against the countersigned §3
  and the builder's refusal to choose between masters was the correct
  act; builder RESUMED :2130 to land both rows and the rename. BUILT
  AND REPORTED, NOT CLOSED, as at this writing.
  AS-BUILT 2026-08-26, second entry, same turn as the close reached this
  seat: CLOSED :2175 at the mentor's hand, every figure re-driven there
  rather than read from the report — seventeen to eleven with GONE
  exactly C4R's six by ID and NEW empty, errors zero, marker confirmed
  before any figure with a coined-marker control returning zero. THE
  FIRST CLOSE IN THIS CAMPAIGN WHOSE EVIDENCE COMES FROM A RUN PROVEN TO
  HAVE COMPLETED — an artifact the estate could not produce on the
  morning of 08-25. The YELLOW tier's loosening hazard checked
  structurally at the close: laws leave the standing set only by naming
  a curer. RAISE-2 (the probe writing outside every fence) explicitly
  NOT discharged by this close; it stays booked at the manager,
  recurring.
  K1R | THE ERA ROWS K1 FALSIFIED — minted 2026-08-25 from the ruled
  substance at :2063: SIX era pins red outside K1's §5 fence (test_ep29
  four, test_ep30_c3 two, every one reading 29 != 28 EXPECTED A MINOR
  MOVE), falsified by K1's founding move AND BY NOTHING ELSE — the law
  move working, the third instance of the pattern, C1R and C3R the
  precedent. C3R's shape verbatim: population from the close's delta
  artifact, each row repaired AT ITS CAUSE never by sweep, standing
  reds untouched, count as consequence never proof. Depends: K1 CLOSED
  (met) | tier at countersign | after K1 | PENDING
  AS-BUILT 2026-08-26 (:2177): population TAKEN from C4R's close arm — a
  closed taking from a closed unit, C4R's own §1 principle satisfied by
  C4R itself. The K1R/K2R candidate set is EIGHT, not the minted six
  plus extras: three of the arm's eleven reds are MAINT-2's, proven at
  comparison sites and excluded. Per-row attribution is each unit's own
  first acceptance row, driven at the comparison site, never by class
  name — and a width-comparison found there is MAINT-2's and a STOP.
  K2R | THE INSTRUMENT THAT CANNOT SEE A SCHEDULED USER — minted
  2026-08-25 from the ruled substance at :2088 claim 4, :2022's FIFTH
  COSTUME: K1's A6 row reds because every_member has no PACK user,
  while THE ROW'S OWN CLAIM admits a named scheduled user and this
  kind has TWO (C4W and C6) — the claim is satisfied and the
  instrument cannot see it, because kinds_with_users reads the pack
  only and its one exception is A HARDCODED SINGLETON, DELIBERATELY
  NOT A PREDICATE. A row right about its population and wrong about
  its claim. K2R repairs the INSTRUMENT: the scheduled-user branch
  becomes a PREDICATE over declared schedule data whose content comes
  from THIS plan list and nowhere else (C4's A6 discipline — a rider
  restating its own schedule is a claim checking its own copy).
  Depends: K2 CLOSED | tier at countersign | after K2 | PENDING
  REMIT EXTENDED 2026-08-26 at the countersign, accepting the :2304
  ruling's forced ground: the two jointly-falsified population pins at
  test_ep29.py:10610 and :11419 are K2R's — A RE-PIN IS MADE ONCE, TO
  THE POPULATION AFTER THE LAST MOVE, AND THE LAST MOVE OWNS A
  JOINTLY-FALSIFIED PIN because every earlier repair would be stale on
  arrival (:10610's own docstring ruled it before either unit existed).
  The extension travelled DECLARED in the object's §1, refusable at the
  signature, and was accepted there; the partition scheme's gap —
  single-cause attribution meeting a dual-cause row — is closed by the
  last-mover rule for every future arc.
  MAINT-2 | THE PINS THAT RED ON REPOSITORY GROWTH — minted 2026-08-26
  from the mentor's raise at :2122. THIRTY seven-character hash literals
  across TEN test files (28z eleven, 28n four with two on one line at
  test_ep28n.py:951, 28j three, 28f/28h/28i/28k/29 two each, 28n2/28p
  one each — population RE-DRIVEN AT THE ARCHITECT'S HAND AT THE MINT,
  tool-counted, matching :2122's corrected figure exactly), every one a
  guard holding a stored seven-character literal against fresh %h
  output, and git now abbreviates to EIGHT: core.abbrev is unset, %h
  width follows repository size, and this repository crossed the
  threshold (mechanism spot-checked at the mint: rev-parse --short
  208a1ee returns 208a1ee3 — SAME COMMIT, LONGER NAME). One mechanism,
  one class, UNIFORM per :2118. The defect is not the reds: it is that
  a pin reddening because the repository GREW is indistinguishable from
  one reddening because its subject MOVED, in the guard layer every
  other verification rests on, on a CLOCK that fires with growth — it
  is MAINT and not an R-unit because NO LAW MOVE causes these reds; the
  environment does. THE REMIT: every exposure repaired so the pin binds
  IDENTITY independently of abbreviation width — it must still red when
  its subject moves and must never red when only the width grows. A
  GUARD NEEDING TO BE LOOSENED TO PASS IS THE STOP CONDITION: this is
  an assertion-repair unit and C4R's tier derivation (the author's own
  disclosure applied against it) is expected at the countersign.
  Depends: C4R CLOSED — two exposures live at test_ep29.py:489 and :494
  inside C4R's fence; THE MINT IS UNBLOCKED, THE DISPATCH IS NOT
  (:2122 claim 4 adopted) | tier at countersign | after C4R | PENDING
  AS-BUILT 2026-08-26, the architect's hand, same day as the mint:
  authored and COUNTERSIGNED YELLOW at :2132 (the :1925 derivation, the
  author's reading and the signer's agreeing) after ONE withhold cycle
  on a one-character §1 defect — a space inside the unit name that
  reversed the dispatch precondition's parse (:2126, repaired wider than
  the finding at :2129 by naming both units). AUTHORED re-filed :2137
  after the resubmission's verb voided it. §3 binds 23089c85 at 3,566
  under the corpus-driven slice rule (EP-SHAPE, fourth substitute-back
  clause — a false calibration at the signing seat was refused by the
  author with a driven table, :2136/:2140). Dispatch remains blocked on
  C4R CLOSED, not reported.
  AS-BUILT 2026-08-26, second entry: THE DEPENDENCY IS MET — C4R CLOSED
  :2175 — and the dispatch is UNBLOCKED at the manager's hand, with the
  plan's own §5 re-take clause now live: the two test_ep29.py literals
  are re-driven at dispatch, never inherited from the authoring.
  AS-BUILT 2026-08-26, third entry (:2177): THREE of the close arm's
  eleven reds are PROVEN MAINT-2's AT THEIR COMPARISON SITES — 28f, 28j,
  and test_ep29:601 (%h output against a seven-char pin) — so the unit
  dispatches with three named reds to clear, not a class to hunt; one of
  its two test_ep29 re-takes is discharged at that taking. THE BOUNDARY
  THE THREE UNITS NOW SHARE: any row K1R or K2R's A1 finds to be a
  width-comparison BELONGS HERE and is their STOP, as their attribution
  rows state — and MAINT-2's A1 caught its own author at test_ep29:588
  and :593, where the same constant is a git INPUT and correct.
  AS-BUILT 2026-08-26, closing entry: CLOSED :2247 at the mentor's hand
  against the plan's own rows, never the report. 11→8, GONE exactly its
  three, NEW empty, both arms inside its own fence — the first unit in
  the estate able to. A1's final split: 30 swept, 26 INPUT, 4 COMPARED,
  and the FOURTH compared site is the close's real yield: test_ep28j:811
  was COMPARED and GREEN — a startswith over seven characters that never
  asserted identity and would have stayed wrong forever BECAUSE nothing
  red. Caught only by A1's classify-by-what-the-line-DOES discipline;
  filed as the two-answers-look-alike family's terminal member. One
  disclosed defect (:2249, an annotation under-describing its own
  figure) does not reopen the unit. The clock defect is DEAD.
  C5 | THE SHADOW MATURES AND RETIRES — EP-22's sock_diag window becomes
  the subsystem's shadow, then retires per the ledger law: shadow-diff ∅
  AND divergence-halt proven, both directions | XHIGH | order 6 | BUILT,
  MATURATION PROVEN — RETIREMENT DEFERRED BY RULING (:2646)
  [AS-BUILT 2026-09-02, the architect's hand, from the board and the
  builder's close: authored by the mentor and countersigned :2624 (tier
  confirmed from this row), built same day. Maturation LANDED whole —
  sustained ∅ 24/24 under a named churn battery (48 opened / 42 closed /
  90 state-changes, not a quiet box), divergence-halt both directions,
  all three red worlds biting. THE RETIREMENT DID NOT HAPPEN, and the
  reason is a finding about what connections ARE: the connection op
  surface is ['OBSERVE-CONNECTION'] — observe-only — so no
  governed-authoritative view exists to retire INTO, and the gate
  refuses the void mechanically (a swap into a void is a naked swap by
  another door). RULED :2646: matured, retirement DEFERRED — the ledger
  row stays open honestly against a target that may never exist;
  "permanently observe-only by design" was refused as a forever-claim
  nothing forces. The files-vs-connection halt asymmetry (files halt
  appends CUSTODY-HALT citing a founding rule because the mount serves;
  the connection halt raises StaleShadow and appends nothing because
  nothing authoritative is served) is CORRECT-BY-CONSTRUCTION — no
  future unit "repairs" it into a founding bump.]
  C6 | THE GROUP BATTERY AND CLOSE — T-SYSCALL-SEMANTIC comms rows ·
  T-CUSTODY-IS-DERIVED (channel state) · T-CUSTODY-MATRIX (comms) · the
  probe sets · the round-trip; both-directions mapping re-checked at this
  close (every §6 obligation of design/39 traces to a unit, every unit
  traces to remit text); AND THE COMMS LAW SCHEDULE SETTLES HERE, ruled
  2026-08-21 completing :1963's rider: any comms-family law still
  cited-and-uncreated when C6 opens is either CREATED at C6 through the
  founding door or RE-SCHEDULED to a named successor in this list — the
  dangling-citation claim (every cited law created or scheduled at a
  named unit) holds pack-wide at the arc's close ON THIS ROW'S
  AUTHORITY, and the schedule data any rider row reads takes its
  content from THIS plan list and nowhere else. THE COMMS-OPEN
  ENDPOINTS WIRING THAT RIDES THIS SETTLEMENT (K2's row) WIRES WITH
  `every_member`, named here by its permanent name so the schedule
  carries the kind and never a description of it | XHIGH | order 7 |
  BUILT — BATTERY AND MAPPING DONE; COMMS CREATE-BRANCH AT THE OWNER
  GATE (:2647)
  [AS-BUILT 2026-09-02, the architect's hand: authored by the mentor and
  countersigned :2628, built same day. The group battery is GREEN AS A
  GROUP (7 comms modules, 128 tests, one process); the design/39 §6
  mapping holds BOTH directions as a set equality (4 obligations→units,
  7 units→remit). THE SETTLEMENT: of eleven cited-and-uncreated laws
  driven over the live pack, NINE re-scheduled within this row's
  authority — MEM-LAW-ALLOC/BUDGET/EVICT/PROTECT owed by EP-31,
  SCHED-LAW-ADMIT/HALT/KILL-CHAIN/ORDER/PRIORITY owed by EP-32 (the
  schedule data of record; the rows below carry it). The comms family
  has no successor after this row, so its laws are CREATES at the owner
  gate: scope RULED :2647 — "cited" means the settled instrument's
  law_cited surface, so TWO go to the owner, COMM-LAW-CONTRACT
  (load-bearing today: live refusals cite it) and COMM-LAW-QUEUE (cited
  only in success decisions of check-less COMMS-SEND/RECV; its create
  precedes its enforcement wiring, stated plainly). Create pending the
  owner's word as at this writing. The old two-count question is
  SETTLED BY DRIVE: 12 distinct check-cites; the "13" was EP-25's
  historical PRE_EXISTING_UNSEEDED set, two members since created.
  Founding pack byte-identical through the whole build — nothing
  minted, R3 proved the naked create refuses.]
  STANDING ACROSS ALL SEVEN, not a unit: the POSIX-ordering stop-and-raise
  (any case where recorded intake order is OBSERVABLE against POSIX's
  guarantee level is a STOP, design/21 the ground); and the packet-logger
  wrong reference stands armed — record decisions, sample flow.
  MAPPING CHECK RUN AT ENUMERATION, both directions as sets: design/39
  §6's four obligations → C1 (crossings, user channel, invariant) and
  C0/C1 (row vocabulary); remit text → C0 substrate/durability, C1
  channels, C2 messages, C3 custody, C4 shared medium, C5 shadow, C6
  battery. No behavior unmapped, no unit tracing to nothing.]**
- **EP-31 — M6: memory.** L, xhigh + MAX speed item. Depends: EP-30. The
  acid test in production; design/22 is the stage brief (minor faults are
  cache fills appending nothing; evictions freeze their evidence); the
  proof is T-CACHE-KILL extended to a swap cycle.
  [SCHEDULE DATA + AS-BUILT 2026-09-02, the architect's hand: EP-31 OWES
  FOUR LAWS by the C6 settlement's re-schedule — MEM-LAW-ALLOC,
  MEM-LAW-BUDGET, MEM-LAW-EVICT, MEM-LAW-PROTECT. The MEM-LAW-BUDGET
  founding gate is ALREADY GRANTED by the owner ("2 yes", :2642, on the
  decision item at planning/exec/EP-31-MEASURE-GATE-DECISION.md). The
  measurement question is RULED (:2633): the MS-HEIGHT measure already
  exists as the `ceiling` kind (through the §5 gate historically, its
  docstring cites it) — EP-31 COMPLETES ceiling, mints no MEASURE
  operator; the §A51 summed-value condition resolves inside
  MEM-LAW-BUDGET's wording if the wording can carry it, else a new-kind
  question returns to the owner separately. design/41 §8.2's "today no
  kind measures anything" was false at its own writing (ceiling landed
  2026-07-15, the doc 2026-08-22) — CONFLICT filed, standing
  unharmonized by the owner's non-answer. Authoring at the mentor as at
  this writing.]
- **EP-32 — M7: scheduling (last, and strictest).** L, xhigh + MAX speed
  item. Depends: EP-31. The final subsystem; T-REALTIME-BOUND is the gate
  (the ruled carve-out: for SCHED_FIFO/RR/DEADLINE the timing bound is the
  semantics). Scheduling's /proc slices complete the port.
  [SCHEDULE DATA 2026-09-02, the architect's hand: EP-32 OWES FIVE LAWS
  by the C6 settlement's re-schedule — SCHED-LAW-ADMIT, SCHED-LAW-HALT,
  SCHED-LAW-KILL-CHAIN, SCHED-LAW-ORDER, SCHED-LAW-PRIORITY. Their
  founding creates take the design/28 §5 owner gate when EP-32 authors
  them, same class as EP-31's. design/41 §8.2's LENGTH axis (time
  bounds) is EP-32's measurement question, deliberately NOT settled by
  the :2633 ceiling ruling — it arrives as its own address, not an
  emergency, per the forecast's own intent.]
  [AS-BUILT 2026-09-02, the architect's hand: EP-32 CLOSED :2681 — the
  scheduler governed at the metal, records-per-dispatch falling 4.0e-4 to
  4.0e-7, core byte-identical after the MAX pass, no SCHED-LAW minted (all
  five held owner-gates). T-REALTIME-BOUND MEASURED on the validation
  kernel (~1 us per governed RT decision recording nothing, ~86x/866x
  headroom vs 100 us/1 ms) and THE ASSUME FLIPPED ON THE OWNER'S WORD
  ("flip yes", board :2685 — first written :2683, a predicted coordinate, corrected by read-back) — the last assume; the port is complete in
  substance. Caps carried honestly: A7's guest conformance leg not
  independently re-run by mgr (invocation artifact, reproducible); the
  04-process-scheduling conformance group inactive under tools/ (MAINT
  item at mgr's gates).]
  Wrong reference: the clock as scheduler — wall-clock alarms driving
  dispatch (the standing 15.1 ban: clock-as-sensor, ticks as INPUT, the
  schedule a recorded rule).
- **EP-33 — Campaign review.** L, xhigh (+ultracode per precedent).
  Depends: all. Two-pass + second-reading; the full seven-set probe ledger
  plus this campaign's additions re-run; the custody authorization matrix
  at OS scale (the four columns over real file/device/comms/memory/sched
  ops); T-TOTAL-ROUNDTRIP-3; the openness grant verified untouched; and the
  paper graded against what held (the paper standard's afterlife clause).

## 7. The deferred-to-live ledger (every flip, retirement, and supersession — each a documented test flip; strictly-stronger obligations stated)

1. **The `fingerprint` check kind ENTERS the engine vocabulary** (EP-23).
   Engine amendment law observed: design/28 §5 gains the row at the landing
   EP's verdict (the owner gate = the design/35 adoption ruling, 2026-07-25).
   Its six tests ship in the same EP; an op definition naming the kind
   before the EP lands refuses at definition time (unchanged law).
2. **occurrence_time becomes load-bearing for decision- and law-family
   records** (EP-26). Strictly-stronger obligation (the EP-17 lesson,
   verbatim rule): the old ledger cannot contain cases in the d<r dimension
   it could not express — so the acceptance ledger is EXTENDED into that
   dimension (the §8 two-times battery) BEFORE any behaviour depends on it,
   and the degenerate case d=r must behave byte-identically to today: the
   entire existing suite is the old-ledger side and re-runs green unchanged.
3. **Per-subsystem shadow views retire only on proof** (EP-25, then each
   Arc C EP). The shadow phase's Linux-authoritative view for a subsystem
   retires only after sustained shadow-diff ∅ AND divergence-halt proven in
   both failure directions (a divergence that fails to halt; a false halt
   that blocks a lawful assume). Never a naked swap.
4. **planning/11's residence assumption is SUPERSEDED** (EP-22). The stage
   spec predates the built engine and says "lift the pwc/cgl spine"; the
   live canon controls: the spine is the campaign-1/2 kernel, and fortress
   purity independently bars the occupant material. Documented here, not
   harmonized silently — planning/11 is FROZEN class; this paper is the
   controlling citation.
5. **The stale bridge runner retires or rebuilds** (EP-25). The campaign-1
   findings file homes src/bridge/run_fuse_files.py to the round that takes
   up the bridge; that round is EP-25.
6. **R20-1: the protection boot-fallback retires** (EP-20B). Directed by the
   owner at the campaign-2 close; the fence names protection.py.
7. **Explicitly NOT flipped this campaign** (guard against helpful drift):
   the openness grant (scaffolding, untouched; narrowing is the pilot's
   recorded act, not DEPTH's); the caller-asserted identity cap (R20-2,
   rides to campaign 4 as the documented boundary); S5 multi-writer (one
   store writer; ordering fields carried); the SOP and OWNER-TUNNEL deferred
   markers (honest via enforced_by, unchanged); V3's re-home (parked to C4
   by name); V6's query-space pointer (rides to the accounts-home-space
   round); the narrowing-time subtleties (bare CREATE-INFO info-kind,
   unfounded-space records — ride to the first narrowing); R20-3/-4/-5 at
   their named homes. The remaining campaign-1 cleanup items ride under the
   standing adjacency rule — builders fix where adjacent, the mentor tracks
   adjacency at each verdict.
8. **Already standing, no work minted** (the handover's own preferred
   outcome): wall primitive 3 (attenuation) lives at the gate chokepoint
   (E1, DIGEST-C2 theorem 12); primitive 7 (gated egress) is an ordinary
   granted emit act (E2). One-line proofs, not new machinery.

## 8. The acceptance battery (named before any code; battery-level names — each EP file lowers them to runnable tests)

T-RECORD-UPSTREAM (effect never precedes its durable decision; an
interrupted crossing heals record→effect on restart) · T-CUSTODY-IS-DERIVED
(kill derived custody state, replay, identical service — the crux test) ·
T-SYSCALL-SEMANTIC (the design/10 rows, three checks each, dual-target) ·
T-UNMODIFIED-PROGRAM (cat/ls/git on the mount, then on the module) ·
T-REALTIME-BOUND (the carve-out, at EP-32) · T-RATE-GOVERNANCE (record rate
tracks decisions, measured, per subsystem) · T-FOLD-AT-RATE (authority-fold
cost measured; cached answers coherent-or-refuse) · T-NO-STORED-TABLE (the
structure guard: no permission table, no stored complement, anywhere on any
path) · T-CONFORMANCE-BASELINE-PINNED (stock baselines are pinned artifacts)
· T-SHADOW-DIFF (∅ under load) · T-DIVERGENCE-HALT (both directions) ·
T-KERNEL-RESIDENCE-ENUMERATED (the K5 audit) · T-CUSTODY-MATRIX (the four
authority columns over custody ops; columns proven able to fail) ·
T-UID-IS-EVIDENCE (uid in provenance; actor derived; no identity table) ·
T-OPENNESS-UNTOUCHED (the grant unchanged outside test worlds) ·
T-TWO-TIMES-ACCEPT (both halves of the owner's worked example) ·
T-OVERTURN-SWEEP (late law → appended overturns → views reconcile → replay
identical) · T-OVERTURN-REACH (outside-scope stands; inside reached;
transitive flip via recomputation; refusal→re-ask, never a fabricated
effect; anchor-guarded overturn refuses) · T-FP-HOLDS / T-FP-STALE /
T-FP-ORTHOGONAL-REFUSAL / T-FP-ABA / T-FP-REPLAY / T-FP-CANONICAL
(design/34 §7 verbatim) · T-CROSSING-REPLAY (in-flight crossings
reconstruct; the answerer never re-runs) · T-CORRELATION-DERIVED (binding is
the store's; an in-band token alone binds nothing) · T-CONTEXT-PINNED (the
four pins recorded on every external call) · T-VAULT-CONSUMER (the system
presents a vault credential; no read path exercised; the record proves use)
· T-SESSION-PUSH (the 9:02 change reaches the 9:00 session before its 9:05
submit, in test time) · T-LANE-PRIORITY (law-family outruns ordinary
traffic) · T-PUSH-APPENDS-NOTHING (kill queues, replay, identical) ·
T-BACKPRESSURE-RESERVE (under flood, the emergency budget still delivers) ·
T-CACHE-KILL-SWAP (design/22's proof extended through a swap cycle) ·
T-TOTAL-ROUNDTRIP-3 (everything derived killed, custody included; replay
identical).

### 8b. The invariant → tests → EP map (GATE 4)

| Invariant | Battery rows | EPs |
|---|---|---|
| K1 | T-RECORD-UPSTREAM · T-CUSTODY-IS-DERIVED | 25, 28–32 |
| K2 | T-SYSCALL-SEMANTIC · T-UNMODIFIED-PROGRAM · T-REALTIME-BOUND | 24 (instrument), 25, 28–32 |
| K3 | T-RATE-GOVERNANCE · T-FOLD-AT-RATE · T-NO-STORED-TABLE | 22 (first evidence), 25, 28–32 (max items) |
| K4 | T-CONFORMANCE-BASELINE-PINNED · T-SHADOW-DIFF · T-DIVERGENCE-HALT | 24, 22, 25, 28–32 |
| K5 | T-KERNEL-RESIDENCE-ENUMERATED | 28–32 |
| K6 | T-CUSTODY-MATRIX · T-UID-IS-EVIDENCE · T-OPENNESS-UNTOUCHED | 25, 28–32, 33 |
| K7 | T-TWO-TIMES-ACCEPT · T-OVERTURN-SWEEP · T-OVERTURN-REACH | 26 |
| K8 | T-CROSSING-REPLAY · T-CORRELATION-DERIVED · T-CONTEXT-PINNED · T-VAULT-CONSUMER | 23 |
| K9 | T-FP-HOLDS/-STALE/-ORTHOGONAL-REFUSAL/-ABA/-REPLAY/-CANONICAL | 23 |
| K10 | T-SESSION-PUSH · T-LANE-PRIORITY · T-PUSH-APPENDS-NOTHING · T-BACKPRESSURE-RESERVE | 26, 27 |
| K11 | T-TOTAL-ROUNDTRIP-3 · the full C1/C2 probe ledger re-run · T-CACHE-KILL-SWAP | 26 onward; final at 33 |

Every battery row above traces to exactly one invariant; every invariant
carries at least one row; EP files may add tests but never subtract these.

## 9. Honest caps and non-goals (named, not hidden)

- **Performance is the campaign's whole risk, and it is two risks.** OS-rate
  recording and the per-act authority fold are both unmeasured today. The
  containment: first numbers taken cheaply in observe mode (EP-22), each
  subsystem's speed tension worked at MAX tier before its authority flip is
  accepted (EP-28/31/32), staged validation pinned-kernel-then-Ubuntu, and
  acceleration only ever as measured calibration under coherent-or-refuse.
  No number in this paper is a measurement; the ones the estate cites
  (design/22 §6) are structural illustrations, Estimate — Medium.
- **Every custody guarantee carries the caller-asserted cap** until
  campaign 4: cannot-do-lawfully and cannot-do-quietly, never
  cannot-do-at-all. Deciding timestamps and observer-asserted
  occurrence times carry the same cap (design/35 §6: the seal bounds a
  claimed deciding time in one direction — it cannot predate the world its
  own pack hash pins; the other direction closes with signing).
- **Session read-sets are declared, not derived** — necessarily, because
  reads append nothing by design (I9); the push's knowledge of exposure is
  therefore as good as the declaration, and the seal is what keeps
  under-declaration a convenience problem, never a legitimacy problem.
- **The sweep reconciles state, not consumptions** (§4b.6): what was read or
  delivered under a since-overturned act is exposure, surfaced as a view;
  the remedy is judgment, deontically governed, not machinery.
- **Observation coverage is a calibration with an evidence step** (the
  coverage audit), never an assumption; interior userland activity (shared-
  memory interiors, futex words) is permanently and honestly out of audit
  reach — the standing boundary, not a gap.
- **Kernel-context engineering (stance 3→4) is real risk, faced last and
  smallest** — one proven subsystem moved down one layer behind an unchanged
  interface; the per-subsystem fallback to stock stays local (Route B per
  subsystem is a contained retreat, not a plan failure).
- **Capacity horizons stay the owner's calibration** (design/23 §4): lever A
  mechanics enter on measured volume, lever B stays owner-authority at a
  long horizon, lever C is compliance's lane; nothing here rules a number.
- **Non-goals, restated once:** no narrowing of the open world; no
  cryptographic closure (C4); no description of foreign governance (C5); no
  federation, no S5 sequencer (C6); no GS-13 (C4); no driver-class breadth
  (D8); no dates — gates, not a schedule.
- **What this paper excludes:** kernel source was not read (clean-room law:
  behaviour and interfaces only; every Linux facility named is trained
  knowledge, Estimate — High, and dates); src/tests/tools were not read
  (the author's channels are the record, the digests, machine evidence);
  Arc C sizes/tiers re-price at each gate (Estimate — Medium); the exact
  FUSE semantics a real program may depend on are settled by the harness's
  evidence, not by this paper's prose.

## 10. The pressure-test record (GATE 2 — two passes, findings folded visibly)

**Pass one — the design attacked as drafted.** Six findings, all folded:

1. Gating everything would die at rate; gating nothing would ungoverned the
   ports. Folded: the design/10 class map IS the gating contract (K3) —
   DECISION/LAW cross the gate, CACHE consults views, STREAM samples.
2. The FUSE caller's identity had no stated resolution — builders would have
   invented a user table (the stored-status template). Folded: K6's
   invoker/actor split; uid as recorded evidence; T-UID-IS-EVIDENCE.
3. The two-times machinery risked reading as decoration riding a custody
   campaign. Found instead: the observe world is ALREADY a two-times world —
   every M1 observation arrives after its occurrence — so EP-26 has a live
   consumer the day it lands. Folded into K7 and EP-26.
4. The conformance instrument, if authored inside the custody EP it judges,
   repeats the maker-reviews-own-object shape. Folded: EP-24 separated.
5. The write-coalescing policy was unpriced. Folded: a recorded policy with
   a PROPOSED default, owner-calibrated (§11 item 5).
6. **The pass's best catch:** the overturn op's effect can reach root
   authority (overturning a recorded handover could orphan or move root) —
   the campaign's one wire-at-birth case, nearly missed. Folded: §4b.7;
   the anchor guard is consulted in the overturn's own definition.

**Pass two — the semantics the first pass assumed without stating.** Seven
findings, all folded:

1. "Deciding time" for a machine-speed syscall was undefined — a builder
   could have adjudicated every synchronous act counterfactually (rate
   disaster) or none (law gap). Folded: d=r by construction for S-plane
   synchronous acts (K7); the regime binds only where deciding leaves the
   store's synchronous path.
2. **The pass's worst finding:** an overturned file write looked like
   retroactive content rewriting — which would falsify past reads and break
   the ports promise. Folded: overturns act FORWARD from their record_time;
   asOf before the overturn still shows the act's effect; the surfaced
   change is ABI-ordinary (K2 note, §4b.3). Order untouched, validity
   changed — the two frames held only once this was stated.
3. Whether a late-arriving refusal can be "overturned into" a permit was
   unstated; fabricating the effect would be the forbidden lie. Folded:
   §4b.4 — re-ask view, never a fabricated effect (raised as a default,
   §11 item 4).
4. The law/authority split at acceptance was implicit — implement either
   uniformly and the model breaks (a revoked chain must refuse regardless
   of deciding time; an old-law act must stand regardless of new law).
   Folded: K7 states the split; it is design/34 §2's division generalized.
5. The session read-set's epistemic status (declared vs derived) was
   unexamined; derived is IMPOSSIBLE because reads append nothing (I9) —
   so declaration is a consequence of standing law, and the seal is the
   backstop that makes it safe. Folded: K10 and §9.
6. The sweep's determinism under replay needed an order rule, not just a
   fixed point. Folded: candidates processed in record order, rounds until
   empty, monotone decreasing — terminates, replay-identical (§4b.5).
7. Multiple observation adapters looked like multi-writer through a side
   reading; S5 must not be built early. Folded: adapters are submitters
   through the one gate; one store writer stands (§3, EP-22).

**Left as owner judgment (not folded):** the §11 items — each one word.

## 11. The ruling list (GATE 3 — each item self-contained; one word answers)

1. **The paper itself.** This document becomes campaign 3's definitive:
   direction and build for Arcs A–B, direction for Arc C with EP files
   authored at each green gate. YES = the sitting mentor's four-gate review
   proceeds and, on its pass, EP-20B dispatches. NO = name the section and
   this seat re-derives it.
   **RULED YES (owner, 2026-07-26): this paper is campaign 3's definitive.**
2. **Campaign start on the fix-first sequence.** EP-20B (the R20-1
   retirement you already directed to this window) runs first; the campaign
   opens when it is DONE and reviewed. YES = launch in that order. NO =
   reorder or hold.
   **RULED YES (owner, 2026-07-26): EP-20B first; the campaign opens when it
   is done and reviewed.**
3. **The sweep's boundary.** When late law overturns an act whose effects
   were already consumed (a program read the bytes; an answer was
   delivered), the machine reconciles the STATE and surfaces WHO consumed
   under the voided act as a view — the remedy for consumption stays human
   judgment under the deontic vocabulary. YES = that split stands. NO = a
   stronger mechanical remedy is wanted and this seat derives its cost.
   **RULED YES (owner, 2026-07-26): the sweep reconciles state; consumption
   surfaces as the exposure view; the remedy is human judgment.** This is one
   of the two words EP-26 preconditions on — that precondition is now met.
4. **The refusal direction.** A late-arriving PERMISSIVE law never converts
   a past refusal into a done act (nothing happened to overturn); the
   affected case surfaces on a re-ask view and the actor re-submits under
   current law. YES = re-ask stands. NO = direct the alternative.
   **RULED YES (owner, 2026-07-26): re-ask stands; no fabricated effects.**
   This is the second word EP-26 preconditions on — that precondition is now
   met, and §4b.4's PROPOSED default becomes ruled law.
5. **A calibration named now, valued later:** the write-coalescing policy
   (how many small writes fold into one recorded decision, citing the
   policy). It arrives at EP-25 with a proposed default and your word sets
   the value then — flagged now so it never lands as a silent default.
6. **A checkpoint named now, worded later:** EP-28 is the kernel-entry
   dispatch (stance 3→4). The route is long ruled; the STEP remains your
   word at that gate. Nothing to answer today.

---

*Register note: this paper is written under REPO-WRITING-GUIDE; its checks
are readings of recorded law and prior proofs; its tests are coverage,
named before code. Labels: the invariants and the §4b specification are
SOURCE-DERIVED from the cited rulings and canon; EP decomposition, sizes,
tiers, and the two §4b policy defaults are PROPOSED with costs stated;
every Linux facility named is trained knowledge (Estimate — High) and
dates.*

---

## ADDENDUM A — the four-gate review's corrections to §4b (2026-07-26, sitting mentor, xhigh)

Appended, not edited into the body, per the paper standard's afterlife rule
(mid-campaign discoveries arrive as a dated addendum). This addendum is law
and is read as part of §4b. EP-26 lowers §4b as corrected here; its own
ADDENDUM 2 carries the same five items in build-facing form.

**The gate verdicts.** GATE 1 (shape) passes: all ten sections of the paper
standard's §1 are present, in order, and honest, with §4b sitting inside the
invariant territory it serves. GATE 2 (pressure-test passes) passes: two
passes ran, each found real findings, each folded them visibly, and the second
pass attacked the semantics the first assumed, which is what the standard
asks. GATE 4 (lowerability) passes: the §8b table traces thirty-four battery
rows to eleven invariants with no orphan in either direction, and the row
names in §8 and §8b reconcile exactly. GATE 3 was closed on 2026-07-26. The
five items below are corrections inside a passing paper, not gate failures.

### A.1 The tie rule binds both doors, and the field it compares needs a stated precision

§4b.1 states the tie rule for the sweep only: candidates are acts X with
d(X) > d(L) strictly, so an act decided at exactly the law's own deciding
moment stands. The strict choice is right and is re-derived here: legitimacy
is created at the deciding moment, the decider of X at that instant could not
have been shown L, and X's seal pins a world that cannot contain L, so
holding X to L would hold a decision to law it demonstrably could not see.

What §4b.1 does not state is the same rule at the ORDINARY door. Its own
closing sentence says acts arriving after r(L) are adjudicated "against the
law as of THEIR deciding time, which now includes L." If the acceptance fold
treats a law with deciding time exactly d as in force at d, then the identical
pair of facts resolves two ways: X stands when it arrives before L and the
sweep passes over it, and X refuses when it arrives after L and meets the
ordinary door. Arrival order would then decide the tie, which is the one thing
the owner's ruling forbids.

**The correction.** The comparison is strict at BOTH doors. The acceptance
step's law-as-of-d fold treats a law-family record whose deciding time equals
d as NOT in force for an act decided at d. §4b.1's rule and the acceptance
rule are one rule, stated once and applied twice.

**The second half, and a CONFLICT marked rather than harmonized.** §4b.1 says
the tie test is a checkable field comparison, so determinism holds. That is
true of the comparison and says nothing about how often the comparison lands
on equal. The field being compared is `occurrence_time`, and design/11 §1.1
specifies it as a supporting field "carried but not load-bearing for
ordering," explicitly noting it "may be vague." §7 item 2 of this paper makes
that same field load-bearing for adjudication. That is a real conflict with a
FROZEN pre-code document and it is marked here rather than smoothed: a strict
inequality over a field whose own specification permits vagueness exempts
every act sharing a law's deciding-time value, and at coarse resolution that
is not a corner case but a whole tick of traffic. design/21 already treats
equal timestamps as the expected case for `record_time` and resolves them with
an injective key; the deciding-time dimension has no such treatment and needs
none, but it does need its precision pinned. **The correction:** EP-26 states
the recorded precision of the deciding-time field for decision- and law-family
records, and its battery covers the equal-value case at that precision.

### A.2 Termination holds, but not for the reason §4b.5 gives

§4b.5 argues the transitive rounds terminate because "exclusions only shrink
the permitted set (grants are positive; the complement is computed), so the
iteration is monotone decreasing over a finite record."

The re-derivation does not support that reason in general. Admission is not
one predicate but the gate's whole check set, and the checks do not all move
in one direction when acts are excluded. A grant check is positive and shrinks
under exclusion. A ceiling check refuses when a limit is already consumed, and
consumption is computed from the record, so excluding acts REDUCES consumption
and can turn a recorded refusal into a counterfactual permit. The admission
predicate is therefore not monotone in the record, and a builder who
implements the loop from §4b.5's stated reason may compute the fixed point in
one pass or stop when the permitted set stops shrinking, neither of which the
guarantee actually supports.

**Termination holds for a different and stronger reason, and this is the one
EP-26 lowers.** The only thing the sweep ever appends is an overturn, and an
overturn is never withdrawn. Refusal-to-permit flips append nothing (§4b.4),
so they cannot remove anything from the overturned set. The overturned set is
therefore monotone non-decreasing inside a candidate set that is finite and
fixed, and the iteration reaches its fixed point in at most one round per
candidate. Two consequences follow and are now stated law:

- **An act once overturned is never un-overturned**, including where a later
  round's larger exclusion set would re-admit it. This is where the ceiling
  class of check surfaces, and the answer is the one already ruled for the
  refusal direction: nothing is appended that would restore an effect's
  standing, and the case is visible on the record as it stands.
- **The candidate set is fixed for the sweep's life.** The overturns the sweep
  appends are themselves decided and recorded by the system in one act, so
  d = r for them and r is later than r(L); §4b.1's own boundary puts them
  outside the sweep's business. The sweep does not chase its own output.

### A.3 A transitive overturn cites its ancestor, not the law

§4b.3 says the overturn cites L, X, and both deciding times. §5's record-kind
table says the overturn cites "the reaching law (or overturned ancestor)."
These differ, and EP-26 lowers §4b.3's narrower form. A round-two overturn is
not reached by L directly; it falls because an act it depended on was
excluded. An overturn of that act citing L as its reason is a citation that
does not carry its refusal, and every refusal citing its rule is P4.

**The correction.** §5's form controls. A direct overturn cites L, the
overturned act, and both deciding times. A transitive overturn cites the
overturned ancestor whose exclusion reached it, the overturned act, and the
ancestor's and the act's deciding times. The chain from any transitive
overturn back to L is then walkable on the record rather than asserted.

### A.4 The anchor guard is a computed test, not a list of three kinds — RAISED, awaiting the owner's word

§4b.7 wires the overturn to the anchor guard and names its scope as three
kinds of target: a handover, a succession, a root grant. The ruling it derives
from is broader. Wire-at-birth (DIGEST-C2 §8, the EP-18 ruling) reads: any op
"whose effect could REMOVE or TRANSFER root authority" wires into the anchor
guard at birth. That is a statement about EFFECT, and §4b.7 has lowered it to
a match on the target's kind.

Two cases sit outside the three named. First, acts that are not anchor acts
but hold anchors up: the creation of an account that a live chain names, or a
mid-chain grant that carries authority downward. Overturning either leaves the
chain below it with nothing above it. Second, and this is the one the
enumeration cannot see at all, the transitive rounds of §4b.5 can end a chain
one hop at a time with no single overturn's target ever being one of the three
kinds. A guard consulted per-overturn on the target's kind reports nothing
wrong at every step of a sweep that ends with authority orphaned.

**The proposed correction, PROPOSED and awaiting the owner's word, cost
stated.** §4b.7's trigger becomes the functional test the anchor law already
carries, computed rather than matched: before the sweep appends, and again on
the sweep's cumulative result, the guard asks whether the post-exclusion
record leaves any chain without a root or moves root, and refuses and routes
to the owner if it does. This is the estate's own standing shape (power is
scope-and-target, never a verb list) applied to the guard's own trigger, and
it is the same correction the power model made to an earlier act-list. **What
a yes does:** the guard refuses more sweeps than the three-kind form would,
each refusal routed to the owner with the chain it would have ended. **What a
no does:** §4b.7 stands as written and the two case classes above are accepted
as reaching the owner only when they happen to target one of the three kinds.
**Cost if the proposal is wrong:** a sweep that would have been lawful stops
and waits for the owner. **Cost if it is not taken:** a sweep can end a chain
without the guard seeing it.

Separately and not part of the proposal: §4b does not state whether the
sweep's overturns are subject to the protected-core floor and the conservation
law. §4b.5 calls the sweep "an ordinary governed act of the SYSTEM," which
reads as crossing the gate and therefore meeting every standing check, and
that is the right reading. EP-26 states it rather than leaving it to
inference, because a system act above the protected core would gap a shield
the conservation law says is never gapped.

### A.5 Sweeps serialize against law-family arrivals

§4b is silent on what happens when a second law-family record arrives while a
sweep is running. It becomes live pressure at EP-27, where the lanes carry
law-family records ahead of ordinary traffic. Replay-determinism survives
either way, because replay reproduces whatever record order occurred, but the
RESULT of two identical inputs would depend on the interleaving, and the
estate's determinism standard (design/21) is stronger than that.

**The correction.** A law-family arrival whose deciding time precedes recorded
acts is not accepted while a sweep is running; the sweep reaches its fixed
point, and the next arrival's sweep computes its candidates from the settled
record. EP-27's lane priority orders arrivals; it does not interleave a sweep.

### A.6 Three K3 battery rows are named in §8b but lowered into no EP

The §8b table maps T-RATE-GOVERNANCE, T-FOLD-AT-RATE and T-NO-STORED-TABLE to
EP-22 and EP-25. Neither EP's acceptance section names any of the three. EP-22
opens the measurement ledger and EP-25 appends to it, and a ledger of numbers
is not an acceptance test: a ledger records what was observed, a test asserts a
property and can fail. K3 is the invariant §9 names as the campaign's whole
risk, and as the EPs stand it is the invariant with no test that can fail.

**The correction.** All three are assertable and are added to the EPs by
marked addendum: recording tracks decisions and not operations (drive a
CACHE-class call population and assert zero appends; drive a DECISION-class
population and assert one covering record each); the authority fold's cached
answers are coherent-or-refuse; and the structure guard holds with no
permission table and no stored complement on any path. EP-22 carries the
observe-scale forms, EP-25 the custody-scale forms.

---

## ADDENDUM B — K3's second half, measured for the first time, and currently false (2026-07-26, sitting mentor, at the EP-22 verdict)

Appended per the paper standard's afterlife rule. Law, and read as part of K3.

**What K3 claims.** Recording scales with governance, never operation — "AND
the authority fold consulted at every gated act is priced the same way (the
re-pricing's second risk)." §9 names this the campaign's whole risk and says
the containment is to take the first numbers cheaply in observe mode, where
nothing can break. That containment worked exactly as designed, and this is
its result.

**What EP-22 measured.** The authority fold costs 0.14 ms over a 103-record
store and 11.5 ms over an 8,000-record store: linear, about 1.4 µs per record
already stored, with the op-definition read on the same path at a further
~1.3 µs per record. A whole gated act costs 6.2 ms at 103 records and 44.5 ms
at 8,000, which is roughly 5.7 ms fixed plus ~4.85 µs per stored record, or 22
acts per second at 8,000. The same EP measured ordinary machine activity
producing 1,287 records in 8.91 seconds, so an hour of observation is on the
order of half a million records and a gated act there costs seconds.

**The reading: this is an invariant not yet met, not a calibration awaiting a
value.** The fold's cost is proportional to the record's total LENGTH while
the fold's inputs are the law-and-grant subset, which grows with governance
and not with operation. Of the 8,000 records in that measurement the great
majority are observations, and an observation cannot change what
`covers(actor, action, info-kind, space)` answers. The proportionality is
therefore incidental to the law rather than required by it, and K3's second
half is false today for a reason that is fixable rather than intrinsic.

**The lawful remedy, and the one it is not.** K3 already names the shape:
acceleration is a measured calibration with a named owner, never a stored
table, and any cached fold answer obeys coherent-or-refuse. A derived index
over the law-and-grant subset satisfies that and is not the refused reference,
because the distinction the estate draws is exactly this: a stored permission
table holds the ANSWER, where an index holds only WHERE THE INPUTS ARE. Kill
the index, replay, it reconstructs identically — a cache under P2, pure
acceleration, provable by T-CACHE-KILL. What it must never become is a stored
verdict, a stored complement, or anything T-NO-STORED-TABLE would catch.

**Sequencing consequence, stated plainly because it moves the campaign.**
EP-25 puts a real filesystem on this path and its store will be far past 8,000
records. The crux cannot land on a gate doing 22 acts per second. Making K3's
second half true is therefore a PRECONDITION OF EP-25 with a measured reason,
not hygiene that can ride to the campaign close. The work is engine work in
the kernel files, so it is not EP-25's to do inside its own fence — EP-25's
fence already turns any engine gap into a stop-and-raise finding, correctly.

**What is NOT concluded here.** Which layer walks the whole record was not
determined; that is a question for the window that does the work, and this
addendum deliberately does not prescribe an implementation. No number here is
a target. The measurement's conditions are in
`planning/build/MEASUREMENTS.md` entry 1 and control over any summary of them.

---

## ADDENDUM C — K3's second half is met as written and the property it exists to guarantee is not (2026-07-26, sitting mentor, at the EP-24B verdict)

Appended per the paper standard's afterlife rule. Law, and read as part of K3
alongside ADDENDUM B.

**What EP-24B achieved, measured.** The authority fold is now flat against
record growth: 0.0676 ms at 104 records and 0.0714 ms at 250,104, with its input
subset at 12 records throughout, while the retained unaccelerated path runs to
184.9 ms at 100,104. It still grows with law-and-grant records, 0.069 ms to 101
ms as the subset goes 12 to 8,012. Both directions measured. K3's second-half
clause — "the authority fold consulted at every gated act is priced the same
way" — is SATISFIED, and satisfied by structure rather than by promise.

**What that did not buy.** A whole gated act at 8,104 records moved 56.9 ms to
43.4 ms: roughly 23 acts per second, against the 22 EP-22 measured. The
authority fold is now about 0.07 ms of those 43.4. Three other folds on the same
per-act path each read the whole record — the op-definition read at 16.5 ms,
active-rules at 13.8 ms, category-packs at 13.0 ms — and they account for
essentially all of what remains.

**The honest statement, and it is a distinction worth keeping.** The clause is
met. The property the clause exists to guarantee — that a gated act does not get
slower as the system records more — is not. ADDENDUM B named the authority fold
because that is what the first measurement named, and fixing it exposed that the
fold was never the whole cost. The evidence was already in the measurement that
produced ADDENDUM B: an authority fold of 11.5 ms inside an act of 44.5 ms is a
quarter of the cost, and this seat read the two numbers without subtracting them.
Recorded as an authoring error against the mentor line, because the record
polices its author too and because under-scoping a fix by arithmetic is the kind
of error that repeats.

**The defect is a CLASS and this addendum names it as one.** Any fold that reads
the whole record to answer a governance question has this defect, and nothing in
the estate currently prevents the next one from being written. Three instances
are named above; the fourth is that `views.op_definitions()` is not head-memoised
and recomputes two to four times per act, which is a repeated-recomputation
defect rather than a subset one. The lawful shape is already built and already
guarded: EP-24B's projection, extended to the record kinds these folds read,
under the acceleration boundary the owner's rider fixed as law and
`TestNoStoredTable` already enforces.

**The rule this addendum adds to K3.** A fold serving the gate's per-act path
reads a governance subset, never the whole record, and a structural guard fails
when a new whole-record fold lands on that path. Naming the instances without
the guard would fix three folds and leave the class, which is the error this
seat made once already this campaign and corrected for citations rather than for
folds.

**What is NOT concluded here.** No implementation is prescribed, no number is a
target, and whether the class fix precedes the crux is the owner's word. The
measurements and their conditions are `planning/build/MEASUREMENTS.md` entry 2
and control over any summary of them.

**A measurement-methodology note, from the same EP and worth more than its
size.** The gate exempts the chain-end from the authority step, so any act
measured as the owner never consults the fold at all and reports a cost that
does not exist. EP-24B's first before-and-after was wrong for exactly that
reason, and its builder caught it, re-measured every act figure as an ordinary
actor, and recorded the error on the stated grounds that the next person to
measure this path will make it. Every future measurement of the gated-act path
is taken as an ordinary actor, and a figure that does not say which actor it
used is not a measurement.

---

## ADDENDUM D — K3's second half is MET, measured; the remaining cost is the append (2026-07-27, sitting mentor, at the EP-24C verdict)

Appended per the paper standard's afterlife rule. Law, and read as part of K3,
closing the loop ADDENDUM B opened and ADDENDUM C carried.

**The measurement.** Every figure below is a gated act taken as an ordinary
actor with a real grant chain, per the method rule at ADDENDUM C's end.

| store size | gated act BEFORE | gated act AFTER |
|---|---|---|
| 106 records | 4.16 ms | 3.98 ms |
| 8,104 records | 36.86 ms | 4.06 ms |
| 100,104 records | 528.31 ms | 4.12 ms |

The act is FLAT against record growth. At the largest store measured the cost
fell by a factor of 128, and the property K3 asserts — that a gated act does not
get slower as the system records more — now holds as a measured fact rather than
as an intention.

**[The 2026-07-30 REOPENING is ITSELF WITHDRAWN the same day — see ADDENDUM O.
K3's second half STANDS as MET. The paragraph below is retained as the record of a
reopening that should not have happened; it was ruled on a throughput curve read as
per-act cost. Original reopening text follows.]**

**[REOPENED 2026-07-30 — see ADDENDUM N. The "MET" below stands for the FOLD class
at the stance and store sizes measured here, and is measured FALSE at 227,000
records. The append question this addendum leaves open two paragraphs down is the
one that came due. The text is not rewritten: it was true when written and the
caveat it carried was correct.]**

**K3's second half is therefore MET**, and met in the way the invariant asks:
by structure rather than by tuning, with a guard that fails when a new
whole-record fold lands on the per-act path, and with the acceleration boundary
the owner fixed as law proven per projection — killed and replayed identical,
coherent-with-the-record or refusing, and holding no answer anywhere.

**What the remaining cost is, and why naming it is the useful output.** One
steady act at 100,124 records is `store._append` at 4.48 ms, with every view read
together under 0.7 ms. The folds are done. What is left is the durable append —
the thing that must actually happen for a decision to exist, and the one cost the
architecture cannot argue away, since a record that is not durably written did
not happen (K1).

**The open question this leaves, named rather than assumed.** Whether the append
itself is flat against record count is NOT established: one figure at one store
size cannot distinguish a constant cost from a slowly growing one. That question
belongs to whichever round next measures the write path, and it is the right next
question rather than a defect. If the append proves to grow, it is a different
problem from the fold class — it is about how the record is written, not about
what is read to decide — and it would want its own derivation rather than another
projection.

**Two whole-record folds remain on conditional branches of the per-act path**,
both DECLARED with their reasons in the guard's own table rather than discovered
later: `opdefs.live_definitions`, which fires on amendment acts, and
`views.current_successor` reached through `chain_end`, which fires on EVERY act
once a handover exists. The second is a latent cliff rather than a current cost —
no handover exists in the live world today, and the first one created takes an
ordinary act from 4.1 ms to 49.9 ms. Homed at the campaign close with that
trigger named, because a cost that appears on a state transition is found in
production rather than in a benchmark unless someone writes down when it arrives.

---

## ADDENDUM E — §4b.7's trigger corrected to the effect-level invariant it always cited; §11 item 5 ruled (2026-07-27, OWNER-RULED)

Appended per the paper standard's afterlife rule. **Law.** Read as part of §4b.7,
§4b.5 and §11.

### E.1 — The anchor guard's trigger (owner ruling, 2026-07-27)

**The owner's framing, which is sharper than the question that was put to him and
which controls.** This is a CORRECTION, not an addition. The invariant was always
effect-level — no chain left rootless, root never moved, which is
CONST-AUTHORITY-ANCHORED — and **the three named kinds were the trigger written
narrower than the law it cited**. §4b.7 lowered an effect-level invariant into a
kind-match, and that lowering was the defect. Nothing new enters here; a trigger
is restored to the reach of the law it was always enforcing.

That distinction matters beyond the wording. A widening would be new policy owing
its own justification. A correction restores what CONST-AUTHORITY-ANCHORED
already requires, and the burden is the opposite one: the narrow trigger was the
thing that needed justifying and never had it.

**The amendment.** §4b.7's trigger is no longer a match on the overturned act's
kind. **The guard computes the question on the sweep's POST-STATE at the FIXED
POINT:** does what remains leave any chain without a root, or move root? If yes,
the sweep refuses and routes to the owner with the chain it would have ended.

**The fixed point is the right place and the reason is the finding that produced
this correction.** Orphaning is EMERGENT across the transitive rounds: a chain can
be ended one ordinary overturn at a time with no single step touching an anchor
act of any kind. A per-overturn guard sees nothing wrong at every step of a sweep
that finishes with authority orphaned. Checking earlier than the fixed point would
also over-refuse, since a chain can be transiently rootless mid-round and whole
again by the end.

### E.2 — What this entails for §4b.5, stated because it is forced rather than chosen

The guard can refuse at the fixed point, and ADDENDUM A.2 rules that an act once
overturned is never un-overturned. Those two together forbid appending as the
rounds run: a sweep that had already committed overturns and then refused would
leave authority orphaned with the record saying so, which is the accepted-but-
cannot-honour shape the estate refuses outright.

**So the sweep is two-phase.** The rounds COMPUTE — §4b.5's exclusion is a
derivation over a set and needs nothing appended to see its own effect — and
§4b.5's "until a round appends nothing" reads "until a round ADDS NOTHING TO THE
COMPUTED OVERTURN SET". The guard runs on that computed post-state. Only then does
the sweep commit, in one act. A refusal means NOTHING was appended and the whole
sweep routes to the owner.

This is entailment rather than instruction: if it is not what the ruling meant,
the ruling controls and this section is wrong.

### E.3 — The two requirements on the swap (owner-set)

**1. The strictly-stronger proof runs on an EXTENDED ledger**, per the standing
retirement law — an old ledger cannot contain cases in a dimension it could not
express, and the old guard's ledger holds only kind-matches while the new
dimension is EFFECT. The extension carries both directions:

- **the accumulation case** — a chain orphaned by ordinary overturns only, no
  named-kind act anywhere in the sweep. The old trigger misses it entirely; this
  is the case the correction exists for.
- **the non-orphaning named-kind case** — an overturn whose target IS a handover,
  succession or root grant and which orphans nothing. The old trigger refuses it
  and the corrected one permits it. **That is an OVER-REFUSAL being removed
  deliberately**, and it must be proven deliberate rather than discovered later as
  a regression.

The second is the half that is easy to skip and it is why the ledger is extended
in both directions rather than only where the guard gains reach.

**2. This paper carries the correction as a dated amendment crediting the
four-gate review's re-derivation.** It does: the emergent-orphaning finding came
from the sitting mentor's independent re-derivation of §4b at the four-gate
review, 2026-07-26, recorded then as ADDENDUM A.4 and raised as PROPOSED pending
this ruling. Credited here as the owner directed.

### E.4 — §11 item 5, the write-coalescing value: RULED

**RULED (owner, 2026-07-27): the proposed default is CONFIRMED unchanged** —
per-fd bursts closed by close, fsync, or the proposed threshold.

The owner's reasoning is carried because it is what makes the confirmation cheap
rather than a commitment: it is recorded policy under latest-wins, so if a finer
account is ever wanted, narrowing the policy is an ordinary recorded act, and the
measurement ledger will say when. The value is not a permanent choice; it is a
recorded rule amendable through the ordinary door, and the evidence for changing
it will arrive as measurement rather than as opinion.

Three independent measurements stand behind the confirmation: folding changes how
many records exist and changes no verdict, no cited rule and no replayed state,
with the conformance spread between the folding and non-folding worlds measured
at ZERO on the third and final round.

**§11 item 5 is CLOSED.** Every item on the ruling list is now ruled except item
6, the EP-28 kernel-entry word, which remains his at that gate.

---

## ADDENDUM F — §4b.2's DOMAIN, and K7's honest cap (2026-07-27, at the EP-26 verdict)

Appended per the paper standard's afterlife rule. **Law.** Read as part of §4b.2
and K7.

### F.1 — The reach test's domain: a record that never crossed the gate has no admission to flip

**The finding, and it is the sharpest thing EP-26 produced.** The sweep's first
smoke run proposed **overturning the entire founding**. Genesis records are
appended DIRECTLY, so re-running the gate's admission test over them asks whether
the founding was permitted by the world the founding was in the middle of
creating — and every one refuses for want of a grant not yet minted.

**The derivation is the builder's and it is correct.** §4b.2 says X is reached iff
re-evaluating X's ADMISSION as of d(X) with L present flips the recorded outcome.
A record that never crossed the gate has no admission, so there is no outcome to
flip. The reach test's domain is ADMITTED records, and that was never stated
because it never had to be until something re-ran the test over a record that
bypassed the door.

**The rule.** §4b.2's candidate set is records that were ADMITTED — that crossed
the gate and have a recorded outcome to re-evaluate. Records appended by a path
that bypasses the gate are outside the sweep's domain entirely, not permitted by
it and not refused by it. The bypassing paths are the ones the gate's own guard
already names, and the exemption is READ from what the estate computes rather
than from a list in code, per the standing law that governance content never
lives in a code verb-list.

**What the four-gate review missed, recorded because the absence is the lesson.**
That review re-derived §4b.1's tie rule, §4b.5's termination, §4b.3/.4's
asymmetry and §4b.7's anchor coverage. It never asked what the reach test's
DOMAIN was. Four derivations were run and the fifth — the one that would have
proposed destroying the founding on first contact with a late-arriving law — was
not among them, because a record that never crossed the gate was invisible to a
review reasoning about which admitted acts flip. **A derivation can be right about
every case it considers and silent about the set it is quantified over.**

**One interaction worth recording.** Had this shipped, the two-phase sweep from
ADDENDUM E.2 would have computed a post-state with the founding overturned, the
effect-level anchor guard would have found every chain rootless, and the sweep
would have refused and routed to the owner without appending anything. Two
corrections made for unrelated reasons, one containing the other's absence. That
is what the layering is for, and it is not an argument for relying on it.

### F.2 — K7's reachability cap, named rather than assumed

**The machinery of K7 is built and proven and is currently UNREACHABLE through
the shipped founding.** No op in the founding pack can submit a law-family record
whose deciding time precedes its recording time, because `occurrence_time_param`
refuses when its declared parameter is absent — correctly — so declaring it on
`CREATE-RULE` would make every existing caller nonconforming. What is missing is
a router declaration that permits an ABSENT parameter and falls back to the
envelope default, which the store already provides.

So the sweep fires in disposable test worlds, reached there through `AMEND-OP` —
the engine's own capability, tier conserved, the amendment itself a record — and
cannot fire in the live world.

**K7 is therefore NOT YET MET and this is stated rather than left to be
discovered at the campaign review.** The invariant reads "two times govern every
crossing"; today they govern every crossing that can be expressed, and the
expression is what is missing. The machinery being correct is not the same as the
invariant holding.

**The fix is one distinction in a declaration** — whether a router's parameter is
required or defaulted — and it closes TWO carried items at once, because EP-25's
R-1 is the same defect on `provenance`: a router that refuses on absence cannot be
declared on an op with both port and non-port callers, which left five inherited
ops incomplete there. One fix, two items, an invariant riding on it.

**Consequence for the campaign close, stated so nobody treats that round as a
tidy-up.** The close pack now carries an INVARIANT, not only hygiene. The campaign
cannot be declared done with K7 unmet, so the close round is required rather than
optional, and this item is its first entry rather than one of thirteen.

---

## ADDENDUM G — a shed is the ABSENCE of an act; the episode is the decision (2026-07-28, at the EP-27 W5 verdict)

Appended per the paper standard's afterlife rule. **Law.** Read as part of K10
and K3.

**The finding, and where it was found is the point.** EP-27's `shed` and
`starved` lists are unbounded derived structures that grow with the flood — 1,118
entries from a 200-act flood. Nothing is appended, so the flood boundary holds
and P2 holds: kill them, replay, they reconstruct. But the worker's memory and
`lane_report()`'s answer are proportional to OPERATION, **inside the very
mechanism built to keep the system governance-proportional under load.** The
thing designed for the extreme case fails in the extreme case.

**Neither obvious answer works, which is why this needs a ruling rather than a
fix.** Recording each shed would make records proportional to operation, which is
K3's violation stated exactly. Remembering each shed without recording it is what
is there now, and it moves the same unboundedness from the record into a process
that has to stay up. EP-27's own W3 says every shed is "recorded citing the
policy" while the flood boundary says deliveries append nothing, so the plan
carried the tension unresolved and the builder resolved it the safe way.

**The derivation.** A delivery appends nothing. **Not delivering is not an act —
it is the absence of one**, and an absence has nothing to record. What IS a
governed decision is the system ENTERING and LEAVING a shedding regime under a
named budget: two records per episode, citing the policy, with a count. That is
governance-proportional, because the number of flood episodes tracks governance
while the number of shed items tracks operation.

**So the class map answers it, and the answer was already in the map.** Individual
sheds are **STREAM** — sampled aggregate, never load-bearing, exactly as
read-traffic is. The episode boundaries are **DECISION** — entered shedding at T
citing the budget, left at T'. The worker keeps a counter and the current
episode, never a list. Bounded by governance in both memory and in what
`lane_report()` can be asked.

**The general rule this carries beyond lanes.** A derived structure that grows
with operation is the same defect as a record that grows with operation, one
layer down, and it is harder to see because nothing is appended and every
standing check stays green. Any mechanism that observes traffic keeps AGGREGATES
of the traffic and RECORDS of its own regime changes. If a derived structure's
size is a function of how busy the system was rather than of how much governance
happened, it is the wrong shape whatever the flood boundary says.

**Not this EP's defect and not fixed here.** The builder found it, read it in
`push.py` at the enqueue and drain paths, left it because the fence said so, and
raised it. Homed at the campaign close with this derivation attached so nobody
re-derives it.

---

## ADDENDUM H — K7 is MET; and a required pin can be satisfied by a fabricated default (2026-07-28, at the EP-27B verdict)

Appended per the paper standard's afterlife rule. **Law.** Read as part of K7,
and it closes ADDENDUM F.2's cap.

### H.1 — K7 is MET in the live world

The reconciliation sweep fires through the SHIPPED founding: a law-family record
carries a deciding time that precedes its arrival, the sweep runs, overturns are
appended, the record reconciles, and the whole thing survives replay from the
record file alone. No amendment and nothing test-only in the path, asserted by
the row's own honesty check rather than claimed in a log.

**The evidence is the ordering, and it was produced deliberately.** The builder
landed the mechanism alone first, with the founding untouched: every mechanism
row went green and **every K7 row stayed RED**, because no shipped op could carry
a deciding time. The pack edit turned them. A cap that was argued at ADDENDUM F.2
is now a cap that was measured — failing first, passing after, on the same tree.

**ADDENDUM F.2's cap is CLOSED and K7 holds.** Every end-state invariant this
paper declares is now met or honestly capped, with one expressiveness gap named
at H.3 that is not K7's.

### H.2 — A required router's refusal can be satisfied by a fabricated default

**The defect, found by running rather than by reading.** `param_defaults`
resolves BEFORE the routers. So an op declaring
`param_defaults: {"at": "1999-01-01T00:00:00+00:00"}` alongside a **required**
`occurrence_time_param: "at"` records that instant on every call, and the
required router's refusal never fires. Confirmed on a founding-only world. It
predates EP-27B and the shipped founding uses no such combination.

**This is the trap EP-27B named, one layer down and through a different door.**
That EP refused "defaulted" sliding into "does not matter" and guarded it at the
declaration. `param_defaults` reaches the same outcome without touching the
declaration at all: the pin is still declared REQUIRED, still reads as required,
and cannot refuse. So the guarantee EP-22 built — a record missing a pin refuses
at submission — is **claimed and defeasible**, holding today only because nobody
has written the combination.

**The ruling.** A `param_defaults` entry for a parameter that a router declares
is REFUSED AT DEFINITION TIME. A default and a required pin are contradictory
claims about the same field, and the contradiction is resolvable by reading the
definition, so it is refused where it is written rather than discovered where it
fires. A parameter that may be absent says so through the router's own
distinction, which is the one place that decision belongs.

**Why this is not a boundary question under charter §A17, stated plainly so the
rule is not stretched.** §A17 holds a boundary for an unmet INVARIANT, not for a
defect. K7 is met; every shipped op is honest; nothing is currently untrue. This
is a defect that could PRODUCE an unmet invariant, which is a different thing,
and treating it as the same would make §A17 mean "nothing crosses a boundary
until nothing is wrong" — which would stop everything forever and is not what was
ruled.

**It is nonetheless fixed before Arc C, on judgment rather than on rule, and the
reasoning is exposure.** Arc C mints op definitions for devices, communication,
memory and scheduling — the largest population of new definitions the campaign
will produce. `param_defaults` is an ordinary convenience, so the combination
arrives by accident rather than by intent, and the arc that follows is precisely
the one that multiplies the chances. Fixing one definition-time check now costs
one work item; finding it later costs a subsystem's worth of definitions written
under a guarantee that was not holding.

### H.3 — What is closed, and what is not

K7's DECIDING-TIME expression is closed. Its SCOPE expression is not: a
space-local law is still unwritable through the shipped `CREATE-RULE`, raised at
EP-26 and unchanged here. Named so this addendum is not read as every law shape
having become expressible — one dimension opened, and the other is where it was.

---

## ADDENDUM I — H.2 was over-broad; the family must read one map; and the founding installer validates SHAPE (2026-07-28, at the EP-27B W6 stop)

Appended per the paper standard's afterlife rule. **Law.** It CORRECTS ADDENDUM
H.2 and is read with it.

### I.1 — H.2's rule was stated at a generality its mechanism does not support

H.2 ruled that a `param_defaults` entry for a parameter **that a router declares**
is refused at definition time, and said the shipped founding was clean. Both
halves were wrong in the same way, and the builder found it by scanning the pack
before writing anything.

**The shipped founding carries the combination once:** `SHM-GRANT` declares
`target_param: ['grantees']` alongside `param_defaults: [{'grantees': [], ...}]`.

**And it is lawful, which is the part that matters.** The routers do not all read
the same map. The two store-minted ones read the COPIED parameter map that
`param_defaults` has already filled, which is exactly how a default satisfies a
required pin. `target_param` reads the caller's RAW parameters, with the line's
own comment stating that a missing field must record `target=None` exactly even
when the same parameter is defaulted in the payload. So a default cannot reach the
target field, there is no contradiction, and `SHM-GRANT` is honest.

**The defect is real and it is narrower than H.2 said.** H.2 generalized from "a
router" when the mechanism is "a router that reads the post-defaults copy." This
seat stated a rule at a level of generality its own mechanism does not support —
the eleventh authoring correction of this campaign and the same class as several
before it.

### I.2 — The root is TWO MECHANISMS FOR ONE IDEA, and the fix is uniformity

Neither of the two readings available to a builder is right, and its refusal to
write either was correct. The narrow reading installs a guard quietly weaker than
the one ordered. The wide reading changes a shipped op's recorded payload. Naming
`SHM-GRANT` inside the check is governance content in a code verb-list, refused at
ADDENDUM F.1.

**The root is that `param_defaults` and the router's own `when_absent`
distinction are two mechanisms for one idea** — how an envelope field is supplied
when the caller omits the parameter. EP-27B's own raise list warned about exactly
this shape: two mechanisms for one idea is how the next four arrivals get created.

**So the ruling is uniformity rather than refusal.** Every member of the router
family reads the SAME map, and it is the RAW caller parameters, as `target_param`
already does. Then `param_defaults` can never reach a router's field, the
contradiction is structurally impossible, and no definition-time refusal is needed
for it at all. A parameter that may be absent says so through the router's own
distinction, which remains the one place that decision belongs, and it falls back
to the store's minted value rather than to an author-chosen constant.

That dissolves the class instead of guarding it, and it leaves `SHM-GRANT`
lawful by construction rather than by exception.

**With the stop that bounds it:** if making the family uniform would change what
any SHIPPED op records, that is a finding and a stop, not a change to be made.

### I.3 — Founding-only legitimacy exempts AUTHORITY, never SHAPE

**The larger finding, and it reaches past the item it was found under.** Op
definitions reach the registry through three doors. `CREATE-OP` and `AMEND-OP`
carry the full definition-shape vocabulary. The third is the founding installer,
which appends every pack record directly and whose only pre-flight checks
referential integrity for tunnel actors, law scopes and grant spaces. **No
definition-shape validation runs over the pack at all**, all 72 live op
definitions entered that way, and Arc C's device, comms, memory and scheduling
definitions will too.

So a definition-time check at the first two doors sits away from the traffic. That
is not a defect in EP-27B, which guarded the doors it was pointed at; it is a
finding about where definitions actually enter.

**The ruling, and the distinction is the whole of it.** Founding-only legitimacy
means nothing can AUTHORIZE the founding — it enters at genesis and its
legitimacy is live-under-it-or-exit. That exempts the founding from AUTHORITY
checks and it exempts it from nothing else. **A record that cannot be interpreted
is not made interpretable by being at genesis.** Shape is not legitimacy: a
malformed declaration is malformed whoever wrote it and whenever it arrived.

The founding installer therefore validates definition shape with the same
vocabulary the `CREATE-OP` path uses. One validation, three doors — the estate's
own enforcement-at-the-chokepoint theorem applied to definition shape rather than
to authority.

**An expected outcome, named so it is not a surprise:** turning validation on over
72 definitions that have never been validated may find some that do not validate.
That is the point of doing it, and each one is a STOP and a raise rather than
something fixed inline.

---

## ADDENDUM J — the `evidence_param` precedence change is the SAME ruling one field over; and what "three doors" rests on (2026-07-28, at the EP-27B W6 verdict)

Appended per the paper standard's afterlife rule. **Law.**

### J.1 — The behaviour change is CORRECT and is not a side effect to revert

Making the router family uniform changed `evidence_param`: where a definition
declares a `param_defaults` entry for the evidence parameter AND an
`evidence_default` for the same field, the definition's own now wins where the
general one used to. No shipped op combines them, so nothing live moved.

**That is ADDENDUM I.2's ruling applied one field over, not a consequence of it.**
I.2 ruled that a parameter which may be absent says so through the FIELD-SPECIFIC
declaration, because that is the one place the decision belongs. `evidence_default`
IS the field-specific declaration for the evidence field; `param_defaults` is a
general convenience. One field with two declared fallbacks and the general one
winning is precisely the two-mechanisms-for-one-idea shape I.2 exists to refuse.

So the previous precedence was a latent wrong-precedence defect, and uniformity
did not create a change — it surfaced and corrected one, in a case nobody was
looking at. **Accepted as built and not reverted.**

### J.2 — What "three doors" rests on, named because it is a dependency and not a proof

The claim that op definitions reach the registry through exactly three doors, and
that replay may therefore re-read definitions without re-validating them, rests
entirely on the sole-appender theorem: every operation-defining record was written
by the gate or by the installer. That theorem is campaign 1's and it is cited
rather than re-proven.

**The cap this leaves, stated once:** a fourth appender would break the claim
silently. Replay would re-read definitions that no door had validated, and the
one-validation-three-doors guarantee would be a guarantee about three of four
doors. Nothing today creates a fourth appender and the estate's own enumeration
of appender sites is what protects it, but the dependency is written down here so
that a future round adding a write path knows it is standing on this.

### J.3 — Two honest caps carried from the same pass

No shipped definition declares an external-executor station, so the station half
of the founding door's new validation is wired and has never run there. And the
family's completeness check works out which members name a parameter from how
they are SPELLED — true today, tested, stated at the line, and wrong the day a
member is spelled against the convention. Both are homed at the campaign close;
neither is exercised by Arc C, which mints op definitions rather than router
members.

---

## ADDENDUM K — the volatile boundary: four rulings, and the definitive DEFERRED on purpose (2026-07-29, OWNER-RULED)

Appended per the paper standard's afterlife rule. **Law.**

Raised by the owner ahead of EP-31's authoring, as a scope question rather than a
build one: is volatile and temporary storage governed anywhere, or delegated
entire? Five surfaces were put: process memory isolation, swap, core dumps,
file-backed shared writable mappings, and residue in freed frames between runs.

### K.0 — What the five turned out to be, which is why they read as separate gaps

**They are one question in four costumes, and it is not a threat-model question.**
The estate has no threat model by standing ruling (03 §0; `00-READ-FIRST` §7's
frame guard; `design/18` §90; `design/24` §86 — "the frame is derivation, not
threat models"), and that ruling stands untouched. But **custody is not security.**
Asking whether the record still owns content once it is a page, a swap block, a
dump, or a freed frame is a K1 question expressible with no adversarial framing at
all. The frame guard forbids organising the kernel around who might reach the
content; it does not excuse a gap in whether the record owns it.

**Process memory isolation is the one surface that is genuinely delegated and
stays so.** 03 §4.4 is the only isolation the estate claims, it is the DEVICE
boundary, and `design/24` §3 caps even that: enforcement strength is a deployment
choice, the governed record is the architecture. The MMU enforces; gov-os records
the grants. What the estate does claim is complete and unchanged — every route by
which one actor reaches another's memory is a recorded rule-citing decision
(`ptrace`, `process_vm_readv/writev`, `shmget`/`shmat`, `mmap(MAP_SHARED)`,
`io_uring_setup`). Nothing to rule; it was never in the set.

### K.1 — mmap: §4.3 owns it, the refusal is PERMANENT, and its scope is narrow

Ruled in full at `design/10` §11.1g's 2026-07-29 amendment, which is the operative
text. The campaign-level facts: **§4.3 owns a file-backed shared writable mapping,
not §4.5.** The M3-stance refusal STANDS and **M6 does not loosen it**. Scope is
shared writable file-backed mappings only — read and execute mappings are fills
and stay served, so program and library loading are untouched. Any future serving
returns through an explicit recording moment with `msync` as the commit point,
never silent writeback and never the §4.5 interior reading.

**This is the only one of the four that changes what EP-31 is built to do**, which
is why it was ruled ahead of authoring rather than at the close.

### K.2 — Core dumps: a named BUILD CONSTRAINT on EP-31 and EP-32, not a rule of its own

A crash dump is the only surface of the four that MINTS a new object. Swap
re-parents content already content-addressed; residue is content nobody minted; a
dump copies governed memory into a file that did not exist. So the exposure is not
containment, it is **an end-state invariant**: a dump written outside the files
subsystem is a code path writing a file outside the gate, and `design/28` **I2**
says the gate is the sole appender.

**Ruled: the dump path goes through the gate, and EP-31's and EP-32's orders state
it.** No new law is needed — `design/26` §8 already maps a dump to "mint content
item of state" and §4.3 makes its content DECISION-class. The derivation covers it
and the orders must say so, because a builder meeting a crash path with no
instruction will reach for the platform's own dump mechanism.

### K.3 — Swap and residue: one line each, to the close ledger

**Swap** (EP-33 item 24): content reaching a swap device is a files-subsystem
DECISION through the gate, and no swap-out bypasses it. Already covered by
derivation (`design/22` §4 makes swap writes content-hashed file decisions; §4.4
makes the device a capability grant); what is missing is the sentence and the
`swapon`/`swapoff` rows, which are in neither `design/10`'s catalogue nor its
named exclusion list.

**Residue** (EP-33 item 25): the anonymous-memory replay invariant DEPENDS on the
platform zeroing freed frames, and that dependency is stated so
`T-CACHE-KILL-SWAP` is not written blind to it. **This is a replay-determinism
statement, not a containment one** — `design/22` §4's "anonymous pages never
written are zero by definition" is false if a freed frame arrives carrying old
content, and then reconstruction produces a different image than the original run.
The failure shape is the worst kind for an instrument: green on a platform that
zeroes, red on one that does not, with nothing in the test naming why.

### K.4 — The definitive is NOT ruled now, and the reason is on the record

The root question — does custody follow content across the volatile boundary? —
is **deferred to M6 by the owner's word**, on the sitting mentor's read that the
root is **unassembled rather than missing**. §4.3, §4.5, §11.1g, `design/22` §4
and `design/28` I2 all bear on it and had simply never been read against each
other. Reading five existing rulings against each other IS the root work, and it
is smaller and better founded than authoring a new definitive against a memory
subsystem that does not exist yet. A root rule written now would be written
against imagined cases; the same rule written after EP-31 measures is written
against a running one.

**The four rulings above hold the line until M6 measures.** The definitive is
carried as named intake, priced as known-unasked rather than found-late.

---

## ADDENDUM L — the speed tension was never a GOVERNANCE tension; it is a DURABILITY tension (2026-07-29, at the EP-28 W8 verdict)

Appended per the paper standard's afterlife rule. **Law, and it is the campaign's
headline result.**

### L.1 — The measurement

One gated act at kernel rate, below the syscall line, measured by a standing
instrument that establishes its own subject:

| component | share of a 2.6–3.5 ms act |
|---|---|
| **the durable append** | **71–85%** |
| every per-act fold together | 13–23% |
| **the authority fold** | **0.8–1.7%** |
| the bridge's own arithmetic | 0.3% |

`stat` is 0.003 ms and crosses nothing. A header is always 2 records and 2
crossings.

### L.2 — What this does to the campaign's own framing

Campaign 3 inherited the speed tension from `design/03` §1–2 and `design/22`,
where it was posed as **the cost of governing**: does recording every governed act
destroy performance? `design/22` answered the hot-path half by showing the busiest
paths append NOTHING because they are cache fills applying already-recorded
decisions. **W8 answers the other half and the answer relocates the question.**

**When a record IS appended, governance is 0.8–1.7% of the cost and durability is
71–85%.** The authority fold — the thing this estate exists to perform, the check
that a governed act is covered — is a rounding error against making the record
exist. **Every per-act fold together, the entire derived-not-stored discipline, is
13–23%.**

So the tension that has been priced, argued and engineered against for two
campaigns is **a storage tension wearing governance's clothes.** Any system
appending a durable record per act pays the same 71–85%, governed or not. The
governance is the cheap part and always was; nobody had measured it.

### L.3 — Why the 71–85% is not a cost to trade, proven by cutting the power

The builder proved the floor by **cutting the guest's power, twice.** An
`fdatasync`ed record survives 300 of 300. And the unsynced case does not fail the
way an engineer expects: **the record does not come back SHORT, the file did not
exist at all.** The module, brain and mount then re-raised over the surviving
record and served all 20 governed files.

**The builder's sentence is the ruling and it is carried verbatim: the sync is not
a cost to trade, it is what makes the record exist.** An append that is not
durable is not an append. The 71–85% is not overhead around the record; it IS the
record.

### L.4 — The floor, and the one lever past it

**Floor: 1.30–2.31 ms per gated act.** Defconfig kernel build projects ~3.2 h at
the FUSE port, ~0.5–1.1 h today, **floor ~0.22–0.38 h.**

**Group commit is the ONLY lever past the floor** — 5.6× at batch 8, 13.5× at
batch 16 — and the channel admits one caller at `govosfs.c:120`.

**[CORRECTED 2026-07-29, OWNER-RULED, same day. The paragraph that stood here was
wrong and the error was this seat's.]** It read the one-caller channel as the
single-writer law and concluded that group commit was the S5 multi-writer question
in costume, carrying S5's lead time.

**The ruling: the store has ONE APPENDER; the channel may admit MANY SUBMITTERS
in flight.** "One caller" at `govosfs.c:120` was a LOWERING of the one-writer law,
not the law. Many submitters queueing into one appender create no second writer.
**S5 covers multiple APPENDERS only — federation — and is untouched by this.**

**So group commit is not blocked, not deferred behind S5, and not an
architectural question. It is lawful engineering behind the owner's ruling, and it
enters as a directed EP after EP-28B** (`planning/exec/EP-28C.md`). The seat's
error is the definitive/derivative confusion running backwards: an implementation
lowering was read as the law it was lowered from, and the consequence was a 13.5×
lever misfiled as a campaign-scale dependency.

**Four invariants ride with the ruling and bind that EP's authoring:**
1. **No reply releases before the sync covering its record.** Non-negotiable.
2. **A batch closes on QUEUE-EMPTY or timeout, whichever comes first**, so light
   traffic never waits for a window that cannot fill.
3. **Batching syncs is NEVER coalescing records.** Every record appends
   individually and attribution is untouched — which is also why this does not
   collide with close-ledger item 30's constraint that coalescing never span
   actors. Nothing is merged.
4. **Async-ack — reply-before-sync — is that EP's named wrong reference.**

**And the concurrent-workload measurement lands there**, which removes it from the
uncited list below on the ground that the reason it could not be measured was
itself the error corrected here.

### L.5 — The honest cap, and it is large

**The floor is a property of THIS SUBSTRATE**, a qcow2 image on virtio, not a
property of the architecture. A physical device — NVMe, a battery-backed
controller, spinning rust — moves it, in either direction and possibly by an order
of magnitude. **Every citation of "the floor" carries the substrate with it or it
is a claim about a virtual disk being passed off as a claim about gov-os.**

**AMENDMENT [2026-07-31] — the HOST's own memory condition is part of the substrate
and was never stated.** For roughly the last two EPs the host ran at 282–374 MB free
with 15 GB in swap, and the guest's pages were being paged out from underneath it.
**That condition was not recorded beside any figure taken in that window.**

**What it does and does not touch, and the split is clean.** **COUNTABLES are
unaffected** — entries examined, records appended, crossings, namespace steps do not
move with the host's memory. **COMPARATIVE conclusions survive**, because both arms
of every comparison in that window were taken in one session under the same
condition, so the pressure applies equally to each side. **ABSOLUTE durations from
that window carry an unstated host-pressure condition** and are not directly
comparable to durations taken on a healthy host.

**The affected figures are named rather than left to be inferred:** ADDENDUM O's and
P.4's per-act decompositions, and W5's stance-3 `stat` timings. **In every case the
load-bearing evidence was a COUNTABLE** — 192,007 entries → 2, zero namespace steps
in both arms — **so no conclusion in this paper rests on an absolute duration from
that window.**

**The rule this generalises to: §L.5's substrate clause covers the HOST as well as
the guest.** A figure taken inside a virtual machine is a figure about the host it
runs on, and **a host under memory pressure is a different substrate from the same
host at rest.**

Also uncited until measured: the kernel-build-scale run to completion (a projection since EP-25),
a large store at kernel rate (largest measured 3,648 records), the mapping path in
TIME rather than counts, and a cold start at this stance.

---

## ADDENDUM M — L's fold band is SUPERSEDED by measurement, and L's headline gets STRONGER (2026-07-30, at the EP-28B verdict)

**The question put: should ADDENDUM L's 13–23% be restated to 1.4%, since a paper
figure now contradicts a measured one? RULED: NO — L's figure STANDS as written,
and this addendum carries the new one.**

**Why the paper figure is not rewritten.** L's 13–23% was a true measurement of
the code as it stood on 2026-07-29. EP-28B's W3 then changed that code.
**Overwriting the old number destroys the only evidence that the change had an
effect** — a paper whose figures silently track the current build cannot show
anyone that anything improved. Preserve, do not smooth: both numbers stand, the
delta is the finding, and L §L.1's table is read with this addendum beside it.

**The new figure.** W3 made `_bump(e)` consult the projections' own `_selects`
predicates rather than bumping every generation on every append. Measured in the
guest against a live 3,205-record store: **21 gated acts cost 0 fold-body
executions; one `CREATE-RULE` costs exactly 1.** The derived share: **the per-act
fold budget falls from 13–23% to about 1.4%.**

**And the builder's own reading of what that band WAS is the finding under the
finding: nearly all of 13–23% was the INVALIDATION, not the folds.** ADDENDUM C
guaranteed the folds read a subset and they did. The cost was never in the reading;
it was in recomputing things that had no reason to recompute.

**HONEST CAP on the 1.4%.** The COUNTABLE is measured — 0 fold-body executions
across 21 gated acts. **The percentage is DERIVED from that countable against L's
prior timing**, not independently timed. That is the right way round per the
standing rule that a property test asserts a countable, and it is stated so nobody
cites 1.4% as a stopwatch reading.

**L's HEADLINE STRENGTHENS rather than weakening, and this is the part that
matters.** L relocated the speed tension: governance is not what costs, durability
is. **If the entire per-act fold budget is now ~1.4%, the durable append's share
RISES.** The authority fold at 0.8–1.7% sits inside a total governance cost of
about 1.4%, against a durable append at 71–85% and climbing. **The claim that the
speed tension was never a governance tension is more true after EP-28B than when
it was written.**

---

## ADDENDUM N — WITHDRAWN. Ruled on a THROUGHPUT curve read as PER-ACT COST. See ADDENDUM O.

> **[WITHDRAWN 2026-07-30, same day, by ADDENDUM O.] Everything below was ruled on
> a throughput curve — records per second during a `tar` extraction — restated by
> this seat as per-act cost. Direct decomposition of the act at 371,856 records
> REFUTES it: the act is flat and ADDENDUM L holds. K3's second half is NOT
> reopened.**
>
> **The pack that carried the curve labelled it correctly in its own deviations:
> "the curve is throughput rather than sampled act cost." This seat read past the
> cap and ruled in a unit the evidence did not carry.**
>
> **The text is retained unedited as the record of what was ruled and on what.** A
> withdrawn ruling deleted is a campaign that cannot show it corrected itself.

## ADDENDUM N (WITHDRAWN — retained as the record) — K3's second half is REOPENED: the act is NOT flat at scale, and the campaign predicted this in writing (2026-07-30, at the defconfig phase-1 report)

Appended per the paper standard's afterlife rule. **Law, and it is the most
consequential finding of campaign 3.**

### N.1 — The measurement

Fresh disposable world at founding 1.13.0, one workload (6.18.38's tree as file
content, 91,191 files), substrate qcow2 on virtio, guest 4096 MB / 2 vCPU on
`6.8.0-134-generic`.

| store (records) | cost per governed act |
|---|---|
| 46,815 | 8.0 ms |
| 104,377 | 13.2 ms |
| 158,533 | 22.9 ms |
| 201,253 | 29.2 ms |
| 227,000 | **~50 ms** |

**Store grew 4.8×; per-act cost grew 6.3×.** Slightly super-linear. Rate fell
monotonically from 124.6 records/sec to about 20/sec across ten intervals **with no
plateau.**

### N.2 — This was NAMED as the open question, by this seat, three days earlier

**ADDENDUM D, 2026-07-27, in its own words:**

> Whether the append itself is flat against record count is **NOT established**:
> one figure at one store size cannot distinguish a constant cost from a slowly
> growing one. That question belongs to whichever round next measures the write
> path… **If the append proves to grow, it is a different problem from the fold
> class** — it is about how the record is written, not about what is read to
> decide.

**The append proved to grow. D's classification is therefore already ruled: this
is the WRITE path, not the fold class**, and it wants its own derivation rather
than another projection.

**And ADDENDUM L, 2026-07-29, supplies the other half nobody put beside it: the
durable append is 71–85% of a gated act.** Read D and L together and this outcome
is not a discovery, it is an arithmetic consequence — **if the append is nearly the
whole cost and the append is not known to be flat, then anything that grows will
present as almost the entire curve growing.**

**That is this seat's error and it is the third of its kind in one week: two filed
laws, each true, never read against each other** (charter §A26's family). L was
filed one day after D. Nothing was hidden and nothing was wrong; the two simply sat
in the same paper without being put side by side.

### N.3 — K3's second half is REOPENED

`design/36` ADDENDUM D declared K3's second half **MET** on evidence that the act
was flat at 4.12 ms across 106 / 8,104 / 100,104 records. **That evidence stands
and is not withdrawn — it was true, for the FOLD class, at the stance and store
sizes measured.**

**K3's second half is nonetheless now measured FALSE at 227,000 records**, and D's
own text is the reason it could be: D closed the fold question and left the append
question open in the same breath. **The MET carried forward; the caveat did not.**

**RULED: K3's second half is REOPENED and is the campaign's live invariant
question.** It is not met until a gated act is flat against record count with the
WRITE path measured, not only the read path.

### N.4 — What is NOT refuted, stated so nobody over-corrects

**ADDENDUM L's ratios stand and its headline stands.** They were measured at a
store of a few thousand records — a regime where this effect is invisible — and
nothing about them was wrong at that scale. **What is now known is L's SCOPE**, and
every future citation of L carries it: *71–85% / 13–23% / 0.8–1.7% at a store of
a few thousand records.*

**L's relocation claim survives and arguably strengthens.** L said the cost is
durability rather than governance. **This run says the durability cost is worse
than L knew**, which moves the number without moving the attribution — the folds
are still not where the time is, and W3 cut them further.

**ADDENDUM M's 1.4% likewise carries its scale**, and its countable is unaffected.

### N.5 — Existential if a property, ordinary if a defect, and the record says defect

**Stated plainly because it should not be softened: a store whose per-act cost
grows with record count cannot be a kernel.** A kernel's record grows without
bound. If this is a property of the architecture, the architecture does not reach
its own target state.

**Three reasons on the record to expect a defect rather than a property.**
1. **A flat curve at 100k records was ACHIEVED and MEASURED once** (ADDENDUM D,
   4.12 ms at 100,104 records) after EP-24B and EP-24C removed a whole-record fold
   from the per-act path. **The same shape has been found and removed before, in
   this campaign, by this method.**
2. **An append to an append-only file is O(1) by construction.** Growth in it is
   something else wearing the append's name — a candidate class rather than a
   candidate line.
3. **The mechanism is unattributed, which is a fact about the measurement rather
   than about the system.** Throughput was measured; the per-act breakdown was not.

**None of that is evidence. It is the reason the next act is attribution rather
than redesign**, and the estate's own rule applies to itself here: locate the root
before touching any surface.

### N.6 — The next measurement, and phase 2 STAYS STOPPED

**Phase 2 does not run.** The standing instruction was that a bending curve is
worth more than a completed build; it bent, and a defconfig build at 20 acts/sec
would consume hours to add nothing to what is already known.

**The next act is the per-act BREAKDOWN at the largest store**, which is ADDENDUM
L's decomposition repeated at roughly sixty times the store size. It requires the
extraction finished, because the channel admits one caller.

**It is a COMPARISON, so it obeys the comparison rules already filed:** the
small-store side is **RE-TAKEN, never carried**; arms interleaved where the design
permits; spread reported beside every central value.

**If the append dominates, decompose the append itself** — open, write,
`fdatasync`, blob write — because "the append grew" is a location and not yet a
cause.

---

## ADDENDUM O — ADDENDUM L HOLDS AT 371,856 RECORDS; K3's second half STANDS; and the one genuine scaling item is a 126 ms `readdir` (2026-07-30, superseding the withdrawn ADDENDUM N)

Appended per the paper standard's afterlife rule. **Law, and it supersedes
ADDENDUM N in full.**

### O.1 — The decomposition, at a store 120× larger than L's

At **371,856 records**, per-act, direct decomposition:

| | FILE-OPEN | FILE-WRITE | FILE-CLOSE |
|---|---|---|---|
| whole act | 3.611 ms | 3.732 ms | 3.257 ms |
| **durable append** | **3.275 ms · 90.7%** | **3.287 ms · 88.1%** | **2.991 ms · 91.8%** |
| `covers` (the authority fold) | 0.046 ms · 1.3% | 0.050 ms · 1.3% | 0.000 ms |
| all three memo folds together | 0.020 ms | 0.025 ms | 0.019 ms |
| the bridge's own arithmetic | **0.014 ms · 0.4%** | | |

**L measured 2.6–3.5 ms with the append at 71–85% on ~3,000 records. At 371,856
records the act is 3.2–3.7 ms and the append is 88–92%.**

**THE ACT IS FLAT.** Across a **120×** store growth the whole act moved from a
2.6–3.5 ms band to a 3.2–3.7 ms band. **K3's second half STANDS as MET** and
ADDENDUM D's declaration was correct, including at a store size D never reached.

**And L's headline is STRONGER at scale rather than weaker.** The append's share
ROSE — not because the append got expensive, but because everything around it got
cheaper (EP-28B's W3). Every per-act fold together is now under 2%, consistent with
ADDENDUM M's 1.4%. **The speed tension is durability and not governance, more
plainly at 371k records than it was at 3k.**

### O.2 — What ADDENDUM N actually measured, and the unit error underneath it

N ruled on **throughput during a `tar` extraction** — 124.6 records/sec falling to
20/sec as the store grew 47k→227k — restated as per-act cost. **The decline is real
and the act is flat, so the extraction spent its time somewhere other than governed
acts.** Two live candidates, neither chased: single-threaded `xz` decompression and
the run's own poller, on a **2 vCPU** guest, against the brain.

**The pack labelled the limitation in its own deviations — "the curve is throughput
rather than sampled act cost" — and this seat ruled in a unit the evidence did not
carry.** The cap was present, correct, and read past.

### O.3 — The one genuine open item: `readdir` on an EMPTY directory costs 126.783 ms

Port-level, at 370,907 records, spreads in brackets:

| operation | cost | records | crossings |
|---|---|---|---|
| `stat` (CACHE-only) | 0.003 ms [0.003–0.011] | +0.0 | +0.0 |
| `open` alone | 2.470 ms [1.748–4.171] | +1.0 | +1.0 |
| `close` alone | 2.707 ms [1.813–4.202] | +1.0 | +1.0 |
| `open`+`read`+`close` | 6.991 ms [4.349–9.342] | +2.0 | +2.0 |
| `create`+`write`+`close` | 29.583 ms [26.704–52.524] | +4.0 | +5.0 |
| **`readdir` on an EMPTY directory** | **126.783 ms** [119.966–150.865] | | 2.0 |

**An order of magnitude above every other row, for an operation that should be
nearly free.** It appends nothing, so it is a FILL — **and a fill that expensive at
this store size is the only row in this campaign that still looks like something
reading more than it needs.**

**This is the shape ADDENDUM N was hunting, found in the place N was not looking:
not the write path, the READ path.** ADDENDUM C's class — a fold reading more than
its subset — was closed for the per-act authority path and for the memos. **It was
never established for `readdir`.**

**RULED: this is the campaign's live scaling question, and it is attribution work,
not redesign.** It is one row, it is reproducible, and it has a spread.

### O.4 — The honest cap on O.1 itself, which this seat owes its own rule

**The small-store side of this comparison is CARRIED from ADDENDUM L, not
re-taken**, against the rule filed two days ago that a comparison re-takes its prior
side. The conclusion is very probably safe — the difference is large and points
away from a problem — **but the rule exists so that the question is not decided by
whether the reviewer likes the answer.** Closing it is cheap: found a fresh world at
~3,000 records and decompose it with the same tool in the same session. **Directed,
and O.1 carries this cap until it is done.**

### O.5 — Two instrument facts recorded rather than relayed as findings

**`w8-speed.py` prints a derived sentence that is internally inconsistent** — "the
channel round trip is 63.391 ms, so the crossing is 1813.4% of a header", where a
63 ms round trip cannot yield a 6.991 ms two-crossing header. The 1813% is the full
126.783 ms divided by the header, mislabelled as the crossing. **The measured rows
stand; the derived sentence does not**, and the separation is the right one: a
derived figure inside an instrument is a carried figure with extra steps.

**The lab's 2 vCPUs are now a known confound for any THROUGHPUT measurement here**
and must be stated as a scale assumption in any authoring that plans one. Per-act
decomposition is unaffected.

### O.6 — 85 files unexplained

The mount holds **91,106** files against **91,191** file members in the tarball. Not
chased. **A governed filesystem that received 91,191 files and holds 91,106 is a
custody question rather than a rounding error**, and the likeliest explanation is
already on the record: the stance-4 capability debt (close item 27) includes
`mknod`/FIFO and the special-file classes, so files the mount could not create would
be exactly this shape. **Directed as a check, not accepted as an explanation.**

---

## ADDENDUM P — [VARIABLE CORRECTED by ADDENDUM Q, same day: it is NAMESPACE-proportional, not store-proportional] `readdir` is store-proportional, and K3 guards the governed act while nothing guards the fill (2026-07-30)

> **[CORRECTED 2026-07-30 by ADDENDUM Q.] The DEFECT is real and the ATTRIBUTION
> was confounded.** Both arms below were taken in worlds where every record minted
> a name — 372,305 records against 91,347 names, 3,926 against 863 — so store and
> namespace moved together and a two-arm design could not separate them. **A third
> world with 300,206 records and 207 names lists an empty directory in 0.083 ms:
> ninety-nine times the history of the small arm, twelve times cheaper.** The cost
> tracks the NAMESPACE. §P.3's gap is real and its proposed invariant names the
> wrong variable. Text retained; read with ADDENDUM Q.

Appended per the paper standard's afterlife rule. **Law.**

### P.1 — The attribution, and it is decisive

Two arms, same probe, same session, 15 reps per row, spreads reported:

| store | `readdir` on an EMPTY directory | per round trip |
|---|---|---|
| **3,001 records** | **1.377 ms** [1.322–2.057] | 0.415 ms |
| **371,856 records** | **132.591 ms** [127.305–202.525] | ~65 ms |

**Store grew 124×; cost grew 96×.** Near-linear in total store size.

**And FLAT in directory size at both arms** — marginal cost per entry −0.0022 ms at
3k and −0.0367 ms at 371k, zero within noise, with 0 / 1 / 10 / 100-entry
directories indistinguishable at either store size.

**So `readdir` reads the whole record to answer a directory listing, and the
directory it is asked about does not matter.**

**The competing hypothesis is dead by measurement rather than by argument.** A
fixed delay — a poll interval, a timeout — would cost the same at both stores. It
costs 1.377 ms at 3k. **It is work, not a constant.**

**`stat` does not share it**: 0.003 ms and zero crossings at 371k. This is one row,
reproducible, with a spread.

### P.2 — It explains the withdrawn ADDENDUM N's observation without rescuing its conclusion

**N saw something real and put it in the wrong place.** Throughput fell during the
extraction — that was true. **The act is flat — that is also true.** Both hold
because **every `create` resolves a path, and path resolution on this filesystem
pays a store-proportional read.**

So the correction to N is not "nothing was happening." It is **"something was
happening, in a different place, and it is a FILL rather than a governed act."**
The run's own poller made it worse; the read path is why it fell at all.

### P.3 — The definitive: K3 guards the ACT and nothing guards the FILL

**This is the finding under the finding and it is a hole in the invariant set.**

K3 says **a gated act does not get slower as the system records more**, and it
holds — measured flat across 95× at item 36. ADDENDUM C's structural guard fires
when a new whole-record fold lands on **the per-act path**. **`readdir` is not a
governed act. It is a fill. It is outside both by construction.**

**And `design/22`'s speed argument was never a claim about this.** §3 says the hot
path is pure S — a fill that records NOTHING. **That is a claim about RECORD RATE.
It was never a claim about FILL COST**, and the two have been read together as one
guarantee for two campaigns.

**Stated as the gap: a system whose governed acts are flat and whose fills are
store-proportional does not scale, and every invariant on the books would report
green while it failed.** The record rate stays bounded by governance exactly as
`design/22` promises; the machine still slows to a stop.

**PROPOSED — K3's sibling, and it is the owner's to number:** *a FILL does not get
slower as the system records more.* With ADDENDUM C's guard extended from the
per-act path to **every path that reads the record**. **Cost if wrong:** the
guard's blast radius grows and some legitimately store-proportional read (a
whole-record report, an audit sweep) has to be declared rather than discovered —
which is the same declared-exception shape ADDENDUM C already uses, and cheap.

### P.4 — Item 36: ADDENDUM L HOLDS, both arms TAKEN in one session

| | 3,926 records | 371,856 records |
|---|---|---|
| FILE-OPEN, whole act | 2.177 ms [1.833–2.890] | 3.611 ms [2.403–5.246] |
| — durable append | 1.821 ms · **83.7%** | 3.275 ms · **90.7%** |
| — covers (authority fold) | 0.060 ms · 2.8% | 0.046 ms · **1.3%** |
| FILE-WRITE, durable append | 2.305 ms · 89.5% | 3.287 ms · 88.1% |
| FILE-CLOSE, durable append | 3.669 ms · 90.7% | 2.991 ms · 91.8% |

**Across 95× the act stays in the same band. K3's second half STANDS. L's headline
is stronger at scale**, and the mechanism is now visible: the append's share rises
because everything around it got cheaper, not because the append got expensive.
**The authority fold SHRINKS as a share, 2.8% → 1.3%.**

**ADDENDUM O §O.4's carried-arm cap is DISCHARGED** — both arms taken with the same
tool in one session, nothing quoted from the ledger.

**One reading declined, by this document's own rule.** FILE-CLOSE is nominally
faster at the large store (4.044 → 3.257 ms), and the small-store spread is
[1.836–8.737]. **A difference smaller than one arm's spread is not a difference**,
so it is recorded and not interpreted.

### P.5 — The instrument's derived sentence, now fully explained

`w8-speed.py` prints a coherent round trip at 3k (0.415 ms, crossing 9.7% of a
header) and nonsense at 371k (63.391 ms, crossing 1813.4%). **The tool derives its
round trip FROM the `readdir` row**, so the moment `readdir` became
store-proportional the derived figure became nonsense while every measured row
stayed sound.

**The tool is not broken. It is correct code whose input stopped being what it
assumed.** Filed with it: **a derived figure inherits every defect of its inputs
and announces none of them, so an instrument that derives states what it derived
FROM.**

---

## ADDENDUM Q — the variable is the NAMESPACE, not the store; and the invariant P proposed would be GREEN over the defect it was written for (2026-07-30, at EP-28E's W1)

Appended per the paper standard's afterlife rule. **Law, and it corrects ADDENDUM
P in the one place that matters.**

### Q.1 — The line, and the third world that separates the variables

**Instrument: `planning/vm/lab/readdir-probe.py`** — committed 2026-07-31 under §A35.
It took every `readdir` figure in ADDENDA P and Q. Run as
`python3 readdir-probe.py <mount> <record.jsonl> [reps]` against a raised mount.
**Its own header records that it could not separate store from namespace, because
both guest worlds mint a name per record — which is the confound EP-28E's W1 broke
with a third world.**


`CustodyState.children()`, `src/bridge/custody.py:312`, iterates `self.names` — the
whole namespace — and filters by parent. **It touches no records at all.** Three
siblings share the class: `path_of` (:306), `nlink` (:293), `snapshot` (:331).

| world | store | namespace | listing an EMPTY directory |
|---|---|---|---|
| A | 3,031 | 3,032 | 0.977 ms |
| B | 371,001 | 96,002 | 32.306 ms |
| **C** | **300,206** | **207** | **0.083 ms** |

**World C has ninety-nine times world A's history and lists twelve times cheaper.**
Cost tracks the namespace at 31.7× against 33.1×. **It does not track the store.**

### Q.2 — Why ADDENDUM P got it wrong, and it is a design fault rather than a reading fault

**In the defconfig world every record minted a name.** 372,305 records against
91,347 names; 3,926 against 863. **Store and namespace were COLLINEAR across both
arms**, so no measurement taken on those two worlds could separate them — and both
seats reported the attribution as established, one calling it decisive.

**The builder built the third world neither seat did.** That is the whole
correction: not a sharper reading of the same data, a **third arm that breaks the
collinearity.**

**Filed as method:** a two-arm comparison cannot separate two variables that move
together, and an arm-set states which variables it holds constant and shows they
actually differ. Full rule at `BUILD-PROMPT-STANDARD`.

### Q.3 — P's proposed invariant is SATISFIED BY THE DEFECT, and so is the guard P asked for

**This is the sharpest finding in the pack and it is a defect in the law, not in
the code.**

**The guard.** ADDENDUM C's guard watches for code that reads the whole HISTORY. **A
directory listing never reads the history.** So extending it "to every path that
reads the record" — ADDENDUM P's words, and EP-28E's W3 as this seat lowered it —
**passes at any width over a namespace-proportional read.** Widening it as written
would ship a green light over a measured red, inside the EP that found the red.

**The invariant.** *A fill does not get slower as the system records more* is
**satisfied by world C while the defect stands.** World C has 300,206 records and
lists in 0.083 ms. And world C's shape — many records, few names — **is how anyone
cheaply builds a big test store**, so the invariant would be tested in precisely
the regime where it cannot fail.

### Q.4 — The corrected formulation: name the DEPENDENCY, never a variable

**A threshold invariant names a variable and inherits every variable it did not
name.** The estate's own shape does better and ADDENDUM C already had it: *the read
consults only the records its answer depends on.*

**PROPOSED, replacing P.3's wording, and still the owner's to number:**

> **A derived answer costs its own dependencies.** Producing it consults only the
> state that answer depends on, and its cost is bounded by that state rather than
> by anything the answer does not read.

**Listing a one-entry directory costs one entry.** Not 96,002, and not 207.

**Why this form and not the other.** It is variable-free, so it does not go stale
when a new unbounded quantity appears. **It is already the shape of the estate's
own test** — the marginal-cost-per-entry measurement that showed `readdir` flat in
directory size is exactly the check this invariant demands, and it is the
measurement that exposed the defect. And **the guard follows from it directly**:
watch for a read whose cost is unbounded in something its answer does not depend
on.

### Q.5 — A namespace scan is ALREADY on the per-act path, and K3 is NOT reopened on it

The builder reports `_posix_precondition` carrying a namespace scan **on the gate's
per-act path**, which ADDENDUM C's guard cannot see.

**This seat will not rule on it.** Twice this week a verdict has run ahead of a
measurement, and the correct act is the third arm rather than a third swing.

**What is on the record and unexplained:** ADDENDUM P.4 measured FILE-OPEN at 2.177
ms in a world of 863 names and 3.611 ms in a world of 96,002. **This seat read that
1.66× rise as one band and did not ask what it was.** If a namespace scan sits on
the per-act path, that rise is a candidate for it.

**The measurement that answers it is cheap and the world already exists.**
Decompose the act in **world C** (300,206 records, 207 names) and compare against
world B (371,001 records, 96,002 names). **Same store size, namespace 460× apart.**
If the act is cheaper in C, the per-act path carries a namespace term and K3's
second half is a live question again — this time from a variable nobody has
measured rather than from a curve nobody decomposed.

---

## ADDENDUM R — the hand-list root has now appeared at EVERY layer the campaign has; and the per-act namespace question is CLOSED by a countable (2026-07-31, at EP-28E's W2/W3/W4)

Appended per the paper standard's afterlife rule. **Law.**

### R.1 — The per-act namespace question is CLOSED, by a count rather than a duration

W4, same store size, namespace **460× apart**:

| act | world C (207 names) | world B (96,002 names) |
|---|---|---|
| FILE-OPEN | **0 steps** · 1.478 ms [1.316–1.779] | **0 steps** · 1.537 ms [1.416–1.771] |
| FILE-WRITE | **0 steps** · 1.526 ms | **0 steps** · 1.516 ms |
| FILE-CLOSE | **0 steps** · 1.623 ms | **0 steps** · 1.336 ms |

**ZERO namespace steps in both arms.** The per-act path carries no namespace term.
EP-28E's raised item 5 is **closed by evidence rather than by inference**, and its
red world planted the REAL scanning `children` on FILE-OPEN's genuine precondition
branch rather than a synthetic scan.

**A count of zero is scale-independent, which is why it is the answer and the
milliseconds are not.** The manager declined to conclude from the durations on the
ground that its last two readings of this question were both wrong in the same
direction and the spreads overlap. **That refusal is the right one and is ratified.**

**One thing stays unexplained and small, named rather than chased.** ADDENDUM P.4's
1.66× rise in FILE-OPEN between the 863-name and 96,002-name worlds is now known
NOT to be the namespace. It sits inside overlapping spreads across worlds differing
in store, namespace and workload shape at once. **It is recorded as unexplained and
is not worth an arm while it is inside the spread.**

### R.2 — The hazard found while landing the fix, and it is worse than the defect the EP was sent for

`shadow_diff` compared two snapshots for equality and then built its readable
difference **from a HAND-LIST of keys.** The snapshot had since grown two keys, so
a divergence in either would make equality false, produce an **empty** difference
list, and `_shadow_check`'s `if diff:` would **not halt the mount.**

**A divergence DETECTED, NOT REPORTED, with the counter recording that a check
ran.** That is the campaign's own safety net under the entire derived-state claim,
in a mode where it is silent about the one thing it exists to say.

**Fixed by reading rather than by hand:** `records_fs.py:859` now iterates
`sorted(set(served) | set(replayed))`, and the unequal-but-no-difference case
returns a **stated message** rather than a falsy list. Regression rows corrupt each
index and require both a named difference and a halt.

**OPEN, and it decides whether anything historical is affected — one question, cheap
to answer: was the hand-list COMPLETE against the pre-W2 snapshot?** If it was, the
gap opened when W2 added `kids` and `paths` and was closed in the same session by
the seat that opened it, and nothing before this EP is in doubt. **If it was not,
every shadow-diff green since the list went stale is uncertain.** Directed at
EP-28E's W5 and it is a read, not a run.

### R.2a — ANSWERED, 2026-07-31: the hand-list was COMPLETE, and nothing historical is in doubt

W5d enumerated **fifteen commits from git**, reading each one's `snapshot()` key set
and `shadow_diff` body **from the syntax tree** rather than from the file's text.
**The list and the key set were the same two names at every commit.** The snapshot
grew `kids` and `paths` and the hand-list was replaced by a read **in the same
commit** — `db58866` → `0d3a2e2`, two minutes apart.

**So the hazard never existed outside one commit, and every shadow-diff green
before this EP stands.**

**A milder one-commit gap is named rather than buried, and the distinction is the
builder's:** across that window the indexes were **outside the compared shape
entirely**, so a divergence there was **NOT DETECTED** rather than
detected-and-unreported. **Those are different failures and the second is far
worse** — a coverage gap is an instrument that does not look, and
detected-and-unreported is an instrument that looks and lies.

**Cap, stated: git's commit granularity is about two minutes**, which is the same
order as the window itself. The finding is that the gap did not span a commit
boundary, not that it lasted zero seconds.

### R.2b — the same root AGAIN, in a measurement entry, and closed MECHANICALLY for the first time

`MEASUREMENTS` entry 11c states `nlink` has exactly one call site. **It has two** —
the second is `replay_snapshot.py:106`, the conformance harness's **replay leg**,
once per node of the tree it replays. A hand-counted caller list is R.3's root in
its plainest form.

**What is new is the fix.** Corrected as a fresh entry rather than an edit, **and
mechanised: the covered-caller set must equal what an AST WALK of `src/` finds.**
**That is the first time this root has been closed by machinery rather than by
someone being careful**, and it is the shape every other instance wants.

### R.3 — One root, now at every layer, and that is the finding rather than the count

**A check whose subject is CONSTRUCTED rather than READ from the thing being
compared has now appeared:**

- **in a seat** — the manager's `find`-built paths, its stripped prefix, its
  `parent_to_children` grep against maps named `kids` and `paths`, and its two-arm
  design whose worlds happened to satisfy the assumption it was testing;
- **in this seat** — a throughput curve restated as per-act cost, a confounded
  attribution called decisive, a fence whose prose contradicted its enumeration,
  and §1.5 asserting world C was in the guest when it is not;
- **in an instrument** — `shadow_diff`'s hand-list, and W1's `path_of` probe
  pointed at the wrong inode;
- **in the PRODUCT** — the same hand-list, shipping in `records_fs.py`;
- **in a test's own reference arm** — `_scanning_children` and `_scanning_path_of`
  exist; **`_scanning_nlink` does not**, so landing `nlink` on the present
  differential would ship a proof that looks present and is absent;
- **and in a `src/` docstring** — the builder's unreachability claim, refuted by
  its own differential at record 255, having already shipped as source prose.

**It is not a code shape. It is a shape a mind makes**, which is why it appears
wherever anything writes a check and why no single mechanism catches it. **The one
countermeasure that has worked every time is the same: establish the subject from
the thing itself rather than from a list of what you believe is in it.**

**And the campaign's own detector has been consistent: a result that reads too
cleanly.** An empty diff. A clean monotonic curve. An `ABSENT` with no partial
matches. A grep returning zero.

---

## ADDENDUM S — K12 is SEEDED, and A.4's anchor guard is RULED YES (2026-07-31, OWNER-RULED)

Appended per the paper standard's afterlife rule. **Law.**

### S.1 — K12, the twelfth end-state invariant

> **K12 — A derived answer costs its own dependencies.** Producing it consults only
> the state that answer depends on, and its cost is bounded by that state rather
> than by anything the answer does not read.

**Plain form, which is how the owner ruled it: when the system answers a question it
looks only at the things that answer depends on.** Listing a directory with one file
in it costs one file's worth of work — not the whole namespace, and not the whole
record.

**It is seeded on measured evidence rather than on intention.** Listing an EMPTY
directory cost **132.591 ms** at 371,856 records because it scanned all 96,002
names; after EP-28E it examines **one entry at 96,005 names**, and a directory
`stat` fell from **32.948 ms to 0.002 ms and from 192,007 entries to 2**.

**Why the DEPENDENCY and not a variable, which is the whole of why the earlier
wording was replaced.** ADDENDUM P proposed *a fill does not get slower as the
system records more* — **and that is satisfied by a world with 300,206 records that
lists in 0.083 ms while the defect stands**, because the cost tracked the namespace
rather than the store. **A threshold invariant inherits every variable it did not
name.** K12 names none, so it cannot go stale when a new unbounded quantity appears.

**Acceptance shape:** the marginal cost per unit of the answer's own dependency,
asserted as a COUNTABLE. **Currently no declared exception anywhere in the fold**,
which is the state it is seeded in. A legitimately unbounded read — a whole-record
report, an audit sweep — is DECLARED in ADDENDUM C's shape and never discovered.
**Guard: `test_ep28e_w3.py`'s `COST_IS_ITS_DEPENDENCY`**, which watches for a read
whose cost is unbounded in something its answer does not depend on, with a control
proving the guard can fail.

**K12 joins K1–K11 as an end-state invariant of campaign 3 and binds every remaining
subsystem: EP-29's devices, EP-30's comms, EP-31's memory, EP-32's scheduling.**
Each authoring names how its read paths satisfy it.

### S.2 — ADDENDUM A.4's anchor guard: RULED YES

**§4b.7's trigger stops matching three KINDS of target and becomes the computed
test the anchor law already carries.**

**Plain form: when the system reverses a past decision, it must not leave anybody's
chain of authority without a root.** The old trigger checked whether the reversal
targeted one of three named situations — a handover, a succession, a root grant.
**The new one asks the actual question: after this, is anyone still in charge?**

**Before the sweep appends, and again on the sweep's cumulative result**, the guard
asks whether the post-exclusion record leaves any chain without a root or moves a
root — **and refuses and routes to the owner if it does.**

**Why the list was wrong and the computed test is right, in the estate's own shape:
power is scope-and-target, never a verb list.** A trigger written as three named
kinds is a verb list wearing different clothes, and **a fourth situation nobody
listed passes straight through.** This is the same correction the power model already
made to an earlier act-list, and it is **charter §A26's class filed before §A26
existed** — a law derived correctly, then lowered one notch too concretely.

**Accepted with its stated cost: the guard now refuses MORE sweeps than the
three-kind form**, each refusal routed to the owner with the chain it would have
ended. **A sweep that would have been lawful stops and waits.** That is the correct
direction — the alternative is a sweep ending a chain without the guard seeing it.

**A.4's separate observation is ADOPTED as the right reading rather than left to
inference:** §4b.5 calls the sweep an ordinary governed act of SYSTEM, so it crosses
the gate and meets every standing check **including the protected-core floor and the
conservation law.** EP-26 states it rather than implying it, because a system act
above the protected core would gap a shield.

**Open since 2026-07-26 — the oldest item on the board — and closed here.**

---

## ADDENDUM T — the lever's baseline is NAMED: concurrency alone collects most of what batching was projected to collect (2026-08-04, the architect seat on the mentor's ruling at the W4e-era measurements)

Appended per the paper standard's afterlife rule. **Law, and read as part of
ADDENDUM L beside ADDENDA M and O.**

**The measurement** (conditions in the pack entry on the log, which controls
over any summary): the barrier cost per record fell **1.152×** between the
compared arms — **inside width 1's spread, so NOT a difference** by the
standing comparison rule. At **32 concurrent publishers, a width-1 barrier
costs 0.1127 ms per record against 1.2935 ms single-threaded.**

**What this does and does not move — the preserve-don't-smooth split:**

- **ADDENDUM L's headline STANDS untouched:** the speed tension is
  durability, not governance, and the sync is what makes the record exist.
- **The 5.6×/13.5× band is NOT refuted — its BASELINE is now named:** those
  factors were measured against a ONE-CALLER floor, and the width-1 arm at
  32 publishers is not that floor. **Concurrency alone — many submitters
  each paying their own barrier, overlapped — collects most of what
  batching was projected to collect.** Every future citation of the band
  carries the baseline with it, exactly as §L.5 made every citation of the
  floor carry the substrate.
- **The honest consequence for this EP's own justification, stated rather
  than softened:** EP-28C exists because group commit was "the only lever
  past the floor." **The lever was largely concurrency.** Batching's
  residual value above concurrent width-1 is what W7's contended arms
  measure when the channel opens — measured against the RIGHT baseline for
  the first time, which is what this addendum exists to make possible.

**The general rule this carries, the third of its family:** a projected
gain names the baseline it was projected against, or the gain silently
absorbs whatever else changed between then and now — the carried-figure
rule (TAKEN or CARRIED) applied to PROJECTIONS.

**[CITATION ADDED 2026-08-04, mentor-directed — the finding has a test
already saying it:** `test_ep28c_w8.py:175` — intermittent, three
isolated runs 10 OK, widest observed batch 7/6/7 against a cap of 16 —
whose own failure message reads **"the arrival rate closes the batch, not
the cap."** Direct evidence for this addendum's finding, sitting in the
suite as a raise before the finding was ruled: the batch never fills
because concurrent arrivals drain continuously, which is concurrency
collecting the gain ahead of batching, observed at the row level.]**

---

**[AS-BUILT, 2026-09-03, the architect's hand — THE CAMPAIGN'S CLOSE ROW,
and the last as-built this paper will receive:** CAMPAIGN 3 IS CLOSED —
acknowledged by the owner first-party, his words verbatim at board :2746
and in `planning/exec/DIGEST-C3.md`'s acknowledgement block ("and btw yes
c3 acknowledged by me, thanks"), under CLOSE-ACT-LAW :2745, which this
close's own final week produced: the close act is an acknowledgement
(testimony + outer-assignment + computed readiness), never a content
approval, and work never queues behind it — C4 was building (EP-34
dispatched) when the acknowledgement landed. The close's figures of
record: whole ledger 3,311/0 deterministic (digest :2738); K1-K11 held
through two independent passes; K12 MET AT ITS TEXT'S SUBSYSTEM SCOPE by
corrected census after THREE limbs found by the cold-independence form
(:2715 views, ceiling fold, :2735+ subsystem views) — the kernel-layer
same-shape folds ride to C4 as named residue. Item 49's ratio moved
visibly: every close-week defect was instrument-found. Residue and the
owner's open batch: the digest carries both. The successor campaign is
design/37 (ACTIVE via `planning/exec/C4-LAUNCH-REPRICING-DRAFT.md`,
board :2739); the acceptance model is design/45. This paper is now
HISTORY IN THE GOOD SENSE: cite its law through the digest, not its
front matter, which carries dated takings of a running campaign that is
no longer running.]**
