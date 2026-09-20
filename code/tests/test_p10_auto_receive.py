# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (received row, INPUT vs DECISION, adoption act, active constitution view); NON-GOAL: no
# offensive capability of any kind — this records a child AUTO-RECEIVING its parent's signed rules as
# INPUT and changing only by its own act, by function. Full declaration: SCOPE-STATEMENT.md.
"""C6 P10 — AUTO-RECEIVE, NEVER AUTO-CHANGE, AND HOLD EXACTLY WHAT BINDS (design/52 B2:51, B5:54,
I3:75, I5:77; plan planning/exec/P10-AUTO-RECEIVE-BUILD.md).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). P10 consumes P7 (the live handshake relation, the parent's key) and P8
(the RECEIPT receiving vocabulary); it MINTS NOTHING (no op, law or check kind, no pack edit) and
re-authors nothing (the border INPUT/DECISION mechanism, keys.verify_countersign / reconstruct's
verify, are READ and reused).

  A1 (I3)  A PARENT ROW LANDS INPUT, NEVER A DECISION. A row signed by the parent's key (the key held
      in the child's live handshake relation, P7) lands with record_class INPUT through the child's
      gate (a receipt whose crossed rule is tagged INPUT); a planted attempt to land it as a DECISION
      is REFUSED and RECORDED (the positive control — the check can fail).
  A2 (B2)  RECEIVE IS NOT CHANGE. the received parent rule is recorded INPUT and does NOT enter the
      child's active constitution until a CHILD-AUTHORED adoption act cites it; the update is a row,
      no reboot.
  A3 (I5)  ADOPTION IS THE CHILD'S OWN ACT, BY HASH. for a received rule in force there is a child
      adoption citing it BY HASH; an unadopted received rule is NOT in the active constitution view
      (recomputed from received+adopted rows alone equals the served one). BOTH paths: by hand AND
      AUTOMATICALLY by the child's own standing rule (L27), the row recording which.
  A4 (B5)  HOLD WHAT BINDS. every parent rule the child was ever bound by is a received row in the
      child's own record; "what bound me at T" recomputes locally.
  A5       whole ledger green PER MODULE.

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect): a forged mark refused; a receipt under no live relation refused; a DECISION-tagged
crossed rule refused; the census fired by a planted DECISION entry; an unadopted rule absent.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel import border, keys                                       # noqa: E402


PARENT_KEY = "ed25519-pub:parent"
ATTACKER_KEY = "ed25519-pub:attacker"


def _body(prefix, entity, actor_class="ai"):
    """One BODY — an independent record (its own data dir), gate and views, with `entity` established
    as an account so it may open a crossing (BORDER-SUBMIT's require_prior over CREATE-ACCOUNT). A
    body writes only its own record (one pen per record, the single-writer lock)."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": entity, "actor_class": actor_class})
    return d, store, gate, views


def _parent_name(genesis="sha256:" + "beef" * 16, key=PARENT_KEY):
    """A parent body's NAME (D08.42): (bound public key, genesis hash)."""
    return border.from_body_name(key, genesis)


def _declare_relation(child_gate, child_entity, parent_name, tag=None):
    """The child declares a LIVE handshake relation naming the parent's body-name (P7). Returns the
    relation id (the declare crossing's content hash)."""
    hs = {"parent": parent_name}
    if tag is not None:
        hs["tag"] = tag
    declare = border.submit(child_gate, child_entity, {"handshake_relation": hs}, actor=child_entity)
    return border.content_id(declare)


def _parent_rule(rule_id, scope=None, seq=1000, record_time="2026-09-10T00:00:00Z", extra=None):
    """A parent RULE record as it crosses to the child: a CREATE-RULE-shaped row with the parent's
    recording fact (seq, record_time) so keys.verify_countersign binds it. content_id ignores the
    recording envelope, so the rule hash is stable."""
    payload = {"rule_id": rule_id, "scope": scope, "policy_key": "govern", "value": "the-rule-body"}
    if extra:
        payload.update(extra)
    return {"actor": "parent", "action": "CREATE-RULE", "object": rule_id, "target": None,
            "payload": payload, "seq": seq, "record_time": record_time}


def _mark(rule_record, key=PARENT_KEY):
    """The parent's countersign mark over the rule record, under `key` (keys.countersign — the modelled
    mark: custody + the recording fact). A mark under the WRONG key fails verify (the red world)."""
    return keys.countersign(rule_record, key)


def _auto_adopt_rule(child_gate, scope, rule_id=None, actor="owner"):
    """The child's OWN standing auto-adopt rule (L27) for a named `scope` — a live CREATE-RULE
    self-declaring the AUTO_ADOPT_MARKER (the P6 liveness idiom). The child may withdraw it."""
    rid = rule_id or ("child-auto-adopt-" + str(scope))
    return child_gate.execute("CREATE-RULE", actor,
                              {"rule_id": rid, "policy_key": border.AUTO_ADOPT_MARKER, "scope": scope})


# =============================================================================================
# A1 (I3) — A PARENT ROW LANDS INPUT, NEVER A DECISION
# =============================================================================================

class TestParentRowLandsInput(unittest.TestCase):
    def setUp(self):
        self.cd, self.store, self.gate, self.views = _body("p10-a1-child-", "child")
        self.parent_name = _parent_name()
        self.rid = _declare_relation(self.gate, "child", self.parent_name)

    def test_a_parent_signed_row_lands_with_record_class_input(self):
        """I3: a row signed by the parent's key (verified against the key held in the child's live
        relation) lands with record_class INPUT through the child's gate — a receipt whose crossed
        rule is tagged INPUT / source parent. The parent never wrote the child's record: it is the
        child's own receipt (a DECISION act), carrying the parent's rule as the parent's claim."""
        rule = _parent_rule("PARENT-TAX-LAW", scope="tax")
        out = border.receive_parent_rule(self.gate, self.views, self.rid, rule, _mark(rule))
        received = border.received_parent_rules(self.store)
        h = border.content_id(rule)
        self.assertIn(h, received)                                       # the parent rule is held
        self.assertEqual(received[h]["record_class"], "INPUT")           # landed INPUT (I3)
        self.assertEqual(received[h]["source"], "parent")                # the parent's claim
        self.assertEqual(received[h]["rule_id"], "PARENT-TAX-LAW")
        # the child's row is a RECEIPT (its own DECISION act), through the child's gate:
        self.assertEqual(out["receipt"]["action"], "RECEIPT")
        self.assertEqual(out["receipt"]["actor"], "SYSTEM")              # the child's recorder, its own pen (I1)

    def test_RW_a_planted_attempt_to_land_it_as_a_decision_is_refused_and_recorded(self):
        """I3 / THE POSITIVE CONTROL (able-to-fail): a receipt whose crossed rule is tagged
        record_class DECISION — a parent's rule landed as a fact the child decided — is REFUSED at the
        receipt chokepoint and RECORDED. Able-to-fail: the INPUT reception above is admitted, so the
        refusal is the DECISION plant's alone."""
        rule = _parent_rule("PARENT-DECISION-PLANT", scope="tax")
        h = border.content_id(rule)
        planted = {"source": "parent", "record_class": "DECISION",       # landed as a DECISION (the plant)
                   "rule_id": "PARENT-DECISION-PLANT", "rule_hash": h, "scope": "tax", "body": {}}
        before = len(self.store.all())
        with self.assertRaises(OpError) as cm:
            border.record_receipt(self.gate, h, self.parent_name, _mark(rule),
                                  revealed_set={border.RECEIVED_RULE_KEY: planted})
        self.assertEqual(cm.exception.rule, "COMM-LAW-CONTRACT")
        # RECORDED: a refusal row landed, and the plant did NOT enter the received-rules fold.
        self.assertGreater(len(self.store.all()), before)               # the refusal is recorded
        self.assertNotIn(h, border.received_parent_rules(self.store))    # the DECISION plant is not held

    def test_RW_a_forged_mark_does_not_verify_and_is_refused(self):
        """I3/I4 (able-to-fail): the parent-signed row is verified against the parent's key in the
        live relation (keys.verify_countersign reused). A mark under the WRONG key does not verify and
        is refused and recorded; nothing is admitted under a row the child cannot prove the parent
        signed."""
        rule = _parent_rule("PARENT-FORGED", scope="tax")
        with self.assertRaises(OpError) as cm:
            border.receive_parent_rule(self.gate, self.views, self.rid, rule, _mark(rule, ATTACKER_KEY))
        self.assertEqual(cm.exception.rule, "COMM-LAW-CONTRACT")
        self.assertNotIn(border.content_id(rule), border.received_parent_rules(self.store))

    def test_RW_a_receipt_under_no_live_relation_is_refused(self):
        """I4 (able-to-fail): a child holds no parent key outside a LIVE relation. Receiving a parent
        rule under an unknown relation id is refused; and after the relation is withdrawn, the same
        receive is refused (the key is gone with the live relation)."""
        rule = _parent_rule("PARENT-NO-REL", scope="tax")
        with self.assertRaises(OpError):
            border.receive_parent_rule(self.gate, self.views, "sha256:" + "0" * 64, rule, _mark(rule))
        # withdraw the live relation, then the same receive is refused (I4: reads as ended).
        border.submit(self.gate, "child", {"handshake_relation": {"withdraws": self.rid}}, actor="child")
        self.assertFalse(self.views.handshake_relation_live(self.rid))
        with self.assertRaises(OpError):
            border.receive_parent_rule(self.gate, self.views, self.rid, rule, _mark(rule))

    def test_the_census_finds_every_received_row_input_and_fires_on_a_planted_decision(self):
        """I7 (the shape of the entries): a census over the received-rules fold finds every peer-origin
        row tagged INPUT (empty on the real fold). Able-to-fail: a planted parent-origin entry tagged
        DECISION fires it; a NON-parent entry does not (it discriminates on source)."""
        rule = _parent_rule("PARENT-CENSUS", scope="tax")
        border.receive_parent_rule(self.gate, self.views, self.rid, rule, _mark(rule))
        real = list(border.received_parent_rules(self.store).values())
        self.assertEqual(border.received_rules_authored_as_decision(real), [])   # every real entry INPUT
        planted = {"source": "parent", "record_class": "DECISION"}
        self.assertEqual(len(border.received_rules_authored_as_decision([planted])), 1)
        self.assertEqual(border.received_rules_authored_as_decision(
            [{"source": "box", "record_class": "DECISION"}]), [])        # non-parent: not caught


# =============================================================================================
# A2 (B2) — RECEIVE IS NOT CHANGE
# =============================================================================================

class TestReceiveIsNotChange(unittest.TestCase):
    def setUp(self):
        self.cd, self.store, self.gate, self.views = _body("p10-a2-child-", "child")
        self.parent_name = _parent_name()
        self.rid = _declare_relation(self.gate, "child", self.parent_name)

    def test_a_received_rule_is_not_in_the_active_constitution_until_a_child_adoption(self):
        """B2: the received parent rule is recorded (INPUT) and does NOT alter the child's active
        constitution until a CHILD-AUTHORED adoption act cites it. Receive changes nothing; the
        update is a row, and there is no reboot (a fresh kernel over the same file recomputes it)."""
        rule = _parent_rule("PARENT-SPEND-LAW", scope="spend")
        h = border.content_id(rule)
        border.receive_parent_rule(self.gate, self.views, self.rid, rule, _mark(rule))
        self.assertIn(h, border.received_parent_rules(self.store))       # received
        self.assertNotIn(h, border.active_constitution(self.store))      # but NOT in force (receive is not change)
        # the child adopts by its own act -> now in force. A row, no reboot.
        border.adopt_received_rule(self.gate, h, "child-obeys-spend", scope="spend")
        self.assertIn(h, border.active_constitution(self.store))
        self.assertEqual(border.active_constitution(self.store)[h]["mode"], "hand")

    def test_no_reboot_a_fresh_kernel_over_the_same_record_recomputes_the_constitution(self):
        """B2 / P2 round-trip: the active constitution is a FOLD — a fresh kernel over the same record
        file recomputes the identical view (kill it, replay, identical). No reboot, no stored status."""
        rule = _parent_rule("PARENT-KEEP", scope="keep")
        h = border.content_id(rule)
        border.receive_parent_rule(self.gate, self.views, self.rid, rule, _mark(rule))
        border.adopt_received_rule(self.gate, h, "child-obeys-keep", scope="keep")
        served = border.active_constitution(self.store)
        s2, _g2, _v2, _b2, _u2 = build_full_kernel(
            os.path.join(self.cd, "record.jsonl"), os.path.join(self.cd, "blobs"),
            os.path.join(self.cd, "vault"))
        self.assertEqual(border.active_constitution(s2), served)


# =============================================================================================
# A3 (I5) — ADOPTION IS THE CHILD'S OWN ACT, BY HASH (BOTH PATHS: HAND AND AUTOMATIC)
# =============================================================================================

class TestAdoptionIsTheChildsOwnActByHash(unittest.TestCase):
    def setUp(self):
        self.cd, self.store, self.gate, self.views = _body("p10-a3-child-", "child")
        self.parent_name = _parent_name()
        self.rid = _declare_relation(self.gate, "child", self.parent_name)

    def test_for_a_received_rule_in_force_there_is_a_child_adoption_citing_it_by_hash(self):
        """I5: for every received rule IN FORCE there exists a child-authored adoption act citing it
        BY HASH; the citation resolves LOCALLY (the received rule is in the child's own record, I6).
        An unadopted received rule is NOT in the active view (recomputed == served, the cache-kill)."""
        adopted = _parent_rule("PARENT-A", scope="a")
        unadopted = _parent_rule("PARENT-B", scope="b")
        ha, hb = border.content_id(adopted), border.content_id(unadopted)
        border.receive_parent_rule(self.gate, self.views, self.rid, adopted, _mark(adopted))
        border.receive_parent_rule(self.gate, self.views, self.rid, unadopted, _mark(unadopted))
        border.adopt_received_rule(self.gate, ha, "child-obeys-a", scope="a")     # adopt ONLY a
        active = border.active_constitution(self.store)
        self.assertIn(ha, active)                                        # in force: has an adoption
        self.assertNotIn(hb, active)                                     # received, no adoption -> not in force
        # the adoption cites the received rule BY HASH, and the hash resolves locally (I6):
        self.assertEqual(border.adoptions(self.store)[ha]["received_rule_hash"], ha)
        self.assertIn(ha, border.received_parent_rules(self.store))      # the cited rule is local

    def test_the_automatic_path_a_standing_rule_adopts_on_receipt_for_named_scopes(self):
        """B2 / L27 — THE AUTO PATH: the child's OWN standing rule adopts AUTOMATICALLY on receipt for
        a named scope, the ROW recording mode 'auto'; a rule in an UNnamed scope is received but NOT
        auto-adopted (both lawful). Drives the word AUTO the plan names."""
        _auto_adopt_rule(self.gate, "econ")                             # the child's standing rule for scope econ
        self.assertIn("econ", border.auto_adopt_scopes(self.store, self.views))
        in_scope = _parent_rule("PARENT-ECON", scope="econ")
        out_scope = _parent_rule("PARENT-HEALTH", scope="health")
        h_in, h_out = border.content_id(in_scope), border.content_id(out_scope)
        r_in = border.receive_parent_rule(self.gate, self.views, self.rid, in_scope, _mark(in_scope))
        r_out = border.receive_parent_rule(self.gate, self.views, self.rid, out_scope, _mark(out_scope))
        self.assertIsNotNone(r_in["adoption"])                          # auto-adopted on receipt
        self.assertIn(h_in, border.active_constitution(self.store))     # in force with no hand act
        self.assertEqual(border.active_constitution(self.store)[h_in]["mode"], "auto")  # the row records AUTO
        self.assertIsNone(r_out["adoption"])                           # unnamed scope: NOT auto-adopted
        self.assertNotIn(h_out, border.active_constitution(self.store))

    def test_the_child_may_withdraw_its_standing_auto_adopt_rule(self):
        """L27: auto-adoption is the child's OWN standing rule, which it may WITHDRAW (supersede). A
        received rule in a WITHDRAWN scope is NOT auto-adopted (the child controls its own updating)."""
        _auto_adopt_rule(self.gate, "trade", rule_id="child-auto-trade")
        self.assertIn("trade", border.auto_adopt_scopes(self.store, self.views))
        # withdraw: supersede the SAME rule_id with a rule that no longer declares the marker.
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "child-auto-trade", "policy_key": "withdrawn"})
        self.assertNotIn("trade", border.auto_adopt_scopes(self.store, self.views))
        rule = _parent_rule("PARENT-TRADE", scope="trade")
        r = border.receive_parent_rule(self.gate, self.views, self.rid, rule, _mark(rule))
        self.assertIsNone(r["adoption"])                                # no longer auto-adopted

    def test_the_active_constitution_recomputed_from_received_rows_alone_equals_the_served(self):
        """I6 (the cache-kill form): the active constitution recomputed from the received + adopted
        rows ALONE equals the served one — a fresh kernel over the same record file reconstructs it
        identically, over a mix of adopted, unadopted and auto-adopted rules."""
        _auto_adopt_rule(self.gate, "auto")
        r1 = _parent_rule("R1", scope="auto")                          # auto-adopted
        r2 = _parent_rule("R2", scope="x")                             # adopted by hand
        r3 = _parent_rule("R3", scope="y")                             # received, never adopted
        for r in (r1, r2, r3):
            border.receive_parent_rule(self.gate, self.views, self.rid, r, _mark(r))
        border.adopt_received_rule(self.gate, border.content_id(r2), "child-obeys-r2", scope="x")
        served = border.active_constitution(self.store)
        self.assertEqual({border.content_id(r1), border.content_id(r2)}, set(served))  # r3 absent
        s2, _g2, _v2, _b2, _u2 = build_full_kernel(
            os.path.join(self.cd, "record.jsonl"), os.path.join(self.cd, "blobs"),
            os.path.join(self.cd, "vault"))
        self.assertEqual(border.active_constitution(s2), served)


# =============================================================================================
# A4 (B5) — HOLD WHAT BINDS
# =============================================================================================

class TestHoldWhatBinds(unittest.TestCase):
    def setUp(self):
        self.cd, self.store, self.gate, self.views = _body("p10-a4-child-", "child")
        self.parent_name = _parent_name()
        self.rid = _declare_relation(self.gate, "child", self.parent_name)

    def test_every_parent_rule_ever_bound_is_a_received_row_in_the_childs_own_record(self):
        """B5: every parent rule the child was ever bound by lives in the child's OWN record as a
        received row — held locally, whether or not it is still in force. Adopted or not, it is held."""
        adopted = _parent_rule("BOUND-1", scope="s1")
        unadopted = _parent_rule("BOUND-2", scope="s2")
        border.receive_parent_rule(self.gate, self.views, self.rid, adopted, _mark(adopted))
        border.receive_parent_rule(self.gate, self.views, self.rid, unadopted, _mark(unadopted))
        border.adopt_received_rule(self.gate, border.content_id(adopted), "child-1", scope="s1")
        held = border.received_parent_rules(self.store)
        self.assertIn(border.content_id(adopted), held)                # in force AND held
        self.assertIn(border.content_id(unadopted), held)              # not in force, STILL held (B5)

    def test_what_bound_me_at_T_recomputes_locally(self):
        """B5 / A4: "what bound me at T" is a local fold as of T. A rule received AFTER T is not in the
        as-of-T answer; a rule received at or before T is. Recomputed from the child's record alone."""
        first = _parent_rule("AT-T-1", scope="s1")
        out1 = border.receive_parent_rule(self.gate, self.views, self.rid, first, _mark(first))
        t = out1["receipt"]["seq"]                                      # the moment T
        second = _parent_rule("AT-T-2", scope="s2")
        border.receive_parent_rule(self.gate, self.views, self.rid, second, _mark(second))
        bound_at_t = border.bound_at(self.store, t)
        self.assertIn(border.content_id(first), bound_at_t)            # bound at T
        self.assertNotIn(border.content_id(second), bound_at_t)        # not yet received at T
        self.assertIn(border.content_id(second), border.bound_at(self.store, None))  # bound by now


# =============================================================================================
# A5 — WHOLE LEDGER GREEN PER MODULE (the per-module suite drive)
# =============================================================================================

class TestA5WholeLedgerSmoke(unittest.TestCase):
    def test_receive_adopt_and_the_constitution_view_compose_end_to_end(self):
        """A5 smoke: the whole path composes on a fresh founded kernel — declare relation, receive,
        auto-adopt and hand-adopt, and the active constitution reads correctly. (The per-module
        `python3 -m unittest tests.test_p10_auto_receive` IS the ledger-green drive for this unit.)"""
        cd, store, gate, views = _body("p10-a5-child-", "child")
        rid = _declare_relation(gate, "child", _parent_name())
        _auto_adopt_rule(gate, "auto")
        auto = _parent_rule("SMOKE-AUTO", scope="auto")
        hand = _parent_rule("SMOKE-HAND", scope="hand")
        border.receive_parent_rule(gate, views, rid, auto, _mark(auto))
        border.receive_parent_rule(gate, views, rid, hand, _mark(hand))
        border.adopt_received_rule(gate, border.content_id(hand), "child-hand", scope="hand")
        active = border.active_constitution(store)
        self.assertEqual({border.content_id(auto), border.content_id(hand)}, set(active))
        self.assertEqual(active[border.content_id(auto)]["mode"], "auto")
        self.assertEqual(active[border.content_id(hand)]["mode"], "hand")


if __name__ == "__main__":
    unittest.main()
