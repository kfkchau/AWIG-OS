/* gov-os — THE STATIC SINGLE-THREAD FLOOR PROVER (C7 P3b-4f-i; design/54 §5 L19).
 *
 * An ORDINARY statically-linked, SINGLE-THREADED glibc C program. It is NOT written to fit the body
 * (L19): it is compiled by the guest's own `gcc -static` against the real C library with NO link-base
 * or position flag of any kind (so its first PT_LOAD sits at the x86_64 canonical base 0x400000, archi
 * :4122), and it exercises the floor the body must be a real home for — the static loader's initial
 * stack and auxiliary vector, a real address-space manager (the growing break + distinct anonymous
 * maps), the main-thread thread-local base in the machine's %fs, and the machine's SSE state — by doing
 * what an ordinary program does: reach main, touch a thread-local, compute with doubles, malloc/free,
 * map memory, read its own AT_RANDOM. Every line below is ordinary glibc C; nothing is shaped to the
 * body. A planted break in the body (no %fs, SSE off, a fixed VA for every map, a constant AT_RANDOM)
 * makes THIS program fail — it never prints PROVER-DONE, or its own check lines red, or the machine
 * faults it — never a body-side flag (L19). It is a built test artifact staged for the body to load;
 * its SOURCE lives here under tests/ (:4107 b), never under src/body (so it is never a signed member).
 *
 * It writes its results with the raw write(2) to fd 1 (the body routes fd 1 to the serial line), so no
 * stdio buffering/fstat surface is needed — the output appears as the program produces it.
 */
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/auxv.h>
#include <sys/mman.h>

static void out(const char *s) { write(1, s, strlen(s)); }

static void outhex(const unsigned char *b, int n) {
    static const char h[] = "0123456789abcdef";
    char t[2];
    for (int i = 0; i < n; i++) { t[0] = h[(b[i] >> 4) & 15]; t[1] = h[b[i] & 15]; write(1, t, 2); }
}

/* a real thread-local — accessing it forces a %fs-relative load/store (the main-thread TLS base). */
static __thread volatile long tls_probe;

int main(void) {
    out("PROVER-START\n");

    /* (A2) THE MAIN-THREAD %fs BASE — a thread-local access. If the body's arch_prctl(ARCH_SET_FS) did
     * not really install %fs, the machine faults this (a real #PF), the body catches it, and PROVER-DONE
     * never prints. */
    tls_probe = 0x5A5A;
    if (tls_probe != 0x5A5A) { out("PROVER-TLS: FAIL\n"); return 2; }
    out("PROVER-TLS: OK\n");

    /* (A4) THE MACHINE'S SSE STATE — double arithmetic the compiler emits with the xmm registers. If the
     * body did not enable SSE (CR4.OSFXSR), the first SSE instruction #UDs — a real fault the body
     * catches (and glibc's own start-up uses SSE too, so this faults even earlier under the plant). */
    volatile double x = 3.0, y = 7.0;
    double z = x * y + 1.5;                 /* 22.5 */
    if ((int)(z * 2.0) != 45) { out("PROVER-SSE: FAIL\n"); return 3; }
    out("PROVER-SSE: OK\n");

    /* (A3 heap) malloc/free over the growing break — distinct, usable, non-overlapping memory. */
    unsigned char *p = malloc(8192), *q = malloc(8192);
    if (!p || !q) { out("PROVER-MALLOC: FAIL(null)\n"); return 4; }
    memset(p, 0xAB, 8192);
    memset(q, 0xCD, 8192);
    int ok = 1;
    for (int i = 0; i < 8192; i++) { if (p[i] != 0xAB || q[i] != 0xCD) { ok = 0; } }
    if (!(p + 8192 <= q || q + 8192 <= p)) { ok = 0; }    /* non-overlap */
    free(p);
    free(q);
    if (!ok) { out("PROVER-MALLOC: FAIL\n"); return 5; }
    out("PROVER-MALLOC: OK\n");

    /* (A3 distinct VAs) two anonymous maps must NOT alias — the address-space manager hands DISTINCT
     * virtual addresses. A body that returns a fixed VA for every map makes m1 and m2 the same region,
     * so m1's bytes are clobbered by m2's write and the check reds (never a flag). */
    size_t msz = 512 * 1024;
    unsigned char *m1 = mmap(NULL, msz, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    unsigned char *m2 = mmap(NULL, msz, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (m1 == MAP_FAILED || m2 == MAP_FAILED) { out("PROVER-MMAP: FAIL(failed)\n"); return 6; }
    memset(m1, 0x11, msz);
    memset(m2, 0x22, msz);
    int mok = (m1 != m2) && m1[0] == 0x11 && m1[msz - 1] == 0x11 && m2[0] == 0x22 && m2[msz - 1] == 0x22;
    munmap(m1, msz);
    munmap(m2, msz);
    if (!mok) { out("PROVER-MMAP: FAIL(alias)\n"); return 7; }
    out("PROVER-MMAP: OK\n");

    /* (A3 / precision b) THE LOADER'S AUXILIARY VECTOR — the 16 AT_RANDOM bytes the body drew from its
     * own entropy act and handed on the initial stack. Printed so two boots can be compared: a real
     * source differs boot to boot; a planted constant is identical (a check that can fail). */
    unsigned long r = getauxval(AT_RANDOM);
    if (!r) { out("PROVER-AT-RANDOM: FAIL(absent)\n"); return 8; }
    out("PROVER-AT-RANDOM: ");
    outhex((const unsigned char *)r, 16);
    out("\n");

    out("PROVER-DONE rc=0\n");
    return 0;
}
