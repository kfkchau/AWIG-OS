"""EP-18 — Succession + the anchor: authority never orphans (design/31 J7).

CONST-AUTHORITY-ANCHORED flips deferred -> live at the gate anchor guard. The work:

  N1  succession records + ops (DESIGNATE-SUCCESSOR / ACCEPT-SUCCESSION / REVOKE-SUCCESSION),
      owner-tier definition-born; the CURRENT successor is a FOLD (latest valid designation-
      acceptance pair, verified + human re-checked LIVE at read), never a stored pointer.
  N2  the anchor refusals at the gate: self-removal (HANDOVER) refuses without a valid successor;
      an unverified or pure-agentic successor refuses at designation; only the root may designate/
      revoke/hand over. With a valid successor the HANDOVER PROCEEDS as a recorded handover.
  N3  cycle/orphan refusal at grant/role mint: a grant or role naming a space whose chain does not
      terminate at the root refuses at creation (for every actor).
  N4  both directions + round-trip: the new chain-end governs and the old record stands; replay.

RIDERS (law, distinct work items):
  R-A GRANT's attenuation leash MOVED from its handler to the gate chokepoint — a grant-kind record
      arriving via ANY op is leashed; a lawful contained GRANT still mints. The `covers` default
      authority regime is now pack DATA (authority-regime-default policy).
  R-B founding a space/role needs a STRUCTURE-CLASS action over the target space, not mere sight —
      a read-only grant does not authorise it. Inert under openness; a narrowed world, both directions.

THE WRONG REFERENCE REFUSED: ownership-transfer-as-a-field-update. There is no owner FIELD — the
chain-end is DERIVED from the founding plus the succession fold; the handover writes records; every
view recomputes. The world stays OPEN (W4): the shipped founding narrows nothing; these tests
CONSTRUCT narrowed worlds only to observe the riders' columns.

Every probe here lands as a regression test (R14).
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402

MOTHER = "space:root"


def _h(s):
    return hashlib.sha256(s.encode()).hexdigest()


class _Kernel(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def _account(self, acct, actor_class="human", verify=True):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": acct, "actor_class": actor_class})
        if verify:
            self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": acct, "evidence_hash": _h(acct)})

    def _ready_successor(self, acct="alice"):
        """A verified human, designated and accepted — a valid successor fold exists."""
        self._account(acct, "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": acct})
        self.gate.execute("ACCEPT-SUCCESSION", acct, {})
        return acct

    def _narrow(self):
        """A test-constructed narrowed world (the owner's act in a TEST — the shipped founding narrows
        nothing): spaces exist, the founding openness grant revoked, so the grant dimensions bite."""
        for n, p in [("team", MOTHER), ("team-sub", "space:team"), ("other", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})

    def _grant(self, gid, grantee, actions, info, space):
        self.gate.execute("GRANT", "owner", {"grant_id": gid, "grantee": grantee,
                          "actions": actions, "info": info, "space": space})


# ---- the documented flip: CONST-AUTHORITY-ANCHORED deferred -> live --------------------------

class TestEnforcementFlip(_Kernel):
    def test_const_authority_anchored_is_live_not_deferred(self):
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["CONST-AUTHORITY-ANCHORED"]["enforcement"], "live")   # deferred -> live

    def test_enforced_by_names_this_machinery(self):
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        eb = rr["CONST-AUTHORITY-ANCHORED"]["enforced_by"]
        self.assertIn("anchor guard", eb)
        self.assertIn("succession", eb)

    def test_the_toothless_view_still_excludes_it(self):
        # a live law with a non-empty `then` (refuse) has teeth — it is not toothless, and the
        # deferred-exemption it used to enjoy is gone (the EP-07B B5 flip pattern).
        self.assertNotIn("CONST-AUTHORITY-ANCHORED", self.views.toothless_musts())

    def test_founding_version_bumped_to_1_5_0(self):
        # EP-18 bumped to 1.5.0; EP-19 bumped to 1.6.0 (the secrets vault); the EP-19 V5/V6 amendment
        # bumps once more to 1.6.1 (VERIFY-ACCOUNT joins the dual-audit pack); EP-23 bumps to 1.7.0
        # (the crossing). [DOCUMENTED FLIP.]
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
        fs = self.store.by_action("FOUND-STORE")[0]
        self.assertEqual((fs.get("payload") or {}).get("founding_version"), v)


# ---- N1: succession is a recorded ceremony; the current successor is a FOLD ------------------

class TestSuccessionFold(_Kernel):
    def test_ops_are_owner_tier_definition_born(self):
        od = self.views.op_definitions()
        for op in ("DESIGNATE-SUCCESSOR", "ACCEPT-SUCCESSION", "REVOKE-SUCCESSION", "HANDOVER"):
            self.assertIn(op, od, op)
            self.assertEqual(od[op]["tier"], "owner", op)

    def test_bare_retire_of_a_succession_op_refuses_conservation(self):
        # owner-tier -> bare removal refuses (conservation branch d), the owner included
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RETIRE-OP", "owner", {"name": "HANDOVER"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_no_successor_until_designated_and_accepted(self):
        self.assertIsNone(self.views.current_successor())
        self._account("alice", "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "alice"})
        self.assertIsNone(self.views.current_successor())          # designated, not yet accepted
        self.gate.execute("ACCEPT-SUCCESSION", "alice", {})
        self.assertEqual(self.views.current_successor(), "alice")  # the pair completes the fold

    def test_the_successor_is_a_fold_not_a_pointer(self):
        # revoke, then re-designate/accept a DIFFERENT successor — the fold answers latest, nothing stored
        self._account("alice", "human")
        self._account("bob", "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "alice"})
        self.gate.execute("ACCEPT-SUCCESSION", "alice", {})
        self.gate.execute("REVOKE-SUCCESSION", "owner", {})
        self.assertIsNone(self.views.current_successor())          # revocation supersedes
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "bob"})
        self.gate.execute("ACCEPT-SUCCESSION", "bob", {})
        self.assertEqual(self.views.current_successor(), "bob")

    def test_a_new_designation_resets_a_prior_acceptance(self):
        self._account("alice", "human")
        self._account("bob", "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "alice"})
        self.gate.execute("ACCEPT-SUCCESSION", "alice", {})
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "bob"})   # supersedes alice
        self.assertIsNone(self.views.current_successor())          # bob has not accepted yet
        self.gate.execute("ACCEPT-SUCCESSION", "bob", {})
        self.assertEqual(self.views.current_successor(), "bob")

    def test_acceptance_by_a_non_designated_actor_is_inert(self):
        self._account("alice", "human")
        self._account("bob", "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "alice"})
        self.gate.execute("ACCEPT-SUCCESSION", "bob", {})          # bob is not the designated successor
        self.assertIsNone(self.views.current_successor())

    def test_verification_is_rechecked_live_at_read(self):
        # the mentor's RAISED-BY-DESIGN read: verify at the moment of the fold's validity. A successor
        # designated+accepted while verified stays valid; the fold reads verified() LIVE, so if the
        # grounding ever fails the successor stops being valid with no stored boolean to rot. Here we
        # prove the positive: a live-verified human is the successor.
        self._account("alice", "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "alice"})
        self.gate.execute("ACCEPT-SUCCESSION", "alice", {})
        self.assertTrue(self.views.verified("alice"))
        self.assertEqual(self.views.current_successor(), "alice")


# ---- N2: the anchor refusals at the gate ----------------------------------------------------

class TestAnchorRefusals(_Kernel):
    def test_self_removal_refuses_without_a_successor(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("HANDOVER", "owner", {})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")
        # and the refusal is recorded (cannot-do-quietly)
        self.assertTrue(any(e["action"] == "op-refused" for e in self.store.all()))

    def test_an_unverified_successor_refuses_at_designation(self):
        self._account("carol", "human", verify=False)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "carol"})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")

    def test_a_pure_agentic_successor_refuses_at_designation(self):
        self._account("eve", "agentic")     # verified, but not human
        with self.assertRaises(OpError) as cm:
            self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "eve"})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")

    def test_only_the_root_may_designate(self):
        self._account("alice", "human")
        with self.assertRaises(OpError) as cm:                    # a non-root actor, under openness
            self.gate.execute("DESIGNATE-SUCCESSOR", "mallory", {"successor": "alice"})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")

    def test_only_the_root_may_hand_over(self):
        self._ready_successor("alice")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("HANDOVER", "mallory", {})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")

    def test_the_lawful_handover_path_proceeds(self):
        self._ready_successor("alice")
        rec = self.gate.execute("HANDOVER", "owner", {})          # a valid successor exists -> proceeds
        self.assertEqual(rec["action"], "HANDOVER")
        self.assertEqual(self.views.chain_end(), "alice")         # the successor is the new chain-end


# ---- N4: the new chain-end governs and the old record stands (both directions + round-trip) --

class TestHandoverGoverns(_Kernel):
    def test_new_chain_end_governs_and_old_owner_does_not(self):
        self._ready_successor("alice")
        self.gate.execute("HANDOVER", "owner", {})
        # the successor now holds the root ceremony: alice may designate her own successor...
        self._account("bob", "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "alice", {"successor": "bob"})
        # ...and the OLD owner may not (its root authority ended by supersession)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "bob"})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")

    def test_the_old_record_stands(self):
        self._ready_successor("alice")
        self.gate.execute("HANDOVER", "owner", {})
        # the founding owner's CREATE-ACTOR, the designation, and the acceptance all remain (append-only)
        self.assertTrue(any(e["action"] == "CREATE-ACTOR"
                            and (e.get("payload") or {}).get("actor_id") == "owner" for e in self.store.all()))
        self.assertTrue(any(e["action"] == "DESIGNATE-SUCCESSOR" for e in self.store.all()))
        self.assertTrue(any(e["action"] == "HANDOVER" for e in self.store.all()))

    def test_the_handover_stores_no_owner_field_the_chain_end_is_derived(self):
        # the refused wrong reference: no owner FIELD is written. The HANDOVER record carries no
        # successor/owner pointer — the chain-end is DERIVED from the succession fold as of the handover.
        self._ready_successor("alice")
        rec = self.gate.execute("HANDOVER", "owner", {})
        self.assertNotIn("successor", rec.get("payload") or {})
        self.assertNotIn("new_owner", rec.get("payload") or {})
        self.assertNotIn("owner", rec.get("payload") or {})

    def test_everything_replays_the_new_chain_end_reconstructs(self):
        self._ready_successor("alice")
        self.gate.execute("HANDOVER", "owner", {})
        before = self.views.chain_end()
        _s2, _g2, v2 = build_kernel(self.path)                    # kill derived, replay from the file alone
        self.assertEqual(v2.chain_end(), before)                  # identical
        self.assertEqual(v2.chain_end(), "alice")


# ---- N3: cycle/orphan refusal at grant/role mint --------------------------------------------

class TestCycleOrphan(_Kernel):
    def test_a_grant_into_an_unfounded_space_refuses_at_mint(self):
        with self.assertRaises(OpError) as cm:                    # for the OWNER too (root is not exempt here)
            self.gate.execute("GRANT", "owner", {"grant_id": "o", "grantee": "x",
                              "actions": ["READ"], "info": ["n"], "space": "space:ghost"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        self.assertNotIn("grant:o", self.views.grants())

    def test_a_role_into_an_unfounded_space_refuses_at_mint(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-ROLE", "owner", {"name": "r", "space": "space:ghost"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        self.assertNotIn("role:r", self.views.roles())

    def test_a_grant_into_a_founded_space_mints(self):
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        self.gate.execute("GRANT", "owner", {"grant_id": "g", "grantee": "x",
                          "actions": ["READ"], "info": ["n"], "space": "space:team"})
        self.assertIn("grant:g", self.views.grants())             # a founded space chains to the root

    def test_the_default_openness_grant_is_not_orphaned(self):
        # a fresh founding refuses nothing: the openness grant (space:root) is present and unrefused
        self.assertIn("grant:founding-openness", self.views.grants())
        self.assertEqual(len(self.store.by_action("op-refused")), 0)


# ---- R-A: GRANT's leash moved to the gate; the covers default is pack data -------------------

class TestRiderA(_Kernel):
    def test_covers_default_regime_is_pack_data(self):
        self.assertEqual(self.views.policy_value("authority-regime-default"), "covers")

    def test_a_lawful_contained_grant_still_mints(self):
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")     # alice's reach
        self.gate.execute("GRANT", "alice", {"grant_id": "ok", "grantee": "bob",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        self.assertIn("grant:ok", self.views.grants())

    def test_an_overwide_grant_refuses_at_the_gate(self):
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")
        with self.assertRaises(OpError) as cm:                    # wider than alice's reach
            self.gate.execute("GRANT", "alice", {"grant_id": "wide", "grantee": "bob",
                              "actions": ["CREATE-RULE"], "info": ["note"], "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")

    def _sneak_op(self):
        """A passthrough op that mints a grant-kind record — the bypass R-A closes."""
        d = {"description": "passthrough grant minter",
             "params": {"grant_id": "required", "grantee": "required", "actions": "required",
                        "info": "required", "space": "required"},
             "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "grant:{grant_id}"},
             "payload_from": ["grantee", "actions", "info", "space", "grant_id"],
             # all five governance fields ride payload_from => inline; mirrors production GRANT, a pure
             # record-producer with no content (vocab door, design/46 member 2).
             "structural_params": ["grant_id", "grantee", "actions", "info", "space"],
             "payload_derive": {"kind": {"tpl": "grant"}, "polarity": {"tpl": "+"}}, "checks": []}
        self.gate.execute("CREATE-OP", "owner", {"name": "SNEAK-GRANT", "definition": d})

    def test_a_grant_kind_record_via_any_op_is_leashed(self):
        # R-A's point: enforcement in GRANT's handler let a passthrough op minting a grant-kind record
        # bypass the leash. At the gate chokepoint, ANY op minting a grant-kind record is leashed.
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")
        self._sneak_op()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("SNEAK-GRANT", "alice", {"grant_id": "wide", "grantee": "bob",
                              "actions": ["CREATE-RULE"], "info": ["note"], "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("grant:wide", self.views.grants())

    def test_a_contained_grant_via_a_passthrough_op_is_allowed(self):
        # the leash refuses only the OVER-WIDE grant-kind record; a CONTAINED one passes the gate (the
        # record is appended, no refusal). It does not become a FUNCTIONAL grant — the grant fold keys on
        # action == GRANT, so only the real GRANT op confers power — but the leash's containment bar is
        # satisfied both directions (refuse over-wide; allow contained), which is R-A's guarantee.
        self._narrow()
        self._grant("la", "alice", ["CREATE-INFO"], ["note"], "space:team")
        self._sneak_op()
        before = len(self.store.by_action("op-refused"))
        rec = self.gate.execute("SNEAK-GRANT", "alice", {"grant_id": "fine", "grantee": "bob",
                                "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        self.assertEqual(rec["action"], "SNEAK-GRANT")                       # appended, not refused
        self.assertEqual(len(self.store.by_action("op-refused")), before)   # the leash allowed it

    def test_the_leash_is_inert_under_openness(self):
        # a fresh founding: a non-root actor mints a grant freely (openness contains it)
        self.gate.execute("GRANT", "alice", {"grant_id": "free", "grantee": "bob",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": MOTHER})
        self.assertIn("grant:free", self.views.grants())


# ---- R-B: structure-class reach for founding spaces and roles --------------------------------

class TestRiderB(_Kernel):
    def test_the_structure_actions_vocabulary_is_a_founding_pack(self):
        levels = self.views.category_packs()["structure-actions"]["levels"]
        self.assertIn("CREATE-SPACE", levels)
        self.assertIn("CREATE-ROLE", levels)

    def test_a_read_grant_does_not_authorise_founding_a_subspace(self):
        # sight is not authority (the R-B point): a read-only grant over a space must not found subspaces
        self._narrow()
        self._grant("read", "alice", ["READ"], ["*"], "space:team")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-SPACE", "alice", {"name": "child", "parent": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("space:child", self.views.spaces())

    def test_a_read_grant_does_not_authorise_founding_a_role(self):
        self._narrow()
        self._grant("read", "alice", ["READ"], ["*"], "space:team")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-ROLE", "alice", {"name": "lead", "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("role:lead", self.views.roles())

    def test_a_structure_class_grant_authorises_founding_a_subspace(self):
        self._narrow()
        self._grant("struct", "alice", ["CREATE-SPACE", "CREATE-ROLE"], ["*"], "space:team")
        self.gate.execute("CREATE-SPACE", "alice", {"name": "child", "parent": "space:team"})
        self.gate.execute("CREATE-ROLE", "alice", {"name": "lead", "space": "space:team"})
        self.assertIn("space:child", self.views.spaces())
        self.assertIn("role:lead", self.views.roles())

    def test_r_b_is_inert_under_openness(self):
        # a fresh founding: a non-root actor founds spaces/roles freely (openness actions = * covers the class)
        self.gate.execute("CREATE-SPACE", "alice", {"name": "as", "parent": MOTHER})
        self.gate.execute("CREATE-ROLE", "alice", {"name": "ar", "space": MOTHER})
        self.assertIn("space:as", self.views.spaces())
        self.assertIn("role:ar", self.views.roles())


# ---- the chain-end is DERIVED (the refused wrong reference) ----------------------------------

class TestChainEndDerived(_Kernel):
    def test_founding_root_is_derived_from_the_record(self):
        # not a hardcoded 'owner' string — the actor the founding minted with root-instruction-authority
        self.assertEqual(self.views.founding_root(), "owner")

    def test_chain_end_is_the_founding_root_under_the_founding(self):
        # day one identical: no handover -> the chain-end is the founding root, every campaign-1 check holds
        self.assertEqual(self.views.chain_end(), "owner")

    def test_the_shipped_founding_narrows_nothing(self):
        # the world stays OPEN (W4): a fresh founding refuses nothing and keeps the openness grant intact
        self.assertEqual(len(self.store.by_action("op-refused")), 0)
        g = self.views.grants()["grant:founding-openness"]
        self.assertEqual((g["grantee"], g["actions"], g["info"], g["space"]), ("*", "*", "*", MOTHER))


if __name__ == "__main__":
    unittest.main()
