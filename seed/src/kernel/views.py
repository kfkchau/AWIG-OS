"""gov-os kernel — views (L2): all current state computed by replay.

Ported from pwc-app/src/domain/views.js. Every "current X" is a fold over the record
(design 02 §1.3; P2 "everything current is computed"). Nothing here persists state.

Head-only memo keyed on an append generation: caching the head is safe because the
log is append-only, so a view computed at log-length N is stable. Delete the memo and
replay yields identical results (round-trip law). asOf queries are never cached.
"""

import hashlib
import json
from collections.abc import Mapping

from . import authority
from .store import PROJECTIONS, frozen_default

# Closed trigger vocabulary for view definitions (design/27 §4; adopted-definitives, B09):
# the dimensions a view's "when" may test. A dimension outside this set is refused at
# creation — an unknown filter does not exist (the closure discipline on view triggers).
VIEW_FILTER_DIMENSIONS = ("action", "actor", "object", "rule_cited", "refused", "payload_kind")

# The S-plane FOLD LIBRARY (design 28 §6, §I4; EP-08): the named engine folds a MASTER view
# definition may BIND to. A master is a RECORD that names a fold; the fold FUNCTIONS stay code
# (mechanism, zero governance value — the S-plane). This closes the loop of §I4: masters are
# derived AND defined-as-records. A definition naming a fold outside this set is refused at
# creation (CREATE-VIEW) — the closure discipline on binds, mirroring the trigger vocabulary.
FOLD_NAMES = ("active_rules", "actors", "resources", "permissions", "relationships",
              "op_definitions", "view_definitions")


def _matches(e, when):
    """Does one record match a view's trigger? Each entry tests one dimension; a value of
    {"not": X} is the minus-inside-a-trigger: the record matches only if the dimension is
    NOT X (absence as a condition — owner ruling 2026-07-15)."""
    for dim, want in (when or {}).items():
        got = (e.get("payload") or {}).get("kind") if dim == "payload_kind" else e.get(dim)
        # `want` may be a frozen mapping (deep-freeze, EP-02) — Mapping catches both a plain
        # dict and a MappingProxyType, where isinstance(_, dict) would miss the frozen one.
        if isinstance(want, Mapping) and "not" in want:
            if got == want["not"]:
                return False
        elif got != want:
            return False
    return True


def digest_of(e):
    """Content digest of a record (dual-audit cross-check; design guards.digestOf)."""
    body = {"seq": e["seq"], "actor": e["actor"], "action": e["action"], "payload": e.get("payload")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=frozen_default).encode("utf-8")).hexdigest()[:16]


class Views:
    """THE MEMO, AND WHAT EP-28B W3 CHANGED ABOUT IT.

    Every "current X" here is a fold over the record, head-memoised on an append generation.
    Until 2026-07-30 there was ONE generation and every append moved it, so a `FILE-OPEN` —
    a custody record that cannot change one word of law — invalidated `active_rules` and the
    gate's per-act path re-derived law it had just derived. The guest measured the per-act folds
    at 13–23% of a gated act with that recompute inside it.

    THE DISTINCTION IS THE FINDING AND IT IS CARRIED VERBATIM: the subset being right and the
    invalidation being wrong are DIFFERENT THINGS. `design/36` ADDENDUM C's law was that a fold
    on the per-act path must not grow with record count, and the trigger written for it tested
    subset-READING only. Invalidation on unrelated traffic reintroduced the growth by a route
    the trigger never looked at — charter §A26's own class, a trigger written one notch narrower
    than the law it cites. So this is that law raised to its own altitude, not a new rule.

    WHAT MAKES IT LAWFUL RATHER THAN A GUESS. A fold with a DECLARED record subset already owns
    a recognition rule — the predicate its projection selects on — and that predicate is the
    only thing the answer can depend on. So the memo for such a fold is invalidated by exactly
    the records that enter its subset, consulted through the SAME predicate the projection uses.
    NO SECOND RECOGNITION RULE IS WRITTEN: that is EP-24B's one-implementation law applied one
    layer up, and it is why a divergence here could only ever be attributed to the subset and
    never to a second opinion about what a law record is.

    AND THE UNDECLARED MEMOS KEEP TODAY'S BEHAVIOUR, on purpose. `founding_prefix`, `accounts`
    and `chain_end` declare no subset, so they stay on the global append generation and are
    invalidated by every append exactly as before. Silence means "everything invalidates me",
    which is the closed direction: a fold nobody has analysed is never quietly exempted."""

    def __init__(self, store):
        self.store = store
        self._memo = {}
        self._memo_gen = 0          # the append generation: EVERY append moves it (undeclared memos)
        self._subset_gens = {}      # per-fold generation for the folds with a declared subset
        # The listener resolves `self._bump` AT CALL TIME, deliberately. Registering the bound
        # method directly would be equivalent in behaviour and would silently disable
        # `tests/test_ep24c.py`'s control, which neuters `_bump` to prove that a memo outliving
        # its head really does serve a stale answer. A guard that can no longer fail is worse
        # than the tidier line is better.
        store.on_append(lambda e: self._bump(e))

    def _bump(self, e=None):
        """The store's on-append listener. `e` is the committed record, which is what makes the
        distinction possible: the question "could this record change this fold's answer" is
        answerable from the record, and it is answered by the fold's own predicate.

        NO RECORD, EVERYTHING MOVES. `e` is optional so a caller with nothing to judge (a test
        forcing an invalidation, a future path that bumps without a record in hand) gets the old
        behaviour — every memo invalidated. The default errs toward recomputing, never toward
        serving."""
        self._memo_gen += 1
        for fold, projection in self.PER_ACT_FOLDS.items():
            if e is None or PROJECTIONS[projection]._selects(e):
                self._subset_gens[fold] = self._subset_gens.get(fold, 0) + 1

    def _generation_of(self, name):
        """Which generation this memo is keyed on. A fold with a declared subset is keyed on its
        OWN generation; everything else is keyed on the append generation."""
        if name in self.PER_ACT_FOLDS:
            return self._subset_gens.get(name, 0)
        return self._memo_gen

    def cached(self, name, as_of, fn):
        """Head-only memo. asOf bypasses the cache (a historical view is never head).

        ONE LIVE ENTRY PER FOLD. A superseded key is dropped when its replacement is stored, so
        the memo is bounded by the number of memoised folds rather than by traffic. The old
        bound was a 64-entry clear-everything cap, which worked when every key moved together;
        with per-subset generations it would have thrown away the very memos this change exists
        to keep, roughly every sixty appends, and the fix would have looked like it was working
        while delivering a fraction of what it claims. The KEY SHAPE `<fold>:<generation>` is
        kept deliberately: `tests/test_ep24b.py` guards that no authority fold's answer is ever
        memoised by reading these keys, and a bare-name key would have made that guard silently
        stop matching."""
        if as_of is not None:
            return fn()
        key = f"{name}:{self._generation_of(name)}"
        if key in self._memo:
            return self._memo[key]
        v = fn()
        for stale in [k for k in self._memo if k.startswith(name + ":")]:
            del self._memo[stale]
        self._memo[key] = v
        return v

    # ---- the generic fold: reduce the record (up to asOf) into a state dict ----
    def fold(self, reducer, initial=None, as_of=None):
        state = dict(initial) if initial else {}
        for e in self.store.all(as_of):
            reducer(state, e)
        return state

    # ---- the per-act-path folds (EP-24C; design/36 ADDENDUM C) --------------------------
    # THE RULE ADDENDUM C ADDS TO K3: a fold serving the gate's per-act path reads a
    # governance SUBSET, never the whole record, and a structural guard fails when a new
    # whole-record fold lands on that path. The guard is `tests/test_ep24c.py`; this is the
    # surface it declares against.
    #
    # ONE IMPLEMENTATION, TWO RECORD SOURCES — exactly the shape EP-24B proved for the
    # authority family and the mentor filed as standing law. Each fold below has ONE body;
    # `view_fold` hands it either its projection or the whole store, and NOTHING ELSE
    # differs. A fast implementation written beside a slow one would make every divergence
    # ambiguous between the subset and the logic, and no test could attribute its own finding.
    PER_ACT_FOLDS = {"op_definitions": "op_definitions",
                     "active_rules": "law",
                     "category_packs": "category_packs"}

    def view_fold(self, name, accelerated=True, as_of=None):
        """Run one named per-act-path fold against either its projection (accelerated) or the
        whole record (the retained unaccelerated oracle, the standing differential baseline)."""
        if name not in self.PER_ACT_FOLDS:
            raise ValueError(f"{name!r} is not a per-act-path fold — the family is: "
                             + ", ".join(sorted(self.PER_ACT_FOLDS)))
        source = self.store.record_projection(self.PER_ACT_FOLDS[name]) if accelerated else self.store
        return getattr(self, "_" + name)(as_of, source)

    # ---- law as data (every subsystem reads its LAW through this) ----
    def active_rules(self, as_of=None):
        return self.cached("active_rules", as_of,
                           lambda: self.view_fold("active_rules", as_of=as_of))

    def _active_rules(self, as_of=None, source=None):
        # A record IS a LAW record iff its payload declares a `rule_id` — recognition by
        # self-declaration, not by a hard-coded action-name list. So any subsystem's LAW
        # op (e.g. a memory budget amendment) is seen without coupling views to its verb.
        rules = {}
        for e in (source or self.store).all(as_of):
            p = e.get("payload") or {}
            rid = p.get("rule_id")
            if rid is not None:
                # Tier-aware latest-wins (defense in depth): a constitutional entry is
                # superseded ONLY by another constitutional-tier write. A lower-tier record
                # carrying the same rule_id — a forged one that reached the store — cannot
                # silently overwrite the constitution in the derivation. The write itself is
                # already refused at the gate's constitution guard; this makes the
                # operative constitution unshakeable even if a future write path slips past.
                if rules.get(rid, {}).get("tier") == "constitutional" and p.get("tier") != "constitutional":
                    continue
                rules[rid] = {**p, "seq": e["seq"]}
        return rules

    def policy_value(self, key, as_of=None):
        """Latest-effective-wins policy read (law is data; design views.policyValue)."""
        rules = self.active_rules(as_of)
        for rid in sorted(rules, key=lambda r: rules[r]["seq"], reverse=True):
            if rules[rid].get("policy_key") == key:
                return rules[rid].get("value")
        return None

    def category_packs(self, as_of=None):
        """Every changeable vocabulary, latest definition per name (re-seeding a pack is an
        amendment; latest wins). A category_pack is a named CREATE-INFO carrying `levels` —
        actor-classes, geometry, the dual-audit action list, the syscall map (design 28 §3).
        The one read path consumers use, so no subsystem scans the raw store for policy."""
        return self.cached("category_packs", as_of,
                           lambda: self.view_fold("category_packs", as_of=as_of))

    def _category_packs(self, as_of=None, source=None):
        # Fold over ALL records by payload KIND, not just CREATE-INFO: a pack is recognised by
        # what it IS (payload.kind == category_pack), so the genesis seeds (CREATE-INFO) AND
        # governed amendments (AMEND-PACK, A5) both count, latest-wins by sequence.
        # A pack with no `levels` LIST is malformed and does not enter the vocabulary (the
        # closure discipline, applied to data). This keeps a bad record — an operator footgun,
        # or a future bad amendment — from reaching consumers who would iterate or hash it; a
        # consumer inside the on-append audit path must never be handed junk.
        packs = {}
        for e in (source or self.store).all(as_of):
            p = e.get("payload") or {}
            if p.get("kind") == "category_pack" and p.get("name") \
                    and isinstance(p.get("levels"), (list, tuple)):
                packs[p["name"]] = {"name": p["name"], "levels": p["levels"], "seq": e["seq"]}
        return packs

    def visible_category_packs(self, viewer, as_of=None):
        """PACK-SCOPE READ half (design/31 J6; EP-17) — the FIRST sight-filtered read surface, P6
        (sight is law) extended from action to KNOWLEDGE. A per-account view of the vocabularies:
        the packs `viewer` may READ, default-deny. owner/SYSTEM see all (can_read exempts the root);
        any other account sees a pack only with a covering GRANT-READ of its object (`pack:<name>`,
        or a `*` target). The kernel's OWN machinery keeps reading the UNFILTERED category_packs()
        (it acts as the kernel, not as an account) — this is an ADDITIONAL surface for an account
        asking 'what vocabularies can I see', never a replacement. The AUDIT FLOOR stays constitutional
        and SCOPE-INDEPENDENT: what an actor can READ never changes what the floor ENFORCES (the gate's
        audit-floor branch fires on any AMEND-PACK that would lower it, whether or not the actor could
        read the pack). Under the founding, no ordinary account holds a GRANT-READ, so it sees no packs
        until sight is granted — default-deny made visible."""
        from .protection import can_read
        root = self.chain_end(as_of)
        return {name: p for name, p in self.category_packs(as_of).items()
                if can_read(self.store, viewer, f"pack:{name}", root)}

    def root_rules(self, as_of=None):
        """The recorded constitution (design/27): root rules in full trigger->outcome form
        (EP-06, design 28 §4), derived from the record — the boot law readable back as a view.
        `text` is the human sentence; `when`/`then` the executable form; `enforced_by` the
        law->machinery map; `enforcement` live|deferred."""
        out = []
        for e in self.store.by_action("CREATE-RULE", as_of):
            p = e.get("payload") or {}
            if p.get("root"):
                out.append({"rule_id": p.get("rule_id"), "polarity": p.get("polarity"),
                            "text": p.get("text"), "tier": p.get("tier", "ordinary"),
                            "enforcement": p.get("enforcement"),
                            "when": p.get("when") or [], "then": p.get("then") or [],
                            "enforced_by": p.get("enforced_by"), "seq": e["seq"]})
        return out

    def toothless_musts(self, as_of=None):
        """Laws claiming force (polarity + or -) whose OUTCOME is empty — teeth-less musts
        (design 28 §8). A law with a non-empty `then` has teeth; an empty `then` is a claim with no
        consequence. A DEFERRED law (enforcement == 'deferred') is EXEMPT — honest, not toothless:
        its machinery is named-not-built (law precedes machinery). Predicate: polarity in {+,-} AND
        then empty AND not deferred.

        WIDENED (EP-07) from root laws to ALL active law records, now that runtime full-form laws
        exist (obligations; CREATE-RULE-minted structural laws). Two kinds are excluded to avoid
        false positives: op_definition and view_definition carry polarity '+' but are DEFINITIONS,
        not outcome-laws (they have no `then`); policy/registration rules carry no polarity and are
        skipped by the polarity test. (The plan's note that view definitions 'carry no polarity' is
        imprecise — they carry '+', so they are excluded by kind here — logged as a plan/code nuance.)"""
        out = []
        for r in self.active_rules(as_of).values():
            if r.get("kind") in ("op_definition", "view_definition"):
                continue
            if r.get("polarity") in ("+", "-") and not r.get("then") and r.get("enforcement") != "deferred":
                out.append(r.get("rule_id"))
        return out

    def wait_wake(self, as_of=None):
        """Who is blocked on which condition (tree 1.2.2): BLOCK-ON events folded MINUS the arrivals
        that wake them. An actor blocked by BLOCK-ON(on=C) is woken once a later record with action C
        is recorded. Returns {actor: [conditions still blocking]} — a fold, nothing stored."""
        blocked = {}
        all_records = self.store.all(as_of)
        for e in self.store.by_action("BLOCK-ON", as_of):
            cond = (e.get("payload") or {}).get("on")
            woken = any(a["action"] == cond and a["seq"] > e["seq"] for a in all_records)
            if not woken:
                blocked.setdefault(e["actor"], []).append(cond)
        return blocked

    def wake(self, arrival, as_of=None):
        """The live check wake(arrival) (25-view-tree.json): match ONE arrival against the blocked
        set and return the actors it wakes — those still blocked on the arrival's action. `arrival`
        is a record (or a bare action string)."""
        action = arrival["action"] if isinstance(arrival, Mapping) else arrival
        return [actor for actor, conds in self.wait_wake(as_of).items() if action in conds]

    # ---- Views as data records (design/27 §4; owner rulings 2026-07-15) ----------------
    # A view IS a standing rule in full trigger->outcome form: "when a record matches
    # <when>, move it to <then.move_to>". It enters as a named info item carrying a
    # rule_id, so the law view sees it (view definitions are REQ-form records) and it is
    # reusable by name like any dictionary item. One engine executes all definitions;
    # no arrangement is hardcoded. Query, standing view, and broadcast are ONE primitive
    # (match -> move); v1 executes on request, records nothing per run (doc 17 — the
    # standing push/worker tree is the later depth stage).

    def view_definitions(self, as_of=None):
        """Every named view, latest definition per name (re-defining = a new event). A view is either
        a FILTER view (`when`->`then.move_to`, DICT trigger) or a MASTER (`bind` names an S-plane fold,
        EP-08). `tier` and `refresh` (a refresh mandate, design 28 §6) ride along where present."""
        defs = {}
        for e in self.store.by_action("CREATE-VIEW", as_of):
            p = e.get("payload") or {}
            if p.get("kind") == "view_definition" and p.get("name"):
                name = p["name"]
                tier = p.get("tier", "ordinary")
                # TIER CONSERVATION for master views (EP-08B B2; mirrors active_rules, defense in depth):
                # a protected master's tier is CARRIED ACROSS its amendment even though create_view mints
                # no tier — an authorized re-definition INHERITS the protected tier. A lower/absent-tier
                # write cannot silently demote the master in the DERIVATION (the gate already refused any
                # unauthorized supersession; this keeps the operative registry honest even if one slipped).
                prev = defs.get(name)
                if prev and prev["tier"] in ("owner", "constitutional") and tier == "ordinary":
                    tier = prev["tier"]
                defs[name] = {"name": name, "when": p.get("when") or {}, "then": p.get("then") or {},
                              "text": p.get("text"), "bind": p.get("bind"), "tier": tier,
                              "refresh": p.get("refresh"), "seq": e["seq"]}
        return defs

    def execute_view(self, name, as_of=None):
        """Run one view: filter the record per its trigger; return the matched rows and
        the outcome template (where matches are to move). None if no such view."""
        d = self.view_definitions(as_of).get(name)
        if d is None:
            return None
        rows = [e for e in self.store.all(as_of) if _matches(e, d["when"])]
        return {"name": name, "rows": rows, "count": len(rows), "then": d["then"]}

    def coverage_statement(self, name, as_of=None):
        """Derived from the definition ALONE: what this view looks at, what it excludes,
        and which dimensions it never discriminates on — every view confesses its blind
        spots mechanically (design/27 §4)."""
        d = self.view_definitions(as_of).get(name)
        if d is None:
            return None
        used = list((d["when"] or {}).keys())
        boundary = " AND ".join(f"{k} = {v}" for k, v in d["when"].items()) if used \
            else "no filters (the whole record)"
        return {"boundary": boundary,
                "complement": f"everything where NOT ({boundary})" if used else "nothing",
                "undiscriminated": [dim for dim in VIEW_FILTER_DIMENSIONS if dim not in used]}

    def op_definitions(self, as_of=None):
        """The definition-born half of the registry, derived from the record (design/27
        §3): operations admitted by CREATE-OP and not retired — the action view's proof
        that the kernel's own surface is data.

        HEAD-MEMOISED SINCE EP-24C, and the memo DIES WITH ITS HEAD. This fold was the only
        one of the three on the gate's per-act path that recomputed on every consultation —
        one to three times inside a single act, measured — while `active_rules` and
        `category_packs` had been head-memoised since campaign 1. The memo is the SAME one
        they use: keyed on the append generation, bumped by the store's own on-append
        listener, so any movement of the head invalidates it and the next read recomputes
        from the record. That boundary is the whole lawfulness of it. A memo keyed to the
        head is a cache under P2 — kill it, replay, identical answers. A memo that could be
        served ACROSS a head change would be a stored answer with a timestamp, which is the
        refused reference wearing an invalidation story. asOf reads are never memoised at
        all (`cached` bypasses for them), because a historical view is never the head."""
        return self.cached("op_definitions", as_of,
                           lambda: self.view_fold("op_definitions", as_of=as_of))

    def _op_definitions(self, as_of=None, source=None):
        live = {}
        for e in (source or self.store).all(as_of):
            p = e.get("payload") or {}
            if e["action"] in ("CREATE-OP", "AMEND-OP") and p.get("kind") == "op_definition":
                live[p["name"]] = {"name": p["name"], "definition": p.get("definition"),
                                   "tier": p.get("tier", "ordinary"), "seq": e["seq"]}  # AMEND-OP supersedes in place
            elif e["action"] == "RETIRE-OP" and p.get("name") in live:
                del live[p["name"]]
        return live

    # ---- MASTERS as records + the standing push (design 28 §6, §I4; EP-08) -------------
    # The five masters + two registries are SEEDED view-definition records that BIND to an
    # S-plane fold (FOLD_NAMES). The engine functions below are those folds; nothing hardcodes
    # which masters exist — that is data in the record. `master(name)` runs the bound fold.

    def _actors(self, as_of=None):
        """Actor master (tree 2.2.1): every minted actor, latest per id (a CREATE-ACTOR fold)."""
        out = {}
        for e in self.store.by_action("CREATE-ACTOR", as_of):
            p = e.get("payload") or {}
            if p.get("actor_id"):
                out[p["actor_id"]] = {"actor_id": p["actor_id"], "role": p.get("role"),
                                      "actor_class": p.get("actor_class"), "seq": e["seq"]}
        return out

    # ---- the account surface over the actor master (A3; design/31 J1) ------------------
    # Identity is an ACCOUNT: a recorded founding + verification evidence, verified DERIVED
    # per check (never a stored boolean — a boolean rots). Verification bottoms out at the
    # founding: owner/SYSTEM/PC_RUNTIME are FOUNDING-ASSERTED, a third resolution state
    # (ANCHORED), derived from the genesis CREATE-ACTOR records — the founding IS the anchor,
    # so no account record is minted for them (addendum-3 ruling 1b). These are folds over the
    # record; nothing here stores a status (P2).

    def _anchor_ids(self, as_of=None):
        """The founding anchors, DERIVED (design/31 J1; ruling 1b) — TIGHTENED to the CONTIGUOUS
        FOUNDING PREFIX (EP-16 directed fix, EP-15 raise #2). An anchor is an actor minted by the
        founding runtime WITHIN the unbroken initial run of records it asserted; the prefix closes
        PERMANENTLY at the first record asserted by anyone else. So a later caller spoofing the
        founding-runtime name mints NO anchor once any post-founding act has landed — the loose
        EP-15 form (any CREATE-ACTOR by the runtime's name, anywhere) is retired. The founding
        runtime is the asserter of the FIRST CREATE-ACTOR; the leading FOUND-STORE designation
        (asserted by the root owner, before any runtime actor exists) precedes the runtime and does
        not break the prefix. RESIDUAL CAP (stated, not chased here): a spoof as the LITERAL first
        post-install act still lands inside the prefix — closed for real by EP-17's verified
        identity. Walks by seq and stops at the break, so the scan is bounded by the founding
        block, and is head-memoised (the prefix is immutable after genesis).

        ONE WALK, TWO ANSWERS (EP-26). The prefix's ids and the prefix's END are the same
        computation read two ways, so `founding_prefix_end` below is not a second walk that
        could drift from this one. The sweep needs the end because genesis is appended DIRECTLY
        — the gate's own guard states that the founding and the audit mirror bypass it — and a
        record that never crossed the gate has no admission for a counterfactual to
        re-evaluate."""
        return self._founding_prefix(as_of)["ids"]

    def _founding_prefix(self, as_of=None):
        def compute():
            founding_runtime = None
            ids = set()
            seq = 1
            end = 0
            while True:
                e = self.store.by_seq(seq)
                if e is None or (as_of is not None and e["seq"] > as_of):
                    break
                actor = e["actor"]
                if founding_runtime is None:
                    if e["action"] == "CREATE-ACTOR":
                        founding_runtime = actor                       # asserter of the first actor mint
                        ids.add(founding_runtime)
                        ids.add((e.get("payload") or {}).get("actor_id") or e.get("object"))
                    elif e["action"] != "FOUND-STORE":
                        break                                          # something other than the designation first
                elif actor != founding_runtime:
                    break                                              # first record by anyone else -> prefix closed
                elif e["action"] == "CREATE-ACTOR":
                    ids.add((e.get("payload") or {}).get("actor_id") or e.get("object"))
                end = seq
                seq += 1
            return {"ids": ids, "end_seq": end}
        return self.cached("founding_prefix", as_of, compute)

    def founding_prefix_end(self, as_of=None):
        """The last seq of the contiguous founding block — where genesis stops and gated acts
        begin. Read by the reconciliation sweep, which never treats a founding record as a
        candidate: re-running the gate's admission test over genesis would ask whether the
        founding was permitted by the world the founding itself created."""
        return self._founding_prefix(as_of)["end_seq"]

    def _verified_accounts(self, as_of=None):
        """The set of accounts with GROUNDED verification evidence (raise #2). Least fixpoint:
        the founding anchors are the recursion floor (J1 — verification bottoms out at the
        founding); an account is verified iff some VERIFY-ACCOUNT names it with a verifier that
        is itself already grounded (an anchor, or an already-verified account). A verification
        loop that never reaches an anchor never grounds, so it never enters — cycles cannot
        manufacture verification. An anchor id is never a 'verified account' (it is ANCHORED, a
        distinct state), so it is excluded from the result even if a verification names it."""
        ground = self._anchor_ids(as_of)
        verifications = [((e.get("payload") or {}).get("account"), e["actor"])
                         for e in self.store.by_action("VERIFY-ACCOUNT", as_of)]
        verified = set()
        changed = True
        while changed:
            changed = False
            for acct, verifier in verifications:
                if acct and acct not in ground and acct not in verified \
                        and (verifier in ground or verifier in verified):
                    verified.add(acct)
                    changed = True
        return verified

    def verified(self, account_id, as_of=None):
        """Is this account VERIFIED — does it hold live verification evidence whose verifier
        chain grounds at the founding anchors? DERIVED per check, never a stored boolean
        (design/31 J1). A founding anchor returns False here — it is ANCHORED, a third state
        (founding-asserted, not system-verified); read its state through accounts()."""
        return account_id in self._verified_accounts(as_of)

    def accounts(self, as_of=None):
        return self.cached("accounts", as_of, lambda: self._accounts(as_of))

    def _accounts(self, as_of=None):
        """The account surface (A3): every FOUNDED identity keyed by id, each carrying its
        resolution state — anchored | verified | unverified. Anchors are derived from the
        genesis CREATE-ACTOR records and are authoritative (never overwritten by an account);
        accounts are CREATE-ACCOUNT records, verified DERIVED. A bare legacy name (no account)
        is NOT here — the gate resolves it to `unverified:<name>` and it STILL ACTS (the
        transition state until EP-17 narrows the founding openness grant)."""
        anchors = self._anchor_ids(as_of)
        verified = self._verified_accounts(as_of)
        actor_class = {}
        for e in self.store.by_action("CREATE-ACTOR", as_of):
            p = e.get("payload") or {}
            actor_class[p.get("actor_id") or e.get("object")] = p.get("actor_class")
        out = {}
        for aid in anchors:
            out[aid] = {"account_id": aid, "actor_class": actor_class.get(aid),
                        "founded_by": None, "resolution": "anchored"}
        for e in self.store.by_action("CREATE-ACCOUNT", as_of):
            p = e.get("payload") or {}
            aid = p.get("account_id") or e.get("object")
            if aid is None or aid in anchors:     # an anchor is never overwritten by an account
                continue
            out[aid] = {"account_id": aid, "actor_class": p.get("actor_class"),
                        "founded_by": p.get("founded_by") or e["actor"],
                        "resolution": "verified" if aid in verified else "unverified"}
        return out

    def resolve_asserted_by(self, caller, as_of=None):
        """A2 (design/31 J1 + §9 pass-two #4): resolve the CALLER to who-the-record-verified —
        the identity written into a record's provenance.asserted_by. A FOUNDED identity (a
        founding anchor or an account) resolves to itself; a bare legacy name resolves to
        `unverified:<name>`. Enforcement of no-account->no-act is EP-17's flip under the
        openness grant; this EP RESOLVES, and a bare name STILL ACTS. Computed FRESH every act
        from the record (the chain evaluated live, J3): there is no session and no cached login
        — the record IS the session, so every act resolves anew (the web-auth wrong reference,
        refused)."""
        if caller in self._anchor_ids(as_of):
            return caller
        if caller in self.accounts(as_of):
            return caller
        return f"unverified:{caller}"

    # ---- the secrets vault surface (EP-19; design/31 J8) --------------------------------
    # Verify, never reveal: a secret's VALUE lives in the vault (write-once, no read path);
    # the record holds only the sealed HASH and the usage decisions. This fold reads the
    # sealed hash for a name — the only thing about a secret the record can answer, and even
    # that is a hash, not the value. A fold over the record; nothing stores a status (P2).

    def sealed_secret_hash(self, name, space=None, as_of=None):
        """The latest secret sealed under `name` IN `space` — its HASH (design/31 J8). ROTATION is
        supersession by hash: re-sealing a name records a new SEAL-SECRET carrying a new hash,
        and this fold reads LATEST-PER-(SPACE, NAME) (the newest seal wins; an older sealed value
        is superseded, never revealed and never comparable-against again). Keying on (space, name)
        rather than bare name is what keeps a seal in one space from clobbering a same-named sealed
        baseline in another (everything lives in a space, J2; the record already carries one via the
        general space passthrough, read back through authority.space_of). `space=None` resolves to
        the mother space — so in the one-space world this is IDENTICAL to the old latest-per-name
        (every seal and every query resolve to the mother space). Returns the "sha256:<hex>" string,
        or None if `name` was never sealed in `space` (VERIFY-SECRET then records NO-MATCH — you
        cannot match a secret that was never sealed here). A fold, never a status."""
        q_space = space if space is not None else authority.mother_space(self.store, as_of)
        latest = None
        for e in self.store.by_action("SEAL-SECRET", as_of):
            p = e.get("payload") or {}
            if p.get("name") == name and authority.space_of(self.store, e, as_of) == q_space:
                latest = p.get("secret_hash")
        return latest

    # ---- the authority surface (EP-16; design/31 J2 + J3-data, design/30 §1) ------------
    # Spaces (where), grants (how far), roles (a name), and the two questions power asks —
    # power_view (the hardened profile) and covers (the one question). All are folds over the
    # record delegated to kernel.authority; nothing here stores a status (P2 applied to
    # authority). PURE READS this EP — they answer, they do not refuse; EP-17 wires refusal.
    #
    # EP-24B: THE FOLD'S READING PATTERN, AND NOTHING ELSE. Every fold below runs the SAME
    # `kernel.authority` code it always ran, unchanged to the byte. What changed is the record
    # source it is handed: the governance index (store.GovernanceIndex), which holds the seq
    # numbers of the law-and-grant records and resolves each one out of the record at read
    # time. `covers` still computes the positive grant and its complement live on every call,
    # exactly as design/30 §1 specifies; it simply no longer walks the observations it cannot
    # be affected by. Nothing anywhere holds a verdict.
    #
    # THE UNACCELERATED FOLD IS RETAINED, PERMANENTLY, as the standing differential baseline
    # for this surface — `authority_fold(name, ..., accelerated=False)` reads the whole record.
    # Not an era-pinned migration oracle: both sides are current code, so both are live and
    # design/10 §11.2a's two-baseline logic does not apply here. A divergence between them is
    # a defect, never a discovery.

    AUTHORITY_FOLDS = ("mother_space", "spaces", "space_reaches", "reaches_space",
                       "within_makers_reach", "space_of", "grants", "roles", "role_meaning",
                       "power_view", "covers")

    def authority_fold(self, name, *args, accelerated=True, as_of=None):
        """Run one named authority fold against either the governance index (accelerated) or
        the whole record (the retained unaccelerated oracle). ONE implementation, TWO record
        sources — so the standing differential tests exactly one variable, the subset. Two
        separate implementations could also diverge in logic, which is a strictly larger
        failure surface for nothing gained."""
        if name not in self.AUTHORITY_FOLDS:
            raise ValueError(f"{name!r} is not an authority fold — the family is: "
                             + ", ".join(self.AUTHORITY_FOLDS))
        source = self.store.governance_index() if accelerated else self.store
        return getattr(authority, name)(source, *args, as_of=as_of)

    def mother_space(self, as_of=None):
        return self.authority_fold("mother_space", as_of=as_of)

    def spaces(self, as_of=None):
        """The space tree (J2), DERIVED: {space_id: {name, parent, seq}}, the mother at the root."""
        return self.authority_fold("spaces", as_of=as_of)

    def space_reaches(self, outer, inner, as_of=None):
        """Containment (J2): does reach over `outer` cover `inner` (inner IS outer or a descendant)?"""
        return self.authority_fold("space_reaches", outer, inner, as_of=as_of)

    def reaches_space(self, account, target, as_of=None):
        """Does `account` reach `target` — a covering grant whose space contains it (J2 containment)?
        The attenuation-family SPATIAL leash for CREATE-SPACE (reach over the parent) and CREATE-ROLE
        (reach over its space); inert under the openness grant (EP-17 Y3). A PURE READ."""
        return self.authority_fold("reaches_space", account, target, as_of=as_of)

    def within_makers_reach(self, creator, proposed, as_of=None):
        """Is `proposed` {grantee, actions, info, space} within `creator`'s own reach (attenuation,
        E1/X4)? Returns (ok, reason). The bar GRANT enforces at creation, reused by the REVOKE leash
        (EP-17 Y3): you may take away only what you could give. A PURE READ."""
        return self.authority_fold("within_makers_reach", creator, proposed, as_of=as_of)

    def space_of(self, record, as_of=None):
        """The DEFAULT-SPACE fold (J2, the migration): a record's space is its explicit payload
        `space` or, absent one, the mother space — membership DERIVED, never stamped."""
        return self.authority_fold("space_of", record, as_of=as_of)

    def grants(self, as_of=None):
        """The grant fold (J3), the permission master's bound fold (rebound from GRANT-READ this
        EP): the live four-dimensional grants, revoke-superseded. See the class note above the
        old GRANT-READ sight surface — sight stays its own check (can_read, protection.py), one
        info-kind of the general model; the join is EP-17's (RAISED)."""
        return self.authority_fold("grants", as_of=as_of)

    def roles(self, as_of=None):
        return self.authority_fold("roles", as_of=as_of)

    def role_meaning(self, role, as_of=None):
        """A role's DERIVED meaning (J3): the live grants that cite it — changes when they change."""
        return self.authority_fold("role_meaning", role, as_of=as_of)

    def power_view(self, account, as_of=None):
        """The account's hardened profile (design/30 §2): the grants covering it, aggregated per
        dimension. A PURE READ — computed fresh every call, no stored capability set."""
        return self.authority_fold("power_view", account, as_of=as_of)

    def covers(self, account, action, info_kind, space, as_of=None):
        """THE ONE QUESTION (J3): does an active grant let `account` take `action` on `info_kind`
        in `space` (all four dimensions in one grant, space by containment)? A PURE READ."""
        return self.authority_fold("covers", account, action, info_kind, space, as_of=as_of)

    # ---- root authority: the chain-end, the succession fold, structural reach (EP-18; design/31 J7) --
    # Root authority is the CHAIN-END, DERIVED from the founding plus the succession fold — never a
    # stored owner field (the refused wrong reference: ownership-transfer-as-a-field-update). The
    # founding owner is the chain-end until a completed HANDOVER supersedes them with the accepted
    # successor (exit-with-continuity). Every read recomputes; nothing here stores a status (P2).

    HUMAN_ACTOR_CLASS = "human"   # the actor-class token a successor must carry (the pack's actor-classes)

    def founding_root(self, as_of=None):
        """The founding chain-end, DERIVED from the record: the actor the founding minted with the
        root-instruction-authority role (the anchor). Not a hardcoded 'owner' string — the founding
        IS the anchor (design/31 J1: verification bottoms out at the founding). Falls back to the
        historical 'owner' only for a bare store with no founding."""
        for e in self.store.by_action("CREATE-ACTOR", as_of):
            if (e.get("payload") or {}).get("role") == "root-instruction-authority":
                return (e.get("payload") or {}).get("actor_id") or e.get("object")
        return "owner"

    def current_successor(self, as_of=None):
        """The CURRENT successor, a FOLD (latest valid designation-acceptance pair), never a stored
        pointer (design/31 J7). A DESIGNATE-SUCCESSOR names a successor and resets any prior
        acceptance; the named successor's own ACCEPT-SUCCESSION completes the pair; a REVOKE-SUCCESSION
        (or a superseding designation) clears it. Validity is RE-CHECKED LIVE at the moment the fold is
        read (the live-chain rule, design/31 J3 — the mentor's RAISED-BY-DESIGN read: a designation may
        age, so verify at the moment of the fold's validity): the successor must be VERIFIED (EP-15)
        AND actor_class human AT READ TIME, not merely at designation. An aged-out or downgraded
        successor simply stops being valid — no stored boolean to rot."""
        designated, accepted = None, False
        for e in self.store.all(as_of):
            a = e["action"]
            if a == "DESIGNATE-SUCCESSOR":
                designated, accepted = (e.get("payload") or {}).get("successor"), False
            elif a == "REVOKE-SUCCESSION":
                designated, accepted = None, False
            elif a == "ACCEPT-SUCCESSION" and designated is not None and e["actor"] == designated:
                accepted = True
        if not accepted or designated is None:
            return None
        if not self.verified(designated, as_of):
            return None
        if self.accounts(as_of).get(designated, {}).get("actor_class") != self.HUMAN_ACTOR_CLASS:
            return None
        return designated

    def chain_end(self, as_of=None):
        """The current ROOT AUTHORITY holder — DERIVED, never stored (no owner FIELD to update). The
        founding root until a completed HANDOVER supersedes it with the successor who was valid as of
        that handover. A HANDOVER only lands through the gate's anchor guard, which refuses it without
        a valid successor, so every recorded handover is lawful by construction (the record polices
        its builder). Under the founding (no handover) this is the founding root, so every campaign-1
        owner-root check is unchanged; only after a handover does the chain-end move. Kill the
        derivation, replay, the chain-end reconstructs identically."""
        return self.cached("chain_end", as_of, lambda: self._chain_end(as_of))

    def _chain_end(self, as_of=None):
        end = self.founding_root(as_of)
        for e in self.store.by_action("HANDOVER", as_of):
            succ = self.current_successor(e["seq"])
            if succ is not None:                       # gate-guaranteed; defensive
                end = succ
        return end

    def reaches_space_structural(self, account, target, action, as_of=None):
        """R-B (EP-18), TIGHTENED to EXACT-ACTION (EP-19 R-C3): does `account` hold a covering grant
        whose action dimension includes THE SPECIFIC structural act `action` (CREATE-SPACE to found a
        space, CREATE-ROLE to found a role) and whose space contains `target`? This is the
        attenuation-family spatial leash for founding spaces/roles — NOT mere space reach: sight is
        not authority, so a read-only grant over a space must not found subspaces/roles there. R-C3
        replaces class-level membership (any structure-class action reached any structural act) with
        the exact act: a CREATE-ROLE grant no longer authorises founding a space, and vice versa —
        class membership alone no longer reaches (the zero-trust ruling: match = the right, and the
        grant must match THIS act). The `structure-actions` vocabulary pack stays as vocabulary (it
        names which acts are structure-class), but the REACH check is now on the exact action. Under
        the founding openness grant (actions = *) every act is covered, so the leash stays INERT until
        the owner narrows; the root (the chain-end) is exempted at the gate before this is consulted.
        A PURE READ, folded live."""
        for g in self.grants(as_of).values():
            if g["grantee"] not in (account, authority.WILDCARD):
                continue
            if not self.space_reaches(g["space"], target, as_of):
                continue
            if authority.dim_covers(g["actions"], action):
                return True
        return False

    def _relationships(self, as_of=None):
        """Relationship master (tree 3): the derived graph from CREATE-RELATIONSHIP records,
        frame-scoped. Empty until relationships are minted (the op is named-pending in
        BOOTSTRAP_OPS) — the master is DEFINED as a record now, its fold ready (RAISED)."""
        return [{"from": (e.get("payload") or {}).get("from"), "to": (e.get("payload") or {}).get("to"),
                 "rel_kind": (e.get("payload") or {}).get("rel_kind"), "seq": e["seq"]}
                for e in self.store.by_action("CREATE-RELATIONSHIP", as_of)]

    def _resources(self, as_of=None):
        """Resource master (tree 2.2, actable-on): the info/content resources minted (a CREATE-INFO
        fold), latest per object. Minimal v1: the info surface; the fuller actor-inclusive resource
        view composes actors + devices + tunnels as those masters mature (RAISED, honest cap)."""
        out = {}
        for e in self.store.by_action("CREATE-INFO", as_of):
            out[e.get("object")] = {"object": e.get("object"),
                                    "kind": (e.get("payload") or {}).get("kind"), "seq": e["seq"]}
        return out

    def creator_of(self, obj, as_of=None):
        """The actor who MINTED an object — the actor of its EARLIEST record (its creation). The sop
        check's maker lookup (design 28 §5; EP-09), read through the view surface here rather than a
        private store scan in opdefs/protection (the read stack, §I8: operations consult views)."""
        for e in self.store.all(as_of):
            if e.get("object") == obj:
                return e["actor"]
        return None

    def halted_watchers(self, as_of=None):
        """The braked watchers (EP-09; design 28 §7): actors whose ops are frozen by a HALT-WATCHER not
        yet resolved. Ordered fold — a later RESOLVE-WATCHER lifts a halt, a later HALT-WATCHER re-brakes.
        Only the ROOT AUTHORITY holder's RESOLVE-WATCHER counts (a watcher cannot self-resolve — the
        resolution is the root's), and SYSTEM / the root can NEVER be braked (the recorder and the
        resolver stay live, so the record never goes dark). The resolver/unbrakable identity is the
        CHAIN-END, DERIVED (R-C1) — never the hardcoded "owner"; under the founding it IS "owner", and
        after a lawful handover it is the successor. SYSTEM stays a literal (the recorder, a founding
        constant). The gate reads this to freeze a halted watcher's ops."""
        # Fold ONLY the (rare) brake records in seq order — not store.all(): this runs at the gate on
        # EVERY op, so it must be cheap. HALT-WATCHER / RESOLVE-WATCHER are governance-rare.
        root = self.chain_end(as_of)
        events = sorted(self.store.by_action("HALT-WATCHER", as_of) + self.store.by_action("RESOLVE-WATCHER", as_of),
                        key=lambda e: e["seq"])
        halted = set()
        for e in events:
            if e["action"] == "HALT-WATCHER":
                w = (e.get("payload") or {}).get("watcher")
                if w and w not in ("SYSTEM", root):
                    halted.add(w)
            elif e["actor"] == root:   # only the ROOT authority holder's RESOLVE-WATCHER lifts a halt
                halted.discard((e.get("payload") or {}).get("watcher"))
        return halted

    # ---- governance health gauges (design 28 §8; EP-10) — pure derivations, append NOTHING ----

    def metabolism(self, since_seq=None, as_of=None):
        """The governance-debt gauge (design 28 §8): per LAW KIND, the INTAKE (law records created)
        vs the RETIREMENT (law records retired) over a RECORD-TIME window — a `since_seq` floor, NEVER
        the wall clock (15.1: the clock is a sensor). `record_time_now` is the recorded-tick clock
        (EP-07), the honest time source if a rate-per-time is wanted. A view routed to the owner queue;
        it appends nothing. High intake with low retirement is accruing governance debt."""
        g = {k: {"intake": 0, "retire": 0} for k in ("rule", "op", "view")}
        intake_of = {"CREATE-RULE": "rule", "CREATE-OP": "op", "CREATE-VIEW": "view"}
        for e in self.store.all(as_of):
            if since_seq is not None and e["seq"] <= since_seq:
                continue
            a = e["action"]
            if a in intake_of:
                g[intake_of[a]]["intake"] += 1
            elif a == "RETIRE-OP":
                g["op"]["retire"] += 1           # rules/views retire by latest-wins supersession, not a RETIRE verb
        for k in g:
            g[k]["net"] = g[k]["intake"] - g[k]["retire"]
        record_time_now = max(((t.get("payload") or {}).get("now", 0)
                               for t in self.store.by_action("TICK", as_of)), default=0)
        return {"per_kind": g, "since_seq": since_seq, "record_time_now": record_time_now}

    def paper_tigers(self, as_of=None):
        """Mandated views with no recorded servicing (design 28 §8): a view_definition carrying a
        `refresh` mandate whose delivery queue is EMPTY is a paper tiger — it claims a refresh cadence
        but the record shows it moving nothing. A view routed to the owner queue; appends nothing.
        Honest cap: DELIVERY is the only per-run signal the record carries in v1, so a mandated
        MASTER/query view (no move_to) has no recorded servicing signal — flagged with that reason
        rather than silently cleared. Same fold family as boot-integrity: a rule (the mandate) × what
        the system did (delivered)."""
        q = self.queues(as_of)
        out = []
        for d in self.view_definitions(as_of).values():
            if not d.get("refresh"):
                continue
            move_to = (d.get("then") or {}).get("move_to")
            if move_to and q.get(move_to):
                continue                          # serviced: it has delivered — not a paper tiger
            reason = ("mandated move-to view has delivered nothing" if move_to
                      else "mandated view has no recorded per-run signal in v1 (delivery is the only one)")
            out.append({"name": d["name"], "refresh": d["refresh"], "reason": reason})
        return out

    def contradictions(self, as_of=None):
        """The comparison contradiction view (design 28 §9; EP-11) — the ONE comparison law made a
        derivation. Verdicts from DIFFERENT frames on the same (a, b) are DIFFERENT INFORMATION: never a
        conflict, both kept, no merger, no averaging — keeping both IS the feature. Only SAME-frame
        incompatibility is a contradiction: verdicts on the same (a, b, frame) holding more than one
        DISTINCT verdict value. Routed to the owner queue as a VIEW — a pure derivation that appends
        nothing (the EP-10 gauge precedent). Frames are DATA, read off each verdict (never an enum), and
        this does NOT reuse ROOT-NEG-6's rule-activation machinery — it guards comparison OUTPUTS, a
        different record family. (v1: (a, b) is ordered — a is compared to b; normalising a/b order is a
        later refinement, RAISED.)"""
        by_key = {}
        for e in self.store.by_action("COMPARE", as_of):
            p = e.get("payload") or {}
            if p.get("kind") != "verdict":
                continue
            by_key.setdefault((p.get("a"), p.get("b"), p.get("frame")), set()).add(p.get("verdict"))
        return [{"a": a, "b": b, "frame": frame, "verdicts": sorted(v)}
                for (a, b, frame), v in by_key.items() if len(v) > 1]

    # ---- the kernel dictionary (EP-12; cgl-app pattern lowered) — pure folds, append NOTHING ----

    def _disputed_entry_seqs(self, as_of=None):
        """The dictionary-entry seqs under an UNRESOLVED dispute — a fold, never a stored 'disputed'
        flag: DISPUTE(ref_seq) marks, RESOLVE-DISPUTE(ref_seq) lifts (cgl-app dispute/resolution)."""
        disputes = {(e.get("payload") or {}).get("ref_seq") for e in self.store.by_action("DISPUTE", as_of)}
        resolved = {(e.get("payload") or {}).get("ref_seq") for e in self.store.by_action("RESOLVE-DISPUTE", as_of)}
        return {s for s in disputes if s is not None} - {s for s in resolved if s is not None}

    def dictionary(self, entity_kind=None, as_of=None):
        """The kernel dictionary (EP-12): reusable TERMS as records, resolved LATEST-UNDISPUTED-WINS —
        a FOLD, never a stored status. Per (entity_kind, term_key) the current entry is the LATEST
        dictionary_entry whose seq is NOT under an unresolved dispute; a dispute changes what the fold
        answers, and a later undisputed entry wins again. `entity_kind` filters (action/resource/actor);
        None = all. Keyed on the EXACT term (v1 — no normalisation primitive in the interpreter)."""
        disputed = self._disputed_entry_seqs(as_of)
        current = {}
        for e in self.store.by_action("DICT-ENTRY", as_of):     # by_action is seq order -> latest wins in place
            p = e.get("payload") or {}
            if p.get("kind") != "dictionary_entry":
                continue
            if entity_kind is not None and p.get("entity_kind") != entity_kind:
                continue
            if e["seq"] in disputed:
                continue                                        # disputed -> not the undisputed winner
            current[(p.get("entity_kind"), p.get("term_key"))] = {**p, "seq": e["seq"]}
        return current

    def disputed_terms(self, as_of=None):
        """Conflict routing (EP-12): terms whose CURRENT (latest) dictionary entry is under an
        unresolved dispute — routed to the owner queue as a VIEW that appends nothing (the EP-10 gauge
        precedent). The owner resolves by a later undisputed entry (latest-undisputed-wins) or a
        RESOLVE-DISPUTE. Same family as EP-11's comparison contradictions — described, not re-derived."""
        disputed = self._disputed_entry_seqs(as_of)
        latest = {}
        for e in self.store.by_action("DICT-ENTRY", as_of):
            p = e.get("payload") or {}
            if p.get("kind") == "dictionary_entry":
                latest[(p.get("entity_kind"), p.get("term_key"))] = e["seq"]
        return [{"entity_kind": ek, "term_key": tk} for (ek, tk), seq in latest.items() if seq in disputed]

    def _fold(self, name):
        """Resolve a bind name to its S-plane fold (mechanism; the master record chose the name).
        The `permissions` bind REBINDS to the four-dimensional grant fold this EP builds (design/31
        S4): the permission master now reflects the general grant world. The bind NAME is unchanged
        (the permission-master record keeps binding `permissions`), only the fold it resolves to —
        the GRANT-READ sight surface stays live as its own check (can_read), not as this master."""
        # The two per-act-path folds bound here read through their projections (EP-24C) and
        # stay UNMEMOISED, exactly as before: a master read returns a freshly folded value,
        # so `master()` cannot hand two callers the same object. Only the record source moved.
        return {"active_rules": lambda as_of=None: self.view_fold("active_rules", as_of=as_of),
                "actors": self._actors, "resources": self._resources,
                "permissions": self.grants, "relationships": self._relationships,
                "op_definitions": lambda as_of=None: self.view_fold("op_definitions", as_of=as_of),
                "view_definitions": self.view_definitions}.get(name)

    def master(self, name, as_of=None):
        """Execute a MASTER view (design 28 §I4): resolve its `bind` against the fold library and run
        that fold — the one engine executing a record, no arrangement hardcoded. Returns the derived
        value with STALENESS metadata (`derived_at` = the store version it reflects). None if `name`
        is not a bound master."""
        d = self.view_definitions(as_of).get(name)
        if not d or not d.get("bind"):
            return None
        fold = self._fold(d["bind"])
        if fold is None:                                    # a bind outside the library (should be caught at
            return None                                     # creation) — no silent wrong answer
        return {"name": name, "bind": d["bind"], "value": fold(as_of),
                "derived_at": self._memo_gen if as_of is None else as_of,
                "refresh": d.get("refresh")}                # a mandated-refresh field (design 28 §6)

    # ---- the crossing surface (EP-23; design/36 K8/K9, design/34) ----------------------
    # THE IN-FLIGHT VIEW IS A DIFFERENCE BETWEEN RECORDS. Hand-outs minus answers minus
    # re-judges — no dict of open crossings, no future, no callback registry, because a
    # registry of what is in flight is exactly the stored status P2 forbids and it dies
    # with its process. Kill every one of these answers, replay from the record file, and
    # the same crossings come back suspended at the same point. Every method here is a PURE
    # READ that appends nothing (the EP-10 gauge precedent); the folds live in
    # kernel.crossing and are imported lazily, the way visible_category_packs imports
    # protection, so the fold module can read this one's view engine without a cycle.

    def crossings(self, as_of=None):
        """Every crossing with its state DERIVED: open | answered | superseded."""
        from . import crossing
        return crossing.crossings(self.store, as_of)

    def open_crossings(self, as_of=None):
        """What is suspended right now — the whole of "in flight"."""
        from . import crossing
        return crossing.open_crossings(self.store, as_of)

    def crossing_fingerprint(self, handout_seq, as_of=None):
        """Does the judged world still hold for one crossing? Answerable independently of
        any return attempt — which is what keeps staleness and authority two separately
        observable verdicts rather than one merged outcome (design/34 §2)."""
        from . import crossing
        return crossing.fingerprint(self.store, self, handout_seq, as_of)

    def stale_crossings(self, as_of=None):
        """Open crossings whose read-set has moved — computed from the world, never read
        off refusal records (a refusal proves someone tried; staleness is a fact about the
        world whether or not anyone tried)."""
        from . import crossing
        return crossing.stale_crossings(self.store, self, as_of)

    def crossings_needing_reask(self, as_of=None):
        """Stale crossings the machine may not retry: policy says abort, or the recorded
        retry budget is spent. The stale refusal stands and a human re-asks — never a silent
        execute, never a silent drop (design/34 §4)."""
        from . import crossing
        return crossing.needing_reask(self.store, self, as_of)

    def crossing_flutter(self, as_of=None):
        """Hot-read-set flutter per station (design/34 §4): repeated re-judges mean the pack
        is over-broad or the station belongs on a coarser view. SURFACED as a view — the
        response to flutter is to see it, never to weaken the check."""
        from . import crossing
        return crossing.flutter(self.store, as_of)

    # ---- the two-times surfaces (EP-26; design/35, design/36 K7/K10 §4b) --------------------
    # Every method here is a PURE READ that appends nothing, and every one is a fold over the
    # record: the session registry, the sweep's products, and both reconciliation views hold
    # nothing at all. Kill them, replay from the record file, and the same answers come back —
    # which is exactly what T-TOTAL-ROUNDTRIP-2 extended asserts. The folds live in
    # kernel.reconcile and are imported lazily, the way the crossing surfaces above do it, so
    # the fold module can read this view engine without a cycle.

    def sessions(self, as_of=None):
        """The session registry: every decider session with its DECLARED read-set, live or
        closed. A derived view, never a table — there is no session store and no cached login,
        because the record IS the session (the web-auth reference, refused at EP-15 and refused
        again here)."""
        from . import reconcile
        return reconcile.sessions(self.store, as_of)

    def live_sessions(self, as_of=None):
        """The contact points a law change would be delivered to. EP-27 makes the delivery; this
        EP records the contact points and their views and delivers nothing new."""
        from . import reconcile
        return reconcile.live_sessions(self.store, as_of)

    def session_read_set(self, session_id, as_of=None):
        """A session's declared read-set, RESOLVED AT USE. Stored as refs and resolved on
        reading, because a resolved copy would be a frozen derivative of a definition that can
        be amended underneath it."""
        from . import reconcile
        return reconcile.session_read_set(self.store, self, session_id, as_of)

    def overturns(self, as_of=None):
        """Every overturn on the record. The acts and their overturns are BOTH permanently
        here — an overturn is an appended decision, never an edit and never a disappearance."""
        from . import reconcile
        return reconcile.overturns(self.store, as_of)

    def standing(self, seq, as_of=None):
        """Does the recorded act at `seq` still stand? asOf BEFORE its overturn still answers
        True: order is untouched, validity is what changed, and two frames give two answers
        without contradicting each other."""
        from . import reconcile
        return reconcile.standing(self.store, seq, as_of)

    def re_ask(self, gate=None, as_of=None):
        """THE RE-ASK VIEW (§4b.4, RULED): refusals a late-arriving permissive law would now
        allow. NOTHING is appended for them — an overturn cannot perform an act that never
        happened, and a record claiming an effect that did not occur is the one forbidden lie.
        The remedy is re-submission at the current head, by the actor, through the ordinary
        door. Pass the gate to have each case RE-EVALUATED rather than merely surfaced."""
        from . import reconcile
        return reconcile.re_ask(self.store, self, gate, as_of)

    def pending_sweeps(self, gate, as_of=None):
        """Every sweep the record implies, RECOMPUTED — the refused ones included. A refused
        sweep appends nothing, so it is derived rather than read: the estate's own answer
        applied to itself, compute what you did not store. A reader holding the record can see
        which sweeps refused and which chain each would have ended."""
        from . import reconcile
        return reconcile.pending(gate, self.store, self, as_of)

    def exposure(self, as_of=None):
        """THE EXPOSURE VIEW (§4b.6, RULED): who consumed what, under which overturned act. The
        sweep reconciles STATE; what was already consumed is out of mechanical reach and the
        owner ruled that no stronger mechanical remedy is wanted. What the machine owes is this
        honest list, and the remedy is judgment on the deontic side."""
        from . import reconcile
        return reconcile.exposure(self.store, as_of)

    # ---- the lane surfaces (EP-27; design/35 §3, design/36 K10, wall primitive 8) ----------
    # The delivery schedule is a DERIVATION like every other view here: the channels, the
    # pending set, what the recorded budget shed, and what reached each live session are all
    # recomputed from the record alone. The on-append worker (kernel/push.py) accelerates
    # exactly this and holds no truth of its own, which is why killing it changes no answer.

    def lane_report(self, as_of=None):
        """THE WHOLE DELIVERY SCHEDULE, DERIVED. Channels, pending (delayed) items, shed items
        with the rule that shed them, per-session law deliveries, and dangling declarations.
        Deliveries APPEND NOTHING (the flood boundary), so every one of these is computed and
        none is stored — including the sheds, which is the EP-26 answer to a refused sweep
        applied to a dropped delivery: do not store what the policy did, compute it."""
        from . import push
        return push.derive(self.store, self, as_of)

    def queues(self, as_of=None):
        """The standing-push delivery queues, DERIVED from the record (design 28 §6): for every active
        move-to view definition, the records its trigger matched, grouped by channel (the move_to
        target). THIS IS THE SOURCE OF TRUTH — the on-append worker (kernel/push.py) keeps an in-memory
        acceleration of exactly this; kill that memory and this rebuilds the same queues from the record
        alone (the round-trip law applied to delivery). Deliveries APPEND NOTHING (doc-17 flood
        boundary): a queue is a view, never a stored list.

        [EP-27] The channels are now the channel half of `lane_report` rather than a second walk
        of the record: with a recorded budget in force, a queue derived WITHOUT the lane schedule
        would disagree with the worker the moment the budget bound, which is the EP-08B defect
        (an acceleration drifting from its derivation) arriving from the other side. One
        derivation, read two ways."""
        return self.lane_report(as_of)["channels"]
