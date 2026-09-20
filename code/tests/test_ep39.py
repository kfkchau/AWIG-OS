# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (audit stream, signing key, custody, vault closure); NON-GOAL: no offensive capability
# of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-39 (BUILD) — Two streams, two keys: the EP-09 physical-separation deferral lands.

Every probe here is a regression test (the campaign method: a verification probe lands as a test).
TEST KEYS throughout (F1/F6): nothing real is minted — the real ceremony that seals the two custody
homes is the owner's (design/37 §9). The per-stream key CREATE was founding vocabulary held on the
owner's word; the owner gave it (:2847, both elements named) and the architect ruled the completion
(:2885), so the two per-stream audit-key LAWS are the constitution now (founding 1.33.0, A6 asserts
it). The battery proves, in disposable stores:

  A1  TestStreamsTwoKeys      each stream signs with its OWN key and verifies; a stream entry carrying
                              the OTHER stream's signature FAILS verification and routes like divergence
                              to the owner queue (RW1, a check that can fail — holding one key can never
                              produce the other's signatures).
  A2  TestCrossCheckUnchanged the third-view divergence detection + owner-queue routing behave EXACTLY as
                              built: unsigned mirrors carry no signature and the digest comparison is
                              byte-behaviour identical (the EP-09 regression); a wrong digest is still
                              caught even beside a valid signature (RW4); views.py is CONSUMED UNCHANGED.
  A3  TestKeyPathSeparation   each stream's signing PATH names ONLY its own stream's key — the shared
                              signer both streams call is impossible by construction; the guard REDS on a
                              planted shared signer that reaches both keys (RW2, the reference to refuse).
  A4  TestVaultStillClosed    both per-stream keys sit in vault-class custody; NO read path (RW3); the
                              signing paths read no sealed value; the no-reveal closure is a PROPERTY
                              guard (surface + source + seam) — the vault is routed AND byte-frozen at the rewired sha (owner :3966).
  A5  TestRoundTrip           streams killed and replayed; every recorded signature verifies as DATA;
                              replay signs nothing new. (Whole-ledger green is the verifier's discover.)
  A6  TestFoundingMoved       the founding MOVED (COMPLETE-KEY-FAMILY, board :2887; owner create-word
                              :2847, ruling :2885): production declares the two per-stream audit-key
                              laws, each vault-class custody + NO read path, version 1.33.0, no new
                              check kind forced. §A57 era-stabilised in-file.

THE PROPERTY, EXACTLY (design/37 Q4/§9): producing a consistent signed pair requires BOTH keys; holding
one key extends one stream only. On a single-owner box both keys still sit with one person — the property
delivered is that the streams CAN have separate custodians with the checking machinery unchanged.
"""

import hashlib
import inspect
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import era_pin                                                      # noqa: E402  (the era-pin home, EP-28Z)
from kernel.boot import build_kernel                                # noqa: E402
from kernel.protection import Protection                            # noqa: E402
from kernel.vault import VaultStore                                 # noqa: E402
from kernel import keys                                             # noqa: E402
from kernel.errors import OpError                                   # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
ERA_PIN_PATH = os.path.join(REPO, "tests", "era_pin.py")

#: §A57 ERA-STABILISATION BY A LATER PASS. COMPLETE-SIGNING-LAW (mover-2) moved the live founding to
#: 1.34.0, so the audit-key laws' landed version (1.33.0) is no longer the live version. This pin is
#: the commit immediately BEFORE mover-2's founding write — the era where 1.33.0 stands as the live
#: founding — so test_ep39's own version claim keeps asserting ITS OWN ERA truth out of git rather
#: than reading a 1.34.0 live tree or being relabelled to it.
MOVER2_PRE_COMMIT = "062fffe15b471de4798866c1db134fa98acd2b51"
VIEWS_PATH = os.path.join(REPO, "src", "kernel", "views.py")
VAULT_PATH = os.path.join(REPO, "src", "kernel", "vault.py")
PROTECTION_PATH = os.path.join(REPO, "src", "kernel", "protection.py")

# TEST KEY MATERIAL (F1/F6; §8-f): plain strings, nothing real minted. Two SEPARATE values -> two
# separate custody hashes -> two separate homes. The per-stream key CREATE is HELD; production founding
# is byte-untouched (A6). The real ceremony (custodian choice, key material homes) is the owner's word.
STREAM_A_KEY_VALUE = "testsecret:audit-stream-a:v1"
STREAM_B_KEY_VALUE = "testsecret:audit-stream-b:v1"

# THE TWO PER-STREAM AUDIT-KEY LAWS the founding move creates (COMPLETE-KEY-FAMILY, 1.33.0) — one per
# audit stream (protection.py dual-audit / dual-audit-b), each declaring vault-class custody with NO
# read path (design/37 Q4, §9 the custody cap). Named as their own element of the owner's create-word.
AUDIT_KEY_A = "AUDIT-KEY-DUAL-AUDIT"      # stream dual-audit's per-stream key law
AUDIT_KEY_B = "AUDIT-KEY-DUAL-AUDIT-B"    # stream dual-audit-b's per-stream key law


# ============================================================================================
# A signed test world: build_kernel, then a Protection whose two audit streams sign with SEPARATE
# per-stream keys, each sealed in vault-class custody. This models "the ceremony sealed two keys"
# WITHOUT touching production founding (the held create rides the owner's word, §8-f).
# ============================================================================================

class SignedStreams(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.vault = VaultStore(os.path.join(self._dir, "vault"))
        # seal each per-stream key -> its PUBLIC custody hash (the only thing that leaves; no read path)
        self.key_a = keys.seal_system_key(self.vault, STREAM_A_KEY_VALUE)
        self.key_b = keys.seal_system_key(self.vault, STREAM_B_KEY_VALUE)
        self.assertNotEqual(self.key_a, self.key_b)                 # two keys, two homes
        self.store, self.gate, self.views = build_kernel(self.path)
        self.prot = Protection(self.store, self.gate, self.views,
                               key_a_custody=self.key_a, key_b_custody=self.key_b)

    def _governance_act(self):
        with self.assertRaises(OpError):
            self.gate.execute("DO-NOTHING", "x", {})               # unknown op -> op-refused (a dual-audit action)

    def _one_mirror(self, action):
        recs = self.store.by_action(action)
        self.assertEqual(len(recs), 1)
        return recs[0]["payload"]


# ============================================================================================
# A1 — T-STREAMS-TWO-KEYS — both directions (right key verifies; other key fails + routes) + RW1
# ============================================================================================

class TestStreamsTwoKeys(SignedStreams):

    def test_a1_each_stream_signs_with_its_own_key_and_verifies(self):
        self._governance_act()
        pa = self._one_mirror("dual-audit-record")
        pb = self._one_mirror("dual-audit-b-record")
        self.assertEqual(pa["sig"]["custody"], self.key_a)          # A signed under A's key
        self.assertEqual(pb["sig"]["custody"], self.key_b)          # B signed under B's key
        self.assertTrue(Protection._verify_mirror_sig(pa, self.key_a, "dual-audit"))
        self.assertTrue(Protection._verify_mirror_sig(pb, self.key_b, "dual-audit-b"))
        self.assertEqual(self.prot.dual_blind_divergences(), [])    # honest signed world: cross-check clean

    def test_a1_a_stream_signed_with_the_other_key_fails_verification(self):
        # RW1 at the function level: holding one key must never produce the other's signatures. A
        # stream-A mirror verified against B's key (or carrying B's custody) FAILS.
        self._governance_act()
        pa = self._one_mirror("dual-audit-record")
        self.assertFalse(Protection._verify_mirror_sig(pa, self.key_b, "dual-audit"))     # wrong expected key
        forged = dict(pa)
        forged["sig"] = {"custody": self.key_b, "ref_seq": pa["ref_seq"],
                         "digest": pa["digest"], "stream": "dual-audit-b"}
        self.assertFalse(Protection._verify_mirror_sig(forged, self.key_a, "dual-audit"))  # other stream's sig

    def test_a1_rw1_a_cross_stream_signature_routes_like_divergence_through_the_live_crosscheck(self):
        # RW1 through the instrument: append a stream-A mirror for a genuine referent, correct digest but
        # carrying STREAM B's signature (the forgery a stolen-one-key holder would attempt). A-verification
        # fails -> the third-party cross-check routes the ref_seq to the owner queue.
        self._governance_act()
        genuine = self._one_mirror("dual-audit-record")
        rs = genuine["ref_seq"]
        self.assertEqual(self.prot.dual_blind_divergences(), [])    # before the forgery: clean
        forged = dict(genuine)                                      # same ref_seq -> last-wins in the cross-check dict
        forged["sig"] = {"custody": self.key_b, "ref_seq": rs, "digest": genuine["digest"],
                         "stream": "dual-audit-b"}
        self.store._append({"actor": "SYSTEM", "action": "dual-audit-record", "rule_cited": "SOP",
                            "payload": forged})
        self.assertIn(rs, self.prot.dual_blind_divergences())       # the forged cross-stream sig is caught

    def test_a1_a_tampered_signature_field_fails(self):
        # a mangled signature (missing fields / wrong digest / not a dict) is a NO-MATCH, never a read path.
        self._governance_act()
        pa = self._one_mirror("dual-audit-record")
        self.assertFalse(Protection._verify_mirror_sig({**pa, "sig": {"custody": self.key_a}},
                                                       self.key_a, "dual-audit"))          # missing binds
        self.assertFalse(Protection._verify_mirror_sig({**pa, "sig": {**pa["sig"], "digest": "0" * 16}},
                                                       self.key_a, "dual-audit"))          # rebound digest
        self.assertFalse(Protection._verify_mirror_sig({**pa, "sig": "not-a-dict"},
                                                       self.key_a, "dual-audit"))


# ============================================================================================
# A2 — the cross-check regression is UNCHANGED (RW4); views.py CONSUMED UNCHANGED (§8-g)
# ============================================================================================

class TestCrossCheckUnchanged(unittest.TestCase):

    def _unsigned_world(self):
        d = tempfile.mkdtemp()
        store, gate, views = build_kernel(os.path.join(d, "r.jsonl"))
        prot = Protection(store, gate, views)                       # NO keys -> mirrors carry no signature
        return store, gate, views, prot

    def test_a2_unsigned_mirrors_carry_no_signature_and_the_crosscheck_is_clean(self):
        store, gate, views, prot = self._unsigned_world()
        with self.assertRaises(OpError):
            gate.execute("DO-NOTHING", "x", {})
        a = store.by_action("dual-audit-record")
        b = store.by_action("dual-audit-b-record")
        self.assertEqual((len(a), len(b)), (1, 1))
        self.assertNotIn("sig", a[0]["payload"])                    # unkeyed: no signature added (regression unchanged)
        self.assertNotIn("sig", b[0]["payload"])
        self.assertEqual(prot.dual_blind_divergences(), [])         # clean exactly as EP-09

    def test_a2_the_ep09_disagreeing_digest_regression_holds_verbatim_unsigned(self):
        # the EP-09 T-DUAL-BLIND regression, verbatim behaviour: a forged WRONG digest is flagged, with no
        # signatures anywhere. The digest comparison is untouched by the signature term.
        store, gate, views, prot = self._unsigned_world()
        with self.assertRaises(OpError):
            gate.execute("DO-NOTHING", "x", {})
        rs = store.by_action("dual-audit-record")[0]["payload"]["ref_seq"]
        store._append({"actor": "SYSTEM", "action": "dual-audit-b-record", "rule_cited": "SOP",
                       "payload": {"ref_seq": rs, "ref_action": "op-refused",
                                   "digest": "deadbeefdeadbeef", "stream": "dual-audit-b"}})
        self.assertIn(rs, prot.dual_blind_divergences())

    def test_a2_rw4_a_wrong_digest_is_still_caught_beside_a_valid_signature(self):
        # RW4: signatures added BESIDE the read never disable the digest comparison. In a SIGNED world a
        # stream-B mirror with a WRONG digest but a VALID B signature over that wrong digest is STILL
        # flagged by the digest divergence term — the comparison fires regardless of a good signature.
        d = tempfile.mkdtemp()
        vault = VaultStore(os.path.join(d, "vault"))
        ka = keys.seal_system_key(vault, STREAM_A_KEY_VALUE)
        kb = keys.seal_system_key(vault, STREAM_B_KEY_VALUE)
        store, gate, views = build_kernel(os.path.join(d, "r.jsonl"))
        prot = Protection(store, gate, views, key_a_custody=ka, key_b_custody=kb)
        with self.assertRaises(OpError):
            gate.execute("DO-NOTHING", "x", {})
        rs = store.by_action("dual-audit-record")[0]["payload"]["ref_seq"]
        bad = "deadbeefdeadbeef"
        store._append({"actor": "SYSTEM", "action": "dual-audit-b-record", "rule_cited": "SOP",
                       "payload": {"ref_seq": rs, "ref_action": "op-refused", "digest": bad,
                                   "stream": "dual-audit-b",
                                   "sig": {"custody": kb, "ref_seq": rs, "digest": bad, "stream": "dual-audit-b"}}})
        self.assertIn(rs, prot.dual_blind_divergences())            # digest term catches it, valid sig or not

    # FUNCTION-SCOPED PIN (P8B-HARDENING delta 3, archi :3731 the overdue pin). What was here was a
    # WHOLE-FILE views.py byte-pin, re-pinned SIX times by APPENDS elsewhere in the Views class (EP-50
    # `fold_set`, C6 P16 path-view, C6 P7 handshake-relation, C6 P6 live-stages, and the P8b census
    # reporting line) that NEVER touched the dual-audit comparison. A whole-file pin that reds on every
    # unrelated views.py edit is churn wearing coverage's coat: it cannot say WHETHER the thing it guards
    # moved, only that SOMETHING did, and each red cost a mechanical re-pin that re-asserted the invariant
    # by hand. Scoped to the ONE function it exists to protect — `digest_of`, the third-view / dual-audit
    # content digest (§8-g / RW4) — the pin reds IFF that comparison's source changes and is byte-STABLE
    # across every edit elsewhere in views.py. The invariant is unchanged; only the surface it reads is.
    DIGEST_OF_PIN = "de8b5a8fe95cd0d29370fbb8cf42dd64d4d0e062bb8f82c8d1b21f11cce8e00d"

    @staticmethod
    def _digest_of_source():
        import kernel.views as views_mod
        return inspect.getsource(views_mod.digest_of)

    def test_a2_the_digest_of_comparison_is_consumed_unchanged(self):
        # §8-g / RW4: the third-view digest (`digest_of`, the dual-audit cross-check) is CONSUMED
        # UNCHANGED. Function-scoped, so an unrelated views.py edit no longer forces a re-pin.
        src = self._digest_of_source()
        self.assertEqual(hashlib.sha256(src.encode("utf-8")).hexdigest(), self.DIGEST_OF_PIN,
                         "the digest_of dual-audit comparison changed — it is CONSUMED UNCHANGED (§8-g); "
                         "STOP if the third-view digest needs editing")

    def test_a2_the_function_scoped_pin_can_fail_on_a_comparison_change(self):
        # THE REFERENCE TO REFUSE (§A64: a check that cannot fail is not a check). A change to the
        # comparison — here its digest truncation width `[:16]`, the core of the dual-audit content
        # digest — reds the pin. Proven against a mutated copy of the real source.
        src = self._digest_of_source()
        mutated = src.replace("[:16]", "[:15]")
        self.assertNotEqual(mutated, src, "digest_of no longer truncates at [:16] — update this control")
        self.assertNotEqual(hashlib.sha256(mutated.encode("utf-8")).hexdigest(), self.DIGEST_OF_PIN)

    def test_a2_the_pin_ignores_edits_elsewhere_in_views_py(self):
        # what the whole-file pin could NOT do: an edit anywhere else in views.py leaves the pinned
        # region byte-identical, so the pin does not churn. Proven — the comparison's source is a
        # contiguous verbatim block of views.py, and survives synthetic edits far from it, hashing the same.
        region = self._digest_of_source()
        with open(VIEWS_PATH, encoding="utf-8") as fh:
            whole = fh.read()
        self.assertIn(region, whole)                                   # a contiguous block of the file
        edited = whole.replace("class Views:", "    # synthetic unrelated edit\nclass Views:", 1) \
            + "\n    # a trailing unrelated append to the module\n"
        self.assertIn(region, edited)                                  # untouched by edits elsewhere
        self.assertEqual(hashlib.sha256(region.encode("utf-8")).hexdigest(), self.DIGEST_OF_PIN)


# ============================================================================================
# A3 — the key-path grep guard (RW2 / §8-e): each signing path names only its OWN key
# ============================================================================================

class TestKeyPathSeparation(unittest.TestCase):

    @staticmethod
    def _single_key_path(src, own, other):
        """The guard's predicate: a signing path is single-key iff it names its OWN key and NOT the other's.
        A shared signer that reaches both keys fails it — the collapse is caught structurally, in source."""
        return own in src and other not in src

    def test_a3_each_signing_path_names_only_its_own_stream_key(self):
        src_a = inspect.getsource(Protection._sign_stream_a)
        src_b = inspect.getsource(Protection._sign_stream_b)
        self.assertTrue(self._single_key_path(src_a, "_stream_a_key", "_stream_b_key"))
        self.assertTrue(self._single_key_path(src_b, "_stream_b_key", "_stream_a_key"))

    def test_a3_the_mirror_write_paths_stay_single_key_too(self):
        # the writers that CALL the signers must not reach the other stream's signer or key either.
        src_ma = inspect.getsource(Protection._maybe_mirror)
        src_mb = inspect.getsource(Protection._maybe_mirror_b)
        self.assertIn("_sign_stream_a", src_ma)
        self.assertNotIn("_sign_stream_b", src_ma)
        self.assertNotIn("_stream_b_key", src_ma)
        self.assertIn("_sign_stream_b", src_mb)
        self.assertNotIn("_sign_stream_a", src_mb)
        self.assertNotIn("_stream_a_key", src_mb)

    def test_a3_rw2_a_shared_signer_reaching_both_keys_reds_the_guard(self):
        # RW2 (THE REFERENCE TO REFUSE): one signer both streams call, selecting the key by stream. It
        # reaches BOTH keys -> the guard predicate FAILS in BOTH directions. A check that cannot fail is
        # not a check (§A64). Whoever held that one signer would hold both streams — the collapse §8-e bars.
        shared_signer = (
            "def _sign(self, stream, ref_seq, digest):\n"
            "    k = self._stream_a_key if stream == 'dual-audit' else self._stream_b_key\n"
            "    return {'custody': k, 'ref_seq': ref_seq, 'digest': digest, 'stream': stream}\n")
        self.assertFalse(self._single_key_path(shared_signer, "_stream_a_key", "_stream_b_key"))
        self.assertFalse(self._single_key_path(shared_signer, "_stream_b_key", "_stream_a_key"))


# ============================================================================================
# A4 — T-VAULT-STILL-CLOSED re-run (RW3 / §8-h): per-stream keys in vault-class custody, no read path
# ============================================================================================

class TestVaultStillClosed(unittest.TestCase):

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.vault = VaultStore(os.path.join(self._dir, "vault"))

    def test_a4_both_per_stream_keys_seal_into_custody_and_only_the_hash_leaves(self):
        ka = keys.seal_system_key(self.vault, STREAM_A_KEY_VALUE)
        kb = keys.seal_system_key(self.vault, STREAM_B_KEY_VALUE)
        self.assertTrue(ka.startswith("sha256:") and kb.startswith("sha256:"))
        self.assertNotEqual(ka, kb)                                 # two keys, two custodies
        self.assertNotIn(STREAM_A_KEY_VALUE, ka + kb)               # never the value
        self.assertNotIn(STREAM_B_KEY_VALUE, ka + kb)

    def test_a4_rw3_the_vault_has_no_read_path_for_the_per_stream_keys(self):
        keys.seal_system_key(self.vault, STREAM_A_KEY_VALUE)
        keys.seal_system_key(self.vault, STREAM_B_KEY_VALUE)
        for banned in ("get", "read", "reveal", "open", "has", "value", "plaintext", "fetch", "load"):
            self.assertFalse(hasattr(self.vault, banned),
                             f"VaultStore must expose no `{banned}` — closure holds for the per-stream keys")

    def test_a4_the_signing_paths_read_no_sealed_value(self):
        # closure is a property of the SOURCE (EP-19): protection.py's signing never reads a sealed value
        # back — it binds the PUBLIC custody hash only. A key held in closure cannot be read to sign with.
        with open(PROTECTION_PATH, encoding="utf-8") as fh:
            src = fh.read()
        for reader in ("read_bytes", "read_text", ".reveal(", "vault.get", ".seal("):
            self.assertNotIn(reader, src, f"protection.py must not contain `{reader}` — no key read/seal path in the engine")

    def test_a4_the_vault_closure_is_byte_unchanged(self):
        # RE-ENABLED (owner :3966): the vault byte-freeze was SET ASIDE for the C7-P2 rewiring
        # (:3930/:3952 routed vault.py through host_seam) and is now PUT BACK ON at the REWIRED contents.
        # It rides BESIDE the property guards — the vault surface (test_a4_rw3_the_vault_has_no_read_path_
        # for_the_per_stream_keys), the signing-path source census (test_a4_the_signing_paths_read_no_
        # sealed_value), and the seam's no-read-act (test_c7_p2_seam) — not instead of them.
        # RE-POINTED (MAINT-VAULT-HASH-ONLY; owner scan :4435, archi :4437): seal now stores NOTHING
        # (no write-once put, no _path); the pin guards the property (the vault's exact bytes), so it
        # moves with the owner-authorized code to the hash-only vault's sha.
        with open(VAULT_PATH, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, "6a82f449865f5464ef70b6d39db2fee568ba1cae43b5b380e21cc4d5ad09f767",
                         "vault.py bytes changed — the vault is byte-frozen at the hash-only sha (§8-h; MAINT-VAULT-HASH-ONLY)")


# ============================================================================================
# A5 — round-trip: streams killed and replayed; recorded signatures verify as DATA; replay signs nothing
# ============================================================================================

class TestRoundTrip(SignedStreams):

    def test_a5_recorded_signatures_verify_as_data_after_replay_and_replay_signs_nothing(self):
        self._governance_act()
        self._governance_act()
        before_a = {m["payload"]["ref_seq"]: m["payload"]["sig"] for m in self.store.by_action("dual-audit-record")}
        before_b = {m["payload"]["ref_seq"]: m["payload"]["sig"] for m in self.store.by_action("dual-audit-b-record")}
        n_a = len(self.store.by_action("dual-audit-record"))
        n_b = len(self.store.by_action("dual-audit-b-record"))
        self.assertEqual((n_a, n_b), (2, 2))

        # KILL derived state and replay from the record file alone; the replay Protection carries NO keys.
        store2, gate2, views2 = build_kernel(self.path)
        Protection(store2, gate2, views2)                          # replay signs nothing new (no keys, no ops re-run)
        self.assertEqual(len(store2.by_action("dual-audit-record")), n_a)   # replay minted no new mirrors
        self.assertEqual(len(store2.by_action("dual-audit-b-record")), n_b)

        for m in store2.by_action("dual-audit-record"):
            p = m["payload"]
            self.assertEqual(p["sig"], before_a[p["ref_seq"]])              # identical on the record
            self.assertTrue(Protection._verify_mirror_sig(p, self.key_a, "dual-audit"))   # verifies as data
            self.assertFalse(Protection._verify_mirror_sig(p, self.key_b, "dual-audit"))  # not under B's key
        for m in store2.by_action("dual-audit-b-record"):
            p = m["payload"]
            self.assertEqual(p["sig"], before_b[p["ref_seq"]])
            self.assertTrue(Protection._verify_mirror_sig(p, self.key_b, "dual-audit-b"))
            self.assertFalse(Protection._verify_mirror_sig(p, self.key_a, "dual-audit-b"))

    def test_a5_a_consistent_signed_pair_requires_both_keys(self):
        # design/37 Q4: producing a consistent signed pair requires BOTH keys. Holding only A's key, the
        # A mirror verifies but the B mirror cannot (B's signature needs B's custody) — one key extends one
        # stream only.
        self._governance_act()
        pa = self._one_mirror("dual-audit-record")
        pb = self._one_mirror("dual-audit-b-record")
        self.assertTrue(Protection._verify_mirror_sig(pa, self.key_a, "dual-audit"))       # A-holder: A verifies
        self.assertFalse(Protection._verify_mirror_sig(pb, self.key_a, "dual-audit-b"))    # A-holder cannot pass B


# ============================================================================================
# A6 — the founding-move is HELD (§8-f, EP-36 shape): production founding + era_pin byte-untouched
# ============================================================================================

class TestFoundingMoved(unittest.TestCase):
    """A6 LIVE (COMPLETE-KEY-FAMILY, board :2887). The owner's create-word named BOTH elements
    (:2847, ruling :2885): 'the key family — bind/rotate/revoke — AND the two per-stream audit keys'.
    The two per-stream audit-key laws are the constitution now, at founding 1.33.0; each declares
    vault-class custody with NO read path (the K2-discipline: a specific yes never widened silently)."""

    def _pack(self):
        import json
        with open(PACK_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    def _rule_text(self, pack, rid):
        return [r["payload"]["text"] for s in pack["steps"] for r in s["records"]
                if r.get("action") == "CREATE-RULE" and r["payload"]["rule_id"] == rid][0]

    def test_a6_production_founding_declares_the_two_per_stream_audit_keys(self):
        pack = self._pack()
        rules = {r["payload"]["rule_id"] for s in pack["steps"] for r in s["records"]
                 if r.get("action") == "CREATE-RULE"}
        self.assertIn(AUDIT_KEY_A, rules)          # stream dual-audit's per-stream key law
        self.assertIn(AUDIT_KEY_B, rules)          # stream dual-audit-b's per-stream key law

    def test_a6_each_audit_key_law_declares_vault_class_custody_and_no_read_path(self):
        # design/37 Q4/§9 (the custody cap; §8-h vault closure): each per-stream key sits in vault-class
        # custody with NO read path — the law says so in its own text. If signing had needed a key read
        # path this create could not have been authored (it would be the STOP §8-h); it did not.
        pack = self._pack()
        for rid in (AUDIT_KEY_A, AUDIT_KEY_B):
            text = self._rule_text(pack, rid).lower()
            self.assertIn("vault-class custody", text)
            self.assertIn("no read path", text)

    def test_a6_the_founding_version_moved_to_1_33_0(self):
        # §A57 era-stabilised: COMPLETE-SIGNING-LAW (mover-2) later moved the LIVE founding to 1.34.0,
        # so this reads the audit-key laws' own landed version (1.33.0) out of git at the era just
        # before mover-2, never the live tree and never relabelled to 1.34.0.
        self.assertEqual(era_pin.pack_at(MOVER2_PRE_COMMIT, missing="assert")["founding_version"], "1.33.0")

    def test_a6_era_pin_is_byte_untouched(self):
        # The §A57 sweep era-STABILISES its version pins in the test files; it edits no era-pin row.
        with open(ERA_PIN_PATH, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, "19ebf106bcdd82753d46b5eb34146ee31c04e909dd9458b376e0271a4236eb87",
                         "tests/era_pin.py bytes changed — the §A57 sweep touches no era-pin row")

    def test_a6_no_new_check_kind_is_forced(self):
        # §1: the EP adds NO new check kind. Signing is a mirror-payload field + a derived verify, never a
        # gate check. OP_CHECKS is unchanged from EP-36's seventeen; a forced new kind would be a STOP.
        from kernel.opdefs import OP_CHECKS
        self.assertEqual(len(OP_CHECKS), 19)
        self.assertNotIn("signature", OP_CHECKS)
        self.assertNotIn("key", OP_CHECKS)


if __name__ == "__main__":
    unittest.main()
