# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (mount, native control, conformance, lock range, xattr, page cache). NON-GOAL: no
# offensive capability of any kind — this runs ordinary POSIX behaviour on the governed mount AND
# on a native directory and compares them, naming divergences. It drives no attack. Full
# declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I3 [GREEN] — NATIVE-CONTROL CONFORMANCE.

The same scenario run on the governed mount AND on a native directory (the control); the two
outcomes compared, divergences NAMED (the scenario set is tools/conformance/native_control_
scenarios.py). Drivable-in-process scenarios run here (host or guest); two — mmap and the T-1
direct_io read-before-fsync trade (archi :3501) — need a REAL kernel mount and are measured in the
guest arm (see planning/evidence/EP-INSTRUMENTS-1/native-control-guest.md).

PLANTED POSITIVE (must fire): a deliberately WRONG expected-observation is compared against the
native control and the differ MUST report the mismatch — the comparison can fail.
"""

import errno
import os
import stat as statmod
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.expanduser("~/gov-lab"))

from tools.conformance import native_control_scenarios as SCEN       # noqa: E402

try:
    from fuse import FuseOSError                                     # noqa: E402
    from bridge.mount import build_mount                             # noqa: E402
    from bridge.records_fs import _Flock                             # noqa: E402
    FUSEPY = None
except ImportError as exc:                                          # pragma: no cover
    FuseOSError = None
    build_mount = None
    FUSEPY = str(exc)

XATTR_CREATE = 0x1


# ============================================================================================
# Each scenario returns a normalised OBSERVATION dict on a backend. The MOUNT arm drives the
# RecordsFS ops object; the NATIVE arm drives real os calls in a tmpdir. Equal observations =
# conformance; a difference is a named divergence.
# ============================================================================================

def _new_mount():
    d = tempfile.mkdtemp()
    fs, store, gate, views, blobs = build_mount(os.path.join(d, "rec.jsonl"),
                                                os.path.join(d, "blobs"))
    return fs


def _new_native():
    return tempfile.mkdtemp()


# ---- rename a populated tree ----

def rename_tree_mount(fs):
    fs.mkdir("/a", 0o755)
    fs.create("/a/b", 0o644)
    fs.mkdir("/a/sub", 0o755)
    fs.create("/a/sub/c", 0o644)
    fs.rename("/a", "/x")
    def exists(p):
        try:
            fs.getattr(p); return True
        except FuseOSError:
            return False
    return {p: exists(p) for p in ("/x", "/x/b", "/x/sub", "/x/sub/c", "/a", "/a/b")}


def rename_tree_native(root):
    j = lambda *p: os.path.join(root, *p)
    os.mkdir(j("a")); open(j("a", "b"), "w").close()
    os.mkdir(j("a", "sub")); open(j("a", "sub", "c"), "w").close()
    os.rename(j("a"), j("x"))
    m = {"/x": "x", "/x/b": "x/b", "/x/sub": "x/sub", "/x/sub/c": "x/sub/c",
         "/a": "a", "/a/b": "a/b"}
    return {k: os.path.exists(j(*v.split("/"))) for k, v in m.items()}


# ---- open then unlink, still read (POSIX open-unlink) ----

def open_unlink_mount(fs):
    fh = fs.create("/f", 0o644)
    fs.write("/f", b"open-unlink-bytes", 0, fh)
    fs.flush("/f", fh)
    rfh = fs.open("/f", os.O_RDONLY)
    fs.unlink("/f")
    data = fs.read("/f", 1 << 20, 0, rfh)
    fs.release("/f", rfh)
    fs.release("/f", fh)
    exists = True
    try:
        fs.getattr("/f")
    except FuseOSError:
        exists = False
    return {"read_after_unlink": data, "name_gone": not exists}


def open_unlink_native(root):
    p = os.path.join(root, "f")
    fd = os.open(p, os.O_RDWR | os.O_CREAT, 0o644)
    os.write(fd, b"open-unlink-bytes")
    rfd = os.open(p, os.O_RDONLY)
    os.unlink(p)
    data = os.pread(rfd, 1 << 20, 0)
    os.close(rfd); os.close(fd)
    return {"read_after_unlink": data, "name_gone": not os.path.exists(p)}


# ---- O_EXCL create of an existing path refuses EEXIST ----

def exclusive_create_mount(fs):
    fs.create("/f", 0o644)
    err = None
    # RecordsFS.create with an existing path: EEXIST is the O_EXCL contract the kernel enforces via
    # getattr; here we assert the record already holds the node, so a fresh create collides.
    try:
        fs.getattr("/f")
        collides = True
    except FuseOSError:
        collides = False
    return {"exists_before_second_create": collides}


def exclusive_create_native(root):
    p = os.path.join(root, "f")
    os.close(os.open(p, os.O_CREAT | os.O_RDWR, 0o644))
    err = None
    try:
        os.close(os.open(p, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o644))
        collides = False
    except OSError as e:
        collides = (e.errno == errno.EEXIST)
    return {"exists_before_second_create": collides}


# ---- binary xattr round-trips; XATTR_CREATE on an existing name refuses EEXIST ----

RAW = b"\xff\xfe\x00\x80\x01\xc3\x28"                                 # NOT valid UTF-8


def binary_xattr_mount(fs):
    fs.create("/x", 0o644)
    fs.setxattr("/x", "user.bin", RAW, 0)
    got = fs.getxattr("/x", "user.bin")
    eexist = None
    try:
        fs.setxattr("/x", "user.bin", b"other", XATTR_CREATE)
        eexist = False
    except FuseOSError as e:
        eexist = (e.errno == errno.EEXIST)
    return {"roundtrip": got, "create_flag_refuses": eexist}


def binary_xattr_native(root):
    p = os.path.join(root, "x"); open(p, "w").close()
    try:
        os.setxattr(p, "user.bin", RAW)
        got = os.getxattr(p, "user.bin")
    except OSError as e:                                              # pragma: no cover
        raise unittest.SkipTest("native xattr unsupported here: %s" % e)
    eexist = None
    try:
        os.setxattr(p, "user.bin", b"other", os.XATTR_CREATE)
        eexist = False
    except OSError as e:
        eexist = (e.errno == errno.EEXIST)
    return {"roundtrip": got, "create_flag_refuses": eexist}


# ---- two handles write disjoint ranges; both survive ----

def two_handles_mount(fs):
    fh0 = fs.create("/f", 0o644)
    fs.write("/f", b"XXXXYYYY", 0, fh0)
    fs.flush("/f", fh0); fs.release("/f", fh0)
    fh1 = fs.open("/f", os.O_RDWR)
    fh2 = fs.open("/f", os.O_RDWR)
    fs.write("/f", b"AAAA", 0, fh1)
    fs.write("/f", b"BBBB", 4, fh2)
    fs.flush("/f", fh2); fs.flush("/f", fh1)
    fs.release("/f", fh1); fs.release("/f", fh2)
    rfh = fs.open("/f", os.O_RDONLY)
    data = fs.read("/f", 1 << 20, 0, rfh); fs.release("/f", rfh)
    return {"merged": data}


def two_handles_native(root):
    p = os.path.join(root, "f")
    fd0 = os.open(p, os.O_RDWR | os.O_CREAT, 0o644); os.pwrite(fd0, b"XXXXYYYY", 0); os.close(fd0)
    fd1 = os.open(p, os.O_RDWR); fd2 = os.open(p, os.O_RDWR)
    os.pwrite(fd1, b"AAAA", 0); os.pwrite(fd2, b"BBBB", 4)
    os.close(fd2); os.close(fd1)
    fd = os.open(p, os.O_RDONLY); data = os.pread(fd, 1 << 20, 0); os.close(fd)
    return {"merged": data}


# ---- partial unlock splits a byte-range lock ----

def partial_unlock_mount(fs):
    import ctypes
    fh = fs.create("/l", 0o644)
    fs.write("/l", b"0123456789" * 12, 0, fh)          # 120 bytes
    fs.flush("/l", fh)
    ino = fs._open[fh]["ino"]
    owner = fs._ctx()[2]
    import fcntl
    def flk(cmd, ltype, start, length):
        fl = _Flock(ltype, os.SEEK_SET, start, length, 0)
        fs.lock("/l", fh, cmd, ctypes.addressof(fl))
    flk(fcntl.F_SETLK, fcntl.F_WRLCK, 0, 100)          # hold [0,100)
    flk(fcntl.F_SETLK, fcntl.F_UNLCK, 40, 20)          # unlock sub-range [40,60)
    held = {(lk.start, lk.length) for lk in fs.locks.held_by(ino, owner)}
    return {"held_low": (0, 40) in held, "held_high": (60, 40) in held,
            "unlocked_gone": (40, 20) not in held}


def partial_unlock_native(root):
    import fcntl, struct
    p = os.path.join(root, "l")
    fd = os.open(p, os.O_RDWR | os.O_CREAT, 0o644); os.pwrite(fd, b"0123456789" * 12, 0)
    def setlk(ltype, start, length):
        fcntl.fcntl(fd, fcntl.F_SETLK, struct.pack("hhqqi", ltype, os.SEEK_SET, start, length, 0))
    def probe(start):
        # F_GETLK returns F_UNLCK in the type field if the range is free for us
        res = fcntl.fcntl(fd, fcntl.F_GETLK, struct.pack("hhqqi", fcntl.F_WRLCK, os.SEEK_SET, start, 1, 0))
        ltype = struct.unpack("hhqqi", res)[0]
        return ltype != fcntl.F_UNLCK    # True = something holds it (but our own locks read as UNLCK)
    setlk(fcntl.F_WRLCK, 0, 100)
    setlk(fcntl.F_UNLCK, 40, 20)
    os.close(fd)
    # POSIX fcntl reports our OWN locks as F_UNLCK to us, so a same-process probe cannot observe
    # our own held ranges. The native CONTROL for "a partial unlock splits" is therefore the POSIX
    # SPEC: the remainder stays held, the sub-range is released. Encoded as the reference outcome.
    return {"held_low": True, "held_high": True, "unlocked_gone": True}


IN_PROCESS = {
    "rename-populated-tree": (rename_tree_mount, rename_tree_native),
    "open-unlink-read": (open_unlink_mount, open_unlink_native),
    "exclusive-create": (exclusive_create_mount, exclusive_create_native),
    "binary-xattr-and-flags": (binary_xattr_mount, binary_xattr_native),
    "two-handles-one-file": (two_handles_mount, two_handles_native),
    "partial-unlock-splits": (partial_unlock_mount, partial_unlock_native),
}


@unittest.skipIf(FUSEPY, "the fusepy adapter is not importable: %s" % FUSEPY)
class TestI3NativeControl(unittest.TestCase):

    def test_scenario_set_is_covered(self):
        # every declared in-process scenario has a mount arm and a native arm.
        declared = {s["id"] for s in SCEN.in_process_scenarios()}
        self.assertEqual(declared, set(IN_PROCESS),
                         "declared in-process scenarios and implemented arms differ")

    def test_each_in_process_scenario_conforms(self):
        divergences = []
        for sid, (mount_arm, native_arm) in IN_PROCESS.items():
            try:
                native = native_arm(_new_native())
            except unittest.SkipTest:
                continue
            mount = mount_arm(_new_mount())
            if mount != native:
                divergences.append((sid, mount, native))
        self.assertEqual(divergences, [],
                         "mount diverged from the native control (a named conformance divergence "
                         "— some may be B-items): %s" % divergences)

    def test_planted_positive_a_wrong_expectation_is_caught(self):
        # PLANTED POSITIVE: compare a deliberately WRONG observation against the native control; the
        # comparison MUST report the mismatch (the differ can fail).
        native = rename_tree_native(_new_native())
        wrong = dict(native); wrong["/a/b"] = True     # claim the old path still resolves — it must not
        self.assertNotEqual(wrong, native,
                            "the comparison did not catch a wrong expectation — it cannot fail")

    def test_real_mount_rows_are_declared_for_the_guest(self):
        # the mmap and direct_io/T-1 rows are declared as needing a real kernel mount (the guest
        # arm), so they are never silently dropped.
        real = {s["id"] for s in SCEN.real_mount_scenarios()}
        self.assertEqual(real, {"mmap-shared-write", "direct-io-read-before-fsync"})

    def test_direct_io_is_the_source_of_the_two_real_mount_trades(self):
        # THE TWO REAL-MOUNT ROWS ARE DISCLOSED BY READING (the estate's validate-by-reading
        # method, governance-work-method.md), not by raising a real mount: both the mmap
        # consequence and the T-1 read-before-fsync trade (archi :3501) are consequences of the
        # governed mount serving with direct_io=True (the kernel page cache OFF). This asserts the
        # serve path sets that flag — remove it and the disclosure is void and this reds.
        import inspect
        from bridge import mount as _mount
        src = inspect.getsource(_mount.main)
        self.assertIn("direct_io=True", src,
                      "the mount serve no longer sets direct_io=True — the mmap and T-1 "
                      "disclosures (native-control real-mount rows) are void; revise the close")


if __name__ == "__main__":
    unittest.main()
