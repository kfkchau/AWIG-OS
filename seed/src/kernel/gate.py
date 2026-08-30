"""gov-os kernel — the gate (L1): the single registered write path.

Ported from pwc-app/src/core/registry.js and the refuse() idiom in
src/domain/guards.js. Every act crosses here as a registered operation and produces
EXACTLY ONE appended record: the decision the op requested (its handler appends it),
or a refusal citing the rule that refused. There is no third outcome and no write
path to the record that bypasses the gate (design 02 §1.2; SC1).

An unregistered op does not exist — a Closure Hit (the bank has no counter, P3).
Enumeration of the registry IS the completeness guarantee.
"""

import threading

from . import opdefs
from .errors import OpError

# =====================================================================================
# THE DECIDE REGION (EP-28G W1) — the serialization single-threading was silently supplying
# =====================================================================================
#
# WHAT THIS IS, AND WHY IT IS A CREATE RATHER THAN A MOVE. Until this construct existed,
# `gate.py` held NO serialization of any kind: the append site below was bare, and the
# sequentiality EP-28 ADDENDUM 10.7 described ("the gate stays sequential so no
# check-then-append race exists") was an EMERGENT PROPERTY of single-threading — one caller
# at `govosfs.c:120`, `store._append` blocking until durable. Nobody built it, nobody could
# point at it, and it ends the moment a second caller exists. This is the citable enforcer
# that property never had.
#
# WHAT IT PROTECTS IS DECISION CONSISTENCY, and that is a different subject from the store's
# single-writer discipline. The store's write lock makes two appends land one after the
# other; it does nothing about two deciders that BOTH read the same pre-state and both then
# append. `opdefs.create_op` reads `gate.has(name)` and refuses ROOT-NEG-6 if the name is
# taken — two concurrent CREATE-OPs of one name both pass that read and both append, and the
# registry ends up with a definition shadowing another. Read the folded state, decide against
# it, append: atomically with respect to other decides. That is this region and nothing else.
#
# ADDENDUM 1's identity is why "decide" and "append" were never two steps to fuse: THE
# DECISION IS THE RECORD. Matching an act against the criteria renders the go/no-go and
# produces the record content in the same move — either a refusal citing the rule it failed
# or the new record citing the rules it matched. The region is the atomicity of ONE act.
#
# THE DURABILITY WAIT IS OUTSIDE, and the reason is structural rather than a preference.
# Deciding needs a consistent fold; ordering needs a monotone `seq`; DURABILITY NEEDS
# NEITHER. One appender writes every record into ONE append-only file through one held
# descriptor and `fdatasync` is cumulative, so durability arrives in file order and a crash
# leaves a PREFIX (measured at EP-28 W8: an unsynced record's file did not exist at all —
# never short, never torn). A decide may therefore lawfully read a record that is appended
# but not yet durable, because anything depending on it sits LATER in the same file: if the
# dependent act ever becomes durable, so did what it depended on. No durable record can ever
# cite a lost one. (EP-28C AMENDMENT 3 §3.3, and the condition it names: this is structural
# for the RECORD FILE alone.) Holding the region across the barrier would be the big lock —
# one record ever in flight, every batch closed at one, single-threading rebuilt with a
# lock's name on it. `store._commit_batch` asserts, on EVERY barrier, that the calling thread
# does not hold this region.
#
# IT IS RE-ENTRANT, AND THAT IS LOAD-BEARING RATHER THAN A CONVENIENCE. The dual-audit mirror
# appends from inside an on-append listener (`protection.py:106`, `:121`), which runs inside
# the region's span; the overturn sweep re-enters `execute` from inside `_maybe_sweep`. A
# region excluding its own thread would DEADLOCK on the mirror. It admits its own thread and
# excludes other decides — it excludes other deciders, not its own consequences.
#
# THE DEPTH IS PER-THREAD AND GLOBAL ACROSS GATES, deliberately. The lock is per-gate (two
# worlds decide independently), but "is this thread inside a decide region" is asked by the
# barrier, which belongs to a store and knows nothing of gates. A thread holding world A's
# region while barriering world B's store would trip the assertion; no such path exists in
# this estate, and if one is ever written the red is the finding rather than a false alarm.
_REGION_DEPTH = threading.local()


def decide_region_held():
    """Is the calling thread inside a decide region? Read by the durability barrier, which is
    the one place the region's exclusion law can be asserted on EVERY execution — a scan of
    the span cannot see a lock still HELD while the barrier runs further down the call
    chain, in `commit.py`, which is exactly the failure mode."""
    return getattr(_REGION_DEPTH, "n", 0) > 0


class DecideRegion:
    """The construct. `enter()` returns True for the OUTERMOST entry on this thread, which is
    the entry that owns the durability wait for everything the act published."""

    __slots__ = ("_lock",)

    def __init__(self):
        self._lock = threading.RLock()

    def enter(self):
        self._lock.acquire()
        n = getattr(_REGION_DEPTH, "n", 0)
        _REGION_DEPTH.n = n + 1
        return n == 0

    def exit(self):
        _REGION_DEPTH.n = getattr(_REGION_DEPTH, "n", 1) - 1
        self._lock.release()

    def held_by_current_thread(self):
        return decide_region_held()


# Root rules (boot-established; design/12 §0 rule namespace).
P3_CLOSURE = "P3-CLOSURE"  # invoked op is not registered -> Closure Hit
AR2 = "AR-2"               # nonconforming call (a required parameter is missing)

# AUTHORITY REGIME IS DATA (EP-17 Y2; the mentor's #1a, retiring the code constant that named the
# four power-structure ops). The ops that WRITE the power structure — grant/revoke/space/role — are
# governed by ATTENUATION, not a covering grant: gating the creation of a grant BY a covering grant
# would be circular (a grant to make a grant) and would wedge lawful delegation. WHICH regime governs
# an op is jurisdictional LAW, read from the op's OWN definition record (`definition.authority_regime`:
# "attenuation-family" for those four, the default "covers" for every other op), NEVER a hardcoded verb
# list — data over code, so a cold reader of the founding pack sees which law governs the op. The
# retired constant was `AUTHORITY_STRUCTURE_ACTIONS = ("GRANT","REVOKE","CREATE-SPACE","CREATE-ROLE")`.

# A full-form law's `when` tests the six closed trigger dimensions (design 28 §4) — action /
# actor / object / rule_cited / refused / payload_kind — the SAME closed vocabulary as the view
# triggers (views.VIEW_FILTER_DIMENSIONS, the one named engine surface; not re-declared here).
def _draft_dimension(draft, dim):
    if dim == "payload_kind":
        p = draft.get("payload")
        return p.get("kind") if isinstance(p, dict) else None
    return draft.get(dim)


def _draft_matches(draft, when):
    """Does a draft satisfy a law's `when` (a LIST of trigger patterns)? EVERY pattern must hold;
    a pattern is a dict of dimension->value with an optional {"not": true} = the trigger-level
    minus (the draft must NOT match this pattern). Reads only the six closed dimensions; a
    view-definition's DICT `when` is not a law trigger and never reaches here (callers list-guard)."""
    for pattern in when:
        neg = bool(pattern.get("not"))
        dims = {k: v for k, v in pattern.items() if k != "not"}
        hit = all(_draft_dimension(draft, k) == v for k, v in dims.items())
        if hit == neg:  # (neg and hit) or (not neg and not hit) -> this pattern fails the chain
            return False
    return True


class Gate:
    def __init__(self, store, views):
        self.store = store
        self.ops = {}  # name -> {"meta": {...}, "handler": fn}
        if views is None:
            # R16: a MISSING arg already raised; an explicit None slipped through and left the
            # constitution guard no-oping (the dead early-return below). Reject the VALUE, not just
            # the arity — a gate that cannot read the recorded law must be unconstructable, period.
            raise ValueError("Gate requires a views object — a gate without its constitution guard is unconstructable")
        self.views = views  # REQUIRED (EP-05C C0): the constitution guard reads the recorded law
        #                     through it — a gate whose guard is unwired must be UNCONSTRUCTABLE,
        #                     never silently fail-open. (Was a post-hoc gate.views = views.)
        self.blobs = None  # set when the full kernel composes; content_params ops (FILE-WRITE,
        #                    COMMS-SEND) put full-fidelity content here and record the hash.
        self.vault = None  # set when the full kernel composes; secret_params ops (SEAL-SECRET) seal
        #                    the value here (no read path) and record the hash; secret_verify ops
        #                    (VERIFY-SECRET) compare a candidate against a sealed hash. EP-19 (J8).
        # ---- the sweep's serialization state (EP-26; design/36 ADDENDUM A.5) ----
        # SWEEPS SERIALIZE against law-family arrivals. Replay reproduces whatever record order
        # occurred either way, so replay-determinism survives an interleaving — but the RESULT of
        # two identical inputs would then depend on the interleaving, and this estate's
        # determinism standard (design/21) is stronger than that. A law-family arrival that lands
        # while a sweep is running is HELD (never interleaved, never refused): the running sweep
        # reaches its fixed point and commits, and the held arrival is then accepted so its own
        # sweep computes candidates from the settled record.
        self._sweep_active = 0
        self._law_queue = []
        # ---- THE DECIDE REGION (EP-28G W1) ----
        # The construct whose derivation is at the head of this module. Its span is the whole
        # of `execute` — the fold read in the handler through the append — and the durability
        # wait sits outside it, released at `execute`'s outermost exit.
        self.region = DecideRegion()
        # Observability only: what the sweeps did, in memory, appended NOWHERE. Nothing
        # load-bearing reads it and killing it changes no answer (the EP-22 aggregate's
        # discipline — a ledger of numbers is not a stored status).
        self.sweeps = []

    # ---- the authority-step dimensions (EP-17; design/31 J3, J5) ---------------------------
    def _info_kind(self, pdict):
        """The INFO-KIND dimension of an act for the gate authority step (design/31 J3: 'a rule
        is info of kind law'). A payload.kind names the kind for the SHAPED records (category_pack,
        op_definition, view_definition, verdict, ...); a bare LAW record (a rule_id with no kind)
        is info of kind 'law' — the info-type that makes rule-writing an ordinary grant with no
        rule-specific machinery; a payloadless act (CREATE-INFO carries its content as the object)
        declares no kind. Under the founding openness grant (info = *) the exact value never gates;
        it gates only once the owner narrows a grant by info kind."""
        if pdict is None:
            return None
        if pdict.get("kind") is not None:
            return pdict.get("kind")
        if pdict.get("rule_id") is not None:
            return "law"
        return None

    def _act_space(self, record, pdict):
        """The SPACE an act binds/lives in for the gate authority step. A law carries its binding
        SCOPE (J5 — 'rules have scope'); every other record uses the default-space fold (an explicit
        payload.space, or the mother space). A non-dict/absent payload has no space -> the mother
        space, so the founding openness grant still covers it and a malformed payload keeps refusing
        at the constitution guard's AR-2 branch rather than at authority."""
        if pdict is None:
            return self.views.mother_space()
        if pdict.get("scope") is not None:
            return pdict["scope"]
        return self.views.space_of(record)

    def _grant_containment(self, actor, name, result):
        """R-A (EP-18) — GRANT's leash, MOVED from its handler to the gate's chokepoint. A grant is
        never wider than its maker (design/31 E1; attenuation): the (actions x info x space) triple
        must be contained whole within a single covering grant of the maker (`within_makers_reach`).
        Enforcing this in GRANT's handler let a PASSTHROUGH route minting a grant-kind record bypass it
        (the campaign-1 ship-blocker shape — enforcement in a handler, not at the write chokepoint); at
        the gate it fires on ANY op that mints a grant-kind record. INERT under openness (the maker's
        reach is the whole tree). Refuses ROOT-NEG-3 — the same family citation."""
        p = result.get("payload") if isinstance(result.get("payload"), dict) else {}
        proposed = {"grantee": p.get("grantee"), "actions": p.get("actions"),
                    "info": p.get("info"), "space": p.get("space")}
        ok, reason = self.views.within_makers_reach(actor, proposed)
        if not ok:
            self.refuse(actor, name, "ROOT-NEG-3", reason)

    def _attenuation_family_leash(self, actor, name, result):
        """EP-17 Y2/Y3 + EP-18 R-A/R-B — the attenuation-family regime (grant/revoke/space/role): the
        ops that WRITE the power structure are governed by ATTENUATION, not a covering grant. Every
        power arrives with its leash in the same round (design/31 J3, E1; the mentor's #1/#6). ALL
        INERT under the founding openness grant (its reach is the whole tree), so a fresh founding
        refuses none of these; a narrowed world observes both directions. Each refuses ROOT-NEG-3 —
        one family (a chain reaches the account but does not authorise THIS structural act):
          * GRANT (or any grant-kind record — R-A) — a grant is never wider than its maker;
            `_grant_containment`, now at the gate so a passthrough route cannot bypass it.
          * REVOKE — you may take away only what you could give: the revoked grant's COVER must be
            within the revoker's own reach (the same attenuation arithmetic on the target grant). The
            revoke is still a DRAFT here, so the grant fold still shows the grant being revoked.
          * CREATE-SPACE — a STRUCTURE-CLASS action over the PARENT (R-B): a space is founded only
            where its founder holds structural authority, not mere sight (sight is not authority).
          * CREATE-ROLE — a STRUCTURE-CLASS action over its SPACE (R-B): likewise for a role."""
        p = result.get("payload") if isinstance(result.get("payload"), dict) else {}
        act = result.get("action")
        if act == "GRANT" or p.get("kind") == "grant":    # R-A: the grant leash, at the gate for any op
            self._grant_containment(actor, name, result)
        elif act == "REVOKE":
            revoked = self.views.grants().get(result.get("object"))
            if revoked is not None:                       # revoking a non-live grant is inert (nothing to bar)
                cover = {"grantee": revoked.get("grantee"), "actions": revoked.get("actions"),
                         "info": revoked.get("info"), "space": revoked.get("space")}
                ok, reason = self.views.within_makers_reach(actor, cover)
                if not ok:
                    self.refuse(actor, name, "ROOT-NEG-3",
                                f"{actor} may revoke only a grant whose cover is within its own reach "
                                f"(you may take away only what you could give) — {reason}")
        elif act == "CREATE-SPACE":
            parent = p.get("parent")
            if not self.views.reaches_space_structural(actor, parent, "CREATE-SPACE"):
                self.refuse(actor, name, "ROOT-NEG-3",
                            f"{actor} holds no grant carrying CREATE-SPACE over parent space {parent} — a space "
                            f"is founded only where its founder holds authority for THAT act, not mere sight and "
                            f"not another structure-class action (R-B exact-action, R-C3; the family leash)")
        elif act == "CREATE-ROLE":
            space = p.get("space")
            if not self.views.reaches_space_structural(actor, space, "CREATE-ROLE"):
                self.refuse(actor, name, "ROOT-NEG-3",
                            f"{actor} holds no grant carrying CREATE-ROLE over space {space} — a role is founded "
                            f"only where its founder holds authority for THAT act, not mere sight and not another "
                            f"structure-class action (R-B exact-action, R-C3; the family leash)")

    def _constitution_guard(self, actor, opname, draft):
        """The constitution is genesis-only, enforced AT THE GATE — the single point every
        GATED write passes (boot handlers, definition-born ops, observe/protection ops alike).
        Genesis and the dual-audit mirror append directly via store._append, bypassing the gate,
        so the founding and the mirror are exempt. A draft that claims a protected tier, targets
        a constitutional rule, or lowers a protected pack's genesis floor is refused and recorded
        — cannot-do-lawfully, cannot-do-quietly. The derived views recognise a law (by rule_id)
        or a pack (by kind) across EVERY action, so the protection MUST live where every write
        converges, not inside particular handlers (a handler that copies caller data into its
        payload — write_activity, the resource observer — would otherwise smuggle the shape
        past a per-handler check). The recorded constitution is read as DATA, never hardcoded."""
        # (R16 removed a `views is None` early-return here — views can no longer be None: __init__
        #  rejects it, so a guardless gate does not exist to reach this line.)
        p = draft.get("payload") if isinstance(draft, dict) else None
        # ROOT authority is the CHAIN-END, DERIVED (EP-18; never the hardcoded "owner"). Under the
        # founding it IS "owner", so every campaign-1 owner-root check below is unchanged; after a
        # lawful HANDOVER it is the successor (the new chain-end inherits the root's protections).
        ce = self.views.chain_end()
        # d) GAP REFUSAL (EP-05C, conservation; W2/finding A2 — reads the RECORD, not the invoked op).
        # A bare removal of a PROTECTED op is refused for EVERY actor, the owner included — bare removal
        # IS the protection gap ("the route to an ungoverned system is exit, not surgery"). A protected
        # op can be AMENDED (AMEND-OP, tier conserved), never bare-removed. Ordinary ops still retire (v1).
        # The guard keys on the DRAFT RECORD'S action, because removal takes effect from the record's
        # action (opdefs/views fold on action=='RETIRE-OP'), NOT from the invoked op's name: an observe-
        # adapter record whose action names the retire act removed a protected op while opname was
        # OBSERVE-RESOURCE, slipping past an opname key. Reading the draft is how every other conservation
        # branch already works (tier/demotion read p, not opname). Checked first: a RETIRE-OP-action
        # payload carries no protected shape, so the payload-shape branches below never see it.
        draft_action = draft.get("action") if isinstance(draft, dict) else None
        if draft_action == "RETIRE-OP" and isinstance(p, dict):
            target_tier = self.views.op_definitions().get(p.get("name"), {}).get("tier", "ordinary")
            if target_tier in ("owner", "constitutional"):
                self.refuse(actor, opname, "BOOT-INT",
                            f'"{p.get("name")}" is a protected operation (tier {target_tier}) — it can be amended, '
                            f"never bare-removed: removing the shield is the ungoverning move")
        if p is None:
            return
        if not isinstance(p, dict):
            # a governed record's payload must be a well-formed object; a non-dict payload (a
            # caller-passed list/scalar via a data-passthrough handler) carries no valid shape
            # and would crash the derived folds — refuse it (P4-REFUSE: fail loud + cite, never
            # crash), which also keeps a malformed payload out of the record entirely.
            self.refuse(actor, opname, AR2, "a governed record's payload must be a well-formed object")
        if not p:
            return
        # --- N2 / J7: THE AUTHORITY ANCHOR (CONST-AUTHORITY-ANCHORED, deferred -> live). Root authority
        # never orphans and never passes to a pure-agentic or unverified actor. Succession is a recorded
        # CEREMONY, never a stored owner field: designation, acceptance, revocation, and the handover are
        # each records; the CURRENT successor is a fold (views.current_successor), verified LIVE at read.
        if draft_action == "DESIGNATE-SUCCESSOR":
            if actor != ce:
                self.refuse(actor, opname, "CONST-AUTHORITY-ANCHORED",
                            "only the current root authority holder may designate a successor — succession "
                            "is the root's ceremony")
            succ = p.get("successor")
            if not self.views.verified(succ):
                self.refuse(actor, opname, "CONST-AUTHORITY-ANCHORED",
                            f"successor {succ!r} is not a verified account — root authority passes only to a "
                            "verified human (verification bottoms out at the founding, EP-15)")
            if self.views.accounts().get(succ, {}).get("actor_class") != self.views.HUMAN_ACTOR_CLASS:
                self.refuse(actor, opname, "CONST-AUTHORITY-ANCHORED",
                            f"successor {succ!r} is not actor_class human — root authority is never "
                            "transferred to a pure-agentic actor")
        elif draft_action == "REVOKE-SUCCESSION":
            if actor != ce:
                self.refuse(actor, opname, "CONST-AUTHORITY-ANCHORED",
                            "only the current root authority holder may revoke a succession designation")
        elif draft_action == "HANDOVER":
            # owner account retirement / self-removal: the root removes its own authority. Refused unless
            # a valid successor fold EXISTS — then it PROCEEDS as a recorded handover (the chain-end fold
            # moves to the successor by supersession; exit-with-continuity). The successor becomes the new
            # chain-end BY DERIVATION — no owner field is written.
            if actor != ce:
                self.refuse(actor, opname, "CONST-AUTHORITY-ANCHORED",
                            "only the current root authority holder may hand over root authority")
            if self.views.current_successor() is None:
                self.refuse(actor, opname, "CONST-AUTHORITY-ANCHORED",
                            "the root may not remove its own authority without a valid, accepted, verified "
                            "human successor — root authority never orphans (exit-with-continuity, not "
                            "surgery on the anchor)")
        # --- N3: CYCLE/ORPHAN REFUSAL at grant/role MINT (corpus §08: circular authority, authority loop).
        # A grant or role whose SPACE chain would loop, or terminate anywhere but the root, refuses at
        # creation for EVERY actor (an orphaned authority record is malformed regardless of who mints it).
        # Every FOUNDED space chains to the mother by construction (CREATE-SPACE's cycle+parent bars), so
        # the live case is a reference to an UNFOUNDED space; a genuine loop is caught the same way (the
        # mother cannot reach it). The founding openness grant bypasses the gate (genesis), so it is exempt.
        if p.get("kind") in ("grant", "role"):
            sp = p.get("space")
            if sp is not None and not self.views.space_reaches(self.views.mother_space(), sp):
                # R-C4 — SPLIT the citation. A genuine LOOP in the referenced space's chain cites
                # BOOT-INT (the space-tree cycle's own citation, mirroring the CREATE-SPACE cycle bar
                # in the space_tree check); an ORPHAN — a reference to an UNFOUNDED space, or a chain
                # that terminates anywhere but the root — keeps CAP-IS-LAW (referential integrity). A
                # FOUNDED space cannot loop (CREATE-SPACE bars cycles at creation), so the live case is
                # the orphan (unfounded space); the loop half guards a corrupted chain — a space that
                # EXISTS in the tree yet cannot be reached from the mother is one whose parents loop.
                if sp in self.views.spaces():
                    self.refuse(actor, opname, "BOOT-INT",
                                f"{p.get('kind')} names space {sp!r}, whose parent chain loops — it does not "
                                "terminate at the root (a space-tree cycle; corpus §08)")
                self.refuse(actor, opname, "CAP-IS-LAW",
                            f"{p.get('kind')} names space {sp!r}, which is not a founded space reaching the root "
                            "(orphan) — authority never orphans (corpus §08)")
        # a)/e) TIER CLAIMS. Constitutional is genesis-only, ALWAYS (ruling 1). An owner-tier claim
        # is admitted ONLY as a legitimate in-place supersession (EP-05C branch e): a live op of the
        # same name whose active tier is exactly "owner", superseded by the actor "owner". Elevation
        # (active not owner), no-target (nothing live to conserve), and wrong-actor all refuse — so
        # AMEND-OP conserves tier while minting/elevation/forging stays refused.
        claimed = p.get("tier")
        if claimed == "constitutional":
            self.refuse(actor, opname, "BOOT-INT",
                        "a decision may not claim tier 'constitutional' — constitutional law is genesis-only")
        elif claimed == "owner":
            active = self.views.op_definitions().get(p.get("name")) if p.get("name") else None
            if not (active and active.get("tier") == "owner" and actor == ce):
                self.refuse(actor, opname, "BOOT-INT",
                            "tier 'owner' may be claimed only as the root's in-place supersession of a live "
                            "owner-tier op — not elevation, minting, or another actor (the root is the "
                            "chain-end, so a successor inherits this after a handover)")
        # f) DEMOTION REFUSAL. Superseding a live PROTECTED op must carry that SAME tier; a lower or
        # absent tier is a gap that never closes (the mirror of tier-laundering — (b) stops a rule's
        # tier being stripped, (f) stops an op's being dropped through supersession).
        if p.get("kind") == "op_definition":
            active = self.views.op_definitions().get(p.get("name")) if p.get("name") else None
            if active and active.get("tier") in ("owner", "constitutional") and claimed != active.get("tier"):
                self.refuse(actor, opname, "BOOT-INT",
                            f'superseding "{p.get("name")}" (tier {active.get("tier")}) with a lower or absent tier '
                            f"is a protection gap — tier is conserved across amendment")
        # (e/f)-VIEW) CONSERVATION FOR MASTER VIEWS (EP-08B B2 — kind-aware, mirroring the op branches
        # against the view_definitions fold). A protected (owner-tier) master view is amended IN PLACE by
        # the OWNER only; it stays live throughout (view amendment is latest-wins — no down moment). A
        # non-owner superseding it, or a write CLAIMING a lower/different tier, refuses BOOT-INT (recorded).
        # Unlike ops, create_view mints NO tier, so an ABSENT claim over a protected view is precisely the
        # owner's tier-conserving amendment — the view_definitions fold carries the protected tier across
        # (defense in depth). Ordinary views are untouched (v1). Kept a SEPARATE branch, not merged into
        # the op branch: for an op an absent tier is a demotion; for a view it is the normal conserved case.
        if p.get("kind") == "view_definition":
            active_tier = self.views.view_definitions().get(p.get("name"), {}).get("tier", "ordinary")
            if active_tier in ("owner", "constitutional") and (actor != ce or (claimed is not None and claimed != active_tier)):
                self.refuse(actor, opname, "BOOT-INT",
                            f'"{p.get("name")}" is a protected master view (tier {active_tier}) — only the root (the '
                            "chain-end) may amend it in place, tier conserved (no supersession, demotion, or elevation by others)")
        # b) a constitutional rule_id is unamendable through the system
        rid = p.get("rule_id")
        if rid is not None and self.views.active_rules().get(rid, {}).get("tier") == "constitutional":
            self.refuse(actor, opname, "BOOT-INT",
                        f'"{rid}" is a constitutional record — it refuses amendment through the system')
        # c) a protected pack's genesis floor never lowers (CONST-RECORDING-TOTAL, carried as data)
        if p.get("kind") == "category_pack":
            recording = self.views.active_rules().get("CONST-RECORDING-TOTAL") or {}
            name = p.get("name")
            if name in (recording.get("protected_packs") or []):
                floor = set()
                for e in self.store.all():
                    ep = e.get("payload") or {}
                    if ep.get("kind") == "category_pack" and ep.get("name") == name:
                        floor = set(ep.get("levels") or [])  # the earliest instance IS the floor
                        break
                dropped = floor - set(p.get("levels") or [])
                if dropped:
                    self.refuse(actor, opname, "CONST-RECORDING-TOTAL",
                                f"would drop protected audit-floor action(s) {sorted(dropped)} — the floor never lowers")
        # g) THE UNTOUCHABLES FLOOR — the REAL scope+target test (EP-17; design/30 §3, design/31 J5).
        # A minted full-form DON'T refuses for EVERY actor (the owner included) ONLY when BOTH prongs
        # hold:
        #   TARGET — it blanket-blocks the rule-processing surface: a law-lifecycle act (or a matches-
        #     everything trigger) with NO concrete actor/object narrowing (`_is_blanket_rule_block`, the
        #     blanket-vs-targeted discriminator — a don't naming a specific actor only bricks that actor,
        #     the surface survives; the law-lifecycle act names are DATA, a floor-pinned category_pack).
        #   SCOPE — it binds the SYSTEM LEVEL: the law's scope is the MOTHER space (the whole tree), so it
        #     reaches the system's capacity to work with rules AT SYSTEM LEVEL. This is the J5 half.
        # This RETIRES the interim heuristic's OVER-REFUSAL: a blanket rule-writing ban scoped to a
        # SUBSPACE is a space-holder's local governance and now PASSES the floor (design/30 §3: "a
        # space-holder's local rule-writing ban passes") — its author's reach over that subspace is
        # checked by the gate authority step (W1), not here. Proven STRICTLY-STRONGER-OR-EQUAL to the
        # heuristic on the whole campaign-1 untouchables/brick ledger BEFORE the swap (every ledger case
        # is system-scoped, so the new test refuses each exactly as the heuristic did) — the ledger proof
        # is the license, never a naked swap (tests/test_ep17.py TestUntouchablesStrictlyStronger; the
        # brick class — a don't matching CREATE-RULE refuses all rule-making, the owner minting it is
        # self-bricking, exit not surgery — still refuses for everyone at system scope).
        if p.get("polarity") == "-" and isinstance(p.get("when"), (list, tuple)) and p.get("when"):
            # EP-17 Y-PASS, Y1 — THE SCOPE+TARGET FLOOR, now SAFE because enforcement is scoped. A
            # blanket don't over the rule-processing surface bricks the system's capacity to work with
            # rules ONLY when it binds the SYSTEM LEVEL (the mother space, the whole tree) — refused for
            # every actor, the owner included (self-bricking is exit, not surgery). A blanket ban scoped
            # to a SUBSPACE is a space-holder's LOCAL governance and passes (design/30 §3): it MINTS, and
            # `_full_form_pass` now fires it ONLY within its own subtree (Y1) — so it can no longer brick
            # the mother's rule-processing surface (the hole Y0 first closed by refusing the mint; Y1
            # re-opens the lawful allowance because enforcement, not the mint, now carries containment).
            # The TARGET prong (blanket vs targeted) is `_is_blanket_rule_block`; the SCOPE prong
            # (system vs space-local) is `_act_space == mother_space`.
            if self._is_blanket_rule_block(p["when"]) and self._act_space(draft, p) == self.views.mother_space():
                self.refuse(actor, opname, "BOOT-INT",
                            "a blanket don't over the system's rule-processing surface, bound at system level (the "
                            "mother space), bricks the system's capacity to work with rules — refused for every actor "
                            "(the untouchables floor, design/30 §3). A targeted rule naming a specific actor/object, or "
                            "a blanket ban scoped to a subspace (space-local governance, enforced only in its subtree), "
                            "passes.")

    # The SCOPE dimensions (W1/finding A1): the record fields that carry space-local narrowing —
    # WHO acts (actor) and WHAT is acted on (object). The definitive of "space-local governance"
    # (design/30 §3: "naming a specific actor/object") is a concrete constraint on one of these.
    # The other trigger dimensions (rule_cited / refused / payload_kind) are DETERMINED by the act
    # itself — every CREATE-RULE carries rule_cited=ROOT-NEG-6, records no payload_kind, and is not
    # refused — so pinning one narrows nothing; nor does an unknown field (it reads absent on every
    # record). Reading scope is what closes the disguises the old shape-check ("any extra field ->
    # targeted") admitted.
    _SCOPE_DIMS = ("actor", "object")

    def _is_blanket_rule_block(self, when):
        """The TARGET prong of the untouchables floor (design/30 §3-§4; EP-17). A minted don't's `when`
        blanket-blocks the rule-processing surface iff it names a law-lifecycle act (or matches everything)
        and does NOT genuinely narrow to a concrete WHO (actor) or WHERE (object) — i.e. it would block
        rule-writing for EVERYONE, not one actor. An always-true field (rule_cited pinned to the value
        every CREATE-RULE carries), an always-absent field (a None-valued or unknown field that reads
        absent on every record), or any non-narrowing dimension narrows nothing and stays blanket; only a
        positive constraint on actor/object makes it targeted (it bricks that actor only, the surface
        survives) and passes. The law-lifecycle act names are DATA (a floor-pinned pack), never a hardcoded
        verb list. Since EP-17 this is the TARGET half of the real scope+target test: branch g refuses only
        when this holds AND the law binds the system level (the mother space, `_act_space == mother_space`,
        the SCOPE prong). So blanket-vs-targeted lives here; system-vs-space-local is the scope prong at
        branch g, which cures the pre-spaces over-refusal — a blanket ban scoped to a subspace now passes
        as space-local governance.
        HONEST CAP (design/30 §5): a NEGATED narrowing (e.g. actor != alice) is broad, not targeted, so it
        reads as non-narrowing here and stays blanket — errs closed."""
        lifecycle = set((self.views.category_packs().get("law-lifecycle-actions") or {}).get("levels") or [])
        actions, matches_everything, scope_narrowed = set(), False, False
        for pattern in when:
            negated = bool(pattern.get("not"))
            dims = {k for k in pattern if k != "not"}
            if not dims:
                matches_everything = True                 # a dimensionless pattern matches every act
            if "action" in pattern and not negated:
                actions.add(pattern.get("action"))
            # a POSITIVE, CONCRETE constraint on WHO/WHERE is space-local governance (design/30 §3)
            if not negated and any(pattern.get(d) is not None for d in self._SCOPE_DIMS):
                scope_narrowed = True
        if scope_narrowed:
            return False                                  # names a specific actor/object -> targeted -> passes
        if matches_everything:
            return True                                   # action-blind, matches everything -> blanket
        return bool(actions) and actions <= lifecycle     # blanket over law-lifecycle act(s), no scope -> brick

    def _authority_step(self, actor, name, result):
        """THE AUTHORITY STEP (design/31 J3, J4; design/30 §1-2; EP-17 — THE CRUX), lifted out of
        `execute` UNCHANGED by EP-26 so that the counterfactual reach test can run THE GATE'S OWN
        TEST rather than a second implementation of it (design/36 §4b.2: "the one interpreter is
        the matcher"). The body below is byte-for-byte the step that ran inline; what moved is
        only where it lives, and the whole existing suite is the proof that nothing else did.

        covers-or-refuse: the INVOKER (who typed the act — the authority, split from the record's
        acting-as `actor`, A2) must hold an ACTIVE GRANT CHAIN whose four dimensions cover this
        act — action x info-kind x space, evaluated LIVE over the grant fold (never a stored
        capability set — that is RBAC, the refused reference). The negative space is the COMPUTED
        complement of the grant set (design/30 §1: no stored deny). The founding openness grant
        (grantee/actions/info = *, space = mother) covers EVERYONE on day one, so behaviour is
        IDENTICAL until the owner narrows it — the flip moves WHERE openness lives (an unstated
        default -> a visible recorded grant), not what works (design/31 transition policy; NO
        dual-mode gate, NO compat flag). ROOT-NEG-1 (no authorising chain at all -> no act) and
        ROOT-NEG-3 (a chain reaches the account but does not authorise THIS operation -> no write).
        This step sits BEFORE the constitution guard (design/31 §3 hop order: chain -> scope ->
        tier/conservation/protected-core); under openness it always passes, so no campaign-1
        citation moves. EXEMPT: the ROOT (owner/SYSTEM) — a wide-power holder passes the grant
        check, capped only by the untouchables floor (design/30 §3).
        Y2 (regime as DATA): WHICH regime governs this op is read from its OWN definition record
        (`authority_regime`), not a code constant. "attenuation-family" ops (grant/revoke/space/
        role) WRITE the power structure and are governed by ATTENUATION (the leash, Y3), not
        a covering grant; every other op defaults to "covers" — covers-or-refuse over the grant fold.

        AND THIS IS WHERE THE TWO TIMES DO NOT REACH (design/36 K7; design/34 §2 generalized).
        AUTHORITY IS ALWAYS EVALUATED LIVE AT EFFECT TIME. A chain revoked between an act's
        deciding moment and its arrival refuses at the door however impeccable the deciding time
        was: that refusal carries AUTHORITY information, not staleness information, and the two
        are never merged. Only the LAW half is evaluated as of the deciding time. Implementing
        the split uniformly in either direction is the quiet third form of the arrival-order
        error — everything-as-of-d would let a revoked chain act on stale power.

        AND THIS IS WHERE A RELEASE DOES NOT GO (design/10 §11.1c, built EP-28B W1). An op whose
        WHOLE effect is to end something the caller already lawfully holds declares that fact —
        `act_kind: "release"` on its own definition record — and the authority fold is skipped
        for it. Not as a speed measure: the guest measured the fold at 0.41–1.07% of an
        open+close pair, so this row would not be worth writing if it were only cheaper. It is a
        CORRECTNESS row. Refusing a release is incoherent — no actor can be denied permission to
        stop holding what it lawfully holds — and it is also an ABI divergence, because POSIX
        `close()` on a valid descriptor cannot fail with a permission error, so a revoked chain
        reaching a close would refuse where the ports contract forbids refusal. The fold both
        costs what it should not and manufactures a wrong answer in the one case where it would
        ever change the answer.

        WHICH KIND OF ACT AN OP IS, LIKE WHICH REGIME GOVERNS IT, IS READ FROM THE OP'S OWN
        DEFINITION — one more line beside the `authority_regime` read below, never a verb list in
        code. The declaration is a statement about the op ("its whole effect is a release"), true
        whether or not this branch exists; the exemption is derived from that statement by
        §11.1c. The vocabulary is closed and validated at all three definition doors
        (`opdefs.ACT_KINDS`), and the exemption sits INSIDE the covers branch on purpose: it
        removes the covering-grant fold and NOTHING else, so an op that declared itself a release
        while minting a grant would still meet the attenuation leash. That combination is refused
        at definition time as well — the guard and the placement are one answer arriving at both
        ends."""
        act = result.get("action")
        # WHICH regime governs this op is read from its OWN definition; the DEFAULT ("covers") is now
        # PACK DATA too (R-A pack line: `authority-regime-default` policy — the default stops living
        # only in code), with the literal only a last-ditch fallback for a foundingless store.
        op_def = ((self.views.op_definitions().get(name) or {}).get("definition") or {})
        op_regime = op_def.get("authority_regime")
        regime = op_regime or self.views.policy_value("authority-regime-default") or "covers"
        # WHAT KIND OF ACT this op is, read from the same definition record. NO DEFAULT AND NO
        # POLICY LINE: silence means the op has not stated that its whole effect is a release, so
        # the fold runs. That is the closed direction — an op that IS a release in fact and does
        # not say so keeps paying the fold and keeps the ABI divergence, which is visible and
        # wrong rather than invisible and wrong. `T-RELEASE-RECORDS-NEVER-REFUSES`'s divergence
        # row drives exactly that case, so the silent-default behaviour is measured and not
        # assumed.
        act_kind = op_def.get("act_kind")
        pdict = result.get("payload") if isinstance(result.get("payload"), dict) else None
        # ROOT is the chain-end, DERIVED (EP-18) — never the hardcoded "owner" string. Under the
        # founding this IS "owner", so no campaign-1 answer moves; after a lawful HANDOVER it is the
        # successor, so the new chain-end governs and the old owner falls back to grant-based power.
        ce = self.views.chain_end()
        if actor not in (ce, "SYSTEM"):
            # attenuation-family ops AND any op minting a grant-kind record (R-A passthrough) are
            # leashed by ATTENUATION, not a covering grant (a grant is made by attenuation).
            if regime == "attenuation-family" or (pdict or {}).get("kind") == "grant":
                self._attenuation_family_leash(actor, name, result)   # Y3/R-A/R-B — attenuation, not covers
            elif act_kind == opdefs.RELEASE:
                return                                                # §11.1c — a release records and is never folded
            else:
                info_kind = self._info_kind(pdict)
                act_space = self._act_space(result, pdict)
                if not self.views.covers(actor, act, info_kind, act_space):
                    # no covering chain at all -> ROOT-NEG-1 (no chain); a chain reaches the account
                    # but does not cover THIS act -> ROOT-NEG-3 (not authorised for this operation).
                    cite = "ROOT-NEG-3" if self.views.power_view(actor)["grants"] else "ROOT-NEG-1"
                    self.refuse(actor, name, cite,
                                f"{actor} holds no active grant covering {act} on info '{info_kind}' in "
                                f"{act_space} — the negative space is the computed complement of the grant "
                                f"set (default deny; power is the positive grant)", draft=result)

    def _full_form_pass(self, actor, opname, draft, rules=None):
        """The EXECUTABLE half of full form (design 28 §I6): a recorded law whose trigger matches
        this draft fires its outcome, read from the record — no rule is hardcoded. v1 executes the
        DON'T direction (a matching don't refuses before the write commits). A law's `when` is a
        LIST of six-dimension patterns; an EMPTY `when` means the law's teeth live in machinery
        (checks / gate-machinery / deferred, per enforced_by), so this pass is INERT for all 18 root
        laws — behavior identical. A structural don't added with a real `when` refuses with no new
        code (the point of full form). View definitions carry a DICT `when` and are skipped by the
        list guard. PRECEDENCE was RULED (R13, owner, 2026-07-17): execution order, written down —
        see execute's pipeline docstring; this pass is step 4 of that order, fires only
        pass-triggered (non-empty-when) laws, and leaves the 18's machinery citations untouched.
        DO auto-firing (must-happen) is the obligation executor (EP-07), not duplicated here.

        THE ACCEPTANCE STEP IS THIS PASS WITH ITS FOLD POINTED AT THE DECIDING TIME (EP-26 W1).
        `rules` defaults to the live fold, which is what every synchronous act gets and is why
        the degenerate case d = r is byte-identical. An arrival carrying a distinct deciding time
        is passed the law in force AS OF THAT MOMENT instead (`reconcile.acceptance_law`). One
        pass, one fold, one filter — there is no second evaluation path that could disagree with
        this one, which is the point: a rule and its enforcement that can drift apart is two
        rules."""
        pdict = draft.get("payload") if isinstance(draft.get("payload"), dict) else None
        act_space = self._act_space(draft, pdict)        # WHERE this act binds (scope -> space -> mother)
        for rule in (self.views.active_rules() if rules is None else rules).values():
            when = rule.get("when")
            # a law's `when` is a LIST (a tuple after deep-freeze on append); a view-definition's
            # `when` is a MAPPING and is excluded here. Empty = machinery-enforced (the 18) -> skip.
            if not isinstance(when, (list, tuple)) or not when:
                continue
            if rule.get("polarity") != "-":              # v1 executes don'ts; dos -> EP-07
                continue
            if not _draft_matches(draft, when):
                continue
            # Y1 (EP-17 Y-pass) — SCOPE-AWARE ENFORCEMENT (design/31 J2 containment, J5). A law fires
            # ONLY on acts within its DECLARED SCOPE's subtree. A law scoped to the mother (space:root)
            # — every one of the 18 root laws, and any system-level don't — reaches every act (the
            # mother reaches the whole tree), so their firing is UNCHANGED. A subspace-scoped local ban
            # reaches ONLY its own subtree: it binds acts inside it and NEVER a parent/sibling act, so it
            # can neither brick the mother's rule-processing surface (a mother-scope CREATE-RULE is
            # outside its reach) nor orphan itself (a superseding rule from the parent's reach is a
            # parent-scope act it does not fire on — always liftable from above). The law's binding space
            # is resolved exactly as `_act_space` resolves an act's: `scope`, else `space`, else mother.
            law_scope = rule.get("scope")
            if law_scope is None:
                law_scope = rule.get("space")
            if law_scope is None:
                law_scope = self.views.mother_space()
            if not self.views.space_reaches(law_scope, act_space):
                continue                                 # the act is outside this law's reach — inert here
            for step in rule.get("then") or []:
                cite = step.get("refuse")
                if cite and not step.get("refrain"):
                    self.refuse(actor, opname, cite,
                                f'{opname} matches the recorded trigger of {rule.get("rule_id")} — refused by law',
                                draft=draft)

    def full_form_outcomes(self, draft):
        """The READ side of full form: resolve (WITHOUT firing) the outcome steps of every recorded
        law whose trigger matches a draft. Proves a law's outcome is executable-shaped — used to show
        a DO's outcome resolves to its op invocation, whose actual auto-execution is EP-07's
        obligation executor. Mechanism only; the laws it reads are data."""
        out = []
        for rule in self.views.active_rules().values():
            when = rule.get("when")
            if isinstance(when, (list, tuple)) and when and _draft_matches(draft, when):
                out.append({"rule_id": rule.get("rule_id"), "polarity": rule.get("polarity"),
                            "then": rule.get("then") or []})
        return out

    def register(self, name, meta, handler):
        if name in self.ops:
            raise ValueError(f"duplicate operation: {name}")
        self.ops[name] = {"meta": meta, "handler": handler}

    def has(self, name):
        return name in self.ops

    def unregister(self, name):
        """Remove a definition-born op (RETIRE-OP machinery only). A retired op reverts
        to not-existing: invoking it is a Closure Hit, exactly as before it was defined."""
        self.ops.pop(name, None)

    def list(self):
        # enumeration IS the completeness guarantee ("the bank has no counter", P3)
        return {
            n: {
                "description": e["meta"].get("description"),
                "rules": e["meta"].get("rules", []),
                "params": e["meta"].get("params", {}),
            }
            for n, e in self.ops.items()
        }

    def refuse(self, actor, op, rule, message, draft=None):
        """A refusal is itself a recorded event, then raised (guards.refuse idiom).
        Attribution + Explanation hold for denials exactly as for grants.

        THE DRAFT RIDES ALONG WHERE ONE EXISTS (EP-26 W5). A refusal that records only its op
        name and message cannot be re-asked: §4b.4 rules that a late-arriving permissive law
        never fabricates an effect and instead surfaces the case for re-submission, and a case
        nobody can re-evaluate is surfaced but not computed. Every refusal raised at the gate's
        OWN steps carries the draft it refused, so the re-ask view answers by recomputation
        rather than by assertion. Refusals raised before a draft exists (a Closure Hit, a
        nonconforming call, a handler check) carry none, and the re-ask view says so rather
        than guessing — the honest half of a view is knowing which half it computed. Parameters
        are deliberately NOT recorded: a secret candidate never lands on the record
        (CONST-SECRETS), so the draft is the widest honest thing a refusal can carry."""
        payload = {"op": op, "message": message}
        if draft is not None:
            payload["draft"] = draft
        self.store._append(
            {
                "actor": "SYSTEM",
                "action": "op-refused",
                "target": actor,
                "rule_cited": rule,
                "payload": payload,
                "refused": True,
            }
        )
        raise OpError(rule, message)

    def execute(self, name, actor, params=None):
        """THE DECIDE REGION'S SPAN (EP-28G W1), wrapped around the act it protects.

        Everything from the fold read in the handler to the append is INSIDE; the durability
        wait is OUTSIDE, taken here once the region has been released. Both exits go through
        it: a refusal is a full record and its caller waits for the covering sync exactly as a
        permit's does (ADDENDUM 1's second boundary condition — the reply is what waits, never
        the decide path's own reading).

        THE WAIT IS TAKEN ONLY BY THE OUTERMOST ENTRY. A sweep re-enters `execute` and the
        dual-audit mirror appends from inside a listener; every record any of them published
        sits later in the same file than the act's own, so ONE barrier at the outermost exit
        covers the whole act. That is the prefix-durability law being used rather than
        restated, and it is what the store did before this split — a nested submission rode
        the outer batch's sync.

        IF THE BARRIER FAILS the wait raises, and it raises THROUGH a refusal that was already
        travelling. That is deliberate: a refusal whose record is not durable is a reply about
        an act that may never have happened, and reporting the refusal instead would be the
        async-ack trap arriving through the error path."""
        outermost = self.region.enter()
        try:
            return self._decide(name, actor, params)
        finally:
            self.region.exit()
            if outermost:
                self.store._await_durable()

    def _decide(self, name, actor, params=None):
        """Run a registered op. The gate is the SOLE appender (design 28 §I2): a handler
        RETURNS the record it intends (a plain draft dict, not yet written), and the gate
        performs the one write. Refusals still record + raise (via refuse, below).

        REFUSAL PRECEDENCE (R13, owner-ruled 2026-07-17 — EXECUTION ORDER, written down as the rule).
        When an act violates several laws at once, the CITED rule is whichever refusal source fires
        FIRST in this pipeline; the gate refuses on the first and raises (no exhaustive evaluation of
        a doomed act):
            1. registry membership        -> P3-CLOSURE   (Closure Hit)
            2. required params             -> AR-2         (nonconforming call)
            3. the handler's own checks    -> the check's cite (require_prior / sight / ceiling /
               (run inside the handler)        consistency -> ROOT-NEG-6, fingerprint -> the
                                               staleness rule, ...)
            4. the authority step          -> ROOT-NEG-1 / ROOT-NEG-3 (covers-or-refuse, or the
                                               attenuation-family leash)
            5. the crossing chokepoint     -> CROSSING-CORRELATION / CROSSING-STALE (a crossing
                                               record's citation must bind an OPEN hand-out)
            6. the full-form pass          -> a recorded structural don't's cited rule (INERT for
                                               the 18 — they carry an empty `when`)
            7. the constitution guard      -> BOOT-INT / CONST-RECORDING-TOTAL (constitutional +
                                               conservation backstop)
        [Steps 4 and 5 were added by EP-17 and EP-23; the list had gone stale at step 4, which
        is why it is restated in full here rather than appended to. Step 4 precedes step 5 by
        derivation, not by accident: a mid-crossing revocation must refuse on AUTHORITY, and
        staleness must never be claimed in its place (design/34 §2).]
        The owner ruled to KEEP this order rather than reorder by tier, accepting the trade-off: the
        citation is determined by wiring, so it can drift if the pipeline is re-sequenced. That drift
        is made VISIBLE, not silent, by the pinned regression (tests/test_full_form.py,
        TestRefusalPrecedence): e.g. a doubly-invalid CREATE-RULE (constitutional target + exclusive
        contradiction) cites ROOT-NEG-6 because the consistency check (3) precedes the guard (5). A
        change to this order that alters a cited rule breaks that test — the rule is written down."""
        # WATCHER BRAKE (EP-09; design 28 §7 — P7's vertical arm). A WATCHED actor may freeze its
        # WATCHER's ops (HALT-WATCHER) pending owner resolution. A halted watcher's EVERY op refuses
        # here (WATCHER-BRAKE, recorded) until the OWNER resolves. The brake halts the WATCHER only —
        # never the recording: this refusal is recorded and the dual-audit mirror keeps mirroring, so
        # the record never goes dark. SYSTEM and owner can never be halted (halted_watchers excludes
        # them), keeping the recorder and the resolver live.
        if actor in self.views.halted_watchers():
            self.refuse(actor, name, "WATCHER-BRAKE",
                        f"{actor}'s ops are frozen — a watched actor braked this watcher, pending owner resolution")
        entry = self.ops.get(name)
        if entry is None:
            # Closure Hit: unregistered = does not exist. Recorded, then raised.
            self.refuse(
                actor,
                name,
                P3_CLOSURE,
                f'operation "{name}" is not registered in this deployment — it does not exist',
            )
        params = params or {}
        spec = entry["meta"].get("params", {})
        for p, req in spec.items():
            if req == "required" and params.get(p) in (None, ""):
                # A malformed call is a nonconforming-call refusal (AR-2), NOT a refusal
                # under the op's own domain rule. The domain rule governs whether the ACT
                # is permitted; that is a different question from whether the CALL is
                # well-formed. Citing rules[0] here made the audit answer to "why refused?"
                # name a domain law (e.g. FS-LAW-PERM) that never fired.
                # refuse BEFORE the handler runs — the handler is never entered.
                self.refuse(actor, name, AR2, f'nonconforming call: parameter "{p}" required for {name}')
        # R28 (EP-10): the brake's AUTHORITY refuses AT THE GATE — never accepted-and-inert (the R18
        # doctrine: an act the system will not honour REFUSES, cited + recorded; it does not
        # record-and-shrug). A4-style actor checks, no new check vocabulary; the fold's exemptions
        # (halted_watchers) stay as defense in depth. Braking SYSTEM (the recorder) or owner (the root
        # resolver) destroys a boot condition — SYSTEM/owner unbrakability is now REFUSED-AND-CITED law,
        # not a silent fold-exemption; and only the owner may resolve a brake.
        # The unbrakable set and the brake resolver are the ROOT AUTHORITY axis, so they read the
        # CHAIN-END, DERIVED (EP-18/R-C1) — never the hardcoded "owner". Under the founding the
        # chain-end IS "owner", so behaviour is unchanged; after a lawful HANDOVER the successor is
        # the unbrakable resolver and the departed owner is an ordinary account (a literal "owner"
        # here would split root authority — the recorder/resolver would stay with the departed root).
        # SYSTEM stays a literal: it is the recorder, a founding constant not subject to handover.
        brake_root = self.views.chain_end()
        if name == "HALT-WATCHER" and params.get("watcher") in ("SYSTEM", brake_root):
            self.refuse(actor, name, "BOOT-INT",
                        "SYSTEM and the root authority holder can never be braked — braking the recorder or "
                        "the resolver destroys a boot condition (the record never goes dark)")
        if name == "RESOLVE-WATCHER" and actor != brake_root:
            self.refuse(actor, name, "BOOT-INT", "only the root authority holder may resolve a watcher brake — resolution is the root's")
        result = entry["handler"](actor, params)
        # The one write. A DRAFT (a plain dict not yet appended, so carrying no minted
        # `seq`) is appended here — the gate is the only path to the record. An already
        # appended record (a MappingProxyType, which is not a dict, carrying `seq`) is
        # passed through unchanged: the safety net that preserves exactly-one-record if a
        # handler ever writes for itself. H3 (rule_cited enforcement) fires inside _append,
        # so it stays on the gate's write path, not outside it.
        if isinstance(result, dict) and "seq" not in result:
            # obligation_ref (EP-07): the obligation executor (run_due) fires an op with this in
            # params; the gate stamps it into the fired record's PAYLOAD so "has this obligation
            # fired" is DERIVED from the record (no status). Universal — works whether the then-op is
            # a boot handler or a definition-born op (both converge here). Inert otherwise. (Payload,
            # not a top-level field: store._append preserves payload and drops unknown envelope keys.)
            # B3 (R23) + R25 (review fix): three payload cases, three behaviors. ABSENT payload —
            # CREATE it carrying the ref (a payloadless outcome op like CREATE-INFO must still record
            # its fired-evidence, else the obligation re-fires forever — the R25 regression). DICT
            # payload — stamp into it. Malformed non-dict (a data-passthrough handler handed a
            # list/scalar) — leave untouched; it falls through to the guard's AR-2 refusal (coercing
            # it crashed uncaught, the R23 regression). No silent evidence loss, no crash.
            if params.get("obligation_ref"):
                pl = result.get("payload")
                if pl is None:
                    result["payload"] = {"obligation_ref": params["obligation_ref"]}
                elif isinstance(pl, dict):
                    pl["obligation_ref"] = params["obligation_ref"]
            # ---- W1: THE AUTHORITY STEP — LIVE AT EFFECT TIME, ALWAYS (EP-17; EP-26 K7) ----
            # The body moved to `_authority_step` at EP-26 so the sweep's counterfactual reach test
            # runs THE GATE'S OWN TEST rather than a copy of it. Nothing about the step changed.
            self._authority_step(actor, name, result)
            # ---- THE CROSSING CHOKEPOINT (EP-23; design/36 K8, wall primitive 6) ----
            # Correlation integrity for any op minting a crossing-family record: the cited hand-out
            # must exist and be OPEN, and an answer must carry a fingerprint verdict. Here, not in a
            # handler, for the reason EP-18 R-A established — a leash inside one op's handler is
            # reached past by any other op that mints the same record shape. Placed AFTER the
            # authority step on purpose: a revoked chain must refuse on AUTHORITY, never come back
            # labelled stale (design/34 §2 — two verdicts, never merged, and the order is what keeps
            # them apart when both would fire).
            from . import crossing as _crossing
            from . import reconcile as _reconcile
            _crossing.correlation_guard(self, self.store, actor, name, result)
            # ---- THE OVERTURN LEASH, WIRED AT BIRTH (EP-26 W4; design/36 §4b.7 as corrected by
            # ADDENDUM E.1). At the chokepoint, not in OVERTURN's handler, for the EP-18 R-A reason:
            # a leash inside one op's handler is reached past by any other op minting the same
            # record shape. The guard's trigger reads NO act kind — it asks the anchor law's own
            # effect-level question of the sweep's post-state.
            _reconcile.overturn_guard(self, self.store, actor, name, result)
            # ---- THE ACCEPTANCE STEP (EP-26 W1; design/35, design/36 K7) ----
            # The law this act is judged by is the law in force AS OF ITS DECIDING MOMENT. For a
            # synchronous act d = r by construction and this IS the live fold, so the existing
            # world does not move a byte. For an arrival that decided elsewhere and travelled — an
            # observation, a crossing's answer, a human hand-in — the fold is pointed at d, and the
            # act is judged by the law it could actually have been shown.
            _reconcile.seal_bound_check(self, self.store, self.views, actor, name, result)
            self._full_form_pass(actor, name, result,       # recorded structural don'ts refuse (INERT for the 18)
                                 rules=_reconcile.acceptance_law(self.views, result))
            self._constitution_guard(actor, name, result)  # refuses+records a write that touches the constitution
            # A2 (design/31 J1 + §9 pass-two #4): ATTRIBUTION SPLITS FROM ACTING AUTHORITY. The
            # record's `actor` field stays who-it-acted-AS — a handler may lawfully set SYSTEM
            # (WRITE-ACTIVITY, the audit mirror, run_due). WHO INVOKED is resolved FRESH from the
            # record here and written to provenance.asserted_by: a founded identity (an account or a
            # founding anchor) resolves to itself, a bare legacy name to `unverified:<name>` — and
            # STILL ACTS (this EP builds RESOLUTION, not refusal; the no-account->no-act flip is
            # EP-17's, under the openness grant). Set ONLY where the handler left provenance to
            # default; a handler that ASSERTS its own provenance (an observe adapter recording
            # through a /proc window) states a deliberate different fact and is preserved untouched.
            if "provenance" not in result:
                result["provenance"] = {"asserted_by": self.views.resolve_asserted_by(actor),
                                        "source": "system", "could_read": []}
            # THE ONE WRITE, AND IT IS THE PUBLISH HALF ONLY (EP-28G W1). `_publish` mints,
            # writes, flushes and makes the record visible to every fold; it returns BEFORE
            # the record is durable. The durability wait is `execute`'s, taken once the
            # region is released — which is the whole seam this EP exists to create. A
            # refusal reaches the record through `refuse`, which still calls `_append`,
            # because `refuse` is also reached from paths that hold no region (boot, the
            # observe seam) and there the pre-split contract is the correct one; inside the
            # region `_append`'s own wait defers to this act's, in one place, by the rule
            # stated at `store._await_durable`.
            appended = self.store._publish(result)
            self._maybe_sweep(appended)
            return appended
        return result

    def _maybe_sweep(self, record):
        """LATE-ARRIVING LAW RECONCILES BY THE SWEEP (EP-26 W3; design/35 §2, design/36 §4b).

        A law-family record whose deciding time precedes its recording time was in force from a
        moment the store had not yet seen, so acts recorded in between were judged without it.
        The store does not rewrite one byte of them: it computes which of them the law reaches
        and appends OVERTURN decisions acting forward. Both the act and its overturn stay on the
        record permanently, and an asOf answer from before the overturn still shows the act's
        effect — order is untouched; validity is what changed.

        A sweep triggers only where the OVERTURN op is registered, which is the composition
        boundary and not a fallback: a store with no founding has no law machinery for a sweep to
        act through, and the skip is recorded in the observable ledger with its reason rather
        than passing silently (ST-A)."""
        from . import reconcile as _reconcile
        if not _reconcile.is_law_family(record):
            return
        d, r = _reconcile.deciding_time(record), _reconcile.recording_time(record)
        if d is None or r is None or not (d < r):
            return                                       # d = r: nothing arrived late, nothing to reconcile
        if not self.has("OVERTURN"):
            self.sweeps.append({"law_seq": record["seq"], "skipped": "OVERTURN is not registered "
                                "on this gate — no founding, so no law machinery to sweep through"})
            return
        self._sweep_active += 1
        try:
            outcome = _reconcile.run(self, self.store, self.views, record)
            self.sweeps.append(outcome)
        finally:
            self._sweep_active -= 1
        if self._sweep_active == 0:
            self._drain_law_queue()

    def _drain_law_queue(self):
        """The held arrivals, accepted in submission order now the record has settled."""
        while self._law_queue:
            d = self._law_queue.pop(0)
            d.record = self.execute(d.op, d.actor, d.params)
