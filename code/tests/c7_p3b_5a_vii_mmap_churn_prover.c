/* gov-os — THE MMAP/MUNMAP CHURN PROVER (C7 P3b-5a-vii; design/54 §5 L19).
 *
 * WHY THIS PROVER EXISTS. The munmap-reclaim plant (serve.c PLANT_FRAME_LEAK — unmap without freeing
 * the owned frame) needs a prover whose map-and-unmap churn genuinely EXCEEDS the 256 MiB frame pool
 * when the reclaim is disabled, so that disabling the reclaim REDS the run by a REAL mechanism (a real
 * out-of-memory), and enabling it runs green (serve_mmap reuses the freed frames). MEASURED, never
 * asserted: a native per-module strace census of the whole estate test suite (planning/evidence/
 * C7-P3b-5a-vii-THE-BODY-RECLAIMS-FRAMES/) found the HEAVIEST ledger module's cumulative munmap at
 * ~30 MiB (test_ep24c/test_ep26) — an order of magnitude below the 256 MiB pool. NO ledger module
 * churns munmap past the pool, so the munmap plant cannot be homed on one (it would be a check that
 * cannot fail, L19). This ordinary real-libc program is that measured prover instead.
 *
 * IT IS NOT WRITTEN TO FIT THE BODY (L19). It is an ordinary dynamically-linked glibc program compiled
 * by the guest's own `gcc -O2 -pthread -no-pie` against the real C library (the P3b-4d DYNAMIC build
 * path). Every line is ordinary glibc C: two real threads under a real mutex (so the dynamic floor's
 * scheduler conditions hold on the clean run, exactly as the 4d prover), then a loop of LARGE
 * malloc/memset/free. Setting a FIXED mmap threshold (mallopt) is the standard, documented way a
 * program that manages large transient buffers keeps them served by mmap and freed by munmap — it is
 * what the program does, not a shape for the body. The body serves the mmap (fresh frames), and free
 * of an mmap'd chunk is a real munmap that reaches serve_munmap. With the reclaim, the freed frames
 * return to the pool and the next round reuses them; without it, every round leaks and the pool drains
 * and malloc returns NULL — the program reports its own OOM by a real mechanism, never a body-side flag.
 *
 * Its source lives under tests/ (never src/body), so it is never a signed member; only the built binary
 * is staged (sealed by its sha256, carried by the -initrd sealed image), exactly like the 4d prover.
 *
 * IT ALSO HOMES A2's PAGE-TABLE-GUARD PLANT (C7 P3b-5a-vii, board :4399). The A2 plant
 * (serve.c PLANT_FRAME_FREE_UNGUARDED — a free WITHOUT the PRESENT+USER guard) over-reaches onto a
 * STILL-PRESENT neighbour page's LIVE frame. It is INERT on the 4d dynamic prover (that program issues
 * no qualifying munmap of a present user page — glibc caches thread stacks, small malloc is arena/brk),
 * so the plant cannot fire there (mgr drove it byte-identical clean). It IS exercised here, by an
 * ordinary real-libc mmap/munmap sequence with the program's OWN data-integrity read: a sentinel page is
 * mmap'd beside a throwaway page, written a known per-offset pattern, and KEPT MAPPED across a partial
 * munmap of only its neighbour. With the guard, the neighbour's frame is freed and the sentinel's frame
 * is untouched, so the pattern reads back intact. WITHOUT the guard, the unguarded free takes the
 * still-live sentinel's frame back to the allocator; pmm_alloc (lowest-free-first, pmm.c) hands that live
 * frame to the very next map; the two mappings ALIAS; the second map's write lands in the sentinel's page;
 * and the sentinel reads back CORRUPTED. A REAL aliasing corruption caught by the read — never a silent
 * within-chunk double-free (a second free of an already-clear bit is a no-op at pmm_free's bit-test, which
 * reds nothing and is refused as a check that cannot fail, L19).
 */
#define _GNU_SOURCE
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <malloc.h>
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

/* two real threads under a real mutex — genuine concurrency, so the dynamic floor's PASS conditions
 * (>=2 threads created and exited, preemption observed) hold on the clean run, as the 4d prover does. */
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

/* CHUNK is well above the fixed mmap threshold set below, so every allocation is served by mmap and
 * every free is a munmap. ROUNDS * CHUNK far exceeds the 256 MiB pool, so with the munmap reclaim
 * disabled the pool drains mid-run; with it, only ~one CHUNK is ever live and the run completes. */
#define CHUNK  (8u * 1024u * 1024u)      /* 8 MiB per round                                          */
#define ROUNDS 64                         /* 64 * 8 MiB = 512 MiB churned — ~2x the 256 MiB pool       */

/* ── A2 (board :4399): the PAGE-TABLE-GUARD plant fires HERE, by real aliasing, caught by our OWN read ──
 * A sentinel page is mmap'd immediately after a throwaway page (ONE 2-page anonymous map -> contiguous
 * virtual addresses: the throwaway at [base], the sentinel at [base + PAGE]). The sentinel is written a
 * known per-offset pattern and KEPT MAPPED while ONLY the throwaway page is munmap'd. serve_munmap's
 * unguarded plant queries the throwaway page's neighbour (== the sentinel), finds it PRESENT, and frees
 * the sentinel's LIVE frame; pmm_alloc (lowest-free-first) then hands that same frame to the next map,
 * which serve_mmap zero-fills and we then overwrite -> the sentinel, still mapped at its own address,
 * reads back corrupted. With the guard the sentinel's frame is never freed, so the pattern survives.
 * Real-libc mmap/munmap only; the check is our own read of our own bytes (L19), never a body-side flag. */
#define APAGE 4096u
static unsigned char apat(unsigned int i) { return (unsigned char)(0xA5u ^ (i & 0xFFu)); }

static int alias_integrity_test(void) {
    out("ALIAS-TEST-START\n");

    /* one 2-page anonymous map: [region .. region+PAGE) throwaway, [region+PAGE .. region+2*PAGE) sentinel.
     * serve_mmap's page loop pmm_alloc's the two lowest free frames in order, so the throwaway frame is
     * lower than the sentinel frame and every OTHER free frame is higher than both — the fact that makes the
     * over-freed sentinel frame the lowest free frame (thus the next one handed out) under the plant. */
    unsigned char *region = (unsigned char *)mmap(NULL, 2u * APAGE, PROT_READ | PROT_WRITE,
                                                  MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (region == MAP_FAILED) { out("ALIAS-TEST: MMAP-FAIL region\n"); return 8; }
    unsigned char *sentinel = region + APAGE;
    for (unsigned int i = 0; i < APAGE; i++) { sentinel[i] = apat(i); }

    /* unmap ONLY the throwaway page; the sentinel page stays mapped. With the guard: the throwaway's frame
     * is freed, the sentinel's is kept. Without the guard: the plant queries the throwaway's neighbour
     * (== the sentinel), frees the sentinel's still-live frame, and the throwaway's own frame leaks. */
    if (munmap(region, APAGE) != 0) { out("ALIAS-TEST: MUNMAP-FAIL\n"); return 8; }

    /* take fresh pages and paint them a different value. Under the plant the sentinel's freed frame is now
     * the lowest free frame, so the FIRST of these maps aliases it and its paint (over serve_mmap's
     * zero-fill) lands in the sentinel's page. Under the guard none of these frames is the sentinel's (it
     * was never freed), so the sentinel is untouched. A handful gives margin; only its own frame matters. */
    unsigned char *nw[8];
    for (int k = 0; k < 8; k++) {
        nw[k] = (unsigned char *)mmap(NULL, APAGE, PROT_READ | PROT_WRITE,
                                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (nw[k] == MAP_FAILED) { out("ALIAS-TEST: MMAP-FAIL nw\n"); return 8; }
        memset(nw[k], 0xCD, APAGE);
    }

    /* our own data-integrity read: the sentinel, still mapped at its own address, must still hold apat(). */
    unsigned long mism = 0;
    for (unsigned int i = 0; i < APAGE; i++) { if (sentinel[i] != apat(i)) { mism++; } }

    if (mism == 0) {
        out("ALIAS-INTEGRITY: OK\n");
        return 0;
    }
    out("ALIAS-CORRUPT mismatches="); outdec(mism); out("\n");
    return 9;                                     /* a REAL aliasing corruption caught by our own read */
}

int main(void) {
    out("MMAPCHURN-START\n");

    /* genuine concurrency first (pool healthy), so the floor's scheduler PASS conditions hold. */
    pthread_t t0, t1;
    if (pthread_create(&t0, NULL, worker, NULL) != 0) { out("MMAPCHURN-THREADS: FAIL\n"); return 2; }
    if (pthread_create(&t1, NULL, worker, NULL) != 0) { out("MMAPCHURN-THREADS: FAIL\n"); return 2; }
    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    if (g_counter != 2 * ITERS) { out("MMAPCHURN-THREADS: FAIL\n"); return 2; }
    out("MMAPCHURN-THREADS: OK\n");

    /* a FIXED mmap threshold: every CHUNK malloc is served by mmap, every free is a munmap. Setting it
     * explicitly disables glibc's dynamic mmap-threshold growth, so the churn is deterministic. */
    mallopt(M_MMAP_THRESHOLD, 1 * 1024 * 1024);
    mallopt(M_TRIM_THRESHOLD, -1);

    unsigned long churned_mib = 0;
    for (int r = 0; r < ROUNDS; r++) {
        unsigned char *p = (unsigned char *)malloc(CHUNK);
        if (!p) {
            out("MMAPCHURN-OOM round="); outdec((unsigned long)r);
            out(" churned_mib="); outdec(churned_mib); out("\n");
            return 7;                         /* the pool drained — a REAL out-of-memory, not a flag */
        }
        memset(p, 0xC7, CHUNK);               /* touch every page — a genuinely PRESENT+USER mapping */
        { volatile unsigned char sink = (unsigned char)(p[0] ^ p[CHUNK - 1]); (void)sink; }
        free(p);                              /* free of an mmap'd chunk -> munmap -> serve_munmap    */
        churned_mib += CHUNK >> 20;
    }
    out("MMAPCHURN-DONE churned_mib="); outdec(churned_mib); out("\n");

    /* A2 (board :4399): the churn completed (the pool sustained it); now exercise the PAGE-TABLE-GUARD plant
     * by real aliasing, caught by our own data-integrity read. Under PLANT_FRAME_LEAK this line is never
     * reached (the churn OOMs above and returns 7); under the unguarded plant the churn completes here (it
     * only over-frees, it does not drain the pool) and this reds by corruption. */
    return alias_integrity_test();
}
