/* gov-os — THE CONCURRENCY FLOOR PROVER (C7 P3b-4f-ii; design/54 §5 L19; the FROZEN P3b-4f A1, threaded).
 *
 * An ORDINARY statically-linked, MULTI-THREADED glibc C program. It is NOT written to fit the body
 * (L19): it is compiled by the guest's own `gcc -static -pthread` against the real C library and
 * libpthread with NO link-base or position flag of any kind (so its first PT_LOAD sits at the x86_64
 * canonical base 0x400000, archi :4122), and it exercises the CONCURRENCY floor the body must be a real
 * home for — real threads that truly take turns on the body's own clock, a lock that truly serializes to
 * an exact total, each thread keeping its own arithmetic (SSE) state across a turn, a timed wait that
 * truly times out, a join that truly waits for the other thread to finish — by doing what an ordinary
 * pthreads program does. Every line below is ordinary glibc C; nothing is shaped to the body.
 *
 * A planted break in the body makes THIS program fail, never a body-side flag (L19):
 *   - a clone3 that returns a fake thread id (no real running context)  -> the workers never run, the
 *     counter never reaches its total, and pthread_join HANGS (the child tid is never cleared).
 *   - a context switch that does NOT save/restore each thread's own SSE state -> a thread's running
 *     floating-point accumulator (live in an xmm register across the loop) is clobbered by the other
 *     thread's work across a turn, and its result no longer matches the single-threaded reference.
 *   - a futex that returns at once (no real wait queue / no real timeout) -> the timed wait does NOT
 *     block until its deadline (returns as if woken) and the timed-wait check reds.
 *   - a thread's own end (SYS_exit) refused, or the child id not cleared/woken on exit -> pthread_join
 *     HANGS (bounded by the body's join watchdog).
 *
 * It writes its results with the raw write(2) to fd 1 (the body routes fd 1 to the serial line), so no
 * stdio buffering/fstat surface is needed. Its SOURCE lives under tests/ (:4107 b), never under src/body
 * (so it is never a signed member); only the built binary is staged for the body to load.
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
    /* the SSE window: a long pure FP loop, the accumulator live in xmm across every iteration. */
    double acc = fp_loop();
    g_fp[id] = acc;
    g_fp_match[id] = (acc == g_fp_ref) ? 1 : 0;    /* identical deterministic loop -> bit-exact, or clobbered */
    /* the exact-count window: increment the shared counter under the real mutex. */
    for (long i = 0; i < ITERS; i++) {
        pthread_mutex_lock(&g_mtx);
        g_counter++;
        pthread_mutex_unlock(&g_mtx);
    }
    return NULL;
}

int main(void) {
    out("PROVER2-START\n");

    /* the clean single-threaded reference for the SSE check (computed before any thread exists). */
    g_fp_ref = fp_loop();

    pthread_t t0, t1;
    if (pthread_create(&t0, NULL, worker, (void *)(intptr_t)0) != 0) { out("PROVER2-CREATE: FAIL\n"); return 2; }
    if (pthread_create(&t1, NULL, worker, (void *)(intptr_t)1) != 0) { out("PROVER2-CREATE: FAIL\n"); return 2; }
    out("PROVER2-CREATE: OK\n");

    /* (A3) A TIMED WAIT THAT TIMES OUT — a semaphore no one posts, with a real absolute deadline. A real
     * futex wait queue with a real timeout returns ETIMEDOUT; a futex that returns at once (no queue) makes
     * this return 0 (as if woken) and the check reds. */
    sem_t s;
    sem_init(&s, 0, 0);
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_nsec += 20L * 1000L * 1000L;             /* +20 ms */
    if (ts.tv_nsec >= 1000000000L) { ts.tv_sec += 1; ts.tv_nsec -= 1000000000L; }
    int r = sem_timedwait(&s, &ts);
    if (r == 0 || errno != ETIMEDOUT) { out("PROVER2-TIMEDWAIT: FAIL (did not time out)\n"); return 3; }
    out("PROVER2-TIMEDWAIT: OK (timed out)\n");

    /* (A2/A4) JOIN — each worker's thread-local end (SYS_exit) clears the child id and wakes the join. A
     * fake tid, a refused SYS_exit, or a child id never cleared/woken makes these HANG. */
    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    out("PROVER2-JOIN: OK\n");

    /* (A2) THE EXACT COUNT — both threads genuinely ran and the mutex serialized. */
    if (g_counter != 2 * ITERS) {
        out("PROVER2-COUNT: FAIL got="); outdec(g_counter); out(" want="); outdec(2 * ITERS); out("\n");
        return 4;
    }
    out("PROVER2-COUNT: OK "); outdec(g_counter); out("\n");

    /* (A2 SSE) each thread's running xmm accumulator survived every turn (per-thread SSE state). */
    if (!g_fp_match[0] || !g_fp_match[1]) {
        out("PROVER2-FP: FAIL (a thread's SSE accumulator was clobbered across a turn)\n");
        return 5;
    }
    out("PROVER2-FP: OK\n");

    /* malloc over the growing break still works with threads up (glibc's arena). */
    unsigned char *p = malloc(4096);
    if (!p) { out("PROVER2-MALLOC: FAIL\n"); return 6; }
    memset(p, 0xE1, 4096);
    int mok = (p[0] == 0xE1 && p[4095] == 0xE1);
    free(p);
    if (!mok) { out("PROVER2-MALLOC: FAIL\n"); return 6; }
    out("PROVER2-MALLOC: OK\n");

    out("PROVER2-DONE rc=0\n");
    return 0;
}
