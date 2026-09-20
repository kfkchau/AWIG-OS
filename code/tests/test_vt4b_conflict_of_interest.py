# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (held power, rule scope, computed overlap, declared IN relation, containment, judge in
# its own cause, contradiction, census). NON-GOAL: no offensive capability of any kind — every
# assertion proves design/25 :134-135 and archi :3837 by function: CONFLICT OF INTEREST is DISTINCT
# from CONCENTRATION. Concentration counts the powers one actor holds over one scope (the census's
# renamed concentration_subthreshold finding); conflict of interest reads an OVERLAP — an actor with
# a power over rule A's scope that also FALLS INSIDE rule B's scope, A and B one ground. Full
# declaration: SCOPE-STATEMENT.md.
"""C6a VT-4b — CONFLICT OF INTEREST, DISTINCT FROM CONCENTRATION (the pair mechanism).

Named in planning/exec/VT-4b-CONFLICT-OF-INTEREST-BUILD.md before code, landed here as regression
tests (charter: every verification probe lands as a regression test). GREEN — a census repair in
tools/conformance; NO new op/law/check kind, NO new field, NO pack edit, NO shared src (views.py /
authority.py READ, never re-authored). VT-4's A2 "conflict-of-interest" finding was actually
CONCENTRATION at a lower threshold (two of three powers over one scope, reading no overlap — a
duplicate of the separation-of-powers refusal). VT-4b (a) RENAMES it and (b) REBUILDS conflict of
interest on the overlap-fed pair mechanism.

  A1  THE TWO-POWERS FINDING IS RENAMED `concentration_subthreshold_findings` — it measures an actor
      holding two of the three powers over ONE (canonical) scope, below the three-power refusal, and
      no longer claims to be conflict of interest. conflict_of_interest_findings is now a DIFFERENT
      thing (empty on a pure two-powers-no-overlap world).
  A2  CONFLICT OF INTEREST REBUILT ON THE PAIR MECHANISM — an actor holding a power over rule A's
      scope AND falling inside rule B's scope (a subject of B: its identity, its group-containment,
      or its actor_class), A and B one canonical ground (computed, or a declared IN row): THE JUDGE
      IN ITS OWN CAUSE. Marked OPPOSED where the contradiction instrument also names A's and B's
      scopes incompatible; named without the mark otherwise.
  A3  THE SEPARATING CONTROLS — (i) two powers over one scope with NO overlapping rule the actor is
      inside is concentration_subthreshold, NOT a conflict (the conflict is NOT derivable from the
      powers count alone); (ii) ONE power over a scope overlapping a scope the actor falls inside IS
      a conflict; (iii) a planted judge-in-own-cause reds; (iv) one actor may lawfully appear in BOTH
      findings for its two DIFFERENT reasons — distinct BY MEASURE, not disjoint by population.

Every acceptance carries its RED WORLD, driven through the gate (a control that cannot red is the
defect). views.py and authority.py are READ, never edited (GREEN, tools/conformance + tests only).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel.compose import build_full_kernel                                     # noqa: E402

from tools.conformance import overlap_checks_census as census                   # noqa: E402


def _kernel(prefix="vt4b-"):
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))[:3]
    return store, gate, views


def _hold_stage(gate, holder, rule_id, stage, scope, minter="owner"):
    """A stage-holding CLAIM (the VT-4 idiom): a LIVE CREATE-RULE self-declaring the held_stage
    marker on the EXISTING accepted params — no founding, no new row field."""
    return gate.execute("CREATE-RULE", minter,
                        {"rule_id": rule_id, "policy_key": "held_stage",
                         "value": stage, "scope": scope, "text": holder})


def _rule_with_scope(gate, rule_id, scope, minter="owner"):
    """Any live rule carrying a `scope` — a candidate 'rule B' the actor may fall inside. An ordinary
    policy key (not a marker), so the marker census is untouched."""
    return gate.execute("CREATE-RULE", minter,
                        {"rule_id": rule_id, "policy_key": "policy:%s" % scope, "value": 1,
                         "scope": scope})


def _declare_overlap(gate, subject, obj, minter="owner"):
    """A DECLARED overlap: a CREATE-RELATIONSHIP row geometry IN (design/53 B8) — joins two grounds
    in the scope equivalence."""
    return gate.execute("CREATE-RELATIONSHIP", minter,
                        {"subject": subject, "object": obj, "geometry": "IN"})


def _actor(gate, aid, minter="owner"):
    return gate.execute("CREATE-ACTOR", minter, {"actor_id": aid})


def _nest(gate, subject, group, minter="owner"):
    """A CONTAINMENT edge (NS): `subject` nested in the group `object`. The gate's no-orphan guard
    requires the group to ground at the constitution's root, so groups are chained to `owner`."""
    return gate.execute("CREATE-RELATIONSHIP", minter,
                        {"subject": subject, "object": group, "geometry": "NS"})


def _compare(gate, actor, a, b, frame, verdict):
    return gate.execute("COMPARE", actor, {"a": a, "b": b, "frame": frame, "verdict": verdict})


# =================================================================================================
# A1 — THE TWO-POWERS FINDING RENAMED `concentration_subthreshold_findings`
# =================================================================================================

class TestConcentrationSubthresholdRename(unittest.TestCase):
    def test_two_powers_over_one_scope_is_concentration_subthreshold_not_conflict(self):
        """A1: an actor holding decision AND enforcement over one scope is a
        concentration_subthreshold finding (two of three powers, below the all-three refusal) — the
        SAME measure the census formerly mis-named conflict-of-interest. conflict_of_interest is now
        a DIFFERENT thing and is EMPTY on this pure two-powers-no-overlap world."""
        store, gate, views = _kernel("vt4b-a1-")
        _hold_stage(gate, "judge", "R1", "decision", "realm")
        _hold_stage(gate, "judge", "R2", "enforcement", "realm")
        sub = census.concentration_subthreshold_findings(store, views)
        self.assertEqual(len(sub), 1)
        self.assertEqual(sub[0]["actor"], "judge")
        self.assertEqual(sub[0]["scope"], "realm")
        self.assertEqual(sub[0]["powers"], ["decision", "enforcement"])
        # NOT the all-three gate refusal, and NOT conflict of interest (no overlap the actor is inside)
        self.assertEqual(census.concentration_hits(store, views), [])
        self.assertEqual(census.conflict_of_interest_findings(store, views), [])

    def test_a_single_power_is_no_concentration_subthreshold(self):
        """A1 — able-to-fail: one power over one scope is no concentration_subthreshold finding."""
        store, gate, views = _kernel("vt4b-a1b-")
        _hold_stage(gate, "judge", "R1", "decision", "realm")
        self.assertEqual(census.concentration_subthreshold_findings(store, views), [])

    def test_the_old_name_is_gone(self):
        """A1: the built two-powers finding no longer answers to `conflict_of_interest_findings` —
        that name now carries the distinct pair mechanism; the census report keys carry BOTH
        findings under their own names."""
        store, gate, views = _kernel("vt4b-a1c-")
        result = census.census(store, gate, views)
        self.assertIn("concentration_subthreshold", result)
        self.assertIn("conflict_of_interest", result)


# =================================================================================================
# A2 — CONFLICT OF INTEREST REBUILT ON THE OVERLAP-FED PAIR MECHANISM (archi :3837)
# =================================================================================================

class TestConflictOfInterestPairMechanism(unittest.TestCase):
    def test_containment_judge_in_own_cause_is_a_conflict_and_marked_opposed(self):
        """A2: a judge holds decision over rule A's scope ('docket') AND falls inside rule B's scope
        ('chamber', by group-containment), A and B one ground (a declared IN row) — the judge in its
        own cause. The contradiction instrument also names docket and chamber incompatible, so the
        finding is marked OPPOSED."""
        store, gate, views = _kernel("vt4b-a2-op-")
        _actor(gate, "chamber"); _nest(gate, "chamber", "owner")     # chamber grounded at the root
        _actor(gate, "judge"); _nest(gate, "judge", "chamber")        # judge nested inside chamber
        _hold_stage(gate, "judge", "RA", "decision", "docket")        # rule A: judge decides 'docket'
        _rule_with_scope(gate, "RB", "chamber")                       # rule B governs 'chamber'
        _declare_overlap(gate, "docket", "chamber")                   # A and B one ground
        _compare(gate, "assessor", "docket", "chamber", "priority", "a-greater")
        _compare(gate, "assessor", "docket", "chamber", "priority", "a-lesser")  # incompatible -> OPPOSED
        coi = census.conflict_of_interest_findings(store, views)
        self.assertEqual(len(coi), 1)
        self.assertEqual(coi[0]["actor"], "judge")
        self.assertEqual(coi[0]["power"], "decision")
        self.assertEqual(coi[0]["power_scope"], "docket")
        self.assertEqual(coi[0]["inside_scope"], "chamber")
        self.assertTrue(coi[0]["opposed"])

    def test_the_same_finding_without_a_contradiction_is_named_without_the_opposed_mark(self):
        """A2: the identical judge-in-own-cause with NO incompatible verdict on the pair is still a
        conflict-of-interest finding — named WITHOUT the OPPOSED mark."""
        store, gate, views = _kernel("vt4b-a2-noop-")
        _actor(gate, "chamber"); _nest(gate, "chamber", "owner")
        _actor(gate, "judge"); _nest(gate, "judge", "chamber")
        _hold_stage(gate, "judge", "RA", "decision", "docket")
        _rule_with_scope(gate, "RB", "chamber")
        _declare_overlap(gate, "docket", "chamber")
        coi = census.conflict_of_interest_findings(store, views)
        self.assertEqual(len(coi), 1)
        self.assertFalse(coi[0]["opposed"])

    def test_the_class_reading_falls_inside_by_actor_class(self):
        """A2 (the 'its CLASS within B's scope' reading): an actor whose actor_class equals rule B's
        scope falls inside B; holding a power over an overlapping scope is the conflict."""
        store, gate, views = _kernel("vt4b-a2-class-")
        gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "inspector", "actor_class": "human"})
        _hold_stage(gate, "inspector", "RA", "monitoring", "coast")   # power over 'coast'
        _rule_with_scope(gate, "RB", "human")                          # rule B governs the class 'human'
        _declare_overlap(gate, "coast", "human")                       # coast and human one ground
        coi = census.conflict_of_interest_findings(store, views)
        self.assertEqual(len(coi), 1)
        self.assertEqual(coi[0]["actor"], "inspector")
        self.assertEqual(coi[0]["inside_scope"], "human")
        self.assertEqual(coi[0]["power_scope"], "coast")

    def test_a_power_over_a_ground_the_actor_is_not_inside_is_no_conflict(self):
        """A2 — able-to-fail: an actor holds a power over a ground governed by a rule, but the actor
        is NOT a subject of that ground (no identity / containment / class match) — no conflict."""
        store, gate, views = _kernel("vt4b-a2-none-")
        _hold_stage(gate, "clerk", "RA", "decision", "ground")
        _rule_with_scope(gate, "RB", "ground")
        self.assertEqual(census.conflict_of_interest_findings(store, views), [])


# =================================================================================================
# A3 — THE SEPARATING CONTROLS (distinct by measure, not disjoint by population)
# =================================================================================================

class TestSeparatingControls(unittest.TestCase):
    def test_i_two_powers_no_overlapping_rule_inside_is_concentration_not_conflict(self):
        """A3 (i) — THE LOAD-BEARING GUARD: an actor holding TWO powers over one scope with NO
        overlapping rule it falls inside is concentration_subthreshold ONLY, NOT a conflict. A
        conflict finding derivable from the POWERS COUNT ALONE (no overlap read) is the defect this
        proves absent."""
        store, gate, views = _kernel("vt4b-a3i-")
        _hold_stage(gate, "regent", "R1", "decision", "s1")
        _hold_stage(gate, "regent", "R2", "enforcement", "s1")
        self.assertEqual(len(census.concentration_subthreshold_findings(store, views)), 1)
        self.assertEqual(census.conflict_of_interest_findings(store, views), [])   # NOT a conflict

    def test_ii_one_power_over_an_overlapping_scope_it_falls_inside_is_a_conflict(self):
        """A3 (ii) — THE LOAD-BEARING GUARD: an actor holding ONE power over a scope overlapping a
        scope it falls inside IS a conflict-of-interest (proving conflict reads the OVERLAP, not the
        powers count — one power suffices). It is NOT a concentration_subthreshold (one power)."""
        store, gate, views = _kernel("vt4b-a3ii-")
        _hold_stage(gate, "judge", "RA", "decision", "coast")          # ONE power over 'coast'
        _rule_with_scope(gate, "RB", "judge")                          # rule B governs the judge itself
        _declare_overlap(gate, "coast", "judge")                       # coast and judge one ground
        coi = census.conflict_of_interest_findings(store, views)
        self.assertEqual(len(coi), 1)
        self.assertEqual(coi[0]["actor"], "judge")
        self.assertEqual(coi[0]["inside_scope"], "judge")
        self.assertEqual(census.concentration_subthreshold_findings(store, views), [])  # one power: no concentration

    def test_iii_a_planted_judge_in_own_cause_reds(self):
        """A3 (iii): the archetypal judge-in-own-cause — a judge holding decision over 'case' who is
        a MEMBER of 'case' (A and B the same ground) — reds as a conflict-of-interest finding."""
        store, gate, views = _kernel("vt4b-a3iii-")
        _actor(gate, "case"); _nest(gate, "case", "owner")
        _actor(gate, "judge"); _nest(gate, "judge", "case")            # judge is inside 'case'
        _hold_stage(gate, "judge", "RA", "decision", "case")           # and judge decides 'case'
        coi = census.conflict_of_interest_findings(store, views)
        self.assertEqual(len(coi), 1)
        self.assertEqual(coi[0]["actor"], "judge")
        self.assertEqual(coi[0]["power_scope"], "case")
        self.assertEqual(coi[0]["inside_scope"], "case")

    def test_iv_one_actor_may_appear_in_both_findings_for_two_different_reasons(self):
        """A3 (iv) — BINDING PRECISION (archi :3840): distinct BY MEASURE, not disjoint by
        population. One actor holds two powers over S1 (concentration_subthreshold) AND one power
        over S2 while falling inside an overlapping rule (conflict). It appears in BOTH — lawful,
        no coincidence defect — and the S1 two-power holding is NOT itself a conflict."""
        store, gate, views = _kernel("vt4b-a3iv-")
        _hold_stage(gate, "regent", "R1", "decision", "s1")            # two powers over s1
        _hold_stage(gate, "regent", "R2", "enforcement", "s1")
        _hold_stage(gate, "regent", "R3", "monitoring", "s2")          # one power over s2
        _rule_with_scope(gate, "RB", "regent")                         # rule B governs the regent itself
        _declare_overlap(gate, "s2", "regent")                         # s2 and regent one ground
        sub = census.concentration_subthreshold_findings(store, views)
        coi = census.conflict_of_interest_findings(store, views)
        self.assertTrue(any(r["actor"] == "regent" and r["scope"] == "s1" for r in sub))
        self.assertTrue(any(r["actor"] == "regent" for r in coi))
        # the two measures are distinct: the s1 two-power holding is NOT a conflict; the conflict is
        # the s2 overlap-fall-inside, read from the overlap the powers count never touches.
        self.assertFalse(any(r["power_scope"] == "s1" for r in coi))
        self.assertTrue(any(r["power_scope"] == "s2" for r in coi))


if __name__ == "__main__":
    unittest.main()
