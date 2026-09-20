/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the worker's enclosure: shared declarations (C7 P3b-4a; design/54 §5 L18, §7 P3b-4a).
 *
 * The body hosts a program BENEATH THE SEAM, at user privilege, on the metal. This header declares the
 * three surfaces the enclosure is built from and the small request protocol OUR test worker speaks:
 *
 *   USER PRIVILEGE   a TSS (the ring-0 stack every crossing and every interrupt from ring 3 lands on),
 *                    a user code/data segment in the GDT, and a return into ring 3 (enter_ring3) — so a
 *                    hosted program runs UNPRIVILEGED and CANNOT reach the body's memory directly.
 *   THE CROSSING     the machine's own call crossing (SYSCALL/SYSRET, its MSRs) — the seam AT THE METAL.
 *                    A worker request is a SYSCALL; the entry stub (enclosure.S: syscall_entry) saves and
 *                    restores the worker's registers, switches to the body stack, dispatches into
 *                    body_request and SYSRETs back. Enclosure is a HARDWARE FACT; every request is a ROW.
 *   THE LOADER       an ELF64 loader (enclosure.c: enclosure_load_worker) that loads OUR test worker from
 *                    a SEALED IMAGE — bytes from the image, NO filesystem walk — after DIGEST-CHECKING it
 *                    (sha256, the SealedArtifact.verify idiom carried to the metal, archi :4085 (b)).
 *
 * THE CROSSING TRAIL (archi :4085 (a)). The body keeps its OWN append-only crossing trail — ONE ROW per
 * crossing SERVED or REFUSED, a refused row carrying the native answer returned. It is the BODY'S trail,
 * memory-resident and read back on the serial line; it is NEVER an unsigned row appended into the estate's
 * signed chain — the body holds no key, and the store's signature and the chain are the gate's, ABOVE the
 * seam (I1/L18). The trail's digest becomes a record row THROUGH THE GATE at P3b-4c/P3b-5, not here.
 *
 * THE REFUSAL. A request OUTSIDE the served set is refused as the worker's OWN NATIVE FAILURE ANSWER — the
 * SYSCALL's own -ENOSYS shape (-38, i.e. 0xffffffffffffffda), never a gov-os-shaped message — and recorded
 * as a row (I7/L18). This slice serves only a HANDFUL of requests with OUR small test worker; the full
 * forty-nine are P3b-4b and the borrowed interpreter is P3b-4c (NOT here).
 *
 * Hand-written and read whole (design/47 §2 I3, §9): no opaque code in the signed base. The built worker
 * IMAGE is a binary, NEVER a signed member (§9 mechanism 3, like the body .elf). Every build and boot is
 * the guest's nested qemu (L11 / EP-00 rule 9); nothing here runs on the host kernel. NO new act kind (the
 * crossing is HOW acts are requested, not a new act — ACT_KINDS stays twelve); founds nothing.
 */
#ifndef ENCLOSURE_H
#define ENCLOSURE_H

#include <stdint.h>
#include <stddef.h>

/* ── The small request protocol OUR test worker speaks (a HANDFUL, not the forty-nine) ───────────
 * The number is in %rax at the SYSCALL; args follow the measured x86_64 shape (a0=%rdi, a1=%rsi, ...).
 * The answer comes back in %rax on SYSRET. These are OUR test codes, not the full Linux syscall table. */
#define REQ_REPORT_PRIV  1u   /* a0 = the worker's %cs, a1 = its %ss (the machine-read privilege level)  */
#define REQ_ECHO         2u   /* a0 = a value; the body returns it (a round-trip the worker reads back)  */
#define REQ_PUTC         3u   /* a0 = a byte; the body writes it to serial (the worker's own announce)   */
#define REQ_TRESPASS_OK  4u   /* a0 = a value the worker read from BODY memory — reached ONLY if the     */
                              /*      hardware failed to fault a direct reach (the PLANT path)           */
#define REQ_EXIT         5u   /* end the worker (the served handful MUST include an EXIT, HOW rider)     */

/* A trail marker for a body-internal event that is a row but not a worker crossing: the sealed-image
 * LOAD (its refusal on a digest mismatch is a trail row, archi :4085 (b)). */
#define REQ_LOAD_MARKER  0xF0u

/* The native failure answer for an out-of-set request — the SYSCALL's own -ENOSYS shape (never a
 * gov-os message). 38 == ENOSYS on x86_64 Linux; the worker sees it as it natively would. */
#define ENOSYS_NATIVE    38u
#define NATIVE_FAIL_ANS  ((uint64_t)(-(int64_t)ENOSYS_NATIVE))   /* 0xffffffffffffffda */

/* ── The append-only crossing trail (memory-resident, read back on serial) ───────────────────────*/
#define TRAIL_MAX 64u
#define VERDICT_SERVED  1u
#define VERDICT_REFUSED 0u

struct trail_row {
    uint32_t seq;        /* 0-based append index                                              */
    uint32_t req;        /* the request number (or REQ_LOAD_MARKER for the load event)        */
    uint64_t arg;        /* the request's first argument                                      */
    uint64_t ans;        /* the answer returned (a refused row carries the native failure)    */
    uint32_t verdict;    /* VERDICT_SERVED | VERDICT_REFUSED                                   */
};

/* ── The recovery context (a tiny setjmp/longjmp, enclosure.S) — a worker fault or the EXIT request
 * unwinds from ring 3 (or the syscall stub) back to the body's enclosure driver. 8 quadwords:
 * rip, rbx, rbp, r12, r13, r14, r15, rsp. ────────────────────────────────────────────────────────*/
typedef uint64_t jmpctx_t[8];

uint64_t body_setjmp(jmpctx_t ctx);              /* 0 on the direct call; the longjmp value otherwise */
void     body_longjmp(jmpctx_t ctx, uint64_t v); /* never returns; body_setjmp returns v (v!=0)       */

/* ── The asm crossing/entry surface (enclosure.S) ───────────────────────────────────────────────*/
void syscall_entry(void);                        /* the SYSCALL entry stub (MSR_LSTAR points here)    */
void enter_ring3(uint64_t entry, uint64_t user_rsp, uint64_t a0, uint64_t a1);  /* iretq into the worker */
void load_tr(uint16_t sel);                      /* ltr — load the task register with the TSS selector */

/* the sealed worker image (an ELF64), embedded by enclosure.S's .incbin; NEVER a signed member. */
extern const uint8_t worker_image_start[];
extern const uint8_t worker_image_end[];

/* ── sha256 (sha256.c) — the sealed-image digest, folded on the metal ───────────────────────────*/
void sha256(const uint8_t *data, uint32_t len, uint8_t out[32]);

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6b — THE BORROWED TCP ENCLOSED (design/54 §5 L18/L5/L19/I3, §7 P3b-6b). A SECOND enclosed worker
 * — lwIP 2.2.0, the static NO_SYS build from the guest archive's SOURCE package, run UNMODIFIED — whose OWN
 * per-enclosure served set is the worker's WHOLE-PROCESS measured set (20 shapes, declared as data), plus
 * three body-native shapes the worker crosses on: send-frame, receive-frame, and a bounded wait. The
 * frames cross to 6a's NIC (net.c). Every frame is a row. NO new act kind (ACT_KINDS stays twelve).
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/

/* the NIC driver's callable frame API (net.c) — 6a's self-check + 6b's callable frame surface (:4295
 * precision 4 — HOW, mechanical; the fence note pre-authorises the net.c API). */
int net_wire_selfcheck(void);                          /* C7 P3b-6a: the ring-0 wire self-check           */
int net_nic_bringup(uint8_t mac_out[6]);               /* reset+negotiate the device; fill the offered MAC */
int net_send_frame(const void *frame, uint32_t len);   /* put ONE Ethernet frame on the wire (0 ok, -1 err)*/
int net_recv_frame(void *out, uint32_t max);           /* deliver ONE received frame, non-blocking (len/0/-1)*/

/* the body request numbers the borrowed worker's glue crosses on. Well above the Linux syscall range so
 * they never collide with a real syscall the static libc issues; on Linux they ENOSYS, so the worker runs
 * ONLY on the body. Served ONLY to the lwIP enclosure (serve.c, L18). */
#define REQ_SEND_FRAME 0x60000001ull   /* a0 = frame VA, a1 = length; puts the frame on 6a's NIC          */
#define REQ_RECV_FRAME 0x60000002ull   /* a0 = out VA, a1 = max; returns one received frame's length or 0 */
#define REQ_WAIT       0x60000003ull   /* a0 = ns; a bounded pause (the NEW performer, sized to 100 ms)   */
#define REQ_YIELD      0x60000004ull   /* C7 P3b-6c(iii): the op-server worker hands control back to the
                                        * bridge (persistent coroutine); returns with the next relayed op */

/* the two enclosures whose DECLARATIONS are distinct while the PERFORMERS are shared (:4302 precision b):
 * the interpreter's fifty-shape set and this worker's twenty-shape set are two lists; a shape in one only
 * is refused BY NAME to the other (L18). ENCL_INTERP (0) is the default — the interpreter path unchanged. */
#define ENCL_INTERP 0u
#define ENCL_LWIP   1u
extern uint32_t g_serve_enclosure;   /* which enclosure serve_request serves (the per-enclosure gate)     */

#ifdef NET_WORKER
/* the sealed static lwIP worker IS the prover_image (embedded by enclosure.S, sealed by build.sh);
 * NET_WORKER implies PROVER_PRESENT. floor_net_run loads it as the SECOND enclosure, brings up the NIC,
 * and runs the worker's OWN lwiperf client to open ONE guest-local connection through our NIC over nested
 * SLIRP; it reads the exchange + the frame trail back. 0 iff the checks pass; prints NET-WORKER: PASS. */
int floor_net_run(void);
#endif

/* ── The one entry the boot path calls (enclosure.c) ────────────────────────────────────────────*/
int enclosure_run(void);   /* 0 iff the whole enclosure self-check passes; prints ENCLOSURE: PASS/FAIL */

/* ── The FORTY-NINE serve run (C7 P3b-4b): the loaded worker re-entered in mode 2 makes each measured
 * request; body_request routes to serve_request (serve.c) while g_serve_phase is set. 0 iff every serve
 * check passes; prints SERVE: PASS/FAIL. Called by kmain after enclosure_run. */
int enclosure_serve_run(void);
extern int g_serve_phase;  /* 1 during the forty-nine run — body_request routes to serve_request */

/* the C request dispatcher the entry stub calls (num in %rax at the SYSCALL, mapped to these args). */
uint64_t body_request(uint64_t num, uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3, uint64_t a4);

/* ── C7 P3b-4f-i — THE STATIC SINGLE-THREAD FLOOR (design/54 §5 L19). Compiled in ONLY when build.sh has
 * sealed and embedded a static glibc prover (PROVER_PRESENT); absent in the worker-only P3b-4a/4b/4L/4m
 * builds, which are byte-for-byte unchanged. The body lays a real initial stack + auxv, runs the address-
 * space manager and the %fs/SSE bring-up, and enters an ORDINARY gcc -static glibc program at ring 3 to
 * prove the floor by RUNNING it (L19). The built prover IMAGE is a binary, NEVER a signed member. ───────*/
#ifdef PROVER_PRESENT
extern const uint8_t prover_image_start[];   /* the sealed static glibc prover (ELF64), embedded by enclosure.S */
extern const uint8_t prover_image_end[];
int floor_run(void);   /* 0 iff the prover ran to completion on the body; prints FLOOR: PASS/FAIL */
#endif

/* ── the worker-fault recovery state (enclosure.c) ──────────────────────────────────────────────
 * idt.c's isr_dispatch reads these: a ring-3 exception while a worker runs (g_in_worker, f->cs RPL 3)
 * is the hardware enforcing the enclosure — the body records it and body_longjmps to g_active_ctx
 * instead of halting, and the enclosure self-check reads what the machine did (L18). */
extern volatile int g_in_worker;
extern uint64_t *g_active_ctx;
extern volatile uint64_t g_worker_fault;    /* the caught worker fault's vector (0 = none)      */
extern volatile uint64_t g_worker_cr2;      /* its faulting address (CR2)                        */
extern volatile uint64_t g_worker_faultcs;  /* the CS the CPU pushed (its RPL == the worker CPL) */
extern volatile uint64_t g_worker_rip;      /* the faulting instruction pointer (C7 P3b-4f-ii diagnostic) */
extern volatile uint64_t g_worker_rsp, g_worker_rbp;

/* ── C7 P3b-4f-ii — THE CONCURRENCY FLOOR (design/54 §5 L19, §7 P3b-4f; :4116 a, :4107 a). Built
 * EDIT-IN-PLACE in enclosure.c/.h/.S (no new src/body file — the 30 stand, ATTESTED 87). Real thread
 * contexts (clone3), a preemptive scheduler on the P3b-3 timer, a real futex wait queue with timeouts and
 * wake, a thread's own end (SYS_exit) clearing + waking the child id (CHILD_CLEARTID). The switch is the
 * enclosure's tested body_setjmp/body_longjmp over a PER-THREAD kernel stack; on every switch RSP0 + the
 * syscall stack point at the incoming thread's kstack, its %fs base is written, its SSE state fxrstor'd.
 * The scheduler routines are serve.c's (g_sched_on path) real machinery behind the kept classification
 * router; idt.c's timer path calls sched_timer_tick. NO new act (ACT_KINDS stays twelve); founds nothing. */
struct isr_frame;   /* clock.h — the timer preempts on it (pointer only here) */

/* C7-MAINT-5B-THREAD-SLOT-RECLAIM: with a finished thread's slot RECLAIMED (sched_alloc reuses a safely
 * finished T_ZOMBIE slot), a program's thread demand is bounded by PEAK concurrency, not cumulative
 * creations. SCHED_MAX_THREADS then bounds PEAK, sized from the measured whole-ledger heaviest peak plus
 * headroom: ep28c_w1's submit_many(16) is 16 workers + main = 17 (the heaviest), the other concurrency
 * modules peak 6/3/2, and every green ledger module survived the old 8-slot cap so its peak was <=7. 32 =
 * peak 17 + headroom, well inside the 4 MiB _bss_end ceiling (linker.ld ASSERT: 32*(16 KiB kstack + one
 * thread struct) ~= 0.4 MiB added). The green ep28c_w1 boot is the on-body confirmation of this figure. */
#define SCHED_MAX_THREADS 32u
#define SCHED_KSTACK_SIZE 16384u
#define SCHED_PIT_HZ      1000u                          /* frequent preemption (a turn likely mid-loop)  */
#define SCHED_NS_PER_TICK (1000000000ull / SCHED_PIT_HZ) /* the timed wait's clock unit, from the PIT rate */

extern int g_sched_on;                       /* 1 during the concurrency floor (real preemptible contexts) */
extern uint32_t g_sched_switches;            /* total context switches (read back)                        */
extern uint32_t g_sched_preempts;            /* timer preemptions of a ring-3 context                     */
extern uint32_t g_sched_threads_created;     /* clone3 real contexts created                              */
extern uint32_t g_sched_exits;               /* threads ended via SYS_exit (child id cleared + woken)     */
extern uint32_t g_sched_switch_in_act;       /* MUST stay 0 — a switch while an act was in progress       */
extern volatile int g_in_act;                /* 1 while serve_request runs an act (the timer must not switch) */
extern uint32_t g_sched_cur_tid;             /* the currently-running thread's tid (diagnostic) */

/* the syscall crossing stashes the return rip/rflags here so clone3 can build the child's first context
 * (the child returns from the clone3 crossing to the same rip with rax=0). Set by syscall_entry. */
extern uint64_t g_syscall_ret_rip;
extern uint64_t g_syscall_ret_rflags;

/* C7 P3b-4d: the SYSCALL's SIXTH argument (r9), stashed by syscall_entry before the register shuffle —
 * mmap's file offset (rdi,rsi,rdx,r10,r8,r9 = addr,len,prot,flags,fd,offset), which body_request's 5-arg
 * (a0..a4) shape otherwise drops. serve.c reads it for ld.so's file-backed segment maps. */
extern uint64_t g_syscall_a5;

void     sched_init(void);                               /* the main thread becomes the first context     */
void     sched_timer_tick(struct isr_frame *f);          /* the timer path (idt.c) — expire + preempt     */
uint64_t sched_clone3(uint64_t cl_args_ptr, uint64_t ret_rip, uint64_t func, uint64_t arg);
void     sched_thread_exit(void);                        /* SYS_exit — clear+wake the child id, tear down */
uint64_t sched_futex(uint64_t uaddr, uint64_t op, uint64_t val, uint64_t timeout_ptr);
void     sched_set_current_fs(uint64_t base);            /* record the current thread's %fs (arch_prctl)  */
uint64_t sched_now_ns(void);                             /* the body clock (serve_clock_gettime lays same) */
void     body_set_kernel_stack(uint64_t top);            /* RSP0 + the syscall stack -> the given top      */

#ifdef PROVER_PRESENT
int      floor2_run(void);                               /* the concurrency floor: run the threaded prover */
#endif

/* ── C7 P3b-4d — THE DYNAMIC LOADER + THE SEALED IMAGE (design/54 §5 L19, §7 P3b-4d; B6). Compiled in ONLY
 * when build.sh sealed a DYNAMIC prover + a sealed image (DYNAMIC_FLOOR). On the concurrency floor (real
 * threads + scheduler + futex), the body brings up the DYNAMIC path: the sealed image as a read-only
 * filesystem of ld.so + libc + companions (digest-checked before load); the loader honours the program's
 * PT_INTERP, loads the requested ld.so from the sealed image, lays the SEVEN-key auxiliary vector (AT_BASE
 * added), and hands over to the linker, which resolves libc from the sealed image by path+offset. PROVEN,
 * per L19, by an ordinary `gcc -pthread -no-pie` DYNAMICALLY-linked glibc program whose start-up now goes
 * through the real linker. The sealed image + the borrowed ld.so/libc are ENCLOSED (hash-pinned, never a
 * member, I3); the built prover is a test artifact (§9 mechanism 3). NO new act (ACT_KINDS stays twelve);
 * founds nothing. NOT the interpreter (P3b-4c). ──────────────────────────────────────────────────────*/
#ifdef DYNAMIC_FLOOR
/* the DYNAMIC prover is the sealed prover_image (prover_image_start/end, built `gcc -pthread -no-pie` by
 * build.sh — ET_EXEC at 0x400000, PT_INTERP present); DYNAMIC_FLOOR implies PROVER_PRESENT. The sealed
 * IMAGE (ld.so + libc + companions as one GOVSIMG1 archive) is embedded separately. Both are ENCLOSED
 * artifacts, NEVER signed members (§9 mechanism 3 / I3). */
extern const uint8_t sealed_image_start[];       /* the sealed image (GOVSIMG1: ld.so + libc + companions) */
extern const uint8_t sealed_image_end[];
int floor3_run(void);   /* 0 iff the dynamic prover ran to completion through the real linker; FLOOR3: PASS */
#ifdef INTERP_FLOOR
int floor3_interp_run(void);  /* C7 P3b-4c: 0 iff the REAL unmodified python3 ran on the body (print(2+2)
                               * + a thread) from the sealed module through the real linker; FLOOR3C: PASS */
#endif
#endif

/* the ring-3 entries the scheduler uses (enclosure.S), interrupts ENABLED (the program is preemptible). */
void enter_ring3_main(uint64_t entry, uint64_t user_rsp);
void enter_ring3_thread(uint64_t entry, uint64_t user_rsp, uint64_t func, uint64_t arg);
/* per-thread SSE state save/restore at the switch (fxsave64/fxrstor64 over a 512-byte 16-aligned area). */
void body_fxsave(void *area);
void body_fxrstor(void *area);

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6c (i) — PER-ENCLOSURE ADDRESS MAPS (design/54 §5 L20/L18, §9 Q11/I3). Each resident enclosure
 * holds its OWN page-table hierarchy handle (its CR3). The hierarchies SHARE the kernel half (the low
 * identity + the higher-half direct map) and have a PRIVATE user half, so two enclosures at base 0x400000
 * coexist with no aliasing; the map is swapped at the coroutine hand-off. Implemented in vmm.c; the handle
 * is a plain CR3 value (a pml4 physical address). ────────────────────────────────────────────────────*/
uint64_t vmm_boot_cr3(void);                        /* the boot map's CR3 (the body's own static pml4)      */
uint64_t vmm_map_new(void);                         /* a fresh hierarchy sharing the kernel half; 0 on OOM  */
void     vmm_switch(uint64_t cr3);                  /* the hand-off primitive: load CR3 + re-point the map  */
uint64_t vmm_query_in(uint64_t cr3, uint64_t virt); /* the PTE mapping virt IN the map at cr3 (0 if absent) */
int      vmm_map_kernel_half_matches(uint64_t cr3); /* 1 iff cr3 carries the kernel half byte-identical     */

#ifdef MAPS_PROVER
/* the sealed maps-prover IMAGE (a bare static ring-3 test enclosure with a writable sentinel word at the
 * canonical base 0x400000 and code above it), embedded by enclosure.S's .incbin from a tests/ fixture —
 * CONTENT, NEVER a signed member (§9 mechanism 3 / I3). floor_maps_run loads it into TWO per-enclosure maps
 * and proves memory isolation, the map swap and the fault-per-map (design/54 §7 P3b-6c slice i). */
extern const uint8_t maps_prover_image_start[];
extern const uint8_t maps_prover_image_end[];
int floor_maps_run(void);   /* 0 iff the per-enclosure-map self-check passes; prints MAPS: PASS/FAIL */
#endif

#ifdef BRIDGE
/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6c slice (ii) — THE COMBINED BUILD + THE COROUTINE BRIDGE (design/54 §5 L18/L19, §9 Q11/I3;
 * §7 P3b-6c slice ii; countersign archi :4550). The body boots the sealed interpreter (P3b-4c, the sealed
 * -initrd module) AND the enclosed lwIP worker (P3b-6b, the incbin'd prover_image) RESIDENT TOGETHER, each
 * in its OWN slice-(i) map (vmm_map_new / vmm_switch). A ring-0 coroutine bridge relays ONE operation from
 * the interpreter to the worker and back across the map swap: the interpreter issues the operation, the
 * bridge swaps to the worker's map + kstack (slice i + the per-thread kstack), the worker performs it and
 * produces its OWN answer WITNESSED (never a fabricated reply, L19), the bridge swaps back, the interpreter
 * receives the worker's real answer. A ring-3 fault mid-relay recovers per map (L18) and the bridge hands
 * the WAITING interpreter an error answer (archi :4550) — never leaves it suspended. BRIDGE implies
 * INTERP_FLOOR + NET_WORKER (both PROVER_PRESENT). NO new act (ACT_KINDS stays twelve); founds nothing;
 * the prover glue is a tests/ fixture (ATTESTED stays 88 — no new src/body member). ────────────────────*/
extern int g_bridge_active;   /* 1 while the interpreter runs under the bridge — serve.c routes its ONE
                               * relayed operation (SYS_socket) to bridge_relay instead of the refusal.   */
/* the ring-0 relay: from the interpreter's crossing (serve.c), cross to the resident worker under its own
 * map + kstack, run it to produce the answer (witnessed), cross back, return the worker's REAL answer (or,
 * on a worker fault mid-relay, an error answer — the interpreter is never left waiting, archi :4550). */
uint64_t bridge_relay(uint64_t num, uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3, uint64_t a4);
int floor_bridge_run(void);   /* 0 iff the combined-boot + one-operation-round-trip self-check passes */
#endif

#ifdef SOCKET_ACT
/* C7 P3b-6c slice (iii) — THE SOCKET ACT. The interpreter drives gov-os's own client-connection act; serve.c
 * relays each socket-family shape across the slice-(ii) bridge to the enclosed lwIP worker (a PERSISTENT
 * coroutine, one connection across relays). The bridge is OUR code; the lwIP core is byte-unmodified (I3). */
extern int g_sa_active;    /* 1 while the interpreter runs under the socket-act bridge (serve.c reads it)   */
extern int g_sa_sock_fd;   /* the fd SOP_SOCKET returned — only THIS fd's shapes relay (serve.c reads it)   */
/* the socket ops the bridge relays (MUST match the worker glue's SOP_*). */
#define SA_OP_SOCKET    1ull
#define SA_OP_IOCTL_NB  2ull
#define SA_OP_CONNECT   3ull
#define SA_OP_GETSOERR  4ull
#define SA_OP_POLL      5ull
#define SA_OP_SEND      6ull
#define SA_OP_RECV      7ull
#define SA_OP_CLOSE     8ull
uint64_t bridge_relay_sock(uint64_t op, uint64_t a0, uint64_t a1, uint64_t a2,
                           const void *in_ptr, uint32_t in_len, void *out_ptr, uint32_t out_max);
void sa_worker_yield(void); /* the worker's REQ_YIELD hand-off back to the bridge                            */
int floor_socket_act_run(void);
#endif

#endif /* ENCLOSURE_H */
