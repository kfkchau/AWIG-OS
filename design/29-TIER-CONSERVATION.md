<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Tier Conservation: Amendment Without a Gap, and Scoped Vocabularies

**Status:** v1, 2026-07-16, mentor session, tier xhigh. SOURCE-DERIVED from three owner
rulings (chat, 2026-07-16; recorded in BUILD-PROGRESS same date) extending the three-tier
ruling (design/28 §I11). The owner's words control over this derivation on any divergence.
Labels per `00-READ-FIRST.md` §6. Build work package: `planning/exec/EP-05C.md`.

---

## 0. The three rulings this derives from

1. **Founding-only legitimacy.** New constitutional law can never enter a running system.
   Genesis-only minting mimics natural legitimacy: supreme law draws its authority from the
   founding moment, not from anyone's ongoing power. The owner's lawful relationship to the
   constitution is live-under-it or leave-it — exit, never override.
2. **The shield never drops.** Any change that would create a protection gap is auto-detected
   and refused. The only lawful amendment of a protected operation is one where the
   replacement arrives in the same package as the removal.
3. **Vocabulary authority is scoped, not privileged.** An actor may rewrite vocabularies
   within their space or power reach; beyond that reach, even reading a vocabulary is a view
   permission. No special guardian role exists for packs.

## 1. The one law the rulings share (the definitive)

All three rulings are the same statement made at three altitudes:

> **Protection is conserved through the system. Only the founding creates it; nothing
> running may create, elevate, demote, gap, or quietly route around it — and every attempt is
> a recorded refusal.**

Phase A already built three corollaries of this law without naming it: runtime minting
refused (genesis-only tiers), tier-laundering refused (the record is untouchable, its tier
goes with it), and unauthorized core retirement refused (A4). The Phase A review's probe
found the two corollaries still missing:

- **No gap** — an amendment path that lowers the shield between the old protection ending
  and the new beginning is itself a violation (the probe: retire + re-create returned an
  ORDINARY core, which a nobody then deleted).
- **No demotion** — a protected definition may not be superseded by a less-protected one,
  even by its lawful amender (demotion is a gap that never closes).

Ruling 2 closes both. Ruling 1 fixes the boundary of the law (founding creates; exit is the
only escape). Ruling 3 extends the same conserved-authority shape sideways: authority over
vocabularies was never an authority to hand a guardian — it is the existing scoped
sight-and-authority model reaching the pack layer.

## 2. Amendment as supersession — the mechanism (ruling 2 lowered)

**The current amendment idiom is the gap.** v1 amends a definition-born op by RETIRE-OP +
CREATE-OP ("shadowing impossible rather than clever" — the v1 crutch, opdefs.py). Between
the two acts the op is gone; after them the tier is gone (CREATE-OP rightly mints ordinary).
The idiom, not any single guard, is the defect — fix the definitive:

**AMEND-OP: one gated act, one appended record, in-place supersession.**

- A new operation `AMEND-OP {name, definition}` — the mirror image of CREATE-OP: it
  REQUIRES the name to be live (CREATE-OP requires it not to be). Its single decision
  record carries the new definition with `tier` **copied from the active definition, never
  from the caller**.
- The `op_definitions` / `live_definitions` folds learn: an AMEND-OP record replaces the
  named definition in place, latest-wins — exactly how CREATE-RULE already amends rules.
- **There is no down moment.** The owner asked for remove-and-add as one package; one
  supersession record is that package in its strongest form — the gap is not detected and
  refused, it is UNREPRESENTABLE. (Detect-and-refuse still guards the residual paths, §3.)
- Authority: amending an owner-tier definition requires actor `owner` (the A4 trust level).
  Ordinary definitions amend under v1 rules. Constitutional definitions refuse amendment
  entirely (ruling 1; the existing A3 branch).
- Retire+create remains lawful for ORDINARY ops only (v1 unchanged there).

## 3. The guard extensions (detect-and-refuse for what remains representable)

`gate._constitution_guard` gains the conservation branches; everything stays refuse-and-
record, cited:

- **(d) Gap refusal.** RETIRE-OP whose target's active tier is `owner` is refused outright
  (BOOT-INT) — for every actor, the owner included. Bare removal of a protected core IS the
  gap. Decommissioning a core without replacement is therefore not possible through the
  system; RULED (owner, 2026-07-16), no longer inferred: "removing the shield is the
  ungoverning move; the route to an ungoverned system is exit, not surgery" — confirmed. [The Phase A test "owner may retire a core" flips to "owner's bare
  retirement is refused; owner's AMEND-OP succeeds" — a ruling-driven semantics change,
  logged.]
- **(e) Conservation exemption to branch (a).** The existing branch (a) refuses ANY payload
  claiming a protected tier. It gains one narrow exemption: an AMEND-OP-class supersession
  whose payload tier EQUALS the active tier of the same live name, executed by an actor
  satisfying that tier's authority. Elevation (active ordinary → claimed owner) refused;
  no-target (nothing live to conserve) refused; wrong actor refused. Constitutional is never
  exempt — branch (b) and ruling 1 stand absolute.
- **(f) Demotion refusal.** Any write superseding a live protected definition must carry
  that same tier — a supersession whose payload claims a LOWER tier (or none) is refused.
  This is laundering's mirror image: (b) stops the tier being stripped from a rule, (f)
  stops it being dropped from an op through supersession.

Together with Phase A's (a)(b)(c), the guard now enforces the §1 law completely for every
gated write. The guard-exempt direct appends (genesis, refusals, the audit mirror) were
re-verified shape-safe in the Phase A review; R10 (function-scoping the sole-appender grep)
carries to EP-13 with constitutional stakes.

## 4. Scoped vocabularies (ruling 3 lowered)

**The law, recorded now:** a new root rule enters genesis —

- `PACK-SCOPE` (−, ordinary tier): *no rewriting a vocabulary beyond the actor's space or
  power reach; no reading one beyond the actor's sight.*

**What it means structurally.** A category_pack is governed information like any other: it
lives in a space, writing it requires authority whose reach covers that space, and reading
it is a sight question (P6 — sight is law). The kernel's own packs (the syscall map,
rule-errno, the audit-action list, the boot vocabularies) live in kernel/root space — beyond
any ordinary actor's reach. That is what cures the Phase A probe (alice emptying the syscall
map): not a guardian authority on AMEND-PACK, but the reach she never had.

**Enforcement is honestly deferred** (the gateless-intake principle — law precedes
machinery): reach needs spaces beyond the mother space plus authority chains; sight-filtered
pack reads need per-actor views. Both land with the accounts/spaces work. Marked
`enforcement: deferred` exactly like CONST-AUTHORITY-ANCHORED. Until then AMEND-PACK keeps
floor-only enforcement — and the audit floor itself stays CONSTITUTIONAL enforcement
(CONST-RECORDING-TOTAL), independent of scope: reach lets you amend a pack you hold; no
reach anywhere lowers the floor.

**Non-collision with ruling 2:** tiers protect DEFINITIONS (rules, ops) by conservation;
scope governs VOCABULARIES by reach. A pack is not tier-protected (only its floor is,
where constitutional law pins it); an op is not scope-governed (its authority is its tier).
Two mechanisms, one root: authority is never created at the point of use.

## 5. What this deliberately does not do (honest caps)

- **Actor strings stay unauthenticated** until accounts land — `actor == "owner"` is
  caller-asserted everywhere, including A4 and branch (e). The guarantee remains
  cannot-do-lawfully + cannot-do-quietly (a spoofed act is recorded AS the owner's,
  visible and attributable-on-inspection), not cannot-do-at-all. Unchanged from Phase A.
- **On-disk edits stay out of scope** (design/28 §I11: detectable by the mirror now,
  signing later).

> **Amendment (documentation-currency, EP-MAINT-C4-FINDINGS F2 — records code state, no design change).** 2026-09-08: real cryptographic signing is the KEY-MATERIAL-REAL unit (in progress); the live shape is modelled — see gate.py:171.
- ~~The decommission edge is derived, not ruled~~ — RULED, confirmed (owner, 2026-07-16;
  §3d).
- **PACK-SCOPE's reach semantics are named, not specified** — the precise reach function
  (space nesting × chain depth) is designed when spaces exist; specifying it now would be
  deduction past the machinery it needs.
- Unread here: EP-05 Phase B's in-flight changes (running while this was written; EP-05C
  is sequenced after it and touches the gate/opdefs/boot surfaces only).
