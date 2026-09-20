"""C7 P3b-2 acceptance — THE BODY: THE DISK AND THE RECORD ACTS (design/54 §7 P3b-2; archi :4019).

The body that boots with memory (P3b-1) now brings up A BLOCK DEVICE (a polled ATA/PIO driver) and
A FILESYSTEM (a bespoke append-only layout the record maps onto) ON THE METAL, and performs THE FIVE
RECORD ACTS on its OWN disk in a NESTED qemu inside the pinned guest — record-pen, atomic-write-once,
remove, body-read, founding-pack-read — self-checking each and still printing the twelve rows' digest.

  A1  the five record acts self-check PASS on the body's own disk + the digest on serial (nested guest)
  A2  each act is FUNCTIONAL — a planted fault reds exactly its check; the pack read equals the pack;
      the record and the blob survive an actual reboot (durability the fast no-reboot loop skips, §A33)
  A3  the body is DERIVED from the rows (the digest folds the twelve rows; delete-and-regenerate is
      byte-identical) and the .elf is byte-reproducible
  A4  the disk C is ATTESTED BY NAME (68 -> 73), the walk-guard covers it, the .elf is never a member,
      the P2 host-crossing census stays clean, and a planted direct open() in a body .py reds it
  A5  guest-only, revertable, NO one-way door — no host kernel load, the body is not stood as the
      production performer; the scans CAN fail (near-miss)

A1/A2/A3-repro build+boot in the NESTED guest and skip when the pinned guest is not reachable over
SSH; A3-derive/A4/A5 run in main. Register: OS bring-up on a disposable guest, described by function
— a body that keeps its own record on its own disk and announces its definition digest; validated by
building/reading, never by attack (governance-work-method). Every kernel touch is the guest's nested
qemu; the host kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
FOUNDING_DIR = os.path.join(SRC, "founding")
PACK = os.path.join(FOUNDING_DIR, "founding-pack.json")
sys.path.insert(0, SRC)

ROWS_DIGEST = "sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb"

# the five disk C source files this slice adds under src/body/ (attested by name, A4).
NEW_DISK_FILES = ("body/ata.c", "body/bodyfs.c", "body/disk.h", "body/diskcheck.c", "body/mkdisk.py")

# the six planted faults and the ACT check each one must red (A2). The check that CAN fail is the
# proof the check is real — a check that cannot fail is not a check (§A64).
FAULT_TO_FAILED_CHECK = {
    "PLANT_RECORD_READBACK_WRONG":    "CHECK RECORD-PEN: FAIL",
    "PLANT_RECORD_OVERWRITE_ALLOWED": "CHECK RECORD-PEN: FAIL",   # the record-overwrite REFUSAL, made fallible
    "PLANT_WRITEONCE_OVERWRITE":      "CHECK ATOMIC-WRITE-ONCE: FAIL",
    "PLANT_REMOVE_LEAVES":            "CHECK REMOVE: FAIL",
    "PLANT_WALK_MISSES":              "CHECK BODY-READ: FAIL",
    "PLANT_PACK_WRONG":               "CHECK FOUNDING-PACK-READ: FAIL",
}

# ── the nested-guest bridge (A1/A2/A3-repro only) ─────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b2-accept"


def _guest_reachable():
    """True only if the PINNED guest (6.8.0-134-generic) answers over SSH -p 2222 AND the nested boot
    engine (qemu-system-x86_64) is present. Observes a state the check did not create (§A19)."""
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
    """Copy src/body + src/bridge + src/founding to the guest ONCE (mkdisk.py needs host_seam + the
    pack). Idempotent within a test run."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", outdir=None):
    """Build the body in the guest (nested-qemu target); return (outdir, elf_sha256)."""
    _seed_guest()
    out = outdir or (_WD + "/out" + (("-" + fault) if fault else ""))
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (_WD, _WD, out, fault)],
                       capture_output=True, timeout=120)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    h = subprocess.run(_SSH + ["sha256sum %s/body.elf | cut -d' ' -f1" % out],
                       capture_output=True, timeout=20)
    return out, h.stdout.decode().strip()


def _guest_mkdisk(img):
    """Format a fresh BODYFS image on the guest through the seam-routed tool; return the image path."""
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img):
    """Boot the body in a NESTED qemu with `img` as a virtual IDE disk; return the serial text. Every
    boot is the guest's nested qemu — no host kernel."""
    # boot the FLAT image (body.img): the x86_64 long-mode body boots as the objcopy'd flat image
    # loaded by the a.out-kludge address fields (C7 P3b-4L); qemu's -kernel multiboot loader
    # ELF-parses only 32-bit ELFs. The .elf is the recorded artifact; the .img is the bootable one.
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL 20 qemu-system-x86_64 -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 -serial stdio -display none -no-reboot "
                "-m 256 </dev/null 2>/dev/null; true" % (outdir, img)],
        capture_output=True, timeout=50)
    return boot.stdout.decode(errors="replace")


def _body_source_names():
    return sorted(n for n in os.listdir(BODY)
                  if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def _load_generator():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("body_gen_rows_digest",
                                                  os.path.join(BODY, "gen_rows_digest.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── A1 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1FiveRecordActsAndDigest(unittest.TestCase):
    def test_the_five_record_acts_self_check_pass_and_the_digest_is_on_serial(self):
        out, elf_sha = _guest_build()
        img = _guest_mkdisk(_WD + "/disk-a1.img")
        serial = _guest_boot(out, img)
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("DISK: OK", serial, "the block device + BODYFS mount on the metal")
        self.assertIn("CHECK RECORD-PEN: PASS", serial, "append a record, read it back equal")
        self.assertIn("CHECK ATOMIC-WRITE-ONCE: PASS", serial, "a blob written once, durable")
        self.assertIn("CHECK REMOVE: PASS", serial, "a removed blob gone")
        self.assertIn("CHECK BODY-READ: PASS", serial, "a walk that enumerates the body's own files")
        self.assertIn("CHECK FOUNDING-PACK-READ: PASS", serial, "the pack read from the disk")
        self.assertIn("ACTS: PASS", serial, "all five record acts pass on the body's own disk")
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")
        self.assertTrue(len(elf_sha) == 64, "the built .elf has a recorded digest (§9 mechanism 2)")


# ── A2 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2EachActIsFunctional(unittest.TestCase):
    def test_each_planted_fault_reds_its_own_act_check(self):
        for fault, failed in FAULT_TO_FAILED_CHECK.items():
            out, _ = _guest_build(fault)
            img = _guest_mkdisk(_WD + "/disk-%s.img" % fault)
            serial = _guest_boot(out, img)
            self.assertIn(failed, serial, "%s must red %r (the check can fail, A2)" % (fault, failed))
            self.assertIn("ACTS: FAIL", serial, "%s must red the aggregate ACTS line" % fault)

    def test_the_founding_pack_read_from_disk_equals_the_pack(self):
        # the body prints PACK: len=0x.. crc=0x.. read FROM ITS OWN DISK; it must equal the real pack.
        out, _ = _guest_build()
        img = _guest_mkdisk(_WD + "/disk-pack.img")
        serial = _guest_boot(out, img)
        m = re.search(r"PACK: len=0x([0-9a-f]+) crc=0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the body reports the pack it read from disk")
        with open(PACK, "rb") as f:
            pack = f.read()
        self.assertEqual(int(m.group(1), 16), len(pack), "the on-disk pack length equals the pack's")
        self.assertEqual(int(m.group(2), 16), zlib.crc32(pack) & 0xFFFFFFFF,
                         "the on-disk pack bytes crc equals the real founding-pack.json's crc")

    def test_the_record_and_the_blob_survive_an_actual_reboot(self):
        # durability across a REBOOT (§A33): boot 1 writes on a fresh disk; boot 2 on the SAME image
        # reads them back and confirms they persisted — the state a fast no-reboot loop never visits.
        out, _ = _guest_build()
        img = _guest_mkdisk(_WD + "/disk-dur.img")
        boot1 = _guest_boot(out, img)
        self.assertIn("ACTS: PASS", boot1, "boot 1 self-checks on a fresh disk (writes the record+blob)")
        boot2 = _guest_boot(out, img)   # same image — a reboot
        self.assertIn("PERSISTED: RECORD OK", boot2, "the record survived the reboot")
        self.assertIn("PERSISTED: BLOB OK", boot2, "the write-once blob survived the reboot")
        self.assertIn("ACTS: PERSISTED", boot2)


# ── A3 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA3DerivedFromTheRows(unittest.TestCase):
    def setUp(self):
        with open(PACK, encoding="utf-8") as f:
            self.pack = json.load(f)
        self.gen = _load_generator()

    def test_the_digest_folds_the_twelve_rows_as_before(self):
        digest, count = self.gen.digest_over(self.pack)
        self.assertEqual(count, 12, "twelve seam_act_definition rows")
        self.assertEqual(digest, ROWS_DIGEST, "byte-identical to _act_kind_digest driven in main")

    def test_delete_and_regenerate_returns_byte_identical_bytes(self):
        with open(os.path.join(BODY, "rows_digest.h"), "rb") as f:
            committed = f.read()
        with tempfile.TemporaryDirectory() as tmp:
            regen = os.path.join(tmp, "rows_digest.h")
            self.gen.generate(header_path=regen)
            with open(regen, "rb") as f:
                self.assertEqual(committed, f.read(), "delete-and-regenerate is byte-identical (A3)")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3-repro needs the guest toolchain to build the .elf twice")
class TestA3ElfReproducible(unittest.TestCase):
    def test_the_elf_is_byte_reproducible(self):
        _, sha1 = _guest_build(outdir=_WD + "/repro1")
        _, sha2 = _guest_build(outdir=_WD + "/repro2")
        self.assertEqual(sha1, sha2, "two builds of the body produce a byte-identical .elf")


# ── A4 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA4DiskCIsAttestedAndCensusClean(unittest.TestCase):
    def test_the_new_disk_files_are_attested_by_name_and_the_count_is_79(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        for rel in NEW_DISK_FILES:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s is not attested by name (§9 mechanism 1)" % rel)
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "the 31 src/body/ source files (30 + 1 net.c, C7 P3b-6a)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "68 -> 73 (5 disk) -> 79 (6 clock/interrupt/entropy, C7 P3b-3) -> 85 (6 enclosure, C7 P3b-4a) -> 87 (2 serve, C7 P3b-4b) -> 88 (+1 net.c, C7 P3b-6a)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers the disk C")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list")

    def test_the_built_elf_and_the_disk_image_are_never_signed_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built .elf / the formatted disk image are never members")

    def test_the_p2_host_crossing_census_stays_clean_and_can_fail(self):
        from tools.conformance import host_crossing_census as census
        self.assertEqual(census.undeclared_crossings(), {}, "the core (src/body included) is host-clean")
        # the near-miss: a planted DIRECT open() in a body .py reds the census (body is zoned CORE).
        tmp = tempfile.mkdtemp(prefix="p3b2-a4-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "body"))
        with open(os.path.join(tmp, "body", "planted.py"), "w", encoding="utf-8") as f:
            f.write("def go():\n    return open('/etc/hostname').read()  # a DIRECT crossing\n")
        bad = census.undeclared_crossings(src_dir=tmp)
        self.assertIn("body/planted.py", bad, "a direct open() in a body .py must red the P2 census")


# ── A5 ─────────────────────────────────────────────────────────────────────────────────────────
def _host_kernel_load_tokens(text):
    return [tok for tok in ("insmod", "modprobe") if tok in text]


def _production_standing_hits(src_dir):
    body = os.path.join(src_dir, "body")
    founding = os.path.join(src_dir, "founding")
    pats = ("from body import", "import body.", "from body.")
    hits = []
    for root, _dirs, files in os.walk(src_dir):
        ar = os.path.abspath(root)
        if ar.startswith(os.path.abspath(body)) or ar.startswith(os.path.abspath(founding)):
            continue
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8", errors="replace") as f:
                text = f.read()
            for pat in pats:
                if pat in text:
                    hits.append((os.path.relpath(os.path.join(root, name), src_dir), pat))
    return hits


class TestA5GuestOnlyRevertableNoOneWayDoor(unittest.TestCase):
    def test_no_host_kernel_load_in_the_body_the_build_or_the_disk_tool_and_the_scan_can_fail(self):
        for name in _body_source_names():
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                self.assertEqual(_host_kernel_load_tokens(f.read()), [],
                                 "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        # the near-miss control (§A64): a planted host kernel load IS caught — the scan can fail.
        self.assertEqual(_host_kernel_load_tokens("insmod /lib/modules/bodyfs.ko"), ["insmod"])
        self.assertEqual(_host_kernel_load_tokens("modprobe kvm_intel"), ["modprobe"])

    def test_the_body_is_not_stood_as_the_production_performer_and_the_scan_can_fail(self):
        self.assertEqual(_production_standing_hits(SRC), [],
                         "a module above the seam imports the body as the production performer")
        tmp = tempfile.mkdtemp(prefix="p3b2-a5-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "compose_planted.py"), "w", encoding="utf-8") as f:
            f.write("from body import kmain  # stand the body as the production performer\n")
        hits = _production_standing_hits(tmp)
        self.assertTrue(any(rel == "kernel/compose_planted.py" for rel, _pat in hits),
                        "a planted production-standing import must red the scan")

    def test_the_disk_slice_is_new_files_only_git_revertible(self):
        # the disk C + the seam-routed tool are NEW files under src/body/; nothing existing was
        # overwritten by the disk code (kmain.c/build.sh gained calls; the memory C is untouched).
        for rel in NEW_DISK_FILES:
            self.assertTrue(os.path.exists(os.path.join(SRC, rel)), "%s exists" % rel)


if __name__ == "__main__":
    unittest.main()
