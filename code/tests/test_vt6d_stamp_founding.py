# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (gate-added envelope field, provenance class, record chain, policy rule, gate step,
# required-stamps refusal, master-view stamp). NON-GOAL: no offensive capability of any kind — every
# assertion proves design/53 B10 / design/25 v2.4 (board :3869) by FUNCTION: a stamp is a gate-written
# field of the provenance class on the act's own row, excluded from the invoker's signed content and
# the store's countersignature, its stored integrity the record chain; a caller may not supply stamps;
# a class of act that a policy rule marks stamped is refused when a required stamp is missing, an
# unstamped class passes untouched; and no number of stamps makes an unlawful act lawful. Full
# declaration: SCOPE-STATEMENT.md.
"""C6a VT-6d — THE STAMP FOUNDING (plan planning/exec/VT-6d-STAMP-FOUNDING-BUILD.md).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). RED founding move — the required-stamps POLICY RULE is founding data
(founding_version 1.53.0 -> 1.54.0); the stamps FIELD is a GATE-ADDED envelope field in code (no
op-META, no opdefs edit, no store change). VT-6a (the climb that POPULATES stamps) and VT-6c (the two
read-side checks) are LATER units — this suite PLANTS stamps directly, via the gate-reserved draft key
`_stamps` on a test op's draft (never a caller param), to exercise the field, the rule and the refusal.

  A1  THE STAMPS FIELD (PROVENANCE CLASS) AND ITS THREE CONTROLS:
      (a) a CALLER-SUPPLIED stamps key in any op's params is refused, FOR EVERY OP (the gate writes
          stamps, never a caller); (b) a MALFORMED stamp is refused where the gate writes the list;
      (c) an ALTERED STORED stamp is caught by the record CHAIN (store.py:1044) — on a TAMPERED COPY
          / a constructed row sequence, never by mutating a live record.
  A2  THE STAMP RIDES THE ACT'S OWN ROW — durable at the one append, INSIDE provenance (the same
      class as the invoking account's signature), EXCLUDED from `_signed_content` and the store
      countersignature (Q10 stays green); NO separate stamp row; the finalised time never a row.
  A3  THE REQUIRED-STAMPS RULE IS A POLICY RULE READ BY A GATE STEP — a stamped-class act missing a
      required stamp is refused; an unstamped-class act passes untouched; NO new op/verb/check kind.
  A4  DETECTION NEVER LEGITIMACY — an act refused on its own merits stays refused even carrying its
      required stamps; three agreeing stamps add no legitimacy.
  A5  RED FOUNDING DISCIPLINE — founding_version 1.54.0; the pack carries the REQUIRED-STAMPS policy
      rule; OP_CHECKS 19, op-population 94 (no op/check kind added); no src engine module.
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
from kernel.gate import (                                                           # noqa: E402
    STAMPS, STAMPS_STAGING, REQUIRED_STAMPS_RULE, REQUIRED_STAMPS_POLICY,
    make_invoker_sig, verify_invoker_sig, _signed_content,
)

_REPO = os.path.join(os.path.dirname(__file__), "..")
_PACK = os.path.join(_REPO, "src", "founding", "founding-pack.json")


def _pack_json():
    with open(_PACK, "rb") as fh:
        return json.loads(fh.read())


def _kernel(prefix="vt6d-"):
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))[:3]
    return store, gate, views


def _plain(x):
    """The store DEEP-FREEZES a record (H1, EP-02): lists become tuples, dicts mappingproxies.
    Re-inflate to plain list/dict for value comparison — the stamp's CONTENT is what matters."""
    if isinstance(x, Mapping):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _stamp(view="auditor", saw_hash=None, version=1):
    """A well-formed master-view stamp (ruling 13): view identity + the hash of what it saw + the
    version = the seq the master was folded at."""
    return {"view": view, "hash": saw_hash or ("sha256:" + "a" * 64), "version": version}


def _seed_required(gate, mapping, minter="owner", rule_id="REQUIRED-STAMPS-TEST"):
    """Override the required-stamps POLICY rule live (latest-effective-wins over the founding {})."""
    return gate.execute("CREATE-RULE", minter,
                        {"rule_id": rule_id, "policy_key": REQUIRED_STAMPS_POLICY,
                         "value": mapping, "text": "test: the stamps a class of act must carry"})


def _register(gate, action, staged=None, rules=("ROOT-NEG-5",)):
    """A test op whose handler STAGES the pending stamps on the gate-reserved draft key (the climb's
    stand-in — a handler, never a caller param). `staged` is a list of stamps, or a non-list to
    exercise the shape control, or None to stage nothing."""
    def handler(actor, params):
        draft = {"actor": actor, "action": action, "object": "x", "rule_cited": "ROOT-NEG-5"}
        if staged is not None:
            draft[STAMPS_STAGING] = staged
        return draft
    gate.register(action, {"description": f"echo {action}", "rules": list(rules), "params": {}}, handler)


def _seed_dont(store, rule_id, action):
    """A recorded structural DON'T (full-form pass) that refuses a matching act — direct append, the
    genesis idiom (tests/test_full_form.py:_seed_law). Fires BEFORE the stamp step, so it is a
    non-stamp merit refusal for A4."""
    return store._append({"actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": rule_id,
                          "rule_cited": "BOOT-INT",
                          "payload": {"rule_id": rule_id, "polarity": "-",
                                      "when": [{"action": action}], "then": [{"refuse": rule_id}]}})


# =============================================================================================
# A1 — THE STAMPS FIELD (PROVENANCE CLASS) AND ITS THREE CONTROLS
# =============================================================================================

class TestA1FieldAndControls(unittest.TestCase):
    def test_a1a_caller_supplied_stamps_key_is_refused_for_every_op(self):
        store, gate, views = _kernel()
        _register(gate, "PLAIN-OP")
        # (a) the check CAN FAIL: a caller stamps key reds — on a plain op ...
        with self.assertRaises(OpError) as cm:
            gate.execute("PLAIN-OP", "owner", {"stamps": [_stamp()]})
        self.assertEqual(cm.exception.rule, REQUIRED_STAMPS_RULE)
        # ... on the reserved staging name too (a caller may name neither) ...
        with self.assertRaises(OpError) as cm2:
            gate.execute("PLAIN-OP", "owner", {STAMPS_STAGING: [_stamp()]})
        self.assertEqual(cm2.exception.rule, REQUIRED_STAMPS_RULE)
        # ... and FOR EVERY OP: an existing production op (COMPARE) is refused the same way.
        with self.assertRaises(OpError) as cm3:
            gate.execute("COMPARE", "owner",
                         {"a": "x", "b": "y", "frame": "f", "verdict": "v", "stamps": [_stamp()]})
        self.assertEqual(cm3.exception.rule, REQUIRED_STAMPS_RULE)
        # the refusal is a RECORDED row, and the act never committed.
        self.assertEqual(store.by_action("PLAIN-OP"), [])
        self.assertTrue(any(r["rule_cited"] == REQUIRED_STAMPS_RULE
                            for r in store.by_action("op-refused")))
        # CONTROL — the check can also PASS: no stamps key, the op commits.
        rec = gate.execute("PLAIN-OP", "owner", {})
        self.assertEqual(rec["action"], "PLAIN-OP")
        self.assertNotIn(STAMPS, rec.get("provenance", {}))         # unstamped class, nothing written

    def test_a1b_a_malformed_stamp_is_refused_where_the_gate_writes_the_list(self):
        # every malformed shape reds; a well-formed one passes (the check can fail AND pass).
        bad_cases = {
            "missing-hash": [{"view": "auditor", "version": 1}],
            "missing-view": [{"hash": "sha256:" + "a" * 64, "version": 1}],
            "missing-version": [{"view": "auditor", "hash": "sha256:" + "a" * 64}],
            "version-not-a-seq": [{"view": "auditor", "hash": "sha256:" + "a" * 64, "version": "1"}],
            "version-zero-not-a-seq": [_stamp(version=0)],
            "version-bool-not-a-seq": [{"view": "auditor", "hash": "sha256:" + "a" * 64, "version": True}],
            "stamp-not-a-dict": ["auditor"],
            "stamps-not-a-list": {"view": "auditor"},
        }
        for label, staged in bad_cases.items():
            store, gate, views = _kernel()
            _seed_required(gate, {"MAL-OP": ["auditor"]})
            _register(gate, "MAL-OP", staged=staged)
            with self.assertRaises(OpError, msg=label) as cm:
                gate.execute("MAL-OP", "owner", {})
            self.assertEqual(cm.exception.rule, REQUIRED_STAMPS_RULE, label)
        # CONTROL — a well-formed stamp on the same stamped class commits.
        store, gate, views = _kernel()
        _seed_required(gate, {"MAL-OP": ["auditor"]})
        _register(gate, "MAL-OP", staged=[_stamp()])
        rec = gate.execute("MAL-OP", "owner", {})
        self.assertEqual(_plain(rec["provenance"][STAMPS]), [_stamp()])

    def test_a1c_an_altered_stored_stamp_is_caught_by_the_record_chain(self):
        # I use a TAMPERED COPY handed to the chain's own hash (store.py:1044 pins
        # canonical_hash(prior record) on the next record's prev_hash) — NEVER a live record or the
        # record file (a record is never edited). A constructed row sequence.
        store, gate, views = _kernel()
        _seed_required(gate, {"CHAIN-OP": ["auditor"]})
        _register(gate, "CHAIN-OP", staged=[_stamp()])
        rec = gate.execute("CHAIN-OP", "owner", {})                    # the stamp is on the act's own row
        self.assertEqual(_plain(rec["provenance"][STAMPS]), [_stamp()])
        pinned = canonical_hash(rec)             # what store.py:1044 pins as the NEXT record's prev_hash
        # CONTROL — an untampered copy still hashes to the pinned link (the chain holds).
        untampered = _plain(rec)
        self.assertEqual(canonical_hash(untampered), pinned)
        # TAMPER a COPY: alter the stored stamp -> the chain's recomputed link no longer matches.
        tampered = _plain(rec)
        tampered["provenance"][STAMPS][0]["hash"] = "sha256:" + "b" * 64
        self.assertNotEqual(canonical_hash(tampered), pinned)
        # the verifier exists and reports (the live store is unanchored here -> vacuously ok).
        self.assertIn("ok", store.verify_chain())


# =============================================================================================
# A2 — THE STAMP RIDES THE ACT'S OWN ROW, EXCLUDED FROM THE SIGNED CONTENT
# =============================================================================================

class TestA2RowHomeAndExclusion(unittest.TestCase):
    def test_a2_stamp_rides_the_acts_own_row_durable_no_separate_row(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"A2-OP": ["auditor"]})
        _register(gate, "A2-OP", staged=[_stamp()])
        before = len(store.all())
        rec = gate.execute("A2-OP", "owner", {})
        # rides the act's OWN row, inside provenance (the provenance class), durable at the one append.
        self.assertEqual(_plain(rec["provenance"][STAMPS]), [_stamp()])
        self.assertNotIn(STAMPS_STAGING, rec)                 # the staging key never lands as a field
        self.assertNotIn(STAMPS, rec)                         # not a top-level field, inside provenance
        # durable — the same stamp reads back off the stored record.
        stored = [e for e in store.all() if e.get("action") == "A2-OP"][-1]
        self.assertEqual(_plain(stored["provenance"][STAMPS]), [_stamp()])
        # NO separate stamp record row: exactly ONE new row landed for the act.
        self.assertEqual(len(store.all()) - before, 1)
        # the finalised time never touches a row (ruling 13).
        self.assertNotIn("finalised_time", rec)
        self.assertNotIn("finalized_time", rec)

    def test_a2_the_stamp_is_excluded_from_the_signed_content_Q10_stays_green(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"A2S-OP": ["auditor"]})
        _register(gate, "A2S-OP", staged=[_stamp()])
        rec = gate.execute("A2S-OP", "owner", {})
        # an invoker signs the act it INTENDED — BEFORE the gate adds the stamp (it cannot know it).
        draft_no_stamp = {"action": "A2S-OP", "object": "x", "target": None, "payload": {}}
        pk = "pk-test"
        mark = make_invoker_sig(pk, draft_no_stamp)
        # the mark made pre-stamp still verifies over the record that now carries the stamp (Q10) —
        # because _signed_content excludes provenance (and so the stamp).
        rec_view = {"action": rec["action"], "object": rec["object"], "target": rec.get("target"),
                    "payload": rec.get("payload") or {}}
        self.assertTrue(verify_invoker_sig(mark, pk, rec_view))
        # the exclusion, shown directly: _signed_content is byte-identical whether or not provenance
        # carries a stamp — a stamp value cannot enter it, so a stamp placed there would break no mark.
        self.assertEqual(_signed_content(draft_no_stamp, None, None),
                         _signed_content({**draft_no_stamp, "provenance": {"stamps": [_stamp()]}},
                                         None, None))
        # and the pins CAN fail: a field that IS in the signed content (the seal) breaks the mark when
        # it changes — so had the stamp lived in the signed content (the :3866 mechanism, refused),
        # the gate adding it post-signing would have RED the Q10 pins. The exclusion keeps them green.
        self.assertFalse(verify_invoker_sig(make_invoker_sig(pk, draft_no_stamp, seal="s1"),
                                            pk, draft_no_stamp, seal="s2"))

    def test_a2_the_signature_functions_still_round_trip(self):
        # make/verify_invoker_sig are MUST-NOT-TOUCH and byte-identical; the round trip proves them
        # intact (byte-identity is asserted by git-diff in the evidence; A6 re-runs the Q10 pins).
        draft = {"action": "X", "object": "o", "target": "t", "payload": {"k": 1}}
        m = make_invoker_sig("pk", draft, deciding_time="2026-01-01T00:00:00Z", seal="s")
        self.assertTrue(verify_invoker_sig(m, "pk", draft, deciding_time="2026-01-01T00:00:00Z", seal="s"))
        self.assertFalse(verify_invoker_sig(m, "pk", {**draft, "action": "Y"},
                                            deciding_time="2026-01-01T00:00:00Z", seal="s"))


# =============================================================================================
# A3 — THE REQUIRED-STAMPS RULE IS A POLICY RULE READ BY A GATE STEP
# =============================================================================================

class TestA3RuleAndStep(unittest.TestCase):
    def test_a3_the_rule_is_a_policy_rule_empty_at_the_founding(self):
        store, gate, views = _kernel()
        # a POLICY rule, read by policy_value — EMPTY {} at the founding (no production stamped class).
        self.assertEqual(views.policy_value(REQUIRED_STAMPS_POLICY), {})
        self.assertIn(REQUIRED_STAMPS_RULE, views.active_rules())
        _seed_required(gate, {"OP-Z": ["auditor"]})
        self.assertEqual(_plain(views.policy_value(REQUIRED_STAMPS_POLICY)), {"OP-Z": ["auditor"]})

    def test_a3_a_stamped_class_missing_a_required_stamp_is_refused(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"REQ-OP": ["auditor"]})
        _register(gate, "REQ-OP", staged=None)                        # a stamped class, no stamp staged
        with self.assertRaises(OpError) as cm:
            gate.execute("REQ-OP", "owner", {})
        self.assertEqual(cm.exception.rule, REQUIRED_STAMPS_RULE)
        self.assertEqual(store.by_action("REQ-OP"), [])
        # missing ONE of two required also reds.
        store2, gate2, views2 = _kernel()
        _seed_required(gate2, {"REQ2-OP": ["auditor", "budget"]})
        _register(gate2, "REQ2-OP", staged=[_stamp(view="auditor")])   # budget missing
        with self.assertRaises(OpError) as cm2:
            gate2.execute("REQ2-OP", "owner", {})
        self.assertEqual(cm2.exception.rule, REQUIRED_STAMPS_RULE)

    def test_a3_an_unstamped_class_passes_untouched(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"REQ-OP": ["auditor"]})                  # a rule that names ANOTHER op
        _register(gate, "FREE-OP", staged=None)                        # not in the rule -> unstamped
        rec = gate.execute("FREE-OP", "owner", {})
        self.assertEqual(rec["action"], "FREE-OP")
        self.assertNotIn(STAMPS, rec["provenance"])                    # untouched: no stamps written
        # and it commits without a stamp even though the rule is present for a DIFFERENT class.
        self.assertTrue([e for e in store.all() if e.get("action") == "FREE-OP"])

    def test_a3_no_new_op_verb_or_check_kind(self):
        # the founding move is a POLICY RULE, not an op/check kind.
        pack = _pack_json()
        recs = [r for step in pack["steps"] for r in step["records"]]
        rule = [r for r in recs if r.get("action") == "CREATE-RULE"
                and (r.get("payload") or {}).get("policy_key") == REQUIRED_STAMPS_POLICY]
        self.assertEqual(len(rule), 1)                                 # exactly one, founding data
        self.assertEqual(rule[0]["payload"]["value"], {})              # empty at the founding
        op_defs = [r for r in recs if (r.get("payload") or {}).get("kind") == "op_definition"]
        self.assertEqual(len(op_defs), 94)                             # op-population UNCHANGED
        self.assertEqual(len(OP_CHECKS), 19)                          # NO new check kind


# =============================================================================================
# A4 — DETECTION NEVER LEGITIMACY
# =============================================================================================

class TestA4DetectionNeverLegitimacy(unittest.TestCase):
    def test_a4_an_act_refused_on_its_own_merits_stays_refused_carrying_its_required_stamps(self):
        store, gate, views = _kernel()
        _seed_required(gate, {"MERIT-OP": ["auditor"]})
        _register(gate, "MERIT-OP", staged=[_stamp()])                # carries its REQUIRED stamp
        _seed_dont(store, "MERIT-NO", "MERIT-OP")                     # a recorded structural DON'T
        with self.assertRaises(OpError) as cm:
            gate.execute("MERIT-OP", "owner", {})
        # refused on the DON'T's own citation (a non-stamp merit), not on a stamp cite: the stamps
        # add NO legitimacy — a refused act stays refused however it is stamped.
        self.assertEqual(cm.exception.rule, "MERIT-NO")
        self.assertNotEqual(cm.exception.rule, REQUIRED_STAMPS_RULE)
        self.assertEqual(store.by_action("MERIT-OP"), [])

    def test_a4_three_agreeing_stamps_add_no_legitimacy(self):
        # a stamped class requiring one view W, carrying THREE well-formed stamps X/Y/Z but not W,
        # is refused (B10: three agreeing stamps add no legitimacy — a refused act stays refused).
        store, gate, views = _kernel()
        _seed_required(gate, {"THREE-OP": ["W"]})
        _register(gate, "THREE-OP", staged=[_stamp(view="X"), _stamp(view="Y"), _stamp(view="Z")])
        with self.assertRaises(OpError) as cm:
            gate.execute("THREE-OP", "owner", {})
        self.assertEqual(cm.exception.rule, REQUIRED_STAMPS_RULE)     # missing W, three stamps notwithstanding


# =============================================================================================
# A5 — RED FOUNDING DISCIPLINE (the pack moved once, lawfully, for the policy rule)
# =============================================================================================

class TestA5FoundingDiscipline(unittest.TestCase):
    def test_a5_the_founding_moved_one_minor_for_the_policy_rule(self):
        pack = _pack_json()
        # §A57 live-version pin: VT-6d's own move was 1.53.0 -> 1.54.0; C7 P3 (THE KERNEL FROM THE
        # RECORD — the twelve act-kind rows) moved the LIVE founding 1.54.0 -> 1.55.0 BY NAME. The
        # REQUIRED-STAMPS rule VT-6d minted is still present (asserted below), unchanged by C7 P3.
        self.assertEqual(pack["founding_version"], "1.55.0")
        recs = [r for step in pack["steps"] for r in step["records"]]
        self.assertTrue(any(r.get("action") == "CREATE-RULE"
                            and (r.get("payload") or {}).get("rule_id") == REQUIRED_STAMPS_RULE
                            for r in recs))
        # NO op / check kind added (a MINOR by a policy rule, not a new surface).
        self.assertEqual(len(OP_CHECKS), 19)
        self.assertEqual(len([r for r in recs
                              if (r.get("payload") or {}).get("kind") == "op_definition"]), 94)


if __name__ == "__main__":
    unittest.main()
