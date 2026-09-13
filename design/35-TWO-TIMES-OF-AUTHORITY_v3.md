<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-25 -->
# GOV-OS — The Two Times of Authority: deciding time carries legitimacy, recording time carries order

**Status:** v1, 2026-07-25, OWNER-RULED (chat, this date; the owner's worked
example controls over this derivation on any divergence). First derivation
recorded here at high tier; the C3 launch paper re-derives the machinery at
full resolution (the session registry, the pipeline logic) — this document
binds the LAW and its placement, not the build detail. Labels per
`00-READ-FIRST.md` §6.

## 0. The ruling (the owner's own structure)

Every judged or authorised act has TWO times, and they carry different halves:

- **The deciding time** — the moment the thing actually became authorised, in
  the decider's hands. **This is where legitimacy is created.** It is never
  created at the point of effect (the same law as founding-only legitimacy,
  at act scale).
- **The recording time** — the moment the store writes it and gives it
  effect. **This is where order is created.** `record_time` remains the sole
  total-order anchor of the log — nothing in this ruling moves that.

**The law: a decision binds from its deciding moment, not from its arrival.
Arrival order never adjudicates; deciding time plus authority adjudicates.
The store's acceptance test is a legitimacy-transfer test: each arriving
decision is evaluated against the law in force AS OF ITS DECIDING TIME, with
its seal (the recorded hash of exactly what the decider was shown, design/34)
as the proof of what world it was decided in.**

## 1. The worked example (SOURCE-DERIVED, the owner's own)

- CEO decides rule X at 9:00; it reaches the store at 10:00. Others decide
  acts the rule touches at 9:30. **Their acts are overturned** — recorded
  overturn events citing the rule and the deciding-time precedence, never a
  silent disappearance — because X was in force from 9:00, its deciding
  moment. They had not been told; that is the push's failure to prevent
  (§3), not a validity question.
- Others decide at 9:00; CEO decides X at 9:15; X arrives 9:30; the others'
  acts arrive 10:00. **The others' acts stand** — decided before the rule
  existed, provable: their deciding timestamps and seals predate X's deciding
  moment. The store accepts them under the law of THEIR deciding time even
  though X arrived first.

## 2. The reconciliation sweep (what "overturn" is, mechanically)

When law arrives whose deciding time predates already-recorded acts, the
store does not rewrite anything (append-only stands absolutely). It computes
the affected set — every recorded act whose deciding time falls after the
rule's deciding time and whose content the rule reaches — and appends
**overturn decisions**, each citing the rule and the two timestamps. Views
then answer with the reconciled state; the original acts and their overturns
are both permanently on the record. Overturning is ordinary governed
activity: recorded, rule-citing, attributable, replayable.

## 3. Priority lanes and the session-aware push (making overturns rare)

An overturn is lawful but expensive — people acted in good faith under law
they were never shown. So the ruling's second half:

- **Law travels faster than traffic.** Rule updates ride a priority lane in
  BOTH directions — up (to the store) and broadcast down (to views) — ahead
  of ordinary acts. Auto-prioritised: the lane is a property of the record
  kind (law-family), read from the record, never a code verb-list.
- **The system knows who is live.** An active session is a known contact
  point: a recorded session-open (and close) with its **personal local rule
  view** — the computed slice of law that binds what that session is doing
  (the local duty profile of the base tree, made session-scoped). The
  standing push (design/28 §6) extends: when a law change lands whose reach
  intersects a live session's local view, the change is delivered to that
  session immediately on the priority lane — the 9:02 update reaches the
  9:00-opened page before its 9:05 submit.
- **Pipeline logic is per-view.** Each view runs its own up/down flow logic
  based on the sessions it knows are active — what to push, to whom, at what
  priority. The flood boundary holds unchanged: deliveries are DERIVED and
  append nothing; kill the queues, replay, identical. Push is evented on
  append — the wall-clock ban (15.1) is untouched.

## 4. The seal is the backstop (relation to design/34 — RULED adopted)

No push closes every race (the update and the submit can truly cross in
flight). The fingerprint (design/34) is the floor under the whole law: every
hand-out records the hash of what the decider was shown; at acceptance the
store compares. Unchanged in what the decision depended on → legitimacy
transfers, effect follows. Changed → refuse, cite, re-ask against the
current world. The owner's ruling adopts the seal as this backstop ("store
can see decision time stamp hash if that is accepted or not"); design/34
lands as the `fingerprint` check kind per its §6, inside this larger law.

## 5. What stands unchanged (checked against canon — no silent conflicts)

- **`record_time` stays the sole total-order anchor** of the log (02 §1.4,
  design/21). The log's order is untouched; this ruling governs VALIDITY,
  which was never the order's job. Two frames, two answers, no contradiction.
- **Tritemporality already carries the field**: the deciding time is
  `occurrence_time` made load-bearing for decision- and law-family records.
  No envelope change (I1 holds); what changes is that adjudication reads it.
- **Append-only stands**: overturns are appended decisions, never edits.
- **The gate's live checks stand**: authority is still evaluated live at
  effect time (a revoked chain still refuses at the door — that refusal is
  authority information, not staleness information; the two frames stay
  separate per design/34 §2).

## 6. Honest caps (named, not hidden)

- **Deciding timestamps are caller-asserted until C4 signs them** — the same
  cap as identity (R20-2), stated not hidden. The seal bounds how far a claimed
  time can run behind the truth in one direction: a claimed deciding time
  cannot predate the store-state its own pack hash pins (a decision cannot be
  claimed at 9:00 over a world that only existed at 9:10). The other direction
  (a claimed time running later than the true one) closes with cryptographic
  signing in C4.
- **The machinery is unbuilt**: the session registry (open/close records,
  read-set declaration), the priority lanes, the per-view pipeline logic,
  and the reconciliation sweep are C3+ campaign work — law recorded now,
  machinery lands with its campaign (the gateless-intake pattern, as with
  every deferred law before it). The C3/C4 paper author carries this
  document as a directional constant.
- **Overturn reach needs its own derivation at the paper**: which recorded
  acts a late-arriving rule "reaches" is a view computation the paper must
  specify precisely (the rule's scope × the act's content × the interval);
  stating it loosely here would be deduction past the machinery — deferred
  on purpose.
