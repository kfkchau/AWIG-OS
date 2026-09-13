"""EP-24D — the instrument repaired on findings from its own first real use.

The acceptance battery EP-24D names before any code:

  T-COALESCE-ASSERTS-THE-POLICY  a coalescible row passes when the folded event
                                 cites the recorded policy and the target declares
                                 it, and fails in both wrong directions.
  T-OUTCOME-CLASS-BINDS          design/10 §11.1a's three classes, each binding:
                                 a REFUSAL that recorded nothing fails; an ABSENCE
                                 or NOT-GOVERNED that recorded fails; and the pass
                                 case for each.
  T-NO-WAIVER-REMAINS            no code path waives the recording check's required
                                 half on `subject_succeeded` or any other proxy.
  T-SUBJECT-IS-VERIFIED          verify against a path that is not what the
                                 descriptor claims fails with a named error rather
                                 than reporting rows; a `~` in a descriptor resolves
                                 or fails, never addressing a directory named `~`.
  T-SUBJECT-LIFECYCLE            a dirty scratch is refused and its contents named;
                                 a run establishes and tears down cleanly; and a run
                                 cannot leave a mountpoint in a state that blocks the
                                 next mount.

T-HARNESS-COLUMNS-FAIL and T-CONFORMANCE-BASELINE-PINNED stay where EP-24 built
them (`tests/test_ep24.py`) and re-run unchanged — the proof that this repair did
not soften the three legs.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.conformance import fixtures  # noqa: E402
from tools.conformance.harness import (  # noqa: E402
    baselines,
    checks,
    probe,
    rows as rows_mod,
    runner,
    targets,
)

ROWS_DIR = REPO / "tools" / "conformance" / "rows"
BASELINES_DIR = REPO / "tools" / "conformance" / "baselines"
TARGETS_DIR = REPO / "tools" / "conformance" / "targets"
HARNESS_DIR = REPO / "tools" / "conformance" / "harness"
HOST = "host-local"


def compile_rows(payload):
    """One group file, written as data and compiled — the same path a real row
    takes. Rows are data, so a test's row needs no harness knowledge either."""
    d = tempfile.mkdtemp()
    (Path(d) / "99-fixture.json").write_text(json.dumps(payload))
    _groups, rows = rows_mod.load_all(d)
    shutil.rmtree(d, ignore_errors=True)
    return {r.row_id: r for r in rows}


def group(rows):
    return {
        "group": "99-fixture",
        "map_ref": "design/10 §6",
        "active": True,
        "activates_at": "EP-24D",
        "rows": rows,
    }


def row(row_id, classes, probe_steps=None, outcome_class=None, rules=None):
    p = {"steps": probe_steps or [{"call": "mkdir", "args": ["d", "0o755"]}]}
    if outcome_class:
        p["outcome_class"] = outcome_class
    r = {
        "row_id": row_id,
        "syscall": row_id.split(".")[-1],
        "what_it_does": "fixture",
        "subsystems": ["files"],
        "recording_class": list(classes),
        "conformance_note": "fixture row for the EP-24D battery.",
        "status": "ENCODED",
        "probe": p,
    }
    if rules:
        r["rules"] = rules
    return r


# ---------------------------------------------------------------------------
# T-COALESCE-ASSERTS-THE-POLICY
# ---------------------------------------------------------------------------


class TestCoalesceAssertsThePolicy(unittest.TestCase):
    """design/10 §11 rule 4, verbatim: a test may assert that the policy exists
    and is cited, NOT that every micro-event has its own record. The harness used
    to require the covering record inside the calling step's bracket, where a
    folded write's covering decision does not land — so it failed the audit leg
    for behaviour the map licenses."""

    def setUp(self):
        self.by_id = compile_rows(
            group([row("files.fold", ["DECISION"], rules={"coalescible": True})])
        )
        self.a = self.by_id["files.fold"]
        self.class_map = {"WRITE": "DECISION", "OPEN": "DECISION"}

    def _check(self, window, policies=("FS-WRITE-COALESCING",), records=(), acts=4):
        """DOCUMENTED FLIP (ADDENDUM 2, W8). This helper used to hand the check the
        subject's bracket AND a separate fold window, because the fold was the one
        rule allowed to read outside the bracket. §11.4a makes that the ordinary
        reading: there is one window, and each record in it is attributed to the
        act it covers. The `records` argument is kept so every case below still
        says what the subject's own bracket held — it is now part of the window,
        which is exactly the point. Not one assertion's meaning changed."""
        return checks.check_recording_class(
            self.a,
            checks.Attribution(
                window=tuple(records) + tuple(window),
                covers={"WRITE": ["write"], "OPEN": ["open"]},
                subject_calls=frozenset({"write"}),
                other_calls=frozenset({"open"}),
            ),
            self.class_map,
            coalescing_policies=tuple(policies),
            subject_acts=acts,
        )

    def _folded(self, policy="FS-WRITE-COALESCING", record_id="rec_9"):
        rec = {"action": "WRITE", "record_id": record_id, "rule_cited": "FS-LAW-PERM",
               "payload": {"coalesced_events": 4, "length": 6}}
        if policy:
            rec["payload"]["coalescing_policy"] = policy
        return rec

    def test_the_folded_event_may_land_outside_the_calling_steps_bracket(self):
        """The pass case, and the defect that produced this EP: the subject step's
        bracket is EMPTY and the one covering decision for four acts lands later in
        the row."""
        result = self._check([self._folded()], records=[])
        self.assertEqual(result.verdict, checks.PASS, result.detail)

    def test_a_folded_event_citing_nothing_fails(self):
        result = self._check([self._folded(policy=None)])
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("cites no recorded coalescing policy" in d for d in result.detail))
        self.assertTrue(any("WRITE(rec_9)" in d for d in result.detail))

    def test_a_folded_event_citing_a_policy_the_target_does_not_declare_fails(self):
        """The other direction, and the reason the check asks whether the record
        names a DECLARED policy rather than whether it names any: a fold citing a
        policy nobody recorded has no named owner, which is what §11.4 requires."""
        result = self._check([self._folded(policy="SOME-OTHER-POLICY")])
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("FS-WRITE-COALESCING" in d for d in result.detail))

    def test_a_target_declaring_no_policy_at_all_fails_a_fold(self):
        """§11.4 makes folding a NAMED calibration. A fold with no recorded policy
        is the silent loss the rule exists to forbid."""
        result = self._check([self._folded()], policies=())
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("declares no coalescing policy" in d for d in result.detail))

    def test_nothing_recorded_at_all_still_fails(self):
        """Not requiring a record PER EVENT is not the same as requiring none: the
        covering event must exist somewhere in the row's window."""
        result = self._check([])
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("never losing the event" in d for d in result.detail))

    def test_one_covering_event_per_act_passes_with_no_policy_cited(self):
        """FOLDING IS LICENSED, NEVER MANDATED. A world whose coalescing policy has
        been superseded to nothing appends one covering decision per write and is
        exactly as conformant — which is the world ep25-nocoalesce measures, and it
        must not be failed for declining to fold."""
        per_act = [
            {"action": "WRITE", "record_id": "rec_%d" % i, "rule_cited": "FS-LAW-PERM"}
            for i in range(4)
        ]
        self.assertEqual(self._check(per_act, policies=()).verdict, checks.PASS)
        self.assertEqual(self._check(per_act).verdict, checks.PASS)

    def test_a_fold_is_seen_from_outside_by_counting_acts_against_events(self):
        """The discriminator uses only what the harness already holds: what the row
        drove, and what the record holds. Neither is the target's vocabulary, and
        neither is the target's word for it."""
        uncited = self._folded(policy=None)
        self.assertEqual(self._check([uncited], acts=1).verdict, checks.PASS)
        self.assertEqual(self._check([uncited], acts=2).verdict, checks.FAIL)

    def test_a_non_coalescible_row_is_unchanged(self):
        by_id = compile_rows(group([row("files.plain", ["DECISION"])]))
        a = by_id["files.plain"]
        cited = checks.check_recording_class(
            a, [{"action": "MKDIR", "rule_cited": "R"}], {"MKDIR": "DECISION"}
        )
        self.assertEqual(cited.verdict, checks.PASS)
        empty = checks.check_recording_class(a, [], {"MKDIR": "DECISION"})
        self.assertEqual(empty.verdict, checks.FAIL)

    def test_the_write_row_of_the_files_group_is_the_coalescible_one(self):
        _g, rows = rows_mod.load_all(ROWS_DIR)
        write = [r for r in rows if r.row_id == "files.write"][0]
        self.assertTrue(write.rules.coalescible)


# ---------------------------------------------------------------------------
# T-OUTCOME-CLASS-BINDS
# ---------------------------------------------------------------------------


class TestOutcomeClassBinds(unittest.TestCase):
    """design/10 §11.1a: every row whose tested outcome is an error return declares
    REFUSAL, ABSENCE or NOT-GOVERNED, and both halves of the recording check then
    bind on it. The discriminator is not the errno — it is whether the gate reached
    a decision, which the row's author declares."""

    def setUp(self):
        self.by_id = compile_rows(
            group(
                [
                    row("files.refused", ["DECISION"], outcome_class="REFUSAL"),
                    row("files.absent", ["CACHE"], outcome_class="ABSENCE"),
                    row("files.ungoverned", ["LAW"], outcome_class="NOT-GOVERNED"),
                ]
            )
        )
        self.class_map = {"REFUSE": "DECISION", "READ": "CACHE", "AMEND": "LAW"}

    def _check(self, row_id, records):
        a = self.by_id[row_id]
        return checks.check_recording_class(
            a, records, self.class_map, outcome_class=a.outcome_class
        )

    def test_a_refusal_that_recorded_nothing_fails(self):
        result = self._check("files.refused", [])
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("REFUSAL" in d for d in result.detail))

    def test_a_refusal_that_recorded_its_rule_citing_decision_passes(self):
        result = self._check(
            "files.refused", [{"action": "REFUSE", "rule_cited": "ROOT-NEG-1"}]
        )
        self.assertEqual(result.verdict, checks.PASS, result.detail)

    def test_a_refusal_whose_record_cites_no_rule_fails(self):
        result = self._check("files.refused", [{"action": "REFUSE", "rule_cited": None}])
        self.assertEqual(result.verdict, checks.FAIL)

    def test_an_absence_that_produced_a_record_fails(self):
        result = self._check("files.absent", [{"action": "READ", "rule_cited": "R"}])
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("ABSENCE" in d for d in result.detail))

    def test_an_absence_that_produced_nothing_passes(self):
        self.assertEqual(self._check("files.absent", []).verdict, checks.PASS)

    def test_a_not_governed_that_produced_a_record_fails(self):
        result = self._check("files.ungoverned", [{"action": "AMEND", "rule_cited": "R"}])
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("NOT-GOVERNED" in d for d in result.detail))

    def test_a_not_governed_that_produced_nothing_passes(self):
        self.assertEqual(self._check("files.ungoverned", []).verdict, checks.PASS)

    def test_the_two_no_record_classes_are_kept_apart_in_what_they_say(self):
        """§11.1a keeps ABSENCE and NOT-GOVERNED apart because a row's author must
        say which is true: "it appends nothing" is not the same claim as "nothing
        was governed here". The failure text says which claim was broken."""
        absent = self._check("files.absent", [{"action": "READ", "rule_cited": "R"}])
        ungoverned = self._check("files.ungoverned", [{"action": "AMEND", "rule_cited": "R"}])
        self.assertNotEqual(absent.detail, ungoverned.detail)

    def test_an_outcome_class_outside_the_three_is_refused_loudly(self):
        with self.assertRaises(rows_mod.RowError):
            compile_rows(group([row("files.bad", ["DECISION"], outcome_class="MAYBE")]))

    def test_the_declaration_rides_the_probe_not_the_row(self):
        """A row's privileged pass tests a different outcome from its unprivileged
        one — files.mount succeeds as root and returns EPERM otherwise. So the
        declaration belongs to the probe whose outcome it describes, and the root
        assertion picks up its own (or none)."""
        _g, rows = rows_mod.load_all(ROWS_DIR)
        mount = [r for r in rows if r.row_id == "files.mount"][0]
        self.assertEqual(mount.outcome_class, "NOT-GOVERNED")
        root = runner.root_assertion(mount)
        self.assertIsNone(root.outcome_class)

    def test_every_files_row_whose_pinned_outcome_is_an_error_declares_its_class(self):
        """W3, asserted structurally rather than by inspection: the pinned stock
        capture says which rows' subject steps all returned an errno, and §11.1a
        says every one of them declares which of the three it asserts."""
        _g, rows = rows_mod.load_all(ROWS_DIR)
        pinned = baselines.load(HOST, BASELINES_DIR)
        undeclared = []
        for a in rows:
            if not (a.active and a.has_probe):
                continue
            obs = pinned.get(a.row_id)
            if obs is None:
                continue
            subjects = a.subject_calls(probe.DRIVES)
            steps = [s for s in obs.get("steps", []) if s.get("call") in subjects]
            if not steps:
                continue
            if any(s.get("errno") is None and "exception" not in s for s in steps):
                continue
            if not a.outcome_class:
                undeclared.append(a.row_id)
        self.assertEqual(undeclared, [], "error-outcome rows with no §11.1a class")


# ---------------------------------------------------------------------------
# T-NO-WAIVER-REMAINS
# ---------------------------------------------------------------------------


class TestNoWaiverRemains(unittest.TestCase):
    """The waiver fired on `subject_succeeded` — computed from the observation, not
    from the row — and it waived the required half exactly where P4 makes a record
    MOST required. It is gone, and this asserts that structurally so it cannot
    return under another name."""

    def test_the_proxy_is_gone_from_the_checks_module(self):
        text = (HARNESS_DIR / "checks.py").read_text()
        self.assertNotIn("subject_succeeded", text)
        self.assertFalse(hasattr(checks, "subject_succeeded"))

    def test_no_check_takes_a_success_proxy_as_a_parameter(self):
        import inspect

        for name in ("check_recording_class", "run_row_checks"):
            params = set(inspect.signature(getattr(checks, name)).parameters)
            for banned in ("subject_succeeded", "subject_ok", "succeeded"):
                self.assertNotIn(banned, params, "%s(%s)" % (name, banned))

    def test_the_runner_computes_no_success_proxy(self):
        self.assertNotIn("subject_succeeded", (HARNESS_DIR / "runner.py").read_text())

    def test_the_required_half_binds_when_the_row_declares_nothing(self):
        """The behavioural half: with no declared outcome class the required half
        binds, whatever the call returned. There is no branch left that switches
        it off."""
        by_id = compile_rows(group([row("files.plain", ["DECISION"])]))
        result = checks.check_recording_class(by_id["files.plain"], [], {})
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertFalse(result.notes)

    def test_only_the_three_declared_classes_can_relieve_the_required_half(self):
        self.assertEqual(
            tuple(checks.OUTCOME_CLASSES), ("REFUSAL", "ABSENCE", "NOT-GOVERNED")
        )
        self.assertEqual(tuple(checks.NO_RECORD_OUTCOMES), ("ABSENCE", "NOT-GOVERNED"))


# ---------------------------------------------------------------------------
# T-SUBJECT-IS-VERIFIED
# ---------------------------------------------------------------------------


class TestSubjectIsVerified(unittest.TestCase):
    """design/10 §11.2b half 1. A pass against an absent subject is worse than a
    failure, because it is indistinguishable from success."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.spec = json.loads((TARGETS_DIR / "fixture-correct.json").read_text())

    def _target(self, **overrides):
        spec = json.loads(json.dumps(self.spec))
        spec.update(overrides)
        path = Path(self.tmp) / ("%s.json" % spec["name"])
        path.write_text(json.dumps(spec))
        return targets.Target.load(spec["name"], self.tmp)

    def test_an_ordinary_directory_where_a_filesystem_was_declared_refuses(self):
        plain = Path(self.tmp) / "plain"
        plain.mkdir()
        t = self._target(subject={"path": str(plain), "fstype": "fuse"})
        with self.assertRaises(targets.SubjectError) as ctx:
            t.establish_subject()
        self.assertIn(str(plain), str(ctx.exception))
        self.assertIn("fuse", str(ctx.exception))

    def test_verify_aborts_before_a_single_row_runs(self):
        """The abort is not a failing row. No row is driven and no verdict is
        produced, because a report about an unestablished subject is the thing
        §11.2b exists to prevent."""
        plain = Path(self.tmp) / "plain2"
        plain.mkdir()
        t = self._target(name="fixture-subject-absent",
                         subject={"path": str(plain), "fstype": "fuse"})
        ran = []
        original = targets.Target.run_probes
        targets.Target.run_probes = lambda *a, **k: ran.append(1) or ({}, {})
        try:
            with self.assertRaises(targets.SubjectError):
                runner.verify(
                    t.name, HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
                    targets_dir=self.tmp, row_ids=["files.mkdir"],
                )
        finally:
            targets.Target.run_probes = original
        self.assertEqual(ran, [])

    def test_a_missing_path_refuses_rather_than_being_created(self):
        gone = Path(self.tmp) / "not-there"
        t = self._target(subject={"path": str(gone), "fstype": "fuse"})
        with self.assertRaises(targets.SubjectError):
            t.establish_subject()
        self.assertFalse(gone.exists())

    def test_a_governed_target_that_declares_no_subject_refuses(self):
        spec = json.loads(json.dumps(self.spec))
        spec.pop("subject", None)
        spec["name"] = "fixture-no-subject"
        (Path(self.tmp) / "fixture-no-subject.json").write_text(json.dumps(spec))
        t = targets.Target.load("fixture-no-subject", self.tmp)
        with self.assertRaises(targets.SubjectError):
            t.establish_subject()

    def test_a_declared_ordinary_directory_is_itself_an_assertion(self):
        """The fixtures' subject IS an ordinary directory, and saying so is a
        check: if one of them ever became a mount point, the run would refuse
        rather than report."""
        plain = Path(self.tmp) / "plain3"
        plain.mkdir()
        t = self._target(subject={"path": str(plain), "fstype": "directory"})
        established = t.establish_subject()
        self.assertEqual(established["path"], str(plain))
        self.assertEqual(established["declared"], "directory")

    def test_a_mount_point_where_an_ordinary_directory_was_declared_refuses(self):
        """/proc is a mount point on any live Linux host, so it stands in for the
        direction this column must also be able to fail in."""
        t = self._target(subject={"path": "/proc", "fstype": "directory"})
        with self.assertRaises(targets.SubjectError) as ctx:
            t.establish_subject()
        self.assertIn("proc", str(ctx.exception))

    def test_the_served_filesystem_is_read_from_the_kernels_own_mount_table(self):
        self.assertEqual(targets.served_by("/proc"), "proc")
        self.assertIsNone(targets.served_by(self.tmp))

    def test_a_tilde_in_a_descriptor_resolves_and_never_becomes_a_directory(self):
        """The historical case, named in EP-24D's defect 3: a `~` in a target
        descriptor sent the probe into a directory literally named `~`, and the
        harness reported ABI 40 of 40 while the record file held one name."""
        home = Path(self.tmp) / "home"
        home.mkdir()
        cwd = os.getcwd()
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(home)
        os.chdir(self.tmp)
        try:
            spec = json.loads(json.dumps(self.spec))
            spec["name"] = "fixture-tilde"
            spec["transport"]["scratch"] = "~/scratch"
            spec["subject"] = {"path": "~", "fstype": "directory"}
            (Path(self.tmp) / "fixture-tilde.json").write_text(json.dumps(spec))
            t = targets.Target.load("fixture-tilde", self.tmp)
            self.assertEqual(t.scratch_path, str(home / "scratch"))
            t.establish_scratch()
            self.assertTrue((home / "scratch").is_dir())
            self.assertFalse(Path(self.tmp, "~").exists())
            self.assertEqual(t.establish_subject()["path"], str(home))
            t.teardown_scratch()
        finally:
            os.chdir(cwd)
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home
        self.assertFalse(Path(self.tmp, "~").exists())

    def test_every_governed_descriptor_in_the_tree_declares_its_subject(self):
        for path in sorted(TARGETS_DIR.glob("*.json")):
            spec = json.loads(path.read_text())
            if spec.get("kind") != "governed":
                continue
            self.assertIn("subject", spec, path.name)
            self.assertIn("path", spec["subject"], path.name)
            self.assertIn("fstype", spec["subject"], path.name)

    def test_the_mount_targets_declare_the_filesystem_they_claim_to_be(self):
        for name in ("ep25-fuse-mount", "ep25-nocoalesce"):
            spec = json.loads((TARGETS_DIR / ("%s.json" % name)).read_text())
            self.assertEqual(spec["subject"]["fstype"], "fuse", name)
            self.assertTrue(spec["transport"]["scratch"].startswith(spec["subject"]["path"]))


# ---------------------------------------------------------------------------
# T-SUBJECT-LIFECYCLE
# ---------------------------------------------------------------------------


class TestSubjectLifecycle(unittest.TestCase):
    """design/10 §11.2b half 2, and EP-24D ADDENDUM 1: a check is not enough,
    because the first mis-addressed run writes real files into the mountpoint and
    those files make every later mount fail. The subject needs a lifecycle."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.spec = json.loads((TARGETS_DIR / "fixture-correct.json").read_text())
        fixtures.stand_up(TARGETS_DIR)

    def _target(self, scratch, name="fixture-lifecycle"):
        """The subject is the place; the scratch is a directory inside it that the
        run creates and removes. Conflating the two would make "the subject must
        already be there" and "the scratch is created if absent" contradict, which
        is the collision this shape resolves — and it is the same shape the mount
        has: subject /tmp/govos-m2/mnt, scratch inside it."""
        scratch = Path(scratch)
        scratch.parent.mkdir(parents=True, exist_ok=True)
        spec = json.loads(json.dumps(self.spec))
        spec["name"] = name
        spec["transport"]["scratch"] = str(scratch)
        spec["subject"] = {"path": str(scratch.parent), "fstype": "directory"}
        (Path(self.tmp) / ("%s.json" % name)).write_text(json.dumps(spec))
        return targets.Target.load(name, self.tmp)

    def test_a_dirty_scratch_is_refused_and_its_contents_are_named(self):
        scratch = Path(self.tmp) / "dirty" / "scratch"
        scratch.mkdir(parents=True)
        (scratch / "run-deadbeef").mkdir()
        (scratch / "leftover.txt").write_text("evidence")
        t = self._target(scratch)
        with self.assertRaises(targets.SubjectError) as ctx:
            t.establish_scratch()
        msg = str(ctx.exception)
        self.assertIn("run-deadbeef", msg)
        self.assertIn("leftover.txt", msg)
        self.assertTrue((scratch / "leftover.txt").exists(), "refused, never cleared")

    def test_an_absent_scratch_is_created_and_a_clean_one_is_accepted(self):
        scratch = Path(self.tmp) / "fresh" / "scratch"
        t = self._target(scratch)
        t.establish_scratch()
        self.assertTrue(scratch.is_dir())
        t.teardown_scratch()
        self.assertFalse(scratch.exists(), "what the run created, the run removes")

        scratch.mkdir()
        t2 = self._target(scratch, name="fixture-lifecycle-2")
        t2.establish_scratch()
        t2.teardown_scratch()
        self.assertTrue(scratch.is_dir(), "a scratch found empty is left as it was found")

    def test_a_run_leaves_the_mountpoint_empty_enough_for_the_next_mount(self):
        """The entrenchment this addendum exists for: leftovers in a mountpoint
        make `mount` fail with `mountpoint is not empty`. After a run there are
        none, so the next mount is possible."""
        scratch = Path(self.tmp) / "cycle" / "scratch"
        t = self._target(scratch)
        t.establish_scratch()
        t.transport.run({"rows": [{"row_id": "files.mkdir",
                                   "steps": [{"call": "mkdir", "args": ["d", "0o755"]}]}]})
        self.assertTrue(any(scratch.iterdir()), "the run really wrote into the scratch")
        t.teardown_scratch()
        self.assertFalse(scratch.exists())

    def test_without_the_teardown_the_next_run_refuses_and_names_why(self):
        """The column proved able to fail: with teardown suppressed, the leftovers
        remain and the next establish REFUSES rather than driving them."""
        scratch = Path(self.tmp) / "no-teardown" / "scratch"
        t = self._target(scratch)
        t.establish_scratch()
        t.transport.run({"rows": [{"row_id": "files.mkdir",
                                   "steps": [{"call": "mkdir", "args": ["d", "0o755"]}]}]})
        t2 = self._target(scratch, name="fixture-lifecycle-3")
        with self.assertRaises(targets.SubjectError) as ctx:
            t2.establish_scratch()
        self.assertIn("run-", str(ctx.exception))

    def test_verify_establishes_and_tears_down_around_the_rows(self):
        report = runner.verify(
            "fixture-correct",
            HOST,
            rows_dir=ROWS_DIR,
            baselines_base=BASELINES_DIR,
            targets_dir=TARGETS_DIR,
            row_ids=["files.mkdir"],
        )
        self.assertTrue(report.ok, report.text())
        spec = json.loads((TARGETS_DIR / "fixture-correct.json").read_text())
        scratch = Path(spec["transport"]["scratch"])
        self.assertFalse(
            scratch.exists() and any(scratch.iterdir()),
            "verify left run directories behind in the scratch",
        )

    def test_the_run_names_the_subject_it_established_in_its_own_report(self):
        """The evidence line: a report says which path it addressed and what
        served it, so a later reader never has to infer which subject a figure
        was taken against."""
        report = runner.verify(
            "fixture-correct",
            HOST,
            rows_dir=ROWS_DIR,
            baselines_base=BASELINES_DIR,
            targets_dir=TARGETS_DIR,
            row_ids=["files.mkdir"],
        )
        self.assertIn("subject", report.text())
        self.assertIn(report.subject["path"], report.text())

    def test_a_transport_that_cannot_be_established_refuses_rather_than_skips(self):
        """The ssh transport's scratch is a fresh uuid directory on the target and
        the harness cannot read that target's mount table from here. It says so and
        REFUSES; it does not quietly report on a subject it never established."""
        spec = json.loads((TARGETS_DIR / "ep21-ubuntu-guest.json").read_text())
        spec["kind"] = "governed"
        spec["name"] = "fixture-remote"
        spec["subject"] = {"path": "/tmp/whatever", "fstype": "fuse"}
        (Path(self.tmp) / "fixture-remote.json").write_text(json.dumps(spec))
        t = targets.Target.load("fixture-remote", self.tmp)
        with self.assertRaises(targets.SubjectError) as ctx:
            t.establish_subject()
        self.assertIn("ssh", str(ctx.exception))


# ---------------------------------------------------------------------------
# T-ATTRIBUTION-BY-COVERED-ACT  (ADDENDUM 2, W8)
# ---------------------------------------------------------------------------


class TestAttributionByCoveredAct(unittest.TestCase):
    """design/10 §11.4a: a record is attributed to the act it COVERS, read from its
    own action, object and citation, and never to the step whose bracket it landed
    in.

    THE CASE THAT PRODUCED THE RULE, and it is one fold producing two failures in
    opposite directions. A governed filesystem folds a burst of writes and emits
    the covering decision at the flush boundary its policy names — so the `write`
    row's own bracket holds nothing and the `fsync` row's bracket holds a DECISION
    the fsync did not make. Attribution by landing point fails both: the write row
    for holding nothing, the fsync row for holding something. Attribution by
    covered act passes both, because the one record is about the write in each
    reading.

    Both directions are proved able to fail: a record covering an act the row never
    drove FAILS, and a record whose covered act the target never declared FAILS.
    """

    #: A target's own vocabulary, read as data: which acts each record kind is
    #: ABOUT. The harness authors none of it — this is the fixture's declaration
    #: standing in for the mount's.
    COVERS = {
        "WRITE": ["write", "pwrite64", "writev"],
        "OPEN": ["open", "openat"],
        "CLOSE": ["close"],
        "QUOTA": ["quotactl"],
        "MAP-UID": [],
    }
    CLASSES = {"WRITE": "DECISION", "OPEN": "DECISION", "CLOSE": "DECISION",
               "QUOTA": "DECISION", "MAP-UID": "DECISION"}

    def _attr(self, window, subject, other=()):
        return checks.Attribution(
            window=tuple(window),
            covers=dict(self.COVERS),
            subject_calls=frozenset(subject),
            other_calls=frozenset(other),
        )

    def _rec(self, action, obj="/w.txt", rule="FS-LAW-PERM"):
        return {"action": action, "object": obj, "rule_cited": rule,
                "record_id": "rec_%s" % action.lower()}

    def _row(self, row_id, classes, rules=None):
        return compile_rows(group([row(row_id, classes, rules=rules)]))[row_id]

    # --- direction 1: the deferred record reaches the act it covers ---------

    def test_the_write_rows_covering_record_lands_in_a_later_step_and_still_counts(self):
        """The act's own row PASSES though its bracket was empty: the covering
        decision landed in the fsync step's bracket and covers the write."""
        a = self._row("files.write", ["DECISION"])
        result = checks.check_recording_class(
            a,
            self._attr([self._rec("WRITE")], subject={"write"}, other={"open", "fsync", "close"}),
            self.CLASSES,
        )
        self.assertEqual(result.verdict, checks.PASS, result.detail)

    def test_the_same_record_does_not_fail_the_later_row(self):
        """The other half, and the one bracket attribution got backwards: a
        CACHE-only fsync row whose bracket holds that same DECISION does NOT fail,
        because the record is about the write the row only set up."""
        a = self._row("files.fsync", ["CACHE"])
        result = checks.check_recording_class(
            a,
            self._attr([self._rec("WRITE")], subject={"fsync"}, other={"open", "write", "close"}),
            self.CLASSES,
        )
        self.assertEqual(result.verdict, checks.PASS, result.detail)
        self.assertTrue(
            any("set up" in n for n in result.notes),
            "an excluded record leaves a trace on the result: %s" % result.notes,
        )

    def test_by_landing_point_that_same_pair_fails_in_both_directions(self):
        """The defect, reproduced, so the repair is measured against it rather than
        asserted. Judged as the subject's own records — which is what a bracket
        hands over — the write row holds nothing and the fsync row holds a
        DECISION."""
        write_row = self._row("files.write", ["DECISION"])
        fsync_row = self._row("files.fsync", ["CACHE"])
        self.assertEqual(
            checks.check_recording_class(write_row, [], self.CLASSES).verdict, checks.FAIL
        )
        self.assertEqual(
            checks.check_recording_class(
                fsync_row, [self._rec("WRITE")], self.CLASSES
            ).verdict,
            checks.FAIL,
        )

    # --- direction 2: a record covering nothing the row drove --------------

    def test_a_record_covering_an_act_the_row_never_drove_fails(self):
        a = self._row("files.fsync", ["CACHE"])
        result = checks.check_recording_class(
            a,
            self._attr([self._rec("QUOTA")], subject={"fsync"}, other={"open", "close"}),
            self.CLASSES,
        )
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("quotactl" in d for d in result.detail), result.detail)

    def test_a_record_whose_action_the_target_never_declared_fails(self):
        """An instrument cannot attribute what the target's vocabulary does not
        describe, and an unattributable record is reported rather than dropped."""
        a = self._row("files.write", ["DECISION"])
        result = checks.check_recording_class(
            a,
            self._attr([self._rec("SOMETHING-ELSE")], subject={"write"}),
            self.CLASSES | {"SOMETHING-ELSE": "DECISION"},
        )
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("covers map" in d for d in result.detail), result.detail)

    def test_a_record_the_target_declares_is_about_no_caller_act_is_excluded_and_noted(self):
        """MAP-UID's shape: the port's own bookkeeping, declared as about no act a
        caller made. Excluded from the row's judgement — and written down, because
        a check that declines to require something leaves a trace."""
        a = self._row("files.fsync", ["CACHE"])
        result = checks.check_recording_class(
            a, self._attr([self._rec("MAP-UID")], subject={"fsync"}), self.CLASSES
        )
        self.assertEqual(result.verdict, checks.PASS, result.detail)
        self.assertTrue(any("no act a caller made" in n for n in result.notes), result.notes)

    # --- the fold is now one case of this, not a branch of its own ----------

    def test_the_fold_leg_reads_the_attributed_records(self):
        """W1's coalescible handling is not a separate window any more: the fold
        counts the covering events attributed to the act under test."""
        a = self._row("files.fold", ["DECISION"], rules={"coalescible": True})
        folded = dict(self._rec("WRITE"), payload={"coalesced_events": 4,
                                                   "coalescing_policy": "FS-WRITE-COALESCING"})
        attr = self._attr([folded], subject={"write"}, other={"open", "close"})
        ok = checks.check_recording_class(
            a, attr, self.CLASSES, coalescing_policies=("FS-WRITE-COALESCING",), subject_acts=4
        )
        self.assertEqual(ok.verdict, checks.PASS, ok.detail)
        uncited = dict(self._rec("WRITE"), payload={"coalesced_events": 4})
        bad = checks.check_recording_class(
            a,
            self._attr([uncited], subject={"write"}, other={"open", "close"}),
            self.CLASSES,
            coalescing_policies=("FS-WRITE-COALESCING",),
            subject_acts=4,
        )
        self.assertEqual(bad.verdict, checks.FAIL)

    def test_no_check_takes_a_bracket_window_any_more(self):
        """Structural: the separate fold window is gone, so no path can attribute
        the coalescible case one way and everything else the other."""
        import inspect

        self.assertNotIn(
            "fold_window", set(inspect.signature(checks.check_recording_class).parameters)
        )
        self.assertNotIn("fold_window", (HARNESS_DIR / "runner.py").read_text())

    def test_the_runner_hands_the_check_a_full_attribution(self):
        """The lenient sequence form exists for this battery, which constructs its
        own cases. The runner must never use it: a bare list means "these are the
        act's records", and deciding that is exactly what §11.4a takes away from
        the bracket."""
        text = (HARNESS_DIR / "runner.py").read_text()
        self.assertIn("checks.Attribution(", text)
        self.assertNotIn("of_subject", text)

    # --- the target's declaration is load-bearing, and it is checked --------

    def test_a_governed_target_that_declares_no_covers_map_is_refused(self):
        """A record source with no vocabulary to read it by cannot be judged, and
        the run REFUSES rather than reporting rows — §11.2b's discipline pointed at
        the target's declaration instead of at its subject."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        spec = json.loads((TARGETS_DIR / "fixture-correct.json").read_text())
        spec.pop("covers_map", None)
        (Path(tmp) / "fixture-correct.json").write_text(json.dumps(spec))
        fixtures.stand_up(tmp)
        with self.assertRaises(targets.VocabularyError) as ctx:
            runner.verify("fixture-correct", HOST, rows_dir=ROWS_DIR,
                          baselines_base=BASELINES_DIR, targets_dir=tmp,
                          row_ids=["files.mkdir"])
        self.assertIn("covers", str(ctx.exception))

    # --- the same thing end to end, through a target that really defers --------

    def test_a_target_that_defers_its_emission_passes_both_rows(self):
        """The whole repair, driven rather than constructed. `fixture-deferred`
        buffers a write's covering decision and appends it at the flush boundary,
        which is where the mount's folded write lands. The write row passes though
        its own bracket held nothing, and the fsync row — CACHE-only, and holding
        that DECISION in its bracket — passes too."""
        fixtures.stand_up(TARGETS_DIR)
        report = runner.verify(
            "fixture-deferred", HOST, rows_dir=ROWS_DIR, baselines_base=BASELINES_DIR,
            targets_dir=TARGETS_DIR, row_ids=["files.write", "files.fsync"],
        )
        by_row = {v.row_id: v for v in report.verdicts}
        self.assertEqual(sorted(by_row), ["files.fsync", "files.write"])
        for row_id, v in by_row.items():
            self.assertEqual(v.verdict, checks.PASS, "%s: %s" % (row_id, report.text()))

    def test_the_deferred_records_really_land_in_a_later_step(self):
        """The fixture is only evidence if it reproduces the defect's mechanism, so
        that is asserted rather than assumed: no covering record lands inside the
        bracket of the write that caused it."""
        fixtures.stand_up(TARGETS_DIR)
        runner.verify("fixture-deferred", HOST, rows_dir=ROWS_DIR,
                      baselines_base=BASELINES_DIR, targets_dir=TARGETS_DIR,
                      row_ids=["files.fsync"])
        target = targets.Target.load("fixture-deferred", TARGETS_DIR)
        recs = target.record_source.since(0)
        deferred = [r for r in recs if r["action"].startswith("fixture-deferred-")]
        self.assertTrue(deferred, "the fixture recorded nothing to defer")
        for r in deferred:
            self.assertEqual(r["payload"]["covers"], "write")
            self.assertIn(r["payload"]["flushed_at"], ("fsync", "fdatasync", "close"))

    def test_a_wrong_covers_map_fails_the_rows_rather_than_passing_them(self):
        """The column proved able to fail end to end: the control fixture with its
        covers map pointed at an act no row drives fails every row it is given,
        which is what makes a RIGHT covers map evidence rather than decoration."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        spec = json.loads((TARGETS_DIR / "fixture-correct.json").read_text())
        from tools.conformance.fixtures import fixture_shim

        spec["covers_map"] = {"inline": {
            a: ["quotactl"] for a in fixture_shim.COVERS_MAP
        }}
        (Path(tmp) / "fixture-correct.json").write_text(json.dumps(spec))
        fixtures.stand_up(tmp)
        report = runner.verify("fixture-correct", HOST, rows_dir=ROWS_DIR,
                               baselines_base=BASELINES_DIR, targets_dir=tmp,
                               row_ids=["files.mkdir", "files.write"])
        self.assertFalse(report.ok)
        for v in report.failed:
            self.assertEqual(v.failed_checks, ["recording-class"])


# ---------------------------------------------------------------------------
# the fence itself
# ---------------------------------------------------------------------------


class TestTheInstrumentNeverAuthorsItsSubject(unittest.TestCase):
    """EP-24D's load-bearing exclusion: ALL of src/ is out of fence. The instrument
    is never repaired by the thing it judges, and never imports it."""

    def test_the_harness_imports_nothing_from_src(self):
        for path in sorted(HARNESS_DIR.glob("*.py")):
            text = path.read_text()
            for banned in ("from kernel", "import kernel", "src.kernel",
                           "from bridge", "import bridge"):
                self.assertNotIn(banned, text, "%s: %s" % (path.name, banned))

    def test_the_probe_stays_stdlib_only(self):
        text = (HARNESS_DIR / "probe.py").read_text()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(("import ", "from ")) and " import " not in line[:6]:
                mod = line.split()[1].split(".")[0]
                self.assertIn(
                    mod,
                    {"errno", "hashlib", "json", "os", "stat", "sys", "tempfile",
                     "ctypes", "fcntl", "struct", "time", "importlib", "shutil"},
                    line,
                )


if __name__ == "__main__":
    unittest.main()
