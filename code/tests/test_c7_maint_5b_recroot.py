# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (the record-tree ROOT /rec, served as a listable directory by the body's finder). NON-GOAL:
# no offensive capability — it lists OUR OWN served record tree on OUR OWN kernel body and asserts the
# root's immediate children are the union of the archive's top-level dirs and the record disk's top-level
# names. Validate by building/reading, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-5B (A2) — the /rec ROOT lists (the finder root-listing prover, run ON THE BODY).

Run on the body via the ledger run stack (GOVOS_RUNMOD=test_c7_maint_5b_recroot). CPython's importlib
LISTS each sys.path entry once per import; /rec is on the path (enclosure.c, landed), so a package import
of `tests.<x>` needs os.listdir('/rec') to return the top-level names. Before this slice the record-tree
ROOT did not stat/list as a directory (serve_tree_is_dir returned 0 for the empty root path), so
os.listdir('/rec') raised FileNotFoundError and the package import failed. This proves the fix on the body.

WHAT THE ROOT LISTS (archi :4467): the union of the tree archive's top-level directories (src, tests) and
the record disk's top-level names (record, founding-pack, runmod, govtree, and the tmp namespace the boot
creates), each once. A listing that showed only the archive's two names would misreport the disk.

THE PLANT (L19): PLANT_TREE_ROOT_NOLIST disables the root's directory answer, so os.listdir('/rec') raises
FileNotFoundError here — the assertion reds by a real mechanism, distinct from a green run (which lists).

OFF-BODY: the /rec record tree is served only on the body; off the body this SKIPS (the guard below), so
the estate's own suite collects it without a spurious red.
"""

import os
import unittest


class TestRecRootListsTheUnion(unittest.TestCase):
    def test_rec_root_lists_the_union(self):
        # The served record tree exists only on the body (a served /rec/tests lists there). Off the body,
        # skip — nothing to prove without the finder.
        if not os.path.isdir("/rec/tests"):
            self.skipTest("off-body: the /rec record tree is served only on the kernel body")

        # Under PLANT_TREE_ROOT_NOLIST the root does not list -> this raises FileNotFoundError (the plant
        # reds by a real mechanism, L19). With the fix the root lists the union.
        names = sorted(os.listdir("/rec"))
        print("RECROOT-LISTING " + " ".join(names), flush=True)

        # the tree archive's top-level directories (src, tests), surfaced at depth zero
        for n in ("src", "tests"):
            self.assertIn(n, names, "the /rec root must list the tree archive top-level dir " + n)
        # the record disk's own top-level names mkdisk stages (record, founding-pack, runmod, govtree)
        for n in ("record", "founding-pack", "runmod", "govtree"):
            self.assertIn(n, names, "the /rec root must list the record-disk top-level name " + n)
        # every listed name is a genuine root child — no name escapes /rec
        for n in names:
            self.assertNotIn("/", n, "a /rec root child name must not contain a path separator: " + n)
        # no duplicates — each child once
        self.assertEqual(len(names), len(set(names)), "the /rec root lists each child exactly once")


if __name__ == "__main__":
    unittest.main()
