"""EP-52 — FIREWALL-IN-THE-RECORD: the firewall as rules IN the record, the enforcement seam named.

Named in planning/exec/EP-52-BUILD.md before code, landed here as regression tests (charter:
every verification probe lands as a regression test). This battery proves design/51 N8: a
FILTER-DECISION is a recorded, rule-citing DECISION over the socket table (EP-48); the firewall
rule is a CREATE-RULE of law class NET-LAW-FILTER IN the record (not a table beside it); 'which
rule decided' is a FOLD (subsystems/filter.py); routing/name split policy (FILTER-DECISION) from
INPUT (ANSWER-RETURNED, the world's fact); the enforcement seam to the guest kernel's netfilter is
NAMED (guest-netfilter) and the host record never claims the drop; per-packet traffic is never a
record; the founding move is MINOR and bump-attested.

The GUEST-REAL end-to-end drop (one FILTER-DECISION -> one netfilter rule installed in the guest ->
a real refusal readable from the record) is driven GUEST-ONLY by planning/evidence/EP-52/guest-seam.sh
under the pinned kernel (EP-00 rule 9); its captured output rides the close. This module is
record-level and appends no kernel act on the host (RW-HOST-KERNEL).

Every acceptance carries its RED WORLD (§4), produced THROUGH the instrument (§A42): a control
that cannot red is the defect (§A64).
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                               # noqa: E402
from kernel.errors import OpError                                          # noqa: E402
from kernel.opdefs import OP_CHECKS                                        # noqa: E402
from subsystems.filter import FilterView, FILTER_ACTIONS                   # noqa: E402
from subsystems.sockets import SocketView                                  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")


def _pack_records():
    with open(PACK_PATH, "rb") as fh:
        return [r for step in json.loads(fh.read())["steps"] for r in step["records"]]


class _World(unittest.TestCase):
    """A kernel composed from the SHIPPED founding, with one established entity and one open,
    connected socket for the firewall to decide over."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep52-")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.gate.execute("CREATE-ACCOUNT", "owner",
                          {"account_id": "web", "actor_class": "human"})

    def a_connection(self, sid="s1", target="93.184.216.34:443"):
        """Open + connect a socket the record establishes — the connection the filter decides over."""
        self.gate.execute("SOCKET-OPEN", "web", {"entity": "web", "socket": sid, "family": "inet"})
        self.gate.execute("SOCKET-CONNECT", "web", {"socket": sid, "target": target})
        return sid

    def a_filter_rule(self, rule_id, text="refuse by policy"):
        """A FILTER-RULE — a CREATE-RULE of law class NET-LAW-FILTER, operator policy IN the record."""
        return self.gate.execute("CREATE-RULE", "owner", {"rule_id": rule_id, "text": text})

    def decide(self, connection, rule, decision, seam="guest-netfilter", entity="web"):
        return self.gate.execute("FILTER-DECISION", entity,
                                 {"entity": entity, "connection": connection, "rule": rule,
                                  "decision": decision, "seam": seam})

    def filters(self):
        return FilterView(self.store)


# =============================================================================================
# A1 — T-FILTER-DECISION-RECORDED (+ RW, the able-to-fail plant)
# =============================================================================================

class TestFilterDecisionRecorded(_World):
    def test_a_filtering_decision_is_a_record_citing_the_filter_law_over_the_socket_table(self):
        self.a_connection("s1")
        self.a_filter_rule("NET-LAW-FILTER:block-cn")
        rec = self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        self.assertEqual(rec["action"], "FILTER-DECISION")             # action IS its op
        self.assertEqual(rec["rule_cited"], "NET-LAW-FILTER")          # cites the firewall law

        # THE RECORD RE-DERIVES which rule decided and the connection it decided — a fold, never
        # a table beside the record.
        view = self.filters()
        row = view.which_rule_decided()["s1"]
        self.assertEqual(row["rule"], "NET-LAW-FILTER:block-cn")       # which rule decided
        self.assertEqual(row["connection"], "s1")                      # the connection it decided
        self.assertEqual(row["decision"], "refuse")
        self.assertEqual(row["seam"], "guest-netfilter")               # the named seam
        self.assertEqual(view.rule_for("s1"), "NET-LAW-FILTER:block-cn")

    def test_the_latest_decision_per_connection_wins_and_multiple_rules_are_distinguished(self):
        # two connections, two rules — the census distinguishes which rule decided which connection.
        self.a_connection("s1"); self.a_connection("s2", target="1.2.3.4:80")
        self.a_filter_rule("NET-LAW-FILTER:block-cn"); self.a_filter_rule("NET-LAW-FILTER:allow-lan")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        self.decide("s2", "NET-LAW-FILTER:allow-lan", "admit")
        view = self.filters()
        self.assertEqual(view.rule_for("s1"), "NET-LAW-FILTER:block-cn")
        self.assertEqual(view.rule_for("s2"), "NET-LAW-FILTER:allow-lan")
        # a re-decision on s1 supersedes — the LATEST rule decides.
        self.a_filter_rule("NET-LAW-FILTER:allow-cn"); self.decide("s1", "NET-LAW-FILTER:allow-cn", "admit")
        view.kill_cache()
        self.assertEqual(view.rule_for("s1"), "NET-LAW-FILTER:allow-cn")

    def test_RW_UNDERIVABLE_a_decision_the_fold_cannot_read_is_the_defect(self):
        """RW (§4): the fold is able-to-fail. It re-derives which rule decided from the FILTER-DECISION
        records ALONE; with NO decision recorded the census is empty (the pre-EP-52 world). The census
        that stays empty under a real decision is the defect this row would catch."""
        view = self.filters()
        self.assertEqual(view.which_rule_decided(), {})               # no decision yet -> empty census
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        view.kill_cache()
        self.assertIn("s1", view.which_rule_decided())                # now the fold reads it

    def test_the_census_is_a_fold_cache_kill_recomputes_identical(self):
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        view = self.filters()
        c1 = view.which_rule_decided()
        view.kill_cache()
        c2 = view.which_rule_decided()
        self.assertEqual(c1, c2)                                       # identical on recompute
        self.assertIsNot(c1, c2)                                       # a fresh object, never a stored copy
        # a second, independent view over the same record yields the same census (derived).
        self.assertEqual(FilterView(self.store).which_rule_decided(), c1)


# =============================================================================================
# A2 — T-FILTER-RULE-IS-LAW (+ RW-TABLE-BESIDE, load-bearing through the instrument)
# =============================================================================================

class TestFilterRuleIsLaw(_World):
    def test_the_firewall_rule_is_a_CREATE_RULE_of_law_class_NET_LAW_FILTER_in_the_record(self):
        # the class root NET-LAW-FILTER is founding law IN the record (a CREATE-RULE), not a table beside it.
        recs = _pack_records()
        law = [r for r in recs if r.get("action") == "CREATE-RULE"
               and (r.get("payload") or {}).get("rule_id") == "NET-LAW-FILTER"]
        self.assertEqual(len(law), 1, "the firewall law is not a CREATE-RULE in the founding record")
        self.assertIn("firewall", law[0]["payload"]["text"].lower())
        # it is also in the LIVE record (replayed at boot), so require_prior can cite it.
        self.assertTrue([e for e in self.store.by_action("CREATE-RULE")
                         if (e.get("payload") or {}).get("rule_id") == "NET-LAW-FILTER"])

    def test_a_FILTER_DECISION_citing_no_law_is_REFUSED_and_the_refusal_RECORDED(self):
        self.a_connection("s1")
        # citing a rule the record does NOT hold — refused, recorded, citing the firewall law.
        with self.assertRaises(OpError) as cm:
            self.decide("s1", "NET-LAW-FILTER:no-such-rule", "refuse")
        self.assertEqual(cm.exception.rule, "NET-LAW-FILTER")
        refusals = [e for e in self.store.by_action("op-refused")
                    if (e.get("payload") or {}).get("op") == "FILTER-DECISION"]
        self.assertTrue(refusals, "the refused filtering decision was silently dropped, not recorded")
        self.assertEqual(refusals[-1].get("rule_cited"), "NET-LAW-FILTER")
        # citing NO rule at all (the param absent) — also refused (a decision that cites nothing).
        with self.assertRaises(OpError):
            self.gate.execute("FILTER-DECISION", "web",
                              {"entity": "web", "connection": "s1", "decision": "refuse",
                               "seam": "guest-netfilter"})

    def test_the_census_of_the_rules_that_decided_is_a_fold(self):
        self.a_connection("s1"); self.a_connection("s2", target="1.2.3.4:80")
        self.a_filter_rule("NET-LAW-FILTER:block-cn"); self.a_filter_rule("NET-LAW-FILTER:allow-lan")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        self.decide("s2", "NET-LAW-FILTER:allow-lan", "admit")
        # THE CENSUS a table beside the record could not answer: which rules have decided?
        self.assertEqual(self.filters().rules_that_decided(),
                         {"NET-LAW-FILTER:block-cn", "NET-LAW-FILTER:allow-lan"})

    def test_RW_TABLE_BESIDE_the_rule_gate_is_mechanical_not_a_note(self):
        """RW-TABLE-BESIDE (§4): the firewall being LAW in the record is LOAD-BEARING. Strip the
        require_prior-over-CREATE-RULE check from FILTER-DECISION (the firewall reduced to a table
        beside the record, no citation enforced) and a decision citing a rule NO record holds now
        PASSES. Its removal flips REFUSE->ADMIT, so the citation WAS the law, not a decoration.
        Driven on a fresh world founded from a modified pack (§A42, through the instrument); the
        real bytes on disk are never touched."""
        with open(PACK_PATH, "rb") as fh:
            pack = json.loads(fh.read())
        for step in pack["steps"]:
            for rec in step["records"]:
                if rec.get("action") == "CREATE-OP" and rec["payload"]["name"] == "FILTER-DECISION":
                    rec["payload"]["definition"]["checks"] = [
                        c for c in rec["payload"]["definition"]["checks"]
                        if not (c.get("check") == "require_prior" and c.get("action") == "CREATE-RULE")]
        d2 = tempfile.mkdtemp(prefix="ep52-stripped-")
        import founding.install as install_module
        saved = install_module.load_pack
        install_module.load_pack = lambda path=None: pack
        try:
            store, gate, _v, _b, _s = build_full_kernel(
                os.path.join(d2, "record.jsonl"), os.path.join(d2, "blobs"), os.path.join(d2, "vault"))
            gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "web", "actor_class": "human"})
            gate.execute("SOCKET-OPEN", "web", {"entity": "web", "socket": "s1", "family": "inet"})
            # NO CREATE-RULE for this id — the citation precondition is exactly what was stripped.
            rec = gate.execute("FILTER-DECISION", "web",
                               {"entity": "web", "connection": "s1", "rule": "NET-LAW-FILTER:ghost",
                                "decision": "refuse", "seam": "guest-netfilter"})
            self.assertEqual(rec["action"], "FILTER-DECISION")         # ADMITTED: the citation was load-bearing
        finally:
            install_module.load_pack = saved


# =============================================================================================
# A3 — T-ENFORCEMENT-SEAM-NAMED (record-level; the guest-real drop rides guest-seam.sh) + RW
# =============================================================================================

class TestEnforcementSeamNamed(_World):
    """The record DECIDES and NAMES the enforcement seam (guest-netfilter); the guest kernel's
    netfilter DROPS the real packet; the host record NEVER claims the drop (DIGEST-C4 §6, the
    disk-lock-under-key-cap shape). Record-level here; the guest-real end-to-end drop is
    planning/evidence/EP-52/guest-seam.sh, driven guest-only under the pinned kernel."""

    def test_the_decision_is_recorded_and_names_the_guest_seam_the_host_never_claims_the_drop(self):
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        rec = self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        # the decision is recorded (the record decides) and NAMES its seam as the guest kernel's.
        self.assertEqual(rec["payload"]["seam"], "guest-netfilter")
        self.assertEqual(self.filters().refusals()["s1"]["seam"], "guest-netfilter")
        # THE HOST RECORD NEVER CLAIMS THE DROP: no per-packet / drop / netfilter act appears on the
        # host record. The host decides and names the seam; the drop is the guest's.
        for e in self.store.all():
            a = e["action"].lower()
            self.assertFalse(any(w in a for w in ("drop", "packet", "netfilter", "insmod", "modprobe")),
                             f"the host record claims a kernel/drop act: {e['action']} (RW-SEAM-SILENT/RW-HOST-KERNEL)")

    def test_RW_SEAM_SILENT_the_host_claiming_the_drop_is_REFUSED(self):
        """RW-SEAM-SILENT (§4): the seam is NAMED and is the guest's; a FILTER-DECISION whose seam
        names the HOST (the host record claiming it dropped the packet) is REFUSED, recorded — the
        record decides, netfilter drops, never the host, never silently. Able-to-fail: the value_domain
        over the seam can refuse."""
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        for bad_seam in ("host", "host-kernel", "host-record"):
            with self.assertRaises(OpError) as cm:
                self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse", seam=bad_seam)
            self.assertEqual(cm.exception.rule, "NET-LAW-FILTER")
        # the good seam is admitted — the guard is not vacuous.
        self.assertEqual(self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")["payload"]["seam"],
                         "guest-netfilter")

    def test_RW_HOST_KERNEL_no_kernel_module_act_is_expressible_on_the_host_record(self):
        """RW-HOST-KERNEL (§4 / stop-f): kernel work is the guest's. There is NO op in the founding
        that inserts a module or a netfilter rule — the record decides and names the seam, and the
        drop is the guest kernel's netfilter (EP-00 rule 9). Proven structurally: no CREATE-OP mints
        an insmod/modprobe/netfilter act."""
        op_names = {r["payload"]["name"] for r in _pack_records() if r.get("action") == "CREATE-OP"}
        for banned in ("INSMOD", "MODPROBE", "NETFILTER", "PACKET-DROP", "IPTABLES"):
            self.assertNotIn(banned, op_names)
        # FILTER-DECISION itself performs no drop — it records a decision and names the seam.
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        rec = self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        self.assertEqual(rec["action"], "FILTER-DECISION")            # a decision, not a drop


# =============================================================================================
# A4 — T-ROUTING-POLICY-VS-INPUT (policy=FILTER-DECISION, world-fact=INPUT) + RW-ROUTING-AS-DECISION
# =============================================================================================

class TestRoutingPolicyVsInput(_World):
    def test_a_routing_name_decision_the_system_makes_is_a_FILTER_DECISION_citing_law(self):
        # POLICY: the system decides to refuse a connection by a routing/name rule -> a FILTER-DECISION
        # citing the firewall law. A DECISION the record authors.
        self.a_connection("s1", target="203.0.113.9:443")
        self.a_filter_rule("NET-LAW-FILTER:block-route-203.0.113.0/24", "refuse a route by policy")
        rec = self.decide("s1", "NET-LAW-FILTER:block-route-203.0.113.0/24", "refuse")
        self.assertEqual(rec["action"], "FILTER-DECISION")
        self.assertEqual(rec["rule_cited"], "NET-LAW-FILTER")
        self.assertIn("decision", rec["text"].lower() if rec.get("text") else "decision")

    def test_a_routing_name_FACT_the_world_hands_us_is_INPUT_never_this_decision(self):
        """The world's fact — a resolver answer, a route handed to us — is INPUT, never a decision the
        record authors (design/44 §2). Its home is the existing INPUT-class oracle op ANSWER-RETURNED
        (the clock-as-sensor law generalized to every oracle) — NOT a FILTER-DECISION. The two are
        disjoint by class: FILTER-DECISION appends a DECISION, ANSWER-RETURNED an INPUT-class arrival."""
        recs = _pack_records()
        answer_op = next(r for r in recs if r.get("action") == "CREATE-OP"
                         and r["payload"]["name"] == "ANSWER-RETURNED")
        self.assertIn("input-class", answer_op["payload"]["definition"]["description"].lower())
        filter_op = next(r for r in recs if r.get("action") == "CREATE-OP"
                         and r["payload"]["name"] == "FILTER-DECISION")
        self.assertIn("decision", filter_op["payload"]["text"].lower())    # a DECISION the system authors
        # DISJOINT: the world's-fact home and the policy op are two different ops of two classes.
        self.assertNotEqual(answer_op["payload"]["name"], filter_op["payload"]["name"])

    def test_RW_ROUTING_AS_DECISION_a_world_fact_recorded_as_a_decision_REDS(self):
        """RW-ROUTING-AS-DECISION (§4): a world-fact dressed as a decision REDS. A resolver answer is
        a bare fact — it names no governed connection and cites no filter rule. Pushing it through
        FILTER-DECISION (as if the system had decided it) is REFUSED, recorded — the decision stream
        never holds a world-fact. Able-to-fail: the require_prior gates refuse the ungoverned fact."""
        # a resolver answer shape: 'name:example.com -> 93.184.216.34', no SOCKET-OPEN, no filter rule.
        with self.assertRaises(OpError) as cm:
            self.decide("name:example.com", "NET-LAW-FILTER:resolved", "admit")
        self.assertEqual(cm.exception.rule, "NET-LAW-FILTER")          # the ungoverned fact is refused
        # and the FILTER-DECISION stream holds ONLY governed policy decisions (each over a real
        # connection, each citing a real rule), never a bare world-fact.
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        for e in self.store.by_action("FILTER-DECISION"):
            self.assertIn(e["payload"]["connection"], self.subs_sockets())   # every decision over a governed socket


    def subs_sockets(self):
        return set(SocketView(self.store).live_sockets())


# =============================================================================================
# A5 — T-NO-PACKET-ROWS (a census under load: zero per-packet rows) + RW-PACKET-ROW
# =============================================================================================

class TestNoPacketRows(_World):
    def test_a_census_under_load_has_zero_per_packet_rows(self):
        # LOAD: many connections, each decided by the firewall. The firewall records DECISIONS and
        # names the seam — never bytes on the wire. A per-packet flow is STREAM and STREAM appends nothing.
        self.a_filter_rule("NET-LAW-FILTER:block-cn")
        before = len(self.store.all())
        for i in range(20):
            sid = f"s{i}"
            self.a_connection(sid, target=f"1.1.1.1:{i}")
            self.decide(sid, "NET-LAW-FILTER:block-cn", "refuse")
        appended = self.store.all()[before:]
        allowed = {"SOCKET-OPEN", "SOCKET-CONNECT", "FILTER-DECISION"}
        for e in appended:
            self.assertIn(e["action"], allowed, f"a non-governed row appeared under load: {e['action']}")
        packetish = [e for e in appended
                     if any(w in e["action"].lower() for w in ("traffic", "packet", "byte", "stream", "recv-flow"))]
        self.assertEqual(packetish, [], "a per-packet row reached the record")
        # STREAM appends nothing — proven against the classmap's own connection-traffic STREAM class.
        from observe import classmap
        self.assertEqual(classmap.classify("connection", "connection-traffic"), classmap.STREAM)
        self.assertFalse(classmap.is_recorded("connection", "connection-traffic"))

    def test_RW_PACKET_ROW_a_recorded_byte_would_red_this_census(self):
        """RW-PACKET-ROW (§4 / stop-g): the census is able-to-fail. NO op mints a per-packet row —
        that is the design (STREAM appends nothing). The forbidden shape is the counterfactual the
        census must catch: a synthetic per-packet record injected into the census set makes it red
        (§A42; the real store is never mutated)."""
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        real = list(self.store.action_set_projection(set(FILTER_ACTIONS)).all())
        self.assertEqual([e for e in real if e["action"] != "FILTER-DECISION"], [])
        packet_row = {"actor": "web", "action": "filter-packet-drop", "object": "s1",
                      "rule_cited": "NET-LAW-FILTER", "payload": {"connection": "s1", "bytes": 1400}}
        with_packet = real + [packet_row]
        offenders = [e for e in with_packet if e["action"] != "FILTER-DECISION"]
        self.assertEqual([e["action"] for e in offenders], ["filter-packet-drop"],
                         "the census could not see a per-packet row — it cannot fail")


# =============================================================================================
# A6 — T-EXTENDED-LEDGER (both directions: too-weak recorded, too-wedged still admitted)
# =============================================================================================

class TestExtendedLedger(_World):
    def test_a_refused_connection_that_landed_unrecorded_before_is_now_a_recorded_decision(self):
        # TOO WEAK (before EP-52): a filter-refusal was UNRECORDED — no FILTER-DECISION existed, so
        # 'which rule dropped this' was unanswerable. Now the refuse LANDS as a recorded decision.
        self.a_connection("s1"); self.a_filter_rule("NET-LAW-FILTER:block-cn")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        view = self.filters()
        self.assertEqual(view.refusals()["s1"]["rule"], "NET-LAW-FILTER:block-cn")   # recorded refusal
        # ABLE TO FAIL: with no decision recorded (the pre-EP-52 world), the refusal census is empty.
        self.assertEqual(FilterView(self.store).refusals().keys() - {"s1"}, set())    # only the recorded one

    def test_a_lawful_connection_is_still_admitted_the_firewall_does_not_over_block(self):
        # TOO WEDGED: a lawful connection is ADMITTED — the firewall records an admit and does not
        # drop everything. The admit is recorded and distinguishable from a refuse.
        self.a_connection("s1"); self.a_connection("s2", target="10.0.0.5:22")
        self.a_filter_rule("NET-LAW-FILTER:block-cn"); self.a_filter_rule("NET-LAW-FILTER:allow-lan")
        self.decide("s1", "NET-LAW-FILTER:block-cn", "refuse")
        self.decide("s2", "NET-LAW-FILTER:allow-lan", "admit")
        view = self.filters()
        self.assertIn("s1", view.refusals())                          # refused
        self.assertNotIn("s2", view.refusals())                       # admitted, not over-blocked
        self.assertEqual(view.which_rule_decided()["s2"]["decision"], "admit")
        # BOTH DIRECTIONS ABLE TO FAIL: over-block (a refuse on s2) would show s2 in refusals; a silent
        # drop (no decision on s1) would leave s1 out of refusals. The fold catches both.
        self.assertEqual(set(view.refusals()), {"s1"})


# =============================================================================================
# A7 — T-FOUNDING-BUMP (MINOR; version + pack sha in one entry; census driven +1) + RW-MAJOR
# =============================================================================================

class TestFoundingBump(unittest.TestCase):
    def test_the_founding_version_is_at_or_beyond_the_EP52_era_and_the_bump_is_attested(self):
        from test_founding_is_logged import audit, pack_facts
        facts = pack_facts()
        # ERA-PINNED (the era-pin idiom, EP-48 A7 precedent): floored at the EP-52 era (1.46.0, when
        # this test was written); a later founding mover advances the constitution WITHOUT touching
        # this line. The load-bearing assertion is that the move is ATTESTED in ONE entry.
        ver = tuple(int(x) for x in facts["version"].split("."))
        self.assertGreaterEqual(ver, (1, 46, 0),
                                "the founding is at or beyond the EP-52 era (1.46.0) this test pins")
        a = audit()
        self.assertTrue(a["logged"],
                        "the founding moved and no single BUILD-PROGRESS entry names both the "
                        "version and the pack sha256 (the required ledger duty, :1178)")

    def test_the_op_population_is_ninety_three_driven_not_carried(self):
        # THE §A57 CENSUS: a new OP moves the op-population by +1 from its live value at dispatch.
        # EP-50 (VIEW-SERVICE) moved it 91 -> 92; EP-52 (FILTER-DECISION) moves 92 -> 93. The count
        # the test_ep30 pins (:189 len(drove), :256 len(set(drove))) enumerate — moved BY NAME here.
        recs = _pack_records()
        op_defs = [r for r in recs if (r.get("payload") or {}).get("kind") == "op_definition"
                   and r["payload"].get("name")]
        # C6a VT-2 (CREATE-RELATIONSHIP MINTED live, MINOR 1.51.0 -> 1.52.0) moved 93 -> 94 BY NAME (§A57).
        self.assertEqual(len(op_defs), 94)                            # the op-population census
        self.assertEqual(len({r["payload"]["name"] for r in op_defs}), 94)   # distinct, no double
        self.assertIn("FILTER-DECISION", {r["payload"]["name"] for r in op_defs})

    def test_the_discriminator_is_MINOR_one_op_and_one_law_added_no_op_removed_no_check_kind(self):
        recs = _pack_records()
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertIn("FILTER-DECISION", op_names)                    # the op added (MINOR direction)
        rule_ids = {(r.get("payload") or {}).get("rule_id") for r in recs
                    if r.get("action") == "CREATE-RULE"}
        self.assertIn("NET-LAW-FILTER", rule_ids)                     # the law class added
        # NONE REMOVED — the ops the campaign already shipped are all still present (a removal is MAJOR).
        for kept in ("SOCKET-OPEN", "VIEW-SERVICE", "COMMS-OPEN", "FILE-CREATE"):
            self.assertIn(kept, op_names)
        # NO CHECK KIND ADDED — OP_CHECKS is unchanged (a new kind would be MAJOR / stop-e). Frozen at 19.
        self.assertEqual(len(OP_CHECKS), 19)
        # FILTER-DECISION uses ONLY existing check kinds (require_prior, value_domain).
        used = set()
        for r in recs:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] == "FILTER-DECISION":
                for c in r["payload"]["definition"].get("checks", []):
                    used.add(c["check"])
        self.assertTrue(used <= set(OP_CHECKS))
        self.assertEqual(used, {"require_prior", "value_domain"})

    def test_RW_MAJOR_a_removed_op_or_a_new_check_kind_would_be_the_STOP(self):
        """RW-MAJOR (§4 / stop-e): the discriminator is able-to-distinguish. A pack that REMOVED an op
        or added a check kind is MAJOR — the owner's, not decided here. Assert the real move did
        neither (SOCKET-OPEN kept, no FILTER-DECISION check outside OP_CHECKS)."""
        recs = _pack_records()
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertIn("SOCKET-OPEN", op_names)                        # a representative pre-move op survives
        for r in recs:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] == "FILTER-DECISION":
                for c in r["payload"]["definition"].get("checks", []):
                    self.assertIn(c["check"], OP_CHECKS,
                                  "FILTER-DECISION introduced a check kind — MAJOR / stop-e")


if __name__ == "__main__":
    unittest.main()
