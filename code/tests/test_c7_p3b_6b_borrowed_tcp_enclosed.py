# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a borrowed TCP/IP stack — lwIP 2.2.0, the static NO_SYS build from the guest archive's SOURCE — run
# UNMODIFIED as a SECOND enclosed user-space worker on our own kernel body, its own per-enclosure served
# set being its whole-process measured set, the frames crossing to our own NIC) as in the seL4/gVisor/
# Fuchsia literature. NON-GOAL: no offensive capability — this DRIVES the acceptance of C7 P3b-6b (a
# borrowed stack enclosed, opening ONE guest-local connection through our own device over nested SLIRP).
# Validate by building/reading, never by attack (governance-work-method).
"""C7 P3b-6b acceptance — THE BORROWED TCP ENCLOSED (design/54 §7 P3b-6b; countersign archi :4302).

The body that hosts the interpreter (P3b-4c) and drives its own NIC on the wire (P3b-6a) now hosts a
SECOND enclosed worker: lwIP 2.2.0 (the static NO_SYS build from the guest archive's SOURCE package,
UNMODIFIED), whose OWN per-enclosure served set is its whole-process measured set (the twenty + clock,
declared as DATA — never the eight), plus three body-native frame shapes. The stack's OWN example
(lwiperf's client) opens ONE guest-local connection OUTBOUND through 6a's NIC over nested SLIRP and
completes a real exchange; every frame is a trail row; no new act kind.

  A1  the sealed static lwIP worker runs UNMODIFIED, enclosed and digest-checked (FLOOR-LOAD: OK +
      the recorded seal). PLANT_NETW_IMAGE_TAMPER -> FLOOR-LOAD: REFUSED (a byte change refuses the load).
  A2  the per-enclosure served set is the whole-process TWENTY (+clock) as data, never the eight; a shape
      beyond it is refused BY NAME; the interpreter's fifty untouched; the cross-refusal each way (L18).
      PLANT_LWIP_BEYOND_SERVED / PLANT_ENCL_CROSS red the served-set / per-enclosure checks.
  A3  the stack's OWN example opens ONE connection through our NIC and completes a real exchange — a plain
      listener in the OUTER guest (reached over nested SLIRP at 10.0.2.2) receives real bytes.
      PLANT_NET_TX_DEAD -> no frame on the wire -> no connection (a real mechanism), CONNECTION reds.
  A4  every send/receive frame is a row: the rows appended == the frames that crossed.
      PLANT_FRAME_TRAIL_SKIP skips one frame's row -> FRAME-TRAIL reds.
  A5  the worker's heap reaches the measured 17,048 B high-water. PLANT_LWIP_HEAP_SMALL sizes it below ->
      the connection starves (a real OOM) -> SIZED reds.
  A6  the glue is configuration only; the sealed lwIP AND its libc are CONTENT, never in body.elf or an
      attested member (I3). A7  the members hold (88, unchanged), the interpreter still runs its fifty
      (a lower slice green), the standing body suite green; ACT_KINDS stays twelve.
  precision(a)  PLANT_LWIP_OVERREACH: the REAL worker issues a shape beyond the set (getpid); the body
      refuses it BY NAME (the native ENOSYS the worker reads back), and the run still passes.

A1-A5 build+boot in the NESTED guest and skip when the pinned guest is not reachable; A6/A7 run in main.
Register: an OS hosting a borrowed network stack on a disposable guest, described by function — validated
by building/reading, never by attack. Every kernel touch is the guest's nested qemu; the host kernel and
host network are never touched (L11 / EP-00 rule 9 / charter §A21).
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

# the config-only fixtures (content, NEVER attested members) staged into the worker build.
GLUE_FIXTURE = os.path.join(HERE, "c7_p3b_6b_lwip_worker_glue.c")
LWIPOPTS_FIXTURE = os.path.join(HERE, "c7_p3b_6b_lwipopts.h")

# the pinned lwIP 2.2.0 SOURCE (mgr's dispatch pre-flight; apt-get source liblwip-dev, provenance-pinned).
DSC_SHA = "7c2a3c003375653b24e7f59ea2192a445b3d68c5a61c989ad8eca0a693752b97"
ORIG_SHA = "3a56474c26be8efe05c6b626a256c67bd9ee3739084e2844a4c989be031e7786"

# ── the nested-guest bridge ──────────────────────────────────────────────────────────────────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "-o", "UserKnownHostsFile=/dev/null",
        "<GUEST>"]
_WD = "/tmp/p3b6b-test"
# every nested boot attaches a virtio-net device on a USER-MODE (SLIRP) network — the gateway (10.0.2.2)
# routes the guest-local connection to a plain listener in the OUTER guest. The host network is untouched.
_QEMU = ("qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc "
         "-netdev user,id=n1 -device virtio-net-pci,netdev=n1")


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
_SEEDED = {"done": False, "lwip": None}
_BUILT = {}   # fault -> outdir (built once, reused)


def _seed_guest():
    """Copy src/body + the config-only fixtures to the guest, and fetch the pinned lwIP 2.2.0 SOURCE
    (apt-get source, provenance-checked). Done ONCE per run."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body"], capture_output=True, timeout=60)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s/port/arch" % (_WD, _WD)],
                   capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True,
                   timeout=60, check=True)
    # stage the config-only port: lwipopts.h + glue.c + a minimal arch/cc.h.
    for src_path, dst in ((GLUE_FIXTURE, _WD + "/port/glue.c"),
                          (LWIPOPTS_FIXTURE, _WD + "/port/lwipopts.h")):
        with open(src_path, "rb") as f:
            subprocess.run(_SSH + ["cat > %s" % dst], input=f.read(), capture_output=True,
                           timeout=30, check=True)
    cc_h = (b"#ifndef LWIP_ARCH_CC_H\n#define LWIP_ARCH_CC_H\n#include <stdio.h>\n#include <stdlib.h>\n"
            b"#include <endian.h>\n#define LWIP_PLATFORM_DIAG(x)   do { } while (0)\n"
            b"#define LWIP_PLATFORM_ASSERT(x) do { } while (0)\n#endif\n")
    subprocess.run(_SSH + ["cat > %s/port/arch/cc.h" % _WD], input=cc_h, capture_output=True,
                   timeout=30, check=True)
    # fetch the pinned lwIP 2.2.0 SOURCE from the guest's own archive (deb-src), provenance-checked.
    fetch = ("set -e; rm -rf %s/lwipsrc; mkdir -p %s/lwipsrc; cd %s/lwipsrc; "
             "apt-get source liblwip-dev >/tmp/aptsrc.log 2>&1; "
             "sha256sum *.dsc *.orig.tar.* ; ls -d lwip-*/" % (_WD, _WD, _WD))
    r = subprocess.run(_SSH + [fetch], capture_output=True, timeout=180)
    out = r.stdout.decode(errors="replace")
    assert DSC_SHA in out and ORIG_SHA in out, "lwIP source provenance mismatch:\n" + out + r.stderr.decode(errors="replace")
    m = re.search(r"(lwip-\S+)/", out)
    assert m, "lwIP source tree not found:\n" + out
    _SEEDED["lwip"] = "%s/lwipsrc/%s" % (_WD, m.group(1))
    _SEEDED["done"] = True


def _guest_build(fault=""):
    """Build the 6b body (NET_WORKER) in the guest; return outdir. Built once per fault, reused."""
    _seed_guest()
    if fault in _BUILT:
        return _BUILT[fault]
    out = _WD + "/out" + (("-" + fault) if fault else "")
    env = ("NET_WORKER=1 LWIP_SRC=%s GLUE_SRC=%s/port/glue.c LWIP_PORT=%s/port"
           % (_SEEDED["lwip"], _WD, _WD))
    b = subprocess.run(_SSH + ["%s bash %s/body/build.sh %s/body %s %s"
                               % (env, _WD, _WD, out, fault)], capture_output=True, timeout=180)
    if b.returncode != 0:
        raise AssertionError("guest build failed (%s): %s" % (fault, b.stderr.decode(errors="replace")))
    _BUILT[fault] = out
    return out


def _guest_boot(outdir, timeout_s=34, hold_open=18):
    """Boot the 6b body in a NESTED qemu with a virtio-net device AND a plain listener in the outer guest
    (the A3 peer): it reads a bounded amount then holds the socket OPEN (no read) so the client's own
    idle/session timer ends the exchange cleanly (the pcb stays valid — lwiperf's err path is avoided).
    Returns (serial, peer_bytes)."""
    # NB: plain concatenation only — NO %-formatting (the peer python contains literal % / repr text).
    peer = (
        "import socket,time,sys\n"
        "s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
        "s.bind(('0.0.0.0',5001));s.listen(1);s.settimeout(40)\n"
        "total=0\n"
        "try:\n"
        " c,a=s.accept();c.settimeout(8)\n"
        " while total<32768:\n"
        "  d=c.recv(4096)\n"
        "  if not d: break\n"
        "  total+=len(d)\n"
        " time.sleep(" + str(hold_open) + ")\n"
        " c.close()\n"
        "except Exception as e: sys.stderr.write('PEER-ERR '+repr(e)+chr(10))\n"
        "open('/tmp/peer6b.log','w').write('PEER-BYTES='+str(total)+chr(10))\n")
    script = (
        "pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; pkill -9 -f peer6b.py 2>/dev/null; "
        "rm -f /tmp/peer6b.log; cat > /tmp/peer6b.py <<'PYEOF'\n" + peer + "PYEOF\n"
        "nohup python3 /tmp/peer6b.py >/tmp/peer6b.out 2>&1 & sleep 1; "
        "timeout --signal=KILL " + str(timeout_s) + " " + _QEMU + " -kernel " + outdir
        + "/body.img </dev/null 2>/dev/null; "
        "sleep 1; echo '=====PEER====='; cat /tmp/peer6b.log 2>/dev/null; "
        "pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; pkill -9 -f peer6b.py 2>/dev/null; true")
    # feed the script (a heredoc that writes the peer, then boots) over STDIN via `bash -s`: a multi-line
    # heredoc is unreliable as a single ssh command argument (rc 255), reliable over stdin.
    boot = subprocess.run(_SSH + ["bash -s"], input=script.encode(), capture_output=True,
                          timeout=timeout_s + 30)
    text = boot.stdout.decode(errors="replace").replace("\r", "")
    serial, _, peerpart = text.partition("=====PEER=====")
    m = re.search(r"PEER-BYTES=(\d+)", peerpart)
    return serial, (int(m.group(1)) if m else 0)


def _body_source_names():
    return sorted(n for n in os.listdir(BODY)
                  if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; "
                               "pkill -9 -f peer6b.py 2>/dev/null; true"], capture_output=True, timeout=20)


# ── the happy-path boot, cached (A1-A5 all read one serial) ───────────────────────────────────────
_HAPPY = {}


def _happy():
    if "serial" not in _HAPPY:
        serial, peer = _guest_boot(_guest_build())
        _HAPPY["serial"], _HAPPY["peer"] = serial, peer
    return _HAPPY["serial"], _HAPPY["peer"]


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: 6b A1-A5 need the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1SealedUnmodifiedEnclosed(unittest.TestCase):
    def test_the_sealed_lwip_worker_runs_enclosed_and_digest_checked(self):
        serial, _ = _happy()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("FLOOR-LOAD: OK (digest matches the seal)", serial, "the sealed worker's digest matched")
        self.assertRegex(serial, r"FLOOR-IMG-SHA256: [0-9a-f]{64}", "the sealed worker's digest is recorded")
        self.assertIn("CHECK NETW-SEALED: PASS", serial, "the sealed worker ran unprivileged and enclosed")
        self.assertIn("NET-WORKER: PASS", serial)
        self.assertIn("ROWS-COUNT: 0000000c", serial, "ACT_KINDS stays twelve — the slice adds no act")
        self.assertIn("BODY-HALT", serial, "the body halts cleanly")

    def test_a_tampered_seal_is_refused_at_load(self):
        serial, _ = _guest_boot(_guest_build("PLANT_NETW_IMAGE_TAMPER"), timeout_s=10)
        self.assertIn("FLOOR-LOAD: REFUSED", serial, "a byte change refuses the load (the seal check)")
        self.assertIn("NET-WORKER: FAIL", serial, "the borrowed worker never starts under the tamper")
        self.assertNotIn("NET-WORKER: PASS", serial)


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: 6b A2 needs the pinned guest + nested qemu")
class TestA2PerEnclosureServedSet(unittest.TestCase):
    def test_the_served_set_is_the_whole_process_twenty_never_the_eight(self):
        serial, _ = _happy()
        self.assertIn("CHECK NETW-SERVED-SET: PASS", serial,
                      "the served set is the whole-process twenty (+clock) as data, never the eight; "
                      "a shape beyond it refused by name; the worker stayed in-set")
        self.assertIn("NET-WORKER-BEYOND-SERVED: 0x00000000", serial, "no beyond-set shape was served")

    def test_the_per_enclosure_cross_refusal_holds_each_way(self):
        serial, _ = _happy()
        self.assertIn("CHECK NETW-PER-ENCLOSURE: PASS", serial,
                      "a frame shape refused to the interpreter's enclosure; an interpreter-only shape "
                      "refused to the lwIP one; the interpreter's own shapes still served (L18)")

    def test_a_beyond_set_shape_served_reds_the_served_set_check(self):
        serial, _ = _guest_boot(_guest_build("PLANT_LWIP_BEYOND_SERVED"))
        self.assertIn("CHECK NETW-SERVED-SET: FAIL", serial, "a shape beyond the twenty served -> reds")
        self.assertIn("NET-WORKER-BEYOND-SERVED: 0x00000001", serial, "the beyond-set shape was served")
        self.assertIn("NET-WORKER: FAIL", serial)

    def test_the_gate_ignoring_the_enclosure_reds_the_cross_check(self):
        serial, _ = _guest_boot(_guest_build("PLANT_ENCL_CROSS"))
        self.assertIn("CHECK NETW-PER-ENCLOSURE: FAIL", serial,
                      "the gate ignoring the enclosure (a frame shape answered for the interpreter) -> reds")
        self.assertIn("NET-WORKER: FAIL", serial)

    def test_the_real_worker_beyond_set_request_is_refused_by_name(self):
        # precision (a): a REAL request beyond the set (getpid) from the real worker -> the native ENOSYS
        # (0xffffffffffffffda == 18446744073709551578), and the run still passes (the gate refused it).
        serial, _ = _guest_boot(_guest_build("PLANT_LWIP_OVERREACH"))
        self.assertIn("WORKER-OVERREACH-ANS=18446744073709551578", serial,
                      "the body refused the real worker's beyond-set getpid BY NAME (the native ENOSYS)")
        self.assertIn("NET-WORKER-BEYOND-SERVED: 0x00000000", serial, "refused, not served")
        self.assertIn("NET-WORKER: PASS", serial, "the run passes — the gate refused the overreach")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: 6b A3 needs the pinned guest + nested qemu")
class TestA3TheStacksOwnExampleOpensTheConnection(unittest.TestCase):
    def test_the_borrowed_client_opens_one_connection_and_a_real_exchange_reaches_the_peer(self):
        serial, peer_bytes = _happy()
        self.assertIn("CHECK NETW-CONNECTION: PASS", serial, "the stack's own client opened one connection")
        m = re.search(r"NET-WORKER-FRAMES-SENT: 0x([0-9a-f]+) RECV: 0x([0-9a-f]+) ROWS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the frame accounting line is on serial")
        sent, recv = int(m.group(1), 16), int(m.group(2), 16)
        self.assertGreater(sent, 0, "frames were sent through our NIC")
        self.assertGreater(recv, 0, "frames were received off the wire (the peer answered)")
        self.assertGreater(peer_bytes, 0, "the plain listener in the OUTER guest received REAL bytes over SLIRP")

    def test_no_frame_on_the_wire_reds_the_connection_by_a_real_mechanism(self):
        serial, peer_bytes = _guest_boot(_guest_build("PLANT_NET_TX_DEAD"))
        self.assertIn("CHECK NETW-CONNECTION: FAIL", serial,
                      "no frame on the wire -> no reply -> no connection (a real mechanism, not a flag)")
        m = re.search(r"NET-WORKER-FRAMES-SENT: 0x[0-9a-f]+ RECV: 0x([0-9a-f]+) ROWS: 0x[0-9a-f]+", serial)
        self.assertIsNotNone(m, "the frame accounting line is on serial")
        self.assertEqual(int(m.group(1), 16), 0, "nothing came back off the wire (the transmit is dead)")
        self.assertEqual(peer_bytes, 0, "the peer received nothing (no frame ever left the NIC)")
        self.assertIn("NET-WORKER: FAIL", serial)


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: 6b A4 needs the pinned guest + nested qemu")
class TestA4EveryFrameATrailRow(unittest.TestCase):
    def test_the_rows_equal_the_frames_that_crossed(self):
        serial, _ = _happy()
        self.assertIn("CHECK NETW-FRAME-TRAIL: PASS", serial, "the rows appended == the frames that crossed")
        m = re.search(r"NET-WORKER-FRAMES-SENT: 0x([0-9a-f]+) RECV: 0x([0-9a-f]+) ROWS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the frame accounting line is on serial")
        sent, recv, rows = int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)
        self.assertEqual(rows, sent + recv, "every send and receive frame is exactly one row")

    def test_a_skipped_frame_row_reds_the_trail_check(self):
        serial, _ = _guest_boot(_guest_build("PLANT_FRAME_TRAIL_SKIP"))
        self.assertIn("CHECK NETW-FRAME-TRAIL: FAIL", serial, "one frame not recorded -> rows != frames")
        self.assertIn("NET-WORKER: FAIL", serial)


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: 6b A5 needs the pinned guest + nested qemu")
class TestA5SizedToThePreflight(unittest.TestCase):
    def test_the_heap_holds_the_measured_high_water(self):
        serial, _ = _happy()
        self.assertIn("CHECK NETW-SIZED: PASS", serial, "the worker's heap reached the 17,048 B high-water")
        peak = int(re.search(r"NET-WORKER-HEAP-PEAK: 0x([0-9a-f]+)", serial).group(1), 16)
        self.assertGreaterEqual(peak, 17048, "the heap held at least the measured high-water")

    def test_a_heap_below_the_high_water_starves_the_connection(self):
        serial, _ = _guest_boot(_guest_build("PLANT_LWIP_HEAP_SMALL"), timeout_s=20)
        self.assertIn("CHECK NETW-SIZED: FAIL", serial,
                      "the heap sized below the high-water -> the connection starves (a real OOM)")
        self.assertIn("NET-WORKER: FAIL", serial)


# ── A6 / A7 — structural, run in main (no guest) ──────────────────────────────────────────────────
class TestA6GlueIsConfigOnlyContentNotInBase(unittest.TestCase):
    def test_no_lwip_source_lives_under_src_body(self):
        # the borrowed stack is CONTENT (a sealed worker image), never hand-rolled into the signed base (I3).
        names = _body_source_names()
        for n in names:
            self.assertFalse(n.startswith("lwip") or n == "lwiperf.c",
                             "borrowed lwIP source must NOT live under src/body (%s)" % n)
        # the two frame functions + PBUF_RAM + sys_now are the worker's OWN glue (a test fixture, content),
        # never a src/body member; net.c only exposes the callable frame API (no serve verdict).
        with open(os.path.join(BODY, "net.c"), encoding="utf-8") as f:
            net = f.read()
        self.assertNotIn("SV_SERVED", net, "net.c adds no served verdict")
        self.assertNotIn('#include "serve.h"', net, "net.c does not reach into the serve trail")
        self.assertIn("int net_send_frame", net, "net.c exposes the callable send-frame API (6b, mechanical)")
        self.assertIn("int net_recv_frame", net, "net.c exposes the callable receive-frame API")

    def test_the_glue_fixture_and_lwipopts_are_config_only_not_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertTrue(os.path.exists(GLUE_FIXTURE), "the worker glue fixture exists (content)")
        self.assertTrue(os.path.exists(LWIPOPTS_FIXTURE), "the lwipopts fixture exists (config)")
        for m in ATTESTED_MEMBERS:
            self.assertNotIn("lwip", m.lower(), "no lwIP artifact is an attested member (I3)")
            self.assertNotIn("lwiperf", m.lower())
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built worker image is NEVER a signed member")


class TestA7MembersHoldTheOtherWorkerHolds(unittest.TestCase):
    def test_the_attested_count_is_unchanged_at_88_no_new_member(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        # 6b is edit-in-place (serve.c/enclosure.c/enclosure.h/net.c/build.sh); it adds NO src/body member.
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "the attested list is unchanged (no new member, C7 P3b-6b)")
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "the 31 src/body source files are unchanged (no new file)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers the members")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list")

    def test_serve_c_still_refuses_the_socket_share_as_the_native_failure(self):
        # the socket act share is still refused (6b serves the borrowed stack's FRAME shapes, not SYS_socket).
        with open(os.path.join(BODY, "serve.c"), encoding="utf-8") as f:
            serve = f.read()
        self.assertIn("case SYS_socket:", serve, "serve.c still handles the socket share")
        self.assertRegex(serve, r"g_socket_refused = 1;\s*/\* refused as the worker's native failure",
                         "SYS_socket is still refused as the native failure — 6b serves frame shapes, not socket")


if __name__ == "__main__":
    unittest.main()
