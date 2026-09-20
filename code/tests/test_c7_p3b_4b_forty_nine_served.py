# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding body serving a measured set of kernel requests in their measured x86_64 shapes: the
# twelve acts' share performed by the act machinery, the bring-up/thread/module-scan/probe requests as
# rows of the body's own append-only crossing trail, module bytes from a sealed image, no filesystem walk)
# as in the seL4/gVisor/Fuchsia and osdev literature. NON-GOAL: no offensive capability — this DRIVES the
# acceptance of C7 P3b-4b: our own body answers exactly the requests a program was measured to make and
# refuses the rest in the program's own words, proven request by request with OUR small test worker (never
# a borrowed interpreter); it boots nothing into production, touches no host kernel (every boot the guest's
# nested qemu).
"""C7 P3b-4b acceptance — THE FORTY-NINE SERVED (design/54 §5 L18, §7 P3b-4b; the P3b-4s FINDINGS the spec;
precision (a)/(b) of board :4089/:4085).

On the enclosed long-mode body (P3b-4a), the body SERVES THE FORTY-NINE MEASURED REQUESTS in their measured
x86_64 shapes — the twelve acts' share performed by the act machinery; the hard floor (bring-up/loader/TLS,
thread creation) realized on the metal as the memory and concurrency acts' machinery; the designed refusal
(module discovery on a live filesystem) refused with module bytes from the SEALED image (digest-checked at
load), no filesystem walk; the stubs degrading; entropy served AT BRING-UP; the network-socket share
refused as the worker's native failure until P3b-6 — and WITNESSES EVERY crossing as ONE UNSIGNED row of
the body's own serve trail. OUR test worker (P3b-4a's, extended) makes each request; the body holds no key.

  A1  the body serves the forty-nine in their measured shapes, request by request, with OUR test worker;
      each served / refused / stubbed and witnessed as one trail row; the twelve rows' digest still on
      serial (nested guest)
  A2  EVERY crossing is one UNSIGNED trail row; the acts' share is PERFORMED and WITNESSED like every
      crossing (precision a — the signed act row is the gate's, ABOVE the seam, deferred to P3b-4c, NO gate
      on the body here; the body is KEY-LESS); planted "an act's-share crossing without a row" / "a signed
      row (a key)" / "a request in the estate's signed chain" / "the socket share served" reds its own check
  A3  the argument shapes that bite are honored (Q-D): memory private no fork (Q11), the futex PRIVATE
      bitset realtime wait, thread-create with SETTLS, the absolute-monotonic commit-window; entropy AT
      BRING-UP; planted wrong-shape faults red their own checks
  A4  the designed refusal: module bytes from the SEALED image (digest-checked before load, precision b),
      no filesystem walk; a planted "filesystem walk served" reds its own check
  A5  OUR serve C is ATTESTED BY NAME (85 -> 87); the built worker IMAGE is never a member; no borrowed
      interpreter enters this slice; guest-only, revertable, no one-way door (the scans CAN fail)
  A6  no founding (ACT_KINDS twelve, the pack byte-unchanged, founding 1.55.0); the count-pins move by name

A1/A2(guest)/A3(guest)/A4(guest) build+boot in the NESTED guest (a bodyfs disk attached so the record acts
perform on the body's own disk, as P3b-2) and skip when the pinned guest is not reachable over SSH; A5/A6
run in main. Register: OS bring-up on a disposable guest, described by function — a body that answers exactly
the measured requests and refuses the rest; validated by building/reading, never by attack
(governance-work-method). Every kernel touch is the guest's nested qemu; the host kernel is never touched
(L11 / EP-00 rule 9 / charter §A21).
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
sys.path.insert(0, SRC)

ROWS_DIGEST = "sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb"

# OUR serve C this slice adds under src/body/ (attested by name, A5). The test worker (worker.S) is
# EXTENDED, not new, so it is not in this list; the built worker IMAGE is never a member.
NEW_SERVE_FILES = ("body/serve.c", "body/serve.h")

# ── the forty-nine, by category (the P3b-4s FINDINGS checklist; the syscall NUMBER -> (name, cat, verdict)).
# cat: 1=A bring-up/loader/TLS floor · 2=B thread floor · 3=ACT the twelve acts' share · 4=C designed
# refusal · 5=D stubs · 6=SOCK the network-socket share refused. A few NAMES carry two rows (a name is not
# a boundary, PURPOSE is): getrandom the bring-up seed (A) + the entropy act (ACT); clock_gettime twice
# (ACT, two clockids); openat the record act (ACT) + the module-search refusal (C).
SERVED, REFUSED, STUBBED = "SERVED", "REFUSED", "STUBBED"
CAT_A, CAT_B, CAT_ACT, CAT_C, CAT_D, CAT_SOCK = 1, 2, 3, 4, 5, 6

# each entry: (num, cat, verdict) that MUST appear as a serve row (a name with two treatments appears twice).
EXPECT_ROWS = [
    # category A — bring-up / loader / TLS floor (SERVED)
    (318, CAT_A, SERVED),   # getrandom GRND_NONBLOCK — entropy AT BRING-UP
    (59, CAT_A, SERVED),    # execve (the loader's own)
    (12, CAT_A, SERVED),    # brk
    (158, CAT_A, SERVED),   # arch_prctl (ARCH_SET_FS — TLS)
    (218, CAT_A, SERVED),   # set_tid_address
    (273, CAT_A, SERVED),   # set_robust_list
    (334, CAT_A, SERVED),   # rseq
    (302, CAT_A, SERVED),   # prlimit64
    (10, CAT_A, SERVED),    # mprotect
    (17, CAT_A, SERVED),    # pread64 (loader ELF headers)
    (21, CAT_A, SERVED),    # access (ld.so.preload)
    (89, CAT_A, SERVED),    # readlink
    (79, CAT_A, SERVED),    # getcwd
    (13, CAT_A, SERVED),    # rt_sigaction
    (14, CAT_A, SERVED),    # rt_sigprocmask
    (231, CAT_A, SERVED),   # exit_group (the run terminator)
    # category B — thread creation floor (SERVED)
    (435, CAT_B, SERVED),   # clone3 (THREAD+VM+SETTLS+CHILD_CLEARTID)
    (28, CAT_B, SERVED),    # madvise (MADV_DONTNEED)
    (186, CAT_B, SERVED),   # gettid
    # the twelve acts' share — performed by the act machinery, witnessed like every crossing (ACT, SERVED)
    (9, CAT_ACT, SERVED),   # mmap — the memory act (Q11)
    (11, CAT_ACT, SERVED),  # munmap
    (202, CAT_ACT, SERVED), # futex — concurrency
    (228, CAT_ACT, SERVED), # clock_gettime — recording-clock + commit-window reads (two rows)
    (230, CAT_ACT, SERVED), # clock_nanosleep — commit-window
    (318, CAT_ACT, SERVED), # getrandom blocking — the entropy act
    (257, CAT_ACT, SERVED), # openat — the record-pen open
    (1, CAT_ACT, SERVED),   # write
    (75, CAT_ACT, SERVED),  # fdatasync
    (74, CAT_ACT, SERVED),  # fsync
    (0, CAT_ACT, SERVED),   # read
    (3, CAT_ACT, SERVED),   # close
    (5, CAT_ACT, SERVED),   # fstat
    (262, CAT_ACT, SERVED), # newfstatat
    (82, CAT_ACT, SERVED),  # rename
    (83, CAT_ACT, SERVED),  # mkdir
    (87, CAT_ACT, SERVED),  # unlink (a blob, never the record)
    (39, CAT_ACT, SERVED),  # getpid — single-writer-lock
    (62, CAT_ACT, SERVED),  # kill(pid,0) — pid_alive
    (217, CAT_ACT, SERVED), # getdents64 — body-read walk
    (8, CAT_ACT, SERVED),   # lseek
    # category C — module discovery on a live filesystem: the DESIGNED REFUSAL (REFUSED)
    (291, CAT_C, REFUSED),  # epoll_create1 — the import machinery
    (257, CAT_C, REFUSED),  # openat(MODULE_SEARCH) — same name, refused purpose
    # category D — io-layer / environment probes: the STUBS (STUBBED)
    (16, CAT_D, STUBBED),   # ioctl (TCGETS — isatty)
    (72, CAT_D, STUBBED),   # fcntl
    (107, CAT_D, STUBBED),  # geteuid
    (102, CAT_D, STUBBED),  # getuid
    (108, CAT_D, STUBBED),  # getegid
    (104, CAT_D, STUBBED),  # getgid
    # the network-socket act share — refused as the native failure until P3b-6 (REFUSED)
    (41, CAT_SOCK, REFUSED),  # socket
]

# category E — EXCLUDED (harness teardown), named for honesty, never issued/served.
EXCLUDED_NUMS = {263: "unlinkat", 84: "rmdir"}

# the distinct measured NAMES: 47 issued + 2 excluded = the forty-nine (the P3b-4s headline).
DISTINCT_ISSUED = {num for (num, _c, _v) in EXPECT_ROWS}
NATIVE_FAIL = "ffffffffffffffda"   # -ENOSYS as a u64 — the socket + designed-refusal native answer

# the serve plants caught in-body and the SERVE CHECK each one must red (a check that can fail, §A64).
SERVE_FAULT_TO_CHECK = {
    "PLANT_SERVE_TRAIL_SKIP":       "SERVE CHECK WITNESSED: FAIL",
    "PLANT_BODY_SIGNS_ROW":         "SERVE CHECK KEYLESS: FAIL",
    "PLANT_ACT_ROW_IN_CHAIN":       "SERVE CHECK UNSIGNED: FAIL",
    "PLANT_ENTROPY_NOT_AT_BRINGUP": "SERVE CHECK ENTROPY-BRINGUP: FAIL",
    "PLANT_MEM_FORK_SHARED":        "SERVE CHECK MEM-PRIVATE: FAIL",
    "PLANT_THREAD_NO_SETTLS":       "SERVE CHECK THREAD-SHAPE: FAIL",
    "PLANT_COMMIT_NOT_ABSOLUTE":    "SERVE CHECK COMMIT-ABSOLUTE: FAIL",
    "PLANT_FUTEX_WRONG_SHAPE":      "SERVE CHECK FUTEX-SHAPE: FAIL",
    "PLANT_FS_WALK_SERVED":         "SERVE CHECK REFUSAL-MODULE: FAIL",
    "PLANT_SOCKET_SERVED":          "SERVE CHECK SOCKET-REFUSED: FAIL",
    "PLANT_SERVE_CATEGORY_E":       "SERVE CHECK EXCLUDED: FAIL",
}
ALL_SERVE_CHECKS = (
    "WITNESSED", "KEYLESS", "UNSIGNED", "ENTROPY-BRINGUP", "MEM-PRIVATE", "THREAD-SHAPE",
    "COMMIT-ABSOLUTE", "FUTEX-SHAPE", "REFUSAL-MODULE", "SOCKET-REFUSED", "EXCLUDED",
)

# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ───────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4b-accept"
_QEMU = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc"

_GDB_BASE = 2000 + (os.getpid() % 2000)
_boot_n = [0]


def _next_gdb_port():
    p = _GDB_BASE + (_boot_n[0] % 1800)
    _boot_n[0] += 1
    return p


def _guest_reachable():
    """True only if the PINNED guest (6.8.0-134-generic) answers over SSH AND the nested boot engine
    (qemu-system-x86_64) is present. Observes a state the check did not create (§A19)."""
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU"],
                           capture_output=True, timeout=20)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return r.returncode == 0 and "6.8.0-134-generic" in out and "QEMU" in out


GUEST = _guest_reachable()
_SEEDED = {"done": False}
_SERIAL_CACHE = {}


def _seed_guest():
    """Copy src/body + src/bridge + src/founding to the guest ONCE (mkdisk.py needs host_seam + the pack)."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=120)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=120, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", outdir=None):
    """Build the body (with OUR extended sealed test worker) in the guest; return (outdir, elf_sha, worker_sha)."""
    _seed_guest()
    out = outdir or (_WD + "/out" + (("-" + fault) if fault else ""))
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (_WD, _WD, out, fault)],
                       capture_output=True, timeout=180)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    line = b.stdout.decode(errors="replace")
    m = re.search(r"worker image seal sha256 ([0-9a-f]{64})", line)
    h = subprocess.run(_SSH + ["sha256sum %s/body.elf | cut -d' ' -f1" % out],
                       capture_output=True, timeout=20)
    return out, h.stdout.decode().strip(), (m.group(1) if m else None)


def _guest_mkdisk(img):
    """Format a FRESH bodyfs disk so the record acts perform on the body's own disk (as P3b-2)."""
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img, timeout_s=24):
    """Boot the body in a NESTED qemu with `img` as a virtual IDE disk (gdb stub from the first line, L17);
    return serial text. Every boot is the guest's nested qemu — no host kernel. Boots are SERIALIZED."""
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d %s -gdb tcp::%d -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, _next_gdb_port(), outdir, img)],
        capture_output=True, timeout=timeout_s + 25)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault=""):
    """Build a fresh disk + build+boot once per fault, cached (each guest boot is ~20s serialized)."""
    if fault not in _SERIAL_CACHE:
        out, _elf, _w = _guest_build(fault)
        img = _guest_mkdisk("%s/disk-%s.img" % (_WD, fault or "clean"))
        _SERIAL_CACHE[fault] = _guest_boot(out, img)
    return _SERIAL_CACHE[fault]


def _serve_rows(serial):
    """Parse the body's serve-trail readback into a list of dicts (each an UNSIGNED crossing row)."""
    rows = []
    for m in re.finditer(
            r"SERVE-ROW seq=0x([0-9a-f]+) num=0x([0-9a-f]+) cat=0x([0-9a-f]+) arg=0x([0-9a-f]+) "
            r"ans=0x([0-9a-f]+) sig=0x([0-9a-f]+) chain=0x([0-9a-f]+) (SERVED|REFUSED|STUBBED)", serial):
        rows.append({"seq": int(m.group(1), 16), "num": int(m.group(2), 16), "cat": int(m.group(3), 16),
                     "arg": m.group(4), "ans": m.group(5), "sig": int(m.group(6), 16),
                     "chain": int(m.group(7), 16), "verdict": m.group(8)})
    return rows


def _body_source_names():
    return sorted(n for n in os.listdir(BODY)
                  if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def tearDownModule():
    """Leave the guest as found: no nested-qemu boot survives this module (serialized guest)."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1TheFortyNineServedRequestByRequest(unittest.TestCase):
    def test_the_body_serves_the_forty_nine_in_their_measured_shapes_each_a_row(self):
        serial = _serial()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("LONGMODE: OK", serial, "the body is in the machine's long mode (P3b-4L)")
        self.assertIn("ENCLOSURE: PASS", serial, "the enclosure MECHANISM still passes (P3b-4a, unchanged)")
        self.assertIn("SERVE: PASS", serial, "the forty-nine serve self-check passes as a group")
        self.assertIn("SERVE-ACTS: PASS", serial)
        rows = _serve_rows(serial)
        # each of the forty-nine measured requests appears as a row with its measured treatment.
        by_key = {(r["num"], r["cat"], r["verdict"]) for r in rows}
        missing = [t for t in EXPECT_ROWS if t not in by_key]
        self.assertEqual(missing, [], "each measured request served/refused/stubbed as a row: missing %r" % missing)
        # the forty-nine distinct NAMES: 47 issued + 2 excluded.
        issued_names = {r["num"] for r in rows}
        self.assertEqual(issued_names, DISTINCT_ISSUED, "exactly the 47 issued measured names appear as rows")
        self.assertEqual(len(DISTINCT_ISSUED) + len(EXCLUDED_NUMS), 49, "47 issued + 2 excluded = the forty-nine")
        # the twelve rows' digest is STILL on serial after the serve phase.
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")

    def test_the_record_acts_perform_on_the_bodys_own_disk(self):
        # the file acts route to bodyfs (the same performers P3b-2 proved) — the disk is mounted this boot.
        serial = _serial()
        self.assertIn("DISK: OK", serial, "the bodyfs disk mounted — the record acts perform on it")
        rows = _serve_rows(serial)
        openat_record = [r for r in rows if r["num"] == 257 and r["cat"] == CAT_ACT]
        self.assertTrue(openat_record, "the record-pen openat is a served acts'-share row")
        # the record-pen open returned a real start_sector (the append hit the body's disk), not a stub 0.
        self.assertNotEqual(int(openat_record[0]["ans"], 16), 0,
                            "the record-pen append returned a disk start sector (performed on the body's disk)")


# ── A2 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2EveryCrossingOneUnsignedRowKeyless(unittest.TestCase):
    def test_every_crossing_is_one_unsigned_row_the_body_is_keyless(self):
        serial = _serial()
        rows = _serve_rows(serial)
        self.assertTrue(rows, "the serve trail has rows")
        # the trail is append-only, seq in order.
        self.assertEqual([r["seq"] for r in rows], list(range(len(rows))), "append-only, seq in order")
        # EVERY row is UNSIGNED (the body holds no key) and OUT of the estate's signed chain (precision a).
        for r in rows:
            self.assertEqual(r["sig"], 0, "row num=0x%x carries a signature — the body must be key-less" % r["num"])
            self.assertEqual(r["chain"], 0, "row num=0x%x appended into the signed chain — forbidden" % r["num"])
        # the acts' share is PERFORMED and WITNESSED like every crossing (never a signed gate row).
        acts = [r for r in rows if r["cat"] == CAT_ACT]
        self.assertTrue(acts, "the acts' share was served and witnessed as unsigned trail rows")
        self.assertTrue(all(r["sig"] == 0 and r["chain"] == 0 for r in acts),
                        "an acts'-share crossing is an UNSIGNED trail row, not a signed gate row (precision a)")
        self.assertIn("SERVE CHECK WITNESSED: PASS", serial, "every crossing recorded as a row")
        self.assertIn("SERVE CHECK KEYLESS: PASS", serial, "the body holds no key")
        self.assertIn("SERVE CHECK UNSIGNED: PASS", serial, "no request in the estate's signed chain")
        # the network-socket share is refused as the native failure (a trail row) until P3b-6.
        sock = [r for r in rows if r["num"] == 41]
        self.assertTrue(sock and sock[0]["verdict"] == REFUSED and sock[0]["ans"] == NATIVE_FAIL,
                        "the network-socket share refused as the worker's native failure (-ENOSYS), a row")
        self.assertIn("SERVE CHECK SOCKET-REFUSED: PASS", serial)

    def test_the_precision_a_and_socket_plants_red_their_own_check(self):
        for fault in ("PLANT_SERVE_TRAIL_SKIP", "PLANT_BODY_SIGNS_ROW", "PLANT_ACT_ROW_IN_CHAIN",
                      "PLANT_SOCKET_SERVED"):
            serial = _serial(fault)
            self.assertIn(SERVE_FAULT_TO_CHECK[fault], serial,
                          "%s must red %r (the check can fail)" % (fault, SERVE_FAULT_TO_CHECK[fault]))
            self.assertIn("SERVE: FAIL", serial, "%s must red the aggregate SERVE line" % fault)
            self._only_its_own_check_reds(serial, SERVE_FAULT_TO_CHECK[fault])

    def _only_its_own_check_reds(self, serial, expected_fail):
        # exactly one SERVE CHECK reds — the plant's own, no collateral (a plant is a targeted probe).
        failed = [c for c in ALL_SERVE_CHECKS if ("SERVE CHECK %s: FAIL" % c) in serial]
        self.assertEqual(len(failed), 1, "exactly one check reds; reds=%r" % failed)
        self.assertEqual("SERVE CHECK %s: FAIL" % failed[0], expected_fail)


# ── A3 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA3TheArgumentShapesBiteEntropyAtBringUp(unittest.TestCase):
    def test_the_qd_shapes_and_entropy_at_bringup_and_memory_private(self):
        serial = _serial()
        rows = _serve_rows(serial)
        # entropy AT BRING-UP: the GRND_NONBLOCK draw is a cat-A row served from the body's source.
        bringup = [r for r in rows if r["num"] == 318 and r["cat"] == CAT_A]
        self.assertTrue(bringup and int(bringup[0]["arg"], 16) == 1,
                        "getrandom(GRND_NONBLOCK) served AT BRING-UP (cat A, flags=1)")
        self.assertIn("SERVE CHECK ENTROPY-BRINGUP: PASS", serial)
        # memory act: MAP_SHARED requested (flags arg 0x21), served anonymous-PRIVATE (Q11, no fork).
        mmap = [r for r in rows if r["num"] == 9]
        self.assertTrue(mmap and (int(mmap[0]["arg"], 16) & 0x1) == 1,
                        "the memory act asks MAP_SHARED (0x21); the body serves it anonymous-PRIVATE (Q11)")
        self.assertIn("SERVE CHECK MEM-PRIVATE: PASS", serial)
        # thread-create: THREAD+VM+SETTLS+CHILD_CLEARTID reproduced (the clone3 flags row).
        clone = [r for r in rows if r["num"] == 435]
        self.assertTrue(clone and (int(clone[0]["arg"], 16) & 0x290100) == 0x290100,
                        "clone3 reproduces THREAD+VM+SETTLS+CHILD_CLEARTID (Q-D)")
        self.assertIn("SERVE CHECK THREAD-SHAPE: PASS", serial)
        # commit-window: clock_nanosleep MONOTONIC TIMER_ABSTIME (an absolute deadline).
        self.assertIn("SERVE CHECK COMMIT-ABSOLUTE: PASS", serial)
        # futex: PRIVATE bitset-wait with a realtime clock.
        futex = [r for r in rows if r["num"] == 202]
        self.assertTrue(futex and (int(futex[0]["arg"], 16) & 0x189) == 0x189,
                        "the wait is FUTEX_WAIT_BITSET|PRIVATE|CLOCK_REALTIME (Q-D)")
        self.assertIn("SERVE CHECK FUTEX-SHAPE: PASS", serial)

    def test_the_wrong_shape_plants_red_their_own_check(self):
        for fault in ("PLANT_ENTROPY_NOT_AT_BRINGUP", "PLANT_MEM_FORK_SHARED",
                      "PLANT_THREAD_NO_SETTLS", "PLANT_COMMIT_NOT_ABSOLUTE", "PLANT_FUTEX_WRONG_SHAPE"):
            serial = _serial(fault)
            self.assertIn(SERVE_FAULT_TO_CHECK[fault], serial,
                          "%s must red %r (Q-D shapes bite)" % (fault, SERVE_FAULT_TO_CHECK[fault]))
            self.assertIn("SERVE: FAIL", serial, "%s must red the aggregate SERVE line" % fault)


# ── A4 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A4 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA4DesignedRefusalModuleBytesFromSealedImage(unittest.TestCase):
    def test_the_module_scan_is_refused_bytes_from_the_sealed_image_no_walk(self):
        serial = _serial()
        # the sealed image was digest-checked before load (P3b-4a's loader, precision b).
        self.assertIn("LOAD: OK (digest matches the seal)", serial, "the sealed image digest-checked before load")
        rows = _serve_rows(serial)
        # module discovery on a live filesystem is REFUSED (category C rows: epoll_create1 + openat(module)).
        cat_c = [r for r in rows if r["cat"] == CAT_C]
        self.assertTrue(any(r["num"] == 291 for r in cat_c), "epoll_create1 refused (import machinery)")
        self.assertTrue(any(r["num"] == 257 for r in cat_c), "openat(MODULE_SEARCH) refused (same name, a refused purpose)")
        self.assertTrue(all(r["verdict"] == REFUSED for r in cat_c), "the module-discovery scan is refused")
        self.assertIn("SERVE CHECK REFUSAL-MODULE: PASS", serial,
                      "the scan refused, the module bytes served from the sealed image (ELF magic), no walk")

    def test_a_planted_filesystem_walk_served_reds_its_own_check(self):
        serial = _serial("PLANT_FS_WALK_SERVED")
        self.assertIn("SERVE CHECK REFUSAL-MODULE: FAIL", serial,
                      "a served module-discovery walk reds the designed-refusal check")
        self.assertIn("SERVE: FAIL", serial)


# ── A5 ───────────────────────────────────────────────────────────────────────────────────────────
def _host_kernel_load_tokens(text):
    return [tok for tok in ("insmod", "modprobe") if tok in text]


# ── C7 MAINT-BODY-SCANS: the "no borrowed interpreter in the body" property, at its real home ──────────
# The scan below once read the body's SOURCE TEXT for the words "cpython"/"libpython"; P3b-4c/4g added
# LEGITIMATE comments naming the real borrowed interpreter (design/54 L19) to serve.c/enclosure.c, so a
# word scan reddened on a comment while property I3 (no borrowed code INSIDE the signed base) held intact.
# The property lives in TWO places — the body.elf link (build.sh, where "linked into body.elf" is decided)
# and the attested member list — and is checked there, never in prose.
def _body_elf_link_command(build_text):
    """The single gcc invocation that links body.elf, with backslash-continuations joined."""
    joined = re.sub(r"\\\n[ \t]*", " ", build_text)
    for line in joined.splitlines():
        if line.lstrip().startswith("gcc") and '-o "$OUT/body.elf"' in line:
            return line
    return None


def _link_inputs(link_command):
    """The object files and library-link flags actually linked into body.elf."""
    objs = re.findall(r'"\$OUT/([A-Za-z0-9_.+-]+\.o)"', link_command)
    libs = re.findall(r"(?:^|\s)(-l[:\w.+-]+)", link_command)
    return objs, libs


def _borrowed_interpreter_link_inputs(objs, libs):
    """Any link input that is a borrowed interpreter / C-library object or a flag pulling one."""
    bad = [o for o in objs if any(t in o.lower() for t in ("cpython", "libpython", "python"))]
    bad += [l for l in libs if l.startswith("-lpython") or l in ("-lc", "-lpython3")]
    return bad


def _interpreter_members(members):
    """Any attested member whose path is a borrowed interpreter file (never a signed member, §9 mech 3)."""
    return [m for m in members
            if any(t in m.lower() for t in ("cpython", "libpython", "ld-linux", "libc.so"))]


class TestA5OurServeCAttestedGuestOnlyRevertable(unittest.TestCase):
    def test_our_serve_c_is_attested_by_name_and_count_is_87(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        for rel in NEW_SERVE_FILES:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s is not attested by name (§9 mechanism 1)" % rel)
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "the 31 src/body/ source files (30 + 1 net.c, C7 P3b-6a)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "85 -> 87 (the 2 serve files) -> 88 (+1 net.c, C7 P3b-6a)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers the new C/.h")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list (I7)")

    def test_the_built_worker_image_is_never_a_signed_member(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built worker image is NEVER a signed member")

    def test_no_borrowed_interpreter_enters_this_slice(self):
        # RE-POINTED (C7 MAINT-BODY-SCANS): from a source-TEXT word scan (which reddened on the legitimate
        # P3b-4c/4g comments naming the real interpreter) to the PROPERTY I3 those comments do not breach —
        # (A2) body.elf links no interpreter / borrowed C-library object, and (A3) no attested member is an
        # interpreter file. The forty-nine are proven with OUR test worker (worker.S), never the borrowed
        # interpreter (that is P3b-4c, a sealed image/module — never linked, never a member).
        from kernel.attestation import ATTESTED_MEMBERS

        # (A2) the body.elf link — where "linked into body.elf" is decided.
        with open(os.path.join(BODY, "build.sh"), encoding="utf-8") as _bf:
            link = _body_elf_link_command(_bf.read())
        self.assertIsNotNone(link, "the body.elf link command was not found in src/body/build.sh")
        self.assertIn("-nostdlib", link, "the body link must be freestanding (no borrowed C runtime linked)")
        objs, libs = _link_inputs(link)
        self.assertEqual(_borrowed_interpreter_link_inputs(objs, libs), [],
                         "body.elf links a borrowed interpreter / C-library object (I3 breach)")
        # PLANT: a linked interpreter object / a -lpython flag reds the check (the scan CAN fail).
        self.assertEqual(_borrowed_interpreter_link_inputs(objs + ["libpython3.12.so"], libs),
                         ["libpython3.12.so"], "the linked-artifact scan cannot fail")
        self.assertEqual(_borrowed_interpreter_link_inputs(objs, libs + ["-lpython3.12"]),
                         ["-lpython3.12"], "the library-flag scan cannot fail")

        # (A3) no attested member is an interpreter file.
        self.assertEqual(_interpreter_members(ATTESTED_MEMBERS), [],
                         "an attested member is a borrowed interpreter file (I3 breach)")
        # PLANT: an interpreter file name in a FIXTURE copy of the member list reds (never the real manifest).
        planted = tuple(ATTESTED_MEMBERS) + ("body/libpython3.12.so.1.0",)
        self.assertEqual(_interpreter_members(planted), ["body/libpython3.12.so.1.0"],
                         "the member-list scan cannot fail")

    def test_no_host_kernel_load_in_the_serve_c_and_the_scan_can_fail(self):
        for name in ("serve.c", "serve.h"):
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                self.assertEqual(_host_kernel_load_tokens(f.read()), [],
                                 "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        self.assertEqual(_host_kernel_load_tokens("insmod x.ko"), ["insmod"])   # the scan CAN fail

    def test_the_p2_host_crossing_census_stays_clean(self):
        from tools.conformance import host_crossing_census as census
        self.assertEqual(census.undeclared_crossings(), {}, "the core (src/body serve.c included) is host-clean")


# ── A6 ───────────────────────────────────────────────────────────────────────────────────────────
class TestA6NoFoundingTwelveActs(unittest.TestCase):
    def test_no_founding_act_kinds_twelve_pack_byte_unchanged(self):
        import json
        from kernel.boot import ACT_KIND_RECORD_KIND

        with open(os.path.join(SRC, "founding", "founding-pack.json"), encoding="utf-8") as f:
            pack = json.load(f)
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
        kinds = {r["seam_kind"] for r in rows}
        self.assertEqual(len(kinds), 12, "ACT_KINDS stays twelve — serving the measured requests adds no act")


if __name__ == "__main__":
    unittest.main()
