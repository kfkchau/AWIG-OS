# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (per-enclosure ADDRESS MAPS: two enclosed user-space programs made resident at once on our own kernel
# body, each in its OWN page-table hierarchy whose user half is private and whose kernel half — the low
# identity + the higher-half direct map — is shared, so two programs based at the same virtual address
# 0x400000 coexist without aliasing, the map swapped at the coroutine hand-off, exactly as a real kernel
# runs two processes) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability — this
# DRIVES the acceptance of C7 P3b-6c slice (i). Validate by building/reading, never by attack.
"""C7 P3b-6c slice (i) acceptance — PER-ENCLOSURE ADDRESS MAPS (design/54 §5 L20/L18, §9 Q11/I3; §7 P3b-6c;
countersign archi :4542).

The body that hosts the interpreter (P3b-4c) and the borrowed lwIP worker (P3b-6b) — each of which loads at
base 0x400000 — now gives EACH RESIDENT ENCLOSURE ITS OWN page-table hierarchy. The hierarchies SHARE the
kernel half (the low identity [0, CANONICAL_BASE) + the higher-half direct map PML4[256]) and have a PRIVATE
user half, so two enclosures at virtual base 0x400000 map DISTINCT physical frames with no aliasing; the map
is swapped at the coroutine hand-off; a ring-3 fault under a worker's OWN map is recovered per map, the other
untouched. Proven on the body with OUR small maps prover instantiated as TWO resident enclosures.

  A1  two enclosures resident, each with its own map; each writes a distinct sentinel to the SAME virtual
      base 0x400000 and reads BACK ITS OWN — the two land on DISTINCT frames (no aliasing).
      PLANT_MAPS_SHARED (one map for both) -> the two ALIAS at 0x400000 -> CHECK MAPS-NO-ALIAS reds.
  A2  the hand-off swaps the active map and returns; the first enclosure's bytes at 0x400000 are INTACT
      after the second ran an operation under its own map.
      PLANT_MAPS_NO_SWAP (the hand-off does not swap) -> the second corrupts the first -> STATE-INTACT reds.
  A3  a ring-3 fault while a worker runs under ITS OWN map is recovered as an enclosure violation exactly as
      under the single map (#PF, vec 14), the other map untouched (L18).
      PLANT_MAPS_FAULT_NOSWAPBACK (the map not restored after the fault) -> the read lands the wrong map ->
      CHECK MAPS-FAULT-PER-MAP reds.
  A4  every enclosure map carries the kernel higher half byte-identical (L20); ACT_KINDS stays twelve
      (ROWS-COUNT 0x0c); ATTESTED unchanged (88 — the prover is a tests/ fixture, no new src/body member);
      the enclosure mechanism (P3b-4a) and the forty-nine (P3b-4b) still pass in the same boot.
      PLANT_MAPS_NO_KERNEL_HALF (a map missing PML4[256]) -> the body faults on its own direct map after a
      swap (EXC vector 0xe) -> no MAPS PASS.
  precision(archi :4542)  the run holds interrupts + the scheduler OFF across the hand-off (the borrowed-TCP
      6b shape), so the timer cannot preempt while a worker's map is active: MAPS-PREEMPT records g_sched_on
      == 0 and the preempt count == 0 — the on-body evidence that the coroutine hand-off alone suffices.

A1-A4 build+boot in the NESTED guest and skip when the pinned guest is not reachable; the ATTESTED count is
checked in main. Register: an OS giving each hosted program its own address space on a disposable guest,
described by function — validated by building/reading, never by attack. Every kernel touch is the guest's
nested qemu; the host kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
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

# the maps prover fixtures (content, NEVER attested members — they live under tests/, not src/body).
MAPS_S = os.path.join(HERE, "c7_p3b_6c_i_maps_prover.S")
MAPS_LD = os.path.join(HERE, "c7_p3b_6c_i_maps_prover.ld")

# ── the nested-guest bridge ──────────────────────────────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR", "<GUEST>"]
_WD = "/tmp/p3b6ci-test"
_QEMU = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc"


def _guest_reachable():
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU; "
                                   "command -v gcc >/dev/null && echo GCC"],
                           capture_output=True, timeout=20)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return r.returncode == 0 and "6.8.0-134-generic" in out and "QEMU" in out and "GCC" in out


GUEST = _guest_reachable()
_SEEDED = {"done": False}
_BOOTED = {}   # fault -> serial text (built+booted once per fault, reused)


def _seed_guest():
    """Copy src/body + the maps prover fixtures to the guest. Done ONCE per run."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s" % (_WD, _WD)], capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True,
                   timeout=60, check=True)
    for src_path, dst in ((MAPS_S, _WD + "/maps_prover.S"), (MAPS_LD, _WD + "/maps_prover.ld")):
        with open(src_path, "rb") as f:
            subprocess.run(_SSH + ["cat > %s" % dst], input=f.read(), capture_output=True,
                           timeout=30, check=True)
    _SEEDED["done"] = True


def _build_and_boot(fault=""):
    """Build the maps body (MAPS_PROVER) in the guest with an optional PLANT, boot it in a NESTED qemu
    (ONE at a time — killed before and after), return the raw serial. Cached per fault."""
    if fault in _BOOTED:
        return _BOOTED[fault]
    _seed_guest()
    out = _WD + "/out" + (("-" + fault) if fault else "")
    env = ("MAPS_PROVER_SRC=%s/maps_prover.S MAPS_PROVER_LD=%s/maps_prover.ld" % (_WD, _WD))
    script = (
        "set -e\n"
        "%s bash %s/body/build.sh %s/body %s %s >/tmp/mapsbuild.log 2>&1 || "
        "{ echo BUILD-FAILED; tail -8 /tmp/mapsbuild.log; exit 0; }\n"
        "pkill -9 -f 'qemu-system.*body.img' 2>/dev/null || true\n"
        "sleep 1\n"
        "timeout --signal=KILL 30 %s -kernel %s/body.img </dev/null 2>/dev/null || true\n"
        "pkill -9 -f 'qemu-system.*body.img' 2>/dev/null || true\n"
        % (env, _WD, _WD, out, fault, _QEMU, out))
    boot = subprocess.run(_SSH + ["bash -s"], input=script.encode(), capture_output=True, timeout=120)
    text = boot.stdout.decode(errors="replace").replace("\r", "")
    assert "BUILD-FAILED" not in text, "guest build failed (%s):\n%s" % (fault, text)
    _BOOTED[fault] = text
    return text


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: pinned gov-lab guest not reachable (6.8.0-134-generic on ssh :2222)")
class TestPerEnclosureMapsHappy(unittest.TestCase):
    """A1-A4 happy path — two resident enclosures, no aliasing, the map swapped, the fault per map."""

    @classmethod
    def setUpClass(cls):
        cls.serial = _build_and_boot("")

    def test_A1_two_residents_no_aliasing(self):
        # each enclosure's 0x400000 is a DISTINCT physical frame; each reads back its OWN sentinel.
        m = re.search(r"MAPS-FRAME-A: 0x([0-9a-f]+) MAPS-FRAME-B: 0x([0-9a-f]+)", self.serial)
        self.assertIsNotNone(m, self.serial)
        fa, fb = int(m.group(1), 16), int(m.group(2), 16)
        self.assertNotEqual(fa, 0)
        self.assertNotEqual(fb, 0)
        self.assertNotEqual(fa, fb, "the two enclosures' 0x400000 must map DISTINCT frames")
        self.assertIn("MAPS-A-READBACK: 0xa11ce5a1 MAPS-B-READBACK: 0xb0b0b0b0", self.serial)
        self.assertIn("CHECK MAPS-NO-ALIAS: PASS", self.serial)

    def test_A2_handoff_swaps_state_intact(self):
        # A's 0x400000 is intact after B ran under its own map.
        self.assertIn("MAPS-A-AFTER-B: 0xa11ce5a1", self.serial)
        self.assertIn("CHECK MAPS-STATE-INTACT: PASS", self.serial)

    def test_A3_fault_per_map(self):
        # a ring-3 fault under B's own map is a #PF (vec 0xe), recovered to A's map; A untouched.
        m = re.search(r"MAPS-FAULT: vec=0x0*e .* active-read-after=0x([0-9a-f]+)", self.serial)
        self.assertIsNotNone(m, self.serial)
        self.assertEqual(int(m.group(1), 16), 0xa11ce5a1)
        self.assertIn("CHECK MAPS-FAULT-PER-MAP: PASS", self.serial)

    def test_A4_kernel_half_shared_nothing_else_moves(self):
        self.assertIn("CHECK MAPS-KERNEL-HALF: PASS", self.serial)
        self.assertIn("ROWS-COUNT: 0000000c", self.serial)          # ACT_KINDS stays twelve
        self.assertIn("ENCLOSURE-ACTS: PASS", self.serial)          # P3b-4a still green (same boot)
        self.assertIn("SERVE-ACTS: PASS", self.serial)              # P3b-4b still green (same boot)
        self.assertIn("MAPS: PASS", self.serial)
        self.assertIn("MAPS-ACTS: PASS", self.serial)

    def test_precision_preemption_off_measured(self):
        # archi :4542 — the timer cannot preempt while a worker's map is active (the 6b shape).
        self.assertIn("MAPS-PREEMPT: g_sched_on=0x00000000 preempts=0x00000000", self.serial)
        self.assertIn("CHECK MAPS-PREEMPT-OFF: PASS", self.serial)


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: pinned gov-lab guest not reachable")
class TestPerEnclosureMapsPlants(unittest.TestCase):
    """Each plant reds ITS check by a REAL mechanism — a check that cannot fail is not a check (L19)."""

    def test_A1_plant_shared_map_aliases(self):
        s = _build_and_boot("PLANT_MAPS_SHARED")
        m = re.search(r"MAPS-FRAME-A: 0x([0-9a-f]+) MAPS-FRAME-B: 0x([0-9a-f]+)", s)
        self.assertIsNotNone(m, s)
        self.assertEqual(int(m.group(1), 16), int(m.group(2), 16), "shared map -> same frame at 0x400000")
        self.assertIn("CHECK MAPS-NO-ALIAS: FAIL", s)
        self.assertIn("MAPS: FAIL", s)
        self.assertNotIn("MAPS-ACTS: PASS", s)

    def test_A2_plant_no_swap_corrupts_first(self):
        s = _build_and_boot("PLANT_MAPS_NO_SWAP")
        # maps distinct, but the un-swapped hand-off let B corrupt A's frame at 0x400000.
        self.assertIn("MAPS-A-AFTER-B: 0xb0b0b0b0", s)
        self.assertIn("CHECK MAPS-STATE-INTACT: FAIL", s)
        self.assertIn("MAPS: FAIL", s)

    def test_A3_plant_no_swapback_wrong_map(self):
        s = _build_and_boot("PLANT_MAPS_FAULT_NOSWAPBACK")
        # A intact + no aliasing (the write phase swapped correctly); ONLY the post-fault map read is wrong.
        self.assertIn("CHECK MAPS-NO-ALIAS: PASS", s)
        self.assertIn("CHECK MAPS-STATE-INTACT: PASS", s)
        self.assertIn("active-read-after=0xb0b0b0b0", s)            # the wrong map's sentinel
        self.assertIn("CHECK MAPS-FAULT-PER-MAP: FAIL", s)
        self.assertIn("MAPS: FAIL", s)

    def test_A4_plant_missing_kernel_half_faults(self):
        s = _build_and_boot("PLANT_MAPS_NO_KERNEL_HALF")
        # a map without PML4[256] -> the body faults on its own direct map after the swap (a real #PF).
        self.assertRegex(s, r"EXC: vector=0x0*e")
        self.assertNotIn("MAPS: PASS", s)
        self.assertNotIn("MAPS-ACTS: PASS", s)


class TestAttestedUnchanged(unittest.TestCase):
    """A4 — ATTESTED stays 88 and the guard surface still equals it (no new src/body member)."""

    def test_attested_count_and_guard_surface(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88)
        gs = set(attestation.law_guard_surface(SRC))
        self.assertEqual(gs, set(attestation.ATTESTED_MEMBERS),
                         "no new src/body member — the maps prover is a tests/ fixture")


if __name__ == "__main__":
    unittest.main()
