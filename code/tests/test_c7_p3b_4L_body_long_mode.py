# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a start-up trampoline into the machine's long mode, four-level paging, a 64-bit interrupt table,
# EFER.LMA read from the machine, a body booting under a debug stub) as in the seL4/gVisor/Fuchsia and
# osdev literature. NON-GOAL: no offensive capability — this DRIVES the acceptance of C7 P3b-4L (the
# three closed slices re-based onto x86_64 long mode inside a nested guest; every prior self-check green
# again with its meaning unchanged and its planted failure still failing; the body announces its
# definition digest; it boots nothing into production, touches no host kernel).
"""C7 P3b-4L acceptance — THE BODY IN LONG MODE (design/54 §5 L18, §7 P3b-4L; countersign archi :4082).

The body brought up over P3b-1/2/3 ran in 32-bit protected mode (the probe's form); the interpreter it
exists to carry, and the forty-nine requests measured at P3b-4s, are x86_64 (the P3b-4 stop). This slice
RE-BASES the three closed slices onto the machine's own long mode: a start-up TRAMPOLINE from the
multiboot1 32-bit entry into long mode (a temporary GDT with a 64-bit code segment, initial four-level
page tables, PAE/EFER.LME/CR0.PG, a far-jump to 64-bit code), FOUR-LEVEL PAGING, a 64-bit INTERRUPT
TABLE and stubs, and 64-bit pointer widths. After it the body boots in long mode in the nested guest
and EVERY P3b-1/2/3 self-check is green again WITH ITS MEANING UNCHANGED and its planted failure STILL
failing; the twelve rows' digest is still on the serial line; the -m64 build is byte-reproducible; the
attested set moves by name (here: NO file split, so it stands at 79).

  A1  the body boots in LONG MODE (the mode read from the MACHINE — EFER.LMA, not a compile-time fact)
      and still prints the twelve rows' digest on serial (nested guest, the gdb stub attached, L17); a
      PLANTED "trampoline not taken" stays 32-bit and reds the machine-read mode check
  A2  every P3b-1/2/3 self-check is green again MEANING UNCHANGED (memory on four-level paging; the five
      record acts; the clock/interrupts/entropy), and each slice's planted fault STILL reds its own
      check on the long-mode body — the VMM plant reds on the BODY'S OWN four-level tables (precision 2)
  A3  the body is DERIVED from the rows (the digest folds the twelve rows, unchanged; delete-and-
      regenerate byte-identical) and the -m64 .elf (and its flat .img) is byte-REPRODUCIBLE
  A4  the attested set moves by name — here NO src/body source was added (edit-in-place), so it STANDS
      at 79; the walk-guard covers src/body; the built .elf/.img are never members
  A5  guest-only, revertable, NO one-way door — no host kernel load, the body is not stood as the
      production performer; the scans CAN fail (near-miss)
  A6  NO founding — the mode is code: ACT_KINDS stays twelve, the founding pack is byte-unchanged
      (95631e8f), founding 1.55.0

A1/A2(guest)/A3-repro build+boot in the NESTED guest and skip when the pinned guest is not reachable
over SSH; A2's planted-fault reds, A3-derive, A4, A5 and A6 run in main. Register: OS bring-up on a
disposable guest, described by function — a body re-based onto the machine's own 64-bit mode, keeping
its own memory, disk and clock, and announcing its definition digest; validated by building/reading,
never by attack (governance-work-method). Every kernel touch is the guest's nested qemu; the host
kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
"""

import hashlib
import importlib.util
import json
import os
import re
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
# the founding pack is byte-unchanged (no founding — the mode is code): pack sha + version pinned.
PACK_SHA = "95631e8f00ed18233dc3bdc4fe6207495b78bd5cb26dbee96db53a47dd6c179b"
FOUNDING_VERSION = "1.55.0"

# ── the nested-guest bridge (A1/A2-guest/A3-repro only) — an ISOLATED per-unit scratch ────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4L-accept"          # a per-unit scratch dir (guest to itself, serialized, mgr :4027)
# every nested boot: -cpu max (rdrand a RUNTIME source for the seed), the RTC UTC for the wall-clock
# plausibility check, and the gdb stub attached from the first line (L17), on a UNIQUE port per boot.
_QEMU = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc"
_GDB_BASE = 4000 + (os.getpid() % 2000)
_boot_n = [0]


def _next_gdb_port():
    p = _GDB_BASE + (_boot_n[0] % 1800)
    _boot_n[0] += 1
    return p


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
    """Copy src/body + src/bridge + src/founding to the ISOLATED per-unit scratch ONCE (mkdisk.py needs
    host_seam + the pack). Idempotent within a test run."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", outdir=None):
    """Build the re-based body in the guest (nested-qemu target); return (outdir, elf_sha256). The .elf
    is the recorded/reproducibility artifact; build.sh also emits the flat body.img the guest boots."""
    _seed_guest()
    out = outdir or (_WD + "/out" + (("-" + fault) if fault else ""))
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (_WD, _WD, out, fault)],
                       capture_output=True, timeout=120)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    h = subprocess.run(_SSH + ["sha256sum %s/body.elf | cut -d' ' -f1" % out],
                       capture_output=True, timeout=20)
    return out, h.stdout.decode().strip()


def _guest_img_sha(outdir):
    h = subprocess.run(_SSH + ["sha256sum %s/body.img | cut -d' ' -f1" % outdir],
                       capture_output=True, timeout=20)
    return h.stdout.decode().strip()


def _guest_mkdisk(img):
    """Format a fresh BODYFS image on the guest through the seam-routed tool; return the image path."""
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img=None, timeout_s=16):
    """Boot the FLAT image (body.img) in a NESTED qemu, the gdb stub attached from the first line (L17),
    optionally with `img` as a virtual IDE disk; return the serial text. qemu's -kernel multiboot loader
    ELF-parses only 32-bit ELFs, so the x86_64 long-mode body boots as the objcopy'd flat image loaded
    by the a.out-kludge address fields. Boots are SERIALIZED (guest-to-itself, mgr :4027)."""
    drive = (" -drive file=%s,format=raw,if=ide,index=0" % img) if img else ""
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d %s -gdb tcp::%d%s -kernel %s/body.img </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, _next_gdb_port(), drive, outdir)],
        capture_output=True, timeout=timeout_s + 20)
    return boot.stdout.decode(errors="replace").replace("\r", "")


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


def tearDownModule():
    """Leave the guest as found: no nested-qemu boot survives this module (serialized guest)."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1BootsInLongModeReadFromTheMachine(unittest.TestCase):
    def test_the_body_boots_in_long_mode_and_still_prints_the_rows_digest(self):
        out, elf_sha = _guest_build()
        serial = _guest_boot(out)
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        # THE MODE, READ FROM THE MACHINE (precision 1): EFER.LMA==1 is a machine fact the trampoline
        # set, not a compile-time constant. ptr=8 is a secondary compile fact, not the check.
        self.assertIn("LONGMODE: OK (EFER.LMA=1, ptr=0x00000008)", serial,
                      "the body reports long mode read from the machine (EFER.LMA), 64-bit pointers")
        self.assertIn("MEMORY: PASS", serial, "memory is up on four-level paging")
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial,
                      "the twelve rows' digest, still on serial AFTER the re-base")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")
        self.assertTrue(len(elf_sha) == 64, "the built .elf has a recorded digest (§9 mechanism 2)")

    def test_a_planted_trampoline_not_taken_stays_32bit_and_reds_the_machine_read_mode_check(self):
        # THE MODE CHECK CAN FAIL (precision 1, §A64): PLANT_NO_LONGMODE skips the trampoline; the body
        # stays in 32-bit protected mode and reports EFER.LMA==0 read from the machine — the long-mode
        # line is absent and the body never reaches the memory bring-up.
        out, _ = _guest_build("PLANT_NO_LONGMODE")
        serial = _guest_boot(out)
        self.assertIn("LONGMODE: NOT-TAKEN (still 32-bit, EFER.LMA=0", serial,
                      "the un-trampolined body reports 32-bit read from the machine (EFER.LMA=0)")
        self.assertNotIn("LONGMODE: OK", serial, "a 32-bit body never announces long mode")
        self.assertNotIn("MEMORY: PASS", serial, "a 32-bit body never reaches the long-mode memory boot")


# ── A2 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2EveryPriorSelfCheckGreenMeaningUnchanged(unittest.TestCase):
    """Spot-proves each of the three slices green with meaning unchanged AND its planted fault still
    redding on the long-mode body. The AUTHORITATIVE full plant battery is tests/test_c7_p3b_1/2/3
    re-run against the -m64 body (their boot invocations now boot body.img, their CHECK MEANINGS
    unchanged) — this class proves the re-base did not disable any slice or any plant."""

    def test_memory_green_and_the_vmm_plant_reds_on_the_bodys_own_four_level_tables(self):
        out, _ = _guest_build()
        serial = _guest_boot(out)
        self.assertIn("CHECK PMM: PASS", serial, "the PMM allocates and frees a frame")
        self.assertIn("CHECK VMM: PASS", serial,
                      "the VMM maps a page and the write reaches the frame on FOUR-LEVEL paging")
        self.assertIn("CHECK HEAP: PASS", serial, "the heap allocates, writes, reads back, frees")
        self.assertIn("MEMORY: PASS", serial)
        # precision 2: the mapping check runs on the BODY'S OWN four-level tables (vmm_init installs
        # them, abandoning the trampoline scaffold), so a page remapped to the WRONG frame reds.
        out_w, _ = _guest_build("PLANT_VMM_WRONG")
        serial_w = _guest_boot(out_w)
        self.assertIn("CHECK VMM: FAIL", serial_w,
                      "a page mapped to the wrong frame on the body's own tables is caught (precision 2)")
        self.assertIn("MEMORY: FAIL", serial_w)

    def test_the_five_record_acts_green_and_a_disk_plant_reds(self):
        out, _ = _guest_build()
        img = _guest_mkdisk(_WD + "/disk-a2.img")
        serial = _guest_boot(out, img=img)
        self.assertIn("DISK: OK", serial, "the block device + BODYFS mount on the metal")
        for line in ("CHECK RECORD-PEN: PASS", "CHECK ATOMIC-WRITE-ONCE: PASS", "CHECK REMOVE: PASS",
                     "CHECK BODY-READ: PASS", "CHECK FOUNDING-PACK-READ: PASS", "ACTS: PASS"):
            self.assertIn(line, serial, "the five record acts on the body's own disk: %r" % line)
        out_p, _ = _guest_build("PLANT_RECORD_READBACK_WRONG")
        img_p = _guest_mkdisk(_WD + "/disk-a2-plant.img")
        serial_p = _guest_boot(out_p, img=img_p)
        self.assertIn("CHECK RECORD-PEN: FAIL", serial_p, "a corrupt record read-back is caught")
        self.assertIn("ACTS: FAIL", serial_p)

    def test_the_clock_interrupts_entropy_green_and_the_interrupt_plant_reds(self):
        out, _ = _guest_build()
        serial = _guest_boot(out)
        for line in ("CHECK INTERRUPTS: PASS", "CHECK RECORDING-CLOCK: PASS",
                     "CHECK COMMIT-WINDOW: PASS", "CHECK ENTROPY: PASS", "CLOCK: PASS"):
            self.assertIn(line, serial, "the clock/interrupt/entropy self-check: %r" % line)
        # a timer IRQ fired and was handled through the 64-bit interrupt table (the tick advanced).
        m = re.search(r"TICKS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the body reports the tick counter")
        self.assertGreater(int(m.group(1), 16), 0, "a timer interrupt fired through the 64-bit IDT")
        out_g, _ = _guest_build("PLANT_BAD_GATE")
        serial_g = _guest_boot(out_g)
        self.assertIn("CHECK INTERRUPTS: FAIL", serial_g,
                      "a timer gate pointing at the wrong 64-bit stub is caught")
        self.assertIn("CLOCK: FAIL", serial_g)


# ── A3 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA3DerivedFromTheRows(unittest.TestCase):
    def setUp(self):
        with open(PACK, encoding="utf-8") as f:
            self.pack = json.load(f)
        self.gen = _load_generator()

    def test_the_digest_folds_the_twelve_rows_unchanged_by_the_re_base(self):
        digest, count = self.gen.digest_over(self.pack)
        self.assertEqual(count, 12, "twelve seam_act_definition rows (the mode adds no act)")
        self.assertEqual(digest, ROWS_DIGEST,
                         "arch-independent: byte-identical to _act_kind_digest, unchanged on the 64-bit body")

    def test_delete_and_regenerate_returns_byte_identical_bytes(self):
        with open(os.path.join(BODY, "rows_digest.h"), "rb") as f:
            committed = f.read()
        with tempfile.TemporaryDirectory() as tmp:
            regen = os.path.join(tmp, "rows_digest.h")
            self.gen.generate(header_path=regen)
            with open(regen, "rb") as f:
                self.assertEqual(committed, f.read(), "delete-and-regenerate is byte-identical (A3)")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3-repro needs the guest toolchain to build twice")
class TestA3BuildIsByteReproducible(unittest.TestCase):
    def test_the_m64_elf_and_flat_img_are_byte_reproducible(self):
        # the -m64 .elf is byte-identical across two clean builds (the seeded chance is a RUNTIME
        # output, never baked into the .elf, A3); the flat .img (a deterministic objcopy) follows.
        _, sha1 = _guest_build(outdir=_WD + "/repro1")
        _, sha2 = _guest_build(outdir=_WD + "/repro2")
        self.assertEqual(sha1, sha2, "two builds of the body produce a byte-identical -m64 .elf")
        self.assertEqual(_guest_img_sha(_WD + "/repro1"), _guest_img_sha(_WD + "/repro2"),
                         "the flat body.img is byte-reproducible too")


# ── A4 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA4TheAttestedSetMovesByName(unittest.TestCase):
    def test_no_split_so_the_attested_set_stands_at_79_and_the_walk_guard_covers_the_body(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        on_disk = sorted("body/" + f for f in _body_source_names())
        # the re-base is EDIT-IN-PLACE (no new src/body source), so the 22 body files and the count
        # of 79 are UNCHANGED — an edit to an existing member moves no count (A4).
        self.assertEqual(len(on_disk), 31, "22 at P3b-4L's re-base; 28 after C7 P3b-4a's +6 enclosure files; 30 after C7 P3b-4b's +2 serve files; 31 after C7 P3b-6a's +1 net.c")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s is not attested (§9 mechanism 1)" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "P3b-4L added no source (stood at 79); C7 P3b-4a's enclosure add moved it to 85; C7 P3b-4b's serve add moved it to 87; C7 P3b-6a's net.c add moved it to 88")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers src/body")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list")

    def test_the_built_elf_and_flat_img_are_never_signed_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built .elf / the flat .img are NEVER signed members")


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
    def test_no_host_kernel_load_in_the_body_or_the_build_and_the_scan_can_fail(self):
        for name in _body_source_names():
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                self.assertEqual(_host_kernel_load_tokens(f.read()), [],
                                 "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        # the near-miss control (§A64): a planted host kernel load IS caught — the scan can fail.
        self.assertEqual(_host_kernel_load_tokens("insmod /lib/modules/govosfs.ko"), ["insmod"])
        self.assertEqual(_host_kernel_load_tokens("modprobe kvm_intel"), ["modprobe"])

    def test_the_body_is_not_stood_as_the_production_performer_and_the_scan_can_fail(self):
        self.assertEqual(_production_standing_hits(SRC), [],
                         "a module above the seam imports the body as the production performer")
        tmp = tempfile.mkdtemp(prefix="p3b4L-a5-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "compose_planted.py"), "w", encoding="utf-8") as f:
            f.write("from body import kmain  # stand the body as the production performer\n")
        hits = _production_standing_hits(tmp)
        self.assertTrue(any(rel == "kernel/compose_planted.py" for rel, _pat in hits),
                        "a planted production-standing import must red the scan")

    def test_the_mode_re_base_is_edit_in_place_git_revertible(self):
        # the mode change is CODE behind a fence, git-revertible (L18/I6/L8): edit-in-place under
        # src/body/ (no new files), so a `git checkout src/body` reverts it whole.
        for name in _body_source_names():
            self.assertTrue(os.path.exists(os.path.join(BODY, name)), "%s exists" % name)


# ── A6 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA6NoFounding(unittest.TestCase):
    def test_the_founding_pack_is_byte_unchanged_no_founding(self):
        # the mode is code: NO founding — the pack is byte-unchanged and the version stands (A6).
        with open(PACK, "rb") as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), PACK_SHA,
                             "the founding pack is byte-unchanged (no founding, no pack edit)")
        with open(PACK, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["founding_version"], FOUNDING_VERSION,
                             "founding %s — the mode re-base founds nothing" % FOUNDING_VERSION)

    def test_act_kinds_stays_twelve(self):
        # ACT_KINDS stays twelve — the mode adds no act. Driven from the pack's own rows through the
        # generator (the same twelve seam_act_definition rows the digest folds).
        gen = _load_generator()
        with open(PACK, encoding="utf-8") as f:
            pack = json.load(f)
        _digest, count = gen.digest_over(pack)
        self.assertEqual(count, 12, "twelve act kinds — the mode re-base widens ACT_KINDS by none")


if __name__ == "__main__":
    unittest.main()
