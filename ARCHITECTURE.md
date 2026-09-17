# AWIG OS: the architecture

This document holds the technical design of AWIG OS. The philosophy it implements lives in the [README](./README.md). This is the machine that carries it.

---

## 0. How to read this work

The code you can run is a reference model of the governing layer: an executable specification, built first so that the rules, the record and the gate run and can be tested before the kernel underneath them exists. Read it as that, not as a finished product. seL4 was built the same way, a running model before the real kernel, and the model is what the kernel is checked against. The line the model draws runs between the unstructured and the structured, what is said and what is done: prose, an AI's included, never moves the system; a structured row that passed a rule does, and the crossing is the gate.

The design papers in `design/` are the contracts that model implements; the map at `design/README.md` names the ten contracts in force, each with its paper and its code, and the note at `design/00-RENDER-NOTE.md` lists every paper with its status. `STATUS.md` says what is true today, machine by machine. The kernel is being built underneath the same contracts, in the private repository, and arrives here when a stranger can boot it.

A defect in a mechanism is not a defect in its contract, and the pages say which is which: a test that fails is listed with what it needs; a promise the code does not yet keep is listed under what is not true yet.

The fence and the two openings. An agent behind a fence holds one permission set for a session and acts directly on everything inside it; the known failure is a document that turns the agent, and the fence has no answer because the agent's act is its own. Here an AI organisation is an entity with two watched openings, the demand side and the supply side. A turned document arrives on the demand side. Whatever the organisation then wants arrives on the supply side as a proposal the gate decides against the rulebook, and taking data out needs a grant that was never made, so the proposal comes back as a refusal row citing the rule. What this bounds is the damage, to the grant set; a turned organisation with a grant can misuse the grant. The border that makes an outside submission a draft the gate decides is built and proven in test worlds between a host and a guest (design 49, `bridge/`); the organisation between the openings is a stand-in pack today (design 51, EP-51).

## 0a. What the rules cannot change

Every act crosses the gate, and the rules decide it. Four kinds of row reach the record without being decided at the gate, and they are named here, each with the file that writes it, so that "one gate" is read exactly. The founding rows, written when a system is born: the gate cannot decide its own birth (`src/kernel/gate.py`, the constitution guard). The two audit streams, each a copy of what was just appended, written blind to each other (`src/kernel/protection.py`). The chain anchor, one row that seals the hash of everything before it, written by a ceremony and never by an act (`src/kernel/store.py`). And the gate's own rows: a refusal, and the failure of an effect that was allowed and then did not complete, written by the gate itself under the rule the act cited (`src/kernel/gate.py`, `refuse` and `_record_effect_failure`). Below the rules there is also a floor the rules do not reach: how a row is written and that no row is ever changed or removed; how each row names the one before it; how the gate itself proceeds, a refusal written before it is raised; which rules are fixed at the founding and cannot be amended; and how the rows are turned into views. A rule can govern any act. A rule cannot change what a row is.

## 1. Five architectural commitments

**Everything as information.**
All system state, events, and actions are represented as structured information. Rules are derived from and act upon information. Nothing operationally relevant is opaque.

**One rule format.**
Every rule in the system, from access control to automation policy, follows the same executable format. There is no privileged rule syntax for privileged actors. Each deployment's complete rule set is its *awig-awig*: self-written, legible, machine-executable.

**Full permission traceability.**
No permission executes without leaving a verifiable form. Authorisation, exercise, and outcome are all recorded in the same information layer the rules run on. Power that leaves no trace does not run.

**A constitutional AI organisation.**
AI capability is structured as an organisation, not an oracle: multiple perspectives, separated powers over separate concerns, collective decision-making, governed by a modular constitution expressed in the system's own rule format. The AI organisation touches the world through exactly two points: a narrow, default-closed tunnel to the system, and an air-gapped read of user text.

**Glass-box containment, owner on top.**
The AI organisation is inspectable from outside and structurally bounded from inside. Unstructured-data transformation is delegated to the AI organisation; structured-data transformation is always performed by the OS. Automation decomposes tasks into atomic units, routes each to OS or AI as appropriate, and recombines the results, with the human owner above the combined automation, never inside it.

AWIG OS does not prescribe what your rules should say. It guarantees how rules exist: one format, legible, executable, traceable.

## 2. Build method: reference model first, then a kernel of our own

The order of work is fixed: the governing layer first, as a running reference model in Python, so that the record, the gate, the rules and the views run and are tested before any kernel exists beneath them; then a kernel written from a blank page beneath a declared seam. The seam names twelve kinds of work. The kernel performs exactly those, and everything above the seam is unchanged. Programs above it see a Linux-compatible surface; the code beneath is ours, written from behaviour and interfaces, not from Linux source. "Linux" is a trademark of Linus Torvalds and is not claimed by this project.

An earlier route, replacing a minimal Linux core subsystem by subsystem, is history and is marked as history in `design/16`. The route in force is `design/47` and `design/54`, and the design map at `design/README.md` says which is which.

The reference model is an executable specification in the sense that the kernel is tested against it, act for act. It is not a proof. Nothing here is formally verified; seL4 is the precedent for that and the bar this project has not reached.

## 2a. Why a kernel of our own, and not a layer on seL4 or Linux

The governing layer runs on Linux today, and a pilot runs it that way. It cannot be the whole answer. A kernel we did not write has its own doors to the disk, the network and the devices, and any program it runs can use them; our gate sees none of that. A program in a box with two doors has a third door the moment the box sits on someone else's kernel. The only way to close it is a kernel that opens nothing except through the gate. So the kernel beneath the seam is ours, and it does the twelve kinds of work and nothing else. seL4 is the nearest thing to it: small, authority held as capabilities, proofs of what it does. Its proofs are the bar. What it does not do is what we need beneath the gate: the record under every act, the border at the wire, custody of content, the two doors. That is why the kernel is written and not borrowed.

## 3. The theory it runs on

The [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard) is the home of the theory, and under it the [Open Meta-Governance Standard (OMGS)](https://github.com/kfkchau/Open-Meta-Governance-Standard/) is a kernel for governing rules themselves: rules about rules, who may make them, how they change, and how a change is recorded. AWIG OS is that kernel as an operating system: the rule lifecycle becomes the system's change process, the ontology becomes its information schema, and the roles (rule users, rule makers, decision makers) become accounts with recorded, traceable permissions.

OMGS is CC BY 4.0. Anyone can implement it, in any system, open or closed, without contacting this project.

## 4. Milestone 0: the seed

The first runnable milestone is deliberately minimal:

> One rule executes in the standard format; one permission runs and leaves a verifiable trace; a third party can independently verify both.

Everything else, the full rule engine, the AI organisation, the automation splitter, grows from that seed, the one a stranger can run.

## 5. What ships, and the one warning

The runnable code is in the [`code`](./code/) folder, generated from the private source and checked, never edited by hand. [`STATUS.md`](./STATUS.md) says in plain words what you can try today, what exists but is not public yet, and what is only designed.

One warning matters to anyone who runs it on real data. The locks are real only once you install the named library; until then the keys are stand-ins of the right shape, and in both states the disk and the machine's memory are readable by whoever holds them. In the build team's exact words:

> Real cryptography is in this code and is off until you turn it on. Install the one vetted library it names and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did, with keys that are stand-ins of the right shape; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.

Two things about the numbers. The commits named in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belong to the private repository and cannot be looked up from here; the tags `milestone-0-seed`, `c4-close` and `c5-close` on this repository are the anchors you can check. And the test suite now ships: `code/run_public_suite.py` runs the tests that can run on a stock machine and prints, for each one it skips, what it would need, so any test count we publish names the machine it ran on.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project, delivered under the [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard).
For attribution, citation, or inquiries: [https://au.linkedin.com/in/kfkchau](https://au.linkedin.com/in/kfkchau)
