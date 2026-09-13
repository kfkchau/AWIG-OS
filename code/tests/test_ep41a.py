"""EP-41A acceptance battery — the content-placement family, members 1-2 (design/46 §2).

MEMBER 1 — THE PLACEMENT LAW. Declared content-interiors live outside the row as
    content-addressed blobs (the built `content_params` mint); the row keeps the HASH, never the
    bytes; the routing criterion is the op's OWN declaration and NO SIZE NUMBER is ever read
    (design/46 §2.1: a number is friction pretending to be coverage — the struck size floor stays
    struck).
MEMBER 2 — THE VOCABULARY DOOR. No op definition enters the founding unless EVERY payload field is
    classified STRUCTURAL (declared in `structural_params`, safe inline) or CONTENT (declared in
    `content_params`/`secret_params`, blob-homed by hash). Enforced in `validate_definition_shape`,
    the ONE clause run at all THREE doors (CREATE-OP, AMEND-OP, the founding installer), and
    ENGAGED ONLY WHERE THE LAW IS LIVE (`VOCAB-DOOR-LAW` declared) — the wire-at-birth gate that
    keeps the HELD founding-move (the create + the census sweep, MOVER 4, owner-gated) inert until
    the owner's word. A one-time classification sweep of the DRIVEN op census rides that create.

A1 TestPlacementByDeclaration   — content declared -> blob, row keeps the hash; structural inline.
A2 TestVocabularyDoorRefuses    — unclassified payload field REFUSED at all three doors (RW1);
                                  and the door INERT where the law is not live (the held guard).
A3 TestVocabularyDoorAdmits     — fully-classified definition ADMITTED at all three doors (RW2).
A4 TestNoSizeNumber             — placement + door are declaration-driven; no size threshold (RW3).
A5 TestCensusSweepExhaustive    — the DRIVEN census, swept, passes the door whole; unswept reds (RW4).

Every probe here lands as a regression test (charter; R14). THE MOVER LANDED (COMPLETE-CUSTODY-FAMILY
members 1-2, board :2870 item 4): the production founding-pack.json now DECLARES both laws and carries
the DRIVEN census's structural classifications, so the vocabulary door is LIVE in every production-
founded world and the founding still passes its own door. The held-guard controls below were flipped
from their byte-untouched / neither-law-present holds to their live inverses; the RW4 / before-sweep
controls now reconstruct the pre-sweep red-world by STRIPPING the classification, and drive it red.
"""

import hashlib
import inspect
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                     # noqa: E402
from kernel.compose import build_full_kernel             # noqa: E402
from kernel.errors import OpError                        # noqa: E402
from kernel import opdefs                                # noqa: E402
from kernel.opdefs import (                              # noqa: E402
    validate_definition_shape, structural_field_classification,
    VOCAB_DOOR_LAW, PLACEMENT_LAW, STRUCTURAL_PARAMS)
from founding import install                             # noqa: E402
from founding.install import FoundingIntegrityError      # noqa: E402


# A door object with the gate's `refuse` contract that RECORDS rather than raises — the cheapest
# way to run a definition through the shared door and read the verdict, and the way to run the
# WHOLE driven census through it without founding 80 separate worlds (A5). Mirrors `_FoundingDoor`'s
# contract (anything with `refuse(actor, op, rule, message)`), the door's own stated shape.
class _RecordingDoor:
    def __init__(self):
        self.refusals = []

    def refuse(self, actor, op, rule, message):
        self.refusals.append((actor, op, rule, message))


def _door_verdict(definition, law_live=True):
    """Run one definition through the shared door with the classification law live; return the list
    of refusals (empty == admitted)."""
    door = _RecordingDoor()
    validate_definition_shape(door, "FOUNDING", "SYSTEM", "PROBE", definition,
                              peers={}, classify_law_live=law_live)
    return door.refusals


def _min_recs_with_op(definition, name="PROBE", declare_law=True):
    """A minimal founding record list: the vocabulary-door LAW (self-declared by rule_id) and one
    CREATE-OP op_definition — enough to drive `install._validate` through the FOUNDING door with the
    law live. No tunnels/grants/root-laws, so the other referential clauses have nothing to check."""
    recs = []
    if declare_law:
        recs.append({"actor": "SYSTEM", "action": "CREATE-RULE", "object": "rule:vocab-door",
                     "rule_cited": "BOOT-INT",
                     "payload": {"rule_id": VOCAB_DOOR_LAW, "value": 1}})
    recs.append({"actor": "SYSTEM", "action": "CREATE-OP", "object": f"op:{name}",
                 "rule_cited": "CAP-IS-LAW",
                 "payload": {"kind": "op_definition", "name": name, "definition": definition}})
    return recs


# A definition every OTHER door clause admits, so a test isolates the classification clause: one
# param, a cited law, no checks. `structural_params` present -> fully classified; absent -> the
# lone param is unclassified.
def _classified_def():
    return {"law_cited": "SOP", "object_param": "x", "params": {"x": "required"},
            "checks": [], STRUCTURAL_PARAMS: ["x"]}


def _unclassified_def():
    return {"law_cited": "SOP", "object_param": "x", "params": {"x": "required"}, "checks": []}


class _World(unittest.TestCase):
    """A disposable world founded from the PRODUCTION pack, blob store wired (so content_params ops
    register — member 1). The mover landed, so production now declares the vocabulary-door law and the
    door is LIVE in this world (its active_rules carry VOCAB-DOOR-LAW); the whole driven census is
    classified in the pack, so the founding still passes its own door."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.blob_dir = os.path.join(self.dir, "blobs")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(self.path, self.blob_dir)

    def _make_law_live(self):
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": VOCAB_DOOR_LAW, "value": 1})
        self.assertIn(VOCAB_DOOR_LAW, self.views.active_rules())


# ---------------------------------------------------------------------------------------------
# A1 — PLACEMENT BY DECLARATION (member 1): content declared -> blob, the row keeps the hash.
# ---------------------------------------------------------------------------------------------
class TestPlacementByDeclaration(_World):
    def test_declared_content_routes_to_blob_row_keeps_hash_structural_inline(self):
        # A test op: `body` declared CONTENT (content_params), `path` STRUCTURAL. The law need not
        # be live for member 1 — placement is the built mechanism; the door is member 2.
        d = {"law_cited": "SOP", "object_param": "path",
             "params": {"path": "required", "body": "required"},
             "payload_from": ["path"], "content_params": {"body": {"hash": "body_hash"}},
             STRUCTURAL_PARAMS: ["path"]}
        self.gate.execute("CREATE-OP", "owner", {"name": "PUT-DOC", "definition": d})
        self.gate.execute("PUT-DOC", "owner", {"path": "/doc", "body": "the full interior text"})

        rec = [e for e in self.store.all() if e.get("action") == "PUT-DOC"][-1]
        payload = rec["payload"]
        # the row keeps the HASH, never the bytes:
        self.assertIn("body_hash", payload)
        self.assertTrue(payload["body_hash"].startswith("sha256:"))
        self.assertNotIn("body", payload)
        self.assertNotIn("the full interior text", repr(payload))
        # the structural field stays inline:
        self.assertEqual(payload.get("path"), "/doc")
        # the blob resolves BY HASH to the exact bytes (content-addressed, custody-conservable):
        self.assertEqual(self.gate.blobs.get(payload["body_hash"]), b"the full interior text")
        self.assertEqual(payload["body_hash"],
                         "sha256:" + hashlib.sha256(b"the full interior text").hexdigest())

    def test_round_trip_content_resolves_by_hash_after_replay(self):
        d = {"law_cited": "SOP", "object_param": "path",
             "params": {"path": "required", "body": "required"},
             "payload_from": ["path"], "content_params": {"body": {"hash": "body_hash"}},
             STRUCTURAL_PARAMS: ["path"]}
        self.gate.execute("CREATE-OP", "owner", {"name": "PUT-DOC", "definition": d})
        self.gate.execute("PUT-DOC", "owner", {"path": "/doc", "body": "replay me"})
        h = [e for e in self.store.all() if e.get("action") == "PUT-DOC"][-1]["payload"]["body_hash"]
        # replay from the file alone: the record carries the hash, the blob still resolves.
        store2, gate2, _, _, _ = build_full_kernel(self.path, self.blob_dir)
        rec2 = [e for e in store2.all() if e.get("action") == "PUT-DOC"][-1]
        self.assertEqual(rec2["payload"]["body_hash"], h)
        self.assertEqual(gate2.blobs.get(h), b"replay me")


# ---------------------------------------------------------------------------------------------
# A2 — THE DOOR REFUSES AN UNCLASSIFIED FIELD (member 2), at all three doors + the held guard.
# ---------------------------------------------------------------------------------------------
class TestVocabularyDoorRefuses(_World):
    def test_founding_door_refuses_unclassified_when_law_live(self):
        recs = _min_recs_with_op(_unclassified_def(), declare_law=True)
        with self.assertRaises(FoundingIntegrityError) as cm:
            install._validate(recs)
        self.assertIn("unclassified", str(cm.exception))

    def test_create_op_door_refuses_unclassified_when_law_live(self):
        self._make_law_live()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-OP", "owner",
                              {"name": "BAD", "definition": _unclassified_def()})
        self.assertIn("unclassified", str(cm.exception))

    def test_amend_op_door_refuses_unclassified_when_law_live(self):
        self._make_law_live()
        # a live, classified op...
        self.gate.execute("CREATE-OP", "owner", {"name": "AMD", "definition": _classified_def()})
        # ...amended DOWN to an unclassified definition is refused at the AMEND-OP door.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-OP", "owner",
                              {"name": "AMD", "definition": _unclassified_def()})
        self.assertIn("unclassified", str(cm.exception))

    def test_door_INERT_where_law_not_live_the_wire_at_birth_toggle(self):
        # THE WIRE-AT-BIRTH GATE IS A REAL TOGGLE, driven both directions. A founding that does NOT
        # declare the vocabulary-door law classifies nothing and founds exactly as before; the SAME
        # unclassified definition is refused ONLY where the law is live. Production now declares the
        # law (the mover landed), so the "not live" world is a founding that OMITS it — a minimal recs
        # list with declare_law=False — never the live production world this class founds from.
        recs = _min_recs_with_op(_unclassified_def(), declare_law=False)
        install._validate(recs)   # no raise: the founding door is inert where the law is not declared
        # and at the shared door function the toggle drives both ways — inert when not live, refusing
        # when live — so the wire-at-birth gate can fail (an always-on door would refuse the left side):
        self.assertEqual(_door_verdict(_unclassified_def(), law_live=False), [])   # inert: admitted
        self.assertTrue(_door_verdict(_unclassified_def(), law_live=True))         # live: refused


# ---------------------------------------------------------------------------------------------
# A3 — THE DOOR ADMITS A FULLY-CLASSIFIED DEFINITION (it discriminates, does not over-block).
# ---------------------------------------------------------------------------------------------
class TestVocabularyDoorAdmits(_World):
    def test_founding_door_admits_fully_classified_when_law_live(self):
        install._validate(_min_recs_with_op(_classified_def(), declare_law=True))   # no raise

    def test_create_op_door_admits_fully_classified_when_law_live(self):
        self._make_law_live()
        self.gate.execute("CREATE-OP", "owner", {"name": "GOOD", "definition": _classified_def()})
        self.assertTrue(self.gate.has("GOOD"))

    def test_amend_op_door_admits_fully_classified_when_law_live(self):
        self._make_law_live()
        self.gate.execute("CREATE-OP", "owner", {"name": "AMD2", "definition": _classified_def()})
        amended = {"law_cited": "SOP", "object_param": "x",
                   "params": {"x": "required", "y": "required"},
                   "checks": [], STRUCTURAL_PARAMS: ["x", "y"]}
        self.gate.execute("AMEND-OP", "owner", {"name": "AMD2", "definition": amended})   # no raise

    def test_content_classified_field_needs_no_structural_entry(self):
        # a param classified CONTENT (content_params) is classified WITHOUT a structural_params
        # entry — the two classes cover the field between them; the door admits.
        self._make_law_live()
        d = {"law_cited": "SOP", "object_param": "path",
             "params": {"path": "required", "body": "required"},
             "payload_from": ["path"], "content_params": {"body": {"hash": "body_hash"}},
             STRUCTURAL_PARAMS: ["path"]}
        self.gate.execute("CREATE-OP", "owner", {"name": "MIXED", "definition": d})
        self.assertTrue(self.gate.has("MIXED"))


# ---------------------------------------------------------------------------------------------
# A4 — NO SIZE NUMBER (design/46 §2.1). Placement + door read the DECLARATION, never a threshold.
# ---------------------------------------------------------------------------------------------
class TestNoSizeNumber(_World):
    def test_tiny_content_still_routes_to_blob_not_kept_inline_for_being_small(self):
        # A size FLOOR would keep small content inline; declaration-routing does not. A one-byte
        # content declared content_params still goes to the blob and the row keeps its hash.
        d = {"law_cited": "SOP", "object_param": "path",
             "params": {"path": "required", "body": "required"},
             "payload_from": ["path"], "content_params": {"body": {"hash": "body_hash"}},
             STRUCTURAL_PARAMS: ["path"]}
        self.gate.execute("CREATE-OP", "owner", {"name": "TINY", "definition": d})
        self.gate.execute("TINY", "owner", {"path": "/p", "body": "x"})
        rec = [e for e in self.store.all() if e.get("action") == "TINY"][-1]
        self.assertNotIn("body", rec["payload"])
        self.assertEqual(self.gate.blobs.get(rec["payload"]["body_hash"]), b"x")

    def test_door_verdict_is_declaration_only_no_size_token_in_the_path(self):
        # The classification path reads NO size/threshold: driven by scanning the exact functions
        # this EP added/owns. A regression that reintroduced the struck size floor would reappear
        # as one of these tokens.
        src = "".join(inspect.getsource(f) for f in (
            opdefs._content_home_params,
            opdefs.structural_field_classification,
            opdefs._require_field_classification))
        for banned in ("size_floor", "threshold", "min_size", "max_size", "size_gate", "SIZE_FLOOR"):
            self.assertNotIn(banned, src,
                             f"a size token {banned!r} entered the declaration-driven path (RW3)")

    def test_classification_verdict_independent_of_any_value(self):
        # The door verdict is a pure function of the DECLARATIONS; there is no value to size at
        # definition time. Same declared def -> same verdict, admitted, with the law live.
        self.assertEqual(_door_verdict(_classified_def()), [])
        self.assertTrue(_door_verdict(_unclassified_def()))   # refused (non-empty), by declaration


# ---------------------------------------------------------------------------------------------
# A5 — THE ONE-TIME CENSUS SWEEP, DRIVEN POPULATION (never a named list, §A57).
# ---------------------------------------------------------------------------------------------
class TestCensusSweepExhaustive(unittest.TestCase):
    def setUp(self):
        # DRIVEN: the census is read from the founding, never a named subset (§A57).
        self.census = install.op_definitions()

    def test_census_is_driven_not_a_named_list(self):
        # driven from install.op_definitions() in setUp (never a named subset, §A57); the count is
        # proven present here. (F5: a constant-True `all(... or True)` line was pruned — it covered
        # nothing; the driven-not-named property is carried by setUp + this count + the STRIPPED
        # can-fail control in test_before_sweep_the_STRIPPED_census_reds_and_names_the_ops below.)
        self.assertGreater(len(self.census), 0)

    def test_before_sweep_the_STRIPPED_census_reds_and_names_the_ops(self):
        # RECONCEIVED (the mover landed): the driven census now CARRIES its classification, so reading
        # it back and running the door proves nothing — it would admit everything (vacuous). To keep a
        # control that CAN FAIL, reconstruct the PRE-SWEEP red-world by STRIPPING every op's
        # structural_params, then drive the door with the law live: every op that declares a non-content
        # param is REFUSED, and the refused set is exactly those ops, NAMED. This is the sweep's real
        # work made visible — a control that cannot fail is not a gate.
        stripped = {n: {k: v for k, v in d.items() if k != STRUCTURAL_PARAMS}
                    for n, d in self.census.items()}
        refused = sorted(n for n, d in stripped.items() if _door_verdict(d))
        must_red = sorted(n for n, d in self.census.items()
                          if structural_field_classification(d))   # ops with a non-content param
        self.assertGreater(len(refused), 0,
                           "the door admitted the STRIPPED census — it cannot fail, so it proves "
                           "nothing (a check that cannot fail is not a gate)")
        self.assertEqual(refused, must_red,
                         "stripping the sweep must red EXACTLY the ops carrying a non-content "
                         "param — no more (over-block), no less (a missed op)")

    def test_after_sweep_the_whole_census_passes_the_door(self):
        # Apply the one-time sweep to the DRIVEN census and run EVERY definition through the door
        # with the law live: zero refusals. An op left unclassified would red here (RW4).
        misses = {}
        for name, d in self.census.items():
            swept = dict(d)
            swept[STRUCTURAL_PARAMS] = structural_field_classification(d)
            refusals = _door_verdict(swept)
            if refusals:
                misses[name] = refusals
        self.assertEqual(misses, {},
                         f"the swept census did not pass the door whole: {sorted(misses)}")

    def test_RW4_an_op_left_unclassified_after_the_sweep_reds(self):
        # Take the whole census (now carrying its classification), then STRIP one op's classification:
        # that op, and only that op, is refused — the sweep is exhaustive over the DRIVEN census, not a
        # named subset. The target is an op with a NON-content param, so removing structural_params
        # leaves it genuinely unclassified (an all-content op would stay classified with none).
        target = next(n for n, d in self.census.items() if structural_field_classification(d))
        offenders = []
        for name, d in self.census.items():
            swept = {k: v for k, v in d.items() if k != STRUCTURAL_PARAMS}   # start from the stripped op
            if name != target:
                swept[STRUCTURAL_PARAMS] = structural_field_classification(d)   # re-sweep every other op
            # target keeps NO structural_params -> its non-content param(s) unclassified
            if _door_verdict(swept):
                offenders.append(name)
        self.assertEqual(offenders, [target],
                         "exactly the un-swept op must red — no more, no less")

    def test_sweep_classes_are_disjoint_content_never_also_structural(self):
        # The two classes stay disjoint by construction: a content-classed param is never also
        # listed structural (design/46 — content and structural are the two exclusive classes).
        for name, d in self.census.items():
            structural = set(structural_field_classification(d))
            content = opdefs._content_home_params(d)
            self.assertEqual(structural & content, set(),
                             f"{name}: a param is in BOTH classes after the sweep")


# ---------------------------------------------------------------------------------------------
# The two founding LAW rule_ids are defined and DECLARED in production (the mover landed).
# ---------------------------------------------------------------------------------------------
class TestLawConstantsDefined(unittest.TestCase):
    def test_the_two_law_rule_ids_exist(self):
        self.assertEqual(PLACEMENT_LAW, "PLACEMENT-LAW")
        self.assertEqual(VOCAB_DOOR_LAW, "VOCAB-DOOR-LAW")

    def test_production_founding_declares_BOTH_laws_the_mover_landed(self):
        # A6 / RW-F FLIPPED LIVE: the create is the owner's fourth serial mover and it LANDED
        # (COMPLETE-CUSTODY-FAMILY members 1-2, board :2870 item 4). Production now declares BOTH laws,
        # so a production-founded world carries VOCAB-DOOR-LAW as an active rule (the door is LIVE) and
        # a fresh unclassified CREATE-OP is refused. This is the live inverse of the retired held guard
        # ("neither law present, byte-untouched"); it reds if the mover is ever reverted.
        pack = install.load_pack()
        rule_ids = {(r.get("payload") or {}).get("rule_id") for r in install.records(pack)}
        self.assertIn(VOCAB_DOOR_LAW, rule_ids)
        self.assertIn(PLACEMENT_LAW, rule_ids)
        d = tempfile.mkdtemp()
        store, gate, views, blobs, _ = build_full_kernel(
            os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"))
        self.assertIn(VOCAB_DOOR_LAW, views.active_rules())
        with self.assertRaises(OpError):
            gate.execute("CREATE-OP", "owner", {"name": "BAD", "definition": _unclassified_def()})


if __name__ == "__main__":
    unittest.main()
