/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the two clock acts on the metal (C7 P3b-3; A1/A2).
 *
 * recording-clock (the wall clock, datetime.now(utc) above the seam today) = read the CMOS RTC and
 * decode it to a calendar time. commit-window (the monotonic window, time.monotonic today) = rdtsc,
 * which advances every CPU cycle and so strictly advances across any two reads. These are the body's
 * OWN metal performers of the two clock acts; they add no act (both exist in the seam's closed set)
 * and found nothing. Read whole; guest-only (every port access is the guest's virtual RTC).
 *
 * A2 near-miss (build.sh -D flag): PLANT_MONO_BACKWARDS makes the monotonic window read a DECREASING
 * value, so the "strictly advances across two reads" self-check FAILs — a clock that goes backwards is
 * exactly the fault archi named (:4023). A check that cannot fail is not a check.
 */
#include "body.h"
#include "clock.h"

/* ── the CMOS RTC (recording-clock) ───────────────────────────────────────────────────────────*/
#define CMOS_ADDR 0x70
#define CMOS_DATA 0x71

static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}
static inline uint8_t inb(uint16_t port) {
    uint8_t r;
    __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}

static uint8_t cmos_read(uint8_t reg) {
    outb(CMOS_ADDR, reg);
    return inb(CMOS_DATA);
}

static int update_in_progress(void) {
    return cmos_read(0x0A) & 0x80;   /* status A bit 7: an RTC update is under way */
}

static uint8_t bcd2bin(uint8_t v) {
    return (uint8_t)((v & 0x0F) + ((v >> 4) & 0x0F) * 10);
}

void rtc_read(struct wallclock *w) {
    /* Read the registers, then read them again, and repeat (bounded) until two consecutive reads
     * agree while no update is in progress — so we never latch a half-updated time. */
    uint8_t s = 0, mi = 0, h = 0, d = 0, mo = 0, y = 0, cent = 0, lstatb;
    uint8_t ls = 0, lm = 0, lh = 0, ld = 0, lmo = 0, ly = 0, lc = 0;

    for (int spin = 0; spin < 1000000; spin++) {
        if (update_in_progress()) {
            continue;
        }
        s    = cmos_read(0x00);
        mi   = cmos_read(0x02);
        h    = cmos_read(0x04);
        d    = cmos_read(0x07);
        mo   = cmos_read(0x08);
        y    = cmos_read(0x09);
        cent = cmos_read(0x32);   /* the century register (0 if the RTC does not carry one) */
        if (s == ls && mi == lm && h == lh && d == ld && mo == lmo && y == ly && cent == lc) {
            break;                 /* two consecutive stable reads */
        }
        ls = s; lm = mi; lh = h; ld = d; lmo = mo; ly = y; lc = cent;
    }

    lstatb = cmos_read(0x0B);      /* status B: bit 2 clear => the values are BCD (qemu's default) */
    if (!(lstatb & 0x04)) {
        s = bcd2bin(s); mi = bcd2bin(mi); d = bcd2bin(d); mo = bcd2bin(mo); y = bcd2bin(y);
        /* the hour's high bit is the PM flag in 12-hour mode; strip it before BCD-decoding */
        h = (uint8_t)((bcd2bin((uint8_t)(h & 0x7F))) | (h & 0x80));
        cent = bcd2bin(cent);
    }

    uint32_t year = y;
    if (cent >= 19 && cent <= 21) {
        year = (uint32_t)cent * 100u + y;   /* a real century register */
    } else {
        year = 2000u + y;                    /* no century register: assume the 21st century */
    }

    w->year   = year;
    w->month  = mo;
    w->day    = d;
    w->hour   = (uint32_t)(h & 0x7F);
    w->minute = mi;
    w->second = s;
}

/* ── the civil date to a Unix epoch (C7 P3b-5a-vi) ────────────────────────────────────────────
 * days-from-civil (Howard Hinnant's public-domain algorithm): the number of days from 1970-01-01 to a
 * proleptic-Gregorian y/m/d, then seconds = days*86400 + h*3600 + m*60 + s. Pure integer arithmetic; the
 * body's RTC (qemu -rtc base=utc) reads a UTC civil date, so no timezone term. Valid for any real RTC year
 * (the estate's decision times are 2020s); a nonsense RTC year yields a nonsense-but-monotone epoch, never a
 * crash. The recording-clock (CLOCK_REALTIME) is this epoch + the monotonic elapsed since the boot read. */
uint64_t clock_epoch_seconds(const struct wallclock *w) {
    int64_t y = (int64_t)w->year;
    uint32_t m = w->month ? w->month : 1u;     /* a zero RTC month/day (unformatted CMOS) -> 1, never /0 */
    uint32_t d = w->day   ? w->day   : 1u;
    y -= (m <= 2);
    int64_t era = (y >= 0 ? y : y - 399) / 400;
    uint64_t yoe = (uint64_t)(y - era * 400);                        /* [0, 399] */
    uint64_t doy = (153u * (m + (m > 2 ? -3u : 9u)) + 2u) / 5u + d - 1u;   /* [0, 365] */
    uint64_t doe = yoe * 365u + yoe / 4u - yoe / 100u + doy;         /* [0, 146096] */
    int64_t days = era * 146097 + (int64_t)doe - 719468;            /* days since 1970-01-01 */
    if (days < 0) { days = 0; }                                     /* a pre-1970 RTC clamps at the epoch */
    return (uint64_t)days * 86400ull
         + (uint64_t)w->hour * 3600ull + (uint64_t)w->minute * 60ull + (uint64_t)w->second;
}

/* ── the monotonic window (commit-window) ─────────────────────────────────────────────────────*/
uint64_t mono_read(void) {
#ifdef PLANT_MONO_BACKWARDS
    /* A2 near-miss: a monotonic window that goes BACKWARDS. Each read returns a smaller value, so the
     * "strictly advances across two reads" self-check FAILs. */
    static uint32_t backwards = 0xFFFFFFFFu;
    backwards -= 0x100000u;
    return (uint64_t)backwards;
#else
    return rdtsc();   /* the CPU timestamp counter: strictly advances across any two reads */
#endif
}
