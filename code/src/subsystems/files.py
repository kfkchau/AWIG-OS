# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS files subsystem — the governed core (design 03 §4.3; doc 11/12/13, files).

Custody of information as governed record. create / write / link / unlink /
permission-change / mount are recorded, rule-cited DECISIONs; the directory tree,
inodes, and permissions are derived views (the cache, rebuilt from the record). File
content is DECISION-class and full-fidelity, content-addressed by hash, never sampled.
Deletion is remove-from-view: the master record and the blobs survive. There is no
destruction function; the only path by which local bytes leave the store is the handover
ceremony (design/46), and it is not here.

NO drivers, NO FUSE, NO in-kernel context here — this is the governed core logic in
user space, the record-based derivative under the architecture. FUSE (M2) and in-kernel
(M3) are later depth stances on this same core.
"""

# The files core op definitions (FILE-CREATE / WRITE / LINK / UNLINK / PERM / MOUNT / UNMOUNT) and
# their law-name constants were RETIRED here in EP-14B: their one authoritative home is the founding
# pack, founding/founding-pack.json. The generic interpreter re-registers them from the record at
# boot; this module keeps only its derived view. Absence is guarded by
# tests/test_ep14b.py::test_no_module_op_definition_dicts_outside_the_founding.

# WHY THIS FILE IMPORTS THE PORT'S MODULE, WHICH ITS OWN DOCSTRING SAYS IT HOLDS NONE OF
# (EP-28T). `formal_name` is not FUSE and not kernel context: it is THE ESTATE'S ONE
# DERIVATION of what a birth act founds from that act's own position in the record, landed
# as law at EP-28S (founding 1.18.0, `mints_from: record_coordinate`). Two folds read the
# same records here — this one and `CustodyState` — and before EP-28T they answered two
# different identities for the same file, because this one carried the pre-1.14.0 regime in
# a default nobody re-read. Copying the arithmetic across the boundary would have made that
# a permanent second computer; charter §A52's own answer is that a boundary is crossed by a
# SHARED DERIVATION, so the derivation is imported rather than reproduced.
#
# RAISED, NOT SOLVED HERE: `formal_name`'s HOME is wrong. It lives in the port's module for
# historical reasons and it is law-level, so the governed core now depends on the bridge —
# an inversion of the layering this file's docstring states. Moving it is out of EP-28T's
# fence (`custody.py` is not in it) and it is a mentor's ruling, not a builder's edit.
from bridge.custody import formal_name

# The departure view (EP-41B): a handed-over hash resolves to the DEPARTURE marker here, not to a
# crash or an empty. Inert until a handover ceremony has appended a departure record — the
# founding-held mechanism (MOVER 4).
from kernel import erasure


class FilesView:
    """Every current file answer is a fold over the record (design 03 §4.3, doc 13 §3)."""

    def __init__(self, store, blobs):
        self.store = store
        self.blobs = blobs

    def tree(self, as_of=None):
        """The active directory tree: create adds, link adds a name, unlink removes."""
        present = {}
        # K12 FAMILY SOURCE (MAINT-K12-SUBSYSTEM-VIEWS; design/36 ADDENDUM S). This tree answer
        # depends only on the FILE-CREATE / FILE-LINK / FILE-UNLINK records, so it reads that
        # family through the existing config-keyed projection (store.action_set_projection, built
        # by MAINT-K12-CEILING-FOLD) rather than the whole record — a family-scoped answer must
        # not cost records it does not depend on. Only the iteration SOURCE moves; the fold body
        # below (and its EP-28T identity cases) is byte-identical.
        for e in self.store.action_set_projection(
                {"FILE-CREATE", "FILE-LINK", "FILE-UNLINK"}).all(as_of):
            a, p = e["action"], (e.get("payload") or {})
            if a == "FILE-CREATE":
                # WHAT NAMES THE THING THIS ACT FOUNDS (EP-28T, completing EP-28S's landing).
                # Two total cases, decided from the RECORD and never from today's law, which
                # is `CustodyState.apply`'s rule read here rather than a second rule:
                #
                #   the record NAMES an identity   -> that is what named it, and it keeps it
                #   the record NAMES NONE          -> the act's own coordinate names it
                #
                # THIS LINE USED TO READ `p.get("inode", p["path"])`. Under founding 1.18.0
                # no birth record names an identity at all, so that default fired on EVERY
                # create and this fold silently answered PATH-AS-IDENTITY — the regime
                # EP-28S deleted, surviving in a second fold, in the one way that shows
                # nowhere: this view's only consumers compare a tree against another tree
                # built from the same record, so both sides were wrong together and agreed.
                #
                # THERE IS NO FALLBACK LEFT. A birth act whose coordinate is absent or
                # unreadable REFUSES through `formal_name`'s own door, citing its rule — the
                # loud path EP-28T §1 requires, and the same refusal the mount gives, because
                # it is the same function.
                identity = p.get("inode")
                if identity is None:
                    identity = formal_name(e.get("seq"))
                present[p["path"]] = identity
            elif a == "FILE-LINK":
                # OFF-SEED AND UNTOUCHED, REPORTED RATHER THAN REPAIRED (EP-28T). This
                # carries the SAME shape as the line above: a link naming a target this fold
                # has never bound substitutes the TARGET PATH as the new name's identity,
                # silently. It is out of EP-28T's directed work — the repair above lands
                # without it — so it waits on a one-line fence ruling and is PINNED by
                # `tests/test_ep28t.py::TheOffSeedSiteIsPinnedRatherThanRemembered` so the
                # ruling is checkable rather than remembered. Two facts are already derived
                # there: the branch is unreachable through the gate (a FILE-LINK on an
                # unbound target is refused), and the definitive fold binds only where the
                # target is bound instead of substituting.
                present[p["new_path"]] = present.get(p["target_path"], p["target_path"])
            elif a == "FILE-UNLINK":
                present.pop(p["path"], None)
        return present

    def perms(self, path, as_of=None):
        perm = None
        # K12 FAMILY SOURCE (MAINT-K12-SUBSYSTEM-VIEWS): a path's live permission depends only on
        # its FILE-CREATE / FILE-PERM records; read that family, not the whole record. Fold body
        # byte-identical.
        for e in self.store.action_set_projection(
                {"FILE-CREATE", "FILE-PERM"}).all(as_of):
            a, p = e["action"], (e.get("payload") or {})
            if p.get("path") == path and a in ("FILE-CREATE", "FILE-PERM"):
                perm = p.get("perm", perm)
        return perm

    def content_at(self, path, as_of=None):
        """Time-travel: the file's exact bytes as of T, fetched by the recorded hash.

        THE DEPARTURE (design/46 member 4). If the hash this path resolved to has had its custody
        handed over by a recorded handover ceremony, the answer is the DEPARTURE marker — not the
        bytes (handed over, gone locally), not None (that means no write), not a crash (`blobs.get`
        would raise on the missing file). The departure is read from the LIVE record (no `as_of`):
        the local bytes are a fact of the physical NOW, so a read as-of a time before the ceremony
        still answers the departure (design/23 Option C — replay reproduces the DEPARTED state).
        Inert until a ceremony fires: with no departure record the departed set is empty and this
        returns exactly what it always did."""
        h = None
        for e in self.store.by_action("FILE-WRITE", as_of):
            if (e.get("payload") or {}).get("path") == path:
                h = e["payload"]["content_hash"]
        if h is None:
            return None
        # The departed set is read through the K12 action-scoped projection (design/36 ADDENDUM S),
        # the same family-scoped source this file's other folds use: a content read must not cost the
        # whole record when it depends only on the handover family (which is empty in every world that
        # has run no ceremony).
        if h in erasure.departed_hashes(
                self.store.action_set_projection({erasure.HANDOVER_OP}).all()):
            return erasure.DEPARTURE
        return self.blobs.get(h)

    def history(self, path, as_of=None):
        # K12 FAMILY SOURCE (MAINT-K12-SUBSYSTEM-VIEWS): a path's history is folded from its
        # FILE-CREATE / FILE-WRITE / FILE-PERM / FILE-UNLINK records; read that family, not the
        # whole record. The filter body is byte-identical.
        return [e for e in self.store.action_set_projection(
                    {"FILE-CREATE", "FILE-WRITE", "FILE-PERM", "FILE-UNLINK"}).all(as_of)
                if (e.get("payload") or {}).get("path") == path
                and e["action"] in ("FILE-CREATE", "FILE-WRITE", "FILE-PERM", "FILE-UNLINK")]
