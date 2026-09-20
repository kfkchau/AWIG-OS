/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — THE FORTY-NINE SERVED: the measured requests classified by purpose (C7 P3b-4b;
 * design/54 §5 L18, §7 P3b-4b; the P3b-4s FINDINGS the spec; precision (a)/(b) of board :4085).
 *
 * The enclosure (P3b-4a) proved the crossing MECHANISM with a handful of test codes. This slice makes
 * the body SERVE THE FORTY-NINE MEASURED REQUESTS in their measured x86_64 shapes — the twelve acts'
 * share performed by the act machinery; the hard floor (bring-up/loader/TLS, thread creation) realized
 * on the metal as the memory and concurrency acts' machinery; the designed refusal (module discovery on
 * a live filesystem) refused with the module bytes served from the sealed image, no filesystem walk; the
 * stubs degrading; entropy served AT BRING-UP; the network-socket share refused as the worker's native
 * failure until P3b-6 — and WITNESSES EVERY crossing as ONE UNSIGNED ROW of the body's own append-only
 * serve trail.
 *
 * THE PRECISION THAT BINDS THIS SLICE (precision (a) of :4085; the first freeze of this row was REFUSED
 * :4087 for checking a per-act SIGNED GATE ROW when no gate runs on the body). EVERY crossing — the acts'
 * share INCLUDED — is one UNSIGNED row of the body's OWN trail, served/refused/stubbed alike. The SIGNED
 * record row for an act is the GATE's, written ABOVE the seam by the Python gate BEFORE it asks the body;
 * NO GATE RUNS ON THE BODY HERE, so the per-act signed-gate-row check is DEFERRED BY NAME to P3b-4c/P3b-5.
 * The body holds NO key: every serve row carries sig==0 and chain==0, and the body NEVER appends a row
 * into the estate's signed chain. The trail's digest becomes one gate row as the worker's act-witness at
 * P3b-4c/P3b-5 — not here.
 *
 * Hand-written and read whole (design/47 §2 I3, §9): no opaque code in the signed base. OUR code, attested
 * BY NAME (serve.c + serve.h join the one attested list). The built worker IMAGE is never a member (§9
 * mechanism 3). NO new act (ACT_KINDS stays twelve — serving the measured requests realizes existing acts
 * + their floor); founds nothing (the pack is byte-unchanged). Every build and boot is the guest's nested
 * qemu (L11 / EP-00 rule 9). NO borrowed interpreter here (that is P3b-4c) — OUR test worker exercises the
 * forty-nine request by request.
 */
#ifndef SERVE_H
#define SERVE_H

#include <stdint.h>
#include <stddef.h>

/* ── The forty-nine measured requests: the real x86_64 syscall numbers (unistd_64) OUR test worker
 * issues in their measured shapes. Twelve acts' share by the acts; category A/B floor; category C the
 * designed refusal; category D the stubs; the network-socket share refused; category E EXCLUDED (named
 * for honesty, never issued/served). Cross-referenced to the P3b-4s FINDINGS Q-A/Q-B/Q-C/Q-D. ────────*/
#define SYS_read            0u
#define SYS_write           1u
#define SYS_writev         20u   /* ld.so/glibc write diagnostics to fd 2 via writev (C7 P3b-4d) */
#define SYS_close           3u
#define SYS_exit           60u   /* a thread's OWN end (C7 P3b-4f-ii — the fiftieth shape the census missed, Q15/:4134) */
#define SYS_fstat           5u
#define SYS_lseek           8u
#define SYS_mmap            9u
#define SYS_mprotect       10u
#define SYS_munmap         11u
#define SYS_brk            12u
#define SYS_rt_sigaction   13u
#define SYS_rt_sigprocmask 14u
#define SYS_ioctl          16u
#define SYS_pread64        17u
#define SYS_access         21u
#define SYS_madvise        28u
#define SYS_getpid         39u
#define SYS_socket         41u
#define SYS_connect        42u   /* C7 P3b-6c(iii): the socket-family shapes the socket-act relay routes  */
#define SYS_sendto         44u   /*   to the enclosed lwIP worker (send = sendto NULL addr)               */
#define SYS_recvfrom       45u   /*   (recv = recvfrom NULL addr)                                         */
#define SYS_getsockopt     55u   /*   getsockopt(SO_ERROR) — the non-blocking handshake                   */
#define SYS_poll            7u   /*   poll(POLLOUT/POLLIN) — the non-blocking handshake                   */
#define SYS_execve         59u
#define SYS_kill           62u
#define SYS_fcntl          72u
#define SYS_ftruncate      77u   /* the one-writer lock act's shape: ftruncate-to-0 on a *.lock (C7 P3b-5a-v) */
#define SYS_fsync          74u
#define SYS_fdatasync      75u
#define SYS_getcwd         79u
#define SYS_rename         82u
#define SYS_rmdir          84u    /* category E — EXCLUDED (harness teardown), never issued/served */
#define SYS_mkdir          83u
#define SYS_unlink         87u
#define SYS_readlink       89u
#define SYS_getuid        102u
#define SYS_getgid        104u
#define SYS_geteuid       107u
#define SYS_getegid       108u
#define SYS_gettid        186u
#define SYS_futex         202u
#define SYS_getdents64    217u
#define SYS_set_tid_address 218u
#define SYS_clock_gettime 228u
#define SYS_clock_nanosleep 230u
#define SYS_exit_group    231u
#define SYS_openat        257u
#define SYS_newfstatat    262u
#define SYS_unlinkat      263u    /* category E — EXCLUDED (harness teardown), never issued/served */
#define SYS_set_robust_list 273u
#define SYS_prlimit64     302u
#define SYS_getrandom     318u
#define SYS_epoll_create1 291u
#define SYS_rseq          334u
#define SYS_arch_prctl    158u
#define SYS_clone3        435u

/* ── The measured argument shapes that BITE (Q-D). Named so the body classifies by PURPOSE, not by the
 * syscall NAME (openat/read/write/mmap/futex carry both act and non-act work — a name is not a boundary).*/
#define GRND_NONBLOCK      0x0001u   /* getrandom: the startup hash-seed draw (AT BRING-UP)             */
#define MAP_SHARED         0x0001u   /* mmap: the MEMORY act asks MAP_SHARED (served anon-PRIVATE, Q11) */
#define MAP_PRIVATE        0x0002u
#define MAP_ANONYMOUS      0x0020u
#define MAP_STACK          0x20000u  /* thread stacks (category B floor)                                */
#define CLONE_VM           0x00000100u
#define CLONE_THREAD       0x00010000u
#define CLONE_SETTLS       0x00080000u
#define CLONE_CHILD_CLEARTID 0x00200000u
/* the four bits thread-create MUST reproduce or Python threads break (Q-D) */
#define CLONE_THREAD_SHAPE (CLONE_VM | CLONE_THREAD | CLONE_SETTLS | CLONE_CHILD_CLEARTID)
#define FUTEX_WAIT_BITSET   9u
#define FUTEX_PRIVATE_FLAG  128u
#define FUTEX_CLOCK_REALTIME 256u
/* the wait shape the lock primitive must support: PRIVATE bitset-wait with a realtime clock (Q-D) */
#define FUTEX_WAIT_SHAPE (FUTEX_WAIT_BITSET | FUTEX_PRIVATE_FLAG | FUTEX_CLOCK_REALTIME)
#define CLOCK_REALTIME     0u        /* the recording-clock read (a cost on a vDSO-less body, Q-D)     */
#define CLOCK_MONOTONIC    1u        /* the commit-window read/sleep                                   */
#define TIMER_ABSTIME      1u        /* clock_nanosleep: an ABSOLUTE monotonic deadline (Q-D)          */
#define O_APPEND           0x400u    /* openat: the record-pen append flag (load-bearing, Q-D)         */
#define O_TRUNC            0x200u    /* openat: the atomic-write-once flag (load-bearing, Q-D)         */
#define O_WRONLY           0x1u      /* openat: write-only (open("a")/open("w") set this, C7 P3b-5a-iv)*/
#define O_RDWR             0x2u      /* openat: read-write (open("a+"), C7 P3b-5a-iv)                  */
#define O_CREAT            0x40u     /* openat: create-on-absent (open("a")/open("w") set this, 5a-iv) */
/* ── C7 P3b-5a-v — the one-writer lock act's fcntl shape (host_seam.lock_write, measured on the guest:
 * fcntl(fd, F_SETLK, {l_type=F_WRLCK,...}) is the HELD exclusive claim; a second claimant is refused). The
 * body serves F_SETLK on a *.lock fd as its one-writer act (grant to one holder, refuse a second by name);
 * F_GETFD stays the io-layer stub. Named so the fcntl case classifies by PURPOSE, not by the syscall name.*/
#define F_GETFD            1u        /* fcntl: the CLOEXEC probe (io-layer stub → FD_CLOEXEC)             */
#define F_SETLK            6u        /* fcntl: the non-blocking record-lock claim (the one-writer act)     */
#define F_WRLCK            1u        /* the exclusive (write) lock type the claim takes                    */
#define AF_INET            2u
#define TCGETS             0x5401u   /* ioctl: the isatty probe (category D stub → ENOTTY)             */

/* A distinguished MODULE-SEARCH sentinel: an openat/getdents64 whose PATH argument is this marker is a
 * MODULE-DISCOVERY scan over a live filesystem — the DESIGNED REFUSAL (category C, same NAME as a file
 * act, different PURPOSE). The module bytes are served from the sealed image instead, no filesystem walk.*/
#define MODULE_SEARCH_SENTINEL 0x4D4F44554C450000ull   /* "MODULE\0\0" — a body-side purpose marker      */

/* ── The verdict + category of a served crossing (read back on serial) ───────────────────────────────*/
#define SV_SERVED   1u    /* the acts' share (performed by the act machinery); the floor (realized)      */
#define SV_REFUSED  0u    /* the network-socket share (native failure); the designed refusal            */
#define SV_STUBBED  2u    /* the io-layer/identity probes (degrade gracefully)                          */

#define CAT_A    1u   /* bring-up / loader / TLS — HARD FLOOR                                            */
#define CAT_B    2u   /* thread creation — HARD FLOOR                                                   */
#define CAT_ACT  3u   /* the twelve acts' share — performed by the act machinery, witnessed like the rest*/
#define CAT_C    4u   /* module discovery on a live filesystem — the DESIGNED REFUSAL                    */
#define CAT_D    5u   /* io-layer / environment probes — the STUBS                                      */
#define CAT_SOCK 6u   /* the network-socket act share — refused as native failure until P3b-6 (act #9)   */
#define CAT_FRAME 7u  /* C7 P3b-6b — a borrowed-TCP frame crossing (send/receive), a row like the rest    */

/* The native failure answer for a request the body does not serve — the SYSCALL's own -ENOSYS shape
 * (never a gov-os message). 38 == ENOSYS on x86_64 Linux; -38 as a u64 == 0xffffffffffffffda. Reused
 * from the enclosure (enclosure.h NATIVE_FAIL_ANS); redeclared here so serve.c stands on its own name. */
#define SERVE_ENOSYS ((uint64_t)(-38))       /* 0xffffffffffffffda — the socket refusal's native answer */
#define SERVE_ENOTTY ((uint64_t)(-25))       /* 0xffffffffffffffe7 — the isatty stub's native answer    */

/* ── One UNSIGNED row of the body's own append-only serve trail. The body holds NO key: sig and chain
 * are ALWAYS 0 (a plant that sets either reds its check). NEVER an unsigned row in the estate's signed
 * chain — that is the gate's, above the seam (precision a). ────────────────────────────────────────*/
#define SERVE_TRAIL_MAX 96u

struct serve_row {
    uint32_t seq;        /* 0-based append index (append-only, in order)                         */
    uint32_t num;        /* the measured syscall number                                          */
    uint32_t cat;        /* CAT_A | CAT_B | CAT_ACT | CAT_C | CAT_D | CAT_SOCK                    */
    uint32_t verdict;    /* SV_SERVED | SV_REFUSED | SV_STUBBED                                   */
    uint64_t arg;        /* the classifying argument (the shape that bites — flags/clockid/path)  */
    uint64_t ans;        /* the answer returned (a refused row carries the native failure)        */
    uint32_t sig;        /* ALWAYS 0 — the body holds no key, never signs a row (precision a)     */
    uint32_t chain;      /* ALWAYS 0 — never appended into the estate's signed chain (precision a)*/
};

/* ── The one dispatcher the crossing calls when the body is in the forty-nine serve phase ────────────
 * enclosure.c's body_request routes here when g_serve_phase is set. Classifies `num` by the argument
 * shape, routes to the act machinery / floor / refusal / stub, appends ONE unsigned serve row, returns
 * the answer in %rax. exit_group ends the run (unwinds via body_longjmp; never returns). */
uint64_t serve_request(uint64_t num, uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3, uint64_t a4);

/* ── C7 P3b-4f-i: the static single-thread floor's real machinery shares this router. The loader sets
 * the program's initial break (just above the loaded image) before the ring-3 run, so serve_brk grows a
 * REAL program break rather than returning a canned fixed address. ───────────────────────────────────*/
void serve_set_brk_base(uint64_t base);
#if defined(BRIDGE) || defined(SOCKET_ACT)
/* C7 P3b-6c (ii/iii): save/restore the brk state around a bridge relay (the two enclosures share serve.c's brk). */
void serve_brk_save(uint64_t *base, uint64_t *cur);
void serve_brk_load(uint64_t base, uint64_t cur);
#endif

/* ── C7 P3b-6b — THE BORROWED TCP ENCLOSURE (design/54 §5 L18; §7 P3b-6b). serve_request serves the
 * per-enclosure declared set: the interpreter's fifty and this worker's twenty are two lists (the
 * PERFORMERS are shared, the DECLARATION is per enclosure, :4302 b). serve_declared(enclosure, num) is
 * that gate as DATA — 1 iff `num` is declared for that enclosure, 0 iff refused BY NAME. The three frame
 * shapes (send/receive/wait) are declared ONLY to the lwIP enclosure; every syscall the worker's
 * whole-process measured set names is declared for it too; everything else is refused by name. ────────*/
int serve_declared(uint32_t enclosure, uint64_t num);   /* the per-enclosure gate, as data (:4302 b)     */

/* the lwIP worker's monotonic clock (sys_now) is rdtsc-based (IF-independent — the worker sits in ring-0
 * frame syscalls); floor_net_run calibrates cycles/ms against the PIT and hands them here before the run. */
void serve_net_clock_calibrate(uint64_t tsc_base, uint64_t tsc_per_ms);
#ifdef SOCKET_ACT
void serve_sa_trail_dump(uint32_t *out_sock_rows, uint32_t *out_frame_rows);  /* A3: the socket-act trail readback */
uint32_t serve_frame_low_water(void);  /* A4: the frame-pool low-water */
void serve_sa_trail_reset(void);  /* A3: reset the socket-act trail before the run */
#endif

/* the borrowed-TCP frame accounting (A4: every frame a row; the counts are the check that can fail).
 * g_frames_sent/recv are the frames that ACTUALLY crossed 6a's NIC (net.c); g_frame_rows is the rows the
 * body appended for them. A4 reds iff they diverge (PLANT_FRAME_TRAIL_SKIP skips one row). */
extern uint32_t g_frames_sent;         /* frames put on the wire for the lwIP worker (net_send_frame ok)  */
extern uint32_t g_frames_recv;         /* frames delivered from the wire to the lwIP worker (recv ok)     */
extern uint32_t g_frame_rows;          /* trail rows appended for frames (== sent+recv unless a skip)     */
extern uint32_t g_lwip_beyond_served;  /* a shape BEYOND the lwIP declared set was SERVED (MUST stay 0)   */
extern uint64_t g_lwip_mem_peak;       /* peak heap bytes the body granted the lwIP worker (A5 >= 17,048) */

/* ── The serve driver's finish: run the checks, print the serve trail + the SERVE CHECK lines + the
 * aggregate, and return 0 iff every check passes. `worker_ok` is true iff the worker's forty-nine run
 * ended by exit_group with no fault. Called by enclosure.c's enclosure_serve_run after the ring-3 run. */
int serve_finish(int worker_ok);

/* the serve run reached exit_group (the worker's forty-nine run ended cleanly) — read by the driver. */
extern volatile int g_serve_exited;
/* C7 P3b-5b-i: the exit_group STATUS the ring-3 program passed (0 green / 1 red for the ledger bootstrap),
 * carried to serial as the REAL exit status the host-side test reads back (design/54 §7 P3b-5b). */
extern volatile int g_serve_exit_status;

/* ── C7 P3b-4d — THE SEALED-IMAGE FILESYSTEM (design/54 §7 P3b-4d; B6; Q15/:4134). floor3 (enclosure.c)
 * digest-checks the sealed image, adopts it (serve_fs_set_image), loads ld.so from the PT_INTERP path
 * (serve_fs_find), and proves the FS is served by listing (serve_fs_listable_check) and the P3b-2 record
 * filesystem is mounted beside with distinct namespaces (serve_fs_beside_check). The sealed-FS ops
 * (openat/read/pread64/fstat/mmap-file-backed/getdents64/close) route here ONLY while g_dyn_fs_on; the
 * P3b-4a/4b/floor/floor2 paths are byte-identical with it clear. ────────────────────────────────────*/
extern int g_dyn_fs_on;                  /* 1 during the floor3 dynamic run (routes the sealed-FS ops)   */

int            serve_fs_set_image(const uint8_t *img, uint32_t len);   /* parse + adopt; entry count or -1 */
const uint8_t *serve_fs_find(const char *path, uint32_t *out_len, int *out_is_dir);  /* resolve -> bytes   */
int            serve_fs_listable_check(const char *dir, const char *name);   /* 1 iff getdents64 lists name */
int            serve_fs_beside_check(void);     /* 1 iff the record FS is reachable beside + namespaces distinct */
int            serve_fs_live_walk(void);        /* 1 iff any outside path was SERVED (a fabricated live walk)    */
uint32_t       serve_fs_outside_refusals(void); /* paths outside both sets refused ENOENT (positive control)     */

#endif /* SERVE_H */
