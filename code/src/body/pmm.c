/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the physical frame allocator (C7 P3b-1; the spike's Q-B, first third).
 *
 * A bitmap PMM over 4 KiB frames. pmm_init parses the multiboot memory map: every frame starts
 * USED, available (type 1) regions are cleared to FREE, then the body reserves what it is
 * standing on — the low 1 MiB and its own image, 0 .. kernel_end (the bitmap and the paging
 * structures live in .bss inside that image, so they are covered). pmm_alloc hands the LOWEST
 * free frame, which keeps early allocations inside the identity-mapped low region the VMM sets
 * up — so a freshly allocated page-table frame is reachable at its physical address. Frame indices
 * stay 32-bit (the mmap is clamped to MAX_PHYS well under 4 GiB) while pointer-derived addresses are
 * uintptr_t; no 64-bit division is used, so the freestanding -m64 body links no libgcc helper.
 */
#include "body.h"

/* Cap the managed range at 256 MiB (the nested guest boots with -m 256). 65536 frames -> an
 * 8 KiB bitmap in .bss. A region above the cap is ignored, reported as reserved. */
#define MAX_PHYS   (256u * 1024u * 1024u)
#define MAX_FRAMES (MAX_PHYS / FRAME_SIZE)

static uint8_t  frame_bitmap[MAX_FRAMES / 8];   /* 1 = used, 0 = free */
static uint32_t g_free_frames;
static uint64_t g_reported_max_phys;            /* the highest phys addr the loader's mmap reports —
                                                 * UNCLAMPED (not capped to MAX_PHYS); the direct-map
                                                 * cap check (C7 P3b-4m) reads it */

extern char kernel_end[];   /* the image top, from linker.ld */

static inline void bm_set(uint32_t f)   { frame_bitmap[f >> 3] |=  (uint8_t)(1u << (f & 7)); }
static inline void bm_clear(uint32_t f) { frame_bitmap[f >> 3] &= (uint8_t)~(1u << (f & 7)); }
static inline int  bm_test(uint32_t f)  { return (frame_bitmap[f >> 3] >> (f & 7)) & 1; }

static void reserve_range(uintptr_t start, uintptr_t end) {
    for (uintptr_t p = start & ~((uintptr_t)(FRAME_SIZE - 1)); p < end; p += FRAME_SIZE) {
        uint32_t f = (uint32_t)(p >> 12);
        if (f < MAX_FRAMES && !bm_test(f)) {
            bm_set(f);
            g_free_frames--;
        }
    }
}

void pmm_init(const struct mb_info *mbi) {
    for (uint32_t i = 0; i < sizeof(frame_bitmap); i++) {
        frame_bitmap[i] = 0xFF;   /* everything used to begin with */
    }
    g_free_frames = 0;
    g_reported_max_phys = 0;

    if (mbi->flags & MB_FLAG_MMAP) {
        uintptr_t addr = mbi->mmap_addr;                       /* a low physical addr, identity-mapped */
        uintptr_t end  = (uintptr_t)mbi->mmap_addr + mbi->mmap_length;
        while (addr < end) {
            const struct mb_mmap_entry *e = (const struct mb_mmap_entry *)addr;
            if (e->type == 1) {
                uint64_t top64 = e->addr + e->len;             /* the UNCLAMPED reported top of this region */
                if (top64 > g_reported_max_phys) {
                    g_reported_max_phys = top64;               /* highest reported phys addr, for the cap check */
                }
            }
            if (e->type == 1 && e->addr < MAX_PHYS) {
                uint32_t s = (uint32_t)e->addr;
                uint32_t l;
                uint64_t top = e->addr + e->len;                 /* 64-bit add + compare only */
                l = (top > MAX_PHYS) ? (MAX_PHYS - s) : (uint32_t)e->len;
                uint32_t f0 = (s + FRAME_SIZE - 1) >> 12;         /* first whole frame          */
                uint32_t f1 = (s + l) >> 12;                      /* one past the last frame    */
                for (uint32_t f = f0; f < f1 && f < MAX_FRAMES; f++) {
                    if (bm_test(f)) {
                        bm_clear(f);
                        g_free_frames++;
                    }
                }
            }
            addr += e->size + 4;   /* `size` does not count itself */
        }
    }

    /* reserve the low 1 MiB (BIOS/legacy) and the body's own loaded image. */
    reserve_range(0, 0x100000u);
    reserve_range(0x100000u, (uintptr_t)kernel_end);

    /* C7 P3b-4c: reserve every multiboot module (the sealed image) so the program is never handed a
     * frame the module is standing on. mbi->mods_addr + the descriptors are in low memory (the loader's),
     * reachable on the boot scaffold's identity map; mod_start/mod_end are physical. A non-interp build
     * has no module (mods_count == 0) — a no-op. reserve_range clamps to MAX_FRAMES. */
    if ((mbi->flags & MB_FLAG_MODS) && mbi->mods_count > 0) {
        const struct mb_mod *mods = (const struct mb_mod *)(uintptr_t)mbi->mods_addr;
        for (uint32_t i = 0; i < mbi->mods_count; i++) {
            reserve_range(mods[i].mod_start, mods[i].mod_end);
        }
    }
}

uint32_t pmm_alloc(void) {
    for (uint32_t f = 0; f < MAX_FRAMES; f++) {
        if (!bm_test(f)) {
            bm_set(f);
            g_free_frames--;
            return f << 12;
        }
    }
    return 0;   /* out of frames */
}

void pmm_free(uint32_t frame) {
    uint32_t f = frame >> 12;
    if (f < MAX_FRAMES && bm_test(f)) {
        bm_clear(f);
        g_free_frames++;
    }
}

uint32_t pmm_free_count(void) {
    return g_free_frames;
}

uint64_t pmm_reported_max(void) {
    return g_reported_max_phys;
}
