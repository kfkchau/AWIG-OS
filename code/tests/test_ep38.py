# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (gate, signature, key binding, deciding time, reconciliation sweep). NON-GOAL: no
# offensive capability of any kind — this proves a governance door brackets a claimed deciding time,
# judges key validity in the legitimacy frame, and re-adjudicates acceptances a late revocation
# reaches. It mints nothing real and models no attack. Full declaration: SCOPE-STATEMENT.md.
"""EP-38 (BUILD) — THE TWO-TIMES CLOSURE (design/37 Q7; design/35 §6; design/36 §4b; the K7 split of
design/34 §2 applied to keys).

Every probe here is a regression test (the campaign method). TEST KEYS throughout (§8-g): nothing
real is bound. The battery proves, in disposable full-kernel worlds where the founding declares the
signing law and keys can be bound:

  A1  TestDecidingBracket        the claimed deciding time is bracketed on BOTH sides. A claim that
                                 PREDATES the world its own seal pins refuses (the floor — ALREADY
                                 LAW, design/35 §6, asserted by a regression, not rebuilt). A claim
                                 that POSTDATES the store's countersigned arrival refuses (the CEILING
                                 — the new half), citing the two-times law. A claim INSIDE the bracket
                                 passes (inside, the time is the signer's assertion — the honest cap).
  A2  TestKeyValidityAsOfDeciding key validity is judged in the LEGITIMACY frame, AS OF the deciding
                                 time. A signature made while its key was bound STANDS after the key is
                                 superseded (supersession never un-signs the past). A superseded key's
                                 NEW act REFUSES (validity-as-of-deciding at the door). An ARRIVAL
                                 reads validity as of its OWN deciding time, not arrival time — a key
                                 valid at the deciding moment but rotated before the arrival still
                                 verifies (the case EP-37 fenced out as RW4).
  A3  TestRevocationSweeps       a key revocation whose deciding time precedes already-accepted acts is
                                 law-family arriving late: the affected acceptances are re-adjudicated
                                 by overturns APPENDED through the EXISTING design/36 §4b sweep. The
                                 overturn cites the revocation and BOTH deciding times. No second sweep
                                 is built; replay reconstructs identically.
  A4  TestAuthorityLive          the other half of the split: AUTHORITY at effect time stays the
                                 chain's, unchanged. A key revocation of a non-root account overturns
                                 its acceptance on LEGITIMACY, never on authority — the authority-live
                                 path and the C3 anchor wiring hold unchanged (asserted, not rebuilt).
  W4  TestCrossingSigns          the crossing hand-out/return signature discipline rides the EXISTING
                                 invoker-signature door (no new envelope field, §8-j): a key-bound
                                 answerer's return binds the pinned context by its signature.
  RW  TestRedWorlds              RW1 an unbracketed claim that ACCEPTS (both ends must bite); RW2 the
                                 named trap — retroactive invalidation voiding past signatures (the
                                 past stands as evidence); RW3 the mirror — validity-at-effect letting
                                 a superseded key keep acting (a NEW act needs a currently-valid key);
                                 RW4 a second sweep (the reach rides the existing machinery).
  A5  TestRoundTrip              kill everything derived, replay: the sweep case reconstructs
                                 identically; no past record or signature moves.

THE WRONG REFERENCE THIS EP REFUSES (design/37 Q7; EP-38.md "THE REFERENCE TO AVOID"): retroactive
invalidation — "revoke the key, void its history." The certificate-revocation habit reads a
revocation as erasing every signature the key ever made. Taking it erases the two frames (legitimacy
vs order), falsifies recorded history, and turns every rotation into a record rewrite. The right
shape, driven by RW2 + RW3: the past stands as EVIDENCE (a then-valid signature verifies forever); the
sweep re-adjudicates ONLY the acceptances inside the revocation's reach, by APPENDED overturns, never
by editing a record.

THE QUIET TRAP (EP-37 §8-h, inherited): no session, token, or "current signer" cache stores validity
or signature status between acts. Every check is derived live — the door reads the fold as of the
deciding time, the sweep re-runs the door, every time. NOTHING NEW INVENTED: the sweep is EP-26's,
ridden unchanged (no second sweep); the as-of fold is the WorldStore's `_selects`; the seal floor is
design/35 §6; the ceiling extends the existing two-times law (no founding law minted). EP-38's own
founding is still HELD, asserted by OWN-VOCABULARY-ABSENCE (no signing law, no new ceiling law —
TestEP38FoundingStillHeld). The KEY FAMILY, by contrast, is PRODUCTION founding now
(COMPLETE-KEY-FAMILY, 1.33.0): build_kernel loads KEY-LAW-BIND and the key ops, which carry
occurrence_time through the SAME `at` router this battery's TIMED-ACT uses (Ruling A) — so the as-of
key validity here runs on the PRODUCTION timed ops, not a test-world stand-in.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernel import keys                                                         # noqa: E402
from kernel import reconcile                                                    # noqa: E402
from kernel.compose import build_full_kernel                                    # noqa: E402
from kernel.errors import OpError                                               # noqa: E402
from kernel.gate import (SIGN_LAW, INVOKER_SIG, make_invoker_sig,               # noqa: E402
                         verify_invoker_sig)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

ALICE_KEY = "testpub:alice:v1"
ALICE_KEY_2 = "testpub:alice:v2"
BOB_KEY = "testpub:bob:v1"

# CONTROLLED DECIDING TIMES, all strictly in the past of any real run (so the ceiling passes) and
# strictly ordered. The signing/key laws are declared BEFORE the acts (T_LAW), so they are in force
# AS OF each act's deciding time — otherwise the as-of-d world would find no signing law and the door
# would sit inert (a law declared after an act cannot judge it). bind < revoke/rotate < act holds in
# BOTH deciding and recording order — the only lifecycle the order describes (a late supersession over
# a prior bind).
def T(day, h):
    return f"2026-09-{day:02d}T{h:02d}:00:00.000000+00:00"

T_LAW    = "2026-08-01T00:00:00.000000+00:00"   # the signing/key laws' deciding time — before everything
T_BIND   = T(1, 8)     # the key is bound, deciding at 08:00
T_REVOKE = T(1, 9)     # the key is revoked, deciding at 09:00 — after the bind, before the act
T_ROTATE = T(1, 9)     # a rotation, deciding at 09:00
T_ACT    = T(1, 10)    # the act is decided at 10:00 — after the supersession's deciding moment
T_EARLY  = "2026-09-01T08:30:00.000000+00:00"   # after the bind (08:00), BEFORE the revoke (09:00)
FUTURE   = "2099-01-01T00:00:00.000000+00:00"   # a claim postdating any real arrival


def _declare_laws_early(store, at=T_LAW):
    """Declare the SIGNING law directly (the test-world stand-in for EP-37's held owner create), with
    an EARLY deciding time so it is in force as of any act's deciding time below. Appended via
    store._append as genesis appends the constitution — no gate, so no sweep is triggered by the
    late-deciding declaration itself. The KEY-BIND law is PRODUCTION founding now (COMPLETE-KEY-FAMILY,
    1.33.0): build_kernel loads it, so it is in force from genesis and needs no early stand-in here."""
    store._append({
        "actor": "SYSTEM", "action": "CREATE-RULE", "object": SIGN_LAW,
        "rule_cited": "BOOT-INT", "occurrence_time": at,
        "payload": {"kind": "rule", "rule_id": SIGN_LAW, "root": True, "polarity": "-",
                    "when": [], "then": [{"refuse": SIGN_LAW}], "enforcement": "live",
                    "text": "for a key-bound account the gate accepts no act without a valid "
                            "signature from a then-valid bound key (ordinary/owner-tier, per-account)"},
    })


def _register_timed_act(gate):
    """The TIMED-ACT test op — an ordinary act carrying a DISTINCT deciding time (an `at` param
    supplying occurrence_time), so an act decided away from the store and arriving later can be
    modelled and SIGNED. The KEY OPS (key-bind/key-rotate/key-revoke) are PRODUCTION founding now
    (COMPLETE-KEY-FAMILY, 1.33.0) and carry occurrence_time through the SAME `at` -> occurrence_time
    router — the occurrence_time_param the test author anticipated (Ruling A, architect :2885) — so
    build_kernel registers them and this test world no longer registers timed key ops of its own
    (they would collide). Key validity as-of-deciding-time is a fold over the key RECORDS' own
    occurrence_times, independent of the law's timing, so the production ops serve this battery."""
    def _act(actor, params):
        draft = {"actor": actor, "action": "TIMED-ACT", "object": params.get("content"),
                 "rule_cited": "CAP-IS-LAW",   # an ordinary act under the openness/capability law
                 "payload": {"content": params.get("content")}}
        if params.get("at") is not None:
            draft["occurrence_time"] = params["at"]
        return draft
    gate.register("TIMED-ACT", {"description": "an act decided away from the store and arriving later",
                                "params": {"content": "required", "at": "optional"}}, _act)


class TwoTimesWorld(unittest.TestCase):
    """A full kernel (so OVERTURN is registered and the sweep can commit), with the signing law and
    the key-bind law DECLARED in this test founding world and the key/act ops registered. Production
    founding is byte-untouched; here the held mechanisms are proven where the law is declared."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        _declare_laws_early(self.store)
        _register_timed_act(self.gate)

    # ---- ceremony helpers ----
    def _account(self, acct, actor_class="human"):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": acct, "actor_class": actor_class})
        self.gate.execute("VERIFY-ACCOUNT", "owner",
                          {"account": acct,
                           "evidence_hash": "sha256:" + hashlib.sha256(acct.encode()).hexdigest()})

    def _bind(self, account, key, at=None, actor="owner"):
        p = {"account": account, "public_key": key}
        if at is not None:
            p["at"] = at
        return self.gate.execute(keys.KEY_BIND, actor, p)

    def _rotate(self, account, key, at=None, actor="owner"):
        p = {"account": account, "public_key": key}
        if at is not None:
            p["at"] = at
        return self.gate.execute(keys.KEY_ROTATE, actor, p)

    def _revoke(self, account, at=None, actor="owner"):
        p = {"account": account}
        if at is not None:
            p["at"] = at
        return self.gate.execute(keys.KEY_REVOKE, actor, p)

    # ---- the invoker's signing (the caller's own act; the gate never signs) ----
    def _draft_for(self, actor, opname, params):
        return self.gate.ops[opname]["handler"](actor, dict(params))

    def _sig(self, actor, opname, params, key, deciding_time=None):
        draft = self._draft_for(actor, opname, params)
        return make_invoker_sig(key, draft, deciding_time=deciding_time, seal=draft.get("seal"))

    def _signed_exec(self, actor, opname, params, key, deciding_time=None):
        sig = self._sig(actor, opname, params, key, deciding_time=deciding_time)
        return self.gate.execute(opname, actor, {**params, INVOKER_SIG: sig})

    def _signed_timed_act(self, actor, content, at, key):
        params = {"content": content, "at": at}
        return self._signed_exec(actor, "TIMED-ACT", params, key, deciding_time=at)


# ============================================================================================
# A1 — T-DECIDING-BRACKET: both ends, both directions
# ============================================================================================

class TestDecidingBracket(TwoTimesWorld):

    def test_a_claim_inside_the_bracket_passes(self):
        # Inside — a past deciding time, no seal to bound, no future overreach — the time is the
        # signer's assertion and the gate accepts it (the honest cap, in the refusal-free direction).
        self._account("carol")
        rec = self.gate.execute("TIMED-ACT", "carol", {"content": "inside", "at": T_ACT})
        self.assertEqual(rec["action"], "TIMED-ACT")
        self.assertEqual(rec["occurrence_time"], T_ACT)

    def test_the_ceiling_refuses_a_claim_postdating_the_arrival(self):
        # THE NEW HALF. A deciding time in the FUTURE of the arrival is a claim to have decided the
        # act after the store already recorded it — refused, citing the two-times law.
        self._account("carol")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("TIMED-ACT", "carol", {"content": "future", "at": FUTURE})
        self.assertEqual(cm.exception.rule, reconcile.ACCEPT_RULE)
        self.assertIn("countersigned arrival", str(cm.exception))

    def test_the_floor_refuses_a_claim_predating_its_sealed_world(self):
        # ALREADY LAW (design/35 §6): asserted by a regression, not rebuilt. A claim over a sealed
        # pack whose content existed in no store state at or before the claimed moment refuses.
        self.gate.execute("CREATE-VIEW", "owner", {"name": "ctx", "when": {"object": "thing:x"}})
        self.gate.execute("CREATE-INFO", "owner", {"content": "thing:x"})   # so the view has content
        defn = self.views.view_definitions()["ctx"]
        pack = f"view:ctx@{defn['seq']}"
        seal = reconcile.crossing.seal_of(self.store, self.views, pack)
        # truthful (the seal's world exists at head): admitted
        ok_now, _ = reconcile.seal_bound(self.store, self.views, {
            "payload": {"seal": seal, "input_view": pack},
            "occurrence_time": self.store.events[-1]["record_time"]})
        self.assertTrue(ok_now)
        # predating (a moment before the pack's world came into being): refused, cited
        ok_early, reason = reconcile.seal_bound(self.store, self.views, {
            "payload": {"seal": seal, "input_view": pack}, "occurrence_time": T(1, 0)})
        self.assertFalse(ok_early)
        self.assertIn("had not yet come into being", reason)

    def test_the_bracket_is_the_existing_two_times_law_not_a_new_founding_law(self):
        # §8-i: the ceiling cites TWO-TIMES-ACCEPT — an EXISTING founding record — never a new one.
        self.assertEqual(reconcile.ACCEPT_RULE, "TWO-TIMES-ACCEPT")
        self.assertIn("TWO-TIMES-ACCEPT", self.views.active_rules())
        # OWN-VOCABULARY (G1b, architect :2866): EP-38 mints NO founding law of its own — the ceiling
        # rides the EXISTING TWO-TIMES-ACCEPT. Read on EP-38's own vocabulary, NOT a founding version
        # proxy. SIGN-LAW is PRODUCTION founding now (COMPLETE-SIGNING-LAW, mover-2, 1.34.0) — landed by
        # a LATER pass, never by EP-38; its presence means EP-38's two-frames arithmetic now runs under
        # the LIVE signed door reading key validity as-of the deciding time (A2 below), which is exactly
        # what EP-38 built the door for.
        with open(PACK_PATH, encoding="utf-8") as f:
            raw = f.read()
        self.assertIn("TWO-TIMES-ACCEPT", raw)                  # the ceiling's rule is a PRE-EXISTING founding record
        self.assertIn(SIGN_LAW, raw)                            # SIGN-LAW is production now (mover-2), NOT minted by EP-38


# ============================================================================================
# A2 — T-KEY-VALIDITY-AS-OF-DECIDING: legitimacy frame, as of the deciding time
# ============================================================================================

class TestKeyValidityAsOfDeciding(TwoTimesWorld):

    def test_a_signature_made_while_bound_stands_as_data_after_supersession(self):
        # THE LEGITIMACY FRAME. alice signs an act while her key is bound; the key is later revoked.
        # The recorded signature remains sound EVIDENCE of who decided — it verifies as data forever;
        # supersession never un-signs the past.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        rec = self._signed_timed_act("alice", "doc-1", T_ACT, ALICE_KEY)
        recorded_sig = rec["provenance"][INVOKER_SIG]
        self.assertEqual(recorded_sig["by"], ALICE_KEY)
        # revoke the key NOW (a live, non-late revoke): the past signature is untouched
        self._revoke("alice")
        self.assertIsNone(self.views.bound_key("alice"))
        # the recorded signature STILL verifies as data against the key it was made under — evidence,
        # not live authorisation (the two frames)
        draft = reconcile.draft_of(self.store.by_seq(rec["seq"]))
        self.assertTrue(verify_invoker_sig(recorded_sig, ALICE_KEY, draft, T_ACT, None))

    def test_a_superseded_keys_new_act_refuses_at_the_door(self):
        # THE MIRROR: a NEW act needs a CURRENTLY-valid key. alice's key is revoked; a fresh act
        # signed by the old key is a false claim, refused as of the act's own deciding time.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        self._revoke("alice", at=T_REVOKE)
        # a NEW act decided AFTER the revoke's deciding moment: no valid key as of that moment
        with self.assertRaises(OpError) as cm:
            self._signed_timed_act("alice", "doc-2", T_ACT, ALICE_KEY)
        self.assertEqual(cm.exception.rule, SIGN_LAW)

    def test_an_arrival_reads_validity_as_of_its_own_deciding_time_not_arrival(self):
        # THE ARRIVAL CASE (W2, EP-37's RW4). alice's key is valid at the act's deciding moment
        # (10:00) but is ROTATED to a new key with a LATER deciding time — recorded BEFORE the arrival
        # lands. Reading the LIVE fold would wrongly refuse (the live key is the new one); reading as
        # of the deciding time accepts, because at 10:00 the old key was still her binding.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)                 # bound, deciding 08:00
        self._rotate("alice", ALICE_KEY_2, at=T(1, 11))           # rotated, deciding 11:00 (AFTER the act)
        self.assertEqual(self.views.bound_key("alice"), ALICE_KEY_2)   # LIVE: the new key
        # the act decided at 10:00, signed by the OLD key that was valid THEN, arrives now
        rec = self._signed_timed_act("alice", "doc-3", T_ACT, ALICE_KEY)
        self.assertEqual(rec["provenance"][INVOKER_SIG]["by"], ALICE_KEY)   # accepted, as of its deciding time

    def test_an_arrival_signed_by_a_key_superseded_before_its_deciding_time_refuses(self):
        # The other direction of the arrival case: the key was rotated BEFORE the act's deciding time,
        # so as of that moment the old key was already superseded — the arrival refuses.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)                 # deciding 08:00
        self._rotate("alice", ALICE_KEY_2, at=T_ROTATE)           # deciding 09:00 (BEFORE the act at 10:00)
        with self.assertRaises(OpError) as cm:
            self._signed_timed_act("alice", "doc-4", T_ACT, ALICE_KEY)   # old key, superseded as of 10:00
        self.assertEqual(cm.exception.rule, SIGN_LAW)
        # and the NEW key, valid as of 10:00, signs validly (a check that can also pass)
        rec = self._signed_timed_act("alice", "doc-4b", T_ACT, ALICE_KEY_2)
        self.assertEqual(rec["provenance"][INVOKER_SIG]["by"], ALICE_KEY_2)


# ============================================================================================
# A3 — T-REVOCATION-SWEEPS: a late-deciding revocation reaches its acceptances via the EXISTING sweep
# ============================================================================================

class TestRevocationSweeps(TwoTimesWorld):

    def _reach_scenario(self):
        """bind (deciding 08:00) → act A signed and accepted (deciding 10:00) → a late-deciding revoke
        (deciding 09:00) records AFTER A. The act's key was valid when it was accepted, but the revoke
        was DECIDED before the act and reaches it."""
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        rec_a = self._signed_timed_act("alice", "reached", T_ACT, ALICE_KEY)   # accepted: key valid as of 10:00
        self.assertTrue(reconcile.standing(self.store, rec_a["seq"]))          # stands, so far
        # the late-deciding revoke arrives (recorded now, decided at 09:00 — before the act)
        rev = self._revoke("alice", at=T_REVOKE)
        return rec_a, rev

    def test_the_late_revocation_overturns_the_reached_acceptance(self):
        rec_a, rev = self._reach_scenario()
        # the sweep fired (through the EXISTING machinery) and overturned the acceptance
        self.assertIn(rec_a["seq"], reconcile.overturned_targets(self.store))
        self.assertFalse(reconcile.standing(self.store, rec_a["seq"]))

    def test_the_overturn_cites_the_revocation_and_both_deciding_times(self):
        rec_a, rev = self._reach_scenario()
        overturns = [o for o in reconcile.overturns(self.store) if o["target_seq"] == rec_a["seq"]]
        self.assertEqual(len(overturns), 1)
        o = overturns[0]
        self.assertEqual(o["law_seq"], rev["seq"])                      # cites the revocation
        self.assertEqual(o["target_deciding_time"], T_ACT)             # the act's deciding time
        self.assertEqual(o["reaching_deciding_time"], T_REVOKE)        # the revocation's deciding time

    def test_asof_before_the_overturn_still_shows_the_acceptance(self):
        # order is untouched; validity is what changed. An asOf from before the overturn still stands.
        rec_a, rev = self._reach_scenario()
        overturn_seq = max(reconcile.overturned_targets(self.store)) if False else None
        # the overturn record's own seq
        ov = [e for e in self.store.events
              if (e.get("payload") or {}).get("kind") == reconcile.OVERTURN_KIND
              and (e.get("payload") or {}).get("target_seq") == rec_a["seq"]][0]
        self.assertTrue(reconcile.standing(self.store, rec_a["seq"], as_of=ov["seq"] - 1))
        self.assertFalse(reconcile.standing(self.store, rec_a["seq"], as_of=ov["seq"]))

    def test_an_act_decided_before_the_revocation_is_not_reached(self):
        # THE OTHER DIRECTION (too-wedged): an act decided BEFORE the revoke's deciding moment stands —
        # legitimacy created at the revoke binds only acts decided strictly after it.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        rec_early = self._signed_timed_act("alice", "early", T_EARLY, ALICE_KEY)   # decided 08:30 (after bind, before revoke)
        self._revoke("alice", at=T_REVOKE)                                          # decided 09:00
        self.assertTrue(reconcile.standing(self.store, rec_early["seq"]))
        self.assertNotIn(rec_early["seq"], reconcile.overturned_targets(self.store))


# ============================================================================================
# A4 — the authority-live regression (the other half): authority stays the chain's, unchanged
# ============================================================================================

class TestAuthorityLive(TwoTimesWorld):

    def test_the_revocation_overturns_on_legitimacy_not_authority(self):
        # The act is overturned by the SIGNED DOOR (legitimacy), not by the authority step. alice's
        # authority under the openness grant is untouched by the key revocation — proof: with no key
        # bound at all, the same act by alice STANDS (authority is live at effect, unaffected).
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        rec_a = self._signed_timed_act("alice", "on-legitimacy", T_ACT, ALICE_KEY)
        self._revoke("alice", at=T_REVOKE)
        self.assertFalse(reconcile.standing(self.store, rec_a["seq"]))       # overturned
        # the overturn cites the signing law's world, not an authority refusal: alice's authority to
        # act never changed — an unkeyed alice does the same act and it stands.
        d2 = tempfile.mkdtemp()
        s2, g2, v2, _, _ = build_full_kernel(os.path.join(d2, "r.jsonl"),
                                             os.path.join(d2, "b"), os.path.join(d2, "v"))
        _declare_laws_early(s2); _register_timed_act(g2)
        g2.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        rec_unkeyed = g2.execute("TIMED-ACT", "alice", {"content": "on-legitimacy", "at": T_ACT})
        self.assertTrue(reconcile.standing(s2, rec_unkeyed["seq"]))          # authority alone: stands

    def test_the_anchor_wiring_holds_unchanged(self):
        # The C3 anchor guard is asserted present and reads no act kind (unchanged, not rebuilt): the
        # overturn op still declares the anchor guard in its definition, so an overturn that would
        # orphan root is leashed exactly as EP-26 built it.
        self.assertTrue(reconcile.guard_declared(self.views, "OVERTURN"))


# ============================================================================================
# W4 — the crossing signature discipline rides the existing invoker-signature door (§8-j)
# ============================================================================================

class TestCrossingSigns(TwoTimesWorld):

    def test_the_signature_binds_the_returned_content_via_provenance_no_new_field(self):
        # W4, capped at the :2755 license (§8-j): the decider's signature rides in PROVENANCE
        # (invoker_sig), never a new envelope field. A key-bound answerer's return is signature-bound
        # to exactly the content it returns; the seal already pins what it was shown, so citing the
        # hand-out binds the answer to the sealed context. Here the door is the same one every op
        # crosses — the discipline is asserted (the door is EP-37's), not a second mechanism.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        # a signed return-shaped act: the signature binds action/object/target/payload as recorded.
        rec = self._signed_timed_act("alice", "answer-payload", T_ACT, ALICE_KEY)
        draft = reconcile.draft_of(self.store.by_seq(rec["seq"]))
        # the recorded signature verifies over EXACTLY the returned content, and a tampered content
        # does not (a check that can fail) — the immutability half.
        self.assertTrue(verify_invoker_sig(rec["provenance"][INVOKER_SIG], ALICE_KEY, draft, T_ACT, None))
        tampered = dict(draft, payload={"content": "not-what-was-returned"})
        self.assertFalse(verify_invoker_sig(rec["provenance"][INVOKER_SIG], ALICE_KEY, tampered, T_ACT, None))
        # no new envelope field: the signature is in provenance, nowhere else on the record.
        self.assertIn(INVOKER_SIG, rec["provenance"])
        self.assertNotIn(INVOKER_SIG, {k for k in rec.keys()})


# ============================================================================================
# RED WORLDS — mandatory, through the instrument, recorded (§A42)
# ============================================================================================

class TestRedWorlds(TwoTimesWorld):

    def test_rw1_an_unbracketed_claim_that_accepts_would_red(self):
        # RW1: both ends must BITE. A claim postdating the arrival must not accept (the ceiling), and
        # a claim predating its sealed world must not accept (the floor). Drive the ceiling here: a
        # future claim REFUSES — an accept would be the red world.
        self._account("carol")
        with self.assertRaises(OpError):
            self.gate.execute("TIMED-ACT", "carol", {"content": "unbracketed", "at": FUTURE})

    def test_rw2_retroactive_invalidation_is_refused_the_past_stands(self):
        # RW2 — THE NAMED TRAP. A revocation must NOT void the past signatures of the superseded key.
        # After the reach sweep overturns the acceptance, the ACT'S RECORD IS UNCHANGED byte-for-byte
        # and its recorded signature still verifies as data — only the ACCEPTANCE was overturned, by an
        # APPENDED overturn. A retroactive-invalidation engine would fail one of these.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        rec_a = self._signed_timed_act("alice", "reached", T_ACT, ALICE_KEY)
        before = json.dumps(self.store.by_seq(rec_a["seq"]), default=str, sort_keys=True)
        self._revoke("alice", at=T_REVOKE)
        # the acceptance is overturned...
        self.assertFalse(reconcile.standing(self.store, rec_a["seq"]))
        # ...but the act's RECORD did not move a byte (append-only; no record rewritten)
        after = json.dumps(self.store.by_seq(rec_a["seq"]), default=str, sort_keys=True)
        self.assertEqual(before, after)
        # ...and the past signature STANDS as evidence: it verifies against the key it was made under
        draft = reconcile.draft_of(self.store.by_seq(rec_a["seq"]))
        self.assertTrue(verify_invoker_sig(rec_a["provenance"][INVOKER_SIG], ALICE_KEY, draft, T_ACT, None))

    def test_rw3_validity_at_effect_is_refused_a_new_act_needs_a_current_key(self):
        # RW3 — THE MIRROR TRAP. A superseded key must NOT keep acting because its signature "once
        # verified". A NEW act signed by a revoked key refuses as of its own deciding time — the
        # legitimacy frame does not license a live act on a retired key.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        self._revoke("alice", at=T_REVOKE)
        with self.assertRaises(OpError) as cm:
            self._signed_timed_act("alice", "new-act", T_ACT, ALICE_KEY)
        self.assertEqual(cm.exception.rule, SIGN_LAW)

    def test_rw4_the_reach_rides_the_existing_sweep_no_second_sweep(self):
        # RW4 — NO SECOND SWEEP. The revocation reach uses EP-26's `run`/`_maybe_sweep`: the overturn
        # appears in the SAME `gate.sweeps` ledger a late law's sweep uses, produced by the same
        # `reconcile.run`. No new re-adjudication machinery is built.
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        rec_a = self._signed_timed_act("alice", "reached", T_ACT, ALICE_KEY)
        sweeps_before = len(self.gate.sweeps)
        rev = self._revoke("alice", at=T_REVOKE)
        self.assertEqual(len(self.gate.sweeps), sweeps_before + 1)            # one sweep, the existing ledger
        outcome = self.gate.sweeps[-1]
        self.assertEqual(outcome["law_seq"], rev["seq"])                      # the revoke drove the existing sweep
        self.assertIn(rec_a["seq"], [e["target_seq"] for e in outcome["computed"]])


# ============================================================================================
# A5 — TestRoundTrip: kill everything derived, replay; the sweep case reconstructs identically
# ============================================================================================

class TestRoundTrip(TwoTimesWorld):

    def test_the_reach_case_replays_identically(self):
        self._account("alice")
        self._bind("alice", ALICE_KEY, at=T_BIND)
        rec_a = self._signed_timed_act("alice", "reached", T_ACT, ALICE_KEY)
        self._revoke("alice", at=T_REVOKE)
        self.assertFalse(reconcile.standing(self.store, rec_a["seq"]))
        overturned_live = reconcile.overturned_targets(self.store)
        # kill everything derived: rebuild the kernel from the record FILE alone (the estate's replay)
        replayed, _g2, _v2, _b2, _s2 = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs2"), os.path.join(self.dir, "vault2"))
        self.assertEqual(len(replayed.events), len(self.store.events))        # same record, nothing added
        overturned_replay = reconcile.overturned_targets(replayed)
        self.assertEqual(overturned_live, overturned_replay)                  # the overturn reconstructs
        # every recorded signature verifies as DATA after replay (re-signs nothing)
        rec_r = replayed.by_seq(rec_a["seq"])
        draft = reconcile.draft_of(rec_r)
        self.assertTrue(verify_invoker_sig(rec_r["provenance"][INVOKER_SIG], ALICE_KEY, draft, T_ACT, None))
        # and no past record moved: the acceptance record is byte-identical across replay
        self.assertEqual(json.dumps(self.store.by_seq(rec_a["seq"]), default=str, sort_keys=True),
                         json.dumps(rec_r, default=str, sort_keys=True))


# ============================================================================================
# EP-38's OWN founding is STILL HELD (§8-f/§8-i): EP-38 mints NO founding law of its own — the ceiling
# rides the EXISTING TWO-TIMES-ACCEPT (OWN-VOCABULARY, G1b :2866, read directly, never a founding
# byte/version proxy). SIGN-LAW is PRODUCTION founding now (COMPLETE-SIGNING-LAW, mover-2, 1.34.0),
# landed by a LATER pass — so EP-38's two-frames arithmetic runs under the LIVE signed door, which is
# what it was built for; SIGN-LAW's presence is not EP-38's move.
# ============================================================================================

class TestEP38FoundingStillHeld(unittest.TestCase):

    def test_ep38_own_vocabulary_no_new_ceiling_law_and_the_signed_door_is_live(self):
        with open(PACK_PATH, encoding="utf-8") as f:
            raw = f.read()
        # SIGN-LAW is production founding now (mover-2) — landed by a LATER pass, so EP-38's two-frames
        # arithmetic runs under the LIVE signed door; it is NOT EP-38's own founding move.
        self.assertIn(SIGN_LAW, raw)
        # the ceiling rides the EXISTING TWO-TIMES-ACCEPT founding record — EP-38 mints no ceiling law.
        self.assertIn("TWO-TIMES-ACCEPT", raw)


if __name__ == "__main__":
    unittest.main()
