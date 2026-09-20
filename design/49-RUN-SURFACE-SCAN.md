<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: design-seed ·
     Vocabulary is OS-architecture (bodies, actors, record, gate, rule). NON-GOAL: no offensive
     capability of any kind. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=DESIGN status=PROPOSED verified=2026-09-07 -->

# 49 — THE RUN-SURFACE SCAN: every digital thing that runs, and whether gov-os can govern it well, now and on the ladder

Written at the architect's hand on the owner's word, 2026-09-07 ("scan all the
digital item that has a thing to run, os or not, and test gov-os current and
gov-os future whether we have confidence it can do it well"). A SCAN for the
owner's correction, not law. Every "now" grade is SOURCE-DERIVED from this
estate's record (what has been built and driven); every "future" grade is
**Estimate —** against the horizon ladder (charter) and the air seed
(design/48), trained knowledge on the platforms, confidence stated per row.
Nothing here mints a campaign; D08.25 ambition calibration governs.

## 1 — The lens: three shapes gov-os can take on a thing

A thing that runs is governed by gov-os in one of three shapes, and the
scan grades each item by the shape that fits it, never by "runs gov-os":

    FULL BODY      the thing holds its own record and gate: the append-only
                   record on its storage, every act crossing the gate, views
                   computed. Needs memory, storage, processing (design/48 §5).
    STAGE MACHINE  the thing holds ONE lifecycle stage's rows (D08.27-29):
                   for real-time things, the ENFORCEMENT carve-out — a compiled
                   rule check, 1/0, outcomes batched behind a recorded grant;
                   the other stages live on other records reached by handshake.
    ACTOR ONLY     the thing cannot hold a record; it writes rows (or has rows
                   written about it) into a nearby body's record. The row
                   grammar without the engine (the air rider, sentence 1).

"Now" means the estate as driven today: a Python program on Linux, one
machine, founding 1.38.0, files/memory/scheduling record-governed (C3),
keys modelled, no networking. "Ladder" names the rung that opens the item:
C5 networking · C6 many records / stage machines · C7 own core, bodies ·
AIR the exposing stream · KEY real key material.

## 2 — The scan

Confidence: HIGH = driven on this estate or a direct port of a driven thing ·
MEDIUM = the shape fits and the estate has proven the mechanism elsewhere,
untested here · LOW = the shape fits on paper only, a named unknown stands.

| # | thing that runs | what runs it | shape | NOW | opens at | FUTURE | the one fact that decides it |
|---|---|---|---|---|---|---|---|
| 1 | laptop / desktop | Linux (the other desktop operating systems: same shape, different host) | FULL BODY | HIGH on Linux, LOW elsewhere | now / AIR for other hosts | HIGH | this estate IS one; the M3 and W4 worlds are laptop records |
| 2 | server, cloud VM, container | Linux under a hypervisor or a container runtime | FULL BODY | HIGH | now; C5 for many | HIGH | a guest is a laptop with a different body check (D08.23); our own guest runs the kernel arms |
| 3 | fleet of servers / orchestrated cluster | Kubernetes-class orchestrators | STAGE MACHINE per node + a decision record | LOW | C5 → C6 | MEDIUM | the transport and one-machine-per-stage-per-scope rule (D08.30); orchestration is the deciding half, parked (charter VM-2) |
| 4 | hypervisor itself | ESXi, KVM, Xen, Hyper-V | FULL BODY (deciding half) / own core (hardware half) | LOW | C6 (deciding) · C7 (hardware) | MEDIUM / LOW | the hardware half is swap-the-core; the deciding half is grant rows + handover (parked VM-2) |
| 5 | phone / tablet | the phone operating systems — sandboxed apps, store gate | FULL BODY inside one app's sandbox; ACTOR beyond it | LOW | AIR (grammar as a library) · C7 for the OS | MEDIUM | the sandbox is a body the host vouches for; the store gate is an outside decision record; no root access is not a blocker, it is the guest pattern |
| 6 | browser / web runtime | JS engine, WASM | FULL BODY in-page (small) · ACTOR (extension) | LOW | AIR | HIGH for ACTOR, MEDIUM for BODY | the owner's browser-extension-first (D08.21): an extension writes rows; a WASM port of the gate is a port, not a gap — a row is a JSON line |
| 7 | database / ledger / blockchain | its own engine; smart contracts | the nearest cousin: a record with rules | n/a (a peer, not a host) | AIR · C5 | HIGH as PEER | a smart contract is rule-as-data on a shared record with many pens — the many-pens construct we deliberately did not mint; relate by handshake, never merge |
| 8 | mainframe / legacy (COBOL, z/OS) | its own OS, batch | ACTOR (rows written about its acts) · FULL BODY beside it | LOW | AIR | MEDIUM | legacy without translation (D08.11): the record wraps the legacy act as a row; the legacy code never changes |
| 9 | network gear (router, switch, firewall) | Linux/BSD control plane + ASIC data plane | STAGE MACHINE (control plane decides; data plane = enforcement carve-out) | LOW | C5 | MEDIUM | the data plane is the purest 1/0 enforcement at line rate; a rule change is a control-plane row; C5 is literally this box's sockets (design/44) |
| 10 | industrial controller (PLC, SCADA) | RTOS or bare metal, scan cycles | STAGE MACHINE (enforcement) | LOW | C7 (own core) + hard-timing measurement | MEDIUM | a scan cycle IS a batch; the rule decides once, the cycle runs under it; worst case unmeasured (D08.30) |
| 11 | car: infotainment | Linux and the car operating systems | FULL BODY | LOW | AIR / C7 | HIGH | a laptop with a screen; nothing new |
| 12 | car: brake / engine / ADAS controller | AUTOSAR RTOS, bare metal; ISO 26262 | STAGE MACHINE (enforcement) | LOW | C7 + measurement + certification (outside us) | LOW-MEDIUM | bounded worst case per decision must be MEASURED and then CERTIFIED by a body outside this estate; the shape is right, the proof is not ours yet |
| 13 | medical device / implant | RTOS, bare metal; regulated | STAGE MACHINE / ACTOR | LOW | C7; regulation outside | LOW | same as 12 with tighter memory; the recorded refusal is what a regulator wants, but the certification road is long |
| 14 | avionics / spacecraft | partitioned RTOS (ARINC 653), rad-hard | STAGE MACHINE per partition | LOW | C7 | LOW | partitions ARE bodies with a host vouching (D08.23); radiation makes the chain's byte-level detection valuable; nothing measured |
| 15 | robot / drone | Linux (ROS) + RTOS controllers | FULL BODY (Linux half) + STAGE MACHINE (controllers) | MEDIUM (Linux half) | now / C7 | HIGH / MEDIUM | two records, one handshake — the host/guest pattern on wheels |
| 16 | TV, set-top, console, camera | the television operating systems, proprietary | FULL BODY | LOW | AIR / C7 | HIGH | a laptop with fewer actors; the store/update gate is an outside decision record |
| 17 | appliance / sensor (bare-metal MCU) | no OS; a firmware loop; KB of RAM | ACTOR ONLY (or the smallest enforcement carve-out) | LOW | AIR | HIGH as ACTOR, LOW as BODY | below the memory line (design/48 §5): it writes rows, a nearby body keeps the record; a hash-chained append per act may not fit — unmeasured |
| 18 | secure element / TPM / smart card / HSM | tiny fixed-function OS | ACTOR (the witness) | LOW | C7 (diving-buddy) · KEY | HIGH as WITNESS | this is the second witness with no shared write path (design/47 §4): it holds genesis, not a record |
| 19 | GPU / accelerator | no OS; kernels dispatched by a host | ACTOR (dispatched under a granted rule) | n/a | C7 | MEDIUM | the host's record grants; the accelerator never holds a record — same as memory grants today |
| 20 | FPGA / configurable hardware | a bitstream, no OS | STAGE MACHINE compiled to gates | LOW | C7 | LOW-MEDIUM | "the rule is data, the executor is fixed" taken to its end: the compiled rule check as a circuit; nobody has tried |
| 21 | serverless function / edge WASM | a runtime that starts per call | ACTOR (each call a row) · BODY at the edge node | LOW | AIR / C5 | HIGH as ACTOR | a function that keeps no state is an act; the record lives at the node that invoked it |
| 22 | AI agent / model runtime | a host program; the model acts | ACTOR (the newest actor class) | MEDIUM | now (design/45) | HIGH | co-intelligence acceptance is already a paper: an AI is an actor whose acts cross the gate like anyone's |
| 23 | the seats of this estate (AI sessions) | [an AI coding assistant] on Linux | ACTOR + a record (the board) | HIGH | now | HIGH | "how we dev = how gov-os is" (D08.9): the board is an append-only record with a fold; the transport law is a permission row |
| 24 | quantum computer | a classical host controls it | ACTOR (via its host) | n/a | never as a body | n/a | it holds no record; its host does |

## 3 — What the scan says, in five lines

1. **Nothing on the list is a wall.** Every row has a shape; the shapes are
   three, and two of them (STAGE MACHINE, ACTOR) were the owner's own moves
   this week (D08.27-29, D08.21). The OS-first roadmap holds (D08.26).
2. **"Now" is honest and narrow:** HIGH only where Linux is underneath and
   Python runs — laptop, server, VM, container, the Linux half of a robot,
   an AI actor. Everything else is LOW now, not because of a gap but because
   nothing has been run there.
3. **Three rungs open almost everything:** AIR opens every ACTOR row
   (phone, browser, sensor, legacy, serverless) because a row is a JSON line
   anyone can write; C5 opens the fleet and network rows; C7 opens the
   real-time and no-OS rows through the enforcement carve-out.
4. **Four rows carry a named unknown that no rung answers by itself:**
   the hard-timing worst case (10, 12, 13, 14 — a measurement, D08.30), the
   tiny-memory fit (17 — a measurement), outside certification (12, 13 — not
   ours to grant), and the compiled-to-hardware rule (20 — untried).
5. **One row is a peer, not a host:** ledgers and smart contracts (7) are
   the many-pens construct on one record; gov-os relates to them by
   handshake and never merges with them.

## 4 — What would raise a grade (each a measurement or a port, none a redesign)

- **The enforcement carve-out compiled** (opens 9, 10, 12-14, 20): a C or
  Rust build of the rule check + batch writer, driven for worst-case
  latency on one RTOS. C7's first spike candidate after the live-move test
  (charter VM-1).
- **The row grammar as a library** (opens 5, 6, 17, 21): the JSON-line
  writer + verifier with no engine, with its conformance test (air rider
  sentence 2). AIR's first join.
- **The tiny-memory fit** (17): the smallest RAM at which a chained append
  still runs, measured, published as the line design/48 §5 draws in words.
- **Two records on two bodies** (3, 9, 15): C5's own first behaviour.

## 5 — Honest caps

Trained knowledge on every platform named (uncitable; the owner's own
sources control where they differ). No item outside 1, 2, 22, 23 has been
run. "Well" is graded as fit of shape and presence of a proven mechanism,
not as measured performance — the only performance figures this estate
holds are C3's one-machine batching band and the fault/dispatch tensions.
Certification regimes (12-14) are outside this estate's power to grant.
Nothing here changes the ladder or seeds a campaign (D08.25).
