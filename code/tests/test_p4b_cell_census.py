# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (cell, declared structure, identity replay, judgment count, census). NON-GOAL: no
# offensive capability of any kind — every assertion proves L28 by function: every declared op reads
# its DECLARED cell, a declared-S op replays to identity, and the census REDS on a declared op with
# no cell or a declared-S op that does not replay. Full declaration: SCOPE-STATEMENT.md.
"""P4b · L28 [GREEN] — THE CELL CENSUS.

Acceptance (design/52 P4b), one instrument, the fifth sibling census:

  A1  COMPLETENESS — the census is over the WHOLE registry (len(rows) == len(gate.ops)); every
      DECLARED op carries a well-formed cell (the cell law's population); system ops are named,
      never findings; a PLANTED declared op with no cell REDS completeness.
  A2  DECLARED-S REPLAYS TO IDENTITY (else a finding) — the real founding is clean; a PLANTED
      declared-S op flagged `replays_to_identity: false` REDS; a declared-judgment op is never
      scored.
  A3  THE JUDGMENT COUNT DERIVED FROM ENFORCEMENT — over the outside constitution's derived pack
      (pwc-app, read-only), the U-enforced rule count is derived, carries its WORLD, and is
      compared to the retired lexical count; a doctored pack proves the comparison CAN diverge.
  A4  EVIDENCE-PINNED, A PLANTED MIS-DECLARATION REDS — the live reading rendered by `--md` equals
      the committed evidence table byte-for-byte; a planted mis-declaration reds the census.
  A5  the module is whole-ledger green per module (the runner-of-record acceptance).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.conformance import cell_census as P4b          # noqa: E402
from kernel.opdefs import CELL_SET, OP_CHECKS               # noqa: E402


# ============================================================================================
# A1 — COMPLETENESS over the whole registry; declared ops carry a cell; system ops are not findings.
# ============================================================================================

class TestA1Completeness(unittest.TestCase):

    def setUp(self):
        self._s, self.gate, self.views = P4b.build_full_kernel_for_census()
        self.rows = P4b.census(self.gate, self.views)

    def test_census_is_over_the_whole_registry(self):
        # completeness = enumeration (P3): one row per registered op, no more, no fewer.
        self.assertEqual(len(self.rows), len(self.gate.ops))
        self.assertEqual(sorted(r["op"] for r in self.rows), sorted(self.gate.ops))

    def test_every_row_carries_a_kind_and_reason(self):
        for r in self.rows:
            self.assertIn(r["kind"], {"declared", "system"},
                          "%s got an out-of-vocabulary kind %r" % (r["op"], r["kind"]))
            self.assertTrue(r["reason"], "%s carries no reason — every reading is recorded" % r["op"])

    def test_every_declared_op_has_a_wellformed_cell(self):
        # the cell law's population: every definition-born op declares a cell in the closed set.
        for r in P4b.declared_rows(self.rows):
            self.assertIn(r["cell"], CELL_SET,
                          "declared op %s has no well-formed cell (%r)" % (r["op"], r["cell"]))

    def test_completeness_findings_empty_on_real_founding(self):
        self.assertEqual(P4b.completeness_findings(self.rows), [],
                         "a declared op is missing a cell on the REAL founding — should be zero")

    def test_system_ops_are_named_never_findings(self):
        # code-registered kernel/bootstrap ops are OUTSIDE the founding cell law — reported by name,
        # never a finding, never guessed (archi P8 precision 3; install.py). The set is non-empty
        # (the recorder has real mechanics) and disjoint from any finding.
        sr = P4b.system_rows(self.rows)
        self.assertTrue(sr, "no system ops found — the composed kernel has code-registered primitives")
        for r in sr:
            self.assertFalse(r["finding"], "system op %s was flagged a finding — it is outside the law" % r["op"])
            self.assertIsNone(r["cell"])

    def test_planted_declared_op_with_no_cell_reds_completeness(self):
        # THE POSITIVE CONTROL (behavioural): a declared op with no cell reds; removed, green again.
        defs = dict(self.views.op_definitions())
        self.assertEqual(P4b.completeness_findings(P4b.census_from(set(self.gate.ops), defs, {})), [])

        defs["CELL-LESS-PLANT"] = {"definition": {"description": "a declared op with no cell"}}
        op_names = set(self.gate.ops) | {"CELL-LESS-PLANT"}
        rows = P4b.census_from(op_names, defs, {})
        cf = [r["op"] for r in P4b.completeness_findings(rows)]
        self.assertIn("CELL-LESS-PLANT", cf,
                      "the planted cell-less op was NOT flagged — the completeness check cannot fail")
        self.assertEqual(len(rows), len(op_names))          # still complete WITH the plant

        del defs["CELL-LESS-PLANT"]
        self.assertEqual(P4b.completeness_findings(P4b.census_from(set(self.gate.ops), defs, {})), [])

    def test_planted_static_classify_of_a_cell_less_declared_op(self):
        # THE POSITIVE CONTROL (static): classify a declared op with no cell directly.
        row = P4b.classify_cell("X", definition={"description": "no cell"},
                                is_definition_born=True, replays=None)
        self.assertTrue(row["finding"])
        self.assertIsNone(row["cell"])


# ============================================================================================
# A2 — a declared-S op replays to identity (else a finding); a planted mis-declaration reds.
# ============================================================================================

class TestA2DeclaredSReplays(unittest.TestCase):

    def setUp(self):
        self._s, self.gate, self.views = P4b.build_full_kernel_for_census()
        self.rows = P4b.census(self.gate, self.views)

    def test_replay_findings_empty_on_real_founding(self):
        # the estate's founding property: every gov-os op is a structured record-mechanic that
        # replays. The estate's own guard (views.declared_s_findings) agrees.
        self.assertEqual(P4b.replay_findings(self.rows), [])
        self.assertEqual(self.views.declared_s_findings(), [])

    def test_planted_declared_s_that_does_not_replay_reds(self):
        # THE POSITIVE CONTROL (behavioural): a declared-S op honestly flagged non-replayable —
        # 'declared S, actually U' — reds; removed, green again.
        defs = dict(self.views.op_definitions())
        defs["MISDECLARED-JUDGE"] = {"definition": {"cell": "S", "replays_to_identity": False}}
        op_names = set(self.gate.ops) | {"MISDECLARED-JUDGE"}
        replay_of = {"MISDECLARED-JUDGE": False}
        rows = P4b.census_from(op_names, defs, replay_of)
        rf = [r["op"] for r in P4b.replay_findings(rows)]
        self.assertIn("MISDECLARED-JUDGE", rf,
                      "the planted declared-S-actually-U op was NOT flagged — the replay guard cannot fail")

        del defs["MISDECLARED-JUDGE"]
        self.assertEqual(P4b.replay_findings(P4b.census_from(set(self.gate.ops), defs, {})), [])

    def test_planted_static_classify_of_a_misdeclared_s(self):
        # THE POSITIVE CONTROL (static): classify a declared-S non-replaying op directly.
        row = P4b.classify_cell("Y", definition={"cell": "S", "replays_to_identity": False},
                                is_definition_born=True, replays=False)
        self.assertTrue(row["finding"])
        self.assertEqual(row["cell"], "S")

    def test_a_declared_judgment_op_is_never_a_replay_finding(self):
        # a declared-U op is validated to schema and NEVER scored — it is never a replay finding,
        # even with no replay reading (the machine does not judge the judgment; L28).
        for jcell in ("U", "U{s}", "S{u}"):
            row = P4b.classify_cell("J", definition={"cell": jcell},
                                    is_definition_born=True, replays=None)
            self.assertFalse(row["finding"], "a declared-%s op was wrongly scored" % jcell)
            self.assertEqual(row["cell"], jcell)

    def test_op_level_judgment_count_is_zero_on_gov_os(self):
        # gov-os's OWN registry: every declared op is S — the op-level judgment count is 0. Judgment
        # lives at stations, not in the recorder's ops (the paper's own claim, P8 disclosure 2).
        self.assertEqual(P4b.op_judgment_count(self.rows), [])


# ============================================================================================
# A3 — the outside constitution's judgment count, derived from enforcement, carries its world.
# ============================================================================================

class TestA3ConstitutionJudgmentCount(unittest.TestCase):

    def setUp(self):
        self.pack = P4b._lazy_derive_twc_pack()
        if self.pack is None:
            self.skipTest("apps/pwc-app is not present beside gov-os; the derived pack needs it")

    def test_derived_count_matches_lexical_and_carries_its_world(self):
        a3 = P4b.constitution_judgment_count(self.pack, as_of_head="HEAD", founding_version="1.51.0")
        # the enforcement-derived judgment count is over RULES (references excluded).
        self.assertEqual(a3["derived_judgment_count"] + a3["s_enforced_rules"], a3["rules"])
        # over THIS world the enforcement-derived count EQUALS the retired lexical count.
        self.assertTrue(a3["match"])
        self.assertEqual(a3["derived_judgment_count"], a3["lexical_count"])
        # the count is not a fact without its world (the pwc law-book hash P5 supplied).
        self.assertTrue(a3["world"]["derived_from"].get("law_book_sha256"))
        self.assertEqual(a3["world"]["outside_pack"], "TWC")
        # the honest disclosure: context (reference) rows carry no check but are NOT rules.
        self.assertEqual(a3["all_no_check"], a3["derived_judgment_count"] + a3["context_rows"])

    def test_the_comparison_can_diverge(self):
        # THE CHECK CAN FAIL: a doctored pack whose enforcement classification disagrees with the
        # lexical count publishes a DIVERGENCE, never smoothed. (A synthetic pack — never founded.)
        doctored = {
            "pack": "SYN", "version": "0.0",
            "source": {"law_book_sha256": "deadbeef", "batch_sha256": "cafe", "law_rows": 2},
            "rows": [
                {"class": "structured", "enforced_by": "structured"},   # S-enforced rule
                {"class": "unstructured", "enforced_by": "judgment"},   # U-enforced rule
            ],
            # lexical says ZERO unstructured — but enforcement finds ONE. They MUST diverge.
            "unstructured": {"count": 0},
        }
        a3 = P4b.constitution_judgment_count(doctored)
        self.assertFalse(a3["match"], "a divergence between enforcement and lexical was NOT reported")
        self.assertEqual(a3["derived_judgment_count"], 1)
        self.assertEqual(a3["lexical_count"], 0)


# ============================================================================================
# A4 — the live reading matches the committed evidence table (regenerated by --md only).
# ============================================================================================

class TestA4EvidencePin(unittest.TestCase):

    @unittest.skipUnless(
        os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planning/evidence/P4b-CELL-CENSUS/cell-census.md")),
        "SKIP PRIVATE-SOURCE: needs planning/evidence/P4b-CELL-CENSUS/cell-census.md (absent in the render)")
    def test_reading_matches_committed_evidence(self):
        _s, gate, views = P4b.build_full_kernel_for_census()
        rows = P4b.census(gate, views)
        a3 = P4b.build_a3()
        generated = P4b.render_markdown(rows, a3)
        with open(P4b.EVIDENCE_PATH, encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(
            generated.strip(), committed.strip(),
            "the cell census reading diverged from the committed evidence table — an op was added, "
            "a cell changed, or the world moved. Regenerate (never hand-edit): "
            "python3 -m tools.conformance.cell_census --md")

    def test_a_planted_mis_declaration_reds_the_census(self):
        # A4's own control: a planted mis-declaration (a judgment op declared S, caught by the
        # replay-to-identity guard) reds. Proven at the census level, not only the classifier.
        _s, gate, views = P4b.build_full_kernel_for_census()
        defs = dict(views.op_definitions())
        defs["MIS"] = {"definition": {"cell": "S", "replays_to_identity": False}}
        rows = P4b.census_from(set(gate.ops) | {"MIS"}, defs, {"MIS": False})
        self.assertTrue(P4b.replay_findings(rows),
                        "the planted mis-declaration did not red the census — A4's control is dead")


# ============================================================================================
# A3-GOV-OS — THIS constitution's judgment count, GENUINELY derived from enforcement and
# INDEPENDENT of the outside pack's shape regexes (archi :3711, the finding this delta fixes).
# ============================================================================================

class TestA3GovOsEnforcementDerived(unittest.TestCase):

    def setUp(self):
        self._s, self.gate, self.views = P4b.build_full_kernel_for_census()
        self.rules = P4b.gov_os_rule_population(self.views.active_rules())
        self.cited = P4b.gov_os_closed_kind_cited_rules(self.views.op_definitions())

    def test_the_count_reads_real_op_check_rows_of_a_closed_kind(self):
        # INDEPENDENCE, positively: every cite the gov-os reading uses came from a check row whose
        # `check` is a member of the CLOSED OP_CHECKS vocabulary — the estate's real enforcement
        # machinery, read directly. Never a shape regex.
        kinds_that_cited = set()
        for entry in self.views.op_definitions().values():
            definition = (entry or {}).get("definition") or {}
            for chk in (definition.get("checks") or []):
                if chk.get("cite"):
                    kinds_that_cited.add(chk.get("check"))
        self.assertTrue(kinds_that_cited, "no op check row carried a cite — the source would be empty")
        self.assertTrue(kinds_that_cited <= set(OP_CHECKS),
                        "a cite came from a check kind OUTSIDE the closed OP_CHECKS vocabulary")
        self.assertTrue(self.cited, "no rule is cited by any closed-kind check — the reading is empty")

    def test_the_gov_os_source_and_the_outside_source_are_disjoint_vocabularies(self):
        # THE FINDING, nailed: the gov-os enforcement vocabulary (OP_CHECKS) and the outside pack's
        # shape-regex vocabulary (test_ep51.CANDIDATE_KINDS) share NO name. The two counts cannot be
        # one count read twice — they read different things. (This is exactly what the outside figure
        # LACKED: its `enforced_by` was set by CANDIDATE_KINDS, so it and the lexical count coincided.)
        from test_ep51 import CANDIDATE_KINDS
        self.assertEqual(set(OP_CHECKS) & set(CANDIDATE_KINDS), set(),
                         "OP_CHECKS and CANDIDATE_KINDS share a name — the two sources are not independent")

    def test_the_count_partitions_the_rule_population(self):
        c = P4b.gov_os_constitution_count(self.rules, self.cited, founding_version="x")
        self.assertEqual(c["judgment_count"] + c["s_enforced"], c["rules"])
        self.assertGreater(c["s_enforced"], 0, "no rule is S-enforced — real machinery enforces some")
        self.assertGreater(c["judgment_count"], 0, "no rule is judgment/deferred — expected some")
        self.assertEqual(c["closed_kinds"], len(OP_CHECKS))
        self.assertEqual(c["world"]["founding_version"], "x")

    def test_a_planted_no_check_rule_moves_the_gov_os_count(self):
        # THE POSITIVE CONTROL (the check can fail): plant a law rule that NO closed-kind check row
        # cites -> the judgment count moves +1, and the rule lands in the judgment set, not the
        # S-enforced set. Removed, the count returns.
        base = P4b.gov_os_constitution_count(self.rules, self.cited)
        planted = dict(self.rules)
        planted["NO-CHECK-PLANT"] = {"rule_id": "NO-CHECK-PLANT", "kind": "rule"}
        moved = P4b.gov_os_constitution_count(planted, self.cited)
        self.assertEqual(moved["judgment_count"], base["judgment_count"] + 1,
                         "the planted no-check rule did NOT move the judgment count — the check cannot fail")
        self.assertEqual(moved["rules"], base["rules"] + 1)
        self.assertIn("NO-CHECK-PLANT", moved["judgment_rule_ids"])
        self.assertNotIn("NO-CHECK-PLANT", moved["s_enforced_rule_ids"])
        # a rule that IS cited by a closed-kind check row is S-enforced, never judgment — the other side.
        some_cited = sorted(self.cited & set(self.rules))[0]
        self.assertIn(some_cited, base["s_enforced_rule_ids"])
        self.assertNotIn(some_cited, base["judgment_rule_ids"])
        # removed -> back to base (the control clears).
        del planted["NO-CHECK-PLANT"]
        self.assertEqual(P4b.gov_os_constitution_count(planted, self.cited)["judgment_count"],
                         base["judgment_count"])

    def test_the_live_count_is_published_beside_the_outside_figure(self):
        # build_a3 carries BOTH figures in one dict from two independent sources; the gov-os figure
        # is always present (it needs no sibling app), the outside may be None if pwc-app is absent.
        a3 = P4b.build_a3()
        self.assertIn("gov_os", a3)
        self.assertIn("outside", a3)
        g = a3["gov_os"]
        self.assertEqual(g["judgment_count"] + g["s_enforced"], g["rules"])
        self.assertGreater(g["rules"], 0)


if __name__ == "__main__":
    unittest.main()
