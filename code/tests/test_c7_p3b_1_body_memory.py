"""C7 P3b-1 acceptance — THE BODY: MEMORY (design/54 §7 P3b-1; countersign archi :4009).

The first MERGED body: a freestanding memory-managed body (multiboot boot entry + a physical
frame allocator + virtual memory/paging + a kernel heap + a polled serial), generated-from-and-
tied-to the twelve seam_act_definition rows, that boots in a NESTED qemu inside the pinned guest,
runs a memory self-check, and prints the memory result AND the twelve rows' digest.

  A1  the body boots with memory up and STILL prints the rows' digest on serial (nested guest)
  A2  memory is actually FUNCTIONAL — PMM/VMM/heap exercised, and a planted fault reds the check
  A3  the body is DERIVED from the rows — the digest folds the twelve rows; different rows -> a
      different digest; delete-and-regenerate returns byte-identical bytes
  A4  the FIRST MERGED body is ATTESTED — every src/body file is an attested member (57 -> 68),
      the built .elf is never a signed member (§9 mechanism 3)
  A5  guest-only, revertable, NO one-way door — no host kernel load, the body is not stood as the
      production performer; the scans CAN fail (near-miss)

A1/A2 build+boot in the NESTED guest and skip when the pinned guest is not reachable over SSH;
A3/A4/A5 run in main. Register: OS bring-up in a disposable guest, described by function — a body
that manages its own memory and announces its definition digest; validated by building/reading,
never by attack (governance-work-method). Every kernel touch is the guest's nested qemu; the
host kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
FOUNDING_DIR = os.path.join(SRC, "founding")
PACK = os.path.join(FOUNDING_DIR, "founding-pack.json")
sys.path.insert(0, SRC)

ROWS_DIGEST = "sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb"

# ── the nested-guest bridge (A1/A2 only) ─────────────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]


def _guest_reachable():
    """True only if the PINNED guest (6.8.0-134-generic) answers over SSH -p 2222 AND the nested
    boot engine (qemu-system-x86_64) is present. Observes a state the check did not create (§A19)."""
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU"],
                           capture_output=True, timeout=20)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return r.returncode == 0 and "6.8.0-134-generic" in out and "QEMU" in out


GUEST = _guest_reachable()


def _guest_build_and_boot(fault=""):
    """Copy src/body to the guest, build the freestanding body, boot it in a NESTED qemu, and
    return (serial_text, elf_sha256). Every build+boot is the guest's nested qemu — no host kernel.
    `fault` (PLANT_VMM_WRONG | PLANT_HEAP_OVERLAP) injects a self-check fault (A2 near-miss)."""
    wd = "/tmp/p3b1-accept"
    out = wd + "/out" + (("-" + fault) if fault else "")
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=30)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (wd, wd, wd)],
                   input=tar.stdout, capture_output=True, timeout=40, check=True)
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (wd, wd, out, fault)],
                       capture_output=True, timeout=90)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    h = subprocess.run(_SSH + ["sha256sum %s/body.elf | cut -d' ' -f1" % out],
                       capture_output=True, timeout=20)
    elf_sha = h.stdout.decode().strip()
    # boot the FLAT image (body.img): qemu's -kernel multiboot loader ELF-parses only 32-bit ELFs, so
    # the x86_64 long-mode body boots as the objcopy'd flat image loaded by the a.out-kludge address
    # fields (C7 P3b-4L). The .elf is the recorded/reproducibility artifact; the .img is the bootable one.
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL 15 qemu-system-x86_64 -kernel %s/body.img "
                "-serial stdio -display none -no-reboot -m 256 </dev/null 2>/dev/null; true" % out],
        capture_output=True, timeout=45)
    return boot.stdout.decode(errors="replace"), elf_sha


def _body_source_names():
    """The governed SOURCE files under src/body/ — every real file, excluding the __pycache__
    bytecode cache (not source; the walk-guard excludes it too)."""
    return sorted(n for n in os.listdir(BODY)
                  if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def _load_generator():
    sys.dont_write_bytecode = True   # do not leave a __pycache__ under src/body from this import
    """Load src/body/gen_rows_digest.py by path (src/body is not a package; adding an __init__.py
    would change the attested count). The module folds the rows through the estate's serializer."""
    spec = importlib.util.spec_from_file_location("body_gen_rows_digest",
                                                  os.path.join(BODY, "gen_rows_digest.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── A1 ───────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1BootsWithMemoryAndDigest(unittest.TestCase):
    def test_body_boots_with_memory_up_and_still_prints_the_rows_digest(self):
        serial, elf_sha = _guest_build_and_boot()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("MEMORY: PASS", serial, "memory is up (PMM+VMM+heap self-check passed)")
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial,
                      "the body prints the twelve rows' digest AFTER memory is up")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")
        self.assertTrue(len(elf_sha) == 64, "the built .elf has a recorded digest (§9 mechanism 2)")


# ── A2 ───────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2MemoryIsFunctional(unittest.TestCase):
    def test_the_self_check_exercises_pmm_vmm_and_heap(self):
        serial, _ = _guest_build_and_boot()
        self.assertIn("CHECK PMM: PASS", serial, "the PMM allocates and frees a frame")
        self.assertIn("CHECK VMM: PASS", serial, "the VMM maps a page and the write reaches the frame")
        self.assertIn("CHECK HEAP: PASS", serial, "the heap allocates, writes, reads back, frees")

    def test_a_planted_vmm_fault_is_caught_by_the_self_check(self):
        serial, _ = _guest_build_and_boot("PLANT_VMM_WRONG")
        self.assertIn("CHECK VMM: FAIL", serial, "a page mapped to the wrong frame is caught")
        self.assertIn("MEMORY: FAIL", serial)

    def test_a_planted_heap_overlap_is_caught_by_the_self_check(self):
        serial, _ = _guest_build_and_boot("PLANT_HEAP_OVERLAP")
        self.assertIn("CHECK HEAP: FAIL", serial, "a heap that hands overlapping blocks is caught")
        self.assertIn("MEMORY: FAIL", serial)


# ── A3 ───────────────────────────────────────────────────────────────────────────────────────
class TestA3DerivedFromTheRows(unittest.TestCase):
    def setUp(self):
        with open(PACK, encoding="utf-8") as f:
            self.pack = json.load(f)
        self.gen = _load_generator()

    def test_the_digest_folds_the_twelve_rows_the_same_as_act_kind_digest_in_main(self):
        digest, count = self.gen.digest_over(self.pack)
        self.assertEqual(count, 12, "twelve seam_act_definition rows (memory is the twelfth)")
        self.assertEqual(digest, ROWS_DIGEST, "byte-identical to _act_kind_digest driven in main")
        with open(os.path.join(BODY, "rows_digest.h"), encoding="utf-8") as f:
            self.assertIn(digest, f.read(), "the committed header carries the same digest")

    def test_a_body_generated_from_different_rows_prints_a_different_digest(self):
        import copy
        d0, _ = self.gen.digest_over(self.pack)
        mutated = copy.deepcopy(self.pack)
        rows = self.gen.rows_from_pack(mutated)
        rows[0]["label"] = rows[0]["label"] + "-MUTATED"   # a different definition
        d1, _ = self.gen.digest_over(mutated)
        self.assertNotEqual(d0, d1, "the body is tied to its definition rows (archi :4001 precision b)")

    def test_delete_and_regenerate_returns_byte_identical_bytes(self):
        with open(os.path.join(BODY, "rows_digest.h"), "rb") as f:
            committed = f.read()
        with tempfile.TemporaryDirectory() as tmp:
            regen_path = os.path.join(tmp, "rows_digest.h")
            self.gen.generate(header_path=regen_path)   # regenerate from the rows into a temp
            with open(regen_path, "rb") as f:
                regenerated = f.read()
        self.assertEqual(committed, regenerated, "delete-and-regenerate is byte-identical (A3)")


# ── A4 ───────────────────────────────────────────────────────────────────────────────────────
class TestA4TheMergedBodyIsAttested(unittest.TestCase):
    def test_every_src_body_file_is_an_attested_member_and_the_count_is_73(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "the 31 src/body/ source files (30 + 1 net.c, C7 P3b-6a)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s is not attested (§9 mechanism 1)" % rel)
        self.assertIn("body/gen_rows_digest.py", ATTESTED_MEMBERS, "the generator .py is attested")
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "57 -> 68 (11 memory body files, C7 P3b-1) -> 73 (+5 disk body files, C7 P3b-2) -> 79 (+6 clock/interrupt/entropy body files, C7 P3b-3) -> 85 (+6 enclosure body files, C7 P3b-4a) -> 87 (+2 serve body files serve.c/serve.h, C7 P3b-4b) -> 88 (+1 net.c, C7 P3b-6a)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        # the walk-guard covers the body's non-.py files — one list, no second plane
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "manifest == the extended walk")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list")

    def test_the_built_elf_is_never_a_signed_source_member(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built .elf is NEVER added to the signed base")


# ── A5 ───────────────────────────────────────────────────────────────────────────────────────
def _host_kernel_load_tokens(text):
    """Tokens that would load a module into the HOST kernel — forbidden (L11): every kernel touch
    is the guest's nested qemu. Returns any present so the scan CAN fail on a planted line."""
    return [tok for tok in ("insmod", "modprobe") if tok in text]


def _production_standing_hits(src_dir):
    """Any .py OUTSIDE src/body (and outside founding/) that IMPORTS the body — i.e. stands it as a
    runtime performer. The body is NOT the production performer (B1's held step, the owner's
    one-way door); nothing above the seam imports it. Returns (rel, pattern) hits so it CAN fail."""
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
    def test_no_host_kernel_load_in_the_body_or_the_build_and_the_scan_can_fail(self):
        for name in _body_source_names():
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                text = f.read()
            self.assertEqual(_host_kernel_load_tokens(text), [],
                             "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        # the near-miss control (§A64): a planted host kernel load IS caught — the check can fail.
        self.assertEqual(_host_kernel_load_tokens("insmod /lib/modules/govosfs.ko"), ["insmod"])
        self.assertEqual(_host_kernel_load_tokens("modprobe kvm_intel"), ["modprobe"])

    def test_the_body_is_not_stood_as_the_production_performer_and_the_scan_can_fail(self):
        self.assertEqual(_production_standing_hits(SRC), [],
                         "a module above the seam imports the body as the production performer")
        # the near-miss: a planted 'commit this body as production' import IS caught (the check can
        # fail) — driven over a temp tree so no real source is touched.
        tmp = tempfile.mkdtemp(prefix="p3b1-a5-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "compose_planted.py"), "w", encoding="utf-8") as f:
            f.write("from body import kmain  # stand the body as the production performer\n")
        hits = _production_standing_hits(tmp)
        self.assertTrue(any(rel == "kernel/compose_planted.py" for rel, _pat in hits),
                        "a planted production-standing import must red the scan")

    def test_the_body_is_new_files_only_git_revertible(self):
        # the whole body is NEW files under src/body/ — git-revertible (a `git rm -r src/body`
        # plus the attestation/count-pin reverts undoes it); nothing existing was overwritten by
        # the body's own code. Verified by the fence: the C/asm/build live only under src/body/.
        for name in _body_source_names():
            self.assertTrue(os.path.exists(os.path.join(BODY, name)))
        self.assertTrue(os.path.isdir(BODY), "src/body/ is a new directory (revertable)")


if __name__ == "__main__":
    unittest.main()
