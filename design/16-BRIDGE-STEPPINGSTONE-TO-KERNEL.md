<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — The Bridge: from record-machine-as-program to record-kernel

> **SUPERSESSION NOTE (2026-07-18 line-audit).** CURRENT AND LOAD-BEARING — nothing
> here superseded. Campaign 1 completed the record-machine-as-program world this bridge
> starts from (with a governed surface this doc could only assume); the crossing itself
> IS Campaign 3 (DEPTH — design/32 §1), which reads this doc first.

**Status:** v0.1, 2026-07-12, xhigh, Route-A assumption. This is the one joint the
architecture named but never designed: how the thing you can build and prove THIS
MONTH (the record machine as an ordinary user-space program) becomes the thing at
the destination (the record kernel replacing Linux subsystem by subsystem). Read
`03-TARGET-STATE-ARCHITECTURE.md` §6 first. Labels per `00-READ-FIRST.md` §6.

---

## 0. Why this document exists

The estate already runs the record machine as an ordinary program (twc, cgl:
append-only store, registered gate, computed views — user-space, zero-dependency
Node). The destination is the same machine AS the kernel. Between them is a gap
nobody had crossed on paper: a user-space program and a kernel subsystem are not
the same artifact, and pretending the jump is trivial is exactly the
architecture-first failure mode (OSI: a clean map with no crossing to running
code). This document designs the crossing so the first kernel step is a small,
proven move, not a leap.

**The crossing is made in four stances**, each a working artifact, each strictly
more kernel-like than the last, and — the load-bearing property — **each one
ships value on its own even if the next never happens.** That is the Semantic-Web
antidote: never a stance whose cost is paid before any benefit arrives.

---

## 1. The four stances (the bridge itself)

### Stance 1 — The record machine as an application (EXISTS TODAY)
- **What it is:** the pwc/cgl spine — store + gate + views — running as a normal
  program on top of Linux. It governs *its own* domain objects (org seats, rules,
  dictionary entries).
- **Kernel-likeness:** low. It governs application data, not machine resources.
- **Ships alone:** yes — it already does (the running estate).
- **What it proves for the bridge:** the five-class discipline and the
  reconstruction invariant hold in practice at application scale.

### Stance 2 — The record machine governing REAL OS resources, in user space
- **What it is:** the same spine, but its objects become *shadows of real kernel
  resources*. It observes real Linux activity through the interfaces Linux
  already exposes to user space — the `/proc` and `/sys` views, `inotify`/fanotify
  for file events, `ptrace`/seccomp-notify or eBPF for syscall observation,
  netlink for device/network events — and records them as INPUT and DECISION
  events, deriving its own caches (a shadow process table, a shadow mount table,
  a shadow fd table).
- **Kernel-likeness:** medium. It now models machine resources, but only observes
  — Linux is still authoritative. It cannot yet decide; it can only record and
  derive.
- **Ships alone:** yes, and richly — this IS an audit product: a running Linux box
  gains a complete, replayable, rule-cited ledger of process/file/device/network
  activity that Linux itself cannot produce. asOf queries ("what could this
  process see at T", "who bound this device, when, under what") work on a real
  machine. Full-grade auditability as a bolt-on, before touching the kernel.
- **What it proves for the bridge:** that gov-os's derived caches can track a real
  kernel's live state — the exact shadow half of shadow/assume/retire, running
  against reality, with **zero risk** because it holds no authority.
- **INFERRED, flagged:** the observation interfaces above are trained-knowledge
  Linux facilities; which combination gives complete-enough coverage is a
  calibration to settle with evidence (a coverage audit), not to assume.

### Stance 3 — The record machine TAKING AUTHORITY for one cold subsystem, still in user space
- **What it is:** for the coldest subsystem (files — §03 orders it first), the
  gov-os machine stops merely shadowing and starts *serving*. Implemented via a
  user-space filesystem interface Linux already provides — **FUSE** — so a real
  mount point is backed by the record machine: file events become recorded
  decisions, contents go to content-addressed blobs, the directory tree is a
  derived cache, and asOf/history is native. Real programs read and write this
  mount without knowing it is records-backed.
- **Kernel-likeness:** high. It is now authoritative for a real OS resource,
  behind a real kernel interface (the VFS, via FUSE) — but still a user-space
  process, so a bug is a failed mount, not a dead machine. This is
  shadow→**assume** for one subsystem, executed at low blast radius.
- **Ships alone:** yes — a versioned, fully-auditable, time-travelling filesystem
  is a product in itself (compliance archives, tamper-evident records, "show me
  this directory as of last Tuesday").
- **What it proves for the bridge:** that the assume step works against real
  userland — that programs cannot tell a records-backed resource from a native
  one, through a real kernel interface. Everything Route A needs to know about
  the hardest question (does the inversion survive contact with real programs?)
  is answered here, still in user space, still safe.

### Stance 4 — The subsystem moves below the syscall line (the kernel step proper)
- **What it is:** the proven records-backed subsystem is moved from a FUSE server
  into the kernel's own VFS layer (Route A: inside a Linux kernel, replacing the
  filesystem subsystem behind the unchanged VFS interface; the shadow/assume/
  retire pattern from §03 §6, now below the syscall line). FUSE's user↔kernel
  transport is removed; the same derivation runs in kernel context.
- **Kernel-likeness:** total. This is the first real kernel subsystem replaced.
- **Ships alone:** yes — a working kernel with strictly more auditability than
  the day before, and every other subsystem still stock Linux.
- **What it proves:** the pattern that all remaining subsystems (devices, comms,
  memory, scheduling) will follow. Stance 4 done once = the route is real; repeat
  per subsystem, hottest last.

---

## 2. What crosses at each stance boundary (the honest deltas)

The crossings are where the real engineering lives; naming them is the point.

| Boundary | What genuinely changes | What stays identical | The risk it retires |
|---|---|---|---|
| 1→2 | objects become resource-shadows; add observation adapters | store + gate + views spine | "can the machine model real OS state at all?" |
| 2→3 | shadow gains authority for one resource via FUSE | the recording classes; the derivations | "can programs use a records-backed resource unaware?" |
| 3→4 | user-space FUSE server → in-kernel VFS module | the record shapes; the reconstruction invariant | "does the derivation survive kernel context (no libc, constrained memory, interrupt context)?" |

The 3→4 delta is the single hardest crossing and it is deliberately faced LAST
and SMALLEST — one already-proven subsystem, moved down one layer, behind an
interface already held constant. That is the difference between this plan and
"write a kernel."

## 3. Why this ordering is forced, not chosen (derivation)

Each stance retires exactly one class of unknown, in dependency order:
- you cannot test "programs use it unaware" (stance 3) before "the machine can
  model the resource" (stance 2);
- you cannot test "survives kernel context" (stance 4) before "works
  authoritatively at all" (stance 3).

So the ordering is not a preference — it is the unknowns' own dependency graph.
And because each stance ships value alone, the project is never in a state where
months of work precede any payoff (the OWL death). If the project stops at stance
2, the owner has a first-of-its-kind Linux audit layer. If it stops at stance 3,
a time-travelling filesystem. Only stance 4 requires kernel commitment, and by
then every representational risk is already retired in user space.

## 4. Where this meets the rest of the package

- The **syscall conformance map** (`10-`) is the acceptance spec for stances 3–4:
  every file-touching syscall must behave identically across the FUSE mount, then
  across the in-kernel module.
- The **seam contracts** (`14-`) formalise the shadow↔authoritative handoff used
  at 2→3 and 3→4.
- The **failure book** (`15-`) owns the divergence case: if a shadow's derived
  state diverges from Linux's live state, the assume is halted and the divergence
  recorded — the safety catch that makes taking authority reversible.
- The **build-route decision** (`03 §7`) is unblocked by this document: stances
  1–3 are Route-A-agnostic (they work regardless), and only stance 4 commits to a
  route. So the owner can authorise stances 1–3 now and defer the route ruling to
  the stance-3→4 boundary — the decision is needed later than it looked.

## 5. Honest caps

- Stances 1–2 are near-term and low-risk (observation only). Stance 3 (FUSE) is
  established technology used unconventionally. Stance 4 is real kernel
  engineering and is where effort concentrates — correctly, and last.
- The observation-coverage question at stance 2 (does the combination of
  /proc + inotify + eBPF + netlink capture *enough* to derive faithful caches?)
  is a calibration with a named owner and an evidence step (a coverage audit),
  not an assumption. PROPOSED; cost if wrong: some resource classes need a deeper
  observation hook than user space offers, which simply moves them earlier into
  the kernel — a local change, not a plan failure.
- Everything here is INFERRED architecture extending the corpus to the metal;
  the Linux facilities named (FUSE, /proc, inotify, eBPF, netlink, ptrace/seccomp)
  are trained knowledge at Estimate — High.
- **This is the bridge Lisp's `eval` was to its theory and TCP/IP's running code
  was to OSI's map:** the small proven slice that turns an architecture into a
  thing that runs. Stance 2 is the earliest place it starts running.
