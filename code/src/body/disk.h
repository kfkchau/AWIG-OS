/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the disk surface: a block device and the body's own filesystem (C7 P3b-2).
 *
 * design/54 §7 P3b-2. The body already boots with memory (P3b-1). This slice adds, ON THE METAL,
 * a block device (a polled ATA/PIO driver) and a small bespoke filesystem — BODYFS — that the
 * estate's record maps onto directly, so the body performs THE FIVE RECORD ACTS on its OWN disk:
 *   record-pen         append a record to the append-only record file; read it back equal
 *   atomic-write-once  write a blob once, durable across a re-read; a second write does NOT corrupt
 *   remove             remove a blob (NEVER the record — remove applies to blobs, the seam's contract)
 *   body-read          walk the body's own files (the directory)
 *   founding-pack-read  read the founding pack from the disk, its bytes equal to the pack
 *
 * Hand-written and read whole (design/47 §2 I3, §9): no opaque code in the signed base. The block
 * driver is the body's OWN metal performer of these acts — it is BENEATH the seam, not a host
 * crossing (the seam-routing binds the host-side Python build tools, not this C body). Every build
 * and boot is the guest's nested qemu, with a virtual block device the nested qemu presents (L11).
 *
 * THE RECORD IS APPEND-ONLY BY CONSTRUCTION (archi :4019, the by-name countersign precision). The
 * filesystem exposes NO truncate and NO in-place overwrite path for the record file: the ONE write
 * primitive (fs_record_write_at) enforces off == the record's current length (the tail), so a
 * write anywhere but the tail is REFUSED — the body-level form of the estate's append-only law and
 * the sole-appender leash. 'remove' refuses the record and applies only to blobs.
 *
 * THE SINGLE-WRITER-LOCK'S METAL MEANING (Q-G, the P1/P2 least-portable crossing; stated on its row
 * here because the pen lands at this slice, :4005). Today the single-writer-lock act is the
 * host-PID liveness lock (pid_alive/getpid/lock_read/lock_write/lock_unlink) — the LEAST-PORTABLE
 * crossing, resting on a foreign OS's PID namespace and advisory-lock facility. A from-blank-page
 * body has NO foreign PID and NO foreign advisory lock: it runs single-core, single-address-space,
 * one writer BY CONSTRUCTION (the body itself is the sole writer — there is no second process
 * contending for the record). So at the metal "there is exactly one writer" stops being something a
 * lock CHECKS and becomes something the body's construction GUARANTEES — the least-portable crossing
 * collapses into a non-crossing. This body IS that one writer; it takes no lock and needs none. The
 * collapse holds ONLY while the body is single-writer by construction (a second writer under SMP or
 * a second body under P6 would need a real intra-body mechanism, not a PID lock — new code beyond
 * this slice). That re-expression is why this slice performs the pen without a lock act at all.
 */
#ifndef DISK_H
#define DISK_H

#include <stdint.h>
#include <stddef.h>

/* ── The block device: a polled ATA/PIO disk on the primary bus (0x1F0), LBA28 ────────────────
 * qemu's `pc` machine presents an IDE controller; `-drive if=ide,index=0` is the primary master.
 * Output is one sector (512 bytes) at a time, polled (no interrupts — Q-C interrupts are a later
 * P3b row). ata_present() observes a state it did not create (a floating bus reads 0xFF). */
#define SECTOR_SIZE 512u

int  ata_present(void);                                    /* 1 if a disk answers the primary master */
int  ata_read_sector(uint32_t lba, void *buf512);          /* 0 ok, -1 on timeout/error              */
int  ata_write_sector(uint32_t lba, const void *buf512);   /* 0 ok, -1 on timeout/error              */
int  ata_flush(void);                                      /* the durability barrier (ATA CACHE FLUSH)*/

/* ── BODYFS02: the bespoke on-disk layout the record maps onto (little-endian, 512-byte sectors) ──
 * Sector 0 is the superblock; sectors [dir_start .. dir_start+dir_sectors) hold the directory
 * (256-byte entries, 2 per sector); the data region begins at data_start. The build tool
 * (src/body/mkdisk.py) formats the disk with the record file (empty, append-only) and the founding
 * pack (its bytes + a crc32); the body MOUNTS it and never formats. mkdisk.py mirrors these exact
 * bytes — the two are kept in lock-step (an mkfs tool mirrors its filesystem driver).
 *
 * C7 P3b-5a-i — THE FORMAT GROWS BODYFS01 -> BODYFS02 TO CARRY PATH-NAMED NAMESPACES, sized by the
 * measurement (planning/evidence/C7-P3b-5s2-WRITE-CLASSES + the 5a pre-flight, archi :4257):
 *   names are PATHS    name[128] >= the 92-byte longest measured path (was name[32]).
 *   MANY entries       2048 >= the 1,230 per-module max path count (test_ep40), a fresh image per
 *                      module boot (was 32).
 *   data region 64MiB  >= 1.9x the 34.16 MiB per-module max write volume (test_ep24c) — a DIFFERENT
 *                      module: byte-max and path-max are decoupled, sized independently.
 * The append-only / write-once / one-writer PROPERTIES are UNCHANGED — the mechanism grows, the
 * property holds, its pins re-point (L14). A BODYFS01 image is REFUSED at mount BY NAME (the magic
 * check in fs_mount fires first): the old format is not silently reinterpreted. The namespace ACTS
 * at caller-named paths under /rec/ (mkdir, create-on-absent, ...) are the NEXT slice (5a-ii,
 * serve.c); this slice grows the substrate ONLY. */
#define BFS_MAGIC       "BODYFS02"
#define BFS_VERSION     2u
#define BFS_NAME_MAX    128u                                /* a name field holds a PATH: >= 92 bytes  */
#define BFS_ENTRY_SIZE  256u                                /* name[128] + 8 u32 (32) + pad; divides 512*/
#define BFS_ENTRIES_PER_SECTOR (SECTOR_SIZE / BFS_ENTRY_SIZE)     /* = 2 entries per sector             */
#define BFS_DIR_START   1u
#define BFS_DIR_SECTORS 1024u                               /* 1024 sectors * 2 entries = 2048 entries  */
#define BFS_DATA_START  (BFS_DIR_START + BFS_DIR_SECTORS)   /* = 1025                                    */
#define BFS_MAX_ENTRIES (BFS_DIR_SECTORS * BFS_ENTRIES_PER_SECTOR)   /* = 2048                           */

/* Entry types. */
#define FT_FREE   0u
#define FT_RECORD 1u
#define FT_BLOB   2u
#define FT_PACK   3u
/* C7 P3b-5a-iv — a CALLER-NAMED append-only record (the record pen at caller-named paths under /rec/,
 * matching the store's sole appender host_seam.open_append = path.open("a")). Distinct from the single
 * fixed RECK-format "record" (FT_RECORD): an FT_NREC entry stores its appended bytes RAW and CONTIGUOUS
 * (created on the first stroke, extended at the tail on later strokes), so a body-read reads back the
 * exact concatenation via fs_read_entry. The append-only property holds by construction (bytes are only
 * added at the tail; there is no overwrite-in-place and no truncate path — O_TRUNC is refused above, in
 * serve.c). A blob (FT_BLOB, write-once) is never appended, and the fixed record (FT_RECORD) is never a
 * caller-named path — the three name classes stay distinct (L21). */
#define FT_NREC   4u
/* C7 P3b-5a-v — a DURABLE WHOLE-FILE WRITE staging file (the store's atomic-write-once act, host_seam.
 * write_file_durably: os.open(tmp, O_WRONLY|O_CREAT|O_TRUNC) on an ABSENT temp name, write, fsync,
 * os.replace(tmp, final)). Distinct from the write-once blob (FT_BLOB, all bytes at once, no clobber) and
 * from the append-only record (FT_NREC): an FT_DURABLE file is CREATED by O_TRUNC on an absent name, its
 * bytes written sequentially, then RENAMED over its final name (fs_swap_rename, which CLOBBERS a present
 * final — the atomic-write-once swap, S5-over-existing). O_TRUNC on a PRESENT record (FT_NREC/FT_RECORD)
 * stays REFUSED by name (R1) — the durable whole-file write is the atomic-write-once act, never an
 * overwrite of the record. The four name classes (record / caller-named record / write-once blob /
 * durable-write staging) stay distinct (L21). */
#define FT_DURABLE 5u
/* C7 P3b-5a-vi — a NAMESPACE DIRECTORY one level under a world (mkdir /rec/<world>/blobs). A zero-length
 * entry (no data sectors, start_sector/capacity 0) whose ONLY meaning is the type: it STATS as a directory
 * (serve.c newfstatat/fstat -> S_IFDIR) and LISTS its immediate children (serve.c getdents over fs_entry_at,
 * the flat name table read as a tree by prefix). NO on-disk byte-format change — the existing `type` field
 * carries a sixth value; the entry layout, sizes and mkdisk.py format are untouched (an edit-in-place, not a
 * new field). A blob written under the directory (tmp/<world>/blobs/<id>) is an ordinary FT_BLOB, served
 * write-once exactly as at the world level (L21 — a declared path class, never a general writable fs). */
#define FT_DIR    6u

/* A record on disk carries a 16-byte header, then its payload, padded to whole sectors — so an
 * append never has to read-modify-write a shared tail sector (records are sector-granular). */
#define RECK_MAGIC 0x5245434Bu                             /* 'RECK' */

struct bfs_super {
    char     magic[8];          /* "BODYFS02"                                 */
    uint32_t version;           /* 2                                          */
    uint32_t block_size;        /* 512                                        */
    uint32_t dir_start;         /* 1                                          */
    uint32_t dir_sectors;       /* 1024                                       */
    uint32_t data_start;        /* 1025                                       */
    uint32_t next_free;         /* next free data sector (blob allocator)     */
    uint32_t total_sectors;     /* the image size, in sectors                 */
    uint32_t dir_count;         /* used entries at format (informational)     */
    uint8_t  pad[SECTOR_SIZE - 44];
} __attribute__((packed));

struct bfs_entry {
    char     name[BFS_NAME_MAX]; /* nul-padded ASCII PATH (BODYFS02: 128 bytes, was 32)        */
    uint32_t type;              /* FT_*                                       */
    uint32_t present;           /* 1 present, 0 free/removed                  */
    uint32_t start_sector;      /* first data sector                          */
    uint32_t length;            /* valid bytes (RECORD: the tail byte offset) */
    uint32_t capacity_sectors;  /* sectors reserved for this file             */
    uint32_t crc32;             /* PACK: crc32 of `length` bytes; else 0      */
    uint32_t append_only;       /* 1 for the RECORD file                      */
    uint32_t reserved;
    uint8_t  pad[BFS_ENTRY_SIZE - BFS_NAME_MAX - 8u * 4u];  /* to BFS_ENTRY_SIZE (256): 2/sector */
} __attribute__((packed));
/* the entry must divide the sector cleanly, so a persist writes back whole sectors (never a
 * straddle) — the property that keeps the on-disk directory sector-granular as it grows (L14). */
_Static_assert(sizeof(struct bfs_entry) == BFS_ENTRY_SIZE, "bfs_entry must be exactly BFS_ENTRY_SIZE");
_Static_assert(SECTOR_SIZE % BFS_ENTRY_SIZE == 0u, "BFS_ENTRY_SIZE must divide SECTOR_SIZE");

struct bfs_rechdr {
    uint32_t magic;             /* RECK_MAGIC                                 */
    uint32_t byte_len;          /* payload length                            */
    uint32_t seq;               /* 0-based append index                       */
    uint32_t reserved;
} __attribute__((packed));

/* CRC-32 (IEEE, reflected — byte-identical to Python's zlib.crc32). Streaming: seed 0, feed bytes,
 * finalize. So the body can crc the 370 KB pack sector-by-sector without buffering the whole file. */
uint32_t crc32_begin(void);
uint32_t crc32_feed(uint32_t crc, const uint8_t *data, uint32_t n);
uint32_t crc32_final(uint32_t crc);

/* Small freestanding helpers (bodyfs.c): a byte compare, a bounded string length, and a directory
 * name compare (names are nul-padded within 32 bytes). */
int      mem_eq(const void *a, const void *b, uint32_t n);
uint32_t str_len(const char *s);
int      fs_name_eq(const char *field, const char *id);

/* ── The filesystem, mounted on the block device ──────────────────────────────────────────────*/
int  fs_mount(void);                                       /* read super+dir; 0 ok, -1 bad/no disk  */
struct bfs_entry *fs_find(const char *name);               /* a present entry by name, or NULL      */
int  fs_name_index(const char *name);                      /* C7-MAINT-5B (A2): a present entry's table
                                                            * index (stable per-file identity), or -1  */

/* record-pen: the append-only record file. fs_record_write_at is the ONE write primitive and it
 * REFUSES any offset but the tail (append-only by construction). fs_record_append is that call at
 * the tail. fs_record_read reads back the record at a given start sector (header + payload). */
int  fs_record_write_at(uint32_t off, const uint8_t *payload, uint32_t n, uint32_t *out_start_sector);
int  fs_record_append(const uint8_t *payload, uint32_t n, uint32_t *out_start_sector);
int  fs_record_read(uint32_t start_sector, uint8_t *out, uint32_t max, uint32_t *out_len);

/* C7 P3b-5a-iv — the record pen at CALLER-NAMED names (design/54 §7 P3b-5a-iv; L21/L14/L19). Create the
 * append-only record `name` (FT_NREC) on its FIRST stroke and append; on a PRESENT one, extend at the
 * tail. Bytes are stored RAW and CONTIGUOUS (fs_read_entry reads back the exact concatenation). APPEND-
 * ONLY BY CONSTRUCTION: bytes are only ever added at the tail — there is no overwrite-in-place and no
 * truncate path (O_TRUNC is refused in serve.c, R1). The entry grows in place when it is the allocator
 * tail; otherwise its bytes are relocated UNCHANGED to the tail (append-only in content). A name of
 * another class (a write-once blob / the fixed record) is refused, not appended. 0 ok, -1 refused. */
int  fs_nrec_append(const char *name, const uint8_t *payload, uint32_t n, uint32_t *out_start_sector);

/* C7 P3b-5a-v — the DURABLE WHOLE-FILE WRITE (host_seam.write_file_durably). fs_durable_write CREATES the
 * staging file `name` (FT_DURABLE) on its first stroke (O_TRUNC on an absent name is a CREATE, not the R1
 * overwrite of a present record) and appends its bytes sequentially at the tail; the bytes are stored RAW
 * and CONTIGUOUS (read back whole via fs_read_entry). fs_swap_rename is the atomic-write-once swap: rename
 * an FT_DURABLE `old` over `new`, CLOBBERING a present `new` (S5-over-existing) — the write-once blob swap
 * the ns rename (fs_rename, no-clobber) is NOT. 0 ok, -1 refused. */
int  fs_durable_write(const char *name, const uint8_t *payload, uint32_t n);
int  fs_swap_rename(const char *oldname, const char *newname);

/* C7 P3b-5a-v — read an entry's bytes at an arbitrary byte offset, STREAMED from disk on demand (no whole-
 * file buffer, no 64 KiB cap): copy up to `count` bytes from byte offset `cursor` of the entry at
 * `start_sector` (length `elen`), spanning sectors. Returns bytes copied (0 at/after the end). A fresh
 * reader of a caller-named record reconstructs the whole record of ANY size through this (CLASS-C). */
uint32_t fs_read_entry_range(uint32_t start_sector, uint32_t elen, uint32_t cursor,
                             uint8_t *dst, uint32_t count);

/* atomic-write-once: a blob written once, durable, write-ONCE. C7 P3b-5a-ii — WRITE-ONCE BY NAME AND
 * CONTENT (A3): the SAME bytes to a present id answer success with nothing performed (idempotent);
 * DIFFERENT bytes refuse by name; a REMOVED id is re-creatable. remove: a blob removed (record refused). */
int  fs_blob_write_once(const char *id, const uint8_t *data, uint32_t n);
int  fs_read_entry(const struct bfs_entry *e, uint8_t *out, uint32_t max, uint32_t *out_len);
int  fs_remove(const char *id);                            /* blobs only; -1 (refused) for the record */

/* C7 P3b-5a-ii — same-name rename (S5, the write-once swap): rename a present entry to an absent
 * name; the record is never renamed; the destination must be absent (no clobber). The
 * same-directory / cross-directory policy is the ns layer's (serve.c). */
int  fs_rename(const char *oldname, const char *newname);
/* C7 P3b-5a-ii — the one-writer act's disk shape (A4): TRUNCATE-REWRITE on the marker name class
 * (*.lock) ONLY; the blob write-once path is untouched (a distinct name class, archi :4248). */
int  fs_marker_write(const char *name, const uint8_t *data, uint32_t n);

/* body-read: walk the body's own present files, newest scan order. Fills `names` up to `max`,
 * returns the count. C7 P3b-5a-ii: the walk surfaces the FULL-WIDTH path name (BFS_NAME_MAX), so a
 * /rec/ world listing sees caller-named paths whole (5a-i deferred this widening to 5a-ii; the two
 * consumers — serve.c serve_file_act getdents and diskcheck.c check_body_read — share this type). */
int  fs_walk(char names[][BFS_NAME_MAX], int max);

/* C7 P3b-5a-vi — mkdir a NAMESPACE DIRECTORY (FT_DIR), idempotent: a present FT_DIR of the same name
 * answers success (0); a present NON-directory of the same name is REFUSED (-1); a too-long name (> the
 * field) is REFUSED. No data sectors are consumed (a directory is a zero-length name-only entry). */
int  fs_mkdir(const char *name);
/* C7 P3b-5a-vi — a PRESENT entry by table index, or NULL (index >= BFS_MAX_ENTRIES or a free slot). serve.c
 * enumerates a record-disk directory's immediate children by scanning [0, BFS_MAX_ENTRIES) with this. */
struct bfs_entry *fs_entry_at(uint32_t i);

/* founding-pack-read: read the pack bytes from disk, crc them, and compare to the recorded
 * (length, crc). 0 = the read matches the recorded pack; fills *out_len,*out_crc for the serial. */
int  fs_founding_pack_read(uint32_t *out_len, uint32_t *out_crc, int *out_match);

/* ── The five-act self-check (diskcheck.c) — each act PASS/FAIL on the serial line ─────────────
 * disk_selfcheck() runs the five acts on a freshly-formatted disk and returns 1 iff all pass.
 * disk_verify_persisted() runs on a REBOOT (a record already present) and confirms the record and
 * the blob survived the reboot — the durability-across-a-reboot demonstration (§A33). */
int disk_selfcheck(void);
int disk_verify_persisted(void);

/* The fixed self-check payloads, shared by the fresh self-check and the reboot verification so the
 * two boots compare against the same known bytes. */
extern const char DISK_RECORD0[];       /* the first appended record's payload            */
extern const char DISK_BLOB_SELF_A[];   /* the write-once blob's bytes                    */

#endif /* DISK_H */
