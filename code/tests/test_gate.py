"""Contract test for the gate (L1) — SC1 acceptance: exactly one outcome, a decision
or a rule-cited refusal; unknown = Closure Hit; params validate before the handler.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import EventStore  # noqa: E402
from kernel.gate import Gate  # noqa: E402
from kernel.views import Views  # noqa: E402
from kernel.errors import OpError  # noqa: E402


class TestGate(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store = EventStore(os.path.join(self.dir, "record.jsonl"))
        self.gate = Gate(self.store, Views(self.store))  # views is required (C0)

        def create_info(actor, params):
            # handlers RETURN the draft; the gate appends it (design 28 §I2)
            return {"actor": actor, "action": "CREATE-INFO", "object": params["content"], "rule_cited": "ROOT-NEG-5"}

        self.gate.register(
            "CREATE-INFO",
            {"description": "mint an info object", "rules": ["ROOT-NEG-5"], "params": {"content": "required"}},
            create_info,
        )

    def test_registered_op_appends_exactly_one_decision(self):
        before = len(self.store.all())
        r = self.gate.execute("CREATE-INFO", "SYSTEM", {"content": "hello"})
        self.assertEqual(len(self.store.all()), before + 1)
        self.assertEqual(r["action"], "CREATE-INFO")
        self.assertEqual(r["object"], "hello")
        self.assertEqual(self.store.by_action("op-refused"), [])  # no refusal

    def test_unknown_op_is_a_closure_hit(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("NOPE", "SYSTEM", {})
        self.assertEqual(cm.exception.rule, "P3-CLOSURE")
        refusals = self.store.by_action("op-refused")
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["rule_cited"], "P3-CLOSURE")
        self.assertTrue(refusals[0].get("refused"))
        self.assertEqual(self.store.by_action("CREATE-INFO"), [])  # zero domain decisions

    def test_missing_param_refuses_before_handler(self):
        entered = {"v": False}

        def needs(actor, params):
            entered["v"] = True
            return {"actor": actor, "action": "X"}

        self.gate.register("NEEDS", {"rules": ["AR-2"], "params": {"x": "required"}}, needs)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("NEEDS", "SYSTEM", {})
        self.assertEqual(cm.exception.rule, "AR-2")
        self.assertFalse(entered["v"])  # handler never entered
        self.assertEqual(len(self.store.by_action("op-refused")), 1)

    def test_nonconforming_call_cites_ar2_not_the_domain_rule(self):
        # F1 regression: a missing-param refusal cites the nonconforming-call rule AR-2,
        # never the op's own domain rule (which governs the act, not the call's form).
        def handler(actor, params):
            return {"actor": actor, "action": "Y", "rule_cited": "DOMAIN-RULE"}

        self.gate.register("HASDOMAIN", {"rules": ["DOMAIN-RULE"], "params": {"x": "required"}}, handler)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("HASDOMAIN", "SYSTEM", {})
        self.assertEqual(cm.exception.rule, "AR-2")  # not "DOMAIN-RULE"
        self.assertEqual(self.store.by_action("op-refused")[0]["rule_cited"], "AR-2")

    def test_list_enumerates_ops(self):
        listing = self.gate.list()
        self.assertIn("CREATE-INFO", listing)
        self.assertEqual(listing["CREATE-INFO"]["params"], {"content": "required"})

    def test_duplicate_registration_refused(self):
        with self.assertRaises(ValueError):
            self.gate.register("CREATE-INFO", {}, lambda a, p: None)


if __name__ == "__main__":
    unittest.main()
