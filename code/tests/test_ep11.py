"""EP-11 — comparison layer v1: frame-carrying verdicts (design 28 §9).

T-VERDICT-FRAMES, both directions of the ONE comparison law:
  * DIFFERENT frames on the same (a, b) are DIFFERENT INFORMATION — both kept, never merged, NEVER
    flagged as a contradiction (keeping both IS the feature; the federation seed);
  * SAME-frame incompatibility IS a contradiction, routed to the owner queue as a pure view that
    appends nothing.
The comparison law is a genesis-seeded rule record COMPARE cites (law as data, never a constant in the
view); frames are data, not an enum; the contradiction view does not reuse ROOT-NEG-6's machinery.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402


class TestVerdictFrames(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "r.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def _compare(self, actor, a, b, frame, verdict):
        return self.gate.execute("COMPARE", actor, {"a": a, "b": b, "frame": frame, "verdict": verdict})

    # ---- DIRECTION 1: different frames are different information — never flagged, never merged ----
    def test_cross_frame_verdicts_coexist_and_are_never_flagged(self):
        self._compare("owner", "x", "y", "cost", "a-greater")     # x beats y on cost
        self._compare("owner", "x", "y", "speed", "a-lesser")     # y beats x on speed
        self.assertEqual(len(self.store.by_action("COMPARE")), 2)  # BOTH kept — no merger, no averaging
        self.assertEqual(self.views.contradictions(), [])          # NEVER a contradiction (different frames)

    def test_frames_are_data_arbitrary_observer_named_frames_work(self):
        self._compare("owner", "p", "q", "some-novel-frame-42", "prefer-p")   # a frame is a name a
        self._compare("owner", "p", "q", "another-frame", "prefer-q")         # observer chose — no enum
        self.assertEqual(self.views.contradictions(), [])

    # ---- DIRECTION 2: same-frame incompatibility is a contradiction routed to the owner ----
    def test_same_frame_incompatibility_is_a_contradiction_routed_to_owner(self):
        self._compare("owner", "x", "y", "cost", "a-greater")
        self._compare("alice", "x", "y", "cost", "a-lesser")       # SAME frame, incompatible -> a dispute
        c = self.views.contradictions()
        self.assertEqual(len(c), 1)
        self.assertEqual((c[0]["a"], c[0]["b"], c[0]["frame"]), ("x", "y", "cost"))
        self.assertEqual(c[0]["verdicts"], ["a-greater", "a-lesser"])   # both incompatible verdicts named

    def test_same_frame_agreement_is_not_a_contradiction(self):
        self._compare("owner", "x", "y", "cost", "a-greater")
        self._compare("bob", "x", "y", "cost", "a-greater")        # same frame, they AGREE -> no dispute
        self.assertEqual(self.views.contradictions(), [])

    # ---- the detection is a pure view; the law is data ----
    def test_the_contradiction_view_appends_nothing(self):
        self._compare("owner", "x", "y", "cost", "a-greater")
        self._compare("alice", "x", "y", "cost", "a-lesser")       # a contradiction exists
        before = len(self.store.all())
        self.views.contradictions()                                # a pure derivation
        self.assertEqual(len(self.store.all()), before)            # detection appended NOTHING

    def test_compare_cites_the_genesis_seeded_comparison_law_not_a_constant(self):
        rec = self._compare("owner", "x", "y", "cost", "a-greater")
        self.assertEqual(rec["rule_cited"], "COMPARISON-LAW")      # the verdict cites the law
        self.assertIn("COMPARISON-LAW", self.views.active_rules())  # which is a genesis-seeded rule RECORD
        self.assertEqual(rec["payload"]["kind"], "verdict")        # a frame-carrying verdict record


if __name__ == "__main__":
    unittest.main()
