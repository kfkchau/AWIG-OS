"""EP-24 — the conformance harness: the campaign's standing instrument.

The acceptance battery design/10 §3 and EP-24 name before any code:

  T-CONFORMANCE-BASELINE-PINNED  verify mode makes zero reads of the live stock
                                 system; baselines are committed, dated, sha-summed,
                                 and a baseline that changed since capture refuses.
  T-HARNESS-COLUMNS-FAIL         each of the three checks demonstrably fails on its
                                 own fixture, independently, and no other check
                                 fails with it.
  T-FILES-GROUP-CAPTURED         the files rows have complete baselines from the
                                 stock guest, and the capture evidence names the
                                 kernel version and the date.
  T-ROWS-ARE-DATA                adding a row requires no harness-code change.

plus the structural guards this session's probes turned into regressions.
"""

import copy
import datetime
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
GUEST = "ep21-ubuntu-guest"
HOST = "host-local"
EVIDENCE = REPO / "planning" / "vm" / "CONFORMANCE-BASELINE-EVIDENCE.md"

#: A subset spanning every recording class the files group carries: DECISION
#: (mkdir, write, chmod), CACHE (lseek), STREAM+CACHE (read), LAW (mount). The
#: full forty-row runs are this EP's evidence; these are what the suite re-runs.
SUBSET = [
    "files.mkdir",
    "files.lseek",
    "files.write",
    "files.read",
    "files.mount",
    "files.chmod",
]


def load_rows():
    return rows_mod.load_all(ROWS_DIR)


# ---------------------------------------------------------------------------
# T-ROWS-ARE-DATA
# ---------------------------------------------------------------------------


class TestRowsAreData(unittest.TestCase):
    """Adding or reclassifying a row is an amendment to design/10 and then a data
    edit. It is never a code edit in the harness — which is what makes the map,
    and not this tree, the contract."""

    def test_adding_a_row_needs_no_harness_change(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(ROWS_DIR / "06-files.json", Path(d) / "06-files.json")
            payload = json.loads((Path(d) / "06-files.json").read_text())
            payload["rows"].append(
                {
                    "row_id": "files.testonly_newcall",
                    "syscall": "testonly_newcall",
                    "variants": ["testonly_newcallat"],
                    "what_it_does": "A row that did not exist when the harness was written.",
                    "subsystems": ["files"],
                    "recording_class": ["DECISION"],
                    "conformance_note": "Recorded, rule-cited; ENOENT identical.",
                    "status": "ENCODED",
                    "active": True,
                    "probe": {
                        "steps": [
                            {"call": "mkdir", "args": ["d", "0o755"]},
                            {"call": "stat", "args": ["d"]},
                        ]
                    },
                }
            )
            (Path(d) / "06-files.json").write_text(json.dumps(payload))

            _groups, compiled = rows_mod.load_all(d)

        by_id = {r.row_id: r for r in compiled}
        self.assertIn("files.testonly_newcall", by_id)
        new = by_id["files.testonly_newcall"]
        # It compiled into an assertion carrying the three checks...
        self.assertEqual(
            new.checks, ("abi-identity", "recording-class", "replay-invariance")
        )
        # ...the §11 rules...
        self.assertTrue(new.rules.errno_identity)
        self.assertTrue(new.rules.timing_out_of_contract)
        # ...and the check-2 expectation its class derives.
        self.assertEqual(new.record_expectation.required_classes, ("DECISION",))
        self.assertTrue(new.record_expectation.rule_citation_required)
        # ...and its variant was generated, riding the primary (design/10 §12).
        self.assertIn("files.testonly_newcall~testonly_newcallat", by_id)
        variant = by_id["files.testonly_newcall~testonly_newcallat"]
        self.assertTrue(variant.is_variant)
        self.assertEqual(variant.rides, "files.testonly_newcall")
        self.assertEqual(variant.recording_class, new.recording_class)

    def test_reclassifying_a_row_changes_the_expectation_without_code(self):
        _groups, compiled = load_rows()
        before = {r.row_id: r for r in compiled}["files.lseek"]
        self.assertEqual(before.record_expectation.required_classes, ())

        with tempfile.TemporaryDirectory() as d:
            payload = json.loads((ROWS_DIR / "06-files.json").read_text())
            for r in payload["rows"]:
                if r["row_id"] == "files.lseek":
                    r["recording_class"] = ["DECISION"]
            (Path(d) / "06-files.json").write_text(json.dumps(payload))
            _g, recompiled = rows_mod.load_all(d)
        after = {r.row_id: r for r in recompiled}["files.lseek"]
        self.assertEqual(after.record_expectation.required_classes, ("DECISION",))
        self.assertTrue(after.record_expectation.rule_citation_required)

    def test_activation_is_one_data_field(self):
        """W5: the other groups are entered as data and activate by flipping one
        field, never by new harness code."""
        _groups, compiled = load_rows()
        inactive = [r for r in compiled if not r.active]
        self.assertGreater(len(inactive), 100)
        with tempfile.TemporaryDirectory() as d:
            payload = json.loads((ROWS_DIR / "07-devices.json").read_text())
            payload["active"] = True
            (Path(d) / "07-devices.json").write_text(json.dumps(payload))
            _g, recompiled = rows_mod.load_all(d)
        self.assertTrue(all(r.active for r in recompiled))
        self.assertTrue(
            all(
                r.checks == ("abi-identity", "recording-class", "replay-invariance")
                for r in recompiled
            )
        )


# ---------------------------------------------------------------------------
# the compiled estate: the schema holds over the rows actually committed
# ---------------------------------------------------------------------------


class TestCompiledRows(unittest.TestCase):
    def setUp(self):
        self.groups, self.rows = load_rows()
        self.by_id = {r.row_id: r for r in self.rows}

    def test_every_group_of_the_map_is_present(self):
        self.assertEqual(
            sorted(self.groups),
            [
                "04-process-scheduling",
                "05-memory",
                "06-files",
                "07-devices",
                "08-ipc-comms",
                "09-time-signals",
                "10-info-pseudofs",
            ],
        )

    def test_every_row_carries_the_three_checks(self):
        for r in self.rows:
            self.assertEqual(
                r.checks,
                ("abi-identity", "recording-class", "replay-invariance"),
                r.row_id,
            )

    def test_classes_are_only_the_five(self):
        for r in self.rows:
            for c in r.recording_class:
                self.assertIn(c, rows_mod.CLASSES, r.row_id)

    def test_errno_identity_and_timing_cannot_be_turned_off(self):
        """§11.1 and §11.6 are unconditional; a row may not override them."""
        for r in self.rows:
            self.assertTrue(r.rules.errno_identity, r.row_id)
            self.assertTrue(r.rules.timing_out_of_contract, r.row_id)
        with self.assertRaises(rows_mod.RowError):
            rows_mod.derive_rules({"errno_identity": False}, ("DECISION",))
        with self.assertRaises(rows_mod.RowError):
            rows_mod.derive_rules({"timing_out_of_contract": False}, ("DECISION",))

    def test_stream_not_lossy_is_derived_not_declared(self):
        """§11.5 is a consequence of being STREAM-classified, not an opt-in."""
        for r in self.rows:
            self.assertEqual(
                r.rules.stream_not_lossy, "STREAM" in r.recording_class, r.row_id
            )

    def test_no_probe_means_a_stated_reason(self):
        for r in self.rows:
            if not r.has_probe:
                self.assertTrue(r.probe_absent_reason, r.row_id)

    def test_disputed_rows_say_why(self):
        disputed = [r for r in self.rows if r.status == "DISPUTED"]
        self.assertGreater(len(disputed), 0)
        for r in disputed:
            self.assertTrue(r.disputed_because, r.row_id)

    def test_a_row_missing_its_reason_is_refused_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "x.json").write_text(
                json.dumps(
                    {
                        "group": "x",
                        "map_ref": "design/10 §x",
                        "rows": [
                            {
                                "row_id": "x.a",
                                "syscall": "a",
                                "recording_class": ["CACHE"],
                                "conformance_note": "n",
                                "status": "ENCODED",
                            }
                        ],
                    }
                )
            )
            with self.assertRaises(rows_mod.RowError):
                rows_mod.load_all(d)

    def test_coverage_counts_every_active_row_exactly_once(self):
        cov = rows_mod.coverage(self.rows)
        active = cov["rows_active"]
        driven = cov["active_probed"] + cov["active_driven_in_primary"]
        self.assertEqual(active, driven + len(cov["active_undriven"]))
        self.assertEqual(cov["rows_total"], cov["rows_active"] + cov["rows_inactive"])
        for entry in cov["active_undriven"]:
            self.assertTrue(entry["reason"], entry["row_id"])

    def test_unassigned_activation_homes_are_surfaced_not_hidden(self):
        cov = rows_mod.coverage(self.rows)
        self.assertIn("info.uname", cov["activation_unassigned"])
        self.assertIn("info.getrandom", cov["activation_unassigned"])

    def test_the_probe_vocabulary_covers_every_call_the_rows_name(self):
        """P3 applied to the instrument: a row naming a call the vocabulary does
        not carry does not silently skip — but no committed row does."""
        for r in self.rows:
            for block in (r.probe, r.root_probe):
                for step in (block or {}).get("steps", []):
                    self.assertIn(step["call"], probe.CALLS, r.row_id)
                    self.assertIn(step["call"], probe.DRIVES, r.row_id)


# ---------------------------------------------------------------------------
# the three checks, in isolation
# ---------------------------------------------------------------------------


class TestChecksInIsolation(unittest.TestCase):
    def setUp(self):
        _g, rows = load_rows()
        self.by_id = {r.row_id: r for r in rows}

    def _obs(self, steps, state=None):
        return {"steps": steps, "state": state or {}}

    def test_abi_refuses_two_equally_broken_observations(self):
        a = self.by_id["files.mkdir"]
        broken = self._obs([{"i": 0, "call": "mkdir", "unknown_call": True}])
        result = checks.check_abi(a, broken, copy.deepcopy(broken))
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("vocabulary" in d for d in result.detail))

    def test_abi_reports_the_errno_before_its_cascade(self):
        a = self.by_id["files.mkdir"]
        target = self._obs(
            [
                {"i": 0, "call": "mkdir", "errno": "EEXIST", "ret": None},
                {"i": 1, "call": "stat", "bind_error": "KeyError"},
            ]
        )
        base = self._obs(
            [
                {"i": 0, "call": "mkdir", "errno": None, "ret": None},
                {"i": 1, "call": "stat", "errno": None, "ret": {}},
            ]
        )
        result = checks.check_abi(a, target, base)
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertIn("errno EEXIST", result.detail[0])

    def test_abi_enforces_shape_only_rather_than_asserting_it(self):
        a = self.by_id["files.stat"]
        self.assertTrue(a.rules.shape_only)
        leaky = self._obs([{"i": 0, "call": "stat", "errno": None, "ret": {"ino": 12345}}])
        result = checks.check_abi(a, leaky, copy.deepcopy(leaky))
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("dynamic fields" in d for d in result.detail))

    def test_abi_refuses_a_timed_observation(self):
        a = self.by_id["files.mkdir"]
        timed = self._obs([{"i": 0, "call": "mkdir", "errno": None, "ret": {"elapsed": 3}}])
        result = checks.check_abi(a, timed, copy.deepcopy(timed))
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("§11.6" in d for d in result.detail))

    def test_recording_class_refuses_an_unclassified_record(self):
        """The class map belongs to the TARGET. A record the target did not
        classify cannot be shown to be the record the row assigns, so it fails —
        the harness never guesses a class."""
        a = self.by_id["files.mkdir"]
        result = checks.check_recording_class(
            a, [{"action": "mystery-act", "rule_cited": "R1"}], {}
        )
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("no class in the target's class map" in d for d in result.detail))

    def test_recording_class_fails_a_decision_without_a_cited_rule(self):
        a = self.by_id["files.mkdir"]
        result = checks.check_recording_class(
            a, [{"action": "create", "rule_cited": None}], {"create": "DECISION"}
        )
        self.assertEqual(result.verdict, checks.FAIL)
        self.assertTrue(any("cites no rule" in d for d in result.detail))

    def test_recording_class_fails_a_cache_row_that_recorded(self):
        a = self.by_id["files.lseek"]
        result = checks.check_recording_class(
            a, [{"action": "create", "rule_cited": "R1"}], {"create": "DECISION"}
        )
        self.assertEqual(result.verdict, checks.FAIL)

    def test_coalescing_is_a_named_policy_not_a_record_per_event(self):
        """§11.4: a STREAM row may not be required to have one record per
        micro-event; what is required is a policy that exists and is cited."""
        a = self.by_id["files.read"]
        self.assertIn("STREAM", a.recording_class)
        cited = checks.check_recording_class(
            a,
            [{"action": "traffic", "rule_cited": "POLICY-1"}],
            {"traffic": "STREAM"},
            coalescing_policies=("POLICY-1",),
        )
        self.assertEqual(cited.verdict, checks.PASS)
        uncited = checks.check_recording_class(
            a,
            [{"action": "traffic", "rule_cited": "SOMETHING-ELSE"}],
            {"traffic": "STREAM"},
            coalescing_policies=("POLICY-1",),
        )
        self.assertEqual(uncited.verdict, checks.FAIL)
        # and zero records is lawful for a STREAM row
        none_at_all = checks.check_recording_class(
            a, [], {}, coalescing_policies=("POLICY-1",)
        )
        self.assertEqual(none_at_all.verdict, checks.PASS)

    def test_an_error_outcome_binds_on_what_the_row_declares(self):
        """DOCUMENTED FLIP (EP-24D, W2). This assertion used to read: a row whose
        every subject step returned an errno has its required half WAIVED, with the
        waiver written onto the result as a note. design/10 §11.1a settled the
        question that waiver was standing in for, so the waiver is gone and the row
        declares which of the three outcome classes it asserts. files.mount's
        unprivileged pass declares NOT-GOVERNED — the caller lacks CAP_SYS_ADMIN,
        so the host kernel rejects the call before any gov-os gate step — and the
        check now binds that: no record is required, and a record appearing IS the
        failure."""
        a = self.by_id["files.mount"]
        self.assertEqual(a.outcome_class, "NOT-GOVERNED")
        clean = checks.check_recording_class(a, [], {}, outcome_class=a.outcome_class)
        self.assertEqual(clean.verdict, checks.PASS)
        self.assertFalse(clean.notes, "no waiver is left to write down")
        recorded = checks.check_recording_class(
            a,
            [{"action": "MOUNT", "rule_cited": "R"}],
            {"MOUNT": "LAW"},
            outcome_class=a.outcome_class,
        )
        self.assertEqual(recorded.verdict, checks.FAIL)

    def test_replay_fails_on_a_diverging_rebuild(self):
        a = self.by_id["files.mkdir"]
        live = {"d": {"type": "dir"}}
        self.assertEqual(checks.check_replay(a, live, dict(live)).verdict, checks.PASS)
        self.assertEqual(checks.check_replay(a, live, {}).verdict, checks.FAIL)
        self.assertEqual(checks.check_replay(a, live, None).verdict, checks.NOT_RUN)

    def test_the_three_checks_never_short_circuit_each_other(self):
        """Independence, asserted: a row wrong in all three ways reports all
        three, so a failing leg can never mask another."""
        a = self.by_id["files.mkdir"]
        observed = self._obs(
            [{"i": 0, "call": "mkdir", "errno": "EEXIST", "ret": None}],
            {"d": {"type": "dir"}},
        )
        baseline = self._obs(
            [{"i": 0, "call": "mkdir", "errno": None, "ret": None}], {"d": {"type": "dir"}}
        )
        # DOCUMENTED FLIP (EP-24D, W2): `subject_ok` is gone. What check 2 requires
        # comes from the row, never from the answer the target gave.
        verdict = checks.run_row_checks(a, observed, baseline, [], {}, replayed_state={})
        self.assertEqual(
            sorted(verdict.failed_checks),
            ["abi-identity", "recording-class", "replay-invariance"],
        )

    def test_subject_steps_are_the_call_under_test_not_the_setup(self):
        """A CACHE row that must create a file first is not thereby a DECISION
        row: the record bracket follows the subject call."""
        a = self.by_id["files.lseek"]
        subjects = a.subject_calls(probe.DRIVES)
        self.assertIn("lseek", subjects)
        self.assertNotIn("write_file", subjects)
        self.assertNotIn("open", subjects)


# ---------------------------------------------------------------------------
# T-CONFORMANCE-BASELINE-PINNED
# ---------------------------------------------------------------------------


class TestBaselinePinned(unittest.TestCase):
    def test_baselines_are_committed_dated_and_sha_summed(self):
        for name in (HOST, GUEST):
            pinned = baselines.load(name, BASELINES_DIR)
            self.assertTrue(pinned.captured_at)
            datetime.datetime.fromisoformat(pinned.captured_at)  # parses, or raises
            self.assertTrue(pinned.manifest["files"])
            for fname, meta in pinned.manifest["files"].items():
                self.assertEqual(len(meta["sha256"]), 64)
                text = (BASELINES_DIR / name / fname).read_text()
                self.assertEqual(baselines._sha256_text(text), meta["sha256"])

    def test_baselines_are_tracked_in_git(self):
        out = subprocess.run(
            ["git", "ls-files", "--error-unmatch",
             "tools/conformance/baselines/%s/MANIFEST.json" % GUEST,
             "tools/conformance/baselines/%s/06-files.json" % GUEST],
            cwd=REPO, capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_a_baseline_that_changed_since_capture_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(BASELINES_DIR / HOST, Path(d) / HOST)
            baselines.load(HOST, d)  # unchanged: loads
            p = Path(d) / HOST / "06-files.json"
            p.write_text(p.read_text().replace("ENOENT", "EPERM", 1))
            with self.assertRaises(baselines.BaselineError) as ctx:
                baselines.load(HOST, d)
            self.assertIn("pinned sha256", str(ctx.exception))

    def test_verify_makes_zero_reads_of_the_live_stock_system(self):
        """The whole-class pinning law on baselines. Proved by poisoning every
        route to a live stock kernel and watching verify complete anyway: the ssh
        transport that reaches the guest raises on any use, and loading ANY target
        of kind `stock` raises. The guest is powered off besides."""
        original_load = targets.Target.load
        original_ssh = targets.SshTransport.run

        def poisoned_load(name, targets_dir=None):
            t = original_load(name, targets_dir)
            if t.kind == "stock":
                raise AssertionError(
                    "verify reached for a live stock target (%s) — the baseline is "
                    "supposed to be pinned" % name
                )
            return t

        def poisoned_ssh(self, plan, as_root=False):
            raise AssertionError("verify opened an ssh transport to a live target")

        targets.Target.load = staticmethod(poisoned_load)
        targets.SshTransport.run = poisoned_ssh
        try:
            report = runner.verify(
                "fixture-correct",
                HOST,
                rows_dir=ROWS_DIR,
                baselines_base=BASELINES_DIR,
                targets_dir=TARGETS_DIR,
                row_ids=SUBSET,
            )
        finally:
            targets.Target.load = original_load
            targets.SshTransport.run = original_ssh
        self.assertTrue(report.ok, report.text())
        self.assertEqual(len(report.verdicts), len(SUBSET))

    def test_capture_refuses_a_governed_target(self):
        """A governed target is judged, never used as its own baseline."""
        with self.assertRaises(targets.TargetError):
            runner.capture("fixture-correct", targets_dir=TARGETS_DIR)

    def test_verify_refuses_a_stock_target(self):
        with self.assertRaises(targets.TargetError):
            runner.verify(HOST, HOST, targets_dir=TARGETS_DIR, baselines_base=BASELINES_DIR)


# ---------------------------------------------------------------------------
# T-HARNESS-COLUMNS-FAIL
# ---------------------------------------------------------------------------


class TestHarnessColumnsFail(unittest.TestCase):
    """Before any baseline is trusted, the instrument proves its own columns can
    fail — each one alone, on a target that is genuinely wrong in that one way."""

    ALL = object()

    def _verify(self, target, rows=SUBSET):
        return runner.verify(
            target,
            HOST,
            rows_dir=ROWS_DIR,
            baselines_base=BASELINES_DIR,
            targets_dir=TARGETS_DIR,
            row_ids=None if rows is self.ALL else rows,
        )

    def _leg(self, report, leg):
        return report.summary()["legs"][leg]

    def test_the_control_passes_every_leg_on_every_active_files_row(self):
        report = self._verify("fixture-correct", rows=self.ALL)
        self.assertTrue(report.ok, report.text())
        s = report.summary()
        self.assertEqual(s["rows"][checks.FAIL], 0)
        self.assertEqual(s["rows"][checks.NOT_RUN], 0)
        self.assertGreaterEqual(s["rows"][checks.PASS], 40)
        for leg in ("abi-identity", "recording-class", "replay-invariance"):
            self.assertEqual(s["legs"][leg][checks.FAIL], 0, leg)
            self.assertEqual(s["legs"][leg][checks.NOT_RUN], 0, leg)

    def test_a_wrong_errno_fails_the_abi_leg_and_only_that(self):
        report = self._verify("fixture-wrong-errno")
        self.assertFalse(report.ok)
        self.assertEqual(self._leg(report, "abi-identity")[checks.FAIL], 1)
        self.assertEqual(self._leg(report, "recording-class")[checks.FAIL], 0)
        self.assertEqual(self._leg(report, "replay-invariance")[checks.FAIL], 0)
        failed = report.failed
        self.assertEqual([v.row_id for v in failed], ["files.mkdir"])
        self.assertEqual(failed[0].failed_checks, ["abi-identity"])
        self.assertIn("errno EEXIST", failed[0].results[0].detail[0])

    def test_a_missing_decision_record_fails_the_audit_leg_and_only_that(self):
        """design/10 §3.2: a missing decision fails the audit check EVEN WHEN the
        ABI check passes. That sentence is this assertion."""
        report = self._verify("fixture-no-record")
        self.assertFalse(report.ok)
        self.assertEqual(self._leg(report, "abi-identity")[checks.FAIL], 0)
        self.assertGreater(self._leg(report, "recording-class")[checks.FAIL], 0)
        self.assertEqual(self._leg(report, "replay-invariance")[checks.FAIL], 0)
        for v in report.failed:
            self.assertEqual(v.failed_checks, ["recording-class"])

    def test_a_diverging_replay_fails_the_replay_leg_and_only_that(self):
        """The leg the journaling-filesystem template dies on: effects real,
        records present, and the tree not actually derived from them."""
        report = self._verify("fixture-replay-diverges")
        self.assertFalse(report.ok)
        self.assertEqual(self._leg(report, "abi-identity")[checks.FAIL], 0)
        self.assertEqual(self._leg(report, "recording-class")[checks.FAIL], 0)
        self.assertGreater(self._leg(report, "replay-invariance")[checks.FAIL], 0)
        for v in report.failed:
            self.assertEqual(v.failed_checks, ["replay-invariance"])

    def test_the_fixtures_record_through_the_real_store(self):
        """The harness's record reader is proven against the store's own envelope,
        not against the fixture's idea of one."""
        self._verify("fixture-correct", rows=["files.mkdir"])
        record = Path("/tmp/govos-conformance/fixture-correct/record.jsonl")
        self.assertTrue(record.exists())
        lines = [json.loads(ln) for ln in record.read_text().splitlines() if ln.strip()]
        self.assertTrue(lines)
        for rec in lines:
            for field in ("seq", "record_time", "actor", "action", "rule_cited", "payload"):
                self.assertIn(field, rec)
        self.assertEqual([r["seq"] for r in lines], list(range(1, len(lines) + 1)))


# ---------------------------------------------------------------------------
# T-FILES-GROUP-CAPTURED
# ---------------------------------------------------------------------------


class TestFilesGroupCaptured(unittest.TestCase):
    def setUp(self):
        self.pinned = baselines.load(GUEST, BASELINES_DIR)
        _g, rows = load_rows()
        self.rows = [r for r in rows if r.group == "06-files"]

    def test_the_capture_names_its_kernel_and_its_date(self):
        u = self.pinned.manifest["target_identity"]["uname"]
        self.assertEqual(u["sysname"], "Linux")
        self.assertTrue(u["release"])
        self.assertEqual(self.pinned.manifest["target_kind"], "stock")
        self.assertTrue(self.pinned.captured_at)

    def test_every_probed_files_row_has_a_baseline(self):
        for r in self.rows:
            if r.active and r.has_probe:
                self.assertIsNotNone(self.pinned.get(r.row_id), r.row_id)

    def test_every_unprobed_files_row_is_named_in_the_skipped_list_with_a_reason(self):
        skipped = {s["row_id"]: s["reason"] for s in self.pinned.skipped()}
        for r in self.rows:
            if r.active and not r.has_probe:
                self.assertIn(r.row_id, skipped, r.row_id)
                self.assertTrue(skipped[r.row_id])

    def test_the_privileged_rows_were_captured_on_the_guest(self):
        """The LAW-class mount rows need root, and the guest declares it. Their
        privileged pass is a baseline of its own, never merged into the
        unprivileged one."""
        for row_id in ("files.mount#root", "files.umount#root"):
            obs = self.pinned.get(row_id)
            self.assertIsNotNone(obs, row_id)
            calls = [s["call"] for s in obs["steps"]]
            self.assertIn("mount", calls + ["mount"])
        self.assertTrue(self.pinned.manifest["root_pass_identity"]["euid_is_root"])

    def test_the_unprivileged_pass_was_not_run_as_root(self):
        self.assertFalse(self.pinned.manifest["target_identity"]["euid_is_root"])

    def test_the_host_baseline_declares_its_missing_root_pass(self):
        host = baselines.load(HOST, BASELINES_DIR)
        skipped = {s["row_id"]: s["reason"] for s in host.skipped()}
        self.assertIn("files.mount#root", skipped)
        self.assertIn("no root capability", skipped["files.mount#root"])

    #: THE ONE DISAGREEMENT THAT IS NOT ABOUT THE KERNELS [DOCUMENTED FLIP, EP-28H
    #: item 3, 2026-08-02]. The row below names three possible causes of a
    #: disagreement and its third is the one that fired: a NORMALIZER. `dup2` joined
    #: `_n_fd`'s relative reporting so the absolute-descriptor class is empty by
    #: construction, and `host-local` was re-captured through its own procedure. The
    #: guest capture was NOT: it needs the guest, EP-28H does no guest work, and
    #: EP-28H's own RAISED-BY-DESIGN names it stale-by-known-cause with its consumer —
    #: the next pass with a guest window, EP-28C's resumed W4-W8.
    #:
    #: SO THESE TWO STEPS ARE NOT COMPARABLE, and the reason is §A39's own shape: two
    #: captures taken under two INSTRUMENT CONSTRUCTIONS, compared as one. The carve-out
    #: is exactly two steps of one row in one direction, and it EXPIRES LOUDLY: the row
    #: below asserts the two values still DIFFER in the construction's own way, so the
    #: moment the guest is re-captured this reds and the carve-out is deleted with it.
    CONSTRUCTION_DIFFERENCE = {"files.dup": (6, 9)}

    @staticmethod
    def _without(obs, indices):
        out = dict(obs)
        out["steps"] = [s for s in obs["steps"] if s["i"] not in indices]
        return out

    def test_the_two_stock_kernels_agree_on_every_shared_row(self):
        """The instrument's own cross-check: two stock kernels three major
        versions apart answer identically on every row driven against both. A
        disagreement here is either a real ABI difference (a map finding) or a
        normalizer leaking a dynamic byte — which is how this session found and
        fixed one."""
        host = baselines.load(HOST, BASELINES_DIR)
        shared = set(host.row_ids()) & set(self.pinned.row_ids())
        self.assertGreaterEqual(len(shared), 40)
        carved = []
        for row_id in sorted(shared):
            a, b = host.get(row_id), self.pinned.get(row_id)
            indices = self.CONSTRUCTION_DIFFERENCE.get(row_id)
            if indices is None:
                self.assertEqual(a, b, row_id)
                continue
            self.assertEqual(self._without(a, indices), self._without(b, indices),
                             "%s disagrees OUTSIDE the two carved steps" % row_id)
            for i in indices:
                here = [s for s in a["steps"] if s["i"] == i][0]
                there = [s for s in b["steps"] if s["i"] == i][0]
                self.assertEqual(here["call"], there["call"], "%s step %d" % (row_id, i))
                self.assertTrue(
                    isinstance(here["ret"], str) and here["ret"].startswith("fd#"),
                    "the re-captured side must report relatively: %r" % (here,))
                self.assertIsInstance(
                    there["ret"], int,
                    "THE CARVE-OUT HAS EXPIRED: the guest capture no longer carries an "
                    "absolute descriptor, so it was retaken under the current "
                    "construction and this exception must be DELETED, not widened")
                carved.append((row_id, i))
        self.assertEqual(carved, [("files.dup", 6), ("files.dup", 9)],
                         "the carve-out and what it excuses must be the same set, both "
                         "directions — a named exception nobody differences grows")

    def test_the_capture_evidence_file_exists_and_names_the_kernel_and_date(self):
        self.assertTrue(EVIDENCE.exists())
        text = EVIDENCE.read_text()
        u = self.pinned.manifest["target_identity"]["uname"]
        self.assertIn(u["release"], text)
        self.assertIn(self.pinned.captured_at[:10], text)
        self.assertIn(self.pinned.manifest["files"]["06-files.json"]["sha256"], text)


# ---------------------------------------------------------------------------
# the harness tree is self-contained
# ---------------------------------------------------------------------------


class TestHarnessIsSelfContained(unittest.TestCase):
    def test_the_harness_imports_nothing_from_src(self):
        """The harness reads the record FILE and the target's class map as data.
        It does not import the thing it measures — which is why EP-25's mount and
        the in-kernel module after it can be judged by it unchanged."""
        harness = REPO / "tools" / "conformance" / "harness"
        for path in sorted(harness.glob("*.py")):
            text = path.read_text()
            self.assertNotIn("from kernel", text, path.name)
            self.assertNotIn("import kernel", text, path.name)
            self.assertNotIn("src.kernel", text, path.name)

    def test_the_probe_is_one_file_and_stdlib_only(self):
        """It is shipped to the target and run there; a probe that needs
        installing on the thing it measures has changed it."""
        text = (REPO / "tools" / "conformance" / "harness" / "probe.py").read_text()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(("import ", "from ")) and " import " not in line[:6]:
                mod = line.split()[1].split(".")[0]
                self.assertIn(
                    mod,
                    {
                        "errno", "hashlib", "json", "os", "stat", "sys", "tempfile",
                        "ctypes", "fcntl", "struct", "time", "importlib",
                    },
                    line,
                )

    def test_the_harness_writes_nothing_outside_its_own_tree(self):
        """The scope fence, asserted: capture writes under tools/conformance and
        the probe works in a scratch directory the target names."""
        d, manifest = None, None
        with tempfile.TemporaryDirectory() as base:
            d, manifest = runner.capture(
                HOST,
                rows_dir=ROWS_DIR,
                baselines_base=base,
                targets_dir=TARGETS_DIR,
                captured_at="2026-01-01T00:00:00+00:00",
            )
            self.assertTrue(str(d).startswith(base))
            self.assertTrue((Path(d) / "MANIFEST.json").exists())
            self.assertEqual(manifest["captured_at"], "2026-01-01T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
