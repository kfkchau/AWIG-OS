<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature. NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=DRAFT supersedes=- superseded-by=- verified=2026-09-02 -->

# GOV-OS — design 43: THE RULE USER — identity, occupancy, and permission on the relation geometry

**Provenance: the owner's design, spoken 2026-09-02 in the architect's chat
(the modular-development dialogue) and filed the same day; the derivation
trail and the honest caps are the architect's, written under the owner's
word. Theory grounds READ AT THE ARCHITECT'S HAND before drafting, on the
owner's order: SCOT core-ontology (draft 0.4), Venn2 formal spec v2
(2026-07-08) + ontology-and-overview, and the CGL foundational layer — all
at `apps/cgl-app/plan/repo/`. This document extends design/39 (program as
entity); it does not amend it. It also stands ON design/42 (the corpus
harvest, owner-ruled 2026-08-22), which already adopted SCOT M1's
entity/resource gradient into design/41's functional-roles law and
confirmed the estate/corpus convergence — where this paper re-states
harvest ground it CITES 42 rather than re-deriving; what is NEW here is
the layered-identity model, the occupancy/permission geometry (§3), the
boundary classes (§5), and the s/u gradient reading (§6). STATUS: seed for
the modular charter's shared governance standard; it becomes law per
estate by that estate's own adoption, not by this filing.**

---

## 1 — The triad (the owner's, on SCOT's own terms)

SCOT Module 1 draws the root line: a RESOURCE cannot originate change in
itself; an ENTITY can — and the capacity is a GRADIENT, not a binary.
Applied to the machine:

    STATIC INGREDIENTS   program bytes, rule records, the record itself —
                         resources. Cannot act, cannot use a rule. Appear
                         in governance only as OBJECTS of acts (custody,
                         citation, amendment).
    LIVING OPERATION     the process / session / running AI — the
                         self-changer, SCOT's entity-in-operation. THE ONLY
                         THING THAT CAN USE A RULE. Mortal by construction;
                         changes itself destructively; keeps no past.
    THE RULE USER        the governed identity the operation acts AS — the
                         continuity anchor (Venn2 §2.1: "the thing that
                         persists through changing relations"). Answers for
                         every act, forever: attribution, once recorded,
                         never expires.

The three sentences that hold it: **the process changes and forgets; the
record remembers and cannot act; the rule user acts through the one and
answers through the other.**

## 2 — Identity is layered

    MASTER IDENTITY      the continuity anchor: a seat, a program, TWC,
                         gov-os itself, a human. Ends only by recorded act
                         (dissolution) — and even then its attributions
                         stand (the human-death case: acting ends, identity
                         persists as the subject of its record).
    SESSION IDENTITY     one incarnation's identity: this window, tonight's
                         process, one document VERSION under its master doc
                         number. Real while it lives; born at load, dead at
                         exit; its acts attribute to it AND through it to
                         its master.

**[D1 — OWNER DECISION, held open]** Where the master↔session relation
lives. Venn2's core EXCLUDES identity relations by design (spec §1: "a
separate identity layer" — `version_of`, `representation_of`). Two lawful
homes: (a) the identity layer (`session_of`, cleanest fit to the spec's own
separation); (b) NS in a dedicated lifecycle frame (the owner's spoken
"parent (venn2)" usage — expressible, since frames scope everything). The
architect recommends (a) and records that the owner's spoken usage was (b);
both are formalism-faithful; the choice binds every estate's schema.

## 3 — Structure, occupancy, and permission on Venn2 (the load-bearing part)

The corpus's own canonical example already carries the whole model:

    John NS McDonald's        frame: organisation      (membership: nested)
    John AD Crew-Member-Role  frame: role occupancy    (the hat: touching)
    John AD Staff-Profile-334 frame: occupancy         (person ↔ record)

So, in the formalism's actual terms (correcting the architect's earlier
two-primitive sketch — Venn2 has FIVE base states, frame-and-time scoped):

- **Org structure** = NS/EM chains in the ORGANISATION frame. Permission
  grants attach to structure nodes (org, division, team, position) as
  relation-instance records.
- **Occupancy (the hat)** = an AD relation instance in its own frame,
  first-class (Venn2 §2.4): it carries `valid_from/valid_to`, status,
  source — so "fire the CEO" is one relation-instance ending, and every
  derived permission updates by replay. REVOCATION-BY-DERIVATION.
- **Effective permission** = a frame-scoped walk: from the actor's live
  occupancy instances, up the organisation frame's NS chain, collecting
  grants. A pure view. No stored ACL anywhere (CGL foundational 07:
  "authority = view over rule + relationship + event records; no authority
  field as primitive truth").
- **THE ANTI-BLEED GUARD, free from the geometry:** the composition table
  binds within ONE frame — "never transit across different frames" (spec
  §3). Physical containment grants nothing organisational; a data-storage
  nesting grants nothing legal. **Context collapse — the classic
  permission-system disease — is impossible at the geometry layer, not
  discouraged at the policy layer.**

## 4 — Multi-identity = pair profiles, one anchor

One person: CEO of the company (AD, occupancy frame, company structure) ·
gatekeeper of football team X · parent of child Y · mentor of group ABC.
Venn2 §11: the full relationship of any pair is a PAIR PROFILE — many
relation instances across frames, no conflict. **One attribution anchor,
many hats; never many selves.** Every act names its capacity:

    ACT: actor = the master identity (stamped — the engine's fact, C4W law)
         capacity = the occupancy relation instance the act is done under
         session = the incarnation that performed it

Permission derives from the capacity; answerability lands on the anchor;
the session is named so the record can say WHICH incarnation acted.

## 5 — Boundary classes (the owner's, 2026-09-02)

    GLASSBOXED ENTITIES   programs, AIs — live inside the two-channel box
                          (design/39); their sessions act inside it.
    THE BORDER ENTITY     the SYSTEM — an entity (it follows and operates
                          rules) whose nature is to BE the border; it
                          cannot live behind one. CGL foundational 02: the
                          only actor that writes governed state after boot.
    EXTERNAL ENTITIES     humans — unboxed, but channel-bounded: identity
                          verified AT the tunnel (CGL foundational 03: a
                          tunnel binds sender, target, permitted class,
                          proof method).

## 6 — s-rules and u-rules = the structurality gradient applied to rules

SCOT Module 8/11: rules inherit structurality. The owner's interface split
is that gradient, named: **s-rules** (structured — hooks, gates, schema
checks; the machine's observation model is uniform by construction, so
enforcement is mechanical) and **u-rules** (unstructured — prose law; binds
by aligned interpretation, holds by discipline). The estate's enforcement
ladder (capability > hook > script > written word) is the same gradient
read as engineering. A u-rule hardened into an s-rule is STRUCTURING WORK
(Module 8), and the estate should know which of its rules sit where.

## 7 — What this makes impossible, and who absorbs it

IMPOSSIBLE: permission bleed across frames (geometry, §3) · unattributable
acts (stamp + capacity + session) · permission surviving its occupancy
(derivation) · a static thing exercising a rule (SCOT Module 1/7) · an
identity erased by a power button (anchors end only by recorded act).
COSTS: every act carries capacity; every occupancy is a first-class record;
the permission walk is computed, so it must be cached lawfully (regenerable
only). ABSORBED BY: the engines, in derivation work — not the owner, and
not the rule users.

## 8 — Honest caps

The Venn2 corpus is marked DRAFT/unsorted at its own paths; its composition
table carries its own provenance warning ("verify against the published
RCC-8 source before production inference") — inheritance walking uses only
NS/EM transitivity, the table's least contested rows, until that check is
done. SCOT core is DRAFT 0.4. D1 (§2) is undecided and blocks schema work
in any estate that adopts this. This document read three theory sources and
no technical/machine-mapping docs, per the owner's scoping instruction;
the zone parameter E, overlap objects, and mediated adjacency are noted as
available but deliberately unused here — the minimality gate holds until a
concrete need names them.

© the owner's design; derivation and caps by the architect seat, 2026-09-02.

## ADDENDUM 2026-09-06 — THE KEY FAMILY'S READ DIRECTION (content-at-rest; owner-asked, D08.19)

**Provenance:** the owner's questions of 2026-09-05/06 ("how do we stop
people seeing info by disk access? do we have encryption?" / "add in the
most architecturally correct place"). Design home ruled HERE: this is the
identity subsystem's second use of the bound key — signing proves WHO
WROTE; this proves WHO MAY OPEN. Not networking (corrected on the
record, D08.19).

**The shape, on the row model:**
1. LOCATION IS NEVER SECRET. Where the record starts is declared in the
   founding, in the open; hiding WHERE is weak and breaks
   verify-without-revealing. Only CONTENT is sealed.
2. THE SECRET IS THE ACTOR'S ID CARD — one identity, two derived keys
   (sign / open), because one key doing both is weaker than two doing one.
3. PER-PIECE KEYS, WRAPPED TO READERS: each content piece (already behind
   its hash by the placement law, design/46) is locked with its own random
   key; that key is wrapped to the card of every allowed reader and stored
   beside the piece. Add a reader = wrap once more (content never
   re-encrypts). Remove a reader = a NEW piece; the old is handed over or
   stays sealed forever — custody conservation, never deletion (:2856).
4. TWO FINGERPRINTS: outer, over the sealed bytes (anyone verifies the
   chain without opening); inner, over the content (checked at opening).
5. OPENING IS A ROW: actor, action open, object the piece — a read of
   sealed content is as recorded as a write. Raw disk reads that bypass
   the gate yield shells + ciphertext only.
6. NEEDS NOTHING NEW: the key family (1.33), the placement law (1.35),
   one open ceremony. No new kind, no new check.

**Relation to the disk lock beneath:** two locks, different jobs — the
OS disk lock stops a stolen drive (on, verified LUKS 2026-09-05); this
stops a logged-in reader who is not an allowed actor.

**Plan home: THE OWNER'S WORD** (new scope; EP-42 stays last by ruling):
either one plan built before the review, or the first plan of the next
campaign. Archi recommends before the review.

**AS-BUILT CORRECTION 2026-09-06 (EP-46 :3107):** point 5's "raw disk
reads that bypass the gate yield shells + ciphertext only" holds for a
reader of the BLOBS alone. A reader of the whole record on disk can
derive a public open key from the recorded sign key and unwrap, because
the key material is modelled estate-wide (design/37 §9 as-built). The
shape is complete; the cryptography is the KEY-MATERIAL-REAL flip, the
owner's word.
