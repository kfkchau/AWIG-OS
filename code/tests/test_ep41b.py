# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (blob store, custody transfer, handover ceremony, departure view); NON-GOAL: no
# offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-41B (BUILD) — the HANDOVER ceremony + the departure record (design/46 members 3-4).

RE-AUTHORED on the owner's fourth word (board :2856): there is NO delete function, and the
vocabulary will never contain one — CAPABILITY-ABSENCE. The one removal function is a HANDOVER:
duplicate the subject chain, verify byte-to-byte, receive the receiving hand's SIGNED received-
custody receipt, THEN remove the local bytes line-by-line (each verified), and stand a DEPARTURE
record forever. Every probe here is a regression test (the campaign method: a verification probe
lands as a test). The A1-A7 battery runs in DISPOSABLE worlds on TEST blobs; nothing real is handed
over. Production compose (build_full_kernel) now REGISTERS the ceremony live via a CODE registration
(members 3-4, board :2972) — the founding pack is byte-untouched (no bump); A6 proves that flip. The
battery proves, in disposable stores:

  A1  TestNoStandaloneDelete   NO op, ceremony, or primitive removes content bytes WITHOUT a
                               completed verified transfer. There is no `destroy` on the store; the
                               only removal method (`hand_off`) refuses without a receipt naming the
                               content; the handover op removes NOTHING without a valid signed
                               receipt. Capability-absence, driven both directions (RW1).
  A2  TestHandoverCeremony     the ceremony performs IN ORDER: duplicate -> verify byte-to-byte ->
                               the receiving hand's signed receipt -> line-by-line verified removal
                               -> the departure record. A missing or unverified step HALTS before
                               any byte is removed.
  A3  TestReceiptGatesRemoval  no local byte is removed until the signed receipt is present and
                               verifies; a ceremony without a valid receipt removes NOTHING, the
                               bytes stay, custody stays here. Driven able to pass AND fail (RW2).
  A4  TestDepartureView        after a completed handover, files.py / replay_snapshot.py /
                               kernel_port.py each answer with the DEPARTURE marker (not the bytes,
                               not empty, not a crash) — at ALL THREE sites; the departure ledger
                               names what/to-whom/when/rule/receipt. A non-departed sibling still
                               returns its real bytes at all three (RW4). Records untouched; replay
                               reproduces the departed state.
  A5  TestRecordsUntouchable   the handover moves/removes only content BYTES, never a record
                               (authority is never orphaned); a target that is a record refuses at
                               the op's own definition (RW3). Scope is full OR partial (per-blob).
  A6  TestEP41BCeremonyLiveInProduction  MEMBERS 3-4 FLIPPED LIVE (board :2972): compose.build_full_
                               kernel now REGISTERS the handover ceremony, so the family is LIVE in
                               production (gate.has HANDOVER-CUSTODY). The flip moves NO founding —
                               register_ceremony is a CODE registration (the register_attestation
                               precedent), so founding-pack.json is byte-untouched and declares no
                               handover member (no bump); build_kernel, the founding path, still never
                               registers it. A planted pack family reds the no-bump guard (RW-F).
                               tests/era_pin.py byte-untouched (the §A57 sweep is a separate deliverable).
  A7  TestRoundTrip            the departure killed and replayed identically from the record ALONE;
                               no record moves. (Whole-ledger green is the suite discover, the
                               verifier's re-run.)

  §8 near-miss controls        the crypto-shred / soft-delete trap (§8-i): the removal tail TRULY
                               removes the bytes; no new check kind forced (§8-h); no schedule
                               automation (§8-j).

EP-41B'S CEREMONY IS NOW LIVE IN PRODUCTION VIA A CODE REGISTRATION (members 3-4, board :2972).
compose.build_full_kernel calls register_ceremony, which self-gates on gate.blobs (present at full
compose) and registers the HANDOVER-CUSTODY op — exactly the register_attestation precedent
(compose.py:71). This moves NO founding: register_ceremony is a CODE registration, so
src/founding/founding-pack.json is byte-untouched (no version bump) and carries no handover-family
member; build_kernel, the founding path, still never registers the ceremony and stays pack-exact and
inert. The handover op blob-homes its content by hash and cites only the hash in the departure record
(RULING-1: no content-carrying field is structural). The A1-A7 battery proves the ceremony's
BEHAVIOUR in disposable TEST founding worlds (the handover law declared, the op registered, a TEST
key signing the TEST receipt); A6 proves the production REGISTRATION flip. HONEST CAP: a departure
record cites HANDOVER-LAW-GS13; that law citation is exercised in the TEST worlds, and a production
handover would additionally cite it at EXECUTION — a downstream concern the registration flip does
not settle and does not need to (as with attestation, the registration lands the capability; nothing
hands over at boot, so no law is cited at compose).
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # so `import era_pin` resolves
from kernel.boot import build_kernel                              # noqa: E402
from kernel.compose import build_full_kernel                      # noqa: E402  (A6: the compose-flip)
from kernel.blobs import BlobStore                                # noqa: E402
from kernel import erasure, keys                                  # noqa: E402
from kernel.gate import make_invoker_sig                          # noqa: E402
from kernel.errors import OpError                                 # noqa: E402
from subsystems.files import FilesView                            # noqa: E402
from bridge.kernel_port import KernelPort                         # noqa: E402
from bridge import replay_snapshot                                # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
ERA_PIN_PATH = os.path.join(REPO, "tests", "era_pin.py")

RECEIVER = "the-receiving-archive"                # the hand custody departs TO
RECEIVER_KEY = "testpub:receiving-archive:v1"     # TEST key material — nothing real minted


# ============================================================================================
# TEST FOUNDING WORLD — a disposable kernel where the handover LAW is declared, the ceremony op
# registered, and the RECEIVER holds a bound key (so its receipt can verify). This models "the
# founding moved" WITHOUT touching the production pack (A6 asserts it byte-untouched); the held
# create rides the owner's mover.
# ============================================================================================

def _declare_handover_law(store):
    """Declare the handover LAW in a test world — a CREATE-RULE, appended directly (as genesis
    appends the constitution directly), the test-world stand-in for the held founding create."""
    store._append({
        "actor": "SYSTEM", "action": "CREATE-RULE", "object": erasure.HANDOVER_LAW,
        "rule_cited": "BOOT-INT",
        "payload": {"kind": "rule", "rule_id": erasure.HANDOVER_LAW, "root": True, "polarity": "+",
                    "text": "handover: on a lawful removal demand, custody of content-addressed blob "
                            "bytes is transferred to a receiving hand under a signed received-custody "
                            "receipt, the local bytes are then removed, and a departure record stands; "
                            "it never touches a record and there is no standalone delete"},
    })


class HandoverWorld(unittest.TestCase):
    """A disposable test founding world: the handover law declared, the ceremony registered, and a
    receiver key bound (the receipt's signature verifies under it)."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.blobdir = os.path.join(self._dir, "blobs")
        self.blobs = BlobStore(self.blobdir)
        self.store, self.gate, self.views = build_kernel(self.path, blobs=self.blobs)
        _declare_handover_law(self.store)
        self.assertTrue(erasure.register_ceremony(self.gate, self.views))   # blobs present -> registers
        self._bind_key(RECEIVER, RECEIVER_KEY)
        self.assertEqual(keys.bound_key(self.store, RECEIVER), RECEIVER_KEY)  # the receipt can verify

    # --- record-plane helpers -----------------------------------------------------------------
    def _bind_key(self, account, public_key):
        """Bind a verification key to `account`, appended directly (the test-world stand-in for the
        key-bind ceremony) so keys.bound_key reads it — the prerequisite that makes a receipt
        provable (EP-36). NOT re-implementing EP-36's fold; only feeding it a record."""
        self.store._append({
            "actor": "SYSTEM", "action": "KEY-BIND", "object": account,
            "rule_cited": "BOOT-INT",
            "payload": {"kind": keys.KEY_BIND, keys.ACCOUNT: account, keys.PUBLIC_KEY: public_key,
                        keys.CLASS: "LAW"},
        })

    def _write_file(self, path, content):
        """Put a blob and record a FILE-CREATE + FILE-WRITE naming it — the record plane a content
        view reads. Appended directly (the test-world stand-in for the files ops), like the law."""
        h = self.blobs.put(content)
        self.store._append({"actor": "owner", "action": "FILE-CREATE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "node_type": "file", "perm": "644"}})
        self.store._append({"actor": "owner", "action": "FILE-WRITE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "content_hash": h, "length": len(content)}})
        return h

    def _signed_receipt(self, chain_copy_hash, receiver=RECEIVER, receiver_key=RECEIVER_KEY,
                        rule="RET-GDPR-1"):
        """The receiving hand's SIGNED received-custody receipt (actor = receiver, action =
        received-custody, object = the chain-copy hash), signed with the receiver's key — the shape
        `erasure._receipt_verifies` checks. A real receiving hand produces this outside this system;
        here a test key stands in for it."""
        body = {"action": erasure.RECEIVED_CUSTODY, "object": chain_copy_hash,
                "target": None, "payload": {"rule": rule}}
        receipt = dict(body)
        receipt["actor"] = receiver
        receipt[erasure.INVOKER_SIG] = make_invoker_sig(receiver_key, body)
        return receipt

    def _handover(self, target, receiver=RECEIVER, receiver_key=RECEIVER_KEY, rule="RET-GDPR-1",
                  receipt="__auto__"):
        """Invoke the handover ceremony. The chain-copy hash is the blob's own hash (content
        addressing: the duplicate is proven identical by hash IDENTITY)."""
        if receipt == "__auto__":
            receipt = self._signed_receipt(target, receiver, receiver_key, rule)
        params = {"target_hash": target, "receiver": receiver, "retention_rule": rule}
        if receipt is not None:
            params["receipt"] = receipt
        return self.gate.execute(erasure.HANDOVER_OP, "owner", params)


# ============================================================================================
# A1 — NO STANDALONE DELETE (capability-absence). No byte leaves without a completed verified
#      transfer — driven both directions (RW1).
# ============================================================================================

class TestNoStandaloneDelete(HandoverWorld):

    def test_a1_the_store_has_no_destroy_function_at_all(self):
        # The standalone delete is GONE from the surface AND the source. There is no `destroy`.
        self.assertFalse(hasattr(BlobStore, "destroy"))
        with open(os.path.join(REPO, "src", "kernel", "blobs.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("def destroy(", src,
                         "blobs.py declares a standalone destroy — capability-absence is the whole point")

    def test_a1_the_removal_tail_refuses_without_a_receipt(self):
        # RW1: the ONLY removal method refuses a call with no receipt covering the hash — a bare
        # removal is impossible. The bytes stay.
        h = self.blobs.put(b"content that cannot be removed by a bare call")
        with self.assertRaises(ValueError):
            self.blobs.hand_off([h], None)                         # no receipt
        self.assertTrue(self.blobs.has(h))                         # nothing removed
        with self.assertRaises(ValueError):
            self.blobs.hand_off([h], {"object": "sha256:some-other-hash"})  # receipt names other content
        self.assertTrue(self.blobs.has(h))                         # still nothing removed

    def test_a1_the_handover_op_removes_nothing_without_a_valid_receipt(self):
        # The op-level capability-absence: the ONE removal op removes NOTHING when the receipt is
        # absent — custody stays, no departure record is written.
        h = self._write_file("/f", b"content the ceremony must not remove without a receipt")
        n_before = len(self.store.all())
        with self.assertRaises(OpError):
            self._handover(h, receipt=None)
        self.assertTrue(self.blobs.has(h))                         # the bytes are still here
        self.assertEqual(erasure.departed_hashes(self.store.all()), set())  # nothing departed

    def test_a1_rw1_the_capability_exists_only_through_the_verified_transfer(self):
        # The can-PASS direction (a check that cannot fail is not a check): with a covering receipt
        # the removal tail works, and the full ceremony with a valid signed receipt removes the
        # bytes. The capability is real — but ONLY through the verified transfer.
        h = self._write_file("/f", b"content handed over lawfully")
        self.assertTrue(self.blobs.has(h))
        self._handover(h)                                          # valid signed receipt
        self.assertFalse(self.blobs.has(h))                        # the bytes departed
        self.assertIn(h, erasure.departed_hashes(self.store.all()))


# ============================================================================================
# A2 — the handover completes IN ORDER; a missing/unverified step halts before any removal.
# ============================================================================================

class TestHandoverCeremony(HandoverWorld):

    def test_a2_a_completed_handover_produces_the_departure_and_removes_the_bytes(self):
        secret = b"personal data older than N years"
        h = self._write_file("/f", secret)
        self._handover(h, rule="RET-GDPR-ART17")
        dep = self.store.events[-1]                                # the departure record
        p = dep["payload"]
        self.assertEqual(p["kind"], erasure.DEPARTURE_RECORD)              # a departure record
        self.assertEqual(p[erasure.TARGET_HASH], h)                       # WHAT, by hash
        self.assertEqual(p[erasure.RECEIVER], RECEIVER)                   # TO WHOM
        self.assertEqual(p[erasure.RETENTION_RULE], "RET-GDPR-ART17")     # WHICH rule
        self.assertEqual(p[erasure.RECEIPT_CITED]["chain_copy_hash"], h)  # RECEIPT cited (by hash)
        self.assertIsNotNone(dep.get("seq"))                             # WHEN (minted seq ...
        self.assertIsNotNone(dep.get("record_time"))                    # ... and record_time)
        self.assertFalse(self.blobs.has(h))                              # the local bytes are gone

    def test_a2_the_duplicate_verify_step_halts_before_any_removal(self):
        # STEP 1-2: a subject whose local bytes are ABSENT cannot be duplicated-and-verified, so the
        # ceremony HALTS before any removal (nothing is handed over as if whole). It is a content
        # hash (passes cannot-orphan), so the refusal is the duplicate-verify halt, not the record guard.
        absent = "sha256:" + hashlib.sha256(b"never stored locally").hexdigest()
        with self.assertRaises(OpError) as cm:
            self._handover(absent, receipt=self._signed_receipt(absent))
        self.assertEqual(cm.exception.rule, erasure.HANDOVER_ANCHOR)
        self.assertNotIn(absent, erasure.departed_hashes(self.store.all()))  # no departure written

    def test_a2_a_byte_to_byte_mismatch_halts_before_any_removal(self):
        # STEP 1-2 (the mismatch direction, RW-class): corrupt the stored blob so its bytes no longer
        # recompute to the named hash. duplicate_and_verify catches it and the ceremony halts — the
        # (corrupt) bytes are NOT removed and no departure is written.
        secret = b"content that will be corrupted on disk"
        h = self._write_file("/f", secret)
        digest = h.split(":", 1)[1]
        blobpath = os.path.join(self.blobdir, digest[:2], digest[2:])
        with open(blobpath, "wb") as fh:
            fh.write(b"tampered bytes that do not hash to h")     # a byte-to-byte mismatch
        with self.assertRaises(OpError) as cm:
            self._handover(h)
        self.assertEqual(cm.exception.rule, erasure.HANDOVER_ANCHOR)
        self.assertTrue(os.path.exists(blobpath))                 # the bytes were NOT removed
        self.assertNotIn(h, erasure.departed_hashes(self.store.all()))

    def test_a2_duplicate_and_verify_is_a_reusable_free_function(self):
        # §8-i (shared machinery with EP-43): the duplicate+verify is a free function, not walled
        # into the handler, so the recover direction can call it. It returns the chain-copy hash on
        # a match and raises on a mismatch — a check that can fail.
        h = self.blobs.put(b"reusable duplicate-and-verify")
        self.assertEqual(erasure.duplicate_and_verify(self.blobs, h), h)   # verifies
        with self.assertRaises(erasure.HandoverHalt):
            erasure.duplicate_and_verify(self.blobs, "sha256:" + "0" * 64)  # absent -> halts


# ============================================================================================
# A3 — the receipt GATES removal; no receipt, no removal, custody stays (RW2).
# ============================================================================================

class TestReceiptGatesRemoval(HandoverWorld):

    def test_a3_no_receipt_removes_nothing(self):
        h = self._write_file("/f", b"content whose custody stays without a receipt")
        with self.assertRaises(OpError) as cm:
            self._handover(h, receipt=None)
        self.assertEqual(cm.exception.rule, erasure.HANDOVER_ANCHOR)
        self.assertTrue(self.blobs.has(h))                         # the bytes stay
        self.assertNotIn(h, erasure.departed_hashes(self.store.all()))

    def test_a3_a_receipt_for_a_different_hash_removes_nothing(self):
        # The receipt must name EXACTLY the chain-copy hash the duplicate produced. A receipt for
        # OTHER content does not gate THIS removal.
        h = self._write_file("/f", b"the subject content")
        other = "sha256:" + hashlib.sha256(b"some other chain").hexdigest()
        with self.assertRaises(OpError):
            self._handover(h, receipt=self._signed_receipt(other))   # names the wrong hash
        self.assertTrue(self.blobs.has(h))

    def test_a3_a_receipt_from_the_wrong_receiver_removes_nothing(self):
        # The receipt's actor must be the named receiver. A receipt whose actor is someone else does
        # not verify (the signed body / actor mismatch), so removal is refused.
        h = self._write_file("/f", b"content")
        forged = self._signed_receipt(h, receiver="an-impostor", receiver_key=RECEIVER_KEY)
        with self.assertRaises(OpError):
            self._handover(h, receipt=forged)                      # actor != named receiver
        self.assertTrue(self.blobs.has(h))

    def test_a3_a_receipt_signed_with_the_wrong_key_removes_nothing(self):
        # The signature must verify under the RECEIVER's bound key. A receipt signed with a key that
        # is not the receiver's binding fails verification — custody stays.
        h = self._write_file("/f", b"content")
        wrong_key_receipt = self._signed_receipt(h, receiver=RECEIVER,
                                                 receiver_key="testpub:not-the-bound-key:v9")
        with self.assertRaises(OpError):
            self._handover(h, receipt=wrong_key_receipt)
        self.assertTrue(self.blobs.has(h))

    def test_a3_a_receiver_with_no_bound_key_cannot_receive(self):
        # RW2 (the unbound-receiver direction): custody cannot depart to a hand this system cannot
        # name. A receiver with no bound key produces no verifiable receipt — removal refused.
        h = self._write_file("/f", b"content")
        unbound = self._signed_receipt(h, receiver="a-nameless-hand", receiver_key="testpub:x")
        with self.assertRaises(OpError):
            self._handover(h, receiver="a-nameless-hand", receipt=unbound)
        self.assertTrue(self.blobs.has(h))

    def test_a3_a_valid_receipt_gates_the_removal_open(self):
        # RW2 (the can-PASS direction): with the receiver's valid signed receipt, the removal
        # proceeds and the bytes depart. The gate can open — it is a real gate, not a wall.
        h = self._write_file("/f", b"content handed over under a valid receipt")
        self.assertTrue(self.blobs.has(h))
        self._handover(h)
        self.assertFalse(self.blobs.has(h))                        # the receipt opened the gate

    def test_a3_the_refusal_is_recorded(self):
        # A refusal is itself a recorded event (the estate's refuse idiom) — the record never goes dark.
        h = self._write_file("/f", b"content")
        with self.assertRaises(OpError):
            self._handover(h, receipt=None)
        refusals = [e for e in self.store.all() if e.get("refused")]
        self.assertTrue(any(e.get("rule_cited") == erasure.HANDOVER_ANCHOR for e in refusals))


# ============================================================================================
# A4 — the DEPARTURE, answered at all three content-resolving sites (RW4); the departure ledger.
# ============================================================================================

class TestDepartureView(HandoverWorld):

    def test_a4_files_view_answers_the_departure_not_the_bytes_not_a_crash(self):
        secret = b"secret file content"
        h = self._write_file("/f", secret)
        fv = FilesView(self.store, self.blobs)
        self.assertEqual(fv.content_at("/f"), secret)              # before: the real bytes
        self._handover(h)
        answer = fv.content_at("/f")                               # after: the departure (no crash)
        self.assertTrue(erasure.is_departed(answer))
        self.assertNotEqual(answer, secret)

    def test_a4_replay_snapshot_answers_the_departure(self):
        secret = b"secret replayed content"
        h = self._write_file("/e", secret)
        before = replay_snapshot.snapshot(self.path, self.blobdir, root="/")
        self.assertEqual(before["e"]["sha256"], hashlib.sha256(secret).hexdigest()[:16])
        self._handover(h)
        after = replay_snapshot.snapshot(self.path, self.blobdir, root="/")
        self.assertEqual(after["e"]["sha256"], hashlib.sha256(erasure.DEPARTURE).hexdigest()[:16])
        self.assertEqual(after["e"]["size"], len(erasure.DEPARTURE))

    def test_a4_kernel_port_fill_content_answers_the_departure(self):
        secret = b"secret port content"
        h = self._write_file("/p", secret)
        port = KernelPort(self.store, self.gate, self.views, self.blobs)
        self.assertEqual(port._fill_content({"hash": h})[2], secret)   # before: the real bytes
        self._handover(h)
        errno_, meta, data = port._fill_content({"hash": h})           # after: the departure (no crash)
        self.assertEqual(errno_, 0)
        self.assertTrue(erasure.is_departed(data))

    def test_a4_rw4_a_non_departed_sibling_still_returns_its_bytes_at_all_three(self):
        # The departure DISCRIMINATES: it fires for the handed-over hash and no other. A kept file's
        # bytes are unchanged at every site (RW4's near-miss — nothing else changes).
        gone = self._write_file("/e", b"the departed one")
        kept_bytes = b"the kept one"
        kept = self._write_file("/k", kept_bytes)
        self._handover(gone)
        fv = FilesView(self.store, self.blobs)
        self.assertEqual(fv.content_at("/k"), kept_bytes)              # files.py: kept
        self.assertTrue(erasure.is_departed(fv.content_at("/e")))      # files.py: departed
        port = KernelPort(self.store, self.gate, self.views, self.blobs)
        self.assertEqual(port._fill_content({"hash": kept})[2], kept_bytes)   # kernel_port: kept
        self.assertTrue(erasure.is_departed(port._fill_content({"hash": gone})[2]))
        snap = replay_snapshot.snapshot(self.path, self.blobdir, root="/")
        self.assertEqual(snap["k"]["sha256"], hashlib.sha256(kept_bytes).hexdigest()[:16])   # replay: kept
        self.assertEqual(snap["e"]["sha256"], hashlib.sha256(erasure.DEPARTURE).hexdigest()[:16])

    def test_a4_the_departure_ledger_names_what_to_whom_when_rule_receipt(self):
        h1 = self._write_file("/a", b"one")
        h2 = self._write_file("/b", b"two")
        self._handover(h1, rule="RET-A")
        self._handover(h2, rule="RET-B")
        ledger = erasure.departure_ledger(self.store.all())
        self.assertEqual(len(ledger), 2)
        by_hash = {row[erasure.TARGET_HASH]: row for row in ledger}
        self.assertEqual(by_hash[h1][erasure.RETENTION_RULE], "RET-A")   # WHICH rule
        self.assertEqual(by_hash[h2][erasure.RECEIVER], RECEIVER)        # TO WHOM
        self.assertEqual(by_hash[h1][erasure.RECEIPT_CITED]["chain_copy_hash"], h1)  # RECEIPT cited
        self.assertIsNotNone(by_hash[h1]["seq"])                         # WHEN

    def test_a4_the_ledger_reveals_the_act_and_the_hand_never_the_content(self):
        secret = b"the departed content"
        h = self._write_file("/f", secret)
        self._handover(h)
        # `default=dict` reinflates the store's frozen mappingproxy payloads for the serialize-and-scan
        # (the same idiom the shell tests used); the check is that the handed-over bytes are nowhere in it.
        serialized = json.dumps(erasure.departure_ledger(self.store.all()), default=lambda o: dict(o))
        self.assertNotIn(secret.decode(), serialized)

    def test_a4_inert_before_any_ceremony_the_views_answer_the_bytes(self):
        # The wire-at-birth safety: with no departure record the departed set is empty and every view
        # is exactly what it was before this EP.
        secret = b"never handed over"
        h = self._write_file("/f", secret)
        fv = FilesView(self.store, self.blobs)
        self.assertEqual(fv.content_at("/f"), secret)
        self.assertEqual(erasure.departed_hashes(self.store.all()), set())

    def test_a4_asof_before_the_ceremony_reproduces_the_departed_state(self):
        # design/23 Option C: a read as-of BEFORE the ceremony reproduces the DEPARTED state — the
        # record replays fully (the FILE-WRITE is still found), the view answers the departure,
        # because the local bytes are a fact of the physical NOW.
        secret = b"content that will depart"
        h = self._write_file("/f", secret)
        before_seq = self.store.events[-1]["seq"]
        fv = FilesView(self.store, self.blobs)
        self.assertEqual(fv.content_at("/f", as_of=before_seq), secret)   # pre-ceremony: the bytes
        self._handover(h)
        self.assertTrue(erasure.is_departed(fv.content_at("/f", as_of=before_seq)))  # now: departed
        self.assertTrue(erasure.is_departed(fv.content_at("/f")))                    # and live, identically


# ============================================================================================
# A5 — records are UNTOUCHABLE; cannot-orphan (RW3); full or partial (per-blob) scope.
# ============================================================================================

class TestRecordsUntouchable(HandoverWorld):

    def test_a5_the_record_is_untouched_the_write_still_stands(self):
        # The handover removes only content BYTES; the FILE-WRITE that named the departed content is
        # STILL in the record after the ceremony (only the bytes departed). The departure is derived.
        secret = b"content"
        h = self._write_file("/f", secret)
        writes_before = [e for e in self.store.all() if e["action"] == "FILE-WRITE"]
        self._handover(h)
        writes_after = [e for e in self.store.all() if e["action"] == "FILE-WRITE"]
        self.assertEqual(len(writes_after), len(writes_before))        # no record moved
        self.assertEqual(writes_after[-1]["payload"]["content_hash"], h)  # the hash still stands

    def test_a5_rw3_a_handover_targeting_a_record_refuses_at_the_ops_own_definition(self):
        # RW3 / cannot-orphan: a target that is not a content hash — a record reference of any shape
        # — refuses. Authority is derived from records; this op can never name one, so it can never
        # orphan authority (records are untouchable).
        for record_ish in ("rec_5", "5", "/some/path", "seq:42"):
            with self.assertRaises(OpError) as cm:
                self._handover(record_ish, receipt=self._signed_receipt(record_ish))
            self.assertEqual(cm.exception.rule, erasure.HANDOVER_ANCHOR)
            self.assertIn("record", str(cm.exception).lower())

    def test_a5_the_check_can_fail_a_content_hash_target_passes(self):
        # The discrimination direction: a genuine content hash is accepted and its bytes depart.
        h = self.blobs.put(b"real content")
        self.assertTrue(self.blobs.has(h))
        self._handover(h)                                              # no refusal
        self.assertFalse(self.blobs.has(h))                           # the bytes departed

    def test_a5_partial_scope_hand_over_one_blob_the_siblings_stay(self):
        # Scope is FULL or PARTIAL — content addressing gives the granularity. Hand over one blob;
        # a sibling blob is untouched, its view still answers its bytes.
        gone = self._write_file("/gone", b"the one handed over")
        kept_bytes = b"the one kept"
        kept = self._write_file("/kept", kept_bytes)
        self._handover(gone)
        self.assertFalse(self.blobs.has(gone))                        # departed
        self.assertTrue(self.blobs.has(kept))                         # kept — partial scope
        self.assertEqual(FilesView(self.store, self.blobs).content_at("/kept"), kept_bytes)

    def test_a5_full_scope_hand_over_every_blob_of_a_subject(self):
        # FULL scope: hand over each of a subject's blobs (per-blob ceremonies). All depart; each
        # departure stands as its own record.
        a = self._write_file("/s/a", b"subject file a")
        b = self._write_file("/s/b", b"subject file b")
        self._handover(a)
        self._handover(b)
        self.assertFalse(self.blobs.has(a))
        self.assertFalse(self.blobs.has(b))
        self.assertEqual(erasure.departed_hashes(self.store.all()), {a, b})


# ============================================================================================
# A6 — MEMBERS 3-4 FLIPPED LIVE: compose registers the ceremony; founding pack byte-untouched (RW-F).
# ============================================================================================

def _pack_handover_family_present(text):
    """Does the founding text carry ANY member of the handover family? The mechanical NO-BUMP signal —
    OWN vocabulary, direct, never a founding byte/version proxy (G1b entry-scoped, architect :2866).
    Under the live flip a member in the pack would be a version bump; the family rides CODE, not pack."""
    return any(tok in text for tok in
               (erasure.DEPARTURE_RECORD, erasure.HANDOVER_OP, erasure.HANDOVER_LAW,
                erasure.RECEIVED_CUSTODY))


class TestEP41BCeremonyLiveInProduction(unittest.TestCase):
    """MEMBERS 3-4 FLIPPED LIVE (board :2972). The handover ceremony is now IN production:
    compose.build_full_kernel REGISTERS the HANDOVER-CUSTODY op (register_ceremony self-gates on
    gate.blobs, present at full compose), so the handover family is LIVE in every full-kernel world —
    gate.has(HANDOVER-CUSTODY). The flip moves NO founding: register_ceremony is a CODE registration,
    exactly like register_attestation (compose.py:71), so founding-pack.json is byte-untouched and
    declares no handover-family member (a pack CREATE-OP would have been a version bump; this is not).
    And build_kernel, the founding path, STILL never registers it: the ceremony rides build_full_kernel
    alone; build_kernel stays pack-exact and inert."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.blobdir = os.path.join(self._dir, "blobs")

    def test_members_3_4_compose_registers_the_ceremony_live(self):
        # THE FLIP, DRIVEN: production compose now registers the handover ceremony. Before this EP's
        # compose edit this assertion REDS (build_full_kernel did not register it); after, it is live.
        # WHAT BECAME TRUE: gate.has(HANDOVER-CUSTODY) in every full-kernel world.
        _store, gate, _views, _blobs, _subs = build_full_kernel(self.path, self.blobdir)
        self.assertTrue(gate.has(erasure.HANDOVER_OP),
                        "production compose.build_full_kernel must register the handover ceremony "
                        "(members 3-4 flip live)")

    def test_the_founding_path_build_kernel_never_registers_the_ceremony(self):
        # R1-twin (mirrors test_ep40.test_build_kernel_the_founding_path_never_attests): the ceremony
        # rides the COMPOSE layer, never the founding boot. build_kernel stays pack-exact and inert —
        # no handover op registered, every departure view empty.
        _store, gate, _views = build_kernel(self.path)
        self.assertFalse(gate.has(erasure.HANDOVER_OP),
                         "the founding path must not register the ceremony — it rides build_full_kernel only")

    def test_the_flip_moves_no_founding_the_pack_declares_no_handover_family(self):
        # THE NO-BUMP GUARD, recast for the live state: the family is live via CODE, so the founding
        # pack carries NO handover-family member (byte-untouched) — register_ceremony is a code
        # registration, not a pack CREATE-OP. Driven able to fail: a planted family member REDS it.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        self.assertFalse(_pack_handover_family_present(real),
                         "the flip is a CODE registration; the founding pack must carry no handover family (no bump)")
        planted = real + '\n{"kind":"op","name":"%s"}' % erasure.HANDOVER_OP
        self.assertTrue(_pack_handover_family_present(planted))        # the no-bump guard can still fail

    def test_a6_era_pin_is_byte_untouched(self):
        # The §A57 era-pin sweep is a SEPARATE deliverable, not this compose-flip; era_pin bytes stand.
        with open(ERA_PIN_PATH, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, "19ebf106bcdd82753d46b5eb34146ee31c04e909dd9458b376e0271a4236eb87",
                         "tests/era_pin.py bytes changed — the §A57 sweep is not part of this compose-flip")


# ============================================================================================
# A7 — round-trip: the departure killed and replayed identically from the record alone.
# ============================================================================================

class TestRoundTrip(HandoverWorld):

    def test_a7_the_departure_replays_identically_from_the_record_alone(self):
        # Hand over a blob, then KILL the derived state and rebuild the kernel from the same record
        # file. The departure is DERIVED from the departure record, so replay reconstructs it
        # identically — no record moved, no byte returned.
        secret = b"content for the round trip"
        h = self._write_file("/f", secret)
        self._handover(h)
        before = FilesView(self.store, self.blobs).content_at("/f")
        self.assertTrue(erasure.is_departed(before))

        store2, gate2, views2 = build_kernel(self.path, blobs=self.blobs)   # kill derived state, replay
        after = FilesView(store2, self.blobs).content_at("/f")
        self.assertTrue(erasure.is_departed(after))
        self.assertEqual(before, after)
        self.assertIn(h, erasure.departed_hashes(store2.all()))            # departed from the record alone

    def test_a7_post_ceremony_replay_from_the_record_alone_is_identical(self):
        secret = b"content to replay"
        h = self._write_file("/f", secret)
        self._handover(h)
        first = replay_snapshot.snapshot(self.path, self.blobdir, root="/")
        second = replay_snapshot.snapshot(self.path, self.blobdir, root="/")   # a fresh, independent read
        self.assertEqual(first, second)
        self.assertEqual(first["f"]["sha256"], hashlib.sha256(erasure.DEPARTURE).hexdigest()[:16])

    def test_a7_no_record_moves_across_the_ceremony(self):
        secret = b"content"
        h = self._write_file("/f", secret)
        seqs_before = [e["seq"] for e in self.store.all()]
        self._handover(h)
        seqs_after = [e["seq"] for e in self.store.all()]
        self.assertEqual(seqs_after[:len(seqs_before)], seqs_before)   # the prefix is untouched (append-only)
        self.assertEqual(len(seqs_after), len(seqs_before) + 1)        # exactly one record added: the departure


# ============================================================================================
# §8 near-miss controls — the trap (§8-i), no new check kind (§8-h), no schedule automation (§8-j).
# ============================================================================================

class TestTheTrapAndBoundaries(HandoverWorld):

    def test_8i_the_removal_tail_truly_removes_the_bytes_never_crypto_shred_or_soft_delete(self):
        # THE LOAD-BEARING TRAP: a removal that left the bytes (crypto-shred) or only removed them
        # from view (soft-delete) is NOT this act. After the handover the bytes must be physically
        # gone from the store.
        secret = b"bytes that must actually leave"
        h = self._write_file("/f", secret)
        self.assertTrue(self.blobs.has(h))
        self._handover(h)
        self.assertFalse(self.blobs.has(h))                            # has() no longer finds it
        with self.assertRaises(FileNotFoundError):
            self.blobs.get(h)                                          # the bytes are not on disk anywhere
        digest = h.split(":", 1)[1]
        self.assertFalse(os.path.exists(os.path.join(self.blobdir, digest[:2], digest[2:])))

    def test_8i_the_removal_tail_is_keyspace_guarded_a_non_content_hash_raises(self):
        # The removal tail refuses anything but a content hash, by its own keyspace — the structural
        # half of cannot-orphan (a record is not content-addressed, so it can never be handed to it).
        for bad in ("rec_5", "not-a-hash", "", 42, None):
            receipt = {"object": bad}
            with self.assertRaises(ValueError):
                self.blobs.hand_off([bad], receipt)

    def test_8i_the_removal_tail_is_idempotent_at_the_primitive(self):
        # The crash-window property at the mechanism layer: removal FIRST, departure record LAST. The
        # removal tail over already-gone bytes COMPLETES without error (each removal verified gone),
        # so a re-run finishes the transfer's tail rather than failing. This is the honest half of
        # the crash-window recovery that lives at the primitive.
        h = self.blobs.put(b"content")
        receipt = self._signed_receipt(h)
        self.blobs.hand_off([h], receipt)                             # first: removes
        self.assertFalse(self.blobs.has(h))
        self.blobs.hand_off([h], receipt)                             # second, already gone: completes
        self.assertFalse(self.blobs.has(h))

    def test_8i_a_second_handover_of_departed_content_halts(self):
        # HANDOVER IS NOT IDEMPOTENT LIKE A DELETE, and that is correct: you cannot hand over content
        # you no longer hold. Once the bytes have departed, a second ceremony has nothing to
        # duplicate-and-verify, so it HALTS (custody conservation — a departed subject is not
        # re-departed). Distinct from the destruction model's re-destroy, deliberately.
        h = self._write_file("/f", b"content")
        self._handover(h)
        self.assertFalse(self.blobs.has(h))
        with self.assertRaises(OpError) as cm:
            self._handover(h)                                         # nothing local to duplicate
        self.assertEqual(cm.exception.rule, erasure.HANDOVER_ANCHOR)
        # exactly one departure stands for this hash — not two
        self.assertEqual(len([r for r in erasure.departure_ledger(self.store.all())
                              if r[erasure.TARGET_HASH] == h]), 1)

    def test_8h_no_new_check_kind_is_forced(self):
        # §8-h: the ceremony rides the existing gate pipeline (registry, required-params, the
        # handler's own checks) — it mints NO new check kind. OP_CHECKS is unchanged; a new kind
        # would be a §8-h owner gate (STOP), not this EP.
        from kernel.opdefs import OP_CHECKS
        self.assertEqual(len(OP_CHECKS), 19)
        self.assertNotIn("handover", OP_CHECKS)
        self.assertNotIn("departure", OP_CHECKS)

    def test_8j_no_schedule_automation_enters_this_module(self):
        # §8-j: the ceremony fires when a lawful removal demand compels it, never as disk relief on a
        # timer. No scheduling primitive lives in kernel.erasure — that is a later round's extension.
        with open(os.path.join(REPO, "src", "kernel", "erasure.py"), encoding="utf-8") as fh:
            src = fh.read()
        for scheduler in ("schedule", "cron", "timer", "sleep(", "Thread(", "run_due"):
            self.assertNotIn(scheduler, src,
                             f"kernel.erasure must not carry `{scheduler}` — no schedule automation (§8-j)")


if __name__ == "__main__":
    unittest.main()
