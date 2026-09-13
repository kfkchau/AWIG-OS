"""EP-30-C5 / M1 — the connection shadow matures and retires, on proof, never by swap.

Named in the EP file before code, landed here as regression tests (charter: every
verification probe lands as a regression test). This battery proves design/36 §7 item 3 — the
retirement ledger law — for the CONNECTION subsystem, reusing the mechanism EP-25 built for
FILES (shadow-diff continuous + divergence-halt in both failure directions). IT MINTS NOTHING:
`shadow.py`'s tracks/current/StaleShadow surface and the sock_diag connection window already
exist; this unit PROVES them mature and GATES the retirement. No check kind, no founding op.

  A1  the subject re-driven, id for id BY NAME (never by line number): which SHADOW_VIEWS
      entry is the connection view and which window it shadows. A moved subject is a different
      unit (stop condition 2).
  A2  sustained shadow-diff ∅ under a connection workload BATTERY — N samples that MAKE and
      TEAR DOWN connections. An empty diff on a quiet box proves nothing (stop condition 5);
      the empty here is EARNED under churn.
  A3  divergence-halt in BOTH directions — (i) a seeded divergence HALTS current() and the
      drift is carried; (ii) NO false halt blocks a lawful assume across the battery.
  A4  retirement on proof, OR the raise — driven whether a governed-authoritative connection
      view exists to retire INTO. None does (connections are observe-only), so the gate
      REFUSES the void and the retirement is the raise; the gate PERMITS only on proof + a
      real target, so the raise is "no target exists", not "the gate can never pass".
  R1  a divergence that FAILS to halt — the drift comparison disabled on a copy: A3(i) reds.
  R2  a FALSE halt — a stuck `differing` though the two agree: A3(ii) reds.
  R3  a NAKED SWAP is refused — the retirement attempted with a proof absent: refused.

WHY THE SUSTAINED PROOF IS INJECTED, NOT LIVE. EP-22's own TestShadowTracks proves this
surface with an injected window (the campaign-1 adapter discipline), never a live one: a live
full-table shadow-diff FLAPS whenever any unrelated connection appears between the read and the
check, which on a busy box is constant. The injected battery makes the churn deterministic and
the empty EARNED. The live sock_diag path is anchored separately (TestRealWorldAnchor): real
loopback connections, observed for real, my own connections tracked.
"""

import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                              # noqa: E402
from observe import shadow                                               # noqa: E402
from observe.seam import (OP_FOR_WINDOW, ObservationSeam,                # noqa: E402
                          register_observe_ops)
from observe.windows import ConnectionWindow, DiffWindow                 # noqa: E402


# =============================================================================================
# The injected connection window and the workload battery — the campaign-1 adapter discipline
# =============================================================================================

class _FakeConnWindow(DiffWindow):
    """A connection window driven by injected snapshots, exactly as EP-22/EP-25 prove
    tracks/current — deterministically, without the live box's churn. `read()` diffs each
    snapshot against the previous and yields the connection crossings; `live_state()` returns
    the last snapshot, so a seeded divergence is a `set_box` that moves the BOX without the
    record catching up."""

    name = "connection"
    act_appeared = "connection-opened"
    act_removed = "connection-closed"
    act_changed = "connection-state-changed"

    def __init__(self, snapshots=(), version="c5-inj-1"):
        super().__init__(source=lambda: self._next())
        self._route = version
        self._snaps = list(snapshots)
        self._last = {}

    @property
    def route(self):
        return self._route

    @property
    def version(self):
        return self._route

    def _next(self):
        if self._snaps:
            self._last = self._snaps.pop(0)
        return self._last

    def live_state(self):
        return self._last

    def set_box(self, table):
        """Seed a divergence: move the box, leaving the record behind."""
        self._last = dict(table)

    def coverage(self):
        return {"facility": "injected connection", "sees": ["what the injection carries"],
                "does_not_see": ["anything the injection omits"]}


def _conn_battery(n_samples):
    """A workload battery. Every sample: two connections OPEN (SYN_SENT), the existing ones
    advance state (SYN_SENT -> ESTABLISHED -> CLOSE_WAIT), and CLOSE_WAIT ones are removed —
    so opens, state-changes and closes all cross every sample once steady state is reached.
    The box is never still; the shadow must fold each crossing to stay matched. Returns
    (snapshots, counts) — the counts NAME the workload so the empty diff is not a quiet box."""
    snaps = []
    live = {}                        # key -> {"state","uid","inode","_stage"}
    counts = {"opened": 0, "closed": 0, "state_changes": 0}
    nxt = 0
    next_state = {"SYN_SENT": "ESTABLISHED", "ESTABLISHED": "CLOSE_WAIT"}
    for _ in range(n_samples):
        for key in list(live):
            stage = live[key]["_stage"]
            if stage == "CLOSE_WAIT":
                del live[key]
                counts["closed"] += 1
            else:
                nxt_stage = next_state[stage]
                live[key]["_stage"] = nxt_stage
                live[key]["state"] = nxt_stage
                counts["state_changes"] += 1
        for _ in range(2):
            key = f"tcp:127.0.0.1:{40000 + nxt}-93.184.216.34:443"
            live[key] = {"state": "SYN_SENT", "uid": 1000, "inode": 500000 + nxt,
                         "_stage": "SYN_SENT"}
            nxt += 1
            counts["opened"] += 1
        snaps.append({key: {kk: vv for kk, vv in val.items() if not kk.startswith("_")}
                      for key, val in live.items()})
    return snaps, counts


class _Composed(unittest.TestCase):
    """The M1 composition EP-22 uses: the built kernel + the observation seam + the shadow
    view definitions. The connection window is supplied per test."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, _b, _s = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"))
        register_observe_ops(self.gate)
        self.seam = ObservationSeam(self.gate)
        shadow.define_shadow_views(self.gate)

    def _shadows(self, windows):
        return shadow.ShadowViews(self.store, self.views, windows)

    def _pump_tracking(self, samples=6):
        snaps, _ = _conn_battery(samples)
        w = _FakeConnWindow(snaps)
        shadows = self._shadows([w])
        for _ in range(samples):
            self.seam.submit_all(w.read())
        self.assertTrue(shadows.tracks("m1-connection-state")["tracks"], "did not reach tracking")
        return w, shadows


# =============================================================================================
# A1 — the subject re-driven, id for id, by NAME
# =============================================================================================

class TestA1SubjectRedriven(_Composed):
    def test_the_connection_view_and_its_window_are_where_the_ledger_law_expects(self):
        # BY NAME, never by line number (the citation discipline, EP §7).
        self.assertIn("m1-connection-state", shadow.SHADOW_VIEWS)
        window_name, _purpose = shadow.SHADOW_VIEWS["m1-connection-state"]
        self.assertEqual(window_name, "connection")
        self.assertEqual(shadow.VIEW_FOR_WINDOW["connection"], "m1-connection-state")
        # the window it shadows, by name, with its three connection acts
        w = ConnectionWindow()
        self.assertEqual(w.name, "connection")
        self.assertEqual((w.act_appeared, w.act_changed, w.act_removed),
                         ("connection-opened", "connection-state-changed", "connection-closed"))
        # the fold and the halt mechanism the EP names as THIS unit's subject
        self.assertIs(shadow.FOLDS["m1-connection-state"], shadow._fold_connection)
        self.assertIn("m1-connection-state", shadow.COMPARATORS)
        self.assertTrue(callable(getattr(shadow.ShadowViews, "current")))
        self.assertTrue(callable(getattr(shadow.ShadowViews, "tracks")))
        self.assertTrue(issubclass(shadow.StaleShadow, Exception))
        # the subject has NOT moved / split / retired: it is present and observe-only.
        self.assertEqual(OP_FOR_WINDOW["connection"], "OBSERVE-CONNECTION")


# =============================================================================================
# A2 — sustained shadow-diff ∅ under a connection workload battery (NOT a quiet box)
# =============================================================================================

class TestA2SustainedEmpty(_Composed):
    N = 24

    def test_shadow_diff_is_empty_across_the_whole_connection_workload_battery(self):
        snaps, counts = _conn_battery(self.N)
        w = _FakeConnWindow(snaps)
        shadows = self._shadows([w])
        empties = 0
        for i in range(self.N):
            self.seam.submit_all(w.read())                     # the sample's crossings recorded
            t = shadows.tracks("m1-connection-state")
            self.assertTrue(t["tracks"], f"sample {i} drifted: {t}")
            self.assertEqual((t["missing"], t["extra"], t["differing"]), ([], [], []),
                             f"sample {i} non-empty")
            empties += 1
        self.assertEqual(empties, self.N)                      # SUSTAINED, every sample
        # NOT a quiet box — the workload genuinely made, changed, and tore down connections.
        self.assertGreaterEqual(counts["opened"], 2 * self.N)
        self.assertGreater(counts["closed"], 0)
        self.assertGreater(counts["state_changes"], 0)


# =============================================================================================
# A3 — divergence-halt in BOTH directions
# =============================================================================================

class TestA3DivergenceHalt(_Composed):
    def test_i_a_seeded_divergence_halts_current_and_the_drift_is_carried(self):
        w, shadows = self._pump_tracking()
        box = dict(w.live_state())
        ghost = "tcp:<LOOPBACK-PORT>-93.184.216.34:443"        # the box gains what the record lacks
        box[ghost] = {"state": "ESTABLISHED", "uid": 1000, "inode": 999999}
        w.set_box(box)
        t = shadows.tracks("m1-connection-state")
        self.assertFalse(t["tracks"])
        self.assertIn(ghost, t["missing"])                     # box has it, record does not
        with self.assertRaises(shadow.StaleShadow) as cm:
            shadows.current("m1-connection-state")
        self.assertEqual(cm.exception.view, "m1-connection-state")
        self.assertIn(ghost, cm.exception.drift["missing"])
        self.assertEqual(cm.exception.drift["reason"], "shadow-diff non-empty")  # cites what diverged
        # the non-claiming answer is still available, labelled for what it is (never a stale current)
        self.assertFalse(shadows.answer("m1-connection-state")["claims_currency"])

    def test_i_a_lost_connection_is_the_mirror_failure_shape_and_also_halts(self):
        w, shadows = self._pump_tracking()
        box = dict(w.live_state())
        lost = next(iter(box))                                 # the box loses what the record has
        del box[lost]
        w.set_box(box)
        with self.assertRaises(shadow.StaleShadow) as cm:
            shadows.current("m1-connection-state")
        self.assertIn(lost, cm.exception.drift["extra"])       # record has it, box does not

    def test_ii_no_false_halt_across_the_battery(self):
        snaps, _ = _conn_battery(24)
        w = _FakeConnWindow(snaps)
        shadows = self._shadows([w])
        served = 0
        for i in range(24):
            self.seam.submit_all(w.read())
            out = shadows.current("m1-connection-state")       # a lawful assume: MUST serve
            self.assertTrue(out["claims_currency"], f"sample {i} refused a lawful assume")
            served += 1
        self.assertEqual(served, 24)                           # no false halt, ever


# =============================================================================================
# R1 — a divergence that FAILS to halt (the first failure direction, made to be caught)
# =============================================================================================

class TestR1DivergenceFailsToHalt(_Composed):
    def test_disabling_the_drift_comparison_serves_a_divergence_reds_A3i_restore_greens(self):
        w, shadows = self._pump_tracking()
        box = dict(w.live_state())
        ghost = "tcp:<LOOPBACK-PORT>-93.184.216.34:443"
        box[ghost] = {"state": "ESTABLISHED", "uid": 1000, "inode": 888888}
        w.set_box(box)

        # REMOVED (guard intact): the real divergence HALTS current() -> A3(i) GREEN
        with self.assertRaises(shadow.StaleShadow):
            shadows.current("m1-connection-state")

        # PRESENT (drift comparison disabled on a copy): tracks blind-reports tracking, so
        # current() SERVES the divergence instead of halting -> A3(i) would RED, the row catches it
        def blind_tracks(name):
            return {"tracks": True, "reason": "shadow-diff empty", "window_at_version": None,
                    "missing": [], "extra": [], "differing": []}
        with mock.patch.object(shadows, "tracks", blind_tracks):
            served = shadows.current("m1-connection-state")
            self.assertTrue(served["claims_currency"])
            self.assertNotIn(ghost, served["table"])           # the divergence served, unseen

        # RESTORE: the guard back, the divergence halts again -> A3(i) GREEN
        with self.assertRaises(shadow.StaleShadow):
            shadows.current("m1-connection-state")


# =============================================================================================
# R2 — a FALSE halt (the second failure direction; a unit testing only R1 ships half the law)
# =============================================================================================

class TestR2FalseHalt(_Composed):
    def test_a_stuck_differing_forces_a_false_halt_reds_A3ii_restore_greens(self):
        w, shadows = self._pump_tracking()

        # REMOVED (honest check): a genuine tracking state SERVES -> A3(ii) GREEN
        self.assertTrue(shadows.current("m1-connection-state")["claims_currency"])

        # PRESENT (tracks stuck non-empty though the two agree): current() HALTS a LAWFUL
        # assume -> A3(ii) would RED, the second failure direction the row catches
        stuck_key = "tcp:<LOOPBACK-PORT>-2.2.2.2:2"

        def stuck_tracks(name):
            return {"tracks": False, "reason": "shadow-diff non-empty", "window_at_version": None,
                    "missing": [], "extra": [], "differing": [stuck_key]}
        with mock.patch.object(shadows, "tracks", stuck_tracks):
            with self.assertRaises(shadow.StaleShadow) as cm:
                shadows.current("m1-connection-state")
            self.assertEqual(cm.exception.drift["differing"], [stuck_key])

        # RESTORE: the honest check back, the lawful assume serves again -> A3(ii) GREEN
        self.assertTrue(shadows.current("m1-connection-state")["claims_currency"])


# =============================================================================================
# R3 — a NAKED SWAP is refused ("only on proof" is mechanical, not a note)
# =============================================================================================

class TestR3NakedSwapRefused(unittest.TestCase):
    PROVEN = {"sustained_empty": True, "halt_seeded_divergence": True, "halt_no_false": True}

    def test_a_retirement_with_any_proof_absent_is_refused_and_a_proven_one_permits(self):
        # PRESENT (a naked swap: at least one proof absent) -> REFUSED, citing the ledger law
        for absent in ("sustained_empty", "halt_seeded_divergence", "halt_no_false"):
            m = dict(self.PROVEN)
            m[absent] = False
            with self.assertRaises(shadow.NakedSwapRefused) as cm:
                shadow.retire_linux_authority("connection", m, target="some-governed-view")
            self.assertIn("maturation not proven", cm.exception.reason)
            self.assertEqual(cm.exception.citation, shadow.RETIREMENT_LAW)

        # REMOVED (proven AND a real target) -> PERMITTED: the gate is not a check that cannot pass
        d = shadow.retire_linux_authority("connection", self.PROVEN, target="some-governed-view")
        self.assertEqual(d["retired"], "connection")
        self.assertEqual(d["cites"], shadow.RETIREMENT_LAW)
        self.assertEqual(d["on_proof"], self.PROVEN)


# =============================================================================================
# A4 — retirement on proof, OR the raise
# =============================================================================================

class TestA4RetirementOrRaise(_Composed):
    """A4 — RE-EXPRESSED at EP-48-BUILD under archi's Option A ruling (:3274), a by-name precision
    riding the :3266 countersign (NO re-freeze). :2646 IS NOW DISCHARGED.

    WHY THIS IS A MEANING RE-EXPRESS AND NOT A SWEEP MEMBER (§A57 MEANING-VERSUS-RANGE, an
    S-stop). When this row shipped (EP-30-C5), the connection subsystem was OBSERVE-ONLY —
    OBSERVE-CONNECTION was its entire op surface — so no governed-authoritative connection view
    existed to retire INTO, and the retirement was the RAISE (:2646, a swap into a void). EP-48
    (SOCKET-GRANTS, the campaign-5 founding mover) mints the six wire ops and derives the
    socket-table fold (src/subsystems/sockets.py `connection_view`), which IS the governed
    connection view. So the CLAIM this row makes changes: the retirement no longer refuses for
    want of a target — it PERMITS on proof, the target being the socket fold. A change to WHAT
    the row asserts is an S-stop re-expression made under a ruling, never a count bumped in place.

    PART 1 (mechanical, same ruling): the CONN filter is narrowed to the OBSERVE FAMILY so
    SOCKET-CONNECT — a wire DECISION op that carries "CONN" in its name — does not trip "the
    observe family's only op is OBSERVE-CONNECTION". The observe family is unchanged, which is the
    point: EP-48 adds a governed WIRE op, not a second observe op.

    THE PROOF that licenses the permit is test_ep48 A3 (T-SHADOW-RETIRED-INTO-VIEW): the socket
    fold reproduces the shadow's mature diff-empty under the churn battery, BOTH directions. This
    row asserts the retirement's SHAPE given that proof; test_ep48 A3 drives the proof itself."""

    PROVEN = {"sustained_empty": True, "halt_seeded_divergence": True, "halt_no_false": True}

    def test_the_shadow_retires_into_the_socket_fold_2646_discharged(self):
        # PART 1 — the OBSERVE FAMILY, narrowed. The observe plane's connection op is STILL exactly
        # OBSERVE-CONNECTION; SOCKET-CONNECT is a WIRE DECISION (EP-48), not an observe op, so the
        # narrowed filter excludes it and this claim keeps its reach over the observe plane.
        self.assertEqual(OP_FOR_WINDOW["connection"], "OBSERVE-CONNECTION")
        observe_conn_ops = sorted(name for name in self.gate.ops
                                  if name.startswith("OBSERVE") and "CONN" in name.upper())
        self.assertEqual(observe_conn_ops, ["OBSERVE-CONNECTION"],
                         f"a second OBSERVE connection op appeared: {observe_conn_ops}")

        # PART 2 — :2646 DISCHARGED. A governed-authoritative connection view now EXISTS: the
        # socket-table fold. Imported HERE (not at file top) so this method — and only this method
        # — is the one that requires the new world; on the pre-EP-48 tree it ERRORS at this import
        # because the target it asserts the retirement permits into DID NOT EXIST (the void :2646
        # named), which is precisely the world-change this re-express tracks (extent-assertor).
        from subsystems.sockets import SocketView
        target = SocketView(self.store).connection_view          # the governed connection view
        self.assertTrue(callable(target))

        # With the maturation proven (test_ep48 A3) AND that real target, the SAME gate that
        # refused the void at EP-30-C5 now PERMITS — the shadow retires INTO the socket fold.
        d = shadow.retire_linux_authority("connection", self.PROVEN, target=target)
        self.assertEqual(d["retired"], "connection")
        self.assertEqual(d["into"], target)
        self.assertEqual(d["cites"], shadow.RETIREMENT_LAW)
        self.assertEqual(d["on_proof"], self.PROVEN)

        # and the retirement is STILL licensed only by proof: strip any half of the maturation and
        # the SAME real target refuses (a naked swap) — this is not a gate that cannot refuse.
        for absent in self.PROVEN:
            m = dict(self.PROVEN); m[absent] = False
            with self.assertRaises(shadow.NakedSwapRefused) as cm:
                shadow.retire_linux_authority("connection", m, target=target)
            self.assertIn("maturation not proven", cm.exception.reason)


# =============================================================================================
# The real-world anchor — the LIVE sock_diag window tracks real connections I make
# =============================================================================================

class TestRealWorldAnchor(_Composed):
    @staticmethod
    def _accept(srv, held):
        while True:
            try:
                conn, _ = srv.accept()
                held.append(conn)
            except OSError:
                return

    def test_the_live_sock_diag_window_tracks_real_loopback_connections(self):
        w = ConnectionWindow()
        ok, _ = w.available()
        if not ok or w.route != "sock_diag":
            self.skipTest("sock_diag route unavailable on this box")
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(5)
        port = srv.getsockname()[1]
        held, clients = [], []
        threading.Thread(target=self._accept, args=(srv, held), daemon=True).start()
        try:
            for _ in range(4):
                c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                c.connect(("127.0.0.1", port))
                clients.append(c)
            time.sleep(0.2)
            shadows = self._shadows([w])
            self.seam.submit_all(w.read())                     # real connections -> real records
            table = shadows.answer("m1-connection-state")["table"]
            mine = [k for k in table if f":{port}-" in k or f"-127.0.0.1:{port}" in k]
            self.assertTrue(mine, "the live window recorded none of the connections I made")
            # AMONG MY OWN KEYS the shadow and the live box agree — robust to background churn on
            # unrelated connections (a live full-table diff is NOT asserted: it flaps on a busy
            # box, which is why the SUSTAINED proof, A2, uses the injected battery).
            t = shadows.tracks("m1-connection-state")
            drift_mine = [k for k in (t["missing"] + t["extra"] + t["differing"])
                          if f":{port}-" in k or f"-127.0.0.1:{port}" in k]
            self.assertEqual(drift_mine, [], f"my own connections drifted: {drift_mine}")
        finally:
            for c in clients:
                c.close()
            for c in held:
                c.close()
            srv.close()


if __name__ == "__main__":
    unittest.main()
