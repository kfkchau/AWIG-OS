"""EP-28O — ONE canonical spelling per name, computed once and read everywhere.

Every probe here is a regression test (the campaign method: a verification probe lands as
a test).

WHAT THIS PASS DECIDES, AND WHAT IT DELIBERATELY DOES NOT. The namespace has had a
canonical spelling since EP-25: `custody._norm`, documented as "the namespace's canonical
spelling of a path". The FOLD called it and the LAW's key derivation did not, so a
directory made as `/a/` was key `/a/` to the law and name `/a` to the namespace — one
object under two keys — and every question the law could ask about a name answered about a
namespace it was not in. This pass makes the key derivation CALL the computer that already
existed. It mints no richer canonical form and it does not touch the OTHER direction of the
same root — one key over two objects, which is rename-recreate and belongs to EP-28P.

THE §A52 COUNTABLE IS THE SPINE: ONE computer, N readers. Two computers is how a
convention gets built where a rule was wanted, and it is how the law and the fold came to
disagree in the first place. `TestOneCanonicaliser` counts, and its red world is a second
computer planted in a copy of the source.

THE NAMED WRONG REFERENCES THIS BATTERY REFUSES.
  1. DEFENSIVE NORMALISATION — every consumer canonicalising "to be safe". Detector:
     `TestOneCanonicaliser`'s count, taken over both fenced trees from the source text.
  2. REWRITING RECORDED KEYS. Detector: `TestHistoryIsUntouched` — a world whose records
     hold non-canonical keys replays to exactly the derivation it always had, and the
     non-vacuity clause asserts that world is non-empty before the comparison is read.
  3. CANONICALISATION CREEP — resolving `..`, collapsing case, chasing links, collapsing
     interior separators. Detector: `TestNormIsTheSpec`, which asserts the key the law
     records equals `custody._norm` of the input EXACTLY, including the two cases where
     `_norm` does LESS than a reader expects.
  4. THE PASS-TWO BLEED — reading a spelling fix as an identity fix. Detector:
     `TestTheMutabilityDoorIsSTILLOPEN`, which drives rename-recreate on two ALREADY
     CANONICAL spellings and asserts the collision is exactly as it was.

Coverage (the EP's named battery):
  T-RESOLVER-ESTABLISHED  W1's citation, asserted against the code rather than written in
                          prose: the `$path` resolution site and the canonicalisation that
                          now precedes it, both located structurally.
  T-ONE-CANONICALISER     the canonical form is computed at exactly one site; the readers
                          are counted; a planted second computer reds the count.
  T-KEY-IS-CANONICAL      the ruled drive through the real path; and the reachable pre-fix
                          exhibition — a lawful act REFUSED over a directory that plainly
                          exists — driven through the loaded module with the one added
                          function removed.
  T-SPELLINGS-CONVERGE    two spellings of one name yield ONE key in both directions and
                          refuse as the duplicate they are; two genuinely distinct names
                          stay distinct, driven on the least-likely member of `_norm`'s
                          own behaviour (§A49).
  T-DEGENERATE-IDENTICAL  an already-canonical world records byte-identical payloads with
                          and without this pass's one function.
  T-NORM-IS-THE-SPEC      the pass's canonical behaviour equals `_norm`'s, exactly.
  THE LEASH               every op declaring a key check today cites the namespace law —
                          asserted, so the first key space that is not a path REDS.
"""
import ast
import contextlib
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bridge import custody                                        # noqa: E402
from kernel import opdefs                                         # noqa: E402
from kernel.compose import build_full_kernel                      # noqa: E402
from bridge.kernel_port import KernelPort                          # noqa: E402
from kernel.errors import OpError                                 # noqa: E402

OWNER = "owner"
PROV = {"uid": 1000, "gid": 1000, "pid": 42, "window": "test"}

NAMESPACE_LAW = "FS-LAW-NAMESPACE"

OPDEFS_PATH = os.path.join(REPO, "src", "kernel", "opdefs.py")
CUSTODY_PATH = os.path.join(REPO, "src", "bridge", "custody.py")

#: THE TWO TREES THE FENCE HOLDS. The count below is taken over these and no others, so a
#: canonicaliser planted anywhere the fence licenses is inside the measurement.
FENCED_TREES = (os.path.join(REPO, "src", "kernel"), os.path.join(REPO, "src", "bridge"))

#: THE CANONICAL FORM ITSELF, as source text. This is what a SECOND COMPUTER would look
#: like: not a call to `_norm` but a re-derivation of what `_norm` returns. Written as a
#: pattern rather than a literal so a copy that spells its variable differently is still
#: counted — a second computer that renamed its argument is still a second computer.
CANONICAL_FORM = re.compile(r'"/"\s*\+\s*\w+(?:\.\w+\(\))?\.strip\(\s*"/"\s*\)')

#: THE READER'S SPELLING. Every site that needs a canonical spelling calls the one computer
#: through this expression, in both trees, so N is countable from the source.
READER_CALL = re.compile(r'(?<!def )_norm\(')


@contextlib.contextmanager
def canonicalisation_removed():
    """THE PRE-FIX ENGINE, THROUGH THE LOADED MODULE (item 24).

    Not a description of what the code used to do and not a hand-built payload: the ONE
    function this pass added is made to answer "this definition declares no keys", which is
    exactly the state `_interpreter` was in before it — `param_defaults` resolving `$path`
    from whatever string the caller spelled, and the checks comparing that string as
    recorded. A world built inside this block is the world EP-28K and EP-28N measured.

    IT MUST WRAP THE BUILD, NOT THE ACT. The declared-key set is read ONCE, when a
    definition is registered onto the gate, so a kernel composed outside this block keeps
    the canonicalisation whatever happens inside it."""
    original = opdefs._declared_keys
    opdefs._declared_keys = lambda d: ()
    try:
        yield
    finally:
        opdefs._declared_keys = original


class _World:
    """A kernel composed from the SHIPPED founding and nothing else."""

    def __init__(self, tmp):
        self.dir = tmp
        self.record = os.path.join(tmp, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(tmp, "blobs"), os.path.join(tmp, "vault"))

    def act(self, op, **params):
        params.setdefault("provenance", PROV)
        return self.gate.execute(op, OWNER, params)

    def keys(self):
        """The law's live key set — what the gate compares an incoming key against.

        DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05): the ROOT IS EXCLUDED HERE, exactly
        as `names()` has always excluded it, and for the same reason turned around. That pass
        declares the root on the law that governs the key space — it is bound by declaration
        and by no act, because nothing creates it — so `_live_bindings` now returns it and
        every row in this file would otherwise carry it. This file's whole subject is
        SPELLINGS, and the root is neither spelled by a caller nor recorded by an act, so
        subtracting it here is what keeps `keys()` and `names()` comparable, which is the
        comparison this file exists to make. THE PROPERTY ITSELF IS NOT HIDDEN: it is
        asserted directly in `tests/test_ep28n2.py`, and `tests/test_ep28k.py`'s
        root-is-substrate row was FLIPPED by that pass rather than adjusted."""
        return set(opdefs._live_bindings(self.store, self.views)) - {"/"}

    def names(self):
        """The namespace fold's names, root excluded (it is substrate, not a recorded name)."""
        return set(custody.fold(self.store.all()).names) - {"/"}

    def recorded(self, action, field="path"):
        return [(e.get("payload") or {}).get(field) for e in self.store.by_action(action)]


class _Tmp(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28o-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def world(self):
        return _World(tempfile.mkdtemp(dir=self.dir))

    def pre_fix_world(self):
        with canonicalisation_removed():
            return _World(tempfile.mkdtemp(dir=self.dir))


# ---------------------------------------------------------------------------------------
# T-RESOLVER-ESTABLISHED — W1's citation, resolved against the code
# ---------------------------------------------------------------------------------------
class TestTheResolverIsWhereW1SaidItIs(unittest.TestCase):
    """W1's establishment, carried as an assertion rather than as a sentence in a log.

    THE CITATION: `$path` resolves in `kernel/opdefs.py`, inside `_interpreter`'s `run`, in
    the `param_defaults` loop — the branch that reads a `$`-prefixed default as the name of
    another parameter. That one line is the whole of the law's identity derivation: the
    identity a minting op records is the value of the parameter the default names.

    THE LAYER SPLIT W1 STATES: BEFORE this pass, everything below `gate.execute` saw the
    RAW spelling (the identity, the payload, the object, the law's key set) and everything
    in `bridge/custody.py` saw the CANONICAL one, because the fold calls `_norm` at every
    door. AFTER it, the canonical spelling is computed once, above the `$path` resolution,
    so both sides read one value.

    This row's falsifiability is the citation resolving against the code (§A38's shape): a
    resolver that moved, or a canonicalisation that stopped preceding it, reds here."""

    def _run_body(self):
        with open(OPDEFS_PATH, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        interp = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "_interpreter")
        run = next(n for n in ast.walk(interp)
                   if isinstance(n, ast.FunctionDef) and n.name == "run")
        return run

    def test_the_dollar_resolution_site_is_inside_the_param_defaults_loop_in_run(self):
        run = self._run_body()
        starts = [n for n in ast.walk(run)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "startswith"
                  and any(isinstance(a, ast.Constant) and a.value == "$" for a in n.args)]
        self.assertEqual(len(starts), 1,
                         "the `$`-prefixed default is resolved at exactly one site in `run`")

    def test_the_canonicalisation_precedes_it_IN_THE_SAME_FUNCTION(self):
        """ORDERING IS A PROPERTY OF THE CODE, NOT OF PROSE (§A48). If the canonical
        spelling were computed after the defaults resolved, the identity would still be
        minted from the raw string and this pass would be green and useless."""
        run = self._run_body()
        norm_lines = [n.lineno for n in ast.walk(run)
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                      and n.func.attr == "_norm"]
        dollar_lines = [n.lineno for n in ast.walk(run)
                        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "startswith"]
        self.assertEqual(len(norm_lines), 1, "one canonicalising call in `run`")
        self.assertTrue(norm_lines[0] < min(dollar_lines),
                        "the key is canonical BEFORE `$path` resolves from it")

    def test_the_key_parameters_are_read_from_the_definition_not_from_a_list(self):
        """The engine holds no list of parameter names: which parameters carry keys is read
        from each definition's own `binding` and `kind` declarations."""
        d = {"checks": [{"check": "binding", "key_param": "path"},
                        {"check": "kind", "key_param": "path"},
                        {"check": "binding", "key_param": "new_path"},
                        {"check": "sight", "target_param": "not_a_key"}]}
        self.assertEqual(opdefs._declared_keys(d), ("new_path", "path"))
        self.assertEqual(opdefs._declared_keys({"checks": []}), ())
        self.assertEqual(opdefs._declared_keys({}), ())


# ---------------------------------------------------------------------------------------
# T-ONE-CANONICALISER — the §A52 count
# ---------------------------------------------------------------------------------------
def _count_over(paths, pattern):
    hits = []
    for root in paths:
        for base, _dirs, files in os.walk(root):
            for f in sorted(files):
                if not f.endswith(".py"):
                    continue
                p = os.path.join(base, f)
                with open(p, encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        if pattern.search(line):
                            hits.append((os.path.relpath(p, REPO), i, line.strip()))
    return hits


class TestOneCanonicaliser(unittest.TestCase):
    """§A52's countable, asserted structurally in both trees the fence holds.

    ONE COMPUTER, N READERS. The count that matters is the FIRST number: a canonical
    spelling is DERIVED at exactly one site and every other site asks that site for it.
    The second number is informational and is asserted only as a floor, because readers
    growing is the mechanism working."""

    def test_the_canonical_form_is_derived_at_exactly_one_site(self):
        hits = _count_over(FENCED_TREES, CANONICAL_FORM)
        self.assertEqual(len(hits), 1, "two derivations of one spelling: %r" % (hits,))
        path, line, _text = hits[0]
        self.assertEqual(path, os.path.join("src", "bridge", "custody.py"))
        self.assertEqual(custody._norm.__code__.co_firstlineno + 4, line,
                         "the one derivation is inside `_norm` and nowhere else")

    def test_the_counter_CAN_return_two_which_is_what_makes_the_one_evidence(self):
        """THE CAN-FAIL CONTROL. A count that has never returned anything but one proves
        nothing about the tree it walked. A second computer is planted in a copy — the
        SOURCE is never touched — and the same counter returns two."""
        tmp = tempfile.mkdtemp(prefix="ep28o-double-")
        try:
            with open(CUSTODY_PATH, encoding="utf-8") as fh:
                body = fh.read()
            shutil.copyfile(CUSTODY_PATH, os.path.join(tmp, "custody.py"))   # C7 P3b-5c: content only, no file-mode (I7)
            with open(os.path.join(tmp, "second.py"), "w", encoding="utf-8") as fh:
                fh.write('def _defensive(p):\n    return "/" + p.strip("/")\n')
            self.assertEqual(len(_count_over((tmp,), CANONICAL_FORM)), 2)
            self.assertIn('"/" + path.strip("/")', body,
                          "non-vacuity: the one real derivation is the text this counts")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_readers_include_the_law_and_the_fold_and_are_counted(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: the four `custody._norm(` reader LINES inside `_posix_precondition`
        (`f.get("path")`, `f.get("new_path")` twice, `f.get("target_path")`). The floor of 28
        was measured with them present; the retirement removed exactly four and the count
        fell to 26.

        THE FLOOR IS RE-MEASURED AND THE DROP IS ACCOUNTED, NOT ABSORBED — 30 minus the four
        this retirement removed. §A52's spine is the FIRST number: ONE computer. The reader
        count is the informational half and is a floor because readers GROWING is the
        mechanism working; a retirement lowering it is the mechanism working too, and the
        only dishonest move would be to leave a floor nothing can now reach."""
        readers = _count_over(FENCED_TREES, READER_CALL)
        files = {p for p, _l, _t in readers}
        self.assertIn(os.path.join("src", "kernel", "opdefs.py"), files,
                      "the law's key derivation is now a reader — the whole of this pass")
        self.assertIn(os.path.join("src", "bridge", "custody.py"), files)
        self.assertGreaterEqual(len(readers), 26,
                                "the reader floor re-measured at EP-28C W4e: the 28 of this "
                                "pass's start less the four lines inside the retired read")
        # AND THE FOUR ARE ACCOUNTED RATHER THAN ASSUMED: the port keeps readers, and none of
        # them is the retired one, so the drop is a removal and not a reader that stopped
        # asking the one computer.
        port_readers = [l for p, l, _t in readers
                        if p == os.path.join("src", "bridge", "kernel_port.py")]
        self.assertEqual(len(port_readers), 2,
                         "the port's surviving `_norm` readers are the two FILL-path calls")


# ---------------------------------------------------------------------------------------
# T-KEY-IS-CANONICAL
# ---------------------------------------------------------------------------------------
class TestTheKeyIsCanonical(_Tmp):
    """THE RULED WORLD, DRIVEN THROUGH THE REAL PATH: a directory made as `/a/`, then a
    create inside it. The recorded key and the fold's name agree on `/a`, which is the
    property; the create succeeding is the consequence."""

    def test_the_recorded_key_and_the_folds_name_agree(self):
        w = self.world()
        w.act("FILE-MKDIR", path="/a/")
        w.act("FILE-CREATE", path="/a/b")
        self.assertEqual(w.recorded("FILE-MKDIR"), ["/a"],
                         "the law records the canonical spelling")
        self.assertEqual(w.keys(), {"/a", "/a/b"})
        self.assertEqual(w.names(), {"/a", "/a/b"},
                         "the law's keys and the fold's names are the SAME SET")

    def test_the_identity_the_founding_derives_is_the_canonical_spelling(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]

        ASSERTED (2026-08-04, EP-28O): `$path` resolves from the CANONICAL value, so a minting
        op records the canonical name as its identity rather than the caller's spelling —
        `/a`, never `/a/`.
        SUPERSEDED (2026-08-08, EP-28S, founding 1.18.0): the minting ops no longer resolve
        `$path` into an identity at all. `mints_from: record_coordinate` — the act's position
        names what it founds — so there is no recorded identity for a spelling to be wrong in.
        REMAINS TRUE, separated out and STILL ASSERTED, and it is this FILE's whole subject:
        THE CANONICAL SPELLING IS WHAT THE LAW RECORDS AND WHAT THE FOLD NAMES. The canonical
        form still reaches the record, in the KEY — `payload.path` is `/a`, not `/a/` — and
        the fold still serves the directory under one canonical name. What EP-28S removed is
        the identity's dependence on the spelling, which is a strengthening of this file's own
        thesis rather than a loss: a name that cannot be spelled two ways can no longer be
        SPELLED into a second object either.
        GIVEN UP: the `inode`-field clause. It asserted a mechanism, and the mechanism moved.
        `test_the_recorded_key_and_the_folds_name_agree` above still holds the key/name
        agreement, untouched by this pass."""
        w = self.world()
        w.act("FILE-MKDIR", path="/a/")
        self.assertEqual(w.recorded("FILE-MKDIR"), ["/a"],
                         "the law records the canonical spelling as the act's own key")
        self.assertEqual(w.recorded("FILE-MKDIR", "inode"), [None],
                         "and it records no identity at all — there is nothing here for a "
                         "caller's spelling to have reached")
        state = custody.fold(w.store.all())
        birth = w.store.by_action("FILE-MKDIR")[0]
        self.assertEqual(state.lookup("/a").identity, custody.formal_name(birth["seq"]))
        self.assertIsNone(state.names.get("/a/"), "the non-canonical spelling names nothing")

    def test_THE_PRE_FIX_WORLD_A_LAWFUL_ACT_REFUSED_over_a_directory_that_plainly_exists(self):
        """THE RED WORLD, DRIVEN RATHER THAN DESCRIBED (§A42 — the bytes are kept).

        THIS IS THE EP'S ROW CORRECTED BY W1, AND THE CORRECTION IS THE FINDING. The plan
        named the exhibition as a PARENT check refusing `FILE-CREATE /a/b`. No parent check
        existed — the six `parent_of` members were exactly the ones EP-28N left blocked on
        this defect — so that refusal was not reachable in any world, before or after. The
        refusal that WAS reachable through a DECLARED check is `FILE-RMDIR`'s: it requires
        its key BOUND, the law holds `/a/`, the caller spells `/a`, and a lawful removal of a
        directory the fold plainly serves is refused.

        Same defect, same key space, same arithmetic — a reachable exhibition in place of an
        unreachable one.

        AND THE UNREACHABLE ONE IS NOW REACHABLE (EP-28N AMENDMENT 1, 2026-08-05). That pass
        declares the container rows the mentor's sentence assumed, so the exhibition it named
        can be driven — added below, beside the substituted one rather than in place of it,
        because which of the two this file could reach on the day it was written is part of
        the record. The claim was WRONG WHEN MADE (no such check existed) and it is TRUE NOW
        for a reason that arrived a pass later: §A63's point exactly."""
        pre = self.pre_fix_world()
        pre.act("FILE-MKDIR", path="/a/")
        self.assertEqual(pre.keys(), {"/a/"}, "the law holds the key AS SPELLED")
        self.assertEqual(pre.names(), {"/a"}, "the fold serves it under its canonical name")
        with self.assertRaises(OpError) as raised:
            pre.act("FILE-RMDIR", path="/a")
        self.assertEqual(raised.exception.rule, NAMESPACE_LAW)
        self.assertIn("not held in the living namespace", str(raised.exception),
                      "the declared check's own refusal, not an incidental error")

    def test_AND_THE_EXHIBITION_THE_PLAN_NAMED_IS_NOW_REACHABLE_TOO(self):
        """DOCUMENTED ADDITION (EP-28N AMENDMENT 1). The mentor's own illustration, driven:
        a create into a directory that plainly exists, REFUSED, because the law's key space
        holds `/a/` and the container of `/a/b` is `/a`. It could not go red for two passes
        for one reason — the check did not exist — and the check now does."""
        pre = self.pre_fix_world()
        pre.act("FILE-MKDIR", path="/a/")
        self.assertEqual(pre.names(), {"/a"}, "the fold plainly serves the directory")
        with self.assertRaises(OpError) as raised:
            pre.act("FILE-CREATE", path="/a/b")
        self.assertEqual(raised.exception.rule, NAMESPACE_LAW)
        self.assertEqual(getattr(raised.exception, "requirement", None),
                         "binding:bound@container",
                         "the container row, keyed by the ACT and by WHICH key it asked about")
        self.assertEqual(pre.store.by_action("FILE-CREATE"), [],
                         "and no act was recorded for the refused create")

    def test_and_the_same_act_is_ADMITTED_under_this_pass(self):
        w = self.world()
        w.act("FILE-MKDIR", path="/a/")
        w.act("FILE-RMDIR", path="/a")
        self.assertEqual(w.keys(), set())
        self.assertEqual(w.names(), set())

    def test_the_pre_fix_engine_ADMITTED_the_create_UNTIL_the_container_rows_landed(self):
        """DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05). The sentence this row asserted
        was: "the create succeeds in BOTH worlds, because nothing declares a check over its
        parent." That was TRUE when written and this pass is what falsifies it — the second
        clause is exactly the fact it removes, so the row keeps its drive and its outcome
        moves.

        The undamaged half is kept and is still the point: under the CANONICAL key the same
        create is ADMITTED (the row above), and under the raw key it is REFUSED. Two spellings
        of one directory, one of which the law cannot see — which is what made the pre-fix
        engine's key space a defect rather than a preference."""
        pre = self.pre_fix_world()
        pre.act("FILE-MKDIR", path="/a/")
        with self.assertRaises(OpError):
            pre.act("FILE-CREATE", path="/a/b")
        self.assertEqual(pre.store.by_action("FILE-CREATE"), [])
        self.assertEqual(pre.keys(), {"/a/"},
                         "and the keys disagree with the fold, which is the defect")
        self.assertEqual(pre.names(), {"/a"})

        w = self.world()
        w.act("FILE-MKDIR", path="/a/")
        w.act("FILE-CREATE", path="/a/b")
        self.assertEqual(len(w.store.by_action("FILE-CREATE")), 1,
                         "the same act, under the canonical key, is admitted")


# ---------------------------------------------------------------------------------------
# T-SPELLINGS-CONVERGE
# ---------------------------------------------------------------------------------------
class TestSpellingsConverge(_Tmp):
    """Two spellings of one name yield ONE key, in both directions — and two genuinely
    distinct names stay distinct, driven on the member of `_norm`'s own behaviour LEAST
    likely to share the property (§A49)."""

    def test_trailing_slash_second_refuses_as_the_duplicate_it_is(self):
        w = self.world()
        w.act("FILE-MKDIR", path="/a")
        with self.assertRaises(OpError) as raised:
            w.act("FILE-MKDIR", path="/a/")
        self.assertEqual(raised.exception.rule, NAMESPACE_LAW)
        self.assertEqual(w.keys(), {"/a"})
        self.assertEqual(len(w.store.by_action("FILE-MKDIR")), 1,
                         "and NO act was recorded for the refused one")

    def test_the_other_direction_too(self):
        w = self.world()
        w.act("FILE-MKDIR", path="/a/")
        with self.assertRaises(OpError):
            w.act("FILE-MKDIR", path="/a")
        self.assertEqual(w.keys(), {"/a"})

    def test_the_least_likely_member_a_spelling_with_no_leading_separator(self):
        """§A49's member, NAMED FROM `_norm` ITSELF rather than chosen for convenience.

        `_norm` returns `"/" + path.strip("/")`, so it does two things a reader thinking
        "trailing slash" would not predict: it makes a RELATIVE spelling absolute, and it
        leaves INTERIOR separators alone. The relative spelling is the convergence case
        furthest from the one the defect was observed on."""
        self.assertEqual(custody._norm("a"), "/a")
        w = self.world()
        w.act("FILE-MKDIR", path="/a")
        with self.assertRaises(OpError):
            w.act("FILE-MKDIR", path="a")
        self.assertEqual(w.keys(), {"/a"})

    def test_and_two_genuinely_distinct_names_stay_distinct(self):
        """THE OTHER HALF, and it is the same member read the other way. `_norm` does NOT
        collapse interior separators — `//a//b//` becomes `/a//b` — so `/a//b` and `/a/b`
        are two names to the namespace and stay two keys to the law. A pass that had
        invented a richer canonical form would green the convergence rows and red here."""
        self.assertEqual(custody._norm("//a//b//"), "/a//b")
        self.assertNotEqual(custody._norm("/a//b"), custody._norm("/a/b"))
        w = self.world()
        w.act("FILE-MKDIR", path="/a")
        w.act("FILE-CREATE", path="/a/b")
        # DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05). `/a//b` was ADMITTED as a third
        # key here; it is now REFUSED, and the reason SHARPENS this row rather than weakening
        # it. `/a//b`'s container is `/a/`, which `_norm` does not fold into `/a` — so the
        # two names are still two names, and the second one now has nowhere to live. That is
        # this file's raise 4 (richer canonical semantics were NOT taken) meeting the
        # container law: the distinctness stands and one of the two distinct names became
        # unreachable, which is stated rather than smoothed.
        with self.assertRaises(OpError) as raised:
            w.act("FILE-CREATE", path="/a//b")
        self.assertEqual(getattr(raised.exception, "requirement", None),
                         "binding:bound@container")
        self.assertEqual(custody.parent_of("/a//b"), "/a/",
                         "and the container it names is the one _norm does not fold")
        self.assertEqual(w.keys(), {"/a", "/a/b"})

    def test_THE_PRE_FIX_WORLD_admits_both_spellings_as_two_names(self):
        """The red world for every row above, driven through the loaded module."""
        pre = self.pre_fix_world()
        pre.act("FILE-MKDIR", path="/a")
        pre.act("FILE-MKDIR", path="/a/")
        self.assertEqual(pre.keys(), {"/a", "/a/"}, "the law holds TWO keys")
        self.assertEqual(pre.names(), {"/a"}, "the fold holds ONE name")
        self.assertEqual(len(pre.store.by_action("FILE-MKDIR")), 2,
                         "and TWO acts were recorded over one directory")


# ---------------------------------------------------------------------------------------
# T-NORM-IS-THE-SPEC
# ---------------------------------------------------------------------------------------
class TestNormIsTheSpec(_Tmp):
    """WRONG REFERENCE 3's DETECTOR. What this pass canonicalises to is `_norm`'s answer and
    nothing else — no dot segments, no case folding, no link chasing, no interior collapse.
    Asserted as an equality against the one computer over a table that includes the cases
    where `_norm` does LESS than a reader expects."""

    SPELLINGS = ["/a", "/a/", "a", "a/", "/a/b", "/a/b/", "//a//b//", "/a//b",
                 "/A", "/a/./b", "/a/../b", "/a b", "/a.b"]

    def test_the_key_the_law_records_equals_norm_of_the_input_exactly(self):
        w = self.world()
        landed = []
        for spelling in self.SPELLINGS:
            try:
                w.act("FILE-CREATE", path=spelling)
                landed.append(spelling)
            except OpError:
                pass                       # a duplicate spelling of a name already made
        self.assertGreater(len(landed), 0, "non-vacuity: the world holds acts to compare")
        self.assertEqual(w.recorded("FILE-CREATE"),
                         [custody._norm(s) for s in landed])
        self.assertEqual(w.keys(), {custody._norm(s) for s in landed})

    def test_the_forms_norm_does_NOT_resolve_are_still_distinct_keys(self):
        """Named individually, because each is a namespace SEMANTICS decision this pass
        refuses to take: a dot segment, a parent segment, and a case difference are three
        separate law questions, and all three are raised rather than answered here."""
        for a, b in (("/a/./b", "/a/b"), ("/a/../b", "/b"), ("/A", "/a"), ("/a//b", "/a/b")):
            self.assertNotEqual(custody._norm(a), custody._norm(b), (a, b))


# ---------------------------------------------------------------------------------------
# T-DEGENERATE-IDENTICAL
# ---------------------------------------------------------------------------------------
#: WHAT AN ACT DECIDED, as distinct from when it was decided or where it landed in the
#: sequence. Two runs of one history cannot share a clock or a record id, and comparing
#: those would make the comparison fail for a reason that has nothing to do with this pass.
#: Everything a spelling could reach is in here: the object, the envelope target, the cited
#: law, and the whole payload.
DECIDED = ("actor", "action", "object", "target", "rule_cited", "payload")


def _comparable(store):
    """The records reduced to what each act DECIDED — the fields a canonical spelling can
    reach — so a difference between two runs can only be a difference this pass caused."""
    return [{k: e.get(k) for k in DECIDED} for e in store.all()]


class TestDegenerateIdentical(_Tmp):
    """An ALREADY-CANONICAL world is byte-identical in what it records, with and without
    this pass's one function. The whole change is invisible where the caller already spelled
    the name the way the namespace does — which is every caller that reached the gate
    through a port, because the ports normalise before they ask."""

    HISTORY = [("FILE-MKDIR", {"path": "/d"}),
               ("FILE-CREATE", {"path": "/d/a"}),
               ("FILE-CREATE", {"path": "/b"}),
               ("FILE-SYMLINK", {"path": "/s", "target": "/b"}),
               ("FILE-LINK", {"target_path": "/b", "new_path": "/h"}),
               ("FILE-RENAME", {"path": "/h", "new_path": "/h2"}),
               ("FILE-UNLINK", {"path": "/h2"}),
               ("FILE-RMDIR", {"path": "/d/a"})]

    def _drive(self, w):
        for op, params in self.HISTORY:
            try:
                w.act(op, **params)
            except OpError:
                pass
        return _comparable(w.store)

    def test_identical_records_with_and_without_the_canonicalisation(self):
        after = self._drive(self.world())
        before = self._drive(self.pre_fix_world())
        self.assertGreater(len(after), 0, "non-vacuity: the histories are non-empty")
        self.assertEqual(len(after), len(before))
        self.assertEqual(after, before)


# ---------------------------------------------------------------------------------------
# HISTORY IS UNTOUCHED — derivation-forward, never history-backward
# ---------------------------------------------------------------------------------------
class TestHistoryIsUntouched(_Tmp):
    """WRONG REFERENCE 2's DETECTOR. Records already holding non-canonical keys ARE the
    record. This pass changes what is DERIVED from here on and rewrites nothing: a
    pre-EP-28O world replays to exactly the derivation it always had, under the shipped
    engine, because the fold has always called `_norm` at its own doors and the law has
    always compared keys as recorded."""

    def test_a_world_holding_non_canonical_keys_replays_as_recorded(self):
        """DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05). The non-canonical world is now
        built from `/a/` and `/a//b` rather than `/a/` and `/a/b`: under the container rows a
        create whose container is spelled `/a` cannot land while the law holds `/a/`, so the
        second act had to become one whose container IS the recorded key. The ROW'S SUBJECT
        IS UNCHANGED and is still asserted on non-canonical records — this pass moved the ACT
        rather than the assertion (EP-28N's own precedent for its rmdir row)."""
        pre = self.pre_fix_world()
        pre.act("FILE-MKDIR", path="/a/")
        pre.act("FILE-CREATE", path="/a//b")
        raw = [k for k in pre.recorded("FILE-MKDIR") + pre.recorded("FILE-CREATE")
               if k != custody._norm(k)]
        self.assertGreater(len(raw), 0,
                           "non-vacuity: the replay world holds non-canonical-keyed records")

        records = pre.store.all()
        # THE SHIPPED ENGINE, over those records, twice: the fold's answer and the law's.
        self.assertEqual(set(custody.fold(records).names) - {"/"}, {"/a", "/a//b"},
                         "the fold reproduces exactly what it always derived")
        self.assertEqual(set(opdefs._live_bindings(pre.store, pre.views)) - {"/"},
                         {"/a/", "/a//b"},
                         "and the law still holds the keys AS RECORDED — nothing rewritten")

    def test_and_no_record_was_edited(self):
        pre = self.pre_fix_world()
        pre.act("FILE-MKDIR", path="/a/")
        with open(pre.record, encoding="utf-8") as fh:
            first = fh.read()
        custody.fold(pre.store.all())
        opdefs._live_bindings(pre.store, pre.views)
        with open(pre.record, encoding="utf-8") as fh:
            self.assertEqual(first, fh.read(), "deriving is not writing")


# ---------------------------------------------------------------------------------------
# THE ENVELOPE CARRIES ONE SPELLING TOO
# ---------------------------------------------------------------------------------------
class TestTheEnvelopeAgreesWithThePayload(_Tmp):
    """A record whose payload said `/a` and whose envelope `target` said `/a/` would be the
    same defect surviving inside one record. The envelope field stays UNDEFAULTED — an
    absent parameter still records an absent target — and carries the canonical spelling
    when the parameter is there."""

    def test_link_and_rename_carry_one_spelling(self):
        w = self.world()
        w.act("FILE-CREATE", path="/b")
        w.act("FILE-LINK", target_path="/b/", new_path="/h/")
        link = w.store.by_action("FILE-LINK")[0]
        self.assertEqual(link["target"], "/b")
        self.assertEqual((link["payload"] or {}).get("target_path"), "/b")
        w.act("FILE-RENAME", path="/h/", new_path="/h2/")
        ren = w.store.by_action("FILE-RENAME")[0]
        self.assertEqual(ren["target"], "/h2")
        self.assertEqual((ren["payload"] or {}).get("new_path"), "/h2")

    def test_an_absent_target_parameter_still_records_an_absent_target(self):
        """THE HALF THAT MUST NOT MOVE, and its standing guard is EP-27B's
        `test_target_param_reads_the_raw_caller_parameters`, which defines an op whose
        `param_defaults` would fabricate a target and asserts the envelope records None.
        That row runs in this suite and is not restated here; what IS asserted here is the
        structural property it rests on — the envelope's value is taken only where the RAW
        caller parameters carried one, so a default still cannot reach it."""
        with open(OPDEFS_PATH, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        interp = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "_interpreter")
        run = next(n for n in ast.walk(interp)
                   if isinstance(n, ast.FunctionDef) and n.name == "run")
        guards = [n for n in ast.walk(run)
                  if isinstance(n, ast.Compare) and len(n.ops) == 1
                  and isinstance(n.ops[0], ast.In)
                  and isinstance(n.comparators[0], ast.Name)
                  and n.comparators[0].id == "params"]
        self.assertGreaterEqual(len(guards), 1,
                                "the envelope reads the RAW caller parameters for presence")


# ---------------------------------------------------------------------------------------
# THE LEASH — the assumption this pass runs on, asserted rather than assumed
# ---------------------------------------------------------------------------------------
class TestTheLeashThisPowerArrivesWith(_Tmp):
    """DESIGN-SOUL §2: every new power arrives with its own leash in the same round.

    THE POWER: the engine applies the NAMESPACE's canonical spelling to every parameter a
    definition declares as a key. THE ASSUMPTION UNDER IT: every declared key is a namespace
    path. That is TRUE TODAY and measured — the ops declaring a key check and the ops citing
    the namespace law are the same seven — and it is not true by construction. THE LEASH:
    this row, which REDS the day a key space arrives that is not a path, so the author meets
    the question instead of the engine silently respelling somebody else's key.

    THE RESIDUAL IS RAISED, NOT RESOLVED: the law-data home for a key's canonical form is a
    declaration on the binding row, which is a founding change and therefore a ruled law
    pass — never an engine pass's side effect."""

    def test_every_op_declaring_a_key_check_cites_the_namespace_law(self):
        w = self.world()
        defs = {n: (v.get("definition") or {})
                for n, v in w.views.op_definitions().items()}
        with_keys = {n for n, d in defs.items() if opdefs._declared_keys(d)}
        self.assertEqual(len(with_keys), 7,
                         "the seven namespace ops, measured: %r" % (sorted(with_keys),))
        laws = {defs[n].get("law_cited") for n in with_keys}
        self.assertEqual(laws, {NAMESPACE_LAW},
                         "a key space outside the namespace law has arrived — the canonical "
                         "spelling applied here is the NAMESPACE's, and this row is where "
                         "that question is met")

    def test_and_the_populations_coincide_in_the_other_direction_too(self):
        w = self.world()
        defs = {n: (v.get("definition") or {})
                for n, v in w.views.op_definitions().items()}
        under_law = {n for n, d in defs.items() if d.get("law_cited") == NAMESPACE_LAW}
        with_keys = {n for n, d in defs.items() if opdefs._declared_keys(d)}
        self.assertEqual(under_law, with_keys,
                         "set-diffed both directions, so neither can grow silently")


# ---------------------------------------------------------------------------------------
# §A55 — WHICH DOOR THIS PASS CLOSED, AND WHAT STILL REACHES THE SUBJECT
# ---------------------------------------------------------------------------------------
class TestTheMutabilityDoorIsSTILLOPEN(_Tmp):
    """THE PASS-TWO BLEED, REFUSED BY DRIVING IT (wrong reference 4).

    The door this pass closed is SPELLING: one object could hold two keys. The OTHER door
    on the same root — one key holding two objects — is that identity is a MUTABLE
    user-controlled string, and canonicalisation changes NOTHING about it: rename-recreate
    collides on two spellings that were ALREADY canonical. It is EP-28P's, it is open, and
    this pass's green says nothing about it."""

    def test_rename_then_recreate_still_puts_two_objects_under_one_identity(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and this is the sharpest row in the
        file: IT ASSERTED THAT THE DEFECT STANDS, AND IT REDS BECAUSE THE DEFECT IS GONE.]

        ASSERTED (2026-08-04, EP-28O): rename-recreate puts TWO distinct objects under ONE
        identity, both spellings already canonical — driven here to refuse the pass-two bleed,
        i.e. to stop anyone reading a SPELLING fix as an IDENTITY fix. The row was a fence: it
        said out loud what this pass did NOT close.
        SUPERSEDED (2026-08-08, EP-28S, founding 1.18.0): identity comes from the birth act's
        own record coordinate, and a coordinate is never reissued. The door this row was
        keeping visible IS NOW SHUT — by EP-28P's stop and EP-28S's landing, exactly the pass
        this row named as its owner.
        REMAINS TRUE, separated out and STILL ASSERTED, and it is the reason the row is kept
        rather than deleted: the two acts are still TWO DISTINCT OBJECTS, the spellings are
        still already canonical, and CANONICALISATION STILL HAS NOTHING TO DO WITH IT. That was
        the row's argument and it survives intact — what changed is the outcome it was
        reporting. Deleting the row would erase the record that this file deliberately left the
        door open and named its owner, which is the one thing an obsolete row must not lose.
        THE ROW NAME IS KEPT DELIBERATELY. A name saying the door is open above a body proving
        it is shut would be a false statement in the suite; a name kept with its history stated
        is a record. The rename is left in the drive because the drive is the evidence."""
        w = self.world()
        w.act("FILE-CREATE", path="/a")
        first_birth = w.store.by_action("FILE-CREATE")[0]
        w.act("FILE-RENAME", path="/a", new_path="/b")
        w.act("FILE-CREATE", path="/a")
        second_birth = w.store.by_action("FILE-CREATE")[1]
        self.assertEqual(w.recorded("FILE-CREATE", "inode"), [None, None],
                         "neither birth records an identity a caller could have spelled")
        self.assertEqual(w.recorded("FILE-CREATE"), ["/a", "/a"],
                         "both acts named the SAME path, already canonical, which is what "
                         "made this a collision under path identity")
        for p in w.recorded("FILE-CREATE"):
            self.assertEqual(p, custody._norm(p),
                             "both spellings were ALREADY canonical — spelling never reached "
                             "this door, which was and remains this row's argument")
        first = custody.formal_name(first_birth["seq"])
        second = custody.formal_name(second_birth["seq"])
        self.assertNotEqual(first, second,
                            "EP-28P's door: two distinct objects must be two identities")
        st = custody.fold(w.store.all())
        self.assertNotEqual(st.names["/a"], st.names["/b"],
                            "the renamed object and the re-created one are one node again")


# ---------------------------------------------------------------------------------------
# THE WORLD THAT SPANS THE CHANGE — the consequence the plan does not name
# ---------------------------------------------------------------------------------------
class TestAWorldThatSPANSTheChange(_Tmp):
    """MEASURED RATHER THAN LEFT TO BE MET, and it is what this pass says perishes.

    Derivation-forward is correct and rewriting the record is the forbidden act, so a binding
    made under the OLD law keeps the key it was recorded with — that is the two-times law
    working, not failing. But `_norm` NEVER RETURNS a non-canonical spelling, so once the law
    canonicalises every incoming key, NO SPELLING A CALLER CAN SUPPLY REACHES THAT KEY. The
    binding is stranded in the law's live set: nothing can unbind it. And because the key its
    canonical spelling occupies is FREE, a create under that spelling is admitted and the fold
    rebinds — reproducing, in a world that spans the change, exactly the orphan this pass
    removed from worlds that do not.

    NONE OF THIS IS A DEFECT IN THE FIX, and the alternative is the one forbidden act. It is
    the cost of a derivation change in an append-only estate; it is BOUNDED — only a world
    already holding a non-canonical key is reachable by it, and a world's exposure is
    countable from its own records; and its remedy is a world DISPOSITION, re-found or
    continue under the recorded law, which is the mentor's word on the EP-28I precedent.
    RAISED there, never taken here. These rows exist so the question cannot be lost."""

    def spanning_world(self):
        """One record file written under the pre-fix engine, then REOPENED under the shipped
        one. The records are not edited and not replaced: the same bytes are read by the law
        this pass landed, which is exactly what a live world does at its next boot."""
        tmp = tempfile.mkdtemp(dir=self.dir)
        with canonicalisation_removed():
            old = _World(tmp)
            old.act("FILE-MKDIR", path="/a/")
        with open(old.record, encoding="utf-8") as fh:
            self.before_bytes = fh.read()
        # EP-MAINT-OUTSIDE-5 (re-spec C): close the first world's writer before reopening the same
        # record, so the reopened world is a WRITER able to act across the change (release-on-close).
        # The reopen still appends nothing (boot attestation is idempotent over an unchanged tree),
        # so `before_bytes` and the no-rewrite check hold.
        old.store.close()
        return old, _World(tmp)

    def test_a_pre_fix_key_cannot_be_reached_by_ANY_spelling_a_caller_can_supply(self):
        old, now = self.spanning_world()
        self.assertEqual(now.keys(), {"/a/"},
                         "non-vacuity: the world holds a key that is not canonical")
        self.assertEqual(now.names(), {"/a"}, "and the fold serves it, as it always did")
        for spelling in ("/a", "/a/", "//a//", "a/", "a"):
            self.assertEqual(custody._norm(spelling), "/a",
                             "every spelling of this name canonicalises to one value")
            with self.assertRaises(OpError, msg=spelling):
                now.act("FILE-RMDIR", path=spelling)
        self.assertEqual(now.keys(), {"/a/"}, "the binding is STRANDED — nothing unbinds it")

    def test_and_the_canonical_spelling_is_free_so_a_create_rebinds_the_served_name(self):
        old, now = self.spanning_world()
        now.act("FILE-MKDIR", path="/a")
        self.assertEqual(now.keys(), {"/a", "/a/"},
                         "two keys for one served name, in a world that spans the change")
        state = custody.fold(now.store.all())
        self.assertEqual(set(state.names) - {"/"}, {"/a"}, "still ONE name")
        self.assertEqual(len(state.inodes), 3,
                         "root plus TWO nodes: the stranded one has no name reaching it")

    def test_the_exposure_is_BOUNDED_and_countable_from_a_worlds_own_records(self):
        """The instrument the disposition question needs, so the answer is a measurement
        rather than a judgement: a world's exposure is the number of recorded keys that are
        not their own canonical spelling. A world driven only through spellings the namespace
        already agreed with has exposure ZERO and spans nothing."""
        old, now = self.spanning_world()
        exposed = [k for k in now.recorded("FILE-MKDIR") if k != custody._norm(k)]
        self.assertEqual(exposed, ["/a/"])

        clean = tempfile.mkdtemp(dir=self.dir)
        with canonicalisation_removed():
            w = _World(clean)
            w.act("FILE-MKDIR", path="/a")
        # EP-MAINT-OUTSIDE-5 (re-spec C): close the first writer before reopening, so `reopened`
        # is a WRITER able to act across the change (release-on-close).
        w.store.close()
        reopened = _World(clean)
        self.assertEqual([k for k in reopened.recorded("FILE-MKDIR")
                          if k != custody._norm(k)], [],
                         "a world already spelling names canonically has exposure zero")
        self.assertEqual(reopened.keys(), {"/a"})
        reopened.act("FILE-RMDIR", path="/a")
        self.assertEqual(reopened.keys(), set(), "and it acts across the change untouched")

    def test_and_no_record_was_rewritten_to_make_any_of_this_true(self):
        old, now = self.spanning_world()
        with open(now.record, encoding="utf-8") as fh:
            self.assertEqual(self.before_bytes, fh.read(),
                             "the record is the record — this pass reaches derivation only")


# ---------------------------------------------------------------------------------------
# THE RESIDUAL, COUNTED — what "one canonical spelling per name" does NOT yet cover
# ---------------------------------------------------------------------------------------
#: OPS THAT TAKE A NAMESPACE NAME AND DECLARE NO QUESTION ABOUT IT. Their `path` is not a KEY
#: — no `binding` and no `kind` check reads it — so this pass leaves it in the caller's
#: spelling, and a reader comparing `payload.path` across a create and a later write on one
#: file can still see two spellings of one name. It is NOT a divergence between the law and
#: the fold, which is what this pass is about: the law holds no key for any of these, and the
#: fold resolves each through `_norm` at its own door exactly as it always has. It IS the
#: honest edge of the goal, so it is counted here rather than described, and RAISED.
UNKEYED_NAME_TAKERS = {
    "FILE-CHOWN", "FILE-CLOSE", "FILE-LOCK", "FILE-OPEN", "FILE-PERM",
    "FILE-READ-AGGREGATE", "FILE-TIMES", "FILE-TRUNCATE", "FILE-UNLOCK", "FILE-WRITE",
    "FILE-XATTR-LAW", "FILE-XATTR-REMOVE", "FILE-XATTR-SET",
}


class TestTheResidualIsCountedNotDescribed(_Tmp):
    """§A24: a raise derives to its residual. The residual of "one canonical spelling per
    name" is the set of ops that take a name and ask nothing about it — thirteen, enumerated
    above and re-derived here from the pack's structure, so the raise carries its arithmetic
    and cannot grow silently while nobody re-counts."""

    PATH_PARAMS = ("path", "new_path", "target_path")

    def _defs(self, w):
        return {n: (v.get("definition") or {}) for n, v in w.views.op_definitions().items()}

    def test_the_set_is_exactly_thirteen_and_set_diffs_both_directions(self):
        w = self.world()
        found = {n for n, d in self._defs(w).items()
                 if set((d.get("params") or {})) & set(self.PATH_PARAMS)
                 and not opdefs._declared_keys(d)}
        self.assertEqual(found, UNKEYED_NAME_TAKERS)
        self.assertEqual(len(found), 13)

    def test_none_of_them_cites_the_namespace_law_which_is_why_no_key_diverges(self):
        w = self.world()
        defs = self._defs(w)
        self.assertNotIn(NAMESPACE_LAW, {defs[n].get("law_cited") for n in UNKEYED_NAME_TAKERS},
                         "an op citing the namespace law and declaring no key would be a "
                         "member of THIS pass's subject that this pass missed")

    def test_and_the_fold_still_resolves_them_through_the_one_computer(self):
        """The consequence that matters is bounded: a write spelled with a trailing slash
        still reaches the file it names, because the fold canonicalises at its own door."""
        w = self.world()
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-WRITE", path="/a/", content="x")
        self.assertEqual(w.recorded("FILE-WRITE"), ["/a/"],
                         "the record keeps the caller's spelling for an unkeyed name")
        node = custody.fold(w.store.all()).lookup("/a")
        self.assertEqual(node.content_hash, w.store.by_action("FILE-WRITE")[0]
                         ["payload"]["content_hash"],
                         "and the write still lands on the file the name resolves to")


# ---------------------------------------------------------------------------------------
# §15's CONTROL — the fenced file that took ZERO lines, and why that is a result
# ---------------------------------------------------------------------------------------
class TestThePortNeededNothing(_Tmp):
    """`src/bridge/kernel_port.py` is IN this pass's fence, named as a consumer to be "made to
    READ the canonical value", and it took ZERO lines. That is a result rather than an
    omission, and these rows are the reason.

    The port hands the gate the caller's spelling exactly as it always did, and reads back the
    canonical one, because the canonicalisation happens BETWEEN those two moments. And its own
    `_posix_precondition` was ALREADY normalising before it asked — which is precisely what
    hid this divergence for two passes: the port answered correctly while the law it called
    held a key the port would never have recognised."""

    def port_world(self):
        w = self.world()
        w.port = KernelPort(w.store, w.gate, w.views, w.blobs)
        return w

    def test_a_trailing_slash_mkdir_through_the_port_serves_one_name_and_one_identity(self):
        w = self.port_world()
        code, out, _body = w.port.handle(
            {"id": "1", "op": "FILE-MKDIR", "class": "DECISION",
             "uid": "1000", "gid": "1000", "pid": "42", "path": "/a/"}, b"")
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]
        # ASSERTED (2026-08-04): a trailing-slash mkdir through the port yields ONE canonical
        #   key, ONE served name whose identity is `/a`, and a wire number that renders from
        #   that identity.
        # SUPERSEDED (2026-08-08, EP-28S): the identity is the birth act's coordinate, so
        #   `render_ino("/a")` is no longer the number this node serves — it is the digest of a
        #   path nothing is identified by any more.
        # REMAINS TRUE, separated out and STILL ASSERTED, and it is the row's own name: ONE
        #   NAME AND ONE IDENTITY. The canonical key still reaches the law, the fold still
        #   serves exactly one name for the two spellings, and the number on the wire is still
        #   the rendering of the identity the fold holds — which is now read FROM THE FOLD
        #   rather than recomputed from a path, so the row asserts the agreement between the
        #   wire and the served state instead of asserting a formula twice.
        self.assertEqual(code, 0, out)
        self.assertEqual(w.keys(), {"/a"}, "the law recorded the canonical key")
        node = w.port.state.lookup("/a")
        birth = w.store.by_action("FILE-MKDIR")[0]
        self.assertEqual(node.identity, custody.formal_name(birth["seq"]))
        self.assertEqual(out.get("ino"), custody.render_ino(node.identity),
                         "and the number the module instantiates renders from that identity")
        self.assertEqual(out.get("ino"), node.ino,
                         "the wire and the served state must name one number")

    def test_and_the_port_still_hands_the_gate_the_callers_spelling(self):
        """Why zero lines is correct rather than lucky: `_params_for` is unchanged and still
        forwards the raw wire value. The canonicalisation is the LAW's, at one site, and the
        port is a reader of its result — which is the difference between this pass and the one
        the dispatch named as its trap."""
        w = self.port_world()
        self.assertEqual(w.port._params_for("FILE-MKDIR", {"path": "/a/"}, b""),
                         {"path": "/a/"})

    def test_the_precondition_that_hid_this_for_two_passes_is_RETIRED(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: a byte pin sliced out of `kernel_port.py` between
        `    def _posix_precondition(self, op, f):` and `    def _refuse_unregistered(...)`,
        asserting `path = custody._norm(f.get("path") or "/")` inside it — "the port
        normalised before it asked, and still does — untouched." The first `index()` now
        raises `ValueError: substring not found`.

        THE THING THAT HID THE DIVERGENCE IS GONE, WHICH IS THE STRONGER END OF THIS ROW'S
        OWN STORY. The port answered correctly for two passes because it normalised before
        asking, while the law it called held a key the port would never have recognised.
        EP-28O made the law derive its key through the fold's own `_norm`; W4e removed the
        second asker. There is now ONE normalisation on the decide path and it is the law's.

        THE PIN IS INVERTED RATHER THAN DELETED, and the surviving half is asserted
        positively: the port's remaining `_norm` readers are the readdir/lookup FILL paths
        and none of them sits on the decide path."""
        import ast
        with open(os.path.join(REPO, "src", "bridge", "kernel_port.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("    def _posix_precondition(self, op, f):", src)
        tree = ast.parse(src)
        decide = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "_decide")
        norms = [n for n in ast.walk(decide)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "_norm"]
        self.assertEqual(norms, [],
                         "the decide path normalises a second time, so the port is asking "
                         "its own question about the key again")
        # NON-VACUITY, on this row's own instrument: the walk CAN see a `_norm` call, proven
        # against the fill path that genuinely still makes one.
        fill = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "_fill_readdir")
        self.assertTrue([n for n in ast.walk(fill)
                         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                         and n.func.attr == "_norm"],
                        "the walk found no `_norm` call anywhere, so the empty result above "
                        "is the instrument and not the code")


if __name__ == "__main__":
    unittest.main()
