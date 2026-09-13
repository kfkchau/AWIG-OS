# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (Merkle root, cross-attestation, mutual receipt, recovery capacity, subtree localization);
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-45 (BUILD) acceptance + red-world battery: cross-attested checkpoints under the recovery-capacity law.

design/47 §4 (the diving-buddy — two witnesses, mutual receipt, no shared write-path) + design/37 §5
(the recovery-capacity law — content × relational redundancy; Merkle-shaped cross-attest, damage
localizes). A CROSS-ATTESTED CHECKPOINT is EP-44's checkpoint made MERKLE-SHAPED: its provenance
carries a Merkle root over its tree-state, so a verification mismatch LOCALIZES to the diverging subtree
instead of reddening the whole; two checkpoints taken by INDEPENDENT folds cross-reference each other's
roots and the pairing verdict is a MUTUAL RECEIPT. Every probe here is a regression test (the campaign
method). The battery runs in DISPOSABLE test founding worlds; nothing real is checkpointed by it. The
recovery-capacity law create — HELD when this battery was built — has since LANDED in production
founding (EP-FND-CAPACITY-LAW, MINOR 1.36.0 -> 1.37.0), so A6/A7 assert the live state.

  A1  TestMerkleRootCarried       provenance carries a Merkle root over the tree-state (leaf =
                                  canonical_hash of a file node; a directory = canonical_hash over [the
                                  dir's OWN metadata entry, its children's sorted (name,hash) pairs] under
                                  scheme 2 — B11, EP-MAINT-OUTSIDE-2; children-only survives as scheme 1,
                                  keyed by the scheme a checkpoint records; root = the top). Persisted and
                                  read back, byte-identical (rides EP-44 A1).
  A2  TestDamageLocalizes         a recomputed tree differing in ONE subtree localizes to that subtree;
                                  an unchanged sibling's hash matches and is reported clean (RW1: a bare
                                  "tree mismatch" that names nothing is EP-44's verify, not this one).
  A3  TestMutualReceipt           two checkpoints by INDEPENDENT folds, each carrying the OTHER's root;
                                  the pairing holds only when BOTH confirm (RW2: a one-sided pairing).
  A4  TestNoSharedWritePath       the two roots must arise from INDEPENDENT folds; a pairing tracing to
                                  ONE writer is refused (RW3). COMPUTATION-blindness, one machine.
  A5  TestVerifiableWithoutEngine the root and the pairing receipt verify against the record + blobs
                                  ALONE — no gate/views/engine, reusing the reader, never a second fold
                                  (RW4, the air rider :2963).
  A6  TestCapacityLawCreate       the recovery-capacity law create is admitted in a TEST founding world;
                                  production founding-pack.json now CARRIES the law (LANDED,
                                  EP-FND-CAPACITY-LAW) (RW6: a truncating recover-capacity wording).
  A7  TestCoverageStated          a per-subsystem coverage declaration (population + basis); a bare
                                  "recoverable" is REFUSED by the founding door (RW5, §A51).
  TestRedWorlds                   RW1-RW6 driven THROUGH the instrument, named (§A42).

Honest cap (design/47 §4, the :3044 precision): A4 proves COMPUTATION-blindness within ONE machine
(the design/28 §7 shape) — the two folds are independent computations, neither reading the other. The
two-PHYSICAL-bodies half of the diving buddy (one witness in the chip's own memory, one on disk, no
shared write-path across devices) is C7's and is NOT claimed here.
"""

import inspect
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                      # noqa: E402  — the compose layer (attests live at boot)
from kernel.canonical import canonical_hash                       # noqa: E402  — the estate's one hash form
from kernel.attestation import attest_boot, register_attestation  # noqa: E402  — the owner-gated attestation op, live in test
from bridge import checkpoint                                     # noqa: E402  — EP-44's artifact, made Merkle-shaped here
from bridge import merkle                                         # noqa: E402  — the module under test (the Merkle fold)
from bridge import replay_snapshot                                # noqa: E402  — the reader the Merkle folds over (REUSED)
from founding import install as founding_install                  # noqa: E402  — the founding door (whole-pack pre-flight)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")


# ---- test-world record-plane helpers (the EP-41B/EP-44 stand-in for the files ops) ---------------

def _mkdir(store, path):
    store._append({"actor": "owner", "action": "FILE-MKDIR", "object": path,
                   "rule_cited": "ROOT-NEG-5", "payload": {"path": path}})


def _write_file(store, blobs, path, content):
    h = blobs.put(content)
    store._append({"actor": "owner", "action": "FILE-CREATE", "object": path,
                   "rule_cited": "ROOT-NEG-5",
                   "payload": {"path": path, "node_type": "file", "perm": "644"}})
    store._append({"actor": "owner", "action": "FILE-WRITE", "object": path,
                   "rule_cited": "ROOT-NEG-5",
                   "payload": {"path": path, "content_hash": h, "length": len(content)}})
    return h


def _attesting_hier_world(dir_):
    """A disposable attesting world with a NESTED tree (two directories, three files), so the Merkle
    has a hierarchy to localize within. The full kernel is composed (attestation live, so a checkpoint
    can be taken), exactly as EP-44's world — production compose holds the attestation op inert until
    the owner's word; the test registers it, the test-world stand-in."""
    path = os.path.join(dir_, "record.jsonl")
    blob_dir = os.path.join(dir_, "blobs")
    store, gate, views, blobs, _subs = build_full_kernel(path, blob_dir)
    register_attestation(gate)
    attest_boot(store, gate)
    _mkdir(store, "/dir1")
    _mkdir(store, "/dir2")
    _write_file(store, blobs, "/dir1/a", b"the alpha file's bytes")
    _write_file(store, blobs, "/dir1/b", b"the beta file's bytes")
    _write_file(store, blobs, "/dir2/c", b"the gamma file's bytes")
    return store, gate, views, blobs, path, blob_dir


# ---- the recovery-capacity law record, built in the test (the LANDED founding create's stand-in) --
#
# The create LANDED at EP-FND-CAPACITY-LAW (MINOR 1.36.0 -> 1.37.0): production founding-pack.json now
# carries RECOVERY-CAPACITY-1 in the production convention shape (PC_RUNTIME / non-root). This stand-in
# keeps the TEST-WORLD envelope (SYSTEM / root:True) so the founding door's root-scope referential
# check engages for the RW near-misses (a ghost scope is refused) — but its TEXT is READ from the
# production row, so the law has ONE wording estate-wide and cannot become a stored copy.

def _prod_capacity_text(rule_id="RECOVERY-CAPACITY-1"):
    """The ONE wording of the recovery-capacity law, READ from the production founding pack's own
    RECOVERY-CAPACITY-1 row — never a second literal (:3093, the archi precision: two wordings of one
    law is the stored-copy defect). A pack with no such row is a world where this test does not apply,
    and the miss is loud (AssertionError) rather than silently masked by a fallback string."""
    for r in founding_install.records(founding_install.load_pack(PACK_PATH)):
        pl = r.get("payload") or {}
        if r.get("action") == "CREATE-RULE" and pl.get("rule_id") == rule_id:
            return pl["text"]
    raise AssertionError("production founding carries no %s row — the capacity law create did not land"
                         % rule_id)


def _capacity_law(scope="space:root", coverage="default", discipline="append-only",
                  permits_truncation=False, rule_id="RECOVERY-CAPACITY-1", text=None):
    """A recovery-capacity law CREATE-RULE — the TEST-WORLD stand-in (SYSTEM / root:True) for the
    production convention-shape row (PC_RUNTIME / non-root) that LANDED at EP-FND-CAPACITY-LAW. Its
    ADMISSION rides the EXISTING founding door (scope names a founded space); its WELL-FORMEDNESS is
    §A51 population + basis and :3024 never-truncate, declared in the payload. Its TEXT defaults to the
    production wording READ from the pack (`_prod_capacity_text`), so the stand-in and production share
    ONE string (:3093); a caller overrides `text` only to exercise a wording red world."""
    if coverage == "default":
        coverage = [
            {"subsystem": "files", "content": "content-addressed blobs (replicas / firmware copy)",
             "relational": "the hash chain + Merkle-shaped localization"},
            {"subsystem": "memory", "content": "the full-fidelity projection pinned at a checkpoint",
             "relational": "the record's derivation relations (fold from LAW+DECISIONS+INPUTS)"},
        ]
    if text is None:
        text = _prod_capacity_text(rule_id)
    return {
        "actor": "SYSTEM", "action": "CREATE-RULE", "object": rule_id, "rule_cited": "BOOT-INT",
        "payload": {
            "kind": "rule", "rule_id": rule_id, "root": True, "polarity": "+", "scope": scope,
            "text": text,
            "coverage": coverage,
            "recover_discipline": discipline,
            "permits_truncation": permits_truncation,
        },
    }


def _prod_records():
    """The production founding records (which found the real spaces) — read-only, never mutated."""
    return list(founding_install.records(founding_install.load_pack(PACK_PATH)))


# ==================================================================================================
# A1 — THE MERKLE ROOT PINNED AND CARRIED
# ==================================================================================================

class TestMerkleRootCarried(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep45-a1-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_hier_world(self.dir)
        self.cp = checkpoint.cross_attest(self.store, self.path, self.blob_dir,
                                          witness="fold-chip", root="/", pack_path=PACK_PATH)

    def test_a1_provenance_carries_the_merkle_root_over_the_tree_state(self):
        mr = self.cp["provenance"]["merkle_root"]
        # the estate's one hash form
        self.assertTrue(mr.startswith("sha256:"), mr)
        # it IS the Merkle root over the checkpoint's tree-state (one fold of snapshot's output)
        self.assertEqual(mr, merkle.merkle_root(self.cp["tree"]))
        # EP-44's triplet is INTACT (this is additive: create is untouched, cross_attest ADDS the root)
        for member in checkpoint.TRIPLET:
            self.assertIn(member, self.cp["provenance"])
        self.assertTrue(checkpoint.is_valid(self.cp))

    def test_a1_the_root_is_built_leaf_dir_top(self):
        # leaf = canonical_hash of a file node; a directory = canonical_hash over [the dir's OWN
        # snapshot entry, its children's sorted (name, hash) pairs]; root = the top (a synthetic dir
        # with no own entry, so its node folds as None). Reproduce the spec by hand over the tree-state.
        # RE-CUT BY NAME for B11 (EP-MAINT-OUTSIDE-2): the settled EP-45 merkle spec now seals a
        # directory's own metadata beside its children — a new checkpoint folds under scheme 2 (the
        # dir-metadata scheme). The old children-only spec survives as scheme 1, keyed by the scheme a
        # checkpoint records; test_a5_an_old_scheme_root_verifies below drives the backward-safe half.
        tree = self.cp["tree"]
        scheme = self.cp["provenance"]["merkle_scheme"]                # a new checkpoint records scheme 2
        self.assertEqual(scheme, merkle.SCHEME_DIR_METADATA)
        node_tree = merkle.merkle_tree(tree, scheme)
        leaf_a = canonical_hash(tree["dir1/a"])
        self.assertEqual(node_tree["children"]["dir1"]["children"]["a"]["hash"], leaf_a)
        dir1_pairs = [[n, node_tree["children"]["dir1"]["children"][n]["hash"]]
                      for n in sorted(node_tree["children"]["dir1"]["children"])]
        # scheme 2: a directory's hash folds its OWN metadata entry (tree["dir1"]) BESIDE the children
        self.assertEqual(node_tree["children"]["dir1"]["hash"],
                         canonical_hash([tree["dir1"], dir1_pairs]))
        top_pairs = [[n, node_tree["children"][n]["hash"]] for n in sorted(node_tree["children"])]
        # the synthetic root has no own snapshot entry, so its node folds as None
        self.assertEqual(node_tree["hash"], canonical_hash([None, top_pairs]))

    def test_a1_persist_read_back_is_byte_identical(self):
        f = os.path.join(self.dir, "cp.json")
        checkpoint.write(self.cp, f)
        with open(f, "rb") as fh:
            bytes1 = fh.read()
        back = checkpoint.read(f)
        self.assertEqual(back["provenance"]["merkle_root"], self.cp["provenance"]["merkle_root"])
        # re-writing the read-back reproduces identical bytes (rides EP-44 A1)
        g = os.path.join(self.dir, "cp2.json")
        checkpoint.write(back, g)
        with open(g, "rb") as fh:
            self.assertEqual(fh.read(), bytes1)

    def test_a1_verify_confirms_the_root_on_an_unchanged_world(self):
        verdict = checkpoint.verify(self.cp, self.path, self.blob_dir, PACK_PATH)
        self.assertTrue(verdict["ok"], verdict)
        self.assertTrue(verdict["merkle_root"])                   # the cross-attested root recomputes
        self.assertNotIn("diverging", verdict)                    # nothing diverges on an unchanged world


# ==================================================================================================
# A2 — DAMAGE LOCALIZES
# ==================================================================================================

class TestDamageLocalizes(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep45-a2-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_hier_world(self.dir)
        self.cp = checkpoint.cross_attest(self.store, self.path, self.blob_dir,
                                          witness="fold-chip", root="/", pack_path=PACK_PATH)
        # a recomputed tree differing in ONE subtree: rewrite /dir1/a, leave dir2 alone
        _write_file(self.store, self.blobs, "/dir1/a", b"the alpha file's bytes - CHANGED")
        self.recomputed = replay_snapshot.snapshot(self.path, self.blob_dir, root="/")

    def test_a2_localizes_to_the_diverging_leaf_not_a_bare_mismatch(self):
        diverging = merkle.localize(self.cp["tree"], self.recomputed)
        self.assertEqual(diverging, ["dir1/a"])                   # NAMES the subtree — not "tree mismatch"

    def test_a2_an_unchanged_sibling_subtree_matches_and_is_clean(self):
        pinned = merkle.merkle_tree(self.cp["tree"])
        recomputed = merkle.merkle_tree(self.recomputed)
        # dir2 changed nothing: its subtree hash is byte-identical (relations adjudicate — clean)
        self.assertEqual(pinned["children"]["dir2"]["hash"], recomputed["children"]["dir2"]["hash"])
        # dir1 DID change: its subtree hash differs (the divergence localizes UP the spine to dir1)
        self.assertNotEqual(pinned["children"]["dir1"]["hash"], recomputed["children"]["dir1"]["hash"])
        # and within dir1, only /a moved; /b is clean
        self.assertEqual(pinned["children"]["dir1"]["children"]["b"]["hash"],
                         recomputed["children"]["dir1"]["children"]["b"]["hash"])

    def test_a2_verify_names_the_diverging_subtree(self):
        verdict = checkpoint.verify(self.cp, self.path, self.blob_dir, PACK_PATH)
        self.assertFalse(verdict["merkle_root"])                  # the tree moved
        self.assertEqual(verdict["diverging"], ["dir1/a"])        # verify NAMES where, not a bare bool

    def test_a2_an_added_and_a_removed_file_localize(self):
        # a file that appeared under dir2 and one that never existed both localize to their own paths
        _write_file(self.store, self.blobs, "/dir2/d", b"a new file under dir2")
        recomputed = replay_snapshot.snapshot(self.path, self.blob_dir, root="/")
        diverging = merkle.localize(self.cp["tree"], recomputed)
        self.assertIn("dir1/a", diverging)
        self.assertIn("dir2/d", diverging)                        # the appeared file localizes
        self.assertNotIn("dir1/b", diverging)                     # untouched — clean


# ==================================================================================================
# A3 — THE MUTUAL RECEIPT (the diving-buddy pairing)
# ==================================================================================================

class TestMutualReceipt(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep45-a3-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_hier_world(self.dir)
        self.root_val = merkle.merkle_root(replay_snapshot.snapshot(self.path, self.blob_dir, root="/"))
        # two checkpoints by two INDEPENDENT folds, each carrying the OTHER's root
        self.cp_a = checkpoint.cross_attest(self.store, self.path, self.blob_dir,
                                            witness="fold-chip", root="/", peer_root=self.root_val)
        self.cp_b = checkpoint.cross_attest(self.store, self.path, self.blob_dir,
                                            witness="fold-disk", root="/", peer_root=self.root_val)

    def test_a3_the_pairing_holds_when_both_confirm(self):
        verdict = checkpoint.pairing_verdict(self.cp_a, self.path, self.blob_dir,
                                             self.cp_b, self.path, self.blob_dir)
        self.assertTrue(verdict["ok"], verdict)
        self.assertTrue(verdict["a_confirms_b"] and verdict["b_confirms_a"])
        self.assertTrue(verdict["independent"])

    def test_a3_rw2_a_one_sided_pairing_fails(self):
        # B carries the WRONG root for A (it confirms nothing): a one-sided receipt is NOT a mutual one.
        cp_b_bad = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-disk",
                                           root="/", peer_root="sha256:" + "0" * 64)
        verdict = checkpoint.pairing_verdict(self.cp_a, self.path, self.blob_dir,
                                             cp_b_bad, self.path, self.blob_dir)
        self.assertTrue(verdict["a_confirms_b"])                  # A still confirms B
        self.assertFalse(verdict["b_confirms_a"])                 # B does NOT confirm A
        self.assertFalse(verdict["ok"])                           # a one-sided receipt fails

    def test_a3_an_absent_peer_root_fails(self):
        # neither alone is authority: a checkpoint carrying no peer root confirms nothing.
        cp_b_none = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-disk",
                                            root="/")            # no peer_root
        verdict = checkpoint.pairing_verdict(self.cp_a, self.path, self.blob_dir,
                                             cp_b_none, self.path, self.blob_dir)
        self.assertFalse(verdict["b_confirms_a"])
        self.assertFalse(verdict["ok"])


# ==================================================================================================
# A4 — NO SHARED WRITE-PATH (the common-mode red)
# ==================================================================================================

class TestNoSharedWritePath(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep45-a4-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_hier_world(self.dir)
        self.root_val = merkle.merkle_root(replay_snapshot.snapshot(self.path, self.blob_dir, root="/"))

    def test_a4_independent_folds_pass_one_fold_is_refused(self):
        # TWO independent folds (distinct witnesses) — the pairing's independence gate holds.
        cp_a = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-chip",
                                       root="/", peer_root=self.root_val)
        cp_b = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-disk",
                                       root="/", peer_root=self.root_val)
        self.assertTrue(checkpoint.pairing_verdict(cp_a, self.path, self.blob_dir,
                                                   cp_b, self.path, self.blob_dir)["independent"])
        # ONE writer / one fold — both checkpoints trace to a single witness: the pair is DEFEATED,
        # even though both roots recompute and both "confirm". Common-mode failure (design/47 §4).
        solo_a = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-solo",
                                         root="/", peer_root=self.root_val)
        solo_b = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-solo",
                                         root="/", peer_root=self.root_val)
        verdict = checkpoint.pairing_verdict(solo_a, self.path, self.blob_dir,
                                             solo_b, self.path, self.blob_dir)
        self.assertFalse(verdict["independent"])                  # one hand wrote both
        self.assertFalse(verdict["ok"])                           # refused despite matching roots

    def test_a4_the_blindness_is_of_computation_within_one_machine(self):
        # THE STATED CAP (design/47 §4; the design/28 §7 EP-09 shape). Independence here is blindness
        # of COMPUTATION — two folds, distinct witnesses — NOT two physical bodies with no shared
        # write-path across devices (that is C7's diving buddy). The pairing refuses a declared single
        # fold; it does not, and does not claim to, prove physical separation. This test pins the cap:
        # the ONLY discriminator between the good pair and the shared-writer pair is the witness.
        cp_a = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="w1",
                                       root="/", peer_root=self.root_val)
        cp_b = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="w2",
                                       root="/", peer_root=self.root_val)
        # same underlying record/blobs (one machine); the pair holds on computation-independence alone
        self.assertEqual(cp_a["provenance"]["merkle_root"], cp_b["provenance"]["merkle_root"])
        self.assertTrue(checkpoint.pairing_verdict(cp_a, self.path, self.blob_dir,
                                                   cp_b, self.path, self.blob_dir)["ok"])


# ==================================================================================================
# A5 — VERIFIABLE WITHOUT THE ENGINE (the air rider)
# ==================================================================================================

class TestVerifiableWithoutEngine(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep45-a5-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_hier_world(self.dir)
        self.root_val = merkle.merkle_root(replay_snapshot.snapshot(self.path, self.blob_dir, root="/"))
        self.cp_a = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-chip",
                                            root="/", peer_root=self.root_val)
        self.cp_b = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-disk",
                                            root="/", peer_root=self.root_val)

    def test_a5_pairing_verifies_from_files_alone(self):
        fa = os.path.join(self.dir, "a.json")
        fb = os.path.join(self.dir, "b.json")
        checkpoint.write(self.cp_a, fa)
        checkpoint.write(self.cp_b, fb)
        # drop EVERY engine handle: only the on-disk checkpoints and the record/blobs remain
        del self.store, self.gate, self.views, self.blobs
        cp_a, cp_b = checkpoint.read(fa), checkpoint.read(fb)
        verdict = checkpoint.pairing_verdict(cp_a, self.path, self.blob_dir,
                                             cp_b, self.path, self.blob_dir)
        self.assertTrue(verdict["ok"], verdict)

    def test_a5_rw4_the_pairing_holds_no_engine_handle(self):
        # pairing_verdict takes CHECKPOINTS and FILE PATHS only — no store, no gate, no views.
        params = list(inspect.signature(checkpoint.pairing_verdict).parameters)
        self.assertEqual(params, ["cp_a", "record_path_a", "blob_dir_a",
                                  "cp_b", "record_path_b", "blob_dir_b"])

    def test_a5_rw4_reuses_the_reader_and_folds_no_record_by_hand(self):
        # the checkpoint module imports no gate/views/compose (the running engine): a static guard.
        with open(os.path.join(REPO, "src", "bridge", "checkpoint.py"), encoding="utf-8") as fh:
            csrc = fh.read()
        import_lines = [ln for ln in csrc.splitlines()
                        if ln.startswith("import ") or ln.startswith("from ")]
        for ln in import_lines:
            for forbidden in ("gate", "views", "compose"):
                self.assertNotIn(forbidden, ln, ln)
        # the Merkle module implements NO second reader and NO second serializer: it imports ONLY the
        # canonical floor (never replay_snapshot, never a store, never hashlib/json) — one fold, reused.
        with open(os.path.join(REPO, "src", "bridge", "merkle.py"), encoding="utf-8") as fh:
            msrc = fh.read()
        m_imports = [ln for ln in msrc.splitlines()
                     if ln.startswith("import ") or ln.startswith("from ")]
        joined = "\n".join(m_imports)
        for forbidden in ("gate", "views", "compose", "store", "replay_snapshot", "hashlib", "import json"):
            self.assertNotIn(forbidden, joined, forbidden)
        self.assertIn("canonical_hash", joined)                   # it DOES reuse the one hash form


# ==================================================================================================
# A6 — THE RECOVERY-CAPACITY LAW ADMITTED (LANDED in production, EP-FND-CAPACITY-LAW)
# ==================================================================================================

class TestCapacityLawCreate(unittest.TestCase):

    def test_a6_the_founding_door_admits_a_well_formed_law_in_a_test_world(self):
        law = _capacity_law()
        # the founding door (the installer's whole-pack pre-flight) admits it — scope names a founded
        # space; no new founding check kind is minted (stop e), it rides the existing referential check.
        founding_install._validate(_prod_records() + [law])       # does not raise -> admitted
        # the wording carries the law: capacity = content × relational; relations adjudicate, anchors
        # supply; neither alone recovers; a recover never truncates (the :3024 precision as law).
        text = law["payload"]["text"]
        self.assertIn("content redundancy × relational redundancy", text)
        self.assertIn("ADJUDICATE", text)
        self.assertIn("SUPPLY", text)
        self.assertIn("neither alone recovers", text)
        self.assertIn("NEVER removes, rewrites, or shortens", text)
        self.assertTrue(checkpoint.capacity_law_wellformed(law))
        self.assertTrue(checkpoint.capacity_never_truncates(law))

    def test_a6_rw6_a_truncating_recover_capacity_wording_is_refused(self):
        # RW6 / stop (h): a capacity law WORDING that permits a recover to SHORTEN the record is the
        # forbidden delete (:2856/:3024). Two truncation-permitting shapes fail the never-truncate law.
        permits = _capacity_law(permits_truncation=True)
        self.assertFalse(checkpoint.capacity_never_truncates(permits))
        self.assertFalse(checkpoint.capacity_law_wellformed(permits))
        not_append_only = _capacity_law(discipline="rewrite-in-place")
        self.assertFalse(checkpoint.capacity_never_truncates(not_append_only))
        self.assertFalse(checkpoint.capacity_law_wellformed(not_append_only))

    def test_a6_the_production_founding_carries_the_recovery_capacity_law(self):
        # the create LANDED (EP-FND-CAPACITY-LAW, MINOR 1.36.0 -> 1.37.0): production
        # founding-pack.json now CARRIES the recovery-capacity law as a data-born row in the
        # production convention shape (PC_RUNTIME / non-root / scope space:root), so the held
        # assertions INVERT to live — RECOVERY-CAPACITY and its recover_discipline are present.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        self.assertIn("RECOVERY-CAPACITY", real)
        self.assertIn("recover_discipline", real)

    def test_a6_the_production_row_is_the_convention_shape_with_the_sealed_forever_clause(self):
        # THE WRONG-REFERENCE TRAP (:3075) GUARDED: production carries the law in the PRODUCTION
        # CONVENTION SHAPE (PC_RUNTIME / CREATE-RULE / non-root / rule_cited BOOT-INT / scope
        # space:root) — the sibling C4-law shape, NOT the test-world SYSTEM/root:true stand-in — and
        # its text carries the sealed-forever clause (:3062/:3090). A shape+clause regression guard so a
        # later edit cannot re-plant the stand-in shape or silently drop the clause.
        recs = founding_install.records(founding_install.load_pack(PACK_PATH))
        row = [r for r in recs if (r.get("payload") or {}).get("rule_id") == "RECOVERY-CAPACITY-1"]
        self.assertEqual(len(row), 1, "exactly one production RECOVERY-CAPACITY-1 row")
        r = row[0]
        self.assertEqual(r["actor"], "PC_RUNTIME")             # the convention shape, not the SYSTEM stand-in
        self.assertEqual(r["action"], "CREATE-RULE")
        self.assertEqual(r["rule_cited"], "BOOT-INT")
        self.assertNotIn("root", r["payload"])                 # non-root — a domain law, not constitutional
        self.assertEqual(r["payload"]["scope"], "space:root")
        self.assertEqual(r["payload"]["recover_discipline"], "append-only")
        self.assertFalse(r["payload"]["permits_truncation"])
        self.assertIn("sealed forever", r["payload"]["text"])  # this unit's own new clause (:3062/:3090)
        # the founding-door predicates admit the PRODUCTION row itself (not only the test-world stand-in)
        self.assertTrue(checkpoint.capacity_law_wellformed(r))
        self.assertTrue(checkpoint.capacity_never_truncates(r))

    def test_a6_rw_f_the_carries_check_can_fail_a_stripped_copy_reds_it(self):
        # §A64 — a check that cannot fail is not a check. Production carries the law; strip its id from
        # a COPY of the pack text and the carries-assertion WOULD red (the guard is real), while
        # production stays byte-untouched. The inverse of the old plant-into-copy proof.
        with open(PACK_PATH, encoding="utf-8") as fh:
            real = fh.read()
        self.assertIn("RECOVERY-CAPACITY", real)                  # production carries it (the live state)
        stripped = real.replace("RECOVERY-CAPACITY", "SOME-OTHER-RULE-ID")
        self.assertNotIn("RECOVERY-CAPACITY", stripped)           # remove it and the assertIn fails


# ==================================================================================================
# A7 — §A51 COVERAGE STATED, NOT ASSUMED
# ==================================================================================================

class TestCoverageStated(unittest.TestCase):

    def test_a7_a_bare_recoverable_is_refused_by_the_founding_door(self):
        # a capacity CLAIMED without its population — its coverage anchors to a subsystem space that no
        # founding step founds — is REFUSED by the founding door via the EXISTING referential-integrity
        # check (scope names a founded space), NOT a new founding check kind (stop e; the EP-31 precedent).
        bare = _capacity_law(scope="space:ghost-subsystem", coverage=[])
        with self.assertRaises(founding_install.FoundingIntegrityError):
            founding_install._validate(_prod_records() + [bare])

    def test_a7_the_near_miss_control_a_founded_scope_is_admitted(self):
        # §A64: the door can ADMIT as well as refuse — the well-formed law over a founded space passes
        # where the bare one is refused. A door that only ever refuses is not a door.
        good = _capacity_law(scope="space:root")
        founding_install._validate(_prod_records() + [good])       # does not raise
        # and the production founding itself passes the same door (the control the near-miss rides on)
        founding_install._validate(_prod_records())

    def test_a7_coverage_is_a_declared_property_population_plus_basis(self):
        # coverage is a DECLARED design property, never assumed (§A51 — a sum cannot recover its
        # addends). Each covered subsystem states BOTH its population (content anchor — the living
        # dialect) and its basis (the relational adjudicator). A bare "recoverable" states neither.
        good = _capacity_law()
        self.assertTrue(checkpoint.capacity_law_wellformed(good))
        for c in good["payload"]["coverage"]:
            self.assertTrue(c["subsystem"] and c["content"] and c["relational"])
        # RW5: a "recoverable" with NO population + basis is not well-formed
        self.assertFalse(checkpoint.capacity_law_wellformed(_capacity_law(coverage=[])))
        self.assertFalse(checkpoint.capacity_law_wellformed(
            _capacity_law(coverage=[{"subsystem": "files"}])))     # names the subsystem, states no basis


# ==================================================================================================
# RED WORLDS — RW1-RW6 driven THROUGH the instrument, named (§A42)
# ==================================================================================================

class TestRedWorlds(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep45-rw-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.blobs, self.path, self.blob_dir = \
            _attesting_hier_world(self.dir)
        self.root_val = merkle.merkle_root(replay_snapshot.snapshot(self.path, self.blob_dir, root="/"))
        self.cp = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-chip",
                                          root="/", peer_root=self.root_val)

    def test_rw1_a_verify_that_only_says_mismatch(self):
        # RW1: whole-tree equality names nothing; the Merkle localizes. Change one file — the verdict
        # NAMES the diverging subtree rather than a bare "tree mismatch".
        _write_file(self.store, self.blobs, "/dir1/a", b"changed")
        verdict = checkpoint.verify(self.cp, self.path, self.blob_dir, PACK_PATH)
        self.assertFalse(verdict["merkle_root"])
        self.assertEqual(verdict["diverging"], ["dir1/a"])         # localized, not bare

    def test_rw2_a_one_sided_pairing(self):
        cp_b_bad = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="fold-disk",
                                           root="/", peer_root="sha256:" + "e" * 64)
        v = checkpoint.pairing_verdict(self.cp, self.path, self.blob_dir,
                                       cp_b_bad, self.path, self.blob_dir)
        self.assertFalse(v["ok"])                                  # a mutual receipt is BOTH or none

    def test_rw3_a_shared_writer(self):
        a = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="one-hand",
                                    root="/", peer_root=self.root_val)
        b = checkpoint.cross_attest(self.store, self.path, self.blob_dir, witness="one-hand",
                                    root="/", peer_root=self.root_val)
        v = checkpoint.pairing_verdict(a, self.path, self.blob_dir, b, self.path, self.blob_dir)
        self.assertFalse(v["independent"])
        self.assertFalse(v["ok"])                                  # one fold defeats the pair

    def test_rw4_a_merkle_verify_that_needs_the_engine(self):
        # the pairing/verify hold NO engine handle — a signature guard (they cannot reach the gate).
        self.assertEqual(list(inspect.signature(checkpoint.pairing_verdict).parameters),
                         ["cp_a", "record_path_a", "blob_dir_a",
                          "cp_b", "record_path_b", "blob_dir_b"])
        self.assertEqual(list(inspect.signature(checkpoint.verify).parameters),
                         ["checkpoint", "record_path", "blob_dir", "pack_path"])

    def test_rw5_a_bare_summable_capacity(self):
        # the founding door does not admit a law that violates §A51 (population + basis).
        bare = _capacity_law(scope="space:nowhere", coverage=[])
        with self.assertRaises(founding_install.FoundingIntegrityError):
            founding_install._validate(_prod_records() + [bare])
        self.assertFalse(checkpoint.capacity_law_wellformed(bare))

    def test_rw6_a_truncating_recover_capacity(self):
        self.assertFalse(checkpoint.capacity_never_truncates(_capacity_law(permits_truncation=True)))
        self.assertFalse(checkpoint.capacity_never_truncates(_capacity_law(discipline="truncate-to-fit")))


if __name__ == "__main__":
    unittest.main()
