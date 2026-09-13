"""EP-28Z — THE ERA-PIN DEBT, DISCHARGED: the mechanism's one home guarded, and the six
can-fail probes landed as regression rows [2026-08-12].

WHAT THIS FILE IS. Two things that arrived as one debt.

FIRST, THE GUARD ON THE EXTRACTION (C1). `tests/era_pin.py` is now the estate's only
implementation of the era-pin act. This file is what keeps it the only one: it walks
`tests/` entire by AST and reds if any file spawns a `<rev>:<path>` blob read of its own.
Without it the extraction is a tidy-up that the eleventh pass undoes, which is exactly how
the mechanism reached eighteen sites across ten files in the first place.

SECOND, THE SIX CAN-FAIL PROBES (C2). EP-29 W1a amended six rows under charter §A57 and
proved every one of them able to fail — by driving each against a wrong input, outside the
repo, in `/tmp`. The mentor's fence that pass forbade new rows, so the only evidence those
six rows can fail lived in a directory the platform wipes at boot (board :407, :412). The
probes were preserved to `~/gov-lab/evidence/ep29-w1a-era/` and they land here, as rows,
under the standing rule that every verification probe becomes a regression test.

WHAT A ROW HERE ASSERTS, and it is one layer up from where a reader expects. It does not
assert that the founding is a particular shape. It asserts that ANOTHER ROW STILL
DISCRIMINATES — that six rows elsewhere in this suite go RED when their era pin is wrong.
A row whose pin stopped being load-bearing would go on passing, silently, about the wrong
era, and nothing else in this estate looks for that.

THE HONEST HALF, CARRIED FORWARD RATHER THAN QUIETLY DROPPED. Two of `test_ep28j`'s three
era rows DO NOT discriminate a one-era-wrong pin: 54/17/1 and 136/64 read the same at
1.17.0 as at 1.18.0. EP-29 W1a's builder measured that and raised it against its own work.
The table below pins that fact as it is, non-discrimination included, so the day either row
starts or stops discriminating is a red rather than a shrug.

MUTATION DISCIPLINE. Driving another row's pin means substituting a module global. Every
substitution here is restored in a `finally`, and a row below asserts the globals are back
where they started. The suite runs sequentially under `discover`; nothing in this file is
safe under a parallel runner, and that is stated rather than assumed away.
"""

import ast
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import era_pin  # noqa: E402  (the home this file guards; tests/ is on the path under discover)

REPO = era_pin.REPO
TESTS = os.path.join(REPO, "tests")

#: The one file allowed to hold a raw blob read: the home itself.
THE_HOME = "era_pin.py"

#: THE POPULATION THE WALK FOUND, and it is the walk's answer rather than the testimony's.
#: The mentor's taking at HOW-NOT-WHAT (board :410) named FIVE test files. The census by
#: signature found EIGHTEEN SITES ACROSS TEN FILES — a FINDING under this pass's own
#: by-class rule, where fewer than five would have been a stop. Every one of these was
#: re-pointed to the home as a documented flip.
REPOINTED = (
    "test_ep14.py",      # 5 sites — three module reconstructions and an era pack
    "test_ep16.py",      # 1 site  — the pre-EP-16 views module
    "test_ep28h.py",     # 1 site  — an ARBITRARY path at the dispatch head
    "test_ep28i.py",     # 1 site  — pack_at
    "test_ep28j.py",     # 2 sites — the ERA_COMMIT reader and TProvenanceHistory's own
    "test_ep28k.py",     # 1 site  — pack_at
    "test_ep28n.py",     # 2 sites — pack_at and a kernel_port read
    "test_ep28n2.py",    # 3 sites — pack_at and two kernel_port reads
    "test_ep28p.py",     # 1 site  — pack_at, written to a temp path
    "test_ep29.py",      # 1 site  — pack_at
)

#: EVERY PIN THIS SUITE HOLDS, read for the one property that decides whether the
#: extraction's UTF-8 decode is equivalent to the `text=True` it replaced. Sourced from the
#: pin constants of the ten files above; `missing="skip"` so a pin that stops resolving
#: reports as a skip rather than as a CR finding it never made.
PINS = (
    ("190cec107cbd5a73c43b7ad837cc4da16fdc454f", "src/kernel/boot.py"),
    ("b922b608fe224a5b217eaeb32a23589fdf67adf4", era_pin.PACK_PATH),
    ("ede19f782ea5af498b441e02b43561690a848a4a", "src/kernel/views.py"),
    ("050d20e", era_pin.PACK_PATH),
    ("0aa8429", era_pin.PACK_PATH),
    ("4f0839dea02f23bce599cd8acd1ad0d50d29074a", era_pin.PACK_PATH),
    ("2965309", era_pin.PACK_PATH),
    ("a6a20f3", era_pin.PACK_PATH),
    ("61f38d8", era_pin.PACK_PATH),
    ("28b1070", era_pin.PACK_PATH),
    ("28b1070", "src/bridge/kernel_port.py"),
    ("9d0822ce5f552d74ddb1c135621f4f9e3f67e6cb", era_pin.PACK_PATH),
    ("aaf7652", era_pin.PACK_PATH),
    ("aaf7652", "src/bridge/kernel_port.py"),
    ("d8a184b81fdd5610880d05af8ab12f634c16b806", era_pin.PACK_PATH),
    ("b9d9573", era_pin.PACK_PATH),
)


# =================================================================================================
# THE CENSUS — factored so it can be driven with SYNTHETIC source (§A42), never only read
# =================================================================================================

_BLOB_VERBS = {"show", "cat-file", "archive"}


def _spawns_git(call):
    f = call.func
    if isinstance(f, ast.Attribute) and f.attr in ("run", "check_output", "Popen", "call",
                                                   "check_call"):
        base = f.value
        if isinstance(base, ast.Name) and base.id == "subprocess":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "subprocess":
            return True
    return isinstance(f, ast.Name) and f.id in ("run", "check_output")


def _argv(call):
    """The statically-visible shape of argv[0]. A substituted hole becomes '\\x00', so a
    dynamic path is VISIBLE as a hole rather than invisible as a missing literal."""
    if not call.args:
        return None
    a = call.args[0]
    if not isinstance(a, (ast.List, ast.Tuple)):
        return None
    out = []
    for e in a.elts:
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            out.append(e.value)
        elif isinstance(e, ast.JoinedStr):
            out.append("".join(v.value if isinstance(v, ast.Constant) else "\x00"
                               for v in e.values))
        elif isinstance(e, ast.BinOp) and isinstance(e.op, ast.Mod) \
                and isinstance(e.left, ast.Constant) and isinstance(e.left.value, str):
            out.append(e.left.value)
        else:
            out.append("\x00")
    return out


def blob_read_sites(source):
    """Every ERA-PIN SITE in `source`: a git spawn carrying a <rev>:<path> blob reference.

    THE SIGNATURE, and its generality is CLAIMED HERE so it can be attacked on its own
    axis (§A64): the caller's post-processing is IRRELEVANT — json.loads, .decode(), exec
    into a module and a write to a temp file are all the same site. What decides membership
    is the argv, and nothing else.

    CORRECTED BEFORE IT SHIPPED, 2026-08-12, and the correction is recorded because it is
    this rule's own failure mode: the first form required the path side of `<rev>:<path>` to
    be a LITERAL (a '/' in it, or a .py/.json suffix). It missed THREE REAL SITES whose path
    is substituted at run time — `test_ep14.py` twice and `test_ep28h.py` once — and
    returned a confident 15 where the answer is 18. A filter encodes an assumption about the
    population's FORM, and the form is not what anyone is thinking about while writing it.
    """
    sites = []
    for n in ast.walk(ast.parse(source)):
        if not (isinstance(n, ast.Call) and _spawns_git(n)):
            continue
        argv = _argv(n)
        if not argv or os.path.basename(argv[0]) != "git":
            continue
        verb = argv[1] if len(argv) > 1 else ""
        if verb not in _BLOB_VERBS:
            continue
        for v in argv[1:]:
            if v.startswith("-"):
                continue
            left, sep, right = v.partition(":")
            if sep and right:
                sites.append((n.lineno, v))
                break
    return sites


def _census():
    out = {}
    for f in sorted(os.listdir(TESTS)):
        if not f.endswith(".py"):
            continue
        with open(os.path.join(TESTS, f), encoding="utf-8") as fh:
            s = blob_read_sites(fh.read())
        if s:
            out[f] = s
    return out


# =================================================================================================
# C1 — ZERO COPIES SURVIVE, and the instrument that says so is driven on both axes
# =================================================================================================

class TestTheMechanismHasExactlyOneHome(unittest.TestCase):

    def test_no_test_file_reads_a_pinned_blob_for_itself(self):
        """THE SET-DIFF, both directions. The census's found-set after this pass must be
        exactly {era_pin.py}: every other file reaches an era through the home.

        RED WORLD: a later pass writing its own `pack_at` reds here on its first arm."""
        found = set(_census())
        self.assertEqual(found - {THE_HOME}, set(),
                         "a test file holds its own blob read — the mechanism has been "
                         "copied again: %s" % sorted(found - {THE_HOME}))
        self.assertEqual({THE_HOME} - found, set(),
                         "non-vacuity: the home itself must contain the one site, or this "
                         "census is walking the wrong tree")

    def test_the_home_holds_exactly_one_site(self):
        """One home means ONE implementation, not one file with three."""
        self.assertEqual(len(_census()[THE_HOME]), 1)

    def test_every_file_the_extraction_touched_imports_the_home(self):
        """NON-VACUITY ON THE FLIP ITSELF: zero copies is the same figure whether the sites
        were re-pointed or deleted. This row is what tells those apart — the ten files the
        census named before the extraction must now IMPORT `era_pin`."""
        for f in REPOINTED:
            with open(os.path.join(TESTS, f), encoding="utf-8") as fh:
                src = fh.read()
            self.assertIn("import era_pin", src,
                          "%s lost its blob read without gaining the home — the site was "
                          "deleted rather than re-pointed" % f)

    def test_every_pin_this_suite_holds_is_free_of_carriage_returns(self):
        """The one input on which `text=True` and an explicit UTF-8 decode differ. The
        extraction replaced the first with the second at nine sites; this row is why that
        replacement is a fact rather than an assumption."""
        checked = 0
        for rev, path in PINS:
            blob = era_pin.blob_at(rev, path, missing="skip")
            self.assertNotIn(b"\r", blob, "%s:%s carries a CR" % (rev, path))
            checked += 1
        self.assertEqual(checked, len(PINS), "non-vacuity: every pin was actually read")
        self.assertGreater(checked, 10, "non-vacuity: the pin list is not a stub")


class TestTheCensusCanTellAMechanismFromALookalike(unittest.TestCase):
    """§A64: a structural row whose subject is a PATTERN is untested until a NEAR-MISS has
    been driven against it. Both directions, both recorded as this suite's own output."""

    SHOULD_MATCH = {
        "subprocess.run, %-format, literal path":
            'subprocess.run(["git", "show", "%s:src/founding/founding-pack.json" % c])',
        "subprocess.check_output, f-string, literal path":
            'subprocess.check_output(["git", "show", f"{SHA}:src/kernel/boot.py"])',
        "a SUBSTITUTED path — the form the first census missed":
            'subprocess.check_output(["git", "show", f"{SHA}:{path}"])',
        "a substituted path in %-format — test_ep28h's spelling":
            'subprocess.run(["git", "show", "%s:%s" % (HEAD, path)])',
        "cat-file blob — the same act, a different verb":
            'subprocess.run(["git", "cat-file", "blob", "%s:src/x.py" % c])',
    }

    #: THE COMMENT-CLAIMED GENERALITY, ON ITS OWN AXIS (§A64's second half). The signature
    #: claims post-processing is irrelevant. These four differ in nothing else.
    POST_PROCESSING = {
        "json.loads": 'json.loads(subprocess.check_output(["git","show","%s:p.json" % c]))',
        "decode":     'subprocess.check_output(["git","show","%s:p.py" % c]).decode()',
        "exec":       'exec(compile(subprocess.check_output(["git","show","%s:p.py" % c]),"x","exec"))',
        "temp file":  'open(t,"w").write(subprocess.run(["git","show","%s:p.py" % c]).stdout)',
    }

    SHOULD_NOT_MATCH = {
        "git show REV — a COMMIT read, not a blob read":
            'subprocess.run(["git", "show", COMMIT])',
        "git show --stat REV — still a commit read, and it has a dash":
            'subprocess.run(["git", "show", "--stat", COMMIT])',
        "git rev-parse — a repository fact":
            'subprocess.check_output(["git", "rev-parse", "HEAD"])',
        "git log with a format — a repository fact wearing a colon-free spec":
            'subprocess.check_output(["git", "log", "-1", "--format=%H", REV])',
        "git status --porcelain -- path — a path, but the LIVE one":
            'subprocess.run(["git", "status", "--porcelain", "--", "src/founding/"])',
        "open() on the live tree — the act an era pin exists to avoid":
            'open(os.path.join(REPO, "src/founding/founding-pack.json")).read()',
        "the phrase in a docstring — testimony, never a call":
            'def f():\n    """we use git show %s:path here"""\n    return 1',
    }

    def test_every_lookalike_that_IS_the_mechanism_is_counted(self):
        for label, src in self.SHOULD_MATCH.items():
            with self.subTest(label):
                self.assertEqual(len(blob_read_sites(src)), 1,
                                 "a real era-pin site spelled %r was not counted" % label)

    def test_the_claimed_generality_holds_on_its_own_axis(self):
        for label, src in self.POST_PROCESSING.items():
            with self.subTest(label):
                self.assertEqual(len(blob_read_sites(src)), 1,
                                 "post-processing %r changed the verdict, so the "
                                 "signature's own comment is false" % label)

    def test_no_lookalike_that_is_NOT_the_mechanism_is_counted(self):
        for label, src in self.SHOULD_NOT_MATCH.items():
            with self.subTest(label):
                self.assertEqual(blob_read_sites(src), [],
                                 "a non-site spelled %r was counted as a copy" % label)


# =================================================================================================
# C2 — THE SIX CAN-FAIL PROBES, AS ROWS
# =================================================================================================
#
# THE PINS PLANTED BELOW ARE THE PRESERVED PROBES' OWN, taken from
# `~/gov-lab/evidence/ep29-w1a-era/canfail2.py` (read-only source, GOV-LAB-RULE clause 3).
# Each is a real commit of this repo carrying a real founding, so a red here is a row failing
# to discriminate a NEIGHBOURING era rather than a row failing to notice a garbage string.

J_TRUE = "4f0839dea02f23bce599cd8acd1ad0d50d29074a"   # 1.18.0, EP-28S's close — the true pin
J_WRONG_FORWARD = "ba125bd7c00289e48cc7d01624cd7c54a900b92a"   # 1.19.0, W1a's own landing
J_WRONG_BACK = "d8a184b81fdd5610880d05af8ab12f634c16b806"      # 1.17.0, one era back
J_WRONG_HALF = "05f29f72278830054f4173ad66f0026ff2d5151e"      # the half-written 1.17.0

N_TRUE = "d8a184b81fdd5610880d05af8ab12f634c16b806"    # EP-28N2's own close
N_WRONG_BEFORE = "aaf7652"                             # the BEFORE itself — nothing moved
N_WRONG_FORWARD = "ba125bd7c00289e48cc7d01624cd7c54a900b92a"
N_WRONG_COINCIDENCE = "4f0839dea02f23bce599cd8acd1ad0d50d29074a"


def drive(case, name):
    """Run ONE row and report GREEN / RED, never raising. A probe that propagates its
    subject's failure would report the subject's red as its own."""
    try:
        getattr(case, name)()
        return "GREEN"
    except AssertionError:
        return "RED"


class TestTheEp28jEraRowsStillDiscriminate(unittest.TestCase):
    """PROBE 2, preserved. `test_ep28j`'s three era-pinned rows against four eras."""

    ROWS = (("digest", "TAuditChangedNoLaw",
             "test_founding_version_and_digest_are_read_not_written"),
            ("axis_b", "TDivergenceTable",
             "test_AXIS_B_the_lone_holdout_is_checks_and_the_holdout_is_DICT_ENTRY"),
            ("near_miss", "TPopulation",
             "test_near_miss_op_shaped_records_that_are_NOT_ops"))

    #: The table EP-29 W1a's builder measured and raised against its own work. Two of the
    #: three rows DO NOT discriminate a one-era-wrong pin, and that is pinned as a fact
    #: rather than smoothed: only `digest` reds on a near-miss era.
    EXPECTED = {
        J_TRUE:          {"digest": "GREEN", "axis_b": "GREEN", "near_miss": "GREEN"},
        J_WRONG_FORWARD: {"digest": "RED",   "axis_b": "RED",   "near_miss": "RED"},
        J_WRONG_BACK:    {"digest": "RED",   "axis_b": "GREEN", "near_miss": "GREEN"},
        J_WRONG_HALF:    {"digest": "RED",   "axis_b": "GREEN", "near_miss": "GREEN"},
    }

    def _sweep(self, module, commit):
        old = module.ERA_COMMIT
        module.ERA_COMMIT = commit
        try:
            return {tag: drive(getattr(module, cls)(name), name)
                    for tag, cls, name in self.ROWS}
        finally:
            module.ERA_COMMIT = old

    def test_the_three_rows_answer_exactly_the_measured_table(self):
        import test_ep28j
        for commit, expected in self.EXPECTED.items():
            with self.subTest(commit[:8]):
                self.assertEqual(self._sweep(test_ep28j, commit), expected)

    def test_the_digest_row_is_the_only_one_carrying_the_pin(self):
        """The finding, asserted rather than described: on a one-era-wrong pin the other two
        rows stay GREEN, so the pin's correctness rests on `digest` ALONE. The day a second
        row starts discriminating, this reds and the single point of failure has moved."""
        import test_ep28j
        back = self._sweep(test_ep28j, J_WRONG_BACK)
        self.assertEqual(back["digest"], "RED")
        self.assertEqual([back["axis_b"], back["near_miss"]], ["GREEN", "GREEN"])

    def test_the_module_global_is_restored(self):
        """The mutation discipline, checked rather than promised."""
        import test_ep28j
        self._sweep(test_ep28j, J_WRONG_FORWARD)
        self.assertEqual(test_ep28j.ERA_COMMIT, J_TRUE)


class TestTheEp28n2AfterPinStillDiscriminates(unittest.TestCase):
    """PROBE 3, preserved. And its last line is the one that matters: THE REJECTED PIN
    PASSES. EP-28S's close is green for both rows by coincidence — its three re-declared
    minting ops happen to fall inside EP-28N2's own enumeration — which is why the pin
    choice was raised as non-falsifiable by the rows it serves."""

    ROWS = ("test_exactly_the_enumerated_definitions_moved_and_nothing_else",
            "test_the_ONLY_non_op_record_that_moved_is_the_law_that_declares_the_key_space")

    EXPECTED = {
        N_TRUE:              ["GREEN", "GREEN"],
        N_WRONG_BEFORE:      ["RED", "RED"],
        N_WRONG_FORWARD:     ["RED", "RED"],
        N_WRONG_COINCIDENCE: ["GREEN", "GREEN"],
    }

    def _sweep(self, module, commit):
        old = module.AFTER_COMMIT
        module.AFTER_COMMIT = commit
        try:
            out = []
            for name in self.ROWS:
                case = module.TestTheDiffIsTheChange(name)
                case.setUp()
                out.append(drive(case, name))
            return out
        finally:
            module.AFTER_COMMIT = old

    def test_both_rows_answer_exactly_the_measured_table(self):
        import test_ep28n2
        for commit, expected in self.EXPECTED.items():
            with self.subTest(commit[:8]):
                self.assertEqual(self._sweep(test_ep28n2, commit), expected)

    def test_the_rejected_pin_is_GREEN_and_that_is_the_whole_reason_it_was_rejected(self):
        """Exhibited, never argued: a green at `4f0839de` is not evidence for the pin. If
        this ever reds, the coincidence has ended and the derivation gained a witness — a
        finding either way, which is why the row asserts the green rather than avoiding it."""
        import test_ep28n2
        self.assertEqual(self._sweep(test_ep28n2, N_WRONG_COINCIDENCE), ["GREEN", "GREEN"])

    def test_the_module_global_is_restored(self):
        import test_ep28n2
        self._sweep(test_ep28n2, N_WRONG_BEFORE)
        self.assertEqual(test_ep28n2.AFTER_COMMIT, N_TRUE)


class TestTheEp25NonIncreaseRowStillDiscriminates(unittest.TestCase):
    """PROBE 1 and 1b, preserved. The row asserts that no name JOINED the cited-but-unseeded
    class. Both directions matter and only one of them is a failure: a name joining must
    RED, and the class SHRINKING must stay GREEN — the shrink is the amendment's entire
    point, and an equality assertion (what the row said before :388) reds on it."""

    ROW = "test_the_pre_existing_ride_did_not_widen"

    def _case(self):
        import test_ep25
        c = test_ep25.TestSeededCitations(self.ROW)
        c.setUp()
        return c

    def test_the_row_is_GREEN_on_the_real_pack(self):
        """The control. Without it a RED below could be the row being broken rather than
        the plant working."""
        self.assertEqual(drive(self._case(), self.ROW), "GREEN")

    def test_a_name_JOINING_the_class_reds_it(self):
        """THE PLANT: an op citing a law no record seeds. Driven through the row's own
        subject — a deep copy of the pack — never against the tree."""
        import copy
        c = self._case()
        planted = copy.deepcopy(c.pack)
        planted["steps"][0]["records"].append(
            {"actor": "X", "action": "CREATE-OP", "object": "op:PLANTED",
             "payload": {"name": "PLANTED-OP",
                         "definition": {"law_cited": "PLANTED-LAW-NOBODY-SEEDED"}}})
        c.pack = planted
        self.assertEqual(drive(c, self.ROW), "RED")

    def test_the_class_SHRINKING_stays_GREEN(self):
        """1b, and it is the assertion the :388 amendment exists for. Three more of the
        twelve seeded shrinks the class 12 -> 9. The superseded EQUALITY form reds here."""
        c = self._case()
        c.seeded = c.seeded | {"MEM-LAW-ALLOC", "SCHED-LAW-HALT", "COMM-LAW-QUEUE"}
        self.assertEqual(drive(c, self.ROW), "GREEN")

    def test_nothing_seeded_at_all_reds_it(self):
        """The far end of the same axis: with the seeded set empty every citation joins the
        class, so the row must red. Non-vacuity on the plant above — it proves the row reads
        `seeded` at all rather than only the pack."""
        c = self._case()
        c.seeded = set()
        self.assertEqual(drive(c, self.ROW), "RED")


def drive_with_message(case, name):
    """`drive` plus the RED's own words. A verdict says the guard fired; only the message
    says it fired ABOUT THE RIGHT THING, and MAINT-2's A3 asks for both."""
    try:
        getattr(case, name)()
        return "GREEN", ""
    except AssertionError as exc:
        return "RED", str(exc)


# =================================================================================================
# MAINT-2 — THE FOUR REPAIRED WIDTH GUARDS, DRIVEN IN BOTH DIRECTIONS
# =================================================================================================
#
# WHY THESE ROWS EXIST, AND IT IS NOT SYMMETRY FOR ITS OWN SAKE. MAINT-2 repaired four
# assertions that compared a stored seven-character literal against fresh `%h` output. `git`
# picks `%h`'s width from REPOSITORY SIZE, so those rows had begun reading red BECAUSE THE
# REPOSITORY GREW, with nothing they guard having moved — a clock nobody set, firing in the
# layer every other verification in this estate rests on.
#
# THE HAZARD OF THAT REPAIR IS THE REPAIR ITSELF. A row that no longer reds on a width change
# and no longer reds on ANYTHING is not repaired, it is deleted, and it looks identical from
# the suite's summary line. So each repaired row is driven here against BOTH worlds:
#
#   SUBJECT MOVED     the pin replaced by a DIFFERENT commit  -> MUST RED, and the message
#                     must still name what moved
#   WIDTH GREW        the pin replaced by the SAME commit at a LONGER rendering -> MUST be
#                     SILENT
#
# NEITHER DIRECTION IS EVIDENCE ALONE. The first without the second is the defect; the second
# without the first is the deletion. They are one row in two directions.
#
# The mutation discipline is this file's own, from the probes above: the class attribute is
# restored in a `finally`, and a row below asserts the restoration rather than promising it.

class TestTheRepairedWidthGuardsStillDiscriminate(unittest.TestCase):

    #: module · class · row · the attribute holding the pin · the SAME commit, LONGER.
    #: The wider spelling is `git rev-parse --short` output for the pin itself, so the pair
    #: differs in RENDERING ONLY — which is the whole world A4 is about.
    GUARDS = (
        ("test_ep28f", "TestTheFourSubjectFilesAreUnchanged",
         "test_the_range_is_the_one_EP_28F_ran_in", "LANDED_AT", "208a1ee3"),
        ("test_ep28j", "TWhereTheDivergenceCameFrom",
         "test_the_pin_is_chosen_by_CONTENT_not_by_a_label", "PIN", "b9d95730"),
        ("test_ep28j", "TAuditChangedNoLaw",
         "test_the_range_the_founding_row_reads_is_THIS_AUDITS_OWN_and_is_CLOSED",
         "AUDIT_LANDED_AT", "69764cf4"),
        ("test_ep29", "TheVocabularyRateHeld",
         "test_the_range_the_engine_row_reads_is_W1as_OWN_and_is_CLOSED",
         "W1A_LANDED_AT", "a96a34da"),
    )

    @staticmethod
    def _cls(module_name, class_name):
        return getattr(__import__(module_name), class_name)

    def _drive_with(self, guard, value):
        module_name, class_name, row, attr, _wider = guard
        cls = self._cls(module_name, class_name)
        old = getattr(cls, attr)
        setattr(cls, attr, value)
        try:
            return drive_with_message(cls(row), row)
        finally:
            setattr(cls, attr, old)

    def test_each_repaired_guard_is_GREEN_as_it_stands(self):
        """THE CONTROL UNDER THE CONTROLS. Without it a GREEN below could be the row having
        stopped asserting rather than the width being genuinely irrelevant."""
        for guard in self.GUARDS:
            with self.subTest(guard[2]):
                verdict, msg = self._drive_with(guard, getattr(
                    self._cls(guard[0], guard[1]), guard[3]))
                self.assertEqual(verdict, "GREEN", msg)

    def test_A3_a_guard_whose_SUBJECT_MOVED_still_REDS(self):
        """THE LOAD-BEARING DIRECTION. `HEAD` is a real commit, resolves cleanly, and is a
        descendant of every near end these rows use — so nothing upstream of the comparison
        can refuse first and the RED that arrives is the identity check's own."""
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout.strip()
        for guard in self.GUARDS:
            with self.subTest(guard[2]):
                verdict, msg = self._drive_with(guard, head)
                self.assertEqual(verdict, "RED",
                                 "the guard went silent on a commit that is not its pin")
                self.assertTrue(msg.strip(), "the guard red with no message at all")
                self.assertIn(head, msg,
                              "the message does not name the commit that moved in")

    def test_A4_a_guard_whose_ABBREVIATION_ONLY_GREW_is_SILENT(self):
        """THE OTHER DIRECTION, and it is the defect MAINT-2 was minted for. Each pin is
        replaced by ITS OWN full-length neighbour — same commit, longer name. Before the
        repair three of these four rows read RED on exactly this substitution."""
        for guard in self.GUARDS:
            wider = guard[4]
            with self.subTest(guard[2]):
                self.assertNotEqual(wider, getattr(self._cls(guard[0], guard[1]), guard[3]),
                                    "the wide spelling is not actually different text")
                self.assertEqual(
                    subprocess.run(["git", "rev-parse", wider + "^{commit}"], cwd=REPO,
                                   capture_output=True, text=True).stdout.strip(),
                    subprocess.run(["git", "rev-parse",
                                    getattr(self._cls(guard[0], guard[1]), guard[3])
                                    + "^{commit}"], cwd=REPO,
                                   capture_output=True, text=True).stdout.strip(),
                    "the two spellings are not the same commit, so this is not a width world")
                verdict, msg = self._drive_with(guard, wider)
                self.assertEqual(verdict, "GREEN", msg)

    def test_the_mutated_attributes_are_restored(self):
        """The mutation discipline, checked rather than promised — this file's own rule from
        the preserved probes above."""
        before = [getattr(self._cls(g[0], g[1]), g[3]) for g in self.GUARDS]
        for guard in self.GUARDS:
            self._drive_with(guard, "deadbee")
        self.assertEqual([getattr(self._cls(g[0], g[1]), g[3]) for g in self.GUARDS], before)

    def test_an_UNRESOLVABLE_pin_RAISES_rather_than_passing_quietly(self):
        """The third world, and it is the one a sentinel-returning resolver would swallow:
        a pin that has stopped naming anything must be a finding, never a silent green."""
        for guard in self.GUARDS:
            with self.subTest(guard[2]):
                verdict, msg = self._drive_with(guard, "deadbee")
                self.assertEqual(verdict, "RED")
                self.assertIn("deadbee", msg)


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
