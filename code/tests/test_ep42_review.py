# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (hash chain, signed door, vault, append-only record). NON-GOAL: no offensive capability
# of any kind — these regressions prove a governed record is edit-evident, a signed door refuses an
# unsigned act, the vault has no read path, and the vocabulary holds no record-removal function.
# Full declaration: SCOPE-STATEMENT.md.
"""EP-42 (the campaign-4 review) — the review's committed probes land as standing regression rows.

The review's independent whole-world legs (tools/mentor-probes/campaign4_sealed_world_probes.py) run
here in the per-module gate so they outlive the review session (the R14 rule applied to the reviewer
itself; charter: "every verification probe lands as a regression test"). Each probe function carries
its own red world / positive control, so a column that stops being able to fail reds this file.

SHAPE OVER MODELLED KEY MATERIAL (design/37 §9 as-built): the signed door checks
possession-plus-provenance, not real cryptography; KEY-MATERIAL-REAL is the named next unit.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "mentor-probes"))

import campaign4_sealed_world_probes as swp                                       # noqa: E402


def _run(probe_fn):
    """Run one probe function in isolation and return its (name, ok) results."""
    swp.RESULTS = []
    probe_fn()
    return list(swp.RESULTS)


class TestSealedWorldProbesLandAsRegressions(unittest.TestCase):

    def _assert_all_pass(self, results):
        self.assertTrue(results, "a probe produced no results — it did not run")
        failed = [name for name, ok in results if not ok]
        self.assertEqual(failed, [], "probe columns failed: %s" % failed)

    def test_cold_whole_world_roundtrip(self):
        # T-TOTAL-ROUNDTRIP-4 shape: rebuild a sealed, keyed, signed world from the record alone.
        self._assert_all_pass(_run(swp.probe_cold_roundtrip))

    def test_chain_red_world_detects_and_locates(self):
        # the chain column proven able to fail: an edited chained record is detected and located.
        self._assert_all_pass(_run(swp.probe_chain_red_world))

    def test_signed_door_refuses_unsigned_accepts_signed(self):
        self._assert_all_pass(_run(swp.probe_signed_door))

    def test_vault_still_closed(self):
        self._assert_all_pass(_run(swp.probe_vault_still_closed))

    def test_no_delete_census_estate_wide(self):
        # design/46 capability-absence over the whole vocabulary + substrate, with a planted control.
        self._assert_all_pass(_run(swp.probe_no_delete_census))


if __name__ == "__main__":
    unittest.main()
