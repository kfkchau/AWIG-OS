# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (crossing, receipt, body name, relation view, countersign); NON-GOAL: no offensive
# capability of any kind — this records a mutual relation between a child and its parent as an act
# in each record, by function. Full declaration: SCOPE-STATEMENT.md.
"""C6 P7 — THE HANDSHAKE RELATION (design/52 v2.0 B1:50, I4:76, L27:125; plan
planning/exec/P7-HANDSHAKE-RELATION-BUILD.md).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). Reading A — the owner's confirmation (:3658): the mutual handshake
relation is recorded over the EXISTING crossing/receipt vocabulary (kernel.border, READ and reused,
never re-authored) with NO PACK EDIT and NO NEW OP. A child and its parent are two bodies IN A LIVE,
WITHDRAWABLE HANDSHAKE RELATION — the tree's binding held as a relation each keeps in its OWN record,
not a pin one is born with.

  A1  BOTH HALVES IN EACH RECORD, MUTUAL (precisions 1, 2, 4): each body records its OWN half as a
      DECISION (a BORDER-SUBMIT naming the counterpart's body-name — key, genesis — under the
      crossing's under_rule); the counterpart's half lands in each record as INPUT (its RECEIPT of
      the crossing), each by its OWN pen (one pen per record, I1). One crossing yields one row; the
      received-back receipt gets ONE receipt and NO loop (RECEIPT idempotence — a second receipt for
      one content hash is refused at the chokepoint). The relation's KIND is the crossing's
      under_rule (its rule_cited); the owner's Q5 tag is ABSENT (None) until he gives it.
  A2  WITHDRAWAL BY CONTENT HASH, EITHER SIDE (precision 3): either side withdraws ITS OWN half by a
      BORDER-SUBMIT citing the relation's content hash; the live-relation view reads the relation as
      ended; the declare and withdraw rows both STAND (no delete).
  A3  THE LIVE-RELATION VIEW, FROM ITS OWN ROWS (precision 1): each side's current relation is a
      fold over ITS OWN declare/withdraw rows (recomputed from those rows alone equals the served
      state), never the peer's record; a relation never declared, or withdrawn, is absent/ended.
  A4  THE CRUX PROVEN AT BUILD: the crossing shape carries STANDING BILATERAL relation state (held
      in both records, withdrawable), so Reading A ships (no pack edit, no new op); Reading B's
      one-op founding need is NOT reached (it would be a STOP and a raise, never a silent mint).

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect, §A42/§A64): a second receipt refused; a withdraw citing a non-relation hash ends
nothing; the peer's declare never enters this body's view; an ordinary crossing is not a relation.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel import border                                            # noqa: E402


def _body(prefix, entity, actor_class="ai"):
    """One BODY — an independent record (its own data dir), gate and views, with `entity` established
    as an account so it may open a crossing (BORDER-SUBMIT's require_prior over CREATE-ACCOUNT). A
    body writes only its own record (one pen per record, the single-writer lock)."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": entity, "actor_class": actor_class})
    return d, store, gate, views


def _body_name(store, key):
    """A body's NAME (D08.42): (bound public key, genesis hash of its first record)."""
    return border.from_body_name(key, border.genesis_hash(store))


def _declare(gate, entity, parent_name, tag=None):
    """A DECLARE crossing: a BORDER-SUBMIT whose draft names the parent's body-name under the
    handshake marker. `tag` (the owner's Q5 HR/NT/SY) is only carried when the owner gives it —
    ABSENT otherwise (never defaulted)."""
    hs = {"parent": parent_name}
    if tag is not None:
        hs["tag"] = tag
    return border.submit(gate, entity, {"handshake_relation": hs}, actor=entity)


def _withdraw(gate, entity, relation_id):
    """A WITHDRAW crossing: a BORDER-SUBMIT whose draft cites the relation's content hash."""
    return border.submit(gate, entity, {"handshake_relation": {"withdraws": relation_id}}, actor=entity)


# =============================================================================================
# A1 — BOTH HALVES IN EACH RECORD, MUTUAL (precisions 1, 2, 4)
# =============================================================================================

class TestBothHalvesInEachRecord(unittest.TestCase):
    def setUp(self):
        self.cd, self.c_store, self.c_gate, self.c_views = _body("p7-a1-child-", "child")
        self.pd, self.p_store, self.p_gate, self.p_views = _body("p7-a1-parent-", "parent")
        self.child_name = _body_name(self.c_store, "ed25519-pub:child")
        self.parent_name = _body_name(self.p_store, "ed25519-pub:parent")

    def test_each_body_holds_its_own_declare_and_the_counterparts_half_as_input(self):
        """A1 / precisions 1-2: each body records its OWN half as a DECISION (a BORDER-SUBMIT naming
        the counterpart's body-name under the crossing's under_rule) and the counterpart's half as
        INPUT (its RECEIPT). One crossing yields one row; each pen writes only its own record."""
        # child's own half: a declare naming the parent (the child's DECISION), one crossing, one row.
        c_declare = _declare(self.c_gate, "child", self.parent_name)
        c_rid = border.content_id(c_declare)
        self.assertEqual(c_declare["action"], "BORDER-SUBMIT")               # over the crossing vocabulary
        self.assertEqual(c_declare.get("rule_cited"), "COMM-LAW-CONTRACT")   # the crossing's under_rule
        self.assertEqual(len([e for e in self.c_store.by_action("BORDER-SUBMIT")]), 1)  # one crossing, one row

        # the parent's own half: a declare naming the child (symmetric — each pen its own record).
        p_declare = _declare(self.p_gate, "parent", self.child_name)
        p_rid = border.content_id(p_declare)

        # the counterpart's half lands in each record as INPUT: each RECEIPTS the other's declare.
        self.p_gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "sys", "actor_class": "ai"})  # no-op guard
        parent_receipt = border.record_receipt(self.p_gate, c_rid, self.child_name, "ed25519-sig:c")
        child_receipt = border.record_receipt(self.c_gate, p_rid, self.parent_name, "ed25519-sig:p")
        self.assertIn(c_rid, border.receipts(self.p_store))                  # parent holds the child's half (INPUT)
        self.assertIn(p_rid, border.receipts(self.c_store))                  # child holds the parent's half (INPUT)

        # both halves in the CHILD's record: its own declare AND its receipt of the parent's declare.
        self.assertIn(c_rid, self.c_views.handshake_relations())            # its own DECISION half
        self.assertIn(p_rid, border.receipts(self.c_store))                 # the counterpart half as INPUT
        # and the parent's declare NEVER entered the child's record (one pen per record, I1).
        self.assertNotIn(p_rid, self.c_views.handshake_relations())
        self.assertEqual(border.receipts(self.p_store).keys() & border.receipts(self.c_store).keys(), set())

        rel = self.c_views.handshake_relations()[c_rid]
        self.assertEqual(rel["parent"], self.parent_name)                   # names the parent (key, genesis)
        self.assertEqual(rel["under_rule"], "COMM-LAW-CONTRACT")            # KIND = the crossing's under_rule (precision 2)
        self.assertIsNone(rel["tag"])                                       # Q5 tag ABSENT until the owner gives it
        self.assertEqual(rel["state"], "live")

    def test_the_Q5_tag_rides_the_same_row_only_when_given_never_defaulted(self):
        """Precision 2: the owner's Q5 relation tag (HR/NT/SY) rides the SAME declare row when he
        gives it, and is ABSENT (None) — not defaulted — until then. Both directions provable."""
        no_tag = _declare(self.c_gate, "child", self.parent_name)          # the owner has NOT given a tag
        self.assertIsNone(self.c_views.handshake_relations()[border.content_id(no_tag)]["tag"])
        with_tag = _declare(self.c_gate, "child", self.parent_name, tag="HR")  # the owner gives one
        self.assertEqual(self.c_views.handshake_relations()[border.content_id(with_tag)]["tag"], "HR")

    def test_RW_the_received_back_receipt_gets_one_receipt_and_no_loop(self):
        """A1 / precision 4 (RECEIPT idempotence): a mutual handshake does NOT recurse into an
        unbounded receipt-of-receipt chain. The child receipts the parent's returned half exactly
        ONCE; a SECOND receipt for the same content hash is refused at the gate chokepoint. Able-to-
        fail: the first receipt is admitted, so the refusal is the second's alone."""
        p_declare = _declare(self.p_gate, "parent", self.child_name)
        p_rid = border.content_id(p_declare)
        first = border.record_receipt(self.c_gate, p_rid, self.parent_name, "sig")   # admitted
        # the received-back receipt itself gets ONE receipt (a receipt of the receipt), and no more.
        rec_ch = border.content_id(first)
        border.record_receipt(self.c_gate, rec_ch, self.parent_name, "sig")          # one receipt of it
        with self.assertRaises(OpError) as cm:
            border.record_receipt(self.c_gate, rec_ch, self.parent_name, "sig")      # a second — refused
        self.assertEqual(cm.exception.rule, "COMM-LAW-CONTRACT")
        self.assertEqual(len([ch for ch in border.receipts(self.c_store) if ch == rec_ch]), 1)  # no loop


# =============================================================================================
# A2 — WITHDRAWAL BY CONTENT HASH, EITHER SIDE (precision 3)
# =============================================================================================

class TestWithdrawalByContentHash(unittest.TestCase):
    def setUp(self):
        self.cd, self.c_store, self.c_gate, self.c_views = _body("p7-a2-child-", "child")
        self.pd, self.p_store, self.p_gate, self.p_views = _body("p7-a2-parent-", "parent")
        self.parent_name = _body_name(self.p_store, "ed25519-pub:parent")

    def test_a_side_withdraws_its_own_half_by_citing_the_relations_content_hash(self):
        """A2 / precision 3: a side withdraws ITS OWN half by a BORDER-SUBMIT citing the relation's
        content hash. The live view then reads the relation as ENDED; the declare AND the withdraw
        rows BOTH STAND (no delete — order is untouched, validity is what changed)."""
        declare = _declare(self.c_gate, "child", self.parent_name)
        rid = border.content_id(declare)
        self.assertTrue(self.c_views.handshake_relation_live(rid))          # live before withdrawal
        _withdraw(self.c_gate, "child", rid)
        self.assertFalse(self.c_views.handshake_relation_live(rid))         # ended after withdrawal
        self.assertEqual(self.c_views.handshake_relations()[rid]["state"], "withdrawn")
        # both rows STAND (no delete): the declare and the withdraw are both on the record.
        submits = self.c_store.by_action("BORDER-SUBMIT")
        self.assertEqual(len(submits), 2)                                   # declare + withdraw both present
        rel = self.c_views.handshake_relations()[rid]
        self.assertIsNotNone(rel["declare_seq"])
        self.assertIsNotNone(rel["withdraw_seq"])
        self.assertLess(rel["declare_seq"], rel["withdraw_seq"])            # withdraw is the later crossing

    def test_either_side_may_withdraw_its_own_half(self):
        """Precision 3: EITHER side may withdraw its own half. The parent, holding its own declare in
        its own record, withdraws its own relation — independently of the child's."""
        child_name = _body_name(self.c_store, "ed25519-pub:child")
        p_declare = _declare(self.p_gate, "parent", child_name)
        p_rid = border.content_id(p_declare)
        self.assertTrue(self.p_views.handshake_relation_live(p_rid))
        _withdraw(self.p_gate, "parent", p_rid)
        self.assertFalse(self.p_views.handshake_relation_live(p_rid))       # the parent ended its own half

    def test_RW_a_withdraw_citing_a_non_relation_hash_ends_nothing(self):
        """RW (able-to-fail): withdrawal is BY the relation's content hash. A withdraw citing a hash
        that is no relation's id ends NOTHING — the live relation stays live. A check that cannot
        fail is not a check: here a wrong citation leaves the state untouched, an honest no-op."""
        declare = _declare(self.c_gate, "child", self.parent_name)
        rid = border.content_id(declare)
        _withdraw(self.c_gate, "child", "sha256:" + "0" * 64)               # cites no relation
        self.assertTrue(self.c_views.handshake_relation_live(rid))          # still live — nothing ended


# =============================================================================================
# A3 — THE LIVE-RELATION VIEW, FROM ITS OWN ROWS (precision 1)
# =============================================================================================

class TestLiveRelationViewFromOwnRows(unittest.TestCase):
    def setUp(self):
        self.cd, self.c_store, self.c_gate, self.c_views = _body("p7-a3-child-", "child")
        self.pd, self.p_store, self.p_gate, self.p_views = _body("p7-a3-parent-", "parent")
        self.parent_name = _body_name(self.p_store, "ed25519-pub:parent")
        self.child_name = _body_name(self.c_store, "ed25519-pub:child")

    def test_recomputed_from_its_own_rows_equals_the_served_state(self):
        """A3 / P2 round-trip: the live-relation view is a FOLD over the body's own declare/withdraw
        rows — recomputed from those rows ALONE equals the served state. A fresh Views over the same
        record file reconstructs an identical answer (kill it, replay, identical)."""
        d1 = _declare(self.c_gate, "child", self.parent_name)
        d2 = _declare(self.c_gate, "child", self.parent_name, tag="NT")
        _withdraw(self.c_gate, "child", border.content_id(d1))
        served = self.c_views.handshake_relations()
        # a fresh kernel over the SAME record file recomputes the identical view (round-trip law).
        _s2, _g2, v2, _b2, _u2 = build_full_kernel(
            os.path.join(self.cd, "record.jsonl"), os.path.join(self.cd, "blobs"),
            os.path.join(self.cd, "vault"))
        self.assertEqual(v2.handshake_relations(), served)
        self.assertEqual(served[border.content_id(d1)]["state"], "withdrawn")
        self.assertEqual(served[border.content_id(d2)]["state"], "live")

    def test_never_the_peers_record_a_relation_the_peer_declared_is_absent_here(self):
        """A3 / precision 1: each side reads ITS OWN rows, NEVER the peer's record. A relation the
        PARENT declared in the parent's record does NOT appear in the CHILD's view — the child's fold
        is over the child's rows alone. Able-to-fail: it appears in the parent's own view, so the
        absence in the child's is the boundary, not an empty query."""
        p_declare = _declare(self.p_gate, "parent", self.child_name)
        p_rid = border.content_id(p_declare)
        self.assertIn(p_rid, self.p_views.handshake_relations())            # the parent's own view holds it
        self.assertNotIn(p_rid, self.c_views.handshake_relations())         # the child's view NEVER does

    def test_a_relation_never_declared_is_absent(self):
        """A3: a relation never declared is ABSENT from the view — the fold reports only what the
        body's own record declared, never a stored placeholder."""
        self.assertEqual(self.c_views.handshake_relations(), {})            # nothing declared -> empty
        self.assertFalse(self.c_views.handshake_relation_live("sha256:" + "a" * 64))


# =============================================================================================
# A4 — THE CRUX PROVEN AT BUILD: Reading A ships (no pack edit, no new op)
# =============================================================================================

class TestCruxProvenAtBuild(unittest.TestCase):
    def setUp(self):
        self.cd, self.c_store, self.c_gate, self.c_views = _body("p7-a4-child-", "child")
        self.pd, self.p_store, self.p_gate, self.p_views = _body("p7-a4-parent-", "parent")
        self.parent_name = _body_name(self.p_store, "ed25519-pub:parent")
        self.child_name = _body_name(self.c_store, "ed25519-pub:child")

    def test_the_crossing_shape_carries_standing_bilateral_relation_state(self):
        """A4: the build DRIVES whether a crossing carries STANDING BILATERAL relation state — a
        relation held in both records, withdrawable. It DOES: (a) the declare carries the parent's
        body-name (key, genesis); (b) the counterpart's RECEIPT cites the relation's content hash
        (the mutual half); (c) a withdraw ends it by content hash; (d) it is held in each record via
        each side's own fold. Therefore Reading A SHIPS — Reading B's one-op founding need is NOT
        reached (it would be a STOP and a raise, never a silent mint)."""
        # (a) standing relation state expressible over the crossing: the declare names the parent.
        declare = _declare(self.c_gate, "child", self.parent_name)
        rid = border.content_id(declare)
        self.assertEqual(self.c_views.handshake_relations()[rid]["parent"], self.parent_name)
        # (b) the mutual half: the parent's RECEIPT of the crossing cites the relation's content hash.
        receipt = border.record_receipt(self.p_gate, rid, self.child_name, "sig")
        self.assertEqual((receipt.get("payload") or {}).get("content_hash"), rid)
        self.assertIn(rid, border.receipts(self.p_store))
        # (c) withdrawable by content hash.
        _withdraw(self.c_gate, "child", rid)
        self.assertFalse(self.c_views.handshake_relation_live(rid))
        # (d) held in both records: the child's own declare, the parent's own receipt of it.
        self.assertIn(rid, self.c_views.handshake_relations())             # child's record
        self.assertIn(rid, border.receipts(self.p_store))                  # parent's record

    def test_RW_an_ordinary_crossing_is_not_a_relation(self):
        """A4 (able-to-fail): recognition is by the handshake marker in the draft. An ORDINARY
        BORDER-SUBMIT (no handshake_relation marker) is NOT a relation act — it does not enter the
        live-relation view. A recognition rule that cannot fail is not a rule."""
        border.submit(self.c_gate, "child", {"want": "read /x"})           # an ordinary crossing
        self.assertEqual(self.c_views.handshake_relations(), {})           # not a relation

    def test_Reading_A_shipped_the_pack_carries_no_handshake_op(self):
        """A4: Reading A means NO PACK EDIT and NO NEW OP. The founding pack carries no
        HANDSHAKE-RELATION op and no handshake vocabulary — the relation rides the existing
        crossing/receipt ops (BORDER-SUBMIT / RECEIPT). Reading B (one op) would be a
        YELLOW->founding re-tier at the owner's word; it was not reached and nothing was minted."""
        import json
        repo = os.path.join(os.path.dirname(__file__), "..")
        with open(os.path.join(repo, "src", "founding", "founding-pack.json"), "rb") as fh:
            raw = fh.read()
        recs = [r for step in json.loads(raw)["steps"] for r in step["records"]]
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertNotIn("HANDSHAKE-RELATION", op_names)                   # no new op minted
        self.assertNotIn(b"handshake", raw.lower())                        # no handshake vocabulary in the pack
        # the existing crossing/receipt ops the relation rides ARE present (reused, not re-authored).
        for kept in ("BORDER-SUBMIT", "RECEIPT"):
            self.assertIn(kept, op_names)


if __name__ == "__main__":
    unittest.main()
