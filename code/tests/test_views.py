"""Contract test for views (L2) — computed-not-stored, asOf, and the kill-the-cache
(round-trip) property at the view level.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import EventStore  # noqa: E402
from kernel.views import Views  # noqa: E402


class TestViews(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store = EventStore(os.path.join(self.dir, "record.jsonl"))
        self.views = Views(self.store)

    def _rule(self, rid, key, value, action="CREATE-RULE"):
        return self.store._append(
            {"actor": "SYSTEM", "action": action, "object": rid,
             "payload": {"rule_id": rid, "policy_key": key, "value": value}}
        )

    def test_policy_value_latest_wins(self):
        self._rule("law:quantum", "quantum_ms", 3)
        self.assertEqual(self.views.policy_value("quantum_ms"), 3)
        self._rule("law:quantum", "quantum_ms", 4, action="AMEND-RULE")
        self.assertEqual(self.views.policy_value("quantum_ms"), 4)

    def test_asof_sees_history(self):
        r1 = self._rule("law:q", "q", 3)
        self._rule("law:q", "q", 4, action="AMEND-RULE")
        self.assertEqual(self.views.policy_value("q"), 4)
        self.assertEqual(self.views.policy_value("q", as_of=r1["seq"]), 3)

    def test_kill_the_cache_is_identical(self):
        for i in range(5):
            self._rule(f"law:{i}", "k", i)
        before = self.views.active_rules()
        self.views._memo.clear()  # kill every derived cache
        after = self.views.active_rules()  # recompute from the record alone
        self.assertEqual(before, after)

    def test_head_memoized_then_bumped_by_an_append_it_depends_on(self):
        """DOCUMENTED FLIP (EP-28B W3, 2026-07-30). This asserted that ANY append recomputes
        `active_rules`, and a bare "noise" record was the append it used — a record that cannot
        change one word of law. That over-invalidation is what W3 removes, so the row now pins
        the property at the altitude of the law it was written for: the memo dies with a change
        it depends on and survives one it cannot."""
        self._rule("law:x", "k", 1)
        a = self.views.active_rules()
        b = self.views.active_rules()
        self.assertIs(a, b)  # head is memoized (same object) until a LAW record lands
        self.store._append({"actor": "SYSTEM", "action": "noise"})
        self.assertIs(self.views.active_rules(), a,
                      "a record declaring no rule_id recomputed the law fold")
        self._rule("law:y", "k", 2)
        c = self.views.active_rules()
        self.assertIsNot(a, c)  # a law record moved this fold's own generation -> recompute
        self.assertIn("law:y", c)

    def test_generic_fold(self):
        for act in ["X", "Y", "X"]:
            self.store._append({"actor": "SYSTEM", "action": act})

        def reducer(state, e):
            state[e["action"]] = state.get(e["action"], 0) + 1

        counts = self.views.fold(reducer, {})
        self.assertEqual(counts.get("X"), 2)
        self.assertEqual(counts.get("Y"), 1)


if __name__ == "__main__":
    unittest.main()
