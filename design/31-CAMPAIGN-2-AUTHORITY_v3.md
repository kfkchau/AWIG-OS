<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Campaign 2: AUTHORITY (the upward half — who, where, how far) — plain-register edition

Plain-register edition, in place (the framed original is retained at `tests/archive/31-CAMPAIGN-2-AUTHORITY.md` and in git history) [banner amended 2026-07-24]: same target state and the same §9
review record, with neutral method language (stress-checks and review passes rather than
"adversarial probes"; unprivileged-caller cases rather than "the hostile nobody").

**Status:** v1 DRAFT, 2026-07-17, mentor session, tier xhigh. The target-state paper for the
campaign AFTER the host-spine campaign (design/28, EP-01..13). SOURCE-DERIVED from the owner's
rulings (three tiers; conservation; the power model + protected core, design/30; the flow
ruling 2026-07-17: store broadcasts DOWN through masters, views cross-check sideways and
cascade down, acts travel UP through parent gates, each hop verified against its local view)
and the corpus (venn2-foundational §§07–09: actor authority derived from records; the boot
pack; ogs-kernel: "rules have scope" is a KERNEL item). Owner rulings control. §8 is the
forward roadmap beyond this campaign.

**Sequencing (owner-accepted default):** starts after EP-13 (the host-spine campaign review)
so it builds from a reviewed, closed base. Every EP number continues the estate sequence.

---

## 0. What this campaign is (one paragraph, functional)

Campaign 1 built the DOWNWARD half and the single wall: one record, one door, computed views,
a constitution that protects its own mechanics. Campaign 2 builds the UPWARD half: **who is
acting (verified, not claimed), where they are acting (spaces), how far their power reaches
(grants), and the chain of local checks an act climbs before it ever reaches the door.** At
its end, a person works against their own loaded power view; an act beyond their reach stops
at their fingertips, locally, before it travels; the gate confirms at the door instead of
standing alone; and four laws that have waited as recorded-law-with-deferred-machinery come
alive. The unprivileged-caller cases of campaign 1 become structurally impossible — not
because the wall got thicker, but because the building finally has floors.

## 1. End-state invariants (the campaign is done when ALL hold)

- **J1 Identity is verified, not claimed — and verification bottoms out at the founding.**
  An actor is an ACCOUNT: a recorded founding of identity plus recorded verification evidence.
  An act carries who-the-system-verified, not who-the-caller-typed; the caller-asserted actor
  string — campaign 1's honest cap — is retired at the gate. **The root identity (owner/SYSTEM)
  is founding-asserted, NOT system-verified** — there is nothing above the root to verify it
  against, exactly as constitutional law is founding-only and legitimacy bottoms out at
  collective formation (corpus §1.1). This is not a hole to plug; it is the same
  self-aware-limitation shape the estate already runs on — stated, not hidden. Verified means
  verified-against-a-recorded-anchor; the anchor itself is the founding.
- **J2 Everything lives in a space, and the tree is containment.** The mother space grows
  into the space TREE (corpus §1.4): every info item, rule, vocabulary, and view belongs to
  a space; every new space nests under a parent. Space membership is data on the record,
  never a folder convention. **Reach over a space includes its subspaces** (nesting IS
  containment — the root's reach covers everything, which is what makes the owner's
  authority coherent), and **every space's authority chain terminates at the root** — a
  space whose grants are all revoked is not orphaned governance: the parent's reach still
  covers it (the corpus's no-circular-authority and no-orphan items, extended from actors
  to territory).
- **J3 Power is the positive grant, enforced — ALL FOUR DIMENSIONS.** design/30 §1 goes
  live: the co-happening grant `(+) actor(verified) × actions × INFO TYPE AND CONTENT ×
  their space` is a RECORD — the owner's exact form, all four dimensions load-bearing. The
  info-type dimension is what makes "a local user removes rule-writing power from users in
  that space" a GRANT operation, not a special case: a rule is info of kind law; granting or
  revoking the law-kind is how rule-writing power moves, with no rule-specific machinery.
  The negative space is COMPUTED (never stored); ROOT-NEG-1 (no chain → no act) and
  ROOT-NEG-3 (no authority → no write) flip from deferred to live as the computed complement
  of the grant set. **Authority is a CHAIN EVALUATED LIVE at every check** (corpus §07:
  actor → role → grant → active → authorised-creator → condition), so revocation is instant
  everywhere downstream — nothing cascades because nothing was stored. Default-deny stops
  being a sentence.
- **J4 The power view rides every IN-KERNEL hop; the gate is the kernel-testable floor.**
  Each actor has a derived POWER VIEW (the hardened local profile): what they may do, where,
  on what — computed from grants. The KERNEL guarantee (testable, this campaign): the gate
  enforces it as the final authority, and every in-kernel hop that answers early (the
  parent-view checks) is COHERENT with the record or refuses to answer — the R26 law applied
  to authority, a hop never lies. The EDGE hop (the client on a user's machine, §7) consumes
  the same power view but is a composition-layer promise, NOT a kernel invariant — named so it
  is not mistaken for something this campaign proves. Same question, every hop, one source; no
  hop writes.
- **J5 Law carries scope, and the heuristic retires only when strictly stronger.** Every law
  record names the space it binds (kernel item: "rules have scope" — ogs-kernel-complete). The
  protected-core floor retires its all-space/targeted HEURISTIC for the real test: a rule whose
  scope exceeds its author's reach refuses at the author's own hop; a rule reaching the
  system's vital organs refuses for everyone (the fifth constitutional law's machinery
  completes). **The swap is gap-free by construction (the conservation lesson applied to
  enforcement transitions): the scope+target test must be proven STRICTLY-STRONGER-OR-EQUAL to
  the heuristic on the whole campaign-1 protected-core ledger BEFORE the heuristic is removed —
  never a naked swap that could open a window weaker than what it replaced.**
- **J6 Vocabulary scope is live.** PACK-SCOPE flips deferred→live: rewriting a vocabulary
  requires reach over its space; READING one is sight — per-actor filtered views (the first
  sight-filtered read surface, P6 extended from action to knowledge).
- **J7 Authority is anchored, succession is human.** CONST-AUTHORITY-ANCHORED flips
  deferred→live: the owner cannot remove their own authority without a recorded, verified
  HUMAN successor; no authority chain ever orphans; no root transfer to a pure-agentic
  actor. The corpus's remaining §08 items (circular authority, authority loops) close here.
- **J8 Secrets verify, never reveal.** CONST-SECRETS flips deferred→live via the vault:
  the record proves a secret was used; no actor, owner included, reads the value.
- **J9 The founding is a document.** Genesis becomes the corpus's own boot step 1: a
  FOUNDING PACK (data — the nineteen laws in full form WITH scope, the vocabularies, the
  actors/tunnel/space, the core ops, the masters) executed by a minimal installer.
  Constitutional evolution = visible pack versions; the founding's law-in-code exception
  closes; "adding supreme law means a new founding" becomes a mechanical fact.
- **J10 Campaign-1 guarantees survive intact.** Every host-spine invariant (I1–I11) and
  every conservation/protected-core protection holds under the new machinery — proven by
  re-running campaign 1's full test ledger as an authorized/unauthorized matrix (§6).

## 2. New record kinds (all in the ONE stream, class-tagged; envelope unchanged — I1 holds)

| payload.kind | Class | What it founds |
|---|---|---|
| account | LAW | an identity: founding + verification evidence refs |
| verification | INPUT/DECISION | evidence an account passed an identity check (vault-backed) |
| space | LAW | a node in the space tree (parent ref; the mother space is genesis) |
| role | LAW | a named bundle of grantable power |
| grant / revoke (widened) | DECISION | the co-happening (+): actor × actions × info × space; revoke supersedes |
| succession | LAW | the recorded human successor (J7's anchor) |
| scope (field, not kind) | — | every law record names the space it binds (J5) |

## 3. The hop model (J4, lowered — how an act travels)

1. **Edge check (local):** the client/driver holds the actor's power view (derived, cached
   with staleness metadata like every view). An act outside it is answered locally —
   recorded ONLY if the actor insists (an over-the-edge attempt is itself governance-grade:
   a refused act, recorded at the gate as today). The edge check is UX + containment; it is
   never the authority.
2. **Parent-view checks (the climb):** an act addressed to a space is checked against that
   space's view of the actor's reach as it routes — sideways cross-checks (contradiction,
   dual-audit) unchanged.
3. **The gate (the door):** final verification against the record itself — chain (J3),
   scope (J5), tier/conservation/protected-core (campaign 1, unchanged). The gate remains the
   SOLE appender. Nothing in the hop model writes; hops only answer early.

Design rule carried from campaign 1: **enforcement lives at the chokepoint; hops are
accelerations of the same derived answer, never sources of truth** — the standing-push
lesson (R26) applied to authority: a hop's cached power view must be coherent with the
record or refuse to answer.

## 4. Execution plans (each gets its own EP file at campaign start; sizes/tiers stated)

- **EP-14 — The founding installer (J9).** The pack as data + the installer; scope fields
  enter every law here (the ground J5 stands on); differential oracle old-genesis vs
  pack-genesis, zero divergence. M, high (known shape; the oracle is the proof).
- **EP-15 — Accounts + verification (J1).** Account/verification records; the gate resolves
  the acting account; the caller-asserted actor retires. **Attribution splits from acting
  authority** (the stamp_actor lesson made structural): a record carries WHO INVOKED (the
  verified account, in provenance) separately from AS-WHOM-IT-ACTED (the actor field a
  handler may lawfully set to SYSTEM — write-activity, the executor, the mirror). Today both
  collapse into one caller string; after EP-15 the invoker is always the verified account
  even when the act is SYSTEM's. The secrets VAULT SEED enters here only as far as
  verification needs it (full vault = EP-19). L, xhigh (identity is fresh derivation; a wrong
  reference makes everything above it wrong).
- **EP-16 — Spaces, roles, grants (J2, J3-data).** The space tree; role records; the
  co-happening grant. Space membership is DERIVED, never stamped (records are append-only +
  frozen — you cannot write a field onto an existing record; I1 forbids it): pre-account
  records belong to the mother space by a DEFAULT-SPACE fold, new records carry explicit
  space. The migration is a fold rule + the mandatory oracle (pre-migration answers
  unchanged), NOT a rewrite. L, xhigh (the power model's data ground).
- **EP-17 — The power view + the live chain (J3-enforcement, J4, J5, J6).** The per-actor
  power view (a COMPUTED FOLD over grant records, like every other view); ROOT-NEG-1/-3 flip
  live at the gate; scope-on-law enforced (EP-14 added the FIELD; this EP adds the CHECK);
  the protected-core heuristic retires for scope+target; PACK-SCOPE live incl. the first
  sight-filtered reads. L, **xhigh — the campaign's crux**; both failure directions on EVERY
  flip (too weak: an unprivileged caller still acts; too broad: lawful work stops working).
  **THE TRANSITION POLICY (how power goes live without wedging the world):** flipping
  default-deny onto a record full of grantless actors would refuse everything ever built.
  The transition is LAWFUL, not special-cased: the founding pack records the mother space's
  CURRENT openness as an EXPLICIT founding grant (today's open world becomes visible law —
  a grant anyone can read, and later NARROW space by space), so the flip changes where
  openness LIVES (from unstated default to recorded grant), not what works on day one.
  Tightening is then ordinary governance: narrow the founding grant, space by space, each
  narrowing a recorded act. No compatibility shim, no dual-mode gate — one law, one grant,
  visible. **THE WRONG REFERENCE THIS TIER EXISTS TO STOP — RBAC.** The template that WILL fire is
  role-based access control: a stored permission table, a user-role-permission join, a checked
  capability SET. Taking it stores a status (violates P2) and stores the negative space
  (violates design/30 §1 — the complement is COMPUTED). The right derivation: the power view is
  a fold over grant records; the check is "does an active grant whose scope covers this act
  exist," never a stored capability list; revoke supersedes, never deletes. Name RBAC, state
  what taking it erases, proceed without it — the documented estate wrong-reference, in the crux EP.
- **EP-18 — Succession + the anchor (J7).** Succession records; owner self-removal refuses
  without a verified human successor; circular-authority/loop detection. M, high.
- **EP-19 — The secrets vault (J8).** Verify-never-reveal; CONST-SECRETS live. M, high.
- **EP-20 — Campaign review (J10).** Two-pass + second-reading; the AUTHORIZATION MATRIX:
  every campaign-1 review test re-run in FOUR columns (the accounts world adds failure
  modes the old bare-string tests never had): (a) NO ACCOUNT → stops at identity, recorded;
  (b) account, NO GRANT → stops at authority, recorded; (c) account + grant IN ANOTHER SPACE
  → stops at scope, recorded; (d) account + covering grant → succeeds. Plus the full
  round-trip with accounts/spaces/grants in the record. L, xhigh (+ultracode if wanted).

## 5. What flips from deferred to live (the four waiting laws + the heuristic retirements)

ROOT-NEG-1 (EP-17) · ROOT-NEG-3 (EP-17) · PACK-SCOPE (EP-17) · CONST-AUTHORITY-ANCHORED
(EP-18) · CONST-SECRETS (EP-19). Retired heuristics: the all-space/targeted protected-core
test (→ scope+target), the caller-asserted actor (→ verified account), "everything is one
room" (→ the space tree). Every retirement is a deliberate test FLIP, already locked as
documentation tests (EP-07B B5's design).

## 6. Acceptance battery (battery-level names; each EP names its tests)

T-FOUNDING-PACK (install = old genesis, oracle-zero) · T-VERIFIED-ACTOR (a claimed name
without verification cannot act) · T-SPACE-TREE · T-GRANT-IS-POWER (grant → act passes;
no grant → stops at the hop AND the gate) · T-COMPLEMENT-COMPUTED (no stored minus anywhere)
· T-POWER-VIEW-COHERENT (a stale hop refuses to answer, never lies — the R26 law) ·
T-SCOPE-ON-LAW (out-of-reach law refuses at mint) · T-PROTECTED-CORE-EXACT (system-organ rule
refuses for owner; space-local rule-ban passes — the heuristic's over-refusal GONE) ·
T-SIGHT-FILTERED-READ · T-SUCCESSION (self-removal without successor refuses) ·
T-VERIFY-NEVER-REVEAL · T-AUTHORIZATION-MATRIX (the full campaign-1 ledger, all columns) ·
T-TOTAL-ROUNDTRIP-2 (kill everything derived; replay; identical, accounts included).

## 7. Honest caps and non-goals

- The edge check's CLIENT half (what runs on a user's machine) is composition-layer, out of
  kernel scope — the kernel provides the power view; drivers consume it.
- "Verified" is as strong as the verification evidence — v1 is recorded-evidence identity,
  not cryptographic identity; signing (the cannot-do-on-disk closure) stays campaign 4.
- Attract-class enforcement (draw acts somewhere, vs block) has no kernel expression yet —
  named as CGL surface, campaign 5's language work.
- Multi-writer ordering (S5) stays deferred — one writer, ordering fields carried.
- **The authority-fold cost is unmeasured.** The power view is a fold over grant records
  consulted at every gated act (and every hop); campaign-1 folds are full-scan +
  head-memoized, which is correct and unproven at organisational scale. Correctness is
  specified here; ACCELERATION is a calibration from real measurement (the same stance as
  the push worker's cost, design 28 §13) — never a stored table passed as an
  optimization without the check matching it (that would be RBAC through an unchecked path).

## 8. THE FORWARD ROADMAP (future campaigns, one paragraph each; numbers are sequence, not dates)

- **Campaign 3 — DEPTH (the hollow-out).** Already owner-ruled in direction: the record
  machine proven in user space takes real custody — FUSE authority beyond the flat proof,
  then the in-kernel replacement subsystem by subsystem behind unchanged interfaces (files
  → devices → comms → memory → scheduling), the syscall port at byte level, /proc. The
  campaign where gov-os stops describing a kernel and starts BEING one. (Grounded:
  design 03 §6, 10-BUILD-ROADMAP; pinned vanilla kernel ruled.)
- **Campaign 4 — PROOF (cryptographic closure).** The guarantee upgrades from
  cannot-do-lawfully/quietly to cannot-do-undetectably-on-disk: record signing and
  chaining, module signing, the GS-13 erasure protocol (the ONLY true destruction, under
  its own ceremony), succession keys. Turns the audit mirror's detection promise into
  mathematics. (Named in 28 §I11 as "signing later.")

> **Amendment (documentation-currency, EP-MAINT-C4-FINDINGS F2 — records code state, no design change).** 2026-09-08: real cryptographic signing is the KEY-MATERIAL-REAL unit (in progress); the live shape is modelled — see gate.py:171.
- **Campaign 5 — LANGUAGE (comparability without merger).** The CGL layer in full: the
  component grammars as content packs, claimed-vs-effective strength (toothless-must
  generalized), targeted/blanket × block/attract as first-class enforcement dimensions,
  translation surfaces from statute/policy prose to full-form law. The kernel learns to
  DESCRIBE other governance, not just run its own. (EP-11's verdict seed grown up.)
- **Campaign 6 — FEDERATION (many records, no merger).** S6 transport: sovereign gov-os
  instances comparing frame-carried verdicts across trust boundaries; cross-instance
  obligations; the multi-writer intake pipeline (S5, already owner-ruled on ordering)
  arriving with real concurrent writers. Comparability mandatory, executability optional.
- **Campaign 7 — METABOLISM AT SCALE (the living organisation).** The TWC userland grown
  onto the kernel: the full separation runtime (content never reviewed by its maker at
  organisational scale, the watched braking the watchers as daily practice), the
  metabolism dashboard driving actual rule retirement, sterility-debt measurement,
  obligation-driven review cycles — the 33-seat proving example re-hosted as the reference
  userland ON gov-os. The campaign where the machine runs an organisation end to end.

Each campaign gets its own target-state paper (this document's shape) before its first EP;
papers are written by the sitting mentor at xhigh and ruled by the owner. The order 3↔4 and
5↔6 may swap on the owner's word — DEPTH before PROOF is the default only because signing
benefits from knowing the final custody surfaces; LANGUAGE before FEDERATION because you
cannot federate what you cannot describe.

## 9. Self-review (mentor, 2026-07-17 — second-reading pass on this own draft)

Seven stress-checks run against the draft before the owner spends reading time on it. What
they turned up, and what changed in the paper above (recorded here, not adjusted silently):

The largest thing the first draft got wrong was leaving RBAC unnamed in the crux EP. EP-17
flips power live, and the template that fires there is role-based access control — a stored
permission table, a capability set, a user-role-permission join — which stores a status and
stores the negative space, against P2 and design/30. The draft said "computed complement" but
never named the template to refuse; given the estate's documented root/admin-template
failures, that omission in the crux EP was its single most likely wrong-reference. EP-17 now
names RBAC, states what taking it erases, and gives the fold-over-grants derivation.

The migration in EP-16 had been written as something that cannot happen: space membership was
described as "derived-OR-stamped," but records are append-only and frozen (I1), so a field
cannot be written onto existing records at all. Membership is now DERIVED — a default-space
fold for pre-account records, explicit space on new ones — and the migration is a fold rule
plus oracle, never a rewrite.

J1 as first written was false for the root: "identity verified, not claimed" cannot hold for
owner/SYSTEM, because nothing sits above the root to verify it against. J1 now states that
verification bottoms out at the founding — the self-aware-limitation shape the estate already
runs on — rather than leaving it as a hidden gap.

J4 claimed an invariant it could not test. The edge/client hop is composition-layer (§7), so
"the power view rides every hop" mixed a kernel-testable claim with a client promise. J4 now
splits: the gate is the kernel floor, in-kernel hops obey the R26 no-lie law, and the edge hop
is named a composition promise.

The authorization matrix undersold itself at two columns. The accounts world adds a third
failure mode the old bare-string tests never had — no account, so the act stops at identity.
EP-20 is now three columns.

J5's heuristic retirement carried a gap hazard: removing the all-space/targeted heuristic in
favour of the scope test could open a window weaker than what it replaced. J5 now requires the
scope test proven strictly-stronger-or-equal on the campaign-1 protected-core ledger BEFORE
the heuristic is removed — the conservation lesson applied to enforcement transitions.

One finding was noted rather than changed: EP-14's oracle is load-bearing beyond its size.
Installer-first means every later EP inherits any genesis bug, and the old-vs-pack differential
oracle is what keeps that safe. EP-14 is M/high by shape but campaign-critical by position —
flagged for the reviewer to hold to zero-divergence hard.

Two items were left as OWNER JUDGMENT rather than mentor-fixed: (a) whether EP-15's account
model is recorded-evidence identity (the v1 assumption) or waits for cryptographic identity
(campaign 4) — the draft assumes the former; and (b) whether the campaign starts after EP-13
(default) or inserts earlier — the draft assumes after. Neither blocks the read; both are one
word.

### Second pass (same date — examining what the first pass spared)

A first pass by the same mind is soft on its own generated structure, so a second pass
examined the SEMANTICS the draft assumed without stating. Seven findings, all folded above:

The worst finding of either pass was that the grant model had flattened the owner's own words.
The owner's grant form is actor × actions × INFO TYPE AND CONTENT × space; the draft had
reduced it to "info". The info-type dimension is load-bearing: it is what makes "remove
rule-writing power in this space" an ordinary grant operation (law is an info KIND) with no
rule-specific machinery — the exact this-is-not-a-special-case shape the owner's rulings keep
insisting on. J3 now carries all four dimensions and says why.

Revocation semantics were unstated. Stored-permission systems cascade deletes; ours must not
need to — authority is a CHAIN EVALUATED LIVE at every check (corpus §07), so revoking any link
is instant everywhere downstream because nothing was stored. This is now in J3, the second half
of the anti-RBAC derivation.

The space tree had no containment rule. Whether parent reach covers subspaces was unstated —
builders would have guessed, and a subspace with all grants revoked would have been left as
orphaned governance. J2 now states it: nesting IS containment; every space's chain terminates
at the root; no orphaned territory (the corpus's no-orphan items extended from actors to
territory).

Attribution versus acting authority at the gate was unstated. Handlers lawfully act as SYSTEM
while a verified account invoked them — the stamp_actor lesson, now structural in EP-15:
invoker (provenance) splits from actor (authority).

The go-live transition was missing — the difference between a landable EP-17 and one that stops
lawful work suite-wide. Flipping default-deny onto a grantless record refuses everything. It is
now stated: the founding pack records today's openness as an EXPLICIT mother-space grant, so
openness becomes visible law that later narrows space by space. No shim, no dual-mode gate.

The matrix needed a fourth column — right grant, wrong space, stops at scope.

Perf honesty was missing: the authority fold's cost is unmeasured, and acceleration is a
measured calibration, never a stored table (RBAC through an unchecked path). This is now §7.

---

## ADDENDUM — 2026-07-24: the two open owner judgments are RULED (dated change; §9's items (a) and (b) close)

Both items §9 left as OWNER JUDGMENT received their word on the pre-campaign-2
ruling sheet (2026-07-24):

- **(a) The account model — RULED "evidence."** Campaign 2 builds
  recorded-evidence identity, exactly as this paper and EP-15 assume;
  cryptographic identity upgrades it in campaign 4. No change to any EP.
- **(b) The campaign start — RULED "go," on the fix-first sequence.** Campaign 2
  launches after EP-13B (the pre-campaign fix pack the same ruling created:
  the five before-a-second-user fixes plus the protection-layer wiring, owner
  ruling "all before + B before"). EP-14's effective precondition becomes
  EP-13B DONE (reviewed) — recorded as a marked addendum on EP-14 and in the
  EP index, this same turn.

Same sheet, touching this paper's ground: the item-surface assumption
(design/28 §2) ruled CONFIRMED ("view"); the two wall-primitive laws ruled YES
and appended as owner-ruled addenda E1 (EP-16: a grant is never wider than its
maker) and E2 (EP-17: emission to a human channel is an ordinary granted act).
The six later cleanups ride into this campaign (builders fix where adjacent;
the mentor tracks adjacency at each EP verdict).

---

## ADDENDUM — 2026-07-25 — the transition policy's ENDGAME, owner-ruled (dated addendum)

The owner ruled and confirmed (BUILD-PROGRESS, this date): the founding
openness grant is SCAFFOLDING, not policy. EP-17's transition policy stands
exactly as written — openness became visible law so the flip changed where
openness lives, not what works — and the destination is now explicit: the
openness grant narrows to ZERO, channel by channel, each real channel opened
by its own explicit enabling grant (zero trust for all structured work; the
deontic vocabulary governs the unstructured side — design/30's dated
addendum carries the regime line). Consequences: the W4 narrowing question
is principled (retire scaffolding as real channels are granted — never
"close spaces by taste"); a future PILOT SPACE is born zero-trust under
explicit grants from its first record, not carved out of an open world; and
EP-20 gains the extinction lens (its marked addendum) — prove in a test
world that the openness grant can retire completely without wedging lawful
work.
