# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary. NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""P8B-HARDENING delta 1 (archi Resolution A, board :3735) — the equivalence guard.

Delta 1 moved the (class, cell) pairing's per-act capability read OFF a per-act store.all() walk and
ONTO a SEPARATE head-memoised fold (`class_capabilities`) that reads through the category_packs record
projection. category_packs() itself is byte-unchanged (Resolution A — test_ep16). The ruling is "NO
behaviour change". This module is the standing proof: the memoised `class_capabilities` equals the
retained record-walk oracle, and `pair()` / `class_band` return identical answers, across four worlds —
the founding, the world before the {human,ai,program} domain goes live, a LEVELS-ONLY amend (AMEND-PACK
strips capabilities, so the founding map must carry forward), and a full CREATE-INFO re-seed that DOES
carry a new map. DIVERGENCES NONE is the acceptance.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernel.boot import build_kernel                                  # noqa: E402

CLASSES = ("human", "ai", "program", "system", "robot", "unclassified-token")
CELLS = ("S", "U", "U{s}", "S{u}", "not-a-cell")


def _oracle_admit(views, actor_class, cell, as_of=None):
    """pair()'s admit boolean recomputed from the RECORD-WALK oracle instead of the memoised fold —
    every other input to pair() (required_capability, the closed domain) is untouched by delta 1, so
    this is the behaviour delta 1 must not move."""
    need = views.required_capability(cell)
    if need is None:
        return False
    held = views._class_capabilities_record_walk(as_of).get(actor_class)
    if held is None:
        return False
    return need in held


class _World(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self._dir, "r.jsonl"))

    def _domain_seq(self, levels):
        for e in self.store.all():
            p = e.get("payload") or {}
            if p.get("kind") == "category_pack" and p.get("name") == "actor-classes" \
                    and list(p.get("levels") or []) == list(levels):
                return e["seq"]
        return None

    def _assert_equivalent(self, as_of=None):
        # 1) the map itself: memoised fold == record-walk oracle
        self.assertEqual(self.views.class_capabilities(as_of),
                         self.views._class_capabilities_record_walk(as_of),
                         f"class_capabilities diverged from the record walk (as_of={as_of})")
        # 2) pair() admit identical for every (class, cell) — the map equality above guarantees the
        #    full tuple (reason string reads the same held map); we assert the admit directly too
        for cls in CLASSES:
            for cell in CELLS:
                self.assertEqual(self.views.pair(cls, cell, as_of)[0],
                                 _oracle_admit(self.views, cls, cell, as_of),
                                 f"pair() admit moved for ({cls!r},{cell!r}) as_of={as_of}")


class TestDelta1MemoisedEqualsRecordWalk(_World):

    def test_the_founding_world(self):
        self._assert_equivalent()
        self.assertEqual(self.views.class_capabilities(),
                         {"human": ("structured-arm", "unstructured-arm"),
                          "ai": ("unstructured-arm",), "program": ("structured-arm",)})

    def test_before_the_domain_goes_live(self):
        # as_of just before the {human,ai,program} pack: both empty, and identical
        seq = self._domain_seq(["human", "ai", "program"])
        self.assertIsNotNone(seq)
        self._assert_equivalent(as_of=seq - 1)
        self.assertEqual(self.views.class_capabilities(as_of=seq - 1), {})

    def test_after_a_levels_only_amend_keeps_the_founding_map(self):
        # AMEND-PACK re-cuts LEVELS but cannot carry capabilities (its op is name/levels only), so the
        # memoised fold must CARRY the founding map forward (skip the caps-less amend), matching the walk.
        self.gate.execute("AMEND-PACK", "owner",
                          {"name": "actor-classes", "levels": ["human", "ai", "program", "robot"]})
        self._assert_equivalent()
        self.assertEqual(self.views.class_capabilities()["ai"], ("unstructured-arm",))   # map unchanged
        self.assertEqual(set(self.views.class_domain()), {"human", "ai", "program", "robot"})  # levels moved

    def test_after_a_full_reseed_tracks_the_new_map(self):
        # a full CREATE-INFO re-seed DOES carry a capabilities map; both paths track the change
        self.store._append({"actor": "owner", "action": "CREATE-INFO", "rule_cited": "BOOT-INT",
                            "object": "pack:actor-classes",
                            "payload": {"kind": "category_pack", "name": "actor-classes",
                                        "levels": ["human", "ai", "program"],
                                        "capabilities": {"human": ["structured-arm", "unstructured-arm"],
                                                         "ai": ["structured-arm", "unstructured-arm"],
                                                         "program": ["structured-arm"]}}})
        self._assert_equivalent()
        self.assertEqual(self.views.class_capabilities()["ai"], ("structured-arm", "unstructured-arm"))

    def test_category_packs_is_byte_identical_no_capabilities_key(self):
        # RESOLUTION A's load-bearing point: category_packs() gains NO capabilities key — the separate
        # fold carries the map, the projection's own shape does not move (test_ep16 stays green).
        for name, pack in self.views.category_packs().items():
            self.assertEqual(set(pack), {"name", "levels", "seq"},
                             f"category_packs['{name}'] shape changed — Resolution A requires it byte-identical")

    def test_class_band_is_unmoved_by_delta_1(self):
        # class_band reads the domain + classify, never capabilities — so it is identical.
        self.assertEqual(self.views.class_band("owner"), "human")        # a declared class
        self.assertIsNone(self.views.class_band("SYSTEM"))               # 'system' not in the domain
        self.assertIsNone(self.views.class_band("nobody-here"))          # no classify, no account


if __name__ == "__main__":
    unittest.main(verbosity=2)
