"""gov-os kernel — GROUP COMMIT: many submitters, one appender (EP-28C W1).

WHY THIS IS ITS OWN MODULE, stated because the EP made it a judgement and asked for the
answer. `store.py` owns WHAT an append is: the envelope, the minting, the barrier, the
round-trip law. This file owns WHEN a batch closes and WHICH thread is the appender —
scheduling questions with their own invariants and their own failure modes. Kept together
they would read as one thing and be two, and `T-ONE-APPENDER`'s structural guard would have
no single subject to point at. Kept apart, the guard is one sentence: every append issues
from `GroupCommit._drain`, and there is exactly one write site in the store it calls.

THE RULING THIS LOWERS (design/36 ADDENDUM L, owner-corrected 2026-07-29): **the store has
ONE APPENDER; the channel may admit MANY SUBMITTERS in flight.** "One caller at a time" in
the module was a LOWERING of the one-writer law, not the law. Many submitters queueing into
one appender create no second writer, so S5 — multiple APPENDERS, federation — is untouched
and `design/21` stays dormant.

THE FOUR INVARIANTS, owner-ruled, not re-openable, and each one visible in the code below:

1. NO REPLY RELEASES BEFORE THE SYNC COVERING ITS RECORD. `_commit` sets no submission's
   `done` until the store's `commit_batch` has returned, and that function returns only
   after its `fdatasync`. A submitter's call returns when ITS record is durable, never when
   its record is queued. This is the whole safety property; everything else here is speed.
2. A BATCH CLOSES ON QUEUE-EMPTY OR TIMEOUT, WHICHEVER COMES FIRST. `_take_batch` closes on
   an empty queue without consulting the clock, so a lone submitter pays nothing for the
   machinery, and it closes on the window when the queue keeps refilling, so no submitter
   waits on traffic it cannot see.
3. BATCHING SYNCS IS NEVER COALESCING RECORDS. Nothing in this file touches a draft. The
   batch is a list of submissions and the store appends each one individually; one
   `fdatasync` covering N individually-appended records is a barrier over N records, never
   one record standing for N acts.
4. THE ECHO-RETIRE BUFFER IS PIPELINE, NEVER AN EFFECT-LICENSE (design/38 §1 as its
   ADDENDUM 1 rules). A submission sitting in this queue licenses nothing. It has exactly
   one consumer — the appender — and one comparison — the echo check in the store. No read
   path can reach it; no verdict can be hung on it.

THE SECOND NAMED WRONG REFERENCE, REFUSED BY SHAPE: THE PERSISTENT QUEUE. Making this queue
durable "so nothing is lost on crash" creates a second place truth lives, which is
`design/38` §1's fence broken from the other side. **In-flight state here is PROCESS-LOCAL
MECHANISM, lost on crash BY DESIGN.** Crash honesty comes from invariant 1, not from
persistence: an unreplied submission may or may not exist, its caller was never told
otherwise, and re-asking at the current head is the lawful remedy. There is no path in this
file that writes anything anywhere, and that absence is asserted by a test.

LEADER-AND-FOLLOWER, AND WHY THERE IS NO BACKGROUND THREAD. A submitter enqueues, then tries
to take the appender role. Whoever takes it drains for everybody and releases every reply;
everybody else waits on its own reply. So the appender is a ROLE rather than a thread, the
single-caller case is today's code path plus one uncontended lock, and a store that nobody
appends to starts nothing and costs nothing. A background appender thread per store would
have been the obvious shape and it is the wrong one: the suite founds thousands of
disposable worlds, and a lifecycle nobody can see is a lifecycle nobody shuts down.
"""

import collections
import os
import threading
import time


class BatchFailed(RuntimeError):
    """The covering sync did not happen, so nothing in this batch is durable and no reply in
    it may be released as a success. Raised to EVERY member: a barrier that covered N records
    fails for all N or for none, and reporting otherwise would be a record about durability
    that is not true."""


#: THE WIDTH CAP — ENGINE CALIBRATION, NOT LAW-DATA, and the distinction is derived rather
#: than assumed. This value changes no verdict, no citation, no record content and no order;
#: it changes only the latency shape. It carries no governance content (I5 untouched), which
#: is exactly the contrast with EP-27's delivery lanes — those ordered LAW delivery and were
#: rightly recorded policy. So it lives here as a named constant, declared beside the figures
#: taken under it in `planning/build/MEASUREMENTS.md`.
#:
#: 16 because that is the top of the band `design/36` ADDENDUM L measured (5.6x at batch 8,
#: 13.5x at batch 16). Past it the amortisation curve is flat and the tail latency of the
#: last submitter in a batch keeps growing, so a wider cap buys the record nothing and costs
#: the slowest caller.
BATCH_WIDTH_CAP = 16

#: THE WINDOW — the same class of value, same reasoning. 2 ms because ADDENDUM L's floor is
#: 1.30-2.31 ms per gated act on this substrate: a batch's members arrive DURING the previous
#: batch's sync, not after it, so a window longer than one sync adds latency without adding
#: members. It is the bound on how long the appender will keep accumulating while the queue
#: keeps refilling — never a delay a lone submitter pays (invariant 2).
BATCH_WINDOW_S = 0.002

#: THE DETERMINISTIC TEST OVERRIDE, declared here and in this EP's log entry so a verifier can
#: run the suite at both widths verbatim:
#:
#:     GOVOS_COMMIT_WIDTH=1   python3 -m unittest discover -s tests -p 'test_*.py'
#:     GOVOS_COMMIT_WINDOW_MS=<float>
#:
#: An unparseable value is a REFUSAL and never a silent fall-back to the shipped default
#: (ST-A): a run that believed it was at width 1 and was not would report the shipped width's
#: result under the override's name, which is the flattering wrong answer this estate keeps
#: catching in other clothes.
WIDTH_ENV = "GOVOS_COMMIT_WIDTH"
WINDOW_ENV = "GOVOS_COMMIT_WINDOW_MS"


def _calibration():
    """The shipped constants, or the declared override. Read once per store."""
    width, window = BATCH_WIDTH_CAP, BATCH_WINDOW_S
    raw = os.environ.get(WIDTH_ENV)
    if raw is not None:
        try:
            width = int(raw)
        except ValueError:
            raise ValueError("%s=%r is not an integer — a calibration override that cannot "
                             "be read REFUSES rather than falling back to the shipped width, "
                             "because a run reporting the shipped width under the override's "
                             "name is worse than no run" % (WIDTH_ENV, raw))
        if width < 1:
            raise ValueError("%s must be at least 1 (got %d): a batch has members or it is "
                             "not a batch" % (WIDTH_ENV, width))
    raw = os.environ.get(WINDOW_ENV)
    if raw is not None:
        try:
            window = float(raw) / 1000.0
        except ValueError:
            raise ValueError("%s=%r is not a number of milliseconds" % (WINDOW_ENV, raw))
        if window < 0:
            raise ValueError("%s must not be negative (got %r)" % (WINDOW_ENV, raw))
    return width, window


class Submission:
    """ONE SUBMITTER'S IN-FLIGHT ITEM. Process-local, lost on crash by design.

    It holds the draft on its way in and the appended record on its way out, and its `done`
    event is the reply. Nothing else may read it: it is pipeline state with exactly one
    consumer (the appender) and one comparison (the store's echo check). An intent sitting
    here licenses no effect — invariant 4, and `design/38` ADDENDUM 1's ruling that the
    echo-retire buffer arrives HERE as pipeline and never as an effect-license.
    """

    __slots__ = ("draft", "record", "echo", "error", "done")

    def __init__(self, draft):
        self.draft = draft
        #: Set by `_publish_one` in the DECIDING thread, before this submission ever reaches
        #: the queue (EP-28G W1). What sits in the queue is therefore a record awaiting its
        #: barrier, not an intent awaiting an append — which is why a decide entering after it
        #: reads a fold that contains it, and why nothing here is a second source of truth: it
        #: points at a record that already lives in the one source.
        self.record = None
        #: The appender's content hash over what it actually wrote, for exactly the fields
        #: this draft stated. The submitter compares it against its own draft on the far side
        #: of the covering sync — `design/38` §1's retire-on-exact-match, which ADDENDUM 1
        #: rules arrives here as pipeline rather than as an effect-license.
        self.echo = None
        self.error = None
        self.done = threading.Event()


class GroupCommit:
    """The queue and the one appender loop.

    `commit_batch(batch)` is supplied by the store: it appends every member individually,
    issues ONE covering `fdatasync`, and returns. It is called from `_drain` and from nowhere
    else, which is what makes `T-ONE-APPENDER` a structural claim rather than a hope.
    """

    #: How long a follower waits on its own reply before trying the appender role again.
    #: It exists to close one narrow race and nothing else: a submitter can enqueue in the
    #: instant between the leader finding the queue empty and the leader releasing the role,
    #: and would then have nobody to drain it. Bounded, small, and the only cost is that one
    #: submitter's latency in that instant.
    FOLLOWER_POLL_S = 0.002

    def __init__(self, commit_batch, verify_echo=None, publish_one=None,
                 publishing_here=None):
        self._commit_batch = commit_batch
        #: `publish_one(submission)` is the store's DECIDING-THREAD half (EP-28G W1): mint,
        #: write, flush, publish into the record, notify. It runs before the submission is
        #: queued. Absent only in the bare-queue tests, where the queue is exercised without a
        #: store behind it.
        self._publish_one = publish_one
        #: `publishing_here()` answers whether THIS thread is already inside a publish — a
        #: listener that appends is, and its record rides the enclosing act's barrier. ONE
        #: counter for that fact and it lives in the store, on its write path — two copies of
        #: one fact drift, which this estate has now found four times in a week.
        self._publishing_here = publishing_here or (lambda: False)
        #: Per-thread: the submissions this thread has published and not yet awaited. A list
        #: rather than one, because an act publishes more than one record — the mirror's, the
        #: sweep's overturns — and every one of them owes its echo check.
        self._pending = threading.local()
        #: `verify_echo(submission)` is the SUBMITTER's side of the echo-retire discipline:
        #: it recomputes the hash from the draft this thread still holds and refuses loud on
        #: any difference. It runs after the covering sync and after the reply is released,
        #: because it confirms a record that already exists — it is not a gate the record
        #: passes through. Supplied by the store; absent only in the bare-queue tests.
        self._verify_echo = verify_echo
        self._queue = collections.deque()
        self._qlock = threading.Lock()
        self._appender = threading.Lock()
        self._leader = None                  # the thread ident currently holding the role
        self.width, self.window_s = _calibration()

        # THE TEST OVERRIDES. `hold_open`, when set to an unset Event, makes the accumulate
        # loop wait on the window rather than closing on an empty queue — it DRIVES the
        # window's own mechanism rather than bypassing it, which is what makes the red world
        # it exhibits a statement about this code. The two `closes_on_*` switches exist so a
        # red world can disable exactly one clause of invariant 2 and leave the other green.
        self.hold_open = None
        self.closes_on_empty = True
        self.closes_on_timeout = True

        # OBSERVABLE COUNTABLES. Every property this EP asserts about the loop is asserted on
        # one of these, never on a duration — a duration is a fact about the box.
        self.batches = 0
        self.members = 0
        self.touched = 0                     # entries the drain examined: K12's countable
        self.largest_batch = 0
        self.closed_on_empty = 0
        self.closed_on_timeout = 0
        self.closed_on_width = 0

    # ---- the submitter's side -------------------------------------------------------
    #
    # THE TWO HALVES, SEPARABLE (EP-28G W1). `submit` used to be one call that enqueued a
    # draft and returned when it was durable. It is now `publish` then `await_pending`, and
    # the pair is composed in `store._append`, which still offers the pre-split contract to
    # every caller that wants it. IT IS COMPOSED THERE AND NOT HERE ON PURPOSE: `_append`
    # carries the H3 check — a governed record appended without a cited rule fails loud — and
    # a convenience wrapper on this side would be a second route to the record that skips it.
    # A one-line wrapper worth a bypass is not worth having.
    def publish(self, draft):
        """THE FIRST HALF: append the record in THIS thread and return before it is durable.

        WHY IT IS THIS THREAD'S WORK RATHER THAN THE APPENDER'S, derived rather than chosen.
        The decide region must not end before the record is visible, or the next decide reads
        a world without its predecessor; and it must not extend across the barrier, or it is
        the big lock. If publication stayed in the appender, a deciding thread could only
        learn its record was published by BECOMING the appender — and the appender publishes
        and syncs in one call, so the region would span the sync — or by waiting for another
        thread to publish it, which cannot happen while it holds the region. Releasing the
        region from inside the appender at each member's publish looks correct and closes
        EVERY batch at width 1: the next decider cannot enqueue until the release, and the
        release happens after `_take_batch` already closed the batch. That shape passes every
        row in this estate except `T-BATCHING-POSSIBLE`, which is why the demoted existential
        was worth keeping.

        So the record is published here, and what accumulates in the queue is records waiting
        for a barrier. Records accumulate WHILE a barrier is in flight, which is the classic
        shape and the one ADDENDUM L's 5.6x/13.5x model already assumes."""
        sub = Submission(draft)
        pending = getattr(self._pending, "subs", None)
        if pending is None:
            pending = self._pending.subs = []
        if self._publish_one is not None:
            self._publish_one(sub)
        if sub.error is not None:
            raise sub.error
        pending.append(sub)
        return sub

    def await_pending(self):
        """THE SECOND HALF: block until everything this thread published is durable, then
        verify every echo. This is the durability wait and it runs with no region held.

        ONE WAIT COVERS THE WHOLE ACT. It waits on the LAST submission this thread published
        and every earlier one is covered by prefix durability — `fdatasync` makes the file's
        written data durable rather than a byte range, and this thread's records are
        contiguous because the region held for the act's whole span. Every one of them is
        still echo-checked: a mutated append must never retire an intent silently, and the
        check is per record even where the barrier is not.

        IT IS A NO-OP WHEN THE CALLER IS NESTED, and the two nestings are different. Inside a
        PUBLISH: a listener appended — the dual-audit mirror does — and its record rides the
        enclosing act's barrier, exactly as a nested submission rode the outer batch's sync
        before the split. Inside the DECIDE REGION: the region's outermost exit owns the wait,
        and taking it here would be the big lock arriving through a side door. Expressed once,
        here, because every append in the system passes through this call."""
        if self._publishing_here():
            return self._last_record()
        from .gate import decide_region_held               # the region's home is `gate.py`
        if decide_region_held():
            return self._last_record()
        pending = getattr(self._pending, "subs", None)
        if not pending:
            return None
        self._pending.subs = []
        sub = pending[-1]

        with self._qlock:
            self._queue.append(sub)

        while not sub.done.is_set():
            if self._appender.acquire(blocking=False):
                self._leader = threading.get_ident()
                try:
                    self._drain()
                finally:
                    self._leader = None
                    self._appender.release()
            else:
                sub.done.wait(self.FOLLOWER_POLL_S)

        if sub.error is not None:
            raise sub.error
        if self._verify_echo is not None:
            for s in pending:
                self._verify_echo(s)
        return sub.record

    def _last_record(self):
        pending = getattr(self._pending, "subs", None)
        return pending[-1].record if pending else None

    # ---- the one appender loop ------------------------------------------------------
    def _drain(self):
        """THE LOOP. Every append in this system issues from here. It takes a batch, commits
        it, and takes the next one until the queue is empty — so a submitter that arrives
        while this thread is committing is drained by this thread rather than waiting for the
        role to change hands."""
        while True:
            batch = self._take_batch()
            if not batch:
                return
            self._commit(batch)

    def _take_batch(self):
        """Close on QUEUE-EMPTY or TIMEOUT, whichever comes first (invariant 2), capped at the
        width. The empty check comes BEFORE any clock is consulted, which is the immediate-
        close clause: a batch of one closes at once and the single-caller case pays nothing."""
        with self._qlock:
            if not self._queue:
                return []
            batch = [self._queue.popleft()]
        self.touched += 1
        deadline = time.monotonic() + self.window_s
        while len(batch) < self.width:
            with self._qlock:
                if self._queue:
                    batch.append(self._queue.popleft())
                    self.touched += 1
                    continue
            if self.closes_on_timeout and time.monotonic() >= deadline:
                self.closed_on_timeout += 1
                return batch
            if self.hold_open is not None and not self.hold_open.is_set():
                # The test override, waiting on the window it is holding open rather than on
                # a queue that will not fill.
                self.hold_open.wait(0.001)
                continue
            if self.closes_on_empty:
                self.closed_on_empty += 1
                return batch
            if not self.closes_on_timeout:
                # Both closes disabled: this is a red world and it is the world where a held
                # batch never closes. Yielding keeps it observable instead of spinning hot.
                time.sleep(0.001)
        self.closed_on_width += 1
        return batch

    def _commit(self, batch):
        """Commit one batch and release its replies — IN THAT ORDER, which is invariant 1.

        `commit_batch` returns only after the covering `fdatasync`. Not one `done` is set
        before it returns, and every path out of it sets every `done` exactly once, because a
        submitter whose reply is never released is a caller wedged forever — the too-wedged
        direction, which this EP tests alongside the too-weak one."""
        self.batches += 1
        self.members += len(batch)
        self.largest_batch = max(self.largest_batch, len(batch))
        try:
            self._commit_batch(batch)
        except BaseException as exc:                          # noqa: BLE001 — re-raised below
            failure = BatchFailed(
                "the covering sync for a batch of %d did not complete (%s: %s), so no record "
                "in it is durable and no reply in it may be released as a success"
                % (len(batch), type(exc).__name__, exc))
            failure.__cause__ = exc
            # EVERY MEMBER FAILS, INCLUDING THE ONES THAT HAD A RECORD. A member whose record
            # was minted and published but whose covering sync did not complete is NOT
            # durable, and releasing it as a success would be a reply about an act that may
            # never have happened — the async-ack trap arriving through the error path
            # instead of through the happy one.
            for s in batch:
                s.record = None
                s.error = failure
        finally:
            # RELEASED AFTER THE SYNC, ALWAYS, AND EXACTLY ONCE. A member that came back with
            # neither a record nor an error is itself a defect and is reported as one rather
            # than left to hang.
            for s in batch:
                if s.record is None and s.error is None:
                    s.error = BatchFailed(
                        "the appender returned without a record and without an error for a "
                        "submission — the loop lost a member")
                s.done.set()
