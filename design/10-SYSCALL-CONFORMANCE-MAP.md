<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Syscall Conformance Map & Standing Conformance-Test Spec

> **SUPERSESSION NOTE (2026-07-18 line-audit).** CURRENT — feeds Campaign 3 (DEPTH)
> unchanged. One residence delta: the syscall→op map and rule→errno table are now
> RECORDED vocabulary packs (`syscall-ops`, `rule-errno`, genesis-seeded since EP-02)
> with labeled code fallbacks — the CONTENT here stands; its residence moved into the
> record. Live canon (design/28 §3) controls on conflict.

**Status:** v0.1, 2026-07-12, high. **Route-A assumption** (hollow-out: gov-os
starts as Linux and replaces subsystems behind unchanged interfaces, per
`03-TARGET-STATE-ARCHITECTURE.md` §6–§7). This document is the item named "not
yet done" in 03 §8 — *the syscall-by-syscall conformance map*. It is a reference
map first and a permanent test spec second; both readings are intended.

> **Trained-knowledge flag (whole document):** the Linux system-call surface —
> names, signatures, semantics, errno behaviour, grouping — is **trained
> knowledge** (Estimate — High). It is the stable Linux ABI as documented in the
> man-pages (sections 2/3) and reproduced on non-Linux substrates (gVisor
> Sentry, Fuchsia Starnix). No live kernel source was read to build this map.
> The **recording-class assignments** in the fourth column are **INFERRED** —
> the owner's five-class rule (03 §2) applied call-by-call to the ABI; each is
> traceable to a subsystem derivation in 03 §4 (cited per row-group). Where a
> classification is a genuine judgement rather than a direct read of 03, it is
> flagged in the note.

---

## 1. What this document is (intro)

This document maps the major Linux system calls onto gov-os's governance
architecture and, in the same stroke, specifies the permanent conformance test
the ports contract demands. Section 5 of the target-state architecture names the
syscall surface as THE compatibility contract: a rebuilt subsystem passes iff
every syscall touching it behaves identically. This map is where "identically"
is written down, call by call. Each row states what the call does, which of the
five governed subsystems it touches, which recording class it exercises (LAW,
DECISION, INPUT, CACHE-only, or STREAM), and what semantic identity means for it
— including the subtleties where gov-os's ledger changes what is *recorded*
without changing what userland *observes*. Read as a test suite, every row is an
assertion: drive the call, observe the ABI-visible result, confirm it matches
Linux while the record captures exactly the class this map assigns. Divergence
in observable behaviour is a conformance failure; a missing or misclassified
record is an audit failure. The two failure modes are kept distinct on purpose.

---

## 2. How to read the columns (legend)

**Column 1 — syscall.** Canonical name(s). Grouped variants (e.g. `pread64`,
`preadv`) ride on the primary row where semantics match.

**Column 2 — what it does.** One plain line. The ABI contract, not the gov-os
mechanism.

**Column 3 — subsystem.** Which of the five governed departments (03 §4) the
call touches: **scheduling** (attention), **memory** (space), **files**
(custody of information), **devices** (capability), **comms** (messages).
`process` and `time` are noted as cross-cutting tags — process lifecycle is
governed jointly by scheduling+memory; time is the clock-as-sensor input feeding
scheduling. A call may touch more than one.

**Column 4 — recording class** (the load-bearing column; classes from 03 §2):

| Class | Meaning for a syscall | Audit consequence |
|---|---|---|
| **LAW** | The call amends a rule-of-rules: a policy, budget, permission, capability, mount, or disposition. | Recorded totally, with amendment authority. Rare, deliberate. |
| **DECISION** | The call changes law-derived state: a grant, a bind, an open, a send *event*, a revoke. | Recorded in full, citing the rule it applied. Never sampled. |
| **INPUT** | The call surfaces an externally-authored happening: a timer expiry, an arrival, an entropy draw. | The state-changing arrival is recorded; raw high-frequency content is sampled. |
| **CACHE-only** | The call reads (or trivially mutates) derived state: a current-state query, an offset move, an fd dup. | No record. Reconstructible from LAW+DECISIONS+INPUTS. A crash loses only this. |
| **STREAM** | The call is raw operation flow applying already-recorded policy: a per-tick dispatch, bulk I/O traffic. | Sampled and aggregated for observability/evidence. Never load-bearing. |

**Column 5 — conformance note.** What "behaves identically" means for this call,
and any semantic subtlety: where the record diverges from Linux internals while
the ABI result does not, where errno must match, where ordering is definitional
(03 §1.4), where a payload is full-fidelity despite the traffic being STREAM.

**Two standing subtleties, stated once so every row can lean on them:**

- **Full-fidelity payloads under STREAM traffic.** "STREAM" classifies the
  *audit aggregate*, never the bytes handed to the caller. A `read`/`recv` that
  the audit view samples still returns exact bytes to userland; file *write*
  content is DECISION-class and never sampled (03 §4.3 `[AUDIT-FIX 4]`). Sampling
  is an observability property, not a data-path property.
- **Shared-memory boundary (03 §4.5 `[AUDIT-FIX 5]`).** For `shm*` and
  `mmap(MAP_SHARED)` the **grant is a recorded DECISION** (who may share which
  region with whom, under what rule); the **interior writes are not audited** —
  they are the applications' own activity, like private thoughts the record does
  not reach. Races *inside* userland's shared region stay userland's business.

---

## 3. How this doubles as the conformance test suite

Each row is a test assertion with three independent checks. A subsystem's
governed rebuild (03 §6 shadow phase) is conformant on a call only when all
three hold:

1. **ABI identity (the port contract, 03 §5).** Same return value, same errno
   set, same visible ordering guarantees, same side-effect on process-visible
   state. Timing and `/proc` *values* are explicitly NOT promised identical —
   `/proc` reflects gov-os's true derived state (03 §5 note).
2. **Recording-class fidelity (the audit contract, 03 §1).** The call produces
   exactly the record this map assigns — a DECISION-class call emits a recorded,
   rule-citing decision; a CACHE-only call emits none; an INPUT-class arrival
   enters the intake pipeline. A missing decision, or a decision without a cited
   rule, fails the audit check even if the ABI check passes.
3. **Replay invariance (03 §1.3).** Re-deriving the subsystem's caches from
   (LAW, DECISIONS, INPUTS) reproduces the post-call state identically. This is
   the shadow-diff = ∅ test of 03 §6, evaluated per call.

The map is versioned as the contract: adding a syscall, or reclassifying one,
is an amendment with authority — the spec is itself governed data.

---

## 4. Process, scheduling & lifecycle

**Subsystem derivation:** 03 §4.1 (scheduling — governing attention). LAW =
scheduling policy records; DECISIONS = admit/block/wake/halt/kill; INPUTS =
timer ticks and wake-causing events; CACHE = the runnable set; STREAM = per-tick
dispatch aggregates. Process creation also touches memory (03 §4.2) via the new
address space. Class assignments below: **INFERRED** from §4.1 applied to the ABI.

| syscall | what it does | subsystem | recording class | conformance note |
|---|---|---|---|---|
| `fork` | Create a child process (COW copy of the caller). | scheduling + memory + process | **DECISION** | Admit-a-process decision: recorded, cites the budget/permission rule that admitted it. Returns child PID to parent, 0 to child — identical. `EAGAIN`/`ENOMEM` must match on budget/RLIMIT exhaustion (the budget is LAW). |
| `vfork` | Fork sharing the address space until `execve`/`exit`. | scheduling + memory + process | **DECISION** | Same admit decision plus a recorded shared-space grant (the parent's suspension is a scheduling decision). ABI: parent blocks until child execs/exits — identical. |
| `clone`, `clone3` | Create a process/thread with explicit sharing flags. | scheduling + memory + process | **DECISION** | Admit decision records the CLONE_* sharing set (VM/FILES/SIGHAND) as the grant's terms. Threads = a share-everything grant. TID/CLONE_SETTLS semantics identical. |
| `execve`, `execveat` | Replace the process image from a file. | process + memory + files | **DECISION** | A governed re-image: permission check on the binary (files subsystem open), new memory grants recorded, old mappings revoked. `ENOEXEC`/`EACCES`/`ETXTBSY` must match. The exec point is a natural decision boundary. |
| `exit`, `exit_group` | Terminate the calling thread / whole process. | scheduling + memory + process | **DECISION** | Halt decision: the actor leaves the runnable set; its grants (memory, fds, locks) are released as recorded revocations. Exit status becomes readable derived state (see `wait4`). |
| `wait4`, `waitpid`, `waitid` | Wait for and reap a child's state change. | scheduling + process | **CACHE-only** read (+ block/wake **DECISION**; reap = release **DECISION**) | Blocking is a recorded scheduling decision; the child's exit was already a recorded DECISION; this call *reads* that derived status (CACHE). The zombie reap is a recorded release. `WNOHANG`, `ECHILD`, status-macro encoding identical. |
| `kill`, `tkill`, `tgkill` | Send a signal to a process/thread. | comms + process | **DECISION** | Governed delivery: permission checked (may this actor signal that target?), recorded, rule-cited. `EPERM`/`ESRCH` must match. Signal *number* semantics unchanged. |
| `pidfd_send_signal` | Send a signal via a pidfd (race-free target). | comms + process | **DECISION** | As `kill`; the pidfd removes PID-reuse races — recorded delivery cites the same permission rule. |
| `pidfd_open` | Open a stable handle to a process. | process | **CACHE-only** | Creates a derived reference to an existing admitted process; no new grant. `ESRCH` on dead PID identical. |
| `sched_setscheduler`, `sched_setparam` | Set a task's scheduling policy/priority. | scheduling | **LAW** | The clearest LAW case: policy is a rule-of-rules. Recorded as a policy amendment with authority. `EINVAL`/`EPERM` on invalid class or unprivileged raise identical. |
| `sched_getscheduler`, `sched_getparam` | Read a task's policy/priority. | scheduling | **CACHE-only** read | Reads current LAW-derived state; no record. Returned values identical. |
| `sched_setaffinity` | Pin a task to a CPU set. | scheduling | **LAW** | Affinity is placement policy — recorded amendment. `EINVAL` on empty mask identical. |
| `sched_getaffinity` | Read a task's CPU mask. | scheduling | **CACHE-only** read | Pure query. |
| `sched_yield` | Yield the CPU to the run-queue. | scheduling | **STREAM** | Canonical STREAM call: applies already-recorded policy, produces a per-tick dispatch, changes no law. Sampled in aggregate, never individually recorded. Always returns 0 — identical. |
| `nice`, `setpriority` | Adjust the nice value of a process/group/user. | scheduling | **LAW** | Nice is priority policy — recorded amendment. `getpriority` counterpart is CACHE-only. `EACCES`/`EPERM` on raising priority identical. |
| `getpriority` | Read the nice value. | scheduling | **CACHE-only** read | Query only. |
| `sched_getcpu` | Which CPU is the caller on. | scheduling | **CACHE-only** read | Reads derived placement. |
| `sched_rr_get_interval` | Read the RR timeslice for a policy. | scheduling | **CACHE-only** read | Reads LAW-derived value. |
| `getpid`, `getppid`, `gettid` | Return caller / parent / thread identifiers. | process | **CACHE-only** read | Pure derived-state read. Values identical; PID namespace semantics preserved. |
| `getpgid`, `getsid` | Read process-group / session id. | process | **CACHE-only** read | Query. |
| `setpgid`, `setsid` | Restructure process-group / session hierarchy. | process + scheduling | **DECISION** | Changes law-derived process structure — recorded. `EPERM`/`EACCES` on cross-session moves identical. |
| `getuid`, `geteuid`, `getgid`, `getegid`, `getgroups` | Read the caller's credentials. | process | **CACHE-only** read | Query. |
| `setuid`, `setgid`, `setresuid`, `setgroups` | Change the caller's credentials. | process | **DECISION** (amends permission LAW) | Credential change alters the actor's authority — recorded, cites the rule authorising the transition. `EPERM` on unprivileged raise identical; saved-set-id semantics preserved exactly. |
| `capget` | Read a process's capability set. | process | **CACHE-only** read | Query over capability LAW. |
| `capset` | Set a process's capability set. | devices + process | **LAW** | Capability is law (03 §4.4 pattern: the R14 amendment shape). Recorded amendment with authority. `EPERM` identical. |
| `prctl` | Miscellaneous per-process control ops. | process (varies) | **mixed** | Op-dependent: setters that change disposition/name/policy (e.g. PR_SET_DUMPABLE, PR_SET_NO_NEW_PRIVS) = DECISION/LAW recorded; queries (PR_GET_*) = CACHE-only. NO_NEW_PRIVS is a gate-restricting amendment (LAW). Each sub-op classified by effect. |
| `seccomp` | Install a syscall filter on the caller. | process + devices | **LAW** | Installs law *at the gate* (03 L1): restricts which registered operations exist for this actor. Recorded amendment, cites authority. Filter semantics and `SECCOMP_RET_*` identical. |
| `bpf` | Load / attach / query BPF programs and maps. | devices + process | **LAW** / **DECISION** | Attaching kernel-resident logic is a governed, authorized amendment (recorded); map lookups are CACHE reads. `EPERM`/`EACCES` identical. Heavily gated. |
| `ptrace` | Observe and control another process. | process | **DECISION** | A governed grant of control over another actor — permission-gated, recorded, rule-cited. `EPERM` under Yama/ptrace_scope identical; stop/continue semantics preserved. |
| `getrlimit`, `prlimit64` (get) | Read a resource limit. | memory/scheduling | **CACHE-only** read | Reads a budget (LAW-derived); no record. |
| `setrlimit`, `prlimit64` (set) | Set a resource limit. | memory/scheduling | **LAW** | Limits are budgets — the budgets-flow-down rule (03 §4.2). Recorded amendment with authority. `EPERM` on raising hard limit identical. |
| `personality` | Set the process execution domain. | process | **DECISION** (amends per-process policy) | Rarely used; recorded when it changes behaviour. ABI flags identical. |
| `set_tid_address`, `set_robust_list`, `get_robust_list` | Register thread-exit / robust-futex bookkeeping. | process + comms | **CACHE-only** | Per-thread derived bookkeeping; reconstructible. No governance decision. Used by the futex machinery (see §8). |

---

## 5. Memory

**Subsystem derivation:** 03 §4.2 (memory — governing space). LAW = allocation
policy + budgets; DECISIONS = mapping created / region granted / page evicted /
budget amended; INPUTS = faults as arrival events; CACHE = page tables and
free-lists; STREAM = raw accesses (hardware access/dirty bits stay ephemeral,
surfacing only as cited eviction evidence, 03 §2/§4.2 `[AUDIT-FIX 3]`).

| syscall | what it does | subsystem | recording class | conformance note |
|---|---|---|---|---|
| `brk`, `sbrk` | Move the program break (grow/shrink heap). | memory | **DECISION** | Region grant/release against the caller's budget — recorded. Returns new break / old break exactly; `ENOMEM` on budget exhaustion identical. |
| `mmap` (private/anon) | Map a region of memory. | memory (+ files if file-backed) | **DECISION** | Mapping-created grant: recorded, cites the budget rule. File-backed also touches files (open custody already granted via the fd). Address, `MAP_FIXED`, `PROT_*` semantics identical; `EACCES`/`ENOMEM`/`EINVAL` match. |
| `mmap` (`MAP_SHARED`) | Map a shared region (file or anon shared). | memory + comms | **DECISION** (grant) — interior writes **not audited** | The §4.5 canonical case: the **grant** (who shares which region with whom) is a recorded decision; the **interior writes are not audited** — userland's own activity. ABI unchanged; coherence/visibility semantics identical. |
| `munmap` | Unmap a region. | memory | **DECISION** | Mapping revoked — recorded release. Subsequent access faults (`SIGSEGV`) identically. |
| `mremap` | Resize / move a mapping. | memory | **DECISION** | Re-grant recorded (old revoked, new granted). `MREMAP_MAYMOVE`, returned address, `ENOMEM` identical. |
| `mprotect`, `pkey_mprotect` | Change protection on a region. | memory | **DECISION** (amends region permission) | A permission change on granted space — recorded, cites rule. Fault behaviour on violation (`SIGSEGV`) identical; `EACCES` on illegal transition matches. |
| `madvise` (advisory) | Advise the kernel on usage patterns. | memory | **STREAM** (hints) | Pure hints (MADV_WILLNEED/SEQUENTIAL/RANDOM) feed the eviction-evidence stream, change no law. Return 0 identical. |
| `madvise` (`MADV_DONTNEED`, `MADV_FREE`, `MADV_REMOVE`) | Release pages / punch holes. | memory | **DECISION** | These *change* resident state — recorded release (and, for REMOVE on shared file, a file content decision). Post-call zero-fill / re-fault semantics identical. |
| `mlock`, `mlock2`, `mlockall` | Pin pages resident. | memory | **DECISION** | A budget-affecting grant (pinned against the RLIMIT_MEMLOCK budget, which is LAW) — recorded, cites rule. `ENOMEM`/`EPERM` on the lock budget identical. |
| `munlock`, `munlockall` | Unpin pages. | memory | **DECISION** | Recorded release of the pin grant. |
| `msync` | Flush a mapped region to its backing file. | memory + files | **DECISION** | Writes file content — content is DECISION-class (03 §4.3); the flush records the write and its blob hash. `MS_SYNC`/`MS_ASYNC` ordering identical. |
| `mincore` | Query which pages are resident. | memory | **CACHE-only** read | Reads page-table-derived residency; no record. Byte-vector result identical. |
| `mbind`, `set_mempolicy` | Set NUMA allocation policy. | memory | **LAW** | Placement policy — recorded amendment. `get_mempolicy` counterpart is CACHE-only. |
| `get_mempolicy` | Read NUMA policy. | memory | **CACHE-only** read | Query. |
| `memfd_create` | Create an anonymous memory-backed file. | memory + files | **DECISION** | Creates a new file object (custody grant) — recorded. Sealing flags (`F_SEAL_*` via `fcntl`) are further recorded decisions. Often mapped `MAP_SHARED` for sharing — the share grant is that mmap's decision (§4.5). |
| `mmap` on device fd | Map device memory (e.g. framebuffer, DMA). | memory + devices | **DECISION** | Grant crosses the typed driver boundary (03 §4.4) — recorded bind of device memory into the address space. Subsequent accesses are device STREAM. |

---

## 6. Files & VFS

**Subsystem derivation:** 03 §4.3 (files — governing custody of information).
LAW = namespace, mount, and permission rules; DECISIONS = create / write / link
/ unlink / permission-change (and `open` itself — the custody grant); CACHE =
the directory tree and inode state; STREAM = read-traffic aggregates. **Content
is never STREAM** — every write's payload is full-fidelity to content-addressed
blobs, the event records the hash (03 §4.3 `[AUDIT-FIX 4]`).

| syscall | what it does | subsystem | recording class | conformance note |
|---|---|---|---|---|
| `open`, `openat`, `openat2` | Open (optionally create) a file; return an fd. | files | **DECISION** | The explicit custody grant of §4.3: permission checked, recorded, rule-cited. `O_CREAT` also records a create decision. The fd-table entry is CACHE. `O_EXCL`, `O_TRUNC`, `O_APPEND`, `O_NONBLOCK`, and the full errno set (`EACCES`/`EEXIST`/`ENOENT`/`EISDIR`) identical. |
| `creat` | Create-and-open (legacy `open` + O_CREAT|O_WRONLY|O_TRUNC). | files | **DECISION** | Create + custody grant recorded. Identical to the `open` equivalent. |
| `close` | Release an fd. | files | **DECISION** (lightweight release) | Symmetric release of the open custody — recorded (low-ceremony). The fd-table slot (CACHE) is dropped. Flush-on-close errors surfaced identically; `EBADF` matches. |
| `read`, `pread64`, `readv`, `preadv`, `preadv2` | Read bytes from an fd. | files | **STREAM** (audit) + **CACHE** (offset) | Read-traffic is sampled for the audit aggregate (§4.3), but the **caller receives exact bytes** — payload is full-fidelity. The offset advance is a CACHE mutation. Short reads, `EAGAIN`, `EINTR` semantics identical. |
| `write`, `pwrite64`, `writev`, `pwritev`, `pwritev2` | Write bytes to an fd. | files | **DECISION** | Content is DECISION-class, **never sampled** (§4.3 `[AUDIT-FIX 4]`): payload goes full-fidelity to a content-addressed blob, the write event records the hash. Event *granularity* may be coalesced under a recorded policy (many small writes → one recorded event citing that policy) — a named calibration, never a silent loss. Short writes, `ENOSPC`, `EDQUOT`, `O_APPEND` atomicity identical. |
| `lseek`, `llseek` | Reposition the fd offset. | files | **CACHE-only** | Canonical CACHE mutation: the offset is derived per-fd state, reconstructible, no governance decision. `SEEK_SET/CUR/END/DATA/HOLE`, `ESPIPE` on pipes identical. |
| `stat`, `lstat`, `fstat`, `fstatat`, `statx` | Read file metadata. | files | **CACHE-only** read | Reads derived inode/dentry state; no record. `statx` mask/attribute semantics identical; `/proc` metadata reflects gov-os's true derived state (03 §5 note). |
| `statfs`, `fstatfs` | Read filesystem-level statistics. | files | **CACHE-only** read | Derived aggregate; values reflect gov-os's true store. |
| `access`, `faccessat`, `faccessat2` | Check permission on a path. | files | **CACHE-only** read | Evaluates the permission rule (LAW) against current state — a pure query, no state change, no record. `R_OK/W_OK/X_OK`, `AT_EACCESS` semantics and errno identical. |
| `link`, `linkat` | Create a hard link (new name for existing inode). | files | **DECISION** | Namespace change — recorded. `EEXIST`/`EMLINK`/`EXDEV` identical. |
| `symlink`, `symlinkat` | Create a symbolic link. | files | **DECISION** | Namespace change — recorded (the link is content of a new inode). |
| `unlink`, `unlinkat` | Remove a name from the namespace. | files | **DECISION** | Records the *name removal*. Subtlety: content is content-addressed, so the blob's history persists in the ledger even when the last link drops — but the POSIX contract is exact (link count decremented; space reclaimed when last link gone AND no open fd holds it). `AT_REMOVEDIR`, `EISDIR`, `ENOTEMPTY` identical. |
| `rename`, `renameat`, `renameat2` | Atomically rename / move. | files | **DECISION** | Namespace change — recorded, atomic. `RENAME_NOREPLACE`/`RENAME_EXCHANGE` semantics and `EEXIST`/`ENOTEMPTY`/`EXDEV` identical. |
| `mkdir`, `mkdirat` | Create a directory. | files | **DECISION** | Namespace create — recorded. `EEXIST` identical. |
| `rmdir` | Remove an empty directory. | files | **DECISION** | Namespace removal — recorded. `ENOTEMPTY` identical. |
| `mknod`, `mknodat` | Create a special (device/FIFO) file. | files (+ devices) | **DECISION** | Create + (for device nodes) a capability reference — recorded. `EPERM` on unprivileged device-node creation identical. |
| `truncate`, `ftruncate` | Set a file's length. | files | **DECISION** | Changes content (grow = zero-fill, shrink = drop) — recorded against the content-addressed state. `EINVAL`/`EFBIG` identical. |
| `fallocate` | Preallocate / punch / zero file space. | files | **DECISION** | Space reservation/hole against the storage budget — recorded. `FALLOC_FL_*` modes and `ENOSPC` identical. |
| `chmod`, `fchmod`, `fchmodat` | Change file mode bits. | files | **DECISION** (amends file permission LAW) | The file's permission rule is amended — recorded, cites authority. `EPERM` on non-owner identical. |
| `chown`, `fchown`, `lchown`, `fchownat` | Change file ownership. | files | **DECISION** (amends permission LAW) | Ownership/permission amendment — recorded. Set-uid-bit-clear side effect and `EPERM` identical. |
| `utimensat`, `futimesat`, `utime` | Set file timestamps. | files | **DECISION** | Metadata mutation recorded; `UTIME_NOW`/`UTIME_OMIT` semantics identical. |
| `setxattr`, `getxattr`, `listxattr`, `removexattr` (+ f/l variants) | Manage extended attributes. | files | get/list = **CACHE-only** read; set/remove = **DECISION** | Attribute writes are recorded metadata decisions (some xattrs are permission-bearing, e.g. `security.*`, `system.posix_acl_*` — those amend permission LAW). ABI and errno identical. |
| `fsync`, `fdatasync` | Force prior writes durable. | files | **CACHE-only** (durability barrier over recorded writes) | Not a governance decision: the writes it commits were already DECISIONS. It is a barrier making the recorded+derived state durable on media. In gov-os the record IS the durability substrate; `fsync` returns after the covering write-decisions are durable. `EIO` on flush failure surfaced identically. |
| `sync`, `syncfs` | Flush all / filesystem buffers. | files | **CACHE-only** (barrier) | As `fsync`, system-/fs-wide. |
| `fcntl` | Per-fd control (flags, dup, locks, leases). | files (+ comms for locks) | **mixed** | `F_DUPFD`/`F_GETFD`/`F_SETFD`/`F_GETFL`/`F_SETFL` = CACHE (fd-table state). `F_GETLK` = CACHE read. `F_SETLK`/`F_SETLKW`/`F_OFD_SETLK` = **DECISION** (a lock grant — recorded, cites rule; a comms coordination event). `F_SETLEASE`/`F_NOTIFY` = DECISION. Blocking-lock wait is a scheduling block/wake. All errno (`EAGAIN`/`EDEADLK`) identical. |
| `flock` | Advisory whole-file lock. | files + comms | **DECISION** | Lock grant recorded. `LOCK_SH`/`LOCK_EX`/`LOCK_NB`, `EWOULDBLOCK` identical. |
| `dup`, `dup2`, `dup3` | Duplicate an fd. | files | **CACHE-only** | Adds an fd-table entry to the same open file description — pure cache, no new custody grant. `dup2` close-of-target and `dup3(O_CLOEXEC)` semantics identical. |
| `getdents`, `getdents64` | Read directory entries. | files | **CACHE-only** read (read-traffic) | Reads the dentry-cache-derived listing; no record. On `/proc` it reads a computed view (§10). Entry order and `d_type` semantics identical. |
| `readlink`, `readlinkat` | Read a symlink target. | files | **CACHE-only** read | Query. |
| `chdir`, `fchdir` | Change the working directory. | files + process | **CACHE-only** | Per-process cwd is derived state — a cache field mutation; no governance decision. `ENOTDIR`/`EACCES` identical. |
| `getcwd` | Read the working directory. | files + process | **CACHE-only** read | Query. |
| `chroot` | Change the process's root directory. | files | **CACHE-only** (the lookup) [RECLASSIFIED 2026-07-27 per §11.1f; this row read **DECISION** — "Recorded confinement decision, cites rule" — until the first governed mount showed no filesystem is ever offered the operation] | `chroot(2)` changes a PROCESS attribute. A filesystem is consulted for the path lookup and never for the root change, and no FUSE filesystem receives it, so a row asserting a filesystem record here can never be satisfied by a correct mount. The lookup is the files-group involvement and it is CACHE. Governance of a process's root re-enters the map with the subsystem that governs process attributes. Refutation condition: if any filesystem interface does receive a root-change notification, this row belongs back in files as DECISION. |
| `umask` | Set the file-creation mode mask. | files + process | **CACHE-only** | Per-process attribute affecting future create decisions; itself derived state. Returns previous mask identically. |
| `mount`, `move_mount`, `fsopen`/`fsconfig`/`fsmount` | Attach a filesystem / configure a new mount. | files | **LAW** | Mount rules are LAW (§4.3/§4.4) — a recorded, authorized amendment to the namespace. `MS_*` flags, `EBUSY`/`EPERM` identical. |
| `umount`, `umount2` | Detach a filesystem. | files | **LAW** | Recorded amendment. `MNT_FORCE`/`MNT_DETACH`, `EBUSY` identical. |
| `pivot_root` | Swap the root mount. | files | **LAW** | Recorded namespace amendment. |
| `copy_file_range` | Copy a range between two files in-kernel. | files | **DECISION** (destination write) | Destination content recorded (content-addressed; may be a cheap blob-reference clone). Source read is STREAM. Short-copy semantics identical. |
| `sendfile` | Copy from a file fd to another fd. | files (+ comms if dst is a socket) | **DECISION** / **STREAM** | If destination is a file: a recorded write decision. If a socket: a comms send (DECISION event + STREAM payload). Offset advance and short-transfer semantics identical. |
| `splice`, `tee`, `vmsplice` | Move data between fds / pipe buffers with zero copy. | files + comms | **STREAM** (+ **DECISION** at a recorded endpoint) | Bulk movement is STREAM traffic; where an endpoint is a durable write or a socket send, that endpoint records its decision. `SPLICE_F_*` and short-move semantics identical. |
| `mount_setattr`, `open_tree` | Adjust mount attributes / clone a mount tree. | files | **LAW** | Mount-rule amendments — recorded. |

---

## 7. Devices & I/O multiplexing

**Subsystem derivation:** 03 §4.4 (devices — governing capability). LAW = device
registration as amendments (capability is law); DECISIONS = bind / unbind /
grant; INPUTS = interrupts and completions as arrival events; CACHE = the live
binding table; STREAM = I/O throughput aggregates. Driver calls cross a
validated, typed boundary. Readiness multiplexing (`epoll`/`poll`/`select`) is
grouped here because it surfaces device/socket INPUT arrivals.

| syscall | what it does | subsystem | recording class | conformance note |
|---|---|---|---|---|
| `ioctl` | Device- or fs-specific control operation. | devices (+ files) | **mixed** | Query ioctls (read state, capabilities) = CACHE-only read. Command ioctls (configure, bind, reset, submit) = **DECISION** crossing the typed driver envelope (§4.4) — recorded, cites the device's capability rule. Terminal `TCGET/SET`, block `BLK*`, etc. Per-driver errno (`ENOTTY`/`EINVAL`) identical. The op number determines the class. |
| `read`/`write` on a device fd | I/O against a device. | devices | **STREAM** (traffic) | I/O throughput is STREAM (§4.4); the payload delivered to/from userland is full-fidelity. The device *bind* (open/ioctl) was the recorded DECISION. Blocking/`O_NONBLOCK`/`EAGAIN` semantics identical. |
| `epoll_create`, `epoll_create1` | Create an epoll (readiness-watch) instance. | devices + scheduling | **CACHE-only** | Creates a derived readiness/observability structure (the interest set is CACHE); no resource grant. Returns an fd identically; `EPOLL_CLOEXEC` honoured. |
| `epoll_ctl` | Add / modify / remove an interest. | devices + scheduling | **CACHE-only** | Mutates the interest set (derived state). `EPOLL_CTL_ADD/MOD/DEL`, `EEXIST`/`ENOENT` identical. |
| `epoll_wait`, `epoll_pwait`, `epoll_pwait2` | Wait for ready fds. | devices + scheduling | **INPUT** (readiness arrivals) + block/wake **DECISION** | Readiness originates as INPUT arrivals (I/O completions, packet arrivals — recorded as inputs); blocking is a recorded scheduling decision. The returned ready-set is a derived read. Level/edge-trigger (`EPOLLET`), timeout, `EINTR` semantics identical. |
| `poll`, `ppoll` | Wait on a set of fds for events. | devices + scheduling | **INPUT** + block/wake **DECISION** | As `epoll_wait`; readiness arrivals are inputs, the wait is a scheduling decision. `POLLIN/OUT/ERR/HUP`, timeout, `ppoll` sigmask semantics identical. |
| `select`, `pselect6` | Wait on read/write/except fd sets. | devices + scheduling | **INPUT** + block/wake **DECISION** | As `poll`. `FD_SETSIZE` limit, timeout residue update, `pselect` sigmask semantics identical. |
| `io_uring_setup` | Create an async I/O submission/completion ring. | devices + comms + memory | **DECISION** (shared-ring grant) | The SQ/CQ rings are a shared-memory grant between userland and kernel — recorded like a `MAP_SHARED` grant (§4.5). Ring sizing/params identical. |
| `io_uring_register` | Register buffers/files with a ring. | devices | **DECISION** | Registers resources into the ring's capability set — recorded grant. |
| `io_uring_enter` | Submit / reap ring I/O. | devices | **STREAM** (traffic) + **DECISION** at durable endpoints | Bulk SQE/CQE flow is STREAM (interior ring activity, like §4.5); individual operations that are durable writes / socket sends record their endpoint decision. Completion semantics identical. |
| `aio_read`/`aio_write`, `io_submit`, `io_getevents` (libaio/kaio) | POSIX/kernel async I/O. | devices + files | **DECISION** (at durable endpoints) + **INPUT** (completions) | Submissions of durable writes record their decision; completions arrive as recorded inputs. Ordering/`errno` per submitted op identical. |
| `eventfd`, `eventfd2` | Create an event-counter fd for signalling. | comms + devices | **DECISION** (channel open) + **STREAM** (counter traffic) | Channel-open recorded; the counter increments/reads are STREAM signalling. `EFD_SEMAPHORE`/`EFD_NONBLOCK` semantics identical. |
| `signalfd`, `signalfd4` | Deliver signals via a readable fd. | devices + comms | **CACHE-only** (delivery structure) + **INPUT** (signal arrivals) | Creates a derived signal-delivery fd; signals arrive as recorded inputs and are read out. `siginfo` layout identical. |
| `inotify_init`, `inotify_init1`, `inotify_add_watch`, `inotify_rm_watch` | Watch filesystem events. | devices + files | init/add = **CACHE-only** (watch structures); events = **INPUT** | Watch structures are derived; filesystem-change events (themselves DECISIONS in the files subsystem) surface here as readable inputs. Event mask/coalescing semantics identical. |
| `fanotify_init`, `fanotify_mark` | Filesystem-wide access notification / permission gating. | devices + files | init/mark = **LAW/DECISION**; permission events = **DECISION** | Permission-gating marks install access rules (LAW-adjacent); permission responses are recorded decisions. Notification-only marks = CACHE. ABI identical. |
| `perf_event_open` | Open a performance-monitoring counter. | devices | **CACHE-only** (observability) | Counters are STREAM/observability instrumentation — creating one is a derived structure, honest-boundary sampling (03 §1.5). ABI/`ioctl` control identical. |

---

## 8. IPC & communication

**Subsystem derivation:** 03 §4.5 (communication — governing messages). LAW =
message-contract and queue rules; DECISIONS = channel open/close and send/receive
*events* (payload full or hash-referenced per recorded policy); CACHE = queue
state; STREAM = high-volume payload traffic under the recorded coalescing policy.
**Kernel-internal state is shared-nothing** — the record is the only shared
medium inside the kernel. **Userland shared memory is honoured at the port**: the
grant is recorded, the interior writes are not audited (`[AUDIT-FIX 5]`).

| syscall | what it does | subsystem | recording class | conformance note |
|---|---|---|---|---|
| `pipe`, `pipe2` | Create an anonymous pipe (read + write fd). | comms | **DECISION** (channel open) | Channel-open event recorded. Buffer capacity, `O_NONBLOCK`/`O_DIRECT`, `SIGPIPE`/`EPIPE`, atomic-write ≤ PIPE_BUF semantics identical. |
| `socket` | Create a communication endpoint. | comms | **DECISION** (channel open) | Endpoint creation recorded as a channel-open. Domain/type/protocol, `O_NONBLOCK`/`SOCK_CLOEXEC` semantics identical. |
| `socketpair` | Create a connected pair of sockets. | comms | **DECISION** (channel open) | Both endpoints + their connection recorded. |
| `bind` | Assign a local address/port to a socket. | comms | **DECISION** | A governed claim on a name (address/port) — recorded, cites the rule allowing it. `EADDRINUSE`/`EACCES` on privileged ports identical. |
| `listen` | Mark a socket passive (accept queue). | comms | **DECISION** (channel role change) | Recorded role change; backlog semantics identical. |
| `accept`, `accept4` | Accept an incoming connection. | comms | **INPUT** (connection arrival) + **DECISION** (channel open) | The connection request arrives as an input; accepting opens a new recorded channel. Blocking is a scheduling decision. `EAGAIN`/`ECONNABORTED`, `SOCK_NONBLOCK` semantics identical. |
| `connect` | Initiate a connection to a peer. | comms | **DECISION** (channel open) | Channel-open recorded, cites reachability/permission rule. Non-blocking `EINPROGRESS`, `ECONNREFUSED`/`ETIMEDOUT` semantics identical. |
| `send`, `sendto`, `sendmsg`, `sendmmsg` | Send data on a socket. | comms | **DECISION** (send *event*) + **STREAM** (payload aggregate) | The send *event* is recorded (payload full or hash-referenced per the recorded coalescing policy, as with files); high-volume payload is STREAM. **Peer receives exact bytes** — full-fidelity. `MSG_*` flags, `EPIPE`/`EMSGSIZE`, ancillary data (SCM_RIGHTS fd-passing — itself a recorded custody transfer) semantics identical. |
| `recv`, `recvfrom`, `recvmsg`, `recvmmsg` | Receive data from a socket. | comms | **INPUT** (data arrival) + **DECISION** (receive event) + **STREAM** (payload) | Arrival recorded as input; the receive event recorded; payload delivered full-fidelity. `MSG_PEEK`/`MSG_WAITALL`/`MSG_TRUNC`, `EAGAIN` semantics identical. |
| `shutdown` | Close one or both directions of a socket. | comms | **DECISION** (channel close/half-close) | Recorded. `SHUT_RD/WR/RDWR` semantics identical. |
| `getsockopt` | Read a socket option. | comms | **CACHE-only** read | Query. |
| `setsockopt` | Set a socket option. | comms | **DECISION** / **CACHE** | Options that change the channel contract (SO_REUSEADDR, SO_BINDTODEVICE, membership) = recorded decision; buffer-size/timeout tuning = CACHE. ABI/`errno` identical. |
| `getsockname`, `getpeername` | Read local / peer address. | comms | **CACHE-only** read | Query. |
| `shmget` | Get / create a SysV shared-memory segment. | comms + memory | **DECISION** (the grant) | The §4.5 grant: who may share which region, under what rule — recorded, rule-cited. `IPC_CREAT`/`IPC_EXCL`, `EEXIST`/`ENOSPC` identical. |
| `shmat` | Attach a shared segment into the address space. | comms + memory | **DECISION** (attach grant) — interior writes **not audited** | Attach grant recorded; **interior writes to the segment are not audited** (§4.5) — the application's own activity. `SHM_RDONLY`/`SHM_RND` semantics identical. |
| `shmdt` | Detach a shared segment. | comms + memory | **DECISION** (revoke) | Recorded release of the attach grant. |
| `shmctl` | Control a shared segment (stat / RMID / lock). | comms + memory | **DECISION/LAW** (lifecycle) + **CACHE** (IPC_STAT) | IPC_RMID/SET = recorded lifecycle decision; IPC_STAT = CACHE read. Lazy-destroy-until-last-detach semantics identical. |
| `semget`, `semctl` | Get / control a SysV semaphore set. | comms | **DECISION/LAW** | Set creation and control = recorded grant/config. `IPC_STAT` = CACHE read. |
| `semop`, `semtimedop` | Operate on semaphores (P/V). | comms + scheduling | **STREAM** (+ block/wake **DECISION**) | Per-op synchronization applying an already-granted contract — high-frequency STREAM; blocking-wait is a scheduling decision. `SEM_UNDO`, `EAGAIN`/`EIDRM` semantics identical. |
| `msgget`, `msgctl` | Get / control a SysV message queue. | comms | **DECISION/LAW** (channel open/config) | Queue creation/control recorded. `IPC_STAT` = CACHE read. |
| `msgsnd`, `msgrcv` | Send / receive on a SysV message queue. | comms | **DECISION** (event) + **STREAM** (payload) | As sockets: event recorded, payload full or hash-referenced; blocking is scheduling. `IPC_NOWAIT`, message-type selection, `E2BIG`/`EAGAIN` semantics identical. |
| `mq_open`, `mq_unlink` | Open / remove a POSIX message queue. | comms | **DECISION** (channel open/close) | Recorded. Named-queue namespace, `O_CREAT`/`O_EXCL` semantics identical. |
| `mq_timedsend`, `mq_timedreceive` | Send / receive on a POSIX message queue. | comms + scheduling | **DECISION** (event) + **STREAM** (payload) | Event recorded, payload per policy; priority ordering and timeout semantics identical. |
| `mq_notify` | Register async notification on a queue. | comms | **DECISION** | Registration recorded; delivery is an INPUT arrival. |
| `futex`, `futex_waitv` | Fast userspace mutex — wait / wake on a userland word. | comms + scheduling | block/wake **DECISION**; the contended word's ops **not audited** | The nuanced §4.5 case: the futex word lives in userland (often shared) memory, so its atomic mutations are **interior shared-memory activity — not audited**. gov-os records only the kernel-side block/wake scheduling decisions (high-frequency wait/wake in aggregate is STREAM). `FUTEX_WAIT/WAKE/REQUEUE/PI`, `EAGAIN`/`ETIMEDOUT`, robust-list cleanup semantics identical. |
| `eventfd` (as IPC) | Lightweight cross-process/thread signalling counter. | comms | **DECISION** (open) + **STREAM** (counter) | See §7; listed here as an IPC primitive. |
| `pidfd_getfd` | Duplicate an fd out of another process. | comms + process | **DECISION** (custody transfer) | Moving a custody grant across processes — recorded, permission-gated. `EPERM` identical. |
| `process_vm_readv`, `process_vm_writev` | Read/write another process's memory directly. | comms + memory | **DECISION** (cross-process access grant) | A governed cross-actor memory access — permission-gated, recorded. `EPERM`/`ESRCH`/`EFAULT` semantics identical. |

---

## 9. Time & signals

**Subsystem derivation:** 03 §4.1 (scheduling) + the clock-as-sensor ruling
(`00-READ-FIRST.md` §4, 03 §2 INPUT class). Timer ticks and expiries are INPUTS;
a schedule is a recorded rule and its firing a recorded activity (the settled
"scheduled execution" derivation). Signal *disposition* is per-process policy;
signal *delivery* is a comms decision.

| syscall | what it does | subsystem | recording class | conformance note |
|---|---|---|---|---|
| `clock_gettime`, `gettimeofday`, `time`, `clock_getres` | Read a clock / its resolution. | time | **CACHE-only** read (sensor read) | Reading the clock is reading a sensor value — no record (the clock-as-sensor ruling). Timer *ticks* enter the record as INPUTS; *reading* the time does not. `CLOCK_MONOTONIC/REALTIME/BOOTTIME`, vDSO fast-path semantics identical. |
| `clock_settime`, `settimeofday`, `adjtimex`, `clock_adjtime` | Set / discipline the system clock. | time | **LAW/DECISION** | Changing the authoritative time base is a governed, recorded decision citing authority (the time base is significant to ordering). `EPERM` on unprivileged, `EINVAL` on bad value identical. |
| `nanosleep`, `clock_nanosleep` | Sleep for a duration / until an absolute time. | scheduling + time | block/wake **DECISION** + **INPUT** (timer expiry) | The sleep is a recorded scheduling decision ("wake at T", a scheduled rule); the timer expiry is a recorded input that wakes it. `TIMER_ABSTIME`, remaining-time on `EINTR` semantics identical. |
| `timer_create`, `timer_settime`, `timer_gettime`, `timer_delete`, `timer_getoverrun` | POSIX per-process interval timers. | time + scheduling | create/settime = **DECISION** (scheduled rule); expiry = **INPUT**; gettime/overrun = **CACHE** read | Arming a timer records a scheduled rule ("fire at/every T"); expiry arrives as a recorded input delivered as a signal or via sigevent. Overrun counting semantics identical. |
| `getitimer`, `setitimer` | Legacy interval timers (REAL/VIRTUAL/PROF). | time + scheduling | set = **DECISION** (scheduled rule); get = **CACHE** read; expiry = **INPUT** | As POSIX timers. Delivered signals (SIGALRM/VTALRM/PROF) semantics identical. |
| `alarm` | Schedule a one-shot SIGALRM. | time + scheduling | **DECISION** (scheduled rule) + **INPUT** (expiry) | Records the scheduled rule; returns seconds remaining on the previous alarm identically. |
| `timerfd_create`, `timerfd_settime`, `timerfd_gettime` | Timers delivered via a readable fd. | time + scheduling + devices | create = **CACHE** (delivery fd); settime = **DECISION** (scheduled rule); expiry = **INPUT** | Arming records the scheduled rule; expiries arrive as recorded inputs readable as an 8-byte count. `TFD_TIMER_ABSTIME`, `CLOCK_*` semantics identical. |
| `rt_sigaction`, `sigaction` | Install a signal handler / disposition. | process + comms | **DECISION** (amends signal-disposition policy) | The per-process rule for handling signal N is amended — recorded. `SA_RESTART`/`SA_SIGINFO`/`SA_NODEFER`, `siginfo` semantics identical. |
| `rt_sigprocmask`, `sigprocmask` | Block / unblock signals (change the mask). | process + comms | **DECISION** (disposition change) — coalescible | Changes which signals are deliverable — a recorded disposition change. Note: trivial save/restore mask toggles (common in libc) may be coalesced under the recorded coalescing policy, parallel to write-coalescing (03 §4.3); never a silent loss. `SIG_BLOCK/UNBLOCK/SETMASK` semantics identical. |
| `rt_sigpending`, `sigpending` | Query pending (blocked) signals. | process | **CACHE-only** read | Query. |
| `rt_sigsuspend`, `sigsuspend` | Atomically set a mask and wait for a signal. | scheduling + comms | block/wake **DECISION** + **INPUT** (signal arrival) | The wait is a scheduling decision; signal delivery is a recorded comms input. Always returns `-EINTR` after the handler — identical. |
| `rt_sigtimedwait`, `sigtimedwait`, `sigwaitinfo` | Synchronously wait for a signal. | scheduling + comms | block/wake **DECISION** + **INPUT** | As above with a timeout; `siginfo` return semantics identical. |
| `pause` | Sleep until any signal is delivered. | scheduling + comms | block/wake **DECISION** + **INPUT** | Wait is a scheduling decision; delivery an input. Always `-EINTR` — identical. |
| `sigaltstack` | Set an alternate signal-handler stack. | process | **CACHE-only** | Per-process attribute; derived state. `SS_DISABLE`/`SS_ONSTACK`, `ENOMEM` on too-small identical. |
| `rt_sigreturn` | Return from a signal handler (context restore). | process | **CACHE-only** (mechanism) | Internal trampoline — restores saved context; not a governance event, no record. Never called directly by application code. |
| `restart_syscall` | Kernel-internal restart of an interrupted call. | scheduling | **CACHE-only** (mechanism) | Internal; no record. Transparent to userland. |

---

## 10. Information & pseudo-filesystems

**Subsystem derivation:** 03 §5 (the ports — pseudo-filesystem surface). `/proc`
and `/sys` are rendered as what they always morally were — computed views, now
honestly derived from the record. Reads of these are CACHE-only reads over a
computed view; their *values* reflect gov-os's true derived state (03 §5 note),
so byte-for-byte equality of dynamic fields is NOT promised — shape and schema
are.

| syscall | what it does | subsystem | recording class | conformance note |
|---|---|---|---|---|
| `uname` | Report kernel name / release / version / machine. | (info) | **CACHE-only** read | Computed identity view. `sysname`/`release` fields report gov-os's true identity (a governed kernel), while the ABI struct shape is identical. Programs that gate on version strings see gov-os's honest values (03 §5). |
| `sysinfo` | Report memory / load / uptime aggregates. | (info) | **CACHE-only** read | Derived aggregates over recorded state + STREAM samples. Struct shape identical; values are gov-os's true derived state (some fields are honest-boundary observability, 03 §1.5). |
| `getrusage` | Report resource usage of self / children. | (info) | **CACHE-only** read | Derived from recorded decisions plus STREAM-sampled counters — CPU-time and fault fields are observability (honest boundary, 03 §1.5), not audit. Struct/`RUSAGE_*` semantics identical. |
| `times` | Report process/children CPU times. | (info) + scheduling | **CACHE-only** read | Derived; tick semantics identical. |
| `getdents`/`read` on `/proc` | Enumerate processes / read `/proc/<pid>/*`. | files (pseudo) | **CACHE-only** read (computed view) | The process list and per-process files are computed views over the record (03 §5) — no record produced by reading them. Schema/field layout identical; dynamic values are gov-os's true state. |
| `readlink /proc/self/{exe,fd/N,cwd,root}` | Resolve process-introspection symlinks. | files (pseudo) | **CACHE-only** read | Computed view; target strings identical in form. |
| `read`/`write` on `/proc/sys/*`, `sysctl` (legacy) | Read / set kernel tunables. | files (pseudo) + LAW | read = **CACHE-only**; write = **LAW** | Tunables ARE law: writing one is a recorded amendment with authority (the legacy `sysctl` syscall is deprecated; the `/proc/sys` path is the live surface). Read shape and `EPERM` on protected keys identical. |
| `getrandom` | Fill a buffer with random bytes. | (info) + devices | **INPUT** (entropy draw) | Clean INPUT case: entropy is external nondeterminism, entering the record as an input event (03 §2). This makes the draw *replayable relative to the recorded input stream* (03 §1.3) — determinism conditioned on the entropy being recorded, never "free." `GRND_NONBLOCK`/`GRND_RANDOM`, `EAGAIN` before pool init, blocking semantics identical. |
| `sysfs` (legacy), `ustat` | Legacy filesystem-info calls. | files (pseudo) | **CACHE-only** read | Rarely used; computed view. |
| `syslog` (klogctl) | Read / control the kernel log ring buffer. | (info) + devices | read = **CACHE-only**; control = **DECISION** | The kernel log is observability; reading it is a view read, control ops (clear, console-level) are recorded decisions. `EPERM` on privileged actions identical. |
| `membarrier` | Issue a process-wide memory barrier. | memory + scheduling | **STREAM** (mechanism) | Applies already-recorded ordering guarantees across cores; a per-op mechanism, not a governance change. `MEMBARRIER_CMD_*` registration/expedited semantics identical. |

---

## 11. Cross-cutting conformance rules (apply to every row)

These hold across all groups and are part of the standing test, so individual
rows do not repeat them:

1. **errno identity is load-bearing.** A conformant call returns the *same errno*
   Linux returns for the same precondition. A gov-os refusal is additionally a
   recorded, rule-citing decision (03 §1.2) — but the errno the caller sees is
   the Linux errno, not a governance code. "A denial cites errno to userland and
   a rule to the record" (03 §0, inverted): the record explains; the ABI stays
   silent in the old vocabulary.

2. **Ordering is definitional where hardware races (03 §1.4, §4.1).** For calls
   whose observable result depends on inter-core order (e.g. two `write`s to the
   same file, two `bind`s to the same port, competing `accept`s), the visible
   ordering guarantee Linux makes is preserved; internally the intake pipeline's
   recorded order *settles* the race rather than describing it. Conformance
   checks the guarantee POSIX makes, not the nanosecond physics.

3. **`/proc` and version values reflect gov-os's true state (03 §5).** Tests that
   assert byte-equality of dynamic `/proc` fields or kernel version strings
   against a Linux baseline are audit-incorrect: shape/schema identity is the
   contract, value honesty is the design.

4. **Coalescing is a named calibration, never a silent loss (03 §4.3).** Where
   event granularity is folded (small writes, mask toggles, high-frequency
   sends), the folding cites a recorded policy with a named owner. A test may
   assert that the *policy exists and is cited*, not that every micro-event has
   its own record.

5. **Payload fidelity is independent of STREAM classification.** No test may
   infer, from a call being STREAM-classified for audit, that its data path is
   lossy. File-write content is DECISION-class and full-fidelity; read/recv
   payloads are delivered exactly; only the *aggregate observability view* is
   sampled.

6. **Timing is explicitly out of contract (03 §5).** No conformance assertion
   depends on latency or throughput matching Linux. Only functional/semantic
   identity is tested.

---

### 11.1b — Prescriptive content is LAW-class, whichever syscall carries it [added 2026-07-26, resolving EP-24's files-group DISPUTED row]

EP-24 encoded the `setxattr` row as the map wrote it — get/list CACHE, set/remove
DECISION — and raised the sub-case the note names without deciding: the map says
`security.*` and `system.posix_acl_*` writes "amend permission LAW" and does not
say whether those writes are LAW-class or DECISION-class records. Encoding the
words and raising the gap was correct. The gap is resolved here, at the level
where it recurs rather than at the row.

**The rule.** A write whose CONTENT IS PRESCRIPTIVE — it changes what is
permitted rather than what is stored — is a LAW record, whichever syscall
carries it. The syscall is transport; the content decides the class. A POSIX ACL
or a security attribute is a rule with a one-file scope, so setting one is
law-making and records as LAW; every other extended-attribute write records as
DECISION; get and list stay CACHE. The row therefore splits by attribute
NAMESPACE as well as by operation.

**Why this and not the two alternatives.** Treating an ACL as ordinary stored
data and letting grants alone answer permission diverges at the ports: a caller
that sets a denying ACL and is then allowed because a grant covers it has been
given a different answer than Linux would give, and K2 is the promise that does
not happen. Consulting the ACL as a side input to the gate puts permission in a
stored table on the filesystem, which is the refused reference arriving through
a path nobody guarded. Recording it as law does neither: the ACL is not a stored
answer, it is a recorded rule with a narrow scope, and the complement is computed
by the same fold as always. The estate already carries space-scoped rules; a
file-scoped rule is the same shape one level down. design/24 reached the same
conclusion for the device boundary, where driver registration is LAW.

**The consequences, stated because they follow rather than because they are
chosen.** A permission-bearing metadata write requires law-making authority in
that scope, not ordinary write authority. It is subject to tier conservation and
the protected-core floor like any law. And it is a law-family record, so it
participates in the two-times regime: an ACL change whose deciding time precedes
recorded accesses reaches them through the reconciliation sweep, and reads
already served surface on the exposure view with the remedy left to judgment
(design/36 §4b.6). None of that is new machinery; it is the existing machinery
declining to make an exception for a syscall.

### 11.2b — An instrument establishes its subject, and cannot corrupt it [added 2026-07-27, from three instances in one day]

§11.2a made two stock baselines mandatory so a row asserting physics is caught.
This subsection is the same discipline pointed at the SUBJECT rather than at the
rows, and it is filed on mechanism rather than on suspicion.

**What happened, three times.** During EP-25 a mount failed to launch and every
check passed against a plain host directory. Separately, a `~` in a target
descriptor sent the probe into a directory literally named `~`, and the harness
reported ABI 40 of 40 while the record file held one name. Then at the EP-25
verdict this estate's own reviewer ran verify without raising the mount, obtained
ABI 40 of 40 with twenty-three recording-class rows reporting "no DECISION-class
record was appended," and the harness reported forty rows rather than refusing.

**And then the mechanism closed.** An attempt to raise the mount properly failed:
`mountpoint is not empty`, filesystem type `ext2/ext3`. The unmounted probe runs
had written REAL FILES into the mountpoint, and those files now prevent the mount
from ever being raised there. **The failure entrenches itself:** the first
accident makes every later measurement impossible until someone notices and clears
it, and nothing in the instrument says that is what happened. A conformance run
that addresses the wrong thing has also damaged the next run that would have
addressed the right one.

**The rule, in two halves.**

1. **Establish the subject before reporting on it.** Verify mode confirms that the
   target is the thing its descriptor claims — that the path is served by the
   filesystem named, not by an ordinary directory — and ABORTS with a named
   failure otherwise. A pass against an absent subject is worse than a failure,
   because it is indistinguishable from success.
2. **Leave the subject as it was found.** The target's scratch is established
   clean before a run and torn down after, so a run cannot pollute the mountpoint
   it addresses. A scratch found dirty is REPORTED and refused, never driven.

**The refused escape, named because the tooling offers it by name.** `libfuse`
suggests the `nonempty` option when a mountpoint is not empty. Taking it mounts
OVER the leftover files and hides both the pollution and the earlier accident that
caused it — the record would then be measured against a subject with someone
else's files underneath. The leftovers are evidence; the option is a way to stop
seeing them.

**What this costs, stated once:** every conformance figure taken before this
subsection lands is uncitable, because none of them can establish which subject
they addressed. That includes figures already recorded in the build log.

### 11.4a — A record is attributed to the act it COVERS, never to the step it landed in [added 2026-07-27, from EP-24D's first citable run]

§11 rule 4 licenses folding and EP-24D lowered it for the coalescible case. The
first trustworthy run showed that the coalescible case is one instance of a wider
mismatch, and the wider one is what this subsection settles.

**The mismatch.** The harness brackets each driven step and checks the records
appended inside that bracket. A governed filesystem does not append a record in
the step that caused it: a folded write's covering decision is emitted at the
flush boundary the policy names. So ONE fold produces TWO failures in opposite
directions — the `write` row fails because its bracket holds no record, and the
`fsync` row fails because its bracket holds a DECISION while the row classes
fsync CACHE-only.

**Neither of those is a defect in the record or in the map.** §6 is right that
fsync authorizes nothing: the record appended there is a FILE-WRITE decision
covering the burst, cited to the coalescing policy. §6's note that "the writes it
commits were already DECISIONS" assumed write-time emission and coalescing defers
it, which the same row explicitly permits. The record is right, the map is right,
and the attribution is wrong.

**The rule.** The recording check attributes a record to the act it COVERS, read
from the record's own action, object and citation, and never to the step whose
bracket it happened to land in. A record carries what it is about; timing is not
needed to know that, and using timing manufactures failures in both directions
wherever emission is deferred.

**Why this is not a coalescing rule.** Every deferred-emission shape breaks
bracket attribution the same way — batching, flush-on-close, an eventual commit,
any future subsystem's equivalent. Fixing the coalescible slice alone would leave
the class, and this section exists so the next subsystem does not rediscover it.

**The consequence that makes it urgent rather than tidy.** While attribution is
by bracket, a recording-leg failure cannot be told from an artifact, so a REAL
recording gap hides inside a set of failures everyone has agreed to discount.
EP-24D found exactly that: `chown` appends nothing at all in either world, which
no attribution model explains, and it sat unnoticed inside failures attributed to
folding. A leg that cannot distinguish its own false positives is not yet
evidence.

### 11.4b — Ownership is DERIVED from the delegation chain; there is no ownership field, and no ownerless case [added 2026-07-29, OWNER-RULED, from the EP-28 R-2 finding]

§11.4a rules that a record is attributed to the act it COVERS. Ownership is that
rule's twin, and EP-28's R-2 is what forced it: every file created through the
stance-3 mount folded back owned by root, behind a fallback that happened to equal
the creator, unseen for an entire EP.

**The rule.** The owner of a thing is **the actor at the head of the recorded
delegation chain on the covering decision.** One rule, no branch. Where a
background worker acts under a clear delegation, the delegator owns; where no
delegation is recorded, the chain ends at the actor that ran, and it owns. The
system's own answer to "who owns it" is therefore always a fold over the record,
never a lookup.

**"Clear delegation" is self-enforcing and needs no extra machinery.** A
delegation is followed only if it is IN the record. An unrecorded delegation is
not a weak delegation, it is no delegation, and the chain stops at the worker.
Nothing has to detect an unclear case; the record's silence is the answer.

**The consequence that matters more than the rule.** There is no ownership FIELD.
A field is a frozen copy of the creating decision, and the fallback that produced
R-2 (`node.uid or os.getuid()`) could only be written because somebody believed
the field might be absent. Under this rule the question cannot arise, so the
default has nowhere to live. **A fold reading an ownership attribute is the defect,
whether or not its value is currently right.**

**Genesis closes the last hole.** The standing objection to creator-derived
ownership is the file that exists before any account does. It has no force here:
the founding mints root law, SYSTEM, the owner tunnel and the mother space
(`design/26` §8; `design/27` §§30, 71), so SYSTEM is a real actor with a real
founding record and not a placeholder. **The system installs itself, so the system
is the creator, so there is no ownerless case.** Owner's formulation, carried
verbatim because it is the whole argument.

**Clarification [2026-07-29, at the EP-28 amend-pass verdict, on the builder's
raise 5].** Two questions arrived against this rule the day after it was filed and
both are answered inside it.

**A `FILE-CHOWN` fold is the DERIVATION, not an attribute read.** The defect this
section names is a fold reading a stored ownership attribute on a derived node. A
chown is a recorded governed decision that changes ownership, so folding a create
plus its subsequent chowns IS the delegation chain being walked. Read the rule as:
**the actor at the head of the recorded delegation chain on the covering decision,
where the covering decision is the most recent recorded decision that determines
ownership.**

**A numeric uid is a RENDERING, not a stored attribute.** POSIX requires a number
and this section speaks of actors; the actor-to-uid mapping is itself recorded
identity. A port converting a derived actor into the number the ABI demands is
rendering a derived answer, which is what every view in the estate does.

**One case is OPEN and is named rather than papered over.** EP-28's mount root has
no record describing it, so the fold answers it from the server's own identity —
stable, same for every caller, and still not derived, against this section's claim
that there is no ownerless case. The derivation is available and cheap: a mount is
a recorded governed act, so the mount root's owner is the actor on the mount
decision. EP-33 close-ledger item 28; EP-31 intake.

**What this section does NOT settle, deliberately.** The hard instance is a write
the kernel performs with no delegation recorded at all — writeback of a page a
process dirtied through a mapping, issued later by a flusher. Under the rule as
written the chain ends at the flusher, which is the wrong answer and is exactly
the root fallback arriving through a different door. `design/10` §11.1g's refusal
keeps that case from existing at M3 and M6; whether any residual class of it
survives is EP-31's to measure and rule, not this section's to guess. Named as
intake in EP-31, not left open here.

### 11.1c AMENDMENT — `munmap` was cited as an example that does not exist; and the class is populated by OP DEFINITIONS [2026-07-30, correcting this document]

**Two corrections, both to §11.1c and both this seat's.**

**1. `munmap` was named as one of two "today" examples and there is no `munmap`
op.** Found by EP-28B's stopped builder while reading all 72 op definitions
against §11.1c's test. The word is removed above. **A law that cites a
non-existent example teaches its own test wrongly** — a builder applying §11.1c
looks for the named cases first, and one of the two named cases could never be
found. That is worse than naming no example, because absence reads as
"not implemented yet" rather than as "never existed."

**2. The class is populated by OP DEFINITIONS, not by served capability.** An op
whose whole effect is to release something the caller already lawfully holds is in
the class **the moment its definition exists.** §11.1c governs the gate's
authority step, which is an op-definition-level question — so whether a subsystem
actually serves the operation is irrelevant to membership.

**Worked, because the ambiguity cost a session.** `FILE-UNLOCK` is in the founding
pack and satisfies the test. `T-FLOCK-RECORDS` is RED and the kernel module's lock
slots are empty. **Those facts do not conflict: `FILE-UNLOCK` is in the class and
is not yet served.** An earlier authoring said the class was defined by the test
AND that `FILE-UNLOCK` would join "when locks land" — treating one condition as
future when it had been satisfied at EP-25 ADDENDUM 9. A builder found both halves
and refused to choose, correctly.

**`COMMS-CLOSE` and `SESSION-CLOSE` are OPEN against this test** — reported
arguable and unevaluated, evaluated at EP-28B and raised there rather than
declared.

### 11.1c AMENDMENT 2 — the class population is CLOSED; `COMMS-CLOSE` and `SESSION-CLOSE` are OUT, by two different failures of one test [2026-07-30, at the EP-28B verdict]

EP-28B's builder read all 72 op definitions against §11.1c's test, declared none,
and raised both candidates with reasons. **Ruled: both are OUT, and the pair is
worth keeping because they fail the SAME test in two DIFFERENT places.**

§11.1c's test, with its load-bearing words marked: *every op whose **WHOLE EFFECT**
is to release something the caller **ALREADY LAWFULLY HOLDS**.*

- **`COMMS-CLOSE` fails "whole effect".** A channel teardown **moves a second
  party's state**. Refusing it is therefore meaningful governance rather than
  incoherent, which is the entire ground §11.1c stands on. OUT.
- **`SESSION-CLOSE` fails "already lawfully holds".** It takes a **global
  `session_id`**, so the definition does not establish that the caller holds the
  thing being released. POSIX `close` cannot structurally name another process's
  descriptor; `SESSION-CLOSE` can. OUT.

**The population is CLOSED at `FILE-CLOSE` and `FILE-UNLOCK`.** Derived free by
the same reading, each excluded with a reason: `MEM-EVICT`, `UNBIND`/`UNMOUNT`,
`REVOKE`, `FILE-UNLINK`, `COMMS-RECV`.

**And the pair teaches the test better than the rule text did**, which is why it is
filed rather than just decided: a candidate can be a genuine release and still be
out because releasing it touches someone else, or because the definition never
established the caller had it. **Neither failure is visible from the verb.**

### 11.2b AMENDMENT — the sixth-firing MECHANISM was wrong; and firings are counted at INSTRUMENTS, not at EPs [2026-07-30, at the EP-28D verdict]

**Two corrections, and the first is a mechanism this section asserted and driving
it refuted.**

**1. The stated mechanism was that the interleaving makes the row's `EBADF` answer
DISAPPEAR. Driven with a held-descriptor double, it does not.** The `files.close`
row's second `close` **SUCCEEDS**, and the `EBADF` it reports is raised a moment
later by the instrument's own barrier on the descriptor the row just closed. **The
ABI leg sees the pinned answer and passes.**

**The corrected reading, and it is worse than the original: this was never a row
red for the wrong reason. It was a row GREEN for the wrong reason.** The prior text
stands above with this correction beside it rather than being rewritten, because a
law that silently acquires the right mechanism loses the evidence that it once had
the wrong one.

**Why green-for-the-wrong-reason is the harder half of this whole section.** In
every earlier instance the instrument's interference produced a WRONG observation,
and a wrong observation eventually gets investigated. **Here the instrument
supplied the EXPECTED answer.** An assertion satisfied by the instrument rather
than by the subject is invisible to the assertion, and nothing downstream has a
reason to look.

**The discriminator that settles it is the RECORD, which is the one thing in the
loop that cannot be the instrument.** A `close` that raises appends nothing, so **a
step whose record bracket GREW is a step whose close RETURNED.** Step 2's bracket
grows; steps 3 and 4, genuine `EBADF`s, do not.

**2. Firings are counted at INSTRUMENTS, not at EPs** — EP-28D's raise, and it is
right. Counting per-EP inflates the total and hides which instruments are repeat
offenders. Re-counted at instruments, the distinct offenders are: **the conformance
harness (twice — rows against an unmounted mountpoint, and the fixture descriptor),
the acceptance battery (fd 9 across a fork), the `virsh` precondition check, and
the fast-revert loop (masking `/tmp` by never rebooting).** **The conformance
harness is the repeat offender and it is also the instrument this campaign leans on
hardest**, which is a fact about where to look next rather than a tally.

**And EP-28D found two MORE instances inside its own battery and declared both** —
a descriptor enumeration that held a descriptor on the table it enumerated and
first reported the mechanism absent while it was present, and tests leaking held
descriptors into each other so that a battery about descriptors depended on test
order. **The EP written to repair instrument self-corruption produced instrument
self-corruption in its own battery, twice.** That is not irony; it is the strongest
available evidence that the class is pervasive rather than occasional.

### 11.1e AMENDMENT — only ROW-level marking is mechanized; a step is ENUMERATED [added 2026-07-27, correcting this document]

§11.1e as filed says "a row, or a step within a row" is marked. **The step half
has no mechanism and this seat wrote it without establishing one.** Measured
against the harness: `active`/`activates_at` compile at ROW level, the runner
drops inactive rows, and a step is a call-and-arguments pair the probe drives
unconditionally, with the ABI check comparing steps positionally against the
pinned baseline. Both row-data routes were driven rather than argued — declaring
a step marked compiles and the probe ignores it, producing the identical failure;
removing the step shifts every later step out of alignment with the baseline.

Worse, this was RAISED once and re-directed anyway before it was measured. The
raise was correct the first time.

**The rule until a mechanism exists.** Row-level marking is marked. A STEP whose
subject is out of scope is **ENUMERATED** — named in the verdict with its cause
and its home, and left red — rather than marked, dropped, or accommodated by
re-capturing a baseline.

**And re-capturing a baseline to make a row pass is refused outright.** A capture
rewrites every pinned answer in its group; doing that because a target fails is
moving the measuring stick to fit the thing measured, which is §11.2a's own
concern one level up. A capture is a deliberate dated act taken for its own
reasons, never a way to resolve a red.

**Why enumeration rather than declaring the whole row an exception.** Declaring
`files.mknod` away would un-assert seven passing FIFO steps to accommodate one
out-of-scope step — throwing away real proven custody to tidy a total. A red row
whose cause is established and whose home is named carries more information than a
green one that stopped asking.

### 11.1f — Two files-group rows reclassified on evidence from the first governed mount [added 2026-07-27]

The first real mount produced two rows that no correct filesystem could pass, for
two different reasons. Both are governed amendments to §6 rather than defects in
that mount.

**`chroot` leaves the files group's DECISION class.** The row assigns DECISION and
a synthetic control fixture models it, which is why declaring the row
NOT-GOVERNED turned it green and broke the control — the fixture produces what the
row declares. But `chroot(2)` changes a PROCESS attribute, not the filesystem's
namespace. A filesystem is consulted for the path lookup and never for the root
change itself, and no FUSE filesystem is offered the operation at all. So the row
is asking a filesystem to record something it is never told about.

Ruled: the files-group involvement in `chroot` is the LOOKUP, which is CACHE-only.
The governance of a process's root belongs with the subsystem that governs process
attributes, and re-enters the map there. **What would refute this** and is stated
so a later round can check it cheaply: if any filesystem interface does receive a
root-change notification, the row belongs back in files and this amendment is
wrong.

**The `mknod` whiteout step is out of campaign 3's scope and is MARKED.** That step
drives a character device 0:0, which both pinned stock baselines create
unprivileged because the kernel exempts it from `CAP_MKNOD` — it references no
driver. So it is not device custody, and the earlier reading that it belonged to
the device round was wrong. It is a namespace entry whose only consumer is an
overlay filesystem, and overlay support is named nowhere in this campaign's scope
(D8: core subsystems in, breadth out). Marked per §11.1e with the reason
"overlay-only namespace entry, out of C3 scope", not with a subsystem round.

**And the correction underneath both.** This seat previously directed that
`mknod`'s device steps be marked because devices are a later round. Seven of that
row's eight steps were FIFOs, which this mount can and should serve, and every
failing step of the dependent row was a FIFO step — so that direction would have
marked away real work and hidden a capability the mount already had. The builder
served the FIFO instead and raised it. A marking rule is only as good as the
premise about what is being marked.

### 11.1d — An absent record is not evidence until the act is shown to have happened [added 2026-07-27, correcting a mentor inference]

At the EP-24D verdict this seat wrote: `chown` appends nothing, and no
attribution model explains a record that does not exist, therefore the mount has
a recording gap. That reasoning was wrong and the measurement refuted it. The
kernel sends no SETATTR when a `chown` changes nothing, so `chown(-1,-1)` never
reaches the filesystem at all, and the row drives only that case or an error. A
real `chown(-1,4)` against the same mount appends `FILE-CHOWN` correctly.

**The rule.** "Nothing was recorded" has two causes and they are not
distinguishable from the record: the act happened and was not recorded, or the
act never happened. An absent record is a finding only once the act is shown to
have occurred. For a filesystem specifically, a caller issuing a syscall does not
mean the filesystem was invoked — the kernel elides operations that change
nothing, satisfies some calls from its own caches, and handles others locally
without ever crossing the boundary.

**What this obliges a row to do.** A row asserting that an act records must DRIVE
that act — with arguments that actually change something — or its recording
assertion is untestable and its failures are about the row. A row that cannot be
made to drive its act says so and is marked, rather than reporting the subject.

**And what it obliges a reviewer to do**, since this correction is a reviewer's:
before calling an absent record a gap, establish that the boundary was crossed.
The cheap check is to drive the act with arguments that must change state and see
whether the record appears.

### 11.1e — A row belonging to an unbuilt subsystem is marked, not failed [added 2026-07-27]

EP-25's mount refuses device nodes with `EPERM` because a device node is a
capability reference and the device subsystem is a later round. The conformance
run counted those refusals as ABI failures of the FILES mount, and a second row
then failed because it listed a directory missing an entry the first row could
not create — two rows reporting one unbuilt subsystem.

`design/10` already carries the answer for whole groups: rows enter as data and
are marked inactive-until-their-EP. The same applies BELOW group level. A row, or
a step within a row, whose subject belongs to a subsystem not yet built is marked
with the round that will activate it, and is reported as not-run rather than as a
failure. Marking is scoping and is a governed amendment to this document;
silently dropping the row would be hiding, and counting it is attributing another
round's absence to this one.

### 11.1c — A release records, and is never folded for authority [added 2026-07-27, from the EP-25 crux measurement]

§6 classes `close` as **DECISION (lightweight release)** — "symmetric release of
the open custody — recorded (low-ceremony)." EP-25 read DECISION as
crosses-the-gate, which is K3's contract, and built `close` as a full gated act.
The consequence it measured: `open` plus `close` is 2.04 gated acts per header,
so one 120-header translation unit costs 4.68 s and a defconfig kernel build
projects to about 3.2 hours.

**The parenthetical was carrying a distinction the row never spelled out, and
this section spells it out.** A release RECORDS — the custody span has to be
closed on the record or replay cannot reconstruct which fds were held — and a
release is never subjected to the authority fold, because **refusing a release is
meaningless**: no actor can be denied permission to stop holding what it lawfully
holds. So the class stays DECISION (it appends, it cites, it replays) and the
gate's authority step is skipped for it.

**This is not a new mechanism.** The gate already exempts the chain-end from the
authority step; a release exemption is that same mechanism keyed on the op's own
declared kind rather than on the actor.

**And folding on release is not merely wasteful, it is WRONG at the ports.** A
revoked chain reaching a `close` would refuse under a fold, and POSIX `close` on
a valid descriptor cannot fail with a permission error. So the fold both costs
what it should not and manufactures an ABI divergence in the one case where it
would ever change the answer. The measurement found the cost; the ports contract
is what makes it a defect rather than a tuning choice.

**Scope: the release CLASS, not one row.** Every op whose whole effect is to
release something the caller already lawfully holds records without an authority
fold — `close` today, and every future subsystem's release
counterpart as it lands. An op that releases AND does something else is not a
release; it is that other thing, and it folds.

### 11.1g — `mmap` at the files stance: reads are FILLS, shared writes REFUSE and cite [added 2026-07-28, at the EP-28 verdict]

EP-25 anticipated this exact arrival and said RAISE rather than improvise the
shared-memory boundary. EP-28 raised it: `mmap` is unserved below the line, and
`git` is what exposed it. So the ruling, rather than a discovery to chase.

**A read mapping is a CACHE FILL and records nothing.** A page fault that fills
from the record is precisely design/22 §2's minor fault — the hot path is a fill,
not a decision — and the content it fills from is already content-addressed by the
files stance. Read mappings are served. That covers most of what exposed the gap:
`git` maps pack files to read them, a compiler maps sources, a linker maps
objects.

**A SHARED WRITABLE mapping REFUSES, with a cited refusal, until the memory
subsystem lands.** The reason is not difficulty, it is honesty about where the
decision happens. A program writing through a shared mapping produces no
filesystem call at write time — the kernel writes back dirty pages at its own
discretion — so the covering decision has no moment to be made at. Serving such a
mapping would mean either recording nothing (custody fiction, K1 dead) or
inventing a decision at writeback (a record that lies about when a thing was
decided). **Refusing honestly is the third option and it is the estate's own
shape**: `mknod` refuses honestly for a subsystem not yet built, and this is the
same, one boundary over.

**The boundary is named rather than left open.** Shared writable mappings are the
memory subsystem's to serve, at EP-31, where design/22's classification table is
the stage brief and where evictions freeze their evidence. Until then a program
that requires one gets a refusal it can see, not data that quietly does not
persist — the correct failure direction, and the only one compatible with
"accepted-but-cannot-honour refuses."

**The honest cap, stated once:** `T-UNMODIFIED-PROGRAM` at this stance means
programs that read through mappings, not programs that write through shared ones.
A program in the second class is out of scope at M3 and is a required green at
M6, not a defect of M3.

**AMENDMENT [2026-07-29, OWNER-RULED — the refusal is PERMANENT, and the last
sentence above is corrected].** The paragraph above assumed the M3 refusal was a
staging decision that M6 would lift. The owner ruled otherwise, and the ruling is
the definitive this section was missing:

**§4.3 owns a file-backed shared writable mapping, not §4.5.** File content is
file content regardless of the door it came through. §4.5's "interior writes are
not audited" governs memory shared between actors, where nothing durable is
produced; it does not reach a mapping whose interior BECOMES file content, and
reading it that way would open a path where a governed write leaves the record as
a mechanical memory poke. The owner's words: no side door.

**So the refusal STANDS at target state. M6 does not loosen it.** The corrected
form of the sentence above: a program that writes through a shared file-backed
mapping is refused at M3 and is STILL refused at M6. It is not a required green at
any milestone, and `T-UNMODIFIED-PROGRAM` never covers that class.

**Scope, confirmed and narrow.** The refusal is **shared writable file-backed
mappings only**. Read-only and execute mappings are CACHE fills, are served, and
stay served — so program loading, library loading, and every tool that maps a file
to read it are unaffected. `MAP_PRIVATE` writable mappings are copy-on-write and
produce no file content, so they are outside the refusal too: nothing durable
leaves them without a `write` or an `msync`.

**The one door that may open later, named now so it is not improvised.** If
serving these mappings is ever wanted, it returns through an explicit recording
MOMENT, with `msync` as the commit point (row §5 `msync` already records the write
and its blob hash). Never silent kernel writeback, and never the §4.5 interior
reading. That is a scoped future decision on its own evidence, not a loosening of
this rule.

**What made the ruling necessary rather than tidy (reporter fact, 2026-07-29).**
The stance-3 FUSE mount never implemented an `mmap` handler and never needed to:
`fuse.ko` is page-cache backed, so the mount inherited mapping support without
anyone deciding to serve it, and `planning/vm/M3-EVIDENCE.md`:419 records it
plainly — mapping worked "for free." **The side door was open by inheritance for
the whole of the crux EP and no document knew.** That is the strongest possible
argument for the owner's reading: an unruled boundary was not a boundary left
open on purpose, it was one nobody had been told existed.

**AMENDMENT 2 [2026-07-29, at the EP-28 amend-pass verdict — "cited refusal"
overreached, and the implementation was right].** This section says a shared
writable mapping "REFUSES, with a cited refusal." EP-28 implemented a boundary
refusal that records nothing, crosses nothing, and is counted in an aggregate.
**That is correct and the wording above was wrong.** "Cited refusal" imports the
recorded-decision shape onto what is a **capability refusal below the crossing
line** — the same shape as `mknod` refusing for a subsystem not yet built, which
the estate already holds as accepted-but-cannot-honour REFUSES. Manufacturing a
crossing so a refusal could be recorded would spend a context switch per attempt
to record that an operation nobody serves was not served. **What the refusal owes
is that it be OBSERVABLE and distinguishable from a no-op**, which the aggregate
delivers and which is also the divergence rule satisfied. Read the paragraph above
with "cited refusal" as "refusal at the boundary, counted, distinguishable from a
no-op."

**INFERRED, and it is EP-31's to settle, not this section's** (trained knowledge
of `fuse.ko`, not read from code): dirty pages from a shared mapping are written
back by the kernel as ordinary filesystem write calls, issued at writeback time
and potentially by a flusher rather than by the writing process. If that holds,
stance-3 mapping writes were RECORDED but attributed to the writeback moment and
possibly to the wrong actor, which is §11.4a's rule (a record is attributed to the
act it covers) meeting the two times of authority. Not lost content; unspecified
attribution. It is stated here as an open fact about a shipped world, not as a
defect of it, and it does not change the ruling above in either direction.

### 11.2a — Two stock baselines, always [added 2026-07-26, the EP-24 finding, sitting mentor]

§11.2 says conformance checks the guarantee POSIX makes, not the nanosecond
physics. It does not say how a row that breaks that rule is CAUGHT, and EP-24
answered it by accident: its harness captured two stock kernels, and comparing
the captures showed exactly one difference — an `O_APPEND` concurrency probe
whose recorded bytes were the interleaving. The guarantee held on both kernels;
only the physics differed. The instrument had committed §11.2's error inside its
own probe, and it found it before first use only because a second baseline
existed.

**The rule.** A conformance capture keeps at least TWO stock targets differing
in kernel version, and their agreement across every shared row is itself an
asserted check. A row on which two stock kernels disagree is a row asserting
implementation detail rather than a guarantee, and it is a finding against the
ROW, never against the target under test.

**Why this is structural rather than a convenience.** An instrument that can
commit the error it exists to detect is the dangerous kind, because its false
verdicts are shaped exactly like findings: a governed target failing a
physics-asserting row looks precisely like a governance defect. With one
baseline that confusion is undetectable. Two stock kernels are the cheapest
mechanical discriminator available, and the estate's own build route already
carries the same shape one level up — prove on the pinned kernel, accept on the
exact Ubuntu kernel. The harness now carries it at the row.

**Consequence for every subsystem EP.** When a governed target fails a row the
two stock baselines disagree on, suspect the row first.

### 11.1a — Three outcome classes for an error return [added 2026-07-26, the EP-24 finding, sitting mentor]

§11.1 says a gov-os refusal is additionally a recorded rule-citing decision. It
does not say WHICH error returns are refusals, and EP-24's harness found the
gap by hitting it: from outside a target, `ENOENT` because an actor could not
lawfully see a path and `ENOENT` because the path was never there are
indistinguishable. Faced with that, the harness waived the required half of its
recording check on rows whose only outcome is an error, and wrote the waiver
onto the result. That waiver is the wrong way round — a refusal is precisely the
case where a record is MOST required (P4) — and it exists only because the
distinction below was missing from this document.

**The discriminator is not the errno. It is whether the gate reached a
decision**, and that is knowable from inside the target, which is where the
recording check already looks. Every row whose tested outcome is an error
return declares which of these three it asserts:

1. **REFUSAL.** The gate decided no, and the errno is that refusal mapped to
   POSIX. A rule-citing DECISION record is REQUIRED; its absence is a failure.
   Sight-is-law denials, missing grants, and protected-core refusals are all
   this class.
2. **ABSENCE.** The view answers "no such thing." The call is a read, so a
   record appearing is the failure — this is the CACHE-class side of the class
   map, and a read that appended is exactly what T-RATE-GOVERNANCE catches.
3. **NOT-GOVERNED.** The call never reached a governed decision at all (a bad
   descriptor, an argument rejected before any gate step). No record, and a
   record appearing is a failure.

Classes 2 and 3 both require no record and are distinguished by what they mean,
not by what they check; they are kept apart because a row's author must say
which one is true, and "it appends nothing" is not the same claim as "nothing
was governed here."

**Consequence for the harness.** With the row declaring its class, both halves
of the recording check bind on every row and the waiver retires. **Consequence
for custody:** this must be settled before a subsystem takes real authority,
because a mount that refuses for real, with its refusals exempt from the
recording check, is a custody claim whose audit leg is switched off precisely
where custody is being asserted.

## 12. Coverage & what this document excludes (honest boundary)

**Covered:** the high-traffic and load-bearing syscalls across process/scheduling
(§4), memory (§5), files/VFS (§6), devices & I/O multiplexing (§7), IPC/comms
(§8), time/signals (§9), and info/pseudo-fs (§10) — approximately the calls a
normal userland (a shell, a browser, a server) exercises, which is the population
the ports contract must hold for.

**Deliberately not exhaustive.** The Linux syscall table has ~450 entries
(architecture-dependent) plus compat/32-bit variants. This map covers the
governing-behaviour representatives; a mechanical row for every `*at`/`compat`/
`_time64` variant is generated from its primary (same class, same note) and is
not spelled out here.

**Out of scope for this document (named, not hidden — per 03 §8):**
- The **`/proc` view catalogue** — now exists: `13-VIEWS-AND-PROC-CATALOGUE.md` §8.
- The **driver-shim detail** (§7 `ioctl`/device-fd behaviour at the typed
  boundary, 03 §4.4) — now exists: `24-DRIVER-SHIM-DETAIL.md`.
- **Architecture-specific calls** (x86 `arch_prctl`, `modify_ldt`; io-port and
  MMIO specifics) — deferred to the driver-model work.
- **Namespace/container calls** (`unshare`, `setns`, `clone(CLONE_NEW*)`) —
  touched via `clone`/`setns` but their full governance treatment (namespaces as
  scoped LAW) is a derivation of its own.
- The **formal proof** that intake ordering yields deterministic replay under
  every interleaving — now exists: `21-ORDERING-DETERMINISM-PROOF.md`. This map
  states ordering as definitional; `21-` proves it.

**Labels recap (per `00-READ-FIRST.md` §6):**
- **trained knowledge (Estimate — High):** the entire Linux ABI surface —
  names, signatures, semantics, errno, grouping (columns 1, 2, 5's ABI clauses).
- **SOURCE-DERIVED:** the five recording classes and every subsystem framing —
  `03-TARGET-STATE-ARCHITECTURE.md` §2 and §4.1–§4.5, cited per row-group; the
  clock-as-sensor and scheduled-execution rulings — `00-READ-FIRST.md` §4.
- **INFERRED:** the per-call recording-class assignment in column 4 — the owner's
  rule applied to each call by me; the classification of judgement calls (e.g.
  `close` as lightweight release, `fsync` as barrier, `sigprocmask` as
  coalescible disposition change, `futex` interior ops as unaudited) is flagged
  in the relevant note.
- **PROPOSED (cost if wrong):** none load-bearing here; where a class is a
  borderline judgement the note says so, and reclassification is a governed
  amendment to this spec (§3), not a silent edit.

**This document excludes** any claim about performance, any architecture-specific
detail, and any syscall not exercised by mainstream userland; and it does not
prove the ordering determinism it relies on.
