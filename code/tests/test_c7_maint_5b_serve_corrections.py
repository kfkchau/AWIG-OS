# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (a path finder that resolves a go-up component and refuses an escape; a file's identity
# number as a property of the FILE; a write on a descriptor the body does not know answering the real
# bad-handle error). NON-GOAL: no offensive capability — it drives OUR OWN body's filesystem shim on
# OUR OWN kernel body inside a nested guest and asserts the corrected behaviour, with a real mechanism
# per plant. Validate by building/reading, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-5B-SERVE-CORRECTIONS — the three body-fixes, asserted ON THE BODY with fallible plants.

This is the "ONE new test asserting A1-A3 with their plants" the plan's fence names. It runs UNDER the
on-body interpreter (the 5b ledger run stack) over the /rec archive; OFF the body it SKIPS (its probes
are statements about the freestanding body's own filesystem shim, reached only there). Every probe is a
regression test (the campaign method), and every one is written so it CAN FAIL — the matching build.sh
-D plant reddens exactly its assertion by a REAL mechanism, never a flag:

  A1  the finder resolves '.' / '..' and REFUSES an escape above the served tree (L21).
      PLANT_FINDER_NO_ESCAPE clamps the escaping '..' -> an escape probe resolves to a SERVED file.
  A2  st_ino is a property of the FILE: the same number from a path stat, an fstat of any open handle,
      and a re-open on a new slot; two different files never share one; a closed fd stats -EBADF.
      PLANT_STAT_PERSLOT restores the per-SLOT ino (+ a char-dev stat of a closed fd) -> path != fd.
  A2r removal is served ONLY under /rec/tmp/: rmtree of a /rec/tmp world completes; an rmdir OUTSIDE
      /rec/tmp/ is refused. PLANT_REMOVE_OUTSIDE_TMP serves the outside removal.
  A3  a write on a descriptor the body does not know answers -EBADF (a loud error), never the canned
      length. PLANT_WRITE_CANNED restores the canned count on an unknown fd.
"""

import os
import shutil
import tempfile
import unittest

# ON THE BODY the whole gov-os tree is served under /rec/ (the 5b ledger archive); OFF the body it is
# not, so these body-shim probes skip (the estate's off-body runner stays green).
ON_BODY = os.path.isdir("/rec/tests") and os.path.isdir("/rec/src")

_SIGNER = "/rec/src/kernel/signer.py"                      # a file KNOWN to be served in the tree archive


@unittest.skipUnless(ON_BODY, "the body-shim corrections are provable only under the on-body 5b run")
class TestServeCorrections(unittest.TestCase):

    # ---- A1 — the finder normalizes a go-up component and refuses an escape ----------------------
    def test_a1_finder_normalizes_dotdot_and_refuses_an_escape(self):
        # a plain served path opens
        with open(_SIGNER, "rb") as fh:
            self.assertTrue(fh.read(4))
        # a LEGIT go-up that stays inside the tree resolves to the same file (CPython reaches signer.py
        # exactly this way: os.path.dirname(__file__) == /rec/tests, joined with '..')
        with open("/rec/tests/../src/kernel/signer.py", "rb") as fh:
            self.assertTrue(fh.read(4))
        # an ESCAPE above the served tree is refused (PLANT_FINDER_NO_ESCAPE clamps it -> this resolves
        # to the SERVED src/kernel/signer.py and the open succeeds, redding this assertion)
        with self.assertRaises(OSError):
            open("/rec/../src/kernel/signer.py", "rb").close()

    # ---- A2 — stat identity is a property of the FILE -------------------------------------------
    def test_a2_stat_identity_is_a_property_of_the_file(self):
        d = tempfile.mkdtemp()                             # /rec/tmp/<world> (the ledger sets tempdir=/rec/tmp)
        p1 = os.path.join(d, "rec.jsonl")
        p2 = os.path.join(d, "rec2.jsonl")
        fd1 = os.open(p1, os.O_WRONLY | os.O_CREAT | os.O_APPEND)   # a caller-named record (NREC)
        try:
            id_fd = (os.fstat(fd1).st_dev, os.fstat(fd1).st_ino)
            id_path = (os.stat(p1).st_dev, os.stat(p1).st_ino)
            self.assertEqual(id_path, id_fd, "a path stat and an fstat of ONE file must agree (samestat)")
            # a re-open on a NEW slot answers the SAME identity (identity is the file, not the slot)
            fd1b = os.open(p1, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            try:
                self.assertEqual((os.fstat(fd1b).st_dev, os.fstat(fd1b).st_ino), id_fd)
            finally:
                os.close(fd1b)
            # a DIFFERENT file never shares the identity
            fd2 = os.open(p2, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            try:
                self.assertNotEqual((os.fstat(fd2).st_dev, os.fstat(fd2).st_ino), id_fd,
                                    "two different files must not share an st_ino")
            finally:
                os.close(fd2)
        finally:
            os.close(fd1)
        # a CLOSED descriptor has no file -> fstat is -EBADF, not a bogus char device
        with self.assertRaises(OSError):
            os.fstat(fd1)

    # ---- A2r — removal served ONLY under /rec/tmp/ ---------------------------------------------
    def test_a2r_removal_only_under_rec_tmp(self):
        # rmtree of a DISCARDED /rec/tmp world completes (unlink each record, rmdir the emptied namespace)
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "f.txt"), "w") as fh:
            fh.write("discardable")
        shutil.rmtree(d)
        self.assertFalse(os.path.exists(d), "rmtree must remove a /rec/tmp world")
        # an rmdir OUTSIDE /rec/tmp/ is REFUSED (PLANT_REMOVE_OUTSIDE_TMP serves it -> no raise -> reds)
        outside = "/rec/ns-outside-probe"
        os.mkdir(outside)                                  # a namespace outside /rec/tmp
        with self.assertRaises(OSError):
            os.rmdir(outside)

    # ---- A3 — a write on a descriptor the body does not know answers -EBADF ---------------------
    def test_a3_write_on_an_unknown_descriptor_is_ebadf(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "w.jsonl")
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        self.assertEqual(os.write(fd, b"hello"), 5, "a served write returns the real byte count")
        os.close(fd)
        # a write on the now-closed (unknown) descriptor is a LOUD error, never a canned length
        # (PLANT_WRITE_CANNED answers the canned 5 -> os.write returns 5, no raise -> this assertion reds)
        with self.assertRaises(OSError):
            os.write(fd, b"x")


if __name__ == "__main__":
    unittest.main()
