/* gov-os — THE DYNAMIC LOADER PROVER (C7 P3b-4d; design/54 §5 L19; the floor of P3b-4f UNDER ld.so).
 *
 * An ORDINARY DYNAMICALLY-LINKED, MULTI-THREADED glibc C program. It is NOT written to fit the body
 * (L19): it is compiled by the guest's own `gcc -pthread -no-pie` against the real C library with NO
 * link flag beyond -no-pie (so its first PT_LOAD sits at the x86_64 canonical base 0x400000 — a dynamic
 * gcc default is PIE/ET_DYN, which ld.so would place at an arbitrary base; the body fixes the program at
 * 0x400000, L20/P3b-4m, so the prover is ET_EXEC/-no-pie, Q15/:4134). Its start-up goes THROUGH the real
 * dynamic linker: the body honours its PT_INTERP, loads the requested ld.so from the sealed image, lays
 * the auxiliary vector, and hands over; ld.so resolves libc.so from the sealed image by path+offset and
 * relocates the program. Then the program does what an ordinary pthreads program does — every line below
 * is ordinary glibc C; nothing is shaped to the body.
 *
 * It proves the same floor P3b-4f proved (two threads under a mutex reach an exact count, each thread
 * keeps its own SSE accumulator across a turn, a timed wait truly times out, the joins return, malloc
 * over the growing break works) — but now it reaches `main` only because the DYNAMIC linker ran first.
 *
 * A planted break in the body makes THIS program fail, never a body-side flag (L19):
 *   - a byte changed in the sealed image      -> the digest-check refuses the load; the program never
 *                                                starts (no PROVER3-START on serial).
 *   - PT_INTERP ignored / the handover skipped -> the body enters the program's e_entry directly with
 *                                                libc unrelocated; the program faults before main.
 *   - the record FS and the sealed image made to collide (libc shadowed by the empty record FS) -> ld.so
 *                                                reads the wrong bytes for libc and cannot load it.
 *
 * It writes with the raw write(2) to fd 1 (the body routes fd 1 to the serial line), so no stdio
 * buffering surface is needed. Its SOURCE lives under tests/ (:4107 b), never under src/body (so it is
 * never a signed member); only the built binary is staged for the body to load.
 */
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>
#include <pthread.h>
#include <semaphore.h>

static void out(const char *s) { (void)write(1, s, strlen(s)); }

static void outdec(long v) {
    char b[24];
    int i = (int)sizeof(b);
    b[--i] = '\0';
    unsigned long u = (v < 0) ? (unsigned long)(-v) : (unsigned long)v;
    if (u == 0) { b[--i] = '0'; }
    while (u) { b[--i] = (char)('0' + (u % 10)); u /= 10; }
    if (v < 0) { b[--i] = '-'; }
    out(&b[i]);
}

/* the shared counter, guarded by a real mutex — two threads reach the EXACT total or the mutex failed. */
static pthread_mutex_t g_mtx = PTHREAD_MUTEX_INITIALIZER;
static long g_counter;                 /* NON-atomic: only the mutex makes the total exact             */
#define ITERS 2000L                     /* per thread; the exact total is 2*ITERS                       */

/* per-thread floating-point work: a PURE recurrence kept in an xmm register across the whole loop, with
 * NO call inside (so the accumulator lives in xmm, not spilled). Deterministic — main computes the same
 * loop single-threaded as the reference; a switch that does not save/restore the thread's own xmm state
 * clobbers the running accumulator with the other thread's work, so the result no longer matches. */
#define FP_ITERS 200000L
static double fp_loop(void) {
    double acc = 1.0;
    for (long i = 0; i < FP_ITERS; i++) {
        acc = acc * 1.0000001 + ((double)(i & 1023) * 0.5 + 0.25);
    }
    return acc;
}

static volatile double g_fp[2];
static volatile int    g_fp_match[2];
static double g_fp_ref;                /* main's single-threaded reference (computed before any thread) */

static void *worker(void *arg) {
    long id = (long)(intptr_t)arg;
    double acc = fp_loop();
    g_fp[id] = acc;
    g_fp_match[id] = (acc == g_fp_ref) ? 1 : 0;    /* identical deterministic loop -> bit-exact, or clobbered */
    for (long i = 0; i < ITERS; i++) {
        pthread_mutex_lock(&g_mtx);
        g_counter++;
        pthread_mutex_unlock(&g_mtx);
    }
    return NULL;
}

int main(void) {
    out("PROVER3-START\n");   /* reached only because the DYNAMIC linker resolved libc and ran the program */

    /* the clean single-threaded reference for the SSE check (computed before any thread exists). */
    g_fp_ref = fp_loop();

    pthread_t t0, t1;
    if (pthread_create(&t0, NULL, worker, (void *)(intptr_t)0) != 0) { out("PROVER3-CREATE: FAIL\n"); return 2; }
    if (pthread_create(&t1, NULL, worker, (void *)(intptr_t)1) != 0) { out("PROVER3-CREATE: FAIL\n"); return 2; }
    out("PROVER3-CREATE: OK\n");

    /* A TIMED WAIT THAT TIMES OUT — a semaphore no one posts, with a real absolute deadline. */
    sem_t s;
    sem_init(&s, 0, 0);
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_nsec += 20L * 1000L * 1000L;             /* +20 ms */
    if (ts.tv_nsec >= 1000000000L) { ts.tv_sec += 1; ts.tv_nsec -= 1000000000L; }
    int r = sem_timedwait(&s, &ts);
    if (r == 0 || errno != ETIMEDOUT) { out("PROVER3-TIMEDWAIT: FAIL (did not time out)\n"); return 3; }
    out("PROVER3-TIMEDWAIT: OK (timed out)\n");

    /* JOIN — each worker's thread-local end (SYS_exit) clears the child id and wakes the join. */
    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    out("PROVER3-JOIN: OK\n");

    /* THE EXACT COUNT — both threads genuinely ran and the mutex serialized. */
    if (g_counter != 2 * ITERS) {
        out("PROVER3-COUNT: FAIL got="); outdec(g_counter); out(" want="); outdec(2 * ITERS); out("\n");
        return 4;
    }
    out("PROVER3-COUNT: OK "); outdec(g_counter); out("\n");

    /* each thread's running xmm accumulator survived every turn (per-thread SSE state). */
    if (!g_fp_match[0] || !g_fp_match[1]) {
        out("PROVER3-FP: FAIL (a thread's SSE accumulator was clobbered across a turn)\n");
        return 5;
    }
    out("PROVER3-FP: OK\n");

    /* malloc over the growing break still works with threads up (glibc's arena, resolved via the linker). */
    unsigned char *p = malloc(4096);
    if (!p) { out("PROVER3-MALLOC: FAIL\n"); return 6; }
    memset(p, 0xE1, 4096);
    int mok = (p[0] == 0xE1 && p[4095] == 0xE1);
    free(p);
    if (!mok) { out("PROVER3-MALLOC: FAIL\n"); return 6; }
    out("PROVER3-MALLOC: OK\n");

    out("PROVER3-DONE rc=0\n");
    return 0;
}
