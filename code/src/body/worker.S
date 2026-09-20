/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — OUR small hand-written test worker (C7 P3b-4a; design/54 §7 P3b-4a).
 *
 * A tiny program of OURS — a BARE STATIC x86_64 image (no C runtime, no libc, no libgcc). It is loaded
 * by the body's OWN ELF64 loader from a SEALED IMAGE, runs UNPRIVILEGED (ring 3), makes a HANDFUL of
 * requests that cross into the body by the machine's own call crossing (SYSCALL), and reads the body's
 * answers. It is OUR source, read whole and attested BY NAME; the built worker IMAGE is a binary, NEVER
 * a signed member (§9 mechanism 3). This proves the ENCLOSURE MECHANISM — NOT the forty-nine (P3b-4b),
 * NOT the borrowed interpreter (P3b-4c).
 *
 * THE CROSSING SHAPE is the measured x86_64 SYSCALL path (planning/evidence/C7-P3b-4s.../FINDINGS.md):
 * the request number in %rax, args in %rdi/%rsi/…, the answer back in %rax; a request the body does not
 * serve returns the native -ENOSYS shape, and the worker fails as it natively would.
 *
 * ONE ENTRY (_wstart), dispatching on %rdi the body sets at entry:
 *   %rdi == 0  -> the MAIN run: report its privilege, echo-round-trip, announce, an out-of-set request
 *                 (refused native), then EXIT (the served handful MUST include EXIT, HOW rider).
 *   %rdi == 1  -> the TRESPASS probe (%rsi = a BODY address): read the body's memory DIRECTLY. The
 *                 hardware faults it (#PF) and the body catches the fault — enclosure is a HARDWARE FACT
 *                 (L18). Only if the machine FAILED to fault (the PLANT path) does the read return and the
 *                 worker report REQ_TRESPASS_OK, which reds the check.
 *   %rdi == 2  -> the FORTY-NINE run (C7 P3b-4b): make each of the measured requests in its measured
 *                 x86_64 shape — the request number in %rax, args in %rdi/%rsi/%rdx/%r10/%r8/%r9 — and
 *                 read the body's answer. The body classifies each by PURPOSE, serves/refuses/stubs it,
 *                 and witnesses each as one unsigned row of its own serve trail. exit_group ends the run.
 *
 * Every instruction runs in the guest's nested qemu at ring 3; nothing here targets the host kernel (L11).
 */
.code64
.section .text
.global _wstart
_wstart:
    cmpq $2, %rdi
    je _wforty                      /* %rdi == 2 -> the forty-nine run (C7 P3b-4b) */
    testq %rdi, %rdi
    jnz _wtrespass                  /* %rdi == 1 -> trespass probe, %rsi = the body address */
    /* fall through to the main run (%rdi == 0) */

/* ── the main run: a handful of requests, reading the body's answers ────────────────────────────*/
_wmain:
    /* REQ_REPORT_PRIV(cs, ss): the worker's OWN privilege level, read from the machine (its %cs/%ss).
     * The low two bits of %cs are the CPL — a machine fact, not a convention. */
    xorq %rdi, %rdi
    movw %cs, %di                   /* a0 = the worker's code selector (RPL == CPL == 3) */
    xorq %rsi, %rsi
    movw %ss, %si                   /* a1 = the worker's stack selector */
    movq $1, %rax                   /* REQ_REPORT_PRIV */
    syscall

    /* REQ_ECHO(0x1234): a round-trip — the body returns the argument; the worker READS the answer back. */
    movq $0x1234, %rdi
    movq $2, %rax                   /* REQ_ECHO */
    syscall
    cmpq $0x1234, %rax              /* the answer the body sent back */
    jne .echo_bad
    movq $0x4b, %rdi                /* 'K' — the worker announces it read the body's answer correctly */
    movq $3, %rax                   /* REQ_PUTC */
    syscall
    jmp .after_echo
.echo_bad:
    movq $0x58, %rdi                /* 'X' — the round-trip disagreed (never expected) */
    movq $3, %rax
    syscall
.after_echo:

    /* an OUT-OF-SET request (99 — not served this slice): the body refuses it as the worker's OWN
     * native failure answer (-ENOSYS). The worker sees the negative answer as it natively would. */
    movq $0x63, %rax                /* request 99 — outside the served handful */
    xorq %rdi, %rdi
    syscall                         /* %rax <- native -ENOSYS (0xffffffffffffffda) */

    /* EXIT: end the worker (the body regains control by the crossing's own recovery). */
    movq $5, %rax                   /* REQ_EXIT */
    syscall
.mhang:
    jmp .mhang                      /* EXIT never returns; a guard if it somehow did */

/* ── the trespass probe: reach the body's memory DIRECTLY (the hardware must fault it) ───────────*/
_wtrespass:
    movq (%rsi), %rax               /* <-- #PF here: a ring-3 read of a supervisor body page */
    /* only reached if the machine FAILED to enforce the boundary (the PLANT path): report what we read. */
    movq %rax, %rdi
    movq $4, %rax                   /* REQ_TRESPASS_OK — the direct reach SUCCEEDED (enclosure broken) */
    syscall
    movq $5, %rax                   /* REQ_EXIT */
    syscall
.thang:
    jmp .thang

/* ── the FORTY-NINE run (C7 P3b-4b): each measured request in its measured x86_64 shape ──────────────
 * The number is in %rax; args in %rdi/%rsi/%rdx/%r10/%r8/%r9 (r10, not rcx — SYSCALL clobbers rcx/r11).
 * The worker makes each crossing and lets the body answer; the body's serve trail (read on serial) is
 * the witness, so the worker need not check every answer. %rsp is preserved across a crossing (the entry
 * stub saves/restores it), so a scratch region on the stack survives the whole run. Order: entropy AT
 * BRING-UP first, then the loader/TLS floor, the thread floor, the acts' share, the designed refusal, the
 * stubs, the socket refusal, and exit_group last (which the body serves by unwinding — the run ends). */
_wforty:
    subq $256, %rsp                 /* a scratch region: [%rsp+128] the clone_args, [%rsp] buffers/paths */
    movq $0x290100, 128(%rsp)       /* clone_args.flags = CLONE_VM|THREAD|SETTLS|CHILD_CLEARTID (Q-D)    */

    /* ── entropy AT BRING-UP: getrandom(buf, 8, GRND_NONBLOCK) — the startup hash seed ──────────────*/
    movq %rsp, %rdi
    movq $8, %rsi
    movq $1, %rdx                   /* GRND_NONBLOCK */
    movq $318, %rax
    syscall

    /* ── category A — bring-up / loader / TLS floor ────────────────────────────────────────────────*/
    movq %rsp, %rdi
    movq $59, %rax                  /* execve (the loader's own — already home) */
    syscall
    xorq %rdi, %rdi
    movq $12, %rax                  /* brk(0) — query the heap break */
    syscall
    movq $0x1002, %rdi              /* ARCH_SET_FS */
    movq %rsp, %rsi
    movq $158, %rax                 /* arch_prctl(ARCH_SET_FS, fsbase) — TLS */
    syscall
    movq %rsp, %rdi
    movq $218, %rax                 /* set_tid_address */
    syscall
    movq %rsp, %rdi
    movq $24, %rsi
    movq $273, %rax                 /* set_robust_list */
    syscall
    movq %rsp, %rdi
    movq $32, %rsi
    movq $334, %rax                 /* rseq */
    syscall
    xorq %rdi, %rdi
    movq $3, %rsi                   /* RLIMIT_STACK */
    movq $302, %rax                 /* prlimit64 */
    syscall
    movq %rsp, %rdi
    movq $4096, %rsi
    movq $3, %rdx                   /* PROT_READ|PROT_WRITE */
    movq $10, %rax                  /* mprotect (memory machinery) */
    syscall
    movq $3, %rdi
    movq %rsp, %rsi
    movq $64, %rdx
    xorq %r10, %r10
    movq $17, %rax                  /* pread64 (the loader's ELF header read) */
    syscall
    movq %rsp, %rdi
    xorq %rsi, %rsi                 /* F_OK */
    movq $21, %rax                  /* access (ld.so.preload — absent) */
    syscall
    movq %rsp, %rdi
    movq %rsp, %rsi
    movq $64, %rdx
    movq $89, %rax                  /* readlink */
    syscall
    movq %rsp, %rdi
    movq $64, %rsi
    movq $79, %rax                  /* getcwd */
    syscall
    movq $13, %rdi                  /* SIGPIPE */
    movq %rsp, %rsi
    xorq %rdx, %rdx
    movq $13, %rax                  /* rt_sigaction(SIGPIPE, SIG_IGN) */
    syscall
    movq $1, %rdi                   /* SIG_UNBLOCK */
    movq %rsp, %rsi
    xorq %rdx, %rdx
    movq $14, %rax                  /* rt_sigprocmask */
    syscall

    /* ── category B — thread creation floor (the flags word bites: THREAD+VM+SETTLS+CHILD_CLEARTID) ─*/
    leaq 128(%rsp), %rdi            /* &clone_args (flags at [%rsp+128]) */
    movq $88, %rsi                  /* sizeof(clone_args) */
    movq $435, %rax                 /* clone3 */
    syscall
    movq %rsp, %rdi
    movq $4096, %rsi
    movq $4, %rdx                   /* MADV_DONTNEED */
    movq $28, %rax                  /* madvise (a thread stack) */
    syscall
    movq $186, %rax                 /* gettid */
    syscall

    /* ── the twelve acts' share — performed by the act machinery, witnessed like every crossing ─────*/
    xorq %rdi, %rdi
    movq $4096, %rsi
    movq $3, %rdx                   /* PROT_READ|PROT_WRITE */
    movq $0x21, %r10                /* MAP_SHARED|MAP_ANONYMOUS — the MEMORY act (served anon-PRIVATE, Q11)*/
    movq $-1, %r8
    xorq %r9, %r9
    movq $9, %rax                   /* mmap */
    syscall
    movq %rax, %r12                 /* keep the mapped address for munmap (r12 is callee-saved) */
    movq %r12, %rdi
    movq $4096, %rsi
    movq $11, %rax                  /* munmap */
    syscall
    movq %rsp, %rdi                 /* uaddr */
    movq $0x189, %rsi              /* FUTEX_WAIT_BITSET|FUTEX_PRIVATE_FLAG|FUTEX_CLOCK_REALTIME (Q-D)   */
    xorq %rdx, %rdx
    xorq %r10, %r10
    movq $202, %rax                 /* futex — the concurrency act */
    syscall
    xorq %rdi, %rdi                 /* CLOCK_REALTIME */
    movq %rsp, %rsi
    movq $228, %rax                 /* clock_gettime(REALTIME) — the recording-clock read (a cost) */
    syscall
    movq $1, %rdi                   /* CLOCK_MONOTONIC */
    movq %rsp, %rsi
    movq $228, %rax                 /* clock_gettime(MONOTONIC) — the commit-window read (a cost) */
    syscall
    movq $1, %rdi                   /* CLOCK_MONOTONIC */
    movq $1, %rsi                   /* TIMER_ABSTIME — an ABSOLUTE monotonic deadline (Q-D) */
    movq %rsp, %rdx
    xorq %r10, %r10
    movq $230, %rax                 /* clock_nanosleep — the commit-window sleep */
    syscall
    movq %rsp, %rdi
    movq $16, %rsi
    xorq %rdx, %rdx                 /* blocking */
    movq $318, %rax                 /* getrandom — the entropy act draw */
    syscall
    movq $-100, %rdi               /* AT_FDCWD */
    movq %rsp, %rsi                 /* a body-fs path (NOT the module sentinel) */
    movq $0x80441, %rdx            /* O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC — record-pen (Q-D O_APPEND)  */
    xorq %r10, %r10
    movq $257, %rax                 /* openat — the record-pen open */
    syscall
    movq $3, %rdi
    movq %rsp, %rsi
    movq $5, %rdx
    movq $1, %rax                   /* write — the record-pen write */
    syscall
    movq $3, %rdi
    movq $75, %rax                  /* fdatasync — the durability barrier */
    syscall
    movq $3, %rdi
    movq $74, %rax                  /* fsync */
    syscall
    movq $3, %rdi
    movq %rsp, %rsi
    movq $64, %rdx
    xorq %r10, %r10
    movq $0, %rax                   /* read — the read-back / body-read */
    syscall
    movq $3, %rdi
    movq $3, %rax                   /* close */
    syscall
    movq $3, %rdi
    movq %rsp, %rsi
    movq $5, %rax                   /* fstat */
    syscall
    movq $-100, %rdi               /* AT_FDCWD */
    movq %rsp, %rsi
    movq %rsp, %rdx
    xorq %r10, %r10
    movq $262, %rax                 /* newfstatat — exists */
    syscall
    movq %rsp, %rdi
    movq %rsp, %rsi
    movq $82, %rax                  /* rename — same-dir atomic (write-once) */
    syscall
    movq %rsp, %rdi
    movq $0777, %rsi
    movq $83, %rax                  /* mkdir */
    syscall
    movq %rsp, %rdi
    movq $87, %rax                  /* unlink — the remove act (a blob) */
    syscall
    movq $39, %rax                  /* getpid — the single-writer-lock */
    syscall
    movq %rax, %rdi                 /* kill(pid, 0) — pid_alive */
    xorq %rsi, %rsi
    movq $62, %rax
    syscall
    movq $3, %rdi                   /* a body dir fd (NOT the module sentinel) */
    movq %rsp, %rsi
    movq $64, %rdx
    movq $217, %rax                 /* getdents64 — the body-read walk */
    syscall
    movq $3, %rdi
    xorq %rsi, %rsi
    xorq %rdx, %rdx
    movq $8, %rax                   /* lseek — founding-pack-read companion */
    syscall

    /* ── category C — module discovery on a live filesystem: the DESIGNED REFUSAL ──────────────────*/
    movq $0x80000, %rdi            /* EPOLL_CLOEXEC */
    movq $291, %rax                 /* epoll_create1 — the import machinery, refused */
    syscall
    movabsq $0x4D4F44554C450000, %r13   /* the MODULE_SEARCH sentinel (kept in a callee-saved reg)     */
    movq $-100, %rdi               /* AT_FDCWD */
    movq %r13, %rsi                 /* a MODULE-SEARCH path -> refused, bytes from the sealed image      */
    xorq %rdx, %rdx
    movq $257, %rax                 /* openat(MODULE_SEARCH) — the same NAME, a refused PURPOSE */
    syscall

    /* ── category D — io-layer / environment probes: the STUBS ─────────────────────────────────────*/
    movq $1, %rdi
    movq $0x5401, %rsi             /* TCGETS — the isatty probe */
    movq $16, %rax                  /* ioctl */
    syscall
    movq $1, %rdi
    movq $1, %rsi                   /* F_GETFD */
    movq $72, %rax                  /* fcntl */
    syscall
    movq $107, %rax                 /* geteuid */
    syscall
    movq $102, %rax                 /* getuid */
    syscall
    movq $108, %rax                 /* getegid */
    syscall
    movq $104, %rax                 /* getgid */
    syscall

    /* ── the network-socket act share: REFUSED as the native failure until P3b-6 ───────────────────*/
    movq $2, %rdi                   /* AF_INET */
    movq $0x80001, %rsi            /* SOCK_STREAM|SOCK_CLOEXEC */
    xorq %rdx, %rdx                 /* IPPROTO_IP */
    movq $41, %rax                  /* socket — refused native */
    syscall

    /* ── exit_group ends the forty-nine run (the body serves it by unwinding to the serve driver) ───*/
    xorq %rdi, %rdi
    movq $231, %rax                 /* exit_group */
    syscall
.fhang:
    jmp .fhang                      /* exit_group never returns; a guard if it somehow did */

/* a freestanding worker never needs an executable stack. */
.section .note.GNU-stack, "", @progbits
