"""EP-28C W4e.R — THE PORT'S PRECONDITION READ, ON A ONE-VARIABLE DIFFERENTIAL.

AMENDMENT 11.1 licenses the retirement the estate's way and never by deletion: the port
read ON and OFF as the ONE varied thing, every (op, outcome) pair of the committed
nineteen driven in both arms, non-vacuity first, and A PAIR THAT DIFFERS IS A STOP NAMING
THE MEMBER. This file is that differential, and it is the licence rather than a report of
one — it runs every suite run, at both widths, forever.

WHAT THE ONE VARIABLE IS, EXACTLY. Both arms call `KernelPort.handle`. The ON arm runs
`RETIRED_READ` — the port's precondition read, carried here verbatim — in front of it and
answers from it when it answers; the OFF arm does not. The port's own copy of the read is
SUPPRESSED in both arms while it still exists on the class, so the read executes exactly
once in the ON arm and exactly zero times in the OFF arm. Suppressing it in both arms is
what keeps this a one-variable differential across the retirement itself: the file measures
the same two things before the read is removed from `kernel_port.py` and after, and neither
measurement moves when the removal lands.

THE TWO STOP DIMENSIONS, ASSERTED, AND THE ONE DELTA, NAMED.

  errno         IDENTICAL, all nineteen. A difference here is the stop clause firing.
  act records   IDENTICAL, all nineteen, and both are ZERO. A refused act appends no
                record claiming its effect — EP-28K's T-NO-PHANTOM-ACT, re-asked from the
                other side of the retirement.
  refusal       DIFFERENT, all nineteen, in one direction and one shape: the ON arm
  records       appends nothing, the OFF arm appends one `op-refused` citing the declared
                check's rule plus its dual-audit mirror. THIS DELTA IS NOT W4e's FINDING
                AND IT IS NOT A STOP. It is EP-28K's own ruled consequence, arriving where
                that pass said it would: §11.1a classed the port's outcomes as ABSENCE and
                "that membership was CONDITIONAL on nothing governing the outcome. A
                declared check supplies the law, so the classification changes because THE
                FACT THAT PUT IT THERE changed" (EP-28K, the derivation, carried at its
                AMENDMENT 1). The declared checks landed at EP-28K/N/N-A1; the port's read
                has been hiding their refusals behind an earlier answer ever since. The
                retirement does not create the delta, it stops concealing it.

  A LITERAL READING OF "IDENTICAL RECORDS" WOULD MAKE THE ACCEPTANCE UNSATISFIABLE, and
  that is why it is not the reading taken: a declared check records by construction and an
  absence-classed read records nothing by construction, so under the literal reading all
  nineteen pairs differ and no retirement could ever be licensed — including the one
  EP-28K's trap-2 detector explicitly reserved to W4e ("the port's retirement is W4e's,
  against this law, one variable at a time"). The reading taken is stated here rather than
  assumed, the measurement is attached, and the entry raises the wording so the ruling seat
  can overrule the reading rather than reconstruct it.

W4e.R DID NOT LAND AND THE REASON IS A FENCE CONFLICT, NOT A DEFECT. The differential
below passes on all nineteen. Applying the retirement and running the tree reds TWENTY-SIX
rows across FIVE test files this EP's fence does not name — the exact inventory, driven and
counted, is in `TestTheReadIsSTILLCalledAndThisRowIsTheExpiry`'s docstring, and the last row
of this file pins today's state so the suite says so rather than a paragraph saying it.

NON-VACUITY COMES FIRST (AMENDMENT 8.1, close item 49's clause). Every row below compares
two derived things, and agreement does not imply either side exists. The rows in
`TestTheDrivenWorldRefusesInEveryClass` prove: the case set IS the table's key set, both
directions; every case actually REFUSES in both arms rather than quietly succeeding; every
one of the SIX distinct ABI outcomes is exercised; and each case's world holds the state its
outcome is about.
"""

import ast
import errno as E
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from bridge import custody                                          # noqa: E402
from bridge.custody import KIND_DIR                                 # noqa: E402
from bridge.kernel_port import (DECISION_OPS, ERRNO_BY_ACT,         # noqa: E402
                                KernelPort)
from bridge.mount import build_brain                                # noqa: E402

PORT_PATH = os.path.join(REPO, "src", "bridge", "kernel_port.py")
FOUNDING = os.path.join(REPO, "src", "founding", "founding-pack.json")


# ---- the ON arm's subject, carried verbatim ------------------------------------------
def RETIRED_READ(port, op, f):
    """`KernelPort._posix_precondition`, CARRIED HERE BYTE-FOR-BYTE IN BEHAVIOUR.

    It lives in the test file rather than in the port because the ON arm is a HISTORICAL
    world, and a historical world kept in product code is dead code that the next reader
    cannot tell from live code. W4a set the precedent one item earlier: the retired
    text-scan guard was driven over the same double and shown blind, in the battery, not
    left in the source it had stopped protecting.

    `self` is passed explicitly so the same body can be driven against any port instance
    without being bound to the class — which is also what keeps it from being reinstalled
    by accident."""
    path = custody._norm(f.get("path") or "/")
    if op in ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK"):
        if port.state.exists(path):
            return -E.EEXIST
        parent = custody.parent_of(path)
        if parent is not None:
            pnode = port.state.lookup(parent)
            if pnode is None:
                return -E.ENOENT
            if pnode.kind != KIND_DIR:
                return -E.ENOTDIR
        return None
    if op == "FILE-RMDIR":
        node = port.state.lookup(path)
        if node is None:
            return -E.ENOENT
        if node.kind != KIND_DIR:
            return -E.ENOTDIR
        if port.state.children(path):
            return -E.ENOTEMPTY
        return None
    if op == "FILE-UNLINK":
        node = port.state.lookup(path)
        if node is None:
            return -E.ENOENT
        if node.kind == KIND_DIR:
            return -E.EISDIR
        return None
    if op == "FILE-RENAME":
        if port.state.lookup(path) is None:
            return -E.ENOENT
        dst = custody._norm(f.get("new_path") or "")
        existing = port.state.lookup(dst)
        if existing is not None and existing.kind == KIND_DIR and port.state.children(dst):
            return -E.ENOTEMPTY
        return None
    if op == "FILE-LINK":
        src = custody._norm(f.get("target_path") or "")
        node = port.state.lookup(src)
        if node is None:
            return -E.ENOENT
        if node.kind == KIND_DIR:
            return -E.EPERM
        if port.state.exists(custody._norm(f.get("new_path") or "")):
            return -E.EEXIST
        return None
    return None


#: THE NINETEEN, DRIVEN. Each row is (op, requirement, setup acts, the act under test).
#: The requirement strings are the table's own keys and the set equality is asserted in
#: BOTH directions below — a case list that drifted from the table would otherwise agree
#: with a table that had drifted from the law.
CASES = (
    ("FILE-CREATE", "binding:unbound",
     (("FILE-CREATE", {"path": "/a", "perm": "644"}),),
     ("FILE-CREATE", {"path": "/a", "perm": "644"})),
    ("FILE-MKDIR", "binding:unbound",
     (("FILE-MKDIR", {"path": "/d", "perm": "755"}),),
     ("FILE-MKDIR", {"path": "/d", "perm": "755"})),
    ("FILE-SYMLINK", "binding:unbound",
     (("FILE-CREATE", {"path": "/a", "perm": "644"}),),
     ("FILE-SYMLINK", {"path": "/a", "target": "/z"})),
    ("FILE-LINK", "binding:unbound",
     (("FILE-CREATE", {"path": "/a", "perm": "644"}),
      ("FILE-CREATE", {"path": "/b", "perm": "644"})),
     ("FILE-LINK", {"target_path": "/a", "new_path": "/b"})),
    ("FILE-RMDIR", "binding:bound", (), ("FILE-RMDIR", {"path": "/nope"})),
    ("FILE-UNLINK", "binding:bound", (), ("FILE-UNLINK", {"path": "/nope"})),
    ("FILE-RENAME", "binding:bound", (),
     ("FILE-RENAME", {"path": "/nope", "new_path": "/x"})),
    ("FILE-LINK", "binding:bound", (),
     ("FILE-LINK", {"target_path": "/nope", "new_path": "/x"})),
    ("FILE-RMDIR", "kind:require:dir",
     (("FILE-CREATE", {"path": "/f", "perm": "644"}),),
     ("FILE-RMDIR", {"path": "/f"})),
    ("FILE-UNLINK", "kind:forbid:dir",
     (("FILE-MKDIR", {"path": "/d", "perm": "755"}),),
     ("FILE-UNLINK", {"path": "/d"})),
    ("FILE-LINK", "kind:forbid:dir",
     (("FILE-MKDIR", {"path": "/d", "perm": "755"}),),
     ("FILE-LINK", {"target_path": "/d", "new_path": "/x"})),
    ("FILE-CREATE", "binding:bound@container", (),
     ("FILE-CREATE", {"path": "/nodir/f", "perm": "644"})),
    ("FILE-MKDIR", "binding:bound@container", (),
     ("FILE-MKDIR", {"path": "/nodir/d", "perm": "755"})),
    ("FILE-SYMLINK", "binding:bound@container", (),
     ("FILE-SYMLINK", {"path": "/nodir/l", "target": "/z"})),
    ("FILE-CREATE", "kind:require:dir@container",
     (("FILE-CREATE", {"path": "/f", "perm": "644"}),),
     ("FILE-CREATE", {"path": "/f/x", "perm": "644"})),
    ("FILE-MKDIR", "kind:require:dir@container",
     (("FILE-CREATE", {"path": "/f", "perm": "644"}),),
     ("FILE-MKDIR", {"path": "/f/x", "perm": "755"})),
    ("FILE-SYMLINK", "kind:require:dir@container",
     (("FILE-CREATE", {"path": "/f", "perm": "644"}),),
     ("FILE-SYMLINK", {"path": "/f/x", "target": "/z"})),
    ("FILE-RMDIR", "contains:empty",
     (("FILE-MKDIR", {"path": "/d", "perm": "755"}),
      ("FILE-CREATE", {"path": "/d/f", "perm": "644"})),
     ("FILE-RMDIR", {"path": "/d"})),
    ("FILE-RENAME", "contains:empty",
     (("FILE-MKDIR", {"path": "/d", "perm": "755"}),
      ("FILE-CREATE", {"path": "/d/f", "perm": "644"}),
      ("FILE-MKDIR", {"path": "/e", "perm": "755"})),
     ("FILE-RENAME", {"path": "/e", "new_path": "/d"})),
)

#: The SIX distinct ABI outcomes the nineteen produce — six, not nineteen, because POSIX
#: gives several of these acts the same errno for different reasons, which is exactly why
#: `ERRNO_BY_ACT` is keyed by (op, requirement) and not by errno. Data, so the coverage
#: clause is a SET EQUALITY rather than a count: nineteen rows that all produced EEXIST
#: would satisfy a counter and say nothing.
OUTCOME_CLASSES = {E.EEXIST, E.ENOENT, E.ENOTDIR, E.EISDIR, E.EPERM, E.ENOTEMPTY}


def _wire(op, kw):
    f = {"id": "1", "op": op, "class": "DECISION",
         "uid": "1000", "gid": "1000", "pid": "42"}
    f.update({k: str(v) for k, v in kw.items()})
    return f


class _Arm:
    """One world, built and driven for one case in one arm, then thrown away.

    A FRESH WORLD PER ARM AND NOT A SHARED ONE. The two arms differ in what they APPEND,
    so a shared world would make the second arm's subject the first arm's leftovers — the
    differential would be measuring its own order."""

    def __init__(self, case, read_on):
        op, requirement, setup, act = case
        self.dir = tempfile.mkdtemp(prefix="w4e-r-")
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)
        # THE READ IS SUPPRESSED IN BOTH ARMS while it still exists on the class, so the ON
        # arm's read is this file's copy and nobody else's. After the retirement lands this
        # is a no-op and the differential is unchanged, which is the property that lets one
        # file measure both sides of the removal.
        if hasattr(self.port, "_posix_precondition"):
            self.port._posix_precondition = lambda o, f: None
        for sop, skw in setup:
            status, _f, _p = self.port.handle(_wire(sop, skw), b"")
            if status != 0:
                raise AssertionError("the case's setup did not build its world: %s %s -> %d"
                                     % (sop, skw, status))
        self.before = len(self.store.all())
        self.names_before = set(self.port.state.names)
        aop, akw = act
        fields = _wire(aop, akw)
        if read_on:
            answer = RETIRED_READ(self.port, aop, fields)
        else:
            answer = None
        if answer is not None:
            self.status = answer
        else:
            self.status, _f, _p = self.port.handle(fields, b"")
        self.added = self.store.all()[self.before:]
        self.names_after = set(self.port.state.names)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def refusals(self):
        # The only reader is the decider class below, which needs a LIVE arm (it re-runs the
        # act through the real gate to catch the raised error). Every other row reads the
        # `_Observed` copy, which outlives its world.
        return [r for r in self.added if r.get("action") == "op-refused"]


class _Observed:
    """What one arm of one case LEFT BEHIND, kept after its world is destroyed.

    ONE DRIVING, MANY READINGS, and it is a derivation rather than a speed trick: the rows
    below assert different properties OF THE SAME RUN, so re-driving per row would let two
    rows disagree about one world and report it as two independent passes. Building the
    thirty-eight worlds once also keeps this file's cost near twenty seconds instead of near
    two minutes, in a suite already measured in hundreds."""

    __slots__ = ("status", "added", "names_before", "names_after")

    def __init__(self, arm):
        self.status = arm.status
        self.added = [dict(r) for r in arm.added]
        self.names_before = set(arm.names_before)
        self.names_after = set(arm.names_after)

    def acts_of(self, op):
        return [r for r in self.added if r.get("action") == op]

    def refusals(self):
        return [r for r in self.added if r.get("action") == "op-refused"]


_DRIVEN = {}


def _drive(case):
    """(ON, OFF) observations for one case, driven once per process."""
    key = (case[0], case[1])
    if key not in _DRIVEN:
        pair = []
        for read_on in (True, False):
            arm = _Arm(case, read_on)
            try:
                pair.append(_Observed(arm))
            finally:
                arm.close()
        _DRIVEN[key] = tuple(pair)
    return _DRIVEN[key]


def _op_definitions():
    """Every op definition in the founding pack, read from the STRUCTURE and not the names
    (§A51). The manager's own M1 at this dispatch is why the walk keys on what the pack
    actually carries: a walker keyed `op`/`type`/`kind` returns zero against this pack and
    a zero-length enumeration agrees with everything."""
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


class TestTheDrivenWorldRefusesInEveryClass(unittest.TestCase):
    """NON-VACUITY, BEFORE THE COMPARISON COUNTS (AMENDMENT 11.1's own clause)."""

    def test_the_case_set_and_the_tables_key_set_are_the_same_set_both_directions(self):
        cases = {(op, req) for op, req, _s, _a in CASES}
        table = set(ERRNO_BY_ACT)
        self.assertEqual(sorted(cases - table), [],
                         "a driven case names an (op, outcome) pair the port cannot render")
        self.assertEqual(sorted(table - cases), [],
                         "the table declares an (op, outcome) pair this differential never "
                         "drives — the nineteen would be a claim about eighteen")
        self.assertEqual(len(CASES), 19)
        self.assertEqual(len(ERRNO_BY_ACT), 19)

    def test_every_pair_the_table_carries_is_declared_by_the_law_it_renders(self):
        """The other direction, against the FOUNDING rather than against the port: every
        (op, requirement) the table renders is a requirement some served op's definition
        actually declares. A table row for a requirement no law states would be an answer
        to a question nobody asks, and it would pass every arm of this differential."""
        from kernel.opdefs import declared_requirements
        declared = set()
        for name, d in _op_definitions().items():
            if name not in DECISION_OPS:
                continue
            for req in declared_requirements(d):
                declared.add((name, req))
        self.assertGreater(len(declared), 0, "no requirements were read from the pack at all")
        self.assertEqual(sorted(set(ERRNO_BY_ACT) - declared), [],
                         "the port renders an outcome no served op declares")

    def test_every_case_actually_refuses_in_BOTH_arms_and_in_every_outcome_class(self):
        seen_on, seen_off = set(), set()
        for case in CASES:
            on, off = _drive(case)
            self.assertLess(on.status, 0,
                            "%s/%s did not refuse in the ON arm — the case builds a "
                            "world its outcome is not about" % (case[0], case[1]))
            self.assertLess(off.status, 0,
                            "%s/%s did not refuse in the OFF arm" % (case[0], case[1]))
            seen_on.add(-on.status)
            seen_off.add(-off.status)
        self.assertEqual(seen_on, OUTCOME_CLASSES,
                         "the ON arm did not exercise every outcome class")
        self.assertEqual(seen_off, OUTCOME_CLASSES,
                         "the OFF arm did not exercise every outcome class")

    def test_each_cases_world_holds_the_state_its_outcome_is_about(self):
        """The fold each case reads is non-empty where the outcome needs it to be, and the
        root is not the only name in the ones whose setup builds a subject."""
        for case in CASES:
            on, off = _drive(case)
            if case[2]:
                self.assertGreater(len(on.names_before), 1,
                                   "%s/%s ran against a world holding only the root"
                                   % (case[0], case[1]))
                self.assertGreater(len(off.names_before), 1)
            self.assertIn("/", on.names_before)
            self.assertIn("/", off.names_before)


class TestTheDifferential(unittest.TestCase):
    """THE ONE-VARIABLE COMPARISON. Every failure message NAMES THE MEMBER, because the
    clause it serves is "a pair that differs is a STOP naming the member"."""

    def test_every_pair_yields_the_identical_errno_in_both_arms(self):
        differed = []
        for case in CASES:
            on, off = _drive(case)
            if on.status != off.status:
                differed.append((case[0], case[1], on.status, off.status))
        self.assertEqual(differed, [],
                         "STOP — these (op, outcome) pairs answer differently with the "
                         "port's read ON and OFF: %r" % (differed,))

    def test_every_pair_yields_the_errno_the_act_keyed_table_declares(self):
        wrong = []
        for case in CASES:
            op, requirement, _s, _a = case
            on, off = _drive(case)
            want = -ERRNO_BY_ACT[(op, requirement)]
            if on.status != want or off.status != want:
                wrong.append((op, requirement, on.status, off.status, want))
        self.assertEqual(wrong, [],
                         "an arm answered something other than the table's own row: %r"
                         % (wrong,))

    def test_no_arm_appends_an_act_record_for_a_refused_act(self):
        """EP-28K's T-NO-PHANTOM-ACT, re-asked from the other side of the retirement. This
        is the second stop dimension and it is asserted separately from the errno because
        the two fail independently: an arm could answer the right errno and still record."""
        recorded = []
        for case in CASES:
            op, requirement, _s, _a = case
            on, off = _drive(case)
            if on.acts_of(op) or off.acts_of(op):
                recorded.append((op, requirement,
                                 len(on.acts_of(op)), len(off.acts_of(op))))
            if on.names_after != on.names_before or off.names_after != off.names_before:
                recorded.append((op, requirement, "the namespace moved under a refusal"))
        self.assertEqual(recorded, [],
                         "STOP — a refused act appended a record claiming its effect, or "
                         "moved the namespace: %r" % (recorded,))

    def test_THE_ONE_DELTA_the_off_arm_records_the_refusal_the_on_arm_conceals(self):
        """THE NAMED DIFFERENCE, DRIVEN RATHER THAN ASSERTED — and it is EP-28K's ruled
        reclassification arriving, not a W4e finding. Both halves are required: the ON arm
        appends NOTHING (the absence class), the OFF arm appends EXACTLY ONE `op-refused`
        (the decision class). A row asserting only the second would pass in a world where
        both arms recorded, which is the world this delta would be a defect in."""
        rows = []
        for case in CASES:
            op, requirement, _s, _a = case
            on, off = _drive(case)
            rows.append((op, requirement, len(on.refusals()), len(off.refusals())))
        bad_on = [r for r in rows if r[2] != 0]
        bad_off = [r for r in rows if r[3] != 1]
        self.assertEqual(bad_on, [], "the ON arm recorded a refusal — the port's read is an "
                                     "ABSENCE and appends nothing: %r" % (bad_on,))
        self.assertEqual(bad_off, [], "the OFF arm did not record exactly one refusal — the "
                                      "declared check is what decides there: %r" % (bad_off,))
        self.assertEqual(len(rows), 19)


class TestTheGatesDeclaredChecksAreTheOnlyDeciderInTheOffArm(unittest.TestCase):
    """AMENDMENT 11.1's third clause. Not "the answer is the same" — WHERE the answer comes
    from. Three independent observations, because a single one of them is satisfiable by
    accident: the refusal cites the declared law, it carries the requirement the act made of
    its key, and it was raised with the decide region HELD."""

    def test_the_off_arms_refusal_cites_the_declared_law_and_carries_the_requirement(self):
        from kernel.errors import OpError
        seen_rules, seen_reqs = set(), []
        for case in CASES:
            op, requirement, setup, act = case
            arm = _Arm(case, False)
            try:
                rec = arm.refusals()[-1]
                seen_rules.add(rec.get("rule_cited"))
                # The requirement travels on the raised error, never on the record — the
                # record stays keyed by the RULE, which is EP-28N's two-key split.
                caught = {}
                real = arm.gate.refuse

                def watched(actor, opname, rule, message, _real=real, _c=caught):
                    try:
                        _real(actor, opname, rule, message)
                    except OpError as e:
                        _c["err"] = e
                        raise

                arm.gate.refuse = watched
                arm.port.handle(_wire(act[0], act[1]), b"")
                arm.gate.refuse = real
                err = caught.get("err")
                self.assertIsNotNone(err, "%s/%s produced no refusal to read" % (op, requirement))
                seen_reqs.append((op, getattr(err, "requirement", None)))
            finally:
                arm.close()
        self.assertEqual(seen_rules, {"FS-LAW-NAMESPACE"},
                         "the OFF arm's refusals cite something other than the declared "
                         "namespace law: %r" % (sorted(seen_rules),))
        missing = [r for r in seen_reqs if r[1] is None]
        self.assertEqual(missing, [],
                         "an OFF-arm refusal carried no requirement, so the act-keyed table "
                         "could not have decided its errno: %r" % (missing,))

    def test_the_off_arms_check_fires_with_the_decide_region_HELD(self):
        """The atomicity claim, observed on the executing path rather than read off a span.
        The predicate answers about the CALLING thread, so asking it from inside the check's
        own refusal is the only place the answer is about the check."""
        from kernel.gate import decide_region_held
        from kernel.errors import OpError
        case = CASES[0]
        arm = _Arm(case, False)
        try:
            seen = {}
            real = arm.gate.refuse

            def watched(actor, opname, rule, message):
                seen["held"] = decide_region_held()
                return real(actor, opname, rule, message)

            arm.gate.refuse = watched
            arm.port.handle(_wire(case[3][0], case[3][1]), b"")
            arm.gate.refuse = real
            self.assertIs(seen.get("held"), True,
                          "the declared check refused with the region NOT held — "
                          "check-then-act is not atomic and the retirement is unsafe")
        finally:
            arm.close()

    def test_the_region_is_NOT_held_when_the_retired_read_answers(self):
        """The control that makes the row above a measurement. The retired read answers from
        outside every region — which is the whole reason it was retireable rather than
        merely redundant — so the same predicate must answer False there. Two observations
        of one predicate, one True and one False, is what rules out a predicate that always
        answers True."""
        from kernel.gate import decide_region_held
        case = CASES[0]
        arm = _Arm(case, True)
        try:
            self.assertLess(arm.status, 0, "non-vacuity: the ON arm did refuse")
            self.assertIs(decide_region_held(), False)
        finally:
            arm.close()


class TestTheReadIsRETIREDAndThisRowIsTheDischarge(unittest.TestCase):
    """THE EXPIRY FIRED AND WAS DISCHARGED — EP-28C W4e, 2026-08-07. The class was
    `TestTheReadIsSTILLCalledAndThisRowIsTheExpiry` and it asserted the read was NOT retired
    on this tree; it is renamed rather than only inverted, because a class named
    `IsSTILLCalled` whose row asserts the call is gone carries a repealed fact in its name.

    WHAT IT SAID BEFORE, kept as the record of the two stopped passes: "W4e.R's differential
    above PASSES: the retirement is measured safe. It did not LAND, and the reason is a fence
    conflict rather than a defect." Its carried inventory was 26 rows across 5 files; the
    pass after it re-derived 36 across 7 by running the FULL SUITE rather than a chosen set.

    THE INVENTORY AT THE LANDING, RE-DERIVED LIVE FROM THE CODE AND FROM THE WHOLE SUITE
    (AMENDMENT 11.1 clause 3 — no count travels; the two figures above are cited as those
    measurements' history and were NOT matched to):

        tests/test_ep28n.py         9   fence-named
        tests/test_ep28k.py         7   fence-named
        tests/test_ep28n2.py        7   fence-named
        tests/test_ep28.py          4   fence-named (the sixth file, mentor-ruled 08-07)
        tests/test_ep28o.py         2   fence-named
        tests/test_ep28e_w4.py      1   fence-named
        tests/test_ep28c_w4e.py     2   this EP's own
        tests/test_ep28c_w4e_c.py   3   this EP's own
        tests/test_ep28c_w4e_r.py   1   this EP's own — the row below
        tests/test_ep28c_w4e_3b.py  1   this EP's own — NOT in either prior figure

    THIRTY-SEVEN ROWS ACROSS EIGHT FILES. The six named files hold 30 and reproduce the
    prior pass's per-file figures exactly; the EIGHTH file is `test_ep28c_w4e_3b.py`, written
    BY the pass that measured 36, whose pre-gate-read enumeration counts FOUR reads and finds
    three once one of them retires. A pass cannot measure the blast radius of a change
    against a battery it has not written yet, and that is the whole of the 36-versus-37 gap.

    THE DISCRIMINATING CLAUSE, COMPUTED PER ROW FROM THE CAPTURED EXCEPTION: 21
    StopIteration (the AST walk finds no `_posix_precondition`), 7 AttributeError
    (getattr/monkeypatch on the removed method), 4 record-count equality (+3 = op-refused
    plus the mirror's two streams), 1 ValueError (a byte pin's `index()`), 1 substring pin,
    1 §A52 reader count, 1 expiry row, 1 pre-gate-read population 4→3. **ROWS FAILING FOR ANY
    OTHER REASON: ZERO.** EP-28F's precedent re-pinned nothing and was right; this one is
    measured the same way and gets the other answer.

    §A64 BINDS THE STRUCTURAL WALK IT USES: a DRIVEN near-miss both ways — one construct
    that SHOULD match spelled differently, one that should NOT spelled similarly. THE
    GENERALISATION CLAIMED is that the walk finds a precondition read on the decide path
    WHATEVER IT IS CALLED, so the near-misses run on that naming axis and not on the one
    spelling this file happens to know."""

    def _decide_calls(self, src):
        """Every attribute call `self.<name>(...)` made inside `_decide`, read from the AST.

        THE SUBJECT IS THE CALL AND NOT THE FUNCTION. A retirement that deleted the method
        and left the call would not compile; a retirement that removed the call and left the
        method is dead code, which is a different defect and is asserted separately. What
        this row protects is that no read runs BEFORE the region."""
        tree = ast.parse(src)
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_decide"), None)
        self.assertIsNotNone(fn, "`_decide` is gone — this row has no subject")
        out = []
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == "self":
                out.append(n.func.attr)
        return out

    NEAR_MISS_SHOULD_MATCH = '''
class KernelPort:
    def _decide(self, op, f, payload):
        # SPELLED DIFFERENTLY AND IT IS THE SAME CONSTRUCT: a precondition read taken
        # before the gate, under a name this file has never seen.
        answer = self.posix_answer_before_the_gate(op, f)
        if answer is not None:
            return answer, {}, b""
        return 0, {}, b""
'''

    NEAR_MISS_SHOULD_NOT_MATCH = '''
class KernelPort:
    def _decide(self, op, f, payload):
        return 0, {}, b""

    def _posix_precondition_helper(self, op, f):
        # SPELLED SIMILARLY AND IT IS NOT THE CONSTRUCT: a method whose NAME is a near
        # neighbour of the retired read, never called from the decide path.
        return self._posix_precondition_helper(op, f)
'''

    def test_THE_DISCHARGE_the_decide_path_reads_NO_precondition_before_the_gate(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: the `self.<name>(...)` call list of `_decide`, asserted to be exactly
        `["_posix_precondition"]`. The retirement removed the call, so the list is empty and
        the row reds — by design, on the CALL, which is behaviour and not a comment.

        THE NON-VACUITY CLAUSE MATTERS MORE AFTER THE FLIP THAN BEFORE IT. An empty result
        is what a broken walk returns too, so the row proves `_decide` makes calls at all,
        proves the walk CAN see a precondition read under a name this file has never met
        (the near-miss below), and proves the reads it does find are the three that are
        supposed to be there."""
        with open(PORT_PATH, encoding="utf-8") as fh:
            calls = self._decide_calls(fh.read())
        self.assertGreater(len(calls), 0, "non-vacuity: `_decide` makes calls at all")
        reads = [c for c in calls if "precondition" in c or "posix" in c.lower()]
        self.assertEqual(reads, [],
                         "the decide path reads a precondition before the gate again: %r. "
                         "W4e.R retired that read and the whole differential in this file "
                         "is about its absence." % (reads,))
        # AND THE PATH IS THE ONE THIS ROW MEANS. An empty `reads` would also be produced by
        # a walk pointed at the wrong function, so the calls that SHOULD be there are named.
        for expected in ("_prov", "_params_for", "_carries_port_provenance"):
            self.assertIn(expected, calls,
                          "`_decide` no longer calls %s, so this walk is not reading the "
                          "decide path" % expected)

    def test_NEAR_MISS_a_read_spelled_differently_is_still_caught(self):
        calls = self._decide_calls(self.NEAR_MISS_SHOULD_MATCH)
        self.assertIn("posix_answer_before_the_gate", calls,
                      "the walk cannot see a call it was not told the name of, so the row "
                      "above proves nothing about a read under a new name")

    def test_NEAR_MISS_a_similarly_named_method_off_the_decide_path_is_not_caught(self):
        calls = self._decide_calls(self.NEAR_MISS_SHOULD_NOT_MATCH)
        self.assertEqual(calls, [],
                         "the walk reported a method that `_decide` never calls, so it is "
                         "reading the file rather than the decide path")


if __name__ == "__main__":
    unittest.main()
