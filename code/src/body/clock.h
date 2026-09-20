/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — clock, interrupts and a seeded source of chance, on the metal (C7 P3b-3).
 *
 * design/54 §7 P3b-3. The body already boots with memory (P3b-1) and a disk (P3b-2). This slice
 * brings up, ON THE METAL, the interrupt machinery the timer rides on and THREE PORTABLE ACTS:
 *   an interrupt path   a flat GDT + a 256-gate IDT (exception stubs + IRQ stubs), the legacy 8259
 *                       PIC remapped and masked to the timer, and a PIT timer source that fires IRQ0
 *   recording-clock     a WALL CLOCK — the CMOS RTC read back as a plausible calendar time
 *   commit-window       a MONOTONIC window — rdtsc, strictly advancing across two reads
 *   entropy             a SEEDED real source of chance — a ChaCha20 CSPRNG keyed from a RUNTIME
 *                       source (rdrand where present + interrupt/tsc jitter), never a compile-time
 *                       constant (a predictable source is worse than none; the .elf stays reproducible)
 *
 * Hand-written and read whole (design/47 §2 I3, §9): no opaque code in the signed base. The interrupt
 * machinery and the three acts are the body's OWN metal performers — BENEATH the seam, not host
 * crossings. Every build and boot is the guest's nested qemu, with the nested qemu's gdb stub attached
 * from the first line so a fault during bring-up is READ FROM THE DEBUGGER, never a silent hang
 * (archi :4023). CONCURRENCY (act #8, preemptive threads) rides on these interrupts but is a later
 * slice; a cooperative body suffices here (the accepted cap).
 *
 * A NOTE ON ARITHMETIC: a freestanding -m64 body links no libgcc, and x86_64 divides 64-bit natively,
 * so no libgcc helper is referenced — rdtsc's 64-bit value is added/compared/cast (inlined by gcc),
 * and the CSPRNG and the jitter mix are pure 32-bit.
 */
#ifndef CLOCK_H
#define CLOCK_H

#include <stdint.h>
#include <stddef.h>

/* rdtsc — the CPU timestamp counter, a strictly-advancing monotonic source. static inline so each
 * translation unit that needs it gets its own copy (no libgcc, no cross-TU symbol). */
static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;   /* 64-bit OR of two 32-bit halves — inlined, no libgcc */
}

/* ── GDT + IDT + interrupt controller + timer (idt.c, isr.S) ───────────────────────────────────*/
void     gdt_install(void);          /* a flat GDT (null, code 0x08, data 0x10) + a segment reload */
void     idt_install(void);          /* 256 gates: exception stubs 0..31, remapped IRQ stubs 32..47 */
void     pic_remap(void);            /* remap the 8259 PIC (master->0x20, slave->0x28); mask to IRQ0 */
void     pit_init(uint32_t hz);      /* program the PIT to fire IRQ0 at `hz` (the timer source)      */
void     interrupts_enable(void);    /* sti                                                          */
void     interrupts_disable(void);   /* cli                                                          */
uint32_t ticks_get(void);            /* the timer tick counter — advanced by the IRQ0 handler        */

/* the asm helpers (isr.S): load the descriptor-table registers, reload the segments. The pointer is
 * a 64-bit address in the System V %rdi argument register (long mode). */
void gdt_flush(uint64_t gdt_ptr);    /* lgdt + far-return CS reload + the data segments */
void idt_flush(uint64_t idt_ptr);    /* lidt */

/* The register frame the common stub builds on the stack; the C dispatcher reads it (long mode). In
 * 64-bit mode the CPU ALWAYS pushes SS:RSP (even ring 0 -> ring 0), so the frame ends at ss. Field
 * order is LOW-address-first, matching isr.S: push r15..rax (r15 lowest), then int_no/err_code the
 * stubs pushed, then the CPU's rip/cs/rflags/rsp/ss. */
struct isr_frame {
    uint64_t r15, r14, r13, r12, r11, r10, r9, r8;   /* r15 at the lowest address */
    uint64_t rbp, rdi, rsi, rdx, rcx, rbx, rax;
    uint64_t int_no, err_code;
    uint64_t rip, cs, rflags, rsp, ss;
};
void isr_dispatch(struct isr_frame *f);   /* called by the common stub for every vector */

/* ── recording-clock (a wall clock) + commit-window (a monotonic window) (clock.c) ─────────────*/
struct wallclock { uint32_t year, month, day, hour, minute, second; };
void     rtc_read(struct wallclock *w);   /* the CMOS RTC, decoded from BCD — the wall clock       */
uint64_t mono_read(void);                 /* the monotonic window; strictly advances across reads   */
/* C7 P3b-5a-vi — the civil date to SECONDS SINCE 1970-01-01T00:00:00 UTC (a days-from-civil computation,
 * proleptic Gregorian). Pure 64-bit integer arithmetic (x86_64 divides 64-bit natively — no libgcc). The
 * body reads the CMOS RTC once at bring-up and CLOCK_REALTIME answers this epoch + the monotonic elapsed. */
uint64_t clock_epoch_seconds(const struct wallclock *w);

/* ── entropy: a seeded real CSPRNG (entropy.c) ─────────────────────────────────────────────────*/
void entropy_feed_jitter(uint32_t sample_lo);   /* the IRQ0 handler feeds interrupt-timing jitter    */
void entropy_seed_init(void);                    /* seed the CSPRNG from a RUNTIME source (rdrand+jitter)*/
int  entropy_seed_nonzero(void);                 /* 1 iff the seed key came from a real (non-zero) source*/
void entropy_draw(uint8_t *out, uint32_t n);     /* n unpredictable bytes; two draws differ           */

/* ── the self-check (clkcheck.c) — each act PASS/FAIL on the serial line ───────────────────────*/
int clock_selfcheck(void);   /* interrupts fire + both clocks + entropy; 1 iff all pass */

#endif /* CLOCK_H */
