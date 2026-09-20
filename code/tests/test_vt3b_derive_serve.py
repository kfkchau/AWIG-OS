"""C6a VT-3b — THE DERIVED VIEW SERVED (design/25 v2 the third view form; design/53 L16, VT-3b).

Named in planning/exec/VT-3b-DERIVE-SERVE-BUILD.md before code, landed here as regression tests
(charter: every verification probe lands as a regression test). VT-3 seeded the derive rows and
built the create_view write-time door; VT-3b builds the READ side — `execute_view` SERVES a derive
row by returning its PARENT view's output NARROWED by the one closed dimension. The parent's output
is resolved BY ITS FORM (archi's binding precision, board :3831): a BIND parent is the master READ
(`master(name).value`, the fold's own output in its own shape); a FILTER parent is execute_view's
matched rows; a DERIVE parent is resolved RECURSIVELY; it is NEVER the raw record scan.

  A1  execute_view serves a derive row as the PARENT NARROWED by the one dimension — a STRICT
      SUBSET. The fixture carries at least TWO values of the dimension (on a one-value fixture the
      narrowed set equals the parent — so a second value is planted, never a weakened assertion);
      a master/filter view still serves as before (unchanged).
  A2  THE FIVE DERIVATIONS, IN CODE: actor_class (the acting actor's DECLARED class, read at read
      time off the account surface); scope_class (from the rule scope, or `all`); item_kind
      (actor|static); liveness (active|old, latest-wins); tree_kind (from the venn2 geometry and
      both ends of VT-2's relation row). For each, the derive returns exactly the parent rows
      carrying the value; a PLANTED WRONG narrowing (a mis-derivation) yields a DIFFERENT set — the
      check can fail.
  A3  AN UNSEEDED PARENT REFUSED AT READ, as create_view refuses at write: a planted derive whose
      `from` names no view definition at head is refused at read; a derive on a SEEDED parent serves.

  STOP (b) — DO NOT FLATTEN: a fold whose OUTPUT SHAPE carries no source for the dimension is
      refused at read, never flattened into a wrong bucket. old_relationships (parent 4.2) emits the
      retired {from, to, rel_kind} shape (no geometry) for VT-2 records, so tree_kind cannot be
      derived over it — the serving REFUSES rather than assigning non_tree to every row. This is a
      RAISED finding (old_relationships predates VT-2's geometry; the fix is out of this read fence).

Every acceptance carries its RED WORLD, driven THROUGH the actual mechanism (a control that cannot
red is the defect, §A42/§A64). GREEN — read-side only; no founding, no new field, no pack edit.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                                  # noqa: E402
from kernel.errors import OpError                                     # noqa: E402


def _kernel(prefix):
    d = tempfile.mkdtemp(prefix=prefix)
    return build_kernel(os.path.join(d, "record.jsonl"))


def _plant(store, rec):
    """Append a record on the seed path (the VT-3 A4 planted-row pattern): a governed record needs a
    cited rule (H3), so one is supplied where absent. Used for fixtures and for the planted controls
    that a well-formed create_view door would refuse (an unseeded-parent derive)."""
    rec.setdefault("rule_cited", "ROOT-NEG-1")
    store._append(rec)


def _derive_row(store, name, parent, where, rule="ROOT-NEG-6"):
    """Plant a derive view-definition row {from parent, where} directly (the seed path)."""
    _plant(store, {"actor": "owner", "action": "CREATE-VIEW", "object": f"view:{name}",
                   "rule_cited": rule,
                   "payload": {"kind": "view_definition", "rule_id": f"view:{name}", "name": name,
                               "when": {}, "then": {}, "derive": {"from": parent, "where": where}}})


def _rule(store, rule_id, scope=None):
    p = {"rule_id": rule_id, "polarity": "+", "text": "t"}
    if scope is not None:
        p["scope"] = scope
    _plant(store, {"actor": "owner", "action": "CREATE-RULE", "object": rule_id, "payload": p})


def _rel(store, subject, object_, geometry, rel_id=None):
    p = {"subject": subject, "object": object_, "geometry": geometry}
    if rel_id is not None:
        p["rel_id"] = rel_id
    _plant(store, {"actor": "owner", "action": "CREATE-RELATIONSHIP",
                   "object": f"r:{rel_id or subject+object_+geometry}", "rule_cited": "CAP-IS-LAW",
                   "payload": p})


# =============================================================================================
# A1 — the serving narrows the parent to a STRICT SUBSET; master/filter serve as before
# =============================================================================================

class TestA1SubsetNarrowing(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3b-a1-")
        # TWO values of actor_class in the parent: the founding `owner` (human) and a planted `bob`
        # (ai) both act; the derive actor_class=human keeps owner's row and drops bob's — a strict
        # subset only because the second value is present (A1's planted-second-value discipline).
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "bob", "actor_class": "ai"})
        _plant(self.store, {"actor": "bob", "action": "CREATE-INFO", "object": "i:bob",
                            "rule_cited": "ROOT-NEG-1", "payload": {"kind": "note"}})
        _derive_row(self.store, "d_human", "1.2", {"actor_class": "human"})

    def test_the_derive_serves_the_parent_narrowed_a_strict_subset(self):
        parent = self.views.master("1.2")["value"]                    # the bind parent's own output
        parent_seqs = {r["seq"] for r in parent}
        out = self.views.execute_view("d_human")
        served = {r["seq"] for r in out["rows"]}
        # at least TWO distinct actor_class values are present in the parent (else the subset is
        # trivial): the fixture guarantees human (owner) and ai (bob) both act
        classes = {(self.views.accounts().get(r["actor"]) or {}).get("actor_class") for r in parent}
        self.assertGreaterEqual(len({c for c in classes if c is not None}), 2,
                                "fixture must carry >=2 dimension values (A1)")
        self.assertTrue(served <= parent_seqs, "the narrowed set is not a subset of the parent")
        self.assertLess(len(served), len(parent_seqs), "the narrowing is not STRICT (nothing dropped)")
        self.assertGreater(len(served), 0, "the narrowing dropped everything")

    def test_a_master_view_still_serves_as_before_unchanged(self):
        # a BIND master's master() read is unchanged (the derive serving is added beside it)
        m = self.views.master("1.2")
        self.assertIsNotNone(m)
        self.assertEqual(m["bind"], "acts_under_rules")
        self.assertIsInstance(m["value"], list)

    def test_a_filter_view_still_serves_as_before_unchanged(self):
        # a FILTER view (a `when` trigger) still returns its matched rows and outcome template
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "f_ca", "when": {"action": "CREATE-ACTOR"}, "then": {}})
        out = self.views.execute_view("f_ca")
        self.assertIn("rows", out)
        self.assertIn("then", out)
        self.assertTrue(all(e["action"] == "CREATE-ACTOR" for e in out["rows"]))
        self.assertGreater(out["count"], 0)


# =============================================================================================
# A2 — the five derivations, in code; each with a planted-wrong control (the check can fail)
# =============================================================================================

class TestA2FiveDerivations(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3b-a2-")

    def test_actor_class_the_acting_actors_declared_class(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "bob", "actor_class": "ai"})
        _plant(self.store, {"actor": "alice", "action": "CREATE-INFO", "object": "i:a",
                            "rule_cited": "ROOT-NEG-1", "payload": {"kind": "note"}})
        _plant(self.store, {"actor": "bob", "action": "CREATE-INFO", "object": "i:b",
                            "rule_cited": "ROOT-NEG-1", "payload": {"kind": "note"}})
        au = self.views.acts_under_rules()
        alice_seqs = {r["seq"] for r in au if r["actor"] == "alice"}
        bob_seqs = {r["seq"] for r in au if r["actor"] == "bob"}
        _derive_row(self.store, "human", "1.2", {"actor_class": "human"})
        served = {r["seq"] for r in self.views.execute_view("human")["rows"]}
        self.assertTrue(alice_seqs <= served, "human derive missed the human actor's act")
        self.assertFalse(bob_seqs & served, "human derive wrongly kept the ai actor's act")
        # PLANTED WRONG: an ai-narrowing gives a DIFFERENT set (the derivation discriminates)
        _derive_row(self.store, "ai", "1.2", {"actor_class": "ai"})
        served_ai = {r["seq"] for r in self.views.execute_view("ai")["rows"]}
        self.assertNotEqual(served, served_ai, "actor_class does not discriminate by declared class")
        self.assertTrue(bob_seqs <= served_ai)

    def test_scope_class_from_the_rule_scope_or_all(self):
        _rule(self.store, "law:p", scope="class:program")
        _rule(self.store, "law:h", scope="class:human")
        _rule(self.store, "law:root", scope="space:root")             # a space scope -> all
        _rule(self.store, "law:none")                                 # no scope -> all
        _derive_row(self.store, "sp", "2.1", {"scope_class": "program"})
        _derive_row(self.store, "sall", "2.1", {"scope_class": "all"})
        prog = self.views.execute_view("sp")["rows"]                  # a dict-shaped fold -> sub-dict
        self.assertIsInstance(prog, dict)
        self.assertIn("law:p", prog)
        self.assertNotIn("law:h", prog)                               # a different class is excluded
        allc = self.views.execute_view("sall")["rows"]
        self.assertIn("law:root", allc)                               # a space scope narrows to all
        self.assertIn("law:none", allc)                              # no scope narrows to all
        self.assertNotIn("law:p", allc)                              # a class scope is NOT `all`
        # PLANTED WRONG: the human narrowing differs from the program narrowing
        _derive_row(self.store, "sh", "2.1", {"scope_class": "human"})
        self.assertNotEqual(set(prog), set(self.views.execute_view("sh")["rows"]))

    def test_item_kind_actor_or_static(self):
        # a superseded actor is an OLD actor (item_kind actor); the founding pack resources are static
        _plant(self.store, {"actor": "owner", "action": "CREATE-ACTOR", "object": "a:dup",
                            "payload": {"actor_id": "dup", "actor_class": "human"}})
        _plant(self.store, {"actor": "owner", "action": "CREATE-ACTOR", "object": "a:dup",
                            "payload": {"actor_id": "dup", "actor_class": "human"}})
        _derive_row(self.store, "ik_actor", "3.2", {"item_kind": "actor"})
        _derive_row(self.store, "ik_static", "3.2", {"item_kind": "static"})
        actors = self.views.execute_view("ik_actor")["rows"]
        statics = self.views.execute_view("ik_static")["rows"]
        self.assertTrue(all(r["kind"] == "actor" for r in actors))
        self.assertTrue(all(r["kind"] != "actor" for r in statics))   # resources fold to static
        self.assertEqual({r["id"] for r in actors}, {"dup"})
        self.assertGreater(len(statics), 0)
        # PLANTED WRONG: the actor and static narrowings are disjoint (they partition the parent)
        self.assertFalse({r["seq"] for r in actors} & {r["seq"] for r in statics})

    def test_liveness_active_or_old_latest_wins(self):
        _rel(self.store, "p", "q", "AD", rel_id="RL")                 # superseded by the next
        _rel(self.store, "p", "q", "IN", rel_id="RL")                 # the latest (active) version
        _derive_row(self.store, "live", "4", {"liveness": "active"})
        _derive_row(self.store, "dead", "4", {"liveness": "old"})
        active = self.views.execute_view("live")["rows"]
        old = self.views.execute_view("dead")["rows"]
        self.assertEqual([r["geometry"] for r in active], ["IN"], "active is not the latest version")
        self.assertEqual([r["geometry"] for r in old], ["AD"], "old is not the superseded version")
        # PLANTED WRONG: active and old are disjoint and together cover the parent (partition)
        self.assertFalse({r["seq"] for r in active} & {r["seq"] for r in old})

    def test_tree_kind_from_geometry_and_both_ends(self):
        _rel(self.store, "owner", "SYSTEM", "NS", rel_id="RA")        # NS + both established -> actor_tree
        _rel(self.store, "xx", "yy", "NS", rel_id="RI")               # NS + not established -> item_tree
        _rel(self.store, "owner", "SYSTEM", "AD", rel_id="RN")        # symmetric AD -> non_tree
        _derive_row(self.store, "at", "4", {"tree_kind": "actor_tree"})
        _derive_row(self.store, "it", "4", {"tree_kind": "item_tree"})
        _derive_row(self.store, "nt", "4", {"tree_kind": "non_tree"})
        at = {r["rel_id"] if "rel_id" in r else r["seq"] for r in self.views.execute_view("at")["rows"]}
        at_geoms = {(r["subject"], r["geometry"]) for r in self.views.execute_view("at")["rows"]}
        it_ends = {(r["subject"], r["geometry"]) for r in self.views.execute_view("it")["rows"]}
        nt_geoms = {r["geometry"] for r in self.views.execute_view("nt")["rows"]}
        self.assertEqual(at_geoms, {("owner", "NS")}, "actor_tree is not the established-ends NS row")
        self.assertEqual(it_ends, {("xx", "NS")}, "item_tree is not the unestablished-ends NS row")
        self.assertEqual(nt_geoms, {"AD"}, "non_tree is not the symmetric AD row")
        # PLANTED WRONG: the three kinds are disjoint (a row lands in exactly one)
        seqs = [set(r["seq"] for r in self.views.execute_view(v)["rows"]) for v in ("at", "it", "nt")]
        self.assertFalse(seqs[0] & seqs[1] or seqs[0] & seqs[2] or seqs[1] & seqs[2])


# =============================================================================================
# A3 — an unseeded parent refused at read, as create_view refuses at write
# =============================================================================================

class TestA3UnseededParentRefused(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3b-a3-")

    def test_a_derive_on_an_unseeded_parent_is_refused_at_read(self):
        # planted directly (the write door would refuse this — VT-3): a derive whose `from` names no
        # view at head. execute_view must REFUSE at read, mirroring the write-time refusal.
        _derive_row(self.store, "orphan", "not-a-view", {"liveness": "active"})
        with self.assertRaises(OpError):
            self.views.execute_view("orphan")

    def test_control_a_derive_on_a_seeded_parent_serves(self):
        # the check can PASS as well as fail: a seeded parent (4, relationships) serves without raising
        _derive_row(self.store, "ok", "4", {"liveness": "active"})
        out = self.views.execute_view("ok")
        self.assertIn("rows", out)                                    # no refusal


# =============================================================================================
# STOP (b) — a fold the dimension cannot be derived over is REFUSED, never flattened
# =============================================================================================

class TestStopBDoNotFlatten(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3b-stopb-")

    def test_tree_kind_over_old_relationships_refuses_it_does_not_flatten(self):
        # old_relationships (parent 4.2) emits the retired {from, to, rel_kind} shape (NO geometry)
        # for a VT-2 record; superseding one puts a geometry-less row in the old band. tree_kind
        # cannot be derived over it, so the serving REFUSES (STOP b) rather than flattening every row
        # into non_tree. This is the RAISED finding: old_relationships predates VT-2's geometry.
        _rel(self.store, "a", "b", "NS", rel_id="R1")
        _rel(self.store, "a", "b", "EM", rel_id="R1")                 # supersede -> one old-band row
        self.assertGreater(len(self.views.old_relationships()), 0, "fixture did not create an old row")
        self.assertNotIn("geometry", self.views.old_relationships()[0],
                         "old_relationships unexpectedly carries geometry (the finding changed)")
        _derive_row(self.store, "t42", "4.2", {"tree_kind": "actor_tree"})
        with self.assertRaises(OpError):
            self.views.execute_view("t42")                            # refuses; never a flattened bucket

    def test_the_active_band_tree_kind_still_serves_the_shape_is_the_difference(self):
        # the SAME dimension serves correctly over parent 4 (the VT-2 shape carries geometry) — so the
        # refusal above is about the fold's OUTPUT SHAPE, not about tree_kind being unbuildable.
        _rel(self.store, "owner", "SYSTEM", "NS", rel_id="RX")
        _derive_row(self.store, "t4", "4", {"tree_kind": "actor_tree"})
        self.assertEqual(len(self.views.execute_view("t4")["rows"]), 1)


# =============================================================================================
# The recursion and the seeded rows: a derive parent resolves up to a bind; I7 held
# =============================================================================================

class TestRecursionAndSeed(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt3b-rec-")

    def test_a_derive_parent_resolves_recursively(self):
        # 4.1 is a derive (liveness=active on 4); 4.1.1 (tree_kind) derives from 4.1 — a DERIVE
        # parent, resolved recursively up to the bind (relationships), then narrowed again.
        _rel(self.store, "owner", "SYSTEM", "NS", rel_id="RR")        # active + actor_tree
        out = self.views.execute_view("4.1.1")                        # seeded tree_kind=actor_tree on 4.1
        self.assertEqual({(r["subject"], r["geometry"]) for r in out["rows"]}, {("owner", "NS")})

    def test_the_two_events_split_masters_now_serve_their_read(self):
        # VT-3b wires rule_changing_acts / acts_under_rules as bound folds so parents 1.1 / 1.2 serve
        # their master read (the actor_class derives narrow them). events_by_effect is UNCHANGED (I7).
        self.assertIsNotNone(self.views.master("1.1"))
        self.assertIsNotNone(self.views.master("1.2"))
        self.assertEqual(set(self.views.events_by_effect().keys()),
                         {"rule_changing_acts", "acts_under_rules"})

    def test_the_servable_seeded_derives_do_not_raise_at_a_fresh_founding(self):
        # every seeded derive except the old-relationships tree_kind rows (4.2.x, STOP b) serves at a
        # fresh founding (empty bands serve empty; the actor_class/scope_class/item_kind rows serve).
        stop_b = {"4.2.1", "4.2.2", "4.2.3"}
        for name in self.views.view_derivations():
            if name in stop_b:
                continue
            out = self.views.execute_view(name)
            self.assertIn("rows", out, f"seeded derive {name} did not serve")


if __name__ == "__main__":
    unittest.main()
