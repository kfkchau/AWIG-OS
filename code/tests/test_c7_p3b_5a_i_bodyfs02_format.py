"""C7 P3b-5a-i acceptance — THE BODYFS02 FORMAT SUBSTRATE (design/54 §7 P3b-5a; archi :4257).

The body's record-disk format grows BODYFS01 -> BODYFS02 to carry PATH-named namespaces, sized by
the measurement (planning/evidence/C7-P3b-5s2-WRITE-CLASSES + the 5a pre-flight, archi :4257):

  name[128]          >= the 92-byte longest measured path      (was name[32])
  2048 entries       >= the 1,230 per-module max path count     (test_ep40; was 32)
  data region 64 MiB >= 1.9x the 34.16 MiB per-module max write (test_ep24c) — a DIFFERENT module;
                        byte-max and path-max are decoupled and sized independently.

This is the FORMAT SUBSTRATE ONLY (mgr's 5a-i sub-slice, plan STOP f). It grows disk.h + bodyfs.c +
mkdisk.py; it does NOT add the namespace acts at /rec/ (serve.c — that is 5a-ii) nor stage the tree
archive (5a-iii). The append-only / write-once / one-writer PROPERTIES are UNCHANGED — the mechanism
grows, the property holds, its pins re-point (L14). A BODYFS01 image is REFUSED at mount BY NAME.

  A1  the format IS BODYFS02: magic "BODYFS02" + version 2; a BODYFS01 image REFUSES at mount by name
      (not silently reinterpreted); names hold paths to >= 92 bytes; a name longer than the field is
      REFUSED, never truncated; the five record acts PASS on the grown format (properties held).
  A7  sized to the per-module maximum: data region 64 MiB, entry table >= 2048, name[128].
  A8  the P3b-2 format mirror re-points (mkdisk.py <-> disk.h in lock-step); ATTESTED stays 88 (all
      files edit-in-place, no new .c); the built .elf / .img are never members.

Register: OS on-disk-format bring-up on a disposable guest, described by function — a record-disk
format grown to hold path-named namespaces; validated by building/reading, never by attack
(governance-work-method). Every kernel touch is the guest's nested qemu (L11 / EP-00 rule 9 / §A21).
The guest cases build+boot in the NESTED guest and skip when the pinned guest is not reachable.
"""

import importlib.util
import os
import re
import struct
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
DISK_H = os.path.join(BODY, "disk.h")
PACK = os.path.join(SRC, "founding", "founding-pack.json")
sys.path.insert(0, SRC)

# the measured figures this slice sizes to (planning/evidence/C7-P3b-5s2-WRITE-CLASSES + 5a pre-flight)
MEASURED_MAX_WRITE_MIB = 34.16          # test_ep24c = 35,820,486 bytes (per-module max write volume)
MEASURED_MAX_PATHS = 1230               # test_ep40 (per-module max path count; a DIFFERENT module)
MEASURED_MAX_NAME = 92                  # longest measured path name, in bytes


def _load_mkdisk():
    """Load src/body/mkdisk.py as a module (its build_image() needs no host I/O)."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("body_mkdisk", os.path.join(BODY, "mkdisk.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _diskh_defines():
    """Parse the #define constants out of src/body/disk.h (the C source of truth for the format)."""
    with open(DISK_H, encoding="utf-8") as f:
        text = f.read()
    out = {}
    for name in ("BFS_VERSION", "BFS_NAME_MAX", "BFS_ENTRY_SIZE", "BFS_DIR_SECTORS", "BFS_DIR_START"):
        m = re.search(r"#define\s+%s\s+(\d+)u?" % name, text)
        if m:
            out[name] = int(m.group(1))
    m = re.search(r'#define\s+BFS_MAGIC\s+"([^"]+)"', text)
    if m:
        out["BFS_MAGIC"] = m.group(1)
    m = re.search(r"char\s+name\[BFS_NAME_MAX\]", text)
    out["NAME_FIELD_IS_BFS_NAME_MAX"] = bool(m)
    return out


def _parse_super(img):
    """Return the BODYFS superblock fields from a formatted image."""
    magic = img[0:8]
    (version, block_size, dir_start, dir_sectors, data_start,
     next_free, total_sectors, dir_count) = struct.unpack("<8I", img[8:40])
    return {"magic": magic, "version": version, "block_size": block_size,
            "dir_start": dir_start, "dir_sectors": dir_sectors, "data_start": data_start,
            "next_free": next_free, "total_sectors": total_sectors, "dir_count": dir_count}


# ── A1 / A7 / A8 — the format substrate, provable in main (no guest) ───────────────────────────
class TestBodyfs02FormatSubstrate(unittest.TestCase):
    def setUp(self):
        self.mk = _load_mkdisk()
        self.dh = _diskh_defines()
        with open(PACK, "rb") as f:
            self.pack = f.read()

    # A1 — the format IS BODYFS02, in disk.h (the C source of truth).
    def test_diskh_is_bodyfs02_with_path_names_and_many_entries(self):
        self.assertEqual(self.dh["BFS_MAGIC"], "BODYFS02", "the magic name is BODYFS02 (version 2)")
        self.assertEqual(self.dh["BFS_VERSION"], 2, "the format version is 2")
        self.assertTrue(self.dh["NAME_FIELD_IS_BFS_NAME_MAX"], "the entry name field is BFS_NAME_MAX wide")
        self.assertGreaterEqual(self.dh["BFS_NAME_MAX"], MEASURED_MAX_NAME,
                                "names hold paths to at least the 92-byte measured max")
        self.assertEqual(self.dh["BFS_NAME_MAX"], 128, "name[128] (the sized width)")
        entries = self.dh["BFS_DIR_SECTORS"] * (512 // self.dh["BFS_ENTRY_SIZE"])
        self.assertGreaterEqual(entries, MEASURED_MAX_PATHS,
                                "the entry table holds at least the 1,230 per-module max path count")
        self.assertEqual(entries, 2048, "2048 entries (the sized capacity)")

    # A8 — mkdisk.py mirrors disk.h byte-for-byte (an mkfs tool mirrors its filesystem driver).
    def test_mkdisk_mirror_agrees_with_diskh_lock_step(self):
        self.assertEqual(self.mk.MAGIC, b"BODYFS02", "mkdisk magic mirrors disk.h")
        self.assertEqual(self.mk.VERSION, self.dh["BFS_VERSION"], "mkdisk version mirrors disk.h")
        self.assertEqual(self.mk.NAME_MAX, self.dh["BFS_NAME_MAX"], "mkdisk NAME_MAX mirrors disk.h")
        self.assertEqual(self.mk.ENTRY_SIZE, self.dh["BFS_ENTRY_SIZE"], "mkdisk ENTRY_SIZE mirrors disk.h")
        self.assertEqual(self.mk.DIR_SECTORS, self.dh["BFS_DIR_SECTORS"], "mkdisk DIR_SECTORS mirrors disk.h")
        self.assertEqual(self.mk.MAX_ENTRIES, 2048, "mkdisk MAX_ENTRIES = 2048")
        self.assertEqual(512 % self.mk.ENTRY_SIZE, 0, "the entry size divides a sector (2 per sector)")

    # A7 — a formatted image is SIZED to the per-module maximum (data region 64 MiB / 2048 / name 128).
    def test_formatted_image_is_sized_to_the_measurement(self):
        img, info = self.mk.build_image(self.pack)
        s = _parse_super(img)
        self.assertEqual(s["magic"], b"BODYFS02", "the formatted image's magic is BODYFS02")
        self.assertEqual(s["version"], 2, "the formatted image's version is 2")
        self.assertEqual(s["dir_sectors"], 1024, "the directory is 1024 sectors (2048 entries)")
        self.assertEqual(s["data_start"], 1025, "the data region begins after the directory")
        data_region_bytes = (s["total_sectors"] - s["data_start"]) * 512
        self.assertGreaterEqual(data_region_bytes, 64 * 1024 * 1024,
                                "the data region is at least 64 MiB (>= 1.9x the 34.16 MiB measured max)")
        self.assertEqual(data_region_bytes, 64 * 1024 * 1024, "the data region is exactly 64 MiB")
        self.assertEqual(s["dir_count"], 2, "the fresh image records 2 used entries (record + pack)")
        self.assertGreater(s["total_sectors"], s["next_free"],
                           "the staged content fits inside the sized data region")

    # A1 PLANT — a name longer than the field is REFUSED, never truncated; a path <= the field fits.
    def test_a_name_longer_than_the_field_is_refused_never_truncated(self):
        with self.assertRaises(ValueError):
            self.mk._entry("x" * (self.mk.NAME_MAX + 1), self.mk.FT_BLOB, 1, 0, 0, 1, 0, 0)
        # a 92-byte path (the measured longest) and a full-width 128-byte name both fit, as 256-byte entries.
        e92 = self.mk._entry("p" * MEASURED_MAX_NAME, self.mk.FT_BLOB, 1, 0, 0, 1, 0, 0)
        e128 = self.mk._entry("p" * self.mk.NAME_MAX, self.mk.FT_BLOB, 1, 0, 0, 1, 0, 0)
        self.assertEqual(len(e92), self.mk.ENTRY_SIZE, "a 92-byte path is stored, not refused")
        self.assertEqual(len(e128), self.mk.ENTRY_SIZE, "a full-width name fills the field")
        # never truncated-and-collided: the 92-byte name reads back whole from its entry.
        self.assertEqual(e92[:MEASURED_MAX_NAME], b"p" * MEASURED_MAX_NAME, "the path is stored whole")

    # A8 — ATTESTED holds at 88 (all files edit-in-place, no new .c); the built artifacts are never members.
    def test_attested_holds_at_88_and_the_format_files_are_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "no new .c in this slice: ATTESTED stays 88")
        for rel in ("body/disk.h", "body/bodyfs.c", "body/mkdisk.py"):
            self.assertIn(rel, ATTESTED_MEMBERS, "%s (edited in place) is an attested member" % rel)
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "the built .elf / .img are never signed members (§9 mechanism 3)")


# ── the nested-guest bridge (A1 boot cases only) ───────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b5ai-accept"


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


def _seed_guest():
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(outdir):
    _seed_guest()
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s" % (_WD, _WD, outdir)],
                       capture_output=True, timeout=120)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    return outdir


def _guest_mkdisk(img):
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img):
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL 30 qemu-system-x86_64 -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 -serial stdio -display none -no-reboot "
                "-m 256 </dev/null 2>/dev/null; true" % (outdir, img)],
        capture_output=True, timeout=60)
    return boot.stdout.decode(errors="replace")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestBodyfs02BootsAndRefusesBodyfs01(unittest.TestCase):
    def test_the_grown_format_mounts_and_the_five_acts_pass_properties_held(self):
        # A1: the body built with the grown disk.h/bodyfs.c mounts a BODYFS02 image and the five
        # record acts PASS — the append-only / write-once / one-writer properties held on the grown
        # format (the P3b-2 checks, on BODYFS02). The twelve rows' digest is still announced.
        out = _guest_build(_WD + "/out")
        img = _guest_mkdisk(_WD + "/disk-02.img")
        serial = _guest_boot(out, img)
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("DISK: OK", serial, "the BODYFS02 image mounts on the metal")
        self.assertIn("ACTS: PASS", serial, "the five record acts pass on the grown format (L14)")
        self.assertIn("CHECK RECORD-PEN: PASS", serial, "append-only property held")
        self.assertIn("CHECK ATOMIC-WRITE-ONCE: PASS", serial, "write-once property held")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c) still announced")
        self.assertRegex(serial, r"ROWS-DIGEST: sha256:[0-9a-f]{64}", "the rows digest is on serial")

    def test_a_bodyfs01_image_is_refused_at_mount_by_name(self):
        # A1 PLANT: an image whose magic name is the OLD "BODYFS01" (everything else valid) is REFUSED
        # at mount by name — the magic check in fs_mount fires first. Not silently reinterpreted, not a
        # fabricated success: the body announces DISK: FS-FAIL and never runs the acts on it.
        out = _guest_build(_WD + "/out")
        good = _guest_mkdisk(_WD + "/disk-02b.img")
        bad = _WD + "/disk-01.img"
        # copy the valid BODYFS02 image and overwrite ONLY its 8-byte magic with the old name.
        patch = ("cp %s %s && python3 - %s <<'PY'\n"
                 "import sys\n"
                 "p=sys.argv[1]\n"
                 "f=open(p,'r+b'); f.seek(0); f.write(b'BODYFS01'); f.close()\n"
                 "PY" % (good, bad, bad))
        r = subprocess.run(_SSH + [patch], capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, "the BODYFS01 plant image was written: "
                         + r.stderr.decode(errors="replace"))
        serial = _guest_boot(out, bad)
        self.assertIn("DISK: FS-FAIL", serial, "a BODYFS01 image is refused at mount by name")
        self.assertNotIn("DISK: OK", serial, "the old format is NOT silently reinterpreted as BODYFS02")
        # the DISK self-check (CHECK RECORD-PEN ...) prints ONLY inside the DISK: OK branch, so its
        # absence proves the five acts never ran on the refused image — no fabricated success. (A bare
        # "ACTS: PASS" would wrongly match the -ACTS: PASS tail of SERVE-ACTS / ENCLOSURE-ACTS / CLOCK-ACTS.)
        self.assertNotIn("CHECK RECORD-PEN", serial,
                         "the disk self-check never runs on a refused image (no fabricated success)")


if __name__ == "__main__":
    unittest.main()
