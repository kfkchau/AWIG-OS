# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28M — the VERIFY door and the PARTIAL-SET door, closed BY NAME.

EP-28L closed ONE of THREE doors to a pinned artifact. §A55 binds how this
battery speaks about itself: every class below names WHICH DOOR it closes and
none of them says "the procedure."

  DOOR 2 — VERIFY.  `verify --group`/`--row` matching nothing selects zero rows;
  `Report.ok` is `not self.failed`; zero rows means nothing failed; the exit
  register returns `0 if report.ok else 1`. Pre-fix that is
  `rows: 0 PASS / 0 FAIL / 0 NOT-RUN`, exit 0.

  DOOR 3 — THE PARTIAL SET.  A `--group` naming a REAL group that is only some
  of what the artifact holds writes a manifest naming that group alone. Every
  other group file stays on disk orphaned, and the load SUCCEEDS, because
  EP-28L's clause asks whether the map is empty and a partial map is not.

WORLD (§A39), the variables named rather than proxied.

  * `/tmp/govos-conformance` — WARM at this pass's open, holding the five
    fixture directories. `fixture-correct`'s scratch is created and torn down
    inside each `verify` call; the DOOR 2 rows depend on that directory being
    reachable, and on `establish_scratch` refusing a scratch found dirty. On a
    box where a crashed run left files under `fixture-correct/`, the rows that
    drive a real verify red with a `SubjectError` rather than passing.
  * `tools/conformance/baselines/` — the COMMITTED pins. Nothing here writes to
    them. Every red world runs against a SCRATCH base holding a planted copy,
    and `TestThePinnedDirectoriesAreUntouched` asserts their content identity
    across the whole module with N > 0 on both sides (handover item 21: the
    identity of two empty things proves nothing).

Every red world is produced THROUGH THE LOADED MODULE (§A42): a guard is removed
from a COPY of the source by AST surgery and the copy is executed, so the true
positive and the exhibition run the same code path. The committed sources are
read and never written.
"""

import ast
import hashlib
import json
import shutil
import tempfile
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HARNESS = REPO / "tools" / "conformance" / "harness"
BASELINES_DIR = REPO / "tools" / "conformance" / "baselines"
ROWS_DIR = REPO / "tools" / "conformance" / "rows"
TARGETS_DIR = REPO / "tools" / "conformance" / "targets"

HOST = "host-local"
GUEST = "ep21-ubuntu-guest"
GOVERNED = "fixture-correct"

#: A group id that names no group. One character off `06-files`, which is the
#: mistake EP-28L's capture door was filed from, aimed one door over.
MISTYPED_GROUP = "06-file"
#: A group id that names a REAL group. DOOR 3's whole point is that this one is
#: valid, so nothing about the value is wrong — only its completeness.
REAL_GROUP = "06-files"
#: A REAL, ACTIVE row that carries no probe. DOOR 2's second branch needs no
#: typo at all: naming this row selects one row and produces zero assertions.
REAL_ROW_WITHOUT_PROBE = "files.open~openat"

import sys

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.conformance.harness import baselines, checks, runner  # noqa: E402


# ---------------------------------------------------------------------------
# red-world machinery: the guard removed from a COPY, the copy executed
# ---------------------------------------------------------------------------


def _neutered(module_name, *cuts):
    """Execute a copy of the module with the named guards removed.

    `__package__` is left unset so the module takes its own script branch and
    imports its siblings absolutely — the same objects the committed module
    holds, so a neutered `runner` still drives the real `targets` and `probe`.
    """
    src = (HARNESS / ("%s.py" % module_name)).read_text()
    for func_name, guard_test in cuts:
        tree = ast.parse(src)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                for stmt in list(node.body):
                    if isinstance(stmt, ast.If) and ast.unparse(stmt.test) == guard_test:
                        node.body.remove(stmt)
                        found = True
        if not found:
            raise AssertionError(
                "no `if %s:` in %s.%s — the red world would exhibit nothing"
                % (guard_test, module_name, func_name)
            )
        src = ast.unparse(ast.fix_missing_locations(tree))
    mod = types.ModuleType("%s_neutered" % module_name)
    mod.__file__ = str(HARNESS / ("%s.py" % module_name))
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def _sha_map(d):
    """Every file under a directory, by sha256. The instrument for "byte
    unchanged" that does not depend on mtimes."""
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(Path(d).iterdir())
        if p.is_file()
    }


def _plant_a_pin(base, name=HOST):
    """A COPY of a committed pin in a scratch base. Every write below lands
    here and never on anything committed."""
    d = Path(base) / name
    shutil.copytree(BASELINES_DIR / name, d)
    return d


def _plant_a_second_group(d, group="07-devices"):
    """Make the planted artifact hold TWO groups, which is the world DOOR 3
    becomes live in. Both committed manifests name exactly one group file
    today, so this world is CREATED rather than inherited."""
    payload = {"group": group, "target": HOST, "rows": {"devices.open": {"steps": []}}}
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    (d / ("%s.json" % group)).write_text(text)
    manifest = json.loads((d / "MANIFEST.json").read_text())
    manifest["files"]["%s.json" % group] = {
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "bytes": len(text.encode("utf-8")),
        "rows": 1,
    }
    (d / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return "%s.json" % group


# ---------------------------------------------------------------------------
# DOOR 2 — the verify selection
# ---------------------------------------------------------------------------


class TestVerifyRefusesAnEmptySelection(unittest.TestCase):
    """[DOOR 2] A `--group` or `--row` matching nothing REFUSES, citing the
    selection clause, before any verdict is computed — and the exit is the
    refusal's, never a vacuous 0."""

    def test_a_group_matching_nothing_refuses(self):
        with self.assertRaises(runner.SelectionError) as ctx:
            runner.verify(
                GOVERNED, HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
                targets_dir=TARGETS_DIR, groups=[MISTYPED_GROUP],
            )
        self.assertIn("ZERO rows", str(ctx.exception))

    def test_the_refusal_cites_the_clause_rather_than_only_the_condition(self):
        """A failed gate cites its rule (P4). The message carries the clause,
        not merely the observation that the count was zero."""
        with self.assertRaises(runner.SelectionError) as ctx:
            runner.verify(
                GOVERNED, HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
                targets_dir=TARGETS_DIR, groups=[MISTYPED_GROUP],
            )
        msg = str(ctx.exception)
        self.assertIn(runner.NON_EMPTY_SELECTION_CLAUSE, msg)
        self.assertIn(MISTYPED_GROUP, msg)
        self.assertIn("06-files", msg)

    def test_a_row_id_matching_nothing_refuses_through_the_same_clause(self):
        """The ruling named `--group`; the code shows BOTH selectors feed one
        `select`. A clause placed on the group alone would leave `--row`
        open, which is the same door with a different key."""
        with self.assertRaises(runner.SelectionError):
            runner.verify(
                GOVERNED, HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
                targets_dir=TARGETS_DIR, row_ids=["files.no-such-row"],
            )

    def test_a_real_active_row_carrying_no_probe_refuses_with_its_own_reason(self):
        """AND THIS ONE NEEDS NO TYPO. `files.open~openat` is real, active, and
        selected — it simply carries no probe, so it produces zero assertions
        and zero verdicts. Sixty-two of the hundred-and-two active rows are in
        that state today. A clause guarding only the SELECTION would pass this
        straight through to a vacuous green."""
        with self.assertRaises(runner.SelectionError) as ctx:
            runner.verify(
                GOVERNED, HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
                targets_dir=TARGETS_DIR, row_ids=[REAL_ROW_WITHOUT_PROBE],
            )
        msg = str(ctx.exception)
        self.assertIn("NONE of them is", msg)
        self.assertIn(runner.NON_EMPTY_SELECTION_CLAUSE, msg)

    def test_THE_RED_WORLD_the_pre_fix_verify_greens_over_the_empty_selection(self):
        """RED WORLD, through the loaded module: the same call against a
        `runner` whose two selection guards are removed returns a report with
        ZERO verdicts, `rows: 0 PASS / 0 FAIL / 0 NOT-RUN`, `ok` TRUE."""
        pre_fix = _neutered(
            "runner",
            ("verify", "not selected"),
            ("verify", "not assertions"),
            ("ok", "not self.verdicts"),
        )
        report = pre_fix.verify(
            GOVERNED, HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
            targets_dir=TARGETS_DIR, groups=[MISTYPED_GROUP],
        )
        self.assertEqual(report.verdicts, [])
        self.assertIn("rows: 0 PASS / 0 FAIL / 0 NOT-RUN", report.text())
        self.assertTrue(report.ok, "pre-fix, a report over nothing answers OK")
        self.assertEqual(0 if report.ok else 1, 0, "and the exit register returns 0")

    def test_the_selection_is_proven_before_the_target_is_touched(self):
        """"Before any verdict is computed" is a property of ORDER, read from
        `verify`'s own body. It matters twice: a caller error costs the caller
        nothing, and `establish_scratch`'s teardown lives in a `finally` further
        down — a refusal raised between the two would leak the scratch."""
        fn = next(
            n for n in ast.parse((HARNESS / "runner.py").read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "verify"
        )
        raises = [
            n for n in ast.walk(fn)
            if isinstance(n, ast.Raise) and "SelectionError" in ast.unparse(n)
        ]
        self.assertEqual(len(raises), 2, "both branches of the clause are present")
        last_guard = max(r.lineno for r in raises)
        touches = [
            n for n in ast.walk(fn)
            if isinstance(n, ast.Call)
            and ast.unparse(n.func) in (
                "target.establish_subject", "target.establish_scratch", "target.run_probes",
            )
        ]
        self.assertTrue(touches)
        for node in touches:
            self.assertGreater(
                node.lineno, last_guard,
                "%s runs before the selection is proven non-empty" % ast.unparse(node.func),
            )

    def test_the_scratch_is_not_left_standing_by_a_refusal(self):
        """The consequence of that order, driven rather than argued: after a
        refusal the target's scratch holds no run directory."""
        spec = json.loads((TARGETS_DIR / ("%s.json" % GOVERNED)).read_text())
        scratch = Path(spec["transport"]["scratch"])
        with self.assertRaises(runner.SelectionError):
            runner.verify(
                GOVERNED, HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
                targets_dir=TARGETS_DIR, groups=[MISTYPED_GROUP],
            )
        self.assertFalse(
            scratch.exists() and any(scratch.iterdir()),
            "the refusal left a run directory behind in %s" % scratch,
        )


class TestTheReportRefusesToAnswerOverNothing(unittest.TestCase):
    """[DOOR 2] The clause at the site that MANUFACTURES the vacuous answer.

    `verify` cannot produce an empty report any more, and a guard placed only
    there would leave `ok` itself still willing to answer TRUE because nothing
    failed rather than because anything passed — which is what the exit register
    reads. This is EP-28L's own placement argument one door over."""

    def test_ok_refuses_over_an_empty_verdict_list(self):
        report = runner.Report(GOVERNED, HOST, None, [], [])
        with self.assertRaises(runner.SelectionError) as ctx:
            report.ok
        self.assertIn(runner.NON_EMPTY_SELECTION_CLAUSE, str(ctx.exception))

    def test_ok_still_answers_over_one_verdict(self):
        """Non-vacuity in the other direction: the clause must not red the
        instrument it protects. One PASS row answers TRUE; one FAIL row answers
        FALSE."""
        good = checks.RowVerdict("files.open", [checks.CheckResult("abi-identity", checks.PASS)])
        bad = checks.RowVerdict("files.open", [checks.CheckResult("abi-identity", checks.FAIL)])
        self.assertTrue(runner.Report(GOVERNED, HOST, None, [good], []).ok)
        self.assertFalse(runner.Report(GOVERNED, HOST, None, [bad], []).ok)

    def test_THE_RED_WORLD_the_pre_fix_ok_answers_true_over_nothing(self):
        """RED WORLD, through the loaded module: the identical construction
        against a `runner` whose `ok` guard is removed answers TRUE."""
        pre_fix = _neutered("runner", ("ok", "not self.verdicts"))
        report = pre_fix.Report(GOVERNED, HOST, None, [], [])
        self.assertTrue(report.ok, "pre-fix, `ok` over zero verdicts is TRUE")

    def test_the_guard_is_at_the_site_and_not_only_at_the_caller(self):
        """Structural, and it is the placement claim itself: the raise sits
        inside `Report.ok`, not in `verify` alone."""
        tree = ast.parse((HARNESS / "runner.py").read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Report")
        ok = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "ok")
        self.assertTrue(
            any(isinstance(n, ast.Raise) for n in ast.walk(ok)),
            "`Report.ok` itself does not refuse",
        )


class TestTheExitRegister(unittest.TestCase):
    """[DOOR 2] The exit is the refusal's, never a vacuous 0 — and never a 1,
    which would say ROWS FAILED for a run in which no row ran."""

    def test_a_refusing_verify_exits_2_through_main(self):
        rc = runner.main([
            "verify", "--target", GOVERNED, "--baseline", HOST, "--group", MISTYPED_GROUP,
        ])
        self.assertEqual(rc, 2, "a refusal is exit 2: this run never happened")

    def test_a_baseline_refusal_also_exits_2_rather_than_tracebacking(self):
        """EP-28L's raise 5. It stops being cosmetic the moment a refusal
        travels this way: `BaselineError` left out of the except clause leaves
        `main` as a traceback and exit 1, which is the code reserved for rows
        that failed."""
        rc = runner.main([
            "verify", "--target", GOVERNED, "--baseline", "no-such-baseline",
        ])
        self.assertEqual(rc, 2)

    def test_the_register_reads_report_ok_and_nothing_else(self):
        """Structural: the verify branch's exit expression is derived from
        `report.ok`, so hardening `ok` hardens the register by construction."""
        fn = next(
            n for n in ast.parse((HARNESS / "runner.py").read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "_dispatch"
        )
        exprs = [
            ast.unparse(n.value) for n in ast.walk(fn)
            if isinstance(n, ast.Return) and n.value is not None
        ]
        self.assertIn("0 if report.ok else 1", exprs)


# ---------------------------------------------------------------------------
# DOOR 3 — the valid-but-partial group set
# ---------------------------------------------------------------------------


class TestNoSilentPartial(unittest.TestCase):
    """[DOOR 3] An invocation whose selected groups would leave artifact members
    unaccounted REFUSES, naming the orphans.

    WORLD: a scratch base holding a planted copy of the committed `host-local`
    pin, given a SECOND group so the artifact is one a partial set can orphan.
    Both committed manifests name exactly one group file today, so this world is
    created here rather than inherited."""

    def test_a_valid_but_partial_capture_stops_before_orphaning(self):
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            orphan = _plant_a_second_group(d)
            before = _sha_map(d)
            self.assertEqual(len(before), 3, "the artifact holds N > 0 members")
            with self.assertRaises(baselines.BaselineError) as ctx:
                baselines.write_capture(
                    HOST, {"kind": "stock"},
                    {REAL_GROUP: {"group": REAL_GROUP, "target": HOST, "rows": {"files.open": {}}}},
                    {}, None, {}, [], base=base,
                )
            msg = str(ctx.exception)
            self.assertIn(orphan, msg)
            self.assertIn(baselines.ACCOUNTED_CLAUSE, msg)
            self.assertEqual(_sha_map(d), before, "the stop wrote something")

    def test_THE_RED_WORLD_the_pre_fix_capture_orphans_and_the_load_still_succeeds(self):
        """RED WORLD, through the loaded module, bytes kept. With the two
        accounting clauses removed the same call rewrites the manifest to name
        one group, leaves the other group file standing, and the load SUCCEEDS
        and hands over a baseline smaller than the artifact — with nothing
        anywhere saying so."""
        pre_fix = _neutered(
            "baselines", ("write_capture", "orphans"), ("load", "orphans"),
        )
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            orphan = _plant_a_second_group(d)
            pre_fix.write_capture(
                HOST, {"kind": "stock"},
                {REAL_GROUP: {"group": REAL_GROUP, "target": HOST, "rows": {"files.open": {"steps": []}}}},
                {}, None, {}, [], base=base,
            )
            manifest = json.loads((d / "MANIFEST.json").read_text())
            self.assertNotIn(orphan, manifest["files"], "the orphan is no longer named")
            self.assertTrue((d / orphan).exists(), "and it is still on disk")
            pinned = pre_fix.load(HOST, base)
            self.assertEqual(pinned.row_ids(), ["files.open"])
            self.assertTrue(
                pinned.manifest["files"],
                "EP-28L's clause passes: a PARTIAL map is not an EMPTY one",
            )

    def test_the_load_refuses_an_artifact_that_already_holds_an_orphan(self):
        """The door as the ruling names it — "and STILL LOADS". An artifact
        reaching this box orphaned, by any route, does not load."""
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            (d / "07-devices.json").write_text('{"group": "07-devices", "rows": {}}\n')
            with self.assertRaises(baselines.BaselineError) as ctx:
                baselines.load(HOST, base)
            msg = str(ctx.exception)
            self.assertIn("07-devices.json", msg)
            self.assertIn("NAMES NOWHERE", msg)
            self.assertIn(baselines.ACCOUNTED_CLAUSE, msg)

    def test_the_accounting_runs_in_BOTH_directions(self):
        """A name with no file, and a file with no name. Non-vacuity: the
        artifact holds N > 0 members before either direction is read."""
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            self.assertTrue(baselines.artifact_members(d), "N > 0 members")
            # direction 1 — a NAME with no FILE
            (d / "06-files.json").unlink()
            with self.assertRaises(baselines.BaselineError):
                baselines.load(HOST, base)
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            # direction 2 — a FILE with no NAME
            (d / "09-time-signals.json").write_text('{"rows": {}}\n')
            with self.assertRaises(baselines.BaselineError) as ctx:
                baselines.load(HOST, base)
            self.assertIn("09-time-signals.json", str(ctx.exception))

    def test_a_first_capture_into_an_empty_base_is_not_a_partial_one(self):
        """The control that keeps the clause from refusing everything: an
        artifact that does not exist yet holds no members, so a first capture
        orphans nothing and writes."""
        with tempfile.TemporaryDirectory() as base:
            d, manifest = baselines.write_capture(
                "scratch-target", {"kind": "stock"},
                {REAL_GROUP: {"group": REAL_GROUP, "target": "scratch-target",
                              "rows": {"files.open": {"steps": []}}}},
                {}, None, {}, [], base=base,
            )
            self.assertEqual(sorted(manifest["files"]), ["06-files.json"])
            self.assertEqual(baselines.artifact_members(d), {"06-files.json"})
            baselines.load("scratch-target", base)  # and it loads

    def test_a_complete_re_capture_of_every_group_is_admitted(self):
        """The other control, and it is the remedy the refusal points at:
        capturing EVERY group the artifact holds leaves nothing orphaned."""
        with tempfile.TemporaryDirectory() as base:
            d = _plant_a_pin(base)
            _plant_a_second_group(d)
            baselines.write_capture(
                HOST, {"kind": "stock"},
                {
                    REAL_GROUP: {"group": REAL_GROUP, "target": HOST, "rows": {"files.open": {"steps": []}}},
                    "07-devices": {"group": "07-devices", "target": HOST, "rows": {"devices.open": {"steps": []}}},
                },
                {}, None, {}, [], base=base,
            )
            pinned = baselines.load(HOST, base)
            self.assertEqual(sorted(pinned.manifest["files"]), ["06-files.json", "07-devices.json"])
            self.assertEqual(baselines.artifact_members(d), set(pinned.manifest["files"]))

    def test_the_orphan_stop_precedes_every_write(self):
        """Structural, and it is why the stop is at the write rather than only
        at the load: nothing is created above it, so the manifest that still
        names the orphan is intact and the undo window stays open (§A53)."""
        fn = next(
            n for n in ast.parse((HARNESS / "baselines.py").read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "write_capture"
        )
        guard = next(
            s for s in fn.body
            if isinstance(s, ast.If) and ast.unparse(s.test) == "orphans"
        )
        writes = [
            n.lineno for n in ast.walk(fn)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr in ("mkdir", "write_text", "write_bytes")
        ]
        self.assertTrue(writes)
        for lineno in writes:
            self.assertGreater(lineno, guard.lineno, "a write precedes the orphan stop")

    def test_the_stop_neither_recovers_nor_substitutes(self):
        """P4, read structurally rather than left to a reader: the stop is one
        `raise` and it re-selects nothing, retries nothing, returns nothing."""
        fn = next(
            n for n in ast.parse((HARNESS / "baselines.py").read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "write_capture"
        )
        guard = next(
            s for s in fn.body
            if isinstance(s, ast.If) and ast.unparse(s.test) == "orphans"
        )
        self.assertEqual(len(guard.body), 1)
        self.assertIsInstance(guard.body[0], ast.Raise)
        self.assertEqual(guard.orelse, [])
        for node in ast.walk(guard):
            self.assertNotIsInstance(node, (ast.Try, ast.For, ast.While, ast.Return, ast.Assign))

    def test_EP28L_s_zero_group_stop_is_still_the_first_statement(self):
        """This pass added a second stop to the same function. EP-28L's is
        still `body[0]`, because its own reason is stricter than mine: it must
        not RESOLVE a path, and mine must read the directory to know what is
        in it."""
        fn = next(
            n for n in ast.parse((HARNESS / "baselines.py").read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "write_capture"
        )
        body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        self.assertIsInstance(body[0], ast.If)
        self.assertEqual(ast.unparse(body[0].test), "not group_files")


class TestTheCommittedArtifactsAccountExactly(unittest.TestCase):
    """[DOOR 3] The clause must not red the estate it protects, and the estate
    must not already be in the state it refuses."""

    def test_both_committed_baselines_account_for_every_file_they_hold(self):
        for name in (HOST, GUEST):
            d = baselines.baseline_dir(name)
            held = baselines.artifact_members(d)
            named = set(json.loads((d / "MANIFEST.json").read_text())["files"])
            self.assertTrue(held, "%s holds N > 0 members" % name)
            self.assertEqual(held, named, "%s: held vs named" % name)

    def test_both_committed_baselines_still_load(self):
        for name in (HOST, GUEST):
            pinned = baselines.load(name, None)
            self.assertTrue(pinned.row_ids(), name)


class TestThePinnedDirectoriesAreUntouched(unittest.TestCase):
    """§A42 clause 2 and EP-28L's own shape: this module exhibits DOOR 3
    through the REAL write path, so it states the committed pins' content
    identity across its own exhibitions rather than asserting it was careful.

    Non-vacuity (handover item 21): both directories hold N > 0 files on both
    sides — the identity of two empty things proves nothing."""

    def test_the_committed_pins_are_byte_identical_across_this_module(self):
        for name in (HOST, GUEST):
            d = BASELINES_DIR / name
            shas = _sha_map(d)
            self.assertGreater(len(shas), 0, "%s holds N > 0 files" % name)
            self.assertEqual(
                shas,
                {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(d.iterdir()) if p.is_file()},
                name,
            )

    def test_no_write_in_this_module_can_resolve_to_the_pinned_directory(self):
        """The structural half: every `write_capture` call in this file passes
        an explicit `base=`, so `base=None`'s resolution to the pinned
        directory is never reached from here."""
        tree = ast.parse(Path(__file__).read_text())
        calls = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("write_capture")
        ]
        self.assertTrue(calls, "no capture is driven here, so this row proves nothing")
        for call in calls:
            self.assertIn(
                "base", [kw.arg for kw in call.keywords],
                "a write_capture call in this file omits base=, which resolves to the PIN",
            )


if __name__ == "__main__":
    unittest.main()
