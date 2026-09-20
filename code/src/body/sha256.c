/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — SHA-256, freestanding, on the metal (C7 P3b-4a; design/54 §5 L18, §7 P3b-4a).
 *
 * The SealedArtifact.verify idiom carried down to the metal (archi :4085 (b)): the body's ELF64 loader
 * folds a sealed image's bytes to a digest and refuses a load whose bytes do not fold to the carried
 * value. The estate seals with SHA-256 (bridge/seal.py: hashlib.sha256), so the body folds with the same
 * function — a byte change in the sealed worker image is refused AT LOAD, exactly as an outer-seal
 * mismatch is refused above the seam.
 *
 * A textbook FIPS-180-4 SHA-256 over an in-memory buffer (the sealed image is already resident — no
 * streaming needed). Hand-written and read whole (I3): no opaque code in the signed base, no libc, no
 * libgcc (32-bit rotates/adds only). Byte-identical to Python's hashlib.sha256 — the body and the host
 * agree on the seal.
 */
#include "enclosure.h"

static inline uint32_t ror(uint32_t x, uint32_t n) { return (x >> n) | (x << (32u - n)); }

static const uint32_t K[64] = {
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
    0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u, 0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
    0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu, 0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
    0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u, 0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
    0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u, 0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
    0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u, 0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
    0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u, 0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u,
};

static void sha256_block(uint32_t h[8], const uint8_t *p) {
    uint32_t w[64];
    for (int i = 0; i < 16; i++) {
        w[i] = ((uint32_t)p[i * 4] << 24) | ((uint32_t)p[i * 4 + 1] << 16)
             | ((uint32_t)p[i * 4 + 2] << 8) | (uint32_t)p[i * 4 + 3];
    }
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ror(w[i - 15], 7) ^ ror(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = ror(w[i - 2], 17) ^ ror(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
    for (int i = 0; i < 64; i++) {
        uint32_t S1 = ror(e, 6) ^ ror(e, 11) ^ ror(e, 25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t t1 = hh + S1 + ch + K[i] + w[i];
        uint32_t S0 = ror(a, 2) ^ ror(a, 13) ^ ror(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t t2 = S0 + maj;
        hh = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
}

void sha256(const uint8_t *data, uint32_t len, uint8_t out[32]) {
    uint32_t h[8] = {0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
                     0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u};
    uint32_t full = len / 64u;
    for (uint32_t i = 0; i < full; i++) {
        sha256_block(h, data + i * 64u);
    }
    /* the tail: the remaining bytes, the 0x80 pad, zeros, and the 64-bit BIT length. At most two
     * final blocks (the length may not fit in the same block as the pad). */
    uint8_t tail[128];
    uint32_t rem = len - full * 64u;
    for (uint32_t i = 0; i < rem; i++) { tail[i] = data[full * 64u + i]; }
    tail[rem] = 0x80u;
    uint32_t total = (rem + 1u <= 56u) ? 64u : 128u;
    for (uint32_t i = rem + 1u; i < total - 8u; i++) { tail[i] = 0u; }
    uint64_t bits = (uint64_t)len * 8u;
    for (int i = 0; i < 8; i++) {
        tail[total - 1u - (uint32_t)i] = (uint8_t)(bits >> (i * 8));
    }
    sha256_block(h, tail);
    if (total == 128u) { sha256_block(h, tail + 64u); }
    for (int i = 0; i < 8; i++) {
        out[i * 4]     = (uint8_t)(h[i] >> 24);
        out[i * 4 + 1] = (uint8_t)(h[i] >> 16);
        out[i * 4 + 2] = (uint8_t)(h[i] >> 8);
        out[i * 4 + 3] = (uint8_t)(h[i]);
    }
}
