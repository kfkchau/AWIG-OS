# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (a freestanding kernel body answering "which directory am I in" with "/" so the C library's
# getcwd returns, and serving the record-tree ROOT /rec as a listable directory so the borrowed
# interpreter's own import machinery resolves a package off the record disk). NON-GOAL: no offensive
# capability — it runs OUR OWN provers on OUR OWN kernel body inside a nested guest and records honestly
# which greens and which reds and why. Every boot is the guest's nested qemu; no host kernel is touched
# (L11). Validate by building/reading, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-5B — CWD AND IMPORT PATH: the two completions proven ON THE BODY (host-side driver).

Guest-gated (the pinned 6.8.0-134 guest + nested qemu over SSH -p 2222). Each acceptance builds the body,
stages a fresh per-module record disk (GOVOS_TREE=1, GOVOS_RUNMOD=<module>), boots it in a NESTED qemu
(one at a time, serial to a file, poll BODY-HALT), and reads the REAL interpreter's report back off serial.

A1 — getcwd fills the caller's buffer with "/" (serve.c, BUILT):
    sole_appender greens (os.path.abspath -> os.getcwd returns "/"); PLANT_GETCWD_BARE_CODE reds it
    (a bare code, buffer never filled -> glibc's getcwd raises FileNotFoundError). Unchanged this slice.

A2 — the record-tree ROOT /rec lists (serve.c finder root-listing, this slice's work):
    the root's immediate children are the UNION of the tree archive's top-level dirs (src, tests) and the
    record disk's top-level names (record, founding-pack, runmod, govtree, tmp) — the same sub-directory
    listing extended to depth zero (archi :4467). With /rec on the import path (enclosure.c, landed):
      * the recroot prover lists the union (os.listdir('/rec'));
      * ep28e_w4 greens (its `from tests.test_ep28e_w3 import ...` package import resolves).
    PLANT_TREE_ROOT_NOLIST disables the root's directory answer -> os.listdir('/rec') raises
    FileNotFoundError -> both provers red BY A REAL MECHANISM, distinct from a green run (which lists).

Every boot's serial is written under planning/evidence/C7-MAINT-5B-CWD-AND-IMPORT-PATH/ for the close.
"""

import os
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
EVID = os.path.join(ROOT, "planning", "evidence", "C7-MAINT-5B-CWD-AND-IMPORT-PATH")

_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "<GUEST>"]
_WD = "/tmp/c7maint5b-cwd"                         # isolated per-unit guest scratch (host uses EVID + /tmp)
_QEMU = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc"
_PIN = "6.8.0-134-generic"

# case -> (build FAULT or "", GOVOS_RUNMOD, wait seconds)
CASES = {
    "a1-green":         ("",                       "test_sole_appender",       240),
    "a1-plant":         ("PLANT_GETCWD_BARE_CODE",  "test_sole_appender",       240),
    "a2-import-green":  ("",                       "test_ep28e_w4",            900),
    "a2-import-plant":  ("PLANT_TREE_ROOT_NOLIST",  "test_ep28e_w4",            240),
    "a2-listing-green": ("",                       "test_c7_maint_5b_recroot", 240),
    "a2-listing-plant": ("PLANT_TREE_ROOT_NOLIST",  "test_c7_maint_5b_recroot", 240),
    "a3-regression":    ("",                       "test_ep14b",               240),
}


def _guest_reachable():
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU"],
                           capture_output=True, timeout=25)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return r.returncode == 0 and _PIN in out and "QEMU" in out


def _nested_count():
    """nested qemu inside the guest, counted by the (15-char-truncated) comm field so this check's OWN ssh
    command line can never self-match — the count that must be 0 at start AND end. The guest VM's qemu runs
    on the HOST, not inside the guest, so any qemu-system here is a nested body boot."""
    r = subprocess.run(_SSH + ["ps -eo comm | grep -c '^qemu-system' || true"],
                       capture_output=True, timeout=20)
    try:
        return int(r.stdout.decode(errors="replace").strip().split("\n")[-1])
    except Exception:
        return -1


_SEEDED = {"done": False}


def _seed(force=False):
    """Ship src+tests into the guest scratch. Idempotent across processes via a sentinel — preserves the
    out-* build dirs so a later boot-case reuses the build the prep step made from THIS src."""
    if _SEEDED["done"]:
        return
    if not force:
        c = subprocess.run(_SSH + ["test -f %s/.seeded && echo YES || echo NO" % _WD],
                           capture_output=True, timeout=20)
        if b"YES" in c.stdout:
            _SEEDED["done"] = True
            return
    tar = subprocess.run(["tar", "-czf", "-", "-C", ROOT, "src", "tests"], capture_output=True, timeout=180)
    subprocess.run(_SSH + ["mkdir -p %s && rm -rf %s/src %s/tests" % (_WD, _WD, _WD)],
                   capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True, timeout=180, check=True)
    subprocess.run(_SSH + ["touch %s/.seeded" % _WD], capture_output=True, timeout=20)
    _SEEDED["done"] = True


def _build(fault):
    """LEDGER build; cached on the guest by a per-fault out dir (skipped if body.img+sealed.img already
    built from the current seed). Returns the out dir path."""
    _seed()
    tag = fault or "clean"
    out = "%s/out-%s" % (_WD, tag)
    have = subprocess.run(_SSH + ["test -f %s/body.img && test -f %s/sealed.img && echo YES || echo NO"
                                  % (out, out)], capture_output=True, timeout=20)
    if b"YES" in have.stdout:
        return out
    cmd = "cd %s/src && LEDGER=1 bash body/build.sh body %s %s" % (_WD, out, fault)
    b = subprocess.run(_SSH + [cmd], capture_output=True, timeout=420)
    txt = b.stdout.decode(errors="replace") + "\n" + b.stderr.decode(errors="replace")
    if b.returncode != 0 or "sealed image seal sha256" not in txt:
        raise AssertionError("guest LEDGER build (%s) failed:\n%s" % (tag, txt[-3000:]))
    return out


def _mkdisk(runmod, label):
    img = "%s/disk-%s.img" % (_WD, label)
    cmd = ("cd %s && GOVOS_TREE=1 GOVOS_RUNMOD=%s PYTHONPATH=%s/src python3 src/body/mkdisk.py %s"
           % (_WD, runmod, _WD, img))
    m = subprocess.run(_SSH + [cmd], capture_output=True, timeout=180)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk (%s) failed: %s" % (label, m.stderr.decode(errors="replace")))
    return img


def _boot(out, img, label, wait_s):
    """One nested boot (detached+poll — a foreground `timeout qemu` holds the ssh session; detached+poll is
    the reliable pattern). Serialized: 0 nested qemu required at entry, image removed and 0 required at exit."""
    assert _nested_count() == 0, "a nested qemu is already running — one boot at a time"
    ser = "%s/serial-%s.txt" % (_WD, label)
    run = "%s/run-%s.sh" % (_WD, label)
    body = ("#!/bin/bash\npkill -9 -f '[q]emu-system-x86_64' 2>/dev/null\nrm -f %s\n"
            "%s -serial file:%s -kernel %s/body.img -initrd %s/sealed.img "
            "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
            % (ser, _QEMU, ser, out, out, img))
    launch = ("cat > %s <<'EOS'\n%sEOS\nchmod +x %s; "
              "setsid timeout --signal=TERM 1000 %s >/dev/null 2>&1 & sleep 1; echo launched"
              % (run, body, run, run))
    subprocess.run(_SSH + [launch], capture_output=True, timeout=30)
    deadline = time.time() + wait_s
    while time.time() < deadline:
        r = subprocess.run(_SSH + ["grep -q BODY-HALT %s 2>/dev/null && echo HALTED || true" % ser],
                           capture_output=True, timeout=20)
        if b"HALTED" in r.stdout:
            break
        time.sleep(3)
    r = subprocess.run(_SSH + ["cat %s 2>/dev/null; true" % ser], capture_output=True, timeout=30)
    serial = r.stdout.decode(errors="replace").replace("\r", "")
    # cleanup: kill the (halted) nested qemu, remove the per-boot image, require 0 nested at exit
    subprocess.run(_SSH + ["pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null; rm -f %s; true" % img],
                   capture_output=True, timeout=20)
    assert _nested_count() == 0, "a nested qemu survived the boot — must be 0 at exit"
    return serial


def run_case(case):
    fault, runmod, wait_s = CASES[case]
    out = _build(fault)
    img = _mkdisk(runmod, case)
    serial = _boot(out, img, case, wait_s)
    os.makedirs(EVID, exist_ok=True)
    with open(os.path.join(EVID, "serial-%s.txt" % case), "w") as f:
        f.write(serial)
    return serial


GUEST = _guest_reachable()


@unittest.skipUnless(GUEST, "needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestCwdAndImportPathOnBody(unittest.TestCase):
    def test_a1_getcwd_greens_sole_appender(self):
        s = run_case("a1-green")
        self.assertIn("BODY-HALT", s)
        self.assertRegex(s, r"LEDGER-RESULT OK ran=11 failures=0 errors=0 skipped=0", s[-1500:])

    def test_a1_plant_bare_code_reds(self):
        s = run_case("a1-plant")
        self.assertIn("BODY-HALT", s)
        self.assertRegex(s, r"LEDGER-RESULT (FAILED|LOADERROR)", s[-1500:])
        self.assertIn("FileNotFoundError", s, "the getcwd fault reds via glibc's getcwd:\n" + s[-1500:])

    def test_a2_import_greens_ep28e_w4(self):
        s = run_case("a2-import-green")
        self.assertIn("BODY-HALT", s)
        self.assertRegex(s, r"LEDGER-RESULT OK ", s[-1500:])

    def test_a2_import_plant_root_nolist_reds(self):
        s = run_case("a2-import-plant")
        self.assertIn("BODY-HALT", s)
        self.assertNotRegex(s, r"LEDGER-RESULT OK ", "the plant must red the import:\n" + s[-1500:])
        self.assertIn("ModuleNotFoundError", s, s[-1500:])

    def test_a2_listing_greens_the_union(self):
        s = run_case("a2-listing-green")
        self.assertIn("BODY-HALT", s)
        self.assertRegex(s, r"LEDGER-RESULT OK ", s[-1500:])
        self.assertIn("RECROOT-LISTING", s)
        for n in ("src", "tests", "record", "founding-pack", "runmod", "govtree"):
            self.assertRegex(s, r"RECROOT-LISTING[^\n]*\b" + n.replace("-", r"\-") + r"\b",
                             "the union must include %s:\n%s" % (n, s[-1500:]))

    def test_a2_listing_plant_root_nolist_reds(self):
        s = run_case("a2-listing-plant")
        self.assertIn("BODY-HALT", s)
        self.assertNotRegex(s, r"LEDGER-RESULT OK ", "the plant must red the listing:\n" + s[-1500:])
        self.assertIn("FileNotFoundError", s, s[-1500:])

    def test_a3_prior_slice_unregressed(self):
        s = run_case("a3-regression")
        self.assertIn("BODY-HALT", s)
        self.assertRegex(s, r"LEDGER-RESULT OK ran=4 failures=0 errors=0 skipped=0", s[-1500:])


if __name__ == "__main__":
    # NO-ARGUMENT LAWFUL ENTRY (RELEASE-4 round 2, board :4642 (5)): a plain `python3 <this>` — the
    # public runner's invocation (it starts each module as its own process with no args) — runs the
    # module as an ordinary unittest. Outside the lab the guest-gated class SKIPS (skipUnless GUEST),
    # so the module reports a clean skip instead of crashing with the usage exit-2 it used to.
    if len(sys.argv) == 1:
        unittest.main()
        sys.exit(0)
    # one-case-per-invocation runner (serial, one nested boot; never all seven in one process). `prep`
    # seeds a clean guest scratch and builds the 3 body variants (no boot) so each boot-case is quick.
    if len(sys.argv) != 2 or (sys.argv[1] != "prep" and sys.argv[1] not in CASES):
        sys.stderr.write("usage: %s <prep|%s>\n" % (sys.argv[0], "|".join(CASES)))
        sys.exit(2)
    if not GUEST:
        sys.stderr.write("guest not reachable / not on the pin %s\n" % _PIN)
        sys.exit(3)
    if sys.argv[1] == "prep":
        subprocess.run(_SSH + ["rm -rf %s" % _WD], capture_output=True, timeout=30)
        _seed(force=True)
        for f in ("", "PLANT_GETCWD_BARE_CODE", "PLANT_TREE_ROOT_NOLIST"):
            o = _build(f)
            print("BUILT %s -> %s" % (f or "clean", o))
        print("PREP DONE; nested qemu now: %d" % _nested_count())
        sys.exit(0)
    out = run_case(sys.argv[1])
    tail = "\n".join(out.strip().split("\n")[-8:])
    print("=== %s ===\n%s" % (sys.argv[1], tail))
