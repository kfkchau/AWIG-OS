# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding body loading and running a DYNAMICALLY-linked program through the real dynamic linker: the
# sealed image a read-only filesystem of ld.so + libc served by path+offset+listing and digest-checked before
# load, the loader honouring the program's PT_INTERP and handing over to ld.so which resolves libc from the
# sealed image, the P3b-2 record filesystem mounted beside it — proven by an ORDINARY gcc -pthread -no-pie
# dynamically-linked glibc program built by the guest's own toolchain) as in the seL4/gVisor/Fuchsia and osdev
# literature. NON-GOAL: no offensive capability — this DRIVES the acceptance of C7 P3b-4d: our own kernel's
# body serves a borrowed program's own libraries from one sealed, checked set of files and hands the program
# to the ordinary linker, proven by running one (L19); it stands nothing as production, binds no key, loads no
# interpreter (that is P3b-4c), touches no host kernel (every boot the guest's nested qemu).
"""C7 P3b-4d acceptance — THE DYNAMIC LOADER + THE SEALED IMAGE (design/54 §5 L19; §7 row P3b-4d; the RE-MINT
countersign board :4141; the pre-flight FINDINGS Q8/Q15/:4134).

On the real floor (P3b-4f) the body runs an ordinary STATIC glibc program. This slice brings up the DYNAMIC
path: the SEALED IMAGE as a read-only filesystem of named files (ld.so, libc) the body serves BY PATH +
OFFSET and BY LISTING, DIGEST-CHECKED before load; the loader honours the program's PT_INTERP, loads the
requested ld.so from the sealed image, lays the SEVEN-key auxiliary vector (AT_BASE) and HANDS OVER to the
linker, which resolves libc from the sealed image and relocates the program; the P3b-2 record filesystem is
mounted BESIDE the read-only image (distinct namespaces). It is PROVEN, per L19, by an ordinary
`gcc -pthread -no-pie` DYNAMICALLY-linked threaded glibc program whose start-up now goes through the real
linker — and each plant makes THAT program fail (never a body-side flag alone).

  A1  the dynamic glibc prover runs to completion on the body THROUGH THE REAL LINKER (PROVER3-START, two
      threads reach the exact count under a mutex, a timed wait times out, the joins return, malloc works,
      PROVER3-DONE rc=0); the enclosure and the forty-nine still pass; the twelve rows' digest on serial;
      FLOOR3: PASS
  A2  the sealed image is a read-only path+offset filesystem SERVED BY LISTING and DIGEST-CHECKED: a planted
      byte change refuses the load and the prover NEVER STARTS (PLANT_SEAL_TAMPER); a planted listing refusal
      reds the listable check (PLANT_LISTING_REFUSED — the image is served by listing, not refused, Q15/:4134)
  A3  the loader honours PT_INTERP and hands over to the linker: a planted skip enters the program directly,
      libc unrelocated, and the real program FAULTS before main (PLANT_SKIP_INTERP)
  A4  the P3b-2 record filesystem is mounted BESIDE with distinct namespaces, and the linker's probes are
      answered from the sealed set with NO live walk: a planted collision shadows libc with the record FS so
      ld.so reads the wrong bytes and cannot load libc (PLANT_FS_COLLIDE); a planted live-walk fabricates a
      hit for a path outside the sealed set and reds the no-live-walk check (PLANT_LIVE_WALK)
  A5  our dynamic-loader / sealed-FS C is edit-in-place (ATTESTED 87 / src/body 30 — no new file); the sealed
      image, the borrowed ld.so/libc and the built prover are NEVER members; the prover source is a fixture
      under tests/ not src/body; no host-kernel load; no interpreter (P3b-4c); the P2 census stays clean
  A6  no founding (ACT_KINDS twelve, pack sha 95631e8f byte-unchanged, founding 1.55.0); the ATTESTED
      count-pins stand at 87 (edit-in-place)

The boot acceptances build+boot in the NESTED guest (a bodyfs disk attached as P3b-2) and skip when the pinned
guest is not reachable over SSH; the rest run in main. Register: OS bring-up on a disposable guest, described
by function — a body that runs an ordinary borrowing program through the ordinary linker, serving its
libraries from one sealed checked set; validated by building/reading, never by attack (governance-work-method).
Every kernel touch is the guest's nested qemu; the host kernel is never touched (L11 / EP-00 rule 9 / §A21).
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

# the prover fixture (ordinary gcc -pthread -no-pie DYNAMICALLY-linked glibc C), built by the guest toolchain.
PROVER_FIXTURE = os.path.join(HERE, "c7_p3b_4d_prover_dynamic.c")

# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ───────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4d-accept"
_QEMU = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc"


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
    """Copy src/body + src/bridge + src/founding AND the dynamic prover fixture to the guest ONCE."""
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
    """Build the body WITH the staged DYNAMIC prover + the SEALED IMAGE (DYN_PROVER_SRC) in the guest."""
    _seed_guest()
    tag = tag or (fault or "clean")
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(
        _SSH + ["cd %s && DYN_PROVER_SRC=%s/prover.c bash body/build.sh body %s %s"
                % (_WD, _WD, out, fault)],
        capture_output=True, timeout=300)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    out_txt = b.stdout.decode(errors="replace")
    assert "sealed image seal sha256" in out_txt, "the sealed image was not staged/embedded: " + out_txt
    return out


def _guest_mkdisk(img):
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img, timeout_s):
    """Boot the body in a NESTED qemu with the sealed image as a boot-time MODULE (-initrd) and `img` as a
    virtual IDE disk; return serial text. C7-MAINT-4D-BOOT-AS-MODULE: the 2.26 MB sealed image is carried as a
    module read through the direct map (g_sealed_module_phys) — exactly as the interpreter body and the ledger
    body already carry theirs — NOT embedded into the body's own image, so the body's end-of-data stays under
    the 4 MiB canonical base and the body boots past "VMM: paging enabled" instead of triple-faulting there
    (FINDINGS.md F1/F2). Every boot is the guest's nested qemu — no host kernel. Boots are SERIALIZED."""
    subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                   capture_output=True, timeout=20)
    boot = subprocess.run(
        _SSH + ["timeout --signal=TERM %d %s -kernel %s/body.img -initrd %s/sealed.img "
                "-drive file=%s,format=raw,if=ide,index=0 </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, outdir, outdir, img)],
        capture_output=True, timeout=timeout_s + 40)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault="", tag=None, timeout_s=150):
    """Build a fresh disk + build+boot once per (fault/tag), cached (each guest boot is serialized)."""
    key = tag or (fault or "clean")
    if key not in _SERIAL_CACHE:
        out = _guest_build(fault, tag=key)
        img = _guest_mkdisk("%s/disk-%s.img" % (_WD, key))
        _SERIAL_CACHE[key] = _guest_boot(out, img, timeout_s)
    return _SERIAL_CACHE[key]


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
class TestA1DynamicGlibcProverRunsThroughTheRealLinker(unittest.TestCase):
    def test_a_dynamically_linked_glibc_program_runs_to_completion_through_ld_so(self):
        serial = _serial()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("LONGMODE: OK", serial, "the body is in the machine's long mode (P3b-4L)")
        self.assertIn("FLOOR3-SEAL: OK (digest matches the seal)", serial, "the sealed image digest-checked")
        self.assertIn("FLOOR3-INTERP: /lib64/ld-linux-x86-64.so.2", serial, "the program's PT_INTERP was read")
        self.assertRegex(serial, r"FLOOR3-HANDOVER: entry=0x00007f", "the handover jumped to ld.so's entry (base 0x7f..)")
        self.assertIn("PROVER3-START", serial, "the prover reached main — only ld.so's relocation got it there")
        self.assertIn("PROVER3-CREATE: OK", serial, "both threads were created (clone3 real contexts)")
        self.assertIn("PROVER3-TIMEDWAIT: OK (timed out)", serial, "the timed wait really timed out (futex timeout)")
        self.assertIn("PROVER3-JOIN: OK", serial, "both joins returned (SYS_exit cleared + woke the child id)")
        self.assertIn("PROVER3-COUNT: OK 4000", serial, "two threads reached the EXACT count under the mutex")
        self.assertIn("PROVER3-FP: OK", serial, "each thread's own SSE accumulator survived every turn")
        self.assertIn("PROVER3-MALLOC: OK", serial, "malloc over the growing break works with threads up")
        self.assertIn("PROVER3-DONE rc=0", serial, "the ordinary dynamically-linked glibc program ran to completion")
        self.assertIn("FLOOR3: PASS", serial, "the dynamic-loader self-check passes as a group")
        self.assertIn("FLOOR3-ACTS: PASS", serial)

    def test_the_scheduler_did_real_concurrency_work_under_the_dynamic_linker(self):
        serial = _serial()
        self.assertIn("FLOOR3-THREADS: 0x00000002", serial, "two real thread contexts were created (clone3)")
        self.assertIn("FLOOR3-EXITS: 0x00000002", serial, "both threads ended via SYS_exit")
        self.assertIn("FLOOR3-SWITCH-IN-ACT: 0x00000000", serial, "the scheduler NEVER switched inside an act (:4107 a)")
        m = re.search(r"FLOOR3-PREEMPTS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the preempt counter is on serial")
        self.assertGreater(int(m.group(1), 16), 0, "the timer preempted a running context at least once")

    def test_the_enclosure_and_forty_nine_router_still_pass_unchanged(self):
        serial = _serial()
        self.assertIn("ENCLOSURE: PASS", serial, "the enclosure MECHANISM still passes (P3b-4a, unchanged)")
        self.assertIn("SERVE: PASS", serial, "the forty-nine classification kept as the router (P3b-4b)")
        self.assertIn("SERVE-ACTS: PASS", serial)
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")


# ── A2 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2SealedImageServedByPathAndListingDigestChecked(unittest.TestCase):
    def test_clean_lists_the_sealed_directory_and_serves_by_path(self):
        serial = _serial()
        self.assertIn("FLOOR3-LISTABLE: OK", serial, "the sealed image is served BY LISTING (getdents64), Q15/:4134")
        self.assertIn("FLOOR3-IMAGE: 0x00000005 entries", serial, "the sealed image parsed (3 dirs + ld.so + libc)")

    def test_a_byte_change_in_the_sealed_image_refuses_the_load_and_the_prover_never_starts(self):
        clean = _serial()
        self.assertIn("PROVER3-DONE rc=0", clean, "clean: the prover runs")
        plant = _serial("PLANT_SEAL_TAMPER", timeout_s=110)
        self.assertIn("FLOOR3-SEAL: REFUSED", plant, "a byte change → the digest-check refuses the load (B6)")
        self.assertNotIn("PROVER3-START", plant, "the prover NEVER starts when the sealed image is refused")
        self.assertIn("FLOOR3-ACTS: FAIL", plant, "the dynamic floor reds")

    def test_a_refused_listing_reds_the_listable_check_the_image_is_served_by_listing(self):
        # the image MUST be served by listing (a getdents64 over a sealed dir is a read of the image, not the
        # designed refusal — Q15/:4134); refusing it reds the listable check. The prover still runs (it reads
        # by path this rung), so the failure is the listing, not the program.
        plant = _serial("PLANT_LISTING_REFUSED", timeout_s=150)
        self.assertIn("FLOOR3-LISTABLE: FAIL", plant, "a refused listing reds the check — listing is served, not refused")
        self.assertIn("PROVER3-DONE rc=0", plant, "the prover still runs by path (listing is exercised at P3b-4c)")
        self.assertIn("FLOOR3-ACTS: FAIL", plant, "the dynamic floor reds on the listable check")


# ── A3 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA3LoaderHonoursPtInterpAndHandsOver(unittest.TestCase):
    def test_skipping_the_interp_handover_faults_the_real_program_before_main(self):
        clean = _serial()
        self.assertRegex(clean, r"FLOOR3-HANDOVER: entry=0x00007f", "clean: the handover enters ld.so")
        # the plant enters the program's own e_entry directly (no ld.so, libc unrelocated): the real program
        # faults before main — a real failure of the real program, not a body-side flag.
        plant = _serial("PLANT_SKIP_INTERP", timeout_s=110)
        self.assertRegex(plant, r"FLOOR3-HANDOVER: entry=0x0000000000401[0-9a-f]+ ld_base=0x0000000000000000",
                         "the plant enters the program's entry directly (no ld.so base)")
        self.assertIn("FLOOR3-FAULT: vec=0x0000000e", plant, "the program #PF's — libc was never relocated")
        self.assertNotIn("PROVER3-START", plant, "the program never reaches main without the handover")
        self.assertIn("FLOOR3-ACTS: FAIL", plant)


# ── A4 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A4 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA4RecordFsBesideNoLiveWalk(unittest.TestCase):
    def test_clean_record_fs_is_reachable_beside_and_no_live_walk(self):
        serial = _serial()
        self.assertIn("FLOOR3-BESIDE: OK", serial, "the P3b-2 record FS is reachable beside with distinct namespaces")
        self.assertIn("FLOOR3-NOWALK: OK", serial, "no path outside the sealed+record sets was served (no live walk)")
        m = re.search(r"FLOOR3-OUTSIDE-REFUSALS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the outside-refusal counter is on serial")
        self.assertGreater(int(m.group(1), 16), 0, "the designed ENOENT refusal was actually exercised (positive control)")

    def test_a_collision_shadowing_libc_with_the_record_fs_makes_ld_so_fail(self):
        # the record namespace shadows the sealed set: ld.so opens libc, gets the record's (empty) bytes, and
        # cannot load it — a real failure of ld.so; the beside collision probe also reds.
        plant = _serial("PLANT_FS_COLLIDE", timeout_s=110)
        self.assertIn("FLOOR3-BESIDE: FAIL", plant, "the collision probe detects a sealed path resolving as a record")
        self.assertNotIn("PROVER3-DONE rc=0", plant, "ld.so reads the wrong bytes for libc and the prover cannot complete")
        self.assertIn("FLOOR3-ACTS: FAIL", plant)

    def test_a_fabricated_live_walk_reds_the_no_live_walk_check(self):
        # the plant fabricates a hit for a path OUTSIDE the sealed+record sets (a live walk); the no-live-walk
        # check reds, and no outside path is refused.
        plant = _serial("PLANT_LIVE_WALK", timeout_s=150)
        self.assertIn("FLOOR3-NOWALK: FAIL", plant, "a fabricated outside hit reds the no-live-walk check")
        self.assertIn("FLOOR3-OUTSIDE-REFUSALS: 0x00000000", plant, "no outside path was refused (all fabricated)")
        self.assertIn("FLOOR3-ACTS: FAIL", plant)


# ── C7-MAINT-4D-BOOT-AS-MODULE — the module carriage + the build-time canonical-base guard ─────────
CANONICAL_BASE = 0x400000   # body.h:71 — the x86_64 ET_EXEC base the higher-half body keeps its image beneath


def _guest_nm_symbol(outdir, symbol):
    """The linked address of `symbol` in the built body.elf (16-hex string), read with nm in the guest."""
    r = subprocess.run(_SSH + ["nm %s/body.elf | awk '$3==\"%s\"{print $1}'" % (outdir, symbol)],
                       capture_output=True, timeout=30)
    return r.stdout.decode(errors="replace").strip()


_LINK_LD = ("gcc -m64 -mno-red-zone -ffreestanding -nostdlib -fno-pie -no-pie -Wl,--build-id=none "
            "-Wl,-z,max-page-size=0x1000 -T body/linker.ld")
_CC_FREESTANDING = ("gcc -m64 -mno-red-zone -mno-mmx -mno-sse -mno-sse2 -ffreestanding -fno-pie "
                    "-fno-stack-protector -nostdlib")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: needs the pinned guest + toolchain over SSH -p 2222")
class TestC7Maint4dBootAsModuleGuardAndBase(unittest.TestCase):
    """C7-MAINT-4D-BOOT-AS-MODULE: the 4d sealed image is carried as a boot-time MODULE (read through the direct
    map via g_sealed_module_phys), not embedded into the body's own image; and linker.ld fails the build loudly
    if any body's end-of-data crosses the 4 MiB canonical base, instead of a silent triple-fault at boot."""

    def test_the_body_end_of_data_stays_under_the_4_mib_canonical_base(self):
        # The 2.26 MB sealed image is carried as a MODULE (not embedded), so the body's end-of-data (_bss_end)
        # drops well under CANONICAL_BASE — the base the higher-half body withdraws from the supervisor identity
        # map at the CR3 switch. Embedding pushed _bss_end to 0x475010, over the base, and the first post-paging
        # global write triple-faulted (FINDINGS.md F1/F2). The boot above proves the run floor green; this is a
        # cheap build-artifact regression on the address itself.
        out = _guest_build(tag="bssend")
        bss_end = _guest_nm_symbol(out, "_bss_end")
        self.assertRegex(bss_end, r"^[0-9a-f]{16}$", "nm reported _bss_end for the built body")
        self.assertLess(int(bss_end, 16), CANONICAL_BASE,
                        "the body end-of-data (0x%s) must stay under the 4 MiB canonical base (0x%06x)"
                        % (bss_end, CANONICAL_BASE))

    def test_the_linker_check_fails_the_build_of_an_over_base_body(self):
        # A2 — THE GUARD THAT CAN FAIL. An image whose .bss crosses the base FAILS THE LINK loudly with the
        # named message, never a silent triple-fault at boot. A minimal freestanding object with a 5 MiB .bss
        # (linked at the body's 1 MiB base) puts _bss_end over 0x400000; linker.ld's ASSERT refuses the link.
        _seed_guest()   # the seeded tree carries body/linker.ld
        over = subprocess.run(
            _SSH + ["cd %s && printf 'char __over_base[0x500000];\\nvoid _start(void){}\\n' > over.c && "
                    "%s -c over.c -o over.o && %s -o over.elf over.o 2>&1; echo RC=$?"
                    % (_WD, _CC_FREESTANDING, _LINK_LD)],
            capture_output=True, timeout=120).stdout.decode(errors="replace")
        self.assertIn("RC=1", over, "the over-base link must FAIL (the guard fires): " + over)
        self.assertIn("canonical base", over, "the ASSERT names the canonical base it guards: " + over)
        # POSITIVE CONTROL: a small image under the base links CLEANLY under the same script — the guard does
        # not false-positive (a check that only ever fires is a check that cannot pass).
        small = subprocess.run(
            _SSH + ["cd %s && printf 'void _start(void){}\\n' > small.c && "
                    "%s -c small.c -o small.o && %s -o small.elf small.o 2>&1; echo RC=$?"
                    % (_WD, _CC_FREESTANDING, _LINK_LD)],
            capture_output=True, timeout=120).stdout.decode(errors="replace")
        self.assertIn("RC=0", small, "a body under the base links cleanly (the guard does not false-positive)")


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


class TestA5EditInPlaceImageAndProverNeverMembers(unittest.TestCase):
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
        self.assertTrue(os.path.exists(PROVER_FIXTURE), "the dynamic prover source is a fixture under tests/")
        self.assertFalse(os.path.exists(os.path.join(BODY, "c7_p3b_4d_prover_dynamic.c")),
                         "the prover source is NOT under src/body (where the walk-guard would make it a member)")

    def test_the_built_prover_sealed_image_and_body_are_never_signed_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built prover / sealed image / body images are NEVER signed members")

    def test_the_sealed_fs_and_dynamic_loader_are_in_the_kept_router(self):
        with open(os.path.join(BODY, "serve.c"), encoding="utf-8") as f:
            serve = f.read()
        for token in ("serve_request", "CAT_ACT", "MODULE_SEARCH_SENTINEL", "SV_REFUSED"):
            self.assertIn(token, serve, "the P3b-4b classification router is kept (%s)" % token)
        for token in ("serve_fs_set_image", "serve_openat_fs", "serve_getdents_fs", "serve_fs_beside_check"):
            self.assertIn(token, serve, "the sealed-image filesystem is present (%s)" % token)
        with open(os.path.join(BODY, "enclosure.c"), encoding="utf-8") as f:
            self.assertIn("floor3_run", f.read(), "the dynamic loader (floor3) is present")

    def test_no_host_kernel_load_in_the_body_c(self):
        for name in ("serve.c", "serve.h", "enclosure.c", "enclosure.h", "enclosure.S", "kmain.c", "build.sh"):
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                self.assertEqual(_host_kernel_load_tokens(f.read()), [],
                                 "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        self.assertEqual(_host_kernel_load_tokens("insmod x.ko"), ["insmod"])   # the scan CAN fail

    def test_no_borrowed_interpreter_in_this_rung(self):
        # RE-POINTED (C7 MAINT-BODY-SCANS): from a source-TEXT word scan (which reddened on the legitimate
        # P3b-4c/4g comments naming the real interpreter) to the PROPERTY I3 those comments do not breach —
        # (A2) body.elf links no interpreter / borrowed C-library object, and (A3) no attested member is an
        # interpreter file. This rung is proven with an ordinary borrowed program run as a sealed image/module
        # (P3b-4c/4d), never linked into the body and never a signed member.
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
        self.assertEqual(len(kinds), 12, "ACT_KINDS stays twelve — the dynamic loader adds no act")


if __name__ == "__main__":
    unittest.main()
