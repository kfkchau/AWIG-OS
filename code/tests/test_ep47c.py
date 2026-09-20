# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · applied-cryptography
# vocabulary (countersignature, attestation seal, key binding) per the libsodium literature; NON-GOAL:
# no offensive capability of any kind — this battery proves the store's append path carries a REAL
# countersignature once a system key is bound, refuses (never fakes) once bound where the library/
# ceremony is absent, and leaves unbound worlds byte-identical. It opens no attack surface and models no
# attack. Full declaration: SCOPE-STATEMENT.md.
"""EP-47C — LIVE-APPEND-WIRING (BUILD). The store's append path (store._append_one) CALLS
compose.append_countersign while composing every record; once a system KEY-LAW-BIND exists the record
carries a REAL countersignature (library present) or the append is REFUSED (library/ceremony absent) —
never a silent modelled mark once bound (theorem 3, EP-47B :3302 / N10). A world with NO bound system
key appends exactly as today (no countersign field — byte-identical). Boot attestation is routed through
compose.boot_attestation_seal (system_attestation_seal, derived).

Every probe is a regression test and is written so it CAN FAIL. The battery is ERA-AWARE like EP-47B's:
each real-signature assertion branches on `crypto.real_available()` — present -> the real assertions
(the appended record's countersign verifies under the bound public half); absent (the CI baseline,
nothing installed) -> the N10 refusal is asserted (a bound append REFUSES citing the absent library,
never a modelled fake), so the module is green in both runs.

  A1  TestRealCountersignAtAppend  bound + present: a record appended THROUGH THE STORE carries a real
                                   countersign verifiable under the bound public key; a tamper fails
                                   (RW-FORGE). Absent: the same append is REFUSED (crypto.LibraryAbsent).
  A2  TestRefusedNoFallback        bound but the ceremony has not run this boot (a restart) OR the library
                                   is absent: the append is REFUSED at the store (CeremonyNotRun /
                                   LibraryAbsent) — NEVER a modelled mark (a planted silent fallback reds).
  A3  TestModelledForUnbound       a world with NO bound system key appends with NO countersign field —
                                   byte-identical to the pre-EP-47C ledger; a normal governed append still
                                   lands; the countersign field, when present, is ALWAYS real (never a
                                   modelled mark reaches a record through the append path).
  A4  TestBootAttestation          boot attestation runs through boot_attestation_seal / system_attestation
                                   _seal: unbound -> None; bound + present -> a real seal verifiable under
                                   the bound public half; bound + absent -> refused.
  A5  TestExtendedLedger           the extended ledger BOTH directions, each able to fail: (too weak) a
                                   modelled mark planted on a bound-world append is DETECTABLE as not-real;
                                   the wired path never lets one land. (too wedged) a lawful append still
                                   LANDS — the append path does not seize.
      TestBootOrder                the architect's :3334 precision, honoured and tested at the append path:
                                   the ceremony's own ceremony/bind rows carry NO countersign field
                                   (system_key_bound flips at the bind row's commit), and a bind attempted
                                   BEFORE the ceremony leaves the NEXT append REFUSED, not modelled.
  A6  TestNothingNew               NOT a founding move: `founding-pack.json` is byte-identical across the
                                   whole ceremony+append flow, the founding version is unchanged, and the
                                   bare founding path (build_kernel) carries no countersign field.
  A7  the whole ledger, per module (the acceptance command, not a class here).

NOT A FOUNDING MOVE: this CALLS the EP-47B functions from the append path — no new op / kind / law /
version bump, no pack edit. THE WRONG REFERENCE THIS BATTERY REFUSES: a modelled countersign silently
reaching a record after the system key is bound (the after-bind no-fallback's whole point) — A2, A3 and
TestExtendedLedger prove the store refuses it rather than let a mark that looks signed but is not land.
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel.compose import (build_full_kernel, seal_system_signer, system_countersign,   # noqa: E402
                            system_attestation_seal, system_key_bound, CeremonyNotRun,
                            append_countersign, boot_attestation_seal)
from kernel import keys                                                                   # noqa: E402
from kernel import crypto                                                                 # noqa: E402  the ONE library boundary
from kernel import attestation                                                            # noqa: E402
from kernel.boot import seed_system_signer                                                # noqa: E402


_FOUNDING_PACK = os.path.join(os.path.dirname(__file__), "..", "src", "founding", "founding-pack.json")


def _build(dir_):
    return build_full_kernel(os.path.join(dir_, "rec.jsonl"),
                             os.path.join(dir_, "blobs"), os.path.join(dir_, "vault"))


def _append_activity(gate, about="ep47c-probe", data=None):
    """A simple governed append that lands through store._append_one (the wired path)."""
    return gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": about, "data": data or {"n": 1}})


def _pack_bytes():
    with open(_FOUNDING_PACK, "rb") as f:
        return f.read()


def _pack_version():
    import json
    with open(_FOUNDING_PACK, "r", encoding="utf-8") as f:
        return json.load(f)["founding_version"]


class _KernelCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, self.blobs, self.subs = _build(self.dir)


# ============================================================================================
# A1 — THE APPEND CARRIES A REAL COUNTERSIGN WHEN BOUND + PRESENT (refused when absent)
# ============================================================================================

class TestRealCountersignAtAppend(_KernelCase):
    def setUp(self):
        super().setUp()
        seal_system_signer(self.store, self.gate, self.views)   # the ceremony: seal the signer, bind the key

    def test_a_bound_world_append_carries_a_real_countersign_or_is_refused(self):
        self.assertTrue(system_key_bound(self.store), "precondition: the ceremony bound the system key")
        if crypto.real_available():
            rec = _append_activity(self.gate)
            mark = rec.get("countersign")
            self.assertIsNotNone(mark, "a bound-world append must carry a countersign field")
            self.assertTrue(crypto.is_real_value(mark), "present: the countersign on the record is REAL")
            self.assertTrue(
                keys.verify_countersign(mark, rec, self.views.system_key_hash, self.views.system_public_key),
                "the real countersign on the record verifies under the bound public half")
            # a countersign over a DIFFERENT recording fact must not verify (RW-FORGE)
            other = {"seq": rec.get("seq") + 1, "record_time": "2000-01-01T00:00:00.000000Z"}
            self.assertFalse(
                keys.verify_countersign(mark, other, self.views.system_key_hash, self.views.system_public_key),
                "the countersign must not verify over a different record (the check that can fail)")
        else:
            # absent: the append is REFUSED at the store citing the library — never a modelled mark
            before = len(self.store.all())
            with self.assertRaises(crypto.LibraryAbsent):
                _append_activity(self.gate)
            self.assertEqual(len(self.store.all()), before,
                             "a refused append leaves NO record (raised before the write)")


# ============================================================================================
# A2 — REFUSED WHERE BOUND BUT ABSENT / UN-CEREMONIED (no silent fallback)
# ============================================================================================

class TestRefusedNoFallback(_KernelCase):
    def test_a_restart_bound_but_no_ceremony_refuses_the_next_append_never_modelled(self):
        # bind the system key, then RESTART (rebuild from the record): the bind persists, the in-memory
        # signer is dropped — a bound world with the ceremony NOT run this boot.
        seal_system_signer(self.store, self.gate, self.views)
        # EP-MAINT-OUTSIDE-5 (re-spec C): a restart genuinely closes the old process — close the live
        # writer so the rebuilt kernel is the new WRITER; the next append then reaches the ceremony
        # guard and is refused with CeremonyNotRun (the intended refusal), not the reader-demotion.
        self.store.close()
        store2, gate2, views2, _b2, _s2 = _build(self.dir)
        self.assertTrue(system_key_bound(store2), "the KEY-LAW-BIND persists across the restart")
        self.assertIsNone(getattr(views2, "signer", None), "the in-memory signer does NOT survive a restart")
        before = len(store2.all())
        # the guard must REFUSE (CeremonyNotRun) rather than fall back to a modelled mark; a planted
        # silent fallback would let this append LAND with a modelled countersign — it must RED
        with self.assertRaises(CeremonyNotRun):
            _append_activity(gate2)
        self.assertEqual(len(store2.all()), before, "the refused append left no record — no modelled mark landed")

    def test_a_bound_world_with_the_library_absent_refuses_the_append(self):
        if crypto.real_available():
            self.skipTest("library present — the bound+absent refusal is proven where the library is absent")
        seal_system_signer(self.store, self.gate, self.views)   # signer set, but library absent
        before = len(self.store.all())
        with self.assertRaises(crypto.LibraryAbsent):
            _append_activity(self.gate)
        self.assertEqual(len(self.store.all()), before, "bound + absent: the append is refused, no record lands")

    def test_the_plant_a_modelled_mark_after_a_bind_is_modelled_material(self):
        # THE PLANT: the modelled path (signer=None) yields a mark that looks countersigned but is not
        # real — exactly the silent material the wired append path must never let a bound world carry.
        seal_system_signer(self.store, self.gate, self.views)
        planted = keys.countersign({"seq": 7, "record_time": "z"}, self.views.system_key_hash, None)
        self.assertFalse(crypto.is_real_value(planted),
                         "the plant IS modelled material — the thing the append path must refuse once bound")


# ============================================================================================
# A3 — THE MODELLED PATH SURVIVES FOR UNBOUND WORLDS (byte-identical)
# ============================================================================================

class TestModelledForUnbound(_KernelCase):
    def test_an_unbound_world_append_carries_no_countersign_field(self):
        self.assertFalse(system_key_bound(self.store), "precondition: no system key bound")
        rec = _append_activity(self.gate)
        self.assertNotIn("countersign", dict(rec),
                         "an unbound-world record carries NO countersign field — byte-identical to today")

    def test_the_whole_boot_ledger_of_an_unbound_world_carries_no_countersign(self):
        # every record the composed (unbound) kernel already holds — genesis, boot attestation, the
        # compose-layer registrations — carries no countersign field
        for rec in self.store.all():
            self.assertNotIn("countersign", dict(rec),
                             "no unbound-world record may carry a countersign field (A3 byte-identity)")

    def test_the_hook_returns_none_for_an_unbound_world(self):
        # the wiring's own decision, driven directly: unbound -> None (no field), never a modelled dict
        self.assertIsNone(append_countersign(self.store, self.views, {"seq": 1, "record_time": "z"}),
                          "append_countersign returns None for an unbound world — the store adds no field")


# ============================================================================================
# A4 — BOOT ATTESTATION THROUGH THE SEAL
# ============================================================================================

class TestBootAttestation(_KernelCase):
    def test_an_unbound_boot_seals_nothing(self):
        self.assertIsNone(boot_attestation_seal(self.store, self.views),
                          "an unbound boot seals nothing (the unsealed set-digest mark stands)")

    def test_a_bound_boot_seals_the_attested_set_or_is_refused(self):
        seal_system_signer(self.store, self.gate, self.views)
        if crypto.real_available():
            seal = boot_attestation_seal(self.store, self.views)
            self.assertIsNotNone(seal)
            self.assertTrue(crypto.is_real_value(seal), "present: a REAL attestation seal")
            self.assertTrue(
                attestation.verify_attestation_seal(attestation.attested_set(), seal,
                                                    self.views.system_public_key),
                "the real boot-attestation seal verifies under the bound public half")
        else:
            with self.assertRaises(crypto.LibraryAbsent):
                boot_attestation_seal(self.store, self.views)


# ============================================================================================
# A5 — THE EXTENDED LEDGER, BOTH DIRECTIONS (each able to fail)
# ============================================================================================

class TestExtendedLedger(_KernelCase):
    def test_too_weak_a_planted_modelled_mark_on_a_bound_world_is_detectable(self):
        # the invariant the wiring upholds: a countersign field on a bound-world record is REAL, never
        # modelled. Prove the CHECK can fail — a planted modelled mark is caught as not-real.
        seal_system_signer(self.store, self.gate, self.views)
        planted_modelled = keys.countersign({"seq": 3, "record_time": "z"}, self.views.system_key_hash, None)
        self.assertFalse(crypto.is_real_value(planted_modelled),
                         "the guard that classifies a mark can distinguish modelled from real (able to fail)")

    def test_too_weak_the_wired_path_never_lands_a_modelled_mark_once_bound(self):
        # drive the wired path: a bound-world append either carries a REAL mark (present) or is REFUSED
        # (absent) — it never lands with a modelled countersign
        seal_system_signer(self.store, self.gate, self.views)
        if crypto.real_available():
            rec = _append_activity(self.gate)
            self.assertTrue(crypto.is_real_value(rec.get("countersign")),
                            "a landed bound-world record carries a REAL mark, never modelled")
        else:
            with self.assertRaises((crypto.LibraryAbsent, CeremonyNotRun)):
                _append_activity(self.gate)

    def test_too_wedged_a_lawful_unbound_append_still_lands(self):
        # the append path must NOT seize for an unbound world (the strictly-stronger obligation:
        # the modelled path survives; the chain does not depend on the library where no key is bound)
        before = len(self.store.all())
        rec = _append_activity(self.gate)
        self.assertEqual(len(self.store.all()), before + 1, "a lawful unbound append LANDS (no seize)")
        self.assertEqual(rec.get("action"), "WRITE-ACTIVITY")

    def test_too_wedged_a_bound_present_append_still_lands(self):
        if not crypto.real_available():
            self.skipTest("library absent — the bound-present append landing is proven where present")
        seal_system_signer(self.store, self.gate, self.views)
        before = len(self.store.all())
        rec = _append_activity(self.gate)
        self.assertEqual(len(self.store.all()), before + 1, "a lawful bound+present append LANDS with a real mark")
        self.assertTrue(crypto.is_real_value(rec.get("countersign")))


# ============================================================================================
# TestBootOrder — the architect's :3334 precision, honoured and tested at the append path
# ============================================================================================

class TestBootOrder(_KernelCase):
    def test_the_ceremonys_own_rows_carry_no_countersign_field(self):
        # system_key_bound flips at the bind row's COMMIT, so during the ceremony's own ceremony/bind
        # rows it is still False — those rows take the byte-identical path (no countersign field). The
        # REAL mark begins at the first governed append AFTER the ceremony.
        seal_system_signer(self.store, self.gate, self.views)
        binds = [e for e in self.store.all()
                 if (e.get("payload") or {}).get("kind") == keys.KEY_BIND
                 and (e.get("payload") or {}).get("account") == keys.SYSTEM_KEY_NAME]
        self.assertEqual(len(binds), 1, "exactly one system KEY-LAW-BIND")
        self.assertNotIn("countersign", dict(binds[0]),
                         "the bind row itself carries no countersign field — bound flips at its commit")
        rows = [e for e in self.store.all()
                if e.get("action") == "WRITE-ACTIVITY" and e.get("object") == "system-signer-ceremony"]
        self.assertEqual(len(rows), 1, "exactly one ceremony row")
        self.assertNotIn("countersign", dict(rows[0]),
                         "the ceremony row (appended before the bind) carries no countersign field")

    def test_a_bind_before_the_ceremony_leaves_the_next_append_refused_not_modelled(self):
        # THE CONTROL (architect :3334): bind the system key WITHOUT running the ceremony (no signer
        # attached). The bind row itself lands (bound flips at its commit); the NEXT append is REFUSED
        # (CeremonyNotRun), NEVER a modelled mark. A silent fallback would let it LAND — it must RED.
        _signer, _custody, public, _descr = seed_system_signer()   # a public half, WITHOUT attaching the signer
        self.gate.execute(keys.KEY_BIND, "SYSTEM",
                          {keys.ACCOUNT: keys.SYSTEM_KEY_NAME, keys.PUBLIC_KEY: public})
        self.assertTrue(system_key_bound(self.store), "the system key is now bound")
        self.assertIsNone(getattr(self.views, "signer", None), "but no ceremony ran — no in-memory signer")
        before = len(self.store.all())
        with self.assertRaises(CeremonyNotRun):
            _append_activity(self.gate)
        self.assertEqual(len(self.store.all()), before,
                         "the append after a bind-without-ceremony is REFUSED — no modelled mark landed")


# ============================================================================================
# A6 — NOT A FOUNDING MOVE
# ============================================================================================

class TestNothingNew(_KernelCase):
    def test_founding_pack_is_byte_identical_across_the_whole_flow(self):
        before = _pack_bytes()
        before_v = _pack_version()
        # the full EP-47C flow: build, ceremony, an append (real or refused) — none of it writes the pack
        seal_system_signer(self.store, self.gate, self.views)
        try:
            _append_activity(self.gate)
        except (crypto.LibraryAbsent, CeremonyNotRun):
            pass
        after = _pack_bytes()
        self.assertEqual(hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest(),
                         "founding-pack.json is byte-identical — the wiring moves no founding")
        self.assertEqual(before_v, _pack_version(), "the founding version is unchanged — no bump")

    def test_the_bare_founding_path_carries_no_countersign_field(self):
        # build_kernel (the pack-exact founding path) has NO append hook — its founding records are
        # untouched by EP-47C; the hook is a COMPOSE-layer attachment only.
        from kernel.boot import build_kernel
        d = tempfile.mkdtemp()
        store, _gate, _views = build_kernel(os.path.join(d, "rec.jsonl"))
        self.assertIsNone(getattr(store, "_append_countersign", None),
                          "a bare founding kernel carries no countersign hook")
        for rec in store.all():
            self.assertNotIn("countersign", dict(rec),
                             "no founding record carries a countersign field (not a founding move)")


if __name__ == "__main__":
    unittest.main()
