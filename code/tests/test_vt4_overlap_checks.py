# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (overlap, collision check, contradiction, double-claim, separation of powers, declared
# marker, venn2 geometry, census). NON-GOAL: no offensive capability of any kind — every assertion
# proves design/53 B8 by function: overlap (computed from two rules' scopes, and declared as a venn2
# IN row) FEEDS the existing collision checks, a conflict-of-interest is a census finding, a misspelt
# marker and a program-declared overlap are named findings, and overlap is never a node. Full
# declaration: SCOPE-STATEMENT.md.
"""C6a VT-4 — OVERLAP FEEDS THE CHECKS (plan planning/exec/VT-4-OVERLAP-FEEDS-CHECKS-BUILD.md).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). NO FOUNDING: no new op/law/check kind, no new field, no pack edit. The
NEW code is one INSTRUMENT under tools/conformance (overlap_checks_census) that READS a record's
overlaps and INVOKES the three BUILT collision checks (kernel.views.contradictions /
handshake_double_claim / separation_of_powers_conflicts) — never re-authored. views.py is untouched.

  A1  OVERLAP FEEDS THE THREE COLLISION CHECKS — a computed overlap (equal rule scopes) and a
      DECLARED overlap (a venn2 IN row) each feed contradiction / double-claim / concentration; a
      planted overlapping pair that should trip a given check trips EXACTLY it; disjoint trips none.
  A2  CONFLICT-OF-INTEREST AS A CENSUS FINDING — an actor holding an opposed PAIR (two powers) for
      one scope is NAMED by the census, STRICTLY WEAKER than the gate's all-three refusal (never a
      new gate check kind); one power is no conflict.
  A3  THE SELF-DECLARED-MARKER CENSUS — the recognised markers (held_stage / adopts_received_rule /
      auto_adopt_parent_rules, READ from source) are censused; a misspelt marker is a FINDING; an
      ordinary policy key is not a marker.
  A4  THE PROGRAM-DECLARED-OVERLAP FINDING — a declared overlap minted by a PROGRAM-class actor reds;
      the gate ADMITS the structured row (it lands) and the census names its minter; a human-class
      declared overlap passes.
  A5  OVERLAP STAYS A CHECK, NEVER A NODE — a view named "overlap" reds; an IN row is never a tree
      edge; a clean record names no overlap node.
  A6  NO FOUNDING — pack byte-unchanged; OP_CHECKS 19, ATTESTED_MEMBERS 54 (tools/ not attested); the
      built checks are imported and invoked, never re-authored.
"""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel.compose import build_full_kernel                                     # noqa: E402
from kernel.errors import OpError                                               # noqa: E402
from kernel.opdefs import OP_CHECKS                                             # noqa: E402
from kernel import attestation, views as views_module, border as border_module  # noqa: E402

from tools.conformance import overlap_checks_census as census                   # noqa: E402

_REPO = os.path.join(os.path.dirname(__file__), "..")


def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    """RELEASE-4 round 3 (owner :4656): the ONE case in this module that shells out to git (the pack
    byte-unchanged reading, `git -C ... diff`) is guarded by this probe -- git present AND this tree a
    git checkout with a HEAD. In the lab the probe is true and the case RUNS; in the render (no .git, or
    no git binary on a stock box) it SKIPS by name instead of erroring. The established RENDER-NO-GIT
    form (test_p11_handshake and five siblings), unchanged. No other case is touched."""
    try:
        return subprocess.run(["git", "-C", _REPO, "rev-parse", "--verify", "HEAD"],
                              capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


def _kernel(prefix="vt4-"):
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))[:3]
    return store, gate, views


def _hold_stage(gate, holder, rule_id, stage, scope, minter="owner"):
    """A stage-holding CLAIM (P6's idiom, reused): a LIVE CREATE-RULE self-declaring the stage on the
    EXISTING accepted params — no founding, no new row field."""
    return gate.execute("CREATE-RULE", minter,
                        {"rule_id": rule_id, "policy_key": "held_stage",
                         "value": stage, "scope": scope, "text": holder})


def _compare(gate, actor, a, b, frame, verdict):
    return gate.execute("COMPARE", actor, {"a": a, "b": b, "frame": frame, "verdict": verdict})


def _declare_overlap(gate, minter, subject, obj):
    """A DECLARED overlap: a CREATE-RELATIONSHIP row geometry IN (design/53 B8)."""
    return gate.execute("CREATE-RELATIONSHIP", minter,
                        {"subject": subject, "object": obj, "geometry": "IN"})


# =================================================================================================
# A1 — OVERLAP FEEDS THE THREE BUILT COLLISION CHECKS (trips exactly the right one; disjoint none)
# =================================================================================================

class TestOverlapFeedsChecks(unittest.TestCase):
    def test_computed_overlap_trips_only_contradiction(self):
        """A1: two verdicts on the SAME (a, b, frame) that are incompatible are a contradiction
        (overlapping ground, opposed content). Only the contradiction check trips."""
        store, gate, views = _kernel("vt4-a1-con-")
        _compare(gate, "alice", "x", "y", "cost", "a-greater")
        _compare(gate, "alice", "x", "y", "cost", "a-lesser")     # same frame, incompatible
        self.assertTrue(census.contradiction_hits(views))         # TRIPS
        self.assertEqual(census.double_claim_hits(store, views), [])
        self.assertEqual(census.concentration_hits(store, views), [])

    def test_computed_overlap_trips_only_double_claim(self):
        """A1 / I8: two DIFFERENT holders claiming decision @ fisheries — an overlapping (stage,
        scope) — is a double-claim. Only the double-claim check trips."""
        store, gate, views = _kernel("vt4-a1-dc-")
        _hold_stage(gate, "gov-a", "R1", "decision", "fisheries")
        _hold_stage(gate, "gov-b", "R2", "decision", "fisheries")   # same (stage, scope), other holder
        self.assertEqual(census.double_claim_hits(store, views), [("decision", "fisheries")])  # TRIPS
        self.assertEqual(census.contradiction_hits(views), [])
        self.assertEqual(census.concentration_hits(store, views), [])

    def test_computed_overlap_trips_only_concentration(self):
        """A1 / I16: one actor holding all three powers for one scope is a concentration. Only the
        concentration check trips (a single holder is no double-claim; no COMPARE, no contradiction)."""
        store, gate, views = _kernel("vt4-a1-conc-")
        _hold_stage(gate, "prince", "R1", "decision", "realm")
        _hold_stage(gate, "prince", "R2", "enforcement", "realm")
        _hold_stage(gate, "prince", "R3", "monitoring", "realm")
        self.assertEqual(census.concentration_hits(store, views), [("prince", "realm")])  # TRIPS
        self.assertEqual(census.contradiction_hits(views), [])
        self.assertEqual(census.double_claim_hits(store, views), [])

    def test_a_declared_overlap_feeds_the_double_claim_check(self):
        """A1 (the DECLARED half): two holders claim decision on scopes 'coast' and 'shore' —
        disjoint strings, NO double-claim on their own. A DECLARED overlap IN(coast, shore) joins the
        two grounds, and the SAME two claims now collide: the declared overlap FED the check."""
        store, gate, views = _kernel("vt4-a1-decl-")
        _hold_stage(gate, "gov-a", "R1", "decision", "coast")
        _hold_stage(gate, "gov-b", "R2", "decision", "shore")
        self.assertEqual(census.double_claim_hits(store, views), [])   # disjoint scopes: no collision
        _declare_overlap(gate, "owner", "coast", "shore")              # the declared overlap
        hits = census.double_claim_hits(store, views)
        self.assertEqual(len(hits), 1)                                 # NOW it trips — the IN row fed it
        self.assertEqual(hits[0][0], "decision")

    def test_disjoint_scopes_trip_none(self):
        """A1: two rules on genuinely disjoint scopes with no declared overlap and no opposed content
        trip NO check (the able-to-fail control: no false positive)."""
        store, gate, views = _kernel("vt4-a1-disj-")
        _hold_stage(gate, "gov-a", "R1", "decision", "fisheries")
        _hold_stage(gate, "gov-b", "R2", "decision", "forestry")   # different scope
        self.assertEqual(census.contradiction_hits(views), [])
        self.assertEqual(census.double_claim_hits(store, views), [])
        self.assertEqual(census.concentration_hits(store, views), [])


# =================================================================================================
# A2 — CONFLICT-OF-INTEREST AS A CENSUS FINDING (never a new gate check kind)
# =================================================================================================

class TestConflictOfInterest(unittest.TestCase):
    def test_two_opposed_powers_is_a_census_finding_not_a_concentration(self):
        """A2: an actor holding decision AND enforcement for one scope is a conflict-of-interest — a
        CENSUS FINDING with its world. It is STRICTLY WEAKER than the gate's separation-of-powers
        refusal (all three): concentration does NOT trip on two powers."""
        store, gate, views = _kernel("vt4-a2-")
        _hold_stage(gate, "judge", "R1", "decision", "realm")
        _hold_stage(gate, "judge", "R2", "enforcement", "realm")
        coi = census.concentration_subthreshold_findings(store, views)   # VT-4b repoint: this measures concentration, not conflict of interest
        self.assertEqual(len(coi), 1)
        self.assertEqual(coi[0]["actor"], "judge")
        self.assertEqual(coi[0]["scope"], "realm")
        self.assertEqual(coi[0]["powers"], ["decision", "enforcement"])
        self.assertEqual(census.concentration_hits(store, views), [])   # NOT a concentration (two, not three)

    def test_the_conflict_of_interest_holding_is_not_refused_at_the_gate(self):
        """A2: a two-power holding is a census finding, NOT a gate refusal — the gate ADMITTED both
        claims (P11 A4 'any two powers pass'). No refusal row cites separation of powers here (a real
        gate refusal would be founding — STOP condition (b), not taken)."""
        store, gate, views = _kernel("vt4-a2b-")
        _hold_stage(gate, "judge", "R1", "decision", "realm")
        _hold_stage(gate, "judge", "R2", "enforcement", "realm")
        refusals = [r for r in store.all() if r.get("refused")]
        self.assertEqual(refusals, [])                                  # nothing refused — the census only NAMES it
        self.assertTrue(census.concentration_subthreshold_findings(store, views))   # VT-4b repoint (was conflict_of_interest_findings)

    def test_a_single_power_is_no_conflict(self):
        """A2 — able-to-fail: one power for one scope is no conflict-of-interest (the finding is
        empty)."""
        store, gate, views = _kernel("vt4-a2c-")
        _hold_stage(gate, "judge", "R1", "decision", "realm")
        self.assertEqual(census.concentration_subthreshold_findings(store, views), [])   # VT-4b repoint (was conflict_of_interest_findings)


# =================================================================================================
# A3 — THE SELF-DECLARED-MARKER CENSUS (recognition READ from source; a misspelt marker a FINDING)
# =================================================================================================

class TestMarkerCensus(unittest.TestCase):
    def test_the_recognised_markers_are_read_from_source_not_redeclared(self):
        """A3 / STOP (d): the recognised set IS the source constants (Views.HELD_STAGE_KEY,
        border.ADOPT_MARKER, border.AUTO_ADOPT_MARKER) — read, never re-declared, never changed."""
        self.assertEqual(census.RECOGNISED_MARKERS, frozenset({
            views_module.Views.HELD_STAGE_KEY,
            border_module.ADOPT_MARKER,
            border_module.AUTO_ADOPT_MARKER,
        }))

    def test_recognised_markers_pass(self):
        """A3: rules declaring each recognised marker are censused as recognised, none misspelt."""
        store, gate, views = _kernel("vt4-a3-ok-")
        gate.execute("CREATE-RULE", "owner", {"rule_id": "H", "policy_key": "held_stage",
                                              "value": "decision", "scope": "s", "text": "gov-a"})
        gate.execute("CREATE-RULE", "owner", {"rule_id": "AD", "policy_key": "adopts_received_rule",
                                              "value": "sha256:x"})
        gate.execute("CREATE-RULE", "owner", {"rule_id": "AU", "policy_key": "auto_adopt_parent_rules",
                                              "value": "s"})
        mc = census.marker_census(store)
        for m in ("held_stage", "adopts_received_rule", "auto_adopt_parent_rules"):
            self.assertIn(m, mc["recognised"])
        self.assertEqual(mc["misspelt"], [])

    def test_a_misspelt_marker_reds(self):
        """A3 — THE CHECK CAN FAIL: a near-miss of a recognised marker is a FINDING (a silent miss —
        it would never be recognised)."""
        store, gate, views = _kernel("vt4-a3-mis-")
        gate.execute("CREATE-RULE", "owner", {"rule_id": "M", "policy_key": "adopts_received_rulle",
                                              "value": "x"})   # one extra 'l'
        mc = census.marker_census(store)
        self.assertEqual(len(mc["misspelt"]), 1)
        self.assertEqual(mc["misspelt"][0]["key"], "adopts_received_rulle")
        self.assertEqual(mc["misspelt"][0]["nearest"], "adopts_received_rule")
        self.assertEqual(mc["misspelt"][0]["distance"], 1)

    def test_an_ordinary_policy_key_is_not_a_marker(self):
        """A3: an ordinary policy key (far from every marker) is not-a-marker, NOT a misspelt finding
        — the census does not red on legitimate non-marker policy."""
        store, gate, views = _kernel("vt4-a3-ord-")
        gate.execute("CREATE-RULE", "owner", {"rule_id": "B", "policy_key": "budget:gov-a", "value": 10})
        mc = census.marker_census(store)
        self.assertIn("budget:gov-a", mc["not_a_marker"])
        self.assertEqual(mc["misspelt"], [])


# =================================================================================================
# A4 — THE PROGRAM-DECLARED-OVERLAP FINDING
# =================================================================================================

class TestProgramDeclaredOverlap(unittest.TestCase):
    def test_a_program_declared_overlap_reds_and_the_row_lands(self):
        """A4: a program-class actor mints a declared overlap (IN). The gate ADMITS the structured row
        (a program holds the structured arm, cell S) — so the row LANDS — and the census names its
        minter as a FINDING (until stations exist; the overlap judgment is a station's step)."""
        store, gate, views = _kernel("vt4-a4-prog-")
        gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "prog1", "actor_class": "program"})
        rec = _declare_overlap(gate, "prog1", "coast", "shore")
        self.assertIsNotNone(rec.get("seq"))                       # the gate admitted it — the row lands
        findings = census.program_declared_overlap_findings(store, views)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["minter"], "prog1")
        self.assertEqual(findings[0]["minter_class"], "program")

    def test_a_human_declared_overlap_passes(self):
        """A4 — able-to-fail: a human-class actor's declared overlap is NOT flagged (passes). The
        census reads the minter's class; only a program-class minter is a finding."""
        store, gate, views = _kernel("vt4-a4-human-")
        gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "clerk", "actor_class": "human"})
        _declare_overlap(gate, "clerk", "coast", "shore")
        self.assertEqual(census.program_declared_overlap_findings(store, views), [])

    def test_an_unclassified_minters_overlap_passes(self):
        """A4: an unclassified minter (owner) is not program-class — its declared overlap passes.
        Only PROGRAM class is the finding."""
        store, gate, views = _kernel("vt4-a4-owner-")
        _declare_overlap(gate, "owner", "coast", "shore")
        self.assertEqual(census.program_declared_overlap_findings(store, views), [])


# =================================================================================================
# A5 — OVERLAP STAYS A CHECK, NEVER A NODE
# =================================================================================================

class TestOverlapNeverANode(unittest.TestCase):
    def test_a_view_named_overlap_reds(self):
        """A5 / design/53 B8 'no view node is named overlap': a view_definition named 'overlap' is a
        FINDING (overlap must stay a check)."""
        store, gate, views = _kernel("vt4-a5-node-")
        gate.execute("CREATE-VIEW", "owner", {"name": "overlap", "when": {"action": "NOOP"},
                                              "then": {"move_to": "Q"}})
        nodes = census.overlap_node_findings(store, views)
        self.assertEqual(nodes["named_nodes"], ["overlap"])

    def test_a_clean_record_names_no_overlap_node(self):
        """A5 — able-to-fail: a record with no view named overlap has an empty finding set."""
        store, gate, views = _kernel("vt4-a5-clean-")
        gate.execute("CREATE-VIEW", "owner", {"name": "ordinary", "when": {"action": "NOOP"},
                                              "then": {"move_to": "Q"}})
        nodes = census.overlap_node_findings(store, views)
        self.assertEqual(nodes["named_nodes"], [])

    def test_an_IN_row_is_never_a_tree_edge(self):
        """A5: a declared overlap (IN) is symmetric and makes NO tree — it never appears as an
        actor-tree containment edge (the reader admits NS/EM only). Its finding set is empty."""
        store, gate, views = _kernel("vt4-a5-inrow-")
        _declare_overlap(gate, "owner", "coast", "shore")
        nodes = census.overlap_node_findings(store, views)
        self.assertEqual(nodes["in_rows_as_tree_edges"], [])
        self.assertEqual(nodes["named_nodes"], [])


# =================================================================================================
# A6 — NO FOUNDING (the built checks reused, not re-authored)
# =================================================================================================

class TestNoFounding(unittest.TestCase):
    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs git and a git checkout (the render is not a "
                         "git checkout) -- the pack byte-unchanged reading shells out to git diff")
    def test_the_founding_pack_is_byte_unchanged(self):
        """A6: VT-4 mints no founding — the pack is byte-unchanged against HEAD (no new op/law/check
        kind, no new field, no pack edit). git diff --stat on the pack is empty."""
        out = subprocess.run(
            ["git", "-C", _REPO, "diff", "--stat", "--", "src/founding/founding-pack.json"],
            capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "", out.stdout)

    def test_no_new_op_check_kind_or_attested_member(self):
        """A6: OP_CHECKS stays 19 (no new gate check kind — the census is a plain instrument, not a
        registered kind); this unit's fence added no src engine module (the census lives under tools/,
        which is NOT attested — the ATTESTED_MEMBERS rider does not fire)."""
        self.assertEqual(len(OP_CHECKS), 19)
        # RE-POINTED (:3934): assert THIS unit's own property — its fence added NO src engine module —
        # NOT the absolute len(ATTESTED_MEMBERS)==N global count (test_ep40/ep46/keymat's property; it
        # churned here on every lawful src add estate-wide, host_seam.py 54->55). This unit's census is
        # tools/-resident and tools/ is NEVER attested, so it adds no attested src module.
        self.assertFalse(any(m.startswith("tools/") for m in attestation.ATTESTED_MEMBERS),
                         "a tools/ file is attested — this unit's census lives under tools/, which is never attested")
        self.assertFalse(any("overlap_checks_census" in m for m in attestation.ATTESTED_MEMBERS))

    def test_the_checks_are_reused_not_re_authored(self):
        """A6: the census INVOKES views.py's three built checks — it does not re-author them. The
        census source defines none of them; it imports the module and calls them."""
        with open(os.path.join(_REPO, "tools", "conformance", "overlap_checks_census.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        for built in ("def contradictions", "def handshake_double_claim",
                      "def refuse_double_claim", "def separation_of_powers_conflicts",
                      "def refuse_separation_of_powers"):
            self.assertNotIn(built, src)                           # not re-authored in the census
        # they ARE the built ones (imported, callable)
        self.assertTrue(callable(views_module.handshake_double_claim))
        self.assertTrue(callable(views_module.separation_of_powers_conflicts))

    def test_the_census_runs_end_to_end_and_produces_a_red(self):
        """A6 / the sibling-census discipline: the census's own demo world produces at least one red
        (a census is proven only by a red it produces) — and render_markdown emits its evidence."""
        store, gate, views = census._demo_world()
        result = census.census(store, gate, views)
        self.assertTrue(result["findings"])                       # the census refuses something
        md = census.render_markdown(result)
        self.assertIn("Overlap feeds the checks", md)


if __name__ == "__main__":
    unittest.main()
