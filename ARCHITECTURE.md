# AWIG OS: the architecture

This document holds the technical design of AWIG OS. The philosophy it implements lives in the [README](./README.md). This is the machine that carries it.

---

## 0. How to read this work

The code you can run is a reference model of the governing layer: an executable specification, built first so that the rules, the record and the gate run and can be tested before the kernel underneath them exists. Read it as that, not as a finished product. seL4 was built the same way, a running model before the real kernel, and the model is what the kernel is checked against.

The design papers in `design/` are the contracts that model implements; the note at `design/00-RENDER-NOTE.md` lists every paper with its status, and a one-page map of the contracts in force is being written. `STATUS.md` says what is true today, machine by machine. The kernel is being built underneath the same contracts, in the private repository, and arrives here when a stranger can boot it.

A defect in a mechanism is not a defect in its contract, and the pages say which is which: a test that fails is listed with what it needs; a promise the code does not yet keep is listed under what is not true yet.

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

## 2. Build method: reference model first

AWIG OS is being rebuilt layer by layer from a running reference model, in the verified-kernel tradition: an executable specification first, with the production implementation written and checked against it.

1. **Reference model.** A complete, running reimplementation of the original minimal Linux core (no device drivers in scope), implemented in Python. This is the executable specification. It defines the required behaviour the production core is checked against.
2. **Layer-by-layer replacement.** Each layer of the reference core is replaced by the new governance-native core while the whole remains running and behaviour-verified against the model. Replace the heart while the robot keeps walking.
3. **Behavioural compatibility.** The system preserves the syscall-level contract, so it is *Linux-compatible* to the programs above it while being independent code beneath.

The result is a clean-room reimplementation: written from behaviour and interfaces, not translated from Linux source. It is Linux-compatible, not Linux. "Linux" is a trademark of Linus Torvalds and is not claimed by this project. The reference model is preserved permanently in the repository history as the project's lineage.

## 3. The theory it runs on

The [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard) is the home of the theory, and under it the [Open Meta-Governance Standard (OMGS)](https://github.com/kfkchau/Open-Meta-Governance-Standard/) is a kernel for governing rules themselves: rules about rules, who may make them, how they change, and how a change is recorded. AWIG OS is that kernel as an operating system: the rule lifecycle becomes the system's change process, the ontology becomes its information schema, and the roles (rule users, rule makers, decision makers) become accounts with recorded, traceable permissions.

OMGS is CC BY 4.0. Anyone can implement it, in any system, open or closed, without contacting this project.

## 4. Milestone 0: the seed

The first runnable milestone is deliberately minimal:

> One rule executes in the standard format; one permission runs and leaves a verifiable trace; a third party can independently verify both.

Everything else, the full rule engine, the AI organisation, the automation splitter, grows from that verified seed.

## 5. What ships, and the one warning

The runnable code is in the [`code`](./code/) folder, generated from the private source and checked, never edited by hand. [`STATUS.md`](./STATUS.md) says in plain words what you can try today, what exists but is not public yet, and what is only designed.

One warning matters to anyone who runs it on real data. The locks are real only once you install the named library; until then the keys are stand-ins of the right shape, and in both states the disk and the machine's memory are readable by whoever holds them. In the build team's exact words:

> Real cryptography is in this code and is off until you turn it on. Install the one vetted library it names and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did, with keys that are stand-ins of the right shape; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.

Two things about the numbers. The commits named in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belong to the private repository and cannot be looked up from here; the tags `milestone-0-seed`, `c4-close` and `c5-close` on this repository are the anchors you can check. And the test suite now ships: `code/run_public_suite.py` runs the tests that can run on a stock machine and prints, for each one it skips, what it would need, so any test count we publish names the machine it ran on.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project, delivered under the [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard).
For attribution, citation, or inquiries: [https://au.linkedin.com/in/kfkchau](https://au.linkedin.com/in/kfkchau)
