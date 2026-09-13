# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28E W5 — `nlink` made to cost its answer, with the reference arm built FIRST.

WHY THE ORDER IS THE POINT AND NOT A PREFERENCE. EP-28E ADDENDUM 2 §2.3 stopped `nlink`
landing on W2's differential, because that differential calls the SAME `state.nlink` on both
of its arms for files and hardcodes the SAME scan on both for directories — only `resolve`
varies, which is `path_of`. So it proves `path_of`'s change did not disturb `nlink`, and it
cannot prove that a replacement `nlink` answers what the scan answered. `_scanning_children`
and `_scanning_path_of` exist as reference arms; `_scanning_nlink` did not. Landing the
change on that differential would have shipped a proof that looks present and is absent —
`design/36` ADDENDUM R's root, in a test's own reference arm.

WHAT IS COMPARED, and it is deliberately narrow. `_scanning_nlink` below is the shipped body
as it stood before W5, INCLUDING its call to the indexed `path_of`. So this differential
isolates exactly the two namespace scans W5 replaces and does not re-open W2's tie-break,
which ADDENDUM 2 §2.4 has already ruled on.

THE ASYMMETRY THE PLAN NAMED RATHER THAN LEFT TO BE DISCOVERED. `kids` holds BASENAMES, not
kinds. So the link count is a lookup — `len(paths[ino])` — but the subdirectory count is a
JOIN per entry back through `names` and `inodes`. It is bounded by that one directory's
entries, so it satisfies the ruled predicate; it is a join rather than a lookup, and this
file says so instead of letting the countable imply otherwise.

THE CALLERS ARE ENUMERATED FROM THE SOURCE, NEVER LISTED. `MEASUREMENTS` entry 11c says
`nlink` "is called from exactly one site in the estate". It is called from TWO —
`records_fs.py` (stance 3's `getattr`) and `replay_snapshot.py` (the conformance harness's
REPLAY leg). That claim is corrected in this EP's ledger entry rather than edited where it
stands, and the correction is mechanised below: the covered-caller set is required to equal
the call sites read out of `src/`, so the next caller cannot be added without this
differential noticing.
"""

import ast
import errno
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
#: This file REUSES the arms and the reference implementations its two predecessors already
#: built, rather than growing a third copy of them — the same rule that keeps one fold body
#: in `src/`. Discovery puts `tests/` on the path; an explicit run of one module does not, so
#: it is added here and the two imports below work either way.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bridge import custody                        # noqa: E402
from bridge import replay_snapshot                 # noqa: E402
from bridge.mount import build_brain               # noqa: E402
from bridge.records_fs import RecordsFS            # noqa: E402

import test_ep28e_w3                               # noqa: E402
from test_ep28e_w2 import _mutation_walk           # noqa: E402
from test_ep28e_w3 import (                        # noqa: E402
    COST_IS_ITS_DEPENDENCY, UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION,
    LARGE_NAMELESS, LARGE_NAMES, PROBE_DIR_INO, SMALL_NAMELESS, SMALL_NAMES,
    _arm, _work,
)


def _guard(name="test_every_read_costs_only_what_its_answer_depends_on"):
    """W3's guard, reached THROUGH ITS MODULE at CALL TIME and never bound at module level.

    THE SHAPE IS FORCED AND IT COST TWO GOES TO GET RIGHT. unittest collects any `TestCase`
    SUBCLASS THAT IS AN ATTRIBUTE OF THE MODULE, so `from test_ep28e_w3 import
    TestTheDependencyGuard` re-runs W3's nine guard rows inside this file — and so does
    `_GUARD = test_ep28e_w3.TestTheDependencyGuard`, which is what the first fix did. Both
    inflate the suite by a DUPLICATION reported as tests, and the arithmetic reconciliation
    the campaign relies on then balances on a count that is nine too high.

    Caught by the arithmetic, not by reading the code: 1193 + 18 predicted, 1220 observed.
    That is charter §A30's own detector working in the other direction — a number that did
    NOT read cleanly."""
    return test_ep28e_w3.TestTheDependencyGuard(name)


# =====================================================================================
# W5a — THE REFERENCE ARM
# =====================================================================================
def _scanning_nlink(state, ino):
    """`CustodyState.nlink` as it stood before EP-28E W5, verbatim in behaviour.

    Two namespace walks: one summing every binding for the link count, and on a directory a
    second one filtering every name by parent. Its answer depends on the one inode's
    bindings and, on a directory, the one directory's entries."""
    node = state.inodes.get(ino)
    n = sum(1 for i in state.names.values() if i == ino)
    if node is not None and node.kind == custody.KIND_DIR:
        path = state.path_of(ino)
        subdirs = sum(1 for c, i in state.names.items()
                      if custody.parent_of(c) == path and
                      state.inodes.get(i) is not None and
                      state.inodes[i].kind == custody.KIND_DIR)
        return 2 + subdirs
    return n


class _ScanningNlink:
    """Reinstate the scanning `nlink` on the real class, for a differential arm or a red
    world. A context manager rather than a helper call, because a red world that leaks its
    monkeypatch into the next row turns a green suite into a meaningless one."""

    def __enter__(self):
        self._real = custody.CustodyState.nlink
        custody.CustodyState.nlink = lambda self_, ino: _scanning_nlink(self_, ino)
        return self

    def __exit__(self, *exc):
        custody.CustodyState.nlink = self._real
        return False


# =====================================================================================
# THE CALLERS — read out of `src/`, never listed
# =====================================================================================
def _nlink_call_sites():
    """Every call to `nlink` in `src/`, taken from the syntax tree of each shipped module.

    Established from the thing itself (`design/36` ADDENDUM R): a grep for the word would
    also match the docstrings that discuss it, and a hand-list would be the defect this EP
    spent its session fixing."""
    out = []
    for path in sorted((REPO / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "nlink":
                out.append("%s:%d" % (path.relative_to(REPO).as_posix(), node.lineno))
    return sorted(out)


#: Which differential covers which call site. The KEY is a module, not a line, because a line
#: number moves when anything above it is edited and a test that fails on an edit teaches
#: people to stop reading it.
COVERED_CALLERS = {
    "src/bridge/records_fs.py":
        "stance 3's `getattr` — `st_nlink` on every stat, covered by "
        "TestTheCallersServeTheSameAnswer.test_stance_3_getattr",
    "src/bridge/replay_snapshot.py":
        "the conformance harness's REPLAY leg — `nlink` per node of the replayed tree, "
        "covered by TestTheCallersServeTheSameAnswer.test_the_replay_leg",
}


class TestEveryCallerIsCovered(unittest.TestCase):

    def test_the_covered_callers_are_the_callers_the_source_has(self):
        """T-W5-CALLERS-READ-NOT-LISTED. `MEASUREMENTS` entry 11c named one caller and there
        are two. This row makes that class of miss fail rather than be noticed."""
        found = sorted({site.rsplit(":", 1)[0] for site in _nlink_call_sites()})
        self.assertEqual(found, sorted(COVERED_CALLERS),
                         "the modules that call `nlink` and the modules this file's caller "
                         "differential covers have drifted apart: source has %r, covered %r"
                         % (found, sorted(COVERED_CALLERS)))

    def test_the_reader_can_find_a_call_site(self):
        """The row above is an equality between two sets and would also hold if the reader
        found nothing and the table were empty. It is required to find the sites it does."""
        sites = _nlink_call_sites()
        self.assertGreaterEqual(len(sites), 2, "the call-site reader found %r" % (sites,))
        self.assertTrue(any(s.startswith("src/bridge/replay_snapshot.py") for s in sites),
                        "the replay leg's call was not found by the reader: %r" % (sites,))


# =====================================================================================
# W5b — THE DIFFERENTIAL: the indexed read against the scan it replaced
# =====================================================================================
class TestTheIndexedNlinkAnswersWhatTheScanAnswered(unittest.TestCase):

    def test_the_differential_over_a_mutation_walk(self):
        """T-W5-DIFFERENTIAL. Every inode in the world, after every seventeenth record of a
        walk that exercises every action which binds or unbinds a name.

        THE ONE DIVERGENCE, NAMED HERE BECAUSE IT IS REAL AND WAS FOUND BY THIS ROW RATHER
        THAN REASONED ABOUT. An UNBOUND directory inode — one whose name a `FILE-RMDIR`
        removed, leaving the `Inode` object in `inodes` with no name at all — is answered 3
        by the scan and 2 by the replacement. The scan's 3 is an artefact of two `None`s
        meeting: `path_of` returns None for an unbound inode, and `parent_of('/')` is also
        None, so the filter `parent_of(c) == path` matches the ROOT and counts it as a
        subdirectory of a directory that is not there. The replacement asks `kids[None]`,
        finds nothing, and answers 2.

        NEITHER NUMBER IS SERVED TO ANYBODY, and that is asserted at both callers below
        rather than claimed here — the W2 lesson, where an unreachability claim built from
        reading one branch was refuted by this file's own kind of differential."""
        recs = _mutation_walk()
        state = custody.CustodyState()
        compared, unbound_dirs = 0, 0
        for n, e in enumerate(recs):
            state.apply(e)
            if n % 17 and n != len(recs) - 1:
                continue
            bound = set(state.names.values())
            for ino in list(state.inodes) + [max(state.inodes) + 5000]:
                node = state.inodes.get(ino)
                if node is not None and node.kind == custody.KIND_DIR and ino not in bound:
                    unbound_dirs += 1
                    continue                      # the named divergence, asserted below
                self.assertEqual(state.nlink(ino), _scanning_nlink(state, ino),
                                 "nlink diverged at record %d for inode %r (kind %r)"
                                 % (n, ino, getattr(node, "kind", None)))
                compared += 1
        self.assertGreater(compared, 2000,
                           "the walk compared only %d answers, which is not a differential"
                           % compared)
        self.assertGreater(unbound_dirs, 0,
                           "the walk produced no unbound directory inode, so the exclusion "
                           "above is untested and may be hiding an ordinary divergence")

    def test_the_named_divergence_is_exactly_the_two_nones_meeting(self):
        """The exclusion above is a hole in a differential, so it is closed by a row that
        states the divergence exactly instead of waving at it: 3 against 2, on an unbound
        directory inode, and 3 only because the ROOT satisfied the scan's filter."""
        state = custody.fold([
            {"action": "FILE-MKDIR", "record_time": 1.0,
             "payload": {"path": "/d", "inode": 2, "perm": "755"}},
            {"action": "FILE-RMDIR", "record_time": 1.0, "payload": {"path": "/d"}},
        ])
        self.assertIsNone(state.path_of(2), "inode 2 is still bound, so this is not the case")
        self.assertEqual(_scanning_nlink(state, 2), 3)
        self.assertEqual(state.nlink(2), 2)
        # AND THE 3 IS THE ROOT BEING COUNTED. Remove the root's own name and the scan's
        # answer collapses to 2, which is the whole of the artefact stated as a measurement.
        state.names.pop("/")
        self.assertEqual(_scanning_nlink(state, 2), 2,
                         "the scan's extra link was not the root after all, so the "
                         "explanation above is wrong and the divergence needs re-deriving")

    def test_the_differential_can_fail(self):
        """T-W5-DIFFERENTIAL-CAN-FAIL. The row above is an equality between two functions and
        would hold if both were broken the same way. One binding is dropped from `paths`
        behind the fold's back and the differential is required to catch it."""
        state = custody.fold(_mutation_walk(steps=60))
        victim = next(i for i in state.paths if state.inodes.get(i) is not None
                      and state.inodes[i].kind != custody.KIND_DIR)
        state.paths.pop(victim)
        self.assertNotEqual(state.nlink(victim), _scanning_nlink(state, victim),
                            "a binding removed from the index did not change what the "
                            "indexed read answered, so the differential proves nothing")


class TestTheCallersServeTheSameAnswer(unittest.TestCase):
    """The change is proven where it is SERVED, not only where it is computed — and the
    divergence excluded above is proven unreachable at each caller rather than argued."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="ep28e-w5-")
        self.addCleanup(shutil.rmtree, self.work, True)
        os.makedirs(os.path.join(self.work, "blobs"), exist_ok=True)
        self.rec = os.path.join(self.work, "rec.jsonl")
        open(self.rec, "w").close()
        self.blobs_dir = os.path.join(self.work, "blobs")

    def _fs(self):
        store, gate, views, blobs = build_brain(self.rec, self.blobs_dir)
        return RecordsFS(store, gate, views, blobs)

    def _tree(self, fs):
        """A world with the shapes `nlink` actually distinguishes: nested directories, a
        hard-linked file, and a directory whose subdirectory is then removed."""
        fs.mkdir("/d", 0o755)
        fs.mkdir("/d/sub", 0o755)
        fs.mkdir("/d/gone", 0o755)
        fs.create("/d/a", 0o644)
        fs.link("/d/b", "/d/a")
        fs.rmdir("/d/gone")

    def test_stance_3_getattr(self):
        """T-W5-STANCE-3-UNDISTURBED. `st_nlink` for every path in the world, under the
        replacement and under the reinstated scan."""
        fs = self._fs()
        self._tree(fs)
        paths = sorted(fs.state.names)
        served = {p: fs.getattr(p)["st_nlink"] for p in paths}
        with _ScanningNlink():
            scanned = {p: fs.getattr(p)["st_nlink"] for p in paths}
        self.assertEqual(served, scanned,
                         "stance 3 serves a different link count after the change")
        # AND THE ANSWERS ARE THE POSIX ONES, so the equality is not two wrongs agreeing.
        self.assertEqual(served["/d"], 3, "a directory holding one subdirectory is 2 + 1")
        self.assertEqual(served["/d/sub"], 2)
        self.assertEqual(served["/d/a"], 2, "a file with two names has two links")
        self.assertEqual(served["/d/b"], 2)

    def test_stance_3_cannot_reach_an_unbound_directory_inode(self):
        """The excluded divergence, closed at this caller by DRIVING it rather than by
        reading one branch. `getattr` reaches an inode two ways — a path, and an open
        descriptor — and both are tried."""
        fs = self._fs()
        fs.mkdir("/d", 0o755)
        gone_ino = fs.state.names["/d"]
        fs.rmdir("/d")
        self.assertIn(gone_ino, fs.state.inodes,
                      "the fold dropped the inode too, so there is no unbound directory "
                      "inode here and this row is testing nothing")
        self.assertIsNone(fs.state.path_of(gone_ino))
        # 1. BY PATH — the name is gone, so the lookup never reaches the inode.
        with self.assertRaises(Exception) as caught:
            fs.getattr("/d")
        self.assertEqual(getattr(caught.exception, "errno", None), errno.ENOENT)
        # 2. BY DESCRIPTOR — a descriptor is only ever minted for a FILE, so no fh can name
        #    a directory inode. Read from the fold rather than asserted: every open
        #    descriptor's inode is a non-directory.
        fs.create("/f", 0o644)
        fh = fs.open("/f", os.O_RDONLY)
        kinds = {fs.state.inodes[o["ino"]].kind for o in fs._open.values()}
        self.assertEqual(kinds, {custody.KIND_FILE},
                         "an open descriptor names something other than a file, so the "
                         "unbound-directory case could reach `getattr` through `fh`")
        fs.release("/f", fh)

    def test_the_replay_leg(self):
        """T-W5-REPLAY-LEG-UNDISTURBED. The conformance harness's check-3 leg replays the
        record and reports `nlink` per node. Driven through the REAL gated port so the
        record it folds is a record the gate wrote."""
        fs = self._fs()
        self._tree(fs)
        replayed = replay_snapshot.snapshot(self.rec, self.blobs_dir, root="/")
        with _ScanningNlink():
            scanned = replay_snapshot.snapshot(self.rec, self.blobs_dir, root="/")
        self.assertEqual(replayed, scanned,
                         "the replay leg reports a different tree after the change")
        self.assertEqual({k: v["nlink"] for k, v in sorted(replayed.items())},
                         {"d": 3, "d/sub": 2, "d/a": 2, "d/b": 2})

    def test_the_replay_leg_only_ever_asks_about_a_bound_inode(self):
        """The excluded divergence, closed at this caller. The leg iterates `state.names`, so
        every inode it hands `nlink` is one a name is bound to. Established by watching the
        real call rather than by reading the loop."""
        fs = self._fs()
        self._tree(fs)
        fs.mkdir("/orphan", 0o755)
        fs.rmdir("/orphan")
        asked = []
        real = custody.CustodyState.nlink

        def watched(self_, ino):
            asked.append((ino, ino in set(self_.names.values())))
            return real(self_, ino)

        custody.CustodyState.nlink = watched
        try:
            replay_snapshot.snapshot(self.rec, self.blobs_dir, root="/")
        finally:
            custody.CustodyState.nlink = real
        self.assertTrue(asked, "the replay leg asked about no inode at all")
        unbound = [ino for ino, bound in asked if not bound]
        self.assertEqual(unbound, [],
                         "the replay leg asked `nlink` about an unbound inode: %r" % unbound)


# =====================================================================================
# W5b — THE COUNTABLE, and the RED WORLD it is proven against
# =====================================================================================
class TestNlinkCostsItsOwnDependencies(unittest.TestCase):

    def test_the_countable_is_the_directory_s_own_entries(self):
        """T-W5-COUNTABLE. A directory holding one entry examines its one entry (plus the one
        binding `path_of` resolves). Stated as a countable, so the property survives a faster
        machine, and checked in the direction that matters too: a wider directory costs more.
        """
        state, counter, _ = _arm(LARGE_NAMES, LARGE_NAMELESS)
        steps, answer = _work(counter, lambda: state.nlink(PROBE_DIR_INO))
        self.assertEqual(answer, 2, "/probe holds one FILE, so it is 2 + 0 subdirectories")
        self.assertEqual(steps, 2,
                         "nlink examined %d entries to answer about a one-entry directory in "
                         "a %d-name namespace" % (steps, len(state.names)))
        wide, wcount, _ = _arm(SMALL_NAMES, SMALL_NAMELESS)
        entries = len(wide.children("/d0"))
        steps_wide, _ = _work(wcount, lambda: wide.nlink(wide.names["/d0"]))
        self.assertEqual(steps_wide, entries + 1,
                         "the countable does not move with the directory's own entries, so "
                         "it is measuring nothing")
        self.assertGreater(entries, 1)

    def test_a_files_link_count_is_a_lookup_and_not_a_join(self):
        """The asymmetry stated in this file's header, asserted rather than described: the
        link count costs NOTHING to look up, and only the subdirectory count is a join."""
        state, counter, _ = _arm(LARGE_NAMES, LARGE_NAMELESS)
        steps, answer = _work(counter, lambda: state.nlink(state.names["/probe/only"]))
        self.assertEqual(answer, 1)
        self.assertEqual(steps, 0, "a file's link count walked %d entries" % steps)

    def test_the_red_world_the_countable_is_proven_against(self):
        """T-W5-COUNTABLE-CAN-FAIL. The rows above assert small numbers, and a small number
        is what an instrument that stopped counting also reports. The scan is reinstated in
        the same arms in the same run and both arms are required to go red — with the LARGE
        arm's cost required to track the namespace, which is the defect returning."""
        small, csmall, _ = _arm(SMALL_NAMES, SMALL_NAMELESS)
        large, clarge, _ = _arm(LARGE_NAMES, LARGE_NAMELESS)
        fixed = {"small": _work(csmall, lambda: small.nlink(PROBE_DIR_INO))[0],
                 "large": _work(clarge, lambda: large.nlink(PROBE_DIR_INO))[0]}
        with _ScanningNlink():
            red = {"small": _work(csmall, lambda: small.nlink(PROBE_DIR_INO))[0],
                   "large": _work(clarge, lambda: large.nlink(PROBE_DIR_INO))[0]}
        self.assertEqual(fixed["small"], fixed["large"],
                         "the fixed read already differs across the arms: %r" % fixed)
        self.assertGreater(red["large"], 20 * red["small"],
                           "reinstating the scan did not make the large arm cost more, so "
                           "the countable above is vacuous: %r" % red)
        self.assertGreaterEqual(red["large"], len(large.names),
                                "the reinstated scan did not walk the namespace")


class TestTheW3GuardRowMoved(unittest.TestCase):
    """W5c. The row MOVES rather than being struck: `_rows` asserts declared-equals-probed and
    `test_the_declarations_are_disjoint_and_total` requires exact coverage, so a deletion
    fails the drift check. Its new home is `COST_IS_ITS_DEPENDENCY`, with its dependency
    stated."""

    def test_nlink_is_declared_as_costing_its_dependency(self):
        self.assertIn("nlink", COST_IS_ITS_DEPENDENCY)
        self.assertNotIn("nlink", UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION)

    def test_the_defect_ledger_is_now_empty_and_that_is_checked_not_assumed(self):
        """THE VACUITY THIS CREATES, CLOSED IN THE SAME STEP. `test_no_stale_declaration`
        iterates the defect ledger, and an EMPTY ledger makes it pass by iterating nothing —
        a green that means "nobody looked". So the ledger's emptiness is asserted as a
        finding, and the guard's other half is required to still catch an undeclared
        unbounded read."""
        self.assertEqual(UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION, {},
                         "the defect ledger is not empty, so this row's premise is wrong")
        guard = _guard()
        with _ScanningNlink():
            a, b = _arm(SMALL_NAMES, SMALL_NAMELESS), _arm(LARGE_NAMES, LARGE_NAMELESS)
            rows = guard._rows(a, b)
            (work_a, ans_a), (work_b, ans_b) = rows["nlink"]
        self.assertEqual(ans_a, ans_b, "the arms answered different questions")
        self.assertGreater(work_b, work_a,
                           "the reinstated scan is not unbounded in the namespace, so the "
                           "'declared or the guard fails' half has nothing to catch")
        self.assertNotIn("nlink", UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION,
                         "an undeclared unbounded read would now be silently permitted")

    def test_the_guard_trips_when_the_scan_is_reinstated(self):
        """T-W5-GUARD-CATCHES-THE-REGRESSION. The row's new home is only worth having if the
        guard fails when the read stops honouring it."""
        guard = _guard()
        with _ScanningNlink():
            found = guard._violations(_arm(SMALL_NAMES, SMALL_NAMELESS),
                                      _arm(LARGE_NAMES, LARGE_NAMELESS))
        self.assertEqual([name for name, _ in found], ["nlink"],
                         "the guard did not name `nlink` when its scan was reinstated, or "
                         "named something else: %r" % (found,))
        self.assertIn("does not depend on", found[0][1])


# =====================================================================================
# W5d — the §2.2 read, and the forward guard that makes the class unrepeatable
# =====================================================================================
class TestTheShadowDiffSubjectIsRead(unittest.TestCase):
    """W5d asked a question about HISTORY — was `shadow_diff`'s hand-list complete against
    the pre-W2 snapshot — and the answer is in this EP's log entry, because a fact about
    what a commit contained is not a property code can hold.

    WHAT CODE CAN HOLD IS THE FORWARD HALF, and that is what this class asserts: the
    comparison's subject is READ off the snapshot, so the list cannot go stale again.
    `test_ep28e_w2.py` proves the behaviour (an unlisted key IS reported); this proves the
    SHAPE, because a future edit could restore the behaviour's opposite while every existing
    row stayed green on the keys that happen to exist today."""

    def test_shadow_diff_names_no_snapshot_key(self):
        """T-W5-NO-HAND-LIST. The four snapshot keys are named in `custody.py`, where they
        are defined. None of them may be named inside `shadow_diff`, where they would be a
        list of what someone believes the snapshot holds."""
        src = (REPO / "src" / "bridge" / "records_fs.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "shadow_diff")
        strings = {n.value for n in ast.walk(fn)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        keys = set(custody.CustodyState().snapshot())
        named = sorted(strings & keys)
        self.assertEqual(named, [],
                         "shadow_diff names snapshot keys %r — the subject of the comparison "
                         "is a hand-list again" % named)

    def test_the_reader_would_see_a_hand_list_if_there_were_one(self):
        """The row above is an ABSENCE. It is proven able to report a presence."""
        planted = "def shadow_diff(self):\n    for key in ('names', 'inodes'):\n        pass\n"
        fn = next(n for n in ast.walk(ast.parse(planted))
                  if isinstance(n, ast.FunctionDef))
        strings = {n.value for n in ast.walk(fn)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        self.assertTrue(strings & set(custody.CustodyState().snapshot()),
                        "the reader cannot see a hand-list even when handed one")

    def test_a_divergence_in_a_key_nobody_listed_still_halts(self):
        """The consequence, end to end and through the real mount object: the hazard §2.2 is
        about is a divergence DETECTED and NOT REPORTED, so `if diff:` does not halt."""
        work = tempfile.mkdtemp(prefix="ep28e-w5-fs-")
        self.addCleanup(shutil.rmtree, work, True)
        os.makedirs(os.path.join(work, "blobs"), exist_ok=True)
        rec = os.path.join(work, "rec.jsonl")
        open(rec, "w").close()
        store, gate, views, blobs = build_brain(rec, os.path.join(work, "blobs"))
        fs = RecordsFS(store, gate, views, blobs)
        fs.mkdir("/d", 0o755)
        fs.create("/d/a", 0o644)
        fs.state.paths.pop(fs.state.names["/d/a"])
        diff = fs.shadow_diff()
        self.assertTrue(diff, "a divergence in `paths` produced no reported difference")
        fs._acts, fs.shadow_every = 0, 1
        fs._shadow_check()
        self.assertTrue(fs.halted, "the divergence did not halt the mount")


if __name__ == "__main__":
    unittest.main()
