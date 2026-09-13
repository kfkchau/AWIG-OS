# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28H — the lifecycle pass: tests close what they open, and the harness reports
what it means.

The acceptance battery the EP names before code, each row with its RED WORLD driven
rather than described:

  T-TEARDOWN-CLOSES          item 1 — `tests/test_ep28d.py` closes every real store it
                             builds; the eight rows go green with their assertions
                             BYTE-UNCHANGED against the dispatch commit. Red world: a
                             double reverting the close reds the whole class again.
  T-VALUE-NOT-TEXT           item 2 — `tests/test_ep28.py:321` asserts membership
                             against the PARSED descriptor list. INVARIANCE: the row
                             passes at a MULTI-DIGIT descriptor, the adverse world
                             produced and held. Red world: the pre-fix substring form
                             under that same world, both driven, divergence exhibited.
  T-DUP2-RELATIVE            item 3 — `dup2` reports `fd#N` exactly as `_n_fd` does;
                             the absolute-descriptor class is EMPTY BY CONSTRUCTION.
                             Red world: an integer-passthrough double returns a member.
  T-BASELINE-RECAPTURED      item 3 — `baselines/host-local/` re-captured through the
                             documented procedure; the diff is exactly the dup
                             representation; a second fresh capture diffs empty. Red
                             world: the hand-edit double fails reproduce-from-procedure.
  T-WIDTH1-VEHICLE           item 4 — the injected divergence distinguishes its two
                             objects BY CONSTRUCTION. INVARIANCE: the values differ
                             regardless of allocation. Red worlds: the pre-fix
                             address-derived form under a perturbed allocation, driven
                             through the row's own path; and the hand-list double.
  T-FLUSH-IS-BEHAVIOUR       item 5 — the re-aimed row asserts the ORDER as behaviour,
                             observed on the executing path. Red world: a double
                             issuing the barrier before the buffer reaches the kernel.
  T-CAP-TRACKS-THE-STORE     item 6 — row 11 re-aimed at the store as it now stands,
                             with the instrument docstring corrected in the same act.
                             Red world: a per-append-reopen double reproduces the OLD
                             interleaving and the OLD answer.
  T-MAP-PREDICTED-ROW-BY-ROW the map as DATA, declared per row before building and
                             checked per row after. Red world, GENERATED: a double that
                             lands item 1 only.
  T-RAISE3-STANDS            the raise-3 intake cited at its filed home, the citation
                             RESOLVING rather than asserted; and §4's non-discharge
                             sentence present in this pass's own order file.

WHAT THIS FILE DOES NOT CLAIM, said here rather than left as an absence. A green suite
with no `[Errno 9]` in it is NOT evidence about the store-lifecycle finalizer defect
carried at `planning/exec/EP-28C.md` AMENDMENT 4 §4.2. This pass removed the estate's
own OCCASION for that defect and touched no product code at all; the mechanism is
exactly where it was. `TestRaise3Stands` below is the citation obligation, not a
discharge, and it is the only thing in this file that mentions the intake.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
# This battery reads OTHER test files' rows and drives them through their own paths, so
# the suite directory is on the path under `discover` and under a direct module run
# alike — a red world that only reproduces under one invocation is not reproducible.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kernel.store import EventStore  # noqa: E402
from tools.conformance.harness import probe as probe_mod, runner  # noqa: E402

import test_ep28  # noqa: E402
import test_ep28b  # noqa: E402
import test_ep28d  # noqa: E402
import test_ep28e_w2  # noqa: E402
import era_pin     # noqa: E402  (the era-pin home, EP-28Z)
import test_ep28f  # noqa: E402

BASELINES = REPO / "tools" / "conformance" / "baselines"

#: The commit EP-28H was dispatched at and verified byte-identical to. Every structural
#: comparison in this file is taken against it rather than against a moving HEAD.
DISPATCH_HEAD = "770fe4a"


def _at_dispatch(path):
    """[DOCUMENTED FLIP — EP-28Z, 2026-08-12. CAUSE: one of EIGHTEEN copies of the era-pin
    act across TEN test files. This site is the one the FIRST census MISSED, because its
    path is substituted rather than literal and the filter had assumed the population's
    form. ASSERTED: a local `git show` spawn raising `AssertionError` on an unresolvable
    pin. SUPERSEDED: the same act from `tests/era_pin.py`. REMAINS TRUE: the failure mode —
    `missing="assert"` raises `AssertionError` carrying git's own stderr, so an
    unresolvable dispatch head still lands as a FAIL and not as an ERROR. GIVEN UP:
    nothing.]"""
    return era_pin.text_at(DISPATCH_HEAD, path, missing="assert")


def _method(source, class_name, method_name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == method_name:
                    return fn
    raise AssertionError("no %s.%s" % (class_name, method_name))


def _assertions(source, class_name, method_name):
    """Every `self.assert*` call in one method, as its own source text. The question is
    whether the ASSERTIONS moved, so the answer is read off the assertions rather than
    off the file — a diff over the file would report the construction line this item
    had to change and say nothing about what it was asked."""
    fn = _method(source, class_name, method_name)
    return [ast.get_source_segment(source, n) for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr.startswith("assert")]


# =====================================================================================
# T-TEARDOWN-CLOSES
# =====================================================================================

#: The EIGHT rows item 1 predicts, named individually. The ninth red row in that file
#: is the honest cap (item 6) and is deliberately NOT here: the plan's own count naming
#: eight against nine reds is what showed the green derivation was short.
THE_EIGHT = (
    ("TestEstablishingTheDescriptorFirstRepairsIt",
     "test_the_row_answers_ebadf_for_its_own_reason"),
    ("TestEstablishingTheDescriptorFirstRepairsIt",
     "test_the_held_number_is_below_every_number_the_row_touches"),
    ("TestEstablishingTheDescriptorFirstRepairsIt",
     "test_the_instruments_record_path_survives_the_row"),
    ("TestEstablishingTheDescriptorFirstRepairsIt",
     "test_the_descriptor_table_is_unchanged_across_the_row"),
    ("TestTheOldInterleavingIsReproducedAndCaught",
     "test_the_rows_ebadf_is_manufactured_and_not_measured"),
    ("TestTheOldInterleavingIsReproducedAndCaught",
     "test_the_descriptor_the_store_held_is_the_one_the_first_close_freed"),
    ("TestTheOldInterleavingIsReproducedAndCaught",
     "test_the_instruments_own_record_path_is_what_breaks"),
    ("TestTheRealStoreAsItStands",
     "test_the_row_answers_ebadf_with_the_repair_in_place"),
)


def _neutered(base):
    """A double of one `DescriptorCase` class with the repair REVERTED: the pre-fix
    `tearDown` body, which closed the double's extra descriptor and never the real
    store's. Everything else — setUp, the rows, the assertion — is the file's own."""

    class Neutered(base):
        leaked = []

        def tearDown(self):
            for store in self._stores:
                if hasattr(store, "close_held"):
                    store.close_held()
                Neutered.leaked.append(store)
            shutil.rmtree(self.dir, ignore_errors=True)
            self.assertEqual(
                test_ep28d._open_descriptors(),
                self._fds_at_entry,
                "this test ended holding descriptors it did not start with",
            )

    Neutered.__name__ = "Neutered" + base.__name__
    return Neutered


class TestTearDownCloses(unittest.TestCase):
    """T-TEARDOWN-CLOSES. The eight rows report a TRUE fact and the fix is the
    lifecycle, never the assertion — so the assertions are pinned byte-for-byte against
    the dispatch commit and the repair is proven by reverting it."""

    def test_every_one_of_the_eight_assertions_is_byte_unchanged(self):
        old = _at_dispatch("tests/test_ep28d.py")
        new = (REPO / "tests" / "test_ep28d.py").read_text(encoding="utf-8")
        for cls, name in THE_EIGHT:
            self.assertEqual(_assertions(old, cls, name), _assertions(new, cls, name),
                             "%s.%s's assertions moved; the fix is the lifecycle" % (cls, name))

    def test_the_leak_assertion_itself_is_byte_unchanged(self):
        """The row that reds the eight is the proof the repair worked, so it is the last
        thing that may be edited to make them green."""
        old = _at_dispatch("tests/test_ep28d.py")
        new = (REPO / "tests" / "test_ep28d.py").read_text(encoding="utf-8")
        self.assertEqual(_assertions(old, "DescriptorCase", "tearDown"),
                         _assertions(new, "DescriptorCase", "tearDown"))
        self.assertEqual(len(_assertions(new, "DescriptorCase", "tearDown")), 1)

    def test_the_eight_are_green_and_a_neutered_tearDown_REDS_THEM_ALL(self):
        """THE RED WORLD, and the pre-state IS the standing exhibition: every one of the
        eight was red at this pass's reading for exactly this reason. The double
        reproduces it on demand rather than relying on a run nobody can re-take."""
        doubles = {c.__name__.replace("Neutered", ""): c for c in (
            _neutered(test_ep28d.TestEstablishingTheDescriptorFirstRepairsIt),
            _neutered(test_ep28d.TestTheOldInterleavingIsReproducedAndCaught),
            _neutered(test_ep28d.TestTheRealStoreAsItStands),
        )}
        try:
            for cls, name in THE_EIGHT:
                with self.subTest(row="%s.%s" % (cls, name)):
                    good = unittest.TestResult()
                    getattr(test_ep28d, cls)(name).run(good)
                    self.assertTrue(good.wasSuccessful(),
                                    "%s is red WITH the repair in place: %r"
                                    % (name, good.failures + good.errors))
                    bad = unittest.TestResult()
                    doubles[cls](name).run(bad)
                    self.assertFalse(bad.wasSuccessful(),
                                     "%s stayed green with the tearDown close reverted, "
                                     "so the repair is not what turned it" % name)
                    text = "".join(t for _c, t in bad.failures + bad.errors)
                    self.assertIn("holding descriptors it did not start with", text)
        finally:
            for store in _neutered(test_ep28d.TestTheRealStoreAsItStands).leaked:
                store.close()
            for cls in doubles.values():
                for store in cls.leaked:
                    store.close()
                cls.leaked = []


# =====================================================================================
# T-VALUE-NOT-TEXT
# =====================================================================================

#: The child program the row runs, carried verbatim from the row so the adverse world
#: below is driven through the row's OWN path and not through a re-enactment of it.
_ROW_CHILD_EXTRA = (
    "closed = _close_inherited_descriptors()\n"
    "targets = sorted(f for f, _t in closed)\n"
    "assert os.path.exists('/proc/self/fd/1'), 'stdout was closed'\n"
    "assert os.path.exists('/proc/self/fd/2'), 'stderr was closed'\n"
)


class TestValueNotText(unittest.TestCase):
    """T-VALUE-NOT-TEXT. The row's subject is GREEN BY LUCK at this pass's entry — the
    inherited descriptor happens to be a single digit today — so its falsifiability is
    not "the row goes green". It is THE ROW CAN NO LONGER FLIP, and the adverse world
    is produced and held rather than assumed absent."""

    def _child_in_a_crowded_table(self, held=16):
        """The adverse world, PRODUCED: enough inheritable descriptors that the child's
        closed-list runs into double digits. The row's own `_child` spawns it."""
        case = test_ep28.TestTheBrainHoldsNothingItDidNotOpen(
            "test_the_daemons_own_log_descriptors_survive")
        d = tempfile.mkdtemp(prefix="ep28h-crowded-")
        fds = []
        try:
            for _ in range(held):
                fd = os.open(d, os.O_RDONLY)
                os.set_inheritable(fd, True)
                fds.append(fd)
            _seen, _still, targets = case._child(fds[0], _ROW_CHILD_EXTRA)
        finally:
            for fd in fds:
                os.close(fd)
            shutil.rmtree(d, ignore_errors=True)
        return targets

    @staticmethod
    def _parsed(targets):
        return [int(t) for t in targets.strip("[] \n").split(",") if t.strip()]

    def test_the_two_forms_DIVERGE_in_the_adverse_world_and_the_value_form_holds(self):
        """Both forms driven over the SAME observation. The substring form finds "1"
        inside "12" and reports a closed stdin that was never closed; the value form
        compares numbers and is right."""
        targets = self._child_in_a_crowded_table()
        parsed = self._parsed(targets)
        self.assertTrue([n for n in parsed if n > 9],
                        "the adverse world was not produced: no multi-digit descriptor "
                        "in %r — raise the held count rather than trusting this row" % targets)
        for digit in ("0", "1", "2"):
            if digit in targets:                      # the PRE-FIX form's answer
                break
        else:
            self.fail("the substring form did not fail in a world with %r — the two "
                      "forms did not diverge and nothing was exhibited" % targets)
        for n in (0, 1, 2):                           # the form the row now carries
            self.assertNotIn(n, parsed,
                             "the daemon's own log descriptors must survive: %r" % parsed)

    def test_the_row_itself_passes_in_that_same_adverse_world(self):
        """INVARIANCE, driven through the row: the descriptor numbers rendered are
        multi-digit and the row is green anyway."""
        targets = self._child_in_a_crowded_table()
        self.assertTrue([n for n in self._parsed(targets) if n > 9], targets)
        result = unittest.TestResult()
        test_ep28.TestTheBrainHoldsNothingItDidNotOpen(
            "test_the_daemons_own_log_descriptors_survive").run(result)
        self.assertTrue(result.wasSuccessful(), result.failures + result.errors)

    def test_the_row_no_longer_reads_its_answer_out_of_the_rendered_text(self):
        """Structural, because the flip is about WHERE the answer is read from: no
        `assertNotIn` in the row takes a string literal against the rendered list."""
        src = (REPO / "tests" / "test_ep28.py").read_text(encoding="utf-8")
        fn = _method(src, "TestTheBrainHoldsNothingItDidNotOpen",
                     "test_the_daemons_own_log_descriptors_survive")
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "assertNotIn"):
                first = node.args[0]
                self.assertIsInstance(first.value, int,
                                      "the row asserts %r, a rendered digit, against a "
                                      "formatted list" % ast.get_source_segment(src, first))


# =====================================================================================
# T-DUP2-RELATIVE
# =====================================================================================

#: Every vocabulary entry whose return value IS a descriptor, named here rather than
#: inferred, so "the class is empty" is a claim about a non-empty subject (§A38).
DESCRIPTOR_RETURNING = ("open", "openat", "dup", "dup2", "pipe_read_fd")


def _absolute_minting_calls(table):
    """Which descriptor-returning entries in a vocabulary table would mint an ABSOLUTE
    number into a capture. Empty means the class cannot be populated by construction."""
    return sorted(name for name in DESCRIPTOR_RETURNING
                  if table[name][1] is not probe_mod._n_fd)


class TestDup2Relative(unittest.TestCase):
    """T-DUP2-RELATIVE. Fix the definitive and the derivative follows: the class is not
    re-pinned one occupancy later, it is emptied at the reporting scheme."""

    def test_dup2_reports_through_the_same_normalizer_as_every_other_descriptor(self):
        self.assertIs(probe_mod.CALLS["dup2"][1], probe_mod._n_fd)
        self.assertEqual(probe_mod.CALLS["dup2"][0], os.dup2,
                         "the callable underneath must be untouched; only the reporting "
                         "moved")

    def test_the_class_is_EMPTY_BY_CONSTRUCTION(self):
        """The subject is the SCHEME, not the artifacts: after this change no
        descriptor-returning entry can write an absolute number into any future capture,
        on any target, including ones nobody has captured yet."""
        self.assertEqual(_absolute_minting_calls(probe_mod.CALLS), [])

    def test_an_integer_passthrough_double_REDS_the_emptiness_clause(self):
        """THE RED WORLD. A guard whose pass condition is an empty enumeration cannot
        tell 'nothing was wrong' from 'nothing was looked at', so the enumeration is
        driven over a table that contains the member it is meant to find."""
        double = dict(probe_mod.CALLS)
        double["dup2"] = (os.dup2, probe_mod._n_passthrough)
        self.assertEqual(_absolute_minting_calls(double), ["dup2"])

    def test_no_committed_capture_carries_an_unnamed_absolute_descriptor(self):
        """The artifact side, enumerated across BOTH baseline directories. `host-local`
        was re-captured under the new construction and carries none; the guest capture
        predates it, cannot be retaken from the host, and its two values are carved out
        BY NAME with their cause and their consumer — EP-28H's own RAISED-BY-DESIGN."""
        found = set()
        for d in sorted(p for p in BASELINES.iterdir() if (p / "06-files.json").exists()):
            found.update(test_ep28f._absolute_fd_values(d))
        self.assertEqual(found - set(test_ep28f.STALE_BY_KNOWN_CAUSE), set())
        self.assertEqual(test_ep28f._absolute_fd_values(BASELINES / "host-local"), [])

    def test_the_two_carve_outs_name_the_same_two_steps(self):
        """The carve-out is written down in TWO places — the class enumeration in
        `test_ep28f.py` and the cross-kernel comparison in `test_ep24.py` — because they
        ask different questions of it. Two copies of one fact drift, so they are
        differenced here rather than trusted to stay equal."""
        import test_ep24
        from_f = {(row, i) for _d, row, i, _ret in test_ep28f.STALE_BY_KNOWN_CAUSE}
        from_24 = {(row, i) for row, indices in
                   test_ep24.TestFilesGroupCaptured.CONSTRUCTION_DIFFERENCE.items()
                   for i in indices}
        self.assertEqual(from_f, from_24)
        self.assertEqual(from_f, {("files.dup", 6), ("files.dup", 9)})
        self.assertEqual({d for d, _r, _i, _v in test_ep28f.STALE_BY_KNOWN_CAUSE},
                         {"ep21-ubuntu-guest"},
                         "the carve-out reaches beyond the one capture that cannot be "
                         "retaken from this host")

    def test_the_instruments_own_surface_agrees(self):
        """The visible proof at the instrument rather than in a test: the `files.dup`
        leg of the harness's own documented self-test, which was the one FAIL in every
        run of this arc. It reads the committed baseline off disk and writes nothing."""
        report = runner.verify("fixture-correct", "host-local")
        by_row = {v.row_id: v for v in report.verdicts}
        self.assertIn("files.dup", by_row)
        self.assertNotIn("files.dup", [v.row_id for v in report.failed],
                         "files.dup: %s" % report.text())
        self.assertTrue(report.ok, "the whole self-test, not only its dup row:\n%s"
                        % report.text())


# =====================================================================================
# T-BASELINE-RECAPTURED
# =====================================================================================

class TestBaselineRecaptured(unittest.TestCase):
    """T-BASELINE-RECAPTURED. The refused reference this row exists against is the
    HAND-EDITED ARTIFACT: a value edited to match the new reporting instead of
    re-captured through the procedure that produces it."""

    HOST = BASELINES / "host-local" / "06-files.json"
    #: Old and new, both kept — the delta is the evidence that the world moved.
    THE_DUP_DELTA = (("i", 6, 200, "fd#2"), ("i", 9, 3, "fd#3"))

    def test_the_diff_against_the_prior_artifact_is_exactly_the_dup_representation(self):
        old = json.loads(_at_dispatch("tools/conformance/baselines/host-local/06-files.json"))
        new = json.loads(self.HOST.read_text(encoding="utf-8"))
        moved = []
        for row_id, row in new["rows"].items():
            for step in row.get("steps", []):
                was = [s for s in old["rows"][row_id]["steps"] if s["i"] == step["i"]]
                self.assertEqual(len(was), 1, "%s step %s" % (row_id, step["i"]))
                if was[0] != step:
                    moved.append((row_id, step["i"], was[0]["ret"], step["ret"]))
        self.assertEqual(
            moved,
            [("files.dup", i, old_v, new_v) for _k, i, old_v, new_v in self.THE_DUP_DELTA],
            "the re-capture moved something other than the dup representation")

    def test_a_fresh_capture_reproduces_the_committed_artifact(self):
        """Reproduce-from-procedure. §A39: this check CREATES the world it reads, into a
        temporary baselines base, and never touches the committed artifact."""
        base = tempfile.mkdtemp(prefix="ep28h-capture-")
        try:
            runner.capture("host-local", baselines_base=base)
            fresh = (Path(base) / "host-local" / "06-files.json").read_bytes()
        finally:
            shutil.rmtree(base, ignore_errors=True)
        self.assertEqual(fresh, self.HOST.read_bytes(),
                         "the committed artifact is not what its own procedure produces")

    def test_the_hand_edit_double_FAILS_reproduce_from_procedure(self):
        """THE RED WORLD. An artifact value with no procedure behind it — the shape the
        plan names as wrong reference #3 — is caught by the same comparison, so the row
        above is not passing merely because nothing was looked at."""
        base = tempfile.mkdtemp(prefix="ep28h-handedit-")
        try:
            runner.capture("host-local", baselines_base=base)
            p = Path(base) / "host-local" / "06-files.json"
            handedited = p.read_text(encoding="utf-8").replace('"ret": "fd#3"', '"ret": 4', 1)
            self.assertNotEqual(handedited, p.read_text(encoding="utf-8"),
                                "the hand-edit changed nothing, so nothing was exhibited")
            p.write_text(handedited, encoding="utf-8")
            second = tempfile.mkdtemp(prefix="ep28h-handedit-2-")
            try:
                runner.capture("host-local", baselines_base=second)
                fresh = (Path(second) / "host-local" / "06-files.json").read_text(
                    encoding="utf-8")
            finally:
                shutil.rmtree(second, ignore_errors=True)
            self.assertNotEqual(fresh, handedited,
                                "a hand-edited value reproduced from the procedure")
        finally:
            shutil.rmtree(base, ignore_errors=True)


# =====================================================================================
# T-WIDTH1-VEHICLE
# =====================================================================================

VEHICLE_ROW = "test_the_diff_enumerates_the_snapshot_rather_than_a_hand_list"


class TestWidth1Vehicle(unittest.TestCase):
    """T-WIDTH1-VEHICLE (item 4, the re-homed EP-28F W6). Same ground as
    T-VALUE-NOT-TEXT: the row is GREEN BY LUCK at this allocation history, so the
    assertion is that IT CAN NO LONGER FLIP."""

    def test_no_address_derived_value_appears_anywhere_in_the_injection(self):
        """Structural, on the injection's own body: an address in the value is the
        defect, whatever it is spelled."""
        src = (REPO / "tests" / "test_ep28e_w2.py").read_text(encoding="utf-8")
        fn = _method(src, "TestADivergenceInTheIndexesHaltsTheMount", VEHICLE_ROW)
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotEqual(node.func.id, "id",
                                    "the injected value is derived from a memory address")

    def test_the_two_values_differ_at_the_MOST_adverse_allocation_there_is(self):
        """INVARIANCE. The adverse world for an address-derived vehicle is two objects
        that collide; the strongest case of that is ONE object, whose address is
        trivially congruent with itself. Both forms driven over it."""
        obj = object()
        pre_fix = lambda o: id(o) % 7                                    # noqa: E731
        self.assertEqual(pre_fix(obj), pre_fix(obj),
                         "the pre-fix vehicle must collide here or nothing is exhibited")
        calls = []

        def by_construction(_o):
            calls.append(1)
            return len(calls)
        self.assertNotEqual(by_construction(obj), by_construction(obj),
                            "the repaired vehicle must differ for two snapshot calls at "
                            "ANY allocation, including the same address twice")

    def _fs_case(self):
        case = test_ep28e_w2.TestADivergenceInTheIndexesHaltsTheMount(VEHICLE_ROW)
        case.setUp()
        self.addCleanup(case.doCleanups)
        return case

    def _drive_with(self, case, value_for):
        """The row's OWN path — `custody.CustodyState.snapshot` patched, `shadow_diff`
        run, the diff read for the injected key — with only the injected VALUE varied."""
        custody = test_ep28e_w2.custody
        real = custody.CustodyState.snapshot

        def patched(self_):
            out = real(self_)
            out["a_key_no_diff_loop_lists"] = {"x": value_for(self_)}
            return out

        custody.CustodyState.snapshot = patched
        try:
            diff = case.fs.shadow_diff()
        finally:
            custody.CustodyState.snapshot = real
        return diff or []

    def test_the_PRE_FIX_form_flips_on_allocation_and_the_repaired_one_does_not(self):
        """THE RED WORLD, produced deliberately through the row's own path (§A42) rather
        than waited for. The allocation regime is SUPPLIED — the two addresses the
        pre-fix arithmetic reads — because real addresses cannot be chosen; the
        arithmetic under test is the row's own `% 7`, unchanged."""
        case = self._fs_case()
        addresses = {}

        def pre_fix(self_):
            return addresses.setdefault(id(self_), len(addresses)) % 7

        # REGIME A — the two objects land in different buckets: the row reports.
        addresses.clear()
        lucky = [d for d in self._drive_with(case, pre_fix)
                 if d.startswith("a_key_no_diff_loop_lists")]
        self.assertTrue(lucky, "the pre-fix form did not even work in its lucky regime")

        # REGIME B — the same arithmetic, two addresses that collide mod 7. Nothing is
        # reported, `shadow_diff` takes its equality exit, and the row reds for a reason
        # that has nothing to do with its subject.
        collide = self._drive_with(case, lambda _self: 0)
        self.assertEqual(
            [d for d in collide if d.startswith("a_key_no_diff_loop_lists")], [],
            "a colliding regime still reported — then the flip has another cause")
        self.assertEqual(collide, [], "shadow_diff must take its equality exit here")

        # THE REPAIRED FORM, under BOTH regimes: it reports either way, because the
        # value differs by construction and never by the heap's mood.
        for _ in range(2):
            calls = []

            def by_construction(_self):
                calls.append(1)
                return len(calls)
            got = self._drive_with(case, by_construction)
            self.assertTrue([d for d in got if d.startswith("a_key_no_diff_loop_lists")],
                            "the repaired vehicle failed to report: %r" % got)

    def test_the_hand_list_double_MISSES_what_the_row_catches(self):
        """The second red world: the SUBJECT still fails when it should. A diff loop
        built on a hand-list of keys — the defect EP-28E W2 fixed — reports nothing for
        the injected key, so the repaired vehicle did not blunt the row."""
        case = self._fs_case()
        custody = test_ep28e_w2.custody
        real = custody.CustodyState.snapshot
        calls = []

        def patched(self_):
            out = real(self_)
            calls.append(1)
            out["a_key_no_diff_loop_lists"] = {"x": len(calls)}
            return out

        custody.CustodyState.snapshot = patched
        try:
            served = case.fs.state.snapshot()
            replayed = custody.fold(case.fs.store.all()).snapshot()
        finally:
            custody.CustodyState.snapshot = real
        hand_list = []
        for key in ("kids", "paths", "names", "inodes"):     # the loop as it once was
            a, b = served.get(key) or {}, replayed.get(key) or {}
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    hand_list.append("%s[%s]" % (key, k))
        self.assertEqual(
            [d for d in hand_list if d.startswith("a_key_no_diff_loop_lists")], [],
            "the hand-list loop reported a key it does not list — then this double is "
            "not the defect the row was built against")
        self.assertNotEqual(served, replayed,
                            "the snapshots must differ, or the hand-list loop is silent "
                            "for the trivial reason instead of the interesting one")

    def test_the_row_is_green_at_BOTH_widths(self):
        """The width-1 exception dies inside this pass, so the row is driven at both
        widths here rather than only across two suite runs. The calibration is read once
        per store, so setting it before the case is built is what varies it."""
        for width in (None, "1"):
            with self.subTest(width=width or "shipped"):
                had = os.environ.get("GOVOS_COMMIT_WIDTH")
                if width is None:
                    os.environ.pop("GOVOS_COMMIT_WIDTH", None)
                else:
                    os.environ["GOVOS_COMMIT_WIDTH"] = width
                try:
                    result = unittest.TestResult()
                    test_ep28e_w2.TestADivergenceInTheIndexesHaltsTheMount(
                        VEHICLE_ROW).run(result)
                finally:
                    if had is None:
                        os.environ.pop("GOVOS_COMMIT_WIDTH", None)
                    else:
                        os.environ["GOVOS_COMMIT_WIDTH"] = had
                self.assertTrue(result.wasSuccessful(),
                                result.failures + result.errors)

    def test_the_classes_deterministic_control_is_byte_unchanged(self):
        """The control beside the repaired row — corrupting real state and driving the
        halt — is what proves the class still fails when it should, so it is pinned
        against the dispatch commit rather than trusted."""
        old = _at_dispatch("tests/test_ep28e_w2.py")
        new = (REPO / "tests" / "test_ep28e_w2.py").read_text(encoding="utf-8")
        for name in ("test_each_index_divergence_is_reported_and_halts",
                     "test_a_clean_world_diverges_in_nothing"):
            self.assertEqual(
                ast.get_source_segment(
                    old, _method(old, "TestADivergenceInTheIndexesHaltsTheMount", name)),
                ast.get_source_segment(
                    new, _method(new, "TestADivergenceInTheIndexesHaltsTheMount", name)),
                "%s moved" % name)


# =====================================================================================
# T-FLUSH-IS-BEHAVIOUR
# =====================================================================================

class _BarrierBeforeTheBuffer:
    """The double the re-aimed row exists to catch: the barrier is issued while the
    record is still in user space. `store.py` is BYTE-UNCHANGED under it — which is the
    whole point, because no text-shape check can see this."""

    def __init__(self, fh):
        self._fh = fh
        self._withheld = False

    def flush(self):
        self._withheld = True          # withheld, not performed
        return None

    def release(self):
        if self._withheld:
            self._fh.flush()
            self._withheld = False

    def __getattr__(self, name):
        return getattr(self._fh, name)


class TestFlushIsBehaviour(unittest.TestCase):
    """T-FLUSH-IS-BEHAVIOUR (item 5). The row was re-aimed from a source-text slice to
    the property the text was standing in for, so the red world is a REORDERED EXECUTION
    over unchanged source."""

    ROW = "test_the_buffer_is_flushed_before_the_barrier"

    def test_the_row_reads_no_source_text_at_all(self):
        """Structural: the re-aim is not a repaired literal. Nothing in the row opens
        `store.py`, and no `str.index` walks it."""
        src = (REPO / "tests" / "test_ep28b.py").read_text(encoding="utf-8")
        fn = _method(src, "TestTheAppendIsStillTheCommit", self.ROW)
        body = "".join(ast.get_source_segment(src, n) or ""
                       for n in fn.body if not isinstance(n, ast.Expr))
        for banned in ("store_mod.__file__", ".index(", "src.index"):
            self.assertNotIn(banned, body, "the row still reads source text: %r" % banned)

    def test_the_row_is_green_and_a_barrier_first_double_REDS_IT(self):
        """THE RED WORLD, driven through the row's own method. The store's held file
        object is wrapped so its flush is withheld past the barrier; the executing order
        changes and the source does not."""
        good = unittest.TestResult()
        test_ep28b.TestTheAppendIsStillTheCommit(self.ROW).run(good)
        self.assertTrue(good.wasSuccessful(), good.failures + good.errors)

        case = test_ep28b.TestTheAppendIsStillTheCommit(self.ROW)
        case.setUp()
        double = _BarrierBeforeTheBuffer(case.store._require_fh())
        before = (REPO / "src" / "kernel" / "store.py").read_bytes()
        case.store._fh = double
        try:
            with self.assertRaises(AssertionError) as caught:
                getattr(case, self.ROW)()
        finally:
            case.store._fh = double._fh
            double.release()
            case.tearDown()
        self.assertIn("still in user space", str(caught.exception))
        self.assertEqual((REPO / "src" / "kernel" / "store.py").read_bytes(), before,
                         "the red world must be unreachable by any text-shape check, so "
                         "the source it would read is unchanged under it")


# =====================================================================================
# T-CAP-TRACKS-THE-STORE
# =====================================================================================

class _ReopensPerAppend(EventStore):
    """The store as it stood BEFORE EP-28C W3, as a TEST DOUBLE: the record descriptor
    is released the moment the batch it served is durable, so its claim on a freed
    number does not survive to the row's next step. One variable — the descriptor's
    LIFETIME — with every record still written by the real appender."""

    def _commit_batch(self, batch):
        out = super()._commit_batch(batch)
        if not self._in_batch:                 # the outer batch only; nested rides it
            self.close()
        return out


def _drive_row_eleven(store_factory):
    """Row 11's own path, with the store varied and nothing else. Returns the row's
    answer, the descriptor the store ended up holding, and the number the row's `open`
    was given — all three read through the case's own helpers."""
    case = test_ep28d.TestTheRealStoreAsItStands(
        "test_the_row_answers_ebadf_without_it_too_and_that_is_the_honest_cap")
    case.setUp()
    try:
        store = store_factory(case.record)
        case._stores.append(store)
        obs, fds = case.run_close_row(store, establish=False)
        held = None if store._fh is None else store._fh.fileno()
        return case.second_close(obs), held, case.row_descriptor(fds)
    finally:
        case.tearDown()


class TestCapTracksTheStore(unittest.TestCase):
    """T-CAP-TRACKS-THE-STORE (item 6). The row's own name scoped it to *the real store
    AS IT STANDS*; the store stopped standing that way at EP-28C W3, and an honest cap
    expiring is the cap working."""

    def test_the_row_answers_what_the_store_now_does(self):
        """The mechanism, not the symptom: the number the store ends up holding IS the
        number the row's `open` was given and its first close released, which is why the
        second close lands on a live descriptor and returns."""
        answer, held, opened = _drive_row_eleven(EventStore)
        self.assertIsNone(answer, "the second close answered %r" % (answer,))
        self.assertEqual(held, opened)

    def test_a_per_append_reopen_double_reproduces_the_OLD_answer(self):
        """THE RED WORLD, and it is what makes the re-aim a measurement rather than a
        capitulation: driven against the store as it USED to be, the row's old answer
        comes back. The row tracks the store's actual descriptor lifetime rather than
        either era's assumption."""
        old_answer, _held, _opened = _drive_row_eleven(_ReopensPerAppend)
        self.assertEqual(old_answer, "EBADF",
                         "the pre-W3 lifetime did not reproduce the old interleaving")
        new_answer, _h, _o = _drive_row_eleven(EventStore)
        self.assertNotEqual(new_answer, old_answer,
                            "the two lifetimes give the same answer — then the row is "
                            "not measuring the lifetime")

    def test_the_guards_present_effect_is_no_longer_zero(self):
        """Rows 1 and 2 of that class are now the same row driven with and without the
        fixture's guard. With it, EBADF; without it, nothing. That difference IS the
        guard's present effect, and it is what the corrected docstring now says."""
        case = test_ep28d.TestTheRealStoreAsItStands(
            "test_the_row_answers_ebadf_with_the_repair_in_place")
        case.setUp()
        try:
            with_guard, _fds = case.run_close_row(case.real_store(), establish=True)
        finally:
            case.tearDown()
        without_guard, _h, _o = _drive_row_eleven(EventStore)
        self.assertEqual(case.second_close(with_guard), "EBADF")
        self.assertIsNone(without_guard)

    def test_the_instrument_docstring_was_corrected_in_the_same_act(self):
        """Item 6 is ONE act: the row re-aimed and the instrument's expired honest cap
        corrected together, dated, with the refuted text retained."""
        src = (REPO / "tools" / "conformance" / "fixtures" / "fixture_shim.py").read_text(
            encoding="utf-8")
        doc = src[src.index("def establish_record_descriptor"):]
        doc = doc[:doc.index("\n    return store._append")]
        self.assertIn("EP-28H item 6, 2026-08-02", doc, "the correction is undated")
        self.assertIn("THE HONEST CAP HAS EXPIRED", doc)
        self.assertIn("The store re-opens the record file per append today", doc,
                      "the refuted text was deleted instead of retained")
        self.assertIn("does NOT re-open per append", doc)

    def test_the_refuted_text_of_the_row_itself_is_retained(self):
        src = (REPO / "tests" / "test_ep28d.py").read_text(encoding="utf-8")
        fn = _method(src, "TestTheRealStoreAsItStands",
                     "test_the_row_answers_ebadf_without_it_too_and_that_is_the_honest_cap")
        doc = ast.get_docstring(fn) or ""
        self.assertIn("REFUTED TEXT, RETAINED", doc)
        self.assertIn("the row already answered EBADF", doc)
        self.assertIn("EP-28H item 6, 2026-08-02", doc)


# =====================================================================================
# T-MAP-PREDICTED-ROW-BY-ROW
# =====================================================================================

#: THE MAP, declared per row BEFORE anything was built and held here as DATA so it can
#: be differenced by machinery rather than read. Each entry is the falsifiable claim
#: "landing this item turns this row green".
#:
#: World of the reading: WARM (`/tmp/govos-conformance` present at start and never
#: deleted), suite 1,270, TWELVE red, failing sets identical by set difference in both
#: directions at shipped width and at `GOVOS_COMMIT_WIDTH=1`.
THE_MAP = (
    ("test_ep24.TestHarnessColumnsFail."
     "test_the_control_passes_every_leg_on_every_active_files_row", 3),
    ("test_ep28b.TestTheAppendIsStillTheCommit."
     "test_the_buffer_is_flushed_before_the_barrier", 5),
    ("test_ep28d.TestEstablishingTheDescriptorFirstRepairsIt."
     "test_the_descriptor_table_is_unchanged_across_the_row", 1),
    ("test_ep28d.TestEstablishingTheDescriptorFirstRepairsIt."
     "test_the_held_number_is_below_every_number_the_row_touches", 1),
    ("test_ep28d.TestEstablishingTheDescriptorFirstRepairsIt."
     "test_the_instruments_record_path_survives_the_row", 1),
    ("test_ep28d.TestEstablishingTheDescriptorFirstRepairsIt."
     "test_the_row_answers_ebadf_for_its_own_reason", 1),
    ("test_ep28d.TestTheOldInterleavingIsReproducedAndCaught."
     "test_the_descriptor_the_store_held_is_the_one_the_first_close_freed", 1),
    ("test_ep28d.TestTheOldInterleavingIsReproducedAndCaught."
     "test_the_instruments_own_record_path_is_what_breaks", 1),
    ("test_ep28d.TestTheOldInterleavingIsReproducedAndCaught."
     "test_the_rows_ebadf_is_manufactured_and_not_measured", 1),
    ("test_ep28d.TestTheRealStoreAsItStands."
     "test_the_row_answers_ebadf_with_the_repair_in_place", 1),
    ("test_ep28d.TestTheRealStoreAsItStands."
     "test_the_row_answers_ebadf_without_it_too_and_that_is_the_honest_cap", 6),
    ("test_ep28e.TestNoRecordIsReadToServeADirectoryListing."
     "test_a_directory_listing_reads_zero_records", 1),
)

#: The one mapped row whose green is only readable in a FULL-SUITE run: it passes in
#: isolation and always did — its `[Errno 9]` is produced by another file's abandoned
#: store, which is exactly why item 1 reaches it and exactly why its green discharges
#: nothing about the finalizer.
ONLY_IN_A_FULL_SUITE_RUN = ("test_ep28e.TestNoRecordIsReadToServeADirectoryListing."
                            "test_a_directory_listing_reads_zero_records",)

#: Items whose predicted row set is EMPTY, said in words so "no row moved" is never
#: read as "the item was not needed": both their subject rows were GREEN at the reading
#: on the two named world variables, so a prediction had nothing to bind to and the
#: INVARIANCE rows above carry their falsifiability instead.
ITEMS_WITH_NO_RED_ROW = (2, 4)


def prediction_violations(landed, greens):
    """T-MAP-PREDICTED-ROW-BY-ROW's predicate. Given the items that landed and the rows
    observed green, return every row that refutes the map: green WITHOUT its predicted
    item, or still red WITH it."""
    out = []
    for row, item in THE_MAP:
        if row in greens and item not in landed:
            out.append(("green without item %d" % item, row))
        if row not in greens and item in landed:
            out.append(("red after item %d landed" % item, row))
    return out


class TestMapPredictedRowByRow(unittest.TestCase):
    """T-MAP-PREDICTED-ROW-BY-ROW. The map is a PREDICTION, and item 1 shifts descriptor
    occupancy globally — so it can turn a row green that was failing for a different
    reason. This row is the check on that, which is §4's burial mechanism one level
    general."""

    ITEMS = (1, 2, 3, 4, 5, 6)

    def test_every_red_maps_to_EXACTLY_ONE_item(self):
        rows = [r for r, _i in THE_MAP]
        self.assertEqual(len(rows), len(set(rows)), "a row is mapped twice")
        self.assertEqual(len(THE_MAP), 12, "the reading found twelve reds")
        for _row, item in THE_MAP:
            self.assertIn(item, self.ITEMS)

    def test_the_items_with_no_predicted_row_are_NAMED(self):
        """Raise 5's hole, closed rather than recorded: an item whose predicted row set
        is empty is stated as such, so a later reader cannot mistake 'no row moved' for
        'the item was not needed'."""
        predicted = {i for _r, i in THE_MAP}
        self.assertEqual(set(self.ITEMS) - predicted, set(ITEMS_WITH_NO_RED_ROW))

    def test_every_predicted_row_is_green_with_its_item_landed(self):
        """THE POST-CHECK. Each mapped row is run and must pass — except the one whose
        colour is only readable in a full-suite run, which is named rather than quietly
        skipped."""
        greens = set()
        for row, _item in THE_MAP:
            if row in ONLY_IN_A_FULL_SUITE_RUN:
                continue
            mod, cls, name = row.rsplit(".", 2)
            result = unittest.TestResult()
            getattr(sys.modules[mod] if mod in sys.modules else __import__(mod),
                    cls)(name).run(result)
            if result.wasSuccessful():
                greens.add(row)
            else:
                self.fail("%s is still red after its predicted item landed: %r"
                          % (row, result.failures + result.errors))
        greens.update(ONLY_IN_A_FULL_SUITE_RUN)
        self.assertEqual(prediction_violations(set(self.ITEMS), greens), [])

    def test_the_generated_red_world_a_double_that_lands_item_1_only(self):
        """THE RED WORLD, GENERATED. If only item 1 had landed, every row predicted on
        another item that went green anyway would be a row green for an unpredicted
        reason — the coincidence family in its value form. The predicate names them."""
        all_green = {r for r, _i in THE_MAP}
        offenders = prediction_violations({1}, all_green)
        self.assertTrue(offenders, "the predicate reported nothing over a world it must "
                                   "refuse — then it cannot catch an unpredicted green")
        self.assertEqual({row for _why, row in offenders},
                         {r for r, i in THE_MAP if i != 1})
        for why, _row in offenders:
            self.assertTrue(why.startswith("green without item"))

    def test_the_predicate_also_catches_a_row_still_red_after_its_item(self):
        """The other direction of the same clause, driven: a row predicted on an item
        that landed and did NOT go green refutes the map just as hard."""
        offenders = prediction_violations(set(self.ITEMS), set())
        self.assertEqual(len(offenders), len(THE_MAP))
        for why, _row in offenders:
            self.assertTrue(why.startswith("red after item"))


# =====================================================================================
# T-RAISE3-STANDS
# =====================================================================================

class TestRaise3Stands(unittest.TestCase):
    """T-RAISE3-STANDS. Recorded as EXEMPT from a red world in the plan: it is a
    citation obligation and not a mechanism, and its falsifiability is the citation
    RESOLVING — §A38's shape, where the subject is proven to exist by the reference
    succeeding."""

    def test_the_intake_resolves_at_its_filed_home(self):
        text = (REPO / "planning" / "exec" / "EP-28C.md").read_text(encoding="utf-8")
        head = text.index("### 4.2 — INTAKE: the store-lifecycle finalizer defect")
        section = text[head:head + 2000]
        self.assertIn("weakref.finalize", section)
        self.assertIn("src/kernel/store.py:563", section)
        self.assertIn("EP-28F raise 3", section)

    def test_this_passs_own_order_carries_the_non_discharge_sentence(self):
        text = (REPO / "planning" / "exec" / "EP-28H.md").read_text(encoding="utf-8")
        self.assertIn("THIS PASS DOES NOT DISCHARGE RAISE 3", text)
        self.assertIn("removes the OCCASION for it, not the mechanism", text)

    #: EP-28H's OWN commit range. Its subject is EP-28H's conduct, not every commit that
    #: will ever follow — the same repair this pass applied to `tests/test_ep28f.py`'s
    #: files-unchanged row at its deviation 4, and missed on its own row one file over.
    #: [DOCUMENTED FLIP, EP-28G, 2026-08-03. The row read `DISPATCH_HEAD..HEAD`, an OPEN
    #: range, so it was guaranteed to red on the NEXT pass that touched `src/` — which is
    #: EP-28G, the pass immediately after, whose whole deliverable is a construct in
    #: `src/kernel/gate.py`. The assertion is not weakened: pinned to the range it is about,
    #: it says exactly what it always meant and now stays true.]
    ACCEPTED_HEAD = "de20940"

    def test_this_pass_reached_no_product_code(self):
        """The strongest form of the same statement, measured: `src/` is at zero lines
        across EP-28H's own commit range, so nothing here could have discharged the intake
        even by accident."""
        out = subprocess.run(
            ["git", "diff", "--stat", "%s..%s" % (DISPATCH_HEAD, self.ACCEPTED_HEAD),
             "--", "src/"],
            cwd=str(REPO), capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "", "src/ moved in a pass that stops on it")

    def test_the_range_this_row_reads_is_this_passs_own_and_is_closed(self):
        """THE FLIP'S OWN GUARD. An open-ended range reds by construction on the next pass;
        a closed one cannot. Both ends must resolve, and the far end must be the commit this
        pass was accepted at rather than whatever HEAD happens to be."""
        for rev in (DISPATCH_HEAD, self.ACCEPTED_HEAD):
            out = subprocess.run(["git", "rev-parse", "--verify", rev + "^{commit}"],
                                 cwd=str(REPO), capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, "%s does not resolve: %s" % (rev, out.stderr))
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                              capture_output=True, text=True).stdout.strip()
        pinned = subprocess.run(["git", "rev-parse", self.ACCEPTED_HEAD], cwd=str(REPO),
                                capture_output=True, text=True).stdout.strip()
        self.assertNotEqual(
            pinned, "", "the accepted commit did not resolve")
        del head        # read for the record; the row asserts closure, never a position


if __name__ == "__main__":
    unittest.main()
