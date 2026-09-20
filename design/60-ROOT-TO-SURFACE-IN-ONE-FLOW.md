<!-- gov-os provenance · FRAME: governance-theory · CORPUS-CLASS: design note. The owner's questions of
     2026-09-17 (dialogue 10, design/59 Part 1c, design/56 §3a/B16/B17) REDONE AS ONE FLOW on his word of the
     same day: "the last 20 rounds, view all them and redo all and reorder output in one to a coherent flow".
     Nothing new is founded here; every sentence restates what the named papers already carry, in root-first
     order. On divergence the papers win. NON-GOAL: none. -->
<!-- doc: class=DESIGN status=LIVE verified=2026-09-17 -->

# ROOT TO SURFACE — the day's design in one flow (2026-09-17)

Eleven steps, root first. Each step stands on the ones before it and on nothing after it.

## 1. What is stored

Two things are stored as truth, and only two. The MASTER RECORD: rows, in the order they were decided, only
ever added to. The CONTENT STORE: content addressed by its hash, written once, never edited. Everything else —
every view, every current state, every permission list — is computed from those two and can be deleted and
recomputed to the same bytes. The signing key's secret lives in memory, not on disk; the record keeps only its
hash. The kernel's own code is not "stored in" the system — it is checked against the digest the record names
before its first act. The founding pack is the seed that writes the record's first rows; after that it has no
further authority. (Dialogue of the day; design/31 J8 addendum; design/47 §9.)

## 2. What information is

Three kinds, and nothing is a fourth (the owner's root, design/59 Part 1c). An ACTIVITY RECORD: the verb —
actor, action, object, target. An ATOMIC INFORMATION ITEM: the noun — a thing that holds content, one thing
one place, versioned never edited. A RELATIONSHIP: the position — no content of its own, two ends and a kind
(containment, custody, bind), one fact with two signed halves. An item is what a thing IS, a relationship is
WHERE it sits among things, an activity is what HAPPENED or is REQUIRED between them.

## 3. The format of a rule, and of an event

Both are the one activity shape — that is why compliance is computable. A RULE is activity in PATTERN form:
actor as a class or a place, action, object kind, target, carrying a requirement (may / must / must not) and
no time. An EVENT is activity in HAPPENED form: this actor, this action, this object, this target, at this
time, decided or refused, citing the rule it was decided under. A rule is not an item and not a document: it
is a row in the master record in the pattern shape, and what makes it a rule is the requirement. The rules in
force at any instant are a READING of the record — computed, not kept anywhere as a list.

## 4. The format of an item

An item's row in the record carries its identity and the HASH of its content; the content's bytes live in the
content store under that hash. A 600 MB file is one row (name, hash, who brought it, when) plus 600 MB in the
content store — the record stays rows, the store stays bytes, and either can prove the other because the hash
binds them. Small content may ride in the row itself; the rule is the same either way: the row is the fact,
the hash is the bridge, the bytes are content and never truth on their own.

## 5. What a view is

A view is a computed reading over the record — the events, rules, items and relationships that concern one
place, one actor, one question. It is derived, used, dropped, and derived again; it is never patched in place
and never consulted as truth. A view may be written to disk or held in memory as a convenience copy; its
digest is recorded, a copy that no longer matches its digest is refused as stale, and no decision is ever
taken against a copy — the gate decides every act against the live record. Memory is not made tamper-proof;
the copy is made tamper-EVIDENT and the decision tamper-IRRELEVANT. (design/25; design/56 §3a.)

## 6. A program before it runs

A program on disk is an ITEM, not an actor — the whole program, folder and all, sealed at installation as one
image under one digest. At that same installation, WITHOUT running it, the system reads the sealed bytes: the
operation names the code references, the regions and object kinds it names. That read — cut against the
maker's shipped declaration (a declaration wider than the code is cut to the code; narrower is kept) and
against the rules of the region it is installed into — yields the program's rule list BEFORE ITS FIRST RUN.
An unmodified Linux program needs no change for this: the read is of what the binary asks of a system, and
what it never declared it can never do. (design/56 §3a; dialogue 10.9–10.13.)

## 7. The load act — how anything becomes an actor

An actor exists only between two rows. When a program starts, a person logs in, an AI opens a session or a
driver binds a device, the system writes one LOAD row: the identity's seal (the image digest, the verified
person, the declared model), the digest of the view computed for it at that moment, and the incarnation's
handle. When it ends, one END row. The stored program files were an item all along; the actor is the
incarnation the load row opens — and it acts only through its two openings, one to the user and one to the
system, every crossing a row. One act, one shape, for every class of actor. (design/56 B1, B7, §3a.)

## 8. Permission — touch points, not inherited authority

What a loaded actor may do is the INTERSECTION of three things: the touch points its installation declared,
the grants the invoking actor actually holds, and the rules of the region the object sits in. A program
started by an administrator holds no more than it declared, and an administrator's grant it did not declare it
cannot use — the old way, where a program inherits the whole authority of its user, is gone. An act outside
the intersection is refused BY NAME and recorded, so a missing touch point shows itself as a refusal row, and
widening it is itself an act by someone holding the grant — never a silent inheritance. (design/56 §3a.)

## 9. Sub-processes, and S against U

Every process a program starts is seen at the gate and born by its own load row; a program that fans out into
many processes is an ORGANISATION of process actors, computed from the load rows, declared by nobody. Whether
an operation is S or U is decided by the OPERATION'S founded cell, never by anyone's claim about the actor: an
ai-class actor is refused at a structured operation whoever ships it. An AI product with an interface half and
a model half is two actors only if it ships them as two processes — inside one process the gate cannot see,
and the split holds only by the installation declaration. (design/56 B4, B5, §3a; dialogue 10.6, 10.8, 10.14.)

## 10. Many machines — the record in chunks, a view on its own machine

The master record may be held as CHUNKS: sealed stretches of its past, each checkable against the anchor row
that sealed it, spread over many machines. What cannot be chunked is the pen: the live tail and the rules in
force stay with the ONE writer. Two machines link their chunks the way the system already speaks to an
outside world — one signed row, one signed receipt, repeatable without harm. And one machine may carry one
view only (the braking machine of a fleet): what travels to it is the gate, that region's sealed rule set
WITH each operation's checks — because "if the checks pass, append citing the law; if not, refuse citing the
rule" is part of the rule set, not of the machine — its chunk, and its own pen; its rows come home by
receipt. A machine missing a check row finds the act undecidable and refuses. (design/56 B16; dialogue 10.1–10.4.)

## 11. Physical things

A physical thing is an item with an identity row and a FINGERPRINT, so the same USB stick is the same item on
whichever machine it appears; a plug-in is a witnessed row. The stick, its driver and the software that drives
it are three different things: the stick an item, the driver information ABOUT driving it, the driving
software an actor that touches hardware. An engine inside a car is containment — parts are items related by
containment rows, so a rebuilt car is the same car or a new one by what the rows say happened, not by opinion.
(design/56 B17; dialogue 10.2.)

## Caps

One hand, 2026-09-17, re-ordering only: sources design/59 Part 1c, design/56 v0.14 (§3a, B16, B17),
design/dialogues/10, design/31 J8 addendum, design/25. Nothing here is built; campaign 8's rows carry the
building. The owner alone grades the flow; his corrections land in the source papers first and here second.
