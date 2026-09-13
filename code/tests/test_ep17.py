"""EP-17 — the power view goes live: the campaign's crux (design/31 J3-enf, J4, J5, J6; E2).

Power enforcement goes LIVE at the gate. The founding openness grant makes day one IDENTICAL:
openness is now a visible recorded grant, not an unstated default. Then:

  W1  the gate authority step — covers-or-refuse over the four-dimension grant fold (never a
      stored capability set — RBAC, the refused reference). ROOT-NEG-1 (no chain -> no act) /
      ROOT-NEG-3 (chain reaches the account, not this op) flip deferred->live. Root (owner/SYSTEM)
      and the authority-structure ops (grant/revoke/space/role, governed by attenuation) are exempt.
  W2  scope-on-law (J5): a law whose scope exceeds its author's reach refuses at the author's own
      hop; the untouchables floor retires its blanket HEURISTIC for the real scope+target test —
      proven STRICTLY-STRONGER-OR-EQUAL on the whole campaign-1 untouchables/brick ledger.
  W3  PACK-SCOPE live (J6): a vocabulary write needs reach; pack READS are sight-filtered; the
      audit floor stays constitutional and scope-INDEPENDENT.
  W6  egress (E2): information leaving the system is an ordinary granted act — the four-dimension
      grant already expresses it with ZERO new machinery (the emit-actions vocabulary pack + the
      general covers step).

Every refusal is BOTH directions (nobody-still-acts AND lawful-work-wedges are both failures).
The FIRST NARROWING is the owner's act (W4 checkpoint) — these tests CONSTRUCT narrowed worlds to
prove the columns; the shipped founding narrows nothing. The named wrong reference — RBAC — is
refused by construction: the check is a fold evaluated live, revoke supersedes, nothing is stored.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.protection import Protection, register_protection_ops  # noqa: E402
from kernel.errors import OpError  # noqa: E402

MOTHER = "space:root"


class _Kernel(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def _spaces(self):
        for n, p in [("team", MOTHER), ("team-sub", "space:team"), ("other", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})

    def _narrow(self):
        """A test-constructed narrowed world: spaces exist and the founding openness grant is
        revoked, so the four-dimension distinctions become observable. The owner does this in a
        TEST — the shipped founding narrows nothing (W4 is the owner's act)."""
        self._spaces()
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})

    def _grant(self, gid, grantee, actions, info, space):
        self.gate.execute("GRANT", "owner", {"grant_id": gid, "grantee": grantee,
                          "actions": actions, "info": info, "space": space})


# ---- the documented flips: two deferred laws go live at the founding level ------------------

class TestEnforcementFlips(_Kernel):
    def test_root_neg_3_and_pack_scope_are_live_not_deferred(self):
        # DOCUMENTED FLIP (design/31 §5): ROOT-NEG-3 and PACK-SCOPE flip deferred->live. Recorded in
        # the founding pack; the enforcement is the gate authority step.
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["ROOT-NEG-3"]["enforcement"], "live")
        self.assertEqual(rr["PACK-SCOPE"]["enforcement"], "live")
        # DOCUMENTED FLIP (EP-18): CONST-AUTHORITY-ANCHORED flipped deferred->live (the gate anchor
        # guard: succession fold + handover). DOCUMENTED FLIP (EP-19): CONST-SECRETS flipped
        # deferred->live (the secrets vault — verify, never reveal).
        self.assertEqual(rr["CONST-AUTHORITY-ANCHORED"]["enforcement"], "live")
        self.assertEqual(rr["CONST-SECRETS"]["enforcement"], "live")

    def test_root_neg_1_carries_its_honest_live_marker(self):
        # EP-17 Y4 (the mentor's #3): ROOT-NEG-1 is enforced (require_prior/ceiling since campaign 1,
        # and the gate authority step since W1), so it gains its honest `enforcement: live` marker — a
        # reader must not need code to know what is enforced.
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["ROOT-NEG-1"]["enforcement"], "live")

    def test_founding_version_bumped_once_to_1_4_0_for_the_whole_y_pass(self):
        # the Y-pass bumped the founding to 1.4.0; EP-18 bumped it to 1.5.0 (succession + the anchor);
        # EP-19 bumped it to 1.6.0 (the secrets vault); the EP-19 V5/V6 amendment bumps once more to
        # 1.6.1 (VERIFY-ACCOUNT joins the dual-audit pack). Constitutional evolution is a visible
        # pack diff (J9). Asserted on both the reader and the recorded FOUND-STORE designation.
        # [DOCUMENTED FLIP: 1.4.0 -> 1.5.0 (EP-18) -> 1.6.0 (EP-19) -> 1.6.1 (EP-19 V5/V6)
        #  -> 1.7.0 (EP-23, the crossing enters as recorded law and two ops).]
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and the flip chain above stops here.]
        # ASSERTED: a FROZEN LITERAL "1.17.0", last set 2026-08-05 (EP-28N AMENDMENT 1).
        # SUPERSEDED: EP-28S landed the identity law on 2026-08-08; founding 1.17.0 -> 1.18.0.
        #   Fifth rewrite of this literal. A version literal in a test is a STORED COPY OF A
        #   COMPUTABLE VALUE, so every lawful bump reds a row that was never about the bump.
        # REMAINS TRUE, separated out and STILL ASSERTED: the founding never goes BACKWARDS
        #   past the version this row recorded (a floor cannot go stale and still reds on a
        #   regression), and THE READER AND THE RECORD AGREE — the pack on disk versus the
        #   designation the installer stamped into FOUND-STORE, two different takings of one
        #   fact. (`load_pack()["founding_version"]` is NOT the second reader: it IS what
        #   `founding_version()` returns, so that pairing is one reading wearing two labels.)
        # GIVEN UP: this row no longer notices a bump — never its job; EP-28N2 holds that
        #   against a PINNED before-side.
        from founding.install import founding_version
        v = founding_version()
        self.assertGreaterEqual(tuple(int(n) for n in v.split(".")), (1, 17, 0))
        fs = [e for e in self.store.by_action("FOUND-STORE")][0]
        self.assertEqual((fs.get("payload") or {}).get("founding_version"), v)

    def test_the_emit_vocabulary_is_a_founding_pack(self):
        # W6: the emit-class action is VOCABULARY (a category pack: records, never enums or code)
        self.assertIn("EMIT", self.views.category_packs()["emit-actions"]["levels"])

    def test_the_founding_still_carries_the_openness_grant(self):
        # the transition policy's ground: openness is a visible recorded grant anyone can read
        g = self.views.grants()["grant:founding-openness"]
        self.assertEqual((g["grantee"], g["actions"], g["info"], g["space"]), ("*", "*", "*", MOTHER))


# ---- W1: THE AUTHORITY STEP — day-one-identical, then the four-column matrix seed ------------

class TestDayOneIdentical(_Kernel):
    """The flip changes WHERE openness lives, not what works. Under the founding openness grant,
    EVERY caller — a verified account, an unverified bare name, nobody — still acts, no refusal."""

    def test_a_bare_name_still_acts_under_openness(self):
        before = len(self.store.by_action("op-refused"))
        rec = self.gate.execute("CREATE-INFO", "legacy-bob", {"content": "still works"})
        self.assertEqual(rec["action"], "CREATE-INFO")
        self.assertEqual(len(self.store.by_action("op-refused")), before)   # no authority refusal

    def test_owner_and_system_act_freely(self):
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "l", "policy_key": "k", "value": 1})
        self.assertEqual(self.views.policy_value("k"), 1)
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme"})

    def test_covers_answers_open_for_everyone_under_the_grant(self):
        self.assertTrue(self.views.covers("nobody", "CREATE-RULE", "law", MOTHER))


class TestFourColumnMatrix(_Kernel):
    """The four-column matrix SEED (design/31 §6; EP-20 runs the full ledger). Built on CREATE-RULE
    so info-kind is well-defined ('law') and the binding space is controllable (the X2 passthrough).
    Both directions on every column: a covered act PASSES (lawful work is not wedged) and each
    uncovered mode REFUSES with the right citation (nobody-still-acts is closed)."""

    def setUp(self):
        super().setUp()
        self._narrow()
        self._grant("la", "alice", ["CREATE-RULE"], ["law"], "space:team")

    def test_covered_passes(self):
        rec = self.gate.execute("CREATE-RULE", "alice",
                                {"rule_id": "cov", "policy_key": "c1", "value": 1, "space": "space:team"})
        self.assertEqual(rec["action"], "CREATE-RULE")

    def test_no_grant_stops_at_authority_root_neg_1(self):
        # bob holds NO grant at all -> no authorising chain -> ROOT-NEG-1
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "bob",
                              {"rule_id": "ng", "policy_key": "c2", "value": 1, "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")

    def test_no_account_stops_at_authority_root_neg_1(self):
        # a bare name with no grant surfaces here as 'no chain' (identity refusal is EP-20's column)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "nobody",
                              {"rule_id": "na", "policy_key": "c3", "value": 1, "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")

    def test_wrong_space_stops_at_scope_root_neg_3(self):
        # alice HOLDS a grant (the chain reaches her) but it is in space:team, not space:other ->
        # not authorised for THIS operation-in-this-space -> ROOT-NEG-3
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice",
                              {"rule_id": "ws", "policy_key": "c4", "value": 1, "space": "space:other"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")

    def test_wrong_action_and_info_also_refuse(self):
        # the info dimension gates too: alice's grant is CREATE-RULE x law; an AMEND-PACK act (a
        # different action, category_pack info) is uncovered -> refuses (she holds a chain -> ROOT-NEG-3)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-PACK", "alice", {"name": "actor-classes", "levels": ["x"]})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")

    def test_the_refusal_is_recorded_and_the_system_is_not_wedged(self):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-RULE", "bob", {"rule_id": "z", "policy_key": "zz", "value": 1, "space": "space:team"})
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)   # recorded
        # a covered actor right after still works — no wedge
        self.gate.execute("CREATE-RULE", "alice", {"rule_id": "ok", "policy_key": "ok", "value": 1, "space": "space:team"})


class TestRevokeIsInstantNoStoredDeny(_Kernel):
    def test_revoke_flips_the_gate_answer_with_no_cleanup(self):
        # the anti-RBAC property, end to end: revoke supersedes, nothing cascades, the NEXT gate check
        # simply answers differently (no stored capability set to purge)
        self._narrow()
        self._grant("la", "alice", ["CREATE-RULE"], ["law"], "space:team")
        self.gate.execute("CREATE-RULE", "alice", {"rule_id": "a", "policy_key": "k", "value": 1, "space": "space:team"})
        before = len(self.store.all())
        self.gate.execute("REVOKE", "owner", {"grant_id": "la"})
        self.assertEqual(len(self.store.all()), before + 1)    # ONLY the revoke — nothing cascaded
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice", {"rule_id": "b", "policy_key": "k2", "value": 1, "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")      # the chain is gone at the next check


# ---- W2: scope-on-law (J5) ------------------------------------------------------------------

class TestScopeOnLaw(_Kernel):
    def setUp(self):
        super().setUp()
        self._narrow()
        self._grant("la", "alice", ["CREATE-RULE"], ["law"], "space:team")

    def test_a_law_within_the_authors_reach_mints(self):
        rec = self.gate.execute("CREATE-RULE", "alice",
                                {"rule_id": "teamlaw", "policy_key": "t", "value": 1, "space": "space:team"})
        self.assertIn("teamlaw", self.views.active_rules())
        self.assertEqual(rec["payload"]["space"], "space:team")

    def test_a_law_scoped_beyond_the_authors_reach_refuses_at_the_authors_hop(self):
        # J5: minting a law whose declared scope (space:other) exceeds alice's reach (space:team)
        # refuses at her own hop — no rule-specific machinery, the same covers step
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-RULE", "alice",
                              {"rule_id": "otherlaw", "policy_key": "o", "value": 1, "space": "space:other"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("otherlaw", self.views.active_rules())

    def test_a_child_space_is_within_reach_containment(self):
        # reach over team covers team-sub (containment) — a law scoped to the child mints
        self.gate.execute("CREATE-RULE", "alice",
                          {"rule_id": "sublaw", "policy_key": "s", "value": 1, "space": "space:team-sub"})
        self.assertIn("sublaw", self.views.active_rules())


class TestUntouchablesStrictlyStronger(_Kernel):
    """W2 + EP-17 Y-PASS: the untouchables floor retires its blanket HEURISTIC for the real
    scope+target test — behind a strictly-stronger proof (design/31 J5). The W4 build proved it only
    on the campaign-1 ledger, which is SYSTEM-SCOPED (it predates scope fields), so it could not
    contain cases in the new dimension — and on subspace-scoped blanket bans the replacement was
    strictly WEAKER (the brick returned through the scope door). The Y-pass RE-RUNS the proof on an
    EXTENDED ledger that exercises the new dimension (subspace-scoped blanket bans + the parent-lift);
    the retirement stays licensed only if the extended ledger passes. The campaign-1 ledger is verbatim
    from test_ep07b TestB1UntouchablesFloor + test_ep13b TestW1RuleTriggerScope."""

    LEDGER_REFUSED = [                                          # blanket over rule-processing, the heuristic refused each
        [{"action": "CREATE-RULE"}],                           # test_ep07b: brick on CREATE-RULE
        [{"action": "AMEND-OP"}],                              # test_ep07b: brick on AMEND-OP (owner too)
        [{}],                                                  # test_ep07b: matches-everything
        [{"action": "CREATE-RULE", "zzz": None}],              # test_ep13b: absent-field disguise
        [{"action": "CREATE-RULE", "rule_cited": "ROOT-NEG-6"}],  # test_ep13b: always-true-field disguise
    ]
    LEDGER_PASSED = [                                           # targeted / non-lifecycle, the heuristic passed each
        [{"action": "CREATE-RULE", "actor": "alice"}],         # targeted WHO
        [{"action": "FROB"}],                                  # non-lifecycle blanket
        [{"action": "FROB", "actor": "bob"}],                  # non-lifecycle + targeted
        [{"action": "CREATE-RULE", "object": "some-rule"}],    # targeted WHERE
    ]
    LEDGER_NEW_DIMENSION = [                                    # subspace-scoped blanket bans (the new dimension)
        [{"action": "CREATE-RULE"}],                           # a blanket rule-writing ban, scoped to a subspace
        [{"action": "AMEND-OP"}],                              # the heuristic over-refused these at MINT
    ]

    def _new_decision(self, when, space=None):
        """The NEW branch-g decision (target AND scope), computed exactly as branch g computes it."""
        payload = {"polarity": "-", "when": when}
        if space is not None:
            payload["space"] = space
        draft = {"action": "CREATE-RULE", "payload": payload}
        return (self.gate._is_blanket_rule_block(when)
                and self.gate._act_space(draft, payload) == self.views.mother_space())

    def test_ledger_proof_scope_target_refuses_everything_the_heuristic_did(self):
        # THE STRICTLY-STRONGER PROOF, run BEFORE relying on the retirement. Every ledger case is
        # SYSTEM-SCOPED (no explicit space -> the mother space), so the scope prong is always true and
        # the new scope+target decision EQUALS the heuristic's on the whole ledger: every refusal the
        # heuristic made, the scope test also makes. No window weaker than what it replaced.
        for when in self.LEDGER_REFUSED:
            self.assertTrue(self.gate._is_blanket_rule_block(when), f"ledger: heuristic refuses {when}")
            self.assertTrue(self._new_decision(when), f"scope+target must ALSO refuse {when}")
        for when in self.LEDGER_PASSED:
            self.assertFalse(self.gate._is_blanket_rule_block(when), f"ledger: heuristic passes {when}")
            self.assertFalse(self._new_decision(when), f"scope+target must ALSO pass {when} (no new refusal)")

    def _new_dimension_probe(self):
        """Execute the NEW dimension end to end: a subspace-scoped blanket ban MINTS (the lawful local
        allowance the heuristic over-refused), yet scope-aware enforcement (Y1) means it can NEVER
        brick the mother's rule-processing surface and is ALWAYS liftable from its parent (no orphan).
        Returns (mints_ok, no_system_brick_ok, parent_lift_ok)."""
        self._team_ban()
        mints_ok = "team-ban" in self.views.active_rules()
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "sys-rule", "policy_key": "s", "value": 1})
        no_system_brick_ok = "sys-rule" in self.views.active_rules()          # mother surface untouched
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "team-ban", "policy_key": "lifted", "value": 1})
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "resumed", "policy_key": "r", "value": 1, "space": "space:team"})
        parent_lift_ok = "resumed" in self.views.active_rules()               # liftable from the parent
        return mints_ok, no_system_brick_ok, parent_lift_ok

    def test_extended_ledger_reproof_and_verdict_line(self):
        # THE STRICTLY-STRONGER PROOF, RE-RUN on the EXTENDED ledger (EP-17 Y-pass). SYSTEM SCOPE:
        # scope+target still EQUALS the heuristic on the campaign-1 ledger (unchanged, still valid).
        sys_refused_ok = all(self._new_decision(w) for w in self.LEDGER_REFUSED)
        sys_passed_ok = all(not self._new_decision(w) for w in self.LEDGER_PASSED)
        # NEW DIMENSION (subspace-scoped blanket bans): the heuristic OVER-refused these at MINT; the
        # scope+target test now MINTS them (restoring lawful local governance) AND scope-aware
        # enforcement contains them — so the PROTECTED INVARIANT the heuristic protected (the system-
        # level rule-processing surface is never bricked; no local ban orphans) is preserved.
        overrefused_by_heuristic = all(self.gate._is_blanket_rule_block(w) for w in self.LEDGER_NEW_DIMENSION)
        mints_now = all(not self._new_decision(w, space="space:team") for w in self.LEDGER_NEW_DIMENSION)
        mints_ok, no_system_brick_ok, parent_lift_ok = self._new_dimension_probe()
        print(f"\n[EP-17 Y-PASS EXTENDED-LEDGER RE-PROOF] extended ledger = "
              f"{len(self.LEDGER_REFUSED)} system-scoped refused + {len(self.LEDGER_PASSED)} passed "
              f"(campaign-1) + {len(self.LEDGER_NEW_DIMENSION)} new-dimension subspace-scoped blanket "
              f"bans + the parent-lift; SYSTEM SCOPE: scope+target preserves EVERY heuristic refusal "
              f"({sys_refused_ok}) and adds NO refusal ({sys_passed_ok}); NEW DIMENSION: the heuristic "
              f"over-refused these at mint ({overrefused_by_heuristic}), scope+target now MINTS them "
              f"({mints_now}) yet scope-aware enforcement NEVER bricks the mother's rule-processing "
              f"surface ({no_system_brick_ok}) and every subspace ban is liftable from its parent "
              f"({parent_lift_ok}) — the protected invariant preserved (equal-or-stronger) while the "
              f"heuristic's over-refusal of lawful local governance is CORRECTED; strictly-stronger-or-"
              f"equal on the EXTENDED ledger PROVEN — retirement stays licensed (an old ledger cannot "
              f"contain cases in a dimension it could not express).")
        self.assertTrue(all((sys_refused_ok, sys_passed_ok, overrefused_by_heuristic, mints_now,
                             mints_ok, no_system_brick_ok, parent_lift_ok)))

    def test_end_to_end_system_brick_refuses_for_everyone_including_owner(self):
        # both directions, nobody-still-bricks: the brick class refuses for the owner too (self-bricking
        # is exit, not surgery). System-scoped (no explicit space).
        for actor in ("alice", "owner"):
            with self.assertRaises(OpError) as cm:
                self.gate.execute("CREATE-RULE", actor,
                                  {"rule_id": f"brick-{actor}", "polarity": "-",
                                   "when": [{"action": "CREATE-RULE"}], "then": [{"refuse": "b"}]})
            self.assertEqual(cm.exception.rule, "BOOT-INT", actor)
        # rule-making is NOT bricked — the mints never took effect
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "ok", "policy_key": "k", "value": 1})
        self.assertEqual(self.views.policy_value("k"), 1)

    def _team_ban(self):
        """A blanket rule-writing ban scoped to space:team (a space-holder's local governance)."""
        for n, par in [("team", MOTHER), ("team-sub", "space:team"), ("other", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": par})
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "team-ban", "polarity": "-", "when": [{"action": "CREATE-RULE"}],
                           "then": [{"refuse": "TEAM-RULE-BAN"}], "space": "space:team"})

    def test_Y1_subspace_local_ban_mints_and_binds_only_its_subtree(self):
        # EP-17 Y-PASS, Y1 (flipped from the Y0 err-closed form once containment ENFORCEMENT landed).
        # design/30 §3, made fully mechanical: a blanket rule-writing ban scoped to a SUBSPACE is a
        # space-holder's LOCAL governance — it MINTS, and (the Y1 fix) `_full_form_pass` fires it ONLY
        # on acts within the ban's DECLARED SCOPE's subtree (containment, J2). So it binds its subtree
        # and NEVER the mother space: the system's capacity to work with rules AT SYSTEM LEVEL is
        # untouched — the brick can no longer return through the scope door.
        self._team_ban()
        self.assertIn("team-ban", self.views.active_rules())               # minted (not over-refused)
        # binds its OWN subtree: a rule-write inside team, and inside its descendant team-sub, refuses
        for space in ("space:team", "space:team-sub"):
            with self.assertRaises(OpError) as cm:
                self.gate.execute("CREATE-RULE", "owner",
                                  {"rule_id": f"x{space}", "policy_key": "k", "value": 1, "space": space})
            self.assertEqual(cm.exception.rule, "TEAM-RULE-BAN", space)     # the LOCAL ban fired
        # NEVER the mother, NEVER a sibling: system-level and sibling rule-writing still work
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "at-mother", "policy_key": "m", "value": 1})
        self.assertIn("at-mother", self.views.active_rules())              # system surface preserved
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "at-other", "policy_key": "o", "value": 1, "space": "space:other"})
        self.assertIn("at-other", self.views.active_rules())              # sibling unaffected

    def test_Y1_parent_scope_lift_never_orphans(self):
        # Y1's no-orphan guarantee: a subspace ban is ALWAYS liftable from above. A superseding rule
        # written from the PARENT's reach (owner at the mother scope) is NEVER blocked by the subspace
        # ban — containment means the ban does not fire on a parent-scope act — so it lifts the ban and
        # rule-writing inside the subtree resumes. No local brick can orphan its own subtree.
        self._team_ban()
        with self.assertRaises(OpError):                                   # blocked before the lift
            self.gate.execute("CREATE-RULE", "owner",
                              {"rule_id": "pre", "policy_key": "k", "value": 1, "space": "space:team"})
        # the parent lift: a superseding team-ban from the mother scope is NOT blocked and takes effect
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "team-ban", "policy_key": "team_ban_lifted", "value": "lifted"})
        self.assertIsNone(self.views.active_rules()["team-ban"].get("when"))  # superseded: no teeth
        # rule-writing inside team resumes — the ban was liftable from the parent, never an orphan
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "post", "policy_key": "k2", "value": 2, "space": "space:team"})
        self.assertIn("post", self.views.active_rules())


# ---- W3: PACK-SCOPE live (J6) ---------------------------------------------------------------

class TestPackScopeLive(_Kernel):
    def test_a_vocabulary_write_needs_reach(self):
        self._narrow()
        # uncovered: alice holds no grant -> no chain -> ROOT-NEG-1
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-PACK", "alice", {"name": "actor-classes", "levels": ["x"]})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")
        # covered: a grant over category_pack info in the mother space lets the write through
        self._grant("pk", "alice", ["AMEND-PACK"], ["category_pack"], MOTHER)
        self.gate.execute("AMEND-PACK", "alice", {"name": "actor-classes", "levels": ["x"]})
        self.assertEqual(list(self.views.category_packs()["actor-classes"]["levels"]), ["x"])

    def test_the_audit_floor_stays_constitutional_and_scope_independent(self):
        # no reach lowers the floor: even an actor COVERED for AMEND-PACK cannot drop a floor action —
        # the constitutional audit-floor branch fires regardless of the grant (CONST-RECORDING-TOTAL)
        self._narrow()
        self._grant("pk", "alice", ["AMEND-PACK"], ["category_pack"], MOTHER)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-PACK", "alice", {"name": "dual-audit-actions", "levels": ["MOUNT"]})
        self.assertEqual(cm.exception.rule, "CONST-RECORDING-TOTAL")

    def test_pack_reads_are_sight_filtered_default_deny(self):
        # J6: reading a vocabulary is a sight question. owner/SYSTEM see all; an ungranted account
        # sees NONE (default-deny — P6 extended from action to knowledge)
        all_packs = self.views.category_packs()
        self.assertEqual(self.views.visible_category_packs("owner"), all_packs)
        self.assertEqual(self.views.visible_category_packs("SYSTEM"), all_packs)
        self.assertEqual(self.views.visible_category_packs("alice"), {})       # sees nothing yet

    def test_a_grant_read_opens_one_pack_to_its_holder(self):
        prot = Protection(self.store, self.gate, self.views)
        register_protection_ops(self.gate, self.store, prot)
        self.gate.execute("GRANT-READ", "owner", {"grantee": "alice", "target": "pack:actor-classes"})
        self.assertEqual(list(self.views.visible_category_packs("alice")), ["actor-classes"])
        self.assertNotIn("law-lifecycle-actions", self.views.visible_category_packs("alice"))  # still hidden


# ---- W6: egress under the grant model (E2) --------------------------------------------------

class TestEgressUnderGrant(_Kernel):
    """E2 (owner-ruled): information leaving the system is an ordinary granted act. The proof is that
    the four-dimension grant ALREADY expresses it — the emit-class action is vocabulary (the founding
    emit-actions pack), and the gate's covers-or-refuse step (W1) applies to it like any act. ZERO new
    machinery: no emit-specific gate branch, no egress subsystem — a trivial emit op stands in for any
    egress op (COMMS-SEND in production); the enforcement is the SAME general covers step."""

    def _register_emit(self):
        # a trivial emit-class op: its recorded action is the emit vocabulary token (a stand-in for
        # any real egress op). No new machinery — just an op whose action is emit-class. Its record
        # carries no explicit space -> the mother space (so the founding openness grant reaches it
        # day one, and a narrowed grant over the mother space covers it).
        self.gate.register("EMIT", {"description": "emit to a human channel", "rules": ["ROOT-NEG-5"],
                                    "params": {}},
                           lambda actor, params: {"actor": actor, "action": "EMIT", "object": "out",
                                                  "rule_cited": "ROOT-NEG-5", "payload": {"kind": "message"}})

    def test_emit_without_covering_grant_refuses(self):
        # an emit act with no covering grant refuses at the gate, cited + recorded, EXACTLY like any
        # other uncovered act — no emit-specific path
        self._narrow()
        self._register_emit()
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("EMIT", "alice", {})
        self.assertIn(cm.exception.rule, ("ROOT-NEG-1", "ROOT-NEG-3"))   # the general authority refusal
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)   # recorded like any refusal
        self.assertEqual(self.store.by_action("EMIT"), [])              # the emit never left

    def test_emit_with_covering_grant_passes(self):
        # the too-wedged direction: a COVERED emit acts normally — emission is an ordinary granted act
        self._narrow()
        self._register_emit()
        self._grant("em", "alice", ["EMIT"], ["message"], MOTHER)
        rec = self.gate.execute("EMIT", "alice", {})
        self.assertEqual(rec["action"], "EMIT")

    def test_emit_is_covered_by_the_founding_openness_grant_day_one(self):
        # under the founding openness grant (no narrowing), an emit acts exactly as everything else —
        # narrowing emission is then ordinary governance (the owner's W4-checkpoint act, never here)
        self._register_emit()
        rec = self.gate.execute("EMIT", "alice", {})
        self.assertEqual(rec["action"], "EMIT")

    def test_no_emit_specific_machinery_was_added(self):
        # the grant model expresses egress with ZERO new machinery: emit is vocabulary + the general
        # covers step. The gate exposes no emit-specific method; the emit action is just an action.
        for attr in dir(self.gate):
            self.assertNotIn("emit", attr.lower(), f"gate grew an emit-specific surface: {attr}")


# ---- the authority-structure exemption (a covers step that is not circular) -----------------

class TestAuthorityRegimeIsData(_Kernel):
    """EP-17 Y2 (the mentor's #1a): which authority regime governs an op is jurisdictional LAW, read
    from the op's OWN definition record (`authority_regime`), not a code constant. The four
    power-structure ops declare `attenuation-family`; the gate reads the regime from data; the code
    constant AUTHORITY_STRUCTURE_ACTIONS is RETIRED (data over code; a cold reader of the pack sees
    which law governs the op)."""

    def test_the_four_power_structure_ops_declare_attenuation_family_in_the_pack(self):
        od = self.views.op_definitions()
        for op in ("GRANT", "REVOKE", "CREATE-SPACE", "CREATE-ROLE"):
            self.assertEqual(od[op]["definition"].get("authority_regime"), "attenuation-family", op)

    def test_an_ordinary_op_reads_as_covers_by_default(self):
        # a covers-governed op carries no attenuation-family marker — the gate defaults it to "covers"
        od = self.views.op_definitions()
        self.assertNotEqual(od["CREATE-RULE"]["definition"].get("authority_regime"), "attenuation-family")

    def test_the_code_constant_is_retired(self):
        # data over code: the enumerating constant no longer governs the exemption
        import kernel.gate as gate_mod
        self.assertFalse(hasattr(gate_mod, "AUTHORITY_STRUCTURE_ACTIONS"),
                         "AUTHORITY_STRUCTURE_ACTIONS must retire — the regime is data on the op record")

    def test_grant_is_still_exempt_from_covers_via_the_data_regime(self):
        # the exemption still holds, now sourced from data: a holder of nothing cannot GRANT, but the
        # refusal is attenuation (in the handler), NOT the covers step gating a grant-to-make-a-grant
        self._narrow()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "nobody", {"grant_id": "x", "grantee": "bob",
                              "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")


class TestAuthorityStructureExemption(_Kernel):
    """The authority-structure ops (grant/revoke/space/role) WRITE the power structure, so the general
    covers step (W1) does not re-gate them with a covering grant — that would be circular (a grant to
    make a grant) and would wedge lawful delegation. Their authority model is attenuation (a grant
    never wider than its maker, design/31 E1). Both directions, preserving EP-16's model."""

    def test_delegation_within_reach_still_mints_not_wedged(self):
        # the lawful-work-not-wedged direction: alice, holding one grant, delegates a subset -> mints
        self._narrow()
        self._grant("a1", "alice", ["CREATE-INFO"], ["note"], "space:team")
        self.gate.execute("GRANT", "alice", {"grant_id": "sub", "grantee": "bob",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team-sub"})
        self.assertIn("grant:sub", self.views.grants())

    def test_delegation_beyond_reach_still_refuses_via_attenuation(self):
        # the nobody-still-acts direction: a widening delegation refuses at attenuation (ROOT-NEG-3),
        # NOT because the authority step gated it (the exemption did not open a hole)
        self._narrow()
        self._grant("a1", "alice", ["CREATE-INFO"], ["note"], "space:team")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "alice", {"grant_id": "wide", "grantee": "bob",
                              "actions": ["CREATE-RULE"], "info": ["note"], "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")

    def test_a_holder_of_nothing_cannot_grant(self):
        # the exemption is not a bypass: attenuation refuses a maker who holds nothing (no covering
        # grant to contain the delegation), so a nobody cannot mint a grant
        self._narrow()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "nobody", {"grant_id": "x", "grantee": "bob",
                              "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")


# ---- Y3: the attenuation family completes (every power arrives with its leash) --------------

class TestAttenuationFamilyComplete(_Kernel):
    """EP-17 Y3 (the mentor's #1/#6): the power-structure ops are all attenuation-family, but the W4
    build leashed only GRANT — REVOKE/CREATE-SPACE/CREATE-ROLE carried no bar, so in a narrowed world
    a non-root actor could revoke any grant or plant spaces/roles anywhere. Y3 completes the family:
    REVOKE only within the revoker's reach over the revoked grant's cover (take away only what you
    could give); CREATE-SPACE requires reach over the parent; CREATE-ROLE requires reach over its
    space (containment, J2). ALL INERT under the founding openness grant; a narrowed world observes
    BOTH directions."""

    # ---- all inert under openness (a fresh founding refuses none of these) ------------------
    def test_all_three_are_inert_under_openness(self):
        # under the openness grant (reach = the whole tree) a non-root actor freely extends structure
        self.gate.execute("CREATE-SPACE", "alice", {"name": "as", "parent": MOTHER})
        self.gate.execute("CREATE-ROLE", "alice", {"name": "ar", "space": MOTHER})
        self.gate.execute("GRANT", "owner", {"grant_id": "g0", "grantee": "bob",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": MOTHER})
        self.gate.execute("REVOKE", "alice", {"grant_id": "g0"})          # openness contains it -> passes
        self.assertNotIn("grant:g0", self.views.grants())

    # ---- REVOKE: take away only what you could give -----------------------------------------
    def test_revoke_within_reach_passes(self):
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")   # alice's reach
        self._grant("gt", "bob", ["CREATE-INFO"], ["note"], "space:team")      # cover within alice's reach
        self.gate.execute("REVOKE", "alice", {"grant_id": "gt"})
        self.assertNotIn("grant:gt", self.views.grants())

    def test_revoke_beyond_reach_refuses(self):
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")   # alice holds CREATE-INFO only
        self._grant("gw", "bob", ["CREATE-RULE"], ["note"], "space:team")      # cover exceeds alice's reach
        with self.assertRaises(OpError) as cm:
            self.gate.execute("REVOKE", "alice", {"grant_id": "gw"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertIn("grant:gw", self.views.grants())                        # not revoked

    # ---- CREATE-SPACE: STRUCTURE-CLASS reach over the parent (EP-18 R-B) ---------------------
    def test_create_space_within_parent_reach_passes(self):
        # DOCUMENTED FLIP (EP-18 R-B): founding a space now needs a STRUCTURE-CLASS action over the
        # parent, not merely any covering grant — sight is not authority. The covering grant carries
        # CREATE-SPACE (structure-class), so the mint passes. (Before R-B a bare CREATE-INFO grant
        # sufficed; that over-broad allowance is corrected — see test_ep18 for the read-grant refusal.)
        self._narrow()
        self._grant("la", "alice", ["CREATE-SPACE"], ["note"], "space:team")
        self.gate.execute("CREATE-SPACE", "alice", {"name": "team-child", "parent": "space:team"})
        self.assertIn("space:team-child", self.views.spaces())

    def test_create_space_beyond_parent_reach_refuses(self):
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-SPACE", "alice", {"name": "other-child", "parent": "space:other"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("space:other-child", self.views.spaces())

    # ---- CREATE-ROLE: STRUCTURE-CLASS reach over its space (EP-18 R-B) -----------------------
    def test_create_role_within_space_reach_passes(self):
        # DOCUMENTED FLIP (EP-18 R-B): founding a role now needs a STRUCTURE-CLASS action over its
        # space (CREATE-ROLE), not merely any covering grant — sight is not authority.
        self._narrow()
        self._grant("la", "alice", ["CREATE-ROLE"], ["note"], "space:team")
        self.gate.execute("CREATE-ROLE", "alice", {"name": "team-lead", "space": "space:team"})
        self.assertIn("role:team-lead", self.views.roles())

    def test_create_role_beyond_space_reach_refuses(self):
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-ROLE", "alice", {"name": "other-lead", "space": "space:other"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("role:other-lead", self.views.roles())


# ---- round-trip: the enforcement world replays identically -----------------------------------

class TestRoundTripWithGrants(_Kernel):
    def test_narrowing_survives_the_round_trip(self):
        # kill everything derived, rebuild from the record file alone — the narrowed authority world
        # (and its gate answers) reconstructs identically
        self._narrow()
        self._grant("la", "alice", ["CREATE-RULE"], ["law"], "space:team")
        self.gate.execute("CREATE-RULE", "alice", {"rule_id": "r", "policy_key": "k", "value": 1, "space": "space:team"})
        before = (self.views.grants(), self.views.spaces())
        _s2, gate2, views2 = build_kernel(self.path)
        self.assertEqual(views2.grants(), before[0])
        self.assertEqual(views2.spaces(), before[1])
        # the gate answers the same after replay: bob is still refused, alice still covered
        with self.assertRaises(OpError):
            gate2.execute("CREATE-RULE", "bob", {"rule_id": "r2", "policy_key": "k2", "value": 1, "space": "space:team"})
        gate2.execute("CREATE-RULE", "alice", {"rule_id": "r3", "policy_key": "k3", "value": 1, "space": "space:team"})


if __name__ == "__main__":
    unittest.main()
