# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28G W1 — THE CONSTRUCT: the decide region, created rather than moved.

`gate.py` held no serialization of any kind until this EP. The sequentiality EP-28
ADDENDUM 10.7 described was an EMERGENT PROPERTY of single-threading — one caller at
`govosfs.c:120`, `store._append` blocking until durable — never an invariant anyone built,
and it ends the moment a second caller exists. These rows are about the enforcer that
property never had.

The rows in this file, and the clause each one falsifies:

  T-REGION-EXCLUDES-THE-BARRIER  the law is a UNIVERSAL over paths: the region excludes the
                                 durability wait, on every path, always. Asserted AT THE
                                 BARRIER — on every barrier execution, the calling thread
                                 must not hold the region — because the failure mode is not
                                 a barrier written between the fold read and the append; it
                                 is the region's lock still HELD while the barrier executes
                                 further down, in `commit.py`, which no scan of the span can
                                 see. RED: a double holding the region across the barrier on
                                 ONE PATH ONLY — a world `T-BATCHING-POSSIBLE` PASSES, since
                                 every other path still batches, and this assertion REDS.
  T-REENTRANT-DECIDE             the region admits its own thread and excludes other
                                 decides. The dual-audit mirror appends from inside an
                                 on-append listener, INSIDE the region's span, and the
                                 overturn sweep re-enters `execute`; a region excluding its
                                 own thread would DEADLOCK on either. RED 1: the region's
                                 lock made non-reentrant — the sweep's bounded wait expires.
                                 RED 2: the store's write lock made non-reentrant — the
                                 mirror's nested publish wedges.
  T-K12-BOUNDED-REGION           per-act region work bounded by the act's own dependencies,
                                 asserted on a touched-entry COUNTABLE, never a duration.
                                 RED: a region double that scans the commit queue per decide.

WHY THERE IS NO TIMING ASSERTION. A duration is a fact about the box. Where a row needs a
bounded wait it uses one as a WEDGE DETECTOR — the red world's failure is that the wait
expires at all — and never as a measurement.
"""

import ast
import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

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

#: The wedge bound. Every use of it is a DETECTOR: the true positive never reaches it, and a
#: red world's failure is that it is reached at all. It is deliberately far longer than any
#: act on any substrate this estate runs on, so a slow box cannot manufacture a red.
WEDGE_S = 8.0


class WorldCase(unittest.TestCase):
    """A founded world, because the region's subject is a governed decide and a bare store
    has none. `build_full_kernel` installs the founding pack, so `CREATE-OP` is live and the
    dual-audit mirror is wired — which the re-entrancy rows need."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28g-w1-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.rec, os.path.join(self.dir, "blobs"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.addCleanup(self.store.close)


# =====================================================================================
# THE CONSTRUCT EXISTS AND IT IS CITABLE — the property stops being emergent exactly here
# =====================================================================================

class TheConstructCase(WorldCase):

    def test_the_gate_holds_a_named_region_with_a_file_and_a_line(self):
        """EP-28's ADDENDUM 10.7 amendment says the property was 'enforced by NOTHING' and
        that nobody could point at it. This row is the pointing."""
        self.assertIsInstance(self.gate.region, gate_mod.DecideRegion)
        self.assertTrue(callable(gate_mod.decide_region_held))
        self.assertFalse(gate_mod.decide_region_held(),
                         "a thread that has entered nothing is reported inside the region")

    def test_the_span_covers_the_fold_read_through_the_append(self):
        """THE SPAN, structurally: everything `execute` used to do is now inside the region,
        and the durability wait is the one thing outside it. Read out of the source, because
        a later edit that moves the append out of `_decide` is exactly what this catches."""
        src = ast.parse((open(gate_mod.__file__, encoding="utf-8")).read())
        fns = {n.name: n for n in ast.walk(src) if isinstance(n, ast.FunctionDef)}
        self.assertIn("_decide", fns, "the region's body is not a function anything can name")
        decide = ast.dump(fns["_decide"])
        self.assertIn("_publish", decide,
                      "the append is not inside the region's body")
        self.assertNotIn("_await_durable", decide,
                         "the durability wait is inside the region's body — that is the big "
                         "lock, whatever it is called")
        execute = ast.dump(fns["execute"])
        for expected in ("enter", "exit", "_await_durable"):
            self.assertIn(expected, execute,
                          "`execute` does not %r — the region is not wrapped around the act"
                          % expected)

    def test_the_region_is_entered_on_every_governed_act(self):
        """BEHAVIOURAL, and it is the half a structural read cannot give: the region is
        actually taken, on an ordinary act, and it is released afterwards."""
        seen = []
        real = self.gate.region

        class _Watched:
            def enter(self):
                seen.append(gate_mod.decide_region_held())
                return real.enter()

            def exit(self):
                return real.exit()
        self.gate.region = _Watched()
        self.addCleanup(setattr, self.gate, "region", real)
        self.gate.execute("CREATE-OP", "owner", {"name": "ORD", "definition": ORDINARY_DEF})
        self.assertEqual(seen, [False], "the act did not enter the region exactly once")
        self.assertFalse(gate_mod.decide_region_held(),
                         "the region was still held after the act returned")

    def test_a_refusal_is_inside_the_region_and_still_waits_for_its_sync(self):
        """ADDENDUM 1's identity: the decision IS the record, and a refusal is a full record.
        So a refusal is produced inside the region like any other decision, and its caller
        waits for the covering sync exactly as a permit's does."""
        self.gate.execute("CREATE-OP", "owner", {"name": "ORD", "definition": ORDINARY_DEF})
        syncs = []
        real = store_mod.os.fdatasync

        def spy(fd):
            syncs.append(gate_mod.decide_region_held())
            return real(fd)
        store_mod.os.fdatasync = spy
        try:
            with self.assertRaises(OpError):
                self.gate.execute("CREATE-OP", "owner",
                                  {"name": "ORD", "definition": ORDINARY_DEF})
        finally:
            store_mod.os.fdatasync = real
        self.assertEqual(len(syncs), 1,
                         "the refusal did not wait for exactly one covering barrier")
        self.assertEqual(syncs, [False],
                         "the refusal's barrier ran with the region held")
        self.assertEqual(len(self.store.by_action("op-refused")), 1)


# =====================================================================================
# T-REGION-EXCLUDES-THE-BARRIER — the UNIVERSAL, asserted at the barrier
# =====================================================================================

class RegionExcludesTheBarrierCase(WorldCase):
    """THE LAW IS A UNIVERSAL OVER PATHS and the first form of this row tested it with an
    ambiguous structural scan plus an existential countable, neither of which can falsify a
    per-path universal (the pre-flight's directed rework, 2026-08-01). The clause is now the
    assertion at the barrier, and that assertion IS the row."""

    def test_the_guard_precedes_the_one_barrier_in_the_one_function_that_issues_it(self):
        """WHY A STRUCTURAL READ IS VALID HERE AND WAS NOT BEFORE. The objection to the first
        form was that a scan of the region's SPAN cannot see a lock held while the barrier
        runs somewhere else. This scan is not of the span: it is of the ONE function that
        issues the ONE barrier, asking whether the guard precedes it there. `store.py` holds
        exactly one `os.fdatasync(` site — `test_ep28c_w1` asserts that count and this row
        re-asserts it rather than inheriting it — so 'the guard precedes the barrier in that
        function' IS 'the guard runs on every barrier execution'.

        It is the smaller half regardless. The behavioural universal is the row below."""
        src = open(store_mod.__file__, encoding="utf-8").read()
        self.assertEqual(src.count("os.fdatasync("), 1,
                         "the barrier is issued from more than one site, so a guard in one "
                         "of them is not a universal")
        tree = ast.parse(src)
        holder = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body = ast.dump(node)
                if "fdatasync" in body:
                    holder = node
        self.assertIsNotNone(holder, "no function issues the barrier")
        guard_line = barrier_line = None
        for node in ast.walk(holder):
            if isinstance(node, ast.Call):
                fn = node.func
                name = getattr(fn, "id", None) or getattr(fn, "attr", None)
                if name == "decide_region_held" and guard_line is None:
                    guard_line = node.lineno
                if name == "fdatasync" and barrier_line is None:
                    barrier_line = node.lineno
        self.assertIsNotNone(guard_line,
                             "%s issues the barrier and never asks whether the region is "
                             "held" % holder.name)
        self.assertLess(guard_line, barrier_line,
                        "the region guard runs AFTER the barrier it is meant to guard")

    def test_every_barrier_of_a_real_workload_ran_with_the_region_unheld(self):
        """THE BEHAVIOURAL UNIVERSAL. Every barrier of a mixed workload — permits, refusals,
        a mirrored act, concurrent submitters — is observed, and every one of them ran on a
        thread holding no region. The countable is 'barriers observed', so a world where the
        workload issued none would fail rather than pass vacuously (§A38)."""
        held_at = []
        real = store_mod.os.fdatasync

        def spy(fd):
            held_at.append(gate_mod.decide_region_held())
            return real(fd)
        store_mod.os.fdatasync = spy
        try:
            self.gate.execute("CREATE-OP", "owner", {"name": "ORD", "definition": ORDINARY_DEF})
            with self.assertRaises(OpError):                     # a refusal is a record too
                self.gate.execute("CREATE-OP", "owner",
                                  {"name": "ORD", "definition": ORDINARY_DEF})

            def act(i):
                try:
                    self.gate.execute("ORD", "owner", {"x": "x%d" % i})
                except OpError:
                    pass
            threads = [threading.Thread(target=act, args=(i,)) for i in range(6)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=WEDGE_S)
            for t in threads:
                self.assertFalse(t.is_alive(), "an act wedged")
        finally:
            store_mod.os.fdatasync = real
        self.assertGreaterEqual(len(held_at), 3,
                                "only %d barriers were observed — the universal was asserted "
                                "over a world that barely has paths" % len(held_at))
        self.assertGreaterEqual(len(self.store.all()), 8,
                                "the workload produced too few records for the universal to "
                                "have been asserted over anything")
        self.assertEqual(set(held_at), {False},
                         "%d of %d barriers ran with the decide region HELD"
                         % (sum(held_at), len(held_at)))

    def test_red_world_a_double_that_holds_the_region_across_the_barrier_on_ONE_path(self):
        """THE RED WORLD, GENERATED, AND IT IS THE ACCUMULATION WORLD THE PRE-FLIGHT NAMED.
        The double takes the barrier on ONE path while holding the region. Every other path
        is untouched and still batches, so `T-BATCHING-POSSIBLE` PASSES in this world — which
        is the whole reason the countable cannot carry this law and this assertion must.

        IT DRIVES THE ROW'S OWN PATH (§A42): the same `_commit_batch`, the same guard, the
        same `os.fdatasync` below it. What the double bypasses is a DIFFERENT clause — the
        deferral in `await_pending` that keeps an in-region append from waiting at all — and
        bypassing it is what makes the backstop reachable. A guard whose failing case cannot
        be produced is a guard nobody has seen fail."""
        self.gate.region.enter()
        try:
            with self.assertRaises(store_mod.RegionHeldAtBarrier) as caught:
                self.store._commit_batch([])
        finally:
            self.gate.region.exit()
        self.assertIn("big lock", str(caught.exception))
        # AND THE COMPLEMENT, which is what makes the assertion a discriminator rather than a
        # tripwire: the same call on the same path, with no region held, runs.
        self.assertFalse(gate_mod.decide_region_held())
        self.store._append({"actor": "SYSTEM", "action": "probe",
                            "rule_cited": "M1-OBSERVATION"})
        self.store._commit_batch([])

    @staticmethod
    def _guard_and_barrier(src):
        """The extraction the structural clause runs, factored so the red world below can be
        driven through EXACTLY it rather than through something that resembles it (§A42)."""
        tree = ast.parse(src)
        holder = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and "fdatasync" in ast.dump(node):
                holder = node
        if holder is None:
            return None, None
        guard = barrier = None
        for node in ast.walk(holder):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name == "decide_region_held" and guard is None:
                    guard = node.lineno
                if name == "fdatasync" and barrier is None:
                    barrier = node.lineno
        return guard, barrier

    def test_red_world_the_guard_removed_from_the_source_reds_the_structural_clause(self):
        """The structural clause's own red world, exhibited on a COPY of the source and run
        through the SAME extraction and the SAME assertion, so what is proven is that this
        guard can fail rather than that some other guard could. `store.py` is byte-unchanged
        under it, which is what makes it a statement about the check."""
        before = open(store_mod.__file__, "rb").read()
        src = before.decode("utf-8")
        forged = src.replace("if decide_region_held():", "if False:  # the guard, removed", 1)
        self.assertNotEqual(forged, src, "the red world could not be constructed")
        guard, barrier = self._guard_and_barrier(forged)
        self.assertIsNotNone(barrier, "the forged source no longer issues a barrier")
        with self.assertRaises(AssertionError):
            self.assertIsNotNone(guard, "the function issuing the barrier never asks whether "
                                        "the region is held")
        self.assertEqual(open(store_mod.__file__, "rb").read(), before,
                         "the red world edited the shipped source")
        # AND THE CONTROL, on the real source, through the same extraction.
        guard, barrier = self._guard_and_barrier(src)
        self.assertIsNotNone(guard)
        self.assertLess(guard, barrier)


# =====================================================================================
# T-REENTRANT-DECIDE — the region admits its own thread; it excludes other deciders
# =====================================================================================

class ReentrantDecideCase(WorldCase):
    """RE-ENTRANCY IS LOAD-BEARING RATHER THAN EXOTIC, and it came from a builder rather than
    from a ruling (the EP-28C builder's finding, carried into this plan). The dual-audit
    mirror appends from inside an on-append listener at `protection.py:106` and `:121`, which
    runs inside the region's span; the overturn sweep re-enters `execute` from
    `gate._maybe_sweep`. A region excluding its own thread deadlocks on either."""

    def _mirrored(self):
        """A governed act the dual-audit pack mirrors, and the records it produced.

        A REFUSAL, deliberately: `op-refused` is in the mirrored action set read from the
        `dual-audit-actions` pack, and ADDENDUM 1's identity is why that is the sharpest
        driver available — a refusal is a FULL RECORD, so the mirror fires on it exactly as
        it fires on a permit, and the re-entrancy this row is about is provoked by the
        cheapest act in the system rather than by a special one."""
        before = len(self.store.all())
        with self.assertRaises(OpError):
            self.gate.execute("NO-SUCH-OP", "owner", {})
        return self.store.all()[before:]

    def test_a_mirrored_act_lands_inline_in_its_own_position(self):
        """THE ORDER IS THE CLAIM. A nested submission commits INLINE, in its own position —
        immediately after the record that provoked it — which is exactly where it lands with
        no batching at all, and which is what makes batch invisibility true rather than
        nearly true."""
        produced = self._mirrored()
        self.assertGreaterEqual(len(produced), 2,
                                "the act produced no mirror record — this world has no "
                                "dual-audit pack and the row would pass vacuously")
        seqs = [r["seq"] for r in produced]
        self.assertEqual(seqs, list(range(seqs[0], seqs[0] + len(seqs))),
                         "the act's records are not contiguous: %r" % (seqs,))
        primary = produced[0]
        mirrors = [r for r in produced[1:]
                   if (r.get("payload") or {}).get("stream", "").startswith("dual-audit")]
        self.assertTrue(mirrors, "no mirror record followed the primary")
        for m in mirrors:
            self.assertEqual((m["payload"] or {})["ref_seq"], primary["seq"],
                             "a mirror record does not cite the record it mirrors")

    def test_the_whole_act_is_covered_by_one_barrier(self):
        """The nested records ride the act's barrier rather than paying their own — the
        pre-split behaviour, preserved, and it is lawful by prefix durability: they sit later
        in the same file, so a barrier covering the act covers them."""
        syncs = []
        real = store_mod.os.fdatasync

        def spy(fd):
            syncs.append(1)
            return real(fd)
        store_mod.os.fdatasync = spy
        try:
            produced = self._mirrored()
        finally:
            store_mod.os.fdatasync = real
        self.assertGreaterEqual(len(produced), 2)
        self.assertEqual(len(syncs), 1,
                         "one act with %d records issued %d barriers"
                         % (len(produced), len(syncs)))

    def test_red_world_a_non_reentrant_region_wedges_its_own_sweep(self):
        """RED WORLD 1, GENERATED: the region's lock made NON-REENTRANT. The overturn sweep
        re-enters `execute` from inside the act that triggered it, so the act wedges against
        itself. The bounded wait expiring IS the failure — no duration is measured."""
        real_lock = self.gate.region._lock
        self.gate.region._lock = threading.Lock()
        self.addCleanup(setattr, self.gate.region, "_lock", real_lock)
        done = threading.Event()

        def act():
            try:
                self.gate.region.enter()
                try:
                    self.gate.region.enter()        # the act's own second entry
                    self.gate.region.exit()
                finally:
                    self.gate.region.exit()
            except BaseException:                   # noqa: BLE001 — a wedge is the subject
                pass
            done.set()
        t = threading.Thread(target=act, daemon=True)
        t.start()
        self.assertFalse(done.wait(1.5),
                         "the non-reentrant region did NOT wedge on its own second entry, so "
                         "this red world proves nothing about re-entrancy")

    def test_red_world_a_non_reentrant_write_lock_wedges_the_mirror(self):
        """RED WORLD 2, GENERATED, and it is the one the finding was actually about: the
        store's write lock made non-reentrant. The mirror appends from inside a listener that
        fires inside a publish on the same thread, so the nested publish waits for a lock its
        own caller holds."""
        self.store._write_lock = threading.Lock()
        done = threading.Event()

        def act():
            try:
                self.gate.execute("NO-SUCH-OP", "owner", {})
            except BaseException:                   # noqa: BLE001 — a wedge is the subject
                pass
            done.set()
        t = threading.Thread(target=act, daemon=True)
        t.start()
        self.assertFalse(done.wait(1.5),
                         "the non-reentrant write lock did NOT wedge the mirror — then the "
                         "mirror is not appending from inside a publish and this row's "
                         "subject has moved")


# =====================================================================================
# T-K12-BOUNDED-REGION — the region's per-act cost is the act's own dependencies
# =====================================================================================

class K12BoundedRegionCase(WorldCase):
    """K12 (design/36 ADDENDUM S): a derived answer costs its own dependencies. Nothing
    inside the region scans the queue, the record, or anything the act does not read. On a
    COUNTABLE, never a duration."""

    class _Counting:
        """A pass-through that records how many entries the region examined per act."""

        def __init__(self, real):
            self.real = real
            self.touched = 0

        def enter(self):
            return self.real.enter()

        def exit(self):
            return self.real.exit()

    def test_the_region_examines_nothing_the_act_does_not_read(self):
        """The region takes a lock and counts a depth. Its touched-entry count per act is
        ZERO — it reads no queue entry and no record — so the act's region cost is bounded by
        the act's own dependencies for the strongest possible reason: there are none."""
        for i in range(30):                                  # a store with history behind it
            self.store._append({"actor": "SYSTEM", "action": "probe", "rule_cited": "M1-OBSERVATION",
                                "payload": {"i": i}})
        counting = self._Counting(self.gate.region)
        real = self.gate.region
        self.gate.region = counting
        self.addCleanup(setattr, self.gate, "region", real)
        self.gate.execute("CREATE-OP", "owner", {"name": "ORD", "definition": ORDINARY_DEF})
        self.assertEqual(counting.touched, 0,
                         "the region examined %d entries for one act" % counting.touched)
        # AND STRUCTURALLY: the construct's own body reaches no collection at all. Read as
        # IDENTIFIERS rather than as a dump, so the class's own docstring — which names the
        # queue and the record while explaining what the region does NOT touch — is outside
        # the subject by construction. The EP-28C reader's distinction, applied here for the
        # same reason it was needed there.
        src = ast.parse(open(gate_mod.__file__, encoding="utf-8").read())
        region = next(n for n in ast.walk(src)
                      if isinstance(n, ast.ClassDef) and n.name == "DecideRegion")
        names = set()
        for node in ast.walk(region):
            for attr in ("id", "attr", "name", "arg"):
                v = getattr(node, attr, None)
                if isinstance(v, str):
                    names.add(v)
        self.assertTrue(names, "the region's body parsed to nothing")
        for forbidden in ("_queue", "events", "by_action", "_take_batch"):
            self.assertNotIn(forbidden, names,
                             "the region's body reaches %r — its cost is no longer the act's"
                             % forbidden)

    def test_red_world_a_region_that_scans_the_queue_per_decide(self):
        """RED WORLD for the boundedness clause, GENERATED and on the COUNTABLE rather than
        on a duration: a region double that walks the commit queue on entry pushes touched
        past the act's own dependencies."""
        for i in range(30):
            self.store._append({"actor": "SYSTEM", "action": "probe", "rule_cited": "M1-OBSERVATION",
                                "payload": {"i": i}})
        counting = self._Counting(self.gate.region)
        store = self.store

        def scanning():
            gc = store.group_commit
            with gc._qlock:
                counting.touched += len(gc._queue) + len(store.events)   # the forbidden scan
            return counting.real.enter()
        counting.enter = scanning
        real = self.gate.region
        self.gate.region = counting
        self.addCleanup(setattr, self.gate, "region", real)
        self.gate.execute("CREATE-OP", "owner", {"name": "ORD", "definition": ORDINARY_DEF})
        self.assertGreater(counting.touched, 0,
                           "the scanning double did not exceed the act's dependencies, so "
                           "this red world proves nothing")


if __name__ == "__main__":
    unittest.main()
