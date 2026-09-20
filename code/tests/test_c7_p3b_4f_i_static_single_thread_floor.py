# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding body completing the STATIC SINGLE-THREAD process floor on the metal — the static loader's
# initial stack and auxiliary vector, a real address-space manager for the maps and the break, the main
# thread's thread-local base in the machine's %fs register, the machine's SSE state enabled — proven by an
# ORDINARY statically-linked single-threaded C program built by the guest's own gcc against the real C
# library) as in the seL4/gVisor/Fuchsia and osdev literature. NON-GOAL: no offensive capability — this
# DRIVES the acceptance of C7 P3b-4f-i: our own kernel's body is a real home for an ordinary program's
# start-up and memory, proven by running one (L19); it stands nothing as production, binds no key, touches
# no host kernel (every boot the guest's nested qemu).
"""C7 P3b-4f-i acceptance — THE STATIC SINGLE-THREAD FLOOR (design/54 §5 L19; §7 row P3b-4f, mgr's size-split
4f-i/4f-ii board :4113/:4114; archi countersign :4116 + precisions :4122/:4131/:4132).

On the enclosed long-mode body (P3b-4a) with the forty-nine SERVED (P3b-4b) kept as the router, the body
becomes a real home for an ORDINARY `gcc -static` SINGLE-THREADED glibc program: it lays a real initial
stack + auxiliary vector (AT_RANDOM/AT_PAGESZ/AT_PHDR/AT_PHENT/AT_PHNUM/AT_ENTRY), backs mmap/munmap/
mprotect/brk with a real address-space manager (distinct VAs, a growing break), installs the main-thread
%fs base (arch_prctl), and enables the machine's SSE state (CR4.OSFXSR, never OSXSAVE) — and PROVES the
floor by RUNNING the program to completion. The PROVER is NOT written to fit the body (L19): its source is
a fixture under tests/ (:4107 b), built by the guest gcc against glibc with NO link-base flag (first LOAD
0x400000, :4122); only the built binary is staged, sealed and embedded (never a signed member, §9 mech 3).

  A1  the static single-threaded glibc prover reaches main, malloc/free and distinct maps work, the
      thread-local and SSE run, it reads its own AT_RANDOM, prints PROVER-DONE rc=0; the enclosure and the
      forty-nine still pass; the twelve rows' digest still on serial (nested guest)
  A2  the main-thread %fs base is REAL (arch_prctl installs %fs) — a plant that does not install it makes
      the PROVER FAULT on its first thread-local access (#PF at ring 3), no completion
  A3  the address space is real and the static loader complete (stack + auxv): distinct maps, a growing
      break; a planted FIXED VA makes the two maps alias and the PROVER's own check red; the AT_RANDOM the
      loader lays DIFFERS boot to boot (the body's entropy act), a planted constant is identical
  A4  the machine's SSE state is enabled for the ring-3 program — a plant that leaves it disabled makes the
      PROVER FAULT (#UD) on its first SSE instruction, no completion
  A5  P3b-4b's classification kept as the router; NO new floor file added (edit-in-place, ATTESTED stays
      87 / 30); the prover source is a fixture under tests/ not src/body; the prover/body IMAGE is never a
      member; guest-only, revertable, the host-crossing census clean, no one-way door
  A6  no founding (ACT_KINDS twelve, pack sha 95631e8f byte-unchanged, founding 1.55.0); the ATTESTED
      count-pins stand at 87 / 30 (edit-in-place — no new src/body file)

A1..A4 build+boot in the NESTED guest (a bodyfs disk attached as P3b-2) and skip when the pinned guest is
not reachable over SSH; A5/A6 run in main. Register: OS bring-up on a disposable guest, described by
function — a body that is a real home for an ordinary program; validated by building/reading, never by
attack (governance-work-method). Every kernel touch is the guest's nested qemu; the host kernel is never
touched (L11 / EP-00 rule 9 / charter §A21).
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

ROWS_DIGEST = "sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb"

# the prover fixture (ordinary gcc -static glibc C), built by the guest toolchain and staged into the body.
PROVER_FIXTURE = os.path.join(HERE, "c7_p3b_4f_i_prover_static.c")

# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ───────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4fi-accept"
_QEMU = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc"

_GDB_BASE = 2300 + (os.getpid() % 1500)
_boot_n = [0]


def _next_gdb_port():
    p = _GDB_BASE + (_boot_n[0] % 1500)
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


def _seed_guest():
    """Copy src/body + src/bridge + src/founding AND the prover fixture to the guest ONCE (mkdisk.py needs
    host_seam + the pack; build.sh builds the prover from the staged fixture)."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=120)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=120, check=True)
    with open(PROVER_FIXTURE, "rb") as f:
        src = f.read()
    subprocess.run(_SSH + ["cat > %s/prover.c" % _WD], input=src, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", tag=None):
    """Build the body WITH the staged static prover (PROVER_SRC set) in the guest; return the outdir."""
    _seed_guest()
    tag = tag or (fault or "clean")
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(
        _SSH + ["cd %s && PROVER_SRC=%s/prover.c bash body/build.sh body %s %s" % (_WD, _WD, out, fault)],
        capture_output=True, timeout=240)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    out_txt = b.stdout.decode(errors="replace")
    assert "prover image seal sha256" in out_txt, "the prover was not sealed/embedded: " + out_txt
    return out


def _guest_mkdisk(img):
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img, timeout_s=28):
    """Boot the body in a NESTED qemu with `img` as a virtual IDE disk (gdb stub from the first line, L17);
    return serial text. Every boot is the guest's nested qemu — no host kernel. Boots are SERIALIZED."""
    boot = subprocess.run(
        _SSH + ["timeout --signal=TERM %d %s -gdb tcp::%d -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, _next_gdb_port(), outdir, img)],
        capture_output=True, timeout=timeout_s + 30)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault="", tag=None):
    """Build a fresh disk + build+boot once per (fault/tag), cached (each guest boot is serialized)."""
    key = tag or (fault or "clean")
    if key not in _SERIAL_CACHE:
        out = _guest_build(fault, tag=key)
        img = _guest_mkdisk("%s/disk-%s.img" % (_WD, key))
        _SERIAL_CACHE[key] = _guest_boot(out, img)
    return _SERIAL_CACHE[key]


def _at_random(serial):
    m = re.search(r"PROVER-AT-RANDOM: ([0-9a-f]{32})", serial)
    return m.group(1) if m else None


def _body_source_names():
    return sorted(n for n in os.listdir(BODY)
                  if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def tearDownModule():
    """Leave the guest as found: no nested-qemu boot survives this module (serialized guest)."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1StaticGlibcProverRunsToCompletion(unittest.TestCase):
    def test_an_ordinary_static_glibc_program_runs_to_completion_on_the_body(self):
        serial = _serial()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("LONGMODE: OK", serial, "the body is in the machine's long mode (P3b-4L)")
        # the floor loaded the sealed prover and it RAN its ordinary glibc start-up to completion.
        self.assertIn("FLOOR-LOAD: OK (digest matches the seal)", serial, "the sealed prover digest-checked")
        self.assertIn("PROVER-START", serial, "the prover reached main")
        self.assertIn("PROVER-TLS: OK", serial, "the main-thread %fs thread-local works")
        self.assertIn("PROVER-SSE: OK", serial, "the machine's SSE state is enabled for the program")
        self.assertIn("PROVER-MALLOC: OK", serial, "malloc/free over the growing break — distinct memory")
        self.assertIn("PROVER-MMAP: OK", serial, "the address-space manager hands DISTINCT virtual addresses")
        self.assertIsNotNone(_at_random(serial), "the loader laid AT_RANDOM (the program read its canary)")
        self.assertIn("PROVER-DONE rc=0", serial, "the ordinary glibc program ran to completion")
        self.assertIn("FLOOR: PASS", serial, "the floor self-check passes as a group")
        self.assertIn("FLOOR-ACTS: PASS", serial)

    def test_the_enclosure_and_forty_nine_router_still_pass_unchanged(self):
        serial = _serial()
        self.assertIn("ENCLOSURE: PASS", serial, "the enclosure MECHANISM still passes (P3b-4a, unchanged)")
        self.assertIn("SERVE: PASS", serial, "the forty-nine classification kept as the router (P3b-4b, A5)")
        self.assertIn("SERVE-ACTS: PASS", serial)
        # the twelve rows' digest is STILL on serial after the floor phase.
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")


# ── A2 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2MainThreadFsBaseIsReal(unittest.TestCase):
    def test_no_fs_base_makes_the_program_fault_on_its_first_thread_local_access(self):
        clean = _serial()
        self.assertIn("PROVER-TLS: OK", clean, "clean: the %fs thread-local works")
        plant = _serial("PLANT_NO_FS_BASE")
        # the program FAULTS (a real ring-3 #PF, vector 0x0e), the body catches it — not a flag.
        self.assertIn("FLOOR-FAULT:", plant, "no %fs base installed → the program faults (a real fault)")
        self.assertRegex(plant, r"FLOOR-FAULT: vec=0x0*e ", "the thread-local access is a #PF (vector 14)")
        self.assertRegex(plant, r"faultcs=0x0*2b", "the fault was taken at ring 3 (user CS 0x2b)")
        self.assertIn("FLOOR: FAIL", plant, "the floor reds when the %fs base is missing")
        self.assertNotIn("PROVER-DONE", plant, "the program never completes without its thread-local base")


# ── A3 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA3AddressSpaceRealLoaderComplete(unittest.TestCase):
    def test_distinct_maps_a_fixed_va_makes_the_maps_alias_and_the_program_red(self):
        clean = _serial()
        self.assertIn("PROVER-MMAP: OK", clean, "clean: two anonymous maps are DISTINCT")
        plant = _serial("PLANT_FIXED_VA")
        # a fixed VA for every map makes the two maps ALIAS → the program's own check reds (a real failure).
        self.assertIn("PROVER-MMAP: FAIL", plant, "a fixed VA aliases the two maps — the program's check reds")
        self.assertNotIn("PROVER-DONE", plant, "the program does not complete once its maps alias")

    def test_the_loaders_at_random_differs_boot_to_boot_a_constant_is_identical(self):
        # the loader lays AT_RANDOM from the body's entropy act: two clean boots differ (a check that fails).
        a = _at_random(_serial("", tag="clean"))
        b = _at_random(_serial("", tag="clean_b"))
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertNotEqual(a, b, "AT_RANDOM differs boot to boot (the body's entropy act, precision b)")
        # a planted constant AT_RANDOM is the SAME every boot — the differ-check CAN fail.
        c = _at_random(_serial("PLANT_AT_RANDOM_CONSTANT"))
        self.assertEqual(c, "5a" * 16, "the planted constant AT_RANDOM is identical every boot (reds the differ-check)")
        self.assertNotIn(c, (a, b), "the real source never produces the planted constant")


# ── A4 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A4 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA4MachineSseStateEnabled(unittest.TestCase):
    def test_sse_disabled_makes_the_program_fault_on_its_first_sse_instruction(self):
        clean = _serial()
        self.assertIn("PROVER-SSE: OK", clean, "clean: the program's SSE instructions execute")
        plant = _serial("PLANT_SSE_DISABLED")
        # the program FAULTS (a real ring-3 #UD, vector 0x06) on its first SSE instruction — not a flag.
        self.assertIn("FLOOR-FAULT:", plant, "SSE left disabled → the program faults (a real fault)")
        self.assertRegex(plant, r"FLOOR-FAULT: vec=0x0*6 ", "an SSE instruction with OSFXSR off #UDs (vector 6)")
        self.assertRegex(plant, r"faultcs=0x0*2b", "the fault was taken at ring 3 (user CS 0x2b)")
        self.assertIn("FLOOR: FAIL", plant, "the floor reds when SSE is not enabled")
        self.assertNotIn("PROVER-DONE", plant, "the program never completes without SSE")


# ── A5 ───────────────────────────────────────────────────────────────────────────────────────────
def _host_kernel_load_tokens(text):
    return [tok for tok in ("insmod", "modprobe") if tok in text]


# ── C7 MAINT-BODY-SCANS: the "no borrowed interpreter in the body" property, at its real home ──────────
# The scan below once read the body's SOURCE TEXT for the words "cpython"/"libpython"; P3b-4c/4g added
# LEGITIMATE comments naming the real borrowed interpreter (design/54 L19) to serve.c/enclosure.c, so a
# word scan reddened on a comment while property I3 (no borrowed code INSIDE the signed base) held intact.
# The property lives in TWO places — the body.elf link (build.sh, where "linked into body.elf" is decided)
# and the attested member list — and is checked there, never in prose.
def _body_elf_link_command(build_text):
    """The single gcc invocation that links body.elf, with backslash-continuations joined."""
    joined = re.sub(r"\\\n[ \t]*", " ", build_text)
    for line in joined.splitlines():
        if line.lstrip().startswith("gcc") and '-o "$OUT/body.elf"' in line:
            return line
    return None


def _link_inputs(link_command):
    """The object files and library-link flags actually linked into body.elf."""
    objs = re.findall(r'"\$OUT/([A-Za-z0-9_.+-]+\.o)"', link_command)
    libs = re.findall(r"(?:^|\s)(-l[:\w.+-]+)", link_command)
    return objs, libs


def _borrowed_interpreter_link_inputs(objs, libs):
    """Any link input that is a borrowed interpreter / C-library object or a flag pulling one."""
    bad = [o for o in objs if any(t in o.lower() for t in ("cpython", "libpython", "python"))]
    bad += [l for l in libs if l.startswith("-lpython") or l in ("-lc", "-lpython3")]
    return bad


def _interpreter_members(members):
    """Any attested member whose path is a borrowed interpreter file (never a signed member, §9 mech 3)."""
    return [m for m in members
            if any(t in m.lower() for t in ("cpython", "libpython", "ld-linux", "libc.so"))]


class TestA5RouterKeptEditInPlaceProverNotAMember(unittest.TestCase):
    def test_no_new_src_body_file_attested_stays_87_and_30(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "31 src/body files (this slice adds none; C7 P3b-6a added net.c)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "edit-in-place — ATTESTED stands at 88 (C7 P3b-6a's net.c)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers src/body")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list (I7)")

    def test_the_prover_source_is_a_fixture_under_tests_not_src_body(self):
        self.assertTrue(os.path.exists(PROVER_FIXTURE), "the prover source is a fixture under tests/")
        self.assertFalse(os.path.exists(os.path.join(BODY, "c7_p3b_4f_i_prover_static.c")),
                         "the prover source is NOT under src/body (where the walk-guard would make it a member)")

    def test_the_built_prover_and_body_images_are_never_signed_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built prover/worker/body images are NEVER signed members")

    def test_the_classification_is_kept_as_the_router_not_rewritten(self):
        # serve.c still classifies the forty-nine by purpose (the router); only the canned answers became
        # real machinery. The measured-shape switch on the syscall names is intact.
        with open(os.path.join(BODY, "serve.c"), encoding="utf-8") as f:
            serve = f.read()
        for token in ("serve_request", "CAT_ACT", "MODULE_SEARCH_SENTINEL", "SV_REFUSED"):
            self.assertIn(token, serve, "the P3b-4b classification router is kept (%s)" % token)
        # the real machinery replaced the canned single-thread answers.
        for token in ("serve_brk", "serve_arch_prctl", "MSR_FS_BASE", "serve_set_brk_base"):
            self.assertIn(token, serve, "the canned answers are replaced by real machinery (%s)" % token)

    def test_no_host_kernel_load_in_the_new_body_c(self):
        for name in ("serve.c", "serve.h", "enclosure.c", "enclosure.h", "enclosure.S", "kmain.c"):
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                self.assertEqual(_host_kernel_load_tokens(f.read()), [],
                                 "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        self.assertEqual(_host_kernel_load_tokens("insmod x.ko"), ["insmod"])   # the scan CAN fail

    def test_no_borrowed_interpreter_in_this_rung(self):
        # RE-POINTED (C7 MAINT-BODY-SCANS): from a source-TEXT word scan (which reddened on the legitimate
        # P3b-4c/4g comments naming the real interpreter) to the PROPERTY I3 those comments do not breach —
        # (A2) body.elf links no interpreter / borrowed C-library object, and (A3) no attested member is an
        # interpreter file. The floor is proven with an ordinary gcc -static program run as a sealed
        # image/module (P3b-4c), never linked into the body and never a signed member.
        from kernel.attestation import ATTESTED_MEMBERS

        # (A2) the body.elf link — where "linked into body.elf" is decided.
        with open(os.path.join(BODY, "build.sh"), encoding="utf-8") as _bf:
            link = _body_elf_link_command(_bf.read())
        self.assertIsNotNone(link, "the body.elf link command was not found in src/body/build.sh")
        self.assertIn("-nostdlib", link, "the body link must be freestanding (no borrowed C runtime linked)")
        objs, libs = _link_inputs(link)
        self.assertEqual(_borrowed_interpreter_link_inputs(objs, libs), [],
                         "body.elf links a borrowed interpreter / C-library object (I3 breach)")
        # PLANT: a linked interpreter object / a -lpython flag reds the check (the scan CAN fail).
        self.assertEqual(_borrowed_interpreter_link_inputs(objs + ["libpython3.12.so"], libs),
                         ["libpython3.12.so"], "the linked-artifact scan cannot fail")
        self.assertEqual(_borrowed_interpreter_link_inputs(objs, libs + ["-lpython3.12"]),
                         ["-lpython3.12"], "the library-flag scan cannot fail")

        # (A3) no attested member is an interpreter file.
        self.assertEqual(_interpreter_members(ATTESTED_MEMBERS), [],
                         "an attested member is a borrowed interpreter file (I3 breach)")
        # PLANT: an interpreter file name in a FIXTURE copy of the member list reds (never the real manifest).
        planted = tuple(ATTESTED_MEMBERS) + ("body/libpython3.12.so.1.0",)
        self.assertEqual(_interpreter_members(planted), ["body/libpython3.12.so.1.0"],
                         "the member-list scan cannot fail")

    def test_the_p2_host_crossing_census_stays_clean(self):
        from tools.conformance import host_crossing_census as census
        self.assertEqual(census.undeclared_crossings(), {}, "the core (src/body included) is host-clean")


# ── A6 ───────────────────────────────────────────────────────────────────────────────────────────
class TestA6NoFoundingTwelveActs(unittest.TestCase):
    def test_no_founding_act_kinds_twelve_pack_byte_unchanged(self):
        import hashlib
        import json
        from kernel.boot import ACT_KIND_RECORD_KIND

        pack_path = os.path.join(SRC, "founding", "founding-pack.json")
        with open(pack_path, "rb") as f:
            raw = f.read()
        self.assertTrue(hashlib.sha256(raw).hexdigest().startswith("95631e8f"),
                        "the founding pack is byte-unchanged (sha256 95631e8f…) — no founding")
        pack = json.loads(raw.decode("utf-8"))
        self.assertEqual(pack["founding_version"], "1.55.0", "no founding — the version is unchanged")

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
        self.assertEqual(len(kinds), 12, "ACT_KINDS stays twelve — the floor adds no act")


if __name__ == "__main__":
    unittest.main()
