# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (live rules, held stage, scope, handshake check, separation of powers). NON-GOAL: no
# offensive capability of any kind — every assertion proves B8/I8/I16 by function: what a machine
# HOLDS is a computed fact of its live rules (never a founding declaration), a machine meeting
# another cannot claim a stage it already holds for the same scope, and no one actor holds decision,
# enforcement and monitoring together. Full declaration: SCOPE-STATEMENT.md.
"""C6 P6 — THE LIVE-STAGES VIEW AND THE HANDSHAKE CHECK (design/52 v2.0 B8:57, I8:80, I16:88,
L26:124, Q2:179 discharged; plan planning/exec/P6-LIVE-STAGES-HANDSHAKE-BUILD.md).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). NO FOUNDING (L26, Q2 discharged): what a machine holds is COMPUTED from
its LIVE rules per scope, never declared at founding; the checks are real over live rules with NO
new op/law/check kind and NO pack edit. The live-stages view reads `active_rules` (READ and reused);
the handshake check consumes P7 (the handshake relation over the crossing/receipt, FROZEN 668441d9,
its live-relation view settled in views.py) as the occasion two machines meet, and runs over BOTH
records' live rules — each machine folding its OWN record (one pen per record, I1), the module-level
check comparing the two presentations (two records are never folded as one truth, I2).

  A1 (B8, L26)  HELD STAGES COMPUTED FROM LIVE RULES — the live-stages view reads what stages a
                machine holds per scope from its `active_rules`; a stage held under a live rule
                appears, one whose rule is ABSENT or WITHDRAWN does not; the HOLDER is the rule's own
                minting actor (a claim is an act); nothing is read from a founding declaration; the
                fold is over this record alone and round-trips (kill it, replay, identical, P2).
  A2 (I8)       THE HANDSHAKE REFUSES A DOUBLE-CLAIM — at a handshake, over BOTH records' live rules,
                a second machine claiming a (stage, scope) another machine holds for the SAME scope
                is refused BY NAME and the planted double-claim reds (the check can fail); disjoint
                scopes or a single holder pass; each presentation is from its own record (I1).
  A3 (I16)      NO ONE ACTOR HOLDS ALL THREE — a declared stage set placing decision, enforcement AND
                monitoring on one actor for one scope is refused (rides protection.SOP); any two of
                the three pass (the control is able-to-fail).
  A4 (L26, Q2)  NO FOUNDING — no new op/law/check kind and no pack edit: the founding pack carries no
                stage vocabulary, the row shape gains no field (I9), OP_CHECKS stays 19 and the
                attested member set stays 54 (no new src module — the rider is inert).

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect): a planted double-claim refused beside a disjoint-scope pass; all three powers refused
beside a two-power pass; a withdrawn stage that had been present.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                                     # noqa: E402
from kernel.errors import OpError                                               # noqa: E402
from kernel import border                                                       # noqa: E402
from kernel.protection import SOP                                               # noqa: E402
from kernel.views import (handshake_double_claim, refuse_double_claim,          # noqa: E402
                          separation_of_powers_conflicts, refuse_separation_of_powers,
                          THREE_POWERS)

_REPO = os.path.join(os.path.dirname(__file__), "..")


def _body(prefix, entity, actor_class="program"):   # P8b companion (archi :3726, disclosed): a MACHINE
    # body doing structured governance ops (CREATE-RULE / stage-holding, cell S) is a PROGRAM (software,
    # structured-arm), not an AI — the live pairing (P8b) refuses an ai-class actor at a raw S op; the
    # stage-holding subject is unchanged (an incidental fixture default moved by the later law).
    """One MACHINE — an independent record (its own data dir), gate and views, with `entity`
    established as an account (a body writes only its own record, one pen per record)."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": entity, "actor_class": actor_class})
    return d, store, gate, views


def _hold_stage(gate, holder, rule_id, stage, scope, minter="owner"):
    """A stage-holding CLAIM: a LIVE rule (CREATE-RULE) self-declaring the stage on the EXISTING
    accepted params — `policy_key` the marker, `value` the stage, `scope` the scope, and the HOLDER
    (I16's actor the constitution assigns the stage to) on the `text` string param. Minted by the
    authority (`minter`, default the root `owner` — the constitution assigns powers; named actors
    do not self-grant). No founding, no new row field (policy_key/value/scope/text are shipped
    CREATE-RULE params)."""
    return gate.execute("CREATE-RULE", minter,
                        {"rule_id": rule_id, "policy_key": "held_stage",
                         "value": stage, "scope": scope, "text": holder})


def _body_name(store, key):
    return border.from_body_name(key, border.genesis_hash(store))


# =================================================================================================
# A1 — HELD STAGES COMPUTED FROM LIVE RULES (B8, L26)
# =================================================================================================

class TestHeldStagesFromLiveRules(unittest.TestCase):
    def setUp(self):
        self.d, self.store, self.gate, self.views = _body("p6-a1-", "gov")

    def test_a_stage_held_under_a_live_rule_appears(self):
        """B8/L26: a machine holds a stage for a scope when a LIVE rule of that stage covers that
        scope — read from `active_rules`, never a founding declaration. The holder is the rule's own
        minting actor (a claim is an act)."""
        _hold_stage(self.gate, "gov", "R-DEC", "decision", "fisheries")
        held = self.views.held_stages()
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["stage"], "decision")
        self.assertEqual(held[0]["scope"], "fisheries")
        self.assertEqual(held[0]["actor"], "gov")                          # the holder is the minting actor
        self.assertIn(("decision", "fisheries"), self.views.held_stage_scopes())

    def test_a_stage_never_declared_is_absent(self):
        """A1: a machine that has not acted holds nothing — held_stages is empty and a (stage, scope)
        never declared is absent (never a stored placeholder)."""
        self.assertEqual(self.views.held_stages(), [])                     # nothing minted -> holds nothing
        self.assertEqual(self.views.held_stage_scopes(), set())
        _hold_stage(self.gate, "gov", "R-DEC", "decision", "fisheries")
        self.assertNotIn(("decision", "forestry"), self.views.held_stage_scopes())   # other scope absent
        self.assertNotIn(("enforcement", "fisheries"), self.views.held_stage_scopes())  # other stage absent

    def test_a_withdrawn_stage_drops_out(self):
        """A1: a stage whose rule is WITHDRAWN does not appear. Withdrawal is superseding the rule_id
        (latest-wins `active_rules`) with a version that no longer declares the marker — existing
        vocabulary, no new op. Able-to-fail: the stage was present BEFORE the withdrawal."""
        _hold_stage(self.gate, "gov", "R-DEC", "decision", "fisheries")
        self.assertIn(("decision", "fisheries"), self.views.held_stage_scopes())   # present first
        # supersede R-DEC with an ordinary policy rule (drops the held_stage marker) -> withdrawn.
        self.gate.execute("CREATE-RULE", "gov", {"rule_id": "R-DEC", "policy_key": "quota", "value": "high"})
        self.assertNotIn(("decision", "fisheries"), self.views.held_stage_scopes())  # dropped out
        self.assertEqual(self.views.held_stages(), [])

    def test_nothing_is_read_from_a_founding_declaration(self):
        """L26/Q2: holdings come from LIVE rules, not founding. A fresh machine (genesis + an
        account, no stage rule) holds nothing; the stage appears only after a runtime CREATE-RULE."""
        self.assertEqual(self.views.held_stages(), [])                     # founding declares no stage
        _hold_stage(self.gate, "gov", "R-MON", "monitoring", "water")
        self.assertIn(("monitoring", "water"), self.views.held_stage_scopes())

    def test_the_fold_is_over_this_record_alone_and_round_trips(self):
        """A1/P2: the live-stages view is a FOLD over this machine's own rows — recomputed from those
        rows alone equals the served state. A fresh kernel over the same record file reconstructs an
        identical answer (kill it, replay, identical)."""
        _hold_stage(self.gate, "gov", "R-DEC", "decision", "fisheries")
        _hold_stage(self.gate, "gov", "R-ENF", "enforcement", "fisheries")
        served = self.views.held_stages()
        _s2, _g2, v2, _b2, _u2 = build_full_kernel(
            os.path.join(self.d, "record.jsonl"), os.path.join(self.d, "blobs"),
            os.path.join(self.d, "vault"))
        self.assertEqual(v2.held_stages(), served)
        self.assertEqual(v2.held_stage_scopes(), self.views.held_stage_scopes())


# =================================================================================================
# A2 — THE HANDSHAKE REFUSES A DOUBLE-CLAIM (I8)
# =================================================================================================

class TestHandshakeDoubleClaim(unittest.TestCase):
    def setUp(self):
        # two MACHINES, each its own record (one pen per record, I1).
        self.ad, self.a_store, self.a_gate, self.a_views = _body("p6-a2-a-", "gov-a")
        self.bd, self.b_store, self.b_gate, self.b_views = _body("p6-a2-b-", "gov-b")
        self.a_name = _body_name(self.a_store, "ed25519-pub:a")
        self.b_name = _body_name(self.b_store, "ed25519-pub:b")

    def _handshake(self):
        """Consume P7: the two machines enter a handshake relation (a declare crossing each, the
        counterpart's RECEIPT the mutual half). This is the OCCASION the check runs over both
        records' live rules; the check itself compares presentations, not these crossings."""
        a_declare = border.submit(self.a_gate, "gov-a", {"handshake_relation": {"parent": self.b_name}}, actor="gov-a")
        b_declare = border.submit(self.b_gate, "gov-b", {"handshake_relation": {"parent": self.a_name}}, actor="gov-b")
        border.record_receipt(self.a_gate, border.content_id(b_declare), self.b_name, "ed25519-sig:b")
        border.record_receipt(self.b_gate, border.content_id(a_declare), self.a_name, "ed25519-sig:a")
        # each machine now holds a live handshake relation with the other (P7's view, reused).
        self.assertTrue(self.a_views.handshake_relation_live(border.content_id(a_declare)))
        self.assertTrue(self.b_views.handshake_relation_live(border.content_id(b_declare)))

    def test_a_second_machine_claiming_a_held_stage_for_the_same_scope_is_refused(self):
        """I8/B8: at the handshake, over BOTH records' live rules, a second machine claiming a
        (stage, scope) the other already holds for the SAME scope is REFUSED BY NAME. The planted
        double-claim reds (the check can fail)."""
        self._handshake()
        _hold_stage(self.a_gate, "gov-a", "R-DEC", "decision", "fisheries")   # machine A holds it first
        _hold_stage(self.b_gate, "gov-b", "R-DEC", "decision", "fisheries")   # machine B claims the same -> a double-claim
        here, there = self.a_views.held_stage_scopes(), self.b_views.held_stage_scopes()
        self.assertEqual(handshake_double_claim(here, there), {("decision", "fisheries")})  # the conflict, by name
        with self.assertRaises(OpError) as cm:
            refuse_double_claim(here, there)                                  # refused
        self.assertEqual(cm.exception.rule, "I8")
        self.assertIn("decision @ fisheries", str(cm.exception))             # by name

    def test_disjoint_scopes_pass(self):
        """I8: two machines holding the SAME stage for DIFFERENT scopes do NOT double-claim — the
        check passes (a control that cannot fail is the defect; here it passes because the scopes
        are disjoint)."""
        self._handshake()
        _hold_stage(self.a_gate, "gov-a", "R-DEC", "decision", "fisheries")
        _hold_stage(self.b_gate, "gov-b", "R-DEC", "decision", "forestry")   # different scope
        here, there = self.a_views.held_stage_scopes(), self.b_views.held_stage_scopes()
        self.assertEqual(handshake_double_claim(here, there), set())         # no conflict
        self.assertIsNone(refuse_double_claim(here, there))                  # the handshake proceeds

    def test_a_single_holder_passes(self):
        """I8: when only one machine holds a (stage, scope), there is no double-claim — pass."""
        self._handshake()
        _hold_stage(self.a_gate, "gov-a", "R-DEC", "decision", "fisheries")  # only A holds
        here, there = self.a_views.held_stage_scopes(), self.b_views.held_stage_scopes()
        self.assertEqual(there, set())                                       # B holds nothing
        self.assertEqual(handshake_double_claim(here, there), set())
        self.assertIsNone(refuse_double_claim(here, there))

    def test_each_presentation_is_from_its_own_record(self):
        """I8/I1: each machine's presentation is folded from its OWN record — the check compares two
        presentations, never folding two records as one truth (I2). A's view never carries B's
        holdings."""
        self._handshake()
        _hold_stage(self.a_gate, "gov-a", "R-DEC", "decision", "fisheries")
        _hold_stage(self.b_gate, "gov-b", "R-ENF", "enforcement", "forestry")
        self.assertEqual(self.a_views.held_stage_scopes(), {("decision", "fisheries")})   # A's own alone
        self.assertEqual(self.b_views.held_stage_scopes(), {("enforcement", "forestry")}) # B's own alone
        self.assertNotIn(("enforcement", "forestry"), self.a_views.held_stage_scopes())   # never the peer's


# =================================================================================================
# A3 — NO ONE ACTOR HOLDS ALL THREE (I16, rides protection.SOP)
# =================================================================================================

class TestSeparationOfPowers(unittest.TestCase):
    def setUp(self):
        self.d, self.store, self.gate, self.views = _body("p6-a3-", "gov")

    def test_all_three_powers_on_one_actor_for_one_scope_is_refused(self):
        """I16/B8: a declared stage set placing decision, enforcement AND monitoring on ONE actor for
        ONE scope is refused, riding protection.SOP. The planted concentration reds (able-to-fail)."""
        _hold_stage(self.gate, "prince", "R1", "decision", "realm")
        _hold_stage(self.gate, "prince", "R2", "enforcement", "realm")
        _hold_stage(self.gate, "prince", "R3", "monitoring", "realm")
        held = self.views.held_stages()
        self.assertEqual(separation_of_powers_conflicts(held), {("prince", "realm")})   # the concentration, by name
        with self.assertRaises(OpError) as cm:
            refuse_separation_of_powers(held)
        self.assertEqual(cm.exception.rule, SOP)                            # rides the SOP mechanism
        self.assertIn("prince @ realm", str(cm.exception))

    def test_any_two_of_the_three_pass(self):
        """I16: holding any TWO of the three powers is NOT a concentration — the control passes (it
        is able-to-fail: the same shape with the third power refuses)."""
        _hold_stage(self.gate, "prince", "R1", "decision", "realm")
        _hold_stage(self.gate, "prince", "R2", "enforcement", "realm")      # two of three only
        held = self.views.held_stages()
        self.assertEqual(separation_of_powers_conflicts(held), set())       # no concentration
        self.assertIsNone(refuse_separation_of_powers(held))               # passes

    def test_the_three_powers_split_across_actors_pass(self):
        """I16: separation of powers is satisfied when the three powers sit on DIFFERENT actors — no
        single actor concentrates all three, so it passes (structured difference, not concentration)."""
        _hold_stage(self.gate, "judge", "R1", "decision", "realm")
        _hold_stage(self.gate, "sheriff", "R2", "enforcement", "realm")
        _hold_stage(self.gate, "auditor", "R3", "monitoring", "realm")
        held = self.views.held_stages()
        self.assertEqual(separation_of_powers_conflicts(held), set())
        self.assertIsNone(refuse_separation_of_powers(held))

    def test_all_three_across_different_scopes_for_one_actor_pass(self):
        """I16: the concentration that is refused is all three powers over the SAME scope; the same
        actor holding one power each over THREE DIFFERENT scopes is not a same-matter concentration
        and passes (the separation-of-powers unit is per actor per scope)."""
        _hold_stage(self.gate, "prince", "R1", "decision", "fisheries")
        _hold_stage(self.gate, "prince", "R2", "enforcement", "forestry")
        _hold_stage(self.gate, "prince", "R3", "monitoring", "water")
        held = self.views.held_stages()
        self.assertEqual(separation_of_powers_conflicts(held), set())       # no single scope has all three
        self.assertIsNone(refuse_separation_of_powers(held))

    def test_the_three_powers_constant_is_the_named_set(self):
        """I16/B7: the three powers are decision, enforcement and monitoring — named, not invented at
        the call site."""
        self.assertEqual(set(THREE_POWERS), {"decision", "enforcement", "monitoring"})


# =================================================================================================
# A4 — NO FOUNDING (L26, Q2 discharged): no new op/law/check kind, no pack edit, no new field
# =================================================================================================

class TestNoFounding(unittest.TestCase):
    def setUp(self):
        self.d, self.store, self.gate, self.views = _body("p6-a4-", "gov")

    def test_the_founding_pack_carries_no_stage_vocabulary(self):
        """Q2 discharged: the check is real over live rules with NO founding declaration of stages.
        The founding pack carries no `held_stage`/`stage` vocabulary and no stage op — the holding
        rides the EXISTING CREATE-RULE op (reused, not re-authored)."""
        with open(os.path.join(_REPO, "src", "founding", "founding-pack.json"), "rb") as fh:
            raw = fh.read()
        recs = [r for step in json.loads(raw)["steps"] for r in step["records"]]
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertNotIn("HELD-STAGE", op_names)                            # no stage op minted
        self.assertNotIn("HANDSHAKE-STAGE", op_names)
        self.assertNotIn(b"held_stage", raw.lower())                        # no stage vocabulary in the pack
        self.assertNotIn(b"stage", raw.lower())
        self.assertIn("CREATE-RULE", op_names)                             # the op the holding rides IS present

    def test_a_stage_holding_row_adds_no_field(self):
        """I9: a stage is a kind of row, no new row field. A stage-holding rule is an ordinary
        CREATE-RULE record; its top-level field set equals a plain CREATE-RULE record's, the stage
        and scope living inside the EXISTING free payload under existing accepted params."""
        self.gate.execute("CREATE-RULE", "gov", {"rule_id": "PLAIN", "policy_key": "quota", "value": "high"})
        _hold_stage(self.gate, "gov", "STAGED", "decision", "fisheries")
        rows = {r["payload"]["rule_id"]: r for r in self.store.by_action("CREATE-RULE")}
        plain, staged = rows["PLAIN"], rows["STAGED"]
        self.assertEqual(set(plain.keys()), set(staged.keys()))            # identical row shape — no new field
        # the stage-holding rides existing payload keys only (policy_key/value/scope/text are shipped params).
        self.assertLessEqual({"policy_key", "value", "scope", "text"}, set(staged["payload"].keys()))

    def test_no_new_check_kind_and_no_new_attested_member(self):
        """A4: the handshake checks are plain instruments (the census idiom), NOT registered check
        kinds — OP_CHECKS stays 19; and they live in views.py (an existing attested member), NOT a
        new src module — this unit's fence added no src engine module and the rider is inert."""
        from kernel import opdefs, attestation
        self.assertEqual(len(opdefs.OP_CHECKS), 19)                         # no check kind added
        # RE-POINTED (:3934): assert THIS unit's own property — its fence added NO src engine module —
        # NOT the absolute len(ATTESTED_MEMBERS)==N global count (test_ep40/ep46/keymat's property; it
        # churned here on every lawful src add estate-wide, host_seam.py 54->55). The live-stage checks
        # live in the existing views.py (asserted below), not a new module.
        self.assertFalse(any(m.endswith("/live_stages.py") for m in attestation.ATTESTED_MEMBERS),
                         "this unit added a new src engine module — its fence adds none (the checks live in views.py)")
        self.assertTrue(any("views.py" in m for m in attestation.ATTESTED_MEMBERS))


if __name__ == "__main__":
    unittest.main()
