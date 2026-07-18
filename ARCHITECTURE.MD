# AWIG OS — Architecture

This document holds the technical design of AWIG OS. The philosophy it implements lives in the [README](./README.md); this is the machine that carries it.

---

## 1. Five architectural commitments

**Everything as information.**
All system state, events, and actions are represented as structured information. Rules are derived from and act upon information; nothing operationally relevant is opaque.

**One rule format.**
Every rule in the system — from access control to automation policy — follows the same executable format. There is no privileged rule syntax for privileged actors. Each deployment's complete rule set is its *awig-awig*: self-written, legible, machine-executable.

**Full permission traceability.**
No permission executes without leaving a verifiable form. Authorisation, exercise, and outcome are all recorded in the same information layer the rules run on. Power that leaves no trace does not run.

**A constitutional AI organisation.**
AI capability is structured as an organisation, not an oracle: multiple perspectives, separated powers over separate concerns, collective decision-making, governed by a modular constitution expressed in the system's own rule format. The AI organisation touches the world through exactly two points: a narrow, default-closed tunnel to the system, and an air-gapped read of user text.

**Glass-box containment, owner on top.**
The AI organisation is inspectable from outside and structurally bounded from inside. Unstructured-data transformation is delegated to the AI organisation; structured-data transformation is always performed by the OS. Automation decomposes tasks into atomic units, routes each to OS or AI as appropriate, and recombines the results — with the human owner above the combined automation, never inside it.

AWIG OS does not prescribe what your rules should say. It guarantees how rules exist: one format, legible, executable, traceable.

## 2. Build method — reference model first

AWIG OS is being rebuilt layer by layer from a running reference model, following the verified-kernel tradition (an executable specification first; the production implementation written and checked against it):

1. **Reference model** — a complete, running reimplementation of the original minimal Linux core (~10k LOC scope; no device drivers), currently ~99% Python. This is the executable specification: it defines 100% of required behaviour.
2. **Layer-by-layer replacement** — each layer of the reference core is replaced by the new governance-native core while the whole remains running and behaviour-verified against the model ("replace the heart while the robot keeps walking").
3. **Behavioural compatibility** — the system preserves the syscall-level contract, so it is *Linux-compatible* to the programs above it while being independent code beneath.

The result is a **clean-room reimplementation**: written from behaviour and interfaces, not translated from Linux source. It is Linux-compatible, not Linux; "Linux" is a trademark of Linus Torvalds and is not claimed by this project. The reference model is preserved permanently in the repository history as the project's lineage.

## 3. Relationship to the Open Governance Framework

The theory underlying AWIG OS begins at the [**Open Governance Framework**](https://github.com/kfkchau/open-governance-framework) — the umbrella and definitive home of the complete governance theory infrastructure. Underneath it sits the full body of work: the shared concepts and ontology for rule systems, the rule lifecycle model, and the standards that formalise them, chief among them the [Open Meta-Governance Standard (OMGS)](https://github.com/kfkchau/Open-Meta-Governance-Standard/) — a domain-agnostic kernel for governing rules themselves. AWIG OS is the operating-system embodiment of that infrastructure.

- **OMGS** defines the concepts, ontology, and rule lifecycle model: the rule ecosystem; actors (rule users, rule makers, decision makers); artefacts (rules, rule submissions, rule content); the coupled proposal and implementation cycles.
- **AWIG OS** implements that kernel at the operating-system layer: the OMGS rule lifecycle becomes the system's actual change-management pipeline; the OMGS ontology becomes the system's information schema; OMGS actors become roles with enforced, traceable permissions.

Earlier expressions of the kernel (the 2021 Governance Lifecycle Framework and the 2025 [Universal Governance Lifecycle Standard](https://github.com/kfkchau/gov-lifecycle/)) are documented in the OMGS repository. OMGS (CC BY 4.0) can be implemented by anyone, in any system, open or closed, without any license contact with this repository; AWIG OS is its open reference implementation.

## 4. Milestone 0 — the seed

The first runnable milestone is deliberately minimal:

> One rule executes in the standard format; one permission runs and leaves a verifiable trace; a third party can independently verify both.

Everything else — the full rule engine, the AI organisation, the automation splitter — grows from that verified seed.

---

© Kelvin Chau, 2026 · This document: CC BY 4.0 · Part of the AWIG OS project.
