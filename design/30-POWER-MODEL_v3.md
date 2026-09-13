<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — The Power Model: Positive Grant, Computed Complement, and the Protected Core (plain-register edition)

Plain-register edition, in place (the framed original is retained at `tests/archive/30-POWER-MODEL.md` and in git history): same derivation, plain function terms. [banner amended 2026-07-24 — it formerly named this file as its own source]

**Status:** v1, 2026-07-17, mentor session, tier xhigh. SOURCE-DERIVED from the owner's
two-round power ruling (chat, 2026-07-17; recorded in BUILD-PROGRESS same date), extending
ruling 3 of the Phase-A gates (PACK-SCOPE) to its general form and re-rooting the EP-07
review's R20 fix. The owner's words control over this derivation. Labels per
`00-READ-FIRST.md` §6. Build consequences: `planning/exec/EP-07B.md` (interim backstop now),
the spaces/accounts stage (full machinery later).

---

## 0. The correction this derives from

The EP-07 review found that any actor could record a self-enforcing rule that blocks all
rule-writing, permanently, and refuses its own removal. The mentor's first fix was a
blocklist: enumerate the law-lifecycle acts and refuse rules that target them. The owner's
correction, two rounds:

1. That is block-only thinking — one tool of a rigid black-and-white system. CGL's
   enforcement space is wider: **targeted vs blanket × block vs attract**. The occasion
   calls for blanket-with-exception: **nothing, except what is granted.**
2. The protected thing is not a list of verbs. A local space-holder removing rule-writing
   power inside their own space is ordinary governance and must pass. What refuses — for
   every actor including the owner — is a rule reaching the **fundamental mechanics or
   legitimacy of the system**.

## 1. The law (the definitive)

> **Power is the positive grant; everything outside it is the grant's computed shadow.
> A rule is info; a view is info; creating info outside your granted space is not your
> power — full stop. And no grant, however wide, reaches the system's vital organs.**

Three clauses, three consequences:

- **The grant is the whole power definition.** Binding an actor to a space is ONE
  co-happening rule: `(+) actor(verified) × actions × info type/content × their space`.
  The matching `(−) … × every other space` is never stored — it is derived, the way every
  current state is derived from the record (P2 applied to authority). Storing the minus twin
  would be storing a status: it rots, and it multiplies (one minus per non-space). Default
  deny (ROOT-NEG-1) stops being a sentence and becomes the computed complement of the
  grant set.
- **Scope is part of every act of law-making.** A rule claiming to bind a space is an act OF
  that space: writing it requires power over that space. A rule of the form "(−) anyone ×
  CREATE-RULE × everywhere" is system-scoped info; system scope was never in an ordinary
  actor's grant; the general power check refuses it — no special guard, no protected-verb
  list. The all-rule-blocking case dissolves at the root. PACK-SCOPE (vocabularies scoped by
  reach and sight) becomes one instance of this law, not a special case.
- **The protected core caps even legitimate width.** A wide-power holder (the owner, SYSTEM)
  passes the grant check — so a second, absolute floor refuses what no grant may reach (§3).

## 2. Verification rides the chain (hop-by-hop)

The actor works against a **hardened local profile** — their loaded power view, derived from
the record's grants. When they type an act beyond their power (an all-space block, an
out-of-space write), the LOCAL view already answers "not your power" before the act travels;
each jump toward the store re-verifies against the same derived view; the gate confirms
against the record at the door. Not one guard at the end — the same question at every hop,
answered from one source (the record's grants). This is the read stack (§I8) applied to
authority: operations consult derived views; nothing waits for the store to find out it was
never allowed.

Machinery: verified identity + spaces + role/grant records + the per-actor power view — the
accounts/spaces stage. Until then the model is RECORDED LAW with an interim backstop (§4);
enforcement is never faked (gateless intake).

## 3. The protected core (the owner's line)

What refuses for EVERY actor, the owner included, is a rule whose effect reaches:

1. **Booting** — the system's capacity to found and re-found itself from its record
   (genesis, replay, the round-trip).
2. **Working with rules** — the system's capacity to receive, evaluate, and amend law at
   SYSTEM level (the gate, the interpreter, the law-lifecycle at system scope).
3. **The recorded legitimacy anchors** — already constitutional: recording-total,
   authority-anchored, secrets, self-protect.

The test is **scope + target**, never a verb list:
- `(−) users × CREATE-RULE × john-space`, written by the holder of john-space power:
  space-local governance of rule-writing — **passes**. (A team lead may lock down their
  workspace; the system's own metabolism is untouched.)
- `(−) anyone × CREATE-RULE × all spaces`, written by ANYONE including the owner:
  reaches the system's capacity to work with rules — **refuses, BOOT-INT, recorded**.
  The owner writing it would be locking the system's own rule-processing against itself, and
  the ruled route to a rule-free system is exit, not surgery (the decommission ruling's
  twin).

**RULED YES and SEEDED (owner, 2026-07-17):** recorded as the fifth constitutional law —
`CONST-SYSTEM-FUNCTION` (−, constitutional, enforcement live): *no rule may destroy the
system's capacity to boot from its record or to process rules at system level; space-local
governance of rule-writing is not this.* Provenance: the corpus's own boot-sequence step 11
(venn2-foundational §09), restored — the founding had never recorded it. Machinery: the
protected-core floor + the conservation branches; citations unchanged per the R13 ruling.

## 4. What lands now vs later (honest sequencing)

- **Now (EP-07B):** the interim backstop at the mint chokepoint. Pre-spaces, every rule is
  effectively system-scoped (only the mother space exists), so the backstop refuses a
  full-form DON'T that is all-space over the rule-processing surface — a trigger that matches
  law-lifecycle acts without any narrowing field, or a field-less trigger (matches
  everything). Labeled as the protected-core floor, not as the power model: the discriminator
  it approximates (system-scoped vs space-local) becomes real when spaces exist.
- **Later (accounts/spaces stage):** verified identity; space + role + grant records; the
  per-actor power view; the hop-by-hop check; scope carried on law records; the backstop's
  heuristic retired in favour of the real scope test. ROOT-NEG-1/-3 and PACK-SCOPE all
  reach full enforcement here — one stage closes four deferred laws.

## 5. Honest caps

- "Space-local" has no mechanical meaning until spaces exist — the interim backstop
  necessarily over-refuses (an all-space rule-writing ban is refused even though a future
  space-holder version would pass). Stated, not hidden; the over-refusal errs closed.
- The enforcement dimensions named by the owner (targeted/blanket × block/attract) are
  wider than what v1 expresses; **attract**-class enforcement (drawing acts somewhere,
  rather than stopping them) has no kernel expression yet — noted as CGL surface for the
  comparison/language layer, not built here.
- Actor identity remains caller-asserted until accounts land ("verified" in the grant form
  is the accounts stage's word); every interim guarantee stays cannot-do-lawfully +
  cannot-do-quietly.

---

## ADDENDUM — 2026-07-25 — OWNER-RULED: the enforcement regime follows the structurality line (dated addendum)

Ruled and confirmed on the record (BUILD-PROGRESS, this date; restated and
owner-confirmed):

- **Structured work — zero trust, blocked by default, as the GOAL STATE.**
  Every machine-executable act is refused unless an enabling rule matches it:
  match = the right; no match = refusal with citation. This section's §1
  (positive grant, computed complement) and the ROOT-NEG laws were always
  this law; the ruling names the destination: the founding openness grant is
  SCAFFOLDING for the enforcement flip, never standing policy — it narrows to
  ZERO as real channels gain their own explicit enabling grants.
- **Unstructured work — deontic governance.** Judgment cannot be gated by
  match=true; it is governed by the graded vocabulary (dos, don'ts, should,
  may — CGL enforcement terms, claimed-vs-effective strength). Binary gating
  for machinery; guidance-and-obligation for judgment. The full vocabulary
  is campaign 5's language work.
- **The seam:** when judgment lands as a structured act, deontics governed
  the deciding; the gate still gates the doing.

---

## 6. The protected core's DATA half, and the dynasty [added 2026-07-29, OWNER-RULED]

Raised at the volatile-boundary intake: the owner described "rules **or data** that
even the admin cannot change." §3's three protected items are all rule-CAPACITY
items, so the data half was put as an open question. It is now ruled, and the
ruling is that it needs no new mechanism.

### 6.1 — A live data-immutability guard is REFUSED as unnecessary; these are PRE-decisions

The owner's three worked cases, and where each already lands:

1. **An admin hands out power until an AI organisation holds the system.**
2. **An admin deletes their own account and leaves the system headless.**
3. **An admin reaches for absolutely guarded, unrecoverable secrets.** §3 item 3
   names `secrets` directly. Already refusing.

**[CORRECTION, same day, sitting mentor.] Cases 1 and 2 are ONE item and neither
§3 entry reaches it.** This section as first filed put case 1 under §3 item 2 (the
capacity to work with rules) and case 2 under item 3's anchor list. Case 1 does
not belong to item 2: an admin handing all power to an AI organisation destroys no
capacity at all — the system still boots, still evaluates law, still amends. What
case 1 loses is what case 2 loses, **the owner anchor**, one by transfer and the
other by deletion. See 6.2, which is rewritten accordingly.

**Ruled: (b) — a runtime guard on live data content — is NOT built.** The owner's
words: it could be pre-decision. The refusal comes from there being no grant, in
law, decided at founding. That is the power model doing its own job: power is the
positive grant and the complement is computed, so an act nobody was granted
refuses and cites without any object needing a protective attribute hung on it.
**A protected-data flag would be a stored complement**, which is the thing this
document exists to remove. Minimality gate applied: nothing added that the grant
model already derives.

### 6.2 — The OWNER ANCHOR is an effect-level protected item, and §3 does not contain it

**This is the load-bearing half of §6 and the first filing of it understated the
weight.** It was written as a small edge case about a headless system. It is not:
it is the item that carries the AI-organisation goal, and the protected core does
not currently contain it.

**Why §3's test does not reach either case.** §3 tests **scope + target**, act by
act. "Delete my own account" is one account at self scope and passes trivially.
"Grant power to this actor" is one grant at one target and passes trivially. Each
step is lawful; the destination is not. **A protection expressed act-by-act cannot
see a destination reached one lawful act at a time**, which is exactly how a
capable actor holding admin power would arrive there — not by one forbidden act
but by a sequence of permitted ones.

**The trigger has to be the EFFECT, and the estate has the shape already.**
`design/36` §4b.7's trigger was corrected from act-level to **effect-level** on
precisely this reasoning, so this is a protected-core item written at the effect
level rather than a new kind of check.

**RULED AND SEEDED (owner, 2026-07-29):** *no act may leave the system without an
owner anchor — not by deleting it, not by handing it away.* Effect-level, per the
`design/36` §4b.7 shape.

**The DERIVATION, and it is the ontology rather than a preference.** The owner's
ontology divides what can SELF-CHANGE — entities, actors — from what cannot —
resources, static things. **A governed environment permits NOTHING that cannot
self-change to exist unmanaged by something that can.** The system is itself such
a composite; **the anchor is its managing entity**; and a headless system, or one
handed away entire, is **the ungoverned-resource case at whole-system scale.**

That is why the protection is effect-level and not act-level: the ontology does
not care by which sequence of lawful acts the managing entity departs, only that
the composite must not be left with none. **This paragraph is §6.2's derivation,
not its decoration** — without it the rule reads as a policy someone chose, and a
policy someone chose is a policy someone can argue out of. Grounded on `design/27` §30's "owner actor +
owner tunnel". **It deliberately does NOT say the anchor must be human**, which
this estate does not require and which would foreclose the AI-organisation case
the rule exists to make safe. Transfer and deletion are caught by one trigger
because they are one failure.

**THE INTERPLAY SENTENCE IS FILED WITH IT, and it is the owner's (carry item 10,
approved 2026-07-29):** **anchor-EXISTENCE is §6.2's protection; anchor-HOLDER
constraints remain `CONST-AUTHORITY-ANCHORED`'s.** The two are different
questions. §6.2 asks whether an anchor remains at all; the standing constitutional
law asks what an anchor must satisfy to hold. Written together, **§6.2's
deliberate silence on whether the anchor is human can never be read as loosening
constitutional law that already speaks to who may hold it.** Without the sentence,
a later reader finds a protection that says nothing about humanity sitting beside
a law that does, and reads the newer one as amending the older by omission. It
does not.

**CLOSED 2026-07-29: §3 takes this as its FOURTH protected item, in the words
above.** It changes no build in campaigns 3 or 4 — no EP touches the protected
core — and it is the item on which the AI-organisation goal rests, so it reaches
the close as a filed protection rather than as an open question.

### 6.3 — The other door is a NEW DYNASTY, not an amendment path

**Ruled: the protected core is repaired by RE-FOUNDING, never by surgery from
inside.** §3 already says the ruled route to a rule-free system is exit, not
surgery; this generalises that from the one case to the whole core.

**Why an unamendable core is safe HERE and would not be safe in a nation.** In an
unstructured environment a founding cannot be replaced without a civil war, so a
constitution must be amendable from inside or its mistakes are permanent. In a
structured-data system **re-founding is cheap and the record is portable**, so all
unchangedness stays temporary — the temporariness simply lives at the installation
boundary rather than inside the running system. The owner's handle: a new dynasty
replaces the old one and the civilisation continues. The core does not bend; the
system is replaced and the record is carried across.

**The alternative this refuses, stated plainly.** A core amendable from inside is
a core an actor holding admin power can walk backwards through, one grant at a
time, until the foundation it stood on is gone. The AI-organisation case is
precisely where that matters, because "you can see what I did" is not sufficient
when the actor doing it can also amend what counts as visible.

**What 6.3 GENERATES, and it does not exist yet.** Re-founding only repairs
anything if the old record can be carried into the new founding. The estate's
tested round-trip is export → wipe derived → import → byte-identical, which
reconstructs under the SAME founding. Carrying a record founded under old law into
a system founded under corrected law is a different operation and is specified
nowhere. The related machinery (era-pinned migration oracles) is pointed at op
definitions changing over time, not at a founding being replaced under a record.
**Filed as EP-33 close-ledger item 26.** Not a hole in the ruling. A consequence
of it, named now because it is far cheaper to specify before the first dynasty
than during it.
