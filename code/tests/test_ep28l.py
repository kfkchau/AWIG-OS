# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28L — the baseline load proves its subject non-empty, and a zero-file
capture stops before writing.

The two ends of one clause, and the second is the load-bearing one.

  LOAD    a manifest whose `files` map is empty REFUSES, citing the clause. The
          load never succeeds vacuously, so no verify downstream can green over
          a baseline with no rows.

  CAPTURE a capture that would write zero files STOPS BEFORE WRITING. It does
          not create the artifact whose load would now refuse, because under
          `base=None` — which resolves to the PINNED directory — an artifact
          that exists-but-refuses has ALREADY cost the pin its content. §A53
          closes the undo window in about two minutes and nothing announces a
          problem. Only the pre-write stop keeps that window open.

§A38 at the ARTIFACT layer, third instance of one mechanism: a check whose pass
condition is the absence of output cannot tell "nothing changed" from "nothing
was looked at", so its SUBJECT is proven non-empty before the pass counts. The
founding block's `ls-files >= 1` is the first; T-MINT-SET-ENUMERATED's
population clause is the second; the manifest's `files` map is this one.

WORLD (§A39), and the variable each row depends on, named rather than proxied.

  * The baseline bases are `TemporaryDirectory`s this file CREATES, populated by
    copying the committed `host-local` capture where a pin must stand. No row
    writes to a committed directory.
  * The three rows that drive `runner.capture` INHERIT one condition they do not
    create: `/tmp/govos-conformance/host-local` must be absent or empty, because
    `establish_scratch` refuses a dirty scratch by design (§11.2b's second half).
    The harness creates and tears that directory down inside each call, so the
    rows leave it as they found it — but a previous crashed run that left files
    there reds them with a `SubjectError`, which is a fact about the box and not
    about the clause. Declared, not assumed away.
  * The rows that address a COMMITTED directory are the two in
    `TestPinnedBaseUnreachedOnStop` that pass `base=None`. Each checks the
    guard's POSITION in the source before making the call, because the call is
    only safe if the guard is where the check says it is.

RED WORLDS (§A42) are generated THROUGH the instrument and never against
anything committed: the guard is removed from a COPY of `baselines.py` by AST
surgery, the copy is executed, and the pre-fix behaviour is driven through the
real functions against the scratch base. That is the same code path the true
positive runs, which is what makes it an exhibition rather than a resemblance.
"""

import ast
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from tools.conformance.harness import baselines, checks, runner  # noqa: E402

BASELINES_SRC = Path(baselines.__file__).resolve()
RUNNER_SRC = Path(runner.__file__).resolve()
PINNED_DIR = baselines.BASELINES_DIR
HOST = "host-local"
GUEST = "ep21-ubuntu-guest"

#: The one-character mistake this whole pass exists to make survivable. The
#: group is `06-files`; the mentor's capture of 2026-08-04 said `files`.
MISTYPED_GROUP = "files"


# ---------------------------------------------------------------------------
# neutering: the red worlds, generated through the instrument
# ---------------------------------------------------------------------------


def _source_without_guard(func_name, guard_test, src=None):
    """`baselines.py`'s source with ONE guard statement removed from ONE
    function, located STRUCTURALLY rather than by text match — so the neutering
    tracks the guard through any rewording of its message, and fails loudly if
    the guard is gone rather than silently exhibiting nothing.

    [DOCUMENTED FLIP, EP-28M] `src` lets cuts COMPOSE. It exists because
    reaching the pre-EP-28L world now takes two of them — see
    `_neutered_pre_EP28L` below."""
    src = BASELINES_SRC.read_text() if src is None else src
    lines = src.splitlines(keepends=True)
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            for stmt in node.body:
                if isinstance(stmt, ast.If) and ast.unparse(stmt.test) == guard_test:
                    return "".join(lines[: stmt.lineno - 1]) + "".join(lines[stmt.end_lineno :])
    raise AssertionError(
        "no guard `if %s:` in %s() — the clause under test is absent from the "
        "source, so there is nothing to neuter and nothing to exhibit"
        % (guard_test, func_name)
    )


def _neutered(func_name, guard_test):
    """Execute that source as a module. It is a copy: the committed file is
    read and never written."""
    mod = types.ModuleType("baselines_neutered_%s" % func_name)
    mod.__file__ = str(BASELINES_SRC)
    exec(compile(_source_without_guard(func_name, guard_test), str(BASELINES_SRC), "exec"),
         mod.__dict__)
    return mod


def _neutered_pre_EP28L():
    """The capture path as it stood BEFORE EP-28L — and reaching it now takes
    TWO cuts rather than one.

    [DOCUMENTED FLIP, EP-28M, mapped to that pass's DOOR 3 clause.] EP-28M
    added a SECOND stop to `write_capture`: a capture that would leave a file
    the artifact already holds unnamed by its new manifest STOPS. A zero-group
    capture is that case at its limit — it names nothing, so everything held is
    orphaned — which is exactly the consequence THIS FILE'S OWN RED-WORLD ROW
    named one pass before the clause existed ("it is ORPHANED, no longer named
    by any manifest").

    So the two guards overlap by derivation rather than by accident, and the
    single-cut world stopped being the pre-EP-28L world. What the first run
    after EP-28M's landing showed is worth keeping: with EP-28L's stop removed,
    EP-28M's stop caught the same call and THE PIN SURVIVED. That is defence in
    depth observed rather than asserted, and it is why this helper removes both
    rather than why EP-28M's clause was narrowed to avoid the overlap.
    """
    src = _source_without_guard("write_capture", "not group_files")
    src = _source_without_guard("write_capture", "orphans", src)
    mod = types.ModuleType("baselines_pre_ep28l")
    mod.__file__ = str(BASELINES_SRC)
    exec(compile(src, str(BASELINES_SRC), "exec"), mod.__dict__)
    return mod


def _sha_map(d):
    """name -> sha256 of bytes, for every file directly under `d`."""
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(Path(d).iterdir())
        if p.is_file()
    }


def _guard_is_live():
    """Does the LOADED `write_capture` actually stop on zero files, right now?

    The two rows below hand `base=None` to `write_capture`, which resolves to the
    COMMITTED pinned directory. That call is safe only while the stop is real, so
    it is proven real first — on a scratch directory, where being wrong costs
    nothing.

    It is a BEHAVIOURAL check and not a source reading, and the difference is the
    point: a source reading and the call it protects have DIFFERENT SUBJECTS the
    moment anything swaps the loaded module (this file's own neutering helper
    does exactly that, and a battery driven against a neutered module would sail
    past a source check straight into the pinned directory). The check and the
    dangerous act must address the same thing, which is §11.2b's own rule —
    establish the subject you are about to report on — pointed at this file.
    """
    with tempfile.TemporaryDirectory() as probe:
        try:
            baselines.write_capture(HOST, {"kind": "stock"}, {}, {}, None, {}, [], base=probe)
        except BaselineErrorClass:
            return not any(Path(probe).iterdir())
        return False


#: bound once at import so a swapped module cannot also swap the exception the
#: check above is looking for
BaselineErrorClass = baselines.BaselineError


def _plant_a_pin(base, name=HOST):
    """Put a REAL pinned baseline where a pin must stand, so what a stop
    protects — and what the pre-fix behaviour destroys — is a working artifact
    with rows in it, not an empty directory."""
    dst = Path(base) / name
    shutil.copytree(PINNED_DIR / name, dst)
    return dst


# ---------------------------------------------------------------------------
# T-LOAD-REFUSES-EMPTY
# ---------------------------------------------------------------------------


class TestLoadRefusesEmpty(unittest.TestCase):
    """A manifest with an empty `files` map refuses at load, citing the clause."""

    def _empty_manifest_at(self, base, name=HOST):
        """An empty-manifest double with the SHAPE the instrument itself
        produces: every other field present and well-formed, `files` empty. It
        is written from the committed manifest's own keys so the double cannot
        drift into being refused for some unrelated malformation."""
        real = json.loads((PINNED_DIR / name / baselines.MANIFEST_NAME).read_text())
        empty = copy.deepcopy(real)
        empty["files"] = {}
        d = Path(base) / name
        d.mkdir(parents=True)
        (d / baselines.MANIFEST_NAME).write_text(json.dumps(empty, indent=1, sort_keys=True) + "\n")
        return d

    def test_a_manifest_with_an_empty_files_map_refuses_at_load(self):
        with tempfile.TemporaryDirectory() as base:
            d = self._empty_manifest_at(base)
            before = (d / baselines.MANIFEST_NAME).read_bytes()
            with self.assertRaises(baselines.BaselineError) as ctx:
                baselines.load(HOST, base)
            msg = str(ctx.exception)
            self.assertIn("names NO files", msg)
            self.assertIn("empty", msg)
            #: The refusal REPAIRS NOTHING (P4). The bytes it refused are the
            #: bytes still on disk: a load that quietly rewrote what it would
            #: not accept would destroy the evidence of how it got that way.
            self.assertEqual((d / baselines.MANIFEST_NAME).read_bytes(), before)

    def test_the_refusal_cites_the_clause_rather_than_only_the_condition(self):
        with tempfile.TemporaryDirectory() as base:
            self._empty_manifest_at(base)
            with self.assertRaises(baselines.BaselineError) as ctx:
                baselines.load(HOST, base)
            #: A refusal that states only "it is empty" tells the next seat what
            #: happened and not why it is fatal. The estate's rule is that a
            #: failed gate cites its rule.
            self.assertIn(baselines.NON_EMPTY_CLAUSE, str(ctx.exception))

    def test_the_empty_load_SUCCEEDS_when_the_clause_is_neutered(self):
        """THE RED WORLD for this clause, driven through the real load path.

        The same bytes that now refuse loaded cleanly before this pass: every
        sum passed, because there were no sums, and the caller got a baseline
        with zero rows and no indication of it."""
        with tempfile.TemporaryDirectory() as base:
            self._empty_manifest_at(base)
            pre_fix = _neutered("load", "not files")
            pinned = pre_fix.load(HOST, base)
            self.assertEqual(pinned.row_ids(), [])
            self.assertEqual(pinned.manifest["files"], {})
            #: and the fixed module refuses the IDENTICAL bytes
            with self.assertRaises(baselines.BaselineError):
                baselines.load(HOST, base)

    def test_the_zero_row_baseline_greens_every_abi_leg_it_is_asked_about(self):
        """WHY the vacuous load matters, exhibited through the real check.

        `check_abi` answers NOT-RUN for a row the baseline does not hold, and
        NOT-RUN is not FAIL, so a report over an empty baseline has nothing in
        `failed` and reports OK. The empty subject verifies perfectly.

        CAP, stated: this drives the ABI leg and the report's own OK rule, not a
        whole `verify` run — a full verify needs a governed target and a mount.
        What it establishes is that nothing between a zero-row baseline and the
        run's exit code turns the absence into a failure."""
        pre_fix = _neutered("load", "not files")
        with tempfile.TemporaryDirectory() as base:
            self._empty_manifest_at(base)
            pinned = pre_fix.load(HOST, base)

        row = _AbiRow()
        result = checks.check_abi(row, {"steps": []}, pinned.get("files.open"))
        self.assertEqual(result.verdict, checks.NOT_RUN)
        self.assertIn("no pinned baseline", result.reason)

        report = runner.Report(HOST, HOST, pinned, [checks.RowVerdict("files.open", [result])], [])
        self.assertEqual(report.failed, [])
        self.assertTrue(report.ok, "a report over a zero-row baseline reports OK")

    def test_the_committed_baselines_still_load(self):
        """The clause must not red the estate it protects. Both committed
        baselines carry a non-empty `files` map and load unchanged."""
        for name in (HOST, GUEST):
            pinned = baselines.load(name, None)
            self.assertTrue(pinned.manifest["files"], name)
            self.assertTrue(pinned.row_ids(), name)

    def test_verify_reads_the_baseline_before_it_touches_a_target(self):
        """"The verify downstream never runs" is a property of ORDER, and it is
        read from `verify`'s own body: `baselines.load` is its first statement,
        so a refusing load returns before a target is loaded, a subject is
        established, or a probe is driven."""
        src = RUNNER_SRC.read_text()
        fn = next(
            n for n in ast.parse(src).body
            if isinstance(n, ast.FunctionDef) and n.name == "verify"
        )
        body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        first = ast.unparse(body[0])
        self.assertIn("baselines.load", first)
        loaded_at = body[0].lineno
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                call = ast.unparse(node.func)
                if call in ("targets.Target.load", "target.establish_subject", "target.run_probes"):
                    self.assertGreater(
                        node.lineno, loaded_at,
                        "%s runs before the baseline is loaded" % call,
                    )


class _AbiRow:
    """The smallest thing `check_abi` needs: a row that HAS a probe. Standing in
    for a real assertion here is honest — the leg's branch under test is the
    `baseline is None` one, which is reached before anything reads the row."""

    has_probe = True
    probe_absent_reason = None
    row_id = "files.open"


# ---------------------------------------------------------------------------
# T-CAPTURE-STOPS-ON-ZERO
# ---------------------------------------------------------------------------


class TestCaptureStopsOnZero(unittest.TestCase):
    """A capture run that matches zero files STOPS before writing; the target
    artifact is byte-unchanged after the stop.

    WORLD (§A39): a scratch base holding a COPY of the committed `host-local`
    pin. The exhibition destroys that copy and never anything committed."""

    def test_a_mistyped_group_stops_the_capture_and_the_pin_survives(self):
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            before = _sha_map(d)
            self.assertGreater(len(before), 0, "non-vacuity: the pin holds files before the run")

            with self.assertRaises(baselines.BaselineError) as ctx:
                runner.capture(HOST, baselines_base=base, groups=[MISTYPED_GROUP])

            self.assertIn("ZERO groups", str(ctx.exception))
            self.assertEqual(_sha_map(d), before, "the pinned artifact moved across the stop")
            #: and it is still a WORKING pin, not merely unchanged bytes
            self.assertTrue(baselines.load(HOST, base).row_ids())

    def test_the_pre_fix_capture_DESTROYS_the_same_pin_on_the_same_base(self):
        """THE RED WORLD for this clause, and it is the whole reason the stop is
        placed before the write rather than after it.

        Same target, same one-character mistake, same scratch base, guard
        removed: the capture reports SUCCESS, and the pin's manifest is replaced
        by one whose `files` map is empty. The rows file is not deleted — it is
        ORPHANED, no longer named by any manifest, which is why nothing
        downstream notices."""
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            before = _sha_map(d)
            pre_fix = _neutered_pre_EP28L()

            #: the whole module is swapped in `runner`'s own namespace rather
            #: than an attribute being patched onto the real one, so the
            #: committed module is never mutated even transiently
            real_module = runner.baselines
            runner.baselines = pre_fix
            try:
                out_dir, manifest = runner.capture(
                    HOST, baselines_base=base, groups=[MISTYPED_GROUP]
                )
            finally:
                runner.baselines = real_module

            #: reported success
            self.assertEqual(Path(out_dir), d)
            self.assertEqual(manifest["files"], {})

            #: and the pin is gone
            after = _sha_map(d)
            self.assertNotEqual(after, before, "the pre-fix capture left the pin intact")
            on_disk = json.loads((d / baselines.MANIFEST_NAME).read_text())
            self.assertEqual(on_disk["files"], {})

            #: THE SECOND END CATCHES IT — and catching is not recovering. The
            #: load now refuses, which tells a reader the pin is gone; it does
            #: not give the pin back. That asymmetry is why the capture-side
            #: stop is the load-bearing half of this pass.
            with self.assertRaises(baselines.BaselineError):
                baselines.load(HOST, base)

    def test_the_stop_neither_recovers_nor_substitutes_a_default(self):
        """P4, the estate's own: the refusal beats the repair. Read from the
        guard's executable body — a guard that could fall back to a default base
        or retry with all groups would turn a caller's error into a silent
        re-capture of something nobody asked for."""
        src = BASELINES_SRC.read_text()
        fn = next(
            n for n in ast.parse(src).body
            if isinstance(n, ast.FunctionDef) and n.name == "write_capture"
        )
        guard = next(
            s for s in fn.body
            if isinstance(s, ast.If) and ast.unparse(s.test) == "not group_files"
        )
        #: one statement, and it RAISES. Not a warning, not a default, not a
        #: narrowed retry.
        self.assertEqual(len(guard.body), 1)
        self.assertIsInstance(guard.body[0], ast.Raise)
        self.assertIsNone(guard.orelse or None)
        for node in ast.walk(guard):
            self.assertNotIsInstance(
                node, (ast.Try, ast.For, ast.While, ast.Return, ast.Assign),
                "the stop contains recovery machinery: %s" % type(node).__name__,
            )

    def test_the_stop_names_what_the_caller_got_wrong(self):
        """A refusal a caller cannot act on sends them back to the code. The
        mistake is a group NAME, so the message says so and says where the real
        names are."""
        with tempfile.TemporaryDirectory() as base:
            _plant_a_pin(base)
            with self.assertRaises(baselines.BaselineError) as ctx:
                runner.capture(HOST, baselines_base=base, groups=[MISTYPED_GROUP])
            msg = str(ctx.exception)
            self.assertIn("--group", msg)
            self.assertIn(HOST, msg)
            self.assertIn(baselines.NON_EMPTY_CLAUSE, msg)


# ---------------------------------------------------------------------------
# T-PINNED-BASE-UNREACHED-ON-STOP
# ---------------------------------------------------------------------------


class TestPinnedBaseUnreachedOnStop(unittest.TestCase):
    """`base=None` resolves to the PINNED directory, and a stopping capture
    never reaches that resolution.

    The red world for this row is NOT constructed here: it is
    `test_the_pre_fix_capture_DESTROYS_the_same_pin_on_the_same_base` above,
    which drives the neutered write against a planted pin on a scratch base.
    Driving a neutered write against the COMMITTED directory would be the
    destruction this pass exists to prevent, performed to prove it is possible."""

    def test_base_none_resolves_to_the_committed_pinned_directory(self):
        """Non-vacuity for the row below: the call it makes really is aimed at
        the pin, and the pin really holds files."""
        self.assertEqual(baselines.baseline_dir(HOST, None), PINNED_DIR / HOST)
        self.assertGreater(len(_sha_map(PINNED_DIR / HOST)), 0)

    def test_the_stop_precedes_every_use_of_the_resolved_path(self):
        """Read STRUCTURALLY, and it is the precondition of the row below: if
        the guard did not come first, the row below would be making a dangerous
        call. This one runs first and refuses without making it."""
        src = BASELINES_SRC.read_text()
        fn = next(
            n for n in ast.parse(src).body
            if isinstance(n, ast.FunctionDef) and n.name == "write_capture"
        )
        body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        guard = body[0]
        self.assertIsInstance(guard, ast.If)
        self.assertEqual(ast.unparse(guard.test), "not group_files")

        #: NON-VACUITY: the function really does resolve `base` to a directory —
        #: so "the resolution is unreached" is a claim about something that
        #: exists — and every one of those resolutions is below the stop.
        resolves = [
            n for n in ast.walk(fn)
            if isinstance(n, ast.Call) and ast.unparse(n.func) == "baseline_dir"
        ]
        self.assertTrue(resolves, "write_capture resolves no path at all")
        for node in resolves:
            self.assertGreater(
                node.lineno, guard.end_lineno, "baseline_dir runs at or before the stop"
            )
        #: and nothing at all executes above it
        self.assertIs(body[0], guard)

    def test_the_pinned_directory_is_unreached_by_a_stopping_capture(self):
        """The assertion the EP names: content identity across the stop, with
        BOTH sides non-empty — the identity of two empty things proves nothing
        (handover item 21, T-CACHE-KILL's own shape).

        It proves the stop is real BEFORE making the call, twice over: the guard
        sits above every path resolution in the source, and the loaded function
        demonstrably stops on a scratch directory. Neither check alone covers
        the other — the source can be right while the loaded module is not."""
        self.test_the_stop_precedes_every_use_of_the_resolved_path()
        self.assertTrue(
            _guard_is_live(),
            "the loaded write_capture does not stop on zero files — refusing to "
            "make the base=None call this row would otherwise make",
        )

        for name in (HOST, GUEST):
            d = PINNED_DIR / name
            before = _sha_map(d)
            self.assertGreater(len(before), 0, "non-vacuity: %s holds files before" % name)

            with self.assertRaises(baselines.BaselineError):
                baselines.write_capture(
                    name, {"kind": "stock"}, {}, {}, None, {}, [], base=None
                )

            after = _sha_map(d)
            self.assertEqual(after, before, "%s moved across the stop" % name)
            self.assertGreater(len(after), 0, "non-vacuity: %s holds files after" % name)

    def test_the_pinned_directory_is_still_loadable_after_the_stop(self):
        """Identity of bytes is not the same claim as the artifact still
        working. Both are asserted, because a pin is a thing that LOADS."""
        self.test_the_stop_precedes_every_use_of_the_resolved_path()
        self.assertTrue(_guard_is_live(), "refusing to make the base=None call")
        for name in (HOST, GUEST):
            with self.assertRaises(baselines.BaselineError):
                baselines.write_capture(
                    name, {"kind": "stock"}, {}, {}, None, {}, [], base=None
                )
            self.assertTrue(baselines.load(name, None).row_ids(), name)


if __name__ == "__main__":
    unittest.main()
