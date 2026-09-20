/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — a seeded real source of chance on the metal (C7 P3b-3; A1/A2; P3b-s #7).
 *
 * The entropy act (os.urandom above the seam today) realized as a real CSPRNG — ChaCha20 — KEYED FROM
 * A RUNTIME SOURCE at boot: rdrand where the CPU offers it, mixed with interrupt-timing jitter (the
 * exact tsc at each timer IRQ, fed in by idt.c) and the tsc at seed time. A predictable source is
 * worse than none (P3b-s Q-B/#7), so the seed is NEVER a compile-time constant — which also keeps the
 * .elf byte-reproducible (no seed baked in; the chance is a RUNTIME output only, A3). Two draws differ
 * (the CSPRNG advances its counter); the output is not all-zero and not a fixed sequence. ChaCha20 is a
 * small, well-understood, read-whole stream cipher (design/47 §2 I3: no opaque code in the signed
 * base). All arithmetic is 32-bit (no libgcc on a freestanding -m32 body).
 *
 * A2 near-misses (build.sh -D flags):
 *   PLANT_ENTROPY_CONSTANT — a source that returns the SAME bytes every draw: two draws are equal, so
 *                            the self-check ("two draws differ") FAILs, caught in-body.
 *   PLANT_ENTROPY_UNSEEDED — key from a FIXED compile-time constant, not a runtime source: two draws
 *                            still differ WITHIN a boot (the counter advances), but the output is
 *                            IDENTICAL ACROSS BOOTS — caught by the acceptance's cross-boot compare
 *                            (a predictable source is worse than none; the .elf would carry the seed).
 */
#include "body.h"
#include "clock.h"

/* ── the runtime seed sources ─────────────────────────────────────────────────────────────────*/
static volatile uint32_t g_jit_a;   /* interrupt-timing jitter, fed from the IRQ0 handler */
static volatile uint32_t g_jit_b;

void entropy_feed_jitter(uint32_t sample_lo) {
    /* mix the exact tsc-at-delivery into the pool with 32-bit xorshift-style stirring (no 64-bit ops) */
    g_jit_a ^= sample_lo + 0x9E3779B9u;
    g_jit_a = (g_jit_a << 13) | (g_jit_a >> 19);
    g_jit_b += g_jit_a ^ (g_jit_b << 7);
    g_jit_b = (g_jit_b << 17) | (g_jit_b >> 15);
}

static int has_rdrand(void) {
    uint32_t ecx;
    __asm__ volatile("cpuid" : "=c"(ecx) : "a"(1) : "ebx", "edx");
    return (ecx >> 30) & 1;   /* CPUID.01H:ECX.RDRAND[bit 30] */
}

static int rdrand32(uint32_t *out) {
    unsigned char ok;
    uint32_t v;
    for (int i = 0; i < 20; i++) {
        __asm__ volatile("rdrand %0; setc %1" : "=r"(v), "=qm"(ok));
        if (ok) {
            *out = v;
            return 1;
        }
    }
    return 0;
}

/* ── ChaCha20 (the CSPRNG) ────────────────────────────────────────────────────────────────────*/
static uint32_t g_state[16];       /* constants | key[8] | counter | nonce[3] */
static uint8_t  g_block[64];       /* the current keystream block            */
static uint32_t g_block_used = 64; /* bytes consumed from g_block (force a refill on first draw) */
static int      g_seed_nonzero;

static inline uint32_t rotl32(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}

#define QR(a, b, c, d)                 \
    a += b; d ^= a; d = rotl32(d, 16); \
    c += d; b ^= c; b = rotl32(b, 12); \
    a += b; d ^= a; d = rotl32(d, 8);  \
    c += d; b ^= c; b = rotl32(b, 7)

static void chacha20_block(const uint32_t in[16], uint8_t out[64]) {
    uint32_t x[16];
    for (int i = 0; i < 16; i++) {
        x[i] = in[i];
    }
    for (int i = 0; i < 10; i++) {            /* 10 double-rounds = 20 rounds */
        QR(x[0], x[4], x[8],  x[12]);
        QR(x[1], x[5], x[9],  x[13]);
        QR(x[2], x[6], x[10], x[14]);
        QR(x[3], x[7], x[11], x[15]);
        QR(x[0], x[5], x[10], x[15]);
        QR(x[1], x[6], x[11], x[12]);
        QR(x[2], x[7], x[8],  x[13]);
        QR(x[3], x[4], x[9],  x[14]);
    }
    for (int i = 0; i < 16; i++) {
        uint32_t w = x[i] + in[i];
        out[i * 4 + 0] = (uint8_t)(w & 0xFF);
        out[i * 4 + 1] = (uint8_t)((w >> 8) & 0xFF);
        out[i * 4 + 2] = (uint8_t)((w >> 16) & 0xFF);
        out[i * 4 + 3] = (uint8_t)((w >> 24) & 0xFF);
    }
}

void entropy_seed_init(void) {
    uint32_t key[8];
    uint32_t nonce[3];

#ifdef PLANT_ENTROPY_UNSEEDED
    /* A2 near-miss: key from a FIXED compile-time constant (not a runtime source). The sequence is
     * then identical on every boot — a predictable source, caught by the cross-boot compare. */
    for (int i = 0; i < 8; i++) {
        key[i] = 0x01020304u + (uint32_t)i;
    }
    nonce[0] = 0xA5A5A5A5u; nonce[1] = 0x5A5A5A5Au; nonce[2] = 0xDEADBEEFu;
#else
    int have_rd = has_rdrand();
    for (int i = 0; i < 8; i++) {
        uint32_t r = 0;
        if (!have_rd || !rdrand32(&r)) {
            r = 0;
        }
        /* mix rdrand with the accumulated interrupt jitter and the tsc at seed time — so the key is
         * runtime-derived even when rdrand is absent (jitter alone still varies boot to boot). */
        key[i] = r ^ g_jit_a ^ (uint32_t)rdtsc();
        entropy_feed_jitter(key[i]);          /* stir the pool between words */
        key[i] ^= g_jit_b;
    }
    nonce[0] = g_jit_a ^ (uint32_t)rdtsc();
    nonce[1] = g_jit_b ^ (uint32_t)rdtsc();
    uint32_t r2 = 0;
    if (have_rd) { rdrand32(&r2); }
    nonce[2] = r2 ^ g_jit_a ^ g_jit_b;
#endif

    g_state[0] = 0x61707865u;  /* "expa" */
    g_state[1] = 0x3320646eu;  /* "nd 3" */
    g_state[2] = 0x79622d32u;  /* "2-by" */
    g_state[3] = 0x6b206574u;  /* "te k" */
    for (int i = 0; i < 8; i++) {
        g_state[4 + i] = key[i];
    }
    g_state[12] = 0;                          /* the block counter */
    g_state[13] = nonce[0];
    g_state[14] = nonce[1];
    g_state[15] = nonce[2];
    g_block_used = 64;                         /* force a fresh keystream block on the first draw */

    g_seed_nonzero = 0;
    for (int i = 0; i < 8; i++) {
        if (key[i] != 0) {
            g_seed_nonzero = 1;
        }
    }
}

int entropy_seed_nonzero(void) {
    return g_seed_nonzero;
}

void entropy_draw(uint8_t *out, uint32_t n) {
#ifdef PLANT_ENTROPY_CONSTANT
    /* A2 near-miss: a source that returns the SAME bytes every draw — two draws are equal, caught by
     * the self-check ("two draws differ"). */
    for (uint32_t i = 0; i < n; i++) {
        out[i] = 0x41;
    }
    return;
#else
    for (uint32_t i = 0; i < n; i++) {
        if (g_block_used >= 64) {
            chacha20_block(g_state, g_block);
            g_state[12]++;                     /* advance the counter: the next block differs */
            g_block_used = 0;
        }
        out[i] = g_block[g_block_used++];
    }
#endif
}
