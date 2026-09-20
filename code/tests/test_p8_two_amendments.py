"""C6 P8 — THE TWO AMENDMENTS (ATTEST; RECEIPT) AND THE TWO DECLARATIONS (the cell; the capabilities).

Acceptance battery A1-A5 (and A3b/A3c/A3d) for the campaign's SOLE founding move, per-module runnable
(`python3 -m unittest tests.test_p8_two_amendments`). Every probe is a regression test.

WHAT P8 DECLARES, and how it is HELD:
  * VERIFY-ACCOUNT (the attest-shaped op) gains OPTIONAL structural `target` + `evidence_kind` (B17);
  * RECEIPT gains OPTIONAL structural `checks` + `disclosure_level` + `address_form` (SPIKE-3 N2 /
    SPIKE-5), admitted_level DERIVED AT READ, never stored (I10);
  * the two capabilities + the closed class domain, the actor-classes founding data (B16, K12);
  * the CELL per operation (S | U | U{s} | S{u}), founding data on every op, and CELL-LAW (L28).
ENFORCEMENT OF THE (class, cell) PAIRING IS HELD — everything here is read-side derivation and a
dry-run census; no live act-door refusal is wired (archi precision 2, board :3688).
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel                      # noqa: E402
from kernel.compose import build_full_kernel              # noqa: E402
from kernel.errors import OpError                         # noqa: E402
from kernel import border                                 # noqa: E402
from kernel.opdefs import (                               # noqa: E402
    validate_definition_shape, OP_CHECKS, CELL, CELL_SET, CELL_LAW, STRUCTURAL_PARAMS)
from founding import install                              # noqa: E402
from founding.install import FoundingIntegrityError, op_definitions  # noqa: E402


# A door that RECORDS refusals instead of raising — reads a definition's verdict at the shared door.
class _RecordingDoor:
    def __init__(self):
        self.refusals = []

    def refuse(self, actor, op, rule, message):
        self.refusals.append((actor, op, rule, message))


def _door_verdict(definition, classify_law_live=False):
    door = _RecordingDoor()
    validate_definition_shape(door, "FOUNDING", "SYSTEM", "PROBE", definition,
                              peers={}, classify_law_live=classify_law_live)
    return door.refusals


def _recs_with_op(definition, name="PROBE", declare_cell_law=True):
    """A minimal founding record list: optionally the CELL-LAW (self-declared by rule_id) and one
    CREATE-OP op_definition — enough to drive `install._validate` through the FOUNDING door."""
    recs = []
    if declare_cell_law:
        recs.append({"actor": "SYSTEM", "action": "CREATE-RULE", "object": "CELL-LAW",
                     "rule_cited": "BOOT-INT", "payload": {"rule_id": CELL_LAW}})
    recs.append({"actor": "SYSTEM", "action": "CREATE-OP", "object": f"op:{name}",
                 "rule_cited": "CAP-IS-LAW",
                 "payload": {"kind": "op_definition", "name": name, "definition": definition}})
    return recs


class _World(unittest.TestCase):
    """A disposable world founded from the PRODUCTION pack v1.51.0, blobs + vault wired."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.path, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))


# =====================================================================================
# A1 — THE ATTEST AMENDMENT: TARGET + EVIDENCE KIND, STRUCTURAL; a class computed AT READ.
# =====================================================================================
class TestA1AttestAmendment(_World):
    def test_the_two_new_params_are_declared_structural_in_the_op_meta(self):
        d = op_definitions()["VERIFY-ACCOUNT"]
        self.assertIn("target", d["params"])
        self.assertIn("evidence_kind", d["params"])
        # DECLARED STRUCTURAL (the op-amend lesson): a new field lives in structural_params or the
        # door refuses it. Both are, and neither is required (a bare identity-verify omits them).
        self.assertIn("target", d[STRUCTURAL_PARAMS])
        self.assertIn("evidence_kind", d[STRUCTURAL_PARAMS])
        self.assertNotEqual(d["params"]["target"], "required")
        self.assertNotEqual(d["params"]["evidence_kind"], "required")

    def test_a_call_carrying_the_new_fields_is_validated_and_recorded(self):
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "acct1", "actor_class": "program"})
        self.gate.execute("VERIFY-ACCOUNT", "owner",
                          {"account": "acct1", "evidence_hash": "sha256:ab",
                           "target": "program", "evidence_kind": "self-attestation"})
        rec = [e for e in self.store.all() if e.get("action") == "VERIFY-ACCOUNT"][-1]
        self.assertEqual(rec["payload"].get("target"), "program")
        self.assertEqual(rec["payload"].get("evidence_kind"), "self-attestation")

    def test_a_class_is_the_latest_live_classify_act_computed_at_read(self):
        # the account's stored actor_class is one thing; a classify act SUPERSEDES it, computed at read.
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "acct2", "actor_class": "program"})
        self.assertEqual(self.views.class_band("acct2"), "program")           # falls back to actor_class
        self.gate.execute("VERIFY-ACCOUNT", "owner",
                          {"account": "acct2", "evidence_hash": "sha256:1", "target": "human",
                           "evidence_kind": "credential"})
        self.assertEqual(self.views.class_band("acct2"), "human")             # the classify act wins
        self.gate.execute("VERIFY-ACCOUNT", "owner",
                          {"account": "acct2", "evidence_hash": "sha256:2", "target": "ai",
                           "evidence_kind": "credential"})
        self.assertEqual(self.views.class_band("acct2"), "ai")                # the LATEST wins, at read
        # nothing was stored as "the band": it is recomputed each read from the record.
        self.assertNotIn("band", (self.views.accounts().get("acct2") or {}))

    def test_a_call_omitting_a_required_structural_field_is_refused_at_the_door(self):
        # the door still refuses a VERIFY-ACCOUNT missing its existing required-structural field.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("VERIFY-ACCOUNT", "owner", {"evidence_hash": "sha256:x"})  # no `account`
        self.assertEqual(cm.exception.rule, "AR-2")

    def test_the_op_amend_lesson_a_field_not_declared_structural_is_refused_at_the_door(self):
        # STOP (b): a new field that "works" without being declared structural is the op-amend defect.
        # A VERIFY-ACCOUNT-shaped def carrying `target` as a param but NOT classifying it is refused at
        # the definition door (the vocabulary door, when the classification law is live).
        d = {"law_cited": "CAP-IS-LAW", "object_param": "account",
             "params": {"account": "required", "target": "optional"},
             STRUCTURAL_PARAMS: ["account"]}                      # `target` UNCLASSIFIED
        refusals = _door_verdict(d, classify_law_live=True)
        self.assertTrue(any(r[2] == "AR-2" and "target" in r[3] for r in refusals),
                        "the door must refuse an undeclared payload field (the op-amend lesson)")
        # declaring it structural admits it (R1 drives both ways).
        d2 = dict(d, **{STRUCTURAL_PARAMS: ["account", "target"]})
        self.assertEqual(_door_verdict(d2, classify_law_live=True), [])


# =====================================================================================
# A2 — THE RECEIPT AMENDMENT: THREE FIELDS, STRUCTURAL; admitted_level DERIVED AT READ.
# =====================================================================================
class TestA2ReceiptAmendment(_World):
    def test_the_three_new_params_are_declared_structural_in_the_op_meta(self):
        d = op_definitions()["RECEIPT"]
        for f in ("checks", "disclosure_level", "address_form"):
            self.assertIn(f, d["params"], f)
            self.assertIn(f, d[STRUCTURAL_PARAMS], f)
            self.assertNotEqual(d["params"][f], "required", f)          # optional: a bare row receipt omits them
        self.assertEqual(d["param_kinds"].get("disclosure_level"), "text")
        self.assertEqual(d["param_kinds"].get("address_form"), "text")

    def test_admitted_level_is_derived_at_read_never_stored(self):
        # a graded receipt CARRIES its checks map + disclosure_level; admitted_level is NOT a field.
        self.gate.execute("RECEIPT", "owner",
                          {"content_hash": "sha256:seg1", "from_body": {"key": "k", "genesis": "g"},
                           "from_sig": "sig", "under_rule": "COMM-LAW-CONTRACT", "revealed_set": {},
                           "checks": {"who": True, "body": True, "memory_sane": False},
                           "disclosure_level": "FULL", "address_form": "row"})
        rec = [e for e in self.store.all() if e.get("action") == "RECEIPT"][-1]["payload"]
        self.assertNotIn("admitted_level", rec)                         # NEVER stored (I10; stop d)
        # derived AT READ from the receipt's own recorded fields:
        self.assertEqual(border.admitted_level(dict(rec["checks"]), rec["disclosure_level"]), "SHELLS")

    def test_admitted_level_derivation_grades_and_never_refuses_when_any_check_passes(self):
        self.assertEqual(border.admitted_level({"who": True, "body": True, "memory_sane": True}, "FULL"), "FULL")
        self.assertEqual(border.admitted_level({"who": True, "body": True, "memory_sane": False}, "FULL"), "SHELLS")
        self.assertEqual(border.admitted_level({"who": True, "body": False, "memory_sane": False}, "FULL"), "HASHES-ONLY")
        self.assertIsNone(border.admitted_level({"who": False, "body": False, "memory_sane": False}, "FULL"))
        # bounded by the presented disclosure ceiling (never above what was shown):
        self.assertEqual(border.admitted_level({"who": True, "body": True, "memory_sane": True}, "HASHES-ONLY"), "HASHES-ONLY")
        self.assertIsNone(border.admitted_level({"who": True}, "NONSENSE"))   # unknown level -> fail-closed

    def test_a_malformed_field_is_refused_at_the_door(self):
        # param_kinds `text` on disclosure_level: a raw bytes value is refused AT THE DOOR (AR-2),
        # before the record write it would crash. The op-amend lesson's door-layer acceptance.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RECEIPT", "owner",
                              {"content_hash": "sha256:seg2", "from_body": {}, "from_sig": "s",
                               "under_rule": "COMM-LAW-CONTRACT", "revealed_set": {},
                               "disclosure_level": b"\xff\xfe"})
        self.assertEqual(cm.exception.rule, "AR-2")

    def test_a_bare_row_receipt_still_records_the_five_original_fields(self):
        # backward compatible: a receipt omitting the three new fields records exactly as before (the
        # new fields carry None, an honest absent, and nothing crashes).
        self.gate.execute("RECEIPT", "owner",
                          {"content_hash": "sha256:seg3", "from_body": {"key": "k"}, "from_sig": "s",
                           "under_rule": "COMM-LAW-CONTRACT", "revealed_set": {}})
        rec = [e for e in self.store.all() if e.get("action") == "RECEIPT"][-1]["payload"]
        self.assertEqual(rec["content_hash"], "sha256:seg3")
        self.assertIsNone(rec.get("disclosure_level"))

    def test_the_segment_binds_check_verifies_by_blob_rehash(self):
        # SPIKE-5: a SEGMENT receipt cites the segment hash in the content_hash slot and is verified
        # by a blob-address rehash, NOT by content_id.
        seg = b"row1\nrow2\nrow3"
        seg_hash = "sha256:" + hashlib.sha256(seg).hexdigest()
        receipt = {"payload": {"content_hash": seg_hash, "address_form": "segment"}}
        self.assertTrue(border.receipt_binds_segment(receipt, seg))
        self.assertFalse(border.receipt_binds_segment(receipt, b"different bytes"))


# =====================================================================================
# A3 — THE TWO CAPABILITY DECLARATIONS; THE CLASS DOMAIN CLOSES (K12).
# =====================================================================================
class TestA3Capabilities(_World):
    def test_the_two_capabilities_and_three_classes_are_founding_data(self):
        caps = self.views.class_capabilities()
        self.assertEqual(caps["human"], ("structured-arm", "unstructured-arm"))   # both
        self.assertEqual(caps["ai"], ("unstructured-arm",))                        # unstructured only
        self.assertEqual(caps["program"], ("structured-arm",))                     # structured only

    def test_the_class_domain_is_closed_a_class_not_in_the_list_is_not_a_valid_band(self):
        self.assertEqual(set(self.views.class_domain()), {"human", "ai", "program"})   # K12 closed
        # P8b COMPANION (archi :3726, disclosed): the write-side closure (P8b A6) now REFUSES a
        # non-domain token AT THE GATE, so this READ-side-closure probe plants its None band by a
        # PRE-FLIP path (a raw append, as a legacy record predating the enforcement) rather than
        # through CREATE-ACCOUNT — the ORIGINAL INTENT (a class outside the domain reads as band None)
        # is preserved unchanged; the write-refusal itself is proved in tests.test_p8b_pairing_enforces.
        self.store._append({"actor": "owner", "action": "CREATE-ACCOUNT", "rule_cited": "CAP-IS-LAW",
                            "object": "weird", "payload": {"account_id": "weird", "actor_class": "wizard"}})
        self.assertIsNone(self.views.class_band("weird"))            # a class outside the domain is None
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "prog", "actor_class": "program"})
        self.assertEqual(self.views.class_band("prog"), "program")   # a declared class is a valid band


# =====================================================================================
# A3b — THE CELL DECLARATION AND THE (class, cell) PAIRING.
# =====================================================================================
class TestA3bCellPairing(_World):
    def test_every_operation_declares_a_cell_as_founding_data(self):
        ops = op_definitions()
        # C6a VT-2 (CREATE-RELATIONSHIP MINTED live, 1.51.0 -> 1.52.0) moved the live base 93 -> 94 BY NAME (§A57).
        self.assertEqual(len(ops), 94)                               # live op-population (P8 +0; VT-2 +1)
        for name, d in ops.items():
            self.assertIn(d.get(CELL), CELL_SET, f"{name} declares no well-formed cell")

    def test_the_required_capability_is_read_off_the_cell_no_table(self):
        self.assertEqual(self.views.required_capability("S"), "structured-arm")
        for judgment_cell in ("U", "U{s}", "S{u}"):
            self.assertEqual(self.views.required_capability(judgment_cell), "unstructured-arm")

    def test_the_pairing_program_refused_at_a_judgment_cell_ai_at_a_pure_S_cell_human_holds_any(self):
        # each planted, each reds / admits (the ceiling machinery's pairing):
        self.assertFalse(self.views.pair("program", "U")[0])         # a program at a judgment cell: refused
        self.assertFalse(self.views.pair("program", "U{s}")[0])
        self.assertTrue(self.views.pair("program", "S")[0])          # a program at a structured cell: held
        self.assertFalse(self.views.pair("ai", "S")[0])              # an AI at a pure-S cell: refused
        self.assertTrue(self.views.pair("ai", "U")[0])               # an AI at a judgment cell: held
        for cell in CELL_SET:
            self.assertTrue(self.views.pair("human", cell)[0])       # a human holds any
        # fail-closed on an undeclared class or an unrecognised cell:
        self.assertFalse(self.views.pair("wizard", "S")[0])
        self.assertFalse(self.views.pair("human", "Z")[0])


# =====================================================================================
# A3c — THE DECLARED-S REPLAY GUARD.
# =====================================================================================
class TestA3cDeclaredSReplay(_World):
    def test_every_declared_S_op_on_the_real_founding_replays_to_identity(self):
        # the estate's founding property: every gov-os op is a structured record-mechanic that replays.
        self.assertEqual(self.views.declared_s_findings(), [])

    def test_a_planted_declared_S_op_that_does_not_replay_is_a_finding(self):
        # a declared-S op flagged non-replayable is a FINDING (reds); a judgment op is exempt (never scored).
        self.gate.execute("CREATE-OP", "owner",
                          {"name": "BADS", "definition": {"law_cited": "SOP", "object_param": "x",
                           "params": {"x": "required"}, "checks": [], STRUCTURAL_PARAMS: ["x"],
                           CELL: "S", "replays_to_identity": False}})
        self.assertIn("BADS", self.views.declared_s_findings())
        self.gate.execute("CREATE-OP", "owner",
                          {"name": "JUDGE", "definition": {"law_cited": "SOP", "object_param": "x",
                           "params": {"x": "required"}, "checks": [], STRUCTURAL_PARAMS: ["x"],
                           CELL: "U", "replays_to_identity": False}})
        self.assertNotIn("JUDGE", self.views.declared_s_findings())    # a judgment op is never scored


# =====================================================================================
# A3d — THE DRY-RUN CENSUS BEFORE ENFORCEMENT (enforcement HELD).
# =====================================================================================
class TestA3dCensus(_World):
    def test_the_census_publishes_with_its_world_and_refuses_no_act(self):
        c = self.views.pairing_census(pack_version="1.51.0")
        self.assertEqual(c["world"]["founding_version"], "1.51.0")
        self.assertEqual(c["world"]["as_of_head"], len(self.store.all()))
        self.assertIn("HELD", c["enforcement"])                        # enforcement is HELD, not live
        # the census REPORTS; it appended nothing and refused nothing (the record is unchanged):
        before = len(self.store.all())
        self.views.pairing_census(pack_version="1.51.0")
        self.assertEqual(len(self.store.all()), before)

    def test_the_recorder_system_is_outside_the_pairing(self):
        c = self.views.pairing_census(pack_version="1.51.0")
        # the founding runtime's acts are excluded (archi precision 3), counted separately:
        self.assertGreater(c["counts"]["recorder_system_excluded"], 0)
        self.assertEqual(c["counts"]["ops_without_wellformed_cell"], 0)

    def test_the_census_names_a_would_be_refusal_by_name(self):
        # plant a real actor act the pairing WOULD refuse: an AI account acting at a pure-S op.
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "ai_bot", "actor_class": "ai"})
        self.store._append({"actor": "ai_bot", "action": "COMPARE", "rule_cited": "SOP",
                            "object": "cmp:1", "payload": {}})
        c = self.views.pairing_census(pack_version="1.51.0")
        hits = [w for w in c["would_refuse"] if w["actor"] == "ai_bot"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["class"], "ai")
        self.assertEqual(hits[0]["cell"], "S")
        self.assertIn("ai", hits[0]["reason"])
        self.assertEqual(c["counts"]["would_refuse"], 1)


# =====================================================================================
# A4 — THE FOUNDING MOVE: ONE MINOR BUMP, NO NEW CHECK KIND; the cell-presence founding door.
# =====================================================================================
class TestA4FoundingMove(unittest.TestCase):
    def test_one_minor_bump_no_new_check_kind_op_population_unchanged(self):
        import json
        with open(os.path.join(os.path.dirname(__file__), "..", "src", "founding",
                               "founding-pack.json")) as f:
            pack = json.load(f)
        # C6a VT-2 (CREATE-RELATIONSHIP MINTED live) bumped 1.51.0 -> 1.52.0 and moved the base 93 -> 94.
        # C6a VT-3 (THE TREE SEEDED AS ROWS — 35 view rows) bumped 1.52.0 -> 1.53.0 BY NAME (§A57); it mints
        # NO op and NO check kind, so op-population and OP_CHECKS below are UNCHANGED (view rows, not ops).
        # C6a VT-6d (THE STAMP FOUNDING — the required-stamps policy rule) bumped 1.53.0 -> 1.54.0 BY NAME (§A57);
        # it mints ONE policy rule, NO op and NO check kind, so op-population and OP_CHECKS below stay UNCHANGED.
        # C7 P3 (THE KERNEL FROM THE RECORD — the twelve act-kind rows) bumped 1.54.0 -> 1.55.0 BY NAME (§A57);
        # act-kind rows are CREATE-RULE law, NO op and NO check kind, so op-population and OP_CHECKS stay UNCHANGED.
        self.assertEqual(pack["founding_version"], "1.55.0")           # the live founding version (C7 P3's move; P8's own move was the 1.51.0 MINOR)
        self.assertEqual(len(OP_CHECKS), 19)                           # NO new check kind
        self.assertEqual(len(op_definitions()), 94)                    # live op-population (P8 +0; VT-2 +1; VT-3 +0)

    def test_the_founding_door_refuses_an_op_that_declares_no_cell_when_cell_law_live(self):
        # every op in a CELL-LAW founding declares a cell or the WHOLE founding is refused (never defaulted).
        cell_less = {"law_cited": "SOP", "object_param": "x", "params": {"x": "required"}, "checks": []}
        with self.assertRaises(FoundingIntegrityError) as cm:
            install._validate(_recs_with_op(cell_less, declare_cell_law=True))
        self.assertIn("cell", str(cm.exception))

    def test_the_founding_door_is_inert_where_cell_law_is_not_declared(self):
        # a world before P8 (no CELL-LAW) requires no cell and founds exactly as before (wire-at-birth).
        cell_less = {"law_cited": "SOP", "object_param": "x", "params": {"x": "required"}, "checks": []}
        install._validate(_recs_with_op(cell_less, declare_cell_law=False))     # no raise

    def test_the_founding_door_admits_an_op_with_a_well_formed_cell(self):
        good = {"law_cited": "SOP", "object_param": "x", "params": {"x": "required"}, "checks": [],
                CELL: "S"}
        install._validate(_recs_with_op(good, declare_cell_law=True))           # no raise

    def test_a_malformed_cell_value_is_refused_at_the_definition_door_at_every_door(self):
        # the value-guard runs at ALL doors, regardless of the law (well-formedness is not law-gated).
        bad = {"law_cited": "SOP", "object_param": "x", "params": {"x": "required"}, "checks": [],
               CELL: "X"}
        refusals = _door_verdict(bad, classify_law_live=False)
        self.assertTrue(any(r[2] == "AR-2" and "cell" in r[3] for r in refusals))


# =====================================================================================
# A5 — the founded kernel builds and replays (the whole-ledger green is the per-module suite drive).
# =====================================================================================
class TestA5WholeLedgerSmoke(_World):
    def test_the_founding_installs_and_the_actor_classes_and_cell_law_are_live(self):
        self.assertIn("CELL-LAW", self.views.active_rules())
        self.assertIn("actor-classes", self.views.category_packs())
        # a rebuild from the file adds nothing (the founding roundtrip property survives the amendment):
        store2, _g2, _v2, _b2, _s2 = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.assertEqual(len(store2.all()), len(self.store.all()))


if __name__ == "__main__":
    unittest.main()
