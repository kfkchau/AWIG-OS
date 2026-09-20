# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (record, pen, scope relation, custody handover, departure record) as in the
# seL4/gVisor literature. NON-GOAL: no offensive capability of any kind — this battery proves, by
# function over mechanisms C5/C6 already built, that a machine holds MANY records each with ONE pen,
# resolves scope overlap by a declared relation in both, and consolidates only by the handover
# ceremony. Full declaration: SCOPE-STATEMENT.md.
"""P14 — MANY RECORDS, ONE PEN EACH; HANDOVER (design/52 B10:59, B11:60, I1:73, I14:86, I19:91).

Named in planning/exec/P14-MANY-RECORDS-HANDOVER-BUILD.md before code, landed here as regression
tests (charter: every verification probe lands as a regression test). YELLOW — an interface other
units build on (the many-records relation and the handover), proven over EXISTING mechanisms, NOT a
new op, law or check kind, no pack edit, no founding bump:

  * the ONE-PEN + NO-DELETE CENSUS (tools/conformance/one_pen_no_delete_census.py, this unit's
    tools/ instrument, NOT attested) — the sibling of the effect-order and five-families censuses,
    over the SAME composed registry.
  * the RELATION check kind `bound_field` (src/kernel/opdefs.py, EP-30-K1) — REUSED, not re-authored.
  * the correlation/overlap guard (src/kernel/crossing.py correlation_guard) — REUSED, driven directly.
  * the single-writer lock (src/kernel/store.py, one writer per data dir) — REUSED (EP-48G precedent).
  * the HANDOVER ceremony (src/kernel/erasure.py) — READ and demonstrated IN A TEST FOUNDING WORLD
    only; its production activation rides owner gate MOVER 4 and is NOT this unit's (the erasure.py
    pattern, the test_ep41b HandoverWorld precedent).

A1 (I1)        one pen, by census: no op appends to a record other than the actor's own (the census
               cross-pen set is empty), a PLANTED cross-pen op reds the census (the check can fail),
               and the single-writer lock holds one writer per data dir.
A2 (B10, I19)  two records declaring overlapping scope are resolved by a relation declared in BOTH
               (each by its own pen), never by silent double-governance (the relation check kind and
               the correlation guard, both driven able-to-pass AND able-to-fail); a body holds many
               records and a box many bodies, and two bodies never share a write path (diving-buddy).
A3 (B11, I14)  in a TEST founding world the handover ceremony runs end to end (duplicate, byte-verify,
               a signed receipt, remove the local bytes, a departure record stands); a census finds NO
               merge-by-copy op and NO standalone-delete op, and a PLANTED one of each reds it.
A4             whole-ledger green PER MODULE is this module's own discover (the verifier's re-run).

HONEST CAP. A3 runs in DISPOSABLE test founding worlds on TEST blobs and a TEST key; nothing real is
handed over, and PRODUCTION founding-pack.json is untouched — the production handover flip is MOVER
4's, not this unit's. The census's merge-by-copy arm is a VOCABULARY reading (see the tool's own CAP);
the semantic floor is carried jointly by the one-pen arm, the standalone-delete arm, and the
effect-order census.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernel.boot import build_kernel                                   # noqa: E402
from kernel.compose import build_full_kernel                           # noqa: E402
from kernel.store import EventStore                                    # noqa: E402
from kernel.blobs import BlobStore                                     # noqa: E402
from kernel import erasure, keys, crossing                             # noqa: E402
from kernel.gate import make_invoker_sig                               # noqa: E402
from kernel.errors import OpError                                      # noqa: E402

from tools.conformance import one_pen_no_delete_census as pen_census   # noqa: E402
from tools.conformance.effect_order_census import build_full_kernel_for_census  # noqa: E402


# =============================================================================================
# Planted control handlers — code-registered ops that the census MUST red. Defined at module
# scope so `inspect.getsource` (the census's reader) can read their bodies. They are REGISTERED
# and CENSUSED, never EXECUTED — the census reads source, it does not run the op.
# =============================================================================================

def _cross_pen_handler(actor, params):
    """A handler that attributes its minted row to ANOTHER party — a second pen on a record. The
    census's one-pen arm must read this as cross-pen (it writes a record other than the actor's own)."""
    return {"actor": params["other_party"], "action": "PLANTED-CROSS-PEN",
            "object": params.get("object"), "rule_cited": "BOOT-INT", "payload": {}}


def _standalone_delete_handler(actor, params):
    """A handler that removes bytes OUTSIDE the handover ceremony — a standalone delete. The census's
    no-delete arm must red it (there is no delete function, L14). NEVER executed; the census reads
    the source only, and os.remove below never runs."""
    os.remove(params["path"])
    return {"actor": actor, "action": "PLANTED-DELETE", "rule_cited": "BOOT-INT", "payload": {}}


def _benign_handler(actor, params):
    """A conserving handler used only to give a planted merge-by-copy op a body; the census reds it on
    its NAME, not its body."""
    return {"actor": actor, "action": "PLANTED-MERGE", "rule_cited": "BOOT-INT", "payload": {}}


# =============================================================================================
# A1 — ONE PEN, BY CENSUS (I1). No op appends to a record other than the actor's own.
# =============================================================================================

class A1OnePenByCensus(unittest.TestCase):

    def test_a1_the_shipped_registry_has_no_cross_pen_op(self):
        """I1: over the whole composed registry, NO op writes a record other than the actor's own.
        The census's cross-pen and unknown-pen sets are both empty."""
        _store, gate, views = build_full_kernel_for_census()
        rows = pen_census.census(gate, views)
        self.assertGreater(len(rows), 0)
        self.assertEqual(pen_census.cross_pen_rows(rows), [],
                         "an op writes a second pen — one pen per record refuted (I1)")
        self.assertEqual(pen_census.unknown_pen_rows(rows), [],
                         "an op's attribution could not be read — a cross-pen write could hide")
        # every op is own-pen or the SYSTEM recorder — the two lawful attributions, nothing else.
        for r in rows:
            self.assertIn(r["pen"], ("own-pen", "recorder"), (r["op"], r["pen"]))

    def test_a1_the_census_reds_a_planted_cross_pen_op_the_check_can_fail(self):
        """A CHECK THAT CANNOT FAIL IS NOT A CHECK (RW2). Register a code op whose handler attributes
        its row to ANOTHER party; re-census; the cross-pen set now names exactly it."""
        _store, gate, views = build_full_kernel_for_census()
        gate.register("PLANTED-CROSS-PEN",
                      {"description": "planted", "params": {"other_party": "required"}},
                      _cross_pen_handler)
        rows = pen_census.census(gate, views)
        cross = pen_census.cross_pen_rows(rows)
        self.assertEqual([r["op"] for r in cross], ["PLANTED-CROSS-PEN"])
        self.assertIn("OTHER than the actor's own", cross[0]["pen_reason"])

    def test_a1_the_single_writer_lock_holds_one_writer_per_data_dir(self):
        """I1 STRUCTURAL (the one-pen mechanism at the write, EP-48G precedent reused): a body's
        record has ONE writer per data dir. A live foreign holder (pid 1, init, always alive) refuses
        a second writer; with the pen free a writer acquires (able-to-fail — the refusal is real)."""
        d = tempfile.mkdtemp(prefix="p14-a1-lock-")
        rec_path = os.path.join(d, "record.jsonl")
        with open(rec_path + ".lock", "w") as fh:
            fh.write("1")                                              # pid 1 is always alive
        with self.assertRaises(RuntimeError) as cm:
            EventStore(rec_path, lock=True)
        self.assertIn("one writer per data dir", str(cm.exception))
        os.remove(rec_path + ".lock")
        self.assertIsNotNone(EventStore(rec_path, lock=True))         # the pen free -> acquires


# =============================================================================================
# A2 — SCOPE OVERLAP -> A DECLARED RELATION (B10, I19). Never silent double-governance.
# =============================================================================================

class A2ScopeOverlapDeclaredRelation(unittest.TestCase):
    """B10: records declare scope and write relation rows about each other; a scope overlap is
    resolved by a relation declared in BOTH, never by silent double-governance. Driven over the
    RELATION check kind (`bound_field`) and the correlation/overlap guard, both directions."""

    # the RELATION check kind, declared on a scratch GOVERN-SCOPE op minted through the ordinary
    # CREATE-OP door (the EP-30-K1 A5 pattern). It binds the PRIOR relation record whose `scope`
    # equals the governing act's `scope`, reads the `governor` the relation designates, and requires
    # the acting party to be that governor. With no declared relation the key is UNBOUND and the
    # policy REFUSES (silent double-governance blocked); with a relation declared in both records —
    # both parties acknowledging one governor for the overlapping scope — it admits that governor and
    # REFUSES the other party (the overlap resolves to a single pen, never two governing at once).
    REL_CHECK = {"check": "bound_field", "action": "DECLARE-SCOPE-REL", "field": "scope",
                 "key_param": "scope", "value_field": "governor", "param": "governor",
                 "when_unbound": "refuse", "cite": "SCOPE-REL-LAW",
                 "message": "this scope is governed by a party no declared relation designates"}

    def _world(self):
        d = tempfile.mkdtemp(prefix="p14-a2-")
        store, gate, views, _blobs, _subs = build_full_kernel(
            os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
        # a scratch governance LAW the op and its check cite — appended directly (the test-world
        # stand-in for a founding create, the test_ep41b precedent). Root so CREATE-OP admits the cite.
        store._append({"actor": "SYSTEM", "action": "CREATE-RULE", "object": "SCOPE-REL-LAW",
                       "rule_cited": "BOOT-INT",
                       "payload": {"kind": "rule", "rule_id": "SCOPE-REL-LAW", "root": True,
                                   "polarity": "+", "text": "a scope is governed only against a "
                                   "counterpart a relation declared in both records names"}})
        for inst in ("inst-A", "inst-B"):
            gate.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": inst, "actor_class": "program"})
        # the scratch GOVERN-SCOPE op, carrying the relation check.
        gate.execute("CREATE-OP", "SYSTEM", {
            "kind": "op_definition", "rule_id": "op:GOVERN-SCOPE", "polarity": "+",
            "name": "GOVERN-SCOPE",
            "definition": {"description": "govern a scope against a declared counterpart",
                           "params": {"scope": "required", "governor": "required"},
                           "structural_params": ["scope", "governor"],
                           "law_cited": "SCOPE-REL-LAW", "object_param": "scope",
                           "payload_from": ["scope", "governor"], "checks": [self.REL_CHECK]},
            "tier": "owner", "text": "P14 A2 scratch — govern a scope by a declared relation"})
        return store, gate, views

    def _declare_relation(self, store, actor, scope, governor):
        """A relation ROW, written by `actor`'s OWN pen (I1) — the test-world stand-in for a
        DECLARE-SCOPE-REL op. Each institution declares its own row acknowledging the governor the
        overlap resolves to: the relation stands in BOTH records, each by its own pen."""
        store._append({"actor": actor, "action": "DECLARE-SCOPE-REL", "object": scope,
                       "rule_cited": "SCOPE-REL-LAW",
                       "payload": {"scope": scope, "governor": governor}})

    def test_a2_governing_an_overlapping_scope_with_no_declared_relation_is_refused(self):
        """SILENT DOUBLE-GOVERNANCE BLOCKED: inst-A tries to govern /east while no relation is
        declared for it — the relation check REFUSES (the key is unbound, the policy refuses)."""
        store, gate, _views = self._world()
        with self.assertRaises(OpError) as cm:
            gate.execute("GOVERN-SCOPE", "SYSTEM", {"scope": "/east", "governor": "inst-A"})
        self.assertEqual(cm.exception.rule, "SCOPE-REL-LAW")

    def test_a2_resolved_by_a_relation_declared_in_both_records(self):
        """RESOLVED BY A DECLARED RELATION IN BOTH: inst-A and inst-B each declare, by their OWN pen,
        the /east relation acknowledging inst-A as its governor; inst-A then lawfully governs /east —
        the check admits — and inst-B governing the SAME scope is REFUSED (the overlap resolves to
        ONE pen, never two governing at once)."""
        store, gate, _views = self._world()
        self._declare_relation(store, "inst-A", "/east", "inst-A")   # A's pen
        self._declare_relation(store, "inst-B", "/east", "inst-A")   # B's pen — the relation in BOTH
        r = gate.execute("GOVERN-SCOPE", "SYSTEM", {"scope": "/east", "governor": "inst-A"})
        self.assertEqual(r["action"], "GOVERN-SCOPE")
        # each relation row is attributed to its own institution — one pen each (I1).
        rels = [e for e in store.all() if e["action"] == "DECLARE-SCOPE-REL"]
        self.assertEqual({e["actor"] for e in rels}, {"inst-A", "inst-B"})
        # NEVER TWO GOVERNING AT ONCE: inst-B may not govern the same overlapping scope.
        with self.assertRaises(OpError) as cm:
            gate.execute("GOVERN-SCOPE", "SYSTEM", {"scope": "/east", "governor": "inst-B"})
        self.assertEqual(cm.exception.rule, "SCOPE-REL-LAW")

    def test_a2_a_declared_relation_designating_a_different_governor_is_refused(self):
        """The relation is a RELATION, not a wildcard: a /east relation designating inst-C as governor
        does not license inst-A governing /east — the field mismatch refuses (able-to-fail)."""
        store, gate, _views = self._world()
        self._declare_relation(store, "inst-A", "/east", "inst-C")
        with self.assertRaises(OpError) as cm:
            gate.execute("GOVERN-SCOPE", "SYSTEM", {"scope": "/east", "governor": "inst-A"})
        self.assertEqual(cm.exception.rule, "SCOPE-REL-LAW")

    def test_a2_the_correlation_guard_detects_an_unbound_relation_and_passes_a_declared_one(self):
        """THE OVERLAP/CORRELATION GUARD, REUSED AND DRIVEN DIRECTLY (crossing.correlation_guard).
        A record citing an OPEN declared relation passes; one citing a relation that is missing or
        already closed is REFUSED — the store binds record to record, so an unbound citation carries
        nothing (no silent double-governance). Both directions, the check able to fail."""
        d = tempfile.mkdtemp(prefix="p14-a2-corr-")
        store, gate, views, _b, _s = build_full_kernel(
            os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
        # seed an OPEN hand-out (a declared, live relation another record may cite) directly.
        store._append({"actor": "inst-A", "action": "COMMS-OPEN", "object": "rel:1",
                       "rule_cited": "BOOT-INT",
                       "payload": {"kind": crossing.HANDOUT_KIND, "record_class": "DECISION",
                                   "station": "rel"}})
        open_seq = store.all()[-1]["seq"]
        # a draft citing the OPEN relation PASSES the guard (returns without refusing).
        good = {"actor": "inst-B", "action": "COMMS-RECV", "object": "rel:1",
                "payload": {"kind": crossing.ANSWER_KIND, "handout_seq": open_seq,
                            "fingerprint_check": "pass"}}
        crossing.correlation_guard(gate, store, "inst-B", "COMMS-RECV", good)   # no raise
        # a draft citing a MISSING relation is REFUSED — an unbound citation binds nothing.
        bad = {"actor": "inst-B", "action": "COMMS-RECV", "object": "rel:404",
               "payload": {"kind": crossing.ANSWER_KIND, "handout_seq": 999999,
                           "fingerprint_check": "pass"}}
        with self.assertRaises(OpError) as cm:
            crossing.correlation_guard(gate, store, "inst-B", "COMMS-RECV", bad)
        self.assertEqual(cm.exception.rule, crossing.CORRELATION_RULE)

    def test_a2_a_body_holds_many_records_a_box_holds_many_bodies_two_bodies_never_share_a_path(self):
        """I19: a body is whatever one anchor vouches for — a box may hold several bodies and a body
        several records, and two bodies never share a write path (the diving-buddy cap)."""
        box = tempfile.mkdtemp(prefix="p14-a2-box-")
        # a BODY holds MANY records.
        store_a = EventStore(os.path.join(box, "A", "record.jsonl"), lock=True)
        for i in range(3):
            store_a._append({"actor": "inst-A", "action": "NOTE", "object": "n%d" % i,
                             "rule_cited": "BOOT-INT", "payload": {"i": i}})
        self.assertGreaterEqual(len([e for e in store_a.all() if e["action"] == "NOTE"]), 3)
        # the BOX holds a SECOND body — a distinct record with its own data dir and its own pen.
        store_b = EventStore(os.path.join(box, "B", "record.jsonl"), lock=True)
        store_b._append({"actor": "inst-B", "action": "NOTE", "object": "b0",
                         "rule_cited": "BOOT-INT", "payload": {}})
        self.assertNotEqual(store_a.file_path, store_b.file_path)     # two bodies, two write paths
        # TWO BODIES NEVER SHARE A WRITE PATH: a foreign live holder on A's dir refuses a second body.
        with open(str(store_a.file_path) + ".lock", "w") as fh:
            fh.write("1")                                             # pid 1, foreign and alive
        with self.assertRaises(RuntimeError) as cm:
            EventStore(str(store_a.file_path), lock=True)             # a second body on A's path
        self.assertIn("one writer per data dir", str(cm.exception))
        os.remove(str(store_a.file_path) + ".lock")


# =============================================================================================
# TEST FOUNDING WORLD for A3 — the handover LAW declared, the ceremony registered, a RECEIVER key
# bound. The test_ep41b HandoverWorld pattern, REUSED (erasure.py is READ and demonstrated here,
# NOT re-authored); production founding-pack.json is untouched (the production flip is MOVER 4's).
# =============================================================================================

RECEIVER = "the-receiving-institution"
RECEIVER_KEY = "testpub:receiving-institution:v1"


class _HandoverWorld(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp(prefix="p14-a3-")
        self.path = os.path.join(self._dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self._dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.path, blobs=self.blobs)
        # declare the handover LAW (a test-world CREATE-RULE, the held founding create's stand-in).
        self.store._append({
            "actor": "SYSTEM", "action": "CREATE-RULE", "object": erasure.HANDOVER_LAW,
            "rule_cited": "BOOT-INT",
            "payload": {"kind": "rule", "rule_id": erasure.HANDOVER_LAW, "root": True, "polarity": "+",
                        "text": "handover: custody of content-addressed blob bytes is transferred to a "
                                "receiving hand under a signed received-custody receipt, the local "
                                "bytes are then removed, and a departure record stands; no delete"}})
        self.assertTrue(erasure.register_ceremony(self.gate, self.views))
        # bind the RECEIVER's verification key (EP-36 stand-in) so its receipt can verify.
        self.store._append({
            "actor": "SYSTEM", "action": "KEY-BIND", "object": RECEIVER, "rule_cited": "BOOT-INT",
            "payload": {"kind": keys.KEY_BIND, keys.ACCOUNT: RECEIVER, keys.PUBLIC_KEY: RECEIVER_KEY,
                        keys.CLASS: "LAW"}})
        self.assertEqual(keys.bound_key(self.store, RECEIVER), RECEIVER_KEY)

    def _write_file(self, path, content):
        h = self.blobs.put(content)
        self.store._append({"actor": "owner", "action": "FILE-CREATE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "node_type": "file", "perm": "644"}})
        self.store._append({"actor": "owner", "action": "FILE-WRITE", "object": path,
                            "rule_cited": "ROOT-NEG-5",
                            "payload": {"path": path, "content_hash": h, "length": len(content)}})
        return h

    def _signed_receipt(self, chain_copy_hash, rule="RET-GDPR-1"):
        body = {"action": erasure.RECEIVED_CUSTODY, "object": chain_copy_hash,
                "target": None, "payload": {"rule": rule}}
        receipt = dict(body)
        receipt["actor"] = RECEIVER
        receipt[erasure.INVOKER_SIG] = make_invoker_sig(RECEIVER_KEY, body)
        return receipt

    def _handover(self, target, rule="RET-GDPR-1", receipt="__auto__"):
        if receipt == "__auto__":
            receipt = self._signed_receipt(target, rule)
        params = {"target_hash": target, "receiver": RECEIVER, "retention_rule": rule}
        if receipt is not None:
            params["receipt"] = receipt
        return self.gate.execute(erasure.HANDOVER_OP, "owner", params)


# =============================================================================================
# A3 — HANDOVER, NEVER MERGE-BY-COPY, NO DELETE (B11, I14).
# =============================================================================================

class A3HandoverCeremony(_HandoverWorld):

    def test_a3_the_ceremony_runs_end_to_end_and_stands_a_departure_record(self):
        """B11: consolidation is the handover ceremony — duplicate, byte-verify, a signed receipt,
        remove the local bytes, a departure record stands (the shells remain). Never a merge-by-copy."""
        h = self._write_file("/inst-A/ledger", b"the record whose custody departs to another hand")
        n_records_before = len(self.store.all())
        self.assertTrue(self.blobs.has(h))
        self._handover(h)
        # the local bytes departed (removed only AFTER the verified receipt).
        self.assertFalse(self.blobs.has(h))
        self.assertIn(h, erasure.departed_hashes(self.store.all()))
        # the shells STAND: no record was removed — the record grew by the departure row, never shrank.
        self.assertGreater(len(self.store.all()), n_records_before)
        # the departure LEDGER names what / to whom / under which rule / receipt cited.
        ledger = erasure.departure_ledger(self.store.all())
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0][erasure.TARGET_HASH], h)
        self.assertEqual(ledger[0][erasure.RECEIVER], RECEIVER)
        self.assertEqual(ledger[0][erasure.RETENTION_RULE], "RET-GDPR-1")
        self.assertIsNotNone(ledger[0][erasure.RECEIPT_CITED])

    def test_a3_no_receipt_no_removal_custody_stays(self):
        """RECEIPT GATES REMOVAL (able-to-fail): a ceremony with no valid receipt removes NOTHING —
        the bytes stay, no departure record is written, custody stays here."""
        h = self._write_file("/inst-A/keep", b"content the ceremony must not remove without a receipt")
        with self.assertRaises(OpError):
            self._handover(h, receipt=None)
        self.assertTrue(self.blobs.has(h))                           # nothing removed
        self.assertEqual(erasure.departed_hashes(self.store.all()), set())

    def test_a3_the_census_finds_no_delete_and_no_merge_by_copy_op(self):
        """I14: over the composed registry (the handover ceremony registered) the census finds NO
        standalone-delete op and NO merge-by-copy op — consolidation is the handover ceremony alone,
        and the ONE removal op reads as the handover, deferred."""
        _store, gate, views = build_full_kernel_for_census()
        rows = pen_census.census(gate, views)
        self.assertEqual(pen_census.standalone_delete_rows(rows), [],
                         "an op removes bytes outside the handover ceremony (there is no delete, L14)")
        self.assertEqual(pen_census.merge_by_copy_rows(rows), [],
                         "an op declares a merge-by-copy consolidation (consolidation is handover only)")
        self.assertEqual(pen_census.unknown_conservation_rows(rows), [])
        handover = [r for r in rows if r["conservation"] == "handover"]
        self.assertEqual([r["op"] for r in handover], [erasure.HANDOVER_OP])

    def test_a3_the_census_reds_a_planted_standalone_delete_op(self):
        """A CHECK THAT CANNOT FAIL IS NOT A CHECK: a planted op that removes bytes outside the
        ceremony reds the no-delete arm (it is NEVER executed — the census reads source only)."""
        _store, gate, views = build_full_kernel_for_census()
        gate.register("PLANTED-DELETE",
                      {"description": "planted", "params": {"path": "required"}},
                      _standalone_delete_handler)
        rows = pen_census.census(gate, views)
        self.assertEqual([r["op"] for r in pen_census.standalone_delete_rows(rows)], ["PLANTED-DELETE"])

    def test_a3_the_census_reds_a_planted_merge_by_copy_op(self):
        """A CHECK THAT CANNOT FAIL IS NOT A CHECK: a planted op whose name declares a merge
        consolidation reds the merge-by-copy arm."""
        _store, gate, views = build_full_kernel_for_census()
        gate.register("MERGE-RECORDS", {"description": "planted", "params": {}}, _benign_handler)
        rows = pen_census.census(gate, views)
        self.assertEqual([r["op"] for r in pen_census.merge_by_copy_rows(rows)], ["MERGE-RECORDS"])


if __name__ == "__main__":
    unittest.main()
