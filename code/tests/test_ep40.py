"""EP-40-BUILD acceptance + red-world battery: engine attestation (design/37 Q3 + §9).

Folded to the :2769 R1/R2/item-4 ruling (2026-09-03): attestation rides at the COMPOSE LAYER
(compose.build_full_kernel), ABOVE the founding boot, THROUGH THE GATE as a governed SYSTEM op;
the op is OWNER-GATED founding-integrity vocabulary. COMPLETE-ATTEST-OP flip (owner's create-word
board :2847, scope confirmed COMPOSE-FLIP-ONLY at :2866): the owner's word has LANDED, so production
compose now REGISTERS the op and attests live at boot. The flip moves NO founding — register_attestation
is a CODE registration, so founding-pack.json is byte-untouched — and build_kernel, the founding path,
still never attests (R1). Production attesting live is now a first-class acceptance (TestProductionAttests).

T-ENGINE-ATTESTS   (A1) the compose-layer boot APPENDS one attestation record THROUGH THE GATE;
                   its digest covers the enumerated attested set INCLUDING the digest machinery
                   itself (canonical.py + attestation.py); idempotent per boot.
TestMatchProbe     (A2) the derived match probe, BOTH directions — matches on an unchanged
                   tree; detects a mutated artifact and routes it to the owner queue
                   (appends nothing). Near-miss control §A64: it can report a mismatch.
TestAttestationTwin(A3) the T-NO-LAW-IN-CODE twin — the guard's grepped surface and the
                   attested set are the SAME set by construction; a governance-bearing
                   surface planted outside the set is detected.
TestRoundTrip      (A4) attestation records replay as DATA (boot never re-attests over an
                   unchanged reload), and the probe recomputes identically.
TestProductionAttests the owner-gate FLIPPED live — production compose registers the op and
                   appends ONE attestation record at boot (the match probe answers both ways);
                   build_kernel, the founding path, STILL never attests (R1).
TestRedWorlds      RW1-RW4 driven THROUGH the instrument.

Honest bound carried in the doc-facing names (design/37 §9): self-attestation proves
CITABILITY, not immunity — never `trusted`.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.boot import build_kernel  # noqa: E402  (the founding path — proven NON-attesting)
from kernel.compose import build_full_kernel  # noqa: E402  (the compose layer — where attestation rides)
from kernel.attestation import (  # noqa: E402
    ATTESTATION_ACTION, ATTESTATION_OP, ATTESTATION_RULE, ATTESTED_MEMBERS, EXCLUDED,
    attest_boot, attested_set, latest_attestation, law_guard_surface, match_probe,
    register_attestation, twin_uncovered,
)
# The law guard this EP twins — imported so the twin's coverage is demonstrated AGAINST the
# guard's own grep surface, not a private re-derivation of it (architect ruling :2751, tooth
# iii: "the twin's coverage and the guard's grep surface are the same set by construction,
# demonstrated in the test").
from test_law_out_of_code import _src_py_outside_founding  # noqa: E402


def _mirror_src(dst_root):
    """A working copy of the real src/ tree, so a red-world mutation is driven through the
    real probe without ever touching a fenced source file. Returns the copy's src dir."""
    real = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    dst = os.path.join(dst_root, "src")
    shutil.copytree(real, dst)
    return dst


def _attesting_world(dir_, name="record.jsonl"):
    """A TEST founding world where the owner's word HAS landed. Build the FULL kernel (attestation
    rides at the compose layer, never in build_kernel), then register the owner-gated attestation
    op and run the compose-layer boot append — exactly the two things production compose holds
    inert until the word lands (compose does NOT call register_attestation). Returns
    (store, gate, views, path, blob_dir) so a caller can reload the same file."""
    path = os.path.join(dir_, name)
    blob_dir = os.path.join(dir_, "blobs")
    store, gate, views, _blobs, _subs = build_full_kernel(path, blob_dir)
    register_attestation(gate)          # the owner's word, landed (production compose omits this)
    attest_boot(store, gate)            # the compose-layer boot append, now live, THROUGH THE GATE
    return store, gate, views, path, blob_dir


class TestEngineAttests(unittest.TestCase):
    """A1 — T-ENGINE-ATTESTS. Proven in a test founding world with the op registered."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep40-a1-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, self.views, self.path, self.blob_dir = _attesting_world(self.dir)

    def test_boot_appends_one_attestation_citing_boot_int_through_the_gate(self):
        att = self.store.by_action(ATTESTATION_ACTION)
        self.assertEqual(len(att), 1, "the compose-layer boot appended exactly one attestation")
        rec = att[0]
        self.assertEqual(rec["actor"], "SYSTEM")               # the recorder, not a governed actor
        self.assertEqual(rec["rule_cited"], ATTESTATION_RULE)  # BOOT-INT, the boot-integrity law
        self.assertEqual(rec["payload"]["kind"], "attestation")
        self.assertTrue(rec["payload"]["set_digest"].startswith("sha256:"))
        # THROUGH THE GATE (R2): the gate is the sole appender, so it accepted this SYSTEM op with
        # no refusal — a raw store._append would have been the refused ungated post-genesis route.
        self.assertEqual(self.store.by_action("op-refused"), [])
        self.assertTrue(self.gate.has(ATTESTATION_OP))

    def test_digest_covers_the_enumerated_set_including_the_digest_machinery(self):
        members = self.store.by_action(ATTESTATION_ACTION)[0]["payload"]["members"]
        # every enumerated member is digested in the record...
        self.assertEqual(set(members), set(ATTESTED_MEMBERS))
        # ...INCLUDING the digest machinery itself — this is what closes the EP-09
        # shared-digest-function cap (design/37 Q3): the function both audit streams rely on is
        # inside the attested surface.
        self.assertIn("kernel/canonical.py", members)
        self.assertIn("kernel/attestation.py", members)
        self.assertTrue(all(d and d.startswith("sha256:") for d in members.values()))
        # the set-digest is a canonical function of the per-member digests (recompute -> equal)
        self.assertEqual(self.store.by_action(ATTESTATION_ACTION)[0]["payload"]["set_digest"],
                         attested_set()["set_digest"])

    def test_the_known_out_member_is_named_with_why_and_a_future_path(self):
        # architect ruling :2751 tooth i + ii: a silent exclusion is undeclared. The record
        # carries the guest module by name, the boundary reason, and when it joins.
        excluded = self.store.by_action(ATTESTATION_ACTION)[0]["payload"]["excluded"]
        self.assertIn("planning/vm/govosfs/", excluded)
        why = excluded["planning/vm/govosfs/"]
        self.assertIn("guest", why.lower())                    # the boundary reason (whose word)
        self.assertIn("campaign 7", why.lower())               # the future path, by name
        # and the excluded member is NOT smuggled into the attested set
        self.assertNotIn("planning/vm/govosfs/", ATTESTED_MEMBERS)

    def test_idempotent_per_boot(self):
        # A second boot over an unchanged tree yields the SAME attested digest, not a divergent
        # record (F2). attest_boot returns None on the idempotent call and the count stays 1.
        first = self.store.by_action(ATTESTATION_ACTION)[0]["payload"]["set_digest"]
        self.assertIsNone(attest_boot(self.store, self.gate),
                          "a second attest over an unchanged tree appends nothing")
        self.assertEqual(len(self.store.by_action(ATTESTATION_ACTION)), 1)
        # a full reload of the SAME file: the attestation replays as data and the re-run boot append
        # (owner's word landed again) finds the digest already recorded — idempotent, still one.
        store2, gate2, _v2, _b2, _s2 = _attesting_world(self.dir, name="record.jsonl")
        self.assertEqual(len(store2.by_action(ATTESTATION_ACTION)), 1)
        self.assertEqual(store2.by_action(ATTESTATION_ACTION)[0]["payload"]["set_digest"], first)


class TestMatchProbe(unittest.TestCase):
    """A2 — the match probe, both directions. A DERIVED check that appends nothing."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep40-a2-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, _v, _p, _b = _attesting_world(self.dir)

    def test_match_direction_unchanged_tree_matches(self):
        before = len(self.store.all())
        probe = match_probe(self.store)
        self.assertTrue(probe["attested"])
        self.assertTrue(probe["matches"])
        self.assertEqual(probe["changed"], [])
        self.assertEqual(probe["missing"], [])
        self.assertEqual(len(self.store.all()), before, "the probe is a derivation; it appends nothing")

    def test_detect_direction_a_mutated_artifact_is_caught_and_routed(self):
        # THE NEAR-MISS CONTROL (§A64): a probe that cannot report a mismatch is not a probe.
        # Mutate one attested artifact in a working copy and drive the SAME probe over it; the
        # attestation on record was taken over the real tree, so the mutated member diverges.
        src = _mirror_src(self.dir)
        victim = os.path.join(src, "kernel/gate.py")
        with open(victim, "a", encoding="utf-8") as f:
            f.write("\n# EP-40 red-world mutation (a silent engine change)\n")
        before = len(self.store.all())
        probe = match_probe(self.store, src_dir=src)
        self.assertFalse(probe["matches"], "a mutated engine artifact must not read as matching")
        self.assertEqual(probe["changed"], ["kernel/gate.py"], "the exact diverging member is named")
        self.assertEqual(len(self.store.all()), before, "routing to the owner queue appends nothing")

    def test_no_attestation_on_record_is_not_a_match(self):
        # An engine that never attested is not a matching engine — the probe reports it rather
        # than defaulting to a silent pass.
        from kernel.store import EventStore
        bare = EventStore(os.path.join(self.dir, "bare.jsonl"), require_rule_cited=False)
        probe = match_probe(bare)
        self.assertFalse(probe["attested"])
        self.assertFalse(probe["matches"])


class TestAttestationTwin(unittest.TestCase):
    """A3 — the T-NO-LAW-IN-CODE twin. Coverage == the guard's grep surface, by construction."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep40-a3-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_the_guard_greps_src_only_and_the_set_is_exactly_that_surface(self):
        # tooth iii: T-NO-LAW-IN-CODE greps every .py under src/ outside founding/ — nothing
        # under planning/vm/govosfs/ — so the attested set covering exactly that surface makes
        # the twin's claim EXACTLY true under the govosfs exclusion.
        guard_surface = {rel for rel, _src in _src_py_outside_founding()}
        self.assertEqual(guard_surface, set(ATTESTED_MEMBERS),
                         "the guard's grep surface and the attested set are the same set")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS))
        # nothing the guard greps lies outside the attested set (the twin's coverage claim)
        self.assertEqual(twin_uncovered(), [])

    def test_a_governance_surface_planted_outside_the_set_is_detected(self):
        # RW1 near-miss: a .py under src/ outside founding/, absent from the manifest, is a
        # governance-bearing surface outside attestation coverage — the twin REDS naming it.
        src = _mirror_src(self.dir)
        planted = os.path.join(src, "kernel", "rogue_law.py")
        with open(planted, "w", encoding="utf-8") as f:
            f.write("# a governance-bearing surface the guard would grep but the set omits\n")
        self.assertEqual(twin_uncovered(src_dir=src), ["kernel/rogue_law.py"])

    def test_an_incidental_non_py_or_founding_file_does_not_trip_the_twin(self):
        # the near-miss control's other half: an over-report would flag files the guard never
        # greps. A non-.py file, and a .py UNDER founding/, are both outside the guard's surface
        # and must NOT be reported as uncovered.
        src = _mirror_src(self.dir)
        with open(os.path.join(src, "kernel", "notes.txt"), "w", encoding="utf-8") as f:
            f.write("not code\n")
        with open(os.path.join(src, "founding", "extra.py"), "w", encoding="utf-8") as f:
            f.write("# law's home — the guard excludes founding/, so the twin must too\n")
        self.assertEqual(twin_uncovered(src_dir=src), [])


class TestRoundTrip(unittest.TestCase):
    """A4 — attestations replay as DATA; the probe recomputes identically."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep40-a4-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_attestation_replays_as_data_and_the_probe_is_stable(self):
        store, _g, _v, _p, _b = _attesting_world(self.dir)
        digest = store.by_action(ATTESTATION_ACTION)[0]["payload"]["set_digest"]
        # replay: a fresh full kernel over the same file — every derived cache killed, the op
        # re-registered (owner's word). The attestation replays as a DATA record (boot does not
        # re-attest: the digest is unchanged) and the probe recomputes the same answer.
        store2, _g2, _v2, _p2, _b2 = _attesting_world(self.dir, name="record.jsonl")
        att2 = store2.by_action(ATTESTATION_ACTION)
        self.assertEqual(len(att2), 1, "replay re-attests nothing — the attestation is data")
        self.assertEqual(att2[0]["payload"]["set_digest"], digest)
        self.assertTrue(match_probe(store2)["matches"])


class TestProductionAttests(unittest.TestCase):
    """THE OWNER-GATE, FLIPPED LIVE (:2769 item 4; COMPLETE-ATTEST-OP, owner's create-word board
    :2847, scope confirmed COMPOSE-FLIP-ONLY at :2866). Production `compose.build_full_kernel` now
    REGISTERS the owner-gated op and attests live at boot: exactly ONE attestation record is
    appended, THROUGH THE GATE (no refusal), and the match probe answers both directions. The flip
    moves NO founding — founding-pack.json is byte-untouched (register_attestation is a CODE
    registration, not a pack CREATE-OP). And build_kernel, the founding path, STILL never attests (R1)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep40-live-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_compose_registers_the_op_and_attests_live_at_boot(self):
        store, gate, _v, _b, _s = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"))
        # the owner's word has landed: production compose now registers the op and attests.
        self.assertTrue(gate.has(ATTESTATION_OP), "production registers the attestation op (flip live)")
        att = store.by_action(ATTESTATION_ACTION)
        self.assertEqual(len(att), 1, "production compose appended exactly one attestation record")
        rec = att[0]
        self.assertEqual(rec["actor"], "SYSTEM")
        self.assertEqual(rec["rule_cited"], ATTESTATION_RULE)          # BOOT-INT
        self.assertEqual(rec["payload"]["kind"], "attestation")
        self.assertEqual(set(rec["payload"]["members"]), set(ATTESTED_MEMBERS))
        self.assertEqual(len(ATTESTED_MEMBERS), 53)                    # the enumerated S-plane set (53 since EP-52-BUILD's subsystems/filter.py add — FIREWALL-IN-THE-RECORD, C5 P7, the founding mover, §5 count-pin companion driven at dispatch; 52 since EP-49A-BUILD's kernel/border.py add — THE BORDER: THE DOOR, the campaign-5 crux, §5 fence "+ its ATTESTED_MEMBERS line and count-pin companion", DRIVEN at dispatch not carried; 51 since EP-48-BUILD's subsystems/sockets.py add — SOCKET-GRANTS, the campaign-5 founding mover, §5 name-and-count sweep + :3255(b) by-name widen, KEY-MATERIAL-REAL's signer.py already in at 50; 50 since KEY-MATERIAL-REAL's kernel/signer.py add — archi :3249, the by-name count-pin widen doubled from crypto.py; 49 at kernel/crypto.py, the :3031/:3041 double-stop companion; 48 at EP-46-BUILD's bridge/seal.py add, board :3031; 47 at EP-43-AUTO's bridge/auto_recover.py add; 46 at EP-45's bridge/merkle.py add, :3045)
        self.assertEqual(len(rec["payload"]["members"]), 53)          # 53 since EP-52-BUILD's subsystems/filter.py add (§5 count-pin companion, driven at dispatch); 52 since EP-49A-BUILD's kernel/border.py add (the boot-attestation's recorded member count, the :259 count-pin's twin; driven at dispatch)
        self.assertTrue(rec["payload"]["set_digest"].startswith("sha256:"))  # set_digest present
        # THROUGH THE GATE (R2): the SYSTEM op was accepted, no refusal reached the record.
        self.assertEqual(store.by_action("op-refused"), [], "0 op-refused — the gate accepted it")
        # the match probe answers BOTH directions against the live production attestation:
        matched = match_probe(store)                                  # unchanged tree -> matches
        self.assertTrue(matched["attested"])
        self.assertTrue(matched["matches"])
        self.assertEqual(matched["changed"], [])
        src = _mirror_src(self.dir)                                    # mutated tree -> detected
        with open(os.path.join(src, "kernel/gate.py"), "a", encoding="utf-8") as f:
            f.write("\n# COMPLETE-ATTEST-OP probe: a silent engine change\n")
        diverged = match_probe(store, src_dir=src)
        self.assertFalse(diverged["matches"], "a mutated artifact must not read as matching")
        self.assertEqual(diverged["changed"], ["kernel/gate.py"])
        # a second boot over the unchanged tree is idempotent — no divergent record.
        self.assertIsNone(attest_boot(store, gate))
        self.assertEqual(len(store.by_action(ATTESTATION_ACTION)), 1)

    def test_build_kernel_the_founding_path_never_attests(self):
        # R1: the attestation is a COMPOSE act, above the founding boot. build_kernel stays
        # pack-exact — a boot append here is the founding-roundtrip divergence (test_ep14) this
        # fold exists to remove.
        store, _g, _v = build_kernel(os.path.join(self.dir, "record.jsonl"))
        self.assertEqual(store.by_action(ATTESTATION_ACTION), [])


class TestRedWorlds(unittest.TestCase):
    """RW1-RW4, each driven THROUGH the instrument and recorded (§A42)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep40-rw-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store, self.gate, _v, _p, _b = _attesting_world(self.dir)

    def test_RW1_unattested_governance_surface_reds(self):
        src = _mirror_src(self.dir)
        with open(os.path.join(src, "subsystems", "shadow_law.py"), "w", encoding="utf-8") as f:
            f.write("# governance surface outside the attested set\n")
        self.assertEqual(twin_uncovered(src_dir=src), ["subsystems/shadow_law.py"])

    def test_RW2_silent_engine_change_reds_through_the_probe(self):
        src = _mirror_src(self.dir)
        with open(os.path.join(src, "kernel/store.py"), "a", encoding="utf-8") as f:
            f.write("\n# EP-40 RW2: a silent engine change with no new boot attestation\n")
        probe = match_probe(self.store, src_dir=src)
        self.assertFalse(probe["matches"])
        self.assertIn("kernel/store.py", probe["changed"])

    def test_RW3_a_shrink_of_the_set_routes_as_a_deliberate_act_violation(self):
        # F1's list is grow-only. Plant a PRIOR attestation recording an extra member; the
        # current tree lacks it, so the probe reports it MISSING — a shrink routes to the owner,
        # never a silent edit. (A test may _append directly; the sole-appender guard greps src/.)
        fatter = attested_set()
        fatter_members = dict(fatter["members"])
        fatter_members["kernel/ghost.py"] = "sha256:" + "0" * 64
        self.store._append({
            "actor": "SYSTEM", "action": ATTESTATION_ACTION, "object": "engine",
            "rule_cited": ATTESTATION_RULE,
            "payload": {"kind": "attestation", "set_digest": "sha256:" + "f" * 64,
                        "members": fatter_members, "excluded": dict(EXCLUDED)},
        })
        probe = match_probe(self.store)
        self.assertIn("kernel/ghost.py", probe["missing"])
        self.assertFalse(probe["matches"])

    def test_RW4_a_divergent_attestation_over_an_unchanged_tree_is_refused(self):
        # Idempotency: boot must NOT append a divergent attestation over an unchanged tree.
        # The near-miss that proves the check can distinguish: over a MUTATED tree, attest_boot
        # DOES append (so the idempotent skip is a real decision, not a blanket no-op).
        self.assertIsNone(attest_boot(self.store, self.gate),
                          "unchanged tree -> no divergent attestation")
        self.assertEqual(len(self.store.by_action(ATTESTATION_ACTION)), 1)
        src = _mirror_src(self.dir)
        with open(os.path.join(src, "kernel/views.py"), "a", encoding="utf-8") as f:
            f.write("\n# EP-40 RW4: a genuine engine change\n")
        appended = attest_boot(self.store, self.gate, src_dir=src)
        self.assertIsNotNone(appended, "a changed tree DOES attest — the skip is a real decision")
        self.assertEqual(len(self.store.by_action(ATTESTATION_ACTION)), 2)


if __name__ == "__main__":
    unittest.main()
