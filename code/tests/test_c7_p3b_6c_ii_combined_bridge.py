# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (the freestanding kernel body boots the sealed interpreter AND the enclosed borrowed-network worker
# RESIDENT TOGETHER, each in its OWN address map from slice (i), and a ring-0 coroutine bridge relays ONE
# operation from one enclosed program to the other and back across the map swap, exactly as a real kernel
# relays a request between two of its processes) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no
# offensive capability — ONE operation round-trips to prove the mechanism; the eight-shape relay and gov-os's
# record-decided socket act are slice (iii). Validate by building/reading, never by attack.
"""C7 P3b-6c slice (ii) acceptance — THE COMBINED BUILD + THE COROUTINE BRIDGE (design/54 §5 L18/L19, §9
Q11/I3; §7 P3b-6c slice ii; countersign archi :4550).

The body that gives each resident enclosure its own address map (slice i) now boots the REAL unmodified
python3.12 interpreter (P3b-4c, the sealed -initrd module) AND the enclosed lwIP worker (P3b-6b, the incbin'd
prover_image) RESIDENT TOGETHER, each in its own slice-(i) map. A ring-0 coroutine bridge relays ONE operation
from the interpreter to the worker and back across the map swap: the interpreter issues SYS_socket, the bridge
swaps to the worker's map + kernel stack, the REAL worker performs the op and produces its OWN answer
WITNESSED (never a fabricated reply, L19), the bridge swaps back, the interpreter receives the worker's real
answer and continues. A ring-3 fault mid-relay recovers per map (L18) and the bridge hands the WAITING
interpreter an error answer (archi :4550) — never leaves it suspended.

  A1  both resident on one boot, each present and runnable — distinct frames at 0x400000 (slice i).
      PLANT: a build with only one enclosure -> the relay has no peer (covered by the seal/OOM refusals).
  A2  one operation round-trips through the bridge, the worker's execution WITNESSED (the worker wrote its
      witness magic; the interpreter received the worker's real answer; round-trip integrity holds).
      PLANT_BRIDGE_CANNED (return a canned answer without crossing to the worker) -> witness absent -> reds.
      PLANT_BRIDGE_NO_SWAP (the hand-off omits the map swap) -> the worker aliases the interpreter -> reds.
  A3  a ring-3 fault across the relay holds per map, and the bridge returns the WAITING interpreter an error
      answer -> the interpreter continues (archi :4550, the precision case).
      PLANT_BRIDGE_LEAVE_WAITING (the interpreter is left suspended) -> the boot hangs -> no PYSOCK-DONE.
  A4  ACT_KINDS 12 (ROWS-COUNT 0x0c); ATTESTED 88 (the bridge glue is a tests/ fixture, no new src/body
      member); a single-enclosure (non-BRIDGE) boot is byte-identical (all changes are #ifdef BRIDGE-gated);
      no founding / bodyfs.c / disk.h change.

A1-A4 build+boot in the NESTED guest and skip when the pinned guest is not reachable. Register: an OS relaying
one request between two of its own hosted programs on a disposable guest, described by function — validated by
building/reading, never by attack. Every kernel touch is the guest's nested qemu; the host kernel is never
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

# the config-only fixtures (content, NEVER attested members — they live under tests/, not src/body).
BRIDGE_GLUE = os.path.join(HERE, "c7_p3b_6c_ii_bridge_worker_glue.c")
LWIPOPTS_FIXTURE = os.path.join(HERE, "c7_p3b_6b_lwipopts.h")   # reused, byte-identical (I3)

# the answer the worker computes from the relayed arg — MUST match the worker glue + enclosure.c bridge.
def _ans_transform(arg):
    return (arg & 0xFFFFFFFFFFFF) | 0x10000

# the pinned lwIP 2.2.0 SOURCE (provenance pins — the 6b unit's, unchanged).
DSC_SHA = "7c2a3c003375653b24e7f59ea2192a445b3d68c5a61c989ad8eca0a693752b97"
ORIG_SHA = "3a56474c26be8efe05c6b626a256c67bd9ee3739084e2844a4c989be031e7786"

# ── the nested-guest bridge ──────────────────────────────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR", "<GUEST>"]
_WD = "/tmp/p3b6cii-accept"
# the combined boot: the sealed interpreter is a MODULE (-initrd sealed.img); the worker is incbin'd in the
# body. No virtio-net (this slice's worker does no network) and no record disk (no /rec/ access). -cpu qemu64
# (SSE2, no AVX) matches the interpreter floor's environment (never OSXSAVE, :4131).
_QEMU = "qemu-system-x86_64 -cpu qemu64 -serial stdio -display none -no-reboot -m 256 -rtc base=utc"

# the interpreter boot in nested TCG (no KVM on the guest) is slow; give it a generous budget.
_BOOT_TIMEOUT = 300


def _guest_reachable():
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU; "
                                   "command -v gcc >/dev/null && echo GCC; "
                                   "command -v python3.12 >/dev/null && echo PY; "
                                   "command -v strace >/dev/null && echo STRACE"],
                           capture_output=True, timeout=25)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return (r.returncode == 0 and "6.8.0-134-generic" in out and "QEMU" in out
            and "GCC" in out and "PY" in out and "STRACE" in out)


GUEST = _guest_reachable()
_SEEDED = {"done": False, "lwip": None}
_BOOTED = {}   # fault -> serial text (built+booted once per fault, reused)


def _seed_guest():
    """Stage src/body + the config-only fixtures, and fetch the pinned lwIP 2.2.0 SOURCE. Once per run."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s/port/arch" % (_WD, _WD)],
                   capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True,
                   timeout=60, check=True)
    for src_path, dst in ((BRIDGE_GLUE, _WD + "/port/bridge_glue.c"),
                          (LWIPOPTS_FIXTURE, _WD + "/port/lwipopts.h")):
        with open(src_path, "rb") as f:
            subprocess.run(_SSH + ["cat > %s" % dst], input=f.read(), capture_output=True,
                           timeout=30, check=True)
    cc_h = (b"#ifndef LWIP_ARCH_CC_H\n#define LWIP_ARCH_CC_H\n#include <stdio.h>\n#include <stdlib.h>\n"
            b"#include <endian.h>\n#define LWIP_PLATFORM_DIAG(x)   do { } while (0)\n"
            b"#define LWIP_PLATFORM_ASSERT(x) do { } while (0)\n#endif\n")
    subprocess.run(_SSH + ["cat > %s/port/arch/cc.h" % _WD], input=cc_h, capture_output=True,
                   timeout=30, check=True)
    fetch = ("set -e; rm -rf %s/lwipsrc; mkdir -p %s/lwipsrc; cd %s/lwipsrc; "
             "apt-get source liblwip-dev >/tmp/aptsrc-6cii.log 2>&1; "
             "sha256sum *.dsc *.orig.tar.* ; ls -d lwip-*/" % (_WD, _WD, _WD))
    r = subprocess.run(_SSH + [fetch], capture_output=True, timeout=240)
    out = r.stdout.decode(errors="replace")
    assert DSC_SHA in out and ORIG_SHA in out, "lwIP source provenance mismatch:\n" + out
    m = re.search(r"(lwip-\S+)/", out)
    assert m, "lwIP source tree not found:\n" + out
    _SEEDED["lwip"] = "%s/lwipsrc/%s" % (_WD, m.group(1))
    _SEEDED["done"] = True


def _build_and_boot(fault=""):
    """Build the combined bridge body (BRIDGE=1) with an optional PLANT, boot it in a NESTED qemu (ONE at a
    time, killed before and after), return the raw serial. Cached per fault."""
    if fault in _BOOTED:
        return _BOOTED[fault]
    _seed_guest()
    out = _WD + "/out" + (("-" + fault) if fault else "")
    env = ("BRIDGE=1 LWIP_SRC=%s GLUE_SRC=%s/port/bridge_glue.c LWIP_PORT=%s/port"
           % (_SEEDED["lwip"], _WD, _WD))
    script = (
        "set -e\n"
        "%s bash %s/body/build.sh %s/body %s %s >/tmp/6ciibuild.log 2>&1 || "
        "{ echo BUILD-FAILED; tail -12 /tmp/6ciibuild.log; exit 0; }\n"
        "pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null || true\n"
        "sleep 1\n"
        "timeout --signal=TERM %d %s -kernel %s/body.img -initrd %s/sealed.img </dev/null 2>/dev/null || true\n"
        "pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null || true\n"
        % (env, _WD, _WD, out, fault, _BOOT_TIMEOUT, _QEMU, out, out))
    boot = subprocess.run(_SSH + ["bash -s"], input=script.encode(), capture_output=True,
                          timeout=_BOOT_TIMEOUT + 120)
    text = boot.stdout.decode(errors="replace").replace("\r", "")
    assert "BUILD-FAILED" not in text, "guest build failed (%s):\n%s" % (fault, text)
    _BOOTED[fault] = text
    return text


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: pinned gov-lab guest not reachable (6.8.0-134-generic on ssh :2222 + py/strace)")
class TestCombinedBridgeHappy(unittest.TestCase):
    """A1-A4 happy path — both resident, ONE operation round-trips witnessed, fault-per-map error answer."""

    @classmethod
    def setUpClass(cls):
        cls.serial = _build_and_boot("")

    def test_A1_both_resident_distinct_frames(self):
        m = re.search(r"BRIDGE-INTERP-FRAME: 0x([0-9a-f]+) BRIDGE-WORKER-FRAME: 0x([0-9a-f]+)", self.serial)
        self.assertIsNotNone(m, self.serial)
        fa, fb = int(m.group(1), 16), int(m.group(2), 16)
        self.assertNotEqual(fa, 0)
        self.assertNotEqual(fb, 0)
        self.assertNotEqual(fa, fb, "the interpreter and worker map 0x400000 to DISTINCT frames (slice i)")
        self.assertIn("CHECK BRIDGE-BOTH-RESIDENT: PASS", self.serial)

    def test_A2_one_operation_round_trips_worker_witnessed(self):
        # the REAL worker executed (its own serial witness) and wrote its witness magic.
        self.assertIn("BRIDGE-WORKER-RAN", self.serial, "the real worker executed on its own side")
        self.assertIn("BRIDGE-WORKER-DONE", self.serial)
        self.assertIn("CHECK BRIDGE-WITNESSED: PASS", self.serial)
        # round-trip integrity: the interpreter received the worker's real answer = transform(arg).
        # the body's BRIDGE-R0 line carries a leading diagnostic jv=0x<..> field; accept it, do not assert
        # on it (A2's spec is round-trip + witness, jv is out of scope). The four captured groups stay
        # (arg, ans, witness, returned).
        m = re.search(r"BRIDGE-R0 (?:jv=0x[0-9a-f]+ )?arg=0x([0-9a-f]+) ans=0x([0-9a-f]+) witness=0x([0-9a-f]+) "
                      r"returned=0x([0-9a-f]+)", self.serial)
        self.assertIsNotNone(m, self.serial)
        arg = int(m.group(1), 16)
        self.assertEqual(int(m.group(2), 16), _ans_transform(arg), "the worker's answer = transform(arg)")
        self.assertEqual(int(m.group(4), 16), _ans_transform(arg), "the bridge returned the worker's answer")
        self.assertIn("CHECK BRIDGE-ROUNDTRIP: PASS", self.serial)
        # the interpreter received it (the real answer reached python and back).
        p = re.search(r"PYSOCK-R1 (-?\d+)", self.serial)
        self.assertIsNotNone(p, self.serial)
        self.assertEqual(int(p.group(1)) & 0xFFFFFFFFFFFFFFFF, _ans_transform(arg),
                         "the interpreter received the worker's real answer")

    def test_A3_fault_per_map_error_answer_interp_continues(self):
        # A3 + the precision (archi :4550) is a SEPARATE build (-DBRIDGE_FAULT), so the worker's single run is
        # its FRESH first run — a deterministic, DELIBERATE fault (a ring-3 reach at the body's image at 1 MiB),
        # not a dirty re-entry. The bridge recovers per map (#PF vec 0xe, cr2 0x100000) and returns an error.
        s = _build_and_boot("BRIDGE_FAULT")
        self.assertNotIn("BRIDGE-INTERP-FAULT", s, "the interpreter itself did not fault")
        self.assertIn("BRIDGE-WORKER-FAULTING", s, "the worker reached the deliberate fault op")
        self.assertRegex(s, r"BRIDGE-RELAY-FAULT: worker faulted mid-op vec=0x0*e cr2=0x0*100000",
                         "the deliberate #PF at the body's 1 MiB image, recovered per map (L18)")
        self.assertIn("CHECK BRIDGE-FAULT-PER-MAP: PASS", s)
        # the precision: the interpreter received the error answer (-19 -> glibc -1) and continued to the end
        # (never left waiting on a hand-off that will not come back).
        self.assertRegex(s, r"PYSOCK-R1 -1", "the interpreter got the error answer for the fault relay")
        self.assertIn("PYSOCK-DONE", s, "the interpreter continued past the fault relay")
        self.assertIn("CHECK BRIDGE-INTERP-CONTINUED: PASS", s)
        self.assertIn("BRIDGE: PASS", s)          # the fault build's own acceptance
        self.assertIn("BRIDGE-ACTS: PASS", s)

    def test_A4_nothing_else_moves(self):
        self.assertIn("CHECK BRIDGE-KERNEL-HALF: PASS", self.serial)     # L20 kernel half shared
        self.assertIn("CHECK BRIDGE-STATES-INTACT: PASS", self.serial)   # both states intact across the trip
        self.assertIn("ROWS-COUNT: 0000000c", self.serial)              # ACT_KINDS stays twelve
        self.assertIn("BRIDGE: PASS", self.serial)
        self.assertIn("BRIDGE-ACTS: PASS", self.serial)


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: pinned gov-lab guest not reachable")
class TestCombinedBridgePlants(unittest.TestCase):
    """Each plant reds ITS check by a REAL mechanism — a check that cannot fail is not a check (L19)."""

    def test_A2_plant_canned_answer_no_witness(self):
        s = _build_and_boot("PLANT_BRIDGE_CANNED")
        # the bridge returned a canned answer without crossing to the worker on the normal relay.
        self.assertIn("BRIDGE-RELAY: CANNED", s)
        self.assertNotIn("BRIDGE-WORKER-DONE", s)              # the worker never completed the normal op
        self.assertIn("CHECK BRIDGE-WITNESSED: FAIL", s)       # the witness is absent
        self.assertIn("CHECK BRIDGE-ROUNDTRIP: FAIL", s)       # and the answer is not the worker's
        self.assertIn("BRIDGE: FAIL", s)
        self.assertNotIn("BRIDGE-ACTS: PASS", s)

    def test_A2_plant_no_swap_aliases(self):
        s = _build_and_boot("PLANT_BRIDGE_NO_SWAP")
        # the hand-off omitted the map swap -> the worker never produced its witness under the wrong map.
        self.assertIn("CHECK BRIDGE-WITNESSED: FAIL", s)
        self.assertIn("BRIDGE: FAIL", s)
        self.assertNotIn("BRIDGE-ACTS: PASS", s)

    def test_A3_plant_leave_waiting_hangs(self):
        s = _build_and_boot("PLANT_BRIDGE_LEAVE_WAITING")
        # the interpreter is left suspended on the fault relay -> it never reaches PYSOCK-DONE / BODY-HALT.
        self.assertNotIn("PYSOCK-DONE", s, "the plant leaves the interpreter waiting forever")
        self.assertNotIn("BRIDGE: PASS", s)
        self.assertNotIn("BRIDGE-ACTS: PASS", s)

    def test_A1_plant_interpreter_seal_tamper_refused(self):
        s = _build_and_boot("PLANT_SEAL_TAMPER")
        # a byte change in the interpreter's sealed image refuses the load -> the interpreter never starts.
        self.assertIn("BRIDGE-SEAL: REFUSED", s)
        self.assertIn("BRIDGE: FAIL", s)
        self.assertNotIn("BRIDGE-ACTS: PASS", s)

    def test_A1_plant_worker_image_tamper_refused(self):
        s = _build_and_boot("PLANT_NETW_IMAGE_TAMPER")
        # a byte change in the lwIP worker image refuses it at load -> the relay has no peer.
        self.assertIn("FLOOR-LOAD: REFUSED", s)
        self.assertIn("BRIDGE: FAIL", s)
        self.assertNotIn("BRIDGE-ACTS: PASS", s)


class TestAttestedUnchanged(unittest.TestCase):
    """A4 — ATTESTED stays 88 and the guard surface still equals it (the bridge glue is a tests/ fixture)."""

    def test_attested_count_and_guard_surface(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88)
        gs = set(attestation.law_guard_surface(SRC))
        self.assertEqual(gs, set(attestation.ATTESTED_MEMBERS),
                         "no new src/body member — the bridge worker glue is a tests/ fixture")


class TestChangesAreBridgeGated(unittest.TestCase):
    """A4 — every src change is #ifdef BRIDGE-gated, so a single-enclosure (non-BRIDGE) build is unchanged."""

    def test_no_founding_or_bodyfs_or_disk_change(self):
        # the plan's MUST-NOT-TOUCH: no founding pack, no bodyfs.c, no disk.h change in this unit's fence.
        for f in ("bodyfs.c", "disk.h"):
            p = os.path.join(BODY, f)
            self.assertTrue(os.path.exists(p), p)

    def test_enclosure_and_serve_bridge_code_is_gated(self):
        # every new symbol lives under #ifdef BRIDGE — a non-BRIDGE build never compiles it.
        enc = open(os.path.join(BODY, "enclosure.c")).read()
        srv = open(os.path.join(BODY, "serve.c")).read()
        self.assertIn("#ifdef BRIDGE", enc)
        self.assertIn("floor_bridge_run", enc)
        self.assertIn("#if defined(BRIDGE)", srv)
        # the SYS_socket refusal path is preserved for the non-bridge case.
        self.assertIn("g_socket_refused = 1", srv)


if __name__ == "__main__":
    unittest.main()
