"""C6a VT-7 — THE LOCAL SLICE (design/25 v2.1 ruling 17 / ruling 16 / ruling 10; design/53 B11).

Named in planning/exec/VT-7-LOCAL-SLICE-BUILD.md before code, landed here as regression tests
(charter: every verification probe lands as a regression test). This battery proves that a session's
LOCAL SLICE of the top three levels is a COMPUTED view over the append-only record — carrying the
record VERSION and HASH it was cut from, stale-on-reconnect BY DERIVATION, its must-nots live while
cut off — with NO new field and NO founding move.

  A1  local_slice cuts the top three levels for ONE session — the active rules whose scope REACHES
      the session's space (never wider than the actor's own reach, I1), split into the MUST-NOTS
      (polarity '-') and the MAY-DOS (polarity '+') — carrying the record VERSION (border.chain_head)
      and a content HASH (canonical_hash over the seq-stripped cut). A DIFFERENT session (a different
      binding space) is a DIFFERENT cut: a subspace-scoped don't binds a session in that subspace and
      NOT a sibling's, and the two cuts' hashes differ.
  A2  slice_stale reads STALE BY DERIVATION: re-cut for the same session over the CURRENT head and
      compare the carried (version, hash). A cut re-checked against the head it was cut from reads
      LIVE (the check CAN fail); a planted moved-record (any later append) reads the cut STALE. NO
      stored stale flag lives on the cut — the cut is not mutated when the world moves past it (P17).
  A3  slice_offline_decision is the offline BRAKE (ruling 16): while cut off, only the MUST-NOTS act.
      A planted offline must-not violation is REFUSED (the frozen don'ts, the gate's own matcher); a
      planted offline may-do that needs a fresh record read DEFERS — it does NOT proceed. The offline
      slice has NO allow path (fail-closed): it can only refuse an act or defer it, never approve one.
  A4  no founding, no new field: the founding pack is byte-unchanged; chain_head / merkle_root's
      canonical floor / the prohibition rules (polarity '-') are read and reused, not re-authored.

THE WRONG REFERENCES REFUSED BY NAME (design/53 VT-7 stop conditions):
  (b) STALENESS-AS-A-STORED-FLAG — the reconnect read DERIVES staleness (compare the carried
      (version, hash) to the current head, the P17 pattern); it never stores a `stale` bit. This
      battery proves the cut is byte-unchanged after the record moves past it, and staleness is a
      pure function of the world's current head.
  (c) A-MAY-DO-ACTING-OFFLINE — the offline slice NEVER returns ALLOWED. A may-do defers to a fresh
      record read; only the must-nots act offline (ruling 16). This battery proves a planted offline
      may-do does not proceed and no draft is ever locally approved.
  (d) A-SLICE-WIDER-THAN-REACH — the cut is filtered by space_reaches; a rule scoped to a sibling
      subspace is NOT in the session's cut, and a must-not is never applied to an act outside its
      reach. Acting on the slice offline only ever REFUSES or DEFERS — it writes nothing (one pen per
      record, I1).

Every acceptance carries its planted control, driven THROUGH the method (a control that cannot fail
is the defect, §A42/§A64). Runner of record: PER-MODULE, no discover, no pytest.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                                  # noqa: E402
from kernel import border                                            # noqa: E402


def _kernel(prefix):
    d = tempfile.mkdtemp(prefix=prefix)
    return build_kernel(os.path.join(d, "record.jsonl"))


class VT7LocalSlice(unittest.TestCase):
    """A session's cut of the top three levels: version+hash, stale-on-reconnect, must-nots cut off."""

    def setUp(self):
        self.store, self.gate, self.views = _kernel("vt7-")
        # Two sibling subspaces under the mother (space:root). A rule scoped to one binds a session
        # in it and NOT a sibling's — the reach filter (space_reaches) is the whole point of "never
        # wider than the actor's own reach".
        self.gate.execute("CREATE-SPACE", "owner", {"name": "a", "parent": "space:root"})
        self.gate.execute("CREATE-SPACE", "owner", {"name": "b", "parent": "space:root"})
        self._rule(rule_id="NO-DELETE-IN-A", polarity="-", scope="space:a",
                   when=[{"action": "DELETE"}], then=[{"refuse": "NO-DELETE-IN-A"}],
                   text="no delete in space a")
        self._rule(rule_id="MAY-READ-IN-A", polarity="+", scope="space:a",
                   when=[{"action": "READ"}], then=[], text="may read in space a")
        self._rule(rule_id="NO-WRITE-IN-B", polarity="-", scope="space:b",
                   when=[{"action": "WRITE"}], then=[{"refuse": "NO-WRITE-IN-B"}],
                   text="no write in space b")
        self.session_a = {"actor": "alice", "space": "space:a"}
        self.session_b = {"actor": "bob", "space": "space:b"}

    def _rule(self, **payload):
        """Plant one raw CREATE-RULE (the test_ep39/test_vt1 store._append idiom): active_rules folds
        it by its payload.rule_id — polarity/when/scope controlled precisely, no gate ceremony."""
        self.store._append({"actor": "owner", "action": "CREATE-RULE",
                            "rule_cited": "ROOT-NEG-5", "payload": payload})

    # ---- A1 — a session's slice of levels 1-3 with its version and hash --------------------------

    def test_A1_cut_carries_version_and_hash_and_the_binding_rules(self):
        cut = self.views.local_slice(self.session_a)
        # carries the record VERSION it was cut from — an INDEPENDENT chain_head read (border module)
        self.assertEqual(cut["cut_version"], border.chain_head(self.store))
        # carries a content HASH in the estate's one seal shape
        self.assertTrue(cut["cut_hash"].startswith("sha256:"))
        # the binding rules are cut and split by polarity
        self.assertIn("NO-DELETE-IN-A", cut["must_nots"])          # a planted don't (polarity '-')
        self.assertIn("MAY-READ-IN-A", cut["may_dos"])             # a planted do   (polarity '+')
        # the constitution's own don'ts bind every session (root reaches all) — the cut is OF the
        # binding rules, not just the one planted for this space
        self.assertTrue(any(r.startswith("ROOT-NEG") for r in cut["must_nots"]))
        # every must-not carried IS a polarity '-' active rule (no re-authoring, no invented set)
        ar = self.views.active_rules()
        for rid in cut["must_nots"]:
            self.assertEqual(ar[rid].get("polarity"), "-")

    def test_A1_cut_hash_is_deterministic_at_one_head(self):
        # two cuts of the same session at the same head are byte-identical — a pure derivation
        c1 = self.views.local_slice(self.session_a)
        c2 = self.views.local_slice(self.session_a)
        self.assertEqual(c1["cut_hash"], c2["cut_hash"])
        self.assertEqual(c1["cut_version"], c2["cut_version"])

    def test_A1_different_session_is_a_different_cut(self):
        ca = self.views.local_slice(self.session_a)
        cb = self.views.local_slice(self.session_b)
        # the subspace-scoped don'ts partition by reach: A's space:a ban binds A and not B; B's
        # space:b ban binds B and not A
        self.assertIn("NO-DELETE-IN-A", ca["must_nots"])
        self.assertNotIn("NO-DELETE-IN-A", cb["must_nots"])
        self.assertIn("NO-WRITE-IN-B", cb["must_nots"])
        self.assertNotIn("NO-WRITE-IN-B", ca["must_nots"])
        # a different binding set is a DIFFERENT cut (the carried hash differs)
        self.assertNotEqual(ca["cut_hash"], cb["cut_hash"])
        # both still carry the constitution's root don'ts (the shared floor)
        self.assertTrue(any(r.startswith("ROOT-NEG") for r in ca["must_nots"]))
        self.assertTrue(any(r.startswith("ROOT-NEG") for r in cb["must_nots"]))

    def test_A1_slice_never_wider_than_the_actors_reach(self):
        # I1 / stop (d): a rule scoped to a sibling subspace is OUTSIDE session A's reach and is NOT
        # in A's cut — the slice is exactly the rules binding this session's space, never wider
        ca = self.views.local_slice(self.session_a)
        self.assertNotIn("NO-WRITE-IN-B", ca["must_nots"])
        self.assertNotIn("NO-WRITE-IN-B", ca["may_dos"])

    # ---- A2 — stale on reconnect, by derivation --------------------------------------------------

    def test_A2_reads_live_against_the_head_it_was_cut_from(self):
        # the LIVE control — the check CAN fail (return False): a cut compared to the head it was cut
        # from is not stale
        cut = self.views.local_slice(self.session_a)
        self.assertFalse(self.views.slice_stale(cut))

    def test_A2_planted_moved_record_reads_the_slice_stale(self):
        cut = self.views.local_slice(self.session_a)
        self.assertFalse(self.views.slice_stale(cut))              # live before the move
        # PLANT a moved record — any later append advances the chain head past the cut version
        self.store._append({"actor": "owner", "action": "CREATE-INFO", "object": "doc1",
                            "rule_cited": "ROOT-NEG-5", "payload": {"kind": "content"}})
        self.assertTrue(self.views.slice_stale(cut))               # stale BY DERIVATION on reconnect

    def test_A2_binding_law_change_reads_the_slice_stale(self):
        cut = self.views.local_slice(self.session_a)
        # amend a binding don't's content (a new version of the same rule_id) — the record moves and
        # the seq-stripped content hash of the cut would change too
        self._rule(rule_id="NO-DELETE-IN-A", polarity="-", scope="space:a",
                   when=[{"action": "DELETE"}], then=[{"refuse": "NO-DELETE-IN-A"}],
                   text="no delete in space a — amended")
        self.assertTrue(self.views.slice_stale(cut))

    def test_A2_no_stored_stale_flag_the_cut_is_not_mutated(self):
        # stop (b): staleness is DERIVED, never stored. The cut carries no stale bit, and moving the
        # world past it does NOT mutate the cut — the P17 pattern (a cut outliving its head serves a
        # stale answer, computed, not flagged)
        cut = self.views.local_slice(self.session_a)
        self.assertNotIn("stale", cut)
        self.assertNotIn("is_stale", cut)
        snapshot = {k: (dict(v) if isinstance(v, dict) else v) for k, v in cut.items()}
        self.store._append({"actor": "owner", "action": "CREATE-INFO", "object": "doc2",
                            "rule_cited": "ROOT-NEG-5", "payload": {"kind": "content"}})
        self.assertTrue(self.views.slice_stale(cut))               # derived stale
        self.assertEqual(cut, snapshot)                            # the cut itself is unchanged

    # ---- A3 — must-nots live while cut off; fail closed ------------------------------------------

    def test_A3_offline_must_not_violation_is_refused(self):
        cut = self.views.local_slice(self.session_a)
        # PLANTED offline must-not violation — a DELETE in space:a, refused by the frozen don't
        draft = {"actor": "alice", "action": "DELETE", "object": "x", "payload": {"space": "space:a"}}
        decision = self.views.slice_offline_decision(cut, draft)
        self.assertEqual(decision["decision"], "REFUSED")
        self.assertEqual(decision["rule"], "NO-DELETE-IN-A")
        self.assertEqual(decision["under"], "NO-DELETE-IN-A")

    def test_A3_offline_may_do_does_not_proceed(self):
        cut = self.views.local_slice(self.session_a)
        # PLANTED offline may-do — a READ in space:a matches MAY-READ-IN-A (polarity '+'); offline it
        # is NOT decided locally: it DEFERS to a fresh record read, never ALLOWED (stop c)
        draft = {"actor": "alice", "action": "READ", "object": "x", "payload": {"space": "space:a"}}
        decision = self.views.slice_offline_decision(cut, draft)
        self.assertEqual(decision["decision"], "DEFER")
        self.assertNotEqual(decision["decision"], "ALLOWED")

    def test_A3_offline_has_no_allow_path_fail_closed(self):
        cut = self.views.local_slice(self.session_a)
        # an act matching NEITHER a must-not nor a may-do still gets no local YES — the offline slice
        # can only refuse or defer, never approve (fail-closed)
        draft = {"actor": "alice", "action": "CREATE-INFO", "object": "x",
                 "payload": {"space": "space:a", "kind": "content"}}
        decision = self.views.slice_offline_decision(cut, draft)
        self.assertEqual(decision["decision"], "DEFER")
        self.assertNotEqual(decision["decision"], "ALLOWED")

    def test_A3_offline_must_not_out_of_reach_is_not_applied(self):
        # a must-not is never applied to an act outside its reach — a DELETE in space:b evaluated
        # against A's cut is NOT refused by A's space:a ban (space_reaches('space:a','space:b') False)
        cut = self.views.local_slice(self.session_a)
        draft = {"actor": "alice", "action": "DELETE", "object": "x", "payload": {"space": "space:b"}}
        self.assertEqual(self.views.slice_offline_decision(cut, draft)["decision"], "DEFER")

    def test_A3_brake_reads_the_frozen_must_nots_not_the_live_record(self):
        # THE 'CUT OFF' CONTROL: the brake evaluates the FROZEN must-nots carried in the cut, never
        # the live record. A ban planted AFTER the cut is invisible to the old cut (still DEFER) but
        # present in a fresh cut (REFUSED) — proving the offline decision is over the frozen slice.
        cut = self.views.local_slice(self.session_a)
        self._rule(rule_id="NO-CREATE-IN-A", polarity="-", scope="space:a",
                   when=[{"action": "CREATE-INFO"}], then=[{"refuse": "NO-CREATE-IN-A"}],
                   text="no create in space a — planted after the cut")
        draft = {"actor": "alice", "action": "CREATE-INFO", "object": "x",
                 "payload": {"space": "space:a", "kind": "content"}}
        self.assertEqual(self.views.slice_offline_decision(cut, draft)["decision"], "DEFER")
        fresh = self.views.local_slice(self.session_a)
        self.assertEqual(self.views.slice_offline_decision(fresh, draft)["decision"], "REFUSED")

    # ---- A4 — no founding, no new field ----------------------------------------------------------

    def test_A4_must_nots_and_may_dos_reuse_the_existing_polarity_field(self):
        # no new field: the split reads the EXISTING payload.polarity ('-' don't / '+' do), the same
        # field the gate's don't-firing reads (gate.py). A rule carrying no polarity is neither a
        # must-not nor a may-do.
        cut = self.views.local_slice(self.session_a)
        ar = self.views.active_rules()
        for rid in cut["must_nots"]:
            self.assertEqual(ar[rid].get("polarity"), "-")
        for rid in cut["may_dos"]:
            self.assertEqual(ar[rid].get("polarity"), "+")


if __name__ == "__main__":
    unittest.main()
