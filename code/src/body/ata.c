/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the block device: a polled ATA/PIO driver (C7 P3b-2; the spike's Q-E disk, part 1).
 *
 * The body's OWN metal performer for reaching its disk — LBA28 PIO on the primary ATA bus (I/O base
 * 0x1F0, control 0x3F6, primary master). This is the block layer the five record acts ride on; it
 * is BENEATH the seam (the body performing an act on its own disk), not a host crossing. No
 * interrupts (Q-C is a later P3b row): every transfer polls the status register. Every access is
 * bounded by a spin counter, so a missing disk fails (-1) rather than hanging the body. Read whole.
 *
 * Every port access here is the guest's virtual IDE controller under the nested qemu; nothing
 * touches the host kernel (L11 / EP-00 rule 9).
 */
#include "disk.h"

#define ATA_IO_BASE   0x1F0u
#define ATA_CTRL_BASE 0x3F6u

#define ATA_REG_DATA    (ATA_IO_BASE + 0)   /* 16-bit data port                       */
#define ATA_REG_ERROR   (ATA_IO_BASE + 1)
#define ATA_REG_SECCNT  (ATA_IO_BASE + 2)   /* sector count                           */
#define ATA_REG_LBA0    (ATA_IO_BASE + 3)   /* LBA bits 0..7                          */
#define ATA_REG_LBA1    (ATA_IO_BASE + 4)   /* LBA bits 8..15                         */
#define ATA_REG_LBA2    (ATA_IO_BASE + 5)   /* LBA bits 16..23                        */
#define ATA_REG_DRIVE   (ATA_IO_BASE + 6)   /* drive/head + LBA bits 24..27           */
#define ATA_REG_STATUS  (ATA_IO_BASE + 7)   /* status (read) / command (write)        */
#define ATA_REG_CMD     (ATA_IO_BASE + 7)

#define ATA_SR_BSY  0x80u   /* busy            */
#define ATA_SR_DRDY 0x40u   /* drive ready     */
#define ATA_SR_DRQ  0x08u   /* data request    */
#define ATA_SR_ERR  0x01u   /* error           */

#define ATA_CMD_READ_PIO   0x20u
#define ATA_CMD_WRITE_PIO  0x30u
#define ATA_CMD_CACHE_FLUSH 0xE7u

#define ATA_MASTER_LBA 0xE0u   /* master, LBA mode; low nibble carries LBA bits 24..27 */

#define ATA_SPIN 2000000u      /* bounded poll; a missing disk fails instead of hanging */

static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}
static inline uint8_t inb(uint16_t port) {
    uint8_t r;
    __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}
static inline uint16_t inw(uint16_t port) {
    uint16_t r;
    __asm__ volatile("inw %1, %0" : "=a"(r) : "Nd"(port));
    return r;
}
static inline void outw(uint16_t port, uint16_t val) {
    __asm__ volatile("outw %0, %1" : : "a"(val), "Nd"(port));
}

/* A short delay after a command: read the alternate status register a few times (~400 ns). */
static void ata_delay400(void) {
    for (int i = 0; i < 4; i++) {
        (void)inb(ATA_CTRL_BASE);
    }
}

/* Spin until BSY clears; then require DRQ (data ready). Returns 0 ok, -1 on timeout or ERR. */
static int ata_wait_drq(void) {
    for (uint32_t i = 0; i < ATA_SPIN; i++) {
        uint8_t s = inb(ATA_REG_STATUS);
        if (s == 0xFFu) {
            return -1;                 /* floating bus — no drive */
        }
        if (s & ATA_SR_ERR) {
            return -1;
        }
        if (!(s & ATA_SR_BSY) && (s & ATA_SR_DRQ)) {
            return 0;
        }
    }
    return -1;
}

/* Spin until BSY clears and DRDY is set (used before issuing a command / after a flush). */
static int ata_wait_ready(void) {
    for (uint32_t i = 0; i < ATA_SPIN; i++) {
        uint8_t s = inb(ATA_REG_STATUS);
        if (s == 0xFFu) {
            return -1;
        }
        if (!(s & ATA_SR_BSY) && (s & ATA_SR_DRDY)) {
            return 0;
        }
    }
    return -1;
}

int ata_present(void) {
    /* Select the primary master, let it settle, and read the status. A floating (absent) bus reads
     * 0xFF; a present qemu IDE disk reports a real status with DRDY. Observes a state we did not
     * create (§A19). */
    outb(ATA_REG_DRIVE, ATA_MASTER_LBA);
    ata_delay400();
    uint8_t s = inb(ATA_REG_STATUS);
    if (s == 0xFFu || s == 0x00u) {
        return 0;
    }
    return (ata_wait_ready() == 0) ? 1 : 0;
}

static void ata_select_lba(uint32_t lba) {
    outb(ATA_REG_DRIVE, (uint8_t)(ATA_MASTER_LBA | ((lba >> 24) & 0x0Fu)));
    outb(ATA_REG_SECCNT, 1);
    outb(ATA_REG_LBA0, (uint8_t)(lba & 0xFFu));
    outb(ATA_REG_LBA1, (uint8_t)((lba >> 8) & 0xFFu));
    outb(ATA_REG_LBA2, (uint8_t)((lba >> 16) & 0xFFu));
}

int ata_read_sector(uint32_t lba, void *buf512) {
    if (ata_wait_ready() != 0) {
        return -1;
    }
    ata_select_lba(lba);
    outb(ATA_REG_CMD, ATA_CMD_READ_PIO);
    if (ata_wait_drq() != 0) {
        return -1;
    }
    uint16_t *w = (uint16_t *)buf512;
    for (int i = 0; i < 256; i++) {          /* 256 words = 512 bytes */
        w[i] = inw(ATA_REG_DATA);
    }
    ata_delay400();
    return 0;
}

int ata_write_sector(uint32_t lba, const void *buf512) {
    if (ata_wait_ready() != 0) {
        return -1;
    }
    ata_select_lba(lba);
    outb(ATA_REG_CMD, ATA_CMD_WRITE_PIO);
    if (ata_wait_drq() != 0) {
        return -1;
    }
    const uint16_t *w = (const uint16_t *)buf512;
    for (int i = 0; i < 256; i++) {
        outw(ATA_REG_DATA, w[i]);
    }
    ata_delay400();
    return 0;
}

int ata_flush(void) {
    /* The durability barrier: ATA CACHE FLUSH makes the written sectors durable — the metal form of
     * the record pen's fdatasync and the atomic-write-once's dir fsync. */
    if (ata_wait_ready() != 0) {
        return -1;
    }
    outb(ATA_REG_CMD, ATA_CMD_CACHE_FLUSH);
    return ata_wait_ready();
}
