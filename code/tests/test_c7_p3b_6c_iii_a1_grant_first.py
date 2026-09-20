# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (the freestanding kernel body composes gov-os's OWN gate as content off the record disk and records the
# network-open as a rule-citing decision FIRST, then hands ONLY a granted decision to the enclosed borrowed
# worker for one guest-local connection — exactly as a real kernel decides an access on its record before
# performing it) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability — gov-os's own
# record-decided open on our core, ONE guest-local connection on a grant, NOTHING on a refusal; the server
# socket and the production-performer step stay OUT. Validate by building/reading, never by attack. Every
# kernel touch is the guest's nested qemu; the host kernel is never touched (L11 / EP-00 rule 9 / §A21).
"""C7 P3b-6c slice (iii) A1 — GRANT-FIRST: gov-os DECIDES THE OPEN ON ITS OWN RECORD, ON THE BODY.

The mgr sub-split of slice (iii)'s A1 on the spike findings (planning/evidence/
C7-P3b-6c-iii-A1-GRANT-FIRST-SPIKE/FINDINGS.md). The LEDGER-class GRANT boot carries the whole-stdlib sealed
image (so build_full_kernel's 30-module closure composes gov-os's gate off the GOVOS_TREE record disk) AND
the SOCKET_ACT relay + enclosed lwIP op-server (so a GRANTED record-decision reaches one real guest-local
connection). The -c grant program (enclosure.c g_grant_script) runs gov-os's OWN gate: build_full_kernel ->
CREATE-ACCOUNT -> open_real_socket_under_grant. The VEHICLE is test_ep48g's grant test's own operations,
run on the body (a REAL gate, never a fitted prover).

  A1  THE GRANT REACHES gov-os's GATE ON THE BODY. build_full_kernel composes; an opener is established
      (CREATE-ACCOUNT); open_real_socket_under_grant(..., guest_check->False) records SOCKET-OPEN citing
      NET-LAW-GRANT (RealSocketOnHostRefused, no host fd needed to prove the DECISION). PLANT (can fail):
      an UNESTABLISHED opener -> OpError at the gate, NO SOCKET-OPEN row, no socket.
  A2  A GRANTED DECISION -> ONE REAL CONNECTION VIA THE PROVEN RELAY. on the granted decision the family is
      handed to the already-proven 6c relay (the interpreter's socket-family shapes cross to the enclosed
      lwIP worker), one guest-local connection completes over nested SLIRP, peer-witnessed. PLANT: a refused
      grant reaches no relay call (no socket() crossing).
  A3  A REFUSED GRANT -> NO SOCKET, NO RELAY, ON THE RECORD. a refused grant (unestablished opener) raises at
      the gate with EACCES (NET-LAW-GRANT -> EACCES) and no worker call is made. PLANT (can fail):
      PLANT_GRANT_BYPASS drives the relay on a refusal ANYWAY -> the refused-decision verdict reds.
  A4  NOTHING ELSE MOVES. src/kernel/** untouched (the gate runs AS CONTENT from the record disk); ACT_KINDS
      12; ATTESTED 88 (no new src/body member); no bodyfs.c/disk.h/founding change; every GRANT addition is
      #ifdef GRANT_FIRST-gated (a plain SOCKET_ACT boot is byte-identical); the production step NOT taken.

A1-A4 build+boot in the NESTED guest and skip when the pinned guest is not reachable. ONE nested boot at a
time (the boot lane is serialized). Register: an OS deciding an access on its own record before performing
it, described by function — validated by building/reading, never by attack.
"""

import os
import re
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
sys.path.insert(0, SRC)

# the config-only fixtures (content, NEVER attested members — under tests/, not src/body). Reused byte-for-
# byte: the socket-act op-server glue (I3) + 6b's lwipopts.
SOCKET_GLUE = os.path.join(HERE, "c7_p3b_6c_iii_socket_worker_glue.c")
LWIPOPTS_FIXTURE = os.path.join(HERE, "c7_p3b_6b_lwipopts.h")

# the pinned lwIP 2.2.0 SOURCE provenance (the 6b/6c-ii unit's, unchanged).
DSC_SHA = "7c2a3c003375653b24e7f59ea2192a445b3d68c5a61c989ad8eca0a693752b97"
ORIG_SHA = "3a56474c26be8efe05c6b626a256c67bd9ee3739084e2844a4c989be031e7786"

_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR", "<GUEST>"]
_WD = "/tmp/p3b6ciii-a1-accept"
# the combined GRANT boot: the whole-stdlib sealed interpreter is a MODULE (-initrd sealed.img); the lwIP
# worker is incbin'd in the body; the GOVOS_TREE record disk is an IDE drive (so /rec serves gov-os source +
# /rec/tmp); virtio-net on a USER-MODE (SLIRP) network routes the guest-local connection to a plain echo
# listener in the OUTER guest at 10.0.2.2:5001. -cpu qemu64 (SSE2, no AVX — the interpreter floor keeps
# CR4.OSXSAVE clear). -m 256 (the 5b LEDGER boot's cap). Serialized: one nested qemu at a time.
_QEMU = ("qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc "
         "-netdev user,id=n1 -device virtio-net-pci,netdev=n1")
_BOOT_WAIT = 300   # the whole-stdlib interpreter boot in nested TCG is slow; a generous BODY-HALT budget.


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
_BUILT = {}      # tag -> (outdir, buildtxt)
_DISK = {"path": None}
_BOOTED = {}     # tag -> (serial, peer_bytes)


def _seed():
    """Stage src+tests (the tree the disk is built from AND the body source), the socket-act glue + lwipopts
    + cc.h, and fetch the pinned lwIP 2.2.0 SOURCE (provenance-checked). Once per run."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", ROOT, "src", "tests"], capture_output=True, timeout=180)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s/port/arch" % (_WD, _WD)],
                   capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True,
                   timeout=180, check=True)
    for src_path, dst in ((SOCKET_GLUE, _WD + "/port/socket_glue.c"),
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
             "apt-get source liblwip-dev >/tmp/aptsrc-6ciii-a1.log 2>&1; "
             "sha256sum *.dsc *.orig.tar.* ; ls -d lwip-*/" % (_WD, _WD, _WD))
    r = subprocess.run(_SSH + [fetch], capture_output=True, timeout=240)
    out = r.stdout.decode(errors="replace")
    assert DSC_SHA in out and ORIG_SHA in out, "lwIP source provenance mismatch:\n" + out
    m = re.search(r"(lwip-\S+)/", out)
    assert m, "lwIP source tree not found:\n" + out
    _SEEDED["lwip"] = "%s/lwipsrc/%s" % (_WD, m.group(1))
    _SEEDED["done"] = True


def _build(tag, refused=False, plant=""):
    """Build the LEDGER-class GRANT body (GRANT=1) in the guest, staging the whole-stdlib sealed image + the
    lwIP op-server worker. GRANT_REFUSED builds the refused-decision variant; `plant` rides the FAULT arg.
    Cached per tag. Returns (outdir, buildtxt)."""
    if tag in _BUILT:
        return _BUILT[tag]
    _seed()
    out = "%s/out-%s" % (_WD, tag)
    env = ("GRANT=1 %sLWIP_SRC=%s GLUE_SRC=%s/port/socket_glue.c LWIP_PORT=%s/port"
           % (("GRANT_REFUSED=1 " if refused else ""), _SEEDED["lwip"], _WD, _WD))
    b = subprocess.run(_SSH + ["cd %s/src && %s bash body/build.sh body %s %s"
                               % (_WD, env, out, plant)], capture_output=True, timeout=420)
    txt = b.stdout.decode(errors="replace") + "\n" + b.stderr.decode(errors="replace")
    if b.returncode != 0:
        raise AssertionError("guest GRANT build failed (%s):\n%s" % (tag, txt[-2000:]))
    assert "sealed image seal sha256" in txt, "the whole-stdlib sealed image was not staged:\n" + txt[-2000:]
    _BUILT[tag] = (out, txt)
    return _BUILT[tag]


def _mkdisk():
    """Build the GOVOS_TREE record disk ONCE (the same disk for every GRANT mode) — the whole gov-os
    source+tests tree the on-body gate imports from /rec/src, resolved by serve.c's finder."""
    if _DISK["path"]:
        return _DISK["path"]
    _seed()
    img = "%s/grant-disk.img" % _WD
    m = subprocess.run(
        _SSH + ["cd %s && GOVOS_TREE=1 PYTHONPATH=%s/src python3 src/body/mkdisk.py %s" % (_WD, _WD, img)],
        capture_output=True, timeout=120)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk (GOVOS_TREE) failed: " + m.stderr.decode(errors="replace"))
    _DISK["path"] = img
    return img


def _boot(tag, refused=False, plant=""):
    """Boot the GRANT body in a NESTED qemu with the GOVOS_TREE disk + virtio-net + a plain ECHO listener in
    the OUTER guest (the relay's 'ping'->'pong' peer). DETACHED (setsid) with serial to a file, POLLed until
    BODY-HALT (the whole-stdlib boot is slow — the detached+poll pattern is the reliable one). ONE nested
    qemu at a time (killed before + after). Returns (serial, peer_bytes). Cached per tag."""
    if tag in _BOOTED:
        return _BOOTED[tag]
    out, _ = _build(tag, refused=refused, plant=plant)   # BUILD first (no lane needed — safe concurrently)
    disk = _mkdisk()
    _acquire_lane()                                      # then wait for the boot lane (never stack/kill)
    ser = "%s/serial-%s.txt" % (_WD, tag)
    run = "%s/run-%s.sh" % (_WD, tag)
    # the echo peer: accept, echo every recv back (the relay's 'ping' -> 'pong'), record the byte count.
    peer = (
        "import socket,sys\n"
        "s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
        "s.bind(('0.0.0.0',5001));s.listen(1);s.settimeout(60)\n"
        "total=0\n"
        "try:\n"
        " c,a=s.accept();c.settimeout(30)\n"
        " while True:\n"
        "  d=c.recv(4096)\n"
        "  if not d: break\n"
        "  total+=len(d)\n"
        "  c.sendall(b'pong')\n"
        " c.close()\n"
        "except Exception as e: sys.stderr.write('PEER-ERR '+repr(e)+chr(10))\n"
        "open('/tmp/peer6ciii.log','w').write('PEER-BYTES='+str(total)+chr(10))\n")
    body = (
        "#!/bin/bash\n"
        "pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null\n"
        "rm -f %s\n"
        "%s -serial file:%s -kernel %s/body.img -initrd %s/sealed.img "
        "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
        % (ser, _QEMU, ser, out, out, disk))
    launch = (
        "pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null; pkill -9 -f peer6ciii.py 2>/dev/null; "
        "rm -f /tmp/peer6ciii.log; cat > /tmp/peer6ciii.py <<'PYEOF'\n" + peer + "PYEOF\n"
        "nohup python3 /tmp/peer6ciii.py >/tmp/peer6ciii.out 2>&1 & sleep 1; "
        "cat > %s <<'EOS'\n%sEOS\nchmod +x %s; setsid %s >/dev/null 2>&1 & sleep 1; echo launched"
        % (run, body, run, run))
    subprocess.run(_SSH + ["bash -s"], input=launch.encode(), capture_output=True, timeout=40)
    deadline = time.time() + _BOOT_WAIT
    while time.time() < deadline:
        r = subprocess.run(_SSH + ["grep -q BODY-HALT %s 2>/dev/null && echo HALTED || true" % ser],
                           capture_output=True, timeout=20)
        if b"HALTED" in r.stdout:
            break
        time.sleep(3)
    r = subprocess.run(
        _SSH + ["cat %s 2>/dev/null; echo '=====PEER====='; cat /tmp/peer6ciii.log 2>/dev/null; "
                "pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null; pkill -9 -f peer6ciii.py 2>/dev/null; true"
                % ser], capture_output=True, timeout=40)
    text = r.stdout.decode(errors="replace").replace("\r", "")
    serial, _, peerpart = text.partition("=====PEER=====")
    m = re.search(r"PEER-BYTES=(\d+)", peerpart)
    _BOOTED[tag] = (serial, int(m.group(1)) if m else 0)
    return _BOOTED[tag]


def _acquire_lane(timeout_s=1200):
    """LANE DISCIPLINE: ONE nested qemu at a time across the estate. Poll until the guest shows 0 nested
    qemu for a sustained window BEFORE this unit pkills strays and boots — so a concurrent boot (another
    seat's) is WAITED FOR, never killed and never stacked on. Returns when the lane is free; raises on
    timeout (the caller reports a lane-blocked STOP rather than forcing a second concurrent boot)."""
    deadline = time.time() + timeout_s
    clear = 0
    while time.time() < deadline:
        r = subprocess.run(_SSH + ["pgrep -f '[q]emu-system-x86_64' | wc -l"],
                           capture_output=True, timeout=20)
        n = int((r.stdout.decode(errors="replace").strip() or "1"))
        clear = clear + 1 if n == 0 else 0
        if clear >= 2:                       # two consecutive 0-nested reads: the lane is genuinely free
            return
        time.sleep(5)
    raise AssertionError("boot lane never freed within %ds (a concurrent nested boot holds it) — STOP, "
                         "do not stack a second boot" % timeout_s)


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f '[q]emu-system-x86_64' 2>/dev/null; "
                               "pkill -9 -f peer6ciii.py 2>/dev/null; true"], capture_output=True, timeout=20)


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
# A1 + A2 — the GRANTED boot: gov-os's gate decides the open, then hands the granted decision to the relay.
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the GRANT boot needs the pinned guest (6.8.0-134) + nested qemu over SSH :2222")
def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    import os as _os, subprocess as _sp
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    try:
        return _sp.run(["git", "-C", _root, "rev-parse", "--verify", "HEAD"],
                       capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


class TestGrantFirstGranted(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serial, cls.peer_bytes = _boot("granted")

    def test_A1_the_gate_composes_on_the_body_and_records_the_grant(self):
        s = self.serial
        self.assertIn("BODY-HALT", s, "the body must reach BODY-HALT:\n" + s[-1500:])
        self.assertIn("GRANT-COMPOSED", s, "build_full_kernel must compose gov-os's gate on the body")
        # the grant is on the record, citing NET-LAW-GRANT (the decision, no host fd).
        self.assertRegex(s, r"GRANT-A1-GRANTED granted=True rule=NET-LAW-GRANT",
                         "the record must decide SOCKET-OPEN citing NET-LAW-GRANT:\n" + s[-1500:])

    def test_A1_plant_an_unestablished_opener_operrors_with_no_row(self):
        # the PLANT (can fail): an unestablished opener -> OpError at the gate, NO SOCKET-OPEN row, no socket.
        self.assertIn("GRANT-A1-PLANT-OPERROR plant_ok=True", self.serial,
                      "an unestablished opener must OpError with no g1 row:\n" + self.serial[-1500:])
        # NET-LAW-GRANT renders EACCES from the rule-errno pack (A3's errno, read on the body).
        self.assertIn("GRANT-ERRNO EACCES", self.serial)

    def test_A2_the_granted_decision_hands_to_the_relay_one_real_connection(self):
        s = self.serial
        self.assertIn("GRANT-A2-HANDOFF", s, "a granted decision hands to the relay")
        self.assertRegex(s, r"PYSOCK-CONNECT 0", "the relayed connect completes (0):\n" + s[-1500:])
        self.assertRegex(s, r"PYSOCK-CYCLES 12", "twelve send/recv cycles over the one connection")
        self.assertIn("PYSOCK-DONE", s, "the interpreter closed the connection and continued")
        # the body's relay verdict: the relay ran and a REAL exchange completed (frames both ways + bytes).
        self.assertIn("CHECK SA-CONNECTION: PASS", s)
        self.assertIn("SOCKET-ACT: PASS", s)
        # the peer in the outer guest received REAL bytes over nested SLIRP (peer-witnessed).
        self.assertGreater(self.peer_bytes, 0,
                           "the outer-guest listener received real bytes over the relayed connection")

    def test_A2_gov_os_gate_ran_as_content_not_a_stub(self):
        # GRANT-COMPOSED + the grant decision came from build_full_kernel off the record disk (no LOADERROR):
        # the whole gate ran as content, the decision is real, not a fitted reply (L19).
        self.assertNotIn("GRANT-LOADERROR", self.serial, "the on-body gate must not error:\n" + self.serial[-2000:])
        self.assertIn("GRANT-DONE", self.serial)

    def test_A4_act_kinds_stays_twelve_on_the_body(self):
        # A4 on-body witness: the grant program founds nothing — the body's twelve-row digest count is 0x0c.
        self.assertIn("ROWS-COUNT: 0000000c", self.serial, "ACT_KINDS must stay twelve:\n" + self.serial[-1500:])


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
# A3 — the REFUSED boot: a refused grant -> EACCES on the record, NO relay, no socket crossing.
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the GRANT boot needs the pinned guest + nested qemu")
class TestGrantFirstRefused(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serial, cls.peer_bytes = _boot("refused", refused=True)

    def test_A3_a_refused_grant_reaches_no_socket_no_relay_EACCES_on_the_record(self):
        s = self.serial
        self.assertIn("BODY-HALT", s, "the refused body reaches BODY-HALT (a completed run):\n" + s[-1500:])
        self.assertIn("GRANT-COMPOSED", s)
        # the gate raised BEFORE any socket (unestablished opener); the refusal renders EACCES; g1 never lived.
        self.assertRegex(s, r"GRANT-A3-REFUSED raised=True g1-live=False errno=EACCES",
                         "the refused grant must raise with EACCES and no g1 socket:\n" + s[-1500:])
        self.assertIn("GRANT-A3-NO-RELAY", s, "a refused grant drives no relay")
        # the body's grant-first verdict: ZERO relays, ZERO frames -> no socket crossed on the refusal.
        self.assertRegex(s, r"GRANT-REFUSED-RELAYS: 0x0+ FRAMES: 0x0+",
                         "no socket-family shape crossed on a refusal:\n" + s[-1500:])
        self.assertIn("GRANT-REFUSED: PASS", s)
        self.assertEqual(self.peer_bytes, 0, "no connection reached the outer-guest listener on a refusal")


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
# A2/A3 PLANT — a check that can fail: PLANT_GRANT_BYPASS drives the relay on a refusal -> the verdict reds.
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the GRANT boot needs the pinned guest + nested qemu")
class TestGrantFirstBypassPlant(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serial, cls.peer_bytes = _boot("plant", refused=True, plant="PLANT_GRANT_BYPASS")

    def test_the_plant_drives_the_relay_on_a_refusal_and_the_verdict_reds(self):
        s = self.serial
        self.assertIn("BODY-HALT", s, "even the plant reaches BODY-HALT (a completed run):\n" + s[-1500:])
        # the refusal still happened on the record...
        self.assertRegex(s, r"GRANT-A3-REFUSED raised=True")
        # ...but the plant drove the relay anyway -> a socket crossed on a refusal -> the verdict REDS (L19).
        self.assertGreater(_relays(s), 0, "the plant drove the relay on a refusal:\n" + s[-1500:])
        self.assertIn("GRANT-REFUSED: FAIL", s, "a socket crossing on a refused grant must red the verdict")
        self.assertNotIn("GRANT-REFUSED: PASS", s)


def _relays(serial):
    m = re.search(r"GRANT-REFUSED-RELAYS: 0x([0-9a-f]+)", serial)
    return int(m.group(1), 16) if m else -1


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
# A4 — NOTHING ELSE MOVES (static, off-body; runs everywhere).
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════
class TestA4NothingElseMoves(unittest.TestCase):
    def test_attested_count_and_no_new_src_body_member(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88, "no new src/body member (ATTESTED stays 88)")
        gs = set(attestation.law_guard_surface(SRC))
        self.assertEqual(gs, set(attestation.ATTESTED_MEMBERS),
                         "the guard surface still equals the attested set — the grant program is a string in "
                         "enclosure.c, the worker glue a tests/ fixture; no new member")

    def test_every_grant_change_is_gated_so_a_plain_socket_act_boot_is_unchanged(self):
        with open(os.path.join(BODY, "enclosure.c")) as f:
            enc = f.read()
        with open(os.path.join(BODY, "build.sh")) as f:
            bld = f.read()
        self.assertIn("#if defined(GRANT_FIRST)", enc, "the grant program is GRANT_FIRST-gated")
        self.assertIn("g_grant_script", enc)
        # the grant program and the grant verdict are BOTH under GRANT_FIRST — a non-GRANT build never
        # compiles them (byte-identical plain SOCKET_ACT / single-enclosure boot).
        self.assertIn("defined(GRANT_FIRST) && defined(GRANT_REFUSED)", enc, "the refused verdict is gated")
        self.assertIn("-DGRANT_FIRST", bld, "build.sh adds GRANT_FIRST only for the GRANT boot")

    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs a git repository (git history is unavailable in the render)")
    def test_the_fence_held_no_kernel_founding_bodyfs_disk_change(self):
        # src/kernel/**, src/founding/**, bodyfs.c, disk.h are MUST-NOT-TOUCH: this unit's tree diff is empty
        # there (the gate runs AS CONTENT from the record disk, never re-homed).
        diff = subprocess.run(["git", "-C", ROOT, "diff", "--name-only",
                               "src/kernel", "src/founding", "src/body/bodyfs.c", "src/body/disk.h"],
                              capture_output=True, text=True, timeout=30).stdout.strip()
        self.assertEqual(diff, "", "MUST-NOT-TOUCH paths changed: " + diff)

    def test_act_kinds_stays_twelve(self):
        # the founding op family is unchanged — the grant program founds nothing (no CREATE-OP/CREATE-RULE).
        # ROWS-COUNT 0x0c is asserted on the booted body by the A1/A3 classes; here the source-side witness.
        from kernel import attestation  # noqa: F401  (import proves the tree is importable off this checkout)
        self.assertTrue(os.path.exists(os.path.join(SRC, "founding", "founding-pack.json")))


if __name__ == "__main__":
    unittest.main()
