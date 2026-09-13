# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28C W1 — the appender loop and the submission queue, as the battery named before code.

MANY SUBMITTERS, ONE APPENDER. The store keeps exactly one appender; the channel and the
suite may put many submitters in flight. Nothing here batches a RECORD — every record is
appended individually and keeps its own attribution — and the only thing shared across a
batch is the `fdatasync` that covers it.

The rows in this file, and the clause each one falsifies:

  T-BATCH-CLOSES-ON-EMPTY      invariant 2's immediate-close clause: a lone submitter waits
                               for no window. RED: hold the window open and its latency
                               visibly degrades while the record still syncs and still
                               replies, so the reply/sync clauses stay green.
  T-QUEUE-EMPTY-OR-TIMEOUT     invariant 2's two closes, each independently falsifiable.
                               RED 1: the queue-empty close disabled — a drained queue waits
                               the full window. RED 2: the timeout disabled — a held batch
                               never closes.
  T-RECORDS-APPEND-INDIVIDUALLY  invariant 3: N submitters produce N records with N
                               attributions, never one. RED: a double that concatenates two
                               queued records into one append fails the count reconciliation
                               while sync and reply still pass.
  T-ONE-APPENDER               every append issues from ONE loop; no ordering-key machinery.
                               RED 1: a second append site bypassing the queue. RED 2: a
                               decoy ordering-key artifact in the diff.
  T-K12-BOUNDED                per-batch work bounded by the batch's own members, asserted
                               on a COUNTABLE. RED: a drain that scans the whole queue or an
                               index per batch pushes the touched-entry count past
                               membership.
  T-DECIDE-READS-THE-APPENDED-RECORD
                               EP-28 ADDENDUM 10.7 item 1, which that verdict directed onto
                               THIS EP as an acceptance row: the gate decides from views
                               folded over the record, so if a fold read from DISK the batch
                               window would leave act N blind to act N−1. The row is built
                               here and the authoring's omission of it is RAISED.
  T-DURABLE-TIME-IS-NOT-RECORDING-TIME
                               ADDENDUM 10.7 item 3, same provenance: a batch shares a
                               durability moment and never a recording position.

WHY THERE IS NO LATENCY ASSERTION EXCEPT AS A RED WORLD. A duration is a fact about the box.
The one place a duration appears below is a red world, where the assertion is that a
deliberately broken close condition makes a lone submitter wait ROUGHLY A WINDOW — a
comparison against a value this test itself set, not against a wall clock the box owns.
"""

import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import commit as commit_mod                          # noqa: E402
from kernel import store as store_mod                            # noqa: E402
from kernel.compose import build_full_kernel                     # noqa: E402


class StoreCase(unittest.TestCase):
    """A bare store, which is the subject of W1. The founded world appears where a row needs
    the gate; the queue itself is a property of the store and is tested there."""

    #: THE WIDTH THESE ROWS ARE ABOUT, DECLARED RATHER THAN INHERITED.
    #:
    #: The suite is run twice — once at the shipped width and once with `GOVOS_COMMIT_WIDTH=1`
    #: — and identical results are required. A row whose SUBJECT is how a batch closes cannot
    #: inherit that override, because at width 1 every batch closes on the width before any
    #: close condition is consulted and the row would be asserting the override rather than
    #: the mechanism. FOUND BY RUNNING BOTH WIDTHS, which is exactly what W6's both-widths
    #: clause exists to find, and it found it in this file first.
    #:
    #: The override's own plumbing is asserted separately, in `CalibrationCase`.
    BATCHING_WIDTH = 16

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28c-w1-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store = store_mod.EventStore(self.rec)
        self.store.group_commit.width = self.BATCHING_WIDTH
        self.addCleanup(self.store.close)
        self.addCleanup(shutil.rmtree, self.dir, True)

    def draft(self, i=0, actor="SYSTEM"):
        return {"actor": actor, "action": "probe", "rule_cited": "M1-OBSERVATION",
                "payload": {"i": i}}

    def submit_many(self, n, expect_errors=False):
        """n concurrent submitters, each blocking on its own reply. Returns the records in
        submission-thread order; every one of them is what THAT thread's call returned.

        `expect_errors` is for red worlds only: a world built to break an invariant will
        often break a second one too, and a helper that hides that is a helper that decides
        what the red world proved."""
        out = [None] * n
        self.errors = [None] * n
        gate = threading.Barrier(n)

        def one(i):
            try:
                gate.wait(timeout=30)
                out[i] = self.store._append(self.draft(i, actor="submitter-%d" % i))
            except BaseException as exc:      # noqa: BLE001 — reported, never swallowed
                self.errors[i] = exc
        threads = [threading.Thread(target=one, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        for t in threads:
            self.assertFalse(t.is_alive(), "a submitter never returned — the queue wedged")
        if not expect_errors:
            self.assertEqual([e for e in self.errors if e is not None], [])
        return out


# =====================================================================================
# T-BATCH-CLOSES-ON-EMPTY — invariant 2's immediate-close clause, and its red world
# =====================================================================================

class BatchClosesOnEmptyCase(StoreCase):

    def test_a_lone_submitter_closes_its_batch_immediately(self):
        """THE SINGLE-CALLER CASE PAYS NOTHING FOR THE MACHINERY. A batch of one closes the
        moment the queue is empty, so the estate's ordinary one-caller path never waits for a
        window that cannot fill. Asserted on the store's own close-reason COUNTABLE rather
        than on a stopwatch: `closed_on_empty` moved and `closed_on_timeout` did not."""
        gc = self.store.group_commit
        before_empty = gc.closed_on_empty
        before_timeout = gc.closed_on_timeout
        self.store._append(self.draft())
        self.assertEqual(gc.closed_on_empty, before_empty + 1)
        self.assertEqual(gc.closed_on_timeout, before_timeout,
                         "a lone submitter waited for the window — invariant 2's "
                         "immediate-close clause is not honoured")

    def test_red_world_holding_the_window_open_degrades_the_lone_submitter(self):
        """RED WORLD for the immediate-close clause, and UNREACHABLE BY THE REPLY AND SYNC
        CLAUSES: with the window held open the record still syncs and the reply still
        arrives, so nothing about durability moves. What moves is the latency, and the
        comparison is against the window THIS TEST set — never against the box."""
        gc = self.store.group_commit
        gc.window_s = 0.25
        gc.hold_open = threading.Event()          # never set: the window runs to its end
        t0 = time.monotonic()
        rec = self.store._append(self.draft())
        waited = time.monotonic() - t0
        self.assertGreaterEqual(waited, 0.2,
                                "the held window did not degrade the lone submitter, so this "
                                "red world proves nothing")
        self.assertEqual(gc.closed_on_empty, 0, "the queue-empty close fired anyway")
        self.assertEqual(gc.closed_on_timeout, 1)
        # THE OTHER CLAUSES ARE STILL GREEN IN THIS WORLD — the point of the red world.
        self.assertEqual(rec["seq"], len(self.store.all()))
        self.assertEqual(rec["payload"]["i"], 0)


# =====================================================================================
# T-QUEUE-EMPTY-OR-TIMEOUT — invariant 2's two clauses, independently falsifiable
# =====================================================================================

class QueueEmptyOrTimeoutCase(StoreCase):

    def test_a_drained_queue_never_holds_a_batch_open_awaiting_the_window(self):
        """CLAUSE ONE. The queue is empty at drain time, so the batch closes then, whatever
        the window says. The window is set LONG here on purpose: if the drained queue waited
        for it, this row would take a quarter of a second and the close reason would say
        `timeout`."""
        self.store.group_commit.window_s = 10.0
        t0 = time.monotonic()
        self.store._append(self.draft())
        self.assertLess(time.monotonic() - t0, 5.0)
        self.assertEqual(self.store.group_commit.closed_on_empty, 1)
        self.assertEqual(self.store.group_commit.closed_on_timeout, 0)

    def test_a_full_window_never_waits_past_the_timeout(self):
        """CLAUSE TWO. With the queue held non-empty by the test override, the batch closes
        on the WINDOW rather than running forever. The clause is asserted on the close
        reason, which is the whole of it.

        THE DURATION BOUND IS DELETED AND NOTHING REPLACES IT [DOCUMENTED FLIP, MAINT-1,
        2026-08-20, serving BUILD-PROMPT-STANDARD's §1 extension — a property test asserts a
        COUNTABLE, never a duration — and ruled at board :1064 and :1086 after the filing at
        :941]. WHAT STOOD HERE: `assertLess(waited, 5.0, "the timeout close did not bound
        the batch")`, fed by a `t0`/`waited` pair whose only consumer it was. WHY IT WAS
        WRONG: it was a wall-clock bound, defective in both directions at once — red on a
        loaded box while the property held, and green on a real regression — because the
        tolerance a timing bound needs to survive machine noise is wider than the signal it
        exists to catch. WHAT CARRIES THE CLAIM NOW: the line below, unchanged and
        untouched. `assertEqual(gc.closed_on_timeout, 1)` IS the property — the batch closed
        on the timeout or it did not, and that is an integer, not a stopwatch. The countable
        was already sitting one line away, which is why this row's cure is DELETION and not
        substitution; a substitute assertion added here would be a loosened guard wearing a
        repair's clothes, and the 5-second bound was only ever a proxy for a close this row
        already reads directly. No claim is removed with it."""
        gc = self.store.group_commit
        gc.window_s = 0.15
        gc.hold_open = threading.Event()
        self.store._append(self.draft())
        self.assertEqual(gc.closed_on_timeout, 1)

    def test_red_world_one_the_queue_empty_close_disabled(self):
        """RED WORLD for clause one, NAMED: with `closes_on_empty` disabled a drained queue
        waits the full window. It is unreachable by clause two, which still closes the batch
        — that is exactly what makes the two clauses separate rows."""
        gc = self.store.group_commit
        gc.window_s = 0.2
        gc.closes_on_empty = False
        t0 = time.monotonic()
        self.store._append(self.draft())
        self.assertGreaterEqual(time.monotonic() - t0, 0.15)
        self.assertEqual(gc.closed_on_empty, 0)
        self.assertEqual(gc.closed_on_timeout, 1)

    def test_red_world_two_the_timeout_disabled_never_closes_a_held_batch(self):
        """RED WORLD for clause two, NAMED: with the timeout removed a held batch never
        closes. Driven in a thread with a bounded join, because the whole point of the red
        world is that the operation does NOT return — asserting that by hanging the suite
        would be the finding destroying its own evidence."""
        gc = self.store.group_commit
        gc.closes_on_timeout = False
        gc.hold_open = threading.Event()
        done = threading.Event()

        def one():
            try:
                self.store._append(self.draft())
            finally:
                done.set()
        t = threading.Thread(target=one, daemon=True)
        t.start()
        self.assertFalse(done.wait(0.5),
                         "the batch closed with both closes disabled — this red world "
                         "proves nothing about the timeout clause")
        gc.hold_open.set()                 # let the world back out so nothing leaks
        gc.closes_on_timeout = True
        self.assertTrue(done.wait(10), "the released batch never completed")


# =====================================================================================
# T-RECORDS-APPEND-INDIVIDUALLY — invariant 3, and its red world
# =====================================================================================

class RecordsAppendIndividuallyCase(StoreCase):

    def test_n_submitters_produce_n_records_with_n_attributions(self):
        """INVARIANT 3, ON THE ARITHMETIC. Eight concurrent submitters, eight records, eight
        distinct actors, eight consecutive seq values with no gap and no duplicate — the
        count reconciliation carried ACROSS the batch boundary rather than inside one act."""
        n = 8
        before = len(self.store.all())
        recs = self.submit_many(n)
        after = self.store.all()
        self.assertEqual(len(after) - before, n)
        self.assertEqual(sorted(r["seq"] for r in recs),
                         list(range(before + 1, before + n + 1)))
        self.assertEqual(sorted(r["actor"] for r in recs),
                         sorted("submitter-%d" % i for i in range(n)))
        self.assertEqual(len({r["actor"] for r in after[before:]}), n,
                         "attribution was merged across the batch — records were coalesced")
        # AND THE FILE AGREES, which is what makes this a record claim rather than a memory one.
        with open(self.rec, encoding="utf-8") as fh:
            self.assertEqual(sum(1 for line in fh if line.strip()), before + n)

    def test_a_batch_of_eight_really_formed(self):
        """THE ROW ABOVE WOULD ALSO PASS IF THE EIGHT SUBMITTERS HAD BEEN SERIALISED one per
        batch, so the batching itself is asserted here: one batch really carried eight
        members and still produced eight records.

        The batch is formed by the WINDOW rather than by luck, deliberately. Whether a batch
        forms naturally depends on how fast this box's `fdatasync` is, and a test whose
        subject is the box is a test that says nothing about the build. What batching does to
        real concurrent traffic is a MEASUREMENT and it is taken in W7, on a stated
        substrate, where a figure about the box belongs."""
        gc = self.store.group_commit
        gc.closes_on_empty = False              # accumulate for the window
        gc.window_s = 0.25
        before = len(self.store.all())
        recs = self.submit_many(8)
        self.assertEqual(gc.largest_batch, 8,
                         "the window did not gather eight submitters into one batch, so "
                         "invariant 3 was proven on a world where batching never happened")
        self.assertEqual(len(self.store.all()) - before, 8)
        self.assertEqual(len({r["seq"] for r in recs}), 8)

    def test_red_world_a_double_that_concatenates_two_queued_records(self):
        """RED WORLD for the no-coalescing clause, NAMED. The double gives N callers ONE
        record. The count reconciliation fails; the sync and reply clauses do not — the
        caller is still answered and the barrier still runs, which is precisely why
        coalescing needs its own row rather than riding on invariant 1.

        RE-AIMED TO THE PUBLISH SITE [DOCUMENTED FLIP, EP-28G, 2026-08-03, mapped to the
        publish/await split, and PREDICTED by EP-28G's stopped session before any code].
        The double used to fire on `len(batch) > 1` inside `_commit_batch`. After the split
        `_commit_batch` receives no drafts at all — every member is already published and
        what a batch shares is only its barrier — so that double is structurally a singleton
        and could never exhibit the world invariant 3 forbids. The forbidden world did not
        move: it is still N callers and one record, and it is now built where records are
        made. What this makes harder to write is a coalescence, which is the point."""
        before = len(self.store.all())
        real = self.store._publish_one
        state = {"first": None}
        guard = threading.Lock()

        def coalescing(sub):
            with guard:
                if state["first"] is None:
                    real(sub)
                    state["first"] = sub
                else:
                    first = state["first"]      # N callers, ONE record: the forbidden world
                    sub.record = first.record
                    sub.echo = first.echo
            return sub
        self.store._publish_one = coalescing
        gc = self.store.group_commit
        gc._publish_one = coalescing
        self.addCleanup(setattr, gc, "_publish_one", real)
        self.addCleanup(setattr, self.store, "_publish_one", real)
        gc.closes_on_empty = False              # make the batch form, so the barrier is shared
        gc.window_s = 0.25
        self.submit_many(8, expect_errors=True)
        appended = len(self.store.all()) - before
        self.assertLess(appended, 8,
                        "the coalescing double appended eight records anyway, so it does not "
                        "exhibit the world invariant 3 forbids")
        # THE SYNC AND REPLY CLAUSES ARE STILL GREEN IN THIS WORLD — every submitter was
        # answered and the barrier ran, which is why coalescing needs its own row rather than
        # riding on invariant 1.
        self.assertEqual(len(self.store.all()), before + appended)
        # AND A SECOND GUARD FIRES ON THE SAME WORLD, WHICH IS WORTH RECORDING RATHER THAN
        # HIDING: the echo-retire check (W2) independently catches coalescing, because a
        # merged record disagrees with every draft but the first on fields those drafts
        # stated. Two independent detectors for one forbidden world is the design working,
        # not a duplicated test.
        import kernel.store as _s
        mismatches = [e for e in self.errors if isinstance(e, _s.EchoMismatch)]
        self.assertGreater(len(mismatches), 0,
                           "the echo did not notice a merged record — a mutated append would "
                           "have silently satisfied an intent")


# =====================================================================================
# T-ONE-APPENDER — one loop, and no sequencer arriving early
# =====================================================================================

class OneAppenderCase(StoreCase):

    def test_every_append_issues_from_one_loop(self):
        """THE STRUCTURAL GUARD. Exactly one site in `store.py` writes to the record file, one
        site issues the barrier, and one site opens the descriptor. Read out of the source
        rather than asserted, because a second write site added later is exactly the change
        this row exists to catch."""
        with open(store_mod.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("self._fh.write("), 1,
                         "the record file is written from more than one site")
        self.assertEqual(src.count("os.fdatasync("), 1,
                         "the barrier is issued from more than one site")
        self.assertEqual(src.count('self.file_path.open("a"'), 1,
                         "the record file is opened for append from more than one site")

    def test_the_record_file_is_opened_once_and_held(self):
        """THE HELD DESCRIPTOR, BEHAVIOURALLY (W3's carried-in item). Twenty appends, one
        open. This is the positive statement of the property whose two documented pins flip
        in this EP, and the flip is the evidence."""
        opens = []
        real = store_mod.Path.open

        def spy(self_path, *a, **k):
            if str(self_path).endswith("rec.jsonl"):
                opens.append(a[0] if a else k.get("mode"))
            return real(self_path, *a, **k)
        store_mod.Path.open = spy
        try:
            for i in range(20):
                self.store._append(self.draft(i))
        finally:
            store_mod.Path.open = real
        self.assertEqual(opens, ["a"],
                         "the record file was opened %d times for twenty appends — the "
                         "descriptor is not held" % len(opens))

    def test_the_appender_role_is_held_by_one_thread_at_a_time(self):
        """Sixteen concurrent submitters and the drain is never re-entered concurrently. The
        countable is the maximum observed concurrency of the drain, which a lock either holds
        at one or does not hold at all."""
        gc = self.store.group_commit
        seen = []
        live = {"n": 0}
        guard = threading.Lock()
        real = gc._commit

        def watched(batch):
            with guard:
                live["n"] += 1
                seen.append(live["n"])
            try:
                return real(batch)
            finally:
                with guard:
                    live["n"] -= 1
        gc._commit = watched
        self.addCleanup(setattr, gc, "_commit", real)
        self.submit_many(16)
        self.assertEqual(max(seen), 1,
                         "two threads were inside the appender at once — there is more than "
                         "one appender")

    def test_red_world_a_second_append_site_bypassing_the_queue(self):
        """RED WORLD, GENERATED not inherited: a source carrying a second write site, around
        the queue. The guard above reads the source, so the red world is exhibited on a COPY
        of the source rather than by editing the shipped file — and the SAME assertion is run
        against it, so what is proven is that this guard can fail rather than that some other
        guard could."""
        with open(store_mod.__file__, encoding="utf-8") as fh:
            src = fh.read()
        forged = src.replace("self._fh.write(json.dumps(",
                             "self._fh.write('')\n        self._fh.write(json.dumps(", 1)
        self.assertNotEqual(forged, src, "the red world could not be constructed")
        with self.assertRaises(AssertionError):
            self.assertEqual(forged.count("self._fh.write("), 1,
                             "the record file is written from more than one site")

    @staticmethod
    def _identifiers(path):
        """Every identifier and every attribute name in a module's EXECUTABLE BODY.

        Read through `ast` rather than as text, so that comments and docstrings are outside
        the subject by construction. That distinction is load-bearing here: `store.py`'s own
        docstring has named S5's ordering key as DEFERRED since campaign 1, and a grep over
        the text would read the sentence saying the machinery is absent as the machinery
        being present."""
        import ast
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            for attr in ("id", "attr", "name", "arg"):
                v = getattr(node, attr, None)
                if isinstance(v, str):
                    names.add(v.lower())
            if isinstance(node, ast.keyword) and node.arg:
                names.add(node.arg.lower())
        return names

    def test_no_ordering_key_machinery_entered_with_the_queue(self):
        """THE THIRD NAMED WRONG REFERENCE, as a structural guard. S5's sequencer — ordering
        keys, arbitration, an intake pipeline — is federation's and stays there. One appender
        mints `seq` exactly as it did before, so nothing on this path needs a key."""
        forbidden = ("ordering_key", "order_key", "time_hash", "arbitrate", "arbitration",
                     "sequencer", "tiebreak", "tie_break")
        for path in (commit_mod.__file__, store_mod.__file__):
            names = self._identifiers(path)
            for token in forbidden:
                self.assertNotIn(token, names,
                                 "%s defines or reads %r — the S5 sequencer arrived early"
                                 % (os.path.basename(path), token))

    def test_red_world_a_decoy_ordering_key_artifact(self):
        """RED WORLD for the guard above, GENERATED: a module that really does carry a key,
        run through the same reader and the same assertion. A guard whose failing case was
        never exhibited is a guard nobody has seen fail — and this one is written against a
        DECOY IN CODE rather than in a comment, which is the distinction the reader makes."""
        import tempfile as _tf
        decoy = os.path.join(self.dir, "decoy_sequencer.py")
        with open(decoy, "w", encoding="utf-8") as fh:
            fh.write("def mint(bucket, built_id, submission_time):\n"
                     "    ordering_key = (bucket, built_id, submission_time)\n"
                     "    return ordering_key\n")
        names = self._identifiers(decoy)
        with self.assertRaises(AssertionError):
            self.assertNotIn("ordering_key", names, "the S5 sequencer arrived early")
        # AND THE COMPLEMENT, which is what makes the reader's choice checkable: the same
        # token in a COMMENT is not the machinery and must not red.
        commented = os.path.join(self.dir, "decoy_comment.py")
        with open(commented, "w", encoding="utf-8") as fh:
            fh.write("# the ordering_key (bucket, built_id, submission_time) is DEFERRED\n"
                     "def mint():\n    return None\n")
        self.assertNotIn("ordering_key", self._identifiers(commented))
        del _tf


# =====================================================================================
# T-K12-BOUNDED — the batch's work is its own members, on a countable
# =====================================================================================

class K12BoundedCase(StoreCase):

    def test_per_batch_work_is_bounded_by_the_batch_members(self):
        """K12 (design/36 ADDENDUM S): a derived answer costs its own dependencies. The
        appender's per-batch work is bounded by what the batch CONTAINS — it never walks the
        queue it did not take, and never walks the record. Asserted on touched entries, which
        is a countable, and NOT on a duration."""
        self.store._append(self.draft())              # a store with history behind it
        for i in range(40):
            self.store._append(self.draft(i))
        gc = self.store.group_commit
        gc.touched = 0
        gc.batches = 0
        gc.members = 0
        recs = self.submit_many(8)
        self.assertEqual(len(recs), 8)
        self.assertEqual(gc.touched, gc.members,
                         "the drain touched %d entries for %d batch members — its cost is "
                         "not bounded by what the batch contains" % (gc.touched, gc.members))
        self.assertEqual(gc.members, 8)

    def test_red_world_a_drain_that_scans_the_whole_record(self):
        """RED WORLD for the boundedness clause, NAMED, and on the COUNTABLE rather than on a
        duration: a drain that walks the record per batch pushes touched past membership."""
        for i in range(30):
            self.store._append(self.draft(i))
        gc = self.store.group_commit
        real = gc._commit

        def scanning(batch):
            gc.touched += len(self.store.events)      # the scan the invariant forbids
            return real(batch)
        gc._commit = scanning
        self.addCleanup(setattr, gc, "_commit", real)
        gc.touched = 0
        gc.members = 0
        self.store._append(self.draft())
        self.assertGreater(gc.touched, gc.members,
                           "the scanning double did not exceed membership, so this red world "
                           "proves nothing")


# =====================================================================================
# T-DECIDE-READS-THE-APPENDED-RECORD — EP-28 ADDENDUM 10.7 item 1, directed onto this EP
# =====================================================================================

class DecideReadsAppendedCase(unittest.TestCase):
    """EP-28's verdict directed this as an acceptance row on the group-commit EP and the
    authoring did not carry one. It is built here and the omission is RAISED. The property:
    the gate decides from views folded over the record, so a fold reading from DISK would
    leave act N blind to act N−1 for the whole batch window."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28c-w1-decide-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.rec, os.path.join(self.dir, "blobs"))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_no_fold_source_reads_the_record_file(self):
        """The structural half: no fold reads the file. Every read path resolves through the
        store's in-memory record, which the appender publishes. Read out of the source of the
        three files that hold the fold read paths."""
        import kernel.views as views_mod
        import kernel.authority as authority_mod
        for mod in (views_mod, authority_mod):
            with open(mod.__file__, encoding="utf-8") as fh:
                src = fh.read()
            self.assertNotIn("file_path", src,
                             "%s names the record file — a fold reading from disk is blind "
                             "to the batch window" % os.path.basename(mod.__file__))
            self.assertNotIn("json.loads", src)

    def test_a_record_is_visible_to_the_folds_before_its_batch_syncs(self):
        """THE BEHAVIOURAL HALF, and it is the one that settles it. A record enters the
        store's in-memory record — the thing every fold reads — BEFORE the covering sync, so
        there is no window in which an appended record is invisible to the decide path. The
        probe watches from inside the barrier."""
        seen = {}
        real = os.fdatasync

        def watching(fd):
            seen["visible"] = [e["action"] for e in self.store.all()][-1:]
            return real(fd)
        store_mod.os.fdatasync = watching
        try:
            self.store._append({"actor": "SYSTEM", "action": "late-probe",
                                "rule_cited": "M1-OBSERVATION"})
        finally:
            store_mod.os.fdatasync = real
        self.assertEqual(seen["visible"], ["late-probe"],
                         "the record was not visible to the folds at the moment its batch "
                         "synced — the decide path can be blind for a whole window")


# =====================================================================================
# T-DURABLE-TIME-IS-NOT-RECORDING-TIME — EP-28 ADDENDUM 10.7 item 3
# =====================================================================================

class DurableTimeCase(StoreCase):

    def test_a_batch_shares_a_durability_moment_and_never_a_recording_position(self):
        """ADDENDUM 10.7 item 3, made a test rather than a sentence. `record_time` carries
        ORDER and comes from the append, which stays per-record; a batch shares only the
        moment its records became durable. So the records of one batch have DISTINCT
        recording positions, and nothing anywhere records a shared durability stamp."""
        recs = self.submit_many(8)
        self.assertEqual(len({r["seq"] for r in recs}), 8)
        for r in recs:
            for key in r.keys():
                self.assertNotIn("durab", key.lower())
                self.assertNotIn("batch", key.lower())


# =====================================================================================
# THE CALIBRATION AND ITS DECLARED TEST OVERRIDE
# =====================================================================================

class CalibrationCase(unittest.TestCase):
    """The width cap and the window are ENGINE CALIBRATION, not law-data. They change no
    verdict, no citation, no record content and no order — only the latency shape — which is
    the contrast with EP-27's delivery lanes, which ordered LAW delivery and were rightly
    recorded policy. So they are named constants with a declared override, and the override's
    invocation form is what a verifier runs verbatim:

        GOVOS_COMMIT_WIDTH=1   python3 -m unittest discover -s tests -p 'test_*.py'
        GOVOS_COMMIT_WINDOW_MS=<float>
    """

    def test_the_shipped_values_are_named_constants(self):
        self.assertEqual(commit_mod.BATCH_WIDTH_CAP, 16)
        self.assertEqual(commit_mod.BATCH_WINDOW_S, 0.002)

    def test_the_override_is_read_from_the_declared_environment_variables(self):
        old = dict(os.environ)
        try:
            os.environ["GOVOS_COMMIT_WIDTH"] = "1"
            os.environ["GOVOS_COMMIT_WINDOW_MS"] = "7.5"
            width, window = commit_mod._calibration()
            self.assertEqual(width, 1)
            self.assertAlmostEqual(window, 0.0075)
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_an_unreadable_override_refuses_rather_than_falling_back(self):
        """ST-A at the one place a silent fall-back would be worst: a run that believed it was
        at width 1 and was not would report the shipped width's result under the override's
        name. That is the flattering wrong answer this estate keeps catching in other
        clothes, so the override REFUSES."""
        old = dict(os.environ)
        try:
            for bad in ("nonsense", "0", "-3"):
                os.environ["GOVOS_COMMIT_WIDTH"] = bad
                with self.assertRaises(ValueError):
                    commit_mod._calibration()
            os.environ.pop("GOVOS_COMMIT_WIDTH")
            os.environ["GOVOS_COMMIT_WINDOW_MS"] = "later"
            with self.assertRaises(ValueError):
                commit_mod._calibration()
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_the_calibration_carries_no_governance_content(self):
        """The derivation stated as a check: nothing in the commit module reads or writes a
        rule, a grant, an actor, a verdict or a citation. A calibration that could reach any
        of those would be recorded policy and would belong in the founding, not in a
        constant."""
        import ast
        with open(commit_mod.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            for attr in ("id", "attr", "name", "arg"):
                v = getattr(node, attr, None)
                if isinstance(v, str):
                    names.add(v.lower())
        for governance in ("rule_cited", "covers", "grant", "actor", "verdict", "authority",
                           "founding", "rule_id", "space", "refuse"):
            self.assertNotIn(governance, names,
                             "the commit loop reaches %r — a batch parameter that can touch "
                             "governance is recorded policy, not a constant" % governance)


if __name__ == "__main__":
    unittest.main()
