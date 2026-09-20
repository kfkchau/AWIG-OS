"""C6a VT-2 — THE RELATION ROW AND ITS OPERATION; NO-ORPHAN / NO-LOOP EXTENDED TO ACTORS.

Named in planning/exec/VT-2-RELATION-ROW-AND-OP-BUILD.md before code, landed here as regression
tests (charter: every verification probe lands as a regression test). This battery proves the
MINT of the named-pending operation CREATE-RELATIONSHIP and the extension of the gate's
no-orphan / no-loop refusal from spaces to actors (design/25 v2.1 rulings 6/7/23; design/53
B5/B6/B7/B12).

  A1  THE RELATION OPERATION IS LIVE, WITH B5'S DOOR CONTROL. CREATE-RELATIONSHIP mints a relation
      row {subject, object, geometry, zone} through the gate; the _relationships fold reads the NEW
      shape; NO rel_kind is stored (the frame derives from rule_cited, surfaced as `frame`). RED
      (the check that CAN fail): a row with NO geometry, and a row with a geometry OUTSIDE the
      closed set {AD, IN, NS, EM}, are each REFUSED AT THE DOOR.
  A2  NO ORPHAN ACTOR (ruling 23). A containment (NS/EM) relation whose group `object` reaches the
      constitution's root group passes; MANY PARENTS lawful. RED: a planted orphan — a containment
      edge under a group that does not itself ground — is refused at the gate.
  A3  NO LOOP (ruling 23). RED: a planted cycle — nesting a group inside its own descendant — is
      refused at the gate, mirroring the space loop refusal.
  A4  THE PACK MOVES ONCE, LAWFULLY. founding_version 1.51.0 -> 1.52.0 (ONE MINOR); op-population
      93 -> 94 (one op MINTED live); the cell is S; geometry and zone are declared STRUCTURAL; the
      geometry value_domain is present. The bump-attestation (version + pack sha256) is one
      BUILD-PROGRESS entry.
  A5  NO NEW CHECK KIND. OP_CHECKS is UNCHANGED at 19; the geometry door rides the EXISTING
      value_domain kind and the actor guard rides the EXISTING anchor least-fixpoint — no op-check
      kind minted, no new law.

THE WRONG REFERENCES REFUSED BY NAME (the plan's traps):
  the SHAPE {from, to, rel_kind} — the retired first-mint placeholder; the row is {subject, object,
  geometry, zone} and NO rel_kind is stored (ruling 7). This battery reads the new keys and asserts
  rel_kind is ABSENT.
  AUTHORITY-AS-A-RELATION-ROW (ruling 7) — a containment row carries no power; the actor guard is
  grounding structure, never an authority grant.
  the SPACE guard is UNTOUCHED — space_tree / mother_space / would_cycle are mirrored, never
  re-authored; the actor guard reads relation rows through a NEW least-fixpoint that rides the
  _verified_accounts shape.

Every acceptance carries its RED WORLD, driven THROUGH the gate (a control that cannot red is the
defect, §A42/§A64).
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                                  # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.opdefs import OP_CHECKS                                   # noqa: E402
from founding.install import founding_version                        # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_PACK = os.path.join(_ROOT, "src", "founding", "founding-pack.json")
_LOG = os.path.join(_ROOT, "planning", "build", "BUILD-PROGRESS_v3.md")


def _kernel(prefix="vt2_"):
    d = tempfile.mkdtemp(prefix=prefix)
    return build_kernel(os.path.join(d, "record.jsonl"))


class RelationOperationIsLive(unittest.TestCase):
    """A1 — the operation is live, the fold reads the new shape, the door refuses a bad geometry."""

    def setUp(self):
        self.store, self.gate, self.views = _kernel()

    def test_the_op_is_live_and_mints_the_new_row_shape(self):
        self.assertTrue(self.gate.has("CREATE-RELATIONSHIP"),
                        "CREATE-RELATIONSHIP is not live — the named-pending op was not minted")
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": "a", "object": "b", "geometry": "AD", "zone": "edge"})
        rows = self.views._relationships()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["subject"], "a")
        self.assertEqual(row["object"], "b")
        self.assertEqual(row["geometry"], "AD")
        self.assertEqual(row["zone"], "edge")
        # the frame DERIVES from the act's cited rule (ruling 6) — never a stored rel_kind
        self.assertEqual(row["frame"], "CAP-IS-LAW")
        self.assertNotIn("rel_kind", row, "the retired {from,to,rel_kind} shape leaked back in")
        self.assertNotIn("from", row)
        self.assertNotIn("to", row)

    def test_zone_is_optional(self):
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": "a", "object": "b", "geometry": "IN"})
        row = self.views._relationships()[0]
        self.assertIsNone(row["zone"], "zone is optional — an absent zone stores None")

    def test_B5_control_no_geometry_is_refused_at_the_door(self):
        # THE CHECK THAT CAN FAIL: unrelated is never stored, so a row with NO geometry is refused.
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-RELATIONSHIP", "owner", {"subject": "a", "object": "b"})
        self.assertEqual(self.views._relationships(), [], "a no-geometry row was recorded")

    def test_B5_control_out_of_domain_geometry_is_refused_at_the_door(self):
        # THE CHECK THAT CAN FAIL: a geometry outside the closed venn2 set {AD, IN, NS, EM}.
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-RELATIONSHIP", "owner",
                              {"subject": "a", "object": "b", "geometry": "XX"})
        self.assertEqual(self.views._relationships(), [], "an out-of-domain geometry row was recorded")

    def test_each_closed_geometry_value_is_admitted(self):
        for g in ("AD", "IN", "NS", "EM"):
            s, gate, _ = _kernel()
            gate.execute("CREATE-RELATIONSHIP", "owner",
                         {"subject": "x", "object": "y", "geometry": g})


class NoOrphanActor(unittest.TestCase):
    """A2 (ruling 23) — an actor grounds at the constitution's root group; an orphan is refused."""

    def setUp(self):
        self.store, self.gate, self.views = _kernel()
        # owner is a founding anchor — the constitution's root group grounds it.
        self.assertTrue(self.views.actor_grounded("owner"),
                        "the founding anchor 'owner' is not grounded — the anchor floor is wrong")

    def _actor(self, aid):
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": aid})

    def _nest(self, subject, group, geometry="NS"):
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": subject, "object": group, "geometry": geometry})

    def test_a_chain_to_the_root_group_grounds_and_many_parents_are_lawful(self):
        self._actor("grp1"); self._actor("grp2"); self._actor("member")
        self._nest("grp1", "owner")            # grp1 nested in the anchor -> grounded
        self.assertTrue(self.views.actor_grounded("grp1"))
        self._nest("grp2", "owner")            # a second grounded group
        self._nest("member", "grp1")           # member under grp1 -> grounded
        self.assertTrue(self.views.actor_grounded("member"))
        # MANY PARENTS: member nested in a SECOND grounded group — lawful, both chains reach root
        self._nest("member", "grp2")
        self.assertEqual(len(self.store.by_action("CREATE-RELATIONSHIP")), 4)

    def test_control_a_planted_orphan_is_refused_at_the_gate(self):
        # an unattached group does NOT reach the root; nesting a child under it would orphan the child
        self._actor("loose_grp"); self._actor("orphan_child")
        self.assertFalse(self.views.actor_grounded("loose_grp"))
        with self.assertRaises(OpError):
            self._nest("orphan_child", "loose_grp")
        self.assertFalse(self.views.actor_grounded("orphan_child"))

    def test_a_non_containment_relation_is_not_an_actor_tree_edge(self):
        # a TOUCHING (AD) relation is non-tree — the actor guard must NOT fire, even under a
        # non-grounded object, and even between two established actors.
        self._actor("p"); self._actor("q")
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": "p", "object": "q", "geometry": "AD"})   # no raise
        self.assertEqual(len(self.store.by_action("CREATE-RELATIONSHIP")), 1)


class NoLoop(unittest.TestCase):
    """A3 (ruling 23) — a cyclic actor-group chain is refused at the gate, mirroring the space loop."""

    def setUp(self):
        self.store, self.gate, self.views = _kernel()

    def _actor(self, aid):
        self.gate.execute("CREATE-ACTOR", "owner", {"actor_id": aid})

    def _nest(self, subject, group):
        self.gate.execute("CREATE-RELATIONSHIP", "owner",
                          {"subject": subject, "object": group, "geometry": "NS"})

    def test_control_a_direct_cycle_is_refused(self):
        self._actor("x")
        self._nest("x", "owner")               # x under the anchor -> grounded
        with self.assertRaises(OpError):       # owner under x would loop: owner -> x -> owner
            self._nest("owner", "x")

    def test_control_a_transitive_cycle_is_refused(self):
        self._actor("x"); self._actor("y")
        self._nest("x", "owner")
        self._nest("y", "x")                    # y -> x -> owner
        with self.assertRaises(OpError):        # owner under y would loop: owner -> y -> x -> owner
            self._nest("owner", "y")


class ThePackMovesOnceLawfully(unittest.TestCase):
    """A4 — one MINOR bump, op-population +1, the cell and structural params declared, attested."""

    def setUp(self):
        self.store, self.gate, self.views = _kernel()

    def test_founding_version_bumped_one_minor(self):
        # VT-2's own move was the 1.51.0 -> 1.52.0 MINOR. This reads the LIVE version, so it is a §A57
        # live-version pin: C6a VT-3 (THE TREE SEEDED AS ROWS — 35 view rows) moved it 1.52.0 -> 1.53.0,
        # then C6a VT-6d (THE STAMP FOUNDING — the required-stamps policy rule) moved it 1.53.0 -> 1.54.0
        # BY NAME (§A57), the standing "re-pinned by the last founding mover" idiom; then C7 P3 (THE KERNEL
        # FROM THE RECORD — the twelve act-kind rows) moved it 1.54.0 -> 1.55.0 BY NAME (§A57).
        self.assertEqual(founding_version(), "1.55.0")

    def test_op_population_moved_by_one_mint(self):
        defs = self.views.op_definitions()          # {name: definition}, head-memoised
        self.assertEqual(len(defs), 94, "op-population did not move 93 -> 94 by the one mint")
        self.assertIn("CREATE-RELATIONSHIP", defs)

    def test_the_op_declares_cell_S_and_structural_geometry_and_zone(self):
        rel = self.views.op_definitions()["CREATE-RELATIONSHIP"]["definition"]
        self.assertEqual(rel.get("cell"), "S")
        structural = set(rel.get("structural_params") or [])
        self.assertIn("geometry", structural)
        self.assertIn("zone", structural)
        # the door validates the closed geometry domain BEFORE the handler (the op-amend lesson)
        checks = {c["check"] for c in (rel.get("checks") or [])}
        self.assertIn("value_domain", checks)

    @unittest.skipUnless(
        os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/build/BUILD-PROGRESS_v3.md")),
        "SKIP PRIVATE-SOURCE: needs planning/build/BUILD-PROGRESS_v3.md (absent in the render)")
    def test_the_bump_is_attested_in_one_BUILD_PROGRESS_entry(self):
        with open(_PACK, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        with open(_LOG, "r", encoding="utf-8") as fh:
            log = fh.read()
        self.assertIn("1.52.0", log, "no BUILD-PROGRESS entry names the new founding version")
        self.assertIn(sha, log, "no BUILD-PROGRESS entry names the pack sha256 (the attestation)")


class NoNewCheckKind(unittest.TestCase):
    """A5 — OP_CHECKS is unchanged at 19; the door and the guard ride existing mechanisms."""

    def test_op_checks_unchanged_at_19_and_value_domain_reused(self):
        self.assertEqual(len(OP_CHECKS), 19, "a check kind was added — the vocabulary must not grow")
        self.assertIn("value_domain", OP_CHECKS)     # the geometry door rides this existing kind
        self.assertIn("space_tree", OP_CHECKS)        # the space guard's kind — untouched


if __name__ == "__main__":
    unittest.main()
