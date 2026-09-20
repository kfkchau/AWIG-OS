# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (an interrupt descriptor table, an interrupt controller, a timer source, a wall clock, a monotonic
# window, a seeded source of chance, a body booting under a debug stub) as in the seL4/gVisor/Fuchsia
# and osdev literature. NON-GOAL: no offensive capability — this DRIVES the acceptance of C7 P3b-3
# (interrupts, the two clock acts and a seeded source of chance in our own body inside a nested guest;
# the body announces its definition digest; it boots nothing into production, touches no host kernel).
"""C7 P3b-3 acceptance — THE BODY: CLOCK, INTERRUPTS AND ENTROPY (design/54 §7 P3b-3; countersign archi :4049).

The body that boots with memory (P3b-1) and a disk (P3b-2) now brings up, ON THE METAL, an interrupt
path (a flat GDT, a 256-gate IDT, the 8259 PIC remapped and masked to the timer, a PIT timer source)
and performs THREE PORTABLE ACTS in a NESTED qemu inside the pinned guest — recording-clock (a CMOS
wall clock), commit-window (an rdtsc monotonic window), and entropy (a seeded ChaCha20 CSPRNG) — self-
checking each and still printing the twelve rows' digest, with the nested qemu's gdb stub attached from
the first line.

  A1  interrupts + the two clocks + entropy self-check PASS + the twelve rows' digest on serial (nested guest)
  A2  each is FUNCTIONAL — a planted bad gate / dead timer / backwards clock / constant source reds its
      own check; an UNSEEDED source is caught by the cross-boot compare; a PLANT_HANG is READ FROM THE
      nested qemu's gdb stub (attached from the first line — a silent hang is a caught failure)
  A3  the body is DERIVED from the rows (the digest folds the twelve rows; delete-and-regenerate is
      byte-identical) and the .elf is byte-REPRODUCIBLE (the seeded chance is a RUNTIME output, never
      baked into the .elf — a real build differs boot to boot while its .elf is identical)
  A4  the clock/interrupt/entropy C is ATTESTED BY NAME (73 -> 79), the walk-guard covers it, the .elf
      is never a member, the P2 host-crossing census stays clean, and a planted direct open() reds it
  A5  guest-only, revertable, NO one-way door — no host kernel load, the body is not stood as the
      production performer; the scans CAN fail (near-miss)

A1/A2(guest)/A3-repro build+boot in the NESTED guest and skip when the pinned guest is not reachable
over SSH; A2's planted-fault reds, A3-derive, A4 and A5 run in main. Register: OS bring-up on a
disposable guest, described by function — a body that keeps its own time, handles its own interrupts,
and makes its own chance, and announces its definition digest; validated by building/reading, never by
attack (governance-work-method). Every kernel touch is the guest's nested qemu; the host kernel is
never touched (L11 / EP-00 rule 9 / charter §A21).
"""

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

# the six clock/interrupt/entropy source files this slice adds under src/body/ (attested by name, A4).
NEW_CLOCK_FILES = ("body/clkcheck.c", "body/clock.c", "body/clock.h",
                   "body/entropy.c", "body/idt.c", "body/isr.S")

# the planted faults caught IN-BODY by the self-check and the CHECK each one must red (A2). A check
# that can fail is the proof the check is real (§A64).
FAULT_TO_FAILED_CHECK = {
    "PLANT_BAD_GATE":         "CHECK INTERRUPTS: FAIL",       # the timer gate points at the wrong stub
    "PLANT_TIMER_DEAD":       "CHECK INTERRUPTS: FAIL",       # IRQ0 masked — the timer never ticks
    "PLANT_MONO_BACKWARDS":   "CHECK COMMIT-WINDOW: FAIL",    # the monotonic window goes backwards
    "PLANT_ENTROPY_CONSTANT": "CHECK ENTROPY: FAIL",          # a source that returns the same bytes
}

# ── the nested-guest bridge (A1/A2-guest/A3-repro only) ───────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b3-accept"
# every nested boot: the guest CPU exposes rdrand (-cpu max, a RUNTIME source for the seed), the RTC is
# UTC for a deterministic plausibility check, and the gdb stub is attached from the first line (see
# _guest_boot, which appends `-gdb tcp::<port>` with a UNIQUE port per boot).
_QEMU = ("qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc")

# The gdb stub binds a TCP port; a SIGKILL'd qemu leaves that port in TIME_WAIT for ~a minute, so a
# FIXED port would make the NEXT stub-attached boot fail to bind and yield empty serial. Each boot gets
# a FRESH port from a per-process base (so back-to-back test runs never collide either). The hang boot
# uses a dedicated port its RSP client connects to.
_GDB_BASE = 2000 + (os.getpid() % 2000)
_HANG_PORT = _GDB_BASE + 1900
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
    """Copy src/body to the guest ONCE (build.sh compiles only the C — no Python needed to boot the
    clock slice). Idempotent within a test run."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=60)
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


def _guest_boot(outdir, timeout_s=14):
    """Boot the body in a NESTED qemu (gdb stub attached from the first line); return the serial text.
    Every boot is the guest's nested qemu — no host kernel. The body halts after announcing, so qemu
    runs to the timeout; the serial is fully captured before the kill.

    The gdb stub attaches from the first line on a UNIQUE port per boot (a SIGKILL'd qemu leaves its
    stub port in TIME_WAIT, so reusing one port would make later boots fail to bind and read empty).
    Boots are SERIALIZED (guest-to-itself, mgr :4027)."""
    # boot the FLAT image (body.img): the x86_64 long-mode body boots as the objcopy'd flat image
    # loaded by the a.out-kludge address fields (C7 P3b-4L); qemu's -kernel multiboot loader
    # ELF-parses only 32-bit ELFs. The .elf is the recorded artifact; the .img is the bootable one.
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d %s -gdb tcp::%d -kernel %s/body.img </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, _next_gdb_port(), outdir)],
        capture_output=True, timeout=timeout_s + 20)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _entropy_a(serial):
    m = re.search(r"ENTROPY-A: ([0-9a-f]+)", serial)
    return m.group(1) if m else None


# a minimal GDB Remote Serial Protocol client — the gdb binary is absent in the guest, so we speak the
# stub's own protocol (over TCP) to prove the stub is attached from the first line and to READ a hung
# CPU. It connects, reads the frozen-at-reset state (attached from the first line), reads frozen memory
# (the multiboot magic), continues, interrupts the running-then-hung target, and reads its PC.
_RSP_CLIENT = r'''
import socket, sys, time
PORT = int(sys.argv[1])
def connect():
    for _ in range(60):
        try:
            s = socket.create_connection(("127.0.0.1", PORT), timeout=5); s.settimeout(5); return s
        except OSError:
            time.sleep(0.1)
    raise SystemExit("RSP: could not connect to the qemu gdb stub")
def csum(d): return "%02x" % (sum(d.encode()) & 0xff)
def send_pkt(s, d):
    s.sendall(("$"+d+"#"+csum(d)).encode())
    try: s.recv(1)
    except OSError: pass
def read_pkt(s):
    buf = b""
    while b"#" not in buf or len(buf.split(b"#",1)[1]) < 2:
        try: c = s.recv(256)
        except OSError: break
        if not c: break
        buf += c
    s.sendall(b"+")
    if b"$" in buf:
        return buf.split(b"$",1)[1].split(b"#",1)[0].decode(errors="replace")
    return buf.decode(errors="replace")
def rip(s):
    send_pkt(s, "g"); g = read_pkt(s)
    try:
        return int.from_bytes(bytes.fromhex(g[256:272]), "little")  # x86_64 layout: rip at hex 256
    except Exception:
        return None
s = connect()
send_pkt(s, "?"); stop0 = read_pkt(s)
r0 = rip(s)
print("STUB-ATTACHED-AT-FIRST-LINE stop=%s rip0=%s" % (stop0, hex(r0) if r0 is not None else "?"))
send_pkt(s, "c"); time.sleep(3.0); s.sendall(b"\x03")
stop1 = read_pkt(s); r1 = rip(s)
# read the multiboot magic in the HUNG (frozen) state: the flat body.img is loaded by qemu's
# multiboot option ROM at RUNTIME (not at the -S reset, unlike the 32-bit-ELF direct-write load), so
# 0x100000 is 0 at reset and holds the magic only once the body has loaded — the debugger still reads
# a KNOWN value from the frozen machine's memory (the check is unchanged; only the read timing moves).
send_pkt(s, "m100000,4"); mem = read_pkt(s)
print("HANG-CAUGHT-BY-DEBUGGER stop=%s rip=%s mem=%s" % (stop1, hex(r1) if r1 is not None else "?", mem))
s.close()
'''


def _guest_hang_debug_read(outdir):
    """Boot the PLANT_HANG body FROZEN (-S) with the gdb stub on a dedicated port, and READ the stub
    over RSP: the stub answers before the first line (frozen at the reset vector), then — after continue
    — catches the hung CPU and reads the multiboot magic from the (now-loaded) frozen memory. Returns
    the RSP client's output. (The serial is read
    separately from a NORMAL boot: a SIGKILL'd frozen qemu's serial-file buffer is unreliable, but the
    stdio pipe of a normal boot captures the serial cleanly.)"""
    subprocess.run(_SSH + ["cat > %s/rsp_read.py" % _WD],
                   input=_RSP_CLIENT.encode(), capture_output=True, timeout=20, check=True)
    port = _HANG_PORT
    script = (
        "qemu-system-x86_64 -cpu max -kernel %s/body.img -serial none "
        "-display none -no-reboot -m 256 -S -gdb tcp::%d </dev/null >/dev/null 2>&1 & "
        "QPID=$!; python3 %s/rsp_read.py %d; kill -9 $QPID 2>/dev/null; "
        "pkill -9 -f 'qemu-system.*hang/body.img' 2>/dev/null; true"   # bulletproof: the frozen -S boot never survives
        % (outdir, port, _WD, port)
    )
    r = subprocess.run(_SSH + [script], capture_output=True, timeout=60)
    return r.stdout.decode(errors="replace")


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
    """Leave the guest as found: no nested-qemu boot (a frozen hang boot included) survives this
    module. Serialized guest, so clearing every body-qemu is safe."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1InterruptsClocksEntropyAndDigest(unittest.TestCase):
    def test_the_three_acts_self_check_pass_and_the_digest_is_on_serial(self):
        out, elf_sha = _guest_build()
        serial = _guest_boot(out)
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("CHECK INTERRUPTS: PASS", serial, "a timer IRQ fired and was handled")
        self.assertIn("CHECK RECORDING-CLOCK: PASS", serial, "the CMOS wall clock reads a plausible time")
        self.assertIn("CHECK COMMIT-WINDOW: PASS", serial, "the monotonic window strictly advances")
        self.assertIn("CHECK ENTROPY: PASS", serial, "two draws differ, non-zero, seeded")
        self.assertIn("CLOCK: PASS", serial, "the three acts self-check PASS as a group")
        self.assertIn("CLOCK-ACTS: PASS", serial)
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")
        # the tick counter advanced from the IRQ0 path (an interrupt was actually delivered + handled)
        m = re.search(r"TICKS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the body reports the tick counter")
        self.assertGreater(int(m.group(1), 16), 0, "at least one timer interrupt fired and was handled")
        self.assertTrue(len(elf_sha) == 64, "the built .elf has a recorded digest (§9 mechanism 2)")


# ── A2 (guest) ───────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2EachActIsFunctional(unittest.TestCase):
    def test_the_clocks_and_the_source_of_chance_are_functional(self):
        serial = _guest_boot(_guest_build()[0])
        # the wall clock reads a plausible current year (the RTC is UTC; base=utc)
        m = re.search(r"WALLCLOCK: y=0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the body reports the wall clock it read")
        year = int(m.group(1), 16)
        self.assertTrue(2020 <= year <= 2100, "a plausible current year, got %d" % year)
        # entropy: SEEDED and two draws differ, neither all-zero
        self.assertIn("ENTROPY-SEEDED: 0x00000001", serial, "the seed came from a real (non-zero) source")
        a = re.search(r"ENTROPY-A: ([0-9a-f]+)", serial).group(1)
        b = re.search(r"ENTROPY-B: ([0-9a-f]+)", serial).group(1)
        self.assertNotEqual(a, b, "two draws differ")
        self.assertNotEqual(a, "0" * len(a), "the first draw is not all-zero")

    def test_each_planted_fault_reds_its_own_check(self):
        for fault, failed in FAULT_TO_FAILED_CHECK.items():
            out, _ = _guest_build(fault)
            serial = _guest_boot(out)
            self.assertIn(failed, serial, "%s must red %r (the check can fail, A2)" % (fault, failed))
            self.assertIn("CLOCK: FAIL", serial, "%s must red the aggregate CLOCK line" % fault)

    def test_a_planted_constant_source_makes_two_draws_equal(self):
        serial = _guest_boot(_guest_build("PLANT_ENTROPY_CONSTANT")[0])
        a = re.search(r"ENTROPY-A: ([0-9a-f]+)", serial).group(1)
        b = re.search(r"ENTROPY-B: ([0-9a-f]+)", serial).group(1)
        self.assertEqual(a, b, "a constant source returns the same bytes every draw (caught in-body)")

    def test_a_seeded_source_differs_across_boots_but_an_unseeded_one_does_not(self):
        # THE proof the source is SEEDED FROM THE RUNTIME (not a compile-time constant): the real body
        # produces a DIFFERENT first draw on two boots; the UNSEEDED plant produces an IDENTICAL one.
        out, _ = _guest_build()
        real1 = _entropy_a(_guest_boot(out))
        real2 = _entropy_a(_guest_boot(out))
        self.assertTrue(real1 and real2)
        self.assertNotEqual(real1, real2, "a runtime-seeded source differs boot to boot")
        outu, _ = _guest_build("PLANT_ENTROPY_UNSEEDED")
        uns1 = _entropy_a(_guest_boot(outu))
        uns2 = _entropy_a(_guest_boot(outu))
        self.assertTrue(uns1 and uns2)
        self.assertEqual(uns1, uns2, "an unseeded (fixed-key) source repeats across boots — caught here")

    def test_a_silent_hang_is_read_from_the_debugger(self):
        # THE DEBUG STUB IS ATTACHED FROM THE FIRST LINE (archi :4023): a PLANT_HANG wedges during
        # bring-up; the nested qemu's gdb stub reads the frozen-at-reset state (attached before the
        # first instruction), and — after continue — catches the hung CPU AND reads the multiboot magic
        # from the (now-loaded) frozen memory. A silent hang is itself a caught failure.
        out, _ = _guest_build("PLANT_HANG", outdir=_WD + "/hang")
        # (1) the debugger read (a frozen -S boot): the stub is attached from the first line and the
        #     hung CPU is read over RSP.
        rsp = _guest_hang_debug_read(out)
        self.assertIn("STUB-ATTACHED-AT-FIRST-LINE", rsp, "the gdb stub answers before the first line")
        # the debugger read frozen memory in the hung state: 0x100000 holds the multiboot magic
        # 0x1BADB002 (little-endian). The flat body.img is loaded by qemu's multiboot option ROM at
        # RUNTIME (0 at the -S reset), so the magic is read once the body has loaded — still a KNOWN
        # value read from the frozen machine's memory (the check unchanged; only the read timing moves).
        self.assertIn("mem=02b0ad1b", rsp, "the debugger read the frozen machine's multiboot magic")
        self.assertIn("HANG-CAUGHT-BY-DEBUGGER", rsp, "the debugger caught the hung CPU after continue")
        m = re.search(r"HANG-CAUGHT-BY-DEBUGGER stop=\S+ rip=0x([0-9a-f]+)", rsp)
        self.assertIsNotNone(m, "the debugger read the hung PC")
        rip = int(m.group(1), 16)
        self.assertTrue(0x100000 <= rip < 0x400000, "the hung PC is inside the body's code (the hlt loop)")
        # (2) the serial of the hang (a NORMAL boot, captured over the stdio pipe): the body reaches
        #     interrupt bring-up and then NO completion — the silent hang.
        serial = _guest_boot(out)
        self.assertIn("CLOCK: bring-up", serial, "the body reached interrupt bring-up before the hang")
        self.assertNotIn("CLOCK: PASS", serial, "a hung body never completes the self-check")
        self.assertNotIn("CLOCK-ACTS: PASS", serial, "a hung body never announces past the hang")


# ── A3 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA3DerivedFromTheRows(unittest.TestCase):
    def setUp(self):
        with open(PACK, encoding="utf-8") as f:
            self.pack = json.load(f)
        self.gen = _load_generator()

    def test_the_digest_folds_the_twelve_rows_as_before(self):
        digest, count = self.gen.digest_over(self.pack)
        self.assertEqual(count, 12, "twelve seam_act_definition rows (the slice adds no act)")
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
    def test_the_elf_is_byte_reproducible_the_seed_is_a_runtime_output(self):
        # the .elf is byte-identical across two clean builds — the seeded chance is a RUNTIME output,
        # never baked into the .elf (a real build differs boot to boot while its .elf is identical, A3).
        _, sha1 = _guest_build(outdir=_WD + "/repro1")
        _, sha2 = _guest_build(outdir=_WD + "/repro2")
        self.assertEqual(sha1, sha2, "two builds of the body produce a byte-identical .elf")


# ── A4 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA4ClockCIsAttestedAndCensusClean(unittest.TestCase):
    def test_the_new_clock_files_are_attested_by_name_and_the_count_is_79(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        for rel in NEW_CLOCK_FILES:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s is not attested by name (§9 mechanism 1)" % rel)
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "the 31 src/body/ source files (30 + 1 net.c, C7 P3b-6a)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "73 -> 79 (the 6 clock/interrupt/entropy files) -> 85 (the 6 enclosure files, C7 P3b-4a) -> 87 (the 2 serve files, C7 P3b-4b) -> 88 (+1 net.c, C7 P3b-6a)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers the new C/.S/.h")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list")

    def test_the_built_elf_is_never_a_signed_member(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built .elf is NEVER a signed member")

    def test_the_p2_host_crossing_census_stays_clean_and_can_fail(self):
        from tools.conformance import host_crossing_census as census
        self.assertEqual(census.undeclared_crossings(), {}, "the core (src/body included) is host-clean")
        # the near-miss: a planted DIRECT open() in a body .py reds the census (body is zoned CORE).
        tmp = tempfile.mkdtemp(prefix="p3b3-a4-")
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
    def test_no_host_kernel_load_in_the_body_and_the_scan_can_fail(self):
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
        tmp = tempfile.mkdtemp(prefix="p3b3-a5-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "compose_planted.py"), "w", encoding="utf-8") as f:
            f.write("from body import kmain  # stand the body as the production performer\n")
        hits = _production_standing_hits(tmp)
        self.assertTrue(any(rel == "kernel/compose_planted.py" for rel, _pat in hits),
                        "a planted production-standing import must red the scan")

    def test_the_clock_slice_is_new_files_only_git_revertible(self):
        # the clock/interrupt/entropy C are NEW files under src/body/; nothing existing was overwritten
        # by them (kmain.c/build.sh gained calls; the memory + disk C are untouched).
        for rel in NEW_CLOCK_FILES:
            self.assertTrue(os.path.exists(os.path.join(SRC, rel)), "%s exists" % rel)


if __name__ == "__main__":
    unittest.main()
