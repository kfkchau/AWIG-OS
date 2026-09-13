# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (handler, effect, gate decision, blob hand_off, deferred thunk). NON-GOAL: no
# offensive capability of any kind — every assertion proves the CORRECT ordering by function: a
# refused act leaves no irreversible effect, and the census REDS on a handler that would break
# that. Full declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I1 [HIGH] — THE EFFECT-ORDER CENSUS.

Three proofs, one instrument:

  A1a  COMPLETENESS — every registered handler is classified, and the census's reading of the
       live registry MATCHES the committed evidence table. A founding mover that adds a byte/world
       handler adds a row or REDS this (the standing guard, archi P4).
  A1b  DECISION-FIRST (behavioural) — the one byte/world irreversible handler on the host
       (HANDOVER-CUSTODY) is driven to a gate refusal; its bytes REMAIN. A refused act leaves no
       effect, so the effect fired AFTER the decision — B1 proven live, not asserted.
  A1c  PLANTED POSITIVE (must fire) — a handler whose irreversible effect is INLINE (before the
       decision) is (i) flagged by the classifier's own reading and (ii) shown to remove the bytes
       DESPITE a gate refusal. The census can fail; it is an instrument.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
_TOOLS = os.path.join(os.path.dirname(__file__), "..", "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kernel.boot import build_kernel                                   # noqa: E402
from kernel.blobs import BlobStore                                     # noqa: E402
from kernel import erasure, keys                                       # noqa: E402
from kernel.gate import make_invoker_sig, IRREVERSIBLE_EFFECT          # noqa: E402
from kernel.errors import OpError                                      # noqa: E402

from tools.conformance import effect_order_census as I1                # noqa: E402


RECEIVER = "the-receiving-archive"
RECEIVER_KEY = "testpub:receiving-archive:v1"


# ============================================================================================
# A1a — COMPLETENESS: the live registry's census matches the committed evidence table.
# ============================================================================================

class TestA1aCensusMatchesEvidence(unittest.TestCase):

    def test_every_handler_is_classified_no_unknown_byte_world(self):
        _s, gate, _v = I1.build_full_kernel_for_census()
        rows = I1.census(gate)
        # no handler's source failed to read in a way that could hide a byte/world call
        unknown = [r["op"] for r in rows if r["touches"] == "unknown"]
        self.assertEqual(unknown, [], "a handler's source could not be classified: %s" % unknown)
        # the census is over the WHOLE registry (completeness = enumeration, P3)
        self.assertEqual(len(rows), len(gate.ops))

    def test_census_reading_matches_committed_evidence(self):
        # THE STANDING GUARD (archi P4): regenerate the table and compare byte-for-byte to the
        # committed evidence. A new byte/world handler, or a changed effect site, moves this table
        # and REDS here until the evidence is regenerated — "adds a row or reds the census".
        _s, gate, _v = I1.build_full_kernel_for_census()
        rows = I1.census(gate)
        generated = I1.render_markdown(rows)
        with open(I1.EVIDENCE_PATH, encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(
            generated.strip(), committed.strip(),
            "the effect-order census reading diverged from the committed evidence table — a "
            "handler was added/changed. Regenerate: python3 -m tools.conformance.effect_order_census --md")

    def test_no_inline_irreversible_handler_exists(self):
        # the load-bearing invariant: not one byte/world handler removes a byte inline.
        _s, gate, _v = I1.build_full_kernel_for_census()
        rows = I1.census(gate)
        offenders = I1.inline_irreversible_rows(rows)
        self.assertEqual(offenders, [], "a handler removes a byte INLINE (before the gate's "
                                        "decision) — B1 violated: %s" % [r["op"] for r in offenders])

    def test_the_one_byte_world_handler_is_handover_deferred(self):
        # the host reading the census PRODUCES (not assumes): exactly one byte/world handler, the
        # handover ceremony, and its effect is deferred past the decision.
        _s, gate, _v = I1.build_full_kernel_for_census()
        bw = I1.byte_world_rows(I1.census(gate))
        self.assertEqual([r["op"] for r in bw], ["HANDOVER-CUSTODY"])
        self.assertEqual(bw[0]["effect_site"], "deferred")
        self.assertIn("hand_off", bw[0]["primitives"])


# ============================================================================================
# The handover world (modelled on tests/test_maint_outside_1._HandoverWorld) for A1b / A1c.
# ============================================================================================

class _HandoverWorld(unittest.TestCase):

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self._dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.path, blobs=self.blobs)
        self._declare_handover_law()
        self.assertTrue(erasure.register_ceremony(self.gate, self.views))
        self._bind_key(RECEIVER, RECEIVER_KEY)

    def _declare_handover_law(self):
        self.store._append({
            "actor": "SYSTEM", "action": "CREATE-RULE", "object": erasure.HANDOVER_LAW,
            "rule_cited": "BOOT-INT",
            "payload": {"kind": "rule", "rule_id": erasure.HANDOVER_LAW, "root": True,
                        "polarity": "+", "text": "handover law (test world)"}})

    def _bind_key(self, account, public_key):
        self.store._append({
            "actor": "SYSTEM", "action": "KEY-BIND", "object": account, "rule_cited": "BOOT-INT",
            "payload": {"kind": keys.KEY_BIND, keys.ACCOUNT: account, keys.PUBLIC_KEY: public_key,
                        keys.CLASS: "LAW"}})

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

    def _refuse_handover_at_the_gate(self, op=erasure.HANDOVER_OP):
        self.store._append({
            "actor": "SYSTEM", "action": "CREATE-RULE", "object": "NO-HANDOVER-STANDING",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "NO-HANDOVER-STANDING", "polarity": "-",
                        "when": [{"action": op}],
                        "then": [{"refuse": "NO-HANDOVER-STANDING"}]}})


# ============================================================================================
# A1b — DECISION-FIRST, proven behaviourally on the real handover handler.
# ============================================================================================

class TestA1bDecisionFirst(_HandoverWorld):

    def test_refused_handover_leaves_the_bytes(self):
        h = self._write_file("/f", b"content a standing rule will refuse the handover of")
        self._refuse_handover_at_the_gate()
        with self.assertRaises(OpError) as cm:
            self.gate.execute(erasure.HANDOVER_OP, "owner",
                              {"target_hash": h, "receiver": RECEIVER, "retention_rule": "RET-GDPR-1",
                               "receipt": self._signed_receipt(h)})
        self.assertEqual(cm.exception.rule, "NO-HANDOVER-STANDING")
        self.assertTrue(self.blobs.has(h),
                        "a refused handover left the bytes REMOVED — the irreversible effect ran "
                        "before the gate's decision (B1 violated)")
        self.assertEqual(erasure.departed_hashes(self.store.all()), set())


# ============================================================================================
# A1c — PLANTED POSITIVE: an INLINE-irreversible handler is (i) flagged by the classifier and
# (ii) shown to remove the bytes despite a gate refusal. The census can fail.
# ============================================================================================

INLINE_BAD_SOURCE = '''\
def _bad_handler(actor, params):
    # the SAME hand_off, but run INLINE (before returning the draft) instead of deferred as a
    # thunk. This is exactly the pre-B1 shape the census exists to catch.
    blobs.hand_off([params["target_hash"]], params["receipt"])
    return {"actor": actor, "action": "HANDOVER-INLINE-BAD", "object": params["target_hash"],
            "rule_cited": "HANDOVER-LAW"}
'''


class TestA1cPlantedPositiveStatic(unittest.TestCase):

    def test_classifier_flags_inline_irreversible(self):
        c = I1.classify_source(INLINE_BAD_SOURCE)
        self.assertEqual(c["touches"], "bytes/world")
        self.assertTrue(c["irreversible"])
        self.assertEqual(c["effect_site"], "inline",
                         "the classifier read an INLINE hand_off as deferred — the census cannot fail")

    def test_classifier_passes_the_real_deferred_handover(self):
        # the control the other way: the real handler's source classifies as DEFERRED, so the
        # planted positive is discriminating, not a check that reds on everything.
        import inspect
        src = inspect.getsource(erasure.handover_handler)
        c = I1.classify_source(src)
        self.assertEqual(c["effect_site"], "deferred")


class TestA1cPlantedPositiveBehavioural(_HandoverWorld):

    def _register_inline_bad_op(self):
        """Register a byte/world op whose irreversible effect is INLINE — the exact violation the
        census exists to catch. Its handler removes the bytes in its body, before returning a
        draft, so the gate's decide passes never get to refuse first."""
        blobs = self.blobs

        def bad_handler(actor, params):
            blobs.hand_off([params["target_hash"]], params["receipt"])          # INLINE effect
            return {"actor": actor, "action": "HANDOVER-INLINE-BAD",
                    "object": params["target_hash"], "rule_cited": erasure.HANDOVER_LAW}
        self.gate.register("HANDOVER-INLINE-BAD",
                           {"description": "planted inline-irreversible handler",
                            "rules": [erasure.HANDOVER_LAW],
                            "params": {"target_hash": "required", "receipt": "required"}},
                           bad_handler)

    def test_inline_effect_fires_despite_refusal(self):
        # THE POSITIVE FIRES: a standing rule refuses the op at the gate, yet the bytes are GONE —
        # the inline effect ran before the decision. This is the defect a census that could not
        # fail would miss.
        self._register_inline_bad_op()
        h = self._write_file("/f", b"bytes an inline handler removes before the gate can refuse")
        self._refuse_handover_at_the_gate(op="HANDOVER-INLINE-BAD")
        with self.assertRaises(OpError):
            self.gate.execute("HANDOVER-INLINE-BAD", "owner",
                              {"target_hash": h, "receipt": self._signed_receipt(h)})
        self.assertFalse(
            self.blobs.has(h),
            "the inline handler did NOT remove the bytes — the planted positive did not fire, so "
            "this test proves nothing")


if __name__ == "__main__":
    unittest.main()
