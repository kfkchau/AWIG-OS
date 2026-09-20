# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a TSS, a user code/data segment, a return into ring 3, the SYSCALL/SYSRET call crossing, an ELF64
# loader of a sealed image, an append-only crossing trail, a hosted worker refused a request as its own
# native failure) as in the seL4/gVisor/Fuchsia and osdev literature. NON-GOAL: no offensive capability —
# this DRIVES the acceptance of C7 P3b-4a (the enclosure MECHANISM proven with OUR small hand-written test
# worker in a nested guest; the body hosts a program of OURS unprivileged, answers a handful of requests
# and refuses the rest, and the boundary is enforced by the hardware; it boots nothing into production,
# touches no host kernel).
"""C7 P3b-4a acceptance — THE WORKER'S ENCLOSURE (design/54 §5 L18, §7 P3b-4a; countersign archi :4085).

The long-mode body (P3b-4L) now hosts a program BENEATH THE SEAM, at user privilege, on the metal: a TSS +
user segments + a return into ring 3; the SYSCALL/SYSRET call crossing (the machine's own); the body's own
ELF64 loader of a SEALED (digest-checked) image; an append-only crossing trail (one row per request served
or refused, a refused row carrying the native answer); and OUR small hand-written test worker making a
handful of requests and reading the body's answers.

  A1  the body loads + runs OUR test worker UNPRIVILEGED via its own loader from the sealed image, and its
      requests cross IN and BACK; the twelve rows' digest still on serial (nested guest)
  A2  the worker is UNPRIVILEGED and the crossing is the MACHINE'S OWN (enclosure is a hardware fact): the
      worker's CS/SS read from the machine (RPL 3); a planted "worker runs at ring 0" / "worker reaches the
      body's memory directly" / "crossing bypassed" reds its own check
  A3  EVERY request is a ROW of the body's own trail; an out-of-set request is REFUSED as the worker's own
      native failure (-ENOSYS) and is a row; a planted "out-of-set served" / "refusal not native" / "a
      request not recorded" / "a digest change accepted (sealed image)" reds its own check
  A4  OUR test worker + the enclosure C are ATTESTED BY NAME (79 -> 85); the built worker IMAGE is never a
      member; the witness classes are kept apart (I7); the P2 host-crossing census stays clean
  A5  guest-only, revertable, NO one-way door — no host-kernel load, the body is not stood as production;
      the scans CAN fail (near-miss)
  A6  no founding (ACT_KINDS twelve, the pack byte-unchanged, founding 1.55.0); the .elf is byte-reproducible

A1/A2(guest)/A3(guest)/A6-repro build+boot in the NESTED guest and skip when the pinned guest is not
reachable over SSH; A4/A5/A6-founding run in main. Register: OS bring-up on a disposable guest, described by
function — a body that hosts a program of ours unprivileged and answers only what it serves; validated by
building/reading, never by attack (governance-work-method). Every kernel touch is the guest's nested qemu;
the host kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
"""

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
sys.path.insert(0, SRC)

ROWS_DIGEST = "sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb"

# the six enclosure source files this slice adds under src/body/ (attested by name, A4).
NEW_ENCL_FILES = ("body/enclosure.S", "body/enclosure.c", "body/enclosure.h",
                  "body/sha256.c", "body/worker.S", "body/worker.ld")

# the native failure answer for an out-of-set request — the SYSCALL's own -ENOSYS shape (never a
# gov-os message). 38 == ENOSYS; -38 as a u64 == 0xffffffffffffffda.
NATIVE_FAIL = "ffffffffffffffda"

# the A2/A3 planted faults caught in-body and the CHECK each one must red (a check that can fail is the
# proof the check is real, §A64).
FAULT_TO_FAILED_CHECK = {
    "PLANT_WORKER_RING0":         "CHECK RING3: FAIL",     # A2 — the worker returns into ring 0
    "PLANT_BODY_USER_ACCESSIBLE": "CHECK TRESPASS: FAIL",  # A2 — the direct reach does not fault
    "PLANT_NO_SYSCALL_MSR":       "CHECK CROSSING: FAIL",  # A2 — the SYSCALL machinery is not enabled
    "PLANT_OUTOFSET_SERVED":      "CHECK REFUSAL: FAIL",   # A3 — the out-of-set request is served
    "PLANT_REFUSAL_NOT_NATIVE":   "CHECK REFUSAL: FAIL",   # A3 — refused with a gov-os-shaped answer
    "PLANT_TRAIL_SKIP":           "CHECK TRAIL: FAIL",     # A3 — a crossing is not recorded as a row
}

# ── the nested-guest bridge (A1/A2-guest/A3-guest/A6-repro only) ─────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4a-accept"
_QEMU = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc"

# a UNIQUE gdb-stub port per boot: a SIGKILL'd qemu leaves its stub port in TIME_WAIT for ~a minute, so a
# fixed port would make later boots fail to bind and read empty (the P3b-3/4L discipline).
_GDB_BASE = 2000 + (os.getpid() % 2000)
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
_BUILD_CACHE = {}
_SERIAL_CACHE = {}


def _seed_guest():
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", outdir=None):
    """Build the body (with OUR sealed test worker) in the guest; return (outdir, elf_sha256, worker_sha)."""
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


def _guest_boot(outdir, timeout_s=16):
    """Boot the body in a NESTED qemu (gdb stub attached from the first line, L17); return serial text.
    Every boot is the guest's nested qemu — no host kernel. Boots are SERIALIZED (guest-to-itself)."""
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d %s -gdb tcp::%d -kernel %s/body.img </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, _next_gdb_port(), outdir)],
        capture_output=True, timeout=timeout_s + 20)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault=""):
    """Build+boot once per fault, cached (each guest boot is ~15s serialized)."""
    if fault not in _SERIAL_CACHE:
        out, _elf, _w = _guest_build(fault)
        _BUILD_CACHE[fault] = out
        _SERIAL_CACHE[fault] = _guest_boot(out)
    return _SERIAL_CACHE[fault]


def _trail_rows(serial):
    """Parse the body's crossing-trail readback into a list of (seq, req, arg, ans, verdict)."""
    rows = []
    for m in re.finditer(r"TRAIL row=0x([0-9a-f]+) req=0x([0-9a-f]+) arg=0x([0-9a-f]+) ans=0x([0-9a-f]+) (SERVED|REFUSED)",
                         serial):
        rows.append((int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4), m.group(5)))
    return rows


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
class TestA1LoadRunUnprivilegedAndCross(unittest.TestCase):
    def test_the_body_loads_and_runs_our_worker_unprivileged_and_its_requests_cross(self):
        serial = _serial()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("LONGMODE: OK", serial, "the body is in the machine's long mode (P3b-4L)")
        self.assertIn("ENCLOSURE: bring-up", serial, "the enclosure phase reached bring-up")
        # the SEALED image was loaded by the body's OWN ELF64 loader (bytes from the image), digest-checked.
        self.assertIn("LOAD: OK (digest matches the seal)", serial, "the sealed image loaded, digest-checked")
        m = re.search(r"WORKER-IMG-SHA256: ([0-9a-f]{64})", serial)
        self.assertIsNotNone(m, "the loader folded the sealed image's bytes and reported the digest")
        # the worker ran at USER privilege (ring 3), read FROM THE MACHINE (its CS/SS RPL).
        cs = re.search(r"WORKER-CS: 0x([0-9a-f]+)", serial)
        ss = re.search(r"WORKER-SS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(cs); self.assertIsNotNone(ss)
        self.assertEqual(int(cs.group(1), 16) & 3, 3, "the worker's CS RPL is 3 (unprivileged)")
        self.assertEqual(int(ss.group(1), 16) & 3, 3, "the worker's SS RPL is 3 (unprivileged)")
        # the requests crossed IN and BACK — five crossings, and the round-trip answer was read by the worker.
        cx = re.search(r"CROSSINGS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(cx)
        self.assertEqual(int(cx.group(1), 16), 5, "report-priv, echo, putc, out-of-set, exit")
        rows = _trail_rows(serial)
        echo = [r for r in rows if r[1] == 0x2]
        self.assertTrue(echo and echo[0][2] == "0000000000001234" and echo[0][3] == "0000000000001234",
                        "the ECHO round-trip: the body sent the argument back and the worker read it")
        self.assertTrue(any(r[1] == 0x3 for r in rows), "the worker announced (PUTC) after reading the answer")
        self.assertIn("CHECK CROSSING: PASS", serial, "the crossing is the machine's own")
        self.assertIn("ENCLOSURE: PASS", serial, "the enclosure self-check passes as a group")
        self.assertIn("ENCLOSURE-ACTS: PASS", serial)
        # the twelve rows' digest is STILL on serial after the enclosure.
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")


# ── A2 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2UnprivilegedAndTheCrossingIsTheMachines(unittest.TestCase):
    def test_the_worker_is_unprivileged_read_from_the_machine(self):
        serial = _serial()
        # read from the machine — not by convention: the CPU pushed the ring-3 CS at the trespass #PF too.
        self.assertIn("CHECK RING3: PASS", serial, "the worker runs at ring 3 (CS/SS RPL 3, read from the machine)")
        fault = re.search(r"TRESPASS-FAULT: vec=0x([0-9a-f]+) cr2=0x([0-9a-f]+) faultcs=0x([0-9a-f]+)", serial)
        self.assertIsNotNone(fault, "the body caught the trespass fault")
        self.assertEqual(int(fault.group(1), 16), 14, "a #PF (vector 14) — the machine faulted the direct reach")
        self.assertEqual(int(fault.group(3), 16) & 3, 3, "the CPU pushed the ring-3 CS at the fault (RPL 3)")
        self.assertIn("CHECK TRESPASS: PASS", serial, "the direct reach at body memory is FAULTED by the hardware")

    def test_each_hardware_fact_plant_reds_its_own_check(self):
        for fault in ("PLANT_WORKER_RING0", "PLANT_BODY_USER_ACCESSIBLE", "PLANT_NO_SYSCALL_MSR"):
            serial = _serial(fault)
            self.assertIn(FAULT_TO_FAILED_CHECK[fault], serial,
                          "%s must red %r (the check can fail, A2)" % (fault, FAULT_TO_FAILED_CHECK[fault]))
            self.assertIn("ENCLOSURE: FAIL", serial, "%s must red the aggregate ENCLOSURE line" % fault)


# ── A3 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA3EveryRequestARowAndOutOfSetRefusedNative(unittest.TestCase):
    def test_every_request_is_a_row_and_the_out_of_set_is_refused_native_and_a_row(self):
        serial = _serial()
        rows = _trail_rows(serial)
        # the body's own append-only trail: the load marker (0xf0) + five crossings = six rows.
        self.assertIn("TRAIL-ROWS: 0x00000006", serial, "six trail rows (the load marker + five crossings)")
        self.assertEqual([r[0] for r in rows], list(range(len(rows))), "the trail is append-only, seq in order")
        self.assertTrue(any(r[1] == 0xf0 and r[4] == "SERVED" for r in rows),
                        "the sealed-image LOAD is a row (the body's own trail)")
        # the out-of-set request (99 = 0x63) is REFUSED as the worker's OWN native failure (-ENOSYS) AND a row.
        oos = [r for r in rows if r[1] == 0x63]
        self.assertTrue(oos, "the out-of-set request is recorded as a row")
        self.assertEqual(oos[0][4], "REFUSED", "the out-of-set request is refused")
        self.assertEqual(oos[0][3], NATIVE_FAIL, "refused as the native -ENOSYS answer (0xffffffffffffffda)")
        oa = re.search(r"OUTOFSET-ANS: 0x([0-9a-f]+)", serial)
        self.assertEqual(oa.group(1), NATIVE_FAIL, "the native failure answer the worker sees")
        # every crossing is a row (the check the body runs).
        self.assertIn("CHECK TRAIL: PASS", serial, "every crossing recorded as a row")
        self.assertIn("CHECK REFUSAL: PASS", serial, "the out-of-set refused as the native failure shape")

    def test_the_trail_and_refusal_plants_red_their_own_check(self):
        for fault in ("PLANT_OUTOFSET_SERVED", "PLANT_REFUSAL_NOT_NATIVE", "PLANT_TRAIL_SKIP"):
            serial = _serial(fault)
            self.assertIn(FAULT_TO_FAILED_CHECK[fault], serial,
                          "%s must red %r (A3)" % (fault, FAULT_TO_FAILED_CHECK[fault]))
            self.assertIn("ENCLOSURE: FAIL", serial, "%s must red the aggregate ENCLOSURE line" % fault)

    def test_a_planted_image_byte_change_is_refused_at_load_and_is_a_row(self):
        # the SEAL: a byte change in the sealed worker image is REFUSED AT LOAD (a digest change is
        # refused, archi :4085 (b)) — the worker never runs, and the refusal is a trail row.
        serial = _serial("PLANT_WORKER_IMAGE_TAMPER")
        self.assertIn("LOAD: REFUSED (digest mismatch", serial, "a tampered sealed image is refused at load")
        self.assertNotIn("WORKER-CS:", serial, "a refused image never runs the worker")
        self.assertNotIn("ENCLOSURE: PASS", serial, "a digest change is never accepted")
        rows = _trail_rows(serial)
        self.assertTrue(any(r[1] == 0xf0 and r[4] == "REFUSED" for r in rows),
                        "the load refusal is a row of the body's own trail")


# ── A4 ───────────────────────────────────────────────────────────────────────────────────────────
class TestA4AttestedByNameWitnessClassesApart(unittest.TestCase):
    def test_our_worker_and_the_enclosure_c_are_attested_by_name_and_count_is_85(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        for rel in NEW_ENCL_FILES:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s is not attested by name (§9 mechanism 1)" % rel)
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "the 31 src/body/ source files (30 + 1 net.c, C7 P3b-6a)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "79 -> 85 (the 6 enclosure files) -> 87 (the 2 serve files, C7 P3b-4b) -> 88 (+1 net.c, C7 P3b-6a)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers the new C/.S/.ld")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list (I7)")

    def test_the_built_worker_image_is_never_a_signed_member(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built worker image (worker.elf) is NEVER a signed member")

    def test_the_p2_host_crossing_census_stays_clean_and_can_fail(self):
        from tools.conformance import host_crossing_census as census
        self.assertEqual(census.undeclared_crossings(), {}, "the core (src/body included) is host-clean")
        tmp = tempfile.mkdtemp(prefix="p3b4a-a4-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "body"))
        with open(os.path.join(tmp, "body", "planted.py"), "w", encoding="utf-8") as f:
            f.write("def go():\n    return open('/etc/hostname').read()  # a DIRECT crossing\n")
        self.assertIn("body/planted.py", census.undeclared_crossings(src_dir=tmp),
                      "a direct open() in a body .py must red the P2 census")


# ── A5 ───────────────────────────────────────────────────────────────────────────────────────────
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
        tmp = tempfile.mkdtemp(prefix="p3b4a-a5-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "compose_planted.py"), "w", encoding="utf-8") as f:
            f.write("from body import kmain  # stand the body as the production performer\n")
        self.assertTrue(any(rel == "kernel/compose_planted.py"
                            for rel, _pat in _production_standing_hits(tmp)),
                        "a planted production-standing import must red the scan")

    def test_the_enclosure_slice_is_new_files_only(self):
        for rel in NEW_ENCL_FILES:
            self.assertTrue(os.path.exists(os.path.join(SRC, rel)), "%s exists" % rel)


# ── A6 ───────────────────────────────────────────────────────────────────────────────────────────
class TestA6NoFoundingTwelveActs(unittest.TestCase):
    def test_no_founding_act_kinds_twelve_pack_byte_unchanged(self):
        import json
        from kernel.boot import ACT_KIND_RECORD_KIND

        with open(os.path.join(SRC, "founding", "founding-pack.json"), encoding="utf-8") as f:
            pack = json.load(f)
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
        self.assertEqual(len(kinds), 12, "ACT_KINDS stays twelve — the crossing is HOW acts are requested")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A6-repro needs the guest toolchain to build the .elf twice")
class TestA6ElfReproducible(unittest.TestCase):
    def test_the_body_elf_and_worker_image_are_byte_reproducible(self):
        _, sha1, w1 = _guest_build(outdir=_WD + "/repro1")
        _, sha2, w2 = _guest_build(outdir=_WD + "/repro2")
        self.assertEqual(sha1, sha2, "two builds of the body produce a byte-identical .elf")
        self.assertTrue(w1 and w1 == w2, "the sealed worker image is byte-reproducible (its seal is stable)")


if __name__ == "__main__":
    unittest.main()
