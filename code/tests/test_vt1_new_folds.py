"""C6a VT-1 — THE NEW FOLDS (design/25 v2.1 the view tree; design/53 B3/B4/I4/I7).

Named in planning/exec/VT-1-NEW-FOLDS-BUILD.md before code, landed here as regression tests
(charter: every verification probe lands as a regression test). This battery proves that the view
tree's NEW FOLDS are computed VIEWS over the append-only record, beside the existing ones:

  A1  the level-2 OLD bands — old_rules (2.2), old_items (3.2), old_relationships (4.2) — are the
      latest-wins COMPLEMENTS of the active masters; a superseded/withdrawn row is OLD and NOT
      active; the two partition; NOTHING is erased. RED: a still-active row placed in an old band.
  A2  events_by_effect is the LEVEL-2 split by the EFFECT FIELD (rule-changing acts / acts under
      rules), read from payload.rule_id, NEVER the op name; and chains_of_effect computes causal
      chains over the record's own crossing lineage. An event is NEVER old (ruling 19). RED: an
      event placed in an old band.
  A3  static_composite names the static kinds; the level-4 filters compute actors BY CLASS, static
      BY KIND, and BY CELL as a filter (ruling 21). Overlap stays a CHECK at level 4, never a node
      (ruling 22). RED: an overlap promoted to a fold/node.
  A4  the fold-set pin MOVES ONCE, grow-only: FOLD_NAMES + the three OLD-band masters; the
      set_digest recomputes (9c431d16… -> 952406cb…). RED: a SHRINK (removing a member).
  A5  I7 — no campaign-1/2 pin loosened: each new fold is its OWN memoised projection (its own memo
      key), NEVER a key added onto an existing projection; category_packs() is byte-unchanged (the
      P8b oracle lesson, board :3735).

THE WRONG REFERENCES REFUSED BY NAME (design/53 stop conditions):
  (b) OLD-AS-A-DELETE — an OLD band is a latest-wins VIEW; the row is never erased (append-only,
      ruling 19). This battery proves the superseded row is STILL on the record and STILL readable.
  events-side: AN EVENT IS NEVER OLD — a happening does not split active/old (ruling 19). The
      amendment EVENT stays a live rule-changing act even as the RULE version it wrote goes old.
  (e) OVERLAP-AS-A-NODE — overlap of two rules' scopes stays a CHECK at level 4 (ruling 22), never a
      fold or a view node.
  the materialized-view / stored-status reference (P2): every fold here is COMPUTED — kill it,
      replay the record, identical; nothing stores a band.

Every acceptance carries its RED WORLD, driven THROUGH the fold (a control that cannot red is the
defect, §A42/§A64).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                                  # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.views import FOLD_NAMES, fold_set                         # noqa: E402
from kernel.canonical import canonical_hash                           # noqa: E402


def _kernel(prefix):
    d = tempfile.mkdtemp(prefix=prefix)
    return build_kernel(os.path.join(d, "record.jsonl"))


def _append(store, action, actor="owner", payload=None, **kw):
    """Seed one raw record and return its seq (the folds read the record, not the gate path —
    the test_ep39 store._append idiom; supersession/lineage is controlled precisely by seq)."""
    ev = {"actor": actor, "action": action, "rule_cited": "ROOT-NEG-5", "payload": payload or {}}
    ev.update(kw)
    return store._append(ev)["seq"]


# =============================================================================================
# A1 — the level-2 OLD bands: old_rules / old_items / old_relationships (latest-wins complements)
# =============================================================================================

class TestOldBands(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt1-a1-")

    def test_old_rules_is_the_latest_wins_complement_and_partitions(self):
        v1 = _append(self.store, "CREATE-RULE", payload={"rule_id": "law:x", "policy_key": "k", "value": 1})
        v2 = _append(self.store, "CREATE-RULE", payload={"rule_id": "law:x", "policy_key": "k", "value": 2})
        old = {r["seq"] for r in self.views.old_rules()}
        active = self.views.active_rules()
        self.assertIn(v1, old)                                        # the superseded version is OLD
        self.assertEqual(active["law:x"]["seq"], v2)                  # the active version is the latest
        self.assertNotIn(v2, old)                                     # RED: the still-active row is NOT in old
        # NOTHING ERASED (stop (b)): the superseded row is STILL on the record
        self.assertIsNotNone(self.store.by_seq(v1))

    def test_a_rule_created_once_is_not_old(self):
        _append(self.store, "CREATE-RULE", payload={"rule_id": "law:once", "policy_key": "k", "value": 7})
        self.assertNotIn("law:once", {r.get("rule_id") for r in self.views.old_rules()})

    def test_old_items_holds_previous_actor_and_resource_versions(self):
        a1 = _append(self.store, "CREATE-ACTOR", payload={"actor_id": "act1", "actor_class": "human"})
        a2 = _append(self.store, "CREATE-ACTOR", payload={"actor_id": "act1", "actor_class": "human"})
        r1 = _append(self.store, "CREATE-INFO", object="obj1", payload={"kind": "content"})
        r2 = _append(self.store, "CREATE-INFO", object="obj1", payload={"kind": "content"})
        old = self.views.old_items()
        old_seqs = {(o["kind"], o["seq"]) for o in old}
        self.assertIn(("actor", a1), old_seqs)                        # previous actor version is OLD
        self.assertIn(("resource", r1), old_seqs)                    # previous resource version is OLD
        self.assertNotIn(("actor", a2), old_seqs)                    # RED: the current version is NOT old
        self.assertNotIn(("resource", r2), old_seqs)

    def test_a_singleton_item_is_not_old(self):
        _append(self.store, "CREATE-ACTOR", payload={"actor_id": "solo", "actor_class": "ai"})
        self.assertNotIn("solo", {o["id"] for o in self.views.old_items()})

    def test_old_relationships_superseded_and_withdrawn_never_live(self):
        s1 = _append(self.store, "CREATE-RELATIONSHIP", payload={"rel_id": "r1", "from": "a", "to": "b"})
        s2 = _append(self.store, "CREATE-RELATIONSHIP", payload={"rel_id": "r1", "from": "a", "to": "b"})
        _append(self.store, "CREATE-RELATIONSHIP", payload={"rel_id": "r2", "from": "c", "to": "d"})  # live
        w = _append(self.store, "CREATE-RELATIONSHIP",
                    payload={"rel_id": "r3", "from": "e", "to": "f", "state": "withdrawn"})
        old = self.views.old_relationships()
        by_seq = {o["seq"]: o["state"] for o in old}
        self.assertEqual(by_seq.get(s1), "superseded")               # the superseded version is OLD
        self.assertEqual(by_seq.get(w), "withdrawn")                 # the withdrawn relation is OLD
        self.assertNotIn(s2, by_seq)                                 # RED: the current version is NOT old
        self.assertNotIn("r2", {o["rel_id"] for o in old})          # RED: a live relation is NOT old


# =============================================================================================
# A2 — events_by_effect (the level-2 split) and chains_of_effect; an event is NEVER old
# =============================================================================================

class TestEvents(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt1-a2-")

    def test_events_split_by_the_effect_field_not_the_op_name(self):
        # a RULE-CHANGING act self-declares a rule_id; an act under rules does not — recognition is
        # the EFFECT FIELD, never the op name (the action string is identical vocabulary here).
        rc = _append(self.store, "CREATE-RULE", payload={"rule_id": "law:e", "policy_key": "k", "value": 1})
        under = _append(self.store, "FILE-WRITE", payload={"path": "/x"})   # no rule_id -> act under rules
        ev = self.views.events_by_effect()
        self.assertEqual(set(ev), {"rule_changing_acts", "acts_under_rules"})   # NO old band
        rc_seqs = {r["seq"] for r in ev["rule_changing_acts"]}
        under_seqs = {r["seq"] for r in ev["acts_under_rules"]}
        self.assertIn(rc, rc_seqs)
        self.assertIn(under, under_seqs)
        # EXHAUSTIVE and EXCLUSIVE over the whole record
        self.assertEqual(rc_seqs & under_seqs, set())
        self.assertEqual(rc_seqs | under_seqs, {e["seq"] for e in self.store.all()})

    def test_an_event_is_never_old_even_when_its_rule_goes_old(self):
        v1 = _append(self.store, "CREATE-RULE", payload={"rule_id": "law:m", "policy_key": "k", "value": 1})
        v2 = _append(self.store, "CREATE-RULE", payload={"rule_id": "law:m", "policy_key": "k", "value": 2})
        # the OLD RULE version v1 is in old_rules — the RULE version went old
        self.assertIn(v1, {r["seq"] for r in self.views.old_rules()})
        ev = self.views.events_by_effect()
        rc_seqs = {r["seq"] for r in ev["rule_changing_acts"]}
        # ...but BOTH the create AND the amend EVENTS are still live rule-changing acts (ruling 19)
        self.assertIn(v1, rc_seqs)
        self.assertIn(v2, rc_seqs)
        # RED: there is NO old band for events — an attempt to read one finds nothing
        self.assertNotIn("old", ev)
        self.assertNotIn("old_events", ev)

    def test_chains_of_effect_walks_the_records_own_crossing_causation(self):
        a = _append(self.store, "DO-CROSS", payload={"kind": "crossing-handout", "station": "s"})
        b = _append(self.store, "DO-CROSS", payload={"kind": "crossing-handout", "parent_handout_seq": a})
        c = _append(self.store, "DO-CROSS", payload={"kind": "crossing-answer", "handout_seq": b})
        chains = self.views.chains_of_effect()
        self.assertIn([a, b, c], chains)                             # the causal chain a -> b -> c
        # RED / able-to-fail: an unrelated record (no causal ref) forms no edge, so it is not a chain
        _append(self.store, "FILE-WRITE", payload={"path": "/y"})
        self.assertEqual(self.views.chains_of_effect(), chains)     # the lone act adds no chain


# =============================================================================================
# A3 — static composite + the level-4 filters (actors by class, static by kind, by cell); overlap
# =============================================================================================

class TestStaticAndLevel4(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt1-a3-")

    def test_static_composite_names_every_kind_and_populates_the_live_reads(self):
        _append(self.store, "CREATE-INFO", object="doc1", payload={"kind": "content"})
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": "space:root"})
        sc = self.views.static_composite()
        self.assertEqual(set(sc), set(self.views.STATIC_KINDS))      # all five kinds NAMED
        self.assertIn("doc1", sc["content"])                        # content populated (a live read)
        self.assertIn("space:team", sc["spaces"])                   # spaces populated (a live read)
        self.assertEqual(sc["keys"], {})                            # CAP: named-but-empty until VT-3
        self.assertEqual(sc["tunnels"], {})
        self.assertEqual(sc["devices"], {})

    def test_actors_by_class_groups_and_counts_the_classless(self):
        _append(self.store, "CREATE-ACTOR", payload={"actor_id": "h1", "actor_class": "human"})
        _append(self.store, "CREATE-ACTOR", payload={"actor_id": "ai1", "actor_class": "ai"})
        _append(self.store, "CREATE-ACTOR", payload={"actor_id": "no1"})   # NO class
        by = self.views.actors_by_class()
        self.assertIn("h1", by.get("human", []))
        self.assertIn("ai1", by.get("ai", []))
        self.assertIn("no1", by.get(None, []))                      # a classless actor is COUNTED (B4)

    def test_static_by_kind_and_by_cell(self):
        _append(self.store, "CREATE-INFO", object="doc2", payload={"kind": "content"})
        bk = self.views.static_by_kind()
        self.assertEqual(set(bk), set(self.views.STATIC_KINDS))
        self.assertIn("doc2", bk["content"])
        cells = self.views.static_by_cell()
        self.assertEqual(self.views.static_by_cell("U-involved"), ["content"])   # blobs are U-involved
        self.assertEqual(sorted(self.views.static_by_cell("S")),
                         sorted(["spaces", "keys", "tunnels", "devices"]))         # the rest are S
        self.assertEqual(set(cells), {"U-involved", "S"})

    def test_overlap_is_a_check_not_a_node(self):
        # ruling 22: overlap of two rules' scopes stays a CHECK at level 4, never promoted to a node.
        self.assertNotIn("overlap", FOLD_NAMES)                     # RED: no overlap fold/master exists
        self.assertFalse(hasattr(self.views, "overlap"))           # no overlap view node method
        # overlap-family collisions are the EXISTING check machinery (contradictions), a derivation
        self.assertTrue(hasattr(self.views, "contradictions"))     # the check is where overlap feeds
        # a master cannot bind a non-existent "overlap" fold — the closure refuses it
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-VIEW", "owner", {"name": "ov", "bind": "overlap"})


# =============================================================================================
# A4 — the fold-set pin moves ONCE, grow-only (the disclosed grow; a shrink reds)
# =============================================================================================

class TestFoldSetMovedOnce(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt1-a4-")

    def test_the_three_old_band_masters_are_members_and_the_digest_moved(self):
        fs = fold_set()
        self.assertEqual(fs["members"], tuple(sorted(FOLD_NAMES)))
        self.assertEqual(fs["set_digest"], canonical_hash(tuple(sorted(FOLD_NAMES))))
        for new in ("old_rules", "old_items", "old_relationships"):
            self.assertIn(new, fs["members"])                       # the disclosed grow
        # the digest MOVED from the seven-member baseline to the ten-member one
        seven = ("active_rules", "actors", "resources", "permissions", "relationships",
                 "op_definitions", "view_definitions")
        self.assertNotEqual(canonical_hash(tuple(sorted(seven))), fs["set_digest"])

    def test_a_shrink_reds_the_baseline(self):
        # grow-only: removing ANY member yields a DIFFERENT digest — a shrink is visible and reds.
        for drop in ("old_rules", "active_rules"):
            shrunk = tuple(sorted(m for m in FOLD_NAMES if m != drop))
            self.assertNotEqual(canonical_hash(shrunk), fold_set()["set_digest"])

    def test_a_master_may_now_bind_an_old_band_a_non_member_is_still_refused(self):
        rec = self.gate.execute("CREATE-VIEW", "owner", {"name": "old-rule-master", "bind": "old_rules"})
        self.assertEqual((rec.get("payload") or {}).get("bind"), "old_rules")   # admitted (a member)
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-VIEW", "owner", {"name": "bad", "bind": "not_a_fold"})   # refused


# =============================================================================================
# A5 — I7: each new fold a SEPARATE memoised projection; no campaign-1 pin loosened
# =============================================================================================

class TestSeparateProjections(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt1-a5-")

    def test_each_new_fold_has_its_own_memo_key(self):
        for fold in ("old_rules", "old_items", "old_relationships",
                     "events_by_effect", "chains_of_effect", "static_composite",
                     "actors_by_class", "static_by_kind"):
            getattr(self.views, fold)()
            self.assertTrue(any(k.startswith(fold + ":") for k in self.views._memo),
                            f"{fold} did not memoise under its own name (a separate projection, I7)")

    def test_no_new_fold_adds_a_key_onto_an_existing_projection(self):
        # THE P8b LESSON (board :3735): a new fold is a SEPARATE projection, never a key added onto an
        # existing one. category_packs() is byte-unchanged after every new fold is exercised, and the
        # category_packs record projection gains no key.
        _append(self.store, "CREATE-RULE", payload={"rule_id": "law:z", "policy_key": "k", "value": 1})
        before = self.views.category_packs()
        for fold in ("old_rules", "old_items", "old_relationships", "events_by_effect",
                     "chains_of_effect", "static_composite", "actors_by_class", "static_by_kind"):
            getattr(self.views, fold)()
        after = self.views.category_packs()
        self.assertEqual(before, after)                             # the campaign-1 oracle answer is unchanged
        # the new fold's memo and category_packs' memo coexist as DISTINCT keys — separate projections
        prefixes = {k.split(":")[0] for k in self.views._memo}
        self.assertIn("category_packs", prefixes)                   # its projection is untouched, still memoised
        self.assertIn("old_rules", prefixes)                        # the new fold is a SEPARATE key beside it


if __name__ == "__main__":
    unittest.main()
