"""gov-os protection layer (L3): sight-is-law + separation of powers (design 02 §3, 03 §3).

Visibility is computed from recorded grants (default-deny) AND binds action: an actor may
not consume what it could not lawfully read (VIS-4). Separation of powers: an actor may
not review or act on its own object (SOP). Dual mutually-blind audit: governance-relevant
acts are mirrored to an audit stream with a content digest, so a divergence between the
primary record and the mirror is detectable. Ported from pwc-app/src/domain/guards.js
(assertCanRead, refuse, the dual-audit mirror).
"""

import hashlib
import json

from .errors import OpError
from .store import frozen_default

SIGHT_IS_LAW = "SIGHT-IS-LAW"  # VIS-4
SOP = "SOP"                    # separation of powers

# NO CODE-RESIDENT ACTION LIST (§I5; EP-20B retires R20-1). The dual-audit action list is the
# `dual-audit-actions` category_pack — seeded at genesis, floor-protected, read through the
# views fold — and it is the ONLY source. The labeled boot fallback that used to sit here was
# unreachable (every Protection is built over a genesis'd store) and had drifted from the live
# pack, which is what a second copy of law kept in code always does. Do not restore it under
# any name: a composition whose record lacks the pack REFUSES to boot (see _audit_actions),
# because a stall that cites its rule is the honest failure and a silent substitute is not.


def _digest(e):
    body = {"seq": e["seq"], "actor": e["actor"], "action": e["action"], "payload": dict(e.get("payload") or {})}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=frozen_default).encode("utf-8")).hexdigest()[:16]


def can_read(store, actor, target, root=None):
    """The sight fold, module-level so the op interpreter (opdefs) can run the same live
    check the protection layer runs: the ROOT authority holder / SYSTEM always; otherwise a
    recorded GRANT-READ must cover the target (default-deny). The root's read exemption is the
    CHAIN-END, DERIVED (R-C1) — the caller passes the resolved chain-end as `root`; a literal
    "owner" here would keep the read exemption with a departed owner after a lawful handover,
    splitting root authority. SYSTEM stays a literal (the recorder). `root=None` (a foundingless
    or unresolved caller) exempts only SYSTEM — err closed on sight."""
    if actor == "SYSTEM" or (root is not None and actor == root):
        return True
    for e in store.by_action("GRANT-READ"):
        p = e.get("payload") or {}
        if p.get("grantee") == actor and p.get("target") in (target, "*"):
            return True
    return False


class Protection:
    def __init__(self, store, gate, views):
        self.store = store
        self.gate = gate
        self.views = views
        self._mirroring = False
        self._mirroring_b = False
        # BOOT CHECK, fail-closed (EP-20B): the audit floor must be IN THE RECORD before the two
        # streams are wired. Asked here, ahead of on_append, so a refused boot leaves no
        # half-attached mirror on the store — the protection layer either has its lawful action
        # list or it does not exist (the guardless-gate shape, gate.__init__).
        self._audit_actions()
        store.on_append(self._maybe_mirror)     # stream A
        store.on_append(self._maybe_mirror_b)   # stream B — MUTUALLY BLIND (EP-09; see _maybe_mirror_b)

    def _audit_actions(self):
        """The governance-relevant actions mirrored to the dual-audit stream, read as data
        from the `dual-audit-actions` category_pack (latest wins, through the views fold) —
        the ONE source, with no code-resident second copy behind it (EP-20B).

        A JUNK pack still never raises here, which matters because this runs inside the
        on-append mirror: a malformed pack is excluded by the fold, so the last well-formed
        pack still stands and the write path keeps committing (the EP-05 ship-blocker
        regression). Only a pack that was NEVER recorded reaches the refusal, and that is a
        boot-integrity failure, not a junk record.

        The refusal is RAISED and not recorded, deliberately: recording it would append from
        inside an append hook (re-entering this same mirror), and a composition missing its
        audit floor has no lawful way to record the fact anyway. Citation is
        CONST-RECORDING-TOTAL — the constitutional law that names this pack protected."""
        pack = self.views.category_packs().get("dual-audit-actions")
        if pack is None:
            raise OpError("CONST-RECORDING-TOTAL",
                          "the `dual-audit-actions` pack is absent from the record: the dual audit has "
                          "no lawful action list, so protection refuses to run rather than mirror "
                          "against a list held in code (law is never code-resident)")
        return {x for x in pack["levels"] if isinstance(x, str)}

    # ---- two mutually-blind audit streams (design 28 §7; EP-09) ----
    # Stream A and stream B each digest the SAME governance referents (the dual-audit-actions pack),
    # but INDEPENDENTLY: neither reads the other (a mirror record is not a governance action, so each
    # skips the other's writes), so neither can copy the other's digest and the two cannot COLLUDE to
    # hide a tampered referent. The blindness that matters is blindness of COMPUTATION — each digests
    # the primary referent, never the other stream. Both ride the sanctioned mirror direct-append
    # (a shape-safe, guard-exempt payload — the sole-appender exemption already granted to the mirror;
    # routing an audit mirror through the gate would recursively audit-mirror it). Physical file
    # separation (design §7 "separate files") is the depth-stage strengthening (signing), deferred.
    # The cross-check (dual_blind_divergences) is a THIRD party — neither writer runs it.
    def _maybe_mirror(self, e):
        if self._mirroring or e["action"] not in self._audit_actions():
            return
        if (e.get("payload") or {}).get("stream") in ("dual-audit", "dual-audit-b"):
            return
        self._mirroring = True
        try:
            self.store._append({"actor": "SYSTEM", "action": "dual-audit-record", "rule_cited": SOP,
                               "payload": {"ref_seq": e["seq"], "ref_action": e["action"],
                                           "digest": _digest(e), "stream": "dual-audit"}})
        finally:
            self._mirroring = False

    def _maybe_mirror_b(self, e):
        # Stream B — blind to A: it digests the primary referent e and NEVER reads a dual-audit-record
        # (not a governance action -> skipped). Own reentrancy guard; own stream tag + record kind.
        if self._mirroring_b or e["action"] not in self._audit_actions():
            return
        if (e.get("payload") or {}).get("stream") in ("dual-audit", "dual-audit-b"):
            return
        self._mirroring_b = True
        try:
            self.store._append({"actor": "SYSTEM", "action": "dual-audit-b-record", "rule_cited": SOP,
                               "payload": {"ref_seq": e["seq"], "ref_action": e["action"],
                                           "digest": _digest(e), "stream": "dual-audit-b"}})
        finally:
            self._mirroring_b = False

    def audit_consistent(self):
        """Stream A self-check: every A-mirror's digest matches the current digest of its referent."""
        for m in self.store.by_action("dual-audit-record"):
            p = m["payload"]
            ref = self.store.by_seq(p["ref_seq"])
            if ref is None or _digest(ref) != p["digest"]:
                return False
        return True

    def dual_blind_divergences(self, as_of=None):
        """The THIRD-PARTY cross-check (design §7): a divergence is any governance referent where the
        two mutually-blind streams and the CURRENT record do not all agree — one stream missing it, the
        streams disagreeing, or either disagreeing with the recomputed digest (a tampered referent).
        Returns the diverging ref_seqs, routed to the owner queue. Neither stream writer computes this."""
        a = {m["payload"]["ref_seq"]: m["payload"]["digest"] for m in self.store.by_action("dual-audit-record", as_of)}
        b = {m["payload"]["ref_seq"]: m["payload"]["digest"] for m in self.store.by_action("dual-audit-b-record", as_of)}
        out = []
        for ref_seq in sorted(set(a) | set(b)):
            ref = self.store.by_seq(ref_seq)
            current = _digest(ref) if ref is not None else None
            if a.get(ref_seq) != b.get(ref_seq) or a.get(ref_seq) != current:
                out.append(ref_seq)
        return out

    # ---- sight-is-law (VIS-4) ----
    def can_read(self, actor, target):
        return can_read(self.store, actor, target, self.views.chain_end())

    def assert_can_read(self, actor, target, op):
        if not self.can_read(actor, target):
            self.gate.refuse(actor, op, SIGHT_IS_LAW,
                             f"{actor} may not act on '{target}' — it could not lawfully read it (sight is law)")

    # ---- separation of powers (SOP) ----
    def assert_separation(self, actor, object_maker, op):
        if actor == object_maker:
            self.gate.refuse(actor, op, SOP, f"{actor} may not review/act on its own object (separation of powers)")


def register_protection_ops(gate, store, protection):
    def grant_read(actor, params):
        return {"actor": actor, "action": "GRANT-READ", "object": params["target"],
                             "target": params["grantee"], "rule_cited": SIGHT_IS_LAW,
                             "payload": {"grantee": params["grantee"], "target": params["target"]}}
    gate.register("GRANT-READ",
                  {"description": "grant an actor read (sight) of a target — sight is a recorded event",
                   "rules": [SIGHT_IS_LAW], "params": {"grantee": "required", "target": "required"}}, grant_read)

    def consume(actor, params):
        protection.assert_can_read(actor, params["target"], "CONSUME")  # sight binds action
        return {"actor": actor, "action": "CONSUME", "object": params["target"],
                             "rule_cited": SIGHT_IS_LAW, "payload": {"target": params["target"]}}
    gate.register("CONSUME",
                  {"description": "act on cited material (refuses unless the actor could read it)",
                   "rules": [SIGHT_IS_LAW], "params": {"target": "required"}}, consume)
