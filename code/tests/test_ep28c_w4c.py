# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28C W4c — T-FINALIZER-CLOSES-NO-STRANGER.

THE ROOT, IN ONE SENTENCE, and it is the sentence EP-28H's evidence upgrade wrote: **A RAW
DESCRIPTOR NUMBER IS NOT A STABLE IDENTITY.**

THE DEFECT (EP-28F raise 3; intaken here by EP-28C AMENDMENT 4 §4.2). `EventStore` registers
a `weakref.finalize` that closes its held record descriptor. For an ABANDONED store that runs
at an arbitrary later garbage-collection point, in whatever code happens to be executing then
— and it used to close the descriptor NUMBER unconditionally. If anything else in the process
had already closed that number, the kernel is free to hand it to the next `open`, and the
late close then closes A DIFFERENT FILE'S descriptor.

THIS IS NOT A CONSTRUCTED HAZARD. The conformance instrument's `files.close` row exists
precisely to close a descriptor number and observe the answer, and `[Errno 9]` from this
family has already reached product code at `src/founding/install.py:72` in full-suite runs.

THE CAP, HELD HARD AND STATED WHERE IT CANNOT BE MISSED (AMENDMENT 4 §4.2). EP-28H's row 11
shares this ROOT and is NOT this item's discharge. Row 11 is same-process, same-store, a
constructed sequence; this is cross-file, at an arbitrary collection point. **Same root,
different exhibition.** Row 11 going green says nothing about this row, and after EP-28H a
green suite and an absent `[Errno 9]` are not evidence about this item either — that pass
removed the OCCASION without touching the MECHANISM.

THE STANDING DIVERGENCE LAW IS WHAT THIS BATTERY OWES: a world where the fallback-shaped
behaviour and the correct behaviour DIFFER, with the two outcomes forced apart. It is here as
`test_the_two_behaviours_are_driven_apart_in_one_world` — one stolen number, two arms, one
stranger left open and one stranger closed.
"""

import gc
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from kernel import store as store_mod                            # noqa: E402
from kernel.store import EventStore                              # noqa: E402


def _draft(i=0):
    return {"actor": "SYSTEM", "action": "probe", "rule_cited": "M1-OBSERVATION",
            "object": "w4c-%d" % i}


class _Theft:
    """ONE WORLD, BUILT THE SAME WAY FOR BOTH ARMS: a store holding a descriptor, that number
    closed from outside it, and a different file opened onto the freed number.

    The theft is the ordinary shape rather than an exotic one — `os.close` on a number, which
    is what any component releasing a descriptor it holds does, and what the conformance row's
    own subject is.
    """

    def __init__(self, case):
        d = tempfile.mkdtemp(prefix="w4c-store-")
        self.store = EventStore(os.path.join(d, "record.jsonl"), require_rule_cited=False)
        self.store._append(_draft())                 # opens and holds the descriptor
        self.fd = self.store._fh.fileno()
        self.store_ident = _ident(self.fd)

        os.close(self.fd)                            # THE THEFT: the number is now free

        # The stranger takes the freed number. POSIX hands out the lowest free descriptor, so
        # this is deterministic; it is asserted rather than assumed, because a world that did
        # not actually reuse the number would make both arms trivially pass.
        self.stranger_path = os.path.join(d, "stranger.txt")
        self.stranger_fd = os.open(self.stranger_path, os.O_WRONLY | os.O_CREAT, 0o600)
        case.assertEqual(self.stranger_fd, self.fd,
                         "the stranger did not take the freed number, so this world does not "
                         "exhibit the hazard and neither arm proves anything")
        self.stranger_ident = _ident(self.stranger_fd)
        case.assertNotEqual(self.stranger_ident, self.store_ident,
                            "the stranger is the same file as the store's record — the two "
                            "outcomes would be indistinguishable")

    def stranger_still_open(self):
        return _ident(self.stranger_fd) == self.stranger_ident

    def cleanup(self):
        try:
            os.close(self.stranger_fd)
        except OSError:
            pass


def _ident(fd):
    st = os.fstat(fd)
    return (st.st_dev, st.st_ino)


class TestTheFinalizerClosesNoStranger(unittest.TestCase):

    def test_the_two_behaviours_are_driven_apart_in_one_world(self):
        """THE DIVERGENCE, WITH THE OUTCOMES FORCED APART. Both arms run the SAME code path
        the true positive runs (§A42): the shipped arm calls the store's real finalizer, and
        the fallback-shaped arm performs the exact act the pre-fix helper performed —
        `fh.close()` on the held wrapper, unconditionally.

        A row that only asserted the good outcome would pass in a world where the stranger
        happened to survive for some other reason. Driving both says WHICH behaviour produced
        WHICH outcome."""
        shipped = _Theft(self)
        self.addCleanup(shipped.cleanup)
        self.assertTrue(shipped.stranger_still_open())
        branch = shipped.store._finalizer()          # the real finalizer, real arguments
        self.assertTrue(shipped.stranger_still_open(),
                        "the shipped finalizer closed a descriptor that names another file")
        self.assertEqual(_ident(shipped.stranger_fd), shipped.stranger_ident,
                         "the number still resolves, but to something other than the stranger")

        fallback = _Theft(self)
        self.addCleanup(fallback.cleanup)
        self.assertTrue(fallback.stranger_still_open())
        fallback.store._fh.close()                   # THE PRE-FIX ACT, unguarded
        with self.assertRaises(OSError,
                               msg="the unguarded close left the stranger open, so the two "
                                   "behaviours do not differ and this row proves nothing"):
            os.fstat(fallback.stranger_fd)

        # AND THE BRANCH IS NAMED, so the shipped arm's pass is attributable rather than
        # merely observed: it did not close because the identity did not match.
        self.assertEqual(branch, "not-ours")

    def test_an_abandoned_store_collected_at_an_arbitrary_point_closes_no_stranger(self):
        """THE INTAKE'S OWN SHAPE. The defect is about a store nobody closed, finalized
        whenever the collector gets to it — so this row abandons the store and collects,
        rather than calling the finalizer by hand."""
        world = _Theft(self)
        self.addCleanup(world.cleanup)
        world.store = None
        gc.collect()
        self.assertTrue(world.stranger_still_open(),
                        "collecting an abandoned store closed a stranger's descriptor")

    def test_a_number_closed_and_not_reused_is_also_let_go_of(self):
        """THE THIRD WORLD, and it is the one an identity check reaches and an absence check
        does not: the number was released and nothing took it yet. There is nothing of ours
        there, so there is nothing to close — and closing anyway would release a number this
        store no longer holds, which is the same defect with a later arrival time."""
        d = tempfile.mkdtemp(prefix="w4c-gone-")
        store = EventStore(os.path.join(d, "record.jsonl"), require_rule_cited=False)
        store._append(_draft())
        fd = store._fh.fileno()
        os.close(fd)
        self.assertEqual(store._finalizer(), "already-closed")

    def test_the_ordinary_close_is_untouched_and_strands_nothing(self):
        """THE COMPLEMENT. A store nobody interfered with closes exactly as it always did, and
        the guard costs it nothing — the stranded list does not grow, so an ordinary run
        cannot be paying for this repair without anyone noticing."""
        before = len(store_mod._STRANDED)
        d = tempfile.mkdtemp(prefix="w4c-normal-")
        store = EventStore(os.path.join(d, "record.jsonl"), require_rule_cited=False)
        store._append(_draft())
        fd = store._fh.fileno()
        self.assertEqual(store._finalizer(), "closed")
        store._finalizer = None
        store._fh = None
        with self.assertRaises(OSError):
            os.fstat(fd)                              # its own descriptor really was released
        self.assertEqual(len(store_mod._STRANDED), before,
                         "an uncontested close stranded a descriptor")

    def test_store_close_is_idempotent_and_the_store_still_reads(self):
        """The public contract `close()` documents, re-driven through the guarded helper:
        idempotent, and a closed store may still be read."""
        d = tempfile.mkdtemp(prefix="w4c-idem-")
        store = EventStore(os.path.join(d, "record.jsonl"), require_rule_cited=False)
        rec = store._append(_draft(1))
        store.close()
        store.close()
        self.assertEqual(store.by_seq(rec["seq"])["object"], "w4c-1")
        store._append(_draft(2))                      # re-opens on demand, as documented
        self.assertEqual(len(store.all()), 2)
        store.close()

    def test_the_identity_is_taken_at_open_and_not_recomputed_later(self):
        """THE CHECK'S OWN SUBJECT MUST BE ESTABLISHED WHERE IT IS CERTAIN (§A38's family). The
        identity is captured at the one moment the number is provably this store's — inside
        `_require_fh`, immediately after the open. Recomputing it at finalize time would be
        the check asking the very question it exists to answer."""
        d = tempfile.mkdtemp(prefix="w4c-ident-")
        store = EventStore(os.path.join(d, "record.jsonl"), require_rule_cited=False)
        store._append(_draft())
        self.addCleanup(store.close)
        alive = store._finalizer.peek()
        self.assertIsNotNone(alive, "the finalizer is not registered at all")
        _obj, func, args, _kw = alive
        self.assertIs(func, store_mod._close_handle)
        held_fh, fd, ident = args
        self.assertIs(held_fh, store._fh)
        self.assertEqual(fd, store._fh.fileno())
        self.assertEqual(ident, _ident(fd))


if __name__ == "__main__":
    unittest.main()
