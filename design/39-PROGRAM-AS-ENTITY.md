<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature. NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-08-19 -->
# GOV-OS — design 39: THE PROGRAM AS ENTITY, THE BOX AS ITS DEFINITION

**Provenance: the owner's design, spoken 2026-08-19 in the architect's chat and
filed the same evening; the derivation trail and the honest caps are the
architect's, written under the owner's word. STATUS: the owner's seed for
EP-30-C's authoring — the comms units are authored UNDER this document; it
becomes campaign law by that authoring absorbing it, not by this filing.**

---

## 1 — The question this answers

Before communications can be governed, "program" has to mean something. Is a
program the bytes on disk? The process in RAM? The folder of data it owns?
Every OS gives a different partial answer, and none of the partial answers can
inherit a permission, because none of them is an identity.

## 2 — The definition (the owner's, kept in his shape)

**A program is an ENTITY — the same kind of thing TWC is.** Its identity is its
recorded establishment. Everything else is a view computed from its record:

- its running **processes** are its current incarnation in RAM;
- its **files and folders** are custody it holds;
- its **permissions** are computed from its record — which is exactly why an
  entity can inherit permission and a bare process ID never could.

Record the act, compute the view — applied to the word "program" itself.

## 3 — The topology (the two-channel glass box)

**Every program lives in its own glass box with exactly TWO watched openings,
by default and without exception:**

    one channel to the USER
    one channel to the SYSTEM

**No program ever moves information to another program directly.** When A
sends to B, that is A exercising ITS OWN authority through its system-facing
channel, the system witnessing and recording the crossing, and B receiving
through its own system-facing channel. **[This sentence binds exactly as §5
cap 1 scopes it: it governs OVERT flows. The one declared fast path — the
shared-memory grant — is recorded at the border and honestly unaudited
inside; read the cap with the claim, never the claim alone. Pointer filed
2026-08-20 at the mentor's :1412 raise, before any EP-30-C unit cites §3.]**

**The system is not the courier. It is the border.** The moving is the
program's act, under the program's authority, on the program's record — the
system gates and witnesses. This keeps agency and accountability where they
belong: a crossing is attributed to the entity that willed it, never to the
infrastructure that carried it.

**The consequence the topology buys: authority and footprint are legible BY
CONSTRUCTION.** Two openings per box, everything crosses them, nothing else
exists. Asking "what can this program do, and what has it done" has one
answer surface, not N.

**[WHAT THE INVARIANT COUNTS — ruled 2026-08-20 at the architect seat, on
EP-30-C1's R4 (the re-open-after-close near-miss), filed here because the
question is about this section's own words: the two-channel invariant counts
LIVE openings at a moment, never openings across a lifetime. Derivation from
this document's own §2/§7: the entity OUTLIVES its incarnations; incarnations
die and their channels close; a program's next incarnation must open its
channels again, so a lifetime quota would bar every restart and contradict
the entity/incarnation split at this design's core. The record holds every
open and close as history — record the act — and the invariant's subject is
the COMPUTED LIVE SET: at most one live system-facing and one live
user-facing channel per entity. A re-open after a close is a LAWFUL new
opening; the no-third-opening check refuses a third LIVE channel, not a
third recorded act.]**

## 4 — What this generalises (and it was already ours)

The glass box was this estate's image for the governed AI organisation —
"acting only through the tunnel, every act on the record." **This document
notices that the glass box is not a special enclosure for AI. It is what a
program IS in gov-os.** Every program a box, two tunnels each; the AI
organisation stops being a special case and becomes the general definition
applied to one particularly interesting tenant.

Derivation trail, so the authoring can cite rather than re-derive:

- **Record-as-only-shared-medium inside the kernel** (design/10 §2, the EP-30
  order): this document is that law stated at the program level, where it had
  never been stated.
- **The capability tradition** (seL4): all authority through explicit gated
  conduits — here radically simplified to a canonical per-program surface of
  two.
- **The custody vocabulary** (EP-30-C's fd-passing rows): handing another
  program an open file is a custody transfer THROUGH the border, recorded.

## 5 — The honest caps (stated here so the claim cannot be overclaimed)

1. **"Never without the system seeing it" governs OVERT flows only.**
   Programs sharing hardware always have side channels — timing, cache, disk
   contention. The claim as law: no overt flow uncrossed; interiors and side
   channels declared out of scope. Stated with this boundary the claim is
   defensible; stated as absolute it is false. Same discipline as the
   shared-memory rule, which is this document's own pressure valve: a
   shared-memory GRANT is recorded at the border and the interior is
   honestly unaudited — the declared fast path, not a hole.
2. **The overheads are real and already priced.** Record growth from
   high-volume small sends is capped by the coalescing policy (the owner
   gate at planning/build/OWNER-GATE-COALESCING.md); the gating cost on the
   send path is the campaign's standing speed tension, priced at ADDENDUM L
   and its family. Two channels is a topology claim, not a serialisation
   claim: the system-facing channel carries many streams, and watching is
   not copying — record decisions, sample flow.
3. **Compatibility is preserved behind unchanged interfaces.** Programs keep
   their sockets, pipes and queues; the crossing happens beneath them —
   the campaign's own method, proven per-subsystem by the conformance
   harness.

## 6 — What EP-30-C's authoring owes this document

- Channel lifecycle, sends and receives authored as crossings of the
  system-facing channel of an ENTITY, never as traffic between processes.
- The user-facing channel treated as a first-class, distinct opening — it is
  where consent and presentation live, and it maps to the external-world
  seam (answers frozen as inputs, sealed at hand-out).
- The two-channel default stated as the invariant; any additional opening is
  a raise, never a convenience.
- The entity/process/custody split of §2 used as the row vocabulary, so
  permission inheritance rows land on the entity and incarnation rows land
  on the process.

---

## 7 — Authoring notes (filed 2026-08-20 at the owner's pre-compact order; the reasons behind §2–§6, so the authoring hand inherits the WHY and not only the WHAT)

**Why the entity/incarnation/custody split falls where it does.** The split
follows what the record can hold without rotting. An establishment act is
append-once — that is what an identity IS here. Processes come and go with
every boot, so anything defined as a process dies with the boot: process must
be a VIEW (the entity's current incarnation), never the identity. Files
change hands, so they are custody EVENTS, not attributes. This is the
stored-copy-rots law applied to the word "program": every OS that stores
program identity in a pid, a binary path, or an ACL is storing a copy of
something that should be computed, and every one of those copies drifts.

**Why permissions are computed, never stored.** A permission must survive
the death of the incarnation that last used it and follow the entity that
owns it. Only derivation from the record does both. A stored permission on a
process dies with the process; a stored permission on a file drifts from the
decisions that granted it. And inheritance — the owner's own test case (TWC
inherits) — is a RECORD RELATION between entities, computable at need; a pid
has no record to derive from, which is exactly why no existing OS can answer
"why does this process have this right" with a citation.

**Considered and rejected, so the authoring does not re-walk these:**
1. *Program = process group (cgroup-shaped).* Rejected: a group is an
   incarnation-set — still dies with the boot, no identity across restarts,
   nothing to inherit from. Groups are how the box is ENFORCED at one layer,
   not what the program IS.
2. *Program = code identity (binary hash).* Rejected: the same bytes run by
   two owners are two authorities. Identity is establishment plus authority
   lineage, not content — the digest names the CODE, never the ACTOR.
3. *Three or more default channels (a separate storage channel, a separate
   admin channel).* Rejected: storage is custody THROUGH the system channel;
   every extra default opening multiplies the audit surface and re-opens the
   N-conduit legibility problem the two-channel shape exists to close. Any
   additional opening is a raise, never a default (§6).
4. *System-as-courier.* Rejected on attribution: if the system moves the
   bytes, a refusal attributes to infrastructure and the acting entity's
   record goes quiet. The border framing keeps every crossing attributed to
   the entity that willed it — the record's attribution law, preserved.

**The exact scope of the honest caps, because overclaiming is this design's
one danger.** "Never without the system seeing it" binds OVERT flows through
the two channels — nothing else. Side channels on shared hardware (timing,
cache, contention) are declared OUT OF SCOPE, not defended against; the
claim's defensibility depends on saying so. The shared-memory grant is the
DECLARED fast path — recorded at the border, interior honestly unaudited —
a pressure valve designed in, never an exception granted ad hoc. Overheads:
record growth is capped by the coalescing policy (the owner gate); per-send
path cost is the campaign's standing speed tension (ADDENDUM L family);
and two channels is a TOPOLOGY claim, not a serialisation claim — the
system-facing channel carries many streams, and watching is not copying.

**Why each §6 item is owed.** Rows land on the entity (not the process)
because permission rows on incarnations would re-create stored-copy rot one
layer down. The user channel is first-class because consent and presentation
live there and it maps to the external-world seam (answers frozen as inputs,
sealed at hand-out) — collapsing it into the system channel would lose the
distinction between "the user said" and "the system decided." The
two-channel default is an INVARIANT with extra openings a raise, because a
convenience opening is a fence hole at the program level — and this estate
has spent a fortnight learning what unnamed openings cost.

---

**[EXTENSION POINTER, 2026-09-02, the architect's hand on the owner's design
dialogue of the same day — this block amends nothing above; it routes the
reader.]** Three questions this paper leaves open are answered in
**design/43-RULE-USER-IDENTITY-AND-PERMISSION.md**, which extends this
document: (1) the word "program" does DOUBLE DUTY — everyday sense (the
static bytes, a resource in SCOT Module 1's terms) versus this paper's
governed sense (the ENTITY) — design/43 §1 separates the two so no future
reader re-fights it; (2) IDENTITY IS LAYERED — the master identity this
paper establishes is parent to SESSION identities (a process's temporary
life holds a real child identity; its acts attribute to it AND through it
to the master) — design/43 §2, with the master↔session formal home held
open as owner decision D1; (3) the BOUNDARY CLASSES the box topology
implies — glassboxed entities, the SYSTEM as the border entity that cannot
live behind a border, humans as external entities verified at the tunnel —
design/43 §5. The two-channel invariant, the entity/process split, and
every §6 obligation above stand unchanged.
