# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (mount, native control, conformance scenario, fold, page cache). NON-GOAL: no
# offensive capability of any kind — this DECLARES the conformance scenario set: the same POSIX
# behaviour run on the governed mount AND on a native directory, the two compared. Full
# declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I3 — the native-control conformance scenario SET (the declared form).

The instrument (tests/test_instr_native_control.py) runs each scenario on the governed mount AND on
a native directory (the control) and compares the observable outcome; divergences are NAMED (some
are the outside read's B-items — a true reading). This module is the DECLARED SET, in the fixture
form of tools/conformance's baselines (the `rows` shape): one row per scenario, its surface, and
whether it is drivable in-process or needs a REAL kernel mount.

Two rows need a REAL kernel FUSE mount (the guest, EP-00 rule 9) because their subject IS the
kernel's own behaviour, invisible to an in-process ops object. BOTH are architect-mandated named
rows for the disclosed consequences of B2's direct_io (RULED :3495):

  mmap-shared-write (:3495 (c)) — a MAP_SHARED writable mmap through the mount under direct_io. The
                               architect ruled this the measured consequence of the governed cache:
                               it is a kernel-version property (the guest is 6.8.0-134; the reader's
                               mmap case passed WITHOUT direct_io), and if it diverges it is
                               DISCLOSED IN STATUS as the price of a governed cache — never silently
                               traded back.
  direct-io-read-before-fsync (T-1, :3501) — with the page cache OFF, a SECOND descriptor reading
                               before an fsync does not see the first descriptor's un-fsynced write
                               via the cache. The accepted, disclosed trade of direct_io — measured
                               and DISCLOSED beside the mmap row, not a defect.

B2 is RESOLVED (:3495): direct_io=True is archi's word and is present in the serve path
(bridge/mount.py:109), so both consequences are in effect. (My dispatch cited ":3491 raised"; the
code has B2 ruled — logged in the close.)
"""

# surface: "in-process" (drivable via the RecordsFS ops object, run on the host or guest) or
# "real-mount" (needs a live kernel FUSE mount — the guest).
SCENARIOS = [
    {"id": "rename-populated-tree", "surface": "in-process",
     "what": "rename a populated directory; every descendant resolves under the new path"},
    {"id": "partial-unlock-splits", "surface": "in-process",
     "what": "unlock a strict sub-range of a held byte-range lock; the remainder stays held"},
    {"id": "binary-xattr-and-flags", "surface": "in-process",
     "what": "a non-UTF-8 xattr value round-trips; XATTR_CREATE on an existing name refuses EEXIST"},
    {"id": "two-handles-one-file", "surface": "in-process",
     "what": "two open handles write disjoint ranges; both survive (no whole-buffer clobber)"},
    {"id": "open-unlink-read", "surface": "in-process",
     "what": "unlink an open file; the descriptor still reads its bytes (POSIX open-unlink)"},
    {"id": "exclusive-create", "surface": "in-process",
     "what": "O_EXCL create of an existing path refuses EEXIST"},
    {"id": "mmap-shared-write", "surface": "real-mount",
     "what": "archi :3495(c): a MAP_SHARED writable mmap through the mount under direct_io — a "
             "kernel-version property (guest 6.8.0-134); if it diverges it is DISCLOSED in STATUS "
             "as the price of a governed cache, never silently traded back"},
    {"id": "direct-io-read-before-fsync", "surface": "real-mount",
     "what": "T-1 (archi :3501): a second descriptor reading before fsync under direct_io does not "
             "see the first's un-fsynced write via the page cache — the disclosed trade of B2's "
             "direct_io; measured and disclosed, not fixed"},
]


def in_process_scenarios():
    return [s for s in SCENARIOS if s["surface"] == "in-process"]


def real_mount_scenarios():
    return [s for s in SCENARIOS if s["surface"] == "real-mount"]
