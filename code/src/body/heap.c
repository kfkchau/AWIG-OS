/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the kernel heap (C7 P3b-1; the spike's Q-B, final third).
 *
 * A first-fit free-list heap over the body's own region (a static, page-aligned area inside the
 * image, so it is identity-mapped and reachable the instant paging turns on). Each block carries
 * a header; kmalloc splits a large-enough free block, kfree marks a block free and coalesces it
 * with the next free neighbour. This slice keeps the heap over a static region for read-whole
 * clarity; re-homing the heap onto PMM-backed, VMM-mapped frames is a later P3b row, not this one
 * (the honest cap is stated in the plan, §8). The self-check exercises alloc / write / read-back
 * / free and a two-block non-overlap.
 */
#include "body.h"

#define HEAP_SIZE (256u * 1024u)

static uint8_t heap_area[HEAP_SIZE] __attribute__((aligned(16)));

typedef struct block {
    uint32_t      size;   /* usable bytes after this header */
    int           free;
    struct block *next;
} block_t;

static block_t *heap_head;

void heap_init(void) {
    heap_head       = (block_t *)heap_area;
    heap_head->size = HEAP_SIZE - sizeof(block_t);
    heap_head->free = 1;
    heap_head->next = 0;
}

void *kmalloc(uint32_t size) {
    size = (size + 15u) & ~15u;   /* 16-byte alignment */

#ifdef PLANT_HEAP_OVERLAP
    /* A5/A2 near-miss: a faulted heap that hands the SAME block every time — two live
     * allocations then overlap, and the self-check's non-overlap test must catch it. */
    return heap_area + sizeof(block_t);
#endif

    for (block_t *b = heap_head; b; b = b->next) {
        if (b->free && b->size >= size) {
            if (b->size >= size + sizeof(block_t) + 16u) {
                block_t *nb = (block_t *)((uint8_t *)b + sizeof(block_t) + size);
                nb->size = b->size - size - sizeof(block_t);
                nb->free = 1;
                nb->next = b->next;
                b->size  = size;
                b->next  = nb;
            }
            b->free = 0;
            return (uint8_t *)b + sizeof(block_t);
        }
    }
    return 0;   /* out of heap */
}

void kfree(void *p) {
    if (!p) {
        return;
    }
    block_t *b = (block_t *)((uint8_t *)p - sizeof(block_t));
    b->free = 1;
    if (b->next && b->next->free) {   /* coalesce forward */
        b->size += sizeof(block_t) + b->next->size;
        b->next  = b->next->next;
    }
}
