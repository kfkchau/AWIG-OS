# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (mount, served state, replay, record fold, content hash). NON-GOAL: no offensive
# capability of any kind — this compares the LIVE served state to the state REBUILT from the record
# alone and asserts they are equal (the view->record direction). It drives no attack and, per archi
# P3, plants its positive AT THE COMPARISON, never by producing an unrecorded byte through the
# adapter. Full declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I2 [HIGH] — THE LIVE-vs-REPLAY DIFFERENTIAL.

"A record can be wrong while every view is right." (the estate's own front-door item.) Every guard
here runs record->view; nothing looks the other way. This instrument does:

    LIVE snapshot     the served state, read by driving the mount's own FUSE ops (readdir, getattr,
                      read, readlink, listxattr) — what a reader actually sees.
    REPLAY snapshot   the state rebuilt from the append-only record + content-addressed blobs ALONE
                      (bridge.replay_snapshot, READ not edited) — what the record says is there.

For every scenario the two MUST be EQUAL: a served byte with no record behind it (the view->record
defect) shows as a divergence. The mount is driven in-process (bridge.build_mount returns the ops
object the tests and the harness's replay adapter both drive — nothing exercises a differently-
composed mount than the one that runs).

PLANTED POSITIVE (archi P3 — planted AT THE COMPARISON, never a real unrecorded byte): two equal
snapshots are taken, then ONE is mutated IN THE HARNESS (a flipped content hash; a phantom entry
the record never held) and the differ MUST report the divergence. The differential can fail without
the test manufacturing a real defect through the adapter.

B2 EDGE (RESOLVED, board :3495 — the dispatch's ":3491 raised" basis is superseded). The architect
RULED B2 at :3495: the keep-burst pin (test_ep25:279) STANDS, the read path serves the COMMITTED
content and never a refused burst, and a second/fresh reader sees no refused byte — GREEN under
direct_io. So this differential CONFIRMS the B2 fix rather than redding: a fresh-reader snapshot of
the served state EQUALS the record on the refused-write edge (no served byte without a record). The
refused burst is retryable only through its OWN writing descriptor (POSIX un-fsynced read); a fresh
reader gets committed content. The test below measures both and asserts exactly that. (Named in the
close: my dispatch cited :3491 "B2 raised"; the code I find has B2 resolved by :3495 — a plan/code
conflict logged and raised, not improvised around.)
"""

import hashlib
import os
import stat as statmod
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.expanduser("~/gov-lab"))                 # the staged fusepy adapter

from bridge import replay_snapshot                                  # noqa: E402  READ only

try:
    from fuse import FuseOSError                                    # noqa: E402
    from bridge.mount import build_mount                            # noqa: E402
    FUSEPY = None
except ImportError as exc:                                          # pragma: no cover
    FuseOSError = None
    build_mount = None
    FUSEPY = str(exc)


# ---- the LIVE snapshot: read the served state by driving the mount's own ops -----------------

def live_snapshot(fs, root="/"):
    """Walk the mount by its FUSE ops (the reader's own path) into replay_snapshot's shape:
    {relpath: {type, perm, nlink, size, sha256|target}}."""
    out = {}
    prefix = "/" if root == "/" else root.rstrip("/") + "/"

    def walk(path):
        for name in fs.readdir(path, None):
            if name in (".", ".."):
                continue
            child = (path.rstrip("/") + "/" + name) if path != "/" else "/" + name
            attr = fs.getattr(child)
            mode = attr["st_mode"]
            rel = child[len(prefix):] if child.startswith(prefix) else child.lstrip("/")
            entry = {"perm": oct(statmod.S_IMODE(mode)), "nlink": attr["st_nlink"]}
            if statmod.S_ISDIR(mode):
                entry["type"] = "dir"
                out[rel] = entry
                walk(child)
            elif statmod.S_ISLNK(mode):
                entry["type"] = "lnk"
                entry["target"] = fs.readlink(child)
                out[rel] = entry
            else:
                entry["type"] = "reg"
                fh = fs.open(child, os.O_RDONLY)
                try:
                    data = fs.read(child, attr["st_size"] or (1 << 20), 0, fh)
                finally:
                    fs.release(child, fh)
                data = data or b""
                entry["size"] = len(data)
                entry["sha256"] = hashlib.sha256(data).hexdigest()[:16]
                out[rel] = entry

    walk(root)
    return out


def compare_snapshots(live, replay):
    """The differential (a pure function over two state dicts). Returns a list of divergences —
    empty means the served state and the record's rebuilt state AGREE."""
    divergences = []
    for path in sorted(set(live) | set(replay)):
        a, b = live.get(path), replay.get(path)
        if a is None:
            divergences.append(("in-record-not-served", path, None, b))
        elif b is None:
            divergences.append(("served-not-in-record", path, a, None))     # a served byte the record lacks
        elif a != b:
            divergences.append(("differs", path, a, b))
    return divergences


@unittest.skipIf(FUSEPY, "the fusepy adapter is not importable: %s" % FUSEPY)
class _Mount(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "rec.jsonl")
        self.blobdir = os.path.join(self.dir, "blobs")
        self.fs, self.store, self.gate, self.views, self.blobs = build_mount(self.record, self.blobdir)

    def _write(self, path, data, perm=0o644):
        fh = self.fs.create(path, perm)
        self.fs.write(path, data if isinstance(data, bytes) else data.encode(), 0, fh)
        self.fs.flush(path, fh)
        self.fs.release(path, fh)

    def _both(self, root="/"):
        return live_snapshot(self.fs, root), replay_snapshot.snapshot(self.record, self.blobdir, root=root)


class TestI2LiveEqualsReplay(_Mount):

    def test_flat_tree_round_trips_equal(self):
        self._write("/a", b"alpha")
        self._write("/b", b"bravo bytes here")
        self.fs.mkdir("/d", 0o755)
        self._write("/d/c", b"under a dir")
        live, replay = self._both()
        self.assertEqual(compare_snapshots(live, replay), [],
                         "the served state and the record-rebuilt state diverge")

    def test_symlink_and_binary_round_trip_equal(self):
        self._write("/bin", b"\x00\x01\x02\xff\xfe binary")
        self.fs.symlink("/link", "/bin")            # symlink(link_path, points_to): /link -> /bin
        live, replay = self._both()
        self.assertEqual(compare_snapshots(live, replay), [])

    def test_the_differential_is_not_vacuous(self):
        # a real, non-empty tree actually compared (guards against "equal because both empty").
        self._write("/x", b"content")
        live, replay = self._both()
        self.assertIn("x", live)
        self.assertIn("x", replay)
        self.assertEqual(compare_snapshots(live, replay), [])


class TestI2PlantedPositive(_Mount):

    def test_planted_divergence_at_the_comparison_fires(self):
        # archi P3: plant AT THE COMPARISON. Take two equal snapshots, then corrupt ONE copy in
        # the harness — NEVER produce a real unrecorded byte through the adapter — and assert the
        # differ reports it.
        self._write("/f", b"the served bytes")
        live, replay = self._both()
        self.assertEqual(compare_snapshots(live, replay), [])          # equal to begin with
        # (a) a served byte with no record behind it: add a phantom to the LIVE copy
        tampered = dict(live)
        tampered["ghost"] = {"type": "reg", "perm": "0o644", "nlink": 1, "size": 3,
                             "sha256": "deadbeefdeadbeef"}
        d = compare_snapshots(tampered, replay)
        self.assertTrue(any(kind == "served-not-in-record" and p == "ghost" for kind, p, *_ in d),
                        "the differ missed a served byte with no record behind it")
        # (b) a flipped content hash on an existing file
        tampered2 = {k: dict(v) for k, v in live.items()}
        tampered2["f"]["sha256"] = "0000000000000000"
        d2 = compare_snapshots(tampered2, replay)
        self.assertTrue(any(kind == "differs" and p == "f" for kind, p, *_ in d2),
                        "the differ missed a flipped content hash — it cannot fail")


class TestI2B2Edge(_Mount):

    def test_refused_write_is_not_a_served_byte_to_a_fresh_reader(self):
        # MEASURE the B2 edge (RESOLVED :3495) — the differential CONFIRMS the fix. A refused write's
        # burst is visible to ITS OWN descriptor (a process reads its own un-fsynced buffer — POSIX,
        # the test_ep25:279 keep-burst pin), but a FRESH reader sees the committed content, so the
        # differential (a fresh-reader read vs the record) AGREES — no served byte without a record.
        import os as _os
        self._write("/f", b"OLD-COMMITTED-CONTENT")
        self.store._append({
            "actor": "SYSTEM", "action": "CREATE-RULE", "object": "NO-WRITE-STANDING",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "NO-WRITE-STANDING", "polarity": "-",
                        "when": [{"action": "FILE-WRITE"}], "then": [{"refuse": "NO-WRITE-STANDING"}]}})
        fh = self.fs.open("/f", _os.O_RDWR)
        self.fs.write("/f", b"REFUSED-BYTES-XX", 0, fh)
        # the SAME descriptor reads its own dirty buffer (POSIX un-fsynced read) — disclosed:
        self.assertIn(b"REFUSED", self.fs.read("/f", 1 << 20, 0, fh))
        with self.assertRaises(FuseOSError):
            self.fs.flush("/f", fh)
        # the differential (fresh-reader served state vs the record) AGREES — no served byte
        # without a record. This is the truthful reading; the B2 raise is a writing-descriptor
        # semantics question, not a view->record leak the differential surfaces.
        live, replay = self._both()
        self.assertEqual(compare_snapshots(live, replay), [],
                         "an unexpected view->record divergence appeared on the refused-write edge "
                         "— if this reds, the refused burst IS being served to a fresh reader (B2), "
                         "and the close's disclosure must be revised")


if __name__ == "__main__":
    unittest.main()
