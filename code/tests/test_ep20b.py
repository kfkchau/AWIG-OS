# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary; NON-GOAL: no offensive capability. Full declaration: SCOPE-STATEMENT.md.
"""EP-20B — the protection boot-fallback is retired (R20-1, owner-directed at the campaign-2 close).

The dual-audit action list is the `dual-audit-actions` category_pack and nothing else. The
code-resident fallback that used to stand behind it was unreachable and had drifted from the
live pack; these tests hold the retirement in place and pin the failure mode that replaces it.

Two directions, both asserted:
  * the shipped composition boots and mirrors with no module-resident action list present;
  * a composition whose record lacks the pack REFUSES at boot, citing CONST-RECORDING-TOTAL —
    it never falls back to code and never degrades to an empty list (both are silent
    substitutes for law, which is the thing the retirement exists to refuse).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel import protection as prot_mod  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.gate import Gate  # noqa: E402
from kernel.protection import Protection  # noqa: E402
from kernel.store import EventStore  # noqa: E402
from kernel.views import Views  # noqa: E402


class TestProtectionBootsFromPackOnly(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.prot = self.views.protection

    def test_protection_boots_from_pack_only(self):
        # the floor the mirror enforces IS the recorded pack, member for member
        pack = self.views.category_packs()["dual-audit-actions"]
        self.assertEqual(self.prot._audit_actions(), {x for x in pack["levels"] if isinstance(x, str)})
        # and it carries the campaign-2 members the retired constant never had
        self.assertIn("VERIFY-ACCOUNT", self.prot._audit_actions())
        self.assertIn("VERIFY-SECRET", self.prot._audit_actions())
        # the streams run: a governance act (an op-refused) is mirrored to BOTH blind streams
        with self.assertRaises(OpError):
            self.gate.execute("NO-SUCH-OP", "alice", {})
        self.assertEqual(len(self.store.by_action("dual-audit-record")), 1)
        self.assertEqual(len(self.store.by_action("dual-audit-b-record")), 1)
        self.assertTrue(self.prot.audit_consistent())
        self.assertEqual(self.prot.dual_blind_divergences(), [])

    def test_no_code_resident_action_list_under_any_name(self):
        # the named corpse is gone
        self.assertFalse(hasattr(prot_mod, "DUAL_AUDIT_ACTIONS"))
        # and so is any RENAMED second copy — designed for the stretch, not the intent: the next
        # hand that wants the comfort back will not reuse the retired name. Any module-level
        # collection holding audit-floor members is the same defect wearing another label.
        floor = self.prot._audit_actions()
        resident = [name for name, obj in vars(prot_mod).items()
                    if isinstance(obj, (set, frozenset, list, tuple))
                    and any(action in obj for action in floor)]
        self.assertEqual(resident, [], f"a code-resident copy of the audit floor survives: {resident}")


class TestMissingPackRefusesLoudly(unittest.TestCase):
    """The fail-closed direction. Reaching it needs a store that never ran genesis — no
    composed world can produce one (build_kernel always seeds the pack, and the pack is
    floor-protected against removal), which is exactly why the fallback was dead code."""

    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "no-founding.jsonl")
        self.store = EventStore(self.path, require_rule_cited=True)
        self.views = Views(self.store)
        self.gate = Gate(self.store, self.views)

    def test_missing_pack_refuses_loudly(self):
        self.assertIsNone(self.views.category_packs().get("dual-audit-actions"))  # the premise
        with self.assertRaises(OpError) as cm:
            Protection(self.store, self.gate, self.views)
        self.assertEqual(cm.exception.rule, "CONST-RECORDING-TOTAL")
        self.assertIn("dual-audit-actions", cm.exception.message)

    def test_a_refused_boot_leaves_no_half_wired_mirror(self):
        with self.assertRaises(OpError):
            Protection(self.store, self.gate, self.views)
        # nothing was attached to the store, so nothing mirrors against an empty or
        # code-supplied list: the refusal is a stall, not a degraded mode
        self.assertEqual([fn for fn in self.store._listeners
                          if isinstance(getattr(fn, "__self__", None), Protection)], [])
        self.store._append({"actor": "SYSTEM", "action": "op-refused", "rule_cited": "P3-CLOSURE",
                            "payload": {"op": "NO-SUCH-OP"}})
        self.assertEqual(self.store.by_action("dual-audit-record"), [])
        self.assertEqual(self.store.by_action("dual-audit-b-record"), [])


if __name__ == "__main__":
    unittest.main()
