<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (socket, port, connection, firewall, routing). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=SEED status=RULED-SHAPE supersedes=- superseded-by=- verified=2026-09-02 -->

# GOV-OS — design 44: THE C5 SEED — NETWORKING AS A GOVERNED SUBSYSTEM

**Provenance: the owner's ruling, spoken 2026-09-02 in the architect's chat
("good, go all" on the architect's recommendation that campaign 5 is
NETWORKING, then distribution, then self-hosting), and the dialogue of the
same day. THIS IS A SEED, NOT THE CAMPAIGN PAPER: the paper (archi-doc
standard, nine sections) is written in campaign 4's back half, after C4's
launch re-pricing, on ground C4 has moved — the estate's own timing
precedent (design/37 was written mid-C3). This seed banks what the dialogue
settled so the paper does not re-derive it. Owner rulings control over
everything here.**

---

## 1 — The debt this campaign pays (already on the record)

The connection subsystem is OBSERVE-ONLY today: its op surface is
`['OBSERVE-CONNECTION']` (driven, EP-30-C5's A4, 2026-09-02). The connection
shadow is PROVEN MATURE — sustained shadow-diff ∅ under a named churn
battery, divergence-halt both directions, three red worlds biting — and its
retirement was DEFERRED BY RULING (board :2646) because **no
governed-authoritative connection view exists to retire INTO**; a swap into
a void is a naked swap by another door. **The ledger row is open, honestly,
against this campaign.** C5's first behavior is the one that consummates it.

## 2 — The shape (PROPOSED; the paper decides WHAT, this seed decides
nothing)

- **Sockets as governed grants.** open / bind / listen / connect / accept /
  close become recorded, rule-citing DECISIONS against the actor's record —
  the same classification template applied for the fifth time (files, comms,
  memory, scheduling before it): LAW (policy: who may open what, to where) ·
  DECISION (the grant, the refusal, the close) · INPUT (packets arriving,
  peer state changes) · CACHE (the live socket table — derived, T-CACHE-KILL
  applies) · STREAM (per-packet traffic — never recorded, the memory-fault
  lesson at the wire).
- **The firewall as rules IN the record**, not a table beside it: a
  filtering decision is an act citing a law; the rule set is founding-door
  law like everything else.
- **Routing and name resolution as governed policy** where they are
  decisions, as INPUT where they are the world's facts.
- **The relation to the comms arc, stated so it is not confused:** EP-30-C
  governed CHANNELS between ENTITIES (the two-channel glass box, design/39).
  C5 governs THE WIRE — the kernel's network subsystem the channels ride on.
  Comms is program-to-program law; networking is box-to-world law.

## 3 — The named collision (where derivation stops and discovery starts)

**The other end of the wire is ungoverned.** The internet does not run
gov-os: packets arrive unattributed, TCP state lives in a peer this record
does not govern. The classification derives cheaply; the honest question
does not: *what does a governed record truthfully say about an ungoverned
counterpart?* The border-entity model (design/43 §5: humans and the system
are unboxed but channel-bounded, identity verified AT the tunnel) is the
starting instrument — a foreign peer is an EXTERNAL entity known only by
what crosses the border. **This is spike territory before it is EP
territory** (task-sizing's UNKNOWN tier: timeboxed, findings to a file, code
thrown away).

## 4 — The two-track boundary, held here in terms

**C5 is ONE-MACHINE work.** It governs THIS box's sockets and THIS box's
border with the world. It does NOT federate records, does NOT trust a peer's
record, does NOT admit a second writer — those belong to the
beyond-one-machine track (the charter's two-track ruling, 2026-09-02; the
W4e precedent), which opens with spikes on its own paper and consumes only
C5's RELEASED, SEALED artifacts. **The distribution rider binds C5 as it
binds C4:** nothing C5 builds may FORECLOSE federation — peer identity
expressible, timestamps honest, no design assuming the machine is alone.

## 5 — What C5 consumes from C4 (the reason for the order)

C4's chain and seal (integrity of THIS record), its signing keys (acts
attributable at the border), and constitutional attestation (the primitive
a governed box will later present to another). C5 needs the first two;
distribution needs the third. Building networking BEFORE proof would govern
a wire with nothing provable at either end.

## 6 — The proposed ladder after C5 (PROPOSED ORDER, the owner's to mint)

    C5  NETWORKING       one-machine · pays the :2646 debt · this seed
    C6  DISTRIBUTION     beyond-one-machine · own paper · spikes first ·
                         intake = W4e's six-item travel list + C4 attestation
    C7  SELF-HOSTING     one-machine, the crown · boot as genesis ceremony ·
                         the firmware anchor (design/37 orbit) is its first brick

## 7 — What this seed excludes (honest caps)

No WHAT is settled here: no invariants, no plan list, no tiers, no sizes —
those are the paper's, written on C4's moved ground. The ungoverned-peer
collision (§3) is named, not answered. Deeper device/driver governance,
namespaces/containers, power states are remainders that may attach to C5 or
wait; the paper decides. The difference-technology half of SCOT (design/42,
named-unscheduled) is not kernel work and is not this campaign.

caps: written at one hand in one turn from the day's dialogue; the fold and
the board outrank every line; every figure is a dated taking of 2026-09-02.
