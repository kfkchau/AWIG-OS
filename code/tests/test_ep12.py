"""EP-12 — the kernel dictionary (cgl-app pattern lowered; tree 2.2, the reuse ruling).

Reusable TERMS as records (action/resource/actor entries), resolved LATEST-UNDISPUTED-WINS (a fold,
never a status); a dispute routes to the owner queue as an append-nothing view; a definition_ref must
resolve to a real op/view definition at the MOMENT OF USE (integrity-at-use, the EP-07 precedent).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402


class TestKernelDictionary(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def test_entries_are_reusable_records_by_kind(self):
        self.gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action"})
        self.gate.execute("DICT-ENTRY", "owner", {"term": "region", "entity_kind": "resource"})
        self.gate.execute("DICT-ENTRY", "owner", {"term": "reviewer", "entity_kind": "actor"})
        d = self.views.dictionary()
        self.assertEqual({("action", "grant"), ("resource", "region"), ("actor", "reviewer")}, set(d))
        self.assertEqual(set(self.views.dictionary("action")), {("action", "grant")})   # filter by kind

    def test_latest_undisputed_wins_and_a_dispute_changes_the_fold(self):
        self.gate.execute("DICT-ENTRY", "alice", {"term": "grant", "entity_kind": "action", "tags": {"v": 1}})
        r2 = self.gate.execute("DICT-ENTRY", "bob", {"term": "grant", "entity_kind": "action", "tags": {"v": 2}})
        self.assertEqual(self.views.dictionary("action")[("action", "grant")]["tags"]["v"], 2)   # latest wins
        self.gate.execute("DISPUTE", "carol", {"ref_seq": r2["seq"]})                            # dispute the latest
        self.assertEqual(self.views.dictionary("action")[("action", "grant")]["tags"]["v"], 1)   # -> undisputed fallback
        self.assertIn({"entity_kind": "action", "term_key": "grant"}, self.views.disputed_terms())  # routed to owner

    def test_a_fully_disputed_term_has_no_current_entry_and_a_later_one_wins_again(self):
        r1 = self.gate.execute("DICT-ENTRY", "alice", {"term": "grant", "entity_kind": "action", "tags": {"v": 1}})
        self.gate.execute("DISPUTE", "carol", {"ref_seq": r1["seq"]})
        self.assertNotIn(("action", "grant"), self.views.dictionary("action"))                   # no undisputed entry
        self.gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action", "tags": {"v": 3}})
        self.assertEqual(self.views.dictionary("action")[("action", "grant")]["tags"]["v"], 3)   # a later undisputed wins

    def test_resolve_dispute_lifts_it(self):
        r1 = self.gate.execute("DICT-ENTRY", "alice", {"term": "grant", "entity_kind": "action"})
        self.gate.execute("DISPUTE", "carol", {"ref_seq": r1["seq"]})
        self.assertNotIn(("action", "grant"), self.views.dictionary("action"))
        self.gate.execute("RESOLVE-DISPUTE", "owner", {"ref_seq": r1["seq"]})
        self.assertIn(("action", "grant"), self.views.dictionary("action"))                      # dispute lifted -> current

    def test_definition_ref_resolves_a_real_link_but_a_dangling_one_refuses_at_use(self):
        self.gate.execute("DICT-ENTRY", "owner",
                          {"term": "admit", "entity_kind": "action", "definition_ref": "op:SCHED-ADMIT"})
        self.assertEqual(self.gate.execute("USE-TERM", "alice", {"entity_kind": "action", "term": "admit"})["action"],
                         "USE-TERM")                                                              # real link resolves
        self.gate.execute("DICT-ENTRY", "owner",
                          {"term": "frob", "entity_kind": "action", "definition_ref": "op:NO-SUCH-OP"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("USE-TERM", "alice", {"entity_kind": "action", "term": "frob"})     # dangling -> refuse AT USE
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")

    def test_definition_ref_resolves_a_live_code_op_r29(self):
        # R29 (EP-13): a term linking a CODE-registered bootstrap op (CREATE-INFO/GRANT-READ, absent
        # from op_definitions but live in the registry) must RESOLVE at use — the old fold-only lookup
        # fail-closed and wrongly refused it. Now definition_ref resolves op: against gate.has.
        self.gate.execute("DICT-ENTRY", "owner",
                          {"term": "mkinfo", "entity_kind": "action", "definition_ref": "op:CREATE-INFO"})
        self.assertEqual(self.gate.execute("USE-TERM", "alice", {"entity_kind": "action", "term": "mkinfo"})["action"],
                         "USE-TERM")

    def test_using_an_unresolved_term_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("USE-TERM", "alice", {"entity_kind": "action", "term": "never-defined"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")

    def test_the_dictionary_views_append_nothing(self):
        self.gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action"})
        before = len(self.store.all())
        self.views.dictionary(); self.views.disputed_terms()
        self.assertEqual(len(self.store.all()), before)

    def test_dictionary_ops_mint_at_ordinary_tier(self):
        ops = self.views.op_definitions()
        for name in ("DICT-ENTRY", "DISPUTE", "RESOLVE-DISPUTE", "USE-TERM"):
            self.assertEqual(ops[name]["tier"], "ordinary")   # the constraint's default; not claimed above

    def test_the_dictionary_survives_replay(self):
        self.gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action", "tags": {"v": 9}})
        _, _, views2 = build_kernel(self.path)
        self.assertEqual(views2.dictionary("action")[("action", "grant")]["tags"]["v"], 9)


if __name__ == "__main__":
    unittest.main()
