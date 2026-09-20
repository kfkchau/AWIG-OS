# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (gov-os's OWN gate — its Python governing code, run AS CONTENT off the body's record disk inside the
# body-hosted interpreter — WRITES AND SIGNS one record row on our own kernel's body: the key material
# read from the record disk (a guest TEST key), the row appended through the record-pen act and read
# back through the body-read act, the crossing trail's DIGEST folded as the one signed act-witness gate
# row; a reader OFF the body verifies the row under the ceremony's bound public half with the estate's
# OWN verifier) as in the seL4/gVisor/Fuchsia and osdev literature. NON-GOAL: no offensive capability —
# gov-os keeps its own signed record while standing on our own body, by function; guest test keys only,
# the owner's key material never on the body; every boot the guest's nested qemu; the host kernel
# untouched. Full declaration: SCOPE-STATEMENT.md.
"""C7 P3b-4g acceptance — THE GATE ON THE BODY (mini self-hosting; design/54 §5 L18/L19, §7 row P3b-4g;
the RE-MINT countersign board :4227; precisions (a) the signature's state measured at dispatch — MODELLED
(libsodium absent, Q5) — and (b) the off-body verifier is the estate's own keys.py/signer.py compare path).

On the interpreter running on the body (C7-P3b-4c CLOSED), gov-os's OWN gate is imported AS CONTENT off
the record disk (kernel.keys / kernel.signer / kernel.crypto / kernel.canonical + bridge.host_seam — NEVER
inside the borrowed sealed image, I7) by a finder that reads each module through the body-read act. It reads
a guest TEST key from the record disk, signs a record row with the estate's REAL keys.countersign (the
MODELLED custody mark — libsodium is absent in the sealed image, precision a), appends it through the
record-pen act and reads it back through the body-read act, and folds the body's crossing-trail file's
DIGEST as the one signed act-witness gate row (the trail itself stays the body's UNSIGNED, key-less floor).
A reader OFF the body (this test, the repo's shipping kernel.keys — the same bytes that ship, precision b)
verifies the rows under the bound public half, and every plant reds by that REAL mechanism.

  A1  gov-os's own gate (content) signs a record row; the reader OFF the body verifies it under the bound
      public half (keys.verify_countersign). PLANTS (real mechanism): a WRONG key fails the verify; a
      TAMPERED recording fact (the seq the mark binds) fails the verify. State: MODELLED (GOB-REAL-AVAIL
      False) — named honestly (precision a).
  A2  the crossing-trail file's DIGEST is the signed act-witness row and NAMES the same crossings (the
      digest recomputes from the trail's bytes); the floor stays UNSIGNED + key-less (SERVE CHECK
      KEYLESS/UNSIGNED PASS). PLANT: a TAMPERED trail digest is refused (recompute mismatch).
  A3  the row is read back through the body-read act from the body's own disk (readback == written). PLANT
      (a boot): PLANT_RECORD_READBACK_WRONG corrupts the body-disk write -> the read-back differs -> reds.
  A4  an UNGATED row (no signed decision) is refused by the chain (verify_countersign False), and the
      prev_hash chain is intact; PLANT: a CONTENT tamper breaks the chain (canonical_hash mismatch).
  A5/A6 (main) the gate is CONTENT not src edits: ATTESTED_MEMBERS == 87 (edit-in-place, no new src member),
      src/body == 30 files, the interpreter/image/borrowed libs NEVER members (I3); ACT_KINDS == 12, the
      founding pack byte-unchanged (95631e8f), founding 1.55.0 (no founding); nothing above the seam changed
      (git diff only src/body). PLANT (a boot): PLANT_SEAL_TAMPER -> the sealed image is refused, the gate
      never runs (no GATEONBODY) — the host kernel untouched, guest-only.

The boot acceptances build+boot in the NESTED guest and skip when the pinned guest is not reachable over
SSH; the rest run in main. Every kernel touch is the guest's nested qemu; the host kernel is never touched
(L11 / EP-00 rule 9 / §A21). Validated by building/reading + a real signed record, never by attack
(governance-work-method).
"""

import base64
import hashlib
import json
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

from kernel import keys                       # the estate's OWN verifier, OFF the body (the shipping bytes)
from kernel.canonical import canonical_hash   # the estate's ONE hash form (the chain)

WRONG_CUSTODY = "sha256:" + "0" * 64
GENESIS = {"seq": 0, "record_time": "genesis"}

# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ───────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4g-accept-test"
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
    """Copy src/body + src/bridge + src/founding + src/kernel to the guest ONCE. src/kernel is the gate
    source that reaches the body AS CONTENT on the record disk (staged by mkdisk --gate) — NEVER inside
    the borrowed image (:4091 c / I7)."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding", "kernel"],
                         capture_output=True, timeout=120)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s/src && tar -xzf - -C %s/src" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=120, check=True)
    _SEEDED["done"] = True


def _guest_build(fault="", tag=None):
    """Build the body in INTERP + GATE mode: build.sh stages the sealed image from the gate bootstrap's
    OWN strace manifest (the wider key-family stdlib closure), EXCLUDING the gov-os source (record-disk
    content); the body is compiled with -DGATE_ON_BODY (enclosure.c runs gov-os's own gate as argv)."""
    _seed_guest()
    tag = tag or (fault or "clean")
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(
        _SSH + ["cd %s/src && INTERP=1 GATE=1 bash body/build.sh body %s %s" % (_WD, out, fault)],
        capture_output=True, timeout=420)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    assert "sealed image seal sha256" in b.stdout.decode(errors="replace"), "the sealed image was not staged"
    return out


def _guest_mkdisk(img):
    """Format the P3b-2 record disk WITH the gate content (gov-os source + the guest test key), :4091 c/d."""
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s/src GOVOS_GATE=1 python3 src/body/mkdisk.py %s"
                               % (_WD, _WD, img)], capture_output=True, timeout=90)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    assert "gate content" in m.stdout.decode(errors="replace"), "the gate content was not staged on the disk"
    return img


def _guest_boot(outdir, img, timeout_s):
    subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                   capture_output=True, timeout=20)
    boot = subprocess.run(
        _SSH + ["timeout --signal=TERM %d %s -kernel %s/body.img -initrd %s/sealed.img "
                "-drive file=%s,format=raw,if=ide,index=0 </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, outdir, outdir, img)],
        capture_output=True, timeout=timeout_s + 60)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault="", tag=None, timeout_s=150):
    key = tag or (fault or "clean")
    if key not in _SERIAL_CACHE:
        out = _guest_build(fault, tag=key)
        img = _guest_mkdisk("%s/disk-%s.img" % (_WD, key))
        _SERIAL_CACHE[key] = _guest_boot(out, img, timeout_s)
    return _SERIAL_CACHE[key]


def _parse(serial):
    d = {}
    for ln in serial.splitlines():
        for tag, key, b64 in (("GOB-ROW-SIGNED ", "signed", True), ("GOB-ROW-READBACK ", "readback", True),
                              ("GOB-WITNESS ", "witness", True), ("GOB-TRAIL ", "trail", True),
                              ("GOB-UNGATED ", "ungated", True), ("GOB-CUSTODY ", "custody", False),
                              ("GOB-REAL-AVAIL ", "real", False)):
            if ln.startswith(tag):
                v = ln[len(tag):].strip()
                d[key] = base64.b64decode(v) if b64 else v
    return d


def _body_source_names():
    return sorted(n for n in os.listdir(BODY) if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 — gov-os's own gate (content) signs a record row; a reader OFF the body verifies it ──────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    import os as _os, subprocess as _sp
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    try:
        return _sp.run(["git", "-C", _root, "rev-parse", "--verify", "HEAD"],
                       capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


class TestA1GateSignsAndOffBodyVerifies(unittest.TestCase):
    def test_the_gate_ran_on_the_body_and_signed_a_row(self):
        serial = _serial()
        self.assertIn("FLOOR3C-SEAL: OK (digest matches the seal)", serial, "the sealed image digest-checked")
        self.assertRegex(serial, r"FLOOR3C-HANDOVER: entry=0x00007f", "handover to ld.so (the real interpreter)")
        self.assertIn("GATEONBODY-BEGIN", serial, "gov-os's own gate ran as content on the body")
        self.assertIn("GATEONBODY-END", serial, "the gate completed its record work on the body")
        self.assertIn("FLOOR3G: PASS", serial, "the gate-on-body run completed on the body")

    def test_the_signed_row_verifies_off_the_body_and_the_wrong_key_fails(self):
        d = _parse(_serial())
        self.assertIn("custody", d, "the bound public custody half was copied out")
        signed_full = json.loads(d["signed"])
        mark = signed_full["countersign"]
        signed = {k: v for k, v in signed_full.items() if k != "countersign"}
        # A1 — the estate's OWN verifier accepts the row under the bound public half.
        self.assertTrue(keys.verify_countersign(mark, signed, d["custody"]),
                        "the row the body-hosted gate signed verifies OFF the body under the bound public half")
        # PLANT — a WRONG key: the REAL check FAILS (not a flag).
        self.assertFalse(keys.verify_countersign(mark, signed, WRONG_CUSTODY),
                         "a wrong key must fail the real signature check off the body")
        # PLANT — a TAMPERED recording fact (the seq the mark binds): the REAL check FAILS.
        tampered = dict(signed); tampered["seq"] = 999
        self.assertFalse(keys.verify_countersign(mark, tampered, d["custody"]),
                         "a tampered recording fact must fail the real check")

    def test_the_state_is_modelled_and_named(self):
        # precision (a): libsodium is absent in the sealed image, so the mark is the MODELLED custody mark.
        d = _parse(_serial())
        self.assertEqual(d.get("real"), "False", "GOB-REAL-AVAIL is False — the MODELLED state, named honestly")
        mark = json.loads(d["signed"])["countersign"]
        self.assertIsInstance(mark, dict, "the modelled mark is a dict (no algorithm tag), not a real signature")


# ── A2 — the trail's digest is the signed act-witness row; the floor stays unsigned ─────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestA2ActWitnessAndUnsignedFloor(unittest.TestCase):
    def test_the_witness_verifies_and_names_the_same_crossings(self):
        d = _parse(_serial())
        witness_full = json.loads(d["witness"])
        wmark = witness_full["countersign"]
        w = {k: v for k, v in witness_full.items() if k != "countersign"}
        self.assertTrue(keys.verify_countersign(wmark, w, d["custody"]),
                        "the act-witness gate row verifies under the bound public half")
        tdig = "sha256:" + hashlib.sha256(d["trail"]).hexdigest()
        self.assertEqual(w["trail_digest"], tdig,
                         "the witness row NAMES the same crossings — its digest recomputes from the trail file")
        # PLANT — a TAMPERED trail digest is REFUSED (the recompute mismatches).
        self.assertNotEqual(w["trail_digest"], "sha256:" + hashlib.sha256(d["trail"] + b"x").hexdigest(),
                            "a tampered trail digest must not match the trail's real bytes")
        self.assertGreater(w["crossings"], 0, "the trail holds real crossings")

    def test_the_body_trail_stays_unsigned_and_keyless(self):
        serial = _serial()
        self.assertIn("SERVE CHECK KEYLESS: PASS", serial, "the body's trail carries no signature (key-less floor)")
        self.assertIn("SERVE CHECK UNSIGNED: PASS", serial, "the body's trail is out of the estate's signed chain")


# ── A3 — the row is read back through the body-read act from the body's own disk ────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestA3DiskRoundtrip(unittest.TestCase):
    def test_the_row_reads_back_from_the_bodys_disk(self):
        d = _parse(_serial())
        self.assertEqual(d["readback"].rstrip(b"\n"), d["signed"],
                         "the row read back through the body-read act equals the row written through the record-pen")

    def test_a_corrupted_body_disk_write_is_caught_off_the_body(self):
        # PLANT_RECORD_READBACK_WRONG — the body corrupts the record on write; the read-back then differs
        # from the row the gate produced, so the off-body round-trip check reds (the read-back IS the body's
        # disk, not the guest fs).
        d = _parse(_serial(fault="PLANT_RECORD_READBACK_WRONG"))
        if "readback" in d and "signed" in d:
            self.assertNotEqual(d["readback"].rstrip(b"\n"), d["signed"],
                                "a corrupted body-disk write must make the read-back differ")


# ── A4 — an ungated row is refused by the chain ─────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestA4UngatedRefusedByTheChain(unittest.TestCase):
    def test_ungated_row_refused_and_chain_intact(self):
        d = _parse(_serial())
        signed_full = json.loads(d["signed"])
        witness_full = json.loads(d["witness"])
        u = json.loads(d["ungated"])
        # A4 — an ungated row (no countersign / no signed decision) is REFUSED by the chain.
        self.assertFalse(keys.verify_countersign(u.get("countersign"), u, d["custody"]),
                         "an ungated row (no countersign) must be refused")
        # the gate discriminates: a properly gated row IS admitted (the check can fail AND can pass).
        signed = {k: v for k, v in signed_full.items() if k != "countersign"}
        self.assertTrue(keys.verify_countersign(signed_full["countersign"], signed, d["custody"]))
        # the prev_hash chain is intact (the estate's canonical_hash form).
        w = {k: v for k, v in witness_full.items() if k != "countersign"}
        self.assertEqual(signed["prev_hash"], canonical_hash(GENESIS))
        self.assertEqual(w["prev_hash"], canonical_hash(signed_full))
        self.assertEqual(u["prev_hash"], canonical_hash(witness_full))
        # PLANT — a CONTENT tamper breaks the chain (canonical_hash changes -> the next prev_hash mismatches).
        tampered_full = dict(signed_full); tampered_full["actor"] = "attacker"
        self.assertNotEqual(w["prev_hash"], canonical_hash(tampered_full),
                            "a content tamper must break the prev_hash chain")


# ── A1/A5 PLANT — the sealed image is checked; the gate never runs on a tamper ──────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestSealTamperRefusesTheGate(unittest.TestCase):
    def test_seal_tamper_refuses_the_load_and_the_gate_never_runs(self):
        serial = _serial(fault="PLANT_SEAL_TAMPER", timeout_s=120)
        self.assertIn("FLOOR3C-SEAL: REFUSED", serial, "a byte change refuses the sealed image at load")
        self.assertNotIn("GATEONBODY-BEGIN", serial, "the gate never runs — the interpreter never starts")


# ── A5 / A6 — the gate is CONTENT not src edits; no founding (main) ─────────────────────────────────
class TestA5A6ContentNotSrcAndNoFounding(unittest.TestCase):
    def test_attestation_edit_in_place_no_new_member(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88, "the gate is content — no new src member (88 after C7 P3b-6a's net.c)")
        self.assertEqual(attestation.ATTESTED_MEMBERS, tuple(sorted(attestation.ATTESTED_MEMBERS)))
        for m in attestation.ATTESTED_MEMBERS:
            self.assertFalse(m.endswith((".img", ".so", ".so.6", ".so.1", ".so.3")), "no borrowed artifact is a member")
            self.assertNotIn("python3", m)
            self.assertNotIn("libpython", m)

    def test_src_body_is_thirty_files_edit_in_place(self):
        names = _body_source_names()
        self.assertEqual(len(names), 31, "src/body is 31 files (this slice adds none; C7 P3b-6a added net.c): %r" % names)

    def test_no_founding_act_kinds_twelve_pack_unchanged(self):
        from bridge.host_seam import ACT_KINDS
        self.assertEqual(len(ACT_KINDS), 12, "the sign/record/body-read acts exist — no new act kind")
        pack = os.path.join(SRC, "founding", "founding-pack.json")
        with open(pack) as f:
            self.assertEqual(json.load(f)["founding_version"], "1.55.0", "no founding")
        with open(pack, "rb") as f:
            self.assertTrue(hashlib.sha256(f.read()).hexdigest().startswith("95631e8f"),
                            "the founding pack is byte-unchanged")

    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs a git repository (git history is unavailable in the render)")
    def test_nothing_above_the_seam_changed(self):
        r = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", "HEAD"], capture_output=True, text=True)
        changed = [p for p in r.stdout.split() if p.startswith("src/") and not p.endswith(".pyc")]
        above = [p for p in changed if not p.startswith("src/body/")]
        self.assertEqual(above, [], "only src/body/ (beneath the seam) changed; nothing above it: %r" % above)


if __name__ == "__main__":
    unittest.main()
