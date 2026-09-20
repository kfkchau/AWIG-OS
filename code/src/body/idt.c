/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the GDT, the IDT, the 8259 PIC and the PIT timer (C7 P3b-3; RE-BASED to x86_64
 * long mode, C7 P3b-4L).
 *
 * The C half of the interrupt path, now for long mode. gdt_install lays a flat 64-bit GDT (null /
 * 64-bit code 0x08 with the L bit / data 0x10) and reloads the segments (via isr.S: gdt_flush, a far
 * return that reloads CS in 64-bit) so the body owns its own descriptors rather than the temporary
 * trampoline GDT. idt_install fills 256 SIXTEEN-BYTE long-mode gates — the exception stubs (0..31) and
 * the remapped IRQ stubs (32..47) from isr.S's isr_stub_table (64-bit stub addresses) — and loads the
 * IDT. pic_remap moves the legacy 8259 vectors clear of the CPU exceptions and masks every line but
 * IRQ0 (the timer). pit_init programs the 8254 PIT to raise IRQ0 at a chosen rate. isr_dispatch is the
 * one C entry every vector reaches: the timer advances a tick counter and feeds interrupt-timing
 * jitter to the entropy pool; any other exception during bring-up is announced and HALTED (so the
 * nested qemu's gdb stub can read the state — never a silent triple-fault, archi :4023). Read whole;
 * guest-only (every port access is the guest's).
 *
 * A2/A5 near-misses (build.sh -D flags — a check that cannot fail is not a check):
 *   PLANT_BAD_GATE   — install the timer's gate pointing at the WRONG stub (IRQ1's), so the timer IRQ
 *                      is misrouted, no tick advances, and the interrupt self-check FAILs
 *   PLANT_TIMER_DEAD — never program the PIT and leave IRQ0 masked, so the timer never ticks and the
 *                      interrupt self-check FAILs
 */
#include "body.h"
#include "clock.h"
#include "enclosure.h"   /* C7 P3b-4a: a ring-3 worker fault recovers to the enclosure driver, not a halt */

/* ── port I/O ──────────────────────────────────────────────────────────────────────────────────*/
static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}
static inline uint8_t inb(uint16_t port) {
    uint8_t r;
    __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}
static inline void io_wait(void) { outb(0x80, 0); }   /* a short I/O delay on an unused port */

/* ── the GDT: three flat entries, the code segment a 64-bit (L-bit) segment ────────────────────*/
struct gdt_entry {
    uint16_t limit_low;
    uint16_t base_low;
    uint8_t  base_mid;
    uint8_t  access;
    uint8_t  gran;          /* limit high nibble + flags (L bit lives here for the code segment) */
    uint8_t  base_high;
} __attribute__((packed));

struct dt_ptr {
    uint16_t limit;
    uint64_t base;          /* 64-bit table base — the lgdt/lidt operand is 10 bytes in long mode */
} __attribute__((packed));

static struct gdt_entry g_gdt[3];
static struct dt_ptr    g_gdtp;

static void gdt_set(int i, uint32_t base, uint32_t limit, uint8_t access, uint8_t flags) {
    g_gdt[i].limit_low = (uint16_t)(limit & 0xFFFF);
    g_gdt[i].base_low  = (uint16_t)(base & 0xFFFF);
    g_gdt[i].base_mid  = (uint8_t)((base >> 16) & 0xFF);
    g_gdt[i].access    = access;
    g_gdt[i].gran      = (uint8_t)(((limit >> 16) & 0x0F) | (flags & 0xF0));
    g_gdt[i].base_high = (uint8_t)((base >> 24) & 0xFF);
}

void gdt_install(void) {
    gdt_set(0, 0, 0, 0, 0);                       /* the null descriptor                        */
    gdt_set(1, 0, 0, 0x9A, 0xA0);                 /* code: ring 0, exec/read, L=1 (64-bit)      */
    gdt_set(2, 0, 0, 0x92, 0xC0);                 /* data: ring 0, read/write (base/limit ignored)*/
    g_gdtp.limit = (uint16_t)(sizeof(g_gdt) - 1);
    g_gdtp.base  = (uint64_t)(uintptr_t)&g_gdt[0];
    gdt_flush((uint64_t)(uintptr_t)&g_gdtp);
}

/* ── the IDT: 256 sixteen-byte long-mode interrupt gates ───────────────────────────────────────*/
struct idt_gate {
    uint16_t off_low;
    uint16_t selector;
    uint8_t  ist;           /* interrupt-stack-table index (0 = use the current stack) */
    uint8_t  type_attr;     /* present, ring 0, 64-bit interrupt gate                  */
    uint16_t off_mid;
    uint32_t off_high;      /* bits 32..63 of the handler offset                       */
    uint32_t zero;
} __attribute__((packed));

static struct idt_gate g_idt[256];
static struct dt_ptr   g_idtp;

extern uint64_t isr_stub_table[48];   /* from isr.S — the 64-bit stub address for each vector 0..47 */

static void idt_set(int n, uint64_t handler) {
    g_idt[n].off_low   = (uint16_t)(handler & 0xFFFF);
    g_idt[n].selector  = 0x08;              /* the flat 64-bit code selector          */
    g_idt[n].ist       = 0;
    g_idt[n].type_attr = 0x8E;              /* present, ring 0, 64-bit interrupt gate */
    g_idt[n].off_mid   = (uint16_t)((handler >> 16) & 0xFFFF);
    g_idt[n].off_high  = (uint32_t)((handler >> 32) & 0xFFFFFFFF);
    g_idt[n].zero      = 0;
}

void idt_install(void) {
    for (int i = 0; i < 256; i++) {
        idt_set(i, 0);                      /* absent-by-default; a stray vector faults, not runs */
    }
    for (int i = 0; i < 48; i++) {
        idt_set(i, isr_stub_table[i]);
    }

#ifdef PLANT_BAD_GATE
    /* A2 near-miss: point the timer's gate (vector 32) at the WRONG stub (IRQ1, vector 33). The timer
     * IRQ is then delivered to the wrong handler — the dispatcher sees int_no 33, EOIs IRQ1, and never
     * advances the tick counter, so the interrupt self-check FAILs (and no wedge: the wrong handler
     * still returns). A gate pointing at the wrong handler is exactly the fault archi named (:4023). */
    idt_set(32, isr_stub_table[33]);
#endif

    g_idtp.limit = (uint16_t)(sizeof(g_idt) - 1);
    g_idtp.base  = (uint64_t)(uintptr_t)&g_idt[0];
    idt_flush((uint64_t)(uintptr_t)&g_idtp);
}

/* ── the 8259 PIC: remap and mask ──────────────────────────────────────────────────────────────*/
#define PIC1_CMD  0x20
#define PIC1_DATA 0x21
#define PIC2_CMD  0xA0
#define PIC2_DATA 0xA1
#define PIC_EOI   0x20

void pic_remap(void) {
    outb(PIC1_CMD, 0x11); io_wait();     /* ICW1: begin init, expect ICW4 */
    outb(PIC2_CMD, 0x11); io_wait();
    outb(PIC1_DATA, 0x20); io_wait();    /* ICW2: master vector base -> 32 */
    outb(PIC2_DATA, 0x28); io_wait();    /* ICW2: slave  vector base -> 40 */
    outb(PIC1_DATA, 0x04); io_wait();    /* ICW3: slave on master IRQ2 */
    outb(PIC2_DATA, 0x02); io_wait();
    outb(PIC1_DATA, 0x01); io_wait();    /* ICW4: 8086 mode */
    outb(PIC2_DATA, 0x01); io_wait();
#ifdef PLANT_TIMER_DEAD
    /* A2 near-miss: mask EVERY line, IRQ0 included, so no timer IRQ ever reaches the CPU (qemu's PIT
     * still free-runs after reset, so merely skipping pit_init would NOT kill the timer — masking
     * IRQ0 is what makes it genuinely dead). The tick counter never advances; the interrupt self-check
     * FAILs. A timer that never ticks is exactly the fault archi named (:4023). */
    outb(PIC1_DATA, 0xFF);
    outb(PIC2_DATA, 0xFF);
#else
    /* mask everything but IRQ0 (the timer) on the master; mask the whole slave. */
    outb(PIC1_DATA, 0xFE);
    outb(PIC2_DATA, 0xFF);
#endif
}

static void pic_eoi(uint32_t irq) {
    if (irq >= 8) {
        outb(PIC2_CMD, PIC_EOI);
    }
    outb(PIC1_CMD, PIC_EOI);
}

/* ── the PIT (8254): the timer source on IRQ0 ─────────────────────────────────────────────────*/
#define PIT_CH0  0x40
#define PIT_CMD  0x43
#define PIT_HZ   1193182u

void pit_init(uint32_t hz) {
    uint32_t divisor = PIT_HZ / hz;
    outb(PIT_CMD, 0x36);                          /* channel 0, lo/hi byte, mode 3 (square wave) */
    outb(PIT_CH0, (uint8_t)(divisor & 0xFF));
    outb(PIT_CH0, (uint8_t)((divisor >> 8) & 0xFF));
}

void interrupts_enable(void)  { __asm__ volatile("sti"); }
void interrupts_disable(void) { __asm__ volatile("cli"); }

/* ── the tick counter + the one C dispatcher ──────────────────────────────────────────────────*/
static volatile uint32_t g_ticks;

uint32_t ticks_get(void) { return g_ticks; }

void isr_dispatch(struct isr_frame *f) {
    if (f->int_no == 32) {                        /* IRQ0 — the timer */
        g_ticks++;
        entropy_feed_jitter((uint32_t)rdtsc());   /* the exact tsc at delivery is real jitter */
        pic_eoi(0);                               /* ack the PIC BEFORE any context switch */
        /* C7 P3b-4f-ii: the preemptive scheduler's tick — expire timed waits, and if a ring-3 context was
         * preempted and another thread is runnable, take a turn (never inside a ring-0 act). Inert until
         * the concurrency floor sets g_sched_on. */
        sched_timer_tick(f);
    } else if (f->int_no >= 32 && f->int_no < 48) {
        pic_eoi(f->int_no - 32);                  /* any other IRQ: acknowledge it and move on */
    } else {
        /* A WORKER FAULT (C7 P3b-4a): a ring-3 exception (f->cs RPL == 3) while a worker runs is the
         * hardware ENFORCING the enclosure — a #PF on the body's memory (the direct reach faulted), a #UD
         * from a disabled SYSCALL, a #GP from a privileged op. The body RECORDS it and RECOVERS to the
         * enclosure driver (body_longjmp), never a halt; the enclosure self-check reads what the machine
         * did (L18: enclosure is a hardware fact). A body-side (ring 0) fault still halts loudly below. */
        if (g_in_worker && (f->cs & 3u) == 3u) {
            uint64_t cr2;
            __asm__ volatile("mov %%cr2, %0" : "=r"(cr2));
            g_worker_fault   = f->int_no;
            g_worker_cr2     = cr2;
            g_worker_faultcs = f->cs;
            g_worker_rip     = f->rip;
            g_worker_rsp     = f->rsp;
            g_worker_rbp     = f->rbp;
            g_in_worker      = 0;
            body_longjmp(g_active_ctx, 2);
            /* unreachable */
        }
        /* a CPU exception during bring-up. Announce it (64-bit rip) and HALT (interrupts off) so the
         * nested qemu's gdb stub can read the faulted state — never a silent triple-fault (archi :4023). */
        serial_puts("EXC: vector=0x");
        serial_puthex32((uint32_t)f->int_no);
        serial_puts(" err=0x");
        serial_puthex32((uint32_t)f->err_code);
        serial_puts(" rip=0x");
        serial_puthex64(f->rip);
        serial_puts("\n");
        for (;;) {
            __asm__ volatile("cli; hlt");
        }
    }
}
