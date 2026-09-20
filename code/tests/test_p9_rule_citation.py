# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (cited rule, local resolution, received row, active constitution view, cache-kill
# recompute, chokepoint refusal); NON-GOAL: no offensive capability of any kind — this proves every
# rule a child obeys resolves inside the child's own record and refuses a received row citing an
# unmapped rule, loudly and by name, by function. Full declaration: SCOPE-STATEMENT.md.
"""C6 P9 — RULE CITATION ACROSS RECORDS (design/52 B4:53 resolved :3755, I6:78, I22:94; plan
planning/exec/P9-RULE-CITATION-ACROSS-RECORDS-BUILD.md).

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). P9 CENSUSES what P10 built (the received row, the adoption citing by
hash, the active-constitution view over received+adopted rows) and ADDS ONE chokepoint guard (I22).
It MINTS NOTHING — no op, law or check kind, NO NEW FIELD, no pack edit (Q4 discharged by the owner
:3755: the child cites its OWN local copy, the parent derived; the received row already carries the
lineage). P10's border machinery is READ and REUSED, never re-authored.

  A1 (I6)  EVERY CITED RULE RESOLVES LOCALLY. A census over the child's whole record confirms every
      rule_cited resolves inside the child's OWN record (a local rule id, or a local received copy by
      hash). A PLANTED rule_cited resolving only in a foreign record reds (the check can fail).
  A2 (I6, cache-kill)  RECOMPUTE EQUALS SERVED. the active constitution recomputed from the child's
      received+adopted rows ALONE equals the served constitution; a planted divergence (a served rule
      with no received+adopted origin, or a received+adopted rule absent from served) reds.
  A3 (I22)  A RECEIVED ROW CITING AN UNMAPPED RULE REFUSES LOUDLY BY NAME. a planted received row
      citing a (relation, rule hash) the child holds NO received row for is REFUSED AT THE RECEIPT
      CHOKEPOINT, and the refusal NAMES THE MISSING MAPPING — not a generic code; the generic-code
      control shows the check can red on a regression that hides the mapping.
  A4 (B4)  CITATION THROUGH THE LOCAL COPY, NO NEW FIELD. a child's adoption cites the parent rule by
      the received row's content hash in the adoption VALUE slot; record-identity and rule-hash derive
      from that copy; the lineage (relation, rule hash, source parent) is kept; the founding pack is
      byte-unchanged.
  A5       NO FOUNDING — no new op/law/check kind, no new field, no pack edit (asserted by census).
  A6       whole ledger green PER MODULE (the per-module `python3 -m unittest tests.test_p9_rule_citation`).

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect): a planted foreign citation reds the census; a planted recompute divergence reds it; a
planted unmapped citation is refused at the chokepoint AND the refusal names the missing mapping (a
generic-code refusal would red the specificity control).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel import border, keys                                      # noqa: E402
from tools.conformance import rule_citation_census as rcc            # noqa: E402


PARENT_KEY = "ed25519-pub:parent"


def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    """RELEASE-4 round 3 (owner :4656): the ONE case in this module that shells out to git (the pack
    byte-unchanged reading, `git diff`) is guarded by this probe -- git present AND this tree a git
    checkout with a HEAD. In the lab the probe is true and the case RUNS; in the render (no .git, or no
    git binary on a stock box) it SKIPS by name instead of erroring. The established RENDER-NO-GIT
    form (test_p11_handshake and five siblings), unchanged. No other case is touched."""
    import subprocess as _sp
    _root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    try:
        return _sp.run(["git", "-C", _root, "rev-parse", "--verify", "HEAD"],
                       capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()


def _body(prefix, entity="child", actor_class="ai"):
    """One child BODY — an independent record, gate and views, with `entity` an account so it may
    open a crossing. Reuses P10's body shape (one pen per record, the single-writer lock)."""
    d = tempfile.mkdtemp(prefix=prefix)
    store, gate, views, _blobs, _subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": entity, "actor_class": actor_class})
    return d, store, gate, views


def _parent_name(genesis="sha256:" + "beef" * 16, key=PARENT_KEY):
    return border.from_body_name(key, genesis)


def _declare_relation(gate, parent_name, entity="child"):
    declare = border.submit(gate, entity, {"handshake_relation": {"parent": parent_name}}, actor=entity)
    return border.content_id(declare)


def _parent_rule(rule_id, scope=None, seq=1000, extra=None):
    """A parent RULE record as it crosses to the child (a CREATE-RULE-shaped row). `extra` merges into
    the payload — the vehicle for a crossed rule that itself CITES another rule (`rule_cited`)."""
    payload = {"rule_id": rule_id, "scope": scope, "policy_key": "govern", "value": "the-rule-body"}
    if extra:
        payload.update(extra)
    return {"actor": "parent", "action": "CREATE-RULE", "object": rule_id, "target": None,
            "payload": payload, "seq": seq, "record_time": "2026-09-10T00:00:00Z"}


def _mark(rule_record, key=PARENT_KEY):
    return keys.countersign(rule_record, key)


def _received_child():
    """A child that has RECEIVED two parent rules and ADOPTED one — the census subject for A1/A2."""
    d, store, gate, views = _body("p9-received-")
    rid = _declare_relation(gate, _parent_name())
    adopted = _parent_rule("PARENT-SPEND", scope="spend")
    unadopted = _parent_rule("PARENT-TRADE", scope="trade", seq=1001)
    border.receive_parent_rule(gate, views, rid, adopted, _mark(adopted))
    border.receive_parent_rule(gate, views, rid, unadopted, _mark(unadopted))
    border.adopt_received_rule(gate, border.content_id(adopted), "child-obeys-spend", scope="spend")
    return d, store, gate, views, rid, adopted, unadopted


# =============================================================================================
# A1 (I6) — EVERY CITED RULE RESOLVES LOCALLY
# =============================================================================================

class TestEveryCitedRuleResolvesLocally(unittest.TestCase):
    def test_the_census_is_green_every_rule_cited_resolves_inside_the_childs_own_record(self):
        """I6 half 1: over a child's whole record — founding rows, the child's acts, the receipts,
        the adoption — every rule_cited resolves to a local rule id or a local received copy. The
        census reads a real record and finds ZERO foreign citations."""
        _d, store, _gate, views, *_ = _received_child()
        result = rcc.census(store, views)
        self.assertTrue(rcc.is_green(result))
        self.assertEqual(result["counts"]["foreign"], 0)
        self.assertGreater(result["counts"]["cited"], 0)            # the census actually read citations

    def test_RW_a_planted_rule_cited_resolving_only_in_a_foreign_record_reds(self):
        """I6 half 1 / THE POSITIVE CONTROL (able-to-fail): a record citing a rule that exists ONLY in
        the parent's record — not a local rule id, not a local received copy — is FOREIGN and reds the
        census. Discriminating: the SAME citation added to the local universe resolves (no false red)."""
        _d, store, _gate, views, *_ = _received_child()
        rule_ids = rcc.local_rule_ids(views)
        received = rcc.local_received_hashes(store)
        planted = {"seq": 9001, "action": "SPEND", "rule_cited": "PARENT-ONLY-RULE"}   # foreign rule id
        red = rcc.foreign_citations([planted], rule_ids, received)
        self.assertEqual(len(red), 1)                                # the plant is caught
        self.assertEqual(red[0]["rule_cited"], "PARENT-ONLY-RULE")
        # discriminates: once the child holds it locally (a rule id), the same citation resolves.
        self.assertEqual(rcc.foreign_citations([planted], rule_ids | {"PARENT-ONLY-RULE"}, received), [])
        # a hash-form citation to a LOCAL received copy resolves; an unheld hash is foreign.
        held_hash = next(iter(received))
        self.assertEqual(rcc.foreign_citations(
            [{"seq": 9002, "action": "SPEND", "rule_cited": held_hash}], rule_ids, received), [])
        self.assertEqual(len(rcc.foreign_citations(
            [{"seq": 9003, "action": "SPEND", "rule_cited": "sha256:" + "0" * 64}], rule_ids, received)), 1)


# =============================================================================================
# A2 (I6, the cache-kill form) — RECOMPUTE EQUALS SERVED
# =============================================================================================

class TestRecomputeEqualsServed(unittest.TestCase):
    def test_the_served_constitution_recomputes_from_received_and_adopted_rows_alone(self):
        """I6 half 2 (the cache-kill): the served active constitution equals the intersection
        recomputed from the child's received + adopted rows alone — no phantom, nothing omitted."""
        _d, store, _gate, _views, *_ = _received_child()
        served = border.active_constitution(store)
        received = border.received_parent_rules(store)
        adopted = border.adoptions(store)
        div = rcc.recompute_divergences(served, received, adopted)
        self.assertEqual(div["served_without_origin"], [])
        self.assertEqual(div["recomputed_absent_from_served"], [])
        self.assertEqual(len(served), 1)                             # exactly the one adopted rule

    def test_RW_a_planted_divergence_reds_both_directions(self):
        """I6 half 2 / THE POSITIVE CONTROL (able-to-fail): a served rule with NO received+adopted
        origin (a phantom) reds; a received+adopted rule ABSENT from the served view reds. The pure
        predicate takes explicit served/received/adopted, so a divergence can be handed in and MUST
        fire."""
        _d, store, _gate, _views, *_ = _received_child()
        served = dict(border.active_constitution(store))
        received = border.received_parent_rules(store)
        adopted = border.adoptions(store)
        # (a) a PHANTOM served rule with no origin.
        phantom = dict(served)
        phantom["sha256:" + "a" * 64] = {"rule_id": "phantom"}
        red_a = rcc.recompute_divergences(phantom, received, adopted)
        self.assertIn("sha256:" + "a" * 64, red_a["served_without_origin"])
        # (b) a received+adopted rule ABSENT from the served view.
        red_b = rcc.recompute_divergences({}, received, adopted)
        self.assertEqual(len(red_b["recomputed_absent_from_served"]), len(served))
        self.assertTrue(all(h in received and h in adopted
                            for h in red_b["recomputed_absent_from_served"]))


# =============================================================================================
# A3 (I22) — A RECEIVED ROW CITING AN UNMAPPED RULE REFUSES LOUDLY BY NAME
# =============================================================================================

class TestUnmappedCitationRefusesLoudlyByName(unittest.TestCase):
    def setUp(self):
        self.d, self.store, self.gate, self.views = _body("p9-i22-")
        self.rid = _declare_relation(self.gate, _parent_name())
        # a first parent rule the child DOES hold a received row for (the mapped citation target).
        self.base = _parent_rule("PARENT-BASE", scope="base")
        border.receive_parent_rule(self.gate, self.views, self.rid, self.base, _mark(self.base))
        self.base_hash = border.content_id(self.base)

    def test_a_received_rule_citing_a_LOCALLY_HELD_parent_rule_by_hash_is_admitted(self):
        """I22 (the GREEN world — the guard must not over-refuse): a received rule whose crossed body
        cites a parent rule the child DOES hold a received row for (by hash, same relation) is admitted
        — the citation resolves to the child's own local received copy."""
        citing = _parent_rule("PARENT-AMENDS", scope="base", seq=1002,
                              extra={"rule_cited": self.base_hash})   # cites the HELD base rule by hash
        out = border.receive_parent_rule(self.gate, self.views, self.rid, citing, _mark(citing))
        self.assertIn(border.content_id(citing), border.received_parent_rules(self.store))
        self.assertEqual(out["received_rule"]["body"]["rule_cited"], self.base_hash)

    def test_RW_a_received_rule_citing_an_UNMAPPED_hash_is_refused_at_the_chokepoint_by_name(self):
        """I22 / THE LOAD-BEARING CONTROL (able-to-fail): a received rule whose crossed body cites a
        (relation, rule hash) the child holds NO received row for is REFUSED AT THE RECEIPT CHOKEPOINT
        and RECORDED, and the refusal NAMES THE EXACT MISSING MAPPING (the relation and the hash) —
        never a generic code. 'A fallback that answers is a check that cannot fail' (I22)."""
        missing_hash = "sha256:" + "d" * 64                          # a hash the child holds no received row for
        citing = _parent_rule("PARENT-DANGLING", scope="base", seq=1003,
                              extra={"rule_cited": missing_hash})
        before = len(self.store.all())
        with self.assertRaises(OpError) as cm:
            border.receive_parent_rule(self.gate, self.views, self.rid, citing, _mark(citing))
        self.assertEqual(cm.exception.rule, "COMM-LAW-CONTRACT")
        msg = cm.exception.message
        # THE MISSING MAPPING IS NAMED — the exact (relation, rule hash), not a generic code.
        self.assertIn(missing_hash, msg)                             # the rule hash, by name
        self.assertIn(self.rid, msg)                                 # the relation, by name
        # RECORDED: a refusal row landed and the dangling citation did NOT enter the received fold.
        self.assertGreater(len(self.store.all()), before)
        self.assertNotIn(border.content_id(citing), border.received_parent_rules(self.store))

    def test_the_specificity_control_a_generic_code_regression_would_red(self):
        """I22's SPECIFICITY CONTROL (the check that CAN fail on a regression): the refusal names the
        exact missing mapping, so a regression that answered with a GENERIC CODE — a message NOT
        carrying the (relation, rule hash) — would fail this assertion. We prove the assertion
        discriminates: a generic message does NOT contain the mapping, the real refusal DOES."""
        missing_hash = "sha256:" + "e" * 64
        citing = _parent_rule("PARENT-DANGLING-2", scope="base", seq=1004,
                              extra={"rule_cited": missing_hash})
        with self.assertRaises(OpError) as cm:
            border.receive_parent_rule(self.gate, self.views, self.rid, citing, _mark(citing))
        real = cm.exception.message
        generic = "EINVAL: invalid argument"                         # the banned generic-code shape
        # the specificity test that gates the guard: the mapping is IN the real refusal, NOT in a
        # generic code. A guard that regressed to `generic` would fail `assertIn(missing_hash, msg)`.
        self.assertIn(missing_hash, real)
        self.assertNotIn(missing_hash, generic)
        self.assertNotIn(self.rid, generic)

    def test_the_guard_is_inert_for_a_received_rule_citing_a_same_record_rule_by_id(self):
        """I22 is INERT for a same-record citation (a bare rule id, not a hash) — the I6 census reads
        those, not this chokepoint. A received rule whose body cites a founding rule by id is admitted;
        the guard fires only on a cross-record citation BY HASH with no local received copy."""
        citing = _parent_rule("PARENT-CITES-FOUNDING", scope="base", seq=1005,
                              extra={"rule_cited": "ROOT-NEG-6"})     # a bare rule id, not a hash
        out = border.receive_parent_rule(self.gate, self.views, self.rid, citing, _mark(citing))
        self.assertIn(border.content_id(citing), border.received_parent_rules(self.store))
        self.assertEqual(out["received_rule"]["body"]["rule_cited"], "ROOT-NEG-6")


# =============================================================================================
# A4 (B4) — CITATION THROUGH THE LOCAL COPY, NO NEW FIELD
# =============================================================================================

class TestCitationThroughTheLocalCopyNoNewField(unittest.TestCase):
    def test_the_adoption_cites_the_parent_rule_by_the_received_rows_hash_in_the_value_slot(self):
        """B4 (resolved :3755): the child's adoption cites the parent rule by the received row's content
        hash in the adoption's VALUE slot (border.py:803); record-identity and rule-hash derive from
        that LOCAL copy, and the citation resolves inside the child's own record (the received row)."""
        _d, store, _gate, _views, _rid, adopted, _unadopted = _received_child()
        h = border.content_id(adopted)
        adoptions = border.adoptions(store)
        self.assertIn(h, adoptions)                                  # keyed by the cited hash
        self.assertEqual(adoptions[h]["received_rule_hash"], h)      # cites BY HASH, in the value slot
        self.assertIn(h, border.received_parent_rules(store))        # the cited rule is the child's own local copy

    def test_the_lineage_relation_rule_hash_source_parent_is_kept_on_the_received_row(self):
        """B4: the received row keeps the lineage (relation, rule hash, source parent) — the parent is
        DERIVED from the local copy, never a new field naming the other machine in the citation slot."""
        _d, store, _gate, _views, rid, adopted, _unadopted = _received_child()
        h = border.content_id(adopted)
        rr = border.received_parent_rules(store)[h]
        self.assertEqual(rr["relation_id"], rid)                     # the relation, kept
        self.assertEqual(rr["rule_hash"], h)                         # the rule hash, kept
        self.assertEqual(rr["source"], "parent")                    # the source parent, kept

    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: needs git and a git checkout (the render is not a "
                         "git checkout) -- the pack byte-unchanged reading shells out to git diff")
    def test_A4_A5_the_founding_pack_is_byte_unchanged_no_new_field_no_founding(self):
        """A4/A5: P9 mints NO founding and adds NO field — the founding pack is byte-unchanged. The
        received-row shape is P10's (source, record_class, rule_id, rule_hash, scope, body,
        relation_id, receipt_seq) — this unit adds none. Proven by the git working tree over the pack
        and by the received-row key set."""
        import subprocess
        repo = os.path.join(os.path.dirname(__file__), "..")
        diff = subprocess.run(["git", "diff", "--stat", "src/founding/founding-pack.json"],
                              cwd=repo, capture_output=True, text=True)
        self.assertEqual(diff.stdout.strip(), "")                    # pack byte-unchanged
        _d, store, _gate, _views, _rid, adopted, _unadopted = _received_child()
        rr = border.received_parent_rules(store)[border.content_id(adopted)]
        self.assertEqual(set(rr.keys()),
                         {"source", "record_class", "rule_id", "rule_hash", "scope", "body",
                          "relation_id", "receipt_seq"})             # P10's shape, no new field


# =============================================================================================
# A6 — WHOLE LEDGER GREEN PER MODULE (the per-module suite drive)
# =============================================================================================

class TestA6WholeLedgerSmoke(unittest.TestCase):
    def test_census_and_guard_compose_end_to_end_on_a_fresh_founded_child(self):
        """A6 smoke: the whole path composes on a fresh founded child — receive, adopt, the census
        green, a mapped citation admitted, an unmapped citation refused. (The per-module
        `python3 -m unittest tests.test_p9_rule_citation` IS the ledger-green drive for this unit.)"""
        d, store, gate, views = _body("p9-a6-")
        rid = _declare_relation(gate, _parent_name())
        base = _parent_rule("A6-BASE", scope="s")
        border.receive_parent_rule(gate, views, rid, base, _mark(base))
        border.adopt_received_rule(gate, border.content_id(base), "child-a6", scope="s")
        self.assertTrue(rcc.is_green(rcc.census(store, views)))
        # a citation to the held base rule is admitted; a dangling one is refused by name.
        ok = _parent_rule("A6-OK", scope="s", seq=1001, extra={"rule_cited": border.content_id(base)})
        border.receive_parent_rule(gate, views, rid, ok, _mark(ok))
        bad = _parent_rule("A6-BAD", scope="s", seq=1002, extra={"rule_cited": "sha256:" + "f" * 64})
        with self.assertRaises(OpError):
            border.receive_parent_rule(gate, views, rid, bad, _mark(bad))


if __name__ == "__main__":
    unittest.main()
