/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the polled serial line (C7 P3b-1; the spike's Q-D surface, carried in).
 *
 * A polled 16550 UART on COM1 (0x3F8): init, then putc spins on the line-status THR-empty bit
 * and writes one byte. Output only — the body announces, it does not read. This is the whole
 * I/O surface the slice needs (~30 lines), and it is what carries the memory result and the
 * twelve rows' digest onto the serial line the nested qemu captures.
 */
#include "body.h"

#define COM1 0x3F8

static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}
static inline uint8_t inb(uint16_t port) {
    uint8_t r;
    __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}

void serial_init(void) {
    outb(COM1 + 1, 0x00);   /* disable interrupts                     */
    outb(COM1 + 3, 0x80);   /* DLAB: set baud divisor                 */
    outb(COM1 + 0, 0x03);   /* divisor low  (0x0003 -> 38400 baud)    */
    outb(COM1 + 1, 0x00);   /* divisor high                           */
    outb(COM1 + 3, 0x03);   /* 8 bits, no parity, one stop bit        */
    outb(COM1 + 2, 0xC7);   /* enable FIFO, clear, 14-byte threshold  */
    outb(COM1 + 4, 0x0B);   /* RTS/DSR set                            */
}

static int thr_empty(void) {
    return inb(COM1 + 5) & 0x20;   /* line status: transmit-holding-register empty */
}

void serial_putc(char c) {
    while (!thr_empty()) { }
    outb(COM1, (uint8_t)c);
}

void serial_puts(const char *s) {
    while (*s) {
        if (*s == '\n') {
            serial_putc('\r');   /* CRLF, so a terminal renders each line cleanly */
        }
        serial_putc(*s++);
    }
}

void serial_puthex32(uint32_t v) {
    static const char hex[] = "0123456789abcdef";
    for (int i = 7; i >= 0; i--) {
        serial_putc(hex[(v >> (i * 4)) & 0xF]);
    }
}

void serial_puthex64(uint64_t v) {
    static const char hex[] = "0123456789abcdef";
    for (int i = 15; i >= 0; i--) {
        serial_putc(hex[(v >> (i * 4)) & 0xF]);
    }
}
