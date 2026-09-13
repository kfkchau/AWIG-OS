"""EP-28C W4e — RAISE 3b DRIVEN, AND RAISE 3 WITH IT: what the decision path reads OUTSIDE the
decide region, measured before the channel admits many.

AMENDMENT 11.2's ruled addition: three reads sit on the DECISION path — `kernel_port.py`'s
`_posix_precondition` (`:413`), `_prov` (`:429`) and `_params_for` (`:430`) — read-derived and
NOT driven, effect on any permitted (op, outcome) combination UNMEASURED. The mentor's own
words: "Read-derived is not sufficient for a clause the channel's safety rests on."

THE CRITERION, STATED ONCE AND COMPUTED BY EVERY ROW BELOW. The standing stop clause asks
whether admitting many in flight would change what a DECLARED operation records or returns. A
single act's own errno is the wrong unit — every errno either read can produce is reachable
under one caller too, just at a different moment. The unit that answers the clause is THE
RECORD STREAM, the sequence of records two acts leave behind, and the test is whether the
interleaved stream is one A SINGLE CALLER COULD HAVE PRODUCED:

    interleaved  IN  {serialized A-then-B, serialized B-then-A}  ->  no new combination
    interleaved  OUTSIDE both                                    ->  the clause's subject

That is the unit the stopped pass's finding already used ("a record stream that is a function of
the thread schedule"), restated as a decision procedure a row can compute instead of a reader
judging it.

WHERE THE THREAD IS HELD, AND WHY ONE PLACE COVERS EVERY READ. `_decide` takes all of its reads
and then calls `gate.execute`. Holding thread A inside a wrapped `execute`, before the real one,
puts A AFTER every read and BEFORE the act, with the decide region NOT yet held — so the mover
enters the region freely. One hold point, no sleeps, no retries: the mover runs to completion on
the main thread while A waits on an event, so the interleaving is CONSTRUCTED and not raced for.

WHAT THE DRIVES FOUND — verdicts first, machinery after.

  `_params_for` -> `_node_by_wire`   DOES NOT DIVERGE, and the mechanism is why rather than
      luck: the value it reads is an IDENTITY, and an identity is immutable once minted.
      `custody._unbind` drops a NAME and leaves `state.inodes` alone — which is POSIX's own
      contract for a write to an unlinked-but-open file — and a rename deliberately KEEPS
      `node.identity`. Nothing in the estate removes an inode from the fold, so a concurrent
      decide can only ADD to what this read could have found and can never take away what it
      did find. Driven over four movers and two members.

  `_prov` -> `_actor`                DIVERGES, and it is reported WITH ITS CAP rather than as a
      stop. The only act that moves the mapping it folds is `MAP-UID`, and `MAP-UID` IS NOT IN
      `DECISION_OPS` — computed here, not remembered. No request this channel can carry is the
      mover, so opening the channel does not create this window; two SURFACES acting
      concurrently do, and that is concurrency the store admitted at W1 rather than anything
      W4e.C adds. Real, driven, capped, RAISED.

  `_posix_precondition`              ALREADY DRIVEN, and NOT re-driven here. Its divergence and
      its convergence-under-suppression are `tests/test_ep28c_w4e_c.py`'s rows, and its
      one-variable differential over all nineteen pairs is `tests/test_ep28c_w4e_r.py`. Copying
      either into this file would be one computation duplicated across a boundary by
      convention, which is the class the freeze calls M4.

  A FOURTH READ NOBODY HAD ENUMERATED     `_carries_port_provenance` (`:441`) calls
      `views.op_definitions()`, which is a live fold over the record, and it sits on the same
      side of the region as the other three. Raise 3b named three; the completeness row below
      computes FOUR. It carries the same cap as `_actor` — the acts that move it are
      `CREATE-OP` and `RETIRE-OP`, neither in `DECISION_OPS` — and it is RAISED rather than
      absorbed. CAP, stated plainly: this member is enumerated and capped, NOT driven
      end-to-end, because the mover is not a call this port can make.

RAISE 3 (fills read the fold outside every region) is homed here by the same ruling and is
correctly NOT a second instance of the stop clause: a fill declares nothing and records nothing.
The honest form is one predicate answered twice — True where the fold moves, False where a fill
reads it — because "fills read outside the region" is only a claim if the two really are on
opposite sides.
"""

import ast
import os
import shutil
import sys
import tempfile
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from bridge.kernel_port import DECISION_OPS, KernelPort             # noqa: E402
from bridge.mount import build_brain                                # noqa: E402
from kernel.gate import decide_region_held                          # noqa: E402
from kernel.errors import OpError                                   # noqa: E402

PORT_PATH = os.path.join(REPO, "src", "bridge", "kernel_port.py")

#: The uid every wire below asserts. ONE value, so a row that meant to move this uid's mapping
#: and moved another's would red instead of quietly measuring nothing.
UID = 1000

PROV = {"asserted_by": "owner", "source": "test", "could_read": []}

#: THE READS RAISE 3b NAMED, by the method that takes them. Carried as the SUBJECT of the
#: completeness row below — which computes its own answer from the source and compares — never
#: as the answer itself.
#:
#: DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. This read
#: `("_posix_precondition", "_prov", "_params_for")`. THE RETIRED CONSTRUCT: the first member.
#: W4e.R removed the port's precondition read, so raise 3b's named population is two on this
#: tree and the pre-gate reads are THREE where the completeness row found four. The count in
#: the row's own NAME moved with it and the row is renamed, not only edited.
RAISE_3B_NAMED = ("_prov", "_params_for")

#: THE MEMBER RAISE 3b NAMED THAT NO LONGER EXISTS, kept as the subject of its own assertion
#: rather than deleted: a member that simply vanishes from a population constant cannot tell a
#: retirement from a typo.
RAISE_3B_RETIRED_AT_W4E = "_posix_precondition"


def _wire(op, **kw):
    f = {"id": "1", "op": op, "class": "DECISION",
         "uid": str(UID), "gid": "1000", "pid": "42"}
    f.update({k: str(v) for k, v in kw.items()})
    return f


class _World:
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="w4e-3b-")
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, op, **kw):
        return self.port.handle(_wire(op, **kw), b"")[0]

    def mark(self):
        return len(self.store.all())

    def stream_since(self, n):
        """THE COMPARABLE VALUE: (action, actor, recorded inode) per record, IN LOG ORDER.

        ORDER IS PART OF THE VALUE ON PURPOSE. Two acts can each carry a content a single
        caller could have produced while sitting in an order a single caller could not, and
        that pair is exactly what the stopped pass's finding was about."""
        out = []
        for r in self.store.all()[n:]:
            p = r.get("payload") or {}
            out.append((r.get("action"), r.get("actor"), p.get("inode")))
        return out


# ---- the three orders ------------------------------------------------------------------
def _interleaved(w, subject, mover):
    """A's reads happen, the mover runs to completion, then A acts. Constructed, not raced.

    THE HOLD IS ONE-SHOT. `gate.execute` is re-entrant BY DESIGN — the dual-audit mirror
    appends from inside an on-append listener and the overturn sweep re-enters — so a hold
    firing on every entry would wedge A inside its own consequences instead of in front of its
    act."""
    at_the_door = threading.Event()
    mover_done = threading.Event()
    real_exec = w.gate.execute

    def ex(name, actor, params=None):
        if threading.current_thread().name == "A" and not at_the_door.is_set():
            at_the_door.set()
            mover_done.wait(30)
        return real_exec(name, actor, params)

    out = {}

    def run():
        out["status"] = subject(w)

    w.gate.execute = ex
    try:
        ta = threading.Thread(target=run, name="A")
        ta.start()
        if not at_the_door.wait(30):
            mover_done.set()
            ta.join(30)
            raise AssertionError(
                "thread A never reached the gate door — the arm did not run, so any agreement "
                "measured from it would be between two things that did not happen")
        try:
            mover(w)
        finally:
            mover_done.set()
        ta.join(30)
    finally:
        w.gate.execute = real_exec
    return out.get("status")


def arm(setup, subject, mover, order):
    """Returns (the subject's status, the record stream the two acts left)."""
    w = _World()
    try:
        setup(w)
        n = w.mark()
        if order == "A-first":
            status = subject(w)
            mover(w)
        elif order == "B-first":
            mover(w)
            status = subject(w)
        elif order == "interleaved":
            status = _interleaved(w, subject, mover)
        else:                                        # pragma: no cover - typo guard
            raise AssertionError("unknown order %r" % (order,))
        return status, w.stream_since(n)
    finally:
        w.close()


def three_arms(setup, subject, mover):
    return {o: arm(setup, subject, mover, o)
            for o in ("A-first", "B-first", "interleaved")}


def map_uid_to(account):
    """The mover for `_actor`, and it is NOT a channel request — the cap row proves that."""
    def go(w):
        w.gate.execute("CREATE-ACCOUNT", "owner",
                       {"account_id": account, "actor_class": "human"})
        w.gate.execute("MAP-UID", "owner",
                       {"uid": UID, "account": account, "provenance": dict(PROV)})
    return go


def channel_call(op, **kw):
    """A mover that is exactly what the channel would carry: one `KernelPort.handle`."""
    def go(w):
        status = w.call(op, **kw)
        assert status == 0, (op, kw, status)
    return go


# ==========================================================================================
class TestTheSubjectExists(unittest.TestCase):
    """NON-VACUITY FIRST (AMENDMENT 8.1, close item 49's clause). Every row below is an
    equality or an inequality between two derived streams, and agreement does not imply either
    side exists."""

    def test_all_three_orders_run_and_each_leaves_both_acts_on_the_record(self):
        got = three_arms(lambda w: None,
                         lambda w: w.call("FILE-CREATE", path="/a", perm="644"),
                         map_uid_to("ann"))
        for order, (status, stream) in got.items():
            self.assertEqual(status, 0, "%s: the subject act did not succeed" % order)
            actions = [a for a, _actor, _ino in stream]
            self.assertIn("FILE-CREATE", actions, "%s: no subject record" % order)
            self.assertIn("MAP-UID", actions, "%s: no mover record" % order)

    def test_the_two_serialized_orders_are_DIFFERENT_from_each_other(self):
        """If both serialized orders produced one stream there would be nothing for an
        interleaved arm to be inside or outside of, and every criterion row would pass
        vacuously."""
        got = three_arms(lambda w: None,
                         lambda w: w.call("FILE-CREATE", path="/a", perm="644"),
                         map_uid_to("ann"))
        self.assertNotEqual(got["A-first"][1], got["B-first"][1],
                            "the two serialized orders are indistinguishable, so the criterion "
                            "has no content")


class TestTheDecidePathsPreGateReadsAreENUMERATED(unittest.TestCase):
    """THE COMPLETENESS CLAIM RAISE 3b RESTS ON, ASSERTED INSTEAD OF ASSUMED — and it finds a
    member the raise did not name.

    Raise 3b names three reads. Nobody had asserted that three is ALL of them, and a class
    whose population is a remembered list is the defect this arc keeps finding (§A51). This row
    walks `_decide`'s own AST for every `self.<name>(...)` call reached BEFORE `gate.execute`,
    and compares that set against the raise's three.

    §A64 BINDS THE WALK. The generalisation claimed is that it finds a pre-gate read on the
    decide path WHATEVER IT IS CALLED, so both near-misses run on that axis: one construct that
    SHOULD match spelled differently, one that should NOT spelled similarly."""

    def _pre_gate_self_calls(self, src):
        """`self.<name>(...)` calls inside `_decide`, in source order, up to `gate.execute`."""
        tree = ast.parse(src)
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_decide"), None)
        self.assertIsNotNone(fn, "`_decide` is gone — this row has no subject")
        seen, stop_line = [], None
        for n in ast.walk(fn):
            if not isinstance(n, ast.Call):
                continue
            src_txt = ast.unparse(n.func) if isinstance(n.func, ast.Attribute) else ""
            if src_txt.endswith("gate.execute"):
                stop_line = n.lineno if stop_line is None else min(stop_line, n.lineno)
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == "self":
                if stop_line is None or n.lineno < stop_line:
                    seen.append((n.lineno, n.func.attr))
        return [name for _ln, name in sorted(set(seen))]

    NEAR_MISS_SHOULD_MATCH = '''
class KernelPort:
    def _decide(self, op, f, payload):
        answer = self.a_name_this_file_has_never_seen(op, f)
        rec = self.gate.execute(op, "who", {})
        return 0, {}, b""
'''

    NEAR_MISS_SHOULD_NOT_MATCH = '''
class KernelPort:
    def _decide(self, op, f, payload):
        rec = self.gate.execute(op, "who", {})
        self.after_the_act_and_therefore_not_a_pre_gate_read(rec)
        return 0, {}, b""
'''

    def test_the_pre_gate_reads_are_THREE_after_W4e_retired_the_fourth(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `_posix_precondition` as a member of `RAISE_3B_NAMED`, required to still be
        on the pre-gate path. It is not; the row's `assertIn` was the only red this file
        produced under the retirement.

        THIS ROW IS THE EIGHTH FILE, AND ITS EXISTENCE IS THE FINDING. The pass that wrote
        this battery measured the retirement's blast radius at 36 rows across seven files and
        did not count this one, because a pass cannot measure a change against a battery it
        has not written yet. The live figure at the landing is 37 across eight.

        THE CLAIM IS UNCHANGED: the population is COMPUTED from `_decide`'s own AST and
        compared against what a raise remembered, and it is the comparison that is the row.
        Four reads were found where raise 3b named three; one of the four has now retired, so
        three are found where the constant names two, and `_carries_port_provenance` is still
        the member no raise ever named."""
        with open(PORT_PATH, encoding="utf-8") as fh:
            src = fh.read()
        calls = self._pre_gate_self_calls(src)
        self.assertGreater(len(calls), 0, "non-vacuity: `_decide` makes pre-gate self calls")
        for name in RAISE_3B_NAMED:
            self.assertIn(name, calls,
                          "a read raise 3b named is no longer on the pre-gate path: %r" % name)
        self.assertNotIn(RAISE_3B_RETIRED_AT_W4E, calls,
                         "the read W4e.R retired is back on the pre-gate path, so this "
                         "file's whole cap re-opens")
        extra = [c for c in calls if c not in RAISE_3B_NAMED and not c.startswith("_refuse")]
        self.assertEqual(extra, ["_carries_port_provenance"],
                         "the pre-gate read population moved. Raise 3b named %r; the source "
                         "says %r. A population that is a remembered list is the defect this "
                         "row exists to catch." % (list(RAISE_3B_NAMED), calls))
        # AND THE RETIREMENT IS A REMOVAL, NOT A RENAME — asserted on the file rather than on
        # the call list, because a method left behind with no caller is dead code and a
        # different defect from the one this row is about.
        self.assertNotIn("def %s" % RAISE_3B_RETIRED_AT_W4E, src)

    def test_NEAR_MISS_a_pre_gate_read_spelled_differently_is_still_found(self):
        self.assertIn("a_name_this_file_has_never_seen",
                      self._pre_gate_self_calls(self.NEAR_MISS_SHOULD_MATCH),
                      "the walk cannot see a read under a name it was not told, so the row "
                      "above proves nothing about a read added under a new name")

    def test_NEAR_MISS_a_self_call_AFTER_the_act_is_not_counted_as_a_pre_gate_read(self):
        self.assertEqual(
            self._pre_gate_self_calls(self.NEAR_MISS_SHOULD_NOT_MATCH), [],
            "a call made AFTER `gate.execute` was counted as a pre-gate read, so the walk is "
            "reading the function rather than the span the region question is about")

    def test_THE_FOURTH_MEMBERS_MOVERS_ARE_ALSO_OUTSIDE_THIS_CHANNEL(self):
        """The cap on the member the raise did not name, computed the same way as `_actor`'s.
        `_carries_port_provenance` folds `op_definitions()`, which moves only on `CREATE-OP`
        and `RETIRE-OP` — neither of which this port serves."""
        for mover in ("CREATE-OP", "RETIRE-OP"):
            self.assertNotIn(mover, DECISION_OPS,
                             "the channel can carry %s, which moves the op-definition fold "
                             "this port reads before the act" % mover)


def create_op(name):
    """The mover for `_carries_port_provenance`: a new definition lands, so `op_definitions()`
    gains a member and the head-memo that served it dies. NOT a channel request — the cap row
    above proves `CREATE-OP` is not in `DECISION_OPS`."""
    def go(w):
        w.gate.execute("CREATE-OP", "owner", {
            "name": name,
            "definition": {"law_cited": "CAP-IS-LAW",
                           "description": "a test-world op that moves the definition fold",
                           "params": {"path": "required"}, "object_param": "path",
                           # `path`: STRUCTURAL — namespace path, inline shape. ADMIT-intent:
                           # this probe op must be created to move the definition fold under the
                           # mover. [design/46 member-2 vocabulary door, archi :2956 RULING 1.]
                           "payload_from": ["path"], "structural_params": ["path"],
                           "checks": []}})
    return go


def retire_op(name):
    """The fold SHRINKS. Ordinary ops only — see `amend_subject_op` for why."""
    def go(w):
        w.gate.execute("RETIRE-OP", "owner", {"name": name})
    return go


def amend_subject_op(name):
    """THE LEAST-LIKELY MEMBER (§A49), and the shape of it was DERIVED rather than chosen.

    The obvious least-likely mover is `RETIRE-OP` of the subject's own op while the subject
    sits at the gate's door with its provenance answer already read. THE ENGINE REFUSES IT,
    measured: `[BOOT-INT] "FILE-CREATE" is a protected operation (tier owner) — it can be
    amended, never bare-removed: removing the shield is the ungoverning move`. So that member
    is unreachable through the lawful path, and the row below asserts the refusal rather than
    letting the drive quietly skip it.

    WHAT THE REFUSAL'S OWN TEXT NAMES IS THE REACHABLE MEMBER: amendment. This mover amends
    the subject's op to DROP `provenance_param`, which is the single field
    `_carries_port_provenance` reads. So thread A reads True, the definition beneath it stops
    saying so, and A then acts on a params dict shaped by an answer the registry no longer
    gives. If any interleaving can put a record outside what one caller could produce, it is
    this one."""
    def go(w):
        d = dict(w.views.op_definitions()[name]["definition"])
        d.pop("provenance_param", None)
        w.gate.execute("AMEND-OP", "owner", {"name": name, "definition": d})
    return go


def _retire_a_created_op():
    """The fold SHRINKS: an ordinary op is created in setup and retired as the mover, so the
    shrink direction is driven as well as the grow direction. Two directions, because a memo
    that invalidated only on growth would pass a grow-only drive."""
    def go(w):
        w.gate.execute("RETIRE-OP", "owner", {"name": "W4E-SHRINK-PROBE"})
    return go


class TestTheFOURTHReadDoesNotDiverge(unittest.TestCase):
    """`_carries_port_provenance` -> `views.op_definitions()`, DRIVEN END-TO-END.

    THE RAISE NAMED THREE READS AND THE SOURCE SAID FOUR. The fourth was found by the
    completeness row above, CAPPED — `CREATE-OP` and `RETIRE-OP` are not in `DECISION_OPS`,
    so no request this channel carries is the mover — and left UNDRIVEN, said plainly, by the
    pass that found it. AMENDMENT 11.1 item 9 homed the driving to W4e.C, "the channel's own
    pass drives it." This is that drive.

    THE CRITERION IS THE SAME COMPUTED ONE the other two members use, and it is computed
    rather than judged: the unit is the RECORD STREAM two acts leave, and the question is
    whether the interleaved stream is one a single caller could have produced — INSIDE the
    set of the two serialized orders, or outside it.

    THE CAP IS NOT WEAKENED BY DRIVING IT. `CREATE-OP` and `RETIRE-OP` still are not channel
    requests; what the drive adds is that the window they open is measured rather than
    reasoned about, because two SURFACES acting concurrently can open it even when one
    channel cannot."""

    OP = "FILE-CREATE"

    def setup_world(self, w):
        assert w.call("FILE-MKDIR", path="/d", perm="755") == 0
        create_op("W4E-SHRINK-PROBE")(w)

    def subject(self, w):
        return w.call("FILE-CREATE", path="/d/f", perm="644")

    def test_the_fold_the_fourth_read_takes_ACTUALLY_MOVES_under_the_mover(self):
        """NON-VACUITY, AND IT IS THE ROW THE DRIVE RESTS ON. A convergence measured while the
        mover changed nothing is a convergence between two identical worlds."""
        w = _World()
        try:
            before = set(w.views.op_definitions())
            self.assertIn(self.OP, before, "the subject's own op is not in the fold")
            create_op("W4E-FOURTH-PROBE")(w)
            after = set(w.views.op_definitions())
            self.assertEqual(after - before, {"W4E-FOURTH-PROBE"},
                             "the CREATE-OP mover did not move the op-definition fold")
            retire_op("W4E-FOURTH-PROBE")(w)
            self.assertNotIn("W4E-FOURTH-PROBE", set(w.views.op_definitions()),
                             "the RETIRE-OP mover did not move the op-definition fold")
        finally:
            w.close()

    def test_the_read_ANSWERS_for_the_subject_so_the_drive_has_a_subject(self):
        """The second non-vacuity clause: `_carries_port_provenance` must actually return
        True for the op being driven, or the interleaving is being measured against a read
        whose answer nothing depends on."""
        w = _World()
        try:
            self.assertTrue(w.port._carries_port_provenance(self.OP),
                            "the subject op does not carry port provenance, so the fourth "
                            "read's answer changes nothing about its record")
            self.assertFalse(w.port._carries_port_provenance("CREATE-ACCOUNT"),
                             "the read answers True for everything, so it is not reading "
                             "the definition it claims to")
        finally:
            w.close()

    def test_the_least_likely_mover_RETIRE_OP_is_REFUSED_by_the_engines_own_shield(self):
        """THE MEMBER §A49 WOULD PICK FIRST, AND IT IS UNREACHABLE — asserted rather than
        skipped, because a drive that quietly omits its hardest member reports coverage it
        does not have. `FILE-CREATE` is tier owner and the engine refuses to bare-remove it.
        The amendment mover below is what the refusal's own text points at."""
        w = _World()
        try:
            with self.assertRaises(OpError) as raised:
                retire_op(self.OP)(w)
            self.assertEqual(raised.exception.rule, "BOOT-INT")
            self.assertIn(self.OP, set(w.views.op_definitions()),
                          "the refusal did not hold — the op left the fold anyway")
        finally:
            w.close()

    def test_every_mover_leaves_the_interleaved_stream_INSIDE_the_serialized_set(self):
        movers = (
            ("AMEND-OP dropping the SUBJECT'S OWN `provenance_param` — §A49's reachable "
             "least-likely member, driven FIRST", amend_subject_op(self.OP)),
            ("CREATE-OP of an unrelated op — the fold grows and the head-memo dies",
             create_op("W4E-FOURTH-PROBE")),
            ("RETIRE-OP of an ordinary op — the fold shrinks", _retire_a_created_op()),
        )
        for label, mover in movers:
            got = three_arms(self.setup_world, self.subject, mover)
            _st, inter = got["interleaved"]
            serialized = [got["A-first"][1], got["B-first"][1]]
            self.assertNotEqual(serialized[0], serialized[1],
                                "%s: the two serialized orders are identical, so 'inside the "
                                "set' is not a test of anything" % label)
            self.assertIn(inter, serialized,
                          "%s: the interleaved stream is OUTSIDE both serialized orders — "
                          "the stop clause's subject.\n  A-first     %r\n  B-first     %r\n"
                          "  interleaved %r" % (label, serialized[0], serialized[1], inter))

    def test_NEAR_MISS_an_act_that_appends_but_does_not_touch_the_fold_is_not_a_mover(self):
        """§A64, on the generalisation this class's movers claim: that they MOVE the fold the
        fourth read takes. An append alone is not that, and the row shows the difference so
        the movers above are known to be movers rather than merely to be appends."""
        w = _World()
        try:
            before = set(w.views.op_definitions())
            assert w.call("FILE-MKDIR", path="/elsewhere", perm="755") == 0
            self.assertEqual(set(w.views.op_definitions()), before,
                             "a plain governed act moved the op-definition fold, so this "
                             "class's movers are not distinguished by what they move")
        finally:
            w.close()


class TestTheFoldReadDoesNotDiverge(unittest.TestCase):
    """`_params_for` -> `_node_by_wire`, DRIVEN OVER FOUR MOVERS AND TWO MEMBERS. It converges.

    §A49 BINDS THE MEMBER CHOICE AND THE LEAST-LIKELY MEMBER IS THE POINT: `FILE-UNLINK` as a
    mover is the one that LOOKS like it must break this, because it is the act that makes the
    name stop resolving. It is driven first, and it converges — because `_unbind` drops the
    name and leaves the inode, which is POSIX's own contract."""

    def setup_world(self, w):
        assert w.call("FILE-CREATE", path="/w", perm="644") == 0
        self.ino = w.port.state.lookup("/w").ino

    def subject_write(self, w):
        return w.call("FILE-WRITE", path="/w", inode=self.ino)

    def subject_perm(self, w):
        return w.call("FILE-PERM", path="/w", inode=self.ino, perm="600")

    def movers(self):
        return (
            ("FILE-UNLINK — the name stops resolving",
             channel_call("FILE-UNLINK", path="/w")),
            ("FILE-RENAME — the name moves",
             channel_call("FILE-RENAME", path="/w", new_path="/w2")),
            ("FILE-CHOWN  — the node's own fields move",
             channel_call("FILE-CHOWN", path="/w", gid=44)),
            ("FILE-MKDIR  — an unrelated bind lands",
             channel_call("FILE-MKDIR", path="/d", perm="755")),
        )

    def test_every_mover_leaves_the_interleaved_stream_INSIDE_the_serialized_set(self):
        for member, subject in (("FILE-WRITE", self.subject_write),
                                ("FILE-PERM", self.subject_perm)):
            for label, mover in self.movers():
                got = three_arms(self.setup_world, subject, mover)
                _st, inter = got["interleaved"]
                serial = [got["A-first"][1], got["B-first"][1]]
                self.assertIn(inter, serial,
                              "%s / %s: the interleaved record stream is one NO single caller "
                              "could produce.\n  interleaved: %r\n  A-first    : %r\n"
                              "  B-first    : %r" % (member, label, inter, serial[0], serial[1]))

    def test_the_recorded_identity_is_ONE_VALUE_under_every_order_and_every_mover(self):
        """The mechanism asserted directly and not only through the criterion: whatever the
        schedule, the subject's record names one identity."""
        seen = set()
        for label, mover in self.movers():
            got = three_arms(self.setup_world, self.subject_write, mover)
            for _order, (_st, stream) in got.items():
                for action, _actor, ino in stream:
                    if action == "FILE-WRITE":
                        seen.add(ino)
            self.assertTrue(seen, "no FILE-WRITE record at all under %s" % label)
        self.assertEqual(len(seen), 1,
                         "the recorded identity moved with the schedule: %r" % (sorted(seen),))


class TestTheStoreReadDIVERGESAndTheCapIsComputed(unittest.TestCase):
    """`_prov` -> `_actor`, DRIVEN, AND IT DIVERGES.

    `_actor` folds every `MAP-UID` record to answer who a uid is. The fold is read at `_prov`,
    outside the region; the act happens inside it. A `MAP-UID` landing in between produces a
    stream in which the mapping record sits BEFORE an act attributed under the mapping it
    replaced — so a replay of the record cannot reproduce the attribution, which is
    `governed-state = f(LAW, DECISIONS, INPUTS)` failing for the actor field.

    THE CAP IS WHAT KEEPS THIS OFF THE STOP CLAUSE AND IT IS COMPUTED RATHER THAN REMEMBERED:
    the only act that moves this fold is `MAP-UID`, and `MAP-UID` is not a member of
    `DECISION_OPS`. No request the kernel channel can carry is the mover, so opening the channel
    does not create this window; two SURFACES acting concurrently do, and that is concurrency
    the store admitted at W1. Driven, capped, RAISED — not absorbed, and not asserted away."""

    def subject(self, w):
        return w.call("FILE-CREATE", path="/a", perm="644")

    def test_the_interleaved_stream_is_OUTSIDE_the_serialized_set(self):
        got = three_arms(lambda w: None, self.subject, map_uid_to("ann"))
        _st, inter = got["interleaved"]
        serial = [got["A-first"][1], got["B-first"][1]]
        self.assertNotIn(inter, serial,
                         "the divergence this row exhibits did not reproduce, so the raise it "
                         "carries would describe a world that is not this one.\n"
                         "  interleaved: %r\n  A-first    : %r\n  B-first    : %r"
                         % (inter, serial[0], serial[1]))

    def test_and_the_divergence_is_EXACTLY_the_actor_under_the_mappings_own_record(self):
        """The shape named rather than only the inequality: the mover's record comes FIRST and
        the subject is still attributed under the mapping that record replaced."""
        got = three_arms(lambda w: None, self.subject, map_uid_to("ann"))
        _st, inter = got["interleaved"]
        actions = [a for a, _actor, _ino in inter]
        self.assertLess(actions.index("MAP-UID"), actions.index("FILE-CREATE"),
                        "the mapping did not land first, so this is not the shape claimed")
        actor = next(ac for a, ac, _i in inter if a == "FILE-CREATE")
        self.assertEqual(actor, "uid:%d" % UID,
                         "the subject was attributed under the NEW mapping, so the stale read "
                         "did not happen and this row is measuring something else")
        _st2, bfirst = got["B-first"]
        self.assertEqual(next(ac for a, ac, _i in bfirst if a == "FILE-CREATE"), "ann",
                         "non-vacuity: the serialized B-first arm must show the mapping taking "
                         "effect, or 'stale' names no difference at all")

    def test_THE_CAP_no_request_this_channel_can_carry_moves_the_mapping(self):
        """COMPUTED FROM THE PORT'S OWN DECLARED SET, never from a list in this file. This is
        the clause that decides whether the divergence above is W4e.C's or somebody else's."""
        self.assertGreater(len(DECISION_OPS), 1, "non-vacuity: the served set is not empty")
        self.assertNotIn("MAP-UID", DECISION_OPS,
                         "the channel can now carry the very act that moves the actor fold, so "
                         "the divergence above IS this item's and the stop clause fires")

    def test_NEAR_MISS_the_cap_names_the_mover_rather_than_reporting_an_empty_set(self):
        """§A64 on the cap's own axis: the cap would be worthless if `DECISION_OPS` simply held
        nothing. A member that also writes identity-shaped fields is shown PRESENT, so the
        absence above is about `MAP-UID` and not about the set being empty of everything."""
        self.assertIn("FILE-CREATE", DECISION_OPS)
        self.assertIn("FILE-CHOWN", DECISION_OPS,
                      "a served member that writes uid and gid is absent, so the cap is not "
                      "discriminating between 'this act is not served' and 'nothing is'")


class TestRaise3FillsReadTheFoldOutsideEveryRegion(unittest.TestCase):
    """RAISE 3, homed here by the same ruling, and CORRECTLY NOT a second instance of the stop
    clause: a fill declares nothing and records nothing.

    The honest form of the claim is one predicate answered twice — True where the fold moves,
    False where a fill reads it — because "fills read outside the region" is only a claim if the
    two really are on opposite sides of it."""

    def test_the_fold_moves_INSIDE_a_region_and_a_fill_reads_it_OUTSIDE_one(self):
        w = _World()
        try:
            seen = {}
            real_apply = w.port.state.apply

            def apply(e):
                seen["at_fold"] = decide_region_held()
                return real_apply(e)

            w.port.state.apply = apply
            try:
                self.assertEqual(w.call("FILE-CREATE", path="/a", perm="644"), 0)
            finally:
                w.port.state.apply = real_apply

            root = w.port.state.lookup("/").ino
            real_lookup = w.port.state.lookup

            def lookup(p):
                seen.setdefault("at_fill", decide_region_held())
                return real_lookup(p)

            w.port.state.lookup = lookup
            try:
                status, _f, _p = w.port.handle(
                    {"id": "1", "op": "FILL-LOOKUP", "class": "FILL", "uid": str(UID),
                     "gid": "1000", "pid": "42", "parent": str(root), "name": "a"}, b"")
            finally:
                w.port.state.lookup = real_lookup

            self.assertEqual(status, 0, "the fill did not answer, so it read nothing")
            self.assertTrue(seen.get("at_fold"),
                            "the fold did not advance inside a region, so the two sides of "
                            "this comparison are not opposite and the claim is empty")
            self.assertIs(seen.get("at_fill"), False,
                          "the fill read inside a region, which would make this raise describe "
                          "a world that is not this one")
        finally:
            w.close()

    def test_a_fill_appends_NOTHING_which_is_why_this_is_not_the_stop_clause(self):
        w = _World()
        try:
            self.assertEqual(w.call("FILE-CREATE", path="/a", perm="644"), 0)
            root = w.port.state.lookup("/").ino
            n = w.mark()
            for op, extra in (("FILL-LOOKUP", {"parent": str(root), "name": "a"}),
                              ("FILL-READDIR", {"ino": str(root)})):
                f = {"id": "1", "op": op, "class": "FILL", "uid": str(UID),
                     "gid": "1000", "pid": "42"}
                f.update(extra)
                status, _fl, _p = w.port.handle(f, b"")
                self.assertEqual(status, 0, op)
            self.assertEqual(w.stream_since(n), [],
                             "a fill appended a record, which would make it a decision")
        finally:
            w.close()


if __name__ == "__main__":
    unittest.main()
