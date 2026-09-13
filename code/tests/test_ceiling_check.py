"""T-CEILING-CHECK [design 28 §5, EP-04]: the campaign's one fresh check, derived to
reproduce the retired `memory._resident` EXACTLY. These tests cover the paths the memory
suite is SILENT on — the ones where a naive port breaks budget law without failing a test.

The aggregate is an ORDERED keyed fold over the whole record (not two by-action scans), so
grant/evict/re-grant interleave correctly; the removal is unfiltered by holder (evictions
carry none); grants overwrite; the holder fallback lands in both the check and the payload;
and a missing policy means unlimited.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from subsystems.memory import MemoryView  # noqa: E402


class TestCeilingCheck(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)
        self.mv = MemoryView(self.store)

    def _budget(self, holder, ceiling):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": holder, "ceiling": ceiling})

    def _grant(self, region, size, **kw):
        return self.gate.execute("MEM-GRANT", kw.pop("actor", "web"),
                                 {"region": region, "size": size, **kw})

    def test_grant_within_budget_allowed(self):
        self._budget("web", 100)
        self._grant("r1", 40, holder="web")
        self.assertEqual(self.mv.resident_size("web"), 40)

    def test_grant_over_budget_refused(self):
        self._budget("web", 100)
        self._grant("r1", 100, holder="web")
        with self.assertRaises(OpError) as cm:
            self._grant("r2", 1, holder="web")
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")

    def test_no_policy_is_unlimited(self):
        # no AMEND-BUDGET -> ceiling is None -> allow (current behaviour, per _resident's caller)
        self._grant("r1", 10 ** 9, holder="web")
        self.assertEqual(self.mv.resident_size("web"), 10 ** 9)

    def test_eviction_frees_budget(self):
        # the removal is unfiltered by holder — an eviction (which carries no holder) frees
        # whatever region it names. Without this, eviction silently stops freeing budget.
        self._budget("web", 100)
        self._grant("r1", 100, holder="web")
        self.gate.execute("MEM-EVICT", "web", {"region": "r1"})
        self._grant("r2", 100, holder="web")  # must be allowed now
        self.assertEqual(self.mv.resident_size("web"), 100)

    def test_ordered_fold_regrant_after_evict_still_counts(self):
        # THE silent-mismatch lock: grant -> evict -> RE-grant. A naive "granted map minus
        # evicted set" drops the re-granted region and lets the holder exceed budget. The
        # ordered fold sees r1 present again, so the next grant is correctly refused.
        self._budget("web", 100)
        self._grant("r1", 100, holder="web")
        self.gate.execute("MEM-EVICT", "web", {"region": "r1"})
        self._grant("r1", 100, holder="web")  # re-granted after eviction
        with self.assertRaises(OpError) as cm:
            self._grant("r2", 1, holder="web")
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")

    def test_regrant_overwrites_not_additive(self):
        # a grant OVERWRITES the region's size (re-grant is not additive). budget 100:
        # r1=60 then r1=40 leaves resident 40, so r2=60 fits; additive (100) would refuse it.
        self._budget("web", 100)
        self._grant("r1", 60, holder="web")
        self._grant("r1", 40, holder="web")          # overwrite -> resident 40, not 100
        self._grant("r2", 60, holder="web")          # allowed iff overwrite
        self.assertEqual(self.mv.resident_size("web"), 100)

    def test_holder_fallback_records_and_counts_the_actor(self):
        # holder defaults to the actor in BOTH the check and the recorded payload, so a
        # holder-less grant cannot silently escape the actor's budget.
        self._budget("web", 100)
        rec = self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 100})  # no holder
        self.assertEqual(rec["payload"]["holder"], "web")     # recorded under the actor
        with self.assertRaises(OpError) as cm:
            self.gate.execute("MEM-GRANT", "web", {"region": "r2", "size": 1})  # no holder
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")  # r1 counted -> refused

    def test_budget_is_per_holder(self):
        # one holder's grants do not consume another holder's budget
        self._budget("web", 100)
        self._budget("db", 100)
        self._grant("r1", 100, holder="web")
        self._grant("r2", 100, holder="db")          # db has its own 100
        self.assertEqual(self.mv.resident_size("web"), 100)
        self.assertEqual(self.mv.resident_size("db"), 100)


if __name__ == "__main__":
    unittest.main()
