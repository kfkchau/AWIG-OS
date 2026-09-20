/* gov-os — THE SLOT-BOUND DISCRIMINATING PROVER (C7-MAINT-5B-THREAD-SLOT-RECLAIM; design/54 §5 L19).
 *
 * An ORDINARY statically-linked, MULTI-THREADED glibc C program. It is NOT written to fit the body
 * (L19): it is compiled by the guest's own `gcc -static -pthread` against the real C library and
 * libpthread with NO link-base or position flag, and it exercises exactly ONE property the body must be
 * a real home for — a finished thread's SLOT is RECLAIMED so a program bounded by PEAK concurrency (not
 * by cumulative creations) runs, and the reclaim NEVER disturbs a live thread's join.
 *
 * THE SHAPE (why it discriminates the slot table from memory):
 *   - It keeps a HANDFUL of long-lived workers blocked on a semaphore (KEEP), so peak concurrency stays
 *     small and only a few 8 MiB stacks are ever live — memory never binds.
 *   - It then CHURNS: create one short thread, join it, repeat ROUNDS times. Cumulative creations
 *     (KEEP + ROUNDS) exceed SCHED_MAX_THREADS, so the slot table MUST be reused for the program to run.
 *   - With the reclaim ON: each finished churn thread's slot is reclaimed and reused -> all creations
 *     succeed at low peak -> SLOTPROVER-DONE (green).
 *
 * A plant in the body makes THIS program fail by the SLOT mechanism, distinct from any memory failure,
 * never a body-side flag (L19):
 *   - PLANT_NO_RECLAIM: a finished thread's slot LEAKS. The churn exhausts the 32-slot table and a
 *     create returns EAGAIN while only a handful of stacks are live (memory free). The blocked workers
 *     are UNTOUCHED (a reclaim-off failure is a slot-count exhaustion, not corruption): they join
 *     cleanly -> SLOTPROVER-KEEP-INTACT: OK, then a clean non-zero exit. NO SLOTPROVER-DONE.
 *   - PLANT_RECLAIM_UNSAFE: the allocator reuses a still-LIVE (blocked) worker's slot when the table is
 *     full. That worker's kernel context is reused under it, so releasing + joining the workers HANGS
 *     (its join never returns). NO SLOTPROVER-KEEP-INTACT, NO SLOTPROVER-DONE.
 *
 * It writes its results with the raw write(2) to fd 1 (the body routes fd 1 to the serial line), so no
 * stdio buffering surface is needed. Its SOURCE lives under tests/ (never src/body): only the built
 * binary is staged for the body to load; it is never a signed member.
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

/* KEEP long-lived workers block here so they stay LIVE (T_BLOCKED) across the whole churn. A handful,
 * so peak concurrency (KEEP + one churn + main) is small and memory never binds. */
#define KEEP 3
/* churn creations. cumulative = KEEP + ROUNDS = 43 > SCHED_MAX_THREADS-1 (31 non-main slots): the slot
 * table MUST be reused for the program to complete, but only KEEP+1 stacks are ever live. */
#define ROUNDS 40

static sem_t g_release;                 /* the workers wait on this until the churn is done      */
static pthread_mutex_t g_kmtx = PTHREAD_MUTEX_INITIALIZER;
static long g_keep_ran;                 /* each worker increments after release -> exact == KEEP */

static void *keepalive(void *arg) {
    (void)arg;
    sem_wait(&g_release);               /* BLOCK live until released (T_BLOCKED across the churn)  */
    pthread_mutex_lock(&g_kmtx);
    g_keep_ran++;
    pthread_mutex_unlock(&g_kmtx);
    return NULL;
}

static volatile long g_churn_sum;
static void *churn(void *arg) {
    long id = (long)(intptr_t)arg;
    /* touch a page of the thread's own stack so the mapping is real, do trivial work, exit. */
    volatile char buf[4096];
    buf[0] = (char)id;
    buf[4095] = (char)(id + 1);
    g_churn_sum += (long)buf[0] + (long)buf[4095];
    return NULL;
}

/* release + join the KEEP workers. Returns 1 if all workers ran (intact); under a corrupting plant the
 * join HANGS and this never returns (the body's boot times out) — the red is a real hang, not a flag. */
static int release_and_join_keep(pthread_t *keep) {
    for (int i = 0; i < KEEP; i++) { sem_post(&g_release); }
    for (int i = 0; i < KEEP; i++) { pthread_join(keep[i], NULL); }
    return (g_keep_ran == KEEP) ? 1 : 0;
}

int main(void) {
    out("SLOTPROVER-START\n");
    sem_init(&g_release, 0, 0);

    /* 1) KEEP long-lived workers, each blocking LIVE on the semaphore. */
    pthread_t keep[KEEP];
    for (int i = 0; i < KEEP; i++) {
        int rc = pthread_create(&keep[i], NULL, keepalive, NULL);
        if (rc != 0) { out("SLOTPROVER-KEEP-CREATE: FAIL rc="); outdec(rc); out("\n"); return 2; }
    }
    out("SLOTPROVER-KEEP: OK "); outdec(KEEP); out(" blocked (live)\n");

    /* 2) churn: create + join a short thread ROUNDS times. cumulative crosses the slot table; peak live
     *    stays KEEP + 1. With the reclaim ON every finished slot is reused -> all succeed. */
    long created = KEEP;
    long peak_live = KEEP + 1;
    for (long r = 0; r < ROUNDS; r++) {
        pthread_t c;
        int rc = pthread_create(&c, NULL, churn, (void *)(intptr_t)r);
        if (rc != 0) {
            /* SLOT-TABLE EXHAUSTION (the reclaim-off shape). Distinct from memory: only KEEP+1 stacks
             * were ever live, and the create failed with EAGAIN (the allocator refused a slot). */
            out("SLOTPROVER-SLOT-EXHAUST rc="); outdec(rc);
            out(rc == EAGAIN ? " (EAGAIN: the slot table refused a slot)" : " (unexpected rc)");
            out(" created="); outdec(created);
            out(" peak_live="); outdec(peak_live); out("\n");
            /* the blocked workers are UNTOUCHED by a slot-count exhaustion: they join cleanly. */
            if (release_and_join_keep(keep)) {
                out("SLOTPROVER-KEEP-INTACT: OK "); outdec(g_keep_ran);
                out(" (the live workers were never disturbed)\n");
            } else {
                out("SLOTPROVER-KEEP-INTACT: FAIL got="); outdec(g_keep_ran); out("\n");
            }
            return 3;
        }
        created++;
        pthread_join(c, NULL);         /* join immediately -> peak live stays KEEP + 1 */
    }
    out("SLOTPROVER-CHURN: OK created="); outdec(created);
    out(" peak_live="); outdec(peak_live);
    out(" (cumulative > SCHED_MAX_THREADS, slots reused)\n");

    /* 3) release + join the workers. A SAFE reclaim never disturbed them -> all ran. A corrupting reuse
     *    (PLANT_RECLAIM_UNSAFE) stole a live worker's slot -> this HANGS (no DONE, boot times out). */
    if (!release_and_join_keep(keep)) {
        out("SLOTPROVER-KEEP-COUNT: FAIL got="); outdec(g_keep_ran); out(" want="); outdec((long)KEEP); out("\n");
        return 4;
    }
    out("SLOTPROVER-KEEP-COUNT: OK "); outdec(g_keep_ran); out("\n");
    out("SLOTPROVER-DONE created="); outdec(created);
    out(" peak_live="); outdec(peak_live); out(" rc=0\n");
    return 0;
}
