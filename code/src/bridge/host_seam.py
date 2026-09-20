# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: engine-source · OS-architecture
# vocabulary (the declared seam, a performer interface, a stub performer, single-writer, the
# guest-gated socket) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability —
# this DECLARES the closed set of acts the governance core asks its host to PERFORM as one interface
# and gives the real host performer the byte-for-byte calls that were scattered inline, so a different
# performer can be swapped beneath the seam (design/54 L1 swap-not-rewrite) without a single act above
# it changing. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS bridge — THE HOST SEAM: the closed act set the core asks its host to perform, one contract.

C7 P2 (design/54 §7 P2; §3 B3/B8; §5 L1/L5/L6/L13). The governance core (kernel/, the founding
installer) never touches the host directly; every crossing it makes is one of a small CLOSED set of
effect acts — the record pen (append/read/sync/stat/mkdir), the atomic write-once, the remove, the
host-PID single-writer lock, the recording clock, the commit-window monotonic/sleep, entropy, the
concurrency substrate, the guest-gated socket, the body read/walk, the founding-pack read. P1's
census (planning/evidence/C7-P1-SEAM-CENSUS/FINDINGS.md) enumerated the set and its ~60 call sites in
eight files. This module declares that set as ONE performer interface and routes the sites through it.

THE TWO SEAMS ARE SEPARATE (L13, archi :3919). This is the EFFECT seam — the acts the core PERFORMS.
The OBSERVE seam (observe/seam.py) is a separate, read-only host surface with its own contract, and
P2 does not touch it. This performer stands in only for the effect set.

WHAT THE SEAM IS, AND WHAT IT IS NOT. Routing changes WHERE a host call is made, never WHAT it does:
the real performer (`RealHost`) makes the identical call — the same bytes appended, the same reads,
the same lock semantics, the same nonce source — so the whole estate is byte-for-byte unchanged above
it. The stub performer (`StubHost`) performs the declared acts against an in-memory stand-in for the
host, so the record round-trip and the reads run green with NO host beneath them — the mechanical
proof that the seam is a contract, not a leak. The set is CLOSED and grow-only by a filed ruling: it
grew 11 -> 12 for C7 P7a (the interpreter-hosting layer added `memory`, host-backed anonymous pages a
hosted CPython needs; archi countersign), and a THIRTEENTH kind cannot be added without a further
filed ruling — exactly as `ATTESTED_MEMBERS` and the effect-order census's `IRREVERSIBLE_PRIMITIVES`
are grow-only closed vocabularies.

THE PORTABILITY LABEL (L6, B8 "no silent Linux"). Every act carries an explicit portability label —
the host-PID single-writer lock is the LEAST-PORTABLE crossing (a different host has different process
semantics; archi :3919 named it the least portable site); the guest-gated socket is a GUEST-GATED
CAPABILITY (real only inside the pinned guest, EP-00 rule 9); everything else is a PORTABLE HOST
PRIMITIVE (disk, clock, entropy, threads — names no Linux facility). The label census (tools/
conformance/host_crossing_census.py) reds a host method that carries no label.

THE SEALED-CORE WORKING ASSUMPTION IS UNTOUCHED (L9). P2 does not decide the core's provenance or the
interpreter's home; it contracts the seam a future performer will stand behind. No one-way door here.
"""

import datetime
import fcntl
import mmap
import os
import socket
import threading
import time
from contextlib import contextmanager


# ---- the closed act set + its portability labels ---------------------------------------------

#: The three portability labels (L6). A host act is exactly one of these.
PORTABLE = "portable-host-primitive"        # names no Linux facility: disk, clock, entropy, threads
LEAST_PORTABLE = "least-portable"           # the host-PID single-writer lock (archi :3919)
GUEST_GATED = "guest-gated-capability"      # real only inside the pinned guest (EP-00 rule 9)

LABELS = frozenset({PORTABLE, LEAST_PORTABLE, GUEST_GATED})

#: THE CLOSED SET of act KINDS the core asks its host to perform (P1 §Q-A). Grow-only by a filed
#: ruling — the same discipline as attestation.ATTESTED_MEMBERS and the effect-order census's
#: IRREVERSIBLE_PRIMITIVES. A new kind cannot enter without widening this set.
#: DECLARED GROWTH 11 -> 12 (C7 P7a, THE INTERPRETER-HOSTING LAYER; design/54 §7 P7; archi
#: countersign — a once-only widen, filed): `memory` joins as the twelfth kind. A hosted CPython
#: needs host-backed memory (anonymous pages) that the eleven acts did not carry; the layer wires
#: that need down to this act (the LIBC SURFACE is built ABOVE the acts and is NOT an act kind).
#: A THIRTEENTH kind still cannot enter without a further filed ruling (declare_act refuses it).
#:
#: C7 P3 — THE DEFINITIONS ARE ROWS IN THE RECORD (design/54 §3 B11, §5 L16; archi :3993). The
#: twelve kinds, each with its portability label and its meaning, are genesis-seeded as CREATE-RULE
#: rows in the founding pack ("13-act-kind-definitions"); the seam's act set is DERIVED from those
#: rows at build by a FOLD (`boot.live_act_kinds`) and is a fold, NEVER a stored status beside the
#: record (L16); delete the built act set and regenerate it from the rows and the same twelve come
#: back. THE RECORD IS THE SINGLE SOURCE of the kinds' contracts; THIS constant is the store-free
#: closed-set GATE `declare_act` refuses a thirteenth against (the C7 P2/P7a pins call declare_act
#: with no store), RECONCILED against the rows at build (A2 + the site-vs-row label check, precision
#: b — a kind in the code path absent from the rows, or a site whose label disagrees with its row,
#: is CAUGHT and refuses) and CHECKED against the rows at every waking (A3, boot.check_kernel_
#: against_rows). This is the op-registry pattern: the op HANDLERS live in code while the op
#: DEFINITIONS live in the record and are reconciled — here the act SITES (the ACTS table below)
#: live in code while the act-kind DEFINITIONS (name + label + meaning) live in the record.
ACT_KINDS = frozenset({
    "record-pen",          # the sole appender + the record reads/stat/mkdir
    "atomic-write-once",   # the blob/vault write-once + the durability barrier (dir fsync)
    "remove",              # the handover removal tail (blobs)
    "single-writer-lock",  # the host-PID liveness lock — the LEAST-PORTABLE crossing
    "recording-clock",     # datetime.now(utc) — the recorded_at on every record
    "commit-window",       # time.monotonic / time.sleep — the group-commit window
    "entropy",             # os.urandom — nonces and fresh secrets
    "concurrency",         # the threading substrate (a host primitive the core must supply)
    "network-socket",      # the one guest-gated outbound socket
    "body-read",           # the attestation member read + os.walk of the S-plane
    "founding-pack-read",  # the installer's read of founding-pack.json (DATA, never edited)
    "memory",              # host-backed anonymous memory — the C7 P7a interpreter-hosting growth (12th)
})


class HostSeamError(RuntimeError):
    """A twelfth act kind was declared, or an undeclared host act was reached — the closed set
    refuses it (never repaired, never widened silently)."""


def declare_act(kind, label):
    """Return the (kind, label) pair for the ACTS table, REFUSING a kind outside the closed
    `ACT_KINDS` or a label outside `LABELS`. This is the mechanical gate on the closed set: a
    twelfth act kind cannot be added to the interface without first widening `ACT_KINDS` by a
    filed ruling (A1 — the set is closed and the check can fail)."""
    if kind not in ACT_KINDS:
        raise HostSeamError(
            "%r is not a declared act kind — the host-seam act set is CLOSED; widen ACT_KINDS by a "
            "filed ruling before adding it (P2, design/54 §5)" % (kind,))
    if label not in LABELS:
        raise HostSeamError(
            "%r is not a portability label — a host act carries exactly one of %s (L6)"
            % (label, sorted(LABELS)))
    return (kind, label)


# ---- the interface: the closed act set, one method per crossing ------------------------------

class HostSeam:
    """The performer INTERFACE — the closed act set declared once. Each method is one host act; the
    `ACTS` table names its kind and portability label. `RealHost` makes the real host call
    byte-for-byte; `StubHost` performs it against an in-memory stand-in. The base refuses every act
    (a bare `HostSeam` performs nothing) so a partially-implemented performer fails loud, never
    silently."""

    #: {method name: (act kind, portability label)} — the closed set as a table. Built through
    #: `declare_act`, so a kind outside ACT_KINDS cannot appear here. The label census reads this to
    #: prove every host method on a performer is declared and labelled (A5).
    ACTS = {
        # -- record pen (the sole appender; the record reads/stat/mkdir/sync) --------------------
        "open_append":        declare_act("record-pen", PORTABLE),
        "open_read":          declare_act("record-pen", PORTABLE),
        "fstat":              declare_act("record-pen", PORTABLE),
        "fdatasync":          declare_act("record-pen", PORTABLE),
        # -- atomic write-once + the durability barrier (blobs, vault) ---------------------------
        "write_file_durably": declare_act("atomic-write-once", PORTABLE),
        "fsync_dir":          declare_act("atomic-write-once", PORTABLE),
        "write_bytes":        declare_act("atomic-write-once", PORTABLE),
        "mkdir_p":            declare_act("atomic-write-once", PORTABLE),
        "path_exists":        declare_act("atomic-write-once", PORTABLE),
        "read_bytes":         declare_act("atomic-write-once", PORTABLE),
        # -- the handover removal tail (blobs) ---------------------------------------------------
        "remove":             declare_act("remove", PORTABLE),
        # -- the host-PID single-writer lock (the LEAST-PORTABLE crossing) -----------------------
        "pid_alive":          declare_act("single-writer-lock", LEAST_PORTABLE),
        "getpid":             declare_act("single-writer-lock", LEAST_PORTABLE),
        "lock_read":          declare_act("single-writer-lock", LEAST_PORTABLE),
        "lock_write":         declare_act("single-writer-lock", LEAST_PORTABLE),
        "lock_unlink":        declare_act("single-writer-lock", LEAST_PORTABLE),
        # -- the recording clock -----------------------------------------------------------------
        "recorded_now_iso":   declare_act("recording-clock", PORTABLE),
        # -- the commit window -------------------------------------------------------------------
        "monotonic":          declare_act("commit-window", PORTABLE),
        "sleep":              declare_act("commit-window", PORTABLE),
        # -- entropy -----------------------------------------------------------------------------
        "urandom":            declare_act("entropy", PORTABLE),
        # -- the concurrency substrate -----------------------------------------------------------
        "new_lock":           declare_act("concurrency", PORTABLE),
        "new_rlock":          declare_act("concurrency", PORTABLE),
        "new_event":          declare_act("concurrency", PORTABLE),
        "new_local":          declare_act("concurrency", PORTABLE),
        "thread_ident":       declare_act("concurrency", PORTABLE),
        # -- host-backed memory (the C7 P7a interpreter-hosting growth, the 12th kind) ------------
        "memory":             declare_act("memory", PORTABLE),
        # -- the body read (attestation) ---------------------------------------------------------
        "open_read_binary":   declare_act("body-read", PORTABLE),
        "walk":               declare_act("body-read", PORTABLE),
        # -- the founding-pack read (the installer) ----------------------------------------------
        "open_read_text":     declare_act("founding-pack-read", PORTABLE),
        # -- the one guest-gated outbound socket -------------------------------------------------
        "open_stream_socket": declare_act("network-socket", GUEST_GATED),
    }

    def _undeclared(self, name):
        raise HostSeamError(
            "the host act %r is not performed by this seam (%s) — the base HostSeam performs "
            "nothing; a real performer must implement every declared act" % (name, type(self).__name__))

    # every act, as a base stub that refuses; RealHost / StubHost override the ones they perform.
    def open_append(self, path):                 self._undeclared("open_append")
    def open_read(self, path):                   self._undeclared("open_read")
    def fstat(self, fd):                         self._undeclared("fstat")
    def fdatasync(self, fd):                     self._undeclared("fdatasync")
    def write_file_durably(self, tmp, final, data, mode=0o644):  self._undeclared("write_file_durably")
    def fsync_dir(self, dirpath):                self._undeclared("fsync_dir")
    def write_bytes(self, path, data):           self._undeclared("write_bytes")
    def mkdir_p(self, dirpath):                  self._undeclared("mkdir_p")
    def path_exists(self, path):                 self._undeclared("path_exists")
    def read_bytes(self, path):                  self._undeclared("read_bytes")
    def remove(self, path):                      self._undeclared("remove")
    def pid_alive(self, pid):                    self._undeclared("pid_alive")
    def getpid(self):                            self._undeclared("getpid")
    def lock_read(self, path):                   self._undeclared("lock_read")
    def lock_write(self, path, text):            self._undeclared("lock_write")
    def lock_unlink(self, path):                 self._undeclared("lock_unlink")
    def recorded_now_iso(self):                  self._undeclared("recorded_now_iso")
    def monotonic(self):                         self._undeclared("monotonic")
    def sleep(self, seconds):                    self._undeclared("sleep")
    def urandom(self, n):                        self._undeclared("urandom")
    def new_lock(self):                          self._undeclared("new_lock")
    def new_rlock(self):                         self._undeclared("new_rlock")
    def new_event(self):                         self._undeclared("new_event")
    def new_local(self):                         self._undeclared("new_local")
    def thread_ident(self):                      self._undeclared("thread_ident")
    def memory(self, n):                         self._undeclared("memory")
    def open_read_binary(self, path):            self._undeclared("open_read_binary")
    def walk(self, top):                         self._undeclared("walk")
    def open_read_text(self, path, encoding="utf-8"):  self._undeclared("open_read_text")
    def open_stream_socket(self, family):        self._undeclared("open_stream_socket")


# ---- the real performer: today's host, byte-for-byte -----------------------------------------

class RealHost(HostSeam):
    """The Linux host performer. Every method makes the IDENTICAL call the site made inline before
    the routing — same open modes, same os flags, same lock semantics, same nonce source — so the
    estate above the seam is byte-for-byte unchanged. This is the ONE place the effect crossings
    live; the census proves nothing above the seam reaches the host except through here."""

    def __init__(self):
        # The single-writer lock's HELD file descriptors, keyed by the resolved lock-file path
        # (EP-MAINT-OUTSIDE-5). One writer holds one fd for the record's lifetime; closing it drops
        # the OS advisory lock. Internal bookkeeping — NOT a host act, so the label census (which
        # skips `_`-prefixed names and non-methods) does not see it and the closed ACTS set is
        # unchanged.
        self._lock_fds = {}

    # -- record pen --------------------------------------------------------------------------
    def open_append(self, path):
        return path.open("a", encoding="utf-8")           # store.py:831 — the SOLE appender

    def open_read(self, path):
        return path.open("r", encoding="utf-8")           # store.py:564

    def fstat(self, fd):
        return os.fstat(fd)                               # store.py:94, :839

    def fdatasync(self, fd):
        return os.fdatasync(fd)                           # store.py:950 — the record's barrier

    # -- atomic write-once + durability barrier ----------------------------------------------
    def write_file_durably(self, tmp, final, data, mode=0o644):
        # blobs.py:124-129 — the atomic write-once, byte-for-byte: bytes durable, then the name.
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())                          # the BYTES are durable
        os.replace(tmp, final)                            # write-once, atomically visible

    def fsync_dir(self, dirpath):
        # blobs.py:89-93 / :205-209 — make the NAME durable (idempotent).
        dfd = os.open(dirpath, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)

    def write_bytes(self, path, data):
        return path.write_bytes(data)                     # vault.py:69 — write-once secret bytes

    def mkdir_p(self, dirpath):
        return dirpath.mkdir(parents=True, exist_ok=True)  # store:556, blobs:78/122, vault:56/67

    def path_exists(self, path):
        return path.exists()                              # blobs/vault/store existence checks

    def read_bytes(self, path):
        return path.read_bytes()                          # blobs.py:114, :134

    # -- the handover removal tail -----------------------------------------------------------
    def remove(self, path):
        return os.remove(path)                            # blobs.py:204 — the bytes leave the store

    # -- the host-PID single-writer lock (LEAST PORTABLE) ------------------------------------
    def pid_alive(self, pid):
        # store.py:116 — the host-PID liveness probe. Its semantics ARE the single-writer lock:
        # a live foreign pid holds the log. Byte-for-byte with the inline `os.kill(pid, 0)` and its
        # exact exception reading (a process owned by another user EXISTS; PermissionError => True).
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def getpid(self):
        return os.getpid()                                # store.py:636, :641, :649

    def lock_read(self, path):
        # The lock file's pid text — a DIAGNOSTIC read (the holder's pid for a refusal message),
        # NOT the admission decision (the held advisory lock below is). Opens and closes its own fd;
        # a loser (no lock held) may read it harmlessly, and it is never read on the acquire happy
        # path — a POSIX record lock is released by closing ANY fd on its inode, so the holder never
        # opens a second one.
        return path.read_text()

    def lock_write(self, path, text):
        # THE SINGLE-WRITER LOCK, MADE REAL (EP-MAINT-OUTSIDE-5). WAS a plain `write_text` — a pid
        # stamp with no atomicity, which admitted two racing writers. NOW: open the lock file and
        # take a HELD, EXCLUSIVE, NON-BLOCKING OS advisory lock on it (fcntl.lockf = POSIX F_SETLK),
        # keeping the fd open for the writer's lifetime so a second PROCESS opening the same record
        # is refused by the OS (BlockingIOError). POSIX record locks are PROCESS-associated (unlike
        # flock, which is open-file-description-associated and would self-conflict in one process),
        # so two opens in ONE process do NOT conflict here — the in-process second-writer gate is
        # store._acquire_lock's registry, by design, and its plant stays able to fail.
        key = os.path.realpath(str(path))
        fd = os.open(key, os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   # refuse a second process, non-blocking
        except OSError:
            os.close(fd)
            raise                                            # store._acquire_lock surfaces the refusal
        os.ftruncate(fd, 0)
        os.write(fd, text.encode("utf-8"))                   # the holder's pid, for diagnosis
        self._lock_fds[key] = fd                             # HOLD it for the writer's lifetime

    def lock_unlink(self, path):
        # RELEASE the held advisory lock (close the fd — the OS drops the lock) then unlink the file.
        # Idempotent; called on the store's close and the atexit backstop.
        key = os.path.realpath(str(path))
        fd = self._lock_fds.pop(key, None)
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    # -- recording clock ---------------------------------------------------------------------
    def recorded_now_iso(self):
        return datetime.datetime.now(datetime.timezone.utc).isoformat()   # store.py:55

    # -- commit window -----------------------------------------------------------------------
    def monotonic(self):
        return time.monotonic()                           # commit.py:331, :338

    def sleep(self, seconds):
        return time.sleep(seconds)                        # commit.py:352

    # -- entropy -----------------------------------------------------------------------------
    def urandom(self, n):
        return os.urandom(n)                              # crypto.py:274, :306

    # -- concurrency substrate ---------------------------------------------------------------
    def new_lock(self):
        return threading.Lock()                           # commit.py:194, :195

    def new_rlock(self):
        return threading.RLock()                          # store.py:615

    def new_event(self):
        return threading.Event()                          # commit.py:152

    def new_local(self):
        return threading.local()                          # commit.py:186, store.py:620

    def thread_ident(self):
        return threading.get_ident()                      # commit.py:290

    # -- host-backed memory (C7 P7a) ---------------------------------------------------------
    def memory(self, n):
        # A writable region of `n` bytes of host-backed anonymous memory (the host's own memory
        # manager, no file, no Linux facility named). This is the twelfth act a hosted CPython needs
        # and the eleven did not carry; the interpreter-hosting layer wires CPython's memory need
        # down to here. mmap(-1, n) is an anonymous mapping — a PORTABLE host primitive.
        return mmap.mmap(-1, n)

    # -- body read (attestation) -------------------------------------------------------------
    def open_read_binary(self, path):
        return open(path, "rb")                           # attestation.py:194 — one member's bytes

    def walk(self, top):
        return os.walk(top)                               # attestation.py:252 — the S-plane walk

    # -- founding-pack read ------------------------------------------------------------------
    def open_read_text(self, path, encoding="utf-8"):
        return open(path, encoding=encoding)              # install.py:72 — the pack is DATA

    # -- the one guest-gated outbound socket -------------------------------------------------
    def open_stream_socket(self, family):
        return socket.socket(family, socket.SOCK_STREAM)  # kernel_port.py:870 — guest-gated real fd


# ---- the stub performer: the declared acts, no host beneath them -----------------------------

class _StubAppendHandle:
    """An in-memory stand-in for the record pen's held append handle — enough of the file protocol
    for the store's held-descriptor pattern (write/flush/fileno/close) with NO host descriptor."""

    def __init__(self, backing, key):
        self._b = backing
        self._key = key
        self._fd = backing._alloc_fd(key)
        backing._files.setdefault(key, "")

    def write(self, s):
        self._b._files[self._key] = self._b._files.get(self._key, "") + s
        return len(s)

    def flush(self):
        pass

    def fileno(self):
        return self._fd

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class _FakeStat:
    """Just the two identity fields the store's held-descriptor pattern reads off a stat."""

    def __init__(self, st_dev, st_ino):
        self.st_dev = st_dev
        self.st_ino = st_ino


class StubHost(HostSeam):
    """A performer that performs the declared acts against an IN-MEMORY stand-in for the host — no
    disk, no real clock, no socket. The record round-trip and the content reads run green above it
    (A3), proving the seam is a contract the core does not see through. Acts a memory host cannot
    honestly perform — the guest-gated socket, a real body read of the on-disk S-plane — REFUSE
    rather than pretend (never a silent no-op that would hide a leak). Concurrency is real (a lock
    must lock even here); entropy is real (a stub secret that is predictable is worse than none)."""

    def __init__(self):
        self._files = {}          # path-string -> bytes|str content
        self._dirs = set()        # path-strings known to exist as directories
        self._next = 900000       # a fake-descriptor allocator, well clear of real fds
        self._fds = {}            # fake fd -> (path key, identity)

    def _alloc_fd(self, key):
        fd = self._next
        self._next += 1
        self._fds[fd] = (key, (7777, fd))     # a stable (dev, ino) identity per fake fd
        return fd

    # -- record pen --------------------------------------------------------------------------
    def open_append(self, path):
        return _StubAppendHandle(self, str(path))

    def open_read(self, path):
        import io
        return io.StringIO(self._files.get(str(path), ""))

    def fstat(self, fd):
        ident = self._fds.get(fd)
        if ident is None:
            raise OSError(9, "bad file descriptor (stub)")
        return _FakeStat(*ident[1])

    def fdatasync(self, fd):
        pass

    # -- atomic write-once -------------------------------------------------------------------
    def write_file_durably(self, tmp, final, data, mode=0o644):
        self._files[str(final)] = bytes(data)
        self._files.pop(str(tmp), None)

    def fsync_dir(self, dirpath):
        pass

    def write_bytes(self, path, data):
        self._files[str(path)] = data if isinstance(data, (bytes, bytearray)) else bytes(data)

    def mkdir_p(self, dirpath):
        self._dirs.add(str(dirpath))

    def path_exists(self, path):
        return str(path) in self._files or str(path) in self._dirs

    def read_bytes(self, path):
        try:
            return self._files[str(path)]
        except KeyError:
            raise FileNotFoundError("stub host holds no bytes for %s" % (path,))

    # -- the handover removal tail -----------------------------------------------------------
    def remove(self, path):
        self._files.pop(str(path), None)

    # -- the host-PID single-writer lock -----------------------------------------------------
    def pid_alive(self, pid):
        return False                          # a memory host has no live foreign writer

    def getpid(self):
        return 1                              # a stable fake identity (no host process)

    def lock_read(self, path):
        return self._files.get(str(path), "")

    def lock_write(self, path, text):
        self._files[str(path)] = text

    def lock_unlink(self, path):
        self._files.pop(str(path), None)

    # -- recording clock ---------------------------------------------------------------------
    def recorded_now_iso(self):
        # A FIXED instant: the stub has no host clock, and a deterministic stamp is the honest
        # stand-in (a record still carries a well-formed recorded_at).
        return "1970-01-01T00:00:00+00:00"

    # -- commit window -----------------------------------------------------------------------
    def monotonic(self):
        return time.monotonic()               # the window's clock is real (a fake would spin)

    def sleep(self, seconds):
        return time.sleep(seconds)

    # -- entropy -----------------------------------------------------------------------------
    def urandom(self, n):
        return os.urandom(n)                  # real: a predictable stub secret is worse than none

    # -- concurrency substrate (real: a lock must lock) --------------------------------------
    def new_lock(self):
        return threading.Lock()

    def new_rlock(self):
        return threading.RLock()

    def new_event(self):
        return threading.Event()

    def new_local(self):
        return threading.local()

    def thread_ident(self):
        return threading.get_ident()

    # -- host-backed memory (real: a memory host CAN honestly supply memory) -----------------
    def memory(self, n):
        # A memory host performs `memory` for real — an in-process writable region (bytearray) IS
        # host-backed memory the stub can honestly hand back, exactly as it performs entropy and
        # concurrency for real. It is not one of the acts the stub must refuse.
        return bytearray(n)

    # -- acts a memory host cannot honestly perform: REFUSE, never pretend -------------------
    def open_read_binary(self, path):
        raise HostSeamError(
            "the stub performs no real body-read — %s lives on the host disk the stub stands in "
            "for; seed it into the stub or run this act against RealHost" % (path,))

    def walk(self, top):
        raise HostSeamError(
            "the stub performs no real body-read walk of %s — the S-plane lives on the host disk" % (top,))

    def open_read_text(self, path, encoding="utf-8"):
        raise HostSeamError(
            "the stub performs no real founding-pack read — %s is host DATA the stub stands in for" % (path,))

    def open_stream_socket(self, family):
        raise HostSeamError(
            "the stub performs no real socket — the network act is a guest-gated capability, real "
            "only inside the pinned guest (EP-00 rule 9); the memory host opens nothing")


# ---- the accessor: one performer, swappable beneath the seam ---------------------------------

_PERFORMER = RealHost()


def host():
    """The current host performer. Production runs `RealHost` (the default), so every routed site
    makes the real host call byte-for-byte. A test swaps in a `StubHost` with `using(...)`."""
    return _PERFORMER


def set_performer(performer):
    """Swap the performer beneath the seam; return the previous one. The whole estate above the seam
    routes through whatever this returns — the mechanism L1 (swap not rewrite) rests on."""
    global _PERFORMER
    prior = _PERFORMER
    _PERFORMER = performer
    return prior


@contextmanager
def using(performer):
    """Run a block with `performer` beneath the seam, restoring the prior one after — the stub swap
    A3's estate-green proof uses."""
    prior = set_performer(performer)
    try:
        yield performer
    finally:
        set_performer(prior)


# ---- C7 P3: the seam's act set DERIVED FROM THE RECORD (design/54 §3 B11, §5 L16) ------------
# The twelve act-kind DEFINITIONS (name + portability label + meaning) live as CREATE-RULE rows in
# the founding pack; the fold that reads them is `boot.live_act_kinds` (the record is the source, a
# fold and never a stored status). This module holds (1) the DERIVED ACT SET the build installs —
# what the delete-and-regenerate operates on — and (2) the RECONCILE that proves the code's declared
# work equal to the rows (A2 + the site-vs-row label check, precision b), refusing on divergence.

#: The record-derived act set {seam_kind: {"label", "meaning"}} the last build folded from the rows.
#: None until a build derives it. NEVER a stored status: it is re-folded from the record on every
#: build and re-derivable at any time (delete-and-regenerate). The store-free `ACT_KINDS` above is
#: the closed-set gate; THIS is the record's own act set, the single source of the kinds' contracts.
_DERIVED_ACT_KINDS = None


def _site_kinds():
    """The set of act kinds the CODE actually uses — read from the declare_act SITES (the ACTS table).
    This is the immutable code half (source B of the reconcile and the wake check); it never changes
    with the record, so comparing the rows against it is a genuine reconciliation, not a match that
    cannot fail."""
    return frozenset(kind for _method, (kind, _label) in HostSeam.ACTS.items())


def reconcile_derived_act_kinds(derived):
    """Reconcile the record-derived act set against the code's declared work — REFUSING on divergence
    (A2 + precision b; the check can fail). The RECORD is the single source; the code SITES are proven
    equal to it or the build refuses.
      A2 — THE KIND SETS MATCH: the kinds folded from the rows equal the kinds the declare_act sites
           use; a kind in the code path ABSENT from the rows, or a kind in the rows absent from the
           code path, is CAUGHT (the derivation is the single source).
      precision (b) — SITE-VS-ROW LABELS: every declare_act SITE's declared label equals the label its
           kind's row carries; a site whose label disagrees with its row is CAUGHT (30 sites, 12 kinds).
    Raises HostSeamError on any divergence."""
    row_kinds = frozenset(derived)
    site_kinds = _site_kinds()
    if row_kinds != site_kinds:
        raise HostSeamError(
            "the act-kind rows diverge from the seam's declared act set — rows-only=%s code-only=%s "
            "(the derivation is the single source; a kind in one absent from the other is caught, A2)"
            % (sorted(row_kinds - site_kinds), sorted(site_kinds - row_kinds)))
    for method, (kind, label) in HostSeam.ACTS.items():
        row_label = derived[kind]["label"]
        if label != row_label:
            raise HostSeamError(
                "the site %r declares label %r for act kind %r but the kind's row carries %r — a site "
                "whose label disagrees with its kind's row is caught (precision b, archi :3993)"
                % (method, label, kind, row_label))


def install_derived_act_kinds(derived):
    """Install the record-derived act set (the build's product), returning the prior (for restore in a
    delete-and-regenerate). Reconciles first: a divergent set never installs (A2 + precision b)."""
    global _DERIVED_ACT_KINDS
    reconcile_derived_act_kinds(derived)
    prior = _DERIVED_ACT_KINDS
    _DERIVED_ACT_KINDS = {k: dict(v) for k, v in derived.items()}
    return prior


def derived_act_kinds():
    """The record-derived act set the last build installed (None if no build has derived it yet)."""
    return _DERIVED_ACT_KINDS


def clear_derived_act_kinds():
    """DELETE the built act set — the delete half of delete-and-regenerate (A1). Returns the prior."""
    global _DERIVED_ACT_KINDS
    prior = _DERIVED_ACT_KINDS
    _DERIVED_ACT_KINDS = None
    return prior
