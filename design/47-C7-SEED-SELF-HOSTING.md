<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture (boot, firmware, kernel, driver, attestation). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and ceremony conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=SEED status=RULED-SHAPE supersedes=- superseded-by=- verified=2026-09-05 provenance=D07.8,D07.9,D07.10,D07.11 -->

# GOV-OS — design 47: THE C7 SEED — SELF-HOSTING

**Provenance: the owner-archi dialogue of 2026-09-04/05, recorded at
D07.8–D07.11 (design/dialogues/07), and the owner's word 2026-09-05
("If 1 and 2 is ready, write and announce"). THIS IS A SEED, NOT THE
CAMPAIGN PAPER — the paper (archi-doc standard, nine sections) is written
when C7 approaches, on ground the intervening campaigns will have moved.
This seed banks what the dialogue settled so the paper does not
re-derive it. Owner rulings control over every line.**

## 1 — The shape (owner's frame, canon: SWAP THE CORE)

C7 is a performer-swap, not a rebuild. The seam C3 built (src/bridge/,
the syscall port) already separates what gov-os asks for from who
performs it; today Linux performs. C7 replaces the performer beneath the
seam — "remove linux core, replace by our core, all will continue to
move" — and nothing above the seam changes. Portable is NOT
general-purpose: the swap changes WHO performs, never widens WHAT is
performed (the acts our machines actually use: one disk, one network
connection, one clock).

## 2 — The two witness classes (D07.8, the paper's load-bearing law)

- **Witness-the-code:** read the thing whole, line by line, sign it.
  REQUIRED for whatever hosts the gate — the host of witnessing cannot
  be act-witnessed, because it runs the witnessing.
- **Witness-the-acts:** interior opaque, every effect crosses the gate
  as a row. The class of every entity — humans, AIs, and borrowed
  driver code alike.

C7's correct form is the COMPOSITE: a code-witnessed tiny core beneath
(small enough to read whole and sign — ours, or an existing verified
kernel consumed as a sealed artifact; the choice is the paper's first
question and the owner's word), act-witnessed borrowed workers above,
and NEVER opaque code inside the signed base. Stretch warning, banked:
an enclosure exists only to perform declared seam-acts; any other opaque
thing wanting in is a new entity at the front door.

## 3 — Genesis as the standing guardian family (owner's ruling, D07.9)

**Memory constructs identity** — the owner's ruling-class view, and this
estate already obeys it by construction: no self is stored anywhere;
every view and authority is computed from the record, so identity
re-derives from memory, wholly, at every waking. Therefore every on/off,
sleep/wake, crash/recover transition is a GENESIS FUNCTION — genesis is
not first-legitimacy only but the standing guardian of the system's
identity-and-memory across every gap in consciousness. This unifies as
ONE FAMILY: the boot ceremony (C7), recovery (EP-43 — waking damaged),
checkpoint views (EP-44 — prepared waking-points), and attestation
(the body-check). ARC R is authored under this frame.

**The wake checklist** (the mechanical meaning of "it knows it is sane
and not crazy"): (1) verify its own body first; (2) verify record
integrity, hash chain end to end; (3) confirm the constitution loaded,
read back exact; (4) rebuild memory into working shape — views fold
fresh, no cache survives sleep on trust; (5) re-derive who it is — own
keys valid, account chain intact; (6) only then the first act as an
actor.

## 4 — The diving-buddy genesis (owner's design, D07.10, canon)

The self-attestation floor ("can an insane person check if they are
sane?") is escaped by PAIRING, not cleverness: two witness processes
with two separate bodies — one in the chip's own memory, one on disk —
each verifies the OTHER's genesis is clean, then each checks the other's
genesis code-and-data against its own copy. The genesis row records BOTH
witnesses' mutual verdicts: the start-up signature is a MUTUAL RECEIPT,
never one signer's claim. This is the owner's
diversity-of-perspective-with-separated-powers at the smallest scale the
machine holds — and it is the same mechanism as EP-45's cross-attested
checkpoints and C6's box-to-box attestation, at three sizes.

**Scope, owner-ruled 2026-09-05: the chip carries the GENESIS PART ONLY**
— the checker plus what verifying needs (digests, the anchor key), never
the constitution. Forced twice over: the chip body must satisfy
witness-the-code (small enough to read whole), and the constitution
lives ONCE, in the record — verified, not duplicated; a second full copy
is a second truth that can drift.

**Requirements and caps, stated:** the two bodies must never share a
write-path (one hand writing both defeats the pair — common-mode
failure); beneath both still sits the chip's maker. Smaller floor,
never no floor.

## 5 — The driver cut (owner-ruled: supply, never own — "like water,
like air")

The translator impersonates ONLY the common driver services — the
narrowest waist in the stack — and everything above it (the bus layer
AND the drivers, borrowed code of the same kind, written against the
same toolbox) comes in together as enclosed workers, unmodified.
**The enabling law, the owner's words as canon: "we are not moving the
whole ecosystem under us, we are supplying the whole ecosystem — like
water, like air; everybody needs them, but air and water doesn't own
everybody."**

Record management is fully retained and fully invisible to the borrowed
code: every grant and refusal lands at the estate's own standard (actor,
action, object, target, rule cited), while the workers see only their
native language — a grant is the service performed, a refusal arrives as
the ordinary failure answer the code already handles. Device discovery
becomes a row (a device appeared, matched to its driver) — recorded,
where today it is silent. The toolbox slice is DRIVEN from the narrow
device list's real calls, never built general.

## 6 — What this seed excludes (honest caps)

No WHAT is settled: no invariants, no plan list, no tiers, no sizes —
the paper's, written near C7 on moved ground. OPEN by name: (a) the
core's provenance (build narrow vs consume a sealed verified kernel —
the owner's one-way door); (b) whether the driver-translator work homes
in C7 or attaches earlier to C5's device remainders; (c) the
no-Linux-assumption rider (D07 item 4) — HELD at the owner's word until
this dialogue thread finishes, then written as one sentence of law.
The two-track law binds C7 as it binds everything: one-machine work,
consuming only sealed released artifacts from other streams.

caps: written at one hand from D07.8–.11; the dialogue records carry the
owner's verbatim words; the board and the fold outrank every line.

## 7 — AS-BUILT (2026-09-05, same day): §6(c) DISCHARGED

The no-Linux-assumption rider was RULED the day this seed was written —
the owner's "okay accept, go" (D07.12). It lives in the charter as THE
NO-SILENT-LINUX RIDER, binding all streams from 2026-09-05. Open items
remaining in §6: (a) core provenance (the owner's one-way door), and
(b) the translator's home (C7 vs C5's device remainders).
