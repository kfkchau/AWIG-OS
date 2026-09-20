# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (the interpreter-hosting layer, a POSIX/libc personality above a small kernel, an enclosed borrowed
# worker consumed sealed, the host seam's closed act set) as in the seL4/gVisor/Fuchsia literature.
# NON-GOAL: no offensive capability — this DRIVES the acceptance of C7 P7a (the layer that supplies
# what CPython needs to run above our own kernel), each check with its own ability to fail. Full
# declaration: SCOPE-STATEMENT.md.
"""C7 P7a — THE INTERPRETER-HOSTING LAYER — acceptance (design/54 §7 P7; design/47 §5 L5 / §2 I3).

A1  a real CPython runs the workload THROUGH the layer; the workload reaches the host ONLY through
    the layer (a raw crossing in the workload is seen), and the layer routes only through the seam.
A2  the surface is DRIVEN — a removed surface element breaks the run (the check can fail).
A3  the borrowed interpreter/libc are consumed SEALED and re-hash-checked at every waking; a planted
    byte change reds the waking.
A4  borrowed code is an ENCLOSED WORKER, never in the signed base; a planted opaque .py in the signed
    base reds the attestation member list (I3).
A5  ACT_KINDS grew ONLY by `memory`; the libc surface is atop the acts, not an act kind; a thirteenth
    act kind is refused.
A6  the attested surface stays coherent with the new layer (manifest == walk, nothing uncovered).
"""

import ast
import inspect
import os
import shutil
import socket
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir, "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from bridge import host_seam as hs                                              # noqa: E402
from hosting.interpreter_host import (                                          # noqa: E402
    InterpreterHost, SealedArtifact, SealSet, SealBrokenError, NeedNotSupplied)
from kernel import attestation as att                                          # noqa: E402
from tools.conformance import host_crossing_census as census                   # noqa: E402

# The eleven acts P2 declared; `memory` is the C7 P7a growth (the twelfth).
_ELEVEN = frozenset({
    "record-pen", "atomic-write-once", "remove", "single-writer-lock", "recording-clock",
    "commit-window", "entropy", "concurrency", "network-socket", "body-read", "founding-pack-read"})


# ==================================================================================================
# THE REPRESENTATIVE WORKLOAD — one function, run hermetically AND scanned AND run in the guest
# ==================================================================================================

def _workload(hl, tmp_path, final_path):
    """A representative CPython workload whose every HOST effect goes THROUGH the interpreter-hosting
    layer `hl` — never a raw os / open / socket. Exercises files, memory, the clock, entropy and the
    concurrency substrate, each accessed through the layer's driven `need(...)` surface so it bottoms
    out in a seam act. Executed hermetically here (StubHost beneath) AND in the guest (RealHost
    beneath); its SOURCE is AST-scanned to prove no direct host path (A1). Returns a results dict."""
    results = {}
    results["two_plus_two"] = 2 + 2                                  # a real interpreter is executing
    region = hl.need("memory").allocate(64)                         # memory need -> the memory act
    region[0:5] = b"hello"
    results["memory"] = bytes(region[0:5])
    results["wall_iso"] = hl.need("clock").now_iso()                # clock need -> recording-clock
    results["monotonic_is_float"] = isinstance(hl.need("clock").monotonic(), float)  # commit-window
    results["entropy_len"] = len(hl.need("entropy").random(16))     # entropy need -> the entropy act
    lock = hl.need("threads").new_lock()                            # threads need -> the concurrency act
    with lock:
        results["lock_held"] = True
    hl.need("files").write_once(tmp_path, final_path, b"through-the-layer")   # files -> write-once act
    results["file_roundtrip"] = hl.need("files").read_all_bytes(final_path)   # files -> record-pen act
    return results


def _direct_host_crossings(src_text):
    """Run the host-crossing census's own AST finder over a source string; return the direct host
    crossings (os/socket/time effects, bare open(), pathlib file methods on a non-host receiver)."""
    finder = census._CrossingFinder()
    finder.visit(ast.parse(src_text))
    return finder.crossings


# ==================================================================================================
# A1 — A REAL CPYTHON RUNS THE WORKLOAD THROUGH THE LAYER; NO HOST PATH EXCEPT THE LAYER
# ==================================================================================================

class TestA1RunsThroughTheLayer(unittest.TestCase):

    def test_a1_a_real_cpython_runs_the_workload_through_the_layer(self):
        self.assertEqual(sys.implementation.name, "cpython",
                         "the interpreter running this acceptance is real CPython")
        hl = InterpreterHost().wake()                       # empty seal set -> wakes clean
        with hs.using(hs.StubHost()):
            r = _workload(hl, "/virtual/note.tmp", "/virtual/note.txt")
        self.assertEqual(r["two_plus_two"], 4)
        self.assertEqual(r["memory"], b"hello")             # memory served through the layer
        self.assertEqual(r["entropy_len"], 16)
        self.assertTrue(r["monotonic_is_float"])
        self.assertTrue(r["lock_held"])
        self.assertEqual(r["file_roundtrip"], b"through-the-layer")   # file round-trip through the layer
        self.assertTrue(InterpreterHost.acts_used() <= hs.ACT_KINDS,
                        "a need bottomed out in an undeclared act")

    def test_a1_the_workload_reaches_the_host_only_through_the_layer(self):
        # The workload's source makes NO direct host crossing — every host touch is a layer call.
        self.assertEqual(_direct_host_crossings(inspect.getsource(_workload)), [],
                         "the workload reaches the host directly, not only through the layer")
        # and the layer module itself is CORE-zone host-clean (it routes every crossing via the seam)
        self.assertNotIn("hosting/interpreter_host.py", census.undeclared_crossings())
        # THE CHECK CAN FAIL: a workload with a raw open() shows a crossing.
        self.assertTrue(_direct_host_crossings("def w():\n    return open('/etc/passwd')\n"),
                        "the no-host-path probe cannot see a direct crossing")

    def test_a1_the_connection_need_routes_to_the_guest_gated_socket_act(self):
        # The connection need wires to the guest-gated network-socket act. Under the memory stub that
        # act is REFUSED (never a silent no-op) — the proof the wiring reaches the guest-gated act; in
        # the guest (RealHost) it opens a real socket (the guest evidence run).
        hl = InterpreterHost()
        with hs.using(hs.StubHost()):
            with self.assertRaises(hs.HostSeamError):
                hl.need("connection").open_socket(socket.AF_INET)


# ==================================================================================================
# A2 — THE SURFACE IS DRIVEN: A REMOVED ELEMENT BREAKS THE RUN
# ==================================================================================================

class TestA2DrivenSurface(unittest.TestCase):

    def test_a2_a_removed_surface_element_breaks_the_run(self):
        # PLANT: the memory surface removed from the layer. The workload that needs it now FAILS —
        # it cannot reach the host by any other path (A2 the check can fail).
        hl = InterpreterHost()
        hl.memory = None
        with hs.using(hs.StubHost()):
            with self.assertRaises(NeedNotSupplied):
                _workload(hl, "/virtual/note.tmp", "/virtual/note.txt")

    def test_a2_with_the_surface_present_the_same_workload_runs(self):
        # The only difference from the failing run above is the presence of the surface element.
        hl = InterpreterHost()
        with hs.using(hs.StubHost()):
            r = _workload(hl, "/virtual/note.tmp", "/virtual/note.txt")
        self.assertEqual(r["memory"], b"hello")


# ==================================================================================================
# A3 — THE INTERPRETER AND ITS LIBC ARE SEALED AND HASH-CHECKED AT EVERY WAKING
# ==================================================================================================

class TestA3SealedAndHashChecked(unittest.TestCase):

    def _sealed_artifact(self, body):
        d = tempfile.mkdtemp(prefix="p7a-seal-")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "cpython.sealed")
        with open(p, "wb") as f:
            f.write(body)
        return p

    def test_a3_a_sealed_artifact_verifies_and_a_planted_byte_change_reds(self):
        p = self._sealed_artifact(b"BORROWED-INTERPRETER-BYTES-v1")
        pin = SealedArtifact("cpython", p, None).digest()           # the pin, from the sealed bytes
        seals = SealSet([SealedArtifact("cpython", p, pin), SealedArtifact("libc", p, pin)])
        self.assertEqual(seals.wake(), {"cpython": True, "libc": True})   # clean at this waking
        with open(p, "ab") as f:                                    # PLANT a byte change in the seal
            f.write(b"X")
        with self.assertRaises(SealBrokenError):                    # the next waking reds (can fail)
            seals.wake()
        v = seals.check()
        self.assertFalse(v["cpython"]); self.assertFalse(v["libc"])

    def test_a3_the_interpreter_host_wakes_only_over_intact_seals(self):
        p = self._sealed_artifact(b"BORROWED-v1")
        pin = SealedArtifact("cpython", p, None).digest()
        hl = InterpreterHost(SealSet([SealedArtifact("cpython", p, pin)]))
        self.assertIs(hl.wake(), hl)                                # an intact seal -> the host wakes
        with open(p, "ab") as f:
            f.write(b"!")                                           # PLANT
        with self.assertRaises(SealBrokenError):
            hl.wake()                                               # a broken seal stops the waking

    def test_a3_an_absent_sealed_artifact_digests_to_none_never_crashes(self):
        seals = SealSet([SealedArtifact("cpython", "/no/such/sealed/artifact", "sha256:whatever")])
        self.assertEqual(seals.check(), {"cpython": False})         # absent -> a fact, not a crash


# ==================================================================================================
# A4 — BORROWED CODE IS AN ENCLOSED WORKER, NEVER IN THE SIGNED BASE (I3)
# ==================================================================================================

class TestA4NoOpaqueInSignedBase(unittest.TestCase):

    def test_a4_borrowed_artifacts_are_outside_the_signed_base(self):
        # The borrowed interpreter/libc are referenced by PATH + hash, never a signed member; and the
        # layer imports no borrowed interpreter/libc SOURCE (its imports are our own seam + canonical).
        for m in att.ATTESTED_MEMBERS:
            self.assertFalse(m.endswith("cpython.sealed") or m.endswith("libc.sealed"),
                             "a borrowed sealed artifact is in the signed member list")
        layer_src = inspect.getsource(sys.modules["hosting.interpreter_host"])
        self.assertNotIn("import cpython", layer_src)
        # our OWN layer code IS read whole and signed (a declared member).
        self.assertIn("hosting/interpreter_host.py", att.ATTESTED_MEMBERS)
        self.assertIn("hosting/__init__.py", att.ATTESTED_MEMBERS)

    def test_a4_a_planted_opaque_py_in_the_signed_base_reds_the_member_list(self):
        # I3: any .py inside the signed base must be a DECLARED signed member; borrowed/opaque code
        # cannot hide under src/. Plant an opaque .py in a temp src outside founding, absent from the
        # manifest -> the attestation twin flags it (the check can fail).
        tmp = tempfile.mkdtemp(prefix="p7a-opaque-")
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "hosting"))
        with open(os.path.join(tmp, "hosting", "borrowed_opaque.py"), "w") as f:
            f.write("# an opaque borrowed body smuggled into the signed base\n")
        self.assertEqual(att.twin_uncovered(src_dir=tmp), ["hosting/borrowed_opaque.py"])
        # the REAL tree has nothing uncovered — our hosting/*.py are declared members.
        self.assertEqual(att.twin_uncovered(), [])


# ==================================================================================================
# A5 — ACT_KINDS WIDENED ONLY BY MEMORY; THE LIBC SURFACE IS NOT AN ACT KIND
# ==================================================================================================

class TestA5PortableNotGeneralPurpose(unittest.TestCase):

    def test_a5_the_act_set_grew_only_by_memory(self):
        self.assertEqual(hs.ACT_KINDS, _ELEVEN | {"memory"})
        self.assertIn("memory", hs.ACT_KINDS)

    def test_a5_the_layer_bottoms_out_only_in_declared_acts_and_the_growth_is_memory(self):
        used = InterpreterHost.acts_used()
        self.assertTrue(used <= hs.ACT_KINDS, "a need bottoms out in an undeclared act")
        self.assertEqual(used - _ELEVEN, {"memory"},
                         "the layer forced a host act beyond the declared memory growth")

    def test_a5_the_libc_surface_is_atop_the_acts_not_an_act_kind(self):
        for banned in ("libc", "libc-surface", "malloc", "posix"):
            self.assertNotIn(banned, hs.ACT_KINDS,
                             "%r is an act kind — the libc surface must be atop the acts, not a kind" % banned)
        hl = InterpreterHost()
        with hs.using(hs.StubHost()):
            region = hl.libc.malloc(8)          # a libc op bottoms out in the memory act
            region[0:1] = b"z"
            self.assertEqual(bytes(region[0:1]), b"z")
        # THE CHECK CAN FAIL: a thirteenth act kind is refused (the set stays closed).
        with self.assertRaises(hs.HostSeamError):
            hs.declare_act("thirteenth-kind", hs.PORTABLE)


# ==================================================================================================
# A6 — THE ATTESTED SURFACE STAYS COHERENT WITH THE NEW LAYER
# ==================================================================================================

class TestA6AttestedSurfaceCoherent(unittest.TestCase):

    def test_a6_the_attested_surface_is_coherent_with_the_new_layer(self):
        self.assertIn("hosting/__init__.py", att.ATTESTED_MEMBERS)
        self.assertIn("hosting/interpreter_host.py", att.ATTESTED_MEMBERS)
        self.assertEqual(att.law_guard_surface(), sorted(att.ATTESTED_MEMBERS))   # manifest == walk
        self.assertEqual(att.twin_uncovered(), [])                                # nothing uncovered
        self.assertEqual(att.ATTESTED_MEMBERS, tuple(sorted(att.ATTESTED_MEMBERS)))  # stays sorted


if __name__ == "__main__":
    unittest.main()
