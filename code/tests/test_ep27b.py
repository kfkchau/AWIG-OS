"""EP-27B — the router's required-or-defaulted distinction, and K7 made reachable.

Every probe here is a regression test (the campaign method: a verification probe lands as a
test).

WHAT THIS EP CLOSES. `design/36` ADDENDUM F.2: the two-times machinery is built and proven and
CANNOT FIRE THROUGH THE SHIPPED FOUNDING, because the envelope router refuses when its declared
parameter is absent — correct for an observer pin that must always be present, and wrong for
`CREATE-RULE`, where declaring it would make every existing caller nonconforming. So K7 reads
"two times govern every crossing" while today they govern every crossing that can be EXPRESSED.
One distinction in a declaration closes that, and closes EP-25's R-1 with it.

THE REFERENCE THIS BATTERY EXISTS TO REFUSE is "defaulted" sliding into "does not matter". A
distinction between required and defaulted becomes, in practice, a distinction between required
and IGNORED — and the place it would show is EP-22's three observer pins, which must still
refuse on absence or an observation's provenance becomes best-effort. Two rows below are that
detector and nothing else: T-SILENCE-MEANS-REQUIRED (an op that says nothing gets today's
behaviour) and T-EXISTING-PINS-STILL-REFUSE (asserted directly, never inferred from the suite
staying green).

Coverage (the EP's named battery):
  T-K7-FIRES-IN-THE-LIVE-WORLD        the row this EP exists for: a law-family record submitted
                                      through a SHIPPED founding op carrying a deciding time
                                      that precedes recorded acts; the sweep runs; overturns are
                                      appended; the record reconciles. No AMEND-OP, no
                                      disposable world, nothing test-only in the path.
  T-SILENCE-MEANS-REQUIRED            silence in a declaration is REQUIRED, per router, and an
                                      absent parameter refuses, cited and recorded.
  T-EXISTING-PINS-STILL-REFUSE        EP-22's three observer pins still refuse on absence.
  T-DEFAULTED-FALLS-BACK-TO-THE-ENVELOPE  a defaulted declaration with an absent parameter takes
                                      the store's own value and NOTHING else. Both columns
                                      proven able to fail.
  T-ROUTER-FAMILY-STILL-ONE-FAMILY    the distinction is expressed the same way across the
                                      members that carry it, read by one parser, with no special
                                      case for the ops this EP touches.
  T-R1-CLOSED                         the five inherited files ops declare `provenance_param`
                                      and carry port evidence when a port supplied it, while
                                      their pre-existing engine caller stays conforming.
  T-DEGENERATE-IDENTITY               an op declaring no router, and an op declaring one and
                                      supplying it, are byte-for-byte what they were.

ADDENDUM 2 (2026-07-28) replaced W6 — a definition-time refusal of `param_defaults` beside a
router — with the root fix and the door the traffic actually uses. Its battery:
  T-ROUTERS-READ-ONE-MAP              every member that names a caller parameter reads the RAW
                                      parameters, so `param_defaults` cannot reach any envelope
                                      field. Per member, behavioural, family-complete.
  T-A-DEFAULT-CANNOT-REACH-A-ROUTER   the exact combination the stopped session ran: a required
                                      pin refuses as declared and a defaulted one takes the
                                      store's mint, not the author's constant.
  T-SHM-GRANT-IS-UNCHANGED            the canary — the one shipped op pairing a default with a
                                      router records byte-for-byte what it recorded before.
  T-THE-FOUNDING-DOOR-VALIDATES       the third door runs the same shape vocabulary as the other
                                      two; a malformed pack refuses the whole founding, cited.
  T-THE-SHIPPED-FOUNDING-IS-CLEAN     standing, over the whole pack, every suite run.
"""

import copy
import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from founding import install as install_module  # noqa: E402
from founding.install import (  # noqa: E402
    FoundingIntegrityError, _validate, load_pack, records as _records,
)
from kernel import opdefs, reconcile  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.store import EventStore  # noqa: E402
from observe.seam import PIN_PARAMS, ObservationSeam, register_observe_ops  # noqa: E402

OWNER = "owner"

#: A caller-supplied value that is neither the store's mint nor anything the store could invent.
WHEN = "2019-03-04T05:06:07+00:00"
PROV = {"asserted_by": "window:proc@m1.1", "source": "observation", "could_read": []}

#: The five campaign-1 files ops EP-25 could not complete (its R-1). Named here rather than
#: computed, because the row asserts a fact about exactly these five.
INHERITED_FILES_OPS = ("FILE-CREATE", "FILE-WRITE", "FILE-LINK", "FILE-UNLINK", "FILE-PERM")


def _iso(delta_seconds):
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=delta_seconds)).isoformat()


class _Live(unittest.TestCase):
    """A kernel composed from the SHIPPED founding and nothing else.

    No `AMEND-OP`, no seeded test op, no narrowed world. Every row that claims something about
    the live world uses this base and asserts the absence of an amendment in its own path."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        self.founding_end = self.views.founding_prefix_end()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def post_founding(self, *actions):
        return [e for e in self.store.events
                if e["seq"] > self.founding_end and e["action"] in actions]

    def definition(self, name):
        return (self.views.op_definitions().get(name) or {}).get("definition") or {}


class _TestWorld(_Live):
    """The same live kernel, plus ops this battery CREATES to exercise the declaration grammar
    on op names the founding has never heard of. Creating an op is an ordinary governed act;
    the distinction between this base and `_Live` is that rows here make no claim about the
    shipped world, only about the mechanism."""

    def define(self, name, **extra):
        d = {"law_cited": "CAP-IS-LAW", "description": "a test-world op",
             "params": {"subject": "required"}, "object_param": "subject",
             "payload_from": ["subject"], "structural_params": ["subject"]}
        d.update(extra)
        self.gate.execute("CREATE-OP", OWNER, {"name": name, "definition": d})
        return d

    def refuses(self, name, params, rule="AR-2"):
        """Invoke and assert the refusal is CITED, RECORDED, and wrote no decision."""
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as raised:
            self.gate.execute(name, OWNER, params)
        self.assertEqual(raised.exception.rule, rule)
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        self.assertEqual(self.store.by_action(name), [])
        return raised.exception


# =============================================================================================
# T-K7-FIRES-IN-THE-LIVE-WORLD — the row this EP exists for
# =============================================================================================

class TestK7FiresInTheLiveWorld(_Live):
    """Under today's founding this class CANNOT pass, and that is the evidence the cap was real
    rather than theoretical (design/36 ADDENDUM F.2)."""

    def submit_late_law(self, rule_id, decided_at, when):
        return self.gate.execute("CREATE-RULE", OWNER, {
            "rule_id": rule_id, "occurrence_time": decided_at, "polarity": "-",
            "when": when, "then": [{"refuse": rule_id}]})

    def test_a_shipped_law_op_carries_a_deciding_time_that_precedes_its_arrival(self):
        decided = _iso(-3600)
        rule = self.submit_late_law("NO-INFO-A", decided, [{"action": "CREATE-INFO"}])
        self.assertEqual(rule["occurrence_time"], decided)
        self.assertLess(rule["occurrence_time"], rule["record_time"])
        self.assertTrue(reconcile.is_law_family(rule))

    def test_the_sweep_fires_and_appends_overturns_through_the_shipped_founding(self):
        act = self.gate.execute("CREATE-INFO", OWNER, {"content": "info:budget-line"})
        rule = self.submit_late_law("NO-INFO-B", _iso(-3600), [{"action": "CREATE-INFO"}])

        sweep = self.gate.sweeps[-1]
        self.assertEqual(sweep["law_seq"], rule["seq"])
        self.assertIsNone(sweep["refused"])
        self.assertNotIn("skipped", sweep)
        self.assertEqual(sorted(reconcile.overturned_targets(self.store)), [act["seq"]])
        self.assertEqual(len(sweep["committed"]), 1)

        overturn = self.store.by_seq(sweep["committed"][0])
        self.assertEqual(overturn["action"], "OVERTURN")
        self.assertEqual(dict(overturn["payload"])["reaching_seq"], rule["seq"])

    def test_the_record_reconciles_and_the_original_act_is_still_on_it(self):
        act = self.gate.execute("CREATE-INFO", OWNER, {"content": "info:reconciled"})
        self.submit_late_law("NO-INFO-C", _iso(-3600), [{"action": "CREATE-INFO"}])
        self.assertFalse(self.views.standing(act["seq"]))
        # append-only stands: the act itself was never rewritten
        self.assertEqual(self.store.by_seq(act["seq"])["object"], "info:reconciled")
        self.assertNotIn("refused", self.store.by_seq(act["seq"]))

    def test_nothing_test_only_and_no_amendment_was_in_the_path(self):
        """The row's own honesty check. If this EP had reached K7 by amending an op, or by
        seeding one, the sweep above would prove nothing about the shipped world."""
        act = self.gate.execute("CREATE-INFO", OWNER, {"content": "info:clean-path"})
        self.submit_late_law("NO-INFO-D", _iso(-3600), [{"action": "CREATE-INFO"}])
        self.assertEqual(self.post_founding("AMEND-OP", "CREATE-OP", "RETIRE-OP"), [])
        self.assertEqual(sorted(reconcile.overturned_targets(self.store)), [act["seq"]])
        # and the op that carried the deciding time is the founding's own, unamended: the live
        # definition is the pack document's, to the byte (the live copy is frozen, so both sides
        # are normalised through the serializer rather than compared as Python objects)
        self.assertEqual(json.dumps(self.definition("CREATE-RULE"), sort_keys=True, default=dict),
                         json.dumps(self.pack_definition("CREATE-RULE"), sort_keys=True))

    def pack_definition(self, name):
        """The op's definition AS WRITTEN IN THE PACK DOCUMENT, found by walking the pack rather
        than by knowing its shape — so the row compares the live registry against the shipped
        source and not against a second copy of the same assumption."""
        from founding.install import load_pack

        def walk(node):
            if isinstance(node, dict):
                if node.get("kind") == "op_definition" and node.get("name") == name:
                    yield node["definition"]
                for value in node.values():
                    yield from walk(value)
            elif isinstance(node, list):
                for value in node:
                    yield from walk(value)

        found = list(walk(load_pack()))
        self.assertEqual(len(found), 1, f"{name} is not in the founding pack exactly once")
        return found[0]

    def test_the_law_family_op_still_works_with_no_deciding_time_given(self):
        """Every existing caller stays conforming — the reason the distinction had to exist."""
        rule = self.gate.execute("CREATE-RULE", OWNER, {
            "rule_id": "PLAIN-LAW", "policy_key": "test:plain", "value": 1})
        self.assertGreaterEqual(rule["occurrence_time"], rule["record_time"])
        self.assertEqual(self.gate.sweeps, [])
        self.assertEqual(reconcile.overturned_targets(self.store), set())

    def test_the_sweep_survives_replay_from_the_record_file_alone(self):
        act = self.gate.execute("CREATE-INFO", OWNER, {"content": "info:replayed"})
        self.submit_late_law("NO-INFO-E", _iso(-3600), [{"action": "CREATE-INFO"}])
        store2, _g2, views2, _b2, _s2 = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs2"), os.path.join(self.dir, "vault2"))
        self.assertEqual(sorted(reconcile.overturned_targets(store2)), [act["seq"]])
        self.assertFalse(views2.standing(act["seq"]))


# =============================================================================================
# T-SILENCE-MEANS-REQUIRED — silence can never weaken an existing pin
# =============================================================================================

class TestSilenceMeansRequired(_TestWorld):

    def params_for(self, router):
        """The parameter this router routes, plus a value only a caller could have supplied."""
        return {"occurrence_time_param": ("at", WHEN), "provenance_param": ("prov", PROV)}[router]

    def test_a_bare_declaration_still_refuses_an_absent_parameter(self):
        for router in opdefs.MINTED_ROUTERS:
            param, _value = self.params_for(router)
            name = f"SILENT-{router}"
            self.define(name, params={"subject": "required", param: "optional"},
                        structural_params=["subject", param], **{router: param})
            e = self.refuses(name, {"subject": "thing:1"})
            self.assertIn(param, str(e))

    def test_an_object_declaration_that_omits_the_distinction_also_refuses(self):
        """Silence is silence in either form of the grammar. An op that writes the declaration
        out longhand and says nothing about absence has said nothing about absence."""
        for router in opdefs.MINTED_ROUTERS:
            param, _value = self.params_for(router)
            name = f"LONGHAND-{router}"
            self.define(name, params={"subject": "required", param: "optional"},
                        structural_params=["subject", param], **{router: {"param": param}})
            self.refuses(name, {"subject": "thing:2"})

    def test_an_explicit_required_declaration_refuses_identically(self):
        for router in opdefs.MINTED_ROUTERS:
            param, _value = self.params_for(router)
            name = f"EXPLICIT-{router}"
            self.define(name, params={"subject": "required", param: "optional"},
                        structural_params=["subject", param],
                        **{router: {"param": param, "when_absent": "required"}})
            self.refuses(name, {"subject": "thing:3"})

    def test_an_empty_value_refuses_the_same_way_under_silence(self):
        self.define("SILENT-EMPTY", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        self.refuses("SILENT-EMPTY", {"subject": "thing:4", "at": ""})

    def test_the_distinction_cannot_be_reached_by_a_typo(self):
        """The leash on the new power. An unknown absence value is refused AT DEFINITION TIME,
        the way an unknown check kind already is — so a misspelt `when_absent` can never read as
        a policy nobody wrote, and can never sit in a definition waiting to surprise a caller."""
        with self.assertRaises(OpError) as raised:
            self.gate.execute("CREATE-OP", OWNER, {"name": "TYPO-OP", "definition": {
                "law_cited": "CAP-IS-LAW", "params": {"subject": "required", "at": "optional"},
                "object_param": "subject", "payload_from": ["subject"],
                "occurrence_time_param": {"param": "at", "when_absent": "defualt"}}})
        self.assertEqual(raised.exception.rule, "AR-2")
        self.assertFalse(self.gate.has("TYPO-OP"))

    def test_a_declaration_naming_no_parameter_is_refused_at_definition_time(self):
        with self.assertRaises(OpError) as raised:
            self.gate.execute("CREATE-OP", OWNER, {"name": "NAMELESS-OP", "definition": {
                "law_cited": "CAP-IS-LAW", "params": {"subject": "required"},
                "object_param": "subject", "payload_from": ["subject"],
                "provenance_param": {"when_absent": "default"}}})
        self.assertEqual(raised.exception.rule, "AR-2")
        self.assertFalse(self.gate.has("NAMELESS-OP"))

    def test_an_unknown_key_in_the_declaration_is_refused_at_definition_time(self):
        with self.assertRaises(OpError) as raised:
            self.gate.execute("CREATE-OP", OWNER, {"name": "EXTRA-KEY-OP", "definition": {
                "law_cited": "CAP-IS-LAW", "params": {"subject": "required", "at": "optional"},
                "object_param": "subject", "payload_from": ["subject"],
                "occurrence_time_param": {"param": "at", "when_absent": "default",
                                          "fallback": "1999-01-01T00:00:00+00:00"}}})
        self.assertEqual(raised.exception.rule, "AR-2")

    def test_an_amendment_cannot_smuggle_a_bad_declaration_past_the_same_check(self):
        """The definition-time check lives at BOTH doors, because an op enters the registry
        through two of them."""
        self.define("AMENDABLE", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        live = self.views.op_definitions()["AMENDABLE"]
        d = json.loads(json.dumps(live["definition"], default=dict))
        d["occurrence_time_param"] = {"param": "at", "when_absent": "whenever"}
        with self.assertRaises(OpError) as raised:
            self.gate.execute("AMEND-OP", OWNER, {"name": "AMENDABLE", "definition": d})
        self.assertEqual(raised.exception.rule, "AR-2")


# =============================================================================================
# T-EXISTING-PINS-STILL-REFUSE — the wrong reference's detector
# =============================================================================================

class TestExistingPinsStillRefuse(unittest.TestCase):
    """EP-22's three observer pins, asserted DIRECTLY rather than inferred from the suite
    staying green. A record missing any of them refuses at submission; that refusal is what
    makes an observation's provenance trustworthy rather than best-effort, and it is the first
    thing a mistaken reading of this EP would take away."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, _b, _s = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"))
        register_observe_ops(self.gate)
        self.seam = ObservationSeam(self.gate)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_each_of_the_three_pins_still_refuses_on_absence(self):
        base = {"window": "mount", "window_version": "test-1",
                "occurrence_time": "2026-07-26T09:00:00+00:00",
                "act": "mount-added", "object": "mount:/x"}
        for pin in PIN_PARAMS:
            params = {k: v for k, v in base.items() if k != pin}
            refusals = len(self.store.by_action("op-refused"))
            with self.assertRaises(OpError, msg=f"{pin} was not required") as raised:
                self.gate.execute("OBSERVE-MOUNT", "m1-observer", params)
            self.assertEqual(raised.exception.rule, "AR-2")
            self.assertEqual(len(self.store.by_action("op-refused")), refusals + 1)
            self.assertEqual(self.store.by_action("mount-added"), [])

    def test_no_observe_op_declares_a_defaulted_router(self):
        """The structural half. The refusal above is the gate's required-parameter check, and
        this row says the same pins are not weakened from the other direction either: no op on
        the observe surface declares an envelope router at all, defaulted or otherwise, so
        nothing on that surface can fall back to a minted value."""
        surface = {n: m for n, m in self.gate.list().items() if n.startswith("OBSERVE-")}
        self.assertTrue(surface, "the observe surface is not registered — the row proves nothing")
        for name, meta in surface.items():
            for pin in PIN_PARAMS:
                self.assertEqual(meta["params"].get(pin), "required",
                                 f"{name} no longer requires the {pin} pin")


# =============================================================================================
# T-DEFAULTED-FALLS-BACK-TO-THE-ENVELOPE — the store's own value, and NOTHING else
# =============================================================================================

class TestDefaultedFallsBackToTheEnvelope(_TestWorld):

    def test_an_absent_occurrence_time_takes_the_stores_own_mint(self):
        self.define("LATE-OK", params={"subject": "required", "at": "optional"},
                    occurrence_time_param={"param": "at", "when_absent": "default"},
                    structural_params=["subject", "at"])
        rec = self.gate.execute("LATE-OK", OWNER, {"subject": "thing:5"})
        # the store's mint, which is its own clock at append and not a value from anywhere else
        self.assertGreaterEqual(rec["occurrence_time"], rec["record_time"])
        minted = datetime.datetime.fromisoformat(rec["occurrence_time"])
        self.assertLess(abs((datetime.datetime.now(datetime.timezone.utc)
                             - minted).total_seconds()), 60)

    def test_an_absent_provenance_takes_the_gates_own_resolution_and_no_more(self):
        self.define("PROV-OK", params={"subject": "required", "prov": "optional"},
                    provenance_param={"param": "prov", "when_absent": "default"},
                    structural_params=["subject", "prov"])
        rec = self.gate.execute("PROV-OK", OWNER, {"subject": "thing:6"})
        self.assertEqual(dict(rec["provenance"]),
                         {"asserted_by": self.views.resolve_asserted_by(OWNER),
                          "source": "system", "could_read": ()})

    def test_the_column_can_fail_the_supplied_value_is_carried_unchanged(self):
        """Prove the column can fail. If a defaulted declaration ignored its parameter — the
        wrong reference exactly — these two rows would be indistinguishable from the two above.
        They are not: a supplied value arrives in the envelope and the store's mint does not."""
        self.define("LATE-GIVEN", params={"subject": "required", "at": "optional"},
                    occurrence_time_param={"param": "at", "when_absent": "default"},
                    structural_params=["subject", "at"])
        rec = self.gate.execute("LATE-GIVEN", OWNER, {"subject": "thing:7", "at": WHEN})
        self.assertEqual(rec["occurrence_time"], WHEN)
        self.assertLess(rec["occurrence_time"], rec["record_time"])

        self.define("PROV-GIVEN", params={"subject": "required", "prov": "optional"},
                    provenance_param={"param": "prov", "when_absent": "default"},
                    structural_params=["subject", "prov"])
        rec = self.gate.execute("PROV-GIVEN", OWNER, {"subject": "thing:8", "prov": PROV})
        self.assertEqual(dict(rec["provenance"])["asserted_by"], PROV["asserted_by"])
        self.assertEqual(dict(rec["provenance"])["source"], "observation")

    def test_an_empty_value_falls_back_rather_than_refusing_under_default(self):
        self.define("LATE-EMPTY", params={"subject": "required", "at": "optional"},
                    occurrence_time_param={"param": "at", "when_absent": "default"},
                    structural_params=["subject", "at"])
        rec = self.gate.execute("LATE-EMPTY", OWNER, {"subject": "thing:9", "at": ""})
        self.assertGreaterEqual(rec["occurrence_time"], rec["record_time"])

    def test_a_defaulted_absence_takes_the_degenerate_two_times_path(self):
        """The consequence that matters downstream: a fallback is d = r, so the acceptance step
        and the sweep both see the world they saw before this EP. A fallback that produced d < r
        would fire a sweep on every caller that omitted the parameter."""
        self.define("LATE-SWEEP", params={"subject": "required", "at": "optional"},
                    occurrence_time_param={"param": "at", "when_absent": "default"},
                    structural_params=["subject", "at"])
        rec = self.gate.execute("LATE-SWEEP", OWNER, {"subject": "thing:10"})
        self.assertGreaterEqual(reconcile.deciding_time(rec), reconcile.recording_time(rec))
        self.assertEqual(self.gate.sweeps, [])
        # and the draft that reached the door carried no deciding time at all, which is what
        # puts it on the degenerate fast path rather than through the acceptance step
        self.assertFalse(reconcile.carries_deciding_time({"payload": {}}))


# =============================================================================================
# T-ROUTER-FAMILY-STILL-ONE-FAMILY — the structural row
# =============================================================================================

class TestRouterFamilyStillOneFamily(_TestWorld):

    def test_the_family_is_unchanged_and_the_distinction_names_a_subset_of_it(self):
        self.assertEqual(opdefs.ENVELOPE_ROUTERS,
                         ("target_param", "content_form", "evidence_param", "stamp_actor",
                          "occurrence_time_param", "provenance_param"))
        for router in opdefs.MINTED_ROUTERS:
            self.assertIn(router, opdefs.ENVELOPE_ROUTERS)

    def test_the_members_that_carry_the_distinction_are_the_store_minted_ones(self):
        """Not a chosen pair. A router carries the distinction iff the STORE mints its envelope
        field when the record does not carry it — which is why absence is a question for these
        two and an answer for the others: an absent target records an absent target, honestly,
        while an absent occurrence_time records a minted one."""
        self.assertEqual(dict(opdefs.MINTED_ROUTERS),
                         {"occurrence_time_param": "occurrence_time",
                          "provenance_param": "provenance"})

    def test_every_member_reads_the_distinction_through_the_one_parser(self):
        for router in opdefs.MINTED_ROUTERS:
            self.assertEqual(opdefs.router_param({}, router), (None, "required"))
            self.assertEqual(opdefs.router_param({router: "p"}, router), ("p", "required"))
            self.assertEqual(opdefs.router_param({router: {"param": "p"}}, router),
                             ("p", "required"))
            self.assertEqual(
                opdefs.router_param({router: {"param": "p", "when_absent": "default"}}, router),
                ("p", "default"))

    def test_the_distinction_is_refused_where_it_would_mean_nothing(self):
        """No decoration. A router whose field the store does not mint may not declare an
        absence policy — because there is no minting to fall back to, and a declaration that
        reads as law and does nothing is how the next four arrivals get created."""
        for router in ("target_param", "evidence_param"):
            with self.assertRaises(OpError) as raised:
                self.gate.execute("CREATE-OP", OWNER, {"name": f"DECOR-{router}", "definition": {
                    "law_cited": "CAP-IS-LAW", "params": {"subject": "required", "p": "optional"},
                    "object_param": "subject", "payload_from": ["subject"],
                    router: {"param": "p", "when_absent": "default"}}})
            self.assertEqual(raised.exception.rule, "AR-2")

    def test_the_interpreter_reads_the_members_through_the_family_table_itself(self):
        """The one-family row with teeth. EP-24B's structural guard asks that each router be
        READ inside the one interpreter, and it answers by searching the source for the router's
        name — which a COMMENT satisfies. That was exact when the interpreter named the two
        members in a literal tuple; now they are a declared table it iterates, so this row
        asserts the stronger fact directly: the interpreter reaches them through the family
        declaration, and the longhand grammar has exactly one reader."""
        with open(opdefs.__file__, encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("def _interpreter"):src.index("def live_definitions")]
        code = "\n".join(line.split("#")[0] for line in body.splitlines())
        self.assertIn("MINTED_ROUTERS.items()", code,
                      "the interpreter no longer iterates the family's own table")
        self.assertIn("router_param(d, decl)", code,
                      "the interpreter no longer reads the declaration through the one parser")
        # and nothing outside that parser unpacks the longhand form
        self.assertEqual(src.count('.get("when_absent")'), 1)

    def test_no_member_reaches_the_distinction_through_a_branch_on_the_op(self):
        with open(opdefs.__file__, encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("def _interpreter"):src.index("def live_definitions")]
        self.assertNotIn("opname ==", body)
        # CODE lines only. Comments name ops as EXAMPLES of who uses a general capability, which
        # is documentation; a branch naming an op is a special case. Only the second is refused.
        code = "\n".join(line.split("#")[0] for line in body.splitlines())
        for op in ("CREATE-RULE", "FILE-CREATE", "FILE-WRITE", "AMEND-BUDGET", "OVERTURN"):
            self.assertNotIn(op, code, f"{op} is named in the interpreter's own code — that is "
                                       "a special case for an op this EP touched")

    def test_the_founding_declares_the_distinction_in_the_same_grammar_a_test_op_uses(self):
        """The no-special-case row, checked against real declarations rather than asserted. A
        shipped op's declaration and a test op's declaration parse to the same shape through the
        same parser."""
        self.define("MIRROR", params={"subject": "required", "occurrence_time": "optional"},
                    occurrence_time_param={"param": "occurrence_time", "when_absent": "default"},
                    structural_params=["subject", "occurrence_time"])
        mine = opdefs.router_param(self.definition("MIRROR"), "occurrence_time_param")
        theirs = opdefs.router_param(self.definition("CREATE-RULE"), "occurrence_time_param")
        self.assertEqual(mine, theirs)


# =============================================================================================
# T-R1-CLOSED — the five inherited files ops
# =============================================================================================

class TestR1Closed(_Live):

    def test_the_five_inherited_ops_declare_the_provenance_router_as_defaulted(self):
        for name in INHERITED_FILES_OPS:
            param, when_absent = opdefs.router_param(self.definition(name), "provenance_param")
            self.assertEqual((param, when_absent), ("provenance", "default"), name)

    def test_the_port_evidence_lands_in_the_envelope_when_a_port_supplies_it(self):
        prov = {"asserted_by": OWNER, "source": "fuse-port", "could_read": [],
                "window": "fuse-port@1", "uid": 4242, "gid": 43, "pid": 44}
        rec = self.gate.execute("FILE-CREATE", OWNER, {"path": "/r1.txt", "provenance": prov})
        self.assertEqual(dict(rec["provenance"])["uid"], 4242)
        self.assertEqual(dict(rec["provenance"])["source"], "fuse-port")
        # and the raw evidence is EVIDENCE, not payload: it stays in the envelope
        self.assertNotIn("provenance", dict(rec["payload"]))

    def test_the_pre_existing_engine_caller_stays_conforming(self):
        """The reason the distinction had to exist rather than the router being relaxed.
        `kernel/syscall_port.py` calls four of these five with no provenance at all; under a
        required declaration every one of those calls becomes nonconforming.

        [DOCUMENTED FLIP, EP-28K: the ORDER moved and nothing else. This row drove the four
        ops as CREATE, UNLINK, PERM, LINK — a sequence that was namespace-arbitrary when it
        was written and is namespace-UNLAWFUL now, because the link named a target the unlink
        had already removed and the declared existence check refuses it. The row's subject is
        the provenance router and is untouched: the same four ops, the same parameters, the
        same assertions, in an order the namespace law admits.]"""
        for name, params in (("FILE-CREATE", {"path": "/plain.txt"}),
                             ("FILE-PERM", {"path": "/plain.txt", "perm": "600"}),
                             ("FILE-LINK", {"new_path": "/a", "target_path": "/plain.txt"}),
                             ("FILE-UNLINK", {"path": "/plain.txt"})):
            rec = self.gate.execute(name, OWNER, params)
            self.assertEqual(dict(rec["provenance"]),
                             {"asserted_by": self.views.resolve_asserted_by(OWNER),
                              "source": "system", "could_read": ()}, name)

    def test_the_port_reads_the_declaration_from_the_record_and_now_answers_yes(self):
        """The bridge asks the op's OWN definition whether it carries port provenance
        (`records_fs._carries_port_provenance`). It is out of this EP's fence and needed no
        edit: the answer moved because the founding did."""
        for name in INHERITED_FILES_OPS:
            self.assertTrue(bool(self.definition(name).get("provenance_param")), name)


# =============================================================================================
# T-DEGENERATE-IDENTITY — the structural half (the whole-suite half is the suite)
# =============================================================================================

class TestDegenerateIdentity(_TestWorld):

    def test_an_op_declaring_no_router_is_exactly_what_it_was(self):
        self.define("PLAIN-27B")
        rec = self.gate.execute("PLAIN-27B", OWNER, {"subject": "thing:11"})
        minted = datetime.datetime.fromisoformat(rec["occurrence_time"])
        self.assertLess(abs((datetime.datetime.now(datetime.timezone.utc)
                             - minted).total_seconds()), 60)
        self.assertEqual(dict(rec["provenance"])["asserted_by"], OWNER)
        self.assertEqual(dict(rec["provenance"])["source"], "system")
        self.assertIsNone(rec["target"])
        self.assertEqual(rec["content_form"], "inline")

    def test_the_four_routers_that_carry_no_distinction_are_untouched(self):
        self.define("OLD-FAMILY-27B",
                    params={"subject": "required", "tgt": "optional", "ev": "optional"},
                    target_param="tgt", evidence_param="ev", content_form="blob",
                    stamp_actor=["granter"], payload_from=["subject", "granter"],
                    structural_params=["subject", "tgt", "ev"])
        rec = self.gate.execute("OLD-FAMILY-27B", OWNER,
                                {"subject": "thing:12", "tgt": "t:1", "ev": "because",
                                 "granter": "someone-else"})
        self.assertEqual(rec["target"], "t:1")
        self.assertEqual(rec["evidence_summary"], "because")
        self.assertEqual(rec["content_form"], "blob")
        self.assertEqual(dict(rec["payload"])["granter"], OWNER)
        # and an absent target still records an absent target rather than refusing
        rec = self.gate.execute("OLD-FAMILY-27B", OWNER, {"subject": "thing:13"})
        self.assertIsNone(rec["target"])


# =============================================================================================
# W6 PROBES — landed as regression tests while the work item's SCOPE is with the mentor
#
# These rows are the measurements the stopped session ran before stopping on EP-27B ADDENDUM 1
# §W6, landed because a verification probe lands as a test. All are SCOPE-NEUTRAL: they record
# what the shipped world contains and what the interpreter does, and none decides which routers
# W6's refusal should cover — that was the question raised.
#
# [2026-07-28, ADDENDUM 2] The scope question was answered by DISSOLVING it: W6's refusal was
# replaced with uniformity, so `param_defaults` can no longer reach any router's field and the
# combination these rows scan for is lawful everywhere rather than dangerous in two places. The
# rows STAY and stay true — they record what the pack contains, which is still worth watching
# when Arc C writes definitions — but read them as a census and not as a defect scan. The rows
# that now carry the guarantee are TestRoutersReadOneMap and TestADefaultCannotReachARouter.
# =============================================================================================

class TestParamDefaultsAgainstTheRouters(_Live):
    """`param_defaults` resolves BEFORE the routers (design/36 ADDENDUM H.2), so a default can
    reach an envelope field the record would otherwise carry honestly. Which routers it can
    actually reach is a fact about the interpreter, and which shipped ops pair the two is a fact
    about the founding. Both are pinned here so a later round cannot move either quietly."""

    ROUTER_NAMES_A_PARAMETER = ("target_param", "evidence_param",
                                "occurrence_time_param", "provenance_param")

    def pairs(self):
        """Every (op, router, parameter) in the SHIPPED founding where a router names a parameter
        that the same definition also gives a `param_defaults` entry. Read from the RECORD, which
        is the definitive, not from the pack file."""
        found = []
        for name in self.views.op_definitions():
            d = self.definition(name)
            defaults = d.get("param_defaults") or {}
            if not defaults:
                continue
            for router in self.ROUTER_NAMES_A_PARAMETER:
                param, _absence = opdefs.router_param(d, router)
                if param is not None and param in defaults:
                    found.append((name, router, param))
        return sorted(found)

    def test_no_minted_router_in_the_shipped_founding_carries_the_combination(self):
        """The half of T-THE-SHIPPED-FOUNDING-IS-CLEAN that was true under EVERY candidate scope:
        no shipped op pairs a default with the two routers whose field the store mints. Asserted
        rather than assumed. [2026-07-28] Since W6b this pairing is harmless everywhere — the
        row is kept as the census it always was, and as the thing that notices if Arc C starts
        writing the shape whose danger the estate spent two sessions establishing."""
        minted = [p for p in self.pairs() if p[1] in opdefs.MINTED_ROUTERS]
        self.assertEqual(minted, [],
                         "a shipped op pairs param_defaults with a store-minted router — the "
                         "ADDENDUM H.2 combination is now instantiated in the founding")

    def test_the_shipped_founding_carries_exactly_one_other_such_pair(self):
        """SHM-GRANT declares `target_param: grantees` and also defaults `grantees` to []. It is
        a LEXICAL pair and not the H.2 defect, because the target field is fed from the RAW
        params (proven by the next row), so the default never reaches the envelope. Pinned as an
        exact set: if Arc C adds a second one, this row names it instead of it arriving unseen."""
        self.assertEqual(self.pairs(), [("SHM-GRANT", "target_param", "grantees")])

    def test_the_shipped_pack_would_pass_the_definition_time_leash_it_never_crosses(self):
        """An op definition reaches the registry through THREE doors: CREATE-OP, AMEND-OP, and
        the founding installer. When this row was written the installer ran no definition-shape
        validation at all, so W1's router leash guarded two doors and the founding came through
        the third; the row applied the grammar to the pack by hand. [2026-07-28, W6c] The third
        door now runs the whole vocabulary itself — see TestTheFoundingDoorValidates — and this
        row stays as the narrower, direct assertion that every shipped definition's ROUTERS parse
        cleanly, independent of whether the installer is wired to check them."""
        for name in self.views.op_definitions():
            opdefs._require_wellformed_routers(self.gate, "CREATE-OP", OWNER,
                                               self.definition(name))
        # and the column can fail: the same call over a malformed declaration refuses
        with self.assertRaises(OpError):
            opdefs._require_wellformed_routers(
                self.gate, "CREATE-OP", OWNER,
                {"occurrence_time_param": {"param": "at", "when_absent": "whenever"}})

    def test_the_column_can_fail_the_scan_sees_a_minted_pair_when_one_exists(self):
        """Both rows above are guards, and a guard that cannot fail is worse than none. A
        definition carrying the ADDENDUM H.2 combination is admitted here and the scan names it.
        The op is never invoked: what is under test is the detector, not the defect. [2026-07-28]
        The admission is now correct rather than a gap — ADDENDUM I.2 ruled the combination
        lawful once no router can read a default, and TestADefaultCannotReachARouter invokes this
        very shape and shows the pin still refusing."""
        self.gate.execute("CREATE-OP", OWNER, {"name": "PINNED-BY-DEFAULT-27B", "definition": {
            "law_cited": "CAP-IS-LAW", "description": "a test-world op",
            "params": {"subject": "required", "at": "optional"},
            "object_param": "subject", "payload_from": ["subject"],
            "structural_params": ["subject", "at"],
            "occurrence_time_param": "at",
            "param_defaults": {"at": "1999-01-01T00:00:00+00:00"}}})
        self.assertIn(("PINNED-BY-DEFAULT-27B", "occurrence_time_param", "at"), self.pairs())

    def test_param_defaults_cannot_reach_the_target_envelope_field(self):
        """The fact the scope question turns on, asserted behaviourally rather than read off a
        comment. `target_param` is routed from the caller's own params, so a default reaches the
        PAYLOAD and never the envelope's target: an absent parameter still records an absent
        target. That is why the pair above cannot fabricate a target, and it is the difference
        between that pair and the combination ADDENDUM H.2 rules on."""
        self.gate.execute("CREATE-OP", OWNER, {"name": "RAW-TARGET-27B", "definition": {
            "law_cited": "CAP-IS-LAW", "description": "a test-world op",
            "params": {"subject": "required", "tgt": "optional"},
            "object_param": "subject", "payload_from": ["subject", "tgt"],
            "structural_params": ["subject", "tgt"],
            "target_param": "tgt", "param_defaults": {"tgt": "fabricated:target"}}})
        rec = self.gate.execute("RAW-TARGET-27B", OWNER, {"subject": "thing:14"})
        self.assertIsNone(rec["target"], "a param default reached the envelope's target field")
        self.assertEqual(dict(rec["payload"])["tgt"], "fabricated:target")


# =============================================================================================
# EP-27B ADDENDUM 2 — W6 REPLACED: the family reads ONE map, and the founding door validates
#
# The rows above measured the world; these change it. The root ADDENDUM I.2 names is TWO
# MECHANISMS FOR ONE IDEA — `param_defaults` and the router's own `when_absent` distinction both
# answer how an envelope field is supplied when the caller omits the parameter — and the fix is
# uniformity rather than a refusal: every member of the family reads the RAW caller parameters,
# as `target_param` already did. Then a default can never reach a router's field, the
# contradiction is structurally impossible, and no definition-time refusal is needed for it.
#
# ADDENDUM I.3 is the larger half: op definitions reach the registry through THREE doors and the
# founding installer, through which all 72 live definitions arrived and all of Arc C's will,
# validated no definition shape at all. Founding-only legitimacy exempts AUTHORITY and never
# SHAPE — a record that cannot be interpreted is not made interpretable by being at genesis.
# =============================================================================================

class TestRoutersReadOneMap(_TestWorld):
    """T-ROUTERS-READ-ONE-MAP (W6a/W6b). Every member that names a caller parameter reads the
    RAW parameters, so `param_defaults` — which fills a COPY before the checks run — cannot
    reach any envelope field. Asserted per member and behaviourally, never inferred from the
    suite staying green."""

    #: A value no store could mint and no caller supplied. If it reaches an envelope field, a
    #: default reached a router.
    FABRICATED = "fabricated-by-a-default"

    def test_the_family_splits_exactly_two_ways_and_the_split_is_derived(self):
        """The family-completeness row, so a SEVENTH member cannot be added and quietly miss
        every row below. A member that routes a caller parameter is spelled `<field>_param`;
        the two that are not — `content_form`, a literal string on the record, and
        `stamp_actor`, a list of payload fields overwritten with the acting actor — name no
        parameter for a default to collide with. The set is computed from the family's own
        spelling rather than enumerated a second time."""
        self.assertEqual(set(opdefs.PARAM_ROUTERS) | {"content_form", "stamp_actor"},
                         set(opdefs.ENVELOPE_ROUTERS))
        self.assertTrue(all(r.endswith("_param") for r in opdefs.PARAM_ROUTERS))
        self.assertEqual(len(opdefs.PARAM_ROUTERS), 4)

    def test_target_param_reads_the_raw_caller_parameters(self):
        """The member that was already uniform, pinned as the reference the other three were
        made to match — and it is the reason `SHM-GRANT` is lawful rather than excepted."""
        self.define("RAW-TARGET-A2", params={"subject": "required", "tgt": "optional"},
                    payload_from=["subject", "tgt"], target_param="tgt",
                    param_defaults={"tgt": self.FABRICATED},
                    structural_params=["subject", "tgt"])
        rec = self.gate.execute("RAW-TARGET-A2", OWNER, {"subject": "thing:20"})
        self.assertIsNone(rec["target"])
        self.assertEqual(dict(rec["payload"])["tgt"], self.FABRICATED)

    def test_evidence_param_reads_the_raw_caller_parameters(self):
        """The third member, which the stop entry SUSPECTED and W6a establishes: it read the
        post-defaults copy, so a default displaced the definition's own declared fallback. Now
        an absent parameter reaches `evidence_default`, which is where a definition says what
        its evidence is when the caller states none."""
        self.define("RAW-EVIDENCE-A2", params={"subject": "required", "ev": "optional"},
                    evidence_param="ev", evidence_default="the definition's own fallback",
                    param_defaults={"ev": self.FABRICATED},
                    structural_params=["subject", "ev"])
        rec = self.gate.execute("RAW-EVIDENCE-A2", OWNER, {"subject": "thing:21"})
        self.assertEqual(rec["evidence_summary"], "the definition's own fallback")
        # the column can fail: a caller who states its evidence still has it recorded
        rec = self.gate.execute("RAW-EVIDENCE-A2", OWNER, {"subject": "thing:22", "ev": "seen"})
        self.assertEqual(rec["evidence_summary"], "seen")

    def test_the_two_members_that_name_no_parameter_route_no_parameter(self):
        """The other half of the family, so the row covers all six. Neither reads a parameter
        map at all, so neither has a map to be uniform on: `content_form` records the literal
        the definition declares and `stamp_actor` overwrites its fields with the acting actor,
        both regardless of any default."""
        self.define("NO-PARAM-ROUTERS-A2",
                    params={"subject": "required", "granter": "optional"},
                    content_form="inline", stamp_actor=["granter"],
                    param_defaults={"inline": self.FABRICATED, "granter": self.FABRICATED},
                    structural_params=["subject", "granter"])
        rec = self.gate.execute("NO-PARAM-ROUTERS-A2", OWNER, {"subject": "thing:23"})
        self.assertEqual(rec["content_form"], "inline")
        self.assertEqual(dict(rec["payload"])["granter"], OWNER)


class TestADefaultCannotReachARouter(_TestWorld):
    """T-A-DEFAULT-CANNOT-REACH-A-ROUTER. The exact combination the stopped session ran, on
    both store-minted members: a fabricated default alongside a REQUIRED pin. The pin refuses
    as declared, and the fabricated value is nowhere on the record."""

    FABRICATED_TIME = "1999-01-01T00:00:00+00:00"
    FABRICATED_PROV = {"asserted_by": "window:nobody@0", "source": "observation",
                       "could_read": []}

    def test_a_default_cannot_satisfy_a_required_occurrence_time_pin(self):
        self.define("PIN-BY-DEFAULT-A2", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at",
                    param_defaults={"at": self.FABRICATED_TIME},
                    structural_params=["subject", "at"])
        self.refuses("PIN-BY-DEFAULT-A2", {"subject": "thing:24"})
        self.assertEqual(self.store.by_action("PIN-BY-DEFAULT-A2"), [])

    def test_a_default_cannot_satisfy_a_required_provenance_pin(self):
        self.define("PROV-PIN-BY-DEFAULT-A2",
                    params={"subject": "required", "prov": "optional"},
                    provenance_param="prov",
                    param_defaults={"prov": self.FABRICATED_PROV},
                    structural_params=["subject", "prov"])
        self.refuses("PROV-PIN-BY-DEFAULT-A2", {"subject": "thing:25"})

    def test_the_column_can_fail_the_same_op_records_a_supplied_value(self):
        """Prove the column can fail. The two refusals above must come from the parameter being
        ABSENT and not from the declaration being unusable: the same definition, called WITH the
        parameter, records exactly what the caller stated."""
        self.define("PIN-GIVEN-A2", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at",
                    param_defaults={"at": self.FABRICATED_TIME},
                    structural_params=["subject", "at"])
        rec = self.gate.execute("PIN-GIVEN-A2", OWNER, {"subject": "thing:26", "at": WHEN})
        self.assertEqual(rec["occurrence_time"], WHEN)

    def test_a_default_cannot_displace_the_stores_own_mint_under_a_defaulted_pin(self):
        """The other direction, and the sharper one. A DEFAULTED declaration falls back to the
        store's minted value and to nothing else — an author-chosen constant is not a fallback
        the router will take, so the record's time is one the store observed rather than one a
        definition invented."""
        self.define("DEFAULTED-BY-DEFAULT-A2",
                    params={"subject": "required", "at": "optional"},
                    payload_from=["subject", "at"],
                    occurrence_time_param={"param": "at", "when_absent": "default"},
                    param_defaults={"at": self.FABRICATED_TIME},
                    structural_params=["subject", "at"])
        rec = self.gate.execute("DEFAULTED-BY-DEFAULT-A2", OWNER, {"subject": "thing:27"})
        self.assertNotEqual(rec["occurrence_time"], self.FABRICATED_TIME)
        self.assertGreaterEqual(rec["occurrence_time"], rec["record_time"])
        # and the payload still carries the default, which is what param_defaults is FOR: the
        # two mechanisms stop overlapping, they do not stop existing
        self.assertEqual(dict(rec["payload"])["at"], self.FABRICATED_TIME)

    def test_an_amendment_cannot_make_a_default_reach_a_router_either(self):
        """The careless-owner archetype, and the both-doors discipline this EP already earned
        once. An op is created clean and then AMENDED to add the default beside its required
        pin — the legitimate wide power used through the documented path. The pin still
        refuses, because the reason it refuses is where the interpreter READS and not what any
        door admitted."""
        self.define("AMENDED-DEFAULT-A2", params={"subject": "required", "at": "optional"},
                    occurrence_time_param="at", structural_params=["subject", "at"])
        self.gate.execute("AMEND-OP", OWNER, {"name": "AMENDED-DEFAULT-A2", "definition": {
            "law_cited": "CAP-IS-LAW", "description": "a test-world op",
            "params": {"subject": "required", "at": "optional"},
            "object_param": "subject", "payload_from": ["subject"],
            "structural_params": ["subject", "at"],
            "occurrence_time_param": "at",
            "param_defaults": {"at": self.FABRICATED_TIME}}})
        self.refuses("AMENDED-DEFAULT-A2", {"subject": "thing:28"})

    def test_a_replayed_definition_reads_the_same_map_as_a_fresh_one(self):
        """The reboot archetype, aimed where this EP's own first draft broke: a definition read
        back off the record is FROZEN, and the parser once took a frozen declaration for a
        parameter named after the whole declaration. So the uniformity claim is asserted on BOTH
        sides of a reboot — the same op, the same call, the same refusal, after the registry is
        rebuilt from the record file alone."""
        self.define("REPLAYED-DEFAULT-A2", params={"subject": "required", "at": "optional"},
                    occurrence_time_param={"param": "at", "when_absent": "default"},
                    payload_from=["subject", "at"],
                    param_defaults={"at": self.FABRICATED_TIME},
                    structural_params=["subject", "at"])
        live = self.gate.execute("REPLAYED-DEFAULT-A2", OWNER, {"subject": "thing:29"})
        # EP-MAINT-OUTSIDE-5 (re-spec C): close the live writer before the reboot so the replayed
        # kernel is a WRITER able to invoke the replayed op (release-on-close); a second live open
        # would be demoted to a reader and its append refused by name.
        self.store.close()
        store, gate, views, _b, _s = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        replayed = gate.execute("REPLAYED-DEFAULT-A2", OWNER, {"subject": "thing:30"})
        for rec in (live, replayed):
            self.assertNotEqual(rec["occurrence_time"], self.FABRICATED_TIME)
            self.assertGreaterEqual(rec["occurrence_time"], rec["record_time"])
            self.assertEqual(dict(rec["payload"])["at"], self.FABRICATED_TIME)


class TestShmGrantIsUnchanged(_Live):
    """T-SHM-GRANT-IS-UNCHANGED. The shipped op nearest this change and therefore the canary:
    it is the one op in the founding that pairs `param_defaults` with a router, and ADDENDUM
    I.2's stop says that if uniformity changes what any shipped op records, that is a finding
    and not a change. The two records below were captured on the tree BEFORE the change and are
    pinned here as literals."""

    #: Every field of the record that does not vary between runs. `seq`, `record_id`,
    #: `record_time`, `submission_time` and the minted `occurrence_time` are the clock and the
    #: position; everything else is what the op RECORDS. The literals below are frozen shapes
    #: (tuples, read-only mappings) because that is what a committed record IS — comparing
    #: against lists would compare against a normalisation this test invented.
    VARIES = ("seq", "record_id", "record_time", "submission_time", "occurrence_time")

    def fixed(self, rec):
        return {k: (dict(v) if hasattr(v, "keys") else v)
                for k, v in dict(rec).items() if k not in self.VARIES}

    def found(self, region, holder="browser"):
        """THE ESTABLISHMENT A SHARE INHERITS, named once for both rows below.

        [DOCUMENTED FLIP — EP-30-C4R, 2026-08-26, §A57 cause-mapped repair. This helper IS the
        repair, and it is stated here once rather than at two call sites so that a reader meets
        the cause once. CAUSE: EP-30-C4 landed `require_prior` over MEM-GRANT's `region` on the
        shipped `SHM-GRANT`. Both rows below granted shares over regions nothing in this file
        ever established — `grep -c MEM-GRANT` returned 0 — so the gate refused and both ERRORED.
        WHAT THIS CLASS IS: its own docstring calls it THE CANARY for exactly this change, and
        ADDENDUM I.2's stop says a change reaching what a shipped op RECORDS is a finding and not
        a change. IT FIRED. C4 is that finding, released and closed at board :2078. THE CANARY
        REPORTED; IT DID NOT FAIL, AND THE PIN IS NOT REMOVED — the literals below are re-taken
        against the post-C4 world and stay literals.]"""
        return self.gate.execute("MEM-GRANT", holder, {"region": region, "size": 4096})

    def test_the_grantees_supplied_record_is_what_it_was(self):
        self.found("shm:44")
        rec = self.gate.execute("SHM-GRANT", "browser",
                                {"region": "shm:44", "grantees": ["renderer"], "mode": "rw"})
        self.assertEqual(self.fixed(rec), {
            "action": "SHM-GRANT", "actor": "browser", "content_form": "inline",
            "evidence_summary": None, "object": "shm:44",
            "origin": {"built_id": 0, "subsystem_id": "kernel"},
            "payload": {"grantees": ("renderer",), "granter": "browser", "mode": "rw",
                        "region": "shm:44"},
            "provenance": {"asserted_by": "unverified:browser", "could_read": (),
                           "source": "system"},
            "refs": (), "rule_cited": "COMM-LAW-SHARE-GRANT", "target": ("renderer",)})

    def test_the_grantees_omitted_record_is_what_it_was(self):
        """The path the default actually takes: `grantees` absent, so the payload carries the
        declared `[]` and the envelope's target stays None. This is the row that would go red if
        uniformity had reached a shipped op.

        A DIFFERENT ROW FROM ITS SIBLING AND REPAIRED SEPARATELY: a different region, and its
        subject is `param_defaults` supplying `grantees` and `mode`, not a supplied grantee list.
        Its establishment is its own."""
        self.found("shm:45")
        rec = self.gate.execute("SHM-GRANT", "browser", {"region": "shm:45"})
        self.assertEqual(self.fixed(rec), {
            "action": "SHM-GRANT", "actor": "browser", "content_form": "inline",
            "evidence_summary": None, "object": "shm:45",
            "origin": {"built_id": 0, "subsystem_id": "kernel"},
            "payload": {"grantees": (), "granter": "browser", "mode": "rw",
                        "region": "shm:45"},
            "provenance": {"asserted_by": "unverified:browser", "could_read": (),
                           "source": "system"},
            "refs": (), "rule_cited": "COMM-LAW-SHARE-GRANT", "target": None})


class TestTheFoundingDoorValidates(unittest.TestCase):
    """T-THE-FOUNDING-DOOR-VALIDATES (W6c; design/36 ADDENDUM I.3). The third door runs the
    SAME definition-shape vocabulary the `CREATE-OP` path runs — not a copy of it, the same
    function, reached through a door object shaped like the gate. One validation, three doors."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.pack = copy.deepcopy(load_pack())

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def definitions(self, pack):
        return [r for step in pack["steps"] for r in step["records"]
                if r.get("action") == "CREATE-OP"
                and (r.get("payload") or {}).get("kind") == "op_definition"]

    def corrupt_first_definition(self, pack, mutate):
        recs = self.definitions(pack)
        self.assertTrue(recs, "the pack defines no ops — the row proves nothing")
        mutate(recs[0]["payload"]["definition"])
        return recs[0]["payload"]["name"]

    def test_a_malformed_definition_refuses_the_whole_founding_cited(self):
        name = self.corrupt_first_definition(
            self.pack, lambda d: d.__setitem__("checks", [{"check": "vibes"}]))
        with self.assertRaises(FoundingIntegrityError) as cm:
            _validate(_records(self.pack))
        self.assertIn(name, str(cm.exception))
        self.assertIn("vibes", str(cm.exception))
        self.assertIn("AR-2", str(cm.exception))

    def test_the_typo_case_is_refused_at_this_door_too(self):
        """The case EP-27B already guards at the other two doors. A misspelt absence value reads
        as REQUIRED to the parser, so a definition would sit in the founding saying something its
        author did not write — and being at genesis does not make it interpretable."""
        self.corrupt_first_definition(
            self.pack,
            lambda d: d.__setitem__("occurrence_time_param",
                                    {"param": "at", "when_absent": "whenver"}))
        with self.assertRaises(FoundingIntegrityError) as cm:
            _validate(_records(self.pack))
        self.assertIn("whenver", str(cm.exception))

    def test_a_definition_citing_no_law_refuses_the_whole_founding(self):
        self.corrupt_first_definition(self.pack, lambda d: d.pop("law_cited", None))
        with self.assertRaises(FoundingIntegrityError):
            _validate(_records(self.pack))

    def test_both_columns_can_fail_the_shipped_pack_passes_this_door(self):
        """Prove the column can fail in the other direction too: the validation that refuses the
        three packs above admits the real one, so the rows measure the definitions and not the
        validator refusing everything."""
        _validate(_records(load_pack()))

    def test_the_refused_founding_appends_nothing(self):
        """A half-founded record is worse than none, and a shape refusal is no different from a
        reference refusal in that respect: `install` validates the WHOLE pack before its first
        append, so a malformed definition leaves an empty store."""
        self.corrupt_first_definition(
            self.pack, lambda d: d.__setitem__("checks", [{"check": "vibes"}]))
        store = EventStore(os.path.join(self.dir, "record.jsonl"), require_rule_cited=True)
        real = install_module.load_pack
        install_module.load_pack = lambda *a, **k: self.pack
        try:
            with self.assertRaises(FoundingIntegrityError):
                install_module.install(store)
        finally:
            install_module.load_pack = real
        self.assertEqual(store.all(), [])

    def test_the_same_definition_is_refused_at_all_three_doors_for_the_same_reason(self):
        """The one-vocabulary claim asserted BEHAVIOURALLY rather than by reading the source.
        One malformed definition, three doors, three refusals carrying the same citation and the
        same words — which is what "one validation" has to mean if it means anything."""
        malformed = {"law_cited": "CAP-IS-LAW", "description": "a test-world op",
                     "params": {"subject": "required", "at": "optional"},
                     "object_param": "subject", "payload_from": ["subject"],
                     "occurrence_time_param": {"param": "at", "when_absent": "whenver"}}
        d = tempfile.mkdtemp()
        try:
            store, gate, _v, _b, _s = build_full_kernel(
                os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                os.path.join(d, "vault"))
            gate.execute("CREATE-OP", OWNER, {"name": "THREE-DOORS-A2", "definition": {
                "law_cited": "CAP-IS-LAW", "params": {"subject": "required"},
                "object_param": "subject", "payload_from": ["subject"],
                "structural_params": ["subject"]}})
            with self.assertRaises(OpError) as created:
                gate.execute("CREATE-OP", OWNER,
                             {"name": "THREE-DOORS-B2", "definition": malformed})
            with self.assertRaises(OpError) as amended:
                gate.execute("AMEND-OP", OWNER,
                             {"name": "THREE-DOORS-A2", "definition": malformed})
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.corrupt_first_definition(
            self.pack, lambda dd: dd.__setitem__("occurrence_time_param",
                                                 malformed["occurrence_time_param"]))
        with self.assertRaises(FoundingIntegrityError) as founded:
            _validate(_records(self.pack))
        self.assertEqual(created.exception.rule, "AR-2")
        self.assertEqual(amended.exception.rule, "AR-2")
        self.assertIn("AR-2", str(founded.exception))
        words = created.exception.message
        self.assertEqual(amended.exception.message, words)
        # the founding door carries the gate's own words through, wrapped in the refusal of the
        # WHOLE founding — the same reason, said once, reported in each door's own register
        self.assertIn(words, str(founded.exception))

    def test_one_validation_three_doors_rather_than_a_second_copy(self):
        """The structural half, and the point of the item. The founding door does not carry its
        own list of what a definition may say: it calls the same `validate_definition_shape` the
        two gate doors call, differing only in the door object that turns a refusal into this
        installer's own whole-founding refusal."""
        for door in ("CREATE-OP", "AMEND-OP"):
            self.assertIn(door, opdefs_source())
        body = opdefs_source()
        self.assertEqual(body.count("def validate_definition_shape"), 1)
        with open(install_module.__file__, encoding="utf-8") as f:
            installer = f.read()
        self.assertIn("validate_definition_shape", installer)
        for vocabulary in ("OP_CHECKS", "when_absent", "law_cited"):
            self.assertNotIn(f'"{vocabulary}"', installer,
                             f"the installer carries its own copy of {vocabulary}")


class TestTheShippedFoundingIsClean(unittest.TestCase):
    """T-THE-SHIPPED-FOUNDING-IS-CLEAN — STANDING, over the whole pack, every suite run. The
    stopped session's own proposal and the reason it matters: a definition-time check that is
    only ever asserted once goes green while the exposure it was ordered against is untouched.
    Seventy-two definitions entered through a door that validated nothing; Arc C's will enter
    through the same one."""

    def test_every_shipped_definition_passes_the_whole_shape_vocabulary(self):
        pack = load_pack()
        names = [(r.get("payload") or {}).get("name") for step in pack["steps"]
                 for r in step["records"] if r.get("action") == "CREATE-OP"]
        self.assertGreaterEqual(len(names), 72,
                                "the pack lost op definitions — this guard is standing over "
                                "fewer than it was written for")
        _validate(_records(pack))          # the whole pre-flight, over the whole pack

    def test_the_column_can_fail_over_the_real_pack(self):
        pack = copy.deepcopy(load_pack())
        for step in pack["steps"]:
            for r in step["records"]:
                if r.get("action") == "CREATE-OP":
                    r["payload"]["definition"]["checks"] = [{"check": "vibes"}]
                    break
        with self.assertRaises(FoundingIntegrityError):
            _validate(_records(pack))


def opdefs_source():
    with open(opdefs.__file__, encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    unittest.main()
