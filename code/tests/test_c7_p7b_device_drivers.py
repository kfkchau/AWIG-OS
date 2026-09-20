# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel body records, at bring-up, one discovery row per device it performs — its own
# block, network and clock drivers — each row riding the existing record-pen act, and the read-only
# device window is re-sourced from those rows) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no
# offensive capability — this DRIVES the acceptance of C7 P7b (the body records what it already discovers
# and surfaces it to a read-only window; the borrowed-driver-enclosed half is cited from the closed lwIP
# worker, not rebuilt). Validate by building/reading, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7 P7b acceptance — THE DEVICE DRIVERS (design/54 §7 P7b; §3 B7 second half + B10; §5 L14/L19/L21).

The body that boots with memory (P3b-1), a disk (P3b-2), a clock/interrupt/entropy path (P3b-3), the
worker enclosure/serve (P3b-4) and its OWN NIC on the wire (P3b-6a) now RECORDS ONE DEVICE-DISCOVERY ROW
PER DEVICE it performs over the settled three-device list (block, network, clock; Q4 :3919) at bring-up,
each an append riding the EXISTING record-pen act, in a NESTED qemu inside the pinned guest.

  A1  a fresh body image (disk + NIC) records exactly one discovery row per device, each naming the
      identity the body EXPORTS at bring-up (block = ata_present's verdict; network = the wire self-check's
      class + the MAC net_nic_bringup exports; clock = the RTC's presence + epoch), each read back from
      the record equal (L19 — a real probe, never a fabricated event) and each tracing to the real probe
      result printed independently on serial. PLANT_DISCOVERY_PHANTOM: a boot with no NIC records a
      network row claiming PRESENT (class=PASS) when the probe found it ABSENT — the trace check reds.
  A2  the discovery row rides record-pen (ROWS-COUNT 0x0c — no 13th act kind); ATTESTED stays 88 (the
      emitter is edit-in-place in an existing boot member — no new file); the device DRIVERS ata.c,
      clock.c, net.c are BYTE-UNCHANGED (a pinned sha256 per file; a driver edit moves it — caught).
  A3/A4/A5 are the OBSERVE-lane half (the device window re-sourced) + the cited lwIP half — they live in
      tests/test_c7_p9_observe_windows_census.py and tests/test_c7_p3b_6b_borrowed_tcp_enclosed.py.

A1 builds+boots in the NESTED guest and skips when the pinned guest is not reachable over SSH; A2's
ATTESTED/driver-sha checks run in main. Register: an OS recording the devices it discovers on a
disposable guest, described by function; validated by building/reading, never by attack. Every kernel
touch is the guest's nested qemu; the host kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
"""

import hashlib
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

# the three device DRIVER files this plan keeps BYTE-UNCHANGED (A2). The sha256 is the baseline captured
# at the P7b build; a driver edit moves it and the pin reds (the plant that can fail — a location that
# guards the "drivers untouched" property, re-pointed only by a deliberate driver change).
DRIVER_SHA = {
    "ata.c":   "99fbe7cc74fb33abcd7c35448a442a75c7b826a093a0d131382de86aeb8cf28c",
    "clock.c": "53aea236fb3d4ca91b8e5f6270920b23eed8bc4162d7e303474bd1e2b7845e3d",
    "net.c":   "768865bda4a330d23ec2986b89243b249412b3a695413d5761fc961ad9640d51",
}

# ── the nested-guest bridge (A1 only) ─────────────────────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p7b-device-accept"                       # per-unit scratch (isolated name, host + guest)
# a virtio-net device on a USER-MODE (SLIRP) network (the gateway 10.0.2.2 is qemu's SLIRP host, an
# OUTSIDE party) AND an IDE disk carrying a fresh BODYFS (the record the discovery rows land in). The
# host network/kernel is never touched: SLIRP + the nested qemu are entirely inside the guest.
_QEMU_NET = ("-netdev user,id=n1 -device virtio-net-pci,netdev=n1")


def _guest_reachable():
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
    """Copy src/body + src/bridge + src/founding to the guest ONCE (mkdisk.py needs host_seam + pack)."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", outdir=None):
    _seed_guest()
    out = outdir or (_WD + "/out" + (("-" + fault) if fault else ""))
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (_WD, _WD, out, fault)],
                       capture_output=True, timeout=120)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    return out


def _guest_mkdisk(img):
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img, with_nic=True, timeout_s=30):
    """Boot the body in a NESTED qemu with `img` as an IDE disk (and a virtio-net device unless
    with_nic=False); return the serial text. Every boot is the guest's nested qemu — no host kernel."""
    qemu = ("qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc "
            + (_QEMU_NET + " " if with_nic else "")
            + "-drive file=%s,format=raw,if=ide,index=0" % img)
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d %s -kernel %s/body.img </dev/null 2>/dev/null; true"
                % (timeout_s, qemu, outdir)],
        capture_output=True, timeout=timeout_s + 20)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def tearDownModule():
    """Leave the guest as found: no nested-qemu boot survives this module (serialized guest)."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── serial parsing ────────────────────────────────────────────────────────────────────────────────
def _device_rows(serial):
    """{device: the row body as READ BACK from the record}."""
    out = {}
    for m in re.finditer(r"DEVICE-DISCOVERY: (device-discovery device=(\w+)[^\n\[]*)", serial):
        out[m.group(2)] = m.group(1).strip()
    return out


def _net_class(serial):
    if "NET-ACTS: PASS" in serial:
        return "PASS"
    if "NET-ACTS: ABSENT" in serial:
        return "ABSENT"
    if "NET-ACTS: FAIL" in serial:
        return "FAIL"
    return None


def _row_net_class(row):
    m = re.search(r"class=(PASS|ABSENT|FAIL)", row or "")
    return m.group(1) if m else None


def _mac(serial, label):
    m = re.search(label + r":?\s*([0-9a-f:]{17})", serial)
    return m.group(1) if m else None


def _traces_to_probes(serial):
    """THE TRACE CHECK (able to fail). Every discovery row must match the probe result the body printed
    INDEPENDENTLY on serial: the block row's present bit == (DISK: OK); the network row's class == the
    NET-ACTS class; the clock row's present bit == (CLOCK-ACTS: PASS). A phantom row disagrees with its
    probe and this returns False; a faithful set of rows returns True (so the check discriminates)."""
    rows = _device_rows(serial)
    if set(rows) != {"block", "network", "clock"}:
        return False
    disk_ok = "DISK: OK" in serial
    if ("present=0x00000001" in rows["block"]) != disk_ok:
        return False
    if _row_net_class(rows["network"]) != _net_class(serial):
        return False
    clk_ok = "CLOCK-ACTS: PASS" in serial
    if ("present=0x00000001" in rows["clock"]) != clk_ok:
        return False
    return True


# ── A1 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1DiscoveryRowPerDevice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = _guest_build()
        img = _guest_mkdisk(_WD + "/disk-p7b-green.img")
        cls.serial = _guest_boot(out, img, with_nic=True)

    def test_the_body_records_exactly_one_discovery_row_per_device_over_the_three_device_list(self):
        s = self.serial
        self.assertIn("MULTIBOOT: OK", s, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("DISK: OK", s, "the record disk is mounted (the discovery rows land in the record)")
        rows = _device_rows(s)
        self.assertEqual(set(rows), {"block", "network", "clock"},
                         "exactly one discovery row per device over the settled three-device list:\n" + s[-1500:])
        self.assertIn("DEVICE-DISCOVERY-COUNT: 0x00000003", s, "three devices probed, three rows")
        self.assertIn("DEVICE-DISCOVERY-ACTS: PASS", s,
                      "each row appended + read back from the record equal (it rode the disk, L19)")
        # each row was READ BACK from the record equal (the serial IS the record read-back).
        self.assertNotIn("[readback=FAIL]", s, "every discovery row read back from the record equal")
        self.assertNotIn("[append-FAIL]", s)

    def test_each_row_names_the_identity_the_body_EXPORTS_and_traces_to_the_real_probe(self):
        s = self.serial
        rows = _device_rows(s)
        # block: the row's present bit == the boot's block verdict (DISK: OK).
        self.assertIn("present=0x00000001", rows["block"], "the block row records ata_present's verdict (present)")
        # network: the row's class == the boot's NET-ACTS class; the MAC == the offered OUR-MAC.
        self.assertEqual(_net_class(s), "PASS", "the NIC is attached in the green boot")
        self.assertEqual(_row_net_class(rows["network"]), "PASS",
                         "the network row records the wire self-check's exported class")
        our_mac = _mac(s, "OUR-MAC")
        row_mac = _mac(rows["network"], "mac=")
        self.assertIsNotNone(our_mac, "the wire self-check printed the offered MAC")
        self.assertEqual(row_mac, our_mac,
                         "the network row records the MAC net_nic_bringup EXPORTS, not a re-probed PCI id")
        # clock: present + a non-zero epoch (a plausible 2020+ RTC yields a large epoch).
        self.assertIn("present=0x00000001", rows["clock"], "the clock row records rtc_read's presence")
        me = re.search(r"device=clock present=0x0*1 epoch=0x([0-9a-f]+)", rows["clock"])
        self.assertIsNotNone(me, "the clock row records clock_epoch_seconds' epoch:\n" + rows["clock"])
        self.assertGreater(int(me.group(1), 16), 0, "a present clock records a non-zero epoch")
        # the WHOLE set traces to the real probes (the discriminating check).
        self.assertTrue(_traces_to_probes(s), "every discovery row traces to its real probe result")

    def test_the_row_never_names_the_file_static_pci_id_slot_or_bar(self):
        # the archi :4605 precision: the network row records the EXPORTED identity (class + MAC), NEVER
        # the file-static PCI vendor/device id / slot / BAR (re-probing them would edit a driver or add a
        # parallel probe). The row's serial names no vendor/device/slot/BAR/iobase token.
        row = _device_rows(self.serial).get("network", "")
        for tok in ("vendor", "device=0x", "slot", "bar", "iobase", "pci"):
            self.assertNotIn(tok, row.lower().replace("device=network", ""),
                             "the network row must not name the file-static PCI %r (precision :4605)" % tok)

    def test_the_slice_founds_no_act_the_digest_is_still_twelve_rows(self):
        self.assertIn("ROWS-COUNT: 0000000c", self.serial, "the discovery row rides record-pen — ACT_KINDS 12")
        self.assertIn("BODY-HALT", self.serial, "the body halts cleanly after recording the rows")


# ── A1 PLANT ─────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the phantom plant needs the pinned guest + nested qemu")
class TestA1PhantomPresentRowPlant(unittest.TestCase):
    def test_the_phantom_present_row_reds_the_trace_check_by_a_real_divergence(self):
        # PLANT_DISCOVERY_PHANTOM + a boot with NO NIC: the probe finds the network ABSENT (NET-ACTS:
        # ABSENT), but the emitter records a network row claiming PRESENT (class=PASS). The recorded
        # identity DISAGREES with the probe, so the trace check reds — a REAL divergence, not a flag.
        out = _guest_build("PLANT_DISCOVERY_PHANTOM")
        img = _guest_mkdisk(_WD + "/disk-p7b-phantom.img")
        serial = _guest_boot(out, img, with_nic=False)
        self.assertIn("NET-ACTS: ABSENT", serial, "no NIC is attached, so the probe finds the network absent")
        rows = _device_rows(serial)
        self.assertEqual(_row_net_class(rows.get("network", "")), "PASS",
                         "the plant records a PHANTOM present (class=PASS) network row:\n" + serial[-1500:])
        # the discriminating trace check REDS on the phantom (the row disagrees with the probe).
        self.assertFalse(_traces_to_probes(serial),
                         "the phantom network row must fail the trace check (recorded PASS vs probed ABSENT)")

    def test_the_same_trace_check_passes_a_faithful_boot(self):
        # the check DISCRIMINATES (not a check that always fails): the green boot's rows all trace.
        out = _guest_build()
        img = _guest_mkdisk(_WD + "/disk-p7b-discriminate.img")
        serial = _guest_boot(out, img, with_nic=True)
        self.assertTrue(_traces_to_probes(serial), "a faithful boot passes the same trace check")


# ── A2 (off-body) ───────────────────────────────────────────────────────────────────────────────
class TestA2RidesRecordPenAttestedAndDriversUnchanged(unittest.TestCase):
    def test_act_kinds_stays_twelve_the_row_rides_record_pen(self):
        from bridge import host_seam as hs
        self.assertEqual(len(hs.ACT_KINDS), 12, "the discovery row rides record-pen — no 13th act kind")
        self.assertIn("record-pen", hs.ACT_KINDS, "record-pen is one of the twelve acts the row rides")

    def test_attested_members_count_unchanged_no_new_src_body_file(self):
        # the emitter is edit-in-place in diskcheck.c (an existing boot member) — no new src/body file,
        # so the attested-members count does not move. 88 is the count DRIVEN this turn; the pin catches
        # a NEW engine module sneaking into the diff.
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88, "no new src/body member (ATTESTED stays 88)")

    def test_the_device_drivers_are_byte_unchanged(self):
        # A2 + THE PLANT (can fail): the three device driver files stay BYTE-UNCHANGED — a pinned sha256
        # per file. Only a boot-time append was added (in diskcheck.c/kmain.c), never in the drivers; a
        # driver I/O-path edit moves the sha and this reds.
        for name, want in DRIVER_SHA.items():
            with open(os.path.join(BODY, name), "rb") as f:
                got = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(got, want, "%s must stay byte-unchanged (the drivers do not move, P7b)" % name)

    def test_the_emitter_lives_in_the_boot_member_not_in_a_driver(self):
        # the emitter is in the boot member diskcheck.c (beside check_record_pen), never in a driver.
        with open(os.path.join(BODY, "diskcheck.c"), encoding="utf-8") as f:
            self.assertIn("disk_record_device_discovery", f.read(),
                          "the emitter lives in the boot member diskcheck.c")
        for name in ("ata.c", "clock.c", "net.c"):
            with open(os.path.join(BODY, name), encoding="utf-8") as f:
                self.assertNotIn("device-discovery", f.read(),
                                 "no device-discovery emitter code in the driver %s" % name)


if __name__ == "__main__":
    unittest.main()
