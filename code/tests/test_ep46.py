# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (content-at-rest, per-piece key, wrapped key, sealed content, outer/inner fingerprint,
# recorded open); NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-46 (BUILD) — Content-at-rest: the key family's READ direction (who may OPEN, not just wrote).

Every probe here is a regression test (the campaign method: a verification probe lands as a test).
TEST WORLDS THROUGHOUT: disposable stores founded from the PRODUCTION pack (the key family + signed
door are live there); secrets live only in local variables and NEVER enter the record. The battery
proves design/43's six points, each an acceptance, plus needs-nothing-new by absence:

  A1  TestTwoDerivedKeys          ONE identity, TWO derived keys — sign (bound_key, unchanged) and
                                  open (open_public from the record, open_private from the secret) —
                                  distinct, neither doing the other's job (RW3). The open key
                                  derives LIVE from the record; the secret never enters it.
  A2  TestSealedContentOpenLocation  content stored as ciphertext (RW1: not recoverable from the
                                  sealed bytes without the key); location in the clear (RW2).
  A3  TestWrappedToReaders        wrapped to each allowed reader; a reader opens, a non-reader
                                  cannot; adding a reader wraps once more, content NOT re-encrypted
                                  (RW5).
  A4  TestTwoFingerprints         OUTER over sealed bytes (verifies without opening; a tamper reds
                                  it); INNER over content (checked at opening; a mismatch reds it).
  A5  TestOpeningIsARow           opening appends a row (actor/open/piece), admitted only for an
                                  allowed reader (the signed door reused); a non-reader's open is
                                  REFUSED and the refusal recorded (RW4).
  A6  TestRemoveReaderNewPiece    removing a reader makes a NEW piece; the old is neither deleted
                                  nor rewritten — custody conservation (RW6).
  A7  TestNeedsNothingNew         the open op rides CREATE-OP (no new founding kind); OP_CHECKS
                                  unchanged (no new check kind); and the production ACTIVATION has
                                  landed — production founding now CARRIES the open op (was held
                                  absent; inverted by EP-FND-OPEN-OP, board :3062(2); RW7).
  A8  TestAttestedMemberAdded     the bridge/seal.py grow-only ATTESTED_MEMBERS add is coherent (the
                                  law guard's surface stays covered). Whole-ledger green is the suite
                                  discover, the verifier's re-run.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel.boot import build_kernel                              # noqa: E402
from kernel import keys                                           # noqa: E402
from kernel.gate import make_invoker_sig, verify_invoker_sig, INVOKER_SIG  # noqa: E402  (the signed door)
from kernel.errors import OpError                                 # noqa: E402
from kernel.opdefs import OP_CHECKS                               # noqa: E402
from kernel.attestation import ATTESTED_MEMBERS, twin_uncovered   # noqa: E402
from bridge import seal                                           # noqa: E402  (the content-at-rest sealer, NEW)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

# PRODUCTION FOUNDING — THE OPEN OP HAS LANDED (EP-FND-OPEN-OP, the production activation, board
# :3062(2)). EP-46 held the pack byte-untouched and proved the open op ABSENT (a SEPARATE unit on its
# own owner word); that unit ran and the mover bumped 1.37.0 → 1.38.0, so production now CARRIES the
# open op. The activation is proven below by the PRESENCE of the op_definition — never by a whole-pack
# sha256 nor a version literal (the standing rule, EP-SHAPE.md:870; the :428 lesson), because both
# move with every lawful founding change and so cannot tell an activation from any other bump.

# TEST SECRETS (local only — NEVER recorded). A holder's own key material; the recorded card is the
# one-way commitment `keys.sign_public_from_secret(secret)`.
ALICE_SECRET = "testsecret:alice:v1"
BOB_SECRET = "testsecret:bob:v1"
CAROL_SECRET = "testsecret:carol:v1"
MALLORY_SECRET = "testsecret:mallory:v1"        # a non-reader — holds a valid card, wrapped to nothing

OPEN_OP = "OPEN-CONTENT"                          # the recorded open op, CREATE-OP'd in test worlds
A_LOCATION = "blob:sha256:the-clear-address"     # a piece's location — never secret (design/43 point 1)


class SealWorld(unittest.TestCase):
    """A disposable world founded from the PRODUCTION pack (key family + signed door live). Readers
    are accounts whose bound SIGN key is the commitment to their own secret, so the read direction's
    two open keys correspond (open_public from the card, open_private from the secret)."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    # --- the ceremony harness (the EP-36/37 signing pattern) ---
    def _do(self, opname, actor, params):
        """Execute AS `actor`, self-signing when the actor holds a bound key (the signed door)."""
        key = self.views.bound_key(actor)
        if key is None:
            return self.gate.execute(opname, actor, dict(params))
        draft = self.gate.ops[opname]["handler"](actor, dict(params))
        sig = make_invoker_sig(key, draft, seal=draft.get("seal"))
        return self.gate.execute(opname, actor, {**params, INVOKER_SIG: sig})

    def _account(self, acct, actor_class="human"):
        self._do("CREATE-ACCOUNT", "owner", {"account_id": acct, "actor_class": actor_class})
        h = "sha256:" + hashlib.sha256(acct.encode()).hexdigest()
        self._do("VERIFY-ACCOUNT", "owner", {"account": acct, "evidence_hash": h})

    def _reader(self, acct, secret):
        """Create the account and bind its SIGN key = the commitment to its own secret."""
        self._account(acct)
        self._do(keys.KEY_BIND, "owner", {"account": acct, "public_key": keys.sign_public_from_secret(secret)})
        return self.views.bound_key(acct)

    def _create_open_op(self):
        """CREATE-OP the recorded open op the GOVERNED way — a data-born definition, no new kind, no
        check (checks=[]). The reader-set enforcement is the seal ceremony's; the identity of the
        opener is the signed door's (per-account key enforcement, reused).

        SKIP when the op is already founded-at-boot (EP-FND-OPEN-OP landed it into PRODUCTION founding;
        mtr :3124). A second CREATE-OP of a live op is refused (ROOT-NEG-6 — a definition may not shadow
        the active registry), so a harness that stages it only where production has not yet founded it is
        the correct reuse. Either way the op the tests exercise is the SAME governed OPEN-CONTENT."""
        if self.gate.has(OPEN_OP):
            return None
        return self._do("CREATE-OP", "owner", {
            "name": OPEN_OP,
            "definition": {"description": "an allowed reader opens a sealed content piece — a recorded read",
                           "params": {"piece": "required"},
                           # `piece` is a STRUCTURAL reference (the piece's clear location, safe inline) —
                           # classified through the vocabulary door (EP-41A member 2, a dependency this EP
                           # rides). The CONTENT is sealed in the blob, never inline; the row names WHERE.
                           "structural_params": ["piece"],
                           "law_cited": "CAP-IS-LAW", "object_param": "piece", "checks": []}})

    def _record_open(self, piece, piece_ref, actor, secret):
        """The open ceremony: recover the content for an allowed reader, then RECORD the open row via
        the OPEN op signed by the actor (the signed door proves identity). A non-reader is refused by
        `open_content` (NotAReader) and the refusal is recorded through the gate. Returns the content
        on success; records op-refused and raises OpError on a non-reader."""
        sign_key = self.views.bound_key(actor)
        try:
            content = seal.open_content(piece, sign_key, secret)
        except seal.NotAReader as exc:
            # the gate records the refusal (op-refused), then raises — no gate edit, existing path
            self.gate.refuse(actor, OPEN_OP, "CAP-IS-LAW", "open refused: " + str(exc))
        draft = self.gate.ops[OPEN_OP]["handler"](actor, {"piece": piece_ref})
        sig = make_invoker_sig(sign_key, draft, seal=draft.get("seal"))
        rec = self.gate.execute(OPEN_OP, actor, {"piece": piece_ref, INVOKER_SIG: sig})
        return content, rec

    def _record_text(self):
        with open(self.path, encoding="utf-8") as fh:
            return fh.read()


# ============================================================================================
# A1 — TWO DERIVED KEYS (sign / open), distinct, each one job (design/43 point 2; RW3)
# ============================================================================================

class TestTwoDerivedKeys(SealWorld):

    def test_a1_one_identity_derives_two_distinct_keys(self):
        sign = self._reader("alice", ALICE_SECRET)                    # the SIGN key (bound_key)
        open_pub = keys.open_public_key(sign)                         # derived from the RECORDED sign key
        open_priv = keys.open_private_key(ALICE_SECRET)              # derived from the OWN secret
        # three distinct keys — the sign key and the two open keys are all different values
        self.assertEqual(len({sign, open_pub, open_priv}), 3)
        self.assertNotEqual(open_pub, sign)
        self.assertNotEqual(open_priv, sign)
        self.assertNotEqual(open_pub, open_priv)

    def test_a1_the_public_open_key_derives_from_the_recorded_sign_key(self):
        # anyone may wrap TO a reader: the public open key is a function of the RECORDED sign key,
        # derived LIVE from the record (never a stored value), the same posture as bound_key.
        self._reader("alice", ALICE_SECRET)
        recorded = self.views.bound_key("alice")
        # (F5: a self-comparison `open_public_key(recorded) == open_public_key(recorded)` was pruned —
        # it could not fail. Determinism is still covered here, and more strongly: the recorded sign key
        # equals sign_public_from_secret(ALICE_SECRET), so the two independent derivations below yielding
        # the SAME value proves both the derivation-from-the-card property AND determinism.)
        self.assertEqual(keys.open_public_key(recorded),
                         keys.open_public_key(keys.sign_public_from_secret(ALICE_SECRET)))  # from the card

    def test_a1_the_private_open_key_and_the_secret_never_enter_the_record(self):
        # the private open key derives from the secret, locally; neither the secret nor the private
        # open key is ever written — only the public commitment (the sign key) is.
        self._reader("alice", ALICE_SECRET)
        record = self._record_text()
        self.assertNotIn(ALICE_SECRET, record)                        # the secret never lands
        self.assertNotIn(keys.open_private_key(ALICE_SECRET), record)  # nor the private open key
        self.assertIn(keys.sign_public_from_secret(ALICE_SECRET), record)  # only the recorded commitment

    def test_a1_rw3_the_sign_key_does_not_open(self):
        # RW3: one key doing both reds. Content wrapped to alice's OPEN key has NO entry keyed by her
        # SIGN key — the sign key is not an open key, so it opens nothing.
        sign = self._reader("alice", ALICE_SECRET)
        piece = seal.seal(b"secret text", [sign], A_LOCATION)
        self.assertIn(keys.open_public_key(sign), piece[seal.WRAP])   # the OPEN key addresses the wrap
        self.assertNotIn(sign, piece[seal.WRAP])                      # the SIGN key does not

    def test_a1_rw3_the_open_key_does_not_sign(self):
        # RW3, the mirror: a mark citing the OPEN key does not verify as a signature against the
        # account's bound SIGN key — the open key cannot sign.
        sign = self._reader("alice", ALICE_SECRET)
        open_pub = keys.open_public_key(sign)
        draft = {"action": "CREATE-INFO", "object": None, "target": None, "payload": {"content": "x"}}
        mark_by_open = make_invoker_sig(open_pub, draft)             # a mark citing the OPEN key
        self.assertFalse(verify_invoker_sig(mark_by_open, sign, draft))   # does not verify as a signature
        self.assertTrue(verify_invoker_sig(make_invoker_sig(sign, draft), sign, draft))  # the sign key does


# ============================================================================================
# A2 — CONTENT SEALED, LOCATION OPEN (design/43 point 1; RW1, RW2)
# ============================================================================================

class TestSealedContentOpenLocation(SealWorld):

    def test_a2_content_is_stored_as_ciphertext(self):
        sign = self._reader("alice", ALICE_SECRET)
        content = b"the content at rest"
        piece = seal.seal(content, [sign], A_LOCATION, piece_key="deadbeef")
        self.assertNotEqual(piece[seal.SEALED], content)             # sealed bytes are not the plaintext (both eras)
        # WITH the key the content round-trips — via the piece's OWN era (a real AEAD when the vetted
        # library is present, the modelled XOR when absent). Re-expressed to the PROPERTY
        # (round-trips-with-the-key) rather than the modelled XOR bytes, so the pin holds in both modes
        # (KEY-MATERIAL-REAL §7 sweep, archi :3249/:3255; the era-split dispatches on the piece's ALG marker).
        self.assertEqual(seal.open_content(piece, sign, ALICE_SECRET), content)

    def test_a2_rw1_content_is_not_recoverable_without_the_key(self):
        # RW1: a piece whose content is recoverable from the raw sealed bytes without a key reds this.
        sign = self._reader("alice", ALICE_SECRET)
        content = b"the content at rest"
        piece = seal.seal(content, [sign], A_LOCATION, piece_key="deadbeef")
        self.assertNotIn(content, piece[seal.SEALED])                # the plaintext is not in the ciphertext
        self.assertNotEqual(seal.seal_bytes(piece[seal.SEALED], "wrongkey"), content)  # a wrong key yields no content
        self.assertNotIn(b"content", piece[seal.SEALED])             # not even a fragment survives in the clear

    def test_a2_rw2_the_location_is_in_the_clear_never_sealed(self):
        # RW2: hiding WHERE the record starts (not only its content) reds this — location is never
        # secret (verify-without-revealing). The piece carries the clear address unchanged.
        sign = self._reader("alice", ALICE_SECRET)
        piece = seal.seal(b"x", [sign], A_LOCATION)
        self.assertEqual(piece[seal.LOCATION], A_LOCATION)           # the clear address, unsealed
        self.assertNotIn(A_LOCATION.encode(), piece[seal.SEALED])    # the location is not inside the sealed bytes

    def test_a2_rw1_the_on_disk_sealed_blob_carries_no_content_plaintext(self):
        # F6 (DIGEST-C4): the other A2 arms read the IN-MEMORY sealed field; the one on-disk read (A1)
        # asserts the SECRET + private open key absent, not that the CONTENT plaintext is absent from the
        # blob AT REST. Persist the sealed bytes as they would land on disk (content-at-rest is the sealed
        # blob) and assert the plaintext — whole and fragment — is absent from the on-disk bytes, and that
        # the key still recovers the content FROM DISK. Composes with the modelled-material cap: a stronger
        # test of the RW1 guarantee (not recoverable without the key), not a new guarantee.
        sign = self._reader("alice", ALICE_SECRET)
        content = b"the content at rest"
        piece = seal.seal(content, [sign], A_LOCATION, piece_key="deadbeef")
        blob_path = os.path.join(self._dir, "piece.blob")
        with open(blob_path, "wb") as fh:
            fh.write(piece[seal.SEALED])
        with open(blob_path, "rb") as fh:
            on_disk = fh.read()
        self.assertEqual(on_disk, piece[seal.SEALED])                # what lands on disk IS the sealed blob
        self.assertNotIn(content, on_disk)                           # the content plaintext is not in the on-disk blob
        self.assertNotIn(b"content", on_disk)                        # not even a fragment survives at rest
        # (the on-disk bytes ARE piece[SEALED]; the key-recovers-content property is the modelled-output
        # pin already carried at test_a2 above and flagged for re-expression by the KEY-MATERIAL-REAL unit
        # — not duplicated here. These plaintext-absence assertions hold under BOTH modelled and real crypto.)


# ============================================================================================
# A3 — WRAPPED TO READERS; ADD A READER = WRAP ONCE MORE (design/43 point 3; RW5)
# ============================================================================================

class TestWrappedToReaders(SealWorld):

    def test_a3_a_reader_opens_a_non_reader_cannot(self):
        alice = self._reader("alice", ALICE_SECRET)
        bob = self._reader("bob", BOB_SECRET)
        self._reader("mallory", MALLORY_SECRET)                      # keyed, but wrapped to nothing
        content = b"minutes of the meeting"
        piece = seal.seal(content, [alice, bob], A_LOCATION)
        # both wrapped readers open
        self.assertEqual(seal.open_content(piece, alice, ALICE_SECRET), content)
        self.assertEqual(seal.open_content(piece, bob, BOB_SECRET), content)
        # the non-reader cannot: not in the wrapped set
        with self.assertRaises(seal.NotAReader):
            seal.open_content(piece, self.views.bound_key("mallory"), MALLORY_SECRET)

    def test_a3_add_a_reader_wraps_once_more_content_not_re_encrypted(self):
        alice = self._reader("alice", ALICE_SECRET)
        carol = self._reader("carol", CAROL_SECRET)
        content = b"minutes of the meeting"
        piece = seal.seal(content, [alice], A_LOCATION, piece_key="feed")
        self.assertEqual(len(piece[seal.WRAP]), 1)
        with self.assertRaises(seal.NotAReader):                     # carol cannot open yet
            seal.open_content(piece, carol, CAROL_SECRET)
        # add carol: wrap the SAME piece key once more (an existing reader supplies it)
        piece_key = seal.unwrap_key(piece, ALICE_SECRET)
        piece2 = seal.add_reader(piece, carol, piece_key)
        self.assertEqual(len(piece2[seal.WRAP]), 2)                  # the wrap set grew by one
        self.assertEqual(piece2[seal.SEALED], piece[seal.SEALED])    # RW5: content NOT re-encrypted
        self.assertEqual(piece2[seal.OUTER], piece[seal.OUTER])      # the outer fingerprint is unmoved
        self.assertEqual(seal.open_content(piece2, carol, CAROL_SECRET), content)  # carol opens now
        self.assertEqual(seal.open_content(piece2, alice, ALICE_SECRET), content)  # alice still opens

    def test_a3_the_wrap_is_addressed_to_open_keys_derived_from_recorded_sign_keys(self):
        alice = self._reader("alice", ALICE_SECRET)
        piece = seal.seal(b"x", [alice], A_LOCATION)
        # the wrap address is the reader's PUBLIC open key, derived from the RECORDED sign key
        self.assertEqual(set(piece[seal.WRAP]), {keys.open_public_key(self.views.bound_key("alice"))})


# ============================================================================================
# A4 — TWO FINGERPRINTS: outer verifies without opening; inner checked at opening (design/43 point 4)
# ============================================================================================

class TestTwoFingerprints(SealWorld):

    def test_a4_outer_verifies_over_ciphertext_without_opening(self):
        # the air rider (:2963): anyone verifies the chain over the sealed bytes from the piece
        # alone — no open key, no engine, no gate, no view.
        sign = self._reader("alice", ALICE_SECRET)
        piece = seal.seal(b"content", [sign], A_LOCATION)
        self.assertTrue(seal.verify_outer(piece))                    # verifies with no reader, no secret

    def test_a4_a_tampered_ciphertext_fails_the_outer(self):
        sign = self._reader("alice", ALICE_SECRET)
        piece = seal.seal(b"content", [sign], A_LOCATION)
        tampered = dict(piece)
        tampered[seal.SEALED] = piece[seal.SEALED][:-1] + bytes([piece[seal.SEALED][-1] ^ 0x01])
        self.assertFalse(seal.verify_outer(tampered))               # the outer check can fail

    def test_a4_the_inner_is_checked_at_opening_and_a_mismatch_reds(self):
        alice = self._reader("alice", ALICE_SECRET)
        content = b"content"
        piece = seal.seal(content, [alice], A_LOCATION)
        self.assertEqual(seal.open_content(piece, alice, ALICE_SECRET), content)   # inner matches at open
        # a piece whose sealed bytes were corrupted opens to something that fails the INNER check
        corrupt = dict(piece)
        corrupt[seal.SEALED] = bytes([b ^ 0x7F for b in piece[seal.SEALED]])
        with self.assertRaises(seal.ContentMismatch):
            seal.open_content(corrupt, alice, ALICE_SECRET)

    def test_a4_the_two_fingerprints_are_over_different_things(self):
        sign = self._reader("alice", ALICE_SECRET)
        content = b"content"
        piece = seal.seal(content, [sign], A_LOCATION)
        self.assertEqual(piece[seal.OUTER], seal.outer_fingerprint(piece[seal.SEALED]))  # over the sealed bytes
        self.assertEqual(piece[seal.INNER], seal.inner_fingerprint(content))             # over the content
        self.assertNotEqual(piece[seal.OUTER], piece[seal.INNER])   # different things, different fingerprints


# ============================================================================================
# A5 — OPENING IS A ROW; the gate admits it only for an allowed reader (design/43 point 5; RW4)
# ============================================================================================

class TestOpeningIsARow(SealWorld):

    def setUp(self):
        super().setUp()
        self._create_open_op()

    def test_a5_an_allowed_reader_opens_and_the_open_is_a_recorded_row(self):
        alice = self._reader("alice", ALICE_SECRET)
        content = b"the content"
        piece = seal.seal(content, [alice], A_LOCATION)
        got, rec = self._record_open(piece, A_LOCATION, "alice", ALICE_SECRET)
        self.assertEqual(got, content)                               # the reader recovered the content
        # opening is a ROW: actor / the open op / object the piece — recorded as a write
        self.assertEqual(rec["actor"], "alice")
        self.assertEqual(rec["action"], OPEN_OP)
        self.assertEqual(rec["object"], A_LOCATION)
        self.assertEqual(len(self.store.by_action(OPEN_OP)), 1)      # the open landed in the record

    def test_a5_a_non_reader_open_is_refused_and_the_refusal_recorded(self):
        alice = self._reader("alice", ALICE_SECRET)
        self._reader("mallory", MALLORY_SECRET)                      # keyed, not a wrapped reader
        piece = seal.seal(b"the content", [alice], A_LOCATION)
        with self.assertRaises(OpError):
            self._record_open(piece, A_LOCATION, "mallory", MALLORY_SECRET)
        refusals = self.store.by_action("op-refused")
        self.assertTrue(any(r.get("target") == "mallory" and (r.get("payload") or {}).get("op") == OPEN_OP
                            for r in refusals))                      # the refusal is recorded (RW4)
        self.assertEqual(self.store.by_action(OPEN_OP), [])          # and no open row was written

    def test_a5_the_open_reuses_the_signed_door_the_actor_signs(self):
        # the open row is admitted only with the actor's OWN valid signature (the signed door,
        # per-account key enforcement, reused): a keyed actor's unsigned open is refused.
        alice = self._reader("alice", ALICE_SECRET)
        piece = seal.seal(b"x", [alice], A_LOCATION)
        self.assertEqual(seal.open_content(piece, alice, ALICE_SECRET), b"x")   # the reader may open
        with self.assertRaises(OpError):                             # but recording it UNSIGNED is refused
            self.gate.execute(OPEN_OP, "alice", {"piece": A_LOCATION})


# ============================================================================================
# A6 — REMOVE A READER = A NEW PIECE, NEVER A DELETION (custody conservation, :2856; RW6)
# ============================================================================================

class TestRemoveReaderNewPiece(SealWorld):

    def test_a6_removing_a_reader_makes_a_new_piece_leaving_the_old_untouched(self):
        alice = self._reader("alice", ALICE_SECRET)
        bob = self._reader("bob", BOB_SECRET)
        content = b"the shared content"
        piece = seal.seal(content, [alice, bob], A_LOCATION, piece_key="key-one")
        old_snapshot = dict(piece)                                   # capture the old piece's exact bytes

        # remove bob: a remaining reader (alice) opens and re-seals to the remaining set {alice}
        remaining = [alice]
        new_piece = seal.remove_reader(piece, content, remaining, piece_key="key-two")

        # the OLD piece is neither deleted nor rewritten — byte-identical to before (RW6)
        self.assertEqual(piece, old_snapshot)
        self.assertEqual(piece[seal.SEALED], old_snapshot[seal.SEALED])
        # the NEW piece is re-keyed (different sealed bytes) and wrapped to the remaining reader only
        self.assertNotEqual(new_piece[seal.SEALED], piece[seal.SEALED])
        self.assertEqual(set(new_piece[seal.WRAP]), {keys.open_public_key(alice)})
        self.assertNotIn(keys.open_public_key(bob), new_piece[seal.WRAP])

    def test_a6_the_removed_reader_cannot_open_the_new_piece_but_the_old_stands(self):
        alice = self._reader("alice", ALICE_SECRET)
        bob = self._reader("bob", BOB_SECRET)
        content = b"the shared content"
        piece = seal.seal(content, [alice, bob], A_LOCATION)
        new_piece = seal.remove_reader(piece, content, [alice])
        # bob can no longer open the NEW piece
        with self.assertRaises(seal.NotAReader):
            seal.open_content(new_piece, bob, BOB_SECRET)
        # custody conservation: the OLD piece is not destroyed, so bob still opens IT (no row removed)
        self.assertEqual(seal.open_content(piece, bob, BOB_SECRET), content)
        # and alice opens the new piece
        self.assertEqual(seal.open_content(new_piece, alice, ALICE_SECRET), content)


# ============================================================================================
# A7 — NEEDS NOTHING NEW (no new kind / no new check); and the production ACTIVATION has LANDED —
#      production founding CARRIES the open op (the held absence inverted, EP-FND-OPEN-OP; RW7)
# ============================================================================================

class TestNeedsNothingNew(SealWorld):

    def test_a7_the_open_op_rides_create_op_no_new_founding_kind(self):
        # RE-EXPRESSED to the founded-at-boot reality (EP-FND-OPEN-OP landed the op into PRODUCTION
        # founding; mtr :3124). The two facts the absent-then-manually-created staging proved — the op is
        # LIVE and it rode the governed CREATE-OP door as a recorded op_definition amendment (not a new
        # founding kind, not a code registration) — now hold against the founded world directly, so the
        # staging is replaced by the founded record itself. Masks nothing: a new founding KIND would show
        # here as a payload kind other than op_definition, and the can-fail control lives in test_a7_no_new_check_kind.
        self.assertTrue(self.gate.has(OPEN_OP))                      # founded at boot, live in the gate
        creates = [e for e in self.store.all()
                   if e.get("action") == "CREATE-OP" and (e.get("payload") or {}).get("name") == OPEN_OP]
        self.assertEqual(len(creates), 1)                            # exactly one governed amendment
        self.assertEqual(creates[0]["payload"]["kind"], "op_definition")  # rode CREATE-OP; no new founding kind

    def test_a7_no_new_check_kind(self):
        # the open check reuses the gate's per-account signature enforcement — OP_CHECKS is unchanged.
        self.assertEqual(len(OP_CHECKS), 19)                         # the seventeen check kinds, no new one
        self.assertNotIn("open", OP_CHECKS)                          # no open-specific check minted

    def test_a7_production_founding_carries_the_open_op_the_activation_landed(self):
        # THE HELD-ASSERTION INVERTED (EP-FND-OPEN-OP, board :3062(2)). EP-46 proved the open op
        # ABSENT from production and held the pack byte-untouched; the activation mover has now landed,
        # so production CARRIES the open op. Proven by the PRESENCE of the op_definition — no version
        # literal, no whole-pack sha (EP-SHAPE.md:870; the :428 lesson), because both move with any
        # lawful founding change and cannot tell an activation apart from another bump.
        with open(PACK_PATH, encoding="utf-8") as fh:
            pack = json.load(fh)
        ops = {r["payload"]["name"] for s in pack["steps"] for r in s["records"]
               if r.get("action") == "CREATE-OP"}
        self.assertIn(OPEN_OP, ops)                                  # the open op is now a PRODUCTION op
        self.assertNotIn("NO-SUCH-OP", ops)                          # §A64: the membership test discriminates
        # the landed record is EP-46's proven shape carried VERBATIM (rides CREATE-OP, no new kind):
        recs = [r for s in pack["steps"] for r in s["records"]
                if r.get("action") == "CREATE-OP" and (r.get("payload") or {}).get("name") == OPEN_OP]
        self.assertEqual(len(recs), 1)                               # exactly one, not shadowed
        d = recs[0]["payload"]["definition"]
        self.assertEqual(d["params"], {"piece": "required"})         # the proven definition, carried
        self.assertIn("piece", d["structural_params"])               # `piece` STRUCTURAL (safe inline)
        self.assertEqual(d["checks"], [])                            # no new check kind rode in


# ============================================================================================
# A8 — the bridge/seal.py ATTESTED_MEMBERS grow-only add is coherent (the F4 twin stays covered)
# ============================================================================================

class TestAttestedMemberAdded(unittest.TestCase):

    def test_a8_seal_is_a_grow_only_attested_member(self):
        self.assertIn("bridge/seal.py", ATTESTED_MEMBERS)            # the new src/bridge/*.py is attested
        self.assertEqual(len(ATTESTED_MEMBERS), 53)                  # 53 since EP-52-BUILD's subsystems/filter.py joined (FIREWALL-IN-THE-RECORD, C5 P7, the founding mover; §5 fence "+ its ATTESTED_MEMBERS line and count-pin companion", driven at dispatch); 52 since EP-49A-BUILD's kernel/border.py joined (THE BORDER: THE DOOR, the campaign-5 crux; §5 fence "+ its ATTESTED_MEMBERS line and count-pin companion", DRIVEN at dispatch not carried — the test_ep40:259 double-stop companion); 51 since EP-48-BUILD's subsystems/sockets.py joined (SOCKET-GRANTS, the campaign-5 founding mover; §5 name-and-count sweep + :3255(b) by-name widen, KEY-MATERIAL-REAL's signer.py already in at 50); 50 since kernel/signer.py joined (KEY-MATERIAL-REAL RE-MINT 2, archi :3249 — the by-name count-pin widen, the crypto.py companion doubled); 49 since kernel/crypto.py (48 before); §A57 name-and-count widen at mgr's hand (OVERNIGHT-DECISION), the double-stop companion the KEY-MATERIAL-REAL plan fenced for test_ep40 but missed here
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)))  # the list stays sorted

    def test_a8_the_law_guard_surface_stays_covered(self):
        # the F4 twin: every .py the law guard greps is inside the attested set. Adding a NEW
        # src/bridge/*.py without attesting it would leave it uncovered — this stays empty because
        # seal.py is on disk AND in the manifest.
        self.assertEqual(twin_uncovered(), [])                      # no governance surface outside coverage


if __name__ == "__main__":
    unittest.main()
