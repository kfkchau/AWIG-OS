"""EP-28T — the landing completed: the THIRD survival of the old regime, repaired LOUD.

WHAT THIS BATTERY HOLDS SHUT, stated once. Founding 1.18.0 (EP-28S) moved the three
minting ops to `mints_from: record_coordinate`: a birth act's own position in the record
names what it founds, and no birth record carries an identity any more. `CustodyState.apply`
was moved with it. `FilesView.tree` — the campaign-1 governed-core fold over the SAME
records — was not, and read

    present[p["path"]] = p.get("inode", p["path"])

so every birth under the new law silently fell back to PATH-AS-IDENTITY. The old regime did
not end at S; it MOVED, into a second fold nobody re-read, and it moved SILENTLY, which is
the worst of the three ways it could have survived: two folds over one record answering two
different identities, with no red anywhere, because the only consumers compare tree to tree.

THE REPAIR IS NOT A BETTER FALLBACK. There is no fallback left at this site. The identity is
DERIVED from the record exactly as `CustodyState.apply` derives it, through the one
implementation (`custody.formal_name`) rather than through a second copy of the arithmetic —
and a birth act whose coordinate is absent or unreadable REFUSES, loudly, through that same
door, citing its rule. The two cases cannot overlap: a record that NAMES an identity keeps
it (an act stands under the law of its deciding time), a record that names none is named by
its own coordinate.

WHAT THIS BATTERY DOES NOT REPAIR, and it is pinned here rather than described. The
`FILE-LINK` branch one line below carries the SAME shape —
`present.get(p["target_path"], p["target_path"])` — a silent path substitution when the link
names a target the fold has never seen. It is OFF-SEED: the EP's §1 names line 35 and the
mentor's one-line fence ruling covers that site, and repairing the link branch is not a
consequence of the directed work, it is work the instruction never directed. So it is
REPORTED, UNTOUCHED, and PINNED by a row here, so that a later ruling is checkable rather
than remembered. Its residual is derived and stated in that row.

Runs on this box: `python3 -m unittest discover -s tests -p 'test_ep28t.py'`.
"""

import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bridge.custody import (CustodyState, SEQ_FLOOR, UnparseableRecordValue,  # noqa: E402
                            UnrenderableIdentity, formal_name)
from kernel.blobs import BlobStore  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from subsystems.files import FilesView  # noqa: E402

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
FILES_PY = os.path.join(SRC, "subsystems", "files.py")
PROV = {"uid": 0, "gid": 0, "pid": 1, "window": "ep28t"}

#: THE REPAIRED SITE and THE SITE LEFT STANDING, as source text. Both are asserted, both
#: ways, by `TheOffSeedSiteIsPinnedRatherThanRemembered` below. This estate has lost a
#: shipped citation to prose rot inside a docstring; a pin that a test reads cannot rot.
OLD_BIRTH_FALLBACK = 'present[p["path"]] = p.get("inode", p["path"])'
LINK_FALLBACK = 'present.get(p["target_path"], p["target_path"])'


def read_source(path):
    """A file read that closes its handle. The estate has lost six `Ran N` lines to
    ResourceWarnings from instruments that leaked descriptors into their own subject."""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class _Records:
    """The smallest thing `FilesView.tree` folds: a record list and nothing else.

    It is a SOURCE, not a second implementation — the fold under test is the shipped one.
    Hand-built records are the only way to reach a birth act with no coordinate, because
    the store mints `seq` at every append and cannot produce one."""

    def __init__(self, events):
        self.events = list(events)

    def all(self, as_of=None):
        return [e for e in self.events
                if as_of is None or e.get("seq", 0) <= as_of]

    def by_action(self, action, as_of=None):
        return [e for e in self.all(as_of) if e["action"] == action]

    def action_set_projection(self, actions):
        # MAINT-K12-SUBSYSTEM-VIEWS: `FilesView.tree` now reads its family through the store's
        # config-keyed projection. This hand-built SOURCE emulates that one method faithfully —
        # the action-set filter, in record order, honouring as_of — so the fold under test is
        # still the shipped one reading these same hand-built records. The identity cases below
        # are UNCHANGED; only the store contract the fold reads through grew by one method.
        acts = frozenset(actions)
        outer = self

        class _Family:
            def all(self, as_of=None):
                return [e for e in outer.all(as_of) if e["action"] in acts]

        return _Family()


def birth(path, seq=None, inode=None):
    e = {"action": "FILE-CREATE", "record_time": 1.0, "payload": {"path": path}}
    if seq is not None:
        e["seq"] = seq
    if inode is not None:
        e["payload"]["inode"] = inode
    return e


class _GatedWorld(unittest.TestCase):
    """A world driven through the shipped gate, so every record here is one the estate
    actually produces. No record in this class is hand-built."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.record, blobs=self.blobs)
        self.fv = FilesView(self.store, self.blobs)


class TheBirthActIsNamedByItsOwnCoordinate(_GatedWorld):

    def test_a_birth_naming_no_identity_gets_its_COORDINATE_and_NEVER_its_PATH(self):
        """THE DIVERGENCE ROW. The fallback value and the true value cannot coincide —
        one is the path string, the other an integer in the formal-name band — so this row
        is red whenever a silent path substitution is answering in this fold, including one
        nobody knew was there. Red world exhibited in `TheRedWorld` below."""
        r = self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/x"})
        served = self.fv.tree()["/x"]
        self.assertIsInstance(served, int)
        self.assertEqual(served, formal_name(r["seq"]))
        self.assertNotEqual(served, "/x")
        self.assertGreaterEqual(served, SEQ_FLOOR)

    def test_THE_TWO_FOLDS_AGREE_the_governed_core_and_the_mount_answer_ONE_identity(self):
        """The estate has TWO folds over one record. Before this pass they answered two
        different identities for the same file and nothing was red, because no consumer
        compares them. This row compares them."""
        for p in ("/a", "/b", "/c"):
            self.gate.execute("FILE-CREATE", "SYSTEM", {"path": p})
        cs = CustodyState()
        for e in self.store.all():
            cs.apply(e)
        tree = self.fv.tree()
        for p in ("/a", "/b", "/c"):
            self.assertIn(p, tree)
            self.assertIn(p, cs.names)
            self.assertEqual(tree[p], cs.names[p],
                             "the two folds answer different identities for %s" % p)

    def test_A49_LEAST_LIKELY_create_unlink_recreate_gives_the_path_TWO_identities(self):
        """§A49, the least-likely member: the very defect the campaign exists to delete,
        seen in THIS view for the first time. Under path identity both births derive `/p`
        and the fold binds ONE identity for TWO files. Under the landed law each birth
        carries its own coordinate, so the second create is a different thing that happens
        to reuse a name."""
        first = self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/p"})
        after_first = self.fv.tree()["/p"]
        self.gate.execute("FILE-UNLINK", "SYSTEM", {"path": "/p"})
        self.assertNotIn("/p", self.fv.tree())
        second = self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/p"})
        after_second = self.fv.tree()["/p"]
        self.assertNotEqual(first["seq"], second["seq"])
        self.assertNotEqual(after_first, after_second,
                            "two births of one path derived ONE identity — the collision")
        self.assertEqual(after_first, formal_name(first["seq"]))
        self.assertEqual(after_second, formal_name(second["seq"]))

    def test_replay_from_the_record_alone_still_gives_the_SAME_tree(self):
        """The property the old regime was bought with, kept: identity is derived from the
        record and from nothing else, so a rebuild answers the same thing. Order-independence
        ACROSS worlds is what was traded away (W3); determinism WITHIN a world is not."""
        for p in ("/a", "/b"):
            self.gate.execute("FILE-CREATE", "SYSTEM", {"path": p})
        before = self.fv.tree()
        store2, _g2, _v2 = build_kernel(self.record)
        self.assertEqual(FilesView(store2, self.blobs).tree(), before)


class TheFallbackThatRemainsIsLOUD(unittest.TestCase):
    """`a record without an identity meets a stated, visible path` — EP-28T §1. There is no
    silent degradation left at this site: either the coordinate names the thing, or the fold
    refuses and says which record and why."""

    def test_a_birth_with_NO_identity_and_NO_coordinate_REFUSES(self):
        """MEASURED, NOT ASSUMED, AND THE FIRST TAKE OF THIS ROW WAS WRONG. An absent
        coordinate refuses through the module's PARSE door as `UnparseableRecordValue`, not
        as `UnrenderableIdentity` — the two are different refusals for different causes and
        this row names the one it actually gets."""
        fv = FilesView(_Records([birth("/x")]), None)
        with self.assertRaises(UnparseableRecordValue) as cm:
            fv.tree()
        self.assertIn("record coordinate", str(cm.exception))

    def test_a_birth_whose_coordinate_is_NOT_A_POSITION_REFUSES(self):
        """The other loud path, and it is a DIFFERENT class: the coordinate parses and then
        fails the band's own floor."""
        fv = FilesView(_Records([birth("/x", seq=0)]), None)
        with self.assertRaises(UnrenderableIdentity) as cm:
            fv.tree()
        self.assertIn("positions start at 1", str(cm.exception))

    def test_the_TWO_refusals_are_DISTINCT_classes_for_DISTINCT_causes(self):
        """Recorded because a single `except (A, B)` in a caller would hide which happened,
        and the two mean different things: `unreadable` versus `read and out of band`."""
        self.assertFalse(issubclass(UnparseableRecordValue, UnrenderableIdentity))
        self.assertFalse(issubclass(UnrenderableIdentity, UnparseableRecordValue))

    def test_NEAR_MISS_a_READABLE_coordinate_is_not_refused(self):
        """§A64, the other way: the loud path must not over-fire. One below the refusing
        value is admitted and derives."""
        fv = FilesView(_Records([birth("/x", seq=1)]), None)
        self.assertEqual(fv.tree()["/x"], SEQ_FLOOR + 1)

    def test_NEAR_MISS_a_record_that_NAMES_an_identity_KEEPS_it(self):
        """The two cases cannot overlap, and the discriminator is the RECORD'S OWN SHAPE.
        An act stands under the law of its deciding time: a pre-1.18.0 birth named its
        identity, so that identity is what named it, and today's law does not reach back and
        rename it."""
        fv = FilesView(_Records([birth("/a", seq=9, inode="/legacy")]), None)
        self.assertEqual(fv.tree()["/a"], "/legacy")

    def test_NEAR_MISS_an_identity_recorded_as_an_INTEGER_is_kept_as_that_INTEGER(self):
        """The least likely member of the same near-miss: a world recorded by the stamping
        FUSE port carries integer identities and they are NOT coordinates. `0` is the
        sharpest case — it is falsy, and a fold that tested truthiness rather than absence
        would silently re-name it."""
        fv = FilesView(_Records([birth("/a", seq=9, inode=0)]), None)
        self.assertEqual(fv.tree()["/a"], 0)


class TheRedWorld(unittest.TestCase):
    """EP-28D's law: a passing row proves nothing until the world in which it fails has been
    EXHIBITED — and the 2026-07-31 amendment: the red world names WHICH CLAUSE it makes fail
    and must be unreachable by every clause that already passed.

    THE CLAUSE UNDER TEST IS THE BIRTH-IDENTITY CLAUSE AND NOTHING ELSE. The world is built
    by taking the SHIPPED source and reverting THAT ONE EXPRESSION — one implementation, one
    varied thing. Nothing else in the module moves, so a red here is that clause going red."""

    #: The repaired clause, verbatim from the shipped file. Reverting exactly this and
    #: nothing else is what makes the exhibition attributable.
    REPAIRED_CLAUSE = ('identity = p.get("inode")\n'
                       '                if identity is None:\n'
                       '                    identity = formal_name(e.get("seq"))\n'
                       '                present[p["path"]] = identity')

    def _neutered_module(self):
        src = read_source(FILES_PY)
        self.assertEqual(src.count(self.REPAIRED_CLAUSE), 1,
                         "the repaired clause is not where this row thinks it is, so a red "
                         "below would be attributable to nothing")
        neutered = src.replace(self.REPAIRED_CLAUSE, OLD_BIRTH_FALLBACK)
        self.assertNotEqual(neutered, src, "the neutering substitution matched nothing")
        mod = types.ModuleType("files_pre_repair_ep28t")
        exec(compile(neutered, "<files.py reverted at the birth-identity clause>", "exec"),
             mod.__dict__)
        return mod

    def test_THE_RED_WORLD_the_pre_repair_clause_answers_the_PATH(self):
        mod = self._neutered_module()
        fv = mod.FilesView(_Records([birth("/x", seq=7)]), None)
        self.assertEqual(fv.tree()["/x"], "/x")          # the silent substitution, exhibited
        self.assertNotEqual(fv.tree()["/x"], SEQ_FLOOR + 7)

    def test_THE_RED_WORLD_the_pre_repair_clause_is_SILENT_where_the_repair_REFUSES(self):
        """The loud half of the same clause: with the repair reverted, a birth naming no
        identity and no coordinate does not refuse — it answers a path and says nothing.
        That silence is the defect, and this row is what makes it visible."""
        mod = self._neutered_module()
        fv = mod.FilesView(_Records([birth("/x")]), None)
        self.assertEqual(fv.tree()["/x"], "/x")

    def test_THE_RED_WORLD_leaves_every_OTHER_clause_of_the_fold_untouched(self):
        """The 2026-07-31 amendment's own test: prove the red world is not reachable by a
        clause that already passed. Unlink still removes; a named identity is still kept."""
        mod = self._neutered_module()
        fv = mod.FilesView(_Records([birth("/a", seq=1, inode="/legacy"),
                                     birth("/b", seq=2, inode="/other"),
                                     {"action": "FILE-UNLINK", "seq": 3,
                                      "payload": {"path": "/b"}}]), None)
        tree = fv.tree()
        self.assertEqual(tree["/a"], "/legacy")
        self.assertNotIn("/b", tree)


class TheOffSeedSiteIsPinnedRatherThanRemembered(unittest.TestCase):
    """RAISED, DERIVED TO ITS RESIDUAL, AND UNTOUCHED.

    WHAT IT IS. `FilesView.tree`'s `FILE-LINK` branch answers
    `present.get(p["target_path"], p["target_path"])` — when the link names a target this
    fold has never bound, it substitutes the TARGET PATH as the new name's identity. Same
    shape, same silence, one line below the site the EP names.

    WHAT IS ALREADY DERIVED, at zero evidence cost. (1) The definitive fold does NOT
    substitute: `CustodyState.apply`'s `FILE-LINK` branch binds only where the target is
    already bound, so the two folds disagree on exactly this branch. (2) The branch is
    UNREACHABLE through the gate — a `FILE-LINK` whose target is unbound is refused, which
    the row below MEASURES rather than argues. So this is the comforting-fallback shape the
    standard names three times: unreachable, and stale the moment the law moved.
    (3) The repair is one line and it is known: bind only where the target is bound.

    THE RESIDUAL, and it is the only thing outstanding: a fence ruling. The EP's §1 names
    line 35; this is off-seed, and the rule-fence form filed 2026-08-08 says an off-seed
    rule-meeting site is REPORTED, not auto-inside. Repairing it is not a consequence of the
    directed work — the directed work lands without it — so by the standard's own
    discriminator it is a fence question and it stops here.

    THESE TWO ROWS GO RED WHEN THE RULING LANDS AND THE SITE IS REPAIRED. That is the point
    of them: the record of an untouched, reported defect cannot rot into a forgotten one."""

    def test_PIN_the_FILE_LINK_branch_STILL_carries_a_target_path_fallback(self):
        self.assertIn(LINK_FALLBACK, read_source(FILES_PY))

    def test_NEAR_MISS_the_BIRTH_fallback_this_pass_DID_repair_is_GONE(self):
        """§A64 both ways on the same structural instrument: the pinned text is found, and
        the text this pass deleted is not. One assertion without the other proves only that
        the reader works."""
        self.assertNotIn(OLD_BIRTH_FALLBACK, read_source(FILES_PY))

    def test_the_gate_REFUSES_a_FILE_LINK_whose_target_is_absent(self):
        """The measurement behind claim (2) above. Driven, not reasoned."""
        d = tempfile.mkdtemp()
        blobs = BlobStore(os.path.join(d, "blobs"))
        _store, gate, _views = build_kernel(os.path.join(d, "record.jsonl"), blobs=blobs)
        with self.assertRaises(OpError):
            gate.execute("FILE-LINK", "SYSTEM",
                         {"target_path": "/gone", "new_path": "/n", "provenance": PROV})


if __name__ == "__main__":
    unittest.main()
