# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (record fold, sideways bounce, unseen flag, stamp divergence, the rogue-chief test).
# NON-GOAL: no offensive capability of any kind — every assertion proves design/53 B10 / design/25
# v2.4 rulings 12/14/15 by FUNCTION: two record folds over the DURABLE stamps in the committed act
# rows (provenance["stamps"], VT-6d) flag a fact whose co-stamping masters disagree on the record
# version they saw (naming the stale master) and a row of a stamped class a relevant master never
# stamped (a row written past the views). The folds read rows only — never the in-memory pending
# buffer (:3885) — and append nothing; detection never legitimacy. Full declaration: SCOPE-STATEMENT.md.
"""C6a VT-6c — THE TWO CHECKS (plan planning/exec/VT-6c-TWO-CHECKS-BUILD.md, frozen sha
6781a0f7…c5b0fe).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). GREEN — two record folds over existing machinery: VT-6a's `relevant_folds`
and VT-6d's durable `provenance["stamps"]` are CONSUMED, not re-authored; NO founding, NO new
op/law/check kind, NO new field, NO pack edit.

  A1  THE SIDEWAYS BOUNCE FLAGS A DIVERGING STAMP — a record fold groups the stamps touching one fact
      (the act's row) and flags any fact whose relevant masters' stamps hold more than one distinct
      version; a PLANTED stale master (stamped at an older record version -> a divergent hash) is
      flagged and NAMED; agreeing stamps are not flagged; the fold appends nothing and reads no buffer.
  A2  THE UNSEEN FLAG — a record fold over committed rows of a stamped class flags any row a RELEVANT
      master (computed by relevant_folds) never stamped; a PLANTED past-the-views row is flagged unseen;
      a fully-stamped row is not; the fold appends nothing and reads no buffer.
  A3  DETECTION NEVER LEGITIMACY — the checks FLAG, they never bless; a refused act stays refused
      carrying its stamps; three agreeing stamps add no legitimacy; a PLANTED "three stamps overturn a
      refusal" reds.
  A4  GREEN, NO FOUNDING — founding_version 1.54.0 unchanged, OP_CHECKS 19, op-population 94; no new
      field, no pack edit; the two folds join the contradictions/paper_tigers family.
"""

import json
import os
import sys
import tempfile
import unittest
from collections.abc import Mapping

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel.compose import build_full_kernel                                        # noqa: E402
from kernel.opdefs import OP_CHECKS                                                 # noqa: E402
from kernel.gate import STAMPS, REQUIRED_STAMPS_POLICY                              # noqa: E402

_REPO = os.path.join(os.path.dirname(__file__), "..")
_PACK = os.path.join(_REPO, "src", "founding", "founding-pack.json")

_H1 = "sha256:" + "a" * 64
_H2 = "sha256:" + "b" * 64
_H3 = "sha256:" + "c" * 64


def _pack_json():
    with open(_PACK, "rb") as fh:
        return json.loads(fh.read())


def _kernel(prefix="vt6c-"):
    d = tempfile.mkdtemp(prefix=prefix)
    path = os.path.join(d, "record.jsonl")
    store, gate, views = build_full_kernel(
        path, os.path.join(d, "blobs"), os.path.join(d, "vault"))[:3]
    return store, gate, views


def _seed_required(gate, mapping):
    """Override the required-stamps POLICY rule live (latest-effective-wins over the founding {}) —
    exactly VT-6a/VT-6d's seed. A class in the mapping is a STAMPED class; its value names the
    required view ids (the fold names, which is what the climb stages per fold)."""
    return gate.execute("CREATE-RULE", "owner",
                        {"rule_id": "REQUIRED-STAMPS-TEST", "policy_key": REQUIRED_STAMPS_POLICY,
                         "value": mapping, "text": "test: the stamps a class of act must carry"})


def _plant(store, stamps=None, refused=False, rule_id="PLANT", action="CREATE-RULE"):
    """Write a row DIRECTLY through the store, PAST THE GATE (past the views) — exactly VT-6a A4's
    seam. `store._append` mints seq/record_time and chains it; the gate's stamp step never runs, so
    the provenance (and its stamps, if any) is exactly what is planted. A rule_cited is supplied
    because the full kernel's store requires one (H3). Returns the committed (frozen) row."""
    ev = {"actor": "owner", "action": action, "object": "x", "rule_cited": "SYS-RECORD",
          "payload": {"rule_id": rule_id}}
    if stamps is not None:
        ev["provenance"] = {"asserted_by": "owner", "source": "system", "could_read": [],
                            "stamps": stamps}
    if refused:
        ev["refused"] = True
    return store._append(ev)


def _stamp(view, version, saw_hash):
    return {"view": view, "hash": saw_hash, "version": version}


# =============================================================================================
# A1 — THE SIDEWAYS BOUNCE FLAGS A DIVERGING STAMP
# =============================================================================================

class TestA1SidewaysBounce(unittest.TestCase):
    def test_a1_a_planted_stale_master_diverges_and_is_named(self):
        store, gate, views = _kernel()
        # a fact whose co-stamps DISAGREE on the record version they saw: active_rules stamped at the
        # head (version 5), category_packs stamped at an OLDER version (3) -> a stale master, a
        # divergent hash. The two masters held part of the same fact and one saw a stale world.
        row = _plant(store, stamps=[_stamp("active_rules", 5, _H1),
                                    _stamp("category_packs", 3, _H2)])
        found = views.stamp_divergences()
        hit = [f for f in found if f["seq"] == row["seq"]]
        self.assertEqual(len(hit), 1)                                   # the fact is flagged
        self.assertEqual(hit[0]["stale_masters"], ["category_packs"])   # the stale master NAMED
        self.assertEqual(hit[0]["versions"], [3, 5])                    # the diverging versions shown

    def test_a1_agreeing_stamps_are_not_flagged(self):
        store, gate, views = _kernel()
        # two masters co-stamping ONE act at the SAME head agree on what they saw -> no divergence.
        agree = _plant(store, stamps=[_stamp("active_rules", 5, _H1),
                                      _stamp("category_packs", 5, _H2)], rule_id="AGREE")
        found = views.stamp_divergences()
        self.assertFalse([f for f in found if f["seq"] == agree["seq"]])
        # a real gate-produced act carries ONE stamp for its one relevant fold -> cannot diverge.
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        rec = gate.execute("CREATE-RULE", "owner", {"rule_id": "REAL", "text": "benign"})
        self.assertEqual(len(rec["provenance"][STAMPS]), 1)
        self.assertFalse([f for f in views.stamp_divergences() if f["seq"] == rec["seq"]])

    def test_a1_the_fold_appends_nothing(self):
        store, gate, views = _kernel()
        _plant(store, stamps=[_stamp("active_rules", 5, _H1), _stamp("category_packs", 3, _H2)])
        before = len(store.all())
        views.stamp_divergences()
        self.assertEqual(len(store.all()), before)                     # a pure derivation

    def test_a1_the_fold_reads_rows_not_the_buffer(self):
        # the check reads the DURABLE rows only; a stamp exists only in a row (:3885). Seeding the
        # in-memory pending buffer with a would-be divergence changes nothing — the control CAN fail:
        # were the fold to consult the buffer, this answer would move.
        store, gate, views = _kernel()
        clean = views.stamp_divergences()
        self.assertEqual(clean, [])                                    # no stamped rows yet
        views._pending_stamps.setdefault("echo", []).append(
            [_stamp("active_rules", 5, _H1), _stamp("category_packs", 3, _H2)])   # a buffer divergence
        self.assertEqual(views.stamp_divergences(), clean)            # unmoved: rows only


# =============================================================================================
# A2 — THE UNSEEN FLAG (the rogue-chief test)
# =============================================================================================

class TestA2UnseenFlag(unittest.TestCase):
    def test_a2_a_planted_past_the_views_row_is_flagged_unseen(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})         # CREATE-RULE is a stamped class
        # a row of the stamped class written PAST the views — no master stamped it (empty stamps).
        row = _plant(store, stamps=[], rule_id="PAST")
        found = views.unseen_rows()
        hit = [f for f in found if f["seq"] == row["seq"]]
        self.assertEqual(len(hit), 1)                                   # flagged unseen
        self.assertEqual(hit[0]["unseen_masters"], ["active_rules"])    # the master its reach touched, NAMED

    def test_a2_a_fully_stamped_row_is_not_flagged(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        # a real gate-produced act: the relevant master (active_rules) stamped it as it climbed.
        rec = gate.execute("CREATE-RULE", "owner", {"rule_id": "SEEN", "text": "benign"})
        self.assertEqual([s["view"] for s in rec["provenance"][STAMPS]], ["active_rules"])
        self.assertFalse([f for f in views.unseen_rows() if f["seq"] == rec["seq"]])
        # CONTROL: a past-the-views row (missing that stamp) in the SAME world IS flagged, so the
        # negative above is a real pass, not an empty query.
        past = _plant(store, stamps=[], rule_id="PAST2")
        self.assertTrue([f for f in views.unseen_rows() if f["seq"] == past["seq"]])

    def test_a2_the_fold_appends_nothing_and_reads_rows_not_the_buffer(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        _plant(store, stamps=[], rule_id="PAST3")
        before = len(store.all())
        found = views.unseen_rows()
        self.assertEqual(len(store.all()), before)                     # appends nothing
        # rows only: a buffer copy that would "service" the row changes nothing.
        views._pending_stamps.setdefault("echo", []).append([_stamp("active_rules", 9, _H1)])
        self.assertEqual(views.unseen_rows(), found)                   # unmoved: rows only


# =============================================================================================
# A3 — DETECTION NEVER LEGITIMACY
# =============================================================================================

class TestA3DetectionNeverLegitimacy(unittest.TestCase):
    def test_a3_a_refused_act_with_three_agreeing_stamps_stays_refused(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        # a REFUSED row carrying THREE agreeing stamps — the "three views agree" case (ruling 14).
        refused = _plant(store, refused=True, rule_id="REF",
                         stamps=[_stamp("active_rules", 9, _H1),
                                 _stamp("category_packs", 9, _H2),
                                 _stamp("op_definitions", 9, _H3)])
        self.assertTrue(refused.get("refused"))
        before = len(store.all())
        div = views.stamp_divergences()
        uns = views.unseen_rows()
        # the checks append nothing — a pure derivation, no bless, no un-refuse.
        self.assertEqual(len(store.all()), before)
        # THE PLANTED "THREE STAMPS OVERTURN A REFUSAL" REDS: the refused act stays refused, every
        # copy of it on the record; no number of agreeing stamps outvotes the record (ruling 14).
        for e in store.all():
            if (e.get("payload") or {}).get("rule_id") == "REF":
                self.assertTrue(e.get("refused"))                      # still refused
        # three agreeing stamps are NOT even a divergence finding (agreement is not a flag) ...
        self.assertFalse([f for f in div if f["seq"] == refused["seq"]])
        # ... and NO fold output carries a legitimacy verdict — the findings are anomaly rows only.
        for f in div + uns:
            for blessed in ("legitimate", "approved", "permit", "lawful", "blessed"):
                self.assertNotIn(blessed, f)

    def test_a3_the_folds_only_ever_return_findings(self):
        # detection is a FINDING on the owner queue, never a gate verdict: the folds return LISTS
        # (possibly empty) of anomaly rows and change no record's standing.
        store, gate, views = _kernel()
        self.assertIsInstance(views.stamp_divergences(), list)
        self.assertIsInstance(views.unseen_rows(), list)


# =============================================================================================
# A4 — GREEN, NO FOUNDING (the two folds join the contradictions/paper_tigers family)
# =============================================================================================

class TestA4GreenNoFounding(unittest.TestCase):
    def test_a4_the_founding_pack_is_byte_unchanged(self):
        pack = _pack_json()
        # §A57 live-version pin: VT-6d set 1.54.0; C7 P3 (THE KERNEL FROM THE RECORD — the twelve
        # act-kind rows) moved the LIVE founding 1.54.0 -> 1.55.0 BY NAME. VT-6c still mints no founding.
        self.assertEqual(pack["founding_version"], "1.55.0")           # C7 P3's live version
        recs = [r for step in pack["steps"] for r in step["records"]]
        self.assertEqual(len(OP_CHECKS), 19)                           # no new check kind
        self.assertEqual(len([r for r in recs
                              if (r.get("payload") or {}).get("kind") == "op_definition"]), 94)
        # the required-stamps policy rule is VT-6d's, EMPTY at the founding — VT-6c re-mints nothing.
        rule = [r for r in recs if r.get("action") == "CREATE-RULE"
                and (r.get("payload") or {}).get("policy_key") == REQUIRED_STAMPS_POLICY]
        self.assertEqual(len(rule), 1)
        self.assertEqual(rule[0]["payload"]["value"], {})

    def test_a4_the_checks_are_pure_derivations_that_append_nothing(self):
        # two folds, no new verb / field: an empty world yields empty findings and no write.
        store, gate, views = _kernel()
        before = len(store.all())
        self.assertEqual(views.stamp_divergences(), [])
        self.assertEqual(views.unseen_rows(), [])
        self.assertEqual(len(store.all()), before)


if __name__ == "__main__":
    unittest.main()
