# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-tests · OS/border vocabulary
# (border, crossing, submit, content hash, seal, edition) per the seL4/gVisor and reproducible-build
# literature. NON-GOAL: no offensive capability of any kind — this proves an OUTSIDE pack's round trip
# through the already-built door with a DUMMY submitter; it founds nothing, builds nothing in src/,
# breaks nothing. The pack is DATA the gate decides a crossing over, never a gov-os decision. Full
# declaration: SCOPE-STATEMENT.md.
"""EP-51 — TWC v0.1 THROUGH THE DOOR AND THE ROUND TRIP (design/51 N7, §5 EP-51, §8, §9). THE TRACER.

Named in planning/exec/EP-51-BUILD.md before code, landed here as regression tests (charter: every
verification probe lands as a regression test). This battery proves the WHOLE border round trip end
to end with a DUMMY outside submitter, building nothing TWC-specific:

  A1  a dummy TWC v0.1 pack (rows + batch as DATA) is founded as an OUTSIDE entity through
      BORDER-SUBMIT (require_prior over CREATE-ACCOUNT, NO peer-minted token), its crossing
      identified by content_id; a census shows ZERO TWC-specific symbols in src/ (D08.41: nothing
      wrapped — the record is gov-os's, TWC is a submitter).
  A2  the round trip pack hash -> the crossing's content hash (content_id) -> the serviced view
      (EP-50) -> the human edition (tools/release/edition.py); the content hash recomputes EQUAL at
      each hop (border.py:92, the round-trip property).
  A3  drift both ways: a changed byte of the PACK moves the content hash (forward); a changed byte of
      what was SHOWN fails the BORDER-REPLY seal (backward). Both proven able to fail.
  A4  the anchor EXCLUDES record_time (D08.40 driven): content_id hashes action/object/target/payload
      only; the SAME pack submitted at two different record_times yields the SAME content hash, so the
      round trip reproduces from the pack alone. The prev_hash chain INCLUDES record_time (correct; it
      seals WHEN a record landed) — named here, not asserted to exclude.
  A5  the unstructured-row count is published WITH ITS WORLD (pack version + source + as-of head),
      never a bare number (the master gradient: a count without its world is not a fact).
  A6  a planted post-cut drift is CAUGHT (the check_clean_from_cut --selftest precedent); the control
      is proven able to fail.
  A7  zero new check kinds minted (OP_CHECKS unchanged at 17; founding-pack byte-identical); the
      candidate check kinds a real TWC would need are RAISED BY NAME (owner's one word; N7 is a raise).

THE PACK IS DERIVED, NOT INVENTED (architect :3393 precision 1): the dummy pack's rows and batch are
generated from apps/pwc-app's OWN law rows (law/law-book.jsonl, 233 rows) and its R31 founding batch
(160 acts), READ-ONLY of pwc-app — so the published unstructured count measures the REAL constitution's
fit through the door, and names the pack version and the source as its world.

THE PEER'S ROWS LAND AS INPUT, NEVER A DECISION (N4; RW-PEER-TRUSTED): the gate decides the crossing;
the pack rows inside it are DATA the renderer re-presents and the census confirms were never founded
as gov-os law (A1 / A7). Nothing in the submit's content is trusted as gov-os truth.
"""

import hashlib
import json
import os
import re
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "tools", "release"))

from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.opdefs import OP_CHECKS                                   # noqa: E402
from kernel import border, canonical, crypto                         # noqa: E402
from kernel.signer import SigningKeyStore                            # noqa: E402
import edition                                                       # noqa: E402  the new pure renderer

# apps/pwc-app is the SIBLING app whose real constitution the dummy pack is derived from (read-only).
PWC = os.path.join(REPO, "..", "pwc-app")
LAW_BOOK = os.path.join(PWC, "law", "law-book.jsonl")
R31_BATCH = os.path.join(PWC, "R31-PWC-FOUNDING-BATCH.json")

TWC_VERSION = "0.1.0"                       # the dummy TWC pack's declared version (v0.1)
SYSTEM_SEED = bytes(range(32))             # a fixed system signing seed for the seal arm (a secret)


# =============================================================================================
# THE CANDIDATE CHECK KINDS — a real TWC would need these; gov-os LACKS them. Two sources (C10,
# design/51 N7): design/42 §2.2/§2.5, and TWC's own rows (D08.39). Each maps to a SHAPE marker over
# a law row's text/policyKey. A row matching any is carried UNSTRUCTURED (enforced_by: judgment) —
# its structured shape needs a check kind this constitution does not have. RAISED BY NAME, NEVER
# MINTED here (A7 / stop-e; N7 is a raise, the owner's one word).
# =============================================================================================

CANDIDATE_KINDS = {
    "quorum":            {"source": "design/42 §2.5 + D08.39 (committee quorum shapes)",
                          "shape": re.compile(r"quorum|ballot|deliberat|deadlock|majority|consensus|\bvote", re.I)},
    "should_verdict":    {"source": "design/42 §2.2 (SHOULD / allow-with-recorded-justification)",
                          "shape": re.compile(r"\bshould\b|justif|discretion|allow[- ]with", re.I)},
    "escalate":          {"source": "design/42 §2.5 (ESCALATE as a gate outcome)",
                          "shape": re.compile(r"escalat", re.I)},
    "blind_position":    {"source": "D08.39 (blind positions / designed blindness)",
                          "shape": re.compile(r"\bblind|blindness", re.I)},
    "focus_lock":        {"source": "D08.39 (focus-lock)",
                          "shape": re.compile(r"focus-lock|focus lock", re.I)},
    "sight_binds_writes": {"source": "D08.39 (sight-binds-writes)",
                           "shape": re.compile(r"sight-bind|sight binds", re.I)},
}


def _needs_kinds(blob):
    """Which candidate (missing) check kinds a law row's text needs — the shape markers it matches.
    Empty => the row maps to an EXISTING gov-os kind (structured)."""
    return sorted(k for k, spec in CANDIDATE_KINDS.items() if spec["shape"].search(blob))


def _sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def derive_twc_pack():
    """DERIVE the dummy TWC v0.1 pack from apps/pwc-app's OWN law rows + R31 founding batch, READ-ONLY
    (architect :3393 precision 1). The pack is DATA — never founded, never trusted, never a gov-os
    decision. Each law row is classified deterministically:

      reference row (contentType 'reference')  -> UNSTRUCTURED, enforced_by 'judgment', class 'context'
                                                  (context, not an enforceable rule shape)
      rule row matching a candidate-kind shape  -> UNSTRUCTURED, enforced_by 'judgment', needs [kinds]
      rule row matching none                    -> STRUCTURED,  enforced_by 'structured'

    The published unstructured count (N7) is the rows whose structured shape needs a check kind this
    constitution LACKS. Deterministic: same source bytes -> same pack. Returns the pack dict, whose
    `source` names its world (the law-book + batch sha256, the pack version)."""
    if not (os.path.exists(LAW_BOOK) and os.path.exists(R31_BATCH)):
        raise unittest.SkipTest("apps/pwc-app is not present beside gov-os; the derived pack needs it")
    with open(LAW_BOOK, encoding="utf-8") as fh:
        law_rows = [json.loads(ln) for ln in fh if ln.strip()]
    with open(R31_BATCH, encoding="utf-8") as fh:
        batch = json.load(fh)
    acts = batch.get("acts", [])

    rows, needs_missing, context = [], 0, 0
    by_kind = {k: 0 for k in CANDIDATE_KINDS}
    for r in law_rows:
        rid = r.get("ruleId")
        blob = (r.get("text", "") or "") + " " + str(r.get("policyKey", "") or "")
        if r.get("contentType") == "reference":
            enforced, needs, cls = "judgment", [], "context"
            context += 1
        else:
            needs = _needs_kinds(blob)
            if needs:
                enforced, cls = "judgment", "unstructured"
                needs_missing += 1
                for k in needs:
                    by_kind[k] += 1
            else:
                enforced, cls = "structured", "structured"
        rows.append({"row_id": rid, "tier": r.get("tier"), "module": r.get("module"),
                     "text": r.get("text", ""), "enforced_by": enforced, "needs": needs, "class": cls})

    structured = sum(1 for x in rows if x["class"] == "structured")
    pack = {
        "pack": "TWC",
        "version": TWC_VERSION,
        "source": {"repo": "apps/pwc-app (sibling; read-only)",
                   "law_book_sha256": _sha256_file(LAW_BOOK),
                   "batch_sha256": _sha256_file(R31_BATCH),
                   "law_rows": len(law_rows), "batch_acts": len(acts)},
        "rows": rows,
        "acts": acts,
        "unstructured": {"count": needs_missing, "of": len(law_rows),
                         "structured": structured, "context": context,
                         "by_kind": {k: v for k, v in by_kind.items() if v}},
        "candidate_kinds": {k: {"source": spec["source"], "count": by_kind[k]}
                            for k, spec in CANDIDATE_KINDS.items()},
    }
    return pack


def publish_count(pack, *, as_of_head, founding_version):
    """Publish the unstructured-row count WITH ITS WORLD (A5, RW-BARE-COUNT). A count is not a fact
    without its world: the pack version, the source it was derived from, and the gov-os head it was
    serviced over. Returns the published object; `world_named` below is able to reject a bare count."""
    return {"unstructured_rows": pack["unstructured"]["count"],
            "world": {"pack": pack["pack"], "version": pack["version"],
                      "derived_from": pack["source"], "as_of_head": as_of_head,
                      "founding_version": founding_version}}


def world_named(published):
    """Is a published count accompanied by its FULL world (A5, the check that can fail)? A bare
    `{"unstructured_rows": N}` with no world, or a world missing any field, is REFUSED."""
    w = published.get("world")
    if not isinstance(w, dict):
        return False
    return all(w.get(f) is not None for f in ("pack", "version", "derived_from",
                                              "as_of_head", "founding_version"))


def pack_hash(pack):
    """The pack's DATA identity — the estate's ONE canonical hash over the pack as data."""
    return canonical.canonical_hash(pack)


def _founding_version():
    with open(os.path.join(REPO, "src", "founding", "founding-pack.json"), encoding="utf-8") as fh:
        return json.load(fh).get("founding_version")


class _World(unittest.TestCase):
    """A kernel from the SHIPPED founding, with the OUTSIDE entity 'twc' established to submit by."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep51-")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        # the OUTSIDE entity founds itself on the record first — recorded establishment, never a
        # peer-minted token (BORDER-SUBMIT's require_prior over CREATE-ACCOUNT).
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "twc", "actor_class": "agentic"})
        self.pack = derive_twc_pack()

    def a_submit(self, pack=None):
        """The dummy TWC pack crosses the border as ONE draft (the whole pack as DATA). The crossing
        is attributed to the 'twc' entity that willed it (design/39 §3)."""
        return border.submit(self.gate, "twc", {"pack": pack if pack is not None else self.pack})


# =============================================================================================
# A1 — T-TWC-FOUNDED-THROUGH-DOOR (+ RW-TWC-BUILT census, RW-PEER-TRUSTED)
# =============================================================================================

class TestTwcFoundedThroughDoor(_World):
    def test_the_dummy_pack_is_admitted_as_an_outside_entity_through_border_submit(self):
        sub = self.a_submit()
        self.assertEqual(sub["action"], "BORDER-SUBMIT")
        self.assertEqual((sub.get("payload") or {}).get("kind"), "border-submit")
        self.assertEqual((sub.get("payload") or {}).get("record_class"), "DECISION")
        self.assertEqual(sub["rule_cited"], "COMM-LAW-CONTRACT")
        # the crossing exists as a DERIVED fold keyed by the submit's own content hash.
        cid = border.content_id(sub)
        self.assertIn(cid, border.submits(self.store))
        # the pack CROSSED as data — the entity that WILLED it is 'twc', never the system.
        self.assertEqual(border.crossings(self.store)[cid]["willed_by"], "twc")
        self.assertEqual(border.system_attributed(self.store), [])

    def test_NO_peer_minted_token_an_unestablished_entity_is_refused(self):
        """RW-PEER-TRUSTED / the API-gateway trap (design/51 §9): identity is recorded establishment,
        never a peer-minted token. A submitter the record never established is refused (CAP-IS-LAW /
        require_prior), however it names itself."""
        with self.assertRaises(OpError) as cm:
            border.submit(self.gate, "twc-imposter-with-a-bearer-token", {"pack": self.pack})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")

    def test_RW_TWC_BUILT_zero_TWC_specific_symbols_in_src(self):
        """RW-TWC-BUILT (D08.41): nothing TWC-specific is built in src/ — the record is gov-os's, TWC
        is a submitter, nothing to wrap. A census over src/*.py must find ZERO occurrences of 'twc'
        (case-insensitive). Able to fail: it counts, and any wrapper would be named."""
        offenders = []
        src = os.path.join(REPO, "src")
        for root, dirs, names in os.walk(src):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in names:
                if name.endswith(".py"):
                    with open(os.path.join(root, name), encoding="utf-8") as fh:
                        if "twc" in fh.read().lower():
                            offenders.append(os.path.relpath(os.path.join(root, name), REPO))
        self.assertEqual(offenders, [], "a TWC-specific symbol was built in src/ (RW-TWC-BUILT)")

    def test_RW_PEER_TRUSTED_a_pack_row_never_becomes_a_govos_decision(self):
        """RW-PEER-TRUSTED (N4): the pack's rows land as INPUT, never as a gov-os DECISION. After the
        crossing, NO pwc ruleId has been founded as a gov-os rule/op — the pack is data inside a
        submit draft, and the census confirms it was never trusted as gov-os truth."""
        self.a_submit()
        # the pack carries real pwc ruleIds; none of them appears as a founded gov-os op or rule.
        founded_ops = {(e.get("payload") or {}).get("name") for e in self.store.by_action("CREATE-OP")}
        founded_rules = {e.get("object") for e in self.store.by_action("CREATE-RULE")}
        pack_ids = {r["row_id"] for r in self.pack["rows"] if r["row_id"]}
        self.assertEqual(pack_ids & (founded_ops | founded_rules), set(),
                         "a peer pack row was admitted as a gov-os decision (RW-PEER-TRUSTED)")
        # the only crossing-shaped act is the BORDER-SUBMIT draft; the pack content is inside it.
        self.assertEqual(len(list(self.store.by_action("BORDER-SUBMIT"))), 1)


# =============================================================================================
# A2 — T-ROUNDTRIP-PACK-TO-VIEW: pack hash -> content_id -> serviced view -> human edition
# =============================================================================================

class TestRoundtripPackToView(_World):
    def test_the_content_hash_recomputes_equal_at_every_hop(self):
        ph = pack_hash(self.pack)

        # HOP 1 — pack -> the crossing's content hash. content_id is DETERMINED by the submit's bytes
        # (which carry the pack); the store's recomputation equals the id computed from the record
        # (border.py:92, the round-trip property).
        sub = self.a_submit()
        cid = border.content_id(sub)
        self.assertIn(cid, border.submits(self.store))                    # store recomputes the same id
        core = {"action": sub["action"], "object": sub["object"],
                "target": sub.get("target"), "payload": sub.get("payload") or {}}
        self.assertEqual(cid, canonical.canonical_hash(canonical.strip_derivation(core)))

        # HOP 2 — the serviced view (EP-50). A mandated MASTER view is serviced over the current head,
        # which INCLUDES the submit; the view's servicing is a record (VIEW-SERVICE). Reading the
        # record AS-OF the serviced head still yields the SAME crossing content hash.
        self.gate.execute("CREATE-VIEW", "owner",
                          {"name": "twc-crossings", "bind": "actors", "refresh": "hourly"})
        head = len(self.store.all())
        svc = self.gate.execute("VIEW-SERVICE", "worker",
                                {"view_name": "twc-crossings", "head_seq": head})
        self.assertEqual((svc.get("payload") or {}).get("head_seq"), head)
        self.assertNotIn("twc-crossings", {t["name"] for t in self.views.paper_tigers()})  # serviced
        self.assertIn(cid, border.submits(self.store, as_of=head))        # the view's world holds the crossing

        # HOP 3 — the human edition (tools/release/edition.py). The edition's `source` IS the crossing
        # content hash, carried into the anchored edition; recompute equal.
        engine = {"founding_version": _founding_version(), "as_of_head": head}
        ed = edition.render_edition(self.pack, source=cid, engine=engine)
        self.assertEqual(ed["stamp"]["source"], cid)                      # the content hash at the edition hop
        self.assertTrue(edition.verify_edition(ed, self.pack, source=cid, engine=engine))
        # every sentence is ANCHORED to its row id (nothing floats free of the record).
        self.assertEqual(len(ed["sentences"]), len(self.pack["rows"]))
        self.assertTrue(all(s["anchor"] for s in ed["sentences"]))

        # the crossing content hash is ONE value across all three hops; the pack hash determined it.
        self.assertEqual(cid, border.content_id(border.submits(self.store)[cid]))
        self.assertTrue(ph)                                              # the pack has a stable data identity


# =============================================================================================
# A3 — T-DRIFT-BOTH-WAYS: a changed pack byte moves the hash; a changed shown byte fails the seal
# =============================================================================================

class TestDriftBothWays(_World):
    def test_a_changed_pack_byte_moves_the_content_hash_forward(self):
        sub = self.a_submit()
        cid = border.content_id(sub)
        # a changed byte of the PACK -> a different submit content -> a different crossing id.
        drifted = json.loads(json.dumps(self.pack))
        drifted["rows"][0]["text"] = drifted["rows"][0]["text"] + "."     # one appended byte
        core_drift = {"action": "BORDER-SUBMIT", "object": sub["object"], "target": sub.get("target"),
                      "payload": {"entity": "twc", "draft": {"pack": drifted}}}
        cid_drift = canonical.canonical_hash(canonical.strip_derivation(core_drift))
        self.assertNotEqual(cid, cid_drift, "a changed pack byte did not move the content hash")

    def test_a_changed_shown_byte_fails_the_seal_backward_real_or_refused(self):
        """The BORDER-REPLY seal binds exactly what was SHOWN. A changed byte of the shown content
        fails it (backward). Real-or-refused (N10): with the vetted library ABSENT (the baseline) the
        seal path REFUSES rather than fakes — a blind seal that passes a changed byte cannot exist
        because no seal is produced at all; with the library PRESENT the altered shown FAILS verify."""
        sub = self.a_submit()
        cid = border.content_id(sub)
        signer = SigningKeyStore()
        custody = signer.seal(SYSTEM_SEED)
        # what was shown to the entity: a digest of the human edition of its own pack.
        engine = {"founding_version": _founding_version(), "as_of_head": len(self.store.all())}
        ed = edition.render_edition(self.pack, source=cid, engine=engine)
        shown = {"edition_digest": ed["edition_digest"]}

        if not crypto.real_available():
            with self.assertRaises(crypto.LibraryAbsent):
                border.seal_reply(signer, custody, cid, shown)
            return
        seal = border.seal_reply(signer, custody, cid, shown)
        public = crypto.public_from_seed(SYSTEM_SEED)
        self.assertTrue(border.verify_seal(public, seal, cid, shown))      # over exactly what was shown
        altered = {"edition_digest": ed["edition_digest"][:-1] + ("0" if ed["edition_digest"][-1] != "0" else "1")}
        self.assertFalse(border.verify_seal(public, seal, cid, altered))   # a changed shown byte fails


# =============================================================================================
# A4 — T-CHAIN-HASH-EXCLUDES-RECORD-TIME (D08.40 driven, of the CONTENT hash)
# =============================================================================================

class TestChainHashExcludesRecordTime(_World):
    def test_the_same_pack_at_two_record_times_yields_one_content_hash(self):
        """D08.40: content_id hashes action/object/target/payload ONLY; record_time is minted at
        append AFTER submit and is NOT in it. The SAME pack submitted in two independently-booted
        bodies (two different record_times) yields the SAME content hash — the round trip reproduces
        from the pack alone."""
        sub1 = self.a_submit()
        # a SECOND, independent body: its own store, its own append clock.
        d2 = tempfile.mkdtemp(prefix="ep51-b2-")
        store2, gate2, _v, _b, _s = build_full_kernel(
            os.path.join(d2, "record.jsonl"), os.path.join(d2, "blobs"), os.path.join(d2, "vault"))
        gate2.execute("CREATE-ACCOUNT", "owner", {"account_id": "twc", "actor_class": "agentic"})
        sub2 = border.submit(gate2, "twc", {"pack": self.pack})

        self.assertIsNotNone(sub1.get("record_time"))                     # record_time IS minted
        self.assertIsNotNone(sub2.get("record_time"))
        self.assertEqual(border.content_id(sub1), border.content_id(sub2),
                         "the content hash depended on record_time (D08.40 broken)")

    def test_mutating_record_time_leaves_content_id_unchanged_but_moves_the_chain_hash(self):
        """The two-hash rule (D08.40), driven on ONE record: mutating record_time does NOT move
        content_id (the round-trip anchor), but DOES move the whole-record canonical hash (the
        prev_hash chain-integrity hash INCLUDES record_time — it seals WHEN a record landed)."""
        sub = self.a_submit()
        before_content = border.content_id(sub)
        before_chain = canonical.canonical_hash(sub)
        mutated = dict(sub)
        mutated["record_time"] = "2099-01-01T00:00:00Z"                   # a different landing time
        self.assertEqual(border.content_id(mutated), before_content)      # content hash: UNCHANGED
        self.assertNotEqual(canonical.canonical_hash(mutated), before_chain)  # chain hash: MOVED


# =============================================================================================
# A5 — T-UNSTRUCTURED-COUNT-NAMED: the count is published WITH ITS WORLD, never bare
# =============================================================================================

class TestUnstructuredCountNamed(_World):
    def test_the_count_is_self_consistent_and_derived_from_the_real_constitution(self):
        pack = self.pack
        counted = sum(1 for r in pack["rows"] if r["class"] == "unstructured")
        self.assertEqual(pack["unstructured"]["count"], counted)          # the pack agrees with itself
        self.assertGreater(pack["unstructured"]["count"], 0)              # a real gap exists
        self.assertLess(pack["unstructured"]["count"], pack["unstructured"]["of"])
        # deterministic: a second derive yields the identical count (same source bytes -> same pack).
        self.assertEqual(derive_twc_pack()["unstructured"]["count"], pack["unstructured"]["count"])

    def test_RW_BARE_COUNT_a_count_without_its_world_is_refused(self):
        """RW-BARE-COUNT (§4): the count is a fact only WITH its world (pack version + source + as-of
        head + founding version). A published count carrying its full world passes `world_named`; a
        BARE count (world stripped) is refused — the check that can fail."""
        head = len(self.store.all())
        published = publish_count(self.pack, as_of_head=head, founding_version=_founding_version())
        self.assertEqual(published["unstructured_rows"], self.pack["unstructured"]["count"])
        self.assertTrue(world_named(published))                          # full world -> a fact
        self.assertFalse(world_named({"unstructured_rows": published["unstructured_rows"]}))  # bare -> refused
        # the world names the pack VERSION and the SOURCE it measured (the real constitution).
        self.assertEqual(published["world"]["version"], TWC_VERSION)
        self.assertEqual(published["world"]["derived_from"]["law_rows"], 233)


# =============================================================================================
# A6 — T-PLANTED-DRIFT-CAUGHT: a planted drift is caught (the --selftest planted-control precedent)
# =============================================================================================

class TestPlantedDriftCaught(unittest.TestCase):
    def test_a_planted_one_byte_drift_in_the_edition_is_named(self):
        """A6 (the check_clean_from_cut --selftest precedent): plant a one-byte drift in a SHOWN
        edition and prove the drift check NAMES it, while the clean edition passes. The plant is the
        strong case — a tampered sentence whose stored digest was RECOMPUTED to match its own tampered
        content (a forger who rehashes); the check catches it anyway because it re-renders the TRUE
        pack and the sentences no longer match. A control that cannot red is the defect."""
        pack = {"pack": "T", "version": "0.0.0",
                "rows": [{"row_id": "R1", "text": "a rule", "enforced_by": "structured"}]}
        source = "sha256:" + "a" * 64
        engine = {"founding_version": "x", "as_of_head": 1}
        ed = edition.render_edition(pack, source=source, engine=engine)
        self.assertTrue(edition.verify_edition(ed, pack, source=source, engine=engine))   # clean passes
        tampered_sentences = [dict(ed["sentences"][0], text="a rulE")]                     # one byte
        forged_digest = hashlib.sha256(json.dumps(
            {"source": source, "engine": engine, "pack": pack["pack"], "version": pack["version"],
             "sentences": tampered_sentences}, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        drifted = dict(ed, sentences=tampered_sentences, edition_digest=forged_digest)
        self.assertFalse(edition.verify_edition(drifted, pack, source=source, engine=engine))  # caught

    def test_the_edition_selftest_control_passes(self):
        """The renderer's own planted-drift control (edition.py --selftest) returns 0 — the control
        both fires on a plant and clears a clean edition."""
        self.assertEqual(edition.selftest(), 0)


# =============================================================================================
# A7 — T-NO-KIND-MINTED: zero new check kinds; candidate kinds RAISED BY NAME, never minted
# =============================================================================================

class TestNoKindMinted(unittest.TestCase):
    def test_OP_CHECKS_is_unchanged_and_the_founding_pack_is_byte_identical(self):
        """A7 / RW-KIND-MINTED (stop-e): this tracer mints NO check kind and moves NO founding. The
        assertion is absolute equality against the LIVE base on purpose — an era-floor (>=) would
        stop catching a mint, which is the one thing this row exists to catch — so it is re-pinned
        by the last founding mover, never widened.

        [BASE RE-PINNED — EP-49C, 2026-09-08, mgr under the :3255 by-name count-pin ownership. EP-49C's
        AMEND-OP added two CODE-BORN check kinds (`live_present`, `fold_threshold`) and bumped the
        genesis pack, moving THIS tracer's base after its EP-50 dispatch base (b619d465, OP_CHECKS 17).
        Re-pinned to the base EP-51 now sits on, both members read from a command: OP_CHECKS 19,
        pack 6181419278 (PYTHONPATH=src `len(OP_CHECKS)`; sha256 of founding-pack.json). EP-51 itself
        still moves neither — the claim is unchanged, only the base it is measured against moved.]

        [BASE RE-PINNED AGAIN — EP-52, 2026-09-08, at the founding mover's hand (this row is re-pinned
        by the last founding mover, per its own rule above). EP-52 (FIREWALL-IN-THE-RECORD, C5 P7) is a
        founding MINT — NET-LAW-FILTER + FILTER-DECISION, 1.45.0 -> 1.46.0 — so it moves THIS tracer's
        base from 6181419278 to 8d0c6a9b. OP_CHECKS is UNCHANGED at 19 (EP-52 minted an op, NOT a check
        kind). EP-51 itself still moves neither op-check-vocabulary nor founding; only the base it is
        measured against moved. Read from a command: sha256 of the live founding-pack.json.]

        [BASE RE-PINNED AGAIN — EP-48G, 2026-09-08, applied at MGR's hand under the :3255 by-name
        hash-pin ownership (the EP-48G builder RAISED it as outside its named fence, correct). EP-48G
        (SOCKET-GRANTS guest-real) is a conditional founding mover — it drove the NET-LAW-GRANT->errno
        row ABSENT and added it (a rule-errno amendment row), 1.46.0 -> 1.47.0 — so it moves THIS
        tracer's base from 8d0c6a9b to 132cd7ff. OP_CHECKS UNCHANGED at 19 (a data row, NOT a check
        kind or an op — op-population also unchanged at 93). EP-51 itself still moves neither; only the
        base it is measured against moved. Read from a command: sha256 of the live founding-pack.json.]

        [BASE RE-PINNED AGAIN — EP-MAINT-OUTSIDE-2, 2026-09-09, at the founding mover's hand (this row
        is re-pinned by the last founding mover, per its own rule above; the §A57 live-hash-pin sweep,
        the EP-49D/EP-50 lesson). The move is a DATA-BORN MINOR 1.47.0 -> 1.48.0: twelve ops gain a
        `param_kinds` META declaration (quantity | text | bytes | measurement — the door guard's data
        half that refuses a malformed quantity or a raw-bytes text value before the record write). It
        moves THIS tracer's base to 83626499. OP_CHECKS UNCHANGED at 19 (the guard reads the
        definition's own declaration and refuses under the existing AR-2 — no check kind minted);
        op-population UNCHANGED at 93 (no op added). EP-51 itself still moves neither; only the base it
        is measured against moved. Read from a command: sha256 of the live founding-pack.json.]

        [BASE RE-PINNED AGAIN — EP-MAINT-OUTSIDE-4, 2026-09-09, at the founding mover's hand. A
        DATA-BORN MINOR 1.48.0 -> 1.49.0: SHM-GRANT gains ONE `live_present` check ROW (a LIVE MEM-GRANT
        prerequisite over MEM-GRANT/MEM-EVICT — the EP-49C kind REUSED, R10). Moves this base to
        c9b8635d. OP_CHECKS UNCHANGED at 19 (live_present reused, no new kind); op-population UNCHANGED
        at 93 (a check ROW, not an op). Read from a command: sha256 of the live founding-pack.json.]

        [BASE RE-PINNED AGAIN — EP-MAINT-OUTSIDE-3, 2026-09-09, at the founding mover's hand (this row is
        re-pinned by the last founding mover, per its own rule above). A DATA-BORN MINOR 1.49.0 -> 1.50.0:
        FILE-READ-AGGREGATE.bytes is re-kinded `bytes -> quantity` (a mis-kinded int byte-TOTAL, now
        guarded by the existing quantity door — no new kind). Moves this base to c196d430. OP_CHECKS
        UNCHANGED at 19 (the `quantity` guard already exists, EP-MAINT-OUTSIDE-2 — a re-kind mints none);
        op-population UNCHANGED at 93 (a param re-kind adds no op). Read from a command: sha256 of the
        live founding-pack.json.]"""
        self.assertEqual(len(OP_CHECKS), 19)
        pack_sha = _sha256_file(os.path.join(REPO, "src", "founding", "founding-pack.json"))
        self.assertEqual(
            pack_sha, "c196d430036c0d14e320ed1fe5d4ca098977b4b32f1af70f3b92db06e7f7b46c",
            "founding-pack.json moved — this tracer is NOT a founding move (RW-KIND-MINTED / stop-f)")

    def test_the_candidate_kinds_are_named_by_source_never_minted(self):
        """A7 / N7: the candidate check kinds a real TWC would need are RAISED BY NAME (the owner's
        one word), from TWO sources (design/42 §2.2/§2.5, and TWC's own rows D08.39). Each names its
        source; none is added to OP_CHECKS. The kinds the derived pack actually needs are a subset of
        the named candidates (the raise is grounded in the real data, not a wishlist)."""
        pack = derive_twc_pack()
        for name, spec in pack["candidate_kinds"].items():
            self.assertIn(name, CANDIDATE_KINDS)
            self.assertTrue(spec["source"], f"candidate kind {name} raised without a source")
            self.assertNotIn(name, OP_CHECKS)                            # named, NOT minted
        observed = {k for k, v in pack["unstructured"]["by_kind"].items()}
        self.assertTrue(observed <= set(CANDIDATE_KINDS), "an unnamed kind appeared in the count")
        self.assertTrue(observed, "no candidate kind was observed — the raise would be empty")


if __name__ == "__main__":
    unittest.main()
