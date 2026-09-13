<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Views & /proc Catalogue (every question the kernel can answer)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** The VIEWS half is superseded in
> mechanism: views are definition RECORDS executed by one engine; the seven masters are
> genesis-seeded records binding named S-plane folds, owner-tier and conserved (EP-08/
> 08B); delivery is the standing push with derived queues (append-nothing, kill-replay
> identical); new gauges exist (toothless-musts, metabolism, paper-tigers). Live canon:
> design/28 §6 + design/25. Sight-FILTERED reads arrive with Campaign 2 (PACK-SCOPE).
> The /proc half stands unchanged and feeds Campaign 3.

**Status:** v0.1, 2026-07-12, Route-A assumption (§7A of `03-TARGET-STATE-ARCHITECTURE.md`: the `/proc` and `/sys` shapes are the pseudo-filesystem *port* — held compatible so unmodified userland reads them — while the answers are computed honestly from the record). Read `00-READ-FIRST.md`, `03-TARGET-STATE-ARCHITECTURE.md`, then `12-OPERATIONS-CATALOGUE.md` (the decisions these views fold) before this. Labels per contract: SOURCE-DERIVED (cites), INFERRED (from what), PROPOSED (cost if wrong), trained knowledge (flagged). **Linux `/proc` and `/sys` shapes named below are trained knowledge** (their fields and layout); the *derivation* of those shapes from the record is the design content.

---

## Intro

This catalogue enumerates every question the kernel can answer. In gov-os no
"current state" is stored — no run-queue, page table, fd table, mount table, or
binding table is primitive truth. Each is a **view**: a pure fold over the recorded
decisions of `12-OPERATIONS-CATALOGUE.md`, recomputable to identity and to any past
point (`asOf`), with caches that accelerate the fold but never *are* the answer
(target-state §L2; twc P2 — "everything current is computed"). The conventional
kernel exposes the same questions through `/proc` and `/sys`, but there they are
snapshots of mutable structures with no provenance: `ps` cannot say *why* a task
ran, and no file says *who* set a mount or *when* a mapping was granted. Here every
`/proc` entry is honestly what it always morally was — a computed reflection of
state — and because the state folds recorded law, decisions, and inputs, the
reflection carries its provenance. Each view states what it answers, which records
it folds, and a worked example; the `/proc` and `/sys` catalogue renders these views
under the compatible pseudo-filesystem shapes.

---

## Conventions (read once, applies to every view)

### What a view is

A view is a deterministic function `state = f(LAW, DECISIONS, INPUTS)` (target-state
§2 invariant). It reads only recorded law, recorded decisions, and recorded inputs —
never a sample (STREAM informs humans, never the function). Every view:

- **folds** an enumerated set of recorded operations (named per view below),
- accepts a universal **`asOf`** parameter (answer as of record-time T; default
  = now = latest `seq`),
- is backed by a **discardable cache** — delete every cache, replay, and the view
  reconstructs identically (the round-trip law, a standing CI gate: tech-arch §1.3),
- carries a **coverage statement** — what it does *not* cover — because "what is
  sampled is observability, not audit" (audit guarantee §1.5).

### The view template (used for each entry)

- **Answers:** the plain question.
- **Folds:** the recorded operations (from FILE 12) it replays.
- **`asOf`:** what the time-travel form gives.
- **Worked example:** records in → answer out.
- **Coverage:** stated exclusions.

### `/proc` honesty note (the recurring point)

Linux `/proc` and `/sys` are *already* virtual — they are not files on a disk, they
are the kernel rendering its live structures as readable paths on each `read()`
[trained knowledge]. gov-os changes nothing a program sees; it changes only what the
render reads *from*: not a mutable struct that forgot its history, but a fold over
the record. So each `/proc` entry is "a computed reflection of state — which is what
it always morally was." The novelty is not the virtual filesystem; it is that the
reflection can now cite its provenance and answer `asOf`.

### Labels on the views

The *machinery* (fold engine, `asOf`, round-trip law) is SOURCE-DERIVED (pwc/cgl
`views.js`; venn2 export→wipe→import). The specific kernel views here are INFERRED
(the target-state doc names the questions; the fold definitions extend the corpus to
the metal, which the corpus does not itself cover). The `/proc`/`/sys` field shapes
are trained knowledge. Where a view is genuinely new to gov-os (the why-did-this-run
audit, the asOf-visibility view, the metabolism gauge) it is marked at the entry.

---

## Section 1 — Process & scheduler views

### 1.1 Process table  (`ps` / `/proc`)
- **Answers:** which processes currently exist and their state
  (running/sleeping/stopped/zombie).
- **Folds:** `admit-process`, `deschedule`, `standby`, `halt`, `kill` (FILE 12 §1),
  plus bootstrap `CREATE-ACTOR` for the process's identity.
- **`asOf`:** the process table *as it stood at T* — including processes long since
  killed, reconstructed exactly.
- **Worked example:** replay for pid 481 finds `admit-process`(seq 900,
  class=normal), `deschedule`(seq 1204, cause=wait-on-input evt 1203), no later
  `admit`/`kill`. Fold → pid 481 is **sleeping**, waiting on input event 1203. The
  same fold at `asOf`=seq 1000 → **running**.
- **Coverage:** existence and coarse state are DECISION-derived and exact; live CPU%
  and instantaneous RSS are STREAM aggregates (observability) — the view labels them
  as sampled, not audit.

### 1.2 Per-process detail  (`/proc/[pid]/`)
- **Answers:** everything about one process — its identity, admitting rule, priority
  history, owner, and lifecycle boundary crossings.
- **Folds:** the same `admit/deschedule/set-priority/kill` decisions filtered to one
  pid, plus every decision whose `actor` is that pid.
- **`asOf`:** the full process dossier as of T.
- **Worked example:** `/proc/481/status` renders name, state (from 1.1), and — the
  gov-os addition — `admitted_under: SCHED-LAW-ADMIT (seq 900)` and a priority
  history `[normal@900, high@1500 under SCHED-LAW-PRIORITY]`. Linux shows the current
  priority; gov-os shows every priority it ever held and the rule for each.
- **Coverage:** trained-knowledge `/proc/[pid]` fields (comm, state, ppid, uid) are
  all present; the *provenance* fields are the derived addition.

### 1.3 Scheduler state — **why-did-this-run**  (audit view; gov-os-native)
- **Answers:** why did this task run (or not run) at time T, citing the rule — the
  audit view a conventional scheduler structurally cannot offer (target-state §4.1:
  "the scheduler's reasoning evaporates as it acts").
- **Folds:** scheduling DECISIONS (`admit/deschedule/set-priority/halt/standby`) +
  the recorded INPUTS that caused wakes (timer ticks, I/O completions) + the LAW in
  force (`SCHED-LAW-*`). Dispatch is a pure function of these, so the schedule
  replays exactly; cross-core races are *settled* (not described) by the intake
  pipeline's definitional order [AUDIT-FIX 2].
- **`asOf`:** the dispatch reasoning at any past instant — reconstructed, not logged.
- **Worked example:** "why did pid 481 run at record-time T?" replays: at seq 1203 an
  I/O completion (INPUT) woke it; `SCHED-LAW-PRIORITY` placed class=high (seq 1500)
  ahead of the runnable set; no `halt` was in force; dispatch selected 481. Answer:
  *"ran because input evt 1203 made it runnable and priority rule (seq 1500) ordered
  it first; cited SCHED-LAW-ORDER."* One tick later in Linux this is unanswerable;
  here it is answerable forever.
- **Coverage:** answers the *governed* why (which rule, which input, which order).
  Nanosecond hardware timing is STREAM — the view states that timing is
  observability, and that the *order* it reports is the record's definitional order,
  not a hardware measurement.

---

## Section 2 — Memory views

### 2.1 Memory map — who-was-granted-what  (`/proc/[pid]/maps`)
- **Answers:** which regions this process holds, their protections, and — the
  gov-os addition — who granted each, when, and under which budget rule.
- **Folds:** `grant-mapping`, `protect-region`, `evict-page` (FILE 12 §2) filtered
  to the pid, against `MEM-LAW-*`.
- **`asOf`:** the process's memory map as of T, including regions since evicted.
- **Worked example:** `/proc/481/maps` replays two grants (seq 950 region A rw under
  `MEM-LAW-ALLOC`, budget check citing `MEM-LAW-BUDGET`; seq 980 region B rx), a
  `protect-region` on A (seq 1010 rw→r), and an `evict-page` touching A (seq 1600,
  `evidence_summary`: cold-page aggregate). Fold → current map = A (r), B (rx); and the view
  can answer "who was granted region A and under what budget?" → *granted seq 950
  under MEM-LAW-BUDGET*. Linux's `maps` shows the ranges; it has no "who/when/under
  which rule."
- **Coverage:** grants/protections/evictions are exact (DECISION-class). Live
  page-residency churn is STREAM; the view marks residency as sampled and the *grant
  ledger* as audit.

### 2.2 Memory pressure & OOM history  (`/proc/meminfo`, OOM audit; gov-os-native audit)
- **Answers:** current allocation vs budget per actor, and — the addition — the full
  OOM decision history with the evidence each acted on.
- **Folds:** `grant-mapping`, `evict-page`, `amend-budget`, `oom-decision` against
  `MEM-LAW-BUDGET/EVICT/OOM`.
- **`asOf`:** budget posture and any OOM event as of T.
- **Worked example:** an `oom-decision` at seq 1600 recorded victim=pid 620,
  reclaimed=512MB, `rule_cited`:`MEM-LAW-OOM`, `evidence_summary`: pressure aggregate + victim
  ranking. The view answers "why was pid 620 killed for memory?" → *selected by the
  OOM ordering law under recorded pressure aggregate A*. In Linux the OOM killer acts
  "silently on live state" (target-state §4.2); here it is a cited, replayable
  decision.
- **Coverage:** decisions and their embedded evidence are audit-complete; the raw
  access stream behind the aggregate was sampled and is not reconstructible byte-for-
  byte — the view says so [AUDIT-FIX 3].

---

## Section 3 — File & mount views

### 3.1 Open files  (`/proc/[pid]/fd`)
- **Answers:** which files/channels this process currently has open, and how each was
  acquired.
- **Folds:** `create`, `write`, `open-channel`, `receive`, `close` filtered to the
  pid; open = acquired-and-not-closed under the fold.
- **`asOf`:** the fd set as of T.
- **Worked example:** pid 481 has `create`(seq 1002, /tmp/x) and `open-channel`(seq
  1100, chan 7), no matching `close`. Fold → fd table = {fd3→/tmp/x, fd4→chan7}. The
  view can also answer "when and under which rule did fd3 open?" → *seq 1002,
  FS-LAW-NAMESPACE*.
- **Coverage:** open/closed status exact; per-fd read/write *throughput* is STREAM.

### 3.2 File history — time-travel per file  (gov-os-native)
- **Answers:** the complete content and permission history of one file — every write
  (by content hash), link/unlink, and permission change, replayable to any point.
- **Folds:** `create`, `write`, `link`, `unlink`, `change-permission` for one inode
  against `FS-LAW-*`.
- **`asOf`:** the file's exact content (via the recorded hash) and permission set at
  T — "time-travel without snapshots" (target-state §4.3).
- **Worked example:** /etc/conf shows `write`(seq 300 hash H1), `write`(seq 900 hash
  H2), `change-permission`(seq 950 644→640). `asOf`=seq 400 → content H1, perms 644;
  now → content H2, perms 640. Because content is DECISION-class (never sampled,
  [AUDIT-FIX 4]) the historical bytes are the real bytes, fetched by hash.
- **Coverage:** full-fidelity for content and permissions; where a write *event* was
  coalesced under `FS-LAW-COALESCE`, the view notes the coalescing policy and its
  named owner (a calibration, never a silent gap).

### 3.3 Mount table  (`/proc/mounts`)
- **Answers:** what is mounted where, and — the addition — who mounted it, when,
  under which mount rule.
- **Folds:** `mount`, `unmount` (FILE 12 §3) against `FS-LAW-MOUNT`; mounted =
  mounted-and-not-unmounted.
- **`asOf`:** the mount table as of T.
- **Worked example:** `mount`(seq 120, src=/dev/sda2 → /home, `FS-LAW-MOUNT`, by
  ADMIN) with no later `unmount`. Fold → /home is mounted from /dev/sda2; and the
  gov-os question "who set this mount and when?" → *ADMIN, seq 120* — the very
  question that "has NO answer today" in Linux (kernel target-state §1).
- **Coverage:** mount identity/authority exact; per-mount I/O stats are STREAM.

---

## Section 4 — Device & capability views

### 4.1 Device bindings  (`/sys`, `lsdev`-shape)
- **Answers:** which drivers are bound to which devices, and which actors hold which
  device capabilities — with the authorising amendment for each.
- **Folds:** `register-driver`, `bind-device`, `unbind`, `grant-capability` (FILE 12
  §4) against `CAP-IS-LAW`/`DEV-LAW-*`.
- **`asOf`:** the binding and capability posture as of T.
- **Worked example:** `register-driver`(seq 60, nvme, by ADMIN, `CAP-IS-LAW`) then
  `bind-device`(seq 61, disk0→nvme). Fold → disk0 bound to nvme; and "which driver
  claimed disk0, when, under whose rule?" → *nvme, seq 61, registered as amendment
  seq 60 by ADMIN* — "the exact gap in the conventional kernel" (target-state §4.4).
- **Coverage:** bindings and grants exact; device I/O throughput is STREAM.

### 4.2 Capability ledger — who-was-granted-what (devices)  (gov-os-native audit)
- **Answers:** every device capability any actor was *ever* granted, and by whom.
- **Folds:** `grant-capability`, `register-driver` across all actors.
- **`asOf`:** the capability grant set as of T (grants are events, so a revoked grant
  is still visible in history).
- **Worked example:** actor `svc-log` shows `grant-capability`(seq 700, cap=raw-disk,
  by ADMIN). The view answers "who can touch raw disk and how did they get it?" →
  *svc-log, granted seq 700 by ADMIN under CAP-IS-LAW*.
- **Coverage:** complete grant ledger; whether a granted capability was *exercised*
  is answered by the I/O STREAM (observability), which the view flags as sampled.

---

## Section 5 — Communication views

### 5.1 Open channels & shared regions  (gov-os-native audit)
- **Answers:** which channels are open between which endpoints, and — the honest
  addition — who was ever granted shared access to which memory region, under what
  rule.
- **Folds:** `open-channel`, `close`, `grant-shared-region` (FILE 12 §5) against
  `COMM-LAW-*`.
- **`asOf`:** the channel/shared-region grant posture as of T.
- **Worked example:** `grant-shared-region`(seq 1300, region R, actors {A,B},
  `COMM-LAW-SHARE-GRANT`). The view answers "who shares R?" → *A and B, granted seq
  1300*. Per target-state §4.5 [AUDIT-FIX 5]: the *grant* is fully audited; the
  interior writes to R are userland's own activity and are honestly out of scope —
  the view states this boundary rather than pretending to cover it.
- **Coverage:** the complete grant-and-channel ledger at the kernel boundary; the
  *contents* exchanged over a channel are DECISION-class (hashed) or, under a
  recorded coalescing policy, folded — the view names the policy; interior shared-
  region writes are explicitly uncovered.

### 5.2 Message ledger  (per channel / per actor)
- **Answers:** who sent/received what through the kernel, and when — "a complete
  grant-and-message ledger" (target-state §4.5), which a conventional kernel does not
  keep at all.
- **Folds:** `send`, `receive` for a channel or actor.
- **`asOf`:** the message flow through T.
- **Worked example:** channel 7 replays `send`(seq 1310, msg H9 by A), `receive`(seq
  1320, msg H9 by B). The view answers "did B receive A's message?" → *yes, seq 1320*
  — an ordinary audit question with no answer in Linux.
- **Coverage:** send/receive *events* and message identity (hash) are audit; high-
  volume payload *traffic* is STREAM under the recorded coalescing policy.

---

## Section 6 — Audit & history views (the cross-cutting time machine)

### 6.1 `asOf` visibility — what could actor X see at time T  (gov-os-native)
- **Answers:** the exact set of records/objects actor X was permitted to read as of
  T — the sight-is-law posture, replayed.
- **Folds:** every grant that populates X's readable view — `change-permission`,
  `grant-mapping`, `grant-capability`, `grant-shared-region`, `open-channel`, plus
  the blindness registry (target-state §3: visibility is computed AND binding;
  default-deny including aggregates; grants are events).
- **`asOf`:** the crux — because visibility is itself a fold over recorded grants, "X
  at T saw exactly V" is mechanical. This underwrites `SIGHT-IS-LAW` refusals in FILE
  12: an actor may not act on what a *replay* shows it could not read.
- **Worked example:** did pid 481 have read on /etc/conf at seq 400? Fold the
  permission decisions on /etc/conf up to seq 400 and 481's grants → *no (640 was set
  at seq 950; at seq 400 it was 644 but 481 was not in the owning group)*. The
  provenance gate would have refused a seq-400 read, and the refusal itself is a
  recorded event.
- **Coverage:** visibility grants are exact; what X *actually looked at* (versus was
  permitted to) is a READ-activity question (6.3), distinct from permission.

### 6.2 who-granted-what-when  (gov-os-native audit)
- **Answers:** for any granted thing — a mapping, a capability, a permission, a
  shared region, a priority — the actor who granted it, the time, and the rule cited.
- **Folds:** every grant/amend decision across subsystems (`grant-*`, `amend-budget`,
  `set-priority`, `change-permission`, `register-driver`, `mount`).
- **`asOf`:** the grant lineage as of T.
- **Worked example:** "account for every actor holding raw-disk capability and how" →
  the fold returns each `grant-capability` with granter, seq, and `CAP-IS-LAW`
  citation. This is Attribution + Explanation (audit guarantees §1.1–1.2) rendered as
  a query — "permissions no one can account for" (the §0 pathology) becomes fully
  accountable.
- **Coverage:** every grant is attributed; a grant made outside the gate cannot
  exist (it would be a Closure Hit), so the ledger is complete by construction.

### 6.3 Refusal & violation view  (gov-os-native audit)
- **Answers:** every refusal and violation, with the rule each cited — a first-class
  view because "every refusal is itself recorded" (FILE 12 cross-cutting invariant 2).
- **Folds:** all `refused:true` decisions (BLOCK events) across every operation.
- **`asOf`:** the refusal history through T.
- **Worked example:** "why did pid 620's mmap fail at seq 1450?" → a refusal record
  `grant-mapping refused, rule_cited: MEM-LAW-BUDGET, reason: over budget`. Contrast
  Linux, where the caller got `ENOMEM` and the *rule* it hit vanished. Also surfaces
  Closure Hits (`P3-CLOSURE`) for the owner.
- **Coverage:** complete — refusals cannot escape the record; this view is the direct
  proof of the "enforcement can explain itself" property.

### 6.4 Full replay / round-trip attestation  (gov-os-native)
- **Answers:** does the entire derived state reconstruct from the record alone? — the
  standing integrity check.
- **Folds:** *everything* — delete every cache and view, replay genesis→now (or
  from a governed checkpoint citing its seq), and diff.
- **`asOf`:** by definition every `asOf` answer is a partial replay; this view is the
  total one.
- **Worked example:** the CI gate: export → wipe → import → byte-identical (venn2
  already runs this; tech-arch §1.3). A non-empty diff is an alarm, not a rounding
  error — it means a cache diverged from the record, and the record wins.
- **Coverage:** covers all governed state (LAW+DECISION+INPUT-derived). Data-plane
  content recovers per its own store's guarantees; a power-cut in-flight tail is
  bounded and recorded as a recovery scar (honest, never silent — tech-arch §1.1).

---

## Section 7 — Governance-debt / metabolism views

### 7.1 Rule metabolism — intake vs retirement  (gov-os-native; INFERRED, cheap)
- **Answers:** at what rate is law being created versus retired, per subsystem — the
  governance-debt gauge (target-state §L3 metabolism; tech-arch §2: "when rule intake
  exceeds retirement capacity, governance debt accumulates").
- **Folds:** `CREATE-RULE` decisions (and their subsystem `*-LAW-*` amendments)
  versus REMOVE-FROM-VIEW-of-a-rule activities, windowed over record-time.
- **`asOf`:** the debt posture at T, and the trend up to it.
- **Worked example:** last window shows 14 `CREATE-RULE` (mounts, capability grants,
  budget amendments) and 3 rule retirements → intake:retirement = 14:3, debt rising
  in the DEV subsystem (11 of the 14 were `register-driver` amendments). Pure view
  work over existing records — "no new primitives" (tech-arch §2).
- **Coverage:** a computed dashboard over recorded LAW changes; it measures rule
  *counts and rates*, not rule *quality* (that is a human-gate judgment, not a fold).

### 7.2 Active law surface  (`/proc/config`-shape; gov-os-native)
- **Answers:** the entire active rule set right now — every `*-LAW-*` and root rule
  in force, each with its amendment authority and provenance. The control plane the
  §0 diagnosis says is scattered across /etc, sysctl, nftables, cgroups, systemd —
  here rendered as one governed, provenance-carrying view (kernel target-state §1).
- **Folds:** all `CREATE-RULE`/amendment decisions minus retirements; active =
  created-and-not-retired-and-not-contradicted.
- **`asOf`:** the law in force at T — "what was the policy when this decision was
  made?" is answerable.
- **Worked example:** "who set this scheduling priority policy, when, and why?" →
  active-law view returns `SCHED-LAW-PRIORITY`, amended seq 1500 by ADMIN, superseding
  the seq-40 boot default. In Linux this "has NO answer today."
- **Coverage:** every active rule with provenance; the *interpretation* of an
  unstructured rule is a plug-in (ogs-kernel-scope "does NOT contain"), not part of
  the fold.

---

## Section 8 — The `/proc` & `/sys` catalogue (compatible shapes → derived views)

Trained knowledge: the paths and field shapes below are Linux's. INFERRED: the
mapping of each to a gov-os view (the "derived from" column) and the added-answer it
newly supports. All are *reads* — `/proc` and `/sys` are render-on-read views, so
this is the pseudo-filesystem port (target-state §5.2) rendered over Section 1–7.

| Path (trained-knowledge shape) | Renders view | Folds (FILE 12 ops) | Gov-os added answer |
|---|---|---|---|
| `/proc` (dir of pids) | 1.1 Process table | admit/deschedule/standby/halt/kill | `asOf` process table incl. dead pids |
| `/proc/[pid]/status` | 1.2 Per-process detail | + CREATE-ACTOR, set-priority | admitting rule + full priority history |
| `/proc/[pid]/sched` | 1.3 why-did-this-run | sched decisions + INPUTs + LAW | the rule+input+order that dispatched it |
| `/proc/[pid]/maps` | 2.1 Memory map | grant-mapping/protect/evict | who-granted-what, under which budget |
| `/proc/meminfo` + OOM audit | 2.2 Pressure & OOM history | grant/evict/amend-budget/oom | replayable, evidence-cited OOM |
| `/proc/[pid]/fd` | 3.1 Open files | create/open-channel/close | when + rule each fd opened |
| `/proc/mounts` | 3.3 Mount table | mount/unmount | who mounted, when, under which rule |
| `/sys/devices`, `/sys/bus` | 4.1 Device bindings | register-driver/bind/unbind | which driver claimed what, under whose amendment |
| `/proc/config`-shape | 7.2 Active law surface | all CREATE-RULE/amendments | one provenance-carrying control plane |
| *(no Linux equivalent)* | 1.3 / 6.1 / 6.2 / 6.3 / 7.1 | — | why-ran, asOf-visibility, grant lineage, refusals, metabolism |

**The honesty line (recurring):** each `/proc` entry above is a computed reflection
of state — which is what it always morally was. gov-os does not add a virtual
filesystem; Linux already had one. It changes what the render reads from: a fold over
the record instead of a mutable struct that forgot its history. The rows with "no
Linux equivalent" are the questions the burned ledger made *unanswerable* — recovered
here for free, because the record was never burned.

---

## Cross-cutting invariants (true of every view above)

1. **Nothing stored, everything folded.** No view reads a stored "current" value;
   each recomputes from LAW+DECISION+INPUT (twc P2; audit invariant §2). Caches are
   pure accelerations, discardable without loss.
2. **`asOf` is universal.** Every view answers "as of T" by folding up to that seq —
   audit guarantee §1.3 (Replay), conditioned on inputs being recorded.
3. **Ordering is definitional.** Where a view reports an order (dispatch, message
   flow), that order is the intake pipeline's recorded order — it *settles* races,
   it does not describe hardware timing [AUDIT-FIX 2].
4. **Coverage is stated, never implied.** Every view names its sampled (STREAM) parts
   and marks them observability, not audit (§1.5). Nothing load-bearing lives in a
   sample.
5. **Refusals are queryable state.** Denials are records, so "what was refused and
   why" is a first-class view (6.3) — the mechanical form of "enforcement can explain
   itself."

---

## What this catalogue excludes (named, not hidden)

- **Concrete `/proc` field-by-field layouts.** The exact byte format of each
  pseudo-file is a port-conformance artifact (target-state §5.2 / §8 named-open),
  not this design reference. Trained knowledge: the field *shapes*.
- **Cache/index implementation.** Memoisation keyed on append generation
  (tech-arch §1.3) is real, but it is acceleration; this doc specifies the *views*,
  not their caches.
- **Physical replay cost.** Replay-wall and tiering-fetch costs are unmeasured
  (tech-arch §12 honest caps); `asOf` correctness is specified, its cost is not.
- **Family view bodies.** The kernel ships view *machinery* plus this small set of
  kernel views; org/corpus/world/pipeline families bring their own view bodies
  (tech-arch §1.3) — out of scope here.
- **Interpretation of unstructured law.** 7.2 renders the active rule set; *applying*
  an unstructured rule is a declared plug-in (ogs-kernel-scope "does NOT contain"),
  not a fold this catalogue defines.
