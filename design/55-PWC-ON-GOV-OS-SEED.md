<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (OS-textbook: actors, capabilities, gates, signed records) · Vocabulary is governance-as-OS (actor class, operation, rule, key, signature, the record). NON-GOAL: no offensive capability — this describes how a second governed program (pwc) is hosted on gov-os so that every act it asks for is recorded, gated and signed; it attacks nothing. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=SEED status=DRAFT supersedes=- superseded-by=- verified=2026-09-12 provenance=owner-archi chat 2026-09-12 -->

# GOV-OS — design 55: THE PWC-ON-GOV-OS SEED — TWO GATES, ONE CHANNEL

**Provenance: the owner's two questions in the architect's chat, 2026-09-12, and the
architect's answer the same turn. THIS IS A SEED, NOT A CAMPAIGN PAPER: it fixes the
shape so a later campaign (after C7) can be cut from it. pwc and twc are one thing under
two names (owner, same turn). `apps/pwc-app` is READ-ONLY to every seat here; nothing in
this seed edits it.**

## 1 — The owner's two questions (his words, compressed as he wrote them)

1. pwc processes only the user's data; everything is air-gapped; anything user- or
   system-facing enters as a text string only — is that the right shape, given gov-os
   enforces permission at the system level by actor (system, program, user, AI)?
2. The channel from pwc to the system is shared and passes through the system-facing
   team and the Controller. How is it controlled? Does each thing on it need a
   fingerprint or hash, so the system-facing Writer bot cannot help but carry a
   system-level mark that it may only run edit-level commands (never install a program
   or change config)? How does the system know a command is Controller-approved? His
   picture: **two gates per channel — one at the pwc end (from), one at the system end (to).**

## 2 — The shape, in gov-os's own terms (what already exists)

- **pwc's bots are actors of the AI class in gov-os's record.** The cell law (design/52
  L28; `gate.py` the (actor class, task cell) pairing) pairs actor class with operation: an
  AI-class actor at an operation outside its class's cells is refused at the gate, by name.
  So the operations open to pwc's bots are exactly the text-in / text-out ones, and nothing
  else, as a rule in the founding — not as a promise in pwc.
- **Text-only at the door is already a field-kind check.** An operation whose parameter is
  declared `text` refuses raw bytes before its handler runs (`opdefs.PARAM_KINDS`; CREATE-INFO
  carries it in code). pwc's inbound rows declare their payload text; a non-text payload is
  refused by the definition, not by pwc.
- **The air gap is an absence, not a wall.** pwc performs none of the twelve kinds of work
  (design/54 P3's rows of law: the record pen, a write-once file, a removal, the one-writer
  invariant, the clock, the wait, entropy, threads, the one connection, the body read, the
  founding-pack read, memory). It asks gov-os; gov-os records the ask and performs or refuses.
  Nothing pwc holds can reach a file, a clock, a socket or a random byte except as a row
  through the gate.
- **The from-gate exists in pwc** (`pwc-constitution-v4.md` §2.14, §9.1): the Controller
  grants a Window opened by a Key whose hash is in pwc's record and whose plaintext is
  delivered once, the whole grant-chain (the Ticket) tied to the Task whose endorsement
  releases it.
- **The to-gate exists in gov-os**: the gate itself. Every act is an operation, citing a
  rule, signed by the actor's key (`_signed_content`); the store's own signature covers the
  recording; the chain covers the whole record. Since C6a, a row can carry **stamps** — a
  gate-added field inside provenance, covered by the chain — and the founding policy rule
  **REQUIRED-STAMPS** (`gate.py:240`, founding 1.54.0) refuses an act of a class that lacks
  the stamps the rule requires.

## 3 — The join (what does NOT exist yet, and is the whole of the work)

**The Controller becomes a signing actor in gov-os's record.** Today pwc's Controller signs
into pwc's record and gov-os's gate reads gov-os's record; the two never meet. The join is:

1. **Keys.** The system-facing Writer bot and the Controller each hold a gov-os key (the
   key ceremony machinery of campaign 4; the vault seals, never reveals). Their actor rows
   carry their class (AI) and their cells.
2. **The command as a row.** The Writer's command to the system is an act: an operation
   (from the edit-level set its cell admits), citing a rule, signed by the Writer's key.
   An install or a config change is not an operation in its cell; asked for, it is refused
   whoever signs.
3. **Controller approval as a stamp.** The Controller's okay travels as a stamp on the
   same row (the C6a mechanism, unchanged), and a REQUIRED-STAMPS policy row names the
   command classes that require the Controller's stamp. A command lacking it is refused at
   the to-gate; the refusal is a row.
4. **The channel stays shared.** Identity is the signature, never the wire. Two bots on one
   channel are two keys; a message with the wrong key, or no stamp, is refused regardless of
   which end it came from.
5. **Three signatures on one row = the owner's "multi-fingerprint".** The Writer's (the
   content), the Controller's (the stamp), the record's own (the recording fact) — each
   covering a different thing, as ruled at VT-6d (board :3869).

## 4 — What the owner's picture gets exactly right, and one cap

- Two gates per channel is the correct shape and it is **two records, two gates, joined by
  one stamp** — not a new protocol on the wire.
- **Cap:** "text only" is necessary, not sufficient. A string can carry an instruction. The
  rule that holds is: text from a user is **content**, never an act. An act is an operation
  citing a rule signed by a key; no string becomes one by being read. pwc's Input-refining
  team reads strings; only a keyed actor at an operation makes a row.

## 5 — What stays the owner's

- Whether pwc moves onto gov-os's record at all (a one-way door for pwc's own record).
- The Controller's key ceremony (who holds the plaintext once).
- Which command classes require the Controller's stamp (a policy row he words).

## 6 — Honest caps of this seed

- Nothing here is built; `apps/pwc-app` is read-only here and was READ for §2's pwc facts
  (§2.14, §9.1 of its constitution v4), not executed.
- pwc's own Window/Key/Ticket is a separate mechanism from gov-os's stamps today; the seed
  proposes the stamp as the join and says nothing about retiring pwc's mechanism.
- The campaign is after C7 (the estate's live campaign is our own kernel).
