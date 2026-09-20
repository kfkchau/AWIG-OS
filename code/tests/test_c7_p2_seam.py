# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (the host seam, a performer, a stub performer, a portability label, the guest-gated socket) as in the
# seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability — this DRIVES the acceptance of C7
# P2 (the closed act set declared as one interface; the sites routed byte-for-byte; the stub; the
# census; the label ratchet), each with its own ability to fail. Full declaration: SCOPE-STATEMENT.md.
"""C7 P2 — THE SEAM AS A CONTRACT — acceptance (design/54 §7 P2; §3 B3/B8; §5 L1/L6/L13).

A1  the closed act set declared as one interface; a planted twelfth act kind is refused (the set closed).
A2  the ~60 sites routed byte-for-byte; a planted behaviour change (a performer that mis-performs) reds.
A3  the stub performer; the estate runs green above it (store/blobs/vault); the stub-green set is NAMED;
    an act the stub does not perform (socket, body-read, pack-read) is REFUSED, never silently no-op'd.
A4  the undeclared-crossing census reds on a planted direct host call; green on the routed core.
A5  the label ratchet: every performer host act carries an L6 label; a planted unlabelled crossing reds.
"""

import ast
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir, "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from bridge import host_seam as hs                                        # noqa: E402
from kernel import store, blobs, vault, crypto                           # noqa: E402
from tools.conformance import host_crossing_census as census             # noqa: E402


# ==================================================================================================
# A1 — THE CLOSED ACT SET DECLARED AS ONE INTERFACE
# ==================================================================================================

class TestA1ClosedActSet(unittest.TestCase):

    def test_the_act_set_is_the_declared_closed_twelve_kinds(self):
        # The 11 kinds P1 enumerated (§Q-A) + the C7 P7a `memory` growth (11 -> 12, archi countersign):
        # the interpreter-hosting layer wires CPython's memory need down to the declared twelfth act.
        self.assertEqual(len(hs.ACT_KINDS), 12)
        for kind in ("record-pen", "atomic-write-once", "remove", "single-writer-lock",
                     "recording-clock", "commit-window", "entropy", "concurrency",
                     "network-socket", "body-read", "founding-pack-read", "memory"):
            self.assertIn(kind, hs.ACT_KINDS)

    def test_every_declared_act_names_a_closed_kind_and_a_label(self):
        for method, (kind, label) in hs.HostSeam.ACTS.items():
            self.assertIn(kind, hs.ACT_KINDS, "%s names an undeclared kind %r" % (method, kind))
            self.assertIn(label, hs.LABELS, "%s carries no valid label" % method)

    def test_a_thirteenth_act_kind_is_refused_the_set_is_closed(self):
        # THE CHECK CAN FAIL, and it MOVED ONCE with the declared growth: `memory` is now the
        # legitimate TWELFTH kind (C7 P7a; the interpreter-hosting layer's once-only widen). A
        # THIRTEENTH kind outside the closed set still cannot be declared without a further ruling —
        # the control keeps its ability to fail (design/54 §5; archi precision a).
        self.assertIn("memory", hs.ACT_KINDS)                  # the declared twelfth is NOT refused
        with self.assertRaises(hs.HostSeamError):
            hs.declare_act("thirteenth-kind", hs.PORTABLE)     # a thirteenth still is
        # a bad portability label is refused too (L6 is a closed set)
        with self.assertRaises(hs.HostSeamError):
            hs.declare_act("entropy", "not-a-label")

    def test_the_least_portable_and_guest_gated_sites_are_labelled_as_such(self):
        # B8/L6: the host-PID lock is the least-portable crossing; the socket is guest-gated.
        self.assertEqual(hs.HostSeam.ACTS["pid_alive"][1], hs.LEAST_PORTABLE)
        self.assertEqual(hs.HostSeam.ACTS["getpid"][1], hs.LEAST_PORTABLE)
        self.assertEqual(hs.HostSeam.ACTS["open_stream_socket"][1], hs.GUEST_GATED)

    def test_the_seam_declares_no_act_that_returns_a_sealed_value(self):
        # VERIFY, NEVER REVEAL (design/31 J8; archi :3930/:3952). Since MAINT-VAULT-HASH-ONLY (owner
        # scan :4435) the vault's seal stores NOTHING (no write-once put, no existence check); its one
        # remaining routed act is its home-dir creation. The seam declares NO act that returns a stored
        # / sealed value: no vault-get, no vault-read, no reveal. The closed ACT_KINDS carries no such
        # kind, and no performer method reads a sealed value back. This is the seam half of the no-reveal
        # guard of record (it JOINS the source census that stands beside the vault's byte-freeze, :3952).
        for banned in ("vault-get", "vault-read", "reveal", "secret-get", "unseal", "vault-reveal"):
            self.assertNotIn(banned, hs.ACT_KINDS,
                             "the seam declares %r — an act that returns a sealed value (forbidden)" % banned)
        self.assertNotIn("vault_get", hs.HostSeam.ACTS)
        self.assertNotIn("reveal", hs.HostSeam.ACTS)
        # THE CHECK CAN FAIL: a PLANTED vault-read act kind is refused by the closed set (declare_act).
        with self.assertRaises(hs.HostSeamError):
            hs.declare_act("vault-read", hs.PORTABLE)


# ==================================================================================================
# A2 — THE SITES ROUTED, RUNTIME BYTE-FOR-BYTE
# ==================================================================================================

class TestA2RoutedByteForByte(unittest.TestCase):

    def test_the_real_performer_makes_the_identical_host_call(self):
        # entropy: RealHost.urandom is os.urandom (right width, non-deterministic)
        h = hs.RealHost()
        self.assertEqual(len(h.urandom(24)), 24)
        self.assertNotEqual(h.urandom(16), h.urandom(16))
        # the recording clock is a real UTC ISO-8601 string
        iso = h.recorded_now_iso()
        self.assertRegex(iso, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
        self.assertTrue(iso.endswith("+00:00") or iso.endswith("Z"))

    def test_a_routed_round_trip_is_byte_identical_on_the_real_host(self):
        d = tempfile.mkdtemp()
        b = blobs.BlobStore(os.path.join(d, "blobs"))
        payload = b"\x00\x01\xff exact bytes \x7f"
        h = b.put(payload)
        self.assertEqual(b.get(h), payload, "the routed atomic-write-once did not preserve the bytes")

    def test_a_planted_behaviour_change_reds_a_round_trip(self):
        # THE CHECK CAN FAIL: a performer whose write-once mis-performs (writes wrong bytes) is caught
        # by the store's own round-trip — routing that changed WHAT the act does would not survive here.
        class _BadHost(hs.RealHost):
            def write_file_durably(self, tmp, final, data, mode=0o644):
                super().write_file_durably(tmp, final, b"CORRUPTED", mode)   # not the bytes it was given
        d = tempfile.mkdtemp()
        with hs.using(_BadHost()):
            b = blobs.BlobStore(os.path.join(d, "blobs"))
            b.put(b"the real payload")          # writes CORRUPTED under name = hash(payload)
            # the SECOND put hits the dedup path, which VERIFIES the stored bytes hash to the name —
            # a routed site that did not perform what the direct call did is caught here, loud.
            with self.assertRaises(ValueError):
                b.put(b"the real payload")


# ==================================================================================================
# A3 — THE STUB PERFORMER; THE ESTATE GREEN ABOVE IT
# ==================================================================================================

# THE STUB-GREEN MODULE SET (architect precision, board): the modules that run green ON THE STUB, and
# the modules that CANNOT — each named with the specific host act the memory stub does not perform.
STUB_GREEN = ("kernel/store.py (record round-trip)", "kernel/blobs.py (put/get)",
              "kernel/vault.py (seal stores nothing / compare — the vault's one routed act is its "
              "home-dir creation, :3952; MAINT-VAULT-HASH-ONLY)",
              "kernel/crypto.py (entropy — real under the stub)",
              "kernel/commit.py (window + concurrency — real under the stub)")
STUB_CANNOT = {
    "kernel/attestation.py": "body-read (open_read_binary / walk of the on-disk S-plane)",
    "src/founding/install.py": "founding-pack-read (open_read_text of founding-pack.json)",
    "bridge/kernel_port.py": "network-socket (open_stream_socket — a real guest-gated socket)",
}
# kernel/vault.py is ROUTED through the seam like every other core file (:3930/:3952). Since
# MAINT-VAULT-HASH-ONLY (owner scan :4435) seal stores NOTHING (no write-once put, no existence check);
# the vault's one remaining routed act is its home-dir creation, so it stays host-clean above the stub
# and is NOT a declared census exception. The no-reveal property is guarded by the vault's own surface
# (no get/read/reveal op), the source census, and the seam's no-read-act assertion — beside the vault
# byte-freeze, re-pointed to the hash-only sha (MAINT-VAULT-HASH-ONLY); the property-guards stay.


class TestA3StubGreen(unittest.TestCase):

    def test_the_record_round_trip_runs_green_above_the_stub(self):
        with hs.using(hs.StubHost()):
            s = store.EventStore("/virtual/log.jsonl")
            s._append({"actor": "owner", "action": "A", "object": "o"})
            s._append({"actor": "owner", "action": "B", "object": "o2"})
            reread = store.EventStore("/virtual/log.jsonl")
            self.assertEqual(len(reread.all()), 2, "the record round-trip did not survive the stub")
            s.close(); reread.close()
        self.assertIsInstance(hs.host(), hs.RealHost, "the performer was not restored after the swap")

    def test_blobs_run_green_above_the_stub(self):
        # The blob store's atomic write-once / get / has run green on the memory stub.
        with hs.using(hs.StubHost()):
            b = blobs.BlobStore("/virtual/blobs")
            h = b.put(b"stub-payload")
            self.assertEqual(b.get(h), b"stub-payload")
            self.assertTrue(b.has(h))

    def test_the_vault_runs_green_above_the_stub(self):
        # The vault's one routed act — its home-dir creation — goes through the seam (:3952), so it
        # constructs green on the memory stub; seal stores NOTHING (MAINT-VAULT-HASH-ONLY) and compare
        # reads no stored value. The vault is not a declared exception.
        with hs.using(hs.StubHost()):
            v = vault.VaultStore("/virtual/vault")
            h = v.seal(b"a secret that crosses once")
            self.assertTrue(h.startswith("sha256:"))
            # compare answers a MATCH / NO-MATCH by hash — there is no stored value to read back out.
            self.assertTrue(v.compare(b"a secret that crosses once", h))
            self.assertFalse(v.compare(b"a different candidate", h))
            # sealing the same value twice is idempotent — seal is a pure hash of the value, storing nothing.
            self.assertEqual(v.seal(b"a secret that crosses once"), h)
        self.assertIsInstance(hs.host(), hs.RealHost, "the performer was not restored after the swap")

    def test_the_stub_refuses_acts_it_does_not_perform_never_a_silent_noop(self):
        # A memory host performs no real socket, no on-disk body read, no pack read — it REFUSES rather
        # than pretend (a silent no-op would hide a leak). This is the mechanical proof of the contract.
        stub = hs.StubHost()
        with self.assertRaises(hs.HostSeamError):
            stub.open_stream_socket(2)                      # the guest-gated network act
        with self.assertRaises(hs.HostSeamError):
            stub.open_read_binary("/real/source.py")        # the body-read act
        with self.assertRaises(hs.HostSeamError):
            stub.open_read_text("/real/founding-pack.json")  # the founding-pack-read act

    def test_a_performer_missing_a_declared_act_refuses_it_not_silently(self):
        # A planted crossing the performer does not declare is not silently performed — the base
        # HostSeam refuses every act, so a partially-built performer fails loud.
        bare = hs.HostSeam()
        with self.assertRaises(hs.HostSeamError):
            bare.urandom(4)

    def test_the_stub_green_set_is_named_and_the_non_stub_modules_carry_their_blocking_act(self):
        # The stub-green set is a DELIVERABLE, not an assumption; the modules that cannot run on the
        # stub are named WITH the act that blocks them (never silently skipped).
        self.assertTrue(STUB_GREEN)
        for module, act in STUB_CANNOT.items():
            self.assertTrue(act, "%s is not stub-green but names no blocking act" % module)


# ==================================================================================================
# A4 — THE UNDECLARED-CROSSING CENSUS (able to fail)
# ==================================================================================================

class TestA4Census(unittest.TestCase):

    def test_the_routed_core_is_host_clean(self):
        self.assertEqual(census.undeclared_crossings(), {},
                         "a governance-core module still crosses to the host directly")
        v = census.verdict()
        self.assertTrue(v["clean"], "the census is not clean on the routed tree")
        # The vault is now ROUTED through the seam like every other core file (:3930/:3952) — no longer a
        # declared exception. No owner-law crossing exception remains; the census carries none, and the
        # vault is not an undeclared crossing (its disk places go through host()). The census stays able
        # to fail on ANY other undeclared crossing (test_a_planted_direct_os_call_...).
        self.assertEqual(v["declared_exceptions"], {},
                         "a declared crossing exception remains — the vault is routed, none should")
        self.assertNotIn("kernel/vault.py", v["undeclared_crossings"])

    def test_a_planted_direct_os_call_in_a_core_module_reds_the_census(self):
        # THE CHECK CAN FAIL: build a temp src tree with a planted direct os call in the core.
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "kernel"))
        with open(os.path.join(tmp, "kernel", "planted.py"), "w") as f:
            f.write("import os\ndef leak():\n    return os.open('/tmp/x', 0)\n")
        bad = census.undeclared_crossings(tmp)
        self.assertIn("kernel/planted.py", bad, "the census did not red a planted direct os call")

    def test_a_planted_pathlib_crossing_in_the_core_reds_but_a_seam_call_does_not(self):
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "kernel"))
        # a direct pathlib crossing reds ...
        with open(os.path.join(tmp, "kernel", "direct.py"), "w") as f:
            f.write("from pathlib import Path\ndef r(p):\n    return Path(p).read_bytes()\n")
        # ... but a routed seam call (host().read_bytes) does NOT (its method name coincides only)
        with open(os.path.join(tmp, "kernel", "routed.py"), "w") as f:
            f.write("from bridge.host_seam import host\ndef r(p):\n    return host().read_bytes(p)\n")
        bad = census.undeclared_crossings(tmp)
        self.assertIn("kernel/direct.py", bad)
        self.assertNotIn("kernel/routed.py", bad,
                         "a routed host().read_bytes(...) was mis-read as a direct crossing")

    def test_observe_is_read_and_classified_below_its_own_seam_never_red(self):
        # The census READS observe/ (required) and classifies it below the observe seam — never red.
        below = census.declared_crossings()
        observe_files = [rel for rel in below if rel.startswith("observe/")]
        self.assertTrue(observe_files, "the census did not read+classify the observe seam")
        for rel in observe_files:
            self.assertNotIn(rel, census.undeclared_crossings())


# ==================================================================================================
# A5 — THE LABEL RATCHET (B8, L6)
# ==================================================================================================

class TestA5LabelRatchet(unittest.TestCase):

    def test_every_performer_host_act_carries_a_label(self):
        self.assertEqual(census.unlabelled_host_methods(), [],
                         "a performer host method carries no L6 portability label")

    def test_a_planted_unlabelled_crossing_below_the_seam_reds_the_label_census(self):
        # THE CHECK CAN FAIL: a performer that adds a host method NOT declared in ACTS is unlabelled.
        class _LeakyHost(hs.RealHost):
            def sneak_read(self, path):          # a host crossing with no ACTS entry (no L6 label)
                return open(path, "rb")
        flagged = census.unlabelled_host_methods(_LeakyHost)
        self.assertIn("sneak_read", flagged,
                      "the label census did not red an unlabelled host method")


if __name__ == "__main__":
    unittest.main()
