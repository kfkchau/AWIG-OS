"""EP-23 — the crossing: external answers as frozen inputs (+ the fingerprint check kind).

Every probe here is a regression test (the campaign method: a verification probe lands as
a test). The crossing is TWO RECORDS — a hand-out DECISION and an answer-returned INPUT —
plus a derived in-flight view computed from their difference. Nothing waits in memory: no
future, no callback registry, no in-band correlation token. The refused reference is
async RPC; taking it would erase replay of in-flight crossings, store-held correlation,
and the never-re-run-the-answerer law.

Coverage (the EP's named acceptance battery, plus the two failure directions):
  T-FP-CANONICAL          the serialization fuzz set — never two hashes for one state,
                          never one hash for two states (W3, proven BEFORE anything hashes).
  T-CONTEXT-PINNED        every hand-out records the four pins; a station definition
                          missing any pin field refuses at definition time.
  T-FP-HOLDS              untouched read-set across the crossing -> the answer is accepted
                          and the record carries the passed check.
  T-FP-STALE              mutate any pack input mid-crossing -> the return refuses citing
                          the staleness rule; re-judge fires within budget, parent-linked.
  T-FP-ORTHOGONAL-REFUSAL revoke the acting grant mid-crossing, read-set untouched ->
                          the fingerprint holds AND the gate refuses on authority.
  T-FP-ABA                write-then-revert inside the read-set -> executes (state-equal);
                          with an interval-guard declared per-station, the same case refuses.
  T-FP-REPLAY             kill everything derived, replay: every mint, check, stale-refusal
                          and re-judge reconstructs identically; the answerer is never re-run.
  T-CROSSING-REPLAY       kill the in-flight view mid-crossing, replay: the open crossing
                          reconstructs and the resume completes identically.
  T-CORRELATION-DERIVED   an answer citing no open hand-out refuses; an answer whose in-band
                          content claims another crossing binds BY THE CITATION.
  T-VAULT-CONSUMER        the stub channel presents the credential; the record proves use;
                          the standing no-read-path checks on the vault are unchanged.
  BOTH DIRECTIONS         too-weak (a mutated read-set that fails to refuse) and too-wedged
                          (an untouched read-set that refuses) are both explicit.
"""

import os
import sys
import tempfile
import unicodedata
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel import canonical  # noqa: E402


# ============================================================================================
# W3 — T-FP-CANONICAL: the serialization fuzz battery.
#
# The check is TCB-grade (design/34 §5): a non-canonical serializer manufactures false
# stales — or worse, false holds — invisibly. Its battery ships WITH the check, and it is
# written FIRST because everything else in this EP hashes with it.
#
# Two directions, both explicit:
#   (a) never two hashes for ONE state — key order, unicode encoding, list/tuple, frozen
#       mappings, -0.0 all fold to one hash;
#   (b) never one hash for TWO states — type tagging and length prefixing keep distinct
#       states distinct, and NO compatibility folding merges characters that differ.
# ============================================================================================

class TestCanonicalOneStateOneHash(unittest.TestCase):
    """(a) One state must never yield two hashes."""

    def test_key_order_does_not_move_the_hash(self):
        a = {"alpha": 1, "beta": 2, "gamma": 3}
        b = {"gamma": 3, "beta": 2, "alpha": 1}
        self.assertEqual(canonical.canonical_hash(a), canonical.canonical_hash(b))

    def test_nested_key_order_does_not_move_the_hash(self):
        a = {"outer": {"x": [1, {"p": 1, "q": 2}], "y": 2}}
        b = {"outer": {"y": 2, "x": [1, {"q": 2, "p": 1}]}}
        self.assertEqual(canonical.canonical_hash(a), canonical.canonical_hash(b))

    def test_unicode_encoding_normalizes_nfc_equals_nfd(self):
        # The SAME abstract character written two ways is ONE state. Without normalization
        # the two byte sequences hash apart and manufacture a false stale.
        nfc = unicodedata.normalize("NFC", "café")        # e + acute, composed
        nfd = unicodedata.normalize("NFD", "café")        # e followed by U+0301
        self.assertNotEqual(nfc, nfd)                          # genuinely different strings
        self.assertEqual(canonical.canonical_hash(nfc), canonical.canonical_hash(nfd))

    def test_unicode_normalization_applies_to_keys_too(self):
        nfc = unicodedata.normalize("NFC", "état")
        nfd = unicodedata.normalize("NFD", "état")
        self.assertEqual(canonical.canonical_hash({nfc: 1}), canonical.canonical_hash({nfd: 1}))

    def test_list_and_tuple_are_one_state(self):
        # The store DEEP-FREEZES records: lists become tuples. A pack hashed before and after
        # the freeze must be one state, or every crossing over a list-valued fold false-stales.
        self.assertEqual(canonical.canonical_hash(["a", "b"]), canonical.canonical_hash(("a", "b")))

    def test_frozen_mapping_and_dict_are_one_state(self):
        from types import MappingProxyType
        d = {"k": ["v", 1]}
        frozen = MappingProxyType({"k": ("v", 1)})
        self.assertEqual(canonical.canonical_hash(d), canonical.canonical_hash(frozen))

    def test_negative_zero_folds_to_zero(self):
        self.assertEqual(canonical.canonical_hash(-0.0), canonical.canonical_hash(0.0))

    def test_the_hash_is_stable_across_calls_and_carries_the_estate_prefix(self):
        v = {"a": [1, 2, {"b": None}]}
        self.assertEqual(canonical.canonical_hash(v), canonical.canonical_hash(v))
        self.assertTrue(canonical.canonical_hash(v).startswith("sha256:"))


class TestCanonicalTwoStatesTwoHashes(unittest.TestCase):
    """(b) Two states must never collide on one hash."""

    def test_int_float_bool_and_string_are_four_states(self):
        hashes = {canonical.canonical_hash(1), canonical.canonical_hash(1.0),
                  canonical.canonical_hash(True), canonical.canonical_hash("1")}
        self.assertEqual(len(hashes), 4, "type tagging must keep 1 / 1.0 / True / '1' apart")

    def test_none_is_not_the_string_null(self):
        self.assertNotEqual(canonical.canonical_hash(None), canonical.canonical_hash("null"))
        self.assertNotEqual(canonical.canonical_hash(None), canonical.canonical_hash("None"))

    def test_no_compatibility_folding_merges_distinct_characters(self):
        # NFKC would fold the ligature into "fi" — that MERGES two states and would be a false
        # HOLD (a changed pack hashing equal). Canonical composition (NFC) must not do it.
        self.assertNotEqual(canonical.canonical_hash("ﬁle"), canonical.canonical_hash("file"))

    def test_length_prefixing_defeats_delimiter_injection(self):
        # Without length-prefixed strings a concatenating serializer collides these.
        self.assertNotEqual(canonical.canonical_hash({"a": "b:c"}), canonical.canonical_hash({"a:b": "c"}))
        self.assertNotEqual(canonical.canonical_hash(["ab", "c"]), canonical.canonical_hash(["a", "bc"]))

    def test_nesting_is_not_flattened(self):
        self.assertNotEqual(canonical.canonical_hash([["a"], ["b"]]), canonical.canonical_hash([["a", "b"]]))
        self.assertNotEqual(canonical.canonical_hash({"a": {"b": 1}}), canonical.canonical_hash({"a": "b", "b": 1}))

    def test_empty_containers_are_distinct_states(self):
        hashes = {canonical.canonical_hash({}), canonical.canonical_hash([]),
                  canonical.canonical_hash(""), canonical.canonical_hash(0)}
        self.assertEqual(len(hashes), 4)

    def test_bytes_and_text_are_distinct_states(self):
        self.assertNotEqual(canonical.canonical_hash("ab"), canonical.canonical_hash(b"ab"))

    def test_float_precision_is_carried_not_rounded(self):
        self.assertNotEqual(canonical.canonical_hash(0.1 + 0.2), canonical.canonical_hash(0.3))


class TestCanonicalRefusesWhatItCannotCanonicalize(unittest.TestCase):
    """Fail loud, never guess (ST-A / P4): an uncanonicalizable value raises rather than
    hashing something approximate. A silent approximation here is invisible forever."""

    def test_non_finite_floats_refuse(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(canonical.NotCanonicalizable):
                canonical.canonical_hash(bad)

    def test_a_key_collision_created_by_normalization_refuses(self):
        # Two keys that are DIFFERENT strings but normalize to the SAME key would silently
        # drop one — one hash for two states. Refuse instead.
        nfc = unicodedata.normalize("NFC", "é")
        nfd = unicodedata.normalize("NFD", "é")
        with self.assertRaises(canonical.NotCanonicalizable):
            canonical.canonical_hash({nfc: 1, nfd: 2})

    def test_an_unsupported_type_refuses(self):
        for bad in ({1, 2}, object(), 1j):
            with self.assertRaises(canonical.NotCanonicalizable):
                canonical.canonical_hash(bad)


# ============================================================================================
# The crossing, end to end. One world, built the way a real station would be: a small
# purpose-built input view (least-context — a master would seal the whole rule set and
# flutter on every unrelated amendment), a station op that names an external executor, and
# a stub answerer that COUNTS ITS CALLS so "the answerer is never re-run" is measured rather
# than asserted.
# ============================================================================================

from kernel.compose import build_full_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel import crossing  # noqa: E402
from kernel.vault import VaultStore  # noqa: E402

OWNER = "owner"

#: A station's declaration. `executor` and `crossing` are op_definition DATA — which law
#: governs an op is read from the op's own record (the EP-16 authority-regime precedent),
#: never a code branch on the op's name.
STATION = {
    "description": "ask an executor outside the S-plane to review a budget line",
    "params": {"line": "required"},
    # `line` is the budget-line IDENTIFIER read inline by object_derive ("review:{line}") and
    # written to the payload — a structural governance field carrying no reachable content, so it
    # is affirmed STRUCTURAL (the vocabulary door, design/46 member 2). Content-homing it is
    # structurally impossible anyway: it is the object_param the derive reads inline.
    "structural_params": ["line"],
    "law_cited": "CAP-IS-LAW",
    "object_derive": {"tpl": "review:{line}"},
    "payload_from": ["line"],
    "executor": "external",
    "crossing": {"input_view": "view:budget-context",
                 "template": "tpl:budget-review@1.0.0",
                 "answerer_identity": "answerer:approver@1",
                 "parser": "parser:verdict-json@1"},
}


class StubAnswerer:
    """The executor outside the S-plane. It holds its own credential — the vault has no read
    path and none is added, so the value cannot come from there — and it COUNTS every time it
    is asked. That counter is the whole proof of the never-re-run law."""

    def __init__(self, verdict="approve", credential=None):
        self.verdict, self.credential = verdict, credential
        self.calls, self.presented = 0, []

    def present_credential(self):
        self.presented.append(self.credential)
        return self.credential

    def ask(self, question):
        self.calls += 1
        return self.verdict


class _World(unittest.TestCase):
    """A full kernel (blobs + vault), a pack view, a station, and the stub answerer."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        self.answerer = StubAnswerer()
        self.gate.execute("CREATE-OP", OWNER, {"name": "SET-BUDGET", "definition": {
            "description": "set a budget line", "params": {"name": "required", "amount": "required"},
            # `name` is the budget-line id read inline by object_derive ("budget:{name}"); `amount`
            # is a small numeric scalar (mirrors the production census's `size`/`ceiling`). Neither
            # carries reachable content — both STRUCTURAL (vocabulary door, design/46 member 2).
            "structural_params": ["name", "amount"],
            "law_cited": "CAP-IS-LAW", "object_derive": {"tpl": "budget:{name}"},
            "payload_from": ["name", "amount"]}})
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "budget-context", "when": {"object": "budget:ops"}})
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "budget-writes", "when": {"object": "budget:ops"}})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 5})
        self.gate.execute("CREATE-OP", OWNER, {"name": "ASK-REVIEW", "definition": STATION})

    # -- the channel adapter: the only thing that talks to the world outside ---------------
    def deliver(self, handout, channel):
        """Carry a hand-out to the external executor. Runs AFTER the hand-out is durably
        appended — the record is upstream of the effect, never a log of it (K1)."""
        p = dict(handout["payload"])
        if p.get("credential"):
            presented = channel.present_credential()
            self.gate.execute("PRESENT-CREDENTIAL", OWNER,
                              {"handout_seq": handout["seq"], "name": dict(p["credential"])["name"],
                               "candidate": presented})
        return channel.ask(p)

    def station(self, name, **crossing_overrides):
        d = dict(STATION, crossing=dict(STATION["crossing"], **crossing_overrides))
        self.gate.execute("CREATE-OP", OWNER, {"name": name, "definition": d})
        return name

    def refusals(self, rule=None):
        return [e for e in self.store.by_action("op-refused")
                if rule is None or e["rule_cited"] == rule]


# ---- T-CONTEXT-PINNED ----------------------------------------------------------------------

class TestContextPinned(_World):
    """Every hand-out records the four pins; a station definition missing any pin field
    refuses AT DEFINITION TIME. Version pinning on every external call is what keeps
    attribution real rather than nominal (wall primitive 5)."""

    def test_the_handout_records_all_four_pins(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        pins = dict(dict(h["payload"])["pins"])
        self.assertEqual(set(pins), {"template", "answerer_identity", "parser", "context"})
        self.assertEqual(pins["template"], "tpl:budget-review@1.0.0")
        self.assertEqual(pins["answerer_identity"], "answerer:approver@1")
        self.assertEqual(pins["parser"], "parser:verdict-json@1")
        # the fourth pin is the CONTEXT SNAPSHOT HASH — a measurement of the world, so it is
        # computed at hand-out and cannot be declared. It is the seal.
        self.assertEqual(pins["context"], h["payload"]["seal"])
        self.assertTrue(pins["context"].startswith("sha256:"))

    def test_the_pack_version_is_pinned_at_handout_not_declared(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        ref = h["payload"]["input_view"]
        self.assertTrue(ref.startswith("view:budget-context@"))
        self.assertEqual(int(ref.rsplit("@", 1)[1]), self.views.view_definitions()["budget-context"]["seq"])

    def test_a_station_missing_any_declared_pin_refuses_at_definition_time(self):
        for pin in ("template", "answerer_identity", "parser"):
            c = {k: v for k, v in STATION["crossing"].items() if k != pin}
            with self.assertRaises(OpError) as cm:
                self.gate.execute("CREATE-OP", OWNER, {"name": f"BAD-{pin}",
                                                       "definition": dict(STATION, crossing=c)})
            self.assertEqual(cm.exception.rule, "AR-2")
            self.assertFalse(self.gate.has(f"BAD-{pin}"))

    def test_a_station_with_an_unversioned_pin_refuses(self):
        c = dict(STATION["crossing"], template="tpl:budget-review")   # no @version
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-OP", OWNER, {"name": "BAD-UNVERSIONED",
                                                   "definition": dict(STATION, crossing=c)})

    def test_a_station_with_no_input_view_refuses(self):
        c = {k: v for k, v in STATION["crossing"].items() if k != "input_view"}
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-OP", OWNER, {"name": "BAD-NOPACK",
                                                   "definition": dict(STATION, crossing=c)})

    def test_an_unknown_executor_does_not_exist(self):
        # the closure discipline the check vocabulary already carries, applied to executors
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-OP", OWNER, {"name": "BAD-EXEC",
                                                   "definition": dict(STATION, executor="rpc")})

    def test_a_station_naming_an_undefined_input_view_refuses_at_hand_out(self):
        # accepted-but-cannot-honour REFUSES: a hand-out with no pack has no seal, so it is
        # unrecordable rather than recordable-and-unchecked.
        self.station("ASK-GHOST", input_view="view:nowhere")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ASK-GHOST", OWNER, {"line": "ops"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")

    def test_amending_a_station_revalidates_its_pins(self):
        bad = dict(STATION, crossing={k: v for k, v in STATION["crossing"].items() if k != "parser"})
        with self.assertRaises(OpError):
            self.gate.execute("AMEND-OP", OWNER, {"name": "ASK-REVIEW", "definition": bad})


# ---- T-FP-HOLDS + the too-wedged direction --------------------------------------------------

class TestFingerprintHolds(_World):
    """An untouched read-set across the crossing: the answer is accepted and the record
    carries the passed check."""

    def test_the_untouched_read_set_executes_and_the_record_carries_the_passed_check(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        verdict = self.deliver(h, self.answerer)
        a = self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": verdict})
        self.assertEqual(a["payload"]["fingerprint_check"], "pass")
        self.assertEqual(a["payload"]["fingerprint_seal"], h["payload"]["seal"])
        self.assertEqual(a["payload"]["record_class"], "INPUT")
        self.assertEqual(a["payload"]["answer"], "approve")
        self.assertEqual(self.views.crossings()[h["seq"]]["state"], "answered")

    def test_too_wedged_an_untouched_read_set_must_not_refuse(self):
        # The explicit second failure direction. A check that refuses a valid return wedges
        # the whole seam and is as broken as one that never refuses — it just fails quietly,
        # in the direction nobody tests.
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        for _ in range(3):
            self.gate.execute("CREATE-INFO", OWNER, {"content": "unrelated traffic"})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "other-line", "amount": 1})
        self.assertTrue(self.views.crossing_fingerprint(h["seq"])["holds"],
                        "writes OUTSIDE the read-set must not stale a crossing")
        a = self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(a["payload"]["fingerprint_check"], "pass")
        self.assertEqual(self.refusals("CROSSING-STALE"), [])

    def test_writes_outside_the_read_set_do_not_move_the_seal(self):
        # §1-necessity: state the answerer was never shown cannot invalidate its reasoning,
        # and invalidating on it would livelock the seam at operating-system rate.
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        before = self.views.crossing_fingerprint(h["seq"])["current_seal"]
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "noise", "when": {"action": "READ"}})
        self.gate.execute("CREATE-INFO", OWNER, {"content": "more noise"})
        self.assertEqual(self.views.crossing_fingerprint(h["seq"])["current_seal"], before)


# ---- T-FP-STALE + the too-weak direction ----------------------------------------------------

class TestFingerprintStale(_World):
    """Mutate any pack input mid-crossing: the return refuses citing the staleness rule, and
    a re-judge fires within budget, parent-linked."""

    def _stale_crossing(self, station="ASK-REVIEW"):
        h = self.gate.execute(station, OWNER, {"line": "ops"})
        self.deliver(h, self.answerer)
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})   # inside the read-set
        return h

    def test_too_weak_a_mutated_read_set_refuses_citing_the_staleness_rule(self):
        h = self._stale_crossing()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(cm.exception.rule, "CROSSING-STALE")
        r = self.refusals("CROSSING-STALE")[-1]
        self.assertEqual(r["payload"]["op"], "ANSWER-RETURNED")
        self.assertTrue(r["refused"])
        self.assertEqual(self.views.crossings()[h["seq"]]["state"], "open",
                         "a refused return does not close the crossing — nothing was answered")

    def test_the_stale_crossing_is_derived_not_read_off_the_refusal(self):
        # Staleness is a fact about the world, answerable before anyone tries to return and
        # after everyone stops. Nothing is stored, and no refusal record is parsed.
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.assertNotIn(h["seq"], self.views.stale_crossings())
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})
        self.assertIn(h["seq"], self.views.stale_crossings())
        self.assertEqual(self.refusals("CROSSING-STALE"), [],
                         "the crossing is stale though no one has tried to return")

    def test_the_rule_it_cites_is_a_record_not_a_constant(self):
        self.assertIn("CROSSING-STALE", self.views.active_rules())
        self.assertIn("CROSSING-CORRELATION", self.views.active_rules())

    def test_re_judge_fires_within_budget_and_is_parent_linked(self):
        h = self._stale_crossing()
        with self.assertRaises(OpError):
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        rs = crossing.retry_state(self.store, self.views, h["seq"])
        self.assertEqual((rs["policy"], rs["budget"], rs["spent"]), ("re-judge", 2, 0))
        fresh = crossing.re_judge(self.gate, self.store, self.views, OWNER, h["seq"])
        self.assertEqual(fresh["payload"]["parent_handout_seq"], h["seq"])
        self.assertEqual(fresh["payload"]["line"], "ops", "the question is re-asked from the RECORD")
        self.assertTrue(self.views.crossing_fingerprint(fresh["seq"])["holds"],
                        "the fresh crossing is minted at the CURRENT head")
        # the stale one is superseded, not answered and not lingering in flight
        self.assertEqual(self.views.crossings()[h["seq"]]["state"], "superseded")
        self.assertEqual(list(self.views.open_crossings()), [fresh["seq"]])

    def test_on_budget_exhaustion_the_stale_refusal_stands_and_the_case_surfaces(self):
        # Never silent execute; never silent drop (design/34 §4).
        h = self._stale_crossing()
        chain = [h]
        for amount in (11, 12):
            nxt = crossing.re_judge(self.gate, self.store, self.views, OWNER, chain[-1]["seq"])
            self.assertIsNotNone(nxt)
            chain.append(nxt)
            self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": amount})
        self.assertIsNone(crossing.re_judge(self.gate, self.store, self.views, OWNER, chain[-1]["seq"]),
                          "budget 2 buys exactly two re-judges")
        self.assertIn(chain[-1]["seq"], self.views.crossings_needing_reask())
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": chain[-1]["seq"], "answer": "approve"})
        self.assertEqual(cm.exception.rule, "CROSSING-STALE")

    def test_a_station_may_name_its_own_recorded_budget(self):
        # A retry budget is recorded policy with a named owner, never a constant in code.
        self.gate.execute("CREATE-RULE", OWNER, {
            "rule_id": "ASK-REVIEW-BUDGET", "polarity": "+", "text": "no retries for this station",
            "policy_key": "crossing-retry-budget:ASK-REVIEW", "value": 0})
        h = self._stale_crossing()
        self.assertEqual(crossing.retry_state(self.store, self.views, h["seq"])["budget"], 0)
        self.assertIsNone(crossing.re_judge(self.gate, self.store, self.views, OWNER, h["seq"]))

    def test_an_abort_policy_never_re_judges(self):
        self.gate.execute("CREATE-RULE", OWNER, {
            "rule_id": "ASK-REVIEW-STALE-POLICY", "polarity": "+", "text": "abort on stale",
            "policy_key": "crossing-stale-policy:ASK-REVIEW", "value": "abort"})
        h = self._stale_crossing()
        self.assertIsNone(crossing.re_judge(self.gate, self.store, self.views, OWNER, h["seq"]))
        self.assertIn(h["seq"], self.views.crossings_needing_reask())

    def test_flutter_is_surfaced_as_a_view(self):
        # A pack whose inputs move faster than answer latency is a DESIGN SMELL to be seen,
        # never a reason to weaken the check (design/34 §4).
        h = self._stale_crossing()
        crossing.re_judge(self.gate, self.store, self.views, OWNER, h["seq"])
        self.assertEqual(self.views.crossing_flutter(), {"ASK-REVIEW": 1})


# ---- T-FP-ORTHOGONAL-REFUSAL ----------------------------------------------------------------

class TestOrthogonalRefusal(_World):
    """Revoke the acting grant mid-crossing with the read-set untouched: the fingerprint
    HOLDS and the gate refuses on AUTHORITY. Two verdicts, two rules, never merged — and
    staleness is never claimed for what is really a revocation."""

    def _narrow_the_world(self):
        # A DISPOSABLE test world, narrowed inside itself: the world at large stays open.
        self.gate.execute("REVOKE", OWNER, {"grant_id": "founding-openness"})
        self.gate.execute("GRANT", OWNER, {"grant_id": "answer-grant", "grantee": "approver",
                                           "actions": ["ANSWER-RETURNED"], "info": ["crossing-answer"],
                                           "space": "space:root"})

    def test_a_revoked_chain_refuses_on_authority_while_the_seal_holds(self):
        self._narrow_the_world()
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.deliver(h, self.answerer)
        self.gate.execute("REVOKE", OWNER, {"grant_id": "answer-grant"})   # mid-crossing
        self.assertTrue(self.views.crossing_fingerprint(h["seq"])["holds"],
                        "the judged world did not move — this is an authority failure, not staleness")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", "approver", {"handout_seq": h["seq"], "answer": "approve"})
        self.assertIn(cm.exception.rule, ("ROOT-NEG-1", "ROOT-NEG-3"))
        self.assertEqual(self.refusals("CROSSING-STALE"), [], "staleness is never claimed here")
        self.assertTrue(self.refusals("ROOT-NEG-1") or self.refusals("ROOT-NEG-3"))

    def test_the_same_crossing_answers_lawfully_while_the_grant_stands(self):
        # Proves the column can pass, so the refusal above is the revocation and not the setup.
        self._narrow_the_world()
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        a = self.gate.execute("ANSWER-RETURNED", "approver", {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(a["payload"]["fingerprint_check"], "pass")

    def test_stale_and_revoked_are_two_separately_observable_verdicts(self):
        self._narrow_the_world()
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.gate.execute("REVOKE", OWNER, {"grant_id": "answer-grant"})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})
        # Both are true at once, and both are answerable WITHOUT attempting the act — which
        # is what "neither substitutes" means when only one refusal can be recorded per call.
        self.assertFalse(self.views.crossing_fingerprint(h["seq"])["holds"])
        self.assertFalse(self.views.covers("approver", "ANSWER-RETURNED", "crossing-answer", "space:root"))


# ---- T-FP-ABA -------------------------------------------------------------------------------

class TestABA(_World):
    """Write-then-revert inside the read-set EXECUTES: fingerprint equality is state-equality,
    not history-equality. With an interval guard declared per station, the same case refuses."""

    def test_write_then_revert_inside_the_read_set_executes(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})
        self.assertFalse(self.views.crossing_fingerprint(h["seq"])["holds"])   # moved away
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 5})   # and back
        self.assertTrue(self.views.crossing_fingerprint(h["seq"])["holds"])
        a = self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(a["payload"]["fingerprint_check"], "pass")

    def test_the_excursion_stays_on_the_record_for_audit(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 5})
        amounts = [(e.get("payload") or {}).get("amount") for e in self.store.by_action("SET-BUDGET")]
        self.assertEqual(amounts, [5, 9, 5], "state returned; history did not, and says so")

    def test_with_an_interval_guard_declared_the_same_case_refuses(self):
        self.station("ASK-REVIEW-GUARDED", interval_guard="view:budget-writes")
        h = self.gate.execute("ASK-REVIEW-GUARDED", OWNER, {"line": "ops"})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 5})
        self.assertTrue(self.views.crossing_fingerprint(h["seq"])["holds"],
                        "the SEAL still holds — path-sensitivity is not folded into it")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(cm.exception.rule, "CROSSING-STALE")
        self.assertIn("interval guard", cm.exception.message)

    def test_the_interval_guard_is_off_by_default(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.assertIsNone(crossing.interval_moved(self.store, h["seq"]))

    def test_a_guarded_station_with_a_quiet_interval_still_executes(self):
        self.station("ASK-REVIEW-QUIET", interval_guard="view:budget-writes")
        h = self.gate.execute("ASK-REVIEW-QUIET", OWNER, {"line": "ops"})
        a = self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(a["payload"]["fingerprint_check"], "pass")


# ---- T-CORRELATION-DERIVED ------------------------------------------------------------------

class TestCorrelationIsTheStores(_World):
    """The store binds request to response by records citing records. An in-band token proves
    nothing, because nothing binds it to the hand-out except the store's own record."""

    def test_an_answer_citing_no_hand_out_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": 999999, "answer": "approve"})
        self.assertEqual(cm.exception.rule, "CROSSING-CORRELATION")

    def test_an_answer_citing_a_record_that_is_not_a_hand_out_refuses(self):
        other = self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 7})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": other["seq"], "answer": "approve"})
        self.assertEqual(cm.exception.rule, "CROSSING-CORRELATION")

    def test_a_crossing_may_be_answered_only_once(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "reject"})
        self.assertEqual(cm.exception.rule, "CROSSING-CORRELATION")

    def test_a_superseded_crossing_refuses_a_late_answer(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})
        crossing.re_judge(self.gate, self.store, self.views, OWNER, h["seq"])
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 5})   # restore the old seal
        self.assertTrue(self.views.crossing_fingerprint(h["seq"])["holds"])
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(cm.exception.rule, "CROSSING-CORRELATION",
                         "a re-judged crossing is closed by supersession, not by staleness")

    def test_the_in_band_claim_never_binds_the_citation_does(self):
        a_h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        b_h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        # the answer's own content claims crossing B; its CITATION names crossing A
        a = self.gate.execute("ANSWER-RETURNED", OWNER, {
            "handout_seq": a_h["seq"], "answer": "approve", "claimed_crossing": b_h["seq"]})
        self.assertEqual(a["payload"]["claimed_crossing"], b_h["seq"])   # the claim is recorded
        self.assertEqual(self.views.crossings()[a_h["seq"]]["state"], "answered")
        self.assertEqual(self.views.crossings()[b_h["seq"]]["state"], "open",
                         "the claim moved nothing — the store's citation is the whole binding")

    def test_the_leash_is_at_the_chokepoint_so_another_op_cannot_reach_past_it(self):
        # The EP-18 R-A shape: a leash inside one op's handler is bypassed by any other op
        # minting the same record shape. This op declares NO fingerprint check and mints an
        # answer-kind record; the gate refuses it anyway.
        self.gate.execute("CREATE-OP", OWNER, {"name": "SNEAK-ANSWER", "definition": {
            "description": "an op that mints an answer-shaped record without declaring the check",
            "params": {"handout_seq": "required", "answer": "required"},
            # ADMIT op (the CREATE-OP must succeed; the gate then refuses the EXECUTION on
            # CROSSING-STALE). Mirrors the production ANSWER-RETURNED census: `handout_seq` is a
            # record-seq citation and `answer` is a small verdict token — both STRUCTURAL.
            "structural_params": ["handout_seq", "answer"],
            "law_cited": "CROSSING-CORRELATION", "payload_from": ["handout_seq", "answer"],
            "payload_derive": {"kind": {"tpl": "crossing-answer"}}}})
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("SNEAK-ANSWER", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(cm.exception.rule, "CROSSING-STALE")
        self.assertEqual(self.views.crossings()[h["seq"]]["state"], "open")
        # and the same op cannot bind a non-existent crossing either
        with self.assertRaises(OpError) as cm2:
            self.gate.execute("SNEAK-ANSWER", OWNER, {"handout_seq": 999999, "answer": "approve"})
        self.assertEqual(cm2.exception.rule, "CROSSING-CORRELATION")


# ---- T-CROSSING-REPLAY and T-FP-REPLAY ------------------------------------------------------

class TestReplay(_World):
    """Kill everything derived, replay from the record file alone, reconstruct identically —
    and never re-run the answerer. A future dies with its process; a record does not."""

    def _rebuild(self):
        """A second kernel over the SAME record file: a fresh registry, fresh views, fresh
        everything derived. Nothing of this session's memory crosses over."""
        return build_full_kernel(self.record, os.path.join(self.dir, "blobs2"),
                                 os.path.join(self.dir, "vault"))

    def test_an_open_crossing_reconstructs_and_the_resume_completes_identically(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.deliver(h, self.answerer)
        self.assertEqual(self.answerer.calls, 1)
        before = self.views.open_crossings()

        store2, gate2, views2, _, _ = self._rebuild()
        self.assertEqual(list(views2.open_crossings()), list(before))
        self.assertEqual(views2.crossings()[h["seq"]]["seal"], h["payload"]["seal"])
        self.assertTrue(views2.crossing_fingerprint(h["seq"])["holds"])
        # the resume completes on the REBUILT machine, from the record alone
        a = gate2.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(a["payload"]["fingerprint_check"], "pass")
        self.assertEqual(self.answerer.calls, 1, "replay never re-runs the answerer")

    def test_every_mint_check_stale_refusal_and_re_judge_reconstructs_identically(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.deliver(h, self.answerer)
        self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 9})
        with self.assertRaises(OpError):
            self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        fresh = crossing.re_judge(self.gate, self.store, self.views, OWNER, h["seq"])
        self.deliver(fresh, self.answerer)
        self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": fresh["seq"], "answer": "approve"})
        snapshot = self.views.crossings()

        store2, gate2, views2, _, _ = self._rebuild()
        self.assertEqual(views2.crossings(), snapshot)
        self.assertEqual(views2.crossing_flutter(), self.views.crossing_flutter())
        self.assertEqual(views2.crossings_needing_reask(), self.views.crossings_needing_reask())
        # the seals are DERIVABLE from the record by replay — the mint can be proven honest
        for seq, c in snapshot.items():
            self.assertEqual(crossing.seal_of(store2, views2, c["input_view"], seq), c["seal"])

    def test_the_answer_is_consumed_as_input_and_the_answerer_is_never_re_invoked(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        verdict = self.deliver(h, self.answerer)
        self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": verdict})
        self.assertEqual(self.answerer.calls, 1)
        for _ in range(3):
            store2, gate2, views2, _, _ = self._rebuild()
            self.assertEqual(views2.crossings()[h["seq"]]["state"], "answered")
            answer = [e for e in store2.all()
                      if (e.get("payload") or {}).get("kind") == "crossing-answer"][0]
            self.assertEqual(answer["payload"]["answer"], "approve")
            self.assertEqual(answer["payload"]["record_class"], "INPUT")
        self.assertEqual(self.answerer.calls, 1,
                         "three replays, zero re-calls — the frozen answer IS the input")

    def test_nothing_holds_the_crossing_between_calls(self):
        # The refused reference, tested structurally: no dict of open crossings anywhere. The
        # module carries no mutable state, and the in-flight answer is a difference between
        # records that a brand-new Views object computes with no help from this one.
        from kernel import views as views_mod
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        module_state = [n for n, v in vars(crossing).items()
                        if not n.startswith("_") and isinstance(v, (dict, list, set))]
        self.assertEqual(module_state, [], f"kernel.crossing holds no mutable module state: {module_state}")
        fresh_views = views_mod.Views(self.store)
        self.assertEqual(fresh_views.open_crossings(), self.views.open_crossings())
        self.assertEqual(list(fresh_views.open_crossings()), [h["seq"]])


# ---- T-VAULT-CONSUMER -----------------------------------------------------------------------

class TestVaultConsumer(_World):
    """The vault finds its consumer. A crossing is handed out under a SEALED credential; the
    channel presents it; the vault compares BY HASH inside the S-plane; the record proves the
    use happened. No actor reads the value, and no read path is added — the presentation is
    possible precisely BECAUSE the check is a comparison rather than a retrieval."""

    CRED = "answerer-api-key-UNIQUE-4b81c"

    def setUp(self):
        super().setUp()
        self.gate.execute("SEAL-SECRET", OWNER, {"name": "answerer-key", "value": self.CRED})
        self.station("ASK-REVIEW-CRED", credential="answerer-key")
        self.answerer = StubAnswerer(credential=self.CRED)

    def test_the_hand_out_pins_the_credential_by_its_sealed_hash(self):
        h = self.gate.execute("ASK-REVIEW-CRED", OWNER, {"line": "ops"})
        cred = dict(h["payload"]["credential"])
        self.assertEqual(cred["name"], "answerer-key")
        self.assertEqual(cred["secret_hash"], self.views.sealed_secret_hash("answerer-key", "space:root"))

    def test_the_channel_presents_it_and_the_record_proves_the_use(self):
        h = self.gate.execute("ASK-REVIEW-CRED", OWNER, {"line": "ops"})
        self.deliver(h, self.answerer)
        self.assertEqual(self.answerer.presented, [self.CRED], "the channel presented the credential")
        self.assertTrue(self.views.crossings()[h["seq"]]["credential_verified"])
        proof = [e for e in self.store.all()
                 if (e.get("payload") or {}).get("kind") == "crossing-credential"][0]
        self.assertEqual(proof["payload"]["result"], "MATCH")
        self.assertEqual(proof["payload"]["handout_seq"], h["seq"])
        self.assertEqual(proof["rule_cited"], "CONST-SECRETS")

    def test_the_value_never_reaches_the_record(self):
        h = self.gate.execute("ASK-REVIEW-CRED", OWNER, {"line": "ops"})
        self.deliver(h, self.answerer)
        with open(self.record) as f:
            self.assertNotIn(self.CRED, f.read(), "the credential is grep-absent from the record")

    def test_a_wrong_credential_is_recorded_as_no_match_never_as_the_value(self):
        h = self.gate.execute("ASK-REVIEW-CRED", OWNER, {"line": "ops"})
        self.deliver(h, StubAnswerer(credential="not-the-key"))
        self.assertFalse(self.views.crossings()[h["seq"]]["credential_verified"])
        with open(self.record) as f:
            self.assertNotIn("not-the-key", f.read())

    def test_a_station_naming_an_unsealed_credential_refuses_rather_than_handing_out(self):
        self.station("ASK-REVIEW-GHOSTCRED", credential="never-sealed")
        with self.assertRaises(OpError) as cm:
            self.gate.execute("ASK-REVIEW-GHOSTCRED", OWNER, {"line": "ops"})
        self.assertEqual(cm.exception.rule, "CONST-SECRETS")

    def test_a_credential_presentation_must_cite_an_open_crossing(self):
        h = self.gate.execute("ASK-REVIEW-CRED", OWNER, {"line": "ops"})
        self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("PRESENT-CREDENTIAL", OWNER, {"handout_seq": h["seq"],
                                                            "name": "answerer-key", "candidate": self.CRED})
        self.assertEqual(cm.exception.rule, "CROSSING-CORRELATION")

    def test_the_standing_no_read_path_checks_are_unchanged(self):
        # Re-run here, not merely relied upon: this EP is the vault's first non-verification
        # consumer, and the whole point is that consuming it added no way to read it.
        vault = VaultStore(os.path.join(self.dir, "vault"))
        for banned in ("get", "read", "reveal", "open", "has", "value", "plaintext", "present"):
            self.assertFalse(hasattr(vault, banned))
        methods = {n for n in dir(vault) if not n.startswith("_") and callable(getattr(vault, n))}
        self.assertEqual(methods, {"seal", "compare"})
        with open(os.path.join(os.path.dirname(__file__), "..", "src", "kernel", "vault.py")) as f:
            src = f.read()
        for reader in ("read_bytes", "read_text", ".read(", "def get", "def read", "def reveal", "def open"):
            self.assertNotIn(reader, src)


# ---- the seam's own shape -------------------------------------------------------------------

class TestTheSeamsShape(_World):
    """The properties that make this a crossing rather than an RPC."""

    def test_the_station_kind_is_data_not_a_code_branch(self):
        # An ordinary op and a station differ ONLY by what their definition records say.
        ordinary = self.gate.execute("SET-BUDGET", OWNER, {"name": "ops", "amount": 6})
        station = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.assertNotIn("kind", dict(ordinary["payload"]))
        self.assertEqual(station["payload"]["kind"], "crossing-handout")
        d = self.views.op_definitions()["ASK-REVIEW"]["definition"]
        self.assertEqual(d["executor"], "external")

    def test_a_station_appends_exactly_one_record_and_runs_no_handler_to_completion(self):
        before = len(self.store.all())
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        self.assertEqual(len(self.store.all()), before + 1)
        self.assertEqual(h["action"], "ASK-REVIEW")
        self.assertEqual(h["payload"]["record_class"], "DECISION")
        self.assertEqual(h["rule_cited"], "CAP-IS-LAW")
        self.assertEqual(self.answerer.calls, 0, "the hand-out precedes the external call")

    def test_the_crossing_is_two_records_and_a_derived_difference(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        a = self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        family = [e for e in self.store.all()
                  if (e.get("payload") or {}).get("kind", "").startswith("crossing-")]
        self.assertEqual([e["seq"] for e in family], [h["seq"], a["seq"]])

    def test_the_fingerprint_joins_the_check_vocabulary(self):
        from kernel.opdefs import OP_CHECKS
        self.assertIn("fingerprint", OP_CHECKS)
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-OP", OWNER, {"name": "BAD-CHECK", "definition": {
                "description": "x", "params": {}, "law_cited": "CAP-IS-LAW",
                "checks": [{"check": "fingerprint-ish"}]}})

    def test_the_pack_is_pinned_to_the_version_the_answerer_was_shown(self):
        h = self.gate.execute("ASK-REVIEW", OWNER, {"line": "ops"})
        pinned = h["payload"]["input_view"]
        # amend the view AFTER hand-out: the return recomputes under the SAME pack version,
        # so a later definition of the same name does not silently change the question.
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "budget-context", "when": {"action": "READ"}})
        self.assertNotEqual(self.views.view_definitions()["budget-context"]["seq"],
                            int(pinned.rsplit("@", 1)[1]))
        self.assertTrue(self.views.crossing_fingerprint(h["seq"])["holds"])
        a = self.gate.execute("ANSWER-RETURNED", OWNER, {"handout_seq": h["seq"], "answer": "approve"})
        self.assertEqual(a["payload"]["fingerprint_check"], "pass")

    def test_a_master_bound_view_may_also_be_a_pack(self):
        # Both view shapes work as packs; a master seals derived STATE (and would flutter, which
        # is why a real station uses a narrow purpose-built view — see crossing_flutter).
        self.gate.execute("CREATE-VIEW", OWNER, {"name": "roles-pack", "bind": "actors"})
        self.station("ASK-ON-ACTORS", input_view="view:roles-pack")
        h = self.gate.execute("ASK-ON-ACTORS", OWNER, {"line": "ops"})
        self.assertTrue(self.views.crossing_fingerprint(h["seq"])["holds"])
        self.gate.execute("CREATE-ACTOR", OWNER, {"actor_id": "newcomer", "role": "worker"})
        self.assertFalse(self.views.crossing_fingerprint(h["seq"])["holds"])

    def test_the_two_new_rules_and_two_policies_are_founding_records(self):
        rules = self.views.active_rules()
        for rid in ("CROSSING-CORRELATION", "CROSSING-STALE",
                    "CROSSING-STALE-POLICY", "CROSSING-RETRY-BUDGET"):
            self.assertIn(rid, rules)
        self.assertEqual(self.views.policy_value("crossing-stale-policy-default"), "re-judge")
        self.assertEqual(self.views.policy_value("crossing-retry-budget-default"), 2)
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and the flip chain above stops here.]
        # ASSERTED: a FROZEN LITERAL "1.17.0", last set 2026-08-05 (EP-28N AMENDMENT 1).
        # SUPERSEDED: EP-28S landed the identity law on 2026-08-08; founding 1.17.0 -> 1.18.0.
        #   Fifth rewrite of this literal. A version literal in a test is a STORED COPY OF A
        #   COMPUTABLE VALUE, so every lawful bump reds a row that was never about the bump.
        # REMAINS TRUE, separated out and STILL ASSERTED: this row's SUBJECT is that the two
        #   rules and two policies are FOUNDING RECORDS — asserted above and untouched. The
        #   version clause is a floor (never backwards) plus THE READER AND THE RECORD
        #   AGREEING: the pack on disk versus the designation the installer stamped into
        #   FOUND-STORE. The FOUND-STORE half is ADDED here rather than removed, because this
        #   row previously had only the one reader and one reader cannot corroborate itself.
        # GIVEN UP: this row no longer notices a bump — never its job; EP-28N2 holds that
        #   against a PINNED before-side.
        from founding.install import founding_version
        v = founding_version()
        self.assertGreaterEqual(tuple(int(n) for n in v.split(".")), (1, 17, 0))
        fs = self.store.by_action("FOUND-STORE")[0]
        self.assertEqual((fs.get("payload") or {}).get("founding_version"), v)


if __name__ == "__main__":
    unittest.main()
