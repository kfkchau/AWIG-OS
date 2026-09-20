# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel body serving the estate store's REMAINING record-disk acts in the EXACT shapes
# the store performs them — the durable whole-file write by temp-and-swap, the one-writer advisory lock,
# read-after-write of everything appended — at caller-named names under a per-world namespace, as in the
# seL4/gVisor/Fuchsia and osdev literature). NON-GOAL: no offensive capability; the body serves the seam's
# OWN declared record-disk acts in their real shapes and refuses every other write class by name (O_TRUNC on
# a present record stays refused, R1; no general writable filesystem, L21). Validated by building/reading a
# real booted body, never by attack (governance-work-method). Every kernel touch is the guest's nested qemu
# (L11 / EP-00 rule 9 / §A21). Full: SCOPE-STATEMENT.md.
"""C7 P3b-5a-v acceptance — THE SEAM'S PERFORMERS SERVED EXACTLY (design/54 §7 P3b-5a-v; archi countersign
:4343; 5a's completion, NOT a new act — ACT_KINDS stays 12).

After 5a-iv served the record pen at caller-named names, the resumed 5b batch found three MORE store paths
the 5s2 census counted served that the body-as-built did not perform, blocking 11 modules (:4341/:4343):
  CLASS-A  write_file_durably (host_seam.py:247) = os.open(tmp, O_WRONLY|O_CREAT|O_TRUNC) on an ABSENT temp
           name, write, fsync, os.replace(tmp, final): the atomic-write-once act by temp-then-swap. The body
           refused it because it refused O_TRUNC BY FLAG, coarser than its own law — R1 is overwrite of a
           PRESENT record; O_TRUNC on an ABSENT name is a create.
  CLASS-B  lock_write (host_seam.py:306) = os.open(<record>.lock, O_CREAT|O_RDWR) + fcntl.lockf(F_SETLK,
           LOCK_EX|LOCK_NB) + the holder text; lock_unlink closes + unlinks: the one-writer act. The body
           served the marker class only as ftruncate-to-0 and answered fcntl with a stub, so the HELD claim
           the seam takes was not performed.
  CLASS-C  a FRESH reader of a caller-named record (open_read/read_bytes/fstat) returned EMPTY — read-after-
           write under-served (the 64 KiB whole-load buffer; the streamed reader removes it).

This slice serves those three on the body in the EXACT shapes host_seam issues (measured on the guest's own
CPython 3.12.3), each PROVEN by the REAL store method on a fresh world path (L19), never a shaped call, each
with a build.sh -D plant that reds exactly its behaviour by a REAL mechanism.

  A1  THE DURABLE WHOLE-FILE WRITE AS write_file_durably PERFORMS IT. O_CREAT|O_TRUNC on an ABSENT name
      creates the staging file; the same-directory swap over an ABSENT or a PRESENT final is served; the
      bytes read back equal; O_TRUNC on a PRESENT record stays REFUSED (R1). PLANTS: PLANT_DURABLE_UNSERVED
      (the pre-5a-v body — O_TRUNC refused by flag — reds the real write_file_durably at os.open, a real
      OSError); PLANT_DURABLE_TRUNC_RECORD (O_TRUNC on a present record SERVED -> the R1 check reds).
  A2  THE ONE-WRITER ACT AS lock_write PERFORMS IT. O_CREAT|O_RDWR opens the *.lock; fcntl F_SETLK holds the
      exclusive claim; the holder text reads back; a SECOND SAME-PROCESS claim is GRANTED, as Linux grants it
      (POSIX record locks are PROCESS-associated, host_seam.py:306-325, and the body is ONE process — Q11, no
      fork), and its holder text reads back; close+unlink releases (the lock is re-claimable); the lock offered
      on a NON-*.lock name is refused by name. The CROSS-process refusal (a DIFFERENT process refused EAGAIN) is
      RECORDED as not provable on a single-process body (a comment + a skip, Q11), never asserted, never planted
      (a plant that cannot fire is a check that cannot fail — L19; C7-MAINT-LOCK-POSIX-PROCESS-CLAIM). PLANTS:
      PLANT_LOCK_UNSERVED (the pre-5a-v body reds the real lock_write at os.open); PLANT_LOCK_FIRST_REFUSED (the
      FIRST same-process claim wrongly answered -EAGAIN -> the real lock_write reds — a plant that CAN fire).
  A3  READ-AFTER-WRITE RETURNS EVERYTHING APPENDED. A fresh reader of a caller-named record reconstructs the
      whole record of any size, STREAMED. PLANT: PLANT_FRESH_READ_PARTIAL (the reader stops after the first
      sector -> a multi-sector record reads back partial, a fresh reader that does not see what was appended).
  A4  5b's GREEN-DEMAND POPULATION DERIVED MECHANICALLY (off-body, from the 5s2 traces). A module is green-
      demand IFF every write class it makes is a shape the body now serves (a host_seam performer) — every
      other module routes by cause. The count is REPORTED from the derived list, never asserted; the plant
      catches a module with an out-of-set class counted green.
  A5  THE PROPERTIES HOLD, GUEST-ONLY, ATTESTED, ACT_KINDS 12, PRODUCTION HELD. The append-only / write-once
      / one-writer properties are unchanged (L14); every other write class and any path outside /rec/ still
      refuse by name (L21); ATTESTED unchanged (edit-in-place); ACT_KINDS 12; founding unchanged; the body is
      not stood as the production performer; git-revertible; NO founding.

THE WRONG REFERENCE THIS SLICE REFUSES: the census's served CLASSES are not the body performing the EXACT
SHAPES the seam issues (:4234/:4341). Each act is proven by the REAL host_seam method (write_file_durably /
lock_write / open_read), never a shaped call that answers success without performing (STOP d, L19). And the
durable whole-file write is the atomic-write-once act (temp-then-swap), NOT an overwrite of the append-only
record — O_TRUNC on a present record stays refused (R1); no general writable filesystem (L21).

DUAL-ROLE. On the body (loaded as the ledger runmod, GOVOS_RUNMOD; sys.path carries /rec/src, tempfile lives
under /rec/tmp) only TestSeamPerformersOnBody runs, driving the real store methods — the body's LEDGER-RESULT
is ran=3. On the host it is the off-body harness (build with each plant, boot in a nested qemu, read the real
on-body run) plus the A4 derivation and the A5 source/property checks.
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

THIS_MOD = "test_c7_p3b_5a_v_seam_performers"


# ══ THE ON-BODY PROOF (A1/A2/A3): the REAL store's performers on a fresh world path (L19) ══════════════
# Runs ONLY on the body (loaded as the ledger runmod). tempfile.mkdtemp lands under /rec/tmp (the ledger
# bootstrap sets tempfile.tempdir), so every path is a caller-named /rec/ path — exactly the store's own.
@unittest.skipUnless(_ON_BODY, "SKIP BODY-BOOT: the seam-performer proof runs on the body (the real store methods)")
class TestSeamPerformersOnBody(unittest.TestCase):
    def _world(self):
        import tempfile
        from pathlib import Path
        return Path(tempfile.mkdtemp())                  # /rec/tmp/tmpXXXX — a fresh caller-named world

    def test_a1_durable_whole_file_write_as_write_file_durably_performs_it(self):
        from bridge.host_seam import host
        from pathlib import Path
        w = self._world()
        final = w / "blobfinal"
        # over an ABSENT final: create staging (O_TRUNC on absent), write, fsync, swap; read back equal.
        host().write_file_durably(str(w / "blob.part"), str(final), b"durable-content-one")
        host().fsync_dir(str(w))
        self.assertEqual(host().read_bytes(final), b"durable-content-one",
                         "the durable whole-file write lands and reads back equal (over an absent final)")
        # over a PRESENT final: the temp-and-swap CLOBBERS the present final (the atomic-write-once swap).
        host().write_file_durably(str(w / "blob2.part"), str(final), b"durable-content-TWO-longer")
        self.assertEqual(host().read_bytes(final), b"durable-content-TWO-longer",
                         "a second durable write swaps over the PRESENT final (S5-over-existing)")
        # R1: O_TRUNC (open('w')) on a PRESENT record is overwrite-in-place — refused by name; bytes STAND.
        rec = w / "caller.jsonl"
        with host().open_append(rec) as fh:
            fh.write("row-0\n")
        with self.assertRaises(OSError):
            open(str(rec), "w")
        with host().open_read(rec) as fh:
            self.assertEqual(fh.read(), "row-0\n", "the refused O_TRUNC left the append-only record intact")

    def test_a2_one_writer_act_as_lock_write_performs_it(self):
        from bridge.host_seam import host
        from pathlib import Path
        w = self._world()
        lockp = w / "record.jsonl.lock"
        host().lock_write(lockp, "12345")                # open O_CREAT|O_RDWR + F_SETLK held + holder text
        self.assertEqual(host().lock_read(lockp), "12345", "the holder's text reads back")
        # C7-MAINT-LOCK-POSIX-PROCESS-CLAIM: POSIX record locks (fcntl F_SETLK) are PROCESS-associated, not
        # per-fd (host_seam.py:306-325), and the body is ONE process (Q11, no fork) — so a SECOND same-process
        # F_SETLK on the *.lock this process already holds is GRANTED, exactly as the Linux kernel grants it.
        host().lock_write(lockp, "99999")                # the SECOND same-process claim SUCCEEDS (no raise)
        self.assertEqual(host().lock_read(lockp), "99999",
                         "the second same-process claim is granted and its holder text reads back")
        host().lock_unlink(lockp)                         # close (release the claim) + unlink
        # the lock is re-claimable after release (a fresh holder takes it), then released again.
        host().lock_write(lockp, "22222")
        self.assertEqual(host().lock_read(lockp), "22222", "a released lock is re-claimable by a fresh holder")
        host().lock_unlink(lockp)
        # the one-writer act is served ONLY on the *.lock name class — a non-*.lock name is refused by name.
        with self.assertRaises(OSError):
            host().lock_write(w / "plain.dat", "x")

    @unittest.skipUnless(
        os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv")),
        "SKIP PRIVATE-SOURCE: needs planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv (absent in the render)")
    def test_a3_read_after_write_returns_everything_appended(self):
        from bridge.host_seam import host
        from pathlib import Path
        w = self._world()
        rec = w / "big.jsonl"
        # append enough rows to span more than one 512-byte sector (a fresh reader must stream all of it).
        rows = ["row-%02d: %s\n" % (i, "x" * 48) for i in range(16)]     # ~960 bytes, > one sector
        for r in rows:
            with host().open_append(rec) as fh:
                fh.write(r)
        with host().open_read(rec) as fh:
            self.assertEqual(fh.read(), "".join(rows),
                             "a fresh reader reconstructs the WHOLE multi-sector record, streamed")


if not _ON_BODY:
    # ══ THE OFF-BODY HARNESS + A4 DERIVATION + A5 SOURCE/PROPERTY CHECKS (host only) ═══════════════════
    import csv

    _KEY = "<HOME><KEYPATH>"
    _SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
            "<GUEST>"]
    _WD = "/tmp/p3b5av-accept"
    _QEMU = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc"
    S2 = os.path.join(ROOT, "planning", "evidence", "C7-P3b-5s2-WRITE-CLASSES")
    RESULTS_TSV = os.path.join(S2, "results.tsv")

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
                           capture_output=True, timeout=400)
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

    def _boot(out, img, tag, wait_s=200):
        """Boot the body in a NESTED qemu (sealed image -initrd, `img` as an IDE disk), DETACHED (setsid)
        with serial to a file, then POLL until BODY-HALT — the reliable pattern (5a-iv/5b-i). SERIALIZED:
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

    # ── clean boot: A1/A2/A3 all pass on the body (the real store methods) ────────────────────────────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
    class TestCleanBootSeamPerformersGreen(unittest.TestCase):
        def test_the_three_seam_performers_run_green_on_the_body(self):
            serial = _serial("clean")
            self.assertIn("BODY-HALT", serial, "the body must reach BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT OK ran=3 failures=0 errors=0 skipped=0",
                             "the three seam-performer behaviours run green on the body:\n" + serial[-2500:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000000", serial, "the REAL exit status is 0 (green)")
            for meth in ("test_a1_durable_whole_file_write_as_write_file_durably_performs_it",
                         "test_a2_one_writer_act_as_lock_write_performs_it",
                         "test_a3_read_after_write_returns_everything_appended"):
                self.assertRegex(serial, re.escape(meth) + r".*ok", meth + " did not report ok")

    # ── A1 plant: the pre-5a-v body — O_TRUNC refused by flag -> the real write_file_durably reds ──────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA1PlantDurableUnservedReds(unittest.TestCase):
        def test_unserved_durable_write_reddens_the_real_write_file_durably(self):
            serial = _serial("durunserved", fault="PLANT_DURABLE_UNSERVED")
            self.assertIn("BODY-HALT", serial, "even a red run reaches BODY-HALT (a completed run)")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3",
                             "the pre-5a-v body reds the durable-write run:\n" + serial[-2500:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertRegex(serial, r"test_a1_durable_whole_file_write.*(FAIL|ERROR)",
                             "A1 (the durable whole-file write) is the reddened behaviour")
            self.assertRegex(serial, r"(PermissionError|OSError|Errno)",
                             "the RED is the REAL write_file_durably answering EPERM — no fabricated flag (L19)")
            self.assertRegex(serial, r"test_a2_one_writer_act.*ok", "A2 is unaffected (the check can fail, precisely)")

    # ── A1 plant: O_TRUNC on a PRESENT record served -> the R1 refusal check reds ──────────────────────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA1PlantTruncRecordServedReds(unittest.TestCase):
        def test_served_truncate_on_a_present_record_reddens_the_r1_refusal(self):
            serial = _serial("truncrec", fault="PLANT_DURABLE_TRUNC_RECORD")
            self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3 failures=1",
                             "serving O_TRUNC on a present record reds exactly the R1 check:\n" + serial[-2500:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertRegex(serial, r"test_a1_durable_whole_file_write.*(FAIL|ERROR)",
                             "A1's R1 refusal is the reddened behaviour")
            self.assertRegex(serial, r"test_a2_one_writer_act.*ok", "A2 still passes (the check can fail, precisely)")

    # ── A2 plant: the pre-5a-v body — the lock open unserved -> the real lock_write reds ───────────────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA2PlantLockUnservedReds(unittest.TestCase):
        def test_unserved_lock_reddens_the_real_lock_write(self):
            serial = _serial("lockunserved", fault="PLANT_LOCK_UNSERVED")
            self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3",
                             "the pre-5a-v body reds the one-writer run:\n" + serial[-2500:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertRegex(serial, r"test_a2_one_writer_act.*(FAIL|ERROR)",
                             "A2 (the one-writer act) is the reddened behaviour")
            self.assertRegex(serial, r"(FileNotFoundError|OSError|Errno)",
                             "the RED is the REAL lock_write answering ENOENT — no fabricated flag (L19)")

    # ── A2 plant (the CAN-FIRE replacement, C7-MAINT-LOCK-POSIX-PROCESS-CLAIM): the FIRST same-process claim
    #    wrongly answered -EAGAIN -> the real lock_write reds. (The retired PLANT_LOCK_SECOND_CLAIM fired on
    #    what is now CORRECT behaviour — a same-process re-claim being granted — a check that cannot fail.) ──
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA2PlantFirstRefusedReds(unittest.TestCase):
        def test_wrongly_refusing_the_first_claim_reddens_the_real_lock_write(self):
            serial = _serial("lockfirstref", fault="PLANT_LOCK_FIRST_REFUSED")
            self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3",
                             "wrongly refusing the first same-process claim reds the one-writer run:\n" + serial[-2500:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertRegex(serial, r"test_a2_one_writer_act.*(FAIL|ERROR)",
                             "A2 (the granted same-process claim) is the reddened behaviour")
            self.assertRegex(serial, r"(BlockingIOError|OSError|Errno)",
                             "the RED is the REAL lock_write answering EAGAIN on the first claim — no fabricated flag (L19)")
            self.assertRegex(serial, r"test_a1_durable_whole_file_write.*ok", "A1 still passes (the check can fail)")

    # ── A3 (the plan) — THE CROSS-PROCESS REFUSAL IS RECORDED, NOT ASSERTED. POSIX record locks are process-
    #    associated; the cross-process refusal (a DIFFERENT process's F_SETLK on the held *.lock answered
    #    EAGAIN) is a real property of host_seam.lock_write on a multi-process host, but the body is ONE
    #    process (Q11, no fork), so a second process cannot be presented to it. This behaviour is therefore
    #    NOT exercisable on a single-process body; it is recorded here as a skip and never asserted, never
    #    planted (a plant that cannot fire is a check that cannot fail — L19). The one-writer cross-process
    #    property is NOT loosened (L14): the body simply cannot host a second claimant process. ─────────────
    class TestA3CrossProcessRefusalRecorded(unittest.TestCase):
        def test_cross_process_refusal_is_not_provable_on_a_single_process_body(self):
            self.skipTest("cross-process one-writer refusal not provable on a single-process body "
                          "(Q11, no fork; POSIX F_SETLK is process-associated) — recorded, never asserted")

    # ── A3 plant: the fresh reader returns partial -> read-after-write reds ────────────────────────────
    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
    class TestA3PlantFreshReadPartialReds(unittest.TestCase):
        def test_partial_fresh_read_reddens_read_after_write(self):
            serial = _serial("readpartial", fault="PLANT_FRESH_READ_PARTIAL")
            self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
            self.assertRegex(serial, r"LEDGER-RESULT FAILED ran=3 failures=1",
                             "a partial fresh read reds exactly read-after-write:\n" + serial[-2500:])
            self.assertIn("LEDGER-EXIT-STATUS: 0x00000001", serial, "the REAL exit status is 1 (red)")
            self.assertRegex(serial, r"test_a3_read_after_write.*(FAIL|ERROR)",
                             "A3 (read-after-write) is the reddened behaviour")
            self.assertRegex(serial, r"test_a1_durable_whole_file_write.*ok", "A1 still passes (the check can fail)")

    # ── A4 — 5b's GREEN-DEMAND POPULATION DERIVED MECHANICALLY against the body's real performer set ───
    # The served-on-body write classes after 5a-v, each mapped to a host_seam performer (design/54 §1, the
    # 5s2 CLASSES taxonomy FINDINGS.md): every S-class + R2 (the one-writer *.lock idiom). A module is green-
    # demand iff every write class in its 5s2 trace is one the body serves; every other module routes by
    # cause (facility / content / harness). The count is reported from the derived list, never asserted.
    _SERVED_ON_BODY = {
        "S1a": "fs_blob_write_once (O_CREAT|O_EXCL create-once, 5a-ii)",
        "S1b": "fs_durable_write   (O_CREAT|O_TRUNC on an absent name — the durable staging create, 5a-v)",
        "S2":  "fs_nrec_append     (O_APPEND — the record pen, 5a-iv)",
        "S3":  "serve_ns_mkdir     (mkdir — declare a namespace, 5a-ii)",
        "S4":  "fs_remove          (unlink — the remove act, 5a-ii/5a-v)",
        "S5":  "fs_rename / fs_swap_rename (same-directory rename incl. the swap-over-existing, 5a-ii/5a-v)",
        "S6":  "fs_read_entry_range (open_read/read_bytes/fstat/getdents — streamed read-after-write, 5a-v)",
        "R2":  "the one-writer lock act (fcntl F_SETLK + ftruncate-to-0 on a *.lock, 5a-v)",
    }

    def _rows():
        with open(RESULTS_TSV, newline="") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def _base_class(code):
        # "S5-from-S1a" / "S5-over-existing" / "S5-from-unknown" all normalise to the S5 rename act.
        return code.split("-", 1)[0]

    def _module_classes(row):
        """The set of BASE write-class codes in a module's 5s2 trace (from classes_with_counts)."""
        out = set()
        for tok in (row.get("classes_with_counts") or "").split():
            code = tok.split("=", 1)[0]
            if code:
                out.add(_base_class(code))
        return out

    class TestA4GreenDemandPopulationDerived(unittest.TestCase):
        @unittest.skipUnless(
            os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv")),
            "SKIP PRIVATE-SOURCE: needs planning/evidence/C7-P3b-5s2-WRITE-CLASSES/results.tsv (absent in the render)")
        def test_green_demand_is_every_module_whose_classes_the_body_serves(self):
            rows = _rows()
            self.assertEqual(len(rows), 207, "5s2 measured 207 modules")
            served = set(_SERVED_ON_BODY)
            guest_driving = {r["module"] for r in rows if r["status"] == "SKIPPED-GUEST-DRIVING"}
            green_demand = [r["module"] for r in rows
                            if r["module"] not in guest_driving and _module_classes(r) <= served]
            # REPORT the count from the derived LIST (never a magic constant).
            report = "A4 green-demand (classes the body serves after 5a-v): %d modules" % len(green_demand)
            self.assertGreater(len(green_demand), 0, report)
            # every derived-green module's classes are a subset of the served set — the property, with a plant.
            for m in green_demand:
                row = next(r for r in rows if r["module"] == m)
                self.assertTrue(_module_classes(row) <= served,
                                "%s counted green but uses a class the body does not serve: %s"
                                % (m, sorted(_module_classes(row) - served)))
            # RECONCILE with 5b's write-class pass set (136): the derivation IS the pass set (all-served OR
            # only-R2-refused), so no green-demand module is outside it, and none has a blocking R-class.
            pass_set = {r["module"] for r in rows
                        if r["status"] == "PASS-CANDIDATE"
                        or (r["status"] == "REFUSED" and r["R_classes"] == "R2")}
            self.assertEqual(set(green_demand) - guest_driving, pass_set - guest_driving,
                             "the class-derived green-demand set reconciles with 5b's 136 write-class pass set")

        def test_the_derivation_catches_a_module_with_an_out_of_set_class(self):
            served = set(_SERVED_ON_BODY)
            # PLANT: a synthetic module trace with an out-of-set class (R8, a successful execve of another
            # program — declared out by facility). It must NOT pass the green-demand test (the check can fail).
            ghost = {"module": "ghost_execve", "status": "REFUSED", "R_classes": "R8",
                     "classes_with_counts": "S2=3 S6=10 R8=1"}
            self.assertFalse(_module_classes(ghost) <= served,
                             "a module whose trace carries R8 (execve) cannot be green-demand (routed by facility)")
            # the near-miss control: the SAME module without R8 IS green-demand (the discriminator works).
            clean = dict(ghost, classes_with_counts="S2=3 S6=10")
            self.assertTrue(_module_classes(clean) <= served,
                            "the same trace without the out-of-set class is green-demand (the check discriminates)")

        def test_each_served_class_maps_to_a_body_performer(self):
            # every served write class names the host_seam performer / body primitive that serves it — so a
            # green-demand verdict is a claim about the body PERFORMING the shape, not the census's class label.
            for code, performer in _SERVED_ON_BODY.items():
                self.assertTrue(performer and "(" in performer, "%s must name its body performer" % code)
            self.assertIn("fs_durable_write", _SERVED_ON_BODY["S1b"], "S1b is the durable whole-file write (5a-v)")
            self.assertIn("F_SETLK", _SERVED_ON_BODY["R2"], "R2 is the one-writer lock act (5a-v)")
            self.assertIn("fs_read_entry_range", _SERVED_ON_BODY["S6"], "S6 is the streamed read (5a-v)")

    # ── A5 — source shape, properties, attestation, act-kinds, production held (main; no guest) ────────
    class TestSourceShapeA5(unittest.TestCase):
        def test_a5_attested_unchanged_act_kinds_12_founding_unchanged(self):
            import json
            from kernel import attestation
            from bridge.host_seam import ACT_KINDS
            self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                             "5a-v edits members in place (serve.c/serve.h/bodyfs.c/disk.h) — no new .c")
            for rel in ("body/serve.c", "body/serve.h", "body/bodyfs.c", "body/disk.h"):
                self.assertIn(rel, attestation.ATTESTED_MEMBERS, "%s is an attested member (edit-in-place)" % rel)
            names = sorted(n for n in os.listdir(BODY)
                           if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))
            self.assertEqual(len(names), 31, "src/body is 31 files (5a-v adds none): %r" % names)
            self.assertEqual(len(ACT_KINDS), 12, "no new act kind — a served shape is not a kind (archi :4343)")
            pack = os.path.join(SRC, "founding", "founding-pack.json")
            with open(pack) as f:
                self.assertEqual(json.load(f)["founding_version"], "1.55.0", "no founding on a body slice")

        def test_a5_the_three_performers_and_their_types_exist(self):
            dh = _read("disk.h")
            self.assertIn("#define FT_DURABLE", dh, "the durable-write staging type is declared")
            self.assertIn("int  fs_durable_write(const char *name, const uint8_t *payload, uint32_t n)", dh,
                          "the durable whole-file write primitive is declared")
            self.assertIn("int  fs_swap_rename(const char *oldname, const char *newname)", dh,
                          "the atomic-write-once swap primitive is declared")
            self.assertIn("uint32_t fs_read_entry_range(", dh, "the streamed-read primitive is declared")
            bf = _read("bodyfs.c")
            for fn in ("int fs_durable_write(const char *name", "int fs_swap_rename(const char *oldname",
                       "uint32_t fs_read_entry_range("):
                self.assertIn(fn, bf, "the primitive %r is defined" % fn)
            sh = _read("serve.h")
            self.assertIn("#define SYS_ftruncate", sh, "the lock act's ftruncate shape is declared")
            self.assertIn("#define F_SETLK", sh, "the one-writer F_SETLK claim is declared")

        def test_a5_serve_dispatch_and_the_plants_exist(self):
            sv = _read("serve.c")
            self.assertIn("#define SI_FD_DWR", sv, "the durable-write staging fd kind exists")
            self.assertIn("#define SI_FD_LOCK", sv, "the one-writer lock fd kind exists")
            self.assertIn("#define SI_FD_NRECRD", sv, "the streamed record read fd kind exists")
            self.assertIn("if (ns_is_marker(rb) && (flags & O_CREAT))", sv,
                          "the one-writer lock open is served on the *.lock class")
            self.assertIn("a1 == F_SETLK", sv, "the HELD exclusive claim is served (fcntl F_SETLK)")
            # every behaviour has a plant (a check that cannot fail is not a check).
            for plant in ("PLANT_DURABLE_UNSERVED", "PLANT_DURABLE_TRUNC_RECORD",
                          "PLANT_LOCK_UNSERVED", "PLANT_LOCK_FIRST_REFUSED"):
                self.assertIn(plant, sv, "%s plant exists in serve.c" % plant)
            self.assertNotIn("PLANT_LOCK_SECOND_CLAIM", sv,
                             "the retired second-claim plant (fired on now-correct behaviour) is gone")
            self.assertIn("PLANT_FRESH_READ_PARTIAL", _read("bodyfs.c"), "the read-after-write plant exists")

        def test_a5_append_only_and_r1_property_held(self):
            # the append-only record is never truncated-in-place: fs_record_write_at still refuses a non-tail
            # offset, and the durable whole-file write refuses O_TRUNC on a PRESENT record (R1) — the property
            # grows a mechanism, it does not loosen (L14).
            bf = _read("bodyfs.c")
            self.assertIn("if (off != e->length) { return -1; }", bf,
                          "the record's sole-appender leash (append-only by construction) is untouched")
            sv = _read("serve.c")
            self.assertIn("if (present_record) { return (uint64_t)(-1); }", sv,
                          "O_TRUNC on a PRESENT record is refused by name (R1) — the record is never truncated")
            # the durable swap clobbers ONLY a durable-write staging source (the ns write-once swap keeps no-
            # clobber) and NEVER the record — the write-once/append-only classes stay distinct (L21).
            self.assertIn("if (dst && dst->type == FT_RECORD) { return -1; }", bf,
                          "the atomic-write-once swap never clobbers the append-only record")

        def test_a5_no_host_kernel_load_in_the_edited_body_files(self):
            for rel in ("serve.c", "serve.h", "bodyfs.c", "disk.h"):
                text = _read(rel)
                for tok in ("insmod", "modprobe"):
                    self.assertNotIn(tok, text, "src/body/%s must not load a host kernel module (L11)" % rel)
            self.assertIn("insmod", "insmod /lib/modules/x.ko")   # the near-miss control (§A64): the scan CAN fail

        def test_a5_the_body_is_not_stood_as_the_production_performer(self):
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
