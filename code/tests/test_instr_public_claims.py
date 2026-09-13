# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (claim, proving test, designed-not-built). NON-GOAL: no offensive capability of any
# kind — this proves every PUBLIC claim is either backed by a resolvable test or tagged not-yet;
# it edits no README word and drives no code. Full declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I6 [GREEN] — THE PUBLIC-CLAIM CENSUS.

Every claim in the public README carries a proving test id (that RESOLVES) or a "designed, not
built" tag; the census reds on a claim with neither, on a claim whose quote drifted from the
README, and on a NEW README claim bullet the map does not cover.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.docmap import claim_census as I6                          # noqa: E402


class TestI6PublicClaimCensus(unittest.TestCase):

    def test_every_quote_is_verbatim_in_the_readme(self):
        readme = I6.load_readme()
        missing = I6.missing_quotes(readme)
        self.assertEqual(missing, [], "claim quote(s) not found verbatim in the public README — "
                                      "the map drifted from the owner's words: %s" % missing)

    def test_every_proving_test_resolves(self):
        bad = I6.unresolvable_tests()
        self.assertEqual(bad, [], "claim(s) map to a test id that does not resolve (renamed or "
                                  "deleted test): %s" % bad)

    def test_no_claim_lacks_both_a_test_and_a_tag(self):
        unproven = I6.unproven_claims()
        self.assertEqual(unproven, [], "claim(s) with NEITHER a proving test nor a "
                                       "designed-not-built tag: %s" % unproven)

    def test_every_readme_claim_bullet_is_covered(self):
        # THE STANDING GUARD: a NEW public claim bullet the map does not cover reds here.
        readme = I6.load_readme()
        uncovered = I6.uncovered_bullets(readme)
        self.assertEqual(uncovered, [], "public README claim bullet(s) not mapped to any claim — "
                                        "a new public claim with no proving test or tag: %s" % uncovered)

    def test_evidence_table_regenerates(self):
        generated = I6.render_markdown()
        with open(os.path.join(os.path.dirname(__file__), "..", "planning", "evidence",
                               "EP-INSTRUMENTS-1", "public-claims.md"), encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(generated.strip(), committed.strip(),
                         "the public-claim map diverged from the committed evidence — regenerate: "
                         "python3 -m tools.docmap.claim_census --md")

    # ---- planted positives (must fire) ----

    def test_planted_positive_a_bogus_test_id_is_caught(self):
        # a claim mapping to a nonexistent test MUST be reported unresolvable.
        original = list(I6.CLAIMS)
        try:
            I6.CLAIMS.append({"id": "planted-bogus", "quote": "Run it",
                              "proving": "test_does_not_exist_xyz.NoSuchClass.no_such_method",
                              "note": "planted"})
            self.assertIn("planted-bogus", I6.unresolvable_tests(),
                          "the census did not catch a claim mapped to a nonexistent test — the "
                          "resolver cannot fail, so the census proves nothing")
        finally:
            I6.CLAIMS[:] = original

    def test_planted_positive_an_uncovered_new_claim_is_caught(self):
        # a README that grew a new claim bullet the map does not cover MUST be flagged.
        fake_readme = (I6.CLAIM_SECTION_HEADING + "\n\n"
                       "- A brand new public promise nothing here maps to and nothing proves.\n")
        uncovered = I6.uncovered_bullets(fake_readme)
        self.assertEqual(len(uncovered), 1,
                         "the census did not flag an unmapped new claim bullet — the coverage "
                         "guard cannot fail, so the census proves nothing")


class TestI6BPublicFrontClaimCensus(unittest.TestCase):
    """EP-I6B — the census extended to the three SHIPPED public front pages (`../awig-os/`
    README, STATUS, ARCHITECTURE). Every checkable claim maps to a test id that RESOLVES or a
    pinned gap row (designed-not-built / stated-gap, with its reason). The SET is exact."""

    def test_every_front_quote_is_verbatim_in_its_named_page(self):
        missing = I6.front_missing_quotes()
        self.assertEqual(missing, [], "front-claim quote(s) not found verbatim in their named public "
                                      "front page — the map drifted from the owner's words: %s" % missing)

    def test_every_front_proving_test_resolves(self):
        bad = I6.front_unresolvable_tests()
        self.assertEqual(bad, [], "front claim(s) map to a test id that does not resolve (renamed or "
                                  "deleted test): %s" % bad)

    def test_no_front_claim_lacks_a_mapping(self):
        unproven = I6.front_unproven_claims()
        self.assertEqual(unproven, [], "front claim(s) with NO valid mapping — neither a proving test "
                                       "nor a gap sentinel carrying a reason: %s" % unproven)

    def test_every_status_claim_bullet_is_covered(self):
        # THE STANDING GUARD: a NEW bullet claim under STATUS.md's claim-inventory headings that the
        # map does not cover reds here (the analog of I6's uncovered_bullets, anchored to STATUS —
        # the only one of the three that bullets its claims).
        uncovered = I6.front_uncovered_status_bullets()
        self.assertEqual(uncovered, [], "STATUS.md claim bullet(s) not mapped to any front claim — a "
                                        "new public claim with no proving test or gap row: %s" % uncovered)

    def test_front_evidence_table_regenerates(self):
        # THE EXACT-SET GUARD: add-a-claim or drop-a-mapping changes the rendered census and reds
        # here until the committed evidence is regenerated. The census is exact, not >=.
        generated = I6.render_front_markdown()
        with open(os.path.join(os.path.dirname(__file__), "..", "planning", "evidence",
                               "EP-I6B", "public-front-claims.md"), encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(generated.strip(), committed.strip(),
                         "the public front-page claim map diverged from the committed evidence — "
                         "regenerate: python3 -m tools.docmap.claim_census --md-front")

    # ---- planted positives (each must fire — a guard that cannot fail proves nothing) ----

    def test_planted_positive_a_bogus_front_test_id_is_caught(self):
        original = list(I6.FRONT_CLAIMS)
        try:
            I6.FRONT_CLAIMS.append({"id": "planted-bogus-test", "doc": "STATUS", "quote": "Run it",
                                    "proving": "test_does_not_exist_xyz.NoSuchClass.no_such_method",
                                    "why": "planted"})
            self.assertIn("planted-bogus-test", I6.front_unresolvable_tests(),
                          "the census did not catch a front claim mapped to a nonexistent test — the "
                          "resolver cannot fail, so the census proves nothing")
        finally:
            I6.FRONT_CLAIMS[:] = original

    def test_planted_positive_a_claim_with_no_mapping_is_caught(self):
        # A2: a planted bogus claim with NO mapping REDS.
        original = list(I6.FRONT_CLAIMS)
        try:
            I6.FRONT_CLAIMS.append({"id": "planted-no-mapping", "doc": "STATUS",
                                    "quote": "The written record is tamper-evident",
                                    "proving": "", "why": ""})
            self.assertIn("planted-no-mapping", I6.front_unproven_claims(),
                          "the census did not flag a claim with no proving test and no gap row — the "
                          "unproven guard cannot fail, so the census proves nothing")
        finally:
            I6.FRONT_CLAIMS[:] = original

    def test_planted_positive_a_gap_row_without_a_reason_is_caught(self):
        # a stated-gap row must carry WHY it is not machine-checkable; an empty reason REDS.
        original = list(I6.FRONT_CLAIMS)
        try:
            I6.FRONT_CLAIMS.append({"id": "planted-reasonless-gap", "doc": "STATUS",
                                    "quote": "One machine, one user",
                                    "proving": I6.STATED_GAP, "why": "   "})
            self.assertIn("planted-reasonless-gap", I6.front_unproven_claims(),
                          "the census accepted a stated-gap row with no reason — a silent skip in "
                          "disguise; the gap must name why it is not machine-checkable")
        finally:
            I6.FRONT_CLAIMS[:] = original

    def test_planted_positive_an_uncovered_new_status_bullet_is_caught(self):
        # a STATUS page that grew a new claim bullet the map does not cover MUST be flagged.
        fake_status = (STATUS_HEADING + "\n\n"
                       "- A brand new public promise nothing here maps to and nothing proves.\n")
        uncovered = I6.front_uncovered_status_bullets(fake_status)
        self.assertEqual(len(uncovered), 1,
                         "the census did not flag an unmapped new STATUS claim bullet — the coverage "
                         "guard cannot fail, so the census proves nothing")

    def test_planted_positive_a_drifted_front_quote_is_caught(self):
        # a claim whose quote is NOT verbatim in its named page MUST be reported as drift.
        original = list(I6.FRONT_CLAIMS)
        try:
            I6.FRONT_CLAIMS.append({"id": "planted-drift", "doc": "README",
                                    "quote": "this exact phrase is nowhere in the public README zzz",
                                    "proving": I6.STATED_GAP, "why": "planted"})
            self.assertIn("planted-drift", I6.front_missing_quotes(),
                          "the census did not catch a quote absent from its named page — the drift "
                          "guard cannot fail, so the census proves nothing")
        finally:
            I6.FRONT_CLAIMS[:] = original

    def test_planted_positive_adding_a_claim_reds_the_exact_set(self):
        # A3: the SET is exact — adding a claim changes the rendered census (drop would too).
        baseline = I6.render_front_markdown()
        original = list(I6.FRONT_CLAIMS)
        try:
            I6.FRONT_CLAIMS.append({"id": "planted-set-drift", "doc": "STATUS",
                                    "quote": "One machine, one user",
                                    "proving": I6.STATED_GAP, "why": "planted"})
            self.assertNotEqual(I6.render_front_markdown(), baseline,
                                "adding a claim did not change the rendered census — the exact-set "
                                "regenerate guard cannot fail, so the SET is not pinned")
        finally:
            I6.FRONT_CLAIMS[:] = original


# STATUS.md's first claim-inventory heading — used by the planted uncovered-bullet control.
STATUS_HEADING = I6.STATUS_CLAIM_SECTIONS[0]


if __name__ == "__main__":
    unittest.main()
