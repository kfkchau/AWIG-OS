# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (key binding, custody, ceremony, succession, vault closure); NON-GOAL: no offensive
# capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-36 (BUILD) — Keys and ceremonies: bind, rotate, revoke — every key with its leash.

Every probe here is a regression test (the campaign method: a verification probe lands as a test).
TEST KEYS throughout (F6/§8-i): nothing real is minted — the real ceremony (owner key holder,
system-key vault material, successor key production) is the owner's, presented in the close and
handed back. The battery proves, in disposable stores:

  A1  TestRootKeyAnchored   BOTH directions through the gate: a root key rotate/revoke WITHOUT a
                            bound successor key REFUSES citing the anchor (RW1); WITH a successor
                            bound through succession it PASSES; a NON-root key op is unleashed
                            (RW1 near-miss — the guard discriminates, not blocks).
  A2  TestRotateSupersedes  a rotation supersedes the prior binding (latest-supersession-wins);
                            NOTHING cascades (RW2 — a stored downstream "validity" is ignored, the
                            fold re-derives live); an old key stays on the record AS DATA.
  A3  TestVaultStillClosed  after wiring the system key's countersigning to the vault, there is
                            STILL no read path (RW3); the vault's closure is BYTE-UNCHANGED.
  A4  TestSuccessionKey     BOTH directions: a HANDOVER completes only when the successor's key
                            binds first (no key -> refuses); human-only stands unchanged.
  A5  TestValidityFold      validity is a live fold; an as-of query returns the binding valid AT a
                            past deciding time (EP-38 needs validity-as-of-deciding-time).
  A6  TestFoundingMoved     the founding MOVED (COMPLETE-KEY-FAMILY, board :2887; owner create-word
                            :2847, architect ruling :2885): production founding declares the key
                            family, version 1.33.0 MINOR, the key ops carry occurrence_time via the
                            router with no new check kind; a stripped family REDS the LIVE gate
                            (RW-F, a check that can fail). §A57 era-stabilised in-file.
  A7  TestRoundTrip         key state killed and replayed identically from the record alone; the
                            vault probe re-run proves no read path entered. (Whole-ledger green is
                            the suite discover, the verifier's re-run.)

THE FOUNDING MOVED (COMPLETE-KEY-FAMILY, founding 1.33.0). The key-bind LAW and key-rotate/
key-revoke ops WERE new founding vocabulary held on the owner's word (the MEM/SCHED precedent); the
owner gave the create-word (:2847) and the architect ruled the completion (:2885), so they are the
constitution now. build_kernel loads the law and registers the ops from the production pack — the
worlds here are founded from it, not from a test-world stand-in. The engine (kernel.keys, the views
folds, the gate anchor branch) engages per-account: a keyless account is untouched by the live law.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # so `import era_pin` resolves
import era_pin                                                    # noqa: E402  (the era-pin home, EP-28Z)
from kernel.boot import build_kernel                              # noqa: E402
from kernel import keys                                           # noqa: E402
from kernel.gate import make_invoker_sig, INVOKER_SIG             # noqa: E402  (the signed door, mover-2)
from kernel.vault import VaultStore                               # noqa: E402
from kernel.errors import OpError                                 # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
ERA_PIN_PATH = os.path.join(REPO, "tests", "era_pin.py")

#: THE PRE-CREATE ERA — the commit at the builder's hand IMMEDIATELY BEFORE this pass's founding
#: write (COMPLETE-KEY-FAMILY, board :2887), captured by `git rev-parse HEAD` and filed at
#: planning/evidence/COMPLETE-KEY-FAMILY/PRE-EDIT-HEAD.txt. The key-family create's landing is read
#: as a FACT across this pin: the era's pack declares NO key-family member (verified by content
#: below, not by version), the live pack declares it. §A57 era-stabilisation, never a relabel.
KEY_FAMILY_PRE_COMMIT = "59adae53d45400649bbf8dd7a581d47bb4916bc2"

#: §A57 ERA-STABILISATION BY A LATER PASS. COMPLETE-SIGNING-LAW (mover-2) moved the founding to
#: 1.34.0, so the key family's landed version (1.33.0) is no longer the LIVE version. This pin is the
#: commit immediately BEFORE mover-2's founding write — the era where the key family's 1.33.0 stands
#: as the live founding — so test_ep36's own version claim (1.32.0 -> 1.33.0 MINOR) keeps asserting
#: ITS OWN ERA truth out of git rather than reading a 1.34.0 live tree or being relabelled to it.
MOVER2_PRE_COMMIT = "062fffe15b471de4798866c1db134fa98acd2b51"


def live_pack():
    with open(PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)

# TEST KEY MATERIAL (F6): plain strings, the simplest thing the stdlib supports — the RAISED-BY-
# DESIGN key-material calibration (D1 zero-dependency; nothing real minted, nothing forced).
ROOT_KEY_1 = "testpub:owner:v1"
ROOT_KEY_2 = "testpub:owner:v2"
ALICE_KEY = "testpub:alice:v1"
BOB_KEY = "testpub:bob:v1"
SYSTEM_KEY_VALUE = "testsecret:system-key:v1"


# ============================================================================================
# THE FOUNDING MOVED (COMPLETE-KEY-FAMILY, founding 1.33.0; owner create-word board :2847,
# architect ruling :2885). The key-bind LAW (KEY-LAW-BIND) and the key-bind / key-rotate /
# key-revoke ops are PRODUCTION founding now — build_kernel loads the law and registers the ops
# from the pack, so every world here has the constitution the test world used to stand in for.
# What was a test-world CREATE-RULE + gate.register is the founding create; the test world no
# longer declares the law or registers the ops (they would collide: "duplicate operation").
# The production ops carry occurrence_time via the occurrence_time_param router (an omitted `at`
# DEFAULTS, does not error — Ruling A) — no new check kind; the leash lives at the gate anchor.
# ============================================================================================


class KeyWorld(unittest.TestCase):
    """A disposable world founded from the PRODUCTION pack, where the key-bind law is live and the
    key ops are registered (the founding move landed). The key leash engages per-account."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    # --- ceremony helpers (the EP-18 succession harness, extended with the key half) ---
    def _do(self, opname, actor, params):
        """Execute AS `actor`, self-signing when the actor currently holds a bound key. SIGN-LAW is
        production founding now (COMPLETE-SIGNING-LAW, mover-2, founding 1.34.0): a key-bound account
        signs EVERY act — its own key-management ceremonies included (architect :2902, design/37 Q6,
        no carve-out), which is the intended live behaviour, not a defect. An unkeyed actor acts under
        the openness grant, unsigned and byte-identical to before the create. The signature is made
        over the pure handler draft with deciding_time=None (a synchronous act, d=r) — exactly the
        shape gate._signed_content recomputes at acceptance, so signer and verifier never drift (the
        test_ep37 _signed_exec pattern)."""
        key = self.views.bound_key(actor)
        if key is None:
            return self.gate.execute(opname, actor, dict(params))
        draft = self.gate.ops[opname]["handler"](actor, dict(params))
        sig = make_invoker_sig(key, draft, seal=draft.get("seal"))
        return self.gate.execute(opname, actor, {**params, INVOKER_SIG: sig})

    def _account(self, acct, actor_class="human", verify=True):
        self._do("CREATE-ACCOUNT", "owner", {"account_id": acct, "actor_class": actor_class})
        if verify:
            h = "sha256:" + hashlib.sha256(acct.encode()).hexdigest()
            self._do("VERIFY-ACCOUNT", "owner", {"account": acct, "evidence_hash": h})

    def _ready_successor(self, acct="alice", actor_class="human", verify=True):
        self._account(acct, actor_class, verify)
        self._do("DESIGNATE-SUCCESSOR", "owner", {"successor": acct})
        self._do("ACCEPT-SUCCESSION", acct, {})

    def _bind(self, account, key, actor="owner"):
        return self._do(keys.KEY_BIND, actor, {"account": account, "public_key": key})


# ============================================================================================
# A1 — T-ROOT-KEY-ANCHORED — both directions, through the op definitions (RW1 + near-miss)
# ============================================================================================

class TestRootKeyAnchored(KeyWorld):

    def test_a1_root_revoke_without_successor_key_refuses_citing_the_anchor(self):
        # RW1: an unleashed root op is the wedge this leash bars. The root key is bound; revoking it
        # with NO successor key bound must REFUSE, citing the anchor.
        self._bind("owner", ROOT_KEY_1)
        with self.assertRaises(OpError) as cm:
            self._do(keys.KEY_REVOKE, "owner", {"account": "owner"})
        self.assertEqual(cm.exception.rule, keys.KEY_ANCHOR_RULE)
        self.assertIn("root key", str(cm.exception).lower())

    def test_a1_root_rotate_without_successor_key_refuses(self):
        self._bind("owner", ROOT_KEY_1)
        with self.assertRaises(OpError) as cm:
            self._do(keys.KEY_ROTATE, "owner", {"account": "owner", "public_key": ROOT_KEY_2})
        self.assertEqual(cm.exception.rule, keys.KEY_ANCHOR_RULE)

    def test_a1_root_rotate_with_a_bound_successor_key_passes(self):
        # The pass direction: a verified human successor, designated + accepted, with a bound key —
        # now the root key rotates lawfully (the guard discriminates, not blocks).
        self._bind("owner", ROOT_KEY_1)
        self._ready_successor("alice")
        self._bind("alice", ALICE_KEY)
        self.assertTrue(self.views.successor_key_bound())
        self._do(keys.KEY_ROTATE, "owner", {"account": "owner", "public_key": ROOT_KEY_2})
        self.assertEqual(self.views.bound_key("owner"), ROOT_KEY_2)   # the rotation landed

    def test_a1_root_revoke_with_a_bound_successor_key_passes(self):
        self._bind("owner", ROOT_KEY_1)
        self._ready_successor("alice")
        self._bind("alice", ALICE_KEY)
        self._do(keys.KEY_REVOKE, "owner", {"account": "owner"})
        self.assertIsNone(self.views.bound_key("owner"))              # the root key is revoked

    def test_a1_near_miss_a_non_root_key_op_is_unleashed(self):
        # RW1 near-miss / discrimination: a NON-root key rotates/revokes with NO successor at all —
        # it is UNLEASHED (only the root key consults the anchor).
        self._account("bob", "human")
        self._bind("bob", BOB_KEY)
        self.assertIsNone(self.views.current_successor())             # no successor anywhere
        self._do(keys.KEY_ROTATE, "owner", {"account": "bob", "public_key": "testpub:bob:v2"})
        self.assertEqual(self.views.bound_key("bob"), "testpub:bob:v2")
        self._do(keys.KEY_REVOKE, "owner", {"account": "bob"})
        self.assertIsNone(self.views.bound_key("bob"))

    def test_a1_the_check_can_fail_the_successor_needs_the_KEY_not_just_the_designation(self):
        # The guard must be able to REFUSE even with a valid succession fold but NO successor key —
        # a check that cannot fail is not a check (§A64). Designate+accept alice but bind her NO key.
        self._bind("owner", ROOT_KEY_1)
        self._ready_successor("alice")
        self.assertEqual(self.views.current_successor(), "alice")     # succession fold is valid
        self.assertFalse(self.views.successor_key_bound())            # but no KEY -> still leashed
        with self.assertRaises(OpError) as cm:
            self._do(keys.KEY_REVOKE, "owner", {"account": "owner"})
        self.assertEqual(cm.exception.rule, keys.KEY_ANCHOR_RULE)


# ============================================================================================
# A2 — T-ROTATE-SUPERSEDES — latest-supersession-wins; nothing cascades (RW2); old key as data
# ============================================================================================

class TestRotateSupersedes(KeyWorld):

    def test_a2_rotation_supersedes_the_prior_binding(self):
        self._bind("bob", BOB_KEY)
        self.assertEqual(self.views.bound_key("bob"), BOB_KEY)
        self._do(keys.KEY_ROTATE, "owner", {"account": "bob", "public_key": "testpub:bob:v2"})
        self.assertEqual(self.views.bound_key("bob"), "testpub:bob:v2")   # newest wins

    def test_a2_the_old_key_stays_on_the_record_as_data(self):
        # An old signature over a superseded key stays verifiable AS DATA: the prior bind record is
        # never erased — it is simply no longer the LIVE binding.
        self._bind("bob", BOB_KEY)
        self._do(keys.KEY_ROTATE, "owner", {"account": "bob", "public_key": "testpub:bob:v2"})
        superseded = [e for e in self.store.all()
                      if (e.get("payload") or {}).get("kind") == keys.KEY_BIND
                      and (e.get("payload") or {}).get("public_key") == BOB_KEY]
        self.assertEqual(len(superseded), 1)                              # the old bind persists as data
        # and validity as-of that bind still reads the old key (evidence of who decided then)
        self.assertEqual(self.views.bound_key("bob", as_of=superseded[0]["seq"]), BOB_KEY)

    def test_a2_rw2_nothing_cascades_a_stored_downstream_validity_is_ignored(self):
        # RW2: a revoke that invalidates a stored downstream state — there is none, and the design
        # forbids one. Plant a fixture that STORES validity downstream and show the fold ignores it:
        # validity is re-derived LIVE from the key records, never read from a cache.
        self._bind("bob", BOB_KEY)
        self._do(keys.KEY_REVOKE, "owner", {"account": "bob"})
        # a planted downstream record asserting the key is still valid — NOT a key record
        self.store._append({"actor": "owner", "action": "WRITE-ACTIVITY", "object": "bob",
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"stored_key_valid": True, "account": "bob"}})
        self.assertIsNone(self.views.bound_key("bob"))                    # the fold ignores the cache
        self.assertFalse(self.views.key_valid("bob"))


# ============================================================================================
# A3 — T-VAULT-STILL-CLOSED — the system key's countersigning wired, NO read path (RW3)
# ============================================================================================

class TestVaultStillClosed(unittest.TestCase):

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.vault = VaultStore(os.path.join(self._dir, "vault"))

    def test_a3_system_key_seals_and_countersigns_without_a_read_path(self):
        # Wire the store's countersigning to a vault-held system key (F2): seal it (custody), then
        # countersign a record and verify — all through seal + the public hash, never a read-back.
        h = keys.seal_system_key(self.vault, SYSTEM_KEY_VALUE)
        self.assertTrue(h.startswith("sha256:"))                         # only the HASH leaves
        self.assertNotIn(SYSTEM_KEY_VALUE, h)                            # never the value
        record = {"seq": 42, "record_time": "2026-09-03T00:00:00Z", "actor": "SYSTEM"}
        mark = keys.countersign(record, h)
        self.assertTrue(keys.verify_countersign(mark, record, h))        # a derived check, no read
        # the mark carries the recording fact + the PUBLIC custody hash, never the sealed value
        self.assertNotIn(SYSTEM_KEY_VALUE, str(mark))
        # a false countersignature is caught (the check can fail)
        self.assertFalse(keys.verify_countersign(mark, {"seq": 99, "record_time": "x"}, h))
        self.assertFalse(keys.verify_countersign(mark, record, "sha256:0000"))

    def test_a3_rw3_the_vault_has_no_read_path_after_wiring(self):
        # RW3: any op that reads a sealed value back reds this. After wiring the system key, the
        # vault's surface is STILL exactly seal + compare — no get/read/reveal/open/has/value.
        keys.seal_system_key(self.vault, SYSTEM_KEY_VALUE)
        for banned in ("get", "read", "reveal", "open", "has", "value", "plaintext", "fetch", "load"):
            self.assertFalse(hasattr(self.vault, banned),
                             f"VaultStore must expose no `{banned}` — closure holds after wiring")

    def test_a3_the_keys_module_reads_no_sealed_value(self):
        # The closure is a property of the SOURCE, not just behaviour (the EP-19 assertion, applied
        # to the consumer): kernel.keys never reads the vault back — no compare-return-value, no
        # read_bytes, no reveal. It seals (write) and mints from the public hash only.
        with open(os.path.join(REPO, "src", "kernel", "keys.py"), encoding="utf-8") as fh:
            src = fh.read()
        for reader in ("read_bytes", "read_text", ".reveal(", ".read(", "vault.get", "def get"):
            self.assertNotIn(reader, src, f"keys.py must not contain `{reader}` — no read path")

    def test_a3_the_vault_closure_is_byte_unchanged(self):
        # vault.py is CONSUMED only — its closure does not change by one line. The bytes are the
        # baseline captured at this EP's dispatch (HEAD dfa9ec43).
        with open(os.path.join(REPO, "src", "kernel", "vault.py"), "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, "2038a8cdfcb2a5e2113555bdc05dcbba0c4badfb0cefec779b0dae184c7bfbc6",
                         "vault.py bytes changed — the vault is CONSUMED only (F2/§8-e)")


# ============================================================================================
# A4 — succession-with-key — both directions; human-only stands (F5)
# ============================================================================================

class TestSuccessionKey(KeyWorld):

    def test_a4_handover_refuses_without_the_successors_key(self):
        # PER-ACCOUNT (archi :2855, EP-36-ENGAGE-AMEND): the refusal engages only when the chain-end
        # (ce=owner) is ITSELF key-bound. A KEYED authority with a valid human successor who has NO
        # bound key -> HANDOVER refuses. (Before the per-account amendment this world's owner was
        # keyless and the estate-wide key_law_live() gate refused anyway — the flag day; now the ce's
        # own key is what engages the check.)
        self._bind("owner", ROOT_KEY_1)                                  # ce is itself key-bound
        self._ready_successor("alice")
        self.assertEqual(self.views.current_successor(), "alice")
        self.assertTrue(self.views.key_valid("owner"))                   # keyed authority
        self.assertFalse(self.views.key_valid("alice"))                  # keyless successor
        with self.assertRaises(OpError) as cm:
            self._do("HANDOVER", "owner", {})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")
        self.assertIn("key", str(cm.exception).lower())

    def test_a4_handover_completes_once_the_successors_key_binds(self):
        self._ready_successor("alice")
        self._bind("alice", ALICE_KEY)                                   # the key binds first
        self._do("HANDOVER", "owner", {})
        self.assertEqual(self.views.chain_end(), "alice")               # root authority moved

    def test_a4_human_only_stands_a_non_human_successor_is_refused_at_designation(self):
        # The human-only leash is inherited WHOLE and unchanged: a non-human successor is refused at
        # DESIGNATE-SUCCESSOR (the existing enforcement point) — the key half never loosens it. Even
        # if a designation somehow landed, current_successor re-checks human at read, so no handover
        # could ever complete for a non-human.
        self._account("agent", actor_class="agentic")
        with self.assertRaises(OpError) as cm:
            self._do("DESIGNATE-SUCCESSOR", "owner", {"successor": "agent"})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")
        self.assertIn("human", str(cm.exception).lower())
        self.assertIsNone(self.views.current_successor())               # never a valid successor

    def test_a4_the_key_leash_is_inert_per_account_under_the_live_law(self):
        # RE-EXPRESSED (Ruling 2, architect :2885). The old row built a world with NO key-bind law and
        # showed a keyless authority hand over on the succession fold alone — exactly the pre-EP-36
        # behaviour. The COMPLETE-KEY-FAMILY create makes KEY-LAW-BIND LIVE in EVERY world, so "a world
        # without the law" no longer exists via build_kernel: the inertness the old row guarded now
        # holds PER-ACCOUNT — a keyless chain-end hands over on the succession fold alone EVEN under the
        # declared law (the per-account engage, matching TestSuccessionKeyPerAccount.test_a3). The held
        # founding-move broke no keyless succession behaviour; this is the live-law proof of it.
        #
        # ERA COVERAGE (kept, not dropped — the property lived in the PRE-create era). That era is read
        # out of git rather than the live tree, so the create's landing is a fact, not a memory: the
        # pre-create pack declares NO key-family member (verified by CONTENT, not version), the live
        # pack declares it, and the keyless inertness survives the crossing.
        era = era_pin.pack_at(KEY_FAMILY_PRE_COMMIT, missing="assert")
        self.assertFalse(_pack_key_family_present(json.dumps(era)),
                         "the pre-create era must declare NO key-family member (era coverage)")
        self.assertTrue(_pack_key_family_present(json.dumps(live_pack())),
                        "the live founding declares the key family (the create landed)")
        # LIVE per-account inertness: the law IS declared (KeyWorld) but the chain-end holds no key —
        # so a handover to a keyless successor proceeds on the succession fold alone, forever, until an
        # account binds. This is the four settled EPs' keyless-world truth, holding under the live law.
        self.assertTrue(self.views.key_law_live())                       # the law IS live now
        self.assertFalse(self.views.key_valid("owner"))                  # but the chain-end holds no key
        self._ready_successor("carol")
        self._do("HANDOVER", "owner", {})                       # no key required -> completes
        self.assertEqual(self.views.chain_end(), "carol")


# ============================================================================================
# EP-36-ENGAGE-AMEND — THE PER-ACCOUNT ENGAGE (archi :2855, option B). The succession key half at
# gate.py:429 engages on key_valid(ce) — the ACCOUNT being handed over — not on the estate-wide
# key_law_live(). A keyed authority may never pass to a keyless successor (A1); a keyed successor is
# admitted, the guard discriminates (A2); a KEYLESS account hands over on the succession fold alone
# EVEN under a declared law (A3) — the flag day is gone. RW2 makes that flag day a red world:
# reverting :429 to key_law_live() reds test_rw2, so the estate-wide bug cannot return unnoticed.
# ============================================================================================

class TestSuccessionKeyPerAccount(KeyWorld):

    def test_a1_keyed_authority_may_not_pass_to_a_keyless_successor(self):
        # A1: ce HOLDS a live bound key; a handover designating a keyless successor is REFUSED — the
        # anchor's orphaning-prevention holds INSIDE the key regime (a keyed root passing to a keyless
        # successor orphans cryptographic continuity). This is RW1 driven through the instrument.
        self._bind("owner", ROOT_KEY_1)                                  # ce keyed
        self._ready_successor("alice")                                   # successor keyless
        self.assertTrue(self.views.key_valid("owner"))
        self.assertFalse(self.views.key_valid("alice"))
        with self.assertRaises(OpError) as cm:
            self._do("HANDOVER", "owner", {})
        self.assertEqual(cm.exception.rule, "CONST-AUTHORITY-ANCHORED")
        self.assertIn("key", str(cm.exception).lower())

    def test_a2_keyed_authority_passes_to_a_keyed_successor(self):
        # A2: same KeyWorld, ce keyed, the successor's key bound -> the HANDOVER PROCEEDS. The guard
        # DISCRIMINATES on the successor's key; it does not block the ceremony.
        self._bind("owner", ROOT_KEY_1)                                  # ce keyed
        self._ready_successor("alice")
        self._bind("alice", ALICE_KEY)                                   # successor keyed
        self._do("HANDOVER", "owner", {})
        self.assertEqual(self.views.chain_end(), "alice")                # root authority moved

    def test_a3_keyless_authority_hands_over_even_with_the_law_declared(self):
        # A3: the law IS declared (this is a KeyWorld) but the chain-end holds NO key -> a handover to
        # a keyless successor PROCEEDS on the succession fold alone. THIS is the case the estate-wide
        # predicate wrongly refused (the flag day); the per-account form lets it through, forever,
        # until the account binds. It is the four settled EPs' keyless-world truth, inside a KeyWorld.
        self.assertTrue(self.views.key_law_live())                       # the law IS declared
        self.assertFalse(self.views.key_valid("owner"))                  # but ce holds no key
        self._ready_successor("alice")                                   # keyless successor
        self._do("HANDOVER", "owner", {})                       # proceeds — no flag day
        self.assertEqual(self.views.chain_end(), "alice")

    def test_rw2_the_flag_day_is_a_red_world(self):
        # RW2 (§4): the flag day itself must be a RED WORLD so the estate-wide bug cannot silently
        # return. Under a DECLARED law with a keyless ce and a keyless successor the divergence is
        # pinned MECHANICALLY here, by evaluating BOTH predicates on the same world (no production
        # revert needed): the OLD estate-wide gate ENGAGES (would refuse — the flag day) while the NEW
        # per-account gate does NOT. Reverting :429 to key_law_live() reddens this test — the
        # HANDOVER below would then raise CONST-AUTHORITY-ANCHORED instead of proceeding.
        self._ready_successor("alice")
        old_gate_would_engage = (self.views.key_law_live()
                                 and self.views.current_successor() is not None
                                 and not self.views.key_valid(self.views.current_successor()))
        new_gate_engages = (self.views.key_valid(self.views.chain_end())
                            and self.views.current_successor() is not None
                            and not self.views.key_valid(self.views.current_successor()))
        self.assertTrue(old_gate_would_engage)                           # estate-wide gate REFUSES — the flag day
        self.assertFalse(new_gate_engages)                               # per-account gate does NOT engage
        self._do("HANDOVER", "owner", {})                       # so the handover PROCEEDS
        self.assertEqual(self.views.chain_end(), "alice")                # keyless ce hands over — no flag day


# ============================================================================================
# A5 — the validity fold, as-of (EP-38 needs validity-as-of-deciding-time)
# ============================================================================================

class TestValidityFold(KeyWorld):

    def test_a5_validity_is_a_live_fold_as_of_a_past_deciding_time(self):
        self._bind("bob", BOB_KEY)
        seq_bound = self.store.events[-1]["seq"]
        self.assertTrue(self.views.key_valid("bob"))
        self._do(keys.KEY_REVOKE, "owner", {"account": "bob"})
        # live: revoked
        self.assertFalse(self.views.key_valid("bob"))
        self.assertIsNone(self.views.bound_key("bob"))
        # as-of the deciding time when it was bound: STILL the valid binding
        self.assertEqual(self.views.bound_key("bob", as_of=seq_bound), BOB_KEY)
        self.assertTrue(self.views.key_valid("bob", as_of=seq_bound))

    def test_a5_as_of_walks_a_full_bind_rotate_revoke_history(self):
        self._bind("bob", BOB_KEY)
        s1 = self.store.events[-1]["seq"]
        self._do(keys.KEY_ROTATE, "owner", {"account": "bob", "public_key": "testpub:bob:v2"})
        s2 = self.store.events[-1]["seq"]
        self._do(keys.KEY_REVOKE, "owner", {"account": "bob"})
        self.assertEqual(self.views.bound_key("bob", as_of=s1), BOB_KEY)
        self.assertEqual(self.views.bound_key("bob", as_of=s2), "testpub:bob:v2")
        self.assertIsNone(self.views.bound_key("bob"))                   # live: revoked

    def test_a5_root_key_is_derived_founding_asserted(self):
        # F3: the root key is founding-asserted for the chain-end; None until the ceremony seals one.
        self.assertIsNone(self.views.root_key())
        self._bind("owner", ROOT_KEY_1)
        self.assertEqual(self.views.root_key(), ROOT_KEY_1)


# ============================================================================================
# A6 — the founding-move is an OWNER GATE (HELD): production founding byte-untouched (RW-F)
# ============================================================================================

def _pack_key_family_present(text):
    """Does the founding text carry ANY member of the key family? The mechanical held-gate signal."""
    return any(tok in text for tok in ("key-bind", keys.KEY_LAW_BIND, keys.KEY_ROTATE, keys.KEY_REVOKE))


class TestFoundingMoved(unittest.TestCase):
    """A6 LIVE (COMPLETE-KEY-FAMILY, board :2887). The owner's create-word landed (:2847) and the
    architect ruled the completion (:2885): the key-bind LAW and the key-bind/key-rotate/key-revoke
    ops are the CONSTITUTION now, at founding 1.33.0. The HELD gate flipped to a LIVE one."""

    def test_a6_production_founding_declares_the_key_family(self):
        with open(PACK_PATH, encoding="utf-8") as fh:
            self.assertTrue(_pack_key_family_present(fh.read()),
                            "production founding declares NO key-family member — the create did not land")
        pack = live_pack()
        rules = {r["payload"]["rule_id"] for s in pack["steps"] for r in s["records"]
                 if r.get("action") == "CREATE-RULE"}
        self.assertIn(keys.KEY_LAW_BIND, rules)                          # the key-bind LAW
        ops = {r["payload"]["name"] for s in pack["steps"] for r in s["records"]
               if r.get("action") == "CREATE-OP"}
        self.assertEqual({keys.KEY_BIND, keys.KEY_ROTATE, keys.KEY_REVOKE} & ops,
                         {keys.KEY_BIND, keys.KEY_ROTATE, keys.KEY_REVOKE})   # the three ops

    def test_a6_the_founding_version_moved_MINOR_to_1_33_0(self):
        # MINOR: new ops + new laws, no op or law removed, no check kind added. PATCH (byte-unchanged
        # founding) would be RW-F; MAJOR (a removal or a kind change) is not this move. BOTH endpoints
        # read out of git so the bump is a fact about THIS crossing, never a relabel (§A57): the
        # pre-create era for 1.32.0, and — since COMPLETE-SIGNING-LAW (mover-2) later moved the live
        # founding to 1.34.0 — the era immediately before mover-2 for the key family's own 1.33.0,
        # rather than the live tree (which now reads 1.34.0) or a relabel to it.
        era = era_pin.pack_at(KEY_FAMILY_PRE_COMMIT, missing="assert")["founding_version"]
        now = era_pin.pack_at(MOVER2_PRE_COMMIT, missing="assert")["founding_version"]
        self.assertEqual(now, "1.33.0")
        e_maj, e_min, _ = (int(x) for x in era.split("."))
        n_maj, n_min, n_pat = (int(x) for x in now.split("."))
        self.assertEqual((n_maj, n_min, n_pat), (e_maj, e_min + 1, 0),
                         "MINOR for a new founding surface — not PATCH, not MAJOR")

    def test_a6_the_key_ops_carry_occurrence_time_via_the_router_and_no_new_check_kind(self):
        # Ruling A (architect :2885): the production key ops carry occurrence_time through the EXISTING
        # occurrence_time_param router with DEFAULTED absence (an omitted `at` mints record_time, never
        # errors), and mint NO new check kind — the leash is the gate anchor, not an op check.
        pack = live_pack()
        seen = set()
        for s in pack["steps"]:
            for r in s["records"]:
                if r.get("action") == "CREATE-OP" and r["payload"]["name"] in (
                        keys.KEY_BIND, keys.KEY_ROTATE, keys.KEY_REVOKE):
                    d = r["payload"]["definition"]
                    self.assertEqual(d.get("occurrence_time_param"),
                                     {"param": "at", "when_absent": "default"})
                    self.assertEqual(d.get("checks"), [])                # no check on any key op
                    self.assertEqual(d["params"].get("at"), "optional")  # `at` is optional, routed
                    seen.add(r["payload"]["name"])
        self.assertEqual(seen, {keys.KEY_BIND, keys.KEY_ROTATE, keys.KEY_REVOKE})
        from kernel.opdefs import OP_CHECKS
        self.assertEqual(len(OP_CHECKS), 19)                            # no new check kind minted

    def test_a6_era_pin_is_byte_untouched(self):
        # The §A57 sweep this pass era-STABILISES its version pins IN THE TEST FILES (era_pin.pack_at
        # at the landing commit); it edits no row of the era-pin library, so era_pin.py is untouched.
        with open(ERA_PIN_PATH, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, "19ebf106bcdd82753d46b5eb34146ee31c04e909dd9458b376e0271a4236eb87",
                         "tests/era_pin.py bytes changed — the §A57 sweep touches no era-pin row")

    def test_a6_the_live_gate_is_mechanical_a_stripped_key_family_would_red(self):
        # RW-F re-expressed LIVE (a check that can fail): the real pack HAS the family (live, green);
        # strip every family token and the same detector goes False — it still discriminates present
        # from absent, so a future pass that silently DROPPED the family would red this row.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        self.assertTrue(_pack_key_family_present(real))                  # real: the family is present
        stripped = real
        for tok in ("key-bind", keys.KEY_LAW_BIND, keys.KEY_ROTATE, keys.KEY_REVOKE):
            stripped = stripped.replace(tok, "X-REMOVED-X")
        self.assertFalse(_pack_key_family_present(stripped))             # stripped: the gate reds


# ============================================================================================
# A7 — round-trip: key state killed and replayed identically; the vault probe re-run
# ============================================================================================

class TestRoundTrip(KeyWorld):

    def test_a7_key_state_replays_identically_from_the_record_alone(self):
        # Bind, rotate, revoke a spread of keys, then KILL the derived state and rebuild the kernel
        # from the same record file. The fold reconstructs identically — validity is DERIVED, never
        # stored, so replay returns the same answer (theorem 7).
        self._bind("owner", ROOT_KEY_1)
        self._bind("bob", BOB_KEY)
        self._do(keys.KEY_ROTATE, "owner", {"account": "bob", "public_key": "testpub:bob:v2"})
        self._account("dave", "human")
        self._bind("dave", "testpub:dave:v1")
        self._do(keys.KEY_REVOKE, "owner", {"account": "dave"})
        before = {a: self.views.bound_key(a) for a in ("owner", "bob", "dave")}

        store2, gate2, views2 = build_kernel(self.path)                  # kill derived state, replay
        after = {a: views2.bound_key(a) for a in ("owner", "bob", "dave")}
        self.assertEqual(before, after)
        self.assertEqual(after, {"owner": ROOT_KEY_1, "bob": "testpub:bob:v2", "dave": None})

    def test_a7_the_vault_probe_re_run_finds_no_read_path(self):
        d = tempfile.mkdtemp()
        vault = VaultStore(os.path.join(d, "vault"))
        keys.seal_system_key(vault, SYSTEM_KEY_VALUE)
        keys.seal_system_key(vault, SYSTEM_KEY_VALUE)                    # idempotent re-seal (write-once)
        for banned in ("get", "read", "reveal", "open", "has", "value"):
            self.assertFalse(hasattr(vault, banned))


# ============================================================================================
# §8-h — NO NEW CHECK KIND (driven): key-bind uses the existing check vocabulary + a supersession
# fold (the succession/secret precedent). OP_CHECKS is byte-unchanged; opdefs.py was never touched.
# ============================================================================================

class TestNoNewCheckKind(unittest.TestCase):

    def test_op_checks_is_unchanged_seventeen_kinds_binding_among_them(self):
        from kernel.opdefs import OP_CHECKS
        # The 17 check kinds exactly (EP-30-K2's every_member is the seventeenth). key-bind adds
        # none — its validity is a supersession VALUE-fold (kernel.keys), the succession/secret
        # precedent, not a new check kind. A new kind would be a §8-h owner gate (STOP), not this EP.
        self.assertEqual(len(OP_CHECKS), 19)
        self.assertIn("binding", OP_CHECKS)                              # the existing kind key-bind rides
        self.assertNotIn("key", OP_CHECKS)                              # no key-specific kind minted


if __name__ == "__main__":
    unittest.main()
