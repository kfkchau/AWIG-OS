"""gov-os kernel — authority folds (L2, EP-16; design/31 J2 + J3-data, design/30 §1).

The UPWARD half's data ground, computed like every other current state: nothing here
persists a status. Three derivations, one root (authority is never stored at the point of
use — it is folded fresh from the record every check):

  * the SPACE TREE — where an act lives (J2). Every space is a record; nesting IS
    containment; reach over a space includes its subspaces; every chain terminates at the
    mother space. A space is NOT a string prefix (the refused wrong reference): membership
    and reach are walks over parent-ref records, and renaming a space is an amendment, not
    a move.
  * the GRANT FOLD — how far a power reaches (J3). A grant is the positive four-dimensional
    co-happening `(+) grantee x actions x info x space` (design/30 §1, the owner's exact
    form). The negative space is the COMPUTED complement of the grant set, never stored.
    `revoke` supersedes a grant latest-wins; NOTHING cascades because nothing downstream was
    stored — the chain is walked afresh at the next check.
  * a ROLE is a NAME referenced by grants (J3). It stores no power (a role carrying its own
    permission list is RBAC — the refused shape). Its meaning is DERIVED: the grants that
    cite it. Change the citing grants, the role's meaning changes. HOLDING a role is an
    ORDINARY GRANT (X3, design/31 §2 "a bundle of GRANTABLE power"): `(+) account x hold x
    role:R x space` — no membership record kind, no role-permission list. `covers` then routes
    ONE hop: a covering DIRECT grant, OR a covering grant whose SUBJECT is a role the account
    holds; both links folded live, so revoking EITHER is instant with zero cascade.

`power_view` and `covers` are PURE READS this EP (they answer; EP-17 wires refusal at the
gate). `within_makers_reach` is the one refusal this EP owns — attenuation, checked at grant
CREATION (design/31 ADDENDUM E1; X4): a grant is never wider than its maker. A non-root grant
must be contained WHOLE — actions AND info AND space together — inside AT LEAST ONE covering
grant of the maker; per-dimension unions across different grants are refused (they admit new
power by recombination). "Never wider than the maker" is the owner's law; whole-containment is
its faithful arithmetic (X4 corrects E1's "dimension by dimension" phrasing).

Wildcard token: `*` (the estate's established token — can_read and the founding openness
grant both use it; see BUILD-PROGRESS EP-16 raise). A wildcard is always EXPLICIT: an ABSENT
dimension covers NOTHING, never everything (design/31 J3: wildcards explicit, never implied).
"""

WILDCARD = "*"


# ---- the space tree (J2) ---------------------------------------------------------------

def mother_space(store, as_of=None):
    """The pack's root — the info_space founded at genesis (`space:root`). The tree's root
    and the DEFAULT-SPACE fold's default (records without a space belong here)."""
    for e in store.by_action("CREATE-INFO", as_of):
        if (e.get("payload") or {}).get("kind") == "info_space":
            return e.get("object")
    return None


def spaces(store, as_of=None):
    """The space tree, DERIVED: {space_id: {name, parent, seq}}. The mother space is the root
    (parent None), read from its genesis info_space record; CREATE-SPACE records add nodes,
    each naming a parent, latest-wins per id (re-creating a space is an amendment — a rename or
    a re-parent, never a filesystem move). The mother's own info_space record wins the id even
    if a later CREATE-SPACE names it, so the root can never be re-parented into the tree."""
    tree = {}
    mother = mother_space(store, as_of)
    for e in store.by_action("CREATE-SPACE", as_of):
        p = e.get("payload") or {}
        sid = e.get("object")
        if sid == mother:                       # the root is not a tree node with a parent
            continue
        tree[sid] = {"space_id": sid, "name": p.get("name"), "parent": p.get("parent"),
                     "seq": e["seq"]}
    if mother is not None:
        # the mother record wins its id — the root has no parent, and no CREATE-SPACE can
        # re-parent it (that would break "every chain terminates at the root").
        me = None
        for e in store.by_action("CREATE-INFO", as_of):
            if e.get("object") == mother and (e.get("payload") or {}).get("kind") == "info_space":
                me = e
                break
        tree[mother] = {"space_id": mother, "name": (me.get("payload") or {}).get("name") if me else "root",
                        "parent": None, "seq": me["seq"] if me else 0}
    return tree


def _ancestors_incl(tree, space_id):
    """space_id and every ancestor up to the root, walking parent refs. A guard breaks a
    pre-existing loop (there should be none — cycles refuse at creation)."""
    out, node, seen = [], space_id, set()
    while node is not None and node not in seen:
        out.append(node)
        seen.add(node)
        node = tree.get(node, {}).get("parent")
    return out


def space_reaches(store, outer, inner, as_of=None):
    """Containment (J2): does reach over `outer` cover `inner`? True iff inner IS outer or a
    DESCENDANT of outer — the root's reach covers everything, a parent's reach covers its
    subtree, a sibling's does not. Walks parent refs up from inner (never a string prefix)."""
    if outer is None or inner is None:
        return False
    return outer in _ancestors_incl(spaces(store, as_of), inner)


def would_cycle(store, space_id, parent, as_of=None):
    """Would giving `space_id` the parent `parent` create a cycle? True iff space_id is
    parent-or-an-ancestor-of-parent — then space_id -> ... -> parent -> space_id loops. At a
    fresh creation this is always False (a new id is in no chain); at an AMENDMENT re-parenting
    a space under its own descendant it is True (the corpus's no-circular-authority item,
    applied to territory)."""
    return space_id in _ancestors_incl(spaces(store, as_of), parent)


def space_exists(store, space_id, as_of=None):
    return space_id in spaces(store, as_of)


# ---- the default-space fold (J2, the migration) ----------------------------------------

def space_of(store, record, as_of=None):
    """Where a record lives — DERIVED, never stamped (records are frozen + append-only, so a
    field cannot be written onto an existing record). A record carrying an explicit `space` in
    its payload lives there; every record without one belongs to the mother space. THE FOLD IS
    THE MIGRATION: no history rewrite, no migration pass — every pre-account record defaults to
    where it already effectively lived (the one mother space)."""
    s = (record.get("payload") or {}).get("space")
    return s if s is not None else mother_space(store, as_of)


# ---- wildcard-aware dimension arithmetic -----------------------------------------------

def _as_set(dim):
    """A dimension value -> a set of concrete items, or the WILDCARD sentinel. `*` is the
    wildcard (covers all); a list/tuple/set is its members (already-aggregated reaches arrive
    as sets); a bare string is a one-item set; None / absent is the EMPTY set (covers nothing —
    a wildcard is never implied)."""
    if dim == WILDCARD:
        return WILDCARD
    if isinstance(dim, (list, tuple, set, frozenset)):
        return set(dim)
    if dim is None:
        return set()
    return {dim}


def dim_covers(granted, wanted):
    """Does one grant's dimension cover one wanted value? `*` covers anything; otherwise
    membership. An absent dimension covers nothing."""
    g = _as_set(granted)
    return True if g == WILDCARD else wanted in g


def _union_dim(dims):
    """Union of several dimension values, wildcard-absorbing: `*` if any is `*`, else the set
    union of the concrete members."""
    acc = set()
    for d in dims:
        s = _as_set(d)
        if s == WILDCARD:
            return WILDCARD
        acc |= s
    return acc


def _dim_subset(sub, sup):
    """Is `sub` (a proposed grant's dimension) within `sup` (the maker's aggregate reach)?
    `sup == *` covers any sub; a `sub == *` exceeds any non-`*` sup; otherwise set subset.
    This is the attenuation arithmetic, dimension by dimension (design/31 E1)."""
    ss, sp = _as_set(sub), _as_set(sup)
    if sp == WILDCARD:
        return True
    if ss == WILDCARD:
        return False
    return ss <= sp


# ---- the grant fold (J3) ---------------------------------------------------------------

def grants(store, as_of=None):
    """The live grants, DERIVED: {grant_id: {grantee, actions, info, space, role, seq}}. A
    GRANT record enters keyed on its object (`grant:<id>`); a REVOKE on the same object
    SUPERSEDES it (latest-wins) — removed from the live set, NOTHING cascades because nothing
    downstream was stored. A later GRANT with the same id re-mints it. The founding openness
    grant parses here as a normal grant (grantee/actions/info all `*`, space the mother)."""
    live = {}
    for e in store.all(as_of):
        a = e["action"]
        p = e.get("payload") or {}
        if a == "GRANT" and p.get("kind") == "grant":
            gid = e.get("object")
            live[gid] = {"grant_id": gid, "grantee": p.get("grantee"), "actions": p.get("actions"),
                         "info": p.get("info"), "space": p.get("space"), "role": p.get("role"),
                         "seq": e["seq"]}
        elif a == "REVOKE":
            live.pop(e.get("object"), None)
    return live


def _covering_grants(store, account, as_of=None):
    """The grants that reach `account`: those addressed to the account itself or to everyone
    (`*`). (Roles are a labelling layer this EP, not a covers hop — see role_meaning; raised.)"""
    return [g for g in grants(store, as_of).values() if g["grantee"] in (account, WILDCARD)]


def power_view(store, account, as_of=None):
    """The account's hardened profile (design/30 §2): the grants covering it, and the aggregate
    of what they permit — the actions it may take, the info kinds, the spaces it reaches, and
    the subject-classes it holds. A PURE READ (it answers; EP-17 wires refusal). Computed fresh
    from the grant fold every call: no stored capability set, no cached login."""
    gs = _covering_grants(store, account, as_of)
    return {"account": account, "grants": gs,
            "actions": _union_dim(g["actions"] for g in gs),
            "info": _union_dim(g["info"] for g in gs),
            "spaces": [g["space"] for g in gs],
            "grantees": _union_dim(g["grantee"] for g in gs)}


def _hold_token(store, as_of=None):
    """The `hold` action token (X3), read from the founding `authority-actions` vocabulary pack —
    HOLD enters as VOCABULARY (a pack, never a hardcoded enum). The founding declares it; code
    never invents it. Latest-wins over the record (an AMEND-PACK could rename it); falls back to
    the literal only if the pack is absent (a bare store with no founding)."""
    token = None
    for e in store.all(as_of):
        p = e.get("payload") or {}
        if p.get("kind") == "category_pack" and p.get("name") == "authority-actions":
            levels = p.get("levels") or []
            if levels:
                token = levels[0]
    return token if token is not None else "hold"


def holds_role(store, account, role_id, space, as_of=None):
    """Does `account` HOLD `role_id` in a space reaching `space` (X3)? Holding is an ORDINARY
    GRANT whose action is the `hold` vocabulary token and whose info names the role
    (`(+) account x hold x role:R x space`) — no membership record kind, no role-permission list
    (the RBAC refusal stands). Folded live from the grant set: revoke the hold grant and the next
    covers() answers false, zero cascade."""
    hold = _hold_token(store, as_of)
    for h in _covering_grants(store, account, as_of):
        if dim_covers(h["actions"], hold) and dim_covers(h["info"], role_id) \
                and space_reaches(store, h["space"], space, as_of):
            return True
    return False


def covers(store, account, action, info_kind, space, as_of=None):
    """THE ONE QUESTION (J3, X3): does an active grant let `account` take `action` on info of kind
    `info_kind` in `space`? A PURE READ (it answers; EP-17 wires refusal). Two routes, ONE hop:
      route 1 — a covering DIRECT grant: grantee (account or `*`) x action x info kind x a space
                whose reach contains the target (containment). UNCHANGED from the first build, so
                no direct-grant answer ever moves.
      route 2 — a covering grant whose SUBJECT IS A ROLE the account holds (X3, additive): a role
                confers to its holders. Both links are live grants, so revoking EITHER (the power
                grant to the role, or the account's hold-grant) is instant with zero cascade.
    Revoke a covering grant and the very next call answers false — nothing cascaded."""
    # route 1 — direct (identical to the first build: guarantees no direct-grant answer changes)
    for g in _covering_grants(store, account, as_of):
        if dim_covers(g["actions"], action) and dim_covers(g["info"], info_kind) \
                and space_reaches(store, g["space"], space, as_of):
            return True
    # route 2 — one-hop role route (ADDITIVE — only reaches grants whose subject is a founded role)
    known_roles = roles(store, as_of)
    for g in grants(store, as_of).values():
        if g["grantee"] in known_roles \
                and dim_covers(g["actions"], action) and dim_covers(g["info"], info_kind) \
                and space_reaches(store, g["space"], space, as_of) \
                and holds_role(store, account, g["grantee"], space, as_of):
            return True
    return False


def role_meaning(store, role, as_of=None):
    """A role's DERIVED meaning (J3): the live grants that cite it. A role stores no power —
    its meaning IS the grants naming it, so changing (or revoking) a citing grant changes the
    role's meaning at the next read. Refuses the RBAC shape by construction: there is no stored
    permission list to consult, only the grant fold filtered by the role label."""
    return {gid: g for gid, g in grants(store, as_of).items() if g.get("role") == role}


def roles(store, as_of=None):
    """The founded role NAMES: {role_id: {name, space, seq}} from CREATE-ROLE records
    (latest-wins). A name only — the power lives in the grants that cite it."""
    out = {}
    for e in store.by_action("CREATE-ROLE", as_of):
        p = e.get("payload") or {}
        rid = e.get("object")
        out[rid] = {"role_id": rid, "name": p.get("name"), "space": p.get("space"), "seq": e["seq"]}
    return out


# ---- attenuation: a grant is never wider than its maker (design/31 ADDENDUM E1, S6) -----

def within_makers_reach(store, creator, proposed, as_of=None):
    """Is a `proposed` grant `{grantee, actions, info, space}` within `creator`'s own reach?
    The one refusal this EP owns (S6/E1; X4): a non-root creator may not mint a grant wider than
    the power it holds. Walks the creator's own live chain (the same grant fold). Two arithmetic
    parts:

    (a) SUBJECT (minimal target dimension, mentor-CONFIRMED until accounts carry spaces): a
        specific delegatee is in scope; widening the subject to everyone (`*`) needs the
        creator's own `*`-subject reach.

    (b) WHOLE CONTAINMENT (X4 — corrects E1's "dimension by dimension"): the (actions, info,
        space) triple must fit inside AT LEAST ONE single covering grant of the creator —
        actions ⊆ that grant's actions AND info ⊆ its info AND target space within its reach
        (containment). Per-dimension UNIONS across DIFFERENT grants are refused: a maker holding
        (read x secrets x A) and (write x public x B) may NOT mint (write x secrets x A), which no
        single grant of theirs covers — new power from recombination. A lawful span across two
        maker grants is expressed as two narrower grants, each contained; no expressiveness lost,
        only the widening.

    Equal reach passes ("no wider" includes equality). Returns (ok, reason); the caller refuses
    AT CREATION citing the creator's own hop. Root/founding grants never reach here (the gate
    exempts the CHAIN-END/SYSTEM before calling this — R-C1, never a literal "owner"; genesis
    grants bypass the gate) — the root's reach is the whole tree by containment, so nothing it
    grants can exceed it. This also bounds a grant whose
    SUBJECT is a role and a hold-role grant hop-by-hop: each is an ordinary grant attenuated at
    its own mint (X3)."""
    gs = _covering_grants(store, creator, as_of)
    # (a) subject scope
    grantee = proposed.get("grantee")
    if grantee == WILDCARD and _union_dim(g["grantee"] for g in gs) != WILDCARD:
        return False, f"{creator} may not widen a grant's subject to all accounts — it holds no such reach"
    # (b) whole containment: actions AND info AND space inside ONE covering grant
    tspace = proposed.get("space")
    for g in gs:
        if _dim_subset(proposed.get("actions"), g["actions"]) \
                and _dim_subset(proposed.get("info"), g["info"]) \
                and space_reaches(store, g["space"], tspace, as_of):
            return True, None
    return False, (f"grant (actions x info x space) is not contained whole within any single grant "
                   f"held by {creator} — a grant is never wider than its maker (no widening by "
                   f"recombination)")


def reaches_space(store, account, target, as_of=None):
    """Does `account` have REACH over `target` — hold a covering grant whose space CONTAINS `target`
    (containment, J2: reach over a space includes its subspaces)? The attenuation-family regime's
    spatial leash (EP-17 Y3): CREATE-SPACE needs reach over the PARENT, CREATE-ROLE over its SPACE —
    a structural extension only within territory the founder already reaches. Purely the grant's
    SPACE dimension: the space-tree walk, never a stored capability, folded live from the grant set
    every call (revoke a covering grant and the very next call answers false). Under the founding
    openness grant (space = the mother) every account reaches every founded space, so the leash is
    INERT until the owner narrows; the root (the CHAIN-END/SYSTEM, R-C1) is exempted at the gate
    before this is consulted, its reach being the whole tree by containment."""
    for g in _covering_grants(store, account, as_of):
        if space_reaches(store, g["space"], target, as_of):
            return True
    return False
