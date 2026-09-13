"""Operations as definition records (design/27 §3, build step three) — T-OP-AMENDMENT:
an op enters by record, runs through one generic interpreter, refuses per its checks,
survives a rebuild (registry = derived state), and retires back to not-existing.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402

# The proving op: send instruction information through a registered tunnel — the
# constitution's OWNER-TUNNEL do made operational, entirely from data.
TUNNEL_SEND = {
    "description": "send instruction information through a registered tunnel",
    "params": {"tunnel": "required", "message": "required"},
    "law_cited": "OWNER-TUNNEL",
    "object_param": "tunnel",
    # VOCAB DOOR (design/46 member 2): both fields inline in this proving op. `tunnel` is the object
    # id. `message` is STRUCTURAL here — not by name-mirror (production's COMMS enqueue content-homes
    # a `message`) but by this op's own construction: it is defined, registered, executed and
    # round-tripped INLINE in a bare kernel (build_kernel, no blob store), and a content-addressed op
    # is unregisterable in a bare kernel (test_ep05c bare-kernel BOOT-INT). The op's hosting context
    # forbids CONTENT, so the honest classification for this synthetic scalar carrier is structural.
    "structural_params": ["tunnel", "message"],
    "checks": [{"check": "require_prior", "action": "CREATE-TUNNEL", "field": "name",
                "param": "tunnel", "cite": "ROOT-NEG-1",
                "message": "no such tunnel — an unregistered path carries nothing"}],
}


class TestOpDefinitions(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def _define(self):
        return self.gate.execute("CREATE-OP", "owner", {"name": "TUNNEL-SEND", "definition": TUNNEL_SEND})

    def test_define_and_execute_end_to_end(self):
        self._define()
        rec = self.gate.execute("TUNNEL-SEND", "owner", {"tunnel": "owner-tunnel", "message": "hello"})
        self.assertEqual(rec["action"], "TUNNEL-SEND")
        self.assertEqual(rec["rule_cited"], "OWNER-TUNNEL")          # decisions cite the law
        self.assertEqual(rec["payload"]["message"], "hello")
        self.assertIn("op:TUNNEL-SEND", self.views.active_rules())  # the definition IS law
        self.assertIn("TUNNEL-SEND", self.views.op_definitions())   # the registry as a view

    def test_check_refuses_and_records(self):
        self._define()
        before = len(self.store.by_action("TUNNEL-SEND"))
        with self.assertRaises(OpError) as cm:
            self.gate.execute("TUNNEL-SEND", "owner", {"tunnel": "ghost", "message": "x"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-1")
        self.assertEqual(len(self.store.by_action("op-refused")), 1)  # the no is a record
        self.assertEqual(len(self.store.by_action("TUNNEL-SEND")), before)  # no decision

    def test_missing_param_refused_before_interpreter(self):
        self._define()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("TUNNEL-SEND", "owner", {"tunnel": "owner-tunnel"})
        self.assertEqual(cm.exception.rule, "AR-2")                  # nonconforming call

    def test_registry_reconstructs_from_the_record(self):
        # THE round-trip, extended to the kernel's own surface: rebuild everything from
        # the record file alone; the definition-born op comes back registered.
        self._define()
        store2, gate2, views2 = build_kernel(self.path)
        rec = gate2.execute("TUNNEL-SEND", "owner", {"tunnel": "owner-tunnel", "message": "again"})
        self.assertEqual(rec["rule_cited"], "OWNER-TUNNEL")

    def test_retire_reverts_to_not_existing(self):
        self._define()
        self.gate.execute("RETIRE-OP", "owner", {"name": "TUNNEL-SEND"})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("TUNNEL-SEND", "owner", {"tunnel": "owner-tunnel", "message": "x"})
        self.assertEqual(cm.exception.rule, "P3-CLOSURE")            # Closure Hit again
        self.assertNotIn("TUNNEL-SEND", self.views.op_definitions())
        store2, gate2, _ = build_kernel(self.path)                   # and it stays retired on rebuild
        with self.assertRaises(OpError):
            gate2.execute("TUNNEL-SEND", "owner", {"tunnel": "owner-tunnel", "message": "x"})

    def test_failed_commit_leaves_no_phantom_op(self):
        # Registry<->record atomicity (design 28 §I3): the registry is derived state and
        # may never get ahead of the record. If the gate's write faults mid-CREATE-OP, the
        # op must NOT be live — no phantom that is callable in-process yet backed by no
        # record (and would vanish on rebuild). The record is the sole trigger for
        # registration, so a fault before commit leaves both record and registry untouched.
        def _boom(ev):
            raise RuntimeError("injected commit fault")
        # BOTH PRIVATE ROUTES, not one [DOCUMENTED FLIP, EP-28G, 2026-08-03, mapped to the
        # publish/await split]. The gate's write moved from `_append` to `_publish` — the
        # region must cover publication and must not cover the durability wait — so an
        # injection at `_append` alone stopped reaching the gate and this row went from
        # exercising a fault to exercising nothing. Faulting BOTH keeps the row's subject
        # (a fault at the gate's write leaves no phantom) independent of which route the
        # gate takes, and reds rather than passes if a third route is ever added.
        self.store._append = _boom
        self.store._publish = _boom
        with self.assertRaises(RuntimeError):
            self.gate.execute("CREATE-OP", "owner", {"name": "GHOST", "definition": TUNNEL_SEND})
        self.assertFalse(self.gate.has("GHOST"))                    # no phantom in the live registry
        self.assertNotIn("GHOST", self.views.op_definitions())      # and nothing recorded

    def test_unknown_check_kind_refused_at_definition(self):
        bad = dict(TUNNEL_SEND, checks=[{"check": "vibes"}])
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-OP", "owner", {"name": "X", "definition": bad})
        self.assertEqual(cm.exception.rule, "AR-2")
        self.assertFalse(self.gate.has("X"))                         # nothing registered

    def test_cannot_shadow_a_builtin(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-OP", "owner", {"name": "CREATE-RULE", "definition": TUNNEL_SEND})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-6")

    def test_cannot_retire_a_boot_op(self):
        # CREATE-ACTOR is still a code-registered boot op (not definition-born), so it cannot be
        # retired by amendment. (CREATE-RULE became data-born in EP-05 Phase B — it is now an
        # owner-tier op the owner may retire, so it is no longer the example here.)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RETIRE-OP", "owner", {"name": "CREATE-ACTOR"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_op_without_law_is_unrecordable(self):
        lawless = {k: v for k, v in TUNNEL_SEND.items() if k != "law_cited"}
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-OP", "owner", {"name": "LAWLESS", "definition": lawless})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-5")

    def test_sight_check_binds_action(self):
        # sight in the vocabulary: an actor may not act on what it could not read
        consume = {"description": "act on cited material",
                   "params": {"target": "required"}, "law_cited": "SIGHT-IS-LAW",
                   "object_param": "target", "structural_params": ["target"],   # object id, inline (vocab door)
                   "checks": [{"check": "sight", "target_param": "target"}]}
        self.gate.execute("CREATE-OP", "owner", {"name": "CONSUME-INFO", "definition": consume})
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CONSUME-INFO", "alice", {"target": "/secret"})
        self.assertEqual(cm.exception.rule, "SIGHT-IS-LAW")
        self.store._append({"actor": "owner", "action": "GRANT-READ", "object": "/secret",
                           "target": "alice", "rule_cited": "SIGHT-IS-LAW",
                           "payload": {"grantee": "alice", "target": "/secret"}})
        rec = self.gate.execute("CONSUME-INFO", "alice", {"target": "/secret"})
        self.assertEqual(rec["action"], "CONSUME-INFO")


if __name__ == "__main__":
    unittest.main()
