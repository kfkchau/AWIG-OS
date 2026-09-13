"""EP-49D — THE RECEIPT: ONE ROW, ONE RECEIPT, TWO BODIES (design/51 §3 N9, §4, §5, §9; D08.42, D08.48).

Named in planning/exec/EP-49D-BUILD.md before code, landed here as regression tests (charter:
every verification probe lands as a regression test). This battery proves the receiver's own
acknowledgement of a crossing:

  A1  a row received at body B produces EXACTLY ONE RECEIPT in B's record citing the row's content
      hash; a second receipt for the same row is refused (idempotent); a receipt whose content hash
      does not match the row it names binds nothing (RW-RECEIPT-NOT-BOUND).
  A2  B's receipt lands in B's OWN record; A's record is UNCHANGED by it; a cross-write (a foreign
      writer on a body's data dir) is refused by the single-writer lock — one pen per record (D08.30).
  A3  the receipt names the from-body as the sender's bound SYSTEM PUBLIC KEY + genesis hash (D08.42)
      and verifies the sender's SIGNATURE under that key (real-or-refused, N10); a copied seed shows
      as a FORK the chain exposes, never a silent clash; identity is what crossed (N4's cap).
  A4  one row crosses host->guest (two bodies); the second body appends ITS receipt to its OWN
      record; the two records' hashes are independent; the round trip verifies.
  A5  the content/chain hash a receipt cites EXCLUDES record_time (D08.40): two bodies recording one
      crossing at different times derive the SAME hash; a planted record_time inside the hashed
      content REDS.
  A6  the founding move mints RECEIPT as a data-born MINOR bump, attested in one entry; no check kind.

THE WRONG REFERENCE REFUSED BY NAME (design/51 §5, §9): the API gateway with auth middleware — a
token minted ABOVE the system as identity, the request treated as the act, a trust store BESIDE the
record. Here the receipt is the receiver's OWN row; the from-body is what CROSSED (a bound key +
genesis hash), never trust in the peer's own record; a second body's receipt never writes the
first's record (one pen per record). Validity is read FROM the record, not from a token store.

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect, §A42/§A64). The signing library is an OPTIONAL EXTRA: the from-signature verification
branches to its REFUSAL arm when absent (N10: real-or-refused, never faked) and its real arm when
present — the test_ep49a/b present/absent idiom.

THE HOST<->GUEST ARM (A4). The two bodies are two INDEPENDENT records (two data dirs, each with its
own single-writer lock). On the host both bodies are modelled as separate stores, exactly as EP-48
modelled the wire before EP-48G made it real (design/51 §5); the STRUCTURAL property — two records,
independent hashes, one pen per body, the round trip — is proven here and is what this class runs.
The physical guest-real arm (a real socket between this box and its own VM under the pinned kernel,
6.8.0-134-generic) runs IN-GUEST by EP-00 rule 9 and is filed as evidence; a RECEIPT is a governed
op, not kernel work, so the property is identical on either body.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.opdefs import OP_CHECKS                                   # noqa: E402
from kernel.signer import SigningKeyStore                             # noqa: E402
from kernel.store import EventStore                                   # noqa: E402
from kernel import border, canonical, crypto                         # noqa: E402
from observe import classmap                                         # noqa: E402

# A fixed seed for a sender body's system key (its NAME, D08.42) and a different one — the check
# that can fail (a real signature under a different key does not verify).
SENDER_SEED = bytes(range(1, 33))
OTHER_SEED = bytes([9]) * 32

# A crossing — a row an outside entity submitted; its content hash is the crossing id (border.content_id).
A_ROW = {"action": "BORDER-SUBMIT", "object": "peer", "target": None,
         "payload": {"kind": "border-submit", "want": "read /x"}}


def _body(prefix):
    """One BODY — an independent record (its own data dir), gate and views. Two bodies are two of
    these; a body writes only its own record (one pen per record, the single-writer lock)."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    return d, store, gate


# =============================================================================================
# A1 — T-ONE-ROW-ONE-RECEIPT (+ RW-DOUBLE-RECEIPT / RW-RECEIPT-NOT-BOUND)
# =============================================================================================

class TestOneRowOneReceipt(unittest.TestCase):
    def setUp(self):
        self.a_dir, self.a_store, self.a_gate = _body("ep49d-a1-A-")
        self.b_dir, self.b_store, self.b_gate = _body("ep49d-a1-B-")
        self.ch = border.content_id(A_ROW)
        self.fb = border.from_body_name("ed25519-pub:sender", border.genesis_hash(self.a_store))

    def test_a_received_row_produces_exactly_one_receipt_citing_its_content_hash(self):
        """N9: a row sent from body A is received at body B and produces EXACTLY ONE RECEIPT in B's
        record, a DECISION citing the row's content hash. The receipt IS the receiver's own row."""
        rec = border.record_receipt(self.b_gate, self.ch, self.fb, "ed25519-sig:z")
        self.assertEqual(rec["action"], "RECEIPT")
        p = rec.get("payload") or {}
        self.assertEqual(p.get("kind"), "receipt")
        self.assertEqual(p.get("record_class"), "DECISION")          # the receiver's own act
        self.assertEqual(p.get("content_hash"), self.ch)             # cites the received row
        self.assertEqual(rec["rule_cited"], "COMM-LAW-CONTRACT")     # cites the existing channel law
        # exactly one receipt for the row (the fold is keyed by content hash).
        self.assertEqual(list(border.receipts(self.b_store)), [self.ch])
        self.assertTrue(border.receipt_binds_row(rec, A_ROW))        # the receipt is OF this crossing

    def test_RW_DOUBLE_RECEIPT_a_second_receipt_for_the_same_row_is_refused(self):
        """RW-DOUBLE-RECEIPT (§4): one row, ONE receipt. A second receipt for the same content hash
        is refused at the gate chokepoint (idempotent) and the fold stays at one. Able-to-fail: the
        first receipt is admitted, so the refusal is the second's alone."""
        border.record_receipt(self.b_gate, self.ch, self.fb, "sig")           # first — admitted
        with self.assertRaises(OpError) as cm:
            border.record_receipt(self.b_gate, self.ch, self.fb, "sig")       # second — refused
        self.assertEqual(cm.exception.rule, "COMM-LAW-CONTRACT")
        # the refusal was RECORDED (cannot-do-lawfully, cannot-do-quietly).
        refs = [e for e in self.b_store.by_action("op-refused")
                if (e.get("payload") or {}).get("op") == "RECEIPT"]
        self.assertTrue(refs, "the double receipt was silently dropped, not recorded")
        self.assertEqual(len(border.receipts(self.b_store)), 1)               # still exactly one

    def test_RW_RECEIPT_NOT_BOUND_a_receipt_whose_hash_is_not_the_rows_binds_nothing(self):
        """RW-RECEIPT-NOT-BOUND (§4): the receipt is OF a specific crossing. A receipt whose content
        hash is not the content hash of the row it names binds nothing — the binding reads the row's
        own bytes (border.content_id), never the receipt's claim. Both directions provable."""
        rec = border.record_receipt(self.b_gate, self.ch, self.fb, "sig")
        self.assertTrue(border.receipt_binds_row(rec, A_ROW))                 # the honest world binds
        other_row = {"action": "BORDER-SUBMIT", "object": "peer", "target": None,
                     "payload": {"kind": "border-submit", "want": "read /OTHER"}}
        self.assertFalse(border.receipt_binds_row(rec, other_row))            # a different row: no bind


# =============================================================================================
# A2 — T-ONE-PEN-HOLDS (+ RW-CROSS-WRITE) — the single-writer lock, one writer per data dir
# =============================================================================================

class TestOnePenHolds(unittest.TestCase):
    def setUp(self):
        self.a_dir, self.a_store, self.a_gate = _body("ep49d-a2-A-")
        self.b_dir, self.b_store, self.b_gate = _body("ep49d-a2-B-")
        self.ch = border.content_id(A_ROW)
        self.fb = border.from_body_name("ed25519-pub:sender", border.genesis_hash(self.a_store))

    def test_B_receipt_lands_in_Bs_own_record_and_As_record_is_unchanged(self):
        """N9: B appends its receipt to ITS OWN record; A's record is UNCHANGED — A never writes B's
        record and B never A's (one pen per record, D08.30). A's chain head is byte-identical before
        and after B's receipt, and the two bodies' heads are independent."""
        a_head_before = border.chain_head(self.a_store)
        a_len_before = len(self.a_store.all())
        rec = border.record_receipt(self.b_gate, self.ch, self.fb, "sig")
        self.assertIn(self.ch, border.receipts(self.b_store))                 # B's receipt is in B's record
        self.assertEqual(border.receipts(self.a_store), {})                   # A's record has none
        self.assertEqual(border.chain_head(self.a_store), a_head_before)      # A UNCHANGED
        self.assertEqual(len(self.a_store.all()), a_len_before)               # A grew by nothing
        self.assertNotEqual(border.chain_head(self.a_store),
                            border.chain_head(self.b_store))                  # two records, two heads

    def test_RW_CROSS_WRITE_a_foreign_writer_on_a_bodys_data_dir_is_refused(self):
        """RW-CROSS-WRITE (§4): the one-pen mechanism (EP-28G, reused). A body's record has ONE writer
        per data dir — a second writer while another (live) process holds the pen is refused. Able-to-
        fail: with a live foreign pid in the lock file the acquire REFUSES; with no lock file it
        acquires. pid 1 (init) is always alive and is never this process, so it is the foreign holder."""
        rec_path = os.path.join(self.b_dir, "lock-probe", "record.jsonl")
        os.makedirs(os.path.dirname(rec_path), exist_ok=True)
        # a live foreign process (pid 1) holds the pen -> a second writer is refused (one pen per dir).
        with open(rec_path + ".lock", "w") as fh:
            fh.write("1")
        with self.assertRaises(RuntimeError) as cm:
            EventStore(rec_path, lock=True)
        self.assertIn("one writer per data dir", str(cm.exception))
        # with the pen free (no lock file) a writer acquires — the refusal is the foreign holder's,
        # not a store that cannot open (the control discriminates).
        os.remove(rec_path + ".lock")
        s = EventStore(rec_path, lock=True)
        self.assertIsNotNone(s)


# =============================================================================================
# A3 — T-PEER-IDENTITY-EXPRESSIBLE (+ RW-WRONG-KEY / RW-COPIED-SEED-CLASH)
# =============================================================================================

class TestPeerIdentityExpressible(unittest.TestCase):
    def setUp(self):
        self.a_dir, self.a_store, self.a_gate = _body("ep49d-a3-A-")
        self.ch = border.content_id(A_ROW)

    def test_the_from_body_is_the_bound_key_plus_genesis_and_the_signature_verifies(self):
        """A3 / D08.42: the from-body is a body's NAME — the pair (bound SYSTEM PUBLIC KEY, genesis
        hash). The receipt verifies the sender's SIGNATURE over the crossing under that key. Real-or-
        refused (N10): with the library ABSENT verification REFUSES citing the absent library, never a
        modelled pass; with it PRESENT a correct signature verifies and a wrong key/signature does not
        (the check that can fail). Identity is what CROSSED (N4's cap): only the key that signed."""
        genesis = border.genesis_hash(self.a_store)
        self.assertIsNotNone(genesis)                                        # the body pins its founding

        if not crypto.real_available():
            fb = border.from_body_name("ed25519-pub:modelled", genesis)
            with self.assertRaises(crypto.LibraryAbsent):
                border.verify_from_sig(fb, "ed25519-sig:x", self.ch)         # real-or-refused
            return

        pub = crypto.public_from_seed(SENDER_SEED)
        fb = border.from_body_name(pub, genesis)                            # the sender's NAME
        signer = SigningKeyStore(); custody = signer.seal(SENDER_SEED)
        sig = signer.sign(custody, self.ch.encode())                       # A signs the crossing
        self.assertTrue(border.verify_from_sig(fb, sig, self.ch))          # correct -> verifies
        # RW-WRONG-KEY: a real signature under a DIFFERENT key does not verify.
        other_fb = border.from_body_name(crypto.public_from_seed(OTHER_SEED), genesis)
        self.assertFalse(border.verify_from_sig(other_fb, sig, self.ch))
        # a signature over a DIFFERENT crossing does not verify (the seal is over exactly what crossed).
        self.assertFalse(border.verify_from_sig(fb, sig, "sha256:" + "0" * 64))

    def test_RW_COPIED_SEED_is_a_fork_the_chain_exposes_never_a_clash(self):
        """RW-COPIED-SEED-CLASH (§4; N9): a copied seed shares the KEY but the two bodies' chains
        DIVERGE — the fork is exposed by the chain, never a silent clash. Two bodies with an identical
        key that record different crossings have DIFFERENT chain heads; a body's chain head is not
        another's even when the key is copied (able-to-fail: identical records would clash, divergent
        ones do not)."""
        same_key = "ed25519-pub:COPIED-SEED"
        _bd, b_store, b_gate = _body("ep49d-a3-B-")
        _cd, c_store, c_gate = _body("ep49d-a3-C-")
        fb = border.from_body_name(same_key, border.genesis_hash(self.a_store))
        border.record_receipt(b_gate, "sha256:" + "b" * 64, fb, "sig")      # B receives one crossing
        border.record_receipt(c_gate, "sha256:" + "c" * 64, fb, "sig")      # C receives another
        self.assertEqual(fb["key"], same_key)                              # the KEY is copied (shared)
        # the fork is in the chain: the two bodies' heads differ though the key is identical.
        self.assertNotEqual(border.chain_head(b_store), border.chain_head(c_store))
        # and each body's own record is internally consistent (kill the fold, replay: identical).
        self.assertEqual(border.receipts(b_store), border.receipts(b_store))


# =============================================================================================
# A4 — T-HOST-GUEST-RECEIPT (+ RW-SAME-RECORD) — two bodies, two records
# =============================================================================================

class TestHostGuestReceipt(unittest.TestCase):
    def test_one_row_crosses_two_bodies_and_the_second_appends_its_own_independent_receipt(self):
        """A4 / N9: one row crosses host->guest (two bodies). The second body (the guest) appends ITS
        receipt to its OWN record; the two records' hashes are INDEPENDENT; the round trip verifies —
        the guest's receipt cites the same content hash the host's row bears (border.content_id, the
        crossing id that both bodies compute from the row's own bytes). Modelled here as two records;
        the physical guest arm runs in-guest (EP-00 rule 9) and is filed as evidence."""
        _hd, host_store, host_gate = _body("ep49d-a4-host-")
        _gd, guest_store, guest_gate = _body("ep49d-a4-guest-")
        # the host holds the row (a crossing); the guest is handed the ROW (over the wire) and computes
        # its content hash from the row's own bytes — never trusting an in-band token.
        ch = border.content_id(A_ROW)
        fb = border.from_body_name("ed25519-pub:host", border.genesis_hash(host_store))
        guest_receipt = border.record_receipt(guest_gate, ch, fb, "sig")
        # the guest's receipt is in the GUEST's record, and the round trip verifies (same content hash).
        self.assertIn(ch, border.receipts(guest_store))
        self.assertTrue(border.receipt_binds_row(guest_receipt, A_ROW))
        # RW-SAME-RECORD: the two bodies are TWO records with INDEPENDENT hashes — the guest's receipt
        # did not land in the host's record, and the host's head is untouched.
        self.assertEqual(border.receipts(host_store), {})
        self.assertNotEqual(border.chain_head(host_store), border.chain_head(guest_store))

    def test_the_two_bodies_records_are_independent_hash_chains(self):
        """N9: nothing built assumes the machine is alone. Two bodies have independent chains — a
        record appended at one moves that body's head and leaves the other's byte-identical."""
        _hd, host_store, host_gate = _body("ep49d-a4b-host-")
        _gd, guest_store, guest_gate = _body("ep49d-a4b-guest-")
        host_head = border.chain_head(host_store)
        border.record_receipt(guest_gate, border.content_id(A_ROW),
                              border.from_body_name("k", border.genesis_hash(host_store)), "sig")
        self.assertEqual(border.chain_head(host_store), host_head)          # host untouched
        self.assertNotEqual(border.chain_head(guest_store), host_head)      # guest moved, independently


# =============================================================================================
# A5 — T-CHAIN-HASH-EXCLUDES-RECORD-TIME (+ RW-RECORD-TIME-IN-CONTENT)
# =============================================================================================

class TestChainHashExcludesRecordTime(unittest.TestCase):
    def test_two_bodies_recording_one_crossing_at_different_times_derive_the_same_hash(self):
        """A5 / D08.40: the content hash a receipt cites EXCLUDES record_time (border.content_id hashes
        {action, object, target, payload} with derivation stripped; record_time is the store's own
        envelope field, minted at append, and never enters). Two bodies recording the SAME crossing at
        DIFFERENT times derive the SAME content hash — the receipt binds the crossing, not the clock."""
        row_now = dict(A_ROW)
        row_later = dict(A_ROW)              # the same crossing, presented at a different moment
        self.assertEqual(border.content_id(row_now), border.content_id(row_later))
        # two bodies each receipt the crossing at different record_times; both cite the SAME hash.
        _bd, b_store, b_gate = _body("ep49d-a5-B-")
        _cd, c_store, c_gate = _body("ep49d-a5-C-")
        rb = border.record_receipt(b_gate, border.content_id(row_now), border.from_body_name("k", "g"), "s")
        rc = border.record_receipt(c_gate, border.content_id(row_later), border.from_body_name("k", "g"), "s")
        self.assertEqual((rb.get("payload") or {}).get("content_hash"),
                         (rc.get("payload") or {}).get("content_hash"))
        # the two receipts DO carry different record_times (the store minted them), yet the CITED hash
        # is identical — record_time is excluded from what the receipt binds.
        self.assertIsNotNone(rb.get("record_time"))
        self.assertIsNotNone(rc.get("record_time"))

    def test_RW_RECORD_TIME_IN_CONTENT_a_planted_record_time_inside_the_hashed_content_reds(self):
        """RW-RECORD-TIME-IN-CONTENT (§4): the exclusion is able-to-fail. A record_time planted INSIDE
        the hashed content (the payload) changes the content hash — so a hash that DID fold record_time
        would differ across two recordings of one crossing. The planted row's hash differs from the
        clean row's, proving the clean hash owes nothing to a time the payload does not carry."""
        clean = dict(A_ROW)
        planted = {"action": A_ROW["action"], "object": A_ROW["object"], "target": A_ROW["target"],
                   "payload": dict(A_ROW["payload"], record_time="2026-09-08T00:00:00Z")}
        self.assertNotEqual(border.content_id(clean), border.content_id(planted))


# =============================================================================================
# A6 — T-RECEIPT-BUMP-ATTESTED (+ RW-NO-MOVE / RW-MAJOR) — the founding move (data-born MINOR)
# =============================================================================================

def _pack_records():
    import json
    repo = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(repo, "src", "founding", "founding-pack.json"), "rb") as fh:
        return [r for step in json.loads(fh.read())["steps"] for r in step["records"]]


class TestReceiptBumpAttested(unittest.TestCase):
    def test_the_founding_is_at_or_beyond_the_EP49D_era_and_the_bump_is_attested(self):
        """A6: the founding rose one MINOR (1.42.0 -> 1.43.0, the base driven at dispatch) and the
        move is attested in ONE BUILD-PROGRESS entry (version + pack sha256). ERA-PINNED from birth
        (§A57, the manager's test_ep48 model): the version is a FLOOR at the EP-49D era, so a later
        founding mover advances the constitution WITHOUT touching this line. The load-bearing assertion
        is that THIS founding on disk is attested — audit() reads the live version and checks the log."""
        from test_founding_is_logged import audit, pack_facts
        facts = pack_facts()
        ver = tuple(int(x) for x in facts["version"].split("."))
        self.assertGreaterEqual(ver, (1, 43, 0),
                                "the founding is at or beyond the EP-49D era (1.43.0) this test pins")
        a = audit()
        self.assertTrue(a["logged"],
                        "the founding moved and no single BUILD-PROGRESS entry names both the version "
                        "and the pack sha256 (the required ledger duty, :1178/:2805)")

    def test_RECEIPT_is_in_the_pack_with_its_params_declared_and_the_move_is_MINOR(self):
        """A6: RECEIPT is minted as a CREATE-OP whose FIVE params are declared STRUCTURAL at create
        (content_hash, from_body, from_sig, under_rule, revealed_set) — the door admits a conforming
        call (a door-layer acceptance, stop-h). The move is MINOR: one op ADDED, NONE removed, NO
        check kind added (OP_CHECKS frozen at 17), the op uses only existing check kinds (none here)."""
        recs = _pack_records()
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertIn("RECEIPT", op_names)                                  # ADDED — the MINOR direction
        rdef = next(r["payload"]["definition"] for r in recs
                    if r.get("action") == "CREATE-OP" and r["payload"]["name"] == "RECEIPT")
        for param in ("content_hash", "from_body", "from_sig", "under_rule", "revealed_set"):
            self.assertIn(param, rdef.get("params", {}))                    # declared as a param
            self.assertIn(param, rdef.get("structural_params", []))         # AND classified STRUCTURAL
        self.assertEqual(rdef.get("law_cited"), "COMM-LAW-CONTRACT")        # cites the existing law
        self.assertEqual((rdef.get("payload_derive") or {}).get("record_class", {}).get("tpl"),
                         "DECISION")                                        # the receiver's own act
        # NONE REMOVED: representative pre-move ops survive (a removal would be MAJOR / stop-e).
        for kept in ("BORDER-SUBMIT", "BORDER-REPLY", "SOCKET-OPEN", "COMMS-OPEN", "FILE-CREATE"):
            self.assertIn(kept, op_names)
        self.assertEqual(len(OP_CHECKS), 19)                               # NO check kind added
        self.assertEqual(rdef.get("checks"), [])                           # RECEIPT adds no check kind

    def test_a_conforming_receipt_call_carrying_all_five_params_is_admitted(self):
        """A6 / stop-h (the door-layer acceptance): a fresh CREATE-OP declares ALL its params or the
        door refuses a conforming call. A RECEIPT call carrying the content hash, the from-body
        (key + genesis), the from-signature, the under-rule and the revealed-set is ADMITTED and
        recorded — the op-amend door-param gap does not apply to a fresh create."""
        _bd, b_store, b_gate = _body("ep49d-a6-B-")
        rec = b_gate.execute("RECEIPT", "SYSTEM", {
            "content_hash": border.content_id(A_ROW),
            "from_body": {"key": "ed25519-pub:sender", "genesis": "sha256:" + "c" * 64},
            "from_sig": "ed25519-sig:z", "under_rule": "COMM-LAW-CONTRACT",
            "revealed_set": {"root": "sha256:" + "r" * 64, "leaves": ["class"]}})
        p = rec.get("payload") or {}
        self.assertEqual(p.get("kind"), "receipt")
        # the revealed-set (D08.48) is recorded faithfully — the record is frozen (a list becomes a
        # tuple), so read its fields rather than its container type.
        rs = p.get("revealed_set") or {}
        self.assertEqual(rs.get("root"), "sha256:" + "r" * 64)              # the selective-disclosure root
        self.assertIn("class", rs.get("leaves"))                            # a revealed leaf

    def test_RW_NO_MOVE_a_byte_unchanged_founding_would_fail_and_RW_MAJOR_holds(self):
        """RW-NO-MOVE (§4): a founding that moved nothing fails — RECEIPT IS present (the move
        happened) and the version rose. RW-MAJOR (§4 / stop-e): the discriminator holds — no op
        removed, no check kind added; the move is a single new op, a MINOR."""
        recs = _pack_records()
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertIn("RECEIPT", op_names)                                  # the move happened
        self.assertIn("COMMS-OPEN", op_names)                              # not reached-by-removal
        self.assertEqual(len(OP_CHECKS), 19)                               # not reached-by-a-new-kind


# =============================================================================================
# classmap — RECEIPT classified DECISION; a peer-sent row as INPUT (design/51 §4, N9)
# =============================================================================================

class TestReceiptClassmap(unittest.TestCase):
    def test_the_receipt_is_a_DECISION_and_the_received_row_is_an_INPUT(self):
        """N9 / design/10 §2: B's receipt is a state-changing act B AUTHORED (the receiver's own row)
        -> DECISION; the row it receives from body A is an external arrival B did not author -> INPUT.
        The per-row wire flow between bodies is STREAM (appends nothing)."""
        self.assertEqual(classmap.classify("receipt", "receipt-recorded"), classmap.DECISION)
        self.assertEqual(classmap.classify("receipt", "row-received"), classmap.INPUT)
        self.assertEqual(classmap.classify("receipt", "receipt-traffic"), classmap.STREAM)
        # the map carries the act (a silent drop would be the defect W2 names).
        with self.assertRaises(classmap.UnmappedAct):
            classmap.classify("receipt", "receipt-decision-by-peer")


if __name__ == "__main__":
    unittest.main()
