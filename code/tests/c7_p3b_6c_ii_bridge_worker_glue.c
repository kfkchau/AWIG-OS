/* gov-os C7 P3b-6c slice (ii) — the BRIDGE worker's glue (design/54 §5 L18/L19/I3; §7 P3b-6c slice ii).
 *
 * CONFIGURATION ONLY. Compiled with the UNMODIFIED lwIP 2.2.0 core (the same byte-for-byte source the 6b
 * worker links, I3) into a static NO_SYS worker. This worker is the PEER the ring-0 coroutine bridge relays
 * ONE operation to: the body's bridge writes the relayed op+arg into a shared page in THIS enclosure's own
 * map, runs the worker at ring 3, and reads back the worker's OWN answer + witness. The answer is PRODUCED
 * BY THE WORKER'S EXECUTION (never a fabricated reply, L19): the real lwIP stack initialises (lwip_init —
 * mem/memp/pbuf/netif/ip bring-up), the worker computes a deterministic answer from the relayed arg, and it
 * writes a WITNESS the bridge reads so a canned answer (the bridge skipping the worker) leaves the witness
 * absent and reds. A FAULT op reaches the body's own memory at ring 3 — the hardware #PFs (US), the body
 * recovers per this enclosure's map (L18) and hands the waiting interpreter an ERROR answer (archi :4550).
 *
 * This is a test fixture (content), NEVER an attested member; the built worker IMAGE is content, never a
 * signed member (§9 mechanism 3 / I3). The lwIP core is byte-unmodified; our glue only configures + relays.
 */
#include "lwip/init.h"
#include "lwip/inet_chksum.h"

#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>

/* the one lwIP port symbol the byte-unmodified core references at link time (timeouts.c): the monotonic
 * clock. The bridge worker does no timers, but the symbol must resolve. clock_gettime is served for the
 * lwIP enclosure exactly as for the 6b worker. */
u32_t sys_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (u32_t)((uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u);
}

/* ── the shared relay page: a fixed USER VA the body maps into THIS enclosure's map (slice i, private half).
 * It sits between the worker's image (0x400000+) and its stack (0x30000000), clear of the brk and of the
 * mmap region (SERVE_MMAP_BASE 0x700000000000). The body writes op+arg before entering the worker and reads
 * witness+answer after; the worker reads op+arg and writes witness/answer/evidence. ────────────────────*/
#define BRIDGE_SHARED_VA      0x20000000UL
#define BRIDGE_OP_NORMAL      0x1ULL       /* perform the op, produce the answer                          */
#define BRIDGE_OP_FAULT       0x2ULL       /* reach the body's memory at ring 3 -> #PF (A3 / the precision)*/
#define BRIDGE_WITNESS_MAGIC  0x6c77495057334bULL   /* "lwIPP3K" — the worker reached the write (executed) */
/* answer = (arg & 48-bit) | 0x10000 : a deterministic transform of the relayed arg (round-trip integrity;
 * the prover replicates it). The 0x10000 floor keeps it a positive value well clear of glibc's errno band
 * [-4095,-1], so the interpreter's raw syscall reads it as a value, not an error. */
#define BRIDGE_ANS_TRANSFORM(a) (((a) & 0xFFFFFFFFFFFFULL) | 0x10000ULL)

struct bridge_slot {
    volatile uint64_t op;             /* body -> worker: the relayed op                                  */
    volatile uint64_t arg;            /* body -> worker: the relayed argument (a nonce)                  */
    volatile uint64_t witness;        /* worker -> body: BRIDGE_WITNESS_MAGIC iff the worker executed    */
    volatile uint64_t answer;         /* worker -> body: the worker's real answer (arg ^ XOR)            */
    volatile uint64_t lwip_evidence;  /* worker -> body: a value the byte-unmodified lwIP checksum ran   */
};

/* ── minimal serial witness (write to fd 2 -> the body's serve.c routes SYS_write to the serial line, so
 * the worker's OWN execution is witnessed on the boot serial too, not only in the shared slot). ────────*/
static void w2(const void *b, unsigned long n) { ssize_t r = write(2, b, n); (void)r; }
static void say(const char *s) { w2(s, (unsigned long)strlen(s)); }
static void sayhex(const char *lbl, uint64_t v) {
    char b[80]; unsigned i = 0;
    while (lbl[i]) { b[i] = lbl[i]; i++; }
    b[i++] = '0'; b[i++] = 'x';
    for (int s = 60; s >= 0; s -= 4) { unsigned d = (unsigned)((v >> s) & 0xF); b[i++] = (char)(d < 10 ? '0' + d : 'a' + d - 10); }
    b[i++] = '\n';
    w2(b, i);
}

int main(void) {
    say("BRIDGE-WORKER-MAIN\n");   /* glibc init completed, main reached (each relay is a FRESH worker) */
    volatile struct bridge_slot *slot = (volatile struct bridge_slot *)(uintptr_t)BRIDGE_SHARED_VA;
    uint64_t op  = slot->op;
    uint64_t arg = slot->arg;

    if (op == BRIDGE_OP_FAULT) {
        /* the worker faults MID-operation, DELIBERATELY and DETERMINISTICALLY: a ring-3 reach at the body's
         * own image (1 MiB, a supervisor page shared in every map's kernel half) -> hardware #PF (US). The
         * body recovers per THIS enclosure's map (L18) and returns the waiting interpreter an ERROR answer
         * (archi :4550). No witness is written — the operation did not complete. */
        slot->witness = 0;
        say("BRIDGE-WORKER-FAULTING\n");
        volatile uint64_t *body_mem = (volatile uint64_t *)(uintptr_t)0x100000ULL;
        uint64_t sink = *body_mem;    /* #PF here — never returns to the worker */
        slot->answer = sink;          /* unreachable */
        _exit(2);
    }

    /* THE REAL BORROWED STACK EXECUTES (L19/I3): lwip_init brings up the unmodified lwIP core (mem, memp,
     * pbuf, netif, ip). If it faulted or hung, the worker would never reach the witness write below. */
    lwip_init();

    /* a value the byte-unmodified lwIP checksum code produced over a fixed probe — printed as evidence the
     * borrowed core actually ran (not prover-recomputed; its PRESENCE/nonzero-ness is the witness). */
    static const uint8_t probe[8] = { 0xde, 0xad, 0xbe, 0xef, 0x12, 0x34, 0x56, 0x78 };
    uint16_t chk = inet_chksum((void *)probe, sizeof(probe));   /* lwIP's own checksum (byte-unmodified) */

    say("BRIDGE-WORKER-RAN\n");
    sayhex("BRIDGE-WORKER-OP=",  op);
    sayhex("BRIDGE-WORKER-ARG=", arg);
    sayhex("BRIDGE-WORKER-LWIPCHK=", (uint64_t)chk);

    /* the worker's OWN answer to the relayed op: a deterministic transform of the arg (round-trip
     * integrity — the prover replicates it and checks the interpreter received exactly this). */
    uint64_t ans = BRIDGE_ANS_TRANSFORM(arg);
    slot->answer        = ans;
    slot->lwip_evidence = (uint64_t)chk;
    slot->witness       = BRIDGE_WITNESS_MAGIC;   /* LAST: proves the worker executed to completion */
    sayhex("BRIDGE-WORKER-ANS=", ans);
    say("BRIDGE-WORKER-DONE\n");
    _exit(0);
    return 0;
}
