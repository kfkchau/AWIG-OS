# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (a freestanding kernel body's memory act corrected so a program's PROT_NONE reservation of
# address space consumes no physical frame, and the protection act that makes a reserved range accessible is
# the commitment point where frames are allocated). NON-GOAL: no offensive capability — it corrects one
# over-eager allocation so RESERVATION is distinguished from COMMITMENT (the real kernel shape), proven by
# running OUR OWN heavy test modules and OUR OWN real-libc prover on OUR OWN kernel body inside a nested
# guest; it stands nothing as production, binds no key, touches no host kernel (every boot the guest's nested
# qemu). Validate by building/reading, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-5B acceptance — RESERVATION IS NOT COMMITMENT (planning/exec/C7-MAINT-5B-THREAD-STACK-MEMORY.md;
archi countersign board :4499; the three-acceptance-module expansion board :4510).

Currently (pre-fix body): serve_mmap (src/body/serve.c) never RECEIVES the syscall's protection argument and
backs+zero-fills every page of every map eagerly; SYS_mprotect is a blanket no-op. So a program's PROT_NONE
reservation of address space it may never touch (glibc's uncapped per-thread malloc arenas) is backed as if
committed and exhausts the 256 MiB pool — the wall behind the heavy concurrency modules (test_ep28c_w1,
test_ep28g_w2, test_ep28c_w4e_c) at the existing 8 MiB thread stacks.

After this plan: serve_mmap receives prot; an anonymous PROT_NONE map RESERVES the range (consumed, NO frame,
NOTHING mapped); the protection act that makes a sub-range ACCESSIBLE is the COMMIT point (the same eager
alloc+map+zero, honest ENOMEM when short); the FIXED-overlay / direct-R-W / file-backed paths are unchanged;
accessible-implies-backed stays universal so a ring-3 touch of a reservation still faults (L18 untouched); no
demand paging.

  A1  the three heavy modules run GREEN on the body at the EXISTING 8 MiB stacks in 256 MiB with the glibc
      arenas UNCAPPED (no MALLOC_ARENA_MAX). PLANT (back-at-reserve): ep28c_w1 reds by honest ENOMEM.
  A2  a real-libc prover mmaps an anonymous PROT_NONE range and TOUCHES it without committing -> a ring-3
      worker fault (FLOOR3-FAULT) at the reservation (L18). PLANT (back-at-reserve): the reservation is
      backed, so the touch does NOT fault (the run produces no reservation-touch fault).
  A3  the same prover makes a sub-range accessible (protection act -> R/W) and writes it -> the write lands
      on freshly committed frames; a commit beyond the pool returns honest ENOMEM. PLANT (mprotect-noop):
      the protection act commits nothing, so the write faults.
  A4  unmap over a partially-committed reservation reclaims EXACTLY the committed frames (reservation pages
      skipped), the address space is reusable, and no live/reservation frame is over-freed. PLANTs:
      frame-leak (committed frames not returned -> the reclaim loop OOMs); free-unguarded (the alias sentinel
      corrupts). And NOTHING ELSE MOVES: serve.c edit-in-place, ATTESTED 88, ACT_KINDS 12, no founding, no
      bodyfs.c/disk.h change.

A1/A2/A3/A4-on-body build+boot in the NESTED guest and skip when the pinned guest is not reachable over SSH
or (A2/A3/A4) when the dynamic prover floor does not reach FLOOR3 in the guest (a pre-existing environmental
blocker recorded at C7 P3b-5a-vii; the reservation fix runs only post-FLOOR3, so the env stop is not this
unit's). The off-body A4 classes (serve.c invariants, ATTESTED/ACT_KINDS/founding) run everywhere.

Register: OS memory reservation/commitment on a disposable nested guest, described by function; validated by
building/reading, never by attack (governance-work-method). Every kernel touch is the guest's nested qemu;
the host kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
"""

import os
import re
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
SERVE_C = os.path.join(BODY, "serve.c")
sys.path.insert(0, SRC)

# the real-libc reservation prover fixture (an ordinary gcc -O2 -pthread -no-pie glibc program, the P3b-4d
# DYNAMIC build path). Its source lives under tests/ — never a signed member; only the built binary is staged.
PROVER_FIXTURE = os.path.join(HERE, "c7_maint_5b_reservation_prover.c")

# the three heavy concurrency modules ruled the acceptance of this unit (board :4510).
A1_MODULES = ("test_ep28c_w1", "test_ep28g_w2", "test_ep28c_w4e_c")


# ── off-body A4 (runs everywhere) — the fence stayed edit-in-place; the invariants stand ───────────────
def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    import os as _os, subprocess as _sp
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    try:
        return _sp.run(["git", "-C", _root, "rev-parse", "--verify", "HEAD"],
                       capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


class TestA4FenceAndInvariants(unittest.TestCase):
    def test_serve_mmap_receives_prot_and_reserves_a_prot_none_anonymous_map(self):
        src = open(SERVE_C).read()
        self.assertIn(
            "static uint64_t serve_mmap(uint64_t addr, uint64_t len, uint64_t prot, uint64_t flags, "
            "uint64_t fd, uint64_t offset) {", src,
            "serve_mmap now RECEIVES the protection argument")
        self.assertIn("int accessible = (prot & (SI_PROT_READ | SI_PROT_WRITE)) != 0;", src,
                      "accessible == the protection gains READ or WRITE")
        self.assertIn("if (anon && !fixed && !accessible) {", src,
                      "an anonymous PROT_NONE map (not a FIXED overlay) reserves")
        # the RESERVE branch allocates NO frame and maps NOTHING — it only advances g_mmap_next + a guard.
        m = re.search(r"if \(anon && !fixed && !accessible\) \{(.*?)\n    \}", src, re.S)
        self.assertIsNotNone(m, "the reservation branch is present")
        reserve = m.group(1)
        self.assertIn("g_mmap_next = rbase + pages * 0x1000ull + 0x1000ull;", reserve,
                      "the reservation consumes the range + a guard page")
        self.assertNotIn("pmm_alloc()", reserve, "the reservation allocates NO frame (no pmm_alloc call)")
        self.assertNotIn("vmm_map_user(", reserve, "the reservation maps NOTHING (no vmm_map_user call)")

    def test_serve_mprotect_is_the_commit_point_with_honest_enomem(self):
        src = open(SERVE_C).read()
        self.assertIn("static uint64_t serve_mprotect(uint64_t addr, uint64_t len, uint64_t prot) {", src,
                      "a real serve_mprotect replaces the SYS_mprotect no-op")
        mp = src[src.index("static uint64_t serve_mprotect("):]
        mp = mp[:mp.index("\nstatic ", 1)]
        self.assertIn("if (!accessible) { return 0; }", mp, "not made accessible -> a no-op success")
        self.assertIn("if (pte & 0x1ull) { continue; }", mp, "an already-present page is left as it is")
        self.assertIn("uint32_t f = pmm_alloc();", mp, "the commit allocates a frame")
        self.assertIn("if (f == 0) { return (uint64_t)(-12); }", mp, "honest ENOMEM when the pool is short")
        self.assertIn("vmm_map_user(page, (uint64_t)f)", mp, "the committed frame is mapped USER")
        self.assertIn("z[k] = 0;", mp, "committed memory is zero-filled")

    def test_the_dispatch_passes_prot_and_calls_serve_mprotect(self):
        src = open(SERVE_C).read()
        self.assertIn("ans = serve_mmap(a0, a1, a2, a3, a4, g_syscall_a5);", src,
                      "the SYS_mmap dispatch passes prot (a2) — it was dropped before")
        self.assertIn("case SYS_mprotect:    cat = CAT_A; ans = serve_mprotect(a0, a1, a2); break;", src,
                      "the SYS_mprotect dispatch calls the real serve_mprotect")

    def test_both_reservation_plants_are_present_and_the_reclaim_plants_are_kept(self):
        src = open(SERVE_C).read()
        # this unit's two real-mechanism plants
        self.assertIn("PLANT_BACK_AT_RESERVE", src, "A1/A2 plant: a reservation backed eagerly (the pre-fix act)")
        self.assertIn("PLANT_MPROTECT_NOOP", src, "A3 plant: the protection act commits nothing")
        # the reservation branch is gated OUT under the back-at-reserve plant (falls through to the eager loop)
        self.assertIn("#if !defined(PLANT_BACK_AT_RESERVE)", src)
        # the 5a-vii reclaim plants A4 re-uses are still there (serve_munmap untouched — must-not-touch)
        self.assertIn("PLANT_FRAME_LEAK", src, "A4 re-uses the existing frame-leak plant")
        self.assertIn("PLANT_FRAME_FREE_UNGUARDED", src, "A4 re-uses the existing unguarded-free plant")

    def test_serve_munmap_untouched_partial_commit_reclaim_stands(self):
        # serve_munmap is MUST-NOT-TOUCH (5a-vii); its PTE-guard already handles a range that MIXES absent
        # reservation pages and present committed pages — a committed page (present+user) is freed, an absent
        # reservation page owns no frame and is skipped. This is what makes A4's exact accounting hold.
        src = open(SERVE_C).read()
        mu = src[src.index("static uint64_t serve_munmap("):]
        mu = mu[:mu.index("\nstatic ", 1)]
        self.assertIn("int owned = (pte & 0x1ull) && (pte & 0x4ull);", mu,
                      "a frame is freed only when its page read PRESENT+USER (a committed page)")
        self.assertIn("if (owned) { pmm_free(f); }", mu, "an absent reservation page is skipped (owns no frame)")

    def test_attested_unchanged_88_serve_c_edit_in_place_no_new_member(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "ATTESTED stays 88 — serve.c edit-in-place, no new member")
        self.assertIn("body/serve.c", ATTESTED_MEMBERS, "serve.c is the attested member edited in place")
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "the built prover image is NEVER a signed member")

    def test_act_kinds_twelve_and_no_founding_change(self):
        import json
        from kernel.boot import ACT_KIND_RECORD_KIND
        pack = json.load(open(os.path.join(SRC, "founding", "founding-pack.json")))
        self.assertEqual(pack["founding_version"], "1.55.0", "no founding — the version is unchanged")
        rows = []

        def scan(node):
            if isinstance(node, dict):
                if node.get("kind") == ACT_KIND_RECORD_KIND:
                    rows.append(node)
                for v in node.values():
                    scan(v)
            elif isinstance(node, list):
                for v in node:
                    scan(v)

        scan(pack)
        self.assertEqual(len({r["seam_kind"] for r in rows}), 12, "ACT_KINDS stays twelve")

    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs a git repository (git history is unavailable in the render)")
    def test_the_fence_held_only_serve_c_changed_no_bodyfs_disk_founding(self):
        # the diff of THIS unit against its base touches only serve.c (+ new tests/ files). bodyfs.c, disk.h
        # and the founding pack are MUST-NOT-TOUCH. Read the tracked diff, never a status field.
        diff = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", "HEAD", "--", "src/"],
                              capture_output=True, text=True).stdout.split()
        for p in diff:
            self.assertEqual(p, "src/body/serve.c",
                             "only src/body/serve.c is edited under src/ (bodyfs.c/disk.h/founding untouched)")


# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu, serialized) ──
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "<GUEST>"]
_WD = "/tmp/c7maint5b-accept"   # ISOLATED per-unit scratch (host-side path on the guest), nothing collides
_QEMU_LEDGER = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc"
_QEMU_DYN = "qemu-system-x86_64 -cpu max -display none -no-reboot -m 256 -rtc base=utc"


def _guest_reachable():
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU"],
                           capture_output=True, timeout=25)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return r.returncode == 0 and "6.8.0-134-generic" in out and "QEMU" in out


GUEST = _guest_reachable()
_SEEDED = {"done": False}
_CACHE = {}


def _seed():
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", ROOT, "src", "tests"], capture_output=True, timeout=180)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s" % (_WD, _WD)], capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True, timeout=180, check=True)
    with open(PROVER_FIXTURE, "rb") as f:
        subprocess.run(_SSH + ["cat > %s/prover.c" % _WD], input=f.read(), capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _kill_boots():
    subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"], capture_output=True, timeout=25)


def tearDownModule():
    if GUEST:
        _kill_boots()


# ── the LEDGER build+boot (A1 — a heavy module on the body) ─────────────────────────────────────────────
def _build_ledger(tag, fault=""):
    _seed()
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(_SSH + ["cd %s/src && LEDGER=1 bash body/build.sh body %s %s" % (_WD, out, fault)],
                       capture_output=True, timeout=420)
    if b.returncode != 0:
        raise AssertionError("guest LEDGER build failed: " + b.stderr.decode(errors="replace"))
    txt = b.stdout.decode(errors="replace") + "\n" + b.stderr.decode(errors="replace")
    assert "sealed image seal sha256" in txt, "the sealed image was not staged: " + txt
    return out


def _mkdisk_tree(tag, module):
    img = "%s/disk-%s.img" % (_WD, tag)
    m = subprocess.run(
        _SSH + ["cd %s && GOVOS_TREE=1 GOVOS_RUNMOD=%s PYTHONPATH=%s/src python3 src/body/mkdisk.py %s"
                % (_WD, module, _WD, img)],
        capture_output=True, timeout=240)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _boot(out, img, tag, qemu, wait_s):
    ser = "%s/serial-%s.txt" % (_WD, tag)
    run = "%s/run-%s.sh" % (_WD, tag)
    body = ("#!/bin/bash\npkill -9 -f 'qemu-system.*body.img' 2>/dev/null\nrm -f %s\n"
            "%s -serial file:%s -kernel %s/body.img -initrd %s/sealed.img "
            "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
            % (ser, qemu, ser, out, out, img))
    launch = ("cat > %s <<'EOS'\n%sEOS\nchmod +x %s; "
              "setsid timeout --signal=TERM %d %s >/dev/null 2>&1 & sleep 1; echo launched"
              % (run, body, run, wait_s + 60, run))
    subprocess.run(_SSH + [launch], capture_output=True, timeout=30)
    deadline = time.time() + wait_s
    while time.time() < deadline:
        r = subprocess.run(_SSH + ["grep -q BODY-HALT %s 2>/dev/null && echo HALTED || true" % ser],
                           capture_output=True, timeout=20)
        if b"HALTED" in r.stdout:
            break
        time.sleep(3)
    r = subprocess.run(_SSH + ["cat %s 2>/dev/null; pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true" % ser],
                       capture_output=True, timeout=40)
    return r.stdout.decode(errors="replace").replace("\r", "")


def _ledger_serial(tag, module, fault=""):
    key = ("ledger", tag)
    if key not in _CACHE:
        out = _build_ledger(tag, fault)
        img = _mkdisk_tree(tag, module)
        _CACHE[key] = _boot(out, img, tag, _QEMU_LEDGER, wait_s=1500)
    return _CACHE[key]


# ── the DYNAMIC prover build+boot (A2/A3/A4) ────────────────────────────────────────────────────────────
def _build_dyn(tag, fault=""):
    _seed()
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(_SSH + ["cd %s && DYN_PROVER_SRC=%s/prover.c bash src/body/build.sh src/body %s %s"
                               % (_WD, _WD, out, fault)],
                       capture_output=True, timeout=360)
    if b.returncode != 0:
        raise AssertionError("guest DYNAMIC build failed: " + b.stderr.decode(errors="replace"))
    txt = b.stdout.decode(errors="replace")
    assert "sealed image seal sha256" in txt, "the sealed ld.so+libc image was not staged: " + txt
    return out


def _mkdisk_plain(tag):
    img = "%s/disk-%s.img" % (_WD, tag)
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s/src python3 src/body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=120)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _dyn_serial(tag, fault=""):
    key = ("dyn", tag)
    if key not in _CACHE:
        out = _build_dyn(tag, fault)
        img = _mkdisk_plain(tag)
        _CACHE[key] = _boot(out, img, tag, _QEMU_DYN, wait_s=1500)
    return _CACHE[key]


def _ledger_result(serial):
    return re.search(r"LEDGER-RESULT (OK|FAILED) ran=(\d+) failures=(\d+) errors=(\d+) skipped=(\d+)", serial)


# ── A1 — the three heavy modules green on the body, arenas UNCAPPED ─────────────────────────────────────
@unittest.skipUnless(GUEST, "A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1HeavyModulesGreenOnBodyUncapped(unittest.TestCase):
    def _assert_module_green(self, tag, module):
        serial = _ledger_serial(tag, module)
        self.assertIn("BODY-HALT", serial, "%s: the body must reach BODY-HALT:\n%s" % (module, serial[-2500:]))
        m = _ledger_result(serial)
        self.assertIsNotNone(m, "%s: a LEDGER-RESULT line is on serial:\n%s" % (module, serial[-2500:]))
        self.assertEqual(m.group(1), "OK",
                         "%s runs GREEN on the body at 8 MiB stacks, arenas uncapped (ran=%s):\n%s"
                         % (module, m.group(2), serial[-2500:]))
        self.assertEqual(m.group(3), "0", "%s: no failures" % module)
        self.assertEqual(m.group(4), "0", "%s: no errors" % module)
        self.assertGreater(int(m.group(2)), 0, "%s: at least one test ran" % module)
        self.assertNotIn("MemoryError", serial, "%s: the pool sustained the run — no exhaustion" % module)
        self.assertIn("LEDGER-EXIT-STATUS: 0x00000000", serial, "%s: the REAL exit status is 0 (green)" % module)

    def test_ep28c_w1_green_uncapped(self):
        self._assert_module_green("w1", "test_ep28c_w1")

    def test_ep28g_w2_green_uncapped(self):
        self._assert_module_green("w2", "test_ep28g_w2")

    def test_ep28c_w4e_c_green_uncapped(self):
        self._assert_module_green("w4ec", "test_ep28c_w4e_c")

    def test_the_back_at_reserve_plant_reds_ep28c_w1_by_honest_pool_exhaustion(self):
        # PLANT (the old behaviour, one that CAN fail): a PROT_NONE reservation is backed eagerly, so the
        # 768 MiB of uncapped arenas exceed the 256 MiB pool. The RED is honest resource exhaustion — the
        # pool drains to ZERO, so a new thread's now-backed arena reservation cannot be allocated (a REAL
        # RuntimeError: can't start new thread / MemoryError), never a flag. The clean run's low-water was
        # > 0 (the pool never exhausted); this run's low-water is 0.
        serial = _ledger_serial("w1-backatreserve", "test_ep28c_w1", fault="PLANT_BACK_AT_RESERVE")
        self.assertIn("BODY-HALT", serial, "even a red run reaches BODY-HALT (a completed run)")
        m = _ledger_result(serial)
        self.assertIsNotNone(m, "a LEDGER-RESULT line is on serial:\n" + serial[-2500:])
        self.assertNotEqual(m.group(1), "OK", "the reservation fix is load-bearing — back-at-reserve reds it")
        low = re.search(r"FRAME-POOL-FREE-LOWWATER: 0x0*([0-9a-fA-F]+)", serial)
        self.assertIsNotNone(low, "the frame-pool low-water is on serial")
        self.assertEqual(int(low.group(1), 16), 0,
                         "the pool was EXHAUSTED (low-water 0) — honest resource exhaustion, not a flag")
        self.assertRegex(serial, r"MemoryError|RuntimeError: can't start new thread|Cannot allocate",
                         "the red is a real allocation failure at the drained pool:\n" + serial[-2500:])


# ── A2/A3/A4 — the real-libc prover on the dynamic floor ────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "A2/A3/A4 need the pinned guest + nested qemu over SSH -p 2222")
class TestReservationCommitmentProver(unittest.TestCase):
    def _skip_if_dynamic_floor_env_blocked(self, serial):
        """The P3b-4d DYNAMIC prover floor is a pre-existing environmental blocker in this guest — it stops
        at 'VMM: paging enabled' before FLOOR3, for BOTH this unit's serve.c AND the original serve.c (proven
        at C7 P3b-5a-vii, MANIFEST.txt: identical baseline stop). The reservation/commit code runs only
        post-FLOOR3, so the env stop is not this unit's; skip rather than misattribute it. A2/A3/A4 are then
        UNVERIFIABLE-BY-BOOT in this guest and are handed up as such (the fix is proven by A1 + reading)."""
        if "FLOOR3-SEAL" not in serial and "PROVER-START" not in serial:
            self.skipTest("dynamic prover floor does not reach FLOOR3 in this guest (pre-existing env blocker; "
                          "the reservation code runs post-FLOOR3, exonerated by the identical original stop)")

    def test_a3_commit_and_a4_reclaim_and_a2_touch_fault_clean(self):
        serial = _dyn_serial("clean")
        self._skip_if_dynamic_floor_env_blocked(serial)
        self.assertIn("PROVER-START", serial, "the prover reached main through the real linker")
        self.assertIn("PROVER-THREADS-OK", serial, "two real threads ran (the dynamic floor's conditions)")
        # A3 — the commit at the protection act works
        self.assertIn("A3-COMMIT-OK", serial,
                      "reserve PROT_NONE + mprotect a sub-range accessible + write -> commit works:\n"
                      + serial[-2500:])
        # A4 — the reclaim loop, remap-reuse, and the alias sentinel all held
        self.assertIn("A4-RECLAIM-LOOP-OK", serial, "committed frames return over churn exceeding the pool")
        self.assertIn("A4-REMAP-OK", serial, "the freed address space is reusable")
        self.assertIn("A4-ALIAS-OK", serial, "no live/reservation frame is over-freed")
        self.assertIn("A4-DONE", serial, "the whole A4 case completed")
        # A3-ENOMEM — a commit beyond the pool returns honest ENOMEM
        self.assertIn("A3-ENOMEM-OK", serial, "a commit that exceeds the pool returns honest ENOMEM")
        self.assertNotIn("A3-ENOMEM-MISSING", serial, "a huge commit is never a silent success")
        # A2 — the reservation touch FAULTS as a ring-3 enclosure violation, cr2 in the reservation
        base = re.search(r"A2-TOUCH base=0x([0-9a-f]+) at=0x([0-9a-f]+)", serial)
        self.assertIsNotNone(base, "the prover printed the A2 reservation base + touched address")
        fault = re.search(r"FLOOR3-FAULT: vec=0x([0-9a-f]+) cr2=0x([0-9a-f]+)", serial)
        self.assertIsNotNone(fault, "the body recorded a worker fault for the reservation touch:\n"
                             + serial[-2500:])
        self.assertEqual(int(fault.group(1), 16), 14, "a #PF (vector 14) — the reservation is not backed (L18)")
        self.assertEqual(int(fault.group(2), 16), int(base.group(2), 16),
                         "cr2 == the touched reservation address (accessible-implies-backed, L18)")
        self.assertNotIn("A2-NO-FAULT", serial, "the reservation touch did not silently succeed")

    def test_the_mprotect_noop_plant_reds_the_commit_a_touch_faults(self):
        # PLANT (A3, one that CAN fail): the protection act commits nothing. glibc reserves a thread stack
        # PROT_NONE and mprotects it to commit — with mprotect a no-op the stack is never backed, so the very
        # first commit-dependent touch (a thread stack, before the A3 phase even prints) faults. A3-COMMIT-OK
        # is never reached and a FLOOR3-FAULT is recorded. This is the protection-act-IS-the-commit-point,
        # shown on the thread-stack path itself.
        serial = _dyn_serial("mprotect-noop", fault="PLANT_MPROTECT_NOOP")
        self._skip_if_dynamic_floor_env_blocked(serial)
        self.assertIn("PROVER-START", serial, "the prover reached main through the real linker")
        self.assertNotIn("A3-COMMIT-OK", serial,
                         "the no-op protection act commits nothing -> a commit-dependent touch faults:\n"
                         + serial[-2500:])
        self.assertRegex(serial, r"FLOOR3-FAULT: vec=0x0*e ",
                         "a #PF (vector 14): with mprotect a no-op, a reserved-then-'committed' page is never "
                         "backed, so the touch faults — the protection act IS the commit point:\n"
                         + serial[-2500:])

    def test_the_back_at_reserve_plant_reds_a2_the_touch_does_not_fault(self):
        # PLANT (A2, one that CAN fail): the reservation is backed at reserve, so touching it does NOT fault
        # — the run produces NO reservation-touch fault (the enforcement check has nothing to record).
        serial = _dyn_serial("back-at-reserve", fault="PLANT_BACK_AT_RESERVE")
        self._skip_if_dynamic_floor_env_blocked(serial)
        self.assertIn("A3-COMMIT-OK", serial, "under the plant a backed reservation still commits+writes")
        self.assertIn("A2-TOUCH", serial, "the prover reached the A2 touch")
        # the distinguishing fact: the clean run faults at the A2 reservation touch; this plant run touches a
        # BACKED reservation and does NOT fault (A2-NO-FAULT), so there is no reservation-touch #PF.
        self.assertIn("A2-NO-FAULT", serial,
                      "the touch of a backed reservation returned without faulting:\n" + serial[-2500:])
        self.assertNotRegex(serial, r"FLOOR3-FAULT: vec=0x0*e cr2=0x7[0-9a-f]{11}",
                            "a backed reservation does not fault when touched (no reservation-touch #PF):\n"
                            + serial[-2500:])

    def test_the_frame_leak_plant_ooms_the_a4_reclaim_loop(self):
        # PLANT (A4, existing serve_munmap frame-leak): the committed frames are not returned on unmap, so the
        # reclaim loop's churn drains the pool and mprotect ENOMEMs (A4-OOM) — the committed frames MUST return.
        serial = _dyn_serial("frameleak", fault="PLANT_FRAME_LEAK")
        self._skip_if_dynamic_floor_env_blocked(serial)
        self.assertIn("A4-START", serial, "the prover reached the A4 reclaim loop")
        self.assertIn("A4-OOM", serial,
                      "the leak drained the pool — the reclaim loop OOMs by a real mechanism:\n" + serial[-2500:])
        self.assertNotIn("A4-RECLAIM-LOOP-OK", serial, "the leak run must not complete the loop")

    def test_the_unguarded_free_plant_corrupts_the_a4_alias_sentinel(self):
        # PLANT (A4, existing serve_munmap unguarded-free): the whole-range unmap over-frees a still-live
        # neighbour frame; pmm_alloc hands it to the next map; the two alias and the sentinel reads back the
        # new map's bytes -> A4-ALIAS-CORRUPT (a double-free is silent and reds nothing, so it frees a LIVE frame).
        serial = _dyn_serial("unguarded", fault="PLANT_FRAME_FREE_UNGUARDED")
        self._skip_if_dynamic_floor_env_blocked(serial)
        self.assertIn("A4-RECLAIM-LOOP-OK", serial, "the unguarded free only over-reaches — the loop still runs")
        self.assertIn("A4-ALIAS-CORRUPT", serial,
                      "the over-freed live frame aliased the next map -> the sentinel reads back corrupted:\n"
                      + serial[-2500:])
        self.assertNotIn("A4-ALIAS-OK", serial, "the plant run must not report the sentinel intact")


if __name__ == "__main__":
    unittest.main()
