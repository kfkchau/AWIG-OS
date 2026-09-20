# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel body names, at bring-up, BOTH sealed released artifacts it runs on — its own
# core image and the interpreter image — by hash in a row on its OWN append-only record disk, riding the
# existing record-pen act, and re-hashes each at every later boot as part of its boot self-check; a planted
# byte in either reds the boot) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability
# — it records and re-checks what the body runs on. The buildable part stops at the owner's one-way step
# (making the code-witness exception standing law, standing the body as the released performer — Q2), fenced
# off and NOT built here. Validate by building/reading, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7 P5 acceptance — THE SEALED INTERPRETER (design/54 §3 B6; §5 L18/L19/L2/L14/L9; §7 P5; countersign
archi :4622, RE-MINT on :4620 READING 2 — the core self-attest runs in the REAL boot pipeline, not a rig).

The body that boots with memory (P3b-1), a disk (P3b-2), a clock/interrupt/entropy path (P3b-3), the worker
enclosure/serve (P3b-4), its own NIC (P3b-6a) and the device-discovery rows (P7b) now NAMES BOTH sealed
released artifacts it runs on — its OWN core image and the INTERPRETER (the sealed image) — by hash in ONE
record-pen row EACH on its OWN record disk at bring-up, and RE-HASHES each against its row at every later
boot, in a NESTED qemu inside the pinned guest.

READING 2 (archi :4620/:4622): the CORE is staged by the REAL boot pipeline — build.sh produces out/core.img
(a verbatim copy of the released out/body.img) — so A1/A2 boot with THE SAME INVOCATION EVERY PRODUCTION BOOT
USES (-initrd sealed.img,core.img, both build.sh artifacts), never a test-fabricated module. The core is our
own kernel (L9, read whole and signed), hashed on the metal with sha256.c; the row pins the MEASURED hash and
every boot compares to that persisted row (the record is the reference — :4620 rider 1). The owner's Q2
one-way step (the interpreter's named L2 exception as standing law; standing the released performer) is fenced
off and NOT built (A4).

  A1  a fresh body image (disk + BOTH sealed artifacts as modules) records exactly TWO sealed-artifact rows
      — core and interpreter — each naming the artifact by its sha256, each an fs_record_append (record-pen),
      each read back from the record equal (L19). The recorded core hash equals sha256(body.img) and the
      recorded interpreter hash equals sha256(sealed.img), the real released bytes, hashed from OUTSIDE (the
      record is the reference; no self-embedded expected hash — :4615 rider 1). PLANT (able to fail): a
      bring-up whose CORE module is one byte off the released body.img records a row whose hash does NOT
      equal sha256(the released body.img) — the row-matches-the-artifact check reds.
  A2  at every later boot the body re-hashes each sealed artifact and compares to its row; a REAL planted
      byte in the CORE image OR the interpreter image (the PLANT_WORKER_IMAGE_TAMPER class — a real byte,
      never a flag; L19) reds the boot attestation, each way INDEPENDENTLY (core-tampered reds CORE with
      INTERP still PASS; interpreter-tampered reds INTERP with CORE still PASS); a clean reboot passes with
      no seal FAIL.
  A3  the two rows ride record-pen (ROWS-COUNT 0x0c — no 13th act kind); ATTESTED stays 88 (edit-in-place of
      an existing boot member, no new src/body file — no src/body/sha256.h created); no founding change.
  A4  the owner's one-way step is FENCED OFF, not taken: design/54 §5 L2 and §9 Q2 keep the code-witness
      exception as the OWNER's held step, NOT written into standing law, and the body is NOT stood as the
      released performer. PLANT: any such standing-switch in the settled-law register — caught.
  A5  the existing boot self-checks (record-pen, atomic-write-once, remove, body-read, founding-pack-read)
      and the interpreter's existing LOAD-time seal check stay GREEN with the two rows present; and every
      existing 0/1-module boot is INERT here — no sealed-artifact row, existing boots byte-unchanged.

A1/A2/A5(on-body) build+boot in the NESTED guest and skip when the pinned guest is not reachable over SSH;
A3/A4/A5(inertness of the guard surface) run in main. Register: an OS naming and re-checking the sealed
artifacts it runs on, on a disposable guest, described by function; validated by building/reading, never by
attack. Every kernel touch is the guest's nested qemu; the host kernel is never touched (L11 / EP-00 rule 9
/ charter §A21).
"""

import hashlib
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
sys.path.insert(0, SRC)

# ── the nested-guest bridge (on-body acceptances only) ──────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "<GUEST>"]
_WD = "/tmp/p5-remint-accept"                     # per-unit scratch (isolated name, host + guest; RE-MINT)
# -cpu qemu64 (SSE2, no AVX — the body keeps CR4.OSXSAVE clear); -m 256 == the PMM cap. The sealed
# interpreter image AND the core image are carried as multiboot MODULES, reached through the direct map.
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


def _seed():
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=180)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s/src" % (_WD, _WD)],
                   capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s/src" % _WD], input=tar.stdout,
                   capture_output=True, timeout=180, check=True)
    _SEEDED["done"] = True


def _guest_build():
    """INTERP build: build.sh stages the ONE sealed interpreter image from the REAL /usr/bin/python3.12 (the
    interpreter + its C library + loader-visible pieces + stdlib) AND — READING 2, archi :4620/:4622 — stages
    the RELEASED CORE image (out/core.img, a verbatim copy of the released out/body.img) so a REAL boot of the
    B6 configuration carries it as a second module. THE PIPELINE stages the core; this test NEVER fabricates
    it (no `cp` here — the retired rig did that). Produces out/body.img (the released body), out/sealed.img
    (the INTERPRETER) and out/core.img (the CORE). Returns (out, sha256(body.img), sha256(sealed.img),
    sha256(core.img)) read on the guest."""
    _seed()
    out = "%s/out" % _WD
    b = subprocess.run(_SSH + ["cd %s/src && INTERP=1 bash body/build.sh body %s" % (_WD, out)],
                       capture_output=True, timeout=400)
    if b.returncode != 0:
        raise AssertionError("guest INTERP build failed: " + b.stderr.decode(errors="replace"))
    txt = b.stdout.decode(errors="replace") + "\n" + b.stderr.decode(errors="replace")
    assert "sealed image seal sha256" in txt, "the sealed interpreter image was not staged: " + txt
    # READING 2: build.sh (the PIPELINE) MUST stage the core — this test does no `cp`. The echo names it.
    assert "core image seal sha256" in txt, \
        "build.sh did not stage the released core image (READING 2 — the pipeline stages the core): " + txt
    h = subprocess.run(_SSH + ["sha256sum %s/body.img %s/sealed.img %s/core.img" % (out, out, out)],
                       capture_output=True, timeout=60)
    lines = h.stdout.decode().split("\n")
    sha_body = lines[0].split()[0]
    sha_sealed = lines[1].split()[0]
    sha_core = lines[2].split()[0]
    return out, sha_body, sha_sealed, sha_core


def _mkdisk(tag):
    img = "%s/disk-%s.img" % (_WD, tag)
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s/src python3 src/body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=120)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _tamper(src_name, dst_name, off=1000):
    """Copy out/<src_name> to out/<dst_name> and flip ONE byte — a REAL planted byte in the artifact (L19),
    the PLANT_WORKER_IMAGE_TAMPER class. The -kernel body.img is untouched, so the body boots and its
    re-check catches the tampered MODULE."""
    out = "%s/out" % _WD
    cmd = ("python3 - <<'PY'\n"
           "b=bytearray(open('%s/%s','rb').read()); b[%d]^=0xff; open('%s/%s','wb').write(bytes(b))\n"
           "PY" % (out, src_name, off, out, dst_name))
    subprocess.run(_SSH + ["cd %s/out && cp %s %s && %s" % (_WD, src_name, dst_name, cmd)],
                   capture_output=True, timeout=30, check=True)


def _boot(out, img, modules, tag, marker, wait_s):
    """Boot the body in a NESTED qemu (the module files as -initrd, comma-joined; `img` an IDE disk),
    DETACHED (setsid) with serial to a file, then POLL until `marker` (BODY-HALT for a full boot, or
    SEALED-ARTIFACT-ACTS to read the re-check verdict before the slow interpreter floor). Serialized — one
    nested qemu at a time; pkill'd after the read."""
    ser = "%s/serial-%s.txt" % (_WD, tag)
    run = "%s/run-%s.sh" % (_WD, tag)
    initrd = ",".join("%s/%s" % (out, m) for m in modules)
    body = ("#!/bin/bash\npkill -9 -f 'qemu-system.*body.img' 2>/dev/null\nrm -f %s\n"
            "%s -serial file:%s -kernel %s/body.img -initrd \"%s\" "
            "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
            % (ser, _QEMU, ser, out, initrd, img))
    launch = ("cat > %s <<'EOS'\n%sEOS\nchmod +x %s; "
              "setsid timeout --signal=TERM %d %s >/dev/null 2>&1 & sleep 1; echo launched"
              % (run, body, run, wait_s + 30, run))
    subprocess.run(_SSH + [launch], capture_output=True, timeout=30)
    deadline = time.time() + wait_s
    while time.time() < deadline:
        r = subprocess.run(_SSH + ["grep -q '%s' %s 2>/dev/null && echo HIT || true" % (marker, ser)],
                           capture_output=True, timeout=20)
        if b"HIT" in r.stdout:
            break
        time.sleep(2)
    r = subprocess.run(_SSH + ["cat %s 2>/dev/null; pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true" % ser],
                       capture_output=True, timeout=30)
    return r.stdout.decode(errors="replace").replace("\r", "")


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── serial parsing ──────────────────────────────────────────────────────────────────────────────────
def _wrote_rows(serial):
    """{artifact: recorded sha256 hex} from the bring-up 'SEALED-ARTIFACT WROTE:' lines (as read back)."""
    out = {}
    for m in re.finditer(r"SEALED-ARTIFACT WROTE: sealed-artifact artifact=(\w+) sha256=([0-9a-f]{64})", serial):
        out[m.group(1)] = m.group(2)
    return out


def _recheck(serial, name):
    """('PASS'|'FAIL', row_hex, got_hex) for a re-check line, or (None, None, None)."""
    mp = re.search(r"SEALED-ARTIFACT %s: PASS \(sha256=([0-9a-f]{64})" % name, serial)
    if mp:
        return "PASS", mp.group(1), mp.group(1)
    mf = re.search(r"SEALED-ARTIFACT %s: FAIL \(row=([0-9a-f]{64}) got=([0-9a-f]{64})\)" % name, serial)
    if mf:
        return "FAIL", mf.group(1), mf.group(2)
    return None, None, None


# ── the on-body sequence (build once; bring-up once into a reference disk; reuse it for the re-checks) ──
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: on-body A1/A2/A5 need the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestSealedInterpreterOnBody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out, cls.sha_body, cls.sha_sealed, cls.sha_core = _guest_build()
        cls.d1 = _mkdisk("bringup")
        # BRING-UP through THE SAME INVOCATION EVERY PRODUCTION BOOT USES (READING 2): a fresh disk, BOTH
        # sealed artifacts as multiboot modules (mods[0]=sealed interpreter, mods[1]=core), BOTH staged by
        # build.sh (the pipeline), booted to BODY-HALT so the whole boot is green WITH the two rows present.
        cls.bringup = _boot(cls.out, cls.d1, ["sealed.img", "core.img"], "bringup", "BODY-HALT", 300)

    # ── A1 ──────────────────────────────────────────────────────────────────────────────────────────
    def test_a1_the_core_is_staged_by_the_pipeline_not_the_test(self):
        # READING 2 (archi :4620/:4622): the core image is staged by the REAL boot pipeline (build.sh), NOT
        # fabricated by this test. out/core.img is a build.sh artifact and a VERBATIM copy of the released
        # out/body.img — so the SAME production invocation every B6 boot uses carries the core (stop (f)
        # retired: no test-only hand-attached module). The staging moved OUT of the test into the pipeline.
        self.assertEqual(self.sha_core, self.sha_body,
                         "build.sh's core.img is a verbatim copy of the released body.img (the core the "
                         "body self-attests is its own released image, L9)")
        r = subprocess.run(_SSH + ["test -f %s/core.img && echo PRESENT || echo ABSENT" % self.out],
                           capture_output=True, timeout=30)
        self.assertIn(b"PRESENT", r.stdout, "build.sh (the pipeline) staged out/core.img — not the test")
        # build.sh's OWN echo named the core seal (the pipeline staged it; _guest_build asserts this too).
        self.assertTrue(self.sha_core and len(self.sha_core) == 64,
                        "the pipeline reported a real core image seal sha256 (READING 2)")

    def test_a1_two_rows_named_by_hash_each_matching_the_real_artifact_bytes(self):
        s = self.bringup
        self.assertIn("MULTIBOOT: OK", s, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertRegex(s, r"MODULE: count=0x0*2 ", "TWO modules: the sealed interpreter and the core image")
        self.assertIn("CORE-MODULE:", s, "the core image arrived as the second multiboot module")
        self.assertIn("DISK: OK", s, "the record disk is mounted (the rows land in the record)")
        rows = _wrote_rows(s)
        self.assertEqual(set(rows), {"core", "interpreter"},
                         "exactly one sealed-artifact row per artifact at bring-up:\n" + s[-1500:])
        self.assertIn("SEALED-ARTIFACT-COUNT: 0x00000002", s, "exactly two sealed-artifact rows")
        self.assertNotIn("[readback=FAIL]", s, "each sealed-artifact row read back from the record equal (L19)")
        self.assertNotIn("[append-FAIL]", s)
        self.assertIn("SEALED-ARTIFACT-ACTS: PASS", s, "bring-up records both rows and passes")
        # the record is the reference, hashed FROM OUTSIDE against the real released bytes (:4615 rider 1).
        self.assertEqual(rows["core"], self.sha_body,
                         "the recorded core hash equals sha256(the released body.img)")
        self.assertEqual(rows["interpreter"], self.sha_sealed,
                         "the recorded interpreter hash equals sha256(the released sealed.img)")

    def test_a1_plant_a_core_off_the_released_image_records_a_row_that_does_not_match(self):
        # PLANT (able to fail): bring up on a FRESH disk with a CORE module one byte off the released body.img.
        # The row honestly records what the body hashed on the metal — which then does NOT equal sha256(the
        # released body.img). The external row-matches-the-artifact check reds. A REAL byte, never a flag.
        _tamper("core.img", "core-a1plant.img", off=2000)
        d = _mkdisk("a1plant")
        s = _boot(self.out, d, ["sealed.img", "core-a1plant.img"], "a1plant", "SEALED-ARTIFACT-ACTS", 150)
        rows = _wrote_rows(s)
        self.assertIn("core", rows, "the bring-up still records a core row:\n" + s[-1200:])
        self.assertNotEqual(rows["core"], self.sha_body,
                            "a core one byte off the released image records a hash that does NOT match it "
                            "(the A1 row-matches-artifact check reds — a check that can fail)")
        # the interpreter row is untouched — the plant is confined to the core.
        self.assertEqual(rows.get("interpreter"), self.sha_sealed, "the interpreter row is unaffected")

    # ── A2 ──────────────────────────────────────────────────────────────────────────────────────────
    def _reboot(self, modules, tag, marker="SEALED-ARTIFACT-ACTS", wait_s=150):
        """Reboot a COPY of the bring-up disk (which carries the two rows) with the given modules."""
        d = "%s/disk-%s.img" % (_WD, tag)
        subprocess.run(_SSH + ["cp %s %s" % (self.d1, d)], capture_output=True, timeout=60, check=True)
        return _boot(self.out, d, modules, tag, marker, wait_s)

    def test_a2_clean_reboot_rechecks_both_and_passes(self):
        s = self._reboot(["sealed.img", "core.img"], "a2clean")
        c, crow, cgot = _recheck(s, "CORE")
        i, irow, igot = _recheck(s, "INTERP")
        self.assertEqual(c, "PASS", "a clean core re-check passes on reboot:\n" + s[-1200:])
        self.assertEqual(i, "PASS", "a clean interpreter re-check passes on reboot")
        self.assertEqual(crow, self.sha_body, "the core row is still the released body.img hash")
        self.assertEqual(irow, self.sha_sealed, "the interpreter row is still the released sealed.img hash")
        self.assertIn("SEALED-ARTIFACT-ACTS: PASS", s, "a clean reboot passes with no seal FAIL")
        self.assertNotIn("SEALED-ARTIFACT CORE: FAIL", s)
        self.assertNotIn("SEALED-ARTIFACT INTERP: FAIL", s)

    def test_a2_core_tampered_reds_the_boot_and_the_interpreter_still_passes(self):
        # a REAL planted byte in the CORE module (not the -kernel): the re-hash disagrees with the row.
        _tamper("core.img", "core-a2.img", off=3000)
        s = self._reboot(["sealed.img", "core-a2.img"], "a2core")
        c, crow, cgot = _recheck(s, "CORE")
        i, irow, igot = _recheck(s, "INTERP")
        self.assertEqual(c, "FAIL", "a tampered core reds the CORE re-check:\n" + s[-1200:])
        self.assertEqual(crow, self.sha_body, "the row still holds the untampered released core hash")
        self.assertNotEqual(cgot, crow, "the re-hash of the tampered core disagrees with its row")
        self.assertEqual(i, "PASS", "the interpreter re-check still passes — each way is INDEPENDENT")
        self.assertIn("SEALED-ARTIFACT-ACTS: FAIL", s, "a core tamper reds the boot attestation")

    def test_a2_interpreter_tampered_reds_the_boot_and_the_core_still_passes(self):
        # a REAL planted byte in the INTERPRETER (sealed) module: the re-hash disagrees with the row.
        _tamper("sealed.img", "sealed-a2.img", off=4000)
        s = self._reboot(["sealed-a2.img", "core.img"], "a2interp")
        c, crow, cgot = _recheck(s, "CORE")
        i, irow, igot = _recheck(s, "INTERP")
        self.assertEqual(i, "FAIL", "a tampered interpreter reds the INTERP re-check:\n" + s[-1200:])
        self.assertEqual(irow, self.sha_sealed, "the row still holds the untampered released interpreter hash")
        self.assertNotEqual(igot, irow, "the re-hash of the tampered interpreter disagrees with its row")
        self.assertEqual(c, "PASS", "the core re-check still passes — each way is INDEPENDENT")
        self.assertIn("SEALED-ARTIFACT-ACTS: FAIL", s, "an interpreter tamper reds the boot attestation")

    # ── A5 (on-body) ──────────────────────────────────────────────────────────────────────────────────
    def test_a5_existing_boot_self_checks_and_the_load_seal_stay_green_with_the_rows_present(self):
        s = self.bringup
        for line in ("CHECK RECORD-PEN: PASS", "CHECK ATOMIC-WRITE-ONCE: PASS", "CHECK REMOVE: PASS",
                     "CHECK BODY-READ: PASS", "CHECK FOUNDING-PACK-READ: PASS", "ACTS: PASS",
                     "DEVICE-DISCOVERY-ACTS: PASS"):
            self.assertIn(line, s, "existing boot self-check stays green WITH the two rows present: " + line)
        # the interpreter's existing LOAD-time seal check is unchanged (this plan ADDS a boot record-row
        # re-check, it never removes the load check).
        self.assertIn("FLOOR3C-SEAL: OK", s, "the interpreter's existing LOAD-time seal check is unchanged")
        self.assertRegex(s, r"ROWS-COUNT: 0*c\b", "the rows ride record-pen; ROWS-COUNT stays twelve (A3)")
        self.assertIn("BODY-HALT", s, "the whole boot completes green with the two sealed-artifact rows present")

    def test_a5_a_one_module_boot_is_inert_no_sealed_artifact_row(self):
        # every EXISTING boot (0 or 1 module — no core image) leaves the emitter inert: no sealed-artifact
        # row, existing boots byte-unchanged. Boot the interpreter alone (as P3b-4c does), no core module.
        d = _mkdisk("inert")
        s = _boot(self.out, d, ["sealed.img"], "inert", "BODY-HALT", 300)
        self.assertRegex(s, r"MODULE: count=0x0*1 ", "ONE module only — the sealed interpreter, no core")
        self.assertNotIn("CORE-MODULE:", s, "no core module is captured")
        self.assertNotIn("SEALED-ARTIFACT", s, "the emitter is INERT with no core module — no row, no re-check")
        self.assertIn("CHECK RECORD-PEN: PASS", s, "existing boot self-checks are unchanged on a 1-module boot")
        self.assertIn("BODY-HALT", s, "the existing 1-module boot is unchanged and completes")


# ── A3 / A4 (main — the guard surface, no guest) ─────────────────────────────────────────────────────
class TestFenceHeldInMain(unittest.TestCase):
    def test_a3_rows_act_count_stays_twelve(self):
        with open(os.path.join(BODY, "rows_digest.h")) as _f:
            rd = _f.read()
        self.assertRegex(rd, r"#define\s+ROWS_ACT_COUNT\s+12\b",
                         "the sealed-artifact rows ride record-pen — no 13th act kind")

    def test_a3_attested_stays_88_and_no_new_src_body_header(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                         "no new src/body member — the interface is an extern, not a new file (:4615 rider 2)")
        self.assertFalse(os.path.exists(os.path.join(BODY, "sha256.h")),
                         "src/body/sha256.h is NOT created — the fence name that does not exist (:4615 rider 2)")
        # the emitter reaches the primitive by an extern declaration in the consuming member (no new header).
        dc = open(os.path.join(BODY, "diskcheck.c")).read()
        self.assertIn("extern void sha256(", dc,
                      "sha256 is reached by an extern in diskcheck.c (the enclosure.c form) — no new header")

    def test_a3_the_rows_are_record_pen_appends_no_founding_or_new_act(self):
        with open(os.path.join(BODY, "diskcheck.c")) as _f:
            dc = _f.read()
        # the sealed-artifact rows are fs_record_append (record-pen), never a blob and never a new act kind.
        self.assertIn("fs_record_append(buf", dc, "the sealed-artifact row is a record-pen append")
        self.assertNotIn("fs_blob_write_once(\"core", dc, "the row is NOT a write-once blob")

    @unittest.skipUnless(
        os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design/54-CAMPAIGN-7-SELF-HOSTING.md")),
        "SKIP PRIVATE-SOURCE: needs design/54-CAMPAIGN-7-SELF-HOSTING.md (absent in the render)")
    def test_a4_the_owner_one_way_step_is_fenced_off_not_taken(self):
        with open(os.path.join(ROOT, "design", "54-CAMPAIGN-7-SELF-HOSTING.md")) as _f:
            d54 = _f.read()
        # §9 Q2 keeps the interpreter as the OWNER's one-way door, a HELD step — not resolved into standing law.
        self.assertRegex(d54, r"Q2 THE INTERPRETER \(one-way door, the owner's\)",
                         "Q2 stays the owner's one-way door (the named code-witness exception is NOT standing law)")
        self.assertIn("His word at P5's held step", d54,
                      "P5's held owner step is still HELD — not taken by this build (A4)")
        # §5 L2 keeps the composite two-witness form; the exception is NOT written as standing law here.
        self.assertRegex(d54, r"\[L2\] Two witness classes: witness-the-code",
                         "L2 keeps its composite two-witness form (the exception stays the owner's, not standing)")


if __name__ == "__main__":
    unittest.main()
