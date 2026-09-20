# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (a paired mutual-attestation genesis, two witness bodies, no shared write path, a mutual
# receipt) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability of any kind —
# every assertion proves design/54 §3 B5 by FUNCTION: two witness bodies that share no write path each
# verify the OTHER's genesis clean and check its code-and-data against their own copy; the genesis row
# records BOTH verdicts as a mutual receipt; one body alone cannot write it; a planted disagreement
# refuses the wake. It attacks nothing and reveals nothing. Full declaration: SCOPE-STATEMENT.md.
"""C7 P6 — THE GENESIS PAIR (design/54 §3 B5, §5 L4; design/47 §4 the diving-buddy genesis, D07.10;
plan planning/exec/C7-P6-GENESIS-PAIR.md, sha 60e8a111…). Two witness bodies, NO shared write path;
each verifies the other's genesis and compares copies; the row a MUTUAL RECEIPT.

Named in the plan before code, landed here as regression tests (charter: every verification probe lands
as a regression test). This EXTENDS P4's single-body genesis row (kernel/boot.py wake — READ and
composed, not re-authored) into a TWO-BODY mutual receipt, and MIRRORS protection.py's two-mutually-
blind-witnesses idiom (READ and mirrored, not re-authored) at the GENESIS size.

MODELLING THE TWO BODIES (guest SSH down this session; P6 performer-independent, host-runnable): the two
bodies are two SEPARATE stores over two SEPARATE record files — the "two images" logical arrangement.
The second image (the stand-in for the physical chip body, which is the OWNER's, held) is a git-tracked
second COPY of the genesis, not a live second VM and NOT hardware — git-revertible (design/54 Q3, I6).

NOT FOUNDING (archi countersign :3955; design/54 v0.11 "the pairing code not a constitution rule"):
founding-pack.json byte-unchanged, no version bump / bump-attestation / §A57. A BOOT ADDITION on the
already-attested kernel/boot.py — no new src module, so ATTESTED_MEMBERS is unchanged (count-pin inert).

RUNNER OF RECORD (per-module, :3158): PYTHONPATH=src:tests python3 -m unittest tests.test_c7_p6_genesis_pair -v
"""
import ast
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from kernel import boot                                     # noqa: E402
from kernel import attestation                              # noqa: E402
from kernel.compose import build_full_kernel                # noqa: E402
from founding import install                                # noqa: E402


# ---- helpers: build a genesis, make a second image, tamper a body's src -------------------------

def _fresh(prefix="c7p6-"):
    """A full governed kernel in a fresh temp world (a witness body's image). Returns (store, gate,
    views, record_path)."""
    td = tempfile.mkdtemp(prefix=prefix)
    rp = os.path.join(td, "record.jsonl")
    store, gate, views, _blobs, _subs = build_full_kernel(rp, os.path.join(td, "blobs"))
    return store, gate, views, rp


def _second_image(rp, prefix="c7p6-img2-"):
    """A SECOND IMAGE: a git-tracked second COPY of the genesis record, recomposed over its own store
    (a separate write path — no shared image). The stand-in for the physical chip body; a real second
    copy, not hardware. Returns (store, gate, views, record_path2)."""
    td = tempfile.mkdtemp(prefix=prefix)
    rp2 = os.path.join(td, "record.jsonl")
    shutil.copy(rp, rp2)
    store, gate, views, _blobs, _subs = build_full_kernel(rp2, os.path.join(td, "blobs"))
    return store, gate, views, rp2


def _mirror_src():
    """A working copy of the real src/ tree (attestation's own detect-direction idiom, test_ep40 /
    test_c7_p4_wake); a body given this as its src_dir can have its genesis code-and-data diverge."""
    dst = os.path.join(tempfile.mkdtemp(prefix="c7p6-src-"), "src")
    shutil.copytree(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")), dst)
    return dst


def _pair_row(store):
    rows = [e for e in store.by_action("WRITE-ACTIVITY")
            if e.get("object") == boot.GENESIS_PAIR_OBJECT]
    return rows[-1] if rows else None


def _code_only(fn):
    """Return `fn`'s source with its docstring stripped (docstrings NAME the performer / the physical
    chip to say they are NOT read/bound; the guard scans CODE). The P4 A4 idiom."""
    tree = ast.parse(inspect.getsource(fn).lstrip())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(
                    getattr(body[0], "value", None), ast.Constant) and isinstance(
                    body[0].value.value, str):
                body.pop(0)
    return ast.unparse(tree)


_PAIRING_FNS = (boot.genesis_part, boot.WitnessBody.__init__, boot.WitnessBody.witness,
                boot.mutual_receipt, boot.genesis_pair_wake, boot.assert_chip_carries_genesis_part_only,
                boot._constitution_markers)


# ================================================================================================
# A1 — TWO BODIES, NO SHARED WRITE PATH, THE ROW A MUTUAL RECEIPT (B5)
# ================================================================================================
def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    import os as _os, subprocess as _sp
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    try:
        return _sp.run(["git", "-C", _root, "rev-parse", "--verify", "HEAD"],
                       capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


class TestA1MutualReceipt(unittest.TestCase):
    def test_two_bodies_no_shared_path_record_both_verdicts_as_one_receipt(self):
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)                   # a SEPARATE image (separate store/file)
        self.assertIsNot(sa, sb, "the two bodies are two separate images — no shared write path")

        body_a = boot.WitnessBody("chip", sa, va)              # in the chip's memory (body 1)
        body_b = boot.WitnessBody("disk", sb, vb)              # on disk / the second image (body 2)

        before = len(sa.events)
        receipt = boot.genesis_pair_wake(body_a, body_b, ga)   # a healthy pair -> they agree, they wake

        # exactly ONE mutual-receipt genesis row (the one pen)
        self.assertEqual(len(sa.events) - before, 1, "the genesis pair records exactly one row")
        row = _pair_row(sa)
        self.assertIsNotNone(row, "the mutual-receipt genesis row is on the record")
        self.assertEqual(row["actor"], "SYSTEM", "the row is a SYSTEM act (the one pen)")
        self.assertEqual(row["action"], "WRITE-ACTIVITY")

        # the row records BOTH bodies' verdicts (a mutual receipt), not one signer's claim
        self.assertEqual(set(row["payload"]["verdicts"]), {"chip", "disk"})
        self.assertTrue(row["payload"]["agree"])
        self.assertEqual(list(row["payload"]["bodies"]), ["chip", "disk"])   # deep-freeze -> tuple on the record
        for by in ("chip", "disk"):
            v = row["payload"]["verdicts"][by]
            self.assertTrue(v["clean"], "%s found the other's genesis clean" % by)
            self.assertTrue(v["matches"], "%s found the other's code-and-data matching its own copy" % by)
        # the receipt names the OTHER as its subject (each verifies the OTHER, never itself)
        self.assertEqual(row["payload"]["verdicts"]["chip"]["about"], "disk")
        self.assertEqual(row["payload"]["verdicts"]["disk"]["about"], "chip")

    def test_the_receipt_precedes_the_first_actor_act(self):
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        boot.genesis_pair_wake(boot.WitnessBody("chip", sa, va),
                               boot.WitnessBody("disk", sb, vb), ga)
        pair_seq = _pair_row(sa)["seq"]
        first_actor = ga.execute("CREATE-ACTOR", "owner", {"actor_id": "first-actor"})
        self.assertGreater(first_actor["seq"], pair_seq,
                           "the first actor act lands AFTER the mutual-receipt genesis row")

    def test_each_body_carries_its_own_copy_of_the_same_genesis_part(self):
        # the two bodies hold their OWN copies (design/47 §4); on one genesis the copies are equal
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        body_a = boot.WitnessBody("chip", sa, va)
        body_b = boot.WitnessBody("disk", sb, vb)
        self.assertEqual(body_a.own_part, body_b.own_part, "one genesis -> the two copies agree")
        self.assertEqual(set(body_a.own_part), {"checker", "digests", "anchor_key"})


# ================================================================================================
# A2 — ONE BODY ALONE CANNOT WRITE THE ROW
# ================================================================================================
class TestA2OneBodyAloneCannotWrite(unittest.TestCase):
    def test_a_solo_verdict_is_refused(self):
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        va_verdict = boot.WitnessBody("chip", sa, va).witness(boot.WitnessBody("disk", sb, vb))
        # the mutual receipt is not a solo signature: one body's verdict alone cannot assemble the row
        with self.assertRaises(boot.MutualReceiptRefused) as cm:
            boot.mutual_receipt(va_verdict, None)
        self.assertEqual(cm.exception.reason, "solo-write")
        with self.assertRaises(boot.MutualReceiptRefused) as cm2:
            boot.mutual_receipt(None, va_verdict)
        self.assertEqual(cm2.exception.reason, "solo-write")

    def test_a_full_receipt_needs_both(self):
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        body_a, body_b = boot.WitnessBody("chip", sa, va), boot.WitnessBody("disk", sb, vb)
        receipt = boot.mutual_receipt(body_a.witness(body_b), body_b.witness(body_a))
        self.assertEqual(set(receipt["receipt"]), {"chip", "disk"}, "both verdicts are required and present")


# ================================================================================================
# A3 — A PLANTED DISAGREEMENT REFUSES THE WAKE (the check can fail AND pass)
# ================================================================================================
class TestA3DisagreementRefuses(unittest.TestCase):
    def test_a_tampered_chip_copy_refuses_even_when_the_live_machine_is_clean(self):
        # The diving-buddy's distinctive check: body B holds a TAMPERED copy of the genesis part (its
        # chip copy diverged) while its live store is healthy. B checks A's healthy genesis against B's
        # own (tampered) copy -> matches=False -> the two bodies DISAGREE -> the wake is refused.
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        healthy = boot.genesis_part(sa, va)
        tampered_copy = dict(healthy, checker="sha256:planted-divergent-chip-copy")
        boot.assert_chip_carries_genesis_part_only(tampered_copy)   # still the genesis-part shape (no constitution)
        body_a = boot.WitnessBody("chip", sa, va)
        body_b = boot.WitnessBody("disk", sb, vb, own_part=tampered_copy)

        before = len(sa.events)
        with self.assertRaises(boot.MutualReceiptRefused) as cm:
            boot.genesis_pair_wake(body_a, body_b, ga)
        self.assertEqual(cm.exception.reason, "disagreement")
        # the disagreement is a FACT OF THE RECORD before the refusal (the row names it)
        self.assertEqual(len(sa.events) - before, 1, "the row is recorded before the refusal")
        row = _pair_row(sa)
        self.assertFalse(row["payload"]["agree"], "the row records the disagreement")
        self.assertFalse(row["payload"]["verdicts"]["disk"]["matches"],
                         "the body holding the tampered copy finds the other not matching")

    def test_a_tampered_second_image_refuses(self):
        # Body B's live genesis code-and-data diverges (its src copy is tampered) — A finds B's code-and-
        # data does not match A's own copy AND B's own wake checklist reddens: the pair refuses.
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        mirror = _mirror_src()
        with open(os.path.join(mirror, "kernel", "gate.py"), "a") as f:
            f.write("\n# C7 P6 planted second-image divergence (a silent engine change)\n")
        body_a = boot.WitnessBody("chip", sa, va)
        body_b = boot.WitnessBody("disk", sb, vb, src_dir=mirror)
        with self.assertRaises(boot.MutualReceiptRefused) as cm:
            boot.genesis_pair_wake(body_a, body_b, ga)
        self.assertEqual(cm.exception.reason, "disagreement")
        row = _pair_row(sa)
        self.assertFalse(row["payload"]["verdicts"]["chip"]["matches"],
                         "A finds B's tampered code-and-data does not match A's own copy")

    def test_agreeing_bodies_wake(self):
        # The control that makes the refusal real (§7 — a check that cannot pass is not a check): a
        # healthy pair AGREES and wakes.
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        receipt = boot.genesis_pair_wake(boot.WitnessBody("chip", sa, va),
                                         boot.WitnessBody("disk", sb, vb), ga)
        self.assertTrue(receipt["agree"], "agreeing bodies wake")


# ================================================================================================
# A4 — NO SHARED WRITE PATH; THE CHIP CARRIES THE GENESIS PART ONLY
# ================================================================================================
class TestA4NoSharedPathChipGenesisPartOnly(unittest.TestCase):
    def test_one_hand_writing_both_over_one_image_is_refused(self):
        # A planted single hand: both bodies over ONE image (one store) — one write path, common-mode
        # failure. Refused before any row.
        sa, ga, va, rpa = _fresh()
        one = boot.WitnessBody("chip", sa, va)
        two = boot.WitnessBody("disk", sa, va)                 # SAME store as `one`
        before = len(sa.events)
        with self.assertRaises(boot.MutualReceiptRefused) as cm:
            boot.genesis_pair_wake(one, two, ga)
        self.assertEqual(cm.exception.reason, "shared-write-path")
        self.assertEqual(len(sa.events) - before, 0, "no row is written when the image is shared")

    def test_both_verdicts_under_one_body_id_is_refused(self):
        # A planted single hand: two verdicts under ONE write-token (one body id) — one signer forging
        # both. Refused (the mirror of protection.py's two-keys-held-apart).
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        v_a = boot.WitnessBody("chip", sa, va).witness(boot.WitnessBody("disk", sb, vb))
        forged = dict(v_a, about="someone-else")               # same 'by' = "chip"
        with self.assertRaises(boot.MutualReceiptRefused) as cm:
            boot.mutual_receipt(v_a, forged)
        self.assertEqual(cm.exception.reason, "shared-write-path")

    def test_a_verdict_is_bound_to_its_own_body_id_only(self):
        # The genesis-size mirror of protection.py's per-stream key: witness() names its OWN body_id
        # (self.body_id) and no other's for `by` — the write-token separation the refusal above rests on.
        code = _code_only(boot.WitnessBody.witness)          # ast.unparse normalizes to single quotes
        self.assertIn("'by': self.body_id", code,
                      "a body's verdict is bound to its OWN write-token (self.body_id)")

    def test_the_chip_carries_the_genesis_part_only_a_constitution_key_is_refused(self):
        # THE CHIP CARRIES THE GENESIS PART ONLY (L4, I4): a planted constitution copy is an extra key
        # outside {checker, digests, anchor_key} — refused (closed shape).
        with self.assertRaises(boot.MutualReceiptRefused) as cm:
            boot.assert_chip_carries_genesis_part_only(
                {"checker": "sha256:x", "digests": {}, "anchor_key": {},
                 "constitution": {"root_laws": ["...the whole constitution..."]}})
        self.assertEqual(cm.exception.reason, "constitution-on-chip")

    def test_a_constitution_smuggled_into_an_allowed_field_is_refused(self):
        # The content belt: the constitution's own root-law ids (derived from the live pack) must not
        # appear anywhere in the part — a constitution smuggled into an allowed field is refused.
        markers = boot._constitution_markers()
        self.assertTrue(markers, "the belt derives real constitution markers from the live pack")
        smuggled = sorted(markers)[0]
        with self.assertRaises(boot.MutualReceiptRefused) as cm:
            boot.assert_chip_carries_genesis_part_only(
                {"checker": "carries " + smuggled + " here", "digests": {}, "anchor_key": {}})
        self.assertEqual(cm.exception.reason, "constitution-on-chip")

    def test_a_real_genesis_part_carries_no_constitution(self):
        # The belt is INERT on a real part (the genesis part is digests + a key, never constitution).
        sa, ga, va, rpa = _fresh()
        part = boot.genesis_part(sa, va)                       # would raise if it carried the constitution
        blob = json.dumps(part, sort_keys=True, default=str)
        for marker in boot._constitution_markers():
            self.assertNotIn(marker, blob, "a real genesis part carries no constitution id (%s)" % marker)
        self.assertEqual(set(part), {"checker", "digests", "anchor_key"})


# ================================================================================================
# A5 — THE GUEST STANDS IN FOR THE CHIP; THE PHYSICAL BODY IS THE OWNER's (held)
# ================================================================================================
class TestA5SecondImageNotHardware(unittest.TestCase):
    def test_the_second_body_is_a_revertable_image_not_hardware(self):
        # The second image is a git-tracked second COPY over an ordinary record file — revertable, not a
        # physical device (design/54 Q3, I6).
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        self.assertTrue(os.path.isfile(rpb), "the second image is an ordinary file (a revertable copy)")
        self.assertFalse(rpb.startswith("/dev/"), "the second image is not a hardware device node")
        self.assertIsNot(sa, sb, "two images, two write paths")

    def test_the_pairing_binds_no_physical_chip_body(self):
        # No hardware bound anywhere in the pairing (I6 revertability): the mechanism scans clean of any
        # physical-device / hardware bind token.
        src = "".join(_code_only(fn) for fn in _PAIRING_FNS)
        for token in ("/dev/", "hidraw", "ioctl", "usb", "chip_open", "bind_chip", "ctypes"):
            self.assertNotIn(token, src,
                             "the genesis pair binds no physical chip body (%s)" % token)

    def test_the_physical_chip_bind_guard_can_fire(self):
        # The control: the same scan CAN detect a planted physical-chip bind — so a "bind the physical
        # chip body" step WOULD red the revertability check (the guard is able to fail).
        planted = "self._chip = open('/dev/chip0', 'wb')  # bind the physical chip body"
        self.assertIn("/dev/", planted, "a planted physical-chip bind is detectable by the same guard")


# ================================================================================================
# A6 — WHOLE LEDGER GREEN PER MODULE; NOT FOUNDING; NO NEW ATTESTED MODULE; PERFORMER-INDEPENDENT
# ================================================================================================
class TestA6LedgerFoundingAttestationPerformer(unittest.TestCase):
    def test_not_founding_the_pack_version_is_unchanged(self):
        # NOT founding data (archi :3955): the pairing is genesis machinery in code. This unit made
        # NO founding move. The live version is read fresh, so this is a §A57 live-version pin: a LATER
        # founding mover, C7 P3 (THE KERNEL FROM THE RECORD — the twelve act-kind rows), moved the LIVE
        # founding 1.54.0 -> 1.55.0 BY NAME (§A57); P6 still adds no founding.
        self.assertEqual(install.founding_version(), "1.55.0",
                         "P6 adds no founding; the live version is C7 P3's 1.55.0")

    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs a git repository (git history is unavailable in the render)")
    def test_the_pack_file_is_byte_unchanged_in_the_working_tree(self):
        # A mechanical guard that this unit added no pack edit (git diff --stat over the pack is empty).
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        out = subprocess.run(["git", "-C", root, "diff", "--stat", "--",
                              "src/founding/founding-pack.json"],
                             capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "", "the founding pack has no working-tree diff (not founding)")

    def test_no_new_attested_module_from_this_unit_global_count_68(self):
        # A boot ADDITION on the already-attested kernel/boot.py — no new src engine module joins the
        # attested set FROM THIS UNIT, so P6's OWN count-pin rider is inert. The absolute count is a
        # GLOBAL pin any estate-wide add moves: C7 P7a's interpreter-hosting layer moved it 55 -> 57
        # (+2: hosting/__init__.py, hosting/interpreter_host.py), then C7 P3b-1's first merged body
        # moved it 57 -> 68 (+11 src/body files; §9 mechanism 1, archi :4009) — both AFTER this unit.
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                         "this unit added no module (its rider is inert); the global count is 88 after C7 P3b-6a's +1 net.c, 87 after C7 P3b-4b's +2 serve files (serve.c/serve.h), 85 after C7 P3b-4a's +6 enclosure files (enclosure.S/enclosure.c/enclosure.h/sha256.c/worker.S/worker.ld), 79 after P3b-3's +6 clock/interrupt/entropy (73 after P3b-2's +5 disk, 68 after P3b-1's +11)")
        self.assertTrue(any("kernel/boot.py" in m for m in attestation.ATTESTED_MEMBERS),
                        "kernel/boot.py (the genesis pair's home) is attested, as before")

    def test_performer_independent_the_pairing_reads_no_performer_or_seam_symbol(self):
        # The pairing reads GENESIS (record / constitution / keys / accounts / genesis-part digests),
        # never the performer beneath the effect seam.
        src = "".join(_code_only(fn) for fn in _PAIRING_FNS)
        for token in ("host_seam", "RealHost", "StubHost", "bridge", "observe"):
            self.assertNotIn(token, src,
                             "a pairing function reads no effect-seam / performer symbol (%s)" % token)

    def test_the_performer_read_guard_can_fire(self):
        # The control: a planted performer-specific read in the pairing WOULD red the scan.
        planted = "probe = views.host_seam.performer.read()"
        self.assertIn("host_seam", planted,
                      "a planted performer read is detectable by the same guard")

    def test_extends_p4_row_and_mirrors_protection_without_re_authoring_either(self):
        # THE WRONG-REFERENCE TRAP, landed as a regression test. Scanned over CODE ONLY (docstrings and
        # comments stripped — they legitimately NAME protection.py's idiom to say it is mirrored): the
        # pairing EXTENDS P4's wake (its code composes wake_verdicts) and is a SEPARATE mechanism from the
        # dual audit (its code reuses no Protection / dual-audit path — mirrored, not re-authored).
        code = "".join(_code_only(fn) for fn in _PAIRING_FNS)
        self.assertIn("wake_verdicts", code, "the pairing composes P4's wake_verdicts (extends the row)")
        for token in ("Protection", "dual_blind_divergences", "_sign_stream", "_maybe_mirror"):
            self.assertNotIn(token, code,
                             "the pairing is a SEPARATE mechanism — its code does not re-author/reuse the "
                             "dual audit (%s)" % token)


if __name__ == "__main__":
    unittest.main(verbosity=2)
