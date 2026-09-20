# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · applied-cryptography
# vocabulary (signature, authenticated encryption, key wrapping, key derivation) per the libsodium
# literature; NON-GOAL: no offensive capability of any kind — this battery proves confidentiality and
# integrity primitives, it attacks nothing. Full declaration: SCOPE-STATEMENT.md.
"""KEY-MATERIAL-REAL (BUILD) — real cryptography under the whole key family, behind unchanged
interfaces, as an OPTIONAL EXTRA (owner's word 2026-09-08, board :3218).

Every probe is a regression test (the campaign method: a verification probe lands as a test), and
every one is written so it CAN FAIL — a check that cannot fail is not a check. The battery is
MODE-AWARE: it runs in BOTH the whole-ledger runs the plan requires — with the vetted library present
(the real, tagged path) and absent (the estate as today, real operations refusing citing the absent
library). Each test branches on `crypto.real_available()`: present -> the real assertions; absent ->
the refusal is asserted, so the module is green in both runs (A9's 'both green').

  A1  TestRealSignatures      an Ed25519 signature binds the signer; a DIFFERENT key or ALTERED bytes
                              fail verification (not an opaque-string equality) — RW-FORGE.
  A2  TestRealSeal            sealed content is unreadable from the ON-DISK bytes without the key; a
                              wrong key fails the AEAD tag (not a silent wrong-plaintext) — RW-SEAL,
                              EP-42 finding-6 answered (reads the on-disk bytes).
  A3  TestRealWrap            the per-piece key is X25519-wrapped to each reader; a reader opens, a
                              non-reader cannot; adding a reader wraps the SAME key once more (content
                              not re-encrypted).
  A4  TestSignerSignsNoRead   the signer (BESIDE the vault) produces a real signature with the SEALED
                              key AND exposes no read path — surface {seal, sign, compare_public}, no
                              get/reveal — RW-VAULT. (The vault routes through the seam AND is byte-frozen
                              at the rewired sha, owner :3966; no-reveal held by surface+source+seam guards.)
  A5  TestRealAttestation     the attestation seal is a real signature over the attested record; a
                              tampered surface fails verification — RW-FORGE.
  A6  TestEraSplit            a pre-real (untagged, modelled) value verifies under the modelled path;
                              a tagged value under the real path; the past is byte-untouched — RW-PAST.
  A7  TestNothingNew          no founding move: no new op/kind/check; real crypto is a code primitive.
  A8  TestWholeLedgerCoherence the new src module stays inside attestation coverage (the F4 twin) — the
                              in-module proxy for A8's whole-ledger-green-per-module run.
  A9  TestOptionalLibrary     with and without the library, both green, and the two absence-refusals
                              (bind a real key; verify a tagged value) PROVEN ABLE TO FIRE — absence
                              simulated at the crypto.py boundary, never by uninstalling — RW-DOWNGRADE.
"""

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel import crypto                                # noqa: E402  the ONE vetted-library boundary
from kernel import keys                                  # noqa: E402  the key family (era-split)
from kernel import attestation                           # noqa: E402  the attestation seal (era-split)
from kernel.vault import VaultStore                      # noqa: E402  the secrets vault (byte-frozen)
from kernel.signer import SigningKeyStore                # noqa: E402  the signing key store, BESIDE the vault
from kernel.opdefs import OP_CHECKS                      # noqa: E402  the closed check vocabulary
from bridge import seal                                  # noqa: E402  content-at-rest (era-split)


def _new_vault():
    return VaultStore(os.path.join(tempfile.mkdtemp(), "vault"))


# THE SIGNING HALF, BUILT BESIDE THE VAULT (KEY-MATERIAL-REAL RE-MINT 2, archi :3249). The vault does
# NOT gain a SIGN op — signing lives BESIDE the vault, not inside it (the vault is routed through the
# host seam AND byte-frozen at the rewired sha, owner :3966; its no-reveal closure is guarded by its
# surface + source census + the seam's no-read-act assertion, BESIDE the byte-freeze). The system signing
# key lives in a NEW SigningKeyStore (signer.py) BESIDE the
# vault, under the vault's own discipline (seal-at-ceremony, sign→a real Ed25519 signature, NO read
# path, surface EXACTLY {seal, sign, compare_public}). A1/A4/A5 exercise the signer directly; the
# earlier in-vault HOLD is DISCHARGED by the re-scope, without touching the vault.
class _Case(unittest.TestCase):
    def setUp(self):
        self.vault = _new_vault()
        self.signer = SigningKeyStore()


# ============================================================================================
# A1 — REAL SIGNATURES BIND (Ed25519, real — not an opaque-string equality; RW-FORGE)
# ============================================================================================

class TestRealSignatures(_Case):

    def test_a1_real_signature_binds_and_a_forgery_fails(self):
        if not crypto.real_available():
            # ABSENT: the real store-countersignature REFUSES rather than faking a signature.
            seed_home = self.signer.seal(b"\x00" * 32)
            with self.assertRaises(crypto.LibraryAbsent):
                keys.countersign({"seq": 1, "record_time": "t"}, seed_home, signer=self.signer)
            return
        seed = crypto.new_signing_seed()
        custody = self.signer.seal(seed)
        pub = crypto.public_from_seed(seed)                            # the published public half
        record = {"seq": 7, "record_time": "2026-09-08T00:00:00Z"}
        mark = keys.countersign(record, custody, signer=self.signer)   # a REAL signature, BY THE SIGNER
        self.assertTrue(crypto.is_real_value(mark))                    # tagged, not the modelled dict
        self.assertTrue(keys.verify_countersign(mark, record, custody, public_key=pub))
        # the signer confirms its own public half (a bool) without ever emitting the key
        self.assertTrue(self.signer.compare_public(custody, pub))
        # ALTERED bytes fail — the signature binds THIS record's recording fact
        self.assertFalse(keys.verify_countersign(mark, {"seq": 8, "record_time": "x"}, custody, public_key=pub))
        # a DIFFERENT key fails — the signature binds the signer
        other_pub = crypto.public_from_seed(crypto.new_signing_seed())
        self.assertFalse(keys.verify_countersign(mark, record, custody, public_key=other_pub))
        # the primitive itself: verify true on the exact bytes, false on a one-byte change
        sig = crypto.sign_with_seed(seed, b"exactly these bytes")
        self.assertTrue(crypto.verify(pub, sig, b"exactly these bytes"))
        self.assertFalse(crypto.verify(pub, sig, b"exactly these byteS"))


# ============================================================================================
# A2 — SEALED CONTENT UNREADABLE WITHOUT THE KEY, ON DISK (RW-SEAL; EP-42 finding-6)
# ============================================================================================

class TestRealSeal(unittest.TestCase):

    def test_a2_sealed_content_is_unreadable_from_disk_without_the_key(self):
        if not crypto.real_available():
            with self.assertRaises(crypto.LibraryAbsent):
                crypto.aead_seal(b"x", "k")
            return
        secret = "testsecret:alice:v1"
        sign = keys.sign_public_from_secret(secret)
        content = b"the confidential minutes of the meeting"
        piece = seal.seal(content, [sign], "blob:sha256:the-clear-address")
        self.assertEqual(piece.get(seal.ALG), crypto.TAG_AEAD)         # a real AEAD piece
        # ON DISK: write the sealed bytes to a real file and read them back (not an in-memory field)
        blob = os.path.join(tempfile.mkdtemp(), "sealed.blob")
        with open(blob, "wb") as fh:
            fh.write(piece[seal.SEALED])
        with open(blob, "rb") as fh:
            on_disk = fh.read()
        self.assertNotEqual(on_disk, content)                          # ciphertext, not the plaintext
        self.assertNotIn(content, on_disk)                             # no plaintext in the sealed bytes
        self.assertNotIn(b"minutes", on_disk)                          # not even a fragment
        # a WRONG key fails the AEAD tag — a refusal, never a silent wrong-plaintext
        with self.assertRaises(Exception):
            crypto.aead_open(on_disk, "the-wrong-piece-key", aad="blob:sha256:the-clear-address")
        # only the reader's own secret opens it
        self.assertEqual(seal.open_content(piece, sign, secret), content)


# ============================================================================================
# A3 — REAL WRAP; ADD A READER WRAPS ONCE MORE (X25519 sealed box; content not re-encrypted)
# ============================================================================================

class TestRealWrap(unittest.TestCase):

    def test_a3_wrapped_to_readers_add_reader_wraps_once_more(self):
        if not crypto.real_available():
            with self.assertRaises(crypto.LibraryAbsent):
                crypto.box_wrap(b"k", "x25519:00")
            return
        alice_s, bob_s, mallory_s = "s:alice", "s:bob", "s:mallory"
        alice = keys.sign_public_from_secret(alice_s)
        bob = keys.sign_public_from_secret(bob_s)
        mallory = keys.sign_public_from_secret(mallory_s)              # keyed, wrapped to nothing
        content = b"wrapped to the readers only"
        piece = seal.seal(content, [alice], "blob:loc")
        # the wrap addresses alice's PUBLIC open key, and the wrapped value is a real sealed box
        self.assertEqual(set(piece[seal.WRAP]), {keys.open_public_key(alice)})
        self.assertTrue(next(iter(piece[seal.WRAP].values())).startswith(crypto.TAG_WRAP + ":"))
        # a reader opens; a non-reader cannot
        self.assertEqual(seal.open_content(piece, alice, alice_s), content)
        with self.assertRaises(seal.NotAReader):
            seal.open_content(piece, mallory, mallory_s)
        # add bob: wrap the SAME piece key once more, content byte-identical (not re-encrypted)
        piece_key = seal.unwrap_key(piece, alice_s)
        piece2 = seal.add_reader(piece, bob, piece_key)
        self.assertEqual(len(piece2[seal.WRAP]), 2)
        self.assertEqual(piece2[seal.SEALED], piece[seal.SEALED])      # RW5: content not re-encrypted
        self.assertEqual(piece2[seal.OUTER], piece[seal.OUTER])        # the outer fingerprint is unmoved
        self.assertEqual(seal.open_content(piece2, bob, bob_s), content)     # bob opens now
        self.assertEqual(seal.open_content(piece2, alice, alice_s), content)  # alice still opens


# ============================================================================================
# A4 — THE SIGNER SIGNS BUT NEVER READS; THE VAULT IS BYTE-IDENTICAL (RW-VAULT; archi :3249)
# ============================================================================================

class TestSignerSignsNoRead(_Case):

    def test_a4_signer_signs_with_the_sealed_key_and_exposes_no_read_path(self):
        # SURFACE PIN — the signer's public surface is EXACTLY {seal, sign, compare_public}: a `sign`,
        # a `compare_public`, and NO getter. The no-read-path law holds in BOTH eras.
        for banned in ("get", "read", "reveal", "open", "peek", "export", "dump", "value", "load"):
            self.assertFalse(hasattr(self.signer, banned),
                             "the signer must expose no %r read path — no method returns the seed" % banned)
        surface = {n for n in dir(self.signer) if not n.startswith("_") and callable(getattr(self.signer, n))}
        self.assertEqual(surface, {"seal", "sign", "compare_public"})
        # SOURCE-GREP no-read guard — the closure is a property of the SOURCE (the EP-19 assertion,
        # carried to the signer): signer.py holds the seed in memory and never reads it back out.
        with open(os.path.join(os.path.dirname(__file__), "..", "src", "kernel", "signer.py")) as fh:
            signer_src = fh.read()
        for reader in ("read_bytes", "read_text", ".read(", "def get", "def read", "def reveal", "def open"):
            self.assertNotIn(reader, signer_src, "signer.py must not contain %r — no read path" % reader)
        # The signer is BESIDE the vault (:3249): the signer source census above guards its no-read
        # property. THE VAULT IS BYTE-FROZEN AT THE REWIRED SHA (owner :3966) — the byte-freeze was set
        # aside for the C7-P2 rewiring (:3930/:3952 routed vault.py through host_seam) and is now PUT
        # BACK ON at the rewired contents, BESIDE the vault's surface + source census + seam no-read-act
        # (test_c7_p2_seam). Signing went BESIDE the vault, so vault.py holds seal/compare only.
        # RE-POINTED (MAINT-VAULT-HASH-ONLY; owner scan :4435, archi :4437): seal now stores NOTHING
        # (no write-once put, no _path); the pin guards the property (the vault's exact bytes), so it
        # moves with the owner-authorized code to the hash-only vault's sha. The signer stays BESIDE it.
        with open(os.path.join(os.path.dirname(__file__), "..", "src", "kernel", "vault.py"), "rb") as fh:
            vdigest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(vdigest, "6a82f449865f5464ef70b6d39db2fee568ba1cae43b5b380e21cc4d5ad09f767",
                         "vault.py bytes changed — the vault stays byte-frozen at the hash-only sha; the signer is BESIDE it")
        if not crypto.real_available():
            with self.assertRaises(crypto.LibraryAbsent):
                self.signer.sign(self.signer.seal(b"\x00" * 32), b"m")
            return
        seed = crypto.new_signing_seed()
        custody = self.signer.seal(seed)
        sig = self.signer.sign(custody, b"attest exactly these bytes")  # signed BY THE SIGNER, beside the vault
        self.assertTrue(crypto.is_real_value(sig))
        self.assertTrue(crypto.verify(crypto.public_from_seed(seed), sig, b"attest exactly these bytes"))
        # compare_public confirms the public half (a bool) and REJECTS a different key — never emits it
        self.assertTrue(self.signer.compare_public(custody, crypto.public_from_seed(seed)))
        self.assertFalse(self.signer.compare_public(custody, crypto.public_from_seed(crypto.new_signing_seed())))
        # NOTHING the signer returns is the secret seed — signing did not read the key out
        self.assertNotIn(seed.hex(), sig)


# ============================================================================================
# A5 — REAL ATTESTATION (a real signature over the attested record; a tamper fails)
# ============================================================================================

class TestRealAttestation(_Case):

    def test_a5_attestation_seal_is_a_real_signature_over_the_attested_record(self):
        attested = attestation.attested_set()                          # the running engine's set
        if not crypto.real_available():
            with self.assertRaises(crypto.LibraryAbsent):
                attestation.attestation_seal(attested, self.signer, self.signer.seal(b"\x00" * 32))
            return
        seed = crypto.new_signing_seed()
        custody = self.signer.seal(seed)
        pub = crypto.public_from_seed(seed)
        the_seal = attestation.attestation_seal(attested, self.signer, custody)
        self.assertTrue(crypto.is_real_value(the_seal))
        self.assertTrue(attestation.verify_attestation_seal(attested, the_seal, pub))
        # a TAMPERED attested surface (any member changed -> a changed set-digest) fails
        tampered = dict(attested)
        tampered["set_digest"] = "sha256:" + "0" * 64
        self.assertFalse(attestation.verify_attestation_seal(tampered, the_seal, pub))
        # a seal under a DIFFERENT key fails
        other_pub = crypto.public_from_seed(crypto.new_signing_seed())
        self.assertFalse(attestation.verify_attestation_seal(attested, the_seal, other_pub))


# ============================================================================================
# A6 — THE ERA-SPLIT: THE PAST IS BYTE-UNTOUCHED (RW-PAST)
# ============================================================================================

class TestEraSplit(_Case):

    def test_a6_a_pre_real_countersign_verifies_under_the_modelled_path_in_either_era(self):
        record = {"seq": 1, "record_time": "t"}
        h = keys.seal_system_key(self.vault, "sysval")
        mark = keys.countersign(record, h)                             # NO vault -> the modelled dict
        self.assertIsInstance(mark, dict)
        self.assertFalse(crypto.is_real_value(mark))                   # untagged -> a pre-real value
        self.assertTrue(keys.verify_countersign(mark, record, h))      # verifies under the modelled path
        self.assertFalse(keys.verify_countersign(mark, {"seq": 9, "record_time": "x"}, h))  # can fail

    def test_a6_a_pre_real_piece_routes_to_the_modelled_path_regardless_of_the_library(self):
        # the era-split dispatches on the PIECE's OWN era, never a global mode: a piece with no ALG
        # marker (the modelled era) opens under the XOR path whether or not the library is present now.
        piece_key = "feedface"
        content = b"a pre-real piece from before the library"
        sealed = seal.seal_bytes(content, piece_key)                   # the modelled primitive, still here
        modelled_piece = {seal.LOCATION: "loc", seal.SEALED: sealed, seal.WRAP: {},
                          seal.OUTER: seal.outer_fingerprint(sealed),
                          seal.INNER: seal.inner_fingerprint(content)}
        self.assertNotIn(seal.ALG, modelled_piece)                     # no era marker -> pre-real
        self.assertFalse(seal._is_real_piece(modelled_piece))          # routes to the modelled path
        self.assertEqual(seal.seal_bytes(modelled_piece[seal.SEALED], piece_key), content)  # XOR recovers
        self.assertTrue(seal.verify_outer(modelled_piece))             # the outer check still holds

    def test_a6_a_real_piece_carries_its_era_marker_when_the_library_is_present(self):
        if not crypto.real_available():
            self.skipTest("no library — the real era is proven in the present run")
        sign = keys.sign_public_from_secret("s")
        piece = seal.seal(b"x", [sign], "loc")
        self.assertEqual(piece.get(seal.ALG), crypto.TAG_AEAD)         # tagged -> the real era
        self.assertTrue(seal._is_real_piece(piece))


# ============================================================================================
# A7 — NO FOUNDING MOVE (no new op/kind/check; real crypto is a code primitive)
# ============================================================================================

class TestNothingNew(unittest.TestCase):

    def test_a7_no_new_check_kind(self):
        self.assertEqual(len(OP_CHECKS), 19)                           # the closed check vocabulary, unmoved
        for planted in ("ed25519", "aead", "wrap", "crypto", "signature"):
            self.assertNotIn(planted, OP_CHECKS)                       # no crypto-specific check minted

    def test_a7_the_founding_pack_carries_no_crypto_vocabulary(self):
        # real crypto is a CODE primitive: the founding pack mints no op, kind or check for it. A
        # plant (a crypto-named founding op) would red this.
        import json
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(repo, "src", "founding", "founding-pack.json"), encoding="utf-8") as fh:
            pack = json.load(fh)
        op_names = {r["payload"]["name"] for s in pack["steps"] for r in s["records"]
                    if r.get("action") == "CREATE-OP"}
        for name in op_names:
            self.assertNotIn("crypto", name.lower())
            self.assertNotIn("ed25519", name.lower())
            self.assertNotIn("key-material", name.lower())
        self.assertIn("OPEN-CONTENT", op_names)                        # §A64: the membership test discriminates

    def test_a7_crypto_module_declares_no_founding_vocabulary(self):
        # the boundary module exposes primitives and tags, never a founding op/kind/check constant.
        self.assertFalse(hasattr(crypto, "OP_CHECKS"))
        self.assertFalse(hasattr(crypto, "CREATE_OP"))


# ============================================================================================
# A8 — WHOLE-LEDGER COHERENCE (the in-module proxy for the per-module whole-ledger run)
# ============================================================================================

class TestWholeLedgerCoherence(unittest.TestCase):

    def test_a8_the_new_boundary_module_is_inside_attestation_coverage(self):
        # the NEW src/kernel/crypto.py AND src/kernel/signer.py are governance-bearing surfaces the law
        # guard greps, so the F4 twin requires BOTH inside the attested set — else either would be an
        # uncovered surface (RW1).
        self.assertIn("kernel/crypto.py", attestation.ATTESTED_MEMBERS)
        self.assertIn("kernel/signer.py", attestation.ATTESTED_MEMBERS)
        self.assertEqual(attestation.twin_uncovered(), [])             # no governance surface outside coverage
        self.assertEqual(attestation.ATTESTED_MEMBERS,
                         tuple(sorted(attestation.ATTESTED_MEMBERS)))  # the list stays sorted
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88)     # 88 since C7 P3b-6a's +1 net.c (the virtio-net driver, archi :4250); 87 since C7 P3b-4b's +2 serve files (serve.c/serve.h, archi :4089); 85 since C7 P3b-4a's enclosure add (+6 src/body files enclosure.S/enclosure.c/enclosure.h/sha256.c/worker.S/worker.ld, archi :4085); 79 since C7 P3b-3's clock/interrupt/entropy add (+6 src/body files clkcheck.c/clock.c/clock.h/entropy.c/idt.c/isr.S, archi :4049); 73 since C7 P3b-2's disk add (+5 src/body files ata.c/bodyfs.c/disk.h/diskcheck.c/mkdisk.py, archi :4019); 68 since C7 P3b-1's first-merged-body add (+11 src/body files: the memory C + boot.S + linker.ld + the generated rows-digest header + the derive-from-rows generator .py + build.sh; §9 mechanism 1 ONE ATTESTED LIST, archi :4009). 57 since C7 P7a's interpreter-hosting layer joined (design/54 §7 P7; +2: hosting/__init__.py, hosting/interpreter_host.py); 55 since C7 P2-SEAM-AS-A-CONTRACT's bridge/host_seam.py joined (the effect-seam performer interface, design/54 §7 P2, §5 count-pin companion driven at dispatch); 54 since P12-CONSTITUTION-SURVIVES-BUILD's bridge/reconstruct.py joined (C6 P12, B6/I15; the §5 count-pin companion driven at the fence amendment, mgr :3631); 53 since EP-52-BUILD's subsystems/filter.py joined (FIREWALL-IN-THE-RECORD, C5 P7, §5 count-pin companion driven at dispatch); 52 since EP-49A-BUILD's kernel/border.py joined (THE BORDER: THE DOOR, the campaign-5 crux; §A57 name-and-count sweep companion driven at dispatch, disclosed to mgr as a hit beyond the EP-49A fence's enumerated pin files — the same convergence test_ep40/test_ep46 carry). 51: this unit's kernel/signer.py add (49->50) + EP-48-BUILD's subsystems/sockets.py, which joined the attested set CONCURRENTLY during this build (SOCKET-GRANTS founding mover). :3255 by-name widen for the concurrent companion; the count-pin states the true set size, whichever unit added what


# ============================================================================================
# A9 — WITH AND WITHOUT THE LIBRARY, BOTH GREEN, AND THE REFUSAL FIRES (RW-DOWNGRADE)
# ============================================================================================

class TestOptionalLibrary(_Case):

    def _force_absent(self):
        os.environ[crypto._FORCE_ABSENT_ENV] = "1"

    def _restore(self, prior):
        if prior is None:
            os.environ.pop(crypto._FORCE_ABSENT_ENV, None)
        else:
            os.environ[crypto._FORCE_ABSENT_ENV] = prior

    def test_a9_absence_refuses_binding_a_real_key_never_falls_back(self):
        # absence SIMULATED at the boundary (never by uninstalling): a real-key bind REFUSES, and the
        # refusal is PROVEN ABLE TO FIRE — a silent fall-back to the modelled path would make
        # assertRaises fail (red). This assertRaises IS the plant-detector the plan requires.
        prior = os.environ.get(crypto._FORCE_ABSENT_ENV)
        self._force_absent()
        try:
            self.assertFalse(crypto.real_available())
            with self.assertRaises(crypto.LibraryAbsent):
                crypto.sign_public_from_secret("s")                    # bind a real key -> REFUSE
            # keys.sign_public_from_secret returns the MODELLED value, not a faked real one
            self.assertFalse(crypto.is_real_value(keys.sign_public_from_secret("s")))
        finally:
            self._restore(prior)

    def test_a9_absence_refuses_verifying_a_tagged_value_never_a_modelled_pass(self):
        prior = os.environ.get(crypto._FORCE_ABSENT_ENV)
        self._force_absent()
        try:
            self.assertFalse(crypto.real_available())
            with self.assertRaises(crypto.LibraryAbsent):
                crypto.verify("ed25519:" + "00" * 32, "ed25519-sig:" + "00" * 64, b"m")
            # a tagged countersignature under absence refuses (no modelled substitute for a real mark)
            with self.assertRaises(crypto.LibraryAbsent):
                keys.verify_countersign("ed25519-sig:" + "00" * 64, {"seq": 1, "record_time": "t"},
                                        "sha256:x", public_key="ed25519:" + "00" * 32)
        finally:
            self._restore(prior)

    def test_a9_presence_turns_the_real_tagged_path_on(self):
        # where the library is ACTUALLY installed (independent of the force-absent hook), presence
        # makes the tagged path real end to end. Skipped where genuinely absent (the current baseline).
        if not crypto._IMPORTED:
            self.skipTest("the vetted library is not installed in this interpreter (the baseline)")
        prior = os.environ.get(crypto._FORCE_ABSENT_ENV)
        self._restore(None) if prior is None else os.environ.pop(crypto._FORCE_ABSENT_ENV, None)
        try:
            self.assertTrue(crypto.real_available())
            # binding a real key produces a TAGGED value; the id-card key family is real end to end
            self.assertTrue(crypto.is_real_value(keys.sign_public_from_secret("s")))
            self.assertTrue(crypto.is_real_value(keys.open_public_key(keys.sign_public_from_secret("s"))))
            # a real signature round-trips (the primitive; the signer is the real producer, A4)
            seed = crypto.new_signing_seed()
            pub = crypto.public_from_seed(seed)
            sig = crypto.sign_with_seed(seed, b"m")
            self.assertTrue(crypto.verify(pub, sig, b"m"))
            self.assertFalse(crypto.verify(pub, sig, b"M"))
        finally:
            self._restore(prior)


if __name__ == "__main__":
    unittest.main()
