/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — shared declarations (C7 P3b-1; design/54 §7 P3b-1).
 *
 * The freestanding memory body's one header: the multiboot info shape the loader hands us,
 * and the four surfaces the body brings up on the metal — a polled serial line, a physical
 * frame allocator (PMM), virtual memory / paging (VMM), and a kernel heap. Hand-written and
 * read whole (design/47 §2 I3, §9): no opaque code in the signed base. The only DERIVED file
 * is rows_digest.h (the twelve rows' digest), included at the bottom.
 */
#ifndef BODY_H
#define BODY_H

#include <stdint.h>
#include <stddef.h>

/* ── Multiboot1 ──────────────────────────────────────────────────────────────────────────
 * The loader leaves this magic in eax at _start and a pointer to the info structure in ebx. */
#define MULTIBOOT_BOOTLOADER_MAGIC 0x2BADB002u
#define MB_FLAG_MODS               (1u << 3)   /* info.flags bit 3: mods_count/mods_addr valid (C7 P3b-4c) */
#define MB_FLAG_MMAP               (1u << 6)   /* info.flags bit 6: mmap_length/mmap_addr valid */

struct mb_info {
    uint32_t flags;
    uint32_t mem_lower, mem_upper;
    uint32_t boot_device;
    uint32_t cmdline;
    uint32_t mods_count, mods_addr;
    uint32_t syms[4];
    uint32_t mmap_length;   /* offset 44 */
    uint32_t mmap_addr;     /* offset 48 */
    /* the rest of the structure is unused by this slice and deliberately omitted. */
};

/* One multiboot1 module descriptor (mbi->mods_addr points at an array of these; C7 P3b-4c). The
 * module's bytes are the physical range [mod_start, mod_end) — the body reads them through its direct
 * map after vmm_init, and the PMM reserves the range so the program never gets a module frame. */
struct mb_mod {
    uint32_t mod_start;
    uint32_t mod_end;
    uint32_t cmdline;
    uint32_t pad;
} __attribute__((packed));

/* C7 P3b-4c — the ONE sealed image, carried as the first multiboot module. kmain sets these from
 * mbi->mods after vmm_init; 0/0 when no module is attached (every non-interp body build). */
extern uint64_t g_sealed_module_phys;
extern uint64_t g_sealed_module_len;

/* One BIOS/e820 memory-map entry, as the loader presents it. `size` does not count itself, so
 * the next entry sits at (uint8_t*)entry + entry->size + 4. type 1 == available RAM. */
struct mb_mmap_entry {
    uint32_t size;
    uint64_t addr;
    uint64_t len;
    uint32_t type;
} __attribute__((packed));

/* ── Serial: a polled 16550 UART on COM1 (0x3F8), output only ─────────────────────────────*/
void serial_init(void);
void serial_putc(char c);
void serial_puts(const char *s);
void serial_puthex32(uint32_t v);
void serial_puthex64(uint64_t v);

/* ── The higher-half layout (C7 P3b-4m, L20 — the hosted program owns the standard low range) ─────
 * An ordinary program is linked to load at the platform's CANONICAL BASE (0x400000 on x86_64), and the
 * interpreter is such a program (ET_EXEC first LOAD at 0x400000) that cannot be moved. So the body never
 * claims that range: its own image sits at 1 MiB, BENEATH the canonical base; it reaches all physical
 * memory through its OWN DIRECT MAP in the higher half (DIRECT_MAP_BASE + phys); the supervisor identity
 * map is kept only for [0, CANONICAL_BASE) (the body's image and low memory) and WITHDRAWN from the
 * program's range (CANONICAL_BASE up), so a user page is mappable from the canonical base. */
#define CANONICAL_BASE   0x400000ull            /* the x86_64 ET_EXEC base: the program's range starts here,
                                                 * the dividing address the withdrawal keeps beneath (the ONE
                                                 * place this magic number is named — body.h) */
#define DIRECT_MAP_BASE  0xffff800000000000ull  /* the conventional higher-half direct-map base (PML4[256]) */
#define DIRECT_MAP_MAX   (1024ull * 1024ull * 1024ull)  /* the CAP the direct map covers: [0, 1 GiB). kmain
                                                 * checks the loader-reported physical max against it — a guest
                                                 * with more RAM than the cap faults the check (precision 1) */

/* THE ONE ACCESSOR: the body reaches a physical address through its own direct map, never at its identity
 * address (withdrawn from the program's range). Every frame the body touches after vmm_init — page tables,
 * PMM frames, the enclosure's segment copies — goes through this. Valid only once vmm_init has installed
 * the direct map (before then the boot scaffold's low identity map is active; pmm_init reads the low mmap
 * on that scaffold). */
static inline void *phys_to_virt(uint64_t phys) {
    return (void *)(DIRECT_MAP_BASE + phys);
}

/* ── PMM: a bitmap physical frame allocator over 4 KiB frames ─────────────────────────────*/
#define FRAME_SIZE 4096u

void     pmm_init(const struct mb_info *mbi);   /* parse the mmap; reserve the body's frames */
uint32_t pmm_alloc(void);                        /* a free physical frame address, or 0 (OOM) */
void     pmm_free(uint32_t frame);
uint32_t pmm_free_count(void);
uint64_t pmm_reported_max(void);                 /* the highest physical addr the loader's mmap reports
                                                  * (UNCLAMPED — the direct-map cap check reads this) */

/* ── VMM: four-level paging (x86_64 long mode), 4 KiB pages ──────────────────────────────────────────────────────*/
void vmm_init(void);                    /* build+install the body's own four-level tables + the direct map */
int  vmm_map(uint64_t virt, uint64_t phys);   /* map one page (supervisor); 0 ok, -1 if no table frame */
int  vmm_map_user(uint64_t virt, uint64_t phys); /* map one USER page (ring 3) — the enclosure loader (P3b-4a) */
void vmm_unmap(uint64_t virt);
void vmm_unmap_in(uint64_t cr3, uint64_t virt);  /* C7 P3b-6c(iii) A4: unmap in a given hierarchy (active map) */
uint64_t vmm_query(uint64_t virt);       /* the PTE mapping virt (0 if unmapped) — the layout self-check reads it */
int  vmm_program_range_identity_withdrawn(void); /* 1 iff no supervisor identity huge page covers [CANONICAL_BASE, 1 GiB) */

/* ── Heap: allocate/free over the body's own region ───────────────────────────────────────*/
void  heap_init(void);
void *kmalloc(uint32_t size);
void  kfree(void *p);

/* ── The twelve rows' digest — DERIVED from the seam_act_definition rows (A3, §9) ─────────*/
#include "rows_digest.h"

#endif /* BODY_H */
