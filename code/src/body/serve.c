/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — THE FORTY-NINE SERVED, on the metal (C7 P3b-4b; design/54 §5 L18, §7 P3b-4b;
 * the P3b-4s FINDINGS the spec; precision (a)/(b) of board :4085).
 *
 * The body classifies each measured crossing by PURPOSE (its argument shape, not its name), routes it to
 * the act machinery / floor / designed-refusal / stub, and WITNESSES it as ONE UNSIGNED ROW of its own
 * append-only serve trail. The twelve acts' share is PERFORMED by the act machinery (memory via pmm/vmm,
 * entropy via the P3b-3 CSPRNG, the clocks via the P3b-3 sources, the record acts via bodyfs) and
 * witnessed like every crossing. The hard floor (bring-up/loader/TLS category A; thread creation category
 * B) is realized on the metal as the memory and concurrency acts' machinery and witnessed. The designed
 * refusal (module discovery on a live filesystem, category C) is refused and the module bytes served from
 * the SEALED IMAGE (digest-checked at load by the P3b-4a loader — precision b), no filesystem walk. The
 * stubs (category D) degrade. Entropy is served AT BRING-UP. The network-socket share is refused as the
 * worker's native failure until P3b-6.
 *
 * THE BODY HOLDS NO KEY (precision a). Every serve row carries sig==0 and chain==0; the body NEVER
 * appends a row into the estate's signed chain. The SIGNED act row is the GATE's, ABOVE the seam, and NO
 * GATE RUNS ON THE BODY here — the per-act signed-gate-row check is DEFERRED to P3b-4c/P3b-5. This is the
 * precision the first freeze of this row missed (refused :4087): it checked a signed gate row that no gate
 * on the body could write.
 *
 * The A2/A3/A4 near-misses (build.sh -D — a check that cannot fail is not a check):
 *   PLANT_SERVE_TRAIL_SKIP     an acts'-share crossing (the mmap) is NOT recorded -> CHECK WITNESSED reds
 *   PLANT_BODY_SIGNS_ROW       an acts'-share row carries a signature (a key in the body) -> CHECK KEYLESS reds
 *   PLANT_ACT_ROW_IN_CHAIN     an acts'-share row is appended into the estate's signed chain -> CHECK UNSIGNED reds
 *   PLANT_ENTROPY_NOT_AT_BRINGUP the bring-up entropy draw is deferred -> CHECK ENTROPY-BRINGUP reds
 *   PLANT_MEM_FORK_SHARED      the memory act serves fork-shareable memory -> CHECK MEM-PRIVATE reds
 *   PLANT_THREAD_NO_SETTLS     thread-create does not reproduce SETTLS -> CHECK THREAD-SHAPE reds
 *   PLANT_COMMIT_NOT_ABSOLUTE  the commit-window deadline is not absolute -> CHECK COMMIT-ABSOLUTE reds
 *   PLANT_FUTEX_WRONG_SHAPE    the wait is not the PRIVATE bitset realtime shape -> CHECK FUTEX-SHAPE reds
 *   PLANT_FS_WALK_SERVED       the module-discovery scan is SERVED (a filesystem walk) -> CHECK REFUSAL-MODULE reds
 *   PLANT_SOCKET_SERVED        the network-socket share is SERVED, not refused -> CHECK SOCKET-REFUSED reds
 *   PLANT_SERVE_CATEGORY_E     a category-E call is declared served, not excluded -> CHECK EXCLUDED reds
 */
#include "body.h"
#include "clock.h"
#include "disk.h"
#include "enclosure.h"
#include "serve.h"

/* the worker's forty-nine run ended by exit_group (read by the enclosure driver). */
volatile int g_serve_exited;
/* C7 P3b-5b-i: the exit_group STATUS the ring-3 program passed (the ledger bootstrap os._exit's 0 green /
 * 1 red). The body carries it to serial (LEDGER-EXIT-STATUS) — the REAL exit status, read back by the
 * host-side test (design/54 §7 P3b-5b, precision 5; :4303). NEVER fabricated: it is exactly the a0 the
 * program passed to exit_group. */
volatile int g_serve_exit_status;

/* ── the body's own append-only serve trail (memory-resident, read back on serial) ───────────────────*/
static struct serve_row g_serve_trail[SERVE_TRAIL_MAX];
static uint32_t g_serve_rows;         /* rows appended (append-only)                                    */
static uint32_t g_serve_crossings;    /* crossings the body processed (== rows unless a row was skipped) */

/* ── C7 P3b-6b — THE BORROWED TCP ENCLOSURE (design/54 §5 L18; §7 P3b-6b). ────────────────────────────
 * g_serve_enclosure selects which per-enclosure DECLARED SET serve_request gates against (the PERFORMERS
 * are shared; :4302 b). Default ENCL_INTERP (0) — the interpreter path is UNCHANGED (it never issues the
 * three frame shapes; if it did, refused). The frame counters + heap peak are the A4/A5 checks-that-fail. */
uint32_t g_serve_enclosure = ENCL_INTERP;
uint32_t g_frames_sent, g_frames_recv, g_frame_rows, g_lwip_beyond_served;
uint64_t g_lwip_mem_peak;

#ifdef SOCKET_ACT
/* C7 P3b-6c(iii) A3 — a DEDICATED socket-act trail. The shared g_serve_trail is flooded by the
 * interpreter's OWN thousands of startup syscalls, so the socket-act act-witness lives in its own bounded
 * append-only trail: ONE row per relayed shape (CAT_SOCK) and ONE per frame crossing (CAT_FRAME), read back
 * after the run (L18). A plant that skips a row makes the count diverge from the acts (the no-trail plant). */
struct sa_row { uint32_t num, cat, verdict; uint64_t ans; };
static struct sa_row g_sa_trail[256];
static uint32_t g_sa_trail_n;
void serve_sa_trail_reset(void) { g_sa_trail_n = 0; }
static void sa_trail_append(uint32_t num, uint32_t cat, uint32_t verdict, uint64_t ans) {
    if (g_sa_trail_n < 256) {
        g_sa_trail[g_sa_trail_n].num = num; g_sa_trail[g_sa_trail_n].cat = cat;
        g_sa_trail[g_sa_trail_n].verdict = verdict; g_sa_trail[g_sa_trail_n].ans = ans;
        g_sa_trail_n++;
    }
}
#endif

/* A5 — the heap budget the body grants the lwIP worker. Comfortably above the measured 17,048 B
 * high-water; PLANT_LWIP_HEAP_SMALL sizes it BELOW, so the connection's allocations starve and it reds by
 * a REAL mechanism (OOM), never a flag (the PBUF_RAM receive is the config sidestep, named in the close). */
#if defined(PLANT_LWIP_HEAP_SMALL)
#define LWIP_HEAP_BUDGET  8192ull        /* below the 17,048 B high-water — the connection overruns/OOMs  */
#else
#define LWIP_HEAP_BUDGET  262144ull      /* 256 KiB — comfortably above the high-water                    */
#endif
static uint64_t g_lwip_mem_served;       /* bytes brk/mmap-granted to the lwIP worker (against the budget) */

/* the lwIP worker's monotonic clock (sys_now): rdtsc-based so it advances in real time REGARDLESS of the
 * ring level (the worker spends most of its time in ring-0 frame syscalls with interrupts masked, which
 * would starve a tick-based clock). floor_net_run calibrates cycles/ms against the PIT before the run. */
static uint64_t g_lwip_tsc_base, g_lwip_tsc_per_ms;
void serve_net_clock_calibrate(uint64_t tsc_base, uint64_t tsc_per_ms) {
    g_lwip_tsc_base = tsc_base; g_lwip_tsc_per_ms = tsc_per_ms;
}

/* record the lwIP worker's cumulative granted heap and enforce the A5 budget. Returns 1 iff `add` bytes
 * may be granted (budget not exceeded); tracks the peak either way. Only consulted for ENCL_LWIP. */
static int lwip_heap_grant(uint64_t add) {
    if (g_lwip_mem_served + add > LWIP_HEAP_BUDGET) { return 0; }
    g_lwip_mem_served += add;
    if (g_lwip_mem_served > g_lwip_mem_peak) { g_lwip_mem_peak = g_lwip_mem_served; }
    return 1;
}

/* ── serve_declared: the per-enclosure gate, as DATA (:4302 b). 1 iff `num` is declared for `enclosure`,
 * 0 iff refused BY NAME. The lwIP enclosure declares its whole-process measured set (the twenty) + the
 * clock (sys_now) + the three frame shapes; the interpreter enclosure declares everything EXCEPT the three
 * frame shapes (so its fifty are unchanged; a frame shape offered to it is refused, L18). ────────────*/
static const uint32_t LWIP_DECLARED[] = {
    /* the twenty whole-process measured shapes (mgr :4297; POST-MAIN 4 + PRE-MAIN 16) */
    SYS_brk, SYS_exit_group, SYS_getrandom, SYS_write,                                    /* post-main */
    SYS_access, SYS_arch_prctl, SYS_close, SYS_execve, SYS_fstat, SYS_mmap, SYS_mprotect, /* pre-main  */
    SYS_munmap, SYS_newfstatat, SYS_openat, SYS_pread64, SYS_prlimit64, SYS_read,
    SYS_rseq, SYS_set_robust_list, SYS_set_tid_address,
    SYS_clock_gettime,                                                                    /* sys_now   */
};
#define LWIP_DECLARED_N ((uint32_t)(sizeof(LWIP_DECLARED) / sizeof(LWIP_DECLARED[0])))

int serve_declared(uint32_t enclosure, uint64_t num) {
    int is_frame = (num == REQ_SEND_FRAME || num == REQ_RECV_FRAME || num == REQ_WAIT);
#if defined(PLANT_ENCL_CROSS)
    /* the fault: the gate ignores the enclosure — a frame shape is answered for the interpreter's
     * enclosure (and an interpreter-only shape for the lwIP one), so the cross-refusal check reds. */
    (void)enclosure; return 1;
#endif
    if (enclosure == ENCL_LWIP) {
        if (is_frame) { return 1; }                        /* the three frame shapes: lwIP-only */
        for (uint32_t i = 0; i < LWIP_DECLARED_N; i++) {
            if ((uint32_t)num == LWIP_DECLARED[i]) { return 1; }
        }
#if defined(PLANT_LWIP_BEYOND_SERVED)
        return 1;   /* the fault: a shape BEYOND the twenty is SERVED to the stack -> served-set check reds */
#else
        return 0;   /* beyond the declared twenty (e.g. socket, clone3, readlinkat): refused BY NAME (L18) */
#endif
    }
    /* ENCL_INTERP: everything the interpreter's fifty already reach is declared; ONLY the three frame
     * shapes are refused to it (it never issues them — the interpreter path is unchanged). */
    return is_frame ? 0 : 1;
}

/* ── the check state — each a DIFFERENT input the corresponding check reads (never the same measure) ──*/
static int g_entropy_at_bringup = -1; /* the GRND_NONBLOCK draw served from the body at bring-up         */
static int g_mem_served_private = -1; /* the MAP_SHARED memory act served anonymous-PRIVATE (Q11)        */
static int g_thread_settls      = -1; /* clone3 reproduced THREAD+VM+SETTLS+CHILD_CLEARTID (Q-D)         */
static int g_commit_absolute    = -1; /* clock_nanosleep was MONOTONIC TIMER_ABSTIME (Q-D)              */
static int g_futex_shape_ok     = -1; /* futex was PRIVATE bitset-wait with a realtime clock (Q-D)       */
static int g_module_refused     = -1; /* the module-discovery scan refused, bytes from the sealed image  */
static int g_socket_refused     = -1; /* the network-socket share refused as the native failure          */
static uint32_t g_seal_byte0;         /* the first byte of the SEALED image the refusal served instead of a walk */

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-4d — THE SEALED IMAGE AS A READ-ONLY FILESYSTEM (design/54 §5 L19, §7 P3b-4d; B6; Q15/:4134).
 *
 * The sealed image is a read-only filesystem of NAMED FILES (the dynamic linker, the C library and its
 * companions) the body serves BY PATH + OFFSET and BY LISTING. It is ONE archive (GOVSIMG1): a header, a
 * table of fixed 128-byte entries {absolute path, offset, length, dir-flag}, then the file-byte region —
 * DIGEST-CHECKED as a whole before load (the SealedArtifact.verify idiom carried to the metal). The body
 * parses the table once (serve_fs_set_image), resolves a path to an entry (si_find), opens an fd, and
 * serves read/pread64/fstat/mmap(file-backed)/getdents64/close from the image bytes — NEVER a live host
 * filesystem walk. A path OUTSIDE the sealed set (and not a record name) is refused ENOENT (the designed
 * refusal that remains, Q15/:4134). The P3b-2 record filesystem is mounted BESIDE it (distinct
 * namespaces). Active ONLY while g_dyn_fs_on (the floor3 dynamic run); the P3b-4a/4b/floor/floor2 paths
 * are byte-identical with it clear. ═══════════════════════════════════════════════════════════════════*/
#define SI_MAGIC "GOVSIMG1"            /* 8 bytes, the archive's leading magic                           */
#define SI_PATH_MAX 104u               /* the fixed path field in an entry                               */
#define SI_DIR_FLAG 1u                 /* entry flags bit0: this entry is a directory                   */
/* C7 P3b-5a-vi — THE OPEN-FD TABLE GROWN TO LINUX'S SHAPE (A1). The estate store holds ONE *.lock fd per
 * live writer for the writer's lifetime (F_SETLK), and the lock-heavy modules build many un-closed stores in
 * ONE process; the old ld.so-sized 48-fd table exhausts and os.open answers -EMFILE where Linux (soft
 * RLIMIT_NOFILE 1024) would not. The width is DERIVED, not guessed (the :4234 lesson): the peak concurrently-
 * open fd over ALL 193 5s2 traces (interpreter opens included) is 203 (test_ep24c) — so Linux's 1024 soft
 * RLIMIT_NOFILE comfortably exceeds it (headroom 5x). prlimit64 RLIMIT_NOFILE reports this same ceiling
 * (serve_prlimit64). 256 MiB holds a table this wide: the arrays indexed by SI_MAX_FD are ~285 KiB total
 * (g_fds 16 B, g_tree_fd 16 B, g_treedir_path 116 B, g_nrec_path 128 B, g_recdir_path 128 B, g_nrecrd 8 B,
 * g_lock_held 1 B per slot). PLANT_FD_TABLE_NARROW restores the 48-fd ceiling -> the lock-heavy modules EMFILE. */
#if defined(PLANT_FD_TABLE_NARROW)
#define SI_MAX_FD 48u                  /* the fault: the old ld.so-sized table -> lock-heavy modules EMFILE  */
#else
#define SI_MAX_FD 1024u                /* Linux's soft RLIMIT_NOFILE; derived peak-concurrent 203 << 1024    */
#endif
#define SI_FD_BASE 16u                 /* first returned fd (0-15 left to stdin/out/err + headroom)      */
#define SI_FD_SEALED 1u                /* a fd on a sealed-image regular file                            */
#define SI_FD_DIR    2u                /* a fd on a sealed-image directory (getdents64)                  */
#define SI_FD_RECORD 3u                /* a fd routed to the P3b-2 record filesystem (mounted beside)    */
#define SI_FD_REC    4u                /* C7 P3b-4g: the record-pen/body-read fd on "/rec/record"        */
#define SI_FD_RECSRC 5u                /* C7 P3b-4g: a body-read fd on record-disk CONTENT (gate source) */

struct si_header {                      /* the archive header (16 bytes)                                 */
    char     magic[8];
    uint32_t version;
    uint32_t count;
} __attribute__((packed));

struct si_entry {                       /* one fixed 128-byte directory entry                            */
    char     path[SI_PATH_MAX];         /* the absolute path, NUL-padded (104)                           */
    uint64_t offset;                    /* byte offset from the image start of this file's bytes (104)   */
    uint64_t length;                    /* byte length (112)                                             */
    uint32_t flags;                     /* bit0 = directory (120)                                        */
    uint32_t mtime;                     /* (124) the file's mtime, seconds — a 32-bit value, exactly the
                                         * timestamp-.pyc source-stamp format (C7 P3b-4c): CPython stats a
                                         * .py (st_mtime+st_size) and validates the __pycache__ .pyc against
                                         * it, so fstat/newfstatat serve the staged mtime or CPython would
                                         * recompile (open the .py). 0 for a directory. -> sizeof 128      */
} __attribute__((packed));

const uint8_t *g_img;                   /* the sealed image base (read by serve_mmap for file-backed maps)*/
uint32_t g_img_len;
static const struct si_entry *g_entries;
static uint32_t g_entry_count;
int g_dyn_fs_on;                        /* 1 during the floor3 dynamic run (routes the FS ops)           */
static int g_live_walk;                 /* a path outside the sealed+record sets was SERVED (a fabricated
                                         * live walk) — MUST stay 0; PLANT_LIVE_WALK sets it (A4 NOWALK)  */
static uint32_t g_outside_refusals;     /* paths outside both sets refused ENOENT (positive control)     */
static struct { uint8_t used, kind; uint32_t entry; uint64_t cursor; } g_fds[SI_MAX_FD];

static int si_streq(const char *a, const char *b) {
    uint32_t i = 0;
    for (; i < SI_PATH_MAX; i++) { if (a[i] != b[i]) { return 0; } if (a[i] == '\0') { return 1; } }
    return 1;
}

/* resolve an absolute path to a sealed-image entry index, or -1. */
static int si_find(const char *path) {
    if (!g_entries) { return -1; }
    for (uint32_t i = 0; i < g_entry_count; i++) {
        if (si_streq(g_entries[i].path, path)) { return (int)i; }
    }
    return -1;
}

/* ══ C7-MAINT-5B (A2) — STAT IDENTITY IS A PROPERTY OF THE FILE ═══════════════════════════════════════
 * Each served file answers ONE st_ino, derived from a stable per-file source, the SAME from a path
 * stat, an fstat through any open handle, and a re-open on another slot; two different files never
 * share one. st_dev is one constant (SI_ST_DEV). Three disjoint namespaces so a record file, a tree
 * file and a tree directory never collide (the sealed image keeps its own entry+1, all < REC_INO_BASE).
 *   record disk : REC_INO_BASE + the entry's TABLE INDEX (fs_name_index; unique for files AND dirs).
 *   tree file   : TREE_INO_BASE + the archive ENTRY INDEX (unique per file).
 *   tree dir    : TREE_DIR_INO_BASE + a stable fold of the dir path (dirs are implicit in the archive).
 * g_fd_ino carries the ino computed AT OPEN for fds whose identity is not re-derivable from a stored
 * name (tree files: the archive index; record content whose name the fd does not keep). Every OTHER
 * record-disk fd re-derives from its stored name so a re-open on a new slot lands the same number. */
#define SERVE_EBADF       ((uint64_t)(-9))         /* C7-MAINT-5B (A2/A3): a descriptor the body does not know */
#define REC_INO_BASE      0x0000000000100000ull   /* record-disk names (table index 0..2047)            */
#define TREE_INO_BASE     0x0000000000200000ull   /* tree-archive files (entry index)                   */
#define TREE_DIR_INO_BASE 0x0000000000400000ull   /* tree-archive directories (path fold, masked)       */
static uint64_t g_fd_ino[SI_MAX_FD];              /* an fd's file ino, set at open where name-derivation
                                                   * is not available (tree files, record content)      */

/* the record-disk ino for a caller-named record entry (by name). Absent -> a distinct high sentinel so
 * a stat of a vanished name never collides with a live entry's index. */
static uint64_t rec_ino_of_name(const char *name) {
    int ix = fs_name_index(name);
    return REC_INO_BASE + (uint64_t)(ix >= 0 ? (uint32_t)ix : (BFS_MAX_ENTRIES + 1u));
}

/* a stable fold of a tree directory path (djb2). Tree directories are implicit (no archive entry), so
 * their identity is derived from the path itself — the same for a path stat and an fstat of its fd. */
static uint64_t tree_dir_ino(const char *p) {
    uint64_t h = 5381u;
    for (uint32_t i = 0; p[i] && i < 128u; i++) { h = ((h << 5) + h) ^ (uint8_t)(unsigned char)p[i]; }
    return TREE_DIR_INO_BASE + (h & 0x00000000000FFFFFull);
}

/* ══ C7-MAINT-5B (A1) — NORMALIZE A /rec-STRIPPED PATH, REFUSE AN ESCAPE ═════════════════════════════
 * Resolve '.' and '..' in the /rec-stripped path `rb` into `out` (a canonical relative path). CPython's
 * import of gov-os reaches signer.py as '/rec/tests/../src/kernel/signer.py' (os.path.dirname(__file__)
 * joined with '..'), so the finder must resolve the go-up before matching the archive/record entry.
 * Returns 0 on success; -1 when a '..' would climb ABOVE the /rec root (an escape out of the served
 * tree, refused — L21). PLANT_FINDER_NO_ESCAPE clamps the escaping '..' instead of refusing, so an
 * escape probe ('/rec/../src/kernel/signer.py') then resolves to a SERVED file and the refusal reds. */
static int si_norm_rec(const char *rb, char *out, uint32_t outsz) {
    uint32_t seg_off[64], nseg = 0, o = 0, i = 0;
    while (rb[i]) {
        uint32_t cs = i;
        while (rb[i] && rb[i] != '/') { i++; }
        uint32_t clen = i - cs;
        if (rb[i] == '/') { i++; }
        if (clen == 0) { continue; }                                   /* // or a leading/trailing '/'   */
        if (clen == 1 && rb[cs] == '.') { continue; }                  /* '.' — the current directory     */
        if (clen == 2 && rb[cs] == '.' && rb[cs + 1] == '.') {         /* '..' — climb one segment         */
            if (nseg == 0) {
#if defined(PLANT_FINDER_NO_ESCAPE)
                continue;                                              /* the fault: clamp (drop the '..') */
#else
                return -1;                                             /* escape above /rec: REFUSE (L21)  */
#endif
            }
            o = seg_off[--nseg];
            continue;
        }
        if (nseg >= 64) { return -1; }                                 /* too deep to normalize            */
        seg_off[nseg] = o;
        if (nseg > 0) { if (o + 1u >= outsz) { return -1; } out[o++] = '/'; }
        if (o + clen >= outsz) { return -1; }
        for (uint32_t k = 0; k < clen; k++) { out[o++] = rb[cs + k]; }
        nseg++;
    }
    out[o] = '\0';
    return 0;
}

/* the sealed-image entry a sealed-file fd refers to (0 for a non-sealed/invalid fd) — read by serve_mmap
 * to copy the file's bytes for a file-backed mapping. */
static const struct si_entry *si_fd_entry(uint64_t fd) {
    if (fd < SI_FD_BASE || fd >= SI_FD_BASE + SI_MAX_FD) { return 0; }
    uint32_t i = (uint32_t)fd - SI_FD_BASE;
    if (!g_fds[i].used || g_fds[i].kind != SI_FD_SEALED) { return 0; }
    return &g_entries[g_fds[i].entry];
}

/* ── THE REAL ADDRESS-SPACE MANAGER (C7 P3b-4f-i, L19) — P3b-4b's classification kept as the router; the
 * CANNED single-thread answers (brk/mmap a fixed VA, arch_prctl a no-op) REPLACED by real machinery:
 * distinct virtual addresses over the PMM/VMM, a growing break, the main-thread %fs base installed in the
 * machine. Used by BOTH the P3b-4b worker (its shapes unchanged; it never reads the returned address) AND
 * the P3b-4f-i static glibc prover (which runs on the metal and DOES). ──────────────────────────────────*/
#define MSR_FS_BASE 0xC0000100u
#define ARCH_SET_FS 0x1002u
#define CANON_LIMIT 0x0000800000000000ull   /* the low canonical half — a %fs base must sit below it */

static inline void serve_wrmsr(uint32_t msr, uint64_t val) {
    uint32_t lo = (uint32_t)val, hi = (uint32_t)(val >> 32);
    __asm__ volatile("wrmsr" : : "c"(msr), "a"(lo), "d"(hi));
}

/* arch_prctl(ARCH_SET_FS, base): REALLY write the machine's %fs base for the main thread (read back by
 * the machine on every thread-local access). PLANT_NO_FS_BASE leaves %fs unwritten → the program's first
 * thread-local access FAULTS (a real #PF, not a flag). A non-canonical base is declined (no #GP). */
static uint64_t serve_arch_prctl(uint64_t code, uint64_t base) {
    if (code == ARCH_SET_FS) {
#if defined(PLANT_NO_FS_BASE)
        (void)base;                          /* the fault: the main-thread %fs base is never installed */
#else
        if (base < CANON_LIMIT) {
            serve_wrmsr(MSR_FS_BASE, base);
            if (g_sched_on) { sched_set_current_fs(base); }   /* record it so a switch restores it per thread */
        }
#endif
    }
    return 0;                                /* arch_prctl returns 0 on success */
}

/* THE GROWING BREAK — a real program break over the PMM/VMM (glibc's main arena grows it with sbrk).
 * g_brk_base is the program's initial break (set by the loader, above the loaded image); brk(0) queries
 * the current break, brk(addr>cur) maps fresh zeroed user pages up to addr. No fixed address. */
static uint64_t g_brk_base;
static uint64_t g_brk_cur;
void serve_set_brk_base(uint64_t base) { g_brk_base = base; g_brk_cur = base; }

#if defined(BRIDGE) || defined(SOCKET_ACT)
/* C7 P3b-6c (ii/iii): the two resident enclosures share serve.c's single brk state, so the ring-0 bridge SAVES
 * the interpreter's (base,cur) before running the worker under its own map and RESTORES it after — else the
 * worker's brk would advance the shared cursor and the interpreter would resume with a hole in its own map's
 * heap. (mmap needs no save/restore: g_mmap_next is monotonic, so each enclosure's maps land at fresh VAs.) */
void serve_brk_save(uint64_t *base, uint64_t *cur) { *base = g_brk_base; *cur = g_brk_cur; }
void serve_brk_load(uint64_t base, uint64_t cur)    { g_brk_base = base;  g_brk_cur = cur; }

/* C7 P3b-6c (ii): serve.c's supervisor map READS (vmm_query) walk the BOOT map, but a bridge relay runs the
 * worker under its OWN map (B). vmm_map_user already WRITES the active map (g_umap); this makes the reads
 * agree, so the brk/mmap precision-1 "keep a present+user page" checks see the WORKER's map, not the boot
 * map (where the resident interpreter's pages live — which otherwise makes brk skip mapping in B and the
 * worker #PFs). Query the current CR3 (== g_umap). Non-BRIDGE builds keep vmm_query (byte-identical). */
static uint64_t serve_active_cr3(void) { uint64_t c; __asm__ volatile("mov %%cr3, %0" : "=r"(c)); return c; }
#if defined(PLANT_SA_BOOT_BOUND_UNMAP)
/* C7 P3b-6c(iii) A4 PLANT: the unmap act stays BOOT-BOUND under the bridge — the read walks the boot map
 * (the worker's page is absent there -> owned==0 -> the frame is NEVER freed) and the unmap zeroes a boot-map
 * PTE that does not exist. Over REPEATED relays an unfreed frame per relay drains the pool MEASURABLY (a real
 * MemoryError / the low-water falling), so the fix carries its own failing check (L19). */
#define VMM_QUERY_ACTIVE(va) vmm_query(va)
#define VMM_UNMAP_ACTIVE(va) vmm_unmap(va)
#else
#define VMM_QUERY_ACTIVE(va) vmm_query_in(serve_active_cr3(), (va))
#if defined(SOCKET_ACT)
/* C7 P3b-6c(iii) A4: the unmap follows the ACTIVE map (the worker's own), so a reclaimed frame is unmapped
 * where it was owned — no stale mapping to a freed frame across repeated relays, the pool holds steady. */
#define VMM_UNMAP_ACTIVE(va) vmm_unmap_in(serve_active_cr3(), (va))
#else
#define VMM_UNMAP_ACTIVE(va) vmm_unmap(va)   /* BRIDGE (slice ii): unmaps stay boot-bound, byte-identical */
#endif
#endif
#else
#define VMM_QUERY_ACTIVE(va) vmm_query(va)
#define VMM_UNMAP_ACTIVE(va) vmm_unmap(va)
#endif

static void frame_pool_sample(void);     /* fwd decl — the precision-3 instrument is defined below serve_mmap */

/* C7 P3b-5a-vii (EXTEND) — THE BODY RECLAIMS BRK-DOWN FRAMES. glibc's malloc_trim issues a NEGATIVE sbrk
 * (a brk-DOWN, to<from) to return heap memory. The pre-fix act lowered g_brk_cur on a shrink WITHOUT
 * unmapping or freeing the shrunk pages, so their frames LEAKED; then the next grow mapped FRESH frames
 * OVER those still-present pages, ORPHANING the old ones — CPython's 77 kernel builds cycle grow/shrink,
 * so the leak grew unbounded, drained the 256 MiB pool, and test_ep26 red by MemoryError. Fixed at the TWO
 * folded sites the leak lives at (board :4377): (1) a brk-DOWN frees each page ABOVE the new break's
 * rounded-up boundary back to the allocator, PTE-guarded exactly like serve_munmap — a frame is freed ONLY
 * when its page read PRESENT (0x1) and USER (0x4), so the page HOLDING the new break (below `to`) is never
 * touched, an absent or supervisor page owns no reclaimable frame, and a re-shrink sees a cleared PTE and
 * frees nothing (never a double-free); each break page's frame is pmm_alloc'd, zero-filled and uniquely
 * mapped at ONE VA (never a sealed-image overlay, which reuses at the SAME page), so freeing ends its only
 * mapping and no reserved or shared frame is ever freed. (2) the GROWING side maps a fresh frame ONLY over
 * an ABSENT page — a page already PRESENT and USER is KEPT, never re-mapped over, so the grow can never
 * orphan an already-owned frame (defensive: after (1) the grow always meets absent pages). Together no path
 * in the break act loses a frame again. Page-TABLE intermediate frames accrue for process life and are NOT
 * reclaimed here (precision 3 — measured, not freed). PLANT_BRK_DOWN_LEAK restores the pre-fix act at BOTH
 * sites (no shrink-free AND an unguarded grow that orphans): a plant that CAN fail (the pool drains, a REAL
 * MemoryError), because with the grow-guard kept a shrink-only plant would merely reuse the pages and cap
 * the pool — a check that could not fail (L19). */
static uint64_t serve_brk(uint64_t addr) {
    if (g_brk_cur == 0) { return 0; }        /* uninitialized (a worker-only boot): a harmless query */
    if (addr == 0) { return g_brk_cur; }
    if (addr < g_brk_base) { return g_brk_cur; }
    uint64_t from = (g_brk_cur + 0xFFFull) & ~0xFFFull;
    uint64_t to   = (addr     + 0xFFFull) & ~0xFFFull;

    if (to < from) {                         /* a brk-DOWN — reclaim the frames above the new break */
#if !defined(PLANT_BRK_DOWN_LEAK)
        for (uint64_t pg = to; pg < from; pg += 0x1000ull) {
            uint64_t pte = VMM_QUERY_ACTIVE(pg);
            int owned = (pte & 0x1ull) && (pte & 0x4ull);      /* PRESENT and USER: an owned break frame */
            uint32_t f = (uint32_t)(pte & 0x000FFFFFFFFFF000ull);
            VMM_UNMAP_ACTIVE(pg);                              /* A4: unmap in the ACTIVE map (worker's own) */
            if (owned) { pmm_free(f); }                        /* return the owned frame to the allocator */
            frame_pool_sample();
        }
#endif
        /* PLANT_BRK_DOWN_LEAK: the shrunk pages are left mapped and their frames leak (the pre-fix act). */
        g_brk_cur = addr;
        return addr;
    }

    /* C7 P3b-6b A5: the lwIP worker's heap is bounded by LWIP_HEAP_BUDGET; the plant sizes it below the
     * 17,048 B high-water, so the connection's allocations starve (a real OOM, glibc falls back and fails). */
    if (g_serve_enclosure == ENCL_LWIP && to > from) {
        if (!lwip_heap_grant(to - from)) { return g_brk_cur; }
    }
    for (uint64_t pg = from; pg < to; pg += 0x1000ull) {
#if !defined(PLANT_BRK_DOWN_LEAK)
        uint64_t pte = VMM_QUERY_ACTIVE(pg);
        if ((pte & 0x1ull) && (pte & 0x4ull)) { continue; }   /* precision 1: KEEP a present+user page */
#endif
        uint32_t f = pmm_alloc();
        if (f == 0) { return g_brk_cur; }    /* OOM: the break does not grow (glibc falls back to mmap) */
        if (vmm_map_user(pg, (uint64_t)f) != 0) { pmm_free(f); return g_brk_cur; }
        uint8_t *z = (uint8_t *)phys_to_virt(f);
        for (int i = 0; i < 4096; i++) { z[i] = 0; }   /* break memory is zero-filled */
    }
    frame_pool_sample();                     /* precision 3: record the pool low-water after this grow burst */
    g_brk_cur = addr;
    return addr;
}

/* prlimit64(resource, ..., old_limit): write a sane rlimit into old_limit (a user pointer); new_limit is
 * ignored (the body sets no limits). RLIMIT_STACK: glibc sizes the main stack (cur 8 MiB, max infinity).
 * C7 P3b-5a-vi (A1) — RLIMIT_NOFILE: report the SERVED open-fd ceiling (SI_MAX_FD, grown to Linux's 1024
 * soft shape), so a caller that probes its fd ceiling sees the width the body actually holds. */
#define RLIMIT_STACK_   3u
#define RLIMIT_NOFILE_  7u
static uint64_t serve_prlimit64(uint64_t resource, uint64_t old_limit_ptr) {
    if (old_limit_ptr != 0 && old_limit_ptr < CANON_LIMIT) {
        uint64_t *rl = (uint64_t *)(uintptr_t)old_limit_ptr;   /* {rlim_cur, rlim_max} */
        if (resource == RLIMIT_NOFILE_) {
            rl[0] = (uint64_t)SI_MAX_FD;    /* soft: the served open-fd ceiling == the table width */
            rl[1] = (uint64_t)SI_MAX_FD;    /* hard: the same — the body's table is fixed-width */
        } else {
            rl[0] = 8ull * 1024ull * 1024ull;   /* RLIMIT_STACK (and every other): 8 MiB / infinity */
            rl[1] = ~0ull;
        }
    }
    return 0;
}

/* THE ANONYMOUS-MAP BUMP ALLOCATOR — distinct virtual addresses, real pages over the PMM/VMM. A HIGH
 * canonical base (like a real Linux mmap region), so glibc's thread-stack bounds arithmetic — which
 * sanity-checks stack addresses against the program's other regions — sees the same address shape it does
 * on a real kernel (a low base tripped glibc's stacksize computation to zero, C7 P3b-4f-ii). */
#define SERVE_MMAP_BASE 0x700000000000ull    /* the prover's anonymous-map region, bumped upward */
static uint64_t g_mmap_next;

/* C7 P3b-5a-vii — THE FRAME-POOL HIGH-WATER INSTRUMENT (precision 3, board :4371). g_frame_free_low tracks
 * the LOWEST free-frame count seen across the run (== the PEAK frame usage), sampled after each map/unmap
 * act. It is emitted at exit_group beside the boot-time count (kmain's "PMM: init, free frames") so the
 * close MEASURES the page-table accrual (boot-free minus at-exit — vmm intermediate frames accrue for
 * process life and are NOT reclaimed here) and shows the pool sustained the churn (low-water > 0 == never
 * exhausted). It RECLAIMS NOTHING — a pure observation, no behaviour change. */
static uint32_t g_frame_free_low = 0xFFFFFFFFu;
static void frame_pool_sample(void) {
    uint32_t n = pmm_free_count();
    if (n < g_frame_free_low) { g_frame_free_low = n; }
}

/* the body's own pid for the single-writer-lock act (a constant — the body is the sole writer, disk.h). */
#define BODY_PID 1u

static int g_fs_ready = -1;           /* the body's disk is present and mounted (best-effort file acts)  */
static int serve_fs_ready(void) {
    if (g_fs_ready < 0) {
        g_fs_ready = (ata_present() && fs_mount() == 0) ? 1 : 0;
    }
    return g_fs_ready;
}

/* ── append ONE UNSIGNED row (sig==0, chain==0 — the body holds no key, precision a) ──────────────────*/
static void serve_append(uint32_t num, uint32_t cat, uint32_t verdict, uint64_t arg, uint64_t ans) {
    uint32_t sig = 0, chain = 0;
#if defined(PLANT_BODY_SIGNS_ROW)
    if (cat == CAT_ACT) { sig = 1; }        /* the fault: an acts'-share row carries a signature (a key) */
#endif
#if defined(PLANT_ACT_ROW_IN_CHAIN)
    if (cat == CAT_ACT) { chain = 1; }      /* the fault: an acts'-share row appended into the signed chain */
#endif
    if (g_serve_rows < SERVE_TRAIL_MAX) {
        g_serve_trail[g_serve_rows].seq     = g_serve_rows;
        g_serve_trail[g_serve_rows].num     = num;
        g_serve_trail[g_serve_rows].cat     = cat;
        g_serve_trail[g_serve_rows].verdict = verdict;
        g_serve_trail[g_serve_rows].arg     = arg;
        g_serve_trail[g_serve_rows].ans     = ans;
        g_serve_trail[g_serve_rows].sig     = sig;
        g_serve_trail[g_serve_rows].chain   = chain;
        g_serve_rows++;
    }
}

/* ── the twelve acts' share, performed by the act machinery (each witnessed as a CAT_ACT row) ─────────*/

/* memory (act 12): MAP_SHARED requested; served anonymous-PRIVATE (Q11 — the act promises anonymous,
 * not fork-sharing; the body has no fork). REAL machinery: distinct virtual addresses, real zeroed pages
 * over the PMM/VMM, `len` rounded to whole pages. PLANT_FIXED_VA returns the SAME base for every map →
 * two maps ALIAS → the program's own bytes are clobbered (a real failure, L19, not a flag). */
#define SI_MAP_FIXED 0x10u                /* MAP_FIXED — the caller demands this exact address            */
#define SI_PROT_READ  0x1u                /* PROT_READ  — the range may be read                          */
#define SI_PROT_WRITE 0x2u                /* PROT_WRITE — the range may be written                        */
static uint64_t serve_mmap(uint64_t addr, uint64_t len, uint64_t prot, uint64_t flags, uint64_t fd, uint64_t offset) {
#if defined(PLANT_MEM_FORK_SHARED)
    g_mem_served_private = 0;             /* the fault: the memory act serves fork-shareable memory */
#else
    g_mem_served_private = 1;             /* served anonymous-PRIVATE — the body has no fork (Q11) */
#endif
    if (g_mmap_next == 0) { g_mmap_next = SERVE_MMAP_BASE; }
    uint64_t pages = (len + 0xFFFull) >> 12;
    if (pages == 0) { pages = 1; }

    /* FILE-BACKED vs ANONYMOUS. In the floor3 dynamic run, ld.so maps libc from the sealed image: a
     * MAP_PRIVATE of a sealed fd (the reservation at offset 0, then MAP_FIXED overlays at their file
     * offsets, then an anonymous MAP_FIXED bss tail). A sealed fd that is NOT anonymous maps the file's
     * bytes; anything else is anonymous zero-fill. With g_dyn_fs_on clear (P3b-4b / floor / floor2) the
     * old behaviour stands byte-identical: anonymous, picked from the bump, the plants preserved. */
    int anon = ((flags & MAP_ANONYMOUS) != 0) || (fd == (uint64_t)(-1));
    const struct si_entry *se = (g_dyn_fs_on && !anon) ? si_fd_entry(fd) : 0;
    int fixed = g_dyn_fs_on && (flags & SI_MAP_FIXED) && addr != 0;

    /* RESERVATION IS NOT COMMITMENT (C7-MAINT-5B, design/54 §5 L18/L19). serve_mmap now RECEIVES prot. An
     * anonymous PROT_NONE map (not a FIXED overlay) RESERVES address space: the range is consumed
     * (g_mmap_next advanced past it and a guard page) but NO frame is allocated and NOTHING is mapped.
     * glibc's per-thread malloc arena reserves 64 MiB of PROT_NONE it may never touch; backing it as if
     * committed exhausts the 256 MiB pool (the ep28c_w1 wall). The protection act that later makes a
     * sub-range ACCESSIBLE (serve_mprotect) is the COMMIT point where the eager law runs. Accessible-
     * implies-backed stays UNIVERSAL: a reservation is not accessible, so a ring-3 touch of it has no legal
     * reading and faults as an enclosure violation exactly as today (L18 untouched); nothing faults in (no
     * demand paging — commitment is eager at the protection act, only RESERVATION is lazy). A direct R/W
     * anonymous map and a file-backed map back eagerly exactly as before. */
    int accessible = (prot & (SI_PROT_READ | SI_PROT_WRITE)) != 0;
#if !defined(PLANT_BACK_AT_RESERVE)
    if (anon && !fixed && !accessible) {
        uint64_t rbase = g_mmap_next;
        g_mmap_next = rbase + pages * 0x1000ull + 0x1000ull;   /* consume the range + a guard page */
        return rbase;                     /* RESERVE: no pmm_alloc, no vmm_map_user — nothing mapped */
    }
#endif
    /* PLANT_BACK_AT_RESERVE (A1/A2, one that CAN fail): a PROT_NONE reservation is BACKED eagerly (the
     * pre-fix behaviour) — the 768 MiB of arenas exhaust the pool, so ep28c_w1 reds by honest ENOMEM (A1);
     * and a touch of a "reservation" does NOT fault, so the A2 enforcement check reds (its worker fault
     * absent). Falling through to the eager loop below IS backing at reserve. */

    /* COMMITMENT: the lwIP heap budget (P3b-6b) is a COMMITMENT budget — a direct R/W anonymous map
     * (glibc's large-alloc mmap fallback) draws it; a PROT_NONE reservation, returned above, does not. */
    if (g_serve_enclosure == ENCL_LWIP && anon) {
        if (!lwip_heap_grant(pages * 0x1000ull)) { return (uint64_t)(-12); }   /* -ENOMEM (MAP_FAILED) */
    }

    uint64_t base;
    if (fixed) { base = addr & ~0xFFFull; }
    else {
        base = g_mmap_next;
#if defined(PLANT_FIXED_VA)
        base = SERVE_MMAP_BASE;           /* the fault: a FIXED address for every map (maps alias) */
#endif
    }

    for (uint64_t i = 0; i < pages; i++) {
        uint64_t page = base + i * 0x1000ull;
        uint64_t pte = VMM_QUERY_ACTIVE(page);
        uint32_t f;
        if (pte & 0x1ull) {               /* a FIXED overlay over an already-reserved page: reuse its frame */
            f = (uint32_t)(pte & 0x000FFFFFFFFFF000ull);
        } else {
            f = pmm_alloc();
            if (f == 0) { return (uint64_t)(-12); }    /* -ENOMEM (MAP_FAILED to glibc) */
            if (vmm_map_user(page, (uint64_t)f) != 0) { pmm_free(f); return (uint64_t)(-12); }
        }
        uint8_t *dst = (uint8_t *)phys_to_virt(f);
        if (se) {                         /* file-backed: the sealed file's bytes at (offset + page-in-map) */
            for (uint32_t k = 0; k < 4096u; k++) {
                uint64_t fpos = offset + (page - base) + k;
                dst[k] = (fpos < se->length) ? g_img[se->offset + fpos] : 0;   /* zero beyond EOF */
            }
        } else {                          /* anonymous memory is zero-filled (incl. ld.so's bss tail) */
            for (int k = 0; k < 4096; k++) { dst[k] = 0; }
        }
    }
#if !defined(PLANT_FIXED_VA)
    if (!fixed) {
        g_mmap_next = base + pages * 0x1000ull + 0x1000ull;   /* advance past a guard page — distinct VAs */
    }
#endif
    frame_pool_sample();                  /* precision 3: record the pool low-water after this alloc burst */
    return base;                          /* the mapped user address the act hands back */
}
/* C7 P3b-5a-vii — THE BODY RECLAIMS MUNMAP'D FRAMES. serve_munmap unmaps each page's virtual address AND
 * returns the physical frame it OWNS to the allocator, so heavy map-and-unmap churn no longer exhausts the
 * 256 MiB pool. The free is PTE-GUARDED (precision 1, board :4371): a frame is freed ONLY when the page was
 * mapped PRESENT (0x1) and USER (0x4) before the unmap — a program-owned frame. Every user frame is uniquely
 * mapped at ONE virtual address (map_segment / the stacks / serve_mmap each take a FRESH pmm_alloc'd frame;
 * the sealed image's bytes are COPIED into fresh frames, never mapped; a FIXED overlay reuses the frame
 * already under THAT SAME page), so unmapping a user page ends the ONLY mapping of its frame and freeing it
 * is correct — never a double-free (a re-unmap sees a zeroed PTE, PRESENT clear, and frees nothing), never a
 * free-while-shared (the sealed-image FIXED-overlay reservation reuses at the SAME VA, never a second one),
 * so the loader's mapping is never corrupted. A SUPERVISOR page (USER==0: the body's own SECRET_VA / identity
 * / direct map) and an ABSENT page (PRESENT==0, incl. the retained identity huge pages, which vmm_query reads
 * as 0) own no reclaimable program frame here and are left untouched. PAGE-TABLE intermediate frames (vmm
 * levels) accrue for process life and are NOT reclaimed here (precision 3 — vmm_unmap zeroes only the leaf). */
static uint64_t serve_munmap(uint64_t addr, uint64_t len) {
    if (addr == 0 || addr >= CANON_LIMIT) { return 0; }
    uint64_t pages = (len + 0xFFFull) >> 12;
    if (pages == 0) { pages = 1; }
    for (uint64_t i = 0; i < pages; i++) {
        uint64_t page = addr + i * 0x1000ull;
        uint64_t pte = VMM_QUERY_ACTIVE(page);
#if defined(PLANT_FRAME_LEAK)
        (void)pte;                              /* the fault (A1): unmap only — the frame LEAKS (the pre-fix
                                                 * behaviour). Heavy churn exhausts the 256 MiB pool and the
                                                 * heaviest module reds by MemoryError, a REAL mechanism. */
        vmm_unmap(page);
#elif defined(PLANT_FRAME_FREE_UNGUARDED)
        /* the fault (A2, precision 2): free WITHOUT the PRESENT+USER guard, taking a STILL-PRESENT
         * NEIGHBOUR's LIVE frame. The neighbour page stays mapped, so its live frame returns to the pool;
         * pmm_alloc later hands that live frame to a second map, the two mappings ALIAS, and the 4d dynamic
         * loader's libc corrupts (a REAL mechanism, NOT a silent double-free — L19; a plain double-free is a
         * no-op at pmm_free's bit-test and is refused as a check that cannot fail). */
        (void)pte;
        uint64_t nbr = VMM_QUERY_ACTIVE(page + 0x1000ull);
        vmm_unmap(page);
        if (nbr & 0x1ull) { pmm_free((uint32_t)(nbr & 0x000FFFFFFFFFF000ull)); }
#else
        int owned = (pte & 0x1ull) && (pte & 0x4ull);          /* PRESENT and USER: a program-owned frame */
        uint32_t f = (uint32_t)(pte & 0x000FFFFFFFFFF000ull);
        VMM_UNMAP_ACTIVE(page);                                /* A4: unmap in the ACTIVE map (worker's own) */
        if (owned) { pmm_free(f); }                            /* return the owned frame to the allocator */
#endif
        frame_pool_sample();
    }
    return 0;
}

/* C7-MAINT-5B — THE PROTECTION ACT IS THE COMMIT POINT (design/54 §5 L18/L19). serve_mmap RESERVES an
 * anonymous PROT_NONE range with no frame; the protection act that makes a sub-range ACCESSIBLE (gains
 * READ or WRITE) COMMITS it — for each page in the range not already present, the SAME eager law runs
 * (pmm_alloc + vmm_map_user + zero-fill), returning honest ENOMEM when the pool is short. A protection act
 * that does NOT make a range accessible (drops to PROT_NONE, or re-protects an already-present range) is a
 * no-op success. Commitment stays EAGER at the protection act — no page ever faults in (no demand paging);
 * only RESERVATION is lazy, so accessible-implies-backed stays universal and a ring-3 fault stays an
 * unambiguous enclosure violation (L18 untouched). The lwIP commit budget (P3b-6b) is drawn here too, so a
 * commitment BY PROTECTION draws it exactly as a direct R/W anonymous map does. A page already present
 * (a FIXED overlay's frame, a direct-mapped page, a re-protect) is left as it is — never re-mapped. */
static uint64_t serve_mprotect(uint64_t addr, uint64_t len, uint64_t prot) {
    if (addr == 0 || addr >= CANON_LIMIT) { return 0; }
#if defined(PLANT_MPROTECT_NOOP)
    (void)prot; (void)len;
    return 0;                                  /* the fault (A3): the protection act commits NOTHING — a
                                                * subsequent write to the "committed" range faults */
#else
    int accessible = (prot & (SI_PROT_READ | SI_PROT_WRITE)) != 0;
    if (!accessible) { return 0; }             /* not made accessible — no commit, a no-op success */
    uint64_t base = addr & ~0xFFFull;
    uint64_t end  = (addr + len + 0xFFFull) & ~0xFFFull;
    for (uint64_t page = base; page < end; page += 0x1000ull) {
        uint64_t pte = VMM_QUERY_ACTIVE(page);
        if (pte & 0x1ull) { continue; }        /* already present (committed / overlaid) — leave it */
        if (g_serve_enclosure == ENCL_LWIP) {  /* commitment by protection draws the lwIP budget (P3b-6b) */
            if (!lwip_heap_grant(0x1000ull)) { return (uint64_t)(-12); }
        }
        uint32_t f = pmm_alloc();
        if (f == 0) { return (uint64_t)(-12); }                    /* -ENOMEM, honest when the pool is short */
        if (vmm_map_user(page, (uint64_t)f) != 0) { pmm_free(f); return (uint64_t)(-12); }
        uint8_t *z = (uint8_t *)phys_to_virt(f);
        for (int k = 0; k < 4096; k++) { z[k] = 0; }               /* committed memory is zero-filled */
    }
    frame_pool_sample();
    return 0;
#endif
}

/* entropy (act 7): served from the body's OWN source (P3b-3 CSPRNG). The GRND_NONBLOCK draw is the
 * startup hash-seed, served AT BRING-UP before the entropy act's layer is reachable (the sequencing
 * constraint) — the body's source is already up. The blocking draw is the entropy act proper. */
static uint64_t serve_getrandom(uint64_t ubuf, uint64_t nbytes, uint64_t flags) {
    uint32_t n = (uint32_t)nbytes;
    if (flags & GRND_NONBLOCK) {
#if defined(PLANT_ENTROPY_NOT_AT_BRINGUP)
        g_entropy_at_bringup = 0;         /* the fault: the bring-up draw is deferred (layer not up) */
        return (uint64_t)(-11);           /* -EAGAIN, as a body that has no entropy at bring-up returns */
#else
        g_entropy_at_bringup = entropy_seed_nonzero();   /* real chance from the body's source, at bring-up */
#endif
    }
    /* REAL machinery: draw n unpredictable bytes into the CALLER's buffer (glibc reads them). A worker's
     * %rsp buffer is a mapped user page; the guard declines a non-canonical/absent pointer. */
    if (ubuf != 0 && ubuf < CANON_LIMIT && n > 0) {
        entropy_draw((uint8_t *)(uintptr_t)ubuf, n);
    } else {
        uint8_t tmp[16];
        entropy_draw(tmp, (n > sizeof(tmp)) ? (uint32_t)sizeof(tmp) : n);
    }
    /* the answer echoes the byte count served (getrandom's own return shape). */
    return (uint64_t)n;
}

/* concurrency (act 8): the wait is FUTEX_WAIT_BITSET_PRIVATE|FUTEX_CLOCK_REALTIME (Q-D). On a
 * single-writer body with no contender the wait returns at once; the SHAPE is what bites. */
static uint64_t serve_futex(uint64_t op) {
#if defined(PLANT_FUTEX_WRONG_SHAPE)
    g_futex_shape_ok = 0;                 /* the fault: the body serves a non-PRIVATE, non-bitset wait */
#else
    g_futex_shape_ok = ((op & FUTEX_WAIT_SHAPE) == FUTEX_WAIT_SHAPE) ? 1 : 0;
#endif
    return 0;                             /* no contender on a single-writer body */
}

/* C7 P3b-5a-vi (A2) — THE CLOCK_REALTIME EPOCH BASE. The recording-clock is a TRUE Unix epoch: the CMOS RTC
 * read ONCE at first use (clock.c rtc_read, the full civil date, qemu -rtc base=utc) converted to seconds
 * since 1970, MINUS the monotonic ns already elapsed at that read — so CLOCK_REALTIME == base + sched_now_ns()
 * is the epoch time at every later read, its rate the same monotonic tick (no drift between the two clocks).
 * The base is captured once and reused by the futex deadline conversion (same offset, so the 4f-ii coupling
 * agrees). CLOCK_MONOTONIC stays sched_now_ns() (since-boot), untouched. */
static uint64_t g_rt_base_ns;
static int      g_rt_base_set;
static uint64_t serve_rt_base_ns(void) {
    if (!g_rt_base_set) {
        struct wallclock w;
        rtc_read(&w);
        uint64_t epoch_ns = clock_epoch_seconds(&w) * 1000000000ull;
        uint64_t mono_ns  = sched_now_ns();
        g_rt_base_ns = epoch_ns - mono_ns;   /* base + sched_now_ns() == epoch_ns at this instant */
        g_rt_base_set = 1;
    }
    return g_rt_base_ns;
}

/* recording-clock (act 5) + commit-window (act 6): on a vDSO-less body the READS are real crossings
 * (a cost, not a break — witnessed as rows). Served from the P3b-3 sources. */
static uint64_t serve_clock_gettime(uint64_t clockid, uint64_t ts_ptr) {
    /* C7 P3b-4f-ii: with the concurrency floor active, glibc reads a REAL timespec here (a threaded
     * program's sem_timedwait computes its absolute deadline from it). CLOCK_MONOTONIC lays sched_now_ns
     * (since-boot), the base the scheduler's timed-wait also reads. C7 P3b-5a-vi (A2): CLOCK_REALTIME lays a
     * TRUE epoch (the RTC-derived base + sched_now_ns), so a witnessed arrival stamps a real 2026 calendar
     * time and the estate's TWO-TIMES rule holds against real decision times; the futex dispatch converts a
     * REALTIME deadline back to the scheduler's monotonic frame under the SAME base (the coupling KEPT). */
    if (g_sched_on && ts_ptr && ts_ptr < CANON_LIMIT) {
        uint64_t ns;
        if (clockid == CLOCK_MONOTONIC) {
            ns = sched_now_ns();               /* the commit-window: since-boot, unchanged */
        } else {                               /* CLOCK_REALTIME (the recording-clock): a true epoch */
#if defined(PLANT_REALTIME_SINCE_BOOT)
            ns = sched_now_ns();               /* the fault: the pre-5a-vi ~1970 clock -> TWO-TIMES reds */
#else
            ns = serve_rt_base_ns() + sched_now_ns();
#endif
        }
        volatile uint64_t *ts = (volatile uint64_t *)(uintptr_t)ts_ptr;
        ts[0] = ns / 1000000000ull;        /* tv_sec  */
        ts[1] = ns % 1000000000ull;        /* tv_nsec */
        return 0;                          /* clock_gettime returns 0 on success */
    }
    if (clockid == CLOCK_MONOTONIC) {
        /* C7 P3b-6b: the borrowed lwIP worker's sys_now reads the TIMESPEC (not the return), and it runs
         * with no scheduler — so fill the buffer from the body's tick clock (ticks advance because
         * floor_net_run runs the PIT). Scoped to ENCL_LWIP: every other caller keeps the old bare return. */
        if (g_serve_enclosure == ENCL_LWIP && ts_ptr && ts_ptr < CANON_LIMIT) {
            volatile uint64_t *ts = (volatile uint64_t *)(uintptr_t)ts_ptr;
            uint64_t ms = g_lwip_tsc_per_ms ? ((rdtsc() - g_lwip_tsc_base) / g_lwip_tsc_per_ms)
                                            : (sched_now_ns() / 1000000ull);  /* fallback: the tick clock */
            ts[0] = ms / 1000ull;              /* tv_sec  */
            ts[1] = (ms % 1000ull) * 1000000ull;   /* tv_nsec */
            return 0;
        }
        return mono_read();
    }
    struct wallclock w;
    rtc_read(&w);                          /* the recording-clock (wall) read */
    return ((uint64_t)w.hour << 16) | ((uint64_t)w.minute << 8) | (uint64_t)w.second;
}
/* the commit-window sleep: an ABSOLUTE monotonic deadline (clock_nanosleep MONOTONIC TIMER_ABSTIME). */
static uint64_t serve_clock_nanosleep(uint64_t clockid, uint64_t flags) {
    (void)clockid;
#if defined(PLANT_COMMIT_NOT_ABSOLUTE)
    g_commit_absolute = 0;                 /* the fault: the deadline is served non-absolute */
#else
    g_commit_absolute = (flags == TIMER_ABSTIME) ? 1 : 0;
#endif
    (void)mono_read();                     /* the commit-window source (no real sleep needed on the metal) */
    return 0;
}

/* the record acts (1-4, 10, 11): routed to bodyfs when a disk is present (the same performers P3b-2
 * proved), classified by PURPOSE from the openat flags. Best-effort: the crossing is WITNESSED whether
 * or not the disk op succeeds — the load-bearing property is the unsigned witnessing, not disk depth. */
static const uint8_t SERVE_RECORD[] = { 'p','3','b','4','b' };
static uint64_t serve_file_act(uint32_t num, uint64_t a0, uint64_t a1, uint64_t a2) {
    (void)a0; (void)a1;
    if (!serve_fs_ready()) { return 0; }   /* no disk this boot — the crossing is still classified + rowed */
    switch (num) {
    case SYS_openat: {
        uint32_t start = 0;
        if (a2 & O_APPEND) {               /* record-pen: append to the append-only record */
            fs_record_append(SERVE_RECORD, (uint32_t)sizeof(SERVE_RECORD), &start);
            return (uint64_t)start;
        }
        if (a2 & O_TRUNC) {                /* atomic-write-once: a blob written once */
            fs_blob_write_once("p3b4b-blob", SERVE_RECORD, (uint32_t)sizeof(SERVE_RECORD));
            return 0;
        }
        return 0;                          /* body-read / founding-pack-read open */
    }
    case SYS_write:  return (uint64_t)sizeof(SERVE_RECORD);   /* the write direction */
    case SYS_read: {
        uint8_t out[64]; uint32_t olen = 0;
        struct bfs_entry *rec = fs_find("record");
        if (rec) { fs_record_read(rec->start_sector, out, sizeof(out), &olen); }
        return (uint64_t)olen;             /* read-back / body-read */
    }
    case SYS_fdatasync:
    case SYS_fsync:  ata_flush(); return 0;                   /* the durability barrier */
    case SYS_newfstatat: return fs_find("record") ? 0 : SERVE_ENOSYS;   /* exists */
    case SYS_unlink: fs_remove("p3b4b-blob"); return 0;      /* the remove act (a blob, never the record) */
    case SYS_getdents64: {
        char names[8][BFS_NAME_MAX];       /* C7 P3b-5a-ii: fs_walk surfaces full-width path names */
        int c = fs_walk(names, 8);         /* the body-read walk */
        return (uint64_t)(c < 0 ? 0 : c);
    }
    default: return 0;
    }
}

/* ════════════════════════════════════════════════════════════════════════════════════════════════════
 * C7 P3b-4d — THE SEALED-IMAGE FILESYSTEM operations + the record FS mounted beside (design/54 §7 P3b-4d).
 * Served ONLY while g_dyn_fs_on; ld.so opens libc.so (and the companions) by path, reads the ELF header
 * (read), the phdrs (pread64), fstat's the size, and maps the segments (mmap, file-backed, above). A path
 * OUTSIDE the sealed set (and not a record name) is refused ENOENT — NO live host-filesystem walk
 * (Q15/:4134). getdents64 over a sealed directory LISTS it (the image is staged carrying its entries).
 * ════════════════════════════════════════════════════════════════════════════════════════════════════*/

/* the P3b-2 record filesystem MOUNTED BESIDE — a record name lives in a DISTINCT namespace from the sealed
 * library paths. ld.so never opens one; the beside-check proves the writable record is reachable alongside
 * the read-only image, and that no sealed path collides with a record name. */
static int si_is_record_name(const char *path) {
    return si_streq(path, "/record") || si_streq(path, "record");
}

/* under PLANT_FS_COLLIDE the record namespace SHADOWS the sealed set: a sealed library path is ALSO served
 * by the record FS (a collision). ld.so then reads the empty record for libc and cannot load it, and the
 * beside-check's collision probe fires. */
static int si_collides_as_record(int sealed_idx) {
#if defined(PLANT_FS_COLLIDE)
    return (sealed_idx >= 0) && !(g_entries[sealed_idx].flags & SI_DIR_FLAG);   /* sealed files shadowed */
#else
    (void)sealed_idx; return 0;
#endif
}

static int si_fd_alloc(uint8_t kind, uint32_t entry) {
    for (uint32_t i = 0; i < SI_MAX_FD; i++) {
        if (!g_fds[i].used) {
            g_fds[i].used = 1; g_fds[i].kind = kind; g_fds[i].entry = entry; g_fds[i].cursor = 0;
            return (int)(SI_FD_BASE + i);
        }
    }
    return -1;
}
static int si_fd_idx(uint64_t fd) {
    if (fd < SI_FD_BASE || fd >= SI_FD_BASE + SI_MAX_FD) { return -1; }
    uint32_t i = (uint32_t)fd - SI_FD_BASE;
    return g_fds[i].used ? (int)i : -1;
}

/* "/rec/<basename>" -> the basename (the record-disk name), or NULL if `path` is not in the /rec/
 * namespace. Unconditional (C7 P3b-5a-ii): the namespace acts and the body-side self-check need it in
 * the plain build; the GATE_ON_BODY resolver uses it too. A short/odd path fails the NUL-vs-prefix
 * compare and returns NULL — no read past the string. */
static const char *si_rec_basename(const char *path) {
    static const char pfx[5] = { '/','r','e','c','/' };
    if (!path) { return 0; }
    for (int k = 0; k < 5; k++) { if (path[k] != pfx[k]) { return 0; } }
    return path + 5;
}

/* C7-MAINT-5B (A2) — 1 iff `path` names the record-tree ROOT exactly: "/rec" or "/rec/". The bare root is
 * where CPython's importlib LISTS /rec (a sys.path entry) to discover the top-level packages (`tests`,
 * `src`). Unlike a "/rec/<name>" path it has no basename after the prefix, so si_rec_basename returns NULL
 * for it and the /rec resolver never sees it — the root is recognized here explicitly. */
static int si_is_rec_root(const char *path) {
    if (!path) { return 0; }
    if (!(path[0] == '/' && path[1] == 'r' && path[2] == 'e' && path[3] == 'c')) { return 0; }
    if (path[4] == '\0') { return 1; }
    return path[4] == '/' && path[5] == '\0';
}

/* ══ C7 P3b-5a-iii — THE WHOLE gov-os TREE AS CONTENT ON THE RECORD DISK, resolved by a finder (A6/I7)══
 * The whole gov-os source+tests tree is staged as ONE archive blob "govtree" on the BODYFS02 record
 * disk (mkdisk.py, GOVOS_TREE=1). A finder EXTENDING 4g's record-disk resolver (serve_openat_fs's
 * "/rec/" path) resolves "/rec/<tree-path>" to the file's EXACT bytes, STREAMED on demand from the disk
 * (files run to hundreds of KiB — opdefs.py, test_ep29.py — past any single buffer). A name not in the
 * archive refuses -ENOENT. This is the content path the on-body ledger (row P3b-5b) imports gov-os from
 * — the tree is CONTENT here, NEVER re-homed into src and NEVER inside the borrowed sealed interpreter
 * image (I7, two witness classes kept apart). The archive layout mirrors mkdisk.py byte-for-byte:
 *   blob sector 0  header: magic "GOVTREE1"(8) + version u32 + count u32 + total_len u32 (LE)
 *   blob sector 1+ entry table: count × 128B {path[116] nul-padded, offset u32, length u32, crc32 u32},
 *                  4 entries/sector; offset is bytes from the ARCHIVE start; crc32 == zlib.crc32.
 *   next sector    file-byte region: each file's bytes at its byte-exact offset.
 * Two plants keep the checks honest: PLANT_TREE_TAMPER (a served byte flipped -> the crc byte-compare
 * reds, L19) and PLANT_TREE_GHOST (a not-in-archive name served -> the ENOENT check reds). */
#define SI_FD_TREE   6u                 /* a body-read fd streaming a tree-archive file off the record disk */
#define SI_FD_TREEDIR 7u                /* C7 P3b-5b-i: an fd on a tree-archive DIRECTORY (getdents over it) */
#define TREE_PATH_MAX 116u              /* the fixed path field in a GOVTREE entry (>= the 92-byte max)  */
#define TREE_ENTRY_SIZE 128u            /* path[116] + 3 u32 (12) -> 4 entries / sector                  */
#define TREE_ENTRIES_PER_SECTOR (SECTOR_SIZE / TREE_ENTRY_SIZE)   /* = 4                                 */

/* one SI_FD_TREE fd's disk-byte base (blob start + the file's offset), byte length, and the archive's
 * stored crc32 for the file — parallel to g_fds, indexed the same. */
static struct { uint64_t base; uint32_t len; uint32_t crc; } g_tree_fd[SI_MAX_FD];
static uint8_t g_tree_scan[SECTOR_SIZE];   /* header/entry-table scan buffer (serve_tree_open)          */
static uint8_t g_tree_sec[SECTOR_SIZE];    /* the streaming read buffer (serve_tree_read_range)         */
static uint8_t g_tree_out[SECTOR_SIZE];    /* the self-check's own dst (must differ from g_tree_sec)    */
/* C7 P3b-5b-i: one SI_FD_TREEDIR fd's directory path (the /rec-stripped tree-path being listed), indexed
 * the same as g_fds — CPython's FileFinder lists /rec/src, /rec/tests to import gov-os (precision 3). */
static char g_treedir_path[SI_MAX_FD][TREE_PATH_MAX];

static uint32_t tree_rd_u32(const uint8_t *p) {          /* a little-endian u32, alignment-safe */
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* compare a nul-terminated path `want` to a 116-byte nul-padded field. */
static int tree_path_eq(const char *field, const char *want) {
    uint32_t i = 0;
    for (; i < TREE_PATH_MAX && want[i]; i++) { if (field[i] != want[i]) { return 0; } }
    if (i < TREE_PATH_MAX) { return field[i] == '\0'; }   /* want ended within the field — field must too */
    return 1;                                             /* want filled the whole field — full match */
}

/* stream up to `count` bytes of a tree-archive file from disk BYTE offset (base + cursor), spanning
 * sectors. Returns bytes copied. PLANT_TREE_TAMPER flips the file's FIRST served byte -> the byte-compare
 * (streamed crc vs stored/repo crc) reds; a genuine "tampered archive byte" caught by the compare. */
static uint32_t serve_tree_read_range(uint64_t base, uint32_t len, uint32_t cursor,
                                      uint8_t *dst, uint32_t count) {
    uint32_t remain = (cursor < len) ? (len - cursor) : 0u;
    uint32_t n = (count < remain) ? count : remain;
    uint64_t pos = base + cursor;
    uint32_t done = 0;
    while (done < n) {
        uint32_t lba  = (uint32_t)((pos + done) / SECTOR_SIZE);
        uint32_t soff = (uint32_t)((pos + done) % SECTOR_SIZE);
        if (ata_read_sector(lba, g_tree_sec) != 0) { break; }
        uint32_t c = SECTOR_SIZE - soff;
        if (c > n - done) { c = n - done; }
        for (uint32_t k = 0; k < c; k++) { dst[done + k] = g_tree_sec[soff + k]; }
        done += c;
    }
#if defined(PLANT_TREE_TAMPER)
    if (cursor == 0 && done > 0) { dst[0] ^= 0xFFu; }   /* the fault: one served byte differs from the archive */
#endif
    return done;
}

/* THE FINDER (extending 4g's): resolve "<tree-path>" (the /rec/-stripped path) against the "govtree"
 * archive on the record disk; on a hit, allocate an SI_FD_TREE fd (base/len/crc recorded) and return it.
 * -1 no tree archive / EMFILE; -2 the path is not in the archive (-ENOENT). */
static int serve_tree_open(const char *treepath) {
    struct bfs_entry *e = fs_find("govtree");
    if (!e) { return -1; }                                    /* no tree archive staged this boot */
    uint64_t ab = (uint64_t)e->start_sector * SECTOR_SIZE;    /* the archive's start byte on disk */
    if (ata_read_sector(e->start_sector, g_tree_scan) != 0) { return -1; }
    if (!mem_eq(g_tree_scan, "GOVTREE1", 8)) { return -1; }   /* not a GOVTREE archive */
    uint32_t count = tree_rd_u32(g_tree_scan + 12);           /* magic(8) + version(4) then count */
    for (uint32_t i = 0; i < count; i++) {
        if (i % TREE_ENTRIES_PER_SECTOR == 0) {               /* one directory sector holds 4 entries */
            uint32_t lba = e->start_sector + 1u + i / TREE_ENTRIES_PER_SECTOR;
            if (ata_read_sector(lba, g_tree_scan) != 0) { return -1; }
        }
        const uint8_t *ent = g_tree_scan + (i % TREE_ENTRIES_PER_SECTOR) * TREE_ENTRY_SIZE;
        if (tree_path_eq((const char *)ent, treepath)) {
            uint32_t off = tree_rd_u32(ent + TREE_PATH_MAX);
            uint32_t len = tree_rd_u32(ent + TREE_PATH_MAX + 4u);
            uint32_t crc = tree_rd_u32(ent + TREE_PATH_MAX + 8u);
            int fd = si_fd_alloc(SI_FD_TREE, 0);
            if (fd < 0) { return -1; }                        /* EMFILE */
            uint32_t idx = (uint32_t)fd - SI_FD_BASE;
            g_tree_fd[idx].base = ab + off; g_tree_fd[idx].len = len; g_tree_fd[idx].crc = crc;
            g_fd_ino[idx] = TREE_INO_BASE + (uint64_t)i;       /* C7-MAINT-5B (A2): per-file ino by tree index */
            return fd;
        }
    }
#if defined(PLANT_TREE_GHOST)
    { int fd = si_fd_alloc(SI_FD_TREE, 0);                    /* the fault: a not-in-archive name served */
      if (fd >= 0) { uint32_t idx = (uint32_t)fd - SI_FD_BASE;
                     g_tree_fd[idx].base = 0; g_tree_fd[idx].len = 0; g_tree_fd[idx].crc = 0; return fd; } }
#endif
    return -2;                                                /* -ENOENT: the name is not in the archive */
}

/* THE BODY-SIDE PROOF (A6): stage the whole tree as ONE archive, resolve a KNOWN file through the finder,
 * and prove its bytes are byte-identical (its streamed crc equals the crc mkdisk stored from the shipping
 * bytes — a check that CAN fail, PLANT_TREE_TAMPER); a not-in-archive name refuses -ENOENT (fallible,
 * PLANT_TREE_GHOST). The body also PRINTS each known file's (len, crc) so the test cross-checks byte-
 * identity against the REPO file off the body. Skips when no tree archive is staged (a non-TREE image). */
static const char TREE_KNOWN_SMALL[] = "src/body/serial.c";      /* a small hand-written source file  */
static const char TREE_KNOWN_LARGE[] = "src/kernel/opdefs.py";   /* > 64 KiB: proves streaming on demand */
static const char TREE_ABSENT[]      = "src/__gov-not-in-archive__.zzz";

static void serve_tree_report(const char *path, int *ok) {
    int fd = serve_tree_open(path);
    if (fd < 0) {
        serial_puts("TREE-FILE "); serial_puts(path); serial_puts(" MISSING\n");
        *ok = 0; return;
    }
    uint32_t idx = (uint32_t)fd - SI_FD_BASE;
    uint32_t len = g_tree_fd[idx].len, stored = g_tree_fd[idx].crc, got = 0;
    uint32_t crc = crc32_begin();
    for (;;) {
        uint32_t n = serve_tree_read_range(g_tree_fd[idx].base, len, got, g_tree_out, sizeof(g_tree_out));
        if (n == 0) { break; }
        crc = crc32_feed(crc, g_tree_out, n);            /* g_tree_out != g_tree_sec (no overlap) */
        got += n;
    }
    crc = crc32_final(crc);
    g_fds[idx].used = 0;                                      /* free the fd (the self-check's own use) */
    serial_puts("TREE-FILE "); serial_puts(path);
    serial_puts(" len=0x"); serial_puthex32(got);
    serial_puts(" crc=0x"); serial_puthex32(crc);
    serial_puts(" stored=0x"); serial_puthex32(stored); serial_puts("\n");
    if (got != len || crc != stored) { *ok = 0; }            /* byte-identity: streamed == the stored crc */
}

static void serve_tree_selfcheck(void) {
    if (!serve_fs_ready() || !fs_find("govtree")) {
        serial_puts("TREE-ACTS: SKIPPED (no tree archive)\n");
        return;
    }
    int ok = 1;
    serve_tree_report(TREE_KNOWN_SMALL, &ok);                 /* a known file, byte-identical to the repo */
    serve_tree_report(TREE_KNOWN_LARGE, &ok);                 /* a > 64 KiB file streamed on demand */
    int absent = (serve_tree_open(TREE_ABSENT) == -2);        /* a not-in-archive name -> ENOENT */
    if (!absent) { ok = 0; }
    serial_puts(absent ? "TREE-ENOENT: PASS\n" : "TREE-ENOENT: FAIL\n");
    serial_puts(ok ? "CHECK TREE-A6: PASS\n" : "CHECK TREE-A6: FAIL\n");
    serial_puts(ok ? "TREE-ACTS: PASS\n" : "TREE-ACTS: FAIL\n");
}

/* ══ C7 P3b-5b-i — THE TREE ARCHIVE SERVED BY LISTING (design/54 §7 P3b-5b, precision 3; archi :4303). ══
 * 5a's finder serves /rec/<tree-path> by PATH (serve_tree_open above). CPython's OWN import machinery ALSO
 * LISTS each sys.path directory (importlib os.listdir's /rec/src, /rec/tests once per import) and STATS the
 * candidate package directories — refuse the listing and every gov-os import fails (the 4x lesson). So the
 * finder is GENERAL over the archive's OWN directory table, never a hardcoded module list (the 7-module
 * _RecFinder of 4g retires for the ledger). The directory structure is IMPLICIT in the sorted file paths
 * (mkdisk.py stages files, not dir entries): an immediate child of directory D is either a FILE (a path
 * under D/ with no further "/") or a SUBDIR (the shared first segment after D/, emitted once). ════════════*/

/* 1 iff `field` (a 116-byte nul-padded entry path) is strictly UNDER directory `want` (nul-terminated);
 * on a hit *rem points at the remainder (the path after "want/"). */
static int tree_under_dir(const char *field, const char *want, const char **rem) {
    uint32_t i = 0;
    for (; want[i]; i++) { if (i >= TREE_PATH_MAX || field[i] != want[i]) { return 0; } }
    if (i >= TREE_PATH_MAX || field[i] != '/') { return 0; }   /* the directory separator */
    *rem = field + i + 1;
    return 1;
}

/* 1 iff `treepath` is a DIRECTORY in the govtree archive (a strict prefix of some entry's path). */
static int serve_tree_is_dir(const char *treepath) {
    struct bfs_entry *e = fs_find("govtree");
    if (!e || !treepath) { return 0; }
    if (treepath[0] == '\0') {                              /* C7-MAINT-5B (A2): the archive ROOT /rec is a directory */
#if defined(PLANT_TREE_ROOT_NOLIST)
        return 0;              /* the fault: the ROOT does not list -> os.listdir('/rec') raises, the import reds (L19) */
#else
        return 1;              /* the same sub-directory listing (serve_tree_getdents) extended to depth 0 */
#endif
    }
    if (ata_read_sector(e->start_sector, g_tree_scan) != 0) { return 0; }
    if (!mem_eq(g_tree_scan, "GOVTREE1", 8)) { return 0; }
    uint32_t count = tree_rd_u32(g_tree_scan + 12);
    for (uint32_t i = 0; i < count; i++) {
        if (i % TREE_ENTRIES_PER_SECTOR == 0) {
            uint32_t lba = e->start_sector + 1u + i / TREE_ENTRIES_PER_SECTOR;
            if (ata_read_sector(lba, g_tree_scan) != 0) { return 0; }
        }
        const char *ent = (const char *)(g_tree_scan + (i % TREE_ENTRIES_PER_SECTOR) * TREE_ENTRY_SIZE);
        const char *rem;
        if (tree_under_dir(ent, treepath, &rem)) { return 1; }
    }
    return 0;
}

/* len of the tree-archive FILE at `treepath` (for stat), or (uint32_t)-1 if not a file entry. */
static uint32_t serve_tree_file_len(const char *treepath) {
    struct bfs_entry *e = fs_find("govtree");
    if (!e) { return (uint32_t)-1; }
    if (ata_read_sector(e->start_sector, g_tree_scan) != 0) { return (uint32_t)-1; }
    if (!mem_eq(g_tree_scan, "GOVTREE1", 8)) { return (uint32_t)-1; }
    uint32_t count = tree_rd_u32(g_tree_scan + 12);
    for (uint32_t i = 0; i < count; i++) {
        if (i % TREE_ENTRIES_PER_SECTOR == 0) {
            uint32_t lba = e->start_sector + 1u + i / TREE_ENTRIES_PER_SECTOR;
            if (ata_read_sector(lba, g_tree_scan) != 0) { return (uint32_t)-1; }
        }
        const uint8_t *ent = g_tree_scan + (i % TREE_ENTRIES_PER_SECTOR) * TREE_ENTRY_SIZE;
        if (tree_path_eq((const char *)ent, treepath)) { return tree_rd_u32(ent + TREE_PATH_MAX + 4u); }
    }
    return (uint32_t)-1;
}

/* C7-MAINT-5B (A2) — the tree-archive ENTRY INDEX of the FILE at `treepath` (for the path stat's ino),
 * or -1 if not a file entry. The SAME index serve_tree_open recorded into g_fd_ino, so a path stat and
 * an fstat of the fd on that file answer the SAME st_ino (TREE_INO_BASE + index). */
static int serve_tree_file_index(const char *treepath) {
    struct bfs_entry *e = fs_find("govtree");
    if (!e) { return -1; }
    if (ata_read_sector(e->start_sector, g_tree_scan) != 0) { return -1; }
    if (!mem_eq(g_tree_scan, "GOVTREE1", 8)) { return -1; }
    uint32_t count = tree_rd_u32(g_tree_scan + 12);
    for (uint32_t i = 0; i < count; i++) {
        if (i % TREE_ENTRIES_PER_SECTOR == 0) {
            uint32_t lba = e->start_sector + 1u + i / TREE_ENTRIES_PER_SECTOR;
            if (ata_read_sector(lba, g_tree_scan) != 0) { return -1; }
        }
        const uint8_t *ent = g_tree_scan + (i % TREE_ENTRIES_PER_SECTOR) * TREE_ENTRY_SIZE;
        if (tree_path_eq((const char *)ent, treepath)) { return (int)i; }
    }
    return -1;
}

/* getdents64 over a tree-archive DIRECTORY fd: emit one linux_dirent64 per IMMEDIATE child (files DT_REG,
 * subdirectories DT_DIR each once). Children are enumerated in the archive's sorted order; the fd cursor
 * counts children already returned, so a buffer-full call resumes on the next. Returns bytes written (0 at
 * end). Forward-declared struct linux_dirent64 / DT_ constants live below (LISTING section). */
struct linux_dirent64;   /* defined in the sealed-image LISTING section below */
static uint64_t serve_tree_getdents(int fdidx, uint64_t buf, uint64_t count);

/* ═══ C7 P3b-5a-ii — THE /rec/ NAMESPACE ACTS at caller-named paths (design/54 §7 P3b-5a; §5 L21). ═══
 * Under /rec/<world>/… the body PERFORMS the seam's OWN record-disk write acts on CALLER-NAMED paths,
 * each backed by the BODYFS02 record disk — THE ONE TRUTH; no namespace lives in body memory. The
 * writable surface is EXACTLY the seam's declared acts (L21): mkdir declares a namespace, create-on-
 * absent is write-once by name AND content, append is the record pen, unlink removes, same-directory
 * rename is the write-once swap, the one-writer act is served on the marker (*.lock) name class,
 * listing and stat are served. EVERY OTHER write class refuses BY NAME; a path outside /rec/ refuses
 * ENOENT. NO served shape answers success without performing (L19). serve_openat_fs (floor3/GATE)
 * resolves caller-named READS through this same disk (fs_find below); the dispatch mkdir/rename become
 * REAL under /rec/ (serve_ns_syscall). A body-side self-check (serve_ns_selfcheck, driven by
 * diskcheck.c) proves A2-A5 with read-back and a plant per direction — a check that cannot fail is not
 * a check. The single-writer HELD claim is an in-body property (the body is the sole writer BY
 * CONSTRUCTION, disk.h §23-34); the marker's EXISTENCE and mark are on the disk. ═══════════════════*/

/* the MARKER name class: a name ending in ".lock" (the record lock-file idiom, 5s2 FINDINGS §1 / archi
 * :4248 — ftruncate-to-0 on a *.lock is the lock act's own shape; nowhere else). */
static int ns_is_marker(const char *name) {
    uint32_t n = 0; while (name[n]) { n++; }
    if (n < 5) { return 0; }
    return name[n-5] == '.' && name[n-4] == 'l' && name[n-3] == 'o' && name[n-2] == 'c' && name[n-1] == 'k';
}

/* same parent directory? — the segment up to the last '/'. Two names with no '/' share the (empty)
 * root parent. A cross-directory rename (R4) is refused by name. */
static int ns_same_dir(const char *a, const char *b) {
    int la = -1, lb = -1;
    for (uint32_t i = 0; a[i]; i++) { if (a[i] == '/') { la = (int)i; } }
    for (uint32_t i = 0; b[i]; i++) { if (b[i] == '/') { lb = (int)i; } }
    if (la != lb) { return 0; }
    for (int k = 0; k < la; k++) { if (a[k] != b[k]) { return 0; } }
    return 1;
}

/* the one-writer HELD-claim table (an in-body property of the current holder; the body is single-writer
 * by construction). The marker's EXISTENCE + mark are on the disk (fs_marker_write). */
#define NS_MARKER_MAX 8u
static char g_ns_held[NS_MARKER_MAX][BFS_NAME_MAX];
static uint32_t g_ns_held_n;
static int ns_marker_held(const char *name) {
    for (uint32_t i = 0; i < g_ns_held_n; i++) { if (fs_name_eq(g_ns_held[i], name)) { return 1; } }
    return 0;
}
static void ns_marker_hold(const char *name) {
    if (g_ns_held_n >= NS_MARKER_MAX) { return; }
    uint32_t k = 0;
    for (; k < BFS_NAME_MAX && name[k]; k++) { g_ns_held[g_ns_held_n][k] = name[k]; }
    for (; k < BFS_NAME_MAX; k++) { g_ns_held[g_ns_held_n][k] = '\0'; }
    g_ns_held_n++;
}
#if defined(GATE_ON_BODY)
/* C7 P3b-5a-v — RELEASE a held claim (the one-writer act's close+unlink release). Compacts the held table
 * so the holder count returns to its true value — a second claimant is refused only while a holder LIVES.
 * (Used only by the LEDGER lock act; guarded so the plain build carries no unused static.) */
static void ns_marker_release(const char *name) {
    for (uint32_t i = 0; i < g_ns_held_n; i++) {
        if (fs_name_eq(g_ns_held[i], name)) {
            for (uint32_t j = i; j + 1 < g_ns_held_n; j++) {
                for (uint32_t k = 0; k < BFS_NAME_MAX; k++) { g_ns_held[j][k] = g_ns_held[j + 1][k]; }
            }
            g_ns_held_n--;
            return;
        }
    }
}
#endif

static int g_ns_mem_shadow;   /* A5: a namespace declared only in body MEMORY (a second truth) — the
                               * disk is the one truth, so it must NOT resolve; PLANT_NS_MEMORY_TRUTH
                               * makes it resolve (the fault). */

/* mkdir: declare the namespace <world> as a DIRECTORY (FT_DIR) — so it STATS as a directory and LISTS its
 * children (C7 P3b-5a-vi, A3; was a zero-length blob that stat'd as a regular file -> os.listdir ENOTDIR).
 * Idempotent. PLANT_NS_STUB_NOOP: answer success, declare NOTHING (the old 0-answering stub) -> stat/list reds. */
static uint64_t serve_ns_mkdir(const char *recpath) {
    const char *name = si_rec_basename(recpath);
    if (!name || name[0] == '\0') { return (uint64_t)(-2); }
#ifdef PLANT_NS_STUB_NOOP
    return 0;                                                   /* the fault: declares nothing */
#else
    return (fs_mkdir(name) == 0) ? 0 : (uint64_t)(-1);          /* an FT_DIR: idempotent; a non-dir name refuses */
#endif
}

/* create-on-absent (O_CREAT|O_EXCL): write-once by name AND content (A3, via fs_blob_write_once). */
static uint64_t serve_ns_create_once(const char *recpath, const uint8_t *data, uint32_t n) {
    const char *name = si_rec_basename(recpath);
    if (!name || name[0] == '\0') { return (uint64_t)(-2); }
    return (fs_blob_write_once(name, data, n) == 0) ? 0 : (uint64_t)(-1);
}

/* append (O_APPEND): the record pen — extend the append-only record; read-back at *start. */
static uint64_t serve_ns_append(const uint8_t *data, uint32_t n, uint32_t *start) {
    return (fs_record_append(data, n, start) == 0) ? 0 : (uint64_t)(-1);
}

/* unlink: remove a blob by name (the record is refused; a removed name is re-creatable, A3 (c)). */
static uint64_t serve_ns_unlink(const char *recpath) {
    const char *name = si_rec_basename(recpath);
    if (!name || name[0] == '\0') { return (uint64_t)(-2); }
    return (fs_remove(name) == 0) ? 0 : (uint64_t)(-1);
}

/* same-directory rename: the write-once swap (S5). Cross-directory (R4) refuses by name.
 * PLANT_NS_STUB_NOOP: the rename stub answers success, renames NOTHING -> the read-back reds. */
static uint64_t serve_ns_rename(const char *oldrec, const char *newrec) {
    const char *o = si_rec_basename(oldrec);
    const char *nn = si_rec_basename(newrec);
    if (!o || !nn || o[0] == '\0' || nn[0] == '\0') { return (uint64_t)(-2); }
    if (!ns_same_dir(o, nn)) { return (uint64_t)(-1); }         /* R4 cross-directory rename: refused by name */
#ifdef PLANT_NS_STUB_NOOP
    return 0;                                                   /* the fault: renames nothing */
#else
    { struct bfs_entry *oe = fs_find(o);                        /* C7 P3b-5a-v — the durable-write swap (S5-over- */
      if (oe && oe->type == FT_DURABLE) {                       /* existing): a staging file swaps over its final, */
          return (fs_swap_rename(o, nn) == 0) ? 0 : (uint64_t)(-1);   /* CLOBBERING a present final (atomic-write-once) */
      } }
    return (fs_rename(o, nn) == 0) ? 0 : (uint64_t)(-1);        /* the ns write-once swap keeps its no-clobber rule */
#endif
}

/* the one-writer act on the MARKER name class (*.lock) ONLY (A4): create-open + a HELD exclusive claim
 * + truncate-to-nothing + the holder's mark (BODY_PID). A SECOND claim on a held marker is REFUSED;
 * the act is NOT served on the record or any other name class. PLANT_NS_SECOND_CLAIM admits a second. */
static uint64_t serve_ns_marker_claim(const char *recpath) {
    const char *name = si_rec_basename(recpath);
    if (!name || name[0] == '\0') { return (uint64_t)(-2); }
    if (!ns_is_marker(name)) { return (uint64_t)(-1); }         /* served ONLY on the marker name class */
    if (ns_marker_held(name)) {
#ifndef PLANT_NS_SECOND_CLAIM
        return (uint64_t)(-1);                                  /* a second claim on a held marker: REFUSED */
#endif
        /* PLANT: fall through and admit the second claim (the held-claim property made fallible) */
    }
    { static const uint8_t mark[1] = { '1' };                   /* the holder's mark: BODY_PID == 1 */
      if (fs_marker_write(name, mark, 1u) != 0) { return (uint64_t)(-1); } }
    ns_marker_hold(name);
    return 0;
}

/* truncate-to-nothing: the one-writer act's shape, served ONLY on a marker; on a NON-marker it is
 * REFUSED by name (R2 — truncate/ftruncate off the lock class is not a served act).
 * PLANT_NS_TRUNC_NONMARKER serves it on a non-marker. */
static uint64_t serve_ns_truncate(const char *recpath) {
    const char *name = si_rec_basename(recpath);
    if (!name || name[0] == '\0') { return (uint64_t)(-2); }
    if (ns_is_marker(name)) { return serve_ns_marker_claim(recpath); }   /* the lock act's own shape */
#ifdef PLANT_NS_TRUNC_NONMARKER
    { static const uint8_t z[1] = { 0 };
      return (fs_marker_write(name, z, 0u) == 0) ? 0 : (uint64_t)(-1); }  /* the fault: truncate a non-marker */
#else
    return (uint64_t)(-1);                                                /* R2: truncate on a non-marker refused */
#endif
}

/* every OTHER write class refuses BY NAME (A5): overwrite-in-place, pwrite-below-size, chmod/fchmod,
 * symlink, link, mmap-write — none is a served act (the dispatch's `default:` refuses these by ENOSYS
 * too). PLANT_NS_OTHERCLASS_SERVED serves one -> the by-name-refusal check reds. */
static uint64_t serve_ns_refuse_class(void) {
#ifdef PLANT_NS_OTHERCLASS_SERVED
    return 0;                                                   /* the fault: an other-class write served */
#else
    return (uint64_t)(-1);                                      /* REFUSED by name */
#endif
}

/* a path OUTSIDE /rec/ (and the sealed set) refuses -ENOENT (A5 R9 / the resolver's designed refusal,
 * NEVER a fabricated live-walk success). PLANT_NS_OUTSIDE_SERVED serves it. */
static uint64_t serve_ns_resolve_outside(const char *path) {
    if (si_rec_basename(path)) { return 0; }                    /* a /rec/ path is INSIDE (not this check) */
#ifdef PLANT_NS_OUTSIDE_SERVED
    return 0;                                                   /* the fault: an outside path served */
#else
    return (uint64_t)(-2);                                      /* -ENOENT: the designed refusal */
#endif
}

/* the disk is the ONE truth (A5): a name resolves ONLY via the record disk (fs_find), never a
 * body-memory shadow. PLANT_NS_MEMORY_TRUTH answers from the memory-only namespace (a second truth). */
static int serve_ns_resolves_on_disk(const char *name) {
    if (fs_find(name)) { return 1; }                            /* present on the record disk */
#ifdef PLANT_NS_MEMORY_TRUTH
    if (g_ns_mem_shadow) { return 1; }                          /* the fault: a memory-only namespace resolves */
#endif
    return 0;
}

/* the dispatch's mkdir/rename made REAL under /rec/ (A2): a /rec/ path performs the ns act; a path
 * OUTSIDE /rec/ keeps the benign no-op (0) the worker/interpreter tolerate — so the floor3/4g boots are
 * unchanged in behaviour (reads of outside paths are refused by the resolver separately). */
static uint64_t serve_ns_syscall(uint32_t num, uint64_t a0, uint64_t a1) {
    const char *p0 = (a0 && a0 < CANON_LIMIT) ? (const char *)(uintptr_t)a0 : 0;
    if (!p0 || !si_rec_basename(p0)) { return 0; }              /* outside /rec/: the benign stub (unchanged) */
    if (num == SYS_mkdir) { return serve_ns_mkdir(p0); }
    { const char *p1 = (a1 && a1 < CANON_LIMIT) ? (const char *)(uintptr_t)a1 : 0;
      if (!p1 || !si_rec_basename(p1)) { return 0; }
      return serve_ns_rename(p0, p1); }                         /* SYS_rename(old=a0, new=a1) */
}

/* THE BODY-SIDE PROOF (A2-A5): drive each /rec/ namespace act at caller-named paths on the record disk,
 * read back, and refuse every other class — printing CHECK NS-A2/A3/A4/A5 PASS/FAIL and an aggregate
 * NS-ACTS. Driven from diskcheck.c's disk_selfcheck (the DISK phase, no interpreter). Each behaviour has
 * a build.sh -D plant that reds exactly its line. Returns 1 iff all four pass. */
#define NS_WALK_MAX 32
static char g_ns_walk[NS_WALK_MAX][BFS_NAME_MAX];
static const uint8_t NS_A[]   = "gov-os ns file a: written once by name AND content (5a-ii)";
static const uint8_t NS_C[]   = "gov-os ns DIFFERENT bytes: an overwrite that must refuse by name";
static const uint8_t NS_APP[] = "gov-os ns append: extends the append-only record pen, read back";
static const uint8_t NS_R[]   = "gov-os ns rename source: the same-directory write-once swap payload";

int serve_ns_selfcheck(void) {
    if (!serve_fs_ready()) { serial_puts("NS-ACTS: SKIPPED (no disk)\n"); return 1; }

    /* ── A2 — THE NAMESPACE ACTS PERFORM, at caller-named paths under /rec/ (each PERFORMING) ──────── */
    int a2 = 1;
    if (serve_ns_mkdir("/rec/ns-w1") != 0) { a2 = 0; }                    /* mkdir declares the directory */
    if (!fs_find("ns-w1")) { a2 = 0; }                                    /* it then stats present */
    if (serve_ns_create_once("/rec/ns-w1/a", NS_A, (uint32_t)sizeof(NS_A)) != 0) { a2 = 0; }  /* create-on-absent */
    { struct bfs_entry *e = fs_find("ns-w1/a"); uint8_t bk[128]; uint32_t bl = 0;
      if (!e || fs_read_entry(e, bk, sizeof(bk), &bl) != 0 || bl != sizeof(NS_A) || !mem_eq(bk, NS_A, bl)) { a2 = 0; } }
    { uint32_t st = 0;                                                    /* append extends the record */
      if (serve_ns_append(NS_APP, (uint32_t)sizeof(NS_APP), &st) != 0) { a2 = 0; }
      uint8_t rb[128]; uint32_t rl = 0;
      if (fs_record_read(st, rb, sizeof(rb), &rl) != 0 || rl != sizeof(NS_APP) || !mem_eq(rb, NS_APP, rl)) { a2 = 0; } }
    { int c = fs_walk(g_ns_walk, NS_WALK_MAX); int found = 0;            /* getdents lists the world */
      for (int i = 0; i < c; i++) { if (fs_name_eq(g_ns_walk[i], "ns-w1/a")) { found = 1; } }
      if (!found) { a2 = 0; } }
    if (serve_ns_create_once("/rec/ns-w1/r1", NS_R, (uint32_t)sizeof(NS_R)) != 0) { a2 = 0; }  /* same-dir rename */
    if (serve_ns_rename("/rec/ns-w1/r1", "/rec/ns-w1/r2") != 0) { a2 = 0; }
    if (fs_find("ns-w1/r1")) { a2 = 0; }                                  /* the old name is gone */
    { struct bfs_entry *e = fs_find("ns-w1/r2"); uint8_t bk[128]; uint32_t bl = 0;
      if (!e || fs_read_entry(e, bk, sizeof(bk), &bl) != 0 || bl != sizeof(NS_R) || !mem_eq(bk, NS_R, bl)) { a2 = 0; } }
    serial_puts(a2 ? "CHECK NS-A2: PASS\n" : "CHECK NS-A2: FAIL\n");

    /* ── A3 — WRITE-ONCE IS BY NAME AND CONTENT ─────────────────────────────────────────────────── */
    int a3 = 1;
    if (serve_ns_create_once("/rec/ns-w1/a", NS_A, (uint32_t)sizeof(NS_A)) != 0) { a3 = 0; }   /* identical -> success */
    if (serve_ns_create_once("/rec/ns-w1/a", NS_C, (uint32_t)sizeof(NS_C)) == 0) { a3 = 0; }   /* different -> refused */
    { struct bfs_entry *e = fs_find("ns-w1/a"); uint8_t bk[128]; uint32_t bl = 0;              /* the first bytes STAND */
      if (!e || fs_read_entry(e, bk, sizeof(bk), &bl) != 0 || bl != sizeof(NS_A) || !mem_eq(bk, NS_A, bl)) { a3 = 0; } }
    if (serve_ns_unlink("/rec/ns-w1/a") != 0) { a3 = 0; }                 /* a REMOVED name ... */
    if (fs_find("ns-w1/a")) { a3 = 0; }                                   /* ... is gone ... */
    if (serve_ns_create_once("/rec/ns-w1/a", NS_A, (uint32_t)sizeof(NS_A)) != 0) { a3 = 0; }   /* ... and re-creatable */
    if (!fs_find("ns-w1/a")) { a3 = 0; }
    serial_puts(a3 ? "CHECK NS-A3: PASS\n" : "CHECK NS-A3: FAIL\n");

    /* ── A4 — THE ONE-WRITER ACT ON THE MARKER NAME CLASS ONLY ──────────────────────────────────── */
    int a4 = 1;
    if (serve_ns_marker_claim("/rec/ns-w1/x.lock") != 0) { a4 = 0; }      /* the one-writer act, served */
    { struct bfs_entry *e = fs_find("ns-w1/x.lock"); uint8_t bk[8]; uint32_t bl = 0;           /* the mark reads back */
      if (!e || fs_read_entry(e, bk, sizeof(bk), &bl) != 0 || bl != 1u || bk[0] != '1') { a4 = 0; } }
    if (serve_ns_marker_claim("/rec/ns-w1/x.lock") == 0) { a4 = 0; }      /* a SECOND claim: REFUSED */
    if (serve_ns_truncate("/rec/ns-w1/a") == 0) { a4 = 0; }               /* truncate on a NON-marker: refused */
    if (serve_ns_marker_claim("/rec/record") == 0) { a4 = 0; }            /* NOT served on the record */
    serial_puts(a4 ? "CHECK NS-A4: PASS\n" : "CHECK NS-A4: FAIL\n");

    /* ── A5 — EVERY OTHER WRITE CLASS REFUSES BY NAME; no second truth in memory ─────────────────── */
    int a5 = 1;
    if (serve_ns_refuse_class() == 0) { a5 = 0; }                         /* chmod/symlink/link/mmap/pwrite */
    if (serve_ns_create_once("/rec/ns-w1/r2", NS_C, (uint32_t)sizeof(NS_C)) == 0) { a5 = 0; }  /* overwrite-in-place */
    if (serve_ns_rename("/rec/ns-w1/r2", "/rec/ns-w2/r2") == 0) { a5 = 0; }                     /* cross-dir rename R4 */
    if (serve_ns_truncate("/rec/record") == 0) { a5 = 0; }                /* truncate/ftruncate on the record */
    if (serve_ns_resolve_outside("/tmp/not-a-rec-path") != (uint64_t)(-2)) { a5 = 0; }          /* outside -> ENOENT */
    g_ns_mem_shadow = 1;                                                  /* a namespace declared only in memory */
    if (serve_ns_resolves_on_disk("ns-ghost-never-written") != 0) { a5 = 0; }  /* memory namespace: refused */
    if (serve_ns_resolves_on_disk("ns-w1") == 0) { a5 = 0; }              /* a real disk name resolves (discriminates) */
    serial_puts(a5 ? "CHECK NS-A5: PASS\n" : "CHECK NS-A5: FAIL\n");

    { int ok = a2 && a3 && a4 && a5;
      serial_puts(ok ? "NS-ACTS: PASS\n" : "NS-ACTS: FAIL\n");
      /* C7 P3b-5a-iii (A6): the whole-tree archive + finder, on the freshly-mounted record disk. Prints
       * its OWN CHECK TREE-A6 + TREE-ACTS lines, kept SEPARATE from NS-ACTS (a non-TREE image SKIPs it,
       * so this addition cannot red an NS or P3b-2 boot). */
      serve_tree_selfcheck();
      return ok; }
}

#if defined(GATE_ON_BODY)
/* ══ C7 P3b-4g — THE GATE ON THE BODY: gov-os's OWN gate, run AS CONTENT off the record disk ══════════
 * The body serves a SECOND namespace under "/rec/" from the P3b-2 record disk (:4091 c — distinct from
 * the sealed image): the gov-os gate source (imported by the body-hosted interpreter), the guest test
 * key, the crossing-trail snapshot, and "/rec/record" (the record-pen append + the body-read read-back
 * of the signed row). The body holds NO key — the SIGNED row is the gate's, produced above the seam by
 * the interpreter; the body only moves bytes to/from its own disk (record-pen / body-read acts). */
static uint8_t g_recsrc_buf[65536];    /* the one active record-disk read buffer (reads are serialized) */
static uint32_t g_recsrc_len;          /* valid bytes in g_recsrc_buf                                   */
static uint32_t g_last_rec_start;      /* start sector of the LAST record-pen append (for body-read)     */
static uint32_t g_last_rec_len;        /* byte length of the LAST record-pen append (for fstat size)     */

/* C7 P3b-5a-iv — the record pen at CALLER-NAMED names. A write fd (open("a")) on a caller-named record
 * under /rec/ carries the record's /rec-stripped name; each write appends through fs_nrec_append. The
 * read-back is the EXISTING body-read (fs_find(rb) -> SI_FD_RECSRC -> fs_read_entry raw bytes), so no
 * new read path is needed — a caller-named record reads back whole via the same act the gate uses. */
#define SI_FD_NREC 8u                  /* C7 P3b-5a-iv: a caller-named record-pen WRITE fd (open("a"))   */
static char g_nrec_path[SI_MAX_FD][BFS_NAME_MAX];   /* the /rec-stripped write-fd name, indexed like g_fds */
/* C7 P3b-5a-v — the seam's remaining record-disk performers, served on the body in the EXACT shapes
 * host_seam issues them (measured on the guest's own CPython). SI_FD_DWR: the durable whole-file write's
 * staging fd (write_file_durably's tmp, O_WRONLY|O_CREAT|O_TRUNC on an absent name). SI_FD_LOCK: the one-
 * writer act's fd (lock_write's *.lock, O_CREAT|O_RDWR + fcntl F_SETLK + ftruncate-to-0 + holder text).
 * SI_FD_NRECRD: a STREAMED caller-named record READ fd (open_read/read_bytes, CLASS-C — a fresh reader
 * reconstructs the whole record of ANY size, no 64 KiB whole-load buffer). g_nrec_path (above) holds the
 * DWR/LOCK write fd's /rec-stripped name too (one fd idx, one kind, so the array is shared). */
#define SI_FD_DWR    9u                /* C7 P3b-5a-v: a durable-write staging fd (write_file_durably tmp) */
#define SI_FD_LOCK  10u                /* C7 P3b-5a-v: a one-writer lock fd (lock_write on a *.lock name)  */
#define SI_FD_NRECRD 11u              /* C7 P3b-5a-v: a STREAMED caller-named record read fd (CLASS-C)     */
#define SI_FD_RECDIR 12u              /* C7 P3b-5a-vi: a record-disk DIRECTORY fd (FT_DIR: getdents/fstat) */
static struct { uint32_t start, len; } g_nrecrd[SI_MAX_FD];   /* a streamed-read fd's disk base + length  */
/* C7 P3b-5a-vi (A3) — the /rec-stripped path of a record-disk DIRECTORY fd (mkdir /rec/<world>/blobs). A
 * getdents over this fd enumerates the flat name table's immediate children of this prefix. BFS_NAME_MAX-wide
 * (names are PATHS, up to 128), indexed like g_fds. */
static char g_recdir_path[SI_MAX_FD][BFS_NAME_MAX];
/* 1 iff this LOCK fd actually ACQUIRED the one-writer claim (fcntl F_SETLK granted) — so CLOSING a fd that
 * was REFUSED the claim (a second claimant) does NOT release the true holder's claim (indexed like g_fds).*/
static uint8_t g_lock_held[SI_MAX_FD];

/* (si_rec_basename moved OUT of GATE_ON_BODY — C7 P3b-5a-ii needs it in the plain build for the /rec/
 * namespace acts and the body-side self-check; defined unconditionally above.) */

/* serialize the body's crossing trail (g_serve_trail) as an append-only file — one line per crossing,
 * key-less and UNSIGNED (the body holds no key). The interpreter reads this via the body-read act and
 * folds its DIGEST as the ONE signed act-witness row (L18); off the body the digest recomputes from
 * these bytes and the row NAMES the same crossings. Each field is 8 hex chars; one '\n' per crossing,
 * so the line count IS the crossing count. Returns the byte length written into `out`. */
static uint32_t g_trail_serialize_hex(uint8_t *out, uint32_t n, uint32_t v) {
    static const char hx[] = "0123456789abcdef";
    for (int i = 7; i >= 0; i--) { out[n++] = (uint8_t)hx[(v >> (i * 4)) & 0xF]; }
    return n;
}
static uint32_t serve_trail_serialize(uint8_t *out, uint32_t max) {
    uint32_t n = 0;
    for (uint32_t i = 0; i < g_serve_rows && n + 48u < max; i++) {
        struct serve_row *r = &g_serve_trail[i];
        n = g_trail_serialize_hex(out, n, r->seq);      out[n++] = ' ';
        n = g_trail_serialize_hex(out, n, r->num);      out[n++] = ' ';
        n = g_trail_serialize_hex(out, n, r->cat);      out[n++] = ' ';
        n = g_trail_serialize_hex(out, n, r->verdict);  out[n++] = '\n';
    }
    return n;
}
#endif /* GATE_ON_BODY */

/* C7-MAINT-5B: forward declaration — the /rec/tmp scope test (defined below with the removal acts) is
 * needed by the O_APPEND record pen to scope the create-empty-then-append adoption to /rec/tmp (L21/A3). */
static int rec_under_tmp(const char *name);

/* openat: resolve the path. Sealed entry -> a sealed fd; record name -> a record fd (beside); otherwise
 * ENOENT (the designed refusal — no live walk). */
static uint64_t serve_openat_fs(uint64_t pathptr, uint64_t flags) {
    if (pathptr == 0 || pathptr >= CANON_LIMIT) { return SERVE_ENOSYS; }
    const char *path = (const char *)(uintptr_t)pathptr;
    (void)flags;
#if defined(GATE_ON_BODY)
    /* C7-MAINT-5B (A2) — the record-tree ROOT "/rec": CPython lists it (a sys.path entry) to discover the
     * top-level packages. si_rec_basename returns NULL for the bare root, so it is recognized here and mapped
     * to a root listing fd (the sub-directory listing extended to depth 0). The plant disables the root
     * (serve_tree_is_dir("")=0), so this whole branch declines -> the /rec resolver declines too -> ENOENT,
     * and os.listdir('/rec') raises. */
    if (si_is_rec_root(path) && serve_fs_ready() && serve_tree_is_dir("")) {
        int df = si_fd_alloc(SI_FD_TREEDIR, 0);
        if (df < 0) { return (uint64_t)(-24); }                 /* -EMFILE */
        uint32_t di = (uint32_t)df - SI_FD_BASE;
        g_treedir_path[di][0] = '\0';                           /* the ROOT: the empty tree-path */
        return (uint64_t)df;
    }
    /* C7 P3b-4g — the record-disk namespace ("/rec/..."), served from the P3b-2 disk (:4091 c). */
    const char *rb0 = si_rec_basename(path);
    if (rb0 && serve_fs_ready()) {
        char nb[BFS_NAME_MAX];                                   /* C7-MAINT-5B (A1): resolve '.' / '..', refuse an
                                                                  * escape above /rec (L21), THEN resolve the name */
        if (si_norm_rec(rb0, nb, sizeof(nb)) != 0) { g_outside_refusals++; return (uint64_t)(-2); }
        const char *rb = nb;
        if (rb[0] == 'r' && rb[1] == 'e' && rb[2] == 'c' && rb[3] == 'o' && rb[4] == 'r'
            && rb[5] == 'd' && rb[6] == '\0') {                 /* "/rec/record": the record-pen + body-read */
            int fd = si_fd_alloc(SI_FD_REC, 0);
            return (fd < 0) ? (uint64_t)(-24) : (uint64_t)fd;
        }
        if (rb[0] == 't' && rb[1] == 'r' && rb[2] == 'a' && rb[3] == 'i' && rb[4] == 'l'
            && rb[5] == '\0') {                                 /* "/rec/trail": snapshot the crossing trail */
            if (!fs_find("trail")) {                            /* write-once snapshot onto the body's disk */
                uint32_t tn = serve_trail_serialize(g_recsrc_buf, sizeof(g_recsrc_buf));
                fs_blob_write_once("trail", g_recsrc_buf, tn);
            }
            struct bfs_entry *te = fs_find("trail");
            g_recsrc_len = 0;
            if (te) { fs_read_entry(te, g_recsrc_buf, sizeof(g_recsrc_buf), &g_recsrc_len); }
            int fd = si_fd_alloc(SI_FD_RECSRC, 0);
            if (fd >= 0) { g_fd_ino[(uint32_t)fd - SI_FD_BASE] = rec_ino_of_name("trail"); }  /* A2: per-file ino */
            return (fd < 0) ? (uint64_t)(-24) : (uint64_t)fd;
        }
        /* C7 P3b-5a-v — THE ONE-WRITER LOCK ACT'S OPEN (host_seam.lock_write, measured: os.open(<record>.lock,
         * O_CREAT|O_RDWR)). A *.lock name opened with O_CREAT is the lock's OPEN — it returns a LOCK fd; the
         * HELD exclusive claim is the fcntl(F_SETLK) crossing, the holder text a write, close+unlink the
         * release. Served ONLY on the marker (*.lock) name class (L21). A *.lock opened O_RDONLY (no O_CREAT)
         * is lock_read — a plain streamed read handled by the fs_find path below. */
        if (ns_is_marker(rb) && (flags & O_CREAT)) {
#ifdef PLANT_LOCK_UNSERVED
            /* the pre-5a-v body: the lock open is not served -> ENOENT -> the real lock_write reds at os.open. */
            g_outside_refusals++;
            return (uint64_t)(-2);
#else
            int fd = si_fd_alloc(SI_FD_LOCK, 0);
            if (fd < 0) { return (uint64_t)(-24); }             /* -EMFILE */
            uint32_t li = (uint32_t)fd - SI_FD_BASE;
            uint32_t k = 0; for (; rb[k] && k < BFS_NAME_MAX - 1u; k++) { g_nrec_path[li][k] = rb[k]; }
            g_nrec_path[li][k] = '\0';
            g_lock_held[li] = 0;                                /* a fresh lock fd has not taken the claim yet */
            return (uint64_t)fd;
#endif
        }
        /* C7 P3b-5a-iv — THE RECORD PEN AT CALLER-NAMED NAMES (design/54 §7 P3b-5a-iv; L21/L14/L19).
         * The store's SOLE appender is host_seam.open_append = path.open("a") = O_WRONLY|O_CREAT|O_APPEND
         * on a CALLER-NAMED record. A caller-named /rec/ path opened for APPEND is the record pen: create
         * it on the FIRST stroke (absent), extend on later strokes (present). O_TRUNC (overwrite-in-place)
         * on the record name class is REFUSED BY NAME (R1) — the append-only record is never truncated-
         * and-rewritten. Read intent (O_RDONLY) falls through to the body-read below (fs_find(rb)). A
         * caller-named record never collides with "record"/"trail" (the gate's fixed names, above). */
        if (flags & O_TRUNC) {
            /* C7 P3b-5a-v — O_TRUNC IS TWO ACTS, told apart by the NAME'S STATE (:4343): O_TRUNC on a
             * PRESENT record is overwrite-in-place, REFUSED (R1); O_TRUNC on an ABSENT name is a CREATE —
             * the durable whole-file write's staging file (host_seam.write_file_durably's tmp). The pre-
             * 5a-v body refused O_TRUNC BY FLAG, coarser than its own law; this narrows the refusal to the
             * R1 property. */
            struct bfs_entry *tr = fs_find(rb);
            int present_record = tr && (tr->type == FT_NREC || tr->type == FT_RECORD);
#if defined(PLANT_NREC_TRUNC_SERVED) || defined(PLANT_DURABLE_TRUNC_RECORD)
            if (present_record) {                              /* the fault: O_TRUNC on a PRESENT record SERVED */
                if (tr->type == FT_NREC) { tr->length = 0; }   /* overwrite-in-place performed -> the R1 check reds */
                int fd = si_fd_alloc(SI_FD_NREC, 0);
                if (fd < 0) { return (uint64_t)(-24); }
                uint32_t ti = (uint32_t)fd - SI_FD_BASE;
                uint32_t k = 0; for (; rb[k] && k < BFS_NAME_MAX - 1u; k++) { g_nrec_path[ti][k] = rb[k]; }
                g_nrec_path[ti][k] = '\0';
                return (uint64_t)fd;
            }
#else
            if (present_record) { return (uint64_t)(-1); }     /* R1: the append-only record is never truncated */
#endif
            if (tr && tr->type == FT_BLOB) { return (uint64_t)(-1); }   /* never O_TRUNC-clobber a write-once blob */
#ifdef PLANT_DURABLE_UNSERVED
            return (uint64_t)(-1);   /* the pre-5a-v body: O_TRUNC refused by flag -> the real write_file_durably reds */
#else
            if (tr) { fs_remove(rb); }                         /* a present staging file (FT_DURABLE): truncate afresh */
            if (fs_durable_write(rb, (const uint8_t *)"", 0u) != 0) { return (uint64_t)(-1); }
            { int fd = si_fd_alloc(SI_FD_DWR, 0);              /* the durable-write staging fd (writes append at tail) */
              if (fd < 0) { return (uint64_t)(-24); }         /* -EMFILE */
              uint32_t di = (uint32_t)fd - SI_FD_BASE;
              uint32_t k = 0; for (; rb[k] && k < BFS_NAME_MAX - 1u; k++) { g_nrec_path[di][k] = rb[k]; }
              g_nrec_path[di][k] = '\0';
              return (uint64_t)fd; }
#endif
        }
        if (flags & O_APPEND) {                                 /* the record pen: create-on-absent, then append */
#ifndef PLANT_NREC_NO_CREATE_APPEND
            /* C7-MAINT-5B — THE CREATE-EMPTY-THEN-APPEND IDIOM SERVED FAITHFULLY. A caller that opens a
             * /rec/tmp name for write on an ABSENT name (O_TRUNC-on-absent), creating it EMPTY, closes it,
             * then re-opens it for APPEND — the ordinary create-then-append a program does — is served: the
             * body typed the empty create as a durable-write STAGING file (FT_DURABLE), and fs_nrec_append
             * below now ADOPTS an unswapped, zero-length FT_DURABLE into the record pen (FT_NREC) so the
             * append succeeds as Linux serves it. The adoption is SCOPED to /rec/tmp (L21/A3): a present
             * FT_DURABLE opened O_APPEND OUTSIDE /rec/tmp keeps the foreign-class refusal. The durable
             * temp-then-swap (host_seam.write_file_durably — a staging file RENAMED over its final, never
             * opened for append) never reaches this path, so it stays DISTINCT and unbroken (A2). */
#ifndef PLANT_RECONCILE_OUTSIDE_TMP
            struct bfs_entry *de = fs_find(rb);
            if (de && de->type == FT_DURABLE && !rec_under_tmp(rb)) {
                return (uint64_t)(-1);                          /* L21/A3: no adoption of a foreign class outside /rec/tmp */
            }
#endif                                                          /* PLANT_RECONCILE_OUTSIDE_TMP: drop the scope -> adopt outside /rec/tmp (A3 reds) */
            uint32_t st = 0;
            if (fs_nrec_append(rb, (const uint8_t *)"", 0u, &st) == 0) {   /* the FIRST stroke creates the record; an empty FT_DURABLE reconciles */
                int fd = si_fd_alloc(SI_FD_NREC, 0);
                if (fd < 0) { return (uint64_t)(-24); }         /* -EMFILE */
                uint32_t ni = (uint32_t)fd - SI_FD_BASE;
                uint32_t k = 0; for (; rb[k] && k < BFS_NAME_MAX - 1u; k++) { g_nrec_path[ni][k] = rb[k]; }
                g_nrec_path[ni][k] = '\0';
                return (uint64_t)fd;
            }
            return (uint64_t)(-1);                              /* create/append refused (name too long / no space)*/
#endif
            /* PLANT_NREC_NO_CREATE_APPEND: the pre-5a-iv body — fall through to ENOENT for a fresh record,
             * so the REAL store's open_append answers ENOENT and reds (A1's plant, L19). */
        }
        struct bfs_entry *e = fs_find(rb);                      /* gate source / the guest test key, by name */
        if (e) {
            if (e->type == FT_DIR) {                            /* C7 P3b-5a-vi (A3): a record-disk DIRECTORY
                                                                 * -> a listing fd (opendir fstats S_IFDIR, then
                                                                 * getdents enumerates its immediate children) */
                int df = si_fd_alloc(SI_FD_RECDIR, 0);
                if (df < 0) { return (uint64_t)(-24); }         /* -EMFILE */
                uint32_t di = (uint32_t)df - SI_FD_BASE;
                uint32_t k = 0; for (; rb[k] && k < BFS_NAME_MAX - 1u; k++) { g_recdir_path[di][k] = rb[k]; }
                g_recdir_path[di][k] = '\0';
                return (uint64_t)df;
            }
            if (e->type == FT_NREC || e->type == FT_DURABLE) {  /* C7 P3b-5a-v — a caller-named record/durable */
                /* CLASS-C: a FRESH reader reconstructs the WHOLE record of ANY size, STREAMED per read()
                 * (no 64 KiB whole-load buffer, the pre-5a-v under-serve). */
                int fd = si_fd_alloc(SI_FD_NRECRD, 0);
                if (fd < 0) { return (uint64_t)(-24); }
                uint32_t ri = (uint32_t)fd - SI_FD_BASE;
                g_nrecrd[ri].start = e->start_sector; g_nrecrd[ri].len = e->length;
                g_fd_ino[ri] = rec_ino_of_name(rb);            /* C7-MAINT-5B (A2): per-file ino by name index */
                return (uint64_t)fd;
            }
            g_recsrc_len = 0;                                   /* gate source / guest key (small): the whole-load path */
            fs_read_entry(e, g_recsrc_buf, sizeof(g_recsrc_buf), &g_recsrc_len);
            int fd = si_fd_alloc(SI_FD_RECSRC, 0);
            if (fd >= 0) { g_fd_ino[(uint32_t)fd - SI_FD_BASE] = rec_ino_of_name(rb); }  /* A2: per-file ino */
            return (fd < 0) ? (uint64_t)(-24) : (uint64_t)fd;
        }
        { int tf = serve_tree_open(rb);                         /* C7 P3b-5a-iii (A6): the whole-tree archive */
          if (tf >= 0) { return (uint64_t)tf; } }               /* a /rec/<tree-path> -> its bytes, streamed */
        if (serve_tree_is_dir(rb)) {                            /* C7 P3b-5b-i: a /rec/<dir> -> a listing fd */
            int df = si_fd_alloc(SI_FD_TREEDIR, 0);             /* CPython lists it to import (precision 3) */
            if (df < 0) { return (uint64_t)(-24); }             /* -EMFILE */
            uint32_t di = (uint32_t)df - SI_FD_BASE;
            uint32_t k = 0; for (; rb[k] && k < TREE_PATH_MAX - 1u; k++) { g_treedir_path[di][k] = rb[k]; }
            g_treedir_path[di][k] = '\0';
            return (uint64_t)df;
        }
        g_outside_refusals++;                                   /* a "/rec/" name with no entry -> ENOENT */
        return (uint64_t)(-2);
    }
#endif
    int idx = si_find(path);
    if (idx >= 0) {
        if (si_collides_as_record(idx)) {                       /* PLANT_FS_COLLIDE: record shadows the file */
            int fd = si_fd_alloc(SI_FD_RECORD, 0);
            return (fd < 0) ? (uint64_t)(-24) : (uint64_t)fd;    /* ld.so reads the empty record -> fails    */
        }
        uint8_t kind = (g_entries[idx].flags & SI_DIR_FLAG) ? SI_FD_DIR : SI_FD_SEALED;
        int fd = si_fd_alloc(kind, (uint32_t)idx);
        return (fd < 0) ? (uint64_t)(-24) : (uint64_t)fd;        /* -EMFILE if the table is full */
    }
    if (si_is_record_name(path) && serve_fs_ready()) {
        int fd = si_fd_alloc(SI_FD_RECORD, 0);
        return (fd < 0) ? (uint64_t)(-24) : (uint64_t)fd;
    }
    /* OUTSIDE both sets — the designed refusal (ENOENT), NEVER a live host-filesystem walk. */
#if defined(PLANT_LIVE_WALK)
    g_live_walk = 1;                                            /* the fault: a fabricated live-walk success */
    { int fd = si_fd_alloc(SI_FD_DIR, 0); return (fd < 0) ? (uint64_t)(-2) : (uint64_t)fd; }
#else
    g_outside_refusals++;
    return (uint64_t)(-2);                                      /* -ENOENT */
#endif
}

static uint64_t serve_read_fs(uint64_t fd, uint64_t buf, uint64_t count) {
    int i = si_fd_idx(fd);
    if (i < 0) { return 0; }
    if (buf == 0 || buf >= CANON_LIMIT) { return (uint64_t)(-14); }   /* -EFAULT */
    uint8_t *dst = (uint8_t *)(uintptr_t)buf;
    if (g_fds[i].kind == SI_FD_SEALED) {
        const struct si_entry *e = &g_entries[g_fds[i].entry];
        uint64_t remain = (g_fds[i].cursor < e->length) ? (e->length - g_fds[i].cursor) : 0;
        uint64_t n = (count < remain) ? count : remain;
        for (uint64_t k = 0; k < n; k++) { dst[k] = g_img[e->offset + g_fds[i].cursor + k]; }
        g_fds[i].cursor += n;
        return n;
    }
#if defined(GATE_ON_BODY)
    if (g_fds[i].kind == SI_FD_RECSRC) {                          /* body-read of record-disk CONTENT */
        uint64_t remain = (g_fds[i].cursor < g_recsrc_len) ? (g_recsrc_len - g_fds[i].cursor) : 0;
        uint64_t n = (count < remain) ? count : remain;
        for (uint64_t k = 0; k < n; k++) { dst[k] = g_recsrc_buf[g_fds[i].cursor + k]; }
        g_fds[i].cursor += n;
        return n;
    }
    if (g_fds[i].kind == SI_FD_REC) {                             /* body-read of the LAST record-pen append */
        if (g_fds[i].cursor == 0) {                               /* load the appended row from the disk once */
            g_recsrc_len = 0;
            if (g_last_rec_len) { fs_record_read(g_last_rec_start, g_recsrc_buf, sizeof(g_recsrc_buf), &g_recsrc_len); }
        }
        uint64_t remain = (g_fds[i].cursor < g_recsrc_len) ? (g_recsrc_len - g_fds[i].cursor) : 0;
        uint64_t n = (count < remain) ? count : remain;
        for (uint64_t k = 0; k < n; k++) { dst[k] = g_recsrc_buf[g_fds[i].cursor + k]; }
        g_fds[i].cursor += n;
        return n;
    }
    if (g_fds[i].kind == SI_FD_TREE) {                            /* C7 P3b-5a-iii: stream a tree-archive file */
        uint32_t got = serve_tree_read_range(g_tree_fd[i].base, g_tree_fd[i].len,
                                             (uint32_t)g_fds[i].cursor, dst, (uint32_t)count);
        g_fds[i].cursor += got;                                  /* the interpreter (5b) imports gov-os by path */
        return got;
    }
    if (g_fds[i].kind == SI_FD_NRECRD) {                          /* C7 P3b-5a-v: STREAMED caller-named record read */
        uint32_t got = fs_read_entry_range(g_nrecrd[i].start, g_nrecrd[i].len,
                                           (uint32_t)g_fds[i].cursor, dst, (uint32_t)count);
        g_fds[i].cursor += got;                                  /* a fresh reader reconstructs the whole record */
        return got;
    }
#endif
    if (g_fds[i].kind == SI_FD_RECORD) {                          /* beside / the collision plant: the record */
        uint8_t out[64]; uint32_t olen = 0;
        struct bfs_entry *rec = fs_find("record");
        if (rec) { fs_record_read(rec->start_sector, out, sizeof(out), &olen); }
        uint64_t n = (count < olen) ? count : olen;
        for (uint64_t k = 0; k < n; k++) { dst[k] = out[k]; }     /* wrong bytes for libc -> ld.so fails */
        return n;
    }
    return 0;
}

static uint64_t serve_pread_fs(uint64_t fd, uint64_t buf, uint64_t count, uint64_t offset) {
    int i = si_fd_idx(fd);
    if (i < 0 || g_fds[i].kind != SI_FD_SEALED) { return 0; }
    if (buf == 0 || buf >= CANON_LIMIT) { return (uint64_t)(-14); }
    const struct si_entry *e = &g_entries[g_fds[i].entry];
    uint8_t *dst = (uint8_t *)(uintptr_t)buf;
    uint64_t remain = (offset < e->length) ? (e->length - offset) : 0;
    uint64_t n = (count < remain) ? count : remain;
    for (uint64_t k = 0; k < n; k++) { dst[k] = g_img[e->offset + offset + k]; }
    return n;                                                     /* pread64 does not move the cursor */
}

/* fill the x86_64 struct stat the C library reads (st_dev @0, st_ino @8, st_nlink @16, st_mode @24,
 * st_size @48; 144 bytes). ld.so reads st_size to sanity-check the object AND (st_dev,st_ino) to tell
 * objects apart — so EACH sealed file gets a UNIQUE nonzero (dev,ino), or ld.so conflates libc with an
 * already-loaded object (dev=0/ino=0), skips mapping, and fails at relocation (measured). */
#define ST_BYTES   144u
#define ST_DEV_O    0u
#define ST_INO_O    8u
#define ST_NLINK_O 16u
#define ST_MODE_O  24u
#define ST_SIZE_O    48u
#define ST_BLKSIZE_O 56u                                         /* st_blksize — opendir sizes its getdents
                                                                  * buffer from it; 0 is survivable but a page
                                                                  * is the natural value */
#define ST_MTIME_O   88u                                         /* st_mtim.tv_sec (x86_64 struct stat) — a
                                                                  * timestamp .pyc validates its source against */
#define S_IFREG_   0100000u
#define S_IFDIR_   0040000u
#define S_IFCHR_   0020000u
#define SI_ST_DEV  0x42ull                                       /* one constant device for the sealed image */
static void si_fill_stat(uint64_t stbuf, uint32_t mode, uint64_t size, uint64_t ino, uint64_t mtime) {
    uint8_t *s = (uint8_t *)(uintptr_t)stbuf;
    for (uint32_t k = 0; k < ST_BYTES; k++) { s[k] = 0; }
    *(volatile uint64_t *)(uintptr_t)(stbuf + ST_DEV_O)     = SI_ST_DEV;
    *(volatile uint64_t *)(uintptr_t)(stbuf + ST_INO_O)     = ino;
    *(volatile uint64_t *)(uintptr_t)(stbuf + ST_NLINK_O)   = 1;
    *(volatile uint32_t *)(uintptr_t)(stbuf + ST_MODE_O)    = mode;
    *(volatile uint64_t *)(uintptr_t)(stbuf + ST_SIZE_O)    = size;
    *(volatile uint64_t *)(uintptr_t)(stbuf + ST_BLKSIZE_O) = 4096u;
    *(volatile uint64_t *)(uintptr_t)(stbuf + ST_MTIME_O)   = mtime;   /* the staged mtime (C7 P3b-4c) */
}
static uint64_t serve_fstat_fs(uint64_t fd, uint64_t stbuf) {
    if (stbuf == 0 || stbuf >= CANON_LIMIT) { return (uint64_t)(-14); }
    int i = si_fd_idx(fd);
    /* C7-MAINT-5B (A2): st_ino is a property of the FILE. Each branch derives the same number a PATH
     * stat of the same file derives (serve_newfstatat_fs), so os.path.samestat holds and a re-open on a
     * new slot re-answers it. PLANT_STAT_PERSLOT restores the pre-fix PER-SLOT inos (identity depends on
     * WHICH fd), so a path stat and an fstat of one file DISAGREE -> samestat false -> rmtree reds. */
#if defined(PLANT_STAT_PERSLOT)
    const int perslot = 1;
#else
    const int perslot = 0;
#endif
    if (i >= 0 && g_fds[i].kind == SI_FD_SEALED) {
        uint32_t e = g_fds[i].entry;
        si_fill_stat(stbuf, S_IFREG_ | 0755u, g_entries[e].length, (uint64_t)e + 1u, g_entries[e].mtime);
    } else if (i >= 0 && g_fds[i].kind == SI_FD_DIR) {            /* a sealed DIRECTORY fd — opendir fstat's it
                                                                  * and REQUIRES S_ISDIR (C7 P3b-4c: CPython's
                                                                  * importlib os.listdir's each sys.path dir) */
        uint32_t e = g_fds[i].entry;
        si_fill_stat(stbuf, S_IFDIR_ | 0755u, 0, (uint64_t)e + 1u, g_entries[e].mtime);
#if defined(GATE_ON_BODY)
    } else if (i >= 0 && g_fds[i].kind == SI_FD_RECSRC) {         /* record-disk CONTENT (loaded at open) */
        si_fill_stat(stbuf, S_IFREG_ | 0644u, g_recsrc_len, perslot ? (0x9100u + (uint64_t)i) : g_fd_ino[i], 0);
    } else if (i >= 0 && g_fds[i].kind == SI_FD_REC) {            /* the record-pen/body-read fd */
        si_fill_stat(stbuf, S_IFREG_ | 0644u, g_last_rec_len, perslot ? 0x9200u : rec_ino_of_name("record"), 0);
    } else if (i >= 0 && g_fds[i].kind == SI_FD_TREE) {           /* C7 P3b-5b-i: a tree-archive FILE fd */
        si_fill_stat(stbuf, S_IFREG_ | 0644u, g_tree_fd[i].len, perslot ? (0x9300u + (uint64_t)i) : g_fd_ino[i], 0);
    } else if (i >= 0 && g_fds[i].kind == SI_FD_TREEDIR) {        /* C7 P3b-5b-i: a tree-archive DIRECTORY fd
                                                                  * (opendir fstat's it and REQUIRES S_ISDIR) */
        si_fill_stat(stbuf, S_IFDIR_ | 0755u, 0, perslot ? (0x9400u + (uint64_t)i) : tree_dir_ino(g_treedir_path[i]), 0);
    } else if (i >= 0 && g_fds[i].kind == SI_FD_RECDIR) {         /* C7 P3b-5a-vi (A3): a record-disk DIRECTORY
                                                                  * fd (opendir fstat's it and REQUIRES S_ISDIR) */
        si_fill_stat(stbuf, S_IFDIR_ | 0755u, 0, perslot ? (0x9C00u + (uint64_t)i) : rec_ino_of_name(g_recdir_path[i]), 0);
    } else if (i >= 0 && g_fds[i].kind == SI_FD_NREC) {           /* C7 P3b-5a-iv: a caller-named record WRITE fd
                                                                  * (open("a") fstat's it — a regular file, the
                                                                  * current record length its size) */
        { struct bfs_entry *e = fs_find(g_nrec_path[i]);
          si_fill_stat(stbuf, S_IFREG_ | 0644u, e ? e->length : 0u,
                       perslot ? (0x9800u + (uint64_t)i) : rec_ino_of_name(g_nrec_path[i]), 0); }
    } else if (i >= 0 && g_fds[i].kind == SI_FD_NRECRD) {         /* C7 P3b-5a-v: a streamed record READ fd — its
                                                                  * size is the record length (read_bytes/fstat) */
        si_fill_stat(stbuf, S_IFREG_ | 0644u, g_nrecrd[i].len, perslot ? (0x9A00u + (uint64_t)i) : g_fd_ino[i], 0);
    } else if (i >= 0 && (g_fds[i].kind == SI_FD_DWR || g_fds[i].kind == SI_FD_LOCK)) {  /* C7 P3b-5a-v: a durable-
                                                                  * write staging fd / a one-writer lock fd */
        { struct bfs_entry *e = fs_find(g_nrec_path[i]);
          si_fill_stat(stbuf, S_IFREG_ | 0644u, e ? e->length : 0u,
                       perslot ? (0x9B00u + (uint64_t)i) : rec_ino_of_name(g_nrec_path[i]), 0); }
#endif
    } else if (fd < SI_FD_BASE) {                                 /* fd 0/1/2 (+ headroom): stdin/out/err char dev */
        si_fill_stat(stbuf, S_IFCHR_ | 0620u, 0, 0, 0);
    } else if (perslot) {                                         /* the fault: a closed managed fd stats as char dev */
        si_fill_stat(stbuf, S_IFCHR_ | 0620u, 0, 0, 0);
    } else {                                                      /* C7-MAINT-5B (A2/A3): a managed fd the body does
                                                                  * not know (closed / never allocated) -> -EBADF, as
                                                                  * Linux does, so a closed-fd stat is an absence not a
                                                                  * bogus char dev (w4c's finalizer 'already-closed') */
        return SERVE_EBADF;
    }
    return 0;                                                     /* fstat returns 0 on success */
}

/* newfstatat(dirfd, path, statbuf, flags): ld.so stats a library path before opening it. Resolve it in
 * the sealed image and fill a matching stat; a path outside is refused ENOENT (no live walk). */
static uint64_t serve_newfstatat_fs(uint64_t pathptr, uint64_t stbuf) {
    if (pathptr == 0 || pathptr >= CANON_LIMIT || stbuf == 0 || stbuf >= CANON_LIMIT) { return (uint64_t)(-14); }
    const char *path = (const char *)(uintptr_t)pathptr;
#if defined(GATE_ON_BODY)
    /* C7-MAINT-5B (A2): the record-tree ROOT "/rec" stats as a directory — CPython's FileFinder stats a
     * sys.path entry before listing it. The plant disables the root, so this declines -> ENOENT and the
     * stat raises. */
    if (si_is_rec_root(path) && serve_fs_ready() && serve_tree_is_dir("")) {
        si_fill_stat(stbuf, S_IFDIR_ | 0755u, 0, tree_dir_ino(""), 0);
        return 0;
    }
    /* C7 P3b-5b-i: a /rec/<tree-path> stat — CPython's FileFinder stats a candidate package DIRECTORY
     * (_path_isdir) and may stat a candidate source FILE. Resolve it in the govtree archive; a record-disk
     * blob (runmod / gate source) stats as a regular file. C7-MAINT-5B (A1): '.' / '..' resolved first,
     * an escape refused; (A2): the ino is a property of the FILE (the same number the fd's fstat answers). */
    const char *rb0 = si_rec_basename(path);
    if (rb0 && serve_fs_ready() && rb0[0] != '\0') {
        char nb[BFS_NAME_MAX];
        if (si_norm_rec(rb0, nb, sizeof(nb)) != 0) { g_outside_refusals++; return (uint64_t)(-2); }
        const char *rb = nb;
        int tix = serve_tree_file_index(rb);
        if (tix >= 0) { si_fill_stat(stbuf, S_IFREG_ | 0644u, serve_tree_file_len(rb),
                                     TREE_INO_BASE + (uint64_t)tix, 0); return 0; }
        if (serve_tree_is_dir(rb)) { si_fill_stat(stbuf, S_IFDIR_ | 0755u, 0, tree_dir_ino(rb), 0); return 0; }
        struct bfs_entry *be = fs_find(rb);
        if (be && be->type == FT_DIR) {                           /* C7 P3b-5a-vi (A3): a record-disk directory */
            si_fill_stat(stbuf, S_IFDIR_ | 0755u, 0, rec_ino_of_name(rb), 0); return 0;
        }
        if (be) { si_fill_stat(stbuf, S_IFREG_ | 0644u, be->length, rec_ino_of_name(rb), 0); return 0; }
        g_outside_refusals++;
        return (uint64_t)(-2);                                    /* a /rec/ name with no entry -> ENOENT */
    }
#endif
    int idx = si_find(path);
    if (idx >= 0) {
        if (g_entries[idx].flags & SI_DIR_FLAG) { si_fill_stat(stbuf, S_IFDIR_ | 0755u, 0, (uint64_t)idx + 1u, g_entries[idx].mtime); }
        else { si_fill_stat(stbuf, S_IFREG_ | 0755u, g_entries[idx].length, (uint64_t)idx + 1u, g_entries[idx].mtime); }
        return 0;
    }
#if defined(PLANT_LIVE_WALK)
    g_live_walk = 1; si_fill_stat(stbuf, S_IFREG_ | 0755u, 0, 0x7777, 0); return 0;   /* fabricated live-walk hit */
#else
    g_outside_refusals++;
    return (uint64_t)(-2);                                        /* -ENOENT — the designed refusal */
#endif
}

static uint64_t serve_close_fs(uint64_t fd) {
    int i = si_fd_idx(fd);
    if (i >= 0) { g_fds[i].used = 0; g_fds[i].kind = 0; g_fds[i].entry = 0; g_fds[i].cursor = 0; }
    return 0;
}

/* C7-MAINT-5B — A REAL FD DUP. CPython's _Py_dup uses fcntl(fd, F_DUPFD_CLOEXEC) and os.scandir(fd) dups
 * the directory fd before fdopendir; the pre-fix fcntl stub answered 1 (stdout), so scandir's fdopendir
 * fstat'd a char device -> ENOTDIR and rmtree could not list the world. A dup produces a NEW fd naming the
 * SAME file: copy the source slot's kind and every per-fd association so the duped fd fstats and getdents
 * exactly as the original (a RECDIR duped is still a RECDIR). Returns the new fd, -1 EBADF, -2 EMFILE. */
#define F_DUPFD_          0u      /* fcntl: duplicate to the lowest fd >= arg                             */
#define F_DUPFD_CLOEXEC_  1030u   /* fcntl: duplicate with O_CLOEXEC (what CPython's _Py_dup issues)      */
static int serve_dup_fd(uint64_t src) {
    int si = si_fd_idx(src);
    if (si < 0) { return -1; }                                   /* EBADF: not a managed fd */
    int nf = si_fd_alloc(g_fds[si].kind, g_fds[si].entry);
    if (nf < 0) { return -2; }                                   /* EMFILE */
    uint32_t ni = (uint32_t)nf - SI_FD_BASE;
    g_fds[ni].cursor = g_fds[si].cursor;                         /* a dup shares the file offset */
    g_fd_ino[ni]  = g_fd_ino[si];
    g_tree_fd[ni] = g_tree_fd[si];
#if defined(GATE_ON_BODY)
    /* C7-MAINT-5B-GATE-BUILD-REPAIR: g_nrecrd / g_lock_held / g_nrec_path / g_recdir_path are the
     * record-disk/one-writer per-fd tables defined ONLY under GATE_ON_BODY (the record-pen / namespace
     * work). The plain non-gate build has no such fds to dup, so these copies belong to the gate build
     * alone. Guarding them stops the plain build reaching gate-only symbols; the gate build is unchanged. */
    g_nrecrd[ni]  = g_nrecrd[si];
    g_lock_held[ni] = g_lock_held[si];
    for (uint32_t k = 0; k < BFS_NAME_MAX; k++) { g_nrec_path[ni][k] = g_nrec_path[si][k]; }
    for (uint32_t k = 0; k < BFS_NAME_MAX; k++) { g_recdir_path[ni][k] = g_recdir_path[si][k]; }
#endif
    for (uint32_t k = 0; k < TREE_PATH_MAX; k++) { g_treedir_path[ni][k] = g_treedir_path[si][k]; }
    return nf;
}

#if defined(GATE_ON_BODY)
/* ══ C7-MAINT-5B (A2) — REMOVAL SERVED ONLY UNDER /rec/tmp/ (shutil.rmtree of a DISCARDED world) ═════════
 * Once stat identity holds, shutil.rmtree gets past its samestat guard and empties a /rec/tmp world:
 * unlink each caller-named record (fs_remove), then rmdir the emptied namespace. Served ONLY under
 * /rec/tmp/ (L21): a name outside /rec/tmp/, the fixed FT_RECORD, and the /rec/tmp root itself stay
 * refused. AT_FDCWD (glibc rmdir/unlink -> unlinkat(AT_FDCWD, abspath, ...)) and a RECDIR-fd-relative
 * name (os.unlink(name, dir_fd=topfd)) both resolve to the SAME /rec-stripped name. ══════════════════════*/
#define AT_FDCWD_     0xFFFFFFFFFFFFFF9Cull   /* -100: dirfd = the current directory (glibc rmdir/unlink)   */
#define AT_REMOVEDIR_ 0x200u                  /* unlinkat flag: remove a directory (rmdir)                  */

/* 1 iff a /rec-stripped name is strictly under "tmp/" (a world or something inside it), never "tmp"
 * itself and never the bare "tmp/". This is the ONLY removable region (L21). */
static int rec_under_tmp(const char *name) {
    return name[0] == 't' && name[1] == 'm' && name[2] == 'p' && name[3] == '/' && name[4] != '\0';
}

/* 1 iff no present record-disk entry is an immediate-or-deeper child of directory `dir` (rmdir refuses a
 * non-empty directory, -ENOTEMPTY, exactly as Linux does — rmtree empties a world before removing it). */
static int rec_dir_empty(const char *dir) {
    uint32_t dl = 0; while (dir[dl]) { dl++; }
    for (uint32_t i = 0; i < BFS_MAX_ENTRIES; i++) {
        struct bfs_entry *e = fs_entry_at(i);
        if (!e) { continue; }
        uint32_t k = 0; for (; k < dl && e->name[k] == dir[k]; k++) { }
        if (k == dl && e->name[dl] == '/' && e->name[dl + 1] != '\0') { return 0; }   /* a child exists */
    }
    return 1;
}

/* resolve the unlinkat/rmdir target to its normalized /rec-stripped name in `out`; return 0 ok, -errno. */
static uint64_t serve_removal_name(uint64_t dirfd, const char *path, char *out, uint32_t outsz) {
    if (dirfd == AT_FDCWD_) {                              /* an absolute /rec/... path (glibc rmdir/unlink) */
        const char *rb = si_rec_basename(path);
        if (!rb || !rb[0]) { return (uint64_t)(-2); }     /* outside /rec -> ENOENT */
        return (si_norm_rec(rb, out, outsz) == 0) ? 0 : (uint64_t)(-2);   /* an escape -> ENOENT (L21) */
    }
    int di = si_fd_idx(dirfd);                             /* a RECDIR-fd-relative name (dir_fd=topfd) */
    if (di < 0 || g_fds[di].kind != SI_FD_RECDIR) { return SERVE_EBADF; }
    char joined[BFS_NAME_MAX];
    uint32_t o = 0; const char *d = g_recdir_path[di];
    for (uint32_t k = 0; d[k] && o + 1u < sizeof(joined); k++) { joined[o++] = d[k]; }
    if (o + 1u < sizeof(joined)) { joined[o++] = '/'; }
    for (uint32_t k = 0; path[k] && o + 1u < sizeof(joined); k++) { joined[o++] = path[k]; }
    joined[o] = '\0';
    return (si_norm_rec(joined, out, outsz) == 0) ? 0 : (uint64_t)(-2);
}

/* unlinkat(dirfd, path, flags): remove a caller-named record (flags 0) or rmdir an emptied namespace
 * (AT_REMOVEDIR), ONLY under /rec/tmp/. SYS_rmdir(path) routes here as unlinkat(AT_FDCWD, path, RMDIR). */
static uint64_t serve_unlinkat_fs(uint64_t dirfd, uint64_t pathptr, uint64_t flags) {
    if (pathptr == 0 || pathptr >= CANON_LIMIT) { return (uint64_t)(-14); }
    const char *path = (const char *)(uintptr_t)pathptr;
    char full[BFS_NAME_MAX];
    uint64_t rc = serve_removal_name(dirfd, path, full, sizeof(full));
    if (rc != 0) { return rc; }
#if !defined(PLANT_REMOVE_OUTSIDE_TMP)
    if (!rec_under_tmp(full)) { return (uint64_t)(-1); }  /* L21: removal served ONLY under /rec/tmp/ (EPERM) */
#endif                                                     /* the fault: serve a removal OUTSIDE /rec/tmp/ */
    struct bfs_entry *e = fs_find(full);
    if (!e) { return (uint64_t)(-2); }                    /* -ENOENT */
    if (e->type == FT_RECORD) { return (uint64_t)(-1); }  /* the fixed append-only record: never removed (L21) */
    if (flags & AT_REMOVEDIR_) {
        if (e->type != FT_DIR) { return (uint64_t)(-20); }        /* -ENOTDIR */
        if (!rec_dir_empty(full)) { return (uint64_t)(-39); }     /* -ENOTEMPTY */
    } else {
        if (e->type == FT_DIR) { return (uint64_t)(-21); }        /* -EISDIR: unlink on a directory */
    }
    return (fs_remove(full) == 0) ? 0 : (uint64_t)(-1);
}
#endif /* GATE_ON_BODY */

/* access(path): a sealed/record path exists (0); a path outside is refused ENOENT (the designed refusal,
 * counted — the NOWALK positive control). ld.so's access("/etc/ld.so.preload") lands here and is refused. */
static uint64_t serve_access_fs(uint64_t pathptr) {
    if (pathptr == 0 || pathptr >= CANON_LIMIT) { return (uint64_t)(-2); }
    const char *path = (const char *)(uintptr_t)pathptr;
    if (si_find(path) >= 0 || (si_is_record_name(path) && serve_fs_ready())) { return 0; }
#if defined(PLANT_LIVE_WALK)
    g_live_walk = 1; return 0;                                   /* the fault: a fabricated live-walk hit */
#else
    g_outside_refusals++;
    return (uint64_t)(-2);                                       /* -ENOENT */
#endif
}

/* ── LISTING: getdents64 over a sealed directory emits one linux_dirent64 per immediate child (the image
 * carries its directory entries — Q15/:4134, served, never refused). The dynamic prover reads by path and
 * does not list this rung; the body-side listable check drives this so P3b-4c can list without redefining
 * the FS. ─────────────────────────────────────────────────────────────────────────────────────────────*/
struct linux_dirent64 { uint64_t d_ino; int64_t d_off; uint16_t d_reclen; uint8_t d_type; char d_name[]; };
#define DT_DIR_ 4u
#define DT_REG_ 8u

static uint32_t si_len(const char *s) { uint32_t n = 0; while (s[n]) { n++; } return n; }

/* 1 iff `child` is an IMMEDIATE child of directory `dir`; on success `*base` points at the basename. */
static int si_immediate_child(const char *child, const char *dir, const char **base) {
    uint32_t dl = si_len(dir);
    uint32_t start;
    if (dl == 1 && dir[0] == '/') {                              /* dir == "/" */
        if (child[0] != '/') { return 0; }
        start = 1;
    } else {
        for (uint32_t i = 0; i < dl; i++) { if (child[i] != dir[i]) { return 0; } }
        if (child[dl] != '/') { return 0; }
        start = dl + 1;
    }
    if (child[start] == '\0') { return 0; }                      /* the dir itself, not a child */
    for (uint32_t i = start; child[i]; i++) { if (child[i] == '/') { return 0; } }   /* a deeper path */
    *base = child + start;
    return 1;
}

/* C7 P3b-5b-i: getdents64 over a tree-archive DIRECTORY fd. Enumerate immediate children of the fd's dir
 * (files DT_REG, subdirectories DT_DIR each once) from the govtree entry table, in the archive's sorted
 * order; the fd cursor counts children already returned so a buffer-full call resumes on the next. */
static uint64_t serve_tree_getdents(int fdidx, uint64_t buf, uint64_t count) {
    const char *dir = g_treedir_path[fdidx];
    int at_root = (dir[0] == '\0');                             /* C7-MAINT-5B (A2): the record-tree ROOT lists the union */
    struct bfs_entry *e = fs_find("govtree");
    if (!e) { return 0; }
    if (ata_read_sector(e->start_sector, g_tree_scan) != 0) { return 0; }
    if (!mem_eq(g_tree_scan, "GOVTREE1", 8)) { return 0; }
    uint32_t total = tree_rd_u32(g_tree_scan + 12);
    uint8_t *out = (uint8_t *)(uintptr_t)buf;
    uint64_t written = 0;
    uint32_t child_idx = 0;                                      /* enumeration index among distinct children */
    char prev_sub[TREE_PATH_MAX]; prev_sub[0] = '\0';
    for (uint32_t i = 0; i < total; i++) {
        if (i % TREE_ENTRIES_PER_SECTOR == 0) {
            uint32_t lba = e->start_sector + 1u + i / TREE_ENTRIES_PER_SECTOR;
            if (ata_read_sector(lba, g_tree_scan) != 0) { break; }
        }
        const char *ent = (const char *)(g_tree_scan + (i % TREE_ENTRIES_PER_SECTOR) * TREE_ENTRY_SIZE);
        const char *rem;
        if (at_root) { rem = ent; }                            /* the ROOT: every entry lies under it (rem = whole path) */
        else if (!tree_under_dir(ent, dir, &rem)) { continue; }
        uint32_t sl = 0; while (rem[sl] && rem[sl] != '/') { sl++; }
        int is_dir = (rem[sl] == '/');
        char name[TREE_PATH_MAX];
        uint32_t cap = (sl < TREE_PATH_MAX - 1u) ? sl : (TREE_PATH_MAX - 1u);
        for (uint32_t k = 0; k < cap; k++) { name[k] = rem[k]; }
        name[cap] = '\0';
        if (is_dir) {                                           /* dedup: sorted, so a subdir's files adjoin */
            int same = (prev_sub[0] != '\0');
            for (uint32_t k = 0; same; k++) { if (prev_sub[k] != name[k]) { same = 0; break; } if (name[k] == '\0') { break; } }
            if (same) { continue; }                            /* this subdir already emitted */
            for (uint32_t k = 0; k < TREE_PATH_MAX; k++) { prev_sub[k] = name[k]; if (name[k] == '\0') { break; } }
        }
        if (child_idx < g_fds[fdidx].cursor) { child_idx++; continue; }   /* already returned on a prior call */
        uint32_t nl = cap + 1u;                                 /* name + NUL */
        uint32_t reclen = (19u + nl + 7u) & ~7u;
        if (written + reclen > count) { return written; }       /* buffer full — resume next call (never fall into PART2) */
        struct linux_dirent64 *d = (struct linux_dirent64 *)(out + written);
        d->d_ino = (uint64_t)child_idx + 0x300000u;             /* nonzero (readdir skips d_ino==0) */
        d->d_off = (int64_t)(written + reclen);
        d->d_reclen = (uint16_t)reclen;
        d->d_type = is_dir ? DT_DIR_ : DT_REG_;
        for (uint32_t k = 0; k < nl; k++) { d->d_name[k] = name[k]; }
        written += reclen;
        child_idx++;
        g_fds[fdidx].cursor++;
    }
#if defined(GATE_ON_BODY)
    /* C7-MAINT-5B (A2), archi :4467 — THE UNION AT THE ROOT. Beyond the tree archive's top-level dirs
     * (src, tests) above, the /rec root ALSO lists the record-disk's own top-level names (record,
     * founding-pack, runmod, govtree, the tmp namespace — whatever mkdisk staged / the boot created), each
     * once, deduped against a tree top-level dir of the same name. A root listing that showed only the
     * archive's two names would misreport the disk; Linux lists everything under a mount point. The record
     * table (fs_entry_at over g_dir) is a distinct buffer from the archive scan (g_tree_scan), so a name
     * pointer stays valid across the dedup rescan. */
    if (at_root) {
        for (uint32_t ei = 0; ei < BFS_MAX_ENTRIES; ei++) {
            struct bfs_entry *be = fs_entry_at(ei);
            if (!be || be->name[0] == '\0') { continue; }
            const char *nm = be->name;
            int has_slash = 0;
            for (uint32_t k = 0; nm[k]; k++) { if (nm[k] == '/') { has_slash = 1; break; } }
            if (has_slash) { continue; }                        /* a nested name is not a root child */
            if (serve_tree_is_dir(nm)) { continue; }            /* already emitted as a tree top-level dir (each once) */
            if (child_idx < g_fds[fdidx].cursor) { child_idx++; continue; }   /* already returned on a prior call */
            uint32_t nl = 0; while (nm[nl]) { nl++; } nl += 1u;  /* name + NUL */
            uint32_t reclen = (19u + nl + 7u) & ~7u;
            if (written + reclen > count) { return written; }   /* buffer full — resume next call */
            struct linux_dirent64 *d = (struct linux_dirent64 *)(out + written);
            d->d_ino = (uint64_t)ei + 0x400000u;                /* nonzero; the record-disk ino space (== serve_recdir) */
            d->d_off = (int64_t)(written + reclen);
            d->d_reclen = (uint16_t)reclen;
            d->d_type = (be->type == FT_DIR) ? DT_DIR_ : DT_REG_;
            for (uint32_t k = 0; k < nl; k++) { d->d_name[k] = nm[k]; }
            written += reclen;
            child_idx++;
            g_fds[fdidx].cursor++;
        }
    }
#endif
    return written;                                             /* 0 at end of directory */
}

#if defined(GATE_ON_BODY)
/* C7 P3b-5a-vi (A3): getdents64 over a record-disk DIRECTORY fd (mkdir /rec/<world>/blobs). Enumerate the
 * IMMEDIATE children of the fd's dir from the flat name table (fs_entry_at scans [0, BFS_MAX_ENTRIES)) — an
 * entry named "<dir>/<child>" with no deeper '/' is one child; a blob is DT_REG, a nested dir DT_DIR. The fd
 * cursor counts children already returned so a buffer-full call resumes on the next (as the sealed/tree
 * paths do). Refuses nothing that exists — the append-only/write-once entries are read, never mutated. */
static uint64_t serve_recdir_getdents(int fdidx, uint64_t buf, uint64_t count) {
    const char *dir = g_recdir_path[fdidx];
    uint8_t *out = (uint8_t *)(uintptr_t)buf;
    uint64_t written = 0;
    uint32_t child_idx = 0;                                     /* children seen (matched), for the cursor */
    for (uint32_t e = 0; e < BFS_MAX_ENTRIES; e++) {
        struct bfs_entry *be = fs_entry_at(e);
        if (!be) { continue; }
        const char *base;
        if (!si_immediate_child(be->name, dir, &base)) { continue; }
        if (child_idx < g_fds[fdidx].cursor) { child_idx++; continue; }   /* already returned on a prior call */
        uint32_t nl = si_len(base) + 1u;                        /* name + NUL */
        uint32_t reclen = (19u + nl + 7u) & ~7u;
        if (written + reclen > count) { break; }                /* buffer full — resume next call */
        struct linux_dirent64 *d = (struct linux_dirent64 *)(out + written);
        d->d_ino = (uint64_t)e + 0x400000u;                     /* nonzero (readdir skips d_ino==0) */
        d->d_off = (int64_t)(written + reclen);
        d->d_reclen = (uint16_t)reclen;
        d->d_type = (be->type == FT_DIR) ? DT_DIR_ : DT_REG_;
        for (uint32_t k = 0; k < nl; k++) { d->d_name[k] = base[k]; }
        written += reclen;
        child_idx++;
        g_fds[fdidx].cursor++;
    }
    return written;                                             /* 0 at end of directory */
}
#endif

static uint64_t serve_getdents_fs(uint64_t fd, uint64_t buf, uint64_t count) {
#if defined(PLANT_LISTING_REFUSED)
    (void)fd; (void)buf; (void)count;
    return SERVE_ENOSYS;                                         /* the fault: the image's listing refused */
#else
    int i = si_fd_idx(fd);
#if defined(GATE_ON_BODY)
    if (i >= 0 && g_fds[i].kind == SI_FD_TREEDIR) {              /* C7 P3b-5b-i: list a /rec tree directory */
        if (buf == 0 || buf >= CANON_LIMIT) { return (uint64_t)(-14); }
        return serve_tree_getdents(i, buf, count);
    }
    if (i >= 0 && g_fds[i].kind == SI_FD_RECDIR) {              /* C7 P3b-5a-vi: list a /rec record-disk dir */
        if (buf == 0 || buf >= CANON_LIMIT) { return (uint64_t)(-14); }
        return serve_recdir_getdents(i, buf, count);
    }
#endif
    if (i < 0 || g_fds[i].kind != SI_FD_DIR) { return 0; }
    if (buf == 0 || buf >= CANON_LIMIT) { return (uint64_t)(-14); }
    const char *dir = g_entries[g_fds[i].entry].path;
    uint8_t *out = (uint8_t *)(uintptr_t)buf;
    uint64_t written = 0;
    uint32_t emitted = 0;
    for (uint32_t e = 0; e < g_entry_count; e++) {
        const char *base;
        if (!si_immediate_child(g_entries[e].path, dir, &base)) { continue; }
        if (emitted < g_fds[i].cursor) { emitted++; continue; }  /* already returned on a prior call */
        uint32_t nl = si_len(base) + 1;                          /* + NUL */
        uint32_t reclen = (19u + nl + 7u) & ~7u;                 /* 8+8+2+1 = 19, name, 8-align */
        if (written + reclen > count) { break; }                 /* buffer full — resume next call */
        struct linux_dirent64 *d = (struct linux_dirent64 *)(out + written);
        d->d_ino = e + 1;
        d->d_off = (int64_t)(written + reclen);
        d->d_reclen = (uint16_t)reclen;
        d->d_type = (g_entries[e].flags & SI_DIR_FLAG) ? DT_DIR_ : DT_REG_;
        for (uint32_t k = 0; k < nl; k++) { d->d_name[k] = base[k]; }
        written += reclen;
        emitted++;
        g_fds[i].cursor++;
    }
    return written;                                              /* 0 at end of directory */
#endif
}

/* ── the public API floor3 (enclosure.c) drives ──────────────────────────────────────────────────────*/

/* parse + adopt the sealed image (after floor3 digest-checks it). Returns the entry count, or -1. */
int serve_fs_set_image(const uint8_t *img, uint32_t len) {
    if (!img || len < sizeof(struct si_header)) { return -1; }
    const struct si_header *h = (const struct si_header *)img;
    static const char magic[8] = SI_MAGIC;
    for (int k = 0; k < 8; k++) { if (h->magic[k] != magic[k]) { return -1; } }
    if (h->version != 1u) { return -1; }
    uint64_t table = sizeof(struct si_header);
    if (table + (uint64_t)h->count * sizeof(struct si_entry) > len) { return -1; }
    g_img = img; g_img_len = len;
    g_entries = (const struct si_entry *)(img + table);
    g_entry_count = h->count;
    for (uint32_t i = 0; i < SI_MAX_FD; i++) { g_fds[i].used = 0; g_fds[i].kind = 0; }
    g_live_walk = 0; g_outside_refusals = 0;
    g_dyn_fs_on = 1;
    return (int)g_entry_count;
}

/* resolve a path to its bytes in the sealed image (floor3 loads ld.so from the PT_INTERP path). */
const uint8_t *serve_fs_find(const char *path, uint32_t *out_len, int *out_is_dir) {
    int idx = si_find(path);
    if (idx < 0) { return 0; }
    if (out_len) { *out_len = (uint32_t)g_entries[idx].length; }
    if (out_is_dir) { *out_is_dir = (g_entries[idx].flags & SI_DIR_FLAG) ? 1 : 0; }
    return g_img + g_entries[idx].offset;
}

/* the listable check: open `dir`, drive the REAL getdents64, and return 1 iff `name` appears among the
 * listed children. Proves the image is served by listing (A2); PLANT_LISTING_REFUSED reds it. */
int serve_fs_listable_check(const char *dir, const char *name) {
    int idx = si_find(dir);
    if (idx < 0 || !(g_entries[idx].flags & SI_DIR_FLAG)) { return 0; }
    int fd = si_fd_alloc(SI_FD_DIR, (uint32_t)idx);
    if (fd < 0) { return 0; }
    static uint8_t dbuf[1024];
    int found = 0;
    for (;;) {
        uint64_t n = serve_getdents_fs((uint64_t)fd, (uint64_t)(uintptr_t)dbuf, sizeof(dbuf));
        if ((int64_t)n <= 0) { break; }                          /* end, or a refusal (ENOSYS) */
        uint64_t off = 0;
        while (off < n) {
            struct linux_dirent64 *d = (struct linux_dirent64 *)(dbuf + off);
            if (si_streq(d->d_name, name)) { found = 1; }
            if (d->d_reclen == 0) { break; }
            off += d->d_reclen;
        }
        if (found) { break; }
    }
    serve_close_fs((uint64_t)fd);
    return found;
}

/* the beside check: the writable P3b-2 record FS is reachable alongside the read-only sealed image (a
 * record round-trip works), and the namespaces are DISTINCT (no sealed path resolves as a record). Returns
 * 1 iff both. PLANT_FS_COLLIDE makes a sealed file resolve as a record -> collision -> reds (and ld.so
 * reads the empty record for libc and fails). */
int serve_fs_beside_check(void) {
    int ready = serve_fs_ready();
    static const uint8_t ROW[] = { 'p','3','b','4','d' };
    uint32_t start = 0;
    int arc = ready ? fs_record_append(ROW, (uint32_t)sizeof(ROW), &start) : -99;
    /* read back the record we JUST appended (at `start`) — a true write→read round-trip proving the
     * writable record FS is reachable beside the read-only sealed image (not the first record, which may
     * be larger than this buffer). */
    uint8_t out[64]; uint32_t olen = 0;
    int rrc = (arc == 0) ? fs_record_read(start, out, sizeof(out), &olen) : -99;
    int match = (rrc == 0) && (olen == (uint32_t)sizeof(ROW)) && (out[0] == 'p') && (out[4] == 'd');
    if (!ready || arc != 0 || !match) { return 0; }
    int roundtrip = match;                                       /* the record is reachable + written beside */
    /* collision probe: does any sealed FILE path resolve as a record? (distinct namespaces). */
    int collision = 0;
    for (uint32_t e = 0; e < g_entry_count; e++) {
        if (g_entries[e].flags & SI_DIR_FLAG) { continue; }
        if (si_collides_as_record((int)e)) { collision = 1; break; }
    }
    return roundtrip && !collision;
}

int serve_fs_live_walk(void) { return g_live_walk; }
uint32_t serve_fs_outside_refusals(void) { return g_outside_refusals; }

/* ── the request dispatcher for the forty-nine serve phase (body_request routes here) ────────────────
 * `num` is the measured x86_64 syscall number; a0.. its args in the measured shape. Classify by PURPOSE,
 * route to the machinery, append ONE unsigned row. exit_group ends the run (unwinds; never returns). */
/* ── C7 P3b-6b — the three frame shapes the borrowed worker crosses on. Each SEND/RECEIVE that actually
 * crosses 6a's NIC is ONE row of the body's own serve trail (A4); the wait is the NEW performer. The body
 * reads/writes the worker's user buffers directly (its pages are mapped USER; SMAP is not enabled). ────*/
static inline uint64_t serve_rdtsc(void) {
    uint32_t lo, hi; __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi)); return ((uint64_t)hi << 32) | lo;
}

static uint64_t serve_send_frame(uint64_t buf, uint64_t len) {
    if (buf == 0 || buf >= CANON_LIMIT || len == 0 || len > 1600) { return SERVE_ENOSYS; }
    if (net_send_frame((const void *)(uintptr_t)buf, (uint32_t)len) != 0) { return SERVE_ENOSYS; }
    g_frames_sent++;
    int skip = 0;
#if defined(PLANT_FRAME_TRAIL_SKIP)
    if (g_frames_sent == 1) { skip = 1; }   /* the fault: the first sent frame is NOT recorded as a row */
#endif
    if (!skip) {
        serve_append((uint32_t)REQ_SEND_FRAME, CAT_FRAME, SV_SERVED, buf, len); g_frame_rows++;
#ifdef SOCKET_ACT
        sa_trail_append((uint32_t)REQ_SEND_FRAME, CAT_FRAME, SV_SERVED, len);   /* A3: every frame a row */
#endif
    }
    return 0;
}

static uint64_t serve_recv_frame(uint64_t out, uint64_t max) {
    static uint8_t tmp[1600];
    if (out == 0 || out >= CANON_LIMIT) { return 0; }
    uint32_t m = (max > sizeof(tmp)) ? (uint32_t)sizeof(tmp) : (uint32_t)max;
    int n = net_recv_frame(tmp, m);
    if (n <= 0) { return 0; }               /* no frame waiting: 0, no row (an empty poll is not a frame) */
    uint8_t *o = (uint8_t *)(uintptr_t)out;
    for (int i = 0; i < n; i++) { o[i] = tmp[i]; }
    g_frames_recv++;
    serve_append((uint32_t)REQ_RECV_FRAME, CAT_FRAME, SV_SERVED, out, (uint64_t)n); g_frame_rows++;
#ifdef SOCKET_ACT
    sa_trail_append((uint32_t)REQ_RECV_FRAME, CAT_FRAME, SV_SERVED, (uint64_t)n);   /* A3: every frame a row */
#endif
    return (uint64_t)n;
}

static uint64_t serve_wait(uint64_t ns) {
    /* the NEW performer: a bounded pause, honouring the worker's requested wait but never hanging (the
     * exchange completes on the peer's own teardown; this only keeps the pump from a tight spin). */
    uint64_t cap = ns; if (cap > 2000000ull) { cap = 2000000ull; }   /* cap 2 ms of request */
    uint64_t cycles = cap;                     /* ~1 cycle/ns floor; exactness is not load-bearing */
    uint64_t start = serve_rdtsc();
    while (serve_rdtsc() - start < cycles) { __asm__ volatile("pause"); }
    return 0;
}

uint64_t serve_request(uint64_t num, uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3, uint64_t a4) {
#ifdef SOCKET_ACT
    /* C7 P3b-6c(iii): the op-server worker's YIELD hands control back to the bridge (persistent coroutine).
     * It longjmps to the bridge and does NOT count as a crossing; on resume it returns 0 to the worker. */
    if (num == REQ_YIELD && g_serve_enclosure == ENCL_LWIP) {
        sa_worker_yield();
        g_in_act = 0;
        return 0;
    }
#endif
    g_serve_crossings++;                   /* EVERY crossing is counted, before any routing (WITNESSED) */

#ifdef SOCKET_ACT
    /* ── C7 P3b-6c(iii) — THE SOCKET-ACT RELAY. The interpreter's socket-family shapes cross to the enclosed
     * lwIP worker via the persistent coroutine bridge; each is ONE CAT_SOCK trail row. Only the fd that
     * SOCKET returned relays its data path (connect/send/recv/close/…); every other fd is the interpreter's
     * own (its fifty untouched, L18). The record decides SOCKET-OPEN FIRST — gov-os's own act on the record
     * runs before SYS_socket ever reaches here (A1); the body sees crossings, not grants. ──────────────*/
    if (g_sa_active && g_serve_enclosure == ENCL_INTERP) {
        uint64_t sa_ans = 0; int sa_hit = 1;
        if (num == SYS_socket) {
            sa_ans = bridge_relay_sock(SA_OP_SOCKET, a0, a1, a2, 0, 0, 0, 0);
            if ((int64_t)sa_ans >= 0) { g_sa_sock_fd = (int)sa_ans; }
        } else if (num == SYS_poll) {
            /* poll(fds, nfds, timeout): the fd is INSIDE struct pollfd {int fd; short events; short revents;}
             * (a0 is the ARRAY, not the fd). Relay ONLY a single-fd poll on the bridged socket; write revents
             * back; answer the ready count. Any other poll is the interpreter's own (falls through). */
            if (a1 == 1 && a0 && a0 < CANON_LIMIT && g_sa_sock_fd >= 0
                && *(int *)(uintptr_t)a0 == g_sa_sock_fd) {
                short events = *(short *)(uintptr_t)(a0 + 4);
                uint64_t re = bridge_relay_sock(SA_OP_POLL, (uint64_t)g_sa_sock_fd, (uint64_t)(uint16_t)events,
                                                0, 0, 0, 0, 0);
                *(short *)(uintptr_t)(a0 + 6) = (short)(uint16_t)re;   /* revents */
                sa_ans = re ? 1u : 0u;                                 /* ready fd count */
            } else {
                sa_hit = 0;
            }
        } else if (g_sa_sock_fd >= 0 && (int)a0 == g_sa_sock_fd) {
            if (num == SYS_connect) {
                sa_ans = bridge_relay_sock(SA_OP_CONNECT, a0, a1, a2,
                                           (const void *)(uintptr_t)a1, (uint32_t)a2, 0, 0);
            } else if (num == SYS_sendto) {
                sa_ans = bridge_relay_sock(SA_OP_SEND, a0, a1, a2,
                                           (const void *)(uintptr_t)a1, (uint32_t)a2, 0, 0);
            } else if (num == SYS_recvfrom) {
                sa_ans = bridge_relay_sock(SA_OP_RECV, a0, a1, a2,
                                           0, 0, (void *)(uintptr_t)a1, (uint32_t)a2);
            } else if (num == SYS_ioctl) {
                sa_ans = bridge_relay_sock(SA_OP_IOCTL_NB, a0, a1, a2, 0, 0, 0, 0);
            } else if (num == SYS_getsockopt) {
                sa_ans = bridge_relay_sock(SA_OP_GETSOERR, a0, a1, a2, 0, 0, 0, 0);
                if (a3 && a3 < CANON_LIMIT) { *(int *)(uintptr_t)a3 = (int)(uint32_t)sa_ans; sa_ans = 0; }
            } else if (num == SYS_close) {
                sa_ans = bridge_relay_sock(SA_OP_CLOSE, a0, a1, a2, 0, 0, 0, 0);
                g_sa_sock_fd = -1;
            } else {
                sa_hit = 0;
            }
        } else {
            sa_hit = 0;
        }
        if (sa_hit) {
            serve_append((uint32_t)num, CAT_SOCK, SV_SERVED, a1, sa_ans);
#if defined(PLANT_SA_NO_TRAIL)
            /* A3 PLANT: the SOCKET shape is served but leaves NO act-witness row -> the sock-row count
             * diverges from the relays -> the trail check reds (a fabricated/absent witness, L19). */
            if (num != SYS_socket) { sa_trail_append((uint32_t)num, CAT_SOCK, SV_SERVED, sa_ans); }
#else
            sa_trail_append((uint32_t)num, CAT_SOCK, SV_SERVED, sa_ans);
#endif
            g_in_act = 0;
            return sa_ans;
        }
    }
#endif

    /* ── C7 P3b-6b — THE PER-ENCLOSURE GATE (L18; :4302 b). A request not declared for the CURRENT
     * enclosure is refused BY NAME (the native -ENOSYS), witnessed as a REFUSED row — never served. The
     * three frame shapes route to the frame performers (lwIP enclosure only); the twenty + clock are
     * declared for the lwIP worker; the interpreter's set is untouched (ENCL_INTERP declares all but the
     * three frame shapes). This gate is INERT for the interpreter (it never issues a frame shape). ────*/
    if (num == REQ_SEND_FRAME || num == REQ_RECV_FRAME || num == REQ_WAIT
        || g_serve_enclosure == ENCL_LWIP) {
        if (!serve_declared(g_serve_enclosure, num)) {
            if (g_serve_enclosure == ENCL_LWIP
                && !(num == REQ_SEND_FRAME || num == REQ_RECV_FRAME || num == REQ_WAIT)) {
                /* a syscall BEYOND the lwIP worker's declared twenty (e.g. readlinkat, socket): refused
                 * by name, glibc/lwIP tolerate the native failure (4x). Counted only if it is SERVED
                 * (a plant) — a refusal here is correct and leaves g_lwip_beyond_served at 0. */
            }
            serve_append((uint32_t)num, CAT_A, SV_REFUSED, a0, SERVE_ENOSYS);
            g_in_act = 0;
            return SERVE_ENOSYS;             /* refused BY NAME — the worker's own native failure shape */
        }
        if (num == REQ_SEND_FRAME) { uint64_t r = serve_send_frame(a0, a1); g_in_act = 0; return r; }
        if (num == REQ_RECV_FRAME) { uint64_t r = serve_recv_frame(a0, a1); g_in_act = 0; return r; }
        if (num == REQ_WAIT)       { uint64_t r = serve_wait(a0);           g_in_act = 0; return r; }
        /* an lwIP-declared syscall (the twenty + clock): a served shape BEYOND the twenty reaching here is
         * the PLANT_LWIP_BEYOND_SERVED fault (serve_declared returned 1 for it) — record it so A2 reds. */
#if defined(PLANT_LWIP_BEYOND_SERVED)
        {
            int in_set = 0;
            for (uint32_t i = 0; i < LWIP_DECLARED_N; i++) { if ((uint32_t)num == LWIP_DECLARED[i]) { in_set = 1; } }
            if (!in_set) { g_lwip_beyond_served++; }   /* a beyond-set shape was served to the stack */
        }
#endif
        /* fall through to the shared classification (the shared PERFORMERS serve it) */
    }
    g_in_act = 1;                          /* an act is in progress — the timer must not switch (:4107 a) */
#ifdef FLOOR2_TRACE
    if (g_sched_on) {
        static uint32_t g_sc_n;
        if (g_sc_n < 400u) {
            g_sc_n++;
            serial_puts("SC t"); serial_puthex32(g_sched_cur_tid);
            serial_puts(" n0x"); serial_puthex32((uint32_t)num);
            serial_puts(" a0=0x"); serial_puthex64(a0);
            serial_puts(" a2=0x"); serial_puthex64(a2); serial_puts("\n");
        }
    }
#endif
#if defined(PLANT_SWITCH_INSIDE_ACT)
    interrupts_enable();                   /* the fault: let the timer fire mid-act (a switch inside an act) */
#endif
    uint64_t ans = 0;
    uint32_t cat = CAT_A, verdict = SV_SERVED;
    uint64_t arg = a0;

    switch (num) {

    /* ── category A — bring-up / loader / TLS floor (realized on the metal; the body IS the home) ──── */
    case SYS_getrandom:
        /* entropy AT BRING-UP (GRND_NONBLOCK) vs the entropy act (blocking). Both from the body's source. */
        cat = (a2 & GRND_NONBLOCK) ? CAT_A : CAT_ACT;
        arg = a2;                          /* the flags are the shape that bites (two distinct draws) */
        ans = serve_getrandom(a0, a1, a2);
        break;
    case SYS_execve:      cat = CAT_A; ans = 0; break;                 /* the loader's own — already home */
    case SYS_brk:         cat = CAT_A; ans = serve_brk(a0); break;      /* the growing program break */
    case SYS_arch_prctl:  cat = CAT_A; ans = serve_arch_prctl(a0, a1); break;   /* ARCH_SET_FS — %fs base */
    case SYS_set_tid_address: cat = CAT_A; ans = BODY_PID; break;
    case SYS_set_robust_list: cat = CAT_A; ans = 0; break;
    case SYS_rseq:        cat = CAT_A; ans = 0; break;
    case SYS_prlimit64:   cat = CAT_A; ans = serve_prlimit64(a1, a3); break;   /* a1=resource: STACK / NOFILE (5a-vi) */
    case SYS_mprotect:    cat = CAT_A; ans = serve_mprotect(a0, a1, a2); break;  /* the COMMIT point (C7-MAINT-5B) */
    case SYS_pread64:     cat = CAT_A;                                 /* the loader's ELF header / phdr read */
        ans = g_dyn_fs_on ? serve_pread_fs(a0, a1, a2, a3) : a2; break; /* floor3: the phdrs from the sealed file */
    case SYS_access:      cat = CAT_A;                                 /* ld.so.preload — absent, natural */
        ans = g_dyn_fs_on ? serve_access_fs(a1) : SERVE_ENOSYS; break; /* floor3: a path outside -> ENOENT (no walk) */
    case SYS_readlink:    cat = CAT_A; ans = SERVE_ENOSYS; break;      /* no filesystem symlink on the body */
    case SYS_getcwd:      cat = CAT_A;                                 /* the body's single root, "/" */
        /* C7-MAINT-5B — FILL THE CALLER'S BUFFER. The raw getcwd syscall writes the path into the caller's
         * buffer (a0=buf, a1=size) and returns the length INCLUDING the NUL; glibc's getcwd then checks
         * buf[0]=='/' and returns buf, else sets ENOENT. Answering a bare code (ans=1) without filling the
         * buffer left buf[0] != '/', so glibc raised — os.getcwd() FileNotFoundError. Write "/" + NUL and
         * return 2 so glibc returns "/". A worker's buffer is a mapped user page; the guard declines a
         * non-canonical/absent pointer. The body serves only "/" (its single root); anything beyond "/" is
         * out of scope (a RAISE). */
#if defined(PLANT_GETCWD_BARE_CODE)
        ans = 1;                          /* the fault: a bare code, buffer never filled -> glibc's getcwd raises */
#else
        if (a0 != 0 && a0 < CANON_LIMIT && a1 >= 2) {
            char *cwd = (char *)(uintptr_t)a0;
            cwd[0] = '/'; cwd[1] = '\0';
            ans = 2;                       /* strlen("/") + 1 — the length WITH the terminating NUL */
        } else {
            ans = (uint64_t)(-34);         /* -ERANGE: the buffer is absent or too small for "/" + NUL */
        }
#endif
        break;
    case SYS_rt_sigaction: cat = CAT_A; ans = 0; break;               /* SIGPIPE, SIG_IGN */
    case SYS_rt_sigprocmask: cat = CAT_A; ans = 0; break;

    /* ── category B — thread creation floor (the concurrency + memory acts' machinery) ─────────────── */
    case SYS_clone3: {
        uint64_t flags = *(volatile uint64_t *)(uintptr_t)a0;   /* clone_args.flags (the caller's struct) */
        cat = CAT_B; arg = flags;
        if (g_sched_on) {
            /* C7 P3b-4f-ii: the concurrency floor — create a REAL thread context (its own stack + TLS),
             * scheduled and preempted by the timer. func=a2 (rdx), arg=a4 (r8); the child returns from the
             * clone3 crossing to g_syscall_ret_rip with rax=0 (glibc's thread_start path). */
            ans = sched_clone3(a0, g_syscall_ret_rip, a2, a4);
        } else {
            /* P3b-4b shape-check (no scheduler yet): reproduce the measured thread-create shape only. */
#if defined(PLANT_THREAD_NO_SETTLS)
            flags &= ~(uint64_t)CLONE_SETTLS;   /* the fault: thread-create does not reproduce SETTLS */
#endif
            g_thread_settls = ((flags & CLONE_THREAD_SHAPE) == CLONE_THREAD_SHAPE) ? 1 : 0;
            uint32_t stack = pmm_alloc();
            if (stack) { pmm_free(stack); }     /* allocate+release: the machinery ran, no second thread here */
            ans = (uint64_t)(BODY_PID + 1);     /* a child tid */
        }
        break;
    }
    case SYS_madvise:     cat = CAT_B; ans = 0; break;                 /* MADV_DONTNEED on a thread stack */
    case SYS_gettid:      cat = CAT_B; ans = BODY_PID; break;

    /* ── the twelve acts' share — performed by the act machinery, witnessed like every crossing ─────── */
    case SYS_mmap:        cat = CAT_ACT; arg = a3;                     /* addr=a0 len=a1 prot=a2 flags=a3 fd=a4 off=a5 */
        ans = serve_mmap(a0, a1, a2, a3, a4, g_syscall_a5); break;     /* prot=a2 (C7-MAINT-5B: reservation vs commit) */
    case SYS_munmap:      cat = CAT_ACT; ans = serve_munmap(a0, a1); break;
    case SYS_futex:       cat = CAT_ACT; arg = a1;
        /* concurrency (Q-D). With the floor active: a REAL wait queue with timeout + wake (uaddr=a0, op=a1,
         * val=a2, timeout=a3). Without it (P3b-4b): the measured-shape check only.
         * C7 P3b-5a-vi (A2 coupling): glibc's sem_timedwait computes its ABSOLUTE deadline from
         * clock_gettime(CLOCK_REALTIME) — now a true epoch — and passes it with FUTEX_CLOCK_REALTIME. The
         * scheduler compares deadlines against its monotonic sched_now_ns (enclosure.c), so a REALTIME
         * (bitset) deadline is CONVERTED here back to the scheduler's frame by subtracting the SAME epoch
         * base — the deadline and the scheduler's "now" agree under one offset, so a 20 ms wait still times
         * out in 20 ms. The user timespec is restored after the call (never left mutated). */
        if (g_sched_on) {
            uint32_t fcmd = (uint32_t)(a1 & ~(uint64_t)(FUTEX_PRIVATE_FLAG | FUTEX_CLOCK_REALTIME));
            int rt_wait = ((a1 & FUTEX_CLOCK_REALTIME) != 0) && (fcmd == FUTEX_WAIT_BITSET)
                          && a3 != 0 && a3 < CANON_LIMIT;
            if (rt_wait) {
                volatile uint64_t *ts = (volatile uint64_t *)(uintptr_t)a3;
                uint64_t o0 = ts[0], o1 = ts[1];
#if !defined(PLANT_DEADLINE_CLOCK_UNCOUPLED)
                uint64_t base = serve_rt_base_ns();
                uint64_t dl   = o0 * 1000000000ull + o1;   /* the absolute REALTIME (epoch) deadline */
                uint64_t mdl  = (dl > base) ? (dl - base) : 0ull;   /* -> the scheduler's monotonic frame */
                ts[0] = mdl / 1000000000ull; ts[1] = mdl % 1000000000ull;
#endif                                                     /* PLANT: skip the conversion -> deadline ~56y out */
                ans = sched_futex(a0, a1, a2, a3);
                ts[0] = o0; ts[1] = o1;                    /* restore the caller's timespec */
            } else {
                ans = sched_futex(a0, a1, a2, a3);
            }
        } else {
            ans = serve_futex(a1);
        }
        break;
    case SYS_clock_gettime: cat = CAT_ACT; arg = a0; ans = serve_clock_gettime(a0, a1); break;
    case SYS_clock_nanosleep: cat = CAT_ACT; arg = a1; ans = serve_clock_nanosleep(a0, a1); break;
    case SYS_getpid:      cat = CAT_ACT; ans = BODY_PID; break;        /* single-writer-lock */
    case SYS_kill:        cat = CAT_ACT; ans = 0; break;               /* kill(pid,0): pid_alive */
    case SYS_lseek:       cat = CAT_ACT; ans = a1; break;              /* founding-pack-read companion */
    case SYS_openat:
        /* the DESIGNED REFUSAL boundary lives on this NAME: a module-search path is refused (category C);
         * a body-fs path is served (the file acts). PURPOSE, not name, is the boundary. */
        if (a1 == MODULE_SEARCH_SENTINEL) { goto module_scan; }
        cat = CAT_ACT; arg = a2;
        /* floor3: resolve the path in the SEALED IMAGE (ld.so opens libc by path); a path outside the
         * sealed+record sets is refused ENOENT (Q15/:4134), never a live walk. */
        ans = g_dyn_fs_on ? serve_openat_fs(a1, a2) : serve_file_act(SYS_openat, a0, a1, a2); break;
    case SYS_write:
        /* fd 1/2 (stdout/stderr) route to the serial line so the ring-3 program's own result appears as
         * it writes it (C7 P3b-4f-i); any other fd is a record-act write (the P3b-2 disk). */
        if ((a0 == 1 || a0 == 2) && a1 < CANON_LIMIT) {
            const char *ub = (const char *)(uintptr_t)a1;
            for (uint64_t i = 0; i < a2; i++) { serial_putc(ub[i]); }
            cat = CAT_ACT; ans = a2;
#if defined(GATE_ON_BODY)
        } else if (g_dyn_fs_on && a1 < CANON_LIMIT) {
            int wi = si_fd_idx(a0);
            if (wi >= 0 && g_fds[wi].kind == SI_FD_REC) {          /* the RECORD-PEN act: append the row */
                uint32_t start = 0;
                if (fs_record_append((const uint8_t *)(uintptr_t)a1, (uint32_t)a2, &start) == 0) {
                    g_last_rec_start = start; g_last_rec_len = (uint32_t)a2;
                }
                cat = CAT_ACT; ans = a2;
            } else if (wi >= 0 && g_fds[wi].kind == SI_FD_NREC) {  /* C7 P3b-5a-iv: the record pen at a caller-named name */
                uint32_t start = 0;
                if (fs_nrec_append(g_nrec_path[wi], (const uint8_t *)(uintptr_t)a1, (uint32_t)a2, &start) == 0) {
                    cat = CAT_ACT; ans = a2;                       /* the stroke extended the append-only record */
                } else {
                    cat = CAT_ACT; ans = (uint64_t)(-1);          /* -EPERM: the append was refused (no space) */
                }
            } else if (wi >= 0 && g_fds[wi].kind == SI_FD_DWR) {   /* C7 P3b-5a-v: the durable whole-file write */
                if (fs_durable_write(g_nrec_path[wi], (const uint8_t *)(uintptr_t)a1, (uint32_t)a2) == 0) {
                    cat = CAT_ACT; ans = a2;                       /* the staging bytes, extended at the tail */
                } else {
                    cat = CAT_ACT; ans = (uint64_t)(-1);          /* -EPERM: the write was refused (no space) */
                }
            } else if (wi >= 0 && g_fds[wi].kind == SI_FD_LOCK) {  /* C7 P3b-5a-v: the one-writer act's holder text */
                if (fs_marker_write(g_nrec_path[wi], (const uint8_t *)(uintptr_t)a1, (uint32_t)a2) == 0) {
                    cat = CAT_ACT; ans = a2;                       /* the holder's pid stamped on the *.lock marker */
                } else {
                    cat = CAT_ACT; ans = (uint64_t)(-1);
                }
            } else {
                /* C7-MAINT-5B (A3): a write on a descriptor the body does not know (an unknown/closed fd, or a
                 * read-only fd) answers -EBADF, as Linux does — a loud error, never the canned length that made
                 * the store's small-write flush see "invalid length 5". PLANT_WRITE_CANNED restores the canned
                 * count on an unknown fd, so w4c's flush reds by the invalid-length message (the pre-fix fault). */
#if defined(PLANT_WRITE_CANNED)
                cat = CAT_ACT; ans = serve_file_act(SYS_write, a0, a1, a2);
#else
                cat = CAT_ACT; ans = SERVE_EBADF;
#endif
            }
#endif
        } else {
            cat = CAT_ACT;
#if defined(GATE_ON_BODY)
            if (g_dyn_fs_on) { ans = (uint64_t)(-14); }   /* interpreter: a bad write buffer -> -EFAULT; the canned
                                                           * :646 return is retired from every interpreter path (A3) */
            else
#endif
            ans = serve_file_act(SYS_write, a0, a1, a2);   /* the P3b-4b worker's write direction (non-dynamic) */
        }
        break;
    case SYS_writev:
        /* floor3: ld.so/glibc write diagnostics to fd 2 via writev (iov[count] of {base,len}); route fd
         * 1/2 to the serial line so the linker's own messages are visible. */
        cat = CAT_ACT;
        if (g_dyn_fs_on && (a0 == 1 || a0 == 2) && a1 < CANON_LIMIT) {
            const uint64_t *iov = (const uint64_t *)(uintptr_t)a1;   /* {base,len} pairs */
            uint64_t total = 0;
            for (uint64_t v = 0; v < a2; v++) {
                uint64_t bptr = iov[v * 2], blen = iov[v * 2 + 1];
                if (bptr && bptr < CANON_LIMIT) {
                    const char *ub = (const char *)(uintptr_t)bptr;
                    for (uint64_t i = 0; i < blen; i++) { serial_putc(ub[i]); }
                }
                total += blen;
            }
            ans = total;
        } else { ans = SERVE_ENOSYS; }
        break;
    case SYS_read:        cat = CAT_ACT;                               /* floor3: the ELF header from the sealed file */
        ans = g_dyn_fs_on ? serve_read_fs(a0, a1, a2) : serve_file_act(SYS_read, a0, a1, a2); break;
    case SYS_fdatasync:   cat = CAT_ACT; ans = serve_file_act(SYS_fdatasync, a0, a1, a2); break;
    case SYS_fsync:       cat = CAT_ACT; ans = serve_file_act(SYS_fsync, a0, a1, a2); break;
    case SYS_close:       cat = CAT_ACT;
#if defined(GATE_ON_BODY)
        if (g_dyn_fs_on) {                                            /* C7 P3b-5a-v: closing the HOLDER's lock fd */
            int ci = si_fd_idx(a0);                                   /* releases the one-writer claim (a refused    */
            if (ci >= 0 && g_fds[ci].kind == SI_FD_LOCK && g_lock_held[ci]) {   /* second claimant's close does not) */
                ns_marker_release(g_nrec_path[ci]); g_lock_held[ci] = 0;
            }
        }
#endif
        ans = g_dyn_fs_on ? serve_close_fs(a0) : 0; break;            /* floor3: release the sealed fd */
    case SYS_fstat:       cat = CAT_ACT;                               /* floor3: ld.so reads libc's st_size */
        ans = g_dyn_fs_on ? serve_fstat_fs(a0, a1) : (uint64_t)sizeof(SERVE_RECORD); break;
    case SYS_newfstatat:  cat = CAT_ACT;                              /* floor3: ld.so stats a library path */
        ans = g_dyn_fs_on ? serve_newfstatat_fs(a1, a2) : serve_file_act(SYS_newfstatat, a0, a1, a2); break;
    case SYS_rename:      cat = CAT_ACT;                              /* C7 P3b-5a-ii: REAL under /rec/ */
        ans = serve_ns_syscall(SYS_rename, a0, a1); break;            /* same-directory write-once swap */
    case SYS_mkdir:       cat = CAT_ACT;                              /* C7 P3b-5a-ii: REAL under /rec/ */
        ans = serve_ns_syscall(SYS_mkdir, a0, a1); break;             /* declare a namespace (a name prefix) */
    case SYS_unlink:      cat = CAT_ACT;                              /* C7 P3b-5a-v: the remove act (S4) under /rec/ */
#if defined(GATE_ON_BODY)
        if (g_dyn_fs_on && a0 && a0 < CANON_LIMIT) {                  /* a *.lock release / a blob handover removal */
            const char *urb = si_rec_basename((const char *)(uintptr_t)a0);
            if (urb && urb[0]) { ans = (fs_remove(urb) == 0) ? 0 : (uint64_t)(-1); break; }   /* record refused */
        }
#endif
        ans = serve_file_act(SYS_unlink, a0, a1, a2); break;
#if defined(GATE_ON_BODY)
    case SYS_unlinkat:    cat = CAT_ACT;                              /* C7-MAINT-5B (A2): rmtree's remove/rmdir under
                                                                      * /rec/tmp — os.unlink/os.rmdir route here via
                                                                      * glibc's unlinkat (dir_fd or AT_FDCWD) */
        ans = g_dyn_fs_on ? serve_unlinkat_fs(a0, a1, a2) : SERVE_ENOSYS; break;
    case SYS_rmdir:       cat = CAT_ACT;                              /* C7-MAINT-5B (A2): rmdir(path) == remove an
                                                                      * emptied /rec/tmp namespace */
        ans = g_dyn_fs_on ? serve_unlinkat_fs(AT_FDCWD_, a0, AT_REMOVEDIR_) : SERVE_ENOSYS; break;
#endif
    case SYS_getdents64:
        if (a0 == MODULE_SEARCH_SENTINEL) { goto module_scan; }
        cat = CAT_ACT;                                                /* floor3: LIST a sealed directory (Q15/:4134) */
        ans = g_dyn_fs_on ? serve_getdents_fs(a0, a1, a2) : serve_file_act(SYS_getdents64, a0, a1, a2); break;

    /* ── category C — module discovery on a live filesystem: the DESIGNED REFUSAL ──────────────────── */
    case SYS_epoll_create1:
    module_scan:
        cat = CAT_C;
#if defined(PLANT_FS_WALK_SERVED)
        verdict = SV_SERVED; g_module_refused = 0; ans = 0;   /* the fault: the scan is served (a fs walk) */
#else
        verdict = SV_REFUSED; g_module_refused = 1;           /* refused: no live-filesystem module scan */
        /* the module bytes come from the SEALED IMAGE (digest-checked at load, precision b), not a walk. */
        g_seal_byte0 = worker_image_start[0];
        ans = SERVE_ENOSYS;
#endif
        break;

    /* ── C7 P3b-5a-v — the one-writer act's HELD claim (host_seam.lock_write's fcntl F_SETLK, F_WRLCK) and
     * its truncate-to-0 shape, served on the *.lock fd class ONLY; every other fcntl/ftruncate keeps its
     * prior verdict (F_GETFD stub / R2 refusal by name). ──────────────────────────────────────────────*/
    case SYS_ftruncate:                                              /* the lock act's shape (ftruncate-to-0) */
        cat = CAT_ACT;
#if defined(GATE_ON_BODY)
        if (g_dyn_fs_on) {
            int fi = si_fd_idx(a0);
            if (fi >= 0 && g_fds[fi].kind == SI_FD_LOCK) { ans = 0; break; }   /* served on a *.lock fd (the marker
                                                                  * bytes are (re)written by the holder-text write) */
        }
#endif
        verdict = SV_REFUSED; ans = SERVE_ENOSYS; break;             /* ftruncate off the lock class: refused (R2) */

    /* ── category D — io-layer / environment probes: the STUBS (degrade gracefully) ────────────────── */
    case SYS_ioctl:       cat = CAT_D; verdict = SV_STUBBED; ans = SERVE_ENOTTY; break;   /* isatty → ENOTTY */
    case SYS_fcntl:
#if defined(GATE_ON_BODY)
        if (g_dyn_fs_on && a1 == F_SETLK) {                          /* the one-writer HELD exclusive claim */
            int fi = si_fd_idx(a0);
            if (fi >= 0 && g_fds[fi].kind == SI_FD_LOCK) {
                cat = CAT_ACT;
                const char *ln = g_nrec_path[fi];
#ifdef PLANT_LOCK_FIRST_REFUSED
                if (!ns_marker_held(ln)) { ans = (uint64_t)(-11); break; }   /* the fault: the FIRST same-process
                                                                 * claim wrongly answered -EAGAIN -> the real
                                                                 * lock_write reds at fcntl (a plant that CAN fire) */
#endif
                /* C7-MAINT-LOCK-POSIX-PROCESS-CLAIM — POSIX record locks (F_SETLK) are PROCESS-associated, and
                 * the body is ONE process (Q11, no fork): a SECOND same-process F_SETLK on a *.lock this process
                 * already holds is GRANTED, exactly as the Linux kernel grants it (host_seam.py:306-325). The
                 * same-process refusal (-EAGAIN) is RETIRED. The CROSS-process refusal — a DIFFERENT process
                 * refused EAGAIN — is not exercisable on a single-process body; it is recorded in the test as
                 * unprovable (a comment + a skip), never asserted, never planted (L19). The cross-process one-
                 * writer property is NOT loosened (L14): a single-process body simply cannot present a second
                 * claimant process. */
                ns_marker_hold(ln); g_lock_held[fi] = 1; ans = 0;   /* granted (same-process re-claim included) */
                break;
            }
        }
#endif
        if (a1 == F_DUPFD_ || a1 == F_DUPFD_CLOEXEC_) {                 /* C7-MAINT-5B: CPython's _Py_dup / scandir(fd)
                                                                        * dups a fd; a REAL dup (not the FD_CLOEXEC
                                                                        * stub that answered stdout -> scandir ENOTDIR) */
            cat = CAT_ACT;
            int nf = serve_dup_fd(a0);
            ans = (nf >= 0) ? (uint64_t)nf : (nf == -2 ? (uint64_t)(-24) : SERVE_EBADF);
            break;
        }
        if (a1 == 3u) {                                                 /* F_GETFL — C7-MAINT-5B: glibc's fdopendir
                                                                        * checks the access mode; a DIRECTORY fd must
                                                                        * read as O_RDONLY (0), else fdopendir -EINVAL.
                                                                        * The stub answered 1 (=O_WRONLY) -> scandir
                                                                        * EINVAL over a /rec/tmp world. */
            int gi = si_fd_idx(a0);
            cat = CAT_D; verdict = SV_STUBBED;
            ans = (gi >= 0 && (g_fds[gi].kind == SI_FD_DIR
#if defined(GATE_ON_BODY)
                               || g_fds[gi].kind == SI_FD_RECDIR   /* C7-MAINT-5B-GATE-BUILD-REPAIR: RECDIR is a
                                                                    * gate-only fd kind; guard so the plain build
                                                                    * does not reach the macro (gate unchanged) */
#endif
                               || g_fds[gi].kind == SI_FD_TREEDIR)) ? 0u : 1u;   /* dir -> O_RDONLY; else the stub */
            break;
        }
        cat = CAT_D; verdict = SV_STUBBED; ans = 1; break;              /* F_GETFD → FD_CLOEXEC (the io-layer stub) */
    case SYS_geteuid:     cat = CAT_D; verdict = SV_STUBBED; ans = 0; break;
    case SYS_getuid:      cat = CAT_D; verdict = SV_STUBBED; ans = 0; break;
    case SYS_getegid:     cat = CAT_D; verdict = SV_STUBBED; ans = 0; break;
    case SYS_getgid:      cat = CAT_D; verdict = SV_STUBBED; ans = 0; break;

    /* ── the network-socket act share (act 9): REFUSED as the native failure until P3b-6 ───────────── */
    case SYS_socket:
        cat = CAT_SOCK; arg = a1;
#if defined(BRIDGE)
        /* C7 P3b-6c (ii): THE ONE RELAYED OPERATION. The interpreter's SYS_socket is routed to the ring-0
         * coroutine bridge, which crosses to the resident lwIP worker (its own map + kstack), runs it to
         * produce the answer WITNESSED (never a fabricated reply, L19), and returns the worker's REAL answer
         * (or an error answer on a worker fault mid-relay, archi :4550) — instead of the socket refusal. */
        if (g_bridge_active && g_serve_enclosure == ENCL_INTERP) {
            uint64_t relayed = bridge_relay(num, a0, a1, a2, a3, a4);
            serve_append((uint32_t)num, CAT_SOCK, SV_SERVED, a2, relayed);
            g_in_act = 0;
            return relayed;
        }
#endif
#if defined(PLANT_SOCKET_SERVED)
        verdict = SV_SERVED; g_socket_refused = 0; ans = 3;   /* the fault: the socket share is served */
#else
        verdict = SV_REFUSED; g_socket_refused = 1;           /* refused as the worker's native failure */
        ans = SERVE_ENOSYS;                                   /* the descriptor stub declined — not built yet */
#endif
        break;

    /* ── a thread's OWN end (C7 P3b-4f-ii): SYS_exit is the fiftieth measured shape (distinct from
     * exit_group, which ends the whole program) — the P3b-4s census missed it. With the concurrency floor
     * active it tears the thread's context down, clears + wakes the child id (CHILD_CLEARTID) so a join
     * returns, and switches away (never returns). ─────────────────────────────────────────────────────*/
    case SYS_exit:
        cat = CAT_B; ans = 0;
        if (g_sched_on) {
            serve_append((uint32_t)num, cat, SV_SERVED, a0, ans);
            sched_thread_exit();               /* clears+wakes the child id, switches away (never returns) */
        }
        break;                                 /* !g_sched_on (the worker never issues SYS_exit): benign */

    /* ── the run terminator: exit_group ends the forty-nine run (category A floor) ─────────────────── */
    case SYS_exit_group:
        cat = CAT_A; ans = 0;
        serve_append(num, cat, SV_SERVED, a0, ans);
        g_serve_exit_status = (int)a0;     /* C7 P3b-5b-i: the REAL exit status (0 green / 1 red), to serial */
        g_serve_exited = 1;
        if (g_dyn_fs_on) {                 /* C7 P3b-5a-vii (precision 3): the pool's at-exit + low-water,
                                            * beside kmain's boot-time count, MEASURE the page-table accrual.
                                            * Scoped to the floor3+ runs (byte-identical serial for 4a/4b). */
            serial_puts("FRAME-POOL-FREE-AT-EXIT: 0x"); serial_puthex32(pmm_free_count()); serial_puts("\n");
            serial_puts("FRAME-POOL-FREE-LOWWATER: 0x"); serial_puthex32(g_frame_free_low); serial_puts("\n");
        }
        body_longjmp(g_active_ctx, 1);     /* unwind to the enclosure serve driver (never returns) */
        break;                             /* unreachable */

    default:
        /* any request BEYOND the measured set is refused as the native failure (L1: nothing beyond). */
        cat = CAT_A; verdict = SV_REFUSED; ans = SERVE_ENOSYS;
        break;
    }

#if defined(PLANT_SERVE_TRAIL_SKIP)
    if (num != SYS_mmap) {                  /* the fault: an acts'-share crossing (mmap) is not a row */
        serve_append((uint32_t)num, cat, verdict, arg, ans);
    }
#else
    serve_append((uint32_t)num, cat, verdict, arg, ans);
#endif
#if defined(PLANT_SWITCH_INSIDE_ACT)
    interrupts_disable();                   /* end the planted mid-act interruptibility window */
#endif
    g_in_act = 0;                           /* the act is complete — the timer may switch again */
    return ans;
}

/* ── the serve trail readback + the checks + the aggregate (called after the ring-3 run) ─────────────*/
static void serve_print_trail(void) {
    serial_puts("SERVE-ROWS: 0x"); serial_puthex32(g_serve_rows); serial_puts("\n");
    for (uint32_t i = 0; i < g_serve_rows; i++) {
        struct serve_row *r = &g_serve_trail[i];
        serial_puts("SERVE-ROW seq=0x");  serial_puthex32(r->seq);
        serial_puts(" num=0x");           serial_puthex32(r->num);
        serial_puts(" cat=0x");           serial_puthex32(r->cat);
        serial_puts(" arg=0x");           serial_puthex64(r->arg);
        serial_puts(" ans=0x");           serial_puthex64(r->ans);
        serial_puts(" sig=0x");           serial_puthex32(r->sig);
        serial_puts(" chain=0x");         serial_puthex32(r->chain);
        serial_puts(r->verdict == SV_SERVED  ? " SERVED\n"
                  : r->verdict == SV_STUBBED ? " STUBBED\n" : " REFUSED\n");
    }
    /* category E — EXCLUDED (harness teardown), named for honesty, never issued/served. */
#if defined(PLANT_SERVE_CATEGORY_E)
    serial_puts("SERVE-EXCLUDED: unlinkat\n");   /* the fault: rmdir dropped from the excluded set */
#else
    serial_puts("SERVE-EXCLUDED: unlinkat rmdir\n");
#endif
}

int serve_finish(int worker_ok) {
    serve_print_trail();

    /* every serve row is UNSIGNED (the body holds no key, sig==0) and OUT of the estate's signed chain
     * (chain==0) — the acts' share INCLUDED (precision a: witnessed like every crossing, never a signed
     * gate row). Each property is ONE check with ONE plant; they do not overlap (KEYLESS reads sig,
     * UNSIGNED reads chain, WITNESSED reads the crossing/row counts). */
    int keyless = 1, unsigned_chain = 1, e_excluded = 1;
    uint32_t acts_seen = 0;
    for (uint32_t i = 0; i < g_serve_rows; i++) {
        struct serve_row *r = &g_serve_trail[i];
        if (r->sig != 0)   { keyless = 0; }
        if (r->chain != 0) { unsigned_chain = 0; }
        if (r->cat == CAT_ACT) { acts_seen++; }
        if (r->num == SYS_unlinkat || r->num == SYS_rmdir) { e_excluded = 0; }   /* E never served */
    }
#if defined(PLANT_SERVE_CATEGORY_E)
    e_excluded = 0;   /* the excluded declaration is corrupted (rmdir dropped) */
#endif

    /* WITNESSED: every crossing is a row (crossings == rows), the worker ended cleanly, AND the acts'
     * share was actually served (acts_seen > 0 — a positive control, so a vacuous phase cannot pass). */
    int witnessed   = (g_serve_crossings > 0) && (g_serve_crossings == g_serve_rows)
                   && worker_ok && (acts_seen > 0);
    int entropy_ok  = (g_entropy_at_bringup == 1);
    int mem_ok      = (g_mem_served_private == 1);
    int thread_ok   = (g_thread_settls == 1);
    int commit_ok   = (g_commit_absolute == 1);
    int futex_ok    = (g_futex_shape_ok == 1);
    int module_ok   = (g_module_refused == 1) && (g_seal_byte0 == 0x7f);  /* ELF magic — bytes from the seal */
    int socket_ok   = (g_socket_refused == 1);

    serial_puts(witnessed    ? "SERVE CHECK WITNESSED: PASS\n"       : "SERVE CHECK WITNESSED: FAIL\n");
    serial_puts(keyless      ? "SERVE CHECK KEYLESS: PASS\n"         : "SERVE CHECK KEYLESS: FAIL\n");
    serial_puts(unsigned_chain ? "SERVE CHECK UNSIGNED: PASS\n"      : "SERVE CHECK UNSIGNED: FAIL\n");
    serial_puts(entropy_ok   ? "SERVE CHECK ENTROPY-BRINGUP: PASS\n" : "SERVE CHECK ENTROPY-BRINGUP: FAIL\n");
    serial_puts(mem_ok       ? "SERVE CHECK MEM-PRIVATE: PASS\n"     : "SERVE CHECK MEM-PRIVATE: FAIL\n");
    serial_puts(thread_ok    ? "SERVE CHECK THREAD-SHAPE: PASS\n"    : "SERVE CHECK THREAD-SHAPE: FAIL\n");
    serial_puts(commit_ok    ? "SERVE CHECK COMMIT-ABSOLUTE: PASS\n" : "SERVE CHECK COMMIT-ABSOLUTE: FAIL\n");
    serial_puts(futex_ok     ? "SERVE CHECK FUTEX-SHAPE: PASS\n"     : "SERVE CHECK FUTEX-SHAPE: FAIL\n");
    serial_puts(module_ok    ? "SERVE CHECK REFUSAL-MODULE: PASS\n"  : "SERVE CHECK REFUSAL-MODULE: FAIL\n");
    serial_puts(socket_ok    ? "SERVE CHECK SOCKET-REFUSED: PASS\n"  : "SERVE CHECK SOCKET-REFUSED: FAIL\n");
    serial_puts(e_excluded   ? "SERVE CHECK EXCLUDED: PASS\n"        : "SERVE CHECK EXCLUDED: FAIL\n");

    int all = witnessed && keyless && unsigned_chain && entropy_ok && mem_ok
            && thread_ok && commit_ok && futex_ok && module_ok && socket_ok && e_excluded;
    serial_puts(all ? "SERVE: PASS\n" : "SERVE: FAIL\n");
    return all ? 0 : 1;
}

#ifdef SOCKET_ACT
/* C7 P3b-6c(iii) A3 — read the socket-act trail back: every relayed shape is ONE CAT_SOCK row and every
 * frame is ONE CAT_FRAME row (the act-witness, L18). Prints each socket row and returns the row counts so
 * floor_socket_act_run can check them; a plant that skips a row makes the count diverge from the acts. */
uint32_t serve_frame_low_water(void) { return g_frame_free_low; }  /* A4: the pool low-water accessor */

void serve_sa_trail_dump(uint32_t *out_sock_rows, uint32_t *out_frame_rows) {
    uint32_t sr = 0, fr = 0;
    serial_puts("SA-TRAIL-ROWS: 0x"); serial_puthex32(g_sa_trail_n); serial_puts("\n");
    for (uint32_t i = 0; i < g_sa_trail_n; i++) {
        struct sa_row *r = &g_sa_trail[i];
        if (r->cat == CAT_SOCK) {
            sr++;
            serial_puts("SA-TRAIL-SOCK num=0x"); serial_puthex32(r->num);
            serial_puts(" verdict=0x"); serial_puthex32(r->verdict);
            serial_puts(" ans=0x"); serial_puthex64(r->ans); serial_puts("\n");
        } else if (r->cat == CAT_FRAME) {
            fr++;
        }
    }
    serial_puts("SA-TRAIL-SOCK-ROWS: 0x"); serial_puthex32(sr);
    serial_puts(" FRAME-ROWS: 0x"); serial_puthex32(fr); serial_puts("\n");
    if (out_sock_rows)  { *out_sock_rows = sr; }
    if (out_frame_rows) { *out_frame_rows = fr; }
}
#endif
