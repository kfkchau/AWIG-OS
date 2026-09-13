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
"""M3 (bridge stance 4): the USER-SPACE HALF of the in-kernel files seam (EP-28 W2).

THE FUSE TRANSPORT IS RETIRED HERE. Stance 3 served a real mount through fusepy, and
every operation — a `stat`, a `readdir`, a `read` — crossed into user space because
`fuse.ko` is a generic transport that knows what none of them MEAN. Below the line the
module holds design/10 §6's class map itself, so it answers the CACHE-class calls from
derived state without crossing at all, and this process is asked only about the things
that are actually governance:

  * a DECISION or LAW-class act, which crosses the gate and appends before any effect
    is released to the caller;
  * a CACHE FILL, which is data and never a verdict.

THE TRANSPORT CHANGED; NONE OF THE LAW DID. This module composes the same kernel
(`bridge.mount.build_brain`), folds the same custody state (`bridge.custody`), calls the
same gate through the same op definitions, and resolves identity by the same EP-15
invoker/actor split. Everything EP-25 proved holds here or it is a finding, and nothing
in this file re-derives anything EP-25 settled.

THE ONE PROPERTY A REVIEWER SHOULD CHECK FIRST, because it is the second wrong reference
this EP names and it is the reason the two request classes are kept apart by name:

    NO FILL HANDLER IN THIS FILE TOUCHES THE GATE.

A fill answers with data or with an errno. It cannot permit anything, so there is no
path by which the kernel could be handed a governance answer to cache. Detach this
process and every governed act below the line fails, while every cache read still
answers — which is T-NO-KERNEL-RESIDENT-ANSWER, and it is a running test rather than a
claim about the code.

    python3 -m bridge.kernel_port <record.jsonl> <blobdir> [/dev/govos-ctl]
"""

import errno
import os
import socket
import stat as statmod
import sys
import threading

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                 # AWIG OS/src

from kernel.errors import OpError                          # noqa: E402
from kernel import erasure                                 # noqa: E402  — GS-13's scar on a destroyed hash

from . import custody                                      # noqa: E402
from .custody import KIND_DIR, KIND_FIFO, KIND_LINK        # noqa: E402

#: This port's own window identity, recorded in every act's provenance so a reader can
#: tell WHICH port asserted the uid it is looking at. The EP-22 window@version precedent,
#: and it is deliberately different from the FUSE port's `fuse-port@1`: the two are
#: different windows onto the same machine and a record must say which one it came
#: through, or "who asserted this uid" stops being answerable.
WINDOW = "kernel-port@1"

CTL_DEFAULT = "/dev/govos-ctl"

#: The channel's cap, matching the module's GOVOS_MSG_MAX. Stated in both halves rather
#: than negotiated, because a cap that one side believes and the other does not is worse
#: than either value.
MSG_MAX = 1 << 20

#: How a governed refusal reaches userland — EP-25's table, unchanged, because §11.1 is
#: unchanged: the caller sees the LINUX errno for the precondition and never a governance
#: code, while the record carries the rule that refused. A denial cites errno to userland
#: and a rule to the record.
#:
#: THIS TABLE IS KEYED BY RULE AND THAT IS CORRECT FOR EVERY ROW IN IT (EP-28N). A sight
#: denial is EACCES whatever act met it; a closure hit is ENOSYS whatever act met it. The
#: key works exactly where ONE RULE DETERMINES ONE ANSWER — and it gains no row here,
#: because the family where it does not is served below instead.
ERRNO_BY_RULE = {
    "ROOT-NEG-1": errno.EACCES,
    "ROOT-NEG-3": errno.EACCES,
    "SIGHT-IS-LAW": errno.EACCES,
    "P3-CLOSURE": errno.ENOSYS,
    "AR-2": errno.EINVAL,
    "FS-LAW-LOCK": errno.EAGAIN,
    "BOOT-INT": errno.EPERM,
    "WATCHER-BRAKE": errno.EPERM,
    "FS-LAW-DIVERGENCE-HALT": errno.EROFS,
}

#: THE ACT'S OWN ANSWER (EP-28N). Keyed by the operation and by WHAT THAT OPERATION REQUIRED
#: OF ITS KEY — never by the rule, because one rule governs every row below while POSIX gives
#: them six different answers. A create that found its name held is EEXIST; an unlink that
#: found its name absent is ENOENT; both are refused under `FS-LAW-NAMESPACE`, so an
#: `FS-LAW-NAMESPACE -> <errno>` row would be wrong for one of them whichever value it took.
#: THE MISSING ROW WAS THE SYMPTOM AND THE KEY WAS THE DEFECT: eleven rows here, one rule
#: there.
#:
#: AND THE RE-KEYING TAKES THE PAYOFF OUT OF LAW-SHOPPING RATHER THAN ONLY EXPOSING IT
#: (§A56). Under the old key a false citation chosen for the errno it produced came out RIGHT
#: — the incentive ran backwards and only a seat asking "why this rule" could tell. Under this
#: key the citation produces no observable at all, so there is nothing left to shop for.
#:
#: IT IS RENDERING, NOT LAW, and it lives here for the reason `SYSCALL_MAP` does: which errno
#: POSIX gives an operation is the ABI's own mechanism, and this file is the ABI's edge. What
#: is LAW is which rule refused, and that is on the record.
#: AND THE SUFFIX IS THE SAME LESSON ONE LAYER DOWN (EP-28N AMENDMENT 1). `binding:bound` over
#: the name an act TAKES and `binding:bound` over the name that CONTAINS it are two different
#: outcomes — POSIX answers the first ENOENT for an unlink of an absent name and the second
#: ENOENT for a create into an absent container — so the requirement carries WHICH KEY it was
#: about. Without the suffix the create family's two rows would collide on one string and this
#: table would need a rule-keyed compromise, which is the defect above wearing new clothes.
#:
#: NINETEEN ROWS, AND NINETEEN IS THE WHOLE ENUMERATION.
#:
#: [CORRECTED IN PLACE — EP-28C W4e, 2026-08-07. The sentence that stood here read:
#: "`_posix_precondition` below serves nineteen (op, outcome) pairs over seven operations
#: from thirteen return points, read from its own AST. Every one of them now has a declared
#: law behind it and an act-keyed answer here — which is what makes that read RETIREABLE at
#: W4e rather than merely redundant." THE RETIREMENT HAPPENED. The read is gone, so that
#: sentence would now describe a function nobody can open, and a comment naming a construct
#: the file no longer holds is a specification the next reader builds against.]
#:
#: The nineteen are DECLARED CHECKS on the op definitions — EP-28K's `binding`, EP-28N's
#: `kind` and `contains`, EP-28N AMENDMENT 1's container rows — decided INSIDE the gate's
#: decide region, and each one records the refusal it makes. What is left at this port is
#: the rendering, which is this table: the ACT's requirement into the errno POSIX gives.
#:
#: SO THIS TABLE IS NOW THE PORT'S ONLY ENUMERATION OF THE NINETEEN, and it is where the
#: rows that used to walk the retired function's AST read the population from instead. It
#: carries strictly more than that walk did: the walk recovered (op, errno), and every key
#: here also names WHICH REQUIREMENT the outcome was about.
ERRNO_BY_ACT = {
    ("FILE-CREATE",  "binding:unbound"):            errno.EEXIST,
    ("FILE-MKDIR",   "binding:unbound"):            errno.EEXIST,
    ("FILE-SYMLINK", "binding:unbound"):            errno.EEXIST,
    ("FILE-LINK",    "binding:unbound"):            errno.EEXIST,
    ("FILE-RMDIR",   "binding:bound"):              errno.ENOENT,
    ("FILE-UNLINK",  "binding:bound"):              errno.ENOENT,
    ("FILE-RENAME",  "binding:bound"):              errno.ENOENT,
    ("FILE-LINK",    "binding:bound"):              errno.ENOENT,
    ("FILE-RMDIR",   "kind:require:dir"):           errno.ENOTDIR,
    ("FILE-UNLINK",  "kind:forbid:dir"):            errno.EISDIR,
    ("FILE-LINK",    "kind:forbid:dir"):            errno.EPERM,
    ("FILE-CREATE",  "binding:bound@container"):    errno.ENOENT,
    ("FILE-MKDIR",   "binding:bound@container"):    errno.ENOENT,
    ("FILE-SYMLINK", "binding:bound@container"):    errno.ENOENT,
    ("FILE-CREATE",  "kind:require:dir@container"): errno.ENOTDIR,
    ("FILE-MKDIR",   "kind:require:dir@container"): errno.ENOTDIR,
    ("FILE-SYMLINK", "kind:require:dir@container"): errno.ENOTDIR,
    ("FILE-RMDIR",   "contains:empty"):             errno.ENOTEMPTY,
    ("FILE-RENAME",  "contains:empty"):             errno.ENOTEMPTY,
}


class PortCannotRenderTheLaw(RuntimeError):
    """The founding declares a precondition this port has no ABI answer for.

    RAISED AT CONSTRUCTION AND NEVER AT A CALL, which is the whole point: a port that
    discovers at the boundary that it cannot render an outcome has already been asked, and
    its only remaining moves are a wrong errno or a hang. The estate's own shape is to make
    the deferral discoverable rather than silent (`content_ops_pending_blobs`), and here the
    honest form is stronger — a port serving a law it cannot answer for is not a port."""

#: The record kind each in-kernel op appends. IT IS THE SAME SET EP-25 USED and no
#: founding bump is taken, which is the derivation rather than a convenience: the
#: transport moved and the law did not, so an op whose definition differed below the line
#: would be asserting that a kernel-resident write is a different governed act from a
#: user-space one. It is not. The same op definitions serve both ports.
DECISION_OPS = {
    "FILE-OPEN", "FILE-CLOSE", "FILE-CREATE", "FILE-MKDIR", "FILE-RMDIR",
    "FILE-UNLINK", "FILE-SYMLINK", "FILE-LINK", "FILE-RENAME", "FILE-WRITE",
    "FILE-TRUNCATE", "FILE-PERM", "FILE-CHOWN", "FILE-TIMES",
    "FILE-XATTR-SET", "FILE-XATTR-REMOVE", "FILE-XATTR-LAW",
    "FILE-LOCK", "FILE-UNLOCK", "FILE-READ-AGGREGATE",
}

_TYPE_NAME = {KIND_DIR: "dir", KIND_LINK: "link", KIND_FIFO: "fifo"}


def _esc(v):
    return str(v).replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")


def _unesc(v):
    out, i = [], 0
    while i < len(v):
        if v[i] == "\\" and i + 1 < len(v):
            nx = v[i + 1]
            out.append("\t" if nx == "t" else "\n" if nx == "n" else nx)
            i += 2
        else:
            out.append(v[i])
            i += 1
    return "".join(out)


def parse_request(blob):
    """Split one request into its header fields and its raw payload.

    The payload is bytes and stays bytes: a governed write's content goes full-fidelity
    to a content-addressed blob (design/10 §6, [AUDIT-FIX 4]), so decoding it as text
    anywhere on this path would corrupt exactly the thing the record promises to
    preserve exactly."""
    nl = blob.find(b"\n")
    if nl < 0:
        raise ValueError("request carries no header terminator")
    head = blob[:nl].decode("utf-8", "surrogateescape")
    payload = blob[nl + 1:]
    fields = {}
    for part in head.split("\t"):
        if "=" in part:
            k, v = part.split("=", 1)
            fields[k] = _unesc(v)
    return fields, payload


def build_reply(req_id, status, fields=None, payload=b""):
    head = "id=%s\tstatus=%d" % (req_id, status)
    for k, v in (fields or {}).items():
        if v is not None:
            head += "\t%s=%s" % (k, _esc(v))
    return head.encode("utf-8", "surrogateescape") + b"\n" + payload


class KernelPort:
    """The brain, answering the seam below the line.

    THE PORT ORDERS THE FOLD'S WRITER AGAINST THE FILL'S READER (EP-28R W4, shape (a),
    mentor-ruled 2026-08-07). It did not before, and nothing else did either: `_on_append`
    advances the fold from inside the appending thread's decide region while `_fill_readdir`
    and `_fill_lookup` walk it from outside every region. What kept them apart was
    `govos_call_lock` below the line — ONE CALLER IN THE CHANNEL AT A TIME — which is the
    exact lowering AMENDMENT 11.2 orders removed, so the ordering has to come from here.

    THE COST IS STATED RATHER THAN HIDDEN, AND IT IS NOT THE SAME COST IN BOTH DIRECTIONS —
    the mentor withdrew their own unqualified word here on 2026-08-07 and this file does not
    re-say it. A fill WAITS: an unrelated governed decision makes a cache read wait for the
    duration of ONE fold advance, and THAT direction is bounded by the decide region. The
    other direction is not bounded the same way: a long fill makes an appender's own fold
    advance wait for the duration of that fill, which is bounded by one fill ONLY IF FILLS DO
    NOT QUEUE — measured x3.72 at a 203-entry root and x5.00 at 3,203, so the bound GROWS with
    fill duration, which grows with directory size. THE QUEUEING QUESTION IS HOMED, not
    dropped: EP-28C §11.2 carries it to the contended arms, and `tests/test_ep28r.py`'s
    inversion class is preserved as its instrument rather than rebuilt there.

    IT STILL BEATS THE SHAPE THAT NEVER WAITS. Serving fills from a snapshot was ruled out
    because a snapshot is a copy of the namespace, so copying it puts a term on the act path
    that grows with the system forever, and `tests/test_ep28e_w4.py` is the standing guard
    that forbids exactly that. The separator is CONDITIONAL against UNCONDITIONAL — a snapshot
    copy is on EVERY act, this ordering only on acts concurrent with a fill — and that is a
    difference in kind. It is NOT "bounded against unbounded", which is what was said first.

    WHAT THE ORDERING IS NOT: it is not the decide region, and it must never become it. The
    fill takes THIS lock and no store lock; the appender takes the store's write lock and
    then this one, so the order is total and no cycle exists. And it is released before the
    durability barrier is ever reached — EP-28G split publication from `fdatasync` precisely
    so no lock spans the barrier, and this pass does not re-couple them.
    """

    def __init__(self, store, gate, views, blobs):
        self.store = store
        self.gate = gate
        self.views = views
        self.blobs = blobs
        # THE ORDERING ITSELF. An RLock rather than a Lock because the store's write lock is
        # re-entrant and a listener may append from inside a listener (the dual-audit mirror
        # does), so this one has to survive being reached twice down one thread's stack.
        self._fold_order = threading.RLock()
        # THE COORDINATE'S STATE — see `_mark_folded`. Held under `_fold_order` like the fold
        # it describes, because a coordinate read apart from the state it names is exactly the
        # thing this pass exists to stop.
        self._folded_high = 0
        self._folded_above = set()
        # THE SAME FOLD, MAINTAINED THE SAME WAY. `custody.fold` builds it from the
        # record alone and the store's on-append listener advances it — one derivation
        # over two sources (EP-24B's rule), so a divergence could only ever mean a
        # record was missed, never that two implementations disagreed about meaning.
        #
        # ONE READ OF THE RECORD, NOT THREE. The two folds and the coordinate's starting
        # value are three statements about the same prefix, and taking three separate reads
        # of `store.all()` to make them would let the three disagree about which prefix they
        # were about — a coordinate one record ahead of the fold it names is the ruling's own
        # red world, arrived at through the constructor instead of through a race.
        records = store.all()
        self.state = custody.fold(records)
        self.locks = custody.fold_locks(records)
        self._folded_high = len(records)
        store.on_append(self._on_append)
        self.counters = {"decisions": 0, "fills": 0, "refusals": 0}
        self._require_every_declared_outcome_is_renderable()

    def _require_every_declared_outcome_is_renderable(self):
        """THE LEASH THE ACT-KEYED TABLE ARRIVES WITH, IN THE SAME ROUND IT DOES (EP-28N).

        The founding this port serves declares, per operation, what each of its checks
        requires. Every one of those requirements is an outcome a caller can meet, so every
        one of them needs an ABI answer — and a table that silently defaults on the one it
        lacks is the defect this pass exists to close, wearing a different key.

        COMPUTED FROM THE LAW, over the OPS THIS PORT ACTUALLY SERVES. A requirement declared
        by an op no port call can reach is not this port's to answer, and demanding a row for
        it would be a guard about somebody else's surface. A world founded before the checks
        existed declares none, so this is inert there — the two-times law again, holding by
        construction rather than by a branch."""
        from kernel.opdefs import declared_requirements
        missing = set()
        for name, v in self.views.op_definitions().items():
            if name not in DECISION_OPS:
                continue
            for requirement in declared_requirements(v.get("definition") or {}):
                if (name, requirement) not in ERRNO_BY_ACT:
                    missing.add((name, requirement))
        if missing:
            raise PortCannotRenderTheLaw(
                "the founding declares preconditions this port has no ABI answer for: %s — a "
                "port that meets one of these at the boundary can only return a wrong errno, "
                "so it refuses to serve instead" % sorted(missing))

    def _on_append(self, record):
        """THE FOLD'S WRITER, NOW ORDERED (EP-28R W4).

        The whole advance is one step to any reader. `custody.CustodyState.apply` folds a
        rename as `self._bind(dst, self._unbind(src))`, and BETWEEN those two calls the name
        is in neither `names` nor `kids` — a condition no record boundary describes and no
        prefix of the record produces. Both of the exhibited tears fall in that one window
        (EP-28R W1), so ordering at whole-call granularity closes both, and ordering at
        individual-fold-read granularity would close neither."""
        with self._fold_order:
            self.state.apply(record)
            self.state.applied += 1
            self.locks.apply(record)
            self._mark_folded(record)

    def _mark_folded(self, record):
        """ADVANCE THE COORDINATE, AND IT IS A CONTIGUOUS HIGH-WATER MARK RATHER THAN A COUNT.

        `state.applied` is the obvious coordinate and it is WRONG, driven rather than argued:
        records do NOT reach this listener in seq order. `protection.Protection._maybe_mirror`
        appends a `dual-audit-record` from INSIDE the on-append callback, the store's write
        lock is re-entrant, and the nested record publishes to every listener before the outer
        one does — so folding an `AMEND-BUDGET` at seq 140 calls this method with 141, then
        142, then 140. A COUNT would read 140 after folding 141, naming a position whose
        PREFIX the served state does not carry. That is a coordinate naming a state that was
        never served, which is the ruled obligation's own red world.

        WHAT THIS VALUE MEANS, EXACTLY, because a coordinate whose meaning is loose is worse
        than none: every record at positions 1..`_folded_high` HAS been folded into this
        state. It does not claim nothing above it has — the out-of-order ones have — and
        `tests/test_ep28r.py` carries the guard behind that guard: NO action the custody fold
        acts on is appendable from inside a fold callback, so everything folded above the mark
        is a no-op on the served namespace and the state IS the fold of the prefix. If that
        ever changes the served namespace starts depending on listener order, and the row says
        so rather than leaving it to be rediscovered.

        A RECORD WITHOUT AN INTEGER POSITION DOES NOT ADVANCE THE MARK. The store mints one on
        every append, so this is inert today; it is written this way because the failure it
        avoids is silent. Refusing to advance keeps the statement above TRUE (the prefix below
        the mark is still all folded) where advancing on a guess would make it false."""
        seq = record.get("seq")
        if not isinstance(seq, int) or isinstance(seq, bool):
            return
        self._folded_above.add(seq)
        while (self._folded_high + 1) in self._folded_above:
            self._folded_high += 1
            self._folded_above.discard(self._folded_high)

    def _node_by_wire(self, f, key):
        """Resolve ONE inode number off the wire to the node it names.

        THE INBOUND HALF OF THE BOUNDARY (EP-28C W4b). The module holds `i_ino`, an
        `unsigned long`, and sends it back on every later call; the fold is keyed by exactly
        that number because `custody.Inode` renders the recorded identity once, at ingestion.
        So this is a PARSE and a lookup, with no second interpretation anywhere.

        AN UNKNOWN NUMBER IS ESTALE AND NEVER A FALLBACK TO THE PATH. The identity is what
        was recorded, never the name it happens to be reachable by — answering by path here
        would quietly undo the property hard links and renames rest on."""
        node = self.state.inodes.get(custody.parse_ino(f.get(key)))
        if node is None:
            raise custody.IdentityNotInFold(
                "the wire names inode %r under %r and this fold holds no such node"
                % (f.get(key), key))
        return node

    # ---- identity at the port (K6) --------------------------------------------------
    def _actor(self, uid):
        """THE ACTING ACTOR IS DERIVED. A uid<->account synchronised table would be a
        stored identity status (P2 dead); the mapping is recorded MAP-UID acts and the
        answer is a fold over them, recomputed every act. The kernel-asserted uid stays
        EVIDENCE and is recorded as evidence. Identical to the FUSE port's derivation,
        because moving below the line changed the transport and not K6."""
        mapped = None
        for e in self.store.by_action("MAP-UID"):
            p = e.get("payload") or {}
            if custody._num(p.get("uid"), "a MAP-UID record's uid") == uid:
                mapped = p.get("account")
        return mapped or ("uid:%d" % uid)

    def _prov(self, f):
        # THE KERNEL-ASSERTED uid IS EVIDENCE (K6) AND EVIDENCE THAT CANNOT BE READ IS NOT
        # EVIDENCE. These three refuse rather than defaulting (EP-28C W4b): a uid the wire
        # states and the port cannot read used to become 0, which is ROOT — the strongest
        # possible actor obtained by a coercion nobody could see.
        uid = custody._num(f.get("uid"), "the port's asserted uid")
        actor = self._actor(uid)
        return actor, {
            "asserted_by": self.views.resolve_asserted_by(actor),
            "source": "kernel-port",
            "could_read": [],
            "window": WINDOW,
            "uid": uid,
            "gid": custody._num(f.get("gid"), "the port's asserted gid"),
            "pid": custody._num(f.get("pid"), "the port's asserted pid"),
        }

    def _carries_port_provenance(self, op):
        """Read from the op's OWN definition record, never from a list in this file —
        the EP-16 authority-regime precedent. The five campaign-1 ops that cannot declare
        it are the same five EP-25 raised (`kernel/syscall_port.py` has a pre-existing
        caller that supplies none), and that engine gap is carried unchanged rather than
        patched from here, because `src/kernel/` is a finding for this EP and not a patch
        site."""
        d = (self.views.op_definitions().get(op) or {}).get("definition") or {}
        return bool(d.get("provenance_param"))

    # ---- the two request classes ----------------------------------------------------
    def handle(self, fields, payload):
        """Returns (status, reply_fields, reply_payload).

        R4 (EP-MAINT-OUTSIDE-4): CONTAINMENT AT THE PORT. A malformed identity or time field is a
        PROTOCOL failure and is mapped to EPROTO HERE, at the handler, for BOTH request classes —
        not only DECISION, whose own inner catches (`_decide`) had it while FILL let a malformed field
        escape as an uncaught exception to the serve loop's EIO backstop. A well-formed handle naming
        nothing is ESTALE (a handle into a world that moved), never EPROTO. The loop's catch stays a
        backstop; the contract is that a malformed field never reaches it."""
        op = fields.get("op") or ""
        cls = fields.get("class") or ""
        try:
            if cls == "FILL":
                self.counters["fills"] += 1
                return self._fill(op, fields)
            if cls == "DECISION":
                self.counters["decisions"] += 1
                return self._decide(op, fields, payload)
            return -errno.EPROTO, {}, b""
        except (custody.UnparseableRecordValue, custody.UnrenderableIdentity):
            return -errno.EPROTO, {}, b""
        except custody.IdentityNotInFold:
            return -errno.ESTALE, {}, b""

    # ---- FILLS: data, never a verdict. Nothing below touches the gate. --------------
    def _fill(self, op, f):
        if op == "FILL-LOOKUP":
            return self._fill_lookup(f)
        if op == "FILL-READDIR":
            return self._fill_readdir(f)
        if op == "FILL-CONTENT":
            return self._fill_content(f)
        return -errno.ENOSYS, {}, b""

    def _node_fields(self, node):
        out = {
            # THE OUTBOUND HALF OF THE BOUNDARY (EP-28C W4b). The fold holds the identity;
            # the wire and the VFS behind it need a number; this is where the one rendering
            # happens. The module NEVER renders — it parses what this computed.
            "ino": custody.render_ino(node.ino),
            "type": _TYPE_NAME.get(node.kind, "file"),
            "perm": oct(statmod.S_IMODE(self.state.mode(node)))[2:],
            "uid": node.uid,
            "gid": node.gid,
            "size": node.size,
        }
        if node.kind == KIND_LINK:
            out["target"] = node.target or ""
        elif node.content_hash:
            out["hash"] = node.content_hash
        return out

    def _fill_lookup(self, f):
        # THE WHOLE READ IS ONE ORDERED OBSERVATION (EP-28R W4). Not the container walk —
        # this member walks none and tore anyway, because what is torn is the STATE and not
        # the dict. `path_of` and `lookup` fall into the two halves of one rebind's window,
        # so a fix that guarded an iteration would have closed neither arm.
        with self._fold_order:
            at_seq = self._folded_high
            parent = self._node_by_wire(f, "parent").ino
            name = f.get("name") or ""
            ppath = self.state.path_of(parent)
            if ppath is None:
                return -errno.ENOENT, {"at_seq": at_seq}, b""
            path = custody._norm(ppath.rstrip("/") + "/" + name)
            node = self.state.lookup(path)
            if node is None:
                # AN ABSENCE, NOT A REFUSAL (design/10 §11.1a class 2). The view answered
                # "no such thing"; the call is a read; a record appearing here would be the
                # failure, and none does.
                #
                # AND IT STILL CITES ITS COORDINATE. A negative answer is a claim about a
                # state exactly as a positive one is — "there is no such name" is only
                # answerable as of a position — so the field is on both branches.
                return -errno.ENOENT, {"at_seq": at_seq}, b""
            out = self._node_fields(node)
            out["at_seq"] = at_seq
            return 0, out, b""

    def _fill_readdir(self, f):
        with self._fold_order:
            at_seq = self._folded_high
            ino = self._node_by_wire(f, "ino").ino
            path = self.state.path_of(ino)
            if path is None:
                return -errno.ENOENT, {"at_seq": at_seq}, b""
            lines = []
            for name in self.state.children(path):
                child = self.state.lookup(custody._norm(path.rstrip("/") + "/" + name))
                if child is None:
                    continue
                t = {KIND_DIR: "d", KIND_LINK: "l", KIND_FIFO: "p"}.get(child.kind, "f")
                # `%d` ON THE RENDERING (EP-28C W4b). `child.ino` is the number
                # `custody.Inode` rendered at ingestion, so this expression can no longer
                # meet a string — which is the `TypeError` EP-28I's residual row exhibited,
                # and the same value that `custody._int` used to turn into 0 without saying
                # anything. Both are gone.
                lines.append("%s\t%s\t%d" % (name, t, child.ino))
            return (0, {"at_seq": at_seq},
                    ("\n".join(lines)).encode("utf-8", "surrogateescape"))

    def _fill_content(self, f):
        """A file's exact bytes, fetched BY THE HASH THE RECORD CARRIES.

        This is the whole difference from the journaling filesystem this campaign
        refuses. Nothing here asks the host filesystem what a path contains; it asks the
        blob store for a hash the record named, which is the record answering through a
        hash rather than the host answering through a path.

        IT TAKES NO ORDERING AND CARRIES NO COORDINATE, and that is a derivation and not an
        omission (EP-28R W4). It reads the fold at no point, so there is no window for it to
        fall into and no state for a coordinate to be about — which is exactly why it was the
        member that did NOT tear when the other two did, and why taking the ordering here
        would make this file's own finding untestable."""
        h = f.get("hash") or ""
        # THE DEPARTURE (design/46 member 4): a hash whose custody was handed over by a recorded
        # handover ceremony resolves to the DEPARTURE marker, not the (now gone) local bytes and not
        # a silent empty — read from the live record, so a read as-of before the ceremony still
        # answers the departure (design/23 Option C). Inert until a departure record exists. Read
        # through the K12 action-scoped projection so a content fill costs only the handover family
        # (empty in every world that has run no ceremony), never the whole record.
        if h and h in erasure.departed_hashes(
                self.store.action_set_projection({erasure.HANDOVER_OP}).all()):
            return 0, {}, erasure.DEPARTURE
        if not h or not self.blobs.has(h):
            return 0, {}, b""
        return 0, {}, self.blobs.get(h)

    # ---- DECISIONS: the gate, and only the gate ------------------------------------
    def _decide(self, op, f, payload):
        if op not in DECISION_OPS:
            # THE CLOSURE HIT (P3): an unregistered operation does not exist. It is
            # refused, and the refusal is recorded by the gate rather than invented here.
            return self._refuse_unregistered(op, f)

        # THE POSIX PRECONDITION READ RETIRED HERE — EP-28C W4e, 2026-08-07.
        #
        # What stood at this line was `precondition = self._posix_precondition(op, f)`,
        # answering nineteen (op, outcome) pairs over seven operations from the fold BEFORE
        # the gate and returning the errno with NOTHING appended. Its own comment cited
        # design/10 §11.1a classes 2 and 3 — an absence is not a refusal — and that reading
        # was OVERTURNED by owner ruling 1 and made law by EP-28K: these outcomes are
        # DECLARED checks, the gate decides every one of them inside the decide region, and
        # a declared refusal RECORDS. So the port asking first was the port doing the gate's
        # job, and after EP-28N/N-A1 completed the declarations there was nothing left for
        # the question to be about.
        #
        # THE CALLER IS ANSWERED EXACTLY AS BEFORE and that is measured, not assumed:
        # `tests/test_ep28c_w4e_r.py` drives all nineteen with this read on and off as the
        # one varied thing — identical errno on every pair, no act record in either arm,
        # and the only delta is the refusal record the declared check is ruled to append.
        #
        # AND THE ONE THING THAT READ KNEW IS KEPT RATHER THAN LOST WITH IT: the emptiness
        # question cannot be answered below the line. The module's `simple_empty` reads the
        # DENTRY CACHE, which under lookup-on-demand holds only the names somebody has
        # already asked for, so a directory whose children were never looked up reads as
        # empty down there and is not empty in the record. It is now the `contains:empty`
        # check's — still above the line, and now INSIDE the region instead of in front of
        # it, which is the whole difference this retirement buys.
        try:
            actor, prov = self._prov(f)
            params = self._params_for(op, f, payload)
        except (custody.UnparseableRecordValue, custody.UnrenderableIdentity):
            # A WIRE THIS PORT CANNOT READ IS A PROTOCOL FAILURE AND SAYS SO (EP-28C W4b).
            # Before this, an unreadable number became 0 and the act proceeded on it. EPROTO
            # is the honest errno: the caller's request never became a question this machine
            # could ask, so nothing is appended and nothing is refused by a rule either.
            return -errno.EPROTO, {}, b""
        except custody.IdentityNotInFold:
            # ESTALE: the number is well-formed and names nothing here. That is what a caller
            # holding a handle into a world that moved is actually told by POSIX.
            return -errno.ESTALE, {}, b""
        if self._carries_port_provenance(op):
            params["provenance"] = prov
        try:
            rec = self.gate.execute(op, actor, params)
        except OpError as e:
            self.counters["refusals"] += 1
            return -self._errno_for_refusal(op, e), {}, b""
        except Exception:
            # ANYTHING THAT IS NOT AN OpError IS A DEFECT IN THIS SEAM, NOT A REFUSAL,
            # and the caller must not be told a governance story about it. The ABI answer
            # stays EIO because that is what Linux says when a filesystem breaks — but
            # the traceback is PRINTED rather than swallowed. A bug that presents to
            # userland as a plain errno and leaves no trace anywhere is the same shape as
            # the `serve` loop's silent exit, which cost a session to find; one instance
            # of that per file is enough.
            import traceback
            traceback.print_exc()
            return -errno.EIO, {}, b""

        out = {}
        p = (rec or {}).get("payload") or {}
        if p.get("inode") is not None:
            # RENDERED ON THE WAY OUT, because what the record minted is an IDENTITY and
            # what the module instantiates is an `unsigned long`. This handed the raw payload
            # value over, which was only ever an integer because the port had just stamped
            # one — and after the stamp's removal it is the derived path.
            out["ino"] = custody.render_ino(p["inode"])
        elif rec is not None and op in custody.MINTING_ACTIONS:
            # THE RECORD NAMES NO IDENTITY, SO THE ACT'S OWN COORDINATE NAMES WHAT IT FOUNDED
            # (EP-28S). From founding 1.18.0 the three minting ops take no `inode` parameter
            # at all, so this branch is the ONLY one a create, a mkdir or a symlink reaches —
            # and without it the reply would carry no `ino` and the module would instantiate
            # an inode it was never told the number of.
            #
            # IT IS THE SAME DERIVATION THE FOLD PERFORMS AND NOT A SECOND ONE. `formal_name`
            # is one function with one body; this calls it, exactly as `_node_fields` calls
            # the one `render_ino` rather than computing a number of its own. The alternative
            # — reading the node back out of the fold — would make the reply depend on the
            # listener having run, which is a timing assumption where a pure derivation from
            # the record in hand needs none.
            out["ino"] = custody.render_ino(custody.formal_name(rec.get("seq")))
        if p.get("content_hash"):
            out["hash"] = p["content_hash"]
        return 0, out, b""

    def _errno_for_refusal(self, op, e):
        """THE ERRNO A REFUSAL CARRIES TO USERLAND, AND WHICH KEY DECIDES IT (EP-28N).

        A refusal raised by a declared precondition carries WHAT THE ACT REQUIRED of its key.
        That is the ACT, so it renders from the act-keyed table and the cited rule is not
        consulted — which is the separation this pass exists for: the record answers "under
        what law", and the caller is answered "what happened to my call", and one rule cannot
        answer the second for two acts POSIX distinguishes.

        A refusal carrying NO requirement did not come from a precondition on a key: an
        authority denial, a sight denial, a closure hit. For those the RULE does determine the
        answer, so they take the rule-keyed path unchanged — this is not a fallback from the
        act key but a different question, and the rows it reads are the rows that were always
        right. The lookup below cannot miss, and that is enforced at construction rather than
        defaulted at the boundary."""
        requirement = getattr(e, "requirement", None)
        if requirement is None:
            return ERRNO_BY_RULE.get(getattr(e, "rule", None), errno.EACCES)
        return ERRNO_BY_ACT[(op, requirement)]

    # `_posix_precondition` STOOD HERE AND IS RETIRED (EP-28C W4e, 2026-08-07). It read the
    # fold for nineteen (op, outcome) pairs in front of the gate and returned an errno with
    # nothing appended. Every one of those outcomes is now a DECLARED check on its op
    # definition, decided inside the decide region and recorded there; `ERRNO_BY_ACT` above
    # renders the same errno from the act's requirement. The removal note at the call site
    # in `_decide` carries the derivation and the one fact this function knew that the
    # module cannot know — why the emptiness question stays above the line.

    def _refuse_unregistered(self, op, f):
        actor, _prov = self._prov(f)
        try:
            self.gate.refuse(actor, op or "UNKNOWN", "P3-CLOSURE",
                             "an unregistered operation does not exist in this "
                             "deployment; the bank has no counter")
        except OpError:
            pass
        self.counters["refusals"] += 1
        return -errno.ENOSYS, {}, b""

    def _params_for(self, op, f, payload):
        """Turn the wire's fields into the op definition's parameters.

        The mapping is per-op and explicit rather than a blanket pass-through, because an
        op definition declares which parameters it takes and the envelope router refuses
        a call that supplies one it did not declare (EP-27B). A blanket forward would
        turn every wire field into a nonconforming call the first time the module grew
        one.

        **[CORRECTED 2026-08-08, EP-28S — the sentence above is KEPT and dated rather than
        scrubbed, because it is why this mapping is written the way it is, and the reason it
        gives is still a good reason. THE REFUSAL IT NAMES DID NOT FIRE WHEN DRIVEN.** A
        `FILE-CREATE`, `FILE-MKDIR` or `FILE-SYMLINK` call carrying an `inode` the definition
        no longer declares is ADMITTED, not refused; the value is dropped because
        `payload_from` does not list it. Measured at EP-28S against all three ops, on the
        shipped founding. **The per-op mapping below is therefore load-bearing rather than
        belt-and-braces**, and the gap between what EP-27B refuses and what this claims is
        RAISED rather than closed here — adding an undeclared-parameter refusal is a law
        change that reaches every caller in the estate.]"""
        path = f.get("path") or "/"
        base = {"path": path}
        if f.get("inode") is not None:
            # THE RECORD SPEAKS ONE IDENTITY LANGUAGE (EP-28C W4b). The wire carries the
            # RENDERING (the module holds an `i_ino` and nothing else), and what gets
            # recorded is the IDENTITY the founding derived for that node — so a reader
            # comparing `payload.inode` across a node's create and its later writes sees one
            # value, not a path on one record and a number on the next.
            base["inode"] = self._node_by_wire(f, "inode").identity

        if op in ("FILE-CREATE", "FILE-MKDIR"):
            out = {"path": path}
            if f.get("perm"):
                out["perm"] = f["perm"]
            # THE PORT SUPPLIES NO INODE, AND THAT IS THE WHOLE OF EP-28C W4b's STAMP
            # REMOVAL. It used to read `self.state.next_ino` HERE, at `:426`, inside
            # `_params_for` and therefore BEFORE `gate.execute` — so two threads carried the
            # same number before either entered the gate, and no gate-level region could
            # serialize a read that happened outside it (AMENDMENT 5's finding at EP-28G's
            # stopped build).
            #
            # THE FIX REMOVES THE ALLOCATION RATHER THAN STRETCHING A LOCK OVER IT. All three
            # namespace ops declare `param_defaults {"inode": "$path"}` (founding 1.14.0,
            # class-wide since EP-28I), so an ABSENT inode is DERIVED by the op definition
            # itself, inside the decide region, unique per path BY CONSTRUCTION. The bridge
            # was duplicating a derivation the law performs safely, and its copy raced where
            # the law's cannot.
            #
            # [CORRECTED 2026-08-08, EP-28S — the paragraph above is KEPT because it is why
            # the stamp went, and that reasoning was right. ONE CLAUSE IN IT IS NO LONGER
            # TRUE OF THE FOUNDING: "unique per path BY CONSTRUCTION" is unique per path and
            # NOT per NODE, because a path is handed back by a rename or an unlink — so two
            # births could derive one identity, which is the defect EP-28S exists to close.
            # From 1.18.0 the three ops declare `mints_from: record_coordinate` and carry no
            # `inode` at all; the fold names the node by the birth act's own position in the
            # record. This port supplies no identity either way, so the code below is
            # unchanged and only the reason under it moved.]
            #
            # AND THE COMMENT THAT STOOD HERE WAS ALREADY TRUE OF THE INTENT AND FALSE OF THE
            # CODE: it said "the module does not choose an inode number and then tell the
            # record what it chose" — which was correct about the MODULE and wrong about this
            # process, which chose one and told the record. Now nobody chooses.
            if op == "FILE-CREATE" and f.get("node_type"):
                out["node_type"] = f["node_type"]
            return out
        if op == "FILE-SYMLINK":
            return {"path": path, "target": f.get("target") or ""}
        if op in ("FILE-RMDIR", "FILE-UNLINK"):
            out = {"path": path}
            for k in ("mechanism", "hidden_path"):
                if f.get(k):
                    out[k] = f[k]
            return out
        if op == "FILE-RENAME":
            return {"path": path, "new_path": f.get("new_path") or ""}
        if op == "FILE-LINK":
            return {"target_path": f.get("target_path") or "",
                    "new_path": f.get("new_path") or ""}
        if op in ("FILE-WRITE", "FILE-TRUNCATE"):
            out = dict(base)
            out["content"] = payload
            return out
        if op == "FILE-PERM":
            out = dict(base)
            out["perm"] = f.get("perm") or "644"
            return out
        if op == "FILE-CHOWN":
            out = dict(base)
            if f.get("uid") is not None:
                out["uid"] = custody._num(f["uid"], "the chown's uid")
            if f.get("gid") is not None:
                out["gid"] = custody._num(f["gid"], "the chown's gid")
            return out
        if op == "FILE-TIMES":
            out = dict(base)
            for k in ("atime", "mtime"):
                if f.get(k) is not None:
                    out[k] = float(f[k])
            return out
        if op == "FILE-OPEN":
            out = dict(base)
            if f.get("flags") is not None:
                out["flags"] = custody._num(f["flags"], "the open's flags")
            return out
        if op in ("FILE-XATTR-SET", "FILE-XATTR-LAW"):
            out = dict(base)
            out["name"] = f.get("name") or ""
            out["value"] = f.get("value") or ""
            return out
        if op == "FILE-XATTR-REMOVE":
            out = dict(base)
            out["name"] = f.get("name") or ""
            return out
        if op in ("FILE-LOCK", "FILE-UNLOCK"):
            out = dict(base)
            for k in ("ltype", "owner", "mechanism"):
                if f.get(k):
                    out[k] = f[k]
            for k in ("start", "length"):
                if f.get(k) is not None:
                    out[k] = custody._num(f[k], "the lock's " + k)
            return out
        if op == "FILE-READ-AGGREGATE":
            out = dict(base)
            for k in ("reads", "bytes"):
                if f.get(k) is not None:
                    out[k] = custody._num(f[k], "the read aggregate's " + k)
            return out
        return base


# ---------------------------------------------------------------------------
# THE GUEST-REAL SOCKET SEAM (EP-48G, design/51 N1). The RECORD decides a
# SOCKET-OPEN grant (NET-LAW-GRANT: who may open what, to where); the GUEST
# kernel opens the real socket. GUEST-ONLY (EP-00 rule 9): a real socket opens
# ONLY in the pinned guest, and this seam REFUSES on any other surface — so
# RW-HOST-SOCKET is a CAPABILITY here, not a promise. EP-48's modelled host
# table stands BESIDE this real arm (the era split), never replaced by it.
# ---------------------------------------------------------------------------

_GUEST_HOST = "gov-lab"          # the pinned guest's hostname   (kcheck.sh's surface)
_GUEST_VIRT = "kvm"              # the pinned guest's virtualisation (kcheck.sh's surface)
_SOCKET_FAMILY = {"inet": socket.AF_INET, "inet6": socket.AF_INET6, "unix": socket.AF_UNIX}


class RealSocketOnHostRefused(RuntimeError):
    """A real socket was asked for outside the pinned guest. The host arm is the
    MODELLED table (EP-48); the real arm is the guest's alone (EP-00 rule 9). A
    real socket opens in the guest or nowhere — refused, never opened on the host."""


def in_pinned_guest():
    """THE TWO SURFACES kcheck.sh READS: virt=kvm AND host=gov-lab. A real socket
    opens only where BOTH hold — the same discrimination the kernel-pin check makes,
    so a host-side call cannot masquerade as the guest (a right-shaped hostname on
    the wrong virt, or the reverse, is refused). systemd-detect-virt prints "none"
    and exits 1 on bare metal, so the value — not the exit — decides."""
    try:
        import subprocess
        virt = subprocess.run(["systemd-detect-virt"], capture_output=True,
                              text=True, timeout=5).stdout.strip()
    except Exception:
        virt = ""
    return virt == _GUEST_VIRT and socket.gethostname() == _GUEST_HOST


def open_real_socket_under_grant(gate, entity, socket_id, family, *, guest_check=in_pinned_guest):
    """Drive a SOCKET-OPEN act REAL: the RECORD decides first, and ONLY under a
    recorded grant does a real socket open in THIS (guest) kernel.

      GRANTED -> (decision_record, real_socket): a real fd in the guest kernel,
                 opened ONLY after the grant is on the record — the grant is
                 load-bearing, a refused act raises before any socket is reached.
      REFUSED -> OpError propagates from the gate; NO real socket is opened; the
                 refusal is on the record and the caller renders the errno the
                 rule-errno pack maps for the cited rule (NET-LAW-GRANT -> EACCES).

    Refuses to open a real socket outside the pinned guest (RW-HOST-SOCKET as a
    capability, not a note). The caller owns the returned socket and MUST close it."""
    # THE RECORD DECIDES FIRST. A refused grant raises here; no real socket is reached.
    decision = gate.execute("SOCKET-OPEN", entity,
                            {"entity": entity, "socket": socket_id, "family": family})
    # GRANTED on the record. The real socket opens ONLY in the guest.
    if not guest_check():
        raise RealSocketOnHostRefused(
            "a real socket may open only in the pinned guest (virt=kvm host=gov-lab, "
            "EP-00 rule 9); on the host the wire is the modelled table (EP-48)")
    fam = _SOCKET_FAMILY.get(family)     # a family the grant law does not name never reaches here
    if fam is None:
        raise RealSocketOnHostRefused("unknown socket family: %r" % (family,))
    real = socket.socket(fam, socket.SOCK_STREAM)
    return decision, real


def serve(port, ctl_path=CTL_DEFAULT, once=False):
    """Attach to the channel and answer until the module goes away.

    THE ORDER IS K1 AND IT IS ENFORCED BY THE STRUCTURE OF THIS LOOP: `handle` returns
    only after `gate.execute` has DURABLY appended (the store's `_append` writes,
    flushes and fsyncs), and the reply — which is what unblocks the caller below the
    line — is written only after `handle` returns. There is no path in this file that
    answers before the record exists."""
    fd = os.open(ctl_path, os.O_RDWR)
    try:
        while True:
            try:
                blob = os.read(fd, MSG_MAX)
            except InterruptedError:
                continue
            except OSError as e:
                # An errno from the channel is a defect in the seam, not a shutdown, and
                # it is raised rather than swallowed. EFAULT here was a real one.
                raise RuntimeError(
                    "kernel-port: the channel failed with %s. This is a defect in the "
                    "seam and not a reason to stop serving quietly." % e) from e
            if not blob:
                # The module woke every waiter and gave us nothing: it is going away.
                #
                # SAID OUT LOUD, because the silent version of this line cost a session.
                # A `copy_to_user` fault in the module also produced a zero-length read
                # here, and this loop treated it as an orderly shutdown and exited — so a
                # kernel defect presented as a clean detach, and the three messages that
                # followed (brain detached, every act refuses, read-only filesystem) were
                # all true and none of them was about the fault. An exit that cannot be
                # told from a failure is not an exit worth having.
                print("kernel-port: channel returned nothing — the module is going away",
                      flush=True)
                return
            try:
                fields, payload = parse_request(blob)
            except ValueError:
                continue
            req_id = fields.get("id", "0")
            status, out_fields, out_payload = port.handle(fields, payload)
            os.write(fd, build_reply(req_id, status, out_fields, out_payload))
            if once:
                return
    finally:
        os.close(fd)


def _close_inherited_descriptors(keep=(0, 1, 2)):
    """Drop every descriptor this process did not open, and SAY which ones (EP-28 A1).

    THE BRAIN IS THE ONE PROCESS THAT MUST NOT PIN THE FILESYSTEM IT SERVES, and that is
    a derivation rather than tidiness. The mount cannot be taken down while any process
    holds a file on it, and the mount cannot be served at all without this process — so a
    descriptor the brain is holding is one nobody can get it to release: taking the
    filesystem down requires killing the very thing that would have to close it. That
    turns T-LOCAL-FALLBACK's property, "falling back to stock files is clean and
    contained", into a property that depends on how the brain happened to be started.

    IT IS NOT HYPOTHETICAL AND IT IS WHAT R-1 ACTUALLY WAS. EP-28's acceptance battery
    holds a descriptor open on the mount (`exec 9<`) so it can prove a warm read answers
    with the brain detached, and then starts a NEW brain while that descriptor is open.
    The forked-and-exec'd brain inherits fd 9, the shell's later `exec 9<&-` closes only
    the shell's copy, and the brain then holds a file on the governed mount for the rest
    of its life. Measured: `umount` returns EBUSY and `rmmod` reports the module in use —
    the exact symptom R-1 recorded, from a cause that is not a kernel reference leak.

    THE ANSWER IS THE DAEMON'S RATHER THAN THE HARNESS'S, because the harness is only one
    caller. Any process that starts the brain while holding a file on the governed mount
    makes that mount unmountable, silently, and the brain is the only place that knows
    the rule. Descriptors 0, 1 and 2 are kept: they are the daemon's own log.

    NOTHING HERE IS SILENT. The closures are RETURNED with what they pointed at, and the
    caller prints them, because a daemon that quietly closed a descriptor its starter
    meant it to have would be trading one invisible defect for another.
    """
    closed = []
    try:
        fds = sorted(int(name) for name in os.listdir("/proc/self/fd"))
    except (OSError, ValueError):
        # No /proc: report honestly by returning nothing rather than guessing a range.
        return closed
    for fd in fds:
        if fd in keep:
            continue
        try:
            target = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            # Already gone — the directory listing's own descriptor is the usual case.
            continue
        try:
            os.close(fd)
        except OSError:
            continue
        closed.append((fd, target))
    return closed


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if len(argv) < 2:
        print(__doc__)
        return 2
    record, blobdir = argv[0], argv[1]
    ctl = argv[2] if len(argv) > 2 else CTL_DEFAULT
    for fd, target in _close_inherited_descriptors():
        print("kernel-port: closed inherited descriptor %d (%s) — a brain holding a file "
              "on the filesystem it serves is a mount nobody can take down" % (fd, target),
              flush=True)
    from bridge.mount import build_brain

    store, gate, views, blobs = build_brain(record, blobdir)
    port = KernelPort(store, gate, views, blobs)
    print("kernel-port: brain up on %s (record %s)" % (ctl, record), flush=True)
    serve(port, ctl)
    return 0


if __name__ == "__main__":
    sys.exit(main())
