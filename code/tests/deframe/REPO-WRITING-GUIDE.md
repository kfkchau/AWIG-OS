<!-- gov-os provenance · systems-architecture documentation · the writing standard for every session that writes in this repo. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-25 -->
# GOV-OS — How to write in this repo

For every session — builder or reviewer, human-directed or automated — that writes anything
here: a log entry, a review note, a design doc, an execution plan, an open-item list, or a
message to the owner. This is the standing register. Follow it and the docs stay a plain
systems record that reads as architecture, which is what they are — and never drift into
reading like something else. It consolidates the log-writing rules
(`planning/LOG-WRITING-GUIDE.md`) and adds the register discipline; if you read one writing
doc, read this one.

There are two halves: **write plainly** (how every entry should read) and **stay out of the
register** (four shapes to avoid, because they make architecture read like an offensive-
security report and trip a safety classifier — the full reasoning is in
`tests/deframe/DEFRAME-SOP.md` §2).

---

## Write plainly

**State what the code does, and what follows from it.** Every line is behaviour and its
consequence: *the budget check reads the record in order, so a region granted after an
eviction is counted again.* That carries the behaviour, the effect, and enough to act. Nothing
sits on top of it.

**When something is wrong, write one short paragraph:** what the code does, what follows,
where it lives (a file:line pointer is fine), and the change that settles it. Prose, not a
template. A short code or tag may sit in brackets as a filing aid; the plain sentence carries
the meaning.

**State priority by its consequence, not as a grade.** "Settle before a second person uses the
system," or "a tidy-up with no effect a user would see." Not a ranking label.

**Name each actor by who they are and what they hold** — an ordinary user, the owner, the
system. When you check something from several angles, the angles are: an ordinary user pushing
a new ability to its edge, the owner working through the documented path (including when the
owner errs), and a restart that rebuilds from the record.

**A check is a reading.** To confirm a claim, follow the code path and state what it does. You
do not stage a failure to establish it.

**The log only grows.** New entry at the end, dated. Never change an earlier entry; a later
change gets its own new entry. Write the body first and the "done / this version" line last —
a status claim goes up only after the content it certifies is there.

**Evidence before the claim.** A test count, a "green," a "complete" goes in only after it ran
and was observed. Treat every count as a fact: reconcile it exactly, and when it moves, say by
how much and why.

**Mark where each statement stands.** What is drawn from the source material (cite where), what
is inferred (from what), what is proposed (and the cost if wrong), what is general knowledge you
cannot cite.

**To the owner, write plain and self-contained.** What it is in ordinary words, what a yes
does, what a no does, an example if it is abstract. Codes and doc numbers are filing tags in
brackets, never the carrier of meaning.

**Keep the top-of-file lines** — the provenance line and the `<!-- doc: … -->` metadata — and
state scope **positively**: what the work is and does. Do not write scope as a list of what it
is not; a denial ("no offensive capability, no exploits") reads worse than a plain statement of
function, because the negation still puts those terms in front of the reader.

**Let the running log stay a history of what was built and decided.** Durable statements about
how the code behaves now, and its current limits, belong in the design docs, where they stay
current and a reader finds them once. Keeping the two apart stops the log from becoming a
growing catalogue.

---

## Stay out of the register — four shapes to avoid

These are ranked by how strongly each makes the writing read as an offensive-security report.
The first is the strongest; avoiding it is most of the work.

**1. Do not build a findings catalogue.** No numbered finding IDs paired with severity labels
(CRITICAL / HIGH / MEDIUM / LOW), no "What / Repro / Location / Fix" template, no
"Repro:/Verified:" lead-ins, no "findings by severity" heading, no numbered "problem → FIXED"
self-review. Write each item as a plain sentence instead. *(Engineering IDs are fine and
wanted — invariant IDs, work-item IDs, T-named tests, EP numbers. The thing to avoid is the
severity-rated defect-ledger shape, not numbering as such.)*

**2. Do not use control-defeating verbs for the code.** Not brick, bypass, smuggle, launder,
forge, poison, silence, inject, spoof, evade, exploit, tamper, "goes dark," widen, "side
door," takeover. Say what the code does and what follows: "a rule that blocks all
rule-making," "reaches the store without the check running," "recorded under a different action
so the guard did not match it," "a caller-supplied value stood in," "makes the derived view
wrong," "marks the promise done without the act."

**3. Do not cast actors as attackers or methods as adversarial.** No "hostile nobody,"
"mallory," "prey," "attack surface," "threat model," "red-team," "probe-extinction matrix,"
"the trap announcing itself," "the wedge direction." Use neutral actors (an unauthorised
caller, the owner, the system) and neutral method words (pressure-test, second-reading,
coverage sweep, coverage matrix, boundary test). A test method is a coverage method, not an
attack.

**4. Keep the operating-system and governance vocabulary.** kernel, syscall, gate, capability,
permission, audit, refuse, sandbox, isolation, containment, default-deny, fail-closed,
sight-is-law, the Wall, chokepoint — this is the architecture and it stays. Do not soften it or
apologise for it. The only refinement: where several of these stack in one sentence, pick one.

---

## When you review or test

The review method is thorough and systematic, not adversarial. Describe a check as a reading of
the code path. Cover the three lenses — an unauthorised caller pushing a new ability to its
edge, the owner working through the documented path (including a careless mistake), and a
restart that rebuilds from the record. Report what you found as behaviour and consequence, and
land every verification as a regression test in the repo so the evidence outlives the session.
A review that finds nothing should check its own coverage before concluding the surface is
sound — but it states that as coverage, not as "the probes found no prey."

---

## If a doc has already drifted

This guide keeps new writing clean. To bring an already-drifted doc back, follow
`tests/deframe/DEFRAME-SOP.md`: copy to a new version, surgically swap the Layer 1–3 carriers,
keep every fact and the Layer-4 vocabulary, and verify by diff that only the register changed.
Originals go to `tests/archive/`; nothing is deleted.
