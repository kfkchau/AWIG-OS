# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (the read-only observe seam's file window, re-sourced from the core's OWN record rather than the
# host's inotify facility — a file change under our core IS a recorded write act) as in the
# seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability — this DRIVES the acceptance of
# C7-MAINT-FILE-WINDOW-FROM-RECORD (the file window moves from declared-ABSENT to SERVED-FROM-THE-
# RECORD: a real write act on the record produces a file-change observation traced to it; no write
# yields none; the audit does not audit its own observation-writes; one window moves, four stay
# absent, no host facility is added). Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-FILE-WINDOW-FROM-RECORD — acceptance (design/54 §3 B10; §5 L21 + the P1 finding; L19).

A1  a REAL write act on the record (a real append through the gate) is read by the file window as
    a file-change observation, its provenance naming the record route and version. PROVEN with a
    real write act (L19), never a fabricated event. PLANT: an observation with no matching write
    act in the record fails the trace check.
A2  with no write act since the last read, the file window yields none (and states its record
    route, never silently empty). PLANT: a phantom observation with no write behind it fails the
    trace check.
A3  the file window does NOT observe its own observation-writes: reading the record and recording
    the observations does not recursively generate observations of those observation-records (the
    self-audit exclusion, inverted for the record source). A bounded read shows no runaway growth.
    PLANT: a window that does NOT exclude its own observation-writes inflates the record each read.
A4  one window moves, nothing else: the census names the file window RE-SOURCED (a core route, no
    host facility), the other four ABSENT-with-reason; the effect seam names no Linux facility;
    ACT_KINDS 12; ATTESTED unchanged; the record window opens no inotify. PLANT: a re-sourced route
    naming a host facility is caught by the census's body-widening guard.
"""

import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir, "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kernel.compose import build_full_kernel                               # noqa: E402
from observe import seam                                                   # noqa: E402
from observe.seam import register_observe_ops, ObservationSeam             # noqa: E402
from observe.windows import (                                             # noqa: E402
    RecordFileWindow, RECORD_ROUTE, OBSERVED_FILE_KIND, Observation)


def _kernel():
    """A REAL kernel: a real record on disk, the observe ops registered, a real submitter. The
    file window reads THIS record's own write acts — nothing is faked."""
    d = tempfile.mkdtemp()
    store, gate, views, _b, _s = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"))
    register_observe_ops(gate)
    return store, gate, ObservationSeam(gate)


def _traces_to_a_real_write_act(obs, store):
    """THE TRACE CHECK (able to fail). An observation traces to a real write act only if the record
    seq it names is actually present in the record. A fabricated observation names a seq no write
    act carries, and this returns False."""
    live_seqs = {e["seq"] for e in store.all()}
    return obs.data.get("record_seq") in live_seqs


# ==================================================================================================
# A1 — A REAL WRITE ACT PRODUCES A FILE-WINDOW OBSERVATION FROM THE RECORD
# ==================================================================================================

class TestA1RealWriteActProducesAnObservation(unittest.TestCase):

    def test_a_real_append_is_read_as_a_file_change_observation_traced_to_it(self):
        store, gate, _seam = _kernel()
        window = RecordFileWindow(record_reader=store.all)
        window.read()                       # drain the founding write acts (the baseline)

        # A REAL write act on the record: a real append through the gate (L19 — not fabricated).
        rec = gate.execute("WRITE-ACTIVITY", "SYSTEM",
                           {"about": "c7-maint-probe", "data": {"probe": "real-write"}})
        obs = window.read()

        self.assertEqual(len(obs), 1, "the one new write act produced exactly one observation")
        o = obs[0]
        self.assertEqual(o.act, "file-modified")     # the append grew the record file
        self.assertEqual(o.data["record_seq"], rec["seq"], "the observation traces to the write act")
        self.assertTrue(_traces_to_a_real_write_act(o, store))
        # provenance names the RECORD route (and its version), never inotify.
        self.assertIn("record", o.window_version)
        self.assertNotIn("inotify", o.window_version)
        self.assertEqual(o.data["source"], RECORD_ROUTE)
        self.assertEqual(o.time_source, "window-reported")   # the record carries the act's own time

    def test_the_A1_plant_a_fabricated_observation_does_not_trace(self):
        # THE A1 PLANT (can fail): an observation carrying a record seq that NO write act in the
        # record holds — a fabricated event — fails the trace check. The SAME check PASSES a real
        # observation, so it discriminates and is not a check that always fails.
        store, gate, _seam = _kernel()
        window = RecordFileWindow(record_reader=store.all)
        real = window.read()[0]
        self.assertTrue(_traces_to_a_real_write_act(real, store))    # discriminates: real passes

        fabricated = Observation(
            window="file", window_version=window.version, act="file-modified",
            object="file:the-record", occurrence_time="2026-09-18T00:00:00+00:00",
            data={"record_seq": 10 ** 9, "source": RECORD_ROUTE})
        self.assertFalse(_traces_to_a_real_write_act(fabricated, store),
                         "a fabricated observation with no write act behind it must not trace")


# ==================================================================================================
# A2 — NO WRITE, NO OBSERVATION
# ==================================================================================================

class TestA2NoWriteNoObservation(unittest.TestCase):

    def test_no_new_write_act_yields_no_observation(self):
        store, gate, _seam = _kernel()
        window = RecordFileWindow(record_reader=store.all)
        window.read()                       # drain everything present
        self.assertEqual(window.read(), [], "with no new write act the window yields none")
        # and it is never silently empty: it states its record route (coverage + version).
        self.assertIn(RECORD_ROUTE, window.version)
        cov = window.coverage()
        self.assertIn(RECORD_ROUTE, cov["facility"])
        self.assertNotIn("inotify", cov["facility"])

    def test_the_A2_plant_a_phantom_observation_has_no_write_behind_it(self):
        # THE A2 PLANT (can fail): a phantom observation manufactured with no write act behind it
        # does not trace. The window itself never manufactures one (the test above proves it yields
        # []); a hand-built phantom fails the trace check.
        store, gate, _seam = _kernel()
        phantom = Observation(
            window="file", window_version="m1.1-record+x", act="file-modified",
            object="file:the-record", data={"record_seq": 777_000, "source": RECORD_ROUTE})
        self.assertFalse(_traces_to_a_real_write_act(phantom, store))


# ==================================================================================================
# A3 — THE AUDIT DOES NOT AUDIT ITSELF
# ==================================================================================================

class _InflatingWindow(RecordFileWindow):
    """The PLANT window: it does NOT exclude its own observation-writes, so reading the record and
    recording the observations makes it observe those observation-records on the next read — the
    record inflates on every read. Proves the exclusion in the real window is load-bearing."""

    @staticmethod
    def is_own_observation_write(entry):
        return False


class TestA3TheAuditDoesNotAuditItself(unittest.TestCase):

    def test_reading_and_recording_does_not_inflate_the_record(self):
        store, gate, seam = _kernel()
        window = RecordFileWindow(record_reader=store.all)
        lengths = []
        for _ in range(5):
            seam.submit_all(window.read())      # read the write acts, record the observations
            lengths.append(len(store.all()))
        # After the first cycle records the observations of the real write acts, the record
        # PLATEAUS — the window excludes its own observation-writes, so no further reads generate
        # observations of observation-records.
        self.assertEqual(lengths[1], lengths[-1], "the record must not grow after the first read")
        self.assertGreater(window.excluded_events, 0,
                           "the self-audit exclusion must have dropped the window's own writes")

    def test_the_A3_plant_without_the_exclusion_the_record_inflates(self):
        # THE A3 PLANT (can fail): the SAME loop with the exclusion removed grows the record on
        # every read — a runaway. The real window plateaus; the inflating one does not.
        store, gate, seam = _kernel()
        inflating = _InflatingWindow(record_reader=store.all)
        lengths = []
        for _ in range(5):
            seam.submit_all(inflating.read())
            lengths.append(len(store.all()))
        self.assertTrue(all(lengths[i] < lengths[i + 1] for i in range(len(lengths) - 1)),
                        "without the exclusion the record must inflate on every read")


# ==================================================================================================
# A4 — ONE WINDOW MOVES, NOTHING ELSE
# ==================================================================================================

class TestA4OneWindowMovesNothingElse(unittest.TestCase):

    def test_the_census_names_the_file_window_re_sourced_and_the_others_absent(self):
        census = {s["window"]: s for s in seam.window_census()}
        self.assertEqual(census["file"]["state"], seam.WINDOW_STATE_RESOURCED)
        self.assertTrue(census["file"]["core_route"], "the file window names its record route")
        # UPDATED by C7 P7b (mechanical delta): the DEVICE window is now re-sourced from the record's
        # discovery rows too — process / mount / connection stay ABSENT-with-reason (this file-window
        # unit moved only the file window; P7b moved the device window).
        self.assertEqual(census["device"]["state"], seam.WINDOW_STATE_RESOURCED)
        for w in ("process", "mount", "connection"):
            self.assertEqual(census[w]["state"], seam.WINDOW_STATE_ABSENT,
                             "%r must stay ABSENT-with-reason" % w)
            self.assertTrue(census[w]["reason"])

    def test_the_file_windows_core_route_names_no_host_facility(self):
        route = seam.CORE_ROUTES["file"]
        self.assertFalse(seam._route_names_linux_facility(route),
                         "the file window is served from the record, never a host facility (L21)")
        for s in seam.window_census():
            r = s.get("core_route")
            if r is not None:
                self.assertFalse(seam._route_names_linux_facility(r))

    def test_the_A4_plant_a_re_sourced_route_naming_a_facility_is_caught(self):
        # THE A4 PLANT (can fail): re-sourcing the file window by ADDING a host facility to the body
        # (the L1/L21 widening this unit refuses) is caught by the census's body-widening guard.
        for facility_route in ("inotify", "/proc scan", "netlink sock_diag", "/sys/bus"):
            with self.assertRaises(seam.BodyWideningWindow):
                seam.window_census(core_routes={"file": facility_route})

    def test_the_record_window_opens_no_inotify_and_carries_no_host_facility(self):
        # The re-source reads the record the body already serves — it opens no host facility.
        store, gate, _seam = _kernel()
        window = RecordFileWindow(record_reader=store.all)
        self.assertEqual(window.route, RECORD_ROUTE)
        self.assertIsNone(type(window).host_facility, "the record window names no host facility")
        self.assertEqual(window.open(), window)          # open is a no-op: no descriptor, no syscall
        self.assertIsNone(window._fd, "the record window never opens an inotify descriptor")

    def test_act_kinds_is_still_twelve_and_attested_unchanged(self):
        from bridge import host_seam as hs
        from kernel import attestation
        self.assertEqual(len(hs.ACT_KINDS), 12)
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88)

    def test_the_observe_surface_is_unchanged_five_ops_one_per_window(self):
        self.assertEqual(len(seam.OP_FOR_WINDOW), 5)


if __name__ == "__main__":
    unittest.main()
