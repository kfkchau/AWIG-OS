# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS syscall port (L5): map Linux syscalls onto governed ops (design 03 §5, doc 10).

The compatibility contract: a syscall (name, args) translates to a AWIG OS op at the gate;
the result translates back to a return value, and a governed refusal maps to the errno
userland expects AND is additionally recorded as a rule-cited refusal (03 §0 inverted: the
record explains, the ABI stays silent in the old vocabulary). This is the host-testable
translation layer; live interception (ptrace/seccomp/in-kernel) is the depth-stage concern.
Only the mainstream calls a normal userland exercises are mapped (doc 10 §12); driver and
arch-specific calls are out (D8).
"""

from collections.abc import Mapping

from .errors import OpError

# syscall -> (AWIG OS op, args->params). The syscall->op NAME mapping is law-as-data: it is
# seeded at genesis as the `syscall-ops` category_pack and read through the views fold, so
# reclassifying a syscall is an amendment. This literal is the labeled boot FALLBACK for the
# op names (used only if the pack is absent). The arg->params MAPPERS stay code — they are
# mechanism (how args translate), not governance content (§I5, EP-02).
SYSCALL_MAP = {
    "open":    ("FILE-CREATE", lambda a: {"path": a["path"]}),
    "write":   ("FILE-WRITE",  lambda a: {"path": a["path"], "content": a["content"]}),
    "unlink":  ("FILE-UNLINK", lambda a: {"path": a["path"]}),
    "chmod":   ("FILE-PERM",   lambda a: {"path": a["path"], "perm": a["perm"]}),
    "mmap":    ("MEM-GRANT",   lambda a: {"region": a["addr"], "size": a["length"], "holder": a.get("holder", "proc")}),
    "mount":   ("MOUNT",       lambda a: {"mount_point": a["target"], "source": a.get("source"), "fs_type": a.get("fstype")}),
    "socket":  ("COMMS-OPEN",  lambda a: {"channel": a["channel"]}),
    "sendmsg": ("COMMS-SEND",  lambda a: {"channel": a["channel"], "message": a["message"], "to": a.get("to")}),
}

# a governed refusal's cited rule -> the errno userland expects. Law-as-data: seeded at
# genesis as the `rule-errno` category_pack and read through the views fold. This literal is
# the labeled boot FALLBACK, used only if that pack is absent (§I5, EP-02).
RULE_TO_ERRNO = {
    "MEM-LAW-BUDGET": "ENOMEM", "FS-LAW-PERM": "EACCES", "FS-LAW-NAMESPACE": "EACCES",
    "CAP-IS-LAW": "EPERM", "SIGHT-IS-LAW": "EACCES", "P3-CLOSURE": "ENOSYS", "ROOT-NEG-6": "EEXIST",
}


class SyscallPort:
    def __init__(self, gate, views):
        self.gate = gate
        self.views = views

    def _syscall_ops(self):
        """syscall name -> op, read as data from the `syscall-ops` pack (fallback: code).
        Only well-formed entries are taken — a junk level is skipped, never crashes."""
        pack = self.views.category_packs().get("syscall-ops")
        if pack:
            return {lvl["syscall"]: lvl["op"] for lvl in pack["levels"]
                    if isinstance(lvl, Mapping) and "syscall" in lvl and "op" in lvl}
        return {n: op for n, (op, _m) in SYSCALL_MAP.items()}  # FALLBACK

    def _errno_for(self, rule):
        """cited rule -> errno, read as data from the `rule-errno` pack (fallback: code)."""
        pack = self.views.category_packs().get("rule-errno")
        if pack:
            for lvl in pack["levels"]:
                if isinstance(lvl, Mapping) and lvl.get("rule") == rule:
                    return lvl.get("errno", "EINVAL")
            return "EINVAL"
        return RULE_TO_ERRNO.get(rule, "EINVAL")  # FALLBACK

    def _mapper(self, name):
        """The arg->params mapper stays code (mechanism, not law). A syscall present in the
        pack but with no code mapper is not serviceable."""
        return (SYSCALL_MAP.get(name) or (None, None))[1]

    def syscall(self, name, actor, args):
        op = self._syscall_ops().get(name)
        mapper = self._mapper(name)
        if op is None or mapper is None:
            # a syscall mapping to no op (or with no code mapper) is a Closure Hit -> ENOSYS
            return {"errno": "ENOSYS", "note": f"syscall '{name}' not in the conformance map"}
        try:
            rec = self.gate.execute(op, actor, mapper(args))
            return {"ok": True, "seq": rec["seq"], "op": op}
        except OpError as e:
            return {"errno": self._errno_for(e.rule), "rule": e.rule}

    def conformance(self):
        # only syscalls that are BOTH mapped to an op AND have a code arg-mapper — i.e. the
        # calls syscall() can actually service. Never over-report a capability the port lacks.
        return sorted(n for n in self._syscall_ops() if self._mapper(n) is not None)
