"""EP-19 — the secrets vault: verify, never reveal (design/31 J8) + rider R-C.

Every probe here is a regression test (the campaign method: a verification probe lands
as a test). The vault's guarantee is CLOSURE, not encryption — there is NO read op for a
secret value; reading one back through the system is a Closure Hit (an ABSENT op, not a
refused one). The value lives write-once in the vault with no read path; the record holds
only the hash and MATCH/NO-MATCH decisions.

Coverage:
  V1  the vault module — write-once, hash-keyed, NO read path; seal + compare only; a
      code-review assertion that no function returns a stored secret value.
  V2  SEAL-SECRET / VERIFY-SECRET — owner-tier, definition-born, through the gate; the
      value never lands in a payload (content_params-style, routed to the vault).
  V3  account verification is a VERIFY-SECRET consumer — one hash home; VERIFY-SECRET
      joins the dual-audit pack (grow-only). [The deeper literal-consumer re-home is
      RAISED — see BUILD-PROGRESS: it would reverse EP-15's frozen caller-pre-hashed.]
  V4  both directions; the literal-absence test (plaintext grep-absent from the record);
      the Closure Hit / owner-cannot-read probes; round-trip (vault file + record); the
      CONST-SECRETS flip; rotation is supersession-by-hash (latest-per-name).
  R-C1 the owner-literal sweep to the chain-end: brake axis + read exemption, with a
       post-handover test (the NEW chain-end inherits; the old owner is ordinary).
  R-C2 the vestigial `attenuation` check kind retired.
  R-C3 R-B tightens to EXACT-ACTION.
  R-C4 the cycle/orphan citation split (BOOT-INT for cycles, CAP-IS-LAW for orphans).
  V5  VERIFY-ACCOUNT joins the dual-audit pack (mentor verdict 2026-07-25): a verification in the
      composed kernel lands in BOTH mutually-blind streams; the third-party cross-check stays clean;
      the streams stay blind and agree independently.
  V6  the rotation fold keys on (space, name), not bare name: same-named secrets in two spaces
      rotate independently (no clobber); same-space rotation still supersedes; inert under one space.
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.vault import VaultStore, secret_hash  # noqa: E402
from kernel.errors import OpError  # noqa: E402

MOTHER = "space:root"
SECRET = "correct-horse-battery-staple-UNIQUE-7f3a9"   # a distinctive plaintext for the absence test


def _h(s):
    return hashlib.sha256(s.encode()).hexdigest()


class _Full(unittest.TestCase):
    """A full kernel with a vault wired (SEAL-SECRET / VERIFY-SECRET registered)."""
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blob_dir = os.path.join(self.dir, "blobs")
        self.vault_dir = os.path.join(self.dir, "vault")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, self.blob_dir, self.vault_dir)


# ---- V1: the vault module — write-once, hash-keyed, NO read path -----------------------------

class TestVaultModule(unittest.TestCase):
    def setUp(self):
        self.vault = VaultStore(tempfile.mkdtemp())

    def test_seal_returns_a_hash_not_the_value(self):
        h = self.vault.seal(SECRET)
        self.assertEqual(h, secret_hash(SECRET))
        self.assertTrue(h.startswith("sha256:"))
        self.assertNotIn(SECRET, h)

    def test_compare_matches_the_sealed_value_and_rejects_others(self):
        h = self.vault.seal(SECRET)
        self.assertTrue(self.vault.compare(SECRET, h))
        self.assertFalse(self.vault.compare("wrong", h))
        self.assertFalse(self.vault.compare(SECRET, None))   # nothing sealed -> no match

    def test_the_module_has_no_read_path(self):
        # the surface is exactly seal + compare (design/31 J8): no get/read/reveal/open/has.
        for banned in ("get", "read", "reveal", "open", "has", "value", "plaintext"):
            self.assertFalse(hasattr(self.vault, banned),
                             f"VaultStore must expose no `{banned}` — the read path must be ABSENT (closure)")
        methods = {n for n in dir(self.vault) if not n.startswith("_") and callable(getattr(self.vault, n))}
        self.assertEqual(methods, {"seal", "compare"})

    def test_code_review_assertion_no_function_returns_a_stored_secret_value(self):
        # grep the module source: no function reads a stored value back out. `seal` WRITES
        # (write_bytes); nothing reads (no read_bytes/read_text/open-for-read). This is the V1
        # code-review assertion — the closure is a property of the SOURCE, not just behaviour.
        with open(os.path.join(os.path.dirname(__file__), "..", "src", "kernel", "vault.py")) as f:
            src = f.read()
        self.assertIn("write_bytes", src)                                  # seal writes
        for reader in ("read_bytes", "read_text", ".read(", "def get", "def read", "def reveal", "def open"):
            self.assertNotIn(reader, src, f"vault.py must not contain `{reader}` — no read path")

    def test_write_once_identical_values_coincide(self):
        h1 = self.vault.seal(SECRET)
        h2 = self.vault.seal(SECRET)   # sealing the same value again is idempotent (write-once)
        self.assertEqual(h1, h2)


# ---- V2: SEAL-SECRET / VERIFY-SECRET — owner-tier, definition-born, through the gate ---------

class TestSecretOps(_Full):
    def test_ops_are_owner_tier_definition_born(self):
        od = self.views.op_definitions()
        for op in ("SEAL-SECRET", "VERIFY-SECRET"):
            self.assertIn(op, od, op)
            self.assertEqual(od[op]["tier"], "owner", op)   # secret infrastructure — genesis-only

    def test_seal_records_the_hash_only_never_the_value(self):
        rec = self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        p = dict(rec["payload"])
        self.assertEqual(p["secret_hash"], secret_hash(SECRET))
        self.assertEqual(p["name"], "db-pw")
        self.assertNotIn("value", p)                        # the value never lands in a payload
        for v in p.values():
            self.assertNotEqual(v, SECRET)

    def test_verify_records_result_and_hash_never_the_candidate(self):
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        ok = self.gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": SECRET})
        p = dict(ok["payload"])
        self.assertEqual(p["result"], "MATCH")
        self.assertEqual(p["secret_hash"], secret_hash(SECRET))
        self.assertNotIn("candidate", p)
        for v in p.values():
            self.assertNotEqual(v, SECRET)
        no = self.gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": "guess"})
        self.assertEqual(dict(no["payload"])["result"], "NO-MATCH")
        self.assertNotIn("guess", str(dict(no["payload"])))

    def test_verify_of_an_unsealed_name_is_no_match(self):
        no = self.gate.execute("VERIFY-SECRET", "owner", {"name": "never-sealed", "candidate": "x"})
        p = dict(no["payload"])
        self.assertEqual(p["result"], "NO-MATCH")
        self.assertIsNone(p["secret_hash"])                 # nothing sealed -> no hash to record

    def test_secret_ops_are_honestly_pending_without_a_vault(self):
        # a bare kernel (no vault) registers neither op — surfaced, not silently broken (like content ops)
        # [DOCUMENTED FLIP, EP-23: the honest ledger GROWS. PRESENT-CREDENTIAL is the vault's third
        #  consumer — a crossing's credential compared by hash — so it is pending for the same reason
        #  and by the same mechanism. The ledger enumerates the deferral; a new vault consumer joining
        #  it is the mechanism working, not a new deferral.]
        from kernel.opdefs import secret_ops_pending_vault
        d = tempfile.mkdtemp()
        store, gate, views = build_kernel(os.path.join(d, "r.jsonl"))
        self.assertFalse(gate.has("SEAL-SECRET"))
        self.assertFalse(gate.has("VERIFY-SECRET"))
        self.assertFalse(gate.has("PRESENT-CREDENTIAL"))
        self.assertEqual(secret_ops_pending_vault(gate, store),
                         ["PRESENT-CREDENTIAL", "SEAL-SECRET", "VERIFY-SECRET"])


# ---- V3: one mechanism — the shared hash home + VERIFY-SECRET in the dual-audit pack ---------

class TestReHome(_Full):
    def test_verify_secret_joins_the_dual_audit_pack_grow_only(self):
        levels = self.views.category_packs()["dual-audit-actions"]["levels"]
        self.assertIn("VERIFY-SECRET", levels)              # verification events are governance-grade
        # grow-only: the campaign-1 floor is preserved (nothing dropped)
        for prior in ("op-refused", "GRANT-READ", "HALT-WATCHER", "RESOLVE-WATCHER"):
            self.assertIn(prior, levels)

    def test_the_vault_is_the_one_hash_home_the_family_shares(self):
        # account verification evidence (EP-15, caller-pre-hashed) and secret sealing share ONE hash
        # scheme — vault.secret_hash — so there is no parallel hashing machinery (design/31 J8 re-home).
        self.assertEqual(secret_hash("x"), "sha256:" + hashlib.sha256(b"x").hexdigest())
        self.gate.execute("SEAL-SECRET", "owner", {"name": "n", "value": "x"})
        self.assertEqual(self.views.sealed_secret_hash("n"), secret_hash("x"))


# ---- V4: both directions; the literal absence; the closure/owner probes; round-trip ---------

class TestVerifyNeverReveal(_Full):
    def test_literal_absence_the_plaintext_is_grep_absent_from_the_record(self):
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        self.gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": SECRET})
        with open(self.record, "rb") as f:
            raw = f.read()
        self.assertNotIn(SECRET.encode(), raw)              # the plaintext is nowhere in the record file
        self.assertIn(b"secret_hash", raw)                  # only the hash is recorded
        self.assertIn(secret_hash(SECRET).encode(), raw)    # and it is the right hash

    def test_on_disk_cap_the_value_is_in_the_vault_not_the_record(self):
        # HONEST CAP (design/31 §7): closure closes the SYSTEM path, not the disk path. The value IS on
        # disk in the vault dir (campaign-4 crypto closes that); it is simply unreadable THROUGH the
        # system — no read op exists. This test states the cap plainly rather than hiding it.
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        on_disk = b""
        for root, _dirs, files in os.walk(self.vault_dir):
            for fn in files:
                with open(os.path.join(root, fn), "rb") as f:
                    on_disk += f.read()
        self.assertIn(SECRET.encode(), on_disk)             # the value lives in the vault (write-once)
        with open(self.record, "rb") as f:
            self.assertNotIn(SECRET.encode(), f.read())     # never in the record

    def test_closure_hit_there_is_no_op_that_returns_a_value(self):
        # reading a secret back is an ABSENT op, not a refused one — a Closure Hit (P3). No read-shaped
        # op is registered at all.
        for name in ("READ-SECRET", "REVEAL-SECRET", "GET-SECRET", "UNSEAL-SECRET", "OPEN-SECRET"):
            self.assertFalse(self.gate.has(name), f"{name} must not exist — no read op for a secret")
            with self.assertRaises(OpError) as cm:
                self.gate.execute(name, "owner", {"name": "db-pw"})
            self.assertEqual(cm.exception.rule, "P3-CLOSURE")

    def test_the_owner_cannot_read_a_secret(self):
        # verify-never-reveal binds EVERY actor including the owner/chain-end: even the owner has no read
        # op; the owner's VERIFY yields only MATCH/NO-MATCH, never the value.
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("REVEAL-SECRET", "owner", {"name": "db-pw"})
        self.assertEqual(cm.exception.rule, "P3-CLOSURE")
        rec = self.gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": SECRET})
        self.assertEqual(dict(rec["payload"])["result"], "MATCH")   # the most the owner learns: it matched
        self.assertNotIn(SECRET, str(dict(rec["payload"])))

    def test_round_trip_vault_file_and_record_replay_together(self):
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        # rebuild the whole kernel from the record file + the same vault dir — nothing derived kept
        store2, gate2, views2, _b, _s = build_full_kernel(self.record, self.blob_dir, self.vault_dir)
        self.assertEqual(views2.sealed_secret_hash("db-pw"), secret_hash(SECRET))
        rec = gate2.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": SECRET})
        self.assertEqual(dict(rec["payload"])["result"], "MATCH")   # verifies after replay

    def test_const_secrets_flip_is_documented(self):
        rr = {r["rule_id"]: r for r in self.views.root_rules()}
        self.assertEqual(rr["CONST-SECRETS"]["enforcement"], "live")      # deferred -> live
        self.assertIn("vault", rr["CONST-SECRETS"]["enforced_by"])        # enforced_by names the vault
        self.assertNotIn("CONST-SECRETS", self.views.toothless_musts())   # not toothless (it has the vault)

    def test_rotation_is_supersession_by_hash_latest_per_name(self):
        # RAISED-BY-DESIGN: secret rotation is supersession by hash; the fold reads latest-per-name.
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "rotated-value-v2"})
        self.assertEqual(self.views.sealed_secret_hash("db-pw"), secret_hash("rotated-value-v2"))
        old = self.gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": SECRET})
        new = self.gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": "rotated-value-v2"})
        self.assertEqual(dict(old["payload"])["result"], "NO-MATCH")      # the old value no longer matches
        self.assertEqual(dict(new["payload"])["result"], "MATCH")         # the newest seal wins


# ---- R-C1: the owner-literal sweep to the chain-end (brake axis + read exemption) ------------

class _Kernel(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "r.jsonl"))

    def _account(self, acct, actor_class="human"):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": acct, "actor_class": actor_class})
        self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": acct, "evidence_hash": _h(acct)})

    def _handover_to(self, acct="alice"):
        self._account(acct, "human")
        self.gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": acct})
        self.gate.execute("ACCEPT-SUCCESSION", acct, {})
        self.gate.execute("HANDOVER", "owner", {})
        self.assertEqual(self.views.chain_end(), acct)     # the chain-end moved


class TestBrakeAxisSweep(_Kernel):
    def test_under_the_founding_the_brake_axis_is_the_founding_root(self):
        # day-one identical: the resolver/unbrakable identity is the chain-end, which IS "owner"
        self.gate.execute("HALT-WATCHER", "owner", {"watcher": "bob"})
        self.assertIn("bob", self.views.halted_watchers())
        self.gate.execute("RESOLVE-WATCHER", "owner", {"watcher": "bob"})   # owner (chain-end) resolves
        self.assertNotIn("bob", self.views.halted_watchers())

    def test_after_handover_the_new_chain_end_resolves_and_is_unbrakable(self):
        self._handover_to("alice")
        # the NEW chain-end (alice) resolves a brake
        self.gate.execute("HALT-WATCHER", "owner", {"watcher": "bob"})
        self.gate.execute("RESOLVE-WATCHER", "alice", {"watcher": "bob"})
        self.assertNotIn("bob", self.views.halted_watchers())
        # the NEW chain-end is UNBRAKABLE (HALT against alice refuses)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("HALT-WATCHER", "owner", {"watcher": "alice"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_after_handover_the_old_owner_is_ordinary(self):
        self._handover_to("alice")
        # the departed owner is no longer the resolver — a RESOLVE-WATCHER by the old owner refuses
        self.gate.execute("HALT-WATCHER", "owner", {"watcher": "bob"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RESOLVE-WATCHER", "owner", {"watcher": "bob"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        # and the old owner is now BRAKABLE (it is an ordinary account, not the root)
        self.gate.execute("HALT-WATCHER", "alice", {"watcher": "owner"})
        self.assertIn("owner", self.views.halted_watchers())


class TestReadExemptionSweep(_Kernel):
    def test_read_exemption_follows_the_chain_end(self):
        from kernel.protection import can_read
        # under the founding, the chain-end (owner) reads everything; a bare account does not
        self.assertTrue(can_read(self.store, "owner", "pack:anything", self.views.chain_end()))
        self.assertFalse(can_read(self.store, "nobody", "pack:anything", self.views.chain_end()))
        # after a handover the NEW chain-end holds the read exemption; the old owner falls to grants
        self._handover_to("alice")
        ce = self.views.chain_end()
        self.assertTrue(can_read(self.store, "alice", "pack:anything", ce))   # successor exempt
        self.assertFalse(can_read(self.store, "owner", "pack:secret-thing", ce))  # old owner not exempt
        self.assertTrue(can_read(self.store, "SYSTEM", "pack:anything", ce))  # SYSTEM stays exempt (recorder)


# ---- R-C2: the vestigial `attenuation` check kind is retired ---------------------------------

class TestAttenuationRetired(_Kernel):
    def test_attenuation_is_no_longer_a_check_kind(self):
        from kernel import opdefs
        self.assertNotIn("attenuation", opdefs.OP_CHECKS)
        # defining an op that cites the retired check is refused as an unknown check kind
        d = {"law_cited": "CAP-IS-LAW", "params": {"x": "required"},
             "checks": [{"check": "attenuation", "grantee_param": "x"}]}
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-OP", "owner", {"name": "USES-ATTEN", "definition": d})
        self.assertEqual(cm.exception.rule, "AR-2")

    def test_grant_containment_still_enforced_at_the_gate(self):
        # the leash did not disappear — it lives at the gate chokepoint now (R-A). In a narrowed world,
        # a non-root actor cannot mint a grant wider than its own reach.
        for n, p in [("team", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.gate.execute("GRANT", "owner", {"grant_id": "narrow", "grantee": "alice",
                          "actions": ["READ"], "info": ["*"], "space": "space:team"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "alice", {"grant_id": "wide", "grantee": "bob",
                              "actions": ["WRITE"], "info": ["*"], "space": MOTHER})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")


# ---- R-C3: R-B tightens to EXACT-ACTION -------------------------------------------------------

class TestExactAction(_Kernel):
    def _narrow(self):
        for n, p in [("team", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})

    def test_a_role_founding_grant_does_not_found_a_space(self):
        # class membership alone no longer reaches: a CREATE-ROLE grant must not authorise CREATE-SPACE
        self._narrow()
        self.gate.execute("GRANT", "owner", {"grant_id": "roleonly", "grantee": "alice",
                          "actions": ["CREATE-ROLE"], "info": ["*"], "space": "space:team"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-SPACE", "alice", {"name": "child", "parent": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("space:child", self.views.spaces())
        # but it DOES authorise founding a role (the exact act it carries)
        self.gate.execute("CREATE-ROLE", "alice", {"name": "lead", "space": "space:team"})
        self.assertIn("role:lead", self.views.roles())

    def test_a_space_founding_grant_does_not_found_a_role(self):
        self._narrow()
        self.gate.execute("GRANT", "owner", {"grant_id": "spaceonly", "grantee": "alice",
                          "actions": ["CREATE-SPACE"], "info": ["*"], "space": "space:team"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-ROLE", "alice", {"name": "lead", "space": "space:team"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.gate.execute("CREATE-SPACE", "alice", {"name": "child", "parent": "space:team"})
        self.assertIn("space:child", self.views.spaces())

    def test_exact_action_is_inert_under_openness(self):
        # a fresh founding (openness actions = *): a non-root actor founds both freely
        self.gate.execute("CREATE-SPACE", "alice", {"name": "as", "parent": MOTHER})
        self.gate.execute("CREATE-ROLE", "alice", {"name": "ar", "space": MOTHER})
        self.assertIn("space:as", self.views.spaces())
        self.assertIn("role:ar", self.views.roles())


# ---- R-C4: the cycle/orphan citation split ---------------------------------------------------

class TestCycleOrphanSplit(_Kernel):
    def test_orphan_grant_cites_cap_is_law(self):
        # a grant naming an UNFOUNDED space -> orphan -> CAP-IS-LAW (referential integrity)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "owner", {"grant_id": "o", "grantee": "x",
                              "actions": ["READ"], "info": ["*"], "space": "space:ghost"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")

    def test_cycle_grant_cites_boot_int(self):
        # a space whose parent chain LOOPS (a corrupted chain — a founded space cannot loop through the
        # gate, so this is white-box constructed) -> the grant naming it -> BOOT-INT (the space-tree
        # cycle citation). Proves the split: orphan and loop no longer share one citation.
        self.store._append({"actor": "owner", "action": "CREATE-SPACE", "object": "space:loop",
                            "rule_cited": "CAP-IS-LAW",
                            "payload": {"kind": "space", "name": "loop", "parent": "space:loop"}})
        self.assertIn("space:loop", self.views.spaces())                       # it exists in the tree
        self.assertFalse(self.views.space_reaches(MOTHER, "space:loop"))       # but never reaches the root
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "owner", {"grant_id": "c", "grantee": "x",
                              "actions": ["READ"], "info": ["*"], "space": "space:loop"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")


# ---- V5: VERIFY-ACCOUNT joins the dual-audit pack (mentor verdict 2026-07-25) ----------------
# An account becoming verified changes who can be trusted downstream — a governance act, exactly
# what the two mutually-blind streams exist to witness. A pilot's identity events must be audited
# from day one. Grow-only pack change; a VERIFY-ACCOUNT in the COMPOSED kernel now mirrors to BOTH
# streams (the documented count movement — it only appears where a VERIFY-ACCOUNT runs in a kernel
# with Protection wired, which is the full composition; no campaign-1 or bare-kernel test does this).

class TestVerifyAccountJoinsDualAudit(_Full):
    def _verify_alice(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        return self.gate.execute("VERIFY-ACCOUNT", "owner", {"account": "alice", "evidence_hash": _h("alice")})

    def test_verify_account_is_in_the_dual_audit_floor_grow_only(self):
        levels = self.views.category_packs()["dual-audit-actions"]["levels"]
        self.assertIn("VERIFY-ACCOUNT", levels)                                    # joined the pack
        self.assertIn("VERIFY-SECRET", levels)                                     # nothing dropped (grow-only)
        self.assertIn("VERIFY-ACCOUNT", self.views.protection._audit_actions())    # the live mirror follows the growth

    def test_verify_account_lands_in_both_blind_streams(self):
        seq = self._verify_alice()["seq"]
        a = [m for m in self.store.by_action("dual-audit-record") if m["payload"]["ref_seq"] == seq]
        b = [m for m in self.store.by_action("dual-audit-b-record") if m["payload"]["ref_seq"] == seq]
        self.assertEqual(len(a), 1)                                                # stream A witnessed the verification
        self.assertEqual(len(b), 1)                                                # stream B witnessed it INDEPENDENTLY
        self.assertEqual(a[0]["payload"]["ref_action"], "VERIFY-ACCOUNT")
        self.assertEqual(b[0]["payload"]["ref_action"], "VERIFY-ACCOUNT")

    def test_the_third_party_cross_check_stays_clean(self):
        self._verify_alice()
        # dual_blind_divergences is the THIRD party (neither stream writer runs it): clean means the two
        # blind streams and the recomputed digest all agree on every witnessed referent.
        self.assertEqual(self.views.protection.dual_blind_divergences(), [])

    def test_the_streams_stay_blind_a_mirror_is_never_itself_mirrored(self):
        self._verify_alice()
        refs = [m["payload"]["ref_action"] for m in self.store.by_action("dual-audit-record")] \
             + [m["payload"]["ref_action"] for m in self.store.by_action("dual-audit-b-record")]
        self.assertNotIn("dual-audit-record", refs)                               # a mirror is not a governance action
        self.assertNotIn("dual-audit-b-record", refs)                             # so neither stream digests the other

    def test_the_two_streams_agree_independently_on_the_verification(self):
        seq = self._verify_alice()["seq"]
        a = {m["payload"]["ref_seq"]: m["payload"]["digest"] for m in self.store.by_action("dual-audit-record")}
        b = {m["payload"]["ref_seq"]: m["payload"]["digest"] for m in self.store.by_action("dual-audit-b-record")}
        self.assertIn(seq, a)
        self.assertIn(seq, b)
        self.assertEqual(a[seq], b[seq])                          # two independent computations, one digest -> agree


# ---- V6: the rotation fold keys on (space, name), not bare name (mentor verdict 2026-07-25) --
# Latest-per-bare-name lets a seal in one space supersede a same-named secret in another (cross-space
# clobbering of sealed baselines). Everything lives in a space (J2); the record already carries one
# (the general space passthrough); the fold uses it. Inert in the one-space world — every seal and
# every query resolve to the mother space, so this is IDENTICAL to the old latest-per-name there.

class TestRotationKeysOnSpaceAndName(_Full):
    def _space(self, name):
        self.gate.execute("CREATE-SPACE", "owner", {"name": name, "parent": MOTHER})
        return "space:" + name

    def test_same_named_secrets_in_two_spaces_rotate_independently(self):
        sx, sy = self._space("teamx"), self._space("teamy")
        # the SAME name "db-pw" sealed in two different spaces with different values
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "x-value-1", "space": sx})
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "y-value-1", "space": sy})
        # the fold reads latest-per-(space, name): each space keeps its OWN baseline (no clobber)
        self.assertEqual(self.views.sealed_secret_hash("db-pw", sx), secret_hash("x-value-1"))
        self.assertEqual(self.views.sealed_secret_hash("db-pw", sy), secret_hash("y-value-1"))
        # VERIFY in space X matches X's value and NOT Y's; in space Y the mirror image
        self.assertEqual(dict(self.gate.execute("VERIFY-SECRET", "owner",
            {"name": "db-pw", "candidate": "x-value-1", "space": sx})["payload"])["result"], "MATCH")
        self.assertEqual(dict(self.gate.execute("VERIFY-SECRET", "owner",
            {"name": "db-pw", "candidate": "y-value-1", "space": sx})["payload"])["result"], "NO-MATCH")
        self.assertEqual(dict(self.gate.execute("VERIFY-SECRET", "owner",
            {"name": "db-pw", "candidate": "y-value-1", "space": sy})["payload"])["result"], "MATCH")

    def test_a_later_seal_in_one_space_does_not_clobber_anothers_baseline(self):
        # the exact defect V6 fixes: under bare-name keying, sy's later seal of "shared" would become the
        # latest-per-name and sx would then verify against y-secret. Under (space, name) it does not.
        sx, sy = self._space("teamx"), self._space("teamy")
        self.gate.execute("SEAL-SECRET", "owner", {"name": "shared", "value": "x-secret", "space": sx})
        self.gate.execute("SEAL-SECRET", "owner", {"name": "shared", "value": "y-secret", "space": sy})  # later, other space
        r = self.gate.execute("VERIFY-SECRET", "owner", {"name": "shared", "candidate": "x-secret", "space": sx})
        self.assertEqual(dict(r["payload"])["result"], "MATCH")             # sx's baseline survived the sy seal

    def test_same_space_rotation_still_supersedes(self):
        sx = self._space("teamx")
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "old", "space": sx})
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "new", "space": sx})   # rotate IN-PLACE
        self.assertEqual(self.views.sealed_secret_hash("db-pw", sx), secret_hash("new"))            # newest-in-space wins
        self.assertEqual(dict(self.gate.execute("VERIFY-SECRET", "owner",
            {"name": "db-pw", "candidate": "old", "space": sx})["payload"])["result"], "NO-MATCH")  # old superseded
        self.assertEqual(dict(self.gate.execute("VERIFY-SECRET", "owner",
            {"name": "db-pw", "candidate": "new", "space": sx})["payload"])["result"], "MATCH")

    def test_one_space_world_is_inert_bare_name_query_equals_mother(self):
        # V6 is INERT under one space: a seal with no space lands in the mother space, and a bare-name
        # query (space defaulting to mother) finds it — identical to the pre-V6 latest-per-name behaviour.
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": SECRET})
        self.assertEqual(self.views.sealed_secret_hash("db-pw"), secret_hash(SECRET))           # bare name -> mother
        self.assertEqual(self.views.sealed_secret_hash("db-pw", MOTHER), secret_hash(SECRET))   # explicit mother, same

    def test_a_secret_sealed_in_a_subspace_is_absent_from_the_mother(self):
        # keying on (space, name): a subspace seal does not answer a mother-space query for the same name
        sx = self._space("teamx")
        self.gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "x-only", "space": sx})
        self.assertEqual(self.views.sealed_secret_hash("db-pw", sx), secret_hash("x-only"))
        self.assertIsNone(self.views.sealed_secret_hash("db-pw"))                # nothing sealed under db-pw in mother
        # and a VERIFY in the mother space records NO-MATCH (you cannot match a secret sealed elsewhere)
        self.assertEqual(dict(self.gate.execute("VERIFY-SECRET", "owner",
            {"name": "db-pw", "candidate": "x-only"})["payload"])["result"], "NO-MATCH")


if __name__ == "__main__":
    unittest.main()
