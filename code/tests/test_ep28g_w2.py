# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28G W2 — THE RACE, EXHIBITED THEN CLOSED, at the gate's own combinations.

RE-SCOPED 2026-08-02 BY THE SPAN RULING, and the re-scope is the finding under the rows.
This item first named the PORT's races — the inode `next_ino` stamps and the POSIX
`EEXIST`/`ENOENT` preconditions — and every one of them is decided in `src/bridge/`, BEFORE
`gate.execute` is called. `design/10` §11.1a classes the port's precondition outcomes as
ABSENCE ("the call is a read, so a record appearing is the failure"), and under ADDENDUM 1's
identity — THE DECISION IS THE RECORD — a precondition returning `EEXIST` produces no record
and is therefore not a decision. A region whose subject is decisions does not extend to cover
reads that answer. The four original combinations were enumerated from file-op SEMANTICS
rather than from WHICH SIDE OF THE LINE DECIDES THEM, which is why they named cases the
component under test never sees.

So the subject here is the GATE'S OWN combinations, and the subject of the enumeration is the
GATE'S OWN CHECK KINDS — computed from the engine's own check set at build, so a check kind
added to the gate later joins BY THE ENUMERATION rather than by staling a list in this file.

  T-DECIDE-APPEND-ATOMIC          N concurrent CREATE-OP submissions of ONE name yield
                                  exactly ONE recorded definition and N-1 refusals citing
                                  their rule. RED: the region neutered — both concurrent
                                  CREATE-OPs pass the shadow check at `opdefs.py`'s
                                  `create_op` and both append, two definitions for one name
                                  exhibited THROUGH THE REAL GATE PATH.
  T-PRECONDITION-UNDER-CONCURRENCY
                                  THE FLOOR IS AN ASSERTION, NOT PROSE, and it runs first:
                                  the enumerated kind set CONTAINS the four cited sites, and
                                  a short enumeration REDS on that clause before any
                                  serial-equivalence clause runs. A computed subject can
                                  SHRINK, and a row over a shrunken set greens — it cannot
                                  tell "every kind is serial-equivalent" from "there were no
                                  kinds to check". It is the founding block's own shape,
                                  `ls-files >= 1` before the identity. RED for the floor: an
                                  enumeration double returning three kinds, unreachable by
                                  every serial-equivalence clause because those still pass
                                  for the kinds that remain. RED per kind: the region
                                  neutered, each generated through the gate path.
"""

import ast
import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import opdefs as opdefs_mod                          # noqa: E402
from kernel.compose import build_full_kernel                     # noqa: E402
from kernel.errors import OpError                                # noqa: E402

ORDINARY_DEF = {"description": "an ordinary op", "params": {"x": "required"},
                "law_cited": "SIGHT-IS-LAW", "object_param": "x", "checks": [],
                # x is the op's object_param — a scalar identity handle, safe inline. Classified
                # STRUCTURAL so this well-formed setup op passes the vocabulary door (design/46
                # member 2; archi :2956 RULING 1 — object_param => structural, not blanket).
                "structural_params": ["x"]}

#: The rendezvous bound. It is a WEDGE DETECTOR and never a measurement: with the region in
#: place the second decider cannot arrive, so the barrier times out and the act proceeds; with
#: the region neutered both arrive and the race is exhibited deterministically rather than by
#: hoping two threads interleave.
MEET_S = 0.35


class _NeuteredRegion:
    """THE REGION, NEUTERED — which is `gate.py` exactly as it stood before this EP: no lock,
    no guarded span, the append site bare. `enter` reports itself outermost so the durability
    wait still happens, and the depth counter is left untouched so the barrier's own guard
    sees what it saw before the construct existed. ONE variable changes: whether decides
    exclude each other."""

    def enter(self):
        return True

    def exit(self):
        pass


def rendezvous(n, timeout=MEET_S):
    """A meeting point for `n` deciders, used to make a check-then-append race REPEATABLE
    through the real gate path (§A42) instead of hoping the scheduler interleaves.

    Returns a callable that blocks until `n` deciders have reached it or the bound expires.
    With the region in place the second decider cannot reach it, so the first waits out the
    bound and proceeds — the true positive pays the bound and asserts nothing about it."""
    barrier = threading.Barrier(n)

    def meet():
        try:
            barrier.wait(timeout=timeout)
        except threading.BrokenBarrierError:
            pass
    return meet


# =====================================================================================
# THE ENUMERATION — computed from the gate's own check set, never from a list here
# =====================================================================================

def enumerate_gate_check_kinds():
    """THE GATE'S OWN CHECK KINDS, COMPUTED. Two families, both read out of the engine:

    (a) THE DECLARED CHECK VOCABULARY — `opdefs.OP_CHECKS`, the engine's own tuple, paired
        with the dispatch site that runs each one. A kind added to the gate later appears
        here without this file being touched, which is the whole reason the subject is
        computed. A declared kind with NO dispatch site is itself a finding and reds.

    (b) THE HANDLER-LEVEL SHADOW CHECKS — a boot handler that reads the LIVE REGISTRY and
        refuses on what it finds. These carry no `checks` entry (their ops declare
        `"checks": []`), so the declared vocabulary cannot see them; they are discovered
        structurally, as a function in `opdefs.py` that both reads the registry and refuses.
        `create_op`'s is the gate's own instance of the `next_ino` race — two concurrent
        CREATE-OPs of one name both pass `gate.has(name)` and both append — and it is fully
        inside the region.

    Returns {kind: (file, line)}."""
    src = open(opdefs_mod.__file__, encoding="utf-8").read()
    tree = ast.parse(src)
    where = os.path.basename(opdefs_mod.__file__)
    kinds = {}

    dispatch = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and node.comparators:
            left, right = node.left, node.comparators[0]
            is_check_key = (isinstance(left, ast.Subscript)
                            and isinstance(getattr(left, "slice", None), ast.Constant)
                            and left.slice.value == "check")
            if is_check_key and isinstance(right, ast.Constant):
                dispatch.setdefault(right.value, node.lineno)
    for name in opdefs_mod.OP_CHECKS:
        kinds["check:" + name] = (where, dispatch.get(name))

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        reads = refuses = None
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                called = getattr(inner.func, "attr", None) or getattr(inner.func, "id", None)
                if called in ("has", "live_definitions") and reads is None:
                    reads = inner.lineno
                if called == "refuse" and refuses is None:
                    refuses = inner.lineno
        if reads is not None and refuses is not None:
            kinds["shadow:" + node.name] = (where, reads)
    return kinds


#: THE FLOOR. Four sites the enumeration MUST contain, named by their stable identity rather
#: than by a line number: a line number is a stored copy of a computable fact and reds on
#: every unrelated edit above it, which is the staling this estate has found four times in a
#: week. The plan cites them as `opdefs.py:673` (create_op's shadow check), `:717` (amend_op's),
#: `require_prior` at `:363` and `consistency` at `:283-291`; the enumeration reports the line
#: it actually found for each, and the assertion is on the KIND being present in the file the
#: plan cites. [DECLARED READING, EP-28G, raised so it can be overturned in one word: if the
#: floor is meant to pin the integers, this clause pins the wrong thing and the cost is that a
#: refactor of `opdefs.py` reds an unrelated EP.]
FLOOR = ("shadow:create_op", "shadow:amend_op", "check:require_prior", "check:consistency")


def assert_floor(case, kinds):
    """THE CLAUSE THAT MAKES THE OTHER CLAUSES TRUSTWORTHY, factored so it can be run against
    a DOUBLE and be seen to red."""
    missing = [k for k in FLOOR if k not in kinds]
    case.assertEqual(missing, [],
                     "the enumerated kind set is short by %r — a serial-equivalence clause "
                     "over a shrunken set greens, and cannot tell 'every kind is serial-"
                     "equivalent' from 'there were no kinds to check'" % (missing,))
    for k in FLOOR:
        where, line = kinds[k]
        case.assertEqual(where, "opdefs.py",
                         "%s was found in %s and the plan cites opdefs.py" % (k, where))
        case.assertIsInstance(line, int, "%s has no site" % k)


class WorldCase(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28g-w2-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.rec, os.path.join(self.dir, "blobs"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.addCleanup(self.store.close)

    def neuter(self):
        real = self.gate.region
        self.gate.region = _NeuteredRegion()
        self.addCleanup(setattr, self.gate, "region", real)

    def drive(self, n, body, timeout=20):
        """`n` concurrent deciders through the REAL gate path. Returns the verdicts in
        submission-thread order: None for a permit, the cited rule for a refusal."""
        out = [None] * n
        start = threading.Barrier(n)

        def one(i):
            start.wait(timeout=30)
            try:
                body(i)
                out[i] = "PERMITTED"
            except OpError as e:
                out[i] = "REFUSED:" + str(getattr(e, "rule", "") or e.args[0])
            except BaseException as e:                # noqa: BLE001 — reported, never hidden
                out[i] = "ERROR:" + type(e).__name__
        threads = [threading.Thread(target=one, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=timeout)
        for t in threads:
            self.assertFalse(t.is_alive(), "a decider wedged")
        return out

    def definitions_of(self, name):
        return [e for e in self.store.by_action("CREATE-OP")
                if (e.get("payload") or {}).get("name") == name]


# =====================================================================================
# T-DECIDE-APPEND-ATOMIC — the gate's OWN race, closed
# =====================================================================================

class DecideAppendAtomicCase(WorldCase):
    """THE MECHANISM, from the ruling: two concurrent decides that both read a pre-state and
    both append produce an outcome neither would have permitted. `create_op` reads
    `gate.has(name)` and refuses ROOT-NEG-6 — *a definition may not shadow the active
    registry* — so two concurrent CREATE-OPs of one name both pass that read and both append.
    Same shape as the port's `next_ino`, and fully inside the region."""

    def _race(self, n=2):
        meet = rendezvous(n)
        real_has = self.gate.has

        def watched(name):
            answer = real_has(name)
            if name == "DUP":
                meet()                       # both deciders hold the same answer, here
            return answer
        self.gate.has = watched
        self.addCleanup(setattr, self.gate, "has", real_has)
        return self.drive(n, lambda i: self.gate.execute(
            "CREATE-OP", "owner", {"name": "DUP", "definition": ORDINARY_DEF}))

    def test_exactly_one_definition_is_recorded_and_the_rest_refuse_citing_their_rule(self):
        verdicts = self._race(n=2)
        self.assertEqual(len(self.definitions_of("DUP")), 1,
                         "%d definitions were recorded for one name — two decides both "
                         "passed the shadow check and both appended"
                         % len(self.definitions_of("DUP")))
        self.assertEqual(sorted(verdicts).count("PERMITTED"), 1, verdicts)
        refusals = [v for v in verdicts if v.startswith("REFUSED")]
        self.assertEqual(len(refusals), 1, verdicts)
        self.assertIn("ROOT-NEG-6", refusals[0],
                      "the loser did not cite the rule that refused it: %r" % refusals[0])
        # ARITHMETIC RECONCILED ACROSS THE BATCH BOUNDARY: one definition, one refusal
        # record, and the record file holds every one of them.
        self.assertEqual(len(self.store.by_action("op-refused")), 1)
        with open(self.rec, encoding="utf-8") as fh:
            self.assertEqual(sum(1 for line in fh if line.strip()), len(self.store.all()))

    def test_red_world_the_region_neutered_records_two_definitions_for_one_name(self):
        """RED WORLD, GENERATED, THROUGH THE REAL GATE PATH. With the region neutered — which
        is `gate.py` exactly as it stood before this EP — both decides read `gate.has("DUP")`
        as False, both proceed, and both append.

        UNREACHABLE BY EVERY REPLY AND SYNC CLAUSE: nothing about durability moved. Both
        records are on the file, both callers were answered, and the barrier ran. What fails
        is the atomicity clause and only that, which is why the region needs its own row."""
        self.neuter()
        verdicts = self._race(n=2)
        self.assertEqual(len(self.definitions_of("DUP")), 2,
                         "the neutered region did not exhibit the double append — verdicts "
                         "%r — so this red world proves nothing" % (verdicts,))
        self.assertEqual(verdicts.count("PERMITTED"), 2, verdicts)
        # The sync and reply clauses are STILL GREEN in this world.
        with open(self.rec, encoding="utf-8") as fh:
            self.assertEqual(sum(1 for line in fh if line.strip()), len(self.store.all()))


# =====================================================================================
# T-PRECONDITION-UNDER-CONCURRENCY — the floor first, then serial equivalence per kind
# =====================================================================================

class PreconditionUnderConcurrencyCase(WorldCase):

    def setUp(self):
        # THE FLOOR RUNS BEFORE ANY SERIAL-EQUIVALENCE CLAUSE, and it runs HERE rather than as
        # a sibling row because sibling rows have no order. Unittest runs methods
        # alphabetically, so a floor written as its own row would run AFTER
        # `test_the_absence_demanding_...` and `test_the_consistency_kind_...`, and in a
        # short-enumeration world those two would green first and be read as evidence. In
        # `setUp` a short enumeration ERRORS every row in this class and NOT ONE
        # serial-equivalence clause runs at all — which is what the directed clause asks for,
        # stated as ordering rather than hoped for from a naming convention.
        assert_floor(self, enumerate_gate_check_kinds())
        super().setUp()

    # ---- the floor -----------------------------------------------------------------
    def test_the_floor_the_enumerated_kind_set_contains_the_four_cited_sites(self):
        """The floor with its own name, so a reader can find it and a verdict can cite it.
        `setUp` has already run it; this row is the statement, not the enforcement."""
        assert_floor(self, enumerate_gate_check_kinds())

    def test_the_enumeration_is_computed_and_not_a_list_in_this_file(self):
        """The reason the floor is needed at all: the subject SHRINKS if the engine shrinks.
        Every declared kind must have a dispatch site, and the set must come from the
        engine's own tuple rather than from a literal here."""
        kinds = enumerate_gate_check_kinds()
        for name in opdefs_mod.OP_CHECKS:
            self.assertIn("check:" + name, kinds)
            self.assertIsNotNone(kinds["check:" + name][1],
                                 "%r is declared in OP_CHECKS and the engine dispatches it "
                                 "nowhere — a check kind that cannot run" % name)
        self.assertGreater(len(kinds), len(FLOOR),
                           "the enumeration found only the floor, so it is a list wearing a "
                           "function's name")

    def test_red_world_an_enumeration_double_returning_three_kinds_reds_the_floor(self):
        """RED WORLD FOR THE FLOOR, GENERATED. A double returns three kinds instead of four.
        The floor clause REDS on it.

        AND IT IS UNREACHABLE BY EVERY SERIAL-EQUIVALENCE CLAUSE, which is the point: those
        clauses still PASS for the kinds that remain, because the kinds that remain really
        are serial-equivalent. That is exactly the world prose could not distinguish from a
        healthy one."""
        full = enumerate_gate_check_kinds()
        short = {k: v for k, v in full.items() if k != "check:consistency"}
        self.assertEqual(len(short), len(full) - 1)
        with self.assertRaises(AssertionError) as caught:
            assert_floor(self, short)
        self.assertIn("short by", str(caught.exception))
        # AND THE ORDERING, ASSERTED rather than described: the floor is this class's `setUp`,
        # so under a short enumeration every serial-equivalence row in it ERRORS before its
        # body runs. A floor that only reds as a sibling row would let those rows green first.
        self.assertIn("assert_floor", ast.dump(next(
            n for n in ast.walk(ast.parse(open(__file__, encoding="utf-8").read()))
            if isinstance(n, ast.FunctionDef) and n.name == "setUp"
            and any(getattr(getattr(c, "func", None), "id", None) == "assert_floor"
                    for c in ast.walk(n)))),
            "the floor is not this class's setUp — the equivalence clauses can run first")
        # THE UNREACHABILITY, EXHIBITED rather than argued: every clause that already passed
        # still passes over the shrunken set.
        for name in opdefs_mod.OP_CHECKS:
            if name != "consistency":
                self.assertIn("check:" + name, short)
        # And the CONTROL, so the double is a discriminator: the real enumeration passes.
        assert_floor(self, full)

    # ---- the structural universal --------------------------------------------------
    def test_every_enumerated_kind_runs_inside_the_region_by_construction(self):
        """THE UNIVERSAL OVER KINDS, and it is structural because that is what makes it a
        universal rather than a sample. Every declared check is dispatched inside the check
        loop, which runs inside a handler; every shadow check is inside a handler; and a
        handler is invoked from exactly one place, `gate._decide`, which is inside the region.
        So the fold read of ANY check kind and the act's append are inside one region, and
        serial equivalence holds for a kind nobody has driven — including one added tomorrow.

        THE DRIVEN INSTANCES BELOW ARE NOT THIS CLAIM'S EVIDENCE; they are the four floor
        kinds exhibited so the structural claim is not the only thing standing."""
        gate_src = open(
            os.path.join(os.path.dirname(opdefs_mod.__file__), "gate.py"),
            encoding="utf-8").read()
        self.assertEqual(gate_src.count('entry["handler"](actor, params)'), 1,
                         "a handler is invoked from more than one site, so 'inside the "
                         "region' no longer follows from where the handlers are called")
        tree = ast.parse(gate_src)
        decide = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "_decide")

        def invokes_a_handler(fn):
            for node in ast.walk(fn):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Subscript)
                        and isinstance(node.func.slice, ast.Constant)
                        and node.func.slice.value == "handler"):
                    return True
            return False
        self.assertTrue(invokes_a_handler(decide),
                        "the handler invocation is not inside the region's body, so nothing "
                        "makes a check kind's fold read part of the decide")
        others = [n.name for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name != "_decide"
                  and invokes_a_handler(n)]
        self.assertEqual(others, [],
                         "%r also invoke a handler — a check kind can be reached outside the "
                         "region" % (others,))
        kinds = enumerate_gate_check_kinds()
        self.assertTrue(kinds, "nothing was enumerated")

    # ---- the driven instances, one per floor kind ----------------------------------
    def _amend_race(self, n=2):
        meet = rendezvous(n)
        real = opdefs_mod.live_definitions

        def watched(store):
            answer = real(store)
            meet()
            return answer
        opdefs_mod.live_definitions = watched
        self.addCleanup(setattr, opdefs_mod, "live_definitions", real)
        return self.drive(n, lambda i: self.gate.execute(
            "AMEND-OP", "owner", {"name": "GHOST", "definition": ORDINARY_DEF}))

    def test_the_prior_demanding_kind_is_serial_equivalent(self):
        """`check:require_prior`. Concurrent submissions of an op whose definition demands a
        prior record: every outcome matches a serial order — a permit only where the prior
        was already recorded, a refusal citing its rule otherwise, never a torn read that
        permits on a prior it did not see."""
        self.gate.execute("CREATE-OP", "owner", {
            "name": "NEEDS-PRIOR",
            "definition": {"description": "demands a prior", "params": {"x": "required"},
                           "law_cited": "SIGHT-IS-LAW", "object_param": "x",
                           # x is the object_param — scalar identity handle, structural inline.
                           "structural_params": ["x"],
                           "checks": [{"check": "require_prior", "param": "x",
                                       "action": "CREATE-OP", "field": "name",
                                       "cite": "ROOT-NEG-1"}]}})
        meet = rendezvous(2)
        real = self.store.by_action

        def watched(action, as_of_seq=None):
            answer = real(action, as_of_seq)
            if action == "CREATE-OP":
                meet()
            return answer
        self.store.by_action = watched
        self.addCleanup(setattr, self.store, "by_action", real)
        verdicts = self.drive(2, lambda i: self.gate.execute(
            "NEEDS-PRIOR", "owner", {"x": "NO-SUCH-PRIOR"}))
        self.assertEqual([v for v in verdicts if v.startswith("ERROR")], [], verdicts)
        for v in verdicts:
            self.assertTrue(v.startswith("REFUSED"),
                            "an act permitted itself on a prior that was never recorded: %r"
                            % (verdicts,))
            self.assertIn("ROOT-NEG-1", v)

    def test_the_consistency_kind_is_serial_equivalent(self):
        """`check:consistency`. Two concurrent CREATE-RULEs proposing CONTRADICTING exclusive
        values on ONE policy key. Exactly one may become active: the check reads the active
        rules and refuses ROOT-NEG-6 on a contradiction, so two decides that both read the
        pre-state and both append would activate a contradiction neither would have
        permitted."""
        meet = rendezvous(2)
        real = self.views.active_rules

        def watched(*a, **k):
            answer = real(*a, **k)
            meet()
            return answer
        self.views.active_rules = watched
        self.addCleanup(setattr, self.views, "active_rules", real)

        def body(i):
            self.gate.execute("CREATE-RULE", "owner", {
                "rule_id": "R%d" % i, "text": "exclusive on one key",
                "policy_key": "KEY", "value": "v%d" % i, "exclusive": True})
        verdicts = self.drive(2, body)
        self.assertEqual([v for v in verdicts if v.startswith("ERROR")], [], verdicts)
        active = [r for r in self.views.active_rules().values()
                  if r.get("policy_key") == "KEY" and r.get("exclusive")]
        values = {r.get("value") for r in active}
        self.assertEqual(len(values), 1,
                         "%d contradicting exclusive values are active on one policy key: %r"
                         % (len(values), values))
        self.assertEqual(verdicts.count("PERMITTED"), 1, verdicts)

    def test_red_world_the_region_neutered_activates_a_contradiction(self):
        """RED WORLD for the consistency kind, GENERATED through the gate path. With the
        region neutered both decides read the same active-rule set, neither sees the other,
        and BOTH append — the world the consistency check exists to make unreachable.

        Unreachable by the clauses that already passed: both records are durable, both
        callers were answered, and the shadow-check row above is untouched."""
        self.neuter()
        meet = rendezvous(2)
        real = self.views.active_rules

        def watched(*a, **k):
            answer = real(*a, **k)
            meet()
            return answer
        self.views.active_rules = watched
        self.addCleanup(setattr, self.views, "active_rules", real)

        def body(i):
            self.gate.execute("CREATE-RULE", "owner", {
                "rule_id": "R%d" % i, "text": "exclusive on one key",
                "policy_key": "KEY", "value": "v%d" % i, "exclusive": True})
        verdicts = self.drive(2, body)
        self.views.active_rules = real
        active = [r for r in real().values()
                  if r.get("policy_key") == "KEY" and r.get("exclusive")]
        values = {r.get("value") for r in active}
        self.assertEqual(verdicts.count("PERMITTED"), 2, verdicts)
        self.assertEqual(len(values), 2,
                         "the neutered region did not activate a contradiction (%r), so this "
                         "red world proves nothing" % (values,))

    def test_the_absence_demanding_shadow_kinds_are_serial_equivalent(self):
        """`shadow:create_op` and `shadow:amend_op`, the two handler-level registry reads.
        `create_op` demands the name is ABSENT; `amend_op` demands it is LIVE. Concurrent
        submissions of each produce an outcome matching a serial order: at most one create
        succeeds, and an amend of a name no serial order ever made live always refuses."""
        meet = rendezvous(2)
        real_has = self.gate.has

        def watched(name):
            answer = real_has(name)
            if name == "TWICE":
                meet()
            return answer
        self.gate.has = watched
        self.addCleanup(setattr, self.gate, "has", real_has)
        verdicts = self.drive(2, lambda i: self.gate.execute(
            "CREATE-OP", "owner", {"name": "TWICE", "definition": ORDINARY_DEF}))
        self.assertEqual(verdicts.count("PERMITTED"), 1, verdicts)
        self.gate.has = real_has

        amend = self._amend_race(2)
        self.assertEqual([v for v in amend if v.startswith("ERROR")], [], amend)
        for v in amend:
            self.assertTrue(v.startswith("REFUSED"),
                            "an AMEND-OP of a name that was never live was permitted: %r"
                            % (amend,))
            self.assertIn("ROOT-NEG-6", v)

    def test_the_verdict_set_is_deterministic_under_interleaving(self):
        """"The verdict set deterministic under interleaving" — the same submission set
        produces the same verdicts in every run, order aside. Asserted on a MULTISET across
        fresh worlds, because which THREAD wins is scheduling and is not the claim; what a
        retry-based design would break is that the SET is stable at all."""
        seen = []
        for _ in range(3):
            case = PreconditionUnderConcurrencyCase("test_the_floor_the_enumerated_kind_set_"
                                                    "contains_the_four_cited_sites")
            case.setUp()
            try:
                meet = rendezvous(3)
                real_has = case.gate.has

                def watched(name, _real=real_has, _meet=meet):
                    answer = _real(name)
                    if name == "STABLE":
                        _meet()
                    return answer
                case.gate.has = watched
                verdicts = case.drive(3, lambda i: case.gate.execute(
                    "CREATE-OP", "owner", {"name": "STABLE", "definition": ORDINARY_DEF}))
                seen.append(tuple(sorted(verdicts)))
            finally:
                case.doCleanups()
        self.assertEqual(len(set(seen)), 1,
                         "the same submission set produced different verdict sets across "
                         "runs: %r — a decide whose recorded basis depends on scheduler "
                         "timing" % (seen,))
        self.assertEqual(seen[0].count("PERMITTED"), 1, seen[0])


class TheFloorGatesTheEquivalenceClausesCase(unittest.TestCase):
    """THE ORDERING, DRIVEN. The directed clause says a short enumeration must red BEFORE any
    serial-equivalence clause runs. That is a claim about EXECUTION, so it is measured by
    executing it: install a short enumeration, run the whole class, and count what ran.

    In its own class so it is not a member of the set it measures."""

    def _run_the_class_under(self, enumeration):
        real = enumerate_gate_check_kinds
        globals()["enumerate_gate_check_kinds"] = enumeration
        try:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(
                PreconditionUnderConcurrencyCase)
            result = unittest.TestResult()
            suite.run(result)
            return result
        finally:
            globals()["enumerate_gate_check_kinds"] = real

    def test_a_short_enumeration_stops_every_row_at_the_floor(self):
        """THE RED WORLD FOR THE ORDERING ITSELF. With `shadow:create_op` removed from the
        enumeration, EVERY row in the class stops in `setUp` at the floor and not one
        serial-equivalence body executes. A floor written as a sibling row would fail this:
        unittest runs methods alphabetically, `test_the_absence_...` and
        `test_the_consistency_...` both sort before `test_the_floor_...`, and both would have
        GREENED first over a set that was missing a kind."""
        real = enumerate_gate_check_kinds
        result = self._run_the_class_under(
            lambda: {k: v for k, v in real().items() if k != "shadow:create_op"})
        self.assertGreater(result.testsRun, 4, "the class barely has rows to gate")
        stopped = result.failures + result.errors
        self.assertEqual(len(stopped), result.testsRun,
                         "%d of %d rows survived a short enumeration — a serial-equivalence "
                         "clause greened over a set that was missing a kind"
                         % (result.testsRun - len(stopped), result.testsRun))
        for _test, tb in stopped:
            self.assertIn("assert_floor", tb,
                          "a row stopped somewhere other than the floor:\n%s" % tb)
            self.assertIn("short by", tb)

    def test_the_control_the_real_enumeration_lets_every_row_run(self):
        """THE CONTROL, without which the row above proves only that a broken world breaks:
        under the REAL enumeration the same class runs green, so what the red world moved is
        the floor and nothing else."""
        result = self._run_the_class_under(enumerate_gate_check_kinds)
        self.assertEqual(result.failures + result.errors, [],
                         "the class is not green under its own enumeration")
        self.assertGreater(result.testsRun, 4)


if __name__ == "__main__":
    unittest.main()
