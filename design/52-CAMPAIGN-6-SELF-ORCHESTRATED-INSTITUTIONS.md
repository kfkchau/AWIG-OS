<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: design-paper · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (record, gate, view, border, receipt, handshake, stage row, key, signature). NON-GOAL: no offensive capability of any kind; defines record, gate, view and border across many bodies only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=DESIGN-PAPER status=ACTIVE verified=2026-09-09 -->

# 52. CAMPAIGN 6: SELF-ORCHESTRATED INSTITUTIONS (the campaign paper). ACTIVE v1.0 from the C5 close, 2026-09-09 (board C6-PAPER ACTIVE line of that date); the owner gates in §9 ride their plans and none blocks the spikes

**First cut, drafted from the intake `planning/exec/C6-PAPER-INTAKE.md` (218 lines, twelve conflicts, eight owner questions, the owner's 2026-09-09 input at its §9) and from the dialogue law it points at (`design/dialogues/08-air-ecosystem.md` D08.49 to D08.56). Form: the campaign-paper shape of design/51 with the sections the archi-doc standard names. Every line carries its label; a cite of the form `intake:N` is a line of the intake, a cite of the form `D08.N` is a paragraph of the dialogue read whole, and a cite of the form `intake:N citing D07.N` is carried through the intake without the dialogue being reopened here. The board and the fold outrank every line the moment this is committed.**

## 1. HEADER

    CAMPAIGN: 6, SELF-ORCHESTRATED INSTITUTIONS
    STATUS: ACTIVE
    VERSION: v1.0
    VERSION LOG: v0 first cut drafted at the architect's seat by a background hand, 2026-09-09; v0.1 revised at the architect's own hand the same day (K2's defining behaviour ruled; N4/N9's review grading and the chain-hash acceptance driven in; §11's two identity words corrected to Q9's); v1.0 ACTIVE on the C5 close (DIGEST-C5 §7, board :3560 and the CLOSED line), same day — content unchanged from v0.1; GREEN and UNKNOWN(spike) rows of §7 are pre-approved for detail and dispatch; RED rows wait on their §9 gate; the caps of this paper stand as written and the charter re-read is owed by the architect at the first as-built sync.
    LAST-AS-BUILT-SYNC: none (campaign not started)
    STANDING ORDER: board :3463, the owner's "keep going if c5 finishes move to c6 auto": C6 starts when C5's last unit closes, without waiting [SOURCE-DERIVED: intake:15-16]
    PREDECESSOR: design/51 (campaign 5, NETWORKING); design/44's "DISTRIBUTION" is this rung under its older name, superseded [SOURCE-DERIVED: intake:154; design/51:106]

## 2. OUTCOME, in the owner's language

Today one box keeps one record and proves it, and two boxes can pass one row across a wire with a receipt. At the end of this campaign a second box is born as the child of the first: at its founding it names its parent's key and the exact version of the parent's rules, holds a sealed copy of them, and checks that copy as its first waking act. When the parent writes a new rule into its own record, the sealed rows travel to the child; the child checks the signature and the version at its own hand, records that they arrived, and changes nothing until its own act adopts them, naming the parent rule by its fingerprint. The parent cannot write a single row into the child's book; if it wants to read the child's book it asks through the child's front door and the child records the read under its own law. Two machines that both claim to be, say, the immigration-law decider for the same scope are refused at the moment they meet, not discovered later. Burn the parent's machine and the children together hold every rule anyone was ever bound by, signed, and the parent's constitution is rebuilt from them. There is no bigger machine above the boxes deciding any of this: each institution orders itself from within and orders its relations between, never from above. [SOURCE-DERIVED: intake:24-29, intake:58-63 citing D08.14 to D08.16; intake:65 citing charter:256-258]

### 2b. Why, in the owner's theory (what C6 makes possible that C1 to C5 do not)

- Rule metabolism becomes measurable across institutions, as propagation with receipts. [SOURCE-DERIVED: intake:33 citing D07.7]
- Diversity of perspective with a guaranteed say becomes structural: "a say hosted on another's machine is revocable, a say at your own hand is not". [SOURCE-DERIVED: intake:33 citing D07.7]
- Customary and non-Western rule systems are first-class without assimilation: a shared grammar, never a shared law. [SOURCE-DERIVED: intake:33 citing D07.7]
- Enforcement theatre is computable link by link across bodies; the no-dark-age property holds at civilisation scale. [SOURCE-DERIVED: intake:33 citing D07.7]
- "C1-C5 build a governed being; C6 makes a governed SOCIETY of them possible." [SOURCE-DERIVED: intake:33 citing D07.7]
- The real-world selector: sealed commits re-verified at the receiver's hand; custody handover between hospitals; an export certificate across sovereign borders; "wherever today there are stamps, certified copies, notaries, apostilles". [SOURCE-DERIVED: intake:34 citing D07.4]
- One mechanism at three sizes: the process pair at boot, checkpoint cross-attestation within a machine, box-to-box attestation here. [SOURCE-DERIVED: intake:36 citing D07.10]
- The limit C6 lifts: authority that ended at the socket, institutions of many bodies that got no help, AI-to-AI relations that stayed ungoverned; beyond an operating system, institutions of humans and AIs as stage machines under one constitution, records relating without a vendor. [SOURCE-DERIVED: intake:37 citing D08.37]

### 2c. What deliberately does not enter (the minimality gate; each refused by name in the sources)

- Not federation, not a second writer on one record, not a peer's row as this record's decision (the word "trust" is K10's). [SOURCE-DERIVED: intake:40 citing design/51:108]
- Not one bigger machine, not a gate above the boxes. [SOURCE-DERIVED: intake:41 citing D07.3]
- Not one book on one operator's machine with one hand and one throat. [SOURCE-DERIVED: intake:42 citing D07.4]
- Not many pens on one record: a mesh is many records, never one record with two pens. [SOURCE-DERIVED: intake:43 citing D08.13]
- Not a blockchain: no global agreement, no consensus cost, no tokens. [SOURCE-DERIVED: intake:44 citing D08.36]
- Not a merge: consolidation only by handover; ledgers and smart contracts are peers that relate by handshake. [SOURCE-DERIVED: intake:45 citing D08.22, D08.31]
- Not a manager of machines; the second virtual machine stays parked until after C6 and only on the owner's word. [SOURCE-DERIVED: intake:46 citing D08.25, charter:228-232]
- Not discovery: the host declares, gov-os never discovers. [SOURCE-DERIVED: intake:47 citing D08.12]
- Not a registry or issuer of names. [SOURCE-DERIVED: intake:48 citing D08.42, D08.43]
- No new row field (a stage is a kind of row); no delete in any new vocabulary; no group object, member list, per-datum label, access list, class that grants, or inheritance of power. [SOURCE-DERIVED: intake:30, intake:91; D08.52 "What is NOT added"]

## 3. TARGET BEHAVIOURS (numbered; each one sentence; each testable by a demo step or a command the plan names)

What C5 proved, so that each behaviour below names what it adds: one row crossing host to guest with a receipt, two chains, one pen each, the receipt citing (key, genesis hash) [SOURCE-DERIVED: intake:54-56; design/51:30].

- **B1 THE TREE.** A child founded pinning its parent (identity and rule set at a version and hash, a sealed copy verified at genesis) checks that copy as its first waking act, and when the parent appends to its own record the sealed segment travels, the child's gate verifies it and records a receipt, and nothing in the child has changed. [SOURCE-DERIVED: intake:58 citing D08.14:224-226, D08.15:247-251]
- **B2 AUTO-RECEIVE, NEVER AUTO-CHANGE.** A standing founding rule admits rows signed by the pinned parent's key as INPUT (verified, recorded); each child declares whether it adopts automatically or only by its own decision, both lawful, the row recording which; either way the change lands as the child's own act, and the update is a row with no reboot. [SOURCE-DERIVED: intake:59 citing D08.15:252-258, D08.27:520-524]
- **B3 THE HANDSHAKE, THREE CHECKS, MUTUAL.** Two bodies meeting each run WHO (signature against the pinned or attested key), BODY (attestation digest: founding version plus running-code digest) and MEMORY SANE (chain head plus proofs), at one of three disclosure levels (HASHES ONLY, SHELLS, FULL); admission is graded, never refused outright when any check passes, and the record says which checks passed. [SOURCE-DERIVED: intake:60 citing D08.17:293-303, D08.18:316-322]
- **B4 RULE CITATION ACROSS RECORDS.** A child's act cites the parent rule it obeys by (record-identity, rule-hash), where today a cited rule names only a rule in the same record; conditional on Q4. [SOURCE-DERIVED: intake:61 citing D08.14:234-236]
- **B5 HOLD EXACTLY WHAT BINDS.** Every parent rule the child was ever bound by lives in the child's own record as received parent-signed rows, so the cited rule is always local, the active constitution is a view over received rows, "what bound me at T" replays locally forever, and history from before the child's birth is a request through the parent's front door. [SOURCE-DERIVED: intake:62 citing D08.16:266-275]
- **B6 THE CONSTITUTION SURVIVES ITS MACHINE.** With the constitution machine destroyed, every child holds signed, chain-verified segments; reconstruction is gather, verify against the parent key, union; what is lost is only rows nobody was ever bound by. [SOURCE-DERIVED: intake:63 citing D08.16:276-282]
- **B7 STAGE ROWS CROSSING MACHINES.** The eight stages of the rule lifecycle are kinds of row that cross by handshake (announcement is the rule row propagated; reporting is a submission row into the decision machine's inbox; monitoring is views over enforcement records; analysis is a separate record, proposals only; environment change is rows by non-body actors; communication is not gov-os's), and rule metabolism is measurable per stage as the time between a row's arrival at one machine and its arrival at the next. [SOURCE-DERIVED: intake:64 citing D08.28:545-580; the mapping is "a first derivation for the owner's correction, not law", intake:64]
- **B8 ONE MACHINE PER STAGE PER SCOPE, CHECKED AT THE HANDSHAKE.** A machine's pack declares the stages it holds and their scope, and a second machine claiming a declared stage for the same scope is refused when the two meet; an AI may hold a stage but never decision, enforcement and monitoring together; conditional on Q2 and on the K6 decision. [SOURCE-DERIVED: intake:65 citing charter:256-258, D08.37:812-814]
- **B9 READING AS A GOVERNED ACT.** An outside institution reads through the asked institution's own gate and the read is a row under the asked institution's law; upward accountability is asking the child's front door for its sealed record, never reaching in. [SOURCE-DERIVED: intake:66 citing D07.5:53-57, D08.14:231-233; the cap is K7]
- **B10 MANY RECORDS PER MACHINE, ONE PEN EACH.** Every record declares its scope as rows; a new install finds records present and handshakes; records write relation rows about each other; a scope overlap is detected by the same-frame rule and resolved by a declared relation in both, never by silent double-governance. [SOURCE-DERIVED: intake:67 citing D08.22:386-401]
- **B11 HANDOVER BETWEEN INSTITUTIONS.** Consolidation runs design/46's ceremony (duplicate the chain, byte-verify, a signed receipt from the receiving hand, remove the local bytes, shells stand, a departure record), and never a merge by copy. [SOURCE-DERIVED: intake:68 citing D07.4:42-43, design/46:36-62]
- **B12 UNLINKABLE PER-PEER KEYS AND ZERO-KNOWLEDGE PREDICATES.** Two peers cannot join the roots of one actor's identity tree, and a predicate ("version at or above a value", "a human") is proven without the value; both over the tree C5 built with DISCLOSURE-BY-LAW. [SOURCE-DERIVED: intake:69 citing D08.48:1161; D08.48 read whole]
- **B13 HONEST STATE ACROSS AN UNGOVERNED BOUNDARY.** A stale picture of a peer reads as stale, and a four-tuple names a socket, never an entity. [SOURCE-DERIVED: intake:70 citing SPIKE-1:115-119]
- **B14 THE TWO-CLOCKS LAW.** Named as one of the three missing pieces; no source read gives its content; the nearest law is "timestamps honest" and the corpus's two times per relation. [INFERRED: from intake:71; the content is C6's own to settle, see §9]
- **B15 THE RECEIVING VOCABULARY.** What row a received segment of many rows writes, where C5 minted RECEIPT for one row and segments are sealed, content-addressed, their hashes held in the chain. [INFERRED: from intake:72 citing D07.3:35, design/51:42, D08.13:194-197]
- **B16 ACTOR CLASSES AS BANDS.** Human, AI and program are labels over two declared capabilities (may be the arm of a structured rule, may be the arm of an unstructured rule: human both, AI unstructured only, program structured only); the cut bounds who executes a rule, never who may ask. [SOURCE-DERIVED: D08.49; D08.56 F1]
- **B17 CLASSIFY IS ATTEST GENERALISED.** A class is the latest live classify act on an entity or on information (actor, object, target the band, evidence, rule cited), computed at read; the act is one existing attest-shaped operation amended to carry a target and an evidence kind, not a new operation. [SOURCE-DERIVED: D08.50 "Four things, all records"; D08.56 F3]
- **B18 CEILINGS ONLY SHRINK.** A class adds a ceiling over what any grant may say and confers nothing; classes may nest because ceilings compose by intersection; for any group three envelopes are views (CLASS MAX, STRUCTURAL MAX, HELD) and HELD sits inside both at every moment. [SOURCE-DERIVED: D08.50]
- **B19 INFORMATION GOVERNED BY TAGGING THE FLOW.** A path is a view over the five families (channels; sockets and tunnels; shared memory; custody handover; sight) naming its endpoints, their positions on the three axes, the content bands it permits and the rule it cites; ceilings attach to paths; the content's class only tightens. [SOURCE-DERIVED: D08.51; D08.56 F2, F5]
- **B20 ORG CLASS COMPUTED, SAY GUARANTEED.** An organisation's class (human-only, AI-only, mixed) is a fold over live occupancy, and a rule at rule level for a mixed organisation may require a human occupant's countersign. [SOURCE-DERIVED: D08.49 "Orgs are not declared a class"]

## 4. INVARIANTS (each states how it is checked; one it cannot check is carried to §9)

- **I1 ONE RECORD, ONE PEN.** Two pens are two records exchanging sealed chunks and shared views. Check: the sender's record is unchanged by any receipt, and a census over every new vocabulary finds no op that appends to a record other than the actor's own. [SOURCE-DERIVED: intake:78 citing D08.13:204-207, D08.22:387-388; design/51 T-ONE-PEN-HOLDS carried]
- **I2 NO GATE ABOVE THE BOXES.** Check: a census of the campaign's vocabulary finds no operation whose actor is a body other than the one whose record it writes, and no view whose inputs are two bodies' records folded as one truth. [SOURCE-DERIVED: intake:79 citing D07.3:31-33, D08.11:160]
- **I3 A PARENT CANNOT WRITE A CHILD'S ROW.** Check: a parent-signed row arriving at the child lands only with the child's record_class INPUT and only through the child's gate; a planted attempt to land it as DECISION is refused and recorded. [SOURCE-DERIVED: intake:80 citing D08.14:218-220; design/51 T-PEER-RECORD-NOT-TRUSTED carried]
- **I4 BINDING IS SELF-DECLARED AT FOUNDING.** Check: the pin lives in the child's genesis as its own founding data, and a child whose pinned copy fails verification refuses to wake. [SOURCE-DERIVED: intake:81 citing D08.14:221-223, D08.15:247-251]
- **I5 AUTO-RECEIVE, NEVER AUTO-CHANGE.** Check: for every received parent rule that is in force at the child there exists a child-authored adoption act citing it by hash; a received rule with no such act is not in the active constitution view. [SOURCE-DERIVED: intake:82 citing D08.15:252-258]
- **I6 CITED RULES ARE ALWAYS LOCAL.** Check: every rule_cited in the child resolves inside the child's own record; the active constitution recomputed from received rows alone equals the served one (the cache-kill form). [SOURCE-DERIVED: intake:83 citing D08.16:266-275]
- **I7 NOTHING FROM A PEER'S RECORD ENTERS AS A DECISION.** Check: enforced by the shape of the entries, not by a guard; a census finds every peer-origin row tagged INPUT. [SOURCE-DERIVED: intake:84 citing design/51 N4, SPIKE-1:78-84]
- **I8 ONE MACHINE PER STAGE PER SCOPE.** Check: at the handshake a stage claim absent from the claimant's declared stages is refused by name; the K6 case (two machines, same stage, same scope, declared as redundancy) is refused until §9 settles what distinguishes it. [SOURCE-DERIVED: intake:85 citing charter:256-258, D08.30:608-610]
- **I9 A STAGE IS A KIND OF ROW, NOT A MACHINE.** Check: no new row field is added by this campaign; the row shape's field census is unchanged at every close. [SOURCE-DERIVED: intake:86 citing D08.29:589-597, charter:259-261]
- **I10 THE HANDSHAKE IS THREE CHECKS, MUTUAL, LEVEL-BLIND; ADMISSION GRADED AND RECORDED.** Check: for each of the three checks a planted failure lowers the admission level and the recorded row names the failed check; no admission row omits the passed set. [SOURCE-DERIVED: intake:87 citing D08.17:293-298, D08.18:316-320]
- **I11 A BODY'S NAME IS (BOUND SYSTEM KEY, GENESIS HASH); NO ISSUER; NO REAL-WORLD DATA IN THE NAME.** Check: a copied seed produces a fork the chain exposes at the first differing row; a name-derivation from any fact row is absent by census. [SOURCE-DERIVED: intake:88 citing D08.42:1078-1080; D08.44 read whole]
- **I12 LEAST DISCLOSURE BY LAW.** Check: a crossing carries exactly the leaves the receiver's rule names; a withheld required leaf is a recorded refusal; an unrevealed leaf is underivable from what the receiver holds. [SOURCE-DERIVED: intake:89; D08.48 reasons 1 to 4]
- **I13 EVERY READ THROUGH AN INSTITUTION'S GATE IS A ROW.** Check: a gate-read with no row is impossible by construction; the cap that a disk-level read is not this gate's is carried in one sentence, K7. [SOURCE-DERIVED: intake:90 citing D07.5:53-55, D08.12:187-188; cap intake:147 citing D08.46:1122]
- **I14 CONSOLIDATION ONLY BY HANDOVER; NO DELETE.** Check: the no-delete census over every new vocabulary; a merge-by-copy op is absent. [SOURCE-DERIVED: intake:91 citing D08.22:397-399, design/46:14-21]
- **I15 THE CONSTITUTION SURVIVES ITS MACHINE.** Check: with the parent's store removed, the union of the children's received segments verified against the parent key reproduces every rule any child was bound by. [SOURCE-DERIVED: intake:92 citing D08.16:276-282]
- **I16 AN ACTOR HOLDS A STAGE, NEVER DECISION PLUS ENFORCEMENT PLUS MONITORING TOGETHER.** Check: the handshake refuses a declared stage set containing all three for one actor. [SOURCE-DERIVED: intake:93 citing D08.37:812-814]
- **I17 EVERY PUBLISHED FIGURE NAMES ITS WORLD.** Check: every count in a close carries its world; the charter rider binds all streams. [SOURCE-DERIVED: intake:94 citing charter:283-287]
- **I18 THE SEALED RECORD IS THE ONLY THING THAT CROSSES ANY LINE.** Check: what a second body consumes is a sealed release or a sealed segment; a census finds no other crossing shape. [SOURCE-DERIVED: intake:95 citing charter:174-176, design/44:69-70]
- **I19 A BODY IS WHATEVER ONE ANCHOR CAN VOUCH FOR.** A box may hold several bodies and a body several records. Check: B10's relation rows, and the diving-buddy cap that two bodies never share a write path. [SOURCE-DERIVED: intake:96 citing D08.23:415-418; cap intake:146 citing D07.10:176-179]
- **I20 NO SIXTH WAY.** Every way information moves is one of the five path families. Check: an instrument over the code, a census of every place bytes move, the sibling of the effect-order census; not a rule the record can check about itself. [SOURCE-DERIVED: D08.51 condition (1); D08.56 F5]
- **I21 HELD SITS INSIDE CLASS MAX AND STRUCTURAL MAX.** Check: the three envelope views computed for every group at every close; held outside class max is the invariant refusing. [SOURCE-DERIVED: D08.50 "Max possible for an actor group"]
- **I22 A RECEIVED ROW CITING A RULE WITH NO LOCAL MAPPING REFUSES LOUDLY BY NAME.** A fallback that answers is a check that cannot fail. Check: a planted received row citing an unmapped (record-identity, rule-hash) is refused with the missing mapping named, never with the generic code. [INFERRED: from intake:125-127, the EINVAL observation at board :3456; cost if wrong, one wasted paper line]
- **TIMESTAMPS HONEST ACROSS TWO CLOCKS** is a candidate whose form is unsettled and whose check nobody can state today; it is carried to §9 as an open item, not written here as an invariant. [SOURCE-DERIVED: intake:97 citing design/44:71-72, D07.3:34]

## 5. SETTLED LAW register

- [L1] The name is "self-orchestrated institution", ordering from within and between, never from above; the ladder name is ruled. source: owner, D07.6; design/51:122; board :3463 [SOURCE-DERIVED: intake:24]
- [L2] Two installs are two strangers; C6 is one box accepting another's record, re-verified at its own hand. source: owner and archi, D07.2 [SOURCE-DERIVED: intake:25]
- [L3] No gate exists above the boxes; a network of boxes never becomes one bigger machine. source: archi, D07.3 [SOURCE-DERIVED: intake:26]
- [L4] Signature machinery is the substance; three pieces are missing (the trust-bootstrap ceremony, the two-clocks law, the receiving vocabulary) plus one (rule citation across records). source: archi, D07.3 and D08.14 [SOURCE-DERIVED: intake:26, intake:61]
- [L5] Law lives in the record as rows; one box per institution is that institution's sole truth; staff machines are doors, not truths. source: owner's probes confirmed, D07.5 [SOURCE-DERIVED: intake:27]
- [L6] Reading is a governed act through the asked institution's own gate; outside institutions request acts through the front door and the grant or refusal is a row under the asked institution's law. source: archi, D07.5 [SOURCE-DERIVED: intake:27]
- [L7] The government is a tree of institutions, each branch a propagated machine with its own right; the two-processor issue is not to be fixed, the tree is the many-books shape. source: owner, D08.14 [SOURCE-DERIVED: intake:28]
- [L8] C6's vocabulary is the eight stages; an institution is a set of stage machines under one constitution; a stage is a kind of row, no new row field. source: charter:252-261, D08.29, D08.34 [SOURCE-DERIVED: intake:30]
- [L9] Two founding-level declarations enter C6's paper at the owner gate: a pack declares the stages it holds and their scope, checked at the handshake; a child pack pins its parent. source: charter:254-259 [SOURCE-DERIVED: intake:30]
- [L10] A software update is the rule-change component held modularly elsewhere and reached by handshake; that is C6 on the rule itself. source: owner, D08.27 [SOURCE-DERIVED: intake:31]
- [L11] The ladder: C4 one record proven, C5 two records talk, C6 institutions, C7 bodies. source: owner, D08.25; D07.1 [SOURCE-DERIVED: intake:32]
- [L12] The law is one pen per record, never one record per machine; many pens on one record stays the deliberately unminted construct. source: D08.13, D08.22; charter:241 [SOURCE-DERIVED: intake:43, intake:78]
- [L13] The closed check vocabulary grows only by owner-gated members; C5 grew it by two (`live_present`, `fold_threshold`), OP_CHECKS now nineteen. source: design/50; design/51:46, :121; board :3354, :3456 [SOURCE-DERIVED: intake:112-113]
- [L14] Consolidation only by handover, never merge by copy; no delete, constitutional class, carried into every future world's founding. source: D08.22; design/46 [SOURCE-DERIVED: intake:45, intake:91]
- [L15] A body's name is (bound system public key, genesis hash); no issuer; no real-world data in the name, facts are rows; "more unique than random" is not a property that exists. source: D08.42, D08.44 [SOURCE-DERIVED: intake:88; D08.44 addendum]
- [L16] The host declares, gov-os never discovers; the air never reaches for you. source: D08.12 [SOURCE-DERIVED: intake:47]
- [L17] Three actor classes, human, AI, program; "system" stays the one border entity; the processing cut is derived from replay and bounds who executes a rule, never who may ask. source: owner, 2026-09-09, D08.49 [SOURCE-DERIVED: D08.49]
- [L18] A category adds a ceiling, never a power; the vocabulary is a rule in the constitution; a category is an act with evidence; membership is a view; ceilings only shrink; classes may nest because ceilings compose by intersection. source: owner and archi, 2026-09-09, D08.50 [SOURCE-DERIVED: D08.50]
- [L19] Information is governed by tagging the opened path, not the datum; five path families today; the invariant to census is "no sixth way"; the content's class only tightens. source: owner, 2026-09-09, D08.51 [SOURCE-DERIVED: D08.51]
- [L20] The derivations vocabulary (views and checks as one thing) is placed after C6; C6 states it as a cap and does not mint it. source: archi, D08.53 [SOURCE-DERIVED: D08.53; intake:215]
- [L21] The brake is a frozen, negative-only view placed at C7; C6 owes it the class ceilings (no AI holds the actuator reach) and "a view served with a deadline" as a named path family case. source: archi, D08.54 [SOURCE-DERIVED: D08.54; intake:216]
- [L22] An installed record grows by law and never forks; a second install for a second use is a second world and is refused by name. source: archi, D08.55 [SOURCE-DERIVED: D08.55]
- [L23] The deriving audit controls where it differs from D08.52: C6's founding price is one amendment (ATTEST gains a target and an evidence kind) plus two declarations (the two capabilities; the boundary positions) plus one census; the check kinds probably stay at nineteen. source: archi, D08.56 [SOURCE-DERIVED: D08.56 closing paragraph; intake:218]
- [L24] C6 starts when C5's last unit closes, without waiting; the owner's word on the six check kinds is one each when this paper puts them. source: owner, board :3463 [SOURCE-DERIVED: intake:15-17, intake:161]
- [L25] Hard timing is C7's; the enforcement carve-out is C7's first spike; C6 measures only. source: design/51:104; charter:262-270; D08.30 [SOURCE-DERIVED: intake:133]

## 6. MUST-NOT-TOUCH

The intake names the paths it held out of bounds; they carry as this campaign's fences until the architect completes the list. [SOURCE-DERIVED: intake:203; the estate's standing fences in `CLAUDE.md`]

- `apps/pwc-app` (out of bounds to the intake; the six check kinds' meanings for three of them are inferred from name for that reason)
- `apps/urban-app/.plan` (the IP boundary)
- `archive/`, `tests/archive/`, any future archive folder (frozen as they are)
- `reference/` (snapshots)
- the C5 papers and spikes as records: `design/51`, `planning/exec/SPIKE-1-FINDINGS`, `SPIKE-2` (cited, never edited; an as-built line owed to charter:151 and :232 is not this campaign's to write, intake:154)

The architect fills the rest.

## 7. PLAN LIST (one line per plan; order shows spikes before the founding movers, as K11 requires; EP numbers assigned at dispatch after C5's last; the whole list is PROPOSED, cost if wrong one re-cut of the list before any dispatch)

    P1  | SPIKE: THE TRUST-BOOTSTRAP CEREMONY  | B3 (BODY and MEMORY SANE of a counterpart, graded admission)       | UNKNOWN (spike, findings file, code thrown away) | 1  | PENDING
    P2  | SPIKE: THE TWO CLOCKS                | B14 (content of the two-clocks law; the timestamps-honest form)     | UNKNOWN (spike)                                  | 2  | PENDING
    P3  | SPIKE: THE RECEIVING VOCABULARY      | B15 (what row a many-row segment writes)                            | UNKNOWN (spike)                                  | 3  | PENDING
    P4  | THE FIVE-FAMILIES CENSUS             | I20 (no sixth way, as an instrument over the code)                  | GREEN                                            | 4  | PENDING
    P5  | THE TWC ROWS READ FOR THE SIX KINDS  | Q1's descriptions verified before the question is put               | GREEN (reading only)                             | 5  | PENDING
    P6  | FOUNDING: STAGES AND SCOPE DECLARED  | B8, I8, I16 (after Q2 YES)                                          | RED (owner gate, new founding vocabulary)        | 6  | PENDING
    P7  | FOUNDING: THE PARENT PIN             | B1, I4 (after Q3 YES)                                               | RED (owner gate, new founding vocabulary)        | 7  | PENDING
    P8  | FOUNDING: ATTEST AMENDED, TWO DECLARATIONS | B16, B17, B18, I21, K12 closed (the actor-class domain)        | RED (founding mover; the op-amend lesson binds)  | 8  | PENDING
    P9  | RULE CITATION ACROSS RECORDS         | B4, I6, I22 (after Q4; field or structured value priced first)      | YELLOW (interface other units build on)          | 9  | PENDING
    P10 | AUTO-RECEIVE AND HOLD WHAT BINDS     | B2, B5, I3, I5                                                      | YELLOW                                           | 10 | PENDING
    P11 | THE HANDSHAKE, THREE CHECKS          | B3, I10, I12 (B12's unlinkable keys and predicates ride here)       | YELLOW                                           | 11 | PENDING
    P12 | THE CONSTITUTION SURVIVES            | B6, I15                                                             | GREEN                                            | 12 | PENDING
    P13 | READING THROUGH THE GATE             | B9, I13 (K7's one sentence carried)                                 | GREEN                                            | 13 | PENDING
    P14 | MANY RECORDS, ONE PEN EACH; HANDOVER | B10, B11, I1, I14, I19                                              | YELLOW                                           | 14 | PENDING
    P15 | STAGE ROWS CROSSING; METABOLISM      | B7 (the fifth number candidate: arrival-to-arrival time)            | YELLOW                                           | 15 | PENDING
    P16 | PATHS AND CEILINGS OVER FLOWS        | B19, B20 (the prior_value locate-by-$actor door change, F4)         | YELLOW                                           | 16 | PENDING
    P17 | HONEST STATE ACROSS THE BOUNDARY     | B13                                                                 | GREEN                                            | 17 | PENDING
    P18 | CAMPAIGN REVIEW                      | every I graded; every published figure naming its world (I17)       | one hand                                         | 18 | PENDING

Whether P1 to P3 run before P6 and P7 is the K11 ruling applied: the two-track law's "opens with spikes" binds the order. [SOURCE-DERIVED: intake:164]

## 8. AS-BUILT LOG

none: campaign not started

## 9. OPEN QUESTIONS / OWNER GATES (each self-contained; one word answers; none blocking today unless marked)

- **Q1 The six check kinds, one word each (batched, as board :3426 asked).** The outside constitution founded through the door in C5 needed six kinds of check that gov-os's nineteen cannot express: `quorum` (enough hands present before an act lands), `escalate` (a gate sends a rule it cannot run mechanically to a human instead of pretending to run it), `should_verdict` (allow, with the reason recorded), `blind_position` (a position that must decide without sight of some rows), `focus_lock` (one focus of attention per actor at a time), `sight_binds_writes` (a write permitted only where sight of the object is held). For each: YES means the kind is minted with its own refusal and positive control. NO means rows needing it stay unstructured, enforced by judgment, and their count stays published with its world. The last three descriptions are inferred from the kind's name because the application that needs them was out of bounds; P5 reads the rows before this question is put. [SOURCE-DERIVED: intake:104-111, intake:170; the meanings of the last three INFERRED, intake:111]
- **Q2 May a machine's founding pack declare the stages it holds and the scope it holds them for, as new founding vocabulary?** YES means "one machine per stage per scope" becomes checkable when two machines meet. NO means the rule stays a promise in prose and no handshake can refuse a stage claim. [SOURCE-DERIVED: intake:171 citing charter:255-258]
- **Q3 May a child's founding pack pin its parent, the parent's key and its rule set at a version, as new founding vocabulary?** YES means a child is born bound and can verify what binds it. NO means binding lives outside the record and the tree cannot be rebuilt from its children. [SOURCE-DERIVED: intake:172 citing charter:259, D08.14, D08.15]
- **Q4 May a decision cite a rule that lives in another record, by (record-identity, rule-hash)?** YES means a child's act can name the parent rule it obeys. NO means every parent rule must be re-created locally as the child's own rule before it can be cited, and the citation loses the parent. Whether this needs a new row field or only a structured value in the existing cited-rule slot is the architect's to price before the question is put; the charter forbids a new field for STAGE only. [SOURCE-DERIVED: intake:173 citing D08.14:234-236, charter:259-261]
- **Q5 In the owner's relation grammar, is the parent-to-child line of the tree an HR line, or NT, or SY?** One of three words; it fixes what "bound by its rules" means on the relation row. [SOURCE-DERIVED: intake:174; K9]
- **Q6 Is the second body for C6's proofs again this machine's own guest, or a second physical machine?** GUEST means nothing is bought, the host-to-host move stays unmeasured and SPIKE-2's cap stays. PHYSICAL means the host-to-host move and "the guest's outside witness" become measurable, and the run waits on the box. [SOURCE-DERIVED: intake:175 citing D08.30:612, SPIKE-2]
- **Q7 Does many-pens-on-one-record stay unminted through C6?** YES means one pen per record is a C6 invariant (I1) and the six-item travel list from EP-28C does not ride. NO means that list binds C6's author and a paper section is owed for it. [SOURCE-DERIVED: intake:176; K5]
- **Q8 The project release key: an owner act, not a paper question.** The owner signing each release tag and stamp with a key whose public half sits at the public root; named here so the identity line (product, then law, then instance) is not read as already signed. [SOURCE-DERIVED: intake:177 citing D08.47]
- **Q9 (owner's word, from D08.49, not in the intake's list).** Whether an AI may ever hold a device reach class; and whether "external" is a fourth actor class or a reach class of the border. The deriving audit answers the second by derivation ("external" is a boundary position on a second axis, no fourth processing class) and leaves the word his. [SOURCE-DERIVED: D08.49 last paragraph; D08.56 F2]

Open to the architect, not the owner (design items, no gate):

- the content and the check of the two-clocks law (B14; the candidate invariant carried out of §4) [SOURCE-DERIVED: intake:71, intake:97]
- what distinguishes lawful redundancy from the forbidden same-stage-same-scope case (K6): a declared-redundancy row, or a scope partition; founding vocabulary if it is, then the owner's word [SOURCE-DERIVED: intake:159]
- one defined word for the two things the sources both call "trust" (K10) [SOURCE-DERIVED: intake:163]
- DRIVEN AT v0.1, no longer open: the chain-hash-excludes-record-time acceptance is GREEN and closed in C5, as the receipt unit's fifth acceptance (tests/test_ep49d.py:268) and the tracer's fourth (tests/test_ep51.py:22), implemented at src/kernel/border.py:470; both units CLOSED on the board. [SOURCE-DERIVED: those three files, read at the architect's hand; intake:205 is discharged]
- DRIVEN AT v0.1, no longer open: the review grades design/51 N4 MET at subsystem scope (the ungoverned-peer remainder is the cap this campaign owns, I19 and B13) and N9 MET (one row, one receipt, two bodies, one pen). [SOURCE-DERIVED: planning/exec/DIGEST-C5.md:34, :39; intake:204 is discharged]
- "the guest's outside witness", claimed by neither the C5 paper nor this draft (rides Q6) [SOURCE-DERIVED: intake:142]

## 10. CONFLICTS PRESERVED (both sides shown; marked CONFLICT; none harmonised here)

- **K1 CONFLICT, the rung's name.** One side: design/44:85 "C6 DISTRIBUTION beyond-one-machine" and charter:151 "C6* DISTRIBUTION"; charter:232 "after C6 (two bodies)"; design/37:477-478 "campaign 6 owns transport". Other side: charter:252-253 "C6 SELF-ORCHESTRATED INSTITUTIONS", D08.25 "C6 institutions", D07.1 "C6 many boxes". Resolving cite: design/51:106 and :122, board :3463 "as ruled"; charter:151 and :232 still carry the old words and an as-built line is owed there, not by this paper. [SOURCE-DERIVED: intake:154]
- **K2 CONFLICT, the size of C6's content.** D07.3: "three missing pieces only … spikes, not a big build". D08.14: the three plus one, and "THIS IS C6'S REAL CONTENT", a tree. charter:252-261: the eight-stage vocabulary plus two founding declarations. D07.2: "one box ACCEPTING another's record". Not contradictory in substance, contradictory in size; later statements control; this paper states one defining behaviour (B1, the tree, with B2 as its first consequence) and prices the size at §7's eighteen rows. [SOURCE-DERIVED: intake:155; the choice of B1 as defining is ARCHI-RULED at v0.1: the later statements control, and every other behaviour is either a consequence of the tree or a piece the tree needs to stand]
- **K3 CONFLICT, "two bodies" is C5's or C6's.** charter:232 "Opens only after C6 (two bodies)" and D08.26 "MANY BODIES … That is C5/C6's own problem". Against: design/51:30 N9 and board :3456 "two bodies, two chains": proven in C5. Resolving cite: design/51:106; VM-2's precondition wording is stale by one campaign. [SOURCE-DERIVED: intake:156]
- **K4 CONFLICT, who owns the transport.** design/37:478 "campaign 6 owns transport". Against: design/44:45-48 "C5 governs THE WIRE", D08.30:612, board :3456 real sockets under recorded grants. Resolving cite: design/51 N1; the residue "the guest's outside witness" is unclaimed and rides Q6. [SOURCE-DERIVED: intake:157]
- **K5 CONFLICT, what this intake is made of.** design/44:86: the intake is "W4e's six-item travel list + C4 attestation". Board :3463: C5's caps, the two spikes' caps, the six check kinds, D08.42 to 48, the EINVAL observation, and no W4e list. D08.13: many pens stays the deliberately unminted construct. The later order controls the intake; this paper says in one line that many pens stays unminted (I1, Q7) and has not read the six-item list. [SOURCE-DERIVED: intake:158]
- **K6 CONFLICT, one machine per stage per scope against lawful redundancy.** D08.30:608-610: disagreement needs two machines holding the same stage for the same scope, which the constitution rule forbids. D08.30:610-612, next sentence: redundancy is parallel records under the same granted rule, and a difference between them is evidence for monitoring, never a truth to reconcile. The charter says the rule is checked at the handshake and not what distinguishes the two cases. Unresolved in any source read; carried to §9 as the architect's. [SOURCE-DERIVED: intake:159]
- **K7 CONFLICT, "an unrecorded read becomes impossible" against the raw-read cap.** D07.5 and D08.12: every read is a row, an unrecorded read impossible not merely banned. D08.19 "gate-reads governed, raw reads not"; D08.46 "no LAWFUL read path, not no read at all"; D08.17's HASHES-ONLY level. The scope resolution, stated nowhere in one place: impossible through the gate; a disk-level read stays the disk-lock cap of C4 and C7's hardware. This paper carries both clauses in I13's one sentence. [SOURCE-DERIVED: intake:160]
- **K8 CONFLICT, where the check-kind word is due.** design/51:121 "your word due when raised at EP-49/EP-51". Board :3426 "surfaced to the owner at the C6 intake, batched, never an urgent standalone raise"; :3463 "one each when the paper puts them". Later controls: this paper puts them (Q1) and §11 must not read as re-asking. [SOURCE-DERIVED: intake:161]
- **K9 CONFLICT, "no HR edge above" against a tree with a parent.** D08.11:160 "self-orchestrated institutions = NT/SY with no HR edge above". D08.14 and D08.15: a tree, a pinned parent, rules that bind. Which tag the parent-to-child relation row carries is stated nowhere read; if HR the D08.11 sentence is about gov-os's edge to hosts only; if NT/SY "bound by its rules" needs the tag explained. Carried as Q5. [SOURCE-DERIVED: intake:162]
- **K10 CONFLICT, "trust in a peer's record", refused yet accepted.** design/51:108 non-goal "trust in a peer's record (C6)". D07.2 "ACCEPTING another's record, re-verified at its own hand"; D08.15 parent-signed rows admitted as INPUT; D08.18 "everything gets exactly the trust it proved, written down". Terminology, not substance: one word for a peer's row entering as this record's DECISION (refused, I7) and for verified INPUT at a recorded grade (built). One defined word is owed; carried to §9. [SOURCE-DERIVED: intake:163]
- **K11 CONFLICT, "spikes, not a big build" against two founding declarations.** D07.3, design/44:85-86, charter:174-175: opens with spikes. charter:254-259 and D08.14: two founding-level declarations and the tree. A founding vocabulary move is not a spike; later controls, and the two-track law still binds the order. §7 shows P1 to P3 as spikes before P6 to P8 as founding movers. [SOURCE-DERIVED: intake:164]
- **K12 CONFLICT, the actor-class field has no declared domain today.** The field exists (CREATE-ACCOUNT carries it as a free string; the succession rule reads "human"); D08.50's vocabulary rule closes it (a class not in the list cannot be written). Where the fix lands is open: the post-close maintenance, or C6's first law (§7 P8 places it in C6, PROPOSED, cost if wrong one row moved between two ledgers). [SOURCE-DERIVED: intake:214; D08.49 "declares NO domain for the field"]

## 11. RAISES, NOT MINTS (named by the sources; minted by nobody here; each awaits the word its source names)

The six candidate check kinds, raised by name by the EP-51 tracer and minted by none, each the owner's one word at Q1 [SOURCE-DERIVED: intake:104]. The board line's counts in the outside constitution's pack, that line's figures and not re-driven against the pack [SOURCE-DERIVED: intake:105-106, intake:206]:

- `quorum` (17 rows) · `escalate` (22) · `blind_position` (8) · `should_verdict` (2) · `focus_lock` (2) · `sight_binds_writes` (0, named as a kind a real constitution would need)

The two identity words the owner owes when this paper puts them are Q9's two, from D08.49's own closing line: whether an AI may ever hold a device reach class, and whether "external" is a fourth actor class or a reach class of the border. [SOURCE-DERIVED: design/dialogues/08-air-ecosystem.md:1173; corrected at v0.1, the first cut had read these as the two mechanisms below]

The two identity mechanisms, named not minted at D08.48 for "C6's paper, when two bodies with their own records need it", both over the tree already built, ride §7 P11 and are the architect's to price, not the owner's word [SOURCE-DERIVED: D08.48:1161; intake:119]:

- UNLINKABLE per-peer keys derived from the body key, so two peers cannot join the roots
- ZERO-KNOWLEDGE predicates, "version at or above a value", "a human", without the value

Also raised, not minted, in the sources this draft folds:

- the ceiling's check shape: likely no new kind (`prior_value` gains `$actor` as a locate source, a door change), confirmed only by driving a real ceiling row; if wrong, one new kind and one owner word [SOURCE-DERIVED: D08.56 F4]
- the derivations vocabulary (views and checks declared as one closed set): after C6, a campaign-sized law pass, stated here as a cap [SOURCE-DERIVED: D08.53]
- the project release key: an owner act (Q8) [SOURCE-DERIVED: D08.47]
- the fifth number, arrival-to-arrival time per stage, beside the four numbers not yet taken [INFERRED: from intake:137 citing D08.28:578-580; not a source's list]

## Caps inherited (named by the sources; C6 receives them; each marked LIFTED by a §7 row or CARRIED past this campaign)

- Hard timing: CARRIED to C7 ("measure only"); the enforcement carve-out is C7's first spike. [SOURCE-DERIVED: intake:133]
- The host-to-host move: not measured in C5 ("Local move only"); LIFTED only if Q6 answers PHYSICAL, else CARRIED. [SOURCE-DERIVED: intake:134 citing SPIKE-2:102-103, :120-125]
- The contended hard cut: the reply-after-covering-sync case has never run; the clean-move result is not evidence for it; CARRIED unless a §7 row claims it. [SOURCE-DERIVED: intake:135 citing SPIKE-2:113-116]
- The cold-boot seam was proven by reading, not by a cold boot; the head check checks the head only; CARRIED. [SOURCE-DERIVED: intake:136 citing SPIKE-2:98-106]
- The four numbers not taken (one-pen group-commit rate; carve-out latency; verify-without-engine at scale with proof size; smallest memory for a chained append): CARRIED; C6 adds a fifth candidate, arrival-to-arrival time per stage (§11). [SOURCE-DERIVED: intake:137; the fifth INFERRED there]
- The ungoverned peer is known by what crosses and nothing more; the remainder SPIKE-1 measured is LIFTED at B13 and B12 to the extent §7 P11 and P17 prove it. [SOURCE-DERIVED: intake:138 citing design/51:101]
- Packet enforcement is the guest kernel's: unchanged by C6. [SOURCE-DERIVED: intake:139 citing design/51:102]
- Real keys only where the library is present; every key record names its kind: unchanged. [SOURCE-DERIVED: intake:140 citing design/51:103]
- Hardware-bound keys, the hardware-born and sealed-to-measured-state secret: CARRIED to C7. [SOURCE-DERIVED: intake:141 citing D08.43, D08.46]
- "The guest's outside witness": claimed by neither paper; rides Q6. [SOURCE-DERIVED: intake:142 citing D08.30:612]
- The eight-stage mapping is a first derivation for the owner's correction, not law; five of the lifecycle corpus's documents were unread by its author. [SOURCE-DERIVED: intake:144 citing D08.28:581]
- Self-attestation is citability, not immunity; a fork of the code is lawful and may call itself what it likes. [SOURCE-DERIVED: intake:145; D08.47 caps (a) and (b)]
- The common-mode cap: two bodies never share a write path, and beneath both still sits the chip's maker. [SOURCE-DERIVED: intake:146 citing D07.10:176-179]
- Software gives no lawful read path, not no read at all (bears on I13 and K7). [SOURCE-DERIVED: intake:147; D08.46 item 1]
- Whether the chain hash excludes record time was moved to a C5 acceptance row: GREEN and closed in C5 (§9's driven line), LIFTED before this campaign opens. [SOURCE-DERIVED: intake:148; tests/test_ep49d.py:268, tests/test_ep51.py:22, src/kernel/border.py:470]
- The derivations vocabulary (D08.53) and the brake (D08.54): stated as caps, placed after C6 and at C7. [SOURCE-DERIVED: intake:215-216]

## Wrong references refused by name (carried from the intake; each with what taking it erases)

- The orchestration platform (a controller above the nodes): erases "no gate above the boxes"; "self-orchestrated" becomes "orchestrated". [SOURCE-DERIVED: intake:183; trained knowledge flagged there]
- The consensus protocol, replicated state machine, blockchain: erases one pen per record and "no global agreement, no consensus cost"; a difference between records becomes a fault to reconcile where D08.30 says it is evidence for monitoring. [SOURCE-DERIVED: intake:184]
- The federation protocol: erases self-declared binding (I4) and the child's own act (I5); imports "a second truth that drifts". [SOURCE-DERIVED: intake:185]
- The workflow engine: erases "a stage is a kind of row, not a machine" and puts communication back inside gov-os. [SOURCE-DERIVED: intake:186]
- The multi-tenant service (one book, one operator's hand): the shape the owner ruled the opposite; erases "a say at your own hand is not revocable". [SOURCE-DERIVED: intake:187 citing D07.4, D07.7]
- Carried refusals: the registry or issuer of names; the API gateway with auth middleware; the sidecar courier; the broker that holds truth. [SOURCE-DERIVED: intake:188]
- The transparency log as authority: the right detector, the wrong authority; a log everyone must append to is a gate above the boxes by another name. [INFERRED: intake:189, cost if wrong one line]

## Caps of this draft (what it did not read)

Inherited whole from the intake's §8: D07 is never reopened here (every D07 cite rides the intake); D08.1 to D08.48 are read only at D08.44 to D08.48 (the lines 1100 onward) and otherwise as the intake carries them; design/42, /43, /46, /47, /48, /49, /50 unread; the charter unread; the two spikes' findings unread; the board unread; EP-28C's six-item list unread; the outside constitution's rows unread, so three of the six check-kind descriptions are inferred from name; no figure re-driven; no test run. [SOURCE-DERIVED: intake:195-206, and this draft's own reading list] At v0.1 the architect drove three items out of this list (N4/N9's grading, the chain-hash acceptance, D08.49's two words); the rest stands until the paper is revised against the charter and the C5 close.

---

*Register: SOURCE-DERIVED cited inline to the intake line or the dialogue paragraph; INFERRED with its source named; PROPOSED with its cost (the plan list, the choice of defining behaviour, the placement of K12). Drafted at one hand in one turn as the architect's first cut; nothing here is law until revised at the architect's seat and marked ACTIVE on the board.*
