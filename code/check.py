#!/usr/bin/env python3
"""AWIG OS seed check battery. Eight readings of the machinery in this folder.

Run it:  python3 check.py

Each check builds its own kernel in a fresh temporary directory and throws it away.
Nothing here reads seed_demo.py, so a green battery is independent of the demo.
Check 6 is the control: it is the one that must report a mismatch, because a
fingerprint that cannot say no is not a check.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

def require_durable_sync():
    """Say why this platform cannot run it, before the engine says it in a traceback.

    The store refuses to append a record it cannot prove reached the disk. On a
    platform with no os.fdatasync that refusal is correct and it fires at the first
    append, three exceptions deep, where a reader cannot see what happened. The
    refusal is the same either way; this one is readable.
    """
    if hasattr(os, "fdatasync"):
        return
    name = os.path.basename(sys.argv[0]) or "check.py"
    sys.stderr.write(
        "\nThis platform has no os.fdatasync, so a record cannot be proved durable\n"
        "and the engine will not append one. That is the system refusing, not a\n"
        "bug: it does not record an act it cannot show reached the disk.\n"
        "\nYou are most likely on Windows. Run it under WSL:\n"
        "\n    wsl python3 %s\n"
        "\nVerified on Linux, Python 3.12.3. See Platforms in README.md.\n\n" % name
    )
    sys.exit(1)


require_durable_sync()

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from kernel.boot import build_kernel                            # noqa: E402
from kernel.errors import OpError                               # noqa: E402
from kernel.canonical import canonical_hash, strip_derivation   # noqa: E402

RULE = "ROOT-NEG-6"
KEY = "demo_setting"
PACK = os.path.join(HERE, "src", "founding", "founding-pack.json")


def world_of(views):
    return {
        "laws_in_force": strip_derivation(views.active_rules()),
        "operations": strip_derivation(views.op_definitions()),
        "accounts": strip_derivation(views.accounts()),
        "spaces": strip_derivation(views.spaces()),
        KEY: views.policy_value(KEY),
    }


class SeedCheck(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="awig-check-")
        self.path = os.path.join(self.dir, "record.jsonl")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _governed(self):
        store, gate, views = build_kernel(self.path)
        return store, gate, views

    def _make_law(self, gate):
        gate.execute("CREATE-RULE", "SYSTEM",
                     {"rule_id": "law:demo", "policy_key": KEY, "value": 4, "exclusive": True})

    def test_1_the_constitution_founds_itself_into_the_record(self):
        """1. The constitution founds itself into the record, one line per entry."""
        store, _gate, _views = self._governed()
        self.assertTrue(os.path.exists(self.path))
        self.assertGreater(len(store.all()), 0)
        with open(self.path, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        self.assertEqual(len(lines), len(store.all()))
        store.close()

    def test_2_the_rule_reads_back_out_of_the_record(self):
        """2. The rule reads back out of the record file, not out of any source code."""
        store, _gate, views = self._governed()
        law = views.active_rules()[RULE]
        self.assertEqual(law["rule_id"], RULE)
        self.assertEqual(law["polarity"], "-")
        self.assertTrue(law["text"])
        with open(self.path, encoding="utf-8") as fh:
            on_file = [json.loads(ln) for ln in fh if ln.strip() and RULE in ln]
        self.assertTrue(any(e.get("object") == RULE for e in on_file))
        store.close()

    def test_3_an_allowed_act_appends_one_record_citing_the_rule(self):
        """3. An allowed act appends exactly one record, and that record cites the rule."""
        store, gate, views = self._governed()
        before = len(store.all())
        self._make_law(gate)
        self.assertEqual(len(store.all()), before + 1)
        appended = store.all()[-1]
        self.assertEqual(appended["action"], "CREATE-RULE")
        self.assertEqual(appended["object"], "law:demo")
        self.assertEqual(appended["rule_cited"], RULE)
        self.assertEqual(views.policy_value(KEY), 4)
        store.close()

    def test_4_a_contradicting_act_is_refused_and_the_refusal_is_recorded(self):
        """4. A contradicting act is refused, and the refusal is itself a record."""
        store, gate, views = self._governed()
        self._make_law(gate)
        before = len(store.all())
        with self.assertRaises(OpError) as caught:
            gate.execute("CREATE-RULE", "SYSTEM",
                         {"rule_id": "law:demo-2", "policy_key": KEY,
                          "value": 10, "exclusive": True})
        self.assertEqual(caught.exception.rule, RULE)
        self.assertEqual(len(store.all()), before + 1)
        refusal = store.all()[-1]
        self.assertEqual(refusal["action"], "op-refused")
        self.assertIs(refusal["refused"], True)
        self.assertEqual(refusal["rule_cited"], RULE)
        self.assertEqual(refusal["payload"]["op"], "CREATE-RULE")
        # the world did not move
        self.assertEqual(views.policy_value(KEY), 4)
        store.close()

    def test_5_killing_the_world_and_replaying_returns_the_same_fingerprint(self):
        """5. Kill the world, replay the record alone, and the fingerprint is identical."""
        store, gate, views = self._governed()
        self._make_law(gate)
        try:
            gate.execute("CREATE-RULE", "SYSTEM",
                         {"rule_id": "law:demo-2", "policy_key": KEY,
                          "value": 10, "exclusive": True})
        except OpError:
            pass
        before = canonical_hash(world_of(views))
        elsewhere = os.path.join(self.dir, "replay", "record.jsonl")
        os.makedirs(os.path.dirname(elsewhere))
        shutil.copy(self.path, elsewhere)
        store.close()
        del store, gate, views
        os.remove(self.path)
        store2, _g2, views2 = build_kernel(elsewhere)
        self.assertEqual(canonical_hash(world_of(views2)), before)
        store2.close()

    def test_6_the_fingerprint_reports_a_record_that_does_not_match(self):
        """6. The control. A fingerprint that cannot report a difference proves nothing,
        so one recorded value is changed on a copy and the answer must come back different."""
        store, gate, views = self._governed()
        self._make_law(gate)
        before = canonical_hash(world_of(views))
        store.close()
        changed = os.path.join(self.dir, "changed", "record.jsonl")
        os.makedirs(os.path.dirname(changed))
        touched = 0
        with open(self.path, encoding="utf-8") as src, open(changed, "w", encoding="utf-8") as dst:
            for line in src:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("object") == "law:demo":
                        entry["payload"]["value"] = 5
                        touched += 1
                    line = json.dumps(entry) + "\n"
                dst.write(line)
        self.assertEqual(touched, 1)
        store2, _g2, views2 = build_kernel(changed)
        self.assertEqual(views2.policy_value(KEY), 5)
        self.assertNotEqual(canonical_hash(world_of(views2)), before)
        store2.close()

    def test_7_the_record_is_one_json_object_per_line_in_unbroken_order(self):
        """7. The record is one JSON object per line, numbered from 1 with no gaps."""
        store, gate, _views = self._governed()
        self._make_law(gate)
        store.close()
        seqs = []
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    seqs.append(json.loads(line)["seq"])
        self.assertEqual(seqs, list(range(1, len(seqs) + 1)))

    def test_8_the_freeze_line_names_the_founding_this_folder_actually_carries(self):
        """8. FREEZE.txt names the founding version this folder actually carries."""
        with open(os.path.join(HERE, "FREEZE.txt"), encoding="utf-8") as fh:
            freeze = fh.read()
        with open(PACK, encoding="utf-8") as fh:
            version = json.load(fh)["founding_version"]
        self.assertIn(version, freeze)
        self.assertIn("commit", freeze)


class WholeDescription(unittest.TextTestResult):
    """Prints each check's whole description, never only its first line.

    unittest's own shortDescription() stops at the first line of a docstring, so an
    explanation written across two lines reaches the screen cut in half while still
    reading like a finished sentence. Collapsing the whole docstring onto one line
    removes that outcome rather than warning about it.
    """

    def getDescription(self, test):
        name = test.id().rsplit(".", 1)[-1]
        doc = getattr(getattr(type(test), name, None), "__doc__", None)
        return " ".join(doc.split()) if doc else str(test)


if __name__ == "__main__":
    print()
    print("AWIG OS seed check battery. Eight readings of the machinery in this folder,")
    print("each in its own fresh temporary directory, none of them reading seed_demo.py.")
    print("Check 6 is the control: it changes one recorded value on a copy and requires")
    print("the fingerprint to come back different, because a fingerprint that cannot")
    print("report a difference has not checked anything.")
    print()
    sys.stdout.flush()

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SeedCheck)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2,
                                     resultclass=WholeDescription).run(suite)
    code = 0 if result.wasSuccessful() else 1
    print()
    print("Exit code %d. Zero means all eight passed; anything else means one did not."
          % code)
    sys.exit(code)
