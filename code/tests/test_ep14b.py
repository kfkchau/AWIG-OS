"""EP-14B acceptance battery — one founding source: the copied-dict residue, ended.

After EP-14 the founding lives in `founding/founding-pack.json` (the single source). EP-14B's
first passes proved the six module op-definition dicts (`subsystems/*.py`, `kernel/obligations.py`)
had NO consumer but the differential oracle, taught that oracle to reconstruct the six modules from
the pinned commit (so it runs in its own era, self-contained — see tests/test_ep14.py), and then
RETIRED the six dicts and their law-name constants. Zero copies is the goal completed: one
authoritative home for the founding's op shapes, the pack.

The guard is therefore ABSENCE, not a match over surviving copies (vacuous once none survive) — the
exact mechanic `test_law_out_of_code` uses for law text, extended to op shapes:

T-NO-OP-DICTS (test_no_module_op_definition_dicts_outside_the_founding) — a scan of src/ outside
    founding/ for the op-definition-dict assignment pattern; any hit is a second home reintroduced
    and fails LOUDLY, naming the pack. Guards accidental reintroduction (the law-out-of-code
    mechanic); a deliberate rename is campaign-review territory, not this guard's job.
T-READER (test_op_definition_reader_matches_the_pack) — install.op_definition(s), the repoint
    target the first build wired the module-dict consumers onto, reads every op shape faithfully
    from the pack.
T-READER-RAISES (test_reader_raises_for_an_op_the_founding_does_not_define) — the reader refuses a
    name the founding does not define.

Every probe here lands as a regression test (R14).
"""

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import frozen_default  # noqa: E402
from founding.install import load_pack, op_definitions, op_definition  # noqa: E402

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
FOUNDING_DIR = os.path.join(SRC, "founding")

# The op-definition-dict assignment shape (e.g. `MEMORY_OP_DEFINITIONS = {`). `(?!=)` excludes `==`
# comparisons; the lowercase pack reader `op_definitions(` is unmatched; a deletion-marker comment
# that only names an op family in prose (no `<NAME>_OP_DEFINITIONS =`) is unmatched. This
# discriminator was verified clean (no false hits) on the deleted-state tree before adoption
# (BUILD-PROGRESS EP-14B second pass, raise #4; accepted on the record in ADDENDUM 2 step 4).
OP_DICT_PATTERN = re.compile(r"[A-Z][A-Z_]*_OP_DEFINITIONS\s*=(?!=)")

PACK_SOURCE = "the founding lives in founding/founding-pack.json — put op shapes there, not in code"


def _canon(x):
    """Serialize to canonical JSON so a pack's JSON-loaded dict compares on VALUE, not on key order
    or Python identity (the EP-14 oracle's normalization, reused by the reader check)."""
    return json.dumps(x, sort_keys=True, default=frozen_default)


class TestNoOpDictsOutsideFounding(unittest.TestCase):
    """The guard, flipped to ABSENCE: the pack is the SOLE home for op shapes. A future edit that
    reintroduces a module-level op-definition dict (a second, silent home) is caught here, loudly."""

    def _scan(self):
        hits = []
        for root, _dirs, files in os.walk(SRC):
            if os.path.commonpath([os.path.abspath(root), FOUNDING_DIR]) == FOUNDING_DIR:
                continue                                  # founding/ is the one legitimate home
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if OP_DICT_PATTERN.search(line):
                            hits.append(f"{os.path.relpath(path, SRC)}:{i}: {line.strip()}")
        return hits

    def test_no_module_op_definition_dicts_outside_the_founding(self):
        hits = self._scan()
        self.assertEqual(
            hits, [],
            "an op-definition dict was (re)introduced outside the founding — " + PACK_SOURCE
            + ":\n" + "\n".join(hits))

    def test_the_absence_guard_can_fail(self):
        # Prove the column can fail: the pattern must flag a reintroduced dict (in-test text, never
        # the real tree). A guard that cannot catch its target is theatre.
        self.assertRegex("MEMORY_OP_DEFINITIONS = {", OP_DICT_PATTERN)
        self.assertRegex("DEVICE_OP_DEFINITIONS={", OP_DICT_PATTERN)
        # and it must NOT fire on the innocents it lives beside
        self.assertNotRegex("if MEMORY_OP_DEFINITIONS == pack_defs:", OP_DICT_PATTERN)
        self.assertNotRegex("defs = op_definitions(load_pack())", OP_DICT_PATTERN)
        self.assertNotRegex("# the DEVICE op definitions were retired to the pack", OP_DICT_PATTERN)


class TestPackReader(unittest.TestCase):
    """The repoint target: install.op_definition(s) reads the op shapes from the pack, so a
    consumer that needs an op's shape reads the SOURCE, not a module copy (the first build wired the
    last module-dict consumers here; nothing imports a module op-definition dict any longer)."""

    def test_op_definition_reader_matches_the_pack(self):
        pack = load_pack()
        recs = [r for s in pack["steps"] for r in s["records"]]
        pack_ops = {r["payload"]["name"]: r["payload"]["definition"]
                    for r in recs if r.get("action") == "CREATE-OP"}
        got = op_definitions(pack)
        self.assertEqual(set(got), set(pack_ops))
        for name, d in pack_ops.items():
            self.assertEqual(_canon(op_definition(name, pack)), _canon(d), name)

    def test_reader_raises_for_an_op_the_founding_does_not_define(self):
        with self.assertRaises(KeyError):
            op_definition("NO-SUCH-FOUNDED-OP")


if __name__ == "__main__":
    unittest.main()
