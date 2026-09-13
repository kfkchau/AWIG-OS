# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (record, fold, grant, standing, overturn, mapping). NON-GOAL: no offensive capability
# of any kind — this instrument (EP-MAINT-OUTSIDE-4 I7) asserts that EVERY fold deriving authority or
# resources over rows a late law can overturn APPLIES STANDING: an overturned row is absent from its
# answer. It plants its positive AT THE CENSUS (a hand-rolled fold that does NOT apply standing must
# be reported as a finding), never by producing an unrecorded byte. Full declaration: SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-4 · I7 — THE STANDING CENSUS.

"An act a late law overturned still authorises a new act and still holds a mapping." (the round-2
read's R1.) Every fold that derives AUTHORITY or RESOURCES reads rows a late law can overturn; each
MUST apply standing — an overturned row is ABSENT from its answer (R1's one mechanism, the store's
live-rows predicate). This census drives a world with an overturned grant AND an overturned mapping
and checks the shipped authority/resource folds carry NEITHER.

PLANTED POSITIVE (planted AT THE CENSUS, never a real unrecorded byte): a hand-rolled fold that reads
the whole record WITHOUT the standing predicate carries the overturned grant, and the census MUST
report it. The census can fail without manufacturing a real defect — a fold that stopped applying
standing would surface here.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel import reconcile, authority                             # noqa: E402
from kernel.compose import build_full_kernel                        # noqa: E402
from subsystems.memory import MemoryView                            # noqa: E402

OWNER = "owner"


def T(h, m, s=0, us=0):
    return f"2026-07-27T{h:02d}:{m:02d}:{s:02d}.{us:06d}+00:00"


def grants_without_standing(store):
    """A DELIBERATELY NON-STANDING grant fold — reads the WHOLE record (never the store's live rows),
    exactly the pre-R1 shape. The census must report this as a finding when a grant is overturned."""
    live = {}
    for e in store.all():
        a = e["action"]
        p = e.get("payload") or {}
        if a == "GRANT" and p.get("kind") == "grant":
            live[e.get("object")] = {"grant_id": e.get("object"), "seq": e["seq"]}
        elif a == "REVOKE":
            live.pop(e.get("object"), None)
    return live


def standing_census(store, ctx, extra_folds=()):
    """THE CENSUS: for every fold in the registry that derives authority or resources over
    late-law-overturnable rows, does its answer CARRY the overturned row planted in `ctx`? A fold
    that does is a FINDING. `extra_folds` lets a test plant a non-standing fold to prove the census
    can catch one. Returns the list of finding names (empty == every fold applies standing)."""
    registry = [
        # authority: the overturned GRANT must be absent from the live grant fold
        ("authority.grants",
         lambda s: ctx["grant_id"] in authority.grants(s)),
        # resources: the overturned MEM-GRANT's region must not be a held mapping
        ("memory.mappings",
         lambda s: ctx["region"] in MemoryView(s).mappings()),
    ] + list(extra_folds)
    return [name for name, carries in registry if carries(store)]


class TestStandingCensus(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep-mo4-i7-")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))

    def _timed(self, name, param="at"):
        live = self.views.op_definitions()[name]
        d = json.loads(json.dumps(live["definition"], default=dict))
        d["params"] = dict(d.get("params") or {}, **{param: "required"})
        d["occurrence_time_param"] = param
        d["structural_params"] = list(dict.fromkeys(list(d.get("structural_params") or []) + [param]))
        self.gate.execute("AMEND-OP", OWNER, {"name": name, "tier": live.get("tier"),
                                              "definition": d})

    def _law(self, rule_id, at, when):
        self.gate.execute("CREATE-RULE", OWNER, {
            "rule_id": rule_id, "at": at, "polarity": "-", "text": f"{rule_id} refuses",
            "when": when, "then": [{"refuse": rule_id}]})

    def _overturned_world(self):
        """A world with a GRANT and a MEM-GRANT both overturned by a late-deciding law."""
        self._timed("CREATE-RULE")
        self._timed("GRANT")
        self._timed("MEM-GRANT")
        self.gate.execute("GRANT", OWNER, {"grant_id": "g1", "grantee": "alice",
                                           "actions": ["CREATE-INFO"], "info": ["note"],
                                           "space": "space:root", "at": T(9, 30)})
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "h", "ceiling": 100000})
        self.gate.execute("MEM-GRANT", "h", {"region": "r1", "size": 100, "holder": "h",
                                             "at": T(9, 30)})
        self._law("NO-GRANT", T(9, 0), [{"action": "GRANT", "object": "grant:g1"}])
        self._law("NO-MG", T(9, 0), [{"action": "MEM-GRANT"}])
        return {"grant_id": "grant:g1", "region": "r1"}

    def test_the_shipped_folds_apply_standing_census_is_empty(self):
        ctx = self._overturned_world()
        # both rows really are overturned (the census's premise)
        self.assertTrue(reconcile.overturned_targets(self.store))
        # I7 (A4): every shipped authority/resource fold applies standing — the census is EMPTY
        self.assertEqual(standing_census(self.store, ctx), [])

    def test_a_fold_that_does_not_apply_standing_is_a_finding(self):
        ctx = self._overturned_world()
        # PLANTED POSITIVE: a fold reading the whole record without the standing predicate carries the
        # overturned grant — the census MUST report it (proving the census can fail).
        planted = [("grants_without_standing",
                    lambda s: ctx["grant_id"] in grants_without_standing(s))]
        findings = standing_census(self.store, ctx, extra_folds=planted)
        self.assertIn("grants_without_standing", findings)


if __name__ == "__main__":
    unittest.main()
