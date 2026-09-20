# AWIG OS: the architecture

This document holds the technical design of AWIG OS. The philosophy it implements lives in the [README](./README.md). This is the machine that carries it.

---

## 0. How to read this work

Two things run in this repository. The governing layer, in Python: the record, the gate, the rules and the views, built first so that they ran and could be tested before any kernel existed. And our own kernel beneath it, in C and assembly under `code/src/body`, which boots in a virtual machine with no Linux under it. The governing layer is the executable specification: the kernel is checked against it, act for act, the same acts under both. seL4 was built the same way, a running model before the real kernel. Neither is a finished product, and the pages say exactly how far each goes. The line the model draws runs between the unstructured and the structured, what is said and what is done: prose, an AI's included, never moves the system; a structured row that passed a rule does, and the crossing is the gate.

The design papers in `design/` are the contracts that model implements; the map at `design/README.md` names the ten contracts in force, each with its paper and its code, and the note at `design/00-RENDER-NOTE.md` lists every paper with its status. `STATUS.md` says what is true today, machine by machine, with the numbers for the same acts under Linux and under our kernel side by side.

A defect in a mechanism is not a defect in its contract, and the pages say which is which: a test that fails is listed with what it needs; a promise the code does not yet keep is listed under what is not true yet.

The fence and the two openings. An agent behind a fence holds one permission set for a session and acts directly on everything inside it; the known failure is a document that turns the agent, and the fence has no answer because the agent's act is its own. Here an AI organisation is an entity with two watched openings, the demand side and the supply side. A turned document arrives on the demand side. Whatever the organisation then wants arrives on the supply side as a proposal the gate decides against the rulebook, and taking data out needs a grant that was never made, so the proposal comes back as a refusal row citing the rule. What this bounds is the damage, to the grant set; a turned organisation with a grant can misuse the grant. The border that makes an outside submission a draft the gate decides is built and proven in test worlds between a host and a guest (design 49, `bridge/`); the organisation between the openings is a stand-in pack today (design 51, EP-51).

## 0a. What the rules cannot change

Every act reaches the record through one gate, which writes a decision citing its rule, or a refusal citing its rule, as a row. Exactly four kinds of row are written without a gate decision, each named and bounded, and every one passes through the store's single appender: the founding rows that bring a world into existence; the two-stream audit mirror; the chain-anchor ceremony; and the gate's own refusal and effect-failure rows. These four are the floor below the rules: what deciding itself stands on. A rule can change what the gate decides; no rule can remove the appender, the chain, or the founding they rest on.

Where each is written, so a reader can check: the founding rows in `src/kernel/gate.py` (the constitution guard); the two audit streams in `src/kernel/protection.py`; the chain anchor in `src/kernel/store.py`; the refusal and effect-failure rows in `src/kernel/gate.py` (`refuse` and `_record_effect_failure`).

## 1. Eight architectural commitments

Each carries its status in the build side's words: BUILT (running, tested), PROVEN IN TEST WORLDS (running between test machines), DESIGNED (on paper).

**Record what happened, compute everything else.**
One append-only record is the only truth. Every view, index and screen is computed from it and can be thrown away and rebuilt. BUILT.

**Information and actors, kept apart.**
A thing is either static information or an actor. Information never acts. A program's files are information; a program becomes an actor only when the system loads it, on the record, with its rules sealed, and it cannot ask for more than it declared. An AI model is a file until a program loads it. The sealed half is BUILT: the kernel and the interpreter are pinned in the record and a changed byte stops the start. The birth row for every program is DESIGNED.

**One rule format, and a permission is one shape.**
Every rule, from who may open a file to how the rules change, has the same readable, executable form. There is no privileged rule syntax for privileged actors. Each deployment's complete rule set is its *awig-awig*: self-written, legible, machine-executable. A permission is one actor, one action, one object, one target; changing it reshapes that one rule by recorded edits, never stacks a second rule on top. The format is BUILT; the shaped permission is DESIGNED.

**Views never act.**
A view is information the system computes. It has no code, no box, no pen. Only the system makes a view; a program's own reading of the record is a private belief. BUILT.

**A gate wherever a pen is, and nowhere else.**
Deciding happens in exactly one place per record, beside the rules in force. Everything else, history, content, views, may live anywhere. On the way to a decision every view a change touches may mark it go or no-go, and the mark stays on the record forever; but a mark is sight, and only the gate has force. No permission executes without leaving a verifiable form: power that leaves no trace does not run. One pen and its gate are BUILT, and run on our own kernel. Many machines are DESIGNED.

**Every actor in a box with two openings.**
One opening faces its user, one faces the system, and there is no third. Actors never talk to each other directly; the system is the only medium, which is why the record is complete. The person holds one opening only, and that is what makes the person the end user. An AI organisation, multiple perspectives with separated powers under its own constitution in the system's rule format, is a tenant of this box, not a special case of it. Unstructured work is delegated to it; structured work is always performed by the system. The two openings are BUILT and PROVEN IN TEST WORLDS; the box for every program at load is DESIGNED; the AI organisation inside it is DESIGNED.

**One handshake for everything outside.**
Who, by signature; what code, by fingerprint; sane memory, by the record chain; then one signed row and one signed receipt. A device, a foreign program, another organisation, a person: the same mechanics, graded by what each can prove. The border and the receipt are BUILT and PROVEN IN TEST WORLDS; the grading is DESIGNED.

**The machine cannot lie about what it runs.**
Our own kernel, with no Linux beneath it, checks its body, its record, its constitution and its keys before its first act, witnessed by two bodies, and refuses to start on a mismatch. The kernel's own definition is rows; its code is derived from them. BUILT, in a virtual machine.

AWIG OS does not prescribe what your rules should say. It guarantees how rules exist, who may act, and that nothing acts unseen. The human owner stands above the whole, never inside it.

## 2. Build method: the record first, and two kernels under one definition

AWIG OS is built record-first. The kernel's definition lives as rows in the record; the running code is derived from those rows at build, and at every waking the built code is checked against the rows by hash; if they disagree, the first act is refused. Two kernels can carry one definition. The active route today is the Python kernel under a Linux carrier, which runs the full estate; beside it stands the freestanding C body, which boots with no Linux beneath it and closed campaign 7: the same acts run under both performers, the numbers read side by side. Nothing above the seam knows which performer is beneath it.

An earlier route, replacing a minimal Linux core subsystem by subsystem, is history and is marked as history in `design/16`. The route in force is `design/47` and `design/54`, and the design map at `design/README.md` says which is which.

The governing layer is an executable specification in the sense that the kernel is tested against it, act for act. It is not a proof. Nothing here is formally verified; seL4 is the precedent for that and the bar this project has not reached.

## 2a. Why a kernel of our own, and not seL4 or Linux

Because the claim is about the record, not the scheduler. seL4 proves isolation; Linux provides everything; neither makes the record the only truth. AWIG OS needs a core whose only writable surface is the record's declared acts (append, write-once, one writer) and where every device effect and every device discovery is a row. Carving that out of Linux means carrying millions of lines that can act without becoming rows; proving it on seL4 means the record law living as a guest on someone else's object model. A small core of our own, read whole and signed, keeps the trusted base enumerable: source files a person can read in a sitting. Linux still serves, where it serves best: as an enclosed driver worker, its crossings declared, refused in its own language, and recorded.

## 3. The theory it runs on

The [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard) is the home of the theory, and under it the [Open Meta-Governance Standard (OMGS)](https://github.com/kfkchau/Open-Meta-Governance-Standard/) is a kernel for governing rules themselves: rules about rules, who may make them, how they change, and how a change is recorded. AWIG OS is that kernel as an operating system: the rule lifecycle becomes the system's change process, the ontology becomes its information schema, and the roles (rule users, rule makers, decision makers) become accounts with recorded, traceable permissions.

OMGS is CC BY 4.0. Anyone can implement it, in any system, open or closed, without contacting this project.

## 4. Milestone 0: the seed

The first runnable milestone is deliberately minimal:

> One rule executes in the standard format; one permission runs and leaves a verifiable trace; a third party can independently verify both.

Everything since, the full rule engine, the border, the kernel, grew from that seed, the one a stranger can run.

## 5. What ships, and the one warning

The runnable code is in the [`code`](./code/) folder, generated from the private source and checked, never edited by hand: the governing layer, its tests and tools, and the kernel's source under `code/src/body`. No bytes of anyone else's code are included; the two inputs the full kernel build takes from your own machine are named in [`THIRD-PARTY.md`](./THIRD-PARTY.md). [`STATUS.md`](./STATUS.md) says in plain words what you can try today, what exists but is not public yet, and what is only designed.

One warning matters to anyone who runs it on real data. The locks are real only once you install the named library; until then the keys are stand-ins of the right shape, and in both states the disk and the machine's memory are readable by whoever holds them. In the build team's exact words:

> Real cryptography is in this code and is off until you turn it on. Install the one vetted library it names and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did, with keys that are stand-ins of the right shape; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.

Two things about the numbers. The commits named in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belong to the private repository and cannot be looked up from here; the tags `milestone-0-seed`, `c4-close`, `c5-close` and `c7-close` on this repository are the anchors you can check. And the test suite now ships: `code/run_public_suite.py` runs the tests that can run on a stock machine and prints, for each one it skips, what it would need, so any test count we publish names the machine it ran on.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project, delivered under the [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard).
For attribution, citation, or inquiries: [https://au.linkedin.com/in/kfkchau](https://au.linkedin.com/in/kfkchau)
