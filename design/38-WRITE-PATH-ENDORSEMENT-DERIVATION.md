<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-31 -->
# GOV-OS — The write path under the two-times law: endorsement, intent buffer, multi-view stamps [dispositions RULED — ADDENDUM 1]

> **[Title bracket amended 2026-07-31 from "RAISED, not ruled" — a dated
> in-place change under CANON law, made when ADDENDUM 1 landed. The body below
> stands as written on 2026-07-26; the addendum carries the rulings.]**

**Status:** v1, 2026-07-26, written by the C3/C4 paper-author seat from the
owner's four ideas (chat, this date) and the seat's derivation, which the
owner has seen. **Nothing here binds until ruled** — this is a derivation
sitting for the owner's word, the design/34 precedent. Intended readers: the
sitting mentor (flagged alongside the A-pack decision), the EP-26/EP-27
authoring when these ideas are wanted, and the C6 paper for §5. Labels per
00-READ-FIRST §6: the owner's four ideas are SOURCE-DERIVED (chat,
2026-07-26); every verdict below is the seat's derivation from standing law,
cited inline.

## 0. The owner's four ideas (restated, owner-confirmed reading)

1. A low-risk act traveling up or sideways may take effect once three-plus
   other active parties confirm it, without waiting for the store's word.
2. A high-risk act may take effect on the master views' endorsement, with
   the store append following rather than preceding.
3. The intake pipeline carries a cache duplicating the master views; an
   entry leaves that cache only when the store broadcasts back the exact
   same update.
4. Cache entries carry a cross-check hash stamped by every relevant master
   view — "not one master view's one-man view."

## 1. The intent buffer (idea 3) — lawful, under two fences

A pending-intent buffer that retires only on exact echo from the store is a
write-ahead intent queue. The retire-on-exact-match discipline is an
integrity property in its own right: confirmation is content-hash identity,
so a mutated or partial append can never silently satisfy an intent.

The two fences standing law puts on it:

- **Durable-or-honest.** A crash that loses unconfirmed intents must surface
  them as lost or re-submit them, never drop them silently — otherwise
  cannot-do-quietly breaks in the gap between endorsement and append.
- **Never a second source of truth for reads.** Any view answering from
  pending entries marks them provisional or refuses — R26 (a hop never
  lies) applied to the one structure that briefly holds truth the store
  does not. As a shadow store it is refused; as a pipeline structure with
  provenance-marked provisional state it is the S5 intake pipeline's front
  half arriving early, and the envelope already carries the fields for it.

## 2. The multi-view stamp (idea 4) — P7 composed with the seal; the strongest of the four

Each relevant master view endorses its own dimension — the rule view
lawfulness, the authority view power, the resource view availability — each
in its own frame, none merged, each stamp a small seal (view identity + the
state hash it endorsed on; design/34's shape). This buys, at once: an audit
answer to "which view confirmed this, looking at what world" for every
in-flight intent, and the dual-audit property on the write path — no single
corrupted or stale view carries an intent alone; a divergence between
stamps is detectable exactly as the blind streams detect divergence.

Cost discipline: the full multi-stamp ceremony is governance-lane work; the
class map decides which acts get it. A cache-fill-class act never needs
five stamps.

## 3. Endorsement before sequencing (idea 2) — lawful BECAUSE of design/35

Effect-on-endorsement-before-append does not break K1 IF the endorsement is
a sealed decision and the intent sits in §1's durable buffer — because that
is exactly the two times of authority: the endorsement is the DECIDING
moment (legitimacy created there, seal proving what the endorsing views
saw); the store append is the ORDERING moment; the store adjudicates at
arrival by deciding-time law; disagreement is the reconciliation sweep's
ordinary work (design/36 §4b). The endorsement-plus-seal is a record in the
weak sense; sequencing catches up.

## 4. The risk gradient runs the other way (the seat's one held correction)

The deciding question for "may the effect precede the sequenced append?"
is: **can the sweep still fully repair this if the store disagrees?**
Overturns reconcile state; they cannot reach what was consumed (design/36
§4b.6, owner-ruled). Therefore:

> **The higher the overturn cost, the earlier the store sits in the path.**
> Cheap-to-overturn effects — reversible, unconsumed, contained — may ride
> endorsement. Expensive-to-overturn effects — consumed outputs, anything
> irreversible — wait for the durable, sequenced append, where
> record-upstream is the only real guarantee.

Risk class is not a label anyone assigns: it is computable as
overturn-reachability — a measurement displaying as bands, never a stored
judgment.

## 5. Quorum (idea 1) — re-homed to federation, not discarded

Inside one record machine, three confirmations add nothing: every hop and
view derives from the same record, so three agreements are one derivation
done three times — correlated, not independent. Agreement is a staleness
check (R26 again), never added legitimacy; no quorum of derived views
outvotes the record they derive from. Quorum becomes real information where
the confirmers hold genuinely DIFFERENT records: sovereign instances
confirming against their own stores — C6's comparability machinery. There
the idea stands as stated.

## 6. Where each lands (none of it in the A-pack)

The A-pack stays the minimal fold acceleration under its named trap. Ideas
3 and 4 are EP-26/EP-27-adjacent (the buffer is the pipeline the lanes
ride; the multi-stamp is the seal generalized) — bound only by a marked
addendum on design/36 when the owner wants them. Idea 2 becomes lawful the
moment 3 and 4 exist. Idea 1 waits for the C6 paper, which should cite §5.

## 7. Honest caps

Unmeasured throughout — no buffer, stamp, or endorsement cost has a number;
every claim is structural. The §4 gradient needs its computable
overturn-reachability test specified before anything acts on it (a view
predicate over effect class — deliberately not specified here; deduction
past the machinery). This document binds nothing until the owner rules it;
if ruled, its homes are §6's and the ruling is one word per home.

---

## ADDENDUM 1 — the dispositions, RULED; filed by the author seat to close a dangling citation (2026-07-31)

The owner's dispositions were ruled and recorded on the log at the block-47
mentor entry (2026-07-29, item 7 — "design/38 is FILED by the author seat on
the owner's word") and their one binding consequence was carried into
`planning/exec/EP-28C.md`'s invariants, which cite "design/38's dated
addendum." This file carried no addendum until now — the citation dangled,
the exact class the close ledger's item 1 exists for. Filed by the author
seat, content SOURCE-DERIVED from the log entry; nothing new is decided here.

**The dispositions, per section:**

- **§1 (the intent buffer) STANDS — as PIPELINE, never an effect-license.**
  The echo-retire buffer arrives at EP-28C subordinated to that EP's first
  invariant: no reply releases before the sync covering its record. An
  intent's presence in the buffer licenses nothing; only the covering sync
  does.
- **§2 (the multi-view stamp) STANDS** as written.
- **§3 (endorsement-before-sequencing) is REFUSED IN-MACHINE, as redundant
  rather than as wrong.** Inside one machine, intents ride the same batch as
  the acts they would front-run, so endorsement-first is cost-identical to
  the gated act — the sync moves earlier, it does not go away. The idea stays
  alive exactly where §3's own derivation located its ground: remote-decider
  crossings, and C6, where the endorsing views and the store are genuinely
  apart.
- **§4 (the overturn-cost gradient) stands** as the frame the refusal itself
  used — the reply-after-covering-sync invariant is its expensive-to-overturn
  branch applied to every in-machine effect.
- **§5 (quorum) CONFIRMED C6-only**, as derived.

**Consequence for readers:** EP-28C's invariant 4 is the one place these
dispositions currently bind machinery; everything else here remains
direction for the EP-26/27-adjacent surfaces and the C6 paper, per §6.
