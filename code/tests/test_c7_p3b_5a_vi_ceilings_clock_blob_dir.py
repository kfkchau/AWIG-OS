# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (a freestanding kernel body whose open-file table is Linux's width and reports it, whose
# CLOCK_REALTIME stamps a true calendar epoch read from the CMOS RTC rather than seconds-since-boot, and
# which serves a namespace one level under a world as a directory — the three axes P3b-5a-vi built and
# closed at both hands). NON-GOAL: no offensive capability — this delivers ONE standing test that watches
# behaviour already built, re-asserting on EVERY run that the three axes hold in the shipped source and,
# on the pinned guest's nested qemu, that the heaviest lock module runs green on the body while the planted
# narrow table reds it by the real EMFILE mechanism the 5a-vi serials show. It builds and reads OUR OWN
# kernel body inside a disposable nested guest; it stands nothing as production, binds no key, touches no
# host kernel (every boot the guest's nested qemu). Validate by building/reading, never by attack
# (governance-work-method). Full declaration: SCOPE-STATEMENT.md.
"""C7 P3b-5a-vi STANDING TEST — CEILINGS, CLOCK AND THE BLOB DIRECTORY (design/54 §7 P3b-5a-vi; the ONE new
test 5a-vi's fence named but did not deliver, found at 5a-vi's outer close and ruled to a GREEN maintenance
unit — plan planning/exec/C7-MAINT-5A-VI-STANDING-TEST.md; board :4398).

The three axes are BUILT and CLOSED — no body code changes here; this is the test that watches them, so the
ledger re-asserts them from run to run (L14: pins on the property, never on a location). Each axis carries
the planted failure the 5a-vi build already showed (a check that cannot fail is not a check, L19):

  A1  THE OPEN-FD TABLE IS LINUX'S WIDTH, AND REPORTED. The table width is Linux's soft RLIMIT_NOFILE
      (SI_MAX_FD 1024, derived peak-concurrent 203 << 1024, the :4234 derive-not-guess figure the 5a-vi
      close states) and serve_prlimit64 reports the SAME width (the report equals the width). PLANT_FD_-
      TABLE_NARROW restores the old 48-fd table -> lock-heavy modules EMFILE. Proven on the body: test_ep24c
      (a lighter lock module than test_ep26, which 5a-vi's fourth axis — frame reclamation, since resolved
      by 5a-vii — otherwise gates) runs GREEN on the body; PLANT_FD_TABLE_NARROW reds test_ep24c by EMFILE
      (OSError [Errno 24], the real mechanism the 5a-vi serials show).
  A2  CLOCK_REALTIME STAMPS A REAL CALENDAR TIME. serve_clock_gettime fills a CLOCK_REALTIME timespec with
      a true epoch — the CMOS RTC read at boot (clock.c rtc_read / clock_epoch_seconds, qemu -rtc base=utc)
      plus the monotonic since boot — so a witnessed arrival stamps a real calendar time, not 1970;
      CLOCK_MONOTONIC stays since-boot; the 4f-ii deadline/scheduler coupling is kept under one epoch base.
      PLANT_REALTIME_SINCE_BOOT answers CLOCK_REALTIME since-boot -> the TWO-TIMES rule reds; PLANT_DEADLINE_-
      CLOCK_UNCOUPLED offsets the deadline clock and not the scheduler's "now" -> the 4f-ii timed wait never
      times out (the 5a-vi serial shows a deadline ~56y out; asserted here WITHIN A BOUNDED WAIT, never a
      forever-hang). Asserted as source-shape pins on the property; the on-body proof stands in the 5a-vi
      serials cited below.
  A3  A NAMESPACE ONE LEVEL UNDER A WORLD IS A DIRECTORY. serve_ns_mkdir declares a namespace under a world
      as an FT_DIR that stats as a directory and lists its children; a present NON-directory name of the same
      spelling refuses mkdir (a directory is a directory, not a flat entry). PLANT_NS_STUB_NOOP answers
      success declaring nothing -> the listing reds. Asserted as source-shape pins on the property; the
      on-body proof (test_ep44 green; PLANT_NS_STUB_NOOP reds its listing) stands in the 5a-vi serials.

The source-shape pins run in main (no guest); the on-body A1 pair builds+boots in the pinned guest's nested
qemu and skips when the guest is not reachable over SSH. Every kernel touch is the guest's nested qemu; the
host kernel is never touched (L11 / EP-00 rule 9 / §A21). Validated by building/reading a real booted body,
never by attack (governance-work-method).

The plants (build.sh -D fault codes, the 5a-vi build's own names): PLANT_FD_TABLE_NARROW (A1),
PLANT_REALTIME_SINCE_BOOT / PLANT_DEADLINE_CLOCK_UNCOUPLED (A2), PLANT_NS_STUB_NOOP (A3). Their on-body
reddening is recorded in planning/evidence/C7-P3b-5a-vi-CEILINGS-CLOCK-BLOB-DIR/serials/ (5a-vi build) and,
for A1 on test_ep24c, in .../standing-test-5a-maint/ (this unit's run).
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
CLOCK_C = os.path.join(BODY, "clock.c")
CLOCK_H = os.path.join(BODY, "clock.h")
BODYFS_C = os.path.join(BODY, "bodyfs.c")
sys.path.insert(0, SRC)


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _func(src, signature):
    """Slice one C function body out of `src` by its signature line up to the next top-level `static `."""
    i = src.index(signature)
    j = src.index("\nstatic ", i + 1)
    return src[i:j]


# ── A1 (source shape) — the open-fd table is Linux's width, and serve_prlimit64 reports that same width ──
class TestA1FdTableWidthIsLinuxAndReported(unittest.TestCase):
    def test_the_table_width_is_linux_soft_rlimit_nofile(self):
        src = _read(SERVE_C)
        self.assertIn("#define SI_MAX_FD 1024u", src,
                      "the open-fd table width is Linux's soft RLIMIT_NOFILE (1024), grown from the old 48")
        self.assertIn("#if defined(PLANT_FD_TABLE_NARROW)", src, "the narrow-table plant gates the width")
        self.assertIn("#define SI_MAX_FD 48u", src,
                      "PLANT_FD_TABLE_NARROW restores the old 48-fd table (a plant that CAN fail, L19)")

    def test_prlimit64_reports_the_served_ceiling_equal_to_the_table_width(self):
        # the report EQUALS the width: serve_prlimit64 answers RLIMIT_NOFILE with SI_MAX_FD itself.
        src = _read(SERVE_C)
        prl = _func(src, "static uint64_t serve_prlimit64(")
        self.assertIn("RLIMIT_NOFILE_", prl, "serve_prlimit64 handles RLIMIT_NOFILE")
        self.assertIn("rl[0] = (uint64_t)SI_MAX_FD;", prl, "soft RLIMIT_NOFILE == the served table width")
        self.assertIn("rl[1] = (uint64_t)SI_MAX_FD;", prl, "hard RLIMIT_NOFILE == the served table width")
        self.assertIn("#define RLIMIT_NOFILE_  7u", src, "RLIMIT_NOFILE is resource 7 (Linux's number)")

    def test_the_fd_arrays_are_indexed_by_the_table_width(self):
        # the property that makes the width real: the fd table array is sized by SI_MAX_FD, not a constant.
        src = _read(SERVE_C)
        self.assertIn("g_fds[SI_MAX_FD]", src, "the fd table array is sized by the served width")


# ── A2 (source shape) — CLOCK_REALTIME is a true epoch; the coupling is kept; both clock plants exist ────
class TestA2ClockRealtimeIsATrueEpoch(unittest.TestCase):
    def test_clock_realtime_lays_the_rtc_derived_epoch_not_since_boot(self):
        src = _read(SERVE_C)
        cg = _func(src, "static uint64_t serve_clock_gettime(")
        self.assertIn("ns = serve_rt_base_ns() + sched_now_ns();", cg,
                      "CLOCK_REALTIME lays a TRUE epoch (RTC-derived base + since-boot), not 1970")
        self.assertIn("#if defined(PLANT_REALTIME_SINCE_BOOT)", cg,
                      "the since-boot plant gates the REALTIME fill (a plant that CAN fail, L19)")
        self.assertIn("the commit-window: since-boot, unchanged", cg,
                      "CLOCK_MONOTONIC stays since-boot (sched_now_ns), untouched")

    def test_the_epoch_base_is_computed_from_the_cmos_rtc_civil_date(self):
        src = _read(SERVE_C)
        base = _func(src, "static uint64_t serve_rt_base_ns(")
        self.assertIn("rtc_read(&w);", base, "the epoch base reads the CMOS RTC once at first use")
        self.assertIn("clock_epoch_seconds(&w)", base, "the civil date is converted to seconds-since-1970")
        ch = _read(CLOCK_H)
        self.assertIn("uint64_t clock_epoch_seconds(const struct wallclock *w);", ch,
                      "clock.h declares the civil-date-to-epoch conversion")
        cc = _read(CLOCK_C)
        self.assertIn("uint64_t clock_epoch_seconds(const struct wallclock *w) {", cc,
                      "clock.c defines the civil-date-to-epoch conversion")

    def test_the_4f_ii_deadline_scheduler_coupling_is_kept_and_its_plant_exists(self):
        src = _read(SERVE_C)
        self.assertIn("#if !defined(PLANT_DEADLINE_CLOCK_UNCOUPLED)", src,
                      "the deadline-coupling plant gates the REALTIME->monotonic conversion")
        self.assertIn("uint64_t base = serve_rt_base_ns();", src,
                      "the futex REALTIME deadline is converted to the scheduler's frame under the SAME base")
        self.assertIn("PLANT_DEADLINE_CLOCK_UNCOUPLED", src,
                      "the uncoupled-deadline plant is present (reds the 4f-ii timed wait, L19)")


# ── A3 (source shape) — a namespace one level under a world is a directory; the stub-noop plant exists ───
class TestA3NamespaceUnderWorldIsADirectory(unittest.TestCase):
    def test_serve_ns_mkdir_declares_a_directory_and_the_stub_plant_declares_nothing(self):
        src = _read(SERVE_C)
        nsm = _func(src, "static uint64_t serve_ns_mkdir(")
        self.assertIn("fs_mkdir(name)", nsm, "mkdir declares the namespace as a directory via fs_mkdir")
        self.assertIn("#ifdef PLANT_NS_STUB_NOOP", nsm,
                      "the stub-noop plant gates serve_ns_mkdir (a plant that CAN fail, L19)")

    def test_fs_mkdir_makes_an_ft_dir_and_a_present_nondirectory_name_refuses(self):
        # the FT_DIR pin: a directory is a directory, not a flat entry; a present non-dir name of the same
        # spelling refuses mkdir (returns -1), the idempotent present-dir returns 0.
        bf = _read(BODYFS_C)
        self.assertIn("int fs_mkdir(const char *name) {", bf, "bodyfs.c defines fs_mkdir")
        self.assertIn("e->type = FT_DIR;", bf, "fs_mkdir creates an FT_DIR directory entry")
        self.assertIn("return (ex->type == FT_DIR) ? 0 : -1;", bf,
                      "a present NON-directory name of the same spelling refuses mkdir (the FT_DIR pin)")

    def test_getdents_types_a_record_disk_directory_as_a_directory(self):
        src = _read(SERVE_C)
        self.assertIn("d->d_type = (be->type == FT_DIR) ? DT_DIR_ : DT_REG_;", src,
                      "getdents reports an FT_DIR child as a directory (DT_DIR), so listing sees a directory")

    def test_the_stub_noop_plant_is_present_in_serve_c(self):
        self.assertIn("PLANT_NS_STUB_NOOP", _read(SERVE_C),
                      "the blob-directory stub-noop plant is present (reds the listing, L19)")


# ── A4/A5 (source shape) — nothing else moved: no founding, no new src member, twelve act kinds ──────────
class TestA4A5NothingElseMoved(unittest.TestCase):
    def test_no_new_src_member_attested_holds_at_88(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                         "5a-vi edits members in place (serve.c/clock.c/clock.h/bodyfs.c/disk.h) — no new .c")
        for rel in ("body/serve.c", "body/clock.c", "body/bodyfs.c", "body/disk.h"):
            self.assertIn(rel, attestation.ATTESTED_MEMBERS, "%s is an attested member (edit-in-place)" % rel)

    def test_act_kinds_stay_twelve(self):
        from bridge.host_seam import ACT_KINDS
        self.assertEqual(len(ACT_KINDS), 12, "a served body ceiling is not a new act kind")

    def test_founding_unchanged_1_55_0(self):
        import json
        with open(os.path.join(SRC, "founding", "founding-pack.json")) as f:
            self.assertEqual(json.load(f)["founding_version"], "1.55.0", "no founding on a body-watching test")


# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu, serialized) ──
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "<GUEST>"]
_WD = "/tmp/p3b5avi-standing-accept"   # ISOLATED per-unit scratch (guest-side), nothing collides
# -m 256 == the PMM cap; -rtc base=utc for the epoch clock. Serialized: one nested qemu at a time.
_QEMU_LEDGER = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc"
RUN_MODULE = "test_ep24c"   # A1's on-body prover — a lock module lighter than test_ep26 (the fourth-axis gate)


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
    _SEEDED["done"] = True


def _kill_boots():
    subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"], capture_output=True, timeout=20)


def _build_ledger(tag, fault=""):
    _seed()
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(_SSH + ["cd %s/src && LEDGER=1 bash body/build.sh body %s %s" % (_WD, out, fault)],
                       capture_output=True, timeout=360)
    if b.returncode != 0:
        raise AssertionError("guest LEDGER build failed: " + b.stderr.decode(errors="replace"))
    txt = b.stdout.decode(errors="replace") + "\n" + b.stderr.decode(errors="replace")
    assert "sealed image seal sha256" in txt, "the sealed image was not staged: " + txt
    return out


def _mkdisk_tree(tag):
    img = "%s/disk-%s.img" % (_WD, tag)
    m = subprocess.run(
        _SSH + ["cd %s && GOVOS_TREE=1 GOVOS_RUNMOD=%s PYTHONPATH=%s/src python3 src/body/mkdisk.py %s"
                % (_WD, RUN_MODULE, _WD, img)],
        capture_output=True, timeout=180)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _boot_ledger(out, img, tag, wait_s=900):
    """Boot the body in a NESTED qemu (sealed image as -initrd MODULE, `img` an IDE disk), DETACHED with
    serial to a file, then POLL until BODY-HALT. wait_s is a CEILING, not a fixed wait — the poll returns
    the instant BODY-HALT appears; a high ceiling only guards a genuinely slow run. Serialized — one nested
    qemu at a time; the body halts (never reboots), pkill'd after the read. The poll runs inside this test
    subprocess (no background harness task)."""
    ser = "%s/serial-%s.txt" % (_WD, tag)
    run = "%s/run-%s.sh" % (_WD, tag)
    body = ("#!/bin/bash\npkill -9 -f 'qemu-system.*body.img' 2>/dev/null\nrm -f %s\n"
            "%s -serial file:%s -kernel %s/body.img -initrd %s/sealed.img "
            "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
            % (ser, _QEMU_LEDGER, ser, out, out, img))
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
    # delete the per-boot disk image immediately (disk hygiene / L11 discipline)
    subprocess.run(_SSH + ["rm -f %s" % img], capture_output=True, timeout=20)
    return r.stdout.decode(errors="replace").replace("\r", "")


def _ledger_serial(tag, fault=""):
    if tag not in _CACHE:
        out = _build_ledger(tag, fault)
        img = _mkdisk_tree(tag)
        _CACHE[tag] = _boot_ledger(out, img, tag)
    return _CACHE[tag]


def tearDownModule():
    if GUEST:
        _kill_boots()
        # remove the whole isolated scratch — 0 nested qemu and no scratch left at end
        subprocess.run(_SSH + ["rm -rf %s 2>/dev/null; true" % _WD], capture_output=True, timeout=30)


# ── A1 on the body — test_ep24c green; PLANT_FD_TABLE_NARROW reds it by EMFILE (the real mechanism) ──────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 on-body needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1LockModuleGreenOnBodyNarrowPlantEmfiles(unittest.TestCase):
    def test_test_ep24c_runs_green_on_the_body_no_emfile(self):
        serial = _ledger_serial("ep24c-green")
        self.assertIn("BODY-HALT", serial, "the body must reach BODY-HALT (a completed run)")
        self.assertRegex(serial, r"LEDGER-RESULT OK ran=31 failures=0 errors=0 skipped=0",
                         "test_ep24c's 31 tests run GREEN on the body:\n" + serial[-2500:])
        self.assertIn("LEDGER-EXIT-STATUS: 0x00000000", serial, "the REAL exit status is 0 (green)")
        self.assertNotIn("Errno 24", serial, "no EMFILE on the wide table — the 1024 ceiling holds")
        self.assertNotIn("MemoryError", serial, "the lighter lock module does not cross the frame-leak line")

    def test_the_narrow_table_plant_reds_test_ep24c_by_emfile(self):
        clean = _ledger_serial("ep24c-green")
        self.assertRegex(clean, r"LEDGER-RESULT OK ran=31", "clean: the module is green (the check CAN pass)")
        serial = _ledger_serial("ep24c-narrow", fault="PLANT_FD_TABLE_NARROW")
        self.assertIn("BODY-HALT", serial, "even a red run reaches BODY-HALT (a completed run)")
        self.assertIn("Errno 24", serial,
                      "the 48-fd table exhausts under the estate's lifetime-held lock fds — a REAL EMFILE "
                      "(OSError [Errno 24] Too many open files), not a flag:\n" + serial[-2500:])
        self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=31 failures=0 errors=[1-9]",
                         "the real run fails with errors (the EMFILE axis) — the wide table is load-bearing")
        self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")


if __name__ == "__main__":
    unittest.main()
