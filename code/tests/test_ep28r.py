"""EP-28R — THE FILL-ORDERING PASS: exhibited at W1, RULED at W3, LANDED here at W4.

W4e.C stopped on four READ-DERIVED rows with no failing input ever constructed: the port
takes no lock, the fold's writer runs inside the appending thread's decide region, the
fold's reader runs outside every region, and nothing in `KernelPort` orders them. W1 was
authored to establish OR REFUTE that reading before anything else ran. IT ESTABLISHED IT.

THE EXHIBITION, AND WHY THIS FORM OF IT ADMITS NO ARGUMENT ABOUT WHICH PREFIX. The mover
is `FILE-RENAME /d/a -> /d/a` — a rename onto ITSELF. It is permitted, it is recorded, and
`custody.State.snapshot()` is BYTE-IDENTICAL either side of it, so the whole record folds
to ONE state and there is no second state for a concurrent reader to have caught early or
late. In that window, with the port UNORDERED:

    FILL-READDIR on the parent answers 0 with an EMPTY listing, for a directory that
    holds exactly one entry in every state the record has ever had;
    FILL-LOOKUP for that entry answers -ENOENT, for a file that exists in every state
    the record has ever had.

THE MECHANISM IS THE REBIND'S TWO STEPS. `custody.State.apply` folds a rename as
`self._bind(dst, self._unbind(src))`. Between those two calls the name is in NEITHER
`names` NOR `kids` — a condition no record boundary describes. The fill's reads are each
atomic; the STATE they read is torn. That distinction is the whole finding, and it is why
the arms below hold the WRITER between its own two mutations rather than holding a reader
inside a dict.

WHAT W4 LANDED — SHAPE (a), MENTOR-RULED 2026-08-07 AND RE-RULED THE SAME DAY. The port
ORDERS the fold's writer against the fill's reader: `_on_append` takes `KernelPort`'s
`_fold_order` across the WHOLE advance, both fold-reading fills take it across their WHOLE
read, and A FILL WAITS RATHER THAN SERVING STALE. The snapshot shape (c) was built, driven
green, and REVERTED: a snapshot is a copy of the namespace, so copying it puts a term on
the act path that grows with the system forever, and `tests/test_ep28e_w4.py`'s
`T-PER-ACT-PATH-CARRIES-NO-NAMESPACE-TERM` is the standing guard that forbids exactly that.

THE SEPARATOR IS CONDITIONAL AGAINST UNCONDITIONAL, NOT BOUNDED AGAINST UNBOUNDED, and the
difference is recorded here because the second phrasing was said first and then WITHDRAWN by
its own author on 2026-08-07. "A wait is bounded" holds unqualified only in the FILL-WAITS
direction. The APPENDER-WAITS direction is bounded by one fill ONLY IF FILLS DO NOT QUEUE —
`TestTheINVERSION` below measures x3.72 at a 203-entry root rising to x5.00 at 3,203, so that
bound GROWS with fill duration, which grows with directory size. (a) still beats (c): (c)'s
namespace term is on EVERY act unconditionally and (a)'s ordering only on acts CONCURRENT
with a fill. THE QUEUEING QUESTION IS HOMED, NOT DROPPED — EP-28C §11.2 carries it to the
contended arms, and `TestTheINVERSION` is PRESERVED as its instrument rather than rebuilt
there.

SO EVERY EXHIBITION ROW IN THIS FILE IS DRIVEN AS A PAIR, and the pair is the whole point:
the SAME arm, through the SAME real fill handlers, against a port whose ordering is
DEFEATED and against the shipped one. Defeated, it tears. Ordered, the reader WAITS and
then answers a state the record held. A convergence row on its own would pass on a port
that had simply become slower.

THE TWO OBLIGATIONS THE RULING CARRIES, both driven below:

  1. Every fold-derived fill answer CITES its coordinate — `at_seq`, the record position
     the answer reflects, on the ENOENT branches as well, because a negative answer is a
     claim about a state exactly as a positive one is.
  2. The staleness carries a stated bound. Under (a) it is DEGENERATE — zero by
     construction — and it is ASSERTED rather than presumed, because a degenerate
     guarantee is still a guarantee somebody has to prove.

AND THE FAIRNESS TEST ON THE RULING'S OWN REASONING. Shape (b) was eliminated for making a
cache read blockable by an unrelated act; shape (a) risks the EXACT INVERSE, and the
mentor filed that as its own defect rather than the pass's. `TestTheINVERSION` drives it:
the fill's ordering and the appender's batch lock are NOT the same lock, and the ordering
is NEVER held across `fdatasync` — EP-28C's decide/sync decoupling is not re-coupled here.
What the arms DO find is reported rather than argued away.
"""

import ast
import errno as E
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from bridge.kernel_port import KernelPort                     # noqa: E402
from bridge.mount import build_brain                          # noqa: E402
from bridge import custody                                    # noqa: E402

GOVOSFS_C = os.path.join(REPO, "planning", "vm", "govosfs", "govosfs.c")

#: How long an arm waits for an event it EXPECTS to fire. Generous on purpose: a timeout
#: here is an arm that did not run, and every row below says so rather than reporting a
#: negative it did not earn.
FIRES = 20


def _wire(op, cls="DECISION", **kw):
    f = {"id": "1", "op": op, "class": cls, "uid": "1000", "gid": "1000", "pid": "42"}
    f.update({k: str(v) for k, v in kw.items()})
    return f


def _names_of(payload):
    if not payload:
        return []
    return sorted(line.split("\t")[0] for line in payload.decode().split("\n") if line)


class _NoOrdering:
    """THE ORDERING, DEFEATED — the port exactly as it stood before W4 landed.

    A context manager that orders nothing. Substituted for `KernelPort._fold_order`, it
    restores the pre-landing composition through the REAL fill handlers and the REAL
    `_on_append`, varying ONE thing. That is what makes every convergence row below a
    near-miss pair rather than an assertion that the code is now correct: a row that only
    ever saw the ordered port would pass on a port that had merely become slow."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _CountingOrder:
    """THE ORDERING, WRAPPED SO A WAIT IS OBSERVED RATHER THAN TIMED.

    A fill that waits produces no answer, and "no answer yet" read off a clock is a
    statement about the clock. This wrapper fires one event when the watched thread REACHES
    the acquire and another when it GETS IN, so "it waited" is the pair (reached, did not
    get in) — and the negative half needs no window at all, because the thread cannot get
    in while the holder holds it. Delegates to the real lock, so the ordered arm is the
    shipped construct and not a model of it."""

    def __init__(self, real, watch="R", ordering=True):
        self._real = real
        self._ordering = ordering
        self.watch = watch
        self.reached = threading.Event()
        self.got_in = threading.Event()
        self.entries = []

    def __enter__(self):
        name = threading.current_thread().name
        if name == self.watch:
            self.reached.set()
        if self._ordering:
            self._real.acquire()
        self.entries.append(name)
        if name == self.watch:
            self.got_in.set()
        return self

    def __exit__(self, *exc):
        if self._ordering:
            self._real.release()
        return False


class _World:
    """One brain, one port, the same construction the other W4e batteries use."""

    def __init__(self, ordered=True):
        self.dir = tempfile.mkdtemp(prefix="ep28r-")
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)
        self.ordering = self.port._fold_order
        if not ordered:
            self.port._fold_order = _NoOrdering()

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, op, payload=b"", **kw):
        return self.port.handle(_wire(op, **kw), payload)[0]

    def full(self, op, payload=b"", **kw):
        return self.port.handle(_wire(op, **kw), payload)

    def ino(self, path):
        return custody.render_ino(self.port.state.lookup(path).ino)

    def fold(self):
        """The whole served state as one comparable value. `snapshot()` is the estate's
        own instrument and is what SHADOW-DIFF compares, so a mover this call cannot tell
        apart is a mover the conformance harness cannot tell apart either."""
        return json.dumps(self.port.state.snapshot(), sort_keys=True)


#: THE WORLD EVERY ARM BUILDS: one directory holding exactly one entry.
SETUP = (("FILE-MKDIR", {"path": "/d", "perm": "755"}),
         ("FILE-CREATE", {"path": "/d/a", "perm": "644"}))

#: THE MOVER. A rename onto itself: PERMITTED, RECORDED, and a no-op on the fold. The
#: no-op is what removes every "you caught it between two different states" answer, and it
#: is asserted rather than asserted-about (`test_the_mover_is_a_NO_OP_on_the_world`).
MOVER = ("FILE-RENAME", {"path": "/d/a", "new_path": "/d/a"})

#: THE THREE MEMBERS OF THE FILL CLASS, ENUMERATED RATHER THAN SAMPLED — the whole of
#: `KernelPort._fill`'s dispatch, so no member is silently left out of the finding. Each
#: is (label, how to build its wire from the world, how to reduce its answer).
#:
#: FILL-CONTENT IS THE DISCRIMINATING NEGATIVE AND NOT A FILLER MEMBER. It reads the blob
#: store by a hash the record named and touches the fold at no point, so it must NOT tear
#: and — §A49, the member LEAST likely to share the landed property — must NOT WAIT and
#: must carry NO coordinate. A finding that every fill tears would be a finding about
#: threads; a finding that the two fills which read the fold tear and the one that does not
#: read it does not is a finding about this composition.
def _members(w):
    dino = w.ino("/d")
    node = w.port.state.lookup("/d/a")
    return (
        ("FILL-READDIR",
         {"op": "FILL-READDIR", "cls": "FILL", "ino": dino},
         lambda st, f, p: (st, tuple(_names_of(p)))),
        ("FILL-LOOKUP",
         {"op": "FILL-LOOKUP", "cls": "FILL", "parent": dino, "name": "a"},
         lambda st, f, p: (st, f.get("ino"))),
        ("FILL-CONTENT",
         {"op": "FILL-CONTENT", "cls": "FILL", "hash": node.content_hash or ""},
         lambda st, f, p: (st, p)),
    )


def _observe(w, wire_kw, reduce_):
    st, f, p = w.port.handle(_wire(**wire_kw), b"")
    return reduce_(st, f, p)


class _swap_listener:
    """REPLACE THE LISTENER THE STORE ACTUALLY HOLDS, NOT THE ATTRIBUTE OF THE SAME NAME.

    THE STANDING CLAUSE — assert the subject exists before patching — IS NOT ENOUGH HERE
    AND FOUR ROWS OF THIS FILE PROVED IT IN ONE RUN. `KernelPort.__init__` calls
    `store.on_append(self._on_append)`, which appends a BOUND METHOD to `store._listeners`.
    Assigning `port._on_append = wrapper` afterwards is legal, the attribute exists both
    before and after, and the store still calls the object it captured at registration. The
    wrapper binds nothing, the arm collects nothing, and the row reports a clean negative
    about a subject it never reached.

    So the subject is located WHERE THE CONSUMER LOOKS, its identity is asserted, and there
    is required to be exactly one of it."""

    def __init__(self, store, port, wrap):
        self.store, self.port, self.wrap = store, port, wrap

    def __enter__(self):
        hits = [i for i, fn in enumerate(self.store._listeners)
                if getattr(fn, "__self__", None) is self.port]
        assert len(hits) == 1, (
            "the store holds %d listeners bound to this port, not one — the arm cannot say "
            "which one it replaced" % len(hits))
        self.i = hits[0]
        self.real = self.store._listeners[self.i]
        assert self.real.__func__ is type(self.port)._on_append, (
            "the port's registered listener is %r and not `_on_append` — wrapping it would "
            "be watching a different thing" % (self.real,))
        self.store._listeners[self.i] = self.wrap(self.real)
        return self

    def __exit__(self, *exc):
        self.store._listeners[self.i] = self.real
        return False


class _RecordingLock:
    """The store's write lock, wrapped so a REACH for it is observable.

    `_thread.RLock` refuses attribute assignment, so the lock is replaced rather than
    patched. Everything the store does with it — `with self._write_lock:` — goes through
    these two methods, so nothing about the store's own use changes."""

    def __init__(self, real):
        self._real = real
        self.reached = []

    def __enter__(self):
        self.reached.append(threading.current_thread().name)
        self._real.acquire()
        return self

    def __exit__(self, *exc):
        self._real.release()
        return False

    def acquire(self, *a, **k):
        self.reached.append(threading.current_thread().name)
        return self._real.acquire(*a, **k)

    def release(self):
        return self._real.release()


class _Arm:
    """What one held arm returns. A named structure rather than a tuple, because this arm
    now reports FIVE things and a five-tuple is where a reader starts guessing."""

    def __init__(self, before, during, after, mover, folds, reached, got_in):
        self.before = before
        self.during = during
        self.after = after
        self.mover = mover
        self.folds = folds
        self.reached = reached      # the fill got as far as asking for the ordering
        self.got_in = got_in        # the fill got the ordering while the writer held it


def held_arm(member_index, ordered=True):
    """THE CONSTRUCTED INTERLEAVING: hold the fold's WRITER between the rename's two
    mutations, and let the FILL run IN ITS OWN THREAD.

    THE ARM MOVED THREADS AT W4 AND THAT IS THE LANDING SHOWING UP IN THE INSTRUMENT. W1
    took the observation on the thread that also had to release the writer, which is sound
    only while the fill cannot block: under the landed ordering that thread would wait for
    a release only it can issue, and the arm would report the post-release answer as though
    it were the answer during the window. So the reader is its own thread, and the arm
    reports whether it ANSWERED during the window at all.

    TWO EVENTS AND ONE ORDER, no sleeps and no retries. Thread A takes the mover through
    the real `port.handle`; `gate.execute` appends; `store._append_one` publishes to its
    listeners before returning; `KernelPort._on_append` takes the ordering and calls
    `state.apply`; `apply` folds the rename as `self._bind(dst, self._unbind(src))` and A
    IS HELD THE INSTANT `_unbind` RETURNS. Thread R is then released, takes its observation
    through the same real `port.handle`, and only then is A let go.

    THE HOLD IS ON A METHOD THAT EXISTS, ASSERTED BEFORE IT IS SHADOWED. A monkeypatch
    assigning to an attribute the subject does not have is legal and binds nothing at all,
    which is how a row hid from a full-suite inventory two passes ago. The wrapper also
    COUNTS its own invocations and the arm refuses to report unless it ran."""
    w = _World(ordered=ordered)
    try:
        for op, kw in SETUP:
            assert w.call(op, **kw) == 0, (op, kw)
        assert w.call("FILE-WRITE", b"ep28r", path="/d/a") == 0
        label, wire_kw, reduce_ = _members(w)[member_index]

        before = _observe(w, wire_kw, reduce_)
        fold_before = w.fold()

        assert "_unbind" in dir(w.port.state), (
            "the fold has no `_unbind` to hold at — the hold point named by this arm does "
            "not exist and shadowing it would bind a wrapper nobody calls")
        watched = _CountingOrder(w.ordering, watch="R", ordering=ordered)
        w.port._fold_order = watched

        real_unbind = w.port.state._unbind
        torn = threading.Event()
        released = threading.Event()
        answered = threading.Event()
        calls = []
        box = {}

        def held_unbind(path):
            out = real_unbind(path)
            calls.append(path)
            if threading.current_thread().name == "A":
                torn.set()
                released.wait(FIRES * 3)
            return out

        w.port.state._unbind = held_unbind

        def mover():
            box["status"] = w.call(MOVER[0], **MOVER[1])

        def reader():
            try:
                box["during"] = _observe(w, wire_kw, reduce_)
            except BaseException as exc:              # noqa: BLE001 — reported, never eaten
                box["during_error"] = exc
            finally:
                answered.set()

        ta = threading.Thread(target=mover, name="A")
        tr = threading.Thread(target=reader, name="R")
        ta.start()
        try:
            if not torn.wait(FIRES):
                raise AssertionError(
                    "the mover never reached the hold point, so this arm did not run: "
                    "status %r, `_unbind` invocations %r" % (box.get("status"), calls))
            tr.start()
            # THE POSITIVE HALF FIRST AND IT IS DETERMINISTIC: R reaches the acquire, or
            # this arm did not run. The NEGATIVE half needs no window — R cannot enter an
            # ordering another thread is holding — but the arm still waits for the answer
            # event so that "did not answer" is a fact about R and not about when we looked.
            reached = watched.reached.wait(FIRES)
            got_in = watched.got_in.is_set()
            answered_during = answered.wait(1.0)
        finally:
            released.set()
            ta.join(FIRES * 2)
            answered.wait(FIRES)
            tr.join(FIRES * 2)
            del w.port.state._unbind
            w.port._fold_order = w.ordering

        if "during_error" in box:
            raise AssertionError("the reader raised inside the window: %r"
                                 % (box["during_error"],))
        after = _observe(w, wire_kw, reduce_)
        assert calls, "the wrapper never ran — it was bound to nothing"
        return _Arm(before, box.get("during"), after, box.get("status"),
                    (fold_before, w.fold()), reached, got_in and answered_during)
    finally:
        w.close()


def answers_about_no_state_the_record_held(before, during, after):
    """THE PREDICATE THE WHOLE FINDING RESTS ON, AND IT IS DELIBERATELY THE WEAKEST ONE
    THAT STILL SAYS SOMETHING.

    A fill's answer is a defect only if it matches NO state the record produced. It is not
    enough that it differs from the answer before, or from the answer after: a reader that
    catches the world early or late has read a real state and answered truthfully about it.
    So the predicate flags only the third case, and `TestTheTEARPredicateITSELF` drives it
    both ways rather than trusting that description."""
    return during != before and during != after


def coordinate_names_a_record_position(records, at):
    """OBLIGATION 1's FIRST HALF AS A FUNCTION: does this coordinate name a position the
    record actually has, and does the record at that position agree it is that position?
    Both halves matter — a bare range check passes for a coordinate that has drifted off
    the seq it claims to index."""
    if not isinstance(at, int) or isinstance(at, bool):
        return False
    if not (1 <= at <= len(records)):
        return False
    return records[at - 1].get("seq") == at


def answer_matches_the_prefix_at(records, at, served_snapshot):
    """OBLIGATION 1's SECOND HALF: the answer's content is what the record's own prefix at
    that coordinate folds to. Re-derived from the record by the SAME `custody.fold` the port
    was built with, so this is one derivation over two sources and not two implementations
    being asked to agree."""
    return json.dumps(custody.fold(records[:at]).snapshot(), sort_keys=True) == served_snapshot


class TestTheSubjectExists(unittest.TestCase):
    """NON-VACUITY FIRST, AND ON EVERY LIMB THE EXHIBITION LEANS ON. An arm that acted on
    nothing, a mover that was refused, or a fill that answered about an empty world would
    all satisfy an inequality between two observations."""

    def setUp(self):
        self.w = _World()
        for op, kw in SETUP:
            self.assertEqual(self.w.call(op, **kw), 0, "%s did not act" % op)
        self.assertEqual(self.w.call("FILE-WRITE", b"ep28r", path="/d/a"), 0)

    def tearDown(self):
        self.w.close()

    def test_the_world_holds_subjects_and_the_directory_holds_exactly_one_entry(self):
        self.assertGreater(len(self.w.port.state.names), 1,
                           "the fold holds nothing but the root, so no fill below can be "
                           "about anything")
        self.assertEqual(self.w.port.state.children("/d"), ["a"],
                         "the arms' directory does not hold exactly one entry, so an empty "
                         "listing during the window would not be a missing entry")

    def test_the_mover_is_PERMITTED_and_is_RECORDED(self):
        """A refused mover exhibits nothing: it would append a refusal, fold nothing, and
        never reach the hold point at all."""
        n = len(self.w.store.all())
        self.assertEqual(self.w.call(MOVER[0], **MOVER[1]), 0,
                         "the mover is refused, so the window it opens does not exist")
        added = self.w.store.all()[n:]
        self.assertEqual([r.get("action") for r in added], ["FILE-RENAME"],
                         "the mover did not record exactly one rename: %r"
                         % ([r.get("action") for r in added],))

    def test_the_mover_is_a_NO_OP_on_the_world(self):
        """THE ROW THAT MAKES THE FINDING UNARGUABLE. If the served state is identical
        either side of the mover, then the record folds to ONE state over the whole window
        and "the reader caught a different prefix" is not an available answer."""
        before = self.w.fold()
        self.assertEqual(self.w.call(MOVER[0], **MOVER[1]), 0)
        self.assertEqual(self.w.fold(), before,
                         "the mover CHANGED the served state, so the record holds two "
                         "states and a differing observation could be either of them — "
                         "this file's whole construction depends on it holding one")

    def test_the_FIRST_CHOICE_mover_is_REFUSED_by_the_law_and_the_refusal_names_the_other(self):
        """§A49, and the parent pass's own experience repeated: the first member chosen was
        the self-rename of the DIRECTORY, which is the more general shape. The engine
        REFUSES it — `contains:empty` is a DECLARED check and a directory holding an entry
        fails it — so the reachable member is the self-rename of the FILE, which is what
        every arm above uses. Recorded as a row rather than as a silent narrowing."""
        self.assertEqual(self.w.call("FILE-RENAME", path="/d", new_path="/d"),
                         -E.ENOTEMPTY,
                         "the directory self-rename is no longer refused ENOTEMPTY — the "
                         "narrowing this row records has expired and the more general "
                         "member is now reachable")

    def test_every_member_answers_about_something_before_any_window_opens(self):
        for label, wire_kw, reduce_ in _members(self.w):
            st, _f, _p = self.w.port.handle(_wire(**wire_kw), b"")
            self.assertEqual(st, 0, "%s does not answer in the quiet world" % label)
        st, fields, payload = self.w.port.handle(
            _wire(**_members(self.w)[0][1]), b"")
        self.assertEqual(_names_of(payload), ["a"],
                         "the readdir does not list the one entry, so an empty listing "
                         "later would not be a loss")
        st, fields, _p = self.w.port.handle(_wire(**_members(self.w)[1][1]), b"")
        self.assertTrue(fields.get("ino"), "the lookup answers about no node")
        _st, _f, payload = self.w.port.handle(_wire(**_members(self.w)[2][1]), b"")
        self.assertEqual(payload, b"ep28r",
                         "the content fill does not answer with the recorded bytes, so its "
                         "role as the discriminating negative is vacuous")


class TestTheTEARPredicateITSELF(unittest.TestCase):
    """§A64 ON THE PREDICATE THAT CARRIES THE FINDING, DRIVEN BOTH WAYS. A predicate that
    flagged every difference would report a tear for a reader that merely arrived early,
    and the exhibition would prove nothing at all."""

    def test_NEAR_MISS_an_answer_matching_the_BEFORE_state_is_not_flagged(self):
        self.assertFalse(answers_about_no_state_the_record_held(
            (0, ("a",)), (0, ("a",)), (0, ("b",))),
            "a reader that answered about the state before the act was flagged as a tear")

    def test_NEAR_MISS_an_answer_matching_the_AFTER_state_is_not_flagged(self):
        self.assertFalse(answers_about_no_state_the_record_held(
            (0, ("a",)), (0, ("b",)), (0, ("b",))),
            "a reader that answered about the state after the act was flagged as a tear")

    def test_an_answer_matching_NEITHER_state_is_flagged(self):
        self.assertTrue(answers_about_no_state_the_record_held(
            (0, ("a",)), (0, ()), (0, ("b",))),
            "an answer belonging to no state of the record was not flagged, so the rows "
            "below cannot report the thing they are for")


class TestTheORDERINGCLOSESBOTHFILLARMS(unittest.TestCase):
    """THE LANDING, DRIVEN AS A PAIR ON EVERY ARM — the fence's own requirement, in the
    fence's own words: `FILL-LOOKUP` walks no container and tears anyway, so a fix aimed at
    the ITERATION closes `FILL-READDIR`'s arm and leaves `FILL-LOOKUP`'s open. The pair
    exists so that fix cannot ship green.

    EACH ROW RUNS THE SAME ARM TWICE THROUGH THE SAME REAL HANDLERS, varying ONE thing: the
    port's `_fold_order`. Defeated, the fill answers DURING the window and its answer
    belongs to no state the record held. Ordered, the fill WAITS — it reaches the acquire
    and does not get in — and then answers a state the record held.

    [FLIPPED AT W4, AND THE FLIP IS THE LANDING. These two rows asserted the TEAR at W1 and
    were EXPIRY ROWS by construction: W1's own entry said so and named the shape of the
    flip. The unordered halves below are those rows, unchanged in mechanism and moved onto
    a port whose ordering is defeated, so the exhibition is not lost when the defect is.]"""

    def _pair(self, index, label, torn_shape):
        loose = held_arm(index, ordered=False)
        self.assertEqual(loose.mover, 0, "the mover was refused, so no window opened")
        self.assertEqual(loose.folds[0], loose.folds[1],
                         "the mover moved the world, so the record holds more than one "
                         "state and this row cannot say the answer belongs to none")
        self.assertTrue(
            answers_about_no_state_the_record_held(
                loose.before, loose.during, loose.after),
            "REFUTED for %s with the ordering DEFEATED: the fill answered %r, which is a "
            "state the record held. The near-miss no longer misses, so the ordered half "
            "below proves nothing." % (label, loose.during))
        self.assertEqual(loose.during, torn_shape,
                         "%s's TEAR has changed shape to %r — the landing is costed "
                         "against the shape, so re-derive before believing the pair"
                         % (label, loose.during))

        tight = held_arm(index, ordered=True)
        self.assertEqual(tight.mover, 0, "the mover was refused, so no window opened")
        self.assertEqual(tight.folds[0], tight.folds[1], "the mover moved the world")
        self.assertTrue(tight.reached,
                        "%s never asked for the ordering, so this arm did not run and its "
                        "negative below is about the instrument" % label)
        self.assertFalse(tight.got_in,
                         "%s got the ordering while the fold's writer held it, so the "
                         "writer and the reader are not ordered against each other" % label)
        self.assertEqual(tight.before, tight.after, "the world did not come back")
        self.assertEqual(
            tight.during, tight.after,
            "%s answered %r after waiting, against %r either side of the mover — a fill "
            "that waits and then answers a state the record never held is the defect "
            "wearing the fix's clothes" % (label, tight.during, tight.after))
        self.assertFalse(
            answers_about_no_state_the_record_held(
                tight.before, tight.during, tight.after),
            "%s STILL answers about no state the record held under the landed ordering: %r"
            % (label, tight.during))
        return loose, tight

    def test_THE_READDIR_ARM_tears_unordered_and_WAITS_ordered(self):
        self._pair(0, "FILL-READDIR", (0, ()))

    def test_THE_LOOKUP_ARM_tears_unordered_and_WAITS_ordered(self):
        """THE MEMBER THE PRIOR PASS PRICED AS UNEXPOSED. Its fold reads are single-key
        `dict.get`s, each atomic. It tore anyway, because what is torn is the STATE and not
        the dict — which is why the ordering covers the fill's WHOLE read and not its
        iteration."""
        self._pair(1, "FILL-LOOKUP", (-E.ENOENT, None))

    def test_the_content_fill_reads_NO_fold_so_it_neither_TEARS_nor_WAITS(self):
        """§A49 — THE MEMBER LEAST LIKELY TO SHARE THE LANDED PROPERTY, and the
        discriminating negative in both directions at once. Without it "the fills wait now"
        would be a claim about threads. With it: the two members that read the fold wait,
        and the one that answers from the blob store by a hash the record named does not
        wait, does not tear, and is not slowed by an unrelated act."""
        arm = held_arm(2, ordered=True)
        self.assertEqual(arm.mover, 0, "the mover was refused, so no window opened")
        self.assertEqual(arm.before, (0, b"ep28r"), "the content fill answered about nothing")
        self.assertEqual(arm.during, (0, b"ep28r"),
                         "the content fill did not answer DURING the window (%r) — it reads "
                         "no fold, so the ordering must not reach it" % (arm.during,))
        self.assertFalse(arm.reached,
                         "the content fill asked for the fold's ordering, so a read that "
                         "touches no fold is now blockable by an unrelated act")
        self.assertFalse(
            answers_about_no_state_the_record_held(arm.before, arm.during, arm.after),
            "the content fill tears too (%r), so the exposure is not the fold reads and "
            "the finding's subject is wrong" % (arm.during,))

    def test_the_RECORD_is_right_while_the_view_was_wrong(self):
        """THE DIRECTION, STATED AS A ROW. W4e exhibited the opposite one — two records for
        one act with every view correct. W1 exhibited one act, one record, and a view that
        was correct at no point of the record. Nothing in this estate looks either way, and
        that stays true after the landing: this row keeps the record→view half honest."""
        w = _World()
        try:
            for op, kw in SETUP:
                self.assertEqual(w.call(op, **kw), 0)
            n = len(w.store.all())
            self.assertEqual(w.call(MOVER[0], **MOVER[1]), 0)
            renames = [r for r in w.store.all()[n:] if r.get("action") == "FILE-RENAME"]
            self.assertEqual(len(renames), 1,
                             "the record does not hold exactly the one act performed, so "
                             "this is W4e's finding again and not its mirror")
            replayed = custody.fold(w.store.all())
            self.assertEqual(json.dumps(replayed.snapshot(), sort_keys=True), w.fold(),
                             "the fold replayed from the record disagrees with the served "
                             "one, which would be a different defect entirely")
        finally:
            w.close()


class TestTheExposureIsNOTTheContainerWalk(unittest.TestCase):
    """THE CORRECTION TO THE PRIOR PASS'S PRICING, DRIVEN, AND IT IS WHY THE LANDING GUARDS
    THE WHOLE READ.

    `tests/test_ep28c_w4e_c.py` priced the exposure at the CONTAINER WALK: `lookup` and
    `exists` are single-key dict reads, `children` returns `sorted(self.kids.get(...))`
    which walks one, so "the exposure the channel would open is the FILL class's" was read
    off the walk. That row is TRUE and its narrowing is TOO NARROW: `FILL-LOOKUP` walks no
    container and tears in the same window.

    [FLIPPED AT W4 IN ONE HALF ONLY, and the halves are named because they flip
    independently. HALF ONE — the lookup fill walks no container — is UNCHANGED and still
    driven. HALF TWO — and it tears — now needs the ordering DEFEATED, because the landing
    closed it. A row that cited the tear against the shipped port would have gone red for
    the right reason and been repaired for the wrong one.]"""

    def test_the_lookup_fill_walks_NO_container(self):
        w = _World()
        try:
            for op, kw in SETUP:
                self.assertEqual(w.call(op, **kw), 0)
            seen = []
            real = {name: getattr(w.port.state, name)
                    for name in ("lookup", "exists", "children", "path_of")}
            for name in real:
                self.assertTrue(callable(real[name]),
                                "the fold has no `%s` to watch" % name)

            def wrap(name):
                def go(*a, **k):
                    seen.append(name)
                    return real[name](*a, **k)
                return go

            for name in real:
                setattr(w.port.state, name, wrap(name))
            try:
                status, fields, _p = w.port.handle(
                    _wire("FILL-LOOKUP", cls="FILL", parent=w.ino("/d"), name="a"), b"")
            finally:
                for name, fn in real.items():
                    setattr(w.port.state, name, fn)
            self.assertEqual(status, 0, "non-vacuity: the lookup fill answered")
            self.assertTrue(fields.get("ino"), "non-vacuity: it answered about a node")
            self.assertTrue(seen, "non-vacuity: it read the fold at all")
            self.assertNotIn("children", seen,
                             "the lookup fill now walks the container too, so it is no "
                             "longer the member that separates walking from tearing")
        finally:
            w.close()

    def test_and_the_same_member_TORE_which_is_why_the_ordering_covers_the_whole_read(self):
        """The second half, cited against the DEFEATED ordering so the two halves of this
        correction cannot drift apart into one true row and one stale one. If this stops
        tearing with the ordering defeated, the walk-based pricing was right after all and
        the landing is guarding something that never needed it."""
        arm = held_arm(1, ordered=False)
        self.assertEqual(arm.mover, 0)
        self.assertTrue(
            answers_about_no_state_the_record_held(arm.before, arm.during, arm.after),
            "the member that walks no container no longer tears without the ordering, so "
            "this correction has expired and the walk-based pricing is right again")


class TestTheCOORDINATE(unittest.TestCase):
    """OBLIGATION 1 OF THE RULING: a served state NAMES the record it is a state OF.

    `at_seq` is the largest position H such that every record at 1..H has been folded into
    the state the answer was read from. It is on both branches of both fold-reading fills —
    a negative answer is a claim about a state exactly as a positive one is — and it is NOT
    on the content fill, which reads no fold and has no state to be about.

    EVERY ROW HERE CARRIES ITS RED WORLD, and the red worlds are real ports rather than
    hand-built tuples: without them a row can pass by reading its own output back."""

    def setUp(self):
        self.w = _World()
        for op, kw in SETUP:
            self.assertEqual(self.w.call(op, **kw), 0)
        self.assertEqual(self.w.call("FILE-WRITE", b"ep28r", path="/d/a"), 0)

    def tearDown(self):
        self.w.close()

    def _at(self, wire_kw):
        st, fields, _p = self.w.port.handle(_wire(**wire_kw), b"")
        return st, fields

    def test_every_FOLD_DERIVED_fill_answer_CITES_a_coordinate_including_the_ABSENCES(self):
        dino = self.w.ino("/d")
        cases = {
            "readdir, found":  {"op": "FILL-READDIR", "cls": "FILL", "ino": dino},
            "lookup, found":   {"op": "FILL-LOOKUP", "cls": "FILL",
                                "parent": dino, "name": "a"},
            "lookup, ABSENT":  {"op": "FILL-LOOKUP", "cls": "FILL",
                                "parent": dino, "name": "nope"},
        }
        for label, kw in sorted(cases.items()):
            with self.subTest(case=label):
                _st, fields = self._at(kw)
                self.assertIn("at_seq", fields,
                              "%s answers without naming the record position it reflects" % label)
                self.assertTrue(
                    coordinate_names_a_record_position(
                        self.w.store.all(), int(fields["at_seq"])),
                    "%s cited %r, which names no position this record has"
                    % (label, fields.get("at_seq")))

    def test_the_content_fill_which_reads_NO_fold_carries_NO_coordinate(self):
        """The discriminating negative on the obligation itself. A coordinate on an answer
        that reflects no fold state would be a number with nothing behind it, and a reader
        would be entitled to compare it against the record."""
        node = self.w.port.state.lookup("/d/a")
        _st, fields, payload = self.w.port.handle(
            _wire("FILL-CONTENT", cls="FILL", hash=node.content_hash or ""), b"")
        self.assertEqual(payload, b"ep28r", "non-vacuity: the content fill answered")
        self.assertNotIn("at_seq", fields,
                         "the content fill cites a record position, and it reads no fold — "
                         "so the coordinate is being stamped on rather than derived")

    def test_RED_WORLD_a_coordinate_naming_NO_record_position_is_caught(self):
        """§A64, driven through a REAL port rather than against a tuple: the ruling's first
        red world is a served answer whose coordinate indexes nothing. The port is given a
        mark past the end of its own record and the row requires the check to say so."""
        dino = self.w.ino("/d")
        real = self.w.port._folded_high
        self.w.port._folded_high = len(self.w.store.all()) + 5
        try:
            _st, fields, _p = self.w.port.handle(
                _wire("FILL-READDIR", cls="FILL", ino=dino), b"")
        finally:
            self.w.port._folded_high = real
        self.assertEqual(int(fields["at_seq"]), len(self.w.store.all()) + 5,
                         "non-vacuity: the inflated mark did not reach the answer, so this "
                         "red world tested nothing")
        self.assertFalse(
            coordinate_names_a_record_position(
                self.w.store.all(), int(fields["at_seq"])),
            "a coordinate naming no record position passed the check, so the row above "
            "would pass for a port that made the number up")

    def test_the_ANSWER_MATCHES_the_fold_of_the_prefix_at_that_coordinate(self):
        dino = self.w.ino("/d")
        _st, fields, _p = self.w.port.handle(
            _wire("FILL-READDIR", cls="FILL", ino=dino), b"")
        at = int(fields["at_seq"])
        self.assertTrue(
            answer_matches_the_prefix_at(self.w.store.all(), at, self.w.fold()),
            "the served state is not what the record's own prefix at %d folds to, so the "
            "coordinate names a position the answer is not about" % at)

    def test_RED_WORLD_a_coordinate_ONE_ACT_EARLY_does_not_match_its_answer(self):
        """The ruling's second red world, and the position is CHOSEN rather than taken as
        `at - 1`: the last record is usually a dual-audit mirror, which the custody fold
        ignores, so dropping it changes nothing and the near-miss would miss. The position
        used is the one just before the last act that MOVED the namespace."""
        recs = self.w.store.all()
        moved = [r["seq"] for r in recs if r.get("action") == "FILE-CREATE"]
        self.assertTrue(moved, "non-vacuity: no namespace-moving act in this world")
        early = moved[-1] - 1
        self.assertGreaterEqual(early, 1)
        self.assertTrue(
            coordinate_names_a_record_position(recs, early),
            "non-vacuity: the chosen early position is not a record position at all, so a "
            "failure below would be about the position and not about the match")
        self.assertFalse(
            answer_matches_the_prefix_at(recs, early, self.w.fold()),
            "the served state matches the prefix at %d, one act before the create that put "
            "the subject there — so the match check cannot tell a right coordinate from a "
            "wrong one and every row above it is vacuous" % early)

    def test_the_coordinate_is_a_CONTIGUOUS_HIGH_WATER_MARK_and_NOT_a_count(self):
        """DRIVEN, because `state.applied` is the obvious coordinate and it is WRONG.

        Records do NOT reach this listener in seq order: the dual-audit mirror appends from
        inside the on-append callback and the nested record publishes to every listener
        before the outer one does. A COUNT therefore reads a position whose PREFIX the
        served state does not carry. This row watches the real composition and requires both
        halves: the order IS out of sequence, and the mark never names an unfolded
        position."""
        steps = []

        def wrap(real):
            def watched(record):
                out = real(record)
                steps.append((record.get("seq"), self.w.port.state.applied,
                              self.w.port._folded_high, set(self.w.port._folded_above)))
                return out
            return watched

        with _swap_listener(self.w.store, self.w.port, wrap):
            # THE MOVER IS A REFUSED ACT ON PURPOSE. `op-refused` is in the
            # `dual-audit-actions` pack and an ordinary FS act is not, so a refusal is what
            # actually makes the mirror append from inside the callback — which is the whole
            # mechanism this row is about, and it is reachable from an ordinary refused
            # filesystem call rather than only from a governance act.
            self.assertEqual(self.w.call("FILE-RMDIR", path="/d"), -E.ENOTEMPTY,
                             "the refused act did not reach its declared check, so no "
                             "mirrored record was appended and this row saw nothing")
        self.assertTrue(steps, "non-vacuity: the fold's writer was not reached at all")
        seqs = [s for s, _a, _h, _ab in steps]
        self.assertNotEqual(seqs, sorted(seqs),
                            "records now reach this listener IN seq order (%r), so the "
                            "count and the mark cannot diverge and the derivation behind "
                            "the mark has expired" % (seqs,))
        diverged = [(s, a, h) for s, a, h, _ab in steps if a != h]
        self.assertTrue(diverged,
                        "the count and the contiguous mark never diverged (%r), so this "
                        "row is not exercising the thing it is about" % (steps,))
        for seq, applied, high, above in steps:
            self.assertLessEqual(
                high, max(seqs + [high]),
                "the mark ran ahead of every position the listener has seen")
            self.assertNotIn(
                high + 1, set(range(1, high + 1)),
                "the mark is not contiguous")
            self.assertTrue(
                all(p > high for p in above),
                "a position at or below the mark is still sitting in the out-of-order set "
                "(mark %d, above %r) — the two disagree about what has been folded"
                % (high, sorted(above)))

    def test_the_guard_BEHIND_the_guard_no_CUSTODY_action_is_appendable_from_a_fold_callback(self):
        """WHY OUT-OF-ORDER FOLDING IS HARMLESS, ASSERTED RATHER THAN ASSUMED.

        The mark says positions 1..H are folded; it does not say nothing above H is. That
        is only safe while every record appendable from INSIDE a fold callback is one the
        custody fold ignores — otherwise the served namespace starts depending on listener
        order, and no coordinate could describe it. The nested appenders are the dual-audit
        mirrors, so their actions are the set to check, and the check is that applying one
        moves the fold NOT AT ALL."""
        nested = ("dual-audit-record", "dual-audit-b-record")
        # THE NESTING HAS TO BE MADE TO HAPPEN FIRST. An ordinary FS act is not in the
        # `dual-audit-actions` pack; `op-refused` is. Without this line the set below is the
        # setUp world's, which holds no mirrored record at all, and the non-vacuity clause
        # would be checking a world in which the mechanism never fired.
        self.assertEqual(self.w.call("FILE-RMDIR", path="/d"), -E.ENOTEMPTY,
                         "the refused act did not record, so nothing nested")
        state = custody.fold(self.w.store.all())
        base = json.dumps(state.snapshot(), sort_keys=True)
        seen = set(r.get("action") for r in self.w.store.all())
        for action in nested:
            self.assertIn(action, seen,
                          "non-vacuity: %s is not in this record at all, so the set this "
                          "row checks is not the set that actually nests" % action)
            state.apply({"seq": 10 ** 6, "actor": "SYSTEM", "action": action,
                         "object": "/d/a", "payload": {"stream": "dual-audit"}})
            self.assertEqual(json.dumps(state.snapshot(), sort_keys=True), base,
                             "%s MOVES the custody fold, so a record folded out of order "
                             "changes the served namespace and the coordinate above cannot "
                             "describe what it names" % action)


class TestTheSTALENESSBOUND(unittest.TestCase):
    """OBLIGATION 2, DEGENERATE UNDER (a) AND STILL PROVEN.

    Shape (c) could serve a REAL but OLDER state and needed a bound on how old. Shape (a)
    serves the current one, so the bound is zero — and a degenerate guarantee is still a
    guarantee somebody has to prove, because "zero by construction" is exactly the shape of
    a claim that quietly stops being true."""

    def setUp(self):
        self.w = _World()
        for op, kw in SETUP:
            self.assertEqual(self.w.call(op, **kw), 0)

    def tearDown(self):
        self.w.close()

    def test_QUIESCENT_the_coordinate_EQUALS_the_records_own_end(self):
        dino = self.w.ino("/d")
        _st, fields, _p = self.w.port.handle(
            _wire("FILL-READDIR", cls="FILL", ino=dino), b"")
        self.assertEqual(int(fields["at_seq"]), len(self.w.store.all()),
                         "a quiet port answers about a position behind its own record, so "
                         "the staleness is not zero and it has no stated bound")

    def test_the_ZERO_is_a_MEASUREMENT_and_not_a_tautology(self):
        """THE RED WORLD FOR A DEGENERATE BOUND. A port whose folding is held back serves a
        genuinely older state, and the SAME check must report the lag rather than zero. If
        it cannot report a non-zero lag it cannot report a zero one either."""
        w = _World()
        try:
            held = []
            with _swap_listener(w.store, w.port, lambda real: held.append):
                self.assertEqual(w.call("FILE-MKDIR", path="/held", perm="755"), 0)
            self.assertTrue(held, "non-vacuity: nothing was held back")
            _st, fields, _p = w.port.handle(_wire("FILL-READDIR", cls="FILL", ino="1"), b"")
            lag = len(w.store.all()) - int(fields["at_seq"])
            self.assertGreater(lag, 0,
                               "the held-back port reports zero lag, so the quiescent zero "
                               "above is a tautology and measures nothing")
            self.assertEqual(
                json.dumps(custody.fold(
                    w.store.all()[:int(fields["at_seq"])]).snapshot(), sort_keys=True),
                w.fold(),
                "the held-back port's coordinate does not name the prefix it is serving, "
                "so the coordinate is not tracking the fold")
        finally:
            w.close()

    def test_a_fill_NEVER_answers_from_inside_the_folds_own_window(self):
        """THE BOUND'S OTHER END, and the one shape (c) could not offer: the served state is
        always the fold of a whole number of records, never a fold caught between two of one
        record's own mutations. Driven by the pair in `TestTheORDERINGCLOSESBOTHFILLARMS`;
        stated here as the bound rather than as a tear, so the two readings of the same fact
        are both on the file."""
        arm = held_arm(0, ordered=True)
        self.assertTrue(arm.reached, "non-vacuity: the fill never asked for the ordering")
        self.assertFalse(arm.got_in,
                         "the fill answered from inside the fold's own window, so the "
                         "bound is not zero and is not bounded at all")


class TestTheINVERSION(unittest.TestCase):
    """THE MENTOR'S OWN FAIRNESS TEST ON ITS OWN REASONING, CARRIED AS ROWS.

    Shape (b) was eliminated for making a cache read blockable by an unrelated act. Shape
    (a) risks the EXACT INVERSE and was not tested for it: `_on_append` writes the fold
    INSIDE THE APPENDING THREAD, so under (a) that write takes the ordering — and if a fill
    holds it for a long read, the appender's callback WAITS, possibly while holding a lock
    other submitters need.

    WHAT PASSING MEANS, NAMED RATHER THAN IMPLIED: the fill's ordering and the appender's
    batch lock MUST NOT be the same lock, and the fold's ordering MUST NOT be held across
    `fdatasync`. EP-28C's ruling stands — batching the sync is ORTHOGONAL to serialising the
    decide — and this pass must not quietly re-couple them. What the arms find BEYOND those
    two conditions is reported as a finding and raised, never argued away and never a reason
    to re-open the snapshot shape: unbounded scaling and bounded latency differ in kind."""

    def test_the_fills_ordering_and_the_stores_write_lock_are_DIFFERENT_LOCKS(self):
        w = _World()
        try:
            self.assertIsNot(w.port._fold_order, w.store._write_lock,
                             "the port's ordering IS the store's write lock, so every fill "
                             "now sits in the appender's own critical section")
            held = []
            for name in dir(w.store):
                if name.startswith("__"):
                    continue
                v = getattr(w.store, name, None)
                if v is w.port._fold_order:
                    held.append(name)
            self.assertEqual(held, [],
                             "the port's ordering is also the store's %r, so the two are "
                             "one lock under two names" % (held,))
        finally:
            w.close()

    def test_the_ORDERING_IS_NOT_HELD_ACROSS_fdatasync(self):
        """EP-28C's decoupling, re-checked against THIS landing rather than cited. The
        barrier already refuses to run with the decide region held; this row asks the same
        question of the new construct, on the thread that actually issues the sync."""
        w = _World()
        try:
            self.assertTrue(hasattr(w.port._fold_order, "_is_owned"),
                            "the ordering cannot report whether this thread holds it, so "
                            "this row cannot be driven and must not pass silently")
            # THE BARRIER IS PATCHED WHERE THE CALLER HOLDS IT. `GroupCommit` captured
            # `store._commit_batch` as a bound method at construction, so assigning to the
            # store's attribute of that name leaves the barrier untouched and the arm reads
            # a clean, empty, meaningless negative. Identity asserted before the swap.
            seen = []
            real = w.store.group_commit._commit_batch
            self.assertIs(getattr(real, "__self__", None), w.store,
                          "the group-commit's barrier is not the store's own method, so "
                          "wrapping it here would watch something else")

            def watched(batch):
                seen.append(w.port._fold_order._is_owned())
                return real(batch)

            w.store.group_commit._commit_batch = watched
            try:
                self.assertEqual(w.call("FILE-MKDIR", path="/d2", perm="755"), 0)
            finally:
                w.store.group_commit._commit_batch = real
            self.assertTrue(seen, "non-vacuity: the barrier was never reached")
            self.assertEqual(set(seen), {False},
                             "the fold's ordering is HELD across `fdatasync` (%r) — the "
                             "decide/sync decoupling EP-28C ruled has been re-coupled by "
                             "this landing" % (seen,))
        finally:
            w.close()

    def test_THE_INVERSION_IS_REAL_AND_ITS_REACH_IS_RECORDED(self):
        """THE FINDING, DRIVEN DETERMINISTICALLY RATHER THAN TIMED.

        A fill holding the ordering blocks `_on_append`, which runs inside the store's write
        lock — so a SECOND submitter, with no interest in either, cannot publish until the
        fill lets go. This row does not assert the inversion away: it establishes it, with
        the second submitter's own progress as the observable, so the raise rests on a
        constructed schedule and not on a stopwatch.

        IT IS A BOUNDED WAIT AND THE BOUND IS THE FILL'S OWN DURATION — which is why it is a
        raise and not a re-opening. The snapshot shape's namespace term grows with the
        system forever; this grows with one readdir."""
        w = _World()
        try:
            self.assertEqual(w.call("FILE-MKDIR", path="/d", perm="755"), 0)
            for i in range(40):
                self.assertEqual(w.call("FILE-CREATE", path="/d/f%d" % i, perm="644"), 0)

            gate = threading.Event()
            let_go = threading.Event()
            real_children = w.port.state.children

            def slow_children(path):
                if threading.current_thread().name == "F":
                    gate.set()
                    let_go.wait(FIRES)
                return real_children(path)

            w.port.state.children = slow_children
            second_done = threading.Event()
            box = {}

            def filler():
                box["fill"] = w.port.handle(
                    _wire("FILL-READDIR", cls="FILL", ino=w.ino("/d")), b"")[0]

            def submitter():
                box["submit"] = w.call("FILE-MKDIR", path="/elsewhere", perm="755")
                second_done.set()

            tf = threading.Thread(target=filler, name="F")
            tf.start()
            try:
                self.assertTrue(gate.wait(FIRES),
                                "the fill never reached the hold, so this arm did not run")
                ts = threading.Thread(target=submitter, name="S")
                ts.start()
                stalled = not second_done.wait(1.0)
            finally:
                let_go.set()
                tf.join(FIRES * 2)
                second_done.wait(FIRES)
                ts.join(FIRES * 2)
                w.port.state.children = real_children
            self.assertEqual(box.get("fill"), 0, "the fill did not answer")
            self.assertEqual(box.get("submit"), 0, "the unrelated act did not complete")
            self.assertTrue(
                stalled,
                "an unrelated submitter completed WHILE a fill held the ordering — the "
                "inversion this row records has been closed, and the raise that carries it "
                "is stale rather than merely unrepaired")
        finally:
            w.close()

    def test_A_FILL_TAKES_NO_STORE_LOCK_so_the_order_is_TOTAL_and_no_cycle_exists(self):
        """DEADLOCK FREEDOM, DRIVEN RATHER THAN REASONED. The appender takes the store's
        write lock and then the ordering; a fill takes the ordering and nothing else. One
        direction only, so no cycle — and the whole of that claim is "a fill appends
        nothing", which is checked here on the fill's own path with the ordering held."""
        w = _World()
        try:
            self.assertEqual(w.call("FILE-MKDIR", path="/d", perm="755"), 0)
            self.assertEqual(w.call("FILE-CREATE", path="/d/a", perm="644"), 0)
            # `_thread.RLock` REFUSES ATTRIBUTE ASSIGNMENT, so the lock is REPLACED rather
            # than patched — the store only ever enters it with `with`, which the wrapper
            # serves. A wrapper that bound nothing would report an empty reach list, which
            # is exactly the answer this row wants, so the instrument is proved live below
            # by an act that MUST reach it.
            real_lock = w.store._write_lock
            watched = _RecordingLock(real_lock)
            w.store._write_lock = watched
            try:
                with w.port._fold_order:
                    st, _f, _p = w.port.handle(
                        _wire("FILL-READDIR", cls="FILL", ino=w.ino("/d")), b"")
                    st2, f2, _p2 = w.port.handle(
                        _wire("FILL-LOOKUP", cls="FILL", parent=w.ino("/d"), name="a"), b"")
                during_fills = list(watched.reached)
                self.assertEqual(w.call("FILE-CREATE", path="/d/b", perm="644"), 0)
                after_decide = list(watched.reached)
            finally:
                w.store._write_lock = real_lock
            self.assertEqual((st, st2), (0, 0), "non-vacuity: the fills answered")
            self.assertTrue(f2.get("ino"), "non-vacuity: the lookup answered about a node")
            self.assertTrue(after_decide,
                            "non-vacuity: a DECIDE did not reach the store's write lock "
                            "either, so the wrapper is bound to nothing and the empty list "
                            "below means nothing")
            self.assertEqual(during_fills, [],
                             "a fill reached for the store's write lock while holding the "
                             "ordering (%r) — the lock order is no longer total and the "
                             "two can now be taken in opposite orders" % (during_fills,))
        finally:
            w.close()

    def test_MANY_FILLS_AND_MANY_DECIDES_TOGETHER_ALL_COMPLETE(self):
        """THE POSITIVE SOAK, and it is the row that would catch a deadlock the structural
        rows above cannot see — an ordering taken in two orders somewhere neither row looks
        would hang here rather than fail an assertion, and the join deadline turns a hang
        into a red."""
        w = _World()
        try:
            self.assertEqual(w.call("FILE-MKDIR", path="/d", perm="755"), 0)
            for i in range(10):
                self.assertEqual(w.call("FILE-CREATE", path="/d/f%d" % i, perm="644"), 0)
            dino = w.ino("/d")
            out = {"fills": [], "decides": []}
            lock = threading.Lock()

            def fills(n):
                for i in range(15):
                    st, _f, _p = w.port.handle(
                        _wire("FILL-READDIR", cls="FILL", ino=dino), b"")
                    with lock:
                        out["fills"].append(st)

            def decides(n):
                for i in range(5):
                    st = w.call("FILE-CREATE", path="/d/t%d_%d" % (n, i), perm="644")
                    with lock:
                        out["decides"].append(st)

            threads = ([threading.Thread(target=fills, args=(i,)) for i in range(3)]
                       + [threading.Thread(target=decides, args=(i,)) for i in range(3)])
            for t in threads:
                t.start()
            for t in threads:
                t.join(FIRES * 3)
            alive = [t.name for t in threads if t.is_alive()]
            self.assertEqual(alive, [],
                             "threads did not finish (%r) — fills and decides taken "
                             "together do not complete, which is a deadlock and not a "
                             "slowdown" % (alive,))
            self.assertEqual(len(out["fills"]), 45, "not every fill ran")
            self.assertEqual(len(out["decides"]), 15, "not every decide ran")
            self.assertEqual(set(out["fills"]) | set(out["decides"]), {0},
                             "a call failed under contention: fills %r decides %r"
                             % (sorted(set(out["fills"])), sorted(set(out["decides"]))))
        finally:
            w.close()


class TestWhatTheLANDINGCOVERS(unittest.TestCase):
    """THE TWO MECHANISMS, PINNED. W3 chose among three shapes and this class is what the
    ruled one is measured against: both windows are inside ONE `apply` call, so ordering the
    fill against `_on_append` at whole-call granularity closes both, and ordering it against
    individual fold reads would close neither.

    [RENAMED AT W4 from `TestWhatAnyFixMustCOVER`. The rows are unchanged and neither
    flipped — the shape is now ruled and landed, so "what any fix must cover" describes a
    choice that has been made.]"""

    def test_the_rename_leaves_the_name_absent_from_BOTH_indexes_mid_apply(self):
        """The `names` window — what `FILL-LOOKUP` fell into — and the `kids` window —
        what `FILL-READDIR` fell into — are the SAME window, opened by one `_unbind` and
        closed by the `_bind` that follows it in the same statement."""
        w = _World()
        try:
            for op, kw in SETUP:
                self.assertEqual(w.call(op, **kw), 0)
            self.assertIn("a", w.port.state.kids.get("/d") or {},
                          "non-vacuity: the entry is in the container to begin with")
            self.assertIn("/d/a", w.port.state.names,
                          "non-vacuity: the entry is in the namespace to begin with")
            seen = {}
            real_unbind = w.port.state._unbind

            def watched(path):
                out = real_unbind(path)
                seen["names"] = "/d/a" in w.port.state.names
                seen["kids"] = "a" in (w.port.state.kids.get("/d") or {})
                return out

            w.port.state._unbind = watched
            try:
                self.assertEqual(w.call(MOVER[0], **MOVER[1]), 0)
            finally:
                del w.port.state._unbind
            self.assertEqual(seen, {"names": False, "kids": False},
                             "the rebind's window no longer empties both indexes at once "
                             "(%r) — the two arms fell into ONE window and the landing is "
                             "covering the wrong thing" % (seen,))
            self.assertIn("/d/a", w.port.state.names,
                          "the window never closed, which would be a fold defect and not "
                          "an ordering one")
        finally:
            w.close()

    def test_the_fold_writer_is_reached_from_the_appending_threads_region(self):
        """The one fact from W4e.C's four that this pass's arms actually stand on, driven
        rather than carried: the hold that opened the window ran INSIDE the decide region,
        which is why no region a fill could take would have excluded it."""
        from kernel.gate import decide_region_held
        w = _World()
        try:
            for op, kw in SETUP:
                self.assertEqual(w.call(op, **kw), 0)
            seen = []
            real_unbind = w.port.state._unbind

            def watched(path):
                seen.append(decide_region_held())
                return real_unbind(path)

            w.port.state._unbind = watched
            try:
                self.assertEqual(w.call(MOVER[0], **MOVER[1]), 0)
            finally:
                del w.port.state._unbind
            self.assertTrue(seen, "non-vacuity: the fold's writer was reached at all")
            self.assertEqual(set(seen), {True},
                             "the fold's rebind no longer runs inside the decide region "
                             "(%r), so the composition this pass exhibits has changed"
                             % (seen,))
        finally:
            w.close()

    def test_a_fill_STILL_reads_the_fold_with_the_DECIDE_REGION_not_held(self):
        """THE LANDING'S OWN BOUNDARY, and the thing that separates it from shape (b). The
        fill now takes AN ordering; it must not have taken THE REGION. If it had, a cache
        read would wait on a durability barrier it has no interest in, which is the shape
        the ruling eliminated on the tail measurements."""
        from kernel.gate import decide_region_held
        w = _World()
        try:
            for op, kw in SETUP:
                self.assertEqual(w.call(op, **kw), 0)
            seen = []
            real_lookup = w.port.state.lookup

            def watched(path):
                seen.append(decide_region_held())
                return real_lookup(path)

            w.port.state.lookup = watched
            try:
                status, fields, _p = w.port.handle(
                    _wire("FILL-LOOKUP", cls="FILL", parent=w.ino("/d"), name="a"), b"")
            finally:
                w.port.state.lookup = real_lookup
            self.assertEqual(status, 0, "non-vacuity: the fill answered")
            self.assertTrue(fields.get("ino"), "non-vacuity: it answered about a node")
            self.assertTrue(seen, "non-vacuity: it read the fold at all")
            self.assertEqual(set(seen), {False},
                             "a fill now reads the fold INSIDE the decide region (%r) — the "
                             "landed shape has become shape (b), which the ruling "
                             "eliminated" % (seen,))
        finally:
            w.close()


class TestTheChannelStillAdmitsONECaller(unittest.TestCase):
    """WHY THE EXHIBITION WAS LATENT AND NOT A LIVE DEFECT, RE-CHECKED HERE RATHER THAN
    CITED. The arms above drive `port.handle` from two threads; the real transport does
    not, because `govos_call_lock` admits one caller at a time. That lowering is exactly
    what AMENDMENT 11.2 orders removed, which is what makes this pass W4e.C's PRECONDITION
    rather than its consequence. §A64 binds the structural walk, so both near-misses are
    driven."""

    NEAR_MISS_SHOULD_MATCH = '''
static DEFINE_MUTEX(govos_call_lock);
static int govos_call(const struct govos_msg *m, struct govos_reply *out)
{
	mutex_lock( &govos_call_lock );
	mutex_unlock(&govos_call_lock);
	return 0;
}
'''

    NEAR_MISS_SHOULD_NOT_MATCH = '''
/* A comment naming govos_call_lock beside a DIFFERENT mutex actually being taken. */
static DEFINE_MUTEX(govos_chan_mutex);
static int govos_call(const struct govos_msg *m, struct govos_reply *out)
{
	mutex_lock(&govos_chan_mutex);
	return 0;
}
'''

    def _lowering_present(self, src):
        declared = re.search(r"DEFINE_MUTEX\(\s*govos_call_lock\s*\)", src) is not None
        taken = re.search(r"mutex_lock\(\s*&\s*govos_call_lock\s*\)", src) is not None
        return declared and taken

    def test_NEAR_MISS_a_lowering_spelled_differently_is_still_seen(self):
        self.assertTrue(self._lowering_present(self.NEAR_MISS_SHOULD_MATCH),
                        "the check reads one spelling rather than the construct")

    def test_NEAR_MISS_a_mere_mention_beside_another_mutex_is_not_the_lowering(self):
        self.assertFalse(self._lowering_present(self.NEAR_MISS_SHOULD_NOT_MATCH),
                         "a comment naming the lock read as the lowering being in place")

    def test_the_one_caller_lowering_is_still_in_place(self):
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            src = fh.read()
        self.assertTrue(self._lowering_present(src),
                        "the one-caller lowering is gone, so the tear this file exhibits "
                        "is reachable through the real transport and is no longer latent")

    def test_the_wire_carries_the_new_field_ADDITIVELY(self):
        """THE ONE THING THE LANDING PUTS ON THE WIRE, CHECKED AGAINST THE MODULE'S OWN
        READER RATHER THAN ASSUMED. `at_seq` is a new reply field and `govosfs.c` is out of
        this pass's fence, so the landing is only user-space if the module's header parser
        SKIPS keys it does not know. It does: `rep_field` scans for its key and steps over
        the rest. Read here as a structural row because "the module ignores it" is a claim
        about another file, and this file's landing depends on it."""
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("rep_field", src,
                      "the module's reply-field reader is no longer called `rep_field`, so "
                      "this row is not reading the parser the landing depends on")
        self.assertNotIn("at_seq", src,
                         "the module now names `at_seq` itself, so the field is no longer "
                         "additive and this pass has become a kernel-side change")

    # A ROW ASSERTING "THIS PASS WROTE NO CHANNEL LINE" VIA `git status` STOOD HERE AND WAS
    # REMOVED BEFORE IT LANDED. Autosync commits this tree every two minutes, so that path
    # is clean whether or not a line was written, and the clause could not fail.
    #
    # THE LOWERING ROW ABOVE *IS* REPEATED FROM `tests/test_ep28c_w4e_c.py`, DELIBERATELY:
    # this file's central claim is that the tear was LATENT rather than live, and that claim
    # rests entirely on the transport admitting one caller. A conclusion resting on another
    # file's row is a conclusion nobody re-checks.


class TestTheTRIPWIRES_RE_DERIVATION_IS_CITED_AND_RESOLVED(unittest.TestCase):
    """THE FENCE'S FIRST CONDITION, MADE MECHANICAL — EP-28R W4, mentor-ruled 2026-08-07.

    `tests/test_ep28c_w4e_c.py`'s `test_the_PORT_ITSELF_TAKES_NO_LOCK` was not a stale
    assertion. It was a TRIPWIRE and it fired exactly as designed: its own message said the
    composition it watched had changed and its consequence must be RE-DERIVED. The ruling
    that let it be repointed carried two conditions — the repoint lands only with the
    re-derivation CITED, and the row is RENAMED and not only flipped.

    A CITATION IN A DOCSTRING IS PROSE, AND PROSE ROTS SILENTLY. That is the whole reason
    this class exists rather than the entry simply claiming the citation was made: the
    repointed row names four rows in THIS file as its derivation, and these rows RESOLVE
    every one of them. A citation naming a row nobody wrote, or naming one that later gets
    renamed away, reds here — so the tripwire cannot be silenced by a sentence.

    WHERE THIS SITS RELATIVE TO THE ROWS IT CHECKS: it asserts nothing about the ordering
    itself. `TestTheINVERSION` derives the consequence; this class only holds that the
    repoint POINTS at that derivation and that the derivation is still there."""

    W4E_C = os.path.join(REPO, "tests", "test_ep28c_w4e_c.py")
    REPOINTED = "test_the_port_takes_EXACTLY_ONE_ORDERING_and_its_CONSEQUENCE_IS_RE_DERIVED"
    RETIRED = "test_the_PORT_ITSELF_TAKES_NO_LOCK"

    #: §A64 on the citation extractor. One docstring whose citation block should be read;
    #: one that should NOT — a row name written in running prose is a MENTION, not a
    #: citation, and reading mentions would make the resolve check fire on the retired
    #: name this very docstring has to be free to discuss.
    NEAR_MISS_SHOULD_CITE = '''
class C:
    def test_x(self):
        """Derivation, by name:
          - test_the_ORDERING_IS_NOT_HELD_ACROSS_fdatasync
        """
'''
    NEAR_MISS_SHOULD_NOT_CITE = '''
class C:
    def test_x(self):
        """What stood here was test_the_PORT_ITSELF_TAKES_NO_LOCK and it is gone; see also
        test_a_row_nobody_ever_wrote, discussed in running prose and cited by nobody."""
'''

    def _src(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def _rows_defined_in(self, src):
        return {n.name for n in ast.walk(ast.parse(src))
                if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}

    def _cited_rows(self, src, row_name):
        """Every row name `row_name`'s docstring CITES, and None if the row is absent.

        A CITATION IS A BULLETED LINE, not any occurrence of the token. The distinction is
        load-bearing rather than tidy: the repointed row's docstring must be able to NAME
        the retired row it replaced, in prose, without that mention being resolved as a
        citation to a row that no longer exists. `None` for an absent row separates "the
        row was renamed away" from "the row cites nothing" — two failures a bare empty
        list would report identically."""
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.FunctionDef) and n.name == row_name:
                return re.findall(r"^\s*-\s+(test_[A-Za-z0-9_]+)\s*$",
                                  ast.get_docstring(n) or "", re.M)
        return None

    def test_NEAR_MISS_a_bulleted_derivation_name_IS_read_as_a_citation(self):
        self.assertEqual(self._cited_rows(self.NEAR_MISS_SHOULD_CITE, "test_x"),
                         ["test_the_ORDERING_IS_NOT_HELD_ACROSS_fdatasync"],
                         "the extractor cannot see a citation in the form the repoint "
                         "actually uses, so the emptiness it reports proves nothing")

    def test_NEAR_MISS_a_row_name_MENTIONED_in_prose_is_not_a_citation(self):
        self.assertEqual(self._cited_rows(self.NEAR_MISS_SHOULD_NOT_CITE, "test_x"), [],
                         "a row name mentioned in running prose was read as a citation, so "
                         "the repoint could not name the tripwire it replaced without this "
                         "class demanding that retired row still exist")

    def test_NEAR_MISS_an_absent_row_reports_ABSENT_and_not_CITES_NOTHING(self):
        self.assertIsNone(self._cited_rows(self.NEAR_MISS_SHOULD_CITE, "test_gone"))

    def test_the_repointed_tripwire_CITES_and_EVERY_CITED_ROW_RESOLVES_HERE(self):
        cited = self._cited_rows(self._src(self.W4E_C), self.REPOINTED)
        self.assertIsNotNone(cited,
                             "the repointed row is not in `tests/test_ep28c_w4e_c.py` under "
                             "the name this class was told it would carry — the tripwire's "
                             "discharge cannot be located, so it cannot be checked")
        # NON-VACUITY: a repoint that cited nothing would pass an "every citation resolves"
        # check trivially, which is exactly the silencing the ruling forbids.
        self.assertGreaterEqual(len(cited), 3,
                                "the repoint cites fewer rows than the re-derivation it was "
                                "required to record: %r" % (cited,))
        here = self._rows_defined_in(self._src(os.path.abspath(__file__)))
        missing = sorted(set(cited) - here)
        self.assertEqual(missing, [],
                         "the tripwire's repoint cites a derivation that is not in this "
                         "file: %r. A citation that does not resolve is prose, and a "
                         "tripwire silenced by prose is worse than the composition it was "
                         "watching." % (missing,))

    def test_CAN_FAIL_a_citation_naming_a_row_NOBODY_WROTE_does_NOT_resolve(self):
        """The row above computes `set(cited) - here` and asserts it is empty. An empty
        difference is exactly what a broken extractor and a vacuous world both produce, so
        the difference is shown here to be capable of being non-empty against the SAME
        resolved set the real row uses."""
        here = self._rows_defined_in(self._src(os.path.abspath(__file__)))
        fabricated = self._cited_rows(self.NEAR_MISS_SHOULD_CITE.replace(
            "test_the_ORDERING_IS_NOT_HELD_ACROSS_fdatasync",
            "test_the_ORDERING_IS_NOT_HELD_ACROSS_fdatasyncc"), "test_x")
        self.assertEqual(sorted(set(fabricated) - here),
                         ["test_the_ORDERING_IS_NOT_HELD_ACROSS_fdatasyncc"],
                         "a cited row that does not exist resolves anyway, so the real "
                         "row's empty difference means nothing")
        # AND THE SAME COMPUTATION IS SATISFIED BY A NAME THAT DOES EXIST — both directions,
        # one instrument.
        self.assertEqual(sorted(set(self._cited_rows(
            self.NEAR_MISS_SHOULD_CITE, "test_x")) - here), [])

    def test_the_tripwire_was_RENAMED_and_not_only_FLIPPED(self):
        """Read off the DEFINED ROWS and not off the text, because the repointed row's own
        docstring quotes the retired name — it has to, to say what it replaced — and a
        text search would find it there and report a rename that did not happen."""
        defined = self._rows_defined_in(self._src(self.W4E_C))
        self.assertIn(self.REPOINTED, defined)
        self.assertNotIn(self.RETIRED, defined,
                         "the row still carries the name of the property the ruling "
                         "reversed, which is the `AppendNothing` shape returning")

    #: §A64 on the binding walk. One source where a SECOND primitive is constructed under a
    #: different attribute — must be seen. One where the SAME ordering is entered and
    #: acquired repeatedly — must NOT be counted twice: a use is not a construction.
    NEAR_MISS_TWO_PRIMITIVES = '''
import threading
class KernelPort:
    def __init__(self):
        self._fold_order = threading.RLock()
        self._other = threading.Lock()
'''
    NEAR_MISS_ONE_PRIMITIVE_USED_OFTEN = '''
import threading
class KernelPort:
    def __init__(self):
        self._fold_order = threading.RLock()
    def a(self):
        with self._fold_order:
            pass
    def b(self):
        self._fold_order.acquire()
        with self._fold_order:
            pass
'''

    def _primitive_bindings(self, src):
        """Every mutual-exclusion primitive this source CONSTRUCTS, with what it is bound to.

        Keyed on the CONSTRUCT, like the tripwire's own instrument: entering one with `with`
        or calling `.acquire()` is a USE. The count of primitives is the thing a lock ORDER
        is derived over, and a use adds none."""
        tree = ast.parse(src)
        kinds = ("Lock", "RLock", "Semaphore", "Condition", "BoundedSemaphore")
        bound, seen = [], set()
        for n in ast.walk(tree):
            if not isinstance(n, ast.Assign):
                continue
            v = n.value
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) \
                    and v.func.attr in kinds:
                seen.add(id(v))
                for t in n.targets:
                    bound.append(((t.attr if isinstance(t, ast.Attribute)
                                   else getattr(t, "id", "<expr>")), v.func.attr))
        # A PRIMITIVE CONSTRUCTED AND NEVER BOUND IS STILL ONE. Reporting only assignments
        # would let a lock built inline vanish from a walk whose whole job is to count them.
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in kinds and id(n) not in seen:
                bound.append(("<unbound>", n.func.attr))
        return sorted(bound)

    def test_NEAR_MISS_a_SECOND_primitive_bound_elsewhere_is_SEEN(self):
        self.assertEqual(self._primitive_bindings(self.NEAR_MISS_TWO_PRIMITIVES),
                         [("_fold_order", "RLock"), ("_other", "Lock")],
                         "the walk cannot see a second primitive, so what it reports about "
                         "the port having exactly one proves nothing")

    def test_NEAR_MISS_the_SAME_ordering_entered_often_is_not_a_second_primitive(self):
        self.assertEqual(self._primitive_bindings(self.NEAR_MISS_ONE_PRIMITIVE_USED_OFTEN),
                         [("_fold_order", "RLock")],
                         "entering or acquiring one ordering was counted as constructing "
                         "another, so the walk is reading uses and not constructions")

    def test_the_ports_ONE_primitive_is_BOUND_TO_THE_FOLD_ORDERING(self):
        """WHICH lock, not how many — the half `_lock_constructs` cannot answer.

        The repointed tripwire asserts the port constructs exactly one primitive and that it
        is re-entrant. It reads a flat list of construct names, so it would be equally happy
        with one `RLock` bound to something else entirely. This row names the binding, which
        is what the citation's derivation is actually ABOUT: `TestTheINVERSION` proves things
        about `_fold_order` specifically, and if the port's one primitive stopped being that
        object those proofs would be about nothing."""
        src = self._src(os.path.join(REPO, "src", "bridge", "kernel_port.py"))
        self.assertEqual(self._primitive_bindings(src), [("_fold_order", "RLock")],
                         "the port's ordering is not one re-entrant primitive bound to "
                         "`_fold_order` — either a second lock exists, whose ORDER against "
                         "this one nobody has derived, or the derivation the tripwire's "
                         "repoint cites is no longer about the object the port uses")
        # AND THE ROWS THAT DERIVE IT REACH THE SAME OBJECT — asserted here rather than
        # assumed, because a structural row about a source file and a driven row about a
        # live port are two subjects until something says they are one.
        w = _World()
        try:
            self.assertIsInstance(w.port._fold_order, type(threading.RLock()))
        finally:
            w.close()


if __name__ == "__main__":
    unittest.main()
