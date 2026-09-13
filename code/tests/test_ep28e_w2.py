# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28E W2 — the two reads made to cost their answers, proven CORRECT and proven DERIVED.

The speed property is in `test_ep28e.py` (the namespace walk is gone) and in
`test_ep28e_w3.py` (the cost is the dependency). This file carries the two things that
decide whether the change is lawful at all, which is a different question from whether it
is fast:

  1. CORRECTNESS — the indexed reads answer exactly what the scanning reads answered, over
     a mutation walk that exercises every action that binds or unbinds a name. The scanning
     implementations live HERE, in the test, and never in `src/`: EP-24C's rule is one
     implementation with a varied source, never two that could diverge in logic.

  2. DERIVED, NOT CACHED — the distinction EP-28E's plan names as its wrong reference. A
     cache holds an ANSWER and must be invalidated; there is no invalidation anywhere in
     this change, and the test ADDENDUM 1 §1.3 sets is kill-it-and-replay. That test was
     already in the suite (`test_ep25.py::test_the_custody_fold_itself_is_killable_and_
     rebuilds_identically`) and now covers the indexes because they are in `snapshot()`.
     What is added here is the half that test cannot see: that a divergence in the indexes
     is REPORTED and HALTS, rather than being detected and silently dropped.

THE HAZARD IN 2 WAS REAL AND IS FIXED IN THIS EP. `shadow_diff` compared the snapshots for
equality and then built its human-readable difference from a HAND-LIST of keys — `names` and
`inodes`. Adding keys to the snapshot without touching that list would have made a
divergence in the new keys fail the equality test, produce an EMPTY difference list, and
`_shadow_check`'s `if diff:` would then not have halted the mount. Detected and not
reported is worse than not detected: the counter says a check ran. The keys are now read off
the snapshot itself, and the two rows below are why that is not merely tidier.
"""

import os
import random
import re
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
# 1. CORRECTNESS — the differential against the reads that were replaced
# =====================================================================================
def _scanning_children(state, path):
    """`CustodyState.children` as it stood before EP-28E W2, verbatim in behaviour."""
    path = custody._norm(path)
    return sorted(custody.basename(c) for c in state.names
                  if c != path and custody.parent_of(c) == path)


def _scanning_path_of(state, ino):
    """`CustodyState.path_of` as it stood before EP-28E W2, verbatim in behaviour."""
    for path, i in state.names.items():
        if i == ino:
            return path
    return None


#: WHAT EACH `path_of` CALLER ACTUALLY SERVES, expressed so the differential can compare the
#: served answer under either implementation. These mirror `kernel_port._fill_readdir`,
#: `kernel_port._fill_lookup` and `CustodyState.nlink` — the only three callers in the estate
#: — reduced to the part that depends on WHICH path came back.
def _served_readdir(state, ino, resolve):
    path = resolve(state, ino)
    return None if path is None else state.children(path)


def _served_lookup_parent(state, ino, resolve):
    ppath = resolve(state, ino)
    if ppath is None:
        return None
    node = state.lookup(custody._norm(ppath.rstrip("/") + "/probe-name"))
    return None if node is None else node.snapshot()


def _served_nlink(state, ino, resolve):
    node = state.inodes.get(ino)
    if node is None or node.kind != custody.KIND_DIR:
        return state.nlink(ino)
    path = resolve(state, ino)
    return 2 + sum(1 for c, i in state.names.items()
                   if custody.parent_of(c) == path
                   and state.inodes.get(i) is not None
                   and state.inodes[i].kind == custody.KIND_DIR)


def _mutation_walk(seed=20260731, steps=400):
    """A record sequence that exercises every action which binds or unbinds a name.

    Deterministic from a seed, because a differential that cannot be re-run on the failing
    sequence reports a divergence nobody can reproduce. Every action `CUSTODY_ACTIONS` lists
    that touches the namespace appears: create, mkdir, symlink, link, unlink, rmdir, rename
    — including the two shapes with the awkward semantics, a rename ONTO AN OCCUPIED NAME
    and a rename onto ITSELF, which are where a naive index and the old scan part company.
    """
    rng = random.Random(seed)
    recs = [{"action": "FILE-MKDIR", "record_time": 1.0,
             "payload": {"path": "/", "inode": 1, "perm": "755"}}]
    live_dirs, live_files, ino = ["/"], [], 2
    for _ in range(steps):
        pick = rng.random()
        parent = rng.choice(live_dirs)
        base = "n%d" % ino
        path = custody._norm(parent.rstrip("/") + "/" + base)
        if pick < 0.30:
            recs.append({"action": "FILE-CREATE", "record_time": 1.0,
                         "payload": {"path": path, "inode": ino, "perm": "644"}})
            live_files.append(path)
            ino += 1
        elif pick < 0.48:
            recs.append({"action": "FILE-MKDIR", "record_time": 1.0,
                         "payload": {"path": path, "inode": ino, "perm": "755"}})
            live_dirs.append(path)
            ino += 1
        elif pick < 0.56:
            recs.append({"action": "FILE-SYMLINK", "record_time": 1.0,
                         "payload": {"path": path, "inode": ino, "perm": "777",
                                     "target": "/wherever"}})
            live_files.append(path)
            ino += 1
        elif pick < 0.68 and live_files:
            src = rng.choice(live_files)
            recs.append({"action": "FILE-LINK", "record_time": 1.0,
                         "payload": {"target_path": src, "new_path": path}})
            live_files.append(path)
        elif pick < 0.78 and live_files:
            gone = live_files.pop(rng.randrange(len(live_files)))
            recs.append({"action": "FILE-UNLINK", "record_time": 1.0,
                         "payload": {"path": gone}})
        elif pick < 0.84 and len(live_dirs) > 1:
            gone = live_dirs.pop(rng.randrange(1, len(live_dirs)))
            recs.append({"action": "FILE-RMDIR", "record_time": 1.0,
                         "payload": {"path": gone}})
        elif live_files:
            src = rng.choice(live_files)
            if pick < 0.90:
                dst = src                                   # RENAME ONTO ITSELF
            elif pick < 0.95 and len(live_files) > 1:
                dst = rng.choice([f for f in live_files if f != src])   # ONTO AN OCCUPIED NAME
                live_files.remove(dst)
            else:
                dst = path
            recs.append({"action": "FILE-RENAME", "record_time": 1.0,
                         "payload": {"path": src, "new_path": dst}})
            if dst != src:
                live_files.remove(src)
                live_files.append(dst)
    return recs


class TestTheIndexedReadsAnswerWhatTheScanAnswered(unittest.TestCase):

    def test_the_differential_over_a_mutation_walk(self):
        """T-W2-DIFFERENTIAL. The indexed read against the scanning read it replaced, for
        every directory and every inode in the world, after every record."""
        recs = _mutation_walk()
        state = custody.CustodyState()
        compared = 0
        for n, e in enumerate(recs):
            state.apply(e)
            if n % 17 and n != len(recs) - 1:
                continue                       # every seventeenth record, and the last
            for path in list(state.names) + ["/", "/nonexistent"]:
                self.assertEqual(state.children(path), _scanning_children(state, path),
                                 "children diverged at record %d for %r" % (n, path))
                compared += 1
            for ino in list(state.inodes) + [max(state.inodes) + 5000]:
                # `path_of` is compared AS ITS CALLERS SEE IT, not raw. The two
                # implementations legitimately differ on which of a hard-linked file's names
                # comes back — see `test_the_tie_break_is_reachable_and_unobservable` — so
                # comparing the raw helper would assert a property the change does not have
                # and never needed. What every caller needs is that the ANSWER IT SERVES is
                # the same, and that is what is compared.
                for served in (_served_readdir, _served_lookup_parent, _served_nlink):
                    self.assertEqual(served(state, ino, custody.CustodyState.path_of),
                                     served(state, ino, _scanning_path_of),
                                     "%s diverged at record %d for inode %r"
                                     % (served.__name__, n, ino))
                    compared += 1
        self.assertGreater(compared, 2000,
                           "the walk compared only %d answers, which is not a differential"
                           % compared)

    def test_the_differential_can_fail(self):
        """T-W2-DIFFERENTIAL-CAN-FAIL. The row above is an equality between two functions,
        and it would also hold if both were broken the same way. One binding is dropped from
        the index behind the fold's back and the differential is required to catch it."""
        state = custody.fold(_mutation_walk(steps=60))
        victim = next(p for p in state.names if p != "/")
        parent = custody.parent_of(victim)
        state.kids[parent].pop(custody.basename(victim))
        self.assertNotEqual(state.children(parent), _scanning_children(state, parent),
                            "a binding removed from the index did not change what the "
                            "indexed read answered, so the differential proves nothing")

    def test_path_of_is_exact_for_every_directory_and_a_real_name_for_a_hard_link(self):
        """THE TIE-BREAK, stated as a property instead of as a docstring claim.

        `path_of` returns the FIRST name an inode was bound under; the scan returned the
        first in `names` key order. For a DIRECTORY the two are the same answer because a
        directory has exactly one name. For a hard-linked FILE the guarantee is weaker and
        is asserted as the weaker thing it is: the answer is one of the inode's actual
        names."""
        state = custody.fold(_mutation_walk())
        for ino, node in state.inodes.items():
            answer = state.path_of(ino)
            if answer is None:
                self.assertNotIn(ino, set(state.names.values()))
                continue
            self.assertEqual(state.names.get(answer), ino,
                             "path_of returned %r, which is not bound to inode %r"
                             % (answer, ino))
            if node.kind == custody.KIND_DIR:
                self.assertEqual(answer, _scanning_path_of(state, ino),
                                 "path_of and the scan disagree on a DIRECTORY, where they "
                                 "must agree because a directory has one name")

    def test_the_tie_break_is_reachable_and_unobservable(self):
        """THE HONEST EDGE, and the first version of this row got it WRONG.

        It asserted that the two orders could only be made to differ by a `FILE-LINK` onto an
        occupied name, which the port refuses with EEXIST — so the divergence was
        unreachable. The differential above then produced one anyway, at record 255 of its
        walk. The reachable route is `FILE-RENAME` over an existing FILE, which is ordinary
        POSIX and permitted: hard-link a file to a fresh name, then rename that name over
        another existing name, and the destination's path key is REUSED — it keeps its old
        position in `names` while its binding is new.

        SO THE CLAIM MOVES TO WHERE IT IS TRUE. The divergence is reachable through the gate,
        and NO CALLER CAN SEE IT: this row builds the divergence through the real port,
        confirms the two implementations disagree about which name comes back, and requires
        every one of the three callers to serve the same answer either way."""
        work = tempfile.mkdtemp(prefix="ep28e-w2-")
        self.addCleanup(shutil.rmtree, work, True)
        os.makedirs(os.path.join(work, "blobs"), exist_ok=True)
        rec = os.path.join(work, "rec.jsonl")
        open(rec, "w").close()
        store, gate, views, blobs = build_brain(rec, os.path.join(work, "blobs"))
        port = KernelPort(store, gate, views, blobs)

        def req(op, **kw):
            f = {"id": "1", "op": op, "class": "DECISION", "uid": "0", "gid": "0",
                 "pid": str(os.getpid())}
            f.update({k: str(v) for k, v in kw.items()})
            return port.handle(f, b"")[0]

        # /a first, so its key sits EARLIER in `names` than /z's.
        self.assertEqual(req("FILE-CREATE", path="/a", perm="644"), 0)
        self.assertEqual(req("FILE-CREATE", path="/z", perm="644"), 0)
        self.assertEqual(req("FILE-LINK", target_path="/z", new_path="/m"), 0)
        self.assertEqual(req("FILE-RENAME", path="/m", new_path="/a"), 0,
                         "a rename over an existing FILE was refused, so this route is not "
                         "the reachable one after all and the edge needs re-deriving")
        state = port.state
        ino = state.names["/z"]
        self.assertEqual(state.names["/a"], ino, "the rename did not land on /a")

        # THE DIVERGENCE, REAL AND THROUGH THE GATE.
        self.assertEqual(state.path_of(ino), "/z")
        self.assertEqual(_scanning_path_of(state, ino), "/a")

        # AND UNOBSERVABLE AT EVERY CALLER.
        for served in (_served_readdir, _served_lookup_parent, _served_nlink):
            with self.subTest(caller=served.__name__):
                self.assertEqual(served(state, ino, custody.CustodyState.path_of),
                                 served(state, ino, _scanning_path_of),
                                 "the tie-break IS observable through %s, so it has to be "
                                 "preserved rather than declared harmless" % served.__name__)

        # AND A DIRECTORY NEVER HAS THE TIE AT ALL — the reason the three real callers, which
        # all pass directory inodes, are safe by construction rather than by coincidence.
        import errno
        self.assertEqual(req("FILE-MKDIR", path="/d", perm="755"), 0)
        dino = state.names["/d"]
        self.assertEqual(req("FILE-LINK", target_path="/d", new_path="/d2"), -errno.EPERM,
                         "a hard link to a DIRECTORY was permitted, so a directory can have "
                         "two names and path_of's tie-break reaches the real callers")
        self.assertEqual([p for p, i in state.names.items() if i == dino], ["/d"])


# =====================================================================================
# 2. DERIVED, NOT CACHED — no invalidation, one door, and a divergence that HALTS
# =====================================================================================
class TestTheIndexesAreDerivedState(unittest.TestCase):

    def test_the_namespace_has_exactly_one_door(self):
        """T-W2-ONE-DOOR. The indexes cannot rot if a name can only enter or leave through
        the two functions that maintain all three structures together. Enforcement at the
        chokepoint, checked the way this estate checks it: a count of something absent.

        Read as text because a route that does not exist is easier to prove absent than one
        that is merely unused today — the `test_ep25.py` precedent, and the same reason
        EP-01 counts `store.append(` outside the gate."""
        src = (REPO / "src" / "bridge" / "custody.py").read_text(encoding="utf-8")
        body = src.split("def _bind", 1)[1]
        inside, outside = body.split("# ---- the one fold body", 1)
        for pattern, what in ((r"self\.names\[[^]]+\]\s*=", "an assignment into names"),
                              (r"self\.names\.pop\(", "a pop from names"),
                              (r"self\.kids\.setdefault|self\.kids\[[^]]+\]\s*=", "a write to kids"),
                              (r"self\.paths\.setdefault|self\.paths\[[^]]+\]\s*=", "a write to paths")):
            with self.subTest(route=what):
                self.assertTrue(re.search(pattern, inside),
                                f"{what} is not inside the door, so this row is looking in "
                                "the wrong place")
                self.assertIsNone(re.search(pattern, outside),
                                  f"{what} happens outside `_bind`/`_unbind` — the indexes "
                                  "can now disagree with the namespace")

    def test_nothing_here_invalidates_anything(self):
        """The wrong reference, checked as an ABSENCE in the shipped module rather than
        assessed as a judgement. A cache is a thing that needs invalidating; if there is no
        invalidation, the question of whether the invalidation is correct cannot arise."""
        src = (REPO / "src" / "bridge" / "custody.py").read_text(encoding="utf-8")
        code = "\n".join(l for l in src.splitlines()
                         if not l.lstrip().startswith("#"))
        for token in ("lru_cache", "@cache", "functools", "_memo", "invalidate", "dirty",
                      "stale"):
            self.assertNotIn(token, code,
                             "the custody fold contains %r — if this change acquired a "
                             "cache, it is the wrong reference this EP names" % token)

    def test_killing_the_indexes_and_replaying_reproduces_them_identically(self):
        """ADDENDUM 1 §1.3's own test, stated here explicitly even though `test_ep25.py`
        already runs it on the whole snapshot: if it reproduces identically it is derived
        state, and if it does not it is a cache and it is refused."""
        recs = _mutation_walk()
        served = custody.fold(recs)
        killed = {"kids": served.kids, "paths": served.paths}
        served.kids, served.paths = {}, {}
        replayed = custody.fold(recs)
        self.assertEqual(killed["kids"], replayed.kids)
        self.assertEqual(killed["paths"], replayed.paths)
        self.assertNotEqual(replayed.kids, {},
                            "the replayed world has no index at all, so this row compared "
                            "two empty structures")


class TestADivergenceInTheIndexesHaltsTheMount(unittest.TestCase):
    """THE HAZARD THIS EP FOUND AND FIXED, as a regression test.

    Before the fix, `shadow_diff` built its difference from a hand-list of snapshot keys. A
    divergence in a key outside that list made the snapshots unequal, produced an EMPTY
    difference, and `_shadow_check`'s `if diff:` did not halt. The mount kept serving while
    its own counter recorded that a check had run."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="ep28e-w2-fs-")
        self.addCleanup(shutil.rmtree, self.work, True)
        os.makedirs(os.path.join(self.work, "blobs"), exist_ok=True)
        rec = os.path.join(self.work, "rec.jsonl")
        open(rec, "w").close()
        from bridge.records_fs import RecordsFS
        store, gate, views, blobs = build_brain(rec, os.path.join(self.work, "blobs"))
        self.fs = RecordsFS(store, gate, views, blobs)
        self.fs.mkdir("/d", 0o755)
        self.fs.create("/d/a", 0o644)

    def test_a_clean_world_diverges_in_nothing(self):
        self.assertIsNone(self.fs.shadow_diff(),
                          "the world diverged before anything was corrupted")

    def test_each_index_divergence_is_reported_and_halts(self):
        for key, corrupt in (
            ("kids", lambda st: st.kids["/d"].pop("a")),
            ("paths", lambda st: st.paths.pop(st.names["/d/a"])),
        ):
            with self.subTest(snapshot_key=key):
                self.setUp()
                corrupt(self.fs.state)
                diff = self.fs.shadow_diff()
                self.assertTrue(diff,
                                f"a divergence in {key} made the snapshots unequal and "
                                "produced NO reported difference — which is the hazard: "
                                "`_shadow_check` would not have halted")
                self.assertTrue(any(d.startswith(key) for d in diff),
                                f"the divergence was reported without naming {key}: {diff}")
                self.fs.halted = False
                self.fs._acts, self.fs.shadow_every = 0, 1
                self.assertTrue(self.fs._shadow_check(), "the check reported nothing")
                self.assertTrue(self.fs.halted,
                                f"a divergence in {key} did not halt the mount")

    def test_the_diff_enumerates_the_snapshot_rather_than_a_hand_list(self):
        """The fix's own property. A snapshot key nobody listed must still be compared, so
        the next key added to the comparable shape cannot be silently unreported.

        THE VEHICLE DISTINGUISHES THE TWO OBJECTS BY CONSTRUCTION [EP-28H item 4, the
        re-homed EP-28F W6, 2026-08-02]. REFUTED VEHICLE, RETAINED: the injected value used
        to be `{"x": id(self_) % 7}` — a MEMORY ADDRESS, which carries a 1-in-7 collision
        floor by construction. When the two addresses landed in the same bucket the injected
        key was EQUAL on both sides, the snapshots compared equal, `shadow_diff` returned
        None on its early exit, and this row went red for a reason that has nothing to do
        with its subject. It was called stable-red on four measurements and then went green
        when twenty-one unrelated tests were added at EP-28F: the outcome was a function of
        heap layout and the four repetitions had varied nothing.

        The key NAME already does the row's real work — proving the diff loop enumerates the
        snapshot rather than a hand-list. Only the VALUE needs to differ, so it differs
        because it was built to: the counter below is one per call, so the two snapshot calls
        of one `shadow_diff` can never carry the same number, at any allocation, at either
        commit width."""
        real = custody.CustodyState.snapshot
        calls = []

        def snapshot_with_a_new_key(self_):
            out = real(self_)
            calls.append(self_)
            out["a_key_no_diff_loop_lists"] = {"x": len(calls)}
            return out

        custody.CustodyState.snapshot = snapshot_with_a_new_key
        try:
            diff = self.fs.shadow_diff()
        finally:
            custody.CustodyState.snapshot = real
        self.assertTrue(diff, "the snapshots differed and nothing was reported")
        self.assertTrue(any(d.startswith("a_key_no_diff_loop_lists") for d in diff),
                        "a divergence in an unlisted snapshot key was not reported: %r"
                        % diff)


if __name__ == "__main__":
    unittest.main()
