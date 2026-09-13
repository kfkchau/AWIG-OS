"""EP-15 acceptance battery (design/31 J1): accounts + verification — who is acting, verified.

This EP builds RESOLUTION, not refusal. An act by an account-holder resolves to the account;
an act by a bare legacy name resolves to `unverified:<name>` and PROCEEDS (enforcement of
no-account->no-act is EP-17's flip, under the founding openness grant). Attribution (who
INVOKED, in provenance.asserted_by) splits from acting authority (the `actor` field a handler
may lawfully set to SYSTEM). Verification bottoms out at the founding: owner/SYSTEM/PC_RUNTIME
are ANCHORED, a third resolution state — founding-asserted, not system-verified.

A4 acceptance, both directions, plus the two named wrong references refused (web-auth sessions;
password/plaintext storage). Every verification probe lands as a regression test (R14 / DIGEST-C1
§4). Three lenses: an ordinary bare actor, the owner through the documented path, a restart.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import EventStore, frozen_default  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from observe.resource_watch import register_resource_observe_ops  # noqa: E402


def _hash(secret):
    """The evidence hash is computed at the EDGE (client), never by the kernel — the kernel
    only ever sees the hash (verify-never-reveal; no plaintext secret enters the record)."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class _Kernel(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)


class TestAccountFoundsVerifiesResolves(_Kernel):
    """A4 direction 1: an account founds, verifies, and resolves in provenance."""

    def test_create_account_founds_an_identity_record(self):
        rec = self.gate.execute("CREATE-ACCOUNT", "owner",
                                {"account_id": "alice", "actor_class": "human"})
        self.assertEqual(rec["action"], "CREATE-ACCOUNT")
        self.assertEqual(rec["payload"]["kind"], "account")
        self.assertEqual(rec["payload"]["account_id"], "alice")
        self.assertEqual(rec["payload"]["actor_class"], "human")
        self.assertEqual(rec["payload"]["founded_by"], "owner")     # stamped = the founder (caller)
        # DERIVED, not a stored boolean: a fresh account has no verification yet -> unverified
        self.assertEqual(self.views.accounts()["alice"]["resolution"], "unverified")
        self.assertFalse(self.views.verified("alice"))

    def test_verify_account_marks_verified_derived_per_check(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        self.assertFalse(self.views.verified("alice"))
        self.gate.execute("VERIFY-ACCOUNT", "owner",
                          {"account": "alice", "evidence_hash": _hash("alice-passport")})
        # verified is now DERIVED true — never written onto the account as a status
        self.assertTrue(self.views.verified("alice"))
        self.assertEqual(self.views.accounts()["alice"]["resolution"], "verified")

    def test_an_account_holders_act_resolves_to_the_account_in_provenance(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        rec = self.gate.execute("CREATE-INFO", "alice", {"content": "note"})
        self.assertEqual(rec["provenance"]["asserted_by"], "alice")   # resolved to the account
        self.assertEqual(rec["actor"], "alice")

    def test_verify_of_an_unfounded_account_refuses(self):
        # referential integrity at use (the require_prior check): you cannot verify an account
        # that was never founded. Refuses + records, cited — never a silent dangling reference.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("VERIFY-ACCOUNT", "owner",
                              {"account": "ghost", "evidence_hash": _hash("x")})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        self.assertEqual(len(self.store.by_action("VERIFY-ACCOUNT")), 0)   # nothing landed


class TestTransitionBareNameStillActs(_Kernel):
    """A4 direction 2 + THE TRANSITION: a bare legacy name still ACTS and is marked unverified.
    This EP does NOT enforce no-account->no-act (that is EP-17). Resolution, not refusal."""

    def test_bare_name_acts_and_is_marked_unverified_in_provenance(self):
        rec = self.gate.execute("CREATE-INFO", "legacy-bob", {"content": "still works"})
        self.assertEqual(rec["action"], "CREATE-INFO")                 # it PROCEEDED
        self.assertEqual(rec["provenance"]["asserted_by"], "unverified:legacy-bob")
        # the bare name is NOT an account (nothing founded it)
        self.assertNotIn("legacy-bob", self.views.accounts())

    def test_bare_name_is_not_refused_this_ep(self):
        # the openness grant covers the bare name until EP-17 narrows it; no refusal is recorded
        before = len(self.store.by_action("op-refused"))
        self.gate.execute("CREATE-INFO", "nobody", {"content": "c"})
        self.assertEqual(len(self.store.by_action("op-refused")), before)


class TestFoundingAnchorsAreAnchoredNotVerified(_Kernel):
    """A4: the founding actors are ANCHORED, not verified — a third resolution state (J1)."""

    def test_owner_system_pc_runtime_are_anchored(self):
        accts = self.views.accounts()
        for anchor in ("owner", "SYSTEM", "PC_RUNTIME"):
            self.assertEqual(accts[anchor]["resolution"], "anchored", anchor)
            self.assertFalse(self.views.verified(anchor), anchor)      # anchored != verified

    def test_no_account_record_is_minted_for_the_anchors(self):
        # ruling 1(b): the anchors are DERIVED from the genesis CREATE-ACTOR records, never minted
        # as account records (a copy of a founding that already happened). Zero account records.
        account_records = [e for e in self.store.all()
                           if (e.get("payload") or {}).get("kind") == "account"]
        self.assertEqual(account_records, [])

    def test_anchor_resolves_to_itself_at_the_gate(self):
        for anchor in ("owner", "SYSTEM", "PC_RUNTIME"):
            self.assertEqual(self.views.resolve_asserted_by(anchor), anchor)

    def test_a_runtime_minted_actor_is_not_an_anchor(self):
        # a runtime CREATE-ACTOR (asserted by owner) mints an actor, NOT a founding anchor
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": "sched", "role": "subsystem"})
        self.assertNotIn("sched", self.views._anchor_ids())
        self.assertEqual(self.views.resolve_asserted_by("sched"), "unverified:sched")


class TestVerificationEvidenceIsAHash(_Kernel):
    """A4 + the named wrong reference (password/plaintext storage) REFUSED: verification evidence
    is hash-only from birth — no plaintext secret ever enters the record (CONST-SECRETS is
    recorded law already; this builds its cousin without violating it)."""

    def test_evidence_is_a_hash_the_record_cannot_reverse(self):
        secret = "my-real-passport-number-8837"
        h = _hash(secret)
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        rec = self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": "alice", "evidence_hash": h})
        self.assertEqual(rec["payload"]["kind"], "verification")
        self.assertEqual(rec["payload"]["evidence_hash"], h)
        # the plaintext secret appears NOWHERE in the record (the whole record serialised)
        blob = json.dumps(rec, default=frozen_default)
        self.assertNotIn(secret, blob)
        # and there is no plaintext-evidence field — only the hash
        self.assertNotIn("evidence", rec["payload"])          # no plaintext `evidence` field
        self.assertNotIn("secret", rec["payload"])

    def test_the_op_accepts_no_plaintext_param(self):
        # structural: VERIFY-ACCOUNT's params are {account, evidence_hash} — there is no plaintext
        # `evidence`/`secret`/`password` parameter to store, so no plaintext CAN enter the record.
        spec = self.gate.list()["VERIFY-ACCOUNT"]["params"]
        self.assertEqual(set(spec), {"account", "evidence_hash"})


class TestAttributionSplitsFromActingAuthority(_Kernel):
    """design/31 §9 pass-two #4 made structural: the record's `actor` is who-it-acted-AS; the
    provenance carries who-INVOKED. WRITE-ACTIVITY acts as SYSTEM while a caller invoked it."""

    def test_write_activity_acts_as_system_but_provenance_carries_the_invoker(self):
        rec = self.gate.execute("WRITE-ACTIVITY", "legacy-bob",
                                {"about": "x", "data": {"note": "telemetry"}})
        self.assertEqual(rec["actor"], "SYSTEM")                       # AS-WHOM (handler-set)
        self.assertEqual(rec["provenance"]["asserted_by"], "unverified:legacy-bob")  # WHO-INVOKED

    def test_system_invoking_write_activity_resolves_anchored(self):
        rec = self.gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": "x", "data": {}})
        self.assertEqual(rec["actor"], "SYSTEM")
        self.assertEqual(rec["provenance"]["asserted_by"], "SYSTEM")   # SYSTEM is a founding anchor


class TestNoSessionResolvesFresh(_Kernel):
    """The web-auth wrong reference REFUSED: there is NO session, no token, no 'current user'
    state. The record IS the session — every act resolves FRESH from the record (chain evaluated
    live, J3). Founding an account changes later resolutions without any cached login."""

    def test_same_name_resolves_differently_before_and_after_its_account_is_founded(self):
        # act 1: bob has no account yet -> unverified
        r1 = self.gate.execute("CREATE-INFO", "bob", {"content": "before"})
        self.assertEqual(r1["provenance"]["asserted_by"], "unverified:bob")
        # bob's account is founded
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "bob", "actor_class": "human"})
        # act 2: the SAME name now resolves to the account — no session carried the change, the
        # record did (each act is resolved anew at its own moment)
        r2 = self.gate.execute("CREATE-INFO", "bob", {"content": "after"})
        self.assertEqual(r2["provenance"]["asserted_by"], "bob")

    def test_the_gate_holds_no_logged_in_state(self):
        # a cached 'current user'/'session'/'token' anywhere would be a stored status (P2 violation)
        for banned in ("session", "sessions", "current_user", "logged_in", "token"):
            self.assertFalse(hasattr(self.gate, banned), banned)


class TestVerifierGroundsAtTheAnchors(_Kernel):
    """Raise #2 (approved): the verifier is itself a verified account, recursion grounding at the
    founding anchors. A verification by a NON-grounded verifier does not manufacture verification
    — design for the stretch (a cycle of mutual unverified verifications never grounds)."""

    def test_an_anchor_grounds_the_first_verification(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": "alice", "evidence_hash": _hash("a")})
        self.assertTrue(self.views.verified("alice"))                  # owner (anchor) grounds it

    def test_a_verified_account_can_verify_the_next_recursion_climbs(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": "alice", "evidence_hash": _hash("a")})
        self.gate.execute("CREATE-ACCOUNT", "alice", {"account_id": "carol", "actor_class": "human"})
        self.gate.execute("VERIFY-ACCOUNT", "alice", {"account": "carol", "evidence_hash": _hash("c")})
        self.assertTrue(self.views.verified("carol"))                 # alice (verified) grounds carol

    def test_verification_by_an_unverified_verifier_does_not_ground(self):
        # dave and erin both have accounts but neither is grounded; they verify each other in a
        # cycle. Neither becomes verified — verification cannot be manufactured off the anchors.
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "dave", "actor_class": "human"})
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "erin", "actor_class": "human"})
        self.gate.execute("VERIFY-ACCOUNT", "dave", {"account": "erin", "evidence_hash": _hash("e")})
        self.gate.execute("VERIFY-ACCOUNT", "erin", {"account": "dave", "evidence_hash": _hash("d")})
        self.assertFalse(self.views.verified("dave"))
        self.assertFalse(self.views.verified("erin"))

    def test_verifier_is_recorded(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        rec = self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": "alice", "evidence_hash": _hash("a")})
        self.assertEqual(rec["payload"]["verifier"], "owner")         # stamped = the acting verifier


class TestAccountsSurviveRoundTrip(_Kernel):
    """The restart lens (DIGEST-C1 §4) + total round-trip: accounts and verification are DERIVED,
    so they replay identically from the record file alone (kill every derived cache, rebuild)."""

    def test_accounts_and_verification_replay_identically(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": "alice", "evidence_hash": _hash("a")})
        self.gate.execute("CREATE-INFO", "legacy-bob", {"content": "bare"})   # a transition act
        before = self.views.accounts()
        # rebuild a fresh kernel from the same file — every derived cache killed
        _s2, _g2, views2 = build_kernel(self.path)
        self.assertEqual(views2.accounts(), before)                   # identical, derived not stored
        self.assertTrue(views2.verified("alice"))
        # the bare act's resolution survives on its own record (provenance is on the record)
        info = [e for e in views2.store.by_action("CREATE-INFO") if e.get("object") == "bare"][0]
        self.assertEqual(info["provenance"]["asserted_by"], "unverified:legacy-bob")


class TestCampaign1BoundaryUnchanged(_Kernel):
    """The one boundary the resolution touches that a campaign-1 test might not pin: a handler
    that ASSERTS its own provenance (an observe adapter, recording through a /proc window) is
    NOT overwritten by the gate's caller-resolution. The full suite proves the rest UNCHANGED."""

    def test_observe_adapter_provenance_is_preserved_not_overwritten(self):
        register_resource_observe_ops(self.gate, self.store)
        rec = self.gate.execute("OBSERVE-RESOURCE", "resource-watcher",
                                {"event": "mount-appeared", "object": "mount:/x",
                                 "source": "/proc/mounts", "data": {"key": "/x"}})
        # the handler's deliberate provenance (asserted_by=the watcher, source=the window) stands
        self.assertEqual(rec["provenance"]["source"], "/proc/mounts")
        self.assertEqual(rec["provenance"]["asserted_by"], "resource-watcher")

    def test_owner_tier_makes_the_account_ops_founding_only(self):
        # CREATE-ACCOUNT/VERIFY-ACCOUNT are owner tier (founding-only, conservation) — a bare
        # RETIRE-OP of a protected op is refused for every actor (EP-05C machinery, reused).
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RETIRE-OP", "owner", {"name": "CREATE-ACCOUNT"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")


if __name__ == "__main__":
    unittest.main()
