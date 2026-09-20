/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the C entry: bring up memory, self-check, announce the digest (C7 P3b-1).
 *
 * boot.S hands us (magic, multiboot-info). We bring up the three memory pieces in order —
 * physical frames (PMM), virtual memory (VMM/paging), the heap — then run a self-check that
 * proves each is FUNCTIONAL, not merely present: the PMM allocates and frees a frame; the VMM
 * maps a virtual page to a frame and proves the write reached that frame; the heap allocates,
 * writes a pattern, reads it back, frees, and hands out two non-overlapping blocks. Each PASS/FAIL
 * goes on the serial line. AFTER memory is up, the body prints the twelve rows' digest — the
 * boot -> memory -> serial path holds, with no Linux beneath. A planted fault (PLANT_VMM_WRONG /
 * PLANT_HEAP_OVERLAP) turns the matching check to FAIL: the self-check can fail (A2).
 */
#include "body.h"
#include "disk.h"
#include "clock.h"
#include "enclosure.h"

/* C7 P3b-4c — the ONE sealed image carried as the first multiboot module (0/0 when none attached). */
uint64_t g_sealed_module_phys;
uint64_t g_sealed_module_len;

/* C7 P5 — the CORE image (the body's own released image) carried as a SECOND multiboot module beside the
 * sealed interpreter (0/0 when none attached — every existing 0/1-module boot). The sealed-artifact emitter
 * hashes it on the metal and names it by hash in a record row (design/54 §3 B6). */
uint64_t g_core_module_phys;
uint64_t g_core_module_len;

/* C7 P3b-6a — OUR virtio-net NIC driver + the ring-0 wire self-check (src/body/net.c). Declared here
 * (kmain calls it beside the other ring-0 self-checks); net.c is a single new attested source file. */
extern int net_wire_selfcheck(void);

/* C7 P7b — the device-discovery emitter (src/body/diskcheck.c, beside check_record_pen). kmain gathers
 * the REAL probe results (block/network/clock) and hands them to the emitter, which records ONE
 * discovery row per device over the settled three-device list, each riding record-pen. Declared here
 * (edit-in-place, no disk.h touch — mirrors serve_ns_selfcheck's declaration in diskcheck.c). */
extern int disk_record_device_discovery(int block_present, int net_class,
                                        const uint8_t net_mac[6], int net_mac_valid,
                                        int clock_present, uint64_t clock_epoch);

/* C7 P5 — the sealed-artifact emitter (src/body/diskcheck.c, beside disk_record_device_discovery). kmain
 * hands it the CORE and INTERPRETER module ranges; at bring-up it names each by hash in a record-pen row,
 * and at every later boot re-hashes each and compares to its row (a tampered byte reds). Declared here
 * (edit-in-place, no disk.h touch — mirrors disk_record_device_discovery's declaration). */
extern int disk_record_sealed_artifacts(uint64_t core_phys, uint64_t core_len,
                                        uint64_t interp_phys, uint64_t interp_len);

/* Read a model-specific register (ring 0). Used to read EFER.LMA — a MACHINE fact that the
 * trampoline sets, so the body reports its mode from the machine, never from a compile-time fact
 * (sizeof(void*) is 8 the moment -m64 is passed, whether or not the trampoline ran — precision 1). */
static inline uint64_t rdmsr(uint32_t msr) {
    uint32_t lo, hi;
    __asm__ volatile("rdmsr" : "=a"(lo), "=d"(hi) : "c"(msr));
    return ((uint64_t)hi << 32) | lo;
}

static int check_pmm(void) {
    uint32_t f1 = pmm_alloc();
    if (f1 == 0) {
        return 0;
    }
    uint32_t before = pmm_free_count();
    pmm_free(f1);
    if (pmm_free_count() != before + 1) {
        return 0;
    }
    uint32_t f2 = pmm_alloc();   /* the freed frame is reclaimable */
    if (f2 == 0) {
        return 0;
    }
    pmm_free(f2);
    return 1;
}

static int check_vmm(void) {
    uint32_t frame = pmm_alloc();
    if (frame == 0) {
        return 0;
    }
    /* 1 GiB — an unmapped region OUTSIDE the body's identity map (which covers only the low 1 GiB),
     * so vmm_map genuinely walks and installs a PD+PT on the body's OWN four-level tables here — not
     * the trampoline scaffold's identity map (precision 2, archi :4082). */
    const uint64_t va = 0x40000000ull;
    if (vmm_map(va, frame) != 0) {
        pmm_free(frame);
        return 0;
    }

#ifdef PLANT_VMM_WRONG
    /* A2 near-miss: remap the same VA to a DIFFERENT frame (on the body's own tables), so the write
     * below does NOT reach `frame` — the physical read-back must then disagree and the check FAILs. */
    {
        uint32_t bad = pmm_alloc();
        if (bad) {
            vmm_map(va, bad);
        }
    }
#endif

    volatile uint32_t *vp = (volatile uint32_t *)va;
    *vp = 0xDEADBEEFu;
    volatile uint32_t *pp = (volatile uint32_t *)phys_to_virt(frame);   /* the frame, through the direct map */
    int ok = (*pp == 0xDEADBEEFu) && (*vp == 0xDEADBEEFu);

    vmm_unmap(va);
    pmm_free(frame);
    return ok;
}

/* C7 P3b-4m (L20) — the address space laid out for the program. Two facts, each a self-check that can
 * fail (the PLANT_IDENTITY_NOT_WITHDRAWN near-miss reds both):
 *   check_layout    — the body reaches a frame through its OWN higher-half direct map (the write lands
 *                     and the view is above DIRECT_MAP_BASE), AND the supervisor identity map is
 *                     WITHDRAWN from the program's range (no identity huge page over [0x400000, 1 GiB)).
 *   check_user_base — a USER page is mappable at the canonical base 0x400000 (vmm_map_user could not do
 *                     this while the low gigabyte was a supervisor huge page): the PTE is PRESENT + USER
 *                     at the expected frame, and the frame is reachable through the direct map. */
static int check_layout(void) {
    uint32_t frame = pmm_alloc();
    if (frame == 0) {
        return 0;
    }
    volatile uint32_t *dm = (volatile uint32_t *)phys_to_virt(frame);
    int higher_half = ((uint64_t)(uintptr_t)dm >= DIRECT_MAP_BASE);
    *dm = 0xD124EC70u;                       /* a sentinel written through the direct map */
    int reached = (*dm == 0xD124EC70u);
    pmm_free(frame);
    int withdrawn = vmm_program_range_identity_withdrawn();
    return higher_half && reached && withdrawn;
}

static int check_user_base(void) {
    uint32_t frame = pmm_alloc();
    if (frame == 0) {
        return 0;
    }
    /* the canonical base is user-mappable now (before the withdrawal it was a supervisor huge page). */
    if (vmm_map_user(CANONICAL_BASE, (uint64_t)frame) != 0) {
        pmm_free(frame);
        return 0;
    }
    uint64_t pte = vmm_query(CANONICAL_BASE);
    *(volatile uint32_t *)phys_to_virt(frame) = 0xCA5E6A5Eu;   /* the body reaches the frame up high */
    int present = (pte & 0x1ull) != 0;
    int user    = (pte & 0x4ull) != 0;
    int to_frame = ((pte & 0x000FFFFFFFFFF000ull) == ((uint64_t)frame & 0x000FFFFFFFFFF000ull));
    int reached  = (*(volatile uint32_t *)phys_to_virt(frame) == 0xCA5E6A5Eu);
    vmm_unmap(CANONICAL_BASE);
    pmm_free(frame);
    return present && user && to_frame && reached;
}

static int check_heap(void) {
    uint8_t *a = (uint8_t *)kmalloc(64);
    uint8_t *b = (uint8_t *)kmalloc(64);
    if (a == 0 || b == 0) {
        return 0;
    }
    for (int i = 0; i < 64; i++) {
        a[i] = 0xAB;
    }
    for (int i = 0; i < 64; i++) {
        if (a[i] != 0xAB) {
            return 0;
        }
    }
    uintptr_t ua = (uintptr_t)a;
    uintptr_t ub = (uintptr_t)b;
    int non_overlap = (ua + 64u <= ub) || (ub + 64u <= ua);
    kfree(a);
    kfree(b);
    return non_overlap;
}

void kmain(uint32_t magic, const struct mb_info *mbi) {
    serial_init();
    serial_puts("gov-os body: memory bring-up (nested guest, no Linux beneath)\n");
    serial_puts((magic == MULTIBOOT_BOOTLOADER_MAGIC) ? "MULTIBOOT: OK\n"
                                                      : "MULTIBOOT: FAIL (bad magic)\n");

    /* THE MODE, READ FROM THE MACHINE (precision 1, archi :4082): EFER.LMA (bit 10) is 1 iff long
     * mode is ACTIVE — a machine fact the trampoline set, not a compile-time constant. Reaching this
     * 64-bit code at all means the trampoline was taken; reading LMA confirms it from the CPU. The
     * PLANT_NO_LONGMODE build never reaches here — it announces "still 32-bit" from boot.S, so this
     * long-mode line is absent and the machine-read mode check reds (a check that can fail). */
    {
        uint64_t efer = rdmsr(0xC0000080u);
        unsigned lma = (unsigned)((efer >> 10) & 1u);
        if (lma) {
            serial_puts("LONGMODE: OK (EFER.LMA=1, ptr=0x");
            serial_puthex32((uint32_t)sizeof(void *));
            serial_puts(")\n");
        } else {
            serial_puts("LONGMODE: FAIL (EFER.LMA=0, still 32-bit)\n");
        }
    }

    pmm_init(mbi);
    serial_puts("PMM: init, free frames=0x");
    serial_puthex32(pmm_free_count());
    serial_puts("\n");

    vmm_init();
    serial_puts("VMM: paging enabled\n");

    /* C7 P3b-4c — capture the first multiboot module (the sealed image): the loader's descriptor array
     * and the module bytes are physical; read them through the direct map now that paging is up. */
    g_sealed_module_phys = 0;
    g_sealed_module_len  = 0;
    g_core_module_phys   = 0;
    g_core_module_len    = 0;
    if ((mbi->flags & MB_FLAG_MODS) && mbi->mods_count > 0) {
        const struct mb_mod *mods = (const struct mb_mod *)phys_to_virt(mbi->mods_addr);
        g_sealed_module_phys = mods[0].mod_start;
        g_sealed_module_len  = (uint64_t)mods[0].mod_end - (uint64_t)mods[0].mod_start;
        serial_puts("MODULE: count=0x");  serial_puthex32(mbi->mods_count);
        serial_puts(" phys=0x");          serial_puthex64(g_sealed_module_phys);
        serial_puts(" len=0x");           serial_puthex64(g_sealed_module_len); serial_puts("\n");
        /* C7 P5 — a SECOND module is the CORE image (the body's own released image); captured through the
         * direct map exactly as the sealed image is. Absent on every existing 0/1-module boot. */
        if (mbi->mods_count > 1) {
            g_core_module_phys = mods[1].mod_start;
            g_core_module_len  = (uint64_t)mods[1].mod_end - (uint64_t)mods[1].mod_start;
            serial_puts("CORE-MODULE: phys=0x"); serial_puthex64(g_core_module_phys);
            serial_puts(" len=0x");              serial_puthex64(g_core_module_len); serial_puts("\n");
        }
    }

    heap_init();
    serial_puts("HEAP: init\n");

    int p = check_pmm();
    int v = check_vmm();
    int h = check_heap();
    serial_puts(p ? "CHECK PMM: PASS\n"  : "CHECK PMM: FAIL\n");
    serial_puts(v ? "CHECK VMM: PASS\n"  : "CHECK VMM: FAIL\n");
    serial_puts(h ? "CHECK HEAP: PASS\n" : "CHECK HEAP: FAIL\n");
    serial_puts((p && v && h) ? "MEMORY: PASS\n" : "MEMORY: FAIL\n");

    /* ── The address space laid out for the program (C7 P3b-4m, L20) ──────────────────────────────
     * The body is a higher-half kernel now: it reaches physical memory through its own direct map above
     * the user range, the supervisor identity map is withdrawn from the program's range, and the
     * canonical base 0x400000 is user-mappable. First: the direct map covers all physical RAM the loader
     * reports — a guest with more RAM than DIRECT_MAP_MAX faults this check (precision 1, a check that can
     * fail; boot a bigger nested guest and DIRECTMAP reds). */
    {
        uint64_t rmax = pmm_reported_max();
        if (rmax <= DIRECT_MAP_MAX) {
            serial_puts("DIRECTMAP: COVERS (reported_max=0x"); serial_puthex64(rmax);
            serial_puts(" <= cap=0x"); serial_puthex64(DIRECT_MAP_MAX); serial_puts(")\n");
        } else {
            serial_puts("DIRECTMAP: FAIL (reported_max=0x"); serial_puthex64(rmax);
            serial_puts(" > cap=0x"); serial_puthex64(DIRECT_MAP_MAX);
            serial_puts(" — the direct map does not cover all physical RAM)\n");
        }
    }
    int lay = check_layout();
    int ub  = check_user_base();
    serial_puts(lay ? "CHECK LAYOUT: PASS\n"    : "CHECK LAYOUT: FAIL\n");
    serial_puts(ub  ? "CHECK USER-BASE: PASS\n" : "CHECK USER-BASE: FAIL\n");
    serial_puts((lay && ub) ? "LAYOUT: PASS\n" : "LAYOUT: FAIL\n");

    /* ── The disk slice (C7 P3b-2): a block device + the body's own filesystem, and the five
     * record acts performed on the body's OWN disk. If no disk is attached (P3b-1's memory boot
     * runs the same body with no -drive), say so and skip — the body still announces its digest.
     * A FRESH disk runs the five-act self-check; a disk that already carries a record (a reboot on
     * the same image) runs the persistence verification instead (durability across a reboot). */
    int disk_here = ata_present();     /* C7 P7b — captured once; the block device's discovered verdict */
    int disk_mounted = 0;              /* set iff BODYFS mounted (the discovery rows need the record) */
    if (!disk_here) {
        serial_puts("DISK: ABSENT (no block device; the record acts are skipped)\n");
    } else if (fs_mount() != 0) {
        serial_puts("DISK: FS-FAIL (no BODYFS on the block device)\n");
    } else {
        serial_puts("DISK: OK\n");
        disk_mounted = 1;
        struct bfs_entry *rec = fs_find("record");
        if (rec != 0 && rec->length == 0) {
            int acts = disk_selfcheck();
            serial_puts(acts ? "ACTS: PASS\n" : "ACTS: FAIL\n");
        } else {
            int persisted = disk_verify_persisted();
            serial_puts(persisted ? "ACTS: PERSISTED\n" : "ACTS: PERSIST-FAIL\n");
        }
    }

    /* ── The clock/interrupt/entropy slice (C7 P3b-3): interrupts, the two clock acts (a wall clock
     * and a monotonic window) and a seeded source of chance, performed on the metal. The self-check
     * shows a timer IRQ firing and being handled, the two clocks reading sanely, and the source of
     * chance producing unpredictable output — all with the nested qemu's gdb stub attached from the
     * first line, so a fault during bring-up is read from the debugger rather than hanging silently. */
    int clk = clock_selfcheck();
    serial_puts(clk ? "CLOCK-ACTS: PASS\n" : "CLOCK-ACTS: FAIL\n");

    /* ── The one connection on the metal (C7 P3b-6a): the body's OWN virtio-net driver drives the
     * network device as its transport and proves it ON THE WIRE — it transmits an address-resolution
     * request and receives the guest gateway's reply off the receive ring (a real round trip answered
     * by qemu's SLIRP gateway, never a loopback of our own bytes). It runs ONCE, prints its verdict, and
     * STOPS kicking; it adds NO served shape (serve.c untouched — the frame-crossing to a worker is 6b's).
     * When no virtio-net device is attached (every other P3b boot runs this same body with no NIC) it
     * prints NET: ABSENT and returns, so the standing body suite stays green. */
    int net = net_wire_selfcheck();
    serial_puts(net == 0 ? "NET-ACTS: PASS\n"
              : net == 2 ? "NET-ACTS: ABSENT (no virtio-net device attached)\n"
                         : "NET-ACTS: FAIL\n");

    /* ── The device-discovery rows (C7 P7b): AFTER the block / network / clock probes, the body records
     * ONE discovery row per device it performs over the settled three-device list, each an append riding
     * record-pen, its payload the identity the body EXPORTS at bring-up — the block verdict (disk_here),
     * the network self-check class (net) + the MAC net_nic_bringup exports, the clock's presence + epoch.
     * Only when a record disk is mounted (the rows land in the record). The device DRIVERS are untouched:
     * this reads their EXPORTED results (rtc_read / net_nic_bringup are the body's own exported performers,
     * idempotent — a later NIC consumer re-brings-up) and appends. Never the file-static PCI id (precision
     * archi :4605). The observe device window (src/observe) re-sources from these rows (B10). */
    if (disk_mounted) {
        struct wallclock dw;
        rtc_read(&dw);
        int clock_present = (dw.year >= 2020 && dw.year <= 2100 && dw.month >= 1 && dw.month <= 12
                             && dw.day >= 1 && dw.day <= 31 && dw.hour <= 23 && dw.minute <= 59
                             && dw.second <= 60);
        uint64_t clock_epoch = clock_epoch_seconds(&dw);
        uint8_t dmac[6];
        int net_mac_valid = (net_nic_bringup(dmac) == 0);   /* the MAC the body exports (net.c:239/290) */
        int dd = disk_record_device_discovery(disk_here, net, dmac, net_mac_valid,
                                              clock_present, clock_epoch);
        serial_puts(dd ? "DEVICE-DISCOVERY-ACTS: PASS\n" : "DEVICE-DISCOVERY-ACTS: FAIL\n");

        /* ── The sealed-artifact rows (C7 P5, design/54 §3 B6): when the body runs with BOTH sealed released
         * artifacts present (a core image module beside the sealed interpreter), it names each by hash in a
         * record-pen row at bring-up and re-hashes each against its row at every later boot — a planted byte
         * in EITHER reds the boot attestation. Gated on a CORE module being present, so every existing
         * 0/1-module boot is inert here (A5). The interpreter's existing LOAD-time seal check is unchanged. */
        if (g_core_module_phys != 0) {
            int sa = disk_record_sealed_artifacts(g_core_module_phys, g_core_module_len,
                                                  g_sealed_module_phys, g_sealed_module_len);
            serial_puts(sa ? "SEALED-ARTIFACT-ACTS: PASS\n" : "SEALED-ARTIFACT-ACTS: FAIL\n");
        }
    }

    /* ── The worker's enclosure (C7 P3b-4a): the body hosts OUR small test worker BENEATH THE SEAM at
     * user privilege, loaded by the body's OWN ELF64 loader from a SEALED (digest-checked) image; the
     * worker runs UNPRIVILEGED (ring 3) and its handful of requests cross by the machine's OWN call
     * crossing (SYSCALL/SYSRET), each recorded as a ROW of the body's own append-only crossing trail; an
     * out-of-set request is refused as the worker's OWN native failure (-ENOSYS) and recorded; a direct
     * reach at the body's memory is FAULTED by the hardware (enclosure is a hardware fact, L18). The body
     * still announces the twelve rows' digest below. */
    int enc = enclosure_run();
    serial_puts(enc == 0 ? "ENCLOSURE-ACTS: PASS\n" : "ENCLOSURE-ACTS: FAIL\n");

    /* ── The forty-nine served (C7 P3b-4b): after the enclosure MECHANISM is proven, the body SERVES the
     * measured requests in their measured x86_64 shapes — the twelve acts' share by the act machinery, the
     * hard floor realized on the metal, the designed refusal (module bytes from the sealed image, no
     * filesystem walk), the stubs degrading, entropy at bring-up, the network-socket share refused as the
     * native failure — each witnessed as one UNSIGNED row of the body's own serve trail (the body holds no
     * key; the signed act row is the gate's, ABOVE the seam, deferred to P3b-4c). Runs only when the
     * enclosure passed (a loaded worker to re-enter); the twelve rows' digest still follows. */
    if (enc == 0) {
        int serve = enclosure_serve_run();
        serial_puts(serve == 0 ? "SERVE-ACTS: PASS\n" : "SERVE-ACTS: FAIL\n");
    } else {
        serial_puts("SERVE-ACTS: SKIPPED (the enclosure did not pass — no loaded worker to re-enter)\n");
    }

    /* ── The static single-thread floor (C7 P3b-4f-i, L19): after the enclosure MECHANISM (P3b-4a) and the
     * forty-nine SERVED (P3b-4b) are proven with OUR worker, the body becomes a real home for an ORDINARY
     * gcc -static single-threaded glibc program — laying its initial stack + auxiliary vector, backing
     * mmap/munmap/mprotect/brk with a real address-space manager, installing the main-thread %fs base, and
     * enabling the machine's SSE state — and PROVES the floor by running the program to completion (it
     * reaches main, malloc/free and distinct maps work, the thread-local and SSE run, it reads its own
     * AT_RANDOM). Compiled in only when build.sh sealed a prover (PROVER_PRESENT); the worker-only builds
     * are byte-for-byte unchanged. The twelve rows' digest still follows. */
#ifdef PROVER_PRESENT
#ifdef SOCKET_ACT
    /* C7 P3b-6c slice (iii) — THE SOCKET ACT (design/54 §5 L18/L19/I3, §7 P3b-6c slice iii; countersign archi
     * :4561): the body boots the sealed interpreter (P3b-4c) AND the enclosed lwIP op-server worker RESIDENT
     * TOGETHER with 6a's live NIC; the interpreter drives a whole client connection, and the body relays the
     * socket-family shapes across the slice-(ii) bridge to the worker (a PERSISTENT coroutine), which opens
     * ONE guest-local connection over nested SLIRP. SOCKET_ACT implies INTERP_FLOOR + NET_WORKER; NO new act. */
    int floor = floor_socket_act_run();
    serial_puts(floor == 0 ? "SOCKET-ACT-ACTS: PASS\n" : "SOCKET-ACT-ACTS: FAIL\n");
#elif defined(BRIDGE)
    /* C7 P3b-6c slice (ii) — THE COMBINED BUILD + THE COROUTINE BRIDGE (design/54 §5 L18/L19, §7 P3b-6c slice
     * ii; countersign archi :4550): the body boots the sealed interpreter (P3b-4c) AND the enclosed lwIP
     * worker (P3b-6b) RESIDENT TOGETHER, each in its own slice-(i) map; a ring-0 coroutine bridge relays ONE
     * operation interpreter->worker->back across the map swap, the worker's answer its OWN execution
     * witnessed (L19). BRIDGE implies INTERP_FLOOR + NET_WORKER; it runs INSTEAD of either single floor. NO
     * new act (ACT_KINDS stays twelve). The twelve rows' digest still follows. */
    int floor = floor_bridge_run();
    serial_puts(floor == 0 ? "BRIDGE-ACTS: PASS\n" : "BRIDGE-ACTS: FAIL\n");
#elif defined(INTERP_FLOOR)
    /* C7 P3b-4c — THE INTERPRETER RUNS ON THE BODY (design/54 §5 L19, §7 P3b-4c): the body's own dynamic
     * loader loads the REAL unmodified /usr/bin/python3.12 from the ONE sealed image (the interpreter + its
     * C library + the loader-visible pieces + its standard library as real files, served by path AND by
     * listing, digest-checked before load) through the real linker (P3b-4d) on the real floor (P3b-4f);
     * the interpreter runs UNPRIVILEGED and UNMODIFIED as an ENCLOSED WORKER and IS THE PROVER — print(2+2)
     * and a thread run for real. A plant makes the REAL interpreter fail, never a flag. */
    int floor = floor3_interp_run();
    serial_puts(floor == 0 ? "FLOOR3C-ACTS: PASS\n" : "FLOOR3C-ACTS: FAIL\n");
#elif defined(DYNAMIC_FLOOR)
    /* C7 P3b-4d — THE DYNAMIC LOADER + THE SEALED IMAGE: the sealed image as a read-only filesystem of
     * ld.so + libc (digest-checked, served by path+offset+listing), the program's PT_INTERP honoured and
     * the handover to the linker, the P3b-2 record FS mounted beside — proven by an ordinary gcc -pthread
     * -no-pie dynamically-linked glibc program whose start-up goes through the real linker (L19). Built on
     * the concurrency floor (real threads), not re-running it. */
    int floor = floor3_run();
    serial_puts(floor == 0 ? "FLOOR3-ACTS: PASS\n" : "FLOOR3-ACTS: FAIL\n");
#elif defined(CONCURRENCY_FLOOR)
    /* C7 P3b-4f-ii — THE CONCURRENCY FLOOR: real threads (clone3), a preemptive scheduler on the P3b-3
     * timer, a real futex wait queue, a thread's own end (SYS_exit) — proven by an ordinary gcc -static
     * -pthread glibc program (L19). The static single-thread floor (4f-i) is built on, not re-run. */
    int floor = floor2_run();
    serial_puts(floor == 0 ? "FLOOR2-ACTS: PASS\n" : "FLOOR2-ACTS: FAIL\n");
#elif defined(NET_WORKER)
    /* C7 P3b-6b — THE BORROWED TCP ENCLOSED: a SECOND enclosed worker — lwIP 2.2.0, the static NO_SYS build
     * from the guest archive's SOURCE, UNMODIFIED — whose OWN per-enclosure served set is its whole-process
     * measured set (declared as data, never the eight); the stack's OWN lwiperf client opens ONE guest-local
     * connection OUTBOUND through 6a's NIC over nested SLIRP and completes a real exchange; every frame a
     * row (L18/L5/L19/I3). No new act (ACT_KINDS stays twelve). */
    int floor = floor_net_run();
    serial_puts(floor == 0 ? "NET-WORKER-ACTS: PASS\n" : "NET-WORKER-ACTS: FAIL\n");
#else
    int floor = floor_run();
    serial_puts(floor == 0 ? "FLOOR-ACTS: PASS\n" : "FLOOR-ACTS: FAIL\n");
#endif
#endif

#ifdef MAPS_PROVER
    /* C7 P3b-6c (i) — PER-ENCLOSURE ADDRESS MAPS: two enclosed programs made RESIDENT AT ONCE, each in its
     * OWN page-table hierarchy that SHARES the kernel half (the low identity + the higher-half direct map,
     * L20) and has a PRIVATE user half — so two enclosures at base 0x400000 coexist with no aliasing; the
     * map is swapped at the coroutine hand-off, and a ring-3 fault under a worker's own map is recovered PER
     * MAP (L18). The maps prover is a tests/ fixture (ATTESTED stays 88); no new act (ACT_KINDS stays
     * twelve); founds nothing. Runs after the enclosure mechanism (P3b-4a) is proven. */
    int mfloor = floor_maps_run();
    serial_puts(mfloor == 0 ? "MAPS-ACTS: PASS\n" : "MAPS-ACTS: FAIL\n");
#endif

    /* AFTER memory is up: the twelve rows' digest, tying the body to its definition. */
    serial_puts("ROWS-DIGEST: ");
    serial_puts(ROWS_DIGEST);
    serial_puts("\n");
    serial_puts("ROWS-COUNT: ");
    serial_puthex32(ROWS_ACT_COUNT);
    serial_puts("\n");

    serial_puts("BODY-HALT\n");
    for (;;) {
        __asm__ volatile("hlt");
    }
}
