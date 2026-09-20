# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (merkle inclusion proof, cross-body verdict, disclosure level, graded admission,
# handshake, separation of powers). NON-GOAL: no offensive capability of any kind — every assertion
# proves B3/I10/I12/I8/I16/B12 by function: one leaf is spot-verifiable under a root, two bodies read
# each other's PRESENTED identity at a disclosure level and grade admission by which checks passed, a
# crossing carries exactly the leaves its level names, and a body meeting another cannot at the
# receipt claim a stage another holds for one scope nor put all three powers in one hand. Full
# declaration: SCOPE-STATEMENT.md.
"""C6 P11 — THE HANDSHAKE, THREE CHECKS, MUTUAL, CROSS-BODY (design/52 B3:52, I10:82, I12:84, I8:80,
I16:88, B12:61; the :3698 amendment; plan planning/exec/P11-HANDSHAKE-THREE-CHECKS-BUILD.md).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). NO FOUNDING: no new op/law/check kind and no pack edit. P11's NEW code is
N1 (the Merkle inclusion/audit-path primitive on the EXISTING bridge/merkle.py — a function, not a
module) and N3 (the cross-body graded verdict EXTENDING bridge/checkpoint.py — no new module), plus
the :3698 amendment on kernel/border.py's receipt act path. It CONSUMES P8 (admitted_level DERIVED at
read, the RECEIPT checks/disclosure_level fields) and P6 (views.refuse_double_claim,
views.refuse_separation_of_powers — READ and INVOKED, never re-authored).

  A1 (N1)          ONE LEAF PROVEN AGAINST A ROOT — an audit path proves one leaf's inclusion; a leaf
                   NOT in the tree fails; the path folds to the same value merkle_root gives.
  A2 (B3/I10/N3)   THREE CHECKS, CROSS-BODY, GRADED, RECORDED — WHO / BODY / MEMORY-SANE over the
                   OTHER body's PRESENTATION at a disclosure level; admission GRADED via admitted_level
                   (never refused outright when any passes); the recorded row names the passed set; a
                   planted failure lowers the admitted level and names the failed check.
  A3 (I12)         LEAST DISCLOSURE BY LAW — a crossing carries exactly the leaves the level names; a
                   planted over-disclosure and a planted withheld-required leaf each red (recorded).
  A4 (:3698/I8/I16) THE RECEIPT REFUSES ON THE ACT PATH — a double-claimed (stage, scope) or an
                   all-three-powers concentration at the receipt is refused BY NAME and RECORDED; a
                   disjoint claim / a single holder / any two powers pass.
  A5 (B12 rides)   A PREDICATE PROVEN WITHOUT THE VALUE — a predicate over the identity tree verifies
                   without disclosing the value; a planted false predicate fails. CAP: full
                   unlinkability of per-peer roots is NOT built (its cost stated).
  A6               NO FOUNDING — pack byte-unchanged; OP_CHECKS 19, ATTESTED_MEMBERS 54 (N1 a function,
                   N3 extends an existing module — the rider is inert).

Crypto is ERA-AWARE (KEY-MATERIAL-REAL's discipline): tests that need a real signature or seal branch
on `crypto.real_available()` — present, the check verifies real material; absent, WHO/BODY are REFUSED
(never faked, N10) and MEMORY-SANE (pure) carries the graded proof. The grading rule itself is proven
in BOTH eras through admitted_level (pure).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from bridge import merkle                                                        # noqa: E402
from bridge import checkpoint                                                    # noqa: E402
from bridge.merkle import SCHEME_CHILDREN_ONLY, SCHEME_DIR_METADATA             # noqa: E402
from kernel import border, canonical, crypto, attestation                       # noqa: E402
from kernel.compose import build_full_kernel                                     # noqa: E402
from kernel.errors import OpError                                               # noqa: E402
from kernel.opdefs import OP_CHECKS                                             # noqa: E402
from kernel.signer import SigningKeyStore                                       # noqa: E402
from kernel import views as views_module                                        # noqa: E402

_REPO = os.path.join(os.path.dirname(__file__), "..")
SENDER_SEED = bytes(range(1, 33))
OTHER_SEED = bytes([9]) * 32


def _sample_tree():
    """A small flat tree-state (the snapshot() shape): file leaves under nested dirs, plus explicit
    dir entries so scheme-2 metadata folds."""
    return {
        "a/b/file1": {"type": "file", "mode": 33188, "nlink": 1, "content": "one"},
        "a/b/file2": {"type": "file", "mode": 33188, "nlink": 1, "content": "two"},
        "a/c/file3": {"type": "file", "mode": 33188, "nlink": 1, "content": "three"},
        "top": {"type": "file", "mode": 33188, "nlink": 1, "content": "t"},
        "a/b": {"type": "dir", "mode": 16877, "nlink": 2},
        "a/c": {"type": "dir", "mode": 16877, "nlink": 2},
        "a": {"type": "dir", "mode": 16877, "nlink": 3},
    }


def _body(prefix, entity, actor_class="ai"):
    """One MACHINE — its own record (data dir), gate and views, `entity` established as an account."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": entity, "actor_class": actor_class})
    return d, store, gate, views


def _hold_stage(gate, holder, rule_id, stage, scope, minter="owner"):
    """A stage-holding CLAIM (P6's idiom, reused): a LIVE CREATE-RULE self-declaring the stage on the
    EXISTING accepted params — no founding, no new row field."""
    return gate.execute("CREATE-RULE", minter,
                        {"rule_id": rule_id, "policy_key": "held_stage",
                         "value": stage, "scope": scope, "text": holder})


# =================================================================================================
# A1 (N1) — THE INCLUSION / AUDIT-PATH PRIMITIVE
# =================================================================================================

def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    import os as _os, subprocess as _sp
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    try:
        return _sp.run(["git", "-C", _root, "rev-parse", "--verify", "HEAD"],
                       capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


class TestInclusionPrimitive(unittest.TestCase):
    def test_one_leaf_proven_against_a_root(self):
        """N1: an audit path for one leaf verifies against merkle_root(tree) — under BOTH schemes."""
        tree = _sample_tree()
        for scheme in (SCHEME_CHILDREN_ONLY, SCHEME_DIR_METADATA):
            root = merkle.merkle_root(tree, scheme)
            for leaf in ("a/b/file1", "a/b/file2", "a/c/file3", "top"):
                proof = merkle.inclusion_proof(tree, leaf, scheme)
                self.assertIsNotNone(proof, leaf)
                self.assertEqual(proof["leaf"], leaf)
                self.assertTrue(merkle.verify_inclusion(proof, root, scheme),
                                f"{leaf} @ scheme {scheme}")

    def test_a_leaf_not_in_the_tree_fails(self):
        """N1 — THE CHECK CAN FAIL: a relpath that names no file leaf yields no proof (None), and a
        None proof does not verify. A directory path yields None (a directory is not one leaf)."""
        tree = _sample_tree()
        self.assertIsNone(merkle.inclusion_proof(tree, "a/b/missing"))     # absent leaf
        self.assertIsNone(merkle.inclusion_proof(tree, "nope"))            # absent top-level
        self.assertIsNone(merkle.inclusion_proof(tree, "a/b"))            # a directory, not one leaf
        self.assertIsNone(merkle.inclusion_proof(tree, ""))               # empty path
        self.assertFalse(merkle.verify_inclusion(None, merkle.merkle_root(tree)))
        self.assertFalse(merkle.verify_inclusion({"path": None}, "sha256:x"))

    def test_the_path_length_and_root_match_merkle_root(self):
        """N1: the path length equals the leaf's DEPTH, and the audit path folds to exactly the value
        the EXISTING merkle_root returns for the same tree (N1 rides the one fold, never a second)."""
        tree = _sample_tree()
        root = merkle.merkle_root(tree)
        deep = merkle.inclusion_proof(tree, "a/b/file1")
        self.assertEqual(len(deep["path"]), 3)                            # a/ b/ file1 -> depth 3
        shallow = merkle.inclusion_proof(tree, "top")
        self.assertEqual(len(shallow["path"]), 1)                         # top -> depth 1
        # the leaf hash the proof carries IS the merkle_tree's leaf hash (the one fold, reused)
        node = merkle.merkle_tree(tree)
        self.assertEqual(deep["leaf_hash"], node["children"]["a"]["children"]["b"]["children"]["file1"]["hash"])

    def test_a_tampered_proof_reds(self):
        """N1 — THE CHECK CAN FAIL: a wrong root, an altered sibling hash, or a wrong scheme all fail."""
        tree = _sample_tree()
        root = merkle.merkle_root(tree)
        proof = merkle.inclusion_proof(tree, "a/b/file1")
        self.assertFalse(merkle.verify_inclusion(proof, "sha256:" + "0" * 64))     # wrong root
        tampered = merkle.inclusion_proof(tree, "a/b/file1")
        tampered["path"][0]["siblings"][0][1] = "sha256:" + "1" * 64               # altered sibling
        self.assertFalse(merkle.verify_inclusion(tampered, root))
        # a proof made under scheme 2 folded under scheme 1 does not reproduce scheme 2's root
        p2 = merkle.inclusion_proof(tree, "a/b/file1", SCHEME_DIR_METADATA)
        self.assertFalse(merkle.verify_inclusion(p2, root, SCHEME_CHILDREN_ONLY))


# =================================================================================================
# A2 (B3, I10, N3) — THE THREE-CHECK, CROSS-BODY, GRADED VERDICT
# =================================================================================================

class TestGradedAdmissionRule(unittest.TestCase):
    """The grading rule itself — PURE (admitted_level, P8, consumed), proven in BOTH eras."""

    def test_admission_is_graded_never_binary_and_names_the_passed_set(self):
        """I10 / SPIKE-3 §3d: admission is graded, NEVER refused outright when ANY check passes. The
        admitted level is the presented level bounded by the confidence the passed checks support."""
        self.assertEqual(border.admitted_level({"who": True, "body": True, "memory_sane": True}, "FULL"), "FULL")
        self.assertEqual(border.admitted_level({"who": True, "body": True, "memory_sane": False}, "FULL"), "SHELLS")
        self.assertEqual(border.admitted_level({"who": True, "body": False, "memory_sane": False}, "FULL"), "HASHES-ONLY")
        self.assertIsNone(border.admitted_level({"who": False, "body": False, "memory_sane": False}, "FULL"))

    def test_a_planted_failure_lowers_the_admitted_level(self):
        """SPIKE-3 §3d: a planted failure of one check drops the admitted level (three passing -> FULL;
        planting one failure -> SHELLS). The presented ceiling still bounds it (FULL checks at
        HASHES-ONLY admit only HASHES-ONLY)."""
        self.assertEqual(border.admitted_level({"who": True, "body": True, "memory_sane": True}, "FULL"), "FULL")
        self.assertEqual(border.admitted_level({"who": False, "body": True, "memory_sane": True}, "FULL"), "SHELLS")
        self.assertEqual(border.admitted_level({"who": True, "body": True, "memory_sane": True}, "HASHES-ONLY"), "HASHES-ONLY")


class TestCrossBodyVerdict(unittest.TestCase):
    def _presentation(self, level="HASHES-ONLY"):
        """A benign local counterpart's PRESENTATION: a body-name, a merkle root + one inclusion
        proof (MEMORY-SANE, pure), and — filled in per era — the WHO/BODY material."""
        tree = _sample_tree()
        root = merkle.merkle_root(tree)
        proof = merkle.inclusion_proof(tree, "a/b/file1")
        return {"disclosure_level": level, "from_body": {"key": "k", "genesis": "g"},
                "merkle_root": root, "inclusion": proof, "founding_version": "1.51.0"}, tree, root

    def test_memory_sane_is_a_cross_body_spot_check_both_eras(self):
        """N3 / MEMORY-SANE: over a PRESENTED root + one inclusion proof (N1 at HASHES-ONLY), the
        verdict spot-verifies a leaf WITHOUT the whole tree crossing — PURE, so it runs in both eras.
        A planted bad proof reddens memory_sane and drops the admitted level to None."""
        pres, _tree, _root = self._presentation()
        v = checkpoint.handshake_verdict(pres, verifier_founding_version="1.51.0")
        self.assertIs(v["checks"]["memory_sane"], True)
        self.assertIn("memory_sane", v["passed"])
        self.assertEqual(v["admitted_level"], "HASHES-ONLY")             # one check -> HASHES-ONLY
        bad = dict(pres); bad["merkle_root"] = "sha256:" + "0" * 64      # planted wrong root
        vb = checkpoint.handshake_verdict(bad, "1.51.0")
        self.assertIs(vb["checks"]["memory_sane"], False)               # THE CHECK CAN FAIL
        self.assertIn("memory_sane", vb["failed"])
        self.assertIsNone(vb["admitted_level"])                         # nothing passes -> nothing admitted

    def test_who_and_body_are_real_or_refused(self):
        """N10 real-or-refused: with the library ABSENT, WHO and BODY REFUSE (None in the verdict,
        never a modelled pass — the underlying primitive raises LibraryAbsent); with it PRESENT, a
        correct signature/seal verifies and admission reaches FULL, a planted failure lowers it."""
        pres, _tree, _root = self._presentation(level="FULL")
        if not crypto.real_available():
            # the primitives themselves refuse (the discipline), and the verdict marks None, never pass
            fb = border.from_body_name("ed25519-pub:modelled", "g")
            with self.assertRaises(crypto.LibraryAbsent):
                border.verify_from_sig(fb, "ed25519-sig:x", "sha256:" + "a" * 64)
            pres["from_body"] = fb
            pres["from_sig"] = "ed25519-sig:x"
            pres["content_hash"] = "sha256:" + "a" * 64
            pres["attested"] = {"members": {"m": "d"}, "set_digest": canonical.canonical_hash({"m": "d"})}
            pres["seal"] = "ed25519-seal:x"
            v = checkpoint.handshake_verdict(pres, "1.51.0")
            self.assertIsNone(v["checks"]["who"])                       # REFUSED, never faked
            self.assertIsNone(v["checks"]["body"])
            self.assertIs(v["checks"]["memory_sane"], True)            # the pure check still carries
            self.assertEqual(v["admitted_level"], "HASHES-ONLY")      # bounded by the one passing check
            return
        # PRESENT era: real signature + real seal -> all three pass -> admitted FULL
        pub = crypto.public_from_seed(SENDER_SEED)
        signer = SigningKeyStore(); custody = signer.seal(SENDER_SEED)
        ch = "sha256:" + "a" * 64
        attested = {"members": {"m": "d"}, "set_digest": canonical.canonical_hash({"m": "d"})}
        pres["from_body"] = border.from_body_name(pub, "g")
        pres["content_hash"] = ch
        pres["from_sig"] = signer.sign(custody, ch.encode())
        pres["attested"] = attested
        pres["seal"] = attestation.attestation_seal(attested, signer, custody)
        v = checkpoint.handshake_verdict(pres, "1.51.0")
        self.assertEqual(v["checks"], {"who": True, "body": True, "memory_sane": True})
        self.assertEqual(v["admitted_level"], "FULL")
        # planted WHO failure: a signature over a DIFFERENT crossing -> who False -> admitted SHELLS
        bad = dict(pres); bad["from_sig"] = signer.sign(custody, ("sha256:" + "b" * 64).encode())
        vb = checkpoint.handshake_verdict(bad, "1.51.0")
        self.assertIs(vb["checks"]["who"], False)
        self.assertIn("who", vb["failed"])
        self.assertEqual(vb["admitted_level"], "SHELLS")               # two of three -> lowered
        # planted BODY failure (RW-FORGE): a member changed after sealing -> set_digest mismatch
        forged = dict(pres); forged["attested"] = {"members": {"m": "TAMPERED"},
                                                   "set_digest": attested["set_digest"]}
        vf = checkpoint.handshake_verdict(forged, "1.51.0")
        self.assertIs(vf["checks"]["body"], False)

    def test_the_recorded_row_names_the_passed_set_and_admitted_is_derived_not_stored(self):
        """A2 / I10: the graded verdict is RECORDED on the RECEIPT (checks + disclosure_level, P8's
        fields); admitted_level is DERIVED AT READ (never a stored field, stop (d)). The recorded row
        NAMES which checks passed."""
        _d, _store, gate, _views = _body("p11-a2-", "gov")
        checks = {"who": True, "body": True, "memory_sane": False}
        rec = border.record_receipt(gate, "sha256:" + "a" * 64, {"key": "k", "genesis": "g"}, "sig",
                                    checks=checks, disclosure_level="FULL")
        # the row NAMES the passed set (who/body/memory_sane, each pass|fail)
        self.assertEqual(dict(rec["payload"]["checks"]), checks)
        self.assertEqual(rec["payload"]["disclosure_level"], "FULL")
        self.assertNotIn("admitted_level", rec["payload"])             # NEVER stored (I10; stop d)
        # DERIVED at read from the recorded receipt (dict() converts the stored mappingproxy, P8's idiom)
        self.assertEqual(border.admitted_level(dict(rec["payload"]["checks"]),
                                               rec["payload"]["disclosure_level"]), "SHELLS")

    def test_a_bare_row_receipt_carries_the_three_fields_as_null(self):
        """A6 / P8: a bare row receipt carries the three graded fields as NULL — P8's design
        ('byte-unchanged from before P8 apart from three null fields the honest record carries'). No
        graded verdict was recorded, so admitted_level over the null checks is None (nothing admitted)."""
        _d, _store, gate, _views = _body("p11-a2b-", "gov")
        rec = border.record_receipt(gate, "sha256:" + "c" * 64, {"key": "k"}, "sig")
        self.assertIsNone(rec["payload"]["checks"])
        self.assertIsNone(rec["payload"]["disclosure_level"])
        self.assertIsNone(rec["payload"]["address_form"])
        self.assertIsNone(border.admitted_level(rec["payload"]["checks"], rec["payload"]["disclosure_level"]))


# =================================================================================================
# A3 (I12) — LEAST DISCLOSURE BY LAW
# =================================================================================================

class TestLeastDisclosure(unittest.TestCase):
    def test_a_crossing_carries_exactly_the_leaves_the_level_names(self):
        """I12: the disclosed leaf names must equal EXACTLY the level's law-named set — no over, no
        withheld (the pure census passes)."""
        for level in ("HASHES-ONLY", "SHELLS", "FULL"):
            required = list(border.DISCLOSURE_LEAVES[level])
            conflicts = border.least_disclosure_conflicts(required, level)
            self.assertEqual(conflicts, {"over": [], "withheld": []}, level)

    def test_a_planted_over_disclosure_reds(self):
        """I12 — THE CHECK CAN FAIL: disclosing a leaf the level does NOT name is an over-disclosure."""
        c = border.least_disclosure_conflicts(
            ["set_digest", "chain_head", "merkle_root", "blobs"], "HASHES-ONLY")
        self.assertEqual(c["over"], ["blobs"])
        self.assertEqual(c["withheld"], [])

    def test_a_planted_withheld_required_leaf_reds(self):
        """I12 — THE CHECK CAN FAIL: omitting a leaf the level REQUIRES is a withheld-required leaf."""
        c = border.least_disclosure_conflicts(["set_digest", "chain_head"], "HASHES-ONLY")
        self.assertEqual(c["over"], [])
        self.assertEqual(c["withheld"], ["merkle_root"])

    def test_the_act_path_refuses_and_records_a_disclosure_violation(self):
        """A3: at the receipt act path, an over-disclosure AND a withheld-required leaf are each a
        RECORDED refusal (a crossing carries exactly the leaves the level names)."""
        _d, store, gate, _views = _body("p11-a3-", "gov")
        # over-disclosure at HASHES-ONLY -> refused and recorded
        with self.assertRaises(OpError):
            border.record_receipt(gate, "sha256:" + "1" * 64, {"key": "k"}, "s",
                                  disclosure_level="HASHES-ONLY",
                                  revealed_set={"leaves": ["set_digest", "chain_head", "merkle_root", "blobs"]})
        self.assertTrue(any(r.get("refused") and "over-disclosed" in str(r.get("payload"))
                            for r in store.all()))
        # withheld-required at HASHES-ONLY -> refused and recorded
        with self.assertRaises(OpError):
            border.record_receipt(gate, "sha256:" + "2" * 64, {"key": "k"}, "s",
                                  disclosure_level="HASHES-ONLY",
                                  revealed_set={"leaves": ["set_digest", "chain_head"]})
        self.assertTrue(any(r.get("refused") and "withheld-required" in str(r.get("payload"))
                            for r in store.all()))

    def test_an_exact_crossing_is_admitted_and_an_unrevealed_leaf_is_absent(self):
        """A3: a crossing disclosing exactly the level's leaves is admitted; a leaf NOT disclosed is
        underivable from what the receiver holds — its value never appears in the receiver's record."""
        _d, store, gate, _views = _body("p11-a3b-", "gov")
        rec = border.record_receipt(gate, "sha256:" + "3" * 64, {"key": "k"}, "s",
                                    disclosure_level="HASHES-ONLY",
                                    revealed_set={"leaves": ["set_digest", "chain_head", "merkle_root"]})
        self.assertIsNotNone(rec.get("seq"))                           # admitted (appended)
        # an unrevealed leaf (blobs) is nowhere in this body's record — it did not cross
        for r in store.all():
            revealed = (r.get("payload") or {}).get("revealed_set", "")
            self.assertNotIn("blobs", str(revealed))


# =================================================================================================
# A4 (:3698, I8, I16) — THE RECEIPT REFUSES ON THE ACT PATH
# =================================================================================================

class TestReceiptRefusesOnActPath(unittest.TestCase):
    def setUp(self):
        self.d, self.store, self.gate, self.views = _body("p11-a4-", "gov-a")

    def test_a_double_claim_at_the_receipt_is_refused_by_name_and_recorded(self):
        """A4 / I8: the receiver holds decision@fisheries; a receipt whose counterpart PRESENTS the
        SAME (stage, scope) is a double-claim — refused BY NAME (I8) and RECORDED as a refusal row.
        The presentation is the counterpart's (revealed_set), the receiver's is its own record (I1)."""
        _hold_stage(self.gate, "gov-a", "R-DEC", "decision", "fisheries")   # the receiver holds it
        with self.assertRaises(OpError) as cm:
            border.record_receipt(self.gate, "sha256:" + "a" * 64, {"key": "kb"}, "s",
                revealed_set={"held_stages": [{"actor": "gov-b", "stage": "decision", "scope": "fisheries"}]})
        self.assertEqual(cm.exception.rule, "I8")                       # refused BY NAME
        self.assertIn("decision @ fisheries", cm.exception.message)
        rows = [r for r in self.store.all() if r.get("refused") and r.get("rule_cited") == "I8"]
        self.assertEqual(len(rows), 1)                                 # RECORDED as a refusal row

    def test_disjoint_scopes_pass(self):
        """A4 / I8: the counterpart presenting the same stage for a DIFFERENT scope is no double-claim
        — the receipt is admitted (a control that cannot pass is the defect; here it passes)."""
        _hold_stage(self.gate, "gov-a", "R-DEC", "decision", "fisheries")
        rec = border.record_receipt(self.gate, "sha256:" + "b" * 64, {"key": "kb"}, "s",
            revealed_set={"held_stages": [{"actor": "gov-b", "stage": "decision", "scope": "forestry"}]})
        self.assertIsNotNone(rec.get("seq"))

    def test_a_single_holder_passes(self):
        """A4 / I8: when only the receiver holds a (stage, scope) and the counterpart presents nothing,
        there is no double-claim — admitted."""
        _hold_stage(self.gate, "gov-a", "R-DEC", "decision", "fisheries")
        rec = border.record_receipt(self.gate, "sha256:" + "c" * 64, {"key": "kb"}, "s",
                                    revealed_set={"held_stages": []})
        self.assertIsNotNone(rec.get("seq"))

    def test_all_three_powers_at_the_receipt_is_refused_by_name_and_recorded(self):
        """A4 / I16: a counterpart presenting decision + enforcement + monitoring on ONE actor for ONE
        scope is refused (rides protection.SOP) and RECORDED. Over BOTH records' live rules."""
        with self.assertRaises(OpError) as cm:
            border.record_receipt(self.gate, "sha256:" + "d" * 64, {"key": "kb"}, "s",
                revealed_set={"held_stages": [
                    {"actor": "prince", "stage": "decision", "scope": "realm"},
                    {"actor": "prince", "stage": "enforcement", "scope": "realm"},
                    {"actor": "prince", "stage": "monitoring", "scope": "realm"}]})
        self.assertIn("prince @ realm", cm.exception.message)
        self.assertTrue(any(r.get("refused") and "separation of powers" in str(r.get("payload"))
                            for r in self.store.all()))

    def test_any_two_powers_pass(self):
        """A4 / I16: holding any TWO of the three powers is not a concentration — admitted (the control
        is able-to-fail: the same shape with the third power refuses, above)."""
        rec = border.record_receipt(self.gate, "sha256:" + "e" * 64, {"key": "kb"}, "s",
            revealed_set={"held_stages": [
                {"actor": "prince", "stage": "decision", "scope": "realm"},
                {"actor": "prince", "stage": "enforcement", "scope": "realm"}]})
        self.assertIsNotNone(rec.get("seq"))

    def test_the_concentration_can_span_both_records(self):
        """A4 / I16: 'over BOTH records' live rules' — the receiver holds two of the three powers, the
        counterpart PRESENTS the third for the same actor+scope; combined, one actor concentrates all
        three and the receipt refuses (the diversity the invariant protects, across the handshake)."""
        _hold_stage(self.gate, "prince", "R1", "decision", "realm")
        _hold_stage(self.gate, "prince", "R2", "enforcement", "realm")
        with self.assertRaises(OpError):
            border.record_receipt(self.gate, "sha256:" + "f" * 64, {"key": "kb"}, "s",
                revealed_set={"held_stages": [{"actor": "prince", "stage": "monitoring", "scope": "realm"}]})

    def test_the_two_refusals_are_invoked_not_re_authored(self):
        """A4: the amendment INVOKES views.py's two refusals (P6's), it does not re-author them. border
        defines neither refuse function; the named checks (I8 / the SOP rule) are views.py's own."""
        self.assertTrue(callable(views_module.refuse_double_claim))
        self.assertTrue(callable(views_module.refuse_separation_of_powers))
        with open(os.path.join(_REPO, "src", "kernel", "border.py"), encoding="utf-8") as fh:
            bsrc = fh.read()
        self.assertNotIn("def refuse_double_claim", bsrc)              # not re-authored in border
        self.assertNotIn("def refuse_separation_of_powers", bsrc)

    def test_a_bare_receipt_is_inert_on_the_act_path(self):
        """A4 / P8: a bare row receipt (no handshake material) is unaffected by the amendment — it is
        admitted exactly as before, and even when the receiver holds a stage, no counterpart
        presentation means no double-claim."""
        _hold_stage(self.gate, "gov-a", "R-DEC", "decision", "fisheries")
        rec = border.record_receipt(self.gate, "sha256:" + "1" * 64, {"key": "kb"}, "s")
        self.assertIsNotNone(rec.get("seq"))


# =================================================================================================
# A5 (B12 rides, bounded) — A PREDICATE PROVEN WITHOUT THE VALUE
# =================================================================================================

class TestPredicateWithoutValue(unittest.TestCase):
    def _identity_tree(self):
        """An identity tree (C5's disclosure-by-law shape): a raw value leaf and a PREDICATE leaf
        (an attested fact 'version at or above 5') side by side."""
        return {
            "id/attr/version": {"type": "file", "content": "SECRET-VALUE-XYZ"},
            "id/attr/version_ge_5": {"type": "file", "content": "true"},
            "id/attr": {"type": "dir", "mode": 16877, "nlink": 2},
            "id": {"type": "dir", "mode": 16877, "nlink": 2},
        }

    def test_a_predicate_verifies_without_disclosing_the_value(self):
        """B12 (predicate half): the predicate leaf's inclusion proves the tree ASSERTS the predicate
        under the root, while the raw value crosses only as a HASH (a sibling), never as its value —
        the value is nowhere in the proof."""
        tree = self._identity_tree()
        root = merkle.merkle_root(tree)
        proof = merkle.inclusion_proof(tree, "id/attr/version_ge_5")
        self.assertIsNotNone(proof)
        self.assertTrue(merkle.verify_inclusion(proof, root))          # the predicate is proven
        # the raw value never appears in the proof — a sibling crosses as its hash, not its value
        self.assertNotIn("SECRET-VALUE-XYZ", json.dumps(proof))

    def test_a_planted_false_predicate_fails(self):
        """B12 — THE CHECK CAN FAIL: a predicate the tree does NOT assert has no inclusion proof
        (None), and a proof for the real predicate does not verify against a wrong root."""
        tree = self._identity_tree()
        root = merkle.merkle_root(tree)
        self.assertIsNone(merkle.inclusion_proof(tree, "id/attr/version_ge_99"))   # not asserted
        good = merkle.inclusion_proof(tree, "id/attr/version_ge_5")
        self.assertFalse(merkle.verify_inclusion(good, "sha256:" + "0" * 64))      # wrong root

    def test_the_unlinkability_half_is_not_built_the_cap(self):
        """CAP (stop (f); A5): full unlinkability of per-peer roots is NOT built here. The identity
        tree folds to ONE deterministic root, so the SAME identity presented to two peers shares that
        root — the roots are LINKABLE. Cost, stated: linking two crossings to one body is possible;
        building per-peer unlinkable roots (a zero-knowledge join-resistance) is a later target, not
        this unit's build. This test PROVES the cap by demonstrating the linkage rather than hiding
        it."""
        tree = self._identity_tree()
        root_to_peer_a = merkle.merkle_root(tree)
        root_to_peer_b = merkle.merkle_root(tree)
        self.assertEqual(root_to_peer_a, root_to_peer_b)              # SAME root -> linkable (the cap)


# =================================================================================================
# A6 — NO FOUNDING
# =================================================================================================

class TestNoFounding(unittest.TestCase):
    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs a git repository (git history is unavailable in the render)")
    def test_the_founding_pack_is_byte_unchanged(self):
        """A6: P11 mints no founding — the pack is byte-unchanged against HEAD (no new op/law/check
        kind, no pack edit). git diff --stat on the pack is empty."""
        out = subprocess.run(
            ["git", "-C", _REPO, "diff", "--stat", "--", "src/founding/founding-pack.json"],
            capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "", out.stdout)

    def test_no_new_op_check_kind_or_attested_member(self):
        """A6: OP_CHECKS stays 19 (no new check kind — the I12/handshake checks are plain census
        instruments, not registered kinds); this unit's fence added NO src engine module (N1 is a
        FUNCTION on the existing merkle.py, N3 EXTENDS the existing checkpoint.py — the rider is inert).
        Both modules are already attested members."""
        self.assertEqual(len(OP_CHECKS), 19)
        # RE-POINTED (:3934): assert THIS unit's own property — its fence added NO src engine module —
        # NOT the absolute len(ATTESTED_MEMBERS)==N global count. That count is test_ep40/ep46/keymat's
        # property (the attested set is their subject); carried here it was a location pin on someone
        # else's property and churned on every lawful src add estate-wide (host_seam.py moved it 54->55).
        self.assertFalse(any(m.endswith("/handshake.py") for m in attestation.ATTESTED_MEMBERS),
                         "P11 added a new src engine module — its fence adds none (N1/N3 extend existing modules)")
        self.assertTrue(any("bridge/merkle.py" in m for m in attestation.ATTESTED_MEMBERS))
        self.assertTrue(any("bridge/checkpoint.py" in m for m in attestation.ATTESTED_MEMBERS))

    def test_the_receipt_op_params_are_p8s_not_p11s(self):
        """A6: the RECEIPT op's optional fields (checks/disclosure_level/address_form) were declared by
        P8 (founding_version 1.51.0), not by P11 — P11 consumes them, mints nothing."""
        with open(os.path.join(_REPO, "src", "founding", "founding-pack.json"), encoding="utf-8") as fh:
            pack = json.load(fh)
        # C6a VT-2 (CREATE-RELATIONSHIP MINTED live) moved the live version 1.51.0 -> 1.52.0.
        # C6a VT-3 (THE TREE SEEDED AS ROWS — 35 view rows) moved it 1.52.0 -> 1.53.0 BY NAME (§A57);
        # C6a VT-6d (THE STAMP FOUNDING — the required-stamps policy rule) moved it 1.53.0 -> 1.54.0 BY NAME (§A57).
        # C7 P3 (THE KERNEL FROM THE RECORD — the twelve act-kind rows) moved it 1.54.0 -> 1.55.0 BY NAME (§A57).
        # P11 still mints nothing — it consumes P8's RECEIPT fields; the live version is read fresh.
        self.assertEqual(pack["founding_version"], "1.55.0")           # the live founding version (C7 P3's move)
        receipt = None
        for step in pack["steps"]:
            for r in step["records"]:
                if r.get("object") == "op:RECEIPT":
                    receipt = r["payload"]["definition"]["params"]
        self.assertIsNotNone(receipt)
        for f in ("checks", "disclosure_level", "address_form"):
            self.assertEqual(receipt[f], "optional")                  # declared by P8, consumed by P11


if __name__ == "__main__":
    unittest.main()
