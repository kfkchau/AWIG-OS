<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=SUPERSEDED supersedes=- superseded-by=design/28-TARGET-STATE-HOST-KERNEL.md verified=2026-07-24 -->
# GOV-OS — Operations Catalogue (the registered surface of the gate)

> **SUPERSESSION NOTE (2026-07-18 line-audit; completed 2026-07-19).** SUBSTANTIALLY
> SUPERSEDED in mechanism: operations are now DEFINITION RECORDS — all five cores plus
> CREATE-RULE enter as `op_definition` records (CREATE-OP / AMEND-OP / RETIRE-OP)
> executed by ONE generic interpreter; the registry is DERIVED from the record and
> rebuilt on replay (EP-01..05C); refusal logic lives in the closed check vocabulary
> (require_prior / sight / ceiling / consistency / sop / due / definition_ref) plus the
> gate's constitution guard, not per-op prose; refusal precedence is the documented
> execution order (the R13 ruling). The op INVENTORY, plain-words intents, and refusal
> conditions here still stand as reference. Live catalogue: design/28 §3/§5 + the
> genesis seed in `src/kernel/boot.py`. Live canon controls on conflict.
> *(Repair note: the 07-18 audit's note was truncated mid-write on disk — the audit's
> "verified 15/15" claim was false for this file. Wording above restored 2026-07-19 by
> the sitting mentor from the audit's own log entry ["Superseded in mechanism, content
> useful: 12 (ops→records)"] and the live canon; logged in BUILD-PROGRESS.)*

**Status:** v0.1, 2026-07-12, Route-A assumption (§7A of `03-TARGET-STATE-ARCHITECTURE.md`: hollow-out — subsystems replace Linux behind unchanged interfaces; the operation *names* here are the governed layer, the Linux syscall port sits above them). Read `00-READ-FIRST.md`, then `03-TARGET-STATE-ARCHITECTURE.md` (the gate) before this. Labels per contract: SOURCE-DERIVED (cites), INFERRED (from what), PROPOSED (cost if wrong), trained knowledge (flagged). Linux syscall shapes named for the port are trained knowledge.

---

## Intro

This catalogue enumerates every governed operation the kernel exposes through its gate (L1 of the layer stack). In a conventional kernel these are the actions behind syscalls — mutating the run-queue, mapping a page, writing an inode, binding a driver, queuing a message. Here each is a *registered operation* that does exactly one of two things: it produces a recorded decision citing the law it applied, or it refuses and records the refusal citing the rule that refused. There is no third path and no unrecorded write. The registry's enumeration is the completeness guarantee — the bank has no counter (`DESIGN-CONCEPTS.md` P3): an operation not in this catalogue **does not exist**, and invoking it is a Closure Hit, recorded and escalated, never massaged into a neighbour. Operations are grouped by the five governed subsystems, preceded by the bootstrap operations that boot the machine into a state where a gate exists at all. Every field — actor class, decision shape, refusal conditions with cited rules — is a design contract, not code.

---

## Conventions (read once, applies to every entry)

### The decision shape

Every operation that succeeds appends **one decision record** in the estate envelope
(`02-TECHNICAL-ARCHITECTURE.md` §1.1), an AAOT atom with provenance:

```jsonc
{
  "record_id": "…", "seq": 0,              // identity + total order (minted at append)
  "record_time": "…",                       // SOLE total-order anchor
  "recorder_id": "SYSTEM",                   // the sole governed-state writer (see actors)
  "asserted_by": "<invoking actor>",         // who requested the act
  "actor": "<invoking actor>",               // AAOT: who
  "action": "<operation name>",              // AAOT: which registered op
  "object": "<what was acted on>",           // AAOT: e.g. a pid, region, path, device
  "target": "<result/context>",              // AAOT: e.g. a priority class, mapping id
  "rule_cited": "<LAW record id>",           // the law this decision applied — ALWAYS present
  "evidence_summary": {},                    // §2 [AUDIT-FIX 3] embedded aggregate, when a
                                             //   decision acted on sampled stream evidence
  "refs": [], "content_form": "…", "payload": {},
  "provenance": {}                           // sight-gate input: what the requester could read
}
```

A **refusal** is the same envelope with `action` = the attempted operation, a
`refused: true` marker, `rule_cited` = the rule that refused, and a `reason`
string. **A refusal is itself a recorded event** — Attribution and Explanation
(audit guarantees §1.1–1.2) hold for denials exactly as for grants. There is no
`errno`-that-forgets-its-rule here (the §0 diagnosis: "enforcement cannot explain
itself").

### Actor classes (who may invoke)

SOURCE-DERIVED from the foundational import pack §02 (boot actors) and §07
(authorisation by rule chain), generalised to the kernel by the target-state doc.

| Class | Who it is | Write power |
|---|---|---|
| **PC_RUNTIME** | External setup actor; exists only during boot | Creates the first objects, then hands off and never writes again |
| **SYSTEM** | The kernel's governed-execution actor; every subsystem handler runs *as* SYSTEM | The **only** actor that writes governed state after boot |
| **OWNER/ADMIN** | Root instruction authority | Never mutates directly; sends messages through the authorised tunnel; SYSTEM records the resulting decisions |
| **SUBSYSTEM** | The five departments (SCHED, MEM, FS, DEV, COMM) | Propose decisions within their own LAW; the decision is written by SYSTEM |
| **PROCESS** | Userland actor reaching the gate through the syscall port | Requests operations; never a governed-state writer — its request becomes a SYSTEM decision that attributes it |
| **AUDITOR** | Read-only oversight actor (separation of powers, twc R25) | No state-changing invocation; views only (see `13-VIEWS-AND-PROC-CATALOGUE.md`) |

"Invoked by" below names the *requesting* class; SYSTEM is always the recorder.

### The rule namespace (what a refusal cites)

Refusals cite a LAW record. LAW is amendable data with named authority
(target-state §2 LAW class), so these ids are handles into the record, not
constants in code. Root rules are SOURCE-DERIVED from the boot sequence
(foundational pack §09) and TWC first principles; subsystem LAW ids are PROPOSED
(cost if wrong: a subsystem needs a different rule decomposition — cheap to
re-key, the shape holds).

**Root rules (boot-established, cross-cutting):**
- `ROOT-NEG-1` — no valid authorising rule chain → no state-changing activity.
- `ROOT-NEG-3` — sender not authorised for this operation → no governed write.
- `ROOT-NEG-4` — no authority check performed → no state-changing activity.
- `ROOT-NEG-5` — no event record producible → no valid state-changing activity.
- `ROOT-NEG-6` — no contradiction check → no activation of a new/changed rule.
- `BOOT-INT` — SYSTEM must not enact a change that destroys a boot condition
  (integrity rule, foundational pack §08).
- `P3-CLOSURE` — invoked operation is not registered → Closure Hit (bank-has-no-counter).
- `P4-REFUSE` — a failed gate refuses and cites; it never improvises a workaround.
- `SIGHT-IS-LAW` — an actor may not act on what it could not read (provenance
  gate, twc R25; target-state §3 Protection).
- `CAP-IS-LAW` — a capability grant is a recorded amendment with named authority,
  not a config edit (twc R14; target-state §4.4).
- `SOP` — separation of powers: deciding ≠ executing; a maker may not review its
  own object (target-state §4.4, §3).

Subsystem LAW ids appear inline in each entry (`SCHED-LAW-*`, `MEM-LAW-*`,
`FS-LAW-*`, `DEV-LAW-*`, `COMM-LAW-*`).

### The one refusal every operation shares

Beyond its own conditions, **every** operation inherits the root refusals:
unauthorised requester (`ROOT-NEG-3`), un-recordable act (`ROOT-NEG-5`), and — if
the operation would change law — un-checked contradiction (`ROOT-NEG-6`). These
are not repeated per entry; they are the floor. Each entry lists only its
*additional* subsystem-specific refusals.

---

## Section 0 — Bootstrap operations (the foundational import pack)

SOURCE-DERIVED verbatim from `reference\corpus\05_Venn2...\00_foundations\venn2-foundational.md`
§01 (the twelve-template pack) and §09 (boot sequence). These are the operations
that exist *before* a subsystem does — they build the gate, the record, the first
actors, and the root rules, then hand off. They are registered like everything
else: after boot, they remain the only way new law, actors, and tunnels enter the
record.

### READ
- **Plain words:** move an information resource into the system's active context so
  it can be reasoned over. Not a state change — a precondition to one.
- **Subsystem:** bootstrap (used by all).
- **Invoked by:** SYSTEM (and, at boot, PC_RUNTIME).
- **Records:** a READ activity (`actor` SYSTEM, `object` the resource, `target`
  active context). READ is what *populates provenance* for a later decision — this
  is the mechanical root of `SIGHT-IS-LAW`.
- **Refusals:** resource not in a readable view for this actor → cite `SIGHT-IS-LAW`.

### FOLLOW
- **Plain words:** apply a named rule object to produce a conclusion, activity, or
  record. The mechanical act of "the law was applied here."
- **Subsystem:** bootstrap.
- **Invoked by:** SYSTEM.
- **Records:** a FOLLOW activity linking the rule (`object`) to what it produced
  (`target`); this link is what later lets a view answer "under which rule?".
- **Refusals:** rule not in the active rule set → cite `ROOT-NEG-1`; rule
  contradicts an active rule in scope → cite `ROOT-NEG-6`.

### CREATE-INFO / CREATE-ACTIVITY / CREATE-RELATIONSHIP / CREATE-RULE / CREATE-ACTOR / CREATE-TUNNEL
- **Plain words:** the six constructors — mint an information object, an activity
  record, a relationship record, a rule object, an actor, or a communication
  tunnel, respectively, into the master record.
- **Subsystem:** bootstrap (CREATE-RULE and CREATE-TUNNEL remain the *only* ways
  law and channels ever enter — every subsystem LAW change is a CREATE-RULE).
- **Invoked by:** PC_RUNTIME (boot) then SYSTEM (on an authorised OWNER message).
- **Records:** the created object plus a creation activity attributing it; per the
  master-database principle, the object is never "primitive truth" — profiles,
  authority, and status are later *views* over these creation records.
- **Refusals (shared shape):**
  - creator not authorised for this construction → `ROOT-NEG-3`.
  - CREATE-RULE whose rule would destroy a boot condition (disable recording,
    remove authority checking, erase the record, create an authority loop) →
    cite `BOOT-INT` (foundational pack §08 enumerates these exactly).
  - CREATE-RULE that contradicts an active rule in the same scope → `ROOT-NEG-6`.
  - CREATE-ACTOR/CREATE-TUNNEL granting capability without named authority →
    `CAP-IS-LAW`.

### WRITE-ACTIVITY
- **Plain words:** record that an activity happened. This is SYSTEM's broad
  evidence-recording power — permission for SYSTEM to *record* any activity, never
  permission for any actor to *perform* any activity (foundational pack §09.10).
- **Subsystem:** bootstrap; the substrate under every decision record above.
- **Invoked by:** SYSTEM only.
- **Records:** the activity envelope itself. This operation is why a refusal can be
  recorded — it is the write path a denial takes.
- **Refusals:** invoked by a non-SYSTEM actor → `ROOT-NEG-3`.

### CHECK-RULE
- **Plain words:** evaluate whether a proposed activity satisfies the governing
  rule chain — the authority check that must precede any state change.
- **Subsystem:** bootstrap; the gate's own conscience.
- **Invoked by:** SYSTEM (runs inside every state-changing operation).
- **Records:** a check activity producing an authorised/refused conclusion, linked
  to the decision it gates. **Its absence is itself a refusal cause** — an act
  with no CHECK-RULE cannot proceed (`ROOT-NEG-4`).
- **Refusals:** n/a as a standalone (it is the check); a *missing* CHECK-RULE on
  any other op → that op cites `ROOT-NEG-4`.

### CHECK-CONTRADICTION
- **Plain words:** compare a proposed rule/change against the active rule set to
  prevent activating a self-destroying or contradictory law set.
- **Subsystem:** bootstrap; runs before any LAW change in any subsystem.
- **Invoked by:** SYSTEM.
- **Records:** a contradiction conclusion linked to the proposed change.
- **Refusals:** a proposed change that fails the check is not silently dropped —
  SYSTEM records the rejection citing `ROOT-NEG-6` (or `BOOT-INT` if a boot
  condition is threatened), exactly as the corpus's worked example ("SYSTEM
  rejected MSG-200, reason: proposed rule disables event recording").

### BLOCK
- **Plain words:** prevent an activity path and create evidence that it was
  refused. BLOCK is the generic refusal constructor — the recorded "no."
- **Subsystem:** bootstrap; the mechanism behind every refusal in this catalogue.
- **Invoked by:** SYSTEM.
- **Records:** a blocked-state / rejection event citing the rule that blocked.
  This is the operation that makes "every refusal is a recorded event" true at the
  metal.
- **Refusals:** n/a — BLOCK *is* the refusal path.

> **The unregistered case (emphasised).** If a request names an operation that is
> not in this catalogue, no handler exists to run it. The gate does not guess a
> nearest match. It raises a **Closure Hit**: BLOCK records the attempt citing
> `P3-CLOSURE`, and the event is escalated to the owner (target-state §L1;
> `DESIGN-CONCEPTS.md` P3). "Unregistered = does not exist" is not a slogan — it
> is the completeness guarantee that makes the catalogue's enumeration meaningful.

---

## Section 1 — Scheduling (governing attention)

Department LAW = scheduling-policy records: priority classes, link-typed ordering,
standby rules, the halt→kill penalty chain (target-state §4.1; `driver.js`
doctrine — "what fires is decided only by the record"). DECISIONS below are
recorded and rule-cited; per-tick dispatch is STREAM (sampled), never one of these.

### admit-process
- **Plain words:** bring a process into the runnable set — the governed form of
  "make schedulable / fork's tail."
- **Invoked by:** PROCESS (via the port) or SUBSYSTEM; recorded by SYSTEM.
- **Records:** decision `action:admit-process`, `object`:pid, `target`:priority
  class, `rule_cited`:`SCHED-LAW-ADMIT`. Feeds the process-table and scheduler-state
  views.
- **Refusals:**
  - admitting would exceed the requester's process budget → cite `SCHED-LAW-BUDGET`.
  - priority class requested above the requester's authority → cite `SCHED-LAW-PRIORITY`.
  - a halt is in force and the process is not a voice-kind → cite `SCHED-LAW-HALT`.

### deschedule
- **Plain words:** remove a process from the runnable set without ending it
  (block/sleep, governed).
- **Invoked by:** PROCESS or SUBSYSTEM; recorded by SYSTEM.
- **Records:** decision `action:deschedule`, `object`:pid, `target`:cause
  (wait-on-input, voluntary yield), `rule_cited`:`SCHED-LAW-ORDER`. The *cause* is
  the input event id, so the scheduler-state view can later answer "why not
  running?".
- **Refusals:** descheduling a process the requester does not own and has no
  scheduling authority over → cite `SOP` (deciding ≠ executing over others' work).

### set-priority
- **Plain words:** change a process's priority class or its link-typed ordering
  relative to others.
- **Invoked by:** OWNER/ADMIN or an authorised SUBSYSTEM; recorded by SYSTEM.
- **Records:** decision `action:set-priority`, `object`:pid, `target`:new class /
  new ordering link, `rule_cited`:`SCHED-LAW-PRIORITY`. Because priority is a
  *decision*, not a mutable field, the view can replay every priority a process
  ever held (the audit Linux cannot give).
- **Refusals:**
  - class above requester's authority ladder rung → cite `SCHED-LAW-PRIORITY`.
  - an ordering link that would create a scheduling cycle → cite `ROOT-NEG-6`
    (contradiction in the active ordering set).

### halt
- **Plain words:** force a governed pause — the standby/brake act; filters the
  runnable set down to voice-kinds only (target-state §4.1; twc halt chain).
- **Invoked by:** OWNER/ADMIN or the AUDITOR-with-brake (twc R25 "the watched can
  brake the watchers"); recorded by SYSTEM.
- **Records:** decision `action:halt`, `object`:scope (a process, a seat, the
  system), `target`:voice-kinds admitted, `rule_cited`:`SCHED-LAW-HALT`.
- **Refusals:** halting a scope the requester cannot see → cite `SIGHT-IS-LAW`;
  halt that would strand a boot-critical duty → cite `BOOT-INT`.

### kill
- **Plain words:** end a process — the terminal rung of the penalty chain
  (halt → mute → restart → kill), each rung a recorded governance act.
- **Invoked by:** OWNER/ADMIN or authorised SUBSYSTEM; recorded by SYSTEM.
- **Records:** decision `action:kill`, `object`:pid, `target`:reason,
  `rule_cited`:`SCHED-LAW-KILL-CHAIN`. Kill records the *rung history* it followed,
  so "why was this killed?" replays the whole referral.
- **Refusals:**
  - kill requested without the prior chain rungs where the chain requires them →
    cite `SCHED-LAW-KILL-CHAIN` (no skipping to terminal force).
  - requester lacks kill authority over the target → cite `ROOT-NEG-3`.

### standby
- **Plain words:** enter the idle governed state — the driver executes nothing; the
  Ask is the wake signal; evented, never clocked (target-state §4.1 STBY-1).
- **Invoked by:** SUBSYSTEM (SCHED) as the exhausted-runnable-set decision;
  recorded by SYSTEM.
- **Records:** decision `action:standby`, `object`:scheduler, `target`:wake
  condition, `rule_cited`:`SCHED-LAW-STANDBY`. INPUT (a wake-causing event) later
  ends standby and is itself recorded.
- **Refusals:** standby proposed while a runnable voice-kind exists → cite
  `SCHED-LAW-STANDBY` (standby is only lawful with nothing runnable).

---

## Section 2 — Memory (governing space)

Department LAW = allocation policy + budgets-flow-down (every actor budgeted; each
allocation checked by predicate) + protection + eviction/OOM rules (target-state
§4.2). Page tables and free-lists are CACHE (rebuilt from these decisions); raw
accesses are STREAM; hardware access/dirty bits stay ephemeral and surface only as
*cited evidence* in eviction decisions [AUDIT-FIX 3].

### grant-mapping
- **Plain words:** create a memory mapping for an actor — the governed form of
  `mmap`/`brk`.
- **Invoked by:** PROCESS (via port); recorded by SYSTEM.
- **Records:** decision `action:grant-mapping`, `object`:actor+region, `target`:
  mapping id + protection, `rule_cited`:`MEM-LAW-ALLOC`. This decision is what the
  `/proc/[pid]/maps` view folds — "who was granted what, when, under which budget."
- **Refusals:**
  - allocation predicate fails (size, alignment, region policy) → cite `MEM-LAW-ALLOC`.
  - grant would exceed the actor's flowed-down budget → cite `MEM-LAW-BUDGET`.
  - actor cannot read the backing object it asks to map → cite `SIGHT-IS-LAW`.

### protect-region
- **Plain words:** change a region's protection bits (rwx) — governed `mprotect`.
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:protect-region`, `object`:mapping id, `target`:new
  protection, `rule_cited`:`MEM-LAW-PROTECT`.
- **Refusals:** requester does not own the mapping → cite `SOP`; a protection
  change barred by policy (e.g. W^X) → cite `MEM-LAW-PROTECT`.

### evict-page
- **Plain words:** reclaim a page (page-out / drop-clean) under memory pressure.
- **Invoked by:** SUBSYSTEM (MEM); recorded by SYSTEM.
- **Records:** decision `action:evict-page`, `object`:page/frame, `target`:backing
  store, `rule_cited`:`MEM-LAW-EVICT`, **`evidence_summary`**: the access-statistics
  aggregate the choice acted on ("evicted X, citing aggregate A") — the decision is
  audit-complete even though the raw stream behind A was sampled [AUDIT-FIX 3].
- **Refusals:** eviction of a pinned/locked region → cite `MEM-LAW-PROTECT`; no
  eviction candidate satisfies the policy predicate → cite `MEM-LAW-EVICT` (and
  refer toward `oom-decision`).

### amend-budget
- **Plain words:** change an actor's memory budget — a LAW change, not a runtime
  tweak (budgets are records with amendment authority).
- **Invoked by:** OWNER/ADMIN; recorded by SYSTEM.
- **Records:** CREATE-RULE-class decision `action:amend-budget`, `object`:actor,
  `target`:new budget, `rule_cited`:`MEM-LAW-BUDGET`, with amendment provenance.
- **Refusals:** amender lacks budget authority → cite `ROOT-NEG-3`; new budget set
  contradicts an active budget invariant → cite `ROOT-NEG-6`; amendment that would
  starve a boot-critical actor → cite `BOOT-INT`.

### oom-decision
- **Plain words:** the out-of-memory decision — which actor loses memory when the
  space cannot satisfy every budget. In gov-os this is a *governed, recorded
  decision citing its rule and evidence*, never a silent reaper (target-state §4.2).
- **Invoked by:** SUBSYSTEM (MEM); recorded by SYSTEM.
- **Records:** decision `action:oom-decision`, `object`:victim actor, `target`:
  reclaimed amount, `rule_cited`:`MEM-LAW-OOM`, **`evidence_summary`**: the pressure
  aggregate and the ranking that selected the victim. "Why was this killed for
  memory?" has a mechanical answer forever.
- **Refusals:** an OOM decision proposed while a lawful eviction path remains →
  cite `MEM-LAW-EVICT` (evict before killing); a victim selection that violates the
  OOM ordering law → cite `MEM-LAW-OOM`.

---

## Section 3 — Files (governing custody of information)

Department LAW = namespace, mount, and permission rules as records (target-state
§4.3). DECISIONS below are recorded; **file *content* is never sampled** — every
write's payload goes full-fidelity to content-addressed blobs and the write event
records the hash (`FS-LAW-CONTENT`, [AUDIT-FIX 4]). Event *granularity* may be
coalesced only under a recorded policy citing `FS-LAW-COALESCE` (a calibration with
a named owner, never a silent loss). The directory tree and inode state are CACHE.

### create
- **Plain words:** bring a new file or directory into the namespace.
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:create`, `object`:path, `target`:inode identity +
  initial permission, `rule_cited`:`FS-LAW-NAMESPACE`.
- **Refusals:** path outside the requester's writable namespace → cite
  `FS-LAW-NAMESPACE`; name collides under a no-overwrite policy → cite `ROOT-NEG-6`.

### write
- **Plain words:** record new content for a file. The write *event* is the
  decision; the *bytes* are decision-class content, hashed into the blob store.
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:write`, `object`:path/inode, `target`:content hash,
  `rule_cited`:`FS-LAW-PERM` (+ `FS-LAW-COALESCE` if the event folds many small
  writes). Every file thus carries a complete, replayable history natively —
  time-travel without snapshots.
- **Refusals:** no write permission on the object → cite `FS-LAW-PERM`; requester
  cannot read a region it references → cite `SIGHT-IS-LAW`.

### link
- **Plain words:** add a name pointing at existing content (hard/sym link).
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:link`, `object`:new name, `target`:existing inode,
  `rule_cited`:`FS-LAW-NAMESPACE`.
- **Refusals:** target outside a readable namespace → cite `SIGHT-IS-LAW`; link
  that would violate a mount's link policy → cite `FS-LAW-MOUNT`.

### unlink
- **Plain words:** remove a name from the namespace. Governed deletion = a recorded
  REMOVE-FROM-VIEW activity; the master record and content blobs survive
  (master-database deletion principle — "remove from active view," not erase).
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:unlink`, `object`:name, `target`:active-namespace
  view, `rule_cited`:`FS-LAW-NAMESPACE`. History remains fully replayable.
- **Refusals:** no unlink permission → cite `FS-LAW-PERM`; an attempt to *erase the
  master record* (not merely unlink) → cite `BOOT-INT` (only owner master-
  destruction with a surviving scar, GS-13, may do that — outside this operation).

### change-permission
- **Plain words:** change a file's permission record — governed `chmod`/`chown`.
- **Invoked by:** OWNER of the object or ADMIN; recorded by SYSTEM.
- **Records:** decision `action:change-permission`, `object`:path, `target`:new
  permission set, `rule_cited`:`FS-LAW-PERM`. Permission is a decision, so
  "who could read this at time T" is an `asOf` view (see FILE 13).
- **Refusals:** requester lacks permission-change authority → cite `SOP`; a change
  creating a permission contradiction in scope → cite `ROOT-NEG-6`.

### mount
- **Plain words:** attach a filesystem/namespace at a point under recorded mount law
  — governed `mount`.
- **Invoked by:** ADMIN; recorded by SYSTEM.
- **Records:** LAW-class decision `action:mount`, `object`:source, `target`:mount
  point, `rule_cited`:`FS-LAW-MOUNT`, with amendment authority. Folds into the
  `/proc/mounts` view.
- **Refusals:** mount point outside admin namespace → cite `FS-LAW-NAMESPACE`;
  mount rule contradicting an active mount → cite `ROOT-NEG-6`; mount that would
  shadow a boot-critical namespace → cite `BOOT-INT`.

### unmount
- **Plain words:** detach a mounted namespace (remove the mount record from the
  active mount view).
- **Invoked by:** ADMIN; recorded by SYSTEM.
- **Records:** decision `action:unmount`, `object`:mount point, `target`:active
  mount view, `rule_cited`:`FS-LAW-MOUNT`.
- **Refusals:** in-use namespace with live bindings barred by policy → cite
  `FS-LAW-MOUNT`; unmount of a boot-critical namespace → cite `BOOT-INT`.

---

## Section 4 — Devices (governing capability)

Department LAW = device registration as *amendments* — capability is law (the twc
R14 pattern: registering a driver is a recorded, authorised amendment, not a config
edit; target-state §4.4). Driver calls cross a validated, typed boundary (the
envelope rule generalised — the one place isolation appears, as a derived property).
The live binding table is CACHE; I/O throughput is STREAM.

### register-driver  *(an amendment)*
- **Plain words:** admit a driver into the kernel's capability law — the governed
  form of "load a module / register a driver," recorded as an amendment with named
  authority, not a mutation of a global table.
- **Invoked by:** ADMIN (capability grant authority); recorded by SYSTEM.
- **Records:** CREATE-RULE-class decision `action:register-driver`, `object`:driver
  identity + capability class, `target`:active capability law, `rule_cited`:
  `CAP-IS-LAW`, with amendment provenance. This is why "which driver claimed what,
  when, under whose rule" is answerable — the exact gap in the conventional kernel.
- **Refusals:**
  - registrant lacks capability-granting authority → cite `ROOT-NEG-3`.
  - a capability that contradicts an active capability rule → cite `ROOT-NEG-6`.
  - registration that would violate the typed driver boundary contract → cite
    `DEV-LAW-ENVELOPE`.

### bind-device
- **Plain words:** attach a registered driver to a device instance so it can serve
  actors.
- **Invoked by:** SUBSYSTEM (DEV) or ADMIN; recorded by SYSTEM.
- **Records:** decision `action:bind-device`, `object`:device, `target`:driver,
  `rule_cited`:`DEV-LAW-BIND`. Folds into the device-bindings / `/sys` view.
- **Refusals:** driver not registered in the active capability law → cite
  `CAP-IS-LAW` (you cannot bind an unregistered capability); device already bound
  under an exclusive-binding rule → cite `DEV-LAW-BIND`.

### unbind
- **Plain words:** detach a driver from a device (remove the binding from the
  active binding view).
- **Invoked by:** SUBSYSTEM (DEV) or ADMIN; recorded by SYSTEM.
- **Records:** decision `action:unbind`, `object`:device, `target`:active binding
  view, `rule_cited`:`DEV-LAW-BIND`.
- **Refusals:** unbind of a boot-critical device (console, boot disk) → cite
  `BOOT-INT`; requester lacks authority over the binding → cite `SOP`.

### grant-capability
- **Plain words:** grant an actor the right to use a device capability — a recorded
  capability decision (who may use which device power, under what rule).
- **Invoked by:** ADMIN; recorded by SYSTEM.
- **Records:** decision `action:grant-capability`, `object`:actor, `target`:
  capability, `rule_cited`:`CAP-IS-LAW`. Feeds the "who-was-granted-what" audit view.
- **Refusals:** granter lacks the capability it purports to grant → cite
  `CAP-IS-LAW` (no granting up beyond your own authority); grant contradicting an
  active capability rule → cite `ROOT-NEG-6`.

---

## Section 5 — Communication (governing messages)

Department LAW = message-contract and queue rules (target-state §4.5). Channel
open/close and send/receive *events* are recorded (payload full or hash-referenced
per the recorded coalescing policy, as with files); high-volume payload traffic is
STREAM. Kernel-internal state is shared-nothing — the record is the only shared
medium inside the kernel. **Userland shared memory is honoured at the port**: the
kernel governs the *granting* of a shared region (a recorded decision), not the
interior writes, which are the applications' own activity [AUDIT-FIX 5].

### open-channel
- **Plain words:** establish a communication path (pipe/socket) under a recorded
  message contract — the governed form of `pipe`/`socket`/`connect`.
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:open-channel`, `object`:endpoints, `target`:channel
  id + contract, `rule_cited`:`COMM-LAW-CONTRACT`. Mirrors the foundational tunnel
  model: a valid tunnel links sender, target, permitted message class, and proof.
- **Refusals:** an endpoint the requester cannot see → cite `SIGHT-IS-LAW`; a
  channel violating the permitted message-class contract → cite `COMM-LAW-CONTRACT`.

### send
- **Plain words:** enqueue a message on a channel. The send *event* is the decision;
  the payload is recorded in full or by hash per the coalescing policy.
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:send`, `object`:channel, `target`:message id/hash,
  `rule_cited`:`COMM-LAW-QUEUE`. Yields a complete grant-and-message ledger at the
  kernel boundary.
- **Refusals:** channel not open / closed → cite `COMM-LAW-QUEUE`; message class
  not permitted by the channel contract → cite `COMM-LAW-CONTRACT`; queue over its
  budget → cite `COMM-LAW-QUEUE`.

### receive
- **Plain words:** dequeue a message from a channel for an actor.
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:receive`, `object`:channel, `target`:message id,
  `rule_cited`:`COMM-LAW-QUEUE`. The receive event is what lets the audit view show
  who actually consumed what (Linux cannot).
- **Refusals:** receiver not an authorised endpoint of the channel → cite
  `ROOT-NEG-3`; receiver could not read the channel → cite `SIGHT-IS-LAW`.

### grant-shared-region
- **Plain words:** grant two or more actors shared access to a memory region —
  governed `shm`/`MAP_SHARED`. The kernel records *the grant* (who shares which
  region with whom, under what rule); it does not audit the interior writes.
- **Invoked by:** PROCESS (owner of the region); recorded by SYSTEM.
- **Records:** decision `action:grant-shared-region`, `object`:region, `target`:
  the sharing actors, `rule_cited`:`COMM-LAW-SHARE-GRANT`. The honest boundary
  (target-state §4.5): a complete ledger of *who was ever granted shared access to
  what* — races *inside* the region remain userland's business.
- **Refusals:** grantor does not own the region → cite `SOP`; a grantee the grantor
  cannot see → cite `SIGHT-IS-LAW`; sharing barred by the region's protection law →
  cite `MEM-LAW-PROTECT`.

### close
- **Plain words:** tear down a channel (remove it from the active channel view).
- **Invoked by:** PROCESS; recorded by SYSTEM.
- **Records:** decision `action:close`, `object`:channel, `target`:active channel
  view, `rule_cited`:`COMM-LAW-CONTRACT`.
- **Refusals:** close by a non-endpoint → cite `ROOT-NEG-3`; close of a
  boot-critical channel (e.g. the ADMIN tunnel) → cite `BOOT-INT`.

---

## Cross-cutting invariants (true of every entry above)

1. **Two outcomes only.** Every operation produces a recorded decision citing its
   law, or a recorded refusal citing the rule that refused. No third path, no
   unrecorded write (`P4-REFUSE`; audit guarantees §1.1–1.2).
2. **Every refusal is an event.** Denials are appended through BLOCK/WRITE-ACTIVITY
   with `rule_cited` set — "why was this refused?" always has a mechanical answer,
   forever. Attribution and Explanation cover refusals identically to grants.
3. **Unregistered = does not exist.** Any operation name not in this catalogue is a
   Closure Hit: recorded, escalated, never coerced into a neighbour (`P3-CLOSURE`).
   Adding a genuinely new operation is itself a CREATE-RULE amendment with named
   authority — the catalogue grows only through the gate.
4. **Decisions embed the evidence they acted on.** Where a decision used sampled
   stream evidence (eviction, OOM), the aggregate is embedded in the record; the
   audit is complete at the decision even though the raw stream was sampled
   [AUDIT-FIX 3].
5. **Views, not stored state.** No operation stores a "current" status, count, or
   pointer. Every "current" answer is computed by folding these decisions — see
   `13-VIEWS-AND-PROC-CATALOGUE.md`.

---

## What this catalogue excludes (named, not hidden)

- **Exact syscall→operation map.** The Linux syscall port sits above these
  operations; the syscall-by-syscall conformance map is named-open in target-state
  §8 and is not drawn here (this is the *governed* layer, not the port). Trained
  knowledge: syscall names/shapes.
- **Parameter schemas.** Each operation validates parameters before its handler
  (target-state §L1); the concrete schemas are a build artifact, not this design
  reference.
- **The formal LAW-id registry.** Subsystem `*-LAW-*` ids here are PROPOSED handles
  (cost if wrong: re-key, shape holds); the authoritative rule set is the record
  itself, amendable with named authority.
- **Sampling/coalescing calibrations.** The recorded rates behind `FS-LAW-COALESCE`
  and the STREAM classes are owner-ruled from evidence (target-state §8 deferred),
  not invented here.
- **Federation operations.** Cross-instance envelope exchange (import/compare) is a
  deduced layer (target-state §8 / tech-arch §8), out of scope for the single-kernel
  gate catalogued here.
