"""C6 P8b — THE PAIRING ENFORCES (the held act-door refusal flipped LIVE).

Acceptance battery A1-A7, per-module runnable
(`PYTHONPATH=src:tests python3 -m unittest tests.test_p8b_pairing_enforces`). Every probe is a
regression test, and each planted control is shown ABLE TO RED (the refusal fires where it should
and admits where it should — a check that cannot fail is no check).

WHAT P8b FLIPS (archi ruling :3726): the (actor class, task cell) pairing P8 built and HELD is
enforced LIVE at the gate's write chokepoint (gate.Gate._pairing_step). An actor whose DECLARED class
lacks the arm the op's cell requires is refused BY NAME and the refusal recorded as a row. THREE
bodies are OUTSIDE the pairing:
  * the recorder-system (PC_RUNTIME / SYSTEM) — A4;
  * a FOREIGN body's ASK / INPUT (a border SUBMIT / a peer INPUT) — B16 "the cut bounds who EXECUTES a
    rule, never who may ASK"; the RECEIPT (our actor's transformation) IS paired;
  * a None band — an UNCLASSIFIED actor (admitted; from the flip forward a None band cannot be WRITTEN,
    A6 closing the CREATE-ACCOUNT write to the closed domain).
No history is re-judged: the census reads 0 before the flip (A5); the door changes behaviour forward.
The pairing LOGIC itself (views.pair / pairing_census / RECORDER_SYSTEM_ACTORS) is READ and reused,
never re-authored. NO founding move: no new op / law / check kind, no pack edit, no version bump.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel              # noqa: E402
from kernel.errors import OpError                          # noqa: E402
from kernel import border                                 # noqa: E402
from kernel.opdefs import CELL, STRUCTURAL_PARAMS, OP_CHECKS  # noqa: E402
from founding.install import op_definitions               # noqa: E402


# A governed pure-S op with simple params, used to drive the pairing at a structured cell.
_S_OP = "COMPARE"
_S_PARAMS = {"a": "x", "b": "y", "frame": "f", "verdict": "v"}


class _World(unittest.TestCase):
    """A disposable world founded from the PRODUCTION pack v1.51.0 — the pairing is enforced live."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))

    # --- helpers -----------------------------------------------------------------------------
    def _account(self, aid, klass):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": aid, "actor_class": klass})

    def _plant_cell_op(self, name, cell):
        """CREATE-OP a governed op declaring `cell` (owner acts — a human, admitted at every cell)."""
        self.gate.execute("CREATE-OP", "owner",
                          {"name": name, "definition": {"law_cited": "SOP", "object_param": "x",
                           "params": {"x": "required"}, "checks": [], STRUCTURAL_PARAMS: ["x"],
                           CELL: cell}})

    def _refusal_rows(self, opname, actor):
        return [e for e in self.store.all()
                if e.get("action") == "op-refused"
                and (e.get("payload") or {}).get("op") == opname and e.get("target") == actor]

    def _admits(self, opname, actor, params):
        try:
            self.gate.execute(opname, actor, dict(params))
        except OpError as e:
            self.fail(f"{actor}@{opname} was refused ({e.rule}) but should have been admitted")

    def _refuses(self, opname, actor, params, rule):
        with self.assertRaises(OpError) as cm:
            self.gate.execute(opname, actor, dict(params))
        self.assertEqual(cm.exception.rule, rule)
        return cm.exception


# =====================================================================================
# A1 — AN AI AT A STRUCTURED OP IS REFUSED LIVE, BY NAME, RECORDED (and the passing control).
# =====================================================================================
class TestA1AiAtStructuredRefusedLive(_World):
    def test_ai_at_a_pure_S_op_is_refused_at_the_gate_by_name_and_recorded(self):
        self._account("aibot", "ai")
        exc = self._refuses(_S_OP, "aibot", _S_PARAMS, "CELL-LAW")     # refused LIVE (not merely censused)
        # the reason names the class, the cell and the missing arm:
        self.assertIn("ai", str(exc))
        self.assertIn("'S'", str(exc))
        self.assertIn("structured-arm", str(exc))
        # RECORDED AS A ROW (one pen — the gate's own recorded refusal, citing the rule by name):
        rows = self._refusal_rows(_S_OP, "aibot")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("rule_cited"), "CELL-LAW")

    def test_the_same_act_by_a_class_holding_the_arm_passes_the_check_can_fail(self):
        # program and human hold the structured arm — admitted at the same op (the check DISCRIMINATES).
        self._account("prog", "program")
        self._account("hum", "human")
        self._admits(_S_OP, "prog", _S_PARAMS)
        self._admits(_S_OP, "hum", _S_PARAMS)

    def test_the_pairing_binds_the_RECEIPT_execute_but_never_the_foreign_submit_ask(self):
        # B16: the cut bounds who EXECUTES a rule, never who may ASK. An outside AI entity's BORDER-SUBMIT
        # (a foreign ASK) is ADMITTED; the SAME class doing a RECEIPT (our actor's EXECUTE) is REFUSED.
        self._account("twc", "ai")
        border.submit(self.gate, "twc", {"pack": {"unstructured": {"count": 1}, "structured": {}}})  # ASK: admitted
        with self.assertRaises(OpError) as cm:
            border.record_receipt(self.gate, "sha256:feed", {"key": "k", "genesis": "g"},
                                  "ed25519-sig:x", actor="twc")                                       # EXECUTE: refused
        self.assertEqual(cm.exception.rule, "CELL-LAW")


# =====================================================================================
# A2 — A PROGRAM AT A JUDGMENT CELL IS REFUSED; A PROGRAM AT A PURE-S CELL PASSES.
# =====================================================================================
class TestA2ProgramAtJudgmentRefused(_World):
    def test_a_program_is_refused_at_every_judgment_cell_and_admitted_at_the_structured_cell(self):
        self._account("prog", "program")
        for i, cell in enumerate(("U", "U{s}", "S{u}")):
            op = "JUDGE_%d" % i
            self._plant_cell_op(op, cell)
            exc = self._refuses(op, "prog", {"x": "k%d" % i}, "CELL-LAW")   # a judgment cell: refused
            self.assertIn("program", str(exc))
            self.assertIn("unstructured-arm", str(exc))                     # the arm it lacks
        # a program AT A PURE-S CELL passes (the check discriminates):
        self._admits(_S_OP, "prog", _S_PARAMS)


# =====================================================================================
# A3 — A HUMAN ADMITS EVERY CELL (holds both arms; no human act refused by the pairing).
# =====================================================================================
class TestA3HumanAdmitsAll(_World):
    def test_a_human_is_admitted_at_S_and_at_every_judgment_cell(self):
        self._account("hum", "human")
        self._admits(_S_OP, "hum", _S_PARAMS)                              # S
        for i, cell in enumerate(("U", "U{s}", "S{u}")):
            op = "HJUDGE_%d" % i
            self._plant_cell_op(op, cell)
            self._admits(op, "hum", {"x": "h%d" % i})                      # every judgment cell


# =====================================================================================
# A4 — THE RECORDER-SYSTEM IS OUTSIDE THE PAIRING (a planted SYSTEM act at any cell passes).
# =====================================================================================
class TestA4RecorderSystemOutside(_World):
    def test_recorder_system_actors_are_never_refused_by_the_live_door_at_any_cell(self):
        self.assertEqual(self.views.RECORDER_SYSTEM_ACTORS, ("PC_RUNTIME", "SYSTEM"))
        self._plant_cell_op("SYSJUDGE", "U")                              # a judgment cell
        for who in ("SYSTEM", "PC_RUNTIME"):
            self._admits(_S_OP, who, _S_PARAMS)                          # a structured cell
            self._admits("SYSJUDGE", who, {"x": "s-%s" % who})           # a judgment cell — still admitted
        # no op-refused row was written against either recorder-system actor:
        self.assertEqual(self._refusal_rows(_S_OP, "SYSTEM"), [])
        self.assertEqual(self._refusal_rows("SYSJUDGE", "PC_RUNTIME"), [])


# =====================================================================================
# A5 — NO HISTORY RE-JUDGED; THE CENSUS READS 0 BEFORE THE FLIP (and the non-zero STOP control).
# =====================================================================================
class TestA5CensusZeroBeforeFlip(_World):
    def test_the_census_over_the_founding_reads_zero_would_refuse_and_reports_the_none_band(self):
        c = self.views.pairing_census(pack_version="1.51.0")
        self.assertEqual(c["counts"]["would_refuse"], 0)                  # nothing WOULD be refused
        self.assertEqual(c["counts"]["considered"], 0)                    # no non-system act is a subject
        self.assertIn("HELD", c["enforcement"])                          # the census itself still only measures
        # the None-band population is REPORTED beside the other counts (archi :3726 — visible, not hidden):
        self.assertIn("none_band_considered", c["counts"])
        self.assertEqual(c["counts"]["none_band_considered"], 0)         # 0 over the founding record

    def test_the_census_can_read_non_zero_the_stop_a_safety_can_fire(self):
        # STOP (a): the census MUST be able to read non-zero (else the safety is a check that cannot
        # fail). Plant an ai act the pairing would refuse — the census counts it, forward-only, WITHOUT
        # the door having been consulted (a pre-flip measurement over the record).
        self._account("aibot", "ai")
        self.store._append({"actor": "aibot", "action": _S_OP, "rule_cited": "SOP",
                            "object": "cmp:1", "payload": {}})
        c = self.views.pairing_census(pack_version="1.51.0")
        self.assertEqual(c["counts"]["would_refuse"], 1)                 # non-zero -> STOP -> raise, not flip
        self.assertEqual(c["would_refuse"][0]["actor"], "aibot")
        self.assertEqual(c["would_refuse"][0]["class"], "ai")

    def test_no_past_act_is_re_judged_the_founding_record_carries_no_pairing_refusal(self):
        # forward only: enforcing the door wrote no op-refused row over the founding record (the flip
        # changes behaviour for acts FROM the flip forward; a past act is never refused retroactively).
        pairing_refusals = [e for e in self.store.all()
                            if e.get("action") == "op-refused"
                            and e.get("rule_cited") == "CELL-LAW"]
        self.assertEqual(pairing_refusals, [])


# =====================================================================================
# A6 — CREATE-ACCOUNT REFUSES AN UN-CANONICAL ACTOR-CLASS TOKEN (and the canonical control).
# =====================================================================================
class TestA6CreateAccountTokenClosure(_World):
    def test_a_novel_non_canonical_token_is_refused_and_recorded(self):
        exc = self._refuses("CREATE-ACCOUNT", "owner",
                            {"account_id": "w1", "actor_class": "wizard"}, "CAP-IS-LAW")
        self.assertIn("wizard", str(exc))
        rows = self._refusal_rows("CREATE-ACCOUNT", "owner")
        self.assertTrue(any(r.get("rule_cited") == "CAP-IS-LAW" for r in rows))

    def test_a_retired_legacy_token_is_also_refused(self):
        # the refusal is the WHOLE closed domain, not just novel tokens: a retired legacy token
        # (process / agentic / system) is refused too (archi :3726 — broader than the dispatch draft).
        for legacy in ("process", "agentic", "system"):
            self._refuses("CREATE-ACCOUNT", "owner",
                          {"account_id": "leg-%s" % legacy, "actor_class": legacy}, "CAP-IS-LAW")

    def test_a_canonical_token_admits_the_check_can_fail(self):
        for good in ("human", "ai", "program"):
            self._admits("CREATE-ACCOUNT", "owner", {"account_id": "ok-%s" % good, "actor_class": good})
            self.assertEqual(self.views.class_band("ok-%s" % good), good)

    def test_the_domain_write_closure_matches_the_read_side_closed_domain(self):
        # the write closure uses the SAME closed domain K12 reads (no second list) — reuse, no new kind.
        self.assertEqual(set(self.views.class_domain()), {"human", "ai", "program"})


# =====================================================================================
# A7 — THE FOUNDING MOVE IS ABSENT; the door is inert before the law (wire-at-birth); builds+replays.
# =====================================================================================
class TestA7NoFoundingWireAtBirth(_World):
    def test_no_new_check_kind_and_op_population_unchanged(self):
        self.assertEqual(len(OP_CHECKS), 19)                             # NO new check kind (P8b mints none)
        # C6a VT-2 (CREATE-RELATIONSHIP MINTED live, 1.51.0 -> 1.52.0) moved the live base 93 -> 94 BY NAME (§A57).
        self.assertEqual(len(op_definitions()), 94)                      # live op-population (P8b +0; VT-2 +1)

    def test_the_founded_kernel_replays_to_identity(self):
        # the founding roundtrip survives the live door: a rebuild from the file adds nothing.
        store2, _g, _v, _b, _s = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.assertEqual(len(store2.all()), len(self.store.all()))


if __name__ == "__main__":
    unittest.main()
