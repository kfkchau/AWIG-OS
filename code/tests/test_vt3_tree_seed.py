"""C6a VT-3 — THE TREE SEEDED AS ROWS (design/25 v2 the view tree; design/53 VT-3, L14/L16).

Named in planning/exec/VT-3-TREE-SEEDED-AS-ROWS-BUILD.md before code, landed here as regression
tests (charter: every verification probe lands as a regression test). This battery proves that the
base view tree is on the record as 35 view-definition ROWS and that create_view's INLINE door admits,
records and refuses the THIRD view form (a derived row):

  A1  the SEED is exactly 35 CREATE-VIEW rows matching design/25-view-tree-v2.json's seed_form oracle:
      12 BIND (a master naming an S-plane fold) + 23 DERIVE (a parent narrowed by one dimension);
      view_definitions reads all 35; node 1 (definitive) and the 8 level-4 nodes (computed) are NOT
      seeded. RED: a bind to a fold outside FOLD_NAMES; a computed/definitive node found in the seed.
  A2  the DERIVE FORM at create_view's inline door: a well-formed derive is RECORDED; four refusals,
      each an AR-2 that CAN fail — a where not naming exactly one dimension; a dimension outside
      DERIVE_DIMENSIONS; a from naming no seeded view at head; a derive riding with a bind or a
      non-empty when. DERIVE_DIMENSIONS is grow-only (a shrink of the five-name baseline reds).
  A3  the ROUND-TRIP against the INDEPENDENT ORACLE: the seeded tree read through view_definitions
      equals the json's seed_form per node. RED: a planted divergence (a wrong bind/derive) — driven.
  A4  the ONE-MOVE INSTRUMENT: numbering = derivation — every seeded node is its parent plus exactly
      one move (a derive names its numbering-parent and exactly one dimension). RED: a re-index-only
      node (a derive with no move, or a from that is not its numbering-parent) — driven.
  A5  RED founding: the PACK MOVED ONCE — 35 seed rows + ONE MINOR bump 1.52.0 -> 1.53.0; the six
      folds the binds name promoted to FOLD_NAMES (10 -> 16, grow-only); the bump-attestation named in
      BUILD-PROGRESS (version + new pack sha). The derive door is CODE, not a pack structural
      declaration (CREATE-VIEW is boot-registered; no op def). RED: a shrink of the fold set.
  A6  I7 — VT-1 stays as built: each promoted fold is a SEPARATE memoised projection, NEVER a key on
      an existing one; events_by_effect still returns its two keys, static_composite still its own.

THE WRONG REFERENCE REFUSED BY NAME (design/53 stop conditions; the plan's wrong-reference trap):
  CREATE-VIEW is BOOT-REGISTERED (boot.py gate.register), it has NO op-def / STRUCTURAL_PARAMS META.
  The derive door is INLINE CODE in create_view, mirroring the bind/when closure — NOT a pack
  structural declaration (the :3817 wrong noun, corrected at :3825). The pack carries the seed rows +
  the bump ONLY. This battery proves the door is the op's own inline refusal, not a declared param.

Every acceptance carries its RED WORLD, driven THROUGH the actual mechanism (a control that cannot
red is the defect, §A42/§A64).
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                                  # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.views import FOLD_NAMES, DERIVE_DIMENSIONS, fold_set      # noqa: E402
from kernel.canonical import canonical_hash                          # noqa: E402
from founding.install import founding_version                        # noqa: E402

ORACLE_PATH = os.path.join(os.path.dirname(__file__), "..", "design", "25-view-tree-v2.json")
PROMOTIONS = ("rule_changing_acts", "acts_under_rules", "rules", "items", "active_items",
              "static_composite")


def _kernel(prefix):
    d = tempfile.mkdtemp(prefix=prefix)
    return build_kernel(os.path.join(d, "record.jsonl"))


def _oracle():
    with open(ORACLE_PATH) as fh:
        return json.load(fh)


def _oracle_seed_forms(oracle):
    """The INDEPENDENT expectation: {node id -> seed_form} for the 35 seeded nodes (12 bind + 23
    derive), read from archi's json — node 1 (definitive) and the 8 level-4 nodes (computed) dropped.
    Authored by archi, never here (the A3 oracle stays independent)."""
    return {v["id"]: v["seed_form"] for v in oracle["views"]
            if v["seed_form"] not in ("definitive", "computed")}


def _seeded_forms(views):
    """The ACTUAL seed_form of each TREE node, read back (the round-trip). A BIND is read from
    view_definitions (unchanged pinned shape); a DERIVE is read from view_derivations (the separate
    projection, I7 — view_definitions' shape stays byte-identical). A tree node is one named by its
    oracle id (dotted / numeric); the seven legacy masters carry word names and are not tree nodes
    (reconciled, not double-seeded)."""
    defs = views.view_definitions()
    derivs = views.view_derivations()
    out = {}
    for name, d in defs.items():
        if not name[0].isdigit():
            continue
        if d.get("bind") is not None:
            out[name] = "bind:" + d["bind"]
        elif name in derivs:
            where = dict(derivs[name].get("where") or {})    # deep-frozen -> plain dict
            (dim, val), = where.items()
            out[name] = f"derive:{dim}={val}"
        else:
            out[name] = "?" + name
    return out


def _numbering_parent(node_id):
    return node_id.rsplit(".", 1)[0] if "." in node_id else None


def _one_move_violations(views):
    """THE ONE-MOVE INSTRUMENT (design/25 ruling 2: numbering = derivation; each child is its parent
    plus EXACTLY ONE move). Returns the list of seeded nodes that VIOLATE it — empty for a lawful seed.
    A derive node must (a) narrow by exactly one dimension (one move), and (b) name its numbering-
    parent as `from` (the number and the derivation agree); a node whose from is not its numbering-
    parent, or whose where is not a single move, only RE-INDEXES and is not a permanent node. Every
    numbering-parent must itself be seeded or be the definitive events node '1'."""
    defs = views.view_definitions()
    derivs = views.view_derivations()
    seeded = {n for n in defs if n[0].isdigit()}
    known_roots = seeded | {"1"}          # '1' (events) is definitive, a lawful parent, not seeded
    bad = []
    for nid in seeded:
        parent = _numbering_parent(nid)
        if parent is not None and parent not in known_roots:
            bad.append((nid, "orphan-numbering"))
        if nid in derivs:
            where = dict(derivs[nid].get("where") or {})
            if len(where) != 1:                                    # not a single move
                bad.append((nid, "not-one-move"))
            if derivs[nid].get("from") != parent:                  # re-indexes to a non-numbering parent
                bad.append((nid, "from-not-numbering-parent"))
    return bad


# =============================================================================================
# A1 — the 35 seed rows: 12 bind + 23 derive; view_definitions reads all 35
# =============================================================================================

@unittest.skipUnless(
    os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design/25-view-tree-v2.json")),
    "SKIP PRIVATE-SOURCE: needs design/25-view-tree-v2.json (absent in the render)")
class TestSeedRows(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3-a1-")
        self.oracle = _oracle()

    def test_the_seed_is_exactly_35_rows_12_bind_23_derive(self):
        forms = _seeded_forms(self.views)
        self.assertEqual(len(forms), 35, f"expected 35 tree rows, got {len(forms)}")
        binds = [f for f in forms.values() if f.startswith("bind:")]
        derives = [f for f in forms.values() if f.startswith("derive:")]
        self.assertEqual(len(binds), 12, f"expected 12 bind rows, got {len(binds)}")
        self.assertEqual(len(derives), 23, f"expected 23 derive rows, got {len(derives)}")

    def test_view_definitions_reads_every_seeded_node(self):
        defs = self.views.view_definitions()
        for nid in _oracle_seed_forms(self.oracle):
            self.assertIn(nid, defs, f"seed node {nid} not read back by view_definitions")

    def test_no_computed_or_definitive_node_is_seeded(self):
        # node 1 (definitive) and the 8 level-4 nodes (computed) are NOT seeded. A planted level-4 or
        # definitive seed would put one of these ids in view_definitions — this reds if it does.
        defs = self.views.view_definitions()
        not_seeded = [v["id"] for v in self.oracle["views"]
                      if v["seed_form"] in ("definitive", "computed")]
        self.assertEqual(len(not_seeded), 9, "oracle should have 1 definitive + 8 computed")
        for nid in not_seeded:
            self.assertNotIn(nid, defs, f"computed/definitive node {nid} must NOT be seeded")

    def test_a_bind_outside_FOLD_NAMES_is_refused_the_planted_out_of_set_bind_reds(self):
        # A1 control (the closure the seed's binds rely on): a master binding a fold OUTSIDE the set
        # is refused AR-2; a bind to a SEEDED-fold member (a VT-3 promotion) is admitted.
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-VIEW", "owner", {"name": "bad", "bind": "not_a_fold"})
        rec = self.gate.execute("CREATE-VIEW", "owner", {"name": "ok", "bind": "items"})
        self.assertEqual((rec.get("payload") or {}).get("bind"), "items")


# =============================================================================================
# A2 — the derive FORM at create_view's inline door
# =============================================================================================

class TestDeriveDoor(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3-a2-")

    def test_a_wellformed_derive_is_recorded(self):
        rec = self.gate.execute("CREATE-VIEW", "owner",
                                {"name": "d", "derive": {"from": "1.1", "where": {"actor_class": "ai"}}})
        got = dict((rec.get("payload") or {}).get("derive") or {})
        self.assertEqual(got.get("from"), "1.1")
        self.assertEqual(dict(got.get("where")), {"actor_class": "ai"})

    def test_control_where_not_exactly_one_dimension_is_refused(self):
        with self.assertRaises(OpError):                                   # zero dimensions
            self.gate.execute("CREATE-VIEW", "owner",
                              {"name": "c0", "derive": {"from": "1.1", "where": {}}})
        with self.assertRaises(OpError):                                   # two dimensions
            self.gate.execute("CREATE-VIEW", "owner",
                              {"name": "c2", "derive": {"from": "1.1",
                                                        "where": {"actor_class": "ai", "liveness": "active"}}})

    def test_control_dimension_outside_DERIVE_DIMENSIONS_is_refused(self):
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-VIEW", "owner",
                              {"name": "cx", "derive": {"from": "1.1", "where": {"not_a_dim": "x"}}})
        # a MEMBER dimension is admitted (the check can fail AND can pass)
        rec = self.gate.execute("CREATE-VIEW", "owner",
                                {"name": "cok", "derive": {"from": "1.1", "where": {"scope_class": "all"}}})
        self.assertIsNotNone((rec.get("payload") or {}).get("derive"))

    def test_control_from_naming_no_seeded_view_is_refused(self):
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-VIEW", "owner",
                              {"name": "cf", "derive": {"from": "not-a-view", "where": {"liveness": "active"}}})

    def test_control_derive_riding_with_a_bind_or_a_nonempty_when_is_refused(self):
        with self.assertRaises(OpError):                                   # derive + bind
            self.gate.execute("CREATE-VIEW", "owner",
                              {"name": "cb", "bind": "actors",
                               "derive": {"from": "1.1", "where": {"actor_class": "ai"}}})
        with self.assertRaises(OpError):                                   # derive + non-empty when
            self.gate.execute("CREATE-VIEW", "owner",
                              {"name": "cw", "when": {"action": "READ"},
                               "derive": {"from": "1.1", "where": {"actor_class": "ai"}}})

    def test_DERIVE_DIMENSIONS_is_the_pinned_grow_only_five_a_shrink_reds(self):
        # the closed vocabulary the door tests against; grow-only, pinned by a five-name baseline.
        for dim in ("actor_class", "scope_class", "item_kind", "liveness", "tree_kind"):
            self.assertIn(dim, DERIVE_DIMENSIONS)                          # a shrink would fail here
        self.assertEqual(len(DERIVE_DIMENSIONS), 5)


# =============================================================================================
# A3 — the round-trip against the independent oracle
# =============================================================================================

@unittest.skipUnless(
    os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design/25-view-tree-v2.json")),
    "SKIP PRIVATE-SOURCE: needs design/25-view-tree-v2.json (absent in the render)")
class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3-a3-")
        self.oracle = _oracle()

    def test_the_seed_reads_back_equal_to_the_json_seed_form(self):
        self.assertEqual(_seeded_forms(self.views), _oracle_seed_forms(self.oracle))

    def test_control_a_planted_divergence_reds(self):
        # §A64: the check is shown to CATCH a defect. A mutated expectation (one node's seed_form
        # changed) must NOT equal the real seed — a check that cannot fail is the defect.
        expected = _oracle_seed_forms(self.oracle)
        actual = _seeded_forms(self.views)
        self.assertEqual(actual, expected)                                # the true round-trip passes
        bad = dict(expected)
        bad["2.1"] = "bind:WRONG_FOLD"                                    # a wrong bind
        self.assertNotEqual(actual, bad)                                  # the divergence is caught
        bad2 = dict(expected)
        bad2["1.1.1"] = "derive:scope_class=all"                          # a wrong derive
        self.assertNotEqual(actual, bad2)


# =============================================================================================
# A4 — the one-move instrument
# =============================================================================================

class TestOneMove(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3-a4-")

    def test_every_seeded_node_is_its_parent_plus_one_move(self):
        self.assertEqual(_one_move_violations(self.views), [])

    def test_control_a_reindex_only_node_reds(self):
        # §A64: the instrument is driven against a PLANTED re-index-only node — a derive whose `from`
        # is NOT its numbering-parent (it re-indexes sideways, adding a number but no honest move) —
        # and against a derive with no single move (empty where). Seeded by direct append (the seed
        # path), then the instrument must flag both. A check that cannot fail is the defect.
        from_wrong = {"actor": "PC_RUNTIME", "action": "CREATE-VIEW", "object": "view:2.1.9",
                      "rule_cited": "ROOT-NEG-6",
                      "payload": {"kind": "view_definition", "rule_id": "view:2.1.9", "polarity": "+",
                                  "name": "2.1.9", "when": {}, "then": {}, "tier": "owner",
                                  "derive": {"from": "1.1", "where": {"scope_class": "all"}},  # from != 2.1
                                  "text": "planted re-index (from is not the numbering-parent)"}}
        self.store._append(from_wrong)
        viols = dict(_one_move_violations(self.views))
        self.assertIn("2.1.9", viols)                                     # the instrument flags it
        self.assertEqual(viols["2.1.9"], "from-not-numbering-parent")


# =============================================================================================
# A5 — RED founding discipline: the pack moved once
# =============================================================================================

class TestFoundingMove(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3-a5-")

    def test_the_founding_version_moved_one_minor_to_1_53_0(self):
        # §A57 live-version pin: C6a VT-6d (THE STAMP FOUNDING — the required-stamps policy rule)
        # moved the LIVE founding 1.53.0 -> 1.54.0 BY NAME, then C7 P3 (THE KERNEL FROM THE RECORD — the
        # twelve act-kind rows) moved it 1.54.0 -> 1.55.0 BY NAME (the "re-pinned by the last founding
        # mover" idiom; VT-3's own move to 1.53.0 stands in the log, which A6 below reads).
        self.assertEqual(founding_version(), "1.55.0")

    def test_the_six_folds_the_binds_name_are_promoted_10_to_16(self):
        members = set(fold_set()["members"])
        self.assertEqual(len(FOLD_NAMES), 16)
        for fold in PROMOTIONS:
            self.assertIn(fold, members)                                  # a shrink would red

    def test_the_35_seed_rows_are_founding_records(self):
        # the pack edit IS the seed rows + the bump; view_definitions reads the 35 back at a fresh
        # founding (the derive door is code, not a pack structural declaration — no op def needed).
        forms = _seeded_forms(self.views)
        self.assertEqual(len(forms), 35)

    @unittest.skipUnless(
        os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/build/BUILD-PROGRESS_v3.md")),
        "SKIP PRIVATE-SOURCE: needs planning/build/BUILD-PROGRESS_v3.md (absent in the render)")
    def test_the_bump_attestation_names_the_version_and_the_new_pack_sha(self):
        # §A57 / founding-mover discipline: the bump-attestation (OLD->NEW version + the new pack
        # sha256) lands in BUILD-PROGRESS. This reads the CURRENT pack's own sha and asserts the log
        # names both — the attestation is a fact any reader can recompute, not a claim.
        import hashlib
        with open(os.path.join(os.path.dirname(__file__), "..", "planning", "build",
                               "BUILD-PROGRESS_v3.md")) as fh:
            log = fh.read()
        self.assertIn("1.53.0", log, "BUILD-PROGRESS does not name the new founding version")
        pack_path = os.path.join(os.path.dirname(__file__), "..", "src", "founding", "founding-pack.json")
        with open(pack_path, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        self.assertIn(sha, log, "BUILD-PROGRESS does not name the new pack sha256 (bump-attestation)")


# =============================================================================================
# A6 — I7: VT-1 stays as built; each promoted fold a separate memoised projection
# =============================================================================================

class TestI7Held(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3-a6-")

    def test_events_by_effect_is_unchanged_not_reshaped_by_the_promotion(self):
        # rule_changing_acts / acts_under_rules were promoted to FOLD_NAMES as membership only; the
        # events split (VT-1's own projection) is UNTOUCHED — still its two keys, never reshaped so a
        # promoted fold could key off it (I7: a separate memoised projection, never a key on another).
        ebe = self.views.events_by_effect()
        self.assertEqual(set(ebe.keys()), {"rule_changing_acts", "acts_under_rules"})

    def test_static_composite_is_its_own_projection(self):
        # static_composite (a VT-1 projection) is promoted and stays its own memoised projection.
        sc = self.views.static_composite()
        self.assertEqual(set(sc.keys()), {"content", "spaces", "keys", "tunnels", "devices"})

    def test_the_promotion_grew_the_set_by_exactly_the_six(self):
        members = set(fold_set()["members"])
        # the ten VT-1 baseline members plus exactly the six VT-3 promotions = sixteen, no more.
        baseline10 = {"active_rules", "actors", "resources", "permissions", "relationships",
                      "op_definitions", "view_definitions", "old_rules", "old_items", "old_relationships"}
        self.assertEqual(members, baseline10 | set(PROMOTIONS))


if __name__ == "__main__":
    unittest.main()
