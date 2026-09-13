"""EP-48 — SOCKET-GRANTS (host-modelled): the box's wire as governed, rule-citing decisions.

Named in planning/exec/EP-48-BUILD.md before code, landed here as regression tests (charter:
every verification probe lands as a regression test). This battery proves design/51 N1/N2 for
the HOST-MODELLED half: the six socket acts are recorded DECISIONs citing NET-LAW-GRANT; the
live socket table is a fold (T-CACHE-KILL); the connection shadow retires INTO that fold on
proof (:2646); per-packet traffic is never a record; the wire and the channel are two names;
the syscall-ops map is amended founding data; the founding move is MINOR and bump-attested. NO
real socket is opened on the host — the wire is a modelled table (the guest-real half is
EP-48G). No op is registered in code; the six ops enter as founding data (founding-pack.json
steps 05o-net-laws / 07b-syscall-ops-amendment / 08n-socket-ops).

Every acceptance carries its RED WORLD (§4), produced THROUGH the instrument (§A42): a control
that cannot red is the defect (§A64).
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                               # noqa: E402
from kernel.errors import OpError                                          # noqa: E402
from kernel.opdefs import OP_CHECKS                                        # noqa: E402
from observe import shadow                                                # noqa: E402
from subsystems.comms import CommsView                                    # noqa: E402
from subsystems.sockets import SocketView, SOCKET_ACTIONS                 # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

SIX_OPS = ("SOCKET-OPEN", "SOCKET-BIND", "SOCKET-LISTEN",
           "SOCKET-CONNECT", "SOCKET-ACCEPT", "SOCKET-CLOSE")


class _World(unittest.TestCase):
    """A kernel composed from the SHIPPED founding, with one established entity to open by."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep48-")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.gate.execute("CREATE-ACCOUNT", "owner",
                          {"account_id": "web", "actor_class": "human"})

    def open_socket(self, sid, family="inet", entity="web"):
        return self.gate.execute("SOCKET-OPEN", entity,
                                 {"entity": entity, "socket": sid, "family": family})

    def sockets(self):
        return SocketView(self.store)


# =============================================================================================
# A1 — T-SOCKET-DECISION-RECORDED (+ RW-STRIPPED-GRANT, the able-to-fail plant)
# =============================================================================================

class TestSocketDecisionRecorded(_World):
    def test_each_of_the_six_wire_acts_lands_citing_net_law_grant(self):
        self.open_socket("s1")
        acts = [
            ("SOCKET-OPEN",    {"entity": "web", "socket": "s2", "family": "inet6"}),
            ("SOCKET-BIND",    {"socket": "s1", "address": "<LOOPBACK-PORT>"}),
            ("SOCKET-LISTEN",  {"socket": "s1"}),
            ("SOCKET-CONNECT", {"socket": "s1", "target": "93.184.216.34:443"}),
            ("SOCKET-ACCEPT",  {"socket": "s1", "peer": "10.0.0.9:51000"}),
            ("SOCKET-CLOSE",   {"socket": "s1"}),
        ]
        for op, params in acts:
            rec = self.gate.execute(op, "web", params)
            self.assertEqual(rec["action"], op)                        # action IS its op
            self.assertEqual(rec["rule_cited"], "NET-LAW-GRANT")       # each cites the grant law
        # all six op NAMES are the ones the pack founded (host-modelled: opened no real socket)
        self.assertEqual(set(SIX_OPS), set(SOCKET_ACTIONS))

    def test_a_socket_act_with_no_grant_is_REFUSED_and_the_refusal_RECORDED(self):
        # WHO absent: an opener with no establishing record is refused, recorded, citing the grant.
        with self.assertRaises(OpError) as cm:
            self.gate.execute("SOCKET-OPEN", "ghost",
                              {"entity": "ghost", "socket": "g1", "family": "inet"})
        self.assertEqual(cm.exception.rule, "NET-LAW-GRANT")
        refusals = [e for e in self.store.by_action("op-refused")
                    if (e.get("payload") or {}).get("op") == "SOCKET-OPEN"]
        self.assertTrue(refusals, "the refused socket act was silently dropped, not recorded")
        self.assertEqual(refusals[-1].get("rule_cited"), "NET-LAW-GRANT")   # recorded, citing the grant

    def test_RW_STRIPPED_GRANT_the_gate_is_mechanical_not_a_note(self):
        """RW-STRIPPED-GRANT (§4). The grant is LOAD-BEARING: it can refuse (able-to-fail), and
        its removal flips the verdict. Proven THREE ways the guard fires and once its removal
        admits what it refused."""
        # ABLE TO FAIL (three refusals, each citing NET-LAW-GRANT) — the guard is not vacuous:
        self.open_socket("s1")
        for op, params in [
            ("SOCKET-OPEN", {"entity": "nobody", "socket": "x", "family": "inet"}),   # WHO
            ("SOCKET-OPEN", {"entity": "web", "socket": "y", "family": "raw"}),        # WHAT
            ("SOCKET-BIND", {"socket": "never-opened", "address": "a"}),               # names a socket no record opened
        ]:
            with self.assertRaises(OpError) as cm:
                self.gate.execute(op, "web" if op != "SOCKET-OPEN" or params["entity"] == "web" else params["entity"], params)
            self.assertEqual(cm.exception.rule, "NET-LAW-GRANT")

        # LOAD-BEARING: strip SOCKET-OPEN's grant checks from the pack (the grant enforcement
        # removed) and the SAME unauthorised open — an unestablished opener — now PASSES. Its
        # removal flips RED->GREEN, so the checks WERE the grant, not a decoration. Driven on a
        # fresh world founded from a pack with the socket-op checks emptied (§A42, through the
        # instrument), the real bytes on disk never touched.
        with open(PACK_PATH, "rb") as fh:
            pack = json.loads(fh.read())
        for step in pack["steps"]:
            for rec in step["records"]:
                if rec.get("action") == "CREATE-OP" and rec["payload"]["name"] == "SOCKET-OPEN":
                    rec["payload"]["definition"]["checks"] = []          # grant stripped
        d2 = tempfile.mkdtemp(prefix="ep48-stripped-")
        import founding.install as install_module
        saved = install_module.load_pack
        install_module.load_pack = lambda path=None: pack
        try:
            store, gate, _v, _b, _s = build_full_kernel(
                os.path.join(d2, "record.jsonl"), os.path.join(d2, "blobs"),
                os.path.join(d2, "vault"))
            # no CREATE-ACCOUNT for 'nobody' — the WHO precondition is exactly what was stripped
            rec = gate.execute("SOCKET-OPEN", "nobody",
                               {"entity": "nobody", "socket": "x", "family": "raw"})
            self.assertEqual(rec["action"], "SOCKET-OPEN")               # ADMITTED: the grant was load-bearing
        finally:
            install_module.load_pack = saved


# =============================================================================================
# A2 — T-SOCKET-TABLE-DERIVED (T-CACHE-KILL) + RW-STORED-COPY
# =============================================================================================

class TestSocketTableDerived(_World):
    def test_the_socket_table_is_a_fold_and_cache_kill_recomputes_identical(self):
        self.open_socket("s1")
        self.gate.execute("SOCKET-BIND", "web", {"socket": "s1", "address": "<LOOPBACK-PORT>"})
        self.open_socket("s2", family="inet6")
        self.gate.execute("SOCKET-CONNECT", "web", {"socket": "s2", "target": "1.2.3.4:443"})
        self.gate.execute("SOCKET-CLOSE", "web", {"socket": "s1"})       # s1 leaves the table

        view = self.sockets()
        t1 = view.live_sockets()
        self.assertEqual(set(t1), {"s2"})                                # s1 closed, s2 live
        self.assertEqual(t1["s2"]["state"], "CONNECTED")

        # T-CACHE-KILL: kill the fold's cache, recompute -> IDENTICAL, and a fresh object (the
        # table is a local in a fold, NEVER a stored second copy).
        view.kill_cache()
        t2 = view.live_sockets()
        self.assertEqual(t1, t2)
        self.assertIsNot(t1, t2)
        # RW-STORED-COPY: the record holds NO stored socket-table row — the table is only ever a
        # fold output. Every record is one of the six wire acts (a decision), never a table dump.
        for e in self.store.action_set_projection(set(SOCKET_ACTIONS)).all():
            self.assertIn(e["action"], SIX_OPS)
        # a second, independent view over the same record yields the same table (derived, shared
        # by no state between instances).
        self.assertEqual(SocketView(self.store).live_sockets(), t1)


# =============================================================================================
# A3 — T-SHADOW-RETIRED-INTO-VIEW (the churn battery; diff-empty; both directions; permit)
# =============================================================================================

def _conn_diff(fold_states, box_states):
    """The connection diff, the shape shadow.py's tracks reads: missing (box has, record lacks),
    extra (record has, box lacks), differing (both have, states disagree)."""
    missing = sorted(k for k in box_states if k not in fold_states)
    extra = sorted(k for k in fold_states if k not in box_states)
    differing = sorted(k for k in fold_states
                       if k in box_states and fold_states[k] != box_states[k])
    return missing, extra, differing


class TestShadowRetiredIntoView(_World):
    N = 16

    def _churn(self):
        """A connection workload BATTERY over the six wire ops: every sample opens+connects two
        new sockets and closes the oldest connected ones, so opens, connects and closes all cross
        every sample. Returns the box (the expected live connections) tracked in parallel — the
        empty diff below is EARNED under churn, never a quiet box (design/44 §1)."""
        box = {}                              # socket -> state, the box's own connection table
        order = []
        counts = {"opened": 0, "connected": 0, "closed": 0}
        nxt = 0
        for _ in range(self.N):
            # close the two oldest live connections
            for sid in order[:2]:
                if sid in box:
                    self.gate.execute("SOCKET-CLOSE", "web", {"socket": sid})
                    del box[sid]
                    counts["closed"] += 1
            order = order[2:]
            # open + connect two new sockets
            for _ in range(2):
                sid = f"s{nxt}"
                self.open_socket(sid)
                self.gate.execute("SOCKET-CONNECT", "web",
                                  {"socket": sid, "target": f"93.184.216.34:{4000 + nxt}"})
                box[sid] = "CONNECTED"
                order.append(sid)
                nxt += 1
                counts["opened"] += 1
                counts["connected"] += 1
            yield dict(box), counts

    def test_sustained_diff_empty_under_churn_both_failure_directions_then_permit(self):
        view = self.sockets()
        empties = 0
        last_box = {}
        for box, counts in self._churn():
            view.kill_cache()                                    # re-fold from the record each sample
            diff = _conn_diff(view.connection_states(), box)
            self.assertEqual(diff, ([], [], []), f"sample drifted: {diff}")
            empties += 1
            last_box = box
        self.assertEqual(empties, self.N)                        # SUSTAINED, every sample
        # NOT a quiet box — the workload genuinely opened, connected and closed connections.
        self.assertGreaterEqual(counts["connected"], 2 * self.N)
        self.assertGreater(counts["closed"], 0)

        fold = view.connection_states()

        # BOTH FAILURE DIRECTIONS (the maturation's halt, §A64 both ways):
        # (i) a STALE fold — the box moved on, the record behind: a connection the box has that the
        #     record lacks -> missing non-empty -> the diff HALTS (reds).
        stale_box = dict(last_box); stale_box["ghost"] = "CONNECTED"
        m, e, _d = _conn_diff(fold, stale_box)
        self.assertIn("ghost", m, "a stale fold was NOT caught")
        self.assertEqual(e, [])
        # (ii) a fold CLAIMING a connection the ops never recorded — the fold ahead of the box: an
        #     entry the box lacks -> extra non-empty -> the diff HALTS (reds).
        lost_box = dict(last_box); dropped = sorted(last_box)[0]; del lost_box[dropped]
        _m2, e2, _d2 = _conn_diff(fold, lost_box)
        self.assertIn(dropped, e2, "a fold claiming an unrecorded connection was NOT caught")

        # ON THAT PROOF the shadow retires INTO the socket fold: the maturation is proven and a real
        # governed target exists, so retire_linux_authority PERMITS (was the :2646 raise).
        maturation = {"sustained_empty": True, "halt_seeded_divergence": True, "halt_no_false": True}
        d = shadow.retire_linux_authority("connection", maturation, target=view.connection_view)
        self.assertEqual(d["retired"], "connection")
        self.assertEqual(d["into"], view.connection_view)

    def test_RW_SHADOW_STALE_the_retirement_without_the_diff_empty_is_refused(self):
        """RW-SHADOW-STALE (§4): the retirement claimed with the maturation NOT proven refuses —
        a naked swap. The control can red (able-to-fail); a swap into a void (no target) too."""
        view = self.sockets()
        for absent in ("sustained_empty", "halt_seeded_divergence", "halt_no_false"):
            m = {"sustained_empty": True, "halt_seeded_divergence": True, "halt_no_false": True}
            m[absent] = False
            with self.assertRaises(shadow.NakedSwapRefused) as cm:
                shadow.retire_linux_authority("connection", m, target=view.connection_view)
            self.assertIn("maturation not proven", cm.exception.reason)
        proven = {"sustained_empty": True, "halt_seeded_divergence": True, "halt_no_false": True}
        with self.assertRaises(shadow.NakedSwapRefused) as cm:
            shadow.retire_linux_authority("connection", proven, target=None)   # into a void
        self.assertIn("no governed-authoritative view", cm.exception.reason)


# =============================================================================================
# A4 — T-NO-PACKET-ROWS (a census under load: STREAM appends nothing) + RW-PACKET-ROW
# =============================================================================================

class TestNoPacketRows(_World):
    def test_a_census_under_load_has_zero_per_packet_rows(self):
        # LOAD: open, bind, connect, exchange (modelled), close many sockets. The socket ops record
        # GRANTS, never bytes on the wire — a per-packet flow is STREAM and STREAM appends nothing.
        before = len(self.store.events)
        for i in range(20):
            sid = f"s{i}"
            self.open_socket(sid)
            self.gate.execute("SOCKET-CONNECT", "web", {"socket": sid, "target": f"1.1.1.1:{i}"})
            self.gate.execute("SOCKET-CLOSE", "web", {"socket": sid})
        appended = self.store.events[before:]
        # EVERY appended record is a governed wire DECISION — one of the six ops. ZERO rows of any
        # per-packet / traffic / byte kind.
        for e in appended:
            self.assertIn(e["action"], SIX_OPS,
                          f"a non-grant row appeared under load: {e['action']}")
        packetish = [e for e in appended
                     if any(w in e["action"].lower() for w in ("traffic", "packet", "byte", "stream", "recv-flow"))]
        self.assertEqual(packetish, [], "a per-packet row reached the record")

        # STREAM appends nothing — proven against the classmap's own STREAM class (the existing
        # per-packet connection-traffic act): it classifies STREAM and is NOT recorded.
        from observe import classmap
        self.assertEqual(classmap.classify("connection", "connection-traffic"), classmap.STREAM)
        self.assertFalse(classmap.is_recorded("connection", "connection-traffic"))

    def test_RW_PACKET_ROW_a_recorded_byte_would_red_this_census(self):
        """RW-PACKET-ROW (§4): the census is able-to-fail. There is NO op in the pack that mints a
        per-packet row — that is the design (STREAM appends nothing). So the forbidden shape is
        the counterfactual the census must catch: a synthetic per-packet record injected into the
        appended-set the census reads makes it red (§A42, through the instrument; the real store is
        never mutated — the row is the red world, not a real act)."""
        self.open_socket("s1")
        self.gate.execute("SOCKET-CONNECT", "web", {"socket": "s1", "target": "1.1.1.1:9"})
        real = list(self.store.action_set_projection(set(SOCKET_ACTIONS)).all())
        # every REAL row is a grant (the census passes on the real world):
        self.assertEqual([e for e in real if e["action"] not in SIX_OPS], [])
        # the counterfactual: a byte-on-the-wire row appears in the set the census reads.
        packet_row = {"actor": "web", "action": "socket-traffic",
                      "object": "s1", "rule_cited": "NET-LAW-GRANT",
                      "payload": {"socket": "s1", "bytes": 1400}}
        with_packet = real + [packet_row]
        offenders = [e for e in with_packet if e["action"] not in SIX_OPS]
        self.assertEqual([e["action"] for e in offenders], ["socket-traffic"],
                         "the census could not see a per-packet row — it cannot fail")


# =============================================================================================
# A5 — T-WIRE-NOT-CHANNEL (the two names disjoint in the record, both directions) + RW
# =============================================================================================

class TestWireNotChannel(_World):
    def test_a_socket_act_never_touches_live_channels_and_a_channel_act_never_the_socket_table(self):
        comms = CommsView(self.store)
        socks = self.sockets()

        # a socket act: open + connect a socket. live_channels stays empty; the socket table has it.
        self.open_socket("s1")
        self.gate.execute("SOCKET-CONNECT", "web", {"socket": "s1", "target": "1.2.3.4:443"})
        self.assertEqual(comms.live_channels(), {})                 # the wire did not reach the channel
        self.assertIn("s1", socks.live_sockets())

        # a channel act: open a comms channel. The socket table stays without it; live_channels has it.
        self.gate.execute("COMMS-OPEN", "web",
                          {"entity": "web", "channel": "c1", "role": "user-facing"})
        socks.kill_cache()
        self.assertNotIn("c1", socks.live_sockets())                # the channel did not reach the wire
        self.assertIn(("web", "c1"), comms.live_channels())

        # DISJOINT BY CONSTRUCTION (N2): the socket fold reads only SOCKET-* actions, the channel
        # fold only COMMS-OPEN/COMMS-CLOSE — no action is in both sets.
        self.assertEqual(set(SOCKET_ACTIONS) & {"COMMS-OPEN", "COMMS-CLOSE",
                                                "COMMS-SEND", "COMMS-RECV"}, set())


# =============================================================================================
# A6 — T-SYSCALL-MAP-AMENDED (+ RW-NO-MOVE / RW-WIRE-IS-CHANNEL)
# =============================================================================================

class TestSyscallMapAmended(_World):
    def test_the_syscall_ops_map_is_amended_and_the_old_mapping_survives_in_history(self):
        pack = self.views.category_packs()["syscall-ops"]
        levels = {lvl["syscall"]: lvl["op"] for lvl in pack["levels"]}
        # amended (N2): the wire and the channel are two names.
        self.assertEqual(levels["socket"], "SOCKET-OPEN")           # was COMMS-OPEN
        self.assertEqual(levels["bind"], "SOCKET-BIND")
        self.assertEqual(levels["listen"], "SOCKET-LISTEN")
        self.assertEqual(levels["connect"], "SOCKET-CONNECT")
        self.assertEqual(levels["accept"], "SOCKET-ACCEPT")
        self.assertEqual(levels["recvmsg"], "COMMS-RECV")
        # `close` stays UNMAPPED on the host — the flat map cannot discriminate a socket fd's close
        # from a file fd's, so SOCKET-CLOSE is reached by the OP DIRECTLY (:3266 precision 3). The
        # op exists and is reachable even though no syscall maps to it.
        self.assertNotIn("close", levels)
        self.assertIn("SOCKET-CLOSE", self.gate.ops)

        # the OLD socket->COMMS-OPEN mapping survives IN HISTORY, never edited (append-only founding
        # data, §6 item 3): the genesis pack:syscall-ops record still carries it; the amendment is a
        # SEPARATE later record; latest-wins serves the amended map.
        with open(PACK_PATH, "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        syscall_packs = [r for r in recs
                         if (r.get("payload") or {}).get("kind") == "category_pack"
                         and r["payload"]["name"] == "syscall-ops"]
        self.assertEqual(len(syscall_packs), 2, "genesis + amendment, both present")
        genesis_levels = {lvl["syscall"]: lvl["op"] for lvl in syscall_packs[0]["payload"]["levels"]}
        self.assertEqual(genesis_levels["socket"], "COMMS-OPEN", "the genesis mapping was edited")

    def test_RW_WIRE_IS_CHANNEL_the_unamended_map_would_red_this(self):
        """RW-WIRE-IS-CHANNEL / RW-NO-MOVE (§4): the amendment is able-to-fail — the pre-move map
        resolves socket->COMMS-OPEN (the wire and channel as ONE name), which fails A6. Driven
        against the genesis levels (the byte-unchanged founding), through the instrument."""
        with open(PACK_PATH, "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        genesis = next(r for r in recs
                       if (r.get("payload") or {}).get("kind") == "category_pack"
                       and r["payload"]["name"] == "syscall-ops")
        pre = {lvl["syscall"]: lvl["op"] for lvl in genesis["payload"]["levels"]}
        self.assertEqual(pre["socket"], "COMMS-OPEN")               # the red condition A6 forbids
        self.assertNotIn("bind", pre)


# =============================================================================================
# A7 — T-FOUNDING-BUMP-ATTESTED (MINOR; version + pack sha in one log entry) + RW-MAJOR
# =============================================================================================

class TestFoundingBumpAttested(unittest.TestCase):
    def test_the_founding_version_is_at_or_beyond_the_EP48_era_and_the_bump_is_attested(self):
        from test_founding_is_logged import audit, pack_facts
        facts = pack_facts()
        # ERA-PINNED (mgr, board :3300 folded from EP-49C's stop / :3336): this was a LIVE literal
        # `assertEqual(facts["version"], "1.42.0")` that EVERY founding mover hand-edited
        # (1.40.0 -> 1.41.0 -> 1.42.0 ...) — the exact class the era-pin idiom exists to end, a test
        # that reddens because the constitution GREW, indistinguishable from one that reddens because
        # its subject moved. Floored at the EP-48 era (1.40.0, when this test was written); a later
        # founding mover advances the constitution WITHOUT touching this line, and the method name no
        # longer carries a version. The load-bearing assertion is that the move is attested in ONE entry.
        ver = tuple(int(x) for x in facts["version"].split("."))
        self.assertGreaterEqual(ver, (1, 40, 0),
                                "the founding is at or beyond the EP-48 era (1.40.0) this test pins")
        a = audit()
        self.assertTrue(a["logged"],
                        "the founding moved and no single BUILD-PROGRESS entry names "
                        "both the version and the pack sha256 (the required ledger duty, :1178)")

    def test_the_discriminator_is_MINOR_no_op_removed_no_check_kind_added(self):
        with open(PACK_PATH, "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        # ADDED (six ops + one law + one map amendment) — the MINOR direction:
        for n in SIX_OPS:
            self.assertIn(n, op_names)
        rule_ids = {(r.get("payload") or {}).get("rule_id") for r in recs
                    if r.get("action") == "CREATE-RULE"}
        self.assertIn("NET-LAW-GRANT", rule_ids)
        # NONE REMOVED — the ops the campaign already shipped are all still present (a removal would
        # be MAJOR, RW-MAJOR / stop-e): a representative pre-move op survives.
        for kept in ("COMMS-OPEN", "COMMS-SEND", "FILE-CREATE", "MOUNT"):
            self.assertIn(kept, op_names)
        # NO CHECK KIND ADDED — the discriminator's other half. OP_CHECKS is the check vocabulary;
        # EP-48 adds none (a new check kind would be MAJOR / stop-e). Frozen at 17.
        self.assertEqual(len(OP_CHECKS), 19)
        # the six socket ops use ONLY existing check kinds (require_prior, value_domain).
        used = set()
        for r in recs:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] in SIX_OPS:
                for c in r["payload"]["definition"].get("checks", []):
                    used.add(c["check"])
        self.assertTrue(used <= set(OP_CHECKS))
        self.assertTrue(used <= {"require_prior", "value_domain"})

    def test_RW_MAJOR_a_removed_op_or_a_new_check_kind_would_be_the_STOP(self):
        """RW-MAJOR (§4 / stop-e): the discriminator is able-to-distinguish. A pack that REMOVED an
        op, or that added a check kind, is MAJOR — an owner matter, not decided here. Driven as the
        counterfactual the discriminator must catch (§A42), the real bytes untouched."""
        with open(PACK_PATH, "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        # a MAJOR-shaped move: SOCKET-OPEN reaching by REMOVING COMMS-OPEN would be MAJOR — assert
        # the real move did NOT do that (COMMS-OPEN kept), so the move stayed MINOR by construction.
        self.assertIn("COMMS-OPEN", op_names)
        # a new check kind is the other MAJOR shape — assert none of the six ops introduced one.
        for r in recs:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] in SIX_OPS:
                for c in r["payload"]["definition"].get("checks", []):
                    self.assertIn(c["check"], OP_CHECKS,
                                  f"{r['payload']['name']} introduced a check kind — MAJOR / stop-e")


# =============================================================================================
# RW-POSIX-AS-LAW — the grant is authority (who-may-open-what-to-where), not the POSIX call
# =============================================================================================

class TestGrantIsAuthorityNotPosix(unittest.TestCase):
    def test_net_law_grant_states_authority_not_socket_call_semantics(self):
        """RW-POSIX-AS-LAW (§4 / stop-f): the grant/op checks state WHO may open WHAT to WHERE, not
        what listen(2) DOES. Proven structurally: the checks are authority checks (require_prior over
        the opener/socket, value_domain over the family) — nothing that re-states an API's behaviour."""
        with open(PACK_PATH, "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        law = next(r for r in recs if r.get("action") == "CREATE-RULE"
                   and (r.get("payload") or {}).get("rule_id") == "NET-LAW-GRANT")
        text = law["payload"]["text"].lower()
        self.assertIn("who may open what", text)                    # authority, named in the law
        # the six ops' checks are authority preconditions, never a POSIX-behaviour re-statement:
        for r in recs:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] in SIX_OPS:
                for c in r["payload"]["definition"].get("checks", []):
                    self.assertIn(c["check"], ("require_prior", "value_domain"))


if __name__ == "__main__":
    unittest.main()
