# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28E W3 — the guard, on the DEPENDENCY rather than on a variable.

THE SUBJECT, RULED at `design/36` ADDENDUM Q §Q.4 and EP-28E ADDENDUM 1 §1.4, and it is
not this file's to choose:

    a read whose COST IS UNBOUNDED IN SOMETHING ITS ANSWER DOES NOT DEPEND ON.

Not "reads the whole record". Not "reads the whole namespace". Both of those name a
VARIABLE, and a threshold invariant inherits every variable it did not name.

WHY THE VARIABLE FORM WAS REFUSED, and it is the sharpest thing in this EP's pack.
ADDENDUM C's guard watches for reads of the whole HISTORY. A directory listing never reads
the history — proven by tracing, in `test_ep28e.py` — so widening that guard "to every path
that reads the record" is GREEN, at any width of path, over the namespace-proportional read
that commissioned the widening. And the invariant proposed alongside it, *a fill does not
get slower as the system records more*, is SATISFIED by a world of 300,206 records and 207
names while the defect stands — which is how anyone cheaply builds a big test store, so it
would have been tested precisely where it cannot fail. A guard and an invariant both green
over a measured red is the property ADDENDUM P was written to name, and lowering W3 on the
variable axis would have reproduced it inside the EP that found it.

HOW THE DEPENDENCY FORM IS MADE CHECKABLE. For each served read, two worlds are built in
which the read's ANSWER IS IDENTICAL — so everything the answer depends on is held fixed and
SHOWN to be, by comparing the answers — while the namespace and the store both grow. The
work the read does is then counted in both. Identical answer plus more work means the extra
work was spent on something the answer does not depend on, which is the defect, stated
without naming any variable at all.

THE ARM-SET RULE IS MECHANISED HERE rather than trusted (`BUILD-PROMPT-STANDARD`, filed at
this EP's W1 verdict): the guard asserts that its own arms actually differ in the namespace
AND in the store before it believes any row that passes. That is what stops a world-C-shaped
pair — store 100x, namespace flat — from being the ground on which a namespace-proportional
read reports clean, and there is a test below that feeds the guard exactly that pair and
requires it to refuse.

FOUR STRUCTURES ARE COUNTED, NOT ONE. `names`, `kids`, `paths` and `inodes`. An instrument
that counted only the namespace table would report EP-28E W2's own new indexes as free, and
a read that walked all of `kids` would pass a guard written one structure too narrow — the
same error one level down from the one this guard exists to correct. Each of the four is
proven countable by planting a read that walks it and requiring the guard to trip.
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


# =====================================================================================
# THE DECLARATIONS — ADDENDUM C's shape. A declaration states what a read IS.
# =====================================================================================
#: Reads required to cost their own dependencies. Each name maps to the plain-words
#: statement of WHAT ITS ANSWER DEPENDS ON, because a guard that checks a property without
#: recording what the property is about becomes unreadable the first time it fails.
COST_IS_ITS_DEPENDENCY = {
    "children": "the entries bound directly under the one directory asked about",
    "path_of":  "the names the one inode asked about is bound under",
    # DOCUMENTED FLIP, EP-28E W5 (ADDENDUM 2 §2.3c) — `nlink` MOVED here from the defect
    # ledger below, where it sat declared and RAISED because ADDENDUM 1 §1.3 scoped W2 to two
    # lines. It is a move and not a deletion on purpose: `_rows` asserts declared-equals-
    # probed and `test_the_declarations_are_disjoint_and_total` requires exact coverage, so
    # striking the row would fail the drift check rather than record the change.
    "nlink":    "the one inode's bindings, and on a directory that one directory's entries",
    "lookup":   "the one name asked about",
    "exists":   "the one name asked about",
    "mode":     "the one inode asked about",
    "_fill_readdir": "the entries of the one directory, plus that directory's own name",
    "_fill_lookup":  "the parent inode's name and the one child name asked about",
}

#: LAWFULLY UNBOUNDED, and this table is the reason the dependency form is better than the
#: variable form rather than merely different. Under "does not read the whole namespace"
#: `snapshot()` is a violation needing an exemption. Under "costs its own dependencies" it
#: is simply CORRECT: its answer IS the whole namespace, so the whole namespace is its
#: dependency and costing it is the rule being obeyed. No exemption is granted to these —
#: they are outside the fixed-answer test because no arm pair can hold their answer fixed
#: while growing the namespace, and the guard PROVES that below rather than assuming it.
ANSWER_DEPENDS_ON_EVERYTHING = {
    "snapshot": "The comparable form of the WHOLE derived state, which is what shadow-diff "
                "compares and what the conformance harness's replay leg reads. Its answer "
                "is every name and every inode, so its dependency is every name and every "
                "inode. Walking them is the invariant satisfied, not waived.",
}

#: UNBOUNDED IN A NON-DEPENDENCY, DECLARED WITH ITS REASON — the defect ledger, in ADDENDUM
#: C's `WHOLE_RECORD_ON_PATH_BY_DESIGN` shape. Every row here is RAISED in this EP's log
#: entry, not fixed. The guard fails on any unbounded read NOT named here, and on any row
#: here that has stopped being unbounded, so the class stays closed while these stay visible.
#:
#: A DECLARATION IS NEVER A SWITCH. Nothing in `src/` reads these tables — proven below by
#: reading the shipped source, because a declaration that changed behaviour would be a knob
#: wearing a ledger's clothes.
#:
#: DOCUMENTED FLIP, EP-28E W5 — THIS TABLE IS NOW EMPTY, and that is the class closed rather
#: than a ledger nobody filled. Its one row was `nlink`, declared and RAISED at W2 because
#: ADDENDUM 1 §1.3 scoped that work to two lines; W5 landed the replacement and the row MOVED
#: into `COST_IS_ITS_DEPENDENCY` above. No read this file probes is now unbounded in
#: something its answer does not depend on.
#:
#: AN EMPTY LEDGER MAKES `test_no_stale_declaration` PASS BY ITERATING NOTHING, which is a
#: green that means "nobody looked". That vacuity is closed in `tests/test_ep28e_w5.py`,
#: which asserts the emptiness as a finding and then requires the other half of the guard —
#: `test_an_unbounded_read_is_declared_or_the_guard_fails` — to still report a read whose
#: scan has been put back. The table stays here, empty, because the next unbounded read has
#: to have somewhere to be declared.
UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION = {}


# =====================================================================================
# THE INSTRUMENT — four structures, and it is made to fail on each before it is trusted
# =====================================================================================
class _Counter:
    """One shared tally, so a read's total work is one number however many structures it
    touched. Kept as an object rather than a global because two arms are counted
    independently and a leaked count between them would read as a scan."""

    def __init__(self):
        self.steps = 0


class _Counted(dict):
    """A fold structure that counts how many entries an operation WALKS.

    A dict subclass, not a wrapper: `apply()` assigns into, pops from and tests membership
    on these objects, and all of that must keep working untouched. Only ITERATION is
    instrumented, which is the thing whose size is in question. `__contains__`, `get`,
    `__len__` and `__setitem__` stay dict's own and stay constant-time, so a read that uses
    only those registers ZERO and that zero is a real answer about the read.
    """

    def __init__(self, src, counter):
        super().__init__(src)
        self._counter = counter

    def _walk(self):
        for key in list(dict.keys(self)):
            self._counter.steps += 1
            yield key

    def __iter__(self):
        return self._walk()

    def keys(self):
        return self._walk()

    def items(self):
        return ((k, dict.__getitem__(self, k)) for k in self._walk())

    def values(self):
        return (dict.__getitem__(self, k) for k in self._walk())


def _instrument(state):
    """Put every one of the fold's four structures under one tally.

    `kids` and `paths` are dicts OF dicts and the inner ones are what `children` and
    `path_of` walk, so the inner ones are instrumented too — an instrument that stopped at
    the outer dict would report a full walk of a directory's entries as free.

    THE STATE IS READ-ONLY AFTER THIS POINT, and that is a real condition rather than a
    convention: `_bind` creates inner dicts with a plain `{}`, so a name bound after
    instrumenting would land in an uncounted container. Every world here is folded first
    and read after, and `test_the_instrument_covers_every_structure_the_fold_holds` fails if
    a structure is left uncounted.
    """
    c = _Counter()
    state.names = _Counted(state.names, c)
    state.inodes = _Counted(state.inodes, c)
    state.kids = _Counted({k: _Counted(v, c) for k, v in state.kids.items()}, c)
    state.paths = _Counted({k: _Counted(v, c) for k, v in state.paths.items()}, c)
    return c


def _work(counter, fn):
    """The work one read does, and the answer it gave. Both, because the guard's whole
    method is comparing work at a FIXED answer, and an answer nobody compared makes the
    work figures a comparison of two different questions."""
    counter.steps = 0
    answer = fn()
    return counter.steps, answer


# =====================================================================================
# THE ARMS — the dependency held fixed and SHOWN fixed; everything else grown
# =====================================================================================
#: The probe subtree, identical in every arm, inode numbers included. Built FIRST so the
#: filler cannot shift it: `path_of` is asked about inode 2 and has to be asked about the
#: same inode in both arms or the answers are not comparable.
PROBE_DIR, PROBE_DIR_INO = "/probe", 2
PROBE_FILE, PROBE_FILE_INO = "/probe/only", 3


def _records(n_names, n_nameless):
    """One arm's record sequence: the fixed probe subtree, then `n_names` filler names, then
    `n_nameless` records that mint no name at all.

    The two filler counts move the two variables INDEPENDENTLY, which is the whole reason
    this helper takes two arguments. ADDENDUM P's two worlds could not separate store size
    from namespace size because every record in them minted a name; an arm-set that cannot
    vary its variables one at a time cannot attribute anything.
    """
    recs = [
        {"action": "FILE-MKDIR", "record_time": 1.0,
         "payload": {"path": PROBE_DIR, "inode": PROBE_DIR_INO, "perm": "755"}},
        {"action": "FILE-CREATE", "record_time": 1.0,
         "payload": {"path": PROBE_FILE, "inode": PROBE_FILE_INO, "perm": "644"}},
    ]
    ino = 4
    per_dir = 8
    for d in range((n_names // (per_dir + 1)) + 1):
        recs.append({"action": "FILE-MKDIR", "record_time": 1.0,
                     "payload": {"path": "/d%d" % d, "inode": ino, "perm": "755"}})
        ino += 1
        for k in range(per_dir):
            recs.append({"action": "FILE-CREATE", "record_time": 1.0,
                         "payload": {"path": "/d%d/f%d" % (d, k), "inode": ino,
                                     "perm": "644"}})
            ino += 1
    recs += [{"action": "CREATE-INFO", "record_time": 1.0,
              "payload": {"object": "i:%d" % i, "content": "x"}}
             for i in range(n_nameless)]
    return recs


def _arm(n_names, n_nameless):
    recs = _records(n_names, n_nameless)
    state = custody.fold(recs)
    counter = _instrument(state)
    return state, counter, len(recs)


#: The guard's own arms. SMALL and LARGE grow the namespace ~30x and the store ~40x
#: together; the guard checks both growths itself before believing a clean row.
SMALL_NAMES, LARGE_NAMES = 200, 6_000
SMALL_NAMELESS, LARGE_NAMELESS = 100, 20_000


def _probes(state):
    """label -> the read, called so its ANSWER is comparable across arms. Every subject is
    the fixed probe subtree, so two arms asked the same question."""
    node = state.inodes[PROBE_FILE_INO]
    return {
        "children": lambda: state.children(PROBE_DIR),
        "path_of":  lambda: state.path_of(PROBE_DIR_INO),
        "lookup":   lambda: state.lookup(PROBE_FILE).snapshot(),
        "exists":   lambda: state.exists(PROBE_FILE),
        "mode":     lambda: state.mode(node),
        "nlink":    lambda: state.nlink(PROBE_DIR_INO),
        "snapshot": lambda: state.snapshot(),
    }


class TestTheInstrument(unittest.TestCase):
    """The control set. A counter that cannot see a walk of a given structure would report
    every row in this file clean, so it is made to see a walk of each of the four."""

    def setUp(self):
        self.state, self.counter, _ = _arm(SMALL_NAMES, SMALL_NAMELESS)

    def test_the_instrument_covers_every_structure_the_fold_holds(self):
        """T-W3-INSTRUMENT-COVERS-THE-FOLD. Enumerated from the live object rather than
        listed here, so a fifth structure added to `CustodyState` fails this row instead of
        being silently uncounted — which is exactly how the guard would go green over the
        next defect."""
        holds = {name for name, value in vars(self.state).items()
                 if isinstance(value, dict)}
        uncounted = sorted(h for h in holds
                           if not isinstance(getattr(self.state, h), _Counted))
        self.assertEqual(uncounted, [],
                         "the fold holds a dict this instrument does not count, so a read "
                         f"walking it would register zero work: {uncounted}")

    def test_it_sees_a_walk_of_each_structure(self):
        state = self.state
        walks = {
            "names":  lambda: [k for k in state.names],
            "inodes": lambda: [k for k in state.inodes],
            "kids":   lambda: [k for k in state.kids],
            "paths":  lambda: [k for k in state.paths],
        }
        for name, walk in sorted(walks.items()):
            with self.subTest(structure=name):
                steps, _ = _work(self.counter, walk)
                self.assertEqual(steps, len(getattr(state, name)),
                                 f"a deliberate full walk of {name} was not counted")

    def test_it_charges_nothing_to_a_constant_time_operation(self):
        state = self.state
        for label, fn in sorted({
            "get":      lambda: state.names.get(PROBE_FILE),
            "contains": lambda: PROBE_FILE in state.names,
            "len":      lambda: len(state.names),
        }.items()):
            with self.subTest(op=label):
                steps, _ = _work(self.counter, fn)
                self.assertEqual(steps, 0, f"the counter charged steps to a dict {label}")

    def test_it_sees_a_walk_of_an_inner_container(self):
        """The inner dicts of `kids` and `paths` are what the two W2 reads actually walk.
        An instrument stopping at the outer dict would call a full walk of a directory's
        entries free, which is the same error as the guard this file replaces."""
        state = self.state
        steps, _ = _work(self.counter, lambda: [n for n in state.kids["/d0"]])
        self.assertEqual(steps, len(state.kids["/d0"]))
        self.assertGreater(steps, 1)


# =====================================================================================
# THE GUARD
# =====================================================================================
class TestTheDependencyGuard(unittest.TestCase):

    def _arms(self, small=(SMALL_NAMES, SMALL_NAMELESS), large=(LARGE_NAMES, LARGE_NAMELESS)):
        return _arm(*small), _arm(*large)

    def _require_the_arms_differ(self, a, b, msg=""):
        """THE ARM-SET RULE, MECHANISED. A clean row means nothing unless the arms actually
        grew in the things the answer does not depend on. Checked here, once, so no row can
        be believed without it — and this is the method that a world-C-shaped pair fails."""
        (sa, _, reca), (sb, _, recb) = a, b
        self.assertGreater(len(sb.names), 20 * len(sa.names),
                           "the arms do not differ in the NAMESPACE, so a "
                           "namespace-proportional read would pass this guard. " + msg)
        self.assertGreater(recb, 20 * reca,
                           "the arms do not differ in the STORE. " + msg)

    def _rows(self, a, b):
        """Every read, with its work and answer in both arms."""
        (sa, ca, _), (sb, cb, _) = a, b
        pa, pb = _probes(sa), _probes(sb)
        self.assertEqual(sorted(pa), sorted(
            set(COST_IS_ITS_DEPENDENCY) - {"_fill_readdir", "_fill_lookup"}
            | set(ANSWER_DEPENDS_ON_EVERYTHING)
            | set(UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION)),
            "the declared reads and the reads actually probed have drifted apart")
        out = {}
        for name in sorted(pa):
            out[name] = (_work(ca, pa[name]), _work(cb, pb[name]))
        return out

    def test_the_declarations_are_disjoint_and_total(self):
        """A read in two tables at once has two verdicts, which is no verdict."""
        tables = (COST_IS_ITS_DEPENDENCY, ANSWER_DEPENDS_ON_EVERYTHING,
                  UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION)
        seen = set()
        for t in tables:
            overlap = sorted(seen & set(t))
            self.assertEqual(overlap, [], f"declared twice: {overlap}")
            seen |= set(t)

    def _violations(self, a, b):
        """THE GUARD ITSELF, as a function returning what it found.

        A function rather than a test body, and that shape was forced by a defect of this
        seat's own: the first version put the checking inside `subTest` and had the control
        assert that calling it RAISED. `subTest` swallows the AssertionError and files it
        against the outer test, so `assertRaises` saw nothing raised while the failure it
        was looking for was printed two lines above it. The control passed for the wrong
        reason in one direction and failed for the wrong reason in the other.

        Returning findings is also strictly the better instrument: the control can now
        require that the guard names the PLANTED read, rather than merely that something
        somewhere tripped. §A30 root 1 — a check whose own construction satisfied it."""
        rows = self._rows(a, b)
        found = []
        for name in sorted(COST_IS_ITS_DEPENDENCY):
            if name.startswith("_fill"):
                continue
            (work_a, ans_a), (work_b, ans_b) = rows[name]
            if ans_a != ans_b:
                found.append((name, "the arms answered different questions"))
            elif work_b != work_a:
                found.append((name, "answered the SAME question and did %d units of work "
                                    "against %d — the extra was spent on something its "
                                    "answer does not depend on, which is %s"
                                    % (work_b, work_a, COST_IS_ITS_DEPENDENCY[name])))
        return found

    def test_every_read_costs_only_what_its_answer_depends_on(self):
        """T-A-DERIVED-ANSWER-COSTS-ITS-DEPENDENCIES. The guard. The answer is required
        IDENTICAL across the arms first — that is what pins the dependency — and then the
        work is required not to have grown."""
        a, b = self._arms()
        self._require_the_arms_differ(a, b)
        found = self._violations(a, b)
        self.assertEqual(found, [], "; ".join("%s: %s" % f for f in found))

    def test_an_unbounded_read_is_declared_or_the_guard_fails(self):
        """The other half: a read that IS unbounded in a non-dependency has to be in the
        declaration table with its reason. Nothing is discovered; everything is declared."""
        a, b = self._arms()
        self._require_the_arms_differ(a, b)
        rows = self._rows(a, b)
        undeclared = []
        for name, ((work_a, ans_a), (work_b, ans_b)) in sorted(rows.items()):
            if name in ANSWER_DEPENDS_ON_EVERYTHING:
                continue
            if ans_a == ans_b and work_b > work_a:
                if name not in UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION:
                    undeclared.append((name, work_a, work_b))
        self.assertEqual(undeclared, [],
                         "a read is unbounded in something its answer does not depend on "
                         "and is not declared — give it its dependency or declare it with "
                         f"a reason: {undeclared}")

    def test_a_lawfully_unbounded_read_cannot_hold_its_answer_fixed(self):
        """`ANSWER_DEPENDS_ON_EVERYTHING` is PROVEN rather than asserted: if a read's answer
        really is the whole state, then no arm pair that grows the namespace can hold that
        answer fixed. A row here whose answer DID stay fixed while its work grew is an
        ordinary defect hiding behind the wrong table, and this row says so."""
        a, b = self._arms()
        rows = self._rows(a, b)
        for name in sorted(ANSWER_DEPENDS_ON_EVERYTHING):
            (_, ans_a), (_, ans_b) = rows[name]
            with self.subTest(read=name):
                self.assertNotEqual(
                    ans_a, ans_b,
                    f"{name} is declared as depending on everything, yet it gave the SAME "
                    "answer in a much larger world — so its dependency is not everything "
                    "and the declaration is wrong")

    def test_no_stale_declaration(self):
        """T-W3-NO-STALE-DECLARATION, the ADDENDUM C precedent. A declared defect that has
        stopped being one fails, so the ledger cannot outlive what it describes and read as
        coverage."""
        a, b = self._arms()
        rows = self._rows(a, b)
        for name in sorted(UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION):
            (work_a, ans_a), (work_b, ans_b) = rows[name]
            with self.subTest(read=name):
                self.assertEqual(ans_a, ans_b)
                self.assertGreater(
                    work_b, work_a,
                    f"{name} is declared unbounded in a non-dependency and no longer is — "
                    "retire the row, it is now bookkeeping pretending to be coverage")

    # ---- the controls: the guard proven able to fail, on each structure ----------------
    def _plant(self, structure):
        """A read that answers correctly and walks one whole structure on the way. Planted on
        `children`, so the row it must break is a row the guard passes today."""
        real = custody.CustodyState.children

        def scanning(self_, path):
            for _ in getattr(self_, structure):
                pass
            return real(self_, path)

        custody.CustodyState.children = scanning
        self.addCleanup(setattr, custody.CustodyState, "children", real)

    def test_the_guard_trips_on_a_read_unbounded_in_each_structure(self):
        """T-W3-GUARD-CAN-FAIL, and `kids` is the row that matters most. ADDENDUM C's guard
        traces whole-RECORD reads; a read walking all of `kids` reads no record at all, so
        that guard is green on it at any width of path. This one is not."""
        for structure in ("names", "kids", "paths", "inodes"):
            with self.subTest(structure=structure):
                self._plant(structure)
                try:
                    found = self._violations(*self._arms())
                    self.assertEqual(
                        [name for name, _ in found], ["children"],
                        f"a read walking the whole of {structure} was not reported by the "
                        f"guard, or something else was: {found}")
                    self.assertIn("does not depend on", found[0][1])
                finally:
                    self.doCleanups()

    def test_the_guard_refuses_a_world_pair_that_does_not_grow_the_namespace(self):
        """THE RED WORLD BUILT DELIBERATELY, and it is EP-28E ADDENDUM 1 §1.4's condition:
        world C must not make this guard pass.

        World C's shape is 300,206 records and 207 names — store enormous, namespace flat —
        and it is how anyone cheaply builds a big test store. A guard whose arms had that
        shape would report a namespace-proportional read clean. So the arm check is fed
        exactly that pair, with the real namespace-proportional read reinstated, and is
        required to REFUSE the pair rather than to pass the read."""
        # WORLD C's SHAPE at a suite-sized scale: the same namespace in both arms, and a
        # store two orders of magnitude apart. The real world C is 300,206 records at 207
        # names; this generator lands on 207 filler names at 200 requested, so the shape is
        # the same one and only the store's absolute size is smaller. The store ratio is
        # asserted rather than assumed, because a small arm carrying nameless records of its
        # own would cap the ratio below 100 — which is what the first version of this row
        # did, and the row caught it.
        self._plant("names")
        a, b = self._arms(small=(SMALL_NAMES, 0), large=(SMALL_NAMES, 30_000))
        (sa, _, reca), (sb, _, recb) = a, b
        self.assertEqual(len(sa.names), len(sb.names),
                         "this pair was built to hold the namespace flat and did not")
        self.assertGreater(recb, 100 * reca, "this pair was built to grow the store 100x")

        # THE READ IS GENUINELY INVISIBLE ACROSS THIS PAIR. Not an argument — the planted
        # namespace-proportional read is running, and its work is identical in both arms.
        self.assertEqual([], self._violations(a, b),
                         "a namespace-proportional read IS visible across a world-C-shaped "
                         "pair after all, which would make the arm check unnecessary")
        # SO THE ARM CHECK IS WHAT STOPS THE PAIR BEING BELIEVED.
        with self.assertRaises(AssertionError) as caught:
            self._require_the_arms_differ(a, b)
        self.assertIn("NAMESPACE", str(caught.exception))

    def test_a_whole_record_guard_is_green_on_this_defect(self):
        """THE FINDING, PINNED SO NOBODY RE-WIDENS THE WRONG GUARD. ADDENDUM C's instrument
        counts calls to `EventStore.all`. A read that is unbounded in the NAMESPACE makes
        ZERO of them, so widening that instrument along the path axis cannot ever see this
        class.

        Run rather than argued: the namespace-proportional read is reinstated, a directory
        listing is served through the REAL port, `EventStore.all` is traced across it, and
        the trace is required to be empty WHILE the scan is provably happening. The trace is
        proven able to report a planted record read in `test_ep28e.py`, so its silence here
        is a fact about the path rather than about the instrument."""
        import collections
        import traceback as tb
        from kernel.store import EventStore

        work = tempfile.mkdtemp(prefix="ep28e-w3-rec-")
        self.addCleanup(shutil.rmtree, work, True)
        os.makedirs(os.path.join(work, "blobs"), exist_ok=True)
        rec = os.path.join(work, "rec.jsonl")
        open(rec, "w").close()
        store, gate, views, blobs = build_brain(rec, os.path.join(work, "blobs"))
        port = KernelPort(store, gate, views, blobs)
        for op, path in (("FILE-MKDIR", PROBE_DIR), ("FILE-CREATE", PROBE_FILE)):
            port.handle({"id": "1", "op": op, "class": "DECISION", "uid": "0", "gid": "0",
                         "pid": str(os.getpid()), "path": path, "perm": "755"}, b"")
        ino = port.state.lookup(PROBE_DIR).ino

        self._plant("names")
        counter = _instrument(port.state)
        seen, real = collections.Counter(), EventStore.all

        def traced(self_, as_of_seq=None):
            f = tb.extract_stack()[-2]
            seen["%s.%s" % (os.path.basename(f.filename)[:-3], f.name)] += 1
            return real(self_, as_of_seq)

        EventStore.all = traced
        try:
            steps, _ = _work(counter, lambda: port.handle(
                {"id": "1", "op": "FILL-READDIR", "class": "FILL", "uid": "0", "gid": "0",
                 "pid": str(os.getpid()), "ino": str(ino)}, b""))
        finally:
            EventStore.all = real

        self.assertGreaterEqual(
            steps, len(port.state.names),
            "the reinstated namespace-proportional read did not scan, so this row proves "
            "nothing about what a whole-record guard would miss")
        self.assertEqual(
            dict(seen), {},
            "a whole-record read happened, so ADDENDUM C's instrument could after all have "
            f"seen this class and this finding needs restating: {dict(seen)}")

    def test_a_declaration_is_never_a_switch(self):
        """ADDENDUM C's rule, checked mechanically: a declaration states what a read IS and
        changes nothing about what it does. Proven by reading the shipped source — if `src/`
        consulted these tables, they would be a knob."""
        names = ("COST_IS_ITS_DEPENDENCY", "ANSWER_DEPENDS_ON_EVERYTHING",
                 "UNBOUNDED_IN_A_NON_DEPENDENCY_BY_DECLARATION")
        for path in sorted((REPO / "src").rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for n in names:
                self.assertNotIn(n, text,
                                 f"{path.name} reads {n} — a declaration became a switch")


# =====================================================================================
# THE GUARD AT THE PORT — the two fills, on the real bodies
# =====================================================================================
class TestTheFillsCostTheirDependencies(unittest.TestCase):
    """The fold reads are guarded above; a syscall pays a FILL, and a fill's cost is its
    fold reads plus whatever the fill body does itself. Guarding the parts and inferring the
    whole is the composition argument this estate refuses, so the fill bodies are counted.

    THE SUBJECT IS CONSTRUCTED AND THAT IS STATED (charter §A30 root 2). The fill bodies are
    the real `KernelPort` methods, unmodified; what is constructed is the STATE they are
    pointed at, which is folded from records rather than gated into being — because two arms
    30x apart in namespace cannot be built through the gate inside a suite. The first row
    below closes that gap: it drives the real gated port end to end on a small world and
    requires the counted work to match the folded-state figure."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="ep28e-w3-")
        os.makedirs(os.path.join(self.work, "blobs"), exist_ok=True)
        rec = os.path.join(self.work, "rec.jsonl")
        open(rec, "w").close()
        store, gate, views, blobs = build_brain(rec, os.path.join(self.work, "blobs"))
        self.port = KernelPort(store, gate, views, blobs)

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def _req(self, op, cls="DECISION", **kw):
        f = {"id": "1", "op": op, "class": cls, "uid": "0", "gid": "0",
             "pid": str(os.getpid())}
        f.update({k: str(v) for k, v in kw.items()})
        return self.port.handle(f, b"")

    def _fill_work(self, state, which, **f):
        counter = _instrument(state) if not isinstance(state.names, _Counted) else None
        if counter is None:
            counter = state.names._counter
        real_state = self.port.state
        self.port.state = state
        try:
            return _work(counter, lambda: getattr(self.port, which)(
                {k: str(v) for k, v in f.items()}))
        finally:
            self.port.state = real_state

    def test_the_real_gated_port_agrees_with_the_folded_state(self):
        """The construction, closed. A world built through the REAL gate, and the same world
        folded from its own record, are counted on the same fill and must agree."""
        self._req("FILE-MKDIR", path=PROBE_DIR, perm="755")
        self._req("FILE-CREATE", path=PROBE_FILE, perm="644")
        gated = self.port.state
        ino = gated.lookup(PROBE_DIR).ino
        folded = custody.fold(self.port.store.all())
        self.assertEqual(folded.snapshot(), gated.snapshot(),
                         "the folded state is not the gated state, so counting the folded "
                         "one says nothing about the port")
        gw, ga = self._fill_work(gated, "_fill_readdir", ino=ino)
        fw, fa = self._fill_work(folded, "_fill_readdir", ino=ino)
        self.assertEqual(ga, fa)
        self.assertEqual(gw, fw, "the same fill did different work on two states that are "
                                 "equal, so one of them is not what it claims to be")

    def test_the_fills_cost_only_what_their_answers_depend_on(self):
        """T-FILLS-COST-THEIR-DEPENDENCIES. `FILL-READDIR` and `FILL-LOOKUP` on the fixed
        probe subtree, in two arms 30x apart in namespace."""
        small, _, reca = _arm(SMALL_NAMES, SMALL_NAMELESS)
        large, _, recb = _arm(LARGE_NAMES, LARGE_NAMELESS)
        self.assertGreater(len(large.names), 20 * len(small.names))
        self.assertGreater(recb, 20 * reca)
        cases = {
            "_fill_readdir": {"ino": PROBE_DIR_INO},
            "_fill_lookup":  {"parent": PROBE_DIR_INO, "name": "only"},
        }
        for which, args in sorted(cases.items()):
            with self.subTest(fill=which, depends_on=COST_IS_ITS_DEPENDENCY[which]):
                wa, aa = self._fill_work(small, which, **args)
                wb, ab = self._fill_work(large, which, **args)
                self.assertEqual(aa, ab, f"{which} answered differently in the two arms")
                self.assertEqual(wb, wa,
                                 f"{which} answered the same question and did {wb} units of "
                                 f"work against {wa}")

    def test_the_countable_is_the_entries_the_answer_has(self):
        """THE COUNTABLE EP-28E ADDENDUM 1 §1.3 NAMES: entries examined, which for a
        one-entry directory is ONE. Stated as a countable and not as a duration, so the
        property survives a faster machine — and checked in the direction that matters too:
        a hundred-entry directory examines a hundred."""
        state, counter, _ = _arm(LARGE_NAMES, LARGE_NAMELESS)
        steps, answer = _work(counter, lambda: state.children(PROBE_DIR))
        self.assertEqual(answer, ["only"])
        self.assertEqual(steps, 1,
                         "listing a one-entry directory examined %d entries in a %d-name "
                         "namespace" % (steps, len(state.names)))
        wide, wcount, _ = _arm(SMALL_NAMES, SMALL_NAMELESS)
        steps_wide, answer_wide = _work(wcount, lambda: wide.children("/d0"))
        self.assertEqual(steps_wide, len(answer_wide))
        self.assertGreater(steps_wide, 1,
                           "the countable does not move with the answer either, so it is "
                           "measuring nothing")

    def test_the_fill_guard_can_fail(self):
        """The fills' rows above are equalities, and an equality holds trivially if the
        instrument sees nothing. The scanning `children` is reinstated and the readdir fill
        is required to become namespace-proportional again."""
        real = custody.CustodyState.children

        def scanning(self_, path):
            path = custody._norm(path)
            return sorted(custody.basename(c) for c in self_.names
                          if c != path and custody.parent_of(c) == path)

        custody.CustodyState.children = scanning
        try:
            small, _, _ = _arm(SMALL_NAMES, SMALL_NAMELESS)
            large, _, _ = _arm(LARGE_NAMES, LARGE_NAMELESS)
            wa, aa = self._fill_work(small, "_fill_readdir", ino=PROBE_DIR_INO)
            wb, ab = self._fill_work(large, "_fill_readdir", ino=PROBE_DIR_INO)
        finally:
            custody.CustodyState.children = real
        self.assertEqual(aa, ab)
        self.assertGreater(wb, 20 * wa,
                           "reinstating the namespace scan did not make the readdir fill "
                           "cost more in the larger arm, so the equality above is vacuous")


if __name__ == "__main__":
    unittest.main()
