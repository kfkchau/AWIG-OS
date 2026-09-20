# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test ·
# OS-architecture vocabulary (gate, view servicing, recorded read, border crossing) as in the
# seL4/gVisor literature. NON-GOAL: no offensive capability of any kind — this battery proves that a
# read THROUGH THE GATE is a recorded act and an outside institution's read is a row under the asked
# institution's own law, by function over the mechanisms C5 already built. Full: SCOPE-STATEMENT.md.
"""P13 — READING THROUGH THE GATE (design/52 B9:58, I13:85; K7:195 carried).

Named in planning/exec/P13-READING-THROUGH-THE-GATE-BUILD.md before code, landed here as regression
tests (charter: every verification probe lands as a regression test). GREEN — proven over existing
mechanisms (views.VIEW-SERVICE / paper_tigers, N6; the border-in/out path), NOT a new op, law or
check kind, no pack edit, no bump. views.py is READ, not edited: the crossing itself is a row BY
CONSTRUCTION at the border, and forcing the VIEW-SERVICE signal to precede every serve would need a
new op (stop-a) — out of scope for GREEN.

THE LOAD-BEARING VERDICT this battery pins (archi's dispatch word), read from the code path:

  * BY CONSTRUCTION at the border — an outside institution's bytes cross the door ONLY as the
    payload of a gate-appended record. The crossing IN is a BORDER-SUBMIT the gate DECIDES before any
    effect (a refused submit leaves NO row — ep49a RW-EFFECT-BEFORE-DECISION); the bytes OUT ride the
    `shown` field of a gate-appended BORDER-REPLY, and with the seal library absent the reply REFUSES
    rather than delivering unsealed (real-or-refused, N10). There is no out-of-band delivery channel,
    so "an outside institution receives bytes with no row" cannot occur — it is impossible by
    construction, not caught after the fact. (A3.)

  * CAUGHT for the mandated-view SERVICING SIGNAL — VIEW-SERVICE (N6, "servicing is a record",
    views.py:883) is an explicit governance op, wired to NO serve site; paper_tigers (views.py:877)
    reads it as an AFTER-THE-FACT derivation and names a mandated view that carries no VIEW-SERVICE
    row (delivery retained as a second witness). This is the check that can fail (A2), not a
    by-construction pre-append.

K7's one sentence, CARRIED not minted (design/52 K7:195, carried in I13:85): reading is a row
IMPOSSIBLE THROUGH THE GATE; a disk-level raw read is not this gate's — it stays the disk-lock cap of
C4 and C7's hardware. (A4.)
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel import border, crypto                                    # noqa: E402

DESIGN_52 = os.path.join(os.path.dirname(__file__), "..",
                         "design", "52-CAMPAIGN-6-SELF-ORCHESTRATED-INSTITUTIONS.md")


def _kernel(prefix):
    """A full kernel (the pack ops registered, so VIEW-SERVICE and the border ops are live)."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    return store, gate, views


# =============================================================================================
# A1 — A READ THROUGH THE GATE IS A ROW: servicing a mandated view appends a VIEW-SERVICE decision.
# =============================================================================================

class TestReadThroughTheGateIsARow(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("p13-a1-")
        # a mandated MASTER view (no move_to): its read is a governed act with a recorded servicing.
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "rule-master", "bind": "active_rules", "refresh": "hourly"})

    def test_servicing_a_mandated_view_appends_a_row_in_the_servicers_own_record(self):
        """B9/I13: servicing (reading) a mandated view through the gate appends a VIEW-SERVICE
        DECISION carrying WHO (servicer), WHEN (this record's seq), OVER-WHICH-HEAD (head_seq). The
        read IS a row — a governed act on the record, not an invisible side effect."""
        head = len(self.store.all())
        rec = self.gate.execute("VIEW-SERVICE", "worker", {"view_name": "rule-master", "head_seq": head})
        self.assertEqual(rec["action"], "VIEW-SERVICE")
        p = rec.get("payload") or {}
        self.assertEqual(p.get("kind"), "view_service")
        self.assertEqual(p.get("record_class"), "DECISION")           # the servicer's own act
        self.assertEqual(p.get("view_name"), "rule-master")           # WHICH view was read
        self.assertEqual(p.get("head_seq"), head)                     # OVER-WHICH-HEAD
        self.assertEqual(p.get("servicer"), "worker")                 # WHO — stamped from the actor
        # the read is a row on the record, keyed by its own seq (WHEN re-derives from the store).
        svc = self.store.by_action("VIEW-SERVICE")
        self.assertEqual(len(svc), 1)
        self.assertEqual((svc[0].get("payload") or {}).get("view_name"), "rule-master")

    def test_the_read_row_is_attributed_to_the_reader_not_the_callers_claim(self):
        """One pen per record (I1): the servicer is the engine's fact, stamped from the acting actor,
        so a read cannot be attributed to another body. A supplied `servicer` is overwritten."""
        head = len(self.store.all())
        rec = self.gate.execute("VIEW-SERVICE", "alice",
                                {"view_name": "rule-master", "head_seq": head, "servicer": "bob"})
        self.assertEqual((rec.get("payload") or {}).get("servicer"), "alice")   # NOT the claimed "bob"


# =============================================================================================
# A2 — A GATE-READ WITH NO ROW IS CAUGHT (the paper-tiger positive control: the check can fail).
# =============================================================================================

class TestGateReadWithNoRowIsCaught(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("p13-a2-")
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "rule-master", "bind": "active_rules", "refresh": "hourly"})

    def test_a_mandated_view_with_no_VIEW_SERVICE_row_is_NAMED_the_positive_control(self):
        """THE CHECK THAT CAN FAIL: a mandated view whose read left NO VIEW-SERVICE row is caught by
        paper_tigers (after the fact), named with the recorded fact 'no VIEW-SERVICE record'. A check
        that can never red is the defect — this is the red world, driven through the instrument."""
        tigers = {t["name"]: t["reason"] for t in self.views.paper_tigers()}
        self.assertIn("rule-master", tigers)                          # CAUGHT: named a paper tiger
        self.assertIn("VIEW-SERVICE", tigers["rule-master"])          # by the recorded fold, not a cap

    def test_with_the_read_row_present_the_view_is_no_longer_caught(self):
        """The other arm: once the read IS a row (a VIEW-SERVICE record over the head), the mandated
        view clears — the catch is a fold over the record, so it moves the moment the record does."""
        self.gate.execute("VIEW-SERVICE", "worker",
                          {"view_name": "rule-master", "head_seq": len(self.store.all())})
        self.assertNotIn("rule-master", {t["name"] for t in self.views.paper_tigers()})


# =============================================================================================
# A3 — AN OUTSIDE INSTITUTION'S READ IS A ROW UNDER THE ASKED INSTITUTION'S LAW.
#      The outside entity asks the FRONT DOOR (crosses IN); the asked institution reads its own view
#      and records its OWN servicing; the requester's record is unchanged (one pen per record). The
#      crossing itself is a row BY CONSTRUCTION — the verdict, landed as a regression test.
# =============================================================================================

class TestOutsideInstitutionReadUnderAskedLaw(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("p13-a3-")
        # the ASKED institution's mandated view (its own front door reads it under its own law).
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "rule-master", "bind": "active_rules", "refresh": "hourly"})
        # an OUTSIDE institution, established on the record (a crossing opens an established channel;
        # BORDER-SUBMIT admits no peer-minted token as identity — the entity must exist on the record).
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "peer", "actor_class": "human"})

    def test_the_outside_read_crosses_IN_through_the_front_door_as_a_gate_decided_row(self):
        """B9: upward accountability is asking the child's FRONT DOOR, never reaching in. The outside
        institution submits a read request; it crosses IN as a BORDER-SUBMIT the gate DECIDES against
        the record, attributed to the entity that willed it — a row, not a reach-in."""
        sub = border.submit(self.gate, "peer", {"want": "read rule-master"})
        self.assertEqual(sub["action"], "BORDER-SUBMIT")
        self.assertEqual(sub["actor"], "peer")                        # willed by the outside entity
        self.assertEqual(sub["rule_cited"], "COMM-LAW-CONTRACT")      # under the channel-contract law
        self.assertIn(border.content_id(sub), border.submits(self.store))   # the crossing is a fold

    def test_the_read_is_the_ASKED_institutions_own_row_requester_record_unchanged(self):
        """B9 / one pen per record (I1): the outside entity asks; the ASKED institution reads its own
        view and records the servicing as ITS OWN act (servicer = the asked institution). The
        requester wrote only its crossing-in — no VIEW-SERVICE row is attributed to the requester."""
        border.submit(self.gate, "peer", {"want": "read rule-master"})
        # the asked institution (owner) services its own view under its own law:
        head = len(self.store.all())
        svc = self.gate.execute("VIEW-SERVICE", "owner", {"view_name": "rule-master", "head_seq": head})
        self.assertEqual((svc.get("payload") or {}).get("servicer"), "owner")   # the ASKED institution
        self.assertEqual(svc["rule_cited"], "ROOT-NEG-6")             # under the asked institution's law
        # the requester's record is UNCHANGED: no VIEW-SERVICE row bears the outside entity's pen.
        service_rows = self.store.by_action("VIEW-SERVICE")
        self.assertTrue(service_rows)
        self.assertFalse([r for r in service_rows if r["actor"] == "peer"],
                         "an outside entity wrote the asked institution's servicing row — one pen "
                         "per record broken")

    def test_the_crossing_carries_the_bytes_BY_CONSTRUCTION_no_out_of_band_delivery(self):
        """THE VERDICT, as a regression test: an outside institution's bytes cross the door ONLY
        inside a gate-appended record — there is no out-of-band delivery, so a delivery with no row is
        impossible BY CONSTRUCTION (not merely caught).

          crossing IN  — a refused BORDER-SUBMIT leaves NO row (the gate DECIDES before any effect);
                         so nothing crosses in without a row. (RW-EFFECT-BEFORE-DECISION.)
          bytes  OUT   — the shown bytes ride the `shown` field of a gate-appended BORDER-REPLY, and
                         with the seal library ABSENT the reply REFUSES rather than delivering
                         unsealed (real-or-refused, N10). Either way the bytes never leave except as
                         a row's payload."""
        # crossing IN: a refused draft produces its refusal and NO border-submit row.
        before = len(list(self.store.by_action("BORDER-SUBMIT")))
        with self.assertRaises(OpError):
            border.submit(self.gate, "ghost", {"want": "read rule-master"})   # unestablished entity
        self.assertEqual(len(list(self.store.by_action("BORDER-SUBMIT"))), before)   # nothing crossed in

        # bytes OUT: the reply is the sole carrier, and it is a gate-appended record — or it refuses.
        from kernel.signer import SigningKeyStore
        sub = border.submit(self.gate, "peer", {"want": "read rule-master"})
        shown = {"answer": "granted", "view": "rule-master"}
        s = SigningKeyStore()
        custody = s.seal(bytes(range(32)))            # seal is a hash handle; never needs the library
        if not crypto.real_available():
            # ABSENT (this estate's baseline): no faked delivery — the reply REFUSES. No bytes leave.
            with self.assertRaises(crypto.LibraryAbsent):
                border.reply(self.gate, self.store, s, custody, sub, shown)
        else:
            rec = border.reply(self.gate, self.store, s, custody, sub, shown)
            self.assertEqual(rec["action"], "BORDER-REPLY")           # bytes cross out AS a row
            self.assertEqual((rec.get("payload") or {}).get("shown"), shown)   # only inside the row


# =============================================================================================
# A4 — K7 CARRIED: the invariant's one sentence states the scope, carried in the paper, not minted.
# =============================================================================================

@unittest.skipUnless(
    os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design/52-CAMPAIGN-6-SELF-ORCHESTRATED-INSTITUTIONS.md")),
    "SKIP PRIVATE-SOURCE: needs design/52-CAMPAIGN-6-SELF-ORCHESTRATED-INSTITUTIONS.md (absent in the render)")
class TestK7Carried(unittest.TestCase):
    def _design_52(self):
        with open(DESIGN_52, encoding="utf-8") as f:
            return f.read()

    def test_I13_carries_K7s_one_sentence_scope(self):
        """K7 is a CARRIED conflict, not this unit's to mint: I13's one sentence carries the cap that
        a disk-level read is not this gate's. Read the paper — the scope rides I13, referencing K7."""
        text = self._design_52()
        i13 = next(ln for ln in text.splitlines() if ln.startswith("- **I13"))
        self.assertIn("impossible by construction", i13)              # every gate-read is a row
        self.assertIn("K7", i13)                                      # the cap carried, named

    def test_K7_states_the_scope_boundary_gate_reads_not_raw_disk_reads(self):
        """The carried sentence, verbatim in the paper: impossible THROUGH THE GATE; a disk-level read
        stays the disk-lock cap of C4 and C7's hardware. Carried, not re-minted here — no new rule
        record, no code guard; the scope lives in the paper and is echoed in this module's docstring."""
        text = self._design_52()
        k7 = next(ln for ln in text.splitlines() if ln.startswith("- **K7"))
        self.assertIn("impossible through the gate", k7)
        self.assertIn("disk-level read", k7)
        # echoed where the mechanism lives, so a reader of the test sees the scope (carried, not minted):
        self.assertIn("impossible through the gate", sys.modules[__name__].__doc__.lower())


if __name__ == "__main__":
    unittest.main()
