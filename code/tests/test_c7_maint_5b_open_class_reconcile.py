# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel body serving the ordinary create-empty-then-append idiom on its own record disk:
#  a program that opens a name for write on an absent name — creating it empty — closes it, then re-opens
#  it to append, exactly as Linux serves it, while the store's durable temp-then-swap, whose real caller
#  RENAMES the staging file over its final, stays distinct and unbroken). NON-GOAL: no offensive capability;
#  the body serves the seam's OWN record-disk acts in their real shapes and refuses every other write class
#  by name (O_TRUNC on a present record stays refused, R1; no general writable filesystem, L21; the adoption
#  is under /rec/tmp only). Validated by building/reading a real booted body, never by attack
#  (governance-work-method). Every kernel touch is the guest's nested qemu (L11 / EP-00 rule 9 / §A21).
#  Full: SCOPE-STATEMENT.md.
"""C7-MAINT-5B-OPEN-CLASS-RECONCILE acceptance — THE CREATE-EMPTY-THEN-APPEND IDIOM SERVED FAITHFULLY
(planning/exec/C7-MAINT-5B-OPEN-CLASS-RECONCILE.md; archi countersign :4431; 5a-v's open-class family, NOT
a new act — ACT_KINDS stays 12, no founding, no on-disk byte-format change).

THE ROOT (measured on the body, mgr's ep28e re-scope): test_ep28e / test_ep28e_w3 setUp does
open(rec, "w").close() before genesis. The body maps O_TRUNC-on-an-absent-name to the durable-write STAGING
class (FT_DURABLE, serve.c O_TRUNC branch / bodyfs.c fs_durable_write, the 5a-v two-acts rule). Then genesis's
store open("a") reaches fs_nrec_append's foreign-class guard (bodyfs.c, e->type != FT_NREC), which refused
the present FT_DURABLE as a FOREIGN CLASS and answered EPERM — though the superblock at the halt read the disk
72% empty. Linux appends to any file a program created; the body refused because it TYPED the empty file as a
staging file. It is an open-class fidelity gap, NOT a capacity limit.

THE FIX (serve.c + bodyfs.c, edit-in-place): an UNSWAPPED, zero-length FT_DURABLE (a staging file created
empty by O_TRUNC-on-an-absent-name, never written and never renamed) is ADOPTED into the record pen
(reconciled to FT_NREC) when it is opened for APPEND, so the append succeeds. The adoption is scoped to
/rec/tmp (L21/A3); the durable temp-then-swap (host_seam.write_file_durably — a staging file RENAMED over its
final, never opened for append) never reaches fs_nrec_append and stays DISTINCT and unbroken (A2).

  A1  CREATE-EMPTY-THEN-APPEND IS SERVED. test_ep28e (ran=9) and test_ep28e_w3 (ran=17) run GREEN on the
      body — their setUp's open("w").close() + genesis open("a") now succeeds. PLANT: PLANT_RECONCILE_REFUSED
      restores the foreign-class refusal -> the store's open("a") reds by a REAL EPERM (L19).
  A2  THE DURABLE TEMP-THEN-SWAP STAYS DISTINCT AND UNBROKEN. test_c7_p3b_5a_v_seam_performers (ran=3, the
      module that exercises write_file_durably) stays GREEN on the body. PLANT: PLANT_RECONCILE_BREAKS_SWAP
      models an over-broad reconcile that mis-types the staging file (a renamed staging file mis-typed) ->
      the FT_DURABLE-only swap refuses -> the real write_file_durably reds (L19).
  A3  L21 AND THE APPEND-ONLY LAW HELD. The adoption is under /rec/tmp ONLY; a present FT_DURABLE opened
      O_APPEND OUTSIDE /rec/tmp keeps the foreign-class refusal; O_TRUNC on a PRESENT record stays refused
      (R1). PLANT: PLANT_RECONCILE_OUTSIDE_TMP drops the /rec/tmp scope -> the outside-/rec/tmp adoption is
      served -> this module's outside-tmp refusal check reds (L19).
  A4  NOTHING ELSE MOVES. ATTESTED unchanged (serve.c/bodyfs.c edit-in-place, no new member); ACT_KINDS 12
      (ROWS-COUNT 0x0000000c on every serial); founding unchanged; no on-disk byte-format change (BODYFS02
      stays v2; FT_NREC / FT_DURABLE are existing kinds). Asserted by reading the shipped source, git-checked
      in the close.

THE WRONG REFERENCE THIS SLICE REFUSES (stop-condition b / A2): the create-empty-then-append idiom and the
durable temp-then-swap SHARE their first act (O_TRUNC-on-an-absent-name -> FT_DURABLE). They are told apart by
the SECOND act — an APPEND adopts (fs_nrec_append), a RENAME swaps (fs_swap_rename) — and the temp-then-swap
never opens its staging file for append, so it never reaches the adoption. Adopting ALL FT_DURABLE, or
adopting a NON-empty staging file, or adopting outside /rec/tmp would collapse that distinction; the shipped
fix adopts only an unswapped, zero-length FT_DURABLE under /rec/tmp.

DUAL-ROLE. On the body (loaded as the ledger runmod, GOVOS_RUNMOD; sys.path carries /rec/src, tempfile lives
under /rec/tmp) only TestOpenClassReconcileOnBody runs, driving the real open acts — the body's LEDGER-RESULT
is ran=3. On the host it is the off-body harness (build with each plant, boot in a nested qemu, read the real
on-body run) plus the A4 source-shape checks.
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

THIS_MOD = "test_c7_maint_5b_open_class_reconcile"


# ══ THE ON-BODY PROOF (A1/A3): the real open acts on the body's own record disk ════════════════════════
# Runs ONLY on the body (loaded as the ledger runmod). tempfile.mkdtemp lands under /rec/tmp (the ledger
# bootstrap sets tempfile.tempdir), so a mkdtemp path is a caller-named /rec/tmp path — exactly the store's.
@unittest.skipUnless(_ON_BODY, "the open-class proof runs on the body (the real record-disk open acts)")
class TestOpenClassReconcileOnBody(unittest.TestCase):
    def test_a1_create_empty_then_append_is_served(self):
        """The create-empty-then-append idiom: create EMPTY (O_TRUNC-on-absent), close, re-open for append,
        append twice, read back the exact concatenation. This is what test_ep28e/w3 setUp does through the
        store; here it is the raw open acts, unmediated, so the adoption is proven directly (L19)."""
        import tempfile
        rec = os.path.join(tempfile.mkdtemp(), "rec.jsonl")   # /rec/tmp/tmpXXXX/rec.jsonl — under /rec/tmp
        open(rec, "w").close()                                # O_TRUNC on an absent name -> an EMPTY FT_DURABLE
        with open(rec, "a", encoding="utf-8") as f:           # adopted into the record pen (FT_NREC)
            f.write("row-one\n")
        with open(rec, "a", encoding="utf-8") as f:           # a later stroke extends the same record
            f.write("row-two\n")
        with open(rec, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "row-one\nrow-two\n",
                             "the create-empty-then-append idiom did not read back the exact appends")

    def test_a3_adoption_refused_outside_rec_tmp(self):
        """L21/A3: the adoption is under /rec/tmp ONLY. A zero-length FT_DURABLE created OUTSIDE /rec/tmp and
        opened for append keeps the foreign-class refusal (EPERM). Under PLANT_RECONCILE_OUTSIDE_TMP the
        /rec/tmp scope is dropped and the append is served, so this check reds."""
        probe = "/rec/reconcile_probe_outside_tmp"            # directly under /rec/, NOT under /rec/tmp
        open(probe, "w").close()                              # O_TRUNC on an absent name -> an EMPTY FT_DURABLE
        with self.assertRaises(OSError,
                               msg="a present FT_DURABLE opened for append OUTSIDE /rec/tmp was adopted; the "
                                   "/rec/tmp scope (L21/A3) did not hold"):
            open(probe, "a", encoding="utf-8").close()

    def test_a3_otrunc_on_a_present_record_stays_refused(self):
        """R1 / append-only law: once a record exists, O_TRUNC (open('w')) on it is refused — the append-only
        record is never truncated-and-rewritten. Held under /rec/tmp, where the record pen lives."""
        import tempfile
        rec = os.path.join(tempfile.mkdtemp(), "rec2.jsonl")
        with open(rec, "a", encoding="utf-8") as f:           # first append creates the record (FT_NREC)
            f.write("seed\n")
        with self.assertRaises(OSError,
                               msg="O_TRUNC on a PRESENT record was served; R1 (append-only) did not hold"):
            open(rec, "w", encoding="utf-8").close()


# ══ THE OFF-BODY HARNESS + A4 SOURCE-SHAPE CHECKS (host only) ══════════════════════════════════════════
if not _ON_BODY:
    import subprocess

    _KEY = "<HOME><KEYPATH>"
    _SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
            "<GUEST>"]
    _WD = "/tmp/c7-5b-recon-test"
    _QEMU = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc"

    def _read(rel):
        with open(os.path.join(BODY, rel), encoding="utf-8") as f:
            return f.read()

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

    def _build(tag, fault=""):
        """LEDGER build (the whole-stdlib sealed image + GATE_ON_BODY); optional -D plant via the FAULT arg."""
        _seed()
        out = "%s/out-%s" % (_WD, tag)
        b = subprocess.run(_SSH + ["cd %s/src && LEDGER=1 bash body/build.sh body %s %s" % (_WD, out, fault)],
                           capture_output=True, timeout=520)
        if b.returncode != 0:
            raise AssertionError("guest LEDGER build failed (%s): %s" % (fault, b.stderr.decode(errors="replace")))
        return out

    def _mkdisk(tag, mod):
        img = "%s/disk-%s-%s.img" % (_WD, tag, mod)
        m = subprocess.run(
            _SSH + ["cd %s && GOVOS_TREE=1 GOVOS_RUNMOD=%s PYTHONPATH=%s/src python3 src/body/mkdisk.py %s"
                    % (_WD, mod, _WD, img)],
            capture_output=True, timeout=120)
        if m.returncode != 0:
            raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
        return img

    def _boot(out, img, tag, mod, wait_s=240):
        """Boot the body in a NESTED qemu (sealed image -initrd, `img` as an IDE disk), DETACHED with serial
        to a file, then POLL until BODY-HALT. SERIALIZED: one nested qemu at a time; the body halts (never
        reboots), so it is pkill'd after the read (L11 / one-at-a-time)."""
        import time
        ser = "%s/serial-%s-%s.txt" % (_WD, tag, mod)
        run = "%s/run-%s-%s.sh" % (_WD, tag, mod)
        body = ("#!/bin/bash\npkill -9 -f 'qemu-system.*body.img' 2>/dev/null\nrm -f %s\n"
                "%s -serial file:%s -kernel %s/body.img -initrd %s/sealed.img "
                "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
                % (ser, _QEMU, ser, out, out, img))
        launch = ("cat > %s <<'EOS'\n%sEOS\nchmod +x %s; "
                  "setsid timeout --signal=TERM 320 %s >/dev/null 2>&1 & sleep 1; echo launched"
                  % (run, body, run, run))
        subprocess.run(_SSH + [launch], capture_output=True, timeout=30)
        deadline = time.time() + wait_s
        while time.time() < deadline:
            r = subprocess.run(_SSH + ["grep -q BODY-HALT %s 2>/dev/null && echo HALTED || true" % ser],
                               capture_output=True, timeout=20)
            if b"HALTED" in r.stdout:
                break
            time.sleep(2)
        r = subprocess.run(_SSH + ["cat %s 2>/dev/null; pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; "
                                   "rm -f %s; true" % (ser, img)], capture_output=True, timeout=30)
        return r.stdout.decode(errors="replace").replace("\r", "")

    def _serial(tag, mod, fault=""):
        key = (tag, mod)
        if key not in _CACHE:
            out = _build(tag, fault=fault)
            img = _mkdisk(tag, mod)
            _CACHE[key] = _boot(out, img, tag, mod)
        return _CACHE[key]

    def tearDownModule():
        if GUEST:
            subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                           capture_output=True, timeout=20)

    # ── A1/A2 GREEN + A3 GREEN on the fixed body (the shipped reconcile) ──────────────────────────────
    @unittest.skipUnless(GUEST, "the body run needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
    class TestCleanBootGreen(unittest.TestCase):
        def test_a1_test_ep28e_green_on_the_body(self):
            s = _serial("clean", "test_ep28e")
            self.assertRegex(s, r"LEDGER-RESULT OK ran=9 failures=0 errors=0",
                             "test_ep28e did not run green on the body:\n" + s)
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000000", s)

        def test_a1_test_ep28e_w3_green_on_the_body(self):
            s = _serial("clean", "test_ep28e_w3")
            self.assertRegex(s, r"LEDGER-RESULT OK ran=17 failures=0 errors=0",
                             "test_ep28e_w3 did not run green on the body:\n" + s)
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000000", s)

        def test_a2_durable_temp_then_swap_green_on_the_body(self):
            s = _serial("clean", "test_c7_p3b_5a_v_seam_performers")
            self.assertRegex(s, r"LEDGER-RESULT OK ran=3 failures=0 errors=0",
                             "the durable temp-then-swap did not stay green on the body:\n" + s)

        def test_a1a3_this_module_green_on_the_body(self):
            s = _serial("clean", THIS_MOD)
            self.assertRegex(s, r"LEDGER-RESULT OK ran=3 failures=0 errors=0",
                             "the create-empty-then-append + /rec/tmp-scope proof did not run green:\n" + s)
            self.assertIn("ROWS-COUNT: 0000000c", s, "ACT_KINDS is not 12 on the body")

    # ── A1 PLANT: the foreign-class refusal restored -> test_ep28e reds by a real EPERM ───────────────
    @unittest.skipUnless(GUEST, "needs the pinned guest + nested qemu")
    class TestA1PlantForeignClassRefusalReds(unittest.TestCase):
        def test_refused_reconcile_reddens_test_ep28e(self):
            s = _serial("a1plant", "test_ep28e", fault="PLANT_RECONCILE_REFUSED")
            self.assertRegex(s, r"LEDGER-RESULT FAILED ran=9",
                             "PLANT_RECONCILE_REFUSED did not red test_ep28e:\n" + s)
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", s)
            self.assertIn("PermissionError", s,
                          "the red is not the REAL foreign-class EPERM (no fabricated flag, L19):\n" + s)

    # ── A2 PLANT: an over-broad reconcile mis-types the staging file -> the durable swap reds ──────────
    @unittest.skipUnless(GUEST, "needs the pinned guest + nested qemu")
    class TestA2PlantTempThenSwapBrokenReds(unittest.TestCase):
        def test_broken_swap_reddens_the_durable_write_acts(self):
            s = _serial("a2plant", "test_c7_p3b_5a_v_seam_performers", fault="PLANT_RECONCILE_BREAKS_SWAP")
            self.assertRegex(s, r"LEDGER-RESULT FAILED ran=3",
                             "PLANT_RECONCILE_BREAKS_SWAP did not red the durable-write acts:\n" + s)
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", s)
            self.assertIn("PermissionError", s,
                          "the red is not the REAL swap refusal (no fabricated flag, L19):\n" + s)

    # ── A3 PLANT: the /rec/tmp scope dropped -> the outside-/rec/tmp adoption is served -> reds ────────
    @unittest.skipUnless(GUEST, "needs the pinned guest + nested qemu")
    class TestA3PlantOutsideTmpReds(unittest.TestCase):
        def test_dropped_scope_reddens_the_outside_tmp_refusal(self):
            s = _serial("a3plant", THIS_MOD, fault="PLANT_RECONCILE_OUTSIDE_TMP")
            self.assertRegex(s, r"LEDGER-RESULT FAILED ran=3",
                             "PLANT_RECONCILE_OUTSIDE_TMP did not red the /rec/tmp-scope check:\n" + s)
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", s)

    # ── A4 — NOTHING ELSE MOVES (host source-shape; git-checked in the close) ─────────────────────────
    class TestA4SourceShape(unittest.TestCase):
        def test_attested_members_unchanged_88(self):
            from kernel import attestation
            self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                             "ATTESTED_MEMBERS moved — the fix is edit-in-place, no new src member")

        def test_founding_unchanged(self):
            import json
            with open(os.path.join(SRC, "founding", "founding-pack.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["founding_version"], "1.55.0",
                                 "founding_version moved — this slice does NO founding")

        def test_no_on_disk_byte_format_change(self):
            disk = _read("disk.h")
            self.assertIn('#define BFS_MAGIC       "BODYFS02"', disk, "BODYFS02 magic changed (byte format)")
            self.assertIn("#define BFS_NAME_MAX    128u", disk, "name field width changed (byte format)")
            self.assertIn("capacity_sectors", disk, "the bfs_entry capacity field changed (byte format)")
            self.assertIn("#define FT_NREC   4u", disk, "FT_NREC is not the existing kind")
            self.assertIn("#define FT_DURABLE 5u", disk, "FT_DURABLE is not the existing kind")

        def test_the_reconcile_and_its_scope_are_in_the_shipped_source(self):
            bodyfs = _read("bodyfs.c")
            serve = _read("serve.c")
            self.assertIn("e->type == FT_DURABLE && e->length == 0", bodyfs,
                          "the zero-length FT_DURABLE reconcile is not in fs_nrec_append")
            self.assertIn("rec_under_tmp(rb)", serve,
                          "the /rec/tmp scope on the O_APPEND adoption is not in serve.c")

        def test_every_plant_exists_and_can_fire(self):
            bodyfs = _read("bodyfs.c")
            serve = _read("serve.c")
            self.assertIn("PLANT_RECONCILE_REFUSED", bodyfs, "A1's plant is absent (a check that cannot fail)")
            self.assertIn("PLANT_RECONCILE_BREAKS_SWAP", bodyfs, "A2's plant is absent")
            self.assertIn("PLANT_RECONCILE_OUTSIDE_TMP", serve, "A3's plant is absent")


if __name__ == "__main__":
    unittest.main(verbosity=2)
