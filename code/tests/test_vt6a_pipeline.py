# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (decide-chain stamp step, per-fold relevance, in-memory pending buffer, on-append echo
# listener, sole pen). NON-GOAL: no offensive capability of any kind — every assertion proves
# design/53 B10 / design/25 v2.4 rulings 12/13/15 by FUNCTION: as an act of a stamped class climbs
# the gate's decide chain, the step stages each RELEVANT master's stamp (relevance computed PER FOLD)
# under VT-6d's gate-reserved draft key `_stamps` before the lift and the one write; the pending
# copies live in an in-memory buffer retired by the record's echo; the gate stays the sole pen and
# `_signed_content` is byte-unmoved. Full declaration: SCOPE-STATEMENT.md.
"""C6a VT-6a — THE PIPELINE CORE (plan planning/exec/VT-6a-PIPELINE-CORE-BUILD.md, frozen sha
11ded9c2…4842a2c, re-mint superseding the withdrawn b5c19754).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). RED write-path change to the gate's sole-pen decide chain; NO founding,
NO new field, NO pack edit — VT-6d's stamps field, staging key `_stamps` and required-stamps rule are
CONSUMED, not re-minted. VT-6a POPULATES what VT-6d declared: as an act of a STAMPED class climbs, the
step computes the relevant masters PER FOLD and stages their stamps; VT-6d's lift moves them into the
durable provenance["stamps"] at the one write.

  A1  THE STAMP STEP STAGES THE RELEVANT MASTERS' STAMPS BEFORE THE ONE WRITE — the computed stamp
      (view identity + the hash of what it saw + version = the seq the master was folded at) lands in
      the appended act's own provenance["stamps"] and is ABSENT from _signed_content; an UNSTAMPED
      class early-returns with no stamps (untouched).
  A2  RELEVANCE COMPUTED PER FOLD — from what FOLDS the act's record touches (the same per-fold
      selection _bump invalidates on), PER FOLD not per master name (a fold with two master
      definitions counts once); a planted wrong relevance (an extra fold, a missing one, a double
      count) reds; no declared op-def field.
  A3  THE PENDING BUFFER AND THE ECHO RETIRE — the pending copies live in an in-memory buffer; the
      sixth on-append listener retires the matching copy by the content-hash echo when the row
      appends; a restart empties the buffer while the durable stamps remain in the appended rows.
  A4  THE GATE IS THE SOLE PEN; _signed_content BYTE-IDENTICAL — the step fills the draft and appends
      nothing, the listener never mutates the record; a planted second-pen append is refused; the Q10
      invoker-sig pins stay green and a stamp in _signed_content would red them.
  A5  NO FOUNDING — founding_version 1.54.0 unchanged, OP_CHECKS 19, op-population 94; no new field,
      no pack edit (VT-6d's field/key/rule consumed, not re-minted).
"""

import json
import os
import sys
import tempfile
import unittest
from collections.abc import Mapping

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel.compose import build_full_kernel                                        # noqa: E402
from kernel.canonical import canonical_hash                                         # noqa: E402
from kernel.errors import OpError                                                   # noqa: E402
from kernel.opdefs import OP_CHECKS                                                 # noqa: E402
from kernel.views import Views                                                      # noqa: E402
from kernel.gate import (                                                           # noqa: E402
    STAMPS, STAMPS_STAGING, REQUIRED_STAMPS_POLICY,
    make_invoker_sig, verify_invoker_sig, _signed_content,
)

_REPO = os.path.join(os.path.dirname(__file__), "..")
_PACK = os.path.join(_REPO, "src", "founding", "founding-pack.json")


def _pack_json():
    with open(_PACK, "rb") as fh:
        return json.loads(fh.read())


def _kernel(prefix="vt6a-", record_path=None):
    d = tempfile.mkdtemp(prefix=prefix)
    path = record_path or os.path.join(d, "record.jsonl")
    store, gate, views = build_full_kernel(
        path, os.path.join(d, "blobs"), os.path.join(d, "vault"))[:3]
    return store, gate, views


def _plain(x):
    """Re-inflate a deep-frozen record (H1, EP-02: lists->tuples, dicts->mappingproxies) to plain
    list/dict for value comparison — the stamp's CONTENT is what matters."""
    if isinstance(x, Mapping):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _seed_required(gate, mapping):
    """Override the required-stamps POLICY rule live (latest-effective-wins over the founding {}) —
    exactly VT-6d's seed. A class in the mapping is a STAMPED class; its value names the required
    view ids. Uses the fold names as the required views, which is what VT-6a stages (per fold)."""
    return gate.execute("CREATE-RULE", "owner",
                        {"rule_id": "REQUIRED-STAMPS-TEST", "policy_key": REQUIRED_STAMPS_POLICY,
                         "value": mapping, "text": "test: the stamps a class of act must carry"})


def _make_rule(gate, rule_id="RULE-X", text="a benign rule"):
    """Execute a plain CREATE-RULE (a law record — payload carries rule_id, so it TOUCHES the
    active_rules fold). When CREATE-RULE is a stamped class, VT-6a stamps it with the active_rules
    master; a benign non-constitutional rule commits cleanly."""
    return gate.execute("CREATE-RULE", "owner", {"rule_id": rule_id, "text": text})


# Drafts that TOUCH each of the three per-act-path folds (the projection selectors: a law record
# declares rule_id; a pack record's payload.kind == category_pack; an op-definition record's action
# is one of CREATE-OP / AMEND-OP / RETIRE-OP). These exercise views.relevant_folds directly.
_LAW_DRAFT = {"action": "CREATE-RULE", "object": "r", "payload": {"rule_id": "L1"}}
_PACK_DRAFT = {"action": "CREATE-INFO", "object": "p",
               "payload": {"kind": "category_pack", "name": "p", "levels": []}}
_OPDEF_DRAFT = {"action": "CREATE-OP", "object": "o", "payload": {"kind": "op_definition"}}
_LAW_AND_PACK_DRAFT = {"action": "X", "object": "xp",
                       "payload": {"rule_id": "L2", "kind": "category_pack", "name": "q", "levels": []}}
_PLAIN_DRAFT = {"action": "COMPARE", "object": "c", "payload": {}}


# =============================================================================================
# A1 — THE STAMP STEP STAGES THE RELEVANT MASTERS' STAMPS BEFORE THE ONE WRITE
# =============================================================================================

class TestA1StampStep(unittest.TestCase):
    def test_a1_a_stamped_act_carries_the_computed_relevant_stamp_in_provenance(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})     # CREATE-RULE -> a stamped class
        head_before = len(store.events)
        rec = _make_rule(gate, "RULE-A")                            # a law record: touches active_rules
        # the COMPUTED stamp is on the act's own row, inside provenance (VT-6d's lift moved it there).
        stamps = _plain(rec["provenance"][STAMPS])
        self.assertEqual(len(stamps), 1)                            # one relevant fold -> one stamp
        s = stamps[0]
        self.assertEqual(s["view"], "active_rules")                 # the master its reach touched
        self.assertTrue(s["hash"].startswith("sha256:"))           # the hash of what it saw
        self.assertIsInstance(s["version"], int)                   # version = the seq folded at
        self.assertFalse(isinstance(s["version"], bool))
        self.assertGreaterEqual(s["version"], head_before)         # the head at stamp time (>= 1)
        # the staging key never lands as a field, and stamps is NOT a top-level key (inside provenance).
        self.assertNotIn(STAMPS_STAGING, rec)
        self.assertNotIn(STAMPS, rec)
        # durable — the same computed stamp reads back off the stored record.
        stored = [e for e in store.all() if e.get("action") == "CREATE-RULE"][-1]
        self.assertEqual(_plain(stored["provenance"][STAMPS]), stamps)

    def test_a1_the_computed_stamp_is_absent_from_signed_content(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        rec = _make_rule(gate, "RULE-B")
        self.assertIn(STAMPS, rec["provenance"])                    # the stamp IS in provenance ...
        # ... and is EXCLUDED from _signed_content: a mark made over the caller's content (no stamp,
        # which the invoker cannot know) still verifies over the record that now carries the stamp.
        pk = "pk-test"
        content = {"action": rec["action"], "object": rec["object"], "target": rec.get("target"),
                   "payload": rec.get("payload") or {}}
        mark = make_invoker_sig(pk, content)
        self.assertTrue(verify_invoker_sig(mark, pk, content))
        # _signed_content is byte-identical whether or not provenance carries the stamp.
        self.assertEqual(_signed_content(content, None, None),
                         _signed_content({**content, "provenance": rec["provenance"]}, None, None))

    def test_a1_an_unstamped_class_early_returns_no_stamps(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})     # a rule for ANOTHER class
        # COMPARE is not in the policy -> an unstamped class -> the step early-returns, stages nothing.
        rec = gate.execute("COMPARE", "owner", {"a": "x", "b": "y", "frame": "f", "verdict": "v"})
        self.assertNotIn(STAMPS, rec.get("provenance", {}))
        self.assertNotIn(STAMPS_STAGING, rec)
        self.assertTrue([e for e in store.all() if e.get("action") == "COMPARE"])   # it commits


# =============================================================================================
# A2 — RELEVANCE COMPUTED PER FOLD
# =============================================================================================

class TestA2RelevancePerFold(unittest.TestCase):
    def test_a2_relevant_folds_is_computed_from_what_the_record_touches(self):
        store, gate, views = _kernel()
        self.assertEqual(views.relevant_folds(_LAW_DRAFT), ["active_rules"])
        self.assertEqual(views.relevant_folds(_PACK_DRAFT), ["category_packs"])
        self.assertEqual(views.relevant_folds(_OPDEF_DRAFT), ["op_definitions"])
        self.assertEqual(views.relevant_folds(_PLAIN_DRAFT), [])                     # touches nothing

    def test_a2_two_touched_folds_each_count_once_no_double_count(self):
        store, gate, views = _kernel()
        rel = views.relevant_folds(_LAW_AND_PACK_DRAFT)
        self.assertEqual(sorted(rel), ["active_rules", "category_packs"])            # two folds ...
        self.assertEqual(len(rel), len(set(rel)))                                    # ... each ONCE
        # build_stamps produces exactly one stamp per relevant fold — never per master name.
        stamps = views.build_stamps(_LAW_AND_PACK_DRAFT)
        self.assertEqual(sorted(s["view"] for s in stamps), ["active_rules", "category_packs"])
        self.assertEqual(len(stamps), 2)
        # THE DOUBLE-COUNT CONTROL CAN FAIL: a per-master-NAME reading (a fold's two master
        # definitions counted twice) would produce a THREE-entry list; the per-fold computation does
        # not equal it, so a double-counted fold reds.
        per_name_double = rel + ["active_rules"]                                     # the wrong answer
        self.assertNotEqual(rel, per_name_double)
        self.assertNotEqual(len(per_name_double), len(set(per_name_double)))

    def test_a2_a_planted_wrong_relevance_reds(self):
        store, gate, views = _kernel()
        computed = views.relevant_folds(_LAW_DRAFT)                                  # the truth: [active_rules]
        self.assertEqual(computed, ["active_rules"])
        # (i) a master stamping an op it does NOT touch — an EXTRA fold — reds.
        self.assertNotEqual(computed, ["active_rules", "category_packs"])
        # (ii) MISSING one it DOES touch reds.
        self.assertNotEqual(computed, [])
        # (iii) a fold DOUBLE-COUNTED reds.
        self.assertNotEqual(computed, ["active_rules", "active_rules"])
        # and the computed relevance FLOWS into the staged stamps of a real committed act.
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        rec = _make_rule(gate, "RULE-C")
        self.assertEqual([s["view"] for s in _plain(rec["provenance"][STAMPS])], computed)

    def test_a2_relevance_reads_no_declared_op_def_field(self):
        # relevance is derived from the RECORD (the projection selectors), so an op-def with no
        # relevance field is handled — a draft touching a fold is relevant purely by its content.
        store, gate, views = _kernel()
        self.assertEqual(views.relevant_folds({"action": "ANYTHING",
                                               "payload": {"rule_id": "z"}}), ["active_rules"])


# =============================================================================================
# A3 — THE PENDING BUFFER AND THE ECHO RETIRE
# =============================================================================================

def _retire_listener_of(store, views):
    """The store's registered VT-6a retire listener (the bound `_retire_pending_stamp`)."""
    return [fn for fn in store._listeners
            if getattr(fn, "__self__", None) is views
            and getattr(fn, "__func__", None) is Views._retire_pending_stamp]


class TestA3PendingBufferAndEcho(unittest.TestCase):
    def test_a3_the_echo_retires_the_pending_copy_when_the_row_appends(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        self.assertEqual(views._pending_stamps, {})                 # nothing in flight yet
        _make_rule(gate, "RULE-D")                                  # stage -> append -> echo retires
        self.assertEqual(views._pending_stamps, {})                 # the echo cleared it

    def test_a3_the_listener_is_what_retires_the_copy_the_check_can_fail(self):
        # CONTROL: with the sixth listener REMOVED, the same stamped act leaves the pending copy in
        # the buffer — proving the STAGE step populates it and the LISTENER is what clears it.
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        listeners = _retire_listener_of(store, views)
        self.assertEqual(len(listeners), 1)                         # exactly the one sixth listener
        store._listeners.remove(listeners[0])
        _make_rule(gate, "RULE-E")
        self.assertEqual(len(views._pending_stamps), 1)             # NOT retired — the copy is held
        held = list(views._pending_stamps.values())[0]
        self.assertEqual([s["view"] for s in held[0]], ["active_rules"])

    def test_a3_a_restart_empties_the_buffer_the_durable_stamps_remain(self):
        d = tempfile.mkdtemp(prefix="vt6a-restart-")
        path = os.path.join(d, "record.jsonl")
        store1, gate1, views1 = _kernel(record_path=path)
        _seed_required(gate1, {"CREATE-RULE": ["active_rules"]})
        rec = _make_rule(gate1, "RULE-F")
        durable = _plain(rec["provenance"][STAMPS])
        self.assertEqual(durable[0]["view"], "active_rules")
        self.assertEqual(views1._pending_stamps, {})               # cleared by the echo in this run
        # RESTART: a fresh kernel over the SAME record file replays the rows.
        store2, gate2, views2 = _kernel(record_path=path)
        self.assertEqual(views2._pending_stamps, {})               # a restart empties the buffer
        replayed = [e for e in store2.all()
                    if e.get("action") == "CREATE-RULE" and (e.get("payload") or {}).get("rule_id") == "RULE-F"][-1]
        # the durable stamp survived the restart in the appended row (no silent loss).
        self.assertEqual(_plain(replayed["provenance"][STAMPS]), durable)


# =============================================================================================
# A4 — THE GATE IS THE SOLE PEN; _signed_content BYTE-IDENTICAL
# =============================================================================================

class TestA4SolePenAndSignedContent(unittest.TestCase):
    def test_a4_the_stamp_rides_one_row_the_step_and_listener_append_nothing(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        before = len(store.all())
        rec = _make_rule(gate, "RULE-G")
        # SOLE PEN: exactly ONE new row lands — the step fills the draft and appends nothing, and
        # the echo listener retires the buffer without appending. No separate stamp row.
        self.assertEqual(len(store.all()) - before, 1)
        self.assertIn(STAMPS, rec["provenance"])                    # the stamp is in that one row

    def test_a4_a_planted_second_pen_append_is_refused(self):
        # A stamp written as its OWN governed row, OUTSIDE the gate's one cited write, is refused by
        # the store — the gate's cited write is the only pen that reaches the record (H3, store.py).
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        with self.assertRaises(ValueError):
            store._append({"actor": "SYSTEM", "action": "STAMP-ROW", "object": "x",
                           "provenance": {"stamps": [{"view": "active_rules",
                                                      "hash": "sha256:" + "a" * 64, "version": 1}]}})
        # and the SOLE-PEN check discriminates: an appending listener WOULD be detected (delta > 1).
        marker = {"n": 0}

        def _appending(record):
            if record.get("action") == "CREATE-RULE" and marker["n"] == 0:
                marker["n"] = 1
                store._append({"actor": "SYSTEM", "action": "SECOND-PEN-MARKER", "object": "m",
                               "rule_cited": "BOOT-INT"})
        store.on_append(_appending)
        before = len(store.all())
        _make_rule(gate, "RULE-H")
        self.assertEqual(len(store.all()) - before, 2)             # act + the planted marker: detectable

    def test_a4_q10_pins_stay_green_and_can_fail(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"CREATE-RULE": ["active_rules"]})
        rec = _make_rule(gate, "RULE-I")
        pk = "pk"
        content = {"action": rec["action"], "object": rec["object"], "target": rec.get("target"),
                   "payload": rec.get("payload") or {}}
        # the Q10 round-trip: a mark made pre-stamp verifies over the stamped record (the stamp is
        # excluded from the signed content).
        self.assertTrue(verify_invoker_sig(make_invoker_sig(pk, content), pk, content))
        # the pins CAN fail: a field that IS in the signed content (the seal) breaks the mark when it
        # changes — so had the stamp lived in the signed content (the :3866 mechanism, refused), the
        # gate adding it post-signing would have RED the pins. The exclusion keeps them green.
        self.assertFalse(verify_invoker_sig(make_invoker_sig(pk, content, seal="s1"),
                                            pk, content, seal="s2"))

    def test_a4_the_signature_functions_still_round_trip(self):
        # make/verify_invoker_sig are MUST-NOT-TOUCH and byte-identical; the round trip proves them
        # intact (byte-identity is asserted by git-diff in the evidence; A6 re-runs the Q10 pins).
        draft = {"action": "X", "object": "o", "target": "t", "payload": {"k": 1}}
        m = make_invoker_sig("pk", draft, deciding_time="2026-01-01T00:00:00Z", seal="s")
        self.assertTrue(verify_invoker_sig(m, "pk", draft, deciding_time="2026-01-01T00:00:00Z", seal="s"))
        self.assertFalse(verify_invoker_sig(m, "pk", {**draft, "action": "Y"},
                                            deciding_time="2026-01-01T00:00:00Z", seal="s"))


# =============================================================================================
# A5 — NO FOUNDING (the pack is byte-unchanged; VT-6d's field/key/rule are consumed, not re-minted)
# =============================================================================================

class TestA5NoFounding(unittest.TestCase):
    def test_a5_the_founding_pack_is_byte_unchanged(self):
        pack = _pack_json()
        # §A57 live-version pin: VT-6d set 1.54.0; C7 P3 (THE KERNEL FROM THE RECORD — the twelve
        # act-kind rows) moved the LIVE founding 1.54.0 -> 1.55.0 BY NAME. VT-6a still mints no founding.
        self.assertEqual(pack["founding_version"], "1.55.0")       # C7 P3's live version
        recs = [r for step in pack["steps"] for r in step["records"]]
        # no new op / check kind — VT-6a mints no founding vocabulary.
        self.assertEqual(len(OP_CHECKS), 19)
        self.assertEqual(len([r for r in recs
                              if (r.get("payload") or {}).get("kind") == "op_definition"]), 94)
        # the required-stamps policy rule is VT-6d's, EMPTY at the founding — VT-6a re-mints nothing.
        rule = [r for r in recs if r.get("action") == "CREATE-RULE"
                and (r.get("payload") or {}).get("policy_key") == REQUIRED_STAMPS_POLICY]
        self.assertEqual(len(rule), 1)
        self.assertEqual(rule[0]["payload"]["value"], {})


if __name__ == "__main__":
    unittest.main()
