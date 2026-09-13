# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28C W2 — the echo-retire reply, and the buffer that licenses nothing.

`design/38` §1 rules the retire-on-exact-match discipline an integrity property in its own
right: **confirmation is content-hash identity, so a mutated or partial append can never
silently satisfy an intent.** ADDENDUM 1 then rules how it arrives here — as PIPELINE, never
an effect-license, subordinated to invariant 1.

  T-ECHO-EXACT                     the reply carries the appended record's identity AND a
                                   content hash over exactly the fields the submitter stated;
                                   the submitting side compares against what it submitted; a
                                   mismatch is a LOUD store error, never a silent retire.
                                   RED: a double that corrupts the echo.
  T-NO-ENDORSEMENT-FIRST-IN-MACHINE
                                   invariant 4 and the second named wrong reference together.
                                   No code path treats a queued intent as licensing any
                                   effect, and no in-flight state is persisted anywhere.
                                   RED: a double serving a READ from a queued intent without
                                   the provisional mark — deliberately a world the async-ack
                                   clause alone would NOT catch, because no reply was
                                   released early in it.

WHY THE ECHO IS OVER THE STATED FIELDS AND NOT OVER THE WHOLE RECORD. `seq`, `record_time`
and the envelope's defaults are MINTED at the append and the submitter does not know them —
hashing them would compare the appender against itself. The property that matters is that
the appended record agrees with the draft on every field the draft STATED, which is exactly
what a mutated or partial append would break.
"""

import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import commit as commit_mod                          # noqa: E402
from kernel import store as store_mod                            # noqa: E402
from kernel.canonical import canonical_hash                      # noqa: E402


class EchoCase(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28c-w2-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store = store_mod.EventStore(self.rec)
        # THE WIDTH THESE ROWS ARE ABOUT, DECLARED RATHER THAN INHERITED — the same reason
        # `tests/test_ep28c_w1.py` gives: the suite runs at two widths and a row whose subject
        # is a queued intent cannot inherit `GOVOS_COMMIT_WIDTH=1`, because at width 1 the
        # batch closes on the width before anything can sit in the queue and the row would be
        # asserting the override rather than the fence.
        self.store.group_commit.width = 16
        self.addCleanup(self.store.close)
        self.addCleanup(shutil.rmtree, self.dir, True)

    def draft(self, i=0):
        return {"actor": "SYSTEM", "action": "probe", "rule_cited": "M1-OBSERVATION",
                "payload": {"i": i, "text": "a governed write's exact bytes"},
                "refs": ["rec_1"], "object": "/d.txt"}


# =====================================================================================
# T-ECHO-EXACT
# =====================================================================================

class EchoExactCase(EchoCase):

    def test_the_reply_carries_the_appended_identity_and_a_content_hash(self):
        """Both halves of the reply, and both are what the submitter compares against."""
        d = self.draft()
        rec = self.store._append(d)
        self.assertEqual(rec["seq"], len(self.store.all()))
        self.assertEqual(store_mod.echo_digest(rec, d),
                         canonical_hash({k: d[k] for k in sorted(store_mod.ECHOED_FIELDS)
                                         if k in d}))

    def test_the_echo_equals_the_submitted_content(self):
        """T-ECHO-EXACT. Every field the draft stated survives the append byte-for-byte, and
        the equality is asserted through the SAME function the submitter uses — which is what
        makes it a check rather than two implementations agreeing by luck."""
        for i in range(5):
            d = self.draft(i)
            rec = self.store._append(d)
            self.assertEqual(store_mod.echo_digest(rec, d), store_mod.echo_digest(d, d))

    def test_a_mutated_append_cannot_silently_satisfy_the_intent(self):
        """THE PROPERTY IN ITS OWN WORDS. A record that differs from the draft in ANY stated
        field has a different echo, so it cannot be retired against that intent."""
        d = self.draft()
        rec = self.store._append(d)
        for field, mutated in (("actor", "someone-else"), ("action", "other"),
                               ("object", "/e.txt"), ("refs", ["rec_9"]),
                               ("payload", {"i": 0, "text": "not the exact bytes"})):
            forged = dict(rec)
            forged[field] = mutated
            self.assertNotEqual(store_mod.echo_digest(forged, d),
                                store_mod.echo_digest(d, d),
                                "a record differing in %r echoed identical to the draft — a "
                                "mutated append would retire the intent silently" % field)

    def test_red_world_a_corrupted_echo_is_loud(self):
        """RED WORLD for the hash-identity clause, NAMED. A double that returns the right
        record with the WRONG echo. The submitter refuses loudly; it does not retire.

        UNREACHABLE BY THE REPLY AND SYNC CLAUSES: the record is appended, durable and on the
        file in this world. What fails is only the identity check — which is the whole reason
        the echo is a separate row."""
        real = self.store._commit_batch

        def corrupting(batch):
            out = real(batch)
            for s in batch:
                if s.record is not None:
                    s.echo = "sha256:" + "0" * 64
            return out
        self.store._commit_batch = corrupting
        self.store.group_commit._commit_batch = corrupting
        self.addCleanup(setattr, self.store.group_commit, "_commit_batch", real)
        self.addCleanup(setattr, self.store, "_commit_batch", real)
        before = len(self.store.all())
        with self.assertRaises(store_mod.EchoMismatch) as caught:
            self.store._append(self.draft())
        self.assertIn("echo", str(caught.exception).lower())
        # The record IS durable in this world — which is what makes the red world specific.
        self.assertEqual(len(self.store.all()), before + 1)
        with open(self.rec, encoding="utf-8") as fh:
            self.assertEqual(sum(1 for line in fh if line.strip()), before + 1)

    def test_the_echo_survives_the_freeze(self):
        """The appended record is deep-frozen (dicts become read-only views, lists become
        tuples), and the draft is not. An echo that changed across the freeze would make
        every comparison a false alarm, so the canonical encoding's treatment of both is
        asserted rather than assumed."""
        d = self.draft()
        rec = self.store._append(d)
        self.assertNotIsInstance(rec, dict)          # frozen: a MappingProxyType
        self.assertIsInstance(rec["refs"], tuple)    # frozen: a tuple, not a list
        self.assertIsInstance(d["refs"], list)
        self.assertEqual(store_mod.echo_digest(rec, d), store_mod.echo_digest(d, d))


# =====================================================================================
# T-NO-ENDORSEMENT-FIRST-IN-MACHINE
# =====================================================================================

class NoEndorsementFirstCase(EchoCase):

    def test_the_buffer_persists_nothing_anywhere(self):
        """THE SECOND NAMED WRONG REFERENCE, refused by shape. Making the in-flight queue
        durable "so nothing is lost on crash" creates a second place truth lives. In-flight
        state here is PROCESS-LOCAL MECHANISM, lost on crash by design; crash honesty comes
        from invariant 1, not from persistence. Read out of `commit.py`'s executable body."""
        import ast
        with open(commit_mod.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            for attr in ("id", "attr", "name", "arg"):
                v = getattr(node, attr, None)
                if isinstance(v, str):
                    names.add(v)
        for forbidden in ("open", "write", "writelines", "fdatasync", "fsync", "dump",
                          "dumps", "flush", "Path", "mkdir", "rename", "replace",
                          "shelve", "pickle", "sqlite3"):
            self.assertNotIn(forbidden, names,
                             "commit.py reaches %r — the in-flight queue is being persisted, "
                             "which is a second store in costume" % forbidden)

    def test_the_queue_has_exactly_one_consumer(self):
        """Invariant 4's structural half: the buffer's entries are pipeline state with no
        consumer other than the appender and the echo comparison. The queue is read in ONE
        place, and no module outside the store and its commit loop names it at all."""
        import ast
        with open(commit_mod.__file__, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src)
        readers = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Attribute) and inner.attr == "_queue":
                        readers.append(node.name)
                        break
        # [DOCUMENTED FLIP, EP-28G, 2026-08-03. The enqueueing half of `submit` moved into
        # `await_pending` when EP-28G split publication from the durability wait, because the
        # gate must hold the decide region across the first and must not hold it across the
        # second. THE SUBJECT IS UNCHANGED AND SO IS THE COUNT: the queue is still reached
        # from exactly one place that is not construction or the appender's own take, and it
        # is still the submitter's own side. Only the name of that place moved. Retained
        # rather than rewritten: `submit` is what it was called before the split.]
        self.assertEqual(sorted(set(readers)), ["__init__", "_take_batch", "await_pending"],
                         "the queue is reached from %s — a consumer other than the appender "
                         "has grown" % sorted(set(readers)))
        # AND NOBODY OUTSIDE REACHES IT. A view that could see a queued intent is the fence
        # `design/38` §1 puts on the buffer, broken from the read side.
        src_root = os.path.dirname(commit_mod.__file__)
        for sub in ("kernel", "bridge"):
            root = os.path.join(os.path.dirname(src_root), sub)
            for name in sorted(os.listdir(root)):
                if not name.endswith(".py") or name in ("commit.py", "store.py"):
                    continue
                with open(os.path.join(root, name), encoding="utf-8") as fh:
                    body = fh.read()
                self.assertNotIn("group_commit._queue", body)
                self.assertNotIn("_take_batch", body)

    def test_no_read_path_answers_from_a_queued_intent(self):
        """THE BEHAVIOURAL HALF. The store's read surface shows APPENDED records and never a
        queued entry that has not been appended.

        RE-AIMED [DOCUMENTED FLIP, EP-28G, 2026-08-03, mapped to the publish/await split].
        The row used to hold a batch open and read the surface while eight submitters waited,
        on the premise that a waiting submitter's record had not been appended yet. EP-28G
        ended that premise: publication moved into the deciding thread, so what waits in the
        queue is a record that HAS been appended and MUST be visible — act N+1's decide,
        entering after act N's append, has to read a fold containing act N or the region
        protects nothing and the race returns wearing its name.

        THE FENCE THE ROW EXISTS FOR IS UNTOUCHED AND IS NOW ASSERTED DIRECTLY. `design/38`
        §1 forbids the buffer becoming a second source of truth for reads. The old
        construction tested that by TIMING and, after the split, its outcome depended on
        which of two threads ran first — it passed three times in six under the new code,
        which is a coin and not a check. The new construction puts an UNPUBLISHED submission
        in the queue by hand and asserts the read surface cannot see it. Deterministic, and
        it is the fence's own claim rather than a proxy for it."""
        gc = self.store.group_commit
        # One REAL record first, so the row asserts both halves: what is appended IS shown,
        # and what is only queued is NOT. A surface showing nothing at all would pass the
        # second half vacuously.
        self.store._append(self.draft(1))
        before = self.store.all()
        self.assertEqual(len(before), 1)
        pending = commit_mod.Submission(self.draft(4242))
        self.assertIsNone(pending.record,
                          "the submission was published before the row could ask about it")
        with gc._qlock:
            gc._queue.append(pending)
        self.addCleanup(lambda: gc._queue.clear())
        during = self.store.all()
        self.assertEqual(len(during), len(before),
                         "a queued intent was visible on the read surface before it was "
                         "appended — the buffer became a second source of truth")
        self.assertNotIn(4242, [(e.get("payload") or {}).get("i") for e in during])
        with open(self.rec, encoding="utf-8") as fh:
            self.assertEqual(sum(1 for line in fh if line.strip()), len(before),
                             "an unpublished submission reached the record file")

    def test_every_queue_member_is_a_record_and_not_an_intent(self):
        """THE SPLIT'S OWN CLAIM, ASSERTED [EP-28G, 2026-08-03]. The row above proves the
        buffer answers no read; this one proves WHY that is now trivially true rather than
        carefully maintained: after the split there is nothing in the queue for a read to
        want. Every member arrives carrying its appended record, so the queue holds pointers
        into the one source of truth instead of a second one.

        It is the positive half of the same fence and it can fail: an implementation that
        went back to queueing drafts would red here while the row above stayed green."""
        gc = self.store.group_commit
        gc.closes_on_empty = False
        gc.window_s = 0.4
        seen = {}

        def watcher(batch):
            with gc._qlock:
                seen["queued"] = [s.record for s in gc._queue] + [s.record for s in batch]
            return real(batch)
        real = gc._commit
        gc._commit = watcher
        self.addCleanup(setattr, gc, "_commit", real)
        self.store._append(self.draft(7))
        self.assertTrue(seen.get("queued"), "the appender never saw a queue member")
        for rec in seen["queued"]:
            self.assertIsNotNone(rec, "a queue member carried no record — the queue is "
                                      "holding intents again and a read could want one")
            self.assertIn("seq", rec)

    def test_red_world_a_view_served_from_a_queued_intent(self):
        """RED WORLD for the no-effect-license clause SPECIFICALLY, and generated rather than
        inherited. A double answers a read by consulting the QUEUE and returns the pending
        entry WITHOUT the provisional mark `design/38` §1's second fence requires.

        THE POINT OF THIS RED WORLD is that the async-ack clause would NOT catch it: no reply
        is released early anywhere in it, every record still syncs before its own reply, and
        invariant 1 is untouched. What fails is only that a queued intent answered a
        question, which is the clause this row exists for."""
        gc = self.store.group_commit
        d = self.draft(99)
        pending = commit_mod.Submission(d)
        with gc._qlock:
            gc._queue.append(pending)

        def leaking_view():
            # The forbidden shape: a read that unions the record with the pending buffer and
            # marks nothing provisional.
            out = [dict(e) for e in self.store.all()]
            with gc._qlock:
                out.extend(dict(s.draft) for s in gc._queue)
            return out
        answered = leaking_view()
        self.assertEqual(answered[-1]["payload"]["i"], 99)
        self.assertNotIn("provisional", answered[-1],
                         "the double marked it provisional, so it does not exhibit the world "
                         "the fence forbids")
        # THE GUARD REDS ON IT — the same assertion the shipped read surface passes.
        with self.assertRaises(AssertionError):
            self.assertEqual(len(answered), len(self.store.all()),
                             "a read answered from a queued intent")
        # AND INVARIANT 1 IS GREEN IN THIS WORLD, which is what makes the row separate.
        with gc._qlock:
            gc._queue.clear()
        rec = self.store._append(self.draft(1))
        self.assertEqual(rec["seq"], len(self.store.all()))


if __name__ == "__main__":
    unittest.main()
