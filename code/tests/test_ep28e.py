# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28E W1 — the read path's cost ATTRIBUTED to a line, and its variable named.

W1 is the whole of what this file lands. [DATED AMENDMENT, EP-28E W2, same EP, after
ADDENDUM 1: W2 and W3 were STOPPED when this file was written and are now BUILT — W2 in
`src/bridge/custody.py`, W3 in `test_ep28e_w3.py`. Four rows here were falsified by that
work and are flipped in place as documented flips, each marked at its site: the two
`_TODAY` rows and the `children` / `path_of` verdicts in the enumeration below. Nothing
else in this file moved, and W1's finding is unchanged — it is `design/36` ADDENDUM Q.]

[SECOND DATED AMENDMENT, EP-28E W5, same EP, after ADDENDUM 2 §2.3: `nlink` was the third
line W1 named and it is now fixed, in `src/bridge/custody.py`, with its reference arm and
its caller differentials in `test_ep28e_w5.py`. One verdict flips here — `nlink` SCANS →
CONSTANT — and the flip's control gains a reinstated scanning `nlink`, because this file's
own rule is that a row asserting a ZERO ships with a world that makes it red. `snapshot` is
now the only SCANS row and it is the one that is supposed to be. THE LINE NUMBERS IN "THE
LINES" BELOW ARE W1's AND ARE NOT UPDATED: they say where the cost was found on 2026-07-30,
which is a fact about a finding rather than a pointer to current code.]

WHAT ADDENDUM P ESTABLISHED, and it is carried, not re-measured: `readdir` on an
EMPTY directory costs 1.377 ms at a 3,001-record store and 132.591 ms at 371,856,
flat in directory size at both arms.

WHAT W1 ADDS, and it changes where the fix goes. ADDENDUM P's sentence is "`readdir`
reads the whole RECORD". Measured, it reads the whole NAMESPACE — the fold's
`names` table — and it reads NO RECORDS AT ALL. In the defconfig world those two
variables are confounded, because every record in that world was a custody act that
minted a name, so 371,856 records carried ~97,000 names and the two grew together.
A third world separates them: at a 300,206-record store holding a 207-name
namespace, the same `readdir` costs 0.083 ms. The cost tracks the namespace.

THE LINES. `src/bridge/custody.py`:

    :312  CustodyState.children(path)  -- iterates EVERY name, keeps those whose
                                          parent matches. THE readdir cost.
    :306  CustodyState.path_of(ino)    -- iterates names until the inode matches;
                                          worst case every name. On EVERY lookup.
    :293  CustodyState.nlink(ino)      -- one scan for the link count, and on a
                                          directory a second scan plus `path_of`.
    :331  CustodyState.snapshot()      -- every name and every inode, by design.

Reached from `src/bridge/kernel_port.py:261,265` (stance 4, the stance ADDENDUM P
measured) and `src/bridge/records_fs.py:288,333` (stance 3).

WHY THE ASSERTIONS BELOW ARE COUNTABLES AND NOT DURATIONS. A duration says this
machine was slow today; a countable says the read examined 806 names to answer a
question about 1, which stays true on a faster machine and is the property W2 has
to move. The standing rule, and the reason the flip row below is checkable.

TWO ROWS WERE THE DEFECT STATED AS A FACT, marked `_TODAY` so no future grep would read
them as a design statement, and they PASSED because the defect was there. W2 made both go
red, which is what they were for. They are now flipped to assert the property and the
marker is gone; a third row reinstates the scanning implementations as doubles and requires
both flipped rows to go red, because each now asserts a ZERO and an unproven zero is
indistinguishable from an instrument that stopped counting.
"""

import collections
import os
import shutil
import sys
import tempfile
import traceback
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from bridge import custody                       # noqa: E402
from bridge.kernel_port import KernelPort         # noqa: E402
from bridge.mount import build_brain              # noqa: E402
from kernel.store import EventStore               # noqa: E402


# =====================================================================================
# the counting instrument, and it is checked before it is trusted
# =====================================================================================
class _CountingNames(dict):
    """The fold's name table, counting how many entries an operation walks.

    A dict subclass rather than a wrapper, because `apply()` assigns into, pops from
    and tests membership on this object, and those must keep working unchanged — only
    ITERATION is instrumented, which is the thing whose size is in question.
    `__contains__`, `get` and `__setitem__` are dict's own and stay constant-time, so
    a read that uses them registers zero steps and that zero is a real answer.
    """

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.steps = 0

    def _walk(self):
        for key in list(dict.keys(self)):
            self.steps += 1
            yield key

    def __iter__(self):
        return self._walk()

    def items(self):
        return ((k, dict.__getitem__(self, k)) for k in self._walk())

    def values(self):
        return (dict.__getitem__(self, k) for k in self._walk())


def _world(n_dirs, per_dir):
    """A namespace built by folding records through the SAME fold body the mount uses.

    Not gated: the subject is what a READ costs given what the fold holds, and no
    figure here is an append. Stated rather than left to be discovered.
    """
    recs = [{"action": "FILE-MKDIR", "record_time": 1.0,
             "payload": {"path": "/probe", "inode": 2, "perm": "755"}},
            {"action": "FILE-CREATE", "record_time": 1.0,
             "payload": {"path": "/probe/only", "inode": 3, "perm": "644"}}]
    ino = 4
    for d in range(n_dirs):
        recs.append({"action": "FILE-MKDIR", "record_time": 1.0,
                     "payload": {"path": "/d%d" % d, "inode": ino, "perm": "755"}})
        ino += 1
        for k in range(per_dir):
            recs.append({"action": "FILE-CREATE", "record_time": 1.0,
                         "payload": {"path": "/d%d/f%d" % (d, k), "inode": ino,
                                     "perm": "644"}})
            ino += 1
    state = custody.fold(recs)
    state.names = _CountingNames(state.names)
    return state, recs


def _steps(state, fn):
    state.names.steps = 0
    fn()
    return state.names.steps


class TestTheCountingInstrument(unittest.TestCase):
    """The control. A counter that cannot tell a scan from a lookup would report every
    row below as clean, so it is made to answer a known scan and a known lookup first."""

    def test_it_counts_a_scan_and_does_not_count_a_lookup(self):
        state, _ = _world(20, 4)
        size = len(state.names)
        self.assertEqual(_steps(state, lambda: [k for k in state.names]), size,
                         "the counter did not see a deliberate full walk of the namespace")
        self.assertEqual(_steps(state, lambda: state.names.get("/probe")), 0,
                         "the counter charged steps to a constant-time dict lookup")


# =====================================================================================
# W1 — the read-path enumeration, with each verdict CHECKED rather than stated
# =====================================================================================
#: Every fold read the served read paths make, with the verdict W1 measured. `SCANS`
#: means the work grows with the namespace; `CONSTANT` means it does not. This table is
#: the deliverable W1 names — "a list of read-path operations checked with their
#: results" — and the test below re-derives every verdict by counting, so a row that
#: stops being true fails rather than sitting here as documentation.
#:
#: DOCUMENTED FLIP, EP-28E W2 — `children` and `path_of` moved SCANS → CONSTANT because W2
#: landed and they no longer walk the namespace at all. Read this table on its own stated
#: axis: CONSTANT here means "does not grow with the NAMESPACE", which is the variable this
#: file's instrument counts. It does NOT mean O(1): `children` costs the entries of the one
#: directory asked about, which is what its answer depends on and therefore what it is
#: supposed to cost. The check that the cost tracks the DEPENDENCY rather than any single
#: variable is W3's guard, in `test_ep28e_w3.py`, which counts all four fold structures
#: instead of only this one.
#:
#: DOCUMENTED FLIP, EP-28E W5 — `nlink` moved SCANS → CONSTANT. It was left SCANS at W2
#: because ADDENDUM 1 §1.3 scoped that work to two lines and RAISED this one; ADDENDUM 2 §2.3
#: directed the replacement and it landed. Same axis as the two rows above: CONSTANT means
#: "does not grow with the NAMESPACE", which is the variable this file's instrument counts.
#: `nlink` still costs the one directory's own entries, which is what its answer depends on
#: and therefore what it is supposed to cost — that half is W3's guard.
#:
#: `snapshot` stays SCANS and is NOT a leftover: its answer IS the whole namespace, so
#: walking it is the invariant obeyed rather than waived. It is the only read here that is
#: unbounded, and W3's guard holds it in the table for reads whose dependency is everything.
READ_PATH_FOLD_READS = {
    "children":  "CONSTANT",
    "path_of":   "CONSTANT",
    "nlink":     "CONSTANT",
    "snapshot":  "SCANS",
    "lookup":    "CONSTANT",
    "exists":    "CONSTANT",
    "mode":      "CONSTANT",
}


class TestTheReadPathEnumeration(unittest.TestCase):

    def _probe(self, state):
        missing = max(state.inodes) + 10_000
        probe_ino = state.names["/probe"]
        leaf = max(state.inodes)
        return {
            "children": lambda: state.children("/probe"),
            "path_of":  lambda: state.path_of(missing),
            "nlink":    lambda: state.nlink(probe_ino),
            "snapshot": lambda: state.snapshot(),
            "lookup":   lambda: state.lookup("/probe/only"),
            "exists":   lambda: state.exists("/probe/only"),
            "mode":     lambda: state.mode(state.inodes[leaf]),
        }

    def test_every_read_path_fold_read_has_its_verdict_checked(self):
        """T-READ-PATH-ENUMERATED. Small namespace and a four-times-larger one: a
        CONSTANT row must not move, a SCANS row must grow with the namespace."""
        small, _ = _world(10, 4)
        large, _ = _world(40, 4)
        self.assertGreater(len(large.names), 3 * len(small.names))
        ps, pl = self._probe(small), self._probe(large)
        self.assertEqual(sorted(ps), sorted(READ_PATH_FOLD_READS),
                         "the enumeration and the reads actually probed have drifted apart")
        for name, verdict in sorted(READ_PATH_FOLD_READS.items()):
            with self.subTest(read=name, verdict=verdict):
                a, b = _steps(small, ps[name]), _steps(large, pl[name])
                if verdict == "CONSTANT":
                    self.assertEqual((a, b), (0, 0),
                                     f"{name} is declared CONSTANT and walked the namespace")
                else:
                    self.assertGreaterEqual(a, len(small.names),
                                            f"{name} is declared SCANS and did not scan")
                    self.assertGreater(b, a,
                                       f"{name} is declared SCANS and did not grow with the "
                                       "namespace")

    def test_the_enumeration_fails_when_a_new_scanning_read_appears(self):
        """T-ENUMERATION-CAN-FAIL. Without this, the row above proves only that the
        reads it was handed behaved — not that an unlisted one would be caught."""
        state, _ = _world(10, 4)
        planted = lambda: [p for p in state.names if p.endswith("/only")]   # noqa: E731
        self.assertGreaterEqual(_steps(state, planted), len(state.names))
        self.assertNotIn("planted", READ_PATH_FOLD_READS,
                         "the control's own name leaked into the enumeration")


# =====================================================================================
# W1 — the variable: the NAMESPACE, not the record. And the record is not read at all.
# =====================================================================================
class TestTheCostVariableIsTheNamespace(unittest.TestCase):

    def test_growing_the_store_without_growing_the_namespace_costs_nothing(self):
        """T-COST-TRACKS-THE-NAMESPACE. The discriminator ADDENDUM P's two worlds
        cannot draw: records that mint no name are added in bulk and the read does not
        move. So the read is not store-proportional; it is namespace-proportional, and
        the two were confounded because the defconfig world's records were all creates."""
        state, recs = _world(10, 4)
        before = _steps(state, lambda: state.children("/probe"))
        noise = [{"action": "CREATE-INFO", "record_time": 1.0,
                  "payload": {"object": "i:%d" % i, "content": "x"}}
                 for i in range(20 * len(recs))]
        names_before = len(state.names)
        for e in noise:
            state.apply(e)
        self.assertEqual(len(state.names), names_before,
                         "the noise records minted names, so this world proves nothing")
        after = _steps(state, lambda: state.children("/probe"))
        self.assertEqual(before, after,
                         "a twenty-fold larger store changed what the read examined, so the "
                         "variable is the store after all and W1's attribution is wrong")


class TestNoRecordIsReadToServeADirectoryListing(unittest.TestCase):
    """The finding W3 turns on. ADDENDUM C's guard traces `EventStore.all`; if a readdir
    never calls it, that guard is green on this defect at ANY width of path — so
    extending it along the path axis alone cannot see the thing it was extended for.
    Established by tracing the real port, not by reading the source."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="ep28e-")
        os.makedirs(os.path.join(self.work, "blobs"), exist_ok=True)
        rec = os.path.join(self.work, "rec.jsonl")
        open(rec, "w").close()
        store, gate, views, blobs = build_brain(rec, os.path.join(self.work, "blobs"))
        self.port = KernelPort(store, gate, views, blobs)
        self._req("FILE-MKDIR", path="/d", perm="755")
        self._req("FILE-CREATE", path="/d/a", perm="644")
        self.dino = self.port.state.lookup("/d").ino

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def _req(self, op, cls="DECISION", **kw):
        f = {"id": "1", "op": op, "class": cls, "uid": "0", "gid": "0",
             "pid": str(os.getpid())}
        f.update({k: str(v) for k, v in kw.items()})
        status, fields, payload = self.port.handle(f, b"")
        return status, fields, payload

    def _traced_readdir(self, extra=None):
        seen = collections.Counter()
        real = EventStore.all

        def traced(self_, as_of_seq=None):
            frame = traceback.extract_stack()[-2]
            seen["%s.%s" % (os.path.basename(frame.filename)[:-3], frame.name)] += 1
            return real(self_, as_of_seq)

        EventStore.all = traced
        try:
            if extra is not None:
                extra(self.port)
            status, _, payload = self._req("FILL-READDIR", cls="FILL", ino=self.dino)
        finally:
            EventStore.all = real
        return status, payload, seen

    def test_a_directory_listing_reads_zero_records(self):
        """T-READDIR-READS-NO-RECORD."""
        status, payload, seen = self._traced_readdir()
        self.assertEqual(status, 0)
        self.assertEqual(payload, b"a\tf\t%d" % self.port.state.lookup("/d/a").ino)
        self.assertEqual(dict(seen), {},
                         "a directory listing read the record; W1's attribution of the cost "
                         f"to the namespace fold is then incomplete: {dict(seen)}")

    def test_the_trace_can_fail(self):
        """T-THE-TRACE-CAN-FAIL. The row above is an ABSENCE, and an absence proven by an
        instrument nobody made fail is indistinguishable from a broken instrument."""
        def plant(port):
            real_fill = KernelPort._fill_readdir

            def scanning(self_, f):
                len(self_.store.all())
                return real_fill(self_, f)
            KernelPort._fill_readdir = scanning
            self.addCleanup(setattr, KernelPort, "_fill_readdir", real_fill)

        _, _, seen = self._traced_readdir(extra=plant)
        self.assertIn("test_ep28e.scanning", seen,
                      "the trace did not report a whole-record read planted on the readdir "
                      "path, so its silence in the row above means nothing")


# =====================================================================================
# THE TWO ROWS THAT WERE THE DEFECT — FLIPPED, because W2 landed and falsified them
# =====================================================================================
# DOCUMENTED FLIP, EP-28E W2. Both rows below asserted the defect as a fact and said in
# their own text that W2's job was to make them fail. It did, so they are flipped to assert
# the property instead, and the `_TODAY` marker is gone from their names because the thing
# it warned about is no longer true. The defect is not deleted from the record — it is at
# `design/36` ADDENDUM Q and in MEASUREMENTS entry 11, which is where a finding lives.
#
# WHAT THESE ROWS PROVE AND WHAT THEY DO NOT. This file's instrument counts iteration of the
# NAMESPACE, so these rows prove the namespace walk is gone — the whole of the measured
# defect. They cannot prove the positive half of the ruled invariant (that the read costs
# the entries its answer depends on) because a read that touches `kids` and not `names`
# registers zero here either way. That half is `test_ep28e_w3.py`, whose instrument counts
# all four of the fold's structures. Split on purpose, and said so rather than left to look
# like the easy half was the whole claim.
class TestTheDefectIsGone(unittest.TestCase):

    def test_children_no_longer_examines_the_namespace(self):
        """WAS `test_children_examines_the_whole_namespace_TODAY`. `children('/probe')`
        answers about ONE entry, and now examines no namespace at all."""
        state, _ = _world(40, 4)
        entries = len(list(state.children("/probe")))
        walked = _steps(state, lambda: state.children("/probe"))
        self.assertEqual(entries, 1)
        self.assertEqual(walked, 0,
                         "children() walked %d namespace entries to answer about %d — the "
                         "defect design/36 ADDENDUM Q measured is back" % (walked, entries))

    def test_a_lookup_no_longer_pays_a_namespace_scan(self):
        """WAS `test_a_lookup_pays_a_namespace_scan_TODAY`, and it is the row ADDENDUM P §P.2
        is really about: every `FILL-LOOKUP` resolves its parent through `path_of`, so a
        namespace scan there was paid per path component. That is what the extraction
        throughput fall was actually spent on — the row that was FELT rather than measured."""
        state, _ = _world(40, 4)
        deepest = max(state.inodes)
        walked = _steps(state, lambda: state.path_of(deepest))
        self.assertEqual(walked, 0,
                         "path_of walked %d namespace entries to resolve one inode" % walked)

    def test_the_flip_can_fail(self):
        """T-THE-FLIP-CAN-FAIL. Both rows above now assert a ZERO, and a zero is an absence:
        an instrument that stopped counting would report the same zero as a fix. The scanning
        implementations are reinstated as doubles and both rows are required to go red."""
        state, _ = _world(40, 4)

        def scanning_children(self_, path):
            path = custody._norm(path)
            return sorted(custody.basename(c) for c in self_.names
                          if c != path and custody.parent_of(c) == path)

        def scanning_path_of(self_, ino):
            for path, i in self_.names.items():
                if i == ino:
                    return path
            return None

        # DOCUMENTED FLIP, EP-28E W5 — `nlink` joined the CONSTANT rows above, so it joins
        # this control by the same rule: its verdict is now an assertion that the counter saw
        # ZERO, and an instrument that stopped counting reports the same zero as a fix.
        def scanning_nlink(self_, ino):
            node = self_.inodes.get(ino)
            n = sum(1 for i in self_.names.values() if i == ino)
            if node is not None and node.kind == custody.KIND_DIR:
                path = self_.path_of(ino)
                return 2 + sum(1 for c, i in self_.names.items()
                               if custody.parent_of(c) == path and
                               self_.inodes.get(i) is not None and
                               self_.inodes[i].kind == custody.KIND_DIR)
            return n

        real_c, real_p = custody.CustodyState.children, custody.CustodyState.path_of
        real_n = custody.CustodyState.nlink
        custody.CustodyState.children = scanning_children
        custody.CustodyState.path_of = scanning_path_of
        custody.CustodyState.nlink = scanning_nlink
        try:
            walked_c = _steps(state, lambda: state.children("/probe"))
            walked_p = _steps(state, lambda: state.path_of(max(state.inodes)))
            walked_n = _steps(state, lambda: state.nlink(state.names["/probe"]))
        finally:
            custody.CustodyState.children = real_c
            custody.CustodyState.path_of = real_p
            custody.CustodyState.nlink = real_n
        self.assertEqual(walked_c, len(state.names),
                         "the counter did not see the reinstated namespace walk in children, "
                         "so the zero the row above asserts means nothing")
        self.assertGreater(walked_p, len(state.names) // 2,
                           "the counter did not see the reinstated namespace walk in path_of")
        self.assertGreaterEqual(walked_n, 2 * len(state.names),
                                "the counter did not see the reinstated namespace walks in "
                                "nlink, so its CONSTANT verdict means nothing")


if __name__ == "__main__":
    unittest.main()
