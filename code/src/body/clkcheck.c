/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the clock/interrupt/entropy self-check on the metal (C7 P3b-3; A1/A2).
 *
 * clock_selfcheck() brings up the interrupt path (a flat GDT, a 256-gate IDT, the PIC remapped and
 * masked to the timer, the PIT firing IRQ0), enables interrupts, seeds the source of chance from the
 * runtime, and proves each of the three acts is FUNCTIONAL, not merely present:
 *   INTERRUPTS       a timer IRQ fired and was handled — the tick counter advanced from the IRQ0 path
 *   recording-clock  the CMOS wall clock reads a plausible calendar time
 *   commit-window    the monotonic window strictly advances across two reads
 *   entropy          two draws differ, neither is all-zero, and the seed came from a real source
 * Each prints CHECK <ACT>: PASS/FAIL on the serial line; the aggregate is CLOCK: PASS/FAIL. The
 * entropy draws and the clock readings are printed too, so the acceptance can cross-check them (and
 * compare the entropy across two boots — a runtime-seeded source differs boot to boot). A planted
 * fault (build.sh -D) reds exactly its check; PLANT_HANG wedges during bring-up so the nested qemu's
 * gdb stub reads the hang (a silent hang is itself a caught failure, archi :4023). Read whole; guest-only.
 */
#include "body.h"
#include "clock.h"

static void put_hex_bytes(const uint8_t *b, uint32_t n) {
    static const char h[] = "0123456789abcdef";
    for (uint32_t i = 0; i < n; i++) {
        serial_putc(h[(b[i] >> 4) & 0xF]);
        serial_putc(h[b[i] & 0xF]);
    }
}

static int buf_eq(const uint8_t *a, const uint8_t *b, uint32_t n) {
    for (uint32_t i = 0; i < n; i++) {
        if (a[i] != b[i]) {
            return 0;
        }
    }
    return 1;
}

/* Wait, BOUNDED, for a timer IRQ to advance the tick counter. Bounded by rdtsc directly (not
 * mono_read, so PLANT_MONO_BACKWARDS cannot affect this wait): a live timer advances the tick within
 * milliseconds; a dead/misrouted timer returns 0 after the bound rather than hanging the body. */
static int check_interrupts(void) {
    uint32_t before = ticks_get();
    uint64_t start = rdtsc();
    for (;;) {
        if (ticks_get() != before) {
            return 1;                              /* a timer IRQ fired and was handled */
        }
        if (rdtsc() - start > 3000000000ull) {     /* ~a few seconds of tsc; a dead timer FAILs */
            return 0;
        }
    }
}

static int check_recording_clock(struct wallclock *w) {
    rtc_read(w);
    return w->year >= 2020 && w->year <= 2100
        && w->month >= 1 && w->month <= 12
        && w->day >= 1 && w->day <= 31
        && w->hour <= 23 && w->minute <= 59 && w->second <= 60;
}

static int check_commit_window(void) {
    uint64_t a = mono_read();
    for (volatile int i = 0; i < 4000; i++) { }   /* a little work between the two reads */
    uint64_t b = mono_read();
    return b > a;                                  /* the monotonic window strictly advances */
}

static int check_entropy(void) {
    uint8_t a[16], b[16];
    entropy_draw(a, 16);
    entropy_draw(b, 16);
    int differ = !buf_eq(a, b, 16);
    int nz_a = 0, nz_b = 0;
    for (int i = 0; i < 16; i++) {
        if (a[i]) { nz_a = 1; }
        if (b[i]) { nz_b = 1; }
    }
    int seeded = entropy_seed_nonzero();
    serial_puts("ENTROPY-A: ");      put_hex_bytes(a, 16); serial_puts("\n");
    serial_puts("ENTROPY-B: ");      put_hex_bytes(b, 16); serial_puts("\n");
    serial_puts("ENTROPY-SEEDED: 0x"); serial_puthex32((uint32_t)seeded); serial_puts("\n");
    return differ && nz_a && nz_b && seeded;
}

int clock_selfcheck(void) {
#ifdef PLANT_HANG
    /* A2 near-miss: a fault during interrupt bring-up wedges the body BEFORE it announces anything.
     * With interrupts off and hlt, the CPU sleeps forever and the nested qemu stays alive — the gdb
     * stub (attached from the first line) reads the hung state; a silent hang is a caught failure. */
    serial_puts("CLOCK: bring-up (a planted hang follows)\n");
    for (;;) {
        __asm__ volatile("cli; hlt");
    }
#endif

    serial_puts("CLOCK: interrupt bring-up (GDT/IDT/PIC/PIT), nested guest\n");
    gdt_install();
    idt_install();
    pic_remap();
#ifndef PLANT_TIMER_DEAD
    pit_init(1000);                 /* the timer source: IRQ0 at 1000 Hz */
#endif
    interrupts_enable();

    int itr = check_interrupts();
    serial_puts("TICKS: 0x");
    serial_puthex32(ticks_get());
    serial_puts("\n");

    /* seed the source of chance AFTER interrupts have fired — the timer jitter is in the pool now. */
    entropy_seed_init();

    struct wallclock w;
    int rc  = check_recording_clock(&w);
    serial_puts("WALLCLOCK: y=0x");  serial_puthex32(w.year);
    serial_puts(" mo=0x");           serial_puthex32(w.month);
    serial_puts(" d=0x");            serial_puthex32(w.day);
    serial_puts(" h=0x");            serial_puthex32(w.hour);
    serial_puts(" mi=0x");           serial_puthex32(w.minute);
    serial_puts(" s=0x");            serial_puthex32(w.second);
    serial_puts("\n");

    int cw  = check_commit_window();
    int ent = check_entropy();

    serial_puts(itr ? "CHECK INTERRUPTS: PASS\n"      : "CHECK INTERRUPTS: FAIL\n");
    serial_puts(rc  ? "CHECK RECORDING-CLOCK: PASS\n" : "CHECK RECORDING-CLOCK: FAIL\n");
    serial_puts(cw  ? "CHECK COMMIT-WINDOW: PASS\n"   : "CHECK COMMIT-WINDOW: FAIL\n");
    serial_puts(ent ? "CHECK ENTROPY: PASS\n"         : "CHECK ENTROPY: FAIL\n");

    int all = itr && rc && cw && ent;
    serial_puts(all ? "CLOCK: PASS\n" : "CLOCK: FAIL\n");
    return all;
}
