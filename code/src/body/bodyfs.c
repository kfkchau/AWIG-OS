/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — BODYFS: the body's own filesystem on its own disk (C7 P3b-2; Q-E disk, part 2).
 *
 * A small bespoke block layout the estate's record maps onto directly (the Q-E "bespoke block
 * layout" option — a simple FS is far larger and buys nothing the record needs). A superblock, a
 * fixed directory of 64-byte entries, and a data region. On it the body performs the five record
 * acts on the metal. Hand-written and read whole (I3): no opaque code in the signed base.
 *
 * THE RECORD IS APPEND-ONLY BY CONSTRUCTION (archi :4019). fs_record_write_at is the ONE write
 * primitive for the record and it REFUSES any offset but the current tail — there is no truncate
 * and no in-place overwrite path. fs_record_append is that primitive at the tail. 'remove' refuses
 * the record and applies only to blobs. This is the body-level form of the append-only record law.
 *
 * Every disk touch is a call into ata.c (the body's own block driver, beneath the seam), under the
 * nested qemu's virtual disk; nothing here reaches the host kernel (L11).
 */
#include "disk.h"

/* ── The four freestanding memory primitives (gcc -ffreestanding may emit calls to these; provide
 * them so the -nostdlib link resolves, and use them here). Read whole; no libc linked. ──────────*/
void *memset(void *d, int c, size_t n) {
    uint8_t *p = (uint8_t *)d;
    while (n--) { *p++ = (uint8_t)c; }
    return d;
}
void *memcpy(void *d, const void *s, size_t n) {
    uint8_t *pd = (uint8_t *)d; const uint8_t *ps = (const uint8_t *)s;
    while (n--) { *pd++ = *ps++; }
    return d;
}
void *memmove(void *d, const void *s, size_t n) {
    uint8_t *pd = (uint8_t *)d; const uint8_t *ps = (const uint8_t *)s;
    if (pd < ps) { while (n--) { *pd++ = *ps++; } }
    else { pd += n; ps += n; while (n--) { *--pd = *--ps; } }
    return d;
}
int memcmp(const void *a, const void *b, size_t n) {
    const uint8_t *pa = (const uint8_t *)a, *pb = (const uint8_t *)b;
    while (n--) { if (*pa != *pb) { return (int)*pa - (int)*pb; } pa++; pb++; }
    return 0;
}

/* ── Small public helpers (declared in disk.h) ────────────────────────────────────────────────*/
int mem_eq(const void *a, const void *b, uint32_t n) {
    return memcmp(a, b, n) == 0;
}
uint32_t str_len(const char *s) {
    uint32_t n = 0; while (s[n]) { n++; } return n;
}
int fs_name_eq(const char *field, const char *id) {
    uint32_t i = 0;
    for (; i < BFS_NAME_MAX && id[i]; i++) { if (field[i] != id[i]) { return 0; } }
    if (i < BFS_NAME_MAX) { return field[i] == '\0'; }  /* id ended within the field — field must too */
    return 1;                                    /* id filled the whole field — full match */
}
static void name_set(char *field, const char *id) {
    uint32_t i = 0;
    for (; i < BFS_NAME_MAX && id[i]; i++) { field[i] = id[i]; }
    for (; i < BFS_NAME_MAX; i++) { field[i] = '\0'; }
}

/* ── CRC-32 (IEEE, reflected — byte-identical to Python's zlib.crc32) ─────────────────────────*/
uint32_t crc32_begin(void) { return 0xFFFFFFFFu; }
uint32_t crc32_feed(uint32_t crc, const uint8_t *data, uint32_t n) {
    for (uint32_t i = 0; i < n; i++) {
        crc ^= data[i];
        for (int k = 0; k < 8; k++) {
            uint32_t mask = (uint32_t)(-(int32_t)(crc & 1u));
            crc = (crc >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return crc;
}
uint32_t crc32_final(uint32_t crc) { return crc ^ 0xFFFFFFFFu; }

/* ── The mounted filesystem state ─────────────────────────────────────────────────────────────*/
static struct bfs_super g_super;
static uint8_t g_dir[BFS_DIR_SECTORS * SECTOR_SIZE];
static uint8_t g_sec[SECTOR_SIZE];

static struct bfs_entry *entry_at(uint32_t i) {
    return (struct bfs_entry *)(g_dir + i * BFS_ENTRY_SIZE);
}

int fs_mount(void) {
    if (ata_read_sector(0, &g_super) != 0) { return -1; }
    if (memcmp(g_super.magic, BFS_MAGIC, 8) != 0) { return -1; }
    if (g_super.version != BFS_VERSION) { return -1; }
    if (g_super.dir_sectors > BFS_DIR_SECTORS) { return -1; }
    for (uint32_t s = 0; s < g_super.dir_sectors; s++) {
        if (ata_read_sector(g_super.dir_start + s, g_dir + s * SECTOR_SIZE) != 0) { return -1; }
    }
    return 0;
}

struct bfs_entry *fs_find(const char *name) {
    for (uint32_t i = 0; i < BFS_MAX_ENTRIES; i++) {
        struct bfs_entry *e = entry_at(i);
        if (e->present && fs_name_eq(e->name, name)) { return e; }
    }
    return 0;
}

/* C7-MAINT-5B (A2) — the directory TABLE INDEX of a present entry by name, or -1. The table slot is a
 * STABLE per-file identity: unique across every entry (directories included, whose start_sector is 0
 * and so is not itself unique), and fixed for an entry's life (an append relocates its DATA but never
 * its table slot). serve.c derives one st_ino per FILE from this so a path-stat, an fstat through any
 * open handle, and a re-open all answer the SAME number, and two different files never share one. */
int fs_name_index(const char *name) {
    for (uint32_t i = 0; i < BFS_MAX_ENTRIES; i++) {
        struct bfs_entry *e = entry_at(i);
        if (e->present && fs_name_eq(e->name, name)) { return (int)i; }
    }
    return -1;
}

static struct bfs_entry *fs_alloc_entry(void) {
    for (uint32_t i = 0; i < BFS_MAX_ENTRIES; i++) {
        struct bfs_entry *e = entry_at(i);
        if (!e->present) { return e; }
    }
    return 0;
}

static void persist_entry(struct bfs_entry *e) {
    uint32_t i = (uint32_t)((uint8_t *)e - g_dir) / BFS_ENTRY_SIZE;
    uint32_t sec = g_super.dir_start + i / BFS_ENTRIES_PER_SECTOR;
    ata_write_sector(sec, g_dir + (i / BFS_ENTRIES_PER_SECTOR) * SECTOR_SIZE);
    ata_flush();
}

static void persist_super(void) {
    ata_write_sector(0, &g_super);
    ata_flush();
}

/* ── record-pen: the append-only record file ──────────────────────────────────────────────────*/
int fs_record_write_at(uint32_t off, const uint8_t *payload, uint32_t n, uint32_t *out_start_sector) {
    struct bfs_entry *e = fs_find("record");
    if (!e || e->type != FT_RECORD) { return -1; }

    /* APPEND-ONLY BY CONSTRUCTION: the record grows only at its tail. A write anywhere else is
     * REFUSED — the body-level sole-appender leash. The plant disables the guard so a planted
     * overwrite SUCCEEDS and the self-check catches it (A2 / the by-name precision). */
#ifndef PLANT_RECORD_OVERWRITE_ALLOWED
    if (off != e->length) { return -1; }
#endif
    if (off % SECTOR_SIZE != 0) { return -1; }              /* records are sector-granular */

    uint32_t span = (sizeof(struct bfs_rechdr) + n + SECTOR_SIZE - 1) / SECTOR_SIZE;
    uint32_t start = e->start_sector + off / SECTOR_SIZE;
    if (off / SECTOR_SIZE + span > e->capacity_sectors) { return -1; }   /* out of record space */

    struct bfs_rechdr hdr;
    hdr.magic = RECK_MAGIC; hdr.byte_len = n; hdr.seq = off / SECTOR_SIZE; hdr.reserved = 0;
    for (uint32_t s = 0; s < span; s++) {
        memset(g_sec, 0, SECTOR_SIZE);
        uint32_t hdr_bytes = (s == 0) ? (uint32_t)sizeof(hdr) : 0u;
        if (s == 0) { memcpy(g_sec, &hdr, sizeof(hdr)); }
        uint32_t src_off = (s == 0) ? 0u : (s * SECTOR_SIZE - (uint32_t)sizeof(hdr));
        uint32_t remain = (src_off < n) ? (n - src_off) : 0u;
        uint32_t room = SECTOR_SIZE - hdr_bytes;
        uint32_t copied = (remain < room) ? remain : room;
        if (copied) { memcpy(g_sec + hdr_bytes, payload + src_off, copied); }
#ifdef PLANT_RECORD_READBACK_WRONG
        /* corrupt one payload byte on write, so a faithful read-back differs (A2). */
        if (s == 0 && n > 0) { g_sec[sizeof(hdr)] ^= 0xFFu; }
#endif
        if (ata_write_sector(start + s, g_sec) != 0) { return -1; }
    }
    ata_flush();

    if (off == e->length) {                                 /* only a tail append advances length */
        e->length += span * SECTOR_SIZE;
        persist_entry(e);
    }
    if (out_start_sector) { *out_start_sector = start; }
    return 0;
}

int fs_record_append(const uint8_t *payload, uint32_t n, uint32_t *out_start_sector) {
    struct bfs_entry *e = fs_find("record");
    if (!e) { return -1; }
    return fs_record_write_at(e->length, payload, n, out_start_sector);
}

int fs_record_read(uint32_t start_sector, uint8_t *out, uint32_t max, uint32_t *out_len) {
    if (ata_read_sector(start_sector, g_sec) != 0) { return -1; }
    struct bfs_rechdr hdr;
    memcpy(&hdr, g_sec, sizeof(hdr));
    if (hdr.magic != RECK_MAGIC) { return -1; }
    uint32_t n = hdr.byte_len;
    if (n > max) { return -1; }
    uint32_t room0 = SECTOR_SIZE - (uint32_t)sizeof(hdr);
    uint32_t c0 = (n < room0) ? n : room0;
    memcpy(out, g_sec + sizeof(hdr), c0);
    uint32_t got = c0, s = 1;
    while (got < n) {
        if (ata_read_sector(start_sector + s, g_sec) != 0) { return -1; }
        uint32_t c = n - got; if (c > SECTOR_SIZE) { c = SECTOR_SIZE; }
        memcpy(out + got, g_sec, c); got += c; s++;
    }
    if (out_len) { *out_len = n; }
    return 0;
}

/* ── C7 P3b-5a-iv — the record pen at CALLER-NAMED names (design/54 §7 P3b-5a-iv; L21/L14/L19) ──────
 * Create the append-only record `name` (FT_NREC) on its FIRST stroke and append; on a PRESENT one,
 * extend at the tail. This matches the store's SOLE appender (host_seam.open_append = path.open("a"),
 * O_WRONLY|O_CREAT|O_APPEND): open("a") on an absent name CREATES the record, on a present one appends.
 * The bytes are stored RAW and CONTIGUOUS so a body-read reads back the exact concatenation via
 * fs_read_entry (a caller-named JSONL record read whole, not one append at a time — this is why FT_NREC
 * carries no per-append RECK header; the fixed FT_RECORD, read a stroke at a time via fs_record_read,
 * still does). APPEND-ONLY BY CONSTRUCTION: bytes are only added at the tail (off == length); there is
 * no in-place overwrite and no truncate path here — O_TRUNC is refused in serve.c (R1). The append
 * grows the entry IN PLACE when it is the allocator tail (next_free); otherwise its existing bytes are
 * relocated UNCHANGED to the tail with the needed capacity (append-only in content — the bytes never
 * change, they only move). The plant makes the by-construction append fallible (a check that cannot
 * fail is not a check). */
int fs_nrec_append(const char *name, const uint8_t *payload, uint32_t n, uint32_t *out_start_sector) {
    uint32_t nlen = 0;
    while (nlen <= BFS_NAME_MAX && name[nlen]) { nlen++; }
    if (nlen > BFS_NAME_MAX) { return -1; }         /* a name longer than the field: refused, never truncated */
    struct bfs_entry *e = fs_find(name);
#ifndef PLANT_RECONCILE_REFUSED
    /* C7-MAINT-5B — RECONCILE THE CREATE-EMPTY-THEN-APPEND IDIOM TO THE RECORD PEN. An UNSWAPPED,
     * zero-length FT_DURABLE (a staging file created empty by O_TRUNC-on-an-absent-name, never written and
     * never renamed) is ADOPTED into the record pen when it is opened for append: it becomes an FT_NREC in
     * place, so the append succeeds as Linux serves it. A NON-empty FT_DURABLE (a durable write in flight)
     * is NOT adopted, so the durable temp-then-swap stays distinct (A2); serve.c scopes the adoption to
     * /rec/tmp (L21/A3). No on-disk byte-format change — FT_NREC and FT_DURABLE are existing kinds. */
    if (e && e->type == FT_DURABLE && e->length == 0) {
        e->type = FT_NREC;                           /* the empty staging file becomes the append-only record */
        e->append_only = 1;
        persist_entry(e);                            /* the class change is durable */
    }
#endif                                               /* PLANT_RECONCILE_REFUSED: skip the adoption -> the foreign-class refusal below reds test_ep28e by EPERM (A1's plant, L19) */
    if (e && e->type != FT_NREC) { return -1; }     /* a present name of another class is not the record pen */
    if (!e) {                                        /* the FIRST stroke: create the append-only record */
        e = fs_alloc_entry();
        if (!e) { return -1; }
        name_set(e->name, name);
        e->type = FT_NREC; e->present = 1;
        e->start_sector = g_super.next_free;         /* claimed by the grow step below (capacity starts 0) */
        e->length = 0; e->capacity_sectors = 0; e->crc32 = 0;
        e->append_only = 1; e->reserved = 0;
    }

#ifdef PLANT_NREC_APPEND_OVERWRITES
    /* the fault: a stroke OVERWRITES at offset 0 rather than EXTENDING at the tail — the read-back-all
     * check sees only the last stroke, not the concatenation in order (A2 reds). */
    uint32_t off = 0;
    uint32_t new_len = n;
#else
    uint32_t off = e->length;                        /* append at the tail — the append-only leash */
    uint32_t new_len = e->length + n;
#endif

    uint32_t need = (new_len + SECTOR_SIZE - 1) / SECTOR_SIZE;
    if (need > e->capacity_sectors) {
        if (e->start_sector + e->capacity_sectors == g_super.next_free) {
            uint32_t extra = need - e->capacity_sectors;             /* the allocator tail: grow in place */
            if (g_super.next_free + extra > g_super.total_sectors) { return -1; }   /* out of data space */
            g_super.next_free += extra;
            e->capacity_sectors = need;
            persist_super();
        } else {                                                     /* not the tail: relocate to the tail */
            uint32_t new_start = g_super.next_free;
            if (new_start + need > g_super.total_sectors) { return -1; }   /* out of data space */
            uint32_t have = (e->length + SECTOR_SIZE - 1) / SECTOR_SIZE;
            for (uint32_t s = 0; s < have; s++) {                   /* the bytes move UNCHANGED (append-only) */
                if (ata_read_sector(e->start_sector + s, g_sec) != 0) { return -1; }
                if (ata_write_sector(new_start + s, g_sec) != 0) { return -1; }
            }
            g_super.next_free += need;
            e->start_sector = new_start;
            e->capacity_sectors = need;
            persist_super();
        }
    }

    /* write the new bytes at byte offset `off`: read-modify-write only the tail sector (preserve the
     * bytes already in it), then whole sectors. A fresh sector boundary (off % SECTOR_SIZE == 0) needs
     * no read — the prior bytes live in the prior sector. */
    uint32_t written = 0;
    while (written < n) {
        uint32_t sec = e->start_sector + off / SECTOR_SIZE;
        uint32_t in  = off % SECTOR_SIZE;
        uint32_t room = SECTOR_SIZE - in;
        uint32_t chunk = (n - written < room) ? (n - written) : room;
        if (in != 0) {
            if (ata_read_sector(sec, g_sec) != 0) { return -1; }   /* preserve the prefix already in the sector */
        } else {
            memset(g_sec, 0, SECTOR_SIZE);                         /* a fresh sector at a boundary */
        }
        memcpy(g_sec + in, payload + written, chunk);
        if (ata_write_sector(sec, g_sec) != 0) { return -1; }
        written += chunk;
        off += chunk;
    }
    ata_flush();

    e->length = new_len;
    persist_entry(e);
    if (out_start_sector) { *out_start_sector = e->start_sector; }
    return 0;
}

/* ── C7 P3b-5a-v — THE DURABLE WHOLE-FILE WRITE (host_seam.write_file_durably) ──────────────────────
 * fs_durable_write CREATES the FT_DURABLE staging file `name` on its FIRST stroke (O_TRUNC on an ABSENT
 * name is a create — the body's coarser O_TRUNC-by-flag refusal was narrowed to the R1 property: only an
 * overwrite of a PRESENT record is refused, :4343) and appends its bytes sequentially at the tail; the
 * bytes are stored RAW and CONTIGUOUS so fs_read_entry reads them back whole. This is the atomic-write-
 * once act's STAGING half; fs_swap_rename is its swap half. Distinct from the append-only record pen
 * (fs_nrec_append, FT_NREC) and the write-once blob (fs_blob_write_once, FT_BLOB): a durable-write
 * staging file is a temp that becomes a blob by an atomic rename, never the record (L21). */
int fs_durable_write(const char *name, const uint8_t *payload, uint32_t n) {
    uint32_t nlen = 0;
    while (nlen <= BFS_NAME_MAX && name[nlen]) { nlen++; }
    if (nlen > BFS_NAME_MAX) { return -1; }          /* a name longer than the field: refused, never truncated */
    struct bfs_entry *e = fs_find(name);
    if (e && e->type != FT_DURABLE) { return -1; }   /* a present name of another class is not a staging file */
    if (!e) {                                         /* the FIRST stroke: create the staging file (O_TRUNC-absent) */
        e = fs_alloc_entry();
        if (!e) { return -1; }
        name_set(e->name, name);
        e->type = FT_DURABLE; e->present = 1;
        e->start_sector = g_super.next_free;          /* claimed by the grow step below (capacity starts 0) */
        e->length = 0; e->capacity_sectors = 0; e->crc32 = 0;
        e->append_only = 0; e->reserved = 0;
    }
#ifdef PLANT_DURABLE_WRITE_NOOP
    (void)payload;
    return 0;                                          /* the fault: answer success, write NOTHING (STOP d, L19) */
#else
    uint32_t off = e->length;                          /* durable writes are sequential — extend at the tail */
    uint32_t new_len = e->length + n;
    uint32_t need = (new_len + SECTOR_SIZE - 1) / SECTOR_SIZE;
    if (need > e->capacity_sectors) {
        if (e->start_sector + e->capacity_sectors == g_super.next_free) {
            uint32_t extra = need - e->capacity_sectors;             /* the allocator tail: grow in place */
            if (g_super.next_free + extra > g_super.total_sectors) { return -1; }   /* out of data space */
            g_super.next_free += extra;
            e->capacity_sectors = need;
            persist_super();
        } else {                                                     /* not the tail: relocate to the tail */
            uint32_t new_start = g_super.next_free;
            if (new_start + need > g_super.total_sectors) { return -1; }   /* out of data space */
            uint32_t have = (e->length + SECTOR_SIZE - 1) / SECTOR_SIZE;
            for (uint32_t s = 0; s < have; s++) {                   /* the bytes move UNCHANGED */
                if (ata_read_sector(e->start_sector + s, g_sec) != 0) { return -1; }
                if (ata_write_sector(new_start + s, g_sec) != 0) { return -1; }
            }
            g_super.next_free += need;
            e->start_sector = new_start;
            e->capacity_sectors = need;
            persist_super();
        }
    }
    uint32_t written = 0;
    while (written < n) {
        uint32_t sec = e->start_sector + off / SECTOR_SIZE;
        uint32_t in  = off % SECTOR_SIZE;
        uint32_t room = SECTOR_SIZE - in;
        uint32_t chunk = (n - written < room) ? (n - written) : room;
        if (in != 0) {
            if (ata_read_sector(sec, g_sec) != 0) { return -1; }   /* preserve the prefix already in the sector */
        } else {
            memset(g_sec, 0, SECTOR_SIZE);
        }
        memcpy(g_sec + in, payload + written, chunk);
        if (ata_write_sector(sec, g_sec) != 0) { return -1; }
        written += chunk;
        off += chunk;
    }
    ata_flush();
    e->length = new_len;
    persist_entry(e);
    return 0;
#endif
}

/* ── C7 P3b-5a-v — THE ATOMIC-WRITE-ONCE SWAP (host_seam.write_file_durably's os.replace(tmp, final)) ──
 * Rename an FT_DURABLE staging file `oldname` over `newname`, CLOBBERING a present `newname` (the temp-and-
 * swap, S5-over-existing). This is the atomic-write-once act's own shape and is served ONLY on a durable-
 * write staging source — the ns write-once swap (fs_rename) keeps its no-clobber rule. The append-only
 * RECORD is NEVER a swap destination (its identity is fixed). The old final's bytes leave the store (its
 * directory entry is freed); the staging file takes the final name in place (no data move). */
int fs_swap_rename(const char *oldname, const char *newname) {
    struct bfs_entry *e = fs_find(oldname);
#ifdef PLANT_RECONCILE_BREAKS_SWAP
    /* the fault (A2's plant, L19): model an OVER-BROAD C7-MAINT-5B reconcile that adopted the STAGING file
     * as a record (FT_NREC) before its swap — the FT_DURABLE-only swap then finds no staging file to
     * rename and refuses, so the real write_file_durably reds. "a renamed staging file mis-typed." */
    if (e && e->type == FT_DURABLE) { e->type = FT_NREC; }
#endif
    if (!e || e->type != FT_DURABLE) { return -1; }   /* only a durable-write staging file swaps (clobbers) */
    uint32_t nlen = 0;
    while (nlen <= BFS_NAME_MAX && newname[nlen]) { nlen++; }
    if (nlen > BFS_NAME_MAX) { return -1; }            /* a name longer than the field: refused, never truncated */
    struct bfs_entry *dst = fs_find(newname);
    if (dst && dst->type == FT_RECORD) { return -1; }  /* never clobber the append-only record (fixed identity) */
#ifdef PLANT_SWAP_NOT_ATOMIC
    return 0;                                           /* the fault: answer success, perform NO swap (STOP d) */
#else
    if (dst) {                                          /* the atomic-write-once swap: the old final leaves */
        dst->present = 0;
        persist_entry(dst);
    }
    name_set(e->name, newname);                         /* the staging file becomes the final name in place */
    persist_entry(e);
    return 0;
#endif
}

/* read a present entry's bytes back off the disk and compare to (data, n) — used by write-once's
 * by-CONTENT precision (A3). Reads sector-by-sector into the shared g_sec buffer (no large buffer on
 * the body's small stack); the caller checks length first, so this only runs when lengths match. */
static int fs_blob_content_eq(const struct bfs_entry *e, const uint8_t *data, uint32_t n) {
    uint32_t got = 0, s = 0;
    while (got < n) {
        if (ata_read_sector(e->start_sector + s, g_sec) != 0) { return 0; }
        uint32_t c = n - got; if (c > SECTOR_SIZE) { c = SECTOR_SIZE; }
        if (memcmp(g_sec, data + got, c) != 0) { return 0; }
        got += c; s++;
    }
    return 1;
}

/* ── atomic-write-once: a blob written once, durable, write-ONCE ──────────────────────────────*/
int fs_blob_write_once(const char *id, const uint8_t *data, uint32_t n) {
    /* BODYFS02: a name longer than the field is REFUSED, never truncated (names are paths). A name
     * that does not fit could otherwise collide with a shorter one after truncation. */
    uint32_t idlen = 0;
    while (idlen <= BFS_NAME_MAX && id[idlen]) { idlen++; }
    if (idlen > BFS_NAME_MAX) { return -1; }

    struct bfs_entry *ex = fs_find(id);
    if (ex) {
        /* WRITE-ONCE BY NAME AND CONTENT (C7 P3b-5a-ii, A3; the sidecar-idempotence model, archi
         * :4257 precision (b) / store.py:711-720): the SAME bytes to a PRESENT name answer success with
         * NOTHING performed — the post-state already equals the request, not a fabricated success — and
         * DIFFERENT bytes REFUSE by name. (archi :4257 (c): a REMOVED name is re-creatable — fs_remove
         * frees the entry, so an absent name reaches fs_alloc_entry below and is created afresh.) */
        if (ex->type == FT_BLOB && ex->length == n && fs_blob_content_eq(ex, data, n)) {
#ifdef PLANT_NS_IDENTICAL_REFUSED
            return -1;    /* the fault: identical bytes to a present name refused (write-once mis-tightened) */
#else
            return 0;     /* idempotent: the bytes already stand — nothing performed */
#endif
        }
#ifndef PLANT_WRITEONCE_OVERWRITE
        return -1;        /* DIFFERENT bytes to a present id: REFUSED by name (write-once; A3 different-refuse) */
#endif
        /* PLANT_WRITEONCE_OVERWRITE: fall through and overwrite (the A3 different-accepted / P3b-2 fault) */
    }
    struct bfs_entry *e = ex ? ex : fs_alloc_entry();
    if (!e) { return -1; }

    uint32_t span = (n + SECTOR_SIZE - 1) / SECTOR_SIZE; if (span == 0) { span = 1; }
    uint32_t start;
    if (ex) {
        start = ex->start_sector;
        if (span > ex->capacity_sectors) { span = ex->capacity_sectors; }
    } else {
        start = g_super.next_free;
        if (start + span > g_super.total_sectors) { return -1; }   /* out of data space */
        g_super.next_free += span;
    }

    /* write the DATA sectors first (durable), THEN the directory name, THEN the allocator advance —
     * the atomic-write-once ordering: bytes durable before the name that reveals them. */
    for (uint32_t s = 0; s < span; s++) {
        memset(g_sec, 0, SECTOR_SIZE);
        uint32_t off = s * SECTOR_SIZE;
        uint32_t c = (off < n) ? (n - off) : 0u; if (c > SECTOR_SIZE) { c = SECTOR_SIZE; }
        if (c) { memcpy(g_sec, data + off, c); }
        if (ata_write_sector(start + s, g_sec) != 0) { return -1; }
    }
    ata_flush();

    name_set(e->name, id);
    e->type = FT_BLOB; e->present = 1; e->start_sector = start; e->length = n;
    e->capacity_sectors = (ex ? ex->capacity_sectors : span); e->crc32 = 0;
    e->append_only = 0; e->reserved = 0;
    persist_entry(e);
    if (!ex) { persist_super(); }
    return 0;
}

int fs_read_entry(const struct bfs_entry *e, uint8_t *out, uint32_t max, uint32_t *out_len) {
    uint32_t n = e->length;
    if (n > max) { return -1; }
    uint32_t got = 0, s = 0;
    while (got < n) {
        if (ata_read_sector(e->start_sector + s, g_sec) != 0) { return -1; }
        uint32_t c = n - got; if (c > SECTOR_SIZE) { c = SECTOR_SIZE; }
        memcpy(out + got, g_sec, c); got += c; s++;
    }
    if (out_len) { *out_len = n; }
    return 0;
}

/* ── C7 P3b-5a-v — STREAMED read of a caller-named record (host_seam.open_read/read_bytes, CLASS-C) ──
 * A FRESH reader reconstructs the WHOLE record of ANY size through this: copy up to `count` bytes from
 * byte offset `cursor` of the RAW-CONTIGUOUS entry at `start_sector` (length `elen`), spanning sectors,
 * WITHOUT a whole-file buffer or the 64 KiB cap fs_read_entry carries (the pre-5a-v under-serve: a record
 * past 64 KiB read back EMPTY). Returns bytes copied (0 at/after the end). Called per read() so a fresh
 * reader streams the record on demand. */
uint32_t fs_read_entry_range(uint32_t start_sector, uint32_t elen, uint32_t cursor,
                             uint8_t *dst, uint32_t count) {
    uint32_t remain = (cursor < elen) ? (elen - cursor) : 0u;
    uint32_t n = (count < remain) ? count : remain;
#ifdef PLANT_FRESH_READ_PARTIAL
    /* the fault: the reader never serves past the FIRST sector, so a multi-sector caller-named record
     * reads back PARTIAL — a fresh reader that does not see what the writer appended (CLASS-C). */
    if (cursor >= SECTOR_SIZE) { return 0; }
    if (cursor + n > SECTOR_SIZE) { n = SECTOR_SIZE - cursor; }
#endif
    uint32_t done = 0;
    uint64_t pos = (uint64_t)start_sector * SECTOR_SIZE + cursor;
    while (done < n) {
        uint32_t lba  = (uint32_t)((pos + done) / SECTOR_SIZE);
        uint32_t soff = (uint32_t)((pos + done) % SECTOR_SIZE);
        if (ata_read_sector(lba, g_sec) != 0) { break; }
        uint32_t c = SECTOR_SIZE - soff;
        if (c > n - done) { c = n - done; }
        memcpy(dst + done, g_sec + soff, c);
        done += c;
    }
    return done;
}

/* ── remove: a blob leaves the store; the record NEVER (the seam's contract) ───────────────────*/
int fs_remove(const char *id) {
    struct bfs_entry *e = fs_find(id);
    if (!e) { return -1; }
    if (e->type == FT_RECORD) { return -1; }   /* remove applies to blobs, NEVER the record */
#ifdef PLANT_REMOVE_LEAVES
    return 0;                                   /* the fault: claim success, leave it present */
#endif
    e->present = 0;
    persist_entry(e);
    return 0;
}

/* ── body-read: walk the body's own present files ─────────────────────────────────────────────
 * BODYFS02 (C7 P3b-5a-ii): the walk surfaces the FULL-WIDTH path name (BFS_NAME_MAX), so a /rec/
 * world listing sees caller-named paths whole (up to the 92-byte measured max). 5a-i left this at
 * char[][32] and deferred the widening to this slice, which carries it with serve.c/diskcheck.c (the
 * two consumers share this buffer type). */
int fs_walk(char names[][BFS_NAME_MAX], int max) {
    int c = 0;
#ifdef PLANT_WALK_MISSES
    int skipped = 0;
#endif
    for (uint32_t i = 0; i < BFS_MAX_ENTRIES && c < max; i++) {
        struct bfs_entry *e = entry_at(i);
        if (!e->present) { continue; }
#ifdef PLANT_WALK_MISSES
        if (!skipped) { skipped = 1; continue; }   /* the fault: the walk misses one file */
#endif
        memcpy(names[c], e->name, BFS_NAME_MAX);
        c++;
    }
    return c;
}

/* C7 P3b-5a-vi — mkdir a NAMESPACE DIRECTORY (FT_DIR): a zero-length name-only entry that stats as a
 * directory and lists its children (serve.c). Idempotent (a present FT_DIR -> 0); a present NON-directory
 * of the same name is REFUSED (-1, never reinterpreted); a name longer than the field is REFUSED (never
 * truncated — a path that does not fit could collide with a shorter one). No data sectors are consumed. */
int fs_mkdir(const char *name) {
    uint32_t idlen = 0;
    while (idlen <= BFS_NAME_MAX && name[idlen]) { idlen++; }
    if (idlen > BFS_NAME_MAX) { return -1; }
    struct bfs_entry *ex = fs_find(name);
    if (ex) { return (ex->type == FT_DIR) ? 0 : -1; }   /* idempotent; a non-dir of the same name refuses */
    struct bfs_entry *e = fs_alloc_entry();
    if (!e) { return -1; }
    name_set(e->name, name);
    e->type = FT_DIR; e->present = 1; e->start_sector = 0; e->length = 0;
    e->capacity_sectors = 0; e->crc32 = 0; e->append_only = 0; e->reserved = 0;
    persist_entry(e);
    return 0;
}

/* C7 P3b-5a-vi — a PRESENT entry by table index, or NULL. serve.c's getdents over a record-disk directory
 * scans [0, BFS_MAX_ENTRIES) with this and emits the entries that are immediate children of the dir path. */
struct bfs_entry *fs_entry_at(uint32_t i) {
    if (i >= BFS_MAX_ENTRIES) { return 0; }
    struct bfs_entry *e = entry_at(i);
    return e->present ? e : 0;
}

/* ── same-name rename: the write-once swap (C7 P3b-5a-ii, S5). Rename a PRESENT entry to an ABSENT
 * name; the RECORD is NEVER renamed (its append-only identity is fixed); a name longer than the field
 * is refused (never truncated); the destination must be ABSENT (write-once — no clobber). This
 * primitive renames the directory entry only (no data move). The same-directory / cross-directory
 * policy is the ns layer's (serve.c) — R4 cross-directory rename refuses there. ───────────────────*/
int fs_rename(const char *oldname, const char *newname) {
    struct bfs_entry *e = fs_find(oldname);
    if (!e) { return -1; }                          /* nothing present to rename */
    if (e->type == FT_RECORD) { return -1; }        /* the record's identity is fixed (append-only) */
    uint32_t nlen = 0;
    while (nlen <= BFS_NAME_MAX && newname[nlen]) { nlen++; }
    if (nlen > BFS_NAME_MAX) { return -1; }          /* a name longer than the field: refused, never truncated */
    if (fs_find(newname)) { return -1; }             /* write-once: the destination must be absent (no clobber) */
    name_set(e->name, newname);
    persist_entry(e);
    return 0;
}

/* ── the one-writer act's DISK shape (C7 P3b-5a-ii, A4): the marker name class (*.lock) is
 * TRUNCATE-REWRITE, not write-once — ftruncate-to-0 on a *.lock is the lock act's OWN shape (5s2
 * FINDINGS §1 / archi :4248), NEVER the record's or a blob's. The blob write-once path
 * (fs_blob_write_once) is UNTOUCHED — this is a SEPARATE primitive on a distinct name class, so the
 * write-once property is not loosened. Create-on-absent, or truncate-to-nothing + rewrite the holder's
 * mark on a present marker. The HELD exclusive claim is the ns layer's (serve.c); this writes bytes. */
int fs_marker_write(const char *name, const uint8_t *data, uint32_t n) {
    uint32_t nlen = 0;
    while (nlen <= BFS_NAME_MAX && name[nlen]) { nlen++; }
    if (nlen > BFS_NAME_MAX) { return -1; }
    struct bfs_entry *ex = fs_find(name);
    if (ex && ex->type == FT_RECORD) { return -1; }  /* the record is never a marker */
    struct bfs_entry *e = ex ? ex : fs_alloc_entry();
    if (!e) { return -1; }

    uint32_t span = (n + SECTOR_SIZE - 1) / SECTOR_SIZE; if (span == 0) { span = 1; }
    uint32_t start;
    if (ex) {
        start = ex->start_sector;                    /* truncate-rewrite within the marker's reserve */
        if (span > ex->capacity_sectors) { span = ex->capacity_sectors; }
    } else {
        start = g_super.next_free;
        if (start + span > g_super.total_sectors) { return -1; }
        g_super.next_free += span;
    }
    for (uint32_t s = 0; s < span; s++) {
        memset(g_sec, 0, SECTOR_SIZE);               /* truncate-to-nothing: the prior bytes are zeroed */
        uint32_t off = s * SECTOR_SIZE;
        uint32_t c = (off < n) ? (n - off) : 0u; if (c > SECTOR_SIZE) { c = SECTOR_SIZE; }
        if (c) { memcpy(g_sec, data + off, c); }
        if (ata_write_sector(start + s, g_sec) != 0) { return -1; }
    }
    ata_flush();
    name_set(e->name, name);
    e->type = FT_BLOB; e->present = 1; e->start_sector = start; e->length = n;
    e->capacity_sectors = (ex ? ex->capacity_sectors : span); e->crc32 = 0;
    e->append_only = 0; e->reserved = 0;
    persist_entry(e);
    if (!ex) { persist_super(); }
    return 0;
}

/* ── founding-pack-read: the pack bytes from disk, crc'd and matched to the recorded pack ──────*/
int fs_founding_pack_read(uint32_t *out_len, uint32_t *out_crc, int *out_match) {
    struct bfs_entry *e = fs_find("founding-pack");
    if (!e || e->type != FT_PACK) { return -1; }
    uint32_t n = e->length;
    uint32_t crc = crc32_begin();
    uint32_t got = 0, s = 0;
    while (got < n) {
        if (ata_read_sector(e->start_sector + s, g_sec) != 0) { return -1; }
        uint32_t c = n - got; if (c > SECTOR_SIZE) { c = SECTOR_SIZE; }
#ifdef PLANT_PACK_WRONG
        if (s == 0) { g_sec[0] ^= 0xFFu; }     /* corrupt one byte -> the crc differs (A2) */
#endif
        crc = crc32_feed(crc, g_sec, c);
        got += c; s++;
    }
    crc = crc32_final(crc);
    if (out_len) { *out_len = n; }
    if (out_crc) { *out_crc = crc; }
    if (out_match) { *out_match = (crc == e->crc32) ? 1 : 0; }
    return 0;
}
