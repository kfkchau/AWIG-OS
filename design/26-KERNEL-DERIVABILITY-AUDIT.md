<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Kernel Derivability Audit (everything, over the base tree)

**Status:** v1, 2026-07-15. The exhaustive check the owner ordered: walk every
concept a modern conventional kernel carries and express it over the base view
tree (`25-VIEW-TREE.md` / `25-view-tree.json`). PASS = derivable with no new
store, no new base node, no new operator. Notation: `do` = must-happen req,
`dont` = must-not req, `live` = live check, `3.1/3.2` = relationship families,
`[frame]` names the frame. Linux vocabulary is trained knowledge used as labels;
every mapping is the derivation content.

## 1. Processes and scheduling

| Conventional thing | Derivation over the base |
|---|---|
| process | system actor (tag: process), minted CREATE-ACTOR; principal = 3.1 [attribution] to a human/agentic actor |
| thread | process actor whose space custody fully overlaps its parent's (3.2 [custody]); thread-vs-process is DERIVED, not a type |
| fork | CREATE-ACTOR + custody edges copied; COW = shared content-housing split on first write event |
| exec | the actor's program housing content replaced (write event) |
| runnable | active process actors − wait/wake (1.2.2) − halts (1.2.1), under sched dos |
| sleeping | present in wait/wake view |
| stopped | halt event in force |
| zombie | exit recorded, reap obligation (a do) not yet fired — a pending duty, not a state flag |
| priority / nice | latest set-priority event folded; the policy = system policy item |
| real-time classes | dos carrying a deadline bound (the one place timing is semantic; T-REALTIME-BOUND) |
| CPU affinity | dont (must-not-dispatch outside core set) |
| cgroups | scope item housing actors (3.1 [grouping]) with budget dos/donts attached to the group item |
| sessions / process groups | same shape: grouping items + 3.1 membership |
| signals | messages through tunnels; delivery = event; permission to signal = live permission() |
| signal handler (sigaction) | registering a do: "when signal S hits this actor → run H" |
| SIGKILL / penalty chain | governance decisions (1.2.1), rule-cited, rung by rung |
| wait()/reaping | block on wait/wake keyed on child-exit; reap = a do |
| context switch / dispatch | STREAM; pure function of runnable + law; records nothing (doc 17/22) |
| load average | STREAM aggregate; tier-3 custom view |

## 2. Memory

| Conventional thing | Derivation |
|---|---|
| virtual address space | non-permanent space item per process actor |
| mmap region / heap / stack | content-housing items in that space (3.1 [custody]); heap/stack = labels derived from the creating action |
| page tables / free-lists | CACHE of custody relations; rebuilt by fold; never governed objects |
| minor page fault | cache fill of an already-recorded grant; records NOTHING (doc 22) |
| major fault | INPUT (io-completion) consumed by a cache fill |
| swap-out / swap-in | the housing's content re-parented between non-permanent and permanent space; the persistence split (2.2.2.1) carries swap natively |
| page cache | the inverse: permanent content cached in volatile space = pure CACHE, no records |
| copy-on-write | shared housing (3.2 [custody-overlap]) split by a write event |
| protection bits (rwx) | donts on the housing; the fault handler's check = live permission() |
| mlock | dont (must-not-evict this housing) |
| OOM | a do firing ("pressure condition → evict per rule"), decision embeds evidence (AUDIT-FIX 3) |
| budgets / limits | dos/donts per actor; headroom = live count of custody vs budget |
| huge pages / NUMA | space properties from providing device; placement preferences = reqs |
| shared memory | 3.2 overlap on one housing; grant recorded, interior writes honestly out (AUDIT-FIX 5) |

## 3. Files and VFS

| Conventional thing | Derivation |
|---|---|
| file | content-housing item in a permanent space |
| memory region | SAME item type in a volatile space (the unification the persistence ruling buys; mmap is the conventional kernel's own admission) |
| directory | scope item housing scope items (3.1 [namespace]) |
| inode | the item id itself |
| dentry / filename | a named 3.1 edge (name binding); hard link = second edge to the same item |
| symlink | content item whose content is a path; resolved by live walk of 3.1 |
| path resolution | walk 3.1 [namespace] root → name |
| fd / open file | custody edge (actor holds housing, with mode); seek offset = per-custody ephemeral cursor (CACHE) |
| dup/dup2 | another custody edge to the same housing |
| rename | unlink + link events (edge swap) |
| file locks (flock/fcntl) | temporary donts scoped to a housing with a holder |
| permissions / ownership / xattrs | req events attached to the housing; checks = live sight()/permission() |
| umask | a policy item consulted at create |
| mount / unmount | law events; the mount = a 3.1 edge grafting one space into another |
| chroot / namespaces (mnt, pid, net...) | actor confined to a space subtree: sight scoped by 3.1 + donts; a PID number = a per-space name binding, real identity stays the item id |
| /dev nodes | a name edge pointing at a DEVICE ACTOR — a file that is an actor |
| quotas | budget donts per actor per space |
| journaling | the event store itself; the journal was always the definitive half (03 §4.3 re-rooting) |

## 4. Devices and capability

| Conventional thing | Derivation |
|---|---|
| device | system actor (tag: device): asserts inputs, is bound/unbound as a resource |
| driver | system actor; its capability = policy item (registration = law amendment, CAP-IS-LAW) |
| module load/unload | CREATE-ACTOR/retire + capability amendment |
| interrupt | INPUT event asserted by a device actor |
| interrupt handler | a do: "when irq n from device D → run H under capability C" |
| IRQ routing | the do's condition term; no routing table stored |
| DMA / MMIO | STREAM inside capability-bounded windows |
| hotplug / udev rules | device actor appears (observed INPUT → CREATE-ACTOR); udev rules ARE dos ("when class X appears → bind Y") |
| power states / suspend | halt events scoped to device actors; wake = INPUT |

## 5. Communication and IPC

| Conventional thing | Derivation |
|---|---|
| socket / pipe / fifo | tunnel items; a named fifo = tunnel + name edge in the space tree |
| port / address | a name binding in a port space; bind = claiming the name; conflict = 3.2 contact on one name → refusal by dont |
| connection | tunnel + endpoint relations; topology = mediated contact (A through tunnel to B) |
| routing table | dos: "packet to X → send via Y"; a system policy item, not a table |
| firewall / netfilter | THE donts view under the comms frame — must-not-forward/accept when condition |
| message queues | tunnel items with queue reqs; depth = fold of send − receive |
| semaphore / futex | block on wait/wake keyed on a counter condition; post/wake = events; futex interior = userland's own (AUDIT-FIX 5) |
| select/poll/epoll | one actor blocked on an OR-set of wait/wake conditions |
| eventfd / timerfd / signalfd | tunnels carrying INPUT events |

## 6. Security

| Conventional thing | Derivation |
|---|---|
| users / groups | human actors; groups = grouping items + 3.1 membership |
| credentials / UIDs | actor identity + attribution chain |
| POSIX capabilities | live permission() over grant chains; never a stored bitmap |
| setuid | a conditional grant (a do on the exec condition) creating a temporary chain; fully attributed |
| SELinux/AppArmor policy | policy items full of donts — the donts view under a security frame |
| seccomp filter | per-actor donts over ACTION items (must-not-call verb V) |
| containers | actors confined to space subtrees: sight + donts + budgets composed; no new mechanism |
| keyrings / secrets | vault items: record holds grants and use-events, never values (the secrets ruling) |
| audit subsystem | 1.2.1 natively — gov-os's spine is what auditd bolts on |
| ptrace | sight + custody granted over another actor; a dangerous grant, chain-checked live |
| eBPF-style hooks | executable content items registered as dos/filters under capability law — amendments, not magic |

## 7. Time

| Conventional thing | Derivation |
|---|---|
| clock read | CACHE; records nothing (clock-as-sensor, doc 10) |
| tick | INPUT event |
| timer / alarm / timeout | a do with a time condition; firing = due() says so; the ONLY firing mechanism |
| NTP adjustment | governance activity amending clock policy |
| watchdog | a do: "no heartbeat by T → restart" |

## 8. Boot, lifecycle, integrity

| Conventional thing | Derivation |
|---|---|
| boot | genesis: PC_RUNTIME mints root law, SYSTEM, owner tunnel, mother space, hands off |
| init | first standing actor with standing dos |
| shutdown / suspend | halt chain, governed, recorded |
| panic | the kernel's own dont firing (must-not-continue with integrity broken) + halt |
| kexec / new kernel | capability amendment at the largest scale |
| entropy | INPUT (getrandom ruling); replay deterministic relative to recorded draws |
| core dump | a do ("on crash → mint content item of state") |
| /proc, /sys | renders of views (doc 13); dmesg = log render |
| getrusage / accounting | once-off aggregates over 1.2; tier 3 |

## 9. Honest boundaries (the misfit list — named, not hidden)

- **Ephemeral cursors** (seek offsets, TCP sequence positions): per-custody CACHE;
  not governed, correctly so — no law-derived state changes.
- **Performance-only structures** (slab, RCU, per-CPU pools, spinlocks): kernel-
  internal CACHE plumbing. Shared-nothing kernel state (03 §4.5) makes the lock
  question vanish at the governed layer; at implementation depth they are S-code.
- **Interior writes to shared userland memory** (futex data, shm contents):
  out by AUDIT-FIX 5. The grant is governed; the thoughts are not.
- **STREAM metrics** (load, throughput, cache hit-rates): observability, tier 3.

## Verdict

Every conventional-kernel concept walked here lands on the base with no new
store, no new base node, no new operator, and no new live check beyond the six.
Recurring discoveries: (1) all handler mechanisms — signal handlers, interrupt
handlers, udev rules, routing, timers, watchdogs — are dos; (2) all security
mechanisms — firewall, seccomp, LSM policy, locks, limits, protection bits —
are donts; (3) permission everywhere is a live check, nowhere a list; (4)
thread/process, file/region, swap/page-cache, zombie are derived distinctions,
not types. The conventional kernel is, in this frame, a do-executor plus a
dont-enforcer plus an unrecorded may-space — with the record burned. gov-os is
the same machine with the record kept.

**Caps:** the inventory is exhaustive at concept level, not syscall level (the
~130-call map is doc 10's job); mappings are INFERRED extensions of the corpus
to the metal; the two live-check-heavy paths (fault check, gate admission) are
exactly where the falsification slice must measure cost.
