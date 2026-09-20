# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a higher-half kernel, a direct map of physical memory in the higher half, a supervisor identity map
# withdrawn from the program's range, a user page mappable at the platform's canonical base, an ET_EXEC
# worker re-linked to that base) as in the seL4/gVisor/Fuchsia and osdev literature. NON-GOAL: no
# offensive capability — this DRIVES the acceptance of C7 P3b-4m (the body laid out to fit the program it
# hosts: the ordinary low addresses left to the program, the body's own workings kept beneath it and
# reached through its own high view of memory; it boots nothing into production, touches no host kernel;
# every boot is the guest's nested qemu).
"""C7 P3b-4m acceptance — THE ADDRESS SPACE LAID OUT FOR THE PROGRAM (design/54 §5 L20, §7 P3b-4m;
countersign archi :4126, two by-name precisions).

The long-mode body (P3b-4L) identity-mapped the low gigabyte as its own SUPERVISOR memory and mapped user
pages only ABOVE it (the P3b-4a worker linked at 1 GiB for that reason). An ordinary program — the
interpreter included (ET_EXEC first LOAD at 0x400000, driven) — loads at the platform's canonical base
INSIDE that supervisor gigabyte and cannot be moved. This slice RE-LAYS the body as a HIGHER-HALF KERNEL:

  - the body's OWN DIRECT MAP of physical memory installed in the higher half (DIRECT_MAP_BASE + phys),
    and EVERY frame access moved to it (page tables, the PMM, the heap's/enclosure's frames);
  - the supervisor identity map WITHDRAWN from the program's range, kept only for [0, 0x400000) (the
    body's image at 1 MiB and low memory);
  - a USER PAGE mappable at the canonical base 0x400000 and up;
  - the P3b-4a worker RE-LINKED from 0x40000000 to 0x400000, its tests unchanged in meaning.

Every P3b-1/2/3/4L/4a/4b self-check is green again with MEANING unchanged and every plant live; the twelve
rows' digest is still on serial; the -m64 build is byte-reproducible.

  A1  a USER page is mappable at the canonical base 0x400000 (vmm_map_user could not do this while the low
      gigabyte was a supervisor huge page): CHECK USER-BASE / LAYOUT pass and the digest is still on
      serial; a PLANTED "identity not withdrawn" reds CHECK USER-BASE
  A2  the body reaches physical memory through its OWN higher-half direct map and the identity map is
      WITHDRAWN from the program's range: CHECK LAYOUT passes and DIRECTMAP COVERS the reported RAM; the
      direct map spans the WHOLE reported range with a CAP (DIRECT_MAP_MAX, 1 GiB, named) whose check CAN
      FAIL — a nested guest with more RAM than the cap reds DIRECTMAP; a PLANTED "identity not withdrawn"
      reds CHECK LAYOUT
  A3  the P3b-4a worker is RE-LINKED to 0x400000 (its ELF entry at the canonical base), its tests unchanged
      in meaning — it runs UNPRIVILEGED (CS/SS RPL 3) and a TRESPASS on the body's memory still FAULTS; a
      planted "body page user-accessible" reds CHECK TRESPASS on the new layout
  A4  EVERY P3b-1/2/3/4L/4a/4b self-check is green again MEANING UNCHANGED and each slice's plant STILL
      reds its own check on the re-laid-out body (a spot battery here; the AUTHORITATIVE full battery is
      test_c7_p3b_1/2/3/4L/4a/4b re-run against this body)
  A5  DERIVED, byte-REPRODUCIBLE, ATTESTED (no new src/body source — edit-in-place, so ATTESTED stands at
      87 and src/body at 30), guest-only, NO one-way door — no host-kernel load, the body not stood as
      production; the scans CAN fail
  A6  NO founding — layout is code: ACT_KINDS stays twelve, the founding pack is byte-unchanged
      (95631e8f), founding 1.55.0

A1/A2/A3/A4-guest/A5-repro build+boot in the NESTED guest on an ISOLATED per-unit scratch and skip when
the pinned guest is not reachable over SSH; A4-inmain, A5-attested and A6 run in main. Register: OS
bring-up on a disposable guest, described by function — a body laid out the way a real machine is, keeping
its own memory/disk/clock and announcing its definition digest; validated by building/reading, never by
attack (governance-work-method). Every kernel touch is the guest's nested qemu; the host kernel is never
touched (L11 / EP-00 rule 9 / charter §A21).
"""

import hashlib
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
# the founding pack is byte-unchanged (no founding — layout is code): pack sha + version pinned.
PACK_SHA = "95631e8f00ed18233dc3bdc4fe6207495b78bd5cb26dbee96db53a47dd6c179b"
FOUNDING_VERSION = "1.55.0"

# the canonical base (L20) and the direct-map cap (DIRECT_MAP_MAX), NAMED here as they are in body.h.
CANONICAL_BASE = 0x400000
DIRECT_MAP_CAP = 1024 * 1024 * 1024   # 1 GiB — the cap the direct map covers (precision 1: named)

# ── the nested-guest bridge (guest arms only) — an ISOLATED per-unit scratch (guest to itself) ────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4m-accept"          # a per-unit scratch dir (guest to itself, serialized, mgr :4027)
# the nested-qemu command WITHOUT -m (the RAM is chosen per boot: -m 256 the standard, -m 1536 the
# bigger-guest arm that reds the direct-map cap). -cpu max, RTC UTC, the gdb stub from the first line (L17).
_QEMU_NOMEM = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -rtc base=utc"
_GDB_BASE = 6000 + (os.getpid() % 2000)
_boot_n = [0]


def _next_gdb_port():
    p = _GDB_BASE + (_boot_n[0] % 1800)
    _boot_n[0] += 1
    return p


def _guest_reachable():
    """True only if the PINNED guest (6.8.0-134-generic) answers over SSH AND the nested boot engine
    (qemu-system-x86_64) is present. Observes a state the check did not create (§A19)."""
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
_BUILD_CACHE = {}


def _seed_guest():
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", outdir=None):
    """Build the re-laid-out body in the guest; return (outdir, elf_sha256, worker_sha)."""
    _seed_guest()
    out = outdir or (_WD + "/out" + (("-" + fault) if fault else ""))
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (_WD, _WD, out, fault)],
                       capture_output=True, timeout=180)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    line = b.stdout.decode(errors="replace")
    m = re.search(r"worker image seal sha256 ([0-9a-f]{64})", line)
    h = subprocess.run(_SSH + ["sha256sum %s/body.elf | cut -d' ' -f1" % out],
                       capture_output=True, timeout=20)
    return out, h.stdout.decode().strip(), (m.group(1) if m else None)


def _guest_boot(outdir, mem=256, timeout_s=18):
    """Boot the flat image in a NESTED qemu with `mem` MiB of RAM (the gdb stub attached from the first
    line, L17); return serial text. Boots are SERIALIZED (guest-to-itself, mgr :4027)."""
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d %s -m %d -gdb tcp::%d -kernel %s/body.img </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU_NOMEM, mem, _next_gdb_port(), outdir)],
        capture_output=True, timeout=timeout_s + 20)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault=""):
    """Build+boot once per fault at the standard -m 256, cached (each guest boot is ~15s serialized)."""
    if fault not in _SERIAL_CACHE:
        out, _elf, _w = _guest_build(fault)
        _BUILD_CACHE[fault] = out
        _SERIAL_CACHE[fault] = _guest_boot(out)
    return _SERIAL_CACHE[fault]


def _worker_entry_va(outdir):
    """The worker ELF's entry symbol address — proves the re-link to the canonical base (A3)."""
    r = subprocess.run(_SSH + ["nm %s/worker.elf | awk '/ _wstart$/{print $1}'" % outdir],
                       capture_output=True, timeout=20)
    s = r.stdout.decode(errors="replace").strip()
    return int(s, 16) if s else None


def _body_source_names():
    return sorted(n for n in os.listdir(BODY)
                  if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def tearDownModule():
    """Leave the guest as found: no nested-qemu boot survives this module (serialized guest)."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1UserPageMappableAtTheCanonicalBase(unittest.TestCase):
    def test_a_user_page_is_mappable_at_0x400000_and_the_digest_is_still_on_serial(self):
        serial = _serial()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("LONGMODE: OK", serial, "the body is in the machine's long mode (P3b-4L)")
        # the canonical base 0x400000 is USER-mappable now (before, it was a supervisor huge page).
        self.assertIn("CHECK USER-BASE: PASS", serial,
                      "a user page is mappable at the canonical base 0x400000 (PRESENT + USER, its frame)")
        self.assertIn("LAYOUT: PASS", serial, "the address-space layout self-check passes as a group")
        # the twelve rows' digest is STILL on serial on the re-laid-out body.
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")

    def test_a_planted_identity_not_withdrawn_reds_the_user_base_check(self):
        # the CHECK CAN FAIL: re-installing the supervisor identity huge page over the program's range
        # makes 0x400000 un-user-mappable again — CHECK USER-BASE reds.
        serial = _serial("PLANT_IDENTITY_NOT_WITHDRAWN")
        self.assertIn("CHECK USER-BASE: FAIL", serial,
                      "0x400000 is not user-mappable while the low identity map still owns the program's range")
        self.assertIn("LAYOUT: FAIL", serial, "the aggregate layout check reds")


# ── A2 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2DirectMapAndIdentityWithdrawn(unittest.TestCase):
    def test_the_body_reaches_memory_through_its_direct_map_and_the_identity_is_withdrawn(self):
        serial = _serial()
        self.assertIn("CHECK LAYOUT: PASS", serial,
                      "the body reaches a frame through its OWN higher-half direct map; the identity is withdrawn")
        # the direct map COVERS the reported physical range (precision 1) at the standard -m 256.
        m = re.search(r"DIRECTMAP: COVERS \(reported_max=0x([0-9a-f]+) <= cap=0x([0-9a-f]+)\)", serial)
        self.assertIsNotNone(m, "the direct-map cap check reports COVERS at -m 256")
        self.assertEqual(int(m.group(2), 16), DIRECT_MAP_CAP, "the cap is DIRECT_MAP_MAX (1 GiB), named")
        self.assertLessEqual(int(m.group(1), 16), DIRECT_MAP_CAP, "reported RAM is within the direct map")

    def test_the_direct_map_cap_check_can_fail_with_a_bigger_guest(self):
        # precision 1: the direct map spans the WHOLE reported range and the check CAN FAIL — a nested
        # guest with MORE RAM than the cap (1 GiB) reds DIRECTMAP. Same body, more RAM.
        out = _BUILD_CACHE.get("")
        if out is None:
            out, _e, _w = _guest_build()
            _BUILD_CACHE[""] = out
        serial_big = _guest_boot(out, mem=1536)
        m = re.search(r"DIRECTMAP: FAIL \(reported_max=0x([0-9a-f]+) > cap=0x([0-9a-f]+)", serial_big)
        self.assertIsNotNone(m, "a guest with more RAM than the cap reds the direct-map check (precision 1)")
        self.assertGreater(int(m.group(1), 16), DIRECT_MAP_CAP,
                           "the reported max exceeds the cap, so the check reds — it is not a tautology")

    def test_a_planted_identity_not_withdrawn_reds_the_layout_check(self):
        serial = _serial("PLANT_IDENTITY_NOT_WITHDRAWN")
        self.assertIn("CHECK LAYOUT: FAIL", serial,
                      "a supervisor identity huge page over the program's range reds the withdrawal check")


# ── A3 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA3WorkerReLinkedToTheCanonicalBaseTestsUnchanged(unittest.TestCase):
    def test_the_worker_is_re_linked_to_0x400000_runs_unprivileged_and_the_trespass_still_faults(self):
        out = _BUILD_CACHE.get("")
        if out is None:
            out, _e, _w = _guest_build()
            _BUILD_CACHE[""] = out
        # the RE-LINK: the worker's ELF entry is at the canonical base 0x400000 (was 0x40000000).
        self.assertEqual(_worker_entry_va(out), CANONICAL_BASE,
                         "the P3b-4a worker is re-linked from 0x40000000 to the canonical base 0x400000")
        serial = _serial()
        # its tests hold with MEANING unchanged: the worker runs UNPRIVILEGED (CS/SS RPL 3) ...
        cs = re.search(r"WORKER-CS: 0x([0-9a-f]+)", serial)
        ss = re.search(r"WORKER-SS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(cs); self.assertIsNotNone(ss)
        self.assertEqual(int(cs.group(1), 16) & 3, 3, "the worker's CS RPL is 3 (unprivileged)")
        self.assertEqual(int(ss.group(1), 16) & 3, 3, "the worker's SS RPL is 3 (unprivileged)")
        self.assertIn("CHECK RING3: PASS", serial, "the worker runs at ring 3 on the new layout")
        # ... and a TRESPASS on the body's memory still FAULTS (the enclosure boundary holds).
        self.assertIn("CHECK TRESPASS: PASS", serial, "a direct reach at body memory is FAULTED by the hardware")
        self.assertIn("CHECK CROSSING: PASS", serial, "the crossing is the machine's own")
        self.assertIn("ENCLOSURE: PASS", serial, "the enclosure self-check passes as a group on the new layout")

    def test_a_planted_body_page_user_accessible_reds_the_trespass_on_the_new_layout(self):
        # the trespass check still LIVES after the re-link: mapping a body page USER reds CHECK TRESPASS.
        serial = _serial("PLANT_BODY_USER_ACCESSIBLE")
        self.assertIn("CHECK TRESPASS: FAIL", serial,
                      "a body page mapped USER lets the reach not fault — the trespass plant still reds")
        self.assertIn("ENCLOSURE: FAIL", serial, "the aggregate enclosure line reds")


# ── A4 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A4-guest needs the pinned guest + nested qemu over SSH -p 2222")
class TestA4EveryPriorSelfCheckGreenMeaningUnchangedEveryPlantLive(unittest.TestCase):
    """A spot battery on the re-laid-out body — the AUTHORITATIVE full battery is test_c7_p3b_1/2/3/4L/4a/
    4b re-run against this body (their boot invocations build the same re-laid-out body). This class
    proves the re-layout did not disable any slice or any plant."""

    def test_memory_clock_enclosure_serve_all_green_on_the_re_laid_out_body(self):
        serial = _serial()
        for line in ("CHECK PMM: PASS", "CHECK VMM: PASS", "CHECK HEAP: PASS", "MEMORY: PASS",
                     "CLOCK: PASS", "CLOCK-ACTS: PASS", "ENCLOSURE-ACTS: PASS",
                     "SERVE: PASS", "SERVE-ACTS: PASS"):
            self.assertIn(line, serial, "%r green on the re-laid-out body (meaning unchanged)" % line)

    def test_a_memory_plant_and_a_clock_plant_still_red_on_the_new_layout(self):
        # the VMM plant reds on the body's own tables; the interrupt-gate plant reds the clock — proving
        # the prior slices' plants stay live after the re-layout (A4 spot).
        serial_v = _serial("PLANT_VMM_WRONG")
        self.assertIn("CHECK VMM: FAIL", serial_v, "the memory VMM plant still reds on the re-laid-out body")
        self.assertIn("MEMORY: FAIL", serial_v)
        serial_g = _serial("PLANT_BAD_GATE")
        self.assertIn("CHECK INTERRUPTS: FAIL", serial_g, "the clock interrupt-gate plant still reds")
        self.assertIn("CLOCK: FAIL", serial_g)


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


class TestA5AttestedRevertableNoOneWayDoor(unittest.TestCase):
    def test_no_new_src_body_source_so_the_attested_set_stands_at_87(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        on_disk = sorted("body/" + f for f in _body_source_names())
        # the re-layout is EDIT-IN-PLACE (no new src/body source), so src/body stays at 30 and ATTESTED
        # stands at 87 — an edit to an existing member moves no count (A5).
        self.assertEqual(len(on_disk), 31, "the 31 src/body/ source files — this slice adds none (C7 P3b-6a added net.c)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s is not attested (§9 mechanism 1)" % rel)
        # the files this row re-laid are existing members (content changed, not the count).
        for rel in ("body/vmm.c", "body/pmm.c", "body/kmain.c", "body/enclosure.c",
                    "body/worker.ld", "body/body.h"):
            self.assertIn(rel, ATTESTED_MEMBERS, "%s (re-laid here) is an attested member" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "layout is an edit-in-place — ATTESTED stands at 88 (C7 P3b-6a's net.c)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers src/body")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list")

    def test_the_built_elf_and_flat_img_are_never_signed_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built .elf / worker image / flat .img are NEVER members")

    def test_no_host_kernel_load_in_the_body_and_the_scan_can_fail(self):
        for name in _body_source_names():
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                self.assertEqual(_host_kernel_load_tokens(f.read()), [],
                                 "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        self.assertEqual(_host_kernel_load_tokens("insmod /lib/modules/govosfs.ko"), ["insmod"])
        self.assertEqual(_host_kernel_load_tokens("modprobe kvm_intel"), ["modprobe"])

    def test_the_body_is_not_stood_as_the_production_performer_and_the_scan_can_fail(self):
        self.assertEqual(_production_standing_hits(SRC), [],
                         "a module above the seam imports the body as the production performer")
        tmp = tempfile.mkdtemp(prefix="p3b4m-a5-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "compose_planted.py"), "w", encoding="utf-8") as f:
            f.write("from body import kmain  # stand the body as the production performer\n")
        self.assertTrue(any(rel == "kernel/compose_planted.py"
                            for rel, _pat in _production_standing_hits(tmp)),
                        "a planted production-standing import must red the scan")

    def test_the_canonical_base_and_direct_map_cap_are_named_in_the_header(self):
        # precision 1 ("declare the cap by name") + precision 2 ("name the dividing address once"): both
        # live in body.h, the ONE place these magic numbers are named.
        with open(os.path.join(BODY, "body.h"), encoding="utf-8") as f:
            hdr = f.read()
        self.assertIn("CANONICAL_BASE   0x400000ull", hdr, "the dividing address named once (precision 2)")
        self.assertIn("DIRECT_MAP_BASE  0xffff800000000000ull", hdr, "the higher-half direct-map base named")
        self.assertIn("DIRECT_MAP_MAX", hdr, "the direct-map cap named (precision 1)")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A5-repro needs the guest toolchain to build the .elf twice")
class TestA5BuildIsByteReproducible(unittest.TestCase):
    def test_the_m64_elf_and_worker_image_are_byte_reproducible(self):
        _, sha1, w1 = _guest_build(outdir=_WD + "/repro1")
        _, sha2, w2 = _guest_build(outdir=_WD + "/repro2")
        self.assertEqual(sha1, sha2, "two builds of the re-laid-out body produce a byte-identical .elf")
        self.assertTrue(w1 and w1 == w2, "the sealed worker image is byte-reproducible (its seal is stable)")


# ── A6 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA6NoFoundingTwelveActs(unittest.TestCase):
    def test_the_founding_pack_is_byte_unchanged_no_founding(self):
        with open(PACK, "rb") as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), PACK_SHA,
                             "the founding pack is byte-unchanged (no founding — layout is code)")
        with open(PACK, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["founding_version"], FOUNDING_VERSION,
                             "founding %s — the layout founds nothing" % FOUNDING_VERSION)

    def test_act_kinds_stays_twelve(self):
        from kernel.boot import ACT_KIND_RECORD_KIND
        with open(PACK, encoding="utf-8") as f:
            pack = json.load(f)
        rows = []

        def scan(node):
            if isinstance(node, dict):
                if node.get("kind") == ACT_KIND_RECORD_KIND:
                    rows.append(node)
                for v in node.values():
                    scan(v)
            elif isinstance(node, list):
                for v in node:
                    scan(v)

        scan(pack)
        kinds = {r["seam_kind"] for r in rows}
        self.assertEqual(len(kinds), 12, "ACT_KINDS stays twelve — the layout adds no act")


if __name__ == "__main__":
    unittest.main()
