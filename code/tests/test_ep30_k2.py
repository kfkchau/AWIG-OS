"""EP-30-K2 — THE SEVENTEENTH CHECK KIND: `every_member`, asking a question of a whole set.

THE ONE SENTENCE THIS UNIT EXISTS FOR: the vocabulary had SIXTEEN WAYS TO ASK ABOUT A VALUE
AND NO WAY TO ASK ABOUT A SET. Every one of the sixteen reads its subject with a single
`params.get` into a single name, so a check declared over a many-valued parameter refused
every input including the ones that must pass.

AND THE SEVENTEENTH IS NOT A SEVENTEENTH QUESTION — IT IS A QUANTIFIER OVER THE OTHER
SIXTEEN. That is the owner's rebuildability rider deciding the design and not taste: a flat
special (`every_grantee_established`) bakes one inner question into the menu, so a re-cut of
the word list would REWRITE it; a quantifier adds an AXIS over the words and survives the
re-cut untouched, because it never names any of them.

EVERY VERIFICATION PROBE THIS UNIT RAN LANDS HERE AS A REGRESSION ROW (charter). The rows are
named for the plan's own acceptance and red-world ids so a reader can pair them with
`planning/evidence/EP-30-K2/`.

SELF-READING, and it is named at authoring per EP-SHAPE (`:1867`): several rows below read the
engine's SOURCE rather than only its behaviour. A claim that a function NAMES NO KIND is a
claim about what the code says, and calling the function cannot discharge it.

THIS UNIT WIRES NOTHING. `SHM-GRANT` and `COMMS-OPEN` are never touched here; every row drives
a SCRATCH definition created through the ordinary CREATE-OP door. Their wirings are
`EP-30-C4W`'s and the C6 law-schedule settlement's.
"""

import ast
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from kernel import opdefs                                          # noqa: E402
from kernel.blobs import BlobStore                                 # noqa: E402
from kernel.boot import build_kernel                               # noqa: E402
from kernel.errors import OpError                                  # noqa: E402

OPDEFS_PATH = opdefs.__file__
OPDEFS_SRC = open(OPDEFS_PATH, encoding="utf-8").read()
D28 = os.path.join(ROOT, "design/28-TARGET-STATE-HOST-KERNEL.md")
D40 = os.path.join(ROOT, "design/40-CHECK-VOCABULARY-DERIVED-FROM-CGL.md")

KIND = "every_member"
SCRATCH = "K2-SCRATCH"
MEMBERS, MEMBER = "members", "m"

#: The inner questions the rows below quantify. TWO DIFFERENT KINDS, deliberately — a
#: quantifier that works for exactly one inner kind is a special wearing a general's name.
INNER_DOMAIN = {"check": "value_domain", "param": MEMBER, "domain": ["alpha", "beta"],
                "cite": "CAP-IS-LAW",
                "message": "a member is not a value this law declares"}
INNER_PRIOR = {"check": "require_prior", "action": "CREATE-ACCOUNT", "field": "account_id",
               "param": MEMBER, "cite": "CAP-IS-LAW",
               "message": "a member names no established account"}


def every_member_row(inner, on_empty="admit", param=MEMBERS, member_param=MEMBER, **over):
    row = {"check": KIND, "param": param, "member_param": member_param,
           "on_empty": on_empty, "inner": inner, "cite": "CAP-IS-LAW"}
    row.update(over)
    for k, v in list(row.items()):
        if v is None:
            del row[k]
    return row


def scratch_definition(checks):
    """A definition carrying a MANY-VALUED PARAMETER, shaped exactly like the pack's two.

    `members` sits in `param_defaults` and not in `params`, which is `SHM-GRANT`'s `grantees`
    and `COMMS-OPEN`'s `endpoints` verbatim: an optional list the caller may supply, defaulting
    to `[]`. Copying the shipped shape matters — a scratch parameter declared some other way
    would prove the kind works on a subject the estate does not have."""
    return {"description": "a scratch definition with a many-valued parameter",
            "law_cited": "CAP-IS-LAW", "object_param": "subject",
            "params": {"subject": "required"},
            # `subject` is this op's object identifier ("s"/"s1") — a small inline scalar, not a
            # custody-conserved body: STRUCTURAL (vocabulary door, design/46 member 2). MEMBERS
            # sits in param_defaults, not params, so the door never reads it (mirrors SHM-GRANT's
            # `grantees` / COMMS-OPEN's `endpoints`) and it needs no classification here.
            "structural_params": ["subject"],
            "param_defaults": {MEMBERS: []},
            "payload_from": ["subject", MEMBERS],
            "checks": checks}


# ---- source-reading instruments (A5, A6, R3) -----------------------------------------------

#: A DEPENDENCY ON THE VOCABULARY'S ORDER rather than on its NAMES. Indexing the tuple, or
#: asking it for a position, ties this unit to WHERE a word sits — so a re-cut that reorders
#: the list would change this unit's behaviour silently. Referencing BY NAME survives a re-cut.
POSITIONAL = re.compile(r"OP_CHECKS\s*\[\s*[-+]?\d+\s*\]"
                        r"|OP_CHECKS\.index\s*\("
                        r"|list\s*\(\s*OP_CHECKS\s*\)\s*\[")


def positional_dependencies(src):
    """Every ORDER-dependent use of the vocabulary, named with its line and its text.

    COMMENT LINES ARE SKIPPED AND THAT IS A STATED CHOICE, not an oversight: prose mentioning
    an index creates no dependency, and a scanner that fired on prose would be a check nobody
    could keep green. The negative control below proves the skip discriminates."""
    out = []
    for i, line in enumerate(src.split("\n"), 1):
        if line.lstrip().startswith("#"):
            continue
        m = POSITIONAL.search(line)
        if m:
            out.append((i, m.group(0), line.strip()))
    return out


def executable_source(src, name):
    """A function's EXECUTABLE source — docstring and comments removed, via unparse.

    A6's question is whether the QUANTIFIER'S CODE names another kind. A docstring naming one
    creates no dependency on it, so the honest subject is what executes. The prose is reported
    separately by its own row rather than hidden."""
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == name)
    body = fn.body
    if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return "\n".join(ast.unparse(n) for n in body)


class WorldCase(unittest.TestCase):
    """A real kernel over a temp record. THE REPO PACK IS NEVER WRITTEN and never amended:
    every definition below enters through CREATE-OP, the ordinary runtime door, which is what
    makes the definition-time rows real refusals rather than direct calls to a guard."""

    def setUp(self):
        d = tempfile.mkdtemp()
        import shutil
        self.addCleanup(shutil.rmtree, d, True)
        self.store, self.gate, self.views = build_kernel(
            os.path.join(d, "record.jsonl"), blobs=BlobStore(os.path.join(d, "blobs")))

    def accounts(self, *ids):
        for a in ids:
            self.gate.execute("CREATE-ACCOUNT", "owner",
                              {"account_id": a, "actor_class": "program"})

    def create(self, checks, name=SCRATCH):
        self.gate.execute("CREATE-OP", "owner",
                          {"name": name, "definition": scratch_definition(checks)})
        landed = self.views.op_definitions()[name]["definition"]
        self.assertEqual([dict(c).get("check") for c in (landed.get("checks") or [])],
                         [c["check"] for c in checks],
                         "the definition did not reach the REGISTRY, so every row built on it "
                         "would be testing a shape nobody registered")
        return name

    def drive(self, members, name=SCRATCH, subject="s1"):
        return self.gate.execute(name, "owner", {"subject": subject, "members": members})

    def refusal_of(self, fn, *a, **kw):
        """Drive an act expected to refuse; return (rule, message).

        AND IT ASSERTS EXACTLY ONE REFUSAL RECORD, which for this kind is a load-bearing clause
        and not boilerplate: a quantifier whose inner question refused through the REAL gate
        would record ONE REFUSAL PER FAILING MEMBER, so a set with three bad members would leave
        three records for a single act. This helper is what makes that visible."""
        before = len(self.store.by_action("op-refused"))
        try:
            fn(*a, **kw)
        except OpError as exc:
            after = len(self.store.by_action("op-refused"))
            self.assertEqual(after, before + 1,
                             "the act recorded %d refusals where a governed refusal is ONE "
                             "recorded rule-citing decision" % (after - before))
            return self.store.by_action("op-refused")[-1].get("rule_cited"), str(exc)
        raise AssertionError("the act was ADMITTED where the law requires a refusal")


# ================================================================================ A2
class A2TheKindExistsAndDispatchesCase(WorldCase):
    """A2 — the kind exists, dispatches, an unknown kind is still refused, and a declaration
    missing its empty-set answer refuses at DEFINITION time."""

    def test_a2_the_vocabulary_holds_seventeen_names_including_this_one(self):
        self.assertEqual(len(opdefs.OP_CHECKS), 19,
                         "the vocabulary is %d names: %r" % (len(opdefs.OP_CHECKS),
                                                             opdefs.OP_CHECKS))
        self.assertIn(KIND, opdefs.OP_CHECKS)

    def test_a2_the_new_arm_is_reached_and_not_merely_declared(self):
        """A DECLARED KIND WITH NO DISPATCH SITE IS A CHECK THAT CANNOT RUN. Reached is proven
        by the arm CHANGING AN OUTCOME — the same declaration refuses one set and admits
        another — never by the absence of an exception."""
        self.create([every_member_row(INNER_DOMAIN)])
        self.drive(["alpha", "beta"])
        rule, msg = self.refusal_of(self.drive, ["alpha", "gamma"])
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("gamma", msg)

    def test_a2_an_unknown_check_kind_is_still_refused_with_the_full_vocabulary(self):
        rule, msg = self.refusal_of(
            self.gate.execute, "CREATE-OP", "owner",
            {"name": "K2-UNKNOWN",
             "definition": scratch_definition([{"check": "every_grantee_established",
                                                "cite": "CAP-IS-LAW"}])})
        self.assertEqual(rule, "AR-2")
        self.assertIn("every_grantee_established", msg)
        for name in opdefs.OP_CHECKS:
            self.assertIn(name, msg, "the refusal does not list %r" % name)

    def test_a2_a_declaration_omitting_its_empty_set_answer_refuses_at_definition_time(self):
        """THE COUNTERSIGNER'S RULING (`:2041`), AND THE ROW THAT MAKES R4's REQUIREMENT A
        CONTROL RATHER THAN A SENTENCE. A *must* with no refusal behind it is the written-rule
        rung of this estate's enforcement ladder, and a rule a seat can breach by accident is
        not a control."""
        row = every_member_row(INNER_DOMAIN)
        del row["on_empty"]
        rule, msg = self.refusal_of(
            self.gate.execute, "CREATE-OP", "owner",
            {"name": "K2-NO-EMPTY-ANSWER", "definition": scratch_definition([row])})
        self.assertEqual(rule, "AR-2")
        self.assertIn("on_empty", msg)
        self.assertIn("vacuous", msg)
        self.assertNotIn(SCRATCH, [n for n in self.views.op_definitions()])

    def test_a2_the_refusal_is_at_DEFINITION_time_and_never_reaches_an_act(self):
        """The distinction the plan draws in `:2041`'s own words: refused at definition time,
        NEVER REACHING AN ACT, never answering vacuously. Proven by the op not existing."""
        row = every_member_row(INNER_DOMAIN)
        del row["on_empty"]
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-OP", "owner",
                              {"name": "K2-NEVER", "definition": scratch_definition([row])})
        self.assertFalse(self.gate.has("K2-NEVER"))
        with self.assertRaises(OpError):
            self.gate.execute("K2-NEVER", "owner", {"subject": "s", "members": []})


# ================================================================================ A3 / A4
class A3AndA4TheTwoDirectionsCase(WorldCase):
    """A3 and A4 are ONE ROW IN TWO DIRECTIONS and neither alone is evidence — the cardinality
    gap this unit closes was itself a check that refused everything (`:1989`)."""

    def test_a3_one_bad_member_refuses_and_the_refusal_NAMES_THE_MEMBER(self):
        """A REFUSAL THAT SAYS ONLY *SOMETHING IN THIS SET IS WRONG* IS THE m3-up DEFECT
        (`:2021`) — two different worlds answered with one string. The member is part of the
        VERDICT, not part of the debugging."""
        self.create([every_member_row(INNER_DOMAIN)])
        rule, msg = self.refusal_of(self.drive, ["alpha", "delta", "beta"])
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("delta", msg, "the refusal does not name the failing member: %s" % msg)
        self.assertIn(MEMBERS, msg, "the refusal does not name the parameter: %s" % msg)

    def test_a3_two_different_bad_members_give_two_different_refusals(self):
        """THE DISCRIMINATION, not merely the presence of a name. A message that named the
        member by luck of a shared substring would pass the row above and fail this one."""
        self.create([every_member_row(INNER_DOMAIN)])
        _, first = self.refusal_of(self.drive, ["delta"])
        _, second = self.refusal_of(self.drive, ["omega"])
        self.assertNotEqual(first, second)
        self.assertIn("delta", first)
        self.assertNotIn("omega", first)
        self.assertIn("omega", second)

    def test_a4_a_set_whose_members_all_pass_is_ADMITTED_and_appended(self):
        self.create([every_member_row(INNER_DOMAIN)])
        before = len(self.store.by_action(SCRATCH))
        self.drive(["alpha", "beta", "alpha"])
        self.assertEqual(len(self.store.by_action(SCRATCH)), before + 1)
        rec = self.store.by_action(SCRATCH)[-1]
        self.assertEqual(rec["rule_cited"], "CAP-IS-LAW")
        # AND THE RECORDED SET ARRIVES BACK AS A TUPLE, not as the list that was supplied: a
        # record in this estate is FROZEN ALL THE WAY DOWN. Stated here because it is the fact
        # that makes the tuple row further down necessary rather than defensive — a re-validated
        # declaration meets its own guard in the frozen spelling.
        self.assertEqual(list((rec.get("payload") or {}).get(MEMBERS)),
                         ["alpha", "beta", "alpha"])

    def test_a3_the_refusal_of_a_many_bad_set_is_ONE_RECORD_not_one_per_member(self):
        """THE PROBE THAT BECAME A ROW. The evaluator asks the inner question through a
        NON-RECORDING gate double and records ONE authoritative refusal itself. Without that,
        three bad members would leave three refusal records for a single act — a record holding
        acts nobody performed."""
        self.create([every_member_row(INNER_DOMAIN)])
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError):
            self.drive(["bad1", "bad2", "bad3"])
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)

    def test_a3_the_first_failing_member_is_the_one_named(self):
        """STATED SO IT CANNOT DRIFT: the verdict names the FIRST member that fails, in the
        order the caller supplied. Declared here rather than discovered by a later reader."""
        self.create([every_member_row(INNER_DOMAIN)])
        _, msg = self.refusal_of(self.drive, ["bad1", "bad2"])
        self.assertIn("bad1", msg)
        self.assertNotIn("bad2", msg)


# ================================================================================ A5
class A5ComposesWithMoreThanOneInnerKindCase(WorldCase):
    """A5 — THE RIDER'S ACCEPTANCE ROW AS MUCH AS THE KIND'S. A quantifier that works for
    exactly one inner kind is a special wearing a general's name."""

    def test_a5_inner_kind_one_value_domain_dispatches_and_refuses_its_own_way(self):
        self.create([every_member_row(INNER_DOMAIN)])
        rule, msg = self.refusal_of(self.drive, ["nope"])
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("nope", msg)
        self.drive(["alpha"])

    def test_a5_inner_kind_two_require_prior_dispatches_and_refuses_its_own_way(self):
        """A DIFFERENT KIND ENTIRELY: `value_domain` reads a declared constant list;
        `require_prior` walks the RECORD. Same quantifier, same declaration shape."""
        self.accounts("ent:a", "ent:b")
        self.create([every_member_row(INNER_PRIOR)])
        self.drive(["ent:a", "ent:b"])
        rule, msg = self.refusal_of(self.drive, ["ent:a", "ent:ghost"])
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("ent:ghost", msg)

    def test_a5_the_two_inner_kinds_are_genuinely_different_arms(self):
        """THE CONTROL FOR THE ROW ABOVE. Two inner kinds that happened to be the same word
        would make 'composes with more than one' a sentence about nothing."""
        self.assertNotEqual(INNER_DOMAIN["check"], INNER_PRIOR["check"])
        self.assertIn(INNER_DOMAIN["check"], opdefs.OP_CHECKS)
        self.assertIn(INNER_PRIOR["check"], opdefs.OP_CHECKS)

    def test_a5_the_quantifiers_own_code_names_NEITHER_kind_and_none_of_the_other_fifteen(self):
        """THE STRUCTURAL HALF, and it is what makes A5 a universal rather than two samples.
        The evaluator takes the engine's ONE dispatch site as a callable; it knows no words."""
        code = executable_source(OPDEFS_SRC, "_every_member_check")
        named = [k for k in opdefs.OP_CHECKS if k != KIND and k in code]
        self.assertEqual(named, [],
                         "the quantifier's executable code names %r — a re-cut of the word "
                         "list would have to rewrite it" % (named,))

    def test_this_units_functions_sit_OUTSIDE_the_neighbouring_arms_source_slices(self):
        """THE PROBE THAT BECAME A ROW, AND IT COST A RED TO FIND.

        `tests/test_ep30_k1.py` reads two SOURCE SLICES of `opdefs.py` BY FUNCTION NAME —
        `_prior_value_check`→`_bound_field_check` and `_bound_field_check`→`_interpreter` — to
        assert an author's `message` override reaches ONE refusal and not three. This unit's
        evaluator was first written between `_bound_field_check` and `_interpreter` and **redded
        that row, `3 != 1`, over code it never touched**.

        A SLICE ANCHORED ON TWO NAMES SILENTLY ADOPTS WHATEVER IS WRITTEN BETWEEN THEM. That is
        a real property of the instrument and the next author will meet it too, so the
        constraint is MECHANICAL here rather than a comment somebody deletes."""
        for first, second in (("def _prior_value_check", "def _bound_field_check"),
                              ("def _bound_field_check", "def _interpreter")):
            seg = OPDEFS_SRC[OPDEFS_SRC.index(first):OPDEFS_SRC.index(second)]
            self.assertEqual(seg.count('c.get("message")'), 1,
                             "%s -> %s carries %d message overrides; a function of this unit "
                             "has been moved inside a neighbour's arm"
                             % (first, second, seg.count('c.get("message")')))
            self.assertNotIn("def _every_member_check", seg)
            self.assertNotIn("class _ProbeGate", seg)

    def test_the_slice_row_above_can_fail_which_is_what_makes_its_zero_mean_something(self):
        """THE CONTROL. Plant this unit's evaluator inside the slice in a COPY of the source and
        the row must red — otherwise it is a check that cannot fail, guarding the exact class of
        defect it was written after."""
        planted = OPDEFS_SRC.replace(
            "def _bound_field_check",
            "def _every_member_check_PLANTED(c):\n    return c.get(\"message\")\n\n\n"
            "def _bound_field_check", 1)
        seg = planted[planted.index("def _prior_value_check"):
                      planted.index("def _bound_field_check")]
        self.assertEqual(seg.count('c.get("message")'), 2,
                         "the plant did not land inside the slice, so this control proves "
                         "nothing about the row above")

    def test_a5_the_control_the_dispatch_site_DOES_name_them_so_the_row_above_can_fail(self):
        """A CHECK THAT CANNOT FAIL PROVES NOTHING. The engine's dispatch chain names every
        kind by construction; if the search above could not find a name anywhere, its empty
        answer would mean nothing."""
        self.assertIn('c["check"] == "every_member"', OPDEFS_SRC)
        chain = OPDEFS_SRC[OPDEFS_SRC.index("def _dispatch_check"):]
        chain = chain[:chain.index("for c in d.get(\"checks\", []):")]
        for k in opdefs.OP_CHECKS:
            self.assertIn('"%s"' % k, chain,
                          "the dispatch chain does not name %r, so the search is not a "
                          "discriminating one" % k)


# ================================================================================ A6
class A6TheRebuildabilityRiderCase(WorldCase):
    """A6 — THE OWNER'S CONDITION, DRIVEN. `design/28` §5, 2026-08-22: 'go for now, but also on
    the condition that these 17 is something we can rebuild later cause I'm keen to rethink
    that.' Three checks, and (c) is EXHIBITED rather than promised."""

    def test_a6a_design40_carries_this_kinds_derivation_row(self):
        """(a) — THE ARCHITECT'S ACT, CHECKED AND NEVER WRITTEN HERE. `design/40` is
        MUST-NOT-TOUCH for this unit (plan §6) and its derivation row is the architect's
        (plan §5). This row CHECKS EXISTENCE. If it reds, the row is owed, not broken."""
        self.assertIn(KIND, open(D40, encoding="utf-8").read(),
                      "design/40 carries no derivation row for %r — the architect's act, owed "
                      "by plan §5, which this row checks and may not write" % KIND)

    def test_a6a_design28_section5_carries_this_kinds_table_row(self):
        """The second architect act plan §5 names. Same standing: checked, never written."""
        self.assertIn(KIND, open(D28, encoding="utf-8").read(),
                      "design/28 §5's table carries no row for %r — the architect's act, owed "
                      "by plan §5, which this row checks and may not write" % KIND)

    def test_a6b_the_kind_is_referenced_BY_NAME_with_no_dependency_on_the_lists_ORDER(self):
        """(b) — no positional or index-based dependency on the vocabulary's ORDER."""
        found = positional_dependencies(OPDEFS_SRC)
        self.assertEqual(found, [],
                         "the engine depends on the vocabulary's ORDER at: %s"
                         % "; ".join("%s:%d %s" % (os.path.basename(OPDEFS_PATH), i, t)
                                     for i, _, t in found))

    def test_a6b_the_scanner_ignores_prose_which_is_why_its_empty_answer_means_something(self):
        """THE NEGATIVE CONTROL for the skip: a mention inside a comment is not a dependency
        and must not fire. Without this, the row above could be green because the filter is
        broken rather than because the code is clean."""
        self.assertEqual(positional_dependencies("# OP_CHECKS[3] discussed in prose\n"), [])
        self.assertEqual(len(positional_dependencies("x = OP_CHECKS[3]\n")), 1)

    def test_a6c_a_re_cut_of_the_word_list_touches_the_law_and_not_this_units_evaluator(self):
        """(c) — EXHIBITED. Rename every word in the vocabulary in a COPY of the source and
        show WHAT MOVED: the tuple, the dispatch arms and the per-kind leashes move, because
        they ARE the law's spelling; the quantifier's evaluator does not move at all.

        THAT IS THE WHOLE OF THE RIDER: a re-derivation is an ordinary (if large) law pass and
        never a rewrite of this unit."""
        recut = OPDEFS_SRC
        for k in opdefs.OP_CHECKS:
            if k != KIND:
                recut = recut.replace('"%s"' % k, '"recut_%s"' % k)
        self.assertNotEqual(recut, OPDEFS_SRC, "the re-cut substitution matched nothing")
        before = executable_source(OPDEFS_SRC, "_every_member_check")
        after = executable_source(recut, "_every_member_check")
        self.assertEqual(before, after,
                         "a re-cut of the word list CHANGED the quantifier's evaluator, which "
                         "is the dependency the owner's rider forbids")
        moved = executable_source(OPDEFS_SRC, "_dispatch_check")
        self.assertNotEqual(moved, executable_source(recut, "_dispatch_check"),
                            "the re-cut moved nothing at the dispatch site either, so this "
                            "row is not exhibiting a re-cut at all")

    def test_a6c_the_declaration_references_its_inner_kind_BY_NAME_and_stays_migratable(self):
        """The rider's 'referenced BY NAME everywhere' applied to the LAW-DATA, not the code:
        a declaration names its inner question with a word, so a re-cut re-spells the
        declaration through the ordinary founding door and nothing else has to move."""
        self.create([every_member_row(INNER_DOMAIN)])
        landed = self.views.op_definitions()[SCRATCH]["definition"]["checks"][0]
        self.assertEqual(dict(dict(landed)["inner"])["check"], "value_domain")
        self.assertIsInstance(dict(dict(landed)["inner"])["check"], str)


# ================================================================================ R1
class R1NoExistingKindExpressesItCase(WorldCase):
    """R1 — THE MINT'S JUSTIFICATION AS A DRIVEN DIFFERENTIAL RATHER THAN AN ARGUMENT.
    If this row cannot separate the two spellings, the kind is not minimal and §8.2 makes the
    mint a STOP."""

    def test_r1_the_closest_existing_spelling_REFUSES_a_set_whose_members_all_pass(self):
        """`require_prior` over the SAME many-valued parameter. Its `want` is the WHOLE LIST,
        and no record's field equals a list, so it refuses the good set."""
        self.accounts("ent:a", "ent:b")
        self.create([{"check": "require_prior", "action": "CREATE-ACCOUNT",
                      "field": "account_id", "param": MEMBERS, "cite": "CAP-IS-LAW",
                      "message": "the closest existing spelling"}], name="K2-OLD-SPELLING")
        self.refusal_of(self.drive, ["ent:a", "ent:b"], name="K2-OLD-SPELLING")

    def test_r1_the_new_kind_ADMITS_the_same_set_in_the_same_world(self):
        """THE OTHER DIRECTION, in a world built the same way. Two rows, opposite verdicts,
        one input — which is what separation means."""
        self.accounts("ent:a", "ent:b")
        self.create([every_member_row(INNER_PRIOR)], name="K2-NEW-SPELLING")
        before = len(self.store.by_action("K2-NEW-SPELLING"))
        self.drive(["ent:a", "ent:b"], name="K2-NEW-SPELLING")
        self.assertEqual(len(self.store.by_action("K2-NEW-SPELLING")), before + 1)

    def test_r1_both_spellings_side_by_side_in_ONE_world_separate(self):
        """THE ROW THAT ACTUALLY DISCHARGES §8.2. Two worlds could differ for a reason nobody
        named; one world with both definitions and one input cannot."""
        self.accounts("ent:a", "ent:b")
        self.create([{"check": "require_prior", "action": "CREATE-ACCOUNT",
                      "field": "account_id", "param": MEMBERS, "cite": "CAP-IS-LAW"}],
                    name="K2-OLD-SPELLING")
        self.create([every_member_row(INNER_PRIOR)], name="K2-NEW-SPELLING")
        good = ["ent:a", "ent:b"]
        self.refusal_of(self.drive, good, name="K2-OLD-SPELLING")
        self.drive(good, name="K2-NEW-SPELLING")

    def test_r1_and_the_old_spelling_is_not_merely_broken_it_admits_a_single_value(self):
        """THE CONTROL. `require_prior` refusing the list is not a dead check — hand it the
        single value it was built for and it admits. The separation is about CARDINALITY."""
        self.accounts("ent:a")
        self.create([{"check": "require_prior", "action": "CREATE-ACCOUNT",
                      "field": "account_id", "param": MEMBERS, "cite": "CAP-IS-LAW"}],
                    name="K2-OLD-SPELLING")
        self.drive("ent:a", name="K2-OLD-SPELLING")


# ================================================================================ R2
class R2TheCheckCanFailAndCanPassCase(WorldCase):
    """R2 — remove the check and A3's refusal becomes an acceptance; restore it and the
    refusal returns. A check never shown changing an outcome is a check that cannot fail."""

    def test_r2_with_the_check_REMOVED_a3s_input_is_ADMITTED(self):
        self.create([], name="K2-NO-CHECK")
        before = len(self.store.by_action("K2-NO-CHECK"))
        self.drive(["alpha", "delta", "beta"], name="K2-NO-CHECK")
        self.assertEqual(len(self.store.by_action("K2-NO-CHECK")), before + 1)

    def test_r2_with_the_check_RESTORED_the_refusal_returns(self):
        self.create([every_member_row(INNER_DOMAIN)], name="K2-WITH-CHECK")
        rule, msg = self.refusal_of(self.drive, ["alpha", "delta", "beta"],
                                    name="K2-WITH-CHECK")
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("delta", msg)

    def test_r2_both_directions_in_ONE_world_so_the_move_is_the_checks_and_nothing_elses(self):
        self.create([], name="K2-NO-CHECK")
        self.create([every_member_row(INNER_DOMAIN)], name="K2-WITH-CHECK")
        bad = ["alpha", "delta"]
        self.drive(bad, name="K2-NO-CHECK")
        self.refusal_of(self.drive, bad, name="K2-WITH-CHECK")


# ================================================================================ R3
class R3TheRiderCanFailCase(WorldCase):
    """R3 — A RIDER CHECK NEVER SHOWN REFUSING ANYTHING would be this arc's signature defect
    authored into the unit that carries the owner's condition."""

    def test_r3_a_planted_ORDER_dependency_reds_a6b_and_NAMES_the_planted_line(self):
        planted = OPDEFS_SRC.replace(
            'if c.get("check") != EVERY_MEMBER:',
            'if c.get("check") != OP_CHECKS[16]:', 1)
        self.assertNotEqual(planted, OPDEFS_SRC, "the plant matched nothing")
        found = positional_dependencies(planted)
        self.assertEqual(len(found), 1, "the plant was not found: %r" % (found,))
        self.assertEqual(found[0][1], "OP_CHECKS[16]")
        self.assertIn("OP_CHECKS[16]", found[0][2])

    def test_r3_with_the_plant_REMOVED_a6b_greens_again(self):
        self.assertEqual(positional_dependencies(OPDEFS_SRC), [])

    def test_r3_the_index_form_and_the_position_form_are_both_caught(self):
        """A rider check that caught ONE spelling of the dependency would be a check with a
        hole in exactly the shape of the next author's habit."""
        self.assertEqual(len(positional_dependencies("k = OP_CHECKS.index('kind')\n")), 1)
        self.assertEqual(len(positional_dependencies("k = list(OP_CHECKS)[0]\n")), 1)
        self.assertEqual(len(positional_dependencies("k = OP_CHECKS[-1]\n")), 1)

    def test_r3_a_name_reference_does_NOT_fire_which_is_the_behaviour_being_protected(self):
        """The rider permits BY-NAME references and forbids only ORDER. A scanner firing on
        both would forbid the thing the rider requires."""
        self.assertEqual(positional_dependencies('if c.get("check") != EVERY_MEMBER:\n'), [])
        self.assertEqual(positional_dependencies('if x in OP_CHECKS:\n'), [])


# ================================================================================ R4
class R4TheBoundariesCase(WorldCase):
    """R4 — THE BOUNDARIES, AND THEY ARE WHERE A QUANTIFIER LIES.

    THE PLAN'S DECLARED ANSWERS, stated here rather than discovered at the close:
      EMPTY SET   answered by the DECLARATION's `on_empty`, which is MANDATORY. There is no
                  engine default in either direction and no branch that could be called one.
      ONE MEMBER  no special case at all — one member is a set of one, asked once.
    """

    def test_r4_an_empty_set_under_on_empty_admit_is_ADMITTED(self):
        self.create([every_member_row(INNER_DOMAIN, on_empty="admit")], name="K2-EMPTY-OK")
        before = len(self.store.by_action("K2-EMPTY-OK"))
        self.drive([], name="K2-EMPTY-OK")
        self.assertEqual(len(self.store.by_action("K2-EMPTY-OK")), before + 1)

    def test_r4_an_empty_set_under_on_empty_refuse_is_REFUSED(self):
        self.create([every_member_row(INNER_DOMAIN, on_empty="refuse")], name="K2-EMPTY-NO")
        rule, msg = self.refusal_of(self.drive, [], name="K2-EMPTY-NO")
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn(MEMBERS, msg)

    def test_r4_the_two_empty_answers_are_the_LAWS_and_not_the_engines(self):
        """THE DIFFERENTIAL THAT MATTERS MOST IN THIS FILE. One input, one engine, two
        declarations, OPPOSITE verdicts — so the answer demonstrably comes from the law-data
        and not from a default this engine supplied."""
        self.create([every_member_row(INNER_DOMAIN, on_empty="admit")], name="K2-EMPTY-OK")
        self.create([every_member_row(INNER_DOMAIN, on_empty="refuse")], name="K2-EMPTY-NO")
        self.drive([], name="K2-EMPTY-OK")
        self.refusal_of(self.drive, [], name="K2-EMPTY-NO")

    def test_r4_the_omitted_parameter_takes_the_declared_default_and_is_still_the_empty_case(self):
        """THE VACUOUS-PASS TRAP AT ITS REAL ENTRY POINT. Both pack parameters default to `[]`,
        so the empty set arrives most often by a caller SAYING NOTHING. Under `admit` that is
        lawful; under `refuse` it refuses — and neither is this engine's opinion."""
        self.create([every_member_row(INNER_DOMAIN, on_empty="refuse")], name="K2-EMPTY-NO")
        self.refusal_of(self.gate.execute, "K2-EMPTY-NO", "owner", {"subject": "s"})

    def test_r4_a_single_member_set_that_passes_is_ADMITTED(self):
        self.create([every_member_row(INNER_DOMAIN)], name="K2-ONE")
        before = len(self.store.by_action("K2-ONE"))
        self.drive(["alpha"], name="K2-ONE")
        self.assertEqual(len(self.store.by_action("K2-ONE")), before + 1)

    def test_r4_a_single_member_set_that_fails_is_REFUSED_and_names_that_member(self):
        self.create([every_member_row(INNER_DOMAIN)], name="K2-ONE")
        rule, msg = self.refusal_of(self.drive, ["solo"], name="K2-ONE")
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("solo", msg)

    def test_r4_the_declaration_requirement_is_DIFFERENTIAL_omission_refuses(self):
        """`:2041`'s own words: plant a declaration with its empty-set answer OMITTED and it is
        REFUSED AT DEFINITION TIME, citing the malformed-declaration door."""
        row = every_member_row(INNER_DOMAIN)
        del row["on_empty"]
        rule, _ = self.refusal_of(
            self.gate.execute, "CREATE-OP", "owner",
            {"name": "K2-OMITTED", "definition": scratch_definition([row])})
        self.assertEqual(rule, "AR-2")
        self.assertFalse(self.gate.has("K2-OMITTED"))

    def test_r4_remove_the_plant_and_the_declaration_REGISTERS(self):
        """THE OTHER DIRECTION. A requirement that refuses everything is not a requirement."""
        self.create([every_member_row(INNER_DOMAIN, on_empty="admit")], name="K2-RESTORED")
        self.assertTrue(self.gate.has("K2-RESTORED"))

    def test_r4_a_MISSPELT_empty_answer_is_refused_and_never_falls_back(self):
        """A wrong word is not silence and never resolves to it — WHEN_UNBOUND's rule applied
        to this key. A misspelt `admitt` falling back to either answer would make an author's
        intent vanish with nothing going red."""
        rule, msg = self.refusal_of(
            self.gate.execute, "CREATE-OP", "owner",
            {"name": "K2-MISSPELT",
             "definition": scratch_definition([every_member_row(INNER_DOMAIN,
                                                                on_empty="admitt")])})
        self.assertEqual(rule, "AR-2")
        self.assertIn("admitt", msg)


# ================================================================================ the leash
class TheDeclarationLeashCase(WorldCase):
    """PROBES THAT BECAME ROWS. Every malformed declaration this unit's guard refuses, driven
    through the ordinary door — because a guard nobody has seen refuse is a guard nobody has
    tested."""

    def bad(self, row, name):
        return self.refusal_of(self.gate.execute, "CREATE-OP", "owner",
                               {"name": name, "definition": scratch_definition([row])})

    def test_a_row_naming_no_param_refuses(self):
        row = every_member_row(INNER_DOMAIN)
        del row["param"]
        self.assertEqual(self.bad(row, "K2-NO-PARAM")[0], "AR-2")

    def test_a_row_naming_a_param_the_op_does_not_take_refuses(self):
        rule, msg = self.bad(every_member_row(INNER_DOMAIN, param="nosuch"), "K2-UNKNOWN-PARAM")
        self.assertEqual(rule, "AR-2")
        self.assertIn("nosuch", msg)

    def test_a_row_naming_no_member_param_refuses(self):
        row = every_member_row(INNER_DOMAIN)
        del row["member_param"]
        self.assertEqual(self.bad(row, "K2-NO-MEMBER")[0], "AR-2")

    def test_a_member_name_SHADOWING_a_real_parameter_refuses(self):
        """The footgun this clause exists for: the quantifier would OVERWRITE a value the
        caller supplied and the inner question would measure the wrong thing on every act."""
        rule, msg = self.bad(every_member_row(INNER_DOMAIN, member_param="subject"),
                             "K2-SHADOW")
        self.assertEqual(rule, "AR-2")
        self.assertIn("subject", msg)

    def test_a_row_carrying_no_inner_question_refuses(self):
        row = every_member_row(INNER_DOMAIN)
        del row["inner"]
        self.assertEqual(self.bad(row, "K2-NO-INNER")[0], "AR-2")

    def test_an_inner_naming_an_unknown_kind_refuses_with_the_full_vocabulary(self):
        rule, msg = self.bad(every_member_row({"check": "no_such_kind", "param": MEMBER}),
                             "K2-INNER-UNKNOWN")
        self.assertEqual(rule, "AR-2")
        for name in opdefs.OP_CHECKS:
            self.assertIn(name, msg)

    def test_a_quantifier_over_a_quantifier_refuses(self):
        """No nesting: a quantifier over a quantifier needs a parameter whose members are
        themselves many-valued and no operation declares one. REFUSED with its reason rather
        than left undefined — and lifting it is one line the day such a parameter exists."""
        rule, msg = self.bad(every_member_row(every_member_row(INNER_DOMAIN)), "K2-NESTED")
        self.assertEqual(rule, "AR-2")
        self.assertIn("quantify another", msg)

    def test_the_INNER_row_meets_its_own_kinds_leash_and_not_only_the_quantifiers(self):
        """THE GAP THIS UNIT HAD TO CLOSE AND THE REASON THE LEASHES MOVED TO ONE HOME. The
        per-kind guards read `d["checks"]` at top level, so an inner row would have escaped its
        own malformed-declaration door entirely. An inner `value_domain` with an EMPTY domain
        is exactly the row `_require_wellformed_value_domain` exists to refuse."""
        rule, msg = self.bad(every_member_row({"check": "value_domain", "param": MEMBER,
                                               "domain": [], "cite": "CAP-IS-LAW"}),
                             "K2-INNER-EMPTY-DOMAIN")
        self.assertEqual(rule, "AR-2")
        self.assertIn("domain", msg)

    def test_an_inner_bound_field_naming_no_action_is_refused_through_the_same_home(self):
        """A SECOND INNER KIND through the same door, so the row above is not one lucky case."""
        rule, _ = self.bad(every_member_row({"check": "bound_field", "param": MEMBER,
                                             "cite": "CAP-IS-LAW"}),
                           "K2-INNER-BAD-BOUND-FIELD")
        self.assertEqual(rule, "AR-2")

    def test_an_inner_row_citing_nothing_is_refused(self):
        """AND IT CITES ROOT-NEG-5, NOT AR-2 — the empty-cite leash's own rule, reached through
        the quantifier's guard. DRIVEN, and it corrected this row: the row first asserted AR-2
        by analogy with its neighbours and the engine was right. A check whose `cite` is present
        but empty drove a refusal that recorded no cite and crashed before appending, which is
        why that leash exists and why it keeps its own rule here."""
        rule, _ = self.bad(every_member_row(dict(INNER_DOMAIN, cite=None)), "K2-INNER-NO-CITE")
        self.assertEqual(rule, "ROOT-NEG-5")

    def test_a_WELL_FORMED_row_registers_which_is_what_makes_the_leash_a_discriminator(self):
        self.create([every_member_row(INNER_DOMAIN)], name="K2-GOOD")
        self.assertTrue(self.gate.has("K2-GOOD"))


# ================================================================================ the subject
class TheSubjectMustBeASetCase(WorldCase):
    """DECIDED BY THIS BUILDER AND STATED, because neither plan nor brief settled it: what a
    quantifier does when its subject is not a set."""

    def test_a_string_is_NOT_a_set_of_its_characters(self):
        """A string is iterable and its members are letters. Admitting one would ask the inner
        question of every character of a name — an answer computed over a subject nobody
        declared, and it would silently PASS or FAIL for reasons no author wrote."""
        self.create([every_member_row(INNER_DOMAIN)], name="K2-STR")
        rule, msg = self.refusal_of(self.drive, "alpha", name="K2-STR")
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("not a set", msg)

    def test_an_absent_parameter_with_no_default_refuses_rather_than_passing_vacuously(self):
        """`value_domain`'s absent-is-not-in-the-domain, one layer out: None is not a set of
        anything, so it refuses instead of being read as an empty set — which would hand the
        vacuous pass back through a second door after `on_empty` closed the first.

        THE DEFAULT IS DECLARED AS `null` AND THAT IS THE POINT OF THE ROW: a law may declare
        that its many-valued parameter defaults to NOTHING AT ALL, which is a different
        statement from defaulting to an empty set, and the two must not collapse into one
        answer. Declaring the parameter `required` instead would refuse at the gate's own
        conforming-call door and never reach this evaluator — driven, and it is why this row
        is shaped this way."""
        self.gate.execute("CREATE-OP", "owner", {"name": "K2-NO-DEFAULT", "definition": {
            "description": "the many-valued parameter defaults to nothing at all",
            "law_cited": "CAP-IS-LAW",
            "object_param": "subject", "params": {"subject": "required"},
            "structural_params": ["subject"],           # object identifier, inline scalar
            "param_defaults": {MEMBERS: None},
            "payload_from": ["subject", MEMBERS],
            "checks": [every_member_row(INNER_DOMAIN, on_empty="admit")]}})
        rule, msg = self.refusal_of(self.gate.execute, "K2-NO-DEFAULT", "owner",
                                    {"subject": "s"})
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("not a set", msg)

    def test_a_required_many_valued_parameter_refuses_at_the_conforming_call_door_instead(self):
        """THE CONTROL FOR THE ROW ABOVE, so its shape is evidenced rather than asserted. The
        same absence, declared `required`, is refused EARLIER and by a different door — which
        is correct, and which is why the row above declares a null default to reach the
        evaluator at all."""
        self.gate.execute("CREATE-OP", "owner", {"name": "K2-REQUIRED", "definition": {
            "description": "the many-valued parameter is required", "law_cited": "CAP-IS-LAW",
            "object_param": "subject",
            "params": {"subject": "required", MEMBERS: "required"},
            # subject = inline object id; members = a set of member ids (many-valued, in params
            # here), STRUCTURAL matching the shipped census's `capabilities` on REGISTER-CAPABILITY.
            # Classifying both lets the CREATE pass the vocabulary door so the missing-required
            # `members` refuses at the intended conforming-call door (also AR-2), per the docstring.
            "structural_params": ["subject", MEMBERS],
            "payload_from": ["subject", MEMBERS],
            "checks": [every_member_row(INNER_DOMAIN, on_empty="admit")]}})
        rule, _ = self.refusal_of(self.gate.execute, "K2-REQUIRED", "owner", {"subject": "s"})
        self.assertEqual(rule, "AR-2")

    def test_a_LIST_and_a_TUPLE_are_both_sets_because_a_recorded_definition_is_frozen(self):
        """`_require_wellformed_value_domain`'s own reasoning, inherited: a re-validated
        declaration arrives in its FROZEN spelling, so a list-only test would refuse a shape
        the estate itself had already admitted."""
        self.create([every_member_row(INNER_DOMAIN)], name="K2-TUP")
        self.drive(("alpha", "beta"), name="K2-TUP")


if __name__ == "__main__":
    unittest.main()
