# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28P — what IDENTITY IS: the establishment, and the pass's STOP, landed as machinery.

Every probe here is a regression test (the campaign method: a verification probe lands as
a test).

WHAT THIS PASS DID AND DID NOT DO, stated first because the file's whole shape follows
from it. EP-28P is a LAW PASS: the founding was REQUIRED to move, and it did not, because
the pass STOPPED AT ITS OWN FENCE (§A27, and W1's own instruction to stop rather than
improvise). The law it was authored to land cannot be landed by the four files D4
enumerates. So what lands here is the ESTABLISHMENT — the exhibition, the version test,
the band derivation, and the fence stop's own evidence — as rows rather than as prose in
a log, because a finding that lives only in an entry is a finding the next seat re-derives.

THE FENCE STOP, IN ONE SENTENCE. The founding and `opdefs` can DECLARE that a formal name
is the birth act's coordinate; `kernel_port` can RENDER it; but the fold that actually
DERIVES a node's identity is `src/bridge/custody.py:350`, which D4 does not name — so a
landing inside the fence moves the founding, validates a declaration nobody reads, and
leaves the collision exactly where it was. `TestAFenceOnlyLandingRepairsNOTHING` drives
that rather than asserting it, because it is the whole reason the pass stopped.

THE NAMED WRONG REFERENCE THIS PASS REFUSES, carried from the EP's own text: THE BURIAL
SHAPE — declaring the mutability defect handled by a change that never touched it. A green
suite plus a moved founding is exactly what a fence-only landing would produce, and it is
what the row above exists to make impossible to mistake for a repair.

Coverage:
  W2   THE CONFIRMATION      rename-recreate under today's law, driven, with the
                             consequences the record does not show: two lawful creates,
                             ONE node, `nlink` 2, and a chmod through one name reaching
                             the other. It REPRODUCED — the object layer is not re-priced.
  W3   THE VERSION TEST      executed, not reasoned: the SHIPPED founding, byte-unchanged,
                             LOADS under the new law past a guard proven able to refuse and
                             proven to admit the lawful value. The branch is MINOR.
  W2b  THE THREE SPACES      the separation derived against a local rendering, with §A64
                             near-misses on BOTH boundaries and the refusals driven. The
                             EP's PROPOSED shape is REFUTED and replaced: see the class.
  W1   WHERE IDENTITY LIVES  the derivation sites located structurally and cited by
                             file:line, so the citation cannot rot into prose.
  --   THE CITATIONS         `render_bind` — cited in shipped source and twice in the EP as
                             a "precedent" — RESOLVES TO NOTHING. Held mechanically.
"""
import ast
import contextlib
import json
import os
import re
import shutil
# [EP-28Z, 2026-08-12] `import subprocess` REMOVED: this file's only spawn was its copy
# of the era-pin act, which now lives at `tests/era_pin.py`. An import naming a capability
# the file no longer uses tells a later reader it spawns processes, which is false.
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "src"))

import era_pin                                                      # noqa: E402  (the era-pin home, EP-28Z)
from bridge import custody                                          # noqa: E402
from kernel import opdefs                                           # noqa: E402
from kernel.compose import build_full_kernel                        # noqa: E402
from founding import install as founding_install                    # noqa: E402

OWNER = "owner"
PROV = {"uid": 1000, "gid": 1000, "pid": 42, "window": "test"}

CUSTODY_PATH = os.path.join(REPO, "src", "bridge", "custody.py")
STORE_PATH = os.path.join(REPO, "src", "kernel", "store.py")
FOUNDING_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
EP_PATH = os.path.join(REPO, "planning", "exec", "EP-28P.md")


def _custody_apply():
    """`CustodyState.apply` — the fold body, selected BY ITS CLASS and not by its argument
    shape. `LockTable.apply` has the identical signature and also reads `p.get("inode")`,
    so a walk keyed on `(self, e)` picks whichever the tree yields first and the row would
    be about a class nobody chose."""
    with open(CUSTODY_PATH, encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == "CustodyState")
    fn = next(n for n in cls.body
              if isinstance(n, ast.FunctionDef) and n.name == "apply")
    return src, fn, ast.get_source_segment(src, fn)

#: THE D4 FENCE, VERBATIM FROM `planning/exec/EP-28P.md`. Data, so the row that reads it
#: is reading the enumeration rather than a reader's memory of it (§A27: the enumeration
#: binds and prose never widens it).
D4_FENCE = (
    "src/founding/founding-pack.json",
    "src/kernel/opdefs.py",
    "src/bridge/kernel_port.py",
    "tests/test_ep28p.py",
)

#: The new law's ONE lawful formal-name source, and the declaration that carries it. Named
#: here so the version test and the fence-only probe use one spelling rather than two.
#: THE LAST FOUNDING THAT DECLARED THE OLD IDENTITY LAW — PINNED BY CONTENT, NOT BY VERSION
#: [EP-28T, 2026-08-08].
#:
#: WHY THIS FILE NEEDS A PIN AT ALL. Every exhibition in `TestTheCONFIRMATION` below was a
#: claim about the world EP-28P found: two lawful creates recording ONE identity, one node
#: under two names, a chmod bleeding through. EP-28S landed the identity law on 2026-08-08 and
#: that world no longer exists, so rows that drove against the LIVE founding started asserting
#: a defect that is gone. THE EXHIBITION IS NOT WRONG — ITS SUBJECT MOVED. Re-pointing these
#: rows at today's outcome would delete the estate's only driven record that the defect was
#: real, which is the one thing an obsolete row must never lose. So the subject is PINNED and
#: the rows keep driving the world they were written about, with today's outcome asserted
#: beside it.
#:
#: AND THE PIN IS CHOSEN BY CONTENT BECAUSE CHOOSING IT BY VERSION PICKS THE WRONG COMMIT.
#: `05f29f7` reads `founding_version: 1.17.0` AND ALREADY CARRIES `mints_from` on all three
#: minting ops — EP-28S's landing caught mid-write by the two-minute commit timer, which is
#: lawful history (EP-00 rule 8) and a trap for anyone pinning on the version string. The
#: version literal and the pack's content disagree in that commit. `d8a184b` is the last one
#: where the CONTENT is the old law: `mints: ["inode"]` on all three, no `mints_from`.
#: `_assert_is_the_pre_law_pack` re-derives that from the pack itself at run time, so the pin
#: is checked rather than trusted and a wrong commit reds instead of quietly exhibiting the
#: new law under the old law's name.
PRE_S_COMMIT = "d8a184b"

FORMAL_NAME = "formal_name"
COORDINATE = "record_coordinate"

#: The three namespace ops that MINT — the ones declaring `mints: ["inode"]` today.
MINTING_OPS = ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK")


class _World:
    """A kernel composed from the SHIPPED founding and nothing else."""

    def __init__(self, tmp, pack_path=None):
        self.dir = tmp
        self.record = os.path.join(tmp, "record.jsonl")
        with _founding_from(pack_path):
            self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
                self.record, os.path.join(tmp, "blobs"), os.path.join(tmp, "vault"))

    def act(self, op, **params):
        params.setdefault("provenance", PROV)
        return self.gate.execute(op, OWNER, params)

    def fold(self):
        return custody.fold(self.store.all())

    def recorded(self, action, field="path"):
        return [(e.get("payload") or {}).get(field) for e in self.store.by_action(action)]


@contextlib.contextmanager
def _founding_from(pack_path):
    """Compose from a pack other than the shipped one. `load_pack` is the pack's ONE reader
    (`founding/install.py:70`), so pointing it is the whole redirection — there is no second
    place a pack can enter, which is why this is a context manager and not a patch set."""
    if pack_path is None:
        yield
        return
    real = founding_install.load_pack
    founding_install.load_pack = lambda path=pack_path: real(pack_path)
    try:
        yield
    finally:
        founding_install.load_pack = real


@contextlib.contextmanager
def _formal_name_law_installed():
    """THE NEW LAW'S DEFINITION-TIME HALF, THROUGH THE LOADED MODULE (§A42, item 24).

    Not a description of what the law would do and not a hand-built refusal: the ONE
    function all three definition doors run (`opdefs.validate_definition_shape`,
    `opdefs.py:881`) is wrapped, so a founding installed inside this block is installed
    under the new vocabulary and nothing else changes.

    ADDITIVE BY CONSTRUCTION: a definition declaring no formal name takes exactly today's
    path. That property is what the version test measures, so it is written here as the
    shape of the wrapper rather than asserted about it afterwards."""
    original = opdefs.validate_definition_shape

    def patched(gate, doorname, actor, name, d, peers=None, **kwargs):
        original(gate, doorname, actor, name, d, peers, **kwargs)
        decl = d.get(FORMAL_NAME)
        if decl is None:
            return
        if decl != COORDINATE:
            gate.refuse(actor, doorname, "AR-2",
                        'this operation declares its formal name comes from %r, and this '
                        'estate holds no such derivation — a formal name is the birth act\'s '
                        'own coordinate in the record (%r) or the operation does not exist'
                        % (decl, COORDINATE))

    opdefs.validate_definition_shape = patched
    inst = getattr(founding_install, "validate_definition_shape", None)
    if inst is not None:
        founding_install.validate_definition_shape = patched
    try:
        yield
    finally:
        opdefs.validate_definition_shape = original
        if inst is not None:
            founding_install.validate_definition_shape = inst


def _pack_with(declaration, ops=MINTING_OPS, version=None):
    """A copy of the SHIPPED pack carrying `declaration` on `ops`. Returns (path, planted).

    `planted` is returned so every caller can assert it is non-zero BEFORE reading the
    result (item 21): a pack that planted nothing loads for reasons that have nothing to do
    with the declaration, and would report a vacuous pass as a real one."""
    with open(FOUNDING_PATH, encoding="utf-8") as f:
        pack = json.load(f)
    if version is not None:
        pack["founding_version"] = version
    planted = 0
    for step in pack["steps"]:
        for r in step["records"]:
            if r.get("action") != "CREATE-OP":
                continue
            if (r.get("payload") or {}).get("name") in ops:
                r["payload"]["definition"][FORMAL_NAME] = declaration
                planted += 1
    d = tempfile.mkdtemp(prefix="ep28p-pack-")
    path = os.path.join(d, "pack.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pack, f)
    return path, planted, d


def _pack_at(commit):
    """The founding pack AS IT WAS at `commit`, written to a temp path. Returns (path, dir).

    [EP-28T] `git show` and nothing else — the estate's own era-pin idiom
    (`test_ep28i.pack_at`, `test_ep28n2.pack_at`), used here for the first time in this file
    because this file's subject is a world that no longer ships.

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. And this docstring is the reason the extraction
    was owed: it names two OTHER FILES as the idiom's home, which is what a mechanism with
    no home looks like from inside one of its copies. ASSERTED: a local `git show` spawn
    with `check=True`. SUPERSEDED: the same act from `tests/era_pin.py`. REMAINS TRUE: the
    failure mode — `check=True` raised `CalledProcessError` and `missing="raise"`, the
    default, is that behaviour by name. GIVEN UP: nothing; the temp-file write is the
    CALLER's business and stays exactly here, which is the separation that lets one home
    serve ten files whose post-processing shares nothing.]"""
    era_text = era_pin.text_at(commit, era_pin.PACK_PATH)
    d = tempfile.mkdtemp(prefix="ep28p-era-")
    path = os.path.join(d, "pack.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(era_text)
    return path, d


class _Tmp(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28p-")
        self._packs = []

    def pre_law_pack(self):
        """The pinned pre-EP-28S founding, CHECKED rather than trusted."""
        path, d = _pack_at(PRE_S_COMMIT)
        self._packs.append(d)
        self._assert_is_the_pre_law_pack(path)
        return path

    def _assert_is_the_pre_law_pack(self, path):
        """NON-VACUITY FOR THE PIN ITSELF (item 21), and it is what makes the commit hash a
        fact rather than a memory: the pinned pack must declare `mints` on all three minting
        ops and `mints_from` on none. A pin that had drifted onto a post-landing commit would
        exhibit the NEW law under the OLD law's name, which is the failure mode a bare hash
        cannot detect."""
        with open(path, encoding="utf-8") as f:
            pack = json.load(f)
        by_field, by_coordinate = set(), set()
        for s in pack["steps"]:
            for r in s["records"]:
                if r.get("action") != "CREATE-OP":
                    continue
                name = (r.get("payload") or {}).get("name")
                if name not in MINTING_OPS:
                    continue
                d = r["payload"]["definition"]
                if d.get("mints"):
                    by_field.add(name)
                if d.get("mints_from"):
                    by_coordinate.add(name)
        self.assertEqual(by_field, set(MINTING_OPS),
                         "the pinned pack does not declare the OLD law — the pin has drifted "
                         "onto a commit at or after EP-28S's landing")
        self.assertEqual(by_coordinate, set(),
                         "the pinned pack already carries the NEW law")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        for d in self._packs:
            shutil.rmtree(d, ignore_errors=True)

    def world(self, pack_path=None):
        return _World(tempfile.mkdtemp(dir=self.dir), pack_path)

    def pack_with(self, declaration, ops=MINTING_OPS, version=None):
        path, planted, d = _pack_with(declaration, ops, version)
        self._packs.append(d)
        return path, planted


# =======================================================================================
# W2 — THE CONFIRMATION. Not a hazard hunt: this establishes the baseline the law repairs.
# =======================================================================================
class TestTheCONFIRMATION(_Tmp):
    """AMENDMENT 10's rename-recreate exhibition, RE-HOMED HERE and DRIVEN.

    IT REPRODUCED. The EP states in advance that a fails-to-reproduce would be a FINDING
    re-pricing the object layer and a good outcome; it is recorded here that the object
    layer was NOT re-priced, because the mechanism drove.

    AND IT DRIVES FURTHER THAN THE AMENDMENT PREDICTED. AMENDMENT 10 describes an
    ALLOCATION collision — "the backend's allocation collides". What actually happens is
    that the two files ARE ONE NODE: they share a number, they share metadata, and the fold
    reports them as hard links of each other. A chmod through one name changes the other.
    That is a data consequence, not an allocation one, and it is driven below rather than
    reasoned from the identity equality.

    `tests/test_ep28o.py:719` holds the same exhibition at the RECORD layer and names it as
    EP-28P's. This file does not duplicate that row — it establishes what the FOLD does
    with the two records, which is the half that pass could not reach."""

    def test_two_LAWFUL_creates_record_ONE_identity(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW; the subject is ERA-PINNED and the
        exhibition is KEPT DRIVING.]

        ASSERTED (2026-08-07, EP-28P): under the founding as it then shipped, two lawful
        creates of one path record ONE identity, `/a` both times.
        SUPERSEDED (2026-08-08, EP-28S, founding 1.18.0): a birth act records no identity at
        all and is named by its own coordinate, so against the LIVE founding this row raised
        `KeyError: 'inode'` — an obsolete READ, not a refuted claim.
        REMAINS TRUE and STILL DRIVEN, against the world it was always about: the pre-landing
        founding is pinned at `PRE_S_COMMIT` and the exhibition runs on it unchanged. The
        estate keeps a DRIVEN record that the defect was real, which no prose can replace.
        AND TODAY'S OUTCOME IS ASSERTED BESIDE IT rather than instead of it, so this one row
        carries both the disease and the cure and neither can be mistaken for the other."""
        w = self.world(self.pre_law_pack())
        first = w.act("FILE-CREATE", path="/a")
        w.act("FILE-RENAME", path="/a", new_path="/b")
        second = w.act("FILE-CREATE", path="/a")
        # NON-VACUITY: two DISTINCT acts, or "they share an identity" is trivially true.
        self.assertNotEqual(first["seq"], second["seq"],
                            "two distinct acts, or the comparison below is about one act")
        self.assertEqual(first["payload"]["inode"], "/a")
        self.assertEqual(second["payload"]["inode"], "/a")
        # AND TODAY: the same two lawful acts, under the shipped founding, record NO identity
        # and are named by their own coordinates — which cannot be equal.
        now = self.world()
        n1 = now.act("FILE-CREATE", path="/a")
        now.act("FILE-RENAME", path="/a", new_path="/b")
        n2 = now.act("FILE-CREATE", path="/a")
        self.assertEqual(now.recorded("FILE-CREATE", "inode"), [None, None])
        self.assertNotEqual(custody.formal_name(n1["seq"]), custody.formal_name(n2["seq"]))

    def test_NEITHER_CREATE_WAS_REFUSED_which_is_why_the_record_is_wrong_and_not_the_state(self):
        """The second create is LAWFUL: the rename freed the name, so the `unbound` binding
        check passes. Both acts are correct under the law that governed them; what is wrong
        is that the record now attributes two histories to one identity."""
        w = self.world()
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-RENAME", path="/a", new_path="/b")
        w.act("FILE-CREATE", path="/a")
        creates = w.store.by_action("FILE-CREATE")
        self.assertEqual(len(creates), 2)
        self.assertFalse(any(e.get("refused") for e in creates),
                         "both creates were accepted — the defect is not a missing refusal")

    def test_THE_CONSEQUENCE_the_two_files_are_ONE_NODE_in_the_folded_state(self):
        """[EP-28T, 2026-08-08 — ERA-PINNED, and today's outcome asserted beside it.]

        ASSERTED: the two files are ONE NODE — one number, both names on it, `nlink` 2 for
        files nobody linked. SUPERSEDED by EP-28S. REMAINS DRIVEN on the pinned pre-law
        founding; the repair is asserted below as the same drive with a different answer, and
        the pair is what makes the repair legible."""
        w = self.world(self.pre_law_pack())
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-RENAME", path="/a", new_path="/b")
        w.act("FILE-CREATE", path="/a")
        st = w.fold()
        self.assertIn("/a", st.names)
        self.assertIn("/b", st.names)
        self.assertEqual(st.names["/a"], st.names["/b"],
                         "the two files share one inode number")
        self.assertEqual(sorted(st.paths[st.names["/a"]]), ["/a", "/b"])
        self.assertEqual(st.nlink(st.names["/a"]), 2,
                         "the fold reports two files nobody linked as hard links")
        # AND TODAY, THE SAME DRIVE: two nodes, one name each, `nlink` 1 each.
        now = self.world()
        now.act("FILE-CREATE", path="/a")
        now.act("FILE-RENAME", path="/a", new_path="/b")
        now.act("FILE-CREATE", path="/a")
        st2 = now.fold()
        self.assertNotEqual(st2.names["/a"], st2.names["/b"])
        self.assertEqual(st2.nlink(st2.names["/a"]), 1)
        self.assertEqual(st2.nlink(st2.names["/b"]), 1)

    def test_A49_LEAST_LIKELY_a_chmod_through_ONE_name_reaches_the_OTHER(self):
        """§A49's least-likely member: the collision is usually described at CREATE time,
        so the member least likely to be checked is a LATER metadata act. It bleeds.

        [EP-28T, 2026-08-08 — ERA-PINNED. THIS IS THE ROW THE WHOLE CAMPAIGN'S ACCEPTANCE
        TURNS ON, so it keeps driving BOTH worlds: the bleed on the pinned pre-law founding,
        and its absence today. A row that only showed the absence would be indistinguishable
        from a suite that never tested for the bleed at all — which is the exact reason the
        mentor ruled per-row treatment rather than a sweep.]"""
        w = self.world(self.pre_law_pack())
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-RENAME", path="/a", new_path="/b")
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-PERM", path="/b", perm="600")
        st = w.fold()
        self.assertEqual(st.inodes[st.names["/b"]].perm, 0o600)
        self.assertEqual(st.inodes[st.names["/a"]].perm, 0o600,
                         "a chmod addressed to /b changed /a, because they are one node")
        # AND TODAY: the same chmod, addressed to the same name, reaches nothing else.
        now = self.world()
        now.act("FILE-CREATE", path="/a")
        now.act("FILE-RENAME", path="/a", new_path="/b")
        now.act("FILE-CREATE", path="/a")
        now.act("FILE-PERM", path="/b", perm="600")
        st2 = now.fold()
        self.assertEqual(st2.inodes[st2.names["/b"]].perm, 0o600, "the addressed file moved")
        self.assertEqual(st2.inodes[st2.names["/a"]].perm, 0o644,
                         "a chmod addressed to /b reached /a — the collision is back")

    def test_NEAR_MISS_two_genuinely_distinct_names_do_NOT_collide(self):
        """§A64, the other way. The row above must be about REUSE and not about creates in
        general: two different names get two different nodes, and this reds if the fold
        ever collapses distinct names."""
        w = self.world()
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-CREATE", path="/c")
        st = w.fold()
        self.assertNotEqual(st.names["/a"], st.names["/c"])
        self.assertEqual(st.nlink(st.names["/a"]), 1)

    def test_NEAR_MISS_re_creating_after_UNLINK_is_the_SAME_thing_and_is_not_the_defect(self):
        """§A64, the harder direction. Unlink-then-recreate ALSO reuses a name — and there
        it is correct that the identity is the same, because the earlier object is gone.
        A repair that made every name-reuse mint a new identity would break this, so the
        row is here to hold the successor pass to the narrower claim."""
        w = self.world()
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-UNLINK", path="/a")
        w.act("FILE-CREATE", path="/a")
        st = w.fold()
        self.assertEqual(len(st.paths.get(st.names["/a"], {})), 1,
                         "one live name; nothing joined, because nothing else survives")
        self.assertEqual(st.nlink(st.names["/a"]), 1)

    def test_THE_RESOLUTION_IS_NOT_RECORDED_unless_a_CALLER_supplies_it(self):
        """D2 item 2 says an act must record BOTH names AND the resolution. It does not.

        Only the three MINTING ops derive `inode` from `$path`; every later act carries an
        identity ONLY if its caller hands one in. So the record's resolution is
        CALLER-ASSERTED where it exists at all — which is the naming law's own defect
        arriving at the second layer: the caller supplying what the system should decide."""
        w = self.world()
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-PERM", path="/a", perm="600")
        perm_rec = w.store.by_action("FILE-PERM")[0]
        self.assertIsNone(perm_rec["payload"].get("inode"),
                          "no resolution is recorded when the caller supplies none")
        # NEAR-MISS (§A64) the other way: supplied, it IS recorded — so the row above is
        # about the DERIVATION being absent, not about the field being unwritable.
        w.act("FILE-PERM", path="/a", inode="/a", perm="640")
        self.assertEqual(w.store.by_action("FILE-PERM")[1]["payload"].get("inode"), "/a")

    def test_only_the_MINTING_ops_derive_an_identity_which_is_WHY(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW, ERA-PINNED for the same reason as
        the rows above.]

        ASSERTED: exactly the three minting ops carry `param_defaults {"inode": "$path"}` —
        which is WHY the collision was theirs alone and not the whole op population's.
        SUPERSEDED (EP-28S): no op carries that default any more; the three declare
        `mints_from: record_coordinate` instead.
        REMAINS TRUE, and it is the row's actual subject: **ONLY THE MINTING OPS DERIVE AN
        IDENTITY, AND IT IS STILL EXACTLY THOSE THREE.** The set has not moved; only the
        source it derives from has. Asserted on BOTH foundings, so the row says the set is
        stable ACROSS the law change rather than restating one side of it."""
        def deriving_in(pack):
            out = set()
            for s in pack["steps"]:
                for r in s["records"]:
                    if r.get("action") != "CREATE-OP":
                        continue
                    d = ((r.get("payload") or {}).get("definition") or {})
                    if (d.get("param_defaults") or {}).get("inode") == "$path" \
                            or d.get("mints_from"):
                        out.add(r["payload"]["name"])
            return out
        with open(FOUNDING_PATH, encoding="utf-8") as f:
            live = json.load(f)
        with open(self.pre_law_pack(), encoding="utf-8") as f:
            era = json.load(f)
        self.assertEqual(deriving_in(era), set(MINTING_OPS),
                         "the pinned pre-law founding derived on exactly the three")
        self.assertEqual(deriving_in(live), set(MINTING_OPS),
                         "and the shipped founding still derives on exactly the three")

    def test_THE_ROUND_TRIP_IS_GREEN_WHILE_THE_RECORD_IS_WRONG(self):
        """The property that makes this class of defect invisible to every guard in the
        estate: the served state and the replayed state AGREE. Both derive the same
        identity from the same records, so nothing that compares them can see it."""
        w = self.world()
        w.act("FILE-CREATE", path="/a")
        w.act("FILE-RENAME", path="/a", new_path="/b")
        w.act("FILE-CREATE", path="/a")
        replayed = custody.fold(w.store.all())
        again = custody.fold(w.store.all())
        self.assertEqual(replayed.snapshot(), again.snapshot(),
                         "kill it, replay, identical — and the wrongness survives intact")


# =======================================================================================
# W3 — THE VERSION QUESTION IS A TEST THE BUILDER EXECUTES, NEVER A NUMBER IT IS GIVEN
# =======================================================================================
class TestTheVERSIONQuestionWasEXECUTEDAndTookMINOR(_Tmp):
    """THE RULED TEST (mentor, 2026-08-07, applying the EP-28I discriminator): does the
    CURRENT founding, BYTE-UNCHANGED, still LOAD under the new law?

    Loads -> MINOR. Does not load -> MAJOR, which is a STOP to the mentor before the pass
    proceeds. MAJOR has never been taken in this estate — the ladder is 1.11 -> 1.17, six
    moves, all MINOR — and it is not a bump a pass takes on its own.

    THE BRANCH TAKEN IS **MINOR**, and it is taken by running the load rather than by
    reasoning about the shape of the change. The guard is shown able to REFUSE first,
    because a founding that loads past a guard that cannot refuse establishes nothing."""

    def test_the_new_laws_guard_CAN_REFUSE(self):
        """Item 21 non-vacuity, and it comes FIRST. Everything below is void without it."""
        path, planted = self.pack_with("whatever-the-caller-said", ops=("FILE-CREATE",))
        self.assertGreaterEqual(planted, 1, "nothing planted — this arm would be vacuous")
        with _formal_name_law_installed():
            with self.assertRaises(Exception) as cm:
                self.world(path)
        self.assertIn("formal name", str(cm.exception).lower())

    def test_NEAR_MISS_the_LAWFUL_declaration_is_ADMITTED(self):
        """§A64 the other way: a guard that refuses everything is not a guard."""
        path, planted = self.pack_with(COORDINATE)
        self.assertEqual(planted, 3, "all three minting ops carry the declaration")
        with _formal_name_law_installed():
            w = self.world(path)
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: this row boots a copy
        # of the SHIPPED pack, deliberately, and asserted the frozen 72 that pack held when this
        # pass ran; EP-29 W1b added two op definitions and the shipped pack now holds 74.
        # ASSERTED: the literal 72. SUPERSEDED: the count COMPUTED FROM THE STRUCTURE of the
        # very pack this world booted from — §A51's own doctrine, "the population is COMPUTED
        # from the structure and reconciled, never carried", applied to the row that was
        # carrying one. REMAINS TRUE, and STRICTLY STRONGER: the claim was never about the
        # number 72, it was that the lawful declaration is ADMITTED and every op still loads;
        # a frozen literal could only catch a dropped op until the next lawful growth, and this
        # catches one forever. GIVEN UP: nothing — an op silently dropped at boot still reds.]
        with open(FOUNDING_PATH, encoding="utf-8") as fh:
            shipped = json.load(fh)
        expected = sum(1 for st in shipped["steps"] for r in st["records"]
                       if r.get("action") == "CREATE-OP")
        self.assertEqual(len(w.store.by_action("CREATE-OP")), expected)

    def test_THE_RULED_TEST_the_SHIPPED_founding_LOADS_under_the_new_law(self):
        """The branch: **MINOR**. `inode: $path` survives as the alias's seed, formal names
        would be minted alongside, and nothing existing is invalidated.

        [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and the SUBJECT is what moved.]
        ASSERTED: the founding THEN SHIPPING, byte-unchanged, loads under the new vocabulary
        and still executes a create — the MINOR branch, taken by running rather than by
        reasoning.
        SUPERSEDED: "the SHIPPED founding" now means 1.18.0, which IS the new law. Asking
        whether it loads under the new law is asking whether the new law admits itself, and
        the create it drives records no `inode`, which is why this row raised `KeyError`.
        REMAINS TRUE and STILL DRIVEN, with the subject pinned to what the sentence meant when
        it was written: THE PRE-LANDING FOUNDING, byte-unchanged, loads under the new
        vocabulary and still executes a create recording its own path-derived identity. That is
        the MINOR branch, and it is now checkable forever instead of only on the day it was
        taken. THE PIN IS THE POINT: a compatibility claim whose "old side" is read live stops
        being a compatibility claim the moment the old side is replaced."""
        era = self.pre_law_pack()
        with open(era, encoding="utf-8") as f:
            before = f.read()
        with _formal_name_law_installed():
            w = self.world(era)                   # the PRE-LANDING pack, unmodified
            rec = w.act("FILE-CREATE", path="/probe")
        self.assertEqual(len(w.store.by_action("CREATE-OP")), 72)
        self.assertEqual(rec["payload"]["inode"], "/probe",
                         "and a create still executes, not merely loads")
        with open(era, encoding="utf-8") as f:
            self.assertEqual(f.read(), before, "the pinned pack was never written")

    def test_the_declaration_is_ADDITIVE_which_is_WHY_the_branch_is_minor(self):
        """The mechanism behind the branch, held separately from the branch itself: a
        definition that declares nothing takes exactly today's path. Every shipped
        definition declares nothing, so every one of them is untouched."""
        with open(FOUNDING_PATH, encoding="utf-8") as f:
            pack = json.load(f)
        declaring = [r for s in pack["steps"] for r in s["records"]
                     if r.get("action") == "CREATE-OP"
                     and FORMAL_NAME in ((r.get("payload") or {}).get("definition") or {})]
        self.assertEqual(declaring, [], "the shipped founding declares no formal name")


# =======================================================================================
# THE FENCE STOP — driven, because it is the pass's entire product
# =======================================================================================
class TestAFenceOnlyLandingRepairsNOTHING(_Tmp):
    """WHY THIS PASS STOPPED, EXHIBITED RATHER THAN ARGUED.

    D4 enumerates four files. This installs the ENTIRE fenced half of the law — the
    founding moved to 1.18.0 and declaring `formal_name: record_coordinate` on all three
    minting ops, validated by the definition-time vocabulary — and then re-drives
    rename-recreate.

    THE COLLISION STANDS. The founding moved, the declaration validates, the suite would
    be green, AND THE DEFECT IS UNTOUCHED — because the fold that derives a node's identity
    is `src/bridge/custody.py:350` and it never reads the declaration.

    THAT IS THE BURIAL SHAPE THE EP REFUSES BY NAME, and it is why a fence stop was the
    correct outcome rather than a failure to finish."""

    def test_the_fenced_half_LOADS_and_the_founding_MOVES(self):
        path, planted = self.pack_with(COORDINATE, version="1.18.0")
        self.assertEqual(planted, 3)
        with _formal_name_law_installed():
            w = self.world(path)
        found = [e for e in w.store.all()
                 if (e.get("payload") or {}).get("founding_version")]
        self.assertTrue(found, "the founding designation carries a version")
        self.assertEqual(found[0]["payload"]["founding_version"], "1.18.0")

    def test_AND_THE_COLLISION_IS_EXACTLY_WHERE_IT_WAS(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW, ERA-PINNED, and this row is the
        estate's ONLY driven proof that a declaration alone repairs nothing.]

        ASSERTED: install the ENTIRE fenced half — the founding moved to 1.18.0 declaring the
        coordinate on all three minting ops, validated at definition time — re-drive
        rename-recreate, AND THE COLLISION STANDS, because the fold never reads the
        declaration. That is why EP-28P stopped at its fence instead of finishing.
        SUPERSEDED (EP-28S): the fold now DOES derive from the coordinate, so a world built
        this way no longer collides — the row's `assertEqual` on the two names went red
        because the burial shape it exhibits is no longer reachable through the live fold.
        REMAINS TRUE and STILL DRIVEN, on the pinned pre-law pack with the declaration planted
        on top: a DECLARATION WITHOUT A FOLD THAT READS IT BINDS NOTHING. The `param_defaults`
        the pinned pack still carries is what the fold then keys on, which is exactly the
        fence-only world EP-28P described. THE BURIAL SHAPE STAYS EXHIBITED — deleting this
        row would leave the estate asserting that declarations work, with no driven evidence
        that one alone does not."""
        base = self.pre_law_pack()
        with open(base, encoding="utf-8") as f:
            pack = json.load(f)
        pack["founding_version"] = "1.18.0"
        planted = 0
        for step in pack["steps"]:
            for r in step["records"]:
                if (r.get("action") == "CREATE-OP"
                        and (r.get("payload") or {}).get("name") in MINTING_OPS):
                    r["payload"]["definition"][FORMAL_NAME] = COORDINATE
                    planted += 1
        d = tempfile.mkdtemp(prefix="ep28p-fenceonly-")
        self._packs.append(d)
        path = os.path.join(d, "pack.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pack, f)
        self.assertEqual(planted, 3, "nothing planted — this world would be vacuous")
        with _formal_name_law_installed():
            w = self.world(path)
            w.act("FILE-CREATE", path="/a")
            w.act("FILE-RENAME", path="/a", new_path="/b")
            w.act("FILE-CREATE", path="/a")
        st = w.fold()
        self.assertEqual(st.names["/a"], st.names["/b"],
                         "the declaration bound nothing: the fold still keys on the path")
        self.assertEqual(w.recorded("FILE-CREATE", "inode"), ["/a", "/a"])

    def test_THE_REASON_the_fold_reads_no_declaration_at_all(self):
        """PATCH WHERE THE CONSUMER LOOKS. `CustodyState.apply` takes ONE argument — a
        record — and derives identity from its payload. It has no access to the op
        definition, so no declaration on a definition can reach it. Located structurally."""
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]
        # ASSERTED: the fold takes ONE argument and no declaration can reach it — detected by
        #   the absence of the strings `formal_name` and `definition` in `apply`'s body.
        # SUPERSEDED (EP-28S): `apply` now CALLS `formal_name`, so the first detector reds.
        #   The CLAIM did not change and the detector was never the claim: `formal_name` is a
        #   pure function of the record's own coordinate, not a reader of an op definition, so
        #   its presence says nothing about whether a declaration can reach the fold.
        # REMAINS TRUE, separated out and STILL ASSERTED, in a form keyed to the PROPERTY
        #   instead of to a name that happened to be absent: `apply` takes `(self, e)` and
        #   nothing else, and its body reads no op definition, no founding pack and no gate.
        #   That is what "no declaration can reach it" means, and it is why EP-28S could land
        #   the law without this row's subject moving — an act stands under the law of its
        #   deciding time, so the fold reads the RECORD's shape and never today's declaration.
        # THE LESSON THIS ROW IS: A DETECTOR THAT NAMES A SYMBOL DIES WHEN THE SYMBOL MOVES.
        #   Naming the argument list and the absent READERS survives, because those are the
        #   property rather than a spelling of it.
        # AND THE INSTRUMENT IS AN AST WALK, NOT A TEXT SEARCH, WHICH THIS ROW LEARNED THE
        # HARD WAY IN THIS VERY EDIT: `assertNotIn("definition", body)` went red on the word
        # "definition" inside `apply`'s own COMMENTS, which discuss the declaration they refuse
        # to read. A grep answers a question about TEXT; the question here is about what the
        # function READS, which is structure. Same lesson as EP-28E W5's `json` matching
        # `"rec.jsonl"`, met again one file over.
        _src, fn, _body = _custody_apply()
        self.assertEqual([a.arg for a in fn.args.args], ["self", "e"],
                         "the fold sees a record and nothing else")
        names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        read = names | attrs
        for reader in ("definition", "op_definitions", "load_pack", "founding_version",
                       "load_founding", "gate", "views", "opdefs"):
            self.assertNotIn(reader, read,
                             "the fold reads %r — a declaration can now reach it and "
                             "EP-28P's whole reason for stopping is void" % reader)
        # CAN-FAIL, so the walk is known to be looking at something: the identifiers the fold
        # DOES read are present, and a reader-name check that finds nothing at all would pass
        # this row while inspecting an empty set.
        self.assertIn("formal_name", read, "the walk found no identifiers — it is broken")
        self.assertIn("get", attrs)

    def test_THE_FENCE_ITSELF_read_from_the_EP_and_it_does_NOT_name_the_fold(self):
        """§A27: the ENUMERATION binds and prose never widens it — so the enumeration is
        READ FROM THE ORDER rather than remembered. This resolves the citation mechanically.

        THIS ROW IS A TRIPWIRE AND IT RETIRES BY FIRING. When the mentor widens the fence to
        include the fold, it reds — which is exactly when someone should read this file."""
        with open(EP_PATH, encoding="utf-8") as f:
            ep = f.read()
        section = ep.split("## D4 — Scope fence", 1)[1].split("## D5", 1)[0]
        enumerated = set(re.findall(r"`([\w./-]+\.(?:py|json))`", section))
        self.assertGreaterEqual(len(enumerated), 3,
                                "the fence parsed to %r — the reader is broken, not the "
                                "fence" % (enumerated,))
        self.assertEqual(enumerated, set(D4_FENCE),
                         "the fence in the order and the fence this file was built against "
                         "have diverged")
        self.assertNotIn("src/bridge/custody.py", enumerated,
                         "THE FENCE HAS BEEN WIDENED TO THE FOLD — this pass's stop is "
                         "discharged and this row retires")


# =======================================================================================
# W2b — THE THREE SPACES. The EP's PROPOSED shape is refuted; the replacement is driven.
# =======================================================================================
SEQ_FLOOR = 1 << 61


def _formal_name_of(seq, seq_floor=SEQ_FLOOR, render_floor=None):
    """THE PROPOSED FORMAL NAME: the birth act's coordinate, LIFTED INTO ITS OWN BAND.

    WHY NOT THE BARE `seq`, which is what D1a proposed. A legacy stamp and a `seq` are both
    small positive integers, so they are told apart by PROVENANCE and not by VALUE — and
    `custody.render_ino` is a pure function of the value, which is precisely the property
    that lets the C half parse what the brain rendered instead of computing its own answer
    (`custody.py:735-739`). A rendering that had to know WHICH allocator minted an integer
    could not stay pure. Lifting the coordinate into a band makes the value self-describing
    and keeps the rendering exactly as pure as it is today."""
    rf = custody.RENDER_FLOOR if render_floor is None else render_floor
    if seq < 1:
        raise ValueError("a seq is 1-based; %r is not a record coordinate" % (seq,))
    n = seq_floor + seq
    if n >= rf:
        raise ValueError("the record's coordinates no longer fit the formal-name band")
    return n


def _space_of(n, seq_floor=SEQ_FLOOR):
    if n < seq_floor:
        return "LEGACY"
    if n < custody.RENDER_FLOOR:
        return "FORMAL"
    return "DIGEST"


class TestTheEPsProposedBandShapeIsREFUTED(unittest.TestCase):
    """W2b's PROPOSED shape says the seq band renders "above a MEASURED legacy ceiling
    (legacy mints are FROZEN — their maximum is a fixed value the builder takes, never
    assumes)".

    THE PREMISE IS FALSE AGAINST THE CODE and this holds it so. `records_fs.py` still
    stamps live, so the legacy space has no ceiling to measure: it grows by one per create
    in any world the FUSE port serves. A band placed above a "measured maximum" would be
    placed above a number that moves."""

    def test_the_legacy_allocator_is_STILL_LIVE_so_there_is_no_ceiling_to_measure(self):
        st = custody.CustodyState()
        first = custody.mint_ino(st)
        second = custody.mint_ino(st)
        self.assertEqual((first, second), (2, 3),
                         "the allocator hands out and advances — it is not frozen")

    def test_and_it_is_REACHED_from_the_FUSE_port_which_is_shipped_code(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and this is the one row in the file
        whose CLAIM ABOUT THE WORLD IS NOW FALSE rather than merely differently expressed. It
        is recorded as a refutation, which is what the estate does with those.]

        ASSERTED (2026-08-07, EP-28P): the legacy allocator is reached from `records_fs.py` at
        THREE live call sites, so the legacy number space has no ceiling to measure — it grows
        by one per create in any world the FUSE port serves. That was the evidence refuting the
        EP's proposed "band above a measured legacy ceiling".
        SUPERSEDED (2026-08-08, EP-28S): the port's mint sites were REMOVED with the landing.
        `records_fs.py` calls `_mint_ino` ZERO times. Measured, not assumed — the same AST walk
        that found three now finds none.
        REMAINS TRUE, separated out and STILL ASSERTED, and the refutation SURVIVES its own
        evidence changing: `custody.mint_ino` is still shipped and still hands out and advances
        (the row above drives it), so the legacy space still has no fixed maximum a band could
        be placed above. What changed is that no SHIPPED CALLER reaches it — which strengthens
        the refutation's conclusion while removing one of its two supports, and both halves are
        asserted so a reader can see which is which.
        AND THE COUNT IS ASSERTED AS ZERO RATHER THAN DELETED, because "no shipped caller
        mints" is now a live property worth a guard: a new call site appearing here would mean
        the retired regime had come back, and this row is where that reds."""
        path = os.path.join(REPO, "src", "bridge", "records_fs.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        calls = [n.lineno for n in ast.walk(tree)
                 if isinstance(n, ast.Call)
                 and getattr(n.func, "attr", None) == "_mint_ino"]
        self.assertEqual(calls, [],
                         "the port mints again at %r — the stamping regime EP-28S retired has "
                         "returned to shipped code" % (calls,))
        # AND THE REFUTATION'S SURVIVING SUPPORT, kept asserted: the allocator itself is not
        # frozen, so there is still no measured ceiling for a band to sit above.
        self.assertTrue(hasattr(custody, "mint_ino"))

    def test_a_seq_and_a_legacy_stamp_are_INDISTINGUISHABLE_BY_VALUE_today(self):
        """The finding under the refutation: today a `seq` renders straight into the legacy
        space, so the bare coordinate cannot be the formal name."""
        seq = 137
        self.assertEqual(custody.render_ino(seq), seq)
        self.assertLess(custody.render_ino(seq), custody.RENDER_FLOOR)
        self.assertEqual(custody.render_ino(seq), custody.render_ino(137),
                         "a legacy stamp of 137 and record 137 render identically")


class TestTheTHREESPACESAreDisjointByConstruction(unittest.TestCase):
    """THE REPLACEMENT SHAPE, DERIVED AND DRIVEN. Three bands, each with a floor, exactly
    as `RENDER_FLOOR` already separates two:

        LEGACY stamps   [1, 2**61)
        FORMAL names    [2**61, 2**62)
        DIGEST renders  [2**62, 2**63)

    NOT A LANDING. Every line of this belongs in `src/bridge/custody.py`, which D4 does not
    name, so it is DRIVEN HERE against a local derivation and carried to the successor pass
    as established rather than as a paragraph it has to re-derive."""

    def test_the_three_bands_are_pairwise_DISJOINT(self):
        legacy = [1, 2, 3, 4096, 10 ** 6, SEQ_FLOOR - 1]
        formal = [_formal_name_of(s) for s in (1, 2, 137, 10 ** 6)]
        digest = [custody.render_ino(p) for p in ("/a", "/b", "/x/y/z", "/" + "q" * 200)]
        # NON-VACUITY before any comparison: N > 0 in every space.
        for name, vals in (("legacy", legacy), ("formal", formal), ("digest", digest)):
            self.assertGreater(len(vals), 0, "%s space asserted empty" % name)
        self.assertEqual({_space_of(v) for v in legacy}, {"LEGACY"})
        self.assertEqual({_space_of(v) for v in formal}, {"FORMAL"})
        self.assertEqual({_space_of(v) for v in digest}, {"DIGEST"})
        self.assertFalse(set(legacy) & set(formal))
        self.assertFalse(set(formal) & set(digest))
        self.assertFalse(set(legacy) & set(digest))

    def test_A64_NEAR_MISS_the_legacy_ceiling_BOTH_WAYS(self):
        self.assertEqual(_space_of(SEQ_FLOOR - 1), "LEGACY", "just inside")
        self.assertEqual(_space_of(SEQ_FLOOR), "FORMAL", "just outside")

    def test_A64_NEAR_MISS_the_digest_floor_BOTH_WAYS(self):
        self.assertEqual(_space_of(custody.RENDER_FLOOR - 1), "FORMAL", "just inside")
        self.assertEqual(_space_of(custody.RENDER_FLOOR), "DIGEST", "just outside")

    def test_the_boundaries_REFUSE_rather_than_overlapping(self):
        """The refusal precedent this estate actually holds is `custody.apply`'s
        `UnrenderableIdentity` raise (`custody.py:373-378`), NOT a function called
        `render_bind` — see `TestTheCITATIONSResolve`."""
        with self.assertRaises(ValueError):
            _formal_name_of(custody.RENDER_FLOOR - SEQ_FLOOR)
        with self.assertRaises(ValueError):
            _formal_name_of(0)

    def test_every_band_fits_the_WIRE_and_the_MODULE(self):
        """`long long` on the wire and `unsigned long` in the module — the constraint
        `tests/test_ep28c_w4b.py:487-489` already holds for two spaces, held for three."""
        for v in (SEQ_FLOOR, custody.RENDER_FLOOR - 1,
                  _formal_name_of(1), custody.render_ino("/a")):
            self.assertGreater(v, 0)
            self.assertLess(v, 1 << 63)

    def test_THE_CAP_RETIREMENT_a_formal_name_needs_NO_DIGEST(self):
        """D1a gain 1, MEASURED. A path identity is a 62-bit digest with a stated birthday
        bound; a formal name is `floor + seq` and `seq` is minted as `len(events)+1` under
        the store's write lock (`store.py:810`), so the map is INJECTIVE."""
        names = {_formal_name_of(s) for s in range(1, 20001)}
        self.assertEqual(len(names), 20000, "no collisions are possible, not merely few")

    def test_AND_THE_CAP_DOES_NOT_RETIRE_FOR_RECORDED_WORLDS(self):
        """Stated so the gain is not overclaimed: this is PROSPECTIVE. The digest space and
        its cap survive for every world already recorded under path-identity."""
        self.assertEqual(custody.render_ino("/a"), 7816720163859614224,
                         "the digest rendering is unchanged and still serves")


# =======================================================================================
# W1 — WHERE IDENTITY IS DERIVED. Cited by file:line, resolved mechanically.
# =======================================================================================
class TestWhereIdentityIsDERIVED(unittest.TestCase):
    """W1's establishment carried as assertions rather than as sentences in a log entry.

    [EP-28T, 2026-08-08] Two of its rows read a founding that no longer ships, so they gained
    the same era pin `_Tmp` carries. This class is not a `_Tmp` — it needs no world — so the
    pin arrives through `pre_law_pack` below with its own cleanup.

    THE CITATIONS: identity is DERIVED from the caller's path by the founding
    (`param_defaults {"inode": "$path"}` on the three minting ops), RESOLVED by
    `opdefs._interpreter`'s `param_defaults` loop, KEYED by `custody.apply`, and RENDERED by
    `custody.render_ino`. Three of those four sites are outside D4's enumeration."""

    def pre_law_pack(self):
        """The pinned pre-EP-28S founding, with the same content check `_Tmp` applies."""
        path, d = _pack_at(PRE_S_COMMIT)
        self.addCleanup(shutil.rmtree, d, True)
        with open(path, encoding="utf-8") as f:
            pack = json.load(f)
        declaring = {r["payload"]["name"] for s in pack["steps"] for r in s["records"]
                     if r.get("action") == "CREATE-OP"
                     and (r.get("payload") or {}).get("name") in MINTING_OPS
                     and (r["payload"]["definition"].get("mints"))}
        self.assertEqual(declaring, set(MINTING_OPS),
                         "the pin has drifted off the pre-law founding")
        return path

    def test_the_founding_derives_identity_from_the_PATH_on_exactly_the_minting_ops(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW; W1's ESTABLISHMENT is a statement
        about the founding EP-28P read, so its subject is PINNED.]

        ASSERTED: the founding derives identity from the PATH — `param_defaults {"inode":
        "$path"}` with `mints: ["inode"]` — on exactly the three minting ops. This is the
        citation the whole pass rests on.
        SUPERSEDED (EP-28S): no op derives from `$path` any more, so against the live pack the
        set is empty.
        REMAINS TRUE and STILL DRIVEN against the pinned founding, because a W1 ESTABLISHMENT
        IS A HISTORICAL READING and re-pointing it would erase what EP-28P actually found.
        AND WHAT REPLACED IT IS ASSERTED BESIDE IT, so this row now carries the whole arc of
        the citation: from `$path` on three ops, to `record_coordinate` on the same three."""
        with open(self.pre_law_pack(), encoding="utf-8") as f:
            pack = json.load(f)
        derive = {}
        for s in pack["steps"]:
            for r in s["records"]:
                if r.get("action") != "CREATE-OP":
                    continue
                d = (r.get("payload") or {}).get("definition") or {}
                if (d.get("param_defaults") or {}).get("inode") == "$path":
                    derive[r["payload"]["name"]] = d.get("mints")
        self.assertEqual(sorted(derive), sorted(MINTING_OPS))
        for name, mints in derive.items():
            self.assertEqual(mints, ["inode"], "%s declares what it mints" % name)
        # AND WHAT THE SHIPPED FOUNDING SAYS NOW: the same three ops, the other source.
        with open(FOUNDING_PATH, encoding="utf-8") as f:
            live = json.load(f)
        now = {r["payload"]["name"]: ((r.get("payload") or {}).get("definition") or {})
               for s in live["steps"] for r in s["records"]
               if r.get("action") == "CREATE-OP"
               and (r.get("payload") or {}).get("name") in MINTING_OPS}
        self.assertEqual(sorted(now), sorted(MINTING_OPS))
        for name, d in now.items():
            self.assertEqual(d.get("mints_from"), "record_coordinate", name)
            self.assertIsNone((d.get("param_defaults") or {}).get("inode"), name)

    def test_the_identity_parameter_is_OPTIONAL_so_a_CALLER_may_supply_it(self):
        """The property that makes the path an ALIAS wearing a tag's costume, in the
        owner ruling's own terms: today the caller can hand the system its identity.

        [EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]
        ASSERTED: the `inode` parameter is `optional` on all three minting ops, so a CALLER
        could hand the system the identity of the thing it was founding. That is the property
        the owner's ruling named as the defect's root.
        SUPERSEDED (EP-28S): the parameter is GONE. Not `required`, not refused — removed, and
        `inode` dropped from `payload_from`, so a caller's value is silently discarded on the
        way to the record.
        REMAINS TRUE and STILL DRIVEN against the pinned founding: the door WAS open, and this
        is the estate's driven record of it. AND THE CLOSURE IS ASSERTED BESIDE IT, which is
        the half that matters going forward — a caller can no longer name what an act founds,
        because there is no parameter to name it with."""
        with open(self.pre_law_pack(), encoding="utf-8") as f:
            pack = json.load(f)
        seen = 0
        for s in pack["steps"]:
            for r in s["records"]:
                if (r.get("action") == "CREATE-OP"
                        and (r.get("payload") or {}).get("name") in MINTING_OPS):
                    params = r["payload"]["definition"]["params"]
                    self.assertEqual(params.get("inode"), "optional")
                    seen += 1
        self.assertEqual(seen, 3, "non-vacuity: all three minting ops were read")
        # AND TODAY: no such parameter exists on any of the three.
        with open(FOUNDING_PATH, encoding="utf-8") as f:
            live = json.load(f)
        for s in live["steps"]:
            for r in s["records"]:
                if (r.get("action") == "CREATE-OP"
                        and (r.get("payload") or {}).get("name") in MINTING_OPS):
                    d = r["payload"]["definition"]
                    self.assertIsNone((d.get("params") or {}).get("inode"),
                                      "the caller's door is open again")
                    self.assertNotIn("inode", d.get("payload_from") or [])

    def test_the_FOLD_keys_on_the_payload_identity_at_custody_apply(self):
        """The consumer, located structurally. This is the site a landing must reach and
        the site D4 does not name."""
        _src, _fn, body = _custody_apply()
        self.assertIn('p.get("inode")', body,
                      "the fold reads the identity out of the record's payload")

    def test_NEAR_MISS_the_locator_picks_the_FOLD_and_not_its_namesake(self):
        """§A64: `LockTable.apply` has the same signature and also reads `p.get("inode")`,
        so an argument-keyed walk would pass this class's rows while pointing at the wrong
        class. The locator is class-keyed, and this holds it so."""
        _src, fn, body = _custody_apply()
        self.assertIn("CUSTODY_ACTIONS", body,
                      "the fold's own action set — LockTable.apply reads LOCK_ACTIONS")
        self.assertNotIn("LOCK_ACTIONS", body)

    def test_the_RECORD_already_holds_a_stable_coordinate_and_it_is_seq(self):
        """D1's derivation, resolved against the code rather than taken from the EP:
        `seq` is minted at append and never supplied."""
        with open(STORE_PATH, encoding="utf-8") as f:
            src = f.read()
        self.assertIn('"seq": len(self.events) + 1', src,
                      "minted at append (store.py:810)")
        self.assertIn("A seq is a LOCATION; the record is the content", src,
                      "and the estate had already written this pass's own sentence")

    def test_seq_is_UNIQUE_and_CONTIGUOUS_over_a_driven_world(self):
        d = tempfile.mkdtemp(prefix="ep28p-seq-")
        try:
            w = _World(d)
            w.act("FILE-CREATE", path="/a")
            w.act("FILE-CREATE", path="/b")
            seqs = [e["seq"] for e in w.store.all()]
            self.assertGreater(len(seqs), 0)
            self.assertEqual(seqs, list(range(1, len(seqs) + 1)))
            self.assertEqual(len(set(seqs)), len(seqs))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_the_ORDINAL_PROPERTY_is_NAMED_AS_LAW_and_not_relied_on(self):
        """D1a's named property: a formal name LEAKS CREATION ORDER, so any comparison of
        formal names acquires an accidental ordering. NAMED AS LAW: no comparison of formal
        names is licensed. This row holds the property so the successor pass meets it."""
        a, b = _formal_name_of(1), _formal_name_of(2)
        self.assertLess(a, b, "the ordering EXISTS — which is exactly the hazard")
        self.assertEqual(b - a, 1, "and it is arithmetically adjacent, which is worse")


class TestTheCITATIONSResolve(unittest.TestCase):
    """A CITATION IN A DOCSTRING IS PROSE AND PROSE ROTS SILENTLY, so the citations this
    pass depends on are resolved mechanically.

    THE ONE THAT DOES NOT RESOLVE: `render_bind`. It is cited in SHIPPED SOURCE
    (`custody.py:749`) and twice in `planning/exec/EP-28P.md` (`:274`, `:339`, the second
    calling it "the `render_bind` refusal precedent" and building W2b's acceptance on it).
    THERE IS NO SUCH FUNCTION ANYWHERE IN THE TREE. The refusal it names is REAL and lives
    in `custody.apply`; only the name is wrong. Held here so the next reader is not sent
    looking for a function that has never existed."""

    def test_render_bind_DOES_NOT_EXIST_anywhere_in_the_estate(self):
        found = []
        for root, dirs, files in os.walk(REPO):
            dirs[:] = [d for d in dirs if d not in
                       ("archive", "reference", ".git", "__pycache__", "node_modules")]
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(root, fn)
                # CLOSED EXPLICITLY, and it is not tidiness: a bare `open(...).read()`
                # here emits one ResourceWarning per file into a suite whose OWN named
                # hazard is ResourceWarning noise eating `Ran N`/`OK` lines. A row that
                # adds 159 of them to the arm it is measured in is a row damaging its
                # own instrument.
                try:
                    with open(p, encoding="utf-8") as fh:
                        tree = ast.parse(fh.read())
                except (SyntaxError, UnicodeDecodeError):
                    continue
                for n in ast.walk(tree):
                    if isinstance(n, ast.FunctionDef) and n.name == "render_bind":
                        found.append(os.path.relpath(p, REPO))
        self.assertEqual(found, [],
                         "if this ever reds, render_bind was WRITTEN and this row retires")

    def test_the_REAL_refusal_it_names_DOES_exist_and_is_in_the_fold(self):
        """The can-fail half: the row above must not pass because the search is broken."""
        with open(CUSTODY_PATH, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("UnrenderableIdentity(", src)
        self.assertIn("both render to", src,
                      "the collision refusal is in `custody.apply`, not in a `render_bind`")
        # and the search instrument CAN find a function when one is there
        tree = ast.parse(src)
        names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        self.assertIn("render_ino", names, "the walker finds functions that exist")
        self.assertNotIn("render_bind", names)


if __name__ == "__main__":
    unittest.main()
