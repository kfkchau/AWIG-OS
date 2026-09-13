"""Views as data records (design/27 §4, build step two) — T-VIEW-DEF-EXECUTES:
a view is a recorded standing rule (trigger -> outcome), executed by one engine,
amendable by re-definition, with its blind spots derived from the definition alone.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402


class TestViewDefinitions(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views = build_kernel(os.path.join(self.dir, "record.jsonl"))

    def test_view_is_a_recorded_req(self):
        # a view enters through the gate as a named item carrying a rule_id — it IS law
        self.gate.execute("CREATE-VIEW", "SYSTEM", {"name": "refusals", "when": {"refused": True}})
        self.assertIn("refusals", self.views.view_definitions())
        self.assertIn("view:refusals", self.views.active_rules())     # REQ-form: the law view sees it
        d = self.views.view_definitions()["refusals"]
        self.assertIn("when a record matches", d["text"])             # the rule readable as a sentence

    def test_execute_filters_the_record(self):
        self.gate.execute("CREATE-VIEW", "SYSTEM", {"name": "law", "when": {"action": "CREATE-RULE"}})
        out = self.views.execute_view("law")
        self.assertGreaterEqual(out["count"], 13)                     # at least the constitution
        self.assertTrue(all(e["action"] == "CREATE-RULE" for e in out["rows"]))

    def test_negated_trigger_element(self):
        # the minus INSIDE a trigger: match records where the dimension is NOT this value
        self.gate.execute("CREATE-VIEW", "SYSTEM",
                          {"name": "non-law", "when": {"action": {"not": "CREATE-RULE"}}})
        out = self.views.execute_view("non-law")
        self.assertTrue(all(e["action"] != "CREATE-RULE" for e in out["rows"]))
        self.assertGreater(out["count"], 0)                           # genesis has non-rule records

    def test_redefinition_is_amendment_history_survives(self):
        first = self.gate.execute("CREATE-VIEW", "SYSTEM", {"name": "w", "when": {"actor": "a"}})
        self.gate.execute("CREATE-VIEW", "SYSTEM", {"name": "w", "when": {"actor": "b"}})
        self.assertEqual(self.views.view_definitions()["w"]["when"], {"actor": "b"})   # latest wins
        old = self.views.view_definitions(as_of=first["seq"])["w"]                     # asOf: history intact
        self.assertEqual(old["when"], {"actor": "a"})

    def test_unknown_trigger_dimension_refused(self):
        # closed vocabulary: an unknown dimension is a nonconforming call, refused, recorded
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-VIEW", "SYSTEM", {"name": "x", "when": {"color": "red"}})
        self.assertEqual(cm.exception.rule, "AR-2")
        self.assertEqual(len(self.store.by_action("op-refused")), 1)
        self.assertNotIn("x", self.views.view_definitions())          # nothing was defined

    def test_coverage_derived_from_definition_alone(self):
        self.gate.execute("CREATE-VIEW", "SYSTEM", {"name": "law", "when": {"action": "CREATE-RULE"}})
        c = self.views.coverage_statement("law")
        self.assertIn("action = CREATE-RULE", c["boundary"])
        self.assertIn("actor", c["undiscriminated"])                  # confesses what it never tests
        self.assertIn("NOT", c["complement"])

    def test_outcome_template_carries_the_move(self):
        # the universal setup: when x matches -> move info x to an entity/channel
        self.gate.execute("CREATE-VIEW", "SYSTEM",
                          {"name": "alerts", "when": {"refused": True},
                           "then": {"move_to": "channel:owner"}})
        out = self.views.execute_view("alerts")
        self.assertEqual(out["then"]["move_to"], "channel:owner")
        d = self.views.view_definitions()["alerts"]
        self.assertIn("move it to channel:owner", d["text"])


if __name__ == "__main__":
    unittest.main()
