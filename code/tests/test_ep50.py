"""EP-50 — VIEW-SERVICING AND THE FOLD SET (design/51 N6, §4, §6 item 4, §8, §9).

Named in planning/exec/EP-50-BUILD.md before code, landed here as regression tests (charter:
every verification probe lands as a regression test). This battery proves that a mandated view's
SERVICING is a record and that the fold library a MASTER may bind is a declared, attested set:

  A1  servicing a mandated view appends a VIEW-SERVICE DECISION carrying (view name, head seq
      serviced, servicer); the record re-derives who/when/over-which-head; a SECOND servicing
      appends a SECOND record (append-only, no overwrite).
  A2  a mandated MASTER view with NO VIEW-SERVICE record over the current head is NAMED a paper
      tiger (the v1 gap closed — a master's servicing was unrecordable); a serviced MASTER is NOT.
  A3  a mandated FILTER view that has DELIVERED but carries no VIEW-SERVICE record is NOT a paper
      tiger — DELIVERY is retained as a SECOND WITNESS (design/51 §6 item 4).
  A4  FOLD_NAMES is a declared attested member set with a set_digest (the EP-40 twin); a CREATE-VIEW
      MASTER binding a fold OUTSIDE the set is refused as today; the set is CITABLE and grow-only.
  A5  the extended ledger, BOTH directions: (too weak) a mandated MASTER never serviced now REDS as
      a paper tiger; (too wedged) a serviced or delivered mandated view still PASSES.
  A6  the founding move mints VIEW-SERVICE as a data-born MINOR bump (1.43.0 -> 1.44.0), attested in
      ONE entry; the op-population census moves 91 -> 92 by name; NO check kind (OP_CHECKS unchanged).

THE WRONG REFERENCE REFUSED BY NAME (design/51 §5, §9): the materialized view / stored procedure — a
definition stored as a code blob in a row, the record depending on an engine to be read. Here the fold
FUNCTIONS stay CODE (mechanism, S-plane, air rider 1); VIEW-SERVICE records only the servicing
DECISION (who/when/head), never a fold's code, and paper_tigers folds OVER the record. THE ONE
PRECISION (architect board :3377): VIEW-SERVICE cites the SAME founded law CREATE-VIEW cites
(ROOT-NEG-6) — no new law is minted.

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect, §A42/§A64).
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.opdefs import OP_CHECKS                                   # noqa: E402
from kernel.views import FOLD_NAMES, fold_set                         # noqa: E402
from kernel.canonical import canonical_hash                          # noqa: E402


def _kernel(prefix):
    """A full kernel (the pack ops registered, so VIEW-SERVICE is live), its store, gate and views."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, blobs, subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    return store, gate, views


def _trivial(gate, action):
    """Register a trivial ordinary op so a delivery record can be authored (the test_ep10 idiom)."""
    gate.register(action, {"description": f"echo {action}", "rules": ["ROOT-NEG-5"], "params": {}},
                  lambda actor, params: {"actor": actor, "action": action, "object": "x",
                                         "rule_cited": "ROOT-NEG-5"})


# =============================================================================================
# A1 — T-VIEW-SERVICE-RECORDED: the servicing is a record
# =============================================================================================

class TestViewServiceRecorded(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("ep50-a1-")
        # a mandated MASTER view (no move_to) — the v1 gap: in v1 it had NO recorded per-run signal.
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "rule-master", "bind": "active_rules", "refresh": "hourly"})

    def test_servicing_appends_a_VIEW_SERVICE_decision_carrying_who_when_head(self):
        """N6: servicing a mandated view appends a VIEW-SERVICE DECISION carrying the view name, the
        head seq serviced over, and the servicer. The servicer is the ENGINE'S fact (stamped from the
        acting actor), never the caller's claim; who/when/head re-derive from the record itself."""
        head = len(self.store.all())
        rec = self.gate.execute("VIEW-SERVICE", "worker", {"view_name": "rule-master", "head_seq": head})
        self.assertEqual(rec["action"], "VIEW-SERVICE")
        self.assertEqual(rec["object"], "view:rule-master")             # object derived view:{name}
        p = rec.get("payload") or {}
        self.assertEqual(p.get("kind"), "view_service")
        self.assertEqual(p.get("record_class"), "DECISION")            # the servicer's own act
        self.assertEqual(p.get("view_name"), "rule-master")            # WHICH view
        self.assertEqual(p.get("head_seq"), head)                      # OVER-WHICH-HEAD
        self.assertEqual(p.get("servicer"), "worker")                 # WHO (stamped from actor)
        self.assertEqual(rec["rule_cited"], "ROOT-NEG-6")             # the SAME law CREATE-VIEW cites
        # WHEN re-derives from the record — the VIEW-SERVICE record is on the store, keyed by its seq.
        svc = self.store.by_action("VIEW-SERVICE")
        self.assertEqual(len(svc), 1)
        self.assertEqual((svc[0].get("payload") or {}).get("view_name"), "rule-master")

    def test_the_servicer_is_stamped_from_the_actor_not_the_callers_claim(self):
        """The servicer is the engine's fact: a caller cannot attribute a servicing to another
        entity — the stamp overwrites any supplied `servicer`, so identity is unforgeable here."""
        head = len(self.store.all())
        rec = self.gate.execute("VIEW-SERVICE", "alice",
                                {"view_name": "rule-master", "head_seq": head, "servicer": "bob"})
        self.assertEqual((rec.get("payload") or {}).get("servicer"), "alice")   # NOT the claimed "bob"

    def test_a_second_servicing_appends_a_second_record_append_only(self):
        """N6 / append-only: a second servicing appends a SECOND VIEW-SERVICE record — the record
        never overwrites (a servicing history accretes, one row per servicing)."""
        self.gate.execute("VIEW-SERVICE", "worker", {"view_name": "rule-master", "head_seq": 1})
        self.gate.execute("VIEW-SERVICE", "worker", {"view_name": "rule-master", "head_seq": 5})
        svc = self.store.by_action("VIEW-SERVICE")
        self.assertEqual(len(svc), 2)                                  # TWO records, append-only
        self.assertEqual([(s.get("payload") or {}).get("head_seq") for s in svc], [1, 5])

    def test_RW_the_head_seq_param_is_declared_structural_a_conforming_call_is_admitted(self):
        """stop-g / the door-layer acceptance: a fresh CREATE-OP declares ALL its read params
        STRUCTURAL or the door refuses a conforming call. A VIEW-SERVICE call carrying the view name
        and the head seq is ADMITTED and recorded — the op-META door-param gap does not apply here."""
        head = len(self.store.all())
        rec = self.gate.execute("VIEW-SERVICE", "SYSTEM", {"view_name": "rule-master", "head_seq": head})
        self.assertEqual((rec.get("payload") or {}).get("kind"), "view_service")


# =============================================================================================
# A2 — T-PAPER-TIGER-BY-FOLD: a mandated MASTER is named (the v1 gap closed)
# =============================================================================================

class TestPaperTigerByFold(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("ep50-a2-")
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "rule-master", "bind": "active_rules", "refresh": "hourly"})

    def test_a_mandated_master_with_no_VIEW_SERVICE_record_is_named(self):
        """A2: a mandated MASTER (no move_to) with NO VIEW-SERVICE record is NAMED a paper tiger, its
        reason the recorded fact ('no VIEW-SERVICE record'), not the old v1 honest-cap non-signal."""
        tigers = {t["name"]: t["reason"] for t in self.views.paper_tigers()}
        self.assertIn("rule-master", tigers)
        self.assertIn("VIEW-SERVICE", tigers["rule-master"])          # named by the recorded fold, not a cap

    def test_a_serviced_master_is_not_named(self):
        """A2: a MASTER with a VIEW-SERVICE record over the current head is NOT named — the v1 gap
        closed: a mandated MASTER's servicing is now recordable and clears it."""
        self.gate.execute("VIEW-SERVICE", "worker",
                          {"view_name": "rule-master", "head_seq": len(self.store.all())})
        self.assertNotIn("rule-master", {t["name"] for t in self.views.paper_tigers()})


# =============================================================================================
# A3 — T-DELIVERY-SECOND-WITNESS: delivery is retained beside the servicing record
# =============================================================================================

class TestDeliverySecondWitness(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("ep50-a3-")

    def test_a_delivered_filter_view_with_no_VIEW_SERVICE_record_is_not_a_paper_tiger(self):
        """A3 / design/51 §6 item 4: a mandated FILTER view that has DELIVERED (its move_to queue is
        non-empty) but carries NO VIEW-SERVICE record is NOT a paper tiger — the delivery signal is
        retained as a SECOND WITNESS. Proven by a view green on DELIVERY ALONE (no servicing record)."""
        self.gate.execute("CREATE-VIEW", "owner", {"name": "busy", "when": {"action": "FROB"},
                                                   "then": {"move_to": "busy-inbox"}, "refresh": "hourly"})
        _trivial(self.gate, "FROB")
        self.gate.execute("FROB", "x", {})                            # a delivery -> busy-inbox queue
        self.assertEqual(self.store.by_action("VIEW-SERVICE"), [])    # NO servicing record exists
        self.assertNotIn("busy", {t["name"] for t in self.views.paper_tigers()})   # yet not a paper tiger

    def test_a_mandated_filter_view_that_delivered_nothing_is_still_a_paper_tiger(self):
        """The second witness is a WITNESS, not a blanket clear: a mandated FILTER view that delivered
        NOTHING and has no VIEW-SERVICE record IS a paper tiger (the check that can fail)."""
        self.gate.execute("CREATE-VIEW", "owner", {"name": "idle", "when": {"action": "FROB"},
                                                   "then": {"move_to": "idle-inbox"}, "refresh": "hourly"})
        self.assertIn("idle", {t["name"] for t in self.views.paper_tigers()})


# =============================================================================================
# A4 — T-FOLD-SET-ATTESTED: the fold library is a declared, attested, grow-only, citable set
# =============================================================================================

class TestFoldSetAttested(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("ep50-a4-")

    def test_the_fold_set_is_a_declared_attested_set_with_a_set_digest(self):
        """A4: fold_set() is the EP-40 twin — a declared member set with a citable set_digest over
        the sorted names, through the estate's ONE canonical hash. CITABLE: any reader recomputes the
        digest from the declared names (a record may name it)."""
        fs = fold_set()
        self.assertEqual(fs["kind"], "fold_set")
        self.assertEqual(fs["members"], tuple(sorted(FOLD_NAMES)))
        self.assertEqual(fs["set_digest"], canonical_hash(tuple(sorted(FOLD_NAMES))))   # recomputable = citable
        self.assertEqual(fold_set()["set_digest"], fs["set_digest"])                    # deterministic

    def test_a_master_binding_a_fold_outside_the_set_is_refused_as_today(self):
        """A4: the closure discipline is KEPT over the now-attested set — a CREATE-VIEW MASTER binding
        a fold OUTSIDE FOLD_NAMES is refused (the check that can fail); a bind to a MEMBER is admitted."""
        with self.assertRaises(OpError):
            self.gate.execute("CREATE-VIEW", "owner", {"name": "bad", "bind": "not_a_fold"})
        rec = self.gate.execute("CREATE-VIEW", "owner", {"name": "good", "bind": "actors"})
        self.assertEqual((rec.get("payload") or {}).get("bind"), "actors")

    def test_the_set_is_grow_only_the_declared_baseline_members_are_all_present(self):
        """A4: grow-only — the pinned baseline (the seven declared folds) must ALL remain a member; a
        shrink (removing any) REDS this pin, and adding a fold moves the set_digest (grow is visible)."""
        members = set(fold_set()["members"])
        for fold in ("active_rules", "actors", "resources", "permissions", "relationships",
                     "op_definitions", "view_definitions"):
            self.assertIn(fold, members)                              # a shrink would fail here
        # grow is visible: a superset yields a DIFFERENT digest (the set is measured, not a bare list).
        grown = canonical_hash(tuple(sorted(FOLD_NAMES + ("a_new_fold",))))
        self.assertNotEqual(grown, fold_set()["set_digest"])


# =============================================================================================
# A5 — T-EXTENDED-LEDGER: both directions provable
# =============================================================================================

class TestExtendedLedger(unittest.TestCase):
    def setUp(self):
        self.store, self.gate, self.views = _kernel("ep50-a5-")
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "rule-master", "bind": "active_rules", "refresh": "hourly"})

    def test_too_weak_a_mandated_master_never_serviced_reds_as_a_paper_tiger(self):
        """(too weak) a mandated MASTER never serviced now REDS as a paper tiger — the v1 gap, where a
        master's servicing was unrecordable, is closed: an un-serviced master is NAMED."""
        self.assertIn("rule-master", {t["name"] for t in self.views.paper_tigers()})

    def test_too_wedged_a_serviced_master_passes(self):
        """(too wedged) a serviced mandated view still PASSES — servicing on the record clears it."""
        self.gate.execute("VIEW-SERVICE", "worker",
                          {"view_name": "rule-master", "head_seq": len(self.store.all())})
        self.assertNotIn("rule-master", {t["name"] for t in self.views.paper_tigers()})

    def test_too_wedged_a_delivered_filter_view_passes(self):
        """(too wedged) a delivered mandated FILTER view still PASSES — the second witness holds."""
        self.gate.execute("CREATE-VIEW", "owner", {"name": "busy", "when": {"action": "FROB"},
                                                   "then": {"move_to": "busy-inbox"}, "refresh": "hourly"})
        _trivial(self.gate, "FROB")
        self.gate.execute("FROB", "x", {})
        self.assertNotIn("busy", {t["name"] for t in self.views.paper_tigers()})


# =============================================================================================
# A6 — T-FOUNDING-BUMP-ATTESTED (MINOR; version + pack sha in one log entry); census by name
# =============================================================================================

def _pack_records():
    repo = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(repo, "src", "founding", "founding-pack.json"), "rb") as fh:
        return [r for step in json.loads(fh.read())["steps"] for r in step["records"]]


class TestFoundingBump(unittest.TestCase):
    def test_the_founding_is_at_or_beyond_the_EP50_era_and_the_bump_is_attested(self):
        """A6: the founding rose one MINOR (1.43.0 -> 1.44.0, the base driven at dispatch) and the
        move is attested in ONE BUILD-PROGRESS entry (version + pack sha256). ERA-PINNED from birth
        (§A57, the manager's test_ep48 model): the version is a FLOOR at the EP-50 era, so a later
        founding mover advances the constitution WITHOUT touching this line."""
        from test_founding_is_logged import audit, pack_facts
        facts = pack_facts()
        ver = tuple(int(x) for x in facts["version"].split("."))
        self.assertGreaterEqual(ver, (1, 44, 0),
                                "the founding is at or beyond the EP-50 era (1.44.0) this test pins")
        a = audit()
        self.assertTrue(a["logged"],
                        "the founding moved and no single BUILD-PROGRESS entry names both the version "
                        "and the pack sha256 (the required ledger duty, :1178/:2805)")

    def test_VIEW_SERVICE_is_in_the_pack_with_params_declared_and_the_move_is_MINOR(self):
        """A6: VIEW-SERVICE is minted as a CREATE-OP whose TWO read params are declared STRUCTURAL at
        create (view_name, head_seq). The move is MINOR: one op ADDED, NONE removed, NO check kind
        added (OP_CHECKS frozen at 17), the op uses only existing check kinds (none here)."""
        recs = _pack_records()
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertIn("VIEW-SERVICE", op_names)                        # ADDED — the MINOR direction
        rdef = next(r["payload"]["definition"] for r in recs
                    if r.get("action") == "CREATE-OP" and r["payload"]["name"] == "VIEW-SERVICE")
        for param in ("view_name", "head_seq"):
            self.assertIn(param, rdef.get("params", {}))               # declared as a param
            self.assertIn(param, rdef.get("structural_params", []))    # AND classified STRUCTURAL
        self.assertEqual(rdef.get("law_cited"), "ROOT-NEG-6")          # the SAME law CREATE-VIEW cites
        self.assertEqual((rdef.get("payload_derive") or {}).get("record_class", {}).get("tpl"),
                         "DECISION")
        self.assertEqual(rdef.get("checks"), [])                       # VIEW-SERVICE adds no check kind
        # NONE REMOVED: representative pre-move ops survive (a removal would be MAJOR / stop-e).
        for kept in ("RECEIPT", "BORDER-SUBMIT", "SOCKET-OPEN", "COMMS-OPEN", "FILE-CREATE"):
            self.assertIn(kept, op_names)
        self.assertEqual(len(OP_CHECKS), 19)                          # NO check kind added

    def test_the_op_population_census_is_92_moved_by_name(self):
        """A6 / the §A57 census: the op-population is 92 (91 -> 92), the count the test_ep30 pins
        (:187 len(drove), :252 len(set(drove))) enumerate and this founding mover moves BY NAME. A
        DIFFERENT count from OP_CHECKS (a KIND census) — a new OP moves this one, a new KIND the other."""
        recs = _pack_records()
        op_defs = [r for r in recs if (r.get("payload") or {}).get("kind") == "op_definition"
                   and r["payload"].get("name")]
        # [§A57 sweep, EP-52 (FIREWALL-IN-THE-RECORD, FILTER-DECISION, 1.45.0 -> 1.46.0): this LIVE
        #  op-population census moved 92 -> 93 BY NAME — a new OP moves it, the same as EP-50's own
        #  91 -> 92 above. Driven at the EP-52 dispatch, not carried.]
        self.assertEqual(len(op_defs), 93)                            # the op-population census
        self.assertEqual(len({r["payload"]["name"] for r in op_defs}), 93)   # distinct, no double

    def test_RW_NO_MOVE_a_byte_unchanged_founding_would_fail_and_RW_MAJOR_holds(self):
        """RW-NO-MOVE (§4): a founding that moved nothing fails — VIEW-SERVICE IS present (the move
        happened). RW-MAJOR (§4 / stop-e): the discriminator holds — no op removed, no check kind
        added; the move is a single new op, a MINOR."""
        recs = _pack_records()
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertIn("VIEW-SERVICE", op_names)                       # the move happened
        self.assertIn("RECEIPT", op_names)                            # not reached-by-removal (EP-49D's op survives)
        self.assertEqual(len(OP_CHECKS), 19)                          # not reached-by-a-new-kind


if __name__ == "__main__":
    unittest.main()
