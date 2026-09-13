"""EP-28C W6 — T-BATCH-INVISIBLE: the record stream carries no batch artifact.

THE ROW: width-1 and shipped-width runs are content-equivalent for the same submissions,
and replay needs no knowledge that batching ever existed.

AND THE CLAUSE THAT MAKES IT MEAN ANYTHING (AMENDMENT 8.1, from close item 49): **every row
whose pass condition is an EQUALITY BETWEEN TWO DERIVED THINGS carries a NON-VACUITY clause
— both sides proven non-empty — because agreement does not imply either side exists.** This
row is the amendment's named standing member, so its non-vacuity is built FIRST and it has
THREE clauses rather than one, because this equality has two ways of being vacuous:

  1. Both record streams non-empty. The plain form: two empty streams agree perfectly.
     This is the shape that made `T-CACHE-KILL` green over a world where nothing was
     written.
  2. The SHIPPED-WIDTH arm actually formed a batch wider than one. Without it the two arms
     are two runs of the SAME configuration, and "identical at both widths" is a statement
     about one width said twice. **This is the vacuity the plain form does not reach**, and
     it is the one that belongs to THIS row rather than to the class: a comparison whose
     independent variable never varied.
  3. The WIDTH-1 arm never formed a batch wider than one, so the two arms are known to have
     differed in the variable and in nothing else the test set.

Clause 2 is why the row is worth having. An equality between two derived things can be
vacuous because a side is empty OR because the sides were never actually different, and the
second is invisible to a non-emptiness check.

WHAT "CONTENT-EQUIVALENT" MEANS HERE, STATED RATHER THAN ASSUMED. It is the multiset of
record CONTENT — actor, action, rule_cited, payload, refused — plus the structural facts
that `seq` runs 1..N with no gap and no repeat in both arms, and that neither arm's records
carry a field the other's do not. It is deliberately NOT "the two files are byte-identical":
`record_time` is a wall clock, and the ORDER in which independent concurrent submitters
reach the queue is a property of the scheduler rather than of batching. Promising an
interleaving would be promising something batching never touched, and a row that asserts
more than its subject supports is the vocabulary breach §A46 names.

THE ROUND-TRIP HALF is driven on a governed world through the real port, and it uses
DISTINCT paths per submitter. That is not decoration: two concurrent creates of ONE path is
the composition `test_ep28c_w4e.py` stops on, and driving it here would mix a finding under
raise into a row about batching. Named so the choice is visible rather than looking like a
convenience.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from bridge.custody import RENDER_FLOOR, ROOT_INO, SEQ_FLOOR       # noqa: E402
from bridge.kernel_port import KernelPort                          # noqa: E402
from bridge.mount import build_brain                               # noqa: E402
from kernel import store as store_mod                              # noqa: E402

#: The two arms. DECLARED IN THE ROW rather than inherited from the environment, for the
#: reason `test_ep28c_w1.py` records: a row whose SUBJECT is the width cannot read the
#: suite's width override, or it asserts the override instead of the mechanism. Under
#: `GOVOS_COMMIT_WIDTH=1` this file still runs both arms, which is what makes it able to
#: say anything about both widths on either run.
WIDTH_ONE = 1
WIDTH_SHIPPED = 16

#: THE WINDOW THE SHIPPED ARM ACCUMULATES OVER, so the batch forms BY THE WINDOW rather than
#: by luck — the estate's established deterministic-batching idiom (`test_ep28g_w4`
#: `concurrent_acts`, `test_ep28c_w1`). The barriers below release the submitters together;
#: this holds the batch open, with the empty-close disabled, long enough for every released
#: submitter to finish its publish work and reach the queue. Without it the default 2 ms
#: window closes the batch the instant the queue drains between two arrivals — which happens
#: whenever the submitters serialize under load — and the shipped arm reports `largest_batch
#: == 1` on a run where batching is perfectly healthy. THE BATCH REMAINS REAL: N real
#: submissions, N real records, one covering `fdatasync`; the window removes the timing luck,
#: it CANNOT manufacture a member that never arrived (`kernel/commit.py` lines 119-121). At
#: `WIDTH_ONE` the accumulate loop is never entered (`len(batch) < 1` is false at once), so a
#: width-1 arm closes every batch on the width regardless of this and `largest_batch` stays 1.
BATCH_GATHER_WINDOW_S = 0.30

#: The fields a record legitimately differs in between two runs of the SAME width.
#:
#: MEASURED, NOT CHOSEN, and that is the whole design of this row. An exclusion list picked
#: by hand is the one structure that can hide the thing under test: a batch artifact lands
#: in a field, and a comparison that ignores the wrong field reports invisibility it never
#: checked. So the list is DERIVED — `MeasuredExclusionCase` runs the same submissions
#: TWICE at width 1 and asserts that the fields which differ are exactly these. A batch
#: artifact cannot enter the set that way, because it does not differ between two runs at
#: one width; only clocks and scheduler-ordered positions do.
#:
#: The reason each member is here, so a reader can check the derivation rather than trust
#: it: three wall clocks, and two positions that follow the order independent concurrent
#: submitters happened to reach the queue in — an order batching never promised to fix.
PER_RUN_FIELDS = {
    "record_time",
    "submission_time",
    "occurrence_time",
    "seq",
    "record_id",       # `rec_<seq>`: derived from the position, so it moves with it
}


def identity_blind(snap):
    """A served snapshot with every inode number RELABELLED by the first path it is bound
    under [EP-28T, 2026-08-08].

    IT IS A RELABELLING, NEVER A FILTER. Nothing is dropped: `kind`, `perm`, `uid`, `gid`,
    `size`, `content_hash`, `xattrs`, `target`, the namespace, the directory children and the
    inode-to-paths index all survive and are all compared. The only thing replaced is the
    NUMBER, and it is replaced by a key derived from the namespace the two worlds share — so
    a difference in anything except allocation order still reds. `TestTheRelabellingCanFail`
    holds that: it perturbs one field at a time and requires each to survive the relabelling
    as a difference."""
    label = {}
    for ino, paths in snap["paths"].items():
        label[ino] = sorted(paths)[0] if paths else "<unbound:%s>" % ino

    def lab(ino):
        return label.get(str(ino), "<unlabelled:%s>" % ino)

    return {
        "names": {p: lab(i) for p, i in snap["names"].items()},
        "inodes": {lab(i): {k: v for k, v in node.items() if k != "ino"}
                   for i, node in snap["inodes"].items()},
        "kids": snap["kids"],
        "paths": {lab(i): paths for i, paths in snap["paths"].items()},
    }


def content_of(record):
    """One record reduced to what batching must not touch."""
    return json.dumps({k: v for k, v in record.items() if k not in PER_RUN_FIELDS},
                      sort_keys=True, default=str)


def differing_fields(a_records, b_records):
    """Which FIELDS differ between two record streams, compared by content rather than by
    position — the streams are ordered by whichever submitter got there first."""
    def by_actor(recs):
        return {r["actor"]: r for r in recs}
    a, b = by_actor(a_records), by_actor(b_records)
    assert set(a) == set(b), "the two streams are not about the same submitters"
    out = set()
    for actor in a:
        for k in set(a[actor]) | set(b[actor]):
            if a[actor].get(k) != b[actor].get(k):
                out.add(k)
    return out


class _Arm:
    """One store at one width, with the countables the non-vacuity clauses read."""

    def __init__(self, root, width, n):
        self.dir = tempfile.mkdtemp(prefix="w6-w%d-" % width, dir=root)
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store = store_mod.EventStore(self.rec)
        self.store.group_commit.width = width
        # Deterministic batch formation on the shipped arm (see BATCH_GATHER_WINDOW_S).
        self.store.group_commit.closes_on_empty = False
        self.store.group_commit.window_s = BATCH_GATHER_WINDOW_S
        self.width = width
        self.n = n
        self.errors = []

    def close(self):
        self.store.close()

    def drive(self):
        """N concurrent submitters released together, each blocking on its own reply.

        The barrier releases them together; the accumulation window (BATCH_GATHER_WINDOW_S,
        set in __init__) holds the shipped arm's batch open long enough to gather every one
        of them. The barrier alone is not enough — a released submitter still does its whole
        publish before it reaches the queue, so under load the submitters arrive spread out
        and, on the default 2 ms empty-close, every batch would close at one; then non-vacuity
        clause 2 would red on a run where batching is perfectly healthy. With the window the
        batch forms on EVERY run — a real batch of N, gathered by the same window mechanism
        production uses, never a manufactured count."""
        gate = threading.Barrier(self.n, timeout=30)

        def one(i):
            try:
                gate.wait()
                self.store._append({"actor": "submitter-%02d" % i, "action": "probe",
                                    "rule_cited": "M1-OBSERVATION", "payload": {"i": i}})
            except BaseException as exc:                            # noqa: BLE001
                self.errors.append(exc)
                gate.abort()

        threads = [threading.Thread(target=one, args=(i,)) for i in range(self.n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        for t in threads:
            assert not t.is_alive(), "a submitter never returned — the queue wedged"
        return self


class BatchInvisibleCase(unittest.TestCase):
    """T-BATCH-INVISIBLE over a bare store: the same submissions at two widths."""

    N = 12

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ep28c-w6-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.one = _Arm(self.root, WIDTH_ONE, self.N)
        self.shipped = _Arm(self.root, WIDTH_SHIPPED, self.N)
        self.addCleanup(self.one.close)
        self.addCleanup(self.shipped.close)
        # INTERLEAVED, not sequential: the shipped arm second would meet a warmer page
        # cache. It costs nothing here and it is the same discipline W7's measurement is
        # held to, applied to a correctness row so the two do not diverge in method.
        self.shipped.drive()
        self.one.drive()
        self.assertEqual(self.one.errors, [])
        self.assertEqual(self.shipped.errors, [])

    # ---- NON-VACUITY, FIRST -------------------------------------------------------
    def test_NON_VACUITY_1_neither_record_stream_is_empty(self):
        self.assertEqual(len(self.one.store.all()), self.N)
        self.assertEqual(len(self.shipped.store.all()), self.N)

    def test_NON_VACUITY_2_the_shipped_arm_actually_formed_a_batch_wider_than_one(self):
        """THE CLAUSE THIS ROW EXISTS FOR. Without it the equality below is an agreement
        between two runs of one configuration."""
        gc = self.shipped.store.group_commit
        self.assertGreater(gc.largest_batch, 1,
                           "the shipped-width arm never batched, so the arms did not "
                           "differ in the variable under test and the equality below "
                           "would be vacuous — it would compare width 1 against width 1")
        self.assertGreater(gc.members, 0)

    def test_NON_VACUITY_3_the_width_one_arm_never_formed_a_batch_wider_than_one(self):
        gc = self.one.store.group_commit
        self.assertEqual(gc.largest_batch, 1,
                         "the width-1 arm batched, so the override did not take and the "
                         "two arms are not the two widths they claim to be")
        self.assertEqual(gc.closed_on_width, gc.batches,
                         "at width 1 every batch closes on the width before any close "
                         "condition is consulted")

    # ---- THE EXCLUSION LIST, DERIVED ------------------------------------------------
    def test_the_excluded_fields_are_exactly_those_a_SAME_WIDTH_pair_differs_in(self):
        """THE CLAUSE THAT MAKES THE EQUALITY TRUSTWORTHY, and it is this row's own §A38.

        A hand-picked exclusion list can hide the artifact it was written to expose. This
        derives it instead: a CONTROL arm at the same width as `self.one`, driven with the
        same submissions, and the fields that differ between two runs at ONE width are by
        construction the clocks and the scheduler-ordered positions — never a batch
        artifact, which does not vary with the scheduler. If this row reds, the exclusion
        list has drifted from the envelope and every comparison below is suspect."""
        control = _Arm(self.root, WIDTH_ONE, self.N)
        self.addCleanup(control.close)
        control.drive()
        self.assertEqual(control.errors, [])
        differ = differing_fields(self.one.store.all(), control.store.all())
        self.assertTrue(differ, "two runs differed in NOTHING, which means the streams are "
                                "not being read — the derivation below would exclude "
                                "nothing and pass for the wrong reason")
        self.assertEqual(differ, PER_RUN_FIELDS,
                         "the fields that vary between two runs at one width are not the "
                         "fields this file excludes — the exclusion list is now either "
                         "hiding something or ignoring something")

    # ---- THE EQUALITY -------------------------------------------------------------
    def test_the_two_widths_differ_in_NOTHING_outside_the_derived_exclusion(self):
        """The row, stated as a set difference so a failure NAMES the field that broke it
        rather than printing two walls of JSON."""
        differ = differing_fields(self.one.store.all(), self.shipped.store.all())
        self.assertTrue(self.one.store.all() and self.shipped.store.all())
        self.assertEqual(differ - PER_RUN_FIELDS, set(),
                         "a field differs between width 1 and the shipped width that is "
                         "not a clock and not a scheduler-ordered position — that is a "
                         "batch artifact in the record stream")

    def test_the_two_widths_produce_content_equivalent_record_streams(self):
        a = sorted(content_of(r) for r in self.one.store.all())
        b = sorted(content_of(r) for r in self.shipped.store.all())
        self.assertTrue(a, "the width-1 content set is empty")
        self.assertTrue(b, "the shipped-width content set is empty")
        self.assertEqual(a, b)

    def test_neither_arm_carries_a_field_the_other_does_not(self):
        """A batch artifact would most cheaply arrive as a NEW FIELD, so the field sets are
        compared as sets in both directions — never by count. An eleven-for-eleven
        reconciliation over mismatched sets reads as reconciled (AMENDMENT 2's lesson,
        executed rather than cited)."""
        fa = {k for r in self.one.store.all() for k in r}
        fb = {k for r in self.shipped.store.all() for k in r}
        self.assertTrue(fa and fb, "a field set is empty")
        self.assertEqual(fa - fb, set(), "the width-1 arm carries a field the batched arm "
                                         "does not")
        self.assertEqual(fb - fa, set(), "the batched arm carries a field width 1 does "
                                         "not — a batch artifact in the record")

    def test_seq_runs_one_to_N_with_no_gap_and_no_repeat_in_BOTH_arms(self):
        """A batch shares a DURABILITY moment and never a RECORDING position. Asserted on
        the countable rather than on the absence of a field, so a batch that quietly gave
        several records one position would red here even if it named nothing."""
        for name, arm in (("width-1", self.one), ("shipped", self.shipped)):
            seqs = [r["seq"] for r in arm.store.all()]
            self.assertEqual(sorted(seqs), list(range(1, self.N + 1)),
                             "%s: seq is not 1..N without gaps or repeats" % name)

    # ---- THE RED WORLD ------------------------------------------------------------
    def test_RED_WORLD_a_double_that_writes_a_batch_identifier_into_a_record(self):
        """The invisibility clause made to FAIL, and unreachable by every clause that
        already passed: the double stamps a batch identifier and nothing else, so both
        streams stay non-empty, both widths still batch as they did, `seq` still runs 1..N,
        and ONLY the content equivalence reds. That is what makes this a red world for
        THIS clause rather than a general breakage."""
        stamped = _Arm(self.root, WIDTH_SHIPPED, self.N)
        self.addCleanup(stamped.close)
        real = stamped.store._commit_batch
        counter = {"n": 0}

        def stamping(batch):
            counter["n"] += 1
            out = real(batch)
            # The record is frozen by the time it is published, so the double stamps the
            # store's own in-memory copy — the cheapest route a real batch artifact could
            # take into the stream, and the one a content comparison must be able to see.
            for s in batch:
                if s.record is not None:
                    stamped.store.events[s.record["seq"] - 1] = dict(
                        s.record, batch_id=counter["n"])
            return out

        stamped.store.group_commit._commit_batch = stamping
        stamped.drive()
        self.assertEqual(stamped.errors, [])

        # The clauses that must STILL pass in this world:
        self.assertEqual(len(stamped.store.all()), self.N, "the stream emptied instead")
        self.assertEqual(sorted(r["seq"] for r in stamped.store.all()),
                         list(range(1, self.N + 1)), "seq moved instead")
        self.assertGreater(stamped.store.group_commit.largest_batch, 1,
                           "the stamped arm stopped batching instead")

        # And the one that must FAIL:
        a = sorted(content_of(r) for r in self.one.store.all())
        c = sorted(content_of(r) for r in stamped.store.all())
        self.assertNotEqual(a, c,
                            "the batch identifier did not make the streams differ — this "
                            "red world proves nothing about the invisibility clause")
        self.assertTrue(any("batch_id" in r for r in stamped.store.all()),
                        "the double did not actually stamp anything")


class ReplayKnowsNothingOfBatchingCase(unittest.TestCase):
    """The round-trip half, on a GOVERNED world through the real port.

    Replay reads the record file and nothing else. If batching left any trace the fold
    depended on, two worlds built at two widths would replay to two states."""

    N = 8

    def _world(self, width):
        d = tempfile.mkdtemp(prefix="w6-rt-w%d-" % width, dir=self.root)
        store, gate, views, blobs = build_brain(os.path.join(d, "rec.jsonl"),
                                                os.path.join(d, "blobs"))
        store.group_commit.width = width
        # Deterministic batch formation on the shipped arm (see BATCH_GATHER_WINDOW_S). The
        # round-trip half drives through the real port, so each submitter does the whole
        # gate-plus-kernel publish before it reaches the queue — the arrival spread is widest
        # here, which is why the flake surfaced in THIS case first.
        store.group_commit.closes_on_empty = False
        store.group_commit.window_s = BATCH_GATHER_WINDOW_S
        port = KernelPort(store, gate, views, blobs)
        errors = []
        gatebar = threading.Barrier(self.N, timeout=30)

        def one(i):
            try:
                gatebar.wait()
                port.handle({"id": "1", "op": "FILE-CREATE", "class": "DECISION",
                             "uid": "1000", "gid": "1000", "pid": "42",
                             "path": "/f%02d" % i, "perm": "644"}, b"")
            except BaseException as exc:                            # noqa: BLE001
                errors.append(exc)
                gatebar.abort()

        threads = [threading.Thread(target=one, args=(i,)) for i in range(self.N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        self.assertEqual(errors, [])
        return d, store, port

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ep28c-w6-rt-")
        self.addCleanup(shutil.rmtree, self.root, True)
        # Interleaved for the same reason as above: shipped first, then width 1.
        self.d_shipped, self.s_shipped, self.p_shipped = self._world(WIDTH_SHIPPED)
        self.d_one, self.s_one, self.p_one = self._world(WIDTH_ONE)
        self.addCleanup(self.s_shipped.close)
        self.addCleanup(self.s_one.close)

    def test_NON_VACUITY_the_batched_world_batched_and_both_worlds_hold_the_files(self):
        self.assertGreater(self.s_shipped.group_commit.largest_batch, 1,
                           "the shipped-width world never batched — the comparison below "
                           "would be width 1 against width 1")
        self.assertEqual(self.s_one.group_commit.largest_batch, 1)
        for name, port in (("shipped", self.p_shipped), ("width-1", self.p_one)):
            created = [p for p in ("/f%02d" % i for i in range(self.N))
                       if port.state.exists(p)]
            self.assertEqual(len(created), self.N,
                             "%s: the world does not hold the files it created, so the "
                             "state compared below is not the state under test" % name)

    def test_replaying_each_world_from_its_record_alone_gives_the_same_served_state(self):
        """The round-trip, per world: kill everything derived, rebuild from the record."""
        for name, d, port in (("shipped", self.d_shipped, self.p_shipped),
                              ("width-1", self.d_one, self.p_one)):
            s2, g2, v2, b2 = build_brain(os.path.join(d, "rec.jsonl"),
                                         os.path.join(d, "blobs"))
            self.addCleanup(s2.close)
            replayed = KernelPort(s2, g2, v2, b2).state.snapshot()
            served = port.state.snapshot()
            self.assertTrue(served, "%s: the served snapshot is empty" % name)
            self.assertTrue(replayed, "%s: the replayed snapshot is empty" % name)
            self.assertEqual(replayed, served, "%s: replay diverged" % name)

    def test_the_two_widths_replay_to_the_SAME_served_state(self):
        """The row itself: a fold reading two records written at two widths cannot tell
        which was which, because there is nothing in either to tell it with.

        =====================================================================================
        [EP-28T, 2026-08-08 — `AppendNothing`, AND THIS ROW IS WHY THE MENTOR RULED PER-ROW
        RATHER THAN A SWEEP. A row asserting a property the estate DELIBERATELY TRADED AWAY is
        OBSOLETE, NOT BROKEN, and deleting it silently would destroy the record that the trade
        was made on purpose.]

        WHAT THIS ROW ASSERTED, and it was TRUE when written (EP-28C W6, 2026-08-03): two
        worlds built at two widths replay to the SAME served state, compared field for field
        INCLUDING every inode number. It held because identity was derived from the PATH
        (founding 1.14.0's class-wide `param_defaults {"inode": "$path"}`), so `/f01` was
        `/f01` in every world no matter which of the eight barrier-released submitters reached
        the queue first.

        WHAT SUPERSEDED IT (EP-28S, founding 1.18.0, 2026-08-08): a birth act is named by its
        own position in the record — `SEQ_FLOOR + seq`. The eight submitters here are released
        at a barrier and reach the queue in whatever order the scheduler gives them, so `/f01`
        takes the position its create actually reached. TWO INDEPENDENTLY BUILT WORLDS
        DISAGREE ON THE NUMBERS BY CONSTRUCTION, not by defect.

        AND THE ROW WAS NEVER TESTING BATCHING — which is the finding, and it took thirteen
        seats. `_world()` builds a SEPARATE directory, store and record file per arm, so these
        are two independent worlds and the only thing that ever made their identity numbers
        agree was that identity was content-derived. It was testing CONTENT-DERIVED IDENTITY
        and did not know it. That is why it never fired in thirteen seats and then fired in
        three full-suite arms the moment the law landed.

        THE TRADE, STATED SO THE SURRENDER IS A DECISION ON THE RECORD RATHER THAN A SWEEP:
        **ORDER-INDEPENDENCE ACROSS WORLDS AND UNIQUENESS ACROSS ONE WORLD'S HISTORY ARE
        INCOMPATIBLE FOR A REUSABLE NAME.** The estate had the first and paid for it with the
        rename-recreate collision — two files under one node, a chmod through one name
        reaching the other. It now takes the second. This is a property of ALLOCATION-ORDER
        IDENTITY AS SUCH, not of `SEQ_FLOOR + seq`: the FUSE port's private counter had
        exactly the same order-dependence, so no counter-based successor recovers it.

        WHAT REMAINS TRUE IS SEPARATED OUT AND STILL ASSERTED, AND IT IS EVERYTHING THE ROW
        WAS WRITTEN TO GUARD. Batching still leaves no trace a fold can read: the two worlds
        serve the SAME namespace, the same directory structure, the same kinds, permissions,
        owners, sizes, content hashes, xattrs and link targets. ONLY THE NUMBERS DIFFER, and
        `identity_blind` removes exactly the numbers and nothing else. The batching claim is
        untouched; the identity claim is surrendered; and the two are now visibly separate,
        which they never were while one assertion carried both.

        WHAT IS GIVEN UP, PLAINLY: this row can no longer detect a batch artifact that lands
        ONLY in an inode number. Nothing else in the file loses anything — the record-stream
        comparison in `BatchInvisibleCase` reads the records directly, at full fidelity, and
        `test_no_word_for_a_batch_appears_anywhere_in_either_record_file` reads the raw bytes.
        =====================================================================================
        """
        a = self.p_one.state.snapshot()
        b = self.p_shipped.state.snapshot()
        self.assertTrue(a, "the width-1 state is empty")
        self.assertTrue(b, "the shipped-width state is empty")
        # NON-VACUITY FIRST (item 21), AND IT IS WHAT KEEPS THE SURRENDER HONEST: both worlds
        # must actually be under ALLOCATION-ORDER identity, or this row has quietly become the
        # old one and the relabelling is laundering nothing. Every non-root inode must sit in
        # the FORMAL-NAME band. Under path identity they would sit at or above `RENDER_FLOOR`
        # and this reds — so a silent return to content-derived identity cannot pass here.
        #
        # It is asserted on the BAND rather than on "the two worlds disagree", deliberately:
        # eight barrier-released threads CAN land in the same order twice, so a
        # they-must-differ clause would be a one-in-a-while red. A structural fact is not.
        for name, snap in (("width-1", a), ("shipped", b)):
            others = [i for i in snap["inodes"] if int(i) != ROOT_INO]
            self.assertTrue(others, "%s: the world holds no minted inodes" % name)
            for i in others:
                self.assertGreaterEqual(int(i), SEQ_FLOOR,
                                        "%s: inode %s is not an allocation-order name — this "
                                        "row's surrender does not apply and the strict "
                                        "equality it gave up should be restored" % (name, i))
                self.assertLess(int(i), RENDER_FLOOR,
                                "%s: inode %s has drifted into the digest band" % (name, i))
        self.assertEqual(identity_blind(a), identity_blind(b))

    def test_no_word_for_a_batch_appears_anywhere_in_either_record_file(self):
        """The blunt half, kept because it is cheap and it catches the artifact a content
        comparison would miss if BOTH arms grew it. Two arms that both learn the same new
        field agree with each other perfectly — the vacuity clause one level over."""
        for name, d in (("shipped", self.d_shipped), ("width-1", self.d_one)):
            with open(os.path.join(d, "rec.jsonl"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertTrue(text.strip(), "%s: the record file is empty" % name)
            for word in ("batch", "durable_at", "synced_at", "commit_id"):
                self.assertNotIn(word, text,
                                 "%s: the record names %r — a batch artifact reached the "
                                 "one place that must not know batching happened"
                                 % (name, word))


class TestTheRelabellingCanFail(unittest.TestCase):
    """THE RED WORLD FOR `identity_blind` [EP-28T, 2026-08-08].

    The row above gave up an equality on inode NUMBERS. That surrender is only honest if the
    relabelling still sees everything else — a comparison that laundered the whole snapshot
    would pass forever and the row would be a description of the code wearing a test's
    clothes. So each field is perturbed ONE AT A TIME and each must survive as a difference.

    AND IT NAMES ITS CLAUSE: the one perturbation that must NOT red is a change to the inode
    NUMBERS alone, because that is exactly and only what was traded away. Both directions, so
    the relabelling can neither over-launder nor under-launder."""

    def snap(self):
        return {
            "names": {"/": 1, "/a": 2305843009213694090, "/b": 2305843009213694091},
            "inodes": {
                "1": {"ino": 1, "kind": "dir", "perm": 0o755, "uid": 0, "gid": 0,
                      "content_hash": None, "size": 0, "xattrs": {}, "target": None},
                "2305843009213694090": {"ino": 2305843009213694090, "kind": "file",
                                        "perm": 0o644, "uid": 1000, "gid": 1000,
                                        "content_hash": "aa", "size": 3, "xattrs": {},
                                        "target": None},
                "2305843009213694091": {"ino": 2305843009213694091, "kind": "file",
                                        "perm": 0o644, "uid": 1000, "gid": 1000,
                                        "content_hash": "bb", "size": 4, "xattrs": {},
                                        "target": None},
            },
            "kids": {"/": ["a", "b"]},
            "paths": {"1": ["/"], "2305843009213694090": ["/a"],
                      "2305843009213694091": ["/b"]},
        }

    def test_NON_VACUITY_an_unperturbed_pair_compares_EQUAL(self):
        self.assertEqual(identity_blind(self.snap()), identity_blind(self.snap()))

    def test_the_ONE_thing_it_IS_meant_to_launder_is_the_NUMBERS(self):
        """The clause this row exists for: renumber both nodes, keep every other fact and the
        whole namespace, and the comparison must be BLIND to it. That is the trade, exhibited
        rather than described."""
        other = self.snap()
        remap = {"2305843009213694090": "2305843009213694099",
                 "2305843009213694091": "2305843009213694098"}
        other["names"] = {p: int(remap.get(str(i), i)) for p, i in other["names"].items()}
        other["inodes"] = {remap.get(k, k): dict(v, ino=int(remap.get(k, k)))
                           for k, v in other["inodes"].items()}
        other["paths"] = {remap.get(k, k): v for k, v in other["paths"].items()}
        self.assertNotEqual(other["names"], self.snap()["names"],
                            "the perturbation did nothing — this row proves nothing")
        self.assertEqual(identity_blind(self.snap()), identity_blind(other))

    def test_EVERY_OTHER_FIELD_still_reds(self):
        """One perturbation per field, each required to survive the relabelling. A field that
        stopped reding here would be a field batching could change unseen."""
        base = identity_blind(self.snap())
        cases = {}
        for field, value in (("kind", "dir"), ("perm", 0o600), ("uid", 4242), ("gid", 4242),
                             ("size", 999), ("content_hash", "zz"),
                             ("xattrs", {"user.x": "1"}), ("target", "/elsewhere")):
            s = self.snap()
            s["inodes"]["2305843009213694090"][field] = value
            cases[field] = s
        s = self.snap()                                   # a name bound to the other node
        s["names"]["/a"] = 2305843009213694091
        cases["names"] = s
        s = self.snap()                                   # a directory child removed
        s["kids"]["/"] = ["a"]
        cases["kids"] = s
        s = self.snap()                                   # a second name on one node
        s["paths"]["2305843009213694090"] = ["/a", "/a2"]
        cases["paths"] = s
        self.assertEqual(len(cases), 11, "the perturbation set is not the size it claims")
        for field, perturbed in sorted(cases.items()):
            self.assertNotEqual(base, identity_blind(perturbed),
                                "a change to %r survived the relabelling unseen — the "
                                "comparison launders more than the numbers" % field)


if __name__ == "__main__":
    unittest.main()
