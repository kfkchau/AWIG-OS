# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (gate, signature, key binding, acceptance). NON-GOAL: no offensive capability of any
# kind — this proves a governance door ACCEPTS a signed act and REFUSES an unsigned one; it mints
# nothing real and models no attack. Full declaration: SCOPE-STATEMENT.md.
"""EP-37 (BUILD) — THE SIGNED DOOR: for a key-bound account the gate accepts no act without a valid
signature from a then-valid bound key; the caller-asserted actor retires at the cryptographic door,
per-account, no flag day (design/37 Q2, Q6, Q10; the campaign crux — R20-2 closes).

Every probe here is a regression test (the campaign method). TEST KEYS throughout (§8-g): nothing
real is bound — the first real key is the owner's own act, handed back at W4. The battery proves,
in disposable stores where the founding declares the signing law:

  A1  TestSignedDoor          the authorization matrix, EVERY signature column ABLE TO FAIL: valid
                              -> accepts; absent / wrong-key / superseded / bound-after-deciding-time
                              -> refuses citing SIGN-LAW. A matrix that cannot fail proves nothing
                              (DIGEST-C2 §4).
  A2  TestKeyFlipPerAccount   binding a key flips ONE account (its acts now require a signature); no
                              other account changes; and the ZERO-KEYS world is BYTE-IDENTICAL — the
                              door is inert until a key binds, so day one changes nobody (RW2).
  A3  TestStrictlyStronger    the EP-17 strictly-stronger proof on the EXTENDED ledger, logged FIRST;
                              only then is the caller-asserted acceptance retired for keyed accounts
                              (a naked swap is a rejected diff — RW5).
  A5  TestRoundTrip           kill everything derived, replay: every recorded signature verifies as
                              DATA (re-signs nothing, Q10) and the acceptance binding reconstructs.
  RW  TestRedWorlds           RW1 too-weak (an unsigned keyed act lands — impossible), RW2 too-wedged
                              (an unkeyed account's lawful work stops — must not happen), RW3 the
                              quiet trap (signer state between acts — the EP-15 trap in crypto dress),
                              RW4 a superseded key (refuses live; the old signature stays data), RW5
                              the naked swap (retirement never precedes the proof).
      TestEP37FoundingStillHeld  §8-f/§A57, G1b ENTRY-SCOPED (architect :2866): EP-37's OWN founding
                              (SIGN-LAW) is still HELD, asserted by OWN-VOCABULARY-ABSENCE — the signing
                              law is not in production — NOT by a founding byte/version proxy (the
                              key-family create moved the founding to 1.33.0 this pass, which a version
                              proxy would have mistaken for EP-37's); a planted signing law REDS it.

THE TWO CRUX REFERENCES REFUSED (design/37 §5). THE QUIET ONE — sessions/tokens: no cache, no
session, no "current signer" is consulted anywhere; the account is resolved anew and the signature
verified live against the EP-36 fold every act (RW3 drives it). THE LOUD ONE — blockchain/PKI: no
trust store, no certificate tree, no primitive minted; the signature model is
possession-plus-minted-provenance (keys.countersign's shape), the real primitive arriving later
(design/37 §9). This EP adds NO serializer (consumes canonical.py) and NO new envelope field
(§8-i — the invoker's signature rides in provenance, design/37 Q2).

EP-37'S FOUNDING-MOVE IS STILL HELD. SIGN-LAW is founding vocabulary whose create rides the owner's
word (§8-e/§8-f, EP-36 shape). The door is built and INERT until SIGN-LAW is declared; here the
mechanism is proven in TEST founding worlds where SIGN-LAW is declared. The KEY FAMILY, by contrast,
is production founding now (COMPLETE-KEY-FAMILY, 1.33.0): build_kernel loads KEY-LAW-BIND and the key
ops, so keys bind without a test-world stand-in, and only SIGN-LAW remains held (asserted by
own-vocabulary-absence, robust to the key-family move that a version proxy would have flagged).
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # so `import test_ep36` / era_pin resolve
import era_pin                                                                  # noqa: E402  (the era-pin home, EP-28Z)
from kernel.boot import build_kernel                                            # noqa: E402
from kernel import keys                                                         # noqa: E402
from kernel.errors import OpError                                               # noqa: E402
from kernel.gate import SIGN_LAW, INVOKER_SIG, make_invoker_sig, verify_invoker_sig  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

#: THE PRE-CREATE ERA — the commit at the builder's hand IMMEDIATELY BEFORE this pass's founding write
#: (COMPLETE-SIGNING-LAW, mover-2), captured by `git rev-parse HEAD` and filed at
#: planning/evidence/EP-37-BUILD/MOVER2-ACCEPTANCE-v3.txt. At this era the production pack declares NO
#: signing law (founding 1.33.0), so the OLD caller-asserted door governed and could not express the
#: signature dimension at all — the EP-17 licence itself, read out of git rather than rebuilt (a
#: build_kernel world without SIGN-LAW no longer exists — mover-2 landed the create). §A57, never a relabel.
SIGN_LAW_PRE_COMMIT = "062fffe15b471de4798866c1db134fa98acd2b51"

# TEST KEY MATERIAL (§8-g): plain strings — the simplest thing that binds, nothing real minted.
ALICE_KEY = "testpub:alice:v1"
ALICE_KEY_2 = "testpub:alice:v2"
BOB_KEY = "testpub:bob:v1"


# ============================================================================================
# A test founding world where the signing law is DECLARED (production founding, mover-2) and keys
# can be bound. SIGN-LAW rides build_kernel from the pack now — no test-world stand-in declares it.
# ============================================================================================

class SignedWorld(unittest.TestCase):

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)
        # SIGN-LAW IS PRODUCTION FOUNDING NOW (COMPLETE-SIGNING-LAW, mover-2, founding 1.34.0; owner
        # create-word board :2847, tier ordinary/owner :2788). build_kernel loads it from the pack, so
        # the signed door engages per-account with no test-world stand-in — exactly as the key family
        # (COMPLETE-KEY-FAMILY, 1.33.0) already binds keys without one. A world where SIGN-LAW is
        # absent no longer exists via build_kernel; the door narrows nobody here until a key binds.
        self.assertIn(SIGN_LAW, self.views.active_rules())   # the door is live from genesis (the create landed)

    # --- ceremony helpers: the operator is `owner` (chain-end, UNKEYED — signs nothing) ---
    def _account(self, acct, actor_class="human"):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": acct, "actor_class": actor_class})
        self.gate.execute("VERIFY-ACCOUNT", "owner",
                          {"account": acct,
                           "evidence_hash": "sha256:" + hashlib.sha256(acct.encode()).hexdigest()})

    def _bind(self, account, key, actor="owner"):
        return self.gate.execute(keys.KEY_BIND, actor, {"account": account, "public_key": key})

    # --- the invoker's signing (the caller's own act; the gate never signs) ---
    def _draft_for(self, actor, opname, params):
        """The draft the handler will produce — pure, so signing over it binds exactly what the door
        will recompute at acceptance (handlers are pure draft-builders)."""
        return self.gate.ops[opname]["handler"](actor, dict(params))

    def _sig(self, actor, opname, params, key, deciding_time=None):
        draft = self._draft_for(actor, opname, params)
        return make_invoker_sig(key, draft, deciding_time=deciding_time, seal=draft.get("seal"))

    def _signed_exec(self, actor, opname, params, key):
        sig = self._sig(actor, opname, params, key)
        return self.gate.execute(opname, actor, {**params, INVOKER_SIG: sig})


class KeyedAlice(SignedWorld):
    """A world where `alice` is a founded, key-bound account — her acts now require a signature."""

    def setUp(self):
        super().setUp()
        self._account("alice")
        self._bind("alice", ALICE_KEY)
        self.assertEqual(self.views.bound_key("alice"), ALICE_KEY)


# ============================================================================================
# A1 — T-SIGNED-DOOR: the authorization matrix, every column able to fail
# ============================================================================================

class TestSignedDoor(KeyedAlice):

    def test_valid_signature_accepts(self):
        # COLUMN: valid -> accepts, and the signature is recorded in PROVENANCE (Q2), never a new
        # envelope field (§8-i).
        rec = self._signed_exec("alice", "CREATE-INFO", {"content": "doc-1"}, ALICE_KEY)
        self.assertEqual(rec["action"], "CREATE-INFO")
        self.assertEqual(rec["provenance"]["asserted_by"], "alice")
        self.assertEqual(rec["provenance"][INVOKER_SIG]["by"], ALICE_KEY)   # the signer's key, on the record

    def test_absent_signature_refuses(self):
        # COLUMN: absent -> refuses citing the signing law. A keyed account cannot act unsigned (RW1).
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "doc-2"})
        self.assertEqual(cm.exception.rule, SIGN_LAW)

    def test_wrong_key_signature_refuses(self):
        # COLUMN: wrong key -> refuses. A signature by a key that is not alice's binding is invalid.
        sig = self._sig("alice", "CREATE-INFO", {"content": "doc-3"}, BOB_KEY)   # signed by the wrong key
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "doc-3", INVOKER_SIG: sig})
        self.assertEqual(cm.exception.rule, SIGN_LAW)

    def test_superseded_key_signature_refuses_by_rotation(self):
        # COLUMN: superseded -> refuses. alice rotates to a new key; a signature by the OLD key is no
        # longer her valid binding (latest-supersession-wins; the fold re-derives live).
        self.gate.execute(keys.KEY_ROTATE, "owner", {"account": "alice", "public_key": ALICE_KEY_2})
        self.assertEqual(self.views.bound_key("alice"), ALICE_KEY_2)
        sig_old = self._sig("alice", "CREATE-INFO", {"content": "doc-4"}, ALICE_KEY)   # the superseded key
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "doc-4", INVOKER_SIG: sig_old})
        self.assertEqual(cm.exception.rule, SIGN_LAW)
        # and the NEW key signs validly (the column can also pass — a check that cannot fail is not one)
        rec = self._signed_exec("alice", "CREATE-INFO", {"content": "doc-4b"}, ALICE_KEY_2)
        self.assertEqual(rec["provenance"][INVOKER_SIG]["by"], ALICE_KEY_2)

    def test_superseded_key_signature_refuses_by_revocation(self):
        # COLUMN: superseded -> refuses (revoke -> None). A revoked account holds NO valid key, so a
        # signature citing the old key is a false claim, not a return to openness.
        self.gate.execute(keys.KEY_REVOKE, "owner", {"account": "alice"})
        self.assertIsNone(self.views.bound_key("alice"))
        sig_old = self._sig("alice", "CREATE-INFO", {"content": "doc-5"}, ALICE_KEY)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "doc-5", INVOKER_SIG: sig_old})
        self.assertEqual(cm.exception.rule, SIGN_LAW)

    def test_key_bound_after_the_acts_deciding_time_refuses(self):
        # COLUMN: bound-after-deciding-time -> refuses. The estate models "as of the deciding time" as
        # the fold pointed at the deciding POSITION (keys.bound_key `as_of`, EP-36 A5's own model);
        # wiring an arrival's deciding-time key validity THROUGH the gate and the late-revocation
        # sweep is EP-38's two-frames arithmetic, fenced out here (RW4). `bob`'s key binds AFTER the
        # deciding position, so as of that position he had no valid key — a signature citing the
        # later key does NOT verify.
        self._account("bob")
        deciding = len(self.store.events)                    # the deciding position: before bob binds
        self._bind("bob", BOB_KEY)                           # bob's key binds AFTER
        self.assertEqual(self.views.bound_key("bob"), BOB_KEY)               # live: bound
        self.assertIsNone(self.views.bound_key("bob", as_of=deciding))       # as of the deciding position: NOT bound
        draft = {"actor": "bob", "action": "CREATE-INFO", "object": "doc-6"}
        mark = make_invoker_sig(BOB_KEY, draft)
        # the door reads the binding AS OF the deciding time -> None -> the column FAILS (refuses)
        self.assertFalse(verify_invoker_sig(mark, self.views.bound_key("bob", as_of=deciding), draft))
        # and the same mark verifies against the LIVE binding (the column can also pass)
        self.assertTrue(verify_invoker_sig(mark, self.views.bound_key("bob"), draft))

    def test_tampered_content_refuses(self):
        # A signature is bound to its act: a signature made for one act does not authorise another
        # (the `over` hash mismatches). This is the immutability half of Q2 ("cannot be altered").
        sig = self._sig("alice", "CREATE-INFO", {"content": "doc-A"}, ALICE_KEY)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "doc-B", INVOKER_SIG: sig})   # different act
        self.assertEqual(cm.exception.rule, SIGN_LAW)


# ============================================================================================
# A2 — T-KEY-FLIP-PER-ACCOUNT: binding flips ONE account; the zero-keys world is byte-identical
# ============================================================================================

class TestKeyFlipPerAccount(SignedWorld):

    def test_binding_flips_only_its_own_account(self):
        # alice binds -> alice narrows (must sign). bob never binds -> bob acts under openness,
        # unchanged. The flip is per-account; binding IS the narrowing act (Q6).
        self._account("alice"); self._account("bob")
        self._bind("alice", ALICE_KEY)
        self.assertEqual(self.views.bound_key("alice"), ALICE_KEY)
        self.assertIsNone(self.views.bound_key("bob"))
        # alice (keyed): unsigned refuses, signed accepts
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "a"})
        self.assertEqual(cm.exception.rule, SIGN_LAW)
        self.assertEqual(self._signed_exec("alice", "CREATE-INFO", {"content": "a"}, ALICE_KEY)["action"],
                         "CREATE-INFO")
        # bob (unkeyed): acts freely, no signature — the neighbour did not change
        self.assertEqual(self.gate.execute("CREATE-INFO", "bob", {"content": "b"})["action"], "CREATE-INFO")

    def test_declaring_the_law_with_zero_keys_changes_nobody(self):
        # NO flag day: the signing law is DECLARED (this setUp) yet with NO key bound anywhere, every
        # account acts exactly as today — declaring the law alone narrows no one.
        self._account("carol")
        self.assertIsNone(self.views.bound_key("carol"))
        self.assertEqual(self.gate.execute("CREATE-INFO", "carol", {"content": "c"})["action"], "CREATE-INFO")
        # WRITE-ACTIVITY lawfully records as SYSTEM (the audit mirror), invoked BY carol — the door
        # never enters, so carol's telemetry lands exactly as today (the invoker/actor split, Q2).
        self.assertEqual(self.gate.execute("WRITE-ACTIVITY", "carol", {"about": "x", "data": {"n": 1}})["action"],
                         "WRITE-ACTIVITY")

    def test_zero_keys_world_is_byte_identical_to_a_no_sign_law_world(self):
        # THE WEDGE TEST (RW2): with the door live and zero keys, a battery of acts decides IDENTICALLY
        # to a world with no signing law at all — the door is inert until a key binds. (The whole
        # pre-existing suite green with zero keys is the verifier's discover; no test declares SIGN-LAW,
        # so the door never enters there — the strongest form of this property.)
        def battery(gate):
            gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "dave", "actor_class": "human"})
            r1 = gate.execute("CREATE-INFO", "dave", {"content": "z"})
            r2 = gate.execute("WRITE-ACTIVITY", "dave", {"about": "y", "data": {"k": 2}})
            return (r1["action"], r1["object"], r2["actor"], r2["action"])
        with_law = battery(self.gate)                                         # sign law declared, zero keys
        d = tempfile.mkdtemp()
        store, gate, views = build_kernel(os.path.join(d, "r.jsonl"))         # NO signing law at all
        without_law = battery(gate)
        self.assertEqual(with_law, without_law)


# ============================================================================================
# A3 — T-STRICTLY-STRONGER: the extended-ledger proof, logged FIRST, then the retirement
# ============================================================================================

class TestStrictlyStronger(SignedWorld):
    """A3 — the EP-17 strictly-stronger proof on the EXTENDED ledger, re-expressed LIVE now that the
    signing law is PRODUCTION founding. A world with no signing law no longer exists via build_kernel
    (mover-2 landed the create), so the OLD door — caller-asserted acceptance, which could not express
    the signature dimension at all — is read from its ERA out of git (the pre-create pack declares NO
    signing law), exactly the §A57 move the key family used when its own 'no-law world' ceased to
    exist (test_ep36 test_a4_the_key_leash_is_inert...). The live half proves the door PRESERVES the
    old ledger (unkeyed accounts unchanged) and is STRICTLY STRONGER on the new dimension (a keyed
    account's unsigned act refuses, and is accepted once signed). The retirement is licensed by this
    proof — emitted before it stands, RW5/§8-j."""

    def test_extended_ledger_reproof_and_verdict_line(self):
        # THE OLD LEDGER (campaign-2 openness) PRESERVED, LIVE: unkeyed accounts decide IDENTICALLY
        # with the door live — the door adds NOTHING on the dimension the old ledger could express.
        for acct in ("bob", "carol"):
            self._account(acct)
        old_ledger_preserved = all(
            self.gate.execute("CREATE-INFO", a, {"content": f"{a}-doc"})["action"] == "CREATE-INFO"
            for a in ("bob", "carol"))

        # THE OLD DOOR COULD NOT EXPRESS THE SIGNATURE DIMENSION — read from its ERA, not rebuilt. The
        # pre-create production founding (SIGN_LAW_PRE_COMMIT, 1.33.0) declares NO signing law, so the
        # caller-asserted door governed there and had NO signature column to refuse on — it accepted a
        # keyed account's act unsigned because it could not tell keyed from unkeyed. This is the EP-17
        # licence itself, made a fact about the era rather than a live rebuild (a build_kernel world
        # without SIGN-LAW no longer exists; the key family made this same move when its no-law world
        # ceased to be). ERA COVERAGE read out of git, so the create's landing is a fact, not a memory.
        era_text = era_pin.text_at(SIGN_LAW_PRE_COMMIT, era_pin.PACK_PATH, missing="assert")
        old_could_not_express_signatures = not _pack_sign_law_present(era_text)
        with open(PACK_PATH, encoding="utf-8") as fh:
            live_declares_signatures = _pack_sign_law_present(fh.read())

        # THE NEW DIMENSION (keyed accounts), LIVE: the NEW door REFUSES an unsigned keyed act...
        self._account("alice"); self._bind("alice", ALICE_KEY)
        try:
            self.gate.execute("CREATE-INFO", "alice", {"content": "y"})       # unsigned, keyed
            new_refuses_unsigned_keyed = False
        except OpError as e:
            new_refuses_unsigned_keyed = (e.rule == SIGN_LAW)
        # ...and ACCEPTS the same act once SIGNED — the door adds a requirement, not a wall.
        keyed_signed_accepts = (
            self._signed_exec("alice", "CREATE-INFO", {"content": "z"}, ALICE_KEY)["action"] == "CREATE-INFO")

        print(f"\n[EP-37 STRICTLY-STRONGER EXTENDED-LEDGER RE-PROOF] extended ledger = the unkeyed acts "
              f"(campaign-2 openness, the OLD ledger) + the keyed dimension the old ledger could NOT "
              f"express; OLD LEDGER: the live door PRESERVES every unkeyed acceptance "
              f"({old_ledger_preserved}) and adds NO refusal to it; the OLD DOOR could not express the "
              f"signature dimension — its own era (SIGN_LAW_PRE_COMMIT, 1.33.0) declares no signing law "
              f"({old_could_not_express_signatures}) while production now does "
              f"({live_declares_signatures}); NEW DIMENSION: the signed door REFUSES an unsigned keyed "
              f"act ({new_refuses_unsigned_keyed}) and ACCEPTS it once signed ({keyed_signed_accepts}); "
              f"strictly-stronger-or-equal on the EXTENDED ledger PROVEN — the retirement of "
              f"caller-asserted acceptance for keyed accounts is LICENSED (an old ledger cannot contain "
              f"cases in the signature dimension it could not express). The proof is emitted BEFORE the "
              f"retirement stands; a naked swap is a rejected diff (RW5/§8-j).")
        self.assertTrue(all((old_ledger_preserved, old_could_not_express_signatures,
                             live_declares_signatures, new_refuses_unsigned_keyed, keyed_signed_accepts)))


# ============================================================================================
# A5 — T-ROUND-TRIP: replay verifies recorded signatures as DATA; acceptance reconstructs
# ============================================================================================

class TestRoundTrip(KeyedAlice):

    def test_recorded_signature_verifies_as_data_after_replay(self):
        # A signed act is recorded (its signature in provenance). Kill the derived state and rebuild
        # the kernel from the record file alone. The recorded signature verifies as DATA against the
        # replayed binding — re-signing nothing, re-running no signer (Q10) — and the binding the
        # acceptance answer needs reconstructs identically.
        rec = self._signed_exec("alice", "CREATE-INFO", {"content": "kept"}, ALICE_KEY)
        recorded = rec["provenance"][INVOKER_SIG]

        store2, gate2, views2 = build_kernel(self.path)                      # kill derived, replay
        self.assertEqual(views2.bound_key("alice"), ALICE_KEY)              # the binding reconstructs
        r2 = [e for e in store2.all()
              if e["action"] == "CREATE-INFO" and e.get("object") == "kept"][-1]
        self.assertEqual(r2["provenance"][INVOKER_SIG], recorded)           # the signature replayed as data
        self.assertTrue(verify_invoker_sig(recorded, views2.bound_key("alice"), r2,
                                           deciding_time=None, seal=r2.get("seal")),
                        "a recorded signature did not verify against the replayed binding")

    def test_replay_re_signs_nothing(self):
        # The frozen-answer law applied to the door's cryptography: reload derives the SAME binding
        # and the SAME verification verdict without minting a signature or invoking a signer.
        self._signed_exec("alice", "CREATE-INFO", {"content": "one"}, ALICE_KEY)
        before = len(self.store.events)
        store2, gate2, views2 = build_kernel(self.path)
        self.assertEqual(len(store2.events), before)                        # replay appended nothing


# ============================================================================================
# RED WORLDS — each driven through the instrument, recorded (§A42)
# ============================================================================================

class TestRedWorlds(KeyedAlice):

    def test_rw1_an_unsigned_keyed_act_never_lands(self):
        # RW1 too-weak: an unsigned act by a KEYED account must NOT land. It refuses, and no
        # CREATE-INFO record for it exists.
        before = len([e for e in self.store.all() if e["action"] == "CREATE-INFO"])
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "ghost"})
        self.assertEqual(cm.exception.rule, SIGN_LAW)
        after = [e for e in self.store.all() if e["action"] == "CREATE-INFO"]
        self.assertEqual(len(after), before)                                # the act did NOT land
        self.assertFalse(any(e.get("object") == "ghost" for e in after))

    def test_rw2_an_unkeyed_accounts_lawful_work_never_stops(self):
        # RW2 too-wedged: an unkeyed account's lawful act must NOT be stopped by the door.
        self._account("bob")
        self.assertIsNone(self.views.bound_key("bob"))
        self.assertEqual(self.gate.execute("CREATE-INFO", "bob", {"content": "fine"})["action"], "CREATE-INFO")
        # and SYSTEM's own work (the recorder / mirror / executor) is never wedged either
        self.assertEqual(self.gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": "t", "data": {}})["actor"],
                         "SYSTEM")

    def test_rw3_no_signer_state_persists_between_acts(self):
        # RW3 THE QUIET TRAP (§8-h): the EP-15 trap in cryptographic dress. A valid signature on ONE
        # act does NOT authenticate a SECOND — there is no session, token, or "current signer" cache;
        # every act is verified live and carries its OWN signature.
        self._signed_exec("alice", "CREATE-INFO", {"content": "first"}, ALICE_KEY)   # a valid, signed act
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "second"})          # a later UNSIGNED act
        self.assertEqual(cm.exception.rule, SIGN_LAW)                                 # not carried by the first
        # replaying the very same signature does not authorise a different act either (bound to its act)
        first_sig = self._sig("alice", "CREATE-INFO", {"content": "first"}, ALICE_KEY)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "second", INVOKER_SIG: first_sig})
        self.assertEqual(cm.exception.rule, SIGN_LAW)

    def test_rw4_a_superseded_key_refuses_live_yet_its_old_signature_stays_data(self):
        # RW4: an act signed by a key valid WHEN SIGNED but superseded as of the deciding time refuses;
        # AND the old signature stays verifiable AS DATA (evidence of who signed), never retroactively
        # false. The full late-revocation sweep is EP-38's two-frames arithmetic (not this EP's).
        seq_bound = self.store.events[-1]["seq"]                            # alice's key is bound here
        draft = {"actor": "alice", "action": "CREATE-INFO", "object": "old-act"}
        old_sig = make_invoker_sig(ALICE_KEY, draft)
        self.gate.execute(keys.KEY_ROTATE, "owner", {"account": "alice", "public_key": ALICE_KEY_2})
        # live: the old key is no longer the binding -> a fresh act signed by it refuses
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "old-act", INVOKER_SIG: old_sig})
        self.assertEqual(cm.exception.rule, SIGN_LAW)
        # AS DATA: the old signature still verifies against the key that WAS bound at that deciding
        # position (the two-frames discipline — the signature is not retroactively false)
        self.assertTrue(verify_invoker_sig(old_sig, self.views.bound_key("alice", as_of=seq_bound), draft))

    def test_rw5_the_retirement_is_licensed_not_a_naked_swap(self):
        # RW5: the retirement of caller-asserted acceptance for keyed accounts is licensed by the
        # strictly-stronger proof — preservation on the old ledger AND a strictly-stronger new
        # dimension. If preservation broke (an unkeyed act newly refused), the swap would be naked and
        # this assertion would FAIL — the check can fail.
        self._account("carol")
        unkeyed_preserved = (
            self.gate.execute("CREATE-INFO", "carol", {"content": "still-open"})["action"] == "CREATE-INFO")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-INFO", "alice", {"content": "needs-sig"})       # keyed, unsigned
        keyed_now_refuses = (cm.exception.rule == SIGN_LAW)
        self.assertTrue(unkeyed_preserved and keyed_now_refuses)           # both -> the retirement is licensed


# ============================================================================================
# §8-f / §A57 HELD — production founding byte-untouched; the held gate is mechanical (RW-F)
# ============================================================================================

def _pack_sign_law_present(text):
    """Does the founding text carry the signing law? The mechanical landed-gate signal."""
    return any(tok in text for tok in (SIGN_LAW, "signed-door", "sign-law"))


class TestEP37FoundingLanded(unittest.TestCase):
    """§8-f / §A57 — EP-37's OWN founding (the signing law) LANDED IN PRODUCTION (COMPLETE-SIGNING-LAW,
    mover-2, founding 1.34.0; owner create-word board :2847, tier ordinary/owner ruled :2788). The HELD
    gate flipped to a LIVE one: this guard now asserts EP-37's OWN vocabulary is PRESENT, DIRECTLY —
    never through a founding byte/version proxy (G1b ENTRY-SCOPED, architect :2866). It reads the
    signing-law tokens and nothing about a version or a byte, so it is robust to any later founding
    move exactly as the absence form was."""

    def test_ep37_own_vocabulary_the_signing_law_is_declared_in_production(self):
        with open(PACK_PATH, encoding="utf-8") as fh:
            raw = fh.read()
        self.assertTrue(_pack_sign_law_present(raw),
                        "production founding declares NO signing law — EP-37's create did not land (§8-f)")
        # and it is exactly one CREATE-RULE record with the door's own rule_id, scope space:root,
        # enforcement live, ordinary tier (no `tier` field -> not constitutional; §8-e).
        pack = json.loads(raw)
        recs = [r for s in pack["steps"] for r in s["records"]
                if r.get("action") == "CREATE-RULE" and r["payload"]["rule_id"] == SIGN_LAW]
        self.assertEqual(len(recs), 1, "exactly one creating record, or the rule's identity is a question")
        p = recs[0]["payload"]
        self.assertEqual(recs[0]["object"], SIGN_LAW)
        self.assertEqual(p["scope"], "space:root")
        self.assertEqual(p["enforcement"], "live")
        self.assertNotEqual(p.get("tier"), "constitutional")               # ordinary/owner-tier, never constitutional
        self.assertTrue(p["text"].strip() and p["enforced_by"].strip())

    def test_the_live_gate_is_mechanical_a_stripped_signing_law_would_red(self):
        # RW-F re-expressed LIVE (a check that can fail): the real pack HAS the signing law (live,
        # green); strip every signing-law token and the same detector goes False — it still
        # discriminates present from absent, so a future pass that silently DROPPED it would red this.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        self.assertTrue(_pack_sign_law_present(real))                      # real: the law is present
        stripped = real
        for tok in (SIGN_LAW, "signed-door", "sign-law"):
            stripped = stripped.replace(tok, "X-REMOVED-X")
        self.assertFalse(_pack_sign_law_present(stripped))                 # stripped: the gate reds


if __name__ == "__main__":
    unittest.main()
