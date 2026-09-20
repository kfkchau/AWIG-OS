# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (rule lifecycle stage, per-body clock, recording moment, local dwell, causal order,
# census). NON-GOAL: no offensive capability of any kind — every assertion proves B7/I9/I23 by
# function: the eight stages are kinds of existing row (no new field), metabolism is a per-body
# local dwell on one body's own record_time plus a causal order, and the census REDS on any view
# that folds two bodies' clocks. Full declaration: SCOPE-STATEMENT.md.
"""C6 P15 [YELLOW] — STAGE ROWS CROSSING; METABOLISM (B7, I23 limb-3).

  A1 (B7, I9)   STAGES ARE ROW KINDS, NO NEW FIELD — the eight stages pin to kinds of EXISTING
                row; every field the pin reads is a member of the shipped record's own field
                census; the pin adds ZERO fields (I9). A pin is asserted, not proved.
  A2 (B7)       METABOLISM IS LOCAL DWELL, PER BODY — a stage's dwell is the interval between two
                arrivals at the SAME body on that one body's own record_time (read from a real
                store), a true local metric; the causal order end to end reads from the
                crossing/receipt binding; NO figure spans two bodies' clocks as a bare number (the
                sanctioned sink RAISES across two bodies).
  A3 (I23 lb-3) THE CENSUS REFUSES A CROSS-CLOCK FOLD (positive control) — the census over the
                shipped views finds NONE that folds; a PLANTED view computing
                `other.record_time - mine.record_time` reds the census (the check can fail);
                removed, it greens. No new check kind.
  A4            THE SEND-TIME-CLAIM IS ABSENT — the default ships local dwell + causal order with NO
                send-time-claim value minted; if one were ever needed it is a RAISE riding P8.
"""

import datetime
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from kernel import border                                          # noqa: E402
from kernel import store as store_mod                              # noqa: E402
from tools.conformance import stage_metabolism as P15              # noqa: E402


# =================================================================================================
# A1 — the stages are kinds of existing row; no new field (B7, I9).
# =================================================================================================

class TestA1StagesAreRowKindsNoNewField(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="p15-a1-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store = store_mod.EventStore(os.path.join(self.dir, "rec.jsonl"))
        self.addCleanup(self.store.close)

    def test_the_shipped_record_field_census_matches_the_pin_s_known_set(self):
        # the pin's KNOWN_RECORD_FIELDS is the row shape's field census; a real drift in the row
        # shape (a genuinely new field) would break this — the I9 tripwire.
        rec = self.store._append({"actor": "SYSTEM", "action": "probe",
                                  "rule_cited": "M1-OBSERVATION", "payload": {"i": 1}})
        self.assertEqual(set(rec.keys()), set(P15.KNOWN_RECORD_FIELDS),
                         "the shipped record's field set diverged from the pin's known set — a row "
                         "field was added or removed (I9's tripwire)")

    def test_every_stage_pin_field_is_an_existing_record_field(self):
        # each stage reads only fields a fresh record already carries — no stage names a field the
        # row shape lacks.
        for field in P15.stage_pin_fields():
            self.assertIn(field, P15.KNOWN_RECORD_FIELDS,
                          "stage pin reads %r, not a field of the shipped row shape" % field)

    def test_the_pin_adds_zero_row_fields(self):
        # I9 stated mechanically: the union of everything the pin reads is a SUBSET of the shipped
        # fields, so the pin introduces none.
        self.assertTrue(P15.stage_pin_fields() <= set(P15.KNOWN_RECORD_FIELDS))
        added = P15.stage_pin_fields() - set(P15.KNOWN_RECORD_FIELDS)
        self.assertEqual(added, set(), "the stage pin added row fields %r — I9 forbids it" % added)

    def test_the_eight_stages_are_pinned_to_row_kinds(self):
        # the mapping exists and is ASSERTED (each stage names a row kind and a reason); communication
        # is recorded as NOT a gov-os stage (B7), the exclusion pinned rather than a row invented.
        self.assertIn("announcement", P15.STAGE_PIN)
        self.assertIn("reporting", P15.STAGE_PIN)
        self.assertIn("monitoring", P15.STAGE_PIN)
        self.assertIn("analysis", P15.STAGE_PIN)
        self.assertIn("environment", P15.STAGE_PIN)
        self.assertFalse(P15.STAGE_PIN["communication"]["gov_os_stage"],
                         "communication must be pinned as NOT a gov-os stage (B7)")
        for stage, spec in P15.STAGE_PIN.items():
            self.assertTrue(spec["row_kind"], "%s carries no row kind" % stage)
            self.assertTrue(spec["reason"], "%s carries no reason — a pin states its assertion" % stage)


# =================================================================================================
# A2 — metabolism is a per-body local dwell on one body's own clock; the end-to-end is a causal order.
# =================================================================================================

class TestA2MetabolismIsLocalDwellPerBody(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="p15-a2-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def _body_store(self, name):
        st = store_mod.EventStore(os.path.join(self.dir, "%s.jsonl" % name))
        self.addCleanup(st.close)
        return st

    def test_local_dwell_reads_one_body_s_own_record_time(self):
        # body A records two stage-rows; the dwell is the interval between them on A's OWN clock,
        # read from real record_time (minted at append, never supplied).
        a = self._body_store("A")
        r1 = a._append({"actor": "A", "action": "announce", "rule_cited": "M1-OBSERVATION",
                        "payload": {"stage": "announcement"}})
        r2 = a._append({"actor": "A", "action": "report", "rule_cited": "M1-OBSERVATION",
                        "payload": {"stage": "reporting"}})
        arrivals = [P15.Arrival("A", "announcement", r1["record_time"]),
                    P15.Arrival("A", "reporting", r2["record_time"])]
        dwells = P15.local_dwell_per_stage(arrivals)
        self.assertEqual(len(dwells), 1)
        self.assertEqual(dwells[0]["body"], "A")
        self.assertEqual((dwells[0]["from_stage"], dwells[0]["to_stage"]),
                         ("announcement", "reporting"))
        # a true local metric: non-negative, on ONE clock (r2 recorded no earlier than r1).
        self.assertGreaterEqual(dwells[0]["dwell_seconds"], 0.0)

    def test_the_sanctioned_sink_refuses_two_bodies(self):
        # THE FLOOR: the one place a record_time subtraction lives refuses two clocks — no figure
        # spans two bodies' clocks (I23 limb 3, the runtime floor).
        far_apart_a = P15.Arrival("A", "reporting", "2020-01-01T00:00:00+00:00")
        far_apart_b = P15.Arrival("B", "reporting", "2099-01-01T00:00:00+00:00")
        with self.assertRaises(P15.CrossClockFold):
            P15.local_interval(far_apart_a, far_apart_b)

    def test_local_dwell_refuses_mixed_body_arrivals(self):
        # metabolism is PER BODY: handed two bodies' arrivals it raises rather than fold them into
        # one interval (I23 limb 3).
        mixed = [P15.Arrival("A", "reporting", "2020-01-01T00:00:00+00:00"),
                 P15.Arrival("B", "reporting", "2099-01-01T00:00:00+00:00")]
        with self.assertRaises(P15.CrossClockFold):
            P15.local_dwell_per_stage(mixed)

    def test_causal_order_end_to_end_is_an_order_not_a_number(self):
        # the end-to-end relation reads from the crossing/receipt binding: B's receipt cites the
        # CONTENT HASH of A's submit (border.content_id, which excludes record_time), so the send
        # causally precedes the receipt. The result is an ORDER; it carries no cross-clock number.
        submit = {"actor": "A", "action": "BORDER-SUBMIT", "object": "draft-1",
                  "target": "B", "payload": {"body": "hello"}}
        receipt = {"actor": "B", "action": "RECEIPT",
                   "payload": {"content_hash": border.content_id(submit)}}
        order = P15.causal_order(submit, receipt)
        self.assertEqual(order, [("A", "reporting-send"), ("B", "reporting-receipt")])
        # an ORDER (a list of (body, stage)) — no float, no subtracted duration anywhere in it.
        for _body, _stage in order:
            self.assertIsInstance(_stage, str)

    def test_causal_order_is_none_when_the_receipt_does_not_bind_the_submit(self):
        # the check can fail the other way: a receipt citing a different content hash binds no
        # crossing, so there is no causal edge to assert (a positive, discriminating reading).
        submit = {"actor": "A", "action": "BORDER-SUBMIT", "object": "draft-1",
                  "target": "B", "payload": {"body": "hello"}}
        wrong_receipt = {"actor": "B", "action": "RECEIPT",
                         "payload": {"content_hash": "sha256:deadbeef"}}
        self.assertIsNone(P15.causal_order(submit, wrong_receipt))


# =================================================================================================
# A3 — the census refuses a cross-clock fold (positive control). No new check kind.
# =================================================================================================

# A PLANTED view that subtracts one body's clock from another's — the exact fold the census exists to
# catch (SPIKE-4 §3: "elapsed = B.receipt.record_time minus A.send.record_time").
PLANT_CROSS_CLOCK_FOLD_SOURCE = '''\
def _cross_clock_fold_plant(other, mine):
    # DISHONEST: a bare subtraction of two bodies' recording moments as though one clock.
    import datetime
    elapsed = (datetime.datetime.fromisoformat(other.record_time)
               - datetime.datetime.fromisoformat(mine.record_time))
    return elapsed.total_seconds()
'''


class TestA3CensusRefusesCrossClockFoldStatic(unittest.TestCase):

    def test_the_shipped_views_fold_nothing(self):
        rows = P15.census()
        self.assertEqual(len(rows), len(P15.METABOLISM_VIEWS))
        self.assertEqual(P15.folding_views(rows), [],
                         "a shipped view folds two clocks: %s"
                         % [(r["view"], r["reasons"]) for r in P15.folding_views(rows)])

    def test_the_classifier_flags_a_planted_cross_clock_fold(self):
        # read the plant directly: it subtracts two record_times -> folds. If this did not fire, the
        # census could not fail and would prove nothing.
        c = P15.classify_view(PLANT_CROSS_CLOCK_FOLD_SOURCE)
        self.assertTrue(c["folds"], "the classifier did not flag a cross-clock subtraction")
        self.assertTrue(c["reasons"])

    def test_the_honest_views_are_not_flagged(self):
        # the control the other way: the real local-dwell view routes its subtraction through the
        # sanctioned same-body sink and is NOT flagged — the check discriminates, it does not red on
        # everything.
        c = P15.classify_view(P15._view_source("local_dwell_per_stage"))
        self.assertFalse(c["folds"], "the honest local-dwell view was flagged — false positive")


class TestA3CensusRefusesCrossClockFoldBehavioural(unittest.TestCase):

    def test_a_planted_view_reds_the_census_then_greens_on_removal(self):
        import types
        # a module-shaped namespace holding the shipped views PLUS the plant (nothing merged into the
        # tree; the plant lives only here, the sibling of the five-families behavioural control).
        planted_mod = types.ModuleType("p15_planted")
        planted_mod.local_dwell_per_stage = P15.local_dwell_per_stage
        planted_mod.causal_order = P15.causal_order
        exec(PLANT_CROSS_CLOCK_FOLD_SOURCE, planted_mod.__dict__)
        views_with_plant = tuple(sorted(P15.METABOLISM_VIEWS + ("_cross_clock_fold_plant",)))

        # green before the plant is counted
        self.assertEqual(P15.folding_views(P15.census()), [])

        # THE POSITIVE FIRES: the plant is present and reads as a fold.
        rows = P15.census(views=views_with_plant, module=planted_mod)
        folding = [r["view"] for r in P15.folding_views(rows)]
        self.assertIn("_cross_clock_fold_plant", folding,
                      "the planted cross-clock fold was NOT flagged — the positive control did not "
                      "fire, so this test proves nothing")
        self.assertEqual(len(rows), len(views_with_plant))          # complete WITH the plant

        # remove the plant: the census is green again — the finding class is kept, not defeated.
        self.assertEqual(P15.folding_views(P15.census()), [])


# =================================================================================================
# A4 — the send-time-claim value is absent (named, not minted; a raise riding P8 if ever needed).
# =================================================================================================

class TestA4SendTimeClaimAbsent(unittest.TestCase):

    def test_the_default_view_needs_no_send_time_claim(self):
        # the default ships local dwell + causal order; neither reads a sender-supplied send-time.
        # A receipt built for causal_order carries only the crossing's content hash — no send-time.
        submit = {"actor": "A", "action": "BORDER-SUBMIT", "object": "d", "target": "B",
                  "payload": {"body": "x"}}
        receipt = {"actor": "B", "action": "RECEIPT",
                   "payload": {"content_hash": border.content_id(submit)}}
        self.assertNotIn("send_time_claim", receipt["payload"])
        self.assertIsNotNone(P15.causal_order(submit, receipt))

    def test_the_module_mints_no_send_time_claim_value(self):
        # no founding param / field named for the send-time-claim is introduced here (it rides P8).
        src = P15._view_source("local_dwell_per_stage") + P15._view_source("causal_order")
        self.assertNotIn("send_time_claim", src)
        self.assertNotIn("send-time-claim", src)
        # and the stage pin adds no field at all (the send-time-claim would be a new field).
        self.assertEqual(P15.stage_pin_fields() - set(P15.KNOWN_RECORD_FIELDS), set())


if __name__ == "__main__":
    unittest.main()
