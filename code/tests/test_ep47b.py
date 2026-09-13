# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · applied-cryptography
# vocabulary (boot ceremony, key seal, signature, entropy) per the libsodium literature; NON-GOAL: no
# offensive capability of any kind — this battery proves the boot wiring that seats a system signing
# key into custody and binds its public half; it opens no attack surface and models no attack. Full
# declaration: SCOPE-STATEMENT.md.
"""EP-47B — SYSTEM-SIGNER-AT-BOOT (BUILD). The recorded ceremony that seals the system's Ed25519 seed
into the signer AT BOOT, binds the public half as a KEY-LAW-BIND row via the EXISTING op:key-bind, and
wires keys.countersign / attestation_seal to the boot-seeded signer.

Every probe is a regression test (the campaign method) and every one is written so it CAN FAIL. The
battery is ERA-AWARE like KEY-MATERIAL-REAL's: each test branches on `crypto.real_available()` —
present -> the real assertions (real signatures verify under the bound public half); absent (the CI
baseline, nothing installed) -> the N10 refusal is asserted, so the module is green in both runs.

  A1  TestSignerSeededAtBoot   after the ceremony the signer holds a SYSTEM key and the public half is
                               bound; before it, no signer and no bind (present: compare_public matches).
  A2  TestRealSignerWired      countersign + attestation route to the boot-seeded signer: present -> real
                               Ed25519 signatures verify under the bound public key, a tamper fails
                               (RW-FORGE); absent -> a real signature is REFUSED citing the library, never
                               a modelled fake (N10 / RW-FAKE-WHEN-ABSENT).
  A3  TestPublicHalfIsKeyLaw   the public half is a single KEY-LAW-BIND row (W4 payload shape, no extra
                               field); the private seed is NOT in the record — the signer exposes no read
                               path and the ceremony row carries only a commitment (RW-SEED-IN-RECORD).
  A4  TestRestartNeedsReSeed   a restart (rebuild from the record) drops the in-memory signer while the
                               bind persists; the store REFUSES to grow — countersign cites the missing
                               ceremony (a planted 'seed silently survived a restart' reds).
      TestSilentModelledAfterBind  the planted control: after a bind, the modelled path taken silently
                               must RED — the guard refuses it (RW-SILENT-MODELLED-AFTER-BIND).
      TestCeremonyEntropyFloor the Option A ceremony (architect precisions, 2026-09-08): the OS source is
                               ALWAYS mixed in; a human contribution is MEASURED and REFUSED below the
                               floor (the planted low-entropy case reds), atomically — no partial record.
      TestCeremonyRecordedRow  the ceremony ROW records THAT it happened, WHEN, HOW MANY events, and a
                               HASH COMMITMENT — never the raw samples; a headless boot records the
                               OS-only path.
  A5  the whole ledger, per module (the acceptance command, not a class here).

NOT A FOUNDING MOVE: the bind rides the EXISTING op:key-bind under the EXISTING KEY-LAW-BIND, and the
ceremony row is an EXISTING WRITE-ACTIVITY record — no new op / kind / law / version bump. THE WRONG
REFERENCE THIS BATTERY REFUSES: a modelled countersign presented as real after the system key is bound
(the era-split's whole point turned on the system's own key) — A2/A4 and the two controls prove the
store refuses it rather than silently producing a mark that looks signed but is not.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel.compose import (build_full_kernel, seal_system_signer, system_countersign,   # noqa: E402
                            system_attestation_seal, system_key_bound, CeremonyNotRun, CEREMONY_ROW)
from kernel import keys                                                                   # noqa: E402
from kernel import crypto                                                                 # noqa: E402  the ONE library boundary
from kernel import attestation                                                            # noqa: E402
from kernel.boot import collect_system_seed, measure_entropy_bits, new_os_material        # noqa: E402
from kernel.signer import SigningKeyStore                                                 # noqa: E402


def _build(dir_):
    return build_full_kernel(os.path.join(dir_, "rec.jsonl"),
                             os.path.join(dir_, "blobs"), os.path.join(dir_, "vault"))


def _system_binds(store):
    return [e for e in store.all()
            if (e.get("payload") or {}).get("kind") == keys.KEY_BIND
            and (e.get("payload") or {}).get("account") == keys.SYSTEM_KEY_NAME]


def _ceremony_rows(store):
    return [e for e in store.all()
            if e.get("action") == "WRITE-ACTIVITY" and e.get("object") == CEREMONY_ROW]


def _record_blob(store):
    """The whole record as one string, for a raw-material scan (records carry mappingproxy payloads,
    so str() rather than json)."""
    return " ".join(str(e) for e in store.all())


_A_RECORD = {"seq": 512, "record_time": "2026-09-08T00:00:00.000000Z"}


class _KernelCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, self.blobs, self.subs = _build(self.dir)


# ============================================================================================
# A1 — THE SIGNER IS SEEDED AT BOOT
# ============================================================================================

class TestSignerSeededAtBoot(_KernelCase):
    def test_before_the_ceremony_there_is_no_signer_and_no_system_bind(self):
        self.assertIsNone(getattr(self.views, "signer", None),
                          "a fresh kernel must carry no signer until the ceremony runs")
        self.assertFalse(system_key_bound(self.store),
                         "a fresh kernel must carry no system KEY-LAW-BIND until the ceremony runs")
        # before the seed step, the store countersignature is the MODELLED mark, not a real signature
        mark = system_countersign(self.store, self.views, _A_RECORD)
        self.assertFalse(crypto.is_real_value(mark),
                         "before the ceremony the countersignature is the modelled mark (as today)")

    def test_after_the_ceremony_the_signer_holds_a_system_key_and_the_public_half_is_bound(self):
        signer = seal_system_signer(self.store, self.gate, self.views)
        self.assertIsNotNone(signer)
        self.assertIs(self.views.signer, signer, "the signer is attached to the composed kernel")
        self.assertTrue(system_key_bound(self.store), "the system public half is bound (a KEY-LAW-BIND)")
        self.assertEqual(keys.bound_key(self.store, keys.SYSTEM_KEY_NAME), self.views.system_public_key)
        self.assertTrue(self.views.system_key_hash.startswith("sha256:"),
                        "the custody hash is the public commitment the countersign binds under")

    def test_present_library_compare_public_matches_the_bound_public_half(self):
        if not crypto.real_available():
            self.skipTest("vetted library absent — the real public-half compare is proven where present")
        seal_system_signer(self.store, self.gate, self.views)
        self.assertTrue(
            self.views.signer.compare_public(self.views.system_key_hash, self.views.system_public_key),
            "the boot-seeded signer's real public half must equal the bound public key")
        # a DIFFERENT public key must NOT match (the check that can fail)
        other = SigningKeyStore()
        other_pub = crypto.public_from_seed(crypto.new_signing_seed())
        self.assertFalse(self.views.signer.compare_public(self.views.system_key_hash, other_pub))


# ============================================================================================
# A2 — COUNTERSIGN + ATTESTATION USE THE REAL SIGNER (present: real; absent: refuse — N10)
# ============================================================================================

class TestRealSignerWired(_KernelCase):
    def setUp(self):
        super().setUp()
        seal_system_signer(self.store, self.gate, self.views)

    def test_countersign_routes_to_the_boot_seeded_signer(self):
        if crypto.real_available():
            mark = system_countersign(self.store, self.views, _A_RECORD)
            self.assertTrue(crypto.is_real_value(mark), "present: a REAL Ed25519 countersignature")
            self.assertTrue(
                keys.verify_countersign(mark, _A_RECORD, self.views.system_key_hash,
                                        self.views.system_public_key),
                "the real countersignature verifies under the bound public half")
            other = {"seq": 999, "record_time": "2026-01-01T00:00:00Z"}
            self.assertFalse(
                keys.verify_countersign(mark, other, self.views.system_key_hash,
                                        self.views.system_public_key),
                "a countersignature over a DIFFERENT record must not verify (RW-FORGE)")
        else:
            with self.assertRaises(crypto.LibraryAbsent):
                system_countersign(self.store, self.views, _A_RECORD)

    def test_attestation_seal_routes_to_the_boot_seeded_signer(self):
        attested = attestation.attested_set()
        if crypto.real_available():
            seal = system_attestation_seal(self.store, self.views, attested)
            self.assertTrue(crypto.is_real_value(seal), "present: a REAL Ed25519 attestation seal")
            self.assertTrue(
                attestation.verify_attestation_seal(attested, seal, self.views.system_public_key),
                "the real seal verifies under the bound public half")
        else:
            with self.assertRaises(crypto.LibraryAbsent):
                system_attestation_seal(self.store, self.views, attested)


# ============================================================================================
# A3 — THE PUBLIC HALF IS A KEY-LAW ROW; THE PRIVATE SEED IS NOT IN THE RECORD
# ============================================================================================

class TestPublicHalfIsKeyLaw(_KernelCase):
    def setUp(self):
        super().setUp()
        self.signer = seal_system_signer(self.store, self.gate, self.views)

    def test_exactly_one_system_bind_with_the_w4_payload_shape(self):
        binds = _system_binds(self.store)
        self.assertEqual(len(binds), 1, "exactly one KEY-LAW-BIND for the system key")
        payload_keys = set(binds[0]["payload"].keys())
        self.assertEqual(payload_keys, {keys.ACCOUNT, keys.PUBLIC_KEY, "kind", keys.CLASS},
                         "the bind payload shape is unchanged — no founding amend / extra field")
        self.assertEqual(binds[0]["payload"][keys.PUBLIC_KEY], self.views.system_public_key,
                         "the bound value is what verification reads")

    def test_the_signer_exposes_no_read_path_so_the_seed_cannot_reach_the_record(self):
        public_surface = sorted(m for m in dir(self.signer) if not m.startswith("_"))
        self.assertEqual(public_surface, ["compare_public", "seal", "sign"],
                         "the signer surface is exactly {seal, sign, compare_public} — no get/reveal/export")

    def test_the_record_carries_the_commitment_not_the_private_seed(self):
        # the ceremony row carries ONLY the commitment + metadata, never a seed field
        row_payload = dict(_ceremony_rows(self.store)[0]["payload"])
        self.assertEqual(set(row_payload),
                         {"ceremony", "source", "event_count", "entropy_bits", "commitment"})
        self.assertEqual(row_payload["commitment"], self.views.system_key_hash,
                         "the recorded commitment is the public custody hash, one-way over the seed")
        self.assertNotIn("seed", row_payload)


# ============================================================================================
# A4 — A RESTART NEEDS RE-SEEDING (the in-memory-only design, proven not assumed)
# ============================================================================================

class TestRestartNeedsReSeed(_KernelCase):
    def setUp(self):
        super().setUp()
        seal_system_signer(self.store, self.gate, self.views)

    def test_a_restart_drops_the_signer_while_the_bind_persists(self):
        store2, gate2, views2, _b2, _s2 = _build(self.dir)   # rebuild from the record = a restart
        self.assertIsNone(getattr(views2, "signer", None),
                          "the in-memory seed does NOT survive a restart")
        self.assertTrue(system_key_bound(store2), "the KEY-LAW-BIND persists on the record")

    def test_after_a_restart_the_store_refuses_to_grow_without_the_ceremony(self):
        store2, _g2, views2, _b2, _s2 = _build(self.dir)
        # a planted 'seed silently survived a restart' would let this produce a modelled mark; it REDS
        with self.assertRaises(CeremonyNotRun):
            system_countersign(store2, views2, _A_RECORD)
        with self.assertRaises(CeremonyNotRun):
            system_attestation_seal(store2, views2, attestation.attested_set())

    def test_re_running_the_ceremony_restores_the_signer(self):
        store2, gate2, views2, _b2, _s2 = _build(self.dir)
        seal_system_signer(store2, gate2, views2)            # the ceremony re-runs
        self.assertIsNotNone(views2.signer)
        # now the store can grow again (real where present, refusing-the-library where absent)
        if crypto.real_available():
            self.assertTrue(crypto.is_real_value(system_countersign(store2, views2, _A_RECORD)))
        else:
            with self.assertRaises(crypto.LibraryAbsent):
                system_countersign(store2, views2, _A_RECORD)


# ============================================================================================
# RW-SILENT-MODELLED-AFTER-BIND — the planted control (build AND prove it able to fail)
# ============================================================================================

class TestSilentModelledAfterBind(_KernelCase):
    def setUp(self):
        super().setUp()
        seal_system_signer(self.store, self.gate, self.views)

    def test_the_raw_modelled_path_after_a_bind_would_be_silent_modelled_material(self):
        # THE PLANT: keys.countersign with signer=None returns a modelled mark that looks countersigned
        # but is not real — exactly the silent modelled path that must never be taken after a bind.
        planted = keys.countersign(_A_RECORD, self.views.system_key_hash, None)
        self.assertFalse(crypto.is_real_value(planted),
                         "the plant IS modelled material — the thing the guard must refuse")

    def test_the_guard_refuses_the_modelled_path_once_the_system_key_is_bound(self):
        # simulate the ceremony not having run (no in-memory signer) while the bind stands
        self.views.signer = None
        with self.assertRaises(CeremonyNotRun):
            system_countersign(self.store, self.views, _A_RECORD)
        with self.assertRaises(CeremonyNotRun):
            system_attestation_seal(self.store, self.views, attestation.attested_set())


# ============================================================================================
# TestCeremonyEntropyFloor — the Option A ceremony's entropy discipline (architect precisions)
# ============================================================================================

class TestCeremonyEntropyFloor(_KernelCase):
    def test_a_low_entropy_or_fixed_contribution_is_refused_atomically(self):
        for label, contributed in [
            ("all-zeros", b"\x00" * 32),
            ("repeated", b"password" * 4),
            ("too-short", b"short"),
            ("stuck-event-stream", [7] * 8),
        ]:
            dir_ = tempfile.mkdtemp()
            store, gate, views, _b, _s = _build(dir_)
            with self.assertRaises(ValueError, msg=f"{label}: a below-floor contribution must be refused"):
                seal_system_signer(store, gate, views, contributed=contributed)
            # the refusal is ATOMIC — no partial record grew (no bind, no ceremony row)
            self.assertFalse(system_key_bound(store), f"{label}: no bind on a refused ceremony")
            self.assertEqual(len(_ceremony_rows(store)), 0, f"{label}: no ceremony row on a refusal")

    def test_the_os_source_is_always_mixed_in_never_replaced(self):
        # the SAME human events yield DIFFERENT seeds — proof the OS source is always in the mix
        events = list(range(64))
        seed_a, _da = collect_system_seed(events)
        seed_b, _db = collect_system_seed(events)
        self.assertNotEqual(seed_a, seed_b, "identical human events must not fix the seed — OS always mixed")
        self.assertEqual(len(seed_a), 32)

    def test_a_generated_os_draw_clears_the_floor_and_a_dead_source_does_not(self):
        self.assertGreaterEqual(measure_entropy_bits(new_os_material()), 128.0,
                                "os.urandom material clears the entropy floor")
        self.assertLess(measure_entropy_bits(b"\x00" * 32), 128.0,
                        "an all-zeros blob is below the floor (the measurement can fail)")


# ============================================================================================
# TestCeremonyRecordedRow — the ceremony row (that/when/how-many/commitment; never raw samples)
# ============================================================================================

class TestCeremonyRecordedRow(_KernelCase):
    def test_a_headless_boot_records_the_os_only_path(self):
        seal_system_signer(self.store, self.gate, self.views)         # no human events = headless
        rows = _ceremony_rows(self.store)
        self.assertEqual(len(rows), 1, "the ceremony records exactly one row")
        payload = dict(rows[0]["payload"])
        self.assertEqual(payload["source"], "headless-os-only", "a headless boot records the OS-only path")
        self.assertEqual(payload["event_count"], 0)
        self.assertTrue(rows[0].get("record_time"), "the row records WHEN (its record_time)")
        self.assertTrue(str(payload["commitment"]).startswith("sha256:"), "the row records a HASH COMMITMENT")

    def test_a_human_mixed_ceremony_records_the_count_and_commitment_never_the_raw_samples(self):
        events = list(range(9000, 9050))
        seal_system_signer(self.store, self.gate, self.views, contributed=events)
        payload = dict(_ceremony_rows(self.store)[0]["payload"])
        self.assertEqual(payload["source"], "human-mixed")
        self.assertEqual(payload["event_count"], len(events), "the row records HOW MANY events")
        blob = _record_blob(self.store)
        self.assertNotIn("9000", blob, "the raw event samples are NEVER in the record")
        self.assertNotIn("9049", blob, "the raw event samples are NEVER in the record")
        self.assertIn(str(payload["commitment"]).split(":", 1)[1], blob,
                      "only the one-way commitment reaches the record")


if __name__ == "__main__":
    unittest.main()
