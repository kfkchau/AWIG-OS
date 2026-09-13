# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28E W4 — the third arm on the PER-ACT path: does a gated act carry a namespace term?

THE QUESTION, and it is EP-28E ADDENDUM 1 §1.6's, not this file's. `design/36` ADDENDUM P.4
measured FILE-OPEN at 2.177 ms in a world of 863 names and 3.611 ms in one of 96,002, and
the sitting mentor read that 1.66x rise as one band without asking what it was. If a
namespace scan sits on the gate's per-act path, that rise is a candidate for it. W1 found
that one does — `_posix_precondition` calls `children` on `rmdir` and on a rename over a
directory — and ADDENDUM C's per-act guard cannot see it, because a namespace read touches
no record.

WHAT THIS FILE SETTLES AND WHAT IT DOES NOT, said first because the difference is the whole
honest content of it.

  SETTLED, here, as a COUNTABLE: whether FILE-OPEN, FILE-WRITE and FILE-CLOSE do work
  proportional to the namespace. A countable is deterministic, has no spread, and survives a
  faster machine — and it answers the structural question completely, because a term that is
  absent from the count cannot be present in the milliseconds.

  NOT SETTLED, and RAISED rather than approximated: the MILLISECONDS in worlds B and C
  through the module and the channel, which is what §1.6 asks for with spreads. Those are
  guest figures and this session could not take them. The reason is in this EP's log entry
  and it is a host condition, not a result.

NO RULING IS MADE HERE AND NO FIX IS TAKEN. §1.6's words: report the numbers, rule nothing.

THE ARMS. Two worlds built through the REAL gate, the same store size, namespaces far apart
— the shape §1.6 names (world B: 371,001 records / 96,002 names; world C: 300,206 / 207).
Scaled down to suite size and stated as such: the ratio is what a countable needs, and the
absolute size is what a duration needs and this is not a duration.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from bridge import custody                        # noqa: E402
from bridge.kernel_port import KernelPort          # noqa: E402
from bridge.mount import build_brain               # noqa: E402
from tests.test_ep28e_w3 import _Counted, _instrument, _work   # noqa: E402

#: The two arms. NAMES_WIDE / NAMES_NARROW is the namespace ratio; both arms are padded to
#: the same STORE size with acts that mint no name, which is exactly how world C separates
#: the two variables that were collinear in every world ADDENDUM P measured.
NAMES_WIDE, NAMES_NARROW = 600, 100

#: The three acts §1.6 names, in the order a real caller performs them.
ACTS = ("FILE-OPEN", "FILE-WRITE", "FILE-CLOSE")


class _Arm:
    """One world, built through the gate, with its custody fold under a step counter."""

    def __init__(self, case, n_names, n_nameless):
        self.work = tempfile.mkdtemp(prefix="ep28e-w4-")
        case.addCleanup(shutil.rmtree, self.work, True)
        os.makedirs(os.path.join(self.work, "blobs"), exist_ok=True)
        rec = os.path.join(self.work, "rec.jsonl")
        open(rec, "w").close()
        store, gate, views, blobs = build_brain(rec, os.path.join(self.work, "blobs"))
        self.port = KernelPort(store, gate, views, blobs)
        self.store, self.gate, self.views = store, gate, views

        # THE SUBJECT OF EVERY ACT: one file, at the same path with the same inode in both
        # arms, so the two arms are asked the same question.
        self._req("FILE-MKDIR", path="/probe", perm="755")
        self._req("FILE-CREATE", path="/probe/f", perm="644")
        self.ino = self.port.state.lookup("/probe/f").ino

        for i in range(n_names):
            self._req("FILE-CREATE", path="/n%d" % i, perm="644")
        # THE STORE PADDING GOES THROUGH THE GATE, NOT THE PORT, and the reason is worth one
        # line: the files port carries the files ops and nothing else, so `CREATE-INFO`
        # through it is a Closure Hit and answers ENOSYS — which is the port being right.
        # The gate is the same appender either way, and the fold advances off the append, so
        # these records land in the world exactly as a port-borne one would.
        for i in range(n_nameless):
            self.gate.execute("CREATE-INFO", "owner", {"object": "i:%d" % i, "content": "x"})

        self.names = len(self.port.state.names)
        self.records = len(self.store.all())
        self.counter = _instrument(self.port.state)

    @property
    def actor(self):
        """WHO THE MEASURED ACTS ARE TAKEN AS. Stated because `design/36` ADDENDUM C's
        method note makes it a condition of a figure meaning anything: the gate exempts the
        chain-end from the authority step, so an act taken as the owner never consults the
        authority fold and reports a cost that does not exist."""
        return self.port._actor(0)

    def _req(self, op, cls="DECISION", **kw):
        f = {"id": "1", "op": op, "class": cls, "uid": "0", "gid": "0",
             "pid": str(os.getpid())}
        f.update({k: str(v) for k, v in kw.items()})
        status, fields, payload = self.port.handle(f, b"")
        if status != 0:
            raise AssertionError("building the arm failed at %s: status %d" % (op, status))
        return status, fields, payload

    def act(self, op):
        """One gated act on the fixed subject, with the namespace work it did."""
        kw = {"path": "/probe/f", "inode": self.ino}
        if op == "FILE-WRITE":
            kw.update(length=1, offset=0)
        return _work(self.counter, lambda: self._req(op, **kw))


class TestThePerActPathNamespaceTerm(unittest.TestCase):
    """T-PER-ACT-PATH-CARRIES-NO-NAMESPACE-TERM, for the three acts §1.6 names."""

    @classmethod
    def setUpClass(cls):
        cls._built = None

    def _arms(self):
        wide = _Arm(self, NAMES_WIDE, 0)
        narrow = _Arm(self, NAMES_NARROW, NAMES_WIDE - NAMES_NARROW)
        return wide, narrow

    def test_the_measured_acts_are_taken_as_a_non_exempt_actor(self):
        """ADDENDUM C's method rule, as a condition rather than a claim. A figure that does
        not say which actor it used is not a measurement, and a figure taken as the chain-end
        skipped the authority step entirely."""
        wide, _ = self._arms()
        self.assertNotEqual(wide.actor, wide.views.chain_end(),
                            "the measured acts are taken as the chain-end, which the gate "
                            "exempts from the authority step — the figures would be of a "
                            "path no ordinary caller uses")
        self.assertEqual(wide.actor, "uid:0",
                         "the acting actor is not the one this file reports")

    def test_the_arms_separate_the_namespace_from_the_store(self):
        """THE ARM-SET RULE FIRST, because a decomposition taken across arms that do not
        differ in the variable under test reports nothing about it. This is the check whose
        absence made ADDENDUM P attribute a namespace cost to the store."""
        wide, narrow = self._arms()
        self.assertGreater(wide.names, 5 * narrow.names,
                           "the arms do not differ in the NAMESPACE, so nothing below is a "
                           "statement about a namespace term")
        self.assertEqual(wide.records, narrow.records,
                         "the arms differ in the STORE (%d vs %d), so a difference below "
                         "could be either variable — which is exactly the confounding "
                         "ADDENDUM Q corrected" % (wide.records, narrow.records))

    def test_no_gated_act_does_work_proportional_to_the_namespace(self):
        """THE DECOMPOSITION, as a countable, side by side. Reported in the failure message
        whichever way it goes, because §1.6 asks for the numbers and not for a verdict."""
        wide, narrow = self._arms()
        rows = {}
        for op in ACTS:
            w_steps, _ = wide.act(op)
            n_steps, _ = narrow.act(op)
            rows[op] = (n_steps, w_steps)
        side_by_side = "; ".join(
            "%s: %d steps at %d names / %d steps at %d names"
            % (op, rows[op][0], narrow.names, rows[op][1], wide.names) for op in ACTS)
        for op in ACTS:
            n_steps, w_steps = rows[op]
            with self.subTest(act=op, decomposition=side_by_side):
                self.assertEqual(
                    n_steps, w_steps,
                    "%s did more namespace work in the wider arm at the same store size, so "
                    "the per-act path DOES carry a namespace term: %s" % (op, side_by_side))

    def test_the_instrument_was_still_counting_after_the_acts(self):
        """A gated act appends, and an append advances the fold — so a bind during the act
        could put a name into a container this instrument does not cover, and every row above
        would then be a zero that means nothing. Checked rather than reasoned about."""
        wide, _ = self._arms()
        for op in ACTS:
            wide.act(op)
        state = wide.port.state
        for name in ("names", "inodes", "kids", "paths"):
            self.assertIsInstance(getattr(state, name), _Counted,
                                 "%s is no longer instrumented after the acts" % name)
        for outer in ("kids", "paths"):
            plain = sorted(k for k, v in dict.items(getattr(state, outer))
                           if not isinstance(v, _Counted))
            self.assertEqual(plain, [],
                             "%s gained an uncounted container during the acts: %s"
                             % (outer, plain))

    def test_the_precondition_namespace_scan_w1_raised_is_closed_by_w2(self):
        """W1's RAISED item 5, closed with evidence rather than by inference.

        W1 reported that `_posix_precondition` calls `children` before the gate is consulted
        on an `rmdir` and on a rename over a directory — so a namespace scan sat on the
        gate's PER-ACT path, where ADDENDUM C's guard cannot see it. W2 did not touch
        `_posix_precondition`; it fixed `children`, and the precondition inherits that. This
        row is here because "the caller inherits the fix" is a composition argument, and the
        estate's rule is to check the composition rather than to state it.

        A REFUSED `rmdir` IS THE SUBJECT ON PURPOSE. The precondition's `children` call is
        the one that answers ENOTEMPTY, so the act that exercises it is an `rmdir` of a
        directory that is NOT empty — and that act appends nothing, which is what makes it a
        precondition rather than a refusal (design/10 §11.1a class 2).

        [CORRECTED IN PLACE — EP-28C W4e, 2026-08-07. The last clause of the paragraph above
        is a repealed fact and is kept as the record of what this pass believed. The act now
        APPENDS: owner ruling 1 reclassified these outcomes, EP-28N declared `contains:empty`
        as law, and W4e retired the port's read, so the emptiness question is the gate's
        declared check and a declared refusal records. THIS ROW DID NOT RED AND NEEDED NO
        FLIP — its subject is the STEP COUNT of the `children` scan, which the gate's check
        makes on the same fold, so the measurement is unchanged and only the sentence about
        what the act leaves behind had gone stale.]"""
        import errno
        wide, narrow = self._arms()
        rows = {}
        for label, arm in (("narrow", narrow), ("wide", wide)):
            steps, (status, _f, _p) = _work(arm.counter, lambda: arm.port.handle(
                {"id": "1", "op": "FILE-RMDIR", "class": "DECISION", "uid": "0", "gid": "0",
                 "pid": str(os.getpid()), "path": "/probe"}, b""))
            self.assertEqual(status, -errno.ENOTEMPTY,
                             "the rmdir did not reach the emptiness precondition, so this "
                             "row is not exercising the read W1 raised")
            rows[label] = steps
        self.assertEqual(
            rows["narrow"], rows["wide"],
            "the rmdir precondition still costs the namespace: %d steps at %d names against "
            "%d steps at %d names" % (rows["narrow"], narrow.names, rows["wide"], wide.names))
        self.assertLessEqual(
            rows["wide"], 2,
            "the rmdir precondition costs %d steps to answer about a directory holding one "
            "entry" % rows["wide"])

    def test_the_decomposition_can_report_a_term_that_is_there(self):
        """THE RED WORLD. Every row above is an equality between two zeros, and two zeros are
        equal whether or not anything is being measured. A namespace read on the DECISION
        PATH — the one W1 found — is put onto FILE-OPEN's branch, and the decomposition is
        required to report it.

        THE PLANTED READ IS THE REAL ONE, not a synthetic scan: it is the scanning `children`
        this EP's W2 replaced. So this row also fixes what the acts WOULD cost if the same
        branch were reached — which is why the finding at RAISED item 5 is worth its own
        derivation.

        DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS READING:
        `KernelPort._posix_precondition`, read off the CLASS and replaced with a wrapper that
        planted the scan on FILE-OPEN's branch. The attribute is gone, so the read raised
        `AttributeError` before the arms ever ran.

        THE PLANT MOVES TO `_decide` ITSELF AND THE ROW IS STRICTLY BETTER FOR IT. What this
        red world has to prove is that the decomposition can SEE a namespace read taken
        before the gate; the retired function was one site on that path, and `_decide` is the
        path. Planting at the path rather than at one of its callees means the row keeps
        working through any later change of which method holds a pre-gate read — which is
        exactly the failure that brought it here."""
        real_decide = KernelPort._decide
        real_children = custody.CustodyState.children

        def scanning(self_, path):
            path = custody._norm(path)
            return sorted(custody.basename(c) for c in self_.names
                          if c != path and custody.parent_of(c) == path)

        def decide_reading_the_namespace(self_, op, f, payload):
            if op == "FILE-OPEN":
                # BEFORE THE GATE, which is the whole point of the plant: this is the
                # position `_posix_precondition` occupied, held now by the path itself.
                self_.state.children("/probe")
            return real_decide(self_, op, f, payload)

        custody.CustodyState.children = scanning
        KernelPort._decide = decide_reading_the_namespace
        try:
            wide, narrow = self._arms()
            w_steps, _ = wide.act("FILE-OPEN")
            n_steps, _ = narrow.act("FILE-OPEN")
        finally:
            KernelPort._decide = real_decide
            custody.CustodyState.children = real_children
        self.assertGreater(
            w_steps, 5 * n_steps,
            "a namespace read planted on FILE-OPEN's own precondition branch was not "
            "reported as proportional to the namespace (%d vs %d), so the equalities above "
            "prove nothing" % (n_steps, w_steps))


if __name__ == "__main__":
    unittest.main()
