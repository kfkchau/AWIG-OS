/* gov-os — THE RESERVATION-IS-NOT-COMMITMENT PROVER (C7-MAINT-5B; design/54 §5 L18/L19).
 *
 * WHY THIS PROVER EXISTS. The 5b fix distinguishes a RESERVATION (an anonymous PROT_NONE map — address
 * space consumed, NO frame allocated, nothing mapped) from a COMMITMENT (the protection act that makes a
 * reserved range ACCESSIBLE, where the eager alloc+map+zero law runs, honest ENOMEM when short). This is an
 * ordinary dynamically-linked glibc program (the P3b-4d DYNAMIC build path: gcc -O2 -pthread -no-pie against
 * the real C library). Every line is ordinary glibc C exercising mmap/mprotect/munmap through the real
 * kernel-crossing; the body serves the acts and the program reads its OWN data back (L19), never a
 * body-side flag. Its source lives under tests/ (never src/body), so it is never a signed member; only the
 * built binary is staged, sealed by its sha256 and carried in the -initrd sealed image, exactly like the 4d
 * and churn provers.
 *
 * IT IS NOT WRITTEN TO FIT THE BODY (L19). Two real threads under a real mutex satisfy the dynamic floor's
 * PASS conditions (>=2 threads created+exited), then the phases below run ordinary libc memory acts and
 * check the program's own bytes.
 *
 * THE PHASES, and the ORDER (A2's clean-run touch of a reservation FAULTS — terminal — so it is LAST):
 *   A3-COMMIT  reserve PROT_NONE, mprotect a sub-range accessible (R/W), write it, read it back -> the
 *              commit at the protection act works (A3-COMMIT-OK). PLANT_MPROTECT_NOOP leaves the protection
 *              act a no-op, so the write faults (no A3-COMMIT-OK; a FLOOR3-FAULT at the write).
 *   A4         (i) a RECLAIM LOOP: reserve big PROT_NONE, commit a sub-range, unmap the WHOLE range, many
 *              rounds whose committed pages far exceed the 256 MiB pool -> the committed frames MUST return
 *              (A4-RECLAIM-LOOP-OK), else PLANT_FRAME_LEAK drains the pool and mprotect ENOMEMs (A4-OOM).
 *              (ii) REMAP REUSE: reserve, commit, write P, unmap the whole range, map fresh, write Q, read Q
 *              -> the freed address space is reusable (A4-REMAP-OK).
 *              (iii) ALIAS SENTINEL: reserve 2 pages, commit both, write a sentinel to page 1, unmap ONLY
 *              page 0 -> the sentinel survives (A4-ALIAS-OK). PLANT_FRAME_FREE_UNGUARDED over-frees page 1's
 *              still-live frame, which pmm_alloc (lowest-free-first) hands to the next map -> the two alias
 *              and the sentinel reads back corrupted (A4-ALIAS-CORRUPT). A double free is silent at
 *              pmm_free's bit-test and reds nothing, so the plant frees a still-LIVE frame (L19).
 *   A3-ENOMEM  reserve a range LARGER than the pool, then commit it via the protection act -> the commit
 *              runs out of frames and mprotect returns honest ENOMEM (A3-ENOMEM-OK), then munmap reclaims
 *              the partially-committed frames (no leak). Proven on the clean run.
 *   A2         reserve PROT_NONE and TOUCH it WITHOUT any protection act -> accessible-implies-backed is
 *              universal, so the touch has no legal reading and FAULTS as a ring-3 enclosure violation (the
 *              body records FLOOR3-FAULT with cr2 in the A2 reservation; L18). PLANT_BACK_AT_RESERVE backs
 *              the reservation, so the touch does NOT fault (the run produces NO reservation-touch fault).
 */
#define _GNU_SOURCE
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/mman.h>
#include <pthread.h>

static void out(const char *s) { (void)write(1, s, strlen(s)); }

static void outdec(unsigned long u) {
    char b[24];
    int i = (int)sizeof(b);
    b[--i] = '\0';
    if (u == 0) { b[--i] = '0'; }
    while (u) { b[--i] = (char)('0' + (u % 10)); u /= 10; }
    out(&b[i]);
}

static void outhex(uint64_t u) {
    char b[19];
    b[0] = '0'; b[1] = 'x';
    for (int k = 0; k < 16; k++) { b[2 + k] = "0123456789abcdef"[(u >> ((15 - k) * 4)) & 0xF]; }
    b[18] = '\0';
    out(b);
}

#define PAGE 4096u

/* two real threads under a real mutex — genuine concurrency, so the dynamic floor's PASS conditions hold. */
#define ITERS 2000L
static pthread_mutex_t g_mtx = PTHREAD_MUTEX_INITIALIZER;
static long g_counter;

static void *worker(void *arg) {
    (void)arg;
    for (long i = 0; i < ITERS; i++) {
        pthread_mutex_lock(&g_mtx);
        g_counter++;
        pthread_mutex_unlock(&g_mtx);
    }
    return NULL;
}

static unsigned char pat(unsigned int i, unsigned char key) { return (unsigned char)(key ^ (i & 0xFFu)); }

/* ── A3-COMMIT: reserve PROT_NONE, make a sub-range accessible, write+read it back ─────────────────────── */
static int phase_a3_commit(void) {
    out("A3-START\n");
    unsigned char *r = (unsigned char *)mmap(NULL, 64u * PAGE, PROT_NONE,
                                             MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (r == MAP_FAILED) { out("A3-RESERVE-FAIL\n"); return 3; }
    unsigned char *sub = r + 8u * PAGE;                    /* commit pages [8,24) — 16 pages */
    if (mprotect(sub, 16u * PAGE, PROT_READ | PROT_WRITE) != 0) { out("A3-MPROTECT-FAIL\n"); return 3; }
    for (unsigned i = 0; i < 16u * PAGE; i++) { sub[i] = pat(i, 0x5Au); }   /* <- PLANT_MPROTECT_NOOP faults here */
    unsigned long mism = 0;
    for (unsigned i = 0; i < 16u * PAGE; i++) { if (sub[i] != pat(i, 0x5Au)) { mism++; } }
    if (mism) { out("A3-COMMIT-CORRUPT mism="); outdec(mism); out("\n"); return 3; }
    out("A3-COMMIT-OK\n");
    munmap(r, 64u * PAGE);
    return 0;
}

/* ── A4 (i): the reclaim loop — committed frames must return over churn exceeding the 256 MiB pool ─────── */
#define A4_ROUNDS   80
#define A4_RESV     (2048u * PAGE)     /* 8 MiB reservation per round (mostly untouched)                  */
#define A4_COMMIT   (1024u * PAGE)     /* 4 MiB committed per round; 80*4 MiB = 320 MiB > 256 MiB pool     */
static int phase_a4(void) {
    out("A4-START\n");
    for (int r = 0; r < A4_ROUNDS; r++) {
        unsigned char *base = (unsigned char *)mmap(NULL, A4_RESV, PROT_NONE,
                                                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (base == MAP_FAILED) { out("A4-RESV-FAIL round="); outdec((unsigned long)r); out("\n"); return 4; }
        unsigned char *c = base + 256u * PAGE;             /* commit the middle 4 MiB */
        if (mprotect(c, A4_COMMIT, PROT_READ | PROT_WRITE) != 0) {
            out("A4-OOM round="); outdec((unsigned long)r);
            out("\n");                                     /* committed frames not returned (a real leak) */
            munmap(base, A4_RESV);
            return 4;
        }
        munmap(base, A4_RESV);                             /* unmap the WHOLE range: committed freed, resv skipped */
    }
    out("A4-RECLAIM-LOOP-OK rounds="); outdec((unsigned long)A4_ROUNDS); out("\n");

    /* (ii) REMAP REUSE: the freed address space is reusable, its frames re-served. */
    unsigned char *R2 = (unsigned char *)mmap(NULL, 128u * PAGE, PROT_NONE,
                                              MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (R2 == MAP_FAILED) { out("A4-REMAP-RESV-FAIL\n"); return 4; }
    unsigned char *cc = R2 + 16u * PAGE;
    if (mprotect(cc, 16u * PAGE, PROT_READ | PROT_WRITE) != 0) { out("A4-REMAP-COMMIT-FAIL\n"); return 4; }
    for (unsigned i = 0; i < 16u * PAGE; i++) { cc[i] = pat(i, 0x11u); }
    munmap(R2, 128u * PAGE);
    unsigned char *fresh = (unsigned char *)mmap(NULL, 16u * PAGE, PROT_READ | PROT_WRITE,
                                                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (fresh == MAP_FAILED) { out("A4-REMAP-FRESH-FAIL\n"); return 4; }
    for (unsigned i = 0; i < 16u * PAGE; i++) { fresh[i] = pat(i, 0x22u); }
    unsigned long m2 = 0;
    for (unsigned i = 0; i < 16u * PAGE; i++) { if (fresh[i] != pat(i, 0x22u)) { m2++; } }
    if (m2) { out("A4-REMAP-CORRUPT mism="); outdec(m2); out("\n"); return 4; }
    out("A4-REMAP-OK\n");
    munmap(fresh, 16u * PAGE);

    /* (iii) ALIAS SENTINEL: reserve 2 pages, commit both, keep the sentinel (page 1) mapped across a munmap
     * of ONLY page 0. Under PLANT_FRAME_FREE_UNGUARDED the unguarded free takes the sentinel's still-live
     * frame; pmm_alloc (lowest-free-first) hands it to the next map; the two alias and the sentinel reads
     * back the new map's bytes. With the PTE guard the sentinel's frame is never freed. */
    unsigned char *two = (unsigned char *)mmap(NULL, 2u * PAGE, PROT_NONE,
                                               MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (two == MAP_FAILED) { out("A4-ALIAS-RESV-FAIL\n"); return 4; }
    if (mprotect(two, 2u * PAGE, PROT_READ | PROT_WRITE) != 0) { out("A4-ALIAS-COMMIT-FAIL\n"); return 4; }
    unsigned char *sent = two + PAGE;
    for (unsigned i = 0; i < PAGE; i++) { sent[i] = pat(i, 0xA5u); }
    if (munmap(two, PAGE) != 0) { out("A4-ALIAS-MUNMAP-FAIL\n"); return 4; }   /* unmap ONLY page 0 */
    unsigned char *nw[8];
    for (int k = 0; k < 8; k++) {
        nw[k] = (unsigned char *)mmap(NULL, PAGE, PROT_READ | PROT_WRITE,
                                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (nw[k] == MAP_FAILED) { out("A4-ALIAS-NW-FAIL\n"); return 4; }
        memset(nw[k], 0xCD, PAGE);
    }
    unsigned long am = 0;
    for (unsigned i = 0; i < PAGE; i++) { if (sent[i] != pat(i, 0xA5u)) { am++; } }
    if (am) { out("A4-ALIAS-CORRUPT mism="); outdec(am); out("\n"); return 4; }
    out("A4-ALIAS-OK\n");
    out("A4-DONE\n");
    return 0;
}

/* ── A3-ENOMEM: commit beyond the pool -> honest ENOMEM at the protection act (clean run) ──────────────── */
static int phase_a3_enomem(void) {
    size_t big = (size_t)320 * 1024 * 1024;                /* 320 MiB > 256 MiB pool */
    unsigned char *h = (unsigned char *)mmap(NULL, big, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (h == MAP_FAILED) {
        out("A3-RESERVE-HUGE-FAILED\n");                   /* PLANT_BACK_AT_RESERVE backs+ENOMEMs the reserve */
        return 0;
    }
    errno = 0;
    int mrc = mprotect(h, big, PROT_READ | PROT_WRITE);    /* commit 320 MiB -> must run the pool out */
    if (mrc != 0 && errno == ENOMEM) { out("A3-ENOMEM-OK\n"); }
    else if (mrc != 0) { out("A3-ENOMEM-OTHER errno="); outdec((unsigned long)errno); out("\n"); }
    else { out("A3-ENOMEM-MISSING\n"); }                   /* a silent success would be a bug */
    munmap(h, big);                                        /* reclaim the partially-committed frames (no leak) */
    return 0;
}

/* ── A2 (LAST): touch a reservation without committing -> FAULTS (terminal on the clean run) ───────────── */
static int phase_a2(void) {
    out("A2-START\n");
    unsigned char *rv = (unsigned char *)mmap(NULL, 4u * PAGE, PROT_NONE,
                                              MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (rv == MAP_FAILED) { out("A2-RESV-FAIL\n"); return 2; }
    volatile unsigned char *t = rv + PAGE;                 /* a page inside the reservation */
    out("A2-TOUCH base="); outhex((uint64_t)rv); out(" at="); outhex((uint64_t)(rv + PAGE)); out("\n");
    *t = 0x42;                                             /* CLEAN: faults (terminal). PLANT: no fault. */
    out("A2-NO-FAULT\n");                                  /* reached only if the reservation was backed */
    return 0;
}

int main(void) {
    out("PROVER-START\n");
    pthread_t t0, t1;
    if (pthread_create(&t0, NULL, worker, NULL) != 0) { out("PROVER-THREADS-FAIL\n"); return 9; }
    if (pthread_create(&t1, NULL, worker, NULL) != 0) { out("PROVER-THREADS-FAIL\n"); return 9; }
    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    if (g_counter != 2 * ITERS) { out("PROVER-THREADS-FAIL\n"); return 9; }
    out("PROVER-THREADS-OK\n");

    int rc;
    rc = phase_a3_commit(); if (rc) { out("PROVER-DONE rc="); outdec((unsigned long)rc); out("\n"); return rc; }
    rc = phase_a4();        if (rc) { out("PROVER-DONE rc="); outdec((unsigned long)rc); out("\n"); return rc; }
    rc = phase_a3_enomem(); if (rc) { out("PROVER-DONE rc="); outdec((unsigned long)rc); out("\n"); return rc; }
    rc = phase_a2();        /* clean: faults here (never returns); PLANT_BACK_AT_RESERVE: returns */
    out("PROVER-DONE rc="); outdec((unsigned long)rc); out("\n");
    return rc;
}
