# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel body serving its OWN append-only record pen at CALLER-NAMED paths under a
# per-world namespace, backed by its bespoke on-disk format — as in the seL4/gVisor/Fuchsia and osdev
# literature). NON-GOAL: no offensive capability; the body serves the seam's OWN record-pen act
# (create-on-first-stroke, extend-at-the-tail) at caller-named names and refuses every other write class
# by name — O_TRUNC (overwrite-in-place) stays refused (R1), there is no general writable filesystem
# (L21). Validated by building/reading a real booted body, never by attack (governance-work-method).
# Every kernel touch is the guest's nested qemu (L11 / EP-00 rule 9 / §A21). Full: SCOPE-STATEMENT.md.
"""C7 P3b-5a-iv acceptance — THE RECORD PEN AT CALLER-NAMED NAMES (design/54 §7 P3b-5a-iv; archi
countersign :4324; 5a's OWN completion, not a new act).

The store's SOLE appender is host_seam.open_append = path.open("a") (store.py:1010) — O_WRONLY|O_CREAT|
O_APPEND on a CALLER-NAMED record. Before this slice serve.c served the pen only three ways that miss it
(the fixed-record append :488, the write-once create :849, the present-record append :856), so a fresh
caller-named record fell between two served acts and answered ENOENT — blocking ~95 of 5b's record-writing
modules. This slice serves the create-OR-append on a caller-named record under /rec/<world>/…, proven by
the REAL store's own open_append on a fresh world record (L19), never a shaped call.

  A1  THE FIRST STROKE CREATES THE RECORD. O_CREAT|O_APPEND on an ABSENT caller-named record creates it
      and appends; the bytes read back equal what was written. PLANT (PLANT_NREC_NO_CREATE_APPEND): the
      pre-5a-iv body — the real open_append on a fresh world record answers ENOENT (FileNotFoundError) ->
      the on-body run reds.
  A2  LATER STROKES APPEND. Each further open("a") on the PRESENT record EXTENDS; the read-back equals ALL
      the bytes written, in order. PLANT (PLANT_NREC_APPEND_OVERWRITES): a stroke overwrites at offset 0
      rather than extending -> the read-back-all check reds.
  A3  OVERWRITE-IN-PLACE STAYS REFUSED (R1). O_TRUNC (open("w")) on a PRESENT record is refused by name —
      the append-only record is never truncated-and-rewritten; the bytes STAND. PLANT
      (PLANT_NREC_TRUNC_SERVED): the truncate is served -> the R1-refusal check reds.
  A4  THE PROPERTIES HOLD, THE PINS RE-POINT, THE SUITE STAYS GREEN. The append-only / write-once /
      one-writer PROPERTIES are unchanged (a create-append never becomes an overwrite; write-once and the
      *.lock one-writer act untouched, L14); ATTESTED unchanged (edit-in-place), ACT_KINDS 12, founding
      unchanged; the 5a-i/5a-ii/5a-iii + P3b-2 regressions run green on the 5a-iv body (the off-body
      harness re-runs them at close).
  A5  GUEST-ONLY, ATTESTED, ACT_KINDS 12, PRODUCTION HELD. Every build/boot/run is the nested qemu's; the
      record disk is NOT a general writable filesystem (O_TRUNC/other write classes refused by name); the
      body is NOT stood as the production performer; git-revertible; NO founding.

THE WRONG REFERENCE THIS SLICE REFUSES: the record pen at caller-named names is NOT the write-once create
(O_CREAT|O_EXCL, :849) and NOT a general writable file — O_TRUNC is refused by name (R1), only the record
name class under /rec/ is served (L21). The record pen GROWS to caller-named names; the append-only
property HOLDS (L14). Proven by the REAL store's open_append, never a shaped call (L19).

This file is DUAL-ROLE. On the host it is the off-body harness (build the body with each plant, boot it
in a nested qemu, and read the REAL on-body run's report). On the body — loaded as the ledger runmod
(GOVOS_RUNMOD), sys.path carries /rec/src — only TestRecordPenOnBody exists and runs the real store's
open_append on a fresh world record; the harness/static classes are not even defined there, so the body's
LEDGER-RESULT is exactly ran=3 for the three record-pen behaviours.
"""

import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
sys.path.insert(0, SRC)

# The body ledger run inserts /rec/src on sys.path (enclosure.c g_ledger_script); the host harness never
# does. This is how the ONE file tells which side it is on, without a subprocess probe on the body.
_ON_BODY = any(p == "/rec/src" for p in sys.path)

THIS_MOD = "test_c7_p3b_5a_iv_record_pen_caller_named"


# ══ THE ON-BODY PROOF (A1/A2/A3): the REAL store's open_append on a fresh world record (L19) ═══════════
# Runs ONLY on the body (loaded as the ledger runmod). Each behaviour is driven by the real appender
# host_seam.open_append (path.open("a")) and the real reader open_read (path.open("r")) on a fresh
# mkdtemp-nested world record under /rec/tmp — exactly the pattern the store's ~95 record-writers use.
@unittest.skipUnless(_ON_BODY, "SKIP BODY-BOOT: the record-pen proof runs on the body (the real store's open_append)")
class TestRecordPenOnBody(unittest.TestCase):
    def _fresh_record(self):
        import tempfile
        from pathlib import Path
        world = tempfile.mkdtemp()                       # /rec/tmp/tmpXXXX — a fresh caller-named world
        return Path(world) / "record.jsonl"

    def test_a1_first_stroke_creates_the_record_and_reads_back(self):
        from bridge.host_seam import host
        rec = self._fresh_record()
        with host().open_append(rec) as fh:              # path.open("a") — the store's SOLE appender (store.py:1010)
            fh.write("row-0\n")
        with host().open_read(rec) as fh:
            self.assertEqual(fh.read(), "row-0\n",
                             "the first stroke creates the caller-named record and reads back equal")

    def test_a2_later_strokes_append_all_in_order(self):
        from bridge.host_seam import host
        rec = self._fresh_record()
        for line in ("row-0\n", "row-1\n", "row-2\n"):   # three separate opens of the PRESENT record
            with host().open_append(rec) as fh:
                fh.write(line)
        with host().open_read(rec) as fh:
            self.assertEqual(fh.read(), "row-0\nrow-1\nrow-2\n",
                             "later strokes EXTEND — the read-back is ALL bytes, in order")

    def test_a3_overwrite_in_place_is_refused(self):
        from bridge.host_seam import host
        rec = self._fresh_record()
        with host().open_append(rec) as fh:
            fh.write("row-0\n")
        # O_TRUNC (open("w")) on a PRESENT record is overwrite-in-place — refused by name (R1). The
        # append-only record is never truncated-and-rewritten.
        with self.assertRaises(OSError):
            open(str(rec), "w")
        with host().open_read(rec) as fh:                # the refused truncate performed nothing
            self.assertEqual(fh.read(), "row-0\n", "the refused truncate left the record intact")


if not _ON_BODY:
    # ══ THE OFF-BODY HARNESS + THE SOURCE/STATIC CHECKS (host only) ═══════════════════════════════════
    import csv  # noqa: F401  (kept for parity with sibling suites; not used on the body)

    _KEY = "<HOME><KEYPATH>"
    _SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
            "<GUEST>"]
    _WD = "/tmp/p3b5aiv-accept"
    _QEMU = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc"

    def _read(rel):
        with open(os.path.join(BODY, rel), encoding="utf-8") as f:
            return f.read()

    def _guest_reachable():
        import subprocess
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
        import subprocess
        if _SEEDED["done"]:
            return
        tar = subprocess.run(["tar", "-czf", "-", "-C", ROOT, "src", "tests"], capture_output=True, timeout=180)
        subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s" % (_WD, _WD)], capture_output=True, timeout=30, check=True)
        subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True, timeout=180, check=True)
        _SEEDED["done"] = True

    def _build(tag, fault=""):
        """LEDGER build (the whole-stdlib sealed image + GATE_ON_BODY); optional -D plant via the FAULT arg."""
        import subprocess
        _seed()
        out = "%s/out-%s" % (_WD, tag)
        b = subprocess.run(_SSH + ["cd %s/src && LEDGER=1 bash body/build.sh body %s %s" % (_WD, out, fault)],
                           capture_output=True, timeout=300)
        if b.returncode != 0:
            raise AssertionError("guest LEDGER build failed (%s): %s" % (fault, b.stderr.decode(errors="replace")))
        return out

    def _mkdisk(tag):
        import subprocess
        img = "%s/disk-%s.img" % (_WD, tag)
        m = subprocess.run(
            _SSH + ["cd %s && GOVOS_TREE=1 GOVOS_RUNMOD=%s PYTHONPATH=%s/src python3 src/body/mkdisk.py %s"
                    % (_WD, THIS_MOD, _WD, img)],
            capture_output=True, timeout=120)
        if m.returncode != 0:
            raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
        return img

    def _boot(out, img, tag, wait_s=180):
        """Boot the body in a NESTED qemu (sealed image -initrd, `img` as an IDE disk), DETACHED (setsid)
        with serial to a file, then POLL the file until BODY-HALT — the reliable pattern (5b-i). SERIALIZED:
        one nested qemu at a time; the body halts (never reboots), so it is pkill'd after the read."""
        import subprocess
        import time
        ser = "%s/serial-%s.txt" % (_WD, tag)
        run = "%s/run-%s.sh" % (_WD, tag)
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

    def _serial(tag, fault=""):
        if tag not in _CACHE:
            out = _build(tag, fault=fault)
            img = _mkdisk(tag)
            _CACHE[tag] = _boot(out, img, tag)
        return _CACHE[tag]

    def tearDownModule():
        import subprocess
        if GUEST:
            subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                           capture_output=True, timeout=20)

    # ── clean boot: A1/A2/A3 all pass on the body (the real store's open_append) ─────────────────────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
    class TestCleanBootRecordPenGreen(unittest.TestCase):
        def test_the_three_record_pen_behaviours_run_green_on_the_body(self):
            serial = _serial("clean")
            self.assertIn("BODY-HALT", serial, "the body must reach BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT OK ran=3 failures=0 errors=0 skipped=0",
                             "the three record-pen behaviours run green on the body:\n" + serial[-2000:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000000", serial, "the REAL exit status is 0 (green)")
            for meth in ("test_a1_first_stroke_creates_the_record_and_reads_back",
                         "test_a2_later_strokes_append_all_in_order",
                         "test_a3_overwrite_in_place_is_refused"):
                self.assertRegex(serial, re.escape(meth) + r".*ok", meth + " did not report ok")

    # ── A1 plant: the pre-5a-iv body — create-append unserved -> the real open_append reds (ENOENT) ──
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA1PlantNoCreateAppendReds(unittest.TestCase):
        def test_unserved_create_append_reddens_the_real_open_append(self):
            serial = _serial("nocreate", fault="PLANT_NREC_NO_CREATE_APPEND")
            self.assertIn("BODY-HALT", serial, "even a red run reaches BODY-HALT (a completed run)")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3",
                             "the pre-5a-iv body reds the record-pen run:\n" + serial[-2000:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertIn("FileNotFoundError", serial,
                          "the RED is the REAL store's open_append answering ENOENT — no fabricated flag (L19)")

    # ── A2 plant: a stroke overwrites rather than extends -> the read-back-all check reds ────────────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA2PlantOverwriteReds(unittest.TestCase):
        def test_overwriting_stroke_reddens_read_back_all(self):
            serial = _serial("overwrite", fault="PLANT_NREC_APPEND_OVERWRITES")
            self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3 failures=1",
                             "the overwriting stroke reds exactly the read-back-all check:\n" + serial[-2000:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertRegex(serial, r"test_a2_later_strokes_append_all_in_order.*(FAIL|ERROR)",
                             "A2 (later strokes append in order) is the reddened behaviour")
            self.assertRegex(serial, r"test_a1_first_stroke_creates_the_record_and_reads_back.*ok",
                             "A1 still passes — a single stroke is unaffected (the check can fail, precisely)")

    # ── A3 plant: O_TRUNC served on a present record -> the R1-refusal check reds ────────────────────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA3PlantTruncServedReds(unittest.TestCase):
        def test_served_truncate_reddens_the_r1_refusal(self):
            serial = _serial("trunc", fault="PLANT_NREC_TRUNC_SERVED")
            self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3 failures=1",
                             "serving the truncate reds exactly the R1-refusal check:\n" + serial[-2000:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertRegex(serial, r"test_a3_overwrite_in_place_is_refused.*(FAIL|ERROR)",
                             "A3 (overwrite-in-place refused) is the reddened behaviour")
            self.assertRegex(serial, r"test_a1_first_stroke_creates_the_record_and_reads_back.*ok",
                             "A1 still passes — the append path is unaffected (the check can fail, precisely)")

    # ── A4/A5 — source shape, properties, attestation, act-kinds, production held (main; no guest) ───
    class TestSourceShapeA4A5(unittest.TestCase):
        def test_a4_attested_unchanged_act_kinds_12_founding_unchanged(self):
            import json
            from kernel import attestation
            from bridge.host_seam import ACT_KINDS
            self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                             "5a-iv edits members in place (serve.c/serve.h/bodyfs.c/disk.h) — no new .c")
            for rel in ("body/serve.c", "body/serve.h", "body/bodyfs.c", "body/disk.h"):
                self.assertIn(rel, attestation.ATTESTED_MEMBERS, "%s is an attested member (edit-in-place)" % rel)
            names = sorted(n for n in os.listdir(BODY)
                           if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))
            self.assertEqual(len(names), 31, "src/body is 31 files (5a-iv adds none): %r" % names)
            self.assertEqual(len(ACT_KINDS), 12, "no new act kind — a served shape is not a kind (archi :4324)")
            pack = os.path.join(SRC, "founding", "founding-pack.json")
            with open(pack) as f:
                self.assertEqual(json.load(f)["founding_version"], "1.55.0", "no founding on a body slice")

        def test_a4_the_record_pen_primitive_and_type_exist(self):
            dh = _read("disk.h")
            self.assertIn("#define FT_NREC", dh, "a caller-named append-only record type is declared")
            self.assertIn("int  fs_nrec_append(const char *name, const uint8_t *payload, uint32_t n, "
                          "uint32_t *out_start_sector)", dh, "the record-pen-at-caller-named primitive is declared")
            bf = _read("bodyfs.c")
            self.assertIn("int fs_nrec_append(const char *name", bf, "the primitive is defined")
            # append-only BY CONSTRUCTION: the tail is off == e->length (never an overwrite offset).
            self.assertIn("uint32_t off = e->length;", bf, "the append lands at the tail (append-only)")
            self.assertIn("PLANT_NREC_APPEND_OVERWRITES", bf,
                          "the overwrite plant exists (a check that cannot fail is not a check)")

        def test_a5_serve_dispatch_and_the_three_plants_exist(self):
            sv = _read("serve.c")
            self.assertIn("static uint64_t serve_openat_fs(uint64_t pathptr, uint64_t flags)", sv,
                          "the openat resolver takes the open flags (the create-append needs them)")
            self.assertIn("#define SI_FD_NREC", sv, "the caller-named record write fd kind exists")
            self.assertIn("if (flags & O_TRUNC)", sv, "O_TRUNC (overwrite-in-place) is handled by name (R1)")
            self.assertIn("if (flags & O_APPEND)", sv, "the record pen (create-on-absent, then append) is served")
            for plant in ("PLANT_NREC_NO_CREATE_APPEND", "PLANT_NREC_TRUNC_SERVED"):
                self.assertIn(plant, sv, "%s plant exists in serve.c (a check that cannot fail is not a check)" % plant)
            sh = _read("serve.h")
            self.assertIn("#define O_CREAT", sh, "the create flag is declared")
            self.assertIn("#define O_WRONLY", sh, "the write-only flag is declared")

        def test_a5_no_host_kernel_load_in_the_edited_body_files(self):
            for rel in ("serve.c", "serve.h", "bodyfs.c", "disk.h"):
                text = _read(rel)
                for tok in ("insmod", "modprobe"):
                    self.assertNotIn(tok, text, "src/body/%s must not load a host kernel module (L11)" % rel)
            # the near-miss control (§A64): the scan CAN fail.
            self.assertIn("insmod", "insmod /lib/modules/x.ko")

        def test_a5_the_body_is_not_stood_as_the_production_performer(self):
            # a source-level control: no module above the seam imports the body as the production performer.
            pats = ("from body import", "import body.", "from body.")
            hits = []
            for root, _dirs, files in os.walk(SRC):
                ar = os.path.abspath(root)
                if ar.startswith(os.path.abspath(BODY)) or ar.startswith(os.path.abspath(os.path.join(SRC, "founding"))):
                    continue
                for name in files:
                    if not name.endswith(".py"):
                        continue
                    with open(os.path.join(root, name), encoding="utf-8", errors="replace") as f:
                        text = f.read()
                    for pat in pats:
                        if pat in text:
                            hits.append((os.path.relpath(os.path.join(root, name), SRC), pat))
            self.assertEqual(hits, [], "a module above the seam stands the body as the production performer")


if __name__ == "__main__":
    unittest.main()
