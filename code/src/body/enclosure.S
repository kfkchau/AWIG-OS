/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the crossing at the metal: the SYSCALL entry stub, the return into ring 3, the recovery,
 * and the sealed worker image (C7 P3b-4a; design/54 §5 L18, §7 P3b-4a).
 *
 * THE CROSSING IS THE MACHINE'S OWN (L18). A worker request is a SYSCALL from ring 3. The CPU (with the
 * MSRs set by enclosure.c) saves the return RIP in %rcx and RFLAGS in %r11, loads the kernel CS/SS from
 * MSR_STAR and RIP from MSR_LSTAR (-> syscall_entry), and — crucially — does NOT switch the stack. So the
 * stub SAVES the worker's %rsp, switches to the body's syscall stack, counts the crossing, saves and
 * restores the worker's registers around the dispatch into body_request, and SYSRETs back to ring 3 with
 * the answer in %rax. Every crossing lands here; the record is not optional (I7). The EXIT request never
 * SYSRETs — body_request unwinds to the body via body_longjmp.
 *
 * Read whole (I3): the entire low-level crossing surface. Every instruction runs in the guest's nested
 * qemu; nothing here targets the host kernel (L11). Assembled by gcc (.S, so the C preprocessor runs —
 * the A2 near-miss PLANT_WORKER_RING0 returns into ring 0 so the machine-read privilege check can fail).
 */
.code64
.section .text

/* ── syscall_entry: the SYSCALL entry stub (MSR_LSTAR points here) ───────────────────────────────
 * On entry (SYSCALL): %rcx = return RIP, %r11 = return RFLAGS, %rax = request number, args in the
 * measured x86_64 shape (%rdi, %rsi, %rdx, %r10, %r8, %r9); still on the WORKER stack, in ring 0. */
.global syscall_entry
.type syscall_entry, @function
syscall_entry:
    movq %rsp, saved_user_rsp(%rip)         /* transient scratch: bridge the stack switch only       */
    movq syscall_kernel_rsp(%rip), %rsp     /* switch to the CURRENT thread's syscall (kernel) stack */
    incq g_crossings(%rip)                   /* EVERY crossing is counted, before the dispatch (I7)  */
    movq %rcx, g_syscall_ret_rip(%rip)       /* C7 P3b-4f-ii: stash the crossing's return rip...     */
    movq %r11, g_syscall_ret_rflags(%rip)    /* ...and rflags, so clone3 can build a child's context */
    movq %r9,  g_syscall_a5(%rip)            /* C7 P3b-4d: stash the 6th arg (r9) — mmap's file offset */
    /* PRESERVE ACROSS THE CROSSING. (1) The Linux syscall ABI leaves ALL registers unchanged except rax
     * (the return), rcx and r11 (clobbered by SYSCALL) — glibc relies on it (e.g. it keeps the thread
     * descriptor in %r9 across an rt_sigprocmask in start_thread). (2) The worker's USER rsp is saved
     * PER-THREAD on this thread's own kernel stack — NOT in the saved_user_rsp global, which another thread's
     * crossing would clobber while this thread is blocked in a syscall (a futex wait that deschedules), so
     * a blocked thread would resume on the wrong stack (C7 P3b-4f-ii). 16 pushes keep the SysV call aligned. */
    pushq saved_user_rsp(%rip)               /* [1] the worker's USER rsp (per-thread, on this kstack) */
    pushq %rax                               /* [2] pad for 16-alignment (discarded; rax is the answer)*/
    pushq %rcx                               /* [3] the return RIP (SYSRET restores it)                */
    pushq %r11                               /* [4] the return RFLAGS                                  */
    pushq %rbx                               /* [5] */
    pushq %rbp                               /* [6] */
    pushq %r12                               /* [7] */
    pushq %r13                               /* [8] */
    pushq %r14                               /* [9] */
    pushq %r15                               /* [10] */
    pushq %rdi                               /* [11] a0 (worker) — preserved across the crossing       */
    pushq %rsi                               /* [12] a1                                                */
    pushq %rdx                               /* [13] a2                                                */
    pushq %r10                               /* [14] a3                                                */
    pushq %r8                                /* [15] a4                                                */
    pushq %r9                                /* [16] a5 (worker) — preserved across the crossing       */
    /* map the SYSCALL arg shape to body_request(num, a0, a1, a2, a3, a4) in the SysV C shape.
     * order chosen so no source is overwritten before it is read. */
    movq %r8,  %r9                           /* a4 (r8)  -> C arg5 (r9)                               */
    movq %r10, %r8                           /* a3 (r10) -> C arg4 (r8)                               */
    movq %rdx, %rcx                          /* a2 (rdx) -> C arg3 (rcx)                              */
    movq %rsi, %rdx                          /* a1 (rsi) -> C arg2 (rdx)                              */
    movq %rdi, %rsi                          /* a0 (rdi) -> C arg1 (rsi)                              */
    movq %rax, %rdi                          /* num (rax)-> C arg0 (rdi)                              */
    call body_request                        /* rax = answer; REQ_EXIT longjmps out (never returns)  */
    popq %r9                                  /* restore the worker's registers (rax keeps the answer) */
    popq %r8
    popq %r10
    popq %rdx
    popq %rsi
    popq %rdi
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbp
    popq %rbx
    popq %r11                                /* the saved return RFLAGS                              */
    popq %rcx                                /* the saved return RIP                                 */
    addq $8, %rsp                            /* discard the pad (do NOT pop into rax — it is the answer) */
    popq %rsp                                /* restore the worker's USER rsp (per-thread, from kstack)  */
    sysretq                                  /* RIP<-rcx, RFLAGS<-r11, CS/SS<-user; rax = the answer */
.size syscall_entry, . - syscall_entry

/* ── enter_ring3(entry=%rdi, user_rsp=%rsi, a0=%rdx, a1=%rcx): iretq into the worker at ring 3 ────
 * Builds the iretq frame (SS, RSP, RFLAGS, CS, RIP), passes a0/a1 in the worker's %rdi/%rsi, and clears
 * the other GP registers so no body state leaks into the worker. RFLAGS bit 1 only (IF=0) — the worker
 * runs with interrupts off, so the enclosure demonstration is deterministic; its faults are exceptions,
 * which IF does not mask. Never returns normally: the worker EXITs or faults, both of which longjmp. */
.global enter_ring3
.type enter_ring3, @function
enter_ring3:
#ifdef PLANT_WORKER_RING0
    /* A2 near-miss (the machine-read privilege check can fail): return into RING 0 (kernel CS/SS). The
     * "worker" then reports %cs with RPL 0, and the ring-3 check reds. */
    pushq $0x10                              /* SS = kernel data (ring 0)                            */
    pushq %rsi
    pushq $0x2
    pushq $0x08                              /* CS = kernel code (ring 0) -> no privilege change     */
    pushq %rdi
#else
    pushq $0x23                              /* SS = user data | RPL 3                               */
    pushq %rsi                               /* the user stack top                                   */
    pushq $0x2                               /* RFLAGS: reserved bit 1 only (IF=0)                   */
    pushq $0x2b                              /* CS = user code64 | RPL 3                             */
    pushq %rdi                               /* RIP = the worker entry                               */
#endif
    movq %rdx, %rax                          /* stash a0                                             */
    movq %rcx, %r11                          /* stash a1                                             */
    xorq %rbx, %rbx
    xorq %rbp, %rbp
    xorq %r8,  %r8
    xorq %r9,  %r9
    xorq %r10, %r10
    xorq %r12, %r12
    xorq %r13, %r13
    xorq %r14, %r14
    xorq %r15, %r15
    xorq %rdx, %rdx
    xorq %rcx, %rcx
    movq %rax, %rdi                          /* a0 -> worker %rdi                                    */
    movq %r11, %rsi                          /* a1 -> worker %rsi                                    */
    xorq %rax, %rax
    xorq %r11, %r11
    iretq
.size enter_ring3, . - enter_ring3

/* ── body_setjmp(ctx=%rdi) / body_longjmp(ctx=%rdi, val=%rsi): the recovery a worker fault or EXIT uses.
 * The context is 8 quadwords: rip, rbx, rbp, r12, r13, r14, r15, rsp. ─────────────────────────────*/
.global body_setjmp
.type body_setjmp, @function
body_setjmp:
    movq (%rsp), %rax                        /* the return address                                   */
    movq %rax, 0(%rdi)
    movq %rbx, 8(%rdi)
    movq %rbp, 16(%rdi)
    movq %r12, 24(%rdi)
    movq %r13, 32(%rdi)
    movq %r14, 40(%rdi)
    movq %r15, 48(%rdi)
    leaq 8(%rsp), %rax                        /* the caller's rsp after the ret pops the return addr  */
    movq %rax, 56(%rdi)
    xorq %rax, %rax                           /* the direct call returns 0                            */
    ret
.size body_setjmp, . - body_setjmp

.global body_longjmp
.type body_longjmp, @function
body_longjmp:
    movq 8(%rdi), %rbx
    movq 16(%rdi), %rbp
    movq 24(%rdi), %r12
    movq 32(%rdi), %r13
    movq 40(%rdi), %r14
    movq 48(%rdi), %r15
    movq 56(%rdi), %rsp
    movq %rsi, %rax
    testq %rax, %rax
    jnz 1f
    movq $1, %rax                             /* longjmp never makes body_setjmp return 0            */
1:
    movq 0(%rdi), %rcx
    jmpq *%rcx
.size body_longjmp, . - body_longjmp

/* ── load_tr(sel=%rdi): load the task register with the TSS selector ─────────────────────────────*/
.global load_tr
.type load_tr, @function
load_tr:
    ltr %di
    ret
.size load_tr, . - load_tr

/* ── C7 P3b-4f-ii — THE CONCURRENCY FLOOR's ring-3 entries + per-thread SSE state (design/54 §5 L19).
 * Both enter ring 3 with interrupts ENABLED (RFLAGS=0x202) so the preemptive scheduler's timer can take a
 * turn — unlike the single-thread floor / worker, which run deterministic with IF=0. ─────────────────*/

/* enter_ring3_main(entry=%rdi, user_rsp=%rsi): the first (main) thread — iretq to ring 3, all GP cleared,
 * IF=1. glibc's _start reads argc/argv/auxv from the initial stack the loader laid. */
.global enter_ring3_main
.type enter_ring3_main, @function
enter_ring3_main:
    pushq $0x23                              /* SS = user data | RPL 3                               */
    pushq %rsi                               /* RSP = the initial (SysV) stack top                   */
    pushq $0x202                             /* RFLAGS: reserved bit 1 + IF=1 (preemptible)          */
    pushq $0x2b                              /* CS = user code64 | RPL 3                             */
    pushq %rdi                               /* RIP = the program entry                              */
    xorq %rax, %rax
    xorq %rbx, %rbx
    xorq %rcx, %rcx
    xorq %rdx, %rdx
    xorq %rsi, %rsi
    xorq %rdi, %rdi
    xorq %rbp, %rbp
    xorq %r8,  %r8
    xorq %r9,  %r9
    xorq %r10, %r10
    xorq %r11, %r11
    xorq %r12, %r12
    xorq %r13, %r13
    xorq %r14, %r14
    xorq %r15, %r15
    iretq
.size enter_ring3_main, . - enter_ring3_main

/* enter_ring3_thread(entry=%rdi, user_rsp=%rsi, func=%rdx, arg=%rcx): a clone3 child — iretq to the
 * clone3-crossing return rip with rax=0 (glibc takes the thread_start path), rdx=func, r8=arg (glibc:
 * `mov %r8,%rdi; call *%rdx`), the rest cleared, IF=1. */
.global enter_ring3_thread
.type enter_ring3_thread, @function
enter_ring3_thread:
    movq %rcx, %r8                           /* r8 = arg (before building the frame)                 */
    pushq $0x23                              /* SS                                                   */
    pushq %rsi                               /* RSP = the new thread stack top                       */
    pushq $0x202                             /* RFLAGS: IF=1                                          */
    pushq $0x2b                              /* CS                                                   */
    pushq %rdi                               /* RIP = the clone3 return (test %rax,%rax ; jz start)  */
    xorq %rax, %rax                          /* the child: rax == 0 -> thread_start                  */
    /* %rdx (func) and %r8 (arg) are preserved — the child reads them. Clear the rest. */
    xorq %rbx, %rbx
    xorq %rcx, %rcx
    xorq %rsi, %rsi
    xorq %rdi, %rdi
    xorq %rbp, %rbp
    xorq %r9,  %r9
    xorq %r10, %r10
    xorq %r11, %r11
    xorq %r12, %r12
    xorq %r13, %r13
    xorq %r14, %r14
    xorq %r15, %r15
    iretq
.size enter_ring3_thread, . - enter_ring3_thread

/* body_fxsave(area=%rdi) / body_fxrstor(area=%rdi): save/restore the full x87+SSE state (512 bytes,
 * 16-aligned) at a context switch — each thread keeps its own xmm/MXCSR across a turn (:4116 a). The body's
 * own C is -mno-sse and never touches xmm, so the saved area is stable between save and restore. */
.global body_fxsave
.type body_fxsave, @function
body_fxsave:
    fxsave64 (%rdi)
    ret
.size body_fxsave, . - body_fxsave

.global body_fxrstor
.type body_fxrstor, @function
body_fxrstor:
    fxrstor64 (%rdi)
    ret
.size body_fxrstor, . - body_fxrstor

/* ── the sealed worker image: OUR worker.elf, embedded (NEVER a signed member, §9 mechanism 3) ───
 * The bytes the body's ELF64 loader reads FROM THE IMAGE (no filesystem walk). build.sh builds worker.elf
 * first, computes its sha256 (carried into the body as WORKER_IMG_SHA256HEX), and here the linker finds it
 * via -I<outdir>. The loader folds these bytes and refuses a load whose digest does not match. */
.section .rodata
.align 16
.global worker_image_start
worker_image_start:
    .incbin "worker.elf"
.global worker_image_end
worker_image_end:

/* ── C7 P3b-4f-i — the sealed STATIC SINGLE-THREAD PROVER: an ordinary gcc -static glibc program (NEVER a
 * signed member, §9 mechanism 3). Embedded ONLY when build.sh sealed one (PROVER_PRESENT); absent in the
 * worker-only builds. build.sh builds prover.elf with the guest's own gcc, carries its sha256 as
 * PROVER_IMG_SHA256HEX, and the body's loader folds these bytes and refuses a digest mismatch (L19). */
/* C7 P3b-6c (ii) MECHANICAL: the COMBINED build (BRIDGE) carries the interpreter as a MODULE (INTERP_FLOOR)
 * AND the lwIP worker as this incbin'd prover_image (NET_WORKER) — so the real prover.elf must be embedded
 * even though INTERP_FLOOR is set. The placeholder below is for the interpreter-ONLY floor (no incbin'd peer).*/
#if defined(PROVER_PRESENT) && (!defined(INTERP_FLOOR) || defined(BRIDGE) || defined(SOCKET_ACT))
.align 16
.global prover_image_start
prover_image_start:
    .incbin "prover.elf"
.global prover_image_end
prover_image_end:
#elif defined(INTERP_FLOOR)
/* C7 P3b-4c — THE INTERPRETER is not a separate incbin'd prover: it is the real /usr/bin/python3.12
 * inside the ONE sealed image, carried as a multiboot MODULE (the body reads it at mbi->mods, not from
 * the kernel image). A placeholder keeps prover_image_start/end defined so the unused static/concurrency
 * floor loaders still link; floor3_interp_run never reads them (it loads the program from the module). */
.align 16
.global prover_image_start
prover_image_start:
    .byte 0
.global prover_image_end
prover_image_end:
#endif

/* ── C7 P3b-6c (i) — the sealed MAPS PROVER: OUR small hand-written ring-3 test enclosure (a tests/ fixture,
 * NEVER a signed member, §9 mechanism 3 / I3). Embedded ONLY when build.sh sealed one (MAPS_PROVER); absent
 * in every other build. build.sh builds maps.elf from the tests/ fixture with the guest's own gcc, carries
 * its sha256 as MAPS_PROVER_IMG_SHA256HEX, and the body's loader folds these bytes and refuses a mismatch. */
#ifdef MAPS_PROVER
.align 16
.global maps_prover_image_start
maps_prover_image_start:
    .incbin "maps.elf"
.global maps_prover_image_end
maps_prover_image_end:
#endif

/* ── C7 P3b-4d / C7-MAINT-4D-BOOT-AS-MODULE — the sealed IMAGE (the guest's own ld.so + libc (+ companions)
 * for the 4d path; the interpreter + its stdlib for 4c/5b) is carried as a boot-time multiboot MODULE placed
 * high in physical memory and reached through the body's direct map (g_sealed_module_phys), NEVER embedded
 * here (NEVER a signed member, §9 mechanism 3 / I3 — a borrowed, hash-pinned, enclosed artifact). The ~2.26 MB
 * (4d) / ~21 MB (4c/5b) image is too large to incbin beneath the program's 0x400000 base: embedding it pushed
 * the body's own .bss (_bss_end) above CANONICAL_BASE, and the first post-paging global write triple-faulted at
 * the CR3 switch (FINDINGS.md F1/F2). The body digest-checks these bytes as a whole before load (B6) and serves
 * the files from them by path+offset+listing — no filesystem walk. A placeholder keeps sealed_image_start/end
 * defined so any unused loader path still links; floor3_run and floor3_interp_run both read the module, never
 * these bytes. The image (its bytes + its seal) is unchanged — only the carriage changed. */
#if defined(DYNAMIC_FLOOR)
.align 16
.global sealed_image_start
sealed_image_start:
    .byte 0
.global sealed_image_end
sealed_image_end:
#endif

/* a freestanding body never needs an executable stack (matches boot.S / isr.S). */
.section .note.GNU-stack, "", @progbits
