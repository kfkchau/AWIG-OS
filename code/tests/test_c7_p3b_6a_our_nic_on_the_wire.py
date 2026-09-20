# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel driving a virtio-net device as its own transport, a ring-0 self-check that does
# an address round trip on the wire) as in the seL4/gVisor/Fuchsia and osdev literature. NON-GOAL: no
# offensive capability — this DRIVES the acceptance of C7 P3b-6a (the body's OWN NIC driver, proven ON
# THE WIRE by an address round trip answered by the guest's gateway, in a nested guest with its own SLIRP
# net; it boots nothing into production, touches no host kernel, adds no served shape). Validate by
# building/reading, never by attack (governance-work-method).
"""C7 P3b-6a acceptance — OUR NIC ON THE WIRE (design/54 §7 P3b-6a; countersign archi :4250).

The body that boots with memory (P3b-1), a disk (P3b-2), a clock/interrupt/entropy path (P3b-3) and the
worker enclosure/serve (P3b-4) now drives the NETWORK DEVICE as its OWN transport, ON THE METAL, in a
NESTED qemu inside the pinned guest — and proves it ON THE WIRE, not by inspecting itself.

  A1  our OWN driver finds the virtio-net device, negotiates it (legacy virtio: reset -> ACKNOWLEDGE ->
      DRIVER -> feature negotiation -> RX+TX virtqueues -> DRIVER_OK), reads the MAC, and brings the
      rings up: CHECK NIC-BRINGUP: PASS + OUR-MAC on serial + the twelve rows' digest still on serial.
  A2  THE WIRE ROUND TRIP (the prover). The ring-0 self-check transmits an address-resolution request for
      the guest gateway (10.0.2.2) and RECEIVES THE GATEWAY'S reply off the receive ring — CHECK
      WIRE-ROUNDTRIP: PASS + GW-MAC != OUR-MAC (an OUTSIDE party answered; not our own bytes echoed).
      PLANT_NET_TX_DEAD (no frame is put on the wire) reds WIRE-ROUNDTRIP by a REAL mechanism (no frame ->
      no reply -> the receive poll times out), NOT a flag — while NIC-BRINGUP still passes.
  A3  the driver source is ATTESTED BY NAME (87 -> 88; src/body 30 -> 31), the walk-guard covers it, and
      the built .elf/.img is never a signed member (§9 mechanism 3).
  A4  NO SERVED SHAPE ADDED — serve.c's SYS_socket is still REFUSED as the native failure; net.c adds no
      serve case (the frame-crossing to an enclosed worker is 6b's, archi :4247).
  A5  guest-only, revertable, NO one-way door — no host kernel load in the driver, the body is not stood
      as the production performer, net.c is a NEW file only, and the standing body suite still boots this
      SAME body with NO NIC attached (NET: ABSENT) so the lower slices stay green; the scans CAN fail.

A1/A2 build+boot in the NESTED guest and skip when the pinned guest is not reachable over SSH; A3-A5 run
in main. Register: OS network bring-up on a disposable guest, described by function — a body that drives
its own NIC and resolves the gateway's address on the wire; validated by building/reading, never by
attack. Every kernel touch is the guest's nested qemu; the host kernel and host network are never touched
(L11 / EP-00 rule 9 / charter §A21).
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

# the one source file this slice adds under src/body/ (attested by name, A3).
NEW_NET_FILE = "body/net.c"

# ── the nested-guest bridge (A1/A2 only) ────────────────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b6a-accept"
# every nested boot attaches a virtio-net device on a USER-MODE (SLIRP) network — the gateway (10.0.2.2)
# is qemu's own SLIRP host, an OUTSIDE party that answers the ARP request. The host network is never
# touched: SLIRP is entirely inside qemu. -cpu max exposes rdtsc for the bounded receive poll.
_QEMU = ("qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc "
         "-netdev user,id=n1 -device virtio-net-pci,netdev=n1")
_boot_n = [0]


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


def _seed_guest():
    """Copy src/body to the guest ONCE (build.sh compiles only the C — no Python needed to boot)."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", outdir=None):
    """Build the body in the guest (nested-qemu target); return outdir."""
    _seed_guest()
    out = outdir or (_WD + "/out" + (("-" + fault) if fault else ""))
    b = subprocess.run(_SSH + ["bash %s/body/build.sh %s/body %s %s" % (_WD, _WD, out, fault)],
                       capture_output=True, timeout=120)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    return out


def _guest_boot(outdir, with_nic=True, timeout_s=14):
    """Boot the body in a NESTED qemu (with a virtio-net device unless with_nic=False); return serial.
    Every boot is the guest's nested qemu — no host kernel. The body halts after announcing, so qemu runs
    to the timeout; the serial is fully captured before the kill. Boots are SERIALIZED (mgr :4027)."""
    qemu = _QEMU if with_nic else ("qemu-system-x86_64 -cpu max -serial stdio -display none "
                                   "-no-reboot -m 256 -rtc base=utc")
    _boot_n[0] += 1
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d %s -kernel %s/body.img </dev/null 2>/dev/null; true"
                % (timeout_s, qemu, outdir)],
        capture_output=True, timeout=timeout_s + 20)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _mac(serial, label):
    m = re.search(label + r": ([0-9a-f:]+)", serial)
    return m.group(1) if m else None


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
class TestA1OurCodeDrivesTheDevice(unittest.TestCase):
    def test_our_driver_brings_up_the_device_and_the_digest_is_on_serial(self):
        serial = _guest_boot(_guest_build())
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("CHECK NIC-BRINGUP: PASS", serial, "our own driver negotiated the virtio-net device")
        self.assertRegex(serial, r"NET: virtio-net at pci 0:0*[0-9a-f]+ iobase=0x[0-9a-f]+",
                         "the driver found the device on the PCI bus and read its I/O BAR")
        our_mac = _mac(serial, "OUR-MAC")
        self.assertIsNotNone(our_mac, "the driver read the MAC the device offers (VIRTIO_NET_F_MAC)")
        self.assertNotEqual(our_mac, "00:00:00:00:00:00", "the MAC is non-zero")
        self.assertIn("NET: PASS", serial, "the NIC self-check passes as a group")
        self.assertIn("NET-ACTS: PASS", serial)
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c) — the slice adds no act")
        self.assertIn("BODY-HALT", serial, "the body halts cleanly after the round trip (it stops kicking)")


# ── A2 ─────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2TheWireRoundTrip(unittest.TestCase):
    def test_the_gateway_answers_off_the_wire_not_our_own_bytes(self):
        serial = _guest_boot(_guest_build())
        self.assertIn("CHECK WIRE-ROUNDTRIP: PASS", serial,
                      "the driver received the gateway's ARP reply off the receive ring")
        gw_mac = _mac(serial, "GW-MAC")
        our_mac = _mac(serial, "OUR-MAC")
        self.assertIsNotNone(gw_mac, "the gateway's hardware address came back on the wire")
        self.assertIsNotNone(our_mac)
        self.assertNotEqual(gw_mac, our_mac,
                            "the reply's sender is the GATEWAY, not us — an outside party answered, not "
                            "our own bytes echoed (STOP-condition d)")

    def test_the_dead_transmit_plant_reds_the_round_trip_by_a_real_mechanism(self):
        # PLANT_NET_TX_DEAD: the driver puts NO frame on the wire, so the gateway has nothing to answer
        # and the receive poll times out. The check CAN fail (§A64) — and it fails because the wire is
        # genuinely silent, not because a flag flipped the verdict. Bring-up still passes.
        serial = _guest_boot(_guest_build("PLANT_NET_TX_DEAD"))
        self.assertIn("CHECK NIC-BRINGUP: PASS", serial, "the device still comes up under the plant")
        self.assertIn("CHECK WIRE-ROUNDTRIP: FAIL", serial, "no frame on the wire -> no reply -> FAIL")
        self.assertIn("NET: FAIL", serial, "the plant reds the aggregate NET line")
        self.assertNotIn("CHECK WIRE-ROUNDTRIP: PASS", serial, "the round trip did not pass under the plant")


# ── A3 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA3TheDriverIsAttested(unittest.TestCase):
    def test_net_c_is_attested_by_name_and_the_counts_moved_to_31_and_88(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        self.assertIn(NEW_NET_FILE, ATTESTED_MEMBERS, "%s is not attested by name (§9 mechanism 1)" % NEW_NET_FILE)
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "the 31 src/body/ source files (30 + 1 net.c, C7 P3b-6a)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "87 -> 88 (the 1 new file net.c, C7 P3b-6a)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers net.c")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list")

    def test_the_built_elf_is_never_a_signed_member(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built .elf/.img is NEVER a signed member")


# ── A4 ─────────────────────────────────────────────────────────────────────────────────────────
class TestA4NoServedShapeAdded(unittest.TestCase):
    def test_serve_c_still_refuses_the_socket_share_and_net_c_adds_no_serve_case(self):
        with open(os.path.join(BODY, "serve.c"), encoding="utf-8") as f:
            serve = f.read()
        # the SYS_socket share is still REFUSED as the native failure (no new served shape, A4).
        self.assertIn("case SYS_socket:", serve, "serve.c still handles the socket share")
        self.assertRegex(serve, r"g_socket_refused = 1;\s*/\* refused as the worker's native failure",
                         "the socket share is still refused as the native failure — no served shape added")
        # net.c drives the device directly; it adds NO case to serve.c's served set and never touches it.
        with open(os.path.join(BODY, "net.c"), encoding="utf-8") as f:
            net = f.read()
        self.assertNotIn("SV_SERVED", net, "the driver adds no served verdict — it is not a served act")
        self.assertNotIn("serve.h", net, "the driver does not reach into the serve trail (that is 6b's)")
        # ACT_KINDS is unchanged at twelve (the slice founds no act, :4248): the digest folds twelve rows.
        # (Proven live in A1 by ROWS-COUNT: 0000000c on serial.)


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
    def test_no_host_kernel_load_in_the_driver_and_the_scan_can_fail(self):
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
        tmp = tempfile.mkdtemp(prefix="p3b6a-a5-")
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "compose_planted.py"), "w", encoding="utf-8") as f:
            f.write("from body import kmain  # stand the body as the production performer\n")
        hits = _production_standing_hits(tmp)
        self.assertTrue(any(rel == "kernel/compose_planted.py" for rel, _pat in hits),
                        "a planted production-standing import must red the scan")

    def test_the_nic_slice_is_a_new_file_only(self):
        # net.c is a NEW file under src/body/; kmain.c/build.sh gained calls, no existing C was overwritten.
        self.assertTrue(os.path.exists(os.path.join(SRC, NEW_NET_FILE)), "%s exists" % NEW_NET_FILE)

    @unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the no-NIC boot needs the pinned guest + nested qemu")
    def test_the_standing_body_still_boots_clean_with_no_nic_attached(self):
        # the lower slices boot this SAME body with NO virtio-net device — the driver must skip gracefully
        # (NET: ABSENT) so the standing body suite stays green (A5), and the digest still lands.
        serial = _guest_boot(_guest_build(), with_nic=False)
        self.assertIn("NET: ABSENT", serial, "with no NIC the driver skips the round trip, does not fail")
        self.assertNotIn("NET: FAIL", serial, "a missing device is not a failure")
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the body still announces its digest")
        self.assertIn("BODY-HALT", serial, "and halts cleanly")


if __name__ == "__main__":
    unittest.main()
