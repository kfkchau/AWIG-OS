# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28V — the check-vocabulary comparator's own can-fail proofs, and the guard it arms.

`design/28` §5 says adding a check kind is "design-doc change + owner gate, never a quiet
addition", and for days FOUR kinds lived in `OP_CHECKS` with no row in that table. The law
had no instrument, so it was a warning; these rows are the mechanism.

READ THE DIRECTION BEFORE THE ROWS, because it is the one thing this file must never be
edited to relax: the table is AUTHORED LAW and is NEVER generated from `OP_CHECKS`. A
generator would make every quiet addition self-documenting and lawful, which is exactly
what the gate exists to prevent. The code is the SUBJECT; the table is the LAW.

  T-CHECKVOCAB-NO-DIVERGENCE   `OP_CHECKS` and §5's table agree in BOTH directions, and the
                               reconciliation carries no remainder. RED WORLD: any kind
                               added to the engine without its row, or any row left behind
                               by a retirement that does not say so in the row.
  T-CHECKVOCAB-CONTROL         the comparator finds KNOWN-PRESENT planted cases of every
                               shape it reports. This is not decoration: DEFECT 4's finding
                               is a SET DIFFERENCE, so a structurally broken comparator
                               returns exactly the clean zero a healthy one returns, and a
                               zero closes a question a wrong number would reopen. The row
                               above is uninterpretable without this one.
  T-CHECKVOCAB-NEAR-MISS       §A64 — a row whose status word is NEARLY right (`[RETIRING`,
                               `[retired`, `(a feed)`) FIRES rather than passes. A pattern
                               that has never met a near-miss has never been tested.
  T-CHECKVOCAB-REFUSES         the comparator refuses loudly on anything it cannot read
                               exactly, and never degrades to a partial set — a smaller
                               code side hides a missing row while looking green.
  T-DEFINITION-REF-TRACED      EP-28V W1's landing: §5's `definition_ref` row no longer
                               says UNTRACED, and the two rules it now names are the two
                               the check site actually defaults to. RED WORLD: the engine's
                               defaults change and the table does not follow.
"""
import ast
import importlib.util
import os
import unittest
import unittest.mock

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

# LOADED BY PATH, and `sys.path` is deliberately NOT touched. unittest runs the whole
# estate in one process, so a row that prepends a directory to the import path changes what
# every other module in the suite resolves — the battery owning something on its subject,
# and the shape that put nine phantom rows in a count one EP ago.
_SPEC = importlib.util.spec_from_file_location(
    "govos_docmap_checkvocab", os.path.join(_ROOT, "tools", "docmap", "checkvocab.py"))
cv = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cv)

def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


OPDEFS_SRC = _read(cv.OPDEFS)
DESIGN28_TEXT = _read(cv.DESIGN28)

#: A synthetic §5 table. Every planted-case row below is built from this by substitution,
#: so a can-fail proof varies exactly ONE thing against a world that is otherwise clean.
_CLEAN_DOC = f"""{cv.SECTION_HEADING} (synthetic)

| Check | Semantics | Refuses citing | Delivered |
|---|---|---|---|
| alpha | a live, documented kind | SOME-RULE | EP-00 |
| beta | a live, documented kind | SOME-RULE | EP-00 |

## 6. the next section
"""
_CLEAN_SRC = 'OP_CHECKS = ("alpha", "beta")\n'
_ROW = "| {name} | {semantics} | {cite} | EP-00 |\n"


def _doc_with(extra_rows=""):
    return _CLEAN_DOC.replace("\n## 6.", extra_rows + "\n## 6.")


class TestTheComparatorAgreesWithTheEstate(unittest.TestCase):
    """T-CHECKVOCAB-NO-DIVERGENCE — the guard this pass exists to arm."""

    def test_op_checks_and_design28_section5_do_not_diverge(self):
        undocumented, unbacked = cv.defect4(OPDEFS_SRC, DESIGN28_TEXT)
        self.assertEqual(undocumented, [],
                         "check kinds live in OP_CHECKS with no row in design/28 §5's "
                         "table — a quiet addition, which is the exact act §5's gate law "
                         "forbids: %r" % (undocumented,))
        self.assertEqual(unbacked, [],
                         "rows in design/28 §5 name no live check kind and carry no "
                         "legitimate-absence status in their own text: %r" % (unbacked,))

    def test_the_reconciliation_carries_no_remainder(self):
        """A count is the weaker check wearing the stronger one's name — so state the
        arithmetic, which is the one detector that fires on a discrepancy rather than on
        suspicious tidiness."""
        kinds = cv.check_kinds_from_source(OPDEFS_SRC)
        rows = cv.check_rows_from_doc(DESIGN28_TEXT)
        legitimate = [n for n, t in rows if cv.has_legitimate_absence(t)]
        self.assertEqual(sorted(legitimate), ["attenuation", "due"],
                         "the legitimate absences moved; each one is a row that switches "
                         "this comparator off for itself, so the set is stated here")
        self.assertEqual(len(kinds) + len(legitimate), len(rows),
                         "live kinds %d + legitimate absences %d != table rows %d"
                         % (len(kinds), len(legitimate), len(rows)))


class TestTheComparatorCanFail(unittest.TestCase):
    """T-CHECKVOCAB-CONTROL — planted cases of every shape the comparator reports.

    The row above returns a SET DIFFERENCE. A comparator that read nothing at all would
    return the same empty result, so without these the green above is a description of the
    code wearing a test's clothes.
    """

    def test_the_shipped_positive_control_passes(self):
        ok, detail = cv.positive_control()
        self.assertTrue(ok, "the control the tool runs on EVERY invocation failed: %s" % detail)

    def test_the_control_can_itself_fail_and_the_tool_then_reports_no_count(self):
        """A guard that cannot fail is not a guard, and that applies to the control as much
        as to the row it backs. Break the comparator in the one way that would make it
        silently permissive — treat every row as legitimately absent — and the control must
        notice, and the tool must print UNINTERPRETABLE where it would have printed a 0."""
        with unittest.mock.patch.object(cv, "has_legitimate_absence", lambda _text: True):
            ok, detail = cv.positive_control()
            self.assertFalse(ok, "a comparator that excuses every row passed its control")
            self.assertIn("planted unbacked rows not found", detail)
            lines, healthy = cv.report()
            self.assertFalse(healthy)
            self.assertIn("UNINTERPRETABLE", lines[0])
            self.assertTrue(any("positive control FAILED" in ln for ln in lines))

    def test_a_planted_key_in_the_code_fires_the_code_to_doc_direction(self):
        planted = 'OP_CHECKS = ("alpha", "beta", "planted_quiet_addition")\n'
        undocumented, unbacked = cv.defect4(planted, _CLEAN_DOC)
        self.assertEqual(undocumented, ["planted_quiet_addition"])
        self.assertEqual(unbacked, [])

    def test_a_planted_row_in_the_table_fires_the_doc_to_code_direction(self):
        doc = _doc_with(_ROW.format(name="planted_orphan_row",
                                    semantics="a row backed by no live kind",
                                    cite="SOME-RULE"))
        undocumented, unbacked = cv.defect4(_CLEAN_SRC, doc)
        self.assertEqual(undocumented, [])
        self.assertEqual(unbacked, ["planted_orphan_row"],
                         "set-diff BOTH DIRECTIONS: a table row that outlives its kind is "
                         "as much a divergence as a kind that outruns its row")

    def test_a_planted_retired_row_does_not_fire(self):
        doc = _doc_with(_ROW.format(name="planted_retired",
                                    semantics="[RETIRED 2026-01-01, some EP] withdrawn",
                                    cite="—"))
        self.assertEqual(cv.defect4(_CLEAN_SRC, doc), ([], []))

    def test_a_planted_feed_row_does_not_fire(self):
        doc = _doc_with(_ROW.format(name="planted_feed",
                                    semantics="a read-only feed for the executor",
                                    cite="— (a feed, not a refusal)"))
        self.assertEqual(cv.defect4(_CLEAN_SRC, doc), ([], []))

    def test_a_kind_planted_into_the_REAL_engine_source_fires_against_the_REAL_table(self):
        """The live guard's own red world, exhibited on the real subjects rather than on a
        synthetic pair. A can-fail proof over synthetic text proves the FUNCTION can fail;
        this proves the row above can fail — the same distinction that put four kinds in
        the engine and none in the table."""
        planted = OPDEFS_SRC.replace('OP_CHECKS = ("require_prior"',
                                     'OP_CHECKS = ("planted_quiet_addition", "require_prior"', 1)
        self.assertNotEqual(planted, OPDEFS_SRC, "the planted substitution matched nothing")
        undocumented, unbacked = cv.defect4(planted, DESIGN28_TEXT)
        self.assertEqual(undocumented, ["planted_quiet_addition"])
        self.assertEqual(unbacked, [])

    def test_a_row_deleted_from_the_REAL_table_fires_against_the_REAL_engine(self):
        """The other direction on the real subjects: a documented kind whose row is removed
        while the kind stays live."""
        stripped = "\n".join(line for line in DESIGN28_TEXT.splitlines()
                             if not line.startswith("| fingerprint |"))
        self.assertNotEqual(stripped, DESIGN28_TEXT, "the fingerprint row was not found")
        undocumented, unbacked = cv.defect4(OPDEFS_SRC, stripped)
        self.assertEqual(undocumented, ["fingerprint"])
        self.assertEqual(unbacked, [])

    def test_the_two_live_legitimate_absences_are_what_silences_them(self):
        """Not a tautology: it proves the SILENCE in the live row comes from the marker in
        the row and not from the comparator never looking. Strip the marker out of the real
        table and both rows must fire."""
        stripped = (DESIGN28_TEXT
                    .replace("[RETIRED 2026-07-25", "[withdrawn 2026-07-25")
                    .replace("(a feed, not a refusal)", "(no refusal here)"))
        undocumented, unbacked = cv.defect4(OPDEFS_SRC, stripped)
        self.assertEqual(undocumented, [])
        self.assertEqual(sorted(unbacked), ["attenuation", "due"])


class TestTheNearMissesFire(unittest.TestCase):
    """T-CHECKVOCAB-NEAR-MISS — §A64. A structural pattern that has never met a construct
    spelled ALMOST right has never been tested; the axis here is the status word itself,
    because the status word is the whole of what switches the comparator off."""

    def _fires(self, semantics, cite):
        doc = _doc_with(_ROW.format(name="planted_near_miss", semantics=semantics, cite=cite))
        return cv.defect4(_CLEAN_SRC, doc)[1]

    def test_a_nearly_right_retirement_word_fires(self):
        self.assertEqual(self._fires("[RETIRING 2026-01-01] being withdrawn", "—"),
                         ["planted_near_miss"])

    def test_a_lowercase_retirement_word_fires(self):
        self.assertEqual(self._fires("[retired 2026-01-01] withdrawn", "—"),
                         ["planted_near_miss"])

    def test_a_truncated_feed_status_fires(self):
        self.assertEqual(self._fires("a read-only feed", "— (a feed)"),
                         ["planted_near_miss"])

    def test_a_status_word_from_the_neighbouring_column_still_fires(self):
        """`GATED` and `GRANDFATHERED` are real status words in this table and neither one
        licenses an absence. A comparator that matched 'a bracketed capitalised word' would
        pass this and be wrong."""
        self.assertEqual(self._fires("[GRANDFATHERED: delivered long ago]", "[GATED]"),
                         ["planted_near_miss"])


class TestTheComparatorRefusesRatherThanDegrades(unittest.TestCase):
    """T-CHECKVOCAB-REFUSES — every one of these would otherwise yield a set that is merely
    SMALLER than the truth, and a smaller side produces a clean-looking zero."""

    def test_a_missing_declaration_refuses(self):
        with self.assertRaises(cv.CheckVocabError):
            cv.check_kinds_from_source("SOMETHING_ELSE = ('a',)\n")

    def test_two_declarations_refuse(self):
        with self.assertRaises(cv.CheckVocabError):
            cv.check_kinds_from_source('OP_CHECKS = ("a",)\nOP_CHECKS = ("b",)\n')

    def test_a_computed_declaration_refuses(self):
        with self.assertRaises(cv.CheckVocabError):
            cv.check_kinds_from_source('OP_CHECKS = tuple(sorted(("a", "b")))\n')

    def test_a_non_string_member_refuses(self):
        with self.assertRaises(cv.CheckVocabError):
            cv.check_kinds_from_source('OP_CHECKS = ("a", SOME_NAME)\n')

    def test_a_renumbered_section_refuses(self):
        with self.assertRaises(cv.CheckVocabError):
            cv.check_rows_from_doc(_CLEAN_DOC.replace(cv.SECTION_HEADING, "## 5b. elsewhere"))

    def test_a_malformed_row_refuses_rather_than_being_skipped(self):
        doc = _doc_with("| planted_two_cells | only two |\n")
        with self.assertRaises(cv.CheckVocabError):
            cv.check_rows_from_doc(doc)

    def test_a_row_whose_first_cell_is_not_a_check_name_refuses(self):
        doc = _doc_with(_ROW.format(name="**bold heading**", semantics="x", cite="y"))
        with self.assertRaises(cv.CheckVocabError):
            cv.check_rows_from_doc(doc)

    def test_a_duplicated_row_refuses(self):
        doc = _doc_with(_ROW.format(name="alpha", semantics="a second alpha", cite="y"))
        with self.assertRaises(cv.CheckVocabError):
            cv.check_rows_from_doc(doc)

    def test_the_reporter_says_UNINTERPRETABLE_rather_than_zero(self):
        """A structural refusal must never reach a reader as a count. It is the whole of
        why this comparator is allowed to report a zero at all."""
        missing = os.path.join(_ROOT, "does", "not", "exist.md")
        lines, healthy = cv.report(doc_path=missing)
        self.assertFalse(healthy)
        self.assertIn("UNINTERPRETABLE", lines[0])
        self.assertNotIn(": 0", lines[0])


def _definition_ref_default_cites(src_text):
    """The rules the engine falls back to at the `definition_ref` check site, read by AST.

    AST and not grep: the question is structural (which string literals sit on the right of
    the `or` inside THIS branch) and the same rule names appear all over this module in
    other branches and in prose. A grep would answer about the file's characters.

    THE BODY, NEVER THE NODE. Python builds an `elif` chain as nested `If`s hanging off
    each `orelse`, so `ast.walk` from the matched node descends into every LATER branch —
    `entry_ref`'s DICT-LAW, `sop`'s SOP, `space_tree`'s BOOT-INT. That is what the first
    version of this walker did, and the §A64 near-miss row below is what found it.
    """
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.Compare) and len(test.comparators) == 1):
            continue
        right = test.comparators[0]
        if not (isinstance(right, ast.Constant) and right.value == "definition_ref"):
            continue
        left = test.left
        if not (isinstance(left, ast.Subscript) and isinstance(left.value, ast.Name)
                and left.value.id == "c"):
            continue
        cites = []
        for stmt in node.body:
            for inner in ast.walk(stmt):
                if isinstance(inner, ast.BoolOp) and isinstance(inner.op, ast.Or):
                    for operand in inner.values:
                        if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                            cites.append(operand.value)
        return cites
    return None


class TestTheDefinitionRefRowIsTraced(unittest.TestCase):
    """T-DEFINITION-REF-TRACED — EP-28V W1. The row landed with its refusal rule UNTRACED;
    this pass traced it from the check site and completed the cell. These rows keep the
    completion honest: the engine cannot change its defaults without the table going red."""

    def _cite_cell(self):
        """The 'Refuses citing' cell — column 3 — and NOT the whole row.

        The subject matters and the first version of this got it wrong: the row's SEMANTICS
        cell keeps the dated history of what the cell used to say (the `AppendNothing`
        treatment — a completion does not erase the record that the completion happened),
        so an assertion over the whole row reads that history as the defect it describes."""
        for name, text in cv.check_rows_from_doc(DESIGN28_TEXT):
            if name == "definition_ref":
                cells = text.split("|")
                self.assertGreaterEqual(len(cells), 6)
                return cells[3].strip()
        self.fail("design/28 §5 carries no definition_ref row")

    def test_the_cite_cell_no_longer_says_untraced(self):
        self.assertNotIn("UNTRACED", self._cite_cell(),
                         "the cell was completed by EP-28V W1 on 2026-08-08")

    def test_the_row_names_the_two_rules_the_check_site_defaults_to(self):
        row = self._cite_cell()
        cites = _definition_ref_default_cites(OPDEFS_SRC)
        self.assertIsNotNone(cites, "the definition_ref branch is no longer findable")
        self.assertEqual(sorted(set(cites)), ["CAP-IS-LAW", "ROOT-NEG-1"],
                         "the engine's default citations at the definition_ref check site "
                         "moved; §5's row now states them and must move with them")
        for rule in ("ROOT-NEG-1", "CAP-IS-LAW"):
            self.assertIn(rule, row,
                          "%s is what the check site cites and the table does not say so" % rule)

    def test_the_near_miss_a_neighbouring_branchs_rules_are_not_picked_up(self):
        """§A64 for the AST walker: `entry_ref` sits immediately below and defaults to
        DICT-LAW. A walker that read the enclosing chain rather than this branch would
        return it, and the row above would then assert the wrong law was documented."""
        cites = _definition_ref_default_cites(OPDEFS_SRC)
        self.assertNotIn("DICT-LAW", cites,
                         "the walker reached out of the definition_ref branch")

    def test_the_walker_follows_a_planted_change_to_the_defaults(self):
        """The proof that the row above can go red: plant a different default and the
        walker reports it, so a real change in the engine reaches the assertion."""
        planted = OPDEFS_SRC.replace('c.get("cite") or "CAP-IS-LAW"',
                                     'c.get("cite") or "PLANTED-OTHER-RULE"', 1)
        self.assertNotEqual(planted, OPDEFS_SRC, "the planted substitution matched nothing")
        cites = _definition_ref_default_cites(planted)
        self.assertIn("PLANTED-OTHER-RULE", cites)
        self.assertNotIn("CAP-IS-LAW", cites)


if __name__ == "__main__":
    unittest.main()
