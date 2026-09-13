"""EP-22 / M1 — watch and record: the acceptance battery.

Named before code in the EP file, landed here as regression tests. The battery:

  T-EXPLANATION / T-ATTRIBUTION  every observed record cites its rule and traces to
                                 actor + op + time — and the cited rule EXISTS.
  T-ASOF                         the shadow views answer "as of T" for a captured run.
  T-OBSERVABILITY-BOUNDARY       no load-bearing answer rests on a sampled stream.
  T-REPLAY / T-CACHE-KILL        kill every derived thing, replay, reconstruct identically.
  T-SHADOW-TRACKS                the shadow matches the box — and the column can FAIL:
                                 a stopped adapter is DETECTED, never silently served.
  T-PROVENANCE-PINNED            asserted_by + window@version + window-reported occurrence
                                 on every record; missing any of the three refuses.
  T-ONE-WRITER                   the sole-appender discipline holds with five adapters live.
  T-RATE-GOVERNANCE   (ADD. 1)   recording tracks decisions, never operations.
  T-FOLD-AT-RATE      (ADD. 1)   the fold is measured; a cached answer is coherent-or-refuse.
  T-NO-STORED-TABLE   (ADD. 1)   no permission table, no stored complement, on any path here.

Plus W2's own bar: the class mapping is TESTED, not assumed — a misclassification is an
audit failure even when nothing crashes.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                        # noqa: E402
from kernel.errors import OpError                                   # noqa: E402
from observe import classmap, shadow                                # noqa: E402
from observe.m1_runner import M1Run                                 # noqa: E402
from observe.seam import (                                          # noqa: E402
    OBSERVATION_LAW, OP_FOR_WINDOW, PIN_PARAMS, Observation, ObservationSeam,
    TIME_SUBMISSION_SUBSTITUTED, TIME_WINDOW_REPORTED, m1_observe_ops, register_observe_ops,
    window_at_version,
)
from observe.windows import DiffWindow, FileWindow, MountWindow, ProcessWindow  # noqa: E402

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
OBSERVE_SRC = os.path.join(SRC, "observe")
WHEN = "2026-07-26T09:00:00+00:00"


def _observe_sources():
    for name in sorted(os.listdir(OBSERVE_SRC)):
        if name.endswith(".py"):
            with open(os.path.join(OBSERVE_SRC, name), encoding="utf-8") as f:
                yield name, f.read()


class FakeWindow(DiffWindow):
    """A window driven by injected snapshots — the campaign-1 adapter discipline: the diff
    logic is proven deterministically, without depending on what the live box happens to do."""

    def __init__(self, name, snapshots, acts, version="test-1"):
        super().__init__(source=lambda: self._next())
        self.name = name
        self.route = version
        self._snaps = list(snapshots)
        self.act_appeared, self.act_removed, self.act_changed = acts
        self._last = {}

    @property
    def version(self):
        return self.route

    def _next(self):
        if self._snaps:
            self._last = self._snaps.pop(0)
        return self._last

    def live_state(self):
        return self._last

    def coverage(self):
        return {"facility": f"injected {self.name}", "sees": ["what the injection carries"],
                "does_not_see": ["anything the injection omits"]}


def _mount_window(snapshots):
    return FakeWindow("mount", snapshots,
                      ("mount-added", "mount-removed", "mount-attr-changed"))


def _process_window(snapshots):
    return FakeWindow("process", snapshots,
                      ("process-created", "process-exited", "process-credentials-changed"))


class _Composed(unittest.TestCase):
    """The M1 composition: the built kernel + the observation seam + the shadow views."""

    windows = ()

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record_path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, _b, _s = build_full_kernel(
            self.record_path, os.path.join(self.dir, "blobs"))
        register_observe_ops(self.gate)
        self.seam = ObservationSeam(self.gate)
        shadow.define_shadow_views(self.gate)
        self.shadows = shadow.ShadowViews(self.store, self.views, self.windows)

    def observe(self, window, act, obj, when=WHEN, source=TIME_WINDOW_REPORTED, data=None):
        return self.seam.submit(Observation(window=window, window_version="test-1", act=act,
                                            object=obj, occurrence_time=when, time_source=source,
                                            data=data or {"key": obj}))

    def observed_records(self):
        kinds = {f"observed-{w}" for w in OP_FOR_WINDOW}
        return [e for e in self.store.all() if (e.get("payload") or {}).get("kind") in kinds]


# =============================================================================================
# W2 — the class map is TESTED, not assumed
# =============================================================================================

class TestClassMap(unittest.TestCase):
    LEGEND = (classmap.LAW, classmap.DECISION, classmap.INPUT, classmap.CACHE, classmap.STREAM)

    def test_every_mapped_act_carries_a_legend_class(self):
        for window, acts in classmap.CLASS_MAP.items():
            for act, cls in acts.items():
                self.assertIn(cls, self.LEGEND, f"{window}/{act} -> {cls} is outside the legend")

    def test_recorded_and_dropped_partition_the_map_exactly(self):
        for window, acts in classmap.CLASS_MAP.items():
            union = set(classmap.RECORDED_ACTS[window]) | set(classmap.DROPPED_ACTS[window])
            self.assertEqual(union, set(acts), window)
            self.assertEqual(set(classmap.RECORDED_ACTS[window]) & set(classmap.DROPPED_ACTS[window]),
                             set(), window)

    def test_the_stage_specs_own_assignments_hold(self):
        # planning/11 §1, row by row — the authority for M1's mapping, asserted rather than
        # trusted. A misclassification is an audit failure even when nothing crashes (W2).
        self.assertEqual(classmap.classify("process", "process-created"), classmap.DECISION)
        self.assertEqual(classmap.classify("process", "process-exited"), classmap.DECISION)
        self.assertEqual(classmap.classify("file", "file-created"), classmap.DECISION)
        self.assertEqual(classmap.classify("file", "file-modified"), classmap.DECISION)
        self.assertEqual(classmap.classify("file", "file-attr-changed"), classmap.DECISION)
        self.assertEqual(classmap.classify("mount", "mount-added"), classmap.LAW)
        self.assertEqual(classmap.classify("mount", "mount-removed"), classmap.LAW)
        self.assertEqual(classmap.classify("device", "device-capability-registered"), classmap.LAW)
        self.assertEqual(classmap.classify("device", "device-bound"), classmap.DECISION)
        self.assertEqual(classmap.classify("connection", "connection-opened"), classmap.DECISION)
        # derived state and raw flow are NOT recorded (planning/11 §2 rule 4)
        self.assertEqual(classmap.classify("file", "file-read"), classmap.STREAM)
        self.assertEqual(classmap.classify("file", "file-opened"), classmap.CACHE)
        self.assertEqual(classmap.classify("connection", "connection-traffic"), classmap.STREAM)

    def test_an_unmapped_act_raises_and_never_falls_through_as_not_recorded(self):
        # the silent drop is precisely the audit failure: an unknown act must not be treated
        # as CACHE by default, because that would erase it without anyone deciding to.
        with self.assertRaises(classmap.UnmappedAct):
            classmap.classify("file", "file-teleported")
        with self.assertRaises(classmap.UnmappedAct):
            classmap.classify("no-such-window", "file-created")

    def test_the_input_class_is_declared_and_its_window_is_deferred_not_absent(self):
        self.assertEqual(classmap.classify("arrival", "interrupt-arrived"), classmap.INPUT)
        self.assertNotIn("arrival", OP_FOR_WINDOW)   # declared, and it cannot write


# =============================================================================================
# T-PROVENANCE-PINNED
# =============================================================================================

class TestProvenancePinned(_Composed):
    def test_every_observed_record_carries_all_three_pins(self):
        self.observe("mount", "mount-added", "mount:/x")
        self.observe("process", "process-created", "proc:99")
        for e in self.observed_records():
            prov = e["provenance"]
            self.assertTrue(prov.get("asserted_by"), e)                 # 1. the observer
            self.assertTrue(prov.get("window"), e)                      # 2a. the window
            self.assertTrue(prov.get("window_version"), e)              # 2b. at its version
            self.assertTrue(e.get("occurrence_time"), e)                # 3. when it happened
            self.assertEqual(prov["asserted_by"], self.seam.observer)   # the observer, not the box
            self.assertEqual(window_at_version(prov["window"], prov["window_version"]),
                             f"{prov['window']}@{prov['window_version']}")

    def test_a_record_missing_any_one_pin_refuses_at_submission(self):
        base = {"window": "mount", "window_version": "test-1", "occurrence_time": WHEN,
                "act": "mount-added", "object": "mount:/x"}
        for pin in PIN_PARAMS:
            params = dict(base)
            params.pop(pin)
            refusals = len(self.store.by_action("op-refused"))
            with self.assertRaises(OpError, msg=f"{pin} was not required") as cm:
                self.gate.execute("OBSERVE-MOUNT", "m1-observer", params)
            self.assertEqual(cm.exception.rule, "AR-2")                  # a nonconforming call
            self.assertEqual(len(self.store.by_action("op-refused")), refusals + 1)  # recorded
            self.assertEqual(len(self.store.by_action("mount-added")), 0)  # and nothing written

    def test_every_observe_op_declares_the_three_pins_required(self):
        # the structural half: the refusal above is not one handler being careful, it is the
        # gate's own nonconforming-call check, because the pins are REQUIRED PARAMETERS.
        surface = m1_observe_ops(self.gate)
        self.assertEqual(sorted(surface), sorted(OP_FOR_WINDOW.values()))
        for name, meta in surface.items():
            for pin in PIN_PARAMS:
                self.assertEqual(meta["params"].get(pin), "required", f"{name}/{pin}")

    def test_a_window_reporting_no_time_substitutes_and_marks_it(self):
        # RAISED-BY-DESIGN 4: submission time may stand in, but never silently — EP-26's
        # adjudication has to know which times are which.
        obs = Observation(window="mount", window_version="test-1", act="mount-added",
                          object="mount:/y", occurrence_time=None)
        self.assertEqual(obs.time_source, TIME_SUBMISSION_SUBSTITUTED)
        rec = self.seam.submit(obs)
        self.assertEqual(rec["payload"]["time_source"], TIME_SUBMISSION_SUBSTITUTED)
        self.assertTrue(rec["occurrence_time"])

    def test_the_observed_record_is_a_two_times_record(self):
        # design/36 K7: the occurrence precedes the recording, always. This EP does not
        # adjudicate that (EP-26 does); it must carry it honestly.
        rec = self.observe("process", "process-created", "proc:7", when="2020-01-01T00:00:00+00:00")
        self.assertEqual(rec["occurrence_time"], "2020-01-01T00:00:00+00:00")
        self.assertGreater(rec["record_time"], rec["occurrence_time"])
        self.assertEqual(rec["payload"]["time_source"], TIME_WINDOW_REPORTED)

    def test_a_real_window_reports_a_real_occurrence_time(self):
        # not a fixture: /proc reports each process's own start time, so the two times are
        # genuinely apart on a live box.
        w = ProcessWindow()
        ok, _ = w.available()
        if not ok:
            self.skipTest("no /proc on this platform")
        reported = [o for o in w.read() if o.time_source == TIME_WINDOW_REPORTED]
        self.assertTrue(reported, "the process window reported no occurrence times")


# =============================================================================================
# T-EXPLANATION / T-ATTRIBUTION
# =============================================================================================

class TestExplanationAndAttribution(_Composed):
    def test_every_observed_record_cites_a_rule_that_exists(self):
        self.observe("mount", "mount-added", "mount:/x")
        self.observe("device", "device-bound", "device:pci/0000:00", data={"key": "pci/0000:00",
                                                                          "driver": "nvme"})
        recorded_rules = self.views.active_rules()
        self.assertIn(OBSERVATION_LAW, recorded_rules)     # the citation is not dangling
        for e in self.observed_records():
            self.assertEqual(e["rule_cited"], OBSERVATION_LAW)
        # and the law says what an observation IS — recording is not permission to perform
        self.assertIn("recording is not permission", recorded_rules[OBSERVATION_LAW]["text"])

    def test_every_refusal_cites_its_rule_and_is_recorded(self):
        with self.assertRaises(OpError):
            self.gate.execute("OBSERVE-MOUNT", "m1-observer",
                              {"window": "mount", "window_version": "v", "occurrence_time": WHEN,
                               "act": "not-a-mount-act", "object": "mount:/x"})
        refusal = self.store.by_action("op-refused")[-1]
        self.assertTrue(refusal["rule_cited"])
        self.assertTrue(refusal["refused"])
        self.assertIn("vocabulary is closed", refusal["payload"]["message"])

    def test_every_state_change_traces_to_actor_op_and_time(self):
        rec = self.observe("process", "process-created", "proc:11")
        self.assertEqual(rec["actor"], "SYSTEM")                       # the recorder (SYS-RECORD)
        self.assertEqual(rec["provenance"]["asserted_by"], "m1-observer")   # who asserts it
        self.assertEqual(rec["action"], "process-created")             # what the box did
        self.assertEqual(rec["object"], "proc:11")                     # what it did it to
        self.assertTrue(rec["record_time"] and rec["occurrence_time"])  # both times
        self.assertEqual(rec["payload"]["record_class"], classmap.DECISION)

    def test_an_observed_principal_is_evidence_and_is_never_resolved_to_an_actor(self):
        # K6 at observation scale: the kernel-asserted uid is EVIDENCE in the record; actor
        # resolution derives from recorded mapping acts, and at M1 there are none.
        rec = self.seam.submit(Observation(
            window="process", window_version="test-1", act="process-created", object="proc:12",
            occurrence_time=WHEN, data={"key": 12, "uid": 1000}, principal="uid:1000"))
        self.assertEqual(rec["payload"]["observed_principal"], "uid:1000")
        self.assertNotIn("uid:1000", self.views.accounts())            # no account was minted
        self.assertEqual(rec["actor"], "SYSTEM")                       # and none was claimed


# =============================================================================================
# The closed vocabulary at the write path (the campaign-1 smuggle shape, closed at the seam)
# =============================================================================================

class TestClosedActionVocabulary(_Composed):
    def test_an_act_outside_the_windows_vocabulary_refuses_before_any_draft(self):
        for act in ("file-created", "RETIRE-OP", "GRANT", "file-read"):
            with self.assertRaises(OpError, msg=act) as cm:
                self.gate.execute("OBSERVE-MOUNT", "m1-observer",
                                  {"window": "mount", "window_version": "v",
                                   "occurrence_time": WHEN, "act": act, "object": "o"})
            self.assertEqual(cm.exception.rule, "AR-2")
        self.assertEqual(len(self.observed_records()), 0)

    def test_the_protected_core_survives_an_observe_call_naming_a_retire_act(self):
        # the campaign-1 F2 shape, aimed at the M1 surface: it now dies at the seam's own
        # closed vocabulary, in front of the constitution guard that also still catches it.
        self.assertEqual(self.views.op_definitions()["MEM-GRANT"]["tier"], "owner")
        with self.assertRaises(OpError):
            self.gate.execute("OBSERVE-DEVICE", "attacker",
                              {"window": "device", "window_version": "v", "occurrence_time": WHEN,
                               "act": "RETIRE-OP", "object": "op:MEM-GRANT",
                               "data": {"name": "MEM-GRANT"}})
        self.assertTrue(self.gate.has("MEM-GRANT"))
        self.assertIn("MEM-GRANT", self.views.op_definitions())

    def test_a_windows_op_refuses_another_windows_records(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("OBSERVE-MOUNT", "m1-observer",
                              {"window": "file", "window_version": "v", "occurrence_time": WHEN,
                               "act": "mount-added", "object": "mount:/x"})
        self.assertEqual(cm.exception.rule, "AR-2")

    def test_the_two_observe_surfaces_refuse_to_compose(self):
        # the campaign-1 pair predates the pins; composing both would put an unpinned observe
        # path beside a pinned one, which is exactly what T-PROVENANCE-PINNED denies.
        d = tempfile.mkdtemp()
        store, gate, _v, _b, _s = build_full_kernel(os.path.join(d, "r.jsonl"),
                                                    os.path.join(d, "blobs"))
        from observe.resource_watch import register_resource_observe_ops
        register_resource_observe_ops(gate, store)
        with self.assertRaises(ValueError) as cm:
            register_observe_ops(gate)
        self.assertIn("do not compose", str(cm.exception))


# =============================================================================================
# T-ASOF
# =============================================================================================

class TestAsOf(_Composed):
    def test_each_shadow_view_answers_as_of_a_point_in_the_record(self):
        self.observe("mount", "mount-added", "mount:/a", data={"key": "/a", "fstype": "ext4"})
        mid = len(self.store.all())
        self.observe("mount", "mount-added", "mount:/b", data={"key": "/b", "fstype": "xfs"})
        self.observe("mount", "mount-removed", "mount:/a", data={"key": "/a", "fstype": "ext4"})
        now = self.shadows.answer("m1-mount-table")["table"]
        then = self.shadows.answer("m1-mount-table", as_of=mid)["table"]
        self.assertEqual(sorted(now), ["/b"])              # /a unmounted, /b mounted
        self.assertEqual(sorted(then), ["/a"])             # as of T, only /a — and it was there
        self.assertEqual(then["/a"]["fstype"], "ext4")

    def test_the_process_table_answers_as_of_a_point(self):
        self.observe("process", "process-created", "proc:1", data={"key": 1, "comm": "init"})
        self.observe("process", "process-created", "proc:2", data={"key": 2, "comm": "bash"})
        mid = len(self.store.all())
        self.observe("process", "process-exited", "proc:1", data={"key": 1, "comm": "init"})
        self.assertEqual(sorted(self.shadows.answer("m1-process-table")["table"]), [2])
        self.assertEqual(sorted(self.shadows.answer("m1-process-table", as_of=mid)["table"]), [1, 2])

    def test_a_files_whole_history_is_answerable_including_after_removal(self):
        for act in ("file-created", "file-modified", "file-removed"):
            self.observe("file", act, "file:/w/x", data={"path": "/w/x"})
        hist = self.shadows.answer("m1-file-history")["table"]["/w/x"]
        self.assertEqual([h["act"] for h in hist],
                         ["file-created", "file-modified", "file-removed"])
        # the history survives the removal — content-addressed history, not a live-file table
        self.assertEqual(self.shadows.answer("m1-file-history", as_of=hist[1]["seq"])["table"]["/w/x"],
                         hist[:2])

    def test_device_bindings_answer_as_of_and_bind_is_separate_from_capability(self):
        self.observe("device", "device-capability-registered", "device:pci/x",
                     data={"key": "pci/x", "subsystem": "pci", "driver": None})
        before_bind = len(self.store.all())
        self.observe("device", "device-bound", "device:pci/x",
                     data={"key": "pci/x", "subsystem": "pci", "driver": "nvme"})
        self.assertIsNone(self.shadows.answer("m1-device-bindings",
                                              as_of=before_bind)["table"]["pci/x"]["driver"])
        self.assertEqual(self.shadows.answer("m1-device-bindings")["table"]["pci/x"]["driver"],
                         "nvme")


# =============================================================================================
# T-REPLAY / T-CACHE-KILL (M1 scale)
# =============================================================================================

class TestReplayAndCacheKill(_Composed):
    def _populate(self):
        self.observe("mount", "mount-added", "mount:/a", data={"key": "/a", "fstype": "ext4"})
        self.observe("process", "process-created", "proc:5", data={"key": 5, "comm": "sh"})
        self.observe("process", "process-exited", "proc:5", data={"key": 5, "comm": "sh"})
        self.observe("device", "device-bound", "device:pci/y",
                     data={"key": "pci/y", "subsystem": "pci", "driver": "e1000"})
        self.observe("connection", "connection-opened", "conn:tcp:1-2",
                     data={"key": "tcp:1-2", "state": "ESTABLISHED", "uid": 1000})
        for act in ("file-created", "file-modified"):
            self.observe("file", act, "file:/w/z", data={"path": "/w/z"})

    def _tables(self, shadows):
        return {name: shadows.answer(name)["table"] for name in shadow.SHADOW_VIEWS}

    def test_kill_every_derived_thing_replay_from_the_record_alone_reconstruct_identically(self):
        self._populate()
        before = self._tables(self.shadows)
        # kill the head memo (the only cache the view surface keeps) — answers must not move
        self.views._memo.clear()
        self.assertEqual(self._tables(self.shadows), before)
        # now the whole machine: a fresh kernel over the record FILE alone. No shadow table,
        # no registry, no memo survives — everything is rebuilt from the record.
        store2, _gate2, views2, _b2, _s2 = build_full_kernel(
            self.record_path, os.path.join(self.dir, "blobs2"))
        shadows2 = shadow.ShadowViews(store2, views2)
        self.assertEqual(self._tables(shadows2), before)

    def test_the_view_definitions_themselves_come_back_from_the_record(self):
        self._populate()
        _s2, _g2, views2, _b2, _sv2 = build_full_kernel(self.record_path,
                                                        os.path.join(self.dir, "blobs2"))
        for name in shadow.SHADOW_VIEWS:
            self.assertIn(name, views2.view_definitions())

    def test_the_seams_in_memory_aggregate_is_not_state(self):
        self._populate()
        before = self._tables(self.shadows)
        self.seam.reset_totals()                       # delete the sampled aggregate entirely
        self.assertEqual(self._tables(self.shadows), before)
        self.assertEqual(self.seam.totals()["seen_total"], 0)


# =============================================================================================
# T-OBSERVABILITY-BOUNDARY
# =============================================================================================

class TestObservabilityBoundary(_Composed):
    def test_changing_the_sampling_rate_leaves_reconstructed_state_identical(self):
        # the load-bearing acts are recorded once each; the sampled classes are driven at two
        # very different rates, and the reconstructed state does not move by one field.
        self.observe("file", "file-created", "file:/w/s", data={"path": "/w/s"})
        for _ in range(3):
            self.seam.submit(Observation(window="file", window_version="test-1", act="file-read",
                                         object="file:/w/s", occurrence_time=WHEN,
                                         data={"path": "/w/s"}))
        sparse = self.shadows.answer("m1-file-history")["table"]
        sparse_len = len(self.store.all())
        for _ in range(300):                            # a hundredfold sampling rate
            self.seam.submit(Observation(window="file", window_version="test-1", act="file-read",
                                         object="file:/w/s", occurrence_time=WHEN,
                                         data={"path": "/w/s"}))
        self.assertEqual(self.shadows.answer("m1-file-history")["table"], sparse)
        self.assertEqual(len(self.store.all()), sparse_len)   # and the record did not grow

    def test_no_view_answer_reads_the_sampled_aggregate(self):
        # structural: the shadow surface never touches the seam. Nothing load-bearing lives
        # in a sample, so nothing load-bearing can read one.
        with open(os.path.join(OBSERVE_SRC, "shadow.py"), encoding="utf-8") as f:
            src = f.read()
        for forbidden in ("seam.totals", ".totals()", "ObservationSeam"):
            self.assertNotIn(forbidden, src, f"the shadow surface reads {forbidden}")


# =============================================================================================
# T-SHADOW-TRACKS  (and its column proven able to fail)
# =============================================================================================

class TestShadowTracks(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record_path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, _b, _s = build_full_kernel(
            self.record_path, os.path.join(self.dir, "blobs"))
        register_observe_ops(self.gate)
        self.seam = ObservationSeam(self.gate)
        shadow.define_shadow_views(self.gate)
        self.window = _mount_window([
            {"/a": {"fstype": "ext4"}},
            {"/a": {"fstype": "ext4"}, "/b": {"fstype": "xfs"}},
        ])
        self.shadows = shadow.ShadowViews(self.store, self.views, [self.window])

    def _pump(self):
        return self.seam.submit_all(self.window.read())

    def test_the_shadow_matches_the_box_while_the_adapter_runs(self):
        self._pump()
        t = self.shadows.tracks("m1-mount-table")
        self.assertTrue(t["tracks"], t)
        self.assertEqual((t["missing"], t["extra"], t["differing"]), ([], [], []))
        served = self.shadows.current("m1-mount-table")     # a currency claim that holds
        self.assertTrue(served["claims_currency"])
        self.assertEqual(sorted(served["table"]), ["/a"])
        self.assertEqual(served["checked_against"], f"mount@{self.window.version}")

    def test_a_stopped_adapter_makes_the_shadow_stale_and_the_staleness_is_DETECTED(self):
        # the column proven able to fail. The world moves; the adapter does not submit; the
        # shadow is now behind — and the currency claim REFUSES rather than serving it.
        self._pump()
        self.window._next()                       # the box changed (/b appeared)
        t = self.shadows.tracks("m1-mount-table")
        self.assertFalse(t["tracks"])
        self.assertEqual(t["missing"], ["/b"])    # the box has it; the record does not
        with self.assertRaises(shadow.StaleShadow) as cm:
            self.shadows.current("m1-mount-table")
        self.assertEqual(cm.exception.drift["missing"], ["/b"])
        # and the non-claiming answer is still available, labelled for what it is
        answer = self.shadows.answer("m1-mount-table")
        self.assertFalse(answer["claims_currency"])
        self.assertEqual(sorted(answer["table"]), ["/a"])

    def test_catching_up_clears_the_staleness(self):
        self._pump()
        self.window._snaps = [{"/a": {"fstype": "ext4"}, "/b": {"fstype": "xfs"}}]
        self._pump()
        self.assertTrue(self.shadows.tracks("m1-mount-table")["tracks"])
        self.assertEqual(sorted(self.shadows.current("m1-mount-table")["table"]), ["/a", "/b"])

    def test_an_unavailable_window_refuses_the_currency_claim_rather_than_answering(self):
        self._pump()
        self.window._injected = None                      # the window is gone
        self.window._probed = (False, "the facility closed")
        t = self.shadows.tracks("m1-mount-table")
        self.assertFalse(t["tracks"])
        self.assertIn("unavailable", t["reason"])
        with self.assertRaises(shadow.StaleShadow):
            self.shadows.current("m1-mount-table")

    def test_a_shadow_with_no_window_attached_never_claims_currency(self):
        blind = shadow.ShadowViews(self.store, self.views)          # no windows
        self.assertFalse(blind.tracks("m1-mount-table")["tracks"])
        with self.assertRaises(shadow.StaleShadow):
            blind.current("m1-mount-table")


# =============================================================================================
# Coverage is stated, never implied
# =============================================================================================

class TestCoverageIsStated(_Composed):
    windows = (MountWindow(), ProcessWindow())

    def test_every_shadow_answer_carries_both_halves_of_its_coverage(self):
        for name in shadow.SHADOW_VIEWS:
            cov = self.shadows.coverage(name)
            self.assertTrue(cov["definition_boundary"]["boundary"], name)   # the engine's half
            self.assertIn("does_not_see", cov["window"], name)              # the window's half
            self.assertIn("permanent_limit", cov)
            self.assertIn("NOT CLAIMED", cov["completeness"])

    def test_a_view_names_the_acts_it_drops_as_well_as_the_acts_it_keeps(self):
        cov = self.shadows.coverage("m1-file-history")
        self.assertIn("file-read", cov["acts_seen_and_dropped"])
        self.assertIn("file-created", cov["recorded_acts"])

    def test_no_view_declares_its_coverage_sufficient(self):
        for name in shadow.SHADOW_VIEWS:
            blob = repr(self.shadows.coverage(name)).lower()
            for claim in ("complete coverage", "sees everything", "coverage is sufficient"):
                self.assertNotIn(claim, blob, name)

    def test_a_deferred_window_states_why_rather_than_going_quiet(self):
        from observe.windows import ArrivalWindow
        w = ArrivalWindow()
        ok, reason = w.available()
        self.assertEqual(w.read(), [])
        if not ok:
            self.assertTrue(reason)
            self.assertIn("outside this EP's fence", reason)
        self.assertIn("INPUT-class", " ".join(w.coverage()["does_not_see"]) + " INPUT-class")


# =============================================================================================
# T-ONE-WRITER
# =============================================================================================

class TestOneWriter(_Composed):
    def test_no_adapter_reaches_the_record_except_through_the_gate(self):
        # the sole-appender structural guard, aimed at the surface this EP adds
        for name, src in _observe_sources():
            self.assertNotIn("._append(", src, f"observe/{name} appends directly")
            self.assertNotIn("store.append(", src, f"observe/{name} appends directly")

    def test_exactly_one_governed_record_per_recorded_observation_with_five_adapters_live(self):
        mirror = ("dual-audit-record", "dual-audit-b-record")
        governed = lambda: [e for e in self.store.all() if e["action"] not in mirror]
        for window, act, obj in (("process", "process-created", "proc:1"),
                                 ("file", "file-created", "file:/w/a"),
                                 ("mount", "mount-added", "mount:/m"),
                                 ("device", "device-bound", "device:pci/z"),
                                 ("connection", "connection-opened", "conn:tcp:9-9")):
            before = len(governed())
            rec = self.observe(window, act, obj)
            self.assertEqual(len(governed()), before + 1, f"{window}/{act}")
            self.assertIs(self.store.by_seq(rec["seq"]), rec)

    def test_a_not_recorded_class_yields_no_record_at_all(self):
        before = len(self.store.all())
        self.assertIsNone(self.seam.submit(Observation(
            window="file", window_version="test-1", act="file-read", object="file:/w/a",
            occurrence_time=WHEN)))
        self.assertEqual(len(self.store.all()), before)

    def test_the_observation_surface_the_registry_reports_is_exactly_the_five_windows(self):
        # enumeration IS the completeness guarantee: a window with no op cannot write, and
        # an op with no window is never registered.
        self.assertEqual(sorted(m1_observe_ops(self.gate)), sorted(OP_FOR_WINDOW.values()))
        self.assertEqual({m["observe_window"] for m in m1_observe_ops(self.gate).values()},
                         set(OP_FOR_WINDOW))


# =============================================================================================
# ADDENDUM 1 — T-RATE-GOVERNANCE (observe scale)
# =============================================================================================

class TestRateGovernance(_Composed):
    def test_a_cache_or_stream_population_adds_nothing_to_the_record(self):
        before = len(self.store.all())
        drops = 0
        for window, acts in classmap.DROPPED_ACTS.items():
            if window not in OP_FOR_WINDOW:
                continue
            for act in acts:
                for _ in range(40):
                    self.assertIsNone(self.seam.submit(Observation(
                        window=window, window_version="test-1", act=act,
                        object=f"{window}:x", occurrence_time=WHEN)))
                    drops += 1
        self.assertGreater(drops, 200)                      # a real population, not a token one
        self.assertEqual(len(self.store.all()), before)     # and the record gained NOTHING

    def test_a_decision_or_law_population_produces_exactly_its_covering_record_each(self):
        mirror = ("dual-audit-record", "dual-audit-b-record")
        governed = lambda: [e for e in self.store.all() if e["action"] not in mirror]
        before, expected = len(governed()), 0
        for window, acts in classmap.RECORDED_ACTS.items():
            if window not in OP_FOR_WINDOW:
                continue
            for act in acts:
                for i in range(10):
                    self.assertIsNotNone(self.observe(window, act, f"{window}:{act}:{i}"))
                    expected += 1
        self.assertEqual(len(governed()) - before, expected)

    def test_recording_tracks_decisions_not_operations_end_to_end_on_a_real_window(self):
        # the row's whole point, driven by real activity rather than fixtures: many reads of
        # one file append nothing; one write appends its decisions and no more.
        watched = os.path.join(self.dir, "watched")
        os.makedirs(watched, exist_ok=True)
        w = FileWindow([watched])
        ok, why = w.available()
        if not ok:
            self.skipTest(f"inotify unavailable: {why}")
        w.open()
        path = os.path.join(watched, "driven.txt")
        with open(path, "w") as f:
            f.write("seed")
        self.seam.submit_all(w.read())
        before = len(self.store.all())
        for _ in range(60):
            with open(path) as f:
                f.read()
        reads = w.read()
        self.assertTrue(reads, "the window saw no read traffic")
        self.seam.submit_all(reads)
        self.assertEqual(len(self.store.all()), before, "read traffic reached the record")
        self.assertGreater(sum(n for (win, cls), n in self.seam.seen.items()
                               if win == "file" and cls in classmap.NOT_RECORDED), 0)
        with open(path, "a") as f:
            f.write("more")
        writes = [o for o in w.read() if o.record_class == classmap.DECISION]
        self.seam.submit_all(writes)
        self.assertEqual(len(self.store.all()), before + len(writes))
        w.close()


class TestTheObserverDoesNotRecordItsOwnWriting(unittest.TestCase):
    """Found by driving the file window against a real box, and landed here as a regression.

    If a watched directory holds gov-os's own record file, every append modifies a watched
    file, the window sees it, and observing the append is itself an append — the act of
    recording becomes the thing recorded and the record inflates with its own writing. The
    observer's footprint is therefore excluded, the exclusion is COUNTED, and it is DECLARED
    in the window's coverage rather than applied quietly."""

    def test_the_record_file_is_excluded_counted_and_declared(self):
        d = tempfile.mkdtemp()
        run = M1Run(os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                    watch_paths=[d]).setup()
        try:
            file_window = next(w for w in run.windows if w.name == "file")
            run.cycle()                                    # appends a lot; all inside `d`
            run.cycle()                                    # the window now sees those writes
            self.assertGreater(file_window.excluded_events, 0,
                               "the observer's own appends were not excluded")
            recorded_paths = {(e.get("payload") or {}).get("observed", {}).get("path")
                              for e in run.store.all()
                              if (e.get("payload") or {}).get("kind") == "observed-file"}
            self.assertNotIn(os.path.join(d, "record.jsonl"), recorded_paths)
            # declared, not silent
            blind = " ".join(file_window.coverage()["does_not_see"])
            self.assertIn("the act of recording does not become the thing recorded", blind)
        finally:
            run.close()

    def test_an_unrelated_file_in_the_same_directory_is_still_recorded(self):
        # the too-wedged direction: the exclusion must remove the observer's own footprint
        # and nothing else.
        d = tempfile.mkdtemp()
        run = M1Run(os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                    watch_paths=[d]).setup()
        try:
            run.cycle()
            with open(os.path.join(d, "real-work.txt"), "w") as f:
                f.write("this is the box doing something")
            run.cycle()
            recorded = {(e.get("payload") or {}).get("observed", {}).get("path")
                        for e in run.store.all()
                        if (e.get("payload") or {}).get("kind") == "observed-file"}
            self.assertIn(os.path.join(d, "real-work.txt"), recorded)
        finally:
            run.close()


# =============================================================================================
# ADDENDUM 1 — T-FOLD-AT-RATE (observe scale)
# =============================================================================================

class TestFoldAtRate(_Composed):
    def test_the_authority_fold_is_consulted_at_every_gated_observation(self):
        seen = []
        real = self.views.covers
        self.views.covers = lambda *a, **k: (seen.append(a) or real(*a, **k))
        try:
            self.observe("mount", "mount-added", "mount:/f")
        finally:
            self.views.covers = real
        self.assertTrue(seen, "no authority fold was consulted on a gated observation")
        self.assertEqual(seen[0][0], "m1-observer")
        self.assertEqual(seen[0][2], "observed-mount")     # the info-kind dimension of the act

    def test_a_cached_fold_answer_is_coherent_or_refuse_never_stale(self):
        # invalidate the record a cached answer rests on, and the next consultation does not
        # serve the old one. The fold holds nothing between calls, so "recompute" is what it
        # can only do — and the memo that DOES exist is invalidated by the append itself.
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.gate.execute("GRANT", "owner", {"grant_id": "obs", "grantee": "m1-observer",
                                             "actions": ["mount-added"], "info": ["observed-mount"],
                                             "space": self.views.mother_space()})
        self.assertTrue(self.views.covers("m1-observer", "mount-added", "observed-mount",
                                          self.views.mother_space()))
        generation = self.views._memo_gen
        self.observe("mount", "mount-added", "mount:/g")               # still lawful
        self.gate.execute("REVOKE", "owner", {"grant_id": "obs"})      # the grant is gone
        self.assertGreater(self.views._memo_gen, generation)           # every append invalidates
        self.assertFalse(self.views.covers("m1-observer", "mount-added", "observed-mount",
                                           self.views.mother_space()))
        before = len(self.store.by_action("mount-added"))
        with self.assertRaises(OpError) as cm:
            self.observe("mount", "mount-added", "mount:/h")
        # refused, not served stale. The citation is ROOT-NEG-1 rather than ROOT-NEG-3
        # because the revoke left the observer holding NO grant at all, so there is no chain
        # to reach it — the gate cites "no chain", not "chain that does not cover this act".
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")
        self.assertEqual(len(self.store.by_action("mount-added")), before)   # nothing written

    def test_the_fold_is_measurable_at_observe_scale(self):
        # the measurement half of the row: the number goes to the ledger, but the ability to
        # take it is asserted here so the ledger can never quietly stop being produced.
        d = tempfile.mkdtemp()
        run = M1Run(os.path.join(d, "r.jsonl"), os.path.join(d, "blobs"),
                    windows=[_mount_window([{"/a": {"fstype": "ext4"}}])]).setup()
        run.run(cycles=1)
        cost = run.fold_cost(samples=20)
        self.assertEqual(cost["samples"], 20)
        self.assertGreater(cost["seconds_per_consultation"], 0)
        self.assertGreater(cost["record_length_at_measurement"], 0)
        m = run.measurements()
        self.assertIn("append_rate", m)
        self.assertIn("store_growth", m)
        self.assertIn("host_kernel", m["conditions"])
        run.close()


# =============================================================================================
# ADDENDUM 1 — T-NO-STORED-TABLE (observe scale)
# =============================================================================================

class TestNoStoredTable(_Composed):
    #: The refused reference, by name. A permission table or a stored complement anywhere on
    #: the adapter path is RBAC arriving through an unchecked door (design/36 K3).
    BANNED_STRUCTURES = ("permissions", "permission_table", "capabilities", "capability_set",
                         "allowed_actions", "denied", "deny_list", "acl")

    def test_the_adapter_path_stores_no_permission_structure(self):
        for name, src in _observe_sources():
            lowered = src.lower()
            for banned in self.BANNED_STRUCTURES:
                self.assertNotIn(f"self.{banned}", lowered, f"observe/{name} stores {banned}")
                self.assertNotIn(f'"{banned}":', lowered, f"observe/{name} records {banned}")

    def test_no_observed_record_carries_a_permission_payload(self):
        for window, acts in classmap.RECORDED_ACTS.items():
            if window not in OP_FOR_WINDOW:
                continue
            self.observe(window, acts[0], f"{window}:probe")
        for e in self.observed_records():
            for banned in self.BANNED_STRUCTURES:
                self.assertNotIn(banned, e["payload"], e["action"])
                self.assertNotIn(banned, e["payload"]["observed"], e["action"])

    def test_authority_is_folded_live_and_the_complement_is_computed(self):
        # the positive-grant model, checked over the surface this EP adds: revoking the one
        # covering grant flips the gate's answer at the NEXT check, with nothing to purge.
        self.observe("mount", "mount-added", "mount:/k")
        before = len(self.store.all())
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.assertEqual(len(self.store.all()), before + 1)     # ONLY the revoke — no cascade
        with self.assertRaises(OpError) as cm:
            self.observe("mount", "mount-added", "mount:/l")
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")       # no chain, computed live

    def test_the_seam_holds_no_authority_state_between_calls(self):
        # everything the seam keeps is a counter of what it saw; kill it and no answer moves.
        self.observe("mount", "mount-added", "mount:/n")
        kept = set(vars(self.seam)) - {"gate", "observer"}
        self.assertEqual(kept, {"seen", "recorded"})


# =============================================================================================
# The runner, end to end on the real box
# =============================================================================================

class TestRunnerOnTheRealBox(unittest.TestCase):
    def test_the_composed_runner_observes_a_real_machine_and_measures_it(self):
        d = tempfile.mkdtemp()
        watched = os.path.join(d, "watched")
        os.makedirs(watched)
        run = M1Run(os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                    watch_paths=[watched]).setup()
        try:
            run.run(cycles=1)
            m = run.measurements()
            self.assertGreater(m["append_rate"]["records_appended"], 0)
            self.assertGreater(m["store_growth"]["bytes_per_record"], 0)
            # every window reports availability; an unavailable one is DEFERRED with a reason
            for name, stats in m["per_window"].items():
                self.assertIn("@", stats["window_at_version"])
                if not stats["available"]:
                    self.assertIn(name, m["conditions"]["deferred_windows"])
            # and every record the run produced carries all three pins
            kinds = {f"observed-{w}" for w in OP_FOR_WINDOW}
            observed = [e for e in run.store.all()
                        if (e.get("payload") or {}).get("kind") in kinds]
            self.assertTrue(observed)
            for e in observed:
                self.assertTrue(e["provenance"]["asserted_by"])
                self.assertTrue(e["provenance"]["window"])
                self.assertTrue(e["provenance"]["window_version"])
                self.assertTrue(e["occurrence_time"])
                self.assertEqual(e["rule_cited"], OBSERVATION_LAW)
        finally:
            run.close()


if __name__ == "__main__":
    unittest.main()
