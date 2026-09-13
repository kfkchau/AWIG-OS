"""EP-28C W4e.C — THE ITEM THE LAW CHANGE REOPENED: WHAT TWO CONCURRENT CREATES OF ONE
PATH DO UNDER FOUNDING 1.18.0.

THE QUESTION, AS THE MENTOR PUT IT AND NOT AS A HYPOTHESIS (release note, 2026-08-08):

  Under the OLD law W4e exhibited it — two records, both deriving ONE identity, the served
  state correct, and THE RECORD HOLDING AN ACT NOBODY PERFORMED. Under 1.18.0 they derive
  DISTINCT identities from distinct birth acts. SO THE OLD ANSWER IS NOT THE ANSWER, and the
  new one is not established. ESTABLISH IT. Do not assume it is fixed and do not assume it
  is broken.

WHAT THIS FILE ESTABLISHES, DRIVEN AND NOT READ: two concurrent creates of one path record
ONE birth and ONE refusal, the refusal citing `FS-LAW-NAMESPACE` and carrying `EEXIST`,
under a constructed interleaving that puts the two callers in the worst order for the
property. The serialized arm and the interleaved arm agree on every countable.

AND THE MECHANISM IS NAMED RATHER THAN CREDITED TO THE WRONG LAW, which is the whole reason
the red world below exists. **It is EP-28K's declared `binding:unbound` check, evaluated
INSIDE the decide region, that closes this — not EP-28S's identity law.** The two changes
landed close together and the tempting reading is that the coordinate identity fixed the
race. It did not: the coordinate makes the two identities DISTINCT, and distinctness is
exactly what turns a silent overwrite into a stranded node. Neuter the check and 1.18.0's
identity law produces a WORSE world than 1.17.0's, not a better one — two birth records,
two live identities, and the first node reachable under no name at all. That is what
`TestTheRedWorld` drives.

THE CHECK'S OWN DECLARED MESSAGE IS THE W4e EXHIBITION, WORD FOR WORD, which is how the
founding says what this file measures:

  "the name is already held in the living namespace, and a create that recorded an act over
   it would be a second act on one name — the state would still be right and the record
   would hold a create nobody performed"

NON-VACUITY BINDS EVERY EQUALITY ROW HERE (AMENDMENT 8.1's clause, from close item 49):
agreement does not imply either side exists, so both sides are proven non-empty before any
comparison counts. `TestTheSubjectExists` is that proof and it runs its own positive control
— the walker is shown finding a KNOWN-PRESENT declaration before any absence is reported.

§A64 BINDS THE STRUCTURAL ROWS: each carries a near-miss both ways — one construct that
SHOULD match spelled differently, one that should NOT spelled similarly, both driven.

THE HARNESS IS IMPORTED, NEVER COPIED. `serialized_arm` and `interleaved_arm` live in
`tests/test_ep28c_w4e_c.py` and are this EP's own; duplicating them here would be one
computation across a boundary (M4) and the two copies would drift on the next ruling.
"""

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

from bridge.kernel_port import KernelPort                               # noqa: E402
from bridge.mount import build_brain                                    # noqa: E402
from bridge import custody                                              # noqa: E402
from kernel import opdefs                                               # noqa: E402

from test_ep28c_w4e_c import (                                          # noqa: E402
    _World, _wire, interleaved_arm, serialized_arm,
)

FOUNDING = os.path.join(REPO, "src", "founding", "founding-pack.json")
GOVOSFS_C = os.path.join(REPO, "planning", "vm", "govosfs", "govosfs.c")

#: The act this file drives. ONE path, two callers, the create that mints.
THE_PATH = "/a"
THE_ACT = ("FILE-CREATE", {"path": THE_PATH, "perm": "644"}, ())


def _minting_definitions():
    """The three minting ops' definitions, WALKED from the founding rather than listed.

    A hand list goes stale the first time an op joins or leaves the minting class and does it
    silently, which is the class this estate keeps finding. The walker's own competence is
    proven by `test_the_walker_finds_a_known_present_declaration_first` before any row here
    reports an absence."""
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


def _births(store, since, path):
    """Every birth record for one path in a window, read from the RECORD."""
    return [r for r in store.all()[since:]
            if r.get("action") in custody.MINTING_ACTIONS
            and custody._norm(((r.get("payload") or {}).get("path"))) == path]


def _refusals(store, since):
    return [r for r in store.all()[since:] if r.get("action") == "op-refused"]


class TestTheSubjectExists(unittest.TestCase):
    """NON-VACUITY AND THE POSITIVE CONTROL, BEFORE ANY COUNT IS REPORTED.

    A taking that reports a count first demonstrates its instrument finds a KNOWN-PRESENT
    case. A zero without a positive control is uninterpretable and is not a count."""

    def test_the_walker_finds_a_known_present_declaration_first(self):
        d = _minting_definitions()
        # THE POSITIVE CONTROL: a declaration nobody disputes is present.
        self.assertIn("FILE-CREATE", d,
                      "the walker cannot find FILE-CREATE in the founding — every absence "
                      "this file reports below would be an artefact of a broken walk")
        self.assertGreaterEqual(len(d), 10,
                                "the walker found %d definitions, which is too few for this "
                                "founding — it is not walking the pack" % len(d))

    def test_the_three_minting_ops_declare_the_coordinate_law_and_the_unbound_check(self):
        d = _minting_definitions()
        for op in custody.MINTING_ACTIONS:
            with self.subTest(op=op):
                spec = d.get(op)
                self.assertIsNotNone(spec, "%s is not declared in the founding" % op)
                self.assertEqual(spec.get("mints_from"), "record_coordinate",
                                 "%s does not mint from the record coordinate — this file's "
                                 "whole subject is the law that says it does" % op)
                self.assertNotIn("inode", spec.get("params") or {},
                                 "%s still takes an inode parameter — a caller could put an "
                                 "identity in the record and the coordinate law would not be "
                                 "the only source" % op)
                unbound = [c for c in (spec.get("checks") or [])
                           if c.get("check") == "binding"
                           and c.get("key_param") == "path"
                           and c.get("require") == "unbound"]
                self.assertEqual(len(unbound), 1,
                                 "%s declares %d binding:unbound checks over its path and the "
                                 "mechanism this file measures is exactly one of them"
                                 % (op, len(unbound)))
                self.assertEqual(unbound[0].get("cite"), "FS-LAW-NAMESPACE")

    def test_both_arms_act_and_leave_a_real_world(self):
        """NON-VACUITY FOR EVERY EQUALITY ROW BELOW: both sides proven non-empty."""
        op, path, extra = THE_ACT
        for name, arm in (("serialized", serialized_arm), ("interleaved", interleaved_arm)):
            with self.subTest(arm=name):
                first, second, refused, acted, after, before = arm(op, path, extra)
                self.assertNotEqual(sorted(after), sorted(before),
                                    "the %s arm left the namespace unchanged — it did not "
                                    "act, so anything it agrees about is agreement between "
                                    "two empty worlds" % name)
                self.assertIn(THE_PATH, after,
                              "the %s arm did not bind the path it was driving" % name)
                self.assertGreaterEqual(acted + refused, 2,
                                        "the %s arm recorded %d acts for two callers"
                                        % (name, acted + refused))


class TestWhatTwoConcurrentCreatesOfOnePathNowDo(unittest.TestCase):
    """THE ESTABLISHMENT. Driven, both arms, on the countables the old exhibition moved.

    The old exhibition's signature was TWO birth records for one path. That is the countable
    this class reads, and it reads it from the RECORD rather than from the served state,
    because the whole point of the original finding is that the served state was CORRECT
    while the record was wrong. A row that checked the namespace would have passed then."""

    def setUp(self):
        op, path, extra = THE_ACT
        self.ser = serialized_arm(op, path, extra)
        self.inter = interleaved_arm(op, path, extra)

    def test_the_interleaved_arm_records_ONE_birth_and_ONE_refusal(self):
        _first, _second, refused, acted, _after, _before = self.inter
        self.assertEqual(acted, 1,
                         "two concurrent creates of one path recorded %d births. ONE is the "
                         "property; more than one is the finding W4e exhibited returning "
                         "under a new identity law." % acted)
        self.assertEqual(refused, 1,
                         "the second create recorded %d refusals — the declared check "
                         "refuses and RECORDS, so exactly one is owed" % refused)

    def test_the_two_arms_converge_on_every_countable(self):
        s_first, s_second, s_ref, s_act, s_after, _sb = self.ser
        i_first, i_second, i_ref, i_act, i_after, _ib = self.inter
        self.assertEqual((s_ref, s_act), (i_ref, i_act),
                         "the record depends on the arrival order: serialized recorded "
                         "(refusals=%d, births=%d) and interleaved recorded (%d, %d)"
                         % (s_ref, s_act, i_ref, i_act))
        self.assertEqual(s_after, i_after,
                         "the two arms served different namespaces")
        self.assertEqual(sorted([s_first, s_second]), sorted([i_first, i_second]),
                         "the two arms answered their callers differently")

    def test_exactly_one_caller_is_told_EEXIST_and_the_other_is_told_yes(self):
        for name, arm in (("serialized", self.ser), ("interleaved", self.inter)):
            with self.subTest(arm=name):
                first, second, _r, _a, _af, _bf = arm
                self.assertEqual(sorted([first, second]), sorted([0, -E.EEXIST]),
                                 "the %s arm answered %r and %r; one caller takes the name "
                                 "and the other is told the name is taken"
                                 % (name, first, second))

    def test_the_one_identity_minted_is_the_birth_acts_OWN_coordinate(self):
        """THE 1.18.0 HALF, AND IT IS WHAT THE OLD ANSWER GOT WRONG.

        The exhibition's signature was two records deriving ONE identity. This asserts the
        surviving birth's identity is `formal_name(seq)` of that record and of nothing else,
        so a future law that reintroduced a content-derived identity reds here."""
        w = _World()
        try:
            n = len(w.store.all())
            self.assertEqual(w.call("FILE-CREATE", path=THE_PATH, perm="644"), 0)
            born = _births(w.store, n, THE_PATH)
            self.assertEqual(len(born), 1, "expected one birth, got %d" % len(born))
            rec = born[0]
            self.assertIsNone((rec.get("payload") or {}).get("inode"),
                              "the birth record names an identity — under 1.18.0 the minting "
                              "ops write none and the coordinate is the only source")
            expected = custody.formal_name(rec.get("seq"))
            node = w.port.state.lookup(THE_PATH)
            self.assertIsNotNone(node, "the fold did not bind the path it just created")
            self.assertEqual(node.identity, expected,
                             "the fold named the node %r where the birth act's own "
                             "coordinate derives %r" % (node.identity, expected))
        finally:
            w.close()

    def test_the_refusal_the_second_caller_causes_cites_the_DECLARED_law(self):
        w = _World()
        try:
            self.assertEqual(w.call("FILE-CREATE", path=THE_PATH, perm="644"), 0)
            n = len(w.store.all())
            self.assertEqual(w.call("FILE-CREATE", path=THE_PATH, perm="644"), -E.EEXIST)
            refs = _refusals(w.store, n)
            self.assertEqual(len(refs), 1,
                             "the second create recorded %d refusals" % len(refs))
            self.assertEqual(refs[0].get("rule_cited"), "FS-LAW-NAMESPACE",
                             "the refusal cites %r — the check that produced it declares "
                             "FS-LAW-NAMESPACE" % refs[0].get("rule_cited"))
        finally:
            w.close()

    def test_kill_it_replay_and_the_served_state_is_identical(self):
        """THE ESTATE'S ONE DETECTOR, applied to the world two concurrent creates leave.

        A record holding an act nobody performed is not visible in the served state — that
        is the original finding's whole shape — so this row compares the SERVED fold against
        a fold rebuilt from the record alone. They agree only if the record holds exactly the
        history the served state was built from."""
        op, path, extra = THE_ACT
        w = _World()
        try:
            a_at_door = threading.Event()
            b_done = threading.Event()
            real_params, real_exec = w.port._params_for, w.gate.execute

            def pre(o, f, payload):
                answer = real_params(o, f, payload)
                if threading.current_thread().name == "B":
                    b_done.set()
                return answer

            def ex(name, actor, params=None):
                if threading.current_thread().name == "A":
                    a_at_door.set()
                    b_done.wait(20)
                return real_exec(name, actor, params)

            w.port._params_for, w.gate.execute = pre, ex
            outcomes = {}

            def run(tag):
                outcomes[tag] = w.call(op, **path)

            ta = threading.Thread(target=run, args=("A",), name="A")
            tb = threading.Thread(target=run, args=("B",), name="B")
            ta.start()
            self.assertTrue(a_at_door.wait(20), "thread A never reached the gate door")
            tb.start()
            ta.join(30)
            tb.join(30)
            served = w.port.state.snapshot()
            replayed = custody.fold(w.store.all()).snapshot()
            self.assertTrue(served.get("inodes"),
                            "the served snapshot is empty — an equality over two empty "
                            "things is agreement about nothing")
            self.assertEqual(served, replayed,
                             "the served state and the state replayed from the record alone "
                             "disagree after two concurrent creates of one path")
        finally:
            w.close()


class TestTheRedWorld(unittest.TestCase):
    """THE MECHANISM NAMED BY MAKING IT FAIL, and the clause it fails is stated.

    RED WORLD: the declared `binding:unbound` check is neutered — nothing else moves. THE
    CLAUSE THIS MAKES FAIL: 'two concurrent creates of one path record ONE birth'. It is
    unreachable by every clause that already passed — the region still serializes, the
    identities are still coordinate-derived, the replay still folds, and the callers are
    still both answered. Only the birth count moves.

    AND WHAT IT SHOWS IS THE FILE'S SECOND FINDING: under 1.18.0 the failure MODE is worse
    than 1.17.0's, not better. Two distinct identities mean the fold's collision guard cannot
    see them (it tests `held.identity != identity` at one RENDERED number, and two distinct
    identities render to two different numbers), so nothing raises — the second birth simply
    rebinds the name and the first node is left reachable under no name at all."""

    def _drive_with_check(self, neutered):
        op, path, extra = THE_ACT
        real = opdefs._binding_check
        if neutered:
            opdefs._binding_check = lambda *a, **k: None
        try:
            w = _World()
            try:
                n = len(w.store.all())
                a_at_door = threading.Event()
                b_done = threading.Event()
                real_params, real_exec = w.port._params_for, w.gate.execute

                def pre(o, f, payload):
                    answer = real_params(o, f, payload)
                    if threading.current_thread().name == "B":
                        b_done.set()
                    return answer

                def ex(name, actor, params=None):
                    if threading.current_thread().name == "A":
                        a_at_door.set()
                        b_done.wait(20)
                    return real_exec(name, actor, params)

                w.port._params_for, w.gate.execute = pre, ex
                out = {}

                def run(tag):
                    out[tag] = w.call(op, **path)

                ta = threading.Thread(target=run, args=("A",), name="A")
                tb = threading.Thread(target=run, args=("B",), name="B")
                ta.start()
                assert a_at_door.wait(20), "thread A never reached the gate door"
                tb.start()
                ta.join(30)
                tb.join(30)
                born = _births(w.store, n, THE_PATH)
                identities = [custody.formal_name(r.get("seq")) for r in born]
                bound = w.port.state.names.get(THE_PATH)
                live = {nd.identity for nd in w.port.state.inodes.values()}
                return born, identities, bound, live, dict(out)
            finally:
                w.close()
        finally:
            opdefs._binding_check = real

    def test_the_check_is_the_mechanism_and_neutering_it_reds_the_birth_count(self):
        born, identities, _bound, _live, _out = self._drive_with_check(neutered=True)
        self.assertEqual(len(born), 2,
                         "the red world did not reach its own condition: with the declared "
                         "check neutered both creates must reach the append, and %d did"
                         % len(born))
        self.assertEqual(len(set(identities)), 2,
                         "the two births derived %d distinct identities — under 1.18.0 two "
                         "birth acts sit at two coordinates and must derive two"
                         % len(set(identities)))

    def test_the_red_world_STRANDS_the_first_node_under_no_name(self):
        """WHAT THE 1.18.0 FAILURE MODE ACTUALLY IS, driven rather than argued."""
        born, identities, bound, live, _out = self._drive_with_check(neutered=True)
        self.assertEqual(len(born), 2, "the red world did not reach its condition")
        reachable = {custody.render_ino(i) for i in identities if custody.render_ino(i) == bound}
        self.assertEqual(len(reachable), 1,
                         "the path binds %r and the two births rendered %r — exactly one of "
                         "two live nodes is reachable by name"
                         % (bound, [custody.render_ino(i) for i in identities]))
        for i in identities:
            self.assertIn(i, live,
                          "identity %r is not in the fold's inode table — the red world's "
                          "claim is that BOTH nodes are live and only one is named" % (i,))

    def test_NEAR_MISS_the_same_construction_with_the_check_LIVE_records_one(self):
        """§A64 BOTH WAYS: the construction that produces two with the check neutered
        produces exactly one with it live, so the row measures the CHECK and not the
        interleaving."""
        born, identities, bound, _live, out = self._drive_with_check(neutered=False)
        self.assertEqual(len(born), 1,
                         "the same construction recorded %d births with the check LIVE — "
                         "then the red world above is measuring the interleaving rather "
                         "than the check" % len(born))
        self.assertEqual(sorted(out.values()), sorted([0, -E.EEXIST]))
        self.assertEqual(bound, custody.render_ino(identities[0]))


class TestTheDrivenBeforeOpenSet(unittest.TestCase):
    """THE SET RE-DERIVED FROM THE CODE, NOT CARRIED FROM THE PLAN'S LINE NUMBERS.

    The plan names four members at `kernel_port.py:413`, `:429`, `:430`, `:441`. THOSE ARE
    ANCHOR-RELATIVE AND VOID — the file has been inside two fences since they were written —
    and the mentor's release note says so and re-derives them as a POINTER, not a pin. This
    class enumerates the live pre-gate reads from the AST of `_decide` itself, so a member
    that moves is still found and a member that RETIRES is reported rather than skipped.

    §A64 NEAR-MISS BOTH WAYS: a call placed before the gate under a name this walk has never
    seen is still found; a call to the same name placed AFTER the gate is not counted as
    pre-gate. Both driven on the walk's own generalisation — position, not spelling."""

    #: RETIRED, AND NAMED RATHER THAN DROPPED. `_posix_precondition` was the third member of
    #: the plan's set. W4e.R retired it (2026-08-07). A member that vanishes from a
    #: population constant cannot tell a retirement from a typo, so it is asserted ABSENT.
    RETIRED_AT_W4E_R = "_posix_precondition"

    def _pre_gate_calls(self, src=None):
        """Every `self.X(...)` on the decision path that runs BEFORE `self.gate.execute`."""
        if src is None:
            import bridge.kernel_port as kp
            with open(kp.__file__, encoding="utf-8") as fh:
                src = fh.read()
        tree = ast.parse(src)
        fn = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_decide":
                fn = node
                break
        assert fn is not None, "no `_decide` in the port — the walk has no subject"
        seen, gate_seen = [], False
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr == "execute":
                gate_seen = True
        # POSITION IS READ OFF THE LINE NUMBER, which is what "before the gate" means in a
        # body with no branches between them. The gate call's own line is the boundary.
        gate_line = min([n.lineno for n in ast.walk(fn)
                         if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute)
                         and n.func.attr == "execute"] or [10 ** 9])
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                val = node.func.value
                if isinstance(val, ast.Name) and val.id == "self" and node.lineno < gate_line:
                    # THE CLOSURE-HIT EXIT IS NOT A PRE-GATE READ, and it is excluded by the
                    # same rule the retired raise-3b walk used rather than by a new one:
                    # `_refuse_unregistered` RETURNS, so nothing downstream of it reaches the
                    # gate at all. Excluding it by prefix keeps the walk positional
                    # everywhere else — a new `_refuse_*` exit is still excluded, and any
                    # other new name is still found.
                    if not node.func.attr.startswith("_refuse"):
                        seen.append(node.func.attr)
        assert gate_seen, "no gate.execute call inside `_decide`"
        return sorted(set(seen))

    def test_the_walk_finds_a_KNOWN_PRESENT_member_first(self):
        """POSITIVE CONTROL before any absence below is reported."""
        calls = self._pre_gate_calls()
        self.assertIn("_prov", calls,
                      "the walk cannot find `_prov`, which is on the decision path before "
                      "the gate — every absence this class reports would be an artefact")

    def test_the_live_set_is_the_three_the_code_holds(self):
        calls = self._pre_gate_calls()
        self.assertEqual(calls, ["_carries_port_provenance", "_params_for", "_prov"],
                         "the pre-gate read set has moved to %r. It is re-derived live on "
                         "purpose, so this is a report and not a failure — name the new "
                         "member, drive it, and update this row." % (calls,))

    def test_the_RETIRED_member_is_absent_and_SAID_TO_BE_RETIRED(self):
        calls = self._pre_gate_calls()
        self.assertNotIn(self.RETIRED_AT_W4E_R, calls,
                         "%s is back on the decision path" % self.RETIRED_AT_W4E_R)
        import bridge.kernel_port as kp
        with open(kp.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("def %s" % self.RETIRED_AT_W4E_R, src)

    def test_NEAR_MISS_a_pre_gate_call_under_an_unseen_name_is_still_found(self):
        src = (
            "class K:\n"
            "    def _decide(self, op, f, payload):\n"
            "        a = self._a_name_this_walk_has_never_seen(f)\n"
            "        return self.gate.execute(op, a, {})\n"
        )
        self.assertIn("_a_name_this_walk_has_never_seen", self._pre_gate_calls(src),
                      "the walk keys on a name list rather than on position")

    def test_NEAR_MISS_the_same_call_placed_AFTER_the_gate_is_not_pre_gate(self):
        src = (
            "class K:\n"
            "    def _decide(self, op, f, payload):\n"
            "        rec = self.gate.execute(op, 'a', {})\n"
            "        return self._prov(rec)\n"
        )
        self.assertEqual(self._pre_gate_calls(src), [],
                         "the walk counted a call that runs AFTER the gate as pre-gate — it "
                         "is keying on spelling and not on position")

    def test_each_live_member_is_DRIVEN_and_its_window_measured(self):
        """DRIVEN UNDER 1.18.0, across the outcomes the declarations permit.

        Each member is wrapped so the drive can observe what it answered, and the two arms
        are compared on the RECORD. A member whose answer differs between the arms is a
        window the channel would open; a member whose answer is identical has none."""
        op, path, extra = THE_ACT
        for member in ("_prov", "_params_for", "_carries_port_provenance"):
            with self.subTest(member=member):
                answers = {}

                def make(w, name):
                    real = getattr(w.port, name)

                    def wrapped(*a, **k):
                        out = real(*a, **k)
                        answers.setdefault(name, []).append(repr(out))
                        return out

                    return wrapped

                w = _World()
                try:
                    setattr(w.port, member, make(w, member))
                    self.assertEqual(w.call(op, **path), 0)
                    self.assertEqual(w.call(op, **path), -E.EEXIST)
                finally:
                    w.close()
                got = answers.get(member) or []
                self.assertEqual(len(got), 2,
                                 "%s was called %d times over two acts — the drive did not "
                                 "reach it on both outcomes" % (member, len(got)))
                self.assertEqual(got[0], got[1],
                                 "%s answered %r on the permit and %r on the refusal — a "
                                 "pre-gate read whose answer depends on the outcome is a "
                                 "window many-in-flight would open" % (member, got[0], got[1]))


class TestTheFillHandedAnInodeMintedOneActAgo(unittest.TestCase):
    """THE MEMBER WHOSE HAZARD DISSOLVED — REPORTED, NEVER QUIETLY SKIPPED.

    The mentor's release note puts this in item 3's set: *`a fill can be handed an inode
    minted ONE ACT AGO` sits in the same set and was written under path-identity. Same
    treatment.* So it gets the same treatment, and the treatment's answer is that the hazard
    is GONE — which is a finding and is stated as one rather than dropped from the list.

    WHAT IT WAS, UNDER PATH-IDENTITY: identity was derived from the path, so unlinking `/a`
    and creating a new `/a` derived THE SAME identity and therefore the same rendered inode.
    A fill still holding the number from the first file was answered about the second, with
    nothing anywhere able to tell them apart — the fold's collision guard tests
    `held.identity != identity` and those two were EQUAL.

    WHAT IT IS UNDER 1.18.0: identity is the birth act's own record coordinate, so the two
    files sit at two coordinates and render to two numbers. A handed-out number names exactly
    one birth act, permanently. There is no window to open.

    AND THE OTHER HALF — that there is no gap between a create's reply and the fold holding
    what it named — is driven rather than argued, because that is the half many-in-flight
    would actually stress."""

    def test_the_replys_inode_is_ALREADY_in_the_fold_when_the_create_returns(self):
        """NO WINDOW BETWEEN REPLY AND FOLD. The fold advance runs inside `_publish`, which
        runs inside the decide region, so `gate.execute` cannot return before the listener
        has folded. This drives that rather than citing it."""
        w = _World()
        try:
            status, fields, _payload = w.port.handle(
                _wire("FILE-CREATE", path="/fresh", perm="644"), b"")
            self.assertEqual(status, 0, "the create did not succeed; the drive did not run")
            ino = fields.get("ino")
            self.assertIsNotNone(ino, "the create's reply carried no inode")
            node = w.port._node_by_wire({"ino": ino}, "ino")
            self.assertIsNotNone(node,
                                 "the fold does not hold the inode the reply just handed "
                                 "out — a fill issued on it would raise out of `handle`")
            self.assertEqual(w.port.state.lookup("/fresh").ino, custody.parse_ino(ino))
        finally:
            w.close()

    def test_unlink_then_recreate_of_ONE_path_yields_TWO_DIFFERENT_inodes(self):
        """THE DISSOLVED HAZARD, DRIVEN. Under path-identity these two were EQUAL."""
        w = _World()
        try:
            s1, f1, _ = w.port.handle(_wire("FILE-CREATE", path="/reused", perm="644"), b"")
            self.assertEqual(s1, 0)
            self.assertEqual(w.call("FILE-UNLINK", path="/reused"), 0)
            s2, f2, _ = w.port.handle(_wire("FILE-CREATE", path="/reused", perm="644"), b"")
            self.assertEqual(s2, 0)
            self.assertNotEqual(f1.get("ino"), f2.get("ino"),
                                "the recreated path was handed the SAME inode %r — the "
                                "coordinate identity law has come undone and a fill holding "
                                "the first file's number is answered about the second"
                                % (f1.get("ino"),))
        finally:
            w.close()

    def test_the_first_births_number_still_names_the_FIRST_birth_after_the_reuse(self):
        """THE PROPERTY THAT MATTERS TO A FILL: a number handed out before the reuse is not
        silently redirected to the file that took the name."""
        w = _World()
        try:
            _s1, f1, _ = w.port.handle(_wire("FILE-CREATE", path="/reused", perm="644"), b"")
            first = custody.parse_ino(f1.get("ino"))
            n = len(w.store.all())
            born_first = _births(w.store, 0, "/reused")
            self.assertEqual(len(born_first), 1)
            self.assertEqual(w.call("FILE-UNLINK", path="/reused"), 0)
            _s2, f2, _ = w.port.handle(_wire("FILE-CREATE", path="/reused", perm="644"), b"")
            second = custody.parse_ino(f2.get("ino"))
            self.assertNotEqual(first, second)
            node = w.port.state.inodes.get(first)
            self.assertIsNotNone(node,
                                 "the first birth's node is gone from the fold — a fill "
                                 "holding its number would raise rather than answer")
            self.assertEqual(node.identity, custody.formal_name(born_first[0].get("seq")),
                             "the first number now names a different birth act")
            self.assertEqual(w.port.state.names.get("/reused"), second,
                             "the path does not name the SECOND birth after the reuse")
            self.assertGreater(len(w.store.all()), n)
        finally:
            w.close()


class TestTheOneFoldReadOutsideTheOrdering(unittest.TestCase):
    """RAISE 3, HOMED HERE BY §11.2 AND DRIVEN RATHER THAN READ.

    EP-28R landed shape (a): the port constructs one re-entrant `_fold_order` and BOTH
    fold-reading fills take it. What survives is exactly ONE fold read that still runs
    outside the ordering — `_node_by_wire` reached from `_params_for`, on the DECISION path,
    before the gate.

    THIS CLASS ESTABLISHES WHY THAT ONE CANNOT TEAR WHERE THE FILLS COULD, and the reason is
    a property of the table rather than a property of the caller: it is a SINGLE-KEY read on
    `state.inodes`, and `state.inodes` is APPEND-ONLY — no unlink, no rmdir, no rename ever
    removes an entry from it. So a fold advance running concurrently can only ADD a key the
    read did not ask for. The fills' reads are the near-miss: they walk `kids` / `names`,
    which `_bind` and `_unbind` MUTATE, which is exactly why shape (a) put them inside the
    ordering and why this one did not need to be.

    THE CAP, PLAINLY: this establishes that the surviving read cannot tear. It does NOT
    establish that the channel is safe to open — that is the transport question, and it is
    raised, not answered here."""

    def _port_src(self):
        import bridge.kernel_port as kp
        with open(kp.__file__, encoding="utf-8") as fh:
            return fh.read()

    def _fold_reads_outside_the_ordering(self, src=None):
        """Every `self.state.X` / `self._node_by_wire(...)` read NOT lexically inside a
        `with self._fold_order:` block, keyed on the AST rather than on indentation."""
        tree = ast.parse(src if src is not None else self._port_src())
        guarded = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                names = [n for n in ast.walk(node)
                         if isinstance(n, ast.Attribute) and n.attr == "_fold_order"]
                if names:
                    for inner in ast.walk(node):
                        guarded.add(id(inner))
        found = []
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            for node in ast.walk(fn):
                if id(node) in guarded:
                    continue
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) \
                        and node.value.attr == "state" and isinstance(node.value.value, ast.Name) \
                        and node.value.value.id == "self":
                    if fn.name not in ("_on_append",):
                        found.append((fn.name, node.attr))
        return sorted(set(found))

    def test_both_fold_reading_fills_take_the_ordering(self):
        """POSITIVE CONTROL for the walk: the two fills are known to be guarded, so a walk
        that reported them as unguarded is broken and every count below is an artefact."""
        outside = {fn for fn, _attr in self._fold_reads_outside_the_ordering()}
        for fill in ("_fill_lookup", "_fill_readdir"):
            self.assertNotIn(fill, outside,
                             "%s reads the fold outside the ordering — EP-28R's shape (a) "
                             "has come undone, or this walk cannot see a `with` block" % fill)

    def test_the_LEXICALLY_unguarded_fold_reads_are_the_two_the_code_holds(self):
        """TWO LEXICAL SITES, AND THE WALK CANNOT TELL REACHABILITY — said rather than
        hidden. `_node_fields` is reached ONLY from the two fills, which hold the ordering
        across the whole call; `_node_by_wire` is reached from those same fills AND from
        `_params_for` on the decision path, where nothing holds it. So exactly one of these
        two is genuinely read without the ordering, and it is the one the next row drives."""
        outside = self._fold_reads_outside_the_ordering()
        self.assertEqual(outside,
                         [("_node_by_wire", "inodes"), ("_node_fields", "mode")],
                         "the set of lexically unguarded fold reads has moved to %r. It is "
                         "re-derived live, so this is a REPORT: name the new member, "
                         "establish whether it can tear, and update this row." % (outside,))

    def test_the_table_that_read_touches_is_APPEND_ONLY_driven(self):
        """DRIVEN: the property the safety rests on, exhibited rather than asserted."""
        w = _World()
        try:
            self.assertEqual(w.call("FILE-CREATE", path="/gone", perm="644"), 0)
            node = w.port.state.lookup("/gone")
            self.assertIsNotNone(node)
            ino = node.ino
            self.assertIn(ino, w.port.state.inodes)
            self.assertEqual(w.call("FILE-UNLINK", path="/gone"), 0)
            self.assertIsNone(w.port.state.lookup("/gone"),
                              "the unlink did not remove the NAME — the drive did not act")
            self.assertIn(ino, w.port.state.inodes,
                          "the unlink removed the identity from `inodes`. That table is what "
                          "the one unguarded read touches, and if it can shrink under a "
                          "concurrent fold advance then this read CAN tear and the channel's "
                          "safety argument needs the ordering extended to it.")
        finally:
            w.close()

    def test_NEAR_MISS_the_container_the_fills_walk_DOES_shrink(self):
        """§A64 THE OTHER WAY: the same act that leaves `inodes` alone empties the container
        a readdir fill walks — which is why the fills are inside the ordering and this read
        is not. Without this row the one above proves only that nothing changed."""
        w = _World()
        try:
            self.assertEqual(w.call("FILE-MKDIR", path="/d", perm="755"), 0)
            self.assertEqual(w.call("FILE-CREATE", path="/d/f", perm="644"), 0)
            self.assertEqual(sorted(w.port.state.children("/d")), ["f"])
            self.assertEqual(w.call("FILE-UNLINK", path="/d/f"), 0)
            self.assertEqual(sorted(w.port.state.children("/d")), [],
                             "the container did not shrink — then the near-miss is not a "
                             "near-miss and the append-only row above proves nothing")
        finally:
            w.close()


class TestTheChannelIsStillOneCaller(unittest.TestCase):
    """THE TRANSPORT FACT, ASSERTED HERE RATHER THAN CLAIMED IN AN ENTRY.

    A conclusion resting on another file's row is a conclusion nobody re-checks, so this
    file states its own subject: the module still admits ONE caller. Every finding above is
    about what happens WHEN that changes, and a reader must be able to see from this file
    that it has not changed yet."""

    def _c(self):
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            return fh.read()

    def test_the_one_caller_lowering_is_still_in_the_module(self):
        src = self._c()
        self.assertIn("DEFINE_MUTEX(govos_call_lock)", src,
                      "the one-caller mutex is gone from govosfs.c — if the channel opened, "
                      "every row in this file is measuring a world that no longer exists "
                      "and the entry must say which pass opened it")

    def test_the_channel_still_holds_ONE_request_slot(self):
        """THE PROPERTY, NOT THE LOCK. A queue keyed by transport id would make the mutex
        removable; a single slot makes it load-bearing. This reads the slot."""
        src = self._c()
        for sym in ("govos_req_pending", "govos_rep_ready", "govos_req_len"):
            self.assertIn(sym, src,
                          "%s is gone — the single-slot transport has changed shape and the "
                          "one-caller reading above no longer follows from the mutex" % sym)

    def test_NEAR_MISS_a_mutex_under_another_name_would_not_satisfy_this_row(self):
        self.assertNotIn("DEFINE_MUTEX(govos_call_lock)",
                         "static DEFINE_MUTEX(govos_other_lock);",
                         "the row matches any mutex rather than the one-caller one")


if __name__ == "__main__":
    unittest.main()
