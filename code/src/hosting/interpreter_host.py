# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: engine-source · OS-architecture
# vocabulary (a POSIX/libc personality above a small kernel, an enclosed borrowed worker consumed
# sealed and act-witnessed, a sealed hash-checked interpreter, the host seam's closed act set) as in
# the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability — this SUPPLIES what CPython
# needs to run above our own kernel, by function; it attacks nothing. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS hosting — THE INTERPRETER-HOSTING LAYER (C7 P7a; design/54 §7 P7; design/47 §5 L5 / §2 I3).

WHAT THIS IS. The layer beneath CPython and above our own kernel. CPython is the code that runs
AWIG OS's rules; it runs today only on Linux's full POSIX/libc surface. This layer SUPPLIES that
surface above our own kernel: it presents, to a hosted CPython, the host-surface needs CPython
exercises — files, threads, memory, the clock, entropy, the one connection, and a libc surface —
and WIRES each need DOWN to the host seam's act set (bridge/host_seam.py: the eleven P2 acts + the
C7 P7a `memory` growth). Nothing here touches the host directly; every crossing is one seam act
(the host-crossing census reds a direct crossing in this CORE-zone module).

THE DRIVER CUT (design/47 §5, L5 — supply, never own). The layer SUPPLIES the ecosystem CPython
needs; it does not re-implement CPython or a C library from scratch. CPython and its libc are
BORROWED. They are consumed SEALED, named by a pinned digest, and RE-CHECKED at every waking
(`SealSet.wake` — the attestation digest idiom, reused). They run as ENCLOSED WORKERS: their
effects cross the boundary as the seam's acts (act-witnessed), and NONE of their code enters the
signed base. Our own code — this layer — IS read whole and signed (an attested member; design/47
§2 I3: no opaque code in the signed base).

WHAT THIS UNIT PROVES, AND WHAT IT DOES NOT (the honest caps).
  PROVES  the layer's SHAPE — every host-surface need CPython exercises maps to a seam act (+ memory)
          or to the libc surface built atop the acts; and a real CPython RUNS THROUGH the layer in
          the pinned guest, its needs served by the layer, the surface DRIVEN by CPython running
          (a removed surface element breaks the run), never assumed.
  DEFERS  the full device-level POSIX/libc personality (a hosted CPython's every raw syscall — a
          C library, a thread creator, a TCP stack of our own) to a fuller build. For P7a the acts
          bottom out in a STAND-IN performer beneath the seam (P2's StubHost, or the hosted base in
          the guest — RealHost); P3 makes them our own kernel. This unit proves the interpreter runs
          THROUGH the layer, NOT that it runs on a tiny kernel (that is P3).
  LEAVES  the interpreter's FINAL witness stance to the owner (Q2, at P5). P7a consumes CPython
          sealed + hash-checked as archi ruled; it does not settle whether that bar is final or the
          gate moves to a signable host later.

PORTABLE, NOT GENERAL-PURPOSE (design/47 §1). The layer maps CPython's needs to the seam's acts + the
one declared `memory` growth; it adds NO host capability CPython did not force. The libc surface is
built ABOVE the acts and is NOT an act kind.
"""

from pathlib import Path                    # path ADAPTATION only (construction, never a file-method call):
                                            # a hosted CPython passes string paths; the seam's contract is
                                            # pathlib.Path (byte-for-byte with the core's callers), so the
                                            # personality adapts str -> Path before every seam file act.
from bridge.host_seam import host          # the closed act set — the ONLY way this layer reaches the host
from kernel.canonical import canonical_hash  # the estate's ONE digest form — the sealed-artifact check reuses it


class SealBrokenError(RuntimeError):
    """A borrowed sealed artifact's bytes no longer match its pinned digest at a waking. The
    interpreter is NOT run above a broken seal — a real seal is never waved through (design/54 B6)."""


class NeedNotSupplied(RuntimeError):
    """The layer was asked for a host-surface need it does not supply — a planted-missing surface
    element (a needed call removed). Raised so the interpreter's run FAILS loud rather than reaching
    the host by some other path (A2: the check can fail; the surface is the driven one)."""


# ==================================================================================================
# THE SEALED BORROWED ARTIFACT — CPython and its libc, consumed sealed, re-checked at every waking
# ==================================================================================================

class SealedArtifact:
    """A BORROWED artifact (the CPython interpreter, its libc) consumed SEALED — named by a pinned
    canonical digest, its bytes never read into the signed base, only hashed to confirm the seal.

    The bytes are read through the seam's body-read act (`host().open_read_binary`) — the same act
    and the same `canonical_hash` the engine attestation uses for its members (attestation._member_digest).
    `digest()` recomputes the seal from the artifact's current bytes; `verify()` answers whether it
    still matches the pin. An absent artifact digests to None (a fact, never a crash)."""

    def __init__(self, name, path, pinned_digest):
        self.name = name                 # "cpython" / "libc" — the enclosed worker's role
        self.path = path                 # the sealed artifact's location (OUTSIDE the signed base)
        self.pinned_digest = pinned_digest   # the digest named at seal time (the pin)

    def digest(self):
        """The canonical digest of the artifact's current bytes, or None if it is not on disk. Read
        through the body-read seam act — the layer never opens the host file directly."""
        try:
            with host().open_read_binary(self.path) as f:
                return canonical_hash(f.read())
        except OSError:
            return None

    def verify(self):
        """True iff the artifact's current bytes still match the pinned digest (the seal holds)."""
        return self.digest() == self.pinned_digest


class SealSet:
    """The set of borrowed sealed artifacts (CPython + its libc). `wake` RE-CHECKS every seal — the
    hash-check at every waking — and REFUSES (raises `SealBrokenError`) if any artifact's bytes have
    moved off its pin. `check` returns the per-artifact verdict without raising (the view the test
    drives). A hosted CPython is run only after `wake` returns clean."""

    def __init__(self, artifacts):
        self._artifacts = {a.name: a for a in artifacts}

    def names(self):
        return sorted(self._artifacts)

    def check(self):
        """{name: True|False} — does each borrowed artifact still match its pin? A pure read."""
        return {name: a.verify() for name, a in self._artifacts.items()}

    def wake(self):
        """Re-check every seal AT THIS WAKING; raise on the first that fails (a planted byte change in
        the sealed CPython or libc reds here — the check can fail, A3). Returns the clean verdict."""
        verdict = self.check()
        broken = sorted(n for n, ok in verdict.items() if not ok)
        if broken:
            raise SealBrokenError(
                "sealed borrowed artifact(s) no longer match their pinned digest at this waking: %s "
                "— the interpreter is not run above a broken seal (design/54 B6)" % broken)
        return verdict


# ==================================================================================================
# THE SURFACE MAP — every host-surface need bottoms out in a declared seam act (+ the memory growth)
# ==================================================================================================

# WHICH SEAM ACT(S) EACH NEED WIRES DOWN TO. This makes "the layer widens the act set only by memory"
# machine-checkable (A5): the union of these act kinds must be a SUBSET of host_seam.ACT_KINDS, and
# the growth over P2's eleven must be exactly {"memory"}. The libc surface (below) is built ATOP these
# needs and names NO act kind of its own.
NEED_ACTS = {
    "files":      ("record-pen", "atomic-write-once", "remove", "body-read"),
    "threads":    ("concurrency",),
    "memory":     ("memory",),           # the C7 P7a growth — the twelfth act
    "clock":      ("recording-clock", "commit-window"),
    "entropy":    ("entropy",),
    "connection": ("network-socket",),
}


class _Files:
    """CPython's file need, wired to the record-pen / atomic-write-once / remove / body-read acts."""
    # NOTE the surface names deliberately AVOID the pathlib file-method names (read_bytes/write_bytes/
    # mkdir/open/...): this module is in the CORE zone, where the host-crossing census reads any
    # `.<file-method>(` call on a non-`host()` receiver as a direct pathlib crossing. The seam calls
    # below (`host().read_bytes(...)`) are exempt; the layer's own delegation names must not collide.
    def open_read(self, path):              return host().open_read(Path(path))
    def open_append(self, path):            return host().open_append(Path(path))
    def write_once(self, tmp, final, data): return host().write_file_durably(Path(tmp), Path(final), data)
    def read_all_bytes(self, path):         return host().read_bytes(Path(path))
    def put_bytes(self, path, data):        return host().write_bytes(Path(path), data)
    def read_binary(self, path):            return host().open_read_binary(Path(path))
    def exists(self, path):                 return host().path_exists(Path(path))
    def make_dir(self, path):               return host().mkdir_p(Path(path))
    def remove(self, path):                 return host().remove(Path(path))
    def walk(self, top):                    return host().walk(Path(top))


class _Threads:
    """CPython's synchronization substrate, wired to the concurrency act (locks/events/thread-local/
    ident — the primitives the seam declares). Thread CREATION itself is interpreter-internal
    (`_thread`) and part of the fuller device-level personality P3 completes; P7a supplies the
    concurrency SUBSTRATE the seam carries."""
    def new_lock(self):          return host().new_lock()
    def new_rlock(self):         return host().new_rlock()
    def new_event(self):         return host().new_event()
    def new_thread_local(self):  return host().new_local()
    def thread_ident(self):      return host().thread_ident()


class _Memory:
    """CPython's memory need, wired to the `memory` act (host-backed anonymous pages — the twelfth
    act kind the eleven did not carry)."""
    def allocate(self, n):       return host().memory(n)


class _Clock:
    """CPython's clock need, wired to the recording-clock (wall) and commit-window (monotonic/sleep) acts."""
    def now_iso(self):           return host().recorded_now_iso()
    def monotonic(self):         return host().monotonic()
    def sleep(self, seconds):    return host().sleep(seconds)


class _Entropy:
    """CPython's entropy need, wired to the entropy act (os.urandom beneath)."""
    def random(self, n):         return host().urandom(n)


class _Connection:
    """CPython's one connection, wired to the guest-gated network-socket act (real only in the guest)."""
    def open_socket(self, family): return host().open_stream_socket(family)


class _Libc:
    """THE LIBC SURFACE — built ABOVE the acts, NOT an act kind (design/47 §5 precision; A5). The
    C-library-shaped surface a hosted CPython links against, each primitive presented atop one of the
    needs above so it bottoms out in a seam act. For P7a this is the surface's SHAPE (the named libc
    personality mapped act-by-act), not a from-scratch C library — the fuller device-level libc is a
    later build. It NAMES no act kind of its own; every call delegates to a need."""

    def __init__(self, hostlayer):
        self._h = hostlayer

    # memory management -> the memory act
    def malloc(self, n):                 return self._h.memory.allocate(n)
    def free(self, region):              # release the region; anonymous memory is reclaimed on drop
        close = getattr(region, "close", None)
        if callable(close):
            close()

    # file i/o -> the file acts (names avoid the pathlib file-method set; see _Files)
    def open_read(self, path):           return self._h.files.open_read(path)
    def read_file_bytes(self, path):     return self._h.files.read_all_bytes(path)
    def write_file_bytes(self, path, data): return self._h.files.put_bytes(path, data)

    # time -> the clock acts
    def clock_gettime(self):             return self._h.clock.monotonic()
    def wall_now(self):                  return self._h.clock.now_iso()

    # entropy -> the entropy act
    def getrandom(self, n):              return self._h.entropy.random(n)

    # threads -> the concurrency act
    def pthread_mutex(self):             return self._h.threads.new_lock()

    # sockets -> the network-socket act
    def socket(self, family):            return self._h.connection.open_socket(family)


class InterpreterHost:
    """THE INTERPRETER-HOSTING LAYER — the surface a hosted CPython consumes, wired down to the seam.

    Construct it with the borrowed sealed artifacts (CPython + its libc). `wake()` re-checks their
    seals (A3) and returns the layer ready to serve; the needs (`.files`, `.threads`, `.memory`,
    `.clock`, `.entropy`, `.connection`) and the `.libc` surface each bottom out in the seam's acts.
    Whatever performer stands beneath the seam (StubHost, or RealHost in the guest — the stand-in),
    the layer is unchanged; P3 swaps our own kernel beneath without a line here moving (design/54 L1)."""

    def __init__(self, seals=None):
        self.seals = seals if seals is not None else SealSet([])
        self.files = _Files()
        self.threads = _Threads()
        self.memory = _Memory()
        self.clock = _Clock()
        self.entropy = _Entropy()
        self.connection = _Connection()
        self.libc = _Libc(self)

    def wake(self):
        """A waking of the interpreter host: RE-CHECK the borrowed seals (raise on a broken one),
        then return self ready to serve. Every waking re-verifies — a sealed artifact whose bytes
        moved off its pin stops the waking (A3)."""
        self.seals.wake()
        return self

    def need(self, name):
        """Return the surface object for a named need, or RAISE `NeedNotSupplied` — the mechanical
        form of A2: a need the layer does not supply cannot be reached by some other host path; the
        run fails loud. (A test drops a need to prove the run breaks — the surface is the driven one.)"""
        supplied = {"files": self.files, "threads": self.threads, "memory": self.memory,
                    "clock": self.clock, "entropy": self.entropy, "connection": self.connection,
                    "libc": self.libc}
        if name not in supplied or getattr(self, name, None) is None:
            raise NeedNotSupplied(
                "the interpreter-hosting layer supplies no %r surface — CPython's run cannot reach the "
                "host except through the layer, so a missing surface makes the run fail (A2)" % (name,))
        return supplied[name]

    @staticmethod
    def acts_used():
        """The set of seam act kinds every supplied need bottoms out in — the union of NEED_ACTS. The
        acceptance holds this against host_seam.ACT_KINDS (subset) and asserts the growth over P2's
        eleven is exactly {'memory'} (A5). The libc surface adds nothing here — it is atop the acts."""
        used = set()
        for acts in NEED_ACTS.values():
            used.update(acts)
        return used
