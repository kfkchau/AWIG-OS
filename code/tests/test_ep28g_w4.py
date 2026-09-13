# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28G W4 — THE LEVER'S SURVIVAL, ASSERTED IN BOTH FORMS.

The wrong reference with the strongest pull is THE BIG LOCK — the region held across the
durability wait — because it is the smallest diff and every atomicity row above passes under
it. Taking it erases the lever SILENTLY: one record ever in flight, the batch always one,
single-threading rebuilt with a lock's name on it. Two detectors, and the pairing is the
point.

  T-REGION-EXCLUDES-THE-BARRIER  the UNIVERSAL, and it lives in `test_ep28g_w1.py` where the
                                 construct is. Cited here rather than rebuilt, because the
                                 pairing is what this file is about.
  T-BATCHING-POSSIBLE            the demoted countable, carrying only what it can support:
                                 under concurrent submitters at least one batch of width >= 2
                                 forms — batching is possible, the lever is alive. IT IS AN
                                 EXISTENTIAL AND IS NOT EVIDENCE FOR THE UNIVERSAL. RED: a
                                 double whose region holds across the sync on every path —
                                 every batch closes at width 1 under load, and it fails on the
                                 COUNTABLE rather than on a duration.
  T-APPENDER-UNTOUCHED           EP-28C's own batteries green at the shipped width AND at
                                 width 1; one barrier per batch from the appender; replies
                                 after the covering sync. RED worlds: CARRIED — EP-28C's own,
                                 cited rather than rebuilt.

AND THE DEMOTED ROW EARNED ITS KEEP FOR A REASON NOBODY PREDICTED. EP-28G's stopped session
derived one plausible shape for the split — release the region from inside the appender, at
each member's publish — which looks correct, keeps `commit.py` intact, and passes every row in
this estate EXCEPT this one: the next decider cannot enqueue until the release, and the
release happens after `_take_batch` has already closed the batch, so every batch closes at
width 1. A guard retained for one reason and load-bearing for another is the argument against
deleting rows that merely look redundant.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from kernel import gate as gate_mod                              # noqa: E402
from kernel import store as store_mod                            # noqa: E402
from kernel.compose import build_full_kernel                     # noqa: E402
from kernel.errors import OpError                                # noqa: E402

ORDINARY_DEF = {"description": "an ordinary op", "params": {"x": "required"},
                "law_cited": "SIGHT-IS-LAW", "object_param": "x", "checks": [],
                # x is the op's object_param — a scalar identity handle, safe inline. Classified
                # STRUCTURAL so this well-formed setup op passes the vocabulary door (design/46
                # member 2; archi :2956 RULING 1 — object_param => structural, not blanket).
                "structural_params": ["x"]}

#: The width these rows are about, DECLARED rather than inherited — the EP-28C precedent. A
#: row whose subject is how wide a batch gets cannot inherit `GOVOS_COMMIT_WIDTH=1`, because at
#: width 1 every batch closes on the width before any other condition is consulted and the row
#: would be asserting the override instead of the mechanism.
BATCHING_WIDTH = 16

WEDGE_S = 30.0


class _OpaqueRegionHeldAcrossTheSync:
    """THE RED WORLD FOR THE EXISTENTIAL: a region built the way a careful engineer would
    build it if nobody had derived the boundary — one lock, taken before the decide and
    released after the record is durable.

    IT IS DELIBERATELY OPAQUE TO THE BARRIER'S OWN GUARD. It never touches the depth counter
    `gate.decide_region_held` reads, so `store._commit_batch`'s assertion stays silent and the
    UNIVERSAL passes in this world. That is the honest model of the hazard: a region built
    with a lock the assertion does not know about. The universal catches a crossing of THIS
    region; it cannot catch a different lock — and the countable can. Each detector catches
    what the other cannot, which is why both are rows."""

    def __init__(self, gate):
        self._gate = gate
        self._lock = threading.RLock()

    def enter(self):
        self._lock.acquire()
        return True

    def exit(self):
        pass                                # released after the wait, by the wrapper below

    def install(self, case):
        real_execute = self._gate.execute
        region = self

        def held_across_the_sync(name, actor, params=None):
            region._lock.acquire()
            try:
                return real_execute(name, actor, params)
            finally:
                region._lock.release()      # AFTER the durability wait inside `execute`
        self._gate.execute = held_across_the_sync
        case.addCleanup(setattr, self._gate, "execute", real_execute)


class WorldCase(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28g-w4-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.rec, os.path.join(self.dir, "blobs"))
        self.store.group_commit.width = BATCHING_WIDTH
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.addCleanup(self.store.close)

    def concurrent_acts(self, n, window_s=0.30):
        """`n` concurrent governed acts through the real gate, with the batch formed BY THE
        WINDOW rather than by luck.

        The window, deliberately, and the reason is EP-28C's: whether a batch forms naturally
        depends on how fast this box's `fdatasync` is, and a test whose subject is the box is a
        test that says nothing about the build. What batching does to real traffic is a
        MEASUREMENT and belongs where a figure about the box belongs. Note what the window
        cannot do: it cannot gather a submitter that never arrives, so a region holding across
        the sync still yields batches of one however long the window is."""
        gc = self.store.group_commit
        gc.closes_on_empty = False
        gc.window_s = window_s
        start = threading.Barrier(n)
        errs = [None] * n

        def one(i):
            start.wait(timeout=WEDGE_S)
            try:
                self.gate.execute("CREATE-OP", "owner",
                                  {"name": "OP%d" % i, "definition": ORDINARY_DEF})
            except BaseException as exc:      # noqa: BLE001 — reported, never swallowed
                errs[i] = exc
        threads = [threading.Thread(target=one, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=WEDGE_S)
        for t in threads:
            self.assertFalse(t.is_alive(), "an act wedged")
        return errs


# =====================================================================================
# T-BATCHING-POSSIBLE — the existential, carrying only what it can support
# =====================================================================================

class BatchingPossibleCase(WorldCase):

    def test_a_batch_of_width_two_or_more_forms_under_concurrent_submitters(self):
        """THE EXISTENTIAL: batching is possible, so the lever is alive. It asserts nothing
        about every path and is NOT evidence for the universal in `test_ep28g_w1.py`."""
        errs = self.concurrent_acts(8)
        self.assertEqual([e for e in errs if e is not None], [])
        gc = self.store.group_commit
        self.assertGreaterEqual(gc.largest_batch, 2,
                                "every batch closed at width 1 under eight concurrent "
                                "submitters — the region is holding across the sync and the "
                                "lever is gone")
        self.assertEqual(len([e for e in self.store.by_action("CREATE-OP")
                              if re.fullmatch(r"OP\d+", (e.get("payload") or {}).get("name", ""))]), 8)

    def test_the_records_of_a_batch_keep_their_own_positions(self):
        """Batching the SYNC is never coalescing records (EP-28C invariant 3), re-asserted at
        the gate level because this EP moved where a record is published: eight acts, eight
        distinct `seq` values, eight attributions."""
        self.concurrent_acts(8)
        recs = [e for e in self.store.by_action("CREATE-OP")
                if re.fullmatch(r"OP\d+", (e.get("payload") or {}).get("name", ""))]
        self.assertEqual(len({r["seq"] for r in recs}), 8)
        self.assertEqual(len({(r.get("payload") or {}).get("name") for r in recs}), 8)

    def test_red_world_a_region_that_holds_across_the_sync_on_EVERY_path(self):
        """THE RED WORLD, GENERATED: a region held from before the decide until after the
        record is durable, on every path. Every batch closes at width 1 under the same load
        and the same window, because the second submitter cannot arrive to be gathered.

        FAILS ON THE COUNTABLE, NEVER ON A DURATION — `largest_batch` is an integer the loop
        maintains, and this world's failure is that it stays at 1 no matter how long the
        window is held open."""
        _OpaqueRegionHeldAcrossTheSync(self.gate).install(self)
        errs = self.concurrent_acts(8)
        self.assertEqual([e for e in errs if e is not None], [],
                         "the red world broke something other than batching")
        gc = self.store.group_commit
        self.assertEqual(gc.largest_batch, 1,
                         "the big-lock double still formed a batch of %d, so this red world "
                         "does not exhibit what it claims" % gc.largest_batch)
        # AND THE UNIVERSAL PASSES IN THIS WORLD, which is the pairing's whole point: this
        # region is opaque to the barrier's guard, so the assertion never fires and only the
        # countable notices. Neither detector subsumes the other.
        self.assertEqual(len([e for e in self.store.by_action("CREATE-OP")
                              if re.fullmatch(r"OP\d+", (e.get("payload") or {}).get("name", ""))]), 8)

    def test_the_two_detectors_catch_different_worlds(self):
        """THE PAIRING, ASSERTED. The one-path crossing (W1's red world) reds the universal
        and PASSES the countable; the every-path opaque hold reds the countable and PASSES the
        universal. Stated as a row so a later seat cannot delete either as redundant."""
        # (a) the one-path crossing: the assertion fires, and batching elsewhere is untouched.
        self.gate.region.enter()
        try:
            with self.assertRaises(store_mod.RegionHeldAtBarrier):
                self.store._commit_batch([])
        finally:
            self.gate.region.exit()
        errs = self.concurrent_acts(4)
        self.assertEqual([e for e in errs if e is not None], [])
        self.assertGreaterEqual(self.store.group_commit.largest_batch, 2,
                                "batching died in the world the universal catches, so the "
                                "countable would have caught it too and the pairing claim "
                                "is wrong")


# =====================================================================================
# T-APPENDER-UNTOUCHED — EP-28C's batteries, re-run at both widths
# =====================================================================================

class AppenderUntouchedCase(unittest.TestCase):
    """THE FENCE'S OWN CONDITION, DISCHARGED. The conditional widening of `store.py` and
    `commit.py` is admitted only for the named consequence, and only if the appender loop, the
    single barrier per batch and reply-after-covering-sync are byte-untouched in BEHAVIOUR and
    RE-PROVEN BY EP-28C's OWN BATTERIES. This row is that re-proof, run rather than asserted.

    IN A SUBPROCESS, because width is read once per store from the environment and a row whose
    subject is the width-1 arm cannot set it after the stores exist. The verifier runs the same
    two commands from the EP; this row runs them so a green here is not conditional on anyone
    remembering to."""

    BATTERIES = ["tests.test_ep28c_w1", "tests.test_ep28c_w2", "tests.test_ep28c_w3"]

    def _run(self, env_extra=None):
        env = dict(os.environ)
        env.pop("GOVOS_COMMIT_WIDTH", None)
        env.update(env_extra or {})
        return subprocess.run([sys.executable, "-m", "unittest"] + self.BATTERIES,
                              cwd=REPO, capture_output=True, text=True, env=env, timeout=600)

    def test_ep28c_batteries_are_green_at_the_shipped_width(self):
        out = self._run()
        self.assertEqual(out.returncode, 0, out.stderr[-4000:])

    def test_ep28c_batteries_are_green_at_width_one(self):
        out = self._run({"GOVOS_COMMIT_WIDTH": "1"})
        self.assertEqual(out.returncode, 0, out.stderr[-4000:])


class OneBarrierPerBatchCase(WorldCase):

    def test_one_barrier_per_batch_issues_from_the_appender(self):
        """The appender's contract, at the gate level: N acts sharing one batch pay ONE
        barrier between them, and it is issued from the appender rather than from a decide."""
        syncs = []
        real = store_mod.os.fdatasync
        gc = self.store.group_commit
        before = gc.batches                 # the founding's own batches are not this measure

        def spy(fd):
            syncs.append(gate_mod.decide_region_held())
            return real(fd)
        store_mod.os.fdatasync = spy
        try:
            self.concurrent_acts(8)
        finally:
            store_mod.os.fdatasync = real
        batches = gc.batches - before
        self.assertEqual(len(syncs), batches,
                         "%d barriers for %d batches — a batch shares exactly one"
                         % (len(syncs), batches))
        self.assertLess(batches, 8,
                        "eight acts produced %d batches, so nothing was shared and this row "
                        "asserted the property over a world without batching" % batches)
        self.assertEqual(set(syncs), {False})

    def test_every_reply_follows_the_covering_sync(self):
        """Invariant 1 at the act's boundary, under concurrency: no act returns before a
        barrier has run since its own record was published. Asserted on the ORDER of observed
        events, not on a clock."""
        events = []
        guard = threading.Lock()
        real = store_mod.os.fdatasync

        def spy(fd):
            with guard:
                events.append(("sync", len(self.store.all())))
            return real(fd)
        store_mod.os.fdatasync = spy
        gc = self.store.group_commit
        gc.closes_on_empty = False
        gc.window_s = 0.25
        start = threading.Barrier(6)

        def one(i):
            start.wait(timeout=WEDGE_S)
            rec = self.gate.execute("CREATE-OP", "owner",
                                    {"name": "OP%d" % i, "definition": ORDINARY_DEF})
            with guard:
                events.append(("reply", rec["seq"]))
        threads = [threading.Thread(target=one, args=(i,)) for i in range(6)]
        try:
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=WEDGE_S)
        finally:
            store_mod.os.fdatasync = real
        for t in threads:
            self.assertFalse(t.is_alive(), "an act wedged")
        covered = 0
        for kind, value in events:
            if kind == "sync":
                covered = max(covered, value)
            else:
                self.assertLessEqual(value, covered,
                                     "an act replied at seq %d with only %d records covered "
                                     "by a barrier — a reply about an act that may never "
                                     "have happened" % (value, covered))
        self.assertGreaterEqual(len([e for e in events if e[0] == "reply"]), 6)


if __name__ == "__main__":
    unittest.main()
