/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the worker's enclosure driver, on the metal (C7 P3b-4a; design/54 §5 L18, §7 P3b-4a).
 *
 * Brings up USER PRIVILEGE (a TSS + user segments + a return into ring 3), THE CROSSING (the SYSCALL/
 * SYSRET MSRs, dispatched here in body_request), and THE BODY'S OWN ELF64 LOADER (a sealed, digest-checked
 * image loaded from bytes, no filesystem walk). It then hosts OUR small test worker beneath the seam,
 * records every request as a ROW of the body's own append-only crossing trail, refuses an out-of-set
 * request as the worker's OWN native failure (-ENOSYS) and records that too, and proves the boundary is a
 * HARDWARE FACT: a direct reach at body memory is FAULTED by the machine and caught by the body.
 *
 * Hand-written and read whole (design/47 §2 I3, §9): no opaque code in the signed base. The built worker
 * IMAGE is never a member (§9 mechanism 3). Every build and boot is the guest's nested qemu (L11). NO new
 * act (the crossing is HOW acts are requested — ACT_KINDS stays twelve); founds nothing.
 *
 * The A2/A3 near-misses (build.sh -D — a check that cannot fail is not a check):
 *   PLANT_WORKER_RING0        the worker returns into ring 0 -> CHECK RING3 reds (enclosure.S)
 *   PLANT_BODY_USER_ACCESSIBLE the body page is mapped USER -> the direct reach does NOT fault -> CHECK TRESPASS reds
 *   PLANT_NO_SYSCALL_MSR      the SYSCALL machinery is not enabled -> the worker's SYSCALL #UDs -> CHECK CROSSING reds
 *   PLANT_OUTOFSET_SERVED     the out-of-set request is SERVED -> CHECK REFUSAL reds
 *   PLANT_REFUSAL_NOT_NATIVE  the out-of-set is refused with a gov-os-shaped answer -> CHECK REFUSAL reds
 *   PLANT_TRAIL_SKIP          a crossing is not recorded as a row -> CHECK TRAIL reds
 *   PLANT_WORKER_IMAGE_TAMPER the sealed image's bytes are changed -> the loader REFUSES it (LOAD: REFUSED)
 */
#include "body.h"
#include "clock.h"      /* gdt_flush (isr.S), interrupts_disable */
#include "enclosure.h"
#include "serve.h"      /* the forty-nine serve dispatcher + driver (C7 P3b-4b) */

/* The carried digest of the sealed worker image (build.sh: sha256 of worker.elf). A never-matching
 * fallback keeps the build honest if the define is somehow absent (the loader then refuses). */
#ifndef WORKER_IMG_SHA256HEX
#define WORKER_IMG_SHA256HEX "0000000000000000000000000000000000000000000000000000000000000000"
#endif

/* worker/stack/secret user-virtual addresses — all ABOVE the body's low-1-GiB identity map (which is
 * supervisor), so the loader maps them on fresh page tables. */
#define USER_STACK_BASE 0x50000000ull
#define USER_STACK_TOP  0x50004000ull   /* four user pages */
#define SECRET_VA       0x60000000ull   /* a body-owned page the trespass probe reaches directly */

/* ── the crossing/enclosure state (read back on serial) ──────────────────────────────────────────*/
uint64_t g_crossings;                    /* incremented by syscall_entry (enclosure.S), EVERY crossing */
uint64_t saved_user_rsp;                 /* enclosure.S scratch: the worker's rsp across a crossing     */
uint64_t syscall_kernel_rsp;             /* the body's syscall stack top (set at MSR install)          */

volatile int g_in_worker;                /* 1 while a worker runs — a ring-3 fault is recovered, not halted */
int g_serve_phase;                        /* 1 during the forty-nine run — body_request routes to serve_request */
uint64_t *g_active_ctx;                  /* the recovery context a worker fault / EXIT longjmps to      */
volatile uint64_t g_worker_fault;        /* the vector of the last caught worker fault (0 = none)       */
volatile uint64_t g_worker_cr2;          /* the faulting address (CR2) of the last caught worker fault  */
volatile uint64_t g_worker_faultcs;      /* the CS the CPU pushed at the fault (its RPL == the worker CPL) */
volatile uint64_t g_worker_rip;          /* the faulting instruction pointer (C7 P3b-4f-ii diagnostic)  */
volatile uint64_t g_worker_rsp, g_worker_rbp;  /* fault diagnostic */

/* C7 P3b-4f-ii: the crossing's return rip/rflags, stashed by syscall_entry so clone3 can build a child's
 * first context (the child returns from the clone3 crossing to this rip, rax=0). */
uint64_t g_syscall_ret_rip;
uint64_t g_syscall_ret_rflags;

/* C7 P3b-4d: the crossing's SIXTH arg (r9), stashed by syscall_entry — mmap's file offset. */
uint64_t g_syscall_a5;

static jmpctx_t g_ctx;                    /* the recovery point in enclosure_run                        */

static uint64_t g_worker_entry;           /* the worker's ELF e_entry (the loader sets it)              */
static uint64_t g_user_rsp;               /* the worker's user stack top                                */
static uint64_t g_secret_va;              /* the body address the trespass probe reads                  */

static uint64_t g_rep_cs, g_rep_ss;       /* the worker's own %cs/%ss (REQ_REPORT_PRIV) — the machine read */
static int      g_worker_exited;          /* the worker ended via REQ_EXIT                              */
static uint64_t g_outofset_ans;           /* the answer to the out-of-set request                       */
static uint32_t g_outofset_verdict;       /* its verdict (must be REFUSED)                              */
static int      g_outofset_seen;          /* the out-of-set request reached the dispatcher              */
static int      g_trespass_reported;      /* the trespass probe reported a successful read (plant path) */
static uint64_t g_trespass_value;         /* what it read, if any                                       */

static struct trail_row g_trail[TRAIL_MAX];
static uint32_t g_trail_n;                 /* rows appended (append-only)                                */
static uint32_t g_trail_crossings;         /* crossing rows (excludes the load marker)                   */

/* ── the append-only crossing trail ─────────────────────────────────────────────────────────────*/
static void trail_append(uint32_t req, uint64_t arg, uint64_t ans, uint32_t verdict) {
    if (g_trail_n < TRAIL_MAX) {
        g_trail[g_trail_n].seq = g_trail_n;
        g_trail[g_trail_n].req = req;
        g_trail[g_trail_n].arg = arg;
        g_trail[g_trail_n].ans = ans;
        g_trail[g_trail_n].verdict = verdict;
        g_trail_n++;
    }
    if (req != REQ_LOAD_MARKER) {
        g_trail_crossings++;
    }
}

/* ── the request dispatcher — the C entry the crossing (syscall_entry) calls ─────────────────────
 * num is the request number (was in %rax at the SYSCALL); a0.. are the args. The answer goes back in
 * %rax on SYSRET. EXIT never returns — it unwinds to the enclosure driver. Every request is a row. */
uint64_t body_request(uint64_t num, uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3, uint64_t a4) {
    /* C7 P3b-4b: during the forty-nine run, the crossing is served by serve_request (serve.c), which
     * classifies by PURPOSE and witnesses each crossing as one UNSIGNED row of the body's serve trail.
     * The P3b-4a handful path below is byte-identical when g_serve_phase is 0 (its meaning unchanged). */
    if (g_serve_phase) {
        return serve_request(num, a0, a1, a2, a3, a4);
    }
    (void)a2; (void)a3; (void)a4;
    uint64_t ans = 0;
    uint32_t verdict = VERDICT_SERVED;

    switch (num) {
    case REQ_REPORT_PRIV:
        g_rep_cs = a0; g_rep_ss = a1; ans = 0;
        break;
    case REQ_ECHO:
        ans = a0;                          /* the round-trip: the body sends the argument back */
        break;
    case REQ_PUTC:
        serial_putc((char)(a0 & 0xFFu)); ans = 0;
        break;
    case REQ_TRESPASS_OK:
        g_trespass_reported = 1; g_trespass_value = a0; ans = 0;   /* reached ONLY on the plant path */
        break;
    case REQ_EXIT:
        g_worker_exited = 1;
        trail_append(REQ_EXIT, a0, 0, VERDICT_SERVED);
        body_longjmp(g_active_ctx, 1);     /* the worker ended — unwind to the body (never returns) */
        break;                             /* unreachable */
    default:                               /* OUT-OF-SET — not served this slice */
#if defined(PLANT_OUTOFSET_SERVED)
        ans = 0; verdict = VERDICT_SERVED;                 /* the fault: serve the unserved request */
#elif defined(PLANT_REFUSAL_NOT_NATIVE)
        ans = 0xDEADull; verdict = VERDICT_REFUSED;        /* the fault: a gov-os-shaped refusal, not native */
#else
        ans = NATIVE_FAIL_ANS; verdict = VERDICT_REFUSED;  /* the native -ENOSYS answer (0xffff…ffda) */
#endif
        g_outofset_ans = ans; g_outofset_verdict = verdict; g_outofset_seen = 1;
        break;
    }

#if defined(PLANT_TRAIL_SKIP)
    if (num != 0x63ull) {                  /* the fault: the out-of-set request (99) is not recorded */
        trail_append((uint32_t)num, a0, ans, verdict);
    }
#else
    trail_append((uint32_t)num, a0, ans, verdict);
#endif
    return ans;
}

/* ── the GDT (with user segments + a 64-bit TSS) and the task register ──────────────────────────*/
struct tss64 {
    uint32_t reserved0;
    uint64_t rsp0;      /* the ring-0 stack a crossing/interrupt from ring 3 lands on (HOW rider) */
    uint64_t rsp1, rsp2, reserved1;
    uint64_t ist1, ist2, ist3, ist4, ist5, ist6, ist7;
    uint64_t reserved2;
    uint16_t reserved3;
    uint16_t iomap_base;
} __attribute__((packed));

static uint64_t g_encl_gdt[8];   /* null / kcode64 / kdata / ucode32 / udata / ucode64 / TSS(2 slots) */
static struct tss64 g_tss;
static uint8_t g_exc_stack[16384]     __attribute__((aligned(16)));   /* RSP0 — faults from ring 3     */
static uint8_t g_syscall_stack[16384] __attribute__((aligned(16)));   /* the SYSCALL kernel stack      */

struct dtp { uint16_t limit; uint64_t base; } __attribute__((packed));

static void set_tss_desc(int idx, uint64_t base, uint32_t limit) {
    uint64_t low = (uint64_t)(limit & 0xFFFFu)
                 | ((uint64_t)(base & 0xFFFFu) << 16)
                 | ((uint64_t)((base >> 16) & 0xFFu) << 32)
                 | ((uint64_t)0x89u << 40)                 /* P=1, type=9 (available 64-bit TSS)   */
                 | ((uint64_t)((limit >> 16) & 0xFu) << 48)
                 | ((uint64_t)((base >> 24) & 0xFFu) << 56);
    g_encl_gdt[idx]     = low;
    g_encl_gdt[idx + 1] = (base >> 32) & 0xFFFFFFFFull;
}

static void enclosure_gdt_tss_install(void) {
    g_encl_gdt[0] = 0x0000000000000000ull;                 /* null                                  */
    g_encl_gdt[1] = 0x00209A0000000000ull;                 /* 0x08 kernel code64 (DPL0, L=1)        */
    g_encl_gdt[2] = 0x0000920000000000ull;                 /* 0x10 kernel data (DPL0)               */
    g_encl_gdt[3] = 0x00CFFA000000FFFFull;                 /* 0x18 user code32 (DPL3) — STAR base    */
    g_encl_gdt[4] = 0x0000F20000000000ull;                 /* 0x20 user data (DPL3)                 */
    g_encl_gdt[5] = 0x0020FA0000000000ull;                 /* 0x28 user code64 (DPL3, L=1)          */

    uint8_t *t = (uint8_t *)&g_tss;
    for (uint32_t i = 0; i < sizeof(g_tss); i++) { t[i] = 0; }
    g_tss.rsp0 = (uint64_t)(uintptr_t)(g_exc_stack + sizeof(g_exc_stack));
    g_tss.iomap_base = (uint16_t)sizeof(g_tss);            /* no I/O bitmap                          */
    set_tss_desc(6, (uint64_t)(uintptr_t)&g_tss, (uint32_t)(sizeof(g_tss) - 1));   /* 0x30 TSS       */

    struct dtp gdtp;
    gdtp.limit = (uint16_t)(sizeof(g_encl_gdt) - 1);
    gdtp.base  = (uint64_t)(uintptr_t)&g_encl_gdt[0];
    gdt_flush((uint64_t)(uintptr_t)&gdtp);                 /* lgdt + reload segments (isr.S)         */
    load_tr(0x30);                                          /* the TSS selector (index 6 * 8)        */
}

/* ── the SYSCALL/SYSRET MSRs ─────────────────────────────────────────────────────────────────────*/
static inline void wrmsr(uint32_t msr, uint64_t val) {
    uint32_t lo = (uint32_t)val, hi = (uint32_t)(val >> 32);
    __asm__ volatile("wrmsr" : : "c"(msr), "a"(lo), "d"(hi));
}
static inline uint64_t rdmsr(uint32_t msr) {
    uint32_t lo, hi;
    __asm__ volatile("rdmsr" : "=a"(lo), "=d"(hi) : "c"(msr));
    return ((uint64_t)hi << 32) | lo;
}

static void enclosure_msr_install(void) {
    syscall_kernel_rsp = (uint64_t)(uintptr_t)(g_syscall_stack + sizeof(g_syscall_stack));
#ifndef PLANT_NO_SYSCALL_MSR
    wrmsr(0xC0000080u, rdmsr(0xC0000080u) | 1u);            /* EFER.SCE — enable SYSCALL/SYSRET      */
    wrmsr(0xC0000081u, ((uint64_t)0x18u << 48) | ((uint64_t)0x08u << 32));   /* STAR: user 0x18 / kernel 0x08 */
    wrmsr(0xC0000082u, (uint64_t)(uintptr_t)syscall_entry);/* LSTAR: the entry stub                 */
    wrmsr(0xC0000084u, 0x700u);                            /* SFMASK: clear TF|IF|DF on entry       */
#else
    /* A2 near-miss: EFER.SCE stays clear, so the worker's SYSCALL raises #UD — the crossing never
     * happens and CHECK CROSSING reds. The TSS is still installed, so the #UD from ring 3 lands on
     * RSP0 and the body catches it. */
#endif
}

/* C7 P3b-4f-ii: point the ring-0 landing stacks (the TSS's RSP0 for a ring-3 interrupt, and the SYSCALL
 * kernel stack) at the given top. Called on every context switch so the incoming thread's crossings and
 * interrupts land on ITS OWN kernel stack (the switch is body_setjmp/body_longjmp over that stack). */
void body_set_kernel_stack(uint64_t top) {
    g_tss.rsp0 = top;
    syscall_kernel_rsp = top;
}

/* ── the ELF64 loader: a sealed image, digest-checked, mapped as USER pages ─────────────────────*/
struct elf64_ehdr {
    uint8_t  e_ident[16];
    uint16_t e_type, e_machine;
    uint32_t e_version;
    uint64_t e_entry, e_phoff, e_shoff;
    uint32_t e_flags;
    uint16_t e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx;
} __attribute__((packed));

struct elf64_phdr {
    uint32_t p_type, p_flags;
    uint64_t p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align;
} __attribute__((packed));

#define PT_LOAD 1u

static int hexval(char c) {
    if (c >= '0' && c <= '9') { return c - '0'; }
    if (c >= 'a' && c <= 'f') { return c - 'a' + 10; }
    if (c >= 'A' && c <= 'F') { return c - 'A' + 10; }
    return -1;
}

static int digest_matches_hex(const uint8_t *got, const char *hex) {
    for (int i = 0; i < 32; i++) {
        int hi = hexval(hex[i * 2]);
        int lo = hexval(hex[i * 2 + 1]);
        if (hi < 0 || lo < 0) { return 0; }
        if (got[i] != (uint8_t)((hi << 4) | lo)) { return 0; }
    }
    return hex[64] == '\0';
}

static void put_hex_digest(const uint8_t *b, uint32_t n) {
    static const char h[] = "0123456789abcdef";
    for (uint32_t i = 0; i < n; i++) {
        serial_putc(h[(b[i] >> 4) & 0xF]);
        serial_putc(h[b[i] & 0xF]);
    }
}

/* map [vaddr, vaddr+memsz) as USER pages, copying the file bytes [vaddr, vaddr+filesz) from the image. */
static int map_segment(uint64_t vaddr, uint64_t offset, uint64_t filesz, uint64_t memsz, const uint8_t *img) {
    uint64_t va_start = vaddr & ~0xFFFull;
    uint64_t va_end   = (vaddr + memsz + 0xFFFull) & ~0xFFFull;
    for (uint64_t page = va_start; page < va_end; page += 0x1000ull) {
        uint32_t frame = pmm_alloc();
        if (frame == 0) { return -1; }
        if (vmm_map_user(page, (uint64_t)frame) != 0) { return -1; }
        uint8_t *dst = (uint8_t *)phys_to_virt(frame);     /* the frame, through the body's direct map */
        for (int i = 0; i < 4096; i++) { dst[i] = 0; }     /* zero (covers .bss)                    */
        uint64_t copy_lo = (page > vaddr) ? page : vaddr;
        uint64_t copy_hi = vaddr + filesz;
        if (copy_hi > page + 0x1000ull) { copy_hi = page + 0x1000ull; }
        if (copy_lo < copy_hi) {
            uint64_t n = copy_hi - copy_lo;
            uint64_t src = offset + (copy_lo - vaddr);
            uint64_t d   = copy_lo - page;
            for (uint64_t i = 0; i < n; i++) { dst[d + i] = img[src + i]; }
        }
    }
    return 0;
}

static int enclosure_load_worker(void) {
    const uint8_t *img = worker_image_start;
    uint32_t img_len = (uint32_t)(worker_image_end - worker_image_start);

    /* THE SEAL: fold the image bytes and refuse a load whose digest does not match the carried value
     * (the SealedArtifact.verify idiom carried to the metal, archi :4085 (b)). */
    uint8_t got[32];
    sha256(img, img_len, got);
    serial_puts("WORKER-IMG-LEN: 0x"); serial_puthex32(img_len); serial_puts("\n");
    serial_puts("WORKER-IMG-SHA256: "); put_hex_digest(got, 32); serial_puts("\n");
    if (!digest_matches_hex(got, WORKER_IMG_SHA256HEX)) {
        serial_puts("LOAD: REFUSED (digest mismatch — sealed image not the sealed bytes)\n");
        trail_append(REQ_LOAD_MARKER, 0, NATIVE_FAIL_ANS, VERDICT_REFUSED);
        return -1;
    }
    serial_puts("LOAD: OK (digest matches the seal)\n");
    trail_append(REQ_LOAD_MARKER, img_len, 0, VERDICT_SERVED);

    /* parse the ELF64 and map its PT_LOAD segments (bytes FROM THE IMAGE — no filesystem walk). */
    const struct elf64_ehdr *eh = (const struct elf64_ehdr *)img;
    if (!(eh->e_ident[0] == 0x7f && eh->e_ident[1] == 'E'
          && eh->e_ident[2] == 'L' && eh->e_ident[3] == 'F')) { return -1; }
    if (eh->e_ident[4] != 2) { return -1; }                /* ELFCLASS64                            */
    if (eh->e_machine != 62) { return -1; }                /* EM_X86_64                             */
    const struct elf64_phdr *ph = (const struct elf64_phdr *)(img + eh->e_phoff);
    for (int i = 0; i < eh->e_phnum; i++) {
        if (ph[i].p_type == PT_LOAD) {
            if (map_segment(ph[i].p_vaddr, ph[i].p_offset, ph[i].p_filesz, ph[i].p_memsz, img) != 0) {
                return -1;
            }
        }
    }
    g_worker_entry = eh->e_entry;

    /* the worker's user stack (USER pages). */
    for (uint64_t p = USER_STACK_BASE; p < USER_STACK_TOP; p += 0x1000ull) {
        uint32_t f = pmm_alloc();
        if (f == 0) { return -1; }
        if (vmm_map_user(p, (uint64_t)f) != 0) { return -1; }
    }
    g_user_rsp = USER_STACK_TOP - 16;

    /* a body-owned page the trespass probe reaches directly. Supervisor by default (a ring-3 read
     * faults); USER under the plant (the machine fails to fault — CHECK TRESPASS reds). */
    uint32_t sf = pmm_alloc();
    if (sf == 0) { return -1; }
#ifdef PLANT_BODY_USER_ACCESSIBLE
    if (vmm_map_user(SECRET_VA, (uint64_t)sf) != 0) { return -1; }
#else
    if (vmm_map(SECRET_VA, (uint64_t)sf) != 0) { return -1; }
#endif
    *(volatile uint32_t *)phys_to_virt(sf) = 0xB0D15EC5u;  /* a known body value at the secret page (direct map) */
    g_secret_va = SECRET_VA;
    return 0;
}

/* ── the trail readback on serial ───────────────────────────────────────────────────────────────*/
static void enclosure_print_trail(void) {
    serial_puts("TRAIL-ROWS: 0x"); serial_puthex32(g_trail_n); serial_puts("\n");
    for (uint32_t i = 0; i < g_trail_n; i++) {
        serial_puts("TRAIL row=0x");    serial_puthex32(g_trail[i].seq);
        serial_puts(" req=0x");         serial_puthex32(g_trail[i].req);
        serial_puts(" arg=0x");         serial_puthex64(g_trail[i].arg);
        serial_puts(" ans=0x");         serial_puthex64(g_trail[i].ans);
        serial_puts(g_trail[i].verdict == VERDICT_SERVED ? " SERVED\n" : " REFUSED\n");
    }
}

/* ── the one entry the boot path calls ──────────────────────────────────────────────────────────*/
int enclosure_run(void) {
    interrupts_disable();   /* a deterministic worker phase (the clock slice proved interrupts already) */
    serial_puts("ENCLOSURE: bring-up (user privilege, the crossing, the loader)\n");

    enclosure_gdt_tss_install();
    enclosure_msr_install();

    if (enclosure_load_worker() != 0) {
        serial_puts("ENCLOSURE: FAIL (the sealed image was refused at load)\n");
        enclosure_print_trail();
        return 1;
    }

    /* the MAIN worker run: a handful of requests, then EXIT (the served handful MUST include EXIT). */
    g_active_ctx = g_ctx;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        enter_ring3(g_worker_entry, g_user_rsp, 0 /*mode: main*/, 0);
        /* unreachable — the worker EXITs (longjmp 1) or faults (longjmp 2) */
    }
    g_in_worker = 0;
    int crossing_ok = (jv == 1 && g_worker_exited && g_worker_fault == 0);

    /* the TRESPASS probe: a direct reach at body memory — the machine MUST fault it. */
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t tv = body_setjmp(g_ctx);
    if (tv == 0) {
        enter_ring3(g_worker_entry, g_user_rsp, 1 /*mode: trespass*/, g_secret_va);
        /* unreachable — the read faults (#PF, longjmp 2), or (plant) it returns and the worker EXITs */
    }
    g_in_worker = 0;
    int trespass_faulted = (tv == 2 && g_worker_fault == 14 && !g_trespass_reported);

    /* ── the checks (each machine-read, each with a plant that reds it) ── */
    int ring_ok     = ((g_rep_cs & 3u) == 3u) && ((g_rep_ss & 3u) == 3u);
    int refusal_ok  = g_outofset_seen
                   && (g_outofset_verdict == VERDICT_REFUSED)
                   && (g_outofset_ans == NATIVE_FAIL_ANS);
    int trail_ok    = (g_crossings > 0) && (g_crossings == g_trail_crossings);

    serial_puts("WORKER-CS: 0x");      serial_puthex32((uint32_t)g_rep_cs);
    serial_puts(" WORKER-SS: 0x");     serial_puthex32((uint32_t)g_rep_ss); serial_puts("\n");
    serial_puts("CROSSINGS: 0x");      serial_puthex32((uint32_t)g_crossings); serial_puts("\n");
    serial_puts("OUTOFSET-ANS: 0x");   serial_puthex64(g_outofset_ans); serial_puts("\n");
    serial_puts("TRESPASS-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
    serial_puts(" cr2=0x");            serial_puthex64(g_worker_cr2);
    serial_puts(" faultcs=0x");        serial_puthex32((uint32_t)g_worker_faultcs); serial_puts("\n");

    serial_puts(ring_ok         ? "CHECK RING3: PASS\n"     : "CHECK RING3: FAIL\n");
    serial_puts(crossing_ok     ? "CHECK CROSSING: PASS\n"  : "CHECK CROSSING: FAIL\n");
    serial_puts(refusal_ok      ? "CHECK REFUSAL: PASS\n"   : "CHECK REFUSAL: FAIL\n");
    serial_puts(trail_ok        ? "CHECK TRAIL: PASS\n"     : "CHECK TRAIL: FAIL\n");
    serial_puts(trespass_faulted? "CHECK TRESPASS: PASS\n"  : "CHECK TRESPASS: FAIL\n");

    enclosure_print_trail();

    int all = ring_ok && crossing_ok && refusal_ok && trail_ok && trespass_faulted;
    serial_puts(all ? "ENCLOSURE: PASS\n" : "ENCLOSURE: FAIL\n");
    return all ? 0 : 1;
}

/* ── the FORTY-NINE serve run (C7 P3b-4b) ────────────────────────────────────────────────────────────
 * After the enclosure self-check, the body re-enters the SAME loaded worker at ring 3 in mode 2. The
 * worker makes each of the measured requests in its measured x86_64 shape; body_request routes to
 * serve_request (serve.c) while g_serve_phase is set, which serves/refuses/stubs each and witnesses it as
 * one UNSIGNED row of the body's serve trail (the body holds no key — precision a). exit_group ends the
 * run by unwinding to the setjmp here. Reuses the enclosure's recovery context, the loaded worker's entry
 * and user stack, and the ring-3 crossing — no second load. Returns 0 iff every serve check passes. */
int enclosure_serve_run(void) {
    serial_puts("SERVE: the forty-nine measured requests (the acts' share by the acts, the floor realized, "
                "the designed refusal, the stubs, entropy at bring-up, the socket refused)\n");
    g_serve_phase = 1;
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_serve_exited = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        enter_ring3(g_worker_entry, g_user_rsp, 2 /*mode: the forty-nine*/, 0);
        /* unreachable — the worker ends via exit_group (longjmp 1) or faults (longjmp 2) */
    }
    g_in_worker = 0;
    g_serve_phase = 0;
    int worker_ok = (jv == 1 && g_serve_exited && g_worker_fault == 0);
    return serve_finish(worker_ok);
}

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-4f-ii — THE CONCURRENCY FLOOR: real thread contexts, a preemptive scheduler, a real futex wait
 * queue (design/54 §5 L19, §7 P3b-4f; the pre-flight FINDINGS Q-D/Q6; archi :4116 a, :4107 a). Built
 * EDIT-IN-PLACE here (no new src/body file). serve.c's classification is kept as the router; its canned
 * concurrency answers (clone3→a fake id, futex→return at once, no SYS_exit) are REPLACED by calls into
 * this real machinery when the concurrency floor is active (g_sched_on). Always compiled (serve.c and
 * idt.c call it); inert until sched_init() sets g_sched_on. NO new act (ACT_KINDS stays twelve).
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/
#define SCHED_MSR_FS_BASE 0xC0000100u
#define SCHED_CANON_LIMIT 0x0000800000000000ull     /* a user pointer must sit in the low canonical half */
#define SCHED_EAGAIN      11u
#define SCHED_ETIMEDOUT   110u
#define FUTEX_WAIT_C        0u
#define FUTEX_WAKE_C        1u
#define FUTEX_WAIT_BITSET_C 9u
#define FUTEX_FLAG_MASK     0x180u                   /* FUTEX_PRIVATE_FLAG(128) | FUTEX_CLOCK_REALTIME(256) */

#define T_FREE     0
#define T_RUNNABLE 1
#define T_RUNNING  2
#define T_BLOCKED  3
#define T_ZOMBIE   4

struct thread {
    int      state;
    uint32_t tid;
    jmpctx_t kctx;               /* the kernel continuation (body_setjmp/body_longjmp)                    */
    uint64_t kstack_top;         /* this thread's ring-0 stack top (RSP0 + the syscall stack)             */
    uint64_t fs_base;            /* this thread's %fs base (restored per switch)                          */
    uint64_t clear_child_tid;    /* CHILD_CLEARTID: cleared + woken on exit so a join returns             */
    uint64_t wait_uaddr;         /* the futex the thread is BLOCKED on (0 if not waiting)                 */
    int      wait_has_deadline;
    uint64_t wait_deadline;      /* ns (sched_now_ns units)                                               */
    int64_t  wake_result;        /* the futex answer when resumed: 0 (woken) or -ETIMEDOUT                */
    int      first_run;          /* a freshly created context that has not yet entered ring 3            */
    uint64_t user_entry, user_rsp, user_func, user_arg;
    uint8_t  sse[512] __attribute__((aligned(16)));   /* the fxsave/fxrstor area (per thread)            */
} __attribute__((aligned(16)));

static struct thread g_threads[SCHED_MAX_THREADS];
static uint8_t g_kstacks[SCHED_MAX_THREADS][SCHED_KSTACK_SIZE] __attribute__((aligned(16)));
static struct thread *g_cur;
static uint32_t g_next_tid = 1;              /* main == 1 (BODY_PID); children 2,3,...                   */

int g_sched_on;
uint32_t g_sched_switches, g_sched_preempts, g_sched_threads_created, g_sched_exits, g_sched_switch_in_act;
volatile int g_in_act;
uint32_t g_sched_cur_tid;                    /* the currently-running thread's tid (read at a fault)      */

uint64_t sched_now_ns(void) { return (uint64_t)ticks_get() * SCHED_NS_PER_TICK; }

/* C7-MAINT-5B-THREAD-SLOT-RECLAIM: allocate a thread slot — a T_FREE slot, else a finished thread's slot
 * RECLAIMED at the first safe point after its switch-away. A finished thread cannot free the kernel stack it
 * is running on, so its slot is freed by whoever runs next — this allocator. The exit path (sched_thread_exit)
 * is UNCHANGED: it clears + wakes the waiter, counts the exit, sets T_ZOMBIE and switches away forever, ALL
 * before any reclaim is possible. Two facts make the reclaim safe for the join (A2, the correctness surface):
 *   - state == T_ZOMBIE implies the exit already cleared + woke the waiter — T_ZOMBIE is assigned in exactly
 *     one place (sched_thread_exit), AFTER the CHILD_CLEARTID clear + futex wake — so a join always found what
 *     it needed before the slot became reclaimable (a detached thread has no waiter and is reclaimed too).
 *   - &g_threads[i] != g_cur — the slot is NEVER the current thread: a zombie is g_cur only inside
 *     sched_thread_exit between setting T_ZOMBIE and switching away, a window in which no allocation runs (one
 *     CPU, ring 0, IF=0 during an act — the timer never switches; sched_alloc is called only from a ring-3
 *     thread-create act). The guard makes the "never the current thread" property local and self-evident. */
static struct thread *sched_alloc(void) {
    for (uint32_t i = 1; i < SCHED_MAX_THREADS; i++) {          /* slot 0 is main */
        if (g_threads[i].state == T_FREE) { return &g_threads[i]; }
#if defined(PLANT_RECLAIM_UNSAFE)
        /* A2 PLANT (a slot reclaimed before its waiter is cleared and woken — a live stack reused): reuse a
         * still-LIVE slot (T_RUNNABLE / T_BLOCKED — a thread that has NOT exited, so its waiter was never
         * cleared + woken). A pending join then finds a different thread on that slot, its kernel stack reused
         * under it. The 4f-ii join prover reds (the join hangs). The check CAN fail — L19. */
        if ((g_threads[i].state == T_RUNNABLE || g_threads[i].state == T_BLOCKED)
            && &g_threads[i] != g_cur) { return &g_threads[i]; }
#elif !defined(PLANT_NO_RECLAIM)
        /* RECLAIM: a safely finished zombie slot (not the current thread; its waiter already cleared + woken
         * before T_ZOMBIE was set). PLANT_NO_RECLAIM disables this — demand reverts to cumulative creations
         * and ep28c_w1 exhausts the table (A1 plant: reds). */
        if (g_threads[i].state == T_ZOMBIE && &g_threads[i] != g_cur) { return &g_threads[i]; }
#endif
    }
    return 0;
}

/* round-robin: the next RUNNABLE context after g_cur (or 0 if none). */
static struct thread *sched_pick_next(void) {
    uint32_t start = (uint32_t)(g_cur - g_threads);
    for (uint32_t k = 1; k <= SCHED_MAX_THREADS; k++) {
        struct thread *t = &g_threads[(start + k) % SCHED_MAX_THREADS];
        if (t->state == T_RUNNABLE) { return t; }
    }
    return 0;
}

/* expire timed waits whose deadline has passed — woken with -ETIMEDOUT (a real timeout). */
static void sched_expire_deadlines(void) {
    uint64_t now = sched_now_ns();
    for (uint32_t i = 0; i < SCHED_MAX_THREADS; i++) {
        struct thread *t = &g_threads[i];
        if (t->state == T_BLOCKED && t->wait_has_deadline && now >= t->wait_deadline) {
            t->wake_result = -(int64_t)SCHED_ETIMEDOUT;
            t->wait_uaddr = 0; t->wait_has_deadline = 0;
            t->state = T_RUNNABLE;
        }
    }
}

/* wake up to `nr` waiters on uaddr — return the count woken (FUTEX_WAKE). */
static uint64_t sched_futex_wake(uint64_t uaddr, uint64_t nr) {
    uint64_t woken = 0;
    for (uint32_t i = 0; i < SCHED_MAX_THREADS && woken < nr; i++) {
        struct thread *t = &g_threads[i];
        if (t->state == T_BLOCKED && t->wait_uaddr == uaddr) {
            t->wake_result = 0; t->wait_uaddr = 0; t->wait_has_deadline = 0;
            t->state = T_RUNNABLE;
            woken++;
        }
    }
    return woken;
}

/* THE SWITCH — save g_cur's kernel continuation, resume `next`; returns when g_cur is resumed. Uniform for
 * the timer-preemption path (from the IRQ on g_cur's kstack) and the voluntary block path (from a syscall
 * on g_cur's kstack). The outgoing thread's live ring-3 SSE (untouched by the -mno-sse body) is fxsave'd;
 * the incoming thread's is fxrstor'd. RSP0 + the syscall stack point at the incoming kstack. */
static void sched_switch_to(struct thread *next) {
    struct thread *prev = g_cur;
    if (prev == next) { return; }
    g_sched_switches++;
    /* a RUNNING thread switched out by the timer is still runnable (it may run again); a thread that set
     * itself BLOCKED/ZOMBIE before switching is left as it is (the block/exit paths own that). */
    if (prev->state == T_RUNNING) { prev->state = T_RUNNABLE; }
#ifndef PLANT_NO_SSE_SWITCH
    body_fxsave(prev->sse);
#endif
    if (body_setjmp(prev->kctx) != 0) {
        g_cur->state = T_RUNNING;                 /* resumed later: prev is g_cur again (SSE fxrstor'd)  */
        return;
    }
    g_cur = next;
    g_sched_cur_tid = next->tid;
    next->state = T_RUNNING;
    body_set_kernel_stack(next->kstack_top);
    wrmsr(SCHED_MSR_FS_BASE, next->fs_base);
#ifndef PLANT_NO_SSE_SWITCH
    body_fxrstor(next->sse);
#endif
    if (next->first_run) {
        next->first_run = 0;
        enter_ring3_thread(next->user_entry, next->user_rsp, next->user_func, next->user_arg);
        /* never returns — the child runs in ring 3 until it blocks, is preempted, or SYS_exits */
    }
    body_longjmp(next->kctx, 1);                  /* resume next where it body_setjmp'd (never returns)  */
}

/* g_cur is BLOCKED — run other threads (or idle) until g_cur is made runnable again. The act's g_in_act is
 * cleared while blocked (another thread runs in ring 3, not in this thread's act) and restored on return. */
static void sched_block(void) {
    g_in_act = 0;
    for (;;) {
        sched_expire_deadlines();
        if (g_cur->state == T_RUNNABLE) { g_cur->state = T_RUNNING; break; }
        struct thread *next = sched_pick_next();
        if (next) { sched_switch_to(next); g_cur->state = T_RUNNING; break; }
        __asm__ volatile("sti; hlt; cli");        /* nobody runnable — idle until the timer wakes someone */
    }
    g_in_act = 1;
}

void sched_init(void) {
    for (uint32_t i = 0; i < SCHED_MAX_THREADS; i++) { g_threads[i].state = T_FREE; }
    struct thread *m = &g_threads[0];
    m->state = T_RUNNING;
    m->tid = g_next_tid++;                        /* main tid == 1 */
    m->kstack_top = (uint64_t)(uintptr_t)(g_kstacks[0] + SCHED_KSTACK_SIZE);
    m->fs_base = 0;                               /* glibc installs the main %fs via arch_prctl */
    m->clear_child_tid = 0; m->first_run = 0;
    g_cur = m;
    g_sched_cur_tid = m->tid;
    body_set_kernel_stack(m->kstack_top);
    g_sched_on = 1;
}

void sched_set_current_fs(uint64_t base) { if (g_cur) { g_cur->fs_base = base; } }

void sched_timer_tick(struct isr_frame *f) {
    if (!g_sched_on) { return; }
#ifdef FLOOR2_TRACE
    { static uint32_t hb; if ((++hb % 1000u) == 0) { serial_puts("."); } }
#endif
    sched_expire_deadlines();
    int ring3 = ((f->cs & 3u) == 3u);
#if defined(PLANT_SWITCH_INSIDE_ACT)
    if (!ring3 && g_in_act) {                     /* the fault: switch while an act is in progress */
        struct thread *n = sched_pick_next();
        if (n) { g_sched_switch_in_act++; sched_switch_to(n); }
        return;
    }
#endif
    if (!ring3) { return; }                       /* ring 0 (a syscall/idle) — never switch inside an act
                                                   * (an act runs in ring 0 with IF=0, so the timer cannot
                                                   * even fire here; a ring-3 context is never in an act) */
    struct thread *next = sched_pick_next();
    if (next) { g_sched_preempts++; sched_switch_to(next); }
}

uint64_t sched_clone3(uint64_t cl_args_ptr, uint64_t ret_rip, uint64_t func, uint64_t arg) {
    if (cl_args_ptr == 0 || cl_args_ptr >= SCHED_CANON_LIMIT) { return (uint64_t)(-(int64_t)SCHED_EAGAIN); }
    volatile uint64_t *ca = (volatile uint64_t *)(uintptr_t)cl_args_ptr;
    uint64_t child_tid  = ca[2];                  /* offset 16 — CHILD_CLEARTID / PARENT_SETTID address */
    uint64_t parent_tid = ca[3];                  /* offset 24 */
    uint64_t stack      = ca[5];                  /* offset 40 */
    uint64_t stack_size = ca[6];                  /* offset 48 */
    uint64_t tls        = ca[7];                  /* offset 56 */

    /* THE CHILD'S INITIAL STACK POINTER — stack + stack_size, exactly as a real kernel computes it (the
     * crossing preserves the worker's registers across the mmap/mprotect syscalls, so glibc's allocate_stack
     * computes the true size, e.g. 0x800300). A DEFENSIVE fallback covers the freestanding case where glibc's
     * default-attr resolution cannot size the default stack (no live /proc) and passes stack_size == 0: then
     * stack + stack_size would land the child at the block's bottom and its first push would fault below the
     * map. The clone_args still carry the thread pointer (tls) at the TOP of the mapped block; on x86_64 (TLS
     * variant II) the static TLS + TCB sit at [tls - tls_size, tls + sizeof(TCB)] with the stack growing DOWN
     * below them, so the body places the child sp just below the TLS block (16-aligned) — the same effective
     * sp a real kernel hands the thread, the whole mapped block below it available to grow into. */
    uint64_t child_rsp = stack + stack_size;
    if (stack_size == 0 && tls > stack && tls < stack + 0x40000000ull) {
        child_rsp = (tls - 0x2000ull) & ~0xFull;
    }
#ifdef FLOOR2_TRACE
    serial_puts("CLONE3 stack=0x"); serial_puthex64(stack);
    serial_puts(" size=0x"); serial_puthex64(stack_size);
    serial_puts(" rsp=0x"); serial_puthex64(child_rsp); serial_puts("\n");
#endif
#if defined(PLANT_FAKE_TID)
    /* the fault: a fake id, NO running context -> the workers never run and pthread_join hangs. */
    (void)ret_rip; (void)func; (void)arg; (void)stack; (void)stack_size; (void)tls; (void)child_rsp;
    uint32_t faketid = g_next_tid++;
    if (parent_tid && parent_tid < SCHED_CANON_LIMIT) { *(volatile uint32_t *)(uintptr_t)parent_tid = faketid; }
    if (child_tid  && child_tid  < SCHED_CANON_LIMIT) { *(volatile uint32_t *)(uintptr_t)child_tid  = faketid; }
    return faketid;
#else
    struct thread *t = sched_alloc();
    if (!t) { return (uint64_t)(-(int64_t)SCHED_EAGAIN); }
    /* C7-MAINT-5B-THREAD-SLOT-RECLAIM (:4460 — a slot reused is a slot RE-BORN, a tid is NEVER reused):
     * a reclaimed slot may carry a finished occupant's stale fields, so EVERY field is re-initialised for the
     * new occupant — nothing of the previous occupant survives (a stale wait/deadline/wake-result/clear-tid,
     * or a stale saved context, would misbehave on the new thread's first wait or join). The tid is FRESH and
     * MONOTONIC (g_next_tid++, never reset, never the zombie's number), so a late joiner or a wake addressed
     * to the old tid finds nothing, not the new thread — the shape Linux keeps within a process's life. */
    t->tid = g_next_tid++;                           /* fresh, monotonic — never the reclaimed slot's old tid */
    t->fs_base = tls;
    t->clear_child_tid = child_tid;
    t->wait_uaddr = 0; t->wait_has_deadline = 0; t->wait_deadline = 0;
    t->wake_result = 0;                              /* re-born: no prior waiter-answer survives (:4460)      */
    for (int z = 0; z < 8; z++) { t->kctx[z] = 0; }  /* re-born: no prior saved kernel context survives       */
    t->first_run = 1;
    t->user_entry = ret_rip;                      /* the child returns from clone3 to this rip (rax=0)   */
    t->user_rsp   = child_rsp;                     /* the child's initial stack top (see the note above)  */
    t->user_func  = func;                         /* rdx in the child (glibc: call *%rdx)                */
    t->user_arg   = arg;                          /* r8 in the child (glibc: mov %r8,%rdi)               */
    t->kstack_top = (uint64_t)(uintptr_t)(g_kstacks[t - g_threads] + SCHED_KSTACK_SIZE);
    /* seed the child's SSE save area with a VALID (clean) state: its first run fxrstor's this area, and a
     * zero-initialized area would load MXCSR=0 (all SIMD exceptions unmasked — the child's first inexact FP
     * op would #XM). The current state (main's) carries the clean MXCSR floor_enable_sse installed. */
    body_fxsave(t->sse);
    t->state = T_RUNNABLE;
    g_sched_threads_created++;
    if (parent_tid && parent_tid < SCHED_CANON_LIMIT) { *(volatile uint32_t *)(uintptr_t)parent_tid = t->tid; }
    if (child_tid  && child_tid  < SCHED_CANON_LIMIT && child_tid != parent_tid) {
        *(volatile uint32_t *)(uintptr_t)child_tid = t->tid;
    }
    return t->tid;                                /* returned to the parent */
#endif
}

void sched_thread_exit(void) {
    struct thread *t = g_cur;
    g_in_act = 0;                                 /* the thread's act is ending; it switches away forever */
#if !defined(PLANT_NO_CHILD_CLEAR)
    if (t->clear_child_tid && t->clear_child_tid < SCHED_CANON_LIMIT) {
        *(volatile uint32_t *)(uintptr_t)t->clear_child_tid = 0;   /* CHILD_CLEARTID: clear the tid */
        sched_futex_wake(t->clear_child_tid, 1);                    /* wake pthread_join's futex     */
    }
#else
    (void)t;                                                       /* the fault: never cleared/woken */
#endif
    g_sched_exits++;
    t->state = T_ZOMBIE;
    for (;;) {                                    /* switch away forever (a zombie is never resumed) */
        struct thread *next = sched_pick_next();
        if (next) { sched_switch_to(next); }
        else { __asm__ volatile("sti; hlt; cli"); }
    }
}

uint64_t sched_futex(uint64_t uaddr, uint64_t op, uint64_t val, uint64_t timeout_ptr) {
    uint32_t cmd = (uint32_t)(op & ~(uint64_t)FUTEX_FLAG_MASK);
#if defined(PLANT_FUTEX_NO_QUEUE)
    /* the fault: no real wait queue / no timeout — every op returns at once. The timed wait never blocks
     * to its deadline; glibc's sem re-loops forever and the prover hangs at the timed wait. */
    (void)uaddr; (void)val; (void)timeout_ptr; (void)cmd;
    return 0;
#else
    if (cmd == FUTEX_WAKE_C) { return sched_futex_wake(uaddr, val); }
    if (cmd == FUTEX_WAIT_C || cmd == FUTEX_WAIT_BITSET_C) {
        if (uaddr == 0 || uaddr >= SCHED_CANON_LIMIT) { return (uint64_t)(-(int64_t)SCHED_EAGAIN); }
        if (*(volatile uint32_t *)(uintptr_t)uaddr != (uint32_t)val) {
            return (uint64_t)(-(int64_t)SCHED_EAGAIN);     /* the word already changed — do not block */
        }
        g_cur->wait_uaddr = uaddr; g_cur->wait_has_deadline = 0; g_cur->wake_result = 0;
        if (cmd == FUTEX_WAIT_BITSET_C && timeout_ptr && timeout_ptr < SCHED_CANON_LIMIT) {
            volatile uint64_t *ts = (volatile uint64_t *)(uintptr_t)timeout_ptr;   /* {tv_sec, tv_nsec} */
            g_cur->wait_deadline = ts[0] * 1000000000ull + ts[1];
            g_cur->wait_has_deadline = 1;
        }
        g_cur->state = T_BLOCKED;
        sched_block();
        g_cur->wait_uaddr = 0;
        return (uint64_t)g_cur->wake_result;               /* 0 (woken) or -ETIMEDOUT */
    }
    return 0;
#endif
}

#ifdef PROVER_PRESENT
/* ── C7 P3b-4f-i — THE STATIC SINGLE-THREAD FLOOR (design/54 §5 L19) ──────────────────────────────────
 * The body becomes a real home for an ORDINARY statically-linked single-threaded glibc program: it lays a
 * real initial stack + auxiliary vector, backs mmap/munmap/mprotect/brk with a real address-space manager
 * (serve.c), installs the main-thread %fs base (serve.c's arch_prctl), and enables the machine's SSE state
 * — then enters the program at ring 3. The PROVER is NOT ours to shape (L19): it is `gcc -static` glibc C
 * built by the guest's own toolchain, staged as a SEALED IMAGE (digest-checked here, §9 mechanism 3 — never
 * a member). It proves the floor by RUNNING (reaching main, malloc/free, distinct maps, the %fs thread-
 * local, SSE, reading AT_RANDOM) and printing its result on serial; a planted break (no %fs, SSE off, a
 * fixed VA, a constant AT_RANDOM) makes THE PROGRAM fail, never a flag. The body's own C stays -mno-sse;
 * only the CPU state is enabled. NO new act (ACT_KINDS stays twelve); founds nothing. */

#ifndef PROVER_IMG_SHA256HEX
#define PROVER_IMG_SHA256HEX "0000000000000000000000000000000000000000000000000000000000000000"
#endif

#define PROVER_STACK_BOT 0x30000000ull
#define PROVER_STACK_TOP 0x30020000ull   /* a 128 KiB initial stack (32 user pages) */

/* the auxiliary-vector types the static loader lays (the named set, design/54 §5 L19; §1). */
#define AT_NULL   0u
#define AT_PHDR   3u
#define AT_PHENT  4u
#define AT_PHNUM  5u
#define AT_PAGESZ 6u
#define AT_BASE   7u   /* C7 P3b-4d: the dynamic linker's load base (laid only for the dynamic floor) */
#define AT_ENTRY  9u
#define AT_RANDOM 25u

static uint64_t g_floor_entry;       /* the prover's e_entry                                   */
static uint64_t g_floor_rsp;         /* the prover's initial %rsp (argc at the SysV stack top)  */
static uint64_t g_floor_phdr_va;     /* AT_PHDR — the program headers' load address            */
static uint64_t g_floor_phnum;       /* AT_PHNUM                                               */
static uint64_t g_floor_phent;       /* AT_PHENT                                               */
static uint64_t g_floor_max_vaddr;   /* the highest loaded vaddr (the initial program break)   */
static uint64_t g_dyn_ld_base;       /* C7 P3b-4d: AT_BASE (the dynamic linker's load base); 0 = static */

/* enable the machine's SSE state for the ring-3 program (precision (d)): CR4.OSFXSR|OSXMMEXCPT + fninit +
 * a clean MXCSR, and NEVER CR4.OSXSAVE (which keeps glibc on the SSE2 path — CPUID.OSXSAVE reads 0, so its
 * ifunc resolvers never select an AVX variant that would need the XSAVE state). The body's own C stays
 * -mno-sse; only the CPU state is switched on. PLANT_SSE_DISABLED skips it → the program's first SSE
 * instruction #UDs, a real fault the body catches. */
static void floor_enable_sse(void) {
#ifndef PLANT_SSE_DISABLED
    uint64_t cr0, cr4;
    __asm__ volatile("mov %%cr0, %0" : "=r"(cr0));
    cr0 &= ~(1ull << 2);    /* CR0.EM = 0 — no x87/SSE emulation                 */
    cr0 |=  (1ull << 1);    /* CR0.MP = 1                                        */
    cr0 &= ~(1ull << 3);    /* CR0.TS = 0 — no #NM on first SSE use              */
    __asm__ volatile("mov %0, %%cr0" : : "r"(cr0));
    __asm__ volatile("mov %%cr4, %0" : "=r"(cr4));
    cr4 |= (1ull << 9);     /* CR4.OSFXSR     — enable SSE + fxsave/fxrstor      */
    cr4 |= (1ull << 10);    /* CR4.OSXMMEXCPT — SIMD FP exceptions -> #XM        */
    /* deliberately NOT CR4.OSXSAVE (bit 18): precision (d). */
    __asm__ volatile("mov %0, %%cr4" : : "r"(cr4));
    __asm__ volatile("fninit");
    uint32_t mxcsr = 0x1F80u;   /* the default clean MXCSR (all SIMD exceptions masked) */
    __asm__ volatile("ldmxcsr %0" : : "m"(mxcsr));
#endif
}

/* load the sealed prover: digest-check, map its PT_LOAD segments as USER pages, record e_entry, the
 * program-header load vaddr (AT_PHDR) and the highest vaddr (the initial break). 0 on success. */
static int floor_load_prover(void) {
    const uint8_t *img = prover_image_start;
    uint32_t img_len = (uint32_t)(prover_image_end - prover_image_start);
    uint8_t got[32];
    sha256(img, img_len, got);
    serial_puts("FLOOR-IMG-LEN: 0x"); serial_puthex32(img_len); serial_puts("\n");
    serial_puts("FLOOR-IMG-SHA256: "); put_hex_digest(got, 32); serial_puts("\n");
    if (!digest_matches_hex(got, PROVER_IMG_SHA256HEX)) {
        serial_puts("FLOOR-LOAD: REFUSED (digest mismatch — sealed prover not the sealed bytes)\n");
        return -1;
    }
    serial_puts("FLOOR-LOAD: OK (digest matches the seal)\n");

    const struct elf64_ehdr *eh = (const struct elf64_ehdr *)img;
    if (!(eh->e_ident[0] == 0x7f && eh->e_ident[1] == 'E'
          && eh->e_ident[2] == 'L' && eh->e_ident[3] == 'F')) { return -1; }
    if (eh->e_ident[4] != 2) { return -1; }    /* ELFCLASS64                           */
    if (eh->e_machine != 62) { return -1; }    /* EM_X86_64                            */
    if (eh->e_type != 2) { return -1; }        /* ET_EXEC — a fixed-base static program (L19/L20) */
    const struct elf64_phdr *ph = (const struct elf64_phdr *)(img + eh->e_phoff);
    uint64_t maxv = 0;
    for (int i = 0; i < eh->e_phnum; i++) {
        if (ph[i].p_type == PT_LOAD) {
            if (map_segment(ph[i].p_vaddr, ph[i].p_offset, ph[i].p_filesz, ph[i].p_memsz, img) != 0) {
                return -1;
            }
            uint64_t end = ph[i].p_vaddr + ph[i].p_memsz;
            if (end > maxv) { maxv = end; }
            /* AT_PHDR: the program headers sit in the segment covering e_phoff (the first LOAD). */
            if (ph[i].p_offset <= eh->e_phoff && eh->e_phoff < ph[i].p_offset + ph[i].p_filesz) {
                g_floor_phdr_va = ph[i].p_vaddr + (eh->e_phoff - ph[i].p_offset);
            }
        }
    }
    g_floor_entry     = eh->e_entry;
    g_floor_phnum     = eh->e_phnum;
    g_floor_phent     = eh->e_phentsize;
    g_floor_max_vaddr = maxv;
    return 0;
}

/* lay the static loader's INITIAL STACK: argc/argv/envp + the auxiliary vector (AT_PAGESZ, AT_PHDR,
 * AT_PHENT, AT_PHNUM, AT_ENTRY, AT_RANDOM, AT_NULL). AT_RANDOM's 16 bytes come from the body's own entropy
 * act (precision b); PLANT_AT_RANDOM_CONSTANT lays a constant (two boots then match). The stack region is
 * USER pages; the body (ring 0) writes them at their user VA (the machine permits a supervisor write to a
 * user page; SMAP is not enabled). */
static void floor_build_stack(void) {
    for (uint64_t p = PROVER_STACK_BOT; p < PROVER_STACK_TOP; p += 0x1000ull) {
        uint32_t f = pmm_alloc();
        if (f == 0) { return; }
        if (vmm_map_user(p, (uint64_t)f) != 0) { return; }
        uint8_t *z = (uint8_t *)phys_to_virt(f);
        for (int i = 0; i < 4096; i++) { z[i] = 0; }
    }
    uint64_t va_random = PROVER_STACK_TOP - 16;
    uint8_t rnd[16];
#if defined(PLANT_AT_RANDOM_CONSTANT)
    for (int i = 0; i < 16; i++) { rnd[i] = 0x5A; }   /* the fault: a constant — two boots match */
#else
    entropy_draw(rnd, 16);                            /* the body's own entropy act (precision b) */
#endif
    for (int i = 0; i < 16; i++) { ((volatile uint8_t *)(uintptr_t)va_random)[i] = rnd[i]; }

    uint64_t va_arg0 = PROVER_STACK_TOP - 32;
    static const char name[] = "prover";
    for (int i = 0; i < 7; i++) { ((volatile char *)(uintptr_t)va_arg0)[i] = name[i]; }   /* 6 + NUL */

    /* the SysV vector, 16-aligned: argc, argv[0], argv-NULL, envp-NULL, auxv[6 pairs], AT_NULL pair. */
    uint64_t rsp = (va_arg0 - 256) & ~0xFull;
    volatile uint64_t *v = (volatile uint64_t *)(uintptr_t)rsp;
    int k = 0;
    v[k++] = 1;                  /* argc                     */
    v[k++] = va_arg0;            /* argv[0]                  */
    v[k++] = 0;                  /* argv terminator          */
    v[k++] = 0;                  /* envp terminator (empty)  */
    v[k++] = AT_PAGESZ; v[k++] = 4096;
    v[k++] = AT_PHDR;   v[k++] = g_floor_phdr_va;
    v[k++] = AT_PHENT;  v[k++] = g_floor_phent;
    v[k++] = AT_PHNUM;  v[k++] = g_floor_phnum;
    v[k++] = AT_ENTRY;  v[k++] = g_floor_entry;
    v[k++] = AT_RANDOM; v[k++] = va_random;
    if (g_dyn_ld_base) { v[k++] = AT_BASE; v[k++] = g_dyn_ld_base; }   /* C7 P3b-4d: the dynamic linker's base */
    v[k++] = AT_NULL;   v[k++] = 0;
    g_floor_rsp = rsp;
}

int floor_run(void) {
    interrupts_disable();   /* a deterministic single-thread run (the clock slice proved interrupts) */
    serial_puts("FLOOR: the static single-thread floor — the loader's stack+auxv, the address-space "
                "manager, the main-thread %fs, the machine's SSE — proven by an ordinary gcc -static "
                "glibc program (L19)\n");
    floor_enable_sse();

    if (floor_load_prover() != 0) {
        serial_puts("FLOOR: FAIL (the sealed prover was refused at load)\n");
        return 1;
    }
    /* the program break starts just above the loaded image (page-aligned). */
    serve_set_brk_base((g_floor_max_vaddr + 0xFFFull) & ~0xFFFull);
    floor_build_stack();

    /* reset %fs to 0: glibc installs its own base via arch_prctl(ARCH_SET_FS); under PLANT_NO_FS_BASE the
     * body does not, so %fs stays 0 and the program's first thread-local access faults (a real #PF). */
    wrmsr(0xC0000100u, 0);

    g_serve_phase = 1;                 /* route the prover's crossings to serve_request (the kept router) */
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        enter_ring3(g_floor_entry, g_floor_rsp, 0, 0);
        /* unreachable — the prover exit_group's (longjmp 1) or faults (longjmp 2) */
    }
    g_in_worker = 0;
    g_serve_phase = 0;

    if (jv == 2) {
        serial_puts("FLOOR-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
        serial_puts(" cr2=0x");             serial_puthex64(g_worker_cr2);
        serial_puts(" faultcs=0x");         serial_puthex32((uint32_t)g_worker_faultcs); serial_puts("\n");
        serial_puts("FLOOR: FAIL (the prover FAULTED — a floor piece is missing)\n");
        return 1;
    }
    serial_puts("FLOOR: PASS (the prover ran to completion on the body)\n");
    return 0;
}

/* ── C7 P3b-4f-ii — THE CONCURRENCY FLOOR (design/54 §5 L19, §7 P3b-4f). On the static single-thread floor
 * (the stack+auxv, the address-space manager, the %fs, SSE), the body becomes a real home for MANY threads:
 * clone3 real contexts, a preemptive scheduler on the P3b-3 timer, a real futex wait queue, SYS_exit that
 * clears + wakes the child id. Unlike floor_run, the program runs with INTERRUPTS ENABLED (preemptible),
 * and the PIT is re-programmed to a frequent rate so a turn likely falls mid-computation (the per-thread SSE
 * state must survive it). Proven by the FROZEN P3b-4f A1 full `gcc -static -pthread` glibc program. */
int floor2_run(void) {
    serial_puts("FLOOR2: the concurrency floor — real threads (clone3), a preemptive scheduler on the "
                "P3b-3 timer (per-thread %fs + SSE at the switch, never inside an act), a real futex wait "
                "queue with timeouts and wake, a thread's own end (SYS_exit) clearing the child id — proven "
                "by an ordinary gcc -static -pthread glibc program (L19)\n");
    floor_enable_sse();

    if (floor_load_prover() != 0) {
        serial_puts("FLOOR2: FAIL (the sealed prover was refused at load)\n");
        return 1;
    }
    serve_set_brk_base((g_floor_max_vaddr + 0xFFFull) & ~0xFFFull);
    floor_build_stack();
    wrmsr(0xC0000100u, 0);              /* main %fs reset; glibc installs its base via arch_prctl */

    pit_init(SCHED_PIT_HZ);             /* frequent preemption + the clock sched_now_ns derives from */
    sched_init();                       /* the main thread becomes the first preemptible context */

    g_serve_phase = 1;                  /* route the prover's crossings to serve_request (the kept router) */
    g_active_ctx = g_ctx;               /* a fault or exit_group unwinds the whole run back to here */
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        interrupts_enable();            /* the program is preemptible — the timer takes turns */
        enter_ring3_main(g_floor_entry, g_floor_rsp);
        /* unreachable — the prover exit_group's (longjmp 1) or faults (longjmp 2) */
    }
    interrupts_disable();
    g_in_worker = 0;
    g_serve_phase = 0;
    g_sched_on = 0;

    if (jv == 2) {
        serial_puts("FLOOR2-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
        serial_puts(" cr2=0x");              serial_puthex64(g_worker_cr2);
        serial_puts(" faultcs=0x");          serial_puthex32((uint32_t)g_worker_faultcs);
        serial_puts(" tid=0x");              serial_puthex32(g_sched_cur_tid);
        serial_puts(" fsbase=0x");           serial_puthex64(rdmsr(0xC0000100u));
        serial_puts(" rip=0x");              serial_puthex64(g_worker_rip);
        serial_puts(" rsp=0x");              serial_puthex64(g_worker_rsp);
        serial_puts(" rbp=0x");              serial_puthex64(g_worker_rbp); serial_puts("\n");
        serial_puts("FLOOR2: FAIL (the prover FAULTED — a concurrency-floor piece is missing)\n");
        return 1;
    }

    serial_puts("FLOOR2-SWITCHES: 0x");     serial_puthex32(g_sched_switches);     serial_puts("\n");
    serial_puts("FLOOR2-PREEMPTS: 0x");     serial_puthex32(g_sched_preempts);     serial_puts("\n");
    serial_puts("FLOOR2-THREADS: 0x");      serial_puthex32(g_sched_threads_created); serial_puts("\n");
    serial_puts("FLOOR2-EXITS: 0x");        serial_puthex32(g_sched_exits);        serial_puts("\n");
    serial_puts("FLOOR2-SWITCH-IN-ACT: 0x");serial_puthex32(g_sched_switch_in_act);serial_puts("\n");

    /* the body-side aggregate: the scheduler did REAL concurrency — two contexts created, both ended via
     * SYS_exit, the timer preempted a running context, and NO switch ever happened inside an act. */
    int ok = (g_sched_threads_created >= 2) && (g_sched_exits >= 2)
          && (g_sched_preempts > 0) && (g_sched_switch_in_act == 0);
    serial_puts(ok ? "FLOOR2: PASS (real threads took turns and finished for one another)\n"
                   : "FLOOR2: FAIL (the scheduler did not do real concurrency work)\n");
    return ok ? 0 : 1;
}

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-4d — THE DYNAMIC LOADER + THE SEALED IMAGE (design/54 §5 L19, §7 P3b-4d; B6; Q8/Q15 of the
 * pre-flight). On the concurrency floor, the body brings up the DYNAMIC path. It (1) DIGEST-CHECKS the
 * sealed image as a whole (B6 — a byte change refuses the load; the prover never starts); (2) adopts the
 * image as a read-only filesystem (serve.c serves ld.so + libc by path+offset+listing); (3) loads the
 * DYNAMIC prover (ET_EXEC, -no-pie) at 0x400000 and reads its PT_INTERP; (4) loads THAT ld.so (ET_DYN)
 * from the sealed image at LD_LOAD_BASE; (5) lays the SEVEN-key auxiliary vector (AT_BASE added) and HANDS
 * OVER to the linker, which resolves libc from the sealed image and relocates the program; (6) the program
 * runs to completion. Proven, per L19, by an ordinary `gcc -pthread -no-pie` glibc program. A plant makes
 * THAT program fail (a byte change → no load; PT_INTERP skipped → a fault; a collision → wrong libc bytes),
 * never a body-side flag. NOT the interpreter (P3b-4c). ═══════════════════════════════════════════════*/
#ifdef DYNAMIC_FLOOR
#ifndef SEALED_IMG_SHA256HEX
#define SEALED_IMG_SHA256HEX "0000000000000000000000000000000000000000000000000000000000000000"
#endif
#define PT_INTERP      3u
#define LD_LOAD_BASE   0x7f0000000000ull   /* the dynamic linker's load base (ET_DYN, above the program)   */

static uint64_t g_dyn_entry;               /* the entry iretq'd into (ld.so's, or the program's under the plant) */

/* read the dynamic program's PT_INTERP (the requested linker path) from the sealed prover image. */
static int floor3_read_interp(char *out, int max) {
    const uint8_t *img = prover_image_start;
    const struct elf64_ehdr *eh = (const struct elf64_ehdr *)img;
    const struct elf64_phdr *ph = (const struct elf64_phdr *)(img + eh->e_phoff);
    for (int i = 0; i < eh->e_phnum; i++) {
        if (ph[i].p_type == PT_INTERP) {
            uint64_t off = ph[i].p_offset, len = ph[i].p_filesz;
            uint64_t cap = (len < (uint64_t)(max - 1)) ? len : (uint64_t)(max - 1);
            for (uint64_t k = 0; k < cap; k++) { out[k] = (char)img[off + k]; }
            out[cap] = '\0';               /* the PT_INTERP string carries its own NUL within p_filesz */
            return 0;
        }
    }
    return -1;                             /* no PT_INTERP — not a dynamically-linked program */
}

/* load ld.so (ET_DYN) from the sealed image at LD_LOAD_BASE. Unlike map_segment (which zeroes a sub-page
 * prefix — fine for the page-aligned program), ld.so's data segment has a SUB-PAGE p_vaddr (0x36360,
 * measured), so the page's leading bytes [page_down(vaddr), vaddr) must come FROM THE FILE at
 * page_down(p_offset) — exactly as the kernel maps it. Segments do not share a page here (measured). */
static int floor3_load_interp(const char *interp) {
    uint32_t ldlen = 0; int isdir = 0;
    const uint8_t *img = serve_fs_find(interp, &ldlen, &isdir);   /* the ld.so bytes in the sealed image */
    if (!img || isdir) { return -1; }
    const struct elf64_ehdr *eh = (const struct elf64_ehdr *)img;
    if (!(eh->e_ident[0] == 0x7f && eh->e_ident[1] == 'E'
          && eh->e_ident[2] == 'L' && eh->e_ident[3] == 'F')) { return -1; }
    if (eh->e_ident[4] != 2) { return -1; }        /* ELFCLASS64                      */
    if (eh->e_machine != 62) { return -1; }        /* EM_X86_64                       */
    if (eh->e_type != 3) { return -1; }            /* ET_DYN — the linker is position-independent */
    const struct elf64_phdr *ph = (const struct elf64_phdr *)(img + eh->e_phoff);
    for (int i = 0; i < eh->e_phnum; i++) {
        if (ph[i].p_type != PT_LOAD) { continue; }
        uint64_t va    = LD_LOAD_BASE + ph[i].p_vaddr;
        uint64_t st    = va & ~0xFFFull;                          /* page_down(vaddr)                 */
        uint64_t fstart = ph[i].p_offset & ~0xFFFull;             /* page_down(offset) — congruent    */
        uint64_t fend  = va + ph[i].p_filesz;                     /* file-backed end (virtual)        */
        uint64_t vend  = (va + ph[i].p_memsz + 0xFFFull) & ~0xFFFull;
        for (uint64_t page = st; page < vend; page += 0x1000ull) {
            uint32_t frame = pmm_alloc();
            if (frame == 0) { return -1; }
            if (vmm_map_user(page, (uint64_t)frame) != 0) { return -1; }
            uint8_t *dst = (uint8_t *)phys_to_virt(frame);
            for (uint32_t i2 = 0; i2 < 4096u; i2++) {
                uint64_t V = page + i2;
                if (V < fend) {
                    uint64_t foff = fstart + (page - st) + i2;    /* the file offset for this byte    */
                    dst[i2] = img[foff];
                } else {
                    dst[i2] = 0;                                  /* bss / beyond filesz              */
                }
            }
        }
    }
    g_dyn_ld_base = LD_LOAD_BASE;                                 /* AT_BASE for the auxv             */
    g_dyn_entry   = LD_LOAD_BASE + eh->e_entry;                   /* the linker's entry              */
    return 0;
}

/* split an absolute path into its directory and basename (for the listable check, derived not hardcoded).*/
static void floor3_split(const char *path, char *dir, char *base, int max) {
    int last = -1;
    for (int i = 0; path[i] && i < max; i++) { if (path[i] == '/') { last = i; } }
    if (last <= 0) { dir[0] = '/'; dir[1] = '\0'; }
    else { int i = 0; for (; i < last && i < max - 1; i++) { dir[i] = path[i]; } dir[i] = '\0'; }
    int j = 0; for (int i = last + 1; path[i] && j < max - 1; i++) { base[j++] = path[i]; } base[j] = '\0';
}

int floor3_run(void) {
    serial_puts("FLOOR3: the dynamic loader + the sealed image — the image a read-only filesystem of "
                "ld.so + libc (digest-checked, served by path+offset+listing), PT_INTERP honoured + the "
                "handover, the P3b-2 record FS mounted beside — proven by an ordinary gcc -pthread -no-pie "
                "dynamically-linked glibc program through the real linker (L19)\n");
    floor_enable_sse();

    /* C7-MAINT-4D-BOOT-AS-MODULE — the 2.26 MB sealed image is carried as a boot-time MODULE (read through
     * the direct map via g_sealed_module_phys), exactly as the interpreter body (floor3_interp_run) and the
     * ledger body already do — NOT embedded into the body's own image. Embedding pushed the body's end-of-data
     * (_bss_end) over CANONICAL_BASE, and the first post-paging global write stored into a page the higher-half
     * body withdraws from the supervisor identity map, triple-faulting at the CR3 switch (FINDINGS.md F1/F2).
     * The image bytes and its seal are UNCHANGED — only the carriage changed. */
    if (g_sealed_module_phys == 0 || g_sealed_module_len == 0) {
        serial_puts("FLOOR3: FAIL (no sealed-image module — boot the nested guest with -initrd sealed.img)\n");
        return 1;
    }
    const uint8_t *img = (const uint8_t *)phys_to_virt(g_sealed_module_phys);   /* the module, via the direct map */
    uint32_t img_len = (uint32_t)g_sealed_module_len;

    /* (A2) THE SEAL — digest-check the sealed image as a whole before load (B6, the SealedArtifact idiom). */
    uint8_t got[32];
    sha256(img, img_len, got);
    serial_puts("FLOOR3-SEAL-LEN: 0x"); serial_puthex32(img_len); serial_puts("\n");
    serial_puts("FLOOR3-SEAL-SHA256: "); put_hex_digest(got, 32); serial_puts("\n");
    if (!digest_matches_hex(got, SEALED_IMG_SHA256HEX)) {
        serial_puts("FLOOR3-SEAL: REFUSED (digest mismatch — the sealed image is not the sealed bytes)\n");
        serial_puts("FLOOR3: FAIL (the sealed image was refused at load — the prover never starts)\n");
        return 1;
    }
    serial_puts("FLOOR3-SEAL: OK (digest matches the seal)\n");

    int nent = serve_fs_set_image(img, img_len);
    if (nent < 0) { serial_puts("FLOOR3: FAIL (the sealed image is not a GOVSIMG1 archive)\n"); return 1; }
    serial_puts("FLOOR3-IMAGE: 0x"); serial_puthex32((uint32_t)nent); serial_puts(" entries\n");

    /* load the DYNAMIC prover (ET_EXEC at 0x400000; digest-checked here), then read its PT_INTERP. */
    if (floor_load_prover() != 0) {
        serial_puts("FLOOR3: FAIL (the sealed dynamic prover was refused at load)\n");
        return 1;
    }
    char interp[128];
    if (floor3_read_interp(interp, (int)sizeof(interp)) != 0) {
        serial_puts("FLOOR3: FAIL (the program has no PT_INTERP — it is not dynamically linked)\n");
        return 1;
    }
    serial_puts("FLOOR3-INTERP: "); serial_puts(interp); serial_puts("\n");

    /* load that ld.so from the sealed image at LD_LOAD_BASE (ET_DYN); record its entry + AT_BASE. */
    if (floor3_load_interp(interp) != 0) {
        serial_puts("FLOOR3: FAIL (the dynamic linker is not in the sealed image, or not ET_DYN)\n");
        return 1;
    }

    /* (A2 listing) the image is served BY LISTING — list the INTERP's own directory and find its basename
     * (derived from PT_INTERP, never hardcoded). (A4 beside) the P3b-2 record FS is reachable alongside the
     * read-only image with distinct namespaces. */
    char dir[128], base[128];
    floor3_split(interp, dir, base, 128);
    int listable = serve_fs_listable_check(dir, base);
    serial_puts(listable ? "FLOOR3-LISTABLE: OK\n" : "FLOOR3-LISTABLE: FAIL\n");
    int beside = serve_fs_beside_check();
    serial_puts(beside ? "FLOOR3-BESIDE: OK\n" : "FLOOR3-BESIDE: FAIL\n");

    serve_set_brk_base((g_floor_max_vaddr + 0xFFFull) & ~0xFFFull);
    floor_build_stack();                       /* now lays the SEVEN-key auxv (AT_BASE, g_dyn_ld_base set) */
    wrmsr(0xC0000100u, 0);                      /* main %fs reset; ld.so installs the base via arch_prctl   */

    pit_init(SCHED_PIT_HZ);
    sched_init();

    /* HAND OVER to the linker. PLANT_SKIP_INTERP enters the program's e_entry directly (no ld.so), with
     * libc unrelocated — the real program faults before main (A3, a real failure, not a flag). */
    uint64_t target = g_dyn_entry;
#if defined(PLANT_SKIP_INTERP)
    target = g_floor_entry;
    g_dyn_ld_base = 0;
#endif
    serial_puts("FLOOR3-HANDOVER: entry=0x"); serial_puthex64(target);
    serial_puts(" ld_base=0x"); serial_puthex64(g_dyn_ld_base); serial_puts("\n");

    g_serve_phase = 1;
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        interrupts_enable();
        enter_ring3_main(target, g_floor_rsp);
        /* unreachable — the prover exit_group's (longjmp 1) or faults (longjmp 2) */
    }
    interrupts_disable();
    g_in_worker = 0;
    g_serve_phase = 0;
    g_sched_on = 0;

    if (jv == 2) {
        serial_puts("FLOOR3-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
        serial_puts(" cr2=0x");              serial_puthex64(g_worker_cr2);
        serial_puts(" faultcs=0x");          serial_puthex32((uint32_t)g_worker_faultcs);
        serial_puts(" tid=0x");              serial_puthex32(g_sched_cur_tid);
        serial_puts(" rip=0x");              serial_puthex64(g_worker_rip); serial_puts("\n");
        serial_puts("FLOOR3: FAIL (the dynamic prover FAULTED — the handover or a sealed-FS piece is missing)\n");
        return 1;
    }

    /* (A4 no live walk) no path outside the sealed+record sets was ever SERVED, and the designed refusal
     * was actually exercised (a positive control — ld.so probed /etc/ld.so.preload + /etc/ld.so.cache). */
    int live_walk = serve_fs_live_walk();
    uint32_t outside = serve_fs_outside_refusals();
    int nowalk = (live_walk == 0) && (outside > 0);
    serial_puts("FLOOR3-OUTSIDE-REFUSALS: 0x"); serial_puthex32(outside); serial_puts("\n");
    serial_puts(nowalk ? "FLOOR3-NOWALK: OK\n" : "FLOOR3-NOWALK: FAIL\n");

    serial_puts("FLOOR3-SWITCHES: 0x");      serial_puthex32(g_sched_switches);        serial_puts("\n");
    serial_puts("FLOOR3-PREEMPTS: 0x");      serial_puthex32(g_sched_preempts);        serial_puts("\n");
    serial_puts("FLOOR3-THREADS: 0x");       serial_puthex32(g_sched_threads_created); serial_puts("\n");
    serial_puts("FLOOR3-EXITS: 0x");         serial_puthex32(g_sched_exits);           serial_puts("\n");
    serial_puts("FLOOR3-SWITCH-IN-ACT: 0x"); serial_puthex32(g_sched_switch_in_act);   serial_puts("\n");

    int ok = (jv == 1) && (g_sched_threads_created >= 2) && (g_sched_exits >= 2)
          && (g_sched_preempts > 0) && (g_sched_switch_in_act == 0)
          && listable && beside && nowalk;
    serial_puts(ok ? "FLOOR3: PASS (a dynamically linked glibc program ran to completion through the real linker)\n"
                   : "FLOOR3: FAIL (the dynamic loader / sealed image / record-beside did not fully hold)\n");
    return ok ? 0 : 1;
}

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-4c — THE INTERPRETER RUNS ON THE BODY (design/54 §5 L19, §7 P3b-4c; B6). The LAST prover on the
 * P3b-4f/P3b-4d path: the REAL, unmodified /usr/bin/python3.12 (ET_EXEC at 0x400000), loaded by the body's
 * own dynamic loader from the ONE sealed image (the interpreter + its C library + the loader-visible pieces
 * + its standard library as REAL FILES, served by path AND by listing), digest-checked before load, run
 * UNPRIVILEGED and UNMODIFIED as an enclosed worker on the real floor through the real linker. The sealed
 * image is too large to incbin beneath the program's base, so it arrives as a multiboot MODULE reached
 * through the direct map. The prover is NOT ours to write (L19): print(2+2) prints 4 and a thread runs
 * because the body genuinely serves what CPython asks; a planted byte change / broken primitive makes the
 * REAL interpreter fail, never a flag. ════════════════════════════════════════════════════════════════*/
#ifdef INTERP_FLOOR
#define AT_EXECFN 31u
#define INTERP_PROGRAM_PATH "/usr/bin/python3.12"
#define INTERP_STACK_BOT 0x30000000ull
#define INTERP_STACK_TOP 0x30800000ull     /* an 8 MiB main stack — RLIMIT_STACK is 8 MiB and CPython's
                                            * import machinery recurses; the body has no demand paging, so
                                            * the whole stack is mapped eagerly (the 128 KiB prover stack,
                                            * fine for the glibc provers, overflows under CPython). */

static char g_interp_path[128];            /* the interpreter's PT_INTERP (the requested ld.so), read from it */

/* the -c program the interpreter runs: the L19 proof (print(2+2)=4) and a real thread, over the gate's own
 * import set (so every staged .pyc/.so/data file is exercised). Choosing WHAT the interpreter runs is using
 * it, not shaping it; the interpreter computes 2+2 itself. The EXACT program the pre-flight manifest staged. */
static const char g_py_script[] =
    "import hmac,hashlib,json,base64,unicodedata,threading,os,io,struct,time,datetime\n"
    "print(2+2)\n"
    "def w():\n"
    "    print('thread-ran')\n"
    "t=threading.Thread(target=w)\n"
    "t.start()\n"
    "t.join()\n";

#ifdef BRIDGE
/* C7 P3b-6c slice (ii) — the interpreter's BRIDGE program (argv -c). The REAL unmodified python3.12 issues
 * ONE socket-family operation via a RAW syscall (ctypes -> glibc's syscall wrapper -> SYS_socket 41), so
 * serve.c routes it to the ring-0 bridge instead of the socket refusal. Whether the bridge relays it as a
 * clean op (the NORMAL build: the worker performs it, the interpreter receives its real answer) or a fault
 * (the -DBRIDGE_FAULT build: the worker faults mid-op, the bridge hands the interpreter an ERROR answer) is
 * a BUILD choice, not a script choice — so the SAME sealed image serves both. The interpreter PRINTS the
 * result (PYSOCK-R1) and reaches PYSOCK-DONE, proving it received the answer and continued (never left
 * waiting). The import set MUST match build.sh's BRIDGE strace SCRIPT. */
static const char g_bridge_script[] =
    "import ctypes\n"
    "libc=ctypes.CDLL(None,use_errno=True)\n"
    "libc.syscall.restype=ctypes.c_long\n"
    "r1=libc.syscall(41,2,1,0)\n"
    "print('PYSOCK-R1',r1)\n"
    "print('PYSOCK-DONE')\n";
#endif

#ifdef SOCKET_ACT
/* C7 P3b-6c slice (iii) — the interpreter's SOCKET-ACT program (argv -c). The REAL unmodified python3.12
 * drives a whole client connection via RAW syscalls (ctypes -> glibc's syscall wrapper): socket / ioctl
 * (FIONBIO) / connect / getsockopt(SO_ERROR) loop / sendto / recvfrom / close, to a numeric listener in the
 * outer guest at 10.0.2.2:5001 over nested SLIRP. Each shape crosses to serve.c, which RELAYS it across the
 * slice-(ii) bridge to the enclosed lwIP op-server worker; the worker performs it on its PERSISTENT
 * connection and drives 6a's NIC. The import set (ctypes,struct) MUST match build.sh's SOCKET_ACT SCRIPT. */
static const char g_sa_script[] =
    "import ctypes,struct\n"
    "libc=ctypes.CDLL(None,use_errno=True)\n"
    "libc.syscall.restype=ctypes.c_long\n"
    "def sc(*a):\n"
    " return libc.syscall(*[ctypes.c_long(x) for x in a])\n"
    "fd=sc(41,2,1,0)\n"                                   /* socket(AF_INET,SOCK_STREAM,0)        */
    "print('PYSOCK-FD',fd)\n"
    "one=ctypes.c_int(1)\n"
    "sc(16,fd,0x5421,ctypes.addressof(one))\n"           /* ioctl(FIONBIO,1) — non-blocking      */
    "addr=struct.pack('<H',2)+struct.pack('>H',5001)+bytes([10,0,2,2])+b'\\x00'*8\n"
    "ab=ctypes.create_string_buffer(addr,16)\n"
    "rc=sc(42,fd,ctypes.addressof(ab),16)\n"             /* connect(10.0.2.2:5001)               */
    "print('PYSOCK-CONNECT',rc)\n"
    "pb=ctypes.create_string_buffer(struct.pack('<ihh',fd,4,0),8)\n"  /* pollfd events=POLLOUT   */
    "pr=0\n"
    "rev=0\n"
    "for _ in range(50):\n"
    " pr=sc(7,ctypes.addressof(pb),1,200)\n"             /* poll(POLLOUT) — connected            */
    " rev=struct.unpack('<ihh',pb.raw)[2]\n"
    " if rev & 4: break\n"
    "print('PYSOCK-POLL',pr,rev)\n"
    "err=ctypes.c_int(-1)\n"
    "el=ctypes.c_int(4)\n"
    "sc(55,fd,1,4,ctypes.addressof(err),ctypes.addressof(el))\n"      /* getsockopt(SO_ERROR)    */
    "print('PYSOCK-SOERR',err.value)\n"
    "rok=0\n"
    "for i in range(12):\n"                              /* REPEATED relays over the one connection (A4) */
    " db=ctypes.create_string_buffer(b'ping',4)\n"
    " sc(44,fd,ctypes.addressof(db),4,0,0,0)\n"          /* sendto('ping')                        */
    " pb2=ctypes.create_string_buffer(struct.pack('<ihh',fd,1,0),8)\n"  /* pollfd events=POLLIN  */
    " j=0\n"
    " while j<50:\n"
    "  sc(7,ctypes.addressof(pb2),1,200)\n"              /* poll(POLLIN)                          */
    "  if struct.unpack('<ihh',pb2.raw)[2] & 1: break\n"
    "  j+=1\n"
    " rb=ctypes.create_string_buffer(64)\n"
    " rn=sc(45,fd,ctypes.addressof(rb),64,0,0,0)\n"      /* recvfrom -> 'pong'                    */
    " if rn>0: rok+=1\n"
    "print('PYSOCK-CYCLES',rok)\n"
    "sc(3,fd)\n"                                         /* close                                 */
    "print('PYSOCK-DONE')\n";
#endif

#if defined(GATE_ON_BODY)
/* C7 P3b-4g — THE GATE ON THE BODY. The argv (using the interpreter, not shaping it) that bootstraps
 * gov-os's OWN gate AS CONTENT off the record disk: a finder imports the gov-os TCB (keys/crypto/
 * canonical/signer + the seam) BY NAME from "/rec/..." via the body-read act (NEVER the borrowed
 * image, I7); reads the guest TEST key; signs a record row (MODELLED — libsodium absent, precision a)
 * with the estate's OWN keys.countersign; appends it through the RECORD-PEN act and reads it back
 * through the BODY-READ act; folds the crossing-trail file's DIGEST as ONE signed act-witness row
 * (L18); and writes an UNGATED row for the chain to refuse. The rows are copied out over serial for
 * the OFF-BODY verifier (the estate's own keys.verify_countersign). The body holds NO key. */
static const char g_gate_script[] =
    "REC = \"/rec/\"\n"
    "import sys, json, base64, hashlib\n"
    "import importlib.abc, importlib.machinery\n"
    "def _rd(name):\n"
    "    with open(REC + name, \"rb\") as f:        # body-read act (routed to the record disk)\n"
    "        return f.read()\n"
    "_MODMAP = {\n"
    "    \"kernel\": (\"ker_init.py\", True),\n"
    "    \"kernel.keys\": (\"keys.py\", False),\n"
    "    \"kernel.crypto\": (\"crypto.py\", False),\n"
    "    \"kernel.canonical\": (\"canonical.py\", False),\n"
    "    \"kernel.signer\": (\"signer.py\", False),\n"
    "    \"bridge\": (\"brg_init.py\", True),\n"
    "    \"bridge.host_seam\": (\"host_seam.py\", False),\n"
    "}\n"
    "class _RecFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):\n"
    "    def find_spec(self, fullname, path, target=None):\n"
    "        m = _MODMAP.get(fullname)\n"
    "        if m is None:\n"
    "            return None\n"
    "        ent, is_pkg = m\n"
    "        spec = importlib.machinery.ModuleSpec(fullname, self, is_package=is_pkg)\n"
    "        spec._ent = ent\n"
    "        return spec\n"
    "    def create_module(self, spec):\n"
    "        return None\n"
    "    def exec_module(self, module):\n"
    "        src = _rd(module.__spec__._ent)\n"
    "        exec(compile(src, \"rec:\" + module.__name__, \"exec\"), module.__dict__)\n"
    "sys.meta_path.insert(0, _RecFinder())\n"
    "from kernel import keys, signer, crypto  # noqa: E402 — the REAL estate gate, run as content\n"
    "from kernel.canonical import canonical_hash  # noqa: E402 — the estate's ONE hash form (the chain)\n"
    "seed = _rd(\"syskey\")\n"
    "sk = signer.SigningKeyStore()\n"
    "custody = sk.seal(seed)                        # the bound public custody half (estate code)\n"
    "GENESIS = {\"seq\": 0, \"record_time\": \"genesis\"}\n"
    "rec = {\"seq\": 1, \"record_time\": \"2026-09-14T00:00:00Z\",\n"
    "       \"actor\": \"system\", \"action\": \"gate-on-body\", \"object\": None,\n"
    "       \"prev_hash\": canonical_hash(GENESIS)}\n"
    "mark = keys.countersign(rec, custody)          # the estate's REAL countersignature (modelled era)\n"
    "signed = dict(rec)\n"
    "signed[\"countersign\"] = mark\n"
    "line = json.dumps(signed, sort_keys=True, separators=(\",\", \":\")).encode()\n"
    "with open(REC + \"record\", \"ab\") as f:\n"
    "    f.write(line + b\"\\n\")\n"
    "with open(REC + \"record\", \"rb\") as f:\n"
    "    readback = f.read()\n"
    "trail = _rd(\"trail\")\n"
    "tdig = \"sha256:\" + hashlib.sha256(trail).hexdigest()\n"
    "witness = {\"seq\": 2, \"record_time\": \"2026-09-14T00:00:01Z\",\n"
    "           \"actor\": \"system\", \"action\": \"act-witness\",\n"
    "           \"trail_digest\": tdig, \"crossings\": trail.count(b\"\\n\"),\n"
    "           \"prev_hash\": canonical_hash(signed)}\n"
    "wmark = keys.countersign(witness, custody)\n"
    "wsigned = dict(witness)\n"
    "wsigned[\"countersign\"] = wmark\n"
    "wline = json.dumps(wsigned, sort_keys=True, separators=(\",\", \":\")).encode()\n"
    "with open(REC + \"record\", \"ab\") as f:\n"
    "    f.write(wline + b\"\\n\")\n"
    "ungated = {\"seq\": 3, \"record_time\": \"2026-09-14T00:00:02Z\",\n"
    "           \"actor\": \"system\", \"action\": \"ungated\",\n"
    "           \"prev_hash\": canonical_hash(wsigned)}          # chained, but NO countersign\n"
    "uline = json.dumps(ungated, sort_keys=True, separators=(\",\", \":\")).encode()\n"
    "with open(REC + \"record\", \"ab\") as f:\n"
    "    f.write(uline + b\"\\n\")\n"
    "def _emit(tag, b):\n"
    "    sys.stdout.write(tag + \" \" + base64.b64encode(b).decode() + \"\\n\")\n"
    "sys.stdout.write(\"GATEONBODY-BEGIN\\n\")\n"
    "sys.stdout.write(\"GOB-CUSTODY \" + custody + \"\\n\")\n"
    "sys.stdout.write(\"GOB-REAL-AVAIL \" + str(crypto.real_available()) + \"\\n\")\n"
    "_emit(\"GOB-ROW-SIGNED\", line)\n"
    "_emit(\"GOB-ROW-READBACK\", readback)\n"
    "_emit(\"GOB-WITNESS\", wline)\n"
    "_emit(\"GOB-TRAIL\", trail)\n"
    "_emit(\"GOB-UNGATED\", uline)\n"
    "sys.stdout.write(\"GATEONBODY-END\\n\")\n"
    "sys.stdout.flush()\n";
#endif /* GATE_ON_BODY */

#if defined(LEDGER_ON_BODY)
/* C7 P3b-5b-i — THE LEDGER RUN STACK (design/54 §7 P3b-5b; archi :4303). The on-body argv runs an ESTATE
 * TEST MODULE whose name is DATA on the record disk (/rec/runmod — the per-module fresh image names its
 * module, precision 2). The bootstrap sets sys.path over the gov-os tree archive (/rec/src, /rec/tests;
 * -I ignores PYTHONPATH so it is set here, precision 2), routes tempfile under /rec (precision 4), and runs
 * the REAL module through the REAL unittest under the REAL interpreter, printing the REAL report AND exit
 * status to serial (precision 5). Imports resolve through CPython's OWN import machinery over the archive
 * served by path AND by listing (precision 3) — never a hardcoded module list. The PROVER IS NOT OURS
 * (L19): a planted assertion in the real module reddens the real run; nothing here reads or fabricates an
 * outcome. Choosing WHICH module to run is USING the interpreter, not shaping it. */
static const char g_ledger_script[] =
    "import sys\n"
    "sys.dont_write_bytecode = True\n"
    /* C7-MAINT-5B — THE RECORD TREE ROOT ON THE IMPORT SEARCH PATH. /rec/src and /rec/tests let a module
     * import by its DIRECT name, but a PACKAGE import (import tests.<x> — e.g. ep28e_w4's
     * `from tests.test_ep28e_w3 import ...`) needs the PARENT of tests/ on the path, i.e. /rec itself, so
     * CPython resolves `tests` as a namespace package over the archive served by listing. This adds only a
     * search-path entry; WHICH module runs (loadTestsFromName below) is untouched. */
#if !defined(PLANT_NO_REC_ON_PATH)
    "sys.path.insert(0, \"/rec\")\n"
#endif
    "sys.path.insert(0, \"/rec/src\")\n"
    "sys.path.insert(0, \"/rec/tests\")\n"
    "import os, tempfile\n"
    "try:\n"
    "    os.mkdir(\"/rec/tmp\")\n"
    "except OSError:\n"
    "    pass\n"
    "tempfile.tempdir = \"/rec/tmp\"\n"
    "with open(\"/rec/runmod\", \"rb\") as _f:\n"
    "    mod = _f.read().decode().strip()\n"
    "import unittest\n"
    "sys.stdout.write(\"LEDGER-RUN-BEGIN \" + mod + \"\\n\"); sys.stdout.flush()\n"
    "ok = False\n"
    "try:\n"
    /* /rec/tests is on sys.path, so the module imports by its DIRECT name — the body has no CWD=repo-root
     * that the host's `-m unittest tests.<mod>` relies on for the `tests.` package prefix; the RUN is the
     * same module, same tests (precision 2). */
    "    suite = unittest.TestLoader().loadTestsFromName(mod)\n"
    "    res = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)\n"
    "    ok = res.wasSuccessful()\n"
    "    sys.stdout.write(\"LEDGER-RESULT \" + (\"OK\" if ok else \"FAILED\")\n"
    "        + \" ran=\" + str(res.testsRun) + \" failures=\" + str(len(res.failures))\n"
    "        + \" errors=\" + str(len(res.errors)) + \" skipped=\" + str(len(res.skipped)) + \"\\n\")\n"
    "except BaseException as ex:\n"
    "    import traceback\n"
    "    traceback.print_exc(file=sys.stdout)\n"
    "    sys.stdout.write(\"LEDGER-RESULT LOADERROR \" + type(ex).__name__ + \"\\n\")\n"
    "    ok = False\n"
    "sys.stdout.write(\"LEDGER-RUN-END\\n\"); sys.stdout.flush()\n"
    "os._exit(0 if ok else 1)\n";
#endif /* LEDGER_ON_BODY */

#if defined(GRANT_FIRST)
/* C7 P3b-6c slice (iii) A1 — THE GRANT-FIRST PROGRAM (design/54 §5 L18/L19; §7 P3b-6c slice iii; the mgr
 * sub-split on the spike findings). The on-body argv runs gov-os's OWN gate AS CONTENT off the record disk:
 * build_full_kernel (the whole 30-module closure, genesis replaying the founding pack to served /rec/tmp) ->
 * CREATE-ACCOUNT (establish an opener) -> open_real_socket_under_grant (the RECORD decides SOCKET-OPEN first,
 * citing NET-LAW-GRANT; guest_check->False refuses the host fd AFTER the grant is recorded, so the DECISION
 * is proven without a real socket). The VEHICLE is test_ep48g's grant test's own operations (the shipped,
 * on-body-green gate — a REAL gate, never a fitted prover). Then, and ONLY on a GRANTED decision, the family
 * is handed to the proven 6c relay: the interpreter's socket-family shapes (drive_relay, byte-identical to
 * g_sa_script) cross to serve.c, which relays each to the enclosed lwIP worker over one guest-local
 * connection. A REFUSED decision (an unestablished opener) raises at the gate before any socket() and reaches
 * NO relay (GRANT_REFUSED). The mode is injected as two constants (_MODE/_BYPASS); the PLANT (PLANT_GRANT_
 * BYPASS) drives the relay on a refusal ANYWAY, and the grant-first verdict — which expects zero relays on a
 * refusal — reds. The body sees crossings, not grants (serve.c): the grant-first gate is here, in gov-os's
 * own code, exactly as EP-48 rules it. Imports resolve through CPython's OWN machinery over the whole-stdlib
 * sealed image + the GOVOS_TREE record disk (served by path AND by listing). */
static const char g_grant_script[] =
    "import sys\n"
    "sys.dont_write_bytecode = True\n"
    "sys.path.insert(0, \"/rec\")\n"
    "sys.path.insert(0, \"/rec/src\")\n"
    "sys.path.insert(0, \"/rec/tests\")\n"
    "import os, tempfile\n"
    "try:\n"
    "    os.mkdir(\"/rec/tmp\")\n"
    "except OSError:\n"
    "    pass\n"
    "tempfile.tempdir = \"/rec/tmp\"\n"
    "import ctypes, struct\n"                                 /* the relay closure (whole-stdlib image) */
    "def drive_relay():\n"                                    /* g_sa_script's shapes, byte-identical    */
    "    libc = ctypes.CDLL(None, use_errno=True)\n"
    "    libc.syscall.restype = ctypes.c_long\n"
    "    def sc(*a):\n"
    "        return libc.syscall(*[ctypes.c_long(x) for x in a])\n"
    "    fd = sc(41, 2, 1, 0)\n"                              /* socket(AF_INET,SOCK_STREAM,0)          */
    "    sys.stdout.write(\"PYSOCK-FD \" + str(fd) + \"\\n\")\n"
    "    one = ctypes.c_int(1)\n"
    "    sc(16, fd, 0x5421, ctypes.addressof(one))\n"          /* ioctl(FIONBIO,1)                       */
    "    addr = struct.pack(\"<H\", 2) + struct.pack(\">H\", 5001) + bytes([10,0,2,2]) + b\"\\x00\"*8\n"
    "    ab = ctypes.create_string_buffer(addr, 16)\n"
    "    rc = sc(42, fd, ctypes.addressof(ab), 16)\n"          /* connect(10.0.2.2:5001)                 */
    "    sys.stdout.write(\"PYSOCK-CONNECT \" + str(rc) + \"\\n\")\n"
    "    pb = ctypes.create_string_buffer(struct.pack(\"<ihh\", fd, 4, 0), 8)\n"
    "    pr = 0\n"
    "    rev = 0\n"
    "    for _ in range(50):\n"
    "        pr = sc(7, ctypes.addressof(pb), 1, 200)\n"       /* poll(POLLOUT)                          */
    "        rev = struct.unpack(\"<ihh\", pb.raw)[2]\n"
    "        if rev & 4: break\n"
    "    sys.stdout.write(\"PYSOCK-POLL \" + str(pr) + \" \" + str(rev) + \"\\n\")\n"
    "    err = ctypes.c_int(-1)\n"
    "    el = ctypes.c_int(4)\n"
    "    sc(55, fd, 1, 4, ctypes.addressof(err), ctypes.addressof(el))\n"   /* getsockopt(SO_ERROR)    */
    "    sys.stdout.write(\"PYSOCK-SOERR \" + str(err.value) + \"\\n\")\n"
    "    rok = 0\n"
    "    for i in range(12):\n"                               /* REPEATED relays over the one connection */
    "        db = ctypes.create_string_buffer(b\"ping\", 4)\n"
    "        sc(44, fd, ctypes.addressof(db), 4, 0, 0, 0)\n"   /* sendto('ping')                         */
    "        pb2 = ctypes.create_string_buffer(struct.pack(\"<ihh\", fd, 1, 0), 8)\n"
    "        j = 0\n"
    "        while j < 50:\n"
    "            sc(7, ctypes.addressof(pb2), 1, 200)\n"       /* poll(POLLIN)                           */
    "            if struct.unpack(\"<ihh\", pb2.raw)[2] & 1: break\n"
    "            j += 1\n"
    "        rb = ctypes.create_string_buffer(64)\n"
    "        rn = sc(45, fd, ctypes.addressof(rb), 64, 0, 0, 0)\n"   /* recvfrom -> 'pong'              */
    "        if rn > 0: rok += 1\n"
    "    sys.stdout.write(\"PYSOCK-CYCLES \" + str(rok) + \"\\n\")\n"
    "    sc(3, fd)\n"                                          /* close                                 */
    "    sys.stdout.write(\"PYSOCK-DONE\\n\")\n"
    "sys.stdout.write(\"GRANT-BEGIN\\n\"); sys.stdout.flush()\n"
    "try:\n"
    "    from bridge import kernel_port\n"
    "    from kernel.compose import build_full_kernel\n"
    "    from kernel.errors import OpError\n"
    "    from kernel.syscall_port import SyscallPort\n"
    "    from subsystems.sockets import SocketView\n"
    "    d = tempfile.mkdtemp(prefix=\"grant-\")\n"
    "    store, gate, views, blobs, subs = build_full_kernel(\n"
    "        os.path.join(d, \"record.jsonl\"), os.path.join(d, \"blobs\"), os.path.join(d, \"vault\"))\n"
    "    sys.stdout.write(\"GRANT-COMPOSED\\n\"); sys.stdout.flush()\n"
    "    errno = SyscallPort(gate, views)._errno_for(\"NET-LAW-GRANT\")\n"
    "    sys.stdout.write(\"GRANT-ERRNO \" + str(errno) + \"\\n\")\n"
#if defined(GRANT_REFUSED)
    "    _MODE = \"refused\"\n"
#else
    "    _MODE = \"granted\"\n"
#endif
#if defined(PLANT_GRANT_BYPASS)
    "    _BYPASS = True\n"
#else
    "    _BYPASS = False\n"
#endif
    "    if _MODE == \"refused\":\n"
    /* A3: an UNESTABLISHED opener -> OpError at the gate BEFORE any socket; the refusal renders EACCES. */
    "        raised = False\n"
    "        try:\n"
    "            kernel_port.open_real_socket_under_grant(gate, \"ghost\", \"g1\", \"inet\", guest_check=lambda: True)\n"
    "        except OpError as e:\n"
    "            raised = (e.rule == \"NET-LAW-GRANT\")\n"
    "        live = SocketView(store).live_sockets()\n"
    "        sys.stdout.write(\"GRANT-A3-REFUSED raised=\" + str(raised) + \" g1-live=\"\n"
    "                         + str(\"g1\" in live) + \" errno=\" + str(errno) + \"\\n\"); sys.stdout.flush()\n"
    "        if _BYPASS:\n"                                    /* THE PLANT (L19): relay on a refusal    */
    "            drive_relay()\n"
    "        else:\n"
    "            sys.stdout.write(\"GRANT-A3-NO-RELAY\\n\")\n"
    "    else:\n"
    /* A1: gov-os's gate records SOCKET-OPEN citing NET-LAW-GRANT FIRST (guest_check->False, no host fd). */
    "        gate.execute(\"CREATE-ACCOUNT\", \"owner\", {\"account_id\": \"web\", \"actor_class\": \"human\"})\n"
    "        granted = False\n"
    "        try:\n"
    "            kernel_port.open_real_socket_under_grant(gate, \"web\", \"s1\", \"inet\", guest_check=lambda: False)\n"
    "        except kernel_port.RealSocketOnHostRefused:\n"
    "            pass\n"                                        /* the grant IS on the record             */
    "        dec = [e for e in store.by_action(\"SOCKET-OPEN\")]\n"
    "        rc0 = dec[-1].get(\"rule_cited\") if dec else None\n"
    "        if dec and rc0 == \"NET-LAW-GRANT\" and \"s1\" in SocketView(store).live_sockets():\n"
    "            granted = True\n"
    "        sys.stdout.write(\"GRANT-A1-GRANTED granted=\" + str(granted) + \" rule=\" + str(rc0) + \"\\n\")\n"
    /* A1 PLANT (able-to-fail): an UNESTABLISHED opener -> OpError, NO SOCKET-OPEN row for it, no socket. */
    "        plant_ok = False\n"
    "        try:\n"
    "            kernel_port.open_real_socket_under_grant(gate, \"ghost\", \"g1\", \"inet\", guest_check=lambda: True)\n"
    "        except OpError as e:\n"
    "            plant_ok = (e.rule == \"NET-LAW-GRANT\") and (\"g1\" not in SocketView(store).live_sockets())\n"
    "        sys.stdout.write(\"GRANT-A1-PLANT-OPERROR plant_ok=\" + str(plant_ok) + \"\\n\"); sys.stdout.flush()\n"
    /* A2: ONLY a granted decision hands to the proven relay -> one real guest-local connection. */
    "        if granted and plant_ok:\n"
    "            sys.stdout.write(\"GRANT-A2-HANDOFF\\n\"); sys.stdout.flush()\n"
    "            drive_relay()\n"
    "        else:\n"
    "            sys.stdout.write(\"GRANT-A2-NO-HANDOFF\\n\")\n"
    "    sys.stdout.write(\"GRANT-DONE\\n\"); sys.stdout.flush()\n"
    "except BaseException as ex:\n"
    "    import traceback\n"
    "    traceback.print_exc(file=sys.stdout)\n"
    "    sys.stdout.write(\"GRANT-LOADERROR \" + type(ex).__name__ + \"\\n\")\n"
    "sys.stdout.flush()\n";
#endif /* GRANT_FIRST */

static uint32_t i_strlen(const char *s) { uint32_t n = 0; while (s[n]) { n++; } return n; }

/* load the REAL interpreter (ET_EXEC) from the sealed image by path: map its PT_LOAD segments as USER pages
 * (bytes FROM THE SEALED IMAGE — serve_fs_find, never an incbin'd blob), record e_entry/AT_PHDR/PHENT/PHNUM
 * and the initial break, and read its PT_INTERP (the requested linker). Mirrors floor_load_prover, reading
 * the program from the image. The whole-image digest was already checked at the seal. */
static int floor3_load_program_from_image(const char *path) {
    uint32_t plen = 0; int isdir = 0;
    const uint8_t *img = serve_fs_find(path, &plen, &isdir);
    if (!img || isdir) { return -1; }
    const struct elf64_ehdr *eh = (const struct elf64_ehdr *)img;
    if (!(eh->e_ident[0] == 0x7f && eh->e_ident[1] == 'E'
          && eh->e_ident[2] == 'L' && eh->e_ident[3] == 'F')) { return -1; }
    if (eh->e_ident[4] != 2) { return -1; }        /* ELFCLASS64                        */
    if (eh->e_machine != 62) { return -1; }        /* EM_X86_64                         */
    if (eh->e_type != 2) { return -1; }            /* ET_EXEC — the interpreter's fixed base (L20) */
    const struct elf64_phdr *ph = (const struct elf64_phdr *)(img + eh->e_phoff);
    uint64_t maxv = 0;
    g_interp_path[0] = '\0';
    for (int i = 0; i < eh->e_phnum; i++) {
        if (ph[i].p_type == PT_LOAD) {
            if (map_segment(ph[i].p_vaddr, ph[i].p_offset, ph[i].p_filesz, ph[i].p_memsz, img) != 0) {
                return -1;
            }
            uint64_t end = ph[i].p_vaddr + ph[i].p_memsz;
            if (end > maxv) { maxv = end; }
            if (ph[i].p_offset <= eh->e_phoff && eh->e_phoff < ph[i].p_offset + ph[i].p_filesz) {
                g_floor_phdr_va = ph[i].p_vaddr + (eh->e_phoff - ph[i].p_offset);
            }
        } else if (ph[i].p_type == PT_INTERP) {
            uint64_t off = ph[i].p_offset, len = ph[i].p_filesz;
            uint64_t cap = (len < 127u) ? len : 127u;
            for (uint64_t k = 0; k < cap; k++) { g_interp_path[k] = (char)img[off + k]; }
            g_interp_path[cap] = '\0';
        }
    }
    g_floor_entry     = eh->e_entry;
    g_floor_phnum     = eh->e_phnum;
    g_floor_phent     = eh->e_phentsize;
    g_floor_max_vaddr = maxv;
    return (g_interp_path[0] == '\0') ? -1 : 0;    /* must be dynamically linked (a PT_INTERP) */
}

/* lay the interpreter's initial SysV stack: argc=5, argv = {python3, -I, -S, -c, <script>}, an empty envp,
 * and the auxiliary vector (AT_PAGESZ/PHDR/PHENT/PHNUM/ENTRY/RANDOM/EXECFN[/BASE]/NULL). The argv strings +
 * AT_RANDOM's 16 bytes sit at the top of the stack; the vector 16-aligned below them. Choosing the program
 * (argv) is using the interpreter, not shaping it. */
static void floor3_build_python_stack(void) {
    for (uint64_t p = INTERP_STACK_BOT; p < INTERP_STACK_TOP; p += 0x1000ull) {
        uint32_t f = pmm_alloc();
        if (f == 0) { return; }
        if (vmm_map_user(p, (uint64_t)f) != 0) { return; }
        uint8_t *z = (uint8_t *)phys_to_virt(f);
        for (int i = 0; i < 4096; i++) { z[i] = 0; }
    }
    uint64_t sp = INTERP_STACK_TOP;
    sp -= 16; uint64_t va_random = sp;                 /* AT_RANDOM's 16 bytes */
    uint8_t rnd[16];
#if defined(PLANT_AT_RANDOM_CONSTANT)
    for (int i = 0; i < 16; i++) { rnd[i] = 0x5A; }
#else
    entropy_draw(rnd, 16);
#endif
    for (int i = 0; i < 16; i++) { ((volatile uint8_t *)(uintptr_t)va_random)[i] = rnd[i]; }

    const char *args[5];
    args[0] = INTERP_PROGRAM_PATH; args[1] = "-I"; args[2] = "-S"; args[3] = "-c";
#if defined(GRANT_FIRST)
    args[4] = g_grant_script;   /* C7 P3b-6c (iii) A1: gov-os's own gate decides the open, then hands a
                                 * granted decision to the relay (GRANT_FIRST implies SOCKET_ACT) */
#elif defined(SOCKET_ACT)
    args[4] = g_sa_script;      /* C7 P3b-6c (iii): drive a whole client connection -> the socket-act relay */
#elif defined(BRIDGE)
    args[4] = g_bridge_script;  /* C7 P3b-6c (ii): issue ONE socket op per relay -> the ring-0 bridge */
#elif defined(LEDGER_ON_BODY)
    args[4] = g_ledger_script;  /* C7 P3b-5b-i: run an estate test module named as data on the record disk */
#elif defined(GATE_ON_BODY)
    args[4] = g_gate_script;    /* C7 P3b-4g: run gov-os's own gate as content off the record disk */
#else
    args[4] = g_py_script;
#endif
    uint64_t argp[5];
    for (int i = 4; i >= 0; i--) {                      /* copy the strings descending; keep the pointers */
        uint32_t L = i_strlen(args[i]) + 1u;
        sp -= L;
        volatile char *d = (volatile char *)(uintptr_t)sp;
        for (uint32_t k = 0; k < L; k++) { d[k] = args[i][k]; }
        argp[i] = sp;
    }

    uint64_t rsp = (sp - 512) & ~0xFull;               /* the SysV vector, 16-aligned, below the strings */
    volatile uint64_t *v = (volatile uint64_t *)(uintptr_t)rsp;
    int k = 0;
    v[k++] = 5;                                        /* argc */
    for (int i = 0; i < 5; i++) { v[k++] = argp[i]; }  /* argv[0..4] */
    v[k++] = 0;                                        /* argv terminator */
    v[k++] = 0;                                        /* envp terminator (empty — -I ignores the environment) */
    v[k++] = AT_PAGESZ; v[k++] = 4096;
    v[k++] = AT_PHDR;   v[k++] = g_floor_phdr_va;
    v[k++] = AT_PHENT;  v[k++] = g_floor_phent;
    v[k++] = AT_PHNUM;  v[k++] = g_floor_phnum;
    v[k++] = AT_ENTRY;  v[k++] = g_floor_entry;
    v[k++] = AT_RANDOM; v[k++] = va_random;
    v[k++] = AT_EXECFN; v[k++] = argp[0];              /* sys.executable falls back here (readlink ENOSYS) */
    if (g_dyn_ld_base) { v[k++] = AT_BASE; v[k++] = g_dyn_ld_base; }
    v[k++] = AT_NULL;   v[k++] = 0;
    g_floor_rsp = rsp;
}

int floor3_interp_run(void) {
    serial_puts("FLOOR3C: the interpreter runs on the body — the REAL unmodified /usr/bin/python3.12, loaded "
                "by the body's own dynamic loader from the ONE sealed image (interp + C library + stdlib as "
                "real files, digest-checked, served by path+listing) on the real floor through the real "
                "linker; print(2+2) and a thread run FOR REAL (L19, the prover is not ours to write)\n");
    floor_enable_sse();

    if (g_sealed_module_phys == 0 || g_sealed_module_len == 0) {
        serial_puts("FLOOR3C: FAIL (no sealed-image module — boot the nested guest with -initrd sealed.img)\n");
        return 1;
    }
    const uint8_t *img = (const uint8_t *)phys_to_virt(g_sealed_module_phys);   /* the module, via the direct map */
    uint32_t img_len = (uint32_t)g_sealed_module_len;

    /* (A1/B6) THE SEAL — digest-check the whole image before any load; a byte change refuses it and the
     * interpreter never starts (a real failure, not a flag). */
    uint8_t got[32];
    sha256(img, img_len, got);
    serial_puts("FLOOR3C-SEAL-LEN: 0x"); serial_puthex32(img_len); serial_puts("\n");
    serial_puts("FLOOR3C-SEAL-SHA256: "); put_hex_digest(got, 32); serial_puts("\n");
    if (!digest_matches_hex(got, SEALED_IMG_SHA256HEX)) {
        serial_puts("FLOOR3C-SEAL: REFUSED (digest mismatch — the sealed image is not the sealed bytes)\n");
        serial_puts("FLOOR3C: FAIL (the sealed image was refused at load — the interpreter never starts)\n");
        return 1;
    }
    serial_puts("FLOOR3C-SEAL: OK (digest matches the seal)\n");

    int nent = serve_fs_set_image(img, img_len);
    if (nent < 0) { serial_puts("FLOOR3C: FAIL (the sealed image is not a GOVSIMG1 archive)\n"); return 1; }
    serial_puts("FLOOR3C-IMAGE: 0x"); serial_puthex32((uint32_t)nent); serial_puts(" entries\n");

    /* load the REAL interpreter (ET_EXEC at 0x400000) from the sealed image; read its PT_INTERP. */
    if (floor3_load_program_from_image(INTERP_PROGRAM_PATH) != 0) {
        serial_puts("FLOOR3C: FAIL (the interpreter is not in the sealed image, or not a dynamic ET_EXEC)\n");
        return 1;
    }
    serial_puts("FLOOR3C-INTERP: "); serial_puts(g_interp_path); serial_puts("\n");

    /* load that ld.so (ET_DYN) from the sealed image at LD_LOAD_BASE; record its entry + AT_BASE. */
    if (floor3_load_interp(g_interp_path) != 0) {
        serial_puts("FLOOR3C: FAIL (the dynamic linker is not in the sealed image, or not ET_DYN)\n");
        return 1;
    }

    /* the image is served BY LISTING — CPython's importlib lists each sys.path directory once per import
     * (Q15/:4134); the P3b-2 record FS is mounted beside the read-only image with distinct namespaces. */
    char dir[128], base[128];
    floor3_split(g_interp_path, dir, base, 128);
    int listable = serve_fs_listable_check(dir, base);
    serial_puts(listable ? "FLOOR3C-LISTABLE: OK\n" : "FLOOR3C-LISTABLE: FAIL\n");
    int beside = serve_fs_beside_check();
    serial_puts(beside ? "FLOOR3C-BESIDE: OK\n" : "FLOOR3C-BESIDE: FAIL\n");

    serve_set_brk_base((g_floor_max_vaddr + 0xFFFull) & ~0xFFFull);
    floor3_build_python_stack();
    wrmsr(0xC0000100u, 0);                      /* main %fs reset; ld.so installs the base via arch_prctl */

    pit_init(SCHED_PIT_HZ);
    sched_init();

    uint64_t target = g_dyn_entry;              /* hand over to ld.so — it relocates the interpreter + libs */
#if defined(PLANT_SKIP_INTERP)
    target = g_floor_entry; g_dyn_ld_base = 0;  /* enter the interpreter with libc unrelocated -> #PF */
#endif
    serial_puts("FLOOR3C-HANDOVER: entry=0x"); serial_puthex64(target);
    serial_puts(" ld_base=0x"); serial_puthex64(g_dyn_ld_base); serial_puts("\n");

    g_serve_phase = 1;
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        interrupts_enable();
        enter_ring3_main(target, g_floor_rsp);  /* the interpreter exit_group's (jv 1) or faults (jv 2) */
    }
    interrupts_disable();
    g_in_worker = 0;
    g_serve_phase = 0;
    g_sched_on = 0;

    if (jv == 2) {
        serial_puts("FLOOR3C-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
        serial_puts(" cr2=0x");               serial_puthex64(g_worker_cr2);
        serial_puts(" faultcs=0x");           serial_puthex32((uint32_t)g_worker_faultcs);
        serial_puts(" tid=0x");               serial_puthex32(g_sched_cur_tid);
        serial_puts(" rip=0x");               serial_puthex64(g_worker_rip); serial_puts("\n");
        serial_puts("FLOOR3C: FAIL (the interpreter FAULTED — a floor / linker / sealed-FS piece is missing)\n");
        return 1;
    }

    int live_walk = serve_fs_live_walk();
    uint32_t outside = serve_fs_outside_refusals();
    int nowalk = (live_walk == 0) && (outside > 0);   /* no fabricated hit; the designed refusal exercised */
    serial_puts("FLOOR3C-OUTSIDE-REFUSALS: 0x"); serial_puthex32(outside); serial_puts("\n");
    serial_puts(nowalk ? "FLOOR3C-NOWALK: OK\n" : "FLOOR3C-NOWALK: FAIL\n");
    serial_puts("FLOOR3C-THREADS: 0x"); serial_puthex32(g_sched_threads_created); serial_puts("\n");
    serial_puts("FLOOR3C-EXITS: 0x");   serial_puthex32(g_sched_exits);           serial_puts("\n");
    /* C7-MAINT-5B-THREAD-SLOT-RECLAIM (:4460 — the close shows a reused slot's new tid greater than every tid
     * before it): the highest tid handed out (g_next_tid-1). tids are fresh + monotonic (g_next_tid++, never
     * reset), so when cumulative creations exceed SCHED_MAX_THREADS the max tid exceeds the slot count — a
     * reclaimed slot was re-born with a tid greater than every tid before it, never the zombie's number. */
    serial_puts("FLOOR3C-MAXTID: 0x");  serial_puthex32(g_next_tid ? g_next_tid - 1u : 0u); serial_puts("\n");

#if defined(LEDGER_ON_BODY)
    /* C7 P3b-5b-i: the ledger run executed a REAL estate test module through the REAL unittest on the body.
     * The body's job is to run it TO COMPLETION; the GREEN/RED verdict is the module's own — carried on
     * serial as LEDGER-RESULT and as the REAL exit status below (0 green / 1 red, precision 5). A red module
     * is a COMPLETED run with exit 1 (correct behaviour, never a body FAIL); the host test gates
     * module-green on OK + exit 0 and plant-red on FAILED + exit 1. */
    serial_puts("LEDGER-EXIT-STATUS: 0x"); serial_puthex32((uint32_t)g_serve_exit_status); serial_puts("\n");
    int ok = (jv == 1) && listable && beside && nowalk;
    serial_puts(ok ? "FLOOR3L: COMPLETED (an estate test module ran to completion on the body)\n"
                   : "FLOOR3L: FAIL (the module run did not complete on the body)\n");
#elif defined(GATE_ON_BODY)
    /* C7 P3b-4g: the gate-on-body run signs a record row (no thread of its own); PASS = the interpreter
     * ran gov-os's own gate to completion off the record disk. The rows' verification is the OFF-BODY
     * reader's (the estate's own keys.verify_countersign), parsed from the GATEONBODY serial lines. */
    int ok = (jv == 1) && listable && beside && nowalk;
    serial_puts(ok ? "FLOOR3G: PASS (gov-os's own gate ran as content on the body and signed a record row)\n"
                   : "FLOOR3G: FAIL (the gate-on-body run did not complete on the body)\n");
#else
    int ok = (jv == 1) && listable && beside && nowalk && (g_sched_threads_created >= 1);
    serial_puts(ok ? "FLOOR3C: PASS (the real unmodified interpreter ran on the body — print(2+2) and a thread)\n"
                   : "FLOOR3C: FAIL (the interpreter did not run to completion on the body)\n");
#endif
    return ok ? 0 : 1;
}
#endif /* INTERP_FLOOR */
#endif /* DYNAMIC_FLOOR */

#ifdef NET_WORKER
/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6b — THE BORROWED TCP ENCLOSED (design/54 §5 L18/L5/L19/I3, §7 P3b-6b). The body hosts a SECOND
 * enclosed worker: lwIP 2.2.0 (the static NO_SYS build from the guest archive's SOURCE, UNMODIFIED), sealed
 * and digest-checked like the interpreter (A1). Its OWN per-enclosure served set is its whole-process
 * measured set (the twenty + clock, DECLARED as data — never the eight; A2), plus the three body-native
 * frame shapes; a shape beyond it is refused BY NAME, the interpreter's fifty untouched (L18). The stack's
 * OWN example (lwiperf's client) is the prover (L19): it opens ONE guest-local connection OUTBOUND through
 * 6a's NIC over nested SLIRP and completes a real exchange (A3). Every frame is a row (A4). The heap holds
 * the measured high-water (A5). Our glue is configuration only; the stack + its libc are CONTENT, never in
 * the signed base (A6/I3). NO new act (ACT_KINDS stays twelve). Reuses the static floor's loader, stack and
 * ring-3 crossing; the worker is the sealed prover_image (built + sealed by build.sh's NET_WORKER path).
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/
int floor_net_run(void) {
    interrupts_disable();   /* a deterministic worker run (the clock slice proved interrupts already) */
    serial_puts("NET-WORKER: the borrowed TCP stack enclosed — lwIP 2.2.0 (static NO_SYS from the guest "
                "archive SOURCE, UNMODIFIED) as a SECOND enclosed worker; its per-enclosure served set is "
                "its whole-process measured set declared as data (never the eight); the stack's OWN lwiperf "
                "client opens ONE connection through our NIC over nested SLIRP; every frame a row "
                "(L18/L5/L19/I3)\n");
    floor_enable_sse();

    /* A1 — the sealed static lwIP worker (the prover_image), DIGEST-CHECKED before load (FLOOR-LOAD: OK). */
    if (floor_load_prover() != 0) {
        serial_puts("NET-WORKER: FAIL (the sealed lwIP worker was refused at load — A1 seal)\n");
        return 1;
    }

    /* bring up 6a's NIC (a full reset) so the frame crossings have a live device. */
    uint8_t mac[6];
    int nst = net_nic_bringup(mac);
    serial_puts(nst == 0 ? "NET-WORKER-NIC: UP\n"
              : nst == 2 ? "NET-WORKER-NIC: ABSENT\n" : "NET-WORKER-NIC: FAIL\n");
    if (nst != 0) {
        serial_puts("NET-WORKER: FAIL (no live NIC to cross frames to — attach a virtio-net device)\n");
        return 1;
    }

    /* the program break just above the loaded image; lay the static loader's stack + auxv. */
    serve_set_brk_base((g_floor_max_vaddr + 0xFFFull) & ~0xFFFull);
    floor_build_stack();
    wrmsr(0xC0000100u, 0);   /* reset %fs: glibc installs its own via arch_prctl (a #PF if it does not) */

    /* the borrowed stack reads a real MONOTONIC clock (sys_now: retransmit timers, the session timer) — so
     * run the PIT and let the timer advance the tick clock during the ring-3 run (like the concurrency
     * floor, but NO scheduler: g_sched_on stays 0, so the timer only advances ticks, it never switches). */
    pit_init(SCHED_PIT_HZ);

    /* calibrate the worker's rdtsc clock (sys_now) against the PIT: enable interrupts, read rdtsc, spin
     * over a known number of ticks (SCHED_PIT_HZ = 1000/s, so 100 ticks == 100 ms), read rdtsc again ->
     * cycles/ms. rdtsc advances regardless of ring level, so sys_now works while the worker sits in its
     * frame syscalls. Done at ring 0 with no worker running (g_in_worker == 0). */
    interrupts_enable();
    {
        uint64_t c0 = rdtsc();
        uint32_t t0 = ticks_get(), t1;
        while ((t1 = ticks_get()) - t0 < 100u) { __asm__ volatile("pause"); }
        uint64_t c1 = rdtsc();
        uint64_t per_ms = (c1 - c0) / (uint64_t)(t1 - t0);   /* ticks are ms at SCHED_PIT_HZ=1000 */
        if (per_ms == 0) { per_ms = 1; }
        serve_net_clock_calibrate(c1, per_ms);
        serial_puts("NET-WORKER-TSC-PER-MS: 0x"); serial_puthex64(per_ms); serial_puts("\n");
    }
    interrupts_disable();

    /* run the worker as the SECOND enclosure — serve_request gates on the lwIP declared set (L18). */
    g_serve_enclosure = ENCL_LWIP;
    g_serve_phase = 1;
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_serve_exited = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        /* interrupts stay OFF for a deterministic run (like the static floor); sys_now is rdtsc-based, so
         * the clock advances without the tick timer. */
        enter_ring3(g_floor_entry, g_floor_rsp, 0, 0);
        /* unreachable — the worker exit_group's (longjmp 1) or faults (longjmp 2) */
    }
    g_in_worker = 0;
    g_serve_phase = 0;
    g_serve_enclosure = ENCL_INTERP;

    if (jv == 2) {
        serial_puts("NET-WORKER-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
        serial_puts(" cr2=0x");                   serial_puthex64(g_worker_cr2);
        serial_puts(" rip=0x");                   serial_puthex64(g_worker_rip); serial_puts("\n");
    }

    int enclosed_ran = (jv == 1) && g_serve_exited && (g_worker_fault == 0);   /* ran enclosed to an exit  */
    int worker_ok    = enclosed_ran && (g_serve_exit_status == 0);             /* + clean exit (conn ok)   */

    /* ── the checks (each machine-read, each with a plant that reds it) ── */
    /* A1 — the sealed static lwIP worker (seal matched at load, gated above) ran UNPRIVILEGED and enclosed
     * (ring 3, through the crossing) to a clean exit; a tampered seal was refused at load (the A1 plant). */
    int a1 = enclosed_ran;

    /* A2 — the served set is the whole-process TWENTY (+clock), declared as data, NEVER the eight: the
     * PRE-MAIN shapes the eight (after-main) excluded are declared; a shape beyond the set is refused BY
     * NAME; and the real worker served ONLY its declared set (g_lwip_beyond_served stayed 0). */
    int set_is_twenty = serve_declared(ENCL_LWIP, SYS_arch_prctl)         /* pre-main — in the 20, not the 8 */
                     && serve_declared(ENCL_LWIP, SYS_set_tid_address)     /* pre-main — in the 20, not the 8 */
                     && serve_declared(ENCL_LWIP, SYS_mmap)                /* pre-main — in the 20, not the 8 */
                     && serve_declared(ENCL_LWIP, SYS_prlimit64)           /* pre-main — in the 20, not the 8 */
                     && serve_declared(ENCL_LWIP, SYS_clock_gettime);      /* sys_now — the clock shape       */
    int beyond_refused = (serve_declared(ENCL_LWIP, SYS_socket) == 0)      /* beyond the 20 -> refused BY NAME */
                      && (serve_declared(ENCL_LWIP, SYS_clone3) == 0)
                      && (serve_declared(ENCL_LWIP, SYS_readlink) == 0);
    int worker_in_set = (g_lwip_beyond_served == 0);                       /* the real worker stayed in-set   */
    int a2 = set_is_twenty && beyond_refused && worker_in_set;

    /* A2 (per-enclosure, L18) — a frame shape refused to the interpreter's enclosure; an interpreter-only
     * shape refused to the lwIP one; the interpreter's own shapes still served (its fifty untouched). */
    int cross = (serve_declared(ENCL_INTERP, REQ_SEND_FRAME) == 0)   /* frame shape -> interpreter: refused  */
             && (serve_declared(ENCL_INTERP, REQ_RECV_FRAME) == 0)
             && (serve_declared(ENCL_INTERP, SYS_write) == 1)        /* the interpreter's own: still served  */
             && (serve_declared(ENCL_INTERP, SYS_clone3) == 1)       /* an interpreter-only shape: served    */
             && (serve_declared(ENCL_LWIP, SYS_clone3) == 0);        /* the SAME shape -> lwIP: refused      */

    /* A3 — the stack's OWN example opened ONE connection through our NIC (frames BOTH ways) and reported
     * cleanly (exit 0). The reply came from a real remote party over SLIRP (proven peer-side + here). */
    int a3 = worker_ok && (g_frames_sent > 0) && (g_frames_recv > 0);

    /* A4 — every frame is a row: the rows appended == the frames that crossed (a plant skips one -> reds). */
    int a4 = ((g_frames_sent + g_frames_recv) > 0)
          && (g_frame_rows == g_frames_sent + g_frames_recv);

    /* A5 — the worker's heap reached the measured high-water (a positive control that real memory flowed);
     * PLANT_LWIP_HEAP_SMALL sizes the budget below it, starving the connection. */
    int a5 = (g_lwip_mem_peak >= 17048ull);

    serial_puts("NET-WORKER-FRAMES-SENT: 0x"); serial_puthex32(g_frames_sent);
    serial_puts(" RECV: 0x");                   serial_puthex32(g_frames_recv);
    serial_puts(" ROWS: 0x");                   serial_puthex32(g_frame_rows); serial_puts("\n");
    serial_puts("NET-WORKER-HEAP-PEAK: 0x");    serial_puthex64(g_lwip_mem_peak); serial_puts("\n");
    serial_puts("NET-WORKER-EXIT: 0x");         serial_puthex32((uint32_t)g_serve_exit_status); serial_puts("\n");
    serial_puts("NET-WORKER-BEYOND-SERVED: 0x");serial_puthex32(g_lwip_beyond_served); serial_puts("\n");

    serial_puts(a1        ? "CHECK NETW-SEALED: PASS\n"        : "CHECK NETW-SEALED: FAIL\n");
    serial_puts(a2        ? "CHECK NETW-SERVED-SET: PASS\n"    : "CHECK NETW-SERVED-SET: FAIL\n");
    serial_puts(cross     ? "CHECK NETW-PER-ENCLOSURE: PASS\n" : "CHECK NETW-PER-ENCLOSURE: FAIL\n");
    serial_puts(a3        ? "CHECK NETW-CONNECTION: PASS\n"    : "CHECK NETW-CONNECTION: FAIL\n");
    serial_puts(a4        ? "CHECK NETW-FRAME-TRAIL: PASS\n"   : "CHECK NETW-FRAME-TRAIL: FAIL\n");
    serial_puts(a5        ? "CHECK NETW-SIZED: PASS\n"         : "CHECK NETW-SIZED: FAIL\n");

    int all = a1 && a2 && cross && a3 && a4 && a5;
    serial_puts(all ? "NET-WORKER: PASS\n" : "NET-WORKER: FAIL\n");
    return all ? 0 : 1;
}
#endif /* NET_WORKER */

#endif /* PROVER_PRESENT */

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6c (i) — PER-ENCLOSURE ADDRESS MAPS: the on-body proof (design/54 §5 L20/L18, §9 Q11/I3; §7 P3b-6c
 * slice i). Two instances of OUR maps prover are made RESIDENT AT ONCE, each in its OWN page-table
 * hierarchy (vmm_map_new — the kernel half shared, the user half private). Each writes a distinct sentinel
 * to the SAME virtual base 0x400000: with per-enclosure maps the two land on DISTINCT frames (no aliasing).
 * The map is swapped at the coroutine hand-off (vmm_switch); the first enclosure's state survives the
 * second running under its own map and back. A ring-3 fault under a worker's OWN map is recovered PER MAP,
 * the other untouched (L18). The prover is a tests/ FIXTURE, incbin'd — ATTESTED stays 88; no new act
 * (ACT_KINDS stays twelve); founds nothing. Built EDIT-IN-PLACE (no new src/body member).
 *
 * PREEMPTION (archi :4542, MEASURED on the body): this run holds interrupts OFF and the scheduler OFF
 * (g_sched_on == 0) across the whole hand-off — the borrowed-TCP 6b shape — so the timer cannot fire while
 * a worker's map is active and no cross-enclosure resume happens. The coroutine hand-off alone suffices; a
 * thread switch WITHIN one enclosure never swaps the map. MAPS-PREEMPT records g_sched_on and the preempt
 * count (both 0) as the on-body evidence.
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/
#ifdef MAPS_PROVER
#define MAPS_SENTINEL_VA  CANONICAL_BASE            /* 0x400000 — the shared base the two enclosures alias on */
#define MAPS_READBACK_VA  (CANONICAL_BASE + 8u)     /* the ring-3 read-back slot (same page)                  */
#define MAPS_CODE_VA      (CANONICAL_BASE + 0x1000u)/* the prover's own code (its ELF LOAD base, above 0x400000)*/
#define MAPS_SENTINEL_A   0xA11CE5A1u               /* enclosure A's distinct sentinel                        */
#define MAPS_SENTINEL_B   0xB0B0B0B0u               /* enclosure B's distinct sentinel                        */
#define MAPS_FAULT_ADDR   0x100000ull               /* the body's image at 1 MiB — PRESENT + SUPERVISOR: a
                                                     * ring-3 read #PFs (US), the enclosure enforced (L18)    */

/* each resident enclosure HOLDS ITS MAP HANDLE (its CR3), plus the entry + user stack the loader set. */
struct maps_encl { uint64_t cr3; uint64_t entry; uint64_t user_rsp; };

static jmpctx_t g_maps_ctx;   /* the recovery point a maps-prover EXIT or fault unwinds to */

/* read the 32-bit word at `va` in the map rooted at `cr3`, THROUGH the frame's direct-map alias — a
 * map-independent read (works whichever map is active), used to inspect an enclosure's own frame. */
static uint32_t maps_read_word(uint64_t cr3, uint64_t va) {
    uint64_t pte = vmm_query_in(cr3, va & ~0xFFFull);
    if (!(pte & 0x1ull)) { return 0xFFFFFFFFu; }               /* unmapped */
    uint64_t frame = (pte & 0x000FFFFFFFFFF000ull) + (va & 0xFFFull);
    return *(volatile uint32_t *)phys_to_virt(frame);
}

/* load the sealed maps prover into the CURRENT map (the caller vmm_switch'd to it): its code segment at
 * 0x401000, a WRITABLE sentinel page at 0x400000, and a user stack — all USER pages in this map's private
 * half. 0 ok, -1 on a seal/parse/OOM failure. */
static int maps_load(struct maps_encl *e) {
    const uint8_t *img = maps_prover_image_start;
    uint32_t img_len = (uint32_t)(maps_prover_image_end - maps_prover_image_start);
    uint8_t got[32];
    sha256(img, img_len, got);
    if (!digest_matches_hex(got, MAPS_PROVER_IMG_SHA256HEX)) {
        serial_puts("MAPS-LOAD: REFUSED (digest mismatch — sealed image not the sealed bytes)\n");
        return -1;
    }
    const struct elf64_ehdr *eh = (const struct elf64_ehdr *)img;
    if (!(eh->e_ident[0] == 0x7f && eh->e_ident[1] == 'E'
          && eh->e_ident[2] == 'L' && eh->e_ident[3] == 'F')) { return -1; }
    if (eh->e_ident[4] != 2 || eh->e_machine != 62) { return -1; }
    const struct elf64_phdr *ph = (const struct elf64_phdr *)(img + eh->e_phoff);
    for (int i = 0; i < eh->e_phnum; i++) {
        if (ph[i].p_type == PT_LOAD) {
            if (map_segment(ph[i].p_vaddr, ph[i].p_offset, ph[i].p_filesz, ph[i].p_memsz, img) != 0) {
                return -1;
            }
        }
    }
    e->entry = eh->e_entry;
    /* the writable SENTINEL PAGE at the canonical base 0x400000 (a USER page in THIS map's private half). */
    uint32_t sfr = pmm_alloc();
    if (sfr == 0) { return -1; }
    if (vmm_map_user(MAPS_SENTINEL_VA, (uint64_t)sfr) != 0) { return -1; }
    /* the prover's user stack (USER pages, this map's private half). */
    for (uint64_t p = USER_STACK_BASE; p < USER_STACK_TOP; p += 0x1000ull) {
        uint32_t f = pmm_alloc();
        if (f == 0) { return -1; }
        if (vmm_map_user(p, (uint64_t)f) != 0) { return -1; }
    }
    e->user_rsp = USER_STACK_TOP - 16;
    return 0;
}

/* run the enclosure at ring 3 (mode in %rdi, arg in %rsi) under the CURRENTLY-ACTIVE map; return the
 * body_setjmp value: 1 = a clean REQ_EXIT, 2 = a caught ring-3 fault. */
static uint64_t maps_run_encl(struct maps_encl *e, uint64_t mode, uint64_t arg) {
    g_active_ctx = g_maps_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_maps_ctx);
    if (jv == 0) {
        enter_ring3(e->entry, e->user_rsp, mode, arg);
        /* unreachable — REQ_EXIT (longjmp 1) or a #PF/#GP/#UD the body catches (longjmp 2) */
    }
    g_in_worker = 0;
    return jv;
}

/* THE COROUTINE HAND-OFF's swap. Normally loads the incoming enclosure's map; the A2 plant suppresses it,
 * so the second enclosure runs under the first's still-active map and corrupts its state. */
static void maps_handoff(uint64_t cr3) {
#ifndef PLANT_MAPS_NO_SWAP
    vmm_switch(cr3);
#else
    (void)cr3;   /* A2 PLANT: the hand-off does NOT swap the map */
#endif
}

int floor_maps_run(void) {
    interrupts_disable();     /* a deterministic run; the timer stays off, so no preemption (measured) */
    g_serve_phase = 0;
    serial_puts("MAPS: per-enclosure address maps — two residents at base 0x400000, the map swapped at the "
                "coroutine hand-off\n");

    /* ── build two per-enclosure maps and load the prover into each (its own private user half). ── */
    struct maps_encl A, B;
    A.cr3 = vmm_map_new();
    if (A.cr3 == 0) { serial_puts("MAPS: FAIL (OOM building map A)\n"); return 1; }
    vmm_switch(A.cr3);
    if (maps_load(&A) != 0) { serial_puts("MAPS: FAIL (loading enclosure A)\n"); return 1; }
#if defined(PLANT_MAPS_SHARED)
    /* A1 PLANT (one map for both): B REUSES A's map, so both 0x400000 land on the SAME frame — B's write
     * clobbers A's sentinel and each reads the other's (the exact collision mgr measured). */
    B.cr3 = A.cr3; B.entry = A.entry; B.user_rsp = A.user_rsp;
#else
    B.cr3 = vmm_map_new();
    if (B.cr3 == 0) { serial_puts("MAPS: FAIL (OOM building map B)\n"); return 1; }
    vmm_switch(B.cr3);
    if (maps_load(&B) != 0) { serial_puts("MAPS: FAIL (loading enclosure B)\n"); return 1; }
#endif

    /* A1 (structural): the two enclosures' user pages at 0x400000 are DISTINCT physical frames. */
    uint64_t fa = vmm_query_in(A.cr3, MAPS_SENTINEL_VA) & 0x000FFFFFFFFFF000ull;
    uint64_t fb = vmm_query_in(B.cr3, MAPS_SENTINEL_VA) & 0x000FFFFFFFFFF000ull;
    int maps_distinct = (fa != 0) && (fb != 0) && (fa != fb);

    /* ── run A under its own map (position on the first resident), write its sentinel. ── */
    vmm_switch(A.cr3);
    uint64_t ja = maps_run_encl(&A, 0 /*write*/, MAPS_SENTINEL_A);
    uint32_t a_readback = maps_read_word(A.cr3, MAPS_READBACK_VA);

    /* ── THE COROUTINE HAND-OFF to B, B writes its sentinel under its OWN map, then hand off back to A. ── */
    maps_handoff(B.cr3);
    uint64_t jb = maps_run_encl(&B, 0 /*write*/, MAPS_SENTINEL_B);
    uint32_t b_readback = maps_read_word(B.cr3, MAPS_READBACK_VA);
    maps_handoff(A.cr3);
    uint64_t ja2 = maps_run_encl(&A, 2 /*read*/, 0);      /* A resumes: re-reads its 0x400000 after B ran */
    uint32_t a_readback_after = maps_read_word(A.cr3, MAPS_READBACK_VA);

    /* ── A3: a ring-3 fault while B runs under ITS OWN map — recovered per map, A untouched. ── */
    maps_handoff(B.cr3);
    uint64_t jf = maps_run_encl(&B, 1 /*fault*/, MAPS_FAULT_ADDR);
    uint64_t fault_vec = g_worker_fault;
#if !defined(PLANT_MAPS_FAULT_NOSWAPBACK)
    maps_handoff(A.cr3);   /* restore A's map after the per-map fault recovery */
#else
    /* A3 PLANT: do NOT restore A's map — the "A" read below lands B's map (the wrong map) and reads B's
     * sentinel, not A's. */
    (void)0;
#endif
    uint32_t active_read_after_fault = *(volatile uint32_t *)(uintptr_t)MAPS_SENTINEL_VA;   /* via active CR3 */

    /* ── the checks (each machine-read, each with a plant that reds it by a real mechanism). ── */
    int a_wrote_read  = (ja == 1) && (a_readback == MAPS_SENTINEL_A);
    int b_wrote_read  = (jb == 1) && (b_readback == MAPS_SENTINEL_B);
    int no_alias      = maps_distinct
                      && (maps_read_word(A.cr3, MAPS_SENTINEL_VA) == MAPS_SENTINEL_A)
                      && (maps_read_word(B.cr3, MAPS_SENTINEL_VA) == MAPS_SENTINEL_B);      /* A1 */
    int state_intact  = (ja2 == 1)
                      && (a_readback_after == MAPS_SENTINEL_A)
                      && (maps_read_word(A.cr3, MAPS_SENTINEL_VA) == MAPS_SENTINEL_A);      /* A2 */
    int fault_per_map = (jf == 2) && (fault_vec == 14)
                      && (active_read_after_fault == MAPS_SENTINEL_A)                        /* recovered to A's map */
                      && (maps_read_word(A.cr3, MAPS_SENTINEL_VA) == MAPS_SENTINEL_A);      /* A untouched (A3) */
    int kernel_half   = vmm_map_kernel_half_matches(A.cr3)
                      && vmm_map_kernel_half_matches(B.cr3);                                 /* A4 */
    int preempt_off   = (g_sched_on == 0) && (g_sched_preempts == 0);                        /* measured */

    serial_puts("MAPS-FRAME-A: 0x");   serial_puthex64(fa);
    serial_puts(" MAPS-FRAME-B: 0x");  serial_puthex64(fb); serial_puts("\n");
    serial_puts("MAPS-A-READBACK: 0x");serial_puthex32(a_readback);
    serial_puts(" MAPS-B-READBACK: 0x");serial_puthex32(b_readback); serial_puts("\n");
    serial_puts("MAPS-A-AFTER-B: 0x"); serial_puthex32(maps_read_word(A.cr3, MAPS_SENTINEL_VA)); serial_puts("\n");
    serial_puts("MAPS-FAULT: vec=0x"); serial_puthex32((uint32_t)fault_vec);
    serial_puts(" cr2=0x");            serial_puthex64(g_worker_cr2);
    serial_puts(" active-read-after=0x"); serial_puthex32(active_read_after_fault); serial_puts("\n");
    serial_puts("MAPS-PREEMPT: g_sched_on=0x"); serial_puthex32((uint32_t)g_sched_on);
    serial_puts(" preempts=0x");       serial_puthex32(g_sched_preempts); serial_puts("\n");

    serial_puts(no_alias      ? "CHECK MAPS-NO-ALIAS: PASS\n"      : "CHECK MAPS-NO-ALIAS: FAIL\n");
    serial_puts(state_intact  ? "CHECK MAPS-STATE-INTACT: PASS\n"  : "CHECK MAPS-STATE-INTACT: FAIL\n");
    serial_puts(fault_per_map ? "CHECK MAPS-FAULT-PER-MAP: PASS\n" : "CHECK MAPS-FAULT-PER-MAP: FAIL\n");
    serial_puts(kernel_half   ? "CHECK MAPS-KERNEL-HALF: PASS\n"   : "CHECK MAPS-KERNEL-HALF: FAIL\n");
    serial_puts(preempt_off   ? "CHECK MAPS-PREEMPT-OFF: PASS\n"   : "CHECK MAPS-PREEMPT-OFF: FAIL\n");

    /* restore the boot map so kmain's post-floor code runs on the map it booted with. */
    vmm_switch(vmm_boot_cr3());

    int all = a_wrote_read && b_wrote_read && no_alias && state_intact && fault_per_map
           && kernel_half && preempt_off;
    serial_puts(all ? "MAPS: PASS\n" : "MAPS: FAIL\n");
    return all ? 0 : 1;
}
#endif /* MAPS_PROVER */

#ifdef BRIDGE
/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6c slice (ii) — THE COMBINED BUILD + THE COROUTINE BRIDGE (design/54 §5 L18/L19, §9 Q11/I3; §7
 * P3b-6c slice ii; countersign archi :4550). The body boots the sealed interpreter (P3b-4c) AND the enclosed
 * lwIP worker (P3b-6b) RESIDENT TOGETHER, each in its OWN slice-(i) map (vmm_map_new). A ring-0 coroutine
 * bridge relays ONE operation interpreter->worker->back: the interpreter issues SYS_socket (serve.c routes
 * it to bridge_relay), the bridge swaps to the worker's OWN map + kernel stack (slice i's vmm_switch + the
 * per-thread kstack so the nested crossing never clobbers the interpreter's), runs the REAL worker to
 * produce its OWN answer WITNESSED (never a fabricated reply, L19), swaps back, and returns the worker's real
 * answer. A ring-3 fault mid-relay recovers per this enclosure's map (L18) and the bridge hands the WAITING
 * interpreter an error answer (archi :4550) — the interpreter continues, never left suspended. The bridge is
 * OUR OWN body code; the worker is byte-unmodified content (I3). NO new act (ACT_KINDS stays twelve).
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/
#define BRIDGE_SHARED_VA     0x20000000ull       /* the relay page (USER) in the worker's private half     */
#define BRIDGE_OP_NORMAL     0x1ull
#define BRIDGE_OP_FAULT      0x2ull
#define BRIDGE_WITNESS_MAGIC 0x6c77495057334bull /* must match the worker glue: the worker executed         */
#define BRIDGE_ANS_TRANSFORM(a) (((a) & 0xFFFFFFFFFFFFull) | 0x10000ull)   /* must match the worker glue    */
#define BRIDGE_ERROR_ANSWER  0xFFFFFFFFFFFFFFEDull /* (uint64_t)(-19) ENODEV — a refusal-shaped completion  */

struct bridge_slot { volatile uint64_t op, arg, witness, answer, lwip_evidence; };

struct bridge_encl { uint64_t cr3; uint64_t entry; uint64_t rsp; uint64_t kstack_top; };
static struct bridge_encl g_bi;   /* the interpreter enclosure (map A) */
static struct bridge_encl g_bw;   /* the lwIP worker enclosure  (map B) */
static jmpctx_t g_bridge_ctx;     /* the worker sub-run's recovery point (a fault/exit unwinds here) */
static uint8_t  g_bridge_wkstack[SCHED_KSTACK_SIZE] __attribute__((aligned(16)));  /* the worker's kstack */
static uint32_t g_bridge_slot_frame;   /* the relay page's physical frame (map-independent access)      */
static uint64_t g_bridge_worker_brk;   /* the worker's brk base (set at load; the bridge resets it per relay) */

int g_bridge_active;               /* 1 while the interpreter runs under the bridge (serve.c reads it)   */
static int      g_bridge_relays;   /* total relays performed                                            */
static uint64_t g_bridge_arg[2];      /* [0]=a normal relay's arg, [1]=a fault relay's arg              */
static uint64_t g_bridge_witness[2];  /* the worker's witness read back per relay class                 */
static uint64_t g_bridge_answer[2];   /* the worker's answer read back per relay class                  */
static uint64_t g_bridge_returned[2]; /* what the bridge returned to the interpreter per relay class     */
static uint64_t g_bridge_jv[2];       /* the worker sub-run's body_setjmp value (1 clean, 2 fault)       */

/* a map-independent pointer to the relay slot (through the direct map — the worker's frame, any active CR3).*/
static volatile struct bridge_slot *bridge_slot_ptr(void) {
    return (volatile struct bridge_slot *)phys_to_virt((uint64_t)g_bridge_slot_frame);
}

/* THE RING-0 RELAY (called from serve.c on the interpreter's SYS_socket crossing). Cross to the resident
 * worker under its OWN map + kstack, run it to produce the answer WITNESSED, cross back, return the answer
 * (or, on a worker fault mid-relay, an error answer — the interpreter is never left waiting, archi :4550). */
uint64_t bridge_relay(uint64_t num, uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3, uint64_t a4) {
    (void)num; (void)a0; (void)a1; (void)a2; (void)a3; (void)a4;
    /* the op is a build choice: the NORMAL build proves the clean round-trip (A2); the -DBRIDGE_FAULT build
     * proves the worker faulting mid-relay (A3 + the precision). ONE relay per boot, so the worker's single
     * run is always its fresh first run (a deliberate, deterministic fault — never a dirty re-entry). */
#if defined(BRIDGE_FAULT) || defined(PLANT_BRIDGE_LEAVE_WAITING)
    uint64_t op = BRIDGE_OP_FAULT;   /* the leave-waiting plant needs a fault to reach its jv==2 branch */
#else
    uint64_t op = BRIDGE_OP_NORMAL;
#endif
    int idx = 0;

    /* a nonce arg (unpredictable, from the body's own entropy) so a canned answer cannot be pre-baked. */
    uint64_t arg = 0;
    entropy_draw((uint8_t *)&arg, 8);
    if (arg == 0) { arg = 0x1122334455667788ull; }

    /* write op+arg into the worker's slot (map-independent, through the direct map); clear the readbacks. */
    volatile struct bridge_slot *slot = bridge_slot_ptr();
    slot->op = op; slot->arg = arg; slot->witness = 0; slot->answer = 0; slot->lwip_evidence = 0;
    g_bridge_arg[idx] = arg;

#ifdef PLANT_BRIDGE_CANNED
    /* the canned-answer plant: return a FABRICATED answer WITHOUT crossing to the worker. The worker never
     * runs -> its witness stays absent (0) and the answer is not the worker's -> BRIDGE-WITNESSED and
     * BRIDGE-ROUNDTRIP both red. A check that cannot fail is not a check (L19). */
    if (op == BRIDGE_OP_NORMAL) {
        g_bridge_witness[idx]  = slot->witness;      /* still 0 — the worker did not run */
        g_bridge_answer[idx]   = 0xCA11EDull;
        g_bridge_jv[idx]       = 1;
        g_bridge_returned[idx] = 0xCA11EDull;        /* a canned answer, NOT the worker's */
        g_bridge_relays++;
        serial_puts("BRIDGE-RELAY: CANNED (plant — no crossing to the worker)\n");
        return 0xCA11EDull;
    }
#endif

    uint64_t *saved_active = g_active_ctx;      /* the interpreter's recovery ctx (restored after the relay) */
    /* the two enclosures share serve.c's single brk state — save the interpreter's, give the worker a fresh
     * one at its own base for this relay, restore the interpreter's exactly afterward (else the interpreter
     * resumes with a hole in its own map's heap). */
    uint64_t saved_brk_base, saved_brk_cur;
    serve_brk_save(&saved_brk_base, &saved_brk_cur);
    serve_set_brk_base(g_bridge_worker_brk);
    /* the worker's glibc init sets its OWN %fs (arch_prctl -> FS_BASE MSR) and the scheduler is per-thread;
     * save the interpreter's %fs + turn the scheduler off for the deterministic worker run, restore after. */
    uint64_t saved_fs   = rdmsr(SCHED_MSR_FS_BASE);
    int      saved_sched = g_sched_on;
    g_sched_on = 0;

    /* ── THE SWAP (the coroutine hand-off): the worker's own kernel stack (its nested crossings + faults
     * land there, NOT on the interpreter's saved crossing state), then the worker's own map (slice i). The
     * worker runs ONCE per boot (its FIRST, fresh run) — the FAULT case is a separate -DBRIDGE_FAULT build,
     * so no relay re-enters a program that already ran to exit. ── */
    body_set_kernel_stack(g_bw.kstack_top);
#ifndef PLANT_BRIDGE_NO_SWAP
    vmm_switch(g_bw.cr3);
#else
    /* the no-swap plant: the hand-off omits the map swap, so the worker's entry aliases the interpreter's
     * code under the interpreter's map -> the worker never runs, the witness stays absent. A check that
     * cannot fail is not a check (L19). */
#endif

    /* ── run the worker sub-run: it performs the op and produces its OWN answer (witnessed on its side). ─ */
    g_serve_enclosure = ENCL_LWIP;
    g_active_ctx = g_bridge_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_bridge_ctx);
    if (jv == 0) {
        enter_ring3(g_bw.entry, g_bw.rsp, 0, 0);   /* the worker runs (exit_group -> jv 1, fault -> jv 2) */
    }
    uint64_t wfault = g_worker_fault, wcr2 = g_worker_cr2, wrip = g_worker_rip;   /* capture before reset */

    /* ── THE SWAP BACK: restore the interpreter's map + kernel stack + recovery ctx + running state. ──── */
#ifndef PLANT_BRIDGE_NO_SWAP
    vmm_switch(g_bi.cr3);
#endif
    body_set_kernel_stack(g_bi.kstack_top);
    serve_brk_load(saved_brk_base, saved_brk_cur);   /* restore the interpreter's brk exactly */
    wrmsr(SCHED_MSR_FS_BASE, saved_fs);              /* restore the interpreter's %fs */
    g_sched_on = saved_sched;
    g_serve_enclosure = ENCL_INTERP;
    g_active_ctx = saved_active;
    g_in_worker = 1;                 /* the interpreter is still the running worker (a later fault recovers) */
    g_worker_fault = 0;
    g_serve_exited = 0;              /* the worker's exit_group must not leak into the interpreter's exit    */

    /* read back the worker's real answer + witness (map-independent, from the worker's own frame). */
    uint64_t witness = slot->witness;
    uint64_t answer  = slot->answer;
    g_bridge_witness[idx] = witness;
    g_bridge_answer[idx]  = answer;
    g_bridge_jv[idx]      = jv;

    /* the answer the WAITING interpreter receives: the worker's real answer, or — on a fault mid-relay — an
     * error answer (a refusal-shaped completion; the interpreter is NEVER left suspended, archi :4550). */
    uint64_t returned;
    if (jv == 2) {
        returned = BRIDGE_ERROR_ANSWER;
        serial_puts("BRIDGE-RELAY-FAULT: worker faulted mid-op vec=0x"); serial_puthex32((uint32_t)wfault);
        serial_puts(" cr2=0x"); serial_puthex64(wcr2);
        serial_puts(" rip=0x"); serial_puthex64(wrip);
        serial_puts(" -> the interpreter gets an error answer (not left waiting)\n");
#ifdef PLANT_BRIDGE_LEAVE_WAITING
        /* the precision plant: do NOT return to the interpreter — it hangs forever on the operation with no
         * outcome; the serial poll's timeout catches the hang (no PYSOCK-DONE, no BODY-HALT). L19. */
        for (;;) { __asm__ volatile("hlt"); }
#endif
    } else {
        returned = answer;
    }
    g_bridge_returned[idx] = returned;
    g_bridge_relays++;
    serial_puts("BRIDGE-RELAY idx=0x"); serial_puthex32((uint32_t)idx);
    serial_puts(" op=0x"); serial_puthex32((uint32_t)op);
    serial_puts(" jv=0x"); serial_puthex32((uint32_t)jv);
    serial_puts(" witness=0x"); serial_puthex64(witness);
    serial_puts(" returned=0x"); serial_puthex64(returned); serial_puts("\n");
    return returned;
}

int floor_bridge_run(void) {
    interrupts_disable();     /* deterministic: no timer, no preemption (slice i's measured shape) */
    serial_puts("BRIDGE: combined boot — the sealed interpreter (P3b-4c) AND the enclosed lwIP worker "
                "(P3b-6b) RESIDENT TOGETHER, each in its own slice-(i) map; a ring-0 coroutine bridge relays "
                "ONE operation interpreter->worker->back across the map swap; the worker's answer is its OWN "
                "execution, witnessed (L18/L19/I3)\n");
    floor_enable_sse();

    if (g_sealed_module_phys == 0 || g_sealed_module_len == 0) {
        serial_puts("BRIDGE: FAIL (no sealed-image module — boot with -initrd sealed.img)\n");
        return 1;
    }
    const uint8_t *img = (const uint8_t *)phys_to_virt(g_sealed_module_phys);
    uint32_t img_len = (uint32_t)g_sealed_module_len;
    uint8_t got[32];
    sha256(img, img_len, got);
    if (!digest_matches_hex(got, SEALED_IMG_SHA256HEX)) {
        serial_puts("BRIDGE-SEAL: REFUSED (interpreter image digest mismatch)\n");
        serial_puts("BRIDGE: FAIL (the sealed image was refused at load)\n");
        return 1;
    }
    serial_puts("BRIDGE-SEAL: OK (the interpreter image digest matches the seal)\n");

    /* ── (1) LOAD THE WORKER into map B (RESIDENT, not yet run). ─────────────────────────────────── */
    g_bw.cr3 = vmm_map_new();
    if (g_bw.cr3 == 0) { serial_puts("BRIDGE: FAIL (OOM building the worker map)\n"); return 1; }
    vmm_switch(g_bw.cr3);
    if (floor_load_prover() != 0) {            /* the sealed lwIP worker (prover_image), digest-checked (A1) */
        serial_puts("BRIDGE: FAIL (the sealed lwIP worker was refused at load)\n"); return 1;
    }
    g_bridge_worker_brk = (g_floor_max_vaddr + 0xFFFull) & ~0xFFFull;
    serve_set_brk_base(g_bridge_worker_brk);
    floor_build_stack();                       /* the worker's SysV stack, in map B */
    g_bw.entry = g_floor_entry;
    g_bw.rsp   = g_floor_rsp;
    g_bw.kstack_top = (uint64_t)(uintptr_t)(g_bridge_wkstack + sizeof(g_bridge_wkstack));
    /* the shared relay page in map B (USER). */
    g_bridge_slot_frame = pmm_alloc();
    if (g_bridge_slot_frame == 0) { serial_puts("BRIDGE: FAIL (OOM for the relay page)\n"); return 1; }
    if (vmm_map_user(BRIDGE_SHARED_VA, (uint64_t)g_bridge_slot_frame) != 0) {
        serial_puts("BRIDGE: FAIL (mapping the relay page)\n"); return 1;
    }
    { volatile struct bridge_slot *s = bridge_slot_ptr();
      s->op = 0; s->arg = 0; s->witness = 0; s->answer = 0; s->lwip_evidence = 0; }

    /* ── (2) LOAD THE INTERPRETER into map A (RESIDENT). ────────────────────────────────────────── */
    g_bi.cr3 = vmm_map_new();
    if (g_bi.cr3 == 0) { serial_puts("BRIDGE: FAIL (OOM building the interpreter map)\n"); return 1; }
    vmm_switch(g_bi.cr3);
    int nent = serve_fs_set_image(img, img_len);
    if (nent < 0) { serial_puts("BRIDGE: FAIL (the sealed image is not a GOVSIMG1 archive)\n"); return 1; }
    if (floor3_load_program_from_image(INTERP_PROGRAM_PATH) != 0) {
        serial_puts("BRIDGE: FAIL (the interpreter is not in the sealed image, or not a dynamic ET_EXEC)\n");
        return 1;
    }
    if (floor3_load_interp(g_interp_path) != 0) {
        serial_puts("BRIDGE: FAIL (the dynamic linker is not in the sealed image)\n"); return 1;
    }
    serve_set_brk_base((g_floor_max_vaddr + 0xFFFull) & ~0xFFFull);
    floor3_build_python_stack();               /* argv = python -I -S -c g_bridge_script (issues SYS_socket) */
    wrmsr(0xC0000100u, 0);                      /* reset %fs; ld.so installs the base via arch_prctl */
    g_bi.entry = g_dyn_entry;                   /* hand over to ld.so (relocates the interpreter + libs) */
    g_bi.rsp   = g_floor_rsp;
    g_bi.kstack_top = (uint64_t)(uintptr_t)(g_syscall_stack + sizeof(g_syscall_stack));

    /* ── A1 (structural): both resident, each at base 0x400000 on DISTINCT frames (no aliasing, slice i). ─ */
    uint64_t fa = vmm_query_in(g_bi.cr3, CANONICAL_BASE) & 0x000FFFFFFFFFF000ull;
    uint64_t fb = vmm_query_in(g_bw.cr3, CANONICAL_BASE) & 0x000FFFFFFFFFF000ull;
    int both_resident = (fa != 0) && (fb != 0) && (fa != fb);
    serial_puts("BRIDGE-INTERP-FRAME: 0x"); serial_puthex64(fa);
    serial_puts(" BRIDGE-WORKER-FRAME: 0x"); serial_puthex64(fb); serial_puts("\n");
    serial_puts(both_resident ? "CHECK BRIDGE-BOTH-RESIDENT: PASS\n" : "CHECK BRIDGE-BOTH-RESIDENT: FAIL\n");

    /* ── (3) RUN THE INTERPRETER under map A; each SYS_socket relays through bridge_relay. The interpreter
     * runs EXACTLY as floor3_interp_run does (the real python3 needs the timer + scheduler brought up before
     * its ld.so start-up): pit_init + sched_init, enter via enter_ring3_main with interrupts enabled. The
     * bridge_relay makes the worker sub-run deterministic (g_sched_on saved+cleared across it). ────────── */
    g_bridge_relays = 0;
    g_bridge_witness[0] = g_bridge_witness[1] = 0;
    g_bridge_jv[0] = g_bridge_jv[1] = 0;
    vmm_switch(g_bi.cr3);
    pit_init(SCHED_PIT_HZ);
    sched_init();                              /* the main thread becomes the first scheduler context */
    g_bi.kstack_top = syscall_kernel_rsp;      /* sched_init set the crossing stack to the main kstack */
    serial_puts("BRIDGE-HANDOVER: entry=0x"); serial_puthex64(g_bi.entry);
    serial_puts(" rsp=0x"); serial_puthex64(g_bi.rsp);
    serial_puts(" ld_base=0x"); serial_puthex64(g_dyn_ld_base); serial_puts("\n");
    g_bridge_active = 1;
    g_serve_phase = 1;
    g_serve_enclosure = ENCL_INTERP;
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        interrupts_enable();
        enter_ring3_main(g_bi.entry, g_bi.rsp);   /* the interpreter runs its script (exits jv 1, faults jv 2) */
    }
    interrupts_disable();
    g_in_worker = 0;
    g_serve_phase = 0;
    g_sched_on = 0;
    g_bridge_active = 0;

    if (jv == 2) {
        serial_puts("BRIDGE-INTERP-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
        serial_puts(" cr2=0x"); serial_puthex64(g_worker_cr2);
        serial_puts(" rip=0x"); serial_puthex64(g_worker_rip); serial_puts("\n");
        serial_puts("BRIDGE: FAIL (the interpreter FAULTED — not a clean round-trip)\n");
        vmm_switch(vmm_boot_cr3());
        return 1;
    }

    /* ── the checks (each machine-read; ONE relay per boot, idx 0). ──────────────────────────────── */
    int relay_ran     = (g_bridge_relays >= 1);
    int witnessed     = (g_bridge_witness[0] == BRIDGE_WITNESS_MAGIC);                      /* A2 */
    int roundtrip     = (g_bridge_answer[0]   == BRIDGE_ANS_TRANSFORM(g_bridge_arg[0]))
                     && (g_bridge_returned[0]  == BRIDGE_ANS_TRANSFORM(g_bridge_arg[0]));   /* A2 integrity */
    int fault_relay   = (g_bridge_jv[0] == 2)                                               /* A3 + precision */
                     && (g_bridge_returned[0] == BRIDGE_ERROR_ANSWER)
                     && (g_bridge_witness[0]  != BRIDGE_WITNESS_MAGIC);
    int interp_done   = (jv == 1);                                                          /* not left waiting */
    int kernel_half   = vmm_map_kernel_half_matches(g_bi.cr3)
                     && vmm_map_kernel_half_matches(g_bw.cr3);                              /* A4 / L20 */
    int states_intact = ((vmm_query_in(g_bi.cr3, CANONICAL_BASE) & 0x000FFFFFFFFFF000ull) == fa)
                     && ((vmm_query_in(g_bw.cr3, CANONICAL_BASE) & 0x000FFFFFFFFFF000ull) == fb);

    serial_puts("BRIDGE-RELAYS: 0x"); serial_puthex32((uint32_t)g_bridge_relays); serial_puts("\n");
    serial_puts("BRIDGE-R0 jv=0x"); serial_puthex32((uint32_t)g_bridge_jv[0]);
    serial_puts(" arg=0x"); serial_puthex64(g_bridge_arg[0]);
    serial_puts(" ans=0x"); serial_puthex64(g_bridge_answer[0]);
    serial_puts(" witness=0x"); serial_puthex64(g_bridge_witness[0]);
    serial_puts(" returned=0x"); serial_puthex64(g_bridge_returned[0]); serial_puts("\n");

#ifdef BRIDGE_FAULT
    serial_puts(fault_relay   ? "CHECK BRIDGE-FAULT-PER-MAP: PASS\n"    : "CHECK BRIDGE-FAULT-PER-MAP: FAIL\n");
#else
    serial_puts(witnessed     ? "CHECK BRIDGE-WITNESSED: PASS\n"        : "CHECK BRIDGE-WITNESSED: FAIL\n");
    serial_puts(roundtrip     ? "CHECK BRIDGE-ROUNDTRIP: PASS\n"        : "CHECK BRIDGE-ROUNDTRIP: FAIL\n");
#endif
    serial_puts(interp_done   ? "CHECK BRIDGE-INTERP-CONTINUED: PASS\n" : "CHECK BRIDGE-INTERP-CONTINUED: FAIL\n");
    serial_puts(kernel_half   ? "CHECK BRIDGE-KERNEL-HALF: PASS\n"      : "CHECK BRIDGE-KERNEL-HALF: FAIL\n");
    serial_puts(states_intact ? "CHECK BRIDGE-STATES-INTACT: PASS\n"    : "CHECK BRIDGE-STATES-INTACT: FAIL\n");

    vmm_switch(vmm_boot_cr3());   /* restore the boot map so kmain's post-floor code runs on it */

#ifdef BRIDGE_FAULT
    int all = both_resident && relay_ran && fault_relay && interp_done && kernel_half && states_intact;
#else
    int all = both_resident && relay_ran && witnessed && roundtrip && interp_done && kernel_half && states_intact;
#endif
    serial_puts(all ? "BRIDGE: PASS\n" : "BRIDGE: FAIL\n");
    return all ? 0 : 1;
}
#endif /* BRIDGE */

#ifdef SOCKET_ACT
/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6c slice (iii) — THE SOCKET ACT (design/54 §5 L18/L19/I3; §7 P3b-6c slice iii; countersign archi
 * :4561). The LAST body slice. The body boots the sealed interpreter (P3b-4c) AND the enclosed lwIP worker
 * (a NEW op-server glue over the SAME byte-unmodified lwIP core, I3) RESIDENT TOGETHER, each in its own
 * slice-(i) map, plus 6a's live NIC. gov-os's own act (open_real_socket_under_grant on the record) decides
 * SOCKET-OPEN FIRST, then the interpreter's socket-family syscalls (socket / ioctl(FIONBIO) / connect /
 * getsockopt / poll / sendto / recvfrom / close) cross to serve.c, which RELAYS each across the slice-(ii)
 * bridge to the resident worker. The worker performs each op on its PERSISTENT lwIP connection, pumping the
 * NIC, and YIELDS (REQ_YIELD) back — a PERSISTENT COROUTINE, unlike slice (ii)'s one-shot relay. One real
 * guest-local connection opens, sends, receives and closes on our core. The worker is byte-unmodified lwIP
 * (I3); the bridge is OUR code; NO new act (ACT_KINDS stays twelve); the server socket + the production step
 * stay OUT (Q5).
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/
#define SA_SHARED_VA     0x20000000ull       /* the relay page (USER) in the worker's private half         */
#define SA_WITNESS_MAGIC 0x6c77495057334bull /* must match the worker glue: the worker executed the op     */
/* the SA_OP_* socket-op codes live in enclosure.h (shared with serve.c); the worker glue mirrors them. */

#define SA_BUF_MAX 2048u
struct sa_slot {
    volatile uint64_t op, a0, a1, a2;
    volatile uint64_t answer, witness, buflen;
    volatile uint8_t  buf[SA_BUF_MAX];
};

struct sa_encl { uint64_t cr3; uint64_t entry; uint64_t rsp; uint64_t kstack_top; };
static struct sa_encl g_sa_i;   /* the interpreter enclosure (map A) */
static struct sa_encl g_sa_w;   /* the lwIP worker enclosure  (map B) */
static jmpctx_t g_sa_relay_ctx;     /* the bridge's recovery point (the worker's yield/fault/exit unwinds here) */
static jmpctx_t g_sa_worker_ctx;    /* the worker's yield continuation (the bridge resumes it here)            */
static uint8_t  g_sa_wkstack[SCHED_KSTACK_SIZE] __attribute__((aligned(16)));
static uint32_t g_sa_slot_frame;    /* the relay page's physical frame (map-independent access)               */
static uint64_t g_sa_worker_brk_base;/* the worker's brk base (set at load; persists across relays)           */
static uint64_t g_sa_worker_brk_cur; /* the worker's brk cursor (its malloc heap persists across relays)       */
static int      g_sa_worker_started;/* 0 until the first relay enters the worker fresh                        */
static uint64_t g_sa_worker_fs;     /* the worker's own %fs (TLS base) — preserved across yields (0 first run) */
static int      g_sa_worker_yielded;/* the worker returned by YIELD (vs. fault/exit)                          */
static int      g_sa_worker_done;   /* the worker exit_group'd (never expected mid-connection)                */

int g_sa_active;                    /* 1 while the interpreter runs under the socket-act bridge (serve.c reads it) */
int g_sa_sock_fd = -1;             /* the fd SOP_SOCKET returned — only THIS fd's ops relay (serve.c reads it)    */
static int g_sa_relays;             /* total socket-op relays performed                                       */
static uint32_t g_sa_free0;         /* A4: the frame-pool free count before the run                           */
static uint32_t g_sa_pool[64];      /* A4: the frame-pool free count sampled after each SEND relay (repeated)  */
static uint32_t g_sa_pool_n;        /* A4: how many SEND-relay pool samples were taken                         */
static int      g_sa_witness_ok = 1;/* A2: every relayed shape carried the worker's witness (it EXECUTED it)   */
static uint32_t g_sa_recv_bytes;    /* A2: real bytes delivered up by the worker's recv (the data exchange)    */

static volatile struct sa_slot *sa_slot_ptr(void) {
    return (volatile struct sa_slot *)phys_to_virt((uint64_t)g_sa_slot_frame);
}

/* THE WORKER'S YIELD (called from serve.c on the worker's REQ_YIELD crossing). Save the worker's
 * continuation and hand control back to the bridge; the bridge resumes it (from bridge_relay_sock) on the
 * next relayed op. */
void sa_worker_yield(void) {
    uint64_t jv = body_setjmp(g_sa_worker_ctx);
    if (jv == 0) {
        g_sa_worker_yielded = 1;
        body_longjmp(g_sa_relay_ctx, 1);   /* back to the bridge (never returns here on this pass) */
    }
    /* jv != 0: the bridge resumed us; return to the worker (the REQ_YIELD syscall returns 0). */
}

/* THE RING-0 SOCKET RELAY (called from serve.c on each of the interpreter's socket-family crossings). Cross
 * to the resident worker under its OWN map + kstack, RESUME it (or start it fresh the first time), let it
 * perform the op on its persistent connection and yield, cross back, return the worker's REAL answer.
 * in_ptr/in_len: a user buffer in map A copied INTO the slot before the relay (sockaddr / send data).
 * out_ptr/out_max: a user buffer in map A the slot's output is copied BACK into after (recv data). */
uint64_t bridge_relay_sock(uint64_t op, uint64_t a0, uint64_t a1, uint64_t a2,
                           const void *in_ptr, uint32_t in_len,
                           void *out_ptr, uint32_t out_max) {
    volatile struct sa_slot *slot = sa_slot_ptr();
    slot->op = op; slot->a0 = a0; slot->a1 = a1; slot->a2 = a2;
    slot->answer = 0; slot->witness = 0;
    /* marshal the input buffer (map A active now) into the map-independent slot. */
    if (in_ptr && in_len) {
        if (in_len > SA_BUF_MAX) { in_len = SA_BUF_MAX; }
        for (uint32_t i = 0; i < in_len; i++) { slot->buf[i] = ((const uint8_t *)in_ptr)[i]; }
        slot->buflen = in_len;
    } else {
        slot->buflen = 0;
    }

    /* A2 PLANT MATRIX — break ONE shape at a time: fabricate its answer WITHOUT crossing to the worker, so
     * the shape is UNWITNESSED (slot->witness stays absent -> SA-WITNESSED reds) and the op never really
     * happened, so a load-bearing shape ALSO reds the connection. Each is a REAL mechanism (the worker did
     * not execute the shape), never a stubbed worker; the matrix DISCRIMINATES (L19), one shape per boot. */
    int sa_break = 0;
#if defined(PLANT_SA_BREAK_SOCKET)
    if (op == SA_OP_SOCKET)   { sa_break = 1; }
#endif
#if defined(PLANT_SA_BREAK_IOCTL)
    if (op == SA_OP_IOCTL_NB) { sa_break = 1; }
#endif
#if defined(PLANT_SA_BREAK_CONNECT)
    if (op == SA_OP_CONNECT)  { sa_break = 1; }
#endif
#if defined(PLANT_SA_BREAK_GETSOERR)
    if (op == SA_OP_GETSOERR) { sa_break = 1; }
#endif
#if defined(PLANT_SA_BREAK_POLL)
    if (op == SA_OP_POLL)     { sa_break = 1; }
#endif
#if defined(PLANT_SA_BREAK_SEND)
    if (op == SA_OP_SEND)     { sa_break = 1; }
#endif
#if defined(PLANT_SA_BREAK_RECV)
    if (op == SA_OP_RECV)     { sa_break = 1; }
#endif
#if defined(PLANT_SA_BREAK_CLOSE)
    if (op == SA_OP_CLOSE)    { sa_break = 1; }
#endif
    if (sa_break) {
        serial_puts("SA-BREAK: shape fabricated, NO worker crossing op=0x"); serial_puthex32((uint32_t)op);
        serial_puts(" (witness absent -> SA-WITNESSED reds)\n");
        g_sa_witness_ok = 0;                 /* the shape is unwitnessed — the worker never executed it */
        g_sa_relays++;
        return (op == SA_OP_SOCKET) ? 500ull : 0ull;   /* a plausible fabricated answer (the plant) */
    }

    uint64_t *saved_active = g_active_ctx;
    uint64_t saved_brk_base, saved_brk_cur;
    serve_brk_save(&saved_brk_base, &saved_brk_cur);   /* the interpreter's brk (restored after) */
    uint64_t saved_fs    = rdmsr(SCHED_MSR_FS_BASE);
    int      saved_sched = g_sched_on;
    g_sched_on = 0;

    /* the worker's own kernel stack + own map; the deterministic worker sub-run. */
    body_set_kernel_stack(g_sa_w.kstack_top);
    vmm_switch(g_sa_w.cr3);
    g_serve_enclosure = ENCL_LWIP;
    g_active_ctx = g_sa_relay_ctx;   /* a worker fault/exit ALSO unwinds here */
    g_worker_fault = 0;
    g_sa_worker_yielded = 0;
    g_sa_worker_done = 0;
    g_in_worker = 1;

    /* restore the worker's PERSISTENT brk (base+cur) — its malloc heap lives across relays in map B. */
    serve_brk_load(g_sa_worker_brk_base, g_sa_worker_brk_cur);
    /* restore the worker's OWN %fs (TLS base): 0 on the fresh first run (glibc's arch_prctl sets it), the
     * captured worker TLS base on every resume — else the worker runs glibc with the interpreter's TLS and
     * a %fs-relative access (errno / the stack canary / malloc's tcache) faults in the worker's map. */
    wrmsr(SCHED_MSR_FS_BASE, g_sa_worker_fs);

    uint64_t jv = body_setjmp(g_sa_relay_ctx);
    if (jv == 0) {
        if (!g_sa_worker_started) {
            g_sa_worker_started = 1;
            enter_ring3(g_sa_w.entry, g_sa_w.rsp, 0, 0);   /* the worker's fresh first run (inits + op 1) */
        } else {
            body_longjmp(g_sa_worker_ctx, 1);              /* resume the worker where it yielded */
        }
        /* unreachable */
    }
    uint64_t wfault = g_worker_fault, wcr2 = g_worker_cr2, wrip = g_worker_rip;

    /* capture the worker's advanced brk + its TLS base (both persist into the next relay). */
    g_sa_worker_fs = rdmsr(SCHED_MSR_FS_BASE);
    serve_brk_save(&g_sa_worker_brk_base, &g_sa_worker_brk_cur);

    vmm_switch(g_sa_i.cr3);
    body_set_kernel_stack(g_sa_i.kstack_top);
    serve_brk_load(saved_brk_base, saved_brk_cur);
    wrmsr(SCHED_MSR_FS_BASE, saved_fs);
    g_sched_on = saved_sched;
    g_serve_enclosure = ENCL_INTERP;
    g_active_ctx = saved_active;
    g_in_worker = 1;
    g_worker_fault = 0;
    g_serve_exited = 0;

    uint64_t answer = slot->answer;
    g_sa_relays++;
    /* A2 — the worker's WITNESS: a relayed shape that did not carry the worker's execution magic was not
     * really performed (a fabricated/absent reply). Every shape must be witnessed (L19). */
    if (jv != 2 && slot->witness != SA_WITNESS_MAGIC) { g_sa_witness_ok = 0; }
    if (op == SA_OP_RECV && (int64_t)answer > 0) { g_sa_recv_bytes += (uint32_t)answer; }  /* real data up */
    /* A4: sample the frame-pool free count after each SEND relay (the repeated body of the loop). With the
     * active-map unmap the water is STEADY (per-relay net delta ~0); the boot-bound-unmap plant drains it. */
    if (op == SA_OP_SEND && g_sa_pool_n < 64) { g_sa_pool[g_sa_pool_n++] = pmm_free_count(); }

    if (jv == 2) {
        serial_puts("SA-RELAY-FAULT: worker faulted mid-op vec=0x"); serial_puthex32((uint32_t)wfault);
        serial_puts(" cr2=0x"); serial_puthex64(wcr2);
        serial_puts(" rip=0x"); serial_puthex64(wrip); serial_puts("\n");
        return (uint64_t)(-19ll) /* -ENODEV: a refusal-shaped completion, never a hang */;
    }
    if (g_sa_worker_done) {
        serial_puts("SA-RELAY: worker EXITED unexpectedly mid-connection\n");
        return (uint64_t)(-19ll);
    }

    /* marshal the output buffer (map A active again) back into the caller's user buffer. */
    if (out_ptr && out_max) {
        uint32_t n = (uint32_t)slot->buflen;
        if (n > out_max) { n = out_max; }
        for (uint32_t i = 0; i < n; i++) { ((uint8_t *)out_ptr)[i] = slot->buf[i]; }
    }
    return answer;
}

int floor_socket_act_run(void) {
    interrupts_disable();
    serial_puts("SOCKET-ACT: the socket act on the body — the sealed interpreter (P3b-4c) drives gov-os's "
                "own client-connection act; the body relays the socket-family shapes across the slice-(ii) "
                "bridge to the enclosed lwIP worker (byte-unmodified core), which opens ONE guest-local "
                "connection through 6a's NIC over nested SLIRP (L18/L19/I3)\n");
    floor_enable_sse();

    if (g_sealed_module_phys == 0 || g_sealed_module_len == 0) {
        serial_puts("SOCKET-ACT: FAIL (no sealed-image module — boot with -initrd sealed.img)\n");
        return 1;
    }
    const uint8_t *img = (const uint8_t *)phys_to_virt(g_sealed_module_phys);
    uint32_t img_len = (uint32_t)g_sealed_module_len;
    uint8_t got[32];
    sha256(img, img_len, got);
    if (!digest_matches_hex(got, SEALED_IMG_SHA256HEX)) {
        serial_puts("SOCKET-ACT-SEAL: REFUSED (interpreter image digest mismatch)\n");
        return 1;
    }
    serial_puts("SOCKET-ACT-SEAL: OK\n");

    /* ── (1) LOAD THE WORKER (op-server) into map B; bring up the NIC; calibrate its clock. ── */
    g_sa_w.cr3 = vmm_map_new();
    if (g_sa_w.cr3 == 0) { serial_puts("SOCKET-ACT: FAIL (OOM worker map)\n"); return 1; }
    vmm_switch(g_sa_w.cr3);
    if (floor_load_prover() != 0) { serial_puts("SOCKET-ACT: FAIL (worker seal refused at load)\n"); return 1; }
    g_sa_worker_brk_base = (g_floor_max_vaddr + 0xFFFull) & ~0xFFFull;
    g_sa_worker_brk_cur  = g_sa_worker_brk_base;
    serve_set_brk_base(g_sa_worker_brk_base);
    floor_build_stack();
    g_sa_w.entry = g_floor_entry;
    g_sa_w.rsp   = g_floor_rsp;
    g_sa_w.kstack_top = (uint64_t)(uintptr_t)(g_sa_wkstack + sizeof(g_sa_wkstack));
    /* the shared relay page in map B (USER). */
    g_sa_slot_frame = pmm_alloc();
    if (g_sa_slot_frame == 0) { serial_puts("SOCKET-ACT: FAIL (OOM relay page)\n"); return 1; }
    if (vmm_map_user(SA_SHARED_VA, (uint64_t)g_sa_slot_frame) != 0) {
        serial_puts("SOCKET-ACT: FAIL (mapping the relay page)\n"); return 1;
    }
    { volatile struct sa_slot *s = sa_slot_ptr(); s->op = 0; s->witness = 0; s->buflen = 0; }

    uint8_t mac[6];
    int nst = net_nic_bringup(mac);
    serial_puts(nst == 0 ? "SOCKET-ACT-NIC: UP\n" : "SOCKET-ACT-NIC: FAIL\n");
    if (nst != 0) { serial_puts("SOCKET-ACT: FAIL (no live NIC — attach virtio-net)\n"); return 1; }

    /* ── (2) LOAD THE INTERPRETER into map A. ── */
    g_sa_i.cr3 = vmm_map_new();
    if (g_sa_i.cr3 == 0) { serial_puts("SOCKET-ACT: FAIL (OOM interp map)\n"); return 1; }
    vmm_switch(g_sa_i.cr3);
    int nent = serve_fs_set_image(img, img_len);
    if (nent < 0) { serial_puts("SOCKET-ACT: FAIL (sealed image not a GOVSIMG1 archive)\n"); return 1; }
    if (floor3_load_program_from_image(INTERP_PROGRAM_PATH) != 0) {
        serial_puts("SOCKET-ACT: FAIL (interpreter not in the sealed image)\n"); return 1;
    }
    if (floor3_load_interp(g_interp_path) != 0) {
        serial_puts("SOCKET-ACT: FAIL (dynamic linker not in the sealed image)\n"); return 1;
    }
    serve_set_brk_base((g_floor_max_vaddr + 0xFFFull) & ~0xFFFull);
    floor3_build_python_stack();
    wrmsr(0xC0000100u, 0);
    g_sa_i.entry = g_dyn_entry;
    g_sa_i.rsp   = g_floor_rsp;
    g_sa_i.kstack_top = (uint64_t)(uintptr_t)(g_syscall_stack + sizeof(g_syscall_stack));

    /* ── (3) calibrate the worker's rdtsc clock (sys_now) against the PIT. ── */
    vmm_switch(g_sa_i.cr3);
    pit_init(SCHED_PIT_HZ);
    interrupts_enable();
    {
        uint64_t c0 = rdtsc();
        uint32_t t0 = ticks_get(), t1;
        while ((t1 = ticks_get()) - t0 < 100u) { __asm__ volatile("pause"); }
        uint64_t c1 = rdtsc();
        uint64_t per_ms = (c1 - c0) / (uint64_t)(t1 - t0);
        if (per_ms == 0) { per_ms = 1; }
        serve_net_clock_calibrate(c1, per_ms);
        serial_puts("SOCKET-ACT-TSC-PER-MS: 0x"); serial_puthex64(per_ms); serial_puts("\n");
    }
    interrupts_disable();

    /* ── (4) RUN THE INTERPRETER under map A; each socket-family syscall relays through bridge_relay_sock. ── */
    g_sa_worker_started = 0;
    g_sa_sock_fd = -1;
    g_sa_relays = 0;
    g_sa_pool_n = 0;
    g_sa_witness_ok = 1;
    g_sa_recv_bytes = 0;
    g_sa_free0 = pmm_free_count();   /* A4: the pool free count before the run (drain baseline) */
    serve_sa_trail_reset();          /* A3: clear the socket-act trail before the relays */
    sched_init();
    g_sa_i.kstack_top = syscall_kernel_rsp;
    serial_puts("SOCKET-ACT-HANDOVER: entry=0x"); serial_puthex64(g_sa_i.entry);
    serial_puts(" rsp=0x"); serial_puthex64(g_sa_i.rsp); serial_puts("\n");
    g_sa_active = 1;
    g_serve_phase = 1;
    g_serve_enclosure = ENCL_INTERP;
    g_active_ctx = g_ctx;
    g_worker_fault = 0;
    g_in_worker = 1;
    uint64_t jv = body_setjmp(g_ctx);
    if (jv == 0) {
        interrupts_enable();
        enter_ring3_main(g_sa_i.entry, g_sa_i.rsp);
    }
    interrupts_disable();
    g_in_worker = 0;
    g_serve_phase = 0;
    g_sched_on = 0;
    g_sa_active = 0;

    if (jv == 2) {
        serial_puts("SOCKET-ACT-INTERP-FAULT: vec=0x"); serial_puthex32((uint32_t)g_worker_fault);
        serial_puts(" cr2=0x"); serial_puthex64(g_worker_cr2);
        serial_puts(" rip=0x"); serial_puthex64(g_worker_rip); serial_puts("\n");
        serial_puts("SOCKET-ACT: FAIL (the interpreter FAULTED)\n");
        vmm_switch(vmm_boot_cr3());
        return 1;
    }

    int interp_done = (jv == 1);
    int relayed     = (g_sa_relays >= 1);
    /* A2 — a REAL exchange: frames crossed BOTH ways AND real bytes were delivered up by the worker's recv
     * (not just a handshake); a broken data-path shape leaves g_sa_recv_bytes at 0 and reds. */
    int conn        = (g_frames_sent > 0) && (g_frames_recv > 0) && (g_sa_recv_bytes > 0);
    int witnessed   = g_sa_witness_ok;   /* A2: every relayed shape carried the worker's execution witness */

    /* A3 — the trail readback: every relayed shape is ONE CAT_SOCK row, every frame ONE CAT_FRAME row. */
    uint32_t sock_rows = 0, frame_rows = 0;
    serve_sa_trail_dump(&sock_rows, &frame_rows);
    int trail_ok = (sock_rows == (uint32_t)g_sa_relays)
                && (frame_rows == g_frames_sent + g_frames_recv)
                && (g_frame_rows == g_frames_sent + g_frames_recv);

    /* A4 — repeated relays did not drain the pool: the per-SEND-relay pool water is STEADY (first vs last
     * sample delta ~0, <= the sample count == <1 frame/relay), and the pool was never exhausted. */
    uint32_t pool_first = g_sa_pool_n ? g_sa_pool[0] : g_sa_free0;
    uint32_t pool_last  = g_sa_pool_n ? g_sa_pool[g_sa_pool_n - 1] : g_sa_free0;
    uint32_t pool_drain = (pool_first > pool_last) ? (pool_first - pool_last) : 0;
    int repeated = (g_sa_pool_n >= 8);                       /* the eight shapes run REPEATEDLY (>=8 sends)  */
    int pool_ok  = (serve_frame_low_water() > 0) && (pool_drain <= g_sa_pool_n);   /* <=1 net frame per relay      */

    serial_puts("SOCKET-ACT-RELAYS: 0x"); serial_puthex32((uint32_t)g_sa_relays); serial_puts("\n");
    serial_puts("SOCKET-ACT-FRAMES-SENT: 0x"); serial_puthex32(g_frames_sent);
    serial_puts(" RECV: 0x"); serial_puthex32(g_frames_recv);
    serial_puts(" ROWS: 0x"); serial_puthex32(g_frame_rows); serial_puts("\n");
    serial_puts("SOCKET-ACT-POOL free0=0x"); serial_puthex32(g_sa_free0);
    serial_puts(" sends=0x"); serial_puthex32(g_sa_pool_n);
    serial_puts(" first=0x"); serial_puthex32(pool_first);
    serial_puts(" last=0x"); serial_puthex32(pool_last);
    serial_puts(" drain=0x"); serial_puthex32(pool_drain);
    serial_puts(" low=0x"); serial_puthex32(serve_frame_low_water()); serial_puts("\n");
    serial_puts("SOCKET-ACT-WITNESS ok=0x"); serial_puthex32((uint32_t)g_sa_witness_ok);
    serial_puts(" recv-bytes=0x"); serial_puthex32(g_sa_recv_bytes); serial_puts("\n");

    serial_puts(interp_done ? "CHECK SA-INTERP-DONE: PASS\n" : "CHECK SA-INTERP-DONE: FAIL\n");
    serial_puts(relayed     ? "CHECK SA-RELAYED: PASS\n"     : "CHECK SA-RELAYED: FAIL\n");
    serial_puts(witnessed   ? "CHECK SA-WITNESSED: PASS\n"   : "CHECK SA-WITNESSED: FAIL\n");
    serial_puts(conn        ? "CHECK SA-CONNECTION: PASS\n"  : "CHECK SA-CONNECTION: FAIL\n");
    serial_puts(trail_ok    ? "CHECK SA-TRAIL: PASS\n"       : "CHECK SA-TRAIL: FAIL\n");
    serial_puts(repeated    ? "CHECK SA-REPEATED: PASS\n"    : "CHECK SA-REPEATED: FAIL\n");
    serial_puts(pool_ok     ? "CHECK SA-POOL-STEADY: PASS\n" : "CHECK SA-POOL-STEADY: FAIL\n");

    vmm_switch(vmm_boot_cr3());
#if defined(GRANT_FIRST) && defined(GRANT_REFUSED)
    /* C7 P3b-6c (iii) A1/A3 — THE REFUSED-DECISION VARIANT: gov-os's gate RAISED before any socket() (the
     * unestablished opener, EACCES on the record), so NOT ONE socket-family shape crossed to the worker —
     * the interpreter completed and the relay count is ZERO. PLANT_GRANT_BYPASS drives the relay on the
     * refusal ANYWAY, so this verdict (which requires zero relays and zero frames) reds — a check that can
     * fail (L19). The grant-first property is gov-os's own (the record decides first); the body only counts
     * crossings, and on a true refusal there are none. */
    int grant_all = interp_done && (g_sa_relays == 0) && (g_frames_sent == 0) && (g_frames_recv == 0);
    serial_puts("GRANT-REFUSED-RELAYS: 0x"); serial_puthex32((uint32_t)g_sa_relays);
    serial_puts(" FRAMES: 0x"); serial_puthex32(g_frames_sent + g_frames_recv); serial_puts("\n");
    serial_puts(grant_all ? "GRANT-REFUSED: PASS (a refused grant reached no relay, no socket crossing)\n"
                          : "GRANT-REFUSED: FAIL (a socket crossed on a refused grant)\n");
    return grant_all ? 0 : 1;
#else
    /* GRANTED / plain socket-act: the relay ran and the connection completed (A2). Under GRANT_FIRST the
     * interpreter ALSO printed the GRANT-A1/A2 lines (gov-os's gate recorded the grant first, then handed
     * to the relay) — read off serial by the prover. */
    int all = interp_done && relayed && witnessed && conn && trail_ok && repeated && pool_ok;
#if defined(GRANT_FIRST)
    serial_puts("GRANT-FIRST: the record decided, then the granted decision handed to the relay\n");
#endif
    serial_puts(all ? "SOCKET-ACT: PASS\n" : "SOCKET-ACT: FAIL\n");
    return all ? 0 : 1;
#endif
}
#endif /* SOCKET_ACT */
