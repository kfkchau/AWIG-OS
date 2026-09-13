"""EP-49B — IDENTITY AT THE TUNNEL (design/51 §3 N4, §5, §9; design/39 §1; design/43 §5).

Named in planning/exec/EP-49B-BUILD.md before code, landed here as regression tests (charter:
every verification probe lands as a regression test). This battery proves identity at the tunnel:

  A1  a crossing is attributed to the entity that WILLED it by its recorded establishment, never to
      the system; the tunnel record binds the FOUR-TUPLE (sender, target, permitted class, proof
      method, design/43 §5); an unbound crossing is refused.
  A2  a fact a peer ASSERTS lands as an INPUT-class record (the world's claim), NEVER as a DECISION
      the record authors — a peer cannot author a decision in this box.
  A3  an entity's identity resolves to its recorded ESTABLISHMENT (design/39 §1); its incarnations
      (a process handle) are a VIEW, never the entity — a crossing cites the establishment.
  A4  the BASIC proof method (a real signature, or secret_verify) admits a correct proof and refuses
      a wrong one, under an EXISTING check kind — a richer method RAISES, never mints (§11 item 3).
  A6  the founding move mints EXTERNAL-TUNNEL as a data-born MINOR bump, attested in one entry.

THE WRONG REFERENCE REFUSED BY NAME (design/51 §5): the API gateway with auth middleware — a token
minted ABOVE the system as identity, the request treated as the act, a trust store BESIDE the
record. Here identity IS the recorded establishment; a crossing is a DRAFT the gate decides;
validity is read FROM the record (design/51 §4 minimality gate: no trust table, session token or
peer certificate); a peer's own claim is INPUT.

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect, §A42/§A64). The signing library is an OPTIONAL EXTRA: the signature proof branches to
its REFUSAL arm when absent (N10: real-or-refused, never faked) and its real arm when present.
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))       # so `import era_pin` resolves
import era_pin                                                        # noqa: E402  (the era-pin home, EP-28Z)
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.opdefs import OP_CHECKS                                   # noqa: E402
from kernel.signer import SigningKeyStore                             # noqa: E402
from kernel.vault import secret_hash                                  # noqa: E402
from kernel import border, authority, crypto                         # noqa: E402
from observe import classmap                                         # noqa: E402

#: EP-49B's LANDING COMMIT — its own close era, where the founding stood at 1.42.0 and the op census
#: was 90 (EP-49B minted a LAW, EXTERNAL-TUNNEL, not an op). Verified BY CONTENT at the EP-49D §A57
#: sweep (board :3352), not by version number alone (era_pin.py's cap): version 1.42.0, census 90,
#: EXTERNAL-TUNNEL present. The op-census "no new op" row below reads THIS era, never the live tree —
#: a later founding mover (EP-49D mints RECEIPT, census -> 91) grows the live census without redding
#: EP-49B's own move evidence (§A57: a founding pass era-pins its predecessor's version and diff rows).
EP49B_LANDING = "1aa30e4d60e0c0875e3739c49ce5995aa78f7dae"

# an external entity's tunnel four-tuple (a dict fixture — CREATE-TUNNEL is boot-only, so a
# runtime external tunnel is exercised at the fold/predicate layer, the EP-49A pure-function idiom).
EXT_TUNNEL = {"name": "twc-tunnel", "sender": "twc", "target": "SYSTEM",
              "permitted": "proposal", "proof_method": "signature"}
ENTITY_SEED = bytes(range(1, 33))          # a fixed seed for the external entity's key (its name)
OTHER_SEED = bytes([9]) * 32               # a different key — the check that can fail


class _World(unittest.TestCase):
    """A kernel from the SHIPPED founding (now 1.42.0), with one external entity established to
    submit by. The shipped owner-tunnel is the CREATE-TUNNEL the fold reads."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep49b-")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.gate.execute("CREATE-ACCOUNT", "owner",
                          {"account_id": "peer", "actor_class": "human"})

    def a_submit(self, entity="peer", draft=None, tunnel=None):
        return border.submit(self.gate, entity, draft if draft is not None else {"want": "read /x"},
                             tunnel=tunnel)


# =============================================================================================
# A1 — T-BORDER-IDENTITY-BY-CROSSING (+ RW-COURIER-IDENTITY / RW-UNBOUND)
# =============================================================================================

class TestIdentityByCrossing(_World):
    def test_the_tunnel_record_binds_the_four_tuple(self):
        """N4 / design/43 §5: a tunnel binds sender, target, permitted class AND proof method. The
        fold reads the shipped owner-tunnel's binding (the owner needs no proof method — it is the
        owner, so proof_method is None); an external entity's tunnel carries the fourth field."""
        tn = border.tunnels(self.store)
        self.assertIn("owner-tunnel", tn)
        owner_t = tn["owner-tunnel"]
        for field in border.TUNNEL_FIELDS:                          # all four fields are read
            self.assertIn(field, owner_t)
        self.assertEqual(owner_t["sender"], "owner")
        self.assertEqual(owner_t["target"], "SYSTEM")
        self.assertEqual(owner_t["permitted"], "instruction information")
        self.assertIsNone(owner_t["proof_method"])                  # the owner needs none
        # an external entity's tunnel binds the fourth field, the proof method.
        self.assertEqual(EXT_TUNNEL["proof_method"], "signature")
        self.assertTrue(border.tunnel_binds(EXT_TUNNEL, "twc", "SYSTEM", "proposal"))
        self.assertFalse(border.tunnel_binds(EXT_TUNNEL, "someone-else"))  # sender is the crux

    def test_a_crossing_is_attributed_to_the_willing_entity_never_the_system(self):
        """N4 / design/39 §3 (the courier rule at the identity layer): a crossing is willed by the
        entity, and its identity resolves to that entity's recorded establishment — never the
        system."""
        sub = self.a_submit()
        cid = border.content_id(sub)
        crossing = border.crossings(self.store)[cid]
        self.assertEqual(crossing["willed_by"], "peer")
        self.assertEqual(border.system_attributed(self.store), [])       # none by the system
        # the crossing's identity IS the establishment of the willing entity (design/39 §1).
        ident = authority.identity_of_crossing(self.store, crossing)
        self.assertIsNotNone(ident)
        self.assertEqual(ident["entity"], "peer")
        self.assertEqual(ident["established_by"], "CREATE-ACCOUNT")

    def test_RW_COURIER_IDENTITY_a_system_willed_crossing_reds_the_census(self):
        """RW-COURIER-IDENTITY (§5): the census is able-to-fail. A crossing whose willing entity is
        the system, planted in the set the census reads, makes it FIRE (design/39 §3)."""
        real = list(border.crossings(self.store).values())
        self.assertEqual(border.system_attributed_over(real), [])        # real world clean
        planted = real + [{"crossing_id": "sha256:beef", "willed_by": "SYSTEM",
                           "entity": "SYSTEM", "state": "open"}]
        offenders = border.system_attributed_over(planted)
        self.assertEqual([c["crossing_id"] for c in offenders], ["sha256:beef"])

    def test_an_unbound_crossing_is_refused_at_the_gate(self):
        """N4: an UNBOUND crossing is refused. A submit declaring a tunnel whose SENDER is not the
        crossing's entity crosses nothing lawful and is refused (RW-UNBOUND). A BOUND crossing (the
        entity IS the tunnel's sender) passes; a submit declaring NO tunnel is untouched (EP-49A)."""
        # BOUND: establish an account matching the owner-tunnel's sender and cross it -> allowed.
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "owner", "actor_class": "human"})
        bound = self.a_submit(entity="owner", draft={"want": "instruct"}, tunnel="owner-tunnel")
        self.assertEqual(bound["action"], "BORDER-SUBMIT")               # bound -> crosses
        # UNBOUND: peer declares owner-tunnel, whose sender is "owner", not "peer" -> refused.
        with self.assertRaises(OpError) as cm:
            self.a_submit(entity="peer", draft={"want": "x"}, tunnel="owner-tunnel")
        self.assertEqual(cm.exception.rule, "COMM-LAW-CONTRACT")
        refs = [e for e in self.store.by_action("op-refused")
                if (e.get("payload") or {}).get("op") == "BORDER-SUBMIT"]
        self.assertTrue(refs, "the unbound submit was silently dropped, not recorded")
        # a submit declaring a tunnel that is not founded is also unbound -> refused.
        with self.assertRaises(OpError):
            self.a_submit(entity="peer", draft={"want": "x"}, tunnel="ghost-tunnel")
        # a submit declaring NO tunnel is not an external-tunnel crossing -> passes (EP-49A intact).
        self.assertEqual(self.a_submit()["action"], "BORDER-SUBMIT")

    def test_RW_UNBOUND_the_binding_census_is_able_to_fail(self):
        """RW-UNBOUND (§5): the unbound census reads from the SET. A crossing whose entity is a
        founded tunnel's sender is BOUND; one whose entity is no tunnel's sender is UNBOUND and
        fires the census (both directions provable)."""
        tunnels = {"twc-tunnel": EXT_TUNNEL}
        bound_c = {"crossing_id": "c1", "willed_by": "twc"}             # twc IS the tunnel's sender
        unbound_c = {"crossing_id": "c2", "willed_by": "stranger"}      # nobody's sender
        cs = [bound_c, unbound_c]
        self.assertEqual([c["crossing_id"] for c in border.bound_over(cs, tunnels)], ["c1"])
        self.assertEqual([c["crossing_id"] for c in border.unbound_over(cs, tunnels)], ["c2"])
        self.assertEqual(border.unbound_over([bound_c], tunnels), [])    # a bound world is clean


# =============================================================================================
# A2 — T-PEER-RECORD-NOT-TRUSTED (+ RW-PEER-TRUSTED)
# =============================================================================================

class TestPeerRecordNotTrusted(unittest.TestCase):
    def test_a_peer_asserted_fact_is_classified_INPUT_never_DECISION(self):
        """N4: a fact a peer ASSERTS is an external arrival the box did not author -> INPUT (the
        world's claim). The `peer` window has NO act mapping to DECISION — a peer cannot author a
        decision in this box (design/51 §4 minimality gate)."""
        self.assertEqual(classmap.classify("peer", "peer-asserted-fact"), classmap.INPUT)
        self.assertEqual(classmap.classify("peer", "peer-state-changed"), classmap.INPUT)
        self.assertEqual(authority.peer_fact_admitted_class(), classmap.INPUT)
        # not one act of the peer window is a DECISION (the class-map's own statement).
        self.assertNotIn(classmap.DECISION, set(classmap.CLASS_MAP["peer"].values()))
        # and the map has no way to name a peer decision at all (a silent drop would be the defect).
        with self.assertRaises(classmap.UnmappedAct):
            classmap.classify("peer", "peer-decision")

    def test_RW_PEER_TRUSTED_a_peer_assertion_admitted_as_a_decision_reds(self):
        """RW-PEER-TRUSTED (§5): the census is able-to-fail. A peer-asserted record marked DECISION —
        a peer's claim admitted as a fact the box decided — fires the census; a peer fact recorded
        as INPUT (the honest world) leaves it empty (discriminates)."""
        planted_decision = {"payload": {"source": "peer", "record_class": "DECISION",
                                        "claim": "I am root"}}
        honest_input = {"payload": {"source": "peer", "record_class": "INPUT",
                                    "claim": "I am root"}}
        self.assertEqual(len(authority.peer_facts_authored_as_decision([planted_decision])), 1)
        self.assertEqual(authority.peer_facts_authored_as_decision([honest_input]), [])
        # a NON-peer decision (the box's own act) is not caught — the census discriminates on source.
        box_decision = {"payload": {"source": "box", "record_class": "DECISION"}}
        self.assertEqual(authority.peer_facts_authored_as_decision([box_decision]), [])


# =============================================================================================
# A3 — T-ESTABLISHMENT-IS-IDENTITY (+ RW-INCARNATION-AS-IDENTITY)
# =============================================================================================

class TestEstablishmentIsIdentity(_World):
    def test_identity_resolves_to_the_recorded_establishment(self):
        """design/39 §1: an entity IS its recorded establishment. A CREATE-ACCOUNT entity resolves;
        a genesis CREATE-ACTOR (owner, an anchor) resolves; both from the record, no stored login."""
        est_peer = authority.establishment_of(self.store, "peer")
        self.assertIsNotNone(est_peer)
        self.assertEqual(est_peer["entity"], "peer")
        self.assertEqual(est_peer["established_by"], "CREATE-ACCOUNT")
        self.assertTrue(authority.is_established(self.store, "peer"))
        est_owner = authority.establishment_of(self.store, "owner")     # the genesis anchor
        self.assertIsNotNone(est_owner)
        self.assertEqual(est_owner["established_by"], "CREATE-ACTOR")

    def test_RW_INCARNATION_AS_IDENTITY_a_transient_handle_is_not_the_entity(self):
        """RW-INCARNATION-AS-IDENTITY (§5): an incarnation (a process handle, an in-band token, a
        session name) is a VIEW of an entity, never the entity. It names no establishment on the
        record, so it resolves to None — and a crossing whose willing name is such a handle has no
        identity (able-to-fail: the resolver returns None where a real crossing returns the
        establishment)."""
        self.assertIsNone(authority.establishment_of(self.store, "pid:12345"))
        self.assertIsNone(authority.establishment_of(self.store, "session-abc"))
        self.assertFalse(authority.is_established(self.store, "bearer-token-xyz"))
        # a real crossing's identity resolves to the establishment; a planted incarnation-as-identity
        # crossing resolves to None (the crossing cites a transient handle, not the establishment).
        sub = self.a_submit()
        real = border.crossings(self.store)[border.content_id(sub)]
        self.assertIsNotNone(authority.identity_of_crossing(self.store, real))
        incarnation = {"crossing_id": "c-pid", "willed_by": "pid:98765", "entity": "pid:98765"}
        self.assertIsNone(authority.identity_of_crossing(self.store, incarnation))


# =============================================================================================
# A4 — T-PROOF-METHOD-BASIC (+ RW-NEW-KIND-SILENT) — real-or-refused, existing kinds only
# =============================================================================================

class TestProofMethodBasic(unittest.TestCase):
    def test_the_signature_proof_method_verifies_real_where_present_refused_where_absent(self):
        """A4: a tunnel whose proof method is a real SIGNATURE admits a correct proof and refuses a
        wrong one, under the EXISTING crypto kind (EP-47's signer / EP-49A's seal). Real-or-refused:
        with the library ABSENT verification REFUSES citing the absent library, never a modelled
        pass (N10). The entity's key IS its name (D08.42)."""
        tun = {"proof_method": "signature"}
        cid = "sha256:" + "a" * 64
        shown = {"answer": "granted", "detail": "cross at 10s"}
        signer = SigningKeyStore()
        custody = signer.seal(ENTITY_SEED)

        if not crypto.real_available():
            with self.assertRaises(crypto.LibraryAbsent):
                border.proof_verifies(tun, "seal:placeholder",
                                      public_key=b"pk", crossing_id=cid, shown=shown)
            return

        pub = crypto.public_from_seed(ENTITY_SEED)
        seal = signer.sign(custody, border.shown_digest(cid, shown))
        self.assertTrue(border.proof_verifies(tun, seal, public_key=pub, crossing_id=cid, shown=shown))
        # WRONG proof: an altered `shown` (the seal is over exactly what was shown) -> refused.
        altered = dict(shown); altered["answer"] = "DENIED"
        self.assertFalse(border.proof_verifies(tun, seal, public_key=pub, crossing_id=cid, shown=altered))
        # WRONG key: a real signature under a DIFFERENT key -> refused (the check that can fail).
        other = crypto.public_from_seed(OTHER_SEED)
        self.assertFalse(border.proof_verifies(tun, seal, public_key=other, crossing_id=cid, shown=shown))

    def test_the_secret_verify_proof_method_admits_correct_refuses_wrong_never_records(self):
        """A4: a tunnel whose proof method is `secret_verify` admits a correct candidate and refuses
        a wrong one, under the EXISTING EP-19 kind — the candidate crosses ONCE, compared BY HASH,
        NEVER recorded (design/31 J8). `proof_verifies` takes no store/gate, so the candidate reaches
        no record: the compare is a pure hash."""
        tun = {"proof_method": "secret_verify", "secret_hash": secret_hash("open-sesame")}
        self.assertTrue(border.proof_verifies(tun, "open-sesame"))
        self.assertFalse(border.proof_verifies(tun, "guess"))            # wrong -> refused
        # a tunnel with no sealed secret admits nothing (there is no hash to match).
        self.assertFalse(border.proof_verifies({"proof_method": "secret_verify"}, "anything"))

    def test_RW_NEW_KIND_SILENT_a_richer_proof_method_raises_never_mints_a_kind(self):
        """RW-NEW-KIND-SILENT (§5 / stop-e): a richer proof method (quorum / blind position /
        focus-lock) is a NEW CHECK KIND — the owner's one word, RAISED never minted here. The
        instrument RAISES rather than modelling a pass, and the check-kind menu stays frozen at 17
        (no kind minted by this EP)."""
        for method in ("quorum", "blind-position", "focus-lock"):
            with self.assertRaises(ValueError) as cm:
                border.proof_verifies({"proof_method": method}, "x")
            self.assertIn("owner's one word", str(cm.exception))
        self.assertEqual(len(OP_CHECKS), 19)                             # no check kind minted
        self.assertEqual(set(border.BASIC_PROOF_METHODS), {"signature", "secret_verify"})


# =============================================================================================
# A6 — T-FOUNDING-BUMP-ATTESTED (+ RW-NO-MOVE / RW-MAJOR) — the founding move (data-born MINOR)
# =============================================================================================

def _pack_records():
    import json
    repo = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(repo, "src", "founding", "founding-pack.json"), "rb") as fh:
        return [r for step in json.loads(fh.read())["steps"] for r in step["records"]]


class TestFoundingBumpAttested(unittest.TestCase):
    def test_the_founding_rose_one_MINOR_and_the_bump_is_attested_in_one_entry(self):
        from test_founding_is_logged import audit, pack_facts
        facts = pack_facts()
        # ERA-PINNED (EP-49D §A57 sweep, the manager's test_ep48 model, board :3352): this was a LIVE
        # literal `assertEqual(facts["version"], "1.42.0")` that every later founding mover would
        # hand-edit — the class the era-pin idiom exists to end. Floored at the EP-49B era (1.42.0,
        # EP-49B's own MINOR landing); a later founding mover advances WITHOUT touching this line. The
        # load-bearing assertion is that THIS founding on disk is attested in ONE entry (audit, below).
        ver = tuple(int(x) for x in facts["version"].split("."))
        self.assertGreaterEqual(ver, (1, 42, 0),
                                "the founding is at or beyond the EP-49B era (1.42.0) this test pins")
        a = audit()
        self.assertTrue(a["logged"],
                        "the founding moved to 1.42.0 and no single BUILD-PROGRESS entry names both "
                        "the version and the pack sha256 (the required ledger duty, :1178/:2805)")

    def test_EXTERNAL_TUNNEL_is_a_root_law_in_the_pack_and_the_move_is_MINOR(self):
        recs = _pack_records()
        root_laws = {r["payload"]["rule_id"]: r["payload"] for r in recs
                     if r.get("action") == "CREATE-RULE" and (r.get("payload") or {}).get("root")}
        self.assertIn("EXTERNAL-TUNNEL", root_laws)                      # ADDED — the MINOR direction
        et = root_laws["EXTERNAL-TUNNEL"]
        self.assertEqual(et["scope"], "space:root")
        self.assertEqual(et.get("tier", "ordinary"), "ordinary")        # not a constitutional privilege
        self.assertEqual(et["enforcement"], "deferred")                 # the general consumer is C6's (§9)
        self.assertTrue(et["then"])                                     # non-empty outcome (full-form)
        self.assertIsNotNone(et["enforced_by"])
        # the OWNER-TUNNEL law it rides beside is UNTOUCHED (append-only founding data; §7).
        self.assertIn("OWNER-TUNNEL", root_laws)
        self.assertIn("owner may send", root_laws["OWNER-TUNNEL"]["text"])

    def test_RW_NO_MOVE_and_RW_MAJOR_the_discriminator_holds(self):
        """RW-NO-MOVE (§5): a founding move that moved nothing fails — EXTERNAL-TUNNEL IS present
        (the move happened). RW-MAJOR (§5 / stop-e): the move is MINOR by construction — NO op or
        law removed, NO check kind added, NO new op minted (op-census unchanged), NO tunnel instance
        minted (a tunnel is per-entity, EP-51's — the CREATE-TUNNEL count is unchanged)."""
        recs = _pack_records()
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        # NONE REMOVED: representative pre-move ops survive (a removal would be MAJOR / stop-e).
        for kept in ("BORDER-SUBMIT", "BORDER-REPLY", "SOCKET-OPEN", "COMMS-OPEN", "FILE-CREATE"):
            self.assertIn(kept, op_names)
        self.assertEqual(len(OP_CHECKS), 19)                            # NO check kind added
        # ERA-PINNED (EP-49D §A57 sweep, board :3352): EP-49B minted a LAW (EXTERNAL-TUNNEL), NO op, so
        # its census was 90 AT ITS ERA. This reads the op census at EP-49B's LANDING commit, not the
        # live tree — EP-49D mints RECEIPT (census -> 91), and a founding pass era-pins its
        # predecessor's diff rows (§A57) so EP-49B's own "no new op" evidence stays exact and green.
        era_ops = {r["payload"]["name"]
                   for step in era_pin.pack_at(EP49B_LANDING, missing="assert")["steps"]
                   for r in step["records"] if r.get("action") == "CREATE-OP"}
        self.assertEqual(len(era_ops), 90)                            # NO new op minted at EP-49B's era
        tunnels = [r for r in recs if r.get("action") == "CREATE-TUNNEL"]
        self.assertEqual(len(tunnels), 1)                             # only owner-tunnel — no instance minted
        # RW-NO-MOVE: the byte-move happened — the law is in the pack and the version rose. FLOORED at
        # the EP-49B era (§A57): a later founding mover advances the live version without redding this.
        from test_founding_is_logged import pack_facts
        ver = tuple(int(x) for x in pack_facts()["version"].split("."))
        self.assertGreaterEqual(ver, (1, 42, 0),
                                "the founding is at or beyond the EP-49B era (1.42.0) this test pins")


# =============================================================================================
# §5 / design/51 §5 — THE WRONG REFERENCE REFUSED BY NAME: the API gateway with auth middleware
# =============================================================================================

class TestApiGatewayTrapRefused(_World):
    def test_identity_is_recorded_establishment_never_a_peer_minted_token(self):
        """design/51 §5 (stop-f): identity is the recorded establishment, NEVER a token minted above
        the system. A submitter the record never established is refused however it names itself; a
        bearer token resolves to no establishment; there is no trust store beside the record —
        validity is read FROM the record."""
        with self.assertRaises(OpError) as cm:
            border.submit(self.gate, "attacker-holding-a-bearer-token", {"want": "root"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        # the token is nobody on the record — no establishment, no trust store to consult.
        self.assertIsNone(authority.establishment_of(self.store, "attacker-holding-a-bearer-token"))
        # design/51 §4 minimality gate: no trust table, session token or peer certificate enters —
        # the tunnel binding and the identity resolution both read only recorded facts.
        self.assertTrue(border.tunnel_binds(EXT_TUNNEL, "twc"))         # by the record's sender field
        self.assertFalse(border.tunnel_binds(EXT_TUNNEL, "twc-with-a-forged-token"))


if __name__ == "__main__":
    unittest.main()
