# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""M1 W4/W5 — the runner: the built kernel, composed with the windows, pointed at a real box.

This is the whole of M1 standing up: the campaign-1/2 kernel (store, gate, views — the one the
474/483-test suite already proves) with the observation seam attached, the five shadow views
defined as recorded acts, and the windows read in a loop. AWIG OS takes NO authority here.
Linux decided everything; the record notes what it saw, through which window, at what version,
and when the window says it happened.

RESIDENCE, STATED BECAUSE planning/11 §3 SAYS OTHERWISE. The stage spec predates the built
engine and says to lift the pwc/cgl spine. That residence assumption is SUPERSEDED
(design/36 §7 item 4): the spine is the campaign-1/2 kernel under `src/`, composed here
unchanged, and fortress purity independently bars any occupant material. Nothing is lifted.

WHAT IT MEASURES, AND WHAT A MEASUREMENT IS. design/36 §9 names performance as the campaign's
whole risk, in two halves that are both unmeasured: recording at OS event rate, and the
authority fold consulted at every gated act. Observe mode is where the first real numbers are
cheap and nothing can break, so they are taken here. Every number this module produces is a
MEASUREMENT WITH ITS CONDITIONS — the box, the window set, the cadence, the record size at the
time. None of them is a promise, none is extrapolated, and the ledger
(`planning/build/MEASUREMENTS.md`) records them as observations with their conditions attached.
"""

import os
import time

from kernel.compose import build_full_kernel

from . import shadow
from .seam import DEFAULT_OBSERVER, ObservationSeam, register_observe_ops
from .windows import default_windows


class M1Run:
    """One observation run: compose, attach, read, submit, measure."""

    def __init__(self, record_path, blob_dir, watch_paths=(), observer=DEFAULT_OBSERVER,
                 windows=None):
        self.record_path = record_path
        self.blob_dir = blob_dir
        self.watch_paths = list(watch_paths)
        self.observer = observer
        self._windows_override = windows
        self.store = self.gate = self.views = None
        self.seam = None
        self.windows = []
        self.shadows = None
        #: measurements — filled by run(); never appended to the record.
        self.cycles = 0
        self.elapsed = 0.0
        self.submit_seconds = 0.0
        self.window_read_seconds = {}
        self.deferred = {}

    def own_footprint(self):
        """Everything this observer itself writes: the record file, its single-writer lock,
        and the blob store. Named here so the exclusion is one list a reader can check."""
        return [self.record_path, self.record_path + ".lock", self.blob_dir,
                os.path.join(os.path.dirname(self.blob_dir) or ".", "vault")]

    # ---- composition ---------------------------------------------------------------------
    def setup(self):
        self.store, self.gate, self.views, _blobs, _sub = build_full_kernel(
            self.record_path, self.blob_dir)
        register_observe_ops(self.gate)
        # The observer's own footprint is declared OUT of the file window's reach. Found by
        # running this against a real box: a watch over a directory holding the record file
        # turns every append into a watched modification, so recording becomes the thing
        # recorded and the record inflates with its own writing. The exclusion is stated in
        # the window's coverage, never applied silently.
        self.windows = (self._windows_override if self._windows_override is not None
                        else default_windows(self.watch_paths, exclude=self.own_footprint()))
        self.seam = ObservationSeam(self.gate, self.observer)
        shadow.define_shadow_views(self.gate)
        self.shadows = shadow.ShadowViews(self.store, self.views, self.windows)
        for w in self.windows:
            ok, reason = w.available()
            if not ok:
                # A window that will not open is DEFERRED with its observed reason and
                # raised — never silently skipped, and never chased by reconfiguring the box.
                self.deferred[w.name] = reason
        return self

    # ---- one pass over every window ------------------------------------------------------
    def cycle(self):
        submitted = 0
        for w in self.windows:
            t0 = time.perf_counter()
            observations = w.read()
            self.window_read_seconds[w.name] = self.window_read_seconds.get(w.name, 0.0) + (
                time.perf_counter() - t0)
            t1 = time.perf_counter()
            submitted += len(self.seam.submit_all(observations))
            self.submit_seconds += time.perf_counter() - t1
        self.cycles += 1
        return submitted

    def run(self, seconds=None, cycles=1, pause=0.0):
        """Read the windows for `seconds` (or a fixed number of cycles). Returns this run."""
        start = time.perf_counter()
        if seconds is not None:
            while time.perf_counter() - start < seconds:
                self.cycle()
                if pause:
                    time.sleep(pause)
        else:
            for _ in range(cycles):
                self.cycle()
                if pause:
                    time.sleep(pause)
        self.elapsed = time.perf_counter() - start
        return self

    def close(self):
        for w in self.windows:
            w.close()

    # ---- W5: the measurements ------------------------------------------------------------
    def fold_cost(self, samples=200):
        """The authority fold, timed. This is the SECOND of the two K3 costs (design/36 K3):
        the fold consulted at every gated act, folded live over the grant records with nothing
        stored. Measured over the record as it stands at the end of the run, which is a
        condition of the number and is reported with it."""
        act = "process-created"
        space = self.views.mother_space()
        t0 = time.perf_counter()
        for _ in range(samples):
            self.views.covers(self.observer, act, "observed-process", space)
        total = time.perf_counter() - t0
        return {"samples": samples, "total_seconds": total,
                "seconds_per_consultation": total / samples,
                "record_length_at_measurement": len(self.store.all()),
                "live_grants": len(self.views.grants())}

    def gate_cost(self, samples=50):
        """The whole chokepoint, timed end to end on a real observation submission: the
        authority fold plus the full-form pass plus the constitution guard plus the append and
        its fsync. Reported alongside the fold so the fold's share is visible rather than
        asserted. Each sample APPENDS — that is the point (this is the append cost) — so the
        count is deliberately small and is stated."""
        from .seam import Observation, TIME_WINDOW_REPORTED
        t0 = time.perf_counter()
        for i in range(samples):
            self.seam.submit(Observation(
                window="mount", window_version="measurement", act="mount-attr-changed",
                object=f"mount:/measurement/{i}", occurrence_time="2026-07-26T00:00:00+00:00",
                time_source=TIME_WINDOW_REPORTED, data={"key": f"/measurement/{i}",
                                                        "fstype": "measurement"}))
        total = time.perf_counter() - t0
        return {"samples": samples, "total_seconds": total,
                "seconds_per_gated_append": total / samples,
                "record_length_at_measurement": len(self.store.all())}

    def store_growth(self):
        size = os.path.getsize(self.record_path) if os.path.exists(self.record_path) else 0
        records = len(self.store.all())
        return {"record_file_bytes": size, "records": records,
                "bytes_per_record": (size / records) if records else 0}

    def measurements(self):
        """Every number this run produced, each with the conditions that produced it."""
        totals = self.seam.totals()
        per_window = {}
        for w in self.windows:
            seen = sum(c for (win, _cls), c in totals["seen"].items() if win == w.name)
            rec = sum(c for (win, _cls), c in totals["recorded"].items() if win == w.name)
            read_s = self.window_read_seconds.get(w.name, 0.0)
            per_window[w.name] = {
                "window_at_version": f"{w.name}@{w.version}",
                "available": w.available()[0],
                "observations_seen": seen,
                "observations_recorded": rec,
                "observations_classified_out": seen - rec,
                "window_read_seconds": read_s,
                "observations_per_second_of_window_read": (seen / read_s) if read_s else 0.0,
            }
        return {
            "conditions": {
                "host_kernel": _read_or("/proc/sys/kernel/osrelease", "unknown"),
                "cycles": self.cycles,
                "elapsed_seconds": self.elapsed,
                "watch_paths": self.watch_paths,
                "windows": [w.name for w in self.windows],
                "deferred_windows": dict(self.deferred),
                "observer": self.observer,
            },
            "per_window": per_window,
            "append_rate": {
                "records_appended": totals["recorded_total"],
                "submit_seconds": self.submit_seconds,
                "records_per_second_of_submit": (totals["recorded_total"] / self.submit_seconds)
                if self.submit_seconds else 0.0,
            },
            "classified_out": {
                "observations_seen": totals["seen_total"],
                "observations_recorded": totals["recorded_total"],
                "appended_nothing": totals["seen_total"] - totals["recorded_total"],
                "by_window_and_class": {f"{w}/{c}": n for (w, c), n in sorted(totals["seen"].items())},
            },
            "store_growth": self.store_growth(),
        }


def _read_or(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return default


def run_m1(record_path, blob_dir, watch_paths=(), seconds=None, cycles=1, pause=0.0):
    """Compose, run, measure, and hand back the run for the caller to read evidence from."""
    run = M1Run(record_path, blob_dir, watch_paths).setup()
    run.run(seconds=seconds, cycles=cycles, pause=pause)
    return run
