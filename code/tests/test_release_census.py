#!/usr/bin/env python3
"""EP-RELEASE-TESTS census: the shipped skip list equals the renderer's manifest (SET equality),
every skipped module exists in this tree, and each carries its reason and named private file.
add-one or drop-one REDS."""
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _read_skiplist():
    out = {}
    with open(os.path.join(HERE, "RELEASE-SKIP-LIST.txt"), encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            mod, reason, dep = line.split("\t")
            out[mod] = (reason, dep)
    return out


class ReleaseSkipCensus(unittest.TestCase):
    def setUp(self):
        self.manifest = json.load(open(os.path.join(ROOT, "RELEASE-TESTS-MANIFEST.json")))
        self.skiplist = _read_skiplist()

    def test_skip_list_set_equals_the_manifest(self):
        man = {e["module"] for e in self.manifest["skip_list"]}
        self.assertEqual(set(self.skiplist), man, "shipped skip list != renderer manifest skip set")

    def test_every_skipped_module_exists_in_this_tree(self):
        for mod in self.skiplist:
            self.assertTrue(os.path.exists(os.path.join(HERE, mod)), "skipped module absent: %s" % mod)

    def test_each_skip_names_its_reason_and_private_file(self):
        man = {e["module"]: e for e in self.manifest["skip_list"]}
        for mod, (reason, dep) in self.skiplist.items():
            self.assertIn(mod, man)
            self.assertEqual(man[mod]["reason"], reason)
            self.assertEqual(man[mod]["private_file"], dep)
            self.assertTrue(reason and dep)

    def test_tree_checksums_present(self):
        self.assertEqual(set(self.manifest.get("tree_checksums", {})), {"src", "tests", "tools"})


if __name__ == "__main__":
    unittest.main()
