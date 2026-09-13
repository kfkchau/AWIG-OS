# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28C W3 — the two items carried in from the EP-28D verdict.

Both live in `src/kernel/store.py`, which is why they land in the EP that works that file.

  1. THE HELD RECORD DESCRIPTOR LANDS. EP-28B wrote it and withdrew it in the same session
     because the conformance fixture appeared to break under it; EP-28D repaired the fixture
     and DROVE BOTH DIRECTIONS, so the change is safe. It is worth under 2% of an act, and
     the reason it is not optional is EP-28D's, carried verbatim: the store still opened per
     append, so the instrument still momentarily occupied the number a row had just released
     — invisible only because the descriptor's lifetime was shorter than the gap between two
     subject calls, WHICH IS A PROPERTY OF THE STORE RATHER THAN A GUARANTEE THE INSTRUMENT
     MAKES. A conformance surface passing on an accident of timing that nobody promises is a
     surface that will move without anyone changing it.

  2. THE `_index` COMMENT ASSERTED A REFUTED MECHANISM and is corrected IN PLACE with a
     dated note rather than deleted — the handling `design/10` §11.2b and EP-28B's raise
     both got. A source comment stating a mechanism that driving it refuted is a
     specification the next reader will build against.

  T-DESCRIPTOR-RED-WORLD    carried from the EP-28D verdict: neuter the descriptor change
                            and the WHOLE CLASS must fail. The clause it names is
                            *the record file is opened once and held*, and it is unreachable
                            by every clause that already passed — in the neutered world
                            records still append individually, still sync, and still reply.

  THE TWO DOCUMENTED FLIPS live where the pins live and flip together:
  `tests/test_ep28_w8.py::test_the_record_file_is_opened_once_and_held` and
  `tests/test_ep28b.py::test_the_held_descriptor_half_landed`. THE FLIP IS THE EVIDENCE.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import store as store_mod                            # noqa: E402


class DescriptorCase(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28c-w3-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store = store_mod.EventStore(self.rec)
        self.addCleanup(self.store.close)
        self.addCleanup(shutil.rmtree, self.dir, True)

    def draft(self, i=0):
        return {"actor": "SYSTEM", "action": "probe", "rule_cited": "M1-OBSERVATION",
                "payload": {"i": i}}

    def opens_during(self, fn):
        """How many times the record file is opened while `fn` runs."""
        opened = []
        real = store_mod.Path.open

        def spy(self_path, *a, **k):
            if str(self_path) == self.rec:
                opened.append(a[0] if a else k.get("mode"))
            return real(self_path, *a, **k)
        store_mod.Path.open = spy
        try:
            fn()
        finally:
            store_mod.Path.open = real
        return opened

    # ---- the CLASS: every assertion the descriptor change makes true ----------------
    def held_descriptor_class(self):
        """THE WHOLE CLASS, in one place, so the red world can require ALL of it to fail.

        Returns the list of failures rather than asserting, because the red world's own
        requirement is that this class goes red as a class — and a helper that raised on the
        first failure could not tell 'the class failed' from 'one member failed'."""
        failures = []
        self.opens_during(lambda: self.store._append(self.draft(1)))
        # THE OBJECT AND NOT THE NUMBER. A store that closes and re-opens gets the same
        # lowest-free number back, so the fd number is identical in both worlds and cannot
        # tell them apart — the file OBJECT can. Measuring the number was tried first and it
        # is exactly the mistake `design/10` §11.2b keeps finding: the countable that looks
        # like the subject and is not.
        held = self.store._fh
        later = self.opens_during(lambda: [self.store._append(self.draft(i))
                                           for i in range(2, 22)])
        if later != []:
            failures.append("twenty later appends opened the record file %d times — the "
                            "descriptor is not held" % len(later))
        if self.store._fh is not held:
            failures.append("the descriptor the store holds is not the one it opened — it "
                            "is being re-allocated, not held")
        return failures

    def test_the_held_descriptor_landed(self):
        """The class, green. Twenty-one appends, ONE open."""
        self.assertEqual(self.held_descriptor_class(), [])

    def test_red_world_neuter_the_descriptor_change_and_the_whole_class_fails(self):
        """T-DESCRIPTOR-RED-WORLD, carried from the EP-28D verdict.

        THE CLAUSE IT NAMES: *the record file is opened once and held*. Neutered by making
        the store re-open per batch — which is exactly the pre-EP-28C behaviour — the whole
        class goes red.

        UNREACHABLE BY EVERY CLAUSE THAT ALREADY PASSED, and that is checked here rather than
        asserted: in this world records still append individually, the barrier still runs,
        every reply still arrives after it, and the echo still matches. So a green on any of
        those clauses says nothing about this one."""
        real = store_mod.EventStore._require_fh

        def reopening(store_self):
            # THE NEUTERED VERSION: a fresh descriptor every time it is asked for, which is
            # what the store did before this EP.
            if store_self._fh is not None:
                store_self._fh.flush()
                store_self._fh.close()
            store_self._fh = store_self.file_path.open("a", encoding="utf-8")
            return store_self._fh
        store_mod.EventStore._require_fh = reopening
        self.addCleanup(setattr, store_mod.EventStore, "_require_fh", real)

        neutered = store_mod.EventStore(os.path.join(self.dir, "neutered.jsonl"))
        self.addCleanup(neutered.close)
        held, self.store, self.rec = self.store, neutered, os.path.join(self.dir,
                                                                        "neutered.jsonl")
        try:
            failures = self.held_descriptor_class()
            self.assertEqual(len(failures), 2,
                             "the neutered world did not fail the whole class — it failed "
                             "%r, so this red world proves less than it claims" % (failures,))
            # THE OTHER CLAUSES ARE GREEN IN THE SAME WORLD.
            before = len(neutered.all())
            d = self.draft(99)
            rec = neutered._append(d)
            self.assertEqual(len(neutered.all()), before + 1)      # appends individually
            self.assertEqual(rec["seq"], len(neutered.all()))      # replies after the sync
            self.assertEqual(store_mod.echo_digest(rec, d),
                             store_mod.echo_digest(d, d))          # the echo still matches
        finally:
            self.store = held


# =====================================================================================
# ITEM 2 — the `_index` comment, corrected in place with a dated note
# =====================================================================================

class IndexCommentCase(unittest.TestCase):
    """The comment beside `_index` asserted that the fixture's interleaving makes the
    `files.close` row's `EBADF` answer DISAPPEAR. EP-28D drove it with a held-descriptor
    double and it does not: the row's second `close` SUCCEEDS, the `EBADF` is raised a moment
    later by the instrument's own barrier, the ABI leg sees the pinned answer and the row
    PASSES — a row GREEN for the wrong reason rather than red for the wrong reason.

    CORRECTED IN PLACE WITH A DATED NOTE, NEVER DELETED, matching how `design/10` §11.2b and
    EP-28B's raise were handled. The raise was right about the thing that mattered — an
    instrument WAS interfering with its subject at exactly the site named — and only the
    predicted symptom was wrong, which is why it is corrected rather than withdrawn."""

    def setUp(self):
        with open(store_mod.__file__, encoding="utf-8") as fh:
            self.src = fh.read()

    def test_the_refuted_mechanism_is_no_longer_asserted_as_fact(self):
        """The specification the next reader would have built against is gone from the
        indicative. What EP-28D actually measured is what the comment now says."""
        self.assertNotIn("the row's EBADF answer disappears", self.src)
        self.assertIn("EP-28D", self.src)

    def test_the_correction_is_dated_and_the_original_claim_is_still_readable(self):
        """PRESERVE, DO NOT SMOOTH. The comment carries a dated correction AND still states
        what the raise predicted, because a correction that erases the prediction leaves the
        next reader unable to tell a refuted mechanism from one nobody ever proposed."""
        self.assertIn("DATED CORRECTION, 2026-08-01", self.src)
        self.assertIn("GREEN for the wrong reason", self.src)
        self.assertIn("WHAT THE RAISE PREDICTED", self.src)
        self.assertIn("[Refuted above:", self.src,
                      "the retained prediction is not marked as refuted where it stands, so "
                      "a reader meeting the paragraph first meets it as fact")
        self.assertIn("THE RAISE AS FILED", self.src)

    def test_the_comment_sits_where_the_raise_named_it(self):
        """`_index`'s neighbourhood, which is where EP-28D's verdict said to correct it."""
        note = self.src.index("GREEN for the wrong reason")
        index_def = self.src.index("    def _index(self, e):")
        self.assertLess(note, index_def)
        self.assertLess(index_def - note, 4000,
                        "the dated correction drifted away from `_index`, where the raise "
                        "named it")


if __name__ == "__main__":
    unittest.main()
