# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel body serving its OWN record-disk write acts under a per-world namespace at
# caller-named paths, backed by its bespoke on-disk format — as in the seL4/gVisor/Fuchsia and osdev
# literature). NON-GOAL: no offensive capability; the body serves the seam's declared write acts under
# /rec/ and refuses every other write class by name; validated by building/reading a real booted body,
# never by attack (governance-work-method). Every kernel touch is the guest's nested qemu (L11 / EP-00
# rule 9 / §A21). Full declaration: SCOPE-STATEMENT.md.
"""C7 P3b-5a-ii acceptance — THE NAMESPACE ACTS (design/54 §7 P3b-5a; archi countersign :4257; the
manager's 5a sub-split, plan STOP f — slice two of three: the /rec/ namespace acts A2-A5, on the
BODYFS02 substrate 5a-i built; the tree archive + finder A6 is 5a-iii).

Under /rec/<world>/… the body PERFORMS the seam's OWN record-disk write acts at CALLER-NAMED paths,
each backed by the record disk (the ONE truth; no namespace in body memory). The writable surface is
EXACTLY the seam's declared acts (design/54 L21); every other write class refuses BY NAME; no served
shape answers success without performing (L19). Proven on the booted body (the DISK phase's self-check
prints CHECK NS-A2/A3/A4/A5 + NS-ACTS), each behaviour with a build.sh -D plant that reds its line —
a check that cannot fail is not a check.

  A2  the acts PERFORM at /rec/<world>/…: mkdir declares (stats present + lists), create-on-absent
      writes once, append extends the record, getdents lists, stat sizes, same-dir rename swaps — the
      bytes written READ BACK equal what was written. PLANT (PLANT_NS_STUB_NOOP): mkdir/rename are the
      0-answering no-op -> the stat/list/read-back reds (L21/L19).
  A3  write-once by name AND content: identical bytes to a present name -> success, nothing performed;
      different bytes -> refuse; a REMOVED name is re-creatable. PLANTS: PLANT_WRITEONCE_OVERWRITE
      (different accepted) and PLANT_NS_IDENTICAL_REFUSED (identical refused) each red NS-A3.
  A4  the one-writer act (create-open + a held exclusive claim + truncate-to-nothing + the holder's
      mark) served ONLY on the marker (*.lock) name class; a second claim on a held marker refused; not
      served on the record. PLANTS: PLANT_NS_SECOND_CLAIM (a second claim admitted) and
      PLANT_NS_TRUNC_NONMARKER (truncate-to-nothing offered on a non-marker) each red NS-A4.
  A5  every OTHER write class refuses BY NAME (overwrite / pwrite-below / cross-dir rename / chmod /
      symlink / link / mmap-write / truncate-the-record); a path OUTSIDE /rec/ refuses -ENOENT; a
      namespace held in body MEMORY is refused (the disk is the one truth). PLANTS:
      PLANT_NS_OTHERCLASS_SERVED (an other class served) and PLANT_NS_OUTSIDE_SERVED (an outside path
      served) each red NS-A5.

The boot acceptances build+boot in the NESTED guest and skip when the pinned guest is not reachable
over SSH; the source/attestation checks run in main. Every kernel touch is the guest's nested qemu; the
host kernel is never touched (L11 / EP-00 rule 9 / §A21). Validated by building/reading a real booted
body, never by attack (governance-work-method).
"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
sys.path.insert(0, SRC)


def _read(rel):
    with open(os.path.join(BODY, rel), encoding="utf-8") as f:
        return f.read()


# ── the source / attestation checks (main; no guest) ───────────────────────────────────────────
class TestSourceShapeAndAttestation(unittest.TestCase):
    def test_no_new_src_member_attested_holds_at_88(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                         "5a-ii edits members in place (serve.c/bodyfs.c/diskcheck.c/disk.h) — no new .c")
        for rel in ("body/serve.c", "body/bodyfs.c", "body/diskcheck.c", "body/disk.h"):
            self.assertIn(rel, attestation.ATTESTED_MEMBERS, "%s is an attested member (edit-in-place)" % rel)

    def test_src_body_is_thirty_one_files_no_new_file(self):
        names = sorted(n for n in os.listdir(BODY)
                       if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))
        self.assertEqual(len(names), 31, "src/body is 31 files (5a-ii adds none): %r" % names)

    def test_no_founding_act_kinds_twelve_pack_unchanged(self):
        import json
        from bridge.host_seam import ACT_KINDS
        self.assertEqual(len(ACT_KINDS), 12, "no new act kind — a served shape is not a kind (archi :4248)")
        pack = os.path.join(SRC, "founding", "founding-pack.json")
        with open(pack) as f:
            self.assertEqual(json.load(f)["founding_version"], "1.55.0", "no founding on a body slice")

    def test_fs_walk_widened_to_full_width_paths(self):
        # 5a-i left fs_walk char[][32] and deferred the widening to this slice (the disk.h comment).
        dh = _read("disk.h")
        self.assertRegex(dh, r"int\s+fs_walk\(char\s+names\[\]\[BFS_NAME_MAX\],\s*int\s+max\)",
                         "the disk.h fs_walk declaration is widened to BFS_NAME_MAX (full-width paths)")
        self.assertNotIn("char names[][32]", dh, "no 32-byte fs_walk declaration remains")
        bf = _read("bodyfs.c")
        self.assertRegex(bf, r"int\s+fs_walk\(char\s+names\[\]\[BFS_NAME_MAX\],\s*int\s+max\)",
                         "the bodyfs.c fs_walk definition is widened")
        self.assertIn("memcpy(names[c], e->name, BFS_NAME_MAX)", bf, "the walk copies the full-width name")
        dc = _read("diskcheck.c")
        self.assertIn("char names[BODY_READ_WALK_MAX][BFS_NAME_MAX]", dc, "the diskcheck.c consumer is widened")
        sv = _read("serve.c")
        self.assertIn("char names[8][BFS_NAME_MAX]", sv, "the serve.c getdents consumer is widened")

    def test_new_bodyfs_primitives_declared(self):
        dh = _read("disk.h")
        self.assertIn("int  fs_rename(const char *oldname, const char *newname)", dh,
                      "fs_rename (the same-dir write-once swap) is declared")
        self.assertIn("int  fs_marker_write(const char *name, const uint8_t *data, uint32_t n)", dh,
                      "fs_marker_write (the one-writer act's disk shape, *.lock only) is declared")

    def test_writeonce_by_name_and_content_in_bodyfs(self):
        bf = _read("bodyfs.c")
        # the A3 idempotent-identical / different-refuse content check
        self.assertIn("fs_blob_content_eq", bf, "write-once compares content on a present name (A3)")
        self.assertIn("PLANT_NS_IDENTICAL_REFUSED", bf, "the identical-refused plant exists (A3, fallible)")

    def test_serve_has_the_namespace_acts_and_dispatch_is_real(self):
        sv = _read("serve.c")
        self.assertIn("int serve_ns_selfcheck(void)", sv, "the body-side namespace-acts proof exists")
        # the mkdir/rename dispatch stubs are made REAL under /rec/ (no bare `ans = 0`)
        self.assertRegex(sv, r"case SYS_mkdir:.*\n.*serve_ns_syscall\(SYS_mkdir",
                         "the SYS_mkdir stub routes to the ns layer (real under /rec/)")
        self.assertRegex(sv, r"case SYS_rename:.*\n.*serve_ns_syscall\(SYS_rename",
                         "the SYS_rename stub routes to the ns layer (real under /rec/)")
        self.assertIn('name[n-5] == \'.\' && name[n-4] == \'l\'', sv,
                      "the marker name class is *.lock (5s2 FINDINGS §1 / :4248)")
        for plant in ("PLANT_NS_STUB_NOOP", "PLANT_NS_SECOND_CLAIM", "PLANT_NS_TRUNC_NONMARKER",
                      "PLANT_NS_OTHERCLASS_SERVED", "PLANT_NS_OUTSIDE_SERVED"):
            self.assertIn(plant, sv, "%s plant exists (a check that cannot fail is not a check)" % plant)


# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ──────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b5aii-accept"


def _guest_reachable():
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
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(outdir, fault=""):
    _seed_guest()
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (_WD, _WD, outdir, fault)],
                       capture_output=True, timeout=180)
    if b.returncode != 0:
        raise AssertionError("guest build failed (%s): %s" % (fault, b.stderr.decode(errors="replace")))
    return outdir


def _guest_mkdisk(img):
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img):
    # SERIALIZED: one nested qemu at a time. Serial goes to a guest FILE (unbuffered, survives the
    # timeout SIGKILL) then is read back — reliable where stdio-over-ssh can drop a KILLed qemu's
    # buffered tail. -pidfile lets us reap by pid without a pattern that could self-match this shell.
    ser = "%s/serial.txt" % outdir
    pidf = "%s/qemu.pid" % outdir
    subprocess.run(
        _SSH + ["rm -f %s %s; timeout --signal=KILL 30 qemu-system-x86_64 -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 -serial file:%s -display none -no-reboot "
                "-m 256 -pidfile %s </dev/null >/dev/null 2>&1; "
                "[ -f %s ] && kill -9 $(cat %s) 2>/dev/null; true"
                % (ser, pidf, outdir, img, ser, pidf, pidf, pidf)],
        capture_output=True, timeout=60)
    r = subprocess.run(_SSH + ["cat %s 2>/dev/null" % ser], capture_output=True, timeout=20)
    return r.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault=""):
    """Build (with the fault), format a fresh disk, boot in nested qemu — cached per fault tag. One
    nested qemu at a time (SERIALIZED): _guest_boot pkills any prior body.img qemu first."""
    tag = fault or "clean"
    if tag not in _SERIAL_CACHE:
        out = _guest_build("%s/out-%s" % (_WD, tag), fault)
        img = _guest_mkdisk("%s/disk-%s.img" % (_WD, tag))
        _SERIAL_CACHE[tag] = _guest_boot(out, img)
    return _SERIAL_CACHE[tag]


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A2-A5 clean boot: the acts PERFORM + read-back; every other class refuses ────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestNamespaceActsPerformClean(unittest.TestCase):
    def test_clean_boot_all_four_acceptances_pass(self):
        serial = _serial()
        self.assertIn("DISK: OK", serial, "the BODYFS02 image mounts on the metal")
        self.assertIn("ACTS: PASS", serial, "the five P3b-2 record acts still pass (regression)")
        # the /rec/ namespace acts perform at caller-named paths, read back, refuse every other class.
        self.assertIn("CHECK NS-A2: PASS", serial, "the acts perform + read-back at caller-named paths")
        self.assertIn("CHECK NS-A3: PASS", serial, "write-once by name AND content (identical/different/re-create)")
        self.assertIn("CHECK NS-A4: PASS", serial, "the one-writer act on the *.lock marker class only")
        self.assertIn("CHECK NS-A5: PASS", serial, "every other write class refuses by name; outside -> ENOENT")
        self.assertIn("NS-ACTS: PASS", serial, "the aggregate namespace-acts proof passes")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c) still announced (no new act kind)")


# ── A2 plant: the mkdir/rename no-op stubs -> the read-back / listing reds ────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestA2StubNoopRedsReadback(unittest.TestCase):
    def test_mkdir_rename_noop_reds_a2(self):
        serial = _serial("PLANT_NS_STUB_NOOP")
        self.assertIn("CHECK NS-A2: FAIL", serial,
                      "leaving mkdir/rename the 0-answering no-op reds the read-back/listing (L21/L19)")
        self.assertIn("NS-ACTS: FAIL", serial, "the aggregate reds")


# ── A3 plants: write-once by name AND content (both directions fallible) ──────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestA3WriteOnceByNameAndContent(unittest.TestCase):
    def test_different_bytes_accepted_reds_a3(self):
        serial = _serial("PLANT_WRITEONCE_OVERWRITE")
        self.assertIn("CHECK NS-A3: FAIL", serial, "different bytes to a present name accepted -> A3 reds")
        self.assertIn("NS-ACTS: FAIL", serial, "the aggregate reds")

    def test_identical_bytes_refused_reds_a3(self):
        serial = _serial("PLANT_NS_IDENTICAL_REFUSED")
        self.assertIn("CHECK NS-A3: FAIL", serial, "identical bytes to a present name refused -> A3 reds")
        self.assertIn("NS-ACTS: FAIL", serial, "the aggregate reds")


# ── A4 plants: the one-writer act on the marker class only (both directions fallible) ─────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestA4OneWriterMarkerClass(unittest.TestCase):
    def test_second_claim_admitted_reds_a4(self):
        serial = _serial("PLANT_NS_SECOND_CLAIM")
        self.assertIn("CHECK NS-A4: FAIL", serial, "a second claim on a held marker admitted -> A4 reds")
        self.assertIn("NS-ACTS: FAIL", serial, "the aggregate reds")

    def test_truncate_on_nonmarker_served_reds_a4(self):
        serial = _serial("PLANT_NS_TRUNC_NONMARKER")
        self.assertIn("CHECK NS-A4: FAIL", serial,
                      "the truncate-to-nothing offered on a non-marker name -> A4 reds")
        self.assertIn("NS-ACTS: FAIL", serial, "the aggregate reds")


# ── A5 plants: every other write class refuses by name; outside -> ENOENT (both directions) ───────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestA5EveryOtherClassRefusesByName(unittest.TestCase):
    def test_other_class_served_reds_a5(self):
        serial = _serial("PLANT_NS_OTHERCLASS_SERVED")
        self.assertIn("CHECK NS-A5: FAIL", serial, "an other write class served as success -> A5 reds")
        self.assertIn("NS-ACTS: FAIL", serial, "the aggregate reds")

    def test_outside_rec_served_reds_a5(self):
        serial = _serial("PLANT_NS_OUTSIDE_SERVED")
        self.assertIn("CHECK NS-A5: FAIL", serial, "a path outside /rec/ served (not ENOENT) -> A5 reds")
        self.assertIn("NS-ACTS: FAIL", serial, "the aggregate reds")


if __name__ == "__main__":
    unittest.main()
