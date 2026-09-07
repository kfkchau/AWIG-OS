# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""M2 (bridge stance 3): a real directory tree SERVED FROM THE RECORD (EP-25 W2/W3/W4/W5).

The record machine stops shadowing and starts serving. A program saves a file and that
save IS a gated, rule-cited, replayable decision; kill every derived structure, replay the
record, and the same filesystem comes back.

THREE LAWS THIS FILE EXISTS TO HOLD, each one mechanical rather than intended:

  RECORD-BEFORE-EFFECT (K1). For every DECISION- and LAW-class call, `self.gate.execute`
  returns only after the covering record is DURABLY appended (`store._append` writes the
  line, flushes and fsyncs), and the derived caches are updated and the reply released only
  AFTER that return. There is no path in this file that mutates served state before its
  record exists. Interrupted between append and reply: the record stands and restart heals
  record -> effect, because the served state is a fold of the record. Interrupted before
  append: nothing happened, in record OR effect. The direction is never effect-without-record.
  The one place this needs saying carefully is a coalesced write, and it is said at
  `_close_burst`.

  THE CLASS MAP IS THE GATING CONTRACT (K3, design/10 §6). Gate everything and the mount
  dies at rate; gate nothing and custody is fiction. So the map decides, row by row:
  DECISION and LAW calls cross the gate and append; CACHE-only calls (getattr, readdir,
  access, readlink, statfs, getxattr, listxattr, fsync-as-barrier) consult views and append
  NOTHING; read traffic is a STREAM aggregate whose caller always receives exact bytes.

  THE HOST FILESYSTEM IS NEVER ASKED WHAT A FILE IS. Not its content, not its mode, not its
  existence, not its children. The only host read is a content-addressed blob fetched BY THE
  HASH THE RECORD CARRIES. That is the whole difference from the journaling filesystem this
  campaign exists to refuse: there, truth lives in the host filesystem and the record is
  decoration; here the store is the definitive and the tree is a view.
"""

import ctypes
import errno
import fcntl
import os
import re
import stat as statmod
import threading
import time

from fuse import FuseOSError, Operations  # fusepy — an ADAPTER dependency, outside the core

from kernel.errors import OpError

from . import custody
from .custody import KIND_DIR, KIND_FILE, KIND_FIFO, KIND_LINK, ROOT_INO

#: The mount's own window identity, recorded in every act's provenance so a reader can tell
#: WHICH port asserted the uid it is looking at (the EP-22 window@version precedent).
WINDOW = "fuse-port@1"

#: "no such attribute". Linux spells it ENODATA; the BSD spelling ENOATTR is absent from
#: Python's errno on Linux, so it is resolved ONCE here rather than at each raise site — a
#: `getattr(errno, "ENODATA", errno.ENOATTR)` evaluates its own default eagerly and raises
#: AttributeError instead of returning the errno, inside the very handler meant to report one.
ENOATTR = getattr(errno, "ENODATA", None) or getattr(errno, "ENOATTR", errno.ENOENT)

#: WHAT A HALTED MOUNT STILL DOES. "The mount goes read-only" is the failure book's remedy,
#: and read-only means no STATE CHANGE — it does not mean no recording. These four acts move
#: nothing in the namespace or in any file's content, so none of them can widen a divergence,
#: and refusing them would do two wrong things at once: it would stop a halted mount serving
#: reads at all (an open is a DECISION, so blocking it blocks `cat`), and it would make custody
#: go quiet exactly when something has gone wrong. Recording less is never the resolution (K3);
#: that holds during a halt as much as during ordinary running.
_PERMITTED_WHILE_HALTED = ("FILE-OPEN", "FILE-CLOSE", "FILE-READ-AGGREGATE", "CUSTODY-HALT")

#: THE PORT'S OWN RESERVED NAME. libfuse honours the POSIX open-file contract for a path-
#: addressed filesystem by renaming an unlinked-but-open file aside as `.fuse_hidden%08x%08x`
#: and unlinking that name when the last descriptor closes. The mechanism is POSIX-required
#: and correct; what it must NOT do is stand in the record IN PLACE OF the decision the actor
#: took, which was an unlink (EP-25 ADDENDUM 9 C2). Recognised by its exact shape rather than
#: by a prefix, because this is a name form the port reserves, not a name a caller chose.
_HIDDEN_NAME = re.compile(r"^\.fuse_hidden[0-9a-fA-F]{16}$")

#: `struct flock` as the platform lays it out (x86-64 Linux, glibc). libfuse hands the high
#: level API a pointer to one, and fusepy passes that pointer through as an address — so the
#: port reads it here rather than guessing at a packed layout. The field offsets are asserted
#: in the suite rather than trusted: a misread flock would grant the wrong bytes silently.
class _Flock(ctypes.Structure):
    _fields_ = [("l_type", ctypes.c_short), ("l_whence", ctypes.c_short),
                ("l_start", ctypes.c_int64), ("l_len", ctypes.c_int64),
                ("l_pid", ctypes.c_int32)]


#: design/10 §6's fcntl row, split as that row splits itself: F_GETLK is a CACHE read,
#: F_SETLK / F_SETLKW are DECISIONS. The names are resolved from `fcntl` rather than written
#: as numbers, which is the same discipline the conformance rows follow.
_F_GETLK, _F_SETLK, _F_SETLKW = fcntl.F_GETLK, fcntl.F_SETLK, fcntl.F_SETLKW
_LTYPE = {fcntl.F_RDLCK: "read", fcntl.F_WRLCK: "write", fcntl.F_UNLCK: "unlock"}


class Halted(RuntimeError):
    """The assume has been halted (FS-LAW-DIVERGENCE-HALT). The mount serves reads and
    refuses every state-changing call with EROFS until a human resolves it."""


class RecordsFS(Operations):
    """A FUSE filesystem whose every governed act is a record and whose every answer is a
    view. Single-threaded by construction (`nothreads=True` at the mount): the store is
    single-writer, and this campaign keeps ONE store writer — the S5 sequencer is not built
    and is not smuggled in here."""

    def __init__(self, store, gate, views, blobs, *, shadow_every=0):
        self.store = store
        self.gate = gate
        self.views = views
        self.blobs = blobs
        self.state = custody.CustodyState()
        self.state.applied = 0
        self._rebuild_from_record()
        # The store's own on-append listener keeps the derived caches current. It is the ONE
        # place the incremental copy advances, so a record that reaches the store and not the
        # cache is impossible by construction rather than by discipline.
        store.on_append(self._on_append)
        self._fh = 0
        self._open = {}          # fh   -> {"ino","path","flags"}
        self._burst = {}         # fh   -> {"bytes": bytearray, "events": int, "ino", "path"}
        self._reads = {}         # ino  -> {"reads": int, "bytes": int, "path": str}
        #: The port's own hidden aliases (C2): a name libfuse minted to keep an unlinked-but-
        #: open file addressable, pointing at the inode the record already minted. IN-FLIGHT,
        #: like the fd table it belongs to — it lives only while a descriptor does, and it is
        #: deliberately NOT part of the served namespace, so `ls` does not show it and neither
        #: does the fold. The record says the name was unlinked, and that is what is true.
        self._hidden = {}        # hidden path -> ino
        #: Who holds exclusivity, folded from the lock decisions by the listener below.
        self.locks = custody.LockTable()
        self._lock = threading.Lock()
        self.halted = None
        self.shadow_every = shadow_every   # 0 = check at every quiescent point
        self._acts = 0
        self.counters = {"gated": 0, "cache": 0, "coalesced_writes": 0, "write_events": 0,
                         "shadow_checks": 0}

    # =================================================================================
    # the record side
    # =================================================================================
    def _rebuild_from_record(self):
        self.state = custody.fold(self.store.all())

    def _on_append(self, record):
        self.state.apply(record)
        self.state.applied += 1
        # The lock fold advances on the SAME listener, for the same reason: a lock that the
        # port believes is held while no record says so is exactly the gap C1 closed.
        self.locks.apply(record)

    def _ctx(self):
        """The caller at the port. `fuse_get_context()` is the KERNEL's assertion about who
        is calling; it is evidence, and it is recorded as evidence."""
        from fuse import fuse_get_context
        try:
            uid, gid, pid = fuse_get_context()
        except Exception:
            uid, gid, pid = os.getuid(), os.getgid(), os.getpid()
        return int(uid), int(gid), int(pid)

    def _actor(self, uid):
        """THE ACTING ACTOR IS DERIVED, and this is the second named wrong reference refused
        in one method. A uid<->account SYNCHRONIZED TABLE would be a stored identity status
        (P2 dead). Instead the mapping is recorded ACTS (MAP-UID) and the answer is a FOLD
        over them, recomputed every act — exactly the EP-15 invoker/actor split, where the
        kernel-asserted uid is EVIDENCE and the actor is derivation. A uid with no recorded
        mapping still ACTS, under the name the port can honestly assert, and provenance says
        so: under the openness grant everything passes on day one, attribution honest,
        narrowing later and never this round's."""
        mapped = None
        for e in self.store.by_action("MAP-UID"):
            p = e.get("payload") or {}
            if custody._int(p.get("uid")) == uid:
                mapped = p.get("account")
        return mapped or ("uid:%d" % uid)

    def _prov(self):
        """The envelope's provenance: WHO the record says acted, and the EVIDENCE the port
        asserted. The uid is not an identity here — it is a fact the kernel stated, recorded
        as one, through a named window at a named version."""
        uid, gid, pid = self._ctx()
        actor = self._actor(uid)
        return actor, {
            "asserted_by": self.views.resolve_asserted_by(actor),
            "source": "fuse-port",
            "could_read": [],
            "window": WINDOW,
            "uid": uid, "gid": gid, "pid": pid,
        }

    def _carries_port_provenance(self, op):
        """Does this op DECLARE that a parameter supplies the envelope's provenance? Read from
        the op's OWN definition record, never from a list in this file — the EP-16
        authority-regime precedent, and the reason the answer moves when the founding does.

        EVERY CUSTODY OP NOW DECLARES IT, in one of two forms, and the two are named rather
        than blurred. The thirteen ops this EP creates declare it REQUIRED, so every act
        through them carries the port's uid, gid, pid and window as recorded evidence. The five
        it inherits from campaign 1 — create, write, link, unlink, perm — declare it DEFAULTED
        (EP-27B, closing this EP's R-1): a call that supplies the parameter carries the port
        evidence exactly as the thirteen do, and a call that omits it falls back to the store's
        own value instead of being refused. That fallback is what lets those five keep their
        pre-existing engine caller (`kernel/syscall_port.py`, which supplies no provenance)
        conforming — declaring the parameter REQUIRED there would have made that caller
        nonconforming, which is why EP-25 raised it as a `src/kernel/` FINDING rather than a
        patch site. EP-27B supplied the defaulted distinction that closes it, so on those five
        a call without port evidence records the DERIVED actor (the uid resolved through
        recorded mapping acts, written to provenance.asserted_by by the gate) rather than raw
        port evidence. The engine question EP-25 stated — whether the provenance router should
        refuse on absence the way the occurrence-time router must — is answered DEFAULTED for
        these five: a minted occurrence_time would be a fabricated observation, while a
        provenance derived from the acting actor says "the system asserted this", which is
        true."""
        d = (self.views.op_definitions().get(op) or {}).get("definition") or {}
        return bool(d.get("provenance_param"))

    def _act(self, op, **params):
        """Cross the gate. Returns only once the covering record is DURABLY appended — which
        is what makes every caller of this method record-before-effect without having to
        remember to be."""
        if self.halted and op not in _PERMITTED_WHILE_HALTED:
            raise FuseOSError(errno.EROFS)
        actor, prov = self._prov()
        if self._carries_port_provenance(op):
            params["provenance"] = prov
        try:
            rec = self.gate.execute(op, actor, params)
        except OpError as e:
            # A REFUSAL (design/10 §11.1a class 1): the gate decided no, recorded a rule-citing
            # decision, and the caller sees the LINUX errno — never a governance code. "A denial
            # cites errno to userland and a rule to the record" (design/10 §11.1).
            raise FuseOSError(_errno_for(e)) from None
        self._acts += 1
        self.counters["gated"] += 1
        return rec

    def _refuse(self, op, rule, message):
        """A REFUSAL THIS PORT DECIDES, recorded before it is returned (design/10 §11.1a
        class 1; P4). The gate's own `refuse` is what appends it — the gate stays the sole
        appender, and the refusal lands in the estate's standing shape (an `op-refused`
        record naming the op, carrying the rule and the reason) rather than in a bespoke
        one. The caller then sees the LINUX errno for the precondition, never a governance
        code: a denial cites errno to userland and a rule to the record.

        The refusals routed through here are the ones the port DECIDES on recorded state —
        today, a lock another owner holds. A POSIX precondition the view answers (ENOENT for
        a name that is not there, EEXIST for one that is) is an ABSENCE, not a refusal, and
        §11.1a is explicit that a record appearing for one of those would be the failure."""
        try:
            self.gate.refuse(self._prov()[0], op, rule, message)
        except OpError as e:
            raise FuseOSError(_errno_for(e)) from None

    # =================================================================================
    # the derived reads (CACHE-only: these append NOTHING, and that is the K3 contract)
    # =================================================================================
    def _node(self, path):
        node = self.state.lookup(path)
        if node is None:
            node = self.state.inodes.get(self._hidden.get(custody._norm(path)))
        if node is None:
            raise FuseOSError(errno.ENOENT)
        return node

    def _content(self, ino):
        """A file's exact bytes: the OPEN BURST if one is in flight (that is the page cache,
        and POSIX has never promised an un-fsynced write is durable), else the blob the
        record named. Never the host filesystem answering for a path."""
        for b in self._burst.values():
            if b["ino"] == ino:
                return bytes(b["bytes"])
        node = self.state.inodes.get(ino)
        if node is None or not node.content_hash:
            return b""
        return self.blobs.get(node.content_hash)

    def getattr(self, path, fh=None):
        self.counters["cache"] += 1
        # AN OPEN DESCRIPTOR ANSWERS FOR ITSELF. Identity here is the inode the record
        # minted, never the string it happens to be reachable by (the same derivation the
        # hard-link case rests on) — so an `fstat` of a file whose name has been unlinked
        # still answers, which is the POSIX contract for an open file with no name left.
        node = None
        if fh is not None and fh in self._open:
            node = self.state.inodes.get(self._open[fh]["ino"])
        node = node or self._node(path)
        size = node.size
        for b in self._burst.values():
            if b["ino"] == node.ino:
                size = len(b["bytes"])
        now = time.time()
        return {
            "st_mode": self.state.mode(node),
            "st_nlink": self.state.nlink(node.ino),
            "st_size": size,
            "st_ino": node.ino,
            # THE FOLD'S ANSWER FOR EVERY INODE A RECORD DESCRIBES, AND THE SERVER'S OWN
            # IDENTITY FOR THE ONE IT DOES NOT.
            #
            # This read `node.uid or os.getuid()` until 2026-07-29, and that ONE expression
            # was doing two jobs that have nothing to do with each other. As a fallback for
            # every inode it is the construct design/10 §11.4b rules has nowhere to live: a
            # second source of truth for ownership, standing behind the first, agreeing with
            # it on every test that ever ran. It was invisible while the fold was broken
            # (every created file folded back owned by root and the fallback happened to
            # equal the creator — EP-28 R-2), and once the fold was repaired it became a live
            # contradiction: a file the record says root created was reported as owned by
            # whoever ran the mount, because `0 or os.getuid()` is `os.getuid()`. Root is a
            # real owner and 0 is a real uid; reading it as "unset" is the defect in one
            # operator.
            #
            # ITS OTHER JOB WAS LEGITIMATE AND REMOVING IT WHOLESALE BROKE THE MOUNT. The
            # ROOT is the one inode NO RECORD DESCRIBES — the fold mints inode 1 with no
            # FILE-CREATE behind it — so the fold has nothing to say about who owns it and
            # answers 0. Reporting that made the mount root a 0755 directory owned by uid 0
            # to a caller who is not uid 0, and the kernel denied every write into it before
            # the server was ever asked. Eight of EP-25's unmodified-program rows went red,
            # which is those rows doing exactly their job.
            #
            # SO THE ANSWER IS SCOPED TO THE QUESTION, and it is the same answer the
            # in-kernel module gives: `govos_fill_super` mints the root with the brain's own
            # uid, captured at attach, precisely because no record states one (the residence
            # audit's row 8). Both stances now answer the same unrecorded question the same
            # way, and neither has a default standing behind a question the record DOES
            # answer.
            "st_uid": os.getuid() if node.ino == ROOT_INO else node.uid,
            "st_gid": os.getgid() if node.ino == ROOT_INO else node.gid,
            "st_ctime": _ts(node.ctime, now),
            "st_mtime": _ts(node.mtime, now),
            "st_atime": _ts(node.atime, now),
            "st_blocks": (size + 511) // 512,
        }

    def readdir(self, path, fh):
        self.counters["cache"] += 1
        node = self._node(path)
        if node.kind != KIND_DIR:
            raise FuseOSError(errno.ENOTDIR)
        return [".", ".."] + self.state.children(path)

    def readlink(self, path):
        self.counters["cache"] += 1
        node = self._node(path)
        if node.kind != KIND_LINK:
            raise FuseOSError(errno.EINVAL)
        return node.target

    def access(self, path, amode):
        self.counters["cache"] += 1
        self._node(path)
        return 0

    def statfs(self, path):
        self.counters["cache"] += 1
        return {"f_bsize": 4096, "f_frsize": 4096, "f_blocks": 1 << 20,
                "f_bfree": 1 << 19, "f_bavail": 1 << 19,
                "f_files": 1 << 16, "f_ffree": 1 << 15, "f_favail": 1 << 15,
                "f_namemax": 255}

    def getxattr(self, path, name, position=0):
        self.counters["cache"] += 1
        node = self._node(path)
        v = node.xattrs.get(name)
        if v is None:
            raise FuseOSError(ENOATTR)
        return v.encode("utf-8") if isinstance(v, str) else v

    def listxattr(self, path):
        self.counters["cache"] += 1
        return list(self._node(path).xattrs)

    # =================================================================================
    # the governed acts (DECISION / LAW: record first, then effect, then reply)
    # =================================================================================
    # THE PORT'S STAMP IS RETIRED, AND WHAT REPLACES IT IS THIS PORT'S OWN OLD IDEA
    # (EP-28S). `_mint_ino` stood here and read `self.state.next_ino` at four call sites —
    # create, the mknod path, mkdir and symlink. Its SHAPE was right and it was the sound
    # regime in this estate: an identity that is an ALLOCATION ORDER cannot collide, which
    # is exactly what the path-derived regime the kernel port adopted at 1.14.0 cannot say.
    # Its SOURCE was the defect. A private counter lives in THIS PROCESS and dies with it,
    # while the records citing the numbers it handed out do not, so two ports serving one
    # record file could hand out one number twice and nothing in the record would know.
    #
    # SO THE REPAIR IS A SOURCE SWAP AND NOT A REMOVAL, and calling this "legacy awaiting
    # deletion" would have aimed the work at the wrong file. The founding now declares
    # `mints_from: record_coordinate` on all three minting ops; the fold derives the formal
    # name from the birth act's own position in the record — allocation order again, taken
    # from the ONE allocator that outlives every process, the store's own append. This port
    # supplies no identity at all, so there is nothing here to disagree with the record.
    #
    # IT ALSO BYPASSED THE ALLOCATOR'S ONE DOOR, WHICH IS REPORTED RATHER THAN LEFT.
    # `custody.mint_ino` exists to REFUSE in a namespace whose identities it has not seen
    # (`AllocatorNotTracking`), and this method touched `state.next_ino` directly — so that
    # refusal could never fire for the only port that stamped, and in a world holding one
    # derived identity `next_ino` is None and `None += 1` would have raised a TypeError out
    # of a create. Both go with the stamp.
    def create(self, path, mode, fi=None):
        if self.state.exists(path):
            raise FuseOSError(errno.EEXIST)
        self._parent_must_be_a_directory(path)
        # THE NUMBER IS READ BACK FROM THE FOLD AND NEVER COMPUTED HERE. `_act` returns only
        # once the record is durably appended and the on-append listener has folded it, so
        # the node exists by the next line — and reading it through the same door every other
        # method uses keeps this port with ZERO derivations of its own. A second derivation
        # agreeing with the fold today is a convention wearing a boundary's name (§A52).
        self._act("FILE-CREATE", path=path, perm=oct(mode & 0o7777)[2:])
        return self._open_fd(path, self._node(path).ino, os.O_WRONLY)

    def mknod(self, path, mode, dev):
        """A FIFO IS NOT A DEVICE NODE, and the difference decides who serves it.

        A device node names a driver by major/minor: it is a CAPABILITY reference, and
        capability is the device subsystem's (design/24, EP-29). This mount refuses one,
        honestly and visibly, because serving it would be claiming custody of something it
        cannot record. A FIFO names no driver. It is a name and a type in this namespace,
        and its data path is the kernel's own pipe — which never reaches a filesystem at
        all. So its whole custody is what this mount already governs: the name, the type
        and the permission, each a recorded decision, replayable like any other create.

        The line is drawn at the CAPABILITY, not at the S_IFMT bit being unfamiliar."""
        if statmod.S_ISREG(mode) or statmod.S_ISFIFO(mode):
            if self.state.exists(path):
                raise FuseOSError(errno.EEXIST)
            self._parent_must_be_a_directory(path)
            self._act("FILE-CREATE", path=path,
                      perm=oct(mode & 0o7777)[2:],
                      node_type="fifo" if statmod.S_ISFIFO(mode) else "file")
            return 0
        raise FuseOSError(errno.EPERM)

    def mkdir(self, path, mode):
        if self.state.exists(path):
            raise FuseOSError(errno.EEXIST)
        self._parent_must_be_a_directory(path)
        self._act("FILE-MKDIR", path=path,
                  perm=oct(mode & 0o7777)[2:])
        return 0

    def rmdir(self, path):
        node = self._node(path)
        if node.kind != KIND_DIR:
            raise FuseOSError(errno.ENOTDIR)
        if self.state.children(path):
            raise FuseOSError(errno.ENOTEMPTY)
        self._act("FILE-RMDIR", path=path)
        return 0

    def unlink(self, path):
        norm = custody._norm(path)
        if norm not in self.state.names and norm in self._hidden:
            # THE MECHANISM COMPLETING, NOT A SECOND DECISION. This is the port unlinking
            # the alias it minted for an unlink ALREADY recorded below — the last descriptor
            # has closed, so the alias goes. Nothing the record governs changes here: the
            # name left the namespace at the decision, and this alias was never in it. So
            # nothing is appended, and that is K3 rather than a gap — a record here would
            # say the actor unlinked a name it never named.
            self._hidden.pop(norm, None)
            return 0
        node = self._node(path)
        if node.kind == KIND_DIR:
            raise FuseOSError(errno.EISDIR)
        # THE BLOB'S HISTORY PERSISTS IN THE LEDGER WHEN THE LAST LINK DROPS, and the POSIX
        # contract stays exact for the living namespace (design/10 §6, unlink row). Nothing
        # is erased: deletion is namespace removal, so "show me this directory as of last
        # Tuesday" still answers. An open fd keeps reading, because its content comes from
        # the recorded hash and a hash does not stop resolving when a name does.
        self._act("FILE-UNLINK", path=path)
        return 0

    def _is_port_rename_aside(self, old, new):
        """Is this rename the PORT's own mechanism rather than the caller's decision?

        libfuse serves a path-addressed filesystem, so it cannot leave an unlinked file
        nameless while a descriptor is open on it: it renames the file aside to a name it
        reserves and unlinks that name when the last descriptor closes. Four conditions
        have to hold at once for that to be what is happening, and all four are read from
        state this port already has:

          the destination is the port's reserved name FORM (not a prefix — the exact
          `.fuse_hidden` + 16 hex digits libfuse mints); the destination does not exist;
          the rename stays inside the source's own directory (libfuse hides in place); and
          THE SOURCE IS OPEN RIGHT NOW, which is the only condition under which libfuse
          does this at all.

        HONEST CAP, because a name test can always be gamed: a caller that deliberately
        renames its own open file onto a 16-hex `.fuse_hidden` name in the same directory
        has its act recorded as the unlink this mechanism serves. That name form is the
        port's reserved namespace rather than a caller's choice, so the cap is that the
        port owns its own names — but it is a cap, and it is stated rather than discovered.
        """
        if not _HIDDEN_NAME.match(custody.basename(new)):
            return False
        if self.state.exists(new):
            return False
        if custody.parent_of(old) != custody.parent_of(new):
            return False
        ino = self.state.names.get(custody._norm(old))
        return any(o["ino"] == ino for o in self._open.values())

    def symlink(self, target, source):
        # fusepy hands (link_path, target). The link is `target` here; `source` is what it
        # points at — the argument names are libfuse's, and they read backwards.
        if self.state.exists(target):
            raise FuseOSError(errno.EEXIST)
        self._parent_must_be_a_directory(target)
        self._act("FILE-SYMLINK", path=target, target=source)
        return 0

    def link(self, target, source):
        node = self.state.lookup(source)
        if node is None:
            raise FuseOSError(errno.ENOENT)
        if node.kind == KIND_DIR:
            raise FuseOSError(errno.EPERM)
        if self.state.exists(target):
            raise FuseOSError(errno.EEXIST)
        # A HARD LINK IS A SECOND NAME FOR ONE INODE, and because content hangs off the inode
        # rather than off the path, writing through one name is visible through the other
        # with no reconciliation anywhere. That is the derivation doing the work: identity is
        # what the record minted, not the string it happens to be reachable by.
        self._act("FILE-LINK", target_path=source, new_path=target)
        return 0

    def rename(self, old, new):
        self._node(old)
        self._parent_must_be_a_directory(new)
        existing = self.state.lookup(new)
        if existing is not None and existing.kind == KIND_DIR and self.state.children(new):
            raise FuseOSError(errno.ENOTEMPTY)
        self._flush_paths((old,))
        if self._is_port_rename_aside(old, new):
            # THE RECORD SAYS WHAT THE ACTOR DECIDED, AND THE MECHANISM SITS BENEATH IT
            # (EP-25 ADDENDUM 9 C2). The caller decided to unlink an open file; the port
            # renamed it aside to honour the POSIX open-file contract. Recording the rename
            # as the governance act showed the MECHANISM and not the DECISION — a reader who
            # was not there would see a rename nobody asked for and no unlink at all. So the
            # decision is recorded as the unlink it is, carrying the aside-name as mechanism.
            ino = self.state.names.get(custody._norm(old))
            self._act("FILE-UNLINK", path=old,
                      mechanism="fuse-rename-aside", hidden_path=custody._norm(new))
            # The alias is IN-FLIGHT and outside the served namespace: the name is gone for
            # every caller (which is what POSIX says happened), and the port can still reach
            # the inode to serve the descriptor that is still open on it.
            self._hidden[custody._norm(new)] = ino
            return 0
        self._act("FILE-RENAME", path=old, new_path=new)
        return 0

    def chmod(self, path, mode):
        self._node(path)
        self._act("FILE-PERM", path=path, inode=self._node(path).ino,
                  perm=oct(mode & 0o7777)[2:])
        return 0

    def chown(self, path, uid, gid):
        node = self._node(path)
        params = {"path": path, "inode": node.ino}
        if uid != -1 and uid != 0xFFFFFFFF:
            params["uid"] = uid
        if gid != -1 and gid != 0xFFFFFFFF:
            params["gid"] = gid
        self._act("FILE-CHOWN", **params)
        return 0

    def utimens(self, path, times=None):
        node = self._node(path)
        atime, mtime = times or (time.time(), time.time())
        self._act("FILE-TIMES", path=path, inode=node.ino, atime=atime, mtime=mtime)
        return 0

    def setxattr(self, path, name, value, options, position=0):
        node = self._node(path)
        text = value.decode("utf-8", "surrogateescape") if isinstance(value, bytes) else value
        # THE SYSCALL IS TRANSPORT; THE CONTENT DECIDES THE CLASS (design/10 §11.1b, ruled at
        # EP-25 ADDENDUM 3). A permission-bearing attribute is a rule with a one-file scope,
        # so setting one is law-making and records as LAW — with everything that follows for a
        # law-family record. Every other attribute write is an ordinary DECISION. One syscall,
        # two classes, decided by the attribute NAMESPACE.
        op = "FILE-XATTR-LAW" if custody.is_law_xattr(name) else "FILE-XATTR-SET"
        self._act(op, path=path, inode=node.ino, name=name, value=text)
        return 0

    def removexattr(self, path, name):
        node = self._node(path)
        if name not in node.xattrs:
            raise FuseOSError(ENOATTR)
        self._act("FILE-XATTR-REMOVE", path=path, inode=node.ino, name=name)
        return 0

    def truncate(self, path, length, fh=None):
        node = self._node(path)
        if node.kind == KIND_DIR:
            raise FuseOSError(errno.EISDIR)
        self._flush_paths((path,))
        cur = self._content(node.ino)
        new = cur[:length] + b"\x00" * max(0, length - len(cur))
        self._act("FILE-TRUNCATE", path=path, inode=node.ino, content=new)
        return 0

    # ---- open / read / write / close -------------------------------------------------
    def _open_fd(self, path, ino, flags):
        self._fh += 1
        fh = self._fh
        self._open[fh] = {"ino": ino, "path": path, "flags": flags}
        return fh

    def open(self, path, flags):
        node = self._node(path)
        if node.kind == KIND_DIR and (flags & (os.O_WRONLY | os.O_RDWR)):
            raise FuseOSError(errno.EISDIR)
        # THE EXPLICIT CUSTODY GRANT (design/10 §6, open row): permission checked, recorded,
        # rule-cited. It is a DECISION and it is the reason an open costs a gated act.
        self._act("FILE-OPEN", path=path, inode=node.ino, flags=int(flags))
        fh = self._open_fd(path, node.ino, flags)
        if flags & os.O_TRUNC:
            self._act("FILE-TRUNCATE", path=path, inode=node.ino, content=b"")
        return fh

    def read(self, path, size, offset, fh):
        """STREAM for the audit aggregate; the CALLER RECEIVES EXACT BYTES. §11.5 forbids
        inferring a lossy data path from the classification, and nothing here samples: the
        sampling is of the OBSERVABILITY VIEW, which is the aggregate appended at the window's
        close, and never of what is handed back."""
        ino = self._open.get(fh, {}).get("ino") or self._node(path).ino
        data = self._content(ino)[offset:offset + size]
        agg = self._reads.setdefault(ino, {"reads": 0, "bytes": 0, "path": path})
        agg["reads"] += 1
        agg["bytes"] += len(data)
        self._maybe_close_read_window(ino)
        return data

    def write(self, path, data, offset, fh):
        if self.halted:
            raise FuseOSError(errno.EROFS)
        node = self._node(path)
        b = self._burst.get(fh)
        if b is None:
            b = self._burst[fh] = {"bytes": bytearray(self._content(node.ino)),
                                   "events": 0, "ino": node.ino, "path": path}
        buf = b["bytes"]
        if offset > len(buf):
            buf.extend(b"\x00" * (offset - len(buf)))
        buf[offset:offset + len(data)] = data
        b["events"] += 1
        self.counters["coalesced_writes"] += 1
        self._maybe_close_burst(fh)
        return len(data)

    def flush(self, path, fh):
        # flush() fires on every close(2), including the last one of a dup'd descriptor. The
        # burst closes here so that a close ALWAYS leaves the record carrying every byte.
        self._close_burst(fh)
        # ...and the POSIX lock rule fires here too, for the same reason flush exists: the
        # caller is closing a descriptor for this file, and POSIX releases that process's
        # locks on the file when ANY descriptor for it is closed. Recorded, because a span
        # of exclusivity that ends without a record cannot be reconstructed (C1).
        self._release_locks(fh, "close-releases-locks")
        return 0

    def fsync(self, path, datasync, fh):
        """fsync is a BARRIER, not a decision (design/10 §6, fsync row: "the writes it commits
        were already DECISIONS"). In AWIG OS the record IS the durability substrate, so the
        barrier's whole content is: make sure every covering write-decision is durable, then
        return. When no burst is open there is literally nothing to do and NOTHING IS
        APPENDED, which is the CACHE-only classification holding. When a burst IS open, the
        covering decision it accumulated is appended here — the row's own note is what
        licenses that ("fsync returns after the covering write-decisions are durable"), and
        the record that lands is the WRITE's, arriving under the recorded coalescing policy,
        not a decision fsync made."""
        self._close_burst(fh)
        return 0

    def release(self, path, fh):
        self._close_burst(fh)
        info = self._open.pop(fh, None)
        if info is not None:
            self._act("FILE-CLOSE", path=info["path"], inode=info["ino"])
        self._shadow_check()
        return 0

    def destroy(self, path):
        for fh in list(self._burst):
            self._close_burst(fh)
        for ino in list(self._reads):
            self._close_read_window(ino)

    # =================================================================================
    # exclusivity (EP-25 ADDENDUM 9 C1): a lock is a governed act, and so is its refusal
    # =================================================================================
    #
    # WHAT WAS WRONG, said plainly because it is the finding this section closes. This
    # mount implemented no lock operation, so libfuse never advertised the capability and
    # THE KERNEL GRANTED LOCKS LOCALLY: a caller held exclusivity the record had no
    # knowledge of, and — worse in governance terms — a DENIED lock is a refusal, and that
    # refusal was issued by the kernel, uncited and unrecorded. design/10 §6 classes both
    # `F_SETLK` and `flock` DECISION. Implementing `lock` is what makes the kernel hand
    # POSIX record locks to this port instead of settling them behind it.
    #
    # WHAT THIS PORT CANNOT REACH, stated here rather than left to be discovered. BSD
    # `flock(2)` does not arrive: the adapter's `fuse_operations` declaration carries no
    # `flock` slot, so libfuse never advertises FUSE_CAP_FLOCK_LOCKS and the kernel keeps
    # settling BSD locks locally, exactly as it did for POSIX locks before this section.
    # That is an ADAPTER limit rather than a FUSE limit (libfuse 2.9 carries the entry),
    # and it is raised rather than worked around: re-declaring a third-party ABI struct
    # from inside this file to reach one function pointer is not a thing to do quietly.

    def _lock_target(self, path, fh):
        """(inode, owner) for a lock request. The owner is the pid the KERNEL asserted for
        this request — evidence, exactly as the uid is (K6), and never a table. HONEST CAP:
        the kernel's own owner token (`lock_owner`, which distinguishes two open file
        descriptions inside one process) is not exposed by this adapter's non-raw file-info
        path, so an OFD lock taken twice in one process does not conflict with itself here
        where POSIX says it would. Named, not papered over."""
        info = self._open.get(fh)
        ino = info["ino"] if info else self._node(path).ino
        return ino, self._ctx()[2]

    def lock(self, path, fh, cmd, lock):
        if not lock:
            raise FuseOSError(errno.EINVAL)
        fl = _Flock.from_address(lock)
        if fl.l_whence != os.SEEK_SET:
            # libfuse resolves the range to absolute bytes before it reaches a filesystem,
            # so anything else is a shape this port cannot honestly interpret — and a lock
            # granted over the wrong bytes is worse than one refused.
            raise FuseOSError(errno.EINVAL)
        ino, owner = self._lock_target(path, fh)
        start, length = int(fl.l_start), int(fl.l_len)
        want = _LTYPE.get(fl.l_type)
        if want is None:
            raise FuseOSError(errno.EINVAL)

        if cmd == _F_GETLK:
            # CACHE-only (design/10 §6, the F_GETLK half of the fcntl row): a query answered
            # from the fold, appending NOTHING. A holder never conflicts with itself, which
            # is why asking about your own lock answers "unlocked" — the POSIX answer.
            self.counters["cache"] += 1
            clash = self.locks.conflict(ino, owner, want, start, length)
            if clash is None:
                fl.l_type = fcntl.F_UNLCK
            else:
                fl.l_type = fcntl.F_WRLCK if clash.exclusive else fcntl.F_RDLCK
                fl.l_start, fl.l_len = clash.start, clash.length
                fl.l_pid = int(clash.owner or 0)
            return 0

        if cmd not in (_F_SETLK, _F_SETLKW):
            raise FuseOSError(errno.EINVAL)

        if want == "unlock":
            self._release_locks(fh, "fcntl-unlock", ino=ino, owner=owner,
                                start=start, length=length)
            return 0

        clash = self.locks.conflict(ino, owner, want, start, length)
        if clash is not None:
            # THE REFUSAL IS THE GOVERNED HALF, and it is the half that was missing. The
            # caller sees the POSIX errno for the precondition — EAGAIN, unchanged at the
            # port — and the record carries FS-LAW-LOCK and who was already holding what.
            #
            # F_SETLKW asks to WAIT, and this stance cannot: the server is single-threaded
            # by construction (one store writer), so blocking here would block the very
            # requests that could release the lock. Refusing is the honest answer and the
            # divergence is named — a wait becomes an immediate refusal — rather than
            # deadlocking a mount. It goes away by construction below the syscall line.
            self._refuse("FILE-LOCK", "FS-LAW-LOCK",
                         "%s [%d,%s) on %s is held by owner %s (%s) — exclusivity is granted "
                         "by decision and refused when another owner holds it%s"
                         % (want, start, "eof" if not length else start + length, path,
                            clash.owner, clash.ltype,
                            "; this port cannot honour a blocking wait and refuses instead"
                            if cmd == _F_SETLKW else ""))
        self._act("FILE-LOCK", path=path, inode=ino, ltype=want,
                  start=start, length=length, owner=owner)
        return 0

    def _release_locks(self, fh, mechanism, ino=None, owner=None, start=0, length=0):
        """Record the release of every lock this owner holds over the range. Appends
        NOTHING when the owner holds none — which is the ordinary case for every close of
        every file, and is why recording still tracks governance rather than operation."""
        if ino is None:
            info = self._open.get(fh)
            if info is None:
                return
            ino, owner = info["ino"], self._ctx()[2]
        for lk in self.locks.held_by(ino, owner):
            if not custody._overlaps(lk.start, lk.length, start, length):
                continue
            self._act("FILE-UNLOCK", path=lk.path, inode=ino, start=lk.start,
                      length=lk.length, owner=owner, mechanism=mechanism)

    # =================================================================================
    # the recorded granularity policies (W5)
    # =================================================================================
    def _coalescing(self):
        """The write-coalescing policy, READ FROM THE RECORD. Absent -> None, and the caller
        FAILS CLOSED to one covering decision per write. Recording more is never the defect
        K3 names, so the safe direction is the one an absent policy takes."""
        return self.views.policy_value("files-write-coalescing")

    def _maybe_close_burst(self, fh):
        pol = self._coalescing()
        b = self._burst.get(fh)
        if b is None:
            return
        if not pol:
            self._close_burst(fh)          # fail-closed: no policy, no coalescing
            return
        if b["events"] >= int(pol.get("max_events") or 1) or \
                len(b["bytes"]) >= int(pol.get("max_bytes") or 1):
            self._close_burst(fh)

    def _close_burst(self, fh):
        """Append the ONE covering decision for a burst, then release the effect.

        THE ORDER HERE IS THE WHOLE OF K1 FOR THE WRITE PATH, so it is spelled out. The blob
        goes down FIRST and durably: a record naming a hash whose bytes are not on the disk
        would be a record claiming an effect that did not occur, which is the one forbidden
        lie. THEN the covering decision is appended (and `store._append` fsyncs it). Only then
        is the burst dropped, so that a crash anywhere in between leaves either (a) an orphan
        blob and no record — nothing happened, in record or effect — or (b) a record and its
        blob, which replay turns back into exactly this content. What can never happen is a
        served byte with no record behind it."""
        b = self._burst.pop(fh, None)
        if b is None:
            return
        pol = self._coalescing()
        content = bytes(b["bytes"])
        try:
            self._act("FILE-WRITE", path=b["path"], inode=b["ino"], content=content,
                      coalesced_events=b["events"],
                      coalescing_policy=("FS-WRITE-COALESCING" if pol else None))
            self.counters["write_events"] += 1
        except FuseOSError:
            self._burst[fh] = b            # the effect is NOT released; the burst stands
            raise

    def _read_policy(self):
        return self.views.policy_value("files-read-aggregation")

    def _maybe_close_read_window(self, ino):
        pol = self._read_policy()
        agg = self._reads.get(ino)
        if not pol or agg is None:
            return
        if agg["reads"] >= int(pol.get("max_reads") or 1) or \
                agg["bytes"] >= int(pol.get("max_bytes") or 1):
            self._close_read_window(ino)

    def _close_read_window(self, ino):
        agg = self._reads.pop(ino, None)
        if not agg or not agg["reads"]:
            return
        self._act("FILE-READ-AGGREGATE", path=agg["path"], inode=ino,
                  reads=agg["reads"], bytes=agg["bytes"])

    def _flush_paths(self, paths):
        want = {custody._norm(p) for p in paths}
        for fh, b in list(self._burst.items()):
            if custody._norm(b["path"]) in want:
                self._close_burst(fh)

    # =================================================================================
    # shadow-diff and the divergence halt (W6)
    # =================================================================================
    def shadow_diff(self):
        """The state served, against the same fold recomputed FROM THE RECORD ALONE. This is
        the leg the journaling template dies on, run continuously rather than once: a
        passthrough-plus-log would pass every syscall row and fail here, because its truth was
        never in the record. Compared at QUIESCENT points — an open burst is a page cache, and
        comparing against it would be comparing the record with bytes POSIX has not promised
        anyone yet."""
        self.counters["shadow_checks"] += 1
        served = self.state.snapshot()
        replayed = custody.fold(self.store.all()).snapshot()
        if served == replayed:
            return None
        # THE KEYS ARE READ OFF THE SNAPSHOT, NEVER LISTED HERE [EP-28E W2]. This loop used
        # to name `names` and `inodes`, and the snapshot has since grown two more keys — so
        # a divergence in one of those would have made `served == replayed` false, produced
        # an EMPTY diff list, and `_shadow_check`'s `if diff:` would then not have halted.
        # A divergence detected and not reported is worse than one not detected: the mount
        # keeps serving and the counter says a check ran. A hand-list of what to compare is
        # the same defect class as any check whose subject is constructed rather than read
        # (charter §A30 root 2), so the subject is read from the thing being compared.
        diff = []
        for key in sorted(set(served) | set(replayed)):
            a, b = served.get(key) or {}, replayed.get(key) or {}
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    diff.append("%s[%s]: served %r vs replayed %r" % (key, k, a.get(k), b.get(k)))
        if not diff:
            # UNEQUAL AND NOTHING TO SHOW. Impossible for two dict-of-dict snapshots, and
            # said out loud rather than returning a falsy list that reads as "no divergence".
            diff = ["snapshots differ but no per-key difference was found: served keys %r "
                    "vs replayed keys %r" % (sorted(served), sorted(replayed))]
        return diff

    def _shadow_check(self):
        if self.halted or self._burst:
            return None
        if self.shadow_every and self._acts % self.shadow_every:
            return None
        diff = self.shadow_diff()
        if diff:
            self.halt("shadow-diff", "; ".join(diff[:8]))
        return diff

    def halt(self, reason, detail=""):
        """HALT THE ASSUME (FS-LAW-DIVERGENCE-HALT). The mount goes read-only and the
        divergence is recorded, citing the rule. Recorded BEFORE the flag is set, so the halt
        itself is a governed act and not a silent state change — the one act still permitted
        once halted is this one."""
        try:
            self._act("CUSTODY-HALT", reason=reason, detail=detail or reason)
        finally:
            self.halted = reason

    # ---- shared refusals --------------------------------------------------------------
    def _parent_must_be_a_directory(self, path):
        parent = custody.parent_of(path)
        if parent is None:
            raise FuseOSError(errno.EEXIST)
        node = self.state.lookup(parent)
        if node is None:
            raise FuseOSError(errno.ENOENT)
        if node.kind != KIND_DIR:
            raise FuseOSError(errno.ENOTDIR)


#: How a governed refusal reaches userland. §11.1 is exact about this: the caller sees the
#: LINUX errno for the precondition, never a governance code — "a denial cites errno to
#: userland and a rule to the record". The record still carries the rule that refused, so
#: the audit answer to "why?" is a law and the ABI answer stays in the old vocabulary.
_ERRNO_BY_RULE = {
    "ROOT-NEG-1": errno.EACCES,      # no authorising chain at all
    "ROOT-NEG-3": errno.EACCES,      # a chain reaches the account, not this act
    "SIGHT-IS-LAW": errno.EACCES,    # could not lawfully read it
    "P3-CLOSURE": errno.ENOSYS,      # the operation does not exist in this deployment
    "AR-2": errno.EINVAL,            # a nonconforming call
    "FS-LAW-LOCK": errno.EAGAIN,     # another owner holds an overlapping lock
    "BOOT-INT": errno.EPERM,         # a constitutional / conservation refusal
    "WATCHER-BRAKE": errno.EPERM,
    "FS-LAW-DIVERGENCE-HALT": errno.EROFS,
}


def _errno_for(op_error):
    return _ERRNO_BY_RULE.get(getattr(op_error, "rule", None), errno.EACCES)


def _ts(value, fallback):
    """A recorded time, as POSIX seconds. Records carry ISO-8601 record_time; a float that a
    FILE-TIMES record supplied passes through. An unparseable value falls back rather than
    crashing a stat — but it falls back VISIBLY to now, never to zero, because a 1970
    timestamp reads as data and a fallback should read as a fallback."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            import datetime
            return datetime.datetime.fromisoformat(value).timestamp()
        except ValueError:
            return fallback
    return fallback
