"""EP-28S — the identity law pass: the birth act's own coordinate names what it founds.

THE DEFECT THIS BATTERY HOLDS SHUT, stated once. Founding 1.14.0 made
`param_defaults {"inode": "$path"}` class-wide, so a node's identity was its PATH. A path
is not stable under rename: create `/a`, rename it to `/b` (the node moves and KEEPS the
identity `/a`), create `/a` again, and two nodes hold one identity. Both acts are lawful,
neither is refused, the fold binds ONE node for TWO files, `nlink` reports two files nobody
linked as hard links of each other, and a chmod addressed to one name changes the other —
while `kill it, replay, identical` HOLDS, because both derivations agree. The RECORD was
wrong and every guard in this estate runs record->view.

WHAT REPLACES IT IS A RETURN. The FUSE port identified nodes by ALLOCATION ORDER — a
private counter — and a counter cannot collide. That regime was sound and was still
running in the other port while this one was replaced. Allocation order comes back with
the record's own append as its source: `SEQ_FLOOR + seq`, injective by construction.

Runs on this box: `python3 -m unittest discover -s tests -p 'test_ep28s.py'`.
"""

import ast
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bridge import custody  # noqa: E402
from bridge.kernel_port import KernelPort  # noqa: E402
from founding import install as install_mod  # noqa: E402
from founding.install import FoundingIntegrityError  # noqa: E402
from kernel import opdefs  # noqa: E402
from kernel.blobs import BlobStore  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
PROV = {"uid": 0, "gid": 0, "pid": 1, "window": "ep28s"}


# =====================================================================================
# W1 — THE IDENTITY-SITE INSTRUMENT, shipped as machinery rather than as a paragraph.
#
# The question "where is an identity value derived" is STRUCTURAL, not textual. Measured
# cost of pretending otherwise: three seats ran four text patterns and reported 29 / 12 / 17.
# An identity arrives in exactly four shapes and only one of them spells `p.get("inode")`.
# =====================================================================================

IDENTITY_KEYS = frozenset({"inode"})
ALLOCATOR_ATTRS = frozenset({"next_ino"})
MINT_CALLS = frozenset({"mint_ino", "_mint_ino"})
RENDER_CALLS = frozenset({"render_ino", "parse_ino", "formal_name"})

MINT, PDEF, FOLD, REND = "MINT", "PARAM_DEFAULT", "FOLD_READ", "RENDERING"


def _callee(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _const_str(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


class _IdentityWalk(ast.NodeVisitor):
    """THE FOUR ARRIVAL SHAPES, each decided from the AST and never from a text pattern."""

    def __init__(self, path):
        self.path = path
        self.hits = []

    def _hit(self, shape, node, why):
        self.hits.append((self.path, node.lineno, shape, why))

    def visit_Attribute(self, node):
        if node.attr in ALLOCATOR_ATTRS:
            self._hit(MINT, node, "allocator attribute %r" % node.attr)
        self.generic_visit(node)

    def visit_Subscript(self, node):
        if _const_str(node.slice) in IDENTITY_KEYS:
            self._hit(FOLD, node, "subscript %r" % _const_str(node.slice))
        self.generic_visit(node)

    def visit_Call(self, node):
        name = _callee(node)
        if name in MINT_CALLS:
            self._hit(MINT, node, "call %s()" % name)
        elif name in RENDER_CALLS:
            self._hit(REND, node, "call %s()" % name)
        elif name == "get" and node.args:
            key = _const_str(node.args[0])
            if key in IDENTITY_KEYS:
                if len(node.args) >= 2:
                    self._hit(PDEF, node, ".get(%r, <default>)" % key)
                else:
                    self._hit(FOLD, node, ".get(%r)" % key)
        self.generic_visit(node)


def walk_source(label, source):
    w = _IdentityWalk(label)
    w.visit(ast.parse(source, filename=label))
    return w.hits


def walk_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        return walk_source(path, fh.read())


def walk_founding(path):
    """The LAW's own identity sites: a `param_defaults` supplying an identity key, and a
    `mints` declaring which field carries the identity an act founds."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    hits = []

    def rec(node, trail):
        if isinstance(node, dict):
            defaults = node.get("param_defaults")
            if isinstance(defaults, dict):
                for key in defaults:
                    if key in IDENTITY_KEYS:
                        hits.append((path, trail + "/param_defaults/" + key, PDEF,
                                     "law supplies %r when absent" % key))
            declared = node.get("mints")
            if isinstance(declared, (list, tuple)):
                for key in declared:
                    if key in IDENTITY_KEYS:
                        hits.append((path, trail + "/mints", MINT,
                                     "law declares the act founds a thing named by %r" % key))
            for key, value in node.items():
                rec(value, trail + "/" + str(key))
        elif isinstance(node, list):
            for i, value in enumerate(node):
                rec(value, trail + "/%d" % i)

    rec(doc, "")
    return hits


def sweep_src(root=SRC):
    hits = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "archive")]
        for name in sorted(files):
            if name.endswith(".py"):
                hits.extend(walk_file(os.path.join(base, name)))
            elif name == "founding-pack.json":
                hits.extend(walk_founding(os.path.join(base, name)))
    return hits


def defined_names(root=SRC):
    """Every function and class NAME `src/` actually defines. The citation-class rule's
    decision procedure: an identifier cited as an existing precedent must be in here."""
    names = set()
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "archive")]
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(base, name), "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=name)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(node.name)
    return names


def read_source(*parts):
    """READ A SOURCE FILE WITHOUT LEAKING ITS HANDLE. Named rather than inlined because the
    inline form leaked four handles in this file's own first run, into the exact
    ResourceWarning class this suite has lost `Ran N` lines to for six seats — a row that
    damages the instrument it is measured in."""
    with open(os.path.join(SRC, *parts), "r", encoding="utf-8") as fh:
        return fh.read()


class TestTheInstrumentCanFail(unittest.TestCase):
    """§A64 — a planted site of EACH arrival shape is FOUND, a near-miss of EACH is NOT.
    An instrument with no can-fail proof can never build the track record the fence's
    promotion clause is earned on, which is why this class is not decoration."""

    PLANTED = {
        MINT: "def f(s):\n    return s.next_ino\n",
        PDEF: "def f(p):\n    return p.get('inode', p['path'])\n",
        FOLD: "def f(p):\n    return p.get('inode')\n",
        REND: "def f(i):\n    return render_ino(i)\n",
    }
    #: Each is ONE token away from its planted twin, and the difference is the whole test:
    #: a walker that matched text rather than shape would take every one of these.
    NEAR_MISS = {
        MINT: "def f(s):\n    return s.next_ino_hint\n",
        PDEF: "def f(p):\n    return p.get('node_type', 'file')\n",
        FOLD: "def f(p):\n    return p.get('inodes')\n",
        REND: "def f(i):\n    return render_int(i)\n",
    }

    def test_each_planted_arrival_shape_is_found(self):
        for shape, source in self.PLANTED.items():
            hits = [h for h in walk_source("<planted>", source) if h[2] == shape]
            self.assertTrue(hits, "the instrument missed a planted %s site" % shape)

    def test_each_near_miss_is_not_found(self):
        """NON-VACUITY IN THE ROW ITSELF (item 21): an instrument that found NOTHING would
        pass every line below, so each near-miss is checked beside the planted twin it is
        one token away from — the empty answer only means something next to a full one."""
        for shape, source in self.NEAR_MISS.items():
            self.assertTrue([h for h in walk_source("<planted>", self.PLANTED[shape])
                             if h[2] == shape], "the walk finds nothing at all")
            hits = [h for h in walk_source("<near-miss>", source) if h[2] == shape]
            self.assertEqual(hits, [], "the instrument took a near-miss as a %s site" % shape)

    def test_the_walk_is_structural_and_not_textual(self):
        """THE LEAST-LIKELY MEMBER (§A49): the identity key inside a STRING is not a site,
        and a walker built on text patterns cannot tell the difference."""
        self.assertTrue(walk_source("<live>", "def f(p):\n    return p.get('inode')\n"))
        source = "def f():\n    return \"p.get('inode')\"\n"
        self.assertEqual(walk_source("<string>", source), [])

    def test_the_census_is_computed_and_names_its_files(self):
        """M2's answer at this level: the census is COMPUTED at every run, never stored.
        The assertion is on the FILE SET, because a new file growing an identity site is
        exactly the rot that put `custody.py` outside EP-28P's fence.

        TWO FILES LEFT THIS SET AT EP-28S AND THAT IS THE PASS'S MEASURED SHAPE rather than
        tidying: `records_fs.py` held six sites and holds none — the port stopped minting —
        and `founding-pack.json` held six and holds none, because the law stopped naming a
        field. 34 sites in 6 files before the landing, 23 in 4 after.

        THE TWO THAT REMAIN AND ARE NOT IN THE SEED ARE REPORTED, NOT ABSORBED.
        `subsystems/files.py` derives a namespace identity with a FALLBACK TO THE PATH and
        MEETS the rule; `observe/windows.py` reads a SOCKET inode out of `sock_diag` and
        meets the rule's KEY while sitting outside its domain. Both wait on a one-line fence
        ruling, and pinning them here is what makes a later ruling checkable."""
        files = sorted({os.path.relpath(h[0], SRC) for h in sweep_src()})
        self.assertEqual(files, [
            "bridge/custody.py",
            "bridge/kernel_port.py",
            "observe/windows.py",
            "subsystems/files.py",
        ])


class TestTheCitationClassRule(unittest.TestCase):
    """§1 — an identifier cited as an EXISTING PRECEDENT must RESOLVE in `src/`.

    `render_bind` was cited in shipped source at `custody.py` and twice in EP-28P as a
    precedent an acceptance criterion rested on. It has never existed. The mechanism was
    always real and always in `CustodyState.apply`; only the name was fiction."""

    def test_render_bind_resolves_to_nothing_and_the_walker_can_still_find_what_exists(self):
        names = defined_names()
        self.assertNotIn("render_bind", names)
        # CAN-FAIL: a resolver that found nothing would pass the line above vacuously.
        for real in ("render_ino", "parse_ino", "formal_name", "mint_ino",
                     "UnrenderableIdentity", "CustodyState"):
            self.assertIn(real, names)

    def test_the_withdrawn_name_never_appears_without_its_withdrawal(self):
        """THE ROW IS NOT "the name is gone", AND THE DIFFERENCE IS THE ESTATE'S OWN RULE.
        Deleting `render_bind` outright would leave the next reader unable to see what was
        wrong — the `AppendNothing` treatment says KEEP the superseded claim and ADD what
        superseded it. So the checkable property is CO-OCCURRENCE: wherever the fabricated
        name appears, the passage also names the mechanism that really fires and says the
        name never existed. That is decidable, and a silent re-introduction fails it."""
        source = read_source("bridge", "custody.py")
        occurrences = [i for i in range(len(source)) if source.startswith("render_bind", i)]
        self.assertTrue(occurrences, "the repair's own record has been deleted")
        for at in occurrences:
            window = source[max(0, at - 1200):at + 1200]
            self.assertIn("UnrenderableIdentity", window)
            self.assertIn("NEVER EXISTED", window.upper())

    def test_the_repaired_citation_names_the_refusal_that_actually_fires(self):
        """`UnrenderableIdentity` is not merely defined — it is what `apply` raises when two
        identities render alike. Resolving the NAME and never the BEHAVIOUR would let the
        citation rot the same way twice."""
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 2, "record_time": 0.0,
                     "payload": {"path": "/x", "inode": 9000}})
        with self.assertRaises(custody.UnrenderableIdentity):
            # a DIFFERENT identity rendering to the SAME number: an integer renders as
            # itself, so this is the collision condition stated in the fewest moving parts.
            state.apply({"action": "FILE-MKDIR", "seq": 3, "record_time": 0.0,
                         "payload": {"path": "/y", "inode": 9000.0}})


# =====================================================================================
# THE THREE NUMBER SPACES — inherited from EP-28P's stop as DRIVEN evidence and re-driven
# HERE, in place, against the shipped constants rather than a local rendering.
# =====================================================================================

class TestTheThreeSpacesAreDisjointByConstruction(unittest.TestCase):

    def test_the_bands_do_not_overlap(self):
        legacy = (1, custody.SEQ_FLOOR)
        formal = (custody.SEQ_FLOOR, custody.RENDER_FLOOR)
        digest = (custody.RENDER_FLOOR, 1 << 63)
        for lo, hi in (legacy, formal, digest):
            self.assertLess(lo, hi)
        self.assertEqual(legacy[1], formal[0])
        self.assertEqual(formal[1], digest[0])

    def test_near_misses_at_both_boundaries_in_both_directions(self):
        """§A64 in its literal form. The value one below a floor and the value at it are the
        only two that could ever be got wrong, and they are driven rather than asserted."""
        self.assertLess(custody.SEQ_FLOOR - 1, custody.SEQ_FLOOR)          # last legacy
        self.assertEqual(custody.formal_name(1), custody.SEQ_FLOOR + 1)    # first formal
        self.assertLess(custody.RENDER_FLOOR - 1, custody.RENDER_FLOOR)    # last formal
        rendered = custody.render_ino("/some/path")
        self.assertGreaterEqual(rendered, custody.RENDER_FLOOR)            # first digest
        self.assertLess(rendered, 1 << 63)

    def test_a_formal_name_is_its_own_rendering(self):
        """The property that makes resolution injective: there is no lookback to be
        ambiguous about, because identity and rendering are ONE VALUE."""
        name = custody.formal_name(137)
        self.assertEqual(custody.render_ino(name), name)

    def test_the_coordinate_is_read_and_never_defaulted(self):
        for absent in (None, "", "not-a-number", {}):
            with self.assertRaises(custody.UnparseableRecordValue):
                custody.formal_name(absent)

    def test_a_coordinate_below_one_refuses(self):
        for bad in (0, -1):
            with self.assertRaises(custody.UnrenderableIdentity):
                custody.formal_name(bad)

    def test_the_bands_ceiling_refuses_and_the_value_below_it_is_admitted(self):
        """NEAR-MISS BOTH WAYS at the band's own ceiling — the boundary a wrap would cross
        silently, answering with a number that means something else."""
        self.assertEqual(custody.formal_name(custody.SEQ_FLOOR - 1),
                         custody.SEQ_FLOOR + custody.SEQ_FLOOR - 1)
        with self.assertRaises(custody.UnrenderableIdentity):
            custody.formal_name(custody.SEQ_FLOOR)

    def test_the_map_from_coordinate_to_formal_name_is_injective(self):
        """No digest, no birthday bound. 200,000 consecutive coordinates, zero collisions —
        and the check is on the SET SIZE, so a collision could not hide in it."""
        names = {custody.formal_name(i) for i in range(1, 200001)}
        self.assertEqual(len(names), 200000)


# =====================================================================================
# THE ACCEPTANCE (raise 3, mentor-ruled into this pass AS A TEST, not as an item):
#   EP-28S PASSES WHEN A CHMOD THROUGH ONE NAME NO LONGER REACHES ANOTHER FILE.
# =====================================================================================

class _Worlds:
    """Two worlds from one script, so the green is DIFFED against the red rather than
    asserted alone. The RED world is built by hand at the RECORD level, which is what a
    world founded before 1.18.0 actually holds — the old pack is not re-installed, because
    a test that needed the old founding on disk would rot the moment the file moved."""

    @staticmethod
    def old_law_records():
        """A pre-1.18.0 world, verbatim in the shape `param_defaults {"inode": "$path"}`
        produced: every birth record NAMES its identity, and it names the PATH."""
        return [
            {"action": "FILE-CREATE", "seq": 1, "record_time": 1.0,
             "payload": {"path": "/a", "inode": "/a", "perm": "644"}},
            {"action": "FILE-RENAME", "seq": 2, "record_time": 2.0,
             "payload": {"path": "/a", "new_path": "/b"}},
            {"action": "FILE-CREATE", "seq": 3, "record_time": 3.0,
             "payload": {"path": "/a", "inode": "/a", "perm": "644"}},
            {"action": "FILE-PERM", "seq": 4, "record_time": 4.0,
             "payload": {"path": "/b", "inode": "/a", "perm": "600"}},
        ]

    @staticmethod
    def new_law_records():
        """The same four acts under 1.18.0: no birth record names an identity at all."""
        return [
            {"action": "FILE-CREATE", "seq": 1, "record_time": 1.0,
             "payload": {"path": "/a", "perm": "644"}},
            {"action": "FILE-RENAME", "seq": 2, "record_time": 2.0,
             "payload": {"path": "/a", "new_path": "/b"}},
            {"action": "FILE-CREATE", "seq": 3, "record_time": 3.0,
             "payload": {"path": "/a", "perm": "644"}},
            {"action": "FILE-PERM", "seq": 4, "record_time": 4.0,
             "payload": {"path": "/b", "inode": custody.SEQ_FLOOR + 1, "perm": "600"}},
        ]


class TestAChmodThroughOneNameNoLongerReachesAnother(unittest.TestCase):
    """THE PASS'S ACCEPTANCE. The reproduction existed before the plan did — it was driven
    at EP-28P's stop — so this class is the cure meeting a symptom that was already on the
    record, not a test written to fit a fix."""

    def _fold(self, records):
        state = custody.CustodyState()
        for e in records:
            state.apply(e)
        return state

    def test_RED_WORLD_the_old_law_still_reaches_the_other_file(self):
        """THE BASELINE THE GREEN IS DIFFED AGAINST, kept rather than deleted. A world
        recorded under the old law is PROSPECTIVELY untouched by this pass, so this row is
        also the coexistence proof: the defect survives exactly where the record put it."""
        state = self._fold(_Worlds.old_law_records())
        self.assertEqual(state.names["/a"], state.names["/b"], "one node, two names")
        self.assertEqual(state.nlink(state.names["/a"]), 2)
        self.assertEqual(state.lookup("/a").perm, 0o600, "the chmod reached the other file")
        self.assertEqual(state.lookup("/b").perm, 0o600)

    def test_GREEN_the_new_law_gives_two_births_two_identities(self):
        state = self._fold(_Worlds.new_law_records())
        self.assertNotEqual(state.names["/a"], state.names["/b"])
        self.assertEqual(state.names["/b"], custody.SEQ_FLOOR + 1)
        self.assertEqual(state.names["/a"], custody.SEQ_FLOOR + 3)

    def test_GREEN_each_file_has_one_name(self):
        state = self._fold(_Worlds.new_law_records())
        self.assertEqual(state.nlink(state.names["/a"]), 1)
        self.assertEqual(state.nlink(state.names["/b"]), 1)

    def test_GREEN_THE_ACCEPTANCE_the_chmod_does_not_reach_the_other_file(self):
        state = self._fold(_Worlds.new_law_records())
        self.assertEqual(state.lookup("/b").perm, 0o600, "the act reached its own subject")
        self.assertEqual(state.lookup("/a").perm, 0o644, "and it reached nothing else")

    def test_the_guard_that_was_blind_to_this_still_holds_in_both_worlds(self):
        """`kill it, replay, identical` HELD while the record was wrong — that is why this
        pass exists — and it must still hold now that it is right. A repair that broke
        replay would have traded one silent wrongness for a loud one."""
        for records in (_Worlds.old_law_records(), _Worlds.new_law_records()):
            self.assertEqual(self._fold(records).snapshot(), self._fold(records).snapshot())


class TestTheReproductionThroughTheLiveGate(unittest.TestCase):
    """The same acceptance, driven through the REAL gate and the REAL founding rather than
    through hand-built records — because a hand-built world proves the fold and says
    nothing about whether the law on disk produces the records the fold expects."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28s-gate-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "record.jsonl"))

    def _state(self):
        state = custody.CustodyState()
        for e in self.store.all():
            state.apply(e)
        return state

    def test_rename_recreate_through_the_live_gate(self):
        c1 = self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/a"})
        self.gate.execute("FILE-RENAME", "SYSTEM",
                          {"path": "/a", "new_path": "/b", "provenance": PROV})
        c2 = self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/a"})
        self.gate.execute("FILE-PERM", "SYSTEM",
                          {"path": "/b", "perm": "600", "provenance": PROV})
        state = self._state()
        self.assertEqual(state.names["/b"], custody.formal_name(c1["seq"]))
        self.assertEqual(state.names["/a"], custody.formal_name(c2["seq"]))
        self.assertEqual(state.lookup("/a").perm, 0o644)
        self.assertEqual(state.lookup("/b").perm, 0o600)

    def test_no_birth_record_names_an_identity_any_more(self):
        self.gate.execute("FILE-MKDIR", "SYSTEM", {"path": "/d", "provenance": PROV})
        self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/d/f"})
        self.gate.execute("FILE-SYMLINK", "SYSTEM",
                          {"path": "/d/l", "target": "/d/f", "provenance": PROV})
        for e in self.store.all():
            if e["action"] in custody.MINTING_ACTIONS:
                self.assertNotIn("inode", e["payload"] or {})

    def test_a_callers_own_identity_never_reaches_the_record(self):
        """THE ALIAS RULE MADE MECHANICAL, and the row states what the machine ACTUALLY does
        rather than what would be tidier.

        I EXPECTED A REFUSAL AND DROVE ONE INSTEAD OF ASSUMING IT, AND THERE IS NONE.
        `kernel_port.py` states in shipped source that "the envelope router refuses a call
        that supplies one it did not declare (EP-27B)". Measured against these three ops:
        it does not. The call is ADMITTED and the value is dropped, because `payload_from`
        no longer lists the field. RAISED, not patched — adding a refusal for an undeclared
        parameter is a law change of its own and reaches every caller in the estate.

        WHAT IS TRUE IS THE PROPERTY THIS PASS NEEDS, and it is the stronger half: the
        caller's value never becomes a recorded identity, so the fold's discriminator cannot
        be defeated from outside. The calling name is an alias whichever door it arrives
        through."""
        for op, extra in (("FILE-CREATE", {}),
                          ("FILE-MKDIR", {"provenance": PROV}),
                          ("FILE-SYMLINK", {"target": "/a", "provenance": PROV})):
            path = "/z-" + op
            rec = self.gate.execute(op, "SYSTEM",
                                    dict({"path": path, "inode": 99}, **extra))
            self.assertNotIn("inode", rec["payload"] or {})
            self.assertEqual(self._state().names[path], custody.formal_name(rec["seq"]))


# =====================================================================================
# THE LAW'S LEASH — declaration and the code that reads it in ONE round (`opdefs.py:588`).
# =====================================================================================

class TestTheDeclarationArrivesWithItsLeash(unittest.TestCase):

    def _pack_records(self):
        return install_mod.records(install_mod.load_pack())

    def _validate(self, records):
        install_mod._validate(records)

    def test_an_unknown_mint_source_is_refused_at_definition_time(self):
        records = copy.deepcopy(self._pack_records())
        planted = 0
        for r in records:
            d = ((r.get("payload") or {}).get("definition") or {})
            if d.get("mints_from"):
                d["mints_from"] = "whatever-the-caller-said"
                planted += 1
                break
        self.assertEqual(planted, 1, "nothing was planted, so nothing was tested")
        with self.assertRaises(FoundingIntegrityError):
            self._validate(records)

    def test_declaring_both_sources_is_refused(self):
        records = copy.deepcopy(self._pack_records())
        planted = 0
        for r in records:
            d = ((r.get("payload") or {}).get("definition") or {})
            if d.get("mints_from"):
                d["mints"] = ["path"]
                planted += 1
                break
        self.assertEqual(planted, 1)
        with self.assertRaises(FoundingIntegrityError):
            self._validate(records)

    def test_the_shipped_founding_is_admitted(self):
        """The near-miss both ways: a guard that refuses everything proves nothing."""
        self._validate(self._pack_records())

    def test_exactly_the_three_minting_ops_declare_the_coordinate(self):
        declaring = set()
        still_minting_a_field = set()
        for r in self._pack_records():
            pl = r.get("payload") or {}
            d = pl.get("definition") or {}
            if d.get("mints_from") == opdefs.RECORD_COORDINATE:
                declaring.add(pl.get("name"))
            if "inode" in (d.get("mints") or []):
                still_minting_a_field.add(pl.get("name"))
        self.assertEqual(declaring, {"FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK"})
        self.assertEqual(still_minting_a_field, set())
        # NON-VACUITY (item 21): `mints` is still read and still finds members — twelve other
        # ops declare one — so the empty set above is a fact about `inode` and not about a
        # reader that stopped looking.
        self.assertGreaterEqual(
            len([r for r in self._pack_records()
                 if ((r.get("payload") or {}).get("definition") or {}).get("mints")]), 10)

    def test_the_minting_ops_take_no_identity_parameter_at_all(self):
        """The property the fold's discriminator RESTS ON: under this law no birth record
        can name an identity, because no caller can supply one and the law supplies none."""
        checked = 0
        for r in self._pack_records():
            pl = r.get("payload") or {}
            d = pl.get("definition") or {}
            if d.get("mints_from") != opdefs.RECORD_COORDINATE:
                continue
            checked += 1
            self.assertNotIn("inode", d.get("params") or {})
            self.assertNotIn("inode", d.get("param_defaults") or {})
            self.assertNotIn("inode", d.get("payload_from") or [])
        self.assertEqual(checked, 3, "item 21 — the subject was proven non-empty first")

    def test_the_version_question_was_MINOR_and_the_evidence_is_this_row(self):
        """W3's ruled test, held as machinery so it cannot rot into a sentence: a founding
        that declares NO source at all — the shape every pack up to 1.17.0 has — still
        loads. `mints_from` is ADDITIVE, which is what made the branch MINOR."""
        records = copy.deepcopy(self._pack_records())
        reverted = 0
        for r in records:
            d = ((r.get("payload") or {}).get("definition") or {})
            if d.pop("mints_from", None):
                d["mints"] = ["inode"]
                d.setdefault("params", {})["inode"] = "optional"
                d.setdefault("param_defaults", {})["inode"] = "$path"
                # Reverting to the pre-1.18.0 shape adds `inode` back as a payload param, so it
                # must carry a classification or the vocabulary door refuses this founding at
                # install. `inode` is STRUCTURAL — a node identity/coordinate scalar, safe
                # inline (census: FILE-PERM and FILE-CLOSE both classify `inode` structural).
                # ADMIT-intent: `_validate` below must load. [design/46 member-2, archi :2956
                # RULING 1 — which names `inode` structural for exactly this founding.]
                d.setdefault("structural_params", []).append("inode")
                reverted += 1
        self.assertEqual(reverted, 3)
        self._validate(records)          # the 1.17.0 shape, admitted under the new law


# =====================================================================================
# PROSPECTIVITY, COEXISTENCE, AND THE RESOLUTION HOLE (§2b / raise 6).
# =====================================================================================

class TestOldAndNewWorldsCoexist(unittest.TestCase):

    def test_a_record_that_names_an_identity_keeps_it(self):
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 7, "record_time": 0.0,
                     "payload": {"path": "/legacy-int", "inode": 42}})
        state.apply({"action": "FILE-CREATE", "seq": 8, "record_time": 0.0,
                     "payload": {"path": "/legacy-path", "inode": "/legacy-path"}})
        self.assertEqual(state.names["/legacy-int"], 42)
        self.assertEqual(state.inodes[42].identity, 42)
        self.assertEqual(state.inodes[state.names["/legacy-path"]].identity, "/legacy-path")

    def test_a_record_that_names_none_is_named_by_its_coordinate(self):
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 9, "record_time": 0.0,
                     "payload": {"path": "/new"}})
        self.assertEqual(state.names["/new"], custody.formal_name(9))

    def test_a_mixed_world_keeps_its_three_spaces_apart(self):
        """The least-likely member (§A49): the world nobody builds on purpose — one written
        by the stamping port, then under path identity, then under the coordinate."""
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 1, "record_time": 0.0,
                     "payload": {"path": "/stamped", "inode": 5}})
        state.apply({"action": "FILE-CREATE", "seq": 2, "record_time": 0.0,
                     "payload": {"path": "/derived", "inode": "/derived"}})
        state.apply({"action": "FILE-CREATE", "seq": 3, "record_time": 0.0,
                     "payload": {"path": "/coordinate"}})
        stamped, derived, coord = (state.names["/stamped"], state.names["/derived"],
                                   state.names["/coordinate"])
        self.assertLess(stamped, custody.SEQ_FLOOR)
        self.assertTrue(custody.SEQ_FLOOR <= coord < custody.RENDER_FLOOR)
        self.assertGreaterEqual(derived, custody.RENDER_FLOOR)
        self.assertEqual(len({stamped, derived, coord}), 3)

    def test_the_allocator_mark_is_poisoned_by_a_formal_name(self):
        """THE GUARD THAT WOULD HAVE REBUILT THE COLLISION ONE LAYER DOWN. Before this pass
        the discriminator was `RENDER_FLOOR`, and a formal name sits BELOW it — so the mark
        would have advanced to `2**61 + seq + 1` and then handed out "fresh" numbers inside
        the formal-name band."""
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 4, "record_time": 0.0,
                     "payload": {"path": "/coordinate"}})
        self.assertIsNone(state.next_ino)
        with self.assertRaises(custody.AllocatorNotTracking):
            custody.mint_ino(state)

    def test_a_stamped_world_still_advances_the_mark(self):
        """The near-miss the row above needs: a mark that poisoned on EVERYTHING would pass
        that assertion while destroying the legacy allocator."""
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 1, "record_time": 0.0,
                     "payload": {"path": "/s", "inode": 5}})
        self.assertEqual(state.next_ino, 6)
        self.assertEqual(custody.mint_ino(state), 6)


class TestResolutionIsInjectiveAfterThisPass(unittest.TestCase):
    """§2b — later acts carry an identity only if a caller hands one in, and the ports hand
    in the RENDERING, so resolution ran render->identity: a lookup NOT INJECTIVE by
    construction. The shipped cap stated it; this pass ends the condition that needed it."""

    def test_RED_WORLD_the_non_injective_lookback_exhibited_before_the_repair_is_believed(self):
        """Two DISTINCT identities rendering to ONE number. Under path identity this is a
        62-bit digest collision and the fold can only REFUSE; the refusal is the honest
        answer and it is also the admission that the lookup was never injective."""
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 1, "record_time": 0.0,
                     "payload": {"path": "/one", "inode": 4242}})
        with self.assertRaises(custody.UnrenderableIdentity):
            state.apply({"action": "FILE-CREATE", "seq": 2, "record_time": 0.0,
                         "payload": {"path": "/two", "inode": 4242.0}})

    def test_GREEN_a_later_act_carrying_the_formal_name_resolves_to_its_own_subject(self):
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 11, "record_time": 0.0,
                     "payload": {"path": "/f"}})
        state.apply({"action": "FILE-PERM", "seq": 12, "record_time": 0.0,
                     "payload": {"path": "/moved-since", "inode": custody.formal_name(11),
                                 "perm": "600"}})
        self.assertEqual(state.lookup("/f").perm, 0o600)

    def test_GREEN_identity_and_rendering_are_one_value_so_there_is_no_lookback(self):
        for seq in (1, 2, 137, 10 ** 6):
            name = custody.formal_name(seq)
            self.assertEqual(custody.render_ino(name), name)

    def test_an_unknown_number_is_ESTALE_and_never_a_fallback_to_the_path(self):
        """THE LEAST-LIKELY MEMBER: the caller holding a handle into a world that moved.
        Answering by path here would quietly undo what renames and hard links rest on."""
        state = custody.CustodyState()
        state.apply({"action": "FILE-CREATE", "seq": 3, "record_time": 0.0,
                     "payload": {"path": "/f"}})
        # NON-VACUITY (item 21): a KNOWN number resolves in this same row, so the None below
        # is the resolver answering rather than the resolver being broken.
        self.assertIsNotNone(state._node({"inode": custody.formal_name(3)}))
        self.assertIsNone(state._node({"inode": custody.formal_name(9999)}))


# =====================================================================================
# THE PORTS — one regime, not two files edited (raise 7's acceptance).
# =====================================================================================

class TestTheTwoPortsNowRunOneRegime(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28s-ports-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(
            os.path.join(self.dir, "record.jsonl"), blobs=self.blobs)

    #: THE FUSE PORT IS CHECKED STRUCTURALLY AND THE REASON IS STATED RATHER THAN WORKED
    #: AROUND: `fusepy` is NOT INSTALLED ON THIS BOX, so `bridge.records_fs` cannot be
    #: imported here at all and a runtime row over it would be a guard that can never fire.
    #: Reading the SOURCE is not a weaker substitute for this particular claim — the claim IS
    #: about the source: that the file holds no identity-derivation site of any arrival shape.
    #: A runtime row could only sample the paths it happened to call.
    def test_the_fuse_port_holds_no_identity_derivation_site_at_all(self):
        source = read_source("bridge", "records_fs.py")
        # NON-VACUITY (item 21): the same walk over a file that DOES hold sites, in this
        # row, so the empty answer below is an answer about `records_fs.py` and not about
        # a walker that has stopped working.
        self.assertTrue(walk_source("custody", read_source("bridge", "custody.py")))
        self.assertEqual(walk_source("records_fs", source), [],
                         "the FUSE port still derives an identity somewhere")
        # The retired name survives ONLY inside the comment that records its retirement —
        # the `AppendNothing` treatment again. What must be gone is the CODE, and the walk
        # above is what says so: a `_mint_ino` call or a `next_ino` read would be a site.
        self.assertNotIn("def _mint_ino", source)

    def test_the_fuse_ports_births_hand_the_record_no_identity(self):
        """The structural half of the same claim, at the CALL rather than the file: no
        `_act` for a minting op passes an `inode`. A near-miss is built into the row — the
        LATER acts still pass one, and if this walk were matching `inode=` anywhere it would
        find those and fail."""
        source = read_source("bridge", "records_fs.py")
        births, laters = [], []
        for node in ast.walk(ast.parse(source)):
            if not (isinstance(node, ast.Call) and _callee(node) == "_act" and node.args):
                continue
            op = _const_str(node.args[0])
            passes_inode = any(kw.arg == "inode" for kw in node.keywords)
            (births if op in custody.MINTING_ACTIONS else laters).append((op, passes_inode))
        self.assertEqual(len(births), 4, "the four birth call sites are the subject")
        self.assertEqual([b for b in births if b[1]], [], "a birth still names an identity")
        self.assertTrue([l for l in laters if l[1]],
                        "no later act passes an inode either — this walk is finding nothing")

    def test_both_ports_derive_identity_from_the_same_one_function(self):
        """RAISE 7's ACCEPTANCE IS ONE REGIME, NOT TWO FILES EDITED. Neither port computes
        an identity: the fold does, through `formal_name`, and both read what it produced."""
        port = KernelPort(self.store, self.gate, self.views, self.blobs)
        rc, out, _ = port.handle({"class": "DECISION", "op": "FILE-CREATE", "path": "/k",
                                  "uid": 0, "gid": 0, "pid": 1}, b"")
        self.assertEqual(rc, 0)
        birth = [e for e in self.store.all() if e["action"] == "FILE-CREATE"][-1]
        self.assertEqual(out["ino"], custody.formal_name(birth["seq"]))
        self.assertNotIn("inode", birth["payload"] or {})

    def test_the_minting_action_set_has_exactly_one_home(self):
        """M4's answer: one computation, one place. A second copy of this tuple in the port
        would drift the first time a fourth minting op arrived.

        DECIDED STRUCTURALLY, because the crude version of this row FIRED ON A NEIGHBOUR:
        `kernel_port.py` legitimately holds other tuples that begin `"FILE-CREATE", "FILE-`
        for unrelated classifications, and a substring test cannot tell a copy of THIS set
        from a different set that happens to start the same way. The property is: no literal
        sequence in the file has the same MEMBERS as `MINTING_ACTIONS`."""
        port_source = read_source("bridge", "kernel_port.py")
        self.assertIn("custody.MINTING_ACTIONS", port_source)
        wanted = set(custody.MINTING_ACTIONS)
        examined = 0
        for node in ast.walk(ast.parse(port_source)):
            if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                examined += 1
                members = {_const_str(el) for el in node.elts}
                self.assertNotEqual(members, wanted,
                                    "a second copy of the minting-action set at line %d"
                                    % node.lineno)
        # NON-VACUITY (item 21): the file holds many literal sequences, so "none of them
        # equals the set" is an answer about the file rather than about an empty walk.
        self.assertGreater(examined, 10)


if __name__ == "__main__":
    unittest.main()
