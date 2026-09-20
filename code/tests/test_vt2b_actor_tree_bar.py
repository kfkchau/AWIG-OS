"""C6a VT-2b — THE ACTOR-TREE BAR AT THE WRITE CHOKEPOINT (no-orphan / no-loop, GENERAL).

Named in planning/exec/VT-2b-ACTOR-TREE-BAR-CHOKEPOINT-BUILD.md before code, landed here as
regression tests (charter: every verification probe lands as a regression test). This battery proves
the no-orphan / no-loop actor-tree bar MOVED from the interpreter (opdefs, VT-2) to the DECIDE-CHAIN
WRITE CHOKEPOINT (gate._relation_tree_step), keyed on the DERIVED row's geometry + both ends, so ANY
op minting a containment relation row — not only CREATE-RELATIONSHIP — is caught where every write
converges (design/25 v2.1 ruling 23; design/53 §7 row VT-2b; the VT-2 close :3811, judgment 2's cap).

  A1  THE BAR AT THE WRITE CHOKEPOINT, GENERAL. The no-orphan / no-loop bar runs at gate._decide,
      keyed on the DERIVED row's geometry + both ends. An orphan (a group that does not reach the
      root) or a loop is refused there for CREATE-RELATIONSHIP; a grounded row with MANY PARENTS
      passes. And a PLANTED SECOND relation-minting op — a NATIVE handler that never runs the opdefs
      interpreter, the case an interpreter-resident bar would MISS — producing an orphan or a loop is
      refused AT THE CHOKEPOINT; a grounded row it mints PASSES (the bar is general both ways).
  A2  THE INTERPRETER BAR RETIRED, NO GAP. The opdefs interpreter bar is retired (its live code is
      gone; a retired-here marker stands in its place); the chokepoint step is wired unconditionally
      into gate._decide. The no-gap proof against the LIVE tree is tests.test_vt2_relation staying
      green (run separately, evidence in planning/evidence/VT-2b-ACTOR-TREE-BAR/); here the orphan /
      loop are shown still refused with the interpreter bar gone.
  A3  THE CENSUS: EVERY RELATION-MINTING OP PASSES THE BAR, ABLE TO FAIL. The census enumerates the
      ops that declare the containment-relation shape (CREATE-RELATIONSHIP) and confirms each subject
      to the bar; the record-level RED SET is EMPTY on a guarded world and REDS on a PLANTED
      PASS-THROUGH — a direct store append of an ungrounded containment row, bypassing the decide
      chain (the check that can fail; the cap VT-2 named becomes a caught condition).
  A4  NO FOUNDING. Asserted by the harness pin (git diff empty) — carried in the evidence, not here.

Every acceptance carries its RED WORLD, driven THROUGH the gate (a control that cannot red is the
defect, §A42/§A64).
"""

import inspect
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                                   # noqa: E402
from kernel.errors import OpError                                      # noqa: E402
from kernel import gate as gate_mod                                    # noqa: E402
from kernel import opdefs as opdefs_mod                                # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from conformance import relation_bar_census as census                 # noqa: E402


def _kernel(prefix="vt2b_"):
    d = tempfile.mkdtemp(prefix=prefix)
    return build_kernel(os.path.join(d, "record.jsonl"))


# A PLANTED SECOND RELATION-MINTING OP — a NATIVE handler (no opdefs definition), so it NEVER runs
# the interpreter: the case an interpreter-resident bar would miss and the chokepoint must catch.
_PLANT_OP = "PLANT-CONTAINMENT"


def _register_plant(gate):
    def _handler(actor, params):
        return {"actor": actor, "action": _PLANT_OP, "object": params.get("subject"),
                "rule_cited": "CAP-IS-LAW",            # H3: a governed record cites a rule (native op stamps its own)
                "payload": {"geometry": params.get("geometry", "NS"),
                            "subject": params.get("subject"), "object": params.get("object")}}
    gate.register(_PLANT_OP, {"params": {}, "rules": ["CAP-IS-LAW"]}, _handler)


class BarAtTheChokepoint(unittest.TestCase):
    """A1 — the bar runs at the write chokepoint, keyed on the derived row, GENERAL across ops."""

    def setUp(self):
        self.store, self.gate, self.views = _kernel()
        _register_plant(self.gate)
        self.assertTrue(self.views.actor_grounded("owner"),
                        "the founding anchor 'owner' is not grounded — the anchor floor is wrong")

    def _actor(self, aid):
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": aid})

    def _nest(self, subject, group, geometry="NS"):
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": subject, "object": group, "geometry": geometry})

    def _plant(self, subject, group, geometry="NS"):
        self.gate.execute(_PLANT_OP, "owner",
                          {"subject": subject, "object": group, "geometry": geometry})

    # ---- the canonical op (CREATE-RELATIONSHIP) still refused / admitted at the chokepoint ----

    def test_orphan_refused_at_the_chokepoint(self):
        self._actor("loose_grp"); self._actor("orphan_child")
        self.assertFalse(self.views.actor_grounded("loose_grp"))
        with self.assertRaises(OpError) as cm:
            self._nest("orphan_child", "loose_grp")
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        self.assertFalse(self.views.actor_grounded("orphan_child"))

    def test_loop_refused_at_the_chokepoint(self):
        self._actor("x")
        self._nest("x", "owner")                       # x under the anchor -> grounded
        with self.assertRaises(OpError) as cm:         # owner under x would loop: owner -> x -> owner
            self._nest("owner", "x")
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_grounded_many_parents_passes(self):
        self._actor("grp1"); self._actor("grp2"); self._actor("member")
        self._nest("grp1", "owner"); self._nest("grp2", "owner")
        self._nest("member", "grp1")
        self.assertTrue(self.views.actor_grounded("member"))
        self._nest("member", "grp2")                   # a second grounded parent — lawful
        self.assertEqual(len(self.store.by_action("CREATE-RELATIONSHIP")), 4)

    # ---- THE PLANTED SECOND OP — a native handler the interpreter never sees ----

    def test_planted_second_op_orphan_refused_at_the_chokepoint(self):
        # the case the interpreter bar alone would MISS: a native op mints a containment row without
        # ever running the opdefs interpreter; the chokepoint bar (keyed on the derived row) catches it.
        self._actor("loose_grp"); self._actor("orphan_child")
        with self.assertRaises(OpError) as cm:
            self._plant("orphan_child", "loose_grp")
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        # nothing recorded under the planted op's action — refused at the chokepoint before the write
        self.assertEqual(self.store.by_action(_PLANT_OP), [])

    def test_planted_second_op_loop_refused_at_the_chokepoint(self):
        self._actor("x")
        self._nest("x", "owner")                       # x grounded under the anchor
        with self.assertRaises(OpError) as cm:         # native op nesting owner under x -> loop
            self._plant("owner", "x")
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.store.by_action(_PLANT_OP), [])

    def test_planted_second_op_grounded_row_passes(self):
        # the bar is general BOTH ways: a native op minting a row whose group `object` GROUNDS is
        # admitted at the chokepoint (the bar's predicate is the object's grounding).
        self._actor("grp"); self._actor("member")
        self._nest("grp", "owner")                     # grp grounded via a CREATE-RELATIONSHIP edge
        self.assertTrue(self.views.actor_grounded("grp"))
        self._plant("member", "grp")                   # member under a grounded group -> admitted, appends
        self.assertEqual(len(self.store.by_action(_PLANT_OP)), 1)

    def test_non_containment_row_is_untouched_by_the_bar(self):
        # a TOUCHING (AD) relation is non-tree — the chokepoint bar must NOT fire even under a
        # non-grounded object between two established actors.
        self._actor("p"); self._actor("q")
        self._nest("p", "q", geometry="AD")            # no raise
        self.assertEqual(len(self.store.by_action("CREATE-RELATIONSHIP")), 1)


class InterpreterBarRetiredNoGap(unittest.TestCase):
    """A2 — the interpreter bar is retired and the chokepoint step is wired; no gap."""

    def test_the_chokepoint_step_is_wired_unconditionally_in_decide(self):
        decide_src = inspect.getsource(gate_mod.Gate._decide)
        self.assertIn("self._relation_tree_step(actor, name, result)", decide_src,
                      "the chokepoint bar is not called in gate._decide")
        # it is an UNCONDITIONAL statement in the one decide path (not nested behind an op name)
        self.assertTrue(hasattr(gate_mod.Gate, "_relation_tree_step"))

    def test_the_interpreter_bar_is_retired(self):
        # the live interpreter code that refused here is GONE; a retired-here marker stands in place.
        src = inspect.getsource(opdefs_mod)
        self.assertIn("THE ACTOR-TREE BAR — RETIRED HERE", src,
                      "the retired-here marker is missing from opdefs")
        self.assertNotIn("_geo = p_in.get(\"geometry\")", src,
                         "the retired interpreter bar's live code is still present in opdefs")

    def test_orphan_and_loop_still_refused_with_the_interpreter_bar_gone(self):
        # the no-gap property, shown live: the orphan / loop the interpreter bar used to refuse are
        # still refused, now by the chokepoint bar (the full battery is tests.test_vt2_relation).
        store, gate, views = _kernel()
        gate.execute("CREATE-ACTOR", "owner", {"actor_id": "loose_grp"})
        gate.execute("CREATE-ACTOR", "owner", {"actor_id": "child"})
        with self.assertRaises(OpError):
            gate.execute("CREATE-RELATIONSHIP", "owner",
                         {"subject": "child", "object": "loose_grp", "geometry": "NS"})
        gate.execute("CREATE-ACTOR", "owner", {"actor_id": "x"})
        gate.execute("CREATE-RELATIONSHIP", "owner", {"subject": "x", "object": "owner", "geometry": "NS"})
        with self.assertRaises(OpError):
            gate.execute("CREATE-RELATIONSHIP", "owner", {"subject": "owner", "object": "x", "geometry": "NS"})


class TheCensusAbleToFail(unittest.TestCase):
    """A3 — the census enumerates relation-minting ops and REDS on a planted pass-through."""

    def setUp(self):
        self.store, self.gate, self.views = _kernel()

    def test_reading1_enumerates_create_relationship_subject_to_the_bar(self):
        minting = census.relation_minting_ops(self.gate, self.views)
        names = {r["op"] for r in minting}
        self.assertIn("CREATE-RELATIONSHIP", names,
                      "the census did not enumerate CREATE-RELATIONSHIP as a relation-minting op")
        self.assertTrue(all(r["subject_to_bar"] for r in minting),
                        "a relation-minting op is not reported subject to the chokepoint bar")

    def test_reading2_empty_on_a_guarded_world(self):
        # lawful grounded rows: the record holds no ungrounded containment row.
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": "grp"})
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": "member"})
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": "grp", "object": "owner", "geometry": "NS"})
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": "member", "object": "grp", "geometry": "NS"})
        self.assertEqual(census.rows_past_the_bar(self.store, self.views), [],
                         "the census red set is non-empty on a world the bar guarded")

    def test_reading2_reds_on_a_planted_passthrough(self):
        # THE CHECK THAT CAN FAIL: a direct store append of an ungrounded containment row, bypassing
        # the decide chain (an external executor / a handler appending directly) — the pass-through
        # the cap VT-2 named. The census FINDS it.
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": "loose_grp"})
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": "orphan_child"})
        # sanity: clean before the plant
        self.assertEqual(census.rows_past_the_bar(self.store, self.views), [])
        self.store._append({"actor": "owner", "action": "SNEAK-REL", "object": "orphan_child",
                            "rule_cited": "CAP-IS-LAW",
                            "payload": {"geometry": "NS", "subject": "orphan_child",
                                        "object": "loose_grp"}})
        red = census.rows_past_the_bar(self.store, self.views)
        self.assertEqual(len(red), 1, "the census did not red on the planted pass-through")
        self.assertEqual(red[0]["subject"], "orphan_child")
        self.assertEqual(red[0]["object"], "loose_grp")
        self.assertEqual(red[0]["why"], "orphan")


if __name__ == "__main__":
    unittest.main()
