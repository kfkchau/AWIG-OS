# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding body running the REAL, unmodified /usr/bin/python3 as an enclosed worker: the interpreter
# loaded by the body's own dynamic loader from ONE sealed digest-checked image — the interpreter + its C
# library + the loader-visible pieces + its standard library as REAL FILES served by path AND by listing — on
# the real floor (P3b-4f) through the real linker (P3b-4d); print(2+2)=4 and a thread run FOR REAL) as in the
# seL4/gVisor/Fuchsia and osdev literature. NON-GOAL: no offensive capability — this RUNS a borrowed program,
# unmodified and unprivileged, on our own kernel's body and proves the same acts under our own performer, by
# function; it stands nothing as production, binds no key, touches no host kernel (every boot the guest's
# nested qemu). Full declaration: SCOPE-STATEMENT.md.
"""C7 P3b-4c acceptance — THE INTERPRETER RUNS ON THE BODY (design/54 §5 L19; §7 row P3b-4c; the RE-MINT
countersign board :4142; the pre-flight FINDINGS Q3/Q4/Q15/:4134/:4135).

On the real floor (P3b-4f) through the dynamic loader + sealed image (P3b-4d), the body loads and runs the
REAL unmodified CPython 3.12.3 — the LAST prover of L19 (static -> dynamic -> the interpreter). The sealed
image carries the interpreter + its C library + the loader-visible pieces + its standard library as REAL
FILES (7 shared objects incl. libcrypto.so.3 via _hashlib, 28 .pyc, the .py present + stat-validated so the
timestamp .pyc is used without opening the .py, the locale/gconv/ssl data files), served BY PATH AND BY
LISTING (importlib lists each sys.path directory once per import, Q15/:4134); it is digest-checked before
load. The interpreter runs UNPRIVILEGED and UNMODIFIED as an enclosed worker and IS THE PROVER (L19): a plant
makes the REAL interpreter FAIL to start or run, never a body-side flag.

  A1  the real unmodified interpreter runs on the body from the digest-checked sealed image through the real
      linker: FLOOR3C-SEAL OK, the interpreter's PT_INTERP read, the handover to ld.so's entry (0x7f..),
      print(2+2) prints 4 AND a thread runs (thread-ran; one thread created + exited), the twelve rows' digest
      on serial, FLOOR3C: PASS. A PLANTED byte change in the sealed image (PLANT_SEAL_TAMPER) refuses the load
      and the interpreter NEVER STARTS; a PLANTED skip of the linker (PLANT_SKIP_INTERP) faults the real
      interpreter before it runs; a PLANTED broken floor primitive (PLANT_NO_FS_BASE — %fs never installed)
      faults the real interpreter in TLS setup. Each is a real failure of the real interpreter, not a flag.
  A2  P7a's interpreter-hosting layer is RE-HOMED onto the body's own metal acts (a PERFORMER-SWAP beneath the
      seam), NOT rewritten: src/hosting/interpreter_host.py and src/bridge/host_seam.py are unchanged, nothing
      above the seam changed; the interpreter's host surface (memory/disk/clock/entropy/the crossing/the real
      floor/the dynamic loader) is performed by the BODY's metal acts (serve.c) instead of a hosted stand-in.
  A5  our re-home is EDIT-IN-PLACE C (no new src/body file): ATTESTED_MEMBERS == 87, src/body == 30; the
      interpreter, its sealed image and the borrowed ld.so/libc/stdlib are NEVER members (enclosed, I3); no
      host-kernel load; gov-os source is not inside the borrowed image.
  A6  no founding (ACT_KINDS twelve, pack sha 95631e8f byte-unchanged, founding 1.55.0); the attested count-
      pins stand at 87 (edit-in-place).

  A3/A4 (the deferred per-act gate row landing on the body; the interpreter act-witnessed / re-pinned) are a
      further sub-build (gov-os's own gate running on the body-hosted interpreter and signing a record row
      from a distinct on-disk witness class — mini-self-hosting, the P3b-5 precursor); see the BUILD-PROGRESS
      entry / EVIDENCE.md for status. Their assertions are added here when built.

The boot acceptances build+boot in the NESTED guest (a bodyfs disk attached as P3b-2, the ~21 MB sealed image
carried as a multiboot module) and skip when the pinned guest is not reachable over SSH; the rest run in main.
Register: OS bring-up on a disposable guest, described by function — a body that runs a borrowed interpreter,
unmodified and unprivileged, through the ordinary linker from one sealed checked set of files; validated by
building/reading, never by attack (governance-work-method). Every kernel touch is the guest's nested qemu; the
host kernel is never touched (L11 / EP-00 rule 9 / §A21).
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

ROWS_DIGEST = "sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb"

# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ───────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4c-accept"
# -cpu qemu64: SSE2, NO AVX — matches the pre-flight's measured (no-AVX) environment, so no library attempts
# an AVX variant while the body keeps CR4.OSXSAVE clear (never OSXSAVE, :4131). -m 256 == the PMM cap.
_QEMU = "qemu-system-x86_64 -cpu qemu64 -serial stdio -display none -no-reboot -m 256 -rtc base=utc"


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
_SERIAL_CACHE = {}


def _seed_guest():
    """Copy src/body + src/bridge + src/founding to the guest ONCE (the interpreter is the guest's own
    /usr/bin/python3.12 — never a fixture; the sealed image is staged at build time by build.sh)."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=120)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s/src && tar -xzf - -C %s/src" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=120, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", tag=None):
    """Build the body in INTERP mode (INTERP=1): build.sh stages the ONE sealed image from the REAL
    interpreter's own strace manifest (the measured set, self-binding to the current guest binary)."""
    _seed_guest()
    tag = tag or (fault or "clean")
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(
        _SSH + ["cd %s/src && INTERP=1 bash body/build.sh body %s %s" % (_WD, out, fault)],
        capture_output=True, timeout=300)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    out_txt = b.stdout.decode(errors="replace")
    assert "sealed image seal sha256" in out_txt, "the sealed image was not staged: " + out_txt
    return out


def _guest_mkdisk(img):
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s/src python3 src/body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img, timeout_s):
    """Boot the body in a NESTED qemu with the sealed image as a MODULE (-initrd) and `img` as a virtual IDE
    disk; return serial text. Every boot is the guest's nested qemu — no host kernel. Boots are SERIALIZED."""
    subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                   capture_output=True, timeout=20)
    boot = subprocess.run(
        _SSH + ["timeout --signal=TERM %d %s -kernel %s/body.img -initrd %s/sealed.img "
                "-drive file=%s,format=raw,if=ide,index=0 </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, outdir, outdir, img)],
        capture_output=True, timeout=timeout_s + 60)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault="", tag=None, timeout_s=300):
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
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 — the REAL unmodified interpreter runs on the body ──────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    import os as _os, subprocess as _sp
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    try:
        return _sp.run(["git", "-C", _root, "rev-parse", "--verify", "HEAD"],
                       capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


class TestA1TheRealInterpreterRunsOnTheBody(unittest.TestCase):
    def test_the_real_unmodified_interpreter_runs_and_prints_and_threads(self):
        serial = _serial(timeout_s=300)
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("LONGMODE: OK", serial, "the body is in the machine's long mode (P3b-4L)")
        self.assertRegex(serial, r"MODULE: count=0x0*1 ", "the ONE sealed image arrived as a multiboot module")
        self.assertIn("FLOOR3C-SEAL: OK (digest matches the seal)", serial, "the sealed image digest-checked")
        self.assertIn("FLOOR3C-INTERP: /lib64/ld-linux-x86-64.so.2", serial, "the interpreter's PT_INTERP read")
        self.assertIn("FLOOR3C-LISTABLE: OK", serial, "the image is served BY LISTING (importlib lists dirs)")
        self.assertIn("FLOOR3C-BESIDE: OK", serial, "the P3b-2 record FS is mounted beside, distinct namespaces")
        self.assertRegex(serial, r"FLOOR3C-HANDOVER: entry=0x00007f", "handover jumped to ld.so's entry (0x7f..)")
        # THE L19 PROOF: the interpreter's OWN output — it computed 2+2 itself, and a real thread ran.
        self.assertRegex(serial, r"(?m)^4$", "print(2+2) printed 4 — the REAL interpreter computed it")
        self.assertIn("thread-ran", serial, "a real Python thread ran on the body (clone3 real context)")
        self.assertIn("FLOOR3C: PASS", serial, "the interpreter-on-body self-check passes as a group")
        self.assertIn("FLOOR3C-ACTS: PASS", serial)
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")

    def test_a_real_thread_was_created_and_exited(self):
        serial = _serial(timeout_s=300)
        m = re.search(r"FLOOR3C-THREADS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the thread counter is on serial")
        self.assertGreaterEqual(int(m.group(1), 16), 1, "at least one real thread context was created (clone3)")
        me = re.search(r"FLOOR3C-EXITS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(me, "the exit counter is on serial")
        self.assertGreaterEqual(int(me.group(1), 16), 1, "the thread ended via SYS_exit (join returned)")

    def test_the_enclosure_and_forty_nine_router_still_pass_unchanged(self):
        serial = _serial(timeout_s=300)
        self.assertIn("ENCLOSURE: PASS", serial, "the enclosure MECHANISM still passes (P3b-4a, unchanged)")
        self.assertIn("SERVE: PASS", serial, "the forty-nine classification kept as the router (P3b-4b)")
        self.assertIn("SERVE-ACTS: PASS", serial)


# ── A1 plants — a plant makes the REAL interpreter fail, never a flag (L19) ─────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the A1 plants need the pinned guest + nested qemu over SSH -p 2222")
class TestA1PlantsMakeTheRealInterpreterFail(unittest.TestCase):
    def test_seal_tamper_refuses_the_load_and_the_interpreter_never_starts(self):
        serial = _serial(fault="PLANT_SEAL_TAMPER", timeout_s=150)
        self.assertIn("FLOOR3C-SEAL: REFUSED", serial, "a byte change refuses the sealed image at load")
        self.assertNotRegex(serial, r"(?m)^4$", "print(2+2) NEVER runs — the interpreter never starts")
        self.assertNotIn("thread-ran", serial, "no thread — the interpreter never starts")
        self.assertIn("FLOOR3C: FAIL", serial)

    def test_skip_interp_faults_the_real_interpreter_before_it_runs(self):
        serial = _serial(fault="PLANT_SKIP_INTERP", timeout_s=200)
        self.assertIn("FLOOR3C-SEAL: OK", serial, "the image is intact — the fault is the skipped linker")
        self.assertRegex(serial, r"FLOOR3C-HANDOVER: entry=0x0*[0-9a-f]+ ld_base=0x0+\b",
                         "the handover skipped ld.so (ld_base=0) — entered the interpreter directly")
        self.assertIn("FLOOR3C-FAULT: vec=0x0000000e", serial, "the real interpreter #PF'd (libc unrelocated)")
        self.assertNotRegex(serial, r"(?m)^4$", "the interpreter never reached print(2+2)")
        self.assertIn("FLOOR3C: FAIL", serial)

    def test_no_fs_base_faults_the_real_interpreter_in_tls_setup(self):
        serial = _serial(fault="PLANT_NO_FS_BASE", timeout_s=200)
        self.assertRegex(serial, r"FLOOR3C-HANDOVER: entry=0x00007f", "the handover to ld.so is correct")
        self.assertIn("FLOOR3C-FAULT: vec=0x0000000e", serial,
                      "the real interpreter #PF'd — a thread-local access with %fs base 0 (a broken primitive)")
        self.assertNotRegex(serial, r"(?m)^4$", "the interpreter never reached print(2+2)")
        self.assertIn("FLOOR3C: FAIL", serial)


# ── A2 — P7a re-homed (performer-swap beneath the seam), NOT rewritten; nothing above the seam changed ─
class TestA2PerformerSwapNotRewrite(unittest.TestCase):
    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs a git repository (git history is unavailable in the render)")
    def test_the_p7a_layer_and_seam_are_unchanged_by_this_slice(self):
        # This slice is a PERFORMER-SWAP beneath the seam: the interpreter's host surface is performed by the
        # BODY's metal acts (serve.c), not the hosted stand-in. The P7a layer contract is untouched — the
        # re-home needed no edit to interpreter_host.py or host_seam.py (they were CLOSED at P7a/P2).
        hs = os.path.join(SRC, "bridge", "host_seam.py")
        ih = os.path.join(SRC, "hosting", "interpreter_host.py")
        self.assertTrue(os.path.exists(hs) and os.path.exists(ih), "the P7a layer + the seam still exist")
        # nothing ABOVE the seam changed: this slice's edits are confined to src/body/ (the metal performer).
        r = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", "HEAD"], capture_output=True, text=True)
        changed = [p for p in r.stdout.split() if p.startswith("src/") and not p.endswith(".pyc")]
        above_seam = [p for p in changed if p.startswith("src/") and not p.startswith("src/body/")]
        self.assertEqual(above_seam, [], "only src/body/ (beneath the seam) changed; nothing above it: %r" % above_seam)


# ── A5 / A6 — attestation edit-in-place; no founding (main) ─────────────────────────────────────────
class TestA5A6AttestationAndNoFounding(unittest.TestCase):
    def test_attestation_edit_in_place_no_new_member(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88, "edit-in-place — this slice adds no src member (88 after C7 P3b-6a's net.c)")
        self.assertEqual(attestation.ATTESTED_MEMBERS, tuple(sorted(attestation.ATTESTED_MEMBERS)))
        # the interpreter / its image / the borrowed libraries are NEVER members (enclosed, I3).
        for m in attestation.ATTESTED_MEMBERS:
            self.assertFalse(m.endswith((".img", ".so", ".so.6", ".so.1", ".so.3")), "no borrowed artifact is a member")
            self.assertNotIn("python3", m)
            self.assertNotIn("libpython", m)

    def test_src_body_is_thirty_files_edit_in_place(self):
        # 30 source files: build.sh has no matched extension in the glob, so count it in.
        names = _body_source_names()
        self.assertEqual(len(names), 31, "src/body is 31 files (this slice adds none; C7 P3b-6a added net.c): %r" % names)

    def test_no_founding_act_kinds_twelve_pack_unchanged(self):
        from bridge.host_seam import ACT_KINDS
        self.assertEqual(len(ACT_KINDS), 12, "running the interpreter realizes existing acts — no new act kind")
        pack = os.path.join(SRC, "founding", "founding-pack.json")
        import json
        with open(pack) as f:
            self.assertEqual(json.load(f)["founding_version"], "1.55.0", "no founding")
        with open(pack, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        self.assertTrue(sha.startswith("95631e8f"), "the founding pack is byte-unchanged (sha %s)" % sha[:8])


if __name__ == "__main__":
    unittest.main()
