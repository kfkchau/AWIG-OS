"""Thin-slice test (design 02 §10) at foundation scale: the composed kernel
(store + gate + views + bootstrap) boots, governs, refuses, and reconstructs
entirely from the record.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel, genesis, unregistered_bootstrap_ops  # noqa: E402
from kernel.errors import OpError  # noqa: E402
# EP-14: the root laws are no longer a boot.py literal — they live in the founding pack,
# read back through the installer's accessor (same (id, polarity, text, extras) shape).
from founding.install import root_laws as _root_laws  # noqa: E402
ROOT_RULES = _root_laws()


class TestBoot(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")

    def test_thin_slice_composes_and_governs(self):
        store, gate, views = build_kernel(self.path)
        genesis(store)
        # a scheduling policy enters as LAW, contradiction-checked, and reads back
        gate.execute("CREATE-RULE", "SYSTEM",
                     {"rule_id": "law:sched-policy", "policy_key": "quantum_ms", "value": 4, "exclusive": True})
        self.assertEqual(views.policy_value("quantum_ms"), 4)
        # READ records provenance-populating access
        gate.execute("READ", "SYSTEM", {"object": "law:sched-policy"})
        self.assertEqual(len(store.by_action("READ")), 1)
        # an unregistered op is a Closure Hit, recorded and raised
        with self.assertRaises(OpError) as cm:
            gate.execute("MAKE-COFFEE", "SYSTEM", {})
        self.assertEqual(cm.exception.rule, "P3-CLOSURE")
        self.assertEqual(len(store.by_action("op-refused")), 1)

    def test_contradiction_is_refused(self):
        store, gate, views = build_kernel(self.path)
        genesis(store)
        gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:x", "policy_key": "k", "value": 1, "exclusive": True})
        with self.assertRaises(OpError) as cm:
            gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:x2", "policy_key": "k", "value": 2, "exclusive": True})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-6")
        # exactly one outcome: a refusal, not a second rule
        self.assertEqual(len(store.by_action("op-refused")), 1)

    def test_whole_kernel_reconstructs_from_the_record(self):
        store, gate, views = build_kernel(self.path)
        genesis(store)
        gate.execute("CREATE-RULE", "SYSTEM", {"rule_id": "law:q", "policy_key": "q", "value": 7})
        gate.execute("CREATE-ACTOR", "SYSTEM", {"actor_id": "sched", "role": "subsystem"})
        # rebuild a fresh kernel from the same file — every cache killed
        store2, gate2, views2 = build_kernel(self.path)
        self.assertEqual(views2.policy_value("q"), 7)
        self.assertEqual(len(store2.by_action("CREATE-ACTOR")), 3)  # SYSTEM + owner (genesis) + sched

    def test_build_seeds_the_constitution_idempotently(self):
        # F2: a composed kernel carries its own root law + SYSTEM actor without a separate
        # genesis() call, and seeding is idempotent (build / reload / explicit call).
        store, gate, views = build_kernel(self.path)  # NO explicit genesis()
        self.assertIn("SYSTEM", [e["object"] for e in store.by_action("CREATE-ACTOR")])
        self.assertGreater(len(store.by_action("CREATE-RULE")), 0)  # root law is present
        before = len(store.all())
        genesis(store)                                  # explicit call: idempotent, adds nothing
        self.assertEqual(len(store.all()), before)
        store2, _, _ = build_kernel(self.path)          # reload: no double-seed
        self.assertEqual(len(store2.by_action("CREATE-ACTOR")), len(store.by_action("CREATE-ACTOR")))

    def test_constitution_recorded(self):
        # T-CONSTITUTION-RECORDED (design/27 §6): a fresh kernel's record carries the
        # founding designation, both boot actors, the owner tunnel, the mother space,
        # and every root rule WITH polarity and text — readable back as a view.
        store, gate, views = build_kernel(self.path)
        self.assertEqual(len(store.by_action("FOUND-STORE")), 1)          # the chain-end
        actors = {(e.get("payload") or {}).get("actor_id") for e in store.by_action("CREATE-ACTOR")}
        self.assertIn("SYSTEM", actors)
        self.assertIn("owner", actors)
        self.assertEqual(len(store.by_action("CREATE-TUNNEL")), 1)        # the instruction path
        spaces = [e for e in store.by_action("CREATE-INFO")
                  if (e.get("payload") or {}).get("kind") == "info_space"]
        self.assertEqual([s["payload"]["name"] for s in spaces], ["root"])  # the mother space
        rr = views.root_rules()
        self.assertEqual(len(rr), len(ROOT_RULES))                        # every rule recorded
        polarities = {r["polarity"] for r in rr}
        self.assertEqual(polarities, {"+", "-"})                          # dos AND don'ts present
        self.assertTrue(all(r["text"] for r in rr))                       # law as text, not just ids
        packs = [e for e in store.by_action("CREATE-INFO")
                 if (e.get("payload") or {}).get("kind") == "category_pack"]
        self.assertIn("actor-classes", [p["payload"]["name"] for p in packs])

    def test_bootstrap_ledger_is_honest(self):
        store, gate, views = build_kernel(self.path)
        pending = unregistered_bootstrap_ops(gate)
        self.assertIn("FOLLOW", pending)          # named-pending, not silently missing
        self.assertNotIn("CREATE-RULE", pending)  # wired


if __name__ == "__main__":
    unittest.main()
