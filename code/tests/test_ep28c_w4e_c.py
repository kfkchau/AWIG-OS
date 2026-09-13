"""EP-28C W4e.C — THE STANDING STOP CLAUSE, RE-ASKED AGAINST THE BUILT DECIDE REGION,
AND IT FIRES.

AMENDMENT 11.2 carries the clause verbatim: *if admitting multiple in-flight requests would
change what any DECLARED operation records or returns — the combinations the declarations
permit, not the traffic you observe — that is a STOP-and-raise naming the operation.*

IT FIRES, ON SEVEN OPERATIONS, AND THE FINDING IS ONE SENTENCE: the port's precondition
read pre-empts the gate's DECLARED check for those seven, so with ONE caller the declared
refusal is unreachable and appends nothing, and with MANY in flight it becomes reachable and
appends an `op-refused` — the same two acts, the same two errnos, and a record stream that
depends on the thread schedule.

NO CHANNEL LINE IS WRITTEN, and that is this file's other assertion rather than the entry's
claim. The clause reserves the disposition to a ruling, so removing `govos_call_lock` while
the clause is unanswered would be improvising around a definitive. The precedent is this
EP's own: `tests/test_ep28c_w4e.py` stopped exactly here in August and was accepted for it.

WHAT IS DIFFERENT FROM THAT EARLIER STOP, so the two are not read as one finding twice. That
one found a race whose outcome was TWO CREATE RECORDS FOR ONE PATH — a wrong world. EP-28K
closed it: the declared check refuses the second create inside the region, and the world that
results here is CORRECT every time (one create record, one name, the same fold). What is left
is not a wrong world. It is a record that says different things about the same history
depending on when two callers happened to arrive, and the direction is the surprising one:
the INTERLEAVED arm records MORE truthfully than the serialized arm, because the serialized
arm's answer comes from a read that appends nothing about a refusal the law declares.

THE DISPOSITION IS ALREADY KNOWN AND IT IS W4e.R (§A24 — a raise derives everything
derivable at zero evidence cost). Retire the port's read and the gate decides every time:
the refusal is always recorded, the record stops depending on the schedule, and the two arms
below converge. `tests/test_ep28c_w4e_r.py` is that retirement's differential and it PASSES
on all nineteen pairs. It did not land because the retirement reds twenty-six rows across
five test files this EP's fence does not name. ONE RULING UNBLOCKS BOTH HALVES.

THE EXPIRY IS BEHAVIOURAL (§A47's extension — an expiry trigger keys on the same KIND of
thing the discharge changes). `test_THE_EXPIRY_*` asserts the DIVERGENCE. When the read
retires, the two arms agree, that row reds, and this file is deleted rather than widened.

===========================================================================================
[THE EXPIRY FIRED AND THE CLAUSE IS DISCHARGED — EP-28C W4e, 2026-08-07. Everything above is
kept as the record of the stop and is now history. Three things about the discharge:

1. THE RETIREMENT LANDED. `_posix_precondition` is gone from `src/bridge/kernel_port.py`,
   after the fence was widened to the six files its reds live in and all thirty-seven rows
   were flipped with each one mapped individually to the retired construct.

2. THE ARMS ARE RE-POINTED, NOT DELETED — and this is the correction to the sentence above
   that says "this file is deleted rather than widened." AMENDMENT 11.2 requires the standing
   clause RE-ASKED against the retired tree, and these two arms ARE that instrument: the same
   two members, the same constructed interleaving, one hold point moved from the read that no
   longer exists to `_params_for`, which is the pre-gate position it occupied. Deleting them
   would have thrown away the only thing that can answer the re-ask, and answered it in prose
   instead. `TestTheClauseFires` is renamed `TestTheClauseIsDISCHARGED` and its rows assert
   CONVERGENCE where they asserted divergence.

3. WHAT THE RE-ASK RETURNS: the two arms agree on both members — one `op-refused` recorded in
   each, the same namespace, the same errno multiset. The record is no longer a function of
   the thread schedule for these seven, which is exactly what the disposition predicted and
   what `test_the_DISPOSITION_converges_*` measured under suppression before it could be
   measured under the retirement.]
==========================================================================================="""

import ast
import errno as E
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from bridge.kernel_port import DECISION_OPS, ERRNO_BY_ACT, KernelPort   # noqa: E402
from bridge.mount import build_brain                                    # noqa: E402
from bridge import custody                                              # noqa: E402

FOUNDING = os.path.join(REPO, "src", "founding", "founding-pack.json")
GOVOSFS_C = os.path.join(REPO, "planning", "vm", "govosfs", "govosfs.c")


def named_by_the_stop():
    """THE SEVEN, COMPUTED FROM THE TABLE RATHER THAN LISTED (§A51).

    An operation is named by this stop when the port answers an outcome for it that the law
    ALSO declares a check for — that is exactly the pre-emption, and it is exactly the key
    set of `ERRNO_BY_ACT`, whose completeness at nineteen is what EP-28N's close established.
    A hand list here would go stale the first time an op joined or left the table, and would
    do it silently, which is the class this estate keeps finding."""
    return {op for op, _requirement in ERRNO_BY_ACT}


def _op_definitions():
    with open(FOUNDING, encoding="utf-8") as fh:
        doc = json.load(fh)
    found = {}

    def walk(o):
        if isinstance(o, list):
            for i in o:
                walk(i)
        elif isinstance(o, dict):
            p = o.get("payload")
            if isinstance(p, dict) and p.get("name") and isinstance(p.get("definition"), dict):
                found[p["name"]] = p["definition"]
            for v in o.values():
                walk(v)

    walk(doc)
    return found


def _wire(op, **kw):
    f = {"id": "1", "op": op, "class": "DECISION",
         "uid": "1000", "gid": "1000", "pid": "42"}
    f.update({k: str(v) for k, v in kw.items()})
    return f


class _World:
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="w4e-c-")
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, op, **kw):
        return self.port.handle(_wire(op, **kw), b"")[0]

    def added_since(self, n, action):
        return [r for r in self.store.all()[n:] if r.get("action") == action]


def serialized_arm(op, path, extra):
    """WHAT THE ONE-CALLER CHANNEL GUARANTEES: the second act runs after the first act's
    record is folded.

    DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. The `read_on` parameter is GONE with its
    subject. It defaulted True and ran the port's precondition read; `read_on=False`
    suppressed exactly that read to stand in W4e.R's world before W4e.R existed. THE
    RETIREMENT LANDED, so there is one world, the suppression has nothing to suppress, and a
    parameter that varies nothing is a lie in the signature."""
    w = _World()
    try:
        for sop, skw in extra:
            assert w.call(sop, **skw) == 0, (sop, skw)
        # THE WINDOW OPENS BEFORE BOTH CALLS, SYMMETRICALLY WITH THE OTHER ARM. Opening it
        # after the first call made the two arms count over different spans, and the row
        # that caught it was the non-vacuity clause — which is what non-vacuity is for.
        n = len(w.store.all())
        before = sorted(set(w.port.state.names))
        first = w.call(op, **path)
        second = w.call(op, **path)
        return (first, second,
                len(w.added_since(n, "op-refused")),
                len(w.added_since(n, op)),
                sorted(set(w.port.state.names)), before)
    finally:
        w.close()


def interleaved_arm(op, path, extra):
    """WHAT MANY IN FLIGHT PERMITS, DETERMINISTICALLY AND NOT BY LUCK.

    Two events and one order, no sleeps and no retries, and the order is stated exactly
    because a comment that describes a mechanism other than the one running is the defect
    this estate keeps finding. Thread A takes its pre-gate reads and is HELD AT THE GATE'S
    DOOR, before entering the region. Thread B is then released, takes its own pre-gate
    reads, and goes through the gate first, taking the name. A is released only once B's
    reads have answered, enters the region behind B, and meets the DECLARED check.

    SO B SUCCEEDS AND A IS REFUSED, EVERY RUN. There is no race left in this arm: both
    events are set by the code under test rather than waited for, which is what makes this a
    constructed interleaving and not a row that passes when a race does not happen.

    DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ARM WAS READING:
    `w.port._posix_precondition`, read into `real_pre` and wrapped so that B could announce
    it had taken its pre-gate read. The attribute is gone.

    THE HOLD POINT MOVES TO `_params_for`, WHICH IS THE POSITION THE READ OCCUPIED — the last
    pre-gate call on the decide path, taken by every one of the seven, still outside the
    region (`tests/test_ep28c_w4e.py` asserts that from behaviour, not from source). The
    interleaving is the SAME interleaving: A is at the gate's door, B has completed its
    pre-gate reads, and the order they reach the region in is the varied thing."""
    w = _World()
    try:
        for sop, skw in extra:
            assert w.call(sop, **skw) == 0, (sop, skw)
        a_at_the_gate_door = threading.Event()
        b_read_done = threading.Event()
        real_params = w.port._params_for
        real_exec = w.gate.execute

        def pre(o, f, payload):
            # THE WRAPPER IS THE SIGNAL AND THE READ IS WHAT IT SIGNALS ABOUT, kept apart on
            # purpose: B must announce that it has reached this point, and the announcement
            # must not change what the read returns.
            answer = real_params(o, f, payload)
            if threading.current_thread().name == "B":
                b_read_done.set()
            return answer

        def ex(name, actor, params=None):
            if threading.current_thread().name == "A":
                a_at_the_gate_door.set()
                b_read_done.wait(20)
            return real_exec(name, actor, params)

        w.port._params_for = pre
        w.gate.execute = ex
        out = {}

        def run(tag):
            out[tag] = w.call(op, **path)

        n = len(w.store.all())
        before = sorted(set(w.port.state.names))
        ta = threading.Thread(target=run, args=("A",), name="A")
        tb = threading.Thread(target=run, args=("B",), name="B")
        ta.start()
        if not a_at_the_gate_door.wait(20):
            b_read_done.set()
            ta.join(20)
            raise AssertionError("thread A never reached the gate door — the arm did not run")
        tb.start()
        ta.join(30)
        tb.join(30)
        return (out.get("A"), out.get("B"),
                len(w.added_since(n, "op-refused")),
                len(w.added_since(n, op)),
                sorted(set(w.port.state.names)), before)
    finally:
        w.close()


#: THE ACTS DRIVEN BY BOTH ARMS — TWO MEMBERS, ON TWO DIFFERENT REQUIREMENTS, because §A49
#: binds: a property observed in one member of a declared set is a property of THAT MEMBER
#: until a second is checked. `FILE-CREATE` asks `binding:unbound` (the name must be free)
#: and `FILE-UNLINK` asks `binding:bound` (the name must be held) — opposite questions under
#: one law, so a mechanism that only worked for absence would be caught here.
#:
#: Each is (op, the act's wire fields, the setup that builds its world). Both are chosen with
#: no container clause, so the two arms differ in ONE thing and not in two.
ACTS = (
    ("FILE-CREATE", {"path": "/a", "perm": "644"}, ()),
    ("FILE-UNLINK", {"path": "/u"}, (("FILE-CREATE", {"path": "/u", "perm": "644"}),)),
)


class TestTheSubjectExists(unittest.TestCase):
    """NON-VACUITY FIRST. Every row below compares two arms, and two arms that both did
    nothing agree perfectly."""

    def test_the_seven_named_operations_are_all_declared_in_the_founding(self):
        defs = _op_definitions()
        self.assertGreaterEqual(len(defs), 1, "no op definitions were read at all")
        named = named_by_the_stop()
        self.assertEqual(len(named), 7, "the stop names %d operations, not seven" % len(named))
        missing = sorted(n for n in named if n not in defs)
        self.assertEqual(missing, [], "the stop names an operation the founding does not "
                                      "declare — the enumeration has gone stale")
        self.assertEqual(sorted(n for n in named if n not in DECISION_OPS), [],
                         "the stop names an operation this port does not serve")

    def test_every_named_operation_declares_the_check_the_ports_read_pre_empts(self):
        """The pre-emption stated as a property of the LAW rather than of the port: each of
        the seven declares at least one check whose requirement the port renders, which is
        what makes the port's earlier answer a pre-emption and not an independent concern."""
        from kernel.opdefs import declared_requirements
        defs = _op_definitions()
        without = []
        for name in sorted(named_by_the_stop()):
            declared = set(declared_requirements(defs[name]))
            rendered = {r for (o, r) in ERRNO_BY_ACT if o == name}
            if not (declared & rendered):
                without.append(name)
        self.assertEqual(without, [],
                         "an operation this stop names declares no check the port's read "
                         "could pre-empt, so the finding's own subject would be wrong: %r"
                         % (without,))

    def test_both_arms_actually_act_in_both_members_and_leave_a_real_world(self):
        for op, path, extra in ACTS:
            want = -E.EEXIST if op == "FILE-CREATE" else -E.ENOENT
            for label, arm in (("serialized", serialized_arm),
                               ("interleaved", interleaved_arm)):
                first, second, _ref, acts, names, before = arm(op, path, extra)
                self.assertEqual(acts, 1,
                                 "%s/%s: the world holds %d %s records, so the arm did not "
                                 "act" % (label, op, acts, op))
                # THE ACT CHANGED THE WORLD, WHICHEVER DIRECTION. A `len(names) > 1` clause
                # was written here first and was wrong for the second member: an unlink that
                # worked leaves the root alone, so the clause called a successful act a dead
                # arm. The op-agnostic statement is that the namespace MOVED.
                self.assertNotEqual(names, before,
                                    "%s/%s: the namespace did not move, so the arm did not "
                                    "act on the world" % (label, op))
                self.assertEqual(sorted({first, second}), sorted([want, 0]),
                                 "%s/%s: the two callers did not get one success and one %d"
                                 % (label, op, want))


class TestTheClauseIsDISCHARGED(unittest.TestCase):
    """THE STANDING STOP CLAUSE, RE-ASKED AGAINST THE RETIRED TREE — AMENDMENT 11.2's own
    requirement, driven rather than reasoned.

    RENAMED AND NOT ONLY FLIPPED (EP-28C W4e, 2026-08-07). It was `TestTheClauseFires`, and a
    class named for a clause firing whose rows assert convergence carries a repealed finding
    in its name.

    THE CLAUSE, VERBATIM: *if admitting multiple in-flight requests would change what any
    DECLARED operation records or returns — the combinations the declarations permit, not the
    traffic you observe — that is a STOP-and-raise naming the operation.*

    ASKED AGAINST THIS TREE IT DOES NOT FIRE FOR THE SEVEN, and the two arms are why. Same
    two members on opposite requirements, same constructed interleaving, and the record they
    leave is now identical. The clause fired before because the port's read pre-empted the
    declared check under one caller and could not under many; with no read in front of the
    gate there is no schedule left for the record to depend on."""

    def test_THE_DISCHARGE_both_arms_record_the_same_refusal_for_both_members(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `serialized_arm`/`interleaved_arm` with the port's precondition read LIVE,
        under `assertEqual(s_ref, 0)` — "the port's read is an ABSENCE and appends nothing" —
        against `assertEqual(i_ref, 1)`, whose own failure message named this discharge.

        THE ARMS NOW AGREE AND THE ROW ASSERTS THE AGREEMENT. Everything the old row asserted
        about what does NOT move is kept unchanged, because a convergence over two arms that
        built different worlds would not be a discharge."""
        for op, path, extra in ACTS:
            s_first, s_second, s_ref, s_acts, s_names, _sb = serialized_arm(op, path, extra)
            i_a, i_b, i_ref, i_acts, i_names, _ib = interleaved_arm(op, path, extra)

            # WHAT DOES NOT MOVE — asserted first, because a convergence between two arms
            # that acted on different worlds says nothing about the clause.
            self.assertEqual(s_names, i_names, "%s: different namespaces" % op)
            self.assertEqual(s_acts, i_acts,
                             "%s: the two arms recorded different numbers of acts — that "
                             "would be EP-28K's race returning, not this clause" % op)
            self.assertEqual(sorted({s_first, s_second}), sorted({i_a, i_b}),
                             "%s: the two arms answered their callers differently" % op)

            # NON-VACUITY: two arms that both did nothing agree perfectly.
            self.assertEqual(s_acts, 1, "%s: the serialized arm did not act" % op)
            self.assertEqual(i_acts, 1, "%s: the interleaved arm did not act" % op)

            # THE DISCHARGE.
            self.assertEqual(s_ref, i_ref,
                             "%s: THE CLAUSE FIRES AGAIN — the two arms disagree about the "
                             "record (%d vs %d), so admitting many in flight changes what a "
                             "DECLARED operation records. STOP and raise, naming this "
                             "operation." % (op, s_ref, i_ref))
            self.assertEqual(s_ref, 1,
                             "%s: the arms agree on recording NOTHING, so the declared "
                             "check is not deciding and this row measures nothing" % op)

    def test_the_refusal_both_arms_record_cites_the_DECLARED_law(self):
        """The second half of the same discharge, kept separate because equality of COUNTS is
        not identity of RECORDS. Two arms could each append one refusal for different reasons
        and satisfy the row above."""
        for op, path, extra in ACTS:
            for label, arm in (("serialized", serialized_arm), ("interleaved", interleaved_arm)):
                w = _World()
                try:
                    for sop, skw in extra:
                        assert w.call(sop, **skw) == 0, (sop, skw)
                    n = len(w.store.all())
                    w.call(op, **path)
                    w.call(op, **path)
                    refusals = w.added_since(n, "op-refused")
                    self.assertEqual(len(refusals), 1,
                                     "%s/%s: %d refusals" % (label, op, len(refusals)))
                    self.assertEqual(refusals[0]["rule_cited"], "FS-LAW-NAMESPACE",
                                     "%s/%s: the recorded refusal does not cite the declared "
                                     "law, so it is not the gate's answer" % (label, op))
                finally:
                    w.close()


class TestTheSecondThingManyInFlightReaches(unittest.TestCase):
    """A RAISE, DRIVEN RATHER THAN ASSERTED, and it is capped: it is NOT a second instance
    of the stop clause, because the clause's subject is DECLARED operations and the subject
    here is FILLS, which declare nothing and record nothing.

    THE OBSERVATION: the fold is ADVANCED inside the decide region — the store's on-append
    listener runs on the appending thread, inside the region's span — and it is READ by
    every fill from outside every region. With one caller that composition cannot be
    observed, because no fill can run while a decide is between two of its own mutations.
    Many in flight is exactly the condition that makes it observable: a `FILL-LOOKUP` or a
    `FILL-READDIR` concurrent with a decide can answer about a state that no record boundary
    describes — a name bound whose node the fold has not finished installing.

    WHAT IS NOT CLAIMED, so the cap is on the row and not only in the entry: this is NOT a
    torn dict and NOT a wrong record. Each individual read is atomic under CPython, the
    served state converges the moment the apply completes, and `_fill_readdir` already skips
    a name whose lookup answers None. What is unestablished is that a fill's answer is a
    read of ONE fold state, and nothing in this estate has ever needed it to be, because
    nothing has ever read the fold concurrently with an append through the real port.

    THE TWO OBSERVATIONS BELOW ARE ONE PREDICATE ANSWERED TWICE — True where the fold moves,
    False where it is read. One observation alone would be satisfied by a predicate that
    always answered the same thing."""

    def test_the_fold_is_advanced_with_the_region_HELD(self):
        from kernel.gate import decide_region_held
        w = _World()
        try:
            seen = []
            real_apply = w.port.state.apply

            def watched(record):
                seen.append(decide_region_held())
                return real_apply(record)

            w.port.state.apply = watched
            self.assertEqual(w.call("FILE-CREATE", path="/a", perm="644"), 0)
            w.port.state.apply = real_apply
            self.assertTrue(seen, "non-vacuity: the fold was advanced at all")
            self.assertEqual(set(seen), {True},
                             "the fold advanced with the region NOT held: %r" % (seen,))
        finally:
            w.close()

    def test_a_fill_reads_that_same_fold_with_the_region_NOT_held(self):
        from kernel.gate import decide_region_held
        w = _World()
        try:
            self.assertEqual(w.call("FILE-CREATE", path="/a", perm="644"), 0)
            seen = []
            real_lookup = w.port.state.lookup

            def watched(path):
                seen.append(decide_region_held())
                return real_lookup(path)

            w.port.state.lookup = watched
            status, fields, _payload = w.port.handle(
                _wire("FILL-LOOKUP", **{"class": "FILL", "parent": "1", "name": "a"}), b"")
            w.port.state.lookup = real_lookup
            self.assertEqual(status, 0, "non-vacuity: the fill answered")
            self.assertTrue(fields.get("ino"), "non-vacuity: the fill answered about a node")
            self.assertTrue(seen, "non-vacuity: the fill read the fold at all")
            self.assertEqual(set(seen), {False},
                             "a fill now reads the fold inside the region — the raise is "
                             "discharged and this class should be deleted: %r" % (seen,))
        finally:
            w.close()


class TestWhatSERIALIZESTheFoldsWriterAgainstAFillsReadIsThePORT(unittest.TestCase):
    """RENAMED FROM `TestWhatSERIALIZESTheFoldsWriterAgainstAFillsReadIsTheCHANNEL` —
    EP-28R W4, mentor-ruled and landed 2026-08-07. THE `AppendNothing` TREATMENT: what this
    class asserted is KEPT below, marked with what superseded it and when. It is not scrubbed.

    WHY THE HISTORY STAYS RATHER THAN BEING TIDIED AWAY: these rows are the reason shape (a)
    was ruled at all. They named a composition nobody had asked about, and the pass that
    answered it exists because they did. A docstring rewritten to describe only the landing
    would erase the finding that produced the landing, and this estate would then hold a lock
    whose reason nobody could reconstruct.

    ── WHAT THIS CLASS ASSERTED, AND IT WAS TRUE WHEN WRITTEN (EP-28C W4e, 2026-08-07) ──

    THE HALF OF RAISE 3 NOBODY HAD ASKED, AND IT IS WHY W4e.C STOPPED. Raise 3 established
    the two positions and the mentor ruled them correctly NOT a second instance of the
    standing stop clause, because fills declare nothing. Both hold. What neither asked is the
    composition question: if the fold's WRITER runs inside the decide region and a fill's
    READER runs outside every region, WHAT keeps them apart?

    READ FROM THE CODE, NOT PROBED. `KernelPort` holds no lock of its own: its `_on_append`
    advances `self.state` and `self.locks` from whichever thread appended, and that thread is
    inside `gate.execute`'s region because `store.append` fires its listeners before it
    returns. `_fill_readdir` and `_fill_lookup` read the same fold and take no region at all.
    Nothing in this process orders those two. What orders them is `govos_call_lock` in
    `planning/vm/govosfs/govosfs.c` — ONE CALLER IN THE CHANNEL AT A TIME — which is the
    exact lowering AMENDMENT 11.2 orders removed.

    SO THE ITEM'S TWO HALVES ARE NOT INDEPENDENT. "The user-space half submits concurrently"
    is not a change to the user-space half alone: it withdraws the only thing serializing a
    fill's read of the port fold against the fold's own advance. THIS IS EP-28G'S FINDING ONE
    LAYER UP — a lock that single-threading was silently supplying — and EP-28G is the
    precedent that a lock of this kind is its own ruled pass and not an item's side effect.

    WHAT WAS NOT CLAIMED, and the cap was on the rows rather than only in the entry: nothing
    here was exhibited failing, and nothing here constructed a failing input. These rows
    asserted what the code IS — no lock in the port, a writer inside a region, a reader
    outside one, and a transport that admits one caller — and the consequence was derived
    from those four facts, stated, and RAISED for a ruling.

    ── WHAT SUPERSEDED IT, AND WHEN (EP-28R, 2026-08-07) ──

    THE CAP CAME OFF FIRST. EP-28R W1 was authored to EXHIBIT OR REFUTE the derivation above
    before anything else ran, and IT EXHIBITED IT: with the fold's writer held between a
    rename's two mutations, `FILL-READDIR` answers an empty listing for a directory holding
    one entry and `FILL-LOOKUP` answers ENOENT for a live file. The four read-derived rows
    were right, and they are now driven rather than derived.

    THEN THE ANSWER LANDED, AND IT MOVED THIS CLASS'S SUBJECT. EP-28R W3 ruled shape (a) —
    LOCK THE FOLD AT THE PORT — and W4 landed it. `KernelPort` now constructs exactly one
    re-entrant primitive, `_fold_order`, taken by `_on_append` across the whole advance and by
    both fold-reading fills across their whole read. **SO WHAT SERIALISES THE FOLD'S WRITER
    AGAINST A FILL'S READ IS THE PORT, AND THIS CLASS IS NAMED FOR THAT.**

    WHAT IS STILL TRUE AND STILL ASSERTED BY THE ROWS BELOW: the writer still runs from
    inside the appending thread's region, a FILL still walks a container a DECISION does not,
    and the channel's one-caller lowering is STILL IN PLACE — so the tear these rows describe
    stays LATENT rather than live, and the last row is what says so. What changed is that the
    channel is no longer the ONLY thing keeping them apart.

    ── THE MENTOR'S OWN DEFECT, IN ITS WORDS, BECAUSE IT BELONGS IN THE FILE IT LANDED ON ──

    The ruling that repointed this class's lock row said "RENAME IT, DO NOT ONLY FLIP IT",
    citing the `AppendNothing` precedent — and then named the ROW and not the CONTAINER that
    describes it. THE SAME DEFECT ONE LEVEL UP, INSIDE THE RULING THAT CITED THE PRECEDENT.
    The builder refused to widen the fence on its own and returned it as its own item; the
    refusal was ruled CORRECT and the fence extended by exactly this one item."""

    def _port_source(self):
        with open(os.path.join(REPO, "src", "bridge", "kernel_port.py"),
                  encoding="utf-8") as fh:
            return fh.read()

    #: §A64, on this class's own generalisation: the claim is that the PORT TAKES NO LOCK,
    #: whatever a lock is spelled. One construct that should match, spelled differently; one
    #: that should not, spelled similarly.
    NEAR_MISS_SHOULD_MATCH = '''
import threading
class KernelPort:
    def __init__(self):
        self._guard = threading.RLock()      # a lock under a name this file has never seen
    def _on_append(self, record):
        with self._guard:
            self.state.apply(record)
'''

    NEAR_MISS_SHOULD_NOT_MATCH = '''
class KernelPort:
    def _params_for(self, op, f, payload):
        # the word lock appears here and takes nothing: FILE-LOCK is an OPERATION NAME.
        if op in ("FILE-LOCK", "FILE-UNLOCK"):
            return {"ltype": f.get("ltype"), "owner": f.get("owner")}
'''

    def _lock_constructs(self, src):
        """Every place this source CONSTRUCTS or ENTERS a mutual-exclusion primitive.

        Keyed on the construct and not on the word: `threading.Lock()` / `RLock()` /
        `Semaphore()` / `Condition()` built, or a `with <expr>:` over one, or an `.acquire()`
        call. An operation whose NAME contains "lock" is not a lock."""
        tree = ast.parse(src)
        found = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                if n.func.attr in ("Lock", "RLock", "Semaphore", "Condition", "BoundedSemaphore"):
                    found.append(n.func.attr)
                elif n.func.attr == "acquire":
                    found.append("acquire")
        return found

    def test_NEAR_MISS_a_lock_under_a_name_this_file_never_saw_is_still_found(self):
        self.assertTrue(self._lock_constructs(self.NEAR_MISS_SHOULD_MATCH),
                        "the walk cannot see a lock built under an unfamiliar attribute "
                        "name, so the emptiness it reports about the port proves nothing")

    def test_NEAR_MISS_an_operation_named_LOCK_is_not_a_lock(self):
        self.assertEqual(self._lock_constructs(self.NEAR_MISS_SHOULD_NOT_MATCH), [],
                         "an op NAMED lock was counted as a mutual-exclusion primitive, so "
                         "the walk is reading the word and not the construct")

    def test_the_port_takes_EXACTLY_ONE_ORDERING_and_its_CONSEQUENCE_IS_RE_DERIVED(self):
        """THE TRIPWIRE FIRED AND THIS IS ITS DISCHARGE — EP-28R W4, mentor-ruled 2026-08-07.

        WHAT STOOD HERE was `test_the_PORT_ITSELF_TAKES_NO_LOCK`, and its message was never
        an assertion that the port must never lock: "the port now takes a lock of its own —
        the composition this class is about has changed and its consequence must be
        re-derived." The port now takes one, by ruling. So this row is repointed onto the
        composition that REPLACED the one it was watching, and the re-derivation it demanded
        is CITED rather than assumed — a tripwire silenced without the derivation it asked
        for is worse than the composition it was watching.

        THE RE-DERIVATION, BY NAME, in `tests/test_ep28r.py`:
          - test_the_fills_ordering_and_the_stores_write_lock_are_DIFFERENT_LOCKS
          - test_the_ORDERING_IS_NOT_HELD_ACROSS_fdatasync
          - test_A_FILL_TAKES_NO_STORE_LOCK_so_the_order_is_TOTAL_and_no_cycle_exists
          - test_THE_INVERSION_IS_REAL_AND_ITS_REACH_IS_RECORDED

        THOSE NAMES ARE RESOLVED, NOT MERELY WRITTEN. `tests/test_ep28r.py`'s
        `TestTheTRIPWIRES_RE_DERIVATION_IS_CITED_AND_RESOLVED` reads this docstring and
        requires every cited name to exist as a row in that file, with near-misses both ways
        — so the citation cannot rot into prose, and cannot name a row nobody wrote.

        WHAT THIS ROW ASSERTS NOW: the port constructs EXACTLY ONE mutual-exclusion
        primitive, and it is RE-ENTRANT. Not zero, because the ruling is that it takes one.
        Not two, because a second primitive in this file is a lock ORDER nobody derived, and
        that is the next composition worth a tripwire. Not a plain `Lock`, because the fold's
        writer is reached twice down one thread's stack — the dual-audit mirror appends from
        inside the on-append callback — so a non-re-entrant one deadlocks the appender
        against itself. THE CLASS'S OWN CONSEQUENCE HAS MOVED WITH IT: what serialises the
        fold's writer against a fill's read is no longer only the CHANNEL, it is this port.
        The channel's one-caller lowering is still in place and this class's last row still
        asserts it; what changed is that it is no longer the ONLY thing.

        INSTRUMENT UNCHANGED, so the flip is in the claim and not in the measurement:
        `_lock_constructs` is keyed on the CONSTRUCT and not on the word, and this class's
        two near-miss rows above still hold it both ways."""
        self.assertEqual(self._lock_constructs(self._port_source()), ["RLock"],
                         "the port's ordering has changed shape — the composition this "
                         "class is about has moved again and its consequence must be "
                         "re-derived a second time, exactly as it was in EP-28R W4")

    def test_the_folds_writer_runs_from_inside_gate_execute(self):
        """Structural, on the two facts that put the writer inside the region: the store
        publishes to its listeners from within `append`, and the port registers `_on_append`
        as one of them. The behavioural half — the region predicate answering True there —
        is the class above and is not repeated here."""
        with open(os.path.join(REPO, "src", "kernel", "store.py"), encoding="utf-8") as fh:
            store_src = fh.read()
        tree = ast.parse(store_src)
        # THE PUBLISHER IS FOUND, NOT NAMED. `_append_one` is where it lives today; a rename
        # or a move must not make this row answer "no publisher" and pass by absence, so the
        # function is located by what it DOES — iterating the listener list — and the row
        # asserts that exactly one function does it.
        publishers = sorted(
            n.name for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and any(isinstance(c, ast.Attribute) and c.attr == "_listeners"
                    and isinstance(c.ctx, ast.Load)
                    and not isinstance(getattr(c, "parent", None), ast.Call)
                    for c in ast.walk(n))
            and n.name != "on_append")
        self.assertEqual(len(publishers), 1,
                         "the store publishes to its listeners from %r — the fold's writer "
                         "is not where this class says it is" % (publishers,))
        port_tree = ast.parse(self._port_source())
        registers = [n for n in ast.walk(port_tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "on_append"]
        self.assertTrue(registers, "the port no longer registers an on-append listener")

    def test_the_EXPOSED_class_is_the_FILL_and_the_decide_path_is_NOT(self):
        """THE RAISE IS PRICED RATHER THAN GENERAL, and the narrowing is what makes it
        actionable: not every request meets the unordered read.

        DRIVEN ON THE PREDICATE, ONE FOLD CALL AT A TIME. Every method the fold offers is
        wrapped, one handler of each class is run through the real `handle`, and the calls
        each class makes are collected. What separates them is not the name of the method
        but whether the call ITERATES a container the fold's writer mutates: `lookup` and
        `exists` are single-key dict reads, and `children` returns
        `sorted(self.kids.get(...))`, which walks one.

        WHAT THIS ESTABLISHES: a DECISION's fold reads are single-key; a FILL's readdir walks
        a container. So the exposure the channel would open is the FILL class's, which is
        also why it is correctly NOT the standing stop clause — fills declare nothing. The
        stop is a composition finding, not a clause firing, and this row is why the raise can
        say which requests are in it."""
        w = _World()
        try:
            self.assertEqual(w.call("FILE-MKDIR", path="/d", perm="755"), 0)
            self.assertEqual(w.call("FILE-CREATE", path="/d/a", perm="644"), 0)
            seen = {}
            real = {name: getattr(w.port.state, name)
                    for name in ("lookup", "exists", "children")}

            def wrap(name, tag):
                def go(*a, **k):
                    seen.setdefault(tag, []).append(name)
                    return real[name](*a, **k)
                return go

            dino = custody.render_ino(w.port.state.lookup("/d").ino)
            for tag, req in (("DECISION", _wire("FILE-CREATE", path="/d/a", perm="644")),
                             ("FILL", _wire("FILL-READDIR", **{"class": "FILL",
                                                               "ino": dino}))):
                for name in real:
                    setattr(w.port.state, name, wrap(name, tag))
                try:
                    status, _f, _p = w.port.handle(req, b"")
                finally:
                    for name, fn in real.items():
                        setattr(w.port.state, name, fn)
                if tag == "FILL":
                    self.assertEqual(status, 0, "non-vacuity: the readdir fill answered")

            self.assertTrue(seen.get("FILL"), "non-vacuity: the fill read the fold at all")
            self.assertIn("children", seen["FILL"],
                          "the readdir fill no longer walks the container the fold's writer "
                          "mutates, so this raise's subject has moved")
            self.assertNotIn("children", seen.get("DECISION", []),
                             "a DECISION now walks the fold's container too — the exposure "
                             "is wider than this raise prices it, and the stop covers the "
                             "decide path as well")
        finally:
            w.close()

    def test_the_transport_is_what_admits_ONE_caller_and_it_is_still_in_place(self):
        """The fourth fact, and the one that makes the other three a stop rather than an
        observation: the serialization is the CHANNEL's, so removing it is what withdraws it.
        Asserted here against the same source `TestTheChannelWasNotTouched` reads, because
        this class's conclusion rests on it and a conclusion resting on another class's row
        is a conclusion nobody re-checks."""
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            c_src = fh.read()
        self.assertIn("govos_call_lock", c_src,
                      "the one-caller lowering is gone: the fill path's read of the port "
                      "fold is now unordered against the fold's own advance, and this "
                      "class's raise has become a live condition rather than a stop")


class TestTheChannelWasNotTouched(unittest.TestCase):
    """W4e.C WROTE NO CHANNEL LINE, and the rows prove it rather than the entry claiming it.

    §A64 binds the structural walk: a DRIVEN near-miss both ways. THE GENERALISATION CLAIMED
    is that the one-caller lowering is IN PLACE — a lock taken around the whole crossing —
    so the near-misses run on that axis: a lowering spelled differently must still be seen,
    and a mention of the lock that takes nothing must not be mistaken for one."""

    NEAR_MISS_SHOULD_MATCH = '''
static DEFINE_MUTEX(govos_call_lock);
static int govos_call(const struct govos_msg *m, struct govos_reply *out)
{
	/* spelled differently and it is the same construct */
	mutex_lock( &govos_call_lock );
	mutex_unlock(&govos_call_lock);
	return 0;
}
'''

    NEAR_MISS_SHOULD_NOT_MATCH = '''
/* A comment naming govos_call_lock and mutex_lock(&govos_chan_mutex) and nothing else. */
static DEFINE_MUTEX(govos_chan_mutex);
static int govos_call(const struct govos_msg *m, struct govos_reply *out)
{
	mutex_lock(&govos_chan_mutex);
	mutex_unlock(&govos_chan_mutex);
	return 0;
}
'''

    def _lowering_present(self, src):
        """Is the whole-crossing lock DECLARED and TAKEN? Both halves, because a declaration
        nobody takes is a dead symbol and a take with no declaration will not build — the
        construct is the pair."""
        import re
        declared = re.search(r"DEFINE_MUTEX\(\s*govos_call_lock\s*\)", src) is not None
        taken = re.search(r"mutex_lock\(\s*&\s*govos_call_lock\s*\)", src) is not None
        return declared and taken

    def test_the_one_caller_lowering_is_still_in_place(self):
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            src = fh.read()
        self.assertTrue(self._lowering_present(src),
                        "the channel lock is gone — a channel line was written while the "
                        "stop clause is unanswered, which is what this file forbids")

    def test_NEAR_MISS_a_lowering_spelled_differently_is_still_seen(self):
        self.assertTrue(self._lowering_present(self.NEAR_MISS_SHOULD_MATCH),
                        "the walk is matching one spelling rather than the construct, so "
                        "the row above would report a removal that did not happen")

    def test_NEAR_MISS_a_mere_mention_of_the_lock_is_not_a_lowering(self):
        self.assertFalse(self._lowering_present(self.NEAR_MISS_SHOULD_NOT_MATCH),
                         "a comment naming the lock, beside a DIFFERENT mutex being taken, "
                         "read as the lowering being in place — the walk is reading the "
                         "file rather than the construct")

    def test_the_wire_already_carries_the_transport_id_the_order_asks_for(self):
        """Derived at zero evidence cost for the ruling seat: the correlation W4e.C is asked
        to build is HALF PRESENT. The module stamps `id=` on every request, the daemon echoes
        it into every reply, and the kernel never reads it back. What the item adds is a
        pending-request table and the daemon's concurrency, not a wire change."""
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('"id=%llu\\t"', src, "the request no longer carries a transport id")
        from bridge.kernel_port import build_reply
        self.assertTrue(build_reply("7", 0).startswith(b"id=7\t"),
                        "the reply no longer carries the transport id it is correlated by")


if __name__ == "__main__":
    unittest.main()
