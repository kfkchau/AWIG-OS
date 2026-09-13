# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS protection layer (L3): sight-is-law + separation of powers (design 02 §3, 03 §3).

Visibility is computed from recorded grants (default-deny) AND binds action: an actor may
not consume what it could not lawfully read (VIS-4). Separation of powers: an actor may
not review or act on its own object (SOP). Dual mutually-blind audit: governance-relevant
acts are mirrored to an audit stream with a content digest, so a divergence between the
primary record and the mirror is detectable. Ported from pwc-app/src/domain/guards.js
(assertCanRead, refuse, the dual-audit mirror).
"""

import hashlib
import json
from collections.abc import Mapping

from .canonical import canonical_hash
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


def _digest(e, algo="json"):
    """The dual-audit content digest, ERA-SPLIT at EP-35's boundary (re-home rows 1 & 2; D4).

    `algo="canonical"` — the NEW era: the body is serialized through the estate's ONE canonical
    serializer (design/37 §4's floor) rather than the ambient JSON dump (the named wrong reference,
    §5), and the None/absent-payload boundary is UNIFIED (payload -> {} exactly as the JSON branch
    already normalizes it), so this copy and views.digest_of agree everywhere — the drift the U-B
    exemption tolerated is closed for new records. The 16-char cross-check width and the
    {seq, actor, action, payload} subject are unchanged; the algorithm rides the mirror record as
    DATA (`digest_algo`), never a minted calibration pack (§8-h item-F bind). It calls the floor's
    own `canonical_hash`, never a raw hashlib over canonical bytes, so the one-serializer guard sees
    no new governed site.

    `algo="json"` (default) — the PRE-ERA serializer, kept BYTE-IDENTICAL to the pre-EP-35 function.
    Mirror records written before the seal carry no `digest_algo` and are NEVER rewritten, so they
    verify under exactly what wrote them, forever (era-split; the past byte-untouched)."""
    if algo == "canonical":
        body = {"seq": e["seq"], "actor": e["actor"], "action": e["action"],
                "payload": dict(e.get("payload") or {})}
        return canonical_hash(body).split(":", 1)[1][:16]
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
    def __init__(self, store, gate, views, key_a_custody=None, key_b_custody=None):
        self.store = store
        self.gate = gate
        self.views = views
        self._mirroring = False
        self._mirroring_b = False
        # PER-STREAM SIGNING KEYS (EP-39; the EP-09 physical-separation deferral landing, design/37 Q4/§9).
        # Each stream signs with its OWN key's PUBLIC custody hash (vault-class custody, from
        # keys.seal_system_key / vault.seal — NO read path, §8-h). `None` => the stream is unkeyed: it
        # mirrors WITHOUT a signature, byte-for-byte as before this field existed — so every existing
        # composition and every pre-ceremony production world is unchanged (the EP-35 era-split shape; A2).
        # The two homes stay SEPARATE and no signing path reaches both (§8-e / RW2: a shared signer is the
        # EP-09 shared-digest cap in signing dress). On a single-owner box both may still sit with one
        # person — the property delivered is that they CAN separate with the checking machinery unchanged.
        self._stream_a_key = key_a_custody
        self._stream_b_key = key_b_custody
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
    def _mirror_payload(self, e, stream):
        """The mirror record's payload, ERA-TAGGED (EP-35 re-home). After the store's prefix is
        sealed the digest is computed through canonical form and the mirror NAMES its algorithm
        (`digest_algo`, D4); before the seal it is the pre-era JSON digest with NO tag — so a
        pre-seal mirror serialises byte-for-byte as it did before this field existed (the past
        byte-untouched) and verification recovers the era from the mirror it reads."""
        algo = "canonical" if self.store._chain_anchored() else "json"
        payload = {"ref_seq": e["seq"], "ref_action": e["action"],
                   "digest": _digest(e, algo), "stream": stream}
        if algo != "json":
            payload["digest_algo"] = algo
        return payload

    def _maybe_mirror(self, e):
        if self._mirroring or e["action"] not in self._audit_actions():
            return
        if (e.get("payload") or {}).get("stream") in ("dual-audit", "dual-audit-b"):
            return
        self._mirroring = True
        try:
            payload = self._mirror_payload(e, "dual-audit")
            sig = self._sign_stream_a(payload["ref_seq"], payload["digest"])   # A's key ONLY
            if sig is not None:
                payload["sig"] = sig
            self.store._append({"actor": "SYSTEM", "action": "dual-audit-record", "rule_cited": SOP,
                               "payload": payload})
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
            payload = self._mirror_payload(e, "dual-audit-b")
            sig = self._sign_stream_b(payload["ref_seq"], payload["digest"])   # B's key ONLY
            if sig is not None:
                payload["sig"] = sig
            self.store._append({"actor": "SYSTEM", "action": "dual-audit-b-record", "rule_cited": SOP,
                               "payload": payload})
        finally:
            self._mirroring_b = False

    # ---- per-stream signing: two keys, two paths that never meet (EP-39; §8-e) ------------------
    # THE TRAP THIS REFUSES (design/37 "THE REFERENCE TO AVOID"): one signer module both streams call.
    # A shared signer collapses exactly the property the two keys keep — whoever holds the one signer
    # holds both streams. So there is NO shared signing path: `_sign_stream_a` names only the A key and
    # `_sign_stream_b` only the B key, and the A3 key-path guard proves neither can reach the other's.
    def _sign_stream_a(self, ref_seq, digest):
        """Stream A's signature — bound under STREAM A's key custody ONLY. This path names its own key
        and no other's, so holding A's key extends stream A alone (§8-e; the A3 key-path guard proves the
        two paths reach no common key). A signature is possession-in-custody + minted provenance (the
        keys.countersign pattern): it binds the mirror's content (ref_seq, digest, stream) under the key's
        PUBLIC custody hash and reads NO sealed value back (§8-h vault closure). None when the stream is
        unkeyed — the mirror then carries no signature, exactly as before EP-39 (the era-split shape; A2)."""
        if self._stream_a_key is None:
            return None
        return {"custody": self._stream_a_key, "ref_seq": ref_seq, "digest": digest, "stream": "dual-audit"}

    def _sign_stream_b(self, ref_seq, digest):
        """Stream B's signature — the mirror image of the stream-A path, bound under STREAM B's key custody
        ONLY and naming its own key and no other's. Separate home, separate path: no signer both streams
        call (§8-e / RW2). None when the stream is unkeyed."""
        if self._stream_b_key is None:
            return None
        return {"custody": self._stream_b_key, "ref_seq": ref_seq, "digest": digest, "stream": "dual-audit-b"}

    @staticmethod
    def _verify_mirror_sig(mirror_payload, expected_custody, stream):
        """Verify one mirror's per-stream signature — part of the THIRD-PARTY cross-check (design §7's
        neutral verifier), from PUBLIC data ONLY: it holds both public custody hashes and reads no sealed
        value, so verifying is not a signing path and does not touch the separation (§8-h). A mirror with
        NO `sig` verifies VACUOUSLY — pre-ceremony and pre-EP-39 mirrors behave exactly as before, so the
        cross-check regression is unchanged (A2, the era-split shape). A present signature must bind THIS
        mirror's content under the EXPECTED stream's key: the OTHER stream's signature (custody != expected)
        FAILS and is routed like divergence (A1 / RW1). Derived on demand, never a recorded mirror."""
        sig = mirror_payload.get("sig")
        if sig is None:
            return True
        return (isinstance(sig, Mapping)   # a stored sig is a frozen mapping (deep-freeze, EP-02)
                and sig.get("custody") == expected_custody
                and sig.get("ref_seq") == mirror_payload.get("ref_seq")
                and sig.get("digest") == mirror_payload.get("digest")
                and sig.get("stream") == stream)

    def audit_consistent(self):
        """Stream A self-check: every A-mirror's digest matches the current digest of its referent,
        RECOMPUTED UNDER THE ERA THE MIRROR RECORDS (EP-35 era-split, D4). A mirror carrying no
        `digest_algo` was written before the seal and verifies under the pre-era JSON serializer;
        a `canonical` tag verifies through the floor — so a mirror never false-diverges from a
        referent it still matches, across the boundary."""
        for m in self.store.by_action("dual-audit-record"):
            p = m["payload"]
            ref = self.store.by_seq(p["ref_seq"])
            if ref is None or _digest(ref, p.get("digest_algo", "json")) != p["digest"]:
                return False
        return True

    def dual_blind_divergences(self, as_of=None):
        """The THIRD-PARTY cross-check (design §7): a divergence is any governance referent where the
        two mutually-blind streams and the CURRENT record do not all agree — one stream missing it, the
        streams disagreeing, or either disagreeing with the recomputed digest (a tampered referent).
        Each stream's digest is recomputed under THE ERA THAT STREAM RECORDED (EP-35 era-split), so a
        referent mirrored before the seal and one mirrored after are each checked honestly.
        Returns the diverging ref_seqs, routed to the owner queue. Neither stream writer computes this."""
        a = {m["payload"]["ref_seq"]: m["payload"] for m in self.store.by_action("dual-audit-record", as_of)}
        b = {m["payload"]["ref_seq"]: m["payload"] for m in self.store.by_action("dual-audit-b-record", as_of)}
        # R7 (EP-MAINT-OUTSIDE-4): the expected set is the RETAINED GOVERNANCE ACTIONS in the record,
        # not merely the refs the streams happen to hold. A governance action present in the record but
        # absent from BOTH streams is a divergence the old union (set(a) | set(b)) could never see — it
        # named neither stream, so it fell out of the enumeration and no cross-check ever ran on it. The
        # expected referents are exactly the acts the `dual-audit-actions` pack says get mirrored.
        audit = self._audit_actions()
        expected = {e["seq"] for e in self.store.all(as_of) if e["action"] in audit}
        out = []
        for ref_seq in sorted(expected | set(a) | set(b)):
            ref = self.store.by_seq(ref_seq)
            pa, pb = a.get(ref_seq), b.get(ref_seq)
            # R7: a retained governance referent missing from EITHER stream is a divergence — a stream
            # that never mirrored a governance act it was supposed to has diverged from the record,
            # whether or not the other stream did. This catches the absent-from-both case the digest
            # comparison below cannot (None != None is False), and the absent-from-one case alike.
            if ref_seq in expected and (pa is None or pb is None):
                out.append(ref_seq)
                continue
            da = pa["digest"] if pa else None
            db = pb["digest"] if pb else None
            ca = _digest(ref, pa.get("digest_algo", "json")) if (ref is not None and pa) else None
            cb = _digest(ref, pb.get("digest_algo", "json")) if (ref is not None and pb) else None
            # SIGNATURE VERIFICATION ADDED BESIDE THE DIGEST READ (EP-39; §8-g — the digest comparison
            # above is UNCHANGED, this is an extra term never a new comparison). A signed mirror that
            # carries the wrong stream's signature routes here like any other divergence; an unsigned
            # mirror verifies vacuously, so this OR-term is inert in every pre-EP-39 world (A2).
            sig_a_ok = self._verify_mirror_sig(pa, self._stream_a_key, "dual-audit") if pa else True
            sig_b_ok = self._verify_mirror_sig(pb, self._stream_b_key, "dual-audit-b") if pb else True
            if da != db or (pa and da != ca) or (pb and db != cb) or not sig_a_ok or not sig_b_ok:
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
