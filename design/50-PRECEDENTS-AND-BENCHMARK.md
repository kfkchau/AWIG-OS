<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: design-seed ·
     Vocabulary is OS-architecture and distributed-systems literature. NON-GOAL: no offensive
     capability of any kind. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=DESIGN status=PROPOSED verified=2026-09-07 -->

# 50 — IS THIS A GOOD SHAPE FOR COMMON USE? Precedents, the benchmark, and an independent assessment

Written at the architect's hand on the owner's word, 2026-09-07 ("is this a
good shape for something aiming to be commonly used? anybody or any work
built for this? assess and benchmark and independent thoughts"). The
subject is the shape stated in design/48 and design/49: an append-only
record of rows (actor, action, object, rule cited, outcome), every state a
computed view, every act crossing a gate that records a rule-citing
decision or refusal, rules as data under a CLOSED check vocabulary, one pen
per record, records related by handshake, the lifecycle's stages as rows.
**Every platform fact below is trained knowledge, uncitable; the owner's
sources control where they differ.** Every judgement is marked PROPOSED.

## 1 — Who built what: the halves exist everywhere, the whole nowhere

The shape is not one idea; it is six, and each half has been built,
adopted at scale, and proven on its own. That is the strongest evidence
that the shape is fit for common use: **the world converged on its halves
independently, over seven centuries, without a constitution joining them.**

| half of the shape | who built it | how common | what it proves | what it lacks that gov-os has |
|---|---|---|---|---|
| **record what happened, compute everything else** | double-entry bookkeeping (journal = record, ledgers = views, trial balance = a fold that can fail), c. 1300 onward | every firm on earth | the oldest append-only record with a check anyone can run | no gate, no rule citation, no refusal recorded |
| the same, in software | event sourcing / CQRS (2000s); "the log is the source of truth" (Kafka, 2011-); Datomic (immutable facts, entity/attribute/value/time — one big table, time-travel views) | enterprise-wide; Kafka in most large estates | one primitive (the append) scales; views are cheap; replay reconstructs | rules live in code beside the log; nothing refuses with a citation |
| **rules as data, executor fixed; decide yes/no fast** | PLC ladder logic (IEC 61131, 1970s-); business rules engines (RETE); policy engines — XACML (OASIS), OPA/Rego (CNCF), AWS Cedar (formally verified), Google Zanzibar / SpiceDB (authorisation as one table of relation tuples) | industry-wide; OPA is the default in cloud estates | **the enforcement carve-out exists as a category**: a decision service, 1/0, with decision logs; Zanzibar is "one big 2D table as the rulebook" at planet scale | the rule language grows into a programming language (XACML died of it; Rego is one); no constitution governs the rule-making; decision logs are not the record of truth |
| **every act under an explicit grant** | capability systems — seL4 (formally verified kernel), Fuchsia/Zircon (everything by handle), CHERI (capabilities in hardware) | seL4 in certified devices; Fuchsia shipping | "the rule decides once, the fast path runs under a recorded grant" is exactly a capability; seL4's proof is the standard for it | the grant is not a row in an append-only record; no rule cited; no lifecycle |
| **append-only, hash-chained, verifiable without the engine** | Git (content-addressed DAG; many independent implementations: libgit2, JGit, go-git, dulwich); Certificate Transparency / Trillian / Sigstore-Rekor (Merkle append-only logs with WITNESSES and gossip) | Git: the most used developer tool on earth; CT: every browser | **grammar without engine wins**: a .git directory is readable by anything; CT's witnesses are the diving-buddy (design/47 §4) already deployed at internet scale; Merkle inclusion verifies in milliseconds | no actors, no rules, no refusals; Git has many pens by design (merge), which is the construct we deferred |
| **many pens on one record** | blockchains / smart contracts (Ethereum), permissioned ledgers (Hyperledger Fabric: endorsement POLICIES = rule-cited approvals; chaincode) | large but costly | rule-as-code on a shared record works; Fabric's endorsement is the nearest thing to a rule-citing gate | the cost of consensus; rules are code; no meta-rules; gov-os deliberately did not mint this (W4e) |
| **rules-as-code for law** | Rules as Code (NZ, OpenFisca — French benefits law executable; Catala — tax law formally specified) | governments, small but real | law can be data an executor runs; the human text and the executable stay paired | no record of acts; no enforcement; no lifecycle beyond the text |
| **replay to recover; determinism** | state-machine replication (Lamport, Schneider), Raft; durable execution (Temporal); TigerBeetle (an append-only, deterministic, single-writer ledger database, 2022-) | Raft under most distributed stores; TigerBeetle in payments | ONE PEN PER RECORD is what the field converged on (Datomic's transactor, Kafka's partition, TigerBeetle's replica): the owner's D08.22 ruling is the industry's | none carries a gate or a rule |

**The assembly — capability-style gate + rule-citing refusals in the record
+ rules as closed-vocabulary data + witnesses + the lifecycle's stages as
records + a constitution that governs its own rule-making — has, as far as
trained knowledge goes, not been built.** The closest single artefacts are
Hyperledger Fabric (permissioned record + endorsement policy) and OPA with
decision logs (decision service + record of decisions). Neither has
meta-rules: neither can say, from its own record, under which rule a rule
was made. That is the owner's core stance (rule metabolism; OMGS) and it is
the part with no precedent.

## 2 — The benchmark: what made the common ones common

Read across the rows above, the systems that became common share five
properties. This is the benchmark, and gov-os is scored against it.

| property of the common ones | example | gov-os today | verdict |
|---|---|---|---|
| **one primitive** | the log (Kafka); the commit (Git); the journal entry | the row | MET by design |
| **verifiable without the vendor** | trial balance; `git fsck`; CT inclusion proof | the air rider, sentence 1; checkpoints verify without the engine (EP-44) | MET in law, one implementation only |
| **cheap to join, free to leave** | a producer is 20 lines; a git clone is the whole record | the air rider, sentences 2-3; the handover ceremony | MET in law, no second implementation |
| **a standalone grammar spec** | the Git object format; the Kafka protocol; Rego's spec; the CT RFC | the grammar lives in code + papers; no one-page spec exists | **NOT MET** |
| **published numbers** | OPA latency; TigerBeetle tx/s; seL4's proof; CT's Merkle proof sizes | C3's batching band and two speed tensions; nothing else | **NOT MET** |

Score: three of five met by design and law; the two unmet are **documents
and measurements, not architecture**. That is the answer to "is it a good
shape": the shape is what the common ones have; what is missing is what the
common ones published.

## 3 — Independent assessment (PROPOSED; cost if wrong stated)

1. **The common shape will be ACTOR and STAGE MACHINE, not FULL BODY.** Kafka
   has few brokers and countless producers; Git has one grammar and many
   tools. gov-os will be common the same way: many things writing rows, a
   few bodies keeping records. Consequence: the exposing stream (AIR) leads
   with the row writer/verifier, not the engine — which is what the owner
   already ruled (D08.1, design/48). Cost if wrong: an engine-first launch
   that nobody can join cheaply.
2. **The closed check vocabulary is the rarest and most valuable choice, and
   it will be the most attacked.** Every rule language that opened became a
   programming language and died of it (XACML) or became code (contracts,
   Rego). gov-os refuses an unknown check kind at definition time (opdefs).
   Adoption pressure will ask to open it. Hold it closed; grow it only by
   owner-gated members, as today. Cost if wrong: the rulebook becomes a
   program and the "one big 2D table" claim dies.
3. **Recorded refusals are the genuine advance.** Institutional analysis
   (Ostrom) warns that rules-in-form differ from rules-in-use; no policy
   engine records the rule-in-use because none records the refusal with its
   citation as part of the truth. gov-os does. This is the thing to show
   first to a governance audience; it is also what OMGS's monitoring stage
   consumes for free (D08.28).
4. **One pen per record is not a limitation to apologise for; it is the
   consensus of the field.** Datomic, Kafka, TigerBeetle all chose it; the
   many-pens world (blockchains) pays consensus for it. The deferral of the
   many-writers construct (W4e) is correct and should be stated as a
   position, not a gap.
5. **Every-act-recorded meets privacy and retention law head on** (erasure
   rights vs append-only). CT survived it by recording hashes, not content;
   gov-os already has the same answer (content blob-homed by hash, the
   erasure shell, custody conservation as handover). Name it in the public
   material before a reader names it first.
6. **The part with no precedent needs its own proof.** Meta-rules — the
   record showing under which rule a rule was made — has no benchmark to
   borrow. The proof is the estate's own record: the constitution's version
   history, each move an owner-worded, hash-bound, rule-cited row (1.33 →
   1.38 this week). That history IS the demonstration; it should be
   rendered as one page for readers.
7. **Python-only is the largest practical gap for common use**, larger than
   any architectural one. Git won on many implementations. A second
   implementation of the row writer/verifier (any language) is worth more
   than any feature.

## 4 — The four numbers to publish (the benchmark's price of entry)

Common systems became credible by publishing a small number of figures.
These four, driven on this estate, would put gov-os on the same footing;
none needs a redesign, and none is minted here (D08.25).

1. **rows appended per second** on one machine, one pen, group commit —
   against Kafka's single-partition figure and TigerBeetle's.
2. **decision latency of the enforcement carve-out** for one compiled rule —
   against OPA's simple-policy latency; the same measurement D08.30 owes.
3. **verify-without-engine time** for a record of one million rows, and the
   size of a Merkle localisation proof — against a CT inclusion proof.
4. **the smallest RAM at which a chained append still runs** — against an
   RTOS footprint; the line design/48 §5 draws in words.

## 5 — Honest caps

Trained knowledge throughout §1-2; no source read this turn; the owner's
own reading of any named system controls. "Common" is judged from
adoption as trained, not measured. The assessment does not price the
seven items; it names them. Nothing here changes the ladder.
