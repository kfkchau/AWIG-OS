# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture
# vocabulary (path family, ceiling, locate source, org occupancy). NON-GOAL: no offensive
# capability of any kind — these tests DRIVE computed views (a path as a view over the five
# families with a ceiling that only shrinks; an org's class as a fold over occupancy) and the
# ceiling check's locate-by-$actor door change, by reading source and running the gate. They mint
# no attack, probe no exploit. Full declaration: SCOPE-STATEMENT.md.
"""C6 P16 — PATHS AND CEILINGS OVER FLOWS (design/52 B19, B20; F4).

A1 (B19) — a PATH is a VIEW over the five families (P4's census classifier, READ), naming its
    endpoints, their positions on the three axes, the content bands it permits and the rule it
    cites; a ceiling attaches; the content's class only TIGHTENS along it (a planted widening reds).
A2 (B18/L18) — the ceiling ONLY SHRINKS: ceilings compose by intersection; a proposed ceiling that
    would WIDEN a grant is refused; HELD sits inside CLASS MAX and STRUCTURAL MAX (I21), held
    outside reds.
A3 (B20) — an org's CLASS is a FOLD over LIVE occupancy (human-only / AI-only / mixed), never a
    stored label (a revoked occupant drops out and the fold changes); a mixed-org rule may require a
    HUMAN OCCUPANT's countersign, and its absence refuses.
A4 (F4) — a REAL ceiling row keyed by `$actor` is DRIVEN through the door: it works as a door
    change over the existing `$actor` locate source (Reading A) — no new check kind, no op-META
    param. The engine's fact (the acting actor) locates the ceiling; a caller cannot forge whose
    budget it spends.

CAP (architect's countersign, board :3650, precisions 1-2): the AXIS values (boundary, reach) and
the org membership/class VOCABULARY are not populated in the record until C6 P8's attest amendment
and the vocabulary rule land; these views read the one signal the record holds today — the
`actor_class` free string (K12) — and NAME the rest. The A4 ceiling row lives in a TEST founding
world; if the estate's own pack ever needs one, that row is founding DATA riding P8's batch, not
this unit.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
# P4's five-families census — READ and REUSED as the classifier of record (never re-authored). The
# path view NAMES the family P4 reads; this test cross-checks the two agree.
from tools.conformance.effect_order_census import build_full_kernel_for_census  # noqa: E402
from tools.conformance.five_families_census import (  # noqa: E402
    classify, _op_definition, _handler_source, FIVE_FAMILIES)


def _p4_family(gate, views, op):
    """The family P4's census reads for `op` — the classifier of record, reused verbatim."""
    d = _op_definition(views, op)
    h = _handler_source(gate, op)
    law = (d or {}).get("law_cited") if d else (gate.ops[op].get("meta") or {}).get("law_cited")
    return classify(op, d, h, law)["class"]


# =======================================================================================
class A1_PathIsAViewOverTheFiveFamilies(unittest.TestCase):
    """A1 (B19): an opened path reads as a view over the five families naming its endpoints, axis
    positions, permitted content bands and cited rule; a ceiling attaches; the class only tightens."""

    def setUp(self):
        # the census kernel is the widest composition (P4's own build) — the surface a path view
        # reads real ops over. Its Views carries the P16 additions (same class).
        self.store, self.gate, self.views = build_full_kernel_for_census()

    def test_the_view_names_the_family_P4_read_and_the_four_attributes(self):
        # a path over each of several families: the view's family is P4's own reading (reused,
        # not re-classified), and the view NAMES all four required attributes.
        for op in ("COMMS-OPEN", "HANDOVER", "MEM-GRANT"):
            fam = _p4_family(self.gate, self.views, op)
            self.assertIn(fam, self.views._PATH_FAMILY_SET)
            v = self.views.path_view(op, fam, permits={"public", "internal"}, actor="owner")
            self.assertEqual(v["family"], fam)                       # family is P4's reading
            self.assertEqual(set(v["endpoints"]), {"source", "target"})   # names its endpoints
            self.assertEqual(tuple(v["axis_positions"]["source"]),
                             self.views.THREE_AXES)                  # names the three axes
            self.assertIn("cited_rule", v)                          # names the rule it cites
            self.assertEqual(v["content_bands"], frozenset({"public", "internal"}))  # content bands

    def test_a_ceiling_attaches_and_the_source_processing_axis_reads_actor_class(self):
        v = self.views.path_view("COMMS-OPEN", "channels", permits={"public"}, actor="owner")
        self.assertEqual(v["ceiling"], frozenset({"public"}))       # a ceiling attaches to the path
        # the PROCESSING axis is populated from actor_class as it stands (owner is human); BOUNDARY
        # and REACH are the named cap (None until P8).
        self.assertEqual(v["axis_positions"]["source"]["processing"], "human")
        self.assertIsNone(v["axis_positions"]["source"]["boundary"])
        self.assertIsNone(v["axis_positions"]["source"]["reach"])

    def test_content_class_only_tightens_along_the_path(self):
        # each successive position permits a subset (narrower or equal) — tightening.
        self.assertTrue(self.views.content_tightens_along(
            [{"public", "internal", "secret"}, {"public", "internal"}, {"public"}]))

    def test_a_planted_widening_reds(self):
        # THE CONTROL THAT MUST FAIL: a later position permitting a band an earlier one did not is a
        # widening, and the check catches it.
        self.assertFalse(self.views.content_tightens_along([{"public"}, {"public", "secret"}]))

    def test_a_census_red_is_not_a_lawful_path(self):
        # P4's sixth-way / unknown are census reds, not paths — the view refuses them.
        with self.assertRaises(ValueError):
            self.views.path_view("anything", "sixth-way")


# =======================================================================================
class A2_TheCeilingOnlyShrinks(unittest.TestCase):
    """A2 (B18/L18): a ceiling only shrinks — ceilings compose by intersection, a widening is
    refused, and HELD sits inside CLASS MAX and STRUCTURAL MAX (I21)."""

    def setUp(self):
        self.store, self.gate, self.views = build_kernel(
            os.path.join(tempfile.mkdtemp(prefix="p16-a2-"), "record.jsonl"))

    def test_composition_is_intersection_and_can_only_narrow(self):
        composed = self.views.compose_ceilings({"a", "b", "c"}, {"a", "b"}, {"b", "c"})
        self.assertEqual(composed, frozenset({"b"}))                # only the common band survives
        self.assertTrue(composed <= frozenset({"a", "b", "c"}))     # never wider than any input

    def test_no_ceiling_composed_is_unbounded(self):
        self.assertIsNone(self.views.compose_ceilings())           # the pre-ceiling reading, stated

    def test_a_widening_ceiling_is_refused(self):
        # a proposed ceiling that permits a band the existing did not WIDENS — refused (never loosen).
        self.assertTrue(self.views.ceiling_widens({"a", "b"}, {"a", "b", "c"}))

    def test_a_narrowing_or_equal_ceiling_widens_nothing(self):
        self.assertFalse(self.views.ceiling_widens({"a", "b"}, {"a"}))
        self.assertFalse(self.views.ceiling_widens({"a", "b"}, {"a", "b"}))

    def test_held_inside_both_envelopes_is_ok(self):
        # I21: HELD sits inside CLASS MAX and STRUCTURAL MAX.
        self.assertTrue(self.views.held_within_envelopes(
            held={"a"}, class_max={"a", "b"}, structural_max={"a", "c"}))

    def test_held_outside_class_max_reds(self):
        # THE I21 CONTROL THAT MUST FAIL: held carries a band the class max does not permit.
        self.assertFalse(self.views.held_within_envelopes(
            held={"b"}, class_max={"a"}, structural_max={"a", "b"}))

    def test_held_outside_structural_max_reds(self):
        self.assertFalse(self.views.held_within_envelopes(
            held={"c"}, class_max={"a", "c"}, structural_max={"a"}))


# =======================================================================================
class A3_OrgClassIsAFoldOverLiveOccupancy(unittest.TestCase):
    """A3 (B20): an org's class is a fold over live occupancy (never a stored label); a mixed-org
    rule may require a human occupant's countersign, and its absence refuses.

    CAP: occupancy is read from LIVE grants at the org node (a founded space), each occupant's class
    from the `actor_class` field AS IT STANDS today (K12: no declared domain until P8). The classify-
    act version of the class arrives with P8 and this test is re-driven then."""

    def setUp(self):
        self.store, self.gate, self.views = build_kernel(
            os.path.join(tempfile.mkdtemp(prefix="p16-a3-"), "record.jsonl"))
        m = self.views.mother_space()
        for nm in ("orgH", "orgA", "orgM"):
            self.gate.execute("CREATE-SPACE", "owner", {"name": nm, "parent": m})
        for aid, cls in (("anna", "human"), ("brit", "human"),
                         ("cyra", "ai"), ("dane", "ai")):
            self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": aid, "actor_class": cls})

    def _grant(self, gid, who, space):
        self.gate.execute("GRANT", "owner", {"grant_id": gid, "grantee": who,
                                             "actions": "read", "info": "doc", "space": space})

    def test_org_class_folds_occupancy_into_human_only_ai_only_mixed(self):
        self._grant("h1", "anna", "space:orgH"); self._grant("h2", "brit", "space:orgH")
        self._grant("a1", "cyra", "space:orgA"); self._grant("a2", "dane", "space:orgA")
        self._grant("m1", "anna", "space:orgM"); self._grant("m2", "cyra", "space:orgM")
        self.assertEqual(self.views.org_class("space:orgH"), "human-only")
        self.assertEqual(self.views.org_class("space:orgA"), "AI-only")
        self.assertEqual(self.views.org_class("space:orgM"), "mixed")

    def test_the_class_is_a_live_fold_never_a_stored_label(self):
        # a member leaving (its grant revoked) changes the class — the fold is live, not stamped.
        self._grant("m1", "anna", "space:orgM"); self._grant("m2", "cyra", "space:orgM")
        self.assertEqual(self.views.org_class("space:orgM"), "mixed")
        self.gate.execute("REVOKE", "owner", {"grant_id": "m2"})     # cyra (ai) leaves
        self.assertEqual(self.views.org_occupants("space:orgM"), frozenset({"anna"}))
        self.assertEqual(self.views.org_class("space:orgM"), "human-only")

    def test_an_empty_org_folds_to_none(self):
        self.assertIsNone(self.views.org_class("space:orgH"))       # no live occupant

    def test_a_mixed_org_requires_a_human_occupants_countersign_absence_refuses(self):
        self._grant("m1", "anna", "space:orgM"); self._grant("m2", "cyra", "space:orgM")
        self.assertEqual(self.views.org_class("space:orgM"), "mixed")
        # ABSENCE REFUSES: no human occupant among the countersigners.
        self.assertFalse(self.views.mixed_org_countersign_ok("space:orgM", countersigners=["cyra"]))
        self.assertFalse(self.views.mixed_org_countersign_ok("space:orgM", countersigners=[]))
        # a HUMAN OCCUPANT's countersign satisfies it.
        self.assertTrue(self.views.mixed_org_countersign_ok("space:orgM", countersigners=["anna"]))

    def test_a_countersigner_who_is_not_a_live_human_occupant_does_not_satisfy(self):
        self._grant("m1", "anna", "space:orgM"); self._grant("m2", "cyra", "space:orgM")
        # brit is human but is NOT an occupant of orgM — a non-occupant does not satisfy the rule.
        self.assertFalse(self.views.mixed_org_countersign_ok("space:orgM", countersigners=["brit"]))

    def test_a_non_mixed_org_does_not_bind_the_countersign_rule(self):
        self._grant("h1", "anna", "space:orgH")
        self.assertTrue(self.views.mixed_org_countersign_ok("space:orgH", countersigners=[]))


# =======================================================================================
class A4_TheCeilingLocatesByActorDriven(unittest.TestCase):
    """A4 (F4): a REAL ceiling row keyed by `$actor` driven through the door — Reading A (a door
    change over the existing `$actor` locate, no new kind). `holder_param` names the literal
    `"$actor"`, so the ceiling locates the ACTING entity (the engine's fact), and `stamp_actor`
    makes the folded holder field the actor too — a caller cannot forge whose budget it spends.

    This is the confirm-by-driving A4 the plan requires: the row expresses cleanly through the
    existing kind, so Reading A ships and Reading B (one new kind + the owner's word) is NOT raised.
    The op lives in this TEST founding world (architect's precision 1)."""

    #: A $actor-keyed ceiling op, founded at runtime (CREATE-OP under the founding-openness grant),
    #: modelled on MEM-GRANT with ONE flip: the ceiling check's `holder_param` is the literal
    #: "$actor" (the door change), and the holder field is `stamp_actor`-stamped so the record's
    #: holder is the actor unforgeably.
    OP_DEF = {
        "kind": "op_definition", "rule_id": "op:P16-GRANT", "polarity": "+",
        "name": "P16-GRANT", "tier": "owner",
        "text": "operation P16-GRANT: when invoked and its checks pass -> append citing MEM-LAW-ALLOC",
        "definition": {
            "description": "a $actor-keyed ceiling grant (C6 P16 A4 — locate by the engine's fact)",
            "params": {"region": "required", "size": "required"},
            "law_cited": "MEM-LAW-ALLOC",
            "param_kinds": {"size": "quantity"},
            "object_param": "region",
            "payload_from": ["region", "holder", "size"],
            "stamp_actor": ["holder"],   # the folded holder field is the actor, unforgeable
            "checks": [{
                "check": "ceiling",
                "policy_key_prefix": "budget:",
                "holder_param": "$actor",      # THE DOOR CHANGE: locate by the acting entity
                "aggregate_action": "P16-GRANT",
                "holder_field": "holder",
                "key_param": "region",
                "aggregate_field": "size",
                "removal_action": "P16-EVICT",
                "amount_param": "size",
                "cite": "MEM-LAW-BUDGET",
            }],
            "mints": ["region"],
            "structural_params": ["region", "size"],
        },
    }

    def setUp(self):
        self.store, self.gate, self.views = build_kernel(
            os.path.join(tempfile.mkdtemp(prefix="p16-a4-"), "record.jsonl"))
        self.gate.execute("CREATE-OP", "PC_RUNTIME", {"object": "op:P16-GRANT", **self.OP_DEF})
        self.assertIn("P16-GRANT", self.gate.ops)      # the $actor-keyed op is live

    def test_the_row_expresses_through_the_existing_kind_no_new_kind_needed(self):
        # Reading A CONFIRMED: the ceiling check kind admitted the $actor-keyed declaration at the
        # founding door (no new kind minted, no op-META param declared — a locate source is not a
        # param). If this founding had refused, A4 would be a Reading-B raise; it does not.
        self.assertEqual(self.views.op_definitions()["P16-GRANT"]["definition"]["checks"][0]["holder_param"],
                         "$actor")

    def test_the_ceiling_locates_the_actors_own_budget_and_refuses_over_it(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "alice", "ceiling": 100})
        rec = self.gate.execute("P16-GRANT", "alice", {"region": "r1", "size": 60})
        self.assertEqual(rec["payload"]["holder"], "alice")        # recorded under the actor
        with self.assertRaises(OpError) as cm:
            self.gate.execute("P16-GRANT", "alice", {"region": "r2", "size": 50})   # 60+50 > 100
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")

    def test_a_caller_cannot_forge_whose_budget_it_spends(self):
        # THE ENGINE'S-FACT CONTROL: alice tries to spend under bob's huge budget by passing
        # holder=bob. stamp_actor overwrites the record's holder to alice AND holder_param="$actor"
        # locates budget:alice regardless of the caller's claim — so the forge is refused. This is
        # the difference from param_defaults (which only fills an ABSENT key and is overridable).
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "alice", "ceiling": 100})
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "bob", "ceiling": 10 ** 9})
        self.gate.execute("P16-GRANT", "alice", {"region": "r1", "size": 100})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("P16-GRANT", "alice",
                              {"region": "r2", "size": 50, "holder": "bob"})
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")       # bound by alice's budget, not bob's

    def test_the_budget_is_per_actor_the_engines_fact(self):
        # two actors, each bound by their OWN budget under the same $actor-keyed row — the locate is
        # the acting entity, so one actor's grants never consume another's budget.
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "alice", "ceiling": 100})
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "carol", "ceiling": 100})
        self.gate.execute("P16-GRANT", "alice", {"region": "r1", "size": 100})
        self.gate.execute("P16-GRANT", "carol", {"region": "r2", "size": 100})   # carol's own 100
        with self.assertRaises(OpError):
            self.gate.execute("P16-GRANT", "alice", {"region": "r3", "size": 1})  # alice is full


if __name__ == "__main__":
    unittest.main()
