"""EP-48G — SOCKET-GRANTS, GUEST-REAL: the six socket acts driven REAL through the guest
kernel under the pinned kernel (design/51 N1 real + N9; §5 EP-48G; §11 ruling 1, :3251).

Named in planning/exec/EP-48G-BUILD.md before code, landed here as regression tests (charter:
every verification probe lands as a regression test). EP-48 records the six socket acts against
a MODELLED table on the HOST (no real socket); EP-49D proved the receipt as two stores ON THE
HOST (a stated cap). EP-48G drives THE SAME OPS REAL through the guest kernel: a real socket
opens ONLY under a recorded grant; a refused grant = NO socket + the real errno the rule-errno
pack maps (NET-LAW-GRANT -> EACCES, added by this unit's founding move) + the refusal row; one
row crosses host<->guest with one receipt, each body appending only to its OWN record (one pen);
host and guest ledgers reconcile. The guest is the SECOND BODY — a second KERNEL AND RECORD on a
separate VIRTUAL machine on this ONE physical host (archi :3421; two physical bodies over a
network are C6's, and N9's row is proven at THAT scope).

  A1  a REAL socket opens in the guest ONLY under a recorded grant; the decision is recorded;
      no grant -> no socket (T-SOCKET-DECISION-RECORDED real).
  A2  a refused grant = NO socket + the errno the rule-errno pack maps (EACCES) + the refusal
      row; a planted grant-bypass (a real socket without a grant) REDS (RW-GRANT-BYPASS).
  A3  the live socket table is a DERIVED view over the socket acts; kill the fold's cache ->
      identical (T-SOCKET-TABLE-DERIVED real).
  A4  a census under real traffic: ZERO rows of any packet kind (T-NO-PACKET-ROWS real).
  A5  one row sent from the host is received at the guest as INPUT through the guest's border;
      the guest appends ITS receipt to ITS OWN record; over a REAL socket (T-ONE-ROW-ONE-RECEIPT).
  A6  the sender's record is unchanged by the receipt; one pen per data dir (store.py single-
      writer lock) — the host never writes the guest's record and the guest never the host's.
  A7  each body's identity — its bound system public key + genesis hash (D08.42) — is
      expressible in the crossing and cited by the receipt; a copied seed is a fork the chain
      exposes (T-PEER-IDENTITY-EXPRESSIBLE).
  A8  each body's ledger is green on its own body; the crossing is consistent read from either
      side (T-LEDGERS-RECONCILE).
  A9  the founding move adds NET-LAW-GRANT -> EACCES to the rule-errno pack — data-born MINOR,
      attested in ONE entry — op-population UNCHANGED (93), OP_CHECKS UNCHANGED (19); the §A57
      three-family sweep.

THE ERA SPLIT, NEVER A REPLACEMENT (design/51 §5): the MODELLED host arm (EP-48) STAYS beside
the REAL arm — a real socket where the guest kernel drives it, modelled where it does not.

GUEST-REAL, NEVER MODELLED (EP-00 rule 9). Kernel/socket work runs ONLY in the guest. The
real-socket arms (A1, A2, A4 real) run IN THE GUEST — detected by kernel_port.in_pinned_guest()
or GOVOS_GUEST_REAL=1 — and SKIP on the host with a stated reason (never a modelled open dressed
as a real one). The real host<->guest crossing (A5/A6/A8 real) is driven over the REAL ssh
socket when GOVOS_HOST_GUEST_CROSS=1 (the host end of the wire), and SKIPS otherwise, its proof
filed under planning/evidence/EP-48G/. The STRUCTURAL properties (the fold, the one-pen lock,
peer identity, the errno rendering, the refusal row, the founding move) are governed-op facts,
identical on either body, and run everywhere as durable regressions.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from bridge import kernel_port                                            # noqa: E402
from kernel.compose import build_full_kernel                             # noqa: E402
from kernel.errors import OpError                                        # noqa: E402
from kernel.opdefs import OP_CHECKS                                      # noqa: E402
from kernel.store import EventStore                                      # noqa: E402
from kernel.syscall_port import SyscallPort                              # noqa: E402
from kernel import border, crypto                                       # noqa: E402
from subsystems.sockets import SocketView, SOCKET_ACTIONS               # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

SIX_OPS = ("SOCKET-OPEN", "SOCKET-BIND", "SOCKET-LISTEN",
           "SOCKET-CONNECT", "SOCKET-ACCEPT", "SOCKET-CLOSE")

# THE SURFACE THAT DECIDES WHETHER A REAL ARM RUNS. in_pinned_guest() reads the two surfaces
# kcheck.sh reads (virt=kvm host=gov-lab); GOVOS_GUEST_REAL=1 is the explicit in-guest run.
_IN_GUEST = kernel_port.in_pinned_guest() or os.environ.get("GOVOS_GUEST_REAL") == "1"
_GUEST_SKIP = ("the REAL socket arm opens a real fd in the guest kernel and runs IN THE GUEST "
               "(EP-00 rule 9); on the host the wire is EP-48's modelled table. Evidence: "
               "planning/evidence/EP-48G/. Run in-guest with GOVOS_GUEST_REAL=1.")

# THE HOST END OF THE REAL host<->guest CROSSING (over the ssh socket to the pinned guest).
_CROSS = os.environ.get("GOVOS_HOST_GUEST_CROSS") == "1"
_CROSS_SKIP = ("the REAL host<->guest crossing runs over the real ssh socket to the pinned "
               "guest; set GOVOS_HOST_GUEST_CROSS=1 (and GOVOS_GUEST_SRC to the shipped guest "
               "src) to drive it. Evidence: planning/evidence/EP-48G/. The STRUCTURAL property "
               "runs here unconditionally.")

# A crossing — a row an outside entity submitted; its content hash is the crossing id.
A_ROW = {"action": "BORDER-SUBMIT", "object": "peer", "target": None,
         "payload": {"kind": "border-submit", "want": "read /x"}}


def _body(prefix):
    """One BODY — an independent record (its own data dir), gate and views. Two bodies are two
    of these; a body writes only its own record (one pen per record, the single-writer lock)."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    return d, store, gate, views


def _world():
    """A kernel from the SHIPPED founding, with one established entity 'web' to open by."""
    d, store, gate, views = _body("ep48g-")
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "web", "actor_class": "human"})
    return d, store, gate, views


# =============================================================================================
# A1 — TestRealSocketUnderGrant : a REAL socket opens in the guest ONLY under a recorded grant
# =============================================================================================

class TestRealSocketUnderGrant(unittest.TestCase):
    def test_the_grant_is_recorded_and_is_the_only_door_to_a_real_socket(self):
        """STRUCTURAL (host+guest): the seam decides on the RECORD first. Under a grant the
        SOCKET-OPEN decision is recorded citing NET-LAW-GRANT; a refused grant raises BEFORE any
        socket is reached (the grant is the only door). Proven without opening a host socket by
        stubbing the guest surface — the record decides regardless of surface, the real fd does
        not (RW-HOST-SOCKET as a capability)."""
        _d, store, gate, _v = _world()
        # a granted open: the record decides; the real socket is refused OFF the guest surface,
        # so no host fd opens, but the GRANT is on the record.
        with self.assertRaises(kernel_port.RealSocketOnHostRefused):
            kernel_port.open_real_socket_under_grant(gate, "web", "s1", "inet",
                                                     guest_check=lambda: False)
        dec = [e for e in store.by_action("SOCKET-OPEN")]
        self.assertTrue(dec and dec[-1]["rule_cited"] == "NET-LAW-GRANT")   # grant recorded
        self.assertIn("s1", SocketView(store).live_sockets())               # under the grant
        # a refused grant (an unestablished opener) raises at the gate — no decision, no socket.
        with self.assertRaises(OpError) as cm:
            kernel_port.open_real_socket_under_grant(gate, "ghost", "g1", "inet",
                                                     guest_check=lambda: True)
        self.assertEqual(cm.exception.rule, "NET-LAW-GRANT")
        self.assertNotIn("g1", SocketView(store).live_sockets())            # no grant -> no socket

    @unittest.skipUnless(_IN_GUEST, _GUEST_SKIP)
    def test_a_real_socket_opens_in_the_guest_only_under_a_grant(self):
        """A1 REAL (guest-only): under a recorded grant a REAL socket opens in THIS guest kernel —
        a real fd, bindable to a real local port. Without a grant the gate raises and no real
        socket is reached. The real fd is closed; the guest is left clean."""
        import socket as _sock
        _d, store, gate, _v = _world()
        decision, real = kernel_port.open_real_socket_under_grant(gate, "web", "s1", "inet")
        try:
            self.assertEqual(decision["action"], "SOCKET-OPEN")
            self.assertGreaterEqual(real.fileno(), 0)                       # a real kernel fd
            real.bind(("127.0.0.1", 0))
            host, port = real.getsockname()
            self.assertTrue(port > 0)                                       # a real local port
        finally:
            real.close()
        # no grant -> no real socket (the gate raises before the seam opens anything).
        with self.assertRaises(OpError):
            kernel_port.open_real_socket_under_grant(gate, "ghost", "g1", "inet")


# =============================================================================================
# A2 — TestRefusedGrant : refused = NO socket + errno (EACCES) + refusal row; bypass REDS
# =============================================================================================

class TestRefusedGrant(unittest.TestCase):
    def test_a_refused_grant_renders_EACCES_from_the_pack_and_records_the_refusal(self):
        """A2 STRUCTURAL: a refused NET-LAW-GRANT renders the errno the rule-errno pack maps —
        EACCES, added by this unit's founding move (before it, EINVAL) — and the refusal is
        RECORDED citing the grant. The errno is read FROM the pack (law-as-data), not the code."""
        _d, store, gate, views = _world()
        with self.assertRaises(OpError) as cm:
            gate.execute("SOCKET-OPEN", "ghost", {"entity": "ghost", "socket": "g1", "family": "inet"})
        self.assertEqual(cm.exception.rule, "NET-LAW-GRANT")
        # the errno the PACK maps for the cited rule (the live map, not the code fallback):
        self.assertEqual(SyscallPort(gate, views)._errno_for("NET-LAW-GRANT"), "EACCES")
        # the refusal is on the record, citing the grant (cannot-do-quietly).
        refusals = [e for e in store.by_action("op-refused")
                    if (e.get("payload") or {}).get("op") == "SOCKET-OPEN"]
        self.assertTrue(refusals, "the refused socket act was silently dropped, not recorded")
        self.assertEqual(refusals[-1].get("rule_cited"), "NET-LAW-GRANT")

    def test_RW_ROW_ABSENT_the_errno_would_be_EINVAL_which_is_this_move_being_load_bearing(self):
        """RW (able-to-fail): EACCES is THIS founding move's doing, not a default. A rule the pack
        does NOT map falls back to EINVAL — so EACCES for NET-LAW-GRANT proves the row is present
        and load-bearing (remove it and the refusal wears EINVAL again, the pre-move state)."""
        _d, _s, gate, views = _world()
        sp = SyscallPort(gate, views)
        self.assertEqual(sp._errno_for("NET-LAW-GRANT"), "EACCES")          # the row is present
        self.assertEqual(sp._errno_for("NO-SUCH-RULE-XYZ"), "EINVAL")       # the unmapped default

    def test_RW_GRANT_BYPASS_the_grant_is_load_bearing_a_bypass_cannot_pass_the_seam(self):
        """RW-GRANT-BYPASS (§4): a real socket without a recorded grant is the forbidden shape.
        The seam decides on the RECORD FIRST, so a refused grant raises before any socket — a
        bypass cannot pass through it. Proven three ways the guard fires (WHO / WHAT / a socket no
        record opened), each citing NET-LAW-GRANT, and once that a granted call DOES reach the
        seam's guest gate (able-to-fail both directions)."""
        _d, store, gate, _v = _world()
        gate.execute("SOCKET-OPEN", "web", {"entity": "web", "socket": "s1", "family": "inet"})
        for entity, params in [
            ("nobody", {"entity": "nobody", "socket": "x", "family": "inet"}),   # WHO
            ("web",    {"entity": "web", "socket": "y", "family": "raw"}),        # WHAT (family)
            ("web",    {"socket": "never-opened", "address": "a"}),               # a socket no record opened
        ]:
            op = "SOCKET-BIND" if "address" in params else "SOCKET-OPEN"
            with self.assertRaises(OpError) as cm:
                gate.execute(op, entity, params)
            self.assertEqual(cm.exception.rule, "NET-LAW-GRANT")
        # the honest world DOES reach the guest gate (so the refusals above are the bypass being
        # stopped, not a seam that refuses everything): a valid grant reaches the guest check.
        with self.assertRaises(kernel_port.RealSocketOnHostRefused):
            kernel_port.open_real_socket_under_grant(gate, "web", "s2", "inet",
                                                     guest_check=lambda: False)

    @unittest.skipUnless(_IN_GUEST, _GUEST_SKIP)
    def test_no_real_socket_opens_on_a_refused_grant_in_the_guest(self):
        """A2 REAL (guest-only): in the guest, a refused grant opens NO real socket — the gate
        raises before the seam reaches socket.socket(). Nothing to close; the guest stays clean."""
        _d, _s, gate, _v = _world()
        with self.assertRaises(OpError) as cm:
            kernel_port.open_real_socket_under_grant(gate, "ghost", "g1", "inet")
        self.assertEqual(cm.exception.rule, "NET-LAW-GRANT")


# =============================================================================================
# A3 — TestSocketTableDerivedReal : the socket table is a DERIVED fold (cache-kill identical)
# =============================================================================================

class TestSocketTableDerivedReal(unittest.TestCase):
    def test_the_socket_table_is_a_fold_over_the_acts_and_cache_kill_recomputes_identical(self):
        """A3 STRUCTURAL (host+guest): the live socket table is a DERIVED view over the socket
        acts, not a stored copy. Kill the fold's cache -> identical, a fresh object; the record
        holds ONLY the six wire acts, never a table dump (T-CACHE-KILL, over the real acts)."""
        _d, store, gate, _v = _world()
        gate.execute("SOCKET-OPEN", "web", {"entity": "web", "socket": "s1", "family": "inet"})
        gate.execute("SOCKET-BIND", "web", {"socket": "s1", "address": "<LOOPBACK-PORT>"})
        gate.execute("SOCKET-OPEN", "web", {"entity": "web", "socket": "s2", "family": "inet6"})
        gate.execute("SOCKET-CONNECT", "web", {"socket": "s2", "target": "1.2.3.4:443"})
        gate.execute("SOCKET-CLOSE", "web", {"socket": "s1"})
        view = SocketView(store)
        t1 = view.live_sockets()
        self.assertEqual(set(t1), {"s2"})                                  # s1 closed, s2 live
        view.kill_cache()
        t2 = view.live_sockets()
        self.assertEqual(t1, t2)
        self.assertIsNot(t1, t2)                                           # a fold local, not a store
        # the record holds only wire acts (no stored table row).
        for e in store.action_set_projection(set(SOCKET_ACTIONS)).all():
            self.assertIn(e["action"], SIX_OPS)
        # a second independent view over the same record yields the same table.
        self.assertEqual(SocketView(store).live_sockets(), t1)

    @unittest.skipUnless(_IN_GUEST, _GUEST_SKIP)
    def test_the_table_is_derived_over_acts_that_opened_a_real_socket(self):
        """A3 REAL (guest-only): each granted open drives a REAL fd in the guest kernel, and the
        table folds over those same governed acts — killing the cache still recomputes identical.
        The real fds are closed; the guest is left clean."""
        _d, store, gate, _v = _world()
        reals = []
        try:
            for sid in ("s1", "s2"):
                _dec, real = kernel_port.open_real_socket_under_grant(gate, "web", sid, "inet")
                reals.append(real)
            gate.execute("SOCKET-CLOSE", "web", {"socket": "s1"})
            view = SocketView(store)
            t1 = view.live_sockets()
            view.kill_cache()
            self.assertEqual(t1, view.live_sockets())
            self.assertEqual(set(t1), {"s2"})
        finally:
            for r in reals:
                r.close()


# =============================================================================================
# A4 — TestNoPacketRows : a census (under real traffic in-guest) has ZERO packet rows
# =============================================================================================

class TestNoPacketRows(unittest.TestCase):
    def test_a_census_over_the_socket_acts_has_zero_per_packet_rows(self):
        """A4 STRUCTURAL: the socket ops record GRANTS, never bytes on the wire — a per-packet
        flow is STREAM and STREAM appends nothing. A census over a workload finds only the six
        ops; a synthetic per-packet row is the counterfactual the census must catch (able-to-fail)."""
        _d, store, gate, _v = _world()
        before = len(store.events)
        for i in range(12):
            sid = f"s{i}"
            gate.execute("SOCKET-OPEN", "web", {"entity": "web", "socket": sid, "family": "inet"})
            gate.execute("SOCKET-CONNECT", "web", {"socket": sid, "target": f"1.1.1.1:{i}"})
            gate.execute("SOCKET-CLOSE", "web", {"socket": sid})
        appended = store.events[before:]
        for e in appended:
            self.assertIn(e["action"], SIX_OPS, f"a non-grant row appeared: {e['action']}")
        # the counterfactual: a byte-on-the-wire row in the set the census reads makes it red.
        packet_row = {"actor": "web", "action": "socket-traffic", "object": "s0",
                      "rule_cited": "NET-LAW-GRANT", "payload": {"socket": "s0", "bytes": 1400}}
        offenders = [e for e in (appended + [packet_row]) if e["action"] not in SIX_OPS]
        self.assertEqual([e["action"] for e in offenders], ["socket-traffic"])
        # STREAM appends nothing (the classmap's own STREAM class is not recorded).
        from observe import classmap
        self.assertEqual(classmap.classify("connection", "connection-traffic"), classmap.STREAM)
        self.assertFalse(classmap.is_recorded("connection", "connection-traffic"))

    @unittest.skipUnless(_IN_GUEST, _GUEST_SKIP)
    def test_no_packet_rows_under_real_traffic_in_the_guest(self):
        """A4 REAL (guest-only): open a REAL connected pair in the guest kernel and exchange REAL
        bytes over it; a census of the record finds ZERO packet rows — real traffic appends
        nothing, exactly as the modelled census claims. The real fds are closed; guest left clean."""
        import socket as _sock
        _d, store, gate, _v = _world()
        before = len(store.events)
        lis = cli = srv = None
        try:
            _dec, lis = kernel_port.open_real_socket_under_grant(gate, "web", "L", "inet")
            lis.bind(("127.0.0.1", 0)); lis.listen(1)
            addr = lis.getsockname()
            gate.execute("SOCKET-LISTEN", "web", {"socket": "L"})
            _dec2, cli = kernel_port.open_real_socket_under_grant(gate, "web", "C", "inet")
            cli.connect(addr)
            gate.execute("SOCKET-CONNECT", "web", {"socket": "C", "target": f"{addr[0]}:{addr[1]}"})
            srv, _peer = lis.accept()
            gate.execute("SOCKET-ACCEPT", "web", {"socket": "L", "peer": f"{_peer[0]}:{_peer[1]}"})
            cli.sendall(b"real-bytes-over-a-real-guest-socket")             # REAL traffic
            self.assertEqual(srv.recv(64), b"real-bytes-over-a-real-guest-socket")
        finally:
            for s in (srv, cli, lis):
                if s is not None:
                    s.close()
        appended = store.events[before:]
        packetish = [e for e in appended if e["action"] not in SIX_OPS]
        self.assertEqual(packetish, [], "a per-packet row reached the record under real traffic")


# =============================================================================================
# A5 — TestOneRowOneReceipt : one row crosses host<->guest, exactly one receipt in the guest
# =============================================================================================

# Cache the one real crossing so A5/A6/A8 reuse it (one ssh round trip, not three).
_CROSSING = {"done": False, "result": None}


def _drive_real_crossing():
    """Drive the REAL host<->guest crossing ONCE over the ssh socket and cache the result.

    Body A = THIS host (a host record). The row A_ROW crosses the REAL ssh socket to the guest.
    Body B = the guest (a guest record composed from the SHIPPED current src). The guest records
    ITS receipt in ITS OWN record and prints the receipt facts back. Returns a dict or None (the
    guest unreachable / src not shipped -> the caller SKIPS, never models-and-claims)."""
    if _CROSSING["done"]:
        return _CROSSING["result"]
    _CROSSING["done"] = True
    guest_src = os.environ.get("GOVOS_GUEST_SRC")
    if not guest_src:
        _CROSSING["result"] = None
        return None
    # body A on the host.
    a_dir, a_store, a_gate, _av = _body("ep48g-cross-host-A-")
    ch = border.content_id(A_ROW)
    fb = border.from_body_name("ed25519-pub:host", border.genesis_hash(a_store))
    a_head_before = border.chain_head(a_store)
    a_len_before = len(a_store.all())
    # the guest-side receipt program: compose body B from the shipped src, record the receipt in
    # B's OWN record, print the receipt facts. The row's bytes cross the REAL ssh socket as argv.
    prog = (
        "import sys,os,json,tempfile\n"
        "sys.path.insert(0, os.path.join(os.environ['GOVOS_GUEST_SRC']))\n"
        "from kernel.compose import build_full_kernel\n"
        "from kernel import border\n"
        "ch, key, gen, sig = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]\n"
        "d=tempfile.mkdtemp(prefix='ep48g-cross-guest-B-')\n"
        "store,gate,views,blobs,subs=build_full_kernel(os.path.join(d,'record.jsonl'),os.path.join(d,'blobs'),os.path.join(d,'vault'))\n"
        "fb={'key':key,'genesis':gen}\n"
        "rec=border.record_receipt(gate, ch, fb, sig)\n"
        "p=rec.get('payload') or {}\n"
        "out={'cited_hash':p.get('content_hash'),'record_class':p.get('record_class'),"
        "'guest_chain_head':border.chain_head(store),'guest_genesis':border.genesis_hash(store),"
        "'receipts':list(border.receipts(store).keys()),'chain_ok':store.verify_chain().get('ok'),"
        "'uname':os.uname().release}\n"
        "print('EP48G_CROSS '+json.dumps(out))\n"
    )
    ssh = ["ssh", "-p", os.environ.get("GOVOS_GUEST_PORT", "2222"),
           "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
           "-o", "ConnectTimeout=10",
           "-i", os.path.expanduser(os.environ.get("GOVOS_GUEST_KEY", "<KEYPATH>")),
           os.environ.get("GOVOS_GUEST_USER", "ubuntu") + "@" + os.environ.get("GOVOS_GUEST_ADDR", "127.0.0.1"),
           "GOVOS_GUEST_SRC=%s python3 - %s %s %s %s" % (guest_src, ch, fb["key"], fb["genesis"], "ed25519-sig:z")]
    try:
        proc = subprocess.run(ssh, input=prog, capture_output=True, text=True, timeout=60)
    except Exception as e:                                                 # unreachable -> skip
        _CROSSING["result"] = {"error": "ssh: %s" % e}
        return _CROSSING["result"]
    line = next((l for l in proc.stdout.splitlines() if l.startswith("EP48G_CROSS ")), None)
    if line is None:
        _CROSSING["result"] = {"error": "guest gave no receipt: rc=%d err=%s"
                               % (proc.returncode, proc.stderr[-400:])}
        return _CROSSING["result"]
    guest = json.loads(line[len("EP48G_CROSS "):])
    _CROSSING["result"] = {
        "content_hash": ch, "guest": guest,
        "a_head_before": a_head_before, "a_head_after": border.chain_head(a_store),
        "a_len_before": a_len_before, "a_len_after": len(a_store.all()),
        "a_receipts": border.receipts(a_store), "a_chain_ok": a_store.verify_chain().get("ok"),
        "receipt_binds": guest["cited_hash"] == ch,
    }
    return _CROSSING["result"]


class TestOneRowOneReceipt(unittest.TestCase):
    def test_one_row_produces_exactly_one_receipt_in_the_receivers_own_record(self):
        """A5 STRUCTURAL: a row received at body B produces EXACTLY ONE RECEIPT in B's record, a
        DECISION citing the row's content hash; a second receipt for the same row is refused
        (one row, one receipt); the receipt binds the row (of a specific crossing)."""
        _d, store, gate, _v = _body("ep48g-a5-B-")
        _ad, a_store, _ag, _av = _body("ep48g-a5-A-")
        ch = border.content_id(A_ROW)
        fb = border.from_body_name("ed25519-pub:host", border.genesis_hash(a_store))
        rec = border.record_receipt(gate, ch, fb, "ed25519-sig:z")
        self.assertEqual(rec["action"], "RECEIPT")
        self.assertEqual((rec.get("payload") or {}).get("content_hash"), ch)
        self.assertEqual(list(border.receipts(store)), [ch])               # exactly one
        self.assertTrue(border.receipt_binds_row(rec, A_ROW))              # of this crossing
        with self.assertRaises(OpError):
            border.record_receipt(gate, ch, fb, "ed25519-sig:z")           # a second: refused
        self.assertEqual(len(border.receipts(store)), 1)

    @unittest.skipUnless(_CROSS, _CROSS_SKIP)
    def test_one_row_crosses_a_real_socket_to_the_guest_and_is_receipted_there(self):
        """A5 REAL (host<->guest): the row crosses the REAL ssh socket to the pinned guest; the
        guest composes its OWN record and appends ITS receipt there, citing the SAME content hash
        (the round trip verifies). The guest reports its own kernel (6.8.0-134) — the second body
        is a second kernel+record on the guest VM, not two temp dirs on one host (archi :3421)."""
        r = _drive_real_crossing()
        self.assertIsNotNone(r, _CROSS_SKIP)
        self.assertNotIn("error", r, r.get("error", ""))
        self.assertEqual(r["guest"]["cited_hash"], r["content_hash"])       # round trip
        self.assertTrue(r["receipt_binds"])
        self.assertEqual(r["guest"]["record_class"], "DECISION")            # the receiver's own act
        self.assertEqual(r["guest"]["receipts"], [r["content_hash"]])       # exactly one, in the guest
        self.assertTrue(r["guest"]["uname"].startswith("6.8.0-134"))        # the pinned guest kernel


# =============================================================================================
# A6 — TestOnePenHolds : one pen per data dir (the single-writer lock); sender unchanged
# =============================================================================================

class TestOnePenHolds(unittest.TestCase):
    def test_the_single_writer_lock_refuses_a_foreign_writer_on_a_bodys_data_dir(self):
        """A6 STRUCTURAL (the one-pen mechanism, EP-28G/EP-49D reused): a body's record has ONE
        writer per data dir. A live foreign process (pid 1) holding the pen refuses a second
        writer; with the pen free a writer acquires (able-to-fail, the refusal is the holder's)."""
        d = tempfile.mkdtemp(prefix="ep48g-a6-pen-")
        rec_path = os.path.join(d, "record.jsonl")
        with open(rec_path + ".lock", "w") as fh:
            fh.write("1")                                                  # pid 1 (init) is always alive
        with self.assertRaises(RuntimeError) as cm:
            EventStore(rec_path, lock=True)
        self.assertIn("one writer per data dir", str(cm.exception))
        os.remove(rec_path + ".lock")
        self.assertIsNotNone(EventStore(rec_path, lock=True))              # the pen free -> acquires

    def test_the_receivers_receipt_does_not_touch_the_senders_record(self):
        """A6 STRUCTURAL: B appends its receipt to ITS OWN record; A's record is UNCHANGED — A
        never writes B's record and B never A's. A's chain head is byte-identical before and
        after B's receipt; the two bodies' heads are independent."""
        _ad, a_store, _ag, _av = _body("ep48g-a6-A-")
        _bd, b_store, b_gate, _bv = _body("ep48g-a6-B-")
        ch = border.content_id(A_ROW)
        fb = border.from_body_name("ed25519-pub:host", border.genesis_hash(a_store))
        a_head = border.chain_head(a_store)
        a_len = len(a_store.all())
        border.record_receipt(b_gate, ch, fb, "sig")
        self.assertIn(ch, border.receipts(b_store))                        # B's receipt in B's record
        self.assertEqual(border.receipts(a_store), {})                     # A's has none
        self.assertEqual(border.chain_head(a_store), a_head)               # A UNCHANGED
        self.assertEqual(len(a_store.all()), a_len)
        self.assertNotEqual(border.chain_head(a_store), border.chain_head(b_store))

    @unittest.skipUnless(_CROSS, _CROSS_SKIP)
    def test_real_one_pen_the_host_record_is_unchanged_by_the_guest_receipt(self):
        """A6 REAL (host<->guest): after the real crossing, the HOST's record is byte-identical —
        the guest wrote only its OWN record, the host never the guest's (one pen per body, over a
        real socket between the two bodies)."""
        r = _drive_real_crossing()
        self.assertIsNotNone(r, _CROSS_SKIP)
        self.assertNotIn("error", r, r.get("error", ""))
        self.assertEqual(r["a_head_before"], r["a_head_after"])            # host UNCHANGED
        self.assertEqual(r["a_len_before"], r["a_len_after"])
        self.assertEqual(r["a_receipts"], {})                              # the receipt is the guest's
        self.assertNotEqual(r["a_head_after"], r["guest"]["guest_chain_head"])  # two records, two heads


# =============================================================================================
# A7 — TestPeerIdentityExpressible : from-body = bound key + genesis; copied seed is a fork
# =============================================================================================

class TestPeerIdentityExpressible(unittest.TestCase):
    SENDER_SEED = bytes(range(1, 33))
    OTHER_SEED = bytes([9]) * 32

    def test_the_from_body_is_the_bound_key_plus_genesis_and_the_signature_is_real_or_refused(self):
        """A7 / D08.42: the from-body is a body's NAME — (bound SYSTEM PUBLIC KEY, genesis hash).
        The receipt verifies the sender's SIGNATURE over the crossing under that key. Real-or-
        refused (N10): library ABSENT -> verification REFUSES citing the absent library, never a
        modelled pass; PRESENT -> a correct signature verifies and a wrong key/crossing does not."""
        _ad, a_store, _ag, _av = _body("ep48g-a7-A-")
        genesis = border.genesis_hash(a_store)
        self.assertIsNotNone(genesis)
        ch = border.content_id(A_ROW)
        if not crypto.real_available():
            fb = border.from_body_name("ed25519-pub:modelled", genesis)
            with self.assertRaises(crypto.LibraryAbsent):
                border.verify_from_sig(fb, "ed25519-sig:x", ch)            # real-or-refused
            return
        from kernel.signer import SigningKeyStore
        pub = crypto.public_from_seed(self.SENDER_SEED)
        fb = border.from_body_name(pub, genesis)
        signer = SigningKeyStore(); custody = signer.seal(self.SENDER_SEED)
        sig = signer.sign(custody, ch.encode())
        self.assertTrue(border.verify_from_sig(fb, sig, ch))               # correct -> verifies
        other = border.from_body_name(crypto.public_from_seed(self.OTHER_SEED), genesis)
        self.assertFalse(border.verify_from_sig(other, sig, ch))           # wrong key -> no
        self.assertFalse(border.verify_from_sig(fb, sig, "sha256:" + "0" * 64))  # wrong crossing -> no

    def test_a_copied_seed_is_a_fork_the_chain_exposes_never_a_silent_clash(self):
        """A7 / N9: a copied seed shares the KEY but the two bodies' chains DIVERGE — the fork is
        exposed by the chain, never a silent clash. Two bodies with an identical key that record
        different crossings have DIFFERENT chain heads."""
        same_key = "ed25519-pub:COPIED-SEED"
        _ad, a_store, _ag, _av = _body("ep48g-a7-fork-A-")
        _bd, b_store, b_gate, _bv = _body("ep48g-a7-fork-B-")
        _cd, c_store, c_gate, _cv = _body("ep48g-a7-fork-C-")
        fb = border.from_body_name(same_key, border.genesis_hash(a_store))
        border.record_receipt(b_gate, "sha256:" + "b" * 64, fb, "sig")
        border.record_receipt(c_gate, "sha256:" + "c" * 64, fb, "sig")
        self.assertEqual(fb["key"], same_key)                              # the KEY is copied
        self.assertNotEqual(border.chain_head(b_store), border.chain_head(c_store))  # the fork is in the chain


# =============================================================================================
# A8 — TestLedgersReconcile : each body's ledger green on its own body; crossing consistent
# =============================================================================================

class TestLedgersReconcile(unittest.TestCase):
    def test_each_body_ledger_verifies_on_its_own_body_and_the_crossing_is_consistent(self):
        """A8 STRUCTURAL: two bodies, each store's prev_hash chain verifies on its OWN body
        (store.verify_chain). The crossing is consistent read from EITHER side — the guest's
        receipt cites the content hash the host's row bears (border.content_id, computed from the
        row's own bytes by both bodies, never an in-band token)."""
        _ad, a_store, _ag, _av = _body("ep48g-a8-A-")
        _bd, b_store, b_gate, _bv = _body("ep48g-a8-B-")
        ch = border.content_id(A_ROW)
        fb = border.from_body_name("ed25519-pub:host", border.genesis_hash(a_store))
        rec = border.record_receipt(b_gate, ch, fb, "sig")
        self.assertTrue(a_store.verify_chain().get("ok"))                  # A green on A
        self.assertTrue(b_store.verify_chain().get("ok"))                  # B green on B
        # consistent from either side: the host computes the crossing id from the row; the guest's
        # receipt cites it; the two agree.
        self.assertEqual((rec.get("payload") or {}).get("content_hash"), border.content_id(A_ROW))

    @unittest.skipUnless(_CROSS, _CROSS_SKIP)
    def test_real_ledgers_reconcile_host_and_guest(self):
        """A8 REAL (host<->guest): after the real crossing, EACH body's ledger verifies on its own
        body — the host's chain here, the guest's chain in the guest — and the crossing's content
        hash is consistent read from either side (per module)."""
        r = _drive_real_crossing()
        self.assertIsNotNone(r, _CROSS_SKIP)
        self.assertNotIn("error", r, r.get("error", ""))
        self.assertTrue(r["a_chain_ok"])                                   # host ledger green on host
        self.assertTrue(r["guest"]["chain_ok"])                            # guest ledger green in guest
        self.assertEqual(r["guest"]["cited_hash"], r["content_hash"])      # consistent from either side


# =============================================================================================
# A9 — TestFoundingBump : the errno row (data-born MINOR, attested); the §A57 three-family sweep
# =============================================================================================

def _pack_records():
    with open(PACK_PATH, "rb") as fh:
        return [r for step in json.loads(fh.read())["steps"] for r in step["records"]]


class TestFoundingBump(unittest.TestCase):
    def test_the_rule_errno_pack_maps_NET_LAW_GRANT_to_EACCES_and_the_genesis_survives(self):
        """A9: the founding move adds NET-LAW-GRANT -> EACCES to the rule-errno pack. The live
        (latest-wins) fold serves the 8-row amendment; the genesis 7-row pack SURVIVES in history,
        never edited (append-only founding data, design/51 §6 item 3). The errno renders EACCES."""
        _d, _s, gate, views = _world()
        pack = views.category_packs()["rule-errno"]
        rows = {lvl["rule"]: lvl["errno"] for lvl in pack["levels"]}
        self.assertEqual(rows.get("NET-LAW-GRANT"), "EACCES")              # the row is served
        self.assertEqual(len(pack["levels"]), 8)                          # 7 genesis + this one
        # the genesis 7-row record survives beside the 8-row amendment (both present in history).
        errno_recs = [r for r in _pack_records() if (r.get("payload") or {}).get("name") == "rule-errno"]
        self.assertEqual(sorted(len(r["payload"]["levels"]) for r in errno_recs), [7, 8])
        # the errno renders EACCES through the shipped rule-keyed renderer (law-as-data).
        self.assertEqual(SyscallPort(gate, views)._errno_for("NET-LAW-GRANT"), "EACCES")

    def test_the_bump_is_a_data_born_MINOR_attested_in_one_entry(self):
        """A9: the founding rose one MINOR (1.46.0 -> 1.47.0, the base driven at dispatch) and the
        move is attested in ONE BUILD-PROGRESS entry (version + pack sha256). ERA-PINNED from
        birth (a FLOOR at the EP-48G era): a later founding mover advances the constitution WITHOUT
        touching this line. The load-bearing assertion is that THIS founding on disk is attested."""
        from test_founding_is_logged import audit, pack_facts
        ver = tuple(int(x) for x in pack_facts()["version"].split("."))
        self.assertGreaterEqual(ver, (1, 47, 0),
                                "the founding is at or beyond the EP-48G era (1.47.0) this test pins")
        self.assertTrue(audit()["logged"],
                        "the founding moved and no single BUILD-PROGRESS entry names both the "
                        "version and the pack sha256 (the required ledger duty, :1178/:2805)")

    def test_the_discriminator_no_op_no_law_no_check_kind_added_population_and_OP_CHECKS_unchanged(self):
        """A9 / §A57 THREE-FAMILY SWEEP: this is a DATA row only. (1) op-population UNCHANGED at
        93 (a rule-errno level is not an op); (2) the rule-errno row count moved 7 -> 8 by this
        move alone; (3) OP_CHECKS UNCHANGED at 19 (no new check kind). No op added or removed, no
        law created — the :3069 discriminator: a data-born MINOR, not a new-surface one."""
        _d, _s, gate, views = _world()
        # EP-48G's own move is +0 (a rule-errno level is not an op); the LIVE base moved 93 -> 94 when
        # C6a VT-2 MINTED CREATE-RELATIONSHIP (1.51.0 -> 1.52.0) — this live-census pin tracks it BY NAME (§A57).
        self.assertEqual(len(views.op_definitions()), 94)                  # live op-population (EP-48G +0; VT-2 +1)
        self.assertEqual(len(OP_CHECKS), 19)                              # no check kind
        self.assertEqual(len(views.category_packs()["rule-errno"]["levels"]), 8)  # the data move
        # NO op or law was added by this move: the pack's op/law populations are unchanged from
        # EP-52's close (the prior founding mover) — no CREATE-OP / CREATE-RULE names NET-LAW-GRANT
        # as a NEW op or a NEW law here (the law and the ops predate this unit, EP-48).
        op_names = {r["payload"]["name"] for r in _pack_records() if r.get("action") == "CREATE-OP"}
        for kept in ("SOCKET-OPEN", "SOCKET-CLOSE", "RECEIPT", "FILTER-DECISION", "COMMS-OPEN"):
            self.assertIn(kept, op_names)                                  # the surface predates this move


if __name__ == "__main__":
    unittest.main()
