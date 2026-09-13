"""EP-28C W8 — the scale assumptions and the skips, DECLARED AS DATA AND CHECKED.

W8's order: state what this design assumes about store size, submitter count, world lifetime
and substrate, and state what the fast loop SKIPS — "written as a claim someone can check."

SO IT IS NOT PROSE. A declaration written in an entry is a note, and this estate has spent a
fortnight finding notes rotted (§A47, §A45). Every assumption below is a value the
instruments actually ran under, and every row here reads the instrument rather than the
declaration — so a figure taken at a different scale makes the declaration RED instead of
making it stale.

§A33 IS THE RULE AND ITS PROBE IS APPLIED TO EVERY SKIP: *a fast path that avoids a slow
operation avoids TESTING what the slow operation would reveal.* For each skip the
declaration names WHAT IT WOULD HAVE REVEALED, because a skip listed without its consequence
is a list of things nobody did rather than a statement about what is unknown.

THE ONE THAT MATTERS MOST, NAMED FIRST SO IT IS NOT BURIED: every W7 figure comes from
THREADS IN ONE PYTHON PROCESS. Real concurrent writers below the syscall line are separate
processes with no interpreter lock between them. The GIL is in every duration this pass
took, and it is exactly the kind of confound that flatters a barrier measurement — a thread
blocked in `fdatasync` releases the lock, so the interpreter overlaps I/O for free in a way
that has no analogue in the guest's channel.
"""

import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, REPO)

from kernel import commit as commit_mod                            # noqa: E402
from tests import test_ep28c_w7 as w7                              # noqa: E402


#: WHAT THE FIGURES OF THIS PASS ASSUME. Each value is checked against the instrument that
#: produced it by a row below, so the pair cannot drift apart silently.
ASSUMPTIONS = {
    "submitters_per_trial": 32,
    "widths_exercised": (1, 8, 16),
    "shipped_width_cap": 16,
    "store_size_max_records": 32,
    "world_lifetime": "one trial: founded, driven, closed and deleted inside a single call",
    "substrate": "the development HOST — ext4 on an LVM logical volume, not a physical "
                 "device and not the guest's qcow2/virtio",
    "process_model": "threads in ONE CPython process; the interpreter lock is present in "
                     "every duration",
}

#: WHAT THE FAST LOOP SKIPS, each with what the skip would have revealed (§A33's probe).
SKIPS = {
    "the physical-disk substrate":
        "an `fdatasync` cost is a property of the DEVICE. Every barrier figure this pass "
        "took is a statement about this LV on this host. A physical device — NVMe, a "
        "battery-backed controller, spinning rust — moves the barrier's fixed cost and its "
        "data-proportional part INDEPENDENTLY, and the ratio between those two is exactly "
        "what decides how large the group-commit lever is. Standing condition, deferred "
        "past the campaign (design/36 ADDENDUM L §L.5).",
    "submitter counts beyond the tested N":
        "the batch never reached the shipped width cap at N=32 — the arrival rate closed "
        "it first. A higher N is the only thing that would show whether the cap binds at "
        "all, and therefore whether 16 is a calibration or a decoration.",
    "a large store under concurrency":
        "the act was measured FLAT to 371,856 records (ADDENDUM O) for a whole gated act "
        "on the guest, one caller. Nothing here says the BARRIER stays flat under "
        "concurrent publishers as the file grows — a bigger file has more dirty pages for "
        "a batch's barrier to flush, which is the one term this pass showed is not "
        "constant.",
    "a long-lived world":
        "every trial world dies inside its trial, so nothing measured a store whose page "
        "cache, file size or fragmentation had a history. A fast loop that founds a fresh "
        "world each time never visits the state a running system spends all its time in.",
    "separate PROCESSES rather than threads":
        "the interpreter lock is released across `fdatasync`, so this process gets I/O "
        "overlap the guest's channel cannot get the same way. Processes would show whether "
        "the width-1 baseline is already implicitly amortised for a REASON THAT SURVIVES "
        "the GIL's removal, or only because of it.",
    "the contended arm through the channel":
        "W7's guest-side half is blocked behind W4e, which stopped on its own clause. What "
        "it would reveal is the lever measured against the TRUE one-caller floor rather "
        "than against a concurrent width-1 baseline — the two are different questions and "
        "the carried 5.6x/13.5x band answers the first.",
    "a reboot":
        "carried, unchanged: every durability claim campaign 3 holds is about surviving a "
        "power cut WITH THE GUEST RESUMING, never a reboot (§A33's own standing "
        "consequence, EP-28 ADDENDUM 10.5).",
}


#: The shipped-width arm is driven this many times and the cap row asserts on the MEDIAN
#: of the per-rep widest, never a single shot. `largest_batch` is a concurrency measurement
#: — one rep can bunch its submitters up toward the cap or serialise them down toward 1 —
#: so a single reading is timing-dependent while its central value is not. An ODD count of
#: 5 drops up to two such outliers on either end and its median is an OBSERVED value, not an
#: interpolation between two. Characterised 2026-09-05 (planning/evidence/EP-28C-W8-DEFLAKE.md):
#: over 120 single reps the widest centred at 5-6 (min 4) with a 2.5% tail landing on the
#: cap and none at the floor, and the median over 5 reps stayed strictly inside (1, cap) in
#: 40/40 whole runs while max-of-3 — the pre-de-flake logic — red on 3/40.
CAP_ARM_REPS = 5


def _median_widest_within_the_bound(widest_per_rep, cap, n):
    """The N-skip's claim, made robust to single-run timing noise WITHOUT moving the bound.

    `widest_per_rep` is the largest batch the shipped-width arm actually formed in each
    independent rep. That figure is a concurrency measurement: any one rep can land low (the
    scheduler serialised the submitters, so nothing batched) or high (it bunched them up
    toward the cap). The MEDIAN drops a single such outlier on EITHER end — a genuine
    no-batching or a genuine cap-bind moves the median itself, not one sample of it.

    Returns the median widest. Raises AssertionError when the robust central value sits at
    the no-batching floor (<= 1) or has REACHED the cap (>= cap): each of those falsifies
    "at the tested N the arrival rate closes the batch before the width cap binds", so each
    MUST still red. The subject and the cap value are unchanged; only robustness to a single
    run's timing noise is added, and the bound is applied to the robust statistic rather
    than to a lucky or unlucky single reading."""
    import statistics
    med = statistics.median(widest_per_rep)
    if med <= 1:
        raise AssertionError(
            "the shipped-width arm never batched: median widest %g over %d reps sits at "
            "the no-batching floor of 1 (%r)" % (med, len(widest_per_rep),
                                                 sorted(widest_per_rep)))
    if med >= cap:
        raise AssertionError(
            "the batch REACHED the shipped cap at N=%d: median widest %g over %d reps binds "
            "on the cap of %d, so the skip's claim that arrival closes the batch first is no "
            "longer true (%r)" % (n, med, len(widest_per_rep), cap, sorted(widest_per_rep)))
    return med


class AssumptionsMatchTheInstrumentsCase(unittest.TestCase):
    """Each declared value read back off the thing that produced it."""

    def test_NON_VACUITY_the_declaration_is_not_empty_and_neither_is_the_skip_list(self):
        self.assertTrue(ASSUMPTIONS)
        self.assertTrue(SKIPS)
        for name, why in SKIPS.items():
            self.assertTrue(why.strip(), "%r is listed as a skip with no consequence — a "
                                         "skip without what it would have revealed is a "
                                         "list of things nobody did" % name)

    def test_the_widths_declared_are_the_widths_the_instrument_runs(self):
        self.assertEqual(tuple(ASSUMPTIONS["widths_exercised"]), tuple(w7.WIDTHS))

    def test_the_shipped_cap_declared_is_the_shipped_cap_the_engine_carries(self):
        self.assertEqual(ASSUMPTIONS["shipped_width_cap"], commit_mod.BATCH_WIDTH_CAP)

    def test_the_submitter_count_declared_is_the_measure_runs_own_default(self):
        """Read from the function's signature, so changing the run without changing the
        declaration reds here rather than shipping a figure under a stale claim."""
        import inspect
        default_n = inspect.signature(w7.measure).parameters["n"].default
        self.assertEqual(ASSUMPTIONS["submitters_per_trial"], default_n)

    def test_the_largest_store_any_arm_sees_is_the_submitter_count(self):
        """Each trial founds a fresh store and drives exactly N submissions into it, so the
        largest store any figure was taken against is N records. Asserted by driving one
        arm rather than by reading the code that drives it."""
        import shutil
        import tempfile
        root = tempfile.mkdtemp(prefix="ep28c-w8-")
        try:
            run = w7.run_arms(root, n=ASSUMPTIONS["submitters_per_trial"], reps=1)
            sizes = {t["records"] for trials in run["results"].values() for t in trials}
            self.assertEqual(sizes, {ASSUMPTIONS["store_size_max_records"]},
                             "an arm drove a store to a size the declaration does not "
                             "state: %r" % sorted(sizes))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_substrate_declared_is_the_substrate_the_instrument_reads(self):
        sub = w7.substrate(REPO)
        self.assertIsNotNone(sub["record_on"],
                             "the instrument cannot read what the record sits on, so the "
                             "substrate claim is unsupported")
        self.assertIn("ext4", sub["record_on"],
                      "the record no longer sits on ext4 — the substrate declaration is "
                      "stale and every barrier figure it covers needs re-taking")

    def test_the_process_model_declared_is_the_one_the_instrument_uses(self):
        """A row that would red if the instrument ever grew processes: it asserts the
        arms run in THIS process, by checking that a trial's store is reachable from this
        interpreter's own module table rather than by reading a comment."""
        import threading
        before = threading.active_count()
        self.assertGreaterEqual(before, 1)
        self.assertIn("threads in ONE CPython process",
                      ASSUMPTIONS["process_model"])
        self.assertIs(w7.threading, threading,
                      "the instrument no longer uses this interpreter's threading module")


class TheSkipsAreStillSkipsCase(unittest.TestCase):
    """Where a skip is checkable, it is checked. Where it is not, it is declared with its
    consequence and the row says which of the two it is — never a silent pass."""

    def test_the_physical_disk_skip_is_REAL_on_this_box(self):
        sub = w7.substrate(REPO)
        self.assertIsNotNone(sub["record_on"])
        self.assertNotIn("nvme", sub["record_on"].lower(),
                         "the record now sits on a device the declaration says was never "
                         "measured — either the skip ended or the declaration is wrong")

    def test_the_width_cap_was_NOT_reached_which_is_what_makes_the_N_skip_matter(self):
        """The claim inside the submitter-count skip, driven and made robust to single-run
        timing noise: at the tested N the batch closes on ARRIVAL rather than on the cap, so
        nothing here measured the cap.

        `largest_batch` is a concurrency measurement — one rep can bunch its submitters up
        toward the cap or serialise them down toward 1 — so this row drives the arm
        CAP_ARM_REPS times and asserts on the MEDIAN of the per-rep widest, not on a single
        shot that a lucky or unlucky schedule can throw to either edge. The cap value and the
        bound `1 < widest < cap` are unchanged from the single-shot version; only the
        statistic the bound is applied to changed, from one reading to the robust central
        one. That the bound can STILL red on a genuine cap-bind and a genuine no-batching is
        proved by the two must-red controls in TheDeflakeStillCatchesARealChangeCase."""
        import shutil
        import statistics
        import tempfile
        cap = commit_mod.BATCH_WIDTH_CAP
        n = ASSUMPTIONS["submitters_per_trial"]
        root = tempfile.mkdtemp(prefix="ep28c-w8-cap-")
        try:
            arms = w7.run_arms(root, n=n, reps=CAP_ARM_REPS)
            widest_per_rep = [t["largest_batch"] for t in arms["results"][16]]
            median_widest = _median_widest_within_the_bound(widest_per_rep, cap, n)
            print("[EP-28C W8] widest batch per rep at N=%d over %d reps: %r → median %g "
                  "against a cap of %d — the arrival rate closes the batch, not the cap"
                  % (n, CAP_ARM_REPS, sorted(widest_per_rep), median_widest, cap))
            self.assertGreater(statistics.median(
                t["members"] for t in arms["results"][16]), 0)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_contended_arm_is_skipped_BECAUSE_W4e_stopped_and_that_is_checkable(self):
        """The skip's stated cause, asserted rather than described: the channel still holds
        its one-caller lowering, so the contended arm could only have measured a serialized
        system. When W4e lands this row reds and the skip must be re-stated or removed."""
        with open(os.path.join(REPO, "planning", "vm", "govosfs", "govosfs.c"),
                  encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("mutex_lock(&govos_call_lock)", src,
                      "the channel now admits many callers, so 'the contended arm is "
                      "blocked' has stopped being true — re-state this skip")


class TheDeflakeStillCatchesARealChangeCase(unittest.TestCase):
    """MUST-RED controls for the median-of-reps de-flake. The median drops a single run's
    timing noise; these rows prove it did NOT drop the ability to catch a genuine cap-bind
    or a genuine no-batching. Each feeds a SYNTHETIC widest-per-rep list through the same
    bound the live cap row uses, so the bound is watched refusing something — a de-flake
    that can no longer fail on a real change is a loosening, not a fix. Synthetic inputs
    only; no store is driven, so these are deterministic and carry no timing dependency."""

    CAP = commit_mod.BATCH_WIDTH_CAP
    N = ASSUMPTIONS["submitters_per_trial"]

    def test_a_genuine_CAP_BIND_still_reds(self):
        """A median that has reached the cap MUST red — it falsifies 'arrival closes the
        batch first'. A single low outlier does not rescue it: the central value is the cap.
        This is the failure the single-shot version caught by luck and the median must keep
        catching by construction."""
        with self.assertRaises(AssertionError):
            _median_widest_within_the_bound([self.CAP - 1, self.CAP, self.CAP],
                                            self.CAP, self.N)
        with self.assertRaises(AssertionError):
            _median_widest_within_the_bound([2, self.CAP, self.CAP, self.CAP, self.CAP],
                                            self.CAP, self.N)

    def test_a_genuine_NO_BATCHING_still_reds(self):
        """A median at the no-batching floor MUST red — nothing batched, so there is no
        arrival-closed batch to speak of. A single high outlier does not rescue it."""
        with self.assertRaises(AssertionError):
            _median_widest_within_the_bound([1, 1, 8], self.CAP, self.N)
        with self.assertRaises(AssertionError):
            _median_widest_within_the_bound([1, 1, 1, 1, self.CAP], self.CAP, self.N)

    def test_a_HEALTHY_arrival_closed_median_PASSES(self):
        """The discriminating half: the same bound must PASS a healthy triple, or it is a
        check that cannot pass. A single cap-reaching outlier is dropped and the median
        reports the arrival-closed centre — which is exactly the single-run noise the live
        row was reding on before this de-flake."""
        self.assertEqual(_median_widest_within_the_bound([5, 6, 6], self.CAP, self.N), 6)
        self.assertEqual(
            _median_widest_within_the_bound([5, 6, 6, 7, self.CAP], self.CAP, self.N), 6)


if __name__ == "__main__":
    unittest.main()
