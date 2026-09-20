/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — virtual memory / paging (C7 P3b-4m; RE-LAID-OUT to the higher-half model, L20).
 *
 * FOUR-LEVEL PAGING (PML4 -> PDPT -> PD -> PT) with 4 KiB pages. The trampoline (boot.S) got the body
 * into long mode on a bring-up SCAFFOLD identity map; vmm_init builds and installs the body's OWN
 * four-level tables and loads CR3, ABANDONING the scaffold. From here every mapping self-check runs on
 * the body's tables, never the scaffold's.
 *
 * THE HIGHER-HALF LAYOUT (C7 P3b-4m, L20 — the hosted program owns the standard low range). The body no
 * longer identity-maps the low gigabyte as its own supervisor memory. Instead:
 *   - it keeps a SUPERVISOR IDENTITY map ONLY for [0, CANONICAL_BASE) (two 2 MiB huge pages: the body's
 *     image at 1 MiB and low memory) — the body's code, stack, heap, bitmap and page structures keep
 *     working the instant CR3 switches, because they all live beneath the canonical base;
 *   - it installs its OWN DIRECT MAP of physical memory in the HIGHER HALF (DIRECT_MAP_BASE + phys,
 *     PML4[256]) covering [0, DIRECT_MAP_MAX) with 2 MiB huge pages — the body reaches every frame it
 *     touches (page tables, PMM frames, the enclosure's copies) through this, via phys_to_virt();
 *   - it WITHDRAWS the supervisor identity map from the program's range (CANONICAL_BASE .. 1 GiB), so an
 *     ordinary program's canonical base (0x400000) is user-mappable (vmm_map_user), which it could not
 *     be while that range was a supervisor huge page.
 *
 * The static tables themselves live in the body's image (beneath CANONICAL_BASE, so their link-time
 * address == their physical address, identity-reachable) — the values written into page-table entries
 * and CR3 are physical addresses taken as &table. A table REACHED during a walk is read through the
 * direct map (phys_to_virt), which aliases the same physical frame.
 *
 * vmm_map installs one 4 KiB page by walking the four levels, taking a fresh PMM frame for any missing
 * intermediate table (reached through the direct map); it writes the PTE and flushes the TLB for that
 * page. The self-check drives VA 1 GiB (outside the retained identity, so the walk genuinely allocates).
 */
#include "body.h"
#include "enclosure.h"   /* C7 P3b-6c (i): the per-enclosure map interface is declared beside the enclosure
                          * that holds each map handle (vmm_map_new / vmm_switch / vmm_query_in / ...). */

#define PAGE_PRESENT 0x1ull
#define PAGE_RW      0x2ull
#define PAGE_USER    0x4ull                       /* ring-3 access permitted (C7 P3b-4a — the worker) */
#define PAGE_PS      0x80ull                     /* 2 MiB huge page (in a PD entry)                */
#define ADDR_MASK    0x000FFFFFFFFFF000ull       /* the 52-bit physical address field of an entry  */

#define HUGE_2M      (2ull * 1024ull * 1024ull)  /* a 2 MiB huge page                              */

/* The body's OWN four-level tables: 512 entries each, 8-byte entries, 4 KiB-aligned.
 *   pml4[0]   -> pdpt_low   : the low canonical half (the retained identity + on-demand user/supervisor
 *                             mappings for the program's range)
 *   pml4[256] -> pdpt_high  : the body's own direct map of physical memory (the higher half)
 *   pdpt_low[0]   -> pd_low       : the low gigabyte's PD — [0, CANONICAL_BASE) as retained identity huge
 *                                   pages, the rest on-demand (the program's user pages)
 *   pdpt_high[0]  -> pd_directmap : [0, DIRECT_MAP_MAX) of physical memory as 2 MiB huge pages */
static uint64_t pml4[512]         __attribute__((aligned(4096)));
static uint64_t pdpt_low[512]     __attribute__((aligned(4096)));
static uint64_t pd_low[512]       __attribute__((aligned(4096)));
static uint64_t pdpt_high[512]    __attribute__((aligned(4096)));
static uint64_t pd_directmap[512] __attribute__((aligned(4096)));

/* the PML4 slot the higher-half direct map lands in: (DIRECT_MAP_BASE >> 39) & 0x1FF == 256. */
#define DIRECT_MAP_PML4_INDEX ((int)((DIRECT_MAP_BASE >> 39) & 0x1FFull))

/* C7 P3b-6c (i) — THE ACTIVE USER-MAP ROOT. The PML4 vmm_map_user edits. It defaults to the body's OWN
 * static pml4 (the boot map), so a single-enclosure boot is byte-identical to today; vmm_switch re-points
 * it (and CR3) at a resident enclosure's OWN map, so the ELF loader's vmm_map_user places that enclosure's
 * user pages in ITS OWN page-table hierarchy — two enclosures at base 0x400000 land on distinct frames with
 * no aliasing (L20). The supervisor walkers (vmm_map / vmm_query / vmm_unmap) keep reading the boot map;
 * per-enclosure reads go through vmm_query_in. */
static uint64_t *g_umap = pml4;

void vmm_init(void) {
    for (int i = 0; i < 512; i++) {
        pml4[i] = 0;
        pdpt_low[i] = 0;
        pd_low[i] = 0;
        pdpt_high[i] = 0;
        pd_directmap[i] = 0;
    }

    /* THE RETAINED IDENTITY — [0, CANONICAL_BASE) only (two 2 MiB huge pages): the body's image at 1 MiB
     * and low memory stay the body's, reachable at their physical address the instant CR3 switches. The
     * program's range (CANONICAL_BASE up) is left OUT of the supervisor identity map — withdrawn (L20). */
    for (uint32_t i = 0; i < (uint32_t)(CANONICAL_BASE / HUGE_2M); i++) {
        pd_low[i] = ((uint64_t)i * HUGE_2M) | PAGE_PRESENT | PAGE_RW | PAGE_PS;
    }
    pdpt_low[0] = ((uint64_t)(uintptr_t)&pd_low[0]) | PAGE_PRESENT | PAGE_RW;
    pml4[0]     = ((uint64_t)(uintptr_t)&pdpt_low[0]) | PAGE_PRESENT | PAGE_RW;

#ifdef PLANT_IDENTITY_NOT_WITHDRAWN
    /* A1/A2 near-miss (a check that cannot fail is not a check): re-install the supervisor identity map
     * over the WHOLE low gigabyte, as the body did before the re-layout — so the program's range is a
     * supervisor huge page again. Then 0x400000 is un-user-mappable (CHECK USER-BASE reds) and the
     * withdrawal check sees a supervisor identity huge page over the program's range (CHECK LAYOUT reds). */
    for (uint32_t i = (uint32_t)(CANONICAL_BASE / HUGE_2M); i < 512; i++) {
        pd_low[i] = ((uint64_t)i * HUGE_2M) | PAGE_PRESENT | PAGE_RW | PAGE_PS;
    }
#endif

    /* THE BODY'S OWN DIRECT MAP — physical memory in the higher half (DIRECT_MAP_BASE + phys), covering
     * [0, DIRECT_MAP_MAX) with 2 MiB huge pages. Every frame the body touches after this is reached here
     * (phys_to_virt), never at its withdrawn identity address. */
    for (uint32_t i = 0; i < (uint32_t)(DIRECT_MAP_MAX / HUGE_2M); i++) {
        pd_directmap[i] = ((uint64_t)i * HUGE_2M) | PAGE_PRESENT | PAGE_RW | PAGE_PS;
    }
    pdpt_high[0]                  = ((uint64_t)(uintptr_t)&pd_directmap[0]) | PAGE_PRESENT | PAGE_RW;
    pml4[DIRECT_MAP_PML4_INDEX]   = ((uint64_t)(uintptr_t)&pdpt_high[0])    | PAGE_PRESENT | PAGE_RW;

    /* install the body's own PML4 — from here the scaffold is abandoned. */
    __asm__ volatile("mov %0, %%cr3" : : "r"((uint64_t)(uintptr_t)&pml4[0]) : "memory");
}

/* 1 iff NO supervisor identity huge page covers the program's range [CANONICAL_BASE, 1 GiB) — i.e. the
 * identity map is withdrawn there. A user PT link (USER set, the program's own mapping) is not an
 * identity huge page and does not count. The A1/A2 plant re-installs the huge pages, redding this. */
int vmm_program_range_identity_withdrawn(void) {
    for (int i = (int)(CANONICAL_BASE / HUGE_2M); i < 512; i++) {
        if ((pd_low[i] & PAGE_PRESENT) && (pd_low[i] & PAGE_PS) && !(pd_low[i] & PAGE_USER)) {
            return 0;   /* a supervisor identity huge page still owns the program's range */
        }
    }
    return 1;
}

/* walk to (and, if `create`, allocate) the next-level table an entry points at; return its address
 * THROUGH THE DIRECT MAP (phys_to_virt), or 0 on OOM / a huge-page collision. */
static uint64_t *next_table(uint64_t *entry, int create) {
    if (*entry & PAGE_PS) {
        return 0;                                 /* a 2 MiB huge-page region — not 4 KiB-mappable */
    }
    if (!(*entry & PAGE_PRESENT)) {
        if (!create) {
            return 0;
        }
        uint32_t frame = pmm_alloc();
        if (frame == 0) {
            return 0;                             /* out of frames for a new table                 */
        }
        uint64_t *t = (uint64_t *)phys_to_virt(frame);   /* the fresh frame, through the direct map */
        for (int i = 0; i < 512; i++) {
            t[i] = 0;
        }
        *entry = ((uint64_t)frame) | PAGE_PRESENT | PAGE_RW;
    }
    return (uint64_t *)phys_to_virt(*entry & ADDR_MASK);
}

int vmm_map(uint64_t virt, uint64_t phys) {
    uint64_t i4 = (virt >> 39) & 0x1FF;
    uint64_t i3 = (virt >> 30) & 0x1FF;
    uint64_t i2 = (virt >> 21) & 0x1FF;
    uint64_t i1 = (virt >> 12) & 0x1FF;

    uint64_t *pdpt_t = next_table(&pml4[i4], 1);
    if (!pdpt_t) { return -1; }
    uint64_t *pd_t = next_table(&pdpt_t[i3], 1);
    if (!pd_t) { return -1; }
    uint64_t *pt_t = next_table(&pd_t[i2], 1);
    if (!pt_t) { return -1; }

    pt_t[i1] = (phys & ADDR_MASK) | PAGE_PRESENT | PAGE_RW;
    __asm__ volatile("invlpg (%0)" : : "r"(virt) : "memory");
    return 0;
}

/* Like next_table, but for a USER mapping (C7 P3b-4a): a created intermediate PERMITS ring 3, and an
 * existing intermediate is PROMOTED to permit it. This is safe — a page is user-accessible only when
 * USER is set at EVERY level AND in the PTE, so promoting the low PD (pd_low), which also carries the
 * retained identity map for [0, CANONICAL_BASE) as supervisor huge pages (USER == 0), never exposes the
 * body's image or low memory (those PDEs keep USER == 0; the PTE gates each page). The program's range
 * (CANONICAL_BASE up) has no identity huge page after the withdrawal, so a user PT installs there. */
static uint64_t *next_table_user(uint64_t *entry, int create) {
    if (*entry & PAGE_PS) {
        return 0;
    }
    if (!(*entry & PAGE_PRESENT)) {
        if (!create) {
            return 0;
        }
        uint32_t frame = pmm_alloc();
        if (frame == 0) {
            return 0;
        }
        uint64_t *t = (uint64_t *)phys_to_virt(frame);   /* the fresh frame, through the direct map */
        for (int i = 0; i < 512; i++) {
            t[i] = 0;
        }
        *entry = ((uint64_t)frame) | PAGE_PRESENT | PAGE_RW | PAGE_USER;
    } else {
        *entry |= PAGE_USER;                      /* promote so ring 3 may reach the PTE below */
    }
    return (uint64_t *)phys_to_virt(*entry & ADDR_MASK);
}

/* Map one 4 KiB page as a USER page (ring-3 readable/writable) — the surface the ELF64 loader drives to
 * place an enclosed worker's segments and stack (C7 P3b-4a). The PTE carries USER; vmm_map (supervisor)
 * does not, so a body page stays out of the worker's reach. 0 ok, -1 if no table frame. */
int vmm_map_user(uint64_t virt, uint64_t phys) {
    uint64_t i4 = (virt >> 39) & 0x1FF;
    uint64_t i3 = (virt >> 30) & 0x1FF;
    uint64_t i2 = (virt >> 21) & 0x1FF;
    uint64_t i1 = (virt >> 12) & 0x1FF;

    /* walk the ACTIVE user-map root (g_umap): the boot map by default, or the resident enclosure's own
     * map after vmm_switch — so an enclosure's user pages land in ITS OWN hierarchy (C7 P3b-6c i, L20). */
    uint64_t *pdpt_t = next_table_user(&g_umap[i4], 1);
    if (!pdpt_t) { return -1; }
    uint64_t *pd_t = next_table_user(&pdpt_t[i3], 1);
    if (!pd_t) { return -1; }
    uint64_t *pt_t = next_table_user(&pd_t[i2], 1);
    if (!pt_t) { return -1; }

    pt_t[i1] = (phys & ADDR_MASK) | PAGE_PRESENT | PAGE_RW | PAGE_USER;
    __asm__ volatile("invlpg (%0)" : : "r"(virt) : "memory");
    return 0;
}

void vmm_unmap(uint64_t virt) {
    uint64_t i4 = (virt >> 39) & 0x1FF;
    uint64_t i3 = (virt >> 30) & 0x1FF;
    uint64_t i2 = (virt >> 21) & 0x1FF;
    uint64_t i1 = (virt >> 12) & 0x1FF;

    uint64_t *pdpt_t = next_table(&pml4[i4], 0);
    if (!pdpt_t) { return; }
    uint64_t *pd_t = next_table(&pdpt_t[i3], 0);
    if (!pd_t) { return; }
    uint64_t *pt_t = next_table(&pd_t[i2], 0);
    if (!pt_t) { return; }

    pt_t[i1] = 0;
    __asm__ volatile("invlpg (%0)" : : "r"(virt) : "memory");
}

/* C7 P3b-6c (iii) A4 — UNMAP one page IN the hierarchy rooted at `cr3` (the ACTIVE enclosure's map), the
 * write-side twin of vmm_query_in. serve.c's unmap acts under the bridge must clear the PTE in the WORKER's
 * OWN map (B), not the boot map, so a reclaimed frame is no longer reachable through the enclosure that
 * owned it (no stale mapping to a freed frame across repeated relays). Walks through the direct map, so it
 * may run while any map is active. A leaf huge page or an absent level is left untouched. Compiled ONLY for
 * the socket-act build so every other body (the shipped single-enclosure body included) is byte-identical. */
#ifdef SOCKET_ACT
void vmm_unmap_in(uint64_t cr3, uint64_t virt) {
    uint64_t *root = (uint64_t *)phys_to_virt(cr3);
    uint64_t i4 = (virt >> 39) & 0x1FF;
    uint64_t i3 = (virt >> 30) & 0x1FF;
    uint64_t i2 = (virt >> 21) & 0x1FF;
    uint64_t i1 = (virt >> 12) & 0x1FF;
    if (!(root[i4] & PAGE_PRESENT) || (root[i4] & PAGE_PS)) { return; }
    uint64_t *pdpt_t = (uint64_t *)phys_to_virt(root[i4] & ADDR_MASK);
    if (!(pdpt_t[i3] & PAGE_PRESENT) || (pdpt_t[i3] & PAGE_PS)) { return; }
    uint64_t *pd_t = (uint64_t *)phys_to_virt(pdpt_t[i3] & ADDR_MASK);
    if (!(pd_t[i2] & PAGE_PRESENT) || (pd_t[i2] & PAGE_PS)) { return; }
    uint64_t *pt_t = (uint64_t *)phys_to_virt(pd_t[i2] & ADDR_MASK);
    pt_t[i1] = 0;
    __asm__ volatile("invlpg (%0)" : : "r"(virt) : "memory");
}
#endif /* SOCKET_ACT */

/* Read the PTE mapping `virt` (0 if any level is absent or the region is a huge page) — a read-only
 * walk through the direct map. The layout self-check reads it to prove the canonical base is mapped
 * PRESENT + USER at the expected frame. */
uint64_t vmm_query(uint64_t virt) {
    uint64_t i4 = (virt >> 39) & 0x1FF;
    uint64_t i3 = (virt >> 30) & 0x1FF;
    uint64_t i2 = (virt >> 21) & 0x1FF;
    uint64_t i1 = (virt >> 12) & 0x1FF;

    uint64_t *pdpt_t = next_table(&pml4[i4], 0);
    if (!pdpt_t) { return 0; }
    uint64_t *pd_t = next_table(&pdpt_t[i3], 0);
    if (!pd_t) { return 0; }
    uint64_t *pt_t = next_table(&pd_t[i2], 0);
    if (!pt_t) { return 0; }
    return pt_t[i1];
}

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-6c (i) — PER-ENCLOSURE ADDRESS MAPS (design/54 §5 L20/L18, §9 Q11/I3). Each resident enclosure
 * gets its OWN four-level page-table hierarchy. The hierarchies SHARE the kernel half — the low identity
 * [0, CANONICAL_BASE) (the body's image, so the #PF handler and every body reach hold under any map) and
 * the higher-half direct map (PML4[256], the SAME pdpt_high, so a frame reads identically the instant CR3
 * changes) — and each has a PRIVATE user half (the program's range, CANONICAL_BASE up). Two enclosures at
 * base 0x400000 map distinct physical frames with no aliasing; the map is swapped at the coroutine hand-off
 * (vmm_switch). The body stays ONE ring-0 process — this is NOT fork (Q11): the user half is per-enclosure,
 * which makes memory MORE private, and no map is shared for writing.
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/

/* the boot map's CR3 (the body's own static pml4 — a link-time address == its physical address, beneath
 * CANONICAL_BASE and identity-reachable). vmm_init already loaded this at boot. */
uint64_t vmm_boot_cr3(void) { return (uint64_t)(uintptr_t)&pml4[0]; }

/* Allocate a fresh per-enclosure hierarchy that SHARES the kernel half and has an EMPTY private user half.
 * Built THROUGH the direct map (phys_to_virt), so it may be built while any map is active. Returns the new
 * hierarchy's CR3 (its pml4 physical address), or 0 on OOM (three frames: pml4, pdpt_low, pd_low). */
uint64_t vmm_map_new(void) {
    uint32_t pml4_f = pmm_alloc();
    if (pml4_f == 0) { return 0; }
    uint32_t pdpt_lo_f = pmm_alloc();
    if (pdpt_lo_f == 0) { pmm_free(pml4_f); return 0; }
    uint32_t pd_lo_f = pmm_alloc();
    if (pd_lo_f == 0) { pmm_free(pml4_f); pmm_free(pdpt_lo_f); return 0; }

    uint64_t *np    = (uint64_t *)phys_to_virt((uint64_t)pml4_f);
    uint64_t *npdpt = (uint64_t *)phys_to_virt((uint64_t)pdpt_lo_f);
    uint64_t *npd   = (uint64_t *)phys_to_virt((uint64_t)pd_lo_f);
    for (int i = 0; i < 512; i++) { np[i] = 0; npdpt[i] = 0; npd[i] = 0; }

    /* THE SHARED LOW IDENTITY [0, CANONICAL_BASE): copy the boot map's identity huge-page entries BY VALUE —
     * the same physical targets, byte-identical, so the body's image, stack, heap and page structures are
     * reachable identically the instant CR3 switches to this map (L20). These are leaf huge pages, so
     * copying the entry IS sharing (no lower table exists). The program's range (pd_low[K..511]) stays
     * empty — the enclosure's PRIVATE user half, filled by vmm_map_user after vmm_switch. */
    for (int i = 0; i < (int)(CANONICAL_BASE / HUGE_2M); i++) {
        npd[i] = pd_low[i];
    }
    npdpt[0] = ((uint64_t)pd_lo_f)   | PAGE_PRESENT | PAGE_RW;
    np[0]    = ((uint64_t)pdpt_lo_f) | PAGE_PRESENT | PAGE_RW;

    /* THE SHARED HIGHER-HALF DIRECT MAP: copy the boot map's PML4[256] entry — it points at the SAME
     * pdpt_high subtree, so this map and every map reach all physical memory through ONE identical direct
     * map (L20). This is the kernel half; it is NEVER made per-enclosure. */
#ifndef PLANT_MAPS_NO_KERNEL_HALF
    np[DIRECT_MAP_PML4_INDEX] = pml4[DIRECT_MAP_PML4_INDEX];
#else
    /* A4 PLANT (a map missing the kernel higher half): leave PML4[256] absent. The body faults on its own
     * direct map the instant it walks or reaches a frame under this map after a swap (a real #PF -> EXC +
     * halt) — a check that cannot fail is not a check (L19). */
    (void)0;
#endif
    return (uint64_t)pml4_f;   /* the new map's CR3 */
}

/* THE MAP-SWITCH (the coroutine hand-off's primitive): load `cr3` (from vmm_map_new / vmm_boot_cr3) into
 * CR3 AND point the active user-map root there, so a later vmm_map_user edits THIS map. The kernel half is
 * shared, so the body's code, stack and direct map keep working across the swap. */
void vmm_switch(uint64_t cr3) {
    g_umap = (uint64_t *)phys_to_virt(cr3);
    __asm__ volatile("mov %0, %%cr3" : : "r"(cr3) : "memory");
}

/* Read the PTE mapping `virt` IN the hierarchy rooted at `cr3` (0 if any level is absent or a huge page) —
 * a read-only walk through the direct map, independent of which map is active. floor_maps_run reads it to
 * prove two maps' user pages at the same virtual base land on DISTINCT physical frames (no aliasing, A1). */
uint64_t vmm_query_in(uint64_t cr3, uint64_t virt) {
    uint64_t *root = (uint64_t *)phys_to_virt(cr3);
    uint64_t i4 = (virt >> 39) & 0x1FF;
    uint64_t i3 = (virt >> 30) & 0x1FF;
    uint64_t i2 = (virt >> 21) & 0x1FF;
    uint64_t i1 = (virt >> 12) & 0x1FF;
    if (!(root[i4] & PAGE_PRESENT) || (root[i4] & PAGE_PS)) { return 0; }
    uint64_t *pdpt_t = (uint64_t *)phys_to_virt(root[i4] & ADDR_MASK);
    if (!(pdpt_t[i3] & PAGE_PRESENT) || (pdpt_t[i3] & PAGE_PS)) { return 0; }
    uint64_t *pd_t = (uint64_t *)phys_to_virt(pdpt_t[i3] & ADDR_MASK);
    if (!(pd_t[i2] & PAGE_PRESENT) || (pd_t[i2] & PAGE_PS)) { return 0; }
    uint64_t *pt_t = (uint64_t *)phys_to_virt(pd_t[i2] & ADDR_MASK);
    return pt_t[i1];
}

/* 1 iff the hierarchy rooted at `cr3` carries the kernel half BYTE-IDENTICAL to the boot map: the
 * higher-half direct map (PML4[256] entry equal — the SAME pdpt_high) AND the low identity
 * [0, CANONICAL_BASE) (each identity huge-page entry equal). floor_maps_run reads it for A4 (L20 — the
 * kernel half is shared, only the user half is per-enclosure). */
int vmm_map_kernel_half_matches(uint64_t cr3) {
    uint64_t *root = (uint64_t *)phys_to_virt(cr3);
    if (root[DIRECT_MAP_PML4_INDEX] != pml4[DIRECT_MAP_PML4_INDEX]) { return 0; }
    if (!(root[0] & PAGE_PRESENT) || (root[0] & PAGE_PS)) { return 0; }
    uint64_t *pdpt_t = (uint64_t *)phys_to_virt(root[0] & ADDR_MASK);
    if (!(pdpt_t[0] & PAGE_PRESENT) || (pdpt_t[0] & PAGE_PS)) { return 0; }
    uint64_t *pd_t = (uint64_t *)phys_to_virt(pdpt_t[0] & ADDR_MASK);
    for (int i = 0; i < (int)(CANONICAL_BASE / HUGE_2M); i++) {
        if (pd_t[i] != pd_low[i]) { return 0; }
    }
    return 1;
}
