<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Record Shapes (kernel-grade envelope catalogue)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** The ENVELOPE stands (I1: unchanged
> forever). The PAYLOAD-KIND catalogue is superseded by growth: op_definition,
> view_definition (bind/tier/refresh), category_pack, obligation, tick/input,
> dual-audit-b-record; root-rule payloads carry FULL FORM (when/then/enforced_by/
> enforcement) + tier; `obligation_ref` rides fired decisions. Live catalogue:
> design/28 §3 + the genesis seed. Campaign 2 adds account/verification/space/role/
> grant/succession (design/31 §2). Live canon controls.

**Status:** v0.1, 2026-07-12, high. **Route-A assumption** — this catalogue is
written for the hollow-out route (03 §7 Route A): each shape is what a governed
subsystem appends while shadowing, then replacing, its Linux counterpart behind
an unchanged interface. No code here — data-shape specifications in prose plus
illustrative JSON sketches. Read `03-TARGET-STATE-ARCHITECTURE.md` (the five
recording classes; the reconstruction invariant) and
`02-TECHNICAL-ARCHITECTURE.md` §1.1 (the stepping-stone envelope) first; this
document is the **kernel-grade** version of that envelope.

Labels per `00-READ-FIRST.md` §6: SOURCE-DERIVED (cite) / INFERRED (from what) /
PROPOSED (cost if wrong) / trained knowledge (flagged). Every JSON block is a
**shape sketch, not a schema commitment** — field names, tiers, and encodings
are illustrative and will move under the S1 store-contract work (02 §9). What
this catalogue fixes is the *shape and class* of each record, not its wire
format.

---

## 0. What this document pins, and what it does not

**Purpose.** Pin the exact shape of every kind of record the kernel appends,
at kernel grade. For each shape: its fields (name, type, meaning), which
recording **CLASS** it belongs to (LAW / DECISION / INPUT — the three recorded
classes; CACHE and STREAM are *not* appended and are covered in §6), a worked
concrete example, and its **reconstruction role** — which derived cache the
record feeds when views are recomputed.

**The invariant this serves** (SOURCE-DERIVED, 03 §2): `governed-state =
f(LAW, DECISIONS, INPUTS)`. STREAM informs humans and calibration, never the
function. Every shape below is justified by its place in that function: a LAW
record is a term of `f`; a DECISION record is an application of `f` recorded in
full; an INPUT record is an argument to `f` the kernel did not author. If a
proposed record is none of those three, it does not belong in the log (§6).

**Not in scope here** (named, not hidden): the syscall-by-syscall mapping from
each record to the `/proc` view it renders (03 §5.2, deferred); the blob-store
format for content-addressed payloads (S1); the sampling/coalescing calibration
values (owner-ruled from evidence, 03 §8 — never invented here); the formal
ordering proof for the built-ID tiebreak (03 §8, max-tier). This document
specifies shapes; those specify machinery and calibration.

**Class legend used throughout.**

| Class | Recorded? | Role in `f` | This doc |
|---|---|---|---|
| **LAW** | always, in full, with amendment authority | a *term* of `f` | §2 |
| **DECISION** | always, in full, rule-cited | an *application* of `f` | §3 |
| **INPUT** | arrivals recorded; raw content sampled | an *argument* to `f` | §4 |
| CACHE | never appended (derived, discardable) | the *output* of `f` | §6 |
| STREAM | never load-bearing (sampled/aggregated) | *not* in `f` | §6 |

---

## 1. The base envelope (common fields all records carry)

Every appended record — LAW, DECISION, or INPUT — is one envelope. This is the
kernel-grade tightening of the stepping-stone envelope in 02 §1.1: the same
union-of-proven-envelopes shape (twc `store.js`, cgl `core/store.js`, venn2
`memstore.mjs`, 3d-auto `store.py`), reduced to the fields that must survive at
kernel speed and made explicit about the ordering fields the intake pipeline
depends on (02 §1.1, 03 §1.4). SOURCE-DERIVED from 02 §1.1; the ordering-field
emphasis is INFERRED from the owner's multi-writer ruling (02 top banner, seam
S5).

### 1.1 Fields

| Field | Type | Meaning |
|---|---|---|
| `record_id` | opaque id (string) | Stable identity of this record. Content-addressable or minted; never reused. |
| `seq` | integer, monotonic | **Total order, minted at append** by the one sequencer. The authoritative order of the whole record. Assigned by the pipeline, never by the writer. |
| `record_time` | timestamp | **Sole total-order anchor** (02 §1.4). When the sequencer recorded it. Feeds the time-hash that orders the pipeline. |
| `submission_time` | timestamp, **monotonic per origin** | When the writing origin submitted. Monotonic *within one origin*, **never globally ordered** (02 §1.1). Used for per-origin causality and federation ingestion, not for global order. |
| `origin` / `subsystem_id` | id + **built-ID** | Which subsystem/CPU/origin wrote this. Carries the origin's **built ID** (creation order) — the tiebreak key. See §1.2. |
| `actor` | id | The AAOT actor: which process / subsystem / driver / owner acted. |
| `action` | registered verb | The AAOT action: a **registered** op (02 §1.2). Unregistered action = does not exist = refusal. |
| `object` | id | The AAOT object: what the action was about (the primary governed entity). |
| `target` | id / null | The AAOT target: the second party or destination, where the action has one (grantee, link target, receiver). |
| `rule_cited` | rule ref (id@version) | The LAW record this action applied or refused under. **Every DECISION cites its rule** (03 §1.2). LAW records cite their *amendment-authority* rule here; INPUT records cite the registration/policy that admits that input class. |
| `provenance` | object | The sight-gate input (02 §1.1, 03 L3): what the writer could read when it acted. Default-deny; you cannot consume what you could not read. |

**Supporting fields carried but not load-bearing for ordering** (from 02 §1.1,
retained for completeness): `occurrence_time` (when it happened in the world,
may be vague), `recorder_id` / `asserted_by`, `confidence_tier`, `refs[]`,
`content_form`, `payload` (payloads above a size floor go to the
content-addressed blob store; the record holds the hash — 02 §1.1, 03 §4.3).

### 1.2 The built-ID tiebreak field, explained explicitly

This is the field that makes replay deterministic under multi-core physics, so
it is spelled out. SOURCE-DERIVED from the owner ruling (02 top banner; 03 §1.4;
seam S5).

**The problem.** At kernel scale many origins (subsystems, and one buffer per
CPU) submit into one ordered intake pipeline at wire rate (03 §2). Ordering is
**time-hash based**. Hardware races at nanosecond scale: two records can hash to
the *same* order position. A tie left unbroken would make replay
non-deterministic — the exact failure the audit contract forbids (03 §1.3–1.4).

**The field.** Each origin carries a **built ID** — its *creation order* in the
system (subsystem 0 built before subsystem 1, and so on). It lives in the
envelope's `origin` / `subsystem_id`. It is assigned once, at the origin's
construction, and never changes.

**The rule.** When **exactly two** entries collide at the same time-hash
position, the sequencer orders them by the two writing origins' built IDs:
lower built ID lands first. Deterministic, recorded, no negotiation (02 banner
ruling 2). Because built IDs are unique and fixed, the tiebreak is a total order
on origins, so *any* two-way collision resolves the same way on every replay.

> **The ordering is definitional, not descriptive** (03 §1.4, `[AUDIT-FIX 2]`).
> The record does not *describe* which core physically won the race; it
> *settles* it — whoever the sequencer lands first IS first, by law. This is
> why replay determinism survives multi-core physics.

**Open, flagged** (03 §8): the proof that time-hash + built-ID tiebreak yields
deterministic replay under *every* interleaving (not just pairwise) is a
max-tier job, deferred. A collision of *three or more* origins at one position
is out of this doc's scope — the ruling names the two-entry case; the general
case is part of the deferred proof. Do not invent a general rule here.

### 1.3 Envelope shape sketch

```jsonc
// shape sketch, not a schema commitment
{
  "record_id": "rec_9f3a…",
  "seq": 480217,                       // total order, minted at append
  "record_time": "2026-07-12T04:11:07.339182Z",   // sole total-order anchor
  "submission_time": "2026-07-12T04:11:07.338900Z",// monotonic per origin only
  "origin": { "subsystem_id": "sched", "built_id": 0 }, // built_id = tiebreak key
  "actor": "proc:1841",
  "action": "SCHEDULE-ADMIT",          // a registered verb
  "object": "proc:1841",
  "target": null,
  "rule_cited": "law:sched-policy@7",
  "provenance": { "could_read": ["runnable-set", "law:sched-policy@7"] },
  "content_form": "inline",
  "payload": { /* class-specific, see below */ }
}
```

---

## 2. LAW records — the rules of rules

**Class: LAW** (SOURCE-DERIVED, 03 §2). LAW is the rules of rules — recorded
*totally*, changes rarely, and each is an **amendable rule record with a named
amendment authority**. A LAW record's `action` is an amendment verb
(`CREATE-INFO/-RULE`, `AMEND-RULE`, `REGISTER-CAPABILITY` — 02 §1.2 bootstrap
op set); its `object` is the rule being created or amended; its `rule_cited` is
the *amendment-authority* rule that permits this change (capability is law —
registering or amending a rule is itself a recorded, authorised amendment, not a
config edit; 03 §4.4, twc R14).

**Common LAW payload fields** (INFERRED from the estate's ⚙ pattern, 03 §1):

| Field | Type | Meaning |
|---|---|---|
| `rule_id` | id | The rule's stable identity (amendments share it, version differs). |
| `version` | integer | Amendment version. Latest-effective-wins under the rule lifecycle. |
| `amendment_authority` | actor ref | **Who may amend this rule.** Named, recorded. The authority ladder (twc committee-tier). |
| `predicate` | expression | The rule body: the condition/mechanism the subsystem applies. Data, not code. |
| `effective_from` | record-time / event | When the amendment takes force (OMGS lifecycle: announcement → effectiveness). |
| `supersedes` | rule ref / null | The prior version this amends, if any. |

**Reconstruction role (all LAW):** LAW records are the *terms* of `f`. They feed
no cache directly; they are the policy the caches are recomputed *under*. Replay
reads LAW to know which rule was in force at each `asOf` point (03 §1.3).

### 2.1 Scheduling-policy rule

- **Class:** LAW. **Feeds:** the run-queue cache (§3.1) is derived *under* it.
- **Fields (payload):** `priority_classes[]`, `ordering_links` (link-typed:
  FS/SS/FF/SF at workflow level, 02 §2), `standby_rules`, `quantum` — the twc
  obligations pattern lowered to dispatch (03 §4.1).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "AMEND-RULE",
  "object": "law:sched-policy",
  "rule_cited": "law:amend-authority:kernel-governor@1",
  "payload": {
    "rule_id": "law:sched-policy", "version": 7,
    "amendment_authority": "seat:kernel-governor",
    "predicate": {
      "priority_classes": ["realtime", "interactive", "batch"],
      "quantum_ms": 4, "standby": "evented-only"
    },
    "effective_from": "seq:480000", "supersedes": "law:sched-policy@6"
  }
}
```

**Worked example:** the governor raises the interactive quantum from 3 ms to
4 ms. This appends `law:sched-policy@7`. From `seq:480000` onward, every
dispatch decision (§3.1) cites `@7`; a replay `asOf` a point before `480000`
still sees `@6`. "Why did this task get 4 ms after 04:11?" cites `@7` and its
authority forever.

### 2.2 Memory-budget rule

- **Class:** LAW. **Feeds:** page tables and free-lists (§3.2) are derived and
  *checked* under it. **SOURCE-DERIVED**, 03 §4.2 (budgets-flow-down: every
  actor budgeted, allocation checked by predicate).
- **Fields (payload):** `budget_holder` (actor/cgroup), `ceiling`, `flow_down`
  (parent→child budget derivation), `oom_policy` (which rule an eviction cites).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "AMEND-RULE", "object": "law:mem-budget:cgroup:web",
  "rule_cited": "law:amend-authority:kernel-governor@1",
  "payload": {
    "rule_id": "law:mem-budget:cgroup:web", "version": 3,
    "amendment_authority": "seat:kernel-governor",
    "predicate": { "budget_holder": "cgroup:web", "ceiling_mb": 2048,
                   "flow_down": "children-share-parent", "oom_policy": "law:evict-coldest@2" },
    "effective_from": "seq:479500"
  }
}
```

**Worked example:** the `web` cgroup ceiling is set to 2048 MB citing
`evict-coldest@2` as its OOM policy. Every later grant (§3.2) is checked against
this ceiling; every eviction cites `evict-coldest@2`. OOM is now a *governed,
recorded decision citing its rule and its evidence* — not a silent reaper
(03 §4.2).

### 2.3 Permission rule

- **Class:** LAW. **Feeds:** the visibility/permission view (03 L3 sight-is-law)
  and gates file DECISIONS (§3.3). **SOURCE-DERIVED**, 03 §4.3 (permission rules
  as records), 03 §3 (default-deny, grants are events).
- **Fields (payload):** `subject`, `object_scope`, `rights[]` (read/write/link/
  exec), `default` (deny), `grant_authority`.

```jsonc
// shape sketch, not a schema commitment
{
  "action": "AMEND-RULE", "object": "law:perm:/var/log",
  "rule_cited": "law:amend-authority:security-governor@1",
  "payload": {
    "rule_id": "law:perm:/var/log", "version": 5,
    "amendment_authority": "seat:security-governor",
    "predicate": { "subject": "role:logger", "object_scope": "/var/log/**",
                   "rights": ["read","write"], "default": "deny" },
    "effective_from": "seq:301002"
  }
}
```

**Worked example:** `role:logger` is granted read+write under `/var/log`,
default-deny elsewhere. A later write DECISION (§3.3) cites `law:perm:/var/log@5`
as the rule that admitted it; a refusal to write outside the scope is *itself
recorded*, citing the same rule (03 §1.2). "Who may write here, and who said so?"
has a mechanical answer.

### 2.4 Device-capability registration

- **Class:** LAW. **Feeds:** the live binding table (§3.4) is derived under it.
  **SOURCE-DERIVED**, 03 §4.4 (capability is law — the twc R14 pattern:
  registering a driver is a recorded, authorised amendment, not a config edit).
- **Fields (payload):** `driver_id`, `device_class`, `capabilities[]` (the typed
  boundary it may cross), `registration_authority`.

```jsonc
// shape sketch, not a schema commitment
{
  "action": "REGISTER-CAPABILITY", "object": "driver:nvme0",
  "rule_cited": "law:amend-authority:device-governor@1",
  "payload": {
    "rule_id": "cap:driver:nvme0", "version": 1,
    "amendment_authority": "seat:device-governor",
    "predicate": { "driver_id": "nvme0", "device_class": "block",
                   "capabilities": ["dma","irq:42"] },
    "effective_from": "seq:12"
  }
}
```

**Worked example:** the `nvme0` driver is registered with DMA and IRQ-42
capability. Only after this LAW record may a bind DECISION (§3.4) grant `nvme0`
to a device. "Which driver claimed this hardware, when, under whose authority?"
is answerable — the exact gap 03 §4.4 diagnoses in the conventional kernel
(capability without law).

### 2.5 Mount rule

- **Class:** LAW. **Feeds:** the namespace/directory-tree cache (§3.3).
  **SOURCE-DERIVED**, 03 §4.3 (namespace, mount, and permission rules as
  records).
- **Fields (payload):** `mount_point`, `source`, `fs_type`, `flags[]`
  (ro/nosuid/…), `namespace`, `mount_authority`.

```jsonc
// shape sketch, not a schema commitment
{
  "action": "AMEND-RULE", "object": "law:mount:/mnt/data",
  "rule_cited": "law:amend-authority:fs-governor@1",
  "payload": {
    "rule_id": "law:mount:/mnt/data", "version": 1,
    "amendment_authority": "seat:fs-governor",
    "predicate": { "mount_point": "/mnt/data", "source": "dev:nvme0p2",
                   "fs_type": "gov-vfs", "flags": ["rw","nosuid"], "namespace": "root" },
    "effective_from": "seq:210"
  }
}
```

**Worked example:** `/mnt/data` is mounted rw,nosuid from `nvme0p2`. The
directory-tree cache (§3.3) is derived to include this subtree only from
`seq:210`; a path-resolution replay `asOf` before `210` does not see it. "When
did this mount appear and under what flags?" is a record fact, not a lost
runtime state.

---

## 3. DECISION records — governed acts, one family per subsystem

**Class: DECISION** (SOURCE-DERIVED, 03 §2). A DECISION is any event that
changes law-derived state. **Always recorded in full, citing its rule. Never
sampled.** Each is an application of `f`. The `rule_cited` field is mandatory and
non-null. Below, one family per governed subsystem (03 §4). Each family names the
cache it feeds (its reconstruction role).

### 3.1 Scheduling — admit / deschedule

- **Subsystem:** Scheduling (03 §4.1). **Feeds:** the **run-queue / runnable-set
  cache**.
- **Verbs:** `SCHEDULE-ADMIT`, `DESCHEDULE` (with the forced-descheduling chain:
  halt → mute → restart → kill, 02 §2 — each rung a recorded governance act).
- **Fields (payload):** `proc`, `priority_class`, `reason` (admit cause / which
  rung of the chain), `wake_cause_ref` (the INPUT that made it runnable, §4).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "SCHEDULE-ADMIT", "actor": "proc:1841", "object": "proc:1841",
  "rule_cited": "law:sched-policy@7",
  "payload": { "priority_class": "interactive",
               "reason": "wake", "wake_cause_ref": "rec_io_88f0" }
}
```

**Worked example:** process 1841 becomes runnable because an I/O completion
(INPUT, §4.2, `rec_io_88f0`) arrived; the scheduler admits it under
`sched-policy@7`. The dispatch that *follows* is a pure function of policy +
this decision + inputs, so it is **not** separately recorded (it is STREAM, §6)
— the schedule replays exactly (03 §4.1). "Why did 1841 run at 04:11?" → admitted
under `@7`, woken by `rec_io_88f0`.

### 3.2 Memory — grant / evict (evict embeds evidence-summary)

- **Subsystem:** Memory (03 §4.2). **Feeds:** **page tables and free-lists**.
- **Verbs:** `MEM-GRANT` (mapping created / region granted), `MEM-EVICT` (page
  evicted / OOM).
- **The eviction evidence-summary field** (SOURCE-DERIVED, 03 §2 `[AUDIT-FIX 3]`,
  03 §4.2): where a decision depends on **stream evidence** — e.g. a page evicted
  *because access statistics say it is cold* — the DECISION record **embeds the
  evidence summary it acted on**. The audit is complete *at the decision*, even
  though the raw stream behind the aggregate was sampled. Hardware access/dirty
  bits stay ephemeral; they surface into the record only as this cited evidence.

| Eviction payload field | Type | Meaning |
|---|---|---|
| `page` / `region` | id | What was evicted. |
| `budget_ref` | rule ref | The memory-budget LAW (§2.2) that forced it. |
| `evidence_summary` | object | **The aggregate acted on**: e.g. `{aggregate: "access-freq", window: "…", value: "cold", coverage: "sampled@…"}`. The evidence, not the raw stream. |

```jsonc
// shape sketch, not a schema commitment
{
  "action": "MEM-EVICT", "actor": "subsystem:mem", "object": "page:0x7f…c000",
  "rule_cited": "law:evict-coldest@2",
  "payload": {
    "region": "cgroup:web/heap", "budget_ref": "law:mem-budget:cgroup:web@3",
    "evidence_summary": { "aggregate": "access-freq", "window_ms": 200,
                          "value": "cold", "coverage": "sampled@1/64" }
  }
}
```

**Worked example (the whole OOM story, made auditable):** the `web` cgroup hits
its 2048 MB ceiling (`mem-budget@3`). The allocator evicts the coldest page,
citing `evict-coldest@2`, and *embeds* the aggregate it trusted: access-freq
over a 200 ms window read "cold", sampled at 1/64 coverage. Replay reconstructs
page tables from grants and evicts alone (the samples are gone, but the
*decision's evidence is in the record*). "Why was this page reclaimed?" →
evict-coldest@2, cold per this aggregate — forever, even though no raw access
was ever recorded (03 §4.2). A grant reconstructs the mapping; an evict removes
it.

### 3.3 Files — create / write / link / unlink (write carries content-hash)

- **Subsystem:** Files (03 §4.3). **Feeds:** the **directory tree, inode state,
  dentry cache**.
- **Verbs:** `FILE-CREATE`, `FILE-WRITE`, `FILE-LINK`, `FILE-UNLINK`,
  `FILE-PERM-CHANGE`.
- **File content is DECISION-class, never STREAM** (SOURCE-DERIVED, 03 §4.3
  `[AUDIT-FIX 4]`): every write's payload goes **full-fidelity** to
  content-addressed blobs; the write event records the **hash**. Contents are
  load-bearing and reconstructible, not sampled. What a recorded *coalescing
  policy* may govern is event **granularity** (many small writes folded into one
  recorded event citing that policy) — a calibration with a named owner, never a
  silent content loss.

| Write payload field | Type | Meaning |
|---|---|---|
| `path` / `inode` | id | The object written. |
| `content_hash` | hash | **The full-fidelity blob address** of the bytes written. Content is recoverable. |
| `length` / `offset` | integer | Extent of the write. |
| `coalesced_under` | rule ref / null | If this event folds several physical writes, the coalescing-policy LAW it cites. |

```jsonc
// shape sketch, not a schema commitment
{
  "action": "FILE-WRITE", "actor": "proc:1841", "object": "inode:558112",
  "rule_cited": "law:perm:/var/log@5",
  "payload": { "path": "/var/log/app.log", "offset": 40960, "length": 512,
               "content_hash": "blake3:2c1d…", "coalesced_under": null }
}
```

**Worked example:** process 1841 appends 512 bytes to `/var/log/app.log`, as
permitted by `perm:/var/log@5`. The bytes go to a blob at `blake3:2c1d…`; the
record holds the hash. Replay reconstructs the file's exact contents at any
`asOf` by folding its write events and fetching the blobs — **time-travel
without snapshots** (03 §4.3). A create adds an inode to the tree; a link adds a
dentry; an unlink removes one. All are DECISION, all rule-cited.

### 3.4 Devices — bind / unbind

- **Subsystem:** Devices (03 §4.4). **Feeds:** the **live binding table**.
- **Verbs:** `DEVICE-BIND`, `DEVICE-UNBIND`, `DEVICE-GRANT`.
- **Fields (payload):** `device`, `driver`, `capability_ref` (the LAW §2.4 that
  registered the driver's capability), `binding_reason`.
- **Precondition:** a bind may only cite a driver whose capability was registered
  by a LAW record (§2.4). No capability record → the bind is a refusal, itself
  recorded (03 §1.2).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "DEVICE-BIND", "actor": "subsystem:dev", "object": "device:pci:0000:03:00.0",
  "target": "driver:nvme0", "rule_cited": "cap:driver:nvme0@1",
  "payload": { "device_class": "block", "binding_reason": "probe-match" }
}
```

**Worked example:** the PCI device at `03:00.0` is bound to `nvme0`, citing the
capability LAW `cap:driver:nvme0@1` (§2.4). The binding-table cache adds the pair
from this `seq`; an unbind removes it. "Which driver held this device between T1
and T2?" is a replay of bind/unbind events — the mutable-global-table blindness
of the conventional kernel (03 §4.4) is gone.

### 3.5 Communication — channel-open + send / receive

- **Subsystem:** Communication (03 §4.5). **Feeds:** the **queue state cache**.
- **Verbs:** `COMMS-OPEN`, `COMMS-CLOSE`, `COMMS-SEND`, `COMMS-RECV`.
- **Fields (payload):** `channel`, `endpoints` (from/to), `contract_ref` (the
  message-contract/queue LAW), and per send/receive: `payload_hash` **or** inline
  payload (full or hash-referenced per recorded coalescing policy, exactly as
  with files — 03 §4.5).
- **Kernel-internal state is shared-nothing:** the record is the only shared
  medium *inside* the kernel, which removes the unrecorded-shared-mutation race
  class from kernel state (03 §4.5).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "COMMS-SEND", "actor": "proc:1841", "object": "channel:sock:7729",
  "target": "proc:2050", "rule_cited": "law:msg-contract:unix-stream@2",
  "payload": { "seqno": 14, "length": 128, "payload_hash": "blake3:9ab0…" }
}
```

**Worked example:** process 1841 sends 128 bytes to 2050 over a UNIX-stream
channel, citing its message-contract LAW. The queue-state cache advances;
`COMMS-RECV` by 2050 (a separate DECISION) drains it. The complete
"who said what to whom through the kernel" ledger the conventional kernel lacks
(03 §4.5) is these events replayed. An open/close bracket the channel's lifetime.

### 3.6 Shared-memory GRANT (who shares which region with whom, under which rule)

- **Subsystem:** Communication / Memory boundary (03 §4.5 `[AUDIT-FIX 5]`).
  **Feeds:** the **shared-region grant ledger** (a cache of live shares).
- **Verb:** `SHM-GRANT` (and `SHM-REVOKE`).
- **The governance boundary, stated honestly** (SOURCE-DERIVED, 03 §4.5): the
  kernel governs the **granting** — a recorded decision of *who shares which
  region with whom, under what rule*. It does **not and cannot** audit the
  *interior writes* of the shared region; those are the applications' own
  activity (§6.3). "The record governs acts and grants, not private thoughts."

| SHM-GRANT payload field | Type | Meaning |
|---|---|---|
| `region` | id | The shared memory region (the `shm`/`MAP_SHARED` object). |
| `granter` | actor | Who owns/offers the region. |
| `grantees[]` | actor list | **Who is granted shared access.** |
| `mode` | enum | ro / rw / cow. |
| `rule_cited` (envelope) | rule ref | The permission/sharing LAW that admits this grant. |

```jsonc
// shape sketch, not a schema commitment
{
  "action": "SHM-GRANT", "actor": "proc:1841", "object": "shmregion:44",
  "target": "proc:2050", "rule_cited": "law:perm:shm:default@1",
  "payload": { "region": "shmregion:44", "granter": "proc:1841",
               "grantees": ["proc:2050"], "mode": "rw" }
}
```

**Worked example:** a browser process (1841) grants a rw share of
`shmregion:44` to a renderer (2050). This DECISION is recorded — the complete
ledger of *who was ever granted shared access to what* (03 §4.5). The bytes the
two processes then write *inside* region 44 are **not** records (§6.3). What
gov-os adds is the grant ledger; what it honestly does not claim is
race-freedom inside userland's own shared region (the v0.1 over-claim corrected
in 03 §4.5).

---

## 4. INPUT records — external nondeterminism entering the record

**Class: INPUT** (SOURCE-DERIVED, 03 §2). INPUT is happenings the kernel does
**not author**: their *state-changing arrivals* are recorded; their *raw
high-frequency content* is sampled (that part is STREAM, §6). This is the
clock-as-sensor ruling generalised (02 §1.4, 03 §2): an external event is sensor
input written into the record; what *fires* from it is still decided only by the
record. An INPUT record's `actor` is the world/hardware source; its
`rule_cited` is the registration or policy that admits that input class.

**Why INPUT exists as a class — the determinism claim** (SOURCE-DERIVED, 03
§1.3 `[AUDIT-FIX 1]`): replay is deterministic **relative to the recorded input
stream**. Determinism is *conditioned on inputs being recorded, never "free."*
The kernel's decisions are a pure function of (LAW, DECISIONS, INPUTS); the only
nondeterminism is what the world hands it, so the world's arrivals must be
captured as records for replay to reproduce the same decisions. Record the
arrivals and the whole causal chain downstream replays identically; fail to
record one and replay diverges exactly there. INPUT records are the *arguments*
to `f`.

**Common INPUT payload fields:** `source` (device/line/clock), `arrival_kind`,
and a class-specific body. The arrival is load-bearing; the raw content beneath
it (every byte of a packet's history, every nanosecond of the timer) is sampled.

### 4.1 Interrupt arrival

- **Class:** INPUT. **Feeds:** whichever DECISION consumes it (e.g. a device
  completion → a scheduling wake, §3.1). **SOURCE-DERIVED**, 03 §4.4 (interrupts
  and completions as arrival events).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "IRQ-ARRIVAL", "actor": "hw:irq:42", "object": "driver:nvme0",
  "rule_cited": "cap:driver:nvme0@1",
  "payload": { "irq": 42, "arrival_kind": "edge" }
}
```

**Worked example:** IRQ 42 fires for `nvme0`. Recorded as an arrival. The
handler's decisions replay deterministically *given* this arrival; without the
arrival record, replay could not know the interrupt happened at all.

### 4.2 I/O completion

- **Class:** INPUT. **Feeds:** scheduling wakes (§3.1), file/comms decisions.
  **SOURCE-DERIVED**, 03 §4.2 (faults/completions as arrival events), §4.4.

```jsonc
// shape sketch, not a schema commitment
{
  "action": "IO-COMPLETION", "actor": "device:nvme0", "object": "ioreq:88f0",
  "rule_cited": "cap:driver:nvme0@1",
  "payload": { "ioreq": "88f0", "status": "ok", "bytes": 4096 }
}
```

**Worked example:** the read request `88f0` completes with 4096 bytes. This
INPUT is the `wake_cause_ref` cited by the schedule-admit in §3.1 — the causal
link from world-event to governed decision is a record edge, replayable.

### 4.3 Timer tick

- **Class:** INPUT (the clock-as-sensor case, 02 §1.4). **Feeds:** elapsed-time
  obligation predicates (02 §2, seam S3), scheduling. **SOURCE-DERIVED**, 03 §2,
  02 §1.4. Scheduled execution is lawful: the tick is *sensor input*; what fires
  is decided by the record (02 banner ruling 1).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "TIMER-TICK", "actor": "clock:monotonic", "object": "kernel",
  "rule_cited": "law:tick-policy@1",
  "payload": { "tick_seq": 99401, "elapsed_ns_since": 1000000 }
}
```

**Worked example:** a monotonic tick is recorded. Obligations whose predicate
reads elapsed record-time may now fire — and the firing is itself a DECISION
citing its rule. Replay from ticks alone reproduces every time-triggered action
(an 18-month review trigger fires from replay alone — seam S3 acceptance).
Only *state-changing* ticks need recording; the raw high-frequency tick stream
is sampled (§6.2).

### 4.4 Packet arrival

- **Class:** INPUT. **Feeds:** comms queue state (§3.5). **SOURCE-DERIVED**, 03
  §2 (packet arrivals as input events), §4.5.
- **Arrival recorded; raw payload sampled or hash-referenced** — the arrival
  that changes queue state is load-bearing; the full high-volume payload traffic
  is under the recorded coalescing policy (03 §4.5), same discipline as file
  content (blob-referenced) versus read-traffic (sampled).

```jsonc
// shape sketch, not a schema commitment
{
  "action": "PACKET-ARRIVAL", "actor": "nic:eth0", "object": "channel:sock:7729",
  "rule_cited": "law:msg-contract:tcp@1",
  "payload": { "flow": "tcp:…:443", "length": 1460, "payload_hash": "blake3:71c…" }
}
```

**Worked example:** a 1460-byte TCP segment arrives for socket 7729. The arrival
advances queue state and is recorded (payload hash-referenced per policy); the
subsequent `COMMS-RECV` DECISION (§3.5) drains it. Replay reconstructs the
channel's delivery order from recorded arrivals — the "who received what, when"
ledger the conventional kernel loses.

---

## 5. Cross-cutting: how a record's class is decided

A quick decision procedure (INFERRED from 03 §2, offered as a checklist, not new
law):

1. **Does it change the rules of rules?** → **LAW** (§2). Recorded totally, with
   amendment authority.
2. **Does it change law-derived state by an act the kernel authored?** →
   **DECISION** (§3). Recorded in full, rule-cited, never sampled. If it acted on
   stream evidence, embed the evidence summary (§3.2).
3. **Is it a happening the kernel did not author, that changes state?** →
   **INPUT** (§4). Record the arrival; sample the raw content.
4. **Is it derived output, or raw already-governed operation flow?** → **not a
   record** (§6): CACHE or STREAM.

The reconstruction invariant is the test of correctness: if replaying LAW +
DECISIONS + INPUTS does **not** reproduce a piece of state, then something that
belonged in one of the three classes was misfiled as CACHE or STREAM — that is
the "cache kept, ledger burned" pathology 03 §0 diagnoses, caught by the
round-trip law (02 §1.3, standing CI gate: delete every derived artifact,
replay, reconstruct identically).

---

## 6. What is NOT a record (and why the omission is honest)

Not everything the kernel does is appended. Two classes are deliberately outside
the log; naming them is part of the honest-observability-boundary guarantee
(03 §1.5). **SOURCE-DERIVED**, 03 §2 (CACHE, STREAM), §4.5 `[AUDIT-FIX 5]`.

### 6.1 Cache reads (CACHE class — derived, never appended)

The hot structures — run-queue, page tables, fd table, dentry cache, binding
table, queue state — are **CACHE**: derived, held in fast memory, discardable,
and reconstructible, because caches read **only** from LAW + DECISIONS + INPUTS,
never from samples. **Reading** a cache changes nothing governed and appends
nothing. **A crash loses only caches; recovery is recompute** (03 §2, 02 §1.5
snapshot law). If a cache read *were* recorded, it would be storing a derivative
— the estate's first prohibition (`03-TARGET-STATE-ARCHITECTURE.md` §0, P2).
Caches are the *output* of `f`, and outputs are never stored.

### 6.2 Per-access stream operations (STREAM class — sampled/aggregated)

The raw operation flow — individual memory accesses, per-tick dispatches that
merely *apply already-recorded policy*, read-traffic, I/O throughput, per-packet
byte histories — is **STREAM**: sampled and aggregated ("measure everything
roughly"), **never load-bearing**, feeding observability and evidence, not
reconstruction (03 §2). The honest boundary (03 §1.5): **what is sampled is
observability, not audit.** Nothing load-bearing lives in a sample, and every
audit view states what it does not cover (coverage statements). Where a DECISION
*needed* stream evidence, that evidence is captured **at the decision** as the
embedded evidence-summary (§3.2), so the audit is complete at the decision even
though the raw stream behind it was sampled. The individual context switch, page
fault, and packet are re-derivable *in kind* from recorded law + boundary inputs;
recording each would cost more than the decision and would be storing
derivatives (`03-TARGET-STATE-ARCHITECTURE.md` §2).

### 6.3 Interior writes to userland shared memory (out of the kernel's ledger)

When the kernel records an `SHM-GRANT` (§3.6), it governs the **grant**. The
**interior writes** the sharing processes then perform inside that region are
**not records** and *cannot* be — they are the applications' own activity, at
memory speed, with no kernel gate crossing (03 §4.5 `[AUDIT-FIX 5]`). The
boundary is stated honestly rather than hidden:

- gov-os **removes** unrecorded shared mutation *of kernel state* (kernel
  internals are shared-nothing; the record is the only shared medium inside the
  kernel — §3.5).
- gov-os **adds** a complete ledger of *who was ever granted shared access to
  what* (§3.6).
- gov-os does **not** claim to audit *interior writes of userland's shared
  regions*; races there remain userland's business. The earlier
  "race-free by construction" claim was corrected on the record (03 §4.5). Like
  the lawful organisation: the record governs acts and grants, not private
  thoughts.

---

## 7. Reconstruction map (record → cache it feeds), at a glance

INFERRED summary table of the reconstruction roles named per shape above. The
right column is the CACHE (§6.1) that a replay of the left column rebuilds.

| Record shape | Class | § | Feeds (derived cache) |
|---|---|---|---|
| Scheduling-policy rule | LAW | 2.1 | run-queue (derived under it) |
| Memory-budget rule | LAW | 2.2 | page tables / free-lists (checked under it) |
| Permission rule | LAW | 2.3 | visibility view; gates file writes |
| Device-capability registration | LAW | 2.4 | binding table (derived under it) |
| Mount rule | LAW | 2.5 | directory-tree / namespace |
| Schedule-admit / deschedule | DECISION | 3.1 | run-queue / runnable-set |
| Memory grant / evict (+evidence) | DECISION | 3.2 | page tables / free-lists |
| File create / write / link / unlink | DECISION | 3.3 | directory tree, inode, dentry cache |
| Device bind / unbind | DECISION | 3.4 | live binding table |
| Comms open / send / recv | DECISION | 3.5 | queue state |
| Shared-memory GRANT | DECISION | 3.6 | shared-region grant ledger |
| Interrupt arrival | INPUT | 4.1 | consuming decision (e.g. sched wake) |
| I/O completion | INPUT | 4.2 | scheduling wake; file/comms decisions |
| Timer tick | INPUT | 4.3 | elapsed-time obligations; scheduling |
| Packet arrival | INPUT | 4.4 | comms queue state |

---

## 8. Honest caps (what this catalogue excludes)

Per `00-READ-FIRST.md` §6, every substantial output states what it excludes:

- **Shapes, not schemas.** Every JSON block is a shape sketch. Field names,
  encodings, tiers, and the blob-hash algorithm are illustrative and settle under
  seam S1 (one store contract), not here.
- **No `/proc` mapping.** Which record renders which `/proc`/`/sys` view (03
  §5.2) is the deferred view catalogue, not this document.
- **No calibration values.** Sampling rates, coalescing granularity, window
  sizes (§3.2, §4.4, §6.2) are owner-ruled from evidence (03 §8) — never invented
  here; the shapes only reserve the *fields* that carry them.
- **Ordering proof deferred.** The built-ID tiebreak shape is fixed (§1.2); the
  proof that time-hash + tiebreak yields deterministic replay under every
  interleaving, and the ≥3-way collision case, are max-tier (03 §8).
- **Route-A framing.** These are the records a subsystem appends while shadowing
  and then assuming authority behind an unchanged Linux interface (03 §6, §7
  Route A). Under Route B the same shapes hold; only the substrate under them
  changes.

**Trained-knowledge flag:** OS vocabulary used as labels (page table, dentry,
IRQ, cgroup, `MAP_SHARED`, TCP) is trained knowledge used descriptively; every
*structural* claim about class, invariant, and reconstruction role carries a
citation to `03-TARGET-STATE-ARCHITECTURE.md` or `02-TECHNICAL-ARCHITECTURE.md`.

**Naming authority:** where this document's field names or verb sketches differ
from `12-OPERATIONS-CATALOGUE.md`, the canonical names are fixed in
`20-CANONICAL-GLOSSARY.md`, which controls until seam S1 freezes the schema.
