# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (a freestanding kernel body running the estate's OWN test ledger green PER MODULE over a
# per-world record-disk namespace, the borrowed interpreter loaded from ONE sealed digest-checked image
# carrying the WHOLE shipped standard library, gov-os imported as content off the record disk by the
# interpreter's own import machinery served by path AND by listing). NON-GOAL: no offensive capability —
# it runs OUR OWN tests on OUR OWN kernel body inside a nested guest and records honestly which cannot run
# and why; it boots nothing into production; it touches no host kernel (every boot is the guest's nested
# qemu). Validate by building/reading, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7 P3b-5b-i — THE BODY: THE LEDGER GREEN ON IT (the walking skeleton).

This is the FIRST sub-slice of C7-P3b-5b (design/54 §7 P3b-5b; the sub-split confirmed as HOW at board
:4303). It proves the on-body Python-execution RUN STACK end-to-end on ONE non-content green-demand module
(test_ep14b), measures the per-module boot cost, and records the A1 derivation + the A2 declared-out record.
Later sub-slices carry the remaining green-demand modules in cost-sized batches, the content axis (A3), and
the wake checklist + genesis pair at boot (A4). The acceptance stays whole across the sub-slices.

A1 (off-body, driven from the 5s2 measurement) — the write-class PASS SET is 81 PASS-CANDIDATE + 55
    R2-only-.lock = 136; the NON-CONTENT green-demand set is 106 (the exit-0 pass set minus the two facility
    names test_ep22 + test_ep30_c5); the 28 exit-1 pass-candidates route by recorded cause (21 content, 3
    fuse, 3 import-at-dispatch, 1 standing red). The counts are RE-DERIVED here from
    planning/evidence/C7-P3b-5s2-WRITE-CLASSES/{results.tsv,exit1-causes.txt} — never inherited from prose.
A2 (off-body) — every module NOT demanded green is declared out with a class and owner; the whole 207
    reconciles (106 non-content + 3 import + 21 content-A3 + 77 declared-out).
B1 (on-body, guest-gated) — test_ep14b runs GREEN per module on the body over 5a's /rec archive: the real
    unmodified CPython, loaded from the ONE sealed image carrying the WHOLE shipped stdlib (digest-checked
    WHOLE), imports gov-os from /rec/src by the interpreter's OWN machinery served by path AND by listing,
    reads the founding pack from the archive, and its real unittest report + exit status come back on serial.
    THE PLANT (L19): a real assertion planted in the staged module reddens the real run — exit status 1,
    the real AssertionError in the report; no runner of ours reads or fabricates a test's outcome.

THE WRONG REFERENCE THIS SLICE REFUSES: results.tsv "PASS-CANDIDATE" is a WRITE-CLASS verdict, NOT green —
28 of the 136 exited 1 under the trace and 2 more are facility-excluded rc-0; a syscall's presence in a
census is not a path's writability (:4234/:4235). The green-demand set is the DERIVATION with the two
facility names subtracted and the 28 routed by cause; the count is re-derived, never a magic constant.
"""

import csv
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

S2 = os.path.join(ROOT, "planning", "evidence", "C7-P3b-5s2-WRITE-CLASSES")
RESULTS_TSV = os.path.join(S2, "results.tsv")
CAUSES_TXT = os.path.join(S2, "exit1-causes.txt")

WALK_MODULE = "test_ep14b"   # the ONE non-content green-demand walking-skeleton module (tmp_paths=0)

FACILITY_RC0 = {"test_ep22", "test_ep30_c5"}   # R2-only rc-0 but facility-excluded (subtracted from 106)


# ────────────────────────────────────────────────────────────────────────────────────────────────────
# A1/A2 — the derivation, driven from the 5s2 measurement (off-body; runs everywhere).
# ────────────────────────────────────────────────────────────────────────────────────────────────────
def _rows():
    with open(RESULTS_TSV, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _pass_set(rows):
    """The 136: status PASS-CANDIDATE, OR status REFUSED whose ONLY refused class is R2 (the .lock idiom)."""
    return [r for r in rows if r["status"] == "PASS-CANDIDATE"
            or (r["status"] == "REFUSED" and r["R_classes"] == "R2")]


def _causes():
    out = {}
    with open(CAUSES_TXT) as f:
        for ln in f:
            p = ln.rstrip("\n").split(" ", 1)
            if p and p[0]:
                out[p[0]] = p[1] if len(p) > 1 else ""
    return out


@unittest.skipUnless(
    os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv")),
    "SKIP PRIVATE-SOURCE: needs planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv (absent in the render)")
class TestA1PassSetDerived(unittest.TestCase):
    """The pass set + the non-content green-demand set, RE-DERIVED (never inherited from prose)."""

    def test_pass_set_is_81_plus_55_eq_136(self):
        rows = _rows()
        self.assertEqual(len(rows), 207, "5s2 measured 207 modules")
        pc = [r for r in rows if r["status"] == "PASS-CANDIDATE"]
        r2 = [r for r in rows if r["status"] == "REFUSED" and r["R_classes"] == "R2"]
        self.assertEqual(len(pc), 81, "81 PASS-CANDIDATE (results.tsv status)")
        self.assertEqual(len(r2), 55, "55 REFUSED whose only class is R2 (the .lock one-writer idiom)")
        self.assertEqual(len(pc) + len(r2), 136, "the write-class pass set is 136")

    def test_noncontent_green_demand_is_106(self):
        rows = _rows()
        ps = _pass_set(rows)
        exit0 = [r for r in ps if r["exit"] == "0"]
        self.assertEqual(len(exit0), 108, "108 of the 136 exited 0 under the trace")
        noncontent = [r for r in exit0 if r["module"] not in FACILITY_RC0]
        self.assertEqual(len(noncontent), 106,
                         "the NON-CONTENT green-demand set is 106 (108 exit-0 minus the 2 facility names)")
        # the two subtracted names are exactly the facility rc-0 pair
        self.assertEqual(sorted(r["module"] for r in exit0 if r["module"] in FACILITY_RC0),
                         ["test_ep22", "test_ep30_c5"])

    def test_the_walking_skeleton_module_is_in_the_106(self):
        rows = _rows()
        noncontent = {r["module"] for r in _pass_set(rows)
                      if r["exit"] == "0" and r["module"] not in FACILITY_RC0}
        self.assertIn(WALK_MODULE, noncontent,
                      "the walking-skeleton module must be a non-content green-demand module")


@unittest.skipUnless(
    os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv")),
    "SKIP PRIVATE-SOURCE: needs planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv (absent in the render)")
class TestA1bExit1RoutedByCause(unittest.TestCase):
    """The 28 exit-1 pass-candidates settled by recorded cause BEFORE any green demand."""

    def test_28_exit1_route_to_21_content_3_fuse_3_import_1_standing_red(self):
        rows = _rows()
        exit1 = [r["module"] for r in _pass_set(rows) if r["exit"] != "0"]
        self.assertEqual(len(exit1), 28, "28 of the 136 pass-candidates exited 1 under the trace")
        cause = _causes()
        fuse = imp = std = content = 0
        for m in exit1:
            c = cause.get(m, "")
            if "fuse" in c:
                fuse += 1
            elif "ImportError" in c:
                imp += 1
            elif "AssertionError" in c:
                std += 1
            else:
                content += 1
        self.assertEqual((content, fuse, imp, std), (21, 3, 3, 1),
                         "21 content, 3 fuse, 3 import-at-dispatch, 1 standing red")
        self.assertEqual(content + fuse + imp + std, 28)

    def test_the_three_fuse_and_one_standing_red_named(self):
        cause = _causes()
        fuse = sorted(m for m, c in cause.items() if "fuse" in c
                      and m in {r["module"] for r in _pass_set(_rows()) if r["exit"] != "0"})
        self.assertEqual(fuse, ["test_ep25", "test_ep28e_w2", "test_maint_outside_3"])
        self.assertIn("AssertionError", cause.get("test_ep28c_w6", ""),
                      "the one standing red is test_ep28c_w6 (:1948)")


@unittest.skipUnless(
    os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv")),
    "SKIP PRIVATE-SOURCE: needs planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv (absent in the render)")
class TestA2DeclaredOutReconciles(unittest.TestCase):
    """Every module NOT demanded green is declared out; the whole 207 reconciles by verdict."""

    def _classify(self):
        rows = _rows()
        cause = _causes()
        ps = {r["module"] for r in _pass_set(rows)}
        verdicts = {}
        for r in rows:
            m, st, R, ex = r["module"], r["status"], r["R_classes"], r["exit"]
            Rs = set(R.split(",")) if R and R != "-" else set()
            if st == "SKIPPED-GUEST-DRIVING":
                verdicts[m] = "DECLARED:GUEST-DRIVING"
            elif m in ps:
                if m in FACILITY_RC0:
                    verdicts[m] = "DECLARED:FACILITY"
                elif ex == "0":
                    verdicts[m] = "GREEN:NON-CONTENT"
                else:
                    c = cause.get(m, "")
                    if "fuse" in c:
                        verdicts[m] = "DECLARED:FACILITY"
                    elif "ImportError" in c:
                        verdicts[m] = "GREEN:IMPORT-AT-DISPATCH"
                    elif "AssertionError" in c:
                        verdicts[m] = "DECLARED:STANDING-RED"
                    else:
                        verdicts[m] = "GREEN-DEFERRED:CONTENT-AXIS-A3"
            elif "R8" in Rs or "R6" in Rs or "R3" in Rs:
                verdicts[m] = "DECLARED:FACILITY"
            elif "R1" in Rs or "R5" in Rs:
                verdicts[m] = "DECLARED:HARNESS"
            else:
                verdicts[m] = "DECLARED:OTHER-REFUSED"
        return verdicts

    def test_all_207_classified_and_reconcile(self):
        v = self._classify()
        self.assertEqual(len(v), 207)
        from collections import Counter
        c = Counter(v.values())
        self.assertEqual(c["GREEN:NON-CONTENT"], 106)
        self.assertEqual(c["GREEN:IMPORT-AT-DISPATCH"], 3)
        self.assertEqual(c["GREEN-DEFERRED:CONTENT-AXIS-A3"], 21)
        declared = sum(n for k, n in c.items() if k.startswith("DECLARED:"))
        self.assertEqual(declared, 77, "77 declared out (facility/guest-driving/harness/standing-red)")
        self.assertEqual(106 + 3 + 21 + 77, 207)

    def test_no_declared_out_module_is_also_green_demand(self):
        v = self._classify()
        # a module is green-demand XOR declared-out — never both (the double-classification the :4288 bounce named)
        for m, verdict in v.items():
            self.assertTrue(verdict.startswith("GREEN") or verdict.startswith("DECLARED"), m)


# ────────────────────────────────────────────────────────────────────────────────────────────────────
# B1 — the on-body run (guest-gated; every boot the guest's nested qemu, host kernel untouched, L11).
# ────────────────────────────────────────────────────────────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "<GUEST>"]
_WD = "/tmp/p3b5bi-accept"
# -cpu qemu64 (SSE2, no AVX — the body keeps CR4.OSXSAVE clear); -m 256 == the PMM cap (the sealed image
# is carried as a multiboot MODULE reached through the direct map). Serialized: one nested qemu at a time.
_QEMU = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc"


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


def _build(tag):
    """LEDGER build: build.sh stages the ONE sealed image carrying the WHOLE shipped stdlib (no per-script
    manifest) + the DT_NEEDED closure of the program and every lib-dynload C extension + openssl.cnf. The
    'LEDGER STAGED ...' measurement line is on stderr; both streams are returned."""
    _seed()
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(_SSH + ["cd %s/src && LEDGER=1 bash body/build.sh body %s" % (_WD, out)],
                       capture_output=True, timeout=300)
    if b.returncode != 0:
        raise AssertionError("guest LEDGER build failed: " + b.stderr.decode(errors="replace"))
    txt = b.stdout.decode(errors="replace") + "\n" + b.stderr.decode(errors="replace")
    assert "sealed image seal sha256" in txt, "the sealed image was not staged: " + txt
    return out, txt


def _mkdisk(tag, plant=None):
    plantenv = ("GOVOS_PLANT_MOD=%s " % plant) if plant else ""
    img = "%s/disk-%s.img" % (_WD, tag)
    m = subprocess.run(
        _SSH + ["cd %s && GOVOS_TREE=1 GOVOS_RUNMOD=%s %sPYTHONPATH=%s/src python3 src/body/mkdisk.py %s"
                % (_WD, WALK_MODULE, plantenv, _WD, img)],
        capture_output=True, timeout=120)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _boot(out, img, tag, wait_s=120):
    """Boot the body in a NESTED qemu (sealed image as -initrd MODULE, `img` as an IDE disk), DETACHED
    (setsid) with serial to a file, then POLL the file until BODY-HALT (a foreground `timeout qemu` holds
    the ssh session — the detached+poll pattern is the reliable one). Serialized — one nested qemu at a
    time; the body halts (never reboots), so it is pkill'd after the read."""
    import time
    ser = "%s/serial-%s.txt" % (_WD, tag)
    run = "%s/run-%s.sh" % (_WD, tag)
    # write a run SCRIPT then setsid it — an inline `setsid bash -c` does not detach reliably over ssh; a
    # script file launched with `setsid <script> &` does (proven). The body halts (never reboots), so it is
    # pkill'd after the read.
    body = ("#!/bin/bash\npkill -9 -f 'qemu-system.*body.img' 2>/dev/null\nrm -f %s\n"
            "%s -serial file:%s -kernel %s/body.img -initrd %s/sealed.img "
            "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
            % (ser, _QEMU, ser, out, out, img))
    launch = ("cat > %s <<'EOS'\n%sEOS\nchmod +x %s; "
              "setsid timeout --signal=TERM 300 %s >/dev/null 2>&1 & sleep 1; echo launched"
              % (run, body, run, run))
    subprocess.run(_SSH + [launch], capture_output=True, timeout=30)
    deadline = time.time() + wait_s
    while time.time() < deadline:
        r = subprocess.run(_SSH + ["grep -q BODY-HALT %s 2>/dev/null && echo HALTED || true" % ser],
                           capture_output=True, timeout=20)
        if b"HALTED" in r.stdout:
            break
        time.sleep(2)
    r = subprocess.run(_SSH + ["cat %s 2>/dev/null; pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true" % ser],
                       capture_output=True, timeout=30)
    return r.stdout.decode(errors="replace").replace("\r", "")


def _serial(tag, plant=None):
    key = tag
    if key not in _CACHE:
        out, buildtxt = _build(tag)
        img = _mkdisk(tag, plant=plant)
        _CACHE[key] = (_boot(out, img, tag), buildtxt)
    return _CACHE[key]


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: B1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestB1LedgerGreenOnBody(unittest.TestCase):
    """test_ep14b runs GREEN per module on the body; the interpreter loads the whole-stdlib sealed image
    and imports gov-os from /rec/src by path AND by listing."""

    def test_module_runs_green_on_the_body(self):
        serial, _ = _serial("green")
        self.assertIn("BODY-HALT", serial, "the body must reach BODY-HALT")
        self.assertRegex(serial, r"LEDGER-RESULT OK ran=4 failures=0 errors=0 skipped=0",
                         "test_ep14b's 4 real tests run green on the body:\n" + serial[-2000:])
        self.assertIn("LEDGER-EXIT-STATUS: 0x00000000", serial, "the REAL exit status is 0 (green)")
        # each of the four real tests reported ok (the finder + listing + pack read + interpreter all held)
        for meth in ("test_no_module_op_definition_dicts_outside_the_founding",
                     "test_op_definition_reader_matches_the_pack",
                     "test_reader_raises_for_an_op_the_founding_does_not_define",
                     "test_the_absence_guard_can_fail"):
            self.assertRegex(serial, re.escape(meth) + r".*ok", meth + " did not report ok")

    def test_planted_assertion_reddens_the_real_run(self):
        serial, _ = _serial("plant", plant=WALK_MODULE)
        self.assertIn("BODY-HALT", serial, "even a red run reaches BODY-HALT (a completed run)")
        self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=5 failures=1 errors=0 skipped=0",
                         "the planted assertion makes the REAL run fail:\n" + serial[-2000:])
        self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
        self.assertIn("AssertionError: 'intact' != 'planted'", serial,
                      "the RED is a real AssertionError in the real module — no fabricated flag (L19)")
        # the four real tests still passed — only the planted one failed (a check that can fail)
        self.assertRegex(serial, r"test_op_definition_reader_matches_the_pack.*ok")

    def test_whole_stdlib_image_measured_under_the_cap(self):
        _, buildtxt = _serial("green")
        # build.sh's LEDGER staging prints the entry/file/byte count and the longest staged path (< 104)
        m = re.search(r"LEDGER STAGED (\d+) entries \((\d+) dirs, (\d+) files\), (\d+) bytes, longest path (\d+)",
                      buildtxt)
        self.assertIsNotNone(m, "the LEDGER staging line must report the image measurement:\n" + buildtxt)
        files, longest = int(m.group(3)), int(m.group(5))
        self.assertGreaterEqual(files, 1090, "the WHOLE shipped stdlib is staged (~1103 files), not a subset")
        self.assertLess(longest, 104, "the longest staged path is under the format cap SI_PATH_MAX (serve.c:72)")
        self.assertIn("sealed image seal sha256", buildtxt, "the whole image is digest-pinned (one digest)")


if __name__ == "__main__":
    unittest.main()
