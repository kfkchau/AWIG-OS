# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (the read-only observe windows, a facility, a census, re-sourced-from-the-core, declared-absent) as
# in the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability — this DRIVES the acceptance
# of C7 P9 (the five observe windows settled under our core: each re-sourced from the core with its
# route, or declared absent with its measured reason, never silently empty; a planted silent-empty
# window reds; a re-sourced window opening a host facility is caught). Full declaration: SCOPE-STATEMENT.md.
"""C7 P9 — THE OBSERVE WINDOWS UNDER OUR CORE — acceptance (design/54 §7 P9; §3 B10; §5 L1/L13/L21).

A1  the census names EVERY window's state: the five (process, file, mount, device, connection),
    DERIVED from OP_FOR_WINDOW / windows.py, never hand-listed; each named RE-SOURCED (with its core
    route) or ABSENT (with its measured reason); the count is five, none unnamed. PLANT: a window with
    no state reds.
A2  no window is silently empty: a window that would yield nothing without declaring absent reds
    (B10's own planted check).
A3  a re-sourced window serves from the core, not a host facility: a re-sourced route naming a Linux
    facility is caught (L1/L21).
A4  nothing else moves: src/kernel untouched, ACT_KINDS 12, ATTESTED unchanged, no founding.
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir, "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from observe import seam                                                   # noqa: E402
from observe import windows as W                                           # noqa: E402


# ==================================================================================================
# A1 — THE CENSUS NAMES EVERY WINDOW'S STATE
# ==================================================================================================

class TestA1CensusNamesEveryWindow(unittest.TestCase):

    def test_the_five_are_derived_from_the_registry_never_hand_listed(self):
        # The census set is DERIVED from OP_FOR_WINDOW and cross-checked against the window classes
        # in windows.py — it is not a literal list in the census. The derived names are exactly the
        # observation-surface windows (arrival is DEFERRED and not among the five: it is not in
        # OP_FOR_WINDOW).
        derived = seam._derived_window_names()
        self.assertEqual(list(derived), list(seam.OP_FOR_WINDOW))
        self.assertEqual(set(derived), {"process", "file", "mount", "device", "connection"})
        self.assertNotIn("arrival", derived)                 # arrival is deferred, not a live window

    def test_the_census_names_five_windows_and_each_carries_a_state(self):
        census = seam.window_census()
        self.assertEqual(len(census), 5, "the census must name exactly the five windows")
        self.assertEqual([s["window"] for s in census], list(seam.OP_FOR_WINDOW))
        for s in census:
            self.assertIn(s["state"], (seam.WINDOW_STATE_RESOURCED, seam.WINDOW_STATE_ABSENT),
                          "window %r carries no settled state" % s["window"])

    def test_every_settlement_is_fully_named_resourced_with_route_or_absent_with_reason(self):
        for s in seam.window_census():
            if s["state"] == seam.WINDOW_STATE_RESOURCED:
                self.assertTrue(s.get("core_route"), "%r re-sourced but names no core route" % s["window"])
            else:
                self.assertTrue(s.get("reason"), "%r absent but states no reason" % s["window"])
                self.assertTrue(s.get("host_facility"), "%r absent but names no host facility" % s["window"])
                # MEASURED, not blanket: the reason names the specific host facility and cites L1.
                self.assertIn(s["host_facility"], s["reason"])
                self.assertIn("L1", s["reason"])

    def test_plant_a_window_with_no_state_reds_the_census(self):
        # THE A1 PLANT (can fail): a window enumerated with no settlement — neither a core route
        # nor a measured absent reason — is a state the census cannot name, and it REDS.
        with self.assertRaises(seam.SilentEmptyWindow):
            seam.window_census(extra_windows=("a-window-with-no-state",))

    def test_a_new_observe_op_without_an_under_our_core_settlement_reds(self):
        # The census guards the REGISTRY: adding an observe op (a sixth window) to OP_FOR_WINDOW
        # without settling it under our core reds the census — the completeness guarantee that no
        # window is added silently. Driven against a temporarily extended registry, restored after.
        saved = dict(seam.OP_FOR_WINDOW)
        try:
            seam.OP_FOR_WINDOW["arrival"] = "OBSERVE-ARRIVAL"        # a window with no settlement
            with self.assertRaises((seam.SilentEmptyWindow, ValueError)):
                seam.window_census()
        finally:
            seam.OP_FOR_WINDOW.clear()
            seam.OP_FOR_WINDOW.update(saved)
        # the registry is restored byte-for-byte
        self.assertEqual(dict(seam.OP_FOR_WINDOW), saved)


# ==================================================================================================
# A2 — NO WINDOW IS SILENTLY EMPTY (the B10 plant)
# ==================================================================================================

class TestA2NoSilentEmptyWindow(unittest.TestCase):

    def test_the_live_census_leaves_no_window_silently_empty(self):
        # Every one of the five is settled with a state and a full declaration — none returns
        # nothing-and-says-nothing.
        for s in seam.window_census():
            declared = bool(s.get("core_route")) or bool(s.get("reason"))
            self.assertTrue(declared, "window %r is silently empty" % s["window"])

    def test_the_silent_empty_plant_reds_b10s_own_failing_check(self):
        # THE B10 PLANT (can fail): a window that would yield [] with NO absent-declaration — modelled
        # as a window name carrying neither a core route nor a measured reason — is SILENT-EMPTY, and
        # settle_window REFUSES it. The refusal names the window and the two ways to settle it.
        with self.assertRaises(seam.SilentEmptyWindow) as cm:
            seam.settle_window("planted-silent-empty")
        self.assertIn("planted-silent-empty", str(cm.exception))
        self.assertIn("SILENT-EMPTY", str(cm.exception).upper())

    def test_the_silent_empty_check_can_also_PASS_a_settled_window(self):
        # The check DISCRIMINATES — it is not a check that always fails: a settled window (absent
        # with reason) passes settle_window and yields a full record.
        s = seam.settle_window("process")
        self.assertEqual(s["state"], seam.WINDOW_STATE_ABSENT)
        self.assertTrue(s["reason"])


# ==================================================================================================
# A3 — RE-SOURCED WINDOWS SERVE FROM THE CORE, NOT A HOST FACILITY (L1/L21)
# ==================================================================================================

class TestA3ResourcedServesFromTheCore(unittest.TestCase):

    def test_live_registry_re_sources_the_file_and_device_windows_by_no_host_facility(self):
        # UPDATED by C7 P7b: the DEVICE window is now SERVED FROM THE RECORD's discovery rows too
        # (was ABSENT), so CORE_ROUTES names the file AND device record routes and no other. Every
        # re-sourced route names the core's own state, never a host facility (neither the file window
        # opens inotify nor the device window opens sysfs).
        self.assertEqual(set(seam.CORE_ROUTES), {"file", "device"})
        for w in ("file", "device"):
            self.assertFalse(seam._route_names_linux_facility(seam.CORE_ROUTES[w]),
                             "the %r window's core route must name no Linux facility (L21)" % w)
        for s in seam.window_census():
            if s["window"] in ("file", "device"):
                self.assertEqual(s["state"], seam.WINDOW_STATE_RESOURCED,
                                 "%r must be re-sourced from the core" % s["window"])
            else:
                self.assertEqual(s["state"], seam.WINDOW_STATE_ABSENT,
                                 "%r must stay ABSENT-with-reason" % s["window"])

    def test_the_device_windows_core_route_names_the_discovery_rows_not_the_pci_id(self):
        # C7 P7b: the device window's core route names the body's OWN discovery rows (the identity the
        # body EXPORTS at bring-up), and NEVER the driver's file-static PCI vendor/device id / slot /
        # BAR — the wrong-reference the archi :4605 precision governs A1's wording away from.
        route = seam.CORE_ROUTES["device"]
        self.assertIn("discovery row", route, "the route names the body's own discovery rows")
        self.assertNotIn("BAR", route, "the route must not name the driver's file-static BAR")
        self.assertNotIn("vendor", route, "the route must not name the file-static PCI vendor id")
        self.assertFalse(seam._route_names_linux_facility(route),
                         "the device window's core route must name no Linux facility (L21)")

    def test_a_valid_core_route_settles_a_window_re_sourced(self):
        # THE RE-SOURCED ARM (driven via an overriding core-route, so the live registry never claims
        # a route the body does not serve): a core route that names the core's OWN state — the record
        # of write acts — settles the file window RE-SOURCED, carrying that route and NO host facility.
        route = "the core's own record of write acts (append / write-once / remove)"
        census = seam.window_census(core_routes={"file": route})
        by_name = {s["window"]: s for s in census}
        self.assertEqual(by_name["file"]["state"], seam.WINDOW_STATE_RESOURCED)
        self.assertEqual(by_name["file"]["core_route"], route)
        self.assertFalse(seam._route_names_linux_facility(route),
                         "the core route must name no Linux facility")

    def test_the_A3_plant_a_re_sourced_route_naming_a_host_facility_is_caught(self):
        # THE A3 PLANT (can fail): a window settled RE-SOURCED whose core route names a Linux host
        # facility is re-sourcing the window BY ADDING A HOST FACILITY to the body — the L1/L21
        # widening — and the census CATCHES it. Every facility token is caught, on the file route AND
        # (C7 P7b) on the DEVICE route (sysfs / uevent are exactly the widening the device window
        # avoids by reading the record's discovery rows).
        for facility_route in ("inotify", "/proc scan", "netlink sock_diag", "/sys/bus", "procnet"):
            with self.assertRaises(seam.BodyWideningWindow):
                seam.window_census(core_routes={"file": facility_route})
        for facility_route in ("/sys/bus/*/devices scan", "netlink uevent", "sysfs", "/sys/class"):
            with self.assertRaises(seam.BodyWideningWindow):
                seam.window_census(core_routes={"device": facility_route})

    def test_no_settled_window_reports_reading_a_host_facility(self):
        # Across the live census, no settlement carries a route that opens a Linux facility. The
        # file AND device windows ARE re-sourced (record routes, not facilities); the other three are
        # absent and name no route. UPDATED by C7 P7b (was: file only re-sourced).
        for s in seam.window_census():
            route = s.get("core_route")
            if route is None:
                self.assertEqual(s["state"], seam.WINDOW_STATE_ABSENT,
                                 "a window with no route must be absent")
            else:
                self.assertFalse(seam._route_names_linux_facility(route),
                                 "a re-sourced window names the core's own state, never a facility")


# ==================================================================================================
# A3 (device) — THE DEVICE WINDOW READS THE DISCOVERY ROWS; A FABRICATED OBSERVATION DOES NOT TRACE
# ==================================================================================================

def _discovery_rows():
    """Three device-discovery rows, one per device the body performs over the settled three-device
    list (block, network, clock), modelling what the C7 P7b body-lane emitter records — each an
    append riding record-pen, each naming the identity the body EXPORTS at bring-up."""
    return [
        {"seq": 1, "action": "device-discovery", "record_time": "2026-09-19T00:00:01+00:00",
         "payload": {"kind": W.DEVICE_DISCOVERY_KIND, "device": "block", "present": True,
                     "identity": "ata present=1"}},
        {"seq": 2, "action": "device-discovery", "record_time": "2026-09-19T00:00:02+00:00",
         "payload": {"kind": W.DEVICE_DISCOVERY_KIND, "device": "network", "present": True,
                     "identity": "class=PASS mac=52:54:00:12:34:56"}},
        {"seq": 3, "action": "device-discovery", "record_time": "2026-09-19T00:00:03+00:00",
         "payload": {"kind": W.DEVICE_DISCOVERY_KIND, "device": "clock", "present": True,
                     "identity": "present=1 epoch=0x68abcdef"}},
    ]


def _traces_to_a_real_discovery_row(obs, rows):
    """THE TRACE CHECK (able to fail). A device observation traces to a real discovery row only if
    the record seq it names is actually present in the discovery rows. A fabricated observation
    names a seq no discovery row carries, and this returns False."""
    live_seqs = {r["seq"] for r in rows}
    return obs.data.get("record_seq") in live_seqs


class TestA3DeviceWindowTracesToADiscoveryRow(unittest.TestCase):

    def test_the_device_window_yields_one_observation_per_discovery_row_traced_to_it(self):
        rows = _discovery_rows()
        window = W.RecordDeviceWindow(source=lambda: rows)
        obs = window.read()
        self.assertEqual(len(obs), 3, "one device observation per discovered device (block/network/clock)")
        self.assertEqual([o.data["device"] for o in obs], ["block", "network", "clock"])
        for o in obs:
            self.assertTrue(_traces_to_a_real_discovery_row(o, rows),
                            "the observation must trace to a real discovery row by its seq")
            # provenance names the RECORD route (and its version), never sysfs/uevent.
            self.assertEqual(o.data["source"], W.RECORD_ROUTE)
            self.assertIn("record", o.window_version)
            self.assertNotIn("sysfs", o.window_version)
            self.assertNotIn("uevent", o.window_version)
            self.assertEqual(o.time_source, seam.TIME_WINDOW_REPORTED)   # the row carries its own time

    def test_the_A3_device_plant_a_fabricated_observation_does_not_trace(self):
        # THE A3 PLANT (can fail): a device observation carrying a record seq that NO discovery row
        # holds — a fabricated event — fails the trace check. The SAME check PASSES a real
        # observation, so it discriminates and is not a check that always fails.
        rows = _discovery_rows()
        window = W.RecordDeviceWindow(source=lambda: rows)
        real = window.read()[0]
        self.assertTrue(_traces_to_a_real_discovery_row(real, rows))    # discriminates: real passes

        fabricated = seam.Observation(
            window="device", window_version=window.version,
            act="device-capability-registered", object="device:phantom",
            occurrence_time="2026-09-19T00:00:00+00:00",
            data={"device": "phantom", "record_seq": 10 ** 9, "source": W.RECORD_ROUTE})
        self.assertFalse(_traces_to_a_real_discovery_row(fabricated, rows),
                         "a fabricated device observation with no discovery row behind it must not trace")

    def test_the_device_window_excludes_its_own_observation_writes(self):
        # The inverted self-audit exclusion: the window's own `observed-device` records are dropped
        # (counted), so reading the record does not observe its own observation-writes.
        rows = _discovery_rows() + [
            {"seq": 4, "action": "observed-device", "record_time": "2026-09-19T00:00:04+00:00",
             "payload": {"kind": W.OBSERVED_DEVICE_KIND, "device": "block"}}]
        window = W.RecordDeviceWindow(source=lambda: rows)
        obs = window.read()
        self.assertEqual(len(obs), 3, "the own observation-write is excluded, not yielded")
        self.assertGreater(window.excluded_events, 0,
                           "the self-audit exclusion must have dropped the window's own write")

    def test_the_device_window_opens_no_sysfs_and_carries_no_host_facility(self):
        # The re-source reads the record the body already serves — it opens no host facility.
        window = W.RecordDeviceWindow(source=lambda: _discovery_rows())
        self.assertEqual(window.route, W.RECORD_ROUTE)
        self.assertIsNone(type(window).host_facility, "the record device window names no host facility")
        cov = window.coverage()
        self.assertIn(W.RECORD_ROUTE, cov["facility"])
        self.assertNotIn("sysfs", cov["facility"])


# ==================================================================================================
# A4 — NOTHING ELSE MOVES
# ==================================================================================================

class TestA4NothingElseMoves(unittest.TestCase):

    def test_act_kinds_is_still_twelve(self):
        from bridge import host_seam as hs
        self.assertEqual(len(hs.ACT_KINDS), 12)

    def test_the_effect_seam_act_kinds_name_no_linux_facility_the_L1_measured_root(self):
        # The measured root of every ABSENT reason: the core's presented effect acts (the twelve
        # ACT_KINDS) name NO Linux facility — so a window's facility genuinely is not presented.
        from bridge import host_seam as hs
        joined = " ".join(hs.ACT_KINDS)
        for facility in ("/proc", "inotify", "mountinfo", "sysfs", "sock_diag", "uevent"):
            self.assertNotIn(facility, joined,
                             "the effect seam names %r — the L1 premise would be false" % facility)

    def test_attested_members_count_unchanged(self):
        # No src engine module was added by P9 — the census lives IN THE EXISTING observe modules
        # (seam.py + windows.py, edited in place) — so the attested-members count does not move.
        # 88 is the count DRIVEN this turn (`len(attestation.ATTESTED_MEMBERS)`); the pin's job is
        # to catch a NEW engine module sneaking into the diff.
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88)

    def test_the_observe_surface_is_unchanged_five_ops_one_per_window(self):
        # P9 adds no op: OP_FOR_WINDOW is still exactly the five, one op per window.
        self.assertEqual(len(seam.OP_FOR_WINDOW), 5)
        self.assertEqual(set(seam.OP_FOR_WINDOW.values()),
                         {"OBSERVE-PROCESS", "OBSERVE-FILE", "OBSERVE-MOUNT",
                          "OBSERVE-DEVICE", "OBSERVE-CONNECTION"})

    def test_the_census_reads_windows_by_static_descriptor_never_opening_a_facility(self):
        # The census names each window's facility from windows.<Window>.host_facility — a STATIC
        # descriptor, not a live probe — so running the census opens no /proc, no inotify, no netlink.
        for cls in (W.ProcessWindow, W.FileWindow, W.MountWindow, W.DeviceWindow, W.ConnectionWindow):
            self.assertTrue(getattr(cls, "host_facility", None),
                            "%s carries no static host_facility descriptor" % cls.__name__)


if __name__ == "__main__":
    unittest.main()
