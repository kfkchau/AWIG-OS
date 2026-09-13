# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-30-C1 — A CHANNEL STOPS BEING A NAME AND BECOMES AN OPENING OF SOMEBODY'S.

Every row of the plan's §3, and every red world of its §4, each carrying the KIND the plan
declares for it (DRIVEN / INSPECTED / MOMENT / ABSENCE) in its own docstring — because C0's
close found three rows whose text never said what kind of row they were, and a row that does
not declare its kind makes every later hand re-derive it.

THE RED FACT THIS PASS CURES, so a later reader can falsify the claim of cure: `COMMS-OPEN`
declared `params: {"channel": "required"}` and `checks: []`, and `CommsView.open_channels`
folded every opening into a `set()` of strings. Nothing named an owner, nothing named an
entity, and the gate admitted every `COMMS-OPEN` that reached it.

WHAT THE INVARIANT COUNTS, and it is the one thing about this file most likely to be read
backwards: LIVE openings at a moment, NEVER openings across a lifetime (design/39 §3). A
re-open after a close is LAWFUL. R4 exists to hold that polarity, and its red world is the
naive implementation that counts recorded ACTS — which would bar every program restart.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import era_pin                                                   # noqa: E402  (the era-pin home, EP-28Z)
from kernel import opdefs as opdefs_mod                          # noqa: E402
from kernel.blobs import BlobStore                               # noqa: E402
from kernel.boot import build_kernel                             # noqa: E402
from kernel.errors import OpError                                # noqa: E402
from subsystems.comms import CommsView                           # noqa: E402
from subsystems.scheduling import SchedulingView                 # noqa: E402

PACK_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "src", "founding", "founding-pack.json")

SYSTEM, USER = "system-facing", "user-facing"


def comms_open_definition():
    """COMMS-OPEN's definition, read out of the founding pack itself — the INSPECTED rows'
    subject. Read from the pack rather than the live registry because A1 and A2 are claims
    about the LAW AS WRITTEN, and a registry read would pass on a definition the pack does
    not carry."""
    with open(PACK_PATH, encoding="utf-8") as fh:
        pack = json.load(fh)
    for step in pack["steps"]:
        for record in step.get("records", []):
            payload = record.get("payload")
            if isinstance(payload, dict) and payload.get("name") == "COMMS-OPEN":
                return payload["definition"]
    raise AssertionError("COMMS-OPEN carries no definition in the founding pack")


def founding_version():
    with open(PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)["founding_version"]


class WorldCase(unittest.TestCase):
    """A world with the changed law installed, plus the helpers the rows share."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep30-c1-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.record, blobs=self.blobs)
        self.comms = CommsView(self.store)
        self.sched = SchedulingView(self.store)
        import shutil
        self.addCleanup(shutil.rmtree, self.dir, True)

    def establish(self, entity, actor_class="program"):
        """An ENTITY on the record — its identity IS its recorded establishment (design/39 §2)."""
        return self.gate.execute("CREATE-ACCOUNT", "owner",
                                 {"account_id": entity, "actor_class": actor_class})

    def opens(self, entity, channel, role, actor="owner"):
        return self.gate.execute("COMMS-OPEN", actor,
                                 {"channel": channel, "entity": entity, "role": role})

    def refusal_of(self, fn, *a, **kw):
        """Drive an act expected to refuse; return (cited rule, message). Fails loudly if the
        act was ADMITTED — an absence row whose subject was never refused proves nothing."""
        before = len(self.store.by_action("op-refused"))
        try:
            fn(*a, **kw)
        except OpError as exc:
            after = len(self.store.by_action("op-refused"))
            self.assertEqual(after, before + 1,
                             "the act raised but recorded no refusal — a governed refusal is a "
                             "RECORDED rule-citing decision, not an exception")
            refusal = self.store.by_action("op-refused")[-1]
            return refusal.get("rule_cited"), str(exc)
        raise AssertionError("the act was ADMITTED where the law requires a refusal")


# =====================================================================================
# A1 / A2 — INSPECTED. The law as written.
# =====================================================================================

class LawAsWrittenCase(unittest.TestCase):

    def test_a1_the_op_requires_an_entity_and_a_role(self):
        """A1 — KIND: INSPECTED. Arity, hand-computed from design/39 §6 bullets 1, 2 and 3."""
        definition = comms_open_definition()
        self.assertEqual(sorted(definition["params"].items()),
                         [("channel", "required"), ("entity", "required"), ("role", "required")])
        self.assertEqual(len(definition["checks"]), 3)

    def test_a2_the_three_checks_are_named_not_counted(self):
        """A2 — KIND: INSPECTED. Identity, not arity. A1 proves there are three; a bare count
        would pass on three WRONG checks, which is the defect this row exists to bar."""
        checks = comms_open_definition()["checks"]
        by_kind = {c["check"]: c for c in checks}
        self.assertEqual(sorted(by_kind), ["live_slot", "require_prior", "value_domain"])

        # the entity-exists check: a prior establishment of the named entity
        entity_check = by_kind["require_prior"]
        self.assertEqual(entity_check["action"], "CREATE-ACCOUNT")
        self.assertEqual(entity_check["field"], "account_id")
        self.assertEqual(entity_check["param"], "entity")

        # the role-is-one-of-two check, and the domain is EXACTLY two (design/39 §7 rejected
        # three-or-more default channels by name)
        role_check = by_kind["value_domain"]
        self.assertEqual(role_check["param"], "role")
        self.assertEqual(sorted(role_check["domain"]), sorted([SYSTEM, USER]))

        # the no-third-opening check, over the LIVE set of (entity, role) slots
        slot_check = by_kind["live_slot"]
        self.assertEqual(slot_check["open_action"], "COMMS-OPEN")
        self.assertEqual(slot_check["close_action"], "COMMS-CLOSE")
        self.assertEqual(slot_check["instance_param"], "channel")
        self.assertEqual(slot_check["slot_params"], ["entity", "role"])

        for check in checks:
            self.assertTrue(check.get("cite"), "a check that cites nothing is unrecordable")


# =====================================================================================
# A3 — DRIVEN, WITH A POSITIVE CONTROL INSIDE IT
# =====================================================================================

class ThirdOpeningRefusedCase(WorldCase):

    def test_a3_two_openings_are_admitted_then_a_third_is_refused_citing_its_rule(self):
        """A3 — KIND: DRIVEN, WITH A POSITIVE CONTROL INSIDE IT.

        PART 1 IS NOT OPTIONAL AND RUNS FIRST. The vacuity mode here is not "an extra open
        sneaks in", it is "the drive never happened": an empty refusal list passes a row that
        tested nothing. Prove the instrument was LIVE before asserting it refused."""
        self.establish("E1")
        before = len(self.store.by_action("COMMS-OPEN"))

        # PART 1 — the positive control. Both must be ADMITTED and both must APPEND.
        self.opens("E1", "sys:1", SYSTEM)
        self.opens("E1", "usr:1", USER)
        appended = len(self.store.by_action("COMMS-OPEN")) - before
        self.assertEqual(appended, 2,
                         "part 1 produced %d appends, not 2 — part 2's refusal would prove "
                         "nothing and this row STOPS" % appended)

        # PART 2 — a third opening for the SAME entity.
        rule, message = self.refusal_of(self.opens, "E1", "sys:2", SYSTEM)
        self.assertEqual(rule, "COMM-LAW-CONTRACT",
                         "the refusal did not cite the rule the check names: %r" % (rule,))
        self.assertIn("live", message.lower())
        # and the third opening left no act-record claiming an effect
        self.assertEqual(len(self.store.by_action("COMMS-OPEN")) - before, 2)


# =====================================================================================
# A4 — DRIVEN. Ownership, not membership.
# =====================================================================================

class OwnershipCase(WorldCase):

    def test_a4_the_view_answers_whose_channel_and_which_of_the_two(self):
        """A4 — KIND: DRIVEN. `open_channels` returning a set of strings is the RED FACT; a row
        that only counted channels would stay green across the cure, so this row asks the
        question the set could not answer."""
        self.establish("E1")
        self.establish("E2")
        self.opens("E1", "sys:1", SYSTEM)
        self.opens("E1", "usr:1", USER)
        self.opens("E2", "sys:2", SYSTEM)

        self.assertEqual(self.comms.channels_of("E1"), {SYSTEM: "sys:1", USER: "usr:1"})
        # E2 has one role filled and the other ABSENT AND PRESENT AS ABSENT — an omitted key
        # and a key holding None read the same to a careless caller.
        self.assertEqual(self.comms.channels_of("E2"), {SYSTEM: "sys:2", USER: None})
        self.assertIn(USER, self.comms.channels_of("E2"))

        # the roles come from the LAW's own record, never a literal in the view
        self.assertEqual(sorted(self.comms.declared_roles()), sorted([SYSTEM, USER]))


# =====================================================================================
# A5 / A6 — DRIVEN. The entity/incarnation split, proven REAL rather than named.
# =====================================================================================

class EntityIncarnationSplitCase(WorldCase):

    def _incarnate_and_end(self, proc):
        self.gate.execute("SCHED-ADMIT", "owner", {"proc": proc})
        self.assertIn(proc, self.sched.runnable(), "the incarnation never began")
        self.gate.execute("SCHED-KILL", "owner", {"proc": proc, "reason": "test"})

    def test_a5_a_permission_lands_on_the_entity_and_survives_the_incarnation(self):
        """A5 — KIND: DRIVEN. design/39 §7: a permission must survive the death of the
        incarnation that last used it and follow the entity that owns it. THIS IS THE ROW THAT
        PROVES THE SPLIT IS REAL RATHER THAN NAMED."""
        self.establish("E1")
        self.gate.execute("GRANT", "owner",
                          {"grant_id": "g1", "grantee": "E1", "actions": ["COMMS-SEND"],
                           "info": "message", "space": self.views.mother_space()})
        self.assertTrue(self.views.covers("E1", "COMMS-SEND", "message", self.views.mother_space()))

        self._incarnate_and_end("proc:E1#1")

        self.assertTrue(
            self.views.covers("E1", "COMMS-SEND", "message", self.views.mother_space()),
            "the permission died with the incarnation — a permission on an entity that does "
            "not outlive its process is stored-copy rot one layer down")
        # and it derives WITH ITS CITATION
        self.assertTrue(any(g.get("grantee") == "E1" for g in self.views.grants().values()))

    def test_a6_an_incarnation_fact_lands_on_the_process_and_does_not_survive_it(self):
        """A6 — KIND: DRIVEN. The mirror of A5, and it is here because A5 ALONE PASSES ON A
        DESIGN THAT SIMPLY NEVER EXPIRES ANYTHING."""
        self.establish("E1")
        self.gate.execute("GRANT", "owner",
                          {"grant_id": "g1", "grantee": "E1", "actions": ["COMMS-SEND"],
                           "info": "message", "space": self.views.mother_space()})
        proc = "proc:E1#1"
        self._incarnate_and_end(proc)

        self.assertNotIn(proc, self.sched.runnable(),
                         "the incarnation-scoped fact outlived the incarnation")
        # printed beside A5's surviving one: the entity's permission still derives
        self.assertTrue(self.views.covers("E1", "COMMS-SEND", "message", self.views.mother_space()))


# =====================================================================================
# A8 — MOMENT (close end, AUDITED not VERIFIED) · R1 — the founding moved
# =====================================================================================

class FoundingMovedCase(unittest.TestCase):

    def test_r1_the_founding_moved_byte_unchanged_would_be_a_failing_outcome(self):
        """R1 — a law pass whose founding does not move DID NOTHING. Asserted at the law level
        rather than on a digest, because a digest row would also green on an unrelated edit."""
        definition = comms_open_definition()
        self.assertNotEqual(definition["checks"], [],
                            "COMMS-OPEN still carries no checks — the pack did not move")
        self.assertIn("entity", definition["params"])
        self.assertIn("role", definition["params"])
        self.assertIn("entity", definition["payload_from"])
        self.assertIn("role", definition["payload_from"])

    #: EP-30-C1's CLOSE END, as a commit that is only ever an ALIAS FOR BYTES.
    #:
    #: [DERIVED INDEPENDENTLY OF THE PROPERTY THIS ROW ASSERTS (board `:1057`), by the route
    #:  `W1B_CLOSE_COMMIT` and `W2_CLOSE_COMMIT` in tests/test_ep30.py were derived by: A
    #:  RECORDED MOMENT, never a version search. A pin chosen as "the last commit whose
    #:  founding still said 1.27.0" would select BY the assertion and leave this row unable to
    #:  fail. This one is the tree at 2026-08-21T08:54:11Z, the autosync commit standing when
    #:  EP-30-C3 took its opening ground — a moment two hands recorded for a different purpose
    #:  before this row's repair existed.
    #:  CROSS-CHECKED BY A ROUTE THAT NEVER READS THE VERSION FIELD, and the digest is the pin
    #:  while the commit is its alias (board `:962`): the pack blob here hashes to
    #:  ebefbd58…, 211,404 bytes, which is EXACTLY what EP-30-C1's OWN BUILDER recorded as its
    #:  close at planning/evidence/EP-30-C1/A8-CLOSE-END.txt on 2026-08-20T10:42:23Z — written
    #:  before EP-30-C3 existed at all. The row checks that digest below rather than trusting
    #:  the alias.]
    C1_CLOSE_COMMIT = "77b50e413321a36d733c24447b5bf7c05fc43219"
    C1_CLOSE_PACK_SHA = "ebefbd58f94dc6a190834db4e0a66083d08fdd9c05462207bce915e6208fdd66"

    def test_a8_the_version_discriminator_moved_by_minor(self):
        """A8 — KIND: MOMENT (this is its AUDITABLE arithmetic, not its open-end reading).

        The open end is a reading of a moment taken by exactly one hand before the first edit
        and preserved at planning/evidence/EP-30-C1/A8-OPEN-END.txt. A later hand AUDITS this
        arithmetic; it can never re-drive that reading. MAJOR would be a STOP (S5).

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION. CAUSE: RANGE.
        SUBJECT-ERA: HISTORICAL — C1's move is finished, and this row's own first sentence
        calls itself a MOMENT. CAUSE, DRIVEN: EP-30-C3 moved the founding 1.27.0 -> 1.28.0.
        ASSERTED: the CLOSE end read from `founding_version()` — THE LIVE TREE. A row that
        declares itself a moment and then reads the live tree is a MOMENT AT ONE END ONLY, and
        the open end silently made C1's arithmetic a claim about every founding move that
        arrives afterwards, forever — this campaign's open-range family, arriving on a row that
        had already named itself immune to it.
        SUPERSEDED: the close end read from the pack at `C1_CLOSE_COMMIT`, verified BY DIGEST
        above. Both ends of the arithmetic are now closed and neither can drift again.
        REMAINS TRUE, carrying both its literals unchanged: C1 moved the founding by exactly one
        MINOR, 1.26.0 -> 1.27.0, and reset PATCH.
        GIVEN UP: nothing this row ever asserted. What it GAINS is re-drivability — the close
        end was a preserved reading no later hand could re-take, and it is now bytes in git that
        any hand can re-read. The MOMENT half that genuinely cannot be re-driven is the OPEN
        end, and that stays a literal, exactly as its own docstring requires.]"""
        opened = (1, 26, 0)                     # the open-end reading, 1.26.0
        self.assertEqual(
            hashlib.sha256(era_pin.blob_at(self.C1_CLOSE_COMMIT,
                                           era_pin.PACK_PATH)).hexdigest(),
            self.C1_CLOSE_PACK_SHA,
            "the close-era pack is not the bytes EP-30-C1 recorded closing over, so the "
            "commit below is an alias for something else and the arithmetic is about the "
            "wrong world")
        now = tuple(int(part) for part
                    in era_pin.pack_at(self.C1_CLOSE_COMMIT)["founding_version"].split("."))
        self.assertEqual(now[0], opened[0],
                         "the founding version moved by MAJOR — S5 says stop, to the owner")
        self.assertEqual(now[1], opened[1] + 1, "expected a MINOR move")
        self.assertEqual(now[2], 0, "a MINOR move resets PATCH")


# =====================================================================================
# R2 / R3 — the two refusals that separate REQUIRED from CHECKED
# =====================================================================================

class RedWorldsCase(WorldCase):

    def test_r2_an_entity_that_was_never_established_is_refused(self):
        """R2 — the entity is PRESENT but UNKNOWN. This separates *required* from *checked*: a
        param can be mandatory and still unverified, and a row that only asserted presence would
        go green on a world where ANY STRING IS AN ENTITY."""
        rule, message = self.refusal_of(self.opens, "E-never-established", "sys:1", SYSTEM)
        self.assertEqual(rule, "CAP-IS-LAW")
        self.assertIn("entity", message.lower())

        # the positive control: the SAME act, once the entity exists, is admitted
        self.establish("E-never-established")
        self.opens("E-never-established", "sys:1", SYSTEM)
        self.assertIn("sys:1", self.comms.open_channels())

    def test_r3_a_third_role_value_is_refused_by_settled_law_not_by_a_parse_error(self):
        """R3 — `role: "storage"`. design/39 §7 rejected three-or-more default channels BY NAME,
        so this is SETTLED LAW REFUSING, and the refusal must CITE the rule rather than raise a
        parse failure."""
        self.establish("E1")
        rule, message = self.refusal_of(self.opens, "E1", "store:1", "storage")
        self.assertEqual(rule, "COMM-LAW-CONTRACT",
                         "a third role value raised something other than a cited refusal")
        # THE ASSERTION IS NO STRONGER THAN WHAT THE LAW'S OWN SENTENCE CARRIES. An earlier
        # spelling of this row demanded the OFFENDING VALUE be echoed; the pack's declared
        # message names the two lawful roles instead, and a test asserting more than the
        # artefact states is a claim about the test author, not about the law.
        self.assertIn(SYSTEM, message)
        self.assertIn(USER, message)
        # nothing was minted for the refused role
        self.assertEqual(self.comms.channels_of("E1"), {SYSTEM: None, USER: None})

    def test_r5_two_entities_may_hold_the_same_channel_name_and_stay_distinct(self):
        """R5 — TWO ENTITIES, SAME CHANNEL NAME. A cure that keys on the NAME ALONE passes every
        row above and fails here: it is the exact shape of the red fact, seen from the other
        side."""
        self.establish("E1")
        self.establish("E2")
        self.opens("E1", "c", SYSTEM)
        self.opens("E2", "c", SYSTEM)

        self.assertEqual(self.comms.channels_of("E1")[SYSTEM], "c")
        self.assertEqual(self.comms.channels_of("E2")[SYSTEM], "c")
        self.assertEqual(len(self.comms.live_channels()), 2,
                         "two entities' same-named channels folded into one entry — the view "
                         "keyed on the name alone")

    def test_r5_red_world_a_view_keyed_on_the_name_alone_loses_one_of_the_two_entities(self):
        """R5's RED WORLD, GENERATED THROUGH THE INSTRUMENT rather than asserted.

        THE DEFECT LIVES IN THE VIEW, which is where R5 says it lives — "a cure that keys on
        the name alone". The retired fold folded openings into a `set()` of names, so two
        entities holding one name were ONE entry and the second entity's channel was
        indistinguishable from the first's.

        UNREACHABLE BY EVERY OTHER ROW IN THIS FILE: A3, R2, R3 and R4 each use one entity, so
        a name-keyed fold answers them exactly as the true one does. Only R5 moves."""
        self.establish("E1")
        self.establish("E2")
        self.opens("E1", "c", SYSTEM)
        self.opens("E2", "c", SYSTEM)

        real = CommsView.live_channels

        def name_keyed(view, as_of=None):
            # the defect: the fold forgets whose the channel is, exactly as the retired
            # `set()` of strings did
            collapsed = {}
            for (_entity, channel), role in real(view, as_of).items():
                collapsed[(None, channel)] = role
            return collapsed
        CommsView.live_channels = name_keyed
        self.addCleanup(setattr, CommsView, "live_channels", real)

        self.assertEqual(len(self.comms.live_channels()), 1,
                         "the name-keyed fold did not collapse the two entries, so this red "
                         "world proves nothing")
        # and the consequence that matters: NEITHER entity can be answered for
        self.assertEqual(self.comms.channels_of("E1"), {SYSTEM: None, USER: None})
        self.assertEqual(self.comms.channels_of("E2"), {SYSTEM: None, USER: None})


# =====================================================================================
# R4 — THE NEAR-MISS CONTROL, AND ITS POLARITY IS THE OPPOSITE OF WHAT THE SHAPE SUGGESTS
# =====================================================================================

class ReopenAfterCloseCase(WorldCase):

    def test_r4_a_reopen_after_a_close_SUCCEEDS(self):
        """R4 — KIND: DRIVEN, near-miss control (§A64). Open two, CLOSE one, open a third.

        EXPECTED: THE RE-OPEN SUCCEEDS. The invariant counts LIVE openings at a moment, never
        openings across a lifetime (design/39 §3, board :1529). A lifetime quota would bar every
        program restart and contradict the design at its core."""
        self.establish("E1")
        self.opens("E1", "sys:1", SYSTEM)
        self.opens("E1", "usr:1", USER)
        self.gate.execute("COMMS-CLOSE", "E1", {"channel": "sys:1"})  # EP-49C: a close is whose-keyed — the holder (entity) closes its own opening
        self.assertNotIn("sys:1", self.comms.open_channels())

        self.opens("E1", "sys:2", SYSTEM)               # the third recorded act, lawfully

        self.assertEqual(self.comms.channels_of("E1"), {SYSTEM: "sys:2", USER: "usr:1"})
        self.assertEqual(len(self.store.by_action("COMMS-OPEN")), 3,
                         "three openings were recorded as history — the record holds every act")
        self.assertEqual(len(self.comms.live_channels()), 2,
                         "the LIVE set is two; the third act is history, not an occupant")

    def test_r4_red_world_an_implementation_that_counts_recorded_acts_refuses_the_lawful_reopen(self):
        """R4's RED WORLD, GENERATED THROUGH THE INSTRUMENT: the naive implementation that counts
        recorded ACTS rather than computing the LIVE SET. It bars the restart.

        UNREACHABLE BY EVERY ROW ABOVE — A3's refusal, R2's, R3's and R5's all still behave
        exactly as they do in the true world, because none of them closes anything. Only the
        re-open moves, which is why this world needs its own row."""
        self.establish("E1")
        self.opens("E1", "sys:1", SYSTEM)
        self.opens("E1", "usr:1", USER)
        self.gate.execute("COMMS-CLOSE", "E1", {"channel": "sys:1"})  # EP-49C: a close is whose-keyed — the holder (entity) closes its own opening

        real = opdefs_mod._live_slots

        def counts_acts(store, check, as_of=None):
            # the defect: openings accumulate across the lifetime; a close frees nothing
            live = {}
            for e in sorted(store.by_action(check["open_action"], as_of),
                            key=lambda e: e["seq"]):
                p = e.get("payload") or {}
                slot = tuple(p.get(k) for k in check["slot_params"])
                live[(slot, p.get(check["instance_param"]))] = slot
            return live
        opdefs_mod._live_slots = counts_acts
        self.addCleanup(setattr, opdefs_mod, "_live_slots", real)

        rule, _ = self.refusal_of(self.opens, "E1", "sys:2", SYSTEM)
        self.assertEqual(rule, "COMM-LAW-CONTRACT",
                         "the act-counting fold did not bar the re-open, so this red world "
                         "proves nothing")


# =====================================================================================
# THE DEFINITION-TIME GUARDS — a malformed slot law must be UNREPRESENTABLE, not unlikely
# =====================================================================================

class MalformedDeclarationCase(WorldCase):

    def _create_op(self, checks):
        return self.gate.execute("CREATE-OP", "owner", {
            "name": "PROBE-OP",
            "definition": {"description": "a probe", "params": {"x": "required"},
                           "law_cited": "CAP-IS-LAW", "object_param": "x", "checks": checks}})

    def test_a_value_domain_declaring_an_empty_domain_is_refused_at_definition_time(self):
        """A domain that is absent or empty ADMITS EVERY VALUE WHILE READING AS A RESTRICTION —
        it would behave as no check while the op carried a false statement about itself."""
        rule, message = self.refusal_of(
            self._create_op, [{"check": "value_domain", "param": "role", "domain": [],
                               "cite": "CAP-IS-LAW"}])
        self.assertEqual(rule, "AR-2")
        self.assertIn("domain", message)

    def test_a_live_slot_declaring_no_slot_params_is_refused_at_definition_time(self):
        """No slot_params and every act shares ONE slot — admitting exactly one opening in the
        whole estate."""
        rule, message = self.refusal_of(
            self._create_op, [{"check": "live_slot", "open_action": "A", "close_action": "B",
                               "instance_param": "x", "slot_params": [], "cite": "CAP-IS-LAW"}])
        self.assertEqual(rule, "AR-2")
        self.assertIn("slot_params", message)

    def test_a_live_slot_declaring_no_close_action_is_refused_at_definition_time(self):
        """Without a close action the live set only ever grows, and the check silently becomes
        the LIFETIME QUOTA this law exists to refuse."""
        rule, _ = self.refusal_of(
            self._create_op, [{"check": "live_slot", "open_action": "A", "close_action": "",
                               "instance_param": "x", "slot_params": ["e"], "cite": "CAP-IS-LAW"}])
        self.assertEqual(rule, "AR-2")


if __name__ == "__main__":
    unittest.main()
