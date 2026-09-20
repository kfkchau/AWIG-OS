# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-30-W1a — the DECLARED STREAM KEY. Engine only; this pass moves no law.

WHAT CHANGED, in one sentence: the DOOR an act enters no longer decides the STREAM its
declaration lands in. The interpreter sets a record's `action` to the op's own registered
name and `store.by_action` locates by that field, so a declaration could not land anywhere
but under the door that wrote it. A definition may now DECLARE the stream instead, and the
engine honours it — while `action` goes on carrying the door, unchanged.

NO SHIPPED OP DECLARES THE KEY IN THIS PASS, and the founding is byte-unchanged. The
capability lands here; its first use is a separate law pass.

The acceptance battery this file carries:

  T-EP30-DEFAULT-PRESERVES-THE-WORLD   Constraint 1 (board :918). All 77 shipped ops write a
                                       record carrying NO stream field and indexed under
                                       their own action — the population asserted whole, by
                                       enumeration, never sampled. RED WORLD: an engine that
                                       honours the key UNCONDITIONALLY, driven below. A
                                       default-preservation row that cannot be made to fail
                                       has asserted nothing.

  T-EP30-THE-DOOR-IS-NEVER-ERASED      Constraint 2. ONE record carries BOTH facts: which
                                       OPERATION wrote it, read back by name from the record
                                       itself, and the DECLARED stream it landed in, read
                                       from the store's own index. RED WORLD: a key that
                                       overwrites the recorded act rather than the stream —
                                       the W4e class built on purpose, where the record holds
                                       an act nobody performed while every view derived from
                                       it still agrees. Reachable here as a driven red, never
                                       as a shipped behaviour.

  T-EP30-THE-KEY-IS-HONOURED           Both arms, in a SCRATCH pack and never the shipped
                                       one. A declaration carrying the key lands under the
                                       declared stream and NOT under its door; the same
                                       declaration without the key lands under its door. One
                                       arm alone is not evidence — the second is what
                                       separates "the key works" from "everything lands
                                       there".

  T-EP30-NEAR-MISS-KEY-IS-REFUSED      §A64, and the sharpest row here. A key one character
                                       from `record_stream` is REFUSED at the definition
                                       door, not ignored. Both directions driven: six
                                       near-miss spellings refused, AND the controls proving
                                       the exact name is accepted and an unrelated key is not
                                       swept up. A malformed key that falls back to the
                                       default is a fail-open wearing a default's clothes —
                                       nothing goes red, no view disagrees, and the founding
                                       says one thing while the record does another.

  T-EP30-A-PLANT-ELSEWHERE-DOES-NOT-RED-THE-ROW
                                       A plant on a DIFFERENT op must NOT red the honoured-key
                                       row. A row reddened by a plant elsewhere is measuring
                                       its fixture rather than its subject.

WHAT THIS FILE DOES NOT ASSERT, stated rather than left as an absence. It makes no claim
about whether a declared stream must NAME AN EXISTING OP — nothing here refuses a stream
value that no op answers to, and that is a law-surface question this engine pass does not
answer. It makes no claim about SUBSET SELECTION: a record projection selects its subset by
`action` (the door) and indexes by stream, and no shipped op declares a stream, so the case
where those disagree is unreachable today and is untested here rather than quietly assumed
safe. Both are raised in the close, not settled here.
"""
import copy
import io
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json                                                        # noqa: E402
import era_pin                                                     # noqa: E402
from kernel.compose import build_full_kernel                       # noqa: E402
from kernel.errors import OpError                                  # noqa: E402
from kernel.store import EchoMismatch, EventStore, stream_of       # noqa: E402

OWNER = "owner"
PACK = os.path.join(REPO, "src", "founding", "founding-pack.json")

#: The scratch pack's two ops. Identical but for the one key under test, which is what makes
#: the pair a controlled comparison rather than two separate observations.
SCRATCH_BASE = {"law_cited": "ROOT-NEG-5", "description": "an EP-30 scratch op",
                "params": {"content": "required"}, "object_param": "content",
                # `content` is this op's OBJECT_PARAM, recorded INLINE via payload_from and read
                # inline by the stream-landing rows below — a structural object handle carrying a
                # short id ("x"/"ep30-content"), not a custody-conserved body. Content-homing is
                # refused for this shape (an object_param is never blob-homed); STRUCTURAL is the
                # op's own declared true nature (vocabulary door, design/46 member 2).
                "structural_params": ["content"],
                "payload_from": ["content"]}
DECLARED_STREAM = "EP30-DECLARED-STREAM"


def shipped_ops():
    """THE POPULATION, READ FROM THE STRUCTURE (§A51). Every `op_definition` record in the
    shipped pack IS an op; the figure is an enumeration and never a name-pattern filter."""
    found = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("kind") == "op_definition" and "name" in o:
                found.append((o["name"], o["definition"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    with open(PACK, encoding="utf-8") as fh:
        walk(json.load(fh))
    return sorted(found)


class _Live(unittest.TestCase):
    """A kernel composed from the SHIPPED founding and nothing else."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep30-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    # ---- the scratch pack ----
    def make_op(self, name, **extra):
        d = dict(SCRATCH_BASE)
        d.update(extra)
        self.gate.execute("CREATE-OP", OWNER, {"name": name, "definition": d})
        return d

    def fire(self, name, content="x"):
        return self.gate.execute(name, OWNER, {"content": content})

    # ---- THE CLAUSES, written once and called by BOTH the green row and its red world ----
    # This is what makes a red world test the instrument rather than a copy of it (§A42): the
    # plant runs the SAME assertion the green row runs, so a red world proves that assertion
    # can fail rather than proving some paraphrase of it can.

    def clause_default_preserves_the_world(self):
        """Constraint 1, over the whole shipped population."""
        drove = []
        for name, _d in shipped_ops():
            before = len(self.store.events)
            try:
                self.gate.execute(name, "SYSTEM", {p: f"ep30-{p}" for p in (_d.get("params") or {})})
            except OpError:
                pass                                    # a refusal still writes a record
            except Exception:                           # noqa: BLE001
                pass
            for rec in self.store.events[before:]:
                self.assertNotIn(
                    "record_stream", rec,
                    f"{name} writes a record carrying a stream field though its definition "
                    "declares none — the default no longer preserves the world")
                self.assertEqual(
                    stream_of(rec), rec["action"],
                    f"{name}'s record is indexed away from its own action without declaring a "
                    "stream")
            drove.append(name)
        # [87 SINCE THE SOCKET-GRANTS FOUNDING MOVE, EP-48-BUILD §A57 re-derivation: 81 -> 87.
        #  81 SINCE THE OPEN-CONTENT FOUNDING MOVE, MAINT §A57, EP-FND-OPEN-OP: 80 -> 81.
        #  Was 80 SINCE THE COMPLETE-KEY-FAMILY MOVE (architect `:2895`); 77 SINCE EP-30-C3R, 2026-08-21.
        #  THE LITERAL IS HAND-COMPUTED AND STAYS A LITERAL: `len(shipped_ops())` would compare this
        #  enumeration with itself and could never fail, which is the one thing this line exists to
        #  prevent. EP-48 (SOCKET-GRANTS, the campaign-5 founding mover) added SIX ops — SOCKET-OPEN /
        #  BIND / LISTEN / CONNECT / ACCEPT / CLOSE — as founding data (MINOR 1.39.0 -> 1.40.0), driven
        #  from the live census at dispatch (87, not carried). This is the LIVE, DELIBERATELY-NOT-ERA-
        #  PINNED census (this class's own docstring, line 213), so the six new ops move it — unlike the
        #  era-pinned population pins in test_ep28j/k/n/n2, which read historical packs and do not.
        #  EP-49A (THE BORDER: THE DOOR, the campaign-5 crux) added THREE more — BORDER-SUBMIT / REPLY /
        #  REFUSAL — as founding data (MINOR 1.40.0 -> 1.41.0), 87 -> 90, driven from the live census at
        #  dispatch; the EP-named op-census pins (test_ep28n/n2/k) are era-pinned and did NOT move, so
        #  THIS live pin is the one the border bump disturbs (disclosed to mgr, beyond the EP-49A fence).
        #  EP-49D (THE RECEIPT) added ONE more — RECEIPT — as founding data (MINOR 1.42.0 -> 1.43.0),
        #  90 -> 91, the §A57 live-census companion the EP-49D builder missed, widened at mgr's hand
        #  (the :3255(b) by-name pattern; the era-pinned pins above still do not move).
        #  EP-50 (VIEW-SERVICING) added ONE more — VIEW-SERVICE — as founding data (MINOR 1.43.0 ->
        #  1.44.0), 91 -> 92, this live-census pin moved BY NAME at dispatch (the era-pinned pins do not).
        #  EP-52 (FIREWALL-IN-THE-RECORD, C5 P7) added ONE more — FILTER-DECISION — as founding data
        #  (MINOR 1.45.0 -> 1.46.0), 92 -> 93, this live-census pin moved BY NAME at dispatch (the §A57
        #  sweep; the era-pinned pins in test_ep28j/k/n/n2/ep51 do not).
        #  C6a VT-2 (CREATE-RELATIONSHIP MINTED live, MINOR 1.51.0 -> 1.52.0) moved 93 -> 94 BY NAME (§A57).]
        self.assertEqual(len(drove), 94, "the population is 94 ops, enumerated from the pack")
        return drove

    def clause_the_door_is_never_erased(self, door, stream):
        """Constraint 2: BOTH facts, in ONE record."""
        landed = self.store.by_action(stream)
        self.assertTrue(landed, f"nothing landed under the declared stream {stream!r}")
        rec = landed[-1]
        # fact 1 — WHICH OPERATION wrote it, by name, from the record itself
        self.assertEqual(rec["action"], door,
                         "the record does not say which operation wrote it: the door was "
                         "erased, which is the W4e class — a record holding an act nobody "
                         "performed while every view derived from it still agrees")
        # fact 2 — the stream it landed in, from the STORE'S OWN INDEX, not from the record
        self.assertIn(rec, self.store.by_action(stream),
                      "the store does not index the record under its declared stream")
        return rec

    def clause_the_key_is_honoured(self, door, stream):
        """The declared stream receives it; the door does not."""
        self.assertEqual(len(self.store.by_action(stream)), 1,
                         f"the declared stream {stream!r} did not receive the record")
        self.assertEqual(len(self.store.by_action(door)), 0,
                         f"the record is still indexed under its door {door!r} — the "
                         "declaration moved nothing")


class TestDefaultPreservesTheWorld(_Live):
    """T-EP30-DEFAULT-PRESERVES-THE-WORLD. Constraint 1, asserted over all 77 and not a
    sample. A single differing op is S4."""

    def test_all_76_shipped_ops_write_an_unmoved_record(self):
        """[DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION. CAUSE:
        POPULATION. SUBJECT-ERA: LIVE, and that decides the repair. EP-30-C3 minted
        FILE-CUSTODY-TRANSFER, so the shipped population is 77.
        ASSERTED: the population is 76. SUPERSEDED: 77, at both non-vacuity sites — this row's
        and the clause's own.
        RE-DERIVED AND DELIBERATELY NOT ERA-PINNED. Constraint 1 is a claim about THE ENGINE
        TODAY, so an era-pin here would drive the 76 operations of a closed world against a
        live kernel and STOP WATCHING THE ONE OPERATION THAT JUST ARRIVED — green while
        asserting nothing, which is the failure mode this arc has paid for. THIS REPAIR MAKES
        THE GUARD COVER MORE, not less: FILE-CUSTODY-TRANSFER is now driven by it.
        REMAINS TRUE, unchanged in substance: every shipped op writes a record carrying no
        stream field and indexed under its own action, asserted whole and never sampled.
        GIVEN UP: nothing.
        AND THE NAME IS NOW STALE, DELIBERATELY. The method name says 76 and the row asserts
        77. RENAMING IT WOULD CHANGE THE ROW'S ID, and an id that changes is indistinguishable
        from a deletion plus an addition — which is exactly what this unit's R2 exists to
        refuse. The id is kept and the mismatch is RAISED rather than tidied: a row that
        carries a moving figure in its own name has no repair that is both id-stable and
        name-true, and choosing between those two is not a builder's call.]"""
        drove = self.clause_default_preserves_the_world()
        # [MAINT §A57 re-derivation, EP-FND-OPEN-OP: 80 -> 81. The OPEN-CONTENT founding move (the
        #  content-sealing production activation) added ONE op; earlier: 77 -> 80 (the COMPLETE-KEY-FAMILY
        #  move, architect `:2895`). This row's docstring says it is a claim about THE ENGINE TODAY,
        #  so the literal tracks the live census and is deliberately NOT era-pinned. The method
        #  name still says 76 by its own ruling (id stable; the name-vs-figure mismatch is
        #  deliberate per the docstring above). 81 -> 87: EP-48-BUILD (SOCKET-GRANTS, the campaign-5
        #  founding mover, 1.39.0 -> 1.40.0) added six socket ops; §A57 name-and-count widen at mgr's
        #  hand under :3255(b) — the companion to the :180 live-census pin the EP-48 builder widened,
        #  missed here; driven at the gate, not carried. 87 -> 90: EP-49A-BUILD (THE BORDER: THE DOOR,
        #  the campaign-5 crux, 1.40.0 -> 1.41.0) added three border ops (BORDER-SUBMIT/REPLY/REFUSAL);
        #  the same live-census companion, driven at the gate, disclosed to mgr as a §A57 sweep hit
        #  beyond the EP-49A fence's enumerated pin files. EP-49D (THE RECEIPT, 1.42.0 -> 1.43.0) added
        #  RECEIPT, 90 -> 91 — the second live-census pin the EP-49D builder missed, widened at mgr's hand.
        #  EP-50 (VIEW-SERVICING, 1.43.0 -> 1.44.0) added VIEW-SERVICE, 91 -> 92 — the SECOND census pin
        #  moved BY NAME at dispatch (the EP-49D lesson folded: a founding op-mint moves BOTH census pins).
        #  EP-52 (FILTER-DECISION, 1.45.0 -> 1.46.0) moved 92 -> 93 — BOTH census pins moved by name (§A57).
        #  C6a VT-2 (CREATE-RELATIONSHIP MINTED, 1.51.0 -> 1.52.0) moved 93 -> 94 — BOTH census pins by name (§A57).]
        self.assertEqual(len(set(drove)), 94)

    def test_THE_RED_WORLD_an_engine_that_honours_the_key_unconditionally(self):
        """R1, produced THROUGH the real append path (§A42). The plant makes every record
        carry a stream whether or not its definition declares one — which is precisely what
        "honour the key unconditionally" means — and the constraint-1 clause must RED.

        A default-preservation row that cannot be made to fail has asserted nothing, so this
        row's value is entirely in the AssertionError below being reachable."""
        original = EventStore._append_one

        def planted(store_self, ev, f):
            ev = dict(ev)
            ev["record_stream"] = ev["action"]      # unconditional: no declaration consulted
            return original(store_self, ev, f)

        with unittest.mock.patch.object(EventStore, "_append_one", planted):
            with self.assertRaises(AssertionError) as caught:
                self.clause_default_preserves_the_world()
        self.assertIn("record_stream", str(caught.exception))


class TestTheDoorIsNeverErased(_Live):
    """T-EP30-THE-DOOR-IS-NEVER-ERASED. Constraint 2, and the stop it carries: if the
    record's shape could not hold both facts, this pass STOPS and RAISES rather than
    overwriting. It holds both — the rows below are that fact, driven."""

    def test_one_record_carries_the_door_and_the_stream(self):
        self.make_op("EP30SPEAKER", record_stream=DECLARED_STREAM)
        self.fire("EP30SPEAKER")
        rec = self.clause_the_door_is_never_erased("EP30SPEAKER", DECLARED_STREAM)
        # and the two facts are genuinely DIFFERENT values, or the row would pass on a record
        # where the door and the stream happen to coincide and assert nothing
        self.assertNotEqual(rec["action"], DECLARED_STREAM,
                            "the door and the stream must differ for this row to mean anything")

    def test_THE_RED_WORLD_a_key_that_overwrites_the_act_rather_than_the_stream(self):
        """R2, the W4e class built ON PURPOSE and reachable as a red world rather than only
        forbidden in prose. The plant makes the declared key rewrite the RECORDED ACT instead
        of naming a stream, so the record lands under the declared name carrying no trace of
        the operation that wrote it. The door-is-never-erased clause must RED.

        This is the shape S5 exists to stop: every view derived from such a record agrees with
        itself, the round trip is green, and the record holds an act nobody performed.

        THE PLANT IS AT THE DRAFT, and where it sits is not a detail. An engine that keys
        records this way builds them this way — in the interpreter, before the gate appends —
        so the draft and the record agree and nothing upstream objects. Planting the same
        mutation AFTER the draft instead exhibits a different world entirely, and the row
        below is that finding kept rather than discarded."""
        self.make_op("EP30SPEAKER", record_stream=DECLARED_STREAM)
        entry = self.gate.ops["EP30SPEAKER"]
        original = entry["handler"]

        def planted(actor, params):
            rec = original(actor, params)
            rec["action"] = rec.pop("record_stream")     # the door, overwritten
            return rec

        entry["handler"] = planted
        try:
            self.fire("EP30SPEAKER")
            with self.assertRaises(AssertionError) as caught:
                self.clause_the_door_is_never_erased("EP30SPEAKER", DECLARED_STREAM)
        finally:
            entry["handler"] = original
        self.assertIn("which operation wrote it", str(caught.exception))

    def test_the_echo_catches_the_same_overwrite_applied_AFTER_the_draft(self):
        """FOUND BY ATTEMPTING R2'S EXHIBITION, and kept because it is a guard nobody had
        asked about. The first form of the plant above mutated the record inside the store,
        after the draft was formed — and it never reached the clause at all, because the
        APPEND ECHO refused first: the appended record disagreed with the draft on a field the
        draft stated.

        So the W4e class has TWO independent guards for two different origins. A record built
        wrong by the engine is caught by the door-is-never-erased row above. A record mutated
        between the draft and the append is caught here, by a mechanism that was already in
        place and that this pass extended to cover the stream field itself."""
        self.make_op("EP30SPEAKER", record_stream=DECLARED_STREAM)
        original = EventStore._append_one

        def planted(store_self, ev, f):
            ev = dict(ev)
            if ev.get("record_stream"):
                ev["action"] = ev.pop("record_stream")   # mutated AFTER the draft
            return original(store_self, ev, f)

        with unittest.mock.patch.object(EventStore, "_append_one", planted):
            with self.assertRaises(EchoMismatch):
                self.fire("EP30SPEAKER")


class TestTheKeyIsHonoured(_Live):
    """T-EP30-THE-KEY-IS-HONOURED. Both arms, in a scratch pack. The shipped pack is never
    touched and no shipped op declares the key."""

    def test_a_declaration_carrying_the_key_lands_under_the_declared_stream(self):
        self.make_op("EP30SPEAKER", record_stream=DECLARED_STREAM)
        self.fire("EP30SPEAKER")
        self.clause_the_key_is_honoured("EP30SPEAKER", DECLARED_STREAM)

    def test_the_SAME_declaration_without_the_key_lands_under_the_door(self):
        """The second arm, and it is what makes the first one evidence. Without it, a store
        that indexed everything under one name would pass the first arm."""
        self.make_op("EP30SILENT")                       # identical but for the key
        self.fire("EP30SILENT")
        self.assertEqual(len(self.store.by_action("EP30SILENT")), 1,
                         "an op declaring no stream must land under its own door")
        self.assertEqual(len(self.store.by_action(DECLARED_STREAM)), 0,
                         "an op declaring no stream reached the declared stream anyway")
        self.assertNotIn("record_stream", self.store.by_action("EP30SILENT")[-1],
                         "an op declaring no stream wrote a stream field")

    def test_the_founding_pack_is_not_the_scratch_pack(self):
        """W1a's rows are driven in a SCRATCH pack, and the shipped population that declares
        the key is NAMED rather than assumed empty.

        [DOCUMENTED FLIP — EP-30-W1b, 2026-08-16.
        ASSERTED: `declaring == []` — NO shipped op declares the key, which was W1a's own
        lands-nothing property and true of the world W1a closed in.
        SUPERSEDED: `declaring == ["UNBIND"]`, the population NAMED. EP-30-W1b is the
        capability's first use and puts the key on op:UNBIND by law.
        REMAINS TRUE, and it is why this row is not merely relaxed: NO OP GAINS THIS KEY
        WITHOUT A LAW PASS SAYING SO. An empty list and a named list are the same guard; a
        list is the form that survives the capability being used. A second op appearing here
        without its own pass is exactly what this row still catches.
        GIVEN UP: nothing. `assertEqual` against a NAMED list keeps both directions — an
        op added here reds it, and an op silently losing the key reds it too.]"""
        declaring = sorted(n for n, d in shipped_ops() if d.get("record_stream"))
        self.assertEqual(declaring, ["UNBIND"],
                         "the set of shipped ops declaring a stream key moved without a law "
                         "pass naming the change")


class TestNearMissKeyIsRefused(_Live):
    """T-EP30-NEAR-MISS-KEY-IS-REFUSED. §A64 in both directions: a pattern that has never met
    a near-miss has never been tested, and a refusal that has never met the exact name has
    never been shown to discriminate."""

    NEAR_MISSES = ("record_streem", "record_strea", "record_streams",
                   "recordstream", "record_stram", "Record_stream")

    def test_six_near_miss_spellings_are_refused_at_the_door(self):
        for i, spelling in enumerate(self.NEAR_MISSES):
            with self.subTest(spelling=spelling):
                with self.assertRaises(OpError) as caught:
                    self.make_op(f"EP30NM{i}", **{spelling: DECLARED_STREAM})
                self.assertIn(spelling, str(caught.exception))

    def test_CONTROL_the_exact_name_is_not_refused(self):
        """The near-miss row is uninterpretable without this one: a validator that refused
        everything would pass the row above and destroy the capability."""
        self.make_op("EP30EXACT", record_stream=DECLARED_STREAM)
        self.fire("EP30EXACT")
        self.clause_the_key_is_honoured("EP30EXACT", DECLARED_STREAM)

    def test_CONTROL_an_unrelated_key_is_not_swept_up(self):
        """The other half of discrimination. The refusal targets keys that were TRYING to be
        `record_stream`; a definition key that merely resembles it in theme is untouched."""
        self.make_op("EP30UNRELATED", record_streaming_policy="whatever")
        self.fire("EP30UNRELATED")
        self.assertEqual(len(self.store.by_action("EP30UNRELATED")), 1)

    def test_a_malformed_value_is_refused_rather_than_falling_back(self):
        """S7's other route. An empty or non-string value would fall back to the door exactly
        as a missing key does — the same fail-open reached differently."""
        for i, bad in enumerate(("", None, 7, [])):
            with self.subTest(value=bad):
                with self.assertRaises(OpError):
                    self.make_op(f"EP30BADVAL{i}", record_stream=bad)


class TestAPlantElsewhereDoesNotRedTheRow(_Live):
    """T-EP30-A-PLANT-ELSEWHERE-DOES-NOT-RED-THE-ROW. R4: a row reddened by a plant on a
    different op is measuring its fixture."""

    def test_a_plant_on_a_DIFFERENT_op_leaves_the_honoured_key_row_green(self):
        self.make_op("EP30SPEAKER", record_stream=DECLARED_STREAM)
        self.make_op("EP30OTHER", record_stream="EP30-OTHER-STREAM")
        self.fire("EP30SPEAKER")
        self.fire("EP30OTHER")
        # the plant: EP30OTHER's records are dragged to a third stream. EP30SPEAKER's row must
        # not notice, or it was never measuring EP30SPEAKER.
        self.assertEqual(len(self.store.by_action("EP30-OTHER-STREAM")), 1)
        self.clause_the_key_is_honoured("EP30SPEAKER", DECLARED_STREAM)
        self.clause_the_door_is_never_erased("EP30SPEAKER", DECLARED_STREAM)


class TestTheStreamHasOneDefinition(unittest.TestCase):
    """The store and its projections must answer "which stream" the same way. Two copies of
    that expression could drift, and the drift would be invisible in the worst way: a fold
    reading through a projection and a check reading the store would locate different sets and
    both would look right."""

    def test_stream_of_defaults_to_the_door(self):
        self.assertEqual(stream_of({"action": "A"}), "A")
        self.assertEqual(stream_of({"action": "A", "record_stream": None}), "A")

    def test_stream_of_prefers_the_declared_stream(self):
        self.assertEqual(stream_of({"action": "A", "record_stream": "B"}), "B")

    #: The two index sites, as the source must spell them. Kept as data so the same clause
    #: runs against the real file and against the planted near-misses below.
    PROJECTION_SITE = 'self._by_action.setdefault(stream_of(e), []).append(e["seq"])'
    STORE_SITE = "self._by_action.setdefault(stream_of(e), []).append(e)"
    OLD_FORM = 'self._by_action.setdefault(e["action"]'

    def clause_one_definition(self, src):
        self.assertIn(self.PROJECTION_SITE, src, "the projection does not route through stream_of")
        self.assertIn(self.STORE_SITE, src, "the store's index does not route through stream_of")
        self.assertNotIn(self.OLD_FORM, src,
                         "an index site still keys on the door directly — two answers to one "
                         "question, and they can drift")

    def test_both_index_sites_route_through_it(self):
        with open(os.path.join(REPO, "src", "kernel", "store.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.clause_one_definition(src)

    def test_NEAR_MISS_the_clause_reds_on_a_source_that_reintroduces_the_old_form(self):
        """§A64. A structural row's subject is the SPACE OF SOURCES that would satisfy it, and
        a pattern that has never met a near-miss has never been tested. Three planted sources,
        each one edit from the real one, each of which MUST red — otherwise this row would go
        on passing while the property it names quietly left."""
        with open(os.path.join(REPO, "src", "kernel", "store.py"), encoding="utf-8") as fh:
            real = fh.read()
        plants = {
            "a third site reintroduces the door-keyed form":
                real + '\n        self._by_action.setdefault(e["action"], []).append(e)\n',
            "the projection reverts to keying on the door":
                real.replace(self.PROJECTION_SITE,
                             'self._by_action.setdefault(e["action"], []).append(e["seq"])'),
            "the store's index reverts to keying on the door":
                real.replace(self.STORE_SITE,
                             'self._by_action.setdefault(e["action"], []).append(e)'),
        }
        for why, planted in plants.items():
            with self.subTest(plant=why):
                self.assertNotEqual(planted, real, "the plant changed nothing — it is not a plant")
                with self.assertRaises(AssertionError):
                    self.clause_one_definition(planted)

    def test_CONTROL_the_clause_passes_the_source_it_is_about(self):
        """The other direction: the clause is not simply refusing everything handed to it."""
        with open(os.path.join(REPO, "src", "kernel", "store.py"), encoding="utf-8") as fh:
            self.clause_one_definition(fh.read())


# =============================================================================================
# EP-30-W1b — THE LAW PASS. The capability above gets its FIRST USE: op:UNBIND's declaration
# names BIND-DEVICE as the stream its records are written under.
#
# WHAT THESE ROWS ASSERT, and it is one sentence: an unbind record LANDS IN THE GRANTING ACT'S
# STREAM WHILE STILL RECORDING THAT UNBIND WROTE IT, so `prior_value`'s latest-seq-wins meets
# the revoking act. EP-30-E1 established that the thirteenth kind already expresses revocation
# where the revoking record is reachable from the granting act's stream — it separated only
# where grant and revoke were ONE operation, and gave ADMIT/ADMIT against this estate's
# SEPARATE op:UNBIND. That blindness is what this pass removes.
#
# WHAT THEY DO NOT ASSERT, stated rather than left as an absence. Nothing here claims any
# operation REFUSES something it used to admit: no consuming operation gains a check in this
# pass, and A5 asserts verdict-for-verdict that nothing new is refused. Enforcement is
# EP-30-W2. Nothing here asserts the containment invariant either — that every device with an
# unbind has a bind — which board :1010 ruled belongs to W2, at the movement whose readers
# start leaning on it.
# =============================================================================================

W1B_STREAM = "BIND-DEVICE"

#: E1's separator SHAPE, transposed to the device family: `prior_value` over the latest
#: BIND-DEVICE record for the named device, asking whether it still declares a driver. E1's own
#: GRANT/role formulation is cited as THE ESTABLISHMENT — the proof the shape can separate at
#: all — and is never this row's subject, because it locates over GRANT and meets no record in
#: BIND-DEVICE's stream. (That mismatch is why this plan's A3 was repaired at board :1029.)
W1B_SEPARATOR = {
    "description": "EP-30-W1b: E1's separator shape over the device family",
    "params": {"device": "required"}, "law_cited": "CAP-IS-LAW",
    # C6 P8 (L28): a probe op founded against the SHIPPED pack (which declares CELL-LAW) must declare
    # a cell or the founding door refuses it — this probe is a structured record-mechanic, cell "S",
    # like every gov-os op (the inversion below inherits it via dict(W1B_SEPARATOR, ...)).
    "cell": "S",
    # `device` is a device identifier ("dev0") — STRUCTURAL, matching the shipped census
    # (BIND-DEVICE/UNBIND/DEVICE-IO-WINDOW-WRITE all declare device structural).
    "structural_params": ["device"],
    "payload_from": ["device"],
    "checks": [{"check": "prior_value", "action": W1B_STREAM, "field": "device",
                "param": "device", "value_field": "driver", "require": "established",
                "cite": "CAP-IS-LAW"}]}


def _pack_with(**unbind_extra):
    """The SHIPPED pack with op:UNBIND's declaration adjusted. Used only to build the RED
    worlds; the green rows read the shipped pack untouched."""
    with open(PACK, encoding="utf-8") as fh:
        p = json.load(fh)
    for s in p["steps"]:
        for r in s["records"]:
            if r.get("action") == "CREATE-OP" and r["payload"].get("name") == "UNBIND":
                d = r["payload"]["definition"]
                for k, v in unbind_extra.items():
                    if v is None:
                        d.pop(k, None)
                    else:
                        d[k] = v
    return p


class _W1bWorld:
    """A world booted from a given pack, its records made by CALLING SHIPPED OPS. The verdict
    is the GATE's and never a reading of a declaration."""

    def __init__(self, pack, probe=None, probe_name="W1BSEP"):
        import copy as _copy
        from founding import install as install_module
        from kernel.boot import build_kernel
        if probe is not None:
            pack = _copy.deepcopy(pack)
            step = [s for s in pack["steps"] if s["step"] == "08-op-definitions"][0]
            step["records"].append({
                "actor": "PC_RUNTIME", "action": "CREATE-OP", "object": "op:%s" % probe_name,
                "rule_cited": "CAP-IS-LAW",
                "payload": {"kind": "op_definition", "rule_id": "op:%s" % probe_name,
                            "polarity": "+", "name": probe_name, "tier": "owner",
                            "text": "an EP-30-W1b probe", "definition": probe}})
        self.dir = tempfile.mkdtemp(prefix="ep30w1b-")
        orig = install_module.load_pack
        install_module.load_pack = lambda *a, **k: _copy.deepcopy(pack)
        try:
            self.store, self.gate, self.views = build_kernel(
                os.path.join(self.dir, "record.jsonl"))
        finally:
            install_module.load_pack = orig

    def call(self, op, **kw):
        return self.gate.execute(op, "SYSTEM", kw)

    def verdict(self, op, **kw):
        try:
            self.call(op, **kw)
            return "ADMIT"
        except OpError as e:
            return "REFUSE:%s" % getattr(e, "rule", "?")

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class _W1bBase(unittest.TestCase):
    """THE CLAUSES, written once and called by BOTH the green rows and their red worlds, so a
    red world proves THAT assertion can fail rather than a paraphrase of it (§A42)."""

    def world(self, pack, **kw):
        w = _W1bWorld(pack, **kw)
        self.addCleanup(w.close)
        return w

    @staticmethod
    def bound(w):
        w.call("REGISTER-CAPABILITY", driver="drv-a")
        w.call("BIND-DEVICE", device="dev0", driver="drv-a")

    def revoked(self, w):
        self.bound(w)
        w.call("UNBIND", device="dev0")

    def clause_separator_pair(self, pack):
        """A3's subject: (verdict while bound, verdict once revoked THROUGH op:UNBIND)."""
        got = []
        for build in (self.bound, self.revoked):
            w = self.world(pack, probe=W1B_SEPARATOR)
            build(w)
            got.append(w.verdict("W1BSEP", device="dev0"))
        return tuple(got)


class TestTheSeparatorSeparatesAgainstTheShippedOp(_W1bBase):
    """A3. THE PLAN'S WHOLE POINT, as a NAMED ROW and never a count."""

    def test_the_separator_REFUSES_once_the_binding_is_revoked_through_op_UNBIND(self):
        with open(PACK, encoding="utf-8") as fh:
            self.assertEqual(self.clause_separator_pair(json.load(fh)),
                             ("ADMIT", "REFUSE:CAP-IS-LAW"))

    def test_THE_RED_WORLD_removing_the_key_makes_the_separator_blind_again(self):
        """R2. A separator that cannot be made blind has demonstrated nothing. The key is
        removed from the LANDED declaration — a perturbation of the shipped pack, not a
        citation of the pre-image — and the same clause must return ADMIT/ADMIT."""
        self.assertEqual(self.clause_separator_pair(_pack_with(record_stream=None)),
                         ("ADMIT", "ADMIT"))

    def test_R5_a_plant_on_a_DIFFERENT_op_does_NOT_red_this_row(self):
        """A row reddened by a plant elsewhere is measuring its fixture. THE PLANT TARGET IS
        CHOSEN AGAINST THE FIXTURE: this row's world drives REGISTER-CAPABILITY, BIND-DEVICE
        and UNBIND, so a plant on any of those three would test the fixture. CREATE-ROLE is a
        pure record producer that no part of this world touches."""
        with open(PACK, encoding="utf-8") as fh:
            p = json.load(fh)
        for s in p["steps"]:
            for r in s["records"]:
                if r.get("action") == "CREATE-OP" and r["payload"].get("name") == "CREATE-ROLE":
                    r["payload"]["definition"]["record_stream"] = "EP30-ELSEWHERE"
        self.assertEqual(self.clause_separator_pair(p), ("ADMIT", "REFUSE:CAP-IS-LAW"))


class TestTheDoorIsNeverErasedAtTheShippedOp(_W1bBase):
    """A4, :918 constraint 2. BOTH facts in ONE record, or the shape could not carry the
    capability at all — which would have been a STOP AND RAISE and never an overwrite."""

    def clause_both_facts(self, rec, indexed_under):
        """THE CLAUSE, called by the green row and by its red world alike. `rec` is the record
        under test and `indexed_under` is the set the store's own index returns for the
        declared stream — passed in rather than re-read, so the same assertion can be run
        against a record the engine will not produce."""
        # fact 1 — WHICH OPERATION wrote it, by name, from the record itself
        self.assertEqual(rec["action"], "UNBIND",
                         "the record does not say which operation wrote it: the door was "
                         "erased, and a record holding an act nobody performed is the one lie "
                         "class this estate refuses")
        # fact 2 — the stream it landed in, from the STORE'S OWN INDEX
        self.assertIn(rec, indexed_under,
                      "the store does not index the unbind under the declared stream")
        self.assertEqual(rec.get("record_stream"), W1B_STREAM)

    def test_one_unbind_record_carries_the_door_AND_the_stream(self):
        with open(PACK, encoding="utf-8") as fh:
            w = self.world(json.load(fh))
        self.revoked(w)
        stream = w.store.by_action(W1B_STREAM)
        unbinds = [e for e in stream if e["action"] == "UNBIND"]
        self.assertEqual(len(unbinds), 1, "no unbind record landed in the granting act's stream")
        self.clause_both_facts(unbinds[0], stream)
        # and the door's own stream is EMPTY — the relocation is a move, never a copy
        self.assertEqual(len(w.store.by_action("UNBIND")), 0,
                         "the unbind record is in BOTH streams: a copy, not a relocation")

    def test_THE_RED_WORLD_a_record_whose_stream_key_ATE_its_door(self):
        """The W4e class built on purpose: a record that landed in the right stream while no
        longer saying who wrote it. THE ENGINE WILL NOT PRODUCE THIS — `action` is set from the
        op's own registered name and `record_stream` is a second field beside it, which is
        exactly constraint 2 — so the world is reached by FORGING the record and running THE
        SAME CLAUSE against it. A clause that cannot red on a door-erased record is not
        checking that the door survived; it is describing what the engine happens to do."""
        with open(PACK, encoding="utf-8") as fh:
            w = self.world(json.load(fh))
        self.revoked(w)
        stream = w.store.by_action(W1B_STREAM)
        real = [e for e in stream if e["action"] == "UNBIND"][0]
        self.clause_both_facts(real, stream)                      # the control: it passes here
        forged = dict(real, action=W1B_STREAM)                    # the door eaten by the stream
        with self.assertRaises(AssertionError):
            self.clause_both_facts(forged, list(stream) + [forged])


class TestTheFoundingMovedAtW1b(_W1bBase):
    """R1. THE FOUNDING BYTE-UNCHANGED IS THE FAILING OUTCOME: a law pass that moves nothing
    has not landed. Both facts are era-pinned so this row's subject is W1b's pass and never
    whatever the founding says later — the open range that cost EP-30-R1 a whole unit."""

    W1B_BEFORE_VERSION = "1.24.0"
    W1B_AFTER_VERSION = "1.25.0"

    #: W1b'S CLOSE COMMIT — the AFTER end of this row's range, which W1b itself could not pin
    #: because a landing pass cannot name a close commit that does not yet exist (§A57).
    #:
    #: [DERIVED INDEPENDENTLY OF THE PROPERTY THIS ROW ASSERTS (board `:1057`). A pin chosen as
    #:  "the last commit where the founding still said 1.25.0" would select BY the assertion and
    #:  leave the row unable to fail. THIS pin is the tree AS EP-30-W2's pass OPENED IT, captured
    #:  by that pass before it wrote one byte, and cross-checked by a route that never reads the
    #:  version field: the pack blob at this commit hashes to f29d9cbbb8a4acf7…, which is the
    #:  founding digest the mentor's own ACCEPTANCE of EP-30-W1b names at board `:1081`.]
    W1B_CLOSE_COMMIT = "0f8c16c6ac04340e7716f6aba0f4b37d3342d663"

    def test_the_pack_version_moved_one_MINOR(self):
        """[DOCUMENTED FLIP — EP-30-W2, 2026-08-16, a §A57 RANGE CLOSURE and not a meaning
        change. CAUSE: EP-30-W2 moved the founding 1.25.0 -> 1.26.0, so this row's open end
        made it a claim about whatever the founding says LATER instead of about W1b's own
        pass. ASSERTED: the founding says 1.25.0. SUPERSEDED: nothing — the assertion, its
        literal and its subject are unchanged; only the SOURCE closes, from the live tree to
        this row's own era. REMAINS TRUE and STILL ASSERTED, unchanged in substance: W1b moved
        the pack version by exactly one MINOR, 1.24.0 -> 1.25.0. GIVEN UP: nothing. The
        class docstring above already CLAIMED both facts were era-pinned; this row was reading
        the live tree, and the claim is now true.]"""
        self.assertEqual(era_pin.pack_at(self.W1B_CLOSE_COMMIT)["founding_version"],
                         self.W1B_AFTER_VERSION)

    def test_the_ERA_PIN_ABOVE_CAN_STILL_FAIL(self):
        """A REPAIRED ROW MUST BE PROVEN STILL ABLE TO FAIL, or the repair has converted a
        falsifiable claim into a constant (board `:1057`). The SAME assertion is driven against
        an era where the founding said something else — W1b's own BEFORE value is the honest
        control, because it is the one version this row must distinguish 1.25.0 from."""
        self.assertNotEqual(self.W1B_BEFORE_VERSION, self.W1B_AFTER_VERSION)
        with self.assertRaises(AssertionError):
            self.assertEqual(era_pin.pack_at(self.W1B_CLOSE_COMMIT)["founding_version"],
                             self.W1B_BEFORE_VERSION)

    def test_op_UNBIND_declares_the_stream_and_names_the_GRANTING_act(self):
        d = dict(shipped_ops())["UNBIND"]
        self.assertEqual(d.get("record_stream"), W1B_STREAM)
        self.assertEqual([c["action"] for c in d["checks"]], [W1B_STREAM],
                         "the stream this op writes into is no longer the one its own check "
                         "reads — the key and the check have come apart")

    def test_THE_CENSUS_no_check_in_the_pack_locates_over_the_action_this_pass_moved(self):
        """WHY THIS PASS IS INERT TO EVERY EXISTING CHECK, as a measurement and not a belief.

        A `record_stream` on op X moves X's records out of the stream named X, so EVERY check
        that locates over `action: X` stops finding them. DRIVEN, not reasoned: a key planted
        on BIND-DEVICE makes op:UNBIND's own `require_prior` refuse a lawful unbind.

        This pass is safe because NOTHING IN THE PACK LOCATES OVER `UNBIND` — and that is a
        property of WHICH OP WAS CHOSEN, not of the capability. This row states the population
        so the next hand to declare a key meets the list rather than the surprise."""
        located_over = {}
        for name, d in shipped_ops():
            for c in (d.get("checks") or []):
                if c.get("check") in ("require_prior", "prior_value") and c.get("action"):
                    located_over.setdefault(c["action"], set()).add(name)
        self.assertEqual(sorted(located_over.get("UNBIND", ())), [],
                         "a check now locates over UNBIND, so relocating UNBIND's records "
                         "changes that check's meaning and this pass is no longer inert")
        # the control: the map is not empty, so an empty answer above is a fact and not a
        # broken filter reporting nothing (an empty search says only that the search found
        # nothing — prefer a claim about reachability)
        # [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION. CAUSE:
        #  POPULATION, in the CONTROL and not in the claim. SUBJECT-ERA: LIVE.
        #  THE PRIMARY ASSERTION ABOVE NEVER MOVED — nothing locates over UNBIND, then or now,
        #  driven at this hand. What moved is this control's known-reader list: EP-30-C3's
        #  FILE-CUSTODY-TRANSFER carries `require_prior` over BIND-DEVICE, so the same filter
        #  now finds FOUR. RE-POPULATED, NOT WEAKENED: a weakened control asserts less; this
        #  one asserts the same thing about a moved world and still reds if the filter stops
        #  finding a reader it is known to have.]
        self.assertEqual(sorted(located_over["BIND-DEVICE"]),
                         ["DEVICE-INTAKE-COVER", "DEVICE-IO-WINDOW-WRITE",
                          "FILE-CUSTODY-TRANSFER", "UNBIND"],
                         "the census filter no longer finds the readers it is known to have")

    def test_R3_the_planted_INVERSION_discriminates_backwards_and_is_NOT_shipped(self):
        """R3, carried unchanged from W1 per :918 constraint 3. Branch B's naive form —
        `require_prior` over the REVOKING action — is the shape EP-30-E1 found discriminating
        IN THE WRONG DIRECTION: a fail-open licence wearing a fail-closed shape. This pass must
        not have shipped it, and the row proves the plant is REACHABLE rather than only
        forbidden in prose.

        AND THE PLANT'S BEHAVIOUR MOVED WITH THIS PASS, which is worth the sentence: before
        the key, the inversion gave REFUSE-while-held / ADMIT-once-revoked. After it, records
        no longer sit under `action: UNBIND`, so the naive form finds nothing and refuses in
        BOTH worlds. The mistake became fail-CLOSED, which is the safe direction, and it is a
        consequence of this pass rather than a claim about the author's intent."""
        inversion = dict(W1B_SEPARATOR,
                         checks=[{"check": "require_prior", "action": "UNBIND",
                                  "field": "device", "param": "device", "cite": "CAP-IS-LAW"}])
        with open(PACK, encoding="utf-8") as fh:
            p = json.load(fh)
        got = []
        for build in (self.bound, self.revoked):
            w = self.world(p, probe=inversion, probe_name="W1BINV")
            build(w)
            got.append(w.verdict("W1BINV", device="dev0"))
        self.assertEqual(tuple(got), ("REFUSE:CAP-IS-LAW", "REFUSE:CAP-IS-LAW"))
        self.assertNotEqual(tuple(got), ("REFUSE:CAP-IS-LAW", "ADMIT"),
                            "the planted inversion admits once revoked — the fail-open licence "
                            "E1 found, and it must never be what a shipped op does")
        # and the shipped op does NOT carry that shape
        self.assertEqual(
            [c["action"] for c in dict(shipped_ops())["UNBIND"]["checks"]], [W1B_STREAM],
            "op:UNBIND carries a check over the revoking action — the inversion shipped")


# =============================================================================================
# EP-30-W2 — ENFORCEMENT. The two CONSUMING operations gain the check, and this is the first
# movement of EP-30 that REFUSES SOMETHING ADMITTED THE DAY BEFORE.
#
# WHAT THESE ROWS ASSERT, in one sentence: once a binding has been revoked through op:UNBIND,
# DEVICE-IO-WINDOW-WRITE and DEVICE-INTAKE-COVER REFUSE citing DEV-LAW-BIND, and a fresh bind
# admits them again.
#
# THE INVERSION THAT MAKES THIS BLOCK DIFFERENT FROM THE TWO ABOVE IT. W1a and W1b were both
# licensed by "NOTHING NEW IS REFUSED" — W1a's default-preservation row over all 76 ops, W1b's
# verdict-for-verdict A5. THIS BLOCK'S LICENCE IS THE OPPOSITE and its acceptance has to be
# too: `TheRevocationBites` asserts that something previously ADMITTED now REFUSES, BY NAME,
# and `TheRefusalIsBounded` bounds it to exactly those two cases. A W2 that refuses nothing has
# not landed; a W2 that refuses anything beyond its two named cases has overshot.
#
# WHY THE MECHANISM WORKS, stated once so no row has to re-derive it. `prior_value` locates
# through `store.by_action`, which indexes by STREAM. W1b put op:UNBIND's records into
# BIND-DEVICE's stream while leaving `action: UNBIND` on them, so the LATEST record in that
# stream for a device is the unbind once one has landed. A bind record carries `driver`
# (payload_from device, driver); an unbind record does not (payload_from device). So the row
# `prior_value(BIND-DEVICE, device, driver, established)` reads the latest declaration and
# finds no driver — and refuses. LATEST-SEQ-WINS IS ALSO WHY REVOCATION IS NOT PERMANENT: a
# re-bind is a newer declaration and the licence computes again.
#
# WHAT THESE ROWS DO NOT ASSERT, stated rather than left as an absence. Nothing here claims the
# custody rows above them became redundant. `require_prior` still fires FIRST for a device NO
# record ever bound, with its own message; the new row fires for a device whose custody ENDED.
# The layering is deliberate and the two refusals are not interchangeable — but nothing in this
# block measures the older row, and a pass that deletes it would not be reddened here.
# =============================================================================================

W2_DEV, W2_DRV = "dev-w2", "drv-w2"
W2_WINDOW, W2_INTAKE = "device-io@w2", "device-intake@w2"

#: THE RELIANT CONSUMERS, named here and in `TheContainmentIsAsserted`'s docstring, so the
#: next hand that weakens op:UNBIND's own check meets the list of what it just unhooked.
#:
#: [RE-POPULATED — EP-30-C3R, 2026-08-21. THREE BECAME FOUR: EP-30-C3's FILE-CUSTODY-TRANSFER
#:  declares `require_prior` over BIND-DEVICE, so it now leans on the containment this list
#:  exists to guard. THE LIST DID ITS JOB — the row over it went red on the day the fourth
#:  arrived, which is precisely what its author built it to do instead of letting a docstring
#:  rot. RE-POPULATION IS NOT WEAKENING: this set still names an exact membership and still
#:  reds on a fifth. THAT A FOURTH OPERATION JOINED THIS RELIANCE IS A FINDING AND IS RAISED,
#:  NOT ABSORBED — see EP-30-C3R's close.]
W2_RELIANT = ("DEVICE-INTAKE-COVER", "DEVICE-IO-WINDOW-WRITE", "FILE-CUSTODY-TRANSFER",
              "UNBIND")

#: The two operations this pass gives the check to. A NAMED SET, never a count (A3).
W2_CONSUMERS = ("DEVICE-INTAKE-COVER", "DEVICE-IO-WINDOW-WRITE")

#: The row this pass ships, written once. The rows below compare the LANDED declaration
#: against this rather than against a paraphrase of it.
W2_CUSTODY_ROW = {"check": "prior_value", "action": "BIND-DEVICE", "field": "device",
                  "param": "device", "value_field": "driver", "require": "established",
                  "cite": "DEV-LAW-BIND"}

#: THE ONE SOURCE THESE ROWS READ, so a red world can hand a SHIPPING row a planted founding
#: instead of a paraphrase of it (§A42). `None` means the shipped pack on disk.
_W2_PACK = None


def w2_pack():
    if _W2_PACK is not None:
        return copy.deepcopy(_W2_PACK)
    with open(PACK, encoding="utf-8") as fh:
        return json.load(fh)


def _w2_ops(pack):
    """Every op definition in a pack, PARSED FROM THE STRUCTURE and never grepped (§A51)."""
    return dict(_walk_ops(pack))


def _walk_ops(o, found=None):
    found = [] if found is None else found
    if isinstance(o, dict):
        if o.get("kind") == "op_definition" and "name" in o:
            found.append((o["name"], o["definition"]))
        for v in o.values():
            _walk_ops(v, found)
    elif isinstance(o, list):
        for v in o:
            _walk_ops(v, found)
    return found


def _w2_seed(pack, action, opname):
    """A declaration payload taken from the FOUNDING'S OWN seeded record, filtered to the
    operation's declared params. NOTHING IS TRANSCRIBED: these declarations carry calibration
    provenance measured on a named guest at a named boot, and a hand-typed copy would rot the
    moment the founding's own values moved."""
    allowed = set(_w2_ops(pack)[opname]["params"])
    for s in pack["steps"]:
        for r in s["records"]:
            if r.get("action") == action:
                return {k: copy.deepcopy(v) for k, v in r["payload"].items() if k in allowed}
    raise AssertionError("the founding holds no %s record to found this world on" % action)


def _w2_without_the_custody_rows(pack):
    """THE PRE-PASS PACK, built by REMOVING exactly what this pass added — a perturbation of
    the shipped pack rather than a citation of a pre-image, so the comparison cannot drift onto
    some other difference between two eras."""
    for name, d in _w2_ops(pack).items():
        if name in W2_CONSUMERS:
            d["checks"] = [c for c in d["checks"]
                           if not (c.get("check") == "prior_value"
                                   and c.get("action") == "BIND-DEVICE")]
    return pack


class _W2Base(_W1bBase):
    """The clauses, written once and called by the green rows AND their red worlds alike, so a
    red world proves THAT assertion can fail rather than a paraphrase of it (§A42)."""

    def w2_world(self, pack=None):
        return self.world(w2_pack() if pack is None else pack)

    def run_up(self, w, pack):
        """Custody granted and both declarations made. EVERY RUN-UP ACT IS ASSERTED ADMITTED,
        or "refuses afterwards" is a sentence about a world where nothing ever worked."""
        win = dict(_w2_seed(pack, "DECLARE-IO-WINDOW", "DECLARE-IO-WINDOW"), window=W2_WINDOW)
        ink = dict(_w2_seed(pack, "DECLARE-INTAKE", "DECLARE-INTAKE"),
                   intake=W2_INTAKE, window=W2_WINDOW)
        for op, params in (("REGISTER-CAPABILITY",
                            dict(driver=W2_DRV, device_class="block",
                                 capabilities=["device:%s" % W2_DEV])),
                           ("BIND-DEVICE", dict(device=W2_DEV, driver=W2_DRV)),
                           ("DECLARE-IO-WINDOW", win),
                           ("DECLARE-INTAKE", ink)):
            self.assertEqual(w.verdict(op, **params), "ADMIT",
                             "the run-up act %s was refused, so nothing below is a statement "
                             "about custody" % op)

    @staticmethod
    def io_write(w):
        return w.verdict("DEVICE-IO-WINDOW-WRITE", device=W2_DEV, window=W2_WINDOW, bytes=4096)

    @staticmethod
    def intake_cover(w):
        return w.verdict("DEVICE-INTAKE-COVER", intake=W2_INTAKE, device=W2_DEV,
                         window=W2_WINDOW, arrival_count=3, byte_total=12288)

    def clause_before_and_after(self, call, pack=None):
        """A4's SUBJECT, and it is a PAIR: (verdict while custody holds, verdict once it has
        been revoked) for ONE named operation IN ONE WORLD. One arm alone is not evidence — an
        ADMIT that could be explained by the unbind never landing says nothing about
        revocation, and a REFUSE that was refusing all along says less."""
        pack = w2_pack() if pack is None else pack
        w = self.world(pack)
        self.run_up(w, pack)
        before = call(w)
        self.assertEqual(w.verdict("UNBIND", device=W2_DEV), "ADMIT",
                         "the unbind itself was refused, so custody never ended")
        return before, call(w)

    def clause_custody_view_emptied(self, w):
        from subsystems.devices import DevicesView
        self.assertNotIn(W2_DEV, DevicesView(w.store).bindings(),
                         "the unbind was ADMITTED and the binding view still holds the device, "
                         "so custody did not end and the rows here measure nothing")


class TheRevocationBites(_W2Base):
    """A4. THE ROW THIS WHOLE EP EXISTS FOR. The subject is the GATE'S RETURNED VERDICT for a
    named call after a named unbind — never a version number, never a count of operations, and
    never the presence of a check declaration (the LABEL-not-a-WORLD failure `:823` retired).

    THESE TWO ROWS ARE THE EXPIRY OF `tests/test_ep29.py`'s EP-30-P1 PINS, which asserted
    ADMIT here and named EP-30-W2 in their own docstrings as the movement that must red them.
    Those rows are flipped in this pass's own fence, not deleted."""

    def test_A4_the_IO_WINDOW_WRITE_REFUSES_once_custody_is_revoked(self):
        self.assertEqual(self.clause_before_and_after(self.io_write),
                         ("ADMIT", "REFUSE:DEV-LAW-BIND"))

    def test_A4_the_INTAKE_COVER_REFUSES_once_custody_is_revoked(self):
        """AND THIS ONE CLOSES A CONTRADICTION IN THE LAW'S OWN WORDS: every intake declaration
        under DEV-LAW-INTAKE names `unbind` as a CLOSER, and until this pass the closer was
        declared and not enforced."""
        self.assertEqual(self.clause_before_and_after(self.intake_cover),
                         ("ADMIT", "REFUSE:DEV-LAW-BIND"))

    def test_A4_the_unbind_that_produced_those_refusals_DID_end_custody(self):
        """THE NON-VACUITY ARM. A refusal after a call that changed nothing is not revocation
        biting; it is a world that was broken to begin with."""
        pack = w2_pack()
        w = self.world(pack)
        self.run_up(w, pack)
        self.assertEqual((self.io_write(w), self.intake_cover(w)), ("ADMIT", "ADMIT"))
        self.assertEqual(w.verdict("UNBIND", device=W2_DEV), "ADMIT")
        self.clause_custody_view_emptied(w)

    def test_R1_THE_RED_WORLD_removing_the_key_from_UNBIND_admits_both_calls_again(self):
        """R1. A revocation that cannot be made blind again has not been shown to depend on the
        mechanism this EP built. With op:UNBIND's records back under their own door, the unbind
        no longer sits in the stream the custody row reads, the latest record for the device is
        the BIND again, and BOTH consuming calls must be ADMITTED."""
        blind = _pack_with(record_stream=None)
        self.assertEqual(self.clause_before_and_after(self.io_write, blind), ("ADMIT", "ADMIT"))
        self.assertEqual(self.clause_before_and_after(self.intake_cover, blind),
                         ("ADMIT", "ADMIT"))
        # and the control, in the same breath: the SHIPPED pack still refuses, so the ADMITs
        # above are the removed key and not a broken fixture
        self.assertEqual(self.clause_before_and_after(self.io_write),
                         ("ADMIT", "REFUSE:DEV-LAW-BIND"))

    def test_R2_NEAR_MISS_a_custody_row_reading_a_field_no_record_carries_REFUSES(self):
        """R2, §A64, and it is the sharpest row here. The check declared with the RIGHT action
        and a value_field the records DO NOT CARRY must refuse when it reads, not admit.

        A CHECK THAT READS NOTHING AND PASSES IS A FAIL-OPEN WEARING A DEFAULT'S CLOTHES, and
        this is the pass where that would be catastrophic: it would ship two operations whose
        custody row looks like law on the page and answers nothing at the gate. The engine's
        middle refusal is what stands here — a declaration SILENT about a field has not said
        "no value", it has said nothing, and nothing filled by a default is the trap.

        THE ROW IS DRIVEN WITH CUSTODY INTACT, deliberately: post-unbind everything refuses
        anyway, so a red world driven there could not tell a working check from a broken one."""
        pack = w2_pack()
        for name, d in _w2_ops(pack).items():
            if name in W2_CONSUMERS:
                for c in d["checks"]:
                    if c.get("check") == "prior_value" and c.get("action") == "BIND-DEVICE":
                        c["value_field"] = "no-record-carries-this-field"
        w = self.world(pack)
        self.run_up(w, pack)
        self.assertEqual((self.io_write(w), self.intake_cover(w)),
                         ("REFUSE:DEV-LAW-BIND", "REFUSE:DEV-LAW-BIND"),
                         "a custody row reading a field no record carries ADMITTED with "
                         "custody intact — it reads nothing and passes")
        # the control: the SAME two calls with the SHIPPED value_field are ADMITTED in the same
        # world shape, so the refusals above are the broken field and not the fixture
        clean = w2_pack()
        wc = self.world(clean)
        self.run_up(wc, clean)
        self.assertEqual((self.io_write(wc), self.intake_cover(wc)), ("ADMIT", "ADMIT"))

    def test_R6_THE_RE_BIND_ADMITS_revocation_is_not_a_one_way_door(self):
        """R6, and it is a WORLD rather than a near-miss. Bind, unbind, BIND AGAIN, then call.
        LATEST-SEQ-WINS MEANS THE NEWEST DECLARATION GOVERNS, so a fresh grant restores what a
        revocation took. A revocation that could not be undone by a re-bind would be a one-way
        door nobody licensed, and EP-30-W2's S8 makes that a STOP rather than a finding."""
        pack = w2_pack()
        w = self.world(pack)
        self.run_up(w, pack)
        self.assertEqual(w.verdict("UNBIND", device=W2_DEV), "ADMIT")
        self.assertEqual((self.io_write(w), self.intake_cover(w)),
                         ("REFUSE:DEV-LAW-BIND", "REFUSE:DEV-LAW-BIND"),
                         "the middle arm does not refuse, so a later ADMIT proves nothing")
        self.assertEqual(w.verdict("BIND-DEVICE", device=W2_DEV, driver=W2_DRV), "ADMIT")
        self.assertEqual((self.io_write(w), self.intake_cover(w)), ("ADMIT", "ADMIT"),
                         "a re-bind did not restore admission — revocation has become "
                         "PERMANENT, which is a one-way door nobody licensed")


class TheCheckIsDeclaredOnExactlyTheTwoConsumers(_W2Base):
    """A3. A NAMED SET, parsed from the pack's own declarations and never grepped, never
    counted. The population is the THREE operations that lean on a device binding."""

    def test_A3_exactly_the_two_consuming_operations_carry_the_custody_row(self):
        carriers = sorted(name for name, d in _w2_ops(w2_pack()).items()
                          for c in (d.get("checks") or [])
                          if c.get("check") == "prior_value" and c.get("action") == "BIND-DEVICE")
        self.assertEqual(carriers, sorted(W2_CONSUMERS),
                         "the set of operations carrying a custody row is not the set this "
                         "pass declared it on")

    def test_A3_each_consumer_gained_EXACTLY_ONE_row_and_it_is_the_shipped_shape(self):
        ops = _w2_ops(w2_pack())
        for name in W2_CONSUMERS:
            rows = [c for c in ops[name]["checks"]
                    if c.get("check") == "prior_value" and c.get("action") == "BIND-DEVICE"]
            self.assertEqual(len(rows), 1, "%s carries %d custody rows" % (name, len(rows)))
            self.assertEqual({k: rows[0].get(k) for k in W2_CUSTODY_ROW}, W2_CUSTODY_ROW,
                             "%s's custody row is not the shape this pass ships" % name)

    def test_A3_op_UNBIND_GAINS_NOTHING(self):
        """op:UNBIND's declaration is W1b's landing and this pass does not touch it."""
        d = _w2_ops(w2_pack())["UNBIND"]
        self.assertEqual([c["check"] for c in d["checks"]], ["require_prior"])
        self.assertEqual([c["action"] for c in d["checks"]], ["BIND-DEVICE"])
        self.assertEqual(d.get("record_stream"), "BIND-DEVICE")


class TheRefusalIsBounded(_W2Base):
    """A5. NOTHING OUTSIDE THE REVOKED CASE BEGINS TO REFUSE.

    POPULATION: the campaign device sequence, named step by step in `SEQUENCE` below — the acts
    a device world performs from registration through revocation and back to a fresh bind.
    BASIS: the gate's returned verdict, taken VERDICT BY VERDICT and never as a count of
    refusals. A count would let one new refusal hide behind one removed."""

    #: (label, op, params-builder). The params are built per world because two of them read the
    #: founding's own seeded declarations.
    SEQUENCE = ("REGISTER-CAPABILITY", "BIND-DEVICE", "DECLARE-IO-WINDOW", "DECLARE-INTAKE",
                "DEVICE-IO-WINDOW-WRITE pre-unbind", "DEVICE-INTAKE-COVER pre-unbind",
                "UNBIND", "DEVICE-IO-WINDOW-WRITE POST-unbind",
                "DEVICE-INTAKE-COVER POST-unbind", "UNBIND again", "BIND-DEVICE again",
                "DEVICE-IO-WINDOW-WRITE after re-bind", "DEVICE-INTAKE-COVER after re-bind")

    #: The two steps this pass is LICENSED to move, by label. Any other movement is S6.
    LICENSED = ("DEVICE-IO-WINDOW-WRITE POST-unbind", "DEVICE-INTAKE-COVER POST-unbind")

    def verdicts(self, pack):
        w = self.world(pack)
        win = dict(_w2_seed(pack, "DECLARE-IO-WINDOW", "DECLARE-IO-WINDOW"), window=W2_WINDOW)
        ink = dict(_w2_seed(pack, "DECLARE-INTAKE", "DECLARE-INTAKE"),
                   intake=W2_INTAKE, window=W2_WINDOW)
        io = dict(device=W2_DEV, window=W2_WINDOW, bytes=4096)
        cov = dict(intake=W2_INTAKE, device=W2_DEV, window=W2_WINDOW,
                   arrival_count=3, byte_total=12288)
        acts = (("REGISTER-CAPABILITY", dict(driver=W2_DRV, device_class="block",
                                             capabilities=["device:%s" % W2_DEV])),
                ("BIND-DEVICE", dict(device=W2_DEV, driver=W2_DRV)),
                ("DECLARE-IO-WINDOW", win), ("DECLARE-INTAKE", ink),
                ("DEVICE-IO-WINDOW-WRITE", io), ("DEVICE-INTAKE-COVER", cov),
                ("UNBIND", dict(device=W2_DEV)),
                ("DEVICE-IO-WINDOW-WRITE", io), ("DEVICE-INTAKE-COVER", cov),
                ("UNBIND", dict(device=W2_DEV)),
                ("BIND-DEVICE", dict(device=W2_DEV, driver=W2_DRV)),
                ("DEVICE-IO-WINDOW-WRITE", io), ("DEVICE-INTAKE-COVER", cov))
        return [w.verdict(op, **params) for op, params in acts]

    def test_A5_the_ONLY_verdicts_that_moved_are_the_two_A4_names(self):
        before = self.verdicts(_w2_without_the_custody_rows(w2_pack()))
        after = self.verdicts(w2_pack())
        self.assertEqual(len(before), len(self.SEQUENCE))
        moved = [label for label, x, y in zip(self.SEQUENCE, before, after) if x != y]
        self.assertEqual(moved, list(self.LICENSED),
                         "a verdict moved outside this pass's licence: before=%r after=%r"
                         % (before, after))

    def test_A5_the_PRE_PASS_pack_admitted_every_step_so_the_comparison_is_not_vacuous(self):
        """THE CONTROL. If the pre-pass arm refused somewhere, "only two moved" could be two
        refusals cancelling out rather than a bounded change."""
        self.assertEqual(set(self.verdicts(_w2_without_the_custody_rows(w2_pack()))), {"ADMIT"})

    def test_A5_the_two_licensed_steps_are_the_ONLY_refusals_after_the_pass(self):
        after = self.verdicts(w2_pack())
        refused = [label for label, v in zip(self.SEQUENCE, after) if v != "ADMIT"]
        self.assertEqual(refused, list(self.LICENSED))
        self.assertEqual([v for label, v in zip(self.SEQUENCE, after) if label in self.LICENSED],
                         ["REFUSE:DEV-LAW-BIND", "REFUSE:DEV-LAW-BIND"])


class TheContainmentIsAsserted(_W2Base):
    """A6, ruled at board :1010, TWO ARMS, and the subject of each is a VERDICT.

    WHY IT LANDS HERE AND NOT AT W1b. W1b made BIND-DEVICE's stream HETEROGENEOUS — it now
    holds records written by two different doors. Every reader of that stream depends on an
    invariant no document stated and no row checked: THAT EVERY DEVICE WITH AN UNBIND RECORD
    ALSO HAS A BIND RECORD. Today that is enforced by A DIFFERENT OPERATION'S CHECK — op:UNBIND
    refuses an unbind of a never-bound device — and not by anything about the stream's own
    contents. The safety moved from the data to a neighbour. W1b created the reliance; THIS
    pass is where readers start leaning on it, and the leaning point is the assertion point.

    THE RELIANT CONSUMERS, BY OPERATION NAME, so the next hand that weakens or re-streams
    op:UNBIND's own `require_prior` meets the list of what it just unhooked:

        DEVICE-INTAKE-COVER · DEVICE-IO-WINDOW-WRITE · FILE-CUSTODY-TRANSFER · UNBIND

    Remove that check and all four locate over a stream where an unbind alone can satisfy a
    question about a bind, with nothing red to say so.

    [FOUR SINCE EP-30-C3R, 2026-08-21. FILE-CUSTODY-TRANSFER arrived with EP-30-C3 carrying
    `require_prior` over BIND-DEVICE. IT IS THE FIRST RELIANT CONSUMER FROM OUTSIDE THE DEVICE
    PLANE — the other three are device operations that grew up beside the binding they read;
    this one is a FILE custody act reaching across into the device stream for its `device`
    parameter. The reliance is the same reliance and the distance is not, and this class's own
    argument — that the safety moved from the data to a neighbour — now spans two planes.]"""

    def clause_unbind_with_no_prior_bind(self, pack):
        """ARM 1, THE GUARD THAT MAKES IT TRUE. Driven, because the containment holds by
        op:UNBIND's own check and by nothing about the stream."""
        return self.world(pack).verdict("UNBIND", device="never-bound-w2")

    def test_A6_DRIVEN_an_unbind_with_no_prior_bind_is_REFUSED_at_the_door(self):
        self.assertEqual(self.clause_unbind_with_no_prior_bind(w2_pack()), "REFUSE:DEV-LAW-BIND")

    def test_R4_THE_RED_WORLD_removing_op_UNBINDs_own_check_breaks_the_containment(self):
        """R4. Remove op:UNBIND's `require_prior` in a scratch pack and the containment must
        FAIL — an unbind of a never-bound device is admitted, and a record claiming a binding
        ended that never began lands in the granting act's own stream. THAT IS THE EXACT FUTURE
        HAND board :1010 EXISTS TO WARN, and the row must fire for it."""
        self.assertEqual(self.clause_unbind_with_no_prior_bind(_pack_with(checks=[])), "ADMIT")
        # the control, in the same breath: the shipped pack still refuses
        self.assertEqual(self.clause_unbind_with_no_prior_bind(w2_pack()), "REFUSE:DEV-LAW-BIND")

    def test_A6_HELD_every_unbind_record_is_preceded_in_seq_by_a_bind_for_the_same_object(self):
        """ARM 2, THAT IT HELD. POPULATION: the campaign device sequence, driven here — two
        unbinds and two binds over one device. BASIS: RECORD ORDER, read from the store."""
        pack = w2_pack()
        w = self.world(pack)
        self.run_up(w, pack)
        for op, params in (("UNBIND", dict(device=W2_DEV)),
                           ("BIND-DEVICE", dict(device=W2_DEV, driver=W2_DRV)),
                           ("UNBIND", dict(device=W2_DEV))):
            self.assertEqual(w.verdict(op, **params), "ADMIT")
        records = list(w.store.all())
        unbinds = [e for e in records if e.get("action") == "UNBIND"]
        binds = [e for e in records if e.get("action") == "BIND-DEVICE"]
        self.assertEqual((len(unbinds), len(binds)), (2, 2),
                         "the sequence did not produce the population this row is about")
        for u in unbinds:
            dev = (u.get("payload") or {}).get("device")
            earlier = [b for b in binds
                       if (b.get("payload") or {}).get("device") == dev and b["seq"] < u["seq"]]
            self.assertTrue(earlier,
                            "an UNBIND at seq %d for %r is preceded by no BIND-DEVICE for the "
                            "same object — the containment every reader of this stream leans "
                            "on does not hold" % (u["seq"], dev))

    def test_A6_the_THREE_RELIANT_CONSUMERS_are_still_exactly_these_three(self):
        """THE LIST KEPT LIVE RATHER THAN ONLY IN PROSE. A docstring naming three operations
        rots the moment a fourth starts reading the stream; this row reds instead.

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION. CAUSE:
        POPULATION. SUBJECT-ERA: LIVE — the question is who reads that stream NOW.
        CAUSE, DRIVEN: EP-30-C3's FILE-CUSTODY-TRANSFER declares `require_prior` over
        BIND-DEVICE. A FOURTH OPERATION STARTED READING THE STREAM AND THIS ROW SAID SO ON THE
        DAY IT HAPPENED — the sentence above is not a warning that aged badly, it is a
        prediction that came true and fired.
        ASSERTED: three. SUPERSEDED: four, via `W2_RELIANT`.
        RE-DERIVED AND DELIBERATELY NOT ERA-PINNED: era-pinning the reliant set would freeze it
        at W2's world and this row would never report a fifth. That is the one outcome its
        author ruled out in writing.
        REMAINS TRUE, unchanged in kind: the set of operations locating over BIND-DEVICE's
        stream is EXACTLY the named membership, and a fifth reds it.
        GIVEN UP: nothing.
        THE NAME IS NOW STALE AND IS KEPT ON PURPOSE — renaming moves the row's id, and an id
        that moves is indistinguishable from a deletion plus an addition (this unit's R2).
        RAISED, NOT TIDIED.]"""
        readers = sorted(name for name, d in _w2_ops(w2_pack()).items()
                         for c in (d.get("checks") or [])
                         if c.get("check") in ("require_prior", "prior_value")
                         and c.get("action") == "BIND-DEVICE")
        self.assertEqual(sorted(set(readers)), sorted(W2_RELIANT),
                         "the set of operations locating over BIND-DEVICE's stream has moved, "
                         "so the containment's reliant list is stale")


class TheFoundingMovedAtW2(_W2Base):
    """A2. THE FOUNDING BYTE-UNCHANGED IS THE FAILING OUTCOME for a law pass. Both facts are
    ERA-PINNED to this pass's own boundaries so this row's subject is W2's move and never
    whatever the founding says later — the open range that cost EP-30-R1 a whole unit."""

    W2_BEFORE_VERSION = "1.25.0"
    W2_AFTER_VERSION = "1.26.0"

    #: [DERIVED INDEPENDENTLY OF THE PROPERTY THIS ROW ASSERTS (board `:1057`), by the same
    #:  route `W1B_CLOSE_COMMIT` above was derived by: THE TREE AS THE NEXT FOUNDING-MOVING
    #:  PASS OPENED IT. EP-30-C1 recorded its content base at 2026-08-20T10:04:44Z before it
    #:  wrote one byte (`planning/evidence/EP-30-C1/BASE-CONTENT-PIN.txt`); this is the last
    #:  autosync commit before that moment, at 10:04:22Z. SELECTED BY A RECORDED MOMENT AND
    #:  NEVER BY THE VERSION FIELD — a pin chosen as "the last commit where the founding
    #:  still said 1.26.0" would select BY the assertion and leave this row unable to fail.
    #:  CROSS-CHECKED BY A ROUTE THAT NEVER READS THAT FIELD: the pack blob here hashes to
    #:  87627b7236856504eb106d3ca99b8d9715ebb4b7b81c382cb7a6489a61090b93, which is the digest
    #:  BOTH EP-30-W2's own close entry AND EP-30-C1's base pin independently name.]
    W2_CLOSE_COMMIT = "81ab5068fa2e7a29f8660fa008550a327eaecfb5"

    def test_A2_the_pack_version_moved_one_MINOR(self):
        """[DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, a §A57 RANGE CLOSURE and not a meaning
        change. CAUSE: RANGE. EP-30-C1 moved the founding 1.26.0 -> 1.27.0, so this row's
        open end made it a claim about whatever the founding says LATER instead of about W2's
        own pass. SUBJECT-ERA: HISTORICAL — the subject is W2's move, which is finished — so
        an era-pin is the lawful repair. ASSERTED: the founding says 1.26.0. SUPERSEDED:
        nothing — the assertion, its literal and its subject are unchanged; only the SOURCE
        closes, from the live tree to this row's own era. REMAINS TRUE and STILL ASSERTED:
        W2 moved the pack version by exactly one MINOR, 1.25.0 -> 1.26.0. GIVEN UP: nothing.
        The class docstring above already CLAIMED both facts were era-pinned; `w2_pack()`
        read the LIVE tree, so the claim was false and is now true.

        THE CAN-STILL-FAIL CONTROL IS FOLDED INTO THIS ROW RATHER THAN GIVEN ITS OWN, and
        the reason is stated because it is a departure from the sibling above: this pass's A1
        pins COLLECTED_BY_LOADER at a hand-computed 2952 and a new method moves it. The
        control is the same one `test_the_ERA_PIN_ABOVE_CAN_STILL_FAIL` runs for W1b — the
        SAME assertion driven against the one version this row must distinguish 1.26.0 from,
        which is W2's own BEFORE."""
        self.assertEqual(era_pin.pack_at(self.W2_CLOSE_COMMIT)["founding_version"],
                         self.W2_AFTER_VERSION)
        # A REPAIRED ROW MUST BE PROVEN STILL ABLE TO FAIL, or the repair has converted a
        # falsifiable claim into a constant (board `:1057`).
        self.assertNotEqual(self.W2_BEFORE_VERSION, self.W2_AFTER_VERSION)
        with self.assertRaises(AssertionError):
            self.assertEqual(era_pin.pack_at(self.W2_CLOSE_COMMIT)["founding_version"],
                             self.W2_BEFORE_VERSION)

    def test_A2_the_genesis_still_LOADS_under_the_amended_law_which_is_why_it_is_MINOR(self):
        """THE DISCRIMINATOR, BUILDER-EXECUTED AND NEVER JUDGED: the genesis records, unchanged,
        still load under the new law -> MINOR. A founding that stopped loading would be MAJOR
        and a STOP TO THE OWNER, never a bump.

        AND THE GROUND IS MEASURED RATHER THAN ASSUMED: no genesis record carries any of the
        four device actions, so no seeded record meets either new row."""
        pack = w2_pack()
        actions = [r.get("action") for s in pack["steps"] for r in s["records"]]
        for a in ("BIND-DEVICE", "UNBIND") + W2_CONSUMERS:
            self.assertEqual(actions.count(a), 0,
                             "the genesis seeds a %s record, so the load test above is a "
                             "statement about that record and not only about the law" % a)
        self.world(pack)                       # boots, or this row raises and the pass is MAJOR


class ThePlantedInversionIsNotShipped(_W2Base):
    """R3, carried unchanged from W1 per board :918 constraint 3, and PLANTED ON THE CONSUMING
    OPERATIONS this pass actually moves rather than on a probe.

    Branch B's naive form — `require_prior` over the REVOKING action — is the shape EP-30-E1
    found discriminating IN THE WRONG DIRECTION: before W1a's key it gave REFUSE-while-held and
    ADMIT-once-revoked, a fail-open licence wearing a fail-closed shape.

    ITS BEHAVIOUR MOVED WITH W1b AND THE MOVE IS REPORTED HERE RATHER THAN ASSUMED AWAY: with
    op:UNBIND's records relocated out of the stream named UNBIND, the naive form now finds
    nothing in EITHER world and refuses in both. The mistake became fail-CLOSED, which is the
    safe direction — but it is STILL WRONG, because it refuses a device whose custody holds,
    and this pass must not have shipped it."""

    def plant(self, pack):
        for name, d in _w2_ops(pack).items():
            if name in W2_CONSUMERS:
                d["checks"] = [{"check": "require_prior", "action": "UNBIND", "field": "device",
                                "param": "device", "cite": "DEV-LAW-BIND"}]
        return pack

    def test_R3_the_planted_inversion_REDS_the_shipped_A4_row_and_removing_it_returns_GREEN(self):
        """PLANT, REQUIRE RED, REMOVE, REQUIRE GREEN — running the SHIPPING row through
        unittest's own machinery, never a paraphrase of it. The clean arm runs FIRST, or a red
        under the plant would be measuring the fixture rather than the plant."""
        meth = "test_A4_the_IO_WINDOW_WRITE_REFUSES_once_custody_is_revoked"
        self.assertTrue(_run_w2_against(None, meth).wasSuccessful(),
                        "%s fails on the LIVE founding, so its red below proves nothing" % meth)
        self.assertFalse(_run_w2_against(self.plant(w2_pack()), meth).wasSuccessful(),
                         "the shipped row stayed GREEN under the planted inversion")
        self.assertTrue(_run_w2_against(None, meth).wasSuccessful(),
                        "%s did not return to GREEN once the plant was removed" % meth)

    def test_R3_the_inversion_refuses_while_custody_HOLDS_which_is_why_it_is_wrong(self):
        """THE PLANT'S OWN BEHAVIOUR, RECORDED rather than described. Both arms driven."""
        pack = self.plant(w2_pack())
        w = self.world(pack)
        self.run_up(w, pack)
        held = (self.io_write(w), self.intake_cover(w))
        self.assertEqual(w.verdict("UNBIND", device=W2_DEV), "ADMIT")
        revoked = (self.io_write(w), self.intake_cover(w))
        self.assertEqual(held, ("REFUSE:DEV-LAW-BIND", "REFUSE:DEV-LAW-BIND"),
                         "the inversion admits while custody holds, so it is not the shape "
                         "board :918 constraint 3 names")
        self.assertNotEqual(revoked, ("ADMIT", "ADMIT"),
                            "the planted inversion ADMITS once revoked — the fail-open licence "
                            "E1 found, and it must never be what a shipped op does")

    def test_R3_the_shipped_consumers_do_NOT_carry_a_check_over_the_revoking_action(self):
        for name, d in _w2_ops(w2_pack()).items():
            self.assertNotIn("UNBIND", [c.get("action") for c in (d.get("checks") or [])],
                             "%s carries a check over the revoking action — the inversion "
                             "shipped" % name)


class APlantOnOneConsumerDoesNotRedTheOthersRow(_W2Base):
    """R5. Each consuming operation is asserted by ITS OWN row, and a row reddened by its
    sibling is measuring its fixture rather than its subject. This is the row that separates
    two independent claims from one entangled one."""

    def plant_on(self, pack, opname):
        """The one plant shape that makes a device act REFUSE on BOTH sides of an unbind: a
        prior scan for an action no record holds. It cannot be confused with this pass's own
        refusal, which appears only after the unbind."""
        _w2_ops(pack)[opname]["checks"].append(
            {"check": "require_prior", "action": "PLANTED-W2-NEVER-RECORDED", "field": "device",
             "param": "device", "cite": "DEV-LAW-BIND", "message": "planted for EP-30-W2 R5"})
        return pack

    def test_R5_a_plant_on_the_INTAKE_COVER_does_not_red_the_IO_WRITE_row(self):
        own = "test_A4_the_IO_WINDOW_WRITE_REFUSES_once_custody_is_revoked"
        other = "test_A4_the_INTAKE_COVER_REFUSES_once_custody_is_revoked"
        planted = self.plant_on(w2_pack(), "DEVICE-INTAKE-COVER")
        self.assertFalse(_run_w2_against(planted, other).wasSuccessful(),
                         "the plant did nothing, so the GREEN below says nothing")
        self.assertTrue(_run_w2_against(planted, own).wasSuccessful(),
                        "the IO-WRITE row REDS under a plant on DEVICE-INTAKE-COVER, an "
                        "operation it does not name")

    def test_R5_a_plant_on_the_IO_WRITE_does_not_red_the_INTAKE_COVER_row(self):
        own = "test_A4_the_INTAKE_COVER_REFUSES_once_custody_is_revoked"
        other = "test_A4_the_IO_WINDOW_WRITE_REFUSES_once_custody_is_revoked"
        planted = self.plant_on(w2_pack(), "DEVICE-IO-WINDOW-WRITE")
        self.assertFalse(_run_w2_against(planted, other).wasSuccessful(),
                         "the plant did nothing, so the GREEN below says nothing")
        self.assertTrue(_run_w2_against(planted, own).wasSuccessful(),
                        "the INTAKE-COVER row REDS under a plant on DEVICE-IO-WINDOW-WRITE, an "
                        "operation it does not name")


def _run_w2_against(pack, meth):
    """Run a REAL shipped row against a PLANTED founding, through unittest's own machinery."""
    global _W2_PACK
    saved = _W2_PACK
    _W2_PACK = pack
    try:
        return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            TheRevocationBites(meth))
    finally:
        _W2_PACK = saved


if __name__ == "__main__":
    unittest.main()
